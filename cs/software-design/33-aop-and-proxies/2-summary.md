# software-design/33-aop-and-proxies — AOP와 프록시: 횡단 관심사를 대리 객체로 끼워 넣기 — 정리 (힌트)

## 해결하는 문제

트랜잭션·로깅·권한 검사·지표 수집은 기능이 아니다. 그런데 서비스 메서드 대부분에 들어가야 한다.

```text
 AOP 없이                                   AOP(프록시)로
 pay()      { 권한검사; tx시작; ... ; 커밋; 로그 }     호출자 ─> [프록시: 권한→tx→로그] ─> pay()      { ... }
 refund()   { 권한검사; tx시작; ... ; 커밋; 로그 }                                     ─> refund()   { ... }
 settle()   { 권한검사; tx시작; ... ; 커밋; 로그 }                                     ─> settle()   { ... }
   ↑ 같은 줄이 N곳에 흩어진다(scattering)            ↑ 부가 기능은 한 곳, 메서드에는 본업만
   ↑ 본업과 부가 기능이 한 메서드에 엉킨다(tangling)
```

- *횡단 관심사(cross-cutting concern)*: 여러 모듈에 걸쳐 같은 모양으로 나타나는 부가 기능. Kiczales 외(ECOOP 1997)는 이것을 기능 분해와 "다르게 합성되면서도 조율돼야 하는" 성질이라고 부르고, 그래서 코드가 엉킨다(tangling)고 적었다.
- *AOP(관점 지향 프로그래밍)*: 횡단 관심사를 *애스펙트*라는 단위로 따로 쓰고, 어디에 끼울지는 규칙(*포인트컷*)으로 정하는 방식.
- *프록시(proxy)*: 진짜 객체와 같은 타입으로 보이는 대리 객체. 호출을 먼저 받아 앞뒤에 일을 끼우고 진짜 객체에 넘긴다.

쉬운 예: 건물 출입 경비원이다. 방마다 경비를 세우지 않고 입구에 한 명을 둔다. 입구를 거치지 않고 방과 방 사이 내부 문으로 다니면 경비는 그 이동을 보지 못한다.\
똑같은 구조다.\
실무 예: Spring의 `@Transactional`·`@Cacheable`·`@PreAuthorize`·`@Async`가 프록시로 동작한다. 경비원(프록시)이 못 보는 "내부 문"이 자기 호출(self-invocation)이다.

트랜잭션 쪽 세부(전파·롤백 규칙·자기 호출로 트랜잭션이 빠지는 현상)는 [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md)가 다룬다.\
이 노트는 그 아래의 **프록시 메커니즘 자체**를 다룬다: 프록시 두 종류, 프록시가 못 가로채는 호출, 여러 어드바이스의 순서, TS 데코레이터와의 차이.

## 동작·원리

### 1. 프록시는 같은 타입의 대리 객체다

```text
 호출자 ──> proxy.pay(1000)
              │  (1) 어드바이스 체인 실행: [권한] → [tx] → [로그]
              │  (2) 체인 끝에서 target.pay(1000) 호출 (리플렉션)
              v
            target(진짜 객체).pay(1000)
              │  결과·예외
              v
 호출자 <── 체인을 거꾸로 거쳐 돌아온다 (tx 커밋/롤백, 로그)
```

- *어드바이스(advice)*: 끼워 넣을 동작. 앞(before)·뒤(after)·감싸기(around)가 있다.
- *조인포인트(join point)*: 끼울 수 있는 지점. Spring AOP에서 조인포인트는 메서드 실행을 뜻한다(Spring 6.2 문서 「AOP Concepts」).
- *포인트컷(pointcut)*: 어느 조인포인트에 끼울지 고르는 식. 예: `@annotation(Tx)`.
- Spring은 빈 하나에 프록시 하나를 만들고, 맞는 어드바이스들을 **그 프록시 안의 목록**(인터셉터 체인)으로 둔다. `ReflectiveMethodInvocation.proceed()`가 인덱스를 하나씩 올리며 다음 인터셉터를 부르고, 끝에 닿으면 진짜 메서드를 부른다(spring-aop 6.2.11 소스).

