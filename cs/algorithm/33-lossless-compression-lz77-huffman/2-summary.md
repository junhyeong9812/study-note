# algorithm/33-lossless-compression-lz77-huffman — 무손실 압축: LZ77 + 허프만 = DEFLATE, 그리고 압축의 한계 — 정리 (힌트)

## 해결하는 문제

로그·JSON·HTML은 같은 문자열이 계속 반복된다.\
글자마다 빈도도 크게 다르다(공백·`"`·`e`는 많고 `Q`는 드물다).\
이 두 가지 "낭비"를 줄이면 저장·전송할 바이트가 준다.

  - *무손실 압축(lossless compression)*: 풀었을 때 원래 바이트와 정확히 같아지는 압축. 이미지·음성의 손실 압축(JPEG·MP3)과 다르다.

쉬운 예: 긴 문서를 손으로 베껴 쓴다고 하자.
- 이미 쓴 문장이 또 나오면 "3줄 위의 그 문장(12글자)"이라고만 적는다. → **반복 제거**
- 자주 쓰는 단어는 약자로, 드문 단어는 풀어서 쓴다. → **빈도에 맞춘 짧은 부호**

똑같은 구조다.\
앞의 것이 LZ77, 뒤의 것이 허프만 부호다.\
DEFLATE(RFC 1951)는 이 둘을 차례로 적용한다. gzip(RFC 1952)·zlib(RFC 1950)·PNG·ZIP·HTTP `Content-Encoding: gzip`의 본체가 이것이다.

실무 예:
- 10MB 로그를 gzip하면 1.5MB가 된다(아래 실험 — 이 합성 로그 기준).
- 이미 압축된 파일·암호문은 다시 압축해도 대개 줄지 않고 조금 커진다.
- 1MB짜리 압축 요청이 1GB로 풀리는 **압축 폭탄**이 메모리를 다 먹는다(DEFLATE 한 겹의 한계가 약 1032:1이라 1KB로는 약 1MB까지다).

## 동작·원리

### 1. 두 단계 파이프라인

```text
  원본 바이트
     │
     ▼
  [LZ77]  반복을 역참조로 바꾼다
     │     "Blah blah blah blah blah!"
     │       → 'B''l''a''h'' ''b' <거리5,길이18> '!'
     ▼
  기호열 (리터럴 0..255 · 길이 3..258 · 거리 1..32768 · 블록 끝 256)
     │
     ▼
  [허프만]  자주 나오는 기호에 짧은 비트열
     │
     ▼
  비트열 (블록마다: 헤더 3비트 + [동적 블록만 부호 길이표] + 데이터)
```

- LZ77이 **반복(중복 문자열)** 을 없앤다.
- 허프만이 **빈도 치우침** 을 없앤다.
- 둘은 서로 다른 낭비를 겨냥한다. 그래서 둘 다 쓴다.

### 2. LZ77 — 슬라이딩 윈도와 역참조

```text
           ◀──────── 윈도 (최근 32KB까지) ────────▶│◀─ 앞으로 볼 부분 ─▶
  ...  B  l  a  h  ␣  b  l  a  h  ␣  b  l  a  h  ...
                   ▲  ▲                 ▲
                   │  └ 일치 시작(거리 5) │ 현재 위치
                   │                    │
  출력: <거리=5, 길이=18>  = "5칸 뒤로 가서 18바이트를 복사하라"
```

- 압축기는 현재 위치에서 시작하는 문자열과 **가장 길게 일치하는 과거 위치**를 윈도 안에서 찾는다.
  - *윈도(window)*: 역참조가 닿을 수 있는 과거 범위. DEFLATE는 거리를 32K바이트, 길이를 258바이트로 제한한다(RFC 1951 §2).
  - *리터럴(literal)*: 일치를 못 찾아 그대로 내보낸 1바이트.
- 일치가 3바이트 미만이면 리터럴로 내보낸다. 길이 범위가 3..258이기 때문이다(RFC 1951 §3.2.5).

**겹치는 복사**가 핵심 묘기다.

```text
  'a' <거리1, 길이19>
  출력: a → a를 1칸 뒤에서 복사 → aa → 다시 1칸 뒤 복사 → aaa ... (20개)

  'abc' <거리3, 길이12>
  출력: abc → abcabc → abcabcabc → abcabcabcabcabc
```

