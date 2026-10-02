# software-design/10-code-smells — 코드 스멜 카탈로그와 다섯 묶음 — 정리 (힌트)

## 해결하는 문제

리팩터링은 "어떻게"는 배우기 쉽지만 "언제"가 어렵다.\
스멜은 그 "언제"를 알려 주는 **눈에 띄는 표면 신호**의 목록이다. 이름이 붙어 있어 팀이 같은 말로 부를 수 있다.

```text
 스멜 없이                                   스멜 카탈로그로
 "이 코드 좀 별로인데…"                        "Shotgun Surgery네요. 통화 표기 하나에 4파일"
   │ 무엇이 왜 별로인지 말 못 함                   │ 이름 → 원인 → 처방(리팩터링)이 이어진다
   └─ 방치 → 변경마다 회귀 버그                    └─ "Move Function으로 한 곳에 모으자"
```

- *코드 스멜(code smell)*: 대개 더 깊은 문제와 대응하는 표면 신호. Kent Beck이 Fowler의 『Refactoring』을 도우며 만든 말이다(Fowler bliki "CodeSmell", 2006-02-09).
- 스멜은 **문제 그 자체가 아니라 지표**다. 긴 메서드라도 괜찮은 것이 있다. 깊이 들여다보고 판단한다(같은 글).

쉬운 예: 냉장고에서 냄새가 나면 바로 어느 반찬이 상했는지는 모른다. 하지만 열어 볼 이유는 생긴다.\
똑같은 구조다.\
실무 예: "결제 수단 추가할 때마다 enum·switch 네 곳을 고친다"(Repeated Switches + Shotgun Surgery), "OrderService는 세금·통화 표기·메일 문구가 바뀔 때마다 고친다"(Divergent Change).

선행 [06-clean-code](../06-clean-code/2-summary.md)의 다섯 속성이 깨진 모양이 스멜이다. 처방(리팩터링 절차)은 13 refactoring에서 다룬다.

## 동작·원리

### 1. Fowler 2판 3장의 스멜 24개

2판(2018) 3장 "Bad Smells in Code"의 절 순서(Pearson 목차 확인):

```text
 Mysterious Name · Duplicated Code · Long Function · Long Parameter List · Global Data · Mutable Data
 Divergent Change · Shotgun Surgery · Feature Envy · Data Clumps · Primitive Obsession · Repeated Switches
 Loops · Lazy Element · Speculative Generality · Temporary Field · Message Chains · Middle Man
 Insider Trading · Large Class · Alternative Classes with Different Interfaces · Data Class
 Refused Bequest · Comments
```

1판(1999, Beck·Fowler 공저 장)의 22개(Pearson 샘플 목차)와 비교하면:

| 변화 | 스멜 |
|---|---|
| 2판에 추가 | Mysterious Name, Global Data, Mutable Data, Loops |
| 2판에서 빠짐 | Parallel Inheritance Hierarchies, Incomplete Library Class |
| 이름 바뀜 | Long Method → Long Function, Switch Statements → Repeated Switches, Lazy Class → Lazy Element, Inappropriate Intimacy → Insider Trading |

- 1판 3장 첫머리: 언제 리팩터링이 늦었는지 정확한 기준을 주지 않겠다고 한다. "In our experience no set of metrics rivals informed human intuition."
- *Repeated Switches*: 1판의 Switch Statements를 바꾼 이름. switch 하나가 아니라 **같은 분기가 여러 곳에 반복**되는 것이 신호라는 뜻이 이름에 들어갔다(분기 다루는 법은 28 taming-conditionals).

### 2. 다섯 묶음 — Mäntylä 분류

긴 목록을 한눈에 보려고 Mäntylä가 묶었다. 그의 웹 페이지(인용 논문: Mäntylä·Lassenius, Empirical Software Engineering 11(3), 2006)의 다섯 묶음이다. 1판 이름 기준이다.

