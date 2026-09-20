# SecurityContextHolderFilter.doFilter

상위: [보안 컨텍스트](../README.md)

저장소에서 컨텍스트를 받아 `ThreadLocal` 에 얹고, 체인이 끝나면 지운다. 저장은 하지 않는다.

## 위치

`web` / `org.springframework.security.web.context` / `SecurityContextHolderFilter.java` L72-L88 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/context/SecurityContextHolderFilter.java#L72-L88))

## 실제 코드

public 진입점은 캐스팅만 하고 private 오버로드로 넘긴다.

```java
// SecurityContextHolderFilter.java L66-L70
@Override
public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    doFilter((HttpServletRequest) request, (HttpServletResponse) response, chain);
}
```

```java
// SecurityContextHolderFilter.java L72-L88
private void doFilter(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
        throws ServletException, IOException {
    if (request.getAttribute(FILTER_APPLIED) != null) {
        chain.doFilter(request, response);
        return;
    }
    request.setAttribute(FILTER_APPLIED, Boolean.TRUE);
    Supplier<SecurityContext> deferredContext = this.securityContextRepository.loadDeferredContext(request);
    try {
        this.securityContextHolderStrategy.setDeferredContext(deferredContext);
        chain.doFilter(request, response);
    }
    finally {
        this.securityContextHolderStrategy.clearContext();
        request.removeAttribute(FILTER_APPLIED);
    }
}
```

## 동작 흐름

```text
 doFilter(request, response, chain)
 |
 | L74 request.getAttribute(FILTER_APPLIED) != null
 |
 +-- 이미 걸렸으면 (중첩 호출)
 |      L75 chain.doFilter 로 그냥 넘기고
 |      L76 return
 |      --> 컨텍스트를 다시 얹지도, 지우지도 않는다
 |
 +-- 처음이면
        L78 FILTER_APPLIED 속성을 심는다
        L79 securityContextRepository.loadDeferredContext(request)
        |     아직 읽지 않는다. Supplier 를 받을 뿐이다
        |
        try (L80)
        |   L81 securityContextHolderStrategy.setDeferredContext(deferredContext)
        |   L82 chain.doFilter(request, response)
        |
        finally (L84)
            L85 securityContextHolderStrategy.clearContext()
            L86 request.removeAttribute(FILTER_APPLIED)
```

```text
 setContext 가 아니라 setDeferredContext 다

 setContext(context)          값을 넣는다. 이미 읽었다는 뜻이다
 setDeferredContext(supplier) 읽는 방법을 넣는다. 아직 안 읽었다

 이 필터는 후자를 쓴다
 그래서 이 필터를 통과하는 것만으로는 세션이 열리지 않는다
```

```text
 저장 단계가 없다

 이 메서드 어디에도 saveContext 호출이 없다
 체인이 끝나도 컨텍스트를 저장소에 쓰지 않는다

 저장은 컨텍스트를 바꾼 쪽이 직접 한다
   AbstractAuthenticationProcessingFilter.successfulAuthentication  L398
   BasicAuthenticationFilter  L229
   RememberMeAuthenticationFilter  L131
   SwitchUserFilter  L196, L214
   SecurityContextLogoutHandler  L85-86 (빈 컨텍스트를 저장해 지운다)

 deprecated 된 SecurityContextPersistenceFilter 는 요청 끝에 자동 저장했다
 그 동작에 기대어 SecurityContextHolder 에만 심는 코드는
 이 필터 아래에서는 다음 요청에 인증이 남지 않는다
```

## 결과가 쓰이는 곳

```text
 ThreadLocal 에 얹힌 Supplier
      --> 체인의 뒤쪽 필터와 컨트롤러가 이것을 통해 인증을 본다
      --> AuthorizationFilter 가 판정에 쓰는 값이 이것이다

 FILTER_APPLIED
      --> forward 나 error 디스패치로 같은 필터가 두 번 걸려도
          컨텍스트를 두 번 얹거나 일찍 지우지 않는다

 finally 의 clearContext
      --> 예외가 나도 반드시 지운다
      --> 스레드를 재사용하는 환경에서 이것이 빠지면
          다음 요청이 앞 사용자의 인증을 물려받는다
```

## 하위 메서드

- [01 SecurityContextRepository.loadDeferredContext](01_SecurityContextRepository.loadDeferredContext/README.md)
