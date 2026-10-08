# math/14-information-theory-basics — 엔트로피·부호화·압축 한계·오류 검출/정정 부호 — 정리 (힌트)

## 해결하는 문제

두 질문에 숫자로 답하는 도구다.
1. 이 데이터는 **얼마까지** 줄일 수 있나 → 엔트로피
2. 비트가 몇 개 뒤집혀도 **알아채거나 고칠 수** 있나 → 해밍 거리·CRC·해밍 부호

쉬운 예: 친구에게 날씨를 매일 문자로 알린다.

```text
  맑음 50%   흐림 25%   비 12.5%   눈 12.5%

  고정 길이:  맑음=00  흐림=01  비=10  눈=11          → 하루 평균 2비트
  가변 길이:  맑음=0   흐림=10  비=110  눈=111        → 평균 0.5×1 + 0.25×2 + 0.125×3 × 2 = 1.75비트
```

- 자주 나오는 것에 짧은 부호를 주면 평균이 준다. 1.75비트보다 더 줄일 방법은 없다(아래 1절). 이 하한이 엔트로피다.
- 문자 한 글자가 깨지면 "맑음"이 "흐림"으로 읽힐 수 있다. 일부러 **남는 비트**를 붙여야 오류를 알아챈다.

똑같은 구조다.\
실무 예:
- 이미 gzip된 응답·JPEG·암호문을 다시 압축하면 대개 **줄지 않고 오히려 조금 커진다.** 남은 반복·치우침이 거의 없어 줄일 여지가 없다(같은 `.gz`를 여러 번 이어 붙인 파일처럼 반복이 있으면 준다).
- 1MB 업로드가 1GB로 풀리는 압축 폭탄은 엔트로피가 0에 가까운 데이터다.
- 디스크·네트워크는 CRC로 우연한 오류를 잡고, 서버 메모리(ECC)는 해밍 계열 부호로 1비트를 고친다.

압축 알고리즘 자체(허프만·LZ77·DEFLATE)는 [algorithm/33-lossless-compression-lz77-huffman](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md), 현대 코덱(zstd·ANS)은 [algorithm/34](../../algorithm/34-modern-codecs-lz4-zstd-brotli/2-summary.md), CRC의 선형성과 위조 불가 문제는 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) §6, 저장 장치 체크섬 운용은 [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md)에 있다. 여기서는 그 밑의 **수학**(엔트로피·부호의 한계·거리)만 다룬다.

## 동작·원리

### 1. 정보량과 엔트로피

```text
  기호      확률 p    정보량 −log₂ p     부호(접두 부호)
  맑음      1/2         1비트              0
  흐림      1/4         2비트              10
  비        1/8         3비트              110
  눈        1/8         3비트              111

  엔트로피 H = Σ p · (−log₂ p) = 0.5×1 + 0.25×2 + 0.125×3 + 0.125×3 = 1.75 비트/기호

  부호 트리 (왼쪽 0, 오른쪽 1)
        ●
      0/ \1
    맑음   ●
         0/ \1
        흐림   ●
             0/ \1
             비   눈
```

- *정보량(self-information)*: `I(x) = −log₂ p(x)`. 드문 일일수록 알았을 때 얻는 정보가 크다.
  - log의 밑이 2라 단위가 비트다. 확률 1/2짜리 사건 하나 = 1비트.
- *엔트로피*: `H(X) = −Σ p(x) log₂ p(x)`. 정보량의 기댓값이다.
  - 균등 분포에서 가장 크다. 기호가 256종(바이트)이면 최대 8비트/바이트다.
  - 한 기호만 나오면 0이다.
- *접두 부호(prefix code)*: 어떤 부호도 다른 부호의 앞부분이 아니다. 그래서 구분자 없이 이어 붙여도 하나로 읽힌다(위 트리의 잎에만 기호가 있다).
- *크래프트 부등식*: 길이 `l₁, l₂, …`인 접두 부호가 존재할 필요충분조건은 `Σ 2^(−lᵢ) ≤ 1`이다.
  - 위 예: 2⁻¹ + 2⁻² + 2⁻³ + 2⁻³ = 1.
- *원천 부호화 정리(Shannon 1948)*: 기호가 독립·동일 분포로 나오는 원천에서, 복호 가능한 부호의 기호당 평균 길이는 H 이상이다. 여러 기호를 묶어 부호화하면 H에 얼마든지 가깝게 할 수 있다.
  - 증명 아이디어: 크래프트 부등식과 깁스 부등식(`Σ p log(p/q) ≥ 0`)을 결합하면 평균 길이 ≥ H가 나온다.
  - 전제: 한 기호 엔트로피 H를 한계로 쓰는 이 형태는 기호끼리 독립·동일 분포일 때다. 실제 데이터는 기억이 있다(2절).
  - 기억 있는 원천(에르고딕 원천)에도 정리가 있고, 한계는 엔트로피율이다(Shannon 1948 정리 9). 분포를 미리 몰라도 보편 부호(LZ77 등)가 데이터를 보며 그 한계에 다가간다(Ziv·Lempel 1977).