```text
 Bloaters (너무 커져서 다루기 힘듦)          Long Method · Large Class · Primitive Obsession · Long Parameter List · Data Clumps
 OO Abusers (객체지향을 덜 씀)              Switch Statements · Temporary Field · Refused Bequest · Alternative Classes with Different Interfaces
 Change Preventers (바꾸기를 막음)          Divergent Change · Shotgun Surgery · Parallel Inheritance Hierarchies
 Dispensables (없어도 되는 것)              Lazy Class · Data Class · Duplicate Code · Dead Code · Speculative Generality
 Couplers (결합이 과함)                    Feature Envy · Inappropriate Intimacy · Message Chains · Middle Man
```

- 2003년 ICSM 논문(Mäntylä·Vanhanen·Lassenius)의 첫 분류에는 Encapsulators·Others 묶음이 더 있었다. 2006년 판에서 이를 없애고 Message Chains·Middle Man을 Couplers로, Parallel Inheritance Hierarchies를 Change Preventers로 옮겼다(2차 자료 dev.to 정리로 확인, 2003 논문 원문 미열람 [?]).
- Dead Code는 Mäntylä 목록에는 있고 Fowler 1·2판 3장 절 목록에는 없다. 2판 카탈로그에는 리팩터링 "Remove Dead Code"가 있다(refactoring.com).
- 06 CLEAN과 대응: Bloaters·OO Abusers ↔ C(응집), Change Preventers·Couplers ↔ L(결합), Data Class·Insider Trading ↔ E·A, Duplicated Code ↔ N.

### 3. 변경 축 스멜 둘 — Divergent Change와 Shotgun Surgery

```text
 Divergent Change: 한 클래스가 여러 이유로 바뀐다       Shotgun Surgery: 한 이유가 여러 클래스를 바꾼다
   세금 변경 ──┐                                      통화 표기 변경 ──┬─> OrderService
   통화 변경 ──┼──> OrderService                                     ├─> InvoicePrinter
   메일 변경 ──┘                                                     ├─> ReceiptMailer
                                                                     └─> AdminReport
          목표: 변경 이유 하나 ↔ 클래스 하나 (일대일)
```

- 1판 원문: "Divergent change is one class that suffers many kinds of changes, and shotgun surgery is one change that alters many classes." 이상적으로는 흔한 변경과 클래스가 **일대일**이 되게 한다.
- Shotgun Surgery의 위험은 1판 표현으로 "it's easy to miss an important change"다. 06·07 실험의 "사본 하나를 놓친 조용한 버그"가 바로 이 경로였다.
- 처방(1판): Divergent는 Extract Class, Shotgun은 Move Method·Move Field로 한 클래스에 모은다(2판 이름: Move Function 등).

### 4. 몇 가지 스멜의 정의 (1판 3장 원문 기준)

- *Feature Envy*: 자기 클래스보다 다른 클래스에 더 관심 있는 메서드. 다른 객체의 getter를 여러 번 불러 값을 계산한다. 처방은 Move Method. 다만 Strategy·Visitor처럼 일부러 이 규칙을 깨는 패턴도 있다. 기준은 "함께 바뀌는 것을 함께 둔다".
- *Speculative Generality*: Brian Foote가 붙인 이름. "언젠가 필요할 것"이라며 만든 훅·특수 경우. 쓰이면 값어치가 있지만 안 쓰이면 방해만 된다. **유일한 사용처가 테스트**면 이 스멜이다. 처방: Collapse Hierarchy, Inline Class, Remove Parameter.
- *Comments*: 주석은 나쁜 냄새가 아니라 좋은 냄새다. 다만 나쁜 코드를 덮는 **탈취제(deodorant)**로 쓰이곤 한다. "A comment is a good place to say why you did something."(→ [09-comments-and-conventions](../09-comments-and-conventions/2-summary.md))
- *Message Chains*: `a.getB().getC().getD()`처럼 객체를 줄줄이 타고 들어간다. 호출자가 중간 구조 전부에 결합된다(Mäntylä 설명).
- *Middle Man*: 결합을 피하려고 위임만 하는 클래스. 결합을 줄이려는 시도가 만드는 스멜이다(Mäntylä 설명).

