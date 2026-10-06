# algorithm/09-sorting-in-practice — 실전 정렬: 안정성·비교자 계약·TimSort·다중 키 — 정리 (힌트)

## 해결하는 문제

실무에서 정렬 알고리즘을 직접 짜는 일은 드물다. `list.sort(cmp)` 한 줄이면 된다.\
그런데 그 한 줄이 틀리는 지점은 알고리즘이 아니라 **계약**에 있다.

```text
  내가 주는 것                         라이브러리가 약속하는 것
  ───────────────────────────         ──────────────────────────────────
  비교자 compare(a, b)        ──▶     "비교자가 계약을 지키면" 정렬된 결과
   · 대칭 · 추이 · 0의 일관성            · 객체 정렬은 안정(같은 키의 원래 순서 유지)
                                       · O(n log n), 거의 정렬된 입력은 약 n번 비교
  계약을 어기면 ──▶ 예외 또는 조용히 틀린 순서
```

쉬운 예: 반 명단을 "이름순"으로 줄 세운 뒤 "점수순"으로 다시 세운다.
- 점수가 같은 학생들이 이름순으로 남아 있으면 그 정렬은 *안정*하다.
- 안정하지 않으면 동점자 순서가 뒤죽박죽이 되어 "점수, 그다음 이름" 명단이 안 나온다.

똑같은 구조다.\
실무 예:
- 주문 목록 API를 `ORDER BY created_at LIMIT 20 OFFSET 20`으로 페이지를 나눴더니 같은 초에 생긴 주문이 1페이지와 2페이지에 둘 다 나오고, 어떤 주문은 어느 페이지에도 안 나온다.
- 배포 후 특정 데이터에서만 `java.lang.IllegalArgumentException: Comparison method violates its general contract!`가 난다.

## 동작·원리

### 1. 안정성 — 같은 키의 원래 순서를 지키나

```text
  입력 (도시, 날짜)            날짜로 안정 정렬               날짜로 불안정 정렬(예)
  ① Seoul  3                  ② Busan  1                    ② Busan  1
  ② Busan  1                  ④ Seoul  1   ← ②가 ④보다 앞    ④ Seoul  1
  ③ Busan  3                  ① Seoul  3   ← ①이 ③보다 앞    ③ Busan  3   ← 뒤바뀔 수 있다
  ④ Seoul  1                  ③ Busan  3                    ① Seoul  3
```

- *안정 정렬(stable sort)*: 비교 결과가 0인(같은 키) 원소들의 입력 순서를 결과에서도 유지하는 정렬.
  - 흔한 오해: "안정성은 원시값 정렬에도 중요하다." — `int` 두 개가 같으면 구별할 방법이 없어 안정성이 보이지 않는다. 실무에서 안정성이 문제 되는 것은 키 말고 다른 필드를 가진 **객체**를 정렬할 때다(드문 예외: `double` 정렬은 모든 NaN을 같은 값으로 보지만 NaN끼리 비트 패턴은 다를 수 있다 — `Arrays.sort(double[])` Javadoc).
- 안정 정렬이면 **2차 키로 먼저 정렬하고 1차 키로 다시 정렬**해 다중 키 정렬을 만들 수 있다(기수 정렬의 LSD 방식과 같은 원리 → [05-non-comparison-sort](../05-non-comparison-sort/2-summary.md)).
- 더 흔한 방법은 비교자 하나에 키를 이어 붙이는 것이다: `comparing(City).thenComparing(Day)`.

### 2. 비교자 계약 — 정렬이 기대는 수학

`java.util.Comparator` Javadoc(OpenJDK 21)이 요구하는 세 조건:

```text
  ① 대칭(반대칭):  sgn(compare(x, y)) == -sgn(compare(y, x))
  ② 추이:         compare(x, y) > 0 이고 compare(y, z) > 0 이면 compare(x, z) > 0
  ③ 0의 일관성:    compare(x, y) == 0 이면 모든 z에 대해 sgn(compare(x, z)) == sgn(compare(y, z))
```

- 이 세 조건을 지키는 비교자는 원소들 위에 *전순서*(같음은 동치류로 묶은 순서, 엄밀히는 total preorder)를 준다. 순서 관계의 정의는 [math 영역 03-sets-relations-orders](../../math/03-sets-relations-orders/2-summary.md).
- 흔히 깨지는 모양 세 가지:

