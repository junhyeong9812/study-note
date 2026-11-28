# java/java-design-patterns/25 — Event Sourcing Basics (이벤트 소싱) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 세 번째 시점은 550,000, 다섯 번째 시점은 720,000

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `p3.getBalance()` → `550000.0`
- `p5.getBalance()` → `720000.0`

**왜 그런가**

- `getEventsUntil(…, 3)` 은 앞 3개 — 생성 100,000 · 입금 500,000 · 출금 50,000 — 를 돌려준다.
- 재생하면 100,000 + 500,000 − 50,000 = 550,000 이다.
- 5개를 모두 재생하면 550,000 + 200,000 − 30,000 = 720,000 으로, 원래 계좌의 현재 잔액과 같다.
- 근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」.

### 2. `2 / 0` — 꺼내면 대기 목록이 빈다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
2 / 0
```

**왜 그런가**

- `create` 가 `AccountCreated` 를, `deposit` 이 `MoneyDeposited` 를 대기 목록에 넣어 2개가 된다.
- 첫 `getUncommittedEvents` 는 2개짜리 복사본을 돌려주고 대기 목록을 비운다.
- 두 번째 호출은 빈 목록의 복사본을 돌려준다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 3. 예외 없이 잔액이 13,000 으로 늘어난다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 예외가 나지 않고 `13000.0` 이 찍힌다.

**왜 그런가**

- `withdraw` 는 해지 여부와 `amount > balance` 만 검사한다 — `-3,000 > 10,000` 은 거짓이라 통과한다.
- 핸들러가 `balance -= -3000` 을 해서 잔액이 13,000 이 된다.
- `double` 을 `println` 하면 소수점 한 자리가 붙은 꼴로 찍힌다.
- 이 이벤트가 저장되면 지울 수 없는 사실이 되므로, 명령 검증이 빠진 것이 그대로 남는다.
- 근거: 2-summary 「동작 방식 (2)」의 검증 표 · 「어디서 틀리나 3」.

### 4. 재생한 이벤트가 다시 저장 대기에 들어가 중복 저장되기 때문이다

- `apply` 는 반영에 더해 이벤트를 「저장 안 된 이벤트」 목록에 넣는다.
- 재생하는 이벤트는 이미 저장소에 있는 것이라, 다시 대기에 넣으면 다음 저장 때 같은 이벤트가 두 번 쌓인다.
- 그러면 다음 재생에서 같은 입금이 두 번 반영되는 식으로 상태가 틀어진다.
- `handleEvent` 만 부르면 상태는 똑같이 만들어지고 대기 목록은 비어 있다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」.

### 5. 이벤트는 이미 일어난 사실이라 되묻지 않고 반영만 하기 때문이다

- 검증은 「이 일을 해도 되나」를 묻는 것이고, 그것은 명령 단계에서 끝났다.
- 핸들러가 받는 이벤트는 이미 허락되어 일어난 사실이다.
- 핸들러에 규칙을 넣으면, 규칙이 바뀐 뒤 옛 이벤트를 재생할 때 거절되어 복원이 깨질 수 있다.
- 또 새 이벤트 반영과 재생이 같은 `handleEvent` 를 쓰므로, 핸들러를 단순하게 두어야 두 길의 결과가 같다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 6. 0 이면 빈 목록 → 기본값 계좌, 100 이면 5개 전부 → 현재 상태

- `eventCount` 0 → `subList(0, 0)` 이라 빈 목록이다.
- 빈 목록을 재생하면 예외 없이 `balance` 0 · `accountId` `null` 인 기본값 계좌가 나온다.
- `eventCount` 100 → `Math.min(100, 5)` = 5 라 5개 전부가 돌아오고, 재생하면 현재 상태(잔액 720,000)와 같다.
- `Math.min` 이 없으면 끝 인덱스가 크기를 넘어 예외가 났을 것이다(원본 주석: endIndex 가 size 를 넘지 않게 min 사용).
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 7. `getEvents` · `getEventsUntil` 이 내부 리스트(와 그 뷰)를 그대로 내준다

- 이벤트 객체는 `final` 필드라 불변이지만, 저장소의 리스트는 바꿀 수 있다.
- `getEvents` 는 맵 안의 `ArrayList` 자체를 돌려주므로, 받은 쪽이 `remove` · `clear` 를 부르면 저장소가 바뀐다.
- `getEventsUntil` 의 `subList` 도 원래 리스트의 뷰라, 고치면 원본에 반영된다.
- 즉 「추가만 가능」은 이 코드에서 수정 메서드를 두지 않는 관례로만 지켜진다.
- 근거: 2-summary 「어디서 틀리나 4」 · 「구현 세부사항 대 언어 보장」 표.

### 8. `snapshot` 은 그때그때 재생한 결과일 뿐이고, 진짜 스냅샷은 저장해 두고 그 뒤만 재생한다

- 데모의 `snapshot` 은 매 반복마다 앞 i 개를 처음부터 다시 재생해 만든 계좌다 — 어디에도 저장하지 않는다.
- 팁의 스냅샷은 어느 시점까지 재생한 상태를 따로 저장해 둔 것이다.
- 복원할 때 그 스냅샷 상태에서 출발해 그 뒤의 이벤트만 재생하므로, 이벤트가 많아도 재생할 양이 줄어든다.
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 7」.

### 9. 쓰기는 이벤트 저장소, 읽기는 이벤트로 갱신한 별도 잔액표

- 쓰기 모델: 명령 → 집합체(검증) → 이벤트를 저장소에 덧붙인다.
- 읽기 모델: 이벤트를 받아 「계좌 ID → 현재 잔액」처럼 조회하기 좋은 꼴로 따로 만들어 둔다.
- 조회 화면은 매번 이벤트를 재생하지 않고 그 읽기 모델만 본다.
- 이렇게 읽기와 쓰기의 모델을 나누는 것이 원본 팁이 말하는 CQRS 와의 조합이다.
- 근거: 2-summary 「동작 방식 (6)」의 CQRS 그림.

## 실습 정답

### 실습 1. 이벤트 소싱 은행 계좌 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 이벤트 ID · 집합체 ID · 발생 시각 자동 채움 | `DomainEvent` 생성자 — `UUID.randomUUID().toString().substring(0, 8)` · `LocalDateTime.now()` |
| 2. getter 와 추상 `getEventType()` | `getEventId` · `getAggregateId` · `getOccurredAt` · `public abstract String getEventType()` |
| 3. 구체 이벤트 넷 | `AccountCreated` · `MoneyDeposited` · `MoneyWithdrawn` · `AccountClosed` 의 `super(accountId)` 와 `getEventType()` |
| 4. ID 별 리스트에 덧붙이기 | `EventStore.append` — `store.computeIfAbsent(…, k -> new ArrayList<>()).add(event)` |
| 5. 없으면 빈 목록 | `getEvents` — `store.getOrDefault(aggregateId, List.of())` |
| 6. 앞 n 개, 넘치면 전부 | `getEventsUntil` — `events.subList(0, Math.min(eventCount, events.size()))` |
| 7. 상태 필드와 대기 리스트 | `accountId` · `ownerName` · `balance` · `isClosed` · `uncommittedEvents` |
| 8. 생성도 이벤트로 | `BankAccount.create` — `account.apply(new AccountCreated(…))` |
| 9. 입금 검증 | `deposit` — `isClosed` · `amount <= 0` 검사 후 `apply(new MoneyDeposited(…))` |
| 10. 출금 검증 | `withdraw` — `isClosed` · `amount > balance` 검사 후 `apply(new MoneyWithdrawn(…))` |
| 11. 해지 검증 | `close` — `isClosed` 검사 후 `apply(new AccountClosed(…))` |
| 12. 반영 + 저장 대기 | `apply` — `handleEvent(event); uncommittedEvents.add(event);` |
| 13. 패턴 매칭 핸들러 | `handleEvent` 의 `switch (event)` — `case AccountCreated e -> {…}` … `default -> throw …` |
| 14. 반영만 하는 재생 | `fromHistory` — `account.handleEvent(event)` 반복 |
| 15. 꺼내고 비우기 | `getUncommittedEvents` — `new ArrayList<>(uncommittedEvents)` 후 `clear()` |
| 16. 계좌 생성과 거래 넷 | `main` 의 `BankAccount.create("ACC-001", "김철수", 100_000)` 와 `deposit` · `withdraw` 호출 |
| 17. 저장하며 출력 · 현재 상태 | `for (DomainEvent event : account.getUncommittedEvents())` 의 `eventStore.append` · `"현재 상태: "` |
| 18. 전체 복원 · 잔액 비교 | `BankAccount.fromHistory(history)` · `account.getBalance() == restored.getBalance()` |
| 19. 시점별 잔액 | `for (int i = 1; i <= history.size(); i++)` 안의 `getEventsUntil` · `fromHistory` · `printf` |
| 20. 감사 로그 | `for (DomainEvent event : history)` 의 `getOccurredAt().format(fmt)` · `event` · `getEventId()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`java/java-design-patterns/reference/event-sourcing-basics.java`