- 길이가 거리보다 길어도 된다. 복사하면서 방금 쓴 바이트를 다시 읽는다.
- RFC 1951 §3.2.3의 예: 마지막 두 바이트가 X, Y일 때 `<길이 5, 거리 2>`는 X,Y,X,Y,X를 더한다.
- 그래서 같은 바이트 1GB도 역참조 몇 개로 표현된다. 압축 폭탄이 가능한 이유가 이것이다(아래 적용 3·장애 1).

### 3. 매치 파인더 — 해시 체인

모든 과거 위치와 비교하면 위치당 O(윈도 크기)라 너무 느리다.\
RFC 1951 §4가 설명하는 방법(특허가 걸리지 않은 것으로 알려진 방식)은 **3바이트 해시 체인**이다.

```text
  head[hash("bla")] ──▶ 위치 15 ──prev──▶ 위치 10 ──prev──▶ 위치 5 ──▶ -1
                        (가장 최근)                          (오래된 것)

  현재 위치 20의 앞 3바이트 "bla"
  → head에서 시작해 체인을 따라가며 실제 바이트를 비교
  → 가장 긴 일치를 고른다 (32KB보다 먼 후보는 버린다)
```

- *해시 체인(hash chain)*: 같은 해시값을 가진 과거 위치들을 최근 순으로 이은 단일 연결 리스트. 위치마다 `prev[i]`를, 해시마다 `head[h]`를 둔다.
- RFC 1951 §4의 설명
  - 체인은 단일 연결이고 지우지 않는다. 너무 오래된 일치는 그냥 버린다.
  - 최악을 피하려고 **체인을 일정 길이에서 자른다**(런타임 파라미터). 이것이 압축 "레벨"의 정체 중 하나다.
  - **게으른 매칭(lazy matching)**: 길이 N 일치를 찾은 뒤, 다음 바이트에서 더 긴 일치가 있는지 한 번 더 본다. 있으면 앞 일치를 리터럴 1개로 줄인다.
  - 가장 최근 위치부터 찾는다. 거리가 짧을수록 허프만 단계에서 부호가 짧아지기 때문이다.
- 해시 충돌이 있으니 후보마다 실제 바이트를 비교해야 한다. 해시는 "후보를 좁히는" 용도다.

### 4. 허프만 부호 — 빈도로 트리를 만든다

`ABRACADABRA`(A 5, B 2, R 2, C 1, D 1)로 만든 트리:

```text
  최소 힙에서 가장 작은 둘을 꺼내 합치기를 반복
   ① C1 + D1 → (CD)2
   ② B2 + R2 → (BR)4
   ③ (CD)2 + (BR)4 → 6
   ④ A5 + 6 → 11 (루트)

              (11)
            0/    \1
           A5      (6)
                 0/    \1
              (CD)2    (BR)4
              0/ \1    0/ \1
              C   D    B   R

  트리 부호:   A=0  C=100  D=101  B=110  R=111
  총 비트:     5·1 + 1·3 + 1·3 + 2·3 + 2·3 = 23비트   (고정 3비트 부호면 33비트)
```

- *접두사 부호(prefix code)*: 어떤 부호도 다른 부호의 앞부분이 아닌 부호. 구분자 없이 이어 붙여도 앞에서부터 하나씩 풀린다.
- *허프만 부호*: 주어진 기호 빈도에서 **평균 비트 수가 가장 작은 접두사 부호**. Huffman(1952)이 만들고, CLRS 3판 16.3이 탐욕 선택의 최적성을 교환 논증으로 증명한다.
  - 흔한 오해: "허프만이면 엔트로피만큼 줄어든다." 기호마다 정수 비트를 써야 해서 기호당 최소 1비트다. 한 기호가 90%인 원천에서 엔트로피는 0.469비트인데 허프만은 1비트다(아래 실험, 34번의 ANS가 이 한계를 넘는다).
- 같은 빈도가 여럿이면 합치는 순서에 따라 트리 모양이 달라진다. 총 비트(23비트)는 같다.
  - 예: ②에서 (CD)2와 B2를 먼저 합치면 길이가 A1·R2·B3·C4·D4가 된다. 5·1 + 2·2 + 2·3 + 1·4 + 1·4 = 23비트로 같다.

### 5. 정규 허프만 부호 — 표 대신 "길이"만 보낸다

압축된 데이터에 트리를 통째로 실으면 크다.\
DEFLATE의 동적 허프만 블록(BTYPE=10)은 **각 기호의 부호 길이만** 보낸다(RFC 1951 §3.2.2·§3.2.7). 고정 허프만 블록(BTYPE=01)은 RFC에 정해진 표를 써서 아무것도 안 보내고, 무압축 블록(BTYPE=00)은 허프만을 쓰지 않는다(§3.2.4·§3.2.6).

