# math/16-math-symptom-index — 증상 사전: 정렬 계약 예외·음수 나머지·간헐 ID 충돌·합계 불일치·이용률 절벽 → 깨진 수학 전제·어림 계산·leaf — 정리 (힌트)

## 해결하는 문제

이 영역의 다른 노트는 **수학에서 증상으로** 간다.\
"비교자의 0이 추이적이지 않으면 TimSort가 예외를 던지거나 조용히 틀린 순서를 낸다"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 증상 한 줄이다. "`Comparison method violates its general contract!`", "`Index -1 out of bounds for length 3`", "가끔 `duplicate key`", "정산 합계가 원장과 0.01 다르다", "트래픽 15% 늘었는데 지연이 두 배".

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                   이 노트 (역방향)
  수학 전제 --> 깨지는 상황 --> 보이는 증상               증상 --> 보이는 형태 --> 원인 후보(수학) --> 어림·측정 --> leaf
  "32비트 공간은 7.7만 개에서 충돌 50%"                  "가끔 duplicate key, 재시도하면 성공. 먼저 ID 비트 수와 행 수로 1 − exp(−k²/2N)"
```

쉬운 예: 체중계가 매일 1kg씩 다르게 나온다.\
체중계가 기울어졌을 수도(측정 방법), 아침·저녁에 쟀을 수도(조건이 다름), 정말 살이 쪘을 수도(실제 변화) 있다.\
"숫자가 이상하다"는 증상 하나에 원인이 여럿이다. 계산 한 번으로 가를 수 있는 것부터 가른다.

똑같은 구조다.\
"합계가 원장과 다르다"는 같은 증상에 수학 원인이 여럿이다.
- 차이가 매번 마지막 한 건 값과 같으면 루프 경계(불변식) 문제다([02-1](../02-induction-and-invariants/2-summary.md)).
- 차이가 10⁻⁴ 같은 작은 소수면 부동소수 반올림 누적이다([15-1](../15-numerical-stability/2-summary.md)).
- 차이 나는 행이 NULL을 가진 행이면 3치 논리다([01-4](../01-propositional-logic/2-summary.md)).

실무 예:
- 수학 증상의 대부분은 **전제가 운영에서 깨질 때** 보인다. 정리·공식에는 전제가 붙어 있다(균일·독립, 정상 상태, 정수는 안 넘친다, 비교자는 전순서다, 실수 덧셈은 결합법칙을 따른다).
- 그래서 첫 질문은 "이 계산이 기대는 전제가 무엇이고, 지금 그 전제가 맞는가"다.

  - *역색인*: "leaf → 증상" 목록을 "증상 → leaf" 목록으로 뒤집은 것([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).
  - *leaf 표기 `NN-k`*: 이 영역 NN번 노트의 「장애 시나리오와 대처」 k번째 시나리오다. 예: `11-1` = [11-modular-arithmetic](../11-modular-arithmetic/2-summary.md)의 시나리오 1(음수 나머지 → 샤드 인덱스 예외). 이 영역은 폴더 번호와 커리큘럼 번호가 같다.
  - *어림 계산(back-of-the-envelope)*: 정확한 값 대신 한두 줄 식으로 크기의 차수를 먼저 잡는 계산. 가설을 고르는 데 쓰고, 확정은 측정으로 한다.

## 동작·원리

### 0. 증상은 어느 수학 전제가 깨진 것인가

```text
   증상 (커리큘럼 다섯 + 나머지)              깨진 전제                                  이 노트의 절
   ──────────────────────────               ─────────                                  ──────────
   Comparison method violates ...            "비교자는 전전순서다"(부호 반대칭·추이성·0의 일관성) 1절
   음수 인덱스 · 샤드가 언어마다 다름           "나머지는 0..n-1이다"                         2절
   간헐 duplicate key · 같은 ID               "공간이 충분히 크고 값이 균일·독립이다"        3절
   합계가 원장과 다름 · 병렬도마다 다른 합     "덧셈은 정확하고 결합법칙을 따른다"           4절
   이용률 조금 올랐는데 지연 급등              "지연은 부하에 선형이다"                       5절
   예외 없는 권한 우회, 무한 루프, 오탐 폭주 등  그 밖의 전제                                  6절
```

- 커리큘럼의 다섯 증상이 1~5절이다. 6절은 01~15 leaf의 나머지 ⚠·시나리오다.
- 알고리즘 쪽 원인(정렬 구현·이진 탐색·정규식)은 [algorithm/42-alg-symptom-index](../../algorithm/42-alg-symptom-index/2-summary.md), 자료구조 쪽은 [data-structure/43-ds-symptom-index](../../data-structure/43-ds-symptom-index/2-summary.md), 운영 지표 쪽은 [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)가 정본이다. 이 노트는 **수학 전제** 쪽 갈래만 본다.

### 0-1. 색인을 쓰기 전에 확보할 것

```text
  ① 원문     예외 전체 + 스택 트레이스, 언어·런타임 판 (Java % 와 Python % 는 다르다)
  ② 크기     n(원소 수·행 수·요청 수), 값의 범위(int 경계? 2^24? 2^53?), ID 비트 수
  ③ 분포     균일한가 치우쳤나(Zipf), 독립인가 몰리나(버스트·같은 AZ), 기저율은?
  ④ 비율     차이·오류·지연이 무엇에 비례하나 (n? n²? ρ/(1−ρ)? 마지막 한 건?)
```

- ②·③이 있어야 7절의 어림 계산을 할 수 있다. 어림 결과가 관측과 차수까지 맞으면 그 원인이 유력하다. 차수가 다르면 다른 원인을 찾는다.

### 1. 정렬 계약 예외 — 비교자·`equals`의 관계 공리

먼저 **비교자(또는 `equals`) 코드가 동치·순서 공리를 지키나**를 본다. 예외는 위반을 우연히 만났을 때만 난다.

```text
  정렬·집합 결과가 이상함
     │
     ├─ IllegalArgumentException: Comparison method violates its general contract! ─▶ 비교자 추이성 위반(허용 오차 "같음")   03-2
     ├─ 예외 없음, 순서가 군데군데 뒤집힘 ─────────────────────────────────────▶ 같은 원인, 위반을 못 만남             03-2
     ├─ HashSet 에 "같은" 원소가 두 개, 넣는 순서마다 크기가 다름 ────────────────▶ equals 대칭 위반(상속)              03-1
     ├─ HashSet 과 TreeSet 의 크기가 다름 (1.0 vs 1.00) ─────────────────────────▶ compare 와 equals 가 다른 동치관계    03-3
     └─ "비슷한 것끼리 묶기"가 먼 것까지 한 덩어리 ────────────────────────────────▶ 비추이 관계의 추이 폐포              03-4
