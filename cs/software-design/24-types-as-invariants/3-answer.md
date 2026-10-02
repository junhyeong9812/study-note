# software-design/24-types-as-invariants — 정답

## 정답

### 1. 반복 검증과 parse

- 검증 결과가 `boolean`·`void`(예외)로 끝나면 "검증됨"이라는 사실이 값에 남지 않는다. 다음 코드는 그 `String`이 검증됐는지 모르니 다시 검사하거나, 검사를 빠뜨린다.
- validate: `String → boolean/void` — 알게 된 것을 버린다. parse: `String → Optional<Email>` — 덜 구조화된 입력을 더 구조화된 값으로 바꾸고, 지식을 타입에 보존한다(King 2019의 `validateNonEmpty` vs `parseNonEmpty`).

### 2. ID 뒤바뀜

(실험 A)

```text
인자 뒤바뀜 : 주문 1 (소유자 2)  ← 컴파일 통과, 남의 주문
Typed.java:14: error: incompatible types: OrderId cannot be converted to UserId
```

- `Long` 판은 컴파일·실행 모두 통과해 다른 사용자의 주문을 돌려줬다. 전용 타입 판은 컴파일 오류.
- 권한(소유자) 검사는 타입과 별개로 필요하다.

### 3. 검증 누락 경로

(실험 C)

```text
DB = [a@example.com, ]  (빈 이메일 1건 저장)
Parse.java:15: error: incompatible types: String cannot be converted to Email
csv  "   " -> 건너뜀(파싱 실패)
DB = [Email[value=a@example.com]]
```

- String 판: 빈 이메일이 저장됐다(에러 없음).
- Email 판: 검증 없이 `save(raw.trim())`을 하면 컴파일이 안 된다. `Email.parse`를 거치게 고치면 실패 입력은 저장 전에 걸러진다.

### 4. 불법 상태를 표현할 수 없게

- 규칙상 있을 수 없는 값 조합을 **만들 방법 자체가 없게** 타입을 짜는 것(Minsky "Make illegal states unrepresentable").
- `status` + nullable `paidAt`은 곱 타입: 필드 조합 전부(PENDING/PAID × null/값)가 표현 가능하고, 그중 (PAID, null)이 불법이다.
- `sealed Order = Pending | Paid(paidAt)`은 합 타입: 정확히 한 경우만 가지며 `Paid`는 시각이 필수라 (PAID, null)을 만들 수 없다.

### 5. 불법 행과 새 상태

(실험 B)

```text
Exception in thread "main" java.lang.NullPointerException: instant
	at java.base/java.time.LocalDate.ofInstant(LocalDate.java:323)
new Paid(1000, null) -> NPE: paidAt (생성 시점에 거절)
Sealed2.java:12: error: the switch expression does not cover all possible input values
```

- 필드 조합 판: 사용하는 곳(정산)에서 NPE. 원인 행은 스택에 없다.
- 상태별 타입 판: 만드는 곳에서 거절. 정산 코드에는 null 검사가 없다.
- `Refunded` 추가 후 `switch` 미수정: default 없는 패턴 매칭 `switch`라 컴파일 오류로 누락이 드러난다(JDK 21, JEP 441).

### 6. 스마트 생성자

- 방법: `record` 간결 생성자에 검사를 두거나(모든 생성 경로가 지나감), `static Optional<T> parse(...)`·`static T of(...)` 팩토리.
- `record`의 표준 생성자는 레코드 클래스 이상의 접근 수준이어야 한다(JEP 395 "at least as much access as the record class"). 그래서 공개 레코드의 생성자를 숨겨 팩토리만 열 수는 없다. 숨겨야 하면 `private` 생성자를 가진 일반 `final` 클래스를 쓴다.

### 7. 타입 상태

- 객체의 상태를 타입으로 나눠, 그 상태에서 허용된 연산만 컴파일되게 하는 것(Strom·Yemini 1986).

```text
TypeState.java:15: error: incompatible types: UnverifiedEmail cannot be converted to VerifiedEmail
reset link -> a@example.com
```

- 인증 전 이메일로 재설정 호출은 컴파일 오류, `verify`를 거친 값만 통과한다.
- 한계: `VerifiedEmail`이 공개 record라 바깥에서 `new VerifiedEmail(...)`로 우회할 수 있다. 생성 경로를 `verify` 하나로 막으려면 생성자를 숨긴 클래스로 만든다.

### 8. 타입이 손해인 경우

- 경계에서 변환 코드(JSON·DB ↔ 타입)가 늘고, 직렬화·ORM 변환기 설정이 필요할 수 있다. 잘게 나눈 타입은 계산마다 감싸기·풀기가 반복된다.
- 기준(해석): 그 값에 규칙(형식·범위·혼동 위험)이 있고 여러 곳을 지나가면 타입으로. 한 메서드 안의 중간값은 원시 타입으로 둔다.

### 9. 정산 NPE

- 원인 데이터 찾기: `SELECT id FROM orders WHERE status = 'PAID' AND paid_at IS NULL;` — 스택에는 행 정보가 없으므로 데이터에서 찾는다. 그 행을 만든 경로(상태만 바꾼 코드·수동 SQL)를 이력으로 추적.
- 코드: 상태별 타입(`Paid`는 `paidAt` 필수)으로 바꾸고, DB에서 읽을 때 parse해 불법 행을 그 자리에서 실패·격리한다.
- DB: `CHECK (status <> 'PAID' OR paid_at IS NOT NULL)` (실험 E에서 불법 INSERT가 `violates check constraint`로 거절됨). 기존 불법 행이 있으면 제약 추가가 실패하므로 먼저 보정하거나 PostgreSQL `NOT VALID`로 새 행부터 막는다.
