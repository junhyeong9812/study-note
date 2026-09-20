# ThreadLocalSecurityContextHolderStrategy.getContext

상위: [보안 컨텍스트](../README.md)

`SecurityContextHolder.getContext()` 가 실제로 닿는 곳이다. 기본 보관 전략이고, 이름 그대로 `ThreadLocal` 하나가 전부다.

## 위치

`core` / `org.springframework.security.core.context` / `ThreadLocalSecurityContextHolderStrategy.java` L32-L79 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/context/ThreadLocalSecurityContextHolderStrategy.java#L32-L79))

## 실제 코드

```java
// ThreadLocalSecurityContextHolderStrategy.java L32-L79
final class ThreadLocalSecurityContextHolderStrategy implements SecurityContextHolderStrategy {

    private static final ThreadLocal<Supplier<SecurityContext>> contextHolder = new ThreadLocal<>();

    @Override
    public void clearContext() {
        contextHolder.remove();
    }

    @Override
    public SecurityContext getContext() {
        return getDeferredContext().get();
    }

    @Override
    public Supplier<SecurityContext> getDeferredContext() {
        Supplier<SecurityContext> result = contextHolder.get();
        if (result == null) {
            SecurityContext context = createEmptyContext();
            result = () -> context;
            contextHolder.set(result);
        }
        return result;
    }

    @Override
    public void setContext(SecurityContext context) {
        Assert.notNull(context, "Only non-null SecurityContext instances are permitted");
        contextHolder.set(() -> context);
    }

    @Override
    public void setDeferredContext(Supplier<SecurityContext> deferredContext) {
        Assert.notNull(deferredContext, "Only non-null Supplier instances are permitted");
        Supplier<SecurityContext> notNullDeferredContext = () -> {
            SecurityContext result = deferredContext.get();
            Assert.notNull(result, "A Supplier<SecurityContext> returned null and is not allowed.");
            return result;
        };
        contextHolder.set(notNullDeferredContext);
    }

    @Override
    public SecurityContext createEmptyContext() {
        return new SecurityContextImpl();
    }

}
```

이 클래스는 `public` 이 아니다. 패키지 밖에서는 `SecurityContextHolder` 를 통해서만 닿는다.

## 동작 흐름

```text
 getContext()
 |
 +-- L43 getDeferredContext().get()
        |
        +-- L48 contextHolder.get()   ThreadLocal 에서 Supplier 를 꺼낸다
        |
        +-- L49 없으면
        |      L50 createEmptyContext()   new SecurityContextImpl()
        |      L51 그 값을 돌려주는 Supplier 로 감싸
        |      L52 ThreadLocal 에 넣는다
        |
        +-- L54 Supplier 를 돌려준다
             그 Supplier 의 get() 이 실제 컨텍스트다
```

```text
 담기는 것은 컨텍스트가 아니라 Supplier 다

 ThreadLocal<Supplier<SecurityContext>>
                ^^^^^^^^

 setContext(context)          L60 () -> context 로 감싸 넣는다
 setDeferredContext(supplier) L71 null 검사를 덧입혀 넣는다

 둘 다 결국 Supplier 로 저장된다
 그래서 "이미 읽은 값"과 "아직 안 읽은 방법"을 같은 자리에 담을 수 있다
```

```text
 getContext 는 null 을 돌려주지 않는다

 비어 있으면 빈 컨텍스트를 만들어 넣고 그것을 돌려준다
 그래서 호출부는 null 검사를 하지 않는다

 대신 "인증되지 않음"은 컨텍스트 안의 authentication 이 null 인 것으로 나타난다
 AuthorizationFilter 가 그 null 을 보고 예외를 던진다

 부작용에 주의할 점
   비어 있을 때 getContext() 를 부르면 ThreadLocal 에 값이 생긴다
   조회만 했는데 상태가 바뀐다
```

```text
 setDeferredContext 가 null 을 막는 방식

 L66-70 에서 받은 Supplier 를 한 겹 더 감싼다
   get() 결과가 null 이면 Assert 로 터뜨린다
 넣는 시점이 아니라 꺼내는 시점에 검사한다
 지연 로딩이라 넣을 때는 결과를 알 수 없기 때문이다
```

## 결과가 쓰이는 곳

```text
 돌려준 SecurityContext
      --> getAuthentication() 으로 인증 정보를 꺼낸다
      --> 인가 판정, @PreAuthorize 평가, 컨트롤러의 @AuthenticationPrincipal
          모두 같은 값을 본다

 ThreadLocal 이라는 점
      --> 같은 스레드 안에서만 보인다
      --> @Async 로 넘긴 작업이나 새로 만든 스레드는 이 값을 못 본다
          그쪽은 별도의 전달 장치가 필요하다
      --> 리액티브 스택은 이 전략 대신 Reactor Context 를 쓴다
      --> 스레드 사이로 컨텍스트를 넘겨야 하면
          core 의 DelegatingSecurityContextRunnable 계열을 쓴다

 다른 전략들
      --> InheritableThreadLocal, Global 구현이 같은 패키지에 있고
          SecurityContextHolder 가 모드로 고른다
      --> ListeningSecurityContextHolderStrategy 는 데코레이터라
          모드로 고르지 않고 직접 감싸 설치한다
```

리액티브 쪽이 같은 일을 어떻게 하는지는 [리액티브 컨텍스트](../../reactive-context/README.md)에 있다.
