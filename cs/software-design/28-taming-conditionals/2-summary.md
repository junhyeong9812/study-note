# software-design/28-taming-conditionals — 조건문 다스리기: 도구 고르기 — 정리 (힌트)

## 해결하는 문제

분기는 프로그램의 본질이다. 문제는 분기가 **한 메서드에 얽히거나, 같은 분기가 여러 곳에 복제될 때**다.

```text
 얽힘                                      복제
 rate(grade, region, promo)                Fee.bp(type)    switch(type) … default
   if VIP                                  Points.earn(type) switch(type) … default
     if DOMESTIC                           Label.of(type)  switch(type) … default
       if promo … else …                   새 타입 추가 → 세 곳 중 한 곳 누락
     else …                                → default가 조용히 받아 준다 (에러 없음)
   else if GOLD …
 새 등급 추가 → 어느 가지에 넣지?
```

- *분기(branch)*: 조건에 따라 실행 경로가 갈리는 지점. `if`·`switch`·삼항 연산자·`&&`/`||`.
- *결정 테이블(decision table)*: 조건 조합을 행으로, 결과를 열로 둔 표. 분기를 데이터로 바꾼다.

쉬운 예: 택배 요금표다. 무게 × 지역을 `if`로 외우지 않고 표를 본다. 표에 없는 칸이면 "문의"라고 적혀 있다.\
똑같은 구조다.\
실무 예: 요금·수수료 계산(고객 등급 × 지역 × 프로모션), 결제 수단별 처리, 상태별 허용 동작.

이 주제는 **도구를 고르는 기준**이다. 패턴 쪽으로 단계별 리팩터링하는 경로는 29 refactoring-to-patterns다.

## 동작·원리

### 1. 도구 사다리 — 아래 단부터

```text
 1 가드 절        예외·특수 경우를 먼저 return → 본문 들여쓰기 한 단
 2 분해           조건식·가지를 이름 있는 함수로 (Decompose Conditional)
 3 테이블(맵)     조건 조합 → 값 이 데이터면 Map/EnumMap/배열
 4 다형성         타입마다 "행동"이 다르면 enum 상수 메서드·Strategy·State
 5 규칙 엔진      규칙을 비개발자가 바꾸고 배포 없이 반영해야 할 때
 위로 갈수록 바꾸기 쉬운 것이 늘지만, 흐름을 따라가기는 어려워진다
```

- Fowler 『Refactoring』 2판 10장 「Simplifying Conditional Logic」의 리팩터링: Decompose Conditional(260쪽) · Consolidate Conditional Expression(263) · Replace Nested Conditional with Guard Clauses(266) · Replace Conditional with Polymorphism(272) · Introduce Special Case(289) · Introduce Assertion(302) — InformIT의 2판 목차로 확인.
- 같은 책 3장 스멜 목록에 **Repeated Switches**(79쪽)가 있다. "`switch`가 있다"가 아니라 "같은 `switch`가 반복된다"가 신호다.

### 2. 언제 어느 단인가

| 신호 | 고를 단 |
|---|---|
| 앞쪽에 예외 경우가 몰려 본문이 깊다 | 1 가드 절 |
| 조건식이 길어 의도가 안 보인다 | 2 분해 |
| 결과가 **값**(요율·라벨·한도)이고 조건이 이산 조합이다 | 3 테이블 |
| 결과가 **행동**이고 같은 타입 분기가 여러 곳에 있다 | 4 다형성(또는 빠짐없는 `switch`) |
| 규칙을 운영자가 자주 바꾸고 배포 주기와 분리해야 한다 | 5 규칙 엔진 |
| 분기가 2~3개이고 한 곳에만 있다 | 그대로 둔다 |

### 실험 A: 얽힌 `if` 사다리 vs 결정 테이블 — 복잡도와 "표에 없는 경우"

같은 요율 규칙(등급 4 × 지역 2 × 프로모션 2 = 16 조합)을 두 방식으로 구현했다.