- 허프만 부호가 이 평균 길이를 기호 단위에서 최소로 만든다. 다만 기호마다 정수 비트를 써서 H보다 클 수 있다. 확률이 2의 거듭제곱(위 예)이면 정확히 H다. 자세히는 [algorithm/33](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md).

### 2. 0차 엔트로피 H₀는 "한계"가 아니다

```text
  H₀ = 바이트를 서로 독립이라 보고 센 엔트로피 (바이트 빈도만 봄)

  무기억 원천   a b a a c a b d …  각 바이트가 독립       → 압축 한계 ≈ H₀
  기억 있는 원천 "ab" "cd" "dc" "aa" 쌍으로만 나옴         → 실제 정보 < H₀
  자연어 텍스트  "트랜잭션"이 나오면 다음도 예측 가능      → 실제 정보 ≪ H₀
```

- *엔트로피율(entropy rate)*: 앞 기호들을 알 때 다음 기호가 주는 평균 정보. 기억이 있는 원천의 진짜 압축 한계다.
  - 실제 데이터의 엔트로피율은 모른다. 그래서 "이 데이터의 H₀가 6비트니 25%밖에 못 줄인다"는 틀린 추론이다.
- LZ77은 반복된 **문자열**을 역참조로 바꿔 문맥을 활용한다. 그래서 텍스트에서는 H₀ 하한보다 더 작게 줄인다.

#### 실험: H₀ 하한 vs gzip 결과

- Python 표준 라이브러리 `gzip`(level 9, `mtime=0`)로 압축하고, 바이트 빈도로 H₀를 계산했다.
- 코드 핵심(`entropy.py`):

```python
def h0(b: bytes) -> float:
    n = len(b); c = collections.Counter(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())

g = gzip.compress(b, compresslevel=9, mtime=0)
print(..., H * len(b) / 8, len(g))          # H₀ 하한(바이트) vs gzip 크기

syms  = random.choices(b'abcd', weights=[4, 2, 1, 1], k=1_000_000)        # 무기억, H = 1.75
pairs = random.choices([b'aa', b'ab', b'cd', b'dc'], weights=[1,1,1,1], k=500_000)  # 쌍 구조, 실제 1 bit/B
```

(실험, Python 3.12.3 호스트, 2026-10-07 — `random.seed(2026)`. `os.urandom` 줄만 실행마다 수 바이트 다르다)

```text
한국어 마크다운 노트                           26,417 B  H0=6.181 bit/B  H0 하한=     20,411 B  gzip=   10,458 B  gzip/H0하한= 0.51
노트.gz 를 다시 gzip                       10,458 B  H0=7.979 bit/B  H0 하한=     10,430 B  gzip=   10,481 B  gzip/H0하한= 1.00
os.urandom (암호문 대용)                1,000,000 B  H0=8.000 bit/B  H0 하한=    999,979 B  gzip=1,000,328 B  gzip/H0하한= 1.00
무기억 4기호 (H=1.75 이론)                1,000,000 B  H0=1.749 bit/B  H0 하한=    218,609 B  gzip=  263,115 B  gzip/H0하한= 1.20
쌍 구조 원천 (실정보 1 bit/B)              1,000,000 B  H0=1.906 bit/B  H0 하한=    238,235 B  gzip=  165,354 B  gzip/H0하한= 0.69
한 기호만 1MB (H0=0)                   1,000,000 B  H0=-0.000 bit/B  H0 하한=         -0 B  gzip=    1,004 B  gzip/H0하한=  inf
```

