# testing/05-tdd — 테스트 목록 → 하나씩 → 통과 → 리팩터링 — 정리 (힌트)

## 해결하는 문제

코드를 다 짜고 나서 테스트를 쓰면 세 가지가 자주 생긴다.

```text
  구현 먼저                                    결과
  ─────────────────────────────────────────────────────────────
  기능을 한 번에 크게 짠다          →  어디서 틀렸는지 찾는 시간이 길다
  다 짠 뒤 "돌아가는 것"을 확인한다  →  테스트가 코드 모양을 따라간다(빠진 경우는 그대로 빠짐)
  기대값을 실행 결과에서 베낀다      →  버그가 정답으로 굳는다
```

- TDD(Test-Driven Development)는 순서를 뒤집는다. **먼저 실패하는 테스트 하나**, 그다음 그걸 통과시키는 코드, 그다음 정리.
  - *빨강(red)*: 새 테스트가 실패하는 상태. 테스트가 실제로 무언가를 검사한다는 증거다.
  - *초록(green)*: 새 테스트와 이전 테스트가 모두 통과하는 상태.
  - *리팩터링(refactoring)*: 동작을 바꾸지 않고 구조를 고치는 일. 초록일 때만 한다.

쉬운 예: 장보기 목록을 들고 장을 본다.
- 목록에서 하나를 집고, 바구니에 넣고, 목록에 줄을 긋는다.
- 가게를 돌다 새로 떠오른 것은 목록에 적어 두고, 지금 집던 것부터 마친다.

똑같은 구조다.\
테스트 목록이 장보기 목록이고, "줄 긋기"가 초록이다. 한 번에 한 항목만 다루니 실패하면 원인이 방금 한 일 안에 있다.

실무 예:
- 금액 계산(할인·반올림)처럼 경우가 많은 규칙을, 경우 하나씩 테스트로 고정하며 짠다.
- 버그 보고를 받으면 먼저 그 버그를 재현하는 실패 테스트를 쓰고 고친다.
- 레거시에는 TDD 전에 특성 테스트로 현재 동작부터 고정한다(17번 노트).

## 동작·원리

### 1. Canon TDD — 다섯 단계

Kent Beck, "Canon TDD"(2023-12-11)의 원문 단계다.

```text
   ┌─▶ 1. 테스트 목록 작성 ("a list of the test scenarios you want to cover")
   │       │
   │       ▼
   │   2. 목록에서 정확히 하나를 실행 가능한 테스트로 → 빨강
   │       │
   │       ▼
   │   3. 코드를 고쳐 이 테스트와 이전 테스트 전부 통과 → 초록
   │       │
   │       ▼
   │   4. (선택) 구현 설계를 다듬는 리팩터링 → 계속 초록
   │       │
   └───5. 목록이 빌 때까지 2로
```

1. "Write a list of the test scenarios you want to cover"
2. "Turn exactly one item on the list into an actual, concrete, runnable test"
3. "Change the code to make the test (& all previous tests) pass (adding items to the list as you discover them)"
4. "Optionally refactor to improve the implementation design"
5. "Until the list is empty, go back to #2"

- 목록은 고정이 아니다. 작업 중 새 경우가 떠오르면 목록에 추가한다.
- Beck은 설계 결정을 둘로 나눈다.
  - *인터페이스 설계*: "How a particular piece of behavior is invoked" — 테스트를 쓰는 2단계에서 정한다.
  - *구현 설계*: "How the system implements that behavior" — 3·4단계에서 정한다.
  - 그래서 1단계 목록에는 구현 결정을 섞지 말라고 한다("Mistake: mixing in implementation design decisions").

### 2. 초록으로 가는 세 전략

『TDD by Example』 28장 "Green Bar Patterns"의 세 전략이다(같은 장에 One to Many 패턴도 있다 — Pearson 견본 PDF 목차·색인 기준).

```text
   Fake It            Triangulate                 Obvious Implementation
   return 0;          예제 2개가 서로 다르면      답이 뻔하면 바로 쓴다
   (상수로 통과)  →   상수로는 둘 다 못 통과 →    sum += price * qty;
                      → 일반화가 강제된다
```

