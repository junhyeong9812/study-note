# software-design/08-function-design — 함수 설계: 한 추상화 수준·인자·CQS·가드 절 — 정리 (힌트)

## 해결하는 문제

함수는 호출하는 쪽에서 **시그니처만 보고** 쓰는 단위다.\
시그니처가 거짓말을 하면(조회처럼 보이는데 상태를 바꿈, 인자 순서가 뜻을 숨김), 호출자는 본문을 열어 보거나 틀리게 쓴다.

```text
 save(order, true, false, null)        getBalance()
   │                                     │
   ├─ true가 뭐지? false는?               ├─ 조회인 줄 알고 로그에 한 번 더 부름
   └─ 순서를 바꿔 써도 컴파일된다           └─ 그런데 캐시를 갱신하는 명령이었다
      → 알림이 엉뚱하게 나간다                 → 로그 한 줄이 수수료를 바꾼다 (실험 A)
```

- *시그니처(signature)*: 함수 이름, 인자 목록(타입·순서), 반환 타입.
- *추상화 수준(level of abstraction)*: 같은 함수 안 코드가 다루는 세부의 높이. "주문 보고서를 만든다"와 "SQL에 `AND status = 'PAID'`를 붙인다"는 높이가 다르다.

쉬운 예: 리모컨 버튼 "볼륨 확인"을 눌렀는데 볼륨이 한 칸 올라간다. 두 번 확인하면 두 칸 올라간다.\
똑같은 구조다.\
실무 예: `getBalance()`가 "읽는 김에" 캐시를 갱신한다. 누군가 디버그 로그에 `getBalance()`를 하나 더 넣자 수수료 면제 판정이 바뀐다.

이 주제는 [06-clean-code](../06-clean-code/2-summary.md)에서 나눴고, 이름은 [07-naming](../07-naming/2-summary.md)에서 다뤘다. 이 노트는 그 이름이 붙는 단위인 함수의 모양을 다룬다.

## 동작·원리

### 1. 한 함수 = 한 추상화 수준 (SLAP)

```text
 섞인 함수 report()                       나눈 함수
 ┌─────────────────────────────┐        report()  ── 보고서 = 쿼리 + 줄들
 │ SQL 문자열 조립 (저수준)       │          ├─ OrderQuery.sql()       SQL 조립
 │ 등급별 할인 정책 (도메인)      │          ├─ DiscountPolicy.discountOf()  할인 정책
 │ CSV 한 줄 형식 (표현)          │          └─ line()                 출력 형식
 └─────────────────────────────┘
  정책을 고치려면 SQL 옆을 만진다            정책 변경은 discountOf()만 만진다
```

- *SLAP(Single Level of Abstraction Principle)*: 한 함수 안의 문장은 같은 추상화 수준에 둔다. Neal Ford가 『The Productive Programmer』에서 이름 붙였고, 뿌리는 Kent Beck의 Composed Method라고 알려져 있다(2차 자료로만 확인 [?]).
- 수준을 맞추면 상위 함수는 "무엇을"만, 하위 함수는 "어떻게"를 말한다. Fowler bliki "FunctionLength"(2016-11-30)의 기준도 같다: 길이가 아니라 **의도와 구현의 분리**. 코드 조각이 무엇을 하는지 알아내는 데 노력이 들면 함수로 뽑고 그 "무엇"으로 이름 붙인다.

### 2. 인자 — 수, 순서, 플래그

```text
 save(Order, boolean, boolean, String)       같은 타입 인자가 나란히 → 순서 실수가 컴파일된다
 save(Order, Notification, Audit)            인자마다 다른 타입    → 순서 실수가 컴파일 오류
 notifyAndSave(order) / saveQuietly(order)   동작마다 이름          → 플래그 자체가 없다
 save(order, SaveOptions)                    인자 객체              → 이름 붙은 필드
```

