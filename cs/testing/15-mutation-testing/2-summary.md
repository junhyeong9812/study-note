# testing/15-mutation-testing — 변이 테스트: 결함을 심어 테스트의 판별력을 잰다 — 정리 (힌트)

## 해결하는 문제

커버리지는 "코드가 실행됐나"만 잰다. 테스트가 **틀린 결과를 알아채는지**는 재지 않는다.

```text
  같은 코드, 같은 커버리지(라인 4/4 · 분기 8/8), 다른 테스트

  NoAssertTest   discountedPrice(150_000, true);   ← 호출만 하고 결과를 안 본다
                 discountedPrice(90_000, true); ...
  StrongTest     assertThat(discountedPrice(100_000, true)).isEqualTo(90_000); ...

  코드에 일부러 결함을 심어 보면?
  NoAssertTest   14개 중 1개 잡음 (7%)
  StrongTest     14개 중 14개 잡음 (100%)
```

- 해법: 코드를 조금씩 바꾼 사본(*변이체*)을 여러 개 만들고, 테스트가 각 변이체를 실패로 잡는지 본다. 잡은 비율이 테스트의 판별력이다.
  - *변이 테스트(mutation testing)*: 프로그램에 단순한 결함을 인공적으로 심어, 테스트 스위트가 그것을 찾아내는 능력으로 스위트를 평가하는 결함 기반 기법(Jia–Harman TSE 2011).

쉬운 예: 소방 훈련이다.
- 경보기가 "설치돼 있다"(커버리지)와 "연기를 피우면 울린다"(변이 테스트)는 다르다. 일부러 연기를 피워 봐야 안다.

똑같은 구조다.\
`>=`를 `>`로 바꾼 사본을 만들어 테스트를 돌려 본다. 테스트가 여전히 초록이면, 운영 코드에 같은 실수가 들어와도 테스트는 초록이다.

실무 예:
- 커버리지 90% 목표를 맞추려고 단언 없는 테스트를 대량으로 붙였다. 경계값 버그가 그대로 운영에 나갔다.
- Google은 코드 리뷰 단계에서 변경된 줄에 변이체를 만들어 살아남은 것을 리뷰 코멘트로 보여 준다(Petrović–Ivanković ICSE-SEIP 2018).

## 동작·원리

### 1. 흐름 — 변이체를 만들고, 테스트로 죽인다

```text
   원본 P ──[변이 연산자]──▶ 변이체 P₁, P₂, ..., Pₙ   (각각 한 군데만 바뀜)
                                │
              각 Pᵢ에 대해 테스트 스위트 T 실행
                                │
         ┌──────────────────────┼─────────────────────────┐
     T가 실패                T가 통과                  Pᵢ 줄을 실행하는
     → KILLED(죽음)           → SURVIVED(생존)          테스트가 없음
                              = 테스트 빈틈 또는         → NO_COVERAGE
                                등가 변이체
```

- *변이체(mutant)*: 원본에서 문법적으로 작은 변경 하나를 가한 프로그램.
- *변이 연산자(mutation operator)*: 변경 규칙. 예) `<`를 `<=`로, `-`를 `+`로, `return x`를 `return 0`으로.
- *죽었다(killed)*: 변이체에서 어떤 테스트가 실패했다. *살아남았다(survived)*: 테스트가 전부 통과했다.

### 2. 왜 작은 결함으로 충분하다고 보나 — 두 가설

- *유능한 프로그래머 가설(CPH)*: 프로그래머는 정답에 가까운 프로그램을 쓴다. 그래서 실제 결함은 몇 개의 작은 문법 변경으로 고칠 수 있는 것이 대부분이라고 본다(DeMillo 외 1978, Jia–Harman 2011 II.A).
- *결합 효과(coupling effect)*: 단순한 결함을 전부 구별해 내는 테스트 데이터는 더 복잡한 결함도 상당 부분 구별해 낸다(같은 곳). Offutt는 이를 "복잡한 변이체(변경 여러 개)는 단순한 변이체(변경 하나)에 결합돼 있다"는 가설로 정식화했다.
- 이 둘은 **가설**이다. 변이 테스트가 "실제 결함 검출력"의 대리 지표가 되는 근거로 쓰인다. Google 논문은 변이체 검출과 실제 결함 검출의 상관을 보인 Just 외(FSE 2014)를 근거로 든다.