### 2. 프록시를 만드는 두 방법 — 인터페이스 구현 vs 서브클래스

```text
 JDK 동적 프록시                             CGLIB 프록시
   «interface» Greeter                         GreeterImpl
        ▲          ▲                               ▲  (상속)
        │          │                               │
   GreeterImpl   $Proxy19 ─위임─> GreeterImpl   GreeterImpl$$SpringCGLIB$$0
   (진짜)        (런타임 생성)                  (런타임 생성 서브클래스, 메서드를 override)
 - 인터페이스에 있는 메서드만 가로챈다          - final 클래스는 상속 불가 → 프록시 못 만듦
 - 프록시는 GreeterImpl 타입이 아니다           - final·private 메서드는 override 불가 → 못 가로챔
```

- *JDK 동적 프록시*: `java.lang.reflect.Proxy`가 런타임에 인터페이스 구현 클래스를 만든다. 프록시의 메서드 호출은 `InvocationHandler.invoke(proxy, Method, args)` 하나로 모인다. `Object`의 `hashCode`·`equals`·`toString`도 핸들러로 간다(JDK 21 `Proxy` API 문서).
- *CGLIB*: 바이트코드를 생성해 대상 클래스의 서브클래스를 만든다. Spring은 spring-core에 재포장해 넣어 둔다(Spring 문서 「Proxying Mechanisms」).
- **누가 고르나** — Spring Framework 6.2의 `DefaultAopProxyFactory`(소스):
  - `optimize=true`이거나 `proxyTargetClass=true`이거나, 사용자가 준 인터페이스가 없으면 → CGLIB. 단 대상 클래스가 없거나 인터페이스·람다·이미 JDK 프록시면 JDK.
  - 그 밖(인터페이스가 있고 `proxyTargetClass=false`) → JDK 동적 프록시.
- `@EnableAspectJAutoProxy`의 `proxyTargetClass` 기본은 `false`다(실험 B에서 JDK 프록시가 나왔다).
- Spring Boot는 기본으로 CGLIB을 쓰게 설정한다. JDK 프록시로 바꾸려면 `spring.aop.proxy-target-class=false`(Spring Boot 3.5 문서 「Aspect-Oriented Programming」).
- CGLIB 프록시 인스턴스는 Objenesis로 만든다. 그래서 대상 생성자가 두 번 불리지 않는다(Spring 문서). 대신 **프록시 인스턴스 자신의 필드는 초기화되지 않는다**(실험 C3).

### 실험 A: 순수 JDK 동적 프록시

```java
Greeter target = new GreeterImpl();
Greeter p = (Greeter) Proxy.newProxyInstance(Greeter.class.getClassLoader(),
        new Class<?>[]{Greeter.class},
        (proxy, method, a) -> {
            System.out.println("    [handler] method=" + method.getName() + " args=" + Arrays.toString(a));
            return method.invoke(target, a);           // 리플렉션으로 진짜 객체 호출
        });
```

(실험, JDK 21.0.12 temurin `--cpus=2`, Spring Framework 6.2.11 · AspectJ weaver 1.9.24, 2026-10-02 — `scratchpad/sd/30/e33/src/exp33/Main.java`. 프록시 클래스 번호(`$Proxy0`·`$Proxy19`)는 실행 환경에 따라 다를 수 있다)

```text
== A. 순수 JDK 동적 프록시 (java.lang.reflect.Proxy)
    [handler] method=hi args=[kim]
  result=hi kim
  class=jdk.proxy1.$Proxy0 isProxyClass=true
  instanceof Greeter=true instanceof GreeterImpl=false
  cast to GreeterImpl -> ClassCastException
```

