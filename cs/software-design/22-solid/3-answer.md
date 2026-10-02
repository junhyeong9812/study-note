# software-design/22-solid — 정답

## 정답

### 1. 출처별 정의

- SRP: Martin. 2014 블로그 "The Single Responsibility Principle" — "each software module should have one and only one reason to change", 그리고 "the reasons for change are people". 근거로 Parnas 1972(바뀔 결정으로 모듈 분해)를 든다. 『Clean Architecture』 7장(목차 확인).
- OCP: Meyer 『Object-Oriented Software Construction』 1판(1988) — 모듈은 "both open and closed". Martin 2014 블로그가 이를 인용하고 "extend the behavior of a system without having to modify that system"으로 다시 쓴다.
- LSP: Liskov 1987 OOPSLA 기조연설 "Data Abstraction and Hierarchy"의 치환 성질, Liskov·Wing 1994 행동적 하위 타입.

### 2. 새 종류 추가

- `git diff --stat` 요약: switch 쪽 `Fee`·`Limit`·`PaymentType` 3 files changed, 3 insertions(+), 1 deletion(-). poly 쪽 `EasyPay`·`Main` 2 files changed, 7 insertions(+), 1 deletion(-).

```text
[switch] EASY_PAY fee(100000)=1500 limit=2000000 label=기타
```

- switch 쪽은 기존 파일 3개를 열었고, `Label`을 빠뜨렸는데도 컴파일·실행이 통과해 라벨이 default의 "기타"가 됐다.
- 다형 쪽은 새 파일 1개 + 등록 1줄. 라벨 구현을 빠뜨리면 인터페이스 미구현으로 컴파일이 안 된다.

### 3. 새 연산 추가

- `git diff --stat` 요약: switch 쪽 `RefundFee.java` 1 file changed, 9 insertions(+). poly 쪽 `Bank`·`Card`·`EasyPay`·`PaymentMethod` 4 files changed, 4 insertions(+).

- 이번에는 다형 설계가 기존 파일 4개를 열었다. OCP는 모든 변경에 닫히는 것이 아니라 **선택한 축**에 닫힌다. 한 축에 닫으면 다른 축에 열린다(표현 문제). 어느 축이 실제로 반복되는지 이력으로 고른다.

### 4. 망라성 검사

```text
RefundFee.java:3: error: the switch expression does not cover all possible input values
```

- default 없는 switch **식**인 `RefundFee`는 컴파일 오류. default가 있는 switch **문**(`Fee`·`Limit`·`Label`)은 조용히 통과해, 새 값이 default 분기로 처리된다.

### 5. LSP 실험

```text
Square area=16 (기대 20과 다름)
List.of                   : add -> UnsupportedOperationException
Arrays.asList             : add -> UnsupportedOperationException
Arrays.asList set(0,z)    : [z, y]
```

- 넷 다 컴파일은 통과한다. `Arrays.asList`는 크기 고정 — 원소 교체(`set`)는 되고 크기 변경(`add`)은 안 된다.

### 6. JDK 불변 리스트는 LSP 위반인가

- `Collection` javadoc은 일부 메서드를 "optional"로 지정하고, 구현하지 않으면 `UnsupportedOperationException`을 던지라고 적는다. `List.add`도 "(optional operation)". 그래서 **상위 타입 계약 안**의 동작이다.
- 대가: 계약이 "던질 수도 있다"로 약해져, 호출자는 타입만 보고 `add`가 되는지 모른다. 수정할 쪽이 사본을 만들거나, 도메인 타입에서는 능력별 타입 분리가 낫다는 것이 원본의 주장이다.

### 7. DIP 테스트

```text
[V1] 테스트 실패: ConnectException: Connection refused
[V2] OK sent=[a@example.com]
```

- V1은 정책이 세부(SMTP 소켓)를 직접 만들어 세부 없이는 테스트가 돌지 않는다. V2는 정책 쪽 인터페이스에 가짜 구현(람다 한 줄)을 넣어 검증한다.
- 비용: 인터페이스와 주입 코드가 는다. 경계를 넘는 의존(DB·외부 API·메일·시계)에만 적용하는 이유다.

### 8. 라벨 "기타"

- 원인: 같은 `switch(type)`이 여러 파일에 흩어져 있고, 새 종류 추가 때 한 곳(라벨)을 빠뜨렸다. default 분기가 누락을 조용히 삼켰다(실험 B 재현).
- 확인: `grep -rn 'case CARD'`로 같은 분기가 있는 파일 목록을 뽑아, 새 값이 빠진 곳을 찾는다.
- 재발 방지: 반복되는 축이면 다형/테이블로 한 곳에 모은다. switch를 유지하면 default 없는 switch 식으로 바꿔 누락을 컴파일 오류로 만든다.

### 9. "좋은 instanceof"의 조건

- `if (tx instanceof Cancellable c) c.cancel();`는 분기 수가 고정된다는 점에서 좋다. 그러나 새 취소 가능 타입이 `Cancellable`을 **구현하지 않으면** 컴파일 오류 없이 취소를 건너뛴다. 이 경우 "컴파일 시점에 드러난다"는 틀리다.
- 컴파일 시점에 잡히는 것은 메서드가 `Cancellable`을 매개변수 타입으로 받아(`void cancel(Cancellable tx)`), 취소 불가 타입을 넘기는 코드가 컴파일되지 않을 때다(원본 「instanceof를 아예 없애는 방법」).