- *플래그 인자(flag argument)*: 값에 따라 함수가 다른 일을 하게 만드는 인자. Fowler bliki "FlagArgument"(2011-06-23): `book(martin, false)`보다 `regularBook(martin)`이 의도를 바로 전한다. 플래그가 본문 여러 곳에 얽혀 있으면 플래그 함수를 숨기고 이름 붙은 함수 둘을 공개하는 방법을 제시한다.
- *인자 객체(parameter object)*: 함께 다니는 인자 묶음을 한 타입으로 만든 것. Fowler 카탈로그 "Introduce Parameter Object".
- 인자 수 기준은 출처마다 다르다. PMD `ExcessiveParameterList`의 기본 임계는 10이다(PMD 7.28.0 문서). Martin 『Clean Code』 3장은 더 적은 수를 권한다고 알려져 있다(본문 미열람 [?]).

### 3. CQS — 명령과 질의를 나눈다

```text
 질의(query)    값을 돌려준다, 관찰 가능한 상태를 바꾸지 않는다   → 몇 번 불러도, 순서를 바꿔도 안전
 명령(command)  상태를 바꾼다, 값을 돌려주지 않는다             → 부르는 횟수·순서가 결과를 바꾼다

 getBalance() { v = cached; cached = ledger; return v; }   ← 둘을 섞었다
   1회: 10,000   2회: 10,100                               (실험 A)
```

- *CQS(Command Query Separation)*: Bertrand Meyer가 『Object-Oriented Software Construction』에서 만든 용어(Fowler bliki "CommandQuerySeparation", 2005-12-05).
- Fowler의 단서: Meyer는 CQS를 예외 없이 적용하길 좋아하지만, 스택의 `pop`처럼 상태를 바꾸는 질의가 유용한 관용구도 있다. Fowler는 Java `Iterator.next()`(값을 주면서 전진)도 예로 들며, 자신은 `advance`·`current`를 나누는 쪽을 선호한다고 쓴다.
- 위험은 **이름이 질의인데 명령인 경우**다. `isX`·`getX`·`hasX`를 보고 호출자는 부작용이 없다고 믿는다. Ousterhout는 Martin과의 대담에서 `isMultipleOfNthPrimeFactor`가 이름은 술어인데 부작용이 있어 읽는 사람을 속인다고 지적했고, Martin도 그 부작용이 마음에 들지 않는다고 답했다(aposd-vs-clean-code 대담, 2024-09~2025-02).
- *출력 인자(output argument)*: 결과를 반환값 대신 인자 객체를 바꿔서 전하는 것(`fill(list)`). 호출자가 인자가 바뀐다는 것을 시그니처에서 알 수 없다. 반환값으로 돌려준다.

### 4. 가드 절 — 예외 경로를 앞에서 끝낸다

```text
 중첩 조건                               가드 절
 if (order != null) {                    if (order == null) return REJECT;
   if (order.isPaid()) {                 if (!order.isPaid()) return REJECT;
     if (!order.isShipped()) {           if (order.isShipped()) return ALREADY;
       ship(order);                      ship(order);
     } ...                               return OK;
```

- *가드 절(guard clause)*: 함수 앞에서 특수한 경우를 바로 반환해, 정상 경로를 들여쓰기 없이 남기는 조건문. Fowler 카탈로그 "Replace Nested Conditional with Guard Clauses".
- 정상 경로가 왼쪽 끝 한 줄기로 읽힌다. 인지 복잡도는 중첩에 가중치를 주므로 가드 절로 줄어든다(SonarSource 「Cognitive Complexity」 백서 1.7판(2023-08-29): 흐름 단절마다 +1, 중첩된 흐름 단절에 추가 증가. 52 complexity-metrics에서 자세히).

### 5. 길이보다 깊이 — 두 입장