- 호출이 핸들러 하나로 모였다. `Method` 객체로 무엇이 불렸는지 안다.
- 프록시는 `Greeter`이지만 `GreeterImpl`은 아니다. 구현 클래스로 캐스팅하면 깨진다.

### 실험 B·C: Spring이 고른 프록시 종류

```text
== B. Spring 6.2 @EnableAspectJAutoProxy 기본 (인터페이스 있음)
  class=jdk.proxy1.$Proxy19
    [advice] -> hi
  result=hi lee
  getBean(GreeterImpl.class) -> NoSuchBeanDefinitionException
  getBean("greeter", GreeterImpl.class) -> BeanNotOfRequiredTypeException
== C. proxyTargetClass=true (CGLIB 서브클래스)
  greeter class=exp33.Main$GreeterImpl$$SpringCGLIB$$0 instanceof GreeterImpl=true
  orderService class=exp33.Main$OrderService$$SpringCGLIB$$0 superclass=OrderService
```

- B: 인터페이스가 있어 JDK 프록시가 됐다. 구현 클래스 타입으로 빈을 찾으면 **빈이 없다고** 나온다. 이름으로 찾고 구현 타입을 요구하면 **타입이 다르다고** 나온다. 컨테이너에 등록된 것은 프록시이고, 프록시는 그 타입이 아니다.
- C: `proxyTargetClass=true`면 같은 빈이 서브클래스 프록시가 되고 구현 클래스 타입으로도 보인다.

### 3. 프록시가 못 가로채는 호출

```text
 외부 ─> proxy.outer() ──> [어드바이스 없음: outer엔 @Counted 없음] ──> target.outer()
                                                                         │ this.inner()
                                                                         v
                                                                   target.inner()   ← this = 진짜 객체
                                                                   (프록시를 안 거침 → @Counted 미적용)

 외부 ─> proxy.finalMethod()   CGLIB 서브클래스가 override 못 함
          └─> 프록시 인스턴스 자신의 finalMethod 본문이 그대로 실행
              this.repo == null (Objenesis로 만든 프록시라 필드 초기화 안 됨) → NPE
```

Spring 문서(6.2 「Proxying Mechanisms」)가 꼽는 CGLIB의 한계:

- final 클래스는 상속할 수 없어 프록시를 못 만든다.
- final 메서드·private 메서드는 override할 수 없어 어드바이스를 못 붙인다.
- 다른 패키지 부모 클래스의 package-private 메서드처럼 보이지 않는 메서드도 사실상 private이라 못 붙인다.
- 자기 호출(`this.bar()`)은 프록시가 아닌 `this`로 가므로 어드바이스가 실행되지 않는다(JDK·CGLIB 공통).

### 실험 C1~C3·D: 자기 호출, final 메서드, final 클래스

```java
public static class OrderService {               // 인터페이스 없음 → CGLIB
    private final Repo repo;
    public OrderService(Repo repo) { this.repo = repo; }
    public String outer() { return "outer>" + inner(); }      // this.inner() — 자기 호출
    @Counted public String inner() { return "inner"; }
    @Counted public final String finalMethod() { return "final:" + repo.name(); }
}
public static final class FinalService { @Counted public String go() { return "go"; } }
```

(실험, 같은 환경, 2026-10-02)

```text
  C1 s.inner() 직접 (프록시 경유):
    [advice] -> inner
    = inner
  C2 s.outer() → this.inner() (자기 호출):
    = outer>inner
  C3 s.finalMethod() (final 메서드):
    -> NullPointerException: Cannot invoke "exp33.Main$Repo.name()" because "this.repo" is null
== D. final 클래스에 어드바이스
WARNING: Exception encountered during context initialization - cancelling refresh attempt: org.springframework.beans.factory.BeanCreationException: Error creating bean with name 'finalService' defined in exp33.Main$FinalCfg: Could not generate CGLIB subclass of class exp33.Main$FinalService: Common causes of this problem include using a final class or a non-visible class
  BeanCreationException / root: IllegalArgumentException: Cannot subclass final class exp33.Main$FinalService
```

