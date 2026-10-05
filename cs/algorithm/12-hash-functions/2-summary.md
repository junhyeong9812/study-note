# algorithm/12-hash-functions — 좋은 해시의 조건, 유니버설 해싱, SipHash, 암호/비암호 구분 — 정리 (힌트)

## 해결하는 문제

해시 테이블은 키를 칸 번호로 바꾸는 함수 하나에 기댄다. 그 함수가 키를 한 칸에 몰아넣으면, 표는 긴 연결 리스트 하나가 된다.

```text
  좋은 해시                          나쁜(또는 들킨) 해시
  칸0 [k3]                           칸0 [k1]-[k2]-[k3]-[k4]-...-[k10000]
  칸1 [k1]-[k7]                      칸1
  칸2 [k2]                           칸2
  칸3 [k4]-[k5]                      칸3
  조회 = 칸 찾기 + 짧은 비교          조회 = 칸 찾기 + 최대 10000번 비교
```

- *해시 함수(hash function)*: 임의 길이의 입력을 고정 크기 정수로 바꾸는 함수.
- *충돌(collision)*: 서로 다른 두 입력이 같은 해시 값(또는 같은 칸)을 받는 것. 입력 공간이 출력보다 크면 비둘기집 원리로 피할 수 없다.
  - 흔한 오해: "좋은 해시는 충돌이 없다." 충돌은 없앨 수 없다. 좋은 해시는 충돌을 **고르게 흩고, 일부러 만들기 어렵게** 한다.

쉬운 예: 사물함 번호를 "생일 달"로 정하면 1월생이 몰리는 해에는 1번 사물함 앞에 줄이 선다. 누가 일부러 1월생만 보내면 더 심하다.

똑같은 구조다. 해시 함수가 공개돼 있고 결정적이면, 공격자는 한 칸에 떨어지는 키만 골라 보낼 수 있다.

실무 예:
- 2011년 12월 oCERT-2011-003: Java·JRuby·PHP·Python·Rubinius·Ruby(공지가 꼽은 언어 구현)의 결정적 문자열 해시를 노린 POST 요청이 "100% of CPU usage which can last up to several hours"를 일으킬 수 있다고 공지됐다.
- Aumasson–Bernstein 논문이 인용한 Klink–Wälde 발표: 신중히 고른 500 KB POST 데이터가 PHP5 서버의 CPU를 1분 동안 붙잡았다.
- 해시는 표 말고도 쓰인다. 샤딩(키 → 노드), 체크섬(전송 오류 검출), 무결성(위조 검출)이다. **용도마다 요구가 다르다.** 용도를 섞으면 느려지거나 뚫린다.

## 동작·원리

### 1. 해시의 네 용도와 요구

```text
  용도                 막아야 하는 것              대표 함수                   속도
  ─────────────────   ─────────────────────────  ─────────────────────────   ────
  해시 테이블·샤딩     우연한 편중                 String.hashCode, Murmur류    매우 빠름
  (외부 입력이면)      + 의도적 편중(HashDoS)       SipHash(비밀 키)             빠름
  체크섬               우연한 비트 오류            CRC32                        매우 빠름
  무결성·위조 방지     의도적 충돌·역상            SHA-256(값을 따로 믿을 때),   느림
                                                  위조 방지는 HMAC·서명
```

- *비암호 해시(non-cryptographic hash)*: 빠르고 분포가 고르게 설계된 해시. 공격자가 충돌을 만드는 것을 막는 것은 목표가 아니다.
- *암호 해시(cryptographic hash)*: 충돌 저항성(같은 출력의 두 입력 찾기 어려움)·역상 저항성(출력에서 입력 찾기 어려움)을 목표로 한 해시. SHA-256이 예다(기초는 [sha256-and-digest](../../foundations/security/sha256-and-digest.md)).
- *PRF(pseudorandom function)*: 비밀 키를 모르는 사람에게는 출력이 무작위 함수와 구별되지 않는 키 있는 함수. SipHash가 이것을 목표로 한다(Aumasson–Bernstein 2012).

세 축은 서로 다르다.
- 체크섬은 우연한 오류만 막는다. 공격자는 막지 못한다.
- 암호 해시는 공개 함수다. 누구나 계산할 수 있으니, 해시 테이블의 칸 번호를 비밀로 만들지는 않는다.
- SipHash 같은 키 있는 PRF는 키를 모르면 칸을 예측할 수 없게 만든다. 해시 테이블 방어는 이쪽이 맞다.

