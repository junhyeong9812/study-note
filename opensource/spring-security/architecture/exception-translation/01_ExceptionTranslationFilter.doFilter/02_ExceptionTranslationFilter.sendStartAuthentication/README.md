# ExceptionTranslationFilter.sendStartAuthentication

상위: [ExceptionTranslationFilter.doFilter](../README.md)

인증을 요구하기 직전에 하는 세 가지다. 짧지만 순서에 의미가 있다.

## 위치

`web` / `org.springframework.security.web.access` / `ExceptionTranslationFilter.java` L214-L222 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/ExceptionTranslationFilter.java#L214-L222))

## 실제 코드

```java
// ExceptionTranslationFilter.java L214-L222
protected void sendStartAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain,
        AuthenticationException reason) throws ServletException, IOException {
    // SEC-112: Clear the SecurityContextHolder's Authentication, as the
    // existing Authentication is no longer considered valid
    SecurityContext context = this.securityContextHolderStrategy.createEmptyContext();
    this.securityContextHolderStrategy.setContext(context);
    this.requestCache.saveRequest(request, response);
    this.authenticationEntryPoint.commence(request, response, reason);
}
```

## 동작 흐름

```text
 sendStartAuthentication(request, response, chain, reason)
 |
 | L218 securityContextHolderStrategy.createEmptyContext()
 | L219 setContext(context)
 |        기존 인증을 버린다
 |        L216-217 주석이 SEC-112 를 들며
 |        "기존 Authentication 은 더 이상 유효하지 않다"고 적고 있다
 |
 | L220 requestCache.saveRequest(request, response)
 |        지금 가려던 요청을 저장한다
 |
 +-- L221 authenticationEntryPoint.commence(request, response, reason)
          인증을 시작시킨다. 응답은 진입점이 쓴다
```

```text
 순서가 계약이다

 컨텍스트 비우기 --> 요청 저장 --> 진입점

 저장이 진입점보다 먼저라는 것은 javadoc 에 계약으로 적혀 있다
 AuthenticationEntryPoint L38-41 --
 "ExceptionTranslationFilter will populate the HttpSession attribute
  ... before calling this method"

 컨텍스트를 비우는 이유로 소스에 적힌 것은 SEC-112 하나다 --
 기존 Authentication 이 더 이상 유효하지 않다는 것
```

```text
 chain 을 받지만 쓰지 않는다

 L214 시그니처에 FilterChain chain 이 있는데 본문에서 쓰지 않는다
 protected 라 하위 클래스가 오버라이드할 때 쓸 수 있게 열어 둔 것으로 보인다
 (그 설명이 소스에 적혀 있지는 않다)
```

## 결과가 쓰이는 곳

```text
 저장된 요청
      --> 로그인 성공 뒤 SavedRequestAwareAuthenticationSuccessHandler 가 꺼내
          원래 가려던 URL 로 되돌려 보낸다
      --> 기본 RequestCache 는 HttpSessionRequestCache 다. 세션을 쓴다
      --> 세션을 안 쓰는 API 서버라면 NullRequestCache 로 꺼 둔다

 비워진 컨텍스트
      --> 정확히는 빈 컨텍스트를 새로 만들어 덮어쓴다 (L218-219)
      --> 저장소에 saveContext 를 부르지는 않는다
          홀더(기본 전략이면 ThreadLocal)만 바뀐다

 진입점에 넘긴 reason
      --> 왜 인증이 필요한지를 담은 예외다
      --> 진입점이 이것을 보고 응답 메시지를 정할 수 있다
```
