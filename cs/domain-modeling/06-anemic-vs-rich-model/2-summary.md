# domain-modeling/06-anemic-vs-rich-model — 빈약한 도메인 모델 vs 풍부한 모델 — 정리 (힌트)

## 해결하는 문제

객체가 자기 상태를 지키지 못하면, 누구든 setter로 업무상 있을 수 없는 상태를 만들어 저장할 수 있다. 규칙은 "이 객체를 쓰는 사람이 서비스를 거쳐 줄 것"이라는 약속에만 기대게 된다.

쉬운 예: 통장.

```text
  통장 A — 고객이 볼펜으로 잔액 칸에 직접 쓴다      통장 B — 창구에서만 입금·출금을 기록한다
     "잔액 100만 원" (실제 입금 기록 없음)            출금 요청 → 창구가 잔액 확인 → 부족하면 거절
        → 기록과 잔액이 어긋나도 아무도 못 막는다        → 기록 없는 잔액은 생길 수 없다
```

똑같은 구조다.\
`Order`에 `setPaid`·`setShipped`·`setTotal`과 수정 가능한 `getLines()`가 열려 있다. `OrderService`의 `pay()`·`ship()`은 규칙을 지키지만, 다른 코드가 `order.setShipped(true)`를 부르면 "결제 안 된 배송" 주문이 저장된다. 아래 실험에서 공개 메서드를 무작위로 부르면 1만 시퀀스 중 9,974개가 불변식을 깼다.

- *빈약한 도메인 모델(anemic domain model)*: 도메인 객체가 관계·구조는 갖췄지만 행위가 거의 없어 "getter와 setter 가방"인 상태(Fowler "AnemicDomainModel", 2003-11-25). 규칙은 서비스에 있다.
- *풍부한 모델(rich domain model)*: 상태와 그 상태를 바꾸는 규칙을 같은 객체에 둔 모델. 상태 변경은 의도를 드러내는 메서드(`pay`, `ship`)로만 한다.
- *불변식(invariant)*: 객체가 살아 있는 동안 늘 참이어야 하는 조건. 예: "배송됨이면 결제됨이다".

## 동작·원리

### 1. 두 모델의 호출 구조

```text
  빈약 모델                                     풍부 모델
  ┌ OrderService ──────────────┐               ┌ OrderService ────────┐
  │ if (!o.isPaid()) return;   │               │ o.ship();            │  ← 시키기만
  │ o.setShipped(true);        │               └──────────┬───────────┘
  │ o.setStatus("SHIPPED");    │                          ▼
  └────────────┬───────────────┘               ┌ Order ───────────────────────────┐
               ▼                               │ ship() {                          │
  ┌ Order ─────────────────────┐               │   if (!paid) throw …;  ← 규칙     │
  │ get/set status, paid,      │  ◀── 누구나    │   shipped = true; status = …;     │
  │ shipped, total, getLines() │      직접 호출  │ }  setter 없음                    │
  └────────────────────────────┘               └───────────────────────────────────┘
  규칙 = 서비스를 거친다는 약속                    규칙 = 객체에 들어가는 유일한 문
```

- Fowler(2003): 이 안티패턴의 근본 문제는 "데이터와 처리를 함께 묶는다"는 객체 지향 설계의 기본 생각과 정반대라는 것이다. 결과는 절차적 설계이고, 사실상 Transaction Script(07번)가 되어 도메인 모델의 이점을 잃는다.
- Fowler는 같은 글에서 Evans의 애플리케이션 계층 정의("얇게 유지하고 업무 규칙을 담지 않는다", 01번)를 인용한다. 빈약 모델은 그 얇아야 할 서비스 계층에 업무 규칙이 쌓인 모습이다.
- Fowler는 도메인 모델이 늘 최선의 도구는 아니라고도 쓴다. 문제는 "도메인 모델이라고 부르면서 행위가 없는 것"이다.