### 2. Java가 실제로 하는 일 — `String.hashCode` → `HashMap.hash` → 칸

```text
  "Aa"  ──String.hashCode──>  s[0]*31 + s[1] = 65*31 + 97 = 2112
  "BB"  ──String.hashCode──>  66*31 + 66      = 2112      ← 같다

  h = key.hashCode()                       32비트 int
  h ^ (h >>> 16)                           위 16비트를 아래로 섞기 (HashMap.hash)
  index = (n - 1) & hash                   n = 2의 거듭제곱 칸 수 → 아래 비트만 쓴다
```

- `String.hashCode`의 정의: `s[0]*31^(n-1) + s[1]*31^(n-2) + ... + s[n-1]`(OpenJDK 21 `String.java` Javadoc). 시드가 없다. 같은 문자열은 어떤 JVM에서든 같은 값이다.
- `HashMap.hash(Object key)`는 `(h = key.hashCode()) ^ (h >>> 16)`이다(OpenJDK 21 `HashMap.java` 336~338행). 칸 수가 작으면 아래 비트만 쓰이므로, 위 비트의 차이를 아래로 내려 준다.
  - 이 섞기는 공격을 막지 못한다. `hashCode`가 **같은** 키는 섞은 뒤에도 같다.
- 충돌이 늘어나는 이유: 길이 같은 두 블록 `s`, `t`의 해시가 같으면, 그 뒤에 무엇을 붙여도 결과 해시가 같다.
  - `h(xy) = h(x) * 31^|y| + h(y)`이기 때문이다.
  - 그래서 "Aa"/"BB" 블록을 k개 이어 붙인 문자열 2^k개는 hashCode가 전부 같다.

```text
  k=1:  Aa, BB                                   2개, hash 2112
  k=2:  AaAa, AaBB, BBAa, BBBB                   4개, hash 2031744
  k=14: 16384개                                   전부 같은 hash
```

### 3. JDK 8 이후의 방어선 — 버킷 트리화

```text
  한 버킷의 노드 수
   1 ─────── 8    노드 8개인 버킷에 하나 더 넣을 때 (그리고 표 크기 ≥ 64)
   연결 리스트      ──treeify──>  레드-블랙 트리(TreeNode)
                   <─untreeify── resize로 쪼갤 때 6 이하면 리스트로 (삭제 때는 트리 모양으로 "너무 작다"를 판단)
   트리 안 정렬 기준: ① hash  ② 같은 클래스 C가 Comparable<C>이면 compareTo
                    ③ 그것도 아니면 삽입은 tieBreakOrder(클래스 이름·identityHashCode)로 자리만 정한다 → 조회 때는 방향을 모른다
```

- 상수(OpenJDK 21 `HashMap.java`): `TREEIFY_THRESHOLD = 8`(260행), `UNTREEIFY_THRESHOLD = 6`(267행), `MIN_TREEIFY_CAPACITY = 64`(275행). 표가 64칸보다 작으면 트리화 대신 표를 키운다.
  - `TREEIFY_THRESHOLD` 주석: "Bins are converted to trees when adding an element to a bin with at least this many nodes". `putVal`의 `binCount >= TREEIFY_THRESHOLD - 1` 검사로, 노드 8개인 버킷에 9번째를 붙일 때 트리화한다.
  - `UNTREEIFY_THRESHOLD = 6`은 resize 때 버킷을 쪼개는 `split`에서만 쓴다. 삭제(`removeTreeNode`)는 트리 모양(루트의 자식이 비었는지)으로 되돌릴지 정한다.
- JEP 180(JDK 8)이 이 변경이다. 제목은 "Handle Frequent HashMap Collisions with Balanced Trees"다. 본문은 앞선 대체 문자열 해싱("alternative string-hashing", `String`의 private `hash32` 필드)을 "can then be removed"라고 적는다.
- 트리화가 통하는 조건은 소스 주석에 있다. "worst-case O(log n) operations when keys either have distinct hashes or are orderable"(`HashMap.java` 구현 노트).
  - 키의 hash가 전부 같고 `Comparable`도 아니면, 트리에서 왼쪽·오른쪽 어느 쪽으로 갈지 정할 수 없다. `TreeNode.find`는 오른쪽 서브트리를 재귀로 다 뒤진 뒤 왼쪽으로 간다. 사실상 선형 탐색이다.
  - 같은 주석: "If neither of these apply, we may waste about a factor of two in time and space compared to taking no precautions."

### 실험: 충돌 키로 HashMap 성능 — Comparable 키 vs 비Comparable 키