- C1과 C2는 같은 `inner()`가 실행됐다. 프록시를 거친 C1만 `[advice]` 줄이 찍혔다. C2는 **에러 없이** 어드바이스 없이 지나갔다.
- C3: final 메서드는 어드바이스가 안 붙었을 뿐 아니라 NPE가 났다. 프록시 인스턴스에서 본문이 돌았고, 그 인스턴스의 `repo`는 null이다.
  - Spring 6.2.11 `CglibAopProxy.doValidateClass` 소스는 이 경우 DEBUG 로그로 "Final method [...] cannot get proxied via CGLIB: Calls to this method will NOT be routed to the target instance and might lead to NPEs against uninitialized fields in the proxy instance."를 남긴다. 인터페이스를 구현한 final 메서드면 WARN이다. 기본 로그 레벨이면 DEBUG는 안 보인다.
- D: final 클래스는 조용히 넘어가지 않고 **기동이 실패**했다. 이 실패는 배포 직후 바로 드러난다.

### 4. 여러 어드바이스의 순서 — 양파

```text
 order 1 (바깥) ─┐                       Spring 규칙(문서 「Advice Ordering」):
 order 2 (안쪽) ─┼─> 메서드                - 들어갈 때: 우선순위 높은(값이 작은) 것이 먼저
                 │                         - 나올 때:   우선순위 높은 것이 나중
 나올 때는 역순 <─┘                        - 서로 다른 애스펙트끼리 순서를 안 주면 순서는 정해지지 않는다
```

- 순서는 애스펙트 클래스에 `@Order`를 달거나 `Ordered`를 구현해서 준다.
- `@EnableTransactionManagement`의 `order` 기본값은 `Ordered.LOWEST_PRECEDENCE`다(Spring 6.2 문서 「Using @Transactional」 설정 표). 다른 애스펙트에 순서를 주면 트랜잭션 어드바이스는 대개 가장 안쪽이 된다.

### 실험 E: 재시도와 트랜잭션의 순서를 바꿔 보기

첫 시도는 `IllegalStateException`, 두 번째는 성공하는 `pay()`에 `@Retry`·`@Tx` 애스펙트(직접 만든 흉내)를 붙였다.

(실험, 같은 환경, 2026-10-02)

```text
== E. 순서: Retry order=1, Tx order=2 (작은 값이 바깥)
    retry attempt 1
    tx#1 begin
      pay() 시도 1
    tx#1 rollback (일시 오류)
    retry attempt 2
    tx#2 begin
      pay() 시도 2
    tx#2 commit
  result=paid
== E. 순서: Retry order=2, Tx order=1 (작은 값이 바깥)
    tx#1 begin
    retry attempt 1
      pay() 시도 1
    retry attempt 2
      pay() 시도 2
    tx#1 commit
  result=paid
```

- 재시도가 바깥이면 시도마다 새 트랜잭션이다. 실패한 시도의 쓰기는 롤백된다.
- 재시도가 안쪽이면 두 시도가 **한 트랜잭션**을 공유한다. 실제 DB 트랜잭션이었다면 첫 시도의 쓰기가 남은 채로 두 번째 시도가 실행된다. 첫 시도 안에서 부른 다른 `@Transactional` 메서드(같은 트랜잭션에 참여)가 예외로 끝났다면 트랜잭션이 rollback-only로 표시돼, 재시도가 성공해도 커밋에서 실패할 수 있다(database/24 「UnexpectedRollbackException」).
- 같은 코드, 같은 애너테이션인데 숫자 두 개로 의미가 바뀌었다.

### 5. TS 데코레이터 — 메서드 자체를 바꿔 끼운다