### 실험 A: git 이력으로 Shotgun Surgery·Divergent Change 재기

같은 요구 3건(R1 통화 표기 "1,000원" → "₩1,000", R2 세율 상수화, R3 메일 제목에 주문번호)을 두 설계에 차례로 커밋했다.\
smelly: `OrderService`가 합계·세금·통화 표기·메일 문구를 다 갖고, 통화 표기 `String.format("%,d원", …)`이 네 클래스에 있다.\
tidy: `Money.format`·`TaxPolicy`·`OrderMail`이 각각 한 가지 이유만 갖는다.

(실험, JDK 21.0.12 temurin `--cpus=2`, git 2.43.0, 2026-10-02, `scratchpad/sd/06/e10/run-history.sh`)

```text
== [smelly] 요구별로 바뀐 파일 수 (Shotgun Surgery 지표)
  R1 format: 통화 표기 ₩ -> 4개 파일
  R2 tax: 세율 상수화 -> 1개 파일
  R3 mail: 제목에 주문번호 -> 1개 파일
== [smelly] 파일별로 바뀐 이유 수 (Divergent Change 지표)
        3 src/OrderService.java
        1 src/ReceiptMailer.java
        1 src/InvoicePrinter.java
        1 src/AdminReport.java
  [주문 완료] o-7 / 합계 ₩3,300
  10/02,₩3,300
  커피 ₩4,500
== [tidy] 요구별로 바뀐 파일 수 (Shotgun Surgery 지표)
  R1 format: 통화 표기 ₩ -> 1개 파일
  R2 tax: 세율 상수화 -> 1개 파일
  R3 mail: 제목에 주문번호 -> 1개 파일
== [tidy] 파일별로 바뀐 이유 수 (Divergent Change 지표)
        1 src/TaxPolicy.java
        1 src/OrderMail.java
        1 src/Money.java
  [주문 완료] o-7 / 합계 ₩3,300
  10/02,₩3,300
  커피 ₩4,500
```

- 관찰 1 — smelly에서 통화 표기 하나가 4파일을 바꿨다(Shotgun Surgery). tidy는 1파일.
- 관찰 2 — smelly의 `OrderService`는 세 요구 모두에서 바뀌었다(이유 3개, Divergent Change). tidy는 파일마다 이유 1개 — 1판이 말한 "일대일"이다.
- 관찰 3 — 동작 결과는 두 설계가 같다. 스멜은 실행 결과가 아니라 **변경 이력**에서 보인다.
- 반대쪽 비용 — tidy는 파일이 3개 많다(src 8 vs 5, `Main` 포함). `OrderMail`은 한 줄짜리 메서드 하나뿐이라 그 자체가 *Lazy Element* 후보다. 메일 문구가 독립적으로 자주 바뀐다는 근거가 있을 때만 정당하다. 그런 근거가 없으면 smelly 쪽이 더 단순하다(12 simple-design-and-yagni).
- 실무에서는 이 두 명령(`git log --numstat`, `git log --name-only | sort | uniq -c`)을 실제 저장소 수백 커밋에 돌린다. 커밋 메시지에 변경 이유가 있어야 이유 수를 셀 수 있다(53 code-forensics-hotspots).

### 실험 B: 정적 분석 도구는 카탈로그 중 무엇을 잡나