키 n개를 `put`한 뒤 전부 `get`하는 시간이다. 세 가지 키를 비교했다.
- normal: `"key0"`, `"key1"`, … (hash가 흩어진다)
- collide-String: "Aa"/"BB" 블록 조합(hash가 전부 같다, `String`은 `Comparable`)
- collide-NonCmp: 같은 문자열을 감싼 클래스. `hashCode`·`equals`만 위임하고 `Comparable`이 아니다.

```java
static final class NC {                 // Comparable 아님
    final String s;
    NC(String s) { this.s = s; }
    @Override public int hashCode() { return s.hashCode(); }
    @Override public boolean equals(Object o) { return o instanceof NC n && n.s.equals(s); }
}
static long run(List<?> keys) {
    long t0 = System.nanoTime();
    Map<Object, Integer> m = new HashMap<>();
    for (Object k : keys) m.put(k, 1);
    long hit = 0;
    for (Object k : keys) hit += m.get(k);
    if (hit != keys.size()) throw new AssertionError();
    return (System.nanoTime() - t0) / 1_000_000;
}
```

(실험, OpenJDK 21.0.12 Temurin, `docker --cpus=2`, 2026-10-05 — normal·collide-String은 3회 중 최솟값, collide-NonCmp는 1회)

```text
"Aa".hashCode()=2112 "BB".hashCode()=2112 "AaBB".hashCode()=2031744 "BBAa".hashCode()=2031744
      n     normal(ms)   collide-String collide-NonCmp
   2048              1                8            283
   4096              3                9            495
   8192              1               18           2894
  16384              2               34          16617
```

- 실행마다 값이 다르다. 같은 프로그램을 세 번 돌렸을 때 n=16384의 collide-NonCmp는 16617~19221 ms, collide-String은 32~37 ms였다(첫 실행만 collide-NonCmp도 3회 중 최솟값). 사실 점검 재실행(같은 환경)에서는 15888 ms·33 ms였고, n=4096의 collide-String이 32 ms로 튀는 등 작은 n의 값은 흔들렸다.
- 관찰
  - collide-String은 n이 두 배가 될 때 대체로 2배 안팎으로 는다. 트리 덕분에 조회 하나가 O(log n)에 가깝다.
  - collide-NonCmp는 n=8192 → 16384에서 약 5.7~6.8배다(재실행 포함 네 번). 조회 하나가 O(n)이면 전체는 O(n²)이라 4배가 예상되는데 그보다 크다.
  - 해석: 키 길이도 n과 함께 자란다(블록 k개 = 2k글자). 그래서 `equals` 한 번의 비용도 커진다. 캐시 적중률 저하도 섞였을 수 있다. 이 부분은 측정으로 분리하지 않았다.
- 결론: JDK 8+ 트리화는 **키가 같은 클래스 `Comparable`이고 서로 다른 키의 `compareTo`가 0이 아닐 때** 비교 횟수를 O(log n)으로 줄인다(`compareTo`가 0이면 `TreeNode.find`가 양쪽을 뒤진다). 자체 키 클래스에 `hashCode`만 정의하고 `Comparable`을 안 붙이면 그 방어선이 없다.

### 4. 유니버설 해싱 — 무작위는 입력이 아니라 함수 선택에

```text
  고정 함수 h(x) = x mod m                 유니버설 족 H = { h_ab(x) = ((a·x + b) mod p) mod m }
  공격자: m의 배수만 보낸다                  프로그램 시작 시 a(1..p-1), b(0..p-1)를 무작위로 고른다
  → 전부 칸 0                                → 공격자는 a, b를 모르니 몰아넣을 키를 못 고른다
```

- *유니버설 해시 족(universal family)*: 함수 집합 H에서 h를 무작위로 골랐을 때, 서로 다른 두 키 x, y에 대해 `Pr[h(x) = h(y)] ≤ 1/m`이 되는 집합(Carter–Wegman 1979, CLRS 3판 11.3).
  - 흔한 오해: "유니버설 해싱은 입력이 무작위라고 가정한다." 반대다. 입력은 공격자가 골라도 되고, 무작위성은 **함수 선택**에서 온다.
- 결과(CLRS 11.3, 체이닝): 키 n개, 칸 m개일 때 한 키를 찾는 기대 비교 수가 `1 + n/m` 이하로 묶인다. 기대값은 함수 선택에 대한 것이다.
- `((a·x + b) mod p) mod m` 족은 p가 키보다 큰 소수일 때 유니버설이다(CLRS 11.3, Carter–Wegman 1979).