- 관찰 1 — 텍스트: gzip 결과(10,458 B)가 H₀ 하한(20,411 B)의 절반이다. 텍스트는 기억 있는 원천이라 H₀가 한계가 아니다.
- 관찰 2 — 무기억 원천: gzip이 H₀ 하한보다 20% 크다. 이 원천에서는 H₀가 진짜 한계이고, gzip(DEFLATE)은 거기에 못 미친다.
  - 초과분 나누기(사실 점검 추가 실험, raw DEFLATE level 9): LZ77 매치를 끄고 허프만만 쓰면(`zlib.Z_HUFFMAN_ONLY`) 234,539 B(약 1.88 bit/B), 기본 설정은 263,004 B다. 블록 헤더·부호표는 수 % 이하다.
  - 해석: 허프만만 써도 남는 약 7%는 DEFLATE 부호 알파벳에 블록 끝(EOB) 기호가 함께 들어가 4기호가 1·2·3·3비트 대신 1·2·3·4비트(평균 1.875)를 받기 때문으로 본다(1.875 bit × 100만 / 8 = 234,375 B와 거의 같다). 나머지 약 12%는 무작위 데이터에서 우연히 맞는 짧은 LZ77 매치를 길이·거리 부호로 적는 비용이다.
- 관찰 3 — 쌍 구조: 실제 정보는 1 bit/B(쌍 4종 = 쌍당 2비트)인데 H₀는 1.906이다. gzip은 H₀ 하한 아래로 갔지만 1 bit/B 하한(125,000 B)에는 못 미쳤다.
- 관찰 4 — 무작위·이미 압축된 것: H₀가 8에 붙어 있다. gzip이 오히려 키웠다(무작위 +328 B, `.gz` 재압축 +23 B).
- 관찰 5 — H₀ = 0(한 바이트 반복): 1,000,000 B → 1,004 B, 약 1,000:1이다. DEFLATE 한 겹의 상한 근처다(algorithm/33의 약 1032:1). 압축 폭탄의 재료다.
- `H0=-0.000`은 `−0.0`이 출력된 것이다(부동소수 음의 0 — 값은 0).

### 3. 어떤 압축기도 모든 입력을 줄이지 못한다

```text
  길이 n비트 입력:        2ⁿ 개
  n비트보다 짧은 출력:    2⁰ + 2¹ + … + 2ⁿ⁻¹ = 2ⁿ − 1 개   ← 하나 모자란다

  비둘기집: 무손실(서로 다른 입력 → 서로 다른 출력)이면
  적어도 한 입력은 줄지 않는다.  실제로는 대부분의 무작위 입력이 줄지 않는다.
```

- 무손실 압축은 "자주 나오는 패턴"을 짧게 하는 대신 나머지를 조금 길게 하는 **재분배**다.
- 무작위 n비트 입력 중 k비트 이상 줄어드는 것의 비율은 2^(1−k) 미만이다(위 세기에서 바로 나온다: n−k비트 이하 출력은 2^(n−k+1) − 1개뿐). 10비트 이상 줄어드는 입력은 0.2% 미만이다.
- 그래서 암호문·이미 압축된 데이터는 대개 줄지 않고, 컨테이너 헤더·꼬리(gzip 최소 18바이트 — algorithm/33)와 DEFLATE 블록 비용만큼 커진다(위 무작위 1MB의 +328 B는 헤더만으로는 설명되지 않는다).
- 비둘기집 원리의 일반형은 [math/05-counting-and-birthday-bound](../05-counting-and-birthday-bound/2-summary.md).

### 4. 오류 검출·정정 — 해밍 거리

```text
  해밍 거리 d(x, y) = 다른 비트 수        d(1011, 1001) = 1

  부호어(codeword)끼리 최소 거리 d_min 이 크면 오류가 다른 부호어로 "건너가지" 못한다

     d_min = 3                                  ○ = 부호어,  · = 오류로 생기는 낱말
     ○ ── · ── · ── ○
     1비트 오류 → 가장 가까운 ○ 가 원래 것  → 정정 가능
     2비트 오류 → 반대편 ○ 에 더 가까워짐   → 잘못 정정

  검출 가능 오류 수 = d_min − 1        정정 가능 오류 수 = ⌊(d_min − 1) / 2⌋
```

- *해밍 거리*: 길이가 같은 두 비트열에서 서로 다른 자리의 수. Java에서는 `Integer.bitCount(x ^ y)`.
- *부호어*: 부호가 허용하는 비트열. 데이터 비트 + 남는(중복) 비트로 만든다.
- *최소 거리(d_min)*: 서로 다른 부호어 쌍의 해밍 거리 중 최솟값. 부호의 능력을 정한다(Hamming 1950).

| 부호 | 데이터 | 전체 | d_min | 할 수 있는 것 |
|---|---|---|---|---|
| 패리티 1비트 | k | k+1 | 2 | 1비트 오류 검출(짝수 개 오류는 못 봄) |
| 해밍(7,4) | 4 | 7 | 3 | 1비트 정정 **또는** 2비트 검출 |
| 확장 해밍(8,4) SECDED | 4 | 8 | 4 | 1비트 정정 **그리고** 2비트 검출 |