한 파일 묶음에 스멜 여덟 가지를 일부러 심고 PMD 7.28.0 규칙 아홉 개(기본 임계)와 CPD를 돌렸다.\
심은 것: Data Class, Global/Mutable Data(공개 정적 가변 리스트), Long Parameter List(11개), Dead Code(안 쓰는 private 메서드), Feature Envy(`Shipment` getter만 쓰는 메서드), Repeated Switches(같은 `zone` switch 둘), Message Chains(`s.getCustomer().getAddress().getCity()`), Speculative Generality(쓰지 않는 매개변수가 많은 package-private 메서드).

(실험, PMD 7.28.0, 같은 환경, `scratchpad/sd/06/e10/run-catalog.sh`)

```text
Shipment.java:1:	DataClass:	The class 'Shipment' is suspected to be a Data Class (WOC=0.000%, NOPA=5, NOAM=5, WMC=5)
ShippingService.java:6:	MutableStaticState:	Do not use non-final non-private static fields
ShippingService.java:9:	ExcessiveParameterList:	Avoid long parameter lists (11 parameters - threshold is 10).
ShippingService.java:38:	UnusedPrivateMethod:	Avoid unused private methods such as 'legacyFee(int)'.
[INFO] Found 4 violations.
-- CPD --minimum-tokens 20
```

- 잡힌 것(4): Data Class, Mutable/Global Data, Long Parameter List, Dead Code. 모두 **한 파일 안의 구조**로 판정되는 스멜이다.
- 못 잡은 것: Feature Envy, Repeated Switches(두 switch의 글자가 달라 CPD도 무반응), Message Chains(`LawOfDemeter` 규칙을 켰지만 이 체인은 보고되지 않았다. 단독 실행에서도 "Found no violations". 원인은 타입 정보 부족이다 — 아래 재실행), Speculative Generality(`UnusedFormalParameter`는 기본으로 private 메서드만 본다. 다른 메서드까지 보려면 `checkAll=true` — PMD 문서).
- 재실행 — 같은 소스를 `javac`로 컴파일해 `--aux-classpath`로 넘기면 `LawOfDemeter`가 체인을 보고해 5건이 된다. 이 규칙은 타입 정보(어느 메서드가 getter인가)가 있어야 동작한다.

(실험, PMD 7.28.0 + `--aux-classpath`, JDK 21.0.12 temurin, `--cpus=2`, 2026-10-02, `scratchpad/sd/adj-09/out-cat-auxcp.txt`)

```text
ShippingService.java:32:	LawOfDemeter:	Call to `getCustomer` on foreign value `s` (degree 1)
[INFO] Found 5 violations.
```

- Shotgun Surgery·Divergent Change는 소스 한 시점이 아니라 **변경 이력**의 성질이라 정적 분석 대상이 아니다(실험 A처럼 git으로 본다).
- 해석 — 1판의 말처럼 지표가 판단을 대신하지 못한다. 도구는 "열어 볼 후보"를 주고, 판정은 사람이 "이 둘은 함께 바뀌나?"로 한다.

## 쓰이는 자료구조·알고리즘

- **변경 이력 = 커밋 × 파일 이분 그래프**: 커밋 하나와 그것이 바꾼 파일들을 잇는다. 커밋 쪽 차수(한 커밋이 바꾼 파일 수)가 크면 Shotgun Surgery, 파일 쪽 차수(한 파일을 바꾼 서로 다른 이유 수)가 크면 Divergent Change다. 함께 바뀐 파일 쌍을 세면 change coupling(53).
- **AST 패턴 매칭과 지표 조합**: PMD는 소스를 AST로 바꾸고 규칙마다 XPath나 Java 방문자로 패턴을 찾는다. `DataClass`·`GodClass`는 지표(WMC·WOC·NOPA·NOAM, WMC·ATFD·TCC)의 조합으로 판정한다(PMD 문서, Lanza–Marinescu 『Object-Oriented Metrics in Practice』의 탐지 전략).
- **토큰 열 매칭(CPD)**: Duplicated Code 후보. 글자가 다른 같은 지식은 못 찾는다(06 실험 C).
- **분류 트리**: 스멜 24개를 다섯 묶음으로 묶는 것은 카탈로그를 "변경 이유별"로 색인하는 트리다. 증상 → 묶음 → 스멜 → 리팩터링 순으로 찾는다.

