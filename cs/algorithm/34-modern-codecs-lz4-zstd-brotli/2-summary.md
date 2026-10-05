# algorithm/34-modern-codecs-lz4-zstd-brotli — 현대 코덱: 속도↔비율, 딕셔너리, ANS/FSE, 프레임 — 정리 (힌트)

## 해결하는 문제

DEFLATE(33번)는 1990년대 설계다. 지금의 요구 몇 가지에 맞지 않는다.

```text
  요구                                     DEFLATE의 한계
  초당 수 GB로 압축·해제 (DB 페이지, RPC)    엔트로피 단계(허프만 비트 단위 처리)가 느림
  더 높은 비율 + 빠른 해제 (로그·백업)       윈도 32KB, 기호당 1비트 이상
  수백 바이트 레코드 하나씩 압축             참조할 "과거"가 없어 거의 안 줄어듦
  웹 정적 자원을 더 작게                     흔한 단어를 매번 처음부터 배워야 함
```

현대 코덱은 이 축 하나씩을 밀어붙인다.
- *LZ4*: 엔트로피 부호를 아예 빼고 바이트 단위 LZ77만 한다 → 속도 극단.
- *zstd(Zstandard)*: LZ77 + 허프만(리터럴) + FSE(나머지) + 큰 윈도 + 딕셔너리 → 넓은 레벨 범위.
- *Brotli*: LZ77 + 허프만 + 문맥 모델링 + 내장 정적 사전 → 웹 텍스트에서 비율.

쉬운 예: 이사 짐 싸기.
- 그냥 상자에 던져 넣기(빠름, 부피 큼) ↔ 하나하나 접고 진공 포장(느림, 부피 작음).
- 같은 모양 상자를 매번 새로 접지 않고, 미리 접어 둔 상자 세트를 쓴다(딕셔너리).

똑같은 구조다.\
"압축 레벨"은 얼마나 공들여 접을지, "딕셔너리"는 미리 준비해 둔 상자 세트다.

실무 예:
- Kafka 프로듀서 `compression.type`은 `none`·`gzip`·`snappy`·`lz4`·`zstd` 중 하나다. 배치 단위로 압축한다(Kafka `ProducerConfig` 소스).
- HTTP `Content-Encoding: br`·`zstd`(network/39).
- 로그 수집에서 레코드 하나씩 압축했더니 비율이 1.1배에 그쳤다(아래 실험).

## 동작·원리

### 1. 속도↔비율 곡선 — 레벨이 바꾸는 것

```text
  비율 ▲
       │                                  ● zstd -19 / xz -6
       │                       ● zstd -9
       │            ● zstd -3 ● gzip -6/-9
       │     ● zstd -1 ● gzip -1
       │  ● zstd --fast=4
       │ ● LZ4 (문서 수치)
       └────────────────────────────────────▶ 압축 시간
         빠름                              느림
  해제 속도: zstd·gzip은 레벨과 거의 무관 (zstd README, 아래 실험)
```

(개념도. 점의 상대 위치는 아래 notes.txt 실험을 대략 따랐고, LZ4는 실측이 없어 문서 수치로 짐작한 자리다)

- 레벨을 올리면 압축기가 하는 일이 는다.
  - 매치 파인더가 해시 체인·이진 트리를 더 깊게 탐색한다(33번 §3).
  - 탐욕 매칭 → 게으른 매칭 → 여러 후보의 비용을 비교하는 "최적 파싱"으로 간다.
  - 윈도를 키운다.
- zstd 1.5.5 소스 `lib/compress/clevels.h`의 레벨 표(입력 256KB 초과용) 발췌:

```text
           W(윈도 log)  C(체인 log)  S(탐색 log)  strat(전략)
  level 1      19          13           1         ZSTD_fast      해시 표 1개
  level 3      21          16           1         ZSTD_dfast     해시 표 2개
  level 5      21          18           3         ZSTD_greedy    탐욕 매칭
  level 9      22          20           4         ZSTD_lazy2     게으른 매칭(2단)
  level 13     22          22           4         ZSTD_btlazy2   이진 트리 매치 파인더
  level 16     22          22           5         ZSTD_btopt     최적 파싱
  level 19     23          24           7         ZSTD_btultra2
  level 22     27          27           9         ZSTD_btultra2  (--ultra)
```

  - 레벨이 오르면 윈도(2^W), 체인·탐색 깊이가 대체로 커지고 전략이 바뀐다. 매개변수마다 단조 증가는 아니다(전체 표에서 S는 레벨 12의 6 → 13의 4로 줄고, 전략이 btlazy2로 바뀐다). 레벨 3의 윈도 2^21 = 2MiB는 아래 실험의 `zstd -lv` 출력 `Window Size: 2.00 MiB`와 같다.
  - 전략 이름은 `lib/zstd.h`의 `ZSTD_strategy`(ZSTD_fast=1 … ZSTD_btultra2=9)다. 오른쪽 설명 열은 이름에서 읽은 해석이다.
- 해제기는 매치를 찾지 않는다. 리터럴·시퀀스를 엔트로피 복호(허프만·FSE, RFC 8878 §3.1.1.3·§4)한 뒤 그대로 복사한다. 그래서 해제 속도는 레벨과 거의 같다. zstd README: "Decompression speed is preserved and remains roughly the same at all settings".
- 기본값이 제품마다 다르다(확인한 것만).
  - gzip CLI 기본 `-6`(gzip 1.12 man), xz 기본 `6`(xz 5.4.5 `--help`).
  - zstd CLI 기본 `3`, 범위 1~19, `--ultra`로 22까지, `--fast=N`은 음수 레벨(zstd 1.5.5 man).
  - Brotli CLI 기본 품질 **11**(`--best`, 범위 0~11, google/brotli `brotli.md`). 최고 레벨이 기본이다.

