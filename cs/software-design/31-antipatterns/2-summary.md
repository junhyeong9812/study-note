# software-design/31-antipatterns — 안티패턴: God Object·싱글턴 남용·Big Ball of Mud·과설계 — 정리 (힌트)

## 해결하는 문제

패턴이 "이럴 땐 이렇게 하면 된다"라면, 안티패턴은 "이렇게들 하는데 결국 손해다"다. 이름이 없으면 같은 함정을 팀마다 새로 밟는다.

```text
 문제 상황 ──> 그럴듯한 해법 ──> 당장은 동작 ──> 시간이 지나며 비용 폭증
              (전역 하나로!        (테스트 통과,     (테스트가 순서 따라 깨짐,
               한 클래스에!)        데모 성공)        병합 충돌, 수정이 딴 데를 깸)
```

- *안티패턴(anti-pattern)*: 흔히 쓰이지만 결과가 나쁜 해법. Andrew Koenig가 1995년 JOOP 칼럼 "Patterns and Antipatterns"에서 처음 썼고, 1998년 책 『AntiPatterns』(Brown 외)가 널리 알렸다(Wikipedia 「Anti-pattern」 — 원문 미열람). Koenig의 정의로 인용되는 문장: 안티패턴은 패턴과 같지만, 해법 대신 "겉보기엔 해법 같지만 아닌 것"을 준다.

쉬운 예: 집 안 물건을 전부 거실 한가운데 상자 하나에 넣는 것이다. 처음엔 찾기 쉽다. 식구가 늘고 물건이 늘면 상자 하나를 두고 다투고, 하나 꺼내다 다른 것을 쏟는다.\
똑같은 구조다.\
실무 예: 기능 대부분이 거쳐 가는 `OrderManager`(God Object), 설정·캐시·카운터를 품은 전역 싱글턴, 아무도 전체 구조를 설명 못 하는 10년 된 모놀리스(Big Ball of Mud), 구현 하나뿐인 인터페이스와 팩토리(과설계).

이 노트는 **설계 수준** 안티패턴 넷을 다룬다. 서버 운영·코드 성능 쪽 안티패턴은 [reliability/47-server-design-antipatterns](../../reliability/47-server-design-antipatterns/2-summary.md)·[reliability/48-performance-and-stability-antipatterns-in-code](../../reliability/48-performance-and-stability-antipatterns-in-code/2-summary.md)에 있다.

## 동작·원리

### 1. 안티패턴이 생기는 이유 — 힘(forces)에 대한 합리적 반응

