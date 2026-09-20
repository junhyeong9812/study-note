# AuthorizationFilter.doFilter

상위: [인가](../README.md)

인가 매니저에게 판정을 맡기고, 거부면 예외를 던진다. 이 필터 자체는 규칙을 하나도 모른다.

## 위치

`web` / `org.springframework.security.web.access.intercept` / `AuthorizationFilter.java` L76-L106 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/intercept/AuthorizationFilter.java#L76-L106))

## 실제 코드

```java
// AuthorizationFilter.java L76-L106
@Override
public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain chain)
        throws ServletException, IOException {

    HttpServletRequest request = (HttpServletRequest) servletRequest;
    HttpServletResponse response = (HttpServletResponse) servletResponse;

    if (this.observeOncePerRequest && isApplied(request)) {
        chain.doFilter(request, response);
        return;
    }

    if (skipDispatch(request)) {
        chain.doFilter(request, response);
        return;
    }

    String alreadyFilteredAttributeName = getAlreadyFilteredAttributeName();
    request.setAttribute(alreadyFilteredAttributeName, Boolean.TRUE);
    try {
        AuthorizationResult result = this.authorizationManager.authorize(this::getAuthentication, request);
        this.eventPublisher.publishAuthorizationEvent(this::getAuthentication, request, result);
        if (result != null && !result.isGranted()) {
            throw new AuthorizationDeniedException("Access Denied", result);
        }
        chain.doFilter(request, response);
    }
    finally {
        request.removeAttribute(alreadyFilteredAttributeName);
    }
}
```

디스패치를 건너뛸지 정하는 부분이 바로 아래 있다.

`web` / `org.springframework.security.web.access.intercept` / `AuthorizationFilter.java` L108-L126 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/intercept/AuthorizationFilter.java#L108-L126))

```java
// AuthorizationFilter.java L108-L126
private boolean skipDispatch(HttpServletRequest request) {
    if (DispatcherType.ERROR.equals(request.getDispatcherType()) && !this.filterErrorDispatch) {
        return true;
    }

    return DispatcherType.ASYNC.equals(request.getDispatcherType()) && !this.filterAsyncDispatch;
}

private boolean isApplied(HttpServletRequest request) {
    return request.getAttribute(getAlreadyFilteredAttributeName()) != null;
}

private String getAlreadyFilteredAttributeName() {
    String name = getFilterName();
    if (name == null) {
        name = getClass().getName();
    }
    return name + ".APPLIED";
}
```

## 동작 흐름

```text
 doFilter(servletRequest, servletResponse, chain)
 |
 +-- L83 observeOncePerRequest 이고 이미 걸렸으면
 |        L84 체인으로 흘리고 L85 return
 |        observeOncePerRequest 기본값은 false 다 (L61)
 |        즉 기본은 디스패치마다 다시 판정한다
 |
 +-- L88 skipDispatch(request) 이면
 |        L89 체인으로 흘리고 L90 return
 |        ERROR 와 ASYNC 디스패치를 거를 수 있는 자리다
 |        filterErrorDispatch, filterAsyncDispatch 둘 다 기본 true 라 (L63, L65)
 |        기본값에서는 아무것도 건너뛰지 않는다
 |
 | L93 alreadyFilteredAttributeName 을 만들고
 | L94 요청 속성에 표시한다
 |
 | try (L95)
 |   L96 authorizationManager.authorize(this::getAuthentication, request)
 |          Authentication 이 아니라 Supplier 를 넘긴다
 |   L97 eventPublisher.publishAuthorizationEvent(...)
 |          허용이든 거부든 발행한다
 |   L98 result 가 null 이 아니고 granted 가 아니면
 |          L99 AuthorizationDeniedException("Access Denied", result)
 |   L101 통과하면 chain.doFilter
 |
 finally (L103)
     L104 요청 속성을 걷는다
```

```text
 null 결과는 거부가 아니다

 L98 if (result != null && !result.isGranted())

 result 가 null 이면 예외를 던지지 않고 그대로 통과한다
 매니저가 "판정하지 않겠다"고 한 것을 거부로 보지 않는다

 실제로 거부하려면 isGranted() 가 false 인 결과를 돌려줘야 한다
```

```text
 응답을 쓰지 않는다

 이 필터는 상태 코드도 본문도 쓰지 않는다
 예외만 던지고 끝난다

 그 예외를 체인 앞쪽의 ExceptionTranslationFilter 가 잡는다
 순서가 중요하다 -- 예외 변환 필터가 인가 필터보다 앞에 있어야
 던진 예외가 그 try 블록 안에서 잡힌다
```

## 결과가 쓰이는 곳

```text
 authorize 에 넘긴 Supplier
      --> 매니저가 필요할 때만 get() 한다
      --> permitAll 이면 Authentication 을 꺼내지도 않는다
      --> 그래서 인증 정보가 없어도 permitAll 경로는 통과한다

 publishAuthorizationEvent
      --> 허용과 거부를 모두 발행한다
      --> 기본 구현은 NoopAuthorizationEventPublisher 라 아무 일도 하지 않는다 (L59)
      --> 감사가 필요하면 이 자리를 갈아 끼운다

 던진 AuthorizationDeniedException
      --> 체인이 끊긴다
      --> 거부 결과(result)를 예외에 담아 넘기므로
          핸들러가 "무엇이 필요했는지"를 볼 수 있다

 요청 속성
      --> observeOncePerRequest 를 켰을 때만 의미가 있다
      --> finally 에서 지우므로 다음 디스패치에는 남지 않는다
```

## 하위 메서드

- [01 AuthorizationFilter.getAuthentication](01_AuthorizationFilter.getAuthentication/README.md)