### 2. Vernon의 진단 질문 (『IDDD』 1장)

- InformIT 발췌(2012-11-09)
  - "domain model"이라 부르는 것에 대부분 public getter·setter만 있고 업무 로직이 거의 없나?
  - 그 "domain model"을 자주 쓰는 컴포넌트들에 시스템 업무 로직 대부분이 있나?
  - Vernon은 올바른 답이 "둘 다 예" 아니면 "둘 다 아니요"라고 쓴다. 둘 다 "예"면 그 "domain model"은 빈약하다("It's anemic"), 둘 다 "아니요"면 건강하다고 같은 발췌에 적혀 있다.
- 원인으로 Vernon이 드는 것: 1990년대 Visual Basic 폼 디자이너의 프로퍼티 시트가 JavaBean 명세와 Hibernate 같은 영속 프레임워크에 영향을 줬고, 지금 시장의 프레임워크 대부분이 단순 객체의 public 프로퍼티를 요구해 그 사용을 부추긴다.
  - 같은 발췌의 단서: Hibernate가 public getter·setter를 요구했다는 비판은 "역사적 관점"이고, Hibernate는 오래전부터 숨긴 접근자와 필드 직접 접근을 지원한다고 Vernon도 적는다(실험 C와 같은 결론).

### 3. 캡슐화 = 상태 공간을 줄인다

```text
  추상 상태 (status 4가지 × paid × shipped × 줄 있음) = 32개

  빈약 모델: setter로 어떤 칸이든 바꿀 수 있다 → 32개 전부 도달
  풍부 모델: 가드가 있는 메서드 4개로만 이동 → 7개만 도달

     NEW ──addLine──▶ NEW(줄 있음) ──pay──▶ PAID ──ship──▶ SHIPPED
      │                    │                  │
      └──cancel──▶ CANCELLED  ◀──cancel───────┘   (배송 뒤에는 cancel 거절)
```

- 풍부 모델은 "불법 상태를 만들 수 없게" 하는 방식으로 불변식을 지킨다. 검사를 잊는 경로가 아예 없다.
- 아래 실험 B가 이 숫자(32 vs 7)를 BFS로 센다.

### 실험 A: 공개 메서드를 무작위로 부를 때 불변식이 깨지는 횟수

- 환경: JDK 21(`eclipse-temurin:21-jdk`, openjdk 21.0.12, `--cpus=2`, 네트워크 없음), `Random(42)` 고정, 2026-10-03.
- 불변식: I1 배송됨 ⇒ 결제됨, I2 `total` = 줄 금액 합, I3 취소됨 ⇒ 배송 안 됨, I4 결제 뒤 줄 수 변경 없음.
- 세 경우
  - 빈약 모델 — 공개 표면 = 서비스 메서드 4개 + setter 4개 + `getLines().add`. 서비스 메서드는 규칙을 지킨다.
  - 빈약 모델, 서비스만 호출 — 팀이 "setter는 서비스에서만" 규율을 완벽히 지킨 경우.
  - 풍부 모델 — 공개 표면 = `addLine`·`pay`·`ship`·`cancel` + `lines()`가 돌려준 목록에 `add` 시도. `lines()`는 `List.copyOf` 복사본을 준다.
- 한 시퀀스 = 새 주문에 무작위 호출 최대 20번. 불변식이 처음 깨지면 그 시퀀스를 "위반"으로 센다.

```java
// 풍부 모델의 문 — 규칙을 어기는 호출은 예외로 거절된다
public void ship() { if (!paid || shipped || status.equals("CANCELLED")) throw new IllegalStateException(); shipped = true; status = "SHIPPED"; }
public List<Long> lines() { return List.copyOf(lines); }          // 복사본만 내준다
```

(실험, JDK 21 temurin, 2026-10-03)