### 2. LZ4 — 엔트로피 단계 없는 바이트 정렬 LZ77

```text
  LZ4 시퀀스 (블록 = 시퀀스의 나열)
  ┌───────────────┬──────────────┬───────────┬─────────┬──────────────┐
  │ token (1바이트)│ 리터럴 길이   │ 리터럴들   │ offset  │ 매치 길이     │
  │ 상위4 │ 하위4  │ 추가 바이트   │ (그대로)   │ 2바이트 LE│ 추가 바이트  │
  │ 리터럴│ 매치    │ (15일 때 255…)│           │ 1..65535 │ (15일 때 …)  │
  └───────────────┴──────────────┴───────────┴─────────┴──────────────┘
  매치 길이 = 하위4 + 4 (minmatch 4)
```

- LZ4 블록 형식 문서(lz4/lz4 `doc/lz4_Block_format.md`)
  - "엔트로피 부호기도 프레이밍 층도 없다." 단순함과 속도를 위한 설계다.
  - offset은 2바이트, 최대 65535. 0은 잘못된(손상된) 블록이다.
  - 최소 매치 길이 4. 블록의 마지막 5바이트는 리터럴이고, 마지막 매치는 블록 끝 12바이트 전에 시작해야 한다.
- 모든 필드가 바이트 경계에 있다. 비트 단위로 읽는 허프만 해제보다 분기·시프트가 적다.
- LZ4 프레임 형식(`lz4_Frame_format.md`): 매직 `0x184D2204`, 블록 최대 크기 64KB·256KB·1MB·4MB 중 하나, 선택적 xxHash-32 블록·콘텐츠 체크섬, 블록 독립 플래그(독립이 아니면 앞 블록 64KB를 참조).
- LZ4_HC: CPU 시간을 더 써서 비율을 올리는 고압축 변형이다. README는 "모든 버전이 같은 해제 속도"라고 적는다.
- LZ4도 사전 압축을 지원한다. 어떤 파일이든 사전으로 쓸 수 있지만 마지막 64KB만 쓰인다(README). offset 상한 65535와 같은 이유다.
- 이 환경에는 lz4 CLI가 없다(설치하지 않음). 속도·비율은 lz4 README의 lzbench 표(Silesia 코퍼스, Core i7-9700K)를 인용만 한다: LZ4 1.9.0 기본 비율 2.101, 압축 780MB/s, 해제 4970MB/s.

### 3. zstd 프레임 구조 (RFC 8878)

```text
  zstd 프레임
  ┌─────────┬───────────────────────────────────────┬─────────┬─────────┬──────────────┐
  │ Magic   │ Frame_Header (2~14바이트)              │ Block   │ Block … │ [Checksum 4] │
  │28 b5 2f fd│ FHD │ [Window_Desc] │ [Dict_ID] │ [FCS] │         │ (마지막) │ XXH64 하위32 │
  └─────────┴───────────────────────────────────────┴─────────┴─────────┴──────────────┘
  블록 크기 ≤ min(Window_Size, 128KB)

  압축 블록 하나 = Literals 섹션 + Sequences 섹션
    Literals:  리터럴 바이트들 (Raw / RLE / 허프만 / 직전 허프만표 재사용)
    Sequences: (리터럴 길이, 매치 길이, offset) 세 줄을 FSE로 부호화
               offset 1~3 = "최근 쓴 offset 재사용"(repeat offsets, 사전 없는 첫 블록 초기값 1·4·8,
                            리터럴 길이 0이면 한 칸 밀려 3 = 최근 offset − 1)
```

- 매직 `0xFD2FB528`(리틀 엔디언이라 파일에는 `28 b5 2f fd`, 아래 실험의 `xxd`).
- *Frame_Content_Size(FCS)*: 원래 크기. **선택 필드**다. 스트림으로 압축하면 크기를 미리 몰라 빠진다(실험).
- *Window_Size*: 해제기가 잡아야 할 최소 버퍼. RFC는 디코더가 8MB까지 지원하고 인코더가 8MB를 넘지 않기를 **권고**한다(§3.1.1.1.2). 디코더는 너무 큰 윈도를 거부해도 된다.
- *Dictionary_ID*: 이 프레임을 풀 때 필요한 사전 번호. 디코더가 맞는 사전인지 확인하는 데 쓴다(§5).
- *Content_Checksum*: 원본의 XXH64 하위 4바이트(§3.1.1).
- *repeat offset*: 구조화 데이터는 같은 거리가 반복된다(같은 필드 간격). 최근 offset 3개를 기억해 1~3이라는 작은 값으로 다시 쓴다(§3.1.1.5).

### 4. ANS/FSE — 기호당 소수 비트

33번의 허프만은 기호마다 **정수 비트**를 쓴다. 90%짜리 기호에도 1비트가 든다.\
ANS는 상태 하나(정수 x)에 기호를 계속 "쌓아" 기호당 소수 비트를 쓴다.

```text
  rANS 인코딩 (빈도 합 M = 4096, 기호 s의 빈도 f_s, 누적 시작 c_s)

     x  ──[기호 s]──▶  x' = (x / f_s) · M + (x mod f_s) + c_s
                       (흔한 기호: f_s 큼 → x가 조금 커짐 → 적은 비트)
                       (드문 기호: f_s 작음 → x가 많이 커짐 → 많은 비트)
     x가 너무 커지면 하위 바이트를 내보내 범위를 유지한다 (재정규화)

  디코딩: slot = x mod M → slot이 속한 구간으로 기호 s 판별
          x = f_s · (x / M) + slot − c_s   ← 인코딩의 역연산
  인코딩은 마지막 기호부터, 디코딩은 첫 기호부터 (스택처럼 거꾸로)
```