```java
// IfLadder: 등급 × 지역 × 프로모션이 한 메서드에 얽힘
if (grade.equals("VIP")) {
    if (region.equals("DOMESTIC")) { if (promo) { r = 50; } else { r = 80; } }
    else { if (promo) { r = 120; } else { r = 150; } }
} else if (grade.equals("GOLD")) { ... }
  else if (grade.equals("SILVER")) { ... }
  else { if (region.equals("DOMESTIC")) { r = 250; } else { r = 300; } }   // 나머지는 BASIC 취급

// Table: 행 하나 = 규칙 하나
record Key(String grade, String region, boolean promo) {}
static final Map<Key, Long> RATE = Map.ofEntries(
    Map.entry(new Key("VIP", "DOMESTIC", true), 50L), Map.entry(new Key("VIP", "DOMESTIC", false), 80L), ... ); // 16행
static long rateBp(String grade, String region, boolean promo) {
    Long r = RATE.get(new Key(grade, region, promo));
    if (r == null) throw new IllegalArgumentException("규칙 없음: " + grade + "/" + region + "/" + promo);
    return r;
}
```

(실험, JDK 21.0.12 temurin `--cpus=2`, PMD 7.17.0, `scratchpad/sd/25/e28/pmd/`, 2026-10-02 — PMD 임계를 1로 낮춘 규칙 파일로 모든 값을 출력)

```text
조합 16개 중 두 구현 결과 일치 16개
IfLadder PLATINUM → 250 (예외 없음, 마지막 else로 처리)
Table PLATINUM → java.lang.IllegalArgumentException: 규칙 없음: PLATINUM/DOMESTIC/false
== PMD (임계 1) — 발췌: 클래스 합계 줄(IfLadder 11, Table 3)은 생략
IfLadder.java:3:	CognitiveComplexity:	The method 'rateBp(String, String, boolean)' has a cognitive complexity of 31, current threshold is 1
IfLadder.java:3:	CyclomaticComplexity:	The method 'rateBp(String, String, boolean)' has a cyclomatic complexity of 11.
Table.java:14:	CognitiveComplexity:	The method 'rateBp(String, String, boolean)' has a cognitive complexity of 1, current threshold is 1
Table.java:14:	CyclomaticComplexity:	The method 'rateBp(String, String, boolean)' has a cyclomatic complexity of 3.
== PMD (design 규칙 CyclomaticComplexity·CognitiveComplexity를 기본 속성으로)
IfLadder.java:3:	CognitiveComplexity:	The method 'rateBp(String, String, boolean)' has a cognitive complexity of 31, current threshold is 15
IfLadder.java:3:	CyclomaticComplexity:	The method 'rateBp(String, String, boolean)' has a cyclomatic complexity of 11.
```

- 두 구현은 16 조합 모두 같은 값을 냈다. 동작은 같고 구조만 다르다.
- 순환 복잡도 11 → 3, 인지 복잡도 31 → 1. 기본 임계(순환 10, 인지 15 — PMD 7.17.0 design 규칙 문서)로는 `IfLadder`만 걸렸다.
- PMD 7.17.0의 `rulesets/java/quickstart.xml`에는 이 두 규칙이 **주석 처리**돼 있다(jar 안 파일로 확인). quickstart만 돌리면 복잡도 경고가 하나도 안 나온다(점검 재실행에서 0건). 규칙을 직접 켜야 한다.
  - *순환 복잡도(cyclomatic complexity)*: 결정 지점 수 + 1. PMD 7.17.0의 계산(`CycloVisitor` 소스)은 `if`·`while`·`for`·`case`·`catch`·삼항·`&&`/`||`에 더해 **`throw`도 +1**로 센다. 그래서 `Table`의 3 = 1 + `if` 1 + `throw` 1이다. `IfLadder`의 11 = 1 + `if` 10. PMD 문서: 1~4 낮음, 5~7 보통, 8~10 높음, 11 이상 매우 높음.
  - *인지 복잡도(cognitive complexity)*: 사람이 읽기 어려운 정도. 중첩될수록 가중치가 붙는다(SonarSource 백서, PMD 문서가 링크). 순환 복잡도는 11인데 인지 복잡도가 31인 것은 중첩 때문이다.
- **새 등급 PLATINUM**: `IfLadder`는 마지막 `else`가 받아 BASIC 요율(250)을 **조용히** 매겼다. `Table`은 "규칙 없음" 예외로 바로 드러냈다.
- 측정 지표의 정의·한계는 52 complexity-metrics에서 다룬다.

### 실험 B: 복제된 `switch`에 새 타입 추가

`PayType`에 `GIFT`를 추가하고 `Fee`만 고쳤다(`Points`·`Label`은 깜빡함). 세 판을 비교했다.