```java
Comparator<Integer> neverZero = (x, y) -> x < y ? -1 : 1;   // compare(x, x) = 1 → ① 위반
Comparator<Integer> subtract  = (x, y) -> x - y;            // 큰 차이에서 int 오버플로 → ② 위반
Comparator<Integer> random    = (x, y) -> rnd.nextInt(3) - 1; // 아무것도 안 지킴
// 올바른 형태: Integer.compare(x, y) 또는 Comparator.naturalOrder()
```

- `subtract`가 틀리는 이유: `Integer.MIN_VALUE - 1`은 `Integer.MAX_VALUE`로 넘어간다. "아주 작은 수 − 양수"가 양수가 되어 "더 크다"로 판정된다.
- `compare == 0`은 "같은 원소"라는 뜻으로도 쓰인다. `TreeSet`·`TreeMap`은 `equals`가 아니라 `compare == 0`으로 중복을 판단한다(아래 실험).

### 3. TimSort — Java 객체 정렬의 실제 알고리즘

OpenJDK 21에서 어떤 정렬이 도는지(소스 `java/util/Arrays.java`·`ArrayList.java`·`Collections.java`·`List.java`):

```text
  호출                                   실제 알고리즘                     안정?
  ─────────────────────────────────────  ───────────────────────────────  ─────
  Arrays.sort(int[]/long[]/double[]…)    DualPivotQuicksort                해당 없음(원시값)
  Arrays.sort(Object[])                  ComparableTimSort                 예
  Arrays.sort(T[], Comparator)           TimSort                           예
  List.sort / Collections.sort           → Arrays.sort(배열, cmp)           예
   (ArrayList는 내부 배열을 바로 정렬)
  -Djava.util.Arrays.useLegacyMergeSort=true  옛 병합 정렬(계약 위반 검사 없음)
```

- `DualPivotQuicksort` 클래스 주석: 피벗 두 개의 퀵 정렬(Yaroslavskiy·Bentley·Bloch)이고, 상황에 따라 혼합 삽입 정렬, run 병합, 힙 정렬, 계수 정렬로 갈라진다.
- TimSort는 Tim Peters가 Python용으로 만든 것(`listsort.txt`)을 Josh Bloch가 Java로 옮겼다(`TimSort.java` 머리 주석).

TimSort의 뼈대:

```text
  입력:  [ 1 2 5 9 | 8 6 3 | 4 7 10 11 12 | ... ]
          └ 오름차순 run ┘└ 내림차순 run → 뒤집어 오름차순으로
                                         └ run이 minRun보다 짧으면 이진 삽입 정렬로 늘림

  run 스택 (위가 최신)          병합 규칙: 스택 위쪽 run 길이가 불변식을 깨면 이웃끼리 병합
   ┌──────┐ C                  (이웃끼리만 병합 → 같은 키가 run을 건너뛰지 않음 → 안정)
   │ 20   │
   ├──────┤ B
   │ 30   │                    병합 중 한쪽이 연속 minGallop번(처음 7) 이기면
   ├──────┤ A                  "갤럽 모드": 지수 탐색으로 한 번에 덩어리째 옮김
   │ 80   │
   └──────┘
```

- *run*: 입력에 이미 있는 오름차순(또는 엄격한 내림차순) 연속 구간.
- *minRun*: 짧은 run을 이진 삽입 정렬로 늘려 맞추는 최소 길이. OpenJDK는 `MIN_MERGE = 32`이고, 길이가 32 미만인 배열은 병합 없이 이진 삽입 정렬로 끝낸다(`TimSort.sort`의 `nRemaining < MIN_MERGE` 분기).
- *갤럽 모드(galloping)*: 한쪽 run이 계속 이기면 1칸씩 비교하는 대신 지수 탐색으로 경계를 찾는다. 시작 문턱 `MIN_GALLOP = 7`(Java·CPython 둘 다).
- 정렬 중에 run 경계·병합 결과가 불가능한 상태를 만나면 `IllegalArgumentException("Comparison method violates its general contract!")`를 던진다(`TimSort.java`의 `mergeLo`·`mergeHi`). **비교자 계약 위반을 우연히 발견했을 때만** 던진다 — 검사기가 아니다.