## 적용 — 풀어나가는 법

### 1. 스멜을 찾는 순서

1. **변경 이력부터**: 최근 N개월 커밋에서 "한 요구에 파일 여러 개"(Shotgun)와 "여러 이유로 자주 바뀌는 파일"(Divergent)을 뽑는다. 변경 비용이 실제로 드는 곳이다.
2. 그 파일들에 정적 분석을 돌려 Bloaters·Dispensables 후보를 얻는다.
3. 리뷰 검사표로 도구가 못 보는 스멜을 본다: Feature Envy(다른 객체 getter를 여러 번?), Repeated Switches(같은 분기가 또 있나?), Message Chains, Speculative Generality(사용처가 테스트뿐인가?).
4. 스멜마다 처방 리팩터링을 정하고, 변경할 때 그 자리부터 정리한다(14 tidy-first). 스멜이 있다고 바로 고치지 않는다 — 그 코드를 바꿀 일이 있을 때가 비용 대비 효과가 크다.

### 2. 스멜 → 처방 (Fowler 카탈로그 이름)

| 스멜 | 처방 |
|---|---|
| Shotgun Surgery | Move Function·Move Field, Combine Functions into Class, Inline Class |
| Divergent Change | Extract Class, Split Phase, Move Function |
| Feature Envy | Move Function (일부만이면 Extract Function 후 이동) |
| Repeated Switches | Replace Conditional with Polymorphism (29) |
| Long Parameter List · Data Clumps | Introduce Parameter Object, Preserve Whole Object |
| Speculative Generality | Collapse Hierarchy, Inline Function·Class, Remove Dead Code |
| Message Chains | Hide Delegate, Extract Function + Move Function |
| Mysterious Name | Rename (07) |

- 처방 이름은 refactoring.com 카탈로그 기준이다. 1판 원문은 Move Method·Extract Method 같은 1판 이름을 쓴다.

### 3. 진단 명령

```bash
# Shotgun Surgery 후보: 커밋당 바뀐 파일 수 상위 (머지 커밋 제외)
git log --no-merges --since=6.months --format='@%h %s' --name-only \
  | awk '/^@/{if(c)print n, c; c=$0; n=0; next} NF{n++} END{print n, c}' | sort -rn | head

# Divergent Change 후보: 파일별 변경 커밋 수 상위
git log --no-merges --since=6.months --format='' --name-only | sort | uniq -c | sort -rn | head

# 한 파일 안 구조 스멜 (PMD 7.x 기본 임계)
pmd check -d src/main/java --aux-classpath target/classes -R category/java/design.xml/DataClass,category/java/design.xml/GodClass,category/java/design.xml/ExcessiveParameterList,category/java/design.xml/MutableStaticState,category/java/bestpractices.xml/UnusedPrivateMethod
```

```java
// Feature Envy → Move Function
// 전: ShippingService가 Shipment의 데이터만 쓴다
long feeOf(Shipment s) { return base(s.getZone()) + s.getWeightGrams() / 1000 * perKg(s.getZone()); }
// 후: 데이터 곁으로
class Shipment { long fee() { return zone.baseFee() + weightGrams / 1000 * zone.perKgFee(); } }
```

## 장애 시나리오와 대처

### 1. 스멜 방치 → 변경마다 회귀 버그 (⚠ 커리큘럼)

