# software-design/29-refactoring-to-patterns — 패턴 쪽으로, 패턴에서 멀어지기 — 정리 (힌트)

## 해결하는 문제

패턴을 **처음부터** 설계하면 축을 잘못 짚기 쉽고, 패턴 없이 **방치**하면 분기가 퍼진다. 그 사이의 길이 "필요해졌을 때 작은 단계로 패턴에 도달하기"다.

```text
 처음부터 패턴                 방치                        리팩터링으로 도달
 Strategy+Factory 미리 →       switch(type)이 3곳 →        스멜이 보일 때
 예측한 축이 틀림               새 타입마다 3곳 수정         작은 단계 × 테스트 초록
 (Speculative Generality)      (Shotgun Surgery)           → 패턴이 필요한 만큼만
                                                           → 필요 없어지면 다시 걷어냄
```

- *리팩터링(refactoring)*: 겉으로 보이는 동작을 바꾸지 않고 내부 구조를 바꾸는 것. 작은 단계마다 테스트로 동작 보존을 확인한다(13 refactoring).
- *Refactoring to Patterns*: Joshua Kerievsky의 2004년 책 제목이자 접근. Fowler는 소개 글에서 이 책이 패턴을 "미리 설계하지 않고 시스템이 자라면서 진화시켜 도달하는" 길을 보인다고 썼다.

쉬운 예: 가구 배치다. 이사 첫날 수납장 위치를 다 정하지 않는다. 짐이 쌓이는 자리가 보이면 그때 수납장을 들인다. 안 쓰게 되면 치운다.\
똑같은 구조다.\
실무 예: 계좌 종류별 `switch`가 이자·수수료·라벨 세 곳에 생긴 뒤에 타입 코드를 enum으로, 분기를 다형성으로 옮긴다. 전역 싱글턴 때문에 테스트 순서가 결과를 바꾸면 싱글턴을 걷어낸다.

## 동작·원리

### 1. 세 방향 — 쪽으로, 가까이, 멀어지기

Kerievsky 카탈로그는 리팩터링 27개를 싣고 있다(Industrial Logic 카탈로그 페이지). 이 노트가 다루는 것:

```text
 스멜                                  리팩터링                                    도달하는 패턴
 문자열·int 타입 코드                  Replace Type Code With Class (K)             (타입 안전 enum/클래스)
 타입마다 계산이 갈리는 조건문          Replace Conditional Logic With Strategy (K)  Strategy
                                      Replace Conditional with Polymorphism (F)    다형성(서브클래스·enum 상수)
 상태 전이를 제어하는 복잡한 조건문    Replace State-Altering Conditionals with State (K)  State
 null 검사가 여기저기 복제             Introduce Null Object (K) / Introduce Special Case (F)  Null Object
 큰 메서드가 지역 변수에 결과를 누적   Move Accumulation To Collecting Parameter (K)  Collecting Parameter
 ───────────────── 멀어지기 ─────────────────
 전역 접근점이 필요 없는 싱글턴        Inline Singleton (K)                          (패턴 제거)
 (K) = Kerievsky 카탈로그, (F) = Fowler 『Refactoring』 2판
```

- Kerievsky 카탈로그의 문제·해법 요지(페이지에서 확인):
  - Replace Type Code With Class — 문제: `String`·`int` 같은 필드 타입이 잘못된 대입과 비교를 막지 못한다. 해법: 필드 타입을 클래스로.
  - Replace Conditional Logic With Strategy — 문제: 메서드 안 조건문이 계산의 변형 중 무엇을 실행할지 정한다. 해법: 변형마다 Strategy를 만들고 위임.
  - Replace State-Altering Conditionals with State — 문제: 상태 전이를 제어하는 조건식이 복잡하다. 해법: 상태·전이를 다루는 State 클래스로.
  - Introduce Null Object — 문제: null 필드·변수를 다루는 로직이 코드 곳곳에 중복. 해법: 알맞은 "없음" 동작을 가진 Null Object로.
  - Move Accumulation To Collecting Parameter — 문제: 지역 변수에 정보를 누적하는 큰 메서드. 해법: 추출한 메서드들에 넘겨지는 Collecting Parameter에 누적.
  - Inline Singleton — 문제: 코드가 객체에 접근해야 하지만 **전역 접근점은 필요 없다**. 해법: 싱글턴의 기능을 그 객체를 저장·제공하는 클래스로 옮기고 싱글턴을 삭제.