```text
 Spring AOP:  객체 바깥에 대리 객체를 세운다     → this 호출은 대리 객체를 우회
 TS 데코레이터: 클래스 정의 시점에 프로토타입의 메서드를 감싼 함수로 교체한다
               → this.inner()도 교체된 함수를 부른다 → 자기 호출도 감싸진다
```

- TypeScript 5.0부터 `--experimentalDecorators` 없이 표준(TC39 Stage 3) 데코레이터를 쓴다. 옛 실험적 데코레이터와 타입 검사·출력이 다르고, 매개변수 데코레이터와 `--emitDecoratorMetadata`를 지원하지 않는다(TS 5.0 릴리스 노트).
- 옛 실험적 데코레이터 문서: 식은 위에서 아래로 평가하고, 결과 함수는 아래에서 위로 호출한다(TS 핸드북 「Decorators」).

### 실험 F: TS 표준 데코레이터의 적용 순서와 자기 호출

```ts
function wrap(label: string) {
  console.log(`  평가: @${label}`);
  return function <T extends (...a: any[]) => any>(fn: T, ctx: ClassMethodDecoratorContext) {
    console.log(`  적용: @${label} → ${String(ctx.name)}`);
    return function (this: unknown, ...args: any[]) {
      console.log(`    ${label} 들어감`);
      try { return fn.apply(this, args); } finally { console.log(`    ${label} 나옴`); }
    } as T;
  };
}
class PaymentService {
  @wrap("tx")
  @wrap("retry")
  pay(amount: number) { console.log(`      pay(${amount}) 본문`); return "ok"; }
  @wrap("log")   outer() { return this.inner(); }          // 자기 호출
  @wrap("audit") inner() { return "inner"; }
}
```

(실험, TypeScript 7.0.2 `tsc --target ES2022`, Node 18.19.1, 2026-10-02 — `scratchpad/sd/30/e33ts/deco.ts`. 출력 JS는 `__esDecorate` 보조 함수로 변환됐다)

```text
  평가: @tx
  평가: @retry
  평가: @log
  평가: @audit
  적용: @retry → pay
  적용: @tx → pay
  적용: @log → outer
  적용: @audit → inner
== 호출 pay()
    tx 들어감
    retry 들어감
      pay(1000) 본문
    retry 나옴
    tx 나옴
== 호출 outer() → this.inner()
    log 들어감
    audit 들어감
    audit 나옴
    log 나옴
```

- 평가는 위→아래, 적용은 아래→위였다. 그래서 **위에 쓴 데코레이터가 바깥**이다(`tx`가 `retry`를 감쌌다).
- `this.inner()`에도 `audit`이 실행됐다. 실험 C2(Spring)와 반대다. 메서드 자체가 바뀌었기 때문이다.

## 쓰이는 자료구조·알고리즘

- **위임 체인** — 프록시 → 인터셉터 1 → 인터셉터 2 → … → 진짜 메서드. Spring은 이것을 리스트 + 현재 인덱스로 구현한다(`ReflectiveMethodInvocation`). 각 인터셉터가 `proceed()`를 부르면 다음 칸으로 간다. 34의 필터 체인과 같은 뼈대다.
- **리플렉션 디스패치** — JDK 프록시에서는 인터페이스 메서드 호출이 `invoke(proxy, Method, args)` 한 곳으로 모이고, `Method` 객체를 키로 무엇을 할지 고른다. Spring은 메서드별로 맞는 인터셉터 목록을 캐시한다(`AdvisedSupport`의 `methodCache`).
- **서브클래스 생성(바이트코드 생성)** — CGLIB은 클래스 파일을 런타임에 만들어 로드한다. 상속 규칙(final 불가, override 불가)이 그대로 한계가 된다.
- **포인트컷 매칭** — AspectJ 포인트컷 식을 메서드 시그니처·애너테이션에 맞춰 본다. 빈에 프록시를 씌울지는 생성 때 정적 매칭으로 정한다. 메서드별 인터셉터 목록은 그 메서드의 첫 호출 때 계산해 `methodCache`에 두고, 인자에 따른 동적 매칭만 매 호출 때 한다(spring-aop 6.2.11 `AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice`).
- **Proxy·Decorator 패턴** — 구조는 같고 의도가 다르다. 기초는 [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) 「12. Proxy」·「9. Decorator」.