- *ANS(Asymmetric Numeral Systems)*: Duda(2013)의 엔트로피 부호. 산술 부호에 가까운 비율을 허프만에 가까운 속도로 내는 것이 목표다(논문 제목 그대로: "entropy coding combining speed of Huffman coding with compression rate of arithmetic coding").
  - *rANS*: 위처럼 곱셈·나눗셈으로 상태를 바꾸는 형태.
  - *tANS*: 상태 전이를 **표**로 미리 만들어 곱셈 없이 표 조회로 하는 형태.
- *FSE(Finite State Entropy)*: zstd가 쓰는 tANS 구현. RFC 8878 §4.1
  - 상태를 기호 사이에 이어 가므로, 디코딩은 인코딩의 **반대 방향**이다. FSE 비트스트림은 끝에서부터 읽는다.
  - 디코딩 표는 크기가 2의 거듭제곱이고 칸마다 (Symbol, Num_Bits, Baseline)를 가진다. 상태 = 표의 인덱스.
- zstd는 **리터럴에는 허프만, 시퀀스(길이·offset 부호)에는 FSE**를 쓴다(RFC 8878 §3.1.1.3). 단 블록마다 고를 수 있어, 리터럴은 Raw·RLE로, 시퀀스 부호는 RLE 모드로 둘 수도 있다(§3.1.1.3.1.1·§3.1.1.3.2.1).

### 5. Brotli — 문맥 모델링 + 내장 사전 (RFC 7932)

```text
  다음 리터럴의 허프만표 선택
     직전 2바이트 (p1, p2) ──문맥 모드(LSB6·MSB6·UTF8·Signed)──▶ Context ID (0..63)
     (블록 타입, Context ID) ──context map──▶ 쓸 허프만표 번호

  역참조 거리
     거리 ≤ min(윈도, 지금까지 출력)  → 일반 LZ77 복사
     거리 >  그 값                   → 내장 정적 사전의 단어 참조
                                      (사전 122,784바이트, 단어마다 121가지 변형)
```

- 리터럴의 허프만표를 **직전 두 바이트의 문맥**으로 고른다(§7.1). 예를 들어 영어 텍스트에서 `q` 다음과 공백 다음에 올 글자의 분포가 다르다(예시) — 이런 차이를 이용한다.
- 내장 사전은 RFC 부록 A에 실린 122,784바이트 배열이다. 복사 길이 4~24의 단어를 121가지 변형(대소문자·앞뒤 덧붙임 등)으로 참조한다(§8, 부록 B).
  - 그래서 처음 보는 짧은 HTML·JS도 첫 바이트부터 "과거"가 있는 것처럼 줄어든다.
- 윈도는 2^WBITS − 16바이트, WBITS 10~24 → 최대 16MiB − 16B(§2, §9.1).
- 최소 복사 길이는 2다(§2). LZ4의 4, DEFLATE의 3보다 짧다.
- 이 환경에 brotli CLI·라이브러리가 없어 실측하지 않았다. 위 내용은 RFC 7932 근거다.

### 6. 딕셔너리 압축 — 작은 레코드에 "과거"를 빌려준다

```text
  레코드 하나만 압축       [헤더][ {"ts":"2026-10-05T12:53:20.929Z","level":"INFO",... } ]
                                   ↑ 참조할 과거가 없음 → 거의 리터럴

  딕셔너리와 함께          [ 사전 내용 (학습된 흔한 조각들) ][ 레코드 ]
                            ▲                                  │
                            └──── 역참조 (<거리, 길이>) ────────┘
                           사전은 압축 데이터에 실리지 않고 양쪽이 미리 가진다
```

- RFC 8878 §5: 사전 내용은 압축할 데이터 **앞의 과거**처럼 동작한다. 사전은 압축 결과에 포함되지 않고 "대역 밖"으로 전달된다.
  - `zstd --train`이 만든 사전 = 매직 `0xEC30A437` + Dictionary_ID + 엔트로피 표 + 내용.
  - 표까지 미리 들어 있으니 작은 레코드에서 표를 싣는 비용도 사라진다.
- zstd README: 사전 이득은 "처음 몇 KB"에서 크다. 데이터가 길어지면 압축기가 이미 푼 앞부분을 과거로 쓰기 때문이다.
- 사전은 데이터 종류별로 하나씩 둔다. "범용 사전은 없다"(README).
- JDK에도 같은 생각이 있다. zlib 프리셋 사전(`Deflater.setDictionary`) — 프레임에 사전의 Adler-32를 적고, 풀 때 확인한다(RFC 1950 FDICT·DICTID).

### 실험: 레벨별 크기·시간 (gzip·zstd·xz)

코드: `bench.py` — 각 CLI를 `subprocess`로 3번 돌려 크기, 압축 시간, 해제 시간(min~max)을 잰다. 해제 결과가 원본과 같은지 `assert`로 확인한다.

```python
for name, c, d in CODECS:
    cts, dts = [], []
    for _ in range(3):
        out, ct = run(c, data); cts.append(ct)
        back, dt = run(d, out); dts.append(dt)
        assert back == data
```

(실험, 호스트 Linux 7.0 · i7-13700HX · GNU gzip 1.12 · zstd 1.5.5 · xz 5.4.5, 모두 단일 스레드(`xz -T1`), 2026-10-05. 시간에 프로세스 시작·파이프 비용이 포함되고, 같은 호스트에서 다른 작업이 돌고 있었다)

