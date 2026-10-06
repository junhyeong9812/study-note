# testing/07-test-design-techniques — 테스트 설계 기법: 동치 분할·경계값·결정 테이블·상태 전이·쌍 조합 — 정리 (힌트)

## 해결하는 문제

입력을 전부 넣어 볼 수는 없다. 그렇다고 손에 잡히는 값 몇 개만 넣으면 결함이 숨는 자리를 비켜 간다.

```text
  int 인자 하나        → 2^32 ≈ 43억 개 값
  인자 5개(3·3·3·4·2값) → 216 조합
  상태 5개 × 이벤트 4개 → 20칸(허용 5칸 + 금지 15칸)

  "아무 값이나 몇 개"를 넣으면?
  ────┬──────────┬──────────┬──────────────┬────
      1        2000|2001    5000|5001      30000
              ↑ 결함은 여기(경계)에 몰리는데, 무작위 값은 거의 안 떨어진다
```

- 해법: 입력 공간을 **"같게 처리될 묶음"** 으로 나누고, 묶음마다 대표값과 경계값을 고른다. 조건 조합은 표로, 상태는 그래프로 펼쳐 빠진 칸을 찾는다.
  - *테스트 설계 기법*: 무엇을 테스트할지(테스트 조건)와 어떤 입력으로 할지(테스트 케이스)를 체계적으로 고르는 방법. ISTQB CTFL 4.0은 명세를 보고 고르는 블랙박스 기법으로 동치 분할·경계값 분석·결정 테이블·상태 전이 네 가지를 다룬다(4.2절).

쉬운 예: 놀이공원 요금이 "만 3세 미만 무료, 3~12세 어린이, 13세 이상 성인"이다.
- 나이 8, 30만 넣어 보면 통과한다. 그런데 코드가 `age < 12`로 짜여 12세를 성인으로 받는 결함은 못 본다.
- 2, 3, 12, 13을 넣으면 바로 보인다.

똑같은 구조다.\
쇼핑몰 배송비가 무게 구간으로 갈린다. 쿠폰은 "5만 원 **이상**"이다. 주문 상태는 "결제 후에만 배송"이다. 전부 구간·조건·상태로 나뉘고, 결함은 그 경계와 금지된 칸에 모인다.

실무 예:
- 쿠폰 조건 `amount > 50000`을 `>=`로 써야 했는데 반대로 썼다. 정확히 5만 원짜리 주문만 쿠폰이 안 먹는다.
- 페이지네이션에서 마지막 페이지가 정확히 꽉 찬 경우(총 100건, 페이지 크기 20)에 빈 6페이지가 생긴다.
- "배송 시작 후 취소 불가" 규칙이 구현에서 빠져 이미 출고된 주문이 취소·환불된다.

## 동작·원리

### 1. 동치 분할 — "같게 처리될 묶음"마다 하나

```text
  명세: 무게 w(g)  1..2000 → 3000원 · 2001..5000 → 4000원 · 5001..30000 → 6000원 · 그 밖 → 거부

   무효        유효 P1        유효 P2         유효 P3            무효
  ───────┼──────────────┼──────────────┼─────────────────┼───────
   ..0   1          2000 2001      5000 5001          30000 30001..
   -500       1000            3500             10000         40000   ← 묶음마다 대표 1개 = 5개
```

- *동치 분할(EP, Equivalence Partitioning)*: 테스트 대상이 같은 방식으로 처리할 것으로 기대되는 값끼리 묶어(분할), 분할마다 하나씩 테스트한다(ISTQB CTFL 4.0 4.2.1).
  - 근거가 되는 가정: 한 값이 결함을 드러내면 같은 분할의 다른 값도 드러낼 것이다. 그래서 분할당 하나로 충분하다고 본다.
- *유효 분할 / 무효 분할*: 처리해야 하는 값의 묶음 / 거부·무시해야 하는 값의 묶음. **무효 분할도 커버리지 항목이다.** 위 그림에서 분할은 5개, EP 100%는 5개 전부를 한 번씩 밟는 것이다.
- 분할은 서로 겹치지 않고, 빈 집합이 아니어야 한다(4.2.1).
- 인자가 여럿이면 분할 집합도 여럿이다. 각 집합의 분할을 한 번씩만 밟는 기준을 *Each Choice 커버리지* 라고 한다. 조합은 보지 않는다.