- 현상: 통화 표기를 바꿀 때마다 어느 화면 하나는 옛 표기로 남는다. 매번 다른 화면이다.
- 보이는 형태: 같은 금액이 화면마다 "1,000원"과 "₩1,000"으로 섞인다. 버그 티켓이 "표기 불일치"로 반복된다.
- 원인: Shotgun Surgery. 같은 지식(통화 표기)이 네 클래스에 있다(실험 A smelly R1 → 4개 파일). 사본이 늘수록 놓칠 확률이 커진다.
- 대처: Move Function으로 `Money.format` 한 곳에 모은다(실험 A tidy R1 → 1개 파일). 이후 같은 요구는 1파일이다.

### 2. 한 클래스가 여러 이유의 변경을 다 받음 → 병합 충돌·무관한 회귀

- 현상: 세금 변경 PR과 메일 문구 변경 PR이 같은 파일에서 충돌한다. 메일 변경 배포 뒤 세금 계산 테스트가 깨진다.
- 보이는 형태: `git log --name-only` 상위 1위 파일이 기능 커밋 대부분에 등장(실험 A smelly `OrderService` 이유 3개).
- 원인: Divergent Change. 서로 다른 이유가 한 클래스에 산다.
- 대처: 변경 이유별로 Extract Class. 나눈 뒤 파일별 이유 수가 1에 가까워졌는지 이력으로 확인한다.

### 3. 쓰이지 않는 일반화 → 읽기·변경 비용만 늘어남

- 현상: 확장점(추상 클래스·플러그인 인터페이스·옵션 매개변수)을 고치려는데 구현이 하나뿐이고 사용처는 테스트뿐이다.
- 보이는 형태: "이 매개변수 어디서 쓰나요?"에 답이 없다. 새 기능 추가 때 쓰이지 않는 훅까지 맞춰 고친다.
- 원인: Speculative Generality — "언젠가 필요할 것" 기준으로 만들었다. 도구도 못 잡았다(실험 B, package-private 메서드의 미사용 매개변수).
- 대처: Collapse Hierarchy·Inline·Remove Parameter. 확장점은 두 번째 요구가 올 때 만든다(12).

### 4. 도구 경고 0건을 "스멜 없음"으로 오해

- 현상: CI의 PMD가 깨끗한데 변경 비용은 계속 높다.
- 보이는 형태: 정적 분석 0건, 그런데 기능 하나에 파일 5~6개 수정이 일상.
- 원인: 변경 축 스멜(Shotgun·Divergent)은 소스 한 시점에 없다. Feature Envy·Repeated Switches는 이번에 돌린 PMD 규칙이 보지 않는다(실험 B: 심은 8개 중 4개만 보고). JDeodorant 같은 별도 도구는 Feature Envy·Type Checking 탐지를 내세운다.
- 대처: 이력 기반 지표(실험 A 명령)를 주기적으로 본다. 리뷰 검사표에 도구 밖 스멜을 넣는다.

### 5. 결합을 피하려다 생긴 위임 껍데기

- 현상: 호출 경로를 따라가면 위임만 하는 클래스를 서너 개 지난다.
- 보이는 형태: 스택 트레이스가 깊다. 기능 하나 바꾸는데 위임 메서드 시그니처를 층마다 고친다.
- 원인: Middle Man — 결합을 줄이려는 위임이 과했다(Mäntylä 설명). APOSD의 Pass-Through Method와 같은 모양이다.
- 대처: Remove Middle Man·Inline Function. 03 deep-modules-and-abstraction의 "통과 메서드"를 함께 본다.

## 핵심 문장

- 스멜은 문제 자체가 아니라 더 깊은 문제를 가리키는 표면 신호다. 깊이 보고 판단한다.
- Fowler 2판 3장은 스멜 24개를 둔다. 1판 22개에서 넷을 더하고 둘을 빼고 넷의 이름을 바꿨다.
- Mäntylä는 이를 Bloaters·OO Abusers·Change Preventers·Dispensables·Couplers 다섯 묶음으로 묶었다.
- Divergent Change는 한 클래스가 여러 이유로, Shotgun Surgery는 한 이유가 여러 클래스를 바꾼다. 목표는 변경 이유와 클래스의 일대일이다. 실험에서 통화 표기 하나가 smelly는 4파일, tidy는 1파일을 바꿨다.
- 이번 실험의 PMD 규칙은 심은 8개 중 4개(타입 정보를 주면 5개)만 잡았다. 파일 간 복붙은 CPD가 잡지만(06 실험 C), 변경 축 스멜은 소스 한 시점에 없어 git 이력으로 본다.

