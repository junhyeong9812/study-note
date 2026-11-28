# java/java-design-patterns/25 — Event Sourcing Basics (이벤트 소싱) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 다섯 번의 거래 뒤 세 번째 시점 (예측)

```java
// 질문용 발췌
BankAccount account = BankAccount.create("ACC-001", "김철수", 100_000);
account.deposit(500_000, "월급");
account.withdraw(50_000, "점심 식사");
account.deposit(200_000, "보너스");
account.withdraw(30_000, "교통비");
// … 이벤트를 eventStore 에 모두 저장한 뒤
BankAccount p3 = BankAccount.fromHistory(eventStore.getEventsUntil("ACC-001", 3));
BankAccount p5 = BankAccount.fromHistory(eventStore.getEventsUntil("ACC-001", 5));
```

- `p3.getBalance()` 와 `p5.getBalance()` 는 각각 얼마인가?

### 2. 대기 중인 이벤트를 두 번 꺼내면 (예측)

```java
// 질문용 발췌
BankAccount a = BankAccount.create("A", "이영희", 1_000);
a.deposit(500, "용돈");
List<DomainEvent> first = a.getUncommittedEvents();
List<DomainEvent> second = a.getUncommittedEvents();
System.out.println(first.size() + " / " + second.size());
```

- 찍히는 한 줄은 무엇인가?

### 3. 음수 금액 출금 (예측)

```java
// 질문용 발췌
BankAccount b = BankAccount.create("B", "박민수", 10_000);
b.withdraw(-3_000, "실수");
System.out.println(b.getBalance());
```

- 예외가 나는가, 아니면 무엇이 찍히는가?

### 4. `fromHistory` 가 `apply` 가 아니라 `handleEvent` 를 부르는 까닭 (왜)

- 재생에서 `apply` 를 부르면 어떤 문제가 생기나?

### 5. 검증은 명령 메서드에만 있고 `handleEvent` 에는 없는 까닭 (왜)

- 이벤트 핸들러가 잔액 부족 같은 규칙을 검사하지 않아도 되는 이유는 무엇인가?

### 6. `getEventsUntil` 에 0 이나 이벤트 수보다 큰 값을 주면 (경계)

- 저장된 이벤트가 5개일 때 `eventCount` 가 0 · 100 이면 각각 무엇이 돌아오고, 재생하면 어떤 계좌가 되나?

### 7. 이 `EventStore` 는 정말 수정 · 삭제를 막는가 (경계)

- `append` 말고는 메서드가 없는데도, 바깥 코드가 저장된 이벤트를 지울 수 있는 길은 어디에 있나?

### 8. 데모의 `snapshot` 변수와 팁의 「스냅샷」 (연결)

- 시간 여행 루프의 `snapshot` 은 팁이 말하는 스냅샷과 무엇이 다르며, 진짜 스냅샷은 재생 시간을 어떻게 줄이나?

### 9. 이벤트 소싱과 CQRS (연결)

- 이벤트 저장소를 쓰기 쪽으로 두었을 때, 「계좌별 현재 잔액」 조회 화면은 CQRS 로 어떻게 나눌 수 있나?

## 실습

### 실습 1. 이벤트 소싱 은행 계좌 만들기

**만들 것** — 계좌의 생성 · 입금 · 출금 · 해지를 이벤트로 남기고, 저장소의 이벤트를 재생해 현재 상태 · 과거 시점 상태 · 감사 로그를 보여 주는 콘솔 프로그램.

**준비물** — 패턴 매칭 `switch` 를 쓰므로 JDK 21 이상. 외부 라이브러리는 없다.

**요구 조건**

1단계 — 이벤트

1. 추상 클래스 `DomainEvent` 의 생성자는 집합체 ID 를 받아, 이벤트 ID(무작위 UUID 의 앞 8자) · 집합체 ID · 발생 시각(지금)을 `final` 필드에 채운다.
2. `DomainEvent` 는 세 값의 getter 와 추상 메서드 `getEventType()` 을 가진다.
3. 구체 이벤트 넷 — `AccountCreated`(소유자 이름 · 초기 잔액) · `MoneyDeposited`(금액 · 설명) · `MoneyWithdrawn`(금액 · 설명) · `AccountClosed`(사유) — 를 만들고, 각자 `super(accountId)` 를 부르며 `getEventType()` 은 자기 클래스 이름 문자열을 돌려준다.

