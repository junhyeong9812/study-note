# CsrfFilter.doFilterInternal

상위: [CSRF 방어](../README.md)

토큰을 꺼내 대조하고, 틀리면 체인을 끊는다. `OncePerRequestFilter` 를 상속해 한 요청에 한 번만 돈다.

## 위치

`web` / `org.springframework.security.web.csrf` / `CsrfFilter.java` L107-L136 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/CsrfFilter.java#L107-L136))

## 실제 코드

```java
// CsrfFilter.java L107-L136
@Override
protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
        throws ServletException, IOException {
    DeferredCsrfToken deferredCsrfToken = this.tokenRepository.loadDeferredToken(request, response);
    request.setAttribute(DeferredCsrfToken.class.getName(), deferredCsrfToken);
    this.requestHandler.handle(request, response, deferredCsrfToken);
    if (!this.requireCsrfProtectionMatcher.matches(request)) {
        if (this.logger.isTraceEnabled()) {
            this.logger.trace("Did not protect against CSRF since request did not match "
                    + this.requireCsrfProtectionMatcher);
        }
        filterChain.doFilter(request, response);
        return;
    }
    CsrfToken csrfToken = deferredCsrfToken.get();
    String actualToken = this.requestHandler.resolveCsrfTokenValue(request, csrfToken);
    if (actualToken != null && this.logger.isTraceEnabled()) {
        this.logger.trace(LogMessage.format("Found a CSRF token in the request"));
    }
    if (!equalsConstantTime(csrfToken.getToken(), actualToken)) {
        boolean missingToken = deferredCsrfToken.isGenerated();
        this.logger
            .debug(LogMessage.of(() -> "Invalid CSRF token found for " + UrlUtils.buildFullRequestUrl(request)));
        AccessDeniedException exception = (!missingToken) ? new InvalidCsrfTokenException(csrfToken, actualToken)
                : new MissingCsrfTokenException(actualToken);
        this.accessDeniedHandler.handle(request, response, exception);
        return;
    }
    filterChain.doFilter(request, response);
}
```

보호 대상을 가르는 기본 매처는 같은 파일 아래쪽에 있다.

`web` / `org.springframework.security.web.csrf` / `CsrfFilter.java` L207-L221 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/csrf/CsrfFilter.java#L207-L221))

```java
// CsrfFilter.java L207-L221
private static final class DefaultRequiresCsrfMatcher implements RequestMatcher {

    private final HashSet<String> allowedMethods = new HashSet<>(Arrays.asList("GET", "HEAD", "TRACE", "OPTIONS"));

    @Override
    public boolean matches(HttpServletRequest request) {
        return !this.allowedMethods.contains(request.getMethod());
    }

    @Override
    public String toString() {
        return "IsNotHttpMethod " + this.allowedMethods;
    }

}
```

## 동작 흐름

```text
 doFilterInternal(request, response, filterChain)
 |
 | L110 tokenRepository.loadDeferredToken(request, response)
 |        아직 읽지 않는다. DeferredCsrfToken 을 받는다
 | L111 요청 속성에 심는다 (키는 DeferredCsrfToken 클래스 이름)
 | L112 requestHandler.handle(request, response, deferredCsrfToken)
 |        뷰가 쓸 수 있게 토큰을 노출한다
 |
 +-- L113 requireCsrfProtectionMatcher 에 안 맞으면
 |        L118 체인으로 흘리고 L119 return
 |        기본 매처는 GET, HEAD, TRACE, OPTIONS 를 제외한다
 |
 | L121 deferredCsrfToken.get()      여기서 실제로 읽는다
 | L122 requestHandler.resolveCsrfTokenValue(request, csrfToken)
 |        헤더에서 먼저 찾고, 없으면 파라미터에서 찾는다
 |
 +-- L126 equalsConstantTime(csrfToken.getToken(), actualToken) 이 false 면
 |        L127 deferredCsrfToken.isGenerated()  방금 만든 것인가
 |        L130 아니면 InvalidCsrfTokenException
 |        L131 맞으면 MissingCsrfTokenException
 |        L132 accessDeniedHandler.handle(...)
 |        L133 return -- 체인을 끊는다
 |
 +-- L135 통과하면 filterChain.doFilter
```

```text
 검사 순서가 중요하다

 L112 토큰 노출은 매처 검사보다 먼저다

 GET 으로 폼 페이지를 여는 요청도 여기를 지나며
 요청 속성에 토큰이 심긴다
 그래야 그 페이지의 폼에 토큰을 넣을 수 있다

 매처 검사(L113)는 그 뒤다
 GET 은 거기서 통과해 대조를 건너뛴다
```

```text
 isGenerated 가 두 예외를 가른다

 deferredCsrfToken.isGenerated()
   true   저장소에 없어서 방금 만들었다 --> MissingCsrfTokenException
   false  저장소에 있던 것이다          --> InvalidCsrfTokenException

 세션이 만료되면 저장소가 비어 새로 만들게 되고,
 사용자가 보낸 옛 토큰과 당연히 다르다
 그 상황이 "위조"가 아니라 "만료"로 구분되는 근거다
```

```text
 예외를 던지지 않는다

 L132 accessDeniedHandler.handle(...) 을 직접 부르고 L133 return

 던지지 않으므로 ExceptionTranslationFilter 가 잡을 기회가 없다
 이 필터가 체인에서 그보다 앞에 있기도 하다

 다만 응답을 바꾸는 방법은 예외 처리 설정 쪽이다
 CsrfConfigurer 에는 accessDeniedHandler 메서드가 없고,
 L293-303 에서 ExceptionHandlingConfigurer 가 가진 핸들러를 꺼내
 CsrfFilter 에 꽂는다 (없으면 AccessDeniedHandlerImpl)

 즉 exceptionHandling().accessDeniedHandler(...) 로 설정하면
 이 필터도 그것을 쓴다. 다만 호출 경로는 직접 호출이라
 ExceptionTranslationFilter 를 거치지는 않는다
```

## 결과가 쓰이는 곳

```text
 요청 속성에 심은 DeferredCsrfToken (L111)
      --> main 소스에서 이 속성을 읽는 곳은
          CsrfTokenHandshakeInterceptor 하나다 (웹소켓 핸드셰이크)
      --> 뷰가 읽는 것은 이것이 아니라
          처리기가 심는 CsrfToken 속성이다

 shouldNotFilter (L102-105)
      --> 정적 메서드 skipRequest(request) 가 심은 속성을 본다
      --> 이 필터 전체를 건너뛰게 만드는 탈출구다

 대조 통과
      --> 체인을 계속 태운다. 이후 인증과 인가가 이어진다

 대조 실패
      --> 핸들러가 응답을 쓰고 끝난다
      --> 기본 핸들러는 AccessDeniedHandlerImpl 이라 403 이다
```

## 하위 메서드

- [01 CsrfTokenRepository.loadDeferredToken](01_CsrfTokenRepository.loadDeferredToken/README.md)
- [02 XorCsrfTokenRequestAttributeHandler.handle](02_XorCsrfTokenRequestAttributeHandler.handle/README.md)
