# software-design/26-functional-core-imperative-shell — 함수형 코어, 명령형 셸 — 정리 (힌트)

## 해결하는 문제

할인 규칙 하나를 시험하고 싶은데, 그 규칙이 저장소 호출 사이에 끼어 있다.

```text
 checkout(orderId)
   order    = orderRepo.find(id)          ← I/O
   customer = customerRepo.find(..)       ← I/O
   coupon   = couponRepo.find(..)         ← I/O
   if VIP → 10% 할인                       ← 규칙
   if 쿠폰 유효(오늘 기준) → 차감          ← 규칙 + 시계
       couponRepo.markUsed(..)            ← I/O
   orderRepo.saveTotal(..)                ← I/O
   events.publish(..)                     ← I/O
 규칙 두 줄을 보려면 I/O 여섯 개를 흉내 내야 한다
```

- *순수 함수(pure function)*: 같은 입력에 늘 같은 값을 돌려주고, 바깥에 아무것도 바꾸지 않는 함수. DB·시계·난수를 건드리지 않는다.
- *부수 효과(side effect)*: 반환값 말고 바깥 세계를 바꾸거나 읽는 것. 저장·발행·현재 시각 읽기.
- *함수형 코어, 명령형 셸(Functional Core, Imperative Shell)*: Gary Bernhardt가 2012년 같은 이름의 스크린캐스트(2012-07-12 공개)와 SCNA 2012 발표 "Boundaries"에서 제시한 구조. 결정은 순수한 코어에, 부수 효과는 얇은 셸에 둔다.

쉬운 예: 식당 주문이다. 주방장(코어)은 재료를 받아 요리를 내놓기만 한다. 장보기·서빙·계산(셸)은 홀 직원이 한다. 주방장의 솜씨를 보려면 재료만 주면 된다.\
똑같은 구조다.\
실무 예: 결제·정산의 요금 계산, 재고 할당, 쿠폰 적용, 권한 판정. 같은 계산을 API와 배치가 함께 쓴다.

25(DI)가 "의존을 바깥에서 넘겨 준다"라면, 이것은 "**결정하는 코드는 의존을 아예 갖지 않는다**"다. Seemann은 이를 *의존성 거부(dependency rejection)* 라 부른다.

## 동작·원리

### 1. 샌드위치 — 읽기 → 결정 → 쓰기

```text
 ┌───────────── 셸 (명령형, 얇게) ─────────────┐
 │ 1. 읽기   order, customer, coupon, today    │  ← I/O·시계는 여기서만
 │           │ 값으로 넘김                     │
 │           v                                 │
 │ ┌──── 코어 (순수) ──────────────────────┐   │
 │ │ decide(order, customer, coupon, today) │   │  ← 분기·계산이 전부 여기
 │ │   → Decision(total, [명령, 명령, …])   │   │
 │ └────────────────────────────────────────┘   │
 │           │ 결정(값)을 돌려받음             │
 │           v                                 │
 │ 3. 쓰기   명령을 하나씩 실행 (save, markUsed, publish)
 └─────────────────────────────────────────────┘
```

- Seemann은 이 모양을 *impureim sandwich*(불순–순수–불순 샌드위치)라 이름 붙였다("Impureim sandwich", 2020). 그 글은 2017년 1월부터 이 구조를 말해 왔다고 적는다.
- 코어에는 분기가 많고 협력 객체가 없다. 셸에는 협력 객체가 많고 분기가 거의 없다.

```text
            분기·결정 많음
                 ^
       코어      │   (피할 곳: 분기도 많고 협력 객체도 많음)
   ──────────────┼──────────────> 협력 객체(I/O) 많음
       값 객체   │      셸
```

- Khorikov 『Unit Testing Principles, Practices, and Patterns』(Manning 2020) 7장이 코드를 네 종류로 나누고 Humble Object 패턴으로 "복잡하면서 협력 객체도 많은" 코드를 쪼갠다(livebook 7장 머리 「This chapter covers」 확인). 축의 정확한 이름은 본문을 확인하지 못했다 [?].
- *Humble Object*: 시험하기 어려운 부분(I/O)을 로직이 없는 얇은 껍질로 남기고, 로직은 시험하기 쉬운 객체로 빼는 패턴.

