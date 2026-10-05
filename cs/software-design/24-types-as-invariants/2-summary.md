# software-design/24-types-as-invariants — 원시 타입 집착 제거·parse, don't validate·불법 상태를 표현할 수 없게 — 정리 (힌트)

## 해결하는 문제

검증을 해도 그 사실이 **값에 남지 않으면**, 다음 코드는 그 값이 검증됐는지 모른다. 그래서 같은 검사를 또 하거나, 빠뜨린다.

```text
 String email  ──> [검증] ──> String email  ──> [검증?] ──> String email ──> save()
                   통과했다는 사실이 타입에 없다      또 해야 하나?            빠진 경로가 있나?

 String raw    ──> [parse] ──> Email email ──> ... ──> save(Email)
                   실패하면 여기서 끝              Email 타입이면 검증된 것 — 다시 안 본다
```

- *원시 타입 집착(Primitive Obsession)*: ID·이메일·금액·수량처럼 규칙이 있는 도메인 값을 `Long`·`String`·`int`로 들고 다니는 것. Fowler 『Refactoring』 2판 3장 "Bad Smells in Code"의 스멜 이름이다(출판사 목차, 78쪽).
- *불법 상태(illegal state)*: 도메인 규칙상 있을 수 없는 값 조합. 예: 결제 완료인데 결제 시각이 없음, 음수 금액.

쉬운 예: 놀이공원 손목 밴드다. 입구에서 한 번 확인하고 밴드를 채우면, 안에서는 밴드만 보면 된다. 놀이기구마다 매표소 영수증을 다시 확인하지 않는다.\
똑같은 구조다.\
실무 예: `findOrder(Long userId, Long orderId)`에 인자를 뒤바꿔 넣어도 컴파일된다. `status=PAID`인데 `paidAt=null`인 행이 정산 배치를 NPE로 멈춘다.

[23-design-by-contract](../23-design-by-contract/2-summary.md)가 "누가 검사하나"를 정했다면, 이 노트는 **검사 결과를 타입에 남겨 다시 검사할 필요를 없애는 것**을 다룬다.

## 동작·원리

### 1. 원시 타입 → 전용 타입 (정제 타입·newtype)

```text
 findOrder(Long userId, Long orderId)         findOrder(UserId userId, OrderId orderId)
           ▲ 둘 다 Long                                 ▲ 서로 다른 타입
 findOrder(orderId, userId)  → 컴파일 통과      findOrder(orderId, userId) → 컴파일 오류
```

- *newtype*: 같은 값에 별개의 이름(타입)을 준 래퍼. 혼동을 막는다. 범위·형식 규칙은 생성자 검사(스마트 생성자)를 따로 붙여야 생긴다(King 2019: "abstract `newtype` with a smart constructor"). 자바에서는 필드 하나짜리 `record`로 흉내 낸다.
- *정제 타입(refinement type)*: 기존 타입 + 술어(예: `{v:Int | v > 0}`). 술어를 타입 검사기가 컴파일 때 증명하는 별도 개념이다(Liquid Haskell 등). 자바에는 없어서 래퍼 + 생성자 검사로 흉내 낼 뿐이다.
- Fowler 카탈로그 "Replace Primitive with Object"(별칭 "Replace Data Value with Object", "Replace Type Code with Class")가 이 리팩터링이다.

### 실험 A: ID를 뒤바꿔 넣으면

```java
// Prim.java — 둘 다 Long
static String findOrder(Long userId, Long orderId) { ... ORDERS.get(orderId) ... }
findOrder(orderId, userId);              // 인자 뒤바뀜
// Typed.java — 전용 타입
record UserId(long value) {}
record OrderId(long value) {}
static String findOrder(UserId userId, OrderId orderId) { ... }
findOrder(orderId, userId);              // 인자 뒤바뀜
```

(실험, JDK 21.0.12 temurin `--cpus=2`, `scratchpad/sd/20/e24/a/`, 2026-10-02 — 주문 10은 사용자 1, 주문 1은 사용자 2의 것)