### 실험: 고정 해시 vs 유니버설 해시 — 공격자가 고른 키

키 = `i × 1024`(i = 0..9999), 칸 1024개. 고정 함수 `x mod 1024`를 아는 공격자가 고른 입력이다. p = 2^31 − 1(메르센 소수).

```java
int idx = universal ? (int) (((a * x + b) % P) % m) : (int) (x % m);
```

(실험, OpenJDK 21.0.12 Temurin, `--cpus=2`, 2026-10-05 — a, b는 실행마다 무작위)

```text
[1] n=10000 keys = i*1024, buckets=1024, 평균 부하=9.765625
  fixed x mod m          : max bucket = 10000
  universal ((ax+b) mod p) mod m, 무작위 a,b #1: max bucket = 12
  universal ((ax+b) mod p) mod m, 무작위 a,b #2: max bucket = 13
  universal ((ax+b) mod p) mod m, 무작위 a,b #3: max bucket = 12
  universal ((ax+b) mod p) mod m, 무작위 a,b #4: max bucket = 12
  universal ((ax+b) mod p) mod m, 무작위 a,b #5: max bucket = 12
```

- 고정 함수는 1만 개를 한 칸에 넣었다. 무작위 a, b는 가장 긴 칸을 평균(9.77)과 비슷한 12~13으로 눌렀다(사실 점검 재실행 5회는 11~13).
- 해석: 이 입력은 등차수열이라 `a·x mod p`가 특히 고르게 퍼졌을 수 있다. 다른 입력에서는 최대 칸 길이가 더 클 수 있다. 보장은 "기대 비교 수" 쪽이다.

### 5. 유니버설 해싱만으로 부족한 이유 → SipHash

- 유니버설 해싱의 충돌 확률 보장은 **키가 함수 선택과 독립적으로 정해질 때**의 것이다. 공격자가 h를 알아낸 뒤 키를 고르면 그 보장은 방어가 되지 못한다.
- Aumasson–Bernstein(2012) 7절의 지적
  - 해시 테이블은 타이밍과 순회 순서로 "이 두 문자열이 같은 칸이다"라는 정보를 흘린다.
  - Crosby–Wallach식 선형 해시 `m0·k0 + m1·k1 + …`는 그런 등식 몇 개로 비밀 계수를 가우스 소거로 풀 수 있다. 그 뒤로는 충돌 문자열을 얼마든지 만든다.
  - "many of the hash-flooding defenses proposed since December 2011 are vulnerable to the same attack."
- 제안: 해시를 **강한 PRF**로 쓴다. 칸 번호 `H(m) mod ℓ`를 보여 줘도 다른 입력의 칸을 예측할 수 없다.

```text
  SipHash-c-d (Aumasson–Bernstein 2012)
  키 128비트 ─┐
  메시지 ─────┼─ 8바이트 블록마다 SipRound c번 (압축) ─ 끝에 SipRound d번 (마무리) ─> 64비트 출력
             └─ SipHash-2-4 = c=2, d=4 (논문의 제안값)
```

- 논문의 측정: 16바이트 입력에 SipHash-2-4가 141 사이클, CityHash 82, SpookyHash 126, MD5 600(AMD FX-8150 "bulldozer"). 비암호 해시에 가깝고 MD5보다 훨씬 빠르다.
- 키를 숨겨도 충돌을 "찾는" 것은 막지 못한다. 논문 계산으로 충돌 문자열 n개를 얻으려면 공격자가 약 n·ℓ개(칸 수 ℓ가 n 정도면 n²개) 문자열을 보내야 한다. CPU 증폭이 통신량의 제곱근으로 묶인다.

언어별 채택(문서로 확인한 것):

| 런타임 | 문자열 해시 | 근거 |
|---|---|---|
| CPython 3.4~3.10 (기본 빌드) | SipHash-2-4 | PEP 456 |
| CPython 3.11+ (기본 빌드) | SipHash-1-3 | What's New 3.11, bpo-29410, configure `--with-hash-algorithm`(fnv·siphash13·siphash24 선택 가능 — 실행 중인 값은 `sys.hash_info.algorithm`) |
| Rust `std::collections::HashMap` | 무작위 시드 SipHash 1-3("currently", 바뀔 수 있음) | Rust std 문서 |
| Java `HashMap` | 시드 없는 `String.hashCode` + 트리화 | JEP 180, `HashMap.java` |

### 실험: CPython 해시 랜덤화 확인

