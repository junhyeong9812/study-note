# domain-modeling/pojo — 정리 (힌트)

> 복습은 [1-question.md](1-question.md)에서 시작하고, 막힐 때만 이 파일을 힌트로 연다.\
> 원고 출처: `jun-bank/docs/study/notes/09-pojo.md` (원본 개념 노트) · 이관일 2026-09-16.\
> 본문 각 절은 **원고**를 고쳐 쓴 것이다(문체·순서 유지). 내부 교재 매핑(축별 문서 링크)은 제거하고, 개념 연결은 「관련 자료」로 일반화했다.\
> 「한눈에」·「전체 흐름」의 비유와 그림은 **Claude가 원고 이해를 돕기 위해 새로 그린 것**이며, 원고에 없던 지식은 맨 끝 `[Claude 추가]`에만 둔다.

**한 줄 정의: 특정 프레임워크에 묶이지 않은, 그냥 평범한 자바 객체(Plain Old Java Object).**\
중요한 건 "무엇인가"보다 **"무엇이 아닌가"**다. POJO는 정의가 아니라 **반대 개념으로 태어난 말**이다.

---

## 한눈에 — 쉽게 말하면

**콘센트에 꽂아야만 켜지는 가전 vs 건전지로 도는 손전등**을 떠올리면 된다. *(Claude 보강 — 원고에 없는 비유)*

```text
프레임워크 종속 객체            POJO
+----------------------+      +----------------------+
| 특정 콘센트에만 꽂힘    |      | 건전지로 켜짐          |
| 그 컨테이너 없으면 죽음 |      | 어디서나 켜본다        |
+----------------------+      +----------------------+
  → 컨테이너 띄워야 테스트        → new 로 만들어 바로 테스트
```

**코드도 똑같은 구조다.** 옛 EJB 객체는 프레임워크 인터페이스를 구현해야 해서 컨테이너(콘센트) 없이는 실행도 테스트도 못 했다.\
POJO는 아무것도 상속·구현하지 않아 `new`로 만들어 바로 돌린다 — 건전지 손전등처럼 콘센트가 없어도 켜진다.

쉽게 말하면 이렇다.\
**POJO는 형태 규칙(getter/setter가 있어야 한다 같은)이 아니라 "무엇에도 종속되지 않는다"는 태도다.** 그래서 판별 질문은 단 하나 — "컨테이너 없이 `new`로 만들어 테스트할 수 있는가."

---

## 문제 — 이 개념이 답하려는 질문

이 주제에는 풀 코드 과제가 없다(개념 정리다). 대신 하나의 역사적 곤경에 답한다.

2000년 무렵 자바 엔터프라이즈의 표준은 **EJB(Enterprise JavaBeans)**였고, 비즈니스 로직 하나를 짜려면 이랬다.

```java
// 옛 EJB 스타일 — 프레임워크가 코드를 지배한다
public class OrderBean implements javax.ejb.SessionBean {
    public void ejbCreate() { }
    public void ejbRemove() { }
    public void ejbActivate() { }
    public void ejbPassivate() { }
    public void setSessionContext(SessionContext ctx) { }

    public void placeOrder(...) {
        // ← 진짜 비즈니스 로직은 여기 한 줄
    }
}
```

문제는 셋이다.

- 프레임워크 인터페이스를 구현해야 해서 **컨테이너 없이는 실행도 테스트도 불가능.**
- 비즈니스 로직이 프레임워크 코드에 파묻힌다.
- 프레임워크를 바꾸면 전부 다시 써야 한다.

Martin Fowler·Rebecca Parsons·Josh MacKenzie는 **"그냥 평범한 객체에 로직을 담자"**고 주장했다. "평범한 객체"라 하면 아무도 안 쓸 것 같아 **멋있어 보이는 이름을 붙였고**, 그게 POJO다.

> 원문 취지: "우리는 왜 그냥 객체를 쓰는 걸 반대하는지 이해할 수 없었다. 이름이 없어서 인기가 없는 것 같아 POJO라는 이름을 붙였고, 훨씬 잘 먹혔다."