- *Fake It('Til You Make It)*: 일단 상수를 돌려줘 초록을 만든다. 다음 테스트가 일반화를 강요한다.
  - 이 Fake는 03번 노트의 테스트 더블 Fake와 다르다. 이쪽은 **제품 코드의 임시 구현**이다.
- *Triangulate*: 예제가 둘 이상일 때에야 추상화한다.
- *Obvious Implementation*: 구현이 분명하면 바로 쓴다. 예상하지 못한 빨강을 만나면 되돌아가 Fake It으로 걸음을 줄인다("As soon as I get unexpected red bar, I back up, shift to faking implementations" — 책 본문은 열지 못했고 독자 노트 <https://stanislaw.github.io/2016-01-25-notes-on-test-driven-development-by-example-by-kent-beck.html>의 인용으로 확인).

### 3. Canon TDD가 꼽은 실수

| 단계 | 실수(원문) |
|---|---|
| 테스트 쓰기 | "write tests without assertions just to get code coverage" |
| 테스트 쓰기 | "convert all the items on the Test List into concrete tests, then make them pass one at a time" |
| 통과시키기 | "delete assertions so the test pretends to pass" |
| 통과시키기 | "copying actual, computed values & pasting them into the expected values of the test" |
| 통과시키기 | "mixing refactoring into making the test pass" |
| 리팩터링 | "refactoring further than necessary for this session" |
| 리팩터링 | "abstracting too soon. Duplication is a hint, not a command" |

- 커리큘럼 ⚠의 두 장애(계산 결과 붙여 넣기, 리팩터링 생략)가 이 표의 넷째 줄과 4단계 생략이다.

### 실험: 사이클을 git 커밋으로 기록하기

문제: 장바구니 합계. 수량 × 단가의 합, 총 수량 10개 이상이면 10% 할인, 원 미만은 반올림(HALF_UP).\
각 단계마다 테스트를 돌리고 결과를 커밋 메시지에 남겼다. 기록을 보이려고 빨강도 커밋했다(Beck이 빨강 커밋을 권한 것은 아니다).

```text
(실험, maven:3.9-eclipse-temurin-21 이미지 — Maven 3.9.16 · JDK 21.0.11 · JUnit 5.13.4 · AssertJ 3.27.3, 2026-10-03)
$ git log --oneline --reverse master
0be3454 list: 테스트 목록 작성
a56e11e red: 빈 장바구니 합계는 0
ee3ad06 green: 빈 장바구니 — 상수 0 반환
0ff81a6 red: 한 품목 — 단가 x 수량
1734370 green: 한 품목 — 누적 합
1ed4dcf test: 여러 품목 — 처음부터 초록(새 코드 불필요)
6a03d3d red: 10개 이상 10% 할인
88bbe86 green: 10개 이상 10% 할인 — 정수 연산
83283c0 refactor: 품목 줄(Line)·할인 판정 추출 — 동작 보존
b05c707 red: 할인 결과 반올림 — 손으로 계산한 기대값 8105
9baac7e green: BigDecimal HALF_UP 반올림
ef00ec9 refactor: 할인율 상수 이름 붙이기
```

단계별 테스트 실행 결과(요약 줄과 실패 메시지만 추림):

| 커밋 | 결과 |
|---|---|
| red: 빈 장바구니 | `COMPILATION ERROR` — `CartTest.java:[6,24] cannot find symbol`(`Cart`가 아직 없다) |
| green: 상수 0 반환 | `Tests run: 1, Failures: 0` |
| red: 한 품목 | `expected: 3000L but was: 0L` — `Tests run: 2, Failures: 1` |
| green: 누적 합 | `Tests run: 2, Failures: 0` |
| test: 여러 품목 | `Tests run: 3, Failures: 0` — 처음부터 초록 |
| red: 10% 할인 | `expected: 9000L but was: 10000L` — `Tests run: 4, Failures: 1` |
| green: 정수 연산 | `Tests run: 4, Failures: 0` |
| refactor: 추출 | `Tests run: 4, Failures: 0` |
| red: 반올림 | `expected: 8105L but was: 8104L` — `Tests run: 5, Failures: 1` |
| green: HALF_UP | `Tests run: 5, Failures: 0` |
| refactor: 상수 | `Tests run: 5, Failures: 0` |

- 첫 빨강은 컴파일 오류였다. 아직 없는 클래스를 테스트가 먼저 부르기 때문이다. 이 순간이 인터페이스 설계(`new Cart()`, `total()`)다.
- "여러 품목"은 처음부터 초록이었다. 새 코드가 필요 없었다는 정보다. 목록 항목이 이미 일반화된 구현에 덮였다.
- 넷째(마지막) 빨강 `8105 vs 8104`: 정수 연산 `subtotal * 9 / 10`이 소수점을 버렸다. 이 버그를 잡은 것은 **손으로 계산한 기대값**이다.

마지막 구현:

```java
public long total() {
    long subtotal = lines.stream().mapToLong(Line::amount).sum();
    return isBulk() ? discounted(subtotal) : subtotal;
}
private boolean isBulk() { return lines.stream().mapToInt(Line::quantity).sum() >= BULK_THRESHOLD; }
private long discounted(long subtotal) {
    return BigDecimal.valueOf(subtotal).multiply(BULK_RATE)
        .setScale(0, RoundingMode.HALF_UP).longValueExact();
}
```

### 실험: 계산 결과를 기대값에 붙여 넣으면

같은 지점(`83283c0`, 정수 연산 버그가 있는 상태)에서 갈래를 만들었다. 이번에는 기대값을 손으로 계산하지 않고, 먼저 실행해 출력을 본 뒤 그 값을 붙여 넣었다.

```java
@Test void discountedTotalRoundsHalfUp() {
    Cart cart = new Cart();
    cart.add(1_000, 9);
    cart.add(5, 1);                            // 9,005원, 10개 → 8,104.5원
    assertThat(cart.total()).isEqualTo(8_104);   // 위 출력을 붙여 넣음
}
```

```text
(실험, 같은 환경)
### (반례) 실행해서 실제 값 보기
ACTUAL=8104
### anti: 계산 결과 8104를 기대값에 붙여 넣기 — 초록, 버그 고정
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

이 갈래의 테스트를 둔 채 구현만 올바른 판(HALF_UP)으로 바꿨다.

```text
(실험, 같은 환경 — 붙여 넣은 테스트 + 고친 구현)
expected: 8104L
 but was: 8105L
```

- 관찰: 붙여 넣은 테스트는 버그가 있을 때 초록이고, **버그를 고치면 빨강**이다. 테스트가 버그를 지키는 쪽에 섰다.
- 해석: 기대값은 구현과 **독립된 근거**(손 계산·명세·다른 계산 경로)에서 와야 한다. Beck의 *Evident Data* 패턴도 기대값과 입력의 관계가 테스트 안에서 보이게 쓰라고 한다(예: `9_005 × 0.9 = 8_104.5 → 8_105`).
- 출력 전체를 사람이 검토해 승인하는 골든 마스터(특성 테스트)는 다른 도구다. 그건 "현재 동작을 고정"하는 것이 목적이고, 레거시 안전망으로 쓴다(17번 노트).

## 쓰이는 자료구조·알고리즘

- **테스트 목록 = 작업 큐**: 항목을 하나 꺼내 처리하고, 처리 중 발견한 항목은 뒤에 넣는다. 목록이 비면 끝.
- **삼각측량 = 예제에서 일반화**: 상수 구현은 예제 하나만 만족한다. 서로 다른 예제가 둘 이상이면 상수로는 모두 만족할 수 없어 일반 규칙이 강제된다.
- **회귀 묶음은 대체로 늘어난다**: 초록이 된 테스트는 기본적으로 남아 회귀 묶음이 된다. 3단계 "& all previous tests pass"가 이전 결정을 지키는 장치다.
  - 다만 Canon TDD 3단계는 "이전 테스트를 통과시키라"는 말이지 "지우지 말라"는 규칙이 아니다. 『TDD by Example』 32장 "Mastering TDD"(193쪽~)는 색인에 "deleting tests, 198" 항목을 두어 테스트 삭제를 따로 다룬다(Pearson 견본 PDF의 목차·색인으로만 확인, 198쪽 본문의 판단 기준은 확인 못 함 [?]). 겹치는 테스트를 지울지는 그 기준에 따라 판단할 문제다.
- **금액 반올림**: `BigDecimal` + `RoundingMode.HALF_UP`, 결과를 정수로 바꿀 때 `longValueExact()`. 반올림 규칙 자체는 domain-modeling [14-money-arithmetic-rounding-allocation](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 한 사이클의 실무 순서

1. 기능 요구를 시나리오 목록으로 적는다. 정상·경계·오류를 함께 적는다. 구현 방식은 적지 않는다.
2. 가장 단순하고 배울 것이 있는 항목 하나를 고른다.
3. 테스트를 쓴다. 기대값은 손 계산이나 명세에서 가져온다. 실행해 **빨강을 눈으로 확인한다.**
   - 빨강을 보지 못한 테스트는 실패할 수 있는지 모르는 테스트다.
4. 가장 작은 변경으로 초록을 만든다. 전체 테스트를 돌린다.
5. 초록에서 중복·이름·구조를 고친다. 테스트는 계속 초록이어야 한다. 커밋한다.
6. 작업 중 떠오른 경우는 목록에 적고 다음 사이클로 미룬다.

### 2. 버그 수정에도 같은 순서

```java
// 1) 버그를 재현하는 테스트 — 지금은 빨강이어야 한다
@Test void elevenItemsOfFiveWonRoundsHalfUp() {
    Cart cart = new Cart();
    cart.add(5, 11);                          // 55원 × 0.9 = 49.5원 → 50원 (예시)
    assertThat(cart.total()).isEqualTo(50);   // 정수 연산 구현이면 49로 빨강
}
// 2) 고친다 → 초록 → 3) 이 테스트는 회귀 테스트로 남는다
```

### 3. 진단 — 기록에서 TDD가 지켜졌는지 보기

```bash
# 테스트와 구현이 같은 커밋에서 함께 바뀌었는지, 리팩터링 커밋이 있는지 훑는다
git log --oneline --stat -- src/test src/main | head -60
# 기대값 리터럴이 실행 결과 출력과 똑같이 생겼는지(붙여 넣기 의심) 찾는 출발점
grep -rnE 'isEqualTo\([0-9_]{4,}\)' src/test/java | head
```

- 점검 질문
  - 이 기대값은 어디서 왔나? 손 계산·명세·독립 계산 중 하나를 말할 수 있어야 한다.
  - 이 테스트가 빨강인 것을 본 적이 있나?
  - 최근 N 사이클에 리팩터링 커밋이 하나도 없나? 중복·긴 메서드가 쌓이고 있지 않나?

## 장애 시나리오와 대처

### 1. 기대값에 계산 결과를 붙여 넣기 → 버그를 정답으로 고정 (⚠ 커리큘럼)

- 현상: 운영에서 할인 금액이 1원씩 모자라다는 문의. 테스트는 전부 초록이다.
- 보이는 형태: 테스트의 기대값 `8_104`가 실제 구현의 출력과 정확히 같다. 고치는 PR을 올리면 그 테스트가 `expected: 8104L but was: 8105L`로 빨강이 된다(실험).
- 원인: 기대값을 구현을 실행한 출력에서 베꼈다. 테스트가 구현을 검사하지 않고 구현을 복사했다.
- 대처
  - 기대값을 명세·손 계산으로 다시 정한다. 계산 근거를 테스트 안 주석이나 식으로 남긴다(Evident Data).
  - 리뷰에서 "이 숫자는 어디서 왔나"를 묻는다.

### 2. 리팩터링 단계 생략 (⚠ 커리큘럼)

- 현상: 기능은 계속 늘지만 한 메서드에 `if`가 쌓이고, 새 테스트 하나를 통과시키는 데 드는 시간이 점점 길어진다.
- 보이는 형태: 커밋 기록에 red·green만 있고 refactor가 없다. 같은 계산이 여러 곳에 복사돼 있다.
- 원인: 초록이 되면 바로 다음 항목으로 넘어갔다. 4단계는 "Optionally"지만, 생략이 계속되면 구현 설계를 다듬을 기회가 사라진다.
- 대처
  - 초록마다 "중복·이름·구조 중 고칠 것이 있나"를 묻는다. 있으면 그 사이클에서 고친다.
  - 반대 방향 실수도 있다. Beck은 "refactoring further than necessary for this session", "abstracting too soon"도 실수로 꼽는다. 중복은 신호이지 명령이 아니다.

### 3. 목록 전체를 먼저 테스트로 바꿈

- 현상: 테스트 20개를 먼저 쓰고 구현을 시작했다. 빨강 20개 중 무엇부터 고칠지 모르고, 첫 구현에서 인터페이스가 바뀌어 테스트 20개를 다 고친다.
- 원인: Canon TDD의 "convert all the items on the Test List into concrete tests, then make them pass one at a time" 실수다.
- 대처: 목록은 글로 두고, 테스트는 한 번에 하나만 쓴다.

### 4. 단언 없는 테스트·단언 삭제

- 현상: 커버리지는 높은데 버그가 그대로 운영에 나간다.
- 보이는 형태: `@Test` 메서드가 SUT를 부르기만 하고 `assert`가 없다. 또는 실패하던 단언이 커밋에서 지워졌다.
- 원인: 커버리지 수치나 초록 자체를 목표로 삼았다.
- 대처: 리뷰에서 단언 없는 테스트를 거른다. 테스트의 판별력은 변이 테스트로 잰다(15번 노트).

### 5. 빨강이 오래 지속됨

- 현상: 테스트 하나를 통과시키려고 한 시간째 고치고 있다. 그 사이 다른 테스트도 깨졌다.
- 원인: 한 걸음이 너무 크다. 또는 통과시키는 중에 리팩터링을 섞었다("mixing refactoring into making the test pass").
- 대처: 변경을 되돌려 마지막 초록으로 간다. 더 작은 테스트(또는 Fake It)로 다시 시작한다.

## 핵심 문장

- Canon TDD는 다섯 단계다: 목록 → 정확히 하나를 테스트로 → 이것과 이전 테스트 통과 → (선택) 리팩터링 → 목록이 빌 때까지 반복.
- 테스트를 쓰는 순간이 인터페이스 설계이고, 통과·리팩터링이 구현 설계다.
- 빨강을 직접 봐야 그 테스트가 실패할 수 있다는 것을 안다.
- 기대값은 구현과 독립된 근거에서 와야 한다. 실험에서 출력을 붙여 넣은 테스트는 버그일 때 초록, 고치면 빨강이었다.
- 리팩터링은 초록일 때만, 이번 사이클에 필요한 만큼만 한다.

## 관련 주제·근거

- 선행
  - [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 좋은 테스트의 조건, AAA
- 후속·연결
  - [03-test-doubles](../03-test-doubles/2-summary.md) — 테스트 더블 Fake(이 노트의 Fake It과 다른 말)
  - [06-outside-in-tdd-and-acceptance-tests](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) — 인수 테스트를 바깥 루프로 둔 이중 루프 TDD
  - [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — 테스트 목록에 넣을 경계값·동치 분할
  - [15-mutation-testing](../15-mutation-testing/2-summary.md) — 단언 없는 테스트를 잡는 법
  - [17-characterization-tests-legacy](../17-characterization-tests-legacy/2-summary.md) — 현재 동작을 고정하는 골든 마스터
  - software-design [13-refactoring](../../software-design/13-refactoring/2-summary.md) — 동작 보존 변경
  - software-design [12-simple-design-and-yagni](../../software-design/12-simple-design-and-yagni/2-summary.md) — 지금 필요한 만큼만
  - software-design [14-tidy-first](../../software-design/14-tidy-first/2-summary.md) — 구조 변경과 동작 변경을 나누기
  - domain-modeling [14-money-arithmetic-rounding-allocation](../../domain-modeling/14-money-arithmetic-rounding-allocation/2-summary.md) — 금액 반올림
- 문헌
  - Kent Beck, "Canon TDD"(2023-12-11) — 다섯 단계, 인터페이스/구현 설계, 단계별 실수 목록 <https://newsletter.kentbeck.com/p/canon-tdd> (옛 주소 tidyfirst.substack.com에서 넘어감)
  - Kent Beck, 『Test-Driven Development: By Example』(Addison-Wesley 2003) — 28장 "Green Bar Patterns"(Fake It, Triangulate, Obvious Implementation, One to Many — 151~156쪽), 25장 "Test-Driven Development Patterns"(Test List 126~127쪽, Evident Data 130~131쪽), 32장 "Mastering TDD"(색인 "deleting tests, 198") — 목차·색인은 Pearson 견본 PDF <https://ptgmedia.pearsoncmg.com/images/9780321146533/samplepages/0321146530.pdf>
- 실험 목록(코드는 scratchpad `ts/03/tdd`, 별도 git 저장소)
  - `maven:3.9-eclipse-temurin-21` 이미지(Maven 3.9.16, JDK 21.0.11), `--cpus=2 -m 1g`, JUnit 5.13.4 · AssertJ 3.27.3
  - A: 테스트 목록 5항목을 사이클별 커밋 12개로 기록(`master`), 단계마다 `mvn test` 요약을 `steps.log`에 남김
  - B: `83283c0`에서 갈래 `paste-anti` — 실행 출력 8104를 기대값에 붙여 넣으면 초록, 고친 구현과 합치면 `expected: 8104L but was: 8105L`