```text
== notes.txt 3522642 bytes
codec               size  ratio  comp ms (min~max)   MB/s    decomp ms
gzip -1          1448373   2.43      194~234        18.1    83~114  
gzip -6          1209249   2.91      499~627         7.1    83~89   
gzip -9          1206528   2.92      755~776         4.7    83~87   
zstd --fast=4    1911287   1.84       55~56         64.0    19~25   
zstd -1          1440940   2.44       64~79         54.8    23~25   
zstd -3          1164010   3.03       87~113        40.4    25~28   
zstd -9          1025471   3.44      270~300        13.1    23~30   
zstd -19          914070   3.85     4325~4736        0.8    25~30   
xz -0            1198096   2.94      672~751         5.2   185~227  
xz -6             894992   3.94     4322~4687        0.8   156~169  
== log.jsonl 10506647 bytes
codec               size  ratio  comp ms (min~max)   MB/s    decomp ms
gzip -1          1952916   5.38      261~319        40.2   182~205  
gzip -6          1605436   6.54      574~601        18.3   134~189  
gzip -9          1472776   7.13     1928~2037        5.5   150~171  
zstd --fast=4    2741597   3.83       60~77        175.6    33~42   
zstd -1          1662097   6.32       87~100       120.8    33~44   
zstd -3          1685777   6.23      142~172        74.0    41~52   
zstd -9          1432906   7.33      528~641        19.9    40~61   
zstd -19         1210673   8.68    20821~23711       0.5    46~56   
xz -0            1633172   6.43     1139~1277        9.2   348~352  
xz -6            1216808   8.63    13392~13633       0.8   306~321  
```

입력은 33번과 같다(`notes.txt` = 이 저장소 한국어 노트 3.5MB, `log.jsonl` = 고정 시드 합성 JSON 로그 10.5MB).

관찰과 해석(이 두 입력·이 호스트 한정):
- **해제 시간은 레벨과 거의 무관하다.** zstd는 `--fast=4`부터 `-19`까지 notes에서 19~30ms 안에 있다(점검 재실행에서는 18~32ms — 시간은 실행마다 다르다). 압축 시간은 55ms → 4.3초로 약 80배 벌어졌다.
- notes에서 zstd -3은 gzip -6/-9보다 작고(1.16MB vs 1.21MB) 압축 시간은 약 1/6~1/9이다(87ms vs 499·755ms, 재실행에서는 91ms vs 480·669ms로 약 1/5~1/7). 해제는 약 3배 빠르다(25ms vs 83ms).
- 높은 레벨의 이득은 체감한다. log에서 zstd -9 → -19는 크기 15.5% 감소에 압축 시간 약 40배.
- 레벨이 높다고 늘 작지는 않다. log에서 zstd -1(1,662,097)이 -3(1,685,777)보다 작았다. 레벨은 "탐색에 쓰는 노력"이지 결과 크기를 보장하지 않는다.
- xz -6은 zstd -19와 비율이 비슷하지만 해제가 6배쯤 느리다(notes 156ms vs 25ms).

### 실험: 작은 레코드 · 딕셔너리 · 배치

코드: `dict.py` — `log.jsonl` 앞 2,000줄을 한 줄씩 파일로 만들어 `zstd --train --maxdict=16384`으로 사전 v1을 학습한다. 50,001~51,000번째 줄 1,000개를 시험 집합으로 쓴다. 앞 1,000줄로 사전 v2(8KB)를 따로 만든다.

```text
zstd --train train/*.json -o v1.dict --maxdict=16384
zstd -3 -c -D v1.dict < one_record.json
zstd -dc -D v2.dict one.zst
```

(실험, 호스트 zstd 1.5.5 · GNU gzip 1.12, 2026-10-05)

```text
train v1 ok
dict v1 size: 16384
1000 records, raw 175240 bytes (avg 175 B/record)
  gzip -6 each        :  159835 bytes  ratio 1.10
  zstd -3 each        :  159773 bytes  ratio 1.10
  zstd -3 each + dict :   57874 bytes  ratio 3.03
  zstd -3 batch(1000) :   28355 bytes  ratio 6.18
decode with v1 dict: exit=0 b'{"ts": "2026-10-05T12:53:20.929Z", "level": "INFO", "user": '
decode with v2 dict: exit=1 /alg-33/dict/one.zst : Decoding error (36) : Dictionary mismatch
decode with no dict: exit=1 /alg-33/dict/one.zst : Decoding error (36) : Dictionary mismatch
...
DictID: 1730221198
Window Size: 2.00 MiB (2097152 B)
Compressed Size: 58 B (58 B)
Check: XXH64 eae1dfc7
```

(오류 줄의 경로 앞부분은 출력에서 잘렸다. `zstd -lv` 머리 줄 일부는 생략)

관찰과 해석:
- 175바이트 레코드를 하나씩 압축하면 gzip·zstd 모두 **1.10배**뿐이다.
- 사전을 쓰면 3.03배, 1,000개를 모아 한 번에 압축하면 6.18배다. 배치가 가능하면 배치가 가장 좋다. 레코드 단위 접근이 필요하면(키-값 저장, 개별 메시지) 사전이 대안이다.
- 다른 사전(v2)이나 사전 없이 풀면 `Dictionary mismatch`로 **실패**한다. 프레임에 DictID(1730221198)가 적혀 있어 디코더가 확인한다.

같은 생각을 JDK만으로 — `DeflateDict.java`(zlib 프리셋 사전, 사전 = 앞 150줄 이어 붙인 26,320바이트):

```java
Deflater d = new Deflater(6);
d.setDictionary(dict);              // 압축 전에 "과거"를 넣는다
...
Inflater inf = new Inflater();
inf.setInput(z);
int n = inf.inflate(out);
if (n == 0 && inf.needsDictionary()) {   // 프레임이 사전을 요구 (getAdler()로 기대 Adler-32 확인)
    inf.setDictionary(dict);              // Adler-32가 다르면 IllegalArgumentException
    n = inf.inflate(out);
}
```