**핵심: POJO는 기술 스펙이 아니라 설계 태도를 가리키는 말이다.** 아래 서머리는 이 태도를 판별법·오해·실익으로 나눠 정리한 것이다.

---

## 전체 흐름

POJO는 반대 개념에서 태어나, 스프링이 실현했고, 오해하면 안티패턴으로 무너진다.

```text
EJB (프레임워크가 코드를 지배 — 침투적)
        ↓  "그냥 평범한 객체에 로직을 담자"
POJO (아무것도 상속/구현 안 함 — new로 테스트 가능)
        ↓  스프링이 IoC + AOP로 실현
평범한 객체에 트랜잭션·보안을 바깥에서 감싼다
        ↓  오해하면
"로직 없는 데이터 덩어리" → 빈약한 도메인 모델 (안티패턴)
```

---

## 판별법 — 무엇이 POJO가 아닌가

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 2절

**언제 쓰나** — 어떤 클래스를 두고 "이게 POJO인가?"를 판정할 때.

```java
// POJO 아님 — 프레임워크 클래스를 상속
public class UserService extends AbstractServiceSupport { }

// POJO 아님 — 프레임워크 인터페이스를 구현
public class OrderBean implements SessionBean { }

// POJO 아님 — 프레임워크 규약에 종속된 생명주기 메서드 강제
public class Job implements InitializingBean, DisposableBean { }

// POJO — 아무것도 상속/구현하지 않음
public class Order {
    private final Long id;
    private OrderStatus status;

    public void approve() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("승인 가능한 상태가 아님");
        }
        this.status = OrderStatus.APPROVED;
    }
}
```

**판별 질문 하나** — "이 클래스를 `main()`에서 `new`로 만들어 테스트할 수 있는가?"\
컨테이너·서버·프레임워크 없이 순수 자바로 실행되면 POJO다.

**비용** — 없다시피 하다. 오히려 종속을 끊는 데서 오는 이득(아래)이 대부분이다.

---

## 혼동하기 쉬운 용어 — 짝짓기

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 3절

**언제 쓰나** — POJO·JavaBean·DTO·VO·Entity가 한 문장에 섞여 나올 때. 무엇을 기준으로 가르는지를 붙든다.

| 용어 | 정의 | **기준** |
|---|---|---|
| **POJO** | 프레임워크에 종속되지 않은 평범한 객체 | **종속성 없음** (형태 규칙 없음) |
| **JavaBean** | ① 기본 생성자 ② private 필드 + public getter/setter ③ `Serializable` | **형태 규약** (도구가 리플렉션으로 다루기 위한 규격) |
| **DTO** | 계층·시스템 간 데이터 전달용. 로직 없음 | **역할** |
| **VO(Value Object)** | 값 자체로 식별되는 불변 객체. `equals`/`hashCode`가 값 기반 | `Money`·`Address`·`Email` |
| **Entity** | 식별자(ID)로 구분되는 객체. 보통 DB 테이블과 대응 | 값이 바뀌어도 같은 객체 |
| **도메인 모델** | 비즈니스 규칙과 상태를 함께 가진 객체 | **로직이 있다** |

### 자주 하는 오해 셋

**오해 ① "POJO = getter/setter가 있는 클래스."**\
아니다. 그건 **JavaBean 규약**이다. getter/setter가 하나도 없어도 POJO이고, 오히려 **setter가 없는 불변 객체가 더 좋은 POJO**인 경우가 많다.

**오해 ② "POJO는 로직이 없는 데이터 덩어리."**\
정반대다. POJO의 원래 취지는 **"평범한 객체에 비즈니스 로직을 담자"**였다. 로직 없는 데이터 덩어리는 DTO이고, 그게 도메인 모델 자리를 차지하면 **빈약한 도메인 모델**(아래) 안티패턴이다.

**오해 ③ "POJO와 JavaBean은 같은 말."**\
교집합이 크지만 방향이 다르다.