- *SECDED*: Single Error Correction, Double Error Detection. 해밍 부호에 전체 패리티 비트 하나를 더해 d_min을 4로 만든다. 서버 ECC 메모리가 쓰는 계열이다(구체 부호는 제품마다 다르다 `[?]`).

```text
  해밍(7,4) 비트 배치 — 위치 번호 1..7, 2의 거듭제곱 자리가 패리티

  위치    1   2   3   4   5   6   7
  역할    p1  p2  d1  p4  d2  d3  d4
  p1 검사 ●       ●       ●       ●       (위치 번호의 1의 자리 비트가 1인 곳)
  p2 검사     ●   ●           ●   ●       (2의 자리)
  p4 검사             ●   ●   ●   ●       (4의 자리)

  신드롬 = (p4 검사 실패, p2 실패, p1 실패)를 이진수로 읽은 값 = 틀린 위치 번호  (0이면 검사 통과)
```

- *신드롬*: 받은 낱말로 다시 계산한 패리티 검사 결과. 1비트 오류면 그 값이 곧 오류 위치다.
  - 0은 "오류 없음"이 아니라 "검사 통과"다. 오류가 1비트 이하라는 가정에서만 오류 없음으로 읽는다. 위치 1·2·3이 함께 뒤집히면 신드롬은 1 ⊕ 2 ⊕ 3 = 0이다.

### 5. CRC — 다항식 나눗셈의 나머지

```text
  메시지 비트 = GF(2) 다항식 M(x)        생성 다항식 G(x), 차수 r
  CRC = (M(x) · x^r) mod G(x)           ← r비트 나머지
  GF(2): 덧셈 = 뺄셈 = XOR, 자리올림 없음

  오류 E(x)가 섞여 R(x) = M(x)·x^r + CRC + E(x)
  → 검사 결과 = E(x) mod G(x).   E가 G의 배수일 때만 놓친다
```

- *GF(2)*: 원소가 0과 1뿐인 체. 덧셈은 XOR다.
- 검출 보장(Peterson & Brown 1961, "Cyclic Codes for Error Detection")
  - G(x)가 상수항(+1)을 가지면, 길이 r 이하의 **연속 오류(버스트)**를 모두 검출한다.
  - *버스트 오류*: 첫 뒤집힌 비트부터 마지막 뒤집힌 비트까지의 구간 길이가 L인 오류.
  - 증명 아이디어: 길이 L ≤ r 버스트는 `E(x) = xⁱ·B(x)`(B의 차수 ≤ r − 1, 상수항 1)로 쓴다. G는 상수항이 있어 x와 공약수가 없고, 차수 r인 G가 차수 r보다 낮은 B를 나눌 수 없다. 그래서 E mod G ≠ 0이다.
  - 출처 확인 범위: 논문 본문은 열지 못했다. 서지(Proc. IRE 49(1), 1961년 1월)는 Crossref, "n비트 CRC는 길이 n 이하 버스트를 모두 검출"은 Wikipedia "Cyclic redundancy check"(2차 출처)로 확인했다.
- 무작위로 크게 망가진 메시지를 놓칠 확률은 약 2^(−r)이다. 이것은 "오류 패턴이 가능한 패턴 중 고르게 무작위(신드롬이 거의 균등)"라는 **가정** 아래의 근사다. CRC-32면 약 2.3×10⁻¹⁰.
  - 오류 분포가 다르면 값도 다르다. 길이가 정확히 r+1인 버스트(안쪽 r−1비트가 고르게 무작위)는 E가 G 자체일 때만 놓치므로 2^(−(r−1))로 두 배다(위 증명 아이디어와 같은 논리 — 계산).
  - 확률이 작아도 규모가 크면 0이 아니다. 손상된 블록이 10¹⁰개면 기대 미검출은 약 2.3개다(예시 계산 — 10¹⁰ × 2⁻³²).
- CRC는 비밀 키가 없고 선형이다. 우연한 오류용이지 위조 방지용이 아니다([algorithm/12](../../algorithm/12-hash-functions/2-summary.md) §6).

#### 실험: CRC-32·CRC-8·해밍(7,4)·SECDED

- 코드 핵심(`Codes.java`):