```java
// v1: switch 문 + default (세 파일에 복제)
class Label { static String of(PayType t) { switch (t) { case CARD: return "카드"; case BANK: return "계좌이체"; case POINT: return "포인트"; default: return "기타"; } } }
// v2: switch 식 + default 없음
class Label { static String of(PayType t) { return switch (t) { case CARD -> "카드"; case BANK -> "계좌이체"; case POINT -> "포인트"; }; } }
// v3: 타입별 지식을 enum 상수 한 곳에
enum PayType { CARD(300, 100, "카드"), BANK(100, 50, "계좌이체"), POINT(0, 0, "포인트"), GIFT(50, 0, "상품권"); ... }
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/25/e28/dup/`, 2026-10-02)

```text
== v1: javac
  (javac exit=0)
  CARD  fee=300bp earn=100bp label=카드
  BANK  fee=100bp earn= 50bp label=계좌이체
  POINT fee=  0bp earn=  0bp label=포인트
  GIFT  fee= 50bp earn=  0bp label=기타
== v2: javac
v2/App.java:4: error: the switch expression does not cover all possible input values
class Points { static long earnBp(PayType t) { return switch (t) { case CARD -> 100; case BANK -> 50; case POINT -> 0; }; } }
                                                      ^
1 error
  (javac exit=1)
== v3: javac
  (javac exit=0)
  ...
  GIFT  fee= 50bp earn=  0bp label=상품권
```

- v1은 컴파일·실행 모두 성공했고 화면에 `label=기타`가 나갔다. 적립은 `default`의 0이라 맞는지 틀린지 코드만 봐서는 모른다. **에러가 없다.**
- v2는 컴파일이 막혔다. JEP 361(Java 14): `switch` **식**은 빠짐없어야(exhaustive) 하고, enum의 모든 상수를 다룬 `switch` 식에는 컴파일러가 `default`를 넣어 준다 — 그래서 `default`를 직접 쓰지 않아야 새 상수에서 컴파일 오류가 난다. `switch` **문**은 빠짐없을 필요가 없다(JEP 361 본문). JEP 441(Java 21)은 패턴 `switch` 문에도 빠짐없음을 요구한다.
- v2에서 javac는 이 실행에서 **한 번에 한 곳만** 보고했다. `Points`를 고치고 다시 컴파일하자 `Label`이 나왔다(세 클래스를 파일 셋으로 나눠도 같았다). 비공개 옵션 `-XDshould-stop.ifError=GENERATE`를 주자 두 곳이 함께 나왔다(`out3.txt`). 누락이 여러 곳이면 컴파일을 여러 번 돌게 된다.
- v3는 타입별 지식이 한 곳(enum 상수)에 있어 `GIFT` 추가가 한 줄이었다. 누락할 다른 곳이 없다.

## 쓰이는 자료구조·알고리즘