### 2. 결정을 명령 값으로 돌려준다

```java
sealed interface Cmd permits SaveTotal, MarkUsed, Publish {}
record SaveTotal(long orderId, long total) implements Cmd {}
record MarkUsed(String code) implements Cmd {}
record Publish(String event) implements Cmd {}
record Decision(long total, List<Cmd> commands) {}

// 코어: 값만 받고 값만 돌려준다. I/O·시계 없음
static Decision decide(Order o, Customer c, Coupon cp, LocalDate today) {
    long total = o.amount();
    if ("VIP".equals(c.grade())) total = total * 90 / 100;
    List<Cmd> cmds = new ArrayList<>();
    if (cp != null && !cp.used() && !today.isAfter(cp.expires())) {
        total = Math.max(0, total - cp.off());
        cmds.add(new MarkUsed(cp.code()));
    }
    cmds.add(new SaveTotal(o.id(), total));
    cmds.add(new Publish("checked-out:" + o.id() + ":" + total));
    return new Decision(total, cmds);
}

// 셸: 읽기 → 결정 → 쓰기
long checkout(long orderId) {
    Order o = orders.find(orderId);
    Coupon cp = o.couponCode() == null ? null : coupons.find(o.couponCode());
    Customer c = customers.find(o.customerId());
    Decision d = decide(o, c, cp, LocalDate.now(clock));
    for (Cmd cmd : d.commands()) switch (cmd) {
        case SaveTotal s -> orders.saveTotal(s.orderId(), s.total());
        case MarkUsed m  -> coupons.markUsed(m.code());
        case Publish p   -> events.publish(p.event());
    }
    return d.total();
}
```

- "쿠폰을 쓴 것으로 표시하라"는 **부수 효과가 아니라 값**(`MarkUsed`)이다. 테스트는 그 값이 목록에 있는지만 본다.
- `sealed` + 패턴 매칭 `switch`(JDK 21)라 명령 종류를 하나 추가하면 셸의 `switch`가 컴파일 오류로 알려 준다. 패턴을 쓰는 `switch` 문도 빠짐없어야 한다(JEP 441). 점검 때 case 하나를 뺀 판을 JDK 21 `javac`로 컴파일하자 `error: the switch statement does not cover all possible input values`가 났다.
- 시계는 코어에 들어가지 않는다. 셸이 `LocalDate.now(clock)`을 읽어 **값**으로 넘긴다.

### 실험 A: 같은 규칙, 두 구조 — 목 개수와 리팩터링 내성

판 1은 위 「해결하는 문제」 그림처럼 계산이 I/O 사이에 있다. 판 2는 위 코드다. 두 판의 `checkout` 결과 값은 같다.\
테스트 대상 규칙: VIP 10% 할인 후 1,000원 쿠폰 차감 → 10,000원 주문이 8,000원.

```java
// 판 1 테스트: 협력 객체를 다 흉내 내고 호출 순서까지 검증
OrderRepo orders = mock(OrderRepo.class); CustomerRepo customers = mock(CustomerRepo.class);
CouponRepo coupons = mock(CouponRepo.class); Events events = mock(Events.class);
when(orders.find(1L)).thenReturn(new Order(1, 7, 10_000, "C10"));
...
InOrder in = inOrder(orders, customers, coupons, events);
in.verify(orders).find(1L); in.verify(customers).find(7L); in.verify(coupons).find("C10"); ...

// 판 2 코어 테스트: 값 넣고 값 확인
Decision d = decide(new Order(1, 7, 10_000, "C10"), new Customer(7, "VIP"),
                    new Coupon("C10", 1_000, LocalDate.of(2026, 12, 31), false), LocalDate.of(2026, 10, 2));
check(d.total() == 8_000);
check(d.commands().equals(List.of(new MarkUsed("C10"), new SaveTotal(1, 8_000), new Publish("checked-out:1:8000"))));
```

그다음 판 1에 **무해한 리팩터링**을 한다: 쿠폰을 고객보다 먼저 읽도록 순서만 바꾼다(결과 값은 같다).

(실험, JDK 21.0.12 temurin `--cpus=2`, Mockito 5.20.0, `scratchpad/sd/25/e26/src/Fcis.java`, 2026-10-02)

