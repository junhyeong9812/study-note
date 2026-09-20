# OAuth2AuthorizationRequestRedirectFilter.doFilterInternal

상위: [OAuth2 로그인](../README.md)

인가 서버로 보내는 리다이렉트를 만든다. 진입 경로는 둘이지만 `try` 는 셋이다 — 리졸브(L182), 체인 위임(L194), 재시도(L206).

## 위치

`oauth2/oauth2-client` / `org.springframework.security.oauth2.client.web` / `OAuth2AuthorizationRequestRedirectFilter.java` L179-L229 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-client/src/main/java/org/springframework/security/oauth2/client/web/OAuth2AuthorizationRequestRedirectFilter.java#L179-L229))

## 실제 코드

```java
// OAuth2AuthorizationRequestRedirectFilter.java L179-L229
@Override
protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
        throws ServletException, IOException {
    try {
        OAuth2AuthorizationRequest authorizationRequest = this.authorizationRequestResolver.resolve(request);
        if (authorizationRequest != null) {
            this.sendRedirectForAuthorization(request, response, authorizationRequest);
            return;
        }
    }
    catch (Exception ex) {
        AuthenticationException wrappedException = new OAuth2AuthorizationRequestException(ex);
        this.authenticationFailureHandler.onAuthenticationFailure(request, response, wrappedException);
        return;
    }
    try {
        filterChain.doFilter(request, response);
    }
    catch (IOException ex) {
        throw ex;
    }
    catch (Exception ex) {
        // Check to see if we need to handle ClientAuthorizationRequiredException
        Throwable[] causeChain = this.throwableAnalyzer.determineCauseChain(ex);
        ClientAuthorizationRequiredException authzEx = (ClientAuthorizationRequiredException) this.throwableAnalyzer
            .getFirstThrowableOfType(ClientAuthorizationRequiredException.class, causeChain);
        if (authzEx != null) {
            try {
                OAuth2AuthorizationRequest authorizationRequest = this.authorizationRequestResolver.resolve(request,
                        authzEx.getClientRegistrationId());
                if (authorizationRequest == null) {
                    throw authzEx;
                }
                this.requestCache.saveRequest(request, response);
                this.sendRedirectForAuthorization(request, response, authorizationRequest);
            }
            catch (Exception failed) {
                AuthenticationException wrappedException = new OAuth2AuthorizationRequestException(ex);
                this.authenticationFailureHandler.onAuthenticationFailure(request, response, wrappedException);
            }
            return;
        }
        if (ex instanceof ServletException) {
            throw (ServletException) ex;
        }
        if (ex instanceof RuntimeException) {
            throw (RuntimeException) ex;
        }
        throw new RuntimeException(ex);
    }
}
```

실제 리다이렉트는 바로 아래에서 일어난다.

`oauth2/oauth2-client` / `org.springframework.security.oauth2.client.web` / `OAuth2AuthorizationRequestRedirectFilter.java` L231-L238 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-client/src/main/java/org/springframework/security/oauth2/client/web/OAuth2AuthorizationRequestRedirectFilter.java#L231-L238))

```java
// OAuth2AuthorizationRequestRedirectFilter.java L231-L238
private void sendRedirectForAuthorization(HttpServletRequest request, HttpServletResponse response,
        OAuth2AuthorizationRequest authorizationRequest) throws IOException {
    if (AuthorizationGrantType.AUTHORIZATION_CODE.equals(authorizationRequest.getGrantType())) {
        this.authorizationRequestRepository.saveAuthorizationRequest(authorizationRequest, request, response);
    }
    this.authorizationRedirectStrategy.sendRedirect(request, response,
            authorizationRequest.getAuthorizationRequestUri());
}
```

## 동작 흐름

```text
 doFilterInternal(request, response, filterChain)
 |
 | try (L182)
 |   L183 authorizationRequestResolver.resolve(request)
 |   |
 |   +-- L184 인가 요청을 만들었으면
 |          L185 sendRedirectForAuthorization -> L186 return
 |   |
 |   +-- 못 만들었으면 (이 요청은 로그인 시작이 아니다) 아래로
 |
 | catch (L189) 리졸브 또는 리다이렉트 전송 중 예외
 |   L190 OAuth2AuthorizationRequestException 으로 감싸
 |   L191 실패 핸들러 -> L192 return
 |
 | try (L194)
 |   L195 filterChain.doFilter   평범하게 체인을 태운다
 |
 | catch (L197) IOException 이면 L198 그대로 던진다
 |
 | catch (L200) 그 밖의 예외
     L202 원인 사슬을 편다
     L203 ClientAuthorizationRequiredException 을 찾는다
     |
     +-- L205 찾았으면
     |     L207 그 registrationId 로 인가 요청을 다시 만든다
     |     L209 못 만들면 L210 잡아낸 ClientAuthorizationRequiredException 을 던진다
     |            이 throw 도 바로 아래 L215 catch 에 걸린다
     |     L212 requestCache.saveRequest   가려던 곳을 저장한다
     |     L213 sendRedirectForAuthorization
     |     L215 그 과정이 실패하면 L217 실패 핸들러
     |     L219 return
     |
     +-- L221 못 찾았으면 타입을 보존해 다시 던진다
           ServletException / RuntimeException / 그 밖은 RuntimeException 으로 감싼다
```

```text
 진입이 두 갈래다

 직접 진입   GET /oauth2/authorization/google
             L183 리졸버가 바로 인가 요청을 만든다

 간접 진입   보호된 자원을 쓰려다 토큰이 없어서
             체인 안쪽에서 ClientAuthorizationRequiredException 이 올라온다
             L205 그것을 잡아 같은 리다이렉트를 건다

 둘째 경로에서만 requestCache.saveRequest 를 부른다 (L212)
 원래 가려던 곳으로 되돌아가야 하기 때문이다
```

```text
 예외 변환 필터와 같은 도구를 쓴다

 L202-204 determineCauseChain + getFirstThrowableOfType
 L221-227 타입을 보존해 다시 던지는 rethrow 패턴

 ExceptionTranslationFilter 와 FilterChainProxy 가 쓰는 것과 같다
 체인 깊은 곳의 예외를 타입으로 건져 내는 공통 수법이다
```

```text
 리다이렉트 전에 저장한다 (L233-235)

 L233 은 AUTHORIZATION_CODE 그랜트일 때만 저장한다

 다만 지금 빌더는 그랜트 타입을 AUTHORIZATION_CODE 로 고정한다
 (OAuth2AuthorizationRequest L287, 세터가 없다)
 그래서 이 조건은 사실상 항상 참인 과거의 잔재다

 순서는 저장(L234)이 먼저고 리다이렉트(L236)가 나중이다
```

## 결과가 쓰이는 곳

```text
 저장된 인가 요청
      --> 콜백을 받는 둘째 필터가 꺼내 쓴다
      --> state 대조의 기준값이다

 리다이렉트 응답
      --> 체인이 거기서 끊긴다
      --> 브라우저가 인가 서버로 이동한다

 저장된 원래 요청 (requestCache)
      --> 간접 진입 경로에서만 저장한다
      --> 로그인이 끝나면 그리로 되돌아간다

 OAuth2AuthorizationRequestException
      --> 이 필터 안의 private 중첩 클래스이고 AuthenticationException 을 상속한다
      --> L190 은 리졸브·리다이렉트 실패를,
          L216 은 체인에서 올라온 원래 예외를 감싼다
      --> 실패 핸들러가 받아 응답을 만든다. 진입점으로 올라가지 않는다
```