(실험, OpenJDK 21.0.12 temurin `--cpus=2`, 2026-10-05. `readAllLines`로 읽어 줄바꿈이 빠지므로 원본 합이 위보다 1,000바이트 작다)

```text
dict v1 26320 bytes adler=1007a812, v2 adler=acad7402
1000 records raw=174240  deflate each=145727 (1.20)  deflate+dict=49628 (3.51)
  needsDictionary=true, frame wants Adler-32 1007a812
decode with v1: {"ts": "2026-10-05T12:53:20.929Z", "leve
  needsDictionary=true, frame wants Adler-32 1007a812
decode with v2: IllegalArgumentException: null
  needsDictionary=true, frame wants Adler-32 1007a812
decode without: (no dictionary given)
```

- 사전 없이 1.20배 → 사전으로 3.51배. zstd 실험과 같은 방향이다(zlib 포장은 gzip보다 헤더·꼬리가 12바이트 작아 "each" 값이 더 작다).
- 틀린 사전은 `IllegalArgumentException`(메시지 `null`)이다. 메시지가 비어 있어 로그만 보고는 원인을 알기 어렵다. 기대 Adler-32를 함께 로그에 남겨야 한다.

### 실험: ANS가 허프만의 1비트 벽을 넘는다

코드: `Rans.java` — 바이트 단위 재정규화 rANS(상태 x ∈ [2²³, 2³¹), M = 2¹²). 기호 2종, p(a) = 0.9 / 0.99 / 0.5, 1,000,000기호. 왕복(인코딩 → 디코딩) 일치를 확인한다.

```java
// 인코딩: 마지막 기호부터
for (int i = n - 1; i >= 0; i--) {
    int s = sym[i];
    long xMax = ((L >> SCALE) << 8) * freq[s];
    while (x >= xMax) { out[--pos] = (byte) x; x >>>= 8; }   // 재정규화
    x = ((x / freq[s]) << SCALE) + (x % freq[s]) + start[s];
}
// 디코딩: 첫 기호부터
int slot = (int) (y & (M - 1));
int s = slot < f0 ? 0 : 1;
y = freq[s] * (y >>> SCALE) + slot - start[s];
while (y < L) y = (y << 8) | (enc[ip++] & 0xff);
```

(실험, OpenJDK 21.0.12 temurin `--cpus=2`, 2026-10-05)

```text
p=0.90 n=1000000  entropy=0.4690 bits/sym -> 58625 bytes
huffman (1 bit/sym minimum)          -> 125000 bytes
rANS                                 -> 58573 bytes (0.4686 bits/sym) roundtrip=true
p=0.99 n=1000000  entropy=0.0808 bits/sym -> 10100 bytes
huffman (1 bit/sym minimum)          -> 125000 bytes
rANS                                 -> 10132 bytes (0.0811 bits/sym) roundtrip=true
p=0.50 n=1000000  entropy=1.0000 bits/sym -> 125000 bytes
huffman (1 bit/sym minimum)          -> 125000 bytes
rANS                                 -> 125004 bytes (1.0000 bits/sym) roundtrip=true
```

- p = 0.9에서 허프만은 125,000바이트, rANS는 58,573바이트다. 엔트로피 근처까지 간다.
  - p = 0.9 줄의 rANS가 "엔트로피" 줄보다 조금 작은 것은 엔트로피 줄이 모델 확률 0.9로 계산한 기댓값이고, 실제 표본의 a 비율이 0.9에서 약간 벗어났기 때문이다.
- p = 0.5에서는 둘 다 1비트다. 치우침이 없으면 ANS도 이득이 없다. 끝의 4바이트 차이는 최종 상태를 싣는 비용이다.
- 이 차이가 zstd가 길이·offset 부호에 FSE를 쓰는 이유다. 그 기호들은 소수 값에 크게 몰려 있다.

### 실험: 프레임 — 스트리밍이면 원래 크기가 빠진다, 윈도가 크면 거부된다

(실험, 호스트 zstd 1.5.5, 2026-10-05)

```text
$ zstd -3 log.jsonl -o log.jsonl.zst ; zstd -lv log.jsonl.zst
Window Size: 2.00 MiB (2097152 B)
Compressed Size: 1.61 MiB (1685781 B)
Decompressed Size: 10.0 MiB (10506647 B)
Check: XXH64 04704c49

$ cat log.jsonl | zstd -3 -c > piped.zst ; zstd -lv piped.zst
Window Size: 2.00 MiB (2097152 B)
Compressed Size: 1.61 MiB (1685777 B)
Check: XXH64 04704c49
                                         ← Decompressed Size 줄이 없다 (FCS 생략)
$ xxd piped.zst | head -1
00000000: 28b5 2ffd 0458 4c94 02ca cc73 8526 204f  (./..XL....s.& O
```

- 파일 입력은 크기를 알아 FCS를 적는다. 파이프 입력은 모르므로 빠진다. 받는 쪽은 "몇 바이트를 할당할지" 프레임만 보고 알 수 없다. 스트리밍으로 조금씩 풀어야 한다.

```text
$ for i in $(seq 20); do cat log.jsonl; done | zstd -1 -c | wc -c
33240383
$ for i in $(seq 20); do cat log.jsonl; done | zstd --long=30 -1 -c > big.zst   # 1.65MB
$ zstd -dc big.zst > /dev/null
big.zst : Decoding error (36) : Frame requires too much memory for decoding
big.zst : Window size larger than maximum : 1073741824 > 134217728
big.zst : Use --long=30 or --memory=1024MB
$ zstd -dc --long=30 big.zst | wc -c
210132940
```