### 2. 경계값 분석 — 결함이 모이는 자리

```text
  2값 BVA: 경계값 + 옆 분할의 가장 가까운 값
       0 | 1        2000 | 2001      5000 | 5001      30000 | 30001
       ^   ^           ^    ^           ^    ^            ^     ^       → 8개

  3값 BVA: 경계값 + 양쪽 이웃
     0 1 2   1999 2000 2001   ...                                       → 더 많다
```

- *경계값 분석(BVA, Boundary Value Analysis)*: 순서가 있는 분할의 최솟값·최댓값(경계값)을 시험한다. 개발자가 경계에서 실수하기 쉽기 때문이다(4.2.2).
  - 잡는 결함: 구현된 경계가 의도보다 한 칸 위·아래로 밀렸거나 아예 빠진 것.
  - *off-by-one*: 경계를 한 칸 어긋나게 구현한 결함(`<=` 대신 `<`, `length` 대신 `length - 1` 등).
- 2값과 3값의 차이(4.2.2의 예): `if (x <= 10)`을 `if (x == 10)`으로 잘못 짰다면, 2값 BVA의 x=10, 11로는 못 잡는다. 3값 BVA가 추가하는 x=9가 잡는다.
- BVA는 **순서가 있는 분할에만** 쓴다. 결제 수단(카드·계좌·포인트)처럼 순서가 없는 값에는 경계가 없다.

### 실험: 경계값 vs 동치 분할 vs 무작위 — 경계 결함 4개

경계를 하나씩 어긋나게 만든 구현 4개를 같은 세 묶음의 테스트 입력에 돌렸다.

```java
// scratchpad/ts/07/a/TechniquesExp.java 발췌
int[] ep  = {-500, 1000, 3500, 10000, 40000};               // 동치 분할: 분할마다 1개
int[] bva = {0, 1, 2000, 2001, 5000, 5001, 30000, 30001};   // 2값 경계값
// 무작위: [-1000, 40000]에서 균등하게 8개 × 10000번 (시드 42)
BUGGY.put("B1 w<=2000 -> w<2000",   w -> ... (w < 2000 ? 3000 : ...));
BUGGY.put("B2 w<=5000 -> w<=5001",  ...);
BUGGY.put("B3 w<1 -> w<0",          ...);
BUGGY.put("B4 w>30000 -> w>=30000", ...);
```

(실험, JDK 21.0.12 eclipse-temurin:21-jdk · `java TechniquesExp.java`, 2026-10-03)

```text
== 1. 경계 결함 검출: 동치 분할(5개) / 경계값(8개) / 무작위 8개 (10000회 반복, 시드 42) ==
B1 w<=2000 -> w<2000     EP=false BVA=true  random=0.00%
B2 w<=5000 -> w<=5001    EP=false BVA=true  random=0.01%
B3 w<1 -> w<0            EP=false BVA=true  random=0.02%
B4 w>30000 -> w>=30000   EP=false BVA=true  random=0.04%
```

- 관찰: 경계값 8개가 4개 결함을 전부 잡았다. 분할 대표값 5개는 하나도 못 잡았다. 무작위 8개는 1만 번 중 0~4번 잡았다.
- 해석: 결함 하나는 값 41,001개 중 정확히 한 점(예: 2000)에서만 드러난다. 무작위 값 8개가 그 점에 떨어질 확률은 약 8/41001 ≈ 0.02%다. 측정값(0.00~0.04%)이 이 크기와 맞다.
- 그렇다고 EP가 쓸모없지는 않다. EP는 "분할이 몇 개인가"를 정해 주고, BVA는 그 분할의 끝을 찌른다. 둘은 함께 쓴다.

### 3. 결정 테이블 — 조건 조합을 빠짐없이

```text
  규칙: VIP이고 10만 원 이상 → 10% 할인 / 아니면 5만 원 이상 → 5% 할인 / 그 밖 → 할인 없음

                      R1   R2   R3   R4   R5   R6
  C1 VIP              T    T    T    F    F    F
  C2 금액 >= 10만      T    F    F    T    F    F
  C3 금액 >= 5만       T    T    F    T    T    F
  ──────────────────────────────────────────────
  A1 10% 할인          X
  A2 5% 할인                X         X    X
  A3 할인 없음                    X              X

  (C2=T, C3=F 조합은 불가능 → 열에서 뺐다: 2^3 = 8 → 6)
```