```text
POJO      : 무엇에 의존하지 않는가   (종속성 기준)
JavaBean  : 어떤 형태를 갖추는가     (형태 기준)

→ JavaBean이면서 POJO인 경우가 대부분이지만
  둘은 서로를 함의하지 않는다.
```

---

## 왜 중요한가 — 실질적 이득 넷

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 4절

**언제 쓰나** — "POJO로 두면 뭐가 좋은데?"에 답할 때. 첫째가 압도적으로 크다.

**① 테스트 용이성 (가장 큰 이득)**

```java
// POJO라면 — 컨테이너 없이 즉시 테스트
@Test
void 승인은_대기상태에서만_가능하다() {
    Order order = new Order(1L, OrderStatus.SHIPPED);
    assertThrows(IllegalStateException.class, order::approve);
}
```

프레임워크 컨텍스트 로딩(수 초~수십 초)이 필요 없다. **테스트가 밀리초 단위로 끝나면 개발자가 실제로 돌린다.**

**② 프레임워크 독립성** — 프레임워크를 바꿔도 핵심 로직은 그대로 산다. 실제로 프레임워크를 바꾸는 일은 드물지만, **버전 업그레이드**(예: `javax` → `jakarta`)에서 차이가 크다.

**③ 이해 비용** — 읽는 사람이 **프레임워크를 몰라도 코드를 읽을 수 있다.** 신규 인원 온보딩 비용에 직결.

**④ 재사용성** — 같은 도메인 객체를 웹·배치·CLI에서 그대로 쓴다.

**비용** — 사실상 없다. 이 넷이 POJO를 고집하는 이유 전부다.

---

## 스프링과 POJO — 침투 vs 비침투

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 5절

**언제 쓰나** — "스프링을 쓰는데도 POJO인가?"라는 질문이 나올 때.

**스프링의 존재 이유 자체가 "POJO에 엔터프라이즈 기능을 주는 것"이었다.**

```text
전 (EJB, 침투적)                  후 (Spring, 비침투적)
프레임워크 인터페이스 구현            프록시 + @Transactional
컨테이너 API 호출                    AOP
JNDI 조회 코드 작성                  DI로 주입받기만
컨테이너 있어야 테스트               new 로 생성 가능
```

| | EJB (침투적) | Spring (비침투적) |
|---|---|---|
| 트랜잭션 | 프레임워크 인터페이스 구현 | **프록시 + `@Transactional`** |
| 보안 | 컨테이너 API 호출 | AOP |
| 의존성 | JNDI 조회 코드 작성 | **DI로 주입받기만** |
| 테스트 | 컨테이너 필요 | `new`로 생성 가능 |

스프링은 **IoC(제어의 역전)와 AOP(프록시)**로 이걸 해냈다. 객체는 평범한 상태로 두고, 부가 기능은 **바깥에서 감싼다.**

```java
// 코드 어디에도 스프링 API 호출이 없다
@Service
public class OrderService {
    private final OrderRepository repository;   // 생성자 주입

    public OrderService(OrderRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public void approve(Long id) {
        Order order = repository.findById(id).orElseThrow();
        order.approve();
    }
}
```

**비용(함정)** — `@Transactional`은 프록시로 동작하므로 **같은 클래스 내부 호출(self-invocation)에는 적용되지 않는다.** POJO를 유지하는 대가(프록시 기반)로 생기는 대표적 함정이다.

---

## 애노테이션이 붙으면 POJO가 아닌가 — 침투 정도 스펙트럼

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 6절

**언제 쓰나** — `@Entity`가 붙은 클래스를 두고 "이건 POJO냐"로 논쟁이 붙을 때.

```java
@Entity
@Table(name = "orders")
public class Order {
    @Id @GeneratedValue
    private Long id;
}
```

이건 POJO인가? **의견이 갈린다.**