참고 — TimSort 자체의 버그와 수정:
- de Gouw 외(CAV 2015)는 정형 검증 중 `mergeCollapse`가 run 스택 불변식을 스택 위 3개만 검사해 전체 불변식이 깨질 수 있음을 보였다. 길이 67,108,864 배열에서 `ArrayIndexOutOfBoundsException`이 나는 입력을 만들었다.
- OpenJDK는 처음에 run 스택 배열 길이만 늘렸고(JDK-8072909, JDK 9 — 최대 40 → 49), 이후 JDK-8203864(JDK 11에서 해결)에서 `mergeCollapse`를 고쳤다. OpenJDK 21 소스의 `mergeCollapse`는 위 4개(`n-2`까지)를 검사한다.
- CPython은 3.11부터 병합 순서 규칙을 Munro–Wild의 powersort로 바꿨다(bpo-34561). Java TimSort와 병합 순서가 다르다.

### 실험: 계약 위반은 언제 예외가 되나

```java
for (int trial = 0; trial < 20; trial++) {
    Random r = new Random(trial);
    List<Integer> list = new ArrayList<>();
    for (int i = 0; i < 2000; i++) list.add(subtractCase ? r.nextInt() : r.nextInt(50));
    try { list.sort(cmp); } catch (IllegalArgumentException ex) { fail++; }
}
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, `java Contract.java`, n=2000, 시드 0~19, 2026-10-05)

```text
neverZero: 20회 중 예외 17회  Comparison method violates its general contract!
subtract: 20회 중 예외 3회  Comparison method violates its general contract!
random: 20회 중 예외 18회  Comparison method violates its general contract!
```

같은 코드를 `-Djava.util.Arrays.useLegacyMergeSort=true`로 돌리면:

```text
neverZero: 20회 중 예외 0회
subtract: 20회 중 예외 0회
random: 20회 중 예외 0회
```

예외가 없을 때 결과는 맞나, 크기에 따라 어떻게 달라지나(`Contract2.java`, 같은 환경 — `neverZero` 행은 값을 0~4에서 뽑아 위 실험(0~49)보다 같은 값이 많다. 그래서 n=2000의 예외 빈도를 위의 20회 중 17회와 바로 비교하지 않는다):

```text
subtract n=2000: 예외 3회, 예외 없이 순서가 틀린 결과 17회 (20회 중)
neverZero n=31: 200회 중 예외 0회
neverZero n=32: 200회 중 예외 4회
neverZero n=64: 200회 중 예외 81회
neverZero n=2000: 200회 중 예외 200회
```

- 같은 비교자라도 **데이터에 따라** 예외가 나기도, 안 나기도 한다. 그래서 "특정 고객 데이터에서만" 터진다.
- 예외가 안 난 17회는 **조용히 틀린 순서**였다. 예외는 오히려 운이 좋은 경우다.
- 31개 이하에서는 병합 단계가 없어 예외가 0회였다(`MIN_MERGE = 32` 분기와 일치). 작은 단위 테스트로는 위반이 안 잡힌다.
- `useLegacyMergeSort`는 예외를 없애 줄 뿐 비교자를 고치지 않는다(계약을 어긴 비교자에는 "올바른 순서"가 정의되지 않는다 — 해석. 이 실험은 legacy 결과의 순서를 검사하지 않았다). 소스 주석도 "향후 릴리스에서 제거 예정"이라고 적는다.

### 실험: TimSort는 입력의 기존 순서를 쓴다

(실험, 같은 환경, `java Adaptive.java`, `Integer[]` 100만 개, 비교 횟수를 센 비교자, 2026-10-05)

```text
n=1,000,000  n*log2(n)=19,931,568
random             comparisons=18,640,462
sorted             comparisons=999,999
reversed           comparisons=999,999
twoRuns            comparisons=1,999,998
nearly(100 swaps)  comparisons=1,013,397
```

- 이미 정렬된 입력과 엄격한 역순 입력은 n−1번 비교로 끝난다. 역순은 run 하나로 보고 뒤집는다.
- 정렬된 두 덩어리를 이어 붙인 입력은 약 2n번. Javadoc의 "정렬된 배열 여럿을 이어 붙여 정렬하면 병합에 잘 맞는다"는 문장이 이것이다.
- 무작위 입력은 n log₂ n보다 조금 적다. 점근 차수는 같다.

### 실험: 원시 배열 vs 객체 배열

(실험, 같은 환경, `java -Xmx1g Prim.java`, 무작위 `int`, 반복 5회 중 3~5번째, 2026-10-05)

```text
n=1,000,000 rep2 int[] 273ms  Integer[] 1346ms
n=1,000,000 rep3 int[] 301ms  Integer[] 1192ms
n=1,000,000 rep4 int[] 328ms  Integer[] 1036ms
n=4,000,000 rep2 int[] 1407ms  Integer[] 6083ms
n=4,000,000 rep3 int[] 1195ms  Integer[] 5386ms
n=4,000,000 rep4 int[] 1173ms  Integer[] 5219ms
```

- 이 환경에서 `Integer[]`가 `int[]`보다 약 3.2~4.9배 느렸다(사실 점검 재실행 두 번은 3.4~4.5배). 박싱된 객체는 참조를 따라가야 해 캐시 지역성이 나쁘고 비교가 메서드 호출을 거친다(해석).
- 절대 시간은 `--cpus=2` 제한과 다른 작업이 함께 도는 호스트의 값이다. 다른 장비에서는 다르다. 측정 방법의 한계는 [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **이 주제가 쓰는 하위 구조**
  - 병합(안정성의 원천) → [algorithm/02-merge-sort](../02-merge-sort/2-summary.md)
  - 이진 삽입 정렬(짧은 run 늘리기), 갤럽 모드의 지수·이진 탐색 → [01-elementary-sort](../01-elementary-sort/2-summary.md), [06-binary-search](../06-binary-search/2-summary.md)
  - run 스택(크기 불변식을 지키는 스택) → [data-structure/03-stack](../../data-structure/03-stack/2-summary.md)
  - 원시 배열: 듀얼 피벗 퀵 정렬과 그 폴백(힙 정렬) → [03-quick-sort](../03-quick-sort/2-summary.md), [04-heap-sort](../04-heap-sort/2-summary.md)
- **이 주제를 쓰는 곳(🔧)**
  - Java `List.sort`·`Collections.sort`·`Arrays.sort(Object[])`(TimSort), CPython `list.sort`(TimSort + powersort 병합 규칙), V8 `Array.prototype.sort`(v7.0부터 TimSort, ES2019부터 명세가 안정성 요구)
  - 다중 키 정렬: `ORDER BY a, b`, API `sort=city,-day` → [api-design/12-filtering-sorting-search](../../api-design/12-filtering-sorting-search/2-summary.md)
  - 페이지네이션의 결정적 순서 → [api-design/06-pagination](../../api-design/06-pagination/2-summary.md)
  - 문자열 정렬 순서(collation)는 비교자 자체가 로캘에 따라 다르다 → [database/10-collation-and-text-comparison](../../database/10-collation-and-text-comparison/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 비교자를 쓰는 순서

```text
  ① 키를 고른다            어떤 필드로? 1차·2차·…
  ② 각 키는 표준 비교로     Integer.compare, Long.compare, Comparator.comparing(...)
  ③ null·방향을 명시한다    nullsLast(...), reversed()
  ④ 동점 해소 키를 붙인다    마지막에 유일 키(id) — 결정적 순서
  ⑤ 테스트는 32개 이상, 무작위 + 동점 많은 데이터로