- *결정 테이블*: 조건(행)과 동작(행), 그리고 조건의 한 조합 = 한 열(규칙)로 업무 규칙을 적은 표. 커버리지 항목은 **실현 가능한 열**이다(4.2.3).
  - "–"는 결과에 무관한 조건, "N/A"는 불가능한 조합이다.
- 강점: 사람이 빠뜨리기 쉬운 조합(R4: VIP 아님 + 10만 원 이상)을 표가 강제로 드러낸다. 요구사항의 빈칸·모순도 이때 보인다.
- 약점: 조건 n개면 열이 최대 2^n개다. 조건이 많으면 열을 합치거나(최소화), 위험 기반으로 고른다(4.2.3).

### 4. 상태 전이 — 그래프와 상태표

```text
  상태 전이 그래프 (허용 전이 5개)

  CREATED ──pay──▶ PAID ──ship──▶ SHIPPED ──deliver──▶ DELIVERED
     │               │
     └──cancel──┐ ┌──cancel
                ▼ ▼
             CANCELLED

  상태표 (행 = 상태, 열 = 이벤트, 빈칸 = 금지 전이)
               pay      ship      deliver     cancel
  CREATED      PAID     ·         ·           CANCELLED
  PAID         ·        SHIPPED   ·           CANCELLED
  SHIPPED      ·        ·         DELIVERED   ·          ← 여기를 허용하는 버그
  DELIVERED    ·        ·         ·           ·
  CANCELLED    ·        ·         ·           ·
```

- *상태 전이 테스트*: 상태·이벤트·전이·동작으로 시스템을 모델링하고, 그 모델에서 테스트를 뽑는다(4.2.4).
- *상태표*: 상태 그래프와 같은 정보를 표로 쓴 것. 그래프와 달리 **금지 전이(빈칸)를 명시적으로 보여 준다.**
- 커버리지 기준 세 가지(4.2.4)
  - *모든 상태 커버리지*: 상태 5개를 한 번씩 거친다. 가장 약하다.
  - *유효 전이 커버리지(0-switch)*: 허용 전이 5개를 한 번씩 실행한다. 가장 널리 쓰인다.
  - *모든 전이 커버리지*: 허용 전이를 전부 실행하고, 금지 전이도 전부 시도한다(위 표 20칸). 한 테스트에서 금지 전이는 하나만 시도해 *결함 가림*(한 결함이 다른 결함 검출을 막는 것)을 피한다. 임무·안전 핵심 소프트웨어의 최소 요구로 권한다.

### 실험: 금지 전이 칸을 시험해야 잡히는 버그

`Order.cancel()`이 SHIPPED에서도 취소를 허용하게 잘못 짰다. 상태표 20칸을 `@CsvSource`로 그대로 옮겨 돌렸다.

```java
// scratchpad/ts/07/b/src/test/java/exp/OrderTransitionTest.java 발췌
@ParameterizedTest(name = "{0} --{1}--> {2}")
@CsvSource({
    "CREATED,pay,PAID", "CREATED,ship,REJECT", "CREATED,deliver,REJECT", "CREATED,cancel,CANCELLED",
    "PAID,pay,REJECT",  "PAID,ship,SHIPPED",   "PAID,deliver,REJECT",    "PAID,cancel,CANCELLED",
    "SHIPPED,pay,REJECT", "SHIPPED,ship,REJECT", "SHIPPED,deliver,DELIVERED", "SHIPPED,cancel,REJECT",
    // DELIVERED·CANCELLED 행 8칸은 전부 REJECT
})
void table(State from, String ev, String to) {
    Order o = orderIn(from);
    if (to.equals("REJECT")) {
        assertThatThrownBy(() -> event(ev).accept(o)).isInstanceOf(IllegalStateException.class);
        assertThat(o.state()).isEqualTo(from);          // 거부 뒤 상태가 그대로인지도 본다
    } else {
        event(ev).accept(o);
        assertThat(o.state()).isEqualTo(State.valueOf(to));
    }
}
```

(실험, maven:3.9-eclipse-temurin-21 · JUnit 5.13.4 · AssertJ 3.27.6 · surefire 3.5.3, 2026-10-03)