- **룩업 맵(해시)** — 조건 조합을 키로 묶어(`record Key`) O(1)로 찾는다. 키 공간이 enum이면 `EnumMap`(배열 기반)이 더 가볍다. 해시 테이블은 [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **결정 테이블** — 조건 n개의 조합이 행이 된다. 이 실험은 4 × 2 × 2 = 16행. 조건이 늘면 곱으로 커진다(설정 조합 폭발). "같은 결과 행 묶기"(예: SILVER는 프로모션 무관)로 줄인다.
- **디스패치 테이블** — 값 대신 **함수**를 담은 맵(`Map<PayType, Function<Order, Long>>`). 테이블과 다형성의 중간.
- **다형 디스패치** — enum 상수 메서드·인터페이스 구현으로 JVM의 가상 호출이 분기를 대신한다. 타입 쪽 지식이 한 곳에 모인다(실험 B v3).
- **완전성 검사** — 컴파일러가 `switch` 식·패턴 `switch`의 모든 경우가 다뤄졌는지 검사한다(JEP 361·441). 테이블은 기동 시점 검사로 대신한다(아래 적용 2).

## 적용 — 풀어나가는 법

### 1. 순서

1. **복제부터 찾는다**: 같은 타입으로 분기하는 곳이 몇 군데인가. 한 곳이면 그대로 두거나 가드 절·분해로 끝낸다.

```bash
# 같은 selector로 switch하는 곳 (예시)
grep -rnE 'switch \((type|payType|method|grade)\)' src/main/java | awk -F: '{print $1}' | sort | uniq -c
# 같은 문자열 비교가 반복되는 곳
grep -rnE '\.equals\("(VIP|GOLD|SILVER)"\)' src/main/java | wc -l
```

2. **결과가 값이면 테이블**, 행동이면 다형성. 결과가 값인데 다형성으로 만들면 클래스 수만 는다.
3. **`default`를 지운다**: enum `switch`는 식으로 바꾸고 `default`를 두지 않는다. 남은 `switch` 문에는 `default -> throw new IllegalStateException(t.name())`처럼 **크게 실패**하게 한다.
4. **복잡도를 잰다**: PMD `CyclomaticComplexity`·`CognitiveComplexity`(기본 10·15), Sonar 인지 복잡도. 전후를 비교한다(실험 A).
5. **규칙 엔진은 마지막**: 운영자가 규칙을 바꿔야 하고 그 변경을 테스트할 장치(규칙 테스트 케이스·검토 절차)가 있을 때만.

### 2. 테이블을 안전하게 — 기동 시점 완전성 검사

```java
enum Grade { VIP, GOLD, SILVER, BASIC }
enum Region { DOMESTIC, OVERSEAS }
static final Map<Grade, Map<Region, Long>> RATE = new EnumMap<>(Grade.class);
static {
    RATE.put(Grade.VIP, new EnumMap<>(Map.of(Region.DOMESTIC, 80L, Region.OVERSEAS, 150L)));
    // ...
    for (Grade g : Grade.values()) for (Region r : Region.values())          // 표에 빈칸이 있으면 기동 실패
        if (RATE.getOrDefault(g, Map.of()).get(r) == null) throw new IllegalStateException("요율 누락: " + g + "/" + r);
}
```

- 문자열 키(`"VIP"`) 대신 enum을 쓰면 오타가 컴파일 오류가 되고, 빈칸 검사를 `values()`로 돌 수 있다.

### 3. 반대 방향 — 단순 분기를 클래스로 만들지 않는다

```java
// 이 정도는 그대로 둔다: 분기 3개, 한 곳, 결과가 값
long shippingFee(Region r) {
    return switch (r) { case DOMESTIC -> 3_000; case JEJU -> 6_000; case OVERSEAS -> 20_000; };
}
```

- 이것을 `ShippingPolicy` 인터페이스 + 구현 3개 + 팩토리 1개로 바꾸면 파일 5개가 생기고 호출 경로가 길어진다. 27 design-patterns-gof 실험 A에서 같은 종류의 과설계가 축이 바뀌자 6파일 변경을 불렀다.

## 장애 시나리오와 대처

### 1. 요금 `if-else` 200줄에 새 등급 추가 → 분기 누락 (⚠ 커리큘럼)

- 현상: PLATINUM 고객이 BASIC 요율로 결제된다. 에러·경고 없음.
- 보이는 형태: 실험 A의 `IfLadder PLATINUM → 250 (예외 없음, 마지막 else로 처리)`. 정산 대사에서 등급별 매출이 어긋나서야 발견.
- 원인: 마지막 `else`가 "나머지 전부"를 받는다. 새 값이 기존 가지 중 하나로 조용히 흘렀다.
- 대처: 조합을 결정 테이블로 옮기고 표에 없으면 예외. 등급을 enum으로 바꾸고 기동 시점 완전성 검사.

### 2. `switch(type)`이 여러 파일에 복제 → 새 타입 때 한 곳 누락, 기본 분기로 조용히 처리 (⚠ 커리큘럼)

- 현상: 새 결제 수단 GIFT의 영수증 라벨이 "기타", 포인트 적립 0.
- 보이는 형태: 실험 B v1 — 컴파일·실행 성공, `label=기타`.
- 원인: Repeated Switches + `default`. 타입별 지식이 세 곳에 흩어져 있고 `default`가 누락을 삼킨다.
- 대처: `switch` 식 + `default` 제거로 컴파일러가 누락을 잡게 한다(v2). 더 나아가 타입별 지식을 enum 상수 한 곳으로 모은다(v3). 컴파일 오류가 한 번에 하나씩 나올 수 있으니 고친 뒤 다시 컴파일한다.

### 3. 단순 분기 3개를 클래스 5개로 → 흐름 추적 불가 (⚠ 커리큘럼)

- 현상: 배송비 하나 바꾸려는데 인터페이스·팩토리·구현을 오가며 실제 계산을 찾는다.
- 보이는 형태: 구현이 하나 또는 몇 개뿐인 인터페이스, 호출 스택 깊이 증가(27 실험 A: 3 vs 5).
- 원인: "if는 나쁘다"는 규칙을 기계적으로 적용. 축이 없는 곳에 다형성을 넣었다.
- 대처: 인라인해 `switch` 식으로 되돌린다(29의 "패턴에서 멀어지기").

### 4. 설정 조합 폭발 — 플래그 n개 = 경로 2ⁿ

- 현상: 기능 플래그 5개 조합 중 일부에서만 버그. 테스트에 없는 조합이다.
- 보이는 형태: 특정 테넌트·특정 플래그 조합에서만 재현.
- 원인: 플래그마다 `if`가 코드 곳곳에 흩어져 조합 수(2⁵ = 32)만큼 경로가 생겼다.
- 대처: 허용 조합을 결정 테이블(또는 enum 프로필)로 명시하고 그 밖은 기동 거부. 다 쓴 플래그 분기는 걷어낸다(54 designing-for-deletion).

## 핵심 문장

- 문제는 분기 자체가 아니라 얽힌 분기와 복제된 분기다. 같은 `switch`가 여러 곳에 반복되는 것이 진짜 신호다(Fowler 2판의 Repeated Switches).
- 도구는 가드 절 → 분해 → 테이블 → 다형성 → 규칙 엔진 순으로, 처음 맞는 단에서 멈춘다.
- 결과가 값이면 테이블, 행동이면 다형성이다. 실험에서 같은 규칙의 순환 복잡도가 11에서 3으로, 인지 복잡도가 31에서 1로 줄었다.
- `default`와 마지막 `else`는 새 값을 조용히 삼킨다. `switch` 식에서 `default`를 빼면 javac가 누락을 컴파일 오류로 알린다.
- 분기 2~3개가 한 곳에만 있으면 그대로 둔다. 클래스로 바꾸면 흐름만 길어진다.

## 관련 주제·근거

- 선행
  - [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) — Strategy·State, 과설계 실험
  - [10 code-smells](../10-code-smells/2-summary.md)
- 후속·연결
  - [29-refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md) — 조건문에서 패턴 쪽으로 단계별 리팩터링
  - [24-types-as-invariants](../24-types-as-invariants/2-summary.md)(sealed·불법 상태), [54-designing-for-deletion](../54-designing-for-deletion/2-summary.md), [52 complexity-metrics](../52-complexity-metrics/2-summary.md)
  - 원본 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) 「20. State」 — enum + 추상 메서드로 전이 규칙을 한 곳에