```java
// CRC-8 (생성 다항식 x^8+x^2+x+1 = 0x07) — 비트 단위 나눗셈 그대로
static int crc8(byte[] b) {
    int c = 0;
    for (byte x : b) { c ^= (x & 0xff);
        for (int k = 0; k < 8; k++) c = (c & 0x80) != 0 ? ((c << 1) ^ 0x07) & 0xff : (c << 1) & 0xff; }
    return c;
}
// 해밍(7,4) 신드롬: 0이면 검사 통과, 아니면 (1비트 오류 가정에서) 오류 위치(1..7)
static int syndrome(int w) {
    int s1 = bit(w,1) ^ bit(w,3) ^ bit(w,5) ^ bit(w,7);
    int s2 = bit(w,2) ^ bit(w,3) ^ bit(w,6) ^ bit(w,7);
    int s4 = bit(w,4) ^ bit(w,5) ^ bit(w,6) ^ bit(w,7);
    return s1 | s2 << 1 | s4 << 2;
}
// SECDED: 신드롬 ≠ 0 인데 전체 패리티가 맞으면 짝수 개 오류 → 정정하지 않고 "정정 불가"
```

- CRC-32는 JDK `java.util.zip.CRC32`. 64바이트(512비트) 무작위 메시지에 (1) 1비트 오류 전부, (2) 2비트 오류 전부, (3) 길이 ≤ 32 버스트 20만 건을 넣었다.
- CRC-8은 메시지의 무작위 위치 4곳을 무작위 바이트로 바꾸는 훼손을 100만 번 했다.

(실험, OpenJDK 21.0.12 temurin, Docker `--cpus=2`, 2026-10-07 — `new Random(14)` 고정, 2회 실행 같은 출력)

```text
CRC-32 64B 메시지: 1비트 오류 512가지 중 미검출 0 | 2비트 오류 130816가지 중 미검출 0 | 길이≤32 버스트 200000건 중 미검출 0
CRC-8 무작위 훼손 1000000건: 미검출 3773 (0.00377, 1/256 = 0.00391)
해밍(7,4): 최소 거리 3 | 1비트 오류 112가지 중 정정 성공 112 | 2비트 오류 336가지 중 잘못 고친 것 336
확장 해밍(8,4) SECDED: 최소 거리 4 | 1비트 128가지 중 정정 128 | 2비트 448가지 중 '정정 불가' 검출 448
```

- 관찰 1: CRC-32는 이 메시지에서 1비트·2비트 오류 전부와 길이 32 이하 버스트 표본 전부를 잡았다. 버스트 결과는 Peterson & Brown의 보장과 맞는다.
- 관찰 2: CRC-8의 미검출률 0.377%는 2⁻⁸ = 0.391% 근처다. 조금 낮은 것은 표본 잡음이다. 사실 점검에서 시드만 1~5로 바꿔 돌리면 3,825~3,984건(0.383~0.398%)으로 1/256의 위아래에 고루 흩어졌다(이항 분포 표준편차 약 62건).
  - 1바이트만 실제로 바뀐 경우(길이 ≤ 8 버스트 — 검출 보장)는 세 자리가 모두 겹치거나 원래 값으로 바뀌어야 해서 100만 건 중 약 20건(사실 점검 모의 계산 18건)뿐이라, 130건 차이를 설명하지 못한다(해석 — 바이트 2개 이상이 무작위로 바뀌면 선형성 때문에 미검출 확률이 거의 정확히 2⁻⁸이다).
- 관찰 3: 해밍(7,4)는 1비트 오류 112가지를 전부 고쳤다. 2비트 오류 336가지는 **전부 다른 데이터로 잘못 고쳤다.** 오류를 고친 척하며 조용히 틀린 값을 낸다.
- 관찰 4: 전체 패리티 1비트를 더한 SECDED는 2비트 오류 448가지를 전부 "정정 불가"로 검출했다. d_min이 3 → 4가 된 효과다.

## 쓰이는 자료구조·알고리즘

- **허프만 트리(최소 힙으로 만든다)** — 엔트로피에 가까운 접두 부호. [algorithm/33-lossless-compression-lz77-huffman](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md), [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)(커리큘럼 10).
- **ANS·산술 부호** — 기호당 정수 비트 제약을 넘어 엔트로피에 더 가깝게. [algorithm/34-modern-codecs-lz4-zstd-brotli](../../algorithm/34-modern-codecs-lz4-zstd-brotli/2-summary.md).
- **CRC(표 조회·하드웨어 명령)** — 다항식 나눗셈을 바이트 단위 표로 빠르게. 저장 장치 운용은 [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md), 해시 용도 구분은 [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md).
- **해밍 부호·SECDED** — ECC 메모리·캐시. 비트 연산(`^`, `bitCount`)으로 구현. [algorithm/29-bit-manipulation](../../algorithm/29-bit-manipulation/2-summary.md), [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)(커리큘럼 35).
- **해밍 거리** — 이진 벡터 유사도(pgvector의 `<~>` 연산자, 이미지 지각 해시 비교). 벡터 거리 일반은 [13-linear-algebra-essentials](../13-linear-algebra-essentials/2-summary.md).
- **엔트로피로 키·토큰 세기 재기** — 공격자가 모르는 정도를 비트로 센다. [security/09-randomness-and-key-management](../../security/09-randomness-and-key-management/2-summary.md).