- Martin(『Clean Code』 1판, APOSD 2판 9.8에 인용): "The first rule of functions is that they should be small. The second rule of functions is that they should be smaller than that."
- Ousterhout(APOSD 2판 9.8 "A different opinion: Clean Code"): 함수가 몇십 줄 수준이 되면 더 줄여도 가독성 이득이 적다. 너무 잘게 나누면 독립성을 잃고 함께 읽어야만 이해되는 *conjoined functions*가 된다(9.8 본문 표현. 「Summary of Red Flags」에는 같은 뜻의 "Conjoined Methods"가 있다). "Depth is more important than length."
- 두 사람의 합의와 이견(대담 요약): 둘 다 분해와 얽힘 회피를 중시한다. 차이는 그 둘의 가중치다. Ousterhout는 "One Thing" 규칙에 과분해를 막는 장치가 없다고 보고, Martin은 판단(judgment)으로 적용한다고 본다.
- 실무 판정 기준: 나눈 함수를 **호출자가 본문을 열지 않고** 쓸 수 있나? 열어야 한다면 나눈 것이 얕다([03-deep-modules-and-abstraction](../03-deep-modules-and-abstraction/2-summary.md)).

### 실험 A: 질의처럼 보이는 명령 — 로그 한 줄이 수수료를 바꾼다

원장에는 입금 100원이 반영돼 10,100원, 계좌 객체 캐시는 옛값 10,000원이다. 잔액이 10,050원을 넘으면 수수료 500원을 면제한다.

```java
public long getBalance() {            // 이름은 질의
    long value = cached;
    cached = ledgerBalance;           // "읽는 김에 캐시도 새로 고쳐 두자" — 명령
    auditLog.add("balance read");
    return value;
}
// CQS로 나눈 쪽
public void refresh() { cached = ledgerBalance; }   // 명령
public long balance() { return cached; }             // 질의
```

(실험, JDK 21.0.12 temurin `--cpus=2`, 2026-10-02, `scratchpad/sd/06/e08/run-cqs.sh`)

```text
1회 getBalance() = 10000
2회 getBalance() = 10100
디버그 로그 끔: fee = 500, auditLog 1건
  [debug] balance=10000
디버그 로그 켬: fee = 0, auditLog 2건
CQS 분리, 로그 끔: fee = 0
  [debug] balance=10100
CQS 분리, 로그 켬: fee = 0
```

- 관찰 1 — 같은 질의를 두 번 부르니 값이 달랐다(10,000 → 10,100).
- 관찰 2 — 디버그 로그 한 줄을 켜자 수수료가 500원에서 0원으로 바뀌었다. 감사 로그 건수도 1건에서 2건으로 늘었다.
- 관찰 3 — CQS로 나누자 로그를 켜든 끄든 수수료가 같았다. 갱신(명령)이 한 번, 명시적인 자리에서 일어난다.
- 해석 — 로그·디버거·`toString()`·모니터링 수집기는 질의를 마음대로 부른다. 질의에 부작용이 있으면 관측 행위가 결과를 바꾼다.

### 실험 B: 플래그 인자 순서 실수 — 컴파일러가 잡나

의도: "감사 로그만 남기고 알림은 보내지 않는다." 작성자는 인자 순서를 (audit, notify)로 기억했다.

```java
// bad: save(Order order, boolean notify, boolean audit, String memo)
save(new Order("o-1"), true, false, null);
// good: save(Order order, Notification notification, Audit audit) — enum 두 개
save(new Order("o-1"), Audit.WRITE, Notification.SKIP);
```

(실험, 같은 환경, `scratchpad/sd/06/e08/run-flags.sh`)

```text
== [bad] javac + java
  saved o-1 +알림발송
  (exit 0)
== [good] javac + java
Flags.java:12: error: incompatible types: Audit cannot be converted to Notification
        save(new Order("o-1"), Audit.WRITE, Notification.SKIP);
                                    ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
  (exit 1)
```

- boolean 둘은 순서가 바뀌어도 컴파일된다. 결과: 알림이 나가고 감사 로그는 없다(의도의 정반대).
- 인자마다 다른 타입이면 같은 실수가 **컴파일 오류**가 된다. 실수가 운영이 아니라 빌드에서 멈춘다.
- 더 나아가면 플래그 자체를 없앤다: `saveWithAuditOnly(order)`처럼 동작마다 이름(Fowler "Remove Flag Argument").