## 적용 — 풀어나가는 법

### 1. 순서

1. **AOP에 맡길 것을 고른다.** 여러 곳에 같은 모양으로 반복되고, 본업과 독립적인 것(트랜잭션 경계, 지표, 감사 로그, 권한 검사). 도메인 규칙은 넣지 않는다 — 코드에서 안 보이는 규칙이 된다.
2. **프록시를 거치는 입구를 정한다.** 어드바이스가 필요한 메서드는 다른 빈에서 부르는 public 메서드로 둔다. 같은 클래스 안에서 부르는 메서드에 애너테이션을 달지 않는다.
3. **final을 확인한다.** CGLIB 프록시 대상 클래스·메서드에 `final`이 없는지 본다.
4. **순서를 명시한다.** 재시도·서킷 브레이커·트랜잭션처럼 의미가 순서에 달린 애스펙트는 `@Order`로 정하고, 테스트로 고정한다.
5. **프록시 종류에 기대지 않는다.** 주입은 인터페이스나 빈 타입으로 받고, 구현 클래스로 캐스팅하지 않는다.

### 2. 코드 — 자기 호출을 빈 분리로 푼다

```java
@Service
class OrderFacade {                       // 바깥 빈
    private final OrderTx tx;             // 다른 빈 → 주입된 것은 프록시
    OrderFacade(OrderTx tx) { this.tx = tx; }
    void place(Cmd c) {
        validate(c);                      // 트랜잭션 밖
        tx.save(c);                       // 프록시를 거친다 → @Transactional 적용
    }
}
@Service
class OrderTx {
    @Transactional public void save(Cmd c) { /* ... */ }
}
```

- 자기 주입(self injection)이나 `AopContext.currentProxy()`도 문서에 나온다. 문서는 `currentProxy()`를 "highly discouraged"라고 쓴다 — 클래스가 Spring AOP에 묶인다.
- AspectJ 컴파일 타임·로드 타임 위빙은 바이트코드 안에 어드바이스를 넣으므로 자기 호출 문제가 없다(Spring 문서).

### 3. 진단

- 빈이 프록시인가: `AopUtils.isAopProxy(bean)`, `AopUtils.isJdkDynamicProxy(bean)`, `bean.getClass().getName()`에 `$$SpringCGLIB$$`·`jdk.proxy`가 보이는가.
- final 메서드 경고를 보려면 `org.springframework.aop.framework.CglibAopProxy` 로거를 DEBUG로 둔다.
- 어드바이스가 실제로 실행됐는가를 **테스트로** 본다. 예: 트랜잭션이면 `TransactionSynchronizationManager.isActualTransactionActive()`를 메서드 안에서 확인하는 테스트.

## 장애 시나리오와 대처

### 1. 자기 호출로 `@Transactional`이 조용히 미적용 (⚠ 커리큘럼)

- 현상: 중간에 예외가 났는데 앞서 쓴 행이 롤백되지 않았다.
- 보이는 형태: 에러 로그는 정상적인 예외 하나. 트랜잭션 매니저 DEBUG 로그에 `Creating new transaction` 줄이 없다.
- 원인: 같은 클래스 안의 `this.method()` 호출은 프록시를 거치지 않는다(실험 C2).
- 대처: 트랜잭션 경계 메서드를 다른 빈으로 분리한다. 세부와 재현은 [database/24](../../database/24-transaction-boundaries-in-app-code/2-summary.md) 「장애 1」.

### 2. final 메서드라 어드바이스 누락 + NPE (⚠ 커리큘럼)