- Fowler 2판에서 대응하는 것: 10장 Replace Conditional with Polymorphism(272쪽)·Introduce Special Case(289쪽), 12장 Replace Type Code with Subclasses(362쪽) — InformIT 2판 목차.

### 2. 작은 단계와 초록 테스트

```text
 v0  String type + switch ×3 (이자·수수료·라벨)        테스트 6개 초록
  │  1단계 Replace Type Code with Class
  v     String → enum AccountType, switch 식(default 없음)   테스트 6개 초록 (테스트 파일 무변경)
  │  2단계 Replace Conditional with Polymorphism
  v     enum 상수마다 interest()/fee()/label             테스트 6개 초록 (테스트 파일 무변경)
 v2  Account는 type에 위임만
```

- 단계마다 **동작이 그대로**인지 테스트로 확인하고 커밋한다. 한 단계가 크면 되돌리기도 크다.
- 공개 생성자 `Account(String, long)`를 남겨 테스트·호출부를 바꾸지 않고 내부만 옮겼다. 이것이 parallel change(옛 입구를 남기고 새 입구를 더한 뒤 나중에 옛 것 제거)의 작은 형태다(51 legacy-change-techniques).
- 테스트 무변경 초록은 **약한** 신호일 뿐이다. 이 실험의 1단계도 테스트가 안 덮는 동작 하나를 바꿨다: 모르는 종류 문자열(`"GOLD"` 등)이 v0에서는 `monthlyInterest()` 호출 때 `IllegalStateException`이었지만, 1단계부터는 생성자의 `AccountType.valueOf`에서 `IllegalArgumentException`이 난다(점검 재실행, 같은 환경: v0 `java.lang.IllegalStateException: GOLD`, 1단계 `java.lang.IllegalArgumentException: No enum constant AccountType.GOLD` — 실패 시점과 예외 타입이 달라진다).

### 실험 A: 단계별 리팩터링과 "새 계좌 종류" 변경