```text
  규칙: ① 길이가 같은 부호는 기호 순서대로 연속된 값
        ② 짧은 부호가 긴 부호보다 사전순으로 앞

  길이만 같으면 됨:  A=1  B=3  C=3  D=3  R=3
  정규 부호:         A=0  B=100  C=101  D=110  R=111
                     (트리 부호와 비트열은 다르지만 길이·총 비트는 같다)
```

- *정규 허프만 부호(canonical Huffman code)*: 부호 길이 목록만으로 복원할 수 있게 값을 정하는 방식. 받는 쪽은 길이표에서 같은 부호를 다시 만든다.
- DEFLATE에는 **최대 부호 길이 제한**이 있다. 리터럴·길이 부호와 거리 부호는 길이 0~15만 적을 수 있다(§3.2.7의 "0 - 15: Represent code lengths").
  - 평범한 허프만 트리는 이보다 깊어질 수 있다. 아래 실험에서 한국어 노트 3.5MB의 바이트 허프만 트리는 최대 깊이 21이었다.
  - 그래서 실제 압축기는 **길이 제한 허프만**을 따로 계산한다. RFC는 이 제약이 "부호 길이 계산을 복잡하게 만든다"고만 적는다.

### 6. DEFLATE 블록과 컨테이너

```text
  DEFLATE 스트림 = 블록 ... 블록(BFINAL=1)
  블록 헤더 3비트: BFINAL(1) + BTYPE(2)
     00 무압축(최대 65,535바이트)    01 고정 허프만표    10 동적 허프만표(표를 블록에 실음)

  gzip 파일(RFC 1952)
  ┌──────────────── 10바이트 ────────────────┐            ┌──── 8바이트 ────┐
  │1f 8b│CM=08│FLG│ MTIME(4) │XFL│OS│ DEFLATE 데이터 ... │ CRC32 │ ISIZE   │
  └──────────────────────────────────────────┘            └─────────────────┘
```

- 블록마다 허프만표를 새로 정할 수 있다. 데이터 성격이 바뀌면 압축기가 새 블록을 연다(§4).
- 역참조 거리는 블록 경계를 넘을 수 있다(§3.2.3).
- gzip은 헤더 최소 10바이트(파일명·주석·추가 필드·헤더 CRC 플래그가 켜지면 더 길다) + 꼬리 8바이트(CRC-32, 원래 길이 mod 2³²)를 붙인다(RFC 1952 §2.3). 그래서 `hi`(2바이트)를 gzip하면 22바이트가 된다(아래 적용의 실험).
- zlib(RFC 1950)은 2바이트 헤더 + Adler-32 4바이트 꼬리로 더 얇다. HTTP `deflate`가 이 포장이다(network/39 참고).

### 7. 압축의 한계 — 세는 논증

```text
  길이 n비트 입력:              2^n 가지
  n비트보다 짧은 출력:   2^0 + 2^1 + ... + 2^(n-1) = 2^n - 1 가지
  → 모든 n비트 입력을 더 짧게 만드는 무손실 압축기는 없다 (비둘기집)
```

- RFC 1951 §1.1도 "간단한 세기 논증으로, 어떤 무손실 압축도 모든 입력을 줄일 수는 없다"고 적는다.
  - DEFLATE의 최악 팽창은 32K 블록당 5바이트(약 0.015%)다(§1.1). 해석: 줄지 않는 블록은 무압축 블록(BTYPE=00)으로 내보내면 블록 헤더·LEN·NLEN만 더해지기 때문이다(RFC 문장은 수치만 적는다).
- *엔트로피(0차, H₀)*: 바이트를 서로 독립이라 볼 때 바이트당 필요한 평균 비트 수의 하한. H₀ = −Σ pᵢ log₂ pᵢ.
  - 흔한 오해: "H₀가 압축의 절대 한계다." H₀는 **바이트를 독립으로 볼 때**의 한계다. LZ77은 바이트 사이의 반복(문맥)을 쓰므로 H₀보다 더 줄일 수 있다(아래 실험의 gzip 열).
- 무작위 바이트·암호문은 반복도 치우침도 없다. 압축기는 줄이지 못하고 헤더만큼 커진다.

### 실험: 허프만 평균 길이 vs 엔트로피, 그리고 LZ77의 몫