(실험, 호스트 CPython 3.12.3, 2026-10-05)

```text
$ python3 -c "import sys;print(sys.version.split()[0], sys.hash_info)"
3.12.3 sys.hash_info(width=64, modulus=2305843009213693951, inf=314159, nan=0, imag=1000003, algorithm='siphash13', hash_bits=64, seed_bits=128, cutoff=0)
$ for i in 1 2 3; do python3 -c "print(hash('abc'))"; done
-8623781418105121559
-4662097646345614414
3974221339465667533
$ for i in 1 2; do PYTHONHASHSEED=0 python3 -c "print(hash('abc'))"; done
-4594863902769663758
-4594863902769663758
$ python3 -c "print(hash(12345), hash(-1), hash(-2))"
12345 -2 -2
```

- 프로세스마다 `hash('abc')`가 다르다. `PYTHONHASHSEED=0`이면 고정된다(재현용 설정이 방어를 끈다).
- `int`의 해시는 랜덤화 대상이 아니다. `hash(12345) == 12345`다. PEP 456도 `str`·`bytes`·`memoryview` 등만 다룬다. 정수 키 dict는 다른 방어(입력 개수 제한)가 필요하다.

### 6. 비암호 해시를 무결성에 쓰면 — CRC는 선형이다

```text
  같은 길이의 x, y, z에 대해
  crc(x ⊕ y ⊕ z) = crc(x) ⊕ crc(y) ⊕ crc(z)
  → 공격자는 메시지를 바꾼 뒤, 몇 바이트를 계산해 맞춰 CRC를 원래대로 되돌릴 수 있다
```

- *CRC(cyclic redundancy check)*: 메시지를 GF(2) 다항식으로 보고 생성 다항식으로 나눈 나머지. 우연한 연속 비트 오류 검출에 강하다. 비밀 키가 없고 선형이다.

(실험, OpenJDK 21.0.12 `java.util.zip.CRC32`, 2026-10-05)

```text
[2] crc(x^y^z)=9fea53c9  crc(x)^crc(y)^crc(z)=9fea53c9
```

- x = "PAY 100 TO ALICE", y = "PAY 900 TO MALLO", z = "XXXXXXXXXXXXXXXX"(각 16바이트). 선형식이 그대로 맞는다.
- 그래서 "파일 + CRC32"를 받아 위조를 검사하는 설계는 뚫린다. 위조 방지는 HMAC-SHA-256처럼 비밀 키가 있는 MAC이나 서명이 맡는다([hmac](../../foundations/security/hmac.md)).
- 반대 방향의 실수: 암호 해시도 영원하지 않다. SHA-1은 2017년 2월 첫 충돌(SHAttered, Stevens 외, CRYPTO 2017)이 공개됐다.

### 실험: 암호 해시를 해시 테이블 키에 쓰면 — 속도

(실험, OpenJDK 21.0.12, `--cpus=2`, 2026-10-05, 키 100만 개 `"user:<i>:session"`, JIT 워밍업 없이 3라운드)

```text
[3] round 1: hashCode 52 ms, SHA-256 588 ms (n=1000000) 0 1
[3] round 2: hashCode 44 ms, SHA-256 468 ms (n=1000000) 0 1
[3] round 3: hashCode 40 ms, SHA-256 318 ms (n=1000000) 0 1
```

- 이 환경·크기에서 SHA-256(`MessageDigest`, `getBytes` 포함)은 `String.hashCode`(캐시 안 된 새 문자열)보다 약 8~11배 느렸다(사실 점검 재실행: 555/47·427/47·284/41 ms → 약 7~12배). 라운드가 갈수록 JIT 효과로 줄었다.
- SHA-256 출력은 32바이트다. 칸 번호로는 앞 몇 비트만 쓰니, 충돌 저항성이라는 비싼 성질의 대부분이 버려진다.

## 쓰이는 자료구조·알고리즘

이 주제가 쓰는 하위 구조:
- 모듈러 산술·소수 p: 유니버설 족 `((ax+b) mod p) mod m`([28-number-theory](../28-number-theory/2-summary.md)).
- 비트 섞기: `h ^ (h >>> 16)`, 2의 거듭제곱 칸 수와 `(n-1) & hash`([29-bit-manipulation](../29-bit-manipulation/2-summary.md)).
- 레드-블랙 트리: JDK 8 트리 버킷([16-red-black-tree](../../data-structure/16-red-black-tree/2-summary.md)).