```text
올바른 호출 : 주문 10 (소유자 1)
인자 뒤바뀜 : 주문 1 (소유자 2)  ← 컴파일 통과, 남의 주문
Typed.java:14: error: incompatible types: OrderId cannot be converted to UserId
        System.out.println(findOrder(orderId, userId));     // 인자 뒤바뀜
                                     ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
```

- `Long` 판은 컴파일·실행 모두 통과하고 남의 주문을 돌려줬다(이 예제의 조회 함수는 소유자 검사를 하지 않는다 — 권한 검사 누락이 겹치면 실제 정보 노출이 된다).
- 전용 타입 판은 같은 실수가 컴파일 오류다.

### 2. parse, don't validate

```text
 validate:  String → boolean (또는 void/예외)    결과를 버린다 → 다음 사람이 다시 확인
 parse:     String → Optional<Email>              결과가 "검증된 타입"으로 남는다
            (덜 구조화된 입력 → 더 구조화된 출력, 실패 가능)
```

- Alexis King, "Parse, don't validate"(2019-11-05): `validateNonEmpty`는 `()`를 돌려줘 알게 된 것을 버리고, `parseNonEmpty`는 `NonEmpty a`를 돌려줘 그 지식을 타입에 보존한다. "a parser is just a function that consumes less-structured input and produces more-structured output."
- 같은 글의 권고: "Use a data structure that makes illegal states unrepresentable", "Push the burden of proof upward as far as possible, but no further" — 가능하면 시스템 경계에서 한 번 파싱한다.
- 같은 글이 인용한 LangSec 용어 *shotgun parsing*: 검증 코드가 처리 코드 사이에 흩어져 "어딘가에서 잡히겠지" 하는 안티패턴. 일부를 처리한 뒤에야 나머지가 무효임을 알게 된다.

### 실험 C: 검증 경로가 셋, 하나가 빠졌다

```java
// Validate.java — String을 들고 다니며 경로마다 검증
static void save(String email) { DB.add(email); }               // 저장소는 "검증됐겠지"
static void signupWeb(String email)   { if (!isValidEmail(email)) throw ...; save(email); }
static void signupAdmin(String email) { if (!isValidEmail(email)) throw ...; save(email); }
static void importCsv(String email)   { save(email.trim()); }     // 새로 생긴 경로 — 검증을 빠뜨렸다

// ParseBroken.java — Email 타입이 있어야 저장할 수 있다
record Email(String value) { Email { if (/* 형식 불일치 */) throw new IllegalArgumentException(...); }
                             static Optional<Email> parse(String raw) { ... } }
static void save(Email email) { DB.add(email); }                  // String을 받지 않는다
static void importCsv(String raw) { save(raw.trim()); }           // 검증을 빠뜨리면?
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e24/c/`, 2026-10-02)

```text
web  ""  -> 거절
DB = [a@example.com, ]  (빈 이메일 1건 저장)
Parse.java:15: error: incompatible types: String cannot be converted to Email
    static void importCsv(String raw) { save(raw.trim()); }           // 검증을 빠뜨리면?
                                                     ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
csv  "   " -> 건너뜀(파싱 실패)
DB = [Email[value=a@example.com]]
```

- validate 판: 경로 셋 중 하나가 검증을 빠뜨렸고, 빈 이메일이 저장됐다. 에러 없음.
- parse 판: 검증 없는 경로는 **컴파일이 안 됐다**(오류 메시지의 파일명은 실험 중 고치기 전 `Parse.java`). `Email.parse(raw)`로 고치자 파싱 실패 입력은 저장 전에 걸러졌다.
- 해석: 검증 규칙이 `Email` 생성자 **한 곳**에 있다. 경로가 7개로 늘어도 규칙을 7번 쓰지 않는다.

### 3. 불법 상태를 표현할 수 없게 — 상태별 타입(합 타입)

```text
 필드 조합 (곱 타입)                         상태별 타입 (합 타입)
 Order { status, paidAt?, amount }           sealed Order = Pending(amount)
 status × paidAt 조합 4가지 중                             | Paid(amount, paidAt)   ← paidAt 필수
 (PAID, null)은 불법인데 표현 가능              (PAID, null)을 만들 방법이 없다
```