### 실험 C: 추상화 수준이 섞인 함수 vs 나눈 함수

같은 동작(SQL 조립 + 등급별 할인 + CSV 줄)을 한 함수와 네 함수로 썼다. 메서드마다 PMD 지표를 출력하려고 임계를 1로 낮췄다.\
(SQL은 실험 단순화로 문자열을 이어 붙였다. 실무에서는 바인드 변수를 쓴다.)

(실험, PMD 7.28.0, 같은 환경, `scratchpad/sd/06/e08/run-slap.sh`)

```text
== [mixed] PMD 7.28.0 (임계 1로 낮춰 모든 메서드 값 출력)
  L7:	CognitiveComplexity:	The method 'report(String, boolean, List<Row>)' has a cognitive complexity of 12
  L7:	CyclomaticComplexity:	The method 'report(String, boolean, List<Row>)' has a cyclomatic complexity of 9.
  L7:	NPathComplexity:	The method 'report(String, boolean, List<Row>)' has an NPath complexity of 36
== [split] PMD 7.28.0 (임계 1로 낮춰 모든 메서드 값 출력)
  L7:	CognitiveComplexity:	The method 'report(String, boolean, List<Row>)' has a cognitive complexity of 1
  L7:	CyclomaticComplexity:	The method 'report(String, boolean, List<Row>)' has a cyclomatic complexity of 2.
  L7:	NPathComplexity:	The method 'report(String, boolean, List<Row>)' has an NPath complexity of 2
  L15:	CyclomaticComplexity:	The method 'line(Row)' has a cyclomatic complexity of 1.
  L15:	NPathComplexity:	The method 'line(Row)' has an NPath complexity of 1
  L25:	CognitiveComplexity:	The method 'sql(String, boolean)' has a cognitive complexity of 3
  L25:	CyclomaticComplexity:	The method 'sql(String, boolean)' has a cyclomatic complexity of 4.
  L25:	NPathComplexity:	The method 'sql(String, boolean)' has an NPath complexity of 6
  L38:	CognitiveComplexity:	The method 'discountOf(String, long)' has a cognitive complexity of 5
  L38:	CyclomaticComplexity:	The method 'discountOf(String, long)' has a cyclomatic complexity of 5.
  L38:	NPathComplexity:	The method 'discountOf(String, long)' has an NPath complexity of 5
== [mixed] 실행 출력
  SELECT customer_id, grade, amount FROM orders WHERE 1=1 AND region = 'seoul' AND status = 'PAID'
  c1,108000
  c2,57000
== [split] 실행 출력
  SELECT customer_id, grade, amount FROM orders WHERE 1=1 AND region = 'seoul' AND status = 'PAID'
  c1,108000
  c2,57000
== [mixed] 정책 변경 diff: 바뀐 줄을 감싼 함수(hunk header)
  @@ -19 +19 @@ static String report(String region, boolean onlyPaid, List<Row> rows) {
== [split] 정책 변경 diff: 바뀐 줄을 감싼 함수(hunk header)
  @@ -40 +40 @@ static long discountOf(String grade, long amount) {
```

- 관찰 1 — 출력은 같다. 섞인 함수의 최댓값(순환 9·인지 12·NPath 36)이 나눈 쪽의 최댓값(순환 5·인지 5·NPath 6)보다 크다.
- 관찰 2 — 순환 복잡도 **합**은 줄지 않았다: mixed 9 vs split 2+1+4+5 = 12. 분해는 복잡도를 없애지 않고 나눠 담는다. 이득은 한 번에 머리에 올릴 양이 줄고, 나눈 조각에 이름이 붙는 데서 온다.
- 관찰 3 — "VIP 기준 10만 → 8만" 변경이 mixed에서는 SQL 조립과 같은 함수(`report`) 안을, split에서는 `discountOf`만 건드렸다. mixed에서 정책을 고치는 사람은 SQL 코드 옆에서 작업한다.
- PMD 7.28.0 기본 임계로는 mixed도 보고되지 않는다(순환 ≥ 10, 인지 ≥ 15, NPath ≥ 200 — 문서). 지표는 판단 재료이지 통과 기준이 아니다(52 complexity-metrics).