### 3. PIT의 변이 연산자 (PIT 1.x 기본 그룹 `DEFAULTS`)

| 연산자 | 변경 | 실험의 보고서 문구 |
|---|---|---|
| CONDITIONALS_BOUNDARY | `<`↔`<=`, `>`↔`>=` | changed conditional boundary |
| NEGATE_CONDITIONALS | `==`↔`!=`, `<`↔`>=` 등 조건 반전 | negated conditional |
| MATH | `+`↔`-`, `*`↔`/` 등 | Replaced integer subtraction with addition |
| INCREMENTS | `i++`↔`i--` | — |
| INVERT_NEGS | `-x` → `x` | removed negation |
| VOID_METHOD_CALLS | void 메서드 호출 제거 | — |
| EMPTY / FALSE / TRUE / NULL / PRIMITIVE_RETURNS | 반환값을 빈 값·false·true·null·0으로 | replaced int return with 0 |

- 출처: pitest.org Mutators 문서의 DEFAULTS 그룹(CONDITIONALS_BOUNDARY·INCREMENTS·INVERT_NEGS·MATH·NEGATE_CONDITIONALS·VOID_METHOD_CALLS·EMPTY_RETURNS·FALSE_RETURNS·TRUE_RETURNS·NULL_RETURNS·PRIMITIVE_RETURNS). 문서는 연산자들이 "쉽게 잡히지 않고, 등가 변이체를 적게 만들도록" 설계됐다고 쓴다.
- PIT는 소스가 아니라 **바이트코드**를 바꾼다. 그래서 보고서는 줄 번호 + 연산자 단위로 나온다.

### 실험: 커버리지는 같고 테스트만 다른 네 스위트

```java
// scratchpad/ts/07/m/src/main/java/exp/Pricing.java (줄 번호 그대로)
 5    public static int discountedPrice(int amount, boolean vip) {
 6        if (amount < 0) throw new IllegalArgumentException("negative: " + amount);
 7        if (vip && amount >= 100_000) return amount - amount / 10;
 8        if (amount >= 50_000) return amount - amount / 20;
 9        return amount;
10    }
```

- NoAssertTest: 5개 입력으로 전 경로를 호출만 한다(단언 없음).
- PartialTest: (150000, VIP)와 음수만 단언한다.
- WeakTest: 구간 한가운데 값(150000 VIP, 60000, 1000, 음수)만 단언한다.
- StrongTest: 경계값 + 결정 테이블 8행(100000/99999 VIP, 100000 비VIP, 50000/49999, 50000 VIP, 0 등)과 음수 1개를 단언한다.

(실험, maven:3.9-eclipse-temurin-21 · JUnit 5.13.4 · PIT(pitest-maven) 1.20.4 + pitest-junit5-plugin 1.2.3 · JaCoCo 0.8.14, `--cpus=2`, 2026-10-03)

```text
=================== NoAssertTest
Pricing,0,30,0,8,0,4                    ← JaCoCo: 명령 30/30 · 분기 8/8 · 라인 4/4
>> Generated 14 mutations Killed 1 (7%)
>> Mutations with no coverage 0. Test strength 7%
=================== PartialTest
Pricing,11,19,4,4,2,2                   ← 분기 4/8 · 라인 2/4
>> Generated 14 mutations Killed 6 (43%)
>> Mutations with no coverage 6. Test strength 75%
=================== WeakTest
Pricing,0,30,1,7,0,4                    ← 분기 7/8 · 라인 4/4
>> Generated 14 mutations Killed 11 (79%)
>> Mutations with no coverage 0. Test strength 79%
=================== StrongTest
Pricing,0,30,0,8,0,4                    ← 분기 8/8 · 라인 4/4
>> Generated 14 mutations Killed 14 (100%)
>> Mutations with no coverage 0. Test strength 100%
```

(JaCoCo 줄은 `jacoco.csv`의 CLASS, INSTRUCTION_MISSED, INSTRUCTION_COVERED, BRANCH_MISSED, BRANCH_COVERED, LINE_MISSED, LINE_COVERED 열)

WeakTest에서 살아남은 변이체(`mutations.csv`의 연산자·메서드·줄·상태):

```text
ConditionalsBoundaryMutator,discountedPrice,6,SURVIVED
ConditionalsBoundaryMutator,discountedPrice,7,SURVIVED
ConditionalsBoundaryMutator,discountedPrice,8,SURVIVED
(나머지 11개는 KILLED)
```