- 같은 10.5MB 로그를 20번 이어 붙인 210MB. 레벨 1의 기본 윈도(2^19 = 512KB, `clevels.h`)로는 10.5MB 뒤의 반복에 닿지 못해 33.2MB다. 1 GiB 윈도(`--long=30`)로는 1.65MB가 된다.
- 대신 해제기도 1 GiB 윈도를 잡아야 한다. zstd CLI는 기본 해제 메모리 한도 128MiB(134,217,728)를 넘는 프레임을 거부한다(man `--memory`). 윈도는 **압축률과 해제 쪽 메모리의 거래**다.

### 실험: 이미 압축된 데이터·무작위

(실험, 호스트 gzip 1.12 · zstd 1.5.5 · xz 5.4.5, 2026-10-05)

```text
orig 10506647 gz 1472776 zst 1685781
gz -> zstd -3: 1472825  gz -> gzip -9: 1473019  gz -> xz -6: 1472908
random.bin 2000000 -> zstd -19: 2000061 xz -6: 2000160
```

- gzip 결과를 다시 zstd·gzip·xz로 압축해도 모두 49~243바이트 **커졌다**. 코덱을 바꿔도 같다.
- 무작위 2MB는 zstd -19로도 61바이트 커졌다.

## 쓰이는 자료구조·알고리즘

이 주제가 쓰는 하위 구조:
- **해시 매치 파인더** — zstd는 레벨에 따라 해시 표(fast·dfast) → 해시 체인·행 해시(greedy·lazy 계열, `zstd_lazy.c`의 `ZSTD_HcFindBestMatch`·`ZSTD_RowFindBestMatch`) → 이진 트리(`ZSTD_BtFindBestMatch`)로 바뀐다(zstd 1.5.5 소스). 원리는 [33번 §3](../33-lossless-compression-lz77-huffman/2-summary.md).
- **ANS/FSE** — 상태 기계 엔트로피 부호. tANS는 2의 거듭제곱 크기 표 조회(RFC 8878 §4.1).
- **정규 허프만** — zstd 리터럴, Brotli 접두사 부호. [33번 §5](../33-lossless-compression-lz77-huffman/2-summary.md)
- **사전 학습 딕셔너리** — 샘플에서 자주 나오는 조각을 고른 바이트 배열 + 엔트로피 표.
- **문맥 모델링** — 직전 바이트로 확률표를 고르는 조건부 분포(Brotli §7).
- **체크섬** — xxHash(zstd XXH64, LZ4 xxh32), 손상 검출용이고 보안 해시가 아니다.