```java
// [디자인 패턴] Event Sourcing Basics (이벤트 소싱)
// 설명: 상태를 직접 저장하는 대신, 상태 변경 이벤트를 순서대로 저장하고 재생하여 현재 상태를 복원하는 패턴
// 팁: 이벤트 소싱의 핵심 장점은 완전한 감사 추적과 시간 여행(특정 시점 복원)이다. 이벤트는 불변이며 추가만 가능하다(수정/삭제 불가). 이벤트 수가 많아지면 스냅샷을 저장하여 재생 시간을 줄인다. CQRS와 함께 사용하면 읽기와 쓰기 모델을 분리할 수 있다.

// === Event Sourcing 기본 개념 ===
// 해결 문제: 도메인의 모든 변경 이력을 보존하고, 어떤 시점이든 상태를 복원하고 싶음
// 참여자: DomainEvent(불변 사실), EventStore(append-only 저장소), Aggregate(이벤트 발생/적용 주체)
// 장점: 완전한 감사 추적, 시간 여행, CQRS 친화. 단점: 복잡도, 이벤트 스키마 진화 어려움
// 은행 계좌 시스템: 이벤트 저장 및 재생으로 상태 복원

// LocalDateTime: 이벤트 발생 시각
import java.time.LocalDateTime;
// DateTimeFormatter: 시각 출력 포맷
import java.time.format.DateTimeFormatter;
// ArrayList: 가변 이벤트 리스트
import java.util.ArrayList;
// HashMap: aggregateId별 이벤트 목록 매핑
import java.util.HashMap;
// List: 이벤트 컬렉션
import java.util.List;
// Map: 키-값 컬렉션
import java.util.Map;
// UUID: 이벤트 식별자 생성
import java.util.UUID;

// === Event 기본 클래스 ===
// DomainEvent: 일어난 사실(불변)을 나타내는 기본 추상
abstract class DomainEvent {
    // 이벤트 자체의 ID (이력 추적용)
    private final String eventId;
    // 이 이벤트가 속한 집합체(여기서는 계좌)의 ID
    private final String aggregateId;
    // 발생 시각
    private final LocalDateTime occurredAt;

    // 생성자: 자동으로 ID와 시각 부여
    protected DomainEvent(String aggregateId) {
        // UUID 앞 8자리만 사용 (가독성)
        this.eventId = UUID.randomUUID().toString().substring(0, 8);
        this.aggregateId = aggregateId;
        this.occurredAt = LocalDateTime.now();
    }

    public String getEventId() { return eventId; }
    public String getAggregateId() { return aggregateId; }
    public LocalDateTime getOccurredAt() { return occurredAt; }
    // 이벤트 종류 식별 (역직렬화/라우팅용)
    public abstract String getEventType();
}

// === Concrete Events ===
// ConcreteEvent 1: 계좌 생성 사실
class AccountCreated extends DomainEvent {
    private final String ownerName;
    private final double initialBalance;

    public AccountCreated(String accountId, String ownerName, double initialBalance) {
        super(accountId);
        this.ownerName = ownerName;
        this.initialBalance = initialBalance;
    }

    public String getOwnerName() { return ownerName; }
    public double getInitialBalance() { return initialBalance; }

    @Override
    public String getEventType() { return "AccountCreated"; }

    @Override
    public String toString() {
        return String.format("[%s] 계좌 생성: %s, 초기잔액=%.0f",
            getEventType(), ownerName, initialBalance);
    }
}

// ConcreteEvent 2: 입금 사실
class MoneyDeposited extends DomainEvent {
    private final double amount;
    private final String description;

    public MoneyDeposited(String accountId, double amount, String description) {
        super(accountId);
        this.amount = amount;
        this.description = description;
    }

    public double getAmount() { return amount; }
    public String getDescription() { return description; }

    @Override
    public String getEventType() { return "MoneyDeposited"; }

    @Override
    public String toString() {
        return String.format("[%s] 입금: +%.0f (%s)", getEventType(), amount, description);
    }
}

// ConcreteEvent 3: 출금 사실
class MoneyWithdrawn extends DomainEvent {
    private final double amount;
    private final String description;

    public MoneyWithdrawn(String accountId, double amount, String description) {
        super(accountId);
        this.amount = amount;
        this.description = description;
    }

    public double getAmount() { return amount; }
    public String getDescription() { return description; }

    @Override
    public String getEventType() { return "MoneyWithdrawn"; }

    @Override
    public String toString() {
        return String.format("[%s] 출금: -%.0f (%s)", getEventType(), amount, description);
    }
}

// ConcreteEvent 4: 계좌 해지 사실
class AccountClosed extends DomainEvent {
    private final String reason;

    public AccountClosed(String accountId, String reason) {
        super(accountId);
        this.reason = reason;
    }

    public String getReason() { return reason; }

    @Override
    public String getEventType() { return "AccountClosed"; }

    @Override
    public String toString() {
        return String.format("[%s] 계좌 해지: %s", getEventType(), reason);
    }
}

// === Event Store: 이벤트 저장소 ===
// EventStore: 추가만 가능한 이벤트 로그 (append-only)
class EventStore {
    // aggregateId별 이벤트 시퀀스
    private final Map<String, List<DomainEvent>> store = new HashMap<>();

    // 이벤트 추가 (수정/삭제 없음)
    public void append(DomainEvent event) {
        // computeIfAbsent: aggregateId가 처음이면 새 리스트 생성
        store.computeIfAbsent(event.getAggregateId(), k -> new ArrayList<>())
            .add(event);
    }

    // 한 집합체의 모든 이벤트 조회
    public List<DomainEvent> getEvents(String aggregateId) {
        return store.getOrDefault(aggregateId, List.of());
    }

    // 특정 시점까지의 이벤트만 조회
    // 시간 여행: N번째까지 자른 부분 시퀀스로 과거 상태 복원
    public List<DomainEvent> getEventsUntil(String aggregateId, int eventCount) {
        List<DomainEvent> events = getEvents(aggregateId);
        // subList의 endIndex가 size 초과하지 않도록 min 사용
        return events.subList(0, Math.min(eventCount, events.size()));
    }
}

// === Aggregate: 이벤트를 발생시키고 재생하는 도메인 객체 ===
// Aggregate: 명령을 받아 검증 후 새 이벤트를 발생시키고, 이벤트로 자기 상태를 업데이트
class BankAccount {
    // 현재 상태 필드들 (이벤트로부터 파생됨)
    private String accountId;
    private String ownerName;
    private double balance;
    private boolean isClosed;

    // 이벤트 재생을 통한 상태 복원
    // 아직 EventStore에 저장되지 않은 새 이벤트들
    private final List<DomainEvent> uncommittedEvents = new ArrayList<>();

    // 빈 상태로 시작 (이벤트 재생용)
    public BankAccount() {}

    // 새 계좌 생성 (명령)
    // 정적 팩토리: 신규 생성도 이벤트로 표현
    public static BankAccount create(String accountId, String ownerName, double initialBalance) {
        BankAccount account = new BankAccount();
        // 생성 이벤트를 발생시키고 적용
        account.apply(new AccountCreated(accountId, ownerName, initialBalance));
        return account;
    }

    // 입금 명령
    // 명령 처리: 검증 -> 이벤트 발생
    public void deposit(double amount, String description) {
        if (isClosed) throw new IllegalStateException("해지된 계좌입니다");
        if (amount <= 0) throw new IllegalArgumentException("입금액은 양수여야 합니다");
        apply(new MoneyDeposited(accountId, amount, description));
    }

    // 출금 명령
    public void withdraw(double amount, String description) {
        if (isClosed) throw new IllegalStateException("해지된 계좌입니다");
        // 잔액 검증 (도메인 불변식)
        if (amount > balance) throw new IllegalStateException("잔액 부족: 현재 " + balance);
        apply(new MoneyWithdrawn(accountId, amount, description));
    }

    // 해지 명령
    public void close(String reason) {
        if (isClosed) throw new IllegalStateException("이미 해지된 계좌입니다");
        apply(new AccountClosed(accountId, reason));
    }

    // 이벤트 적용 (상태 변경)
    // apply: 새 이벤트일 때 호출 - 상태 변경 + uncommitted 큐 추가
    private void apply(DomainEvent event) {
        handleEvent(event);
        uncommittedEvents.add(event);
    }

    // 이벤트 핸들러: 이벤트 -> 상태 변경
    // handleEvent: 이벤트로부터 상태를 결정 (재생 시에도 동일 로직 사용)
    private void handleEvent(DomainEvent event) {
        // Java 21+ 패턴 매칭 switch
        switch (event) {
            case AccountCreated e -> {
                // 생성 이벤트: 모든 필드 초기화
                this.accountId = e.getAggregateId();
                this.ownerName = e.getOwnerName();
                this.balance = e.getInitialBalance();
                this.isClosed = false;
            }
            // 잔액 증감
            case MoneyDeposited e -> this.balance += e.getAmount();
            case MoneyWithdrawn e -> this.balance -= e.getAmount();
            // 해지 플래그 설정
            case AccountClosed e -> this.isClosed = true;
            default -> throw new IllegalArgumentException("알 수 없는 이벤트: " + event.getEventType());
        }
    }

    // 이벤트 히스토리로부터 상태 복원
    // fromHistory: 저장된 이벤트들을 순서대로 재생하여 현재 상태 만들기
    public static BankAccount fromHistory(List<DomainEvent> events) {
        BankAccount account = new BankAccount();
        for (DomainEvent event : events) {
            // 재생 시에는 uncommitted에 넣지 않음 (이미 저장된 이벤트)
            account.handleEvent(event); // uncommitted에는 추가하지 않음
        }
        return account;
    }

    // 저장되지 않은 이벤트 반환 및 초기화
    // EventStore에 flush 후 비움
    public List<DomainEvent> getUncommittedEvents() {
        List<DomainEvent> events = new ArrayList<>(uncommittedEvents);
        uncommittedEvents.clear();
        return events;
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

// 데모 진입점
public class EventSourcingDemo {
    public static void main(String[] args) {
        // 이벤트 저장소 생성
        EventStore eventStore = new EventStore();
        // 시각 포맷터
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("HH:mm:ss.SSS");

        // === 1. 이벤트 발생 및 저장 ===
        System.out.println("=== 이벤트 발생 ===");
        // 계좌 생성 + 여러 명령 실행 -> 이벤트 다수 발생
        BankAccount account = BankAccount.create("ACC-001", "김철수", 100_000);
        account.deposit(500_000, "월급");
        account.withdraw(50_000, "점심 식사");
        account.deposit(200_000, "보너스");
        account.withdraw(30_000, "교통비");

        // 이벤트 저장
        // uncommitted 이벤트들을 EventStore에 한꺼번에 append
        for (DomainEvent event : account.getUncommittedEvents()) {
            eventStore.append(event);
            System.out.println("  저장: " + event);
        }
        System.out.println("\n현재 상태: " + account);

        // === 2. 이벤트 재생으로 상태 복원 ===
        // 저장된 모든 이벤트를 처음부터 적용 -> 현재 상태 복원
        System.out.println("\n=== 이벤트 재생 (전체 복원) ===");
        List<DomainEvent> history = eventStore.getEvents("ACC-001");
        BankAccount restored = BankAccount.fromHistory(history);
        System.out.println("복원된 상태: " + restored);
        // 원본과 복원본의 잔액 일치 확인
        System.out.println("원본과 동일? balance=" + (account.getBalance() == restored.getBalance()));

        // === 3. 특정 시점 상태 복원 (Time Travel) ===
        // 이벤트를 1, 2, 3...개씩 재생하여 과거 시점들을 복원
        System.out.println("\n=== 시점별 상태 복원 (Time Travel) ===");
        for (int i = 1; i <= history.size(); i++) {
            List<DomainEvent> partialHistory = eventStore.getEventsUntil("ACC-001", i);
            BankAccount snapshot = BankAccount.fromHistory(partialHistory);
            System.out.printf("  이벤트 %d개 재생 -> 잔액: %.0f원%n", i, snapshot.getBalance());
        }

        // === 4. 이벤트 로그 = 완전한 감사 추적 ===
        // 시간순으로 모든 변경 이력을 그대로 출력
        System.out.println("\n=== 이벤트 로그 (감사 추적) ===");
        for (DomainEvent event : history) {
            System.out.printf("  [%s] %s (id=%s)%n",
                event.getOccurredAt().format(fmt),
                event,
                event.getEventId());
        }
    }
}
```

**실행 결과** — 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다).

**풀이 요점**

- 상태를 바꾸는 코드는 `handleEvent` 한 곳뿐이고, 새 이벤트(`apply`)와 재생(`fromHistory`)이 모두 이것을 쓴다.
- 명령 메서드는 검증만 하고 이벤트를 만들어 넘긴다 — 핸들러는 검증하지 않는다.
- `fromHistory` 가 `apply` 가 아니라 `handleEvent` 를 불러야 중복 저장이 생기지 않는다.
- `getUncommittedEvents` 는 복사본을 돌려주고 비우므로, 저장 루프에서 한 번만 부른다.
- 시간 여행은 별도 기능이 아니라 「앞 n 개 잘라서 재생」이다 — `Math.min` 이 범위를 지킨다.
- 시점별 잔액은 100,000 → 600,000 → 550,000 → 750,000 → 720,000 이 되어야 손계산과 맞는다(코드를 읽어 추론한 값).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Java 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(JDK 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