코드(핵심): `Huffman.java` — 바이트 빈도 → `PriorityQueue`로 허프만 트리 → 기호별 부호 길이 → 평균 비트와 H₀ 비교.

```java
static int[] codeLengths(long[] freq) {
    PriorityQueue<Node> pq = new PriorityQueue<>(
        Comparator.comparingLong(Node::freq).thenComparingInt(Node::order));
    int order = 0;
    for (int s = 0; s < freq.length; s++)
        if (freq[s] > 0) pq.add(new Node(freq[s], s, null, null, order++));
    int[] len = new int[freq.length];
    if (pq.size() == 1) { len[pq.peek().sym()] = 1; return len; }
    while (pq.size() > 1) {                       // 가장 드문 둘을 합친다 (탐욕)
        Node a = pq.poll(), b = pq.poll();
        pq.add(new Node(a.freq() + b.freq(), -1, a, b, order++));
    }
    fill(pq.poll(), 0, len);                      // 깊이 = 부호 길이
    return len;
}
```

입력 네 개:
- `notes.txt`: 이 저장소 network·database·os 영역 `2-summary.md`를 이어 붙인 한국어 UTF-8 텍스트(3,522,642바이트).
- `log.jsonl`: 고정 시드로 만든 합성 JSON 로그 60,000줄(10,506,647바이트).
- `random.bin`: `/dev/urandom` 2,000,000바이트(암호문 대용).
- `skew.txt`: `a` 90% · `b` 10%의 무작위 문자열 1,000,000바이트.

(실험, OpenJDK 21.0.12 temurin `--cpus=2`, 2026-10-05)

```text
canonical A len=2 code=10
canonical B len=1 code=0
canonical C len=3 code=110
canonical D len=3 code=111
notes.txt    bytes=3522642 symbols=178 H0=6.0913 bits/byte huffman=6.1125 maxLen=21 -> 2691522 bytes (76.4%)
log.jsonl    bytes=10506647 symbols=56 H0=4.9596 bits/byte huffman=5.0007 maxLen=11 -> 6567618 bytes (62.5%)
random.bin   bytes=2000000 symbols=256 H0=7.9999 bits/byte huffman=8.0000 maxLen=8 -> 2000000 bytes (100.0%)
skew.txt     bytes=1000000 symbols=2 H0=0.4694 bits/byte huffman=1.0000 maxLen=1 -> 125000 bytes (12.5%)
```

같은 파일을 gzip(LZ77 + 허프만)으로 (호스트 GNU gzip 1.12):

```text
notes.txt   orig=  3522642 gzip-9=  1206538
log.jsonl   orig= 10506647 gzip-9=  1472786
random.bin  orig=  2000000 gzip-9=  2000339
skew.txt    orig=  1000000 gzip-9=    81557
```

관찰과 해석:
- 첫 네 줄은 RFC 1951 §3.2.2 예시(길이 2,1,3,3 → `10, 0, 110, 111`)를 그대로 재현한다.
- 허프만 평균은 H₀보다 조금 크다(6.1125 vs 6.0913). 허프만은 H₀ 아래로 내려가지 못한다.
- `skew.txt`에서 허프만은 기호당 1비트(125,000바이트)에 묶인다. H₀는 0.469비트다.
- **gzip은 H₀ 한계보다 훨씬 작다.** `log.jsonl`의 허프만 단독은 6.57MB인데 gzip은 1.47MB다. 차이는 LZ77이 잡은 **반복**의 몫이다. `skew.txt`도 `aaaa…` 연속을 LZ77이 묶어 허프만 단독(125,000)보다 작다(81,557).
- `random.bin`은 허프만으로도 gzip으로도 줄지 않는다. gzip은 339바이트 커졌다.
- `notes.txt`의 최대 부호 길이 21은 DEFLATE 한도 15를 넘는다. 길이 제한 허프만이 필요한 실제 사례다.

### 실험: 장난감 LZ77(해시 체인)의 토큰

코드(핵심): `Lz77.java` — 3바이트 해시 체인, 32KB 윈도, 길이 3..258, 탐욕 매칭. 체인 탐색 상한(`maxChain`)을 바꿔 본다.

```java
while (cand >= 0 && i - cand <= WINDOW && chain++ < maxChain) {
    int l = 0;
    while (l < MAX && i + l < in.length && in[cand + l] == in[i + l]) l++; // 겹침 허용
    if (l > bestLen) { bestLen = l; bestDist = i - cand; }
    cand = prev[cand];                                  // 체인의 다음(더 오래된) 후보
}
...
// 해제: 1바이트씩 복사하므로 거리 < 길이여도(겹침) 맞게 풀린다
case Ref r -> { for (int k = 0; k < r.len(); k++, n++) buf[n] = buf[n - r.dist()]; }
```