| 입장 | 근거 |
|---|---|
| **POJO다** | 상속·구현이 없다. `new`로 만들고 테스트할 수 있다. 애노테이션은 **메타데이터**일 뿐 동작을 강제하지 않는다 |
| **POJO 아니다** | 어쨌든 JPA에 대한 컴파일 타임 의존이 생긴다. `jakarta.persistence`가 없으면 컴파일이 안 된다 |

실용적 결론은 이분법이 아니라 **침투 정도(invasiveness)의 스펙트럼**으로 보는 것이다.

```text
전혀 없음 ──────────────────────────────────▶ 완전 종속
순수 클래스   애노테이션만   인터페이스 구현   프레임워크 상속
   ↑             ↑              ↑               ↑
  이상적       실용적 타협      주의           피할 것
```

**판단 기준은 "테스트할 수 있는가"다.** 애노테이션이 붙어도 `new`로 만들어 로직을 테스트할 수 있으면 POJO의 실질적 이득은 유지된다.

**비용** — 도메인 모델(핵심 규칙)만큼은 애노테이션도 최소화하자는 게 헥사고날/클린 아키텍처의 입장이다. 대가는 도메인 모델과 JPA 엔티티를 따로 두고 매핑 코드를 쓰는 것 — **작은 프로젝트에서는 과잉**인 경우가 많다.

---

## 현대 자바에서의 모습

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 7절

**언제 쓰나** — record·Lombok·값 객체 중 무엇을 쓸지 고를 때.

**record (Java 16+) — DTO/VO에 최적**

```java
public record OrderResponse(Long id, String status, BigDecimal amount) { }
```

불변, `equals`/`hashCode`/`toString` 자동. **DTO·VO의 표준 선택지.**\
주의: **JPA 엔티티로는 못 쓴다**(기본 생성자·가변 필드 필요).

**Lombok**

```java
@Getter @Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Order { }
```

보일러플레이트 제거엔 유용하나, **`@Data`와 `@Setter`는 도메인 객체에 쓰지 않기를 권장.** 모든 필드에 setter를 열면 객체가 아무 상태로나 바뀔 수 있어 불변식이 무너진다.\
엔티티에 `@ToString`/`@EqualsAndHashCode`를 무심코 쓰면 **연관관계를 타고 가서 무한 순환·N+1**을 일으킨다.

**값 객체 활용 — 요구사항을 타입으로 짝짓기**

```java
// 원시 타입 집착 (Primitive Obsession)
public void transfer(Long from, Long to, BigDecimal amount) { }

// 값 객체
public void transfer(AccountId from, AccountId to, Money amount) { }
```

인자 순서를 바꿔 넣는 실수를 **컴파일 타임에** 막는다. 도메인 모델링에서 "요구사항 문장의 개념을 어느 타입으로 세우는가"의 실천이다.

**비용** — 값 객체가 늘면 클래스 수가 늘지만, 컴파일 타임 안전과 의미 명확성으로 갚는다.

---

## 안티패턴 — 빈약한 도메인 모델

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 8절

**언제 나오나** — POJO를 "로직 없는 데이터 덩어리"로 오해했을 때 가장 흔히 나오는 결과. Fowler가 명시적으로 비판한 안티패턴이다.

```text
전 (빈약한 모델)                     후 (규칙을 객체 안에)
데이터만 + 로직은 서비스에            상태 변경은 의미 있는 메서드로만
setStatus 아무 데서나 호출 가능        approve() 안에서만 전이
규칙이 여러 서비스에 흩어짐            규칙이 객체 한 곳에
```

```java
// 데이터만 있는 객체 + 로직은 전부 서비스에
public class Order {
    private OrderStatus status;
    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus s) { this.status = s; }
}

public class OrderService {
    public void approve(Long id) {
        Order order = repo.findById(id).orElseThrow();
        if (order.getStatus() != OrderStatus.PENDING) {   // 규칙이 여기 있다
            throw new IllegalStateException();
        }
        order.setStatus(OrderStatus.APPROVED);
    }
}
```

**무엇이 문제인가**