- *합 타입(sum type)·태그드 유니온(tagged union)*: "A 또는 B 또는 C" 중 정확히 하나인 타입. 자바 17+는 `sealed interface` + `record`로 만든다(JEP 409).
- *곱 타입(product type)*: 필드들의 모든 조합을 담는 타입(클래스·레코드). 필드가 많을수록 불법 조합도 표현 가능해진다.
- Yaron Minsky의 "Make illegal states unrepresentable" — Jane Street 블로그 "Effective ML Revisited"(2011-03-09, 2010년 Harvard 강연 "Effective ML"의 재방문)에서 연결 상태 레코드의 `option` 필드들을 상태별 레코드로 나누는 예로 보인다.

### 실험 B: `status=PAID`, `paidAt=null` 행

```java
// Flags.java — 필드 조합
static String settle(Order o) {
    if (o.status == Status.PAID) return "정산일 " + LocalDate.ofInstant(o.paidAt, ZoneOffset.UTC);
    return "대기";
}
// Sealed.java — 상태별 타입
sealed interface Order permits Pending, Paid {}
record Pending(long amount) implements Order {}
record Paid(long amount, Instant paidAt) implements Order { Paid { Objects.requireNonNull(paidAt, "paidAt"); } }
static String settle(Order o) {
    return switch (o) {                         // default 없음 — 컴파일러가 망라성을 검사
        case Pending p -> "대기";
        case Paid p -> "정산일 " + LocalDate.ofInstant(p.paidAt(), ZoneOffset.UTC);
    };
}
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e24/b/`, 2026-10-02 — 스택은 앞 두 줄만 발췌, 그 아래는 `Flags.settle`·`Flags.main` 프레임)

```text
정산일 2026-10-01
Exception in thread "main" java.lang.NullPointerException: instant
	at java.base/java.util.Objects.requireNonNull(Objects.java:259)
	at java.base/java.time.LocalDate.ofInstant(LocalDate.java:323)
정산일 2026-10-01
new Paid(1000, null) -> NPE: paidAt (생성 시점에 거절)
```

- 필드 조합 판: 불법 행을 읽어 **정산 시점**에 NPE. 스택은 `LocalDate.ofInstant`를 가리켜, 원인 데이터가 언제 어디서 들어왔는지는 알려 주지 않는다.
- 상태별 타입 판: 같은 불법 값은 **만드는 시점**에 거절된다. 정산 코드에는 null 검사가 없다 — `Paid`면 시각이 있다.
- 여기에 새 상태 `Refunded`를 추가하고 `settle`을 안 고치면(`Sealed2.java`):

```text
Sealed2.java:12: error: the switch expression does not cover all possible input values
        return switch (o) {                         // default 없음 — 컴파일러가 망라성을 검사
               ^
1 error
```

- `sealed` + default 없는 패턴 매칭 `switch`(JDK 21, JEP 441)는 새 상태를 처리하지 않은 곳을 컴파일 오류로 알려 준다.

### 4. 스마트 생성자·팩토리와 타입 상태

- *스마트 생성자(smart constructor)*: 검사를 통과해야만 값을 돌려주는 생성 함수. 자바에서는 `record` 간결 생성자 또는 `static Optional<T> parse(...)`·`static T of(...)` 팩토리. 정적 팩토리만 열고 생성자를 숨기려면 일반 클래스에 `private` 생성자를 쓴다(`record`의 표준 생성자는 레코드 클래스 이상의 접근 수준이어야 해서 숨길 수 없다 — JEP 395 "at least as much access as the record class").
- *타입 상태(typestate)*: 객체의 상태를 타입으로 나눠, 그 상태에서 허용된 연산만 컴파일되게 하는 것. Strom·Yemini 1986 "Typestate" 논문이 이름을 붙였다.

### 실험 D: 인증 전 이메일로 비밀번호 재설정

