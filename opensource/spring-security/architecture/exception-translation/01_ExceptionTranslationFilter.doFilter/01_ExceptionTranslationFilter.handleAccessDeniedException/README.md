# ExceptionTranslationFilter.handleAccessDeniedException

상위: [ExceptionTranslationFilter.doFilter](../README.md)

401 과 403 이 갈리는 자리다. 같은 `AccessDeniedException` 이 누가 요청했느냐에 따라 다른 응답이 된다.

## 위치

`web` / `org.springframework.security.web.access` / `ExceptionTranslationFilter.java` L188-L212 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/ExceptionTranslationFilter.java#L188-L212))

## 실제 코드

분기를 시작하는 곳은 바로 위에 있다.

`web` / `org.springframework.security.web.access` / `ExceptionTranslationFilter.java` L172-L180 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/ExceptionTranslationFilter.java#L172-L180))

```java
// ExceptionTranslationFilter.java L172-L180
private void handleSpringSecurityException(HttpServletRequest request, HttpServletResponse response,
        FilterChain chain, @Nullable RuntimeException exception) throws IOException, ServletException {
    if (exception instanceof AuthenticationException) {
        handleAuthenticationException(request, response, chain, (AuthenticationException) exception);
    }
    else if (exception instanceof AccessDeniedException) {
        handleAccessDeniedException(request, response, chain, (AccessDeniedException) exception);
    }
}
```

```java
// ExceptionTranslationFilter.java L188-L212
private void handleAccessDeniedException(HttpServletRequest request, HttpServletResponse response,
        FilterChain chain, AccessDeniedException exception) throws ServletException, IOException {
    Authentication authentication = this.securityContextHolderStrategy.getContext().getAuthentication();
    boolean isAnonymous = this.authenticationTrustResolver.isAnonymous(authentication);
    if (isAnonymous || this.authenticationTrustResolver.isRememberMe(authentication)) {
        if (logger.isTraceEnabled()) {
            logger.trace(LogMessage.format("Sending %s to authentication entry point since access is denied",
                    authentication), exception);
        }
        AuthenticationException ex = new InsufficientAuthenticationException(
                this.messages.getMessage("ExceptionTranslationFilter.insufficientAuthentication",
                        "Full authentication is required to access this resource"),
                exception);
        ex.setAuthenticationRequest(authentication);
        sendStartAuthentication(request, response, chain, ex);
    }
    else {
        if (logger.isTraceEnabled()) {
            logger.trace(
                    LogMessage.format("Sending %s to access denied handler since access is denied", authentication),
                    exception);
        }
        this.accessDeniedHandler.handle(request, response, exception);
    }
}
```

## 동작 흐름

```text
 handleAccessDeniedException(request, response, chain, exception)
 |
 | L190 securityContextHolderStrategy.getContext().getAuthentication()
 | L191 authenticationTrustResolver.isAnonymous(authentication)
 |
 +-- L192 익명이거나 isRememberMe 이면
 |      L197 InsufficientAuthenticationException 을 새로 만든다
 |             메시지 키 ExceptionTranslationFilter.insufficientAuthentication
 |             기본 문구 "Full authentication is required to access this resource"
 |             원래 예외를 cause 로 담는다
 |      L201 예외에 현재 인증을 담고
 |      L202 sendStartAuthentication(...)  --> 진입점으로
 |
 +-- L204 아니면
        L210 accessDeniedHandler.handle(request, response, exception)
               --> 403
```

```text
 신뢰 수준이 세 갈래다

 익명          AnonymousAuthenticationToken. 로그인한 적 없다
 기억된 사용자  RememberMeAuthenticationToken. 쿠키로 복원됐다
 완전 인증      그 밖. 익명 토큰도 remember-me 토큰도 아닌 경우
                authentication 이 null 인 경우도 여기로 떨어진다

 앞의 둘은 "더 인증하면 풀릴 수 있다"로 보고 진입점으로 보낸다
 마지막은 "더 인증해도 같다"로 보고 403 을 준다
```

```text
 기억된 사용자가 진입점으로 가는 근거

 javadoc 은 remember-me 를 "완전히 인증된 사용자가 아닌 것"으로
 분류한다 (AuthenticationTrustResolver L46-47)

 다만 민감한 작업을 실제로 막을지는 이 필터가 정하지 않는다
 인가 규칙의 fullyAuthenticated() 가 정하고,
 이 필터는 그 결과로 난 거부만 받는다
```

```text
 AccessDeniedException 이 AuthenticationException 으로 바뀐다

 들어올 때  AccessDeniedException ("권한 없음")
 나갈 때    InsufficientAuthenticationException ("인증이 부족함")

 타입이 바뀌므로 진입점은 자기가 다루는 예외 타입만 보면 된다
 원래 예외는 cause 로 남아 추적할 수 있다
```

## 결과가 쓰이는 곳

```text
 isAnonymous / isRememberMe 판정
      --> 기본 구현은 토큰 타입으로 판단한다
      --> 그래서 익명 필터를 체인에서 빼면 authentication 이 null 이 되고
          판정 결과가 달라질 수 있다

 진입점으로 간 경우
      --> 응답은 인증 방식이 정한다. 리다이렉트일 수도 401 일 수도 있다
      --> 원래 요청이 저장되어 로그인 후 되돌아간다

 거부 핸들러로 간 경우
      --> 기본 구현 AccessDeniedHandlerImpl 은
          errorPage 가 없으면 sendError(403),
          있으면 403 상태로 그 경로에 forward 한다
      --> forward 하는 경우 요청 속성에 예외를 담아 뷰가 쓸 수 있게 한다
```