- 글·문서
  - Martin Fowler, 『Refactoring』 2판(Addison-Wesley, 2018) 3장 Repeated Switches(79쪽), 10장 Simplifying Conditional Logic(259쪽~) — InformIT 2판 목차 <https://www.informit.com/store/refactoring-improving-the-design-of-existing-code-9780134757681> · 카탈로그 "Replace Conditional with Polymorphism" <https://refactoring.com/catalog/replaceConditionalWithPolymorphism.html>
  - Steve McConnell, 『Code Complete』 2판(2004)의 표 기반 방법(Table-Driven Methods) 장 — 18장 "Table-Driven Methods"(411쪽), Microsoft Press 샘플 PDF 목차로 확인 <https://www.microsoftpressstore.com/content/images/9780735619678/samplepages/9780735619678.pdf>
  - JEP 361 "Switch Expressions"(Java 14, 빠짐없음과 enum의 암묵 default) <https://openjdk.org/jeps/361> · JEP 441 "Pattern Matching for switch"(Java 21) <https://openjdk.org/jeps/441>
  - PMD 7.17.0 Java design 규칙 문서(CyclomaticComplexity 기본 메서드 10·클래스 80, CognitiveComplexity 기본 15) <https://docs.pmd-code.org/pmd-doc-7.17.0/pmd_rules_java_design.html> · SonarSource "Cognitive Complexity" 백서 <https://www.sonarsource.com/docs/CognitiveComplexity.pdf>
- 실험 목록 (코드: scratchpad `sd/25/e28/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`)
  - A `pmd/IfLadder.java`·`Table.java`·`Check.java`·`ruleset.xml` — 16 조합 결과 일치, PLATINUM 처리, PMD 7.17.0 복잡도(임계 1과 기본)
  - B `dup/v1`·`v2`·`v2b`·`v2c`·`v3` — 복제 `switch` + default 누락, `switch` 식 컴파일 오류(한 번에 하나, `-XDshould-stop.ifError=GENERATE`로 둘), enum 한 곳 집중