```java
record UnverifiedEmail(String value) {
    VerifiedEmail verify(String code, String expected) {
        if (!code.equals(expected)) throw new IllegalArgumentException("code mismatch");
        return new VerifiedEmail(value);
    }
}
record VerifiedEmail(String value) {}
static String sendPasswordReset(VerifiedEmail to) { return "reset link -> " + to.value(); }
```

(실험, JDK 21.0.12, `scratchpad/sd/20/e24/d/TypeStateBroken.java`·`TypeState.java`)

```text
TypeState.java:15: error: incompatible types: UnverifiedEmail cannot be converted to VerifiedEmail
        System.out.println(sendPasswordReset(e));          // 인증 전 이메일로 호출
                                             ^
Note: Some messages have been simplified; recompile with -Xdiags:verbose to get full output
1 error
reset link -> a@example.com
```

- 첫 블록: 인증 전 값을 넘기는 호출이 컴파일 오류(파일명은 실험 중 그 줄을 지우기 전 이름). 둘째 줄: 그 호출을 지운 뒤 `verify`를 거친 값만 재설정 링크를 받았다.
- 한계: `new VerifiedEmail("...")`를 바깥에서 직접 부르면 우회된다. 막으려면 `VerifiedEmail`을 생성자가 `private`인 일반 클래스로 만들고 `verify`만 생성 경로로 둔다.

### 5. 비용 — 타입이 손해인 경우 (주장, 측정 아님)

- 경계에서 변환 코드가 는다: JSON·DB·메시지 ↔ 전용 타입. 직렬화·ORM 매핑에 변환기 설정이 필요할 수 있다(프레임워크·버전별 확인 [?]).
- 타입이 너무 잘게 나뉘면 단순 계산에도 `.value()` 풀기·감싸기가 반복된다.
- 판단 기준(해석): 그 값에 **규칙**(형식·범위·혼동 위험)이 있고 **여러 곳을 지나가면** 타입으로 만든다. 한 메서드 안에서만 쓰는 중간값은 원시 타입으로 둔다.

## 쓰이는 자료구조·알고리즘

- **합 타입 = 태그드 유니온**: 값 + "어느 경우인지" 태그. JVM에서 `sealed` 계층은 클래스(태그 = 실제 클래스)로 표현되고, 패턴 매칭 `switch`가 태그로 분기한다. 컴파일러는 `permits` 목록으로 망라성을 검사한다.
- **newtype + 스마트 생성자**: 값 하나를 감싼 래퍼 + 생성 시 술어 검사. 만들 수 있는 값은 술어를 통과한 값뿐이다(정제 타입이 컴파일 때 증명하는 것을 실행 시점 검사로 흉내 낸다).
- **타입 상태 = 상태 기계를 타입으로**: 상태 = 타입, 전이 = 한 타입을 받아 다른 타입을 돌려주는 메서드(`verify: Unverified → Verified`). 허용되지 않은 전이는 메서드가 없어서 호출할 수 없다. 상태 기계 기초는 [domain-modeling/11-state-machines-in-domain](../../domain-modeling/11-state-machines-in-domain/2-summary.md).
- **파서(parser)**: 덜 구조화된 입력(문자열·바이트)을 구조화된 값으로 바꾸는 부분 함수. 실패 가능하므로 `Optional`/`Result`/예외로 실패를 표현한다(실패 표현 선택은 [16-error-strategy-exceptions-vs-results](../16-error-strategy-exceptions-vs-results/2-summary.md)).

## 적용 — 풀어나가는 법

1. **혼동되기 쉬운 ID부터 전용 타입으로.** 같은 원시 타입 인자가 둘 이상인 메서드가 1순위(실험 A).
2. **규칙이 있는 값(이메일·금액·수량·기간)을 값 타입으로.** 검증은 생성자 한 곳.
3. **경계에서 parse.** 컨트롤러·메시지 리스너·CSV 리더에서 원시 입력을 도메인 타입으로 바꾸고, 안쪽 메서드는 도메인 타입만 받는다. 저장소 메서드 시그니처도 도메인 타입으로.
4. **"이 필드는 이 상태일 때만 있음"이 보이면 상태별 타입으로.** `nullable` 필드 + `status` enum 조합이 신호다. `sealed` + `record`, `switch`는 default 없이.
5. **DB에서 읽을 때도 parse.** 불법 행이 이미 있을 수 있다. 읽는 시점에 실패시키고 로그로 남겨, 정산 같은 먼 곳에서 터지지 않게 한다.