- 관찰
  - NoAssertTest와 StrongTest는 JaCoCo 수치가 **똑같다**(라인 4/4, 분기 8/8). 변이 점수는 7% vs 100%다.
  - NoAssertTest가 죽인 1개는 6번 줄 `amount < 0` 반전이다. 정상 입력에서 예외가 터져 테스트가 실패했다 — 단언 없이도 **예외**는 잡힌다.
  - WeakTest의 생존자 3개는 전부 경계 변이(`<`→`<=`, `>=`→`>`)다. 경계값 테스트가 없다는 뜻이다([07-test-design-techniques](../07-test-design-techniques/2-summary.md)).
- 처방: 생존자 줄을 보고 경계 입력(0, 99999/100000, 49999/50000)을 추가한 것이 StrongTest다.

### 4. 점수의 정의 — 분모가 다르다

```text
  학술 정의(Jia–Harman 2011)   MS = 죽인 수 / (전체 − 등가 변이체 수)
  PIT "Killed %"              = 죽인 수 / 생성한 전체 (NO_COVERAGE 포함)
  PIT "Test strength"         = 죽인 수 / (죽인 수 + 생존 수)  — NO_COVERAGE 제외

  PartialTest: 6 / 14 = 43%   vs   6 / (14 − 6) = 75%
```

- PIT maven 문서: `mutationThreshold`는 "전체 변이 중 죽인 비율", `testStrengthThreshold`는 "killed / (killed + survived), 커버리지 정보가 없는 변이 제외"로 정의한다.
- 해석: Test strength는 "**실행된 곳에서** 단언이 얼마나 날카로운가", Killed %는 "실행 여부까지 포함한 전체 판별력"이다. PartialTest처럼 실행 범위가 좁으면 둘이 크게 갈린다.
- PIT는 생성된 변이체가 등가인지 판정해 분모에서 빼지 않는다. 다만 흔한 등가·무의미 변이 일부는 아예 만들지 않는다 — 예: 로깅 프레임워크 호출이 있는 줄은 변이하지 않는다(PIT Basic concepts, 기능 `FLOGCALL`). 그래서 PIT 점수는 학술 정의의 MS보다 낮게 나올 수 있다.

### 5. 등가 변이체 — 죽일 수 없는 변이

```java
// scratchpad/ts/07/m/src/main/java/exp/MathUtil.java
public static int abs(int x) {
    if (x < 0) return -x;     // 변이: x <= 0 → x = 0이면 -0 = 0, 결과가 같다
    return x;
}
```

(실험, PIT 1.20.4, `AbsTest`: -5, -1, 0, 1, 7)

```text
>> Generated 5 mutations Killed 4 (80%)
ConditionalsBoundaryMutator,abs,5,SURVIVED
InvertNegsMutator,abs,5,KILLED
NegateConditionalsMutator,abs,5,KILLED
returns.PrimitiveReturnsMutator,abs,5,KILLED
returns.PrimitiveReturnsMutator,abs,6,KILLED
```

- *등가 변이체(equivalent mutant)*: 문법은 다르지만 동작이 원본과 같은 변이체. 어떤 테스트로도 죽일 수 없다.
- 등가 여부를 자동으로 전부 판정하는 것은 불가능하다 — 프로그램 동치는 결정 불가능하기 때문이다(Jia–Harman 2011 II.B). 사람이 보고 판단한다.
- 결과: 테스트가 0을 포함해 충분해도 점수는 80%에서 멈췄다. **100%를 목표로 강제하면** 등가 변이체 앞에서 억지 테스트나 코드 비틀기가 생긴다.

### 6. 비용 — 변이체 수 × 테스트 수

```text
  나이브:  변이체 n개 × 스위트 전체  → 큰 코드베이스에서 실행 불가
  PIT:    줄별 커버리지를 먼저 재고 → 그 줄을 덮는 테스트만 실행
          (실험 NoAssertTest: "Ran 14 tests (1 tests per mutation)")
  Google: 변경된 줄 중 커버되고 "arid"가 아닌 줄에만, 줄당 변이체 1개
```