```text
시퀀스 10000개 × 최대 20호출 (seed 42)
빈약 모델(공개 setter 포함)   불변식 위반 시퀀스 = 9974
  처음 깬 호출→불변식: {getLines().add→I2=4171, setPaid→I1=80, setPaid→I4=3, setShipped→I1=1679, setShipped→I3=127, setStatus→I3=43, setTotal→I2=3871}
빈약 모델(서비스만 호출)      불변식 위반 시퀀스 = 0
풍부 모델(공개 메서드 전부)   불변식 위반 시퀀스 = 0  (거절된 호출 126938)
```

- 관찰
  - 빈약 모델에서 처음 불변식을 깬 호출은 전부 setter·컬렉션 노출이었다. 서비스 메서드가 깬 경우는 없었다.
  - 규율을 완벽히 지킨 빈약 모델도 0이다. 차이는 **규칙이 지켜지는 근거**다. 빈약 모델은 "모두가 서비스를 거친다"는 약속, 풍부 모델은 "객체에 다른 문이 없다"는 구조다.
  - 풍부 모델은 무작위 호출 대부분을 예외로 거절했다(126,938회). 호출하는 쪽은 거절을 다뤄야 한다. 이것이 풍부 모델의 비용이다.
  - 무작위 호출은 실제 코드의 호출 분포가 아니다. 위반 비율 자체가 아니라 "어떤 문으로 깨지나"를 본다.

### 실험 B: 도달 가능한 상태 수 (BFS)

- 추상 상태 `(status, paid, shipped, 줄 있음)` 32개. 각 모델의 공개 연산을 간선으로 보고 `NEW·미결제·미배송·줄 없음`에서 BFS.
- 이 실험의 "불법" = 배송됨인데 미결제, 취소됨인데 배송됨, 결제됨인데 줄 없음.

(실험, JDK 21 temurin, 2026-10-03)

```text
anemic 도달 가능 상태 32개 / 전체 32개, 그중 불법 17개
rich   도달 가능 상태  7개 / 전체 32개, 그중 불법 0개
   S[st=NEW, paid=false, shipped=false, lines=false]
   S[st=NEW, paid=false, shipped=false, lines=true]
   S[st=CANCELLED, paid=false, shipped=false, lines=false]
   S[st=PAID, paid=true, shipped=false, lines=true]
   S[st=CANCELLED, paid=false, shipped=false, lines=true]
   S[st=SHIPPED, paid=true, shipped=true, lines=true]
   S[st=CANCELLED, paid=true, shipped=false, lines=true]
```

- 관찰: 빈약 모델은 setter 때문에 모든 조합에 도달한다. `status = "PAID"`인데 `paid = false`처럼 필드끼리 어긋난 조합(이 실험의 "불법" 정의 밖)도 여기에 들어 있다. 풍부 모델은 7개만 도달하고, 테스트할 상태도 7개로 준다.

### 실험 C: setter 없는 풍부 엔티티를 JPA로 저장할 수 있나

- 환경: 위 JDK 21 + Hibernate ORM 6.6.29.Final + H2 2.3.232 인메모리.
- `@Id`를 필드에 둔 `Order`(필드 접근), `protected` 인자 없는 생성자, setter 0개, `addLine`·`pay`만 공개.

(실험, JDK 21 temurin + Hibernate 6.6.29, 2026-10-03)

```text
복원: status=PAID total=5000
복원 뒤에도 규칙 유지: 결제 뒤 변경 불가
Order의 set* 메서드 수 = 0
```

- 관찰: Hibernate 6.6은 필드 접근으로 setter 없이 저장·복원했다. "ORM 때문에 setter가 필요하다"는 이 설정에서는 성립하지 않는다(요구사항은 02번 표).

## 쓰이는 자료구조·알고리즘