이 주제를 쓰는 곳(🔧):
- Kafka 프로듀서 배치 압축 — [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) · 배치 크기와 왕복 — [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md)
- HTTP `br`·`zstd`, 공유 사전(`dcb`·`dcz`) — [network/39-http-content-encoding](../../network/39-http-content-encoding/2-summary.md)
- TOAST 압축의 LZ4 선택지(PostgreSQL `default_toast_compression` — 기본 `pglz`, `--with-lz4` 빌드에서 `lz4` 선택 가능, PostgreSQL 문서 runtime-config-client) — [database/06-pages-and-tuple-layout](../../database/06-pages-and-tuple-layout/2-summary.md) · 컬럼 저장 압축 — [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md)
- 측정 방법 — [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 코덱·레벨 고르기 (순서대로 묻는다)

```text
  ① 압축이 이득인 데이터인가?        아니면(이미 압축·암호문·작은 메시지 단독) → 끈다
  ② 해제 쪽이 무엇을 지원하나?       브라우저/상대 서비스의 코덱·사전 지원 확인 (협상: network/39)
  ③ 압축은 몇 번, 해제는 몇 번?
        한 번 압축·여러 번 해제 (정적 자원, 백업, 배포 아티팩트) → 높은 레벨 (zstd -19, br 11, xz)
        요청마다 압축 (동적 응답, RPC, 로그 전송)               → 낮은 레벨 (zstd -1~3, lz4, gzip -1~5 (예시))
  ④ 레코드가 작은가?                 배치 가능 → 배치 압축 / 레코드 단위 접근 필요 → 사전
  ⑤ 내 데이터로 잰다                 레벨별 크기·압축 시간·해제 시간 (위 bench.py 같은 방식)
```

- 문서의 벤치마크(lzbench, Silesia)는 그 코퍼스·CPU의 값이다. 우리 데이터에서는 순서가 바뀔 수 있다(위 실험: zstd -1 < -3).

### 2. Java에서

- JDK에는 DEFLATE(`java.util.zip`)만 있다. zstd·LZ4·Brotli는 외부 라이브러리다.
  - Kafka는 `com.github.luben:zstd-jni`, `at.yawk.lz4:lz4-java`, `org.xerial.snappy:snappy-java`를 쓴다(apache/kafka trunk `gradle/dependencies.gradle`, 2026-10-05 확인).
- Kafka 프로듀서 설정(값은 (예시)):

```java
Properties p = new Properties();
p.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "zstd");   // none·gzip·snappy·lz4·zstd
p.put(ProducerConfig.LINGER_MS_CONFIG, 20);              // 모아서 보낼 시간 (예시)
p.put(ProducerConfig.BATCH_SIZE_CONFIG, 64 * 1024);      // 배치 크기, 기본 16384 (예시 값)
// trunk 소스에는 compression.zstd.level 등 레벨 설정도 있다
```

  - `COMPRESSION_TYPE_DOC`: "Compression is of full batches of data, so the efficacy of batching will also impact the compression ratio." 배치가 작으면(위 "each" 실험처럼) 비율이 떨어진다.

### 3. 진단

- `zstd -lv file.zst` — DictID, Window Size, 원래 크기(FCS) 유무, 체크섬.
- `xxd file | head -1` — 매직으로 코덱 식별: zstd `28b52ffd`, LZ4 프레임 `04224d18`(0x184D2204 리틀 엔디언), gzip `1f8b`.
- 지표: 압축률(원래/압축), 압축 CPU 시간, p99 지연. 압축률이 1.0 근처면 끈다.
- CPU 프로파일에서 압축 함수가 상위에 보이면 레벨부터 의심한다. 예: zstd `ZSTD_compressBlock_btlazy2`·`ZSTD_compressBlock_greedy`(1.5.5 `zstd_lazy.c`), zlib `deflate_slow`·`deflate_fast`(`deflate.c`). 함수 이름은 버전에 따라 바뀔 수 있다.

## 장애 시나리오와 대처

### 1. 최고 레벨 고정 → CPU 병목·꼬리 지연

- **현상**: "작을수록 좋다"며 동적 응답·로그 전송에 최고 레벨을 켰더니 처리량이 떨어지고 p99가 뛴다.
- **보이는 형태**: CPU 사용률 포화, 프로파일 상위에 압축 함수, 요청 지연 p99 상승, 프로듀서 쪽 배치 대기 증가. 실험에서 zstd -19는 log를 0.5MB/s로 압축했다(-3은 74MB/s).
- **원인**: 높은 레벨은 매치 탐색·파싱에 쓰는 노력을 크게 늘린다. 크기 이득은 체감한다(-9 → -19: 15.5% 감소에 약 40배 시간). Brotli CLI는 **기본이 최고 품질 11**이라, 정적 빌드용 설정을 동적 응답에 그대로 옮기면 이 상황이 된다.
- **대처**: 요청마다 하는 압축은 낮은 레벨(zstd 1~3, lz4) · 높은 레벨은 빌드 시 한 번(정적 `.br`·`.zst`) · 레벨 변경 전후로 내 데이터 벤치 · 압축 CPU를 지표로.

### 2. 공유 딕셔너리 버전 불일치 → 해제 실패

- **현상**: 사전을 새로 학습해 배포한 뒤 일부 소비자가 메시지를 못 푼다. 또는 오래된 저장 데이터를 못 연다.
- **보이는 형태**: zstd `Decoding error (36) : Dictionary mismatch`(실험), JDK zlib `IllegalArgumentException`(메시지 `null`, 실험), 소비 지연·DLQ 증가.
- **원인**: 프레임은 사전 자체는 싣지 않고 기껏해야 사전 ID(zstd DictID — 선택 필드라 없을 수도 있다, RFC 8878 §3.1.1.1.3 · zlib Adler-32)만 싣는다(RFC 8878 §5 "대역 밖"). 생산자·소비자·저장 데이터가 서로 다른 사전 버전을 본다.
- **대처**: 사전에 버전 ID를 붙여, 그 사전으로 압축된 데이터가 남아 있는 동안 **과거 버전을 보관** · 소비자가 새 사전을 먼저 받은 뒤 생산자 전환(호환 배포 순서) · 해제 실패 시 DictID를 로그에 남김 · 장기 저장 데이터는 사전 없이 압축하거나 사전을 함께 보관.

### 3. 작은 레코드를 하나씩 압축 → 비율 저하

- **현상**: 메시지마다 압축을 켰는데 트래픽·저장이 거의 안 준다.
- **보이는 형태**: 압축률 1.1 근처(실험: 175바이트 레코드 1.10배), CPU만 증가.
- **원인**: 레코드 하나 안에는 참조할 과거가 없다. 프레임 헤더·체크섬 비용이 상대적으로 크다.
- **대처**: 배치 압축(실험 6.18배 — Kafka처럼 배치 단위) · 레코드 단위 접근이 필요하면 학습 사전(3.03배) · 배치 지연(`linger.ms`)과 크기의 거래를 정한다.

### 4. 큰 윈도로 압축한 데이터를 다른 곳에서 못 푼다

- **현상**: 백업을 `--long`으로 압축해 크기를 크게 줄였는데, 복구 서버나 다른 도구에서 해제가 거부된다.
- **보이는 형태**: `Frame requires too much memory for decoding` / `Window size larger than maximum : 1073741824 > 134217728`(실험).
- **원인**: 윈도가 크면 해제 쪽도 그만큼 메모리를 잡아야 한다. 디코더는 너무 큰 윈도를 거부할 수 있다(RFC 8878 §3.1.1.1.2, HTTP용은 8MB 상한 — RFC 9659, network/39).
- **대처**: 상호 운용이 필요한 데이터는 윈도 8MB 이하 · 큰 윈도를 쓰면 해제 쪽 설정(`--long=N`·`--memory`)을 복구 절차 문서에 함께 적는다 · 해제 메모리 상한은 폭탄 방어이기도 하므로 무작정 올리지 않는다.

### 5. 이미 압축된 데이터를 다른 코덱으로 다시 압축

- **현상**: "zstd가 더 좋다니까" gzip 파일·이미지 묶음을 zstd로 다시 감쌌더니 줄지 않는다.
- **보이는 형태**: 크기 변화 +수십 바이트(실험: gz → zstd +49바이트), CPU 시간만 소비.
- **원인**: 잘 압축된 결과는 무작위에 가깝다. 코덱을 바꿔도 남은 반복이 거의 없다(33번 세는 논증). 예외: DEFLATE 무압축 블록(RFC 1951 §3.2.4)처럼 원본 바이트가 그대로 든 경우, 32KB 윈도 밖 반복은 큰 윈도 코덱이 줄일 수 있다(판정 시 확인: 무작위 100KB를 두 번 이은 200,000바이트 → gzip -9 200,060 → zstd -3 100,125바이트, 호스트 gzip 1.12·zstd 1.5.5).
- **대처**: 원본(풀린 데이터)에서 새 코덱으로 압축 · 압축 대상 선별(Content-Type, 확장자) · 압축률 지표.

## 핵심 문장

- 현대 코덱의 레벨은 "압축기가 탐색에 쓰는 노력"이다. 압축 시간은 수십 배 벌어지고 크기 이득은 체감하며, 해제 속도는 거의 그대로다.
- LZ4는 엔트로피 단계를 빼고 바이트 정렬 형식으로 속도를, zstd는 큰 윈도·허프만+FSE·사전으로 넓은 범위를, Brotli는 문맥 모델링과 내장 사전으로 웹 텍스트 비율을 노린다.
- ANS(FSE)는 상태 하나에 기호를 쌓아 기호당 소수 비트를 쓴다. 허프만의 1비트 벽을 넘는다.
- 작은 레코드는 과거가 없어 안 줄어든다. 배치로 모으거나, 과거를 빌려주는 사전을 쓴다. 사전은 프레임에 실리지 않으므로 버전 관리가 곧 해제 가능성이다.
- 윈도·FCS·사전 ID·체크섬은 프레임에 적힌 "해제 계약"이다. 큰 윈도는 해제 쪽 메모리를 요구하고, 스트리밍 프레임에는 원래 크기가 없을 수 있다.

## 관련 주제·근거

선행·후속:
- 선행: [algorithm/33-lossless-compression-lz77-huffman](../33-lossless-compression-lz77-huffman/2-summary.md)
- 관련: [systems/kafka-why-fast](../../systems/kafka-why-fast/2-summary.md) · [network/39-http-content-encoding](../../network/39-http-content-encoding/2-summary.md) · [network/43-compression-side-channels](../../network/43-compression-side-channels/2-summary.md) · [network/44-websocket-compression](../../network/44-websocket-compression/2-summary.md) · [database/06-pages-and-tuple-layout](../../database/06-pages-and-tuple-layout/2-summary.md) · [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md) · [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) · [reliability/40-batching-and-round-trips](../../reliability/40-batching-and-round-trips/2-summary.md) · [algorithm 영역 표](../curriculum.md)

근거:
- RFC 8878 Zstandard — §3.1.1(프레임, 매직, XXH64 체크섬) · §3.1.1.1.2(Window_Size, 8MB 권고) · §3.1.1.2.4(블록 ≤ min(윈도, 128KB)) · §3.1.1.3(리터럴 허프만·시퀀스) · §3.1.1.5(repeat offsets 1·4·8) · §4.1(FSE) · §5(사전 형식·대역 밖 전달) — https://www.rfc-editor.org/rfc/rfc8878
- RFC 7932 Brotli — §2(윈도 2^WBITS−16, 최소 복사 길이 2) · §7(문맥 모델링) · §8·부록 A·B(정적 사전 122,784바이트, 121 변형) — https://www.rfc-editor.org/rfc/rfc7932
- RFC 9659(HTTP zstd 윈도 8MB) — network/39 참고
- LZ4 Block format — https://github.com/lz4/lz4/blob/dev/doc/lz4_Block_format.md · Frame format — https://github.com/lz4/lz4/blob/dev/doc/lz4_Frame_format.md · README(lzbench 표, LZ4_HC)
- zstd README(lzbench 표, 해제 속도·사전 설명) — https://github.com/facebook/zstd · zstd 1.5.5 man page(레벨 1~19·`--ultra` 22·기본 3·`--long`·`--memory` 기본 128MiB)
- zstd 소스 v1.5.5 `lib/compress/clevels.h`(레벨 표) · `lib/zstd.h`(`ZSTD_strategy`) · `lib/compress/zstd_lazy.c`(매치 파인더) — https://github.com/facebook/zstd/tree/v1.5.5
- zlib `deflate.c`(`deflate_fast`·`deflate_slow`) — https://github.com/madler/zlib
- google/brotli `c/tools/brotli.md`(`-q` 0~11, `--best` 기본, `--lgwin` 10~24)
- J. Duda, "Asymmetric numeral systems: entropy coding combining speed of Huffman coding with compression rate of arithmetic coding", arXiv:1311.2540, 2013.
- Apache Kafka trunk `clients/.../producer/ProducerConfig.java`(`compression.type` 값과 배치 압축 문구) · `gradle/dependencies.gradle`(zstd-jni·lz4-java·snappy-java)
- RFC 1950 zlib(FDICT·DICTID 프리셋 사전)

실험 목록(코드: scratchpad `dsa/alg-33/`, 2026-10-05):
- `bench.py` — gzip·zstd·xz 레벨별 크기·시간 · 호스트(Linux 7.0, i7-13700HX, gzip 1.12, zstd 1.5.5, xz 5.4.5) · `python3 bench.py data/notes.txt data/log.jsonl`
- `dict.py` — 작은 레코드 개별/사전/배치, 사전 불일치 해제 · 호스트 zstd 1.5.5 · `python3 dict.py`
- `DeflateDict.java` — JDK zlib 프리셋 사전과 불일치 예외 · OpenJDK 21.0.12 temurin 컨테이너 `--cpus=2 --network none`
- `Rans.java` — rANS vs 허프만 1비트 하한 · 같은 컨테이너 · `java Rans.java 0.9` (0.99, 0.5)
- 프레임·윈도 — `zstd -lv`, 파이프 입력 FCS 생략, `--long=30` 해제 거부 · 호스트 zstd 1.5.5
- 재압축 — gz → zstd/gzip/xz, 무작위 → zstd -19/xz -6 · 호스트