```

| 증상 | 보이는 형태 | 원인 후보(수학 개념) | 확인 방법(어림·측정) | leaf |
|---|---|---|---|---|
| 특정 데이터 정렬에서만 500 | `java.lang.IllegalArgumentException: Comparison method violates its general contract!`, 트레이스에 `TimSort.mergeHi`/`mergeLo` | "차이 ≤ ε이면 0" 비교자 — `compare == 0`이 추이적이지 않음 | 세 값 a≈b, b≈c, a≉c를 직접 넣어 본다. n이 32 이상인가(31 이하는 병합 없음) | [03-2](../03-sets-relations-orders/2-summary.md) |
| 예외 없이 틀린 순서 | `Near.java` 실험: 값이 빽빽하지 않은 분포(범위 0.60·n·0.10·n)에서 200회 중 예외 0~5회, "예외 없이 역전" 88~200회 | 같은 원인 | 정렬 결과를 올바른 기준 비교자로 재검사 | [03-2](../03-sets-relations-orders/2-summary.md) · [algorithm/09](../../algorithm/09-sorting-in-practice/2-summary.md) |
| 중복 제거 목록에 같은 것이 두 번 | `add(p)` 후 `add(cp)`는 size=2, 순서를 바꾸면 size=1 | `equals` 대칭 위반(`instanceof` 상위·하위 타입) | `a.equals(b) == b.equals(a)`를 하위 타입 섞어 검사 | [03-1](../03-sets-relations-orders/2-summary.md) |
| 두 컬렉션 크기가 다름 | `HashSet size=2  TreeSet size=1`(`BigDecimal` 1.0·1.00) | 한 원소 집합에 동치관계가 둘 | `compare == 0`과 `equals`가 같은 값인가 | [03-3](../03-sets-relations-orders/2-summary.md) |
| 묶음 하나의 폭이 임계값의 몇 배 | 임계 0.5인데 1.0과 2.2가 한 묶음 | union-find가 비추이 관계의 추이 폐포를 계산 | 묶음별 최소·최대 차이 | [03-4](../03-sets-relations-orders/2-summary.md) |

- `-Djava.util.Arrays.useLegacyMergeSort=true`로 예외를 덮지 않는다. 예외가 사라질 뿐 비교자는 그대로 틀리다([03-2](../03-sets-relations-orders/2-summary.md), 실사건은 [17-math-incidents](../17-math-incidents/2-summary.md) 사건 2).
- 뺄셈 비교자 오버플로·정렬 중 바뀌는 키 같은 구현 쪽 원인은 [algorithm/42-alg-symptom-index](../../algorithm/42-alg-symptom-index/2-summary.md) 2절.

### 2. 음수 모듈러 — 나머지의 정의가 언어마다 다르다

먼저 **해시(또는 피제수)가 음수일 수 있나, 어느 언어의 `%`인가**를 본다.

```text
  인덱스·샤드 계산 이상
     │
     ├─ ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 3 ──▶ Java % 는 피제수 부호            11-1
     ├─ Java 가 쓴 데이터를 Python 이 일부 못 찾음(음수 해시 키만) ─────────────▶ truncate % vs floor %          11-2
     ├─ Math.abs 로 고쳤는데 아주 드물게 같은 예외 ─────────────────────────────▶ Math.abs(MIN_VALUE) 가 음수      11-3
     ├─ 큰 모듈러 계산이 가끔 다른 값, 예외 없음 ───────────────────────────────▶ 곱셈 넘침(2^63)                 11-4
     └─ 파티션 몇 개만 뜨거움 / 숫자 코드의 앞쪽 숫자가 잦음 ────────────────────▶ gcd 쏠림·모듈로 편향            11-5
```

| 증상 | 보이는 형태 | 원인 후보(수학 개념) | 확인 방법(어림·측정) | leaf |
|---|---|---|---|---|
| 특정 키만 실패 | `java.lang.ArrayIndexOutOfBoundsException: Index -1 out of bounds for length 3` | Java `%`는 피제수 부호(JLS §15.17.3) — 나머지 범위가 −(n−1)..n−1 | `-7 % 3`: Java −1, Python 2. 음수 해시 키 하나로 재현 | [11-1](../11-modular-arithmetic/2-summary.md) |
| 두 언어의 샤드 번호가 n만큼 차이 | 음수 해시 키에서만 "없음" | 나머지의 정의 차이(truncate vs floor) | 같은 테스트 벡터(음수 포함)를 양쪽에서 계산 | [11-2](../11-modular-arithmetic/2-summary.md) |
| `Math.abs` 뒤에도 드물게 음수 | `Math.abs(MIN_VALUE) = -2147483648`, `Index -8 out of bounds for length 10` | 2의 보수에서 −MIN_VALUE는 표현 불가 | 해시가 `Integer.MIN_VALUE`인 키를 넣는다. 어림: 균일 해시면 2^32개 중 1개 | [11-3](../11-modular-arithmetic/2-summary.md) · [algorithm/12](../../algorithm/12-hash-functions/2-summary.md) |
| 큰 모듈러 결과 불일치 | m = 40억에서 무작위 10만 건 중 87,604건이 `BigInteger.modPow`와 다름 | `(a * a) % m`에서 a² > 2^63 넘침(JLS §4.2.2: 넘침을 알리지 않음) | 피연산자 < m이므로 (m − 1)² ≤ 2^63 − 1인가 — m ≤ 3,037,000,500이면 `long` 안전 | [11-4](../11-modular-arithmetic/2-summary.md) |
| 일부 칸만 뜨거움 | 8의 배수 ID가 64칸 중 8칸에만 | 칸 수 n과 키 간격 s의 공약수 — 최대 n / gcd(s, n)칸만 쓰임(키가 그보다 적으면 키 수만큼) | 키 간격과 칸 수의 gcd | [11-5](../11-modular-arithmetic/2-summary.md) |

- 처방의 방향: `Math.floorMod(h, n)`(n > 0)으로 나머지 범위를 0..n−1로 고정한다. 샤드 규칙은 "해시 함수 + floor 나머지 + n"을 명세로 적는다. `& 0x7fffffff`와 `floorMod`는 결과가 다르므로 바꿀 때 데이터 재배치를 계획한다([11-3](../11-modular-arithmetic/2-summary.md)).

### 3. 간헐 ID 충돌 — 세기와 생일 한계

먼저 **ID의 무작위 비트 수 b와 지금까지 만든 개수 k**로 어림한다. 어림 확률이 관측 빈도와 차수까지 맞으면 생일 한계, 훨씬 자주 나면 무작위성 가정이 깨진 것이다.

```text
  가끔 같은 ID / duplicate key
     │
     ├─ 수만 행에서 가끔 duplicate key, 재시도하면 성공 ───────────────▶ 32비트 무작위 ID의 생일 한계        05-1
     ├─ "short object ID ... is ambiguous", 캐시 키가 남의 데이터 ────────▶ 해시 prefix 절단(칸 2^b)          05-2
     ├─ 계산상 수십억 년에 한 번인 충돌이 배포 직후 여러 번 ──────────────▶ 균일·독립 전제 붕괴(같은 시드)      05-3 · 12-1 · 17 사건 1
     └─ 피크에 ID 발급 지연, worker 설정 실수로 겹침 ─────────────────────▶ 곱 법칙 상한(4096/ms/worker)       05-4