- **상태 공간 탐색(BFS)** — 상태를 정점, 공개 연산을 간선으로 보면 "불법 상태에 도달할 수 있나"는 그래프 도달성 문제다(실험 B). [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)
- **무작위 탐색(퍼징)** — 실험 A는 공개 API를 무작위로 부르는 속성 기반 테스트의 축소판이다. 상태가 많아 BFS가 어려울 때 쓴다.
- **방어적 복사** — 내부 컬렉션은 `List.copyOf`·`Collections.unmodifiableList`로 내준다. 실험 A에서 컬렉션 노출(`getLines().add`)이 I2 위반의 첫 원인 4,171건이었다. [languages/java/syntax/40](../../../languages/java/syntax/40-list-set-and-immutable-factories/2-summary.md)
- **상태 기계** — 풍부 모델의 의도 메서드는 상태 전이 표의 간선이다. 표로 명시하는 법은 11번. [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 빈약 모델을 풍부하게 — 리팩터링 순서

1. 진단: Vernon의 두 질문, 그리고 setter 호출처를 센다.

```bash
grep -rnE "\.set(Status|Paid|Shipped|Total)\(" src/main/java | grep -v "/domain/" | wc -l
grep -rnE "\.get(Lines|Items)\(\)\.(add|remove|clear)\(" src/main/java
```

2. 의도 메서드를 만든다: 서비스에 있던 "검사 + setter 묶음"을 `Order.ship()`처럼 한 메서드로 옮긴다.
3. 호출처를 의도 메서드로 바꾼다. 한 번에 하나씩, 테스트를 돌리며.
4. setter 가시성을 줄인다: `public` → 패키지 비공개 → 삭제. 컴파일 오류가 남은 호출처를 알려 준다.
5. 컬렉션은 복사본·읽기 전용 뷰만 내준다.
6. 불법 상태 테스트를 추가한다: "결제 전 배송은 거절된다", "결제 뒤 줄 추가는 거절된다".

### 2. 풍부 모델 + JPA (실험 C의 모양)

```java
@Entity
public class Order {
    @Id private Long id;                                    // 필드 접근
    @Enumerated(EnumType.STRING) private Status status = Status.NEW;
    @ElementCollection private List<Long> lines = new ArrayList<>();
    private long total;

    protected Order() {}                                     // JPA 전용
    public Order(Long id) { this.id = id; }

    public void addLine(long amount) {
        if (status != Status.NEW) throw new IllegalStateException("결제 뒤 변경 불가");
        if (amount <= 0) throw new IllegalArgumentException("금액은 양수");
        lines.add(amount); total += amount;
    }
    public void pay() {
        if (lines.isEmpty() || status != Status.NEW) throw new IllegalStateException("결제할 수 없음");
        status = Status.PAID;
    }
    public List<Long> lines() { return List.copyOf(lines); }
}
```

- Lombok: 도메인 엔티티에 `@Data`·`@Setter`를 쓰지 않는다(원본 [pojo](../pojo/2-summary.md) 「현대 자바」). `@Getter`도 컬렉션 필드에는 복사본 getter를 직접 쓴다.

### 3. 빈약 모델이 맞는 자리

- 지켜야 할 불변식이 없는 데이터: 설정값 CRUD, 조회 전용 읽기 모델, 계층·시스템 경계를 넘는 DTO(원본 [domain-vs-application-logic](../domain-vs-application-logic/2-summary.md) 「더 알면 좋은 것」).
- Evans 4장은 업무 규칙이 적고 데이터 입력·표시가 대부분인 단순한 프로젝트에는 Smart UI 같은 단순한 접근이 맞을 수 있다고 쓴다(07번).
- 판단 기준: "이 객체의 필드 사이에, 또는 상태 변화에 지켜야 할 규칙이 있나?" 없으면 DTO로 두고 "도메인 모델"이라 부르지 않는다.

### 4. DB 제약을 마지막 방어선으로

- 풍부 모델이어도 배치 SQL·다른 서비스·수동 수정이 DB를 직접 바꿀 수 있다. 단순한 불변식은 DB에도 건다.

```sql
ALTER TABLE orders ADD CONSTRAINT shipped_requires_paid CHECK (NOT shipped OR paid);   -- I1
```

## 장애 시나리오와 대처

### 1. setter로 불법 상태 저장 (⚠ 커리큘럼)

- **현상**: "결제 안 됐는데 배송됨", "취소됐는데 배송됨" 주문이 DB에 있다. 정산·배송 집계가 어긋난다.
- **보이는 형태**: `select count(*) from orders where shipped and not paid` 가 0이 아니다. 어느 코드가 썼는지 로그로 추적이 안 된다.
- **원인**: 상태 setter가 공개돼 있었고, 어떤 코드(관리 도구, 배치, 테스트 데이터 스크립트)가 서비스를 거치지 않고 썼다. 실험 A에서 `setShipped`가 I1을 처음 깬 경우가 1,679건이었다.
- **대처**: 의도 메서드로 바꾸고 setter를 닫는다. DB `CHECK` 제약을 건다. 기존 불법 행은 원천 기록(결제·배송 이벤트)으로 판정해 업무 담당자와 정정한다.

### 2. 컬렉션 노출로 합계 불일치

- **현상**: 주문 합계(`total`)와 주문 줄 합이 다르다. 결제 금액과 영수증 금액이 어긋난다.
- **보이는 형태**: `select o.id from orders o join order_line l on … group by o.id, o.total having o.total <> sum(l.amount)`에 행이 나온다.
- **원인**: `getLines()`가 내부 목록을 그대로 돌려줘 호출자가 `add`했고, 합계 갱신 규칙을 지나지 않았다(실험 A: I2의 첫 원인 4,171건). 또는 `setTotal`을 따로 불렀다(3,871건).
- **대처**: 합계는 줄에서 계산하거나 줄을 바꾸는 메서드 안에서만 갱신한다. 컬렉션은 복사본만 내준다.

### 3. 서비스마다 다른 규칙 사본

- **현상**: 같은 "배송 가능" 판정이 서비스 A와 B에서 다르다.
- **보이는 형태**: `if (o.isPaid() && !o.isShipped() …)` 같은 조건식이 여러 서비스에 조금씩 다르게 있다.
- **원인**: 규칙이 객체가 아니라 호출자에 있어서 복사됐고, 사본이 따로 고쳐졌다(01번 실험의 구조).
- **대처**: 판정을 `Order.canShip()`·`ship()`으로 하나만 둔다. 사본 위치를 `grep`으로 찾아 모두 그 메서드로 바꾼다.

### 4. 반대 방향 — 풍부 모델 과잉

- **현상**: 단순 CRUD 화면 하나에 엔티티·값 객체·팩토리·리포지토리·매퍼가 줄줄이 생긴다. 필드 하나 추가에 파일 여러 개를 고친다.
- **보이는 형태**: 엔티티 메서드가 setter와 하는 일이 같다(`rename(String n) { this.name = n; }`만 있다). 07번 실험에서 공지 제목 수정 하나가 5파일 23줄 vs 1파일 5줄이었다.
- **원인**: 지켜야 할 불변식이 없는 데이터에 도메인 모델 구조를 씌웠다.
- **대처**: 불변식이 없으면 단순한 구조(Transaction Script·DTO)로 둔다. 규칙이 생기는 시점에 그 부분만 풍부하게 옮긴다(07번).

### 5. 풍부 엔티티가 외부 의존을 끌어들인다

- **현상**: "행위를 객체에" 하다 보니 엔티티가 리포지토리·HTTP 클라이언트·메일 발송기를 주입받는다.
- **보이는 형태**: 엔티티 생성에 스프링 빈이 필요하다. 엔티티 테스트에 목이 많다.
- **원인**: 업무 판단과 흐름(외부 호출·알림)을 구분하지 않고 둘 다 엔티티로 옮겼다.
- **대처**: 엔티티에는 자기 상태에 관한 판단만 둔다. 외부 조회가 필요한 규칙은 값을 인자로 받거나 도메인 서비스로, 흐름은 애플리케이션 서비스로 둔다(01·02번).

## 핵심 문장

- 빈약 모델은 관계·구조는 있고 행위가 없는 "getter·setter 가방"이다. Fowler는 데이터와 처리를 함께 묶는 객체 지향의 기본 생각과 정반대라고 본다.
- 빈약 모델에서 규칙은 "모두가 서비스를 거친다"는 약속에 기댄다. 풍부 모델에서는 "객체에 다른 문이 없다"는 구조가 지킨다.
- 실험에서 setter와 컬렉션이 열린 빈약 모델은 무작위 1만 시퀀스 중 9,974개가 불변식을 깼다. 서비스만 부른 경우와 풍부 모델은 0이었다.
- 도달 가능한 추상 상태는 빈약 모델 32개 전부, 풍부 모델 7개였다. 불법 상태를 만들 수 없으면 검사를 잊을 수도 없다.
- 지켜야 할 불변식이 없는 데이터는 빈약한 구조가 맞다. 판단 기준은 "규칙이 있는가"다.

## 관련 주제·근거

- 선행: [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) — 불변식과 일관성 경계
- 연결
  - [01-domain-vs-application-logic](../01-domain-vs-application-logic/2-summary.md) — 규칙 사본 실험
  - [02-pojo-and-persistence-ignorance](../02-pojo-and-persistence-ignorance/2-summary.md) — JPA 엔티티 요구사항
  - [07-domain-logic-patterns-and-service-layer](../07-domain-logic-patterns-and-service-layer/2-summary.md) — 빈약 모델 = Transaction Script, 선택 기준
  - [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md) — 의도 메서드를 전이 표로
  - 원본 [pojo](../pojo/2-summary.md) 「안티패턴 — 빈약한 도메인 모델」 · 원본 [domain-vs-application-logic](../domain-vs-application-logic/2-summary.md) 「여기에 비즈니스 규칙이 새어나오는 신호」
  - [software-design/06-clean-code](../../software-design/06-clean-code/2-summary.md)(Tell, Don't Ask) · [software-design/19-immutability-and-value-objects](../../software-design/19-immutability-and-value-objects/2-summary.md) · [software-design/23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md) · [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md) · [software-design/31-antipatterns](../../software-design/31-antipatterns/2-summary.md)
  - [database/02-keys-and-constraints](../../database/02-keys-and-constraints/2-summary.md) — `CHECK` 제약
- 근거
  - Fowler "AnemicDomainModel"(2003-11-25) <https://martinfowler.com/bliki/AnemicDomainModel.html>
  - Vernon 『Implementing Domain-Driven Design』(2013) 1장 Getting Started with DDD — InformIT 발췌 "Getting Started with Domain-Driven Design"(2012-11-09), 진단 질문·원인·"Anemia and Memory Loss" <https://www.informit.com/articles/article.aspx?p=1944876&seqNum=2>
  - Evans 『DDD』 4장(애플리케이션 계층 정의, Smart UI) — 2003 최종 원고 PDF 대조
  - Hibernate ORM 6.6 User Guide §3.4(필드 접근, 인자 없는 생성자) <https://docs.hibernate.org/orm/6.6/userguide/html_single/Hibernate_User_Guide.html>
- 실험 목록
  - A. 무작위 호출 퍼징(1만 시퀀스 × 20호출, seed 42): 빈약(setter 포함) 9,974 / 빈약(서비스만) 0 / 풍부 0(거절 126,938), 첫 위반 원인 분포
  - B. 추상 상태 BFS: 도달 32/32(불법 17) vs 7/32(불법 0)
  - C. setter 없는 엔티티 Hibernate 6.6.29 + H2 2.3.232 저장·복원, 복원 뒤 규칙 유지, `set*` 메서드 0개
  - 공통: JDK 21.0.12(temurin), `--cpus=2`·네트워크 없음