```text
[리팩터링 전]
  판1 상호작용 테스트                        PASS  (목 4개)
  판2 코어 테스트                          PASS  (목 0개)
[리팩터링 후 — 쿠폰을 고객보다 먼저 읽게 순서만 바꿈, 결과 값은 같다]
  판1 상호작용 테스트                        FAIL  (목 4개) VerificationInOrderFailure: Verification in order failure / Wanted but not invoked: / couponRepo.find("C10");
  판2 코어 테스트                          PASS  (목 0개)
```

- 판 1 테스트는 동작이 같은데 깨졌다. 테스트가 **결과가 아니라 구현 순서**에 묶였다. Khorikov는 이것을 좋은 테스트의 속성 중 *리팩터링 내성(resistance to refactoring)* 이 낮다고 부른다(livebook 7장 서두가 4장의 네 속성을 다시 든다).
- 판 2 코어 테스트는 목이 0개이고 셸의 읽기 순서와 무관했다.
- 판 2의 셸은 여전히 I/O를 한다. 셸은 분기가 거의 없어 소수의 통합 테스트로 덮는다(이 실험에서는 셸 테스트를 쓰지 않았다).

### 실험 B: 같은 계산을 배치에서 재사용

(같은 실행, 저장소·시계 없이 코어만 호출)

```text
[배치 재사용 — 코어만 호출, 저장소·시계 없음]
  order 10 → total=45000 cmds=[SaveTotal[orderId=10, total=45000], Publish[event=checked-out:10:45000]]
  order 11 → total=0 cmds=[MarkUsed[code=C5], SaveTotal[orderId=11, total=0], Publish[event=checked-out:11:0]]
  order 12 → total=20000 cmds=[SaveTotal[orderId=12, total=20000], Publish[event=checked-out:12:20000]]
```

- 배치는 데이터를 한 번에 읽어 맵에 두고 코어를 부른다. 명령 목록을 모아 한꺼번에 쓸 수도 있다.
- 쿠폰이 금액보다 크면 0원(`Math.max(0, …)`), 만료 쿠폰(`OLD`)은 쓰지 않았다 — 같은 규칙이 API·배치에서 같은 답을 낸다.

### 3. 이 구조가 손해인 때

- **결정 중간에 더 읽어야 할 때**: "재고가 없으면 다른 창고를 조회"처럼 다음 I/O가 결정 결과에 달려 있으면 샌드위치 한 겹으로 안 된다. 셸을 여러 겹(읽기–결정–읽기–결정–쓰기)으로 나누거나, 필요한 데이터를 미리 넉넉히 읽는다.
  - Seemann도 "Dependency rejection"(2017)에서 이 리팩터링이 "놀랄 만큼 자주" 되지만 항상 된다고 주장하지는 않는다고 적었다.
- **미리 읽기의 비용**: 쓰지 않을 수도 있는 데이터까지 읽는다(쿼리·메모리 증가).
- **규칙이 거의 없는 CRUD**: 코어가 비어 있으면 명령 값 타입만 늘어난다. 이때는 셸만 두는 편이 단순하다(12 simple-design-and-yagni의 균형).

## 쓰이는 자료구조·알고리즘

- **값 파이프라인(map/filter/fold)** — 코어 안의 계산은 불변 값을 받아 새 값을 만드는 단계의 연결이다. 주문 목록 → 할인 적용(map) → 0원 제외(filter) → 합계(fold).
- **명령 값 목록(Command 반환)** — 결정을 `List<Cmd>`로 돌려준다. GoF Command가 "요청을 객체로" 만든 것과 같은 발상이고, 실행은 셸이 한다. 원본 [design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) 「14. Command」.
- **합 타입(sealed interface) + 패턴 매칭 디스패치** — 명령 종류를 닫힌 집합으로 두고 셸의 `switch`가 빠짐없이 처리하는지 컴파일러가 본다. 24 types-as-invariants.
- **불변 값(record)** — 코어의 입력·출력이 바뀌지 않아야 "같은 입력 → 같은 출력"이 성립한다. 19 immutability-and-value-objects.

## 적용 — 풀어나가는 법

### 1. 순서