(실험, git 2.43.0 + JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/25/e29/build.sh`·`measure.sh`, 2026-10-02)

v0의 모양:

```java
long monthlyInterest() {
    switch (type) {
        case "CHECKING": return 0;
        case "SAVINGS":  return balance * 2 / 1000;
        case "PREMIUM":  return balance * 3 / 1000;
        default: throw new IllegalStateException(type);
    }
}
// monthlyFee()에 같은 switch, Statement.label()에 같은 switch(default: return "?")
```

2단계 후의 모양:

```java
public enum AccountType {
    CHECKING("입출금") {
        long interest(long balance) { return 0; }
        long fee(long balance) { return balance < 100_000 ? 1_000 : 0; }
    },
    SAVINGS("저축")   { long interest(long balance) { return balance * 2 / 1000; } },
    PREMIUM("프리미엄") { long interest(long balance) { return balance * 3 / 1000; } };
    final String label;
    AccountType(String label) { this.label = label; }
    abstract long interest(long balance);
    long fee(long balance) { return 0; }
}
```

같은 변경 요청 — **BUSINESS 계좌 추가(이자 0.1%, 수수료 월 5,000원)** — 을 v0 브랜치와 2단계 뒤 브랜치에 각각 적용했다. v0 쪽은 `Account`의 두 `switch`만 고치고 `Statement.label`은 깜빡한 상황이다.

```text
== 리팩터링 단계별 diff (테스트 파일 변경 여부 포함)
  [step1: Replace Type Code with Class]  3 files changed, 18 insertions(+), 20 deletions(-)
       src/Account.java     | 26 ++++++++++++--------------
       src/AccountType.java |  1 +
       src/Statement.java   | 11 +++++------
  [step2: Replace Conditional with Polymorphism]  3 files changed, 19 insertions(+), 21 deletions(-)
       src/Account.java     | 15 ++-------------
       src/AccountType.java | 17 ++++++++++++++++-
       src/Statement.java   |  8 +-------
== 같은 변경 요청: BUSINESS 계좌 추가
  [add-business-on-v0]  1 file changed, 3 insertions(+), 1 deletion(-)
       src/Account.java | 4 +++-
  [add-business-after-refactor]  1 file changed, 4 insertions(+)
       src/AccountType.java | 4 ++++
== 실행 [v0] v0: type code + switch x3
  tests: 6 pass, 0 fail
== 실행 [main~1] step1: Replace Type Code with Class
  tests: 6 pass, 0 fail
== 실행 [main] step2: Replace Conditional with Polymorphism
  tests: 6 pass, 0 fail
== 실행 [add-business-on-v0] add BUSINESS (on v0) - Statement.label 깜빡함
  tests: 6 pass, 0 fail
  BUSINESS interest=1000 fee=5000 label=?
== 실행 [add-business-after-refactor] add BUSINESS (after refactor)
  tests: 6 pass, 0 fail
  BUSINESS interest=1000 fee=5000 label=사업자
```

- 관찰 1 — 두 단계 모두 **테스트 파일을 고치지 않고** 6개 초록이었다. 단계 하나가 약 40줄 diff였다.
- 관찰 2 — 숫자로는 둘 다 4줄이다. 하지만 v0의 4줄은 라벨을 **빠뜨린 불완전한 변경**이다. 요구를 다 채우려면 `Statement.java`에도 `case` 1줄을 더해 2파일을 고쳐야 한다(이 완전한 판은 커밋해 재지 않았다). 그래서 이 실험은 크기 비교가 아니다. 보인 것은 **누락 가능성**이다. v0은 `Statement.label`을 빠뜨려도 테스트가 다 초록이었고 화면에 `label=?`가 나갔다.
- 관찰 3 — 리팩터링 후에는 라벨이 enum 생성자 인자라 빠뜨릴 수 없다. 이자를 빠뜨리면 컴파일이 막힌다:

(같은 환경, BUSINESS에서 `interest` 구현을 지운 판, `scratchpad/sd/25/e29/abstractmiss/`)

```text
/e/abstractmiss/AccountType.java:12: error: <anonymous AccountType$4> is not abstract and does not override abstract method interest(long) in AccountType
    BUSINESS("사업자") {
    ^
1 error
```

- 해석: 이 리팩터링은 "다음 변경을 더 작게"보다 "다음 변경에서 **한 곳을 잊을 수 없게**"를 샀다. 비용은 두 단계 약 80줄의 diff와, 타입별 지식이 계좌 종류 쪽으로 옮겨져 "이자 규칙 전체"를 한눈에 보려면 enum 상수를 훑어야 한다는 점이다.

### 3. 패턴에서 멀어지기 — Inline Singleton

```text
 전: PricingBefore ──getInstance()──> RateTable(전역, 가변 promoBp)
       테스트 A가 promo를 설정 → 테스트 B가 그 값을 본다
 후: PricingAfter(Rates r)  ← 테스트마다 자기 Rates를 만들어 넘긴다
```

### 실험 B: 가변 싱글턴과 테스트 순서

```java
static final class RateTable {                           // 전
    private static final RateTable INSTANCE = new RateTable();
    static RateTable getInstance() { return INSTANCE; }
    private long promoBp = 0;
    void setPromo(long bp) { promoBp = bp; }
    long rateBp() { return 300 - promoBp; }
}
static final class PricingAfter {                        // 후
    final Rates rates; PricingAfter(Rates r) { rates = r; }
    long fee(long amount) { return amount * rates.rateBp() / 10_000; }
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/25/e29/singleton/Singleton.java`, 2026-10-02 — 같은 JVM에서 테스트 두 개를 지정한 순서로 실행)

```text
  [before] 순서 [defaultTest, promoTest] → defaultTest=PASS promoTest=PASS
  [before] 순서 [promoTest, defaultTest] → promoTest=PASS defaultTest=FAIL
  [after] 순서 [defaultTest, promoTest] → defaultTest=PASS promoTest=PASS
  [after] 순서 [promoTest, defaultTest] → promoTest=PASS defaultTest=PASS
```

- 싱글턴 판은 **순서에 따라** `defaultTest`가 깨졌다. 앞 테스트가 바꾼 전역 상태가 남았다.
- 인스턴스를 넘기는 판은 두 순서 모두 초록이었다. 싱글턴 대신 "하나만 만들기"는 조립 지점(25 dependency-injection-and-composition-root)이나 Spring 빈 스코프가 맡는다.

## 쓰이는 자료구조·알고리즘

- **조건 분기 → 다형 디스패치 테이블** — `switch(type)`은 런타임에 문자열 비교·점프로 가지를 고른다. enum 상수 메서드·가상 메서드는 JVM이 객체의 클래스로 구현을 고른다(가상 호출 — HotSpot은 클래스 메타데이터(`InstanceKlass`)에 메서드 표(vtable)를 넣어 둔다: `src/hotspot/share/oops/klassVtable.hpp` 주석 "the variable-length vtable that is embedded in InstanceKlass". 다른 JVM의 구현 세부는 다를 수 있고, JIT는 인라인 캐시·인라인으로 표 조회를 생략하기도 한다). 효과는 "타입 → 구현" 표를 언어가 관리하는 것이다.
- **enum = 닫힌 집합** — 상수가 고정이라 `values()`로 전부 순회하고, 추상 메서드로 각 상수의 구현을 강제한다(실험 A의 컴파일 오류).
- **Null Object = 항등원** — "할인 없음"은 곱셈의 1처럼 아무것도 바꾸지 않는 원소다. 분기 대신 이 원소를 넘긴다.
- **Collecting Parameter = 누적기 전달** — 여러 메서드가 하나의 누적 객체(`StringBuilder`·`List`)에 결과를 더한다. fold의 객체 지향 형태다.

### 실험 C: Introduce Null Object

```java
static long priceNullable(String customer, long amount) {
    Discount d = byCustomer.get(customer);             // 없으면 null
    return d.apply(amount);
}
static long priceNullObject(String customer, long amount) {
    return byCustomer.getOrDefault(customer, NoDiscount.INSTANCE).apply(amount);
}
```

(실험, 같은 환경, `scratchpad/sd/25/e29/singleton/NullObj.java`, `-g` 없이 컴파일)

```text
  null 반환판   alice → 9000
  Null Object판 alice → 9000
  null 반환판   bob → java.lang.NullPointerException: Cannot invoke "NullObj$Discount.apply(long)" because "<local3>" is null
  Null Object판 bob → 10000
```

- 할인이 없는 고객(bob)에서 null 반환판은 NPE, Null Object판은 원가 10,000원.
- NPE 메시지의 `<local3>`는 디버그 정보(`-g`) 없이 컴파일해서 지역 변수 이름 대신 슬롯 번호가 나온 것이다.
- "없음"을 null·Optional·Null Object·예외 중 무엇으로 나타낼지는 18 absence-and-null-design에서 다룬다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **스멜을 확인한다**: 같은 `switch`가 몇 곳인가, 같은 null 검사가 몇 곳인가. 한 곳이면 아직 패턴이 필요 없다(28 taming-conditionals).
2. **안전망**: 바꿀 동작을 덮는 테스트가 있는지. 없으면 특성 테스트(현재 동작을 그대로 기록하는 테스트)부터.
3. **가장 작은 리팩터링부터**: 타입 코드 → enum이 먼저, 그다음 분기 → 다형성. 단계마다 테스트 초록 + 커밋.
4. **패턴은 필요한 만큼만**: 계산 변형이 값 몇 개면 enum 상수 필드로 끝낸다. 변형이 여러 연산·상태를 가지거나 바깥에서 추가돼야 할 때 Strategy 클래스로.
5. **멀어지기도 같은 절차로**: 구현이 하나로 줄어든 Strategy, 아무도 안 바꾸는 Factory, 전역 접근점이 필요 없는 Singleton은 인라인한다.

### 2. 커밋 단위 확인

```bash
# 리팩터링 커밋에서 테스트 파일이 바뀌지 않았는지 (동작 보존의 약한 신호)
git diff --stat HEAD~1 HEAD -- 'src/test/**' 'src/**/*Test.java'
# 리팩터링과 기능 변경이 한 커밋에 섞였는지 — 커밋 메시지와 diff를 함께 본다
git log --stat --format='%h %s' -5
```

- 리팩터링 커밋과 기능 커밋을 나눈다(14 tidy-first). 실험 A도 step1·step2와 "add BUSINESS"를 다른 커밋으로 뒀다.

### 3. 진단 — 싱글턴과 전역 상태

```bash
grep -rnE 'getInstance\(\)|static .* INSTANCE' src/main/java
# 테스트 순서 의존 확인: JUnit 5는 @TestMethodOrder(MethodOrderer.Random.class)로 무작위 순서를 걸어 본다
```

- 무작위 순서에서만 깨지는 테스트는 공유 가변 상태(싱글턴·정적 필드·정적 캐시)를 의심한다.

## 장애 시나리오와 대처

### 1. 처음부터 패턴을 설계 → Speculative Generality (⚠ 커리큘럼)

- 현상: 구현이 하나뿐인 Strategy·Factory가 여러 개. 실제 요구가 오면 미리 만든 구조가 안 맞아 층마다 고친다.
- 보이는 형태: 27 design-patterns-gof 실험 A — 예측한 축과 실제 축이 달라 6파일 변경(plain은 1파일).
- 원인: 스멜이 생기기 전에 패턴을 넣었다.
- 대처: 인라인해 단순하게 되돌리고, 같은 분기가 실제로 반복될 때 이 노트의 단계로 다시 도달한다.

### 2. 분기 폭증 방치 → 새 타입마다 `switch` N곳 수정 (Shotgun Surgery) (⚠ 커리큘럼)

- 현상: 새 계좌 종류를 추가했는데 명세서 라벨이 "?"로 나온다. 테스트는 다 초록.
- 보이는 형태: 실험 A의 `add-business-on-v0` — `tests: 6 pass, 0 fail`, `label=?`.
- 원인: 타입별 지식이 세 `switch`에 흩어지고 한 곳에 `default`가 있었다. 기존 테스트는 새 타입을 몰랐다.
- 대처: Replace Type Code with Class → Replace Conditional with Polymorphism. 타입별 지식을 한 곳에 모으면 누락이 컴파일 오류가 된다(실험 A의 `is not abstract and does not override`).

### 3. 패턴을 제거하지 못해 간접 계층 화석화 (⚠ 커리큘럼)

- 현상: 몇 년 전 만든 `PaymentStrategyFactory`가 이제 구현 하나만 돌려준다. 아무도 지우지 못한다.
- 보이는 형태: 구현이 하나인 인터페이스, 호출 경로의 통과 메서드, "왜 있는지 아무도 모름".
- 원인: 패턴 도입은 쉽지만 제거에는 테스트와 확신이 필요하다. 안전망이 없으면 그대로 둔다.
- 대처: 호출부를 전수 확인(IDE 호출 계층·grep)하고 인라인 리팩터링을 작은 단계로. Kerievsky의 Inline Singleton처럼 "패턴에서 멀어지는" 리팩터링도 정식 절차로 다룬다.

### 4. 가변 싱글턴 → 테스트 순서에 따라 실패

- 현상: CI에서 가끔만 깨지는 테스트. 로컬에서 그 테스트만 돌리면 초록.
- 보이는 형태: 실험 B — `[promoTest, defaultTest]` 순서에서만 `defaultTest=FAIL`.
- 원인: 앞 테스트가 싱글턴의 가변 상태를 바꾸고 되돌리지 않았다.
- 대처: Inline Singleton — 인스턴스를 만들어 넘기고, "하나만"은 조립 지점에서 보장한다. 당장 못 걷어내면 테스트마다 상태를 초기화하는 훅을 두되, 그것은 증상 완화다.

## 핵심 문장

- 패턴은 처음부터 설계하기보다 스멜이 보일 때 작은 리팩터링 단계로 도달한다(Kerievsky 2004).
- 실험에서 타입 코드 → enum → 다형성 두 단계를 테스트 파일을 바꾸지 않고 초록으로 마쳤다.
- 이 리팩터링이 산 것은 다음 변경의 크기가 아니라 누락 불가능성이다. v0은 라벨을 빠뜨려도 테스트가 초록이었고, 리팩터링 후에는 빠뜨린 구현이 컴파일 오류가 됐다.
- 패턴에서 멀어지는 것도 리팩터링이다. Inline Singleton은 전역 접근점이 필요 없을 때 싱글턴을 지운다.
- 가변 싱글턴은 테스트 순서 의존을 만든다. 실험에서 한 순서에서만 테스트가 깨졌고, 인스턴스를 넘기자 두 순서 모두 초록이었다.

## 관련 주제·근거

- 선행
  - [13-refactoring](../13-refactoring/2-summary.md)
  - [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) — 패턴 목록과 과설계 실험, 원본 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md)
- 후속·연결
  - [28-taming-conditionals](../28-taming-conditionals/2-summary.md) — 조건문 도구 선택(테이블·빠짐없는 `switch`)
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 싱글턴 대신 조립 지점
  - [18-absence-and-null-design](../18-absence-and-null-design/2-summary.md), [51-legacy-change-techniques](../51-legacy-change-techniques/2-summary.md), [10 code-smells](../10-code-smells/2-summary.md)·[14 tidy-first](../14-tidy-first/2-summary.md)
- 글·문서
  - Joshua Kerievsky, 『Refactoring to Patterns』(Addison-Wesley, 2004) — Industrial Logic 카탈로그(27개)와 항목별 문제·해법 페이지: Replace Type Code With Class, Replace Conditional Logic With Strategy, Replace State-Altering Conditionals with State, Introduce Null Object, Move Accumulation To Collecting Parameter, Inline Singleton <https://www.industriallogic.com/xp/refactoring/catalog.html>
  - Martin Fowler, Kerievsky 책 소개 글 <https://martinfowler.com/books/r2p.html>
  - Martin Fowler, 『Refactoring』 2판(Addison-Wesley, 2018) — 10장 Replace Conditional with Polymorphism(272쪽)·Introduce Special Case(289쪽), 12장 Replace Type Code with Subclasses(362쪽), InformIT 목차 <https://www.informit.com/store/refactoring-improving-the-design-of-existing-code-9780134757681>
- 실험 목록 (코드: scratchpad `sd/25/e29/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`)
  - A `build.sh`(git 저장소: v0 → step1 → step2, BUSINESS 추가 브랜치 2개) → `measure.sh`(단계·변경 diff, 커밋마다 테스트·`Probe.java`) / `abstractmiss/`(구현 누락 컴파일 오류)
  - B `singleton/Singleton.java` — 가변 싱글턴 vs 인스턴스 전달, 테스트 순서 두 가지
  - C `singleton/NullObj.java` — null 반환 vs Null Object