- PIT는 변이 전 원본에서 스위트가 초록이어야 한다. 실험에서 기대값을 잘못 적은 테스트가 있을 때 `1 tests did not pass without mutation when calculating line coverage. Mutation testing requires a green suite.`로 멈췄다.
- Google(Petrović–Ivanković ICSE-SEIP 2018)
  - 리뷰 중인 diff에서 **변경되고, 커버되고, arid가 아닌 줄**만 변이한다. 줄당 변이체 하나, 연산자는 무작위로 고른다.
  - *arid 노드*: 로그 출력·메모리 예약 호출처럼 단위 테스트가 보통 검증하지 않는 코드. 언어별 전문가 규칙 + 개발자의 "Not useful" 피드백으로 걸러낸다.
  - 7만 개 넘는 diff에서 110만 변이체를 시험해 15만 개의 조치 가능한 발견을 리뷰에 띄웠다. 피드백 반영으로 "유용함" 비율이 20%에서 80%로 올랐다(논문 초록·서론).

## 쓰이는 자료구조·알고리즘

- **변이 연산자 = 코드 재작성 규칙**: PIT는 바이트코드 명령 단위(비교 점프 명령을 경계가 다른 명령으로 바꾸는 식), Google은 AST 노드 단위로 바꾼다. 규칙 표 하나가 연산자 집합이다.
- **줄 → 테스트 커버리지 맵**: 변이 전에 "어느 테스트가 어느 줄을 실행하나"를 재 둔다. 변이체마다 그 줄을 덮는 테스트만 돌린다. 덮는 테스트가 없으면 실행 없이 NO_COVERAGE다.
- **변이체 × 테스트 결과 행렬**: 행 = 변이체, 열 = 테스트, 칸 = 실패 여부. 한 테스트가 실패하면 그 변이체는 더 돌리지 않는다(조기 종료).
- **AST와 재귀 판정**: Google의 arid 판정은 "복합 노드는 자식이 전부 arid일 때만 arid"라는 재귀 정의다(트리 후위 순회).
- **표본 추출**: 줄당 하나, 연산자 무작위 선택은 변이체 집합의 표본 추출이다. Jia–Harman은 비용 절감 기법으로 mutant sampling·selective mutation(연산자 일부만)을 정리한다.

## 적용 — 풀어나가는 법

### 순서

1. **스위트를 초록으로 만든다.** PIT는 초록 스위트에서만 돈다.
2. **대상을 좁혀 돌린다.** 핵심 도메인 클래스부터(`targetClasses`), 필요한 테스트만(`targetTests`).
3. **보고서에서 SURVIVED와 NO_COVERAGE를 나눠 본다.**
   - NO_COVERAGE: 테스트가 아예 실행 안 한 줄 → 테스트 추가.
   - SURVIVED: 실행은 했지만 단언이 못 잡음 → 단언·입력 보강(경계값이 가장 흔하다).
4. **생존자마다 "이 변이가 운영에 들어오면 문제인가"를 묻는다.** 문제면 테스트를 추가한다. 동작이 같으면 등가 변이체로 기록하고 넘어간다.
5. **CI에서는 변경분 위주로 돌린다.** 전체 실행이 무거우면 증분 분석(`withHistory`)이나 변경된 클래스만 대상으로 한다. 임계값은 Killed %(`mutationThreshold`)와 Test strength(`testStrengthThreshold`) 중 무엇인지 분명히 정한다.

### 설정과 실행

```xml
<!-- pom.xml 발췌: PIT 1.20.4 + JUnit 5 플러그인 -->
<plugin>
  <groupId>org.pitest</groupId><artifactId>pitest-maven</artifactId><version>1.20.4</version>
  <dependencies>
    <dependency><groupId>org.pitest</groupId><artifactId>pitest-junit5-plugin</artifactId><version>1.2.3</version></dependency>
  </dependencies>
  <configuration>
    <targetClasses><param>exp.Pricing</param></targetClasses>
    <outputFormats><param>CSV</param><param>HTML</param></outputFormats>
    <timestampedReports>false</timestampedReports>
    <threads>2</threads>
  </configuration>
</plugin>
```

```bash
# 스위트 하나만 대상으로 변이 테스트
mvn org.pitest:pitest-maven:mutationCoverage -DtargetTests=exp.WeakTest
# 결과: target/pit-reports/index.html, mutations.csv
```

### 생존자에서 테스트로