```

| 증상 | 보이는 형태 | 원인 후보(수학 개념) | 확인 방법(어림·측정) | leaf |
|---|---|---|---|---|
| 가끔 INSERT 실패 | PostgreSQL `duplicate key value violates unique constraint`, SQLite `UNIQUE constraint failed`(실험: 4.8만~10.3만 행에서 첫 실패) | 생일 한계 — 32비트 공간은 약 7.7만 개에서 충돌 확률 50% | P ≈ 1 − exp(−k(k−1)/2N), N = 2^b. 균일 가정 | [05-1](../05-counting-and-birthday-bound/2-summary.md) |
| 짧은 ID가 모호하거나 엉뚱한 대상 | git `error: short object ID 821e is ambiguous` | 비둘기집 — 2^b칸에 2^b개 넘게 넣으면 겹침을 피할 수 없음 | prefix 비트 b와 대상 수 k 비교: k ≈ 2^(b/2)부터 충돌이 흔해짐 | [05-2](../05-counting-and-birthday-bound/2-summary.md) |
| 충돌 ID가 호스트·시각별로 짝을 이룸 | 다른 인스턴스가 같은 ID 수열 | 생성기 시드가 같다(상수·시작 시각) → 같은 시드의 인스턴스들이 같은 수열을 되풀이 | 충돌 쌍의 생성 호스트·기동 시각 비교, 두 인스턴스의 n번째 값끼리 겹치나. 서로 다른 수열은 시드 수만큼뿐이다(인스턴스당 값 하나만 쓰는 키 생성이면 공간 = 시드 수 — 17 사건 1) | [05-3](../05-counting-and-birthday-bound/2-summary.md) · [12-1](../12-randomness-and-prng/2-summary.md) |
| 피크에 발급 대기 | ms당 4096개 넘는 요청이 다음 ms를 기다림 | 곱 법칙 — 시각 × machine × 순번의 한 칸이 넘침 | 피크 발급률 vs 2^12/ms/worker | [05-4](../05-counting-and-birthday-bound/2-summary.md) · [distributed/13](../../distributed/13-distributed-id-generation/2-summary.md) |

- 생일 어림은 **균일·독립**일 때의 값이다. 관측 충돌이 어림보다 차수 이상 잦으면, 비트 수를 늘리기 전에 생성기를 의심한다. Debian OpenSSL(2008)은 실제 공간이 아키텍처(·키 종류·길이·`~/.rnd` 유무 같은 입력 상태)마다 PID 수(32,767) 이하로 줄었던 사례다([17-math-incidents](../17-math-incidents/2-summary.md) 사건 1).
- 순차 ID의 열거·추측 문제는 보안 쪽이다([security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md)).

### 4. 합계 불일치 — 반올림·결합법칙·경계

먼저 **차이의 크기와 모양**을 본다. 마지막 한 건 값이면 경계, 작은 소수면 반올림, 병렬도·파티션 설정마다 다르면 덧셈 순서, NULL 행이면 3치 논리다.

```text
  합계·건수가 기준과 다름
     │
     ├─ 차이 = 마지막 한 건의 값 (매번) ────────────────────────────▶ off-by-one, 불변식이 끝에서 전체를 말하지 않음   02-1
     ├─ 차이가 10^-4 같은 작은 소수, 또는 float 누적이면 큰 금액 ─────▶ 큰 수 + 작은 수 반올림 누적                    15-1
     ├─ 같은 데이터인데 병렬도·파티션 수마다 마지막 자리가 다름 ───────▶ 부동소수 덧셈은 결합법칙이 없음                15-2
     ├─ 표준편차가 NaN, 분산이 음수 ─────────────────────────────────▶ E[X²] − E[X]² 의 파국적 상쇄                   15-3
     ├─ 카운터가 16,777,216 근처에서 멈춤 ────────────────────────────▶ float 가수 24비트, 2^24 이후 간격 2              15-5
     ├─ 두 쿼리 건수 합 < 전체 건수 ──────────────────────────────────▶ SQL 3치 논리(NULL → UNKNOWN)                  01-4
     └─ 대량 전송 대사에서 소수 불일치, 체크섬 실패 로그는 없음 ─────────▶ r비트 체크섬의 미검출 확률 ≈ 2^-r(무작위 훼손 가정) 14-4
```

| 증상 | 보이는 형태 | 원인 후보(수학 개념) | 확인 방법(어림·측정) | leaf |
|---|---|---|---|---|
| 정산 합계가 원장보다 한 건 적음 | 차이 = 마지막 원소 값(실험 `sum(offByOne=true)` = 9 vs 14) | 루프 경계 `i < n - 1` — 불변식 "s = 앞 i개의 합"이 종료 시 i = n − 1 | 길이 0·1·2 입력으로 합 비교 | [02-1](../02-induction-and-invariants/2-summary.md) |
| `double` 합이 원장과 다름 | `BigDecimal` 원장과 `compareTo` ≠ 0(실험 차이 1.969×10⁻⁴), `float` 누적이면 약 270만 원 | 큰 누적값에 작은 항 — 하위 비트 절단 | 누적값 / 항의 크기 비가 2^53(double)·2^24(float)에 가까운가 | [15-1](../15-numerical-stability/2-summary.md) · [domain-modeling/14](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md) |
| 골든 테스트가 병렬도 변경 뒤 실패 | `expected 4999835704.520057 but was 4999835704.520033` | 덧셈 순서(나무 모양)가 바뀜 — 결합법칙 없음 | 병렬도 1·3·7·15에서 결과 비교(실험: 네 가지 값) | [15-2](../15-numerical-stability/2-summary.md) |
| 표준편차 대시보드가 빔 | `NaN`, 분산 −128(실험) | 큰 값·작은 분산에서 파국적 상쇄 | 값의 크기 / 표준편차 비가 큰가(에포크 나노초 등) | [15-3](../15-numerical-stability/2-summary.md) |
| 릴리스 빌드만 합이 덜 정확 | `-ffast-math`에서 Kahan 합 = 단순 합(실험) | 재결합 허용으로 보상항이 0으로 정리됨 | 빌드 옵션별 같은 입력 합계 | [15-4](../15-numerical-stability/2-summary.md) |
| 카운터가 멈춤 | 그래프가 16,777,216 근처에서 평평 | `float` 가수 24비트 | 멈춘 값이 2^24인가 | [15-5](../15-numerical-stability/2-summary.md) |
| 허용·거부 건수 합이 전체보다 적음 | `count(*)` − (두 쿼리 합) = 조건 열이 NULL인 행 수 | 3치 논리 — `P`와 `NOT P`가 둘 다 UNKNOWN | `WHERE col IS NULL` 건수와 차이 비교 | [01-4](../01-propositional-logic/2-summary.md) |
| 깨진 데이터가 검사 통과 | 다운스트림 대사의 소수 불일치 | r비트 체크섬의 미검출 ≈ 2^(−r) — 오류 패턴이 고르게 무작위라는 가정의 근사(다항식·길이·오류 분포에 따라 다르다 — 길이 r+1 버스트는 2^(−(r−1))) | 손상 블록 수 × 2^(−r) ≥ 1인가 | [14-4](../14-information-theory-basics/2-summary.md) |

- 처방의 방향: 금액은 `long` 최소 단위나 `BigDecimal`. 재현성이 계약이면 정확한 누적 또는 순서 고정. 통계 지표면 보상 합과 허용 오차 비교(보상 합이 요구사항이면 Kahan을 직접 쓴다 — `DoubleStream.sum()`은 보상 합으로 구현될 "수 있을" 뿐 보장이 아니다, [15](../15-numerical-stability/2-summary.md) 3절). 분산은 웰퍼드 갱신.

### 5. 이용률 절벽 — 큐잉의 비선형

먼저 **이용률 ρ와 지연의 관계**를 본다. ρ가 조금 올랐는데 지연이 몇 배면 큐잉, 평균은 그대로인데 p99만 나쁘면 분포 꼬리, 짧은 구간만 넘치면 버스트다.

```text
  지연이 갑자기 나빠짐
     │
     ├─ 트래픽 10~20% 증가, 이용률 80~90%대, 지연 2배 이상 ──────────────▶ M/M/1 대기 ∝ ρ/(1−ρ)                     10-1
     ├─ Connection is not available, request timed out after 30000ms ────▶ 풀 크기 = 평균 동시 수 → ρ = 1            10-2
     ├─ 평균 처리 시간은 그대로인데 같은 풀의 짧은 요청 p99 상승 ──────────▶ 서비스 시간 분산(E[S²]) — P-K 공식         10-3
     ├─ 서버를 늘렸는데 기대만큼 안 줄고 인스턴스별 편차가 큼 ──────────────▶ 인스턴스별 큐(M/M/1 여럿) vs 공유 큐(M/M/c) 10-4
     ├─ 큐 길이·컨슈머 랙이 단조 증가 ────────────────────────────────────▶ ρ ≥ 1, 정상 상태 아님(Little 전제 붕괴)    10-5
     ├─ 분당 지표는 평온, 초 단위 스파이크 ───────────────────────────────▶ 포아송(독립 도착) 가정 붕괴 — 버스트        09-1
     ├─ 평균 SLO는 지켰는데 타임아웃 민원 ─────────────────────────────────▶ 평균만 봄, 긴 꼬리                         08-1 · 09-4
     └─ 입력 2배에 시간 4배 / n이 1 늘 때 1.6배 ─────────────────────────▶ 점화식 Θ(n²) / 지수                         06-2 · 06-3