```java
// 경계: 원시 입력 → 도메인 타입 (한 번만)
@PostMapping("/signup")
ResponseEntity<?> signup(@RequestBody SignupRequest req) {
    Optional<Email> email = Email.parse(req.email());
    if (email.isEmpty()) return ResponseEntity.badRequest().body("이메일 형식");
    signupService.signup(email.get());          // 안쪽은 Email만 안다 — 다시 검증하지 않는다
    return ResponseEntity.ok().build();
}
// DB 행 → 상태별 타입 (불법 조합은 여기서 실패)
static Order fromRow(String status, Instant paidAt, long amount) {
    return switch (status) {
        case "PENDING" -> new Pending(amount);
        case "PAID"    -> new Paid(amount, paidAt);          // paidAt == null 이면 여기서 NPE("paidAt")
        default -> throw new IllegalStateException("unknown status: " + status);
    };
}
```

진단:

```bash
# 같은 원시 타입 ID 인자가 둘 이상인 메서드 (뒤바뀜 위험)
grep -rnE '\((Long|long|String) \w+Id, (Long|long|String) \w+Id' src/main/java
# 같은 검증 함수가 몇 곳에서 불리나 (shotgun parsing 후보)
grep -rn 'isValidEmail(' src/main/java | wc -l
```

```sql
-- 이미 저장된 불법 상태 찾기 (예시 스키마)
SELECT id FROM orders WHERE status = 'PAID' AND paid_at IS NULL;
SELECT id FROM orders WHERE amount < 0;
```

## 장애 시나리오와 대처

### 1. `userId`와 `orderId`가 둘 다 `Long` → 인자 뒤바뀜, 남의 주문 조회

- 현상: 고객이 자기 것이 아닌 주문 상세를 본다.
- 보이는 형태: 에러 없음. 실험 A의 `주문 1 (소유자 2)`. 접근 로그에서 요청 사용자와 조회된 주문 소유자가 다르다.
- 원인: 같은 원시 타입 인자 둘. 컴파일러가 구분할 수 없다. 조회에 소유자 검사가 없으면 바로 노출이 된다.
- 대처: `UserId`·`OrderId` 전용 타입(컴파일 오류로 차단). 별도로 조회 시 소유자 검사(권한은 타입과 별개 층이다).

### 2. 같은 검증이 7곳에 반복, 1곳만 최신 → 불법 상태 저장

- 현상: 빈 이메일 회원, 음수 금액 주문이 DB에 있다.
- 보이는 형태: 실험 C validate 판의 `빈 이메일 1건 저장`. 새로 생긴 경로(CSV 가져오기·관리자 API)에서만 발생.
- 원인: 검증한 사실이 타입에 남지 않아 경로마다 다시 검증해야 했고, 한 경로가 빠졌다(shotgun parsing).
- 대처: 값 타입 생성자에 규칙을 한 번 두고, 저장소·도메인 메서드는 그 타입만 받는다. 검증 없는 경로는 컴파일 오류가 된다(실험 C parse 판). 저장된 불법 데이터는 SQL로 찾아 보정.

### 3. `status=PAID`인데 `paidAt=null` → 정산 NPE

- 현상: 새벽 정산 배치가 NPE로 중단된다.
- 보이는 형태: `NullPointerException: instant ... at java.time.LocalDate.ofInstant`(실험 B). 원인 행은 스택에 나오지 않는다.
- 원인: 상태와 필드를 독립 컬럼으로 두어 불법 조합이 표현 가능했고, 어느 경로가 상태만 바꿨다.
- 대처: 상태별 타입(`Paid`는 `paidAt` 필수). DB 읽기에서 parse해 불법 행을 그 자리에서 실패·격리. DB에도 제약을 둘 수 있다 — (실험 E, PostgreSQL 17.11 전용 일회용 컨테이너, 2026-10-02):