1. **규칙을 찾는다**: 서비스 메서드에서 `if`·계산이 있는 줄에 표시한다. I/O 줄과 섞여 있으면 대상이다.
2. **필요한 입력을 값으로 모은다**: 규칙이 읽는 것(엔티티 필드, 오늘 날짜, 설정 값)을 인자 목록으로 만든다. 시계·난수·UUID도 **값**으로 넘긴다.
3. **결정을 값으로 돌려준다**: 계산 결과와 "할 일"(저장·발행·표시)을 명령 값으로.
4. **셸을 샌드위치로**: 읽기 → `decide` → 명령 실행. 셸에는 분기를 두지 않는다(명령 디스패치 정도).
5. **테스트를 옮긴다**: 규칙 테스트는 코어에 목 없이. 셸은 통합 테스트 몇 개.
6. **트랜잭션 경계는 셸에**: 읽기와 쓰기가 한 트랜잭션이어야 하면 셸 메서드에 경계를 둔다([database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md)).

### 2. TypeScript로 같은 모양

```typescript
type Cmd = { kind: "save"; orderId: number; total: number }
         | { kind: "markUsed"; code: string }
         | { kind: "publish"; event: string };

// 코어
export function decide(o: Order, c: Customer, cp: Coupon | null, today: string): { total: number; cmds: Cmd[] } { /* … */ }

// 셸
export async function checkout(id: number, deps: Deps) {
  const o = await deps.orders.find(id);
  const [c, cp] = await Promise.all([deps.customers.find(o.customerId), o.couponCode ? deps.coupons.find(o.couponCode) : null]);
  const { total, cmds } = decide(o, c, cp, deps.today());
  for (const cmd of cmds) await run(cmd, deps);
  return total;
}
```

- 읽기를 `Promise.all`로 병렬화해도 코어 테스트는 영향이 없다. 실험 A의 "순서만 바꾼 리팩터링"과 같은 종류의 변경이다.

### 3. 진단

```bash
# 서비스 테스트의 목·순서 검증 밀도 (예시 패턴)
grep -c 'mock(' src/test/java/**/CheckoutServiceTest.java
grep -c 'inOrder\|verify(' src/test/java/**/CheckoutServiceTest.java
# 코어 후보: 저장소 호출과 if가 한 메서드에 함께 있는 곳
grep -nE 'Repository|Repo\.' -A3 src/main/java/**/CheckoutService.java | grep -n 'if ('
```

- 규칙 테스트 하나에 목이 여러 개이고 `verify`가 `assert`보다 많으면 결정이 I/O에 섞인 것이다.

## 장애 시나리오와 대처

### 1. 규칙 하나 테스트에 목 여러 개 + 순서 검증 → 리팩터링마다 대량 실패 (⚠ 커리큘럼)

- 현상: 쿼리 순서를 바꾸거나 두 조회를 하나로 합쳤을 뿐인데 테스트 수십 개가 빨갛게 된다. 동작은 그대로다.
- 보이는 형태: `VerificationInOrderFailure … Wanted but not invoked`, `TooManyActualInvocations`(실험 A의 판 1).
- 원인: 할인 계산이 리포지토리 호출 사이에 끼어, 테스트가 결과 대신 호출 순서를 검증한다(깨지기 쉬운 테스트).
- 대처: 계산을 순수 함수로 빼고 값으로 검증한다. 남는 상호작용 검증은 "외부에 보이는 부수 효과"(발행된 메시지, 저장된 값)로 줄인다.

### 2. 같은 계산이 배치·API에서 부수 효과와 엉켜 재사용 불가 (⚠ 커리큘럼)

- 현상: 정산 배치가 API의 할인 로직을 못 써서 복사본을 만든다. 시간이 지나 두 결과가 달라진다.
- 보이는 형태: 같은 주문에 대해 API 화면 금액과 정산 금액이 다르다. 코드 검색에 비슷한 계산이 두 곳.
- 원인: 계산이 "한 건 조회 → 계산 → 한 건 저장" 서비스 메서드 안에 갇혔다. 배치는 대량 조회가 필요해 그 메서드를 못 부른다.
- 대처: 코어 `decide`를 꺼내 API 셸과 배치 셸이 함께 부른다(실험 B).

### 3. 시계·난수 직접 호출 → 재현 불가 버그 (⚠ 커리큘럼)