```

| 증상 | 보이는 형태 | 원인 후보(수학 개념) | 확인 방법(어림·측정) | leaf |
|---|---|---|---|---|
| 조금 늘었는데 지연 급등 | p99·평균 급등, 풀 큐 길이 상승, 이용률 80~90%대, 오류율은 처음엔 그대로 | M/M/1 평균 대기 Wq = ρ/(1−ρ) · E[S] — ρ 0.8 → 0.9에 4 → 9배(시뮬레이션 3.98~4.05 → 8.83~9.17) | 이용률 = λ × E[S] / 서버 수. ρ/(1−ρ)를 두 시점에 계산해 비율 비교 | [10-1](../10-queueing-and-littles-law/2-summary.md) |
| 풀 고갈 | `SQLTransientConnectionException: … Connection is not available, request timed out after 30000ms`(HikariCP) | 풀 크기 c = 평균 동시 점유 수 a(Little: a = λ × E[S], E[S] = 평균 점유 시간)면 ρ = 1 | λ × E[S]를 계산해 풀 크기와 비교. 여유는 Erlang C(M/M/c 가정) | [10-2](../10-queueing-and-littles-law/2-summary.md) · [database/21](../../database/21-connection-pooling/2-summary.md) |
| 느린 작업이 섞이자 모두 느림 | 짧은 요청 p99 상승, 리포트·배치 시간대와 겹침 | P-K: Wq = λ·E[S²] / (2(1 − ρ)) — 서비스 시간 분산 | Cs² = Var(S)/E[S]²(시뮬레이션: ρ = 0.8에서 Cs² 1 → 5.5로 대기 4 → 12.7) | [10-3](../10-queueing-and-littles-law/2-summary.md) |
| 서버를 늘려도 덜 줄어듦 | 인스턴스별 큐 길이 편차 | 따로 줄(M/M/1 × c) vs 공유 줄(M/M/c) | 서버당 ρ = 0.8 시뮬레이션: 따로 3.98 vs 공유 0.203 | [10-4](../10-queueing-and-littles-law/2-summary.md) |
| L ≠ λ × W | 큐 길이·랙 단조 증가 | 랙까지 계속 늘면 도착률 ≥ 처리율일 가능성 — 평균이 수렴하지 않음. 또는 측정 창이 체류 시간보다 짧아 창 끝에 걸친 건이 빠짐 | 먼저 들어온 수 − 나간 수의 추세, 다음으로 측정 창 > 체류 시간인가 | [10-5](../10-queueing-and-littles-law/2-summary.md) |
| 특정 초만 넘침 | `RejectedExecutionException`·503이 특정 초에 몰림 | 독립 도착 가정 붕괴(정각 cron·푸시·재시도) — 분산 ≫ 평균 | 초 단위 카운트의 분산/평균(포아송이면 1 근처). 실험: 9.86%의 초가 용량 초과 | [09-1](../09-common-distributions/2-summary.md) |
| 평균은 정상, 민원 증가 | 평균 30ms대, p99 수백 ms | 오른쪽 꼬리 긴 분포에서 평균은 꼬리를 숨김 | 히스토그램 백분위. 정규 가정 p99(계산 134ms) vs 실측(205ms) | [08-1](../08-expectation-variance-tails/2-summary.md) · [09-4](../09-common-distributions/2-summary.md) |
| 테스트는 빠르고 운영은 타임아웃 | 입력 2배에 시간 3.4~5.3배(`remove(0)` 20만에 약 5~7초, 부하에 따라) | 숨은 선형 일 T(n) = T(n−1) + n = Θ(n²) | 크기 두 배 → 시간 비율 | [06-2](../06-recurrences-and-asymptotics/2-summary.md) |
| n=30은 빠르고 40은 초 단위 | n이 1 늘 때 약 1.6배 | T(n) = T(n−1) + T(n−2) — 지수 | 호출 수 2·F(n+1) − 1 | [06-3](../06-recurrences-and-asymptotics/2-summary.md) |

- 처방의 방향: 목표 이용률을 낮게 잡고(여유 대수), 오토스케일은 대기·지연 지표로도 건다. 넘치면 로드 셰딩([reliability/12](../../reliability/12-backpressure-and-load-shedding/2-summary.md)). 느린 작업은 별도 풀로. 분배는 공유 큐나 최소 요청 수 우선.
- M/M/1 식의 전제(포아송 도착·지수 서비스·정상 상태)가 운영에서 정확히 맞는 일은 드물다. 그래도 "ρ가 1에 다가가면 대기가 1/(1−ρ)꼴로 커진다"는 모양은 서비스 시간 분포가 달라도 나타난다(포아송 도착인 M/G/1의 P-K 식 분모 1 − ρ). 수치는 어림이고 확정은 부하 테스트로 한다.

### 6. 그 밖의 증상

| 증상 | 보이는 형태 | 원인 후보(수학 개념) | 확인 방법(어림·측정) | leaf |
|---|---|---|---|---|
| 권한 없는 사용자의 성공 요청 | 예외 없음, 감사 로그에 200, 리팩터링 직후 | 드모르간 실수 `!(a && b)` → `!a && !b` | 진리표 4행 전수 비교 | [01-1](../01-propositional-logic/2-summary.md) |
| 비로그인 요청만 500 | `Cannot invoke "Npe$User.isAdmin()" because "u" is null`(`-g` 컴파일) | 단락 평가 순서 — 가드가 뒤로 감 | `&&` 왼쪽이 가드인가 | [01-2](../01-propositional-logic/2-summary.md) |
| 설정 배포 뒤 누구나 관리 기능 접근 | 에러 없음, 필수 역할 목록이 비었음 | 공허한 참 — 빈 집합의 ∀는 참(`allMatch`) | 목록 크기 0 검사 | [01-3](../01-propositional-logic/2-summary.md) |
| 부정 테스트는 녹색, 운영 버그 | 테스트 이름이 "A가 아니면 B 아님" | 조건문 부정을 이(裏)로 씀 — `A → B`의 반례는 `A ∧ ¬B` | 테스트가 전제 참·결론 거짓 경우를 보나 | [01-5](../01-propositional-logic/2-summary.md) |
| 요청 하나가 CPU 한 코어 100% | `jstack`에서 같은 줄 `RUNNABLE` | 종료 척도 부재(구간이 안 줄어듦, 정수 감김) | 덤프 2~3장이 같은 줄인가, 갱신 줄이 척도를 줄이나 | [02-2](../02-induction-and-invariants/2-summary.md) |
| 있는 키를 "없음" | 실험: `hi = mid - 1` 판이 10,000회 중 2,230회 틀림 | 이진 탐색 불변식의 유지 단계 깨짐 | 불변식 `assert`를 넣고 무작위 입력 | [02-3](../02-induction-and-invariants/2-summary.md) |
| 테스트에서 잡던 위반이 운영에서 조용 | 운영 JVM 인자에 `-ea` 없음 | `assert`는 기본 꺼짐(JLS §14.10) | `assert` 활성 여부 출력 | [02-4](../02-induction-and-invariants/2-summary.md) |
| 특정 데이터에서 재귀가 죽음 | `java.lang.StackOverflowError`(실험: 약 1.1만 호출 뒤) | 의존 그래프를 DAG로 가정 — 사이클 | 3색 DFS로 GRAY 재방문 | [04-1](../04-graph-theory-basics/2-summary.md) |
| Spring Boot 2.6+ 기동 실패 | `BeanCurrentlyInCreationException`, `Is there an unresolvable circular reference ...` | 빈 의존 그래프의 사이클 | 메시지의 빈 이름 경로 | [04-2](../04-graph-theory-basics/2-summary.md) |
| 빌드·마이그레이션 순서 도구가 일부만 처리 | Kahn식이면 처리 수 < 전체(실험 `2/5`) | 사이클 — 위상정렬 없음 | 3색 DFS로 사이클 경로 추출 | [04-3](../04-graph-theory-basics/2-summary.md) |
| 두 트랜잭션·스레드가 멈춤 | PostgreSQL `ERROR: deadlock detected`, `jstack`의 `Found one Java-level deadlock:` | 대기 그래프의 사이클 | 락 획득 순서가 하나의 전순서인가 | [04-4](../04-graph-theory-basics/2-summary.md) · [os/19](../../os/19-deadlock/2-summary.md) |
| 정상 다이아몬드 의존에 "순환" 오류 | 출력된 사이클의 화살표 방향이 안 맞음 | 무방향 판정법을 방향 그래프에 씀 | 판정 알고리즘이 방향을 보나 | [04-5](../04-graph-theory-basics/2-summary.md) |
| 큰 입력의 재귀가 죽음 | `StackOverflowError`(실험: 1만 통과, 10만 실패) | 빼기형 점화식 — 재귀 트리 높이 n | 깊이가 n인가 log n인가 | [06-1](../06-recurrences-and-asymptotics/2-summary.md) · [06-4](../06-recurrences-and-asymptotics/2-summary.md) |
| "n log n이니 10배면 11배"가 100배 | 두 배 실험 4배 | 마스터 정리 잘못 적용(부분 문제 개수 a 누락) | 재귀 트리 두세 층의 층별 일 | [06-5](../06-recurrences-and-asymptotics/2-summary.md) |
| 알람 대부분이 오탐, 온콜이 무시 | 하루 수천~수만 건, 조치 비율 한 자릿수 % | 기저율 무시 — 유병률 0.1%·민감도 99%·특이도 99%면 PPV 약 9% | 베이즈: PPV = 민감도·기저율 / (민감도·기저율 + (1 − 특이도)(1 − 기저율)) | [07-1](../07-probability-and-bayes/2-summary.md) |
| 블룸 필터 뒤 DB 조회가 다시 늘음 | 위양성 1% → 15%(설계 2배 삽입) | 켜진 비트 비율 상승 → FP ≈ (켜진 비율)^k | 삽입 수 / 설계 n | [07-2](../07-probability-and-bayes/2-summary.md) |
| "에러의 70%가 Android"로 단정 | 전체 트래픽의 70%도 Android | 조건부 확률 방향 혼동 P(A\|에러) vs P(에러\|A) | 세그먼트별 에러율 | [07-3](../07-probability-and-bayes/2-summary.md) |
| 확률 0.999 출력인데 오분류 잦음 | 보정 곡선이 대각선에서 멂 | 상관된 특징을 독립으로 곱함 | 검증 집합의 보정 곡선 | [07-4](../07-probability-and-bayes/2-summary.md) |
| 99.9999% 이중화가 한 번에 둘 다 다운 | 두 복제본 다운 시작 시각이 같음 | 독립 가정한 가용성 곱 — 공통 원인 | 같은 AZ·랙·배포 시각인가(실험: 동시 다운 확률 500배) | [08-2](../08-expectation-variance-tails/2-summary.md) |
| 인스턴스 p99 평균이 사용자 p99와 다름 | 트래픽 적은 인스턴스가 평균을 흔듦 | 백분위는 선형이 아님 | 히스토그램 버킷 합친 뒤 백분위 | [08-3](../08-expectation-variance-tails/2-summary.md) |
| 무작위로 n번 데웠는데 미스 많음 | 키의 약 37%가 비어 있음 | 쿠폰 수집 — 다 덮으려면 기대 n·H_n | (1 − 1/n)^n ≈ e⁻¹ | [08-4](../08-expectation-variance-tails/2-summary.md) |
| 샤드 하나만 CPU 100% | 샤드 요청 수가 평균의 2배, 상위 키 하나가 8% | Zipf — 해시는 키를 나눌 뿐 요청을 나누지 않음 | 상위 키 비율 | [09-2](../09-common-distributions/2-summary.md) |
| 캐시 적중률이 테스트 70% → 운영 45% | DB QPS가 계획의 두 배 가까이 | Zipf 지수 s가 다름(s=1에서 74%, 0.8에서 47%) | 운영 로그로 s 추정 | [09-3](../09-common-distributions/2-summary.md) |
| 재시도 3번이면 97%라 했는데 다 실패 | 재시도 횟수가 상한에 붙음 | 기하분포·무기억성은 독립 시도에서만 | 실패의 시간 상관(같은 장애 구간인가) | [09-5](../09-common-distributions/2-summary.md) |
| 복구 직후 재시도가 한꺼번에 | 인스턴스 재시도 시각이 ms 단위로 같음 | 같은 시드 → 같은 지터 수열(실험: 100대가 한 칸) | 지터 난수의 시드 출처 | [12-1](../12-randomness-and-prng/2-summary.md) |
| 재설정 링크·세션 탈취 | 실패 없이 첫 시도에 맞는 토큰 | LCG 출력에서 상태 복원 — 반환값 전체가 토큰에 드러날 때(실험: `nextDouble` 값 하나로 다음 5개 일치) | 토큰 생성기가 `Math.random`·`Random`인가 | [12-2](../12-randomness-and-prng/2-summary.md) |
| 추첨·A/B 배정 편향 | 특정 순열 25% 더 많음, JS 비교자 셔플은 원래 순서 2.2배 | 경우의 수가 n!로 나뉘지 않는 셔플(n^n 경로 셔플은 n ≥ 3에서) | 순열 빈도의 카이제곱 | [12-3](../12-randomness-and-prng/2-summary.md) |
| `rand() % 2`가 A, B, A, B | 주기 2 패턴 | 법 2^k이고 a·c가 홀수인 LCG의 최하위 비트 주기 2 | 하위 비트 수열 출력 | [12-4](../12-randomness-and-prng/2-summary.md) |
| 어떤 질의든 같은 긴 문서가 상위 | 상위 결과 노름이 평균의 13배 | 정규화 없는 내적 — 점수에 길이가 곱해짐 | 결과 벡터의 노름 분포 | [13-1](../13-linear-algebra-essentials/2-summary.md) |
| 모델 교체 뒤 일부 결과가 엉뚱 | 오류 없이 낮은 점수 | 서로 다른 좌표계의 벡터를 내적 | 저장 벡터의 모델 버전 | [13-2](../13-linear-algebra-essentials/2-summary.md) |
| 배치가 크기 대비 비선형으로 느려짐 | CPU 바쁜데 IPC 낮음, 캐시 미스 큼(실험: 9.3~10.8배) | 열 우선 순회 — 행 길이만큼 점프 | 안쪽 루프의 인덱스가 어느 차원인가 | [13-3](../13-linear-algebra-essentials/2-summary.md) |
| 벡터 수 증가로 p99 상승, ANN 뒤 결과 누락 | N 4배 → 지연 약 3.6~5.0배 | 무차별 O(N·d), ANN은 재현율과 맞바꿈 | 정확 탐색 대비 재현율 | [13-4](../13-linear-algebra-essentials/2-summary.md) |
| gzip 켰더니 응답이 커짐 | 1MB 무작위 +328 B, `.gz` 재압축 +23 B | 반복·치우침이 거의 남지 않음(H₀ ≈ 8비트/바이트는 신호일 뿐 — H₀ = 8이어도 반복이 있으면 준다) | 콘텐츠 타입, 표본 압축률 > 1 | [14-1](../14-information-theory-basics/2-summary.md) |
| 작은 업로드에 OOM | `OutOfMemoryError: Java heap space`, exit 137 | 엔트로피 0 근처 → 1,000:1(실험 1MB → 1,004 B) | 해제 누적 바이트·비율 상한 | [14-2](../14-information-theory-basics/2-summary.md) |
| 정정 부호가 있는데 값이 조용히 틀림 | 하위 계층 로그에 "정정함"만 | 1비트 정정 부호(d_min = 3)는 2비트 정정을 보장하지 않는다 — 해밍(7,4)을 최근접 부호어로 복호하면 2비트 오류를 잘못 고친다(실험 336가지 전부) | 부호의 최소 거리, EDAC `ce_count`·`ue_count` | [14-3](../14-information-theory-basics/2-summary.md) |
| CRC 검증을 통과한 변조 | 검증 성공 로그 + 악성 내용 | CRC는 선형·키 없음 | 무결성 목적이 위조 방지인가 | [14-5](../14-information-theory-basics/2-summary.md) |

### 7. 어림 계산 모음 — 식 한 줄로 원인 후보를 가른다

```text
  질문                                   식 (전제)                                          예
  ─────                                  ─────────                                          ──
  k개 무작위 ID가 겹칠 확률은?             P ≈ 1 − exp(−k(k−1)/2N), N = 2^b (균일·독립)       b=32, k≈77,163 → 0.5
  알람 중 진짜 비율은?                     PPV = s·p / (s·p + (1−t)(1−p))                      s=t=0.99, p=0.001 → 9.02%
                                          (s 민감도, t 특이도, p 기저율)
  이용률이 오르면 대기는?                  Wq = ρ/(1−ρ) · E[S]  (M/M/1, 정상 상태, ρ < 1)       ρ 0.8 → 0.9: 4 → 9
  평균 동시 처리 수는?                     L = λ × W  (장기 평균, 안정 상태)                    λ=200/s, W=1s → 200
  체크섬이 놓칠 기대 건수는?               손상 블록 수 × 2^(−r)  (오류 패턴이 고르게 무작위)    r=8 → 1/256
  정수가 부동소수에서 사라지는 곳은?        float 2^24 = 16,777,216, double 2^53                 float 카운터가 멈춘 값
  모듈러 곱이 long에서 안전한가?            (m−1)² ≤ 2^63−1  ⇔  m ≤ 3,037,000,500              m = 40억은 넘침
  "독립" 곱셈이 맞나?                      P(A∧B) = P(A)·P(B) 는 독립일 때만                    같은 AZ면 공통 원인 항 추가
