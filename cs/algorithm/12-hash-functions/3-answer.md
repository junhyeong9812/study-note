# algorithm/12-hash-functions — 정답

## 정답

### 1. 충돌은 못 없앤다 — 좋은 해시의 뜻

- 입력(임의 길이 문자열)이 출력(32·64비트 정수, 또는 칸 m개)보다 훨씬 많다. 비둘기집 원리로 충돌은 생긴다.
- 해시 테이블용 해시가 좋다는 것
  - 빠르다(본문 실험 [3]: 새 문자열 100만 개의 `hashCode`가 40~52 ms, 키 하나에 수십 나노초).
  - 보통 입력에서 칸이 고르게 찬다. 그래야 기대 체인 길이가 `1 + n/m` 근처에 머문다.
- 외부 입력이면 추가 조건: **공격자가 같은 칸의 키를 일부러 만들 수 없어야** 한다. 함수가 공개·결정적이면 이 조건이 깨진다(HashDoS). 그래서 무작위 선택(유니버설 해싱)이나 비밀 키(SipHash)가 필요하다.

### 2. Java의 칸 계산

```text
  "Aa" → String.hashCode = 65*31 + 97 = 2112
  "BB" → 66*31 + 66 = 2112

  h = key.hashCode()
  hash = h ^ (h >>> 16)                 (HashMap.hash, OpenJDK 21 336~338행)
  index = (table.length - 1) & hash      (table.length = 2의 거듭제곱)
```

- hashCode가 같으니 섞은 hash도 같고, 칸도 같다.
- 2^k개 만드는 원리: `h(xy) = h(x)·31^|y| + h(y)`. 길이 같은 두 블록의 해시가 같으면, 어떤 접미사를 붙여도 결과가 같다. "Aa"/"BB"를 블록마다 골라 k개 이으면 2^k개가 전부 같은 hashCode다(실험: `"AaBB"`·`"BBAa"` 모두 2031744).

### 3. 두 배 늘렸을 때

(실험, OpenJDK 21.0.12 Temurin `--cpus=2`)

```text
      n     normal(ms)   collide-String collide-NonCmp
   8192              1               18           2894
  16384              2               34          16617
```

- `String` 키: 약 2배 안팎(세 번 실행에서 n=16384가 32~37 ms). 트리 버킷 안에서 `compareTo`로 방향을 정해 조회의 비교 횟수가 O(log n)에 가깝다(비교 한 번은 키 길이에 비례).
- 비Comparable 키: 약 5.7~6.8배(사실 점검 재실행 포함 네 번의 범위). 조회 하나가 O(n)이라 전체는 O(n²) → 4배가 기본이다. 키 길이가 n과 함께 자라 `equals` 비용도 커져 4배를 넘은 것으로 해석한다(분리 측정은 안 함).
- 규칙(`HashMap.java` 구현 노트): 트리 버킷은 hash로 먼저, 같으면 같은 `Comparable` 클래스의 `compareTo`로 정렬한다. 둘 다 안 되면(`compareTo`가 0을 내는 경우 포함) `TreeNode.find`가 오른쪽 서브트리를 재귀로 뒤진 뒤 왼쪽으로 간다. 트리화 조건은 노드 `TREEIFY_THRESHOLD = 8`개인 버킷에 하나를 더 넣을 때, 표 크기 `MIN_TREEIFY_CAPACITY = 64` 이상.

### 4. 유니버설 해시 족

- 정의: 함수 집합 H에서 h를 무작위로 골랐을 때, 서로 다른 두 키 x, y에 대해 `Pr[h(x) = h(y)] ≤ 1/m`(Carter–Wegman 1979, CLRS 11.3).
- `((a·x + b) mod p) mod m`에서 무작위로 고르는 것은 **a와 b**다(a는 1..p−1, b는 0..p−1, p는 키보다 큰 소수). 입력은 공격자가 골라도 된다.
- 보장: 체이닝에서 한 키를 찾는 기대 비교 수 ≤ `1 + n/m`. 기대값은 함수 선택에 대한 것이다.
- 깨지는 가정: 공격자가 **고른 함수(a, b)를 모른다**는 것. 타이밍·순회 순서로 같은 칸 정보가 새면, 선형 해시는 등식 몇 개로 계수를 풀 수 있다(Aumasson–Bernstein 7절).
- 실험(키 = i×1024, 칸 1024): 고정 `x mod 1024`는 최대 칸 10000, 무작위 a, b는 최대 칸 11~13(평균 9.77, 실행마다 다름).