- 현상: 특정 메서드만 트랜잭션·캐시가 안 걸린다. 또는 주입된 필드가 null이라는 NPE가 그 메서드에서만 난다.
- 보이는 형태: `NullPointerException: ... because "this.repo" is null`(실험 C3). 생성자 주입을 했는데 null이다.
- 원인: CGLIB 서브클래스가 final 메서드를 override하지 못한다. 본문이 프록시 인스턴스에서 실행되고, 그 인스턴스 필드는 초기화되지 않았다.
- 대처: final을 뗀다. 또는 그 메서드를 인터페이스에 올리고 JDK 프록시를 쓴다(Spring WARN 메시지가 권하는 방법). DEBUG 로그로 "cannot get proxied via CGLIB" 줄을 찾는다.

### 3. final 클래스라 프록시 생성 실패 (⚠ 커리큘럼)

- 현상: 애플리케이션이 뜨지 않는다.
- 보이는 형태: `BeanCreationException ... Could not generate CGLIB subclass of class ...`, 근본 원인 `IllegalArgumentException: Cannot subclass final class`(실험 D).
- 원인: 애스펙트가 걸리는 빈의 클래스가 final이다.
- 대처: final을 떼거나 인터페이스를 두고 JDK 프록시로 만든다. 2번과 달리 기동에서 바로 드러나므로 배포 전 통합 테스트로 잡힌다.

### 4. 프록시 순서가 뒤바뀌어 재시도가 트랜잭션 안에서 돈다 (⚠ 커리큘럼)

- 현상: 재시도가 성공했는데 커밋에서 실패한다. 또는 실패한 시도의 쓰기가 성공한 시도와 함께 커밋된다.
- 보이는 형태: 로그에 트랜잭션 시작이 한 번, 재시도가 여러 번(실험 E 두 번째). `UnexpectedRollbackException`.
- 원인: 재시도 애스펙트의 우선순위가 트랜잭션보다 낮다(값이 크다). 순서를 지정하지 않으면 서로 다른 애스펙트 사이 순서는 정해지지 않는다(Spring 문서).
- 대처: 재시도를 바깥(작은 값), 트랜잭션을 안쪽(큰 값)으로 명시한다. 순서를 출력하는 테스트로 고정한다.

### 5. JDK 프록시인데 구현 클래스로 주입

- 현상: 기동 실패 또는 `ClassCastException`.
- 보이는 형태: `NoSuchBeanDefinitionException`(구현 타입으로 조회), `BeanNotOfRequiredTypeException`(이름 + 구현 타입으로 조회) — 둘 다 실험 B. 직접 캐스팅하면 `ClassCastException`(실험 A).
- 원인: JDK 프록시는 인터페이스만 구현한다. 구현 클래스 타입이 아니다.
- 대처: 인터페이스 타입으로 주입받는다. 또는 `proxyTargetClass=true`(Spring Boot 기본).

## 핵심 문장

- Spring AOP는 같은 타입의 대리 객체(프록시)를 세워 메서드 호출 앞뒤에 어드바이스를 끼운다. 프록시를 거친 외부 호출에만 적용된다.
- 인터페이스가 있고 `proxyTargetClass=false`면 JDK 동적 프록시, 아니면 CGLIB 서브클래스다. Spring Boot는 기본으로 CGLIB을 쓴다.
- CGLIB은 상속이라 final 클래스는 기동 실패, final 메서드는 조용한 누락이다. 실험에서 final 메서드는 프록시 인스턴스의 null 필드로 NPE까지 냈다.
- 여러 어드바이스는 양파처럼 감싼다. 우선순위가 높은(값이 작은) 것이 바깥이고, 재시도와 트랜잭션은 순서에 따라 시도마다 새 트랜잭션이 되기도 하고 한 트랜잭션을 공유하기도 한다.
- TS 표준 데코레이터는 메서드 자체를 교체한다. 그래서 자기 호출도 감싸지고, 위에 쓴 데코레이터가 바깥이 된다.