## 쓰이는 자료구조·알고리즘

- **제어 흐름 그래프와 순환 복잡도**: 함수의 분기·반복을 그래프로 그리면, 순환 복잡도 = 결정 지점 수 + 1(PMD 문서의 정의). 실험 C의 `sql()`은 `if` 둘에 `&&` 하나라 4다. 대략 "분기마다 한 번씩 거치려면 필요한 독립 경로 수"로 읽는다(McCabe 1976, 52에서 자세히).
- **NPath**: 함수를 지나는 비순환 실행 경로 수. 순차로 놓인 결정은 곱해진다. mixed의 36은 SQL 쪽 경우 수와 할인 쪽 경우 수가 곱해진 결과다. 나누면 함수별로 따로 센다.
- **호출 스택과 프레임**: 함수 하나가 스택 프레임 하나다. 인자는 프레임에 위치 순서로 놓인다. 같은 타입 인자의 순서 실수를 런타임이 구별하지 못하는 이유다. 기초는 [systems/call-stack](../../systems/call-stack/README.md).
- **디스패치 테이블**: 플래그 분기를 없애는 다른 방법. `Map<Mode, Handler>`로 동작을 고른다([28-taming-conditionals](../28-taming-conditionals/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 함수를 읽을 때 순서

1. 이름이 질의(`get`·`is`·`has`·`find`)인가? 그렇다면 본문에 상태 변경·I/O·캐시 갱신이 있나 찾는다. 있으면 "Separate Query from Modifier".
2. 인자에 같은 타입이 나란히 있나? boolean이 있나? 호출처에서 리터럴(`true`·`null`)로 넘기나? 있으면 동작별 함수·전용 타입·인자 객체.
3. 인자를 바꿔서 결과를 전하나(출력 인자)? 반환값으로.
4. 한 함수에 높이가 다른 문장이 섞였나(SQL 문자열과 할인율이 같은 들여쓰기에)? "Extract Function" 또는 "Split Phase".
5. 중첩이 3단 이상인가? 가드 절로 펼친다.
6. 나눈 뒤 호출자가 본문을 열지 않고 쓸 수 있나? 아니면 다시 합친다("Inline Function").

### 2. 고치기 (Java)

```java
// 전: 질의에 숨은 명령, 플래그 인자, 출력 인자
long getBalance();                                    // 캐시 갱신 포함
void save(Order o, boolean notify, boolean audit, String memo);
void collectOverdue(List<Invoice> out);

// 후
void refresh();             long balance();           // 명령과 질의 분리
void save(Order o, Notification n, Audit a);          // 또는 saveAndNotify(o) / saveQuietly(o)
List<Invoice> overdueInvoices();                      // 반환값으로
```

### 3. 진단

```bash
# 이름이 질의인데 void를 돌려주거나 setter가 값을 돌려주는 것 (PMD 7.x)
pmd check -d src/main/java -R category/java/codestyle.xml/LinguisticNaming

# 인자 수·복잡도 (기본 임계: 인자 10, 순환 10, 인지 15, NPath 200)
pmd check -d src/main/java -R category/java/design.xml/ExcessiveParameterList,category/java/design.xml/CyclomaticComplexity,category/java/design.xml/CognitiveComplexity,category/java/design.xml/NPathComplexity

# boolean 리터럴을 넘기는 호출처 (플래그 인자 후보)
grep -rnE '\((.*, *)?(true|false)( *,.*)?\)' src/main/java | grep -v 'assert' | head
```

- `getX`가 상태를 바꾸는 경우는 도구가 직접 못 잡는다(LinguisticNaming은 반환 타입만 본다). 리뷰 질문으로 남긴다.

## 장애 시나리오와 대처

### 1. `save(order, true, false, null)` → 의미 불명, 순서 실수 (⚠ 커리큘럼)

- 현상: "감사 로그만" 의도였는데 고객에게 알림이 나가고 감사 로그는 없다.
- 보이는 형태: 컴파일·테스트 통과(실험 B bad, exit 0). 고객 문의와 감사 누락이 나중에 발견된다.
- 원인: 같은 타입(boolean) 인자 둘의 순서를 호출자가 반대로 기억했다.
- 대처: 동작별 함수(`saveWithAuditOnly`) 또는 전용 타입(enum) — 실험 B good에서 같은 실수가 `incompatible types` 컴파일 오류가 됐다. 인자가 많으면 인자 객체·빌더.

### 2. 조회처럼 보이는 `getBalance()`가 캐시 갱신 → 두 번 부르면 결과가 다름 (⚠ 커리큘럼)

- 현상: 디버그 로그를 켜면 수수료 면제 건수가 늘어난다. 끄면 줄어든다.
- 보이는 형태: 실험 A — 로그 끔 `fee = 500`, 로그 켬 `fee = 0`. 감사 로그 "balance read"가 요청당 1건 또는 2건으로 흔들린다.
- 원인: 질의 이름의 함수가 명령(캐시 갱신)을 겸한다. 관측(로그·디버거)이 상태를 바꾼다.
- 대처: "Separate Query from Modifier" — `refresh()`(명령)와 `balance()`(질의). 갱신 시점을 호출 흐름에서 명시한다.

### 3. SQL 조립과 할인 정책이 한 함수에 → 정책 변경 때 SQL 회귀 (⚠ 커리큘럼)

- 현상: 할인 기준만 바꿨는데 보고서 쿼리에서 지역 조건이 빠졌다.
- 보이는 형태: 보고서 건수 급증. diff는 "할인 기준 1줄"로 보이지만 같은 함수 안 SQL 쪽 줄도 함께 움직였다(병합 충돌 해결 중 등).
- 원인: 추상화 수준이 다른 두 관심사가 한 함수에 있어, 정책 변경이 SQL 코드의 이웃에서 일어난다(실험 C mixed: 변경 hunk가 `report` 안).
- 대처: `OrderQuery.sql()`·`DiscountPolicy.discountOf()`로 나눈다(Split Phase/Extract Function). 정책 변경은 `discountOf`만 건드린다(실험 C split). SQL 쪽은 쿼리 문자열 스냅샷 테스트로 지킨다.

### 4. 너무 잘게 나눈 함수 → 함께 읽어야만 이해됨

- 현상: 버그를 고치려고 3줄짜리 함수 여덟 개를 오가야 한다. 한 함수의 부작용이 다른 함수의 인자 조건을 만든다.
- 보이는 형태: 리뷰 코멘트 "이 함수가 무엇을 전제하는지 모르겠다". 이름을 믿고 본문을 안 읽은 사람이 버그를 만든다.
- 원인: 얕은 분해(conjoined methods). 이름이 질의인데 부작용이 있는 경우가 겹치면 더 위험하다(Ousterhout–Martin 대담의 `isMultipleOfNthPrimeFactor`).
- 대처: 다시 합쳐(Inline Function) 깊은 함수 하나로 만들고, 필요하면 인터페이스 주석으로 계약을 적는다(09).

## 핵심 문장

- 함수의 시그니처는 약속이다. 이름이 질의면 상태를 바꾸지 말고, 인자는 순서 실수가 컴파일 오류가 되게 만든다.
- 실험에서 질의 이름의 함수가 캐시를 갱신하자, 디버그 로그 한 줄이 수수료를 500원에서 0원으로 바꿨다. 명령과 질의를 나누자 로그와 무관해졌다.
- boolean 인자 둘의 순서 실수는 컴파일되고 정반대로 동작했다. 인자마다 전용 타입을 주자 같은 실수가 컴파일 오류가 됐다.
- 한 함수에는 한 추상화 수준을 둔다. 나누면 함수당 복잡도는 줄지만 합은 줄지 않는다(실험 순환 합 9 → 12). 이득은 이름 붙은 조각과 좁아진 변경 범위다.
- 길이보다 깊이: 나눈 함수는 호출자가 본문을 열지 않고 쓸 수 있어야 한다.

## 관련 주제·근거

- 선행
  - [07-naming](../07-naming/2-summary.md) — 이름이 약속하는 것
- 후속·연결
  - [09-comments-and-conventions](../09-comments-and-conventions/2-summary.md) — 시그니처가 못 담는 계약은 인터페이스 주석으로
  - [10-code-smells](../10-code-smells/2-summary.md) — Long Function·Long Parameter List·Data Clumps
  - [06-clean-code](../06-clean-code/2-summary.md) — 원본 「L」의 제어 결합(플래그 인자)
  - [03-deep-modules-and-abstraction](../03-deep-modules-and-abstraction/2-summary.md) · [13-refactoring](../13-refactoring/2-summary.md) · [23-design-by-contract](../23-design-by-contract/2-summary.md) · [24-types-as-invariants](../24-types-as-invariants/2-summary.md) · [28-taming-conditionals](../28-taming-conditionals/2-summary.md) · [52-complexity-metrics](../52-complexity-metrics/2-summary.md)
  - [systems/call-stack](../../systems/call-stack/README.md)
- 글·문서
  - Martin Fowler, "CommandQuerySeparation"(2005-12-05) <https://martinfowler.com/bliki/CommandQuerySeparation.html> · "FlagArgument"(2011-06-23) <https://martinfowler.com/bliki/FlagArgument.html> · "FunctionLength"(2016-11-30) <https://martinfowler.com/bliki/FunctionLength.html>
  - refactoring.com 카탈로그 — Separate Query from Modifier, Remove Flag Argument, Introduce Parameter Object, Replace Nested Conditional with Guard Clauses, Extract Function, Inline Function, Split Phase <https://refactoring.com/catalog/>
  - John Ousterhout, 『A Philosophy of Software Design』 2판 9장 "Better Together Or Better Apart?"(9.7 Splitting and joining methods, 9.8 A different opinion: Clean Code) — 2판 커뮤니티 번역 사이트 영문판으로 장 도입·9.8 확인 <https://yingang.github.io/aposd2e-zh/en/ch09.html>
  - Ousterhout·Martin, "A Philosophy of Software Design vs Clean Code"(2024-09~2025-02 대담 기록) — Method Length Summary, `isMultipleOfNthPrimeFactor` 부작용 <https://github.com/johnousterhout/aposd-vs-clean-code>
  - Bertrand Meyer, 『Object-Oriented Software Construction』 — CQS 출처(Fowler 인용으로 확인, 원문 미열람 [?])
  - Robert C. Martin, 『Clean Code』(Pearson, 2009 — APOSD 각주 표기) 3장 Functions — APOSD 9.8의 인용으로만 확인, 장 번호 [?]
  - G. Ann Campbell, "Cognitive Complexity" 백서 1.7판(SonarSource, 2023-08-29) <https://www.sonarsource.com/docs/CognitiveComplexity.pdf>
  - PMD 7.28.0 design 규칙(ExcessiveParameterList 기본 10, CyclomaticComplexity 메서드 10·클래스 80, CognitiveComplexity 15, NPathComplexity 200) <https://docs.pmd-code.org/pmd-doc-7.28.0/pmd_rules_java_design.html>
- 실험 목록 (코드: scratchpad `sd/06/e08/`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, PMD 7.28.0, git 2.43.0)
  - A 질의 이름의 명령 — `run-cqs.sh` (두 번 호출 값, 로그 켬/끔 수수료)
  - B 플래그 인자 순서 실수 — `run-flags.sh` (boolean: exit 0 / enum: 컴파일 오류)
  - C 섞인 함수 vs 나눈 함수 — `run-slap.sh` (순환·인지·NPath, 같은 출력, 정책 변경 hunk header)