## 관련 주제·근거

- 선행
  - [06-clean-code](../06-clean-code/2-summary.md) — 스멜은 CLEAN 속성이 깨진 모양
- 후속·연결
  - [07-naming](../07-naming/2-summary.md) — Mysterious Name · [08-function-design](../08-function-design/2-summary.md) — Long Function·Long Parameter List · [09-comments-and-conventions](../09-comments-and-conventions/2-summary.md) — Comments
  - [11-when-to-abstract](../11-when-to-abstract/2-summary.md) · [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md) · [13-refactoring](../13-refactoring/2-summary.md) · [14-tidy-first](../14-tidy-first/2-summary.md) · [28-taming-conditionals](../28-taming-conditionals/2-summary.md) · [29-refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md) · [31-antipatterns](../31-antipatterns/2-summary.md) · [52-complexity-metrics](../52-complexity-metrics/2-summary.md) · [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md)
- 글·문서
  - Martin Fowler, 『Refactoring』 2판(Addison-Wesley, 2018) 3장 "Bad Smells in Code" — 절 목록은 Pearson 목차 PDF로 확인, 본문 미열람 <https://www.pearson.de/media/muster/toc/toc_9780134757698.pdf>
  - Martin Fowler·Kent Beck, 『Refactoring』 1판(1999) 3장 — Pearson 샘플 PDF로 목차와 본문 일부(Divergent Change·Shotgun Surgery·Feature Envy·Speculative Generality·Comments) 확인 <https://ptgmedia.pearsoncmg.com/images/9780201485677/samplepages/9780201485677.pdf>
  - Martin Fowler, "CodeSmell"(2006-02-09) <https://martinfowler.com/bliki/CodeSmell.html> · refactoring.com 카탈로그 <https://refactoring.com/catalog/>
  - JDeodorant README — 탐지 대상 Feature Envy·Type/State Checking·Long Method·God Class·Duplicated Code <https://github.com/tsantalis/JDeodorant>
  - Mika Mäntylä, "A Taxonomy for 'Bad Code Smells'" — 다섯 묶음과 설명, 인용 논문 Mäntylä·Lassenius 2006(Empirical Software Engineering 11(3)) <https://mmantyla.github.io/BadCodeSmellsTaxonomy>
  - Mäntylä·Vanhanen·Lassenius, "A Taxonomy and an Initial Empirical Study of Bad Smells in Code", ICSM 2003 — 원문 미열람, 2003→2006 변경은 2차 정리로 확인 [?] <https://dev.to/trikitrok/de-taxonomias-y-catalogos-de-code-smells-356g>
  - PMD 7.28.0 규칙 문서(DataClass·GodClass 탐지 전략, ExcessiveParameterList 기본 10, MutableStaticState, UnusedPrivateMethod) <https://docs.pmd-code.org/pmd-doc-7.28.0/pmd_rules_java_design.html>
- 실험 목록 (코드: scratchpad `sd/06/e10/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, git 2.43.0, PMD 7.28.0)
  - A 요구 3건 × 두 설계, git 이력으로 Shotgun·Divergent 지표 — `run-history.sh`
  - B 스멜 8종을 심은 코드에 PMD 규칙 9개 + CPD — `run-catalog.sh` (4건 보고). 판정 재실행: 컴파일 클래스를 `--aux-classpath`로 주면 `LawOfDemeter` 포함 5건 — `scratchpad/sd/adj-09/` (JDK 21.0.12, PMD 7.28.0)