```text
[ERROR] Tests run: 20, Failures: 1, Errors: 0, Skipped: 0, ... <<< FAILURE! -- in exp.OrderTransitionTest
[ERROR] exp.OrderTransitionTest.table(State, String, String)[12] -- Time elapsed: 0.011 s <<< FAILURE!
Expecting code to raise a throwable.
```

- 12번째 행이 `SHIPPED,cancel,REJECT`다. 허용 전이 5개만 테스트하는 유효 전이 커버리지로는 이 버그를 못 잡는다 — 버그가 **금지 칸**에 있기 때문이다.
- 같은 실행에서 배송비 경계 테스트(`@CsvSource` 6행 + 범위 밖 2개)도 `2000g`에서 `expected: 3000 but was: 4000`으로 실패했다(구현이 `grams < 2000`).

### 5. 쌍 조합(pairwise) — 조합 폭발 줄이기

```text
  인자: 브라우저 3 × OS 3 × 언어 3 × 결제 수단 4 × 회원 여부 2 = 216 조합(전수)

  pairwise: "아무 두 인자의 아무 값 쌍"이 한 번 이상 나오면 된다
    (Safari, Bank) · (Android, Point) · (ja, Guest) ... 쌍 총 89개

    Chrome | Windows | ko | Card   | Member
    Chrome | macOS   | en | Bank   | Guest
    Safari | Windows | ja | Point  | Guest
    ...                                        → 13행으로 89쌍 전부
```

- *조합 테스트*: 여러 인자 값의 특정 조합에서만 나는 실패(*상호작용 실패*)를 노린다. ISTQB에서는 CTFL이 아니라 **Advanced Test Analyst(CTAL-TA) 4.0의 3.1.2절**이 다룬다.
  - *pairwise 커버리지*: 아무 두 인자에 대해, 그 두 인자 값의 쌍이 전부 한 번 이상 나오게 한다. 최소 개수의 테스트 집합을 찾는 것은 일반적으로 어렵다(CTAL-TA 3.1.2).
  - *base choice 커버리지*: 인자마다 기준값을 정해 기준 조합 하나를 만들고, 인자 하나씩만 다른 값으로 바꾼다.