2단계 — 저장소

4. `EventStore` 는 집합체 ID → 이벤트 리스트 맵을 갖고, `append` 는 그 ID 가 처음이면 새 리스트를 만들어 이벤트를 덧붙인다.
5. `getEvents(id)` 는 그 ID 의 이벤트 목록을, 없으면 빈 목록을 돌려준다.
6. `getEventsUntil(id, n)` 은 앞에서 n 개를 돌려주되, n 이 이벤트 수보다 크면 전부를 돌려준다.

3단계 — 집합체 `BankAccount`

7. 상태 필드(계좌 ID · 소유자 · 잔액 · 해지 여부)와 「아직 저장 안 된 이벤트」 리스트를 둔다.
8. 정적 팩토리 `create` 는 빈 계좌를 만들고 `AccountCreated` 를 적용해 돌려준다.
9. `deposit` 은 해지된 계좌면 `IllegalStateException`, 금액이 0 이하면 `IllegalArgumentException` 을 던지고, 통과하면 `MoneyDeposited` 를 적용한다.
10. `withdraw` 는 해지된 계좌거나 금액이 잔액보다 크면 `IllegalStateException` 을 던지고, 통과하면 `MoneyWithdrawn` 을 적용한다.
11. `close` 는 이미 해지된 계좌면 `IllegalStateException` 을 던지고, 통과하면 `AccountClosed` 를 적용한다.
12. `apply` 는 이벤트를 핸들러로 반영한 뒤 「저장 안 된 이벤트」 리스트에 넣는다.
13. `handleEvent` 는 패턴 매칭 `switch` 로 — 생성이면 네 필드를 모두 설정 · 입금이면 잔액 증가 · 출금이면 잔액 감소 · 해지면 해지 표시 — 하고, 모르는 이벤트는 `IllegalArgumentException` 으로 거절한다.
14. 정적 메서드 `fromHistory` 는 빈 계좌에 이벤트들을 `handleEvent` 로만 차례로 반영한다(저장 대기에 넣지 않는다).
15. `getUncommittedEvents` 는 대기 이벤트의 복사본을 돌려주고 대기 리스트를 비운다.

4단계 — 데모 `main`

16. 계좌(`ACC-001`, 김철수, 100,000)를 만들고 입금 500,000 · 출금 50,000 · 입금 200,000 · 출금 30,000 을 차례로 실행한다.
17. 대기 이벤트를 꺼내 하나씩 저장소에 덧붙이며 「저장: 이벤트」를 찍고, 현재 상태를 찍는다.
18. 저장소의 전체 이벤트로 계좌를 복원해 찍고, 원래 계좌와 잔액이 같은지 `true`/`false` 로 찍는다.
19. 이벤트를 1개, 2개, … 전체 개수까지 재생하며 그때마다의 잔액을 찍는다.
20. 전체 이벤트를 차례로 돌며 발생 시각 · 이벤트 · 이벤트 ID 를 한 줄씩 찍는다(감사 로그).

**시작 코드**