```

- 기호: k 개수, N 칸 수, b 비트 수, ρ 이용률(= λ·E[S] / 서버 수), λ 도착률, W 평균 체류 시간, E[S] 평균 서비스 시간, r 체크섬 비트 수.
- 각 식의 출처·정확식·근사 오차는 leaf에 있다. 생일([05](../05-counting-and-birthday-bound/2-summary.md)), 베이즈([07](../07-probability-and-bayes/2-summary.md)), 큐잉·Little([10](../10-queueing-and-littles-law/2-summary.md)), 체크섬([14](../14-information-theory-basics/2-summary.md)), 부동소수([15](../15-numerical-stability/2-summary.md)), 모듈러([11](../11-modular-arithmetic/2-summary.md)), 독립([08](../08-expectation-variance-tails/2-summary.md)).
- 전제가 깨진 곳에서는 그 식의 값을 그대로 쓸 수 없다. 생성 모형을 다시 세워 계산한다. 예: 생일 식은 균일·독립 생성기에서의 확률이다. 독립·동일 분포인데 값만 치우쳤다면 균일 식은 하한이다(균일일 때 충돌 확률이 가장 작다 — N = 50, k = 8 계산: 균일 0.446, 치우친 분포 2,000개 중 최소 0.544). 독립이 깨지면 하한도 아니다 — 같은 시드면 훨씬 잦고, 순차 발급이면 k ≤ N에서 0이다.

### 8. 증상별 "하지 말 것" 한 줄

| 증상 | 하지 말 것 | 대신 |
|---|---|---|
| 정렬 계약 예외 | `useLegacyMergeSort`로 덮음 | 비교자를 전전순서로(양자화·`Double.compare`·`thenComparing`) |
| 음수 인덱스 | `Math.abs(h) % n` | `Math.floorMod(h, n)`, 규칙을 명세로 |
| 간헐 ID 충돌 | 재시도로 덮음, upsert로 덮어씀 | 생일 어림 → 비트 수 늘리기·순번 ID, 생성기 시드 점검 |
| 합계 불일치 | 차이를 "반올림 오차"로 넘김 | 차이의 모양(한 건·소수·순서·NULL)으로 원인을 가름 |
| 이용률 절벽 | 이용률 90% 목표로 운영 | ρ/(1−ρ)로 여유를 잡고 대기 지표로 스케일 |

## 쓰이는 자료구조·알고리즘

- **역색인·결정 트리**: 이 노트의 뼈대([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)). 결정 트리의 질문은 확인 비용이 싼 것부터 둔다.
- **어림 계산 → 측정**: 7절의 식으로 가설을 고르고, leaf의 실험 방법(진리표 전수, 두 배 실험, 시뮬레이션, 히스토그램)으로 확정한다.
- **이 노트가 가리키는 구조·알고리즘**: 정렬·비교자([algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md)), 해시·모듈러([algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)), 위상정렬·사이클 탐지([04](../04-graph-theory-basics/2-summary.md)), 큐·풀([database/21-connection-pooling](../../database/21-connection-pooling/2-summary.md)), 보상 합([15](../15-numerical-stability/2-summary.md)).
- **쓰이는 곳(🔧)**: 장애 대응의 "수학 원인" 갈래. 운영 색인([reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md))의 지연 급증·데이터 불일치에서 이 노트로 내려온다.

## 적용 — 풀어나가는 법

### 1. 증상을 받으면 이 순서로

1. 원문·크기·분포·비율을 모은다(0-1절).
2. 0절 표에서 깨진 전제를 고른다. 예외 이름이 있으면 그 절로, 없으면 "숫자가 틀림(4절) / 느림(5절) / 겹침(3절)"으로.
3. 결정 트리의 질문을 위에서부터 묻는다.
4. 7절의 식으로 어림한다. 어림과 관측이 차수까지 맞는지 본다.
5. 원인이 둘 이상 남으면 둘을 가르는 입력을 하나 만든다. 예: 음수 해시 키 하나, 길이 0·1·2 입력, 병렬도 1과 8, 같은 시드로 뜬 인스턴스 두 대.
6. leaf의 처방으로 간다. 처방이 "덮기"(예외 숨김·재시도·한도 상향)뿐이면 8절을 다시 본다.

### 2. 첫 진단 명령·질의

```bash
jcmd <pid> Thread.print > d1.txt; sleep 3; jcmd <pid> Thread.print > d2.txt   # 같은 줄이면 종료 척도 문제(6절 02-2)
jcmd <pid> Thread.print | grep -A3 'Found one Java-level deadlock'           # 대기 그래프 사이클(04-4)
jcmd <pid> VM.system_properties | grep -i legacymergesort                    # 계약 예외를 덮는 옵션이 켜져 있나
```

```sql
-- 합계 불일치: NULL 행이 허용·거부 어디에도 안 잡히나 (01-4)
SELECT count(*) FILTER (WHERE blocked) AS t, count(*) FILTER (WHERE NOT blocked) AS f,
       count(*) FILTER (WHERE blocked IS NULL) AS unknown, count(*) AS total FROM users;