- 같은 규칙이 **여러 서비스에 흩어져 중복**된다(하나만 고치면 다른 곳이 남는다).
- `setStatus`가 public이라 **누구든 규칙을 우회**할 수 있다.
- 객체가 자기 불변식을 지키지 못한다 → **동시성·정합성 문제의 온상.**

```java
// 규칙을 객체 안에
public class Order {
    private OrderStatus status;

    public void approve() {
        if (status != OrderStatus.PENDING) {
            throw new IllegalStateException("승인 가능한 상태가 아님: " + status);
        }
        this.status = OrderStatus.APPROVED;
    }
    // setStatus 없음 — 상태 변경은 의미 있는 메서드로만
}
```

**비용/균형** — 모든 프로젝트가 풍부한 도메인 모델을 필요로 하지는 않는다. 단순 CRUD 위주면 빈약한 모델이 오히려 합리적이다. **문제는 복잡한 규칙이 있는데도 서비스에 흩뿌리는 경우.**

> POJO의 원래 취지는 "평범한 객체에 로직을 담자"였다. 로직을 다 빼고 getter/setter만 남기면, POJO의 이름만 쓰고 목적은 버린 것이다.

---

## 체크리스트

> 출처: `jun-bank/docs/study/notes/09-pojo.md` — 9절

- [ ] 도메인 객체가 프레임워크 클래스를 상속/구현하지 않는가
- [ ] `new`로 생성해 컨테이너 없이 테스트할 수 있는가
- [ ] 비즈니스 규칙이 서비스가 아니라 **객체 안**에 있는가
- [ ] 모든 필드에 무분별하게 setter를 열어두지 않았는가
- [ ] 불변으로 만들 수 있는 것은 불변인가 (`final`, record)
- [ ] DTO와 도메인 모델을 구분하고 있는가
- [ ] 엔티티에 `@Data`/`@ToString`을 무심코 쓰지 않았는가

---

## 핵심 문장

- **POJO는 형태 규칙이 아니라 "무엇에도 종속되지 않는다"는 태도다** — 판별 질문은 "`new`로 테스트되는가" 하나.
- **POJO는 반대 개념(EJB)에서 태어났다** — 그래서 "무엇인가"보다 "무엇이 아닌가"가 핵심.
- **POJO의 최대 실익은 테스트 용이성이다** — 밀리초에 끝나면 개발자가 실제로 돌린다.
- **POJO를 "데이터 덩어리"로 오해하면 빈약한 도메인 모델이 된다** — 원래 취지는 정반대(로직을 담자).
- **`@Transactional`은 프록시라 self-invocation에 안 걸린다** — POJO를 지키는 대가로 생긴 대표 함정.

---

## 한 문단 요약

> POJO는 특정 프레임워크에 종속되지 않은 평범한 자바 객체다. EJB처럼 프레임워크 인터페이스를 구현해야 하던 시절에 대한 반작용으로 나온 개념이라, 정의보다 **"무엇에 의존하지 않는가"**가 핵심이다. 실질적 이득은 **테스트 용이성**이다 — 프레임워크 컨텍스트를 띄우지 않고 `new`로 만들어 바로 검증하니 테스트가 빠르고, 그래서 실제로 돌리게 된다. 스프링 자체가 IoC와 AOP로 POJO에 트랜잭션 같은 기능을 얹는 방식이라 이 철학 위에 서 있다. 다만 POJO를 "로직 없는 데이터 덩어리"로 오해하면 빈약한 도메인 모델이 된다. 원래 취지는 반대로 **평범한 객체에 비즈니스 로직을 담자**는 것이었다.

---

## 관련 자료

- **CLEAN 5속성 중 A(단정적)** — "빈약한 도메인 모델"을 정면으로 다루는 형제 개념. POJO의 오해가 곧 A 속성 위반이다.
- Martin Fowler, "POJO"(martinfowler.com 용어 항목) 및 "Anemic Domain Model"(2003) — POJO의 유래와, 빈약한 도메인 모델을 안티패턴으로 지목한 원 출처. *(Claude 보강 — 실명 출처 보완)*
- 헥사고날/클린 아키텍처 — 도메인 모델을 프레임워크 애노테이션에서까지 떼어내려는 입장의 근거. 도메인·엔티티 분리와 매핑 코드의 트레이드오프. *(Claude 보강)*