이 주제를 쓰는 곳(🔧):
- 해시맵 체이닝·트리화([05-hashmap](../../data-structure/05-hashmap/2-summary.md)), 개방 주소법([29-open-addressing](../../data-structure/29-open-addressing/2-summary.md)).
- 샤딩: 키 → 노드([31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md), [33-partitioning-and-sharding](../../database/33-partitioning-and-sharding/2-summary.md)).
- 해시 인덱스·해시 조인([39-hash-indexes](../../database/39-hash-indexes/2-summary.md), [11-join-algorithms](../../database/11-join-algorithms/2-summary.md)).
- 블룸 필터의 k개 해시([11-bloom-filter](../../data-structure/11-bloom-filter/2-summary.md)), HyperLogLog([19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)).
- 롤링 해시(커리큘럼 alg 29, 폴더 [27-string-hashing](../27-string-hashing/2-summary.md)).
- 체크섬([33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md)), 머클 트리([27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 용도부터 정한다

```text
  질문 1: 입력을 외부(사용자·네트워크)가 고르나?
          아니오 → 빠른 비암호 해시로 충분 (String.hashCode, Objects.hash, record의 자동 hashCode)
          예     → 질문 2
  질문 2: 해시 테이블/샤딩 칸 고르기인가, 위조 검출인가?
          칸 고르기 → 키 있는 해시(SipHash) 또는 입력 개수 제한 + 트리화되는 Comparable 키
          위조 검출 → HMAC-SHA-256·서명 (CRC·hashCode 금지)
  질문 3: 우연한 전송·저장 오류만 잡으면 되나? → CRC32/CRC32C
```

### 2. Java에서 외부 키를 받을 때

- 키 클래스는 `equals`·`hashCode`를 같이 정의한다. 해시 충돌 공격이 걱정되면 `Comparable`도 구현한다(서로 다른 키가 `compareTo` 0을 내지 않게). 그래야 JDK 8+ 트리 버킷이 비교 횟수 O(log n)을 지킨다(위 실험).
- 요청 하나가 만드는 키 수를 제한한다. oCERT-2011-003의 권고도 "sufficient limits for the number of parameters in POST requests"였다.
- `record`의 자동 `hashCode`는 구성 요소의 해시를 조합한다. 구성 요소가 `String`이면 공격자가 충돌을 만들 수 있다는 점은 그대로다.

### 3. 샤드 번호를 해시로 고를 때 — 음수 함정

```java
int shard = Math.floorMod(key.hashCode(), shardCount);   // 0..shardCount-1
// int shard = Math.abs(key.hashCode()) % shardCount;    // ✗ Integer.MIN_VALUE면 음수
```

(실험, OpenJDK 21.0.12, 2026-10-05)

```text
hashCode=-2147483648 (Integer.MIN_VALUE=-2147483648)
h % n = -8, Math.abs(h) % n = -8, Math.floorMod(h, n) = 2
java.lang.ArrayIndexOutOfBoundsException: Index -8 out of bounds for length 10
```

- `"polygenelubricants".hashCode()`가 정확히 `Integer.MIN_VALUE`다. `Math.abs(Integer.MIN_VALUE)`는 표현 범위를 넘어 그대로 음수다.
- 노드 수가 바뀌면 `mod n`은 키 대부분을 옮긴다. 노드 증감이 잦으면 일관 해싱([31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md))을 쓴다.

### 4. 코딩 테스트 — 롤링 해시

- 고정 base·mod 롤링 해시는 anti-hash 테스트로 깨질 수 있다. 실행 시 base를 무작위로 고르고, 필요하면 mod 두 개를 쓴다([27-string-hashing](../27-string-hashing/2-summary.md)). 유니버설 해싱과 같은 생각이다.

### 5. 진단 — CPU 100%인데 요청 수는 평소와 같다

```text
$ jcmd <pid> Thread.print | grep -A8 '"http-nio'
   at java.util.HashMap$TreeNode.find(...)
   at java.util.HashMap$TreeNode.find(...)
   at java.util.HashMap.getNode(...)
   ...  (요청 처리 스레드 여러 개가 같은 프레임에)
```

- 위는 이런 상황에서 기대하는 모양의 예시다(실제 캡처 아님). 비Comparable 충돌 키면 `TreeNode.find`의 재귀가, JDK 7 이하라면 연결 리스트 순회가 상위 프레임에 보인다.
- 확인 순서: ① 스레드 덤프 2~3회로 같은 프레임이 반복되는지 ② 프로파일러 플레임 그래프에서 `HashMap` 메서드 비중 ③ 문제 요청의 파라미터·JSON 키 수 ④ 키의 `hashCode` 분포(같은 값 개수).

## 장애 시나리오와 대처

### 1. HashDoS — 예측 가능한 해시로 CPU 고갈

- 현상: 소수의 요청만으로 웹 서버 CPU가 100%가 되고 응답이 멈춘다.
- 보이는 형태: 요청률·트래픽은 평소 수준. 요청 처리 스레드 CPU 100%. 스레드 덤프에 `HashMap.putVal`·`getNode`·`TreeNode.find`. 요청 하나의 처리 시간이 수십 초~분.
- 원인: 시드 없는 결정적 해시(Java `String.hashCode`, 2011년 당시 PHP·Python 등)라 공격자가 같은 칸의 키를 미리 계산해 POST 파라미터·JSON 키로 보낸다(oCERT-2011-003, Crosby–Wallach 2003). Python에서 재현성을 위해 `PYTHONHASHSEED=0`을 운영에 고정해도 같은 상태가 된다.
- 대처: 요청당 파라미터·키 수 제한. 런타임의 키 있는 해시(CPython 3.4+ `str` SipHash, Rust 기본 `RandomState`) 유지. Java는 JDK 8+ 트리화가 `String` 키에 대해 비교 횟수 O(log n)을 지킨다. 비교 한 번은 키 길이 L에 비례할 수 있어 조회는 O(L·log n)이므로 키 수·키 길이 상한은 여전히 둔다.
- ⚠ 커리큘럼: "예측 가능 해시 → HashDoS".

### 2. 자체 키 클래스 충돌 — 트리화가 안 통한다

- 현상: 특정 고객의 데이터에서만 배치가 수십 배 느려진다.
- 보이는 형태: 프로파일에서 `HashMap$TreeNode.find` 재귀가 상위. 키 수가 두 배면 시간이 4배 이상(위 실험: 8192 → 16384에서 약 6배).
- 원인: `hashCode`가 좁은 범위를 내는 자체 키(예: 몇 필드만 더한 값)이고 `Comparable`이 아니다. 트리 버킷이 순서를 못 정해 선형 탐색을 한다(`HashMap.java` 구현 노트).
- 대처: `hashCode`를 `Objects.hash`나 record 자동 생성처럼 전 필드를 섞게 고친다. 이는 분포 개선일 뿐 충돌 방어는 아니다(필드 해시가 같으면 그대로 충돌). 키에 `Comparable`을 구현한다. 키별 `hashCode` 값의 중복 수를 테스트로 확인한다.

### 3. 암호 해시를 해시맵·샤딩에 — 느림

- 현상: 캐시 키·샤드 키를 "안전하게" SHA-256으로 바꾼 뒤 지연 시간이 늘었다.
- 보이는 형태: 프로파일에 `MessageDigest`·`sun.security.provider.SHA2.implCompress`. 키 해시 단계 CPU 증가.
- 원인: 충돌·역상 저항이라는 칸 고르기에 불필요한 성질에 비용을 낸다. 위 실험에서 이 환경 기준 약 7~12배(실행마다 다름).
- 대처: 외부 입력 방어가 목적이면 SipHash 같은 짧은 입력용 키 있는 해시. 외부 입력이 아니면 비암호 해시.
- ⚠ 커리큘럼: "암호 해시를 해시맵에 → 느림".

### 4. 비암호 해시를 무결성에 — 위조

- 현상: 다운로드 파일·메시지 위조를 막겠다고 CRC32(또는 `hashCode`)를 붙였는데 변조된 데이터가 검증을 통과한다.
- 보이는 형태: 검증 로그는 "checksum OK". 내용은 다르다.
- 원인: CRC는 선형이고 키가 없다. 위 실험의 `crc(x⊕y⊕z) = crc(x)⊕crc(y)⊕crc(z)`처럼 공격자가 바뀐 메시지에 맞는 CRC를 계산하거나, 몇 바이트를 덧붙여 원래 CRC를 맞출 수 있다.
- 대처: 위조 방지는 HMAC-SHA-256 또는 전자 서명. 공개 다운로드라면 SHA-256 다이제스트를 별도 신뢰 채널(서명된 목록)로 배포한다. CRC는 전송 오류 검출용으로만 남긴다.
- ⚠ 커리큘럼: "비암호 해시를 무결성에 → 위조".

### 5. 음수 해시 → 샤드 인덱스 예외

- 현상: 특정 키에서만 `ArrayIndexOutOfBoundsException`.
- 보이는 형태: `Index -8 out of bounds for length 10`(위 실험).
- 원인: `hashCode() % n` 또는 `Math.abs(hashCode()) % n`. `Integer.MIN_VALUE`의 `abs`는 음수다.
- 대처: `Math.floorMod(h, n)` 또는 `(h & 0x7fffffff) % n`. 해당 키(`"polygenelubricants"`)를 테스트에 넣는다.

## 핵심 문장

- 충돌은 없앨 수 없다. 좋은 해시는 충돌을 고르게 흩고, 해시 테이블용이라면 공격자가 일부러 만들기 어렵게 한다.
- 해시는 용도가 넷이다. 칸 고르기, 외부 입력 칸 고르기, 오류 검출, 위조 검출. 요구도 함수도 다르다.
- 유니버설 해싱의 무작위성은 입력이 아니라 함수 선택에 있다. 함수가 새면 보장도 사라지므로, 외부 입력에는 SipHash 같은 키 있는 PRF를 쓴다.
- Java `HashMap`은 시드 없는 `hashCode`를 쓰고, JDK 8+ 트리 버킷으로 버틴다. 그 방어는 키가 같은 클래스 `Comparable`이고 서로 다른 키를 `compareTo`로 구분할 수 있을 때만 비교 횟수 O(log n)이다.
- CRC는 선형이라 위조를 못 막고, SHA-256은 칸 고르기에 비싸다. 용도를 섞지 않는다.

## 관련 주제·근거

선행·후속:
- 선행: 해시맵(커리큘럼 ds 07, 폴더 [05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- 후속: 롤링 해시([27-string-hashing](../27-string-hashing/2-summary.md)), 무작위 알고리즘([39-randomized-algorithms](../39-randomized-algorithms/2-summary.md)), 암호 해시의 3성질([sha256-and-digest](../../foundations/security/sha256-and-digest.md)), MAC([hmac](../../foundations/security/hmac.md)).
- 함께: 개방 주소법([29-open-addressing](../../data-structure/29-open-addressing/2-summary.md)), 일관 해싱([31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)), 해시 인덱스([39-hash-indexes](../../database/39-hash-indexes/2-summary.md)), 체크섬([33-data-integrity-checksums](../../os/33-data-integrity-checksums/2-summary.md)). 커리큘럼 표는 [../curriculum.md](../curriculum.md).

근거:
- CLRS 3판 11.3 해시 함수(유니버설 해싱 포함).
- J. L. Carter, M. N. Wegman, "Universal classes of hash functions", JCSS 18:143–154, 1979.
- J.-P. Aumasson, D. J. Bernstein, "SipHash: a fast short-input PRF", INDOCRYPT 2012(LNCS 7668) — https://www.aumasson.jp/siphash/siphash.pdf (1·2·6·7절).
- S. A. Crosby, D. S. Wallach, "Denial of Service via Algorithmic Complexity Attacks", USENIX Security 2003 — https://www.usenix.org/legacy/event/sec03/tech/full_papers/crosby/crosby.pdf
- oCERT-2011-003(2011-12-28) — https://ocert.org/advisories/ocert-2011-003.html , Klink–Wälde 28C3 발표(SipHash 논문 7절의 인용으로 확인).
- JEP 180 — https://openjdk.org/jeps/180
- OpenJDK 21 `src/java.base/share/classes/java/util/HashMap.java`(github.com/openjdk/jdk21u — 260·267·275·336~338행, 구현 노트, `TreeNode.find`), `java/lang/String.java`(`hashCode` Javadoc).
- PEP 456 — https://peps.python.org/pep-0456/ , Python 3.11 What's New(SipHash13, bpo-29410).
- Rust `std::collections::HashMap` 문서 — https://doc.rust-lang.org/std/collections/struct.HashMap.html
- M. Stevens 외, "The first collision for full SHA-1", CRYPTO 2017 — https://eprint.iacr.org/2017/190.pdf

실험 목록(전부 2026-10-05, 코드 핵심은 본문):
- HashMap 충돌 키: `HashCollide.java` — OpenJDK 21.0.12 Temurin 컨테이너 `--cpus=2 --network none`, 3회 실행.
- 고정 vs 유니버설 해시·CRC32 선형성·hashCode vs SHA-256 속도: `HashKinds.java` — 같은 환경.
- 샤드 인덱스 음수: `ShardIdx.java` — 같은 환경.
- CPython 해시 랜덤화: 호스트 CPython 3.12.3 한 줄 명령.