```

- 이용률 절벽은 지표 두 개(처리율 λ, 평균 서비스 시간 E[S])로 ρ를 계산하는 데서 시작한다. 풀이면 풀 크기를 서버 수로 본다([10](../10-queueing-and-littles-law/2-summary.md)).

### 3. 어림 계산을 코드로 — Java 21

```java
final class MathTriage {
    // 3절: 무작위 b비트 ID k개의 충돌 확률 (균일·독립 가정)
    static double birthday(long k, int bits) {
        double n = Math.pow(2, bits);
        return -Math.expm1(-(double) k * (k - 1) / (2 * n));     // 1 − exp(−k(k−1)/2N)
    }
    // 6절 07-1: 양성 예측도
    static double ppv(double sens, double spec, double base) {
        return sens * base / (sens * base + (1 - spec) * (1 - base));
    }
    // 5절 10-1: M/M/1 평균 대기 (E[S] 단위), ρ >= 1 이면 정상 상태가 없다
    static double mm1Wait(double rho) {
        if (rho >= 1) throw new IllegalArgumentException("rho >= 1: 정상 상태가 없어 평균 대기가 정의되지 않는다");
        return rho / (1 - rho);
    }
    // 2절 11-1: 샤드 인덱스 — 음수 해시에서도 0..n-1
    static int shard(int hash, int n) { return Math.floorMod(hash, n); }