---

## 용어 풀이

- **POJO(Plain Old Java Object)** — 프레임워크에 종속되지 않은 평범한 자바 객체. 종속성 없음이 기준.
- **EJB(Enterprise JavaBeans)** — 프레임워크 인터페이스 구현을 강제하던 옛 자바 엔터프라이즈 표준. 침투적.
- **JavaBean** — 기본 생성자 + private 필드 + getter/setter + `Serializable`을 갖춘 형태 규약. 도구가 리플렉션으로 다루기 위한 규격.
- **DTO(Data Transfer Object)** — 계층·시스템 간 데이터 운반용 객체. 로직 없음이 정상.
- **VO(Value Object)** — 값 자체로 식별되는 불변 객체. `equals`/`hashCode`가 값 기반.
- **Entity** — 식별자(ID)로 구분되는 객체. 값이 바뀌어도 같은 객체.
- **도메인 모델(Domain Model)** — 비즈니스 규칙과 상태를 함께 가진 객체.
- **빈약한 도메인 모델(Anemic Domain Model)** — 데이터만 있고 행위가 없는 도메인 객체. POJO를 오해한 결과.
- **IoC(제어의 역전)** — 객체 생성·연결을 프레임워크가 맡고, 코드는 주입받기만 하는 방식.
- **AOP(관점 지향 프로그래밍)** — 트랜잭션·보안 같은 부가 기능을 코드 바깥에서 프록시로 감싸 얹는 방식.
- **DI(의존성 주입)** — 필요한 협력 객체를 생성자 등으로 주입받는 것. IoC의 대표 실현.
- **self-invocation** — 같은 클래스 내부에서 자기 메서드를 호출하는 것. 프록시 기반 `@Transactional`이 이때 안 걸린다.
- **원시 타입 집착(Primitive Obsession)** — 개념을 값 객체로 세우지 않고 `Long`·`String` 같은 원시 타입으로 흘려보내는 냄새.
- **불변식(Invariant)** — 객체가 살아 있는 동안 항상 참이어야 하는 조건. 예: 상태 전이는 정해진 순서로만.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **왜 프록시가 self-invocation을 못 잡나 — 더 정확히.** 스프링은 원본 객체를 감싼 프록시 객체를 빈으로 등록한다. 외부에서 부를 때는 프록시를 거치지만, 같은 객체 안에서 `this.otherMethod()`를 부르면 프록시를 우회해 원본을 직접 부른다 — 그래서 `@Transactional`·`@Cacheable` 같은 프록시 기반 애노테이션이 안 먹는다. 우회책은 자기 자신을 주입받아 부르거나, 메서드를 별도 빈으로 분리하는 것.
- **DDD의 Aggregate와 POJO.** 도메인 주도 설계에서 애그리거트 루트는 "규칙을 담은 POJO"의 대표 형태다. `Order`가 자기 `OrderLine`들의 불변식(합계·상태 전이)을 지키는 구조가 빈약한 모델의 반대편 극단이다.
- **"Plain Old …" 계보.** POJO의 성공 이후 다른 언어에도 같은 작명이 퍼졌다 — POCO(C#), PORO(Ruby). 전부 "프레임워크가 지배하지 않는 평범한 객체"라는 같은 태도를 가리킨다.
- **record가 엔티티가 못 되는 이유 — 한 겹 더.** JPA는 프록시·더티 체킹을 위해 기본 생성자와 가변 필드가 필요한데, record는 불변이고 기본 생성자가 없다. 그래서 record는 경계 바깥(DTO·VO)에 두고, 영속화 엔티티는 별도 클래스로 두는 분리가 자연스럽다.