```java
// WeakTest의 생존자: 6·7·8번 줄 경계 변이 → 경계 입력을 추가한 StrongTest
@ParameterizedTest
@CsvSource({
    "100000,true,90000",  "99999,true,95000",  "150000,true,135000",
    "100000,false,95000", "50000,false,47500", "49999,false,49999",
    "50000,true,47500",   "0,false,0"
})
void table(int amount, boolean vip, int expected) {
    assertThat(Pricing.discountedPrice(amount, vip)).isEqualTo(expected);
}
```

- `0,false,0`이 6번 줄 `amount < 0` → `<=` 변이를 죽인다(0에서 예외가 나면 실패).
- `99999,true,95000`·`100000,true,90000`이 7번 줄을, `49999`·`50000`이 8번 줄 경계 변이를 죽인다.

## 장애 시나리오와 대처

### 1. 커버리지 100%인데 단언이 없음 → 버그가 그대로 통과

- **현상**: 커버리지 게이트는 통과했는데, 할인 금액이 틀린 채로 배포됐다.
- **보이는 형태**: JaCoCo 라인·분기 100%. PIT를 돌려 보면 `Killed 1 (7%)` 같은 낮은 수치.
- **원인**: 테스트가 메서드를 호출만 하고 결과를 단언하지 않았다(커버리지 목표 맞추기).
- **대처**: 핵심 모듈에 변이 테스트를 돌려 Test strength를 본다. 단언 없는 테스트를 찾아 결과 단언을 넣는다(→ [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md)).

### 2. 경계 변이 생존 → off-by-one 장애

- **현상**: 정확히 10만 원짜리 VIP 주문만 할인이 5%로 계산된다.
- **보이는 형태**: 예외 없음. 보고서에 `changed conditional boundary → SURVIVED`(7번 줄).
- **원인**: 테스트가 구간 한가운데 값(150000)만 썼다. `>=`가 `>`로 바뀌어도 테스트가 모른다.
- **대처**: 생존한 경계 변이마다 경계값과 ±1을 추가한다. 실험에서 79% → 100%.

### 3. 등가 변이체 앞에서 100% 목표 → 억지 테스트·코드 비틀기

- **현상**: 변이 점수 100%를 CI 게이트로 걸었더니 몇 달째 통과를 못 하거나, 의미 없는 테스트가 늘어난다.
- **보이는 형태**: `abs`의 `x < 0` → `x <= 0`처럼 죽일 수 없는 생존자가 남는다(실험: 5개 중 4개, 80%).
- **원인**: 등가 변이체는 동작이 같아 어떤 테스트로도 못 죽인다. 자동 판정도 불가능하다.
- **대처**: 100%를 목표로 걸지 않는다. 생존자를 사람이 검토해 등가로 표시하고, 임계값은 팀이 정한 수준으로 둔다. 변경분의 새 생존자를 리뷰에서 보는 방식(Google)이 대안이다.

### 4. 실행 시간 폭증·타임아웃 → 아무도 안 돌림

- **현상**: 전체 프로젝트 PIT 실행이 수십 분~수 시간 걸려 CI에서 빠진다.
- **보이는 형태**: 변이체 수 × 테스트 시간이 커진다. 무한 루프가 된 변이체는 `TIMED_OUT`으로 끝난다(예: 루프 증가 연산 제거).
- **원인**: 대상 범위가 넓고, 느린 통합 테스트까지 변이마다 돈다.
- **대처**: `targetClasses`·`targetTests`로 범위를 좁히고, `threads`를 쓰고, 증분 분석(`withHistory`)이나 변경된 줄만 대상으로 한다. 타임아웃 기준은 `timeoutFactor`(기본 1.25)·`timeoutConstant`(기본 4000ms)다(PIT maven 문서).

### 5. 원본 스위트가 빨강 또는 불안정 → PIT가 멈추거나 거짓 "죽음"

- **현상**: PIT가 시작하자마자 실패한다. 또는 같은 코드에서 실행마다 변이 점수가 달라진다.
- **보이는 형태**: `1 tests did not pass without mutation when calculating line coverage. Mutation testing requires a green suite.`(실험). 불안정 테스트가 있으면 변이와 무관하게 실패해 "KILLED"로 세어진다.
- **원인**: 원본에서 실패하는 테스트, 또는 시간·순서·네트워크에 의존하는 불안정 테스트.
- **대처**: 먼저 스위트를 초록·결정적으로 만든다(→ [09-flaky-tests](../09-flaky-tests/2-summary.md)). 불안정 테스트는 변이 대상 테스트에서 뺀다.