```

```java
record Order(long id, String city, LocalDate day, BigDecimal amount) {}

Comparator<Order> cmp = Comparator
        .comparing(Order::city, Comparator.nullsLast(Comparator.naturalOrder()))  // 1차
        .thenComparing(Order::day, Comparator.reverseOrder())                     // 2차, 최신 먼저
        .thenComparingLong(Order::id);                                            // 동점 해소(유일)
orders.sort(cmp);
```

- 뺄셈 비교(`a - b`), "같으면 1" 비교, 정렬 도중 바뀌는 필드(캐시된 점수·현재 시각)를 키로 쓰는 것을 피한다.
- `double` 키는 `Double.compare`를 쓴다. `NaN`을 `<`·`>`로 비교하면 어느 쪽도 참이 아니라 계약이 깨진다.

### 2. 코테 — 다중 키는 비교자 하나로

```java
// 점수 내림차순, 같으면 이름 오름차순
int[][] a = ...;                  // {score, nameIndex}
Arrays.sort(a, (x, y) -> x[0] != y[0] ? Integer.compare(y[0], x[0])
                                       : Integer.compare(x[1], y[1]));
```

- `int[][]`의 행은 객체라 TimSort(안정)가 돈다. `int[]` 한 줄을 정렬하는 것과 다르다.

### 실험: 안정 정렬 두 번 = 다중 키, 동점 순서가 흔들리면 페이지가 겹친다

```java
List<Order> s = new ArrayList<>(orders); s.sort(byDay); s.sort(byCity);   // 안정 정렬 두 번(2차 키 먼저)
List<Order> u = heapSort(heapSort(orders, byDay), byCity);                // 불안정 정렬 두 번(PriorityQueue)