(실험, OpenJDK 21.0.12 temurin `--cpus=2`, 2026-10-05)

```text
abcabcabcabcabcX           -> abc<3,12>X  roundtrip=true
aaaaaaaaaaaaaaaaaaaa       -> a<1,19>  roundtrip=true
Blah blah blah blah blah!  -> Blah b<5,18>!  roundtrip=true
notes.txt  chain=   1 tokens=  846332 literals=  212552 refs= 633780 avgRefLen=5.2 coveredByRefs=94.0% 525ms roundtrip=true
notes.txt  chain=   8 tokens=  675564 literals=  176036 refs= 499528 avgRefLen=6.7 coveredByRefs=95.0% 290ms roundtrip=true
notes.txt  chain= 128 tokens=  621542 literals=  169192 refs= 452350 avgRefLen=7.4 coveredByRefs=95.2% 715ms roundtrip=true
notes.txt  chain=4096 tokens=  619671 literals=  168810 refs= 450861 avgRefLen=7.4 coveredByRefs=95.2% 880ms roundtrip=true
```

관찰과 해석:
- 위 세 줄은 겹치는 복사(`<1,19>`, `<3,12>`)가 실제로 풀리는 것을 보인다.
- 체인을 길게 볼수록 토큰 수가 준다(84.6만 → 62.0만). 대신 비교가 는다.
- 체인 128 → 4096에서는 토큰이 거의 줄지 않는다. **레벨을 올려도 얻는 것이 줄어드는** 모양이다(34번의 레벨 실험과 같은 모양).
- 시간 열은 한 JVM에서 차례로 잰 값이라 JIT 워밍업이 섞였다(첫 줄 525ms가 둘째 줄보다 느리다). 시간 비교에는 쓰지 않는다.

## 쓰이는 자료구조·알고리즘