- 현상: "어제 밤 11시 59분 주문만 쿠폰이 안 먹었다". 재현이 안 된다.
- 보이는 형태: 특정 시각·특정 난수에서만 나는 실패. 로그에는 입력이 다 같아 보인다.
- 원인: 코어가 `LocalDate.now()`·`Math.random()`을 스스로 읽어 입력이 로그에 남지 않았다.
- 대처: 셸이 시각·난수를 읽어 값으로 넘기고, 결정 입력을 로그에 남긴다. 그러면 같은 입력으로 코어를 다시 돌려 재현할 수 있다.

### 4. 코어에 I/O가 다시 새어 들어온다

- 현상: 몇 달 뒤 `decide`가 "VIP 등급은 캐시에서 확인"하며 저장소를 받는다. 코어 테스트에 다시 목이 생긴다.
- 보이는 형태: 코어 파일의 import에 `Repository`·`Clock`·HTTP 클라이언트가 보인다.
- 원인: 경계가 관례로만 지켜졌다.
- 대처: 코어 패키지가 인프라 패키지에 의존하지 못하게 규칙으로 막는다(ArchUnit — 41 architecture-fitness-rules).

## 핵심 문장

- 결정은 순수 함수(코어)가, 읽기·쓰기·시계는 얇은 셸이 한다. 모양은 읽기 → 결정 → 쓰기 샌드위치다.
- 결정은 부수 효과가 아니라 명령 값으로 돌려준다. 테스트는 그 값만 본다.
- 실험에서 같은 규칙의 테스트가 판 1은 목 4개, 판 2 코어는 목 0개였다. 읽기 순서만 바꾸자 판 1 테스트만 깨졌다.
- 코어는 저장소 없이 불리므로 API와 배치가 같은 계산을 공유한다.
- 결정 도중에 더 읽어야 하면 샌드위치가 여러 겹이 되거나 미리 읽기 비용이 생긴다. 규칙이 거의 없는 CRUD에서는 이득이 작다.

## 관련 주제·근거

- 선행
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 의존을 받는 법. 이 주제는 결정 코드에서 의존을 없애는 법
  - [24-types-as-invariants](../24-types-as-invariants/2-summary.md)
  - language/18-functional-concepts — 미작성([language README](../../language/README.md))
- 후속·연결
  - [testing/10-testing-time-and-concurrency](../../testing/10-testing-time-and-concurrency/2-summary.md)
  - [19-immutability-and-value-objects](../19-immutability-and-value-objects/2-summary.md), [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md), [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md)
  - [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md) — 셸에 둘 트랜잭션 경계
- 글·문서
  - Gary Bernhardt, "Boundaries", SCNA 2012 발표 — 단순한 값을 컴포넌트 경계로 쓰기, 목 유무의 격리 테스트 <https://www.destroyallsoftware.com/talks/boundaries> · 스크린캐스트 "Functional Core, Imperative Shell"(2012-07-12, Ruby) <https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell>
  - Mark Seemann, "Dependency rejection"(2017-02-02) — "함수형 프로그래밍에서는 의존이라는 개념을 거부해야 한다", 항상 가능하다고는 주장하지 않음 <https://blog.ploeh.dk/2017/02/02/dependency-rejection/> · "Impureim sandwich"(2020) <https://blog.ploeh.dk/2020/03/02/impureim-sandwich/>
  - Vladimir Khorikov, 『Unit Testing Principles, Practices, and Patterns』(Manning, 2020) 7장 "Refactoring toward valuable unit tests" — 네 종류의 코드, Humble Object(livebook 7장 서두·절 목록 확인, 본문 세부는 [?]) <https://livebook.manning.com/book/unit-testing/chapter-7>
- 실험 목록 (코드: scratchpad `sd/25/e26/src/Fcis.java`, JDK 21.0.12 temurin 컨테이너 `--cpus=2`, Mockito 5.20.0 jar)
  - A 같은 할인 규칙: I/O 사이에 낀 판(목 4개, `InOrder`) vs 코어(목 0개), 읽기 순서만 바꾼 리팩터링 후 판 1만 실패
  - B 코어를 배치에서 저장소 없이 호출 — 주문 3건의 결과·명령 목록