### 5. SipHash를 제안한 이유

- 유니버설 해싱: 함수가 새면 무너진다. 실제 해시 테이블은 타이밍과 순회 순서로 정보를 흘린다. 2011년 12월 이후 제안된 방어 다수가 같은 공격에 약하다고 논문이 지적했다.
- SHA-256 같은 암호 해시: 공개 함수라 칸 번호를 비밀로 못 만든다. 짧은 입력에서 느리다(논문 측정 16바이트: MD5 600 사이클 vs SipHash-2-4 141).
- 제안: 128비트 비밀 키를 가진 강한 PRF를 쓴다. 칸 번호 `H(m) mod ℓ`를 보여 줘도 다른 입력의 칸을 예측할 수 없다. 짧은 입력에서 비암호 해시(CityHash 82, SpookyHash 126 사이클)에 가까운 속도다.
- 2와 4: SipHash-c-d에서 c = 메시지 블록(8바이트)마다 도는 압축 SipRound 수, d = 마지막 마무리 SipRound 수. SipHash-2-4는 c=2, d=4다. CPython 3.11+는 SipHash-1-3이 기본이다.

### 6. CPython 해시

(실험, 호스트 CPython 3.12.3)

```text
-8623781418105121559
-4662097646345614414
3974221339465667533          ← 프로세스마다 다르다

-4594863902769663758
-4594863902769663758         ← PYTHONHASHSEED=0이면 고정
12345                        ← hash(12345)
```

- `sys.hash_info.algorithm`은 `'siphash13'`이었다.
- `int` 해시는 랜덤화되지 않는다. PEP 456은 `str`·`bytes`·`memoryview` 등만 다룬다. 정수 키로 받는 입력은 다른 방어(개수 제한)가 필요하다.

### 7. CRC32로 위조 방지

- 문제: CRC에는 비밀 키가 없고 선형이다. 공격자는 파일을 바꾼 뒤, 바뀐 파일의 CRC를 새로 계산해 함께 내거나, 몇 바이트를 조정해 원래 CRC를 맞출 수 있다.
- 성질: 같은 길이의 x, y, z에 대해 `crc(x⊕y⊕z) = crc(x)⊕crc(y)⊕crc(z)`. 실험에서 양쪽이 `9fea53c9`로 같았다.
- 대체: HMAC-SHA-256(공유 키) 또는 전자 서명. 공개 배포라면 서명된 SHA-256 목록. CRC는 우연한 오류 검출용으로만 쓴다.

### 8. CPU 100% + `TreeNode.find`

- 원인 후보
  - ① 외부 입력이 고른 충돌 키(HashDoS). POST 파라미터·JSON 키 다수가 같은 hashCode를 가진다.
  - ② 자체 키 클래스의 `hashCode`가 좁은 범위를 내고, 키가 `Comparable`이 아니다. 트리 버킷이 순서를 못 정해 선형 탐색한다.
- 확인 순서
  - 스레드 덤프 2~3회(`jcmd <pid> Thread.print`)로 같은 프레임이 반복되는지 본다.
  - 프로파일러로 `HashMap` 메서드 비중을 본다.
  - 문제 요청의 키 개수, 키의 `hashCode` 중복 수를 센다.
- 대처: ①이면 요청당 키 수 제한과 입력 크기 제한. ②면 `hashCode`를 전 필드를 섞도록 고치고(분포 개선일 뿐, 중복 수를 테스트로 확인) `Comparable`을 구현한다(서로 다른 키가 `compareTo` 0을 내지 않게).

### 9. 음수 샤드 인덱스

- `"polygenelubricants".hashCode()`가 `Integer.MIN_VALUE`(−2147483648)다. `Math.abs(Integer.MIN_VALUE)`는 오버플로로 그대로 음수다.
- 실험(n=10): `Math.abs(h) % n = -8` → `ArrayIndexOutOfBoundsException: Index -8 out of bounds for length 10`.
- 고친 식: `Math.floorMod(key.hashCode(), n)`(실험 결과 2) 또는 `(h & 0x7fffffff) % n`.