```text
CREATE TABLE orders(id int primary key, status text, paid_at timestamptz, amount bigint,
                    CHECK (status <> 'PAID' OR paid_at IS NOT NULL));
INSERT INTO orders VALUES (1,'PAID',now(),1000);   → INSERT 0 1
INSERT INTO orders VALUES (2,'PAID',NULL,1000);    →
ERROR:  new row for relation "orders" violates check constraint "orders_check"
DETAIL:  Failing row contains (2, PAID, null, 1000).
```

  - 타입은 우리 애플리케이션 경로를, DB 제약은 다른 경로(수동 SQL·다른 서비스)까지 막는다. 기존 불법 행이 있으면 제약 추가 자체가 실패한다. 불법 행 1건이 이미 든 테이블 `o`에서 확인한 출력(같은 PostgreSQL 17.11, `psql -e`):

```text
ALTER TABLE o ADD CONSTRAINT c1 CHECK (status <> 'PAID' OR paid_at IS NOT NULL);
ERROR:  check constraint "c1" of relation "o" is violated by some row
ALTER TABLE o ADD CONSTRAINT c1 CHECK (status <> 'PAID' OR paid_at IS NOT NULL) NOT VALID;
ALTER TABLE
INSERT INTO o VALUES (2,'PAID',NULL);
ERROR:  new row for relation "o" violates check constraint "c1"
DETAIL:  Failing row contains (2, PAID, null).
ALTER TABLE o VALIDATE CONSTRAINT c1;
ERROR:  check constraint "c1" of relation "o" is violated by some row
```

  - `NOT VALID`는 기존 행 검사를 미루고 새 행부터 막는다. 기존 불법 행을 보정하기 전에는 `VALIDATE CONSTRAINT`가 실패한다.

  - 먼저 불법 행을 보정하거나, `NOT VALID`로 새 행부터 막고 보정 뒤 `VALIDATE CONSTRAINT`로 검증한다.

### 4. 검증한 사실이 타입에 안 남음 → 방어 코드 중복

- 현상: 서비스·도메인·저장소에 같은 null·형식 검사가 겹겹이 있고, 규칙 변경 때 어긋난다.
- 보이는 형태: `isValidEmail(` 호출 수가 경로 수만큼(위 grep). 일부는 규칙 버전이 다르다.
- 원인: `String`은 "검증됨"을 표현하지 못한다. 그래서 각 층이 스스로 방어했다(23의 방어적 중복과 같은 병).
- 대처: parse 한 번 + 안쪽은 타입 신뢰. 중복 검사는 지운다.

### 5. 새 상태를 추가했는데 처리 누락 → default 분기로 조용히

- 현상: `REFUNDED` 상태를 추가한 뒤 일부 화면·리포트가 환불 주문을 "대기"로 보여 준다.
- 보이는 형태: 에러 없음. `switch`/`if-else`의 기본 분기가 새 상태를 받았다.
- 원인: enum + default 있는 분기. 망라성 검사가 꺼져 있다.
- 대처: `sealed` + default 없는 패턴 매칭 `switch`(또는 enum에 대한 default 없는 switch 식) — 새 상태 추가 시 컴파일 오류(실험 B `Sealed2.java`).

## 핵심 문장

- 검증 결과가 `boolean`이면 다음 사람이 모른다. **parse**해서 검증된 타입으로 돌려주면 그 사실이 타입에 남아 다시 검사할 필요가 없다(King 2019).
- 같은 원시 타입 ID 둘은 뒤바뀌어도 컴파일된다. 전용 타입이면 컴파일 오류다(실험 A).
- "이 필드는 이 상태일 때만 있다"는 상태별 타입(합 타입)으로 표현하면 불법 조합을 만들 수 없고, 새 상태의 처리 누락은 `sealed` 망라성 검사가 잡는다(실험 B).
- 검증 규칙을 값 타입 생성자 한 곳에 두면 검증 없는 경로가 컴파일되지 않는다(실험 C).
- 비용은 경계의 변환 코드다. 규칙이 있고 여러 곳을 지나가는 값부터 타입으로 만든다.