Foote·Yoder, "Big Ball of Mud"(PLoP '97, 1997; PLoPD4 29장, 2000)는 진흙 덩어리를 게으름 탓으로만 보지 않는다. 다음 힘들에 대한 반응으로 본다.

```text
 Time(시간 없음) · Cost(구조는 비쌈) · Experience(도메인 경험 부족) · Skill(실력 차)
 Visibility(코드 구조는 눈에 안 보임) · Complexity(문제 자체가 복잡) · Change(미래 예측 실패) · Scale(규모)
        │
        v
 THROWAWAY CODE(버릴 코드가 남음) → PIECEMEAL GROWTH(조금씩 덧붙임) → KEEP IT WORKING(돌아가게만)
        │                                                              │
        └──> SHEARING LAYERS(변경 속도별로 층 분리) · SWEEPING IT UNDER THE RUG(덮어 두기) · RECONSTRUCTION(재작성)
```

- 논문의 정의: "haphazardly structured, sprawling, sloppy, duct-tape and bailing wire, spaghetti code jungle." 정보가 먼 요소들 사이에 마구 공유되어 중요한 정보가 거의 전역이 되거나 중복된다.
- 논문은 이것을 실무에서 가장 많이 배포된 "사실상의 표준" 아키텍처라고 부른다(저자 주장).
- 해석: 안티패턴을 고치려면 그것을 낳은 힘(마감·경험·보이지 않음)을 함께 다뤄야 한다. 코드만 고치면 같은 힘이 같은 모양을 다시 만든다.

### 2. God Object — 길이 다 한 클래스를 지난다

```text
 RefundController ─┐                      ┌─> OrderRepo
 CouponController ─┤                      ├─> PgClient
 SettleBatch ──────┼──> OrderManager ─────┼─> Mailer
 AdminApi ─────────┤   (필드 12, 메서드 80) ├─> CouponRepo
 WebhookHandler ───┘                      └─> SettlementRepo
   들어오는 의존(fan-in) 많음                   나가는 의존(fan-out) 많음
```

- *God Object*: 너무 많은 종류를 참조하고, 서로 관련 없는 메서드를 많이 가진 객체(Wikipedia 「God object」). Riel 『Object-Oriented Design Heuristics』(1996)의 휴리스틱 3.2 "god 클래스를 만들지 말라, 이름에 Driver·Manager·System·Subsystem이 든 추상을 의심하라"가 자주 인용된다(Wikipedia 경유, 책 미열람 [?]).
- 깨지는 방식: 서로 무관한 기능 변경이 같은 파일·같은 필드 목록을 건드린다. 병합 충돌이 잦고, 한 기능을 고치다 다른 기능을 깬다.

### 실험 A: 같은 두 기능을 God Object와 분리된 클래스에 넣고 병합

쿠폰 기능과 정산 기능을 두 브랜치에서 동시에 추가했다. God 판은 둘 다 `OrderManager`에 필드 1줄 + 메서드 1줄을 더한다. 분리 판은 각각 새 클래스를 만든다.

```java
class OrderManager {
    private OrderRepo orders;
    private PgClient pg;
    private Mailer mailer;
    // 쿠폰 브랜치: private CouponRepo coupons;          정산 브랜치: private SettlementRepo settlements;
    void place(Order o) { orders.save(o); pg.charge(o); mailer.send(o); }
    void refund(Order o) { pg.refund(o); orders.markRefunded(o); }
    // 쿠폰 브랜치: int applyCoupon(...)                 정산 브랜치: void settleDaily()
}
```

(실험, git 2.43.0 `LC_ALL=C`, 2026-10-02 — `scratchpad/sd/30/e31god/god`, `.../split`)

```text
### god
  coupon:  1 file changed, 2 insertions(+)
  settlement:  1 file changed, 2 insertions(+)
CONFLICT (content): Merge conflict in OrderManager.java
Automatic merge failed; fix conflicts and then commit the result.
### split
  coupon:  1 file changed, 4 insertions(+)
  settlement:  1 file changed, 5 insertions(+)
Merge made by the 'ort' strategy.
 1 file changed, 5 insertions(+)
```

- 줄 수로는 God 판이 더 작았다(2줄씩). 그런데 두 변경이 같은 자리(필드 목록 끝·메서드 목록 끝)에 붙어 충돌했다.
- 분리 판은 줄이 더 많았지만(4·5줄) 파일이 겹치지 않아 자동 병합됐다.
- 반대 상황: 기능이 하나뿐이고 혼자 개발하면 분리 판은 파일만 늘린다. God Object의 비용은 **동시에 바뀌는 무관한 기능 수**에 비례한다.

### 3. 싱글턴 남용 — 상태를 가진 전역

```text
 테스트 A ──set(할인 20%)──> ┌─────────────────────┐ <──read── 테스트 B ("할인 없음"을 가정)
 요청 스레드 1 ──count++──>  │ Pricing.INSTANCE    │ <──count++── 요청 스레드 2
                             │ discountRate, map,  │
                             │ quoteCount          │  ← 프로세스 하나에 하나, 누구나 쓰고 누구나 읽는다
                             └─────────────────────┘
```

- *싱글턴(Singleton, GoF)*: 인스턴스를 하나로 보장하고 전역 접근점을 주는 패턴. 기존 노트는 "상태를 가진 싱글턴 = 전역 변수"라고 정리한다([engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) 「1. Singleton」).
- 문제는 "하나"가 아니라 **"전역에서 꺼내 쓰는 가변 상태"**다. Spring 빈도 기본 스코프가 싱글턴이지만 주입으로 받고, 상태가 없으면 이 문제가 없다.

### 실험 B: 전역 싱글턴 → 테스트 순서 의존

```java
public enum Pricing {
    INSTANCE;
    private double discountRate = 0.0;                 // 테스트·요청이 공유하는 상태
    private final Map<String, Integer> lastQuote = new HashMap<>();   // 동기화 없음
    private long quoteCount = 0;                       // 동기화 없음
    public void setDiscountRate(double r) { discountRate = r; }
    public int quote(String sku, int base) {
        quoteCount++;
        int price = (int) Math.round(base * (1 - discountRate));
        lastQuote.put(sku, price);
        return price;
    }
}
class SingletonTest {
    @Test void promotionDay() { Pricing.INSTANCE.setDiscountRate(0.2); assertEquals(8000, Pricing.INSTANCE.quote("A", 10000)); }
    @Test void normalDay()    { assertEquals(10000, Pricing.INSTANCE.quote("A", 10000)); }
}
class InjectedTest {   // 고친 판: 테스트마다 새 인스턴스를 만든다
    @Test void promotionDay() { assertEquals(8000, new PricingService(0.2).quote("A", 10000)); }
    @Test void normalDay()    { assertEquals(10000, new PricingService(0.0).quote("A", 10000)); }
}
```

JUnit의 메서드 순서만 바꿔 같은 테스트를 두 번 돌렸다(`junit.jupiter.testmethod.order.default`에 `MethodName`, 그리고 이름 역순으로 정렬하는 실험용 `ReverseName`).

(실험, JUnit Platform Console Standalone 1.12.2, JDK 21.0.12 temurin `--cpus=2`, 2026-10-02 — `scratchpad/sd/30/e31/`)

```text
== 순서 A: MethodName (이름순)
    run SingletonTest.normalDay
    run SingletonTest.promotionDay
[         4 tests successful      ]
[         0 tests failed          ]
== 순서 B: ReverseName (이름 역순)
    run SingletonTest.promotionDay
    run SingletonTest.normalDay
│  │  └─ normalDay() ✘ expected: <10000> but was: <8000>
[         3 tests successful      ]
[         1 tests failed          ]
```

- 코드는 그대로인데 실행 순서만으로 결과가 바뀌었다. `promotionDay`가 남긴 할인율이 `normalDay`로 샜다.
- 주입판(`InjectedTest`)은 두 순서 모두 통과했다(실패 1건은 `SingletonTest.normalDay`).

### 실험 C: 전역 싱글턴 → 동시성 버그

4개 스레드가 각 10만 번 `quote`를 불렀다(스레드마다 다른 SKU 1,000개, 총 4,000개). 같은 일을 `AtomicLong`·`ConcurrentHashMap`을 쓴 주입판으로도 했다.

(실험, 같은 환경 `--cpus=2`, 2026-10-02 — 실행마다 다르다. 처음 5회 출력)

```text
  singleton 호출 400000 → 카운트 261412 | 키 4000 → 5106 | 예외로 끝난 스레드 0 []
  injected  호출 400000 → 카운트 400000 | 키 4000 → 4000 | 예외로 끝난 스레드 0 []
  singleton 호출 400000 → 카운트 245434 | 키 4000 → 4314 | 예외로 끝난 스레드 0 []
  injected  호출 400000 → 카운트 400000 | 키 4000 → 4000 | 예외로 끝난 스레드 0 []
  singleton 호출 400000 → 카운트 267384 | 키 4000 → 5244 | 예외로 끝난 스레드 0 []
  injected  호출 400000 → 카운트 400000 | 키 4000 → 4000 | 예외로 끝난 스레드 0 []
  singleton 호출 400000 → 카운트 281368 | 키 4000 → 4401 | 예외로 끝난 스레드 0 []
  injected  호출 400000 → 카운트 400000 | 키 4000 → 4000 | 예외로 끝난 스레드 0 []
  singleton 호출 400000 → 카운트 279636 | 키 4000 → 5450 | 예외로 끝난 스레드 0 []
  injected  호출 400000 → 카운트 400000 | 키 4000 → 4000 | 예외로 끝난 스레드 0 []
```

- `long++`은 읽기·더하기·쓰기 세 단계라 겹치면 증가분이 사라진다. 이후 15회를 더 돌린 것까지 20회에서 카운트는 219,162~303,651이었다(기대 400,000). 사실 점검 때 같은 조건으로 20회를 다시 돌리니 215,829~327,778이었다 — 합친 40회 범위는 약 21.6만~32.8만이다.
- `HashMap.size()`는 4,000이어야 하는데 3,464~5,450이 나왔다(20회 범위, 점검 재실행 20회는 3,641~6,468 — 합쳐 3,464~6,468). 4,000보다 작게도 크게도 나온다. 예외는 한 번도 안 났다 — **조용히 틀린다.** JDK 21 `HashMap` Javadoc: 이 구현은 동기화되지 않으며, 여러 스레드가 동시에 접근하고 하나라도 구조를 바꾸면 외부에서 동기화해야 한다.
- 집필 중 첫 실행(감시 없는 판, 같은 `Pricing`)은 끝나지 않았다. 2분 넘게 스레드 하나가 CPU를 쓰고, 나머지 셋은 제 몫을 끝내고 작업 큐에서 대기 중이었다. 그때 뜬 스레드 덤프:

```text
"pool-1-thread-3" #20 [262] prio=5 os_prio=0 cpu=140087.53ms elapsed=141.94s tid=0x00007d927c1127f0 nid=262 runnable  [0x00007d9258a48000]
   java.lang.Thread.State: RUNNABLE
	at java.util.HashMap$TreeNode.balanceInsertion(java.base@21.0.12/HashMap.java:2398)
	at java.util.HashMap$TreeNode.treeify(java.base@21.0.12/HashMap.java:2104)
	at java.util.HashMap$TreeNode.split(java.base@21.0.12/HashMap.java:2339)
	at java.util.HashMap.resize(java.base@21.0.12/HashMap.java:720)
	at java.util.HashMap.putVal(java.base@21.0.12/HashMap.java:669)
	at java.util.HashMap.put(java.base@21.0.12/HashMap.java:618)
	at Pricing.quote(Pricing.java:12)
```

  - 해석: 동시 `put`이 크기 조정(resize) 중 트리 버킷 구조를 망가뜨려, 트리 균형 맞추기가 끝나지 않는 루프에 빠졌다. 집필 때 이 실험 환경에서 21회 돌려 1회 나왔고, 점검 재실행 20회(5초 감시 판)에서는 한 번도 나오지 않았다 — 합쳐 41회 중 1회. 드물지만 나면 스레드 하나가 CPU 100%로 영영 돈다.
- 주입판은 출력한 5회 모두 400,000·4,000이었다(뒤 15회는 싱글턴 줄만 출력했다).

### 4. 과설계 — 오지 않은 변화를 위한 구조

```text
 요구: 배송비 = 5만 원 이상 무료, 아니면 3천 원
 과설계: ShippingFeePolicy(인터페이스) + DefaultShippingFeePolicy + ShippingFeePolicyFactory + Checkout
 단순:   ShippingFee.of(amount) + Checkout
```

- 구현이 하나뿐인 인터페이스, 한 번도 교체되지 않은 전략, 이름만 `~Factory`·`~Manager`인 클래스. 스멜 Speculative Generality가 같은 것을 가리킨다(세부와 근거는 [10-code-smells](../10-code-smells/2-summary.md)).
- 같은 변경 세 번을 두 판에 적용해 잰 결과(파일·줄 수, 할증 규칙 복제)는 [30-pattern-languages-and-catalogs](../30-pattern-languages-and-catalogs/2-summary.md) 실험 A에 있다. 판단 기준(두 번째 요구가 올 때 확장점을 만든다)은 [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **의존 그래프의 차수** — God Object는 들어오는 간선(fan-in)과 나가는 간선(fan-out)이 함께 큰 노드다. 차수를 세면 후보가 보인다.
- **강한 연결 요소(SCC)** — Big Ball of Mud의 한 신호는 패키지·모듈 그래프의 큰 순환 묶음이다. 순환 탐지는 Tarjan·Kosaraju 알고리즘으로 한다. 규칙으로 막는 법은 [41-architecture-fitness-rules](../41-architecture-fitness-rules/2-summary.md).
- **공유 가변 상태 + 비원자적 갱신** — `long++`(읽기-수정-쓰기)는 원자적이지 않다. `AtomicLong`은 CAS(compare-and-swap)로 고친다. 원리는 [os/15-race-conditions](../../os/15-race-conditions/2-summary.md)·[os/20-concurrency-bugs](../../os/20-concurrency-bugs/2-summary.md).
- **해시 테이블의 크기 조정과 트리 버킷** — JDK `HashMap`은 버킷 충돌이 많으면 연결 리스트를 레드-블랙 트리로 바꾼다(`treeify`). 동시 수정이 이 구조를 깨면 실험 C의 무한 루프가 난다.

## 적용 — 풀어나가는 법

### 1. 찾기

1. **God Object 후보** — 크기와 변경 빈도를 함께 본다.

```bash
# 최근 1년 변경이 많은 파일 (변경 빈도)
git log --since=1.year --name-only --format= | sort | uniq -c | sort -rn | head
# 그 파일의 크기와 import 수 (나가는 의존의 대리 지표)
wc -l src/main/java/**/OrderManager.java; grep -c '^import ' src/main/java/**/OrderManager.java
# 그 클래스를 쓰는 파일 수 (들어오는 의존)
grep -rl 'OrderManager' src/main/java | wc -l
```

2. **가변 전역 상태** — `static` 가변 필드, 상태를 가진 `enum INSTANCE`, `getInstance()` 호출처를 찾는다.

```bash
grep -rnE 'static (volatile )?[A-Za-z<>, ]+ [a-zA-Z_]+ *(=|;)' src/main/java | grep -v ' final '
grep -rn 'getInstance()\|\.INSTANCE\.' src/main/java | wc -l
```

3. **진흙 덩어리** — 패키지 순환(`jdeps -verbose:package`로 패키지 의존 목록을 뽑아 SCC로 순환을 찾거나 — jdeps는 순환을 직접 보고하지 않는다 —, ArchUnit 1.4의 `slices().matching("..myapp.(*)..").should().beFreeOfCycles()`로 막는다), "아무도 설명 못 하는 모듈" 목록, 함께 커밋되는 파일 쌍([53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md)).

### 2. 고치기

- God Object → 변경 이유별로 나눈다. 먼저 함께 바뀌는 필드·메서드 묶음을 찾는다(같은 커밋에서 같이 바뀌는 것). 한 묶음씩 새 클래스로 옮기고 원래 클래스는 위임만 남긴다(Fowler 『Refactoring』 Extract Class).
- 싱글턴 → 인스턴스를 주입받게 바꾼다. 테스트에서는 테스트마다 새 인스턴스. 상태를 꼭 공유해야 하면 동시성 안전 자료구조(`ConcurrentHashMap`·`AtomicLong`)를 쓴다.

```java
// 전: 어디서나 Pricing.INSTANCE.quote(...)
// 후: 생성자로 받는다 — 테스트는 new PricingService(0.2)를 넘긴다
class CheckoutService {
    private final PricingService pricing;
    CheckoutService(PricingService pricing) { this.pricing = pricing; }
}
```

- Big Ball of Mud → 전면 재작성보다 경계를 하나씩 세운다. Foote·Yoder의 SHEARING LAYERS(변경 속도가 다른 것을 다른 층으로)와 Strangler Fig(50)가 그 방향이다.
- 과설계 → 구현이 하나뿐인 인터페이스·팩토리를 인라인한다. 패턴에서 멀어지는 리팩터링도 카탈로그에 있다 — Kerievsky 『Refactoring to Patterns』 카탈로그의 Inline Singleton(Industrial Logic 카탈로그 페이지, [29-refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md)).

## 장애 시나리오와 대처

### 1. 전역 싱글턴 → 테스트 간 상태 누출 (⚠ 커리큘럼)

- 현상: 로컬에서는 통과, CI에서는 가끔 실패. 테스트 하나만 돌리면 통과.
- 보이는 형태: `expected: <10000> but was: <8000>`처럼 앞 테스트의 값이 보이는 단언 실패(실험 B 순서 B).
- 원인: 앞 테스트가 전역 싱글턴에 상태를 남겼다. 테스트 실행 순서가 바뀌자 드러났다.
- 대처: 상태를 인스턴스로 옮기고 주입한다(실험 B 주입판). 당장 못 바꾸면 `@BeforeEach`/`@AfterEach`로 초기화한다 — 단 병렬 테스트에서는 이것으로도 부족하다.

### 2. 전역 싱글턴 → 동시성 버그 (⚠ 커리큘럼)

- 현상: 집계 수치가 실제 요청 수보다 적다. 드물게 서버 한 대가 CPU 100%로 응답을 멈춘다.
- 보이는 형태: 카운트 유실(실험 C: 400,000 중 약 21.6만~32.8만만 기록, 40회 범위), `size()`가 실제 키 수와 다름, 예외 없음. 멈춘 서버의 스레드 덤프에 `HashMap$TreeNode.balanceInsertion`에서 RUNNABLE인 스레드.
- 원인: 동기화 없는 가변 상태를 여러 요청 스레드가 공유했다.
- 대처: 전역 가변 상태를 없앤다. 공유가 꼭 필요하면 `AtomicLong`·`LongAdder`·`ConcurrentHashMap`. 스레드 덤프를 2~3번 떠서 같은 스택에 머무는 RUNNABLE 스레드를 찾는다.

### 3. God Object → 병합 충돌과 엉뚱한 곳 장애

- 현상: 무관한 두 기능 PR이 같은 파일에서 충돌한다. 쿠폰 수정 배포 뒤 정산이 깨진다.
- 보이는 형태: `CONFLICT (content): Merge conflict in OrderManager.java`(실험 A). `git log`에서 그 파일이 변경 빈도 1위.
- 원인: 변경 이유가 다른 책임이 한 클래스에 모였다.
- 대처: 함께 바뀌는 묶음별로 Extract Class. 나눈 뒤 같은 두 변경은 자동 병합됐다(실험 A 분리 판).

### 4. Big Ball of Mud → 아무도 못 건드리는 코드

- 현상: 작은 수정에도 회귀가 나고, 추정이 늘 빗나간다. "그 모듈은 ○○님만 안다."
- 보이는 형태: 패키지 순환이 크고, 한 변경의 `git diff --stat`이 여러 디렉터리에 퍼진다.
- 원인: Foote·Yoder가 꼽은 힘(시간·비용·경험·가시성·변화)이 오래 작용했다.
- 대처: 변경이 잦은 곳부터 경계를 세운다(53 핫스팟으로 순위). 전면 재작성(RECONSTRUCTION)은 마지막 선택지 — 빅뱅 재작성의 위험은 50.

### 5. 과설계 → 읽고 고칠 곳만 늘어남

- 현상: 규칙 하나를 찾으려고 인터페이스 → 팩토리 → 구현을 따라간다. 규칙 수정이 여러 클래스에 퍼진다.
- 보이는 형태: 구현이 하나뿐인 인터페이스. 30 실험 A에서 같은 할증 변경이 단순 판 1파일, 패턴 판 2파일.
- 원인: 오지 않은 변화를 위해 확장점을 먼저 만들었다.
- 대처: 인라인한다. 두 번째 변형이 실제로 오면 그때 추출한다.

## 핵심 문장

- 안티패턴은 겉보기엔 해법이지만 시간이 지나며 손해가 되는 흔한 선택이다. Foote·Yoder는 Big Ball of Mud를 시간·비용·경험·가시성·변화 같은 힘에 대한 반응으로 설명한다.
- God Object의 비용은 동시에 바뀌는 무관한 기능 수에 비례한다. 실험에서 두 기능 추가가 God 판은 충돌, 분리 판은 자동 병합이었다.
- 싱글턴의 문제는 "하나"가 아니라 전역에서 꺼내 쓰는 가변 상태다. 실험에서 테스트 순서만 바꿔 실패가 났다.
- 전역 가변 상태를 스레드가 공유하면 조용히 틀린다. 실험에서 카운트는 40만 중 약 21.6만~32.8만만 남았고(40회), 41회 중 1회는 `HashMap`이 무한 루프에 빠졌다.
- 고칠 때는 주입·분리·인라인으로 코드를 바꾸되, 그것을 낳은 힘(마감·보이지 않음)도 함께 다룬다.

## 관련 주제·근거

- 선행
  - [27-design-patterns-gof](../27-design-patterns-gof/2-summary.md) · 기존 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) — Singleton·Facade(커지면 God Object)
- 연결·후속
  - [30-pattern-languages-and-catalogs](../30-pattern-languages-and-catalogs/2-summary.md) — 힘을 보지 않고 패턴 이름만 빌린 결과(과설계 실험)
  - [10-code-smells](../10-code-smells/2-summary.md) — 스멜 카탈로그(Speculative Generality·Global Data 등)
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 싱글턴을 주입으로 바꾸기
  - [12-simple-design-and-yagni](../12-simple-design-and-yagni/2-summary.md) — 확장점은 두 번째 요구가 올 때 · [29-refactoring-to-patterns](../29-refactoring-to-patterns/2-summary.md) — Inline Singleton 등 패턴에서 멀어지기
  - [53-code-forensics-hotspots](../53-code-forensics-hotspots/2-summary.md) — 변경 빈도로 God Object·진흙 찾기
  - [50-legacy-migration-strangler-fig](../50-legacy-migration-strangler-fig/2-summary.md) — 진흙 덩어리를 재작성 없이 걷어내기
  - [reliability/47-server-design-antipatterns](../../reliability/47-server-design-antipatterns/2-summary.md) · [reliability/48-performance-and-stability-antipatterns-in-code](../../reliability/48-performance-and-stability-antipatterns-in-code/2-summary.md)
  - [os/15-race-conditions](../../os/15-race-conditions/2-summary.md) · [os/20-concurrency-bugs](../../os/20-concurrency-bugs/2-summary.md)
- 글·문서
  - Brian Foote, Joseph Yoder, "Big Ball of Mud", PLoP '97(1997), Technical Report WUCS-97-34, PLoPD4 29장(2000) <http://www.laputan.org/mud/mud.html>
  - Wikipedia 「Anti-pattern」(Koenig 1995 JOOP 8(1), Brown 외 『AntiPatterns』 1998) <https://en.wikipedia.org/wiki/Anti-pattern> — 원문 미열람
  - Wikipedia 「God object」(Riel 1996 휴리스틱 3.2 인용) <https://en.wikipedia.org/wiki/God_object> — Riel 책 미열람
  - Joshua Kerievsky, 『Refactoring to Patterns』 카탈로그(Inline Singleton 등) <https://www.industriallogic.com/refactoring-to-patterns/catalog/>
  - JDK 21 API `java.util.HashMap`(동기화되지 않음, 외부 동기화 필요) <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html>
- 실험 목록 (JDK 21.0.12 temurin `--cpus=2` 일회용 컨테이너, git 2.43.0)
  - A God Object vs 분리 클래스 병합 — `scratchpad/sd/30/e31god/` (`god`·`split` 저장소, 브랜치 `coupon`·`settlement`)
  - B 전역 싱글턴 테스트 순서 의존 — `scratchpad/sd/30/e31/` (JUnit Platform Console Standalone 1.12.2, `MethodName` vs 실험용 `ReverseName`)
  - C 전역 싱글턴 동시성(카운트 유실·`HashMap` 크기 오류) 20회 + 감시 없는 첫 실행의 무한 루프 스레드 덤프 (사실 점검 재실행 20회 — 무한 루프 0회) — `e31/src/Race.java`, `e31/Race_v1_no_watchdog.java.txt`, `e31/hang-threaddump.txt`