## 적용 — 풀어나가는 법

### 1. "압축을 켤까?" — 표본으로 잰다

1. **증상**: 압축을 켰는데 CPU만 늘고 전송량은 그대로이거나 늘었다.
2. **어림**: 데이터가 이미 압축 형식(gzip·zip·JPEG·PNG·MP4·암호문)이고 H₀가 8비트/바이트에 붙어 있으면 대개 줄지 않는다. H₀ = 8만으로는 모른다(0~255를 차례로 반복한 1,024,000 B는 H₀ = 8.000인데 gzip 4,311 B). 텍스트·JSON은 H₀보다 훨씬 잘 준다(H₀는 한계가 아니다).
3. **코드로 확인**: 실제 페이로드 표본을 압축해 비율을 본다. H₀만으로 판단하지 않는다.

```java
/** 표본 압축 비율. 0.95 이상이면 압축 이득이 거의 없다(문턱은 예시 — 서비스에서 정한다). */
static double gzipRatio(byte[] sample) throws IOException {
    var bos = new ByteArrayOutputStream();
    try (var gz = new GZIPOutputStream(bos)) { gz.write(sample); }
    return (double) bos.size() / sample.length;
}

/** 0차 엔트로피(비트/바이트). 8에 가까우면 무작위·압축·암호문일 가능성이 크다. 작으면 "줄 수 있다"는 신호일 뿐 한계는 아니다. */
static double h0(byte[] b) {
    long[] cnt = new long[256];
    for (byte x : b) cnt[x & 0xff]++;
    double h = 0;
    for (long c : cnt) if (c > 0) { double p = (double) c / b.length; h -= p * Math.log(p) / Math.log(2); }
    return h;
}
```

4. **고친다**: 이미 압축된 콘텐츠 형식은 압축 대상에서 뺀다. 작은 메시지는 문턱 이하이면 압축하지 않는다(헤더 비용 — algorithm/33). 해제 쪽에는 크기 상한을 둔다(압축 폭탄 — algorithm/33 적용 3).

### 2. 오류를 잡을 부호 고르기

```text
  질문 1: 누군가 일부러 바꿀 수 있나?    예 → HMAC·서명 (CRC 금지)  — security/05·06
  질문 2: 고쳐야 하나, 알기만 하면 되나?
          알기만 → CRC32C(저장·전송), 길이·규모에 맞는 비트 수
          고쳐야 → 정정 부호: 1비트 = SECDED, 블록 단위 = 리드–솔로몬·이레이저 코딩 [?]
  질문 3: 규모 × 2^(−r) 이 감당 가능한가?  안 되면 더 긴 체크섬 또는 암호학적 해시
```

- 해밍 부호는 d_min = 3이라 "1비트 정정"과 "2비트 검출"을 동시에 못 한다. 둘 다 필요하면 SECDED(d_min = 4)다.
- 리드–솔로몬 등 블록 정정 부호는 이 노트 범위 밖이다(근거 미확인 `[?]`).

## 장애 시나리오와 대처

### 1. 이미 압축·암호화된 데이터를 다시 압축 → 오히려 커짐 (⚠)

- 현상: 게이트웨이에서 모든 응답에 gzip을 켰더니 이미지·파일 다운로드가 느려지고 크기가 늘었다.
- 보이는 형태: `Content-Encoding: gzip` 응답 크기가 원본보다 몇 바이트~수백 바이트 크다(실험: 1MB 무작위 +328 B, `.gz` 재압축 +23 B). 게이트웨이 CPU 사용률 증가.
- 원인: 반복·치우침이 거의 남지 않은 데이터다(H₀가 8비트/바이트에 붙어 있다). 비둘기집 원리상 무손실 압축은 이런 입력을 대개 줄이지 못하고, 컨테이너 헤더·꼬리와 블록 비용만 더한다.
- 대처: 콘텐츠 타입으로 제외 목록을 둔다(이미지·동영상·압축 파일). 압축과 암호화를 모두 한다면 순서는 "압축 → 암호화"다(암호문은 무작위처럼 보여 압축이 안 된다).

### 2. 압축 폭탄 → OOM (⚠)