이 주제가 쓰는 하위 구조:
- **최소 힙** — 허프만 트리 구성에서 "가장 작은 둘 꺼내기"를 n−1번. 기호 n개에 O(n log n)(CLRS 3판 16.3). [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **탐욕 + 교환 논증** — 허프만의 최적성 증명. [algorithm/23-greedy](../23-greedy/2-summary.md)
- **슬라이딩 윈도** — LZ77의 최근 32KB. 구현은 보통 원형 버퍼다. [algorithm/09-sliding-window](../09-sliding-window/2-summary.md)
- **해시 체인(해시 테이블 + 위치별 연결)** — 매치 파인더. 충돌이 있으므로 후보마다 바이트 비교. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **정규 허프만 부호** — 길이표만으로 부호 재구성(RFC 1951 §3.2.2).
- **CRC-32 / Adler-32** — 컨테이너의 무결성 검사값(RFC 1952 / RFC 1950).

이 주제를 쓰는 곳(🔧):
- HTTP `Content-Encoding: gzip`·`deflate` — [network/39-http-content-encoding](../../network/39-http-content-encoding/2-summary.md)
- WebSocket permessage-deflate(기본은 메시지 사이에 LZ77 윈도 유지, `*_no_context_takeover`를 협상한 방향은 메시지마다 빈 윈도 — RFC 7692 §7.1.1) — [network/44-websocket-compression](../../network/44-websocket-compression/2-summary.md)
- 압축 길이 사이드채널(CRIME·BREACH): "비밀과 추측이 일치하면 LZ77 역참조로 짧아진다" — [network/43-compression-side-channels](../../network/43-compression-side-channels/2-summary.md)
- PNG·ZIP·`java.util.zip`, 컬럼 저장 DB의 블록 압축 — [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md)
- 더 빠른/더 강한 후속 코덱(LZ4·zstd·Brotli) — [34-modern-codecs-lz4-zstd-brotli](../34-modern-codecs-lz4-zstd-brotli/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 압축할지부터 판단한다

```text
  압축이 이득          반복 많은 텍스트(JSON·로그·HTML·CSV), 큰 본문
  거의 이득 없음        이미 압축된 것(jpg·png·mp4·zip·gz), 암호문, 무작위 ID 덩어리
  오히려 손해           수십 바이트 메시지 (gzip 헤더+꼬리 18바이트)
```

- 순서: **압축 → 암호화**. 암호화한 뒤에는 무작위처럼 보여 압축이 안 된다. 단, 비밀과 공격자 입력을 함께 압축하면 길이가 새는 문제(network/43)를 따로 따진다.
- 작은 메시지는 압축을 건너뛰는 최소 길이를 둔다(nginx `gzip_min_length`, network/39 §1).

### 2. Java로 쓰기 — `java.util.zip`

```java
// 압축
byte[] gzip(byte[] in) throws IOException {
    var bos = new ByteArrayOutputStream();
    try (var gz = new GZIPOutputStream(bos)) { gz.write(in); }   // close가 꼬리(CRC32·ISIZE)를 쓴다
    return bos.toByteArray();
}
```

- `GZIPOutputStream`을 닫지(또는 `finish()`) 않으면 마지막 블록과 꼬리가 빠진다. 받는 쪽은 `java.io.EOFException: Unexpected end of ZLIB input stream`으로 실패한다(아래 장애 4의 실험).
- 레벨을 고르려면 `Deflater(level)`을 직접 쓴다. `Deflater.BEST_SPEED`(1)~`BEST_COMPRESSION`(9).

### 3. 해제에는 크기 상한을 둔다 (압축 폭탄 방어)

```java
static long safeGunzip(InputStream src, long limit) throws IOException {
    try (var in = new GZIPInputStream(src)) {
        byte[] buf = new byte[64 * 1024];
        long total = 0;
        for (int n; (n = in.read(buf)) > 0; ) {
            total += n;
            if (total > limit) throw new IOException("decompressed size exceeds limit " + limit + " bytes");
            // 여기서 buf를 처리한다 (전체를 메모리에 모으지 않는다)
        }
        return total;
    }
}
```

- gzip 꼬리의 ISIZE(원래 길이)는 **믿으면 안 된다**. 공격자가 쓴 값이고 mod 2³²다.
- `readAllBytes()`로 한 번에 푸는 코드가 폭탄에 가장 약하다.

### 실험: 작은 입력·무작위·압축 폭탄

코드: `DeflateLimits.java` — 위 `gzip`과 `safeGunzip`. 폭탄은 0 바이트 64KB를 16,384번(1 GiB) 흘려 압축한다(메모리에 1 GiB를 만들지 않음).

(실험, OpenJDK 21.0.12 temurin `--cpus=2` `-Xmx256m`, 2026-10-05)

```text
small:    2 bytes -> gzip   22 bytes
small:   11 bytes -> gzip   31 bytes
small:  100 bytes -> gzip   24 bytes
random: 1048576 bytes -> gzip 1048914 bytes
bomb: 1073741824 bytes of zeros -> gzip 1043656 bytes (ratio 1029:1)
unlimited inflate -> 1073741824 bytes
limited inflate   -> decompressed size exceeds limit 10485760 bytes
```

관찰과 해석:
- 2바이트·11바이트는 20바이트씩 커졌다. 헤더+꼬리 18바이트와 최소 DEFLATE 블록 때문이다. 같은 문자 100개는 24바이트로 줄었다.
- 무작위 1MiB는 338바이트 커졌다.
- 0으로 채운 1 GiB가 약 1MB(1029:1)로 줄었다. zlib 기술 문서는 zlib 형식(DEFLATE)의 이론 한계를 **1032:1**로 든다(길이·거리 쌍 하나가 최대 258바이트, 길이·거리 부호가 각각 최소 1비트 → 2비트에 258바이트, 8비트에 1032바이트). 측정값이 그 한계에 거의 붙었다.
- 1MB를 받아 1 GiB를 푸는 일이 `-Xmx256m` 안에서도 됐다. 스트리밍으로 버렸기 때문이다. 같은 것을 `readAllBytes()`로 받았다면 힙 256MB를 넘는다.
- 상한 10MiB를 둔 해제는 10MiB에서 멈췄다.
- 중첩 압축(zip 안의 zip)은 단계마다 배율이 곱해질 수 있다. 전체 해제 크기에 상한을 둬야 한다(이 실험은 1단만 보였다).

### 4. 코테·면접 순서

1. 빈도표 → 최소 힙 → 허프만 트리(합치기 n−1번) → 깊이 = 부호 길이 → Σ 빈도×길이.
2. "가장 작은 둘 합치기" 문제(파일 합치기 최소 비용 등)는 허프만과 같은 구조다.
3. LZ77 토큰 해석 문제는 **1바이트씩 복사**(겹침)만 지키면 된다. `System.arraycopy`로 한 번에 복사하면 거리 < 길이일 때 틀린다.

## 장애 시나리오와 대처

### 1. 압축 폭탄 — 작은 업로드가 메모리를 다 먹는다

- **현상**: 수백 KB~수 MB짜리 gzip 요청·업로드 몇 개에 서버가 죽거나 GC가 폭주한다(중첩 아카이브면 더 작은 파일로도 가능).
- **보이는 형태**: `java.lang.OutOfMemoryError: Java heap space`, 컨테이너 OOMKilled(exit 137), 디스크 가득(해제 결과를 파일로 쓸 때).
- **원인**: LZ77의 겹치는 복사로 같은 바이트 1GB를 1MB로 표현할 수 있다(DEFLATE 한계 1032:1, 실험 1029:1). 해제 코드에 출력 크기 상한이 없다.
- **대처**: 스트리밍 해제 + 누적 크기 상한(위 `safeGunzip`) · 압축률 상한(예: 100:1 넘으면 거부 (예시)) · 중첩 아카이브 깊이 제한 · ISIZE 불신. 요청 본문 압축을 받는 엔드포인트(network/39 §7)에 특히.

### 2. 작은 메시지를 압축했더니 오히려 커졌다

- **현상**: 메시지 큐·RPC에서 메시지마다 gzip을 켰더니 트래픽이 줄지 않거나 늘었다.
- **보이는 형태**: 바이트 지표가 그대로이거나 증가, CPU만 상승. 2바이트 → 22바이트(실험).
- **원인**: gzip 헤더 10 + 꼬리 8바이트 + 블록 헤더(동적 블록이면 부호 길이표). 작은 메시지 안에는 LZ77이 참조할 과거가 거의 없다.
- **대처**: 최소 길이 이하는 압축 생략 · 여러 메시지를 모아 배치 압축 · 공유 사전(34번의 zstd 딕셔너리, zlib 프리셋 사전).

### 3. 암호문·이미 압축된 데이터를 압축 — CPU만 쓴다

- **현상**: 백업·전송 파이프라인에 압축을 넣었는데 크기가 안 줄고 시간만 늘었다.
- **보이는 형태**: 압축률 ≈ 1.00, 원본보다 약간 큼(무작위 1MiB +338바이트, 실험).
- **원인**: 무작위처럼 보이는 데이터에는 반복도 빈도 치우침도 없다. 세는 논증상 모든 입력을 줄일 수는 없다.
- **대처**: 압축을 암호화보다 **먼저** · Content-Type으로 압축 대상 선별(network/39 §1) · 압축률을 지표로 남겨 1.0 근처면 끈다.

### 4. 받는 쪽이 "깨진 압축 데이터"라고 한다

- **현상**: 같은 gzip 파일이 어떤 클라이언트에선 풀리고 어떤 곳에선 실패한다.
- **보이는 형태**: OpenJDK 21에서 확인한 세 가지 —
  - gzip이 아닌 바이트: `java.util.zip.ZipException: Not in GZIP format`(첫 2바이트가 `1f 8b`가 아님)
  - 꼬리(CRC32) 손상: `java.util.zip.ZipException: Corrupt GZIP trailer`
  - 닫지 않은 스트림(꼬리 없음): `java.io.EOFException: Unexpected end of ZLIB input stream`
- **원인**: 스트림을 `close()`/`finish()` 안 해 꼬리 누락 · zlib 포장(`deflate`)과 gzip 포장 혼동 · 전송 중 잘림 · 이미 풀린 본문에 `Content-Encoding`을 그대로 남김.
- **대처**: `xxd file | head -1`로 매직 바이트 확인(gzip은 `1f8b`, zlib은 첫 바이트가 흔히 `78`) · `gzip -t`로 무결성 검사 · try-with-resources로 닫기 보장.

(실험, OpenJDK 21.0.12 temurin `--cpus=2`, 2026-10-05 — `GzErrors.java`: `flush()`만 하고 닫지 않은 스트림, 평문, CRC 1비트 손상을 각각 `GZIPInputStream`으로 읽음)

```text
unclosed stream bytes=10
read unclosed -> java.io.EOFException: Unexpected end of ZLIB input stream
read plain   -> java.util.zip.ZipException: Not in GZIP format
read bad crc -> java.util.zip.ZipException: Corrupt GZIP trailer
```

- 닫지 않은 스트림은 2,300바이트 입력인데 10바이트(gzip 헤더)만 나와 있었다. `GZIPOutputStream`의 `flush()`는 기본 설정에서 압축기 안의 데이터를 밀어내지 않는다(생성자의 `syncFlush` 기본값 false — Javadoc).

## 핵심 문장

- DEFLATE는 LZ77로 **반복**을, 허프만으로 **빈도 치우침**을 없앤다. 서로 다른 낭비라 둘 다 쓴다.
- LZ77의 역참조는 길이가 거리보다 길 수 있다(겹치는 복사). 그래서 같은 바이트 1GB가 1MB로 표현되고, 압축 폭탄이 된다 — 해제에는 크기 상한을 둔다.
- 허프만은 최적 접두사 부호지만 기호당 정수 비트라 H₀ 아래로 못 가고, 기호당 1비트 밑으로도 못 간다.
- DEFLATE의 동적 허프만 블록은 부호표 대신 부호 길이만 보내고(정규 허프만), 길이는 15비트로 제한한다.
- 어떤 무손실 압축도 모든 입력을 줄일 수 없다. 무작위·암호문·이미 압축된 데이터·아주 작은 메시지는 오히려 커진다.

## 관련 주제·근거

선행·후속:
- 선행: math/14-information-theory-basics(엔트로피 — 미작성, [math 영역](../../math/README.md)) · [algorithm/23-greedy](../23-greedy/2-summary.md)(허프만의 탐욕·교환 논증) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)(커리큘럼 ds 10)
- 후속: [algorithm/34-modern-codecs-lz4-zstd-brotli](../34-modern-codecs-lz4-zstd-brotli/2-summary.md)
- 관련: [algorithm/09-sliding-window](../09-sliding-window/2-summary.md) · [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md) · [network/39-http-content-encoding](../../network/39-http-content-encoding/2-summary.md) · [network/43-compression-side-channels](../../network/43-compression-side-channels/2-summary.md) · [network/44-websocket-compression](../../network/44-websocket-compression/2-summary.md) · [database/37-row-vs-column-storage](../../database/37-row-vs-column-storage/2-summary.md) · [algorithm 영역 표](../curriculum.md)

근거:
- RFC 1951 DEFLATE — §1.1(세는 논증·최악 팽창 32K당 5바이트) · §2(거리 32K·길이 258) · §3.2.2(정규 허프만) · §3.2.3(블록 헤더·겹치는 복사 예) · §3.2.5(길이 3..258·거리 1..32,768) · §3.2.7(부호 길이 0~15) · §4(해시 체인·게으른 매칭) — https://www.rfc-editor.org/rfc/rfc1951
- RFC 1952 gzip — §2.3(헤더 최소 10바이트, CRC32·ISIZE 꼬리) — https://www.rfc-editor.org/rfc/rfc1952
- RFC 1950 zlib — https://www.rfc-editor.org/rfc/rfc1950
- D. A. Huffman, "A Method for the Construction of Minimum-Redundancy Codes", Proc. IRE 40(9):1098–1101, 1952.
- J. Ziv, A. Lempel, "A Universal Algorithm for Sequential Data Compression", IEEE Trans. Inf. Theory 23(3):337–343, 1977 (doi:10.1109/TIT.1977.1055714).
- CLRS 3판 16.3 허프만 부호.
- zlib Technical Details("Maximum Compression Factor" 1032:1, 메모리 공식) — https://zlib.net/zlib_tech.html

실험 목록(코드: scratchpad `dsa/alg-33/`, 2026-10-05):
- `Huffman.java` — 허프만 길이 vs H₀, 정규 부호 예시 · OpenJDK 21.0.12 temurin 컨테이너 `--cpus=2 --network none` · `java Huffman.java data/notes.txt data/log.jsonl data/random.bin data/skew.txt`
- `HuffDemo.java` — `ABRACADABRA` 트리(§4 그림의 길이·23비트 확인) · 같은 환경
- `gzip -9 -c <file> | wc -c` — 호스트 GNU gzip 1.12 (Linux 7.0, i7-13700HX)
- `Lz77.java` — 해시 체인 LZ77 토큰·왕복 확인 · 같은 컨테이너 `-Xmx1g`
- `DeflateLimits.java` — 작은 입력·무작위·1 GiB 폭탄·상한 해제 · 같은 컨테이너 `-Xmx256m`
- `GzErrors.java` — 닫지 않은 스트림·평문·CRC 손상의 예외 문구 · 같은 컨테이너