## 관련 주제·근거

- 선행
  - [32-inversion-of-control-and-framework-flow](../32-inversion-of-control-and-framework-flow/2-summary.md) — 컨테이너가 객체를 만들고 부른다. 프록시는 그 컨테이너가 만든 객체다
  - [25-dependency-injection-and-composition-root](../25-dependency-injection-and-composition-root/2-summary.md) — 주입된 것이 프록시다
- 연결·후속
  - [database/24-transaction-boundaries-in-app-code](../../database/24-transaction-boundaries-in-app-code/2-summary.md) — `@Transactional` 프록시, 자기 호출, 롤백 규칙, 전파
  - [34-middleware-filter-interceptor-chains](../34-middleware-filter-interceptor-chains/2-summary.md) — 같은 위임 체인을 요청 단위로
  - [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md) — Resilience4j Spring Boot 애스펙트 순서(Retry가 가장 바깥)
  - [engineering/design-patterns-gof](../../engineering/design-patterns-gof/2-summary.md) — Proxy·Decorator
  - [35-annotation-and-metadata-programming](../35-annotation-and-metadata-programming/2-summary.md) — 애너테이션을 읽어 동작을 만드는 쪽
- 글·문서
  - Gregor Kiczales 외, "Aspect-Oriented Programming", ECOOP 1997, Springer LNCS 1241 — cross-cut·aspect weaver <https://www.cs.ubc.ca/~gregor/papers/kiczales-ECOOP1997-AOP.pdf>
  - Spring Framework 6.2 문서 「Proxying Mechanisms」(JDK/CGLIB 선택, final·private 한계, Objenesis, 자기 호출과 해법) <https://docs.spring.io/spring-framework/reference/6.2/core/aop/proxying.html>
  - Spring Framework 6.2 문서 「Declaring Advice」의 Advice Ordering <https://docs.spring.io/spring-framework/reference/6.2/core/aop/ataspectj/advice.html>
  - Spring Framework 6.2 문서 「Using @Transactional」(`order` 기본 `Ordered.LOWEST_PRECEDENCE`) <https://docs.spring.io/spring-framework/reference/6.2/data-access/transaction/declarative/annotations.html>
  - spring-aop 6.2.11 소스: `DefaultAopProxyFactory.createAopProxy`, `CglibAopProxy.doValidateClass`, `ReflectiveMethodInvocation.proceed`
  - Spring Boot 3.5 문서 「Aspect-Oriented Programming」(기본 CGLIB, `spring.aop.proxy-target-class`) <https://docs.spring.io/spring-boot/3.5/reference/features/aop.html>
  - JDK 21 API `java.lang.reflect.Proxy` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/reflect/Proxy.html>
  - TypeScript 5.0 릴리스 노트 「Decorators」 <https://www.typescriptlang.org/docs/handbook/release-notes/typescript-5-0.html> · TS 핸드북 「Decorators」(실험적 데코레이터, 평가·호출 순서) <https://www.typescriptlang.org/docs/handbook/decorators.html>
- 실험 목록 (JDK 21.0.12 temurin `--cpus=2` 일회용 컨테이너, Spring Framework 6.2.11 · AspectJ weaver 1.9.24 · micrometer-observation 1.14.11 jar)
  - A 순수 JDK 프록시: 핸들러 디스패치, 구현 클래스 캐스팅 실패 — `scratchpad/sd/30/e33/src/exp33/Main.java`
  - B·C 프록시 종류(JDK vs CGLIB), 구현 타입 조회 실패
  - C1~C3·D 자기 호출 미적용, final 메서드 NPE, final 클래스 기동 실패
  - E 재시도·트랜잭션 애스펙트 순서 바꾸기
  - F TS 7.0.2 표준 데코레이터 순서·자기 호출 — `scratchpad/sd/30/e33ts/deco.ts`