- 현상: 작은 업로드 하나에 서버가 죽는다.
- 보이는 형태: `java.lang.OutOfMemoryError: Java heap space`, 컨테이너 OOMKilled(exit 137). 직전 요청의 본문이 수 KB~수 MB.
- 원인: 엔트로피가 0에 가까운 데이터는 1,000:1 근처로 줄어든다(실험: 1MB → 1,004 B). 여러 겹·중첩 아카이브는 더 커진다. 해제 크기에 상한이 없었다.
- 대처: 해제 스트림에서 누적 바이트를 세어 상한을 넘으면 중단한다. 압축 비율 상한도 둔다. 코드는 [algorithm/33](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md) 적용 3과 장애 1.

### 3. 1비트 정정 부호의 2비트 오류 → 조용한 데이터 손상

- 현상: 정정 부호가 있는 저장 계층에서 값이 가끔 틀린데 오류 보고가 없다.
- 보이는 형태: 응용 수준의 체크섬 불일치·파싱 오류가 뒤늦게 난다. 하위 계층 로그에는 "정정함"만 있거나 아무것도 없다.
- 원인: 해밍(7,4) 같은 d_min = 3 부호는 2비트 오류를 다른 부호어로 잘못 고친다(실험: 336가지 전부).
- 대처: 정정과 검출이 함께 필요한 곳은 SECDED(d_min = 4)처럼 검출 여유가 있는 부호를 쓴다. 하위 계층이 고쳐 줘도 응용 수준 종단 체크섬을 따로 둔다(os/33의 종단 간 원칙). Linux에서는 EDAC가 정정된 오류(CE)와 정정 불가 오류(UE) 수를 `/sys/devices/system/edac/mc/mcX/ce_count`·`ue_count`에 낸다. 커널 RAS 문서는 CE가 앞으로 올 UE의 예측 신호일 수 있지만 반드시 그렇지는 않다고 적는다. 또 CE를 보이는 메모리 모듈을 미리 교체하면 UE 가능성을 줄일 수 있다고 적는다.

### 4. 짧은 체크섬을 큰 규모에 씀 → 미검출 누적

- 현상: 대량 전송·복제 파이프라인에서 드물게 깨진 데이터가 검사를 통과했다.
- 보이는 형태: 다운스트림 대사(건수·합계)에서 소수의 불일치. 체크섬 검사 실패 로그는 없다.
- 원인: r비트 체크섬의 무작위 훼손 미검출 확률은 약 2^(−r)이다(실험: CRC-8 약 1/256). 손상 블록 수가 2^r에 가까워지면 기대 미검출이 1건을 넘는다.
- 대처: 규모 × 2^(−r)을 계산해 비트 수를 정한다. 저장 데이터는 CRC32C 이상, 장기 보관·전송 종단은 SHA-256 다이제스트를 함께 둔다.

### 5. CRC로 위조 방지 → 변조가 통과

- 현상: CRC32를 붙여 "무결성 검증"을 했는데 변조된 파일이 통과했다.
- 보이는 형태: 검증 성공 로그와 함께 악성 내용이 처리됨.
- 원인: CRC는 선형이고 키가 없다. 공격자가 바뀐 메시지에 맞는 CRC를 계산할 수 있다.
- 대처: 위조 방지는 HMAC·서명. 자세히는 [algorithm/12](../../algorithm/12-hash-functions/2-summary.md) 장애 시나리오와 [security/05-mac-and-hmac](../../security/05-mac-and-hmac/2-summary.md).

## 핵심 문장

- 엔트로피 `H = −Σ p log₂ p`는 독립·동일 분포 원천에서 기호당 평균 부호 길이의 하한이다(Shannon 1948).
- 바이트 빈도로 센 H₀는 기억 있는 데이터(텍스트)의 한계가 아니다. 실험에서 gzip이 텍스트를 H₀ 하한의 절반으로 줄였다.
- 무손실 압축은 모든 입력을 줄일 수 없다(비둘기집). 무작위·압축·암호문은 다시 압축하면 대개 줄지 않고 조금 커진다.
- 부호의 최소 거리 d_min이 능력을 정한다: d_min − 1개 검출, ⌊(d_min − 1)/2⌋개 정정. 해밍(7,4)는 2비트 오류를 조용히 잘못 고친다.
- r비트 CRC는 길이 r 이하 버스트를 모두 잡고, 무작위 훼손은 약 2^(−r) 확률로 놓친다. 위조는 막지 못한다.

## 관련 주제·근거

- 선행·같은 영역
  - [07-probability-and-bayes](../07-probability-and-bayes/2-summary.md) — 확률·독립(엔트로피의 전제)
  - [05-counting-and-birthday-bound](../05-counting-and-birthday-bound/2-summary.md) — 비둘기집·세기
  - [13-linear-algebra-essentials](../13-linear-algebra-essentials/2-summary.md) — 벡터 거리(해밍 거리는 이진 벡터의 거리)