// 페이지네이션 흉내: 질의마다 물리 순서가 달라지는 상황(셔플) → 정렬 → 100건씩 10페이지
for (int page = 0; page < 10; page++) {
    List<Order> shuffled = new ArrayList<>(orders); Collections.shuffle(shuffled, new Random(100 + page));
    List<Order> res = heapSort(shuffled, key);
    for (Order o : res.subList(page * 100, page * 100 + 100)) if (!seen.add(o.id())) dup++;
}
```

(실험, OpenJDK 21.0.12 Temurin, docker `--cpus=2`, `java Stable.java`, 주문 1,000건·도시 3개·날짜 30개, 2026-10-05 — 시뮬레이션)

```text
안정(List.sort) 두 번  == 정답 키 순서? true
불안정(힙) 두 번       == 정답 키 순서? false
ORDER BY day        : 10페이지 동안 중복 55건, 한 번도 안 나온 행 55건
ORDER BY day, id    : 10페이지 동안 중복 0건, 한 번도 안 나온 행 0건
```

- 이 시뮬레이션은 "DB가 동점 행을 질의마다 다른 순서로 돌려준다"를 셔플 + 불안정 정렬로 흉내 낸 것이다. 실제 DB 동작이 아니다.
- 실제 DB도 같은 경고를 한다. PostgreSQL 17 문서 7.6 LIMIT and OFFSET: "결과 행을 유일한 순서로 묶는 `ORDER BY`를 쓰지 않으면 예측할 수 없는 부분집합을 받는다", "다른 `LIMIT`/`OFFSET` 값마다 다른 계획(다른 행 순서)이 나올 수 있다."
- 대처는 정렬 알고리즘을 바꾸는 것이 아니라 **동점 해소 키(유일 키)를 붙이는 것**이다. 안정 정렬도 "입력 순서"를 지킬 뿐, 입력 순서가 질의마다 다르면 소용없다.

### 3. 진단

- `Comparison method violates its general contract!`의 스택 트레이스에서 `TimSort.mergeLo`/`mergeHi` 위의 **호출 지점**이 아니라 넘겨준 비교자를 본다.
- 재현: 운영 데이터 샘플을 덤프해 같은 비교자로 정렬한다. 32개 이상, 동점이 많을수록 잘 재현된다.
- 계약 검사 테스트: 무작위 세 원소 x, y, z를 뽑아 ①②③을 직접 확인하는 속성 기반 테스트를 둔다.

## 장애 시나리오와 대처

### 1. `Comparison method violates its general contract!` (⚠ 커리큘럼)

- **현상**: 배포 후 특정 고객·특정 날짜 데이터에서만 목록 API가 500. 테스트는 통과.
- **보이는 형태**: `java.lang.IllegalArgumentException: Comparison method violates its general contract!`, 트레이스에 `java.util.TimSort.mergeHi` 또는 `mergeLo`.
- **원인**: 비교자가 대칭·추이를 어긴다(같으면 1 반환, 뺄셈 오버플로, `NaN`, 정렬 중 바뀌는 키, 여러 필드를 일관되지 않게 섞은 비교). 31개 이하 입력은 병합을 안 해 테스트에서 안 보인다(실험).
- **대처**: `Integer.compare`·`Comparator.comparing().thenComparing()`으로 다시 쓴다. 키를 정렬 전에 스냅숏한다. `useLegacyMergeSort`로 덮지 않는다 — 예외가 사라질 뿐 비교자는 그대로 틀리다(기본 TimSort 실험: 20회 중 예외 없이 끝난 17회가 모두 틀린 순서. legacy 결과의 순서는 따로 검사하지 않았다).

### 2. 예외 없이 순서가 틀리다

- **현상**: 금액 순 랭킹에서 아주 큰 값과 아주 작은 값의 위치가 뒤집혀 있다.
- **보이는 형태**: 예외 없음. 결과를 `Integer.compare`로 다시 검사하면 역전 쌍이 나온다.
- **원인**: 뺄셈 비교자 `a - b`의 `int` 오버플로. TimSort가 위반을 우연히 만날 때만 예외가 나므로 대부분은 조용히 지나간다.
- **대처**: 표준 비교 메서드로 바꾸고, 정렬 결과의 단조성을 검증하는 테스트를 둔다.

### 3. 동점 순서가 흔들려 페이지가 겹치거나 빠진다 (⚠ 커리큘럼)

- **현상**: 무한 스크롤에서 같은 주문이 두 번 보이고, 어떤 주문은 안 보인다.
- **보이는 형태**: 페이지 간 id 중복(시뮬레이션에서 10페이지 동안 중복 55건·누락 55건). 같은 쿼리를 다시 돌리면 다른 결과.
- **원인**: 정렬 키(`created_at`)에 동점이 많은데 동점 해소 키가 없다. DB는 동점 행의 순서를 보장하지 않고, 불안정 정렬·병렬 스캔·다른 실행 계획으로 순서가 바뀐다.
- **대처**: `ORDER BY created_at, id`처럼 유일 키를 마지막에 붙인다. 그래도 `OFFSET`은 페이지 사이에 앞쪽에 새 행이 끼면 겹칠 수 있다. 오프셋 대신 키셋 페이지네이션(오름차순이면 `WHERE (created_at, id) > (?, ?)`, `ORDER BY created_at DESC, id DESC`이면 `<`)을 쓴다 → [api-design/06-pagination](../../api-design/06-pagination/2-summary.md).

### 4. `TreeSet`·`TreeMap`에서 원소가 사라진다

- **현상**: 이름순 `TreeSet`에 사용자 3명을 넣었는데 2명만 남았다.
- **보이는 형태**:

(실험, 같은 환경, `java TreeDrop.java`)

```text
name만:      2 [User[id=1, name=kim], User[id=2, name=lee]]
name, id:    3 [User[id=1, name=kim], User[id=3, name=kim], User[id=2, name=lee]]
```

- **원인**: 정렬 컬렉션은 `compare == 0`이면 같은 원소로 보고 두 번째를 버린다. 비교자가 `equals`와 일관되지 않다(Comparator Javadoc의 "inconsistent with equals" 경고).
- **대처**: 정렬 컬렉션의 비교자에는 유일 키까지 넣는다. 정렬만 필요하면 `List` + `sort`를 쓴다.

### 5. 객체 배열 정렬이 예상보다 느리고 메모리를 먹는다

- **현상**: 수백만 건 정렬이 배치 시간의 대부분을 차지하고 GC가 잦다.
- **보이는 형태**: (예시) 프로파일에 `ComparableTimSort`·`TimSort`의 병합 메서드와 `compareTo`·비교자 람다가 상위. 실험에서 `Integer[]`가 `int[]`보다 3.2~4.9배 느렸다.
- **원인**: 박싱된 원소, 참조 추적, TimSort의 임시 배열(최악 n/2 참조 — `TimSort.java` 머리 주석).
- **대처**: 키를 원시 배열로 뽑아 정렬하거나(인덱스 배열 + 원시 키), DB의 `ORDER BY`·인덱스로 정렬을 옮긴다.

## 핵심 문장

- 실무 정렬의 버그는 알고리즘이 아니라 비교자 계약(대칭·추이·0의 일관성)에서 나온다.
- TimSort는 계약 위반을 우연히 만날 때만 `Comparison method violates its general contract!`를 던진다. 예외가 없다고 순서가 맞은 것은 아니다.
- Java 객체 정렬(`List.sort`·`Arrays.sort(Object[])`)은 안정한 TimSort, 원시 배열 정렬은 듀얼 피벗 퀵 정렬이다(OpenJDK 21).
- 안정 정렬은 "입력 순서"를 지킬 뿐이다. 결정적인 순서가 필요하면 마지막에 유일 키를 붙인다.
- `TreeSet`·`TreeMap`은 `compare == 0`을 같은 원소로 본다. 비교자가 곧 동등성이다.

## 관련 주제·근거

- 선행
  - [algorithm/02-merge-sort](../02-merge-sort/2-summary.md) — 병합과 안정성의 원리(커리큘럼 선행 06)
  - [math 03-sets-relations-orders](../../math/03-sets-relations-orders/2-summary.md) — 부분·전순서
- 후속·연결
  - [algorithm/05-non-comparison-sort](../05-non-comparison-sort/2-summary.md) — LSD 기수 정렬도 안정성에 기댄다(커리큘럼 10)
  - [algorithm/11-external-sort-and-k-way-merge](../11-external-sort-and-k-way-merge/2-summary.md) — 메모리보다 큰 정렬
  - [api-design/06-pagination](../../api-design/06-pagination/2-summary.md), [api-design/12-filtering-sorting-search](../../api-design/12-filtering-sorting-search/2-summary.md)
  - [database/10-collation-and-text-comparison](../../database/10-collation-and-text-comparison/2-summary.md) — 문자열 비교자의 로캘 의존
  - [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md) — DB 정렬 연산
  - [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) — 정렬 시간 측정의 함정
- 소스·문서
  - OpenJDK 21(jdk21u) `src/java.base/share/classes/java/util/TimSort.java`(`MIN_MERGE = 32`, `MIN_GALLOP = 7`, `mergeCollapse`, 계약 위반 예외), `ComparableTimSort.java`, `Arrays.java`(`sort(int[])` → `DualPivotQuicksort`, `LegacyMergeSort`), `DualPivotQuicksort.java`, `ArrayList.java`(`sort`), `List.java`, `Collections.java`, `Comparator.java`(계약 3조건) <https://github.com/openjdk/jdk21u>
  - Tim Peters, `listsort.txt`(CPython `Objects/listsort.txt` — 안정·적응형 자연 병합 정렬, MIN_GALLOP 7, powersort) <https://github.com/python/cpython/blob/main/Objects/listsort.txt>
  - de Gouw, Rot, de Boer, Bubel, Hähnle, "OpenJDK's Java.utils.Collection.sort() Is Broken: The Good, the Bad and the Worst Case", CAV 2015 <https://link.springer.com/chapter/10.1007/978-3-319-21690-4_16>
  - JDK-8203864 "Execution error in Java's Timsort"(JDK 11 해결) <https://bugs.openjdk.org/browse/JDK-8203864>
  - JDK-8072909 "TimSort fails with ArrayIndexOutOfBoundsException on worst case long arrays"(JDK 9) <https://bugs.openjdk.org/browse/JDK-8072909>
  - CPython bpo-34561 powersort 전환(3.11) <https://bugs.python.org/issue34561>
  - V8 블로그 "Getting things sorted in V8"(2018), "Stable Array.prototype.sort"(2019) <https://v8.dev/features/stable-sort>
  - PostgreSQL 17 문서 7.6 LIMIT and OFFSET <https://www.postgresql.org/docs/17/queries-limit.html>
  - CLRS 3판 2.1(삽입 정렬), 2.3(병합 정렬), 7장(퀵 정렬), 8.3(기수 정렬과 안정성)
- 실험 목록(모두 2026-10-05, OpenJDK 21.0.12 Temurin, docker `--cpus=2`)
  - 계약 위반 비교자 3종의 예외 빈도, `useLegacyMergeSort` 비교(`Contract.java`)
  - 예외 없이 틀린 순서, 크기 31·32·64·2000별 예외 빈도(`Contract2.java`)
  - 입력 모양별 비교 횟수(`Adaptive.java`)
  - 안정 정렬 두 번 vs 불안정 정렬, 페이지네이션 중복 시뮬레이션(`Stable.java`)
  - `int[]` vs `Integer[]` 정렬 시간(`Prim.java`, 반복 5회)
  - `TreeSet` 원소 소실(`TreeDrop.java`)