```java
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

abstract class DomainEvent {
    private final String eventId;
    private final String aggregateId;
    private final LocalDateTime occurredAt;

    protected DomainEvent(String aggregateId) {
        // TODO: eventId(UUID 앞 8자) · aggregateId · occurredAt(지금) 채우기
    }

    public String getEventId() { return eventId; }
    public String getAggregateId() { return aggregateId; }
    public LocalDateTime getOccurredAt() { return occurredAt; }
    // TODO: 이벤트 종류를 돌려주는 추상 메서드
}

class AccountCreated extends DomainEvent {
    private final String ownerName;
    private final double initialBalance;

    public AccountCreated(String accountId, String ownerName, double initialBalance) {
        // TODO: 부모 생성자 호출과 필드 채우기
    }

    public String getOwnerName() { return ownerName; }
    public double getInitialBalance() { return initialBalance; }

    // TODO: getEventType()

    @Override
    public String toString() {
        return String.format("[%s] 계좌 생성: %s, 초기잔액=%.0f",
            getEventType(), ownerName, initialBalance);
    }
}

class MoneyDeposited extends DomainEvent {
    // TODO: amount, description 필드 · 생성자 · getter · getEventType()

    @Override
    public String toString() {
        return String.format("[%s] 입금: +%.0f (%s)", getEventType(), amount, description);
    }
}

class MoneyWithdrawn extends DomainEvent {
    // TODO: amount, description 필드 · 생성자 · getter · getEventType()

    @Override
    public String toString() {
        return String.format("[%s] 출금: -%.0f (%s)", getEventType(), amount, description);
    }
}

class AccountClosed extends DomainEvent {
    // TODO: reason 필드 · 생성자 · getter · getEventType()

    @Override
    public String toString() {
        return String.format("[%s] 계좌 해지: %s", getEventType(), reason);
    }
}

class EventStore {
    private final Map<String, List<DomainEvent>> store = new HashMap<>();

    public void append(DomainEvent event) {
        // TODO: 집합체 ID 별 리스트에 덧붙이기 (처음이면 새 리스트)
    }

    public List<DomainEvent> getEvents(String aggregateId) {
        // TODO: 없으면 빈 목록
        return null;
    }

    public List<DomainEvent> getEventsUntil(String aggregateId, int eventCount) {
        // TODO: 앞에서 eventCount 개 (이벤트 수를 넘지 않게)
        return null;
    }
}

class BankAccount {
    private String accountId;
    private String ownerName;
    private double balance;
    private boolean isClosed;

    private final List<DomainEvent> uncommittedEvents = new ArrayList<>();

    public BankAccount() {}

    public static BankAccount create(String accountId, String ownerName, double initialBalance) {
        // TODO: 빈 계좌 + 생성 이벤트 적용
        return null;
    }

    public void deposit(double amount, String description) {
        // TODO: 검증 → 입금 이벤트 적용
    }

    public void withdraw(double amount, String description) {
        // TODO: 검증 → 출금 이벤트 적용
    }

    public void close(String reason) {
        // TODO: 검증 → 해지 이벤트 적용
    }

    private void apply(DomainEvent event) {
        // TODO: 반영 + 저장 대기
    }

    private void handleEvent(DomainEvent event) {
        // TODO: 패턴 매칭 switch 로 이벤트 → 상태 변경
    }

    public static BankAccount fromHistory(List<DomainEvent> events) {
        // TODO: 빈 계좌에 이벤트를 반영만 하기
        return null;
    }

    public List<DomainEvent> getUncommittedEvents() {
        // TODO: 복사본 반환 + 대기 리스트 비우기
        return null;
    }

    public String getAccountId() { return accountId; }
    public String getOwnerName() { return ownerName; }
    public double getBalance() { return balance; }
    public boolean isClosed() { return isClosed; }

    @Override
    public String toString() {
        return String.format("BankAccount{id='%s', owner='%s', balance=%.0f, closed=%s}",
            accountId, ownerName, balance, isClosed);
    }
}

public class EventSourcingDemo {
    public static void main(String[] args) {
        EventStore eventStore = new EventStore();
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("HH:mm:ss.SSS");

        System.out.println("=== 이벤트 발생 ===");
        // TODO: 계좌 생성 + 입금 · 출금 네 번
        // TODO: 대기 이벤트를 저장소에 덧붙이며 "  저장: " + event 출력
        // TODO: "\n현재 상태: " + account 출력

        System.out.println("\n=== 이벤트 재생 (전체 복원) ===");
        // TODO: 전체 이벤트로 복원 · 출력 · 잔액 비교 출력

        System.out.println("\n=== 시점별 상태 복원 (Time Travel) ===");
        // TODO: 1 ~ 전체 개수까지 재생하며 "  이벤트 %d개 재생 -> 잔액: %.0f원%n" 출력

        System.out.println("\n=== 이벤트 로그 (감사 추적) ===");
        // TODO: "  [%s] %s (id=%s)%n" 으로 시각 · 이벤트 · ID 출력
    }
}
```

**확인 방법** — 파일을 `EventSourcingDemo.java` 로 저장하고 `javac EventSourcingDemo.java && java EventSourcingDemo` 로 돌린다.
현재 상태와 복원된 상태의 잔액이 같고 비교 줄이 `true` 인지, 시점별 잔액이 손으로 더하고 뺀 값과 맞는지, 감사 로그가 다섯 줄 차례대로 나오는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