- 근거로 드는 관찰(CTAL-TA 3.1.2가 인용한 Kuhn 외 2004): 실패의 약 97%가 조건 하나 또는 두 개의 상호작용으로 일어났다. 그래서 pairwise가 효과적이라고 본다.
  - 단, 97%는 원 논문 Table 1의 **의료기기 리콜 109건** 값이다. 같은 표에서 조건 1~2개로 일어난 실패 비율은 Mozilla 브라우저 76.1%, Apache 서버 70.3%, NASA 분산 DB 93.3%로 데이터셋마다 다르다(Kuhn·Wallace·Gallo, IEEE TSE 2004, NIST 프리프린트 <https://csrc.nist.gov/CSRC/media/Projects/automated-combinatorial-testing-for-software/documents/kuhn-wallace-gallo-tse-preprint.pdf>). 같은 표로 보면 조건 3개 이상이 필요한 실패, 곧 pairwise만으로는 보장되지 않는 몫이 데이터셋에 따라 약 3~30%다(100−97 … 100−70.3).

### 실험: 216 조합 vs pairwise

남은 쌍을 가장 많이 덮는 행을 216개 후보에서 하나씩 고르는 단순 탐욕법으로 만들었다.

(실험, JDK 21.0.12 · `java TechniquesExp.java`, 2026-10-03)

```text
== 2. pairwise(2-way) vs 전수 조합 ==
전수 조합 수 = 216
greedy pairwise 조합 수 = 13
모든 값 쌍 덮었나 = true, 쌍 총수 = 89
이론 하한(가장 큰 두 인자 값 수의 곱) = 12
3-way 값 조합 덮는 비율 = 124/261 (47.5%)
Safari+Bank 포함 = true
Safari+Android+Point 포함 = false
```

- 216 → 13행(약 6%). 하한 12(결제 4값 × 브라우저 3값 쌍은 각각 다른 행에 있어야 한다)에 가깝지만 최소라는 보장은 없다(탐욕법).
- 대가: 세 인자 값 조합은 47.5%만 덮었다. "Safari + Android + Point"에서만 나는 결함은 이 13행으로 못 잡는다. pairwise는 **두 인자 상호작용까지만** 보장한다.

## 쓰이는 자료구조·알고리즘

- **정렬된 경계 배열**: 동치 분할은 수직선을 경계값 배열로 자른 것이다. 구현 쪽에서는 `if` 사슬이나 경계 배열 + [이진 탐색](../../algorithm/06-binary-search/2-summary.md)으로 구간을 찾는다. 테스트는 그 배열의 원소와 원소±1을 찌른다.
- **진리표**: 결정 테이블은 조건 n개의 진리표(최대 2^n 열)에서 불가능한 열을 지우고, 결과가 같은 열을 합친 것이다.
- **방향 그래프·인접 행렬**: 상태 전이 그래프는 [그래프](../../data-structure/08-graph/2-summary.md)이고, 상태표는 (상태 × 이벤트) 인접 행렬이다. 빈칸 = 금지 전이.
  - 유효 전이 커버리지 = 간선 전부를 한 번씩 덮는 경로 집합. 0-switch는 길이 1 경로, 1-switch는 연속 전이 2개(길이 2 경로)다. 시작 상태에서 [DFS](../../algorithm/12-dfs/2-summary.md)·BFS로 각 상태에 가는 접두 경로를 만든다(위 실험의 `orderIn(state)`).
- **덮개 배열(covering array)과 탐욕법**: pairwise 집합은 강도 2의 덮개 배열이다. 위 실험은 "남은 쌍을 가장 많이 덮는 행"을 고르는 [탐욕법](../../algorithm/23-greedy/2-summary.md)(한 번에 한 행씩, 후보 216개 전부를 비교하는 단순판)으로 만들었다. 최소 크기를 보장하지 않는다.
- **파라미터 표(데이터 주도 테스트)**: 위 기법들의 결과는 결국 "입력·기대값 표"다. JUnit 5의 `@ParameterizedTest` + `@CsvSource`가 그 표를 그대로 실행한다.

## 적용 — 풀어나가는 법

### 순서

1. **입력·출력·상태·환경을 나열한다.** 함수 인자만이 아니라 설정값·시간·외부 응답·출력 값도 분할 대상이다(ISTQB 4.2.1은 출력·설정·시간 값도 든다).
2. **분할한다.** 유효 분할과 무효 분할을 따로 적는다. 빈 입력(빈 문자열·빈 목록·null 허용 여부)은 대개 자기만의 분할이다.
3. **순서 있는 분할이면 경계값을 뽑는다.** 최소·최대와 바로 바깥. 위험이 크면 3값 BVA.
   - 숫자 범위의 끝: 0, 1, 최댓값, `Integer.MAX_VALUE`, 컬렉션 크기 0·1·가득 참, 페이지 크기의 배수.
4. **조건이 둘 이상 얽히면 결정 테이블을 그린다.** 불가능한 열을 지우고, 열마다 테스트 하나.
5. **상태가 있으면 상태표를 그린다.** 허용 칸 전부 + 금지 칸 전부(최소한 위험한 금지 칸). 거부 뒤 상태가 그대로인지까지 단언한다.
6. **환경·설정 조합이 많으면 pairwise로 줄인다.** 이미 알려진 위험 조합은 손으로 더한다(CTAL-TA 3.1.2).
7. **표를 파라미터 테스트로 옮긴다.**

```java
// scratchpad/ts/07/b/src/test/java/exp/ShippingTest.java
@ParameterizedTest(name = "{0}g -> {1}")
@CsvSource({ "1,3000", "2000,3000", "2001,4000", "5000,4000", "5001,6000", "30000,6000" })
void boundaries(int grams, int expected) {
    assertThat(Shipping.fee(grams)).isEqualTo(expected);
}

@ParameterizedTest
@ValueSource(ints = { 0, 30001 })
void outside(int grams) {
    assertThatThrownBy(() -> Shipping.fee(grams)).isInstanceOf(IllegalArgumentException.class);
}
```

(실험, JUnit 5.13.4 · AssertJ 3.27.6, 2026-10-03 — 구현이 `grams < 2000`인 상태)

```text
[ERROR] Tests run: 8, Failures: 1, Errors: 0, Skipped: 0, ... <<< FAILURE! -- in exp.ShippingTest
[ERROR] exp.ShippingTest.boundaries(int, int)[2] -- Time elapsed: 0.028 s <<< FAILURE!
expected: 3000
 but was: 4000
```

- surefire 보고서의 `[2]`는 `@CsvSource`의 두 번째 행(`2000,3000`)이다. 표가 곧 진단표가 된다.

### 진단: 어떤 기법이 빠졌는지 보는 질문

| 운영에서 본 실패 | 빠진 기법 | 추가할 테스트 |
|---|---|---|
| 특정 금액·날짜·개수에서만 틀림 | 경계값 | 경계와 ±1 |
| "그 조합은 생각 못 했다" | 결정 테이블 | 빠진 열 |
| "그 상태에서 그게 되면 안 되는데" | 상태 전이(금지 칸) | 금지 전이 시도 + 상태 불변 단언 |
| 특정 브라우저+결제 수단에서만 | 조합(pairwise) | 그 쌍이 들어간 행 |
| 빈 목록·null·0에서 예외 | 동치 분할(빈 입력 분할 누락) | 빈 입력 분할 |

## 장애 시나리오와 대처

### 1. 경계값 누락 → off-by-one으로 정확히 그 값에서만 장애

- **현상**: 정확히 5만 원짜리 주문만 쿠폰이 적용되지 않는다는 문의가 들어온다. 4만 9천 원, 6만 원은 정상이다.
- **보이는 형태**: 에러·예외가 없다. 정산 대사에서 특정 금액대의 할인 누락 건수만 튄다.
- **원인**: `amount > 50_000`(명세는 "이상"). 테스트는 3만·7만 원 같은 구간 한가운데 값만 썼다.
- **대처**: 경계값(49,999 / 50,000 / 50,001)을 파라미터 표에 넣는다. 명세 문구("이상·초과·미만·이하")를 표의 행으로 그대로 옮긴다. 비슷한 비교 연산자를 [변이 테스트](../15-mutation-testing/2-summary.md)로 찔러 경계 테스트가 있는지 확인한다.

### 2. 빈 입력·최댓값 분할 누락 → 드문 입력에서 예외

- **현상**: 장바구니가 빈 상태로 결제 페이지에 들어오면 500 에러. 또는 페이지 크기의 배수만큼 결과가 있을 때 빈 마지막 페이지가 보인다.
- **보이는 형태**: `IndexOutOfBoundsException: Index 0 out of bounds for length 0`, `ArithmeticException: / by zero`(빈 목록 평균), 페이지 번호가 하나 더 찍힌 UI.
- **원인**: 크기 0·1·가득 참을 별도 분할로 보지 않았다. 총 페이지 수를 `total / size + 1`로 계산했다.
- **대처**: 컬렉션은 크기 0·1·여러 개·상한, 정수는 0·1·최댓값을 분할 목록의 기본 항목으로 둔다. 총 페이지 수 공식은 total = 0, 99, 100, 101로 시험한다.

### 3. 금지 전이 미검증 → 있어서는 안 되는 상태 변화

- **현상**: 이미 출고된 주문이 취소·환불되어 상품과 돈이 둘 다 나갔다.
- **보이는 형태**: 주문 이력에 `SHIPPED → CANCELLED`가 찍힌다. 예외는 없다.
- **원인**: 테스트가 허용 전이(행복 경로)만 다뤘다. 금지 칸은 아무도 시험하지 않았다(위 실험의 12번째 행).
- **대처**: 상태표 전체를 파라미터 테스트로 옮긴다. 금지 전이는 "예외 + 상태 그대로"를 함께 단언한다. 상태가 DB에 있으면 조건부 갱신(`UPDATE ... WHERE state = 'PAID'`)으로 DB에서도 막는다(→ [domain-modeling/11-state-machines-in-domain](../../domain-modeling/11-state-machines-in-domain/2-summary.md)).

### 4. 조합 폭발 → 전수를 포기하고 "대표 하나"만 테스트

- **현상**: 특정 브라우저 + 특정 결제 수단에서만 결제 버튼이 동작하지 않는다.
- **보이는 형태**: 오류 로그가 그 두 값을 가진 요청에만 몰린다.
- **원인**: 216 조합을 다 못 하니 "Chrome + 카드" 하나만 테스트했다(Each Choice조차 아님).
- **대처**: pairwise 집합(위 실험에서 13행)으로 두 인자 상호작용을 덮는다. 알려진 위험 조합은 손으로 추가한다. 세 인자 이상에서만 나는 결함은 pairwise로 보장되지 않는다는 점(위 실험의 3-way 47.5%)을 문서에 남긴다.

## 핵심 문장

- 입력을 다 넣을 수 없으니, "같게 처리될 묶음"으로 나눠 묶음마다 하나(동치 분할), 그리고 묶음의 끝(경계값)을 시험한다.
- 경계 결함은 값 한 점에서만 드러난다. 위 실험에서 경계값 8개는 경계 결함 4개를 전부 잡았고, 무작위 8개는 1만 번 중 0~4번 잡았다.
- 결정 테이블은 조건 조합을 강제로 펼쳐 빠진 조합과 명세의 빈칸을 드러낸다. 대가는 최대 2^n 열이다.
- 상태표는 금지 전이를 칸으로 보여 준다. 허용 전이만 시험하면 금지 칸의 버그를 못 잡는다.
- pairwise는 두 인자 상호작용을 적은 행(216 → 13)으로 덮지만, 세 인자 이상 조합은 보장하지 않는다.

## 관련 주제·근거

- 선행
  - testing [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 좋은 테스트의 기준
  - [math 02-induction-and-invariants](../../math/02-induction-and-invariants/2-summary.md) — 루프 불변식과 경계 조건
- 후속·연결
  - testing [14-property-based-testing](../14-property-based-testing/2-summary.md) — 사람이 고른 예제 대신 생성기로 입력을 뽑는다
  - testing [15-mutation-testing](../15-mutation-testing/2-summary.md) — 경계 변이(`<` → `<=`)가 살아남으면 경계 테스트가 빠진 것이다
  - testing [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md) — 화이트박스 쪽 기준(문장·분기 커버리지)
  - testing [17-characterization-tests-legacy](../17-characterization-tests-legacy/2-summary.md) — 레거시 출력 고정 때 입력 고르기
  - software-design [23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md) — 사전조건이 무효 분할을 정한다
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md) · [algorithm/23-greedy](../../algorithm/23-greedy/2-summary.md) · [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md)
- ISTQB
  - CTFL Syllabus v4.0.1 4장 — 4.2.1 동치 분할(유효·무효 분할, Each Choice), 4.2.2 경계값 분석(2값·3값, `x ≤ 10` vs `x = 10` 예), 4.2.3 결정 테이블(실현 가능한 열, 2^n 증가), 4.2.4 상태 전이(모든 상태·유효 전이(0-switch)·모든 전이, 결함 가림) <https://astqb.org/assets/documents/ISTQB_CTFL_Syllabus_v4.0.1.pdf>
  - CTAL-TA Syllabus v4.0 3.1.2 Combinatorial Testing — base choice·pairwise, 최소 집합 찾기 어려움, Kuhn 외 2004 인용(약 97%가 1~2개 조건) <https://astqb.org/assets/documents/ISTQB-CTAL-TA-Syllabus-v4.0-EN-4.pdf>
- JUnit 5 User Guide — Parameterized Tests(`@CsvSource`·`@ValueSource`) <https://junit.org/junit5/docs/current/user-guide/#writing-tests-parameterized-tests>
- 실험 목록(2026-10-03, 코드는 scratchpad/ts/07/)
  - `a/TechniquesExp.java` — eclipse-temurin:21-jdk(JDK 21.0.12) `java TechniquesExp.java`: 경계 결함 4개에 대한 EP·BVA·무작위(1만 회, 시드 42) 검출, 5인자 216 조합 vs 탐욕 pairwise 13행, 3-way 덮는 비율
  - `b/` maven 프로젝트 — maven:3.9-eclipse-temurin-21, JUnit 5.13.4·AssertJ 3.27.6·surefire 3.5.3 `mvn test`: 배송비 경계 파라미터 테스트 실패 출력, 주문 상태표 20칸 테스트의 금지 칸(SHIPPED·cancel) 실패 출력
  - 사실 점검 재실행(같은 환경, `--network none`) — `a/` 출력 전체(시드 42 결정적)와 `b/`의 실패 행·메시지(`[2]` 3000/4000, `[12]` Expecting code to raise a throwable.) 일치. 경과 시간(`Time elapsed`)만 실행마다 다르다