## 관련 주제·근거

- 선행
  - [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md) — 값 객체·불변
  - [23-design-by-contract](../23-design-by-contract/2-summary.md) — 계약(누가 검사하나), record 간결 생성자
  - language/05 `type-systems`, language/08 `error-handling-models` — 미작성([language/README](../../language/README.md))
- 후속·연결
  - [18-absence-and-null-design](../18-absence-and-null-design/2-summary.md) — null을 타입으로 다루기
  - [16-error-strategy-exceptions-vs-results](../16-error-strategy-exceptions-vs-results/2-summary.md) — parse 실패를 무엇으로 돌려주나
  - [domain-modeling/04-entities-and-value-objects](../../domain-modeling/04-entities-and-value-objects/2-summary.md)·[domain-modeling/05-aggregates-and-invariants](../../domain-modeling/05-aggregates-and-invariants/2-summary.md)·[domain-modeling/11-state-machines-in-domain](../../domain-modeling/11-state-machines-in-domain/2-summary.md)
  - [22-solid](../22-solid/2-summary.md) — switch 식 망라성(OCP 실험)
- 글·문서
  - Alexis King, "Parse, don't validate", 2019-11-05 <https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/>
  - Yaron Minsky, "Effective ML Revisited", Jane Street Tech Blog, 2011-03-09("Make illegal states unrepresentable" 절, 2010년 강연 재방문) <https://blog.janestreet.com/effective-ml-revisited/>
  - Scott Wlaschin, 『Domain Modeling Made Functional』(Pragmatic, 2018-01) — 출판사 목차의 "Domain Modeling with Types", "Integrity and Consistency in the Domain"(Enforcing Invariants with the Type System), "Modeling Workflows as Pipelines"(Modeling an Order as a Set of States) 장. 본문 미열람 <https://pragprog.com/titles/swdddf/domain-modeling-made-functional/>
  - Martin Fowler, 『Refactoring』 2판(Addison-Wesley, 2018) 3장 목차 "Primitive Obsession" <https://www.informit.com/store/refactoring-improving-the-design-of-existing-code-9780134757711>
  - Martin Fowler, refactoring.com "Replace Primitive with Object"(별칭 Replace Data Value with Object, Replace Type Code with Class) <https://refactoring.com/catalog/replacePrimitiveWithObject.html>
  - R. E. Strom, S. Yemini, "Typestate: A programming language concept for enhancing software reliability", IEEE TSE SE-12(1):157–171, 1986. doi:10.1109/TSE.1986.6312929
  - JEP 409 Sealed Classes(JDK 17), JEP 441 Pattern Matching for switch(JDK 21), JEP 395 Records(JDK 16) <https://openjdk.org/jeps/409> · <https://openjdk.org/jeps/441> · <https://openjdk.org/jeps/395>
- 실험 목록 (JDK 21.0.12 temurin 컨테이너 `--cpus=2 --network none`, 2026-10-02)
  - A `scratchpad/sd/20/e24/a/Prim.java`·`Typed.java` — 원시 ID 뒤바뀜 vs 전용 타입 컴파일 오류
  - B `scratchpad/sd/20/e24/b/Flags.java`·`Sealed.java`·`Sealed2.java` — 필드 조합 NPE vs 상태별 타입, 새 상태 망라성 오류
  - C `scratchpad/sd/20/e24/c/Validate.java`·`ParseBroken.java`·`Parse.java` — validate 경로 누락 vs parse 컴파일 오류
  - D `scratchpad/sd/20/e24/d/TypeStateBroken.java`·`TypeState.java` — 타입 상태(인증 전/후 이메일)
  - E `postgres:17` 일회용 컨테이너 `sn-sd-w20-pg`(`--network none`, 실행 후 삭제) — `CHECK` 제약으로 불법 조합 거절