    public static void main(String[] a) {
        System.out.printf("32bit k=77,163: %.3f%n", birthday(77_163, 32));
        System.out.printf("PPV(0.99,0.99,0.001): %.4f%n", ppv(0.99, 0.99, 0.001));
        System.out.printf("Wq rho 0.8 -> 0.9: %.1f -> %.1f%n", mm1Wait(0.8), mm1Wait(0.9));
        System.out.println("shard(-7, 3) = " + shard(-7, 3) + "  vs  -7 % 3 = " + (-7 % 3));
    }
}
```

(실행, eclipse-temurin:21-jdk = OpenJDK 21.0.12, docker `--network none --cpus=2`, `java MathTriage.java`, 2026-10-07)

```text
32bit k=77,163: 0.500
PPV(0.99,0.99,0.001): 0.0902
Wq rho 0.8 -> 0.9: 4.0 -> 9.0
shard(-7, 3) = 2  vs  -7 % 3 = -1
```

- 출력은 leaf의 계산·시뮬레이션 값과 맞는다(32비트 k = 77,163에서 0.5000 — [05](../05-counting-and-birthday-bound/2-summary.md), PPV 9.02% — [07](../07-probability-and-bayes/2-summary.md), 4 → 9 — [10](../10-queueing-and-littles-law/2-summary.md), `-7 % 3` = −1·`floorMod` = 2 — [11](../11-modular-arithmetic/2-summary.md)). 식의 확인일 뿐 운영 측정이 아니다.
- `Math.expm1`을 쓰는 이유: k²/2N이 아주 작을 때 `1 - Math.exp(x)`는 파국적 상쇄로 유효 숫자를 잃는다([15](../15-numerical-stability/2-summary.md)).

## 장애 시나리오와 대처

### 1. 예외만 없애고 틀린 결과를 남김

- **현상**: `Comparison method violates its general contract!`가 나서 `useLegacyMergeSort`를 켰다. 예외는 사라졌다. 화면 순서가 가끔 이상하다는 문의가 온다.
- **보이는 형태**: 정렬 결과를 올바른 기준으로 재검사하면 역전 쌍이 나온다(`Near.java` 실험: 분포·크기에 따라 200회 중 26~200회가 예외 없이 역전).
- **원인**: 예외는 비교자 추이성 위반의 **증상**이었다. 위반은 그대로다([03-2](../03-sets-relations-orders/2-summary.md)).
- **대처**: 비교자를 전전순서로 다시 쓴다(허용 오차 대신 양자화한 키). 정렬 결과 검증을 테스트에 둔다. 사례는 [17-math-incidents](../17-math-incidents/2-summary.md) 사건 2.

### 2. "확률상 안 겹친다"를 믿고 충돌을 재시도로 덮음

- **현상**: ID 충돌이 하루 몇 건씩 나서 재시도 로직을 넣었다. 몇 달 뒤 충돌이 하루 수십 건이 됐다.
- **보이는 형태**: 하루 발급량이 일정해도 하루 `duplicate key` 건수가 누적 행 수에 비례해 는다(하루 m개를 k행에 넣으면 하루 기대 충돌 ≈ m·k/N). 지금까지의 누적 충돌 쌍은 k²에 비례한다.
- **원인**: 생일 한계 — k개 안의 충돌 쌍 기대 수는 k(k−1)/2N이다. 행 수가 두 배면 누적 충돌 쌍의 기대 수가 네 배, 새 행 하나가 기존 행과 부딪힐 확률(≈ k/N)은 두 배다([05-1](../05-counting-and-birthday-bound/2-summary.md)).
- **대처**: 지금 k와 1년 뒤 k로 7절 식을 계산한다. 비트 수를 늘리거나 순번 ID로 바꾼다. 관측 빈도가 어림보다 훨씬 잦으면 생성기 시드부터 본다([05-3](../05-counting-and-birthday-bound/2-summary.md)).

### 3. 합계 차이를 전부 "부동소수 오차"로 분류

- **현상**: 정산 대사 차이를 "반올림 오차"로 분류해 무시해 왔다. 감사에서 매일 한 건씩 누락된 것이 드러났다.
- **보이는 형태**: 차이가 매일 마지막 거래 한 건의 금액과 같았다. 소수가 아니었다.
- **원인**: 원인이 둘 섞여 있었다. 부동소수 누적([15-1](../15-numerical-stability/2-summary.md))과 루프 경계 off-by-one([02-1](../02-induction-and-invariants/2-summary.md)).
- **대처**: 차이의 **모양**으로 먼저 가른다(4절 결정 트리). 금액은 정수·`BigDecimal`로 누적해 반올림 갈래를 없애면 남는 차이가 진짜 결함이다.

### 4. 이용률 90%를 "효율적"이라 보고 목표로 잡음

- **현상**: 비용 절감으로 인스턴스를 줄여 CPU 이용률을 60%에서 90%로 올렸다. 평소엔 괜찮다가 트래픽이 조금 늘자 타임아웃이 쏟아진다.
- **보이는 형태**: 이용률 90%대, 풀 대기 시간 급등, 오류율은 늦게 오른다.
- **원인**: Wq = ρ/(1−ρ) · E[S]. ρ 0.6에서 1.5, 0.9에서 9, 0.95에서 19(E[S] 단위). 마지막 몇 %가 대기를 몇 배로 만든다([10-1](../10-queueing-and-littles-law/2-summary.md)).
- **대처**: 지연 목표에서 거꾸로 목표 ρ를 정한다. 이용률이 아니라 대기·지연으로도 스케일한다.

### 5. 같은 식을 전제가 다른 곳에 씀

- **현상**: 포아송 가정으로 용량을 잡고(09), 독립 가정으로 가용성을 곱하고(08), 균일 가정으로 ID 비트를 정했다(05). 각각 계산상 넉넉했는데 셋 다 운영에서 깨졌다.
- **보이는 형태**: 계산 대비 실제 실패 빈도가 차수 단위로 크다. 실패가 특정 시각·특정 AZ·특정 배포에 몰린다.
- **원인**: 식은 맞았다. 전제(독립·균일)가 운영에서 성립하지 않았다. 공통 원인이 사건들을 묶었다.
- **대처**: 식을 쓸 때 전제를 같은 줄에 적는다(7절 표의 괄호). 실패가 시각·장소에 몰리는지 보는 지표를 둔다. 공통 원인 항을 계산에 넣는다([08-2](../08-expectation-variance-tails/2-summary.md)).

## 핵심 문장

- 이 노트는 **증상 → 보이는 형태 → 깨진 수학 전제 → 어림·측정 → leaf** 순서의 역색인이다.
- 수학 증상의 대부분은 공식이 틀려서가 아니라 **전제**(균일·독립, 정상 상태, 정수 범위, 전순서, 결합법칙)가 운영에서 깨져서 보인다.
- 커리큘럼의 다섯 증상은 각각 한 전제에 대응한다. 정렬 예외 = 비교자 계약(추이성 등), 음수 나머지 = `%`의 정의, 간헐 ID 충돌 = 생일 한계(균일 가정), 합계 불일치 = 반올림·경계·3치 논리, 이용률 절벽 = ρ/(1−ρ).
- 어림 계산 한 줄로 원인 후보를 고르고, 관측과 차수까지 맞는지 본다. 맞지 않으면 그 식의 전제가 깨진 것을 의심한다.
- 예외를 덮는 처방(`useLegacyMergeSort`, 재시도, 한도 상향, "반올림 오차" 분류)은 전제 위반을 그대로 둔다.

## 관련 주제·근거

- 선행: 이 영역 leaf 01~15 전체([math README](../README.md)). 표기 `NN-k`는 각 leaf 「장애 시나리오와 대처」의 k번째 시나리오다.
  - [01-propositional-logic](../01-propositional-logic/2-summary.md) · [02-induction-and-invariants](../02-induction-and-invariants/2-summary.md) · [03-sets-relations-orders](../03-sets-relations-orders/2-summary.md) · [04-graph-theory-basics](../04-graph-theory-basics/2-summary.md) — 논리·증명·관계·그래프
  - [05-counting-and-birthday-bound](../05-counting-and-birthday-bound/2-summary.md) · [06-recurrences-and-asymptotics](../06-recurrences-and-asymptotics/2-summary.md) · [11-modular-arithmetic](../11-modular-arithmetic/2-summary.md) — 세기·점화식·모듈러
  - [07-probability-and-bayes](../07-probability-and-bayes/2-summary.md) · [08-expectation-variance-tails](../08-expectation-variance-tails/2-summary.md) · [09-common-distributions](../09-common-distributions/2-summary.md) · [12-randomness-and-prng](../12-randomness-and-prng/2-summary.md) — 확률
  - [13-linear-algebra-essentials](../13-linear-algebra-essentials/2-summary.md) · [14-information-theory-basics](../14-information-theory-basics/2-summary.md) · [15-numerical-stability](../15-numerical-stability/2-summary.md) · [10-queueing-and-littles-law](../10-queueing-and-littles-law/2-summary.md) — 선형대수·정보·수치·큐잉
- 후속: [17-math-incidents](../17-math-incidents/2-summary.md) — Debian OpenSSL PRNG(2008), Java 7 TimSort 계약 예외, TimSort 형식 검증(de Gouw 외 2015)
- 다른 영역 색인: [algorithm/42-alg-symptom-index](../../algorithm/42-alg-symptom-index/2-summary.md) · [data-structure/43-ds-symptom-index](../../data-structure/43-ds-symptom-index/2-summary.md) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) · [security/29-security-symptom-index](../../security/29-security-symptom-index/2-summary.md)
- 근거
  - 표의 메시지·수치는 각 leaf의 실험 출력과 인용을 옮겼다(OpenJDK 21.0.12 Temurin 컨테이너 등, 2026-10-07 판). 각 수치의 환경·시드·반복 수는 해당 leaf의 「실험」 절에 있다.
  - JLS §15.17.3(나머지 연산자), §4.2.2(정수 연산의 넘침), §14.10(`assert`) — [11](../11-modular-arithmetic/2-summary.md)·[02](../02-induction-and-invariants/2-summary.md)에서 확인한 범위.
  - Little 1961, M/M/1·P-K 식 — [10](../10-queueing-and-littles-law/2-summary.md)의 근거 목록. 생일 한계 — MCS 17.4 The Birthday Principle·CLRS 3판 5.4(소절 번호는 확인 못 함), [05](../05-counting-and-birthday-bound/2-summary.md)의 근거 목록.
- 실험 목록
  - `MathTriage.java`(적용 3의 코드 그대로) — 생일·PPV·M/M/1·`floorMod` 어림 식이 leaf 값과 같은지. `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp -v <dir>:/w -w /w eclipse-temurin:21-jdk java MathTriage.java` 한 번(결정적 계산). 2차 리뷰 판정에서 예외 메시지만 고친 판을 다시 돌려 같은 출력을 확인했다. 그 밖의 수치는 leaf 실험에서 옮겼다.
  - `skew.py`(2차 리뷰 판정 보조, Python 3.12.3 호스트) — 7절의 "치우친 독립 분포에서는 균일 식이 하한" 확인: N = 50, k = 8의 정확 충돌 확률(기본 대칭 다항식), 균일 0.446 vs 무작위로 치우친 분포 2,000개(`random.seed(1)`) 중 최소 0.544.