- 다른 영역
  - [algorithm/33-lossless-compression-lz77-huffman](../../algorithm/33-lossless-compression-lz77-huffman/2-summary.md) · [algorithm/34-modern-codecs-lz4-zstd-brotli](../../algorithm/34-modern-codecs-lz4-zstd-brotli/2-summary.md) — 압축 알고리즘, 압축 폭탄 방어
  - [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md) — CRC 선형성
  - [os/33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md) — 저장 계층 체크섬·종단 간 검증
  - [security/03-symmetric-encryption-and-aead](../../security/03-symmetric-encryption-and-aead/2-summary.md) · [security/05-mac-and-hmac](../../security/05-mac-and-hmac/2-summary.md) · [security/09-randomness-and-key-management](../../security/09-randomness-and-key-management/2-summary.md)
- 후속(AI 엔지니어링): [ai-engineering/03-cross-entropy-and-perplexity](../../ai-engineering/03-cross-entropy-and-perplexity/2-summary.md) — 교차 엔트로피·perplexity(언어 모델의 손실)
- 근거
  - C. E. Shannon, "A Mathematical Theory of Communication", Bell System Technical Journal 27, pp. 379–423, 623–656, 1948 — 엔트로피, 원천 부호화 정리
  - R. W. Hamming, "Error Detecting and Error Correcting Codes", Bell System Technical Journal 29(2), pp. 147–160, 1950 <https://doi.org/10.1002/j.1538-7305.1950.tb00463.x>
  - W. W. Peterson, D. T. Brown, "Cyclic Codes for Error Detection", Proceedings of the IRE 49(1), pp. 228–235, 1961 <https://doi.org/10.1109/JRPROC.1961.287814> — 차수 r 생성 다항식의 버스트 검출(본문 미열람 — 서지는 Crossref, 주장은 Wikipedia "Cyclic redundancy check"와 위 증명 아이디어로 확인)
  - MIT 6.042 『Mathematics for Computer Science』(Lehman·Leighton·Meyer) — 세기·확률 장(장 번호 미확인 `[?]`)
  - Java SE 21 `java.util.zip.CRC32`·`GZIPOutputStream`, Python 3.12 `gzip`·`collections.Counter`
  - J. Ziv, A. Lempel, "A Universal Algorithm for Sequential Data Compression", IEEE Trans. Information Theory 23(3), 1977 — 원천 분포를 미리 모르는 보편 부호
  - RFC 1951(DEFLATE) <https://datatracker.ietf.org/doc/html/rfc1951>, RFC 1952(gzip — 헤더 10바이트·꼬리 8바이트, 여러 멤버 이어 붙이기 허용) <https://datatracker.ietf.org/doc/html/rfc1952>
  - pgvector README — `<~>` 해밍 거리(이진 벡터) <https://github.com/pgvector/pgvector>
  - Linux 커널 문서 "Reliability, Availability and Serviceability (RAS)" — EDAC CE·UE 정의, `ce_count`·`ue_count` sysfs <https://docs.kernel.org/admin-guide/RAS/main.html>
- 실험 목록
  - `entropy.py` — 한국어 노트(`cs/database/16-mvcc/2-summary.md`)·그 `.gz`·`os.urandom` 1MB·무기억 4기호·쌍 구조·한 기호 반복의 H₀ vs gzip(level 9). Python 3.12.3 호스트, `random.seed(2026)`, 2026-10-07.
  - `Codes.java` — CRC-32 1비트·2비트 전수·버스트 20만, CRC-8 무작위 훼손 100만, 해밍(7,4)·SECDED 전수. OpenJDK 21.0.12 temurin, Docker `--cpus=2 --network none`, 2026-10-07, 2회 실행 + 사실 점검 재실행(같은 출력) + CRC-8 시드 1~5 변형.
  - 2차 리뷰 판정 확인(Python 3.12.3 호스트 `gzip`, 2026-10-07): 0~255 반복 1,024,000 B — H₀ 8.000, gzip 4,311 B. 같은 1,000 B 무작위 `.gz` 멤버 1,000개 이어 붙인 1,023,000 B → 재gzip 6,180 B.
  - 사실 점검 추가: `entropy.py` 재실행(`os.urandom` 줄 외 같은 출력), 무기억 4기호 원천을 raw DEFLATE 기본·`Z_HUFFMAN_ONLY`로 나눠 압축(Python 3.12.3 `zlib`).