## 핵심 문장

- 변이 테스트는 코드에 작은 결함을 심어, 테스트가 그것을 잡는지로 테스트의 판별력을 잰다.
- 같은 라인·분기 100%에서도 단언 없는 스위트는 변이 14개 중 1개, 경계값 스위트는 14개 전부를 잡았다.
- PIT의 Killed %는 실행되지 않은 변이까지 분모에 넣고, Test strength는 실행된 곳만 본다. 학술 정의는 등가 변이체를 분모에서 뺀다.
- 등가 변이체는 동작이 원본과 같아 죽일 수 없고 자동 판정도 불가능하다. 그래서 100% 목표는 맞지 않는다.
- 비용이 크므로 변경된 줄·핵심 모듈부터, 커버하는 테스트만 돌린다.

## 관련 주제·근거

- 선행
  - testing [02-good-unit-tests](../02-good-unit-tests/2-summary.md) — 회귀 방지 기둥과 단언
  - testing [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — 경계 변이를 죽이는 입력은 경계값 분석이 준다
- 후속·연결
  - testing [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md) — 커버리지가 재지 못하는 것을 변이 테스트가 잰다
  - testing [14-property-based-testing](../14-property-based-testing/2-summary.md) — 성질의 판별력도 변이로 잴 수 있다
  - testing [09-flaky-tests](../09-flaky-tests/2-summary.md) — 불안정 테스트가 변이 결과를 오염시킨다
- 논문
  - Yue Jia, Mark Harman. "An Analysis and Survey of the Development of Mutation Testing." IEEE TSE 37(5), 2011 — II.A 유능한 프로그래머 가설·결합 효과(DeMillo 외 1978, Offutt), II.B 등가 변이체(결정 불가능)·변이 점수 정의, III 비용 절감(mutant sampling·selective mutation), IV 등가 변이체 검출 기법 <http://crest.cs.ucl.ac.uk/fileadmin/crest/sebasepaper/JiaH10.pdf>
  - Goran Petrović, Marko Ivanković. "State of Mutation Testing at Google." ICSE-SEIP 2018 — diff 기반, 커버되고 arid가 아닌 줄당 변이체 1개, arid 노드 판정, 7만+ diff·110만 변이체·15만 발견, 유용함 20% → 80%, 6,000명 엔지니어 <https://research.google.com/pubs/archive/46584.pdf>
- 도구 문서
  - PIT Mutators — DEFAULTS 그룹 목록, CONDITIONALS_BOUNDARY 정의, 등가 변이 최소화 설계 <https://pitest.org/quickstart/mutators/>
  - PIT Basic concepts — KILLED·SURVIVED·NO_COVERAGE·TIMED_OUT·NON_VIABLE·MEMORY_ERROR·RUN_ERROR <https://pitest.org/quickstart/basic_concepts/>
  - PIT Maven quickstart — `mutationThreshold`·`testStrengthThreshold`(정의)·`targetClasses`·`targetTests`·`withHistory`·`threads`·`timeoutFactor` 1.25·`timeoutConstant` 4000 <https://pitest.org/quickstart/maven/>
- 실험 목록(2026-10-03, 코드는 scratchpad/ts/07/m/)
  - `run.sh` — maven:3.9-eclipse-temurin-21, JUnit 5.13.4·AssertJ 3.27.6·JaCoCo 0.8.14·PIT 1.20.4·pitest-junit5-plugin 1.2.3, `--cpus=2`: 스위트 4개(NoAssert·Partial·Weak·Strong)마다 `mvn clean test -Dtest=X jacoco:report` → `jacoco.csv`, `mvn org.pitest:pitest-maven:mutationCoverage -DtargetTests=exp.X` → 통계·`mutations.csv`
  - `MathUtil.abs` + `AbsTest` — `-DtargetClasses=exp.MathUtil -DtargetTests=exp.AbsTest`: 등가 경계 변이 생존(4/5, 80%)
  - 기대값 오류(99999 VIP → 94999로 잘못 적음)가 있던 첫 실행에서 PIT의 "requires a green suite" 중단 메시지 확인
  - 사실 점검 재실행(같은 환경, `--network none`) — 스위트 4개의 `jacoco.csv`·PIT 통계·`mutations.csv`, `abs` 4/5, green suite 중단 메시지(기대값을 94999로 바꾼 사본) 모두 같은 출력
