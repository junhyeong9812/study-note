# ProviderManager.authenticate

상위: [폼 로그인](../README.md)

`AuthenticationManager` 의 기본 구현이다. 직접 인증하지 않고, 등록된 프로바이더 중 이 토큰을 다룰 줄 아는 것에게 넘긴다.

## 위치

`core` / `org.springframework.security.authentication` / `ProviderManager.java` L166-L266 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/ProviderManager.java#L166-L266))

## 실제 코드

```java
// ProviderManager.java L166-L266
public Authentication authenticate(Authentication authentication) throws AuthenticationException {
    Class<? extends Authentication> toTest = authentication.getClass();
    AuthenticationException lastException = null;
    AuthenticationException parentException = null;
    Authentication result = null;
    Authentication parentResult = null;
    int currentPosition = 0;
    int size = this.providers.size();
    for (AuthenticationProvider provider : getProviders()) {
        if (!provider.supports(toTest)) {
            continue;
        }
        if (logger.isTraceEnabled()) {
            logger.trace(LogMessage.format("Authenticating request with %s (%d/%d)",
                    provider.getClass().getSimpleName(), ++currentPosition, size));
        }
        try {
            result = provider.authenticate(authentication);
            if (result != null) {
                copyDetails(authentication, result);
                break;
            }
        }
        catch (AccountStatusException ex) {
            prepareException(ex, authentication);
            logger.debug(LogMessage.format("Authentication failed for user '%s' since their account status is %s",
                    authentication.getName(), ex.getMessage()), ex);
            // SEC-546: Avoid polling additional providers if auth failure is due to
            // invalid account status
            throw ex;
        }
        catch (InternalAuthenticationServiceException ex) {
            prepareException(ex, authentication);
            logger.debug(LogMessage.format("Authentication service failed internally for user '%s'",
                    authentication.getName()), ex);
            // SEC-546: Avoid polling additional providers if auth failure is due to
            // invalid account status
            throw ex;
        }
        catch (AuthenticationException ex) {
            ex.setAuthenticationRequest(authentication);
            logger.debug(LogMessage.format("Authentication failed with provider %s since %s",
                    provider.getClass().getSimpleName(), ex.getMessage()));
            lastException = ex;
        }
    }
    if (result == null && this.parent != null) {
        // Allow the parent to try.
        try {
            parentResult = this.parent.authenticate(authentication);
            result = parentResult;
        }
        catch (ProviderNotFoundException ex) {
            // ignore as we will throw below if no other exception occurred prior to
            // calling parent and the parent
            // may throw ProviderNotFound even though a provider in the child already
            // handled the request
        }
        catch (AuthenticationException ex) {
            parentException = ex;
            lastException = ex;
        }
    }
    if (result != null) {
        if (this.eraseCredentialsAfterAuthentication && (result instanceof CredentialsContainer)) {
            // Authentication is complete. Remove credentials and other secret data
            // from authentication
            ((CredentialsContainer) result).eraseCredentials();
        }
        // If the parent AuthenticationManager was attempted and successful then it
        // will publish an AuthenticationSuccessEvent
        // This check prevents a duplicate AuthenticationSuccessEvent if the parent
        // AuthenticationManager already published it
        if (parentResult == null) {
            this.eventPublisher.publishAuthenticationSuccess(result);
        }

        return result;
    }

    // Parent was null, or didn't authenticate (or throw an exception).
    if (lastException == null) {
        lastException = new ProviderNotFoundException(this.messages.getMessage("ProviderManager.providerNotFound",
                new Object[] { toTest.getName() }, "No AuthenticationProvider found for {0}"));
    }
    // If the parent AuthenticationManager was attempted and failed then it will
    // publish an AbstractAuthenticationFailureEvent
    // This check prevents a duplicate AbstractAuthenticationFailureEvent if the
    // parent AuthenticationManager already published it
    if (parentException == null) {
        prepareException(lastException, authentication);
    }

    // Ensure this message is not logged when authentication is attempted by
    // the parent provider
    if (this.parent != null) {
        logger.debug("Denying authentication since all attempted providers failed");
    }

    throw lastException;
}
```

## 동작 흐름

```text
 authenticate(authentication)
 |
 +-- L174 for (AuthenticationProvider provider : getProviders())
 |      |
 |      +-- L175 provider.supports(toTest) 가 false 면 L176 건너뛴다
 |      |
 |      +-- L183 provider.authenticate(authentication)
 |      |      L184 결과가 null 이 아니면
 |      |             L185 copyDetails 로 details 를 옮기고
 |      |             L186 break -- 첫 성공에서 멈춘다
 |      |
 |      +-- L189 AccountStatusException  --> L195 즉시 다시 던진다
 |      +-- L197 InternalAuthenticationServiceException --> L203 즉시 던진다
 |      +-- L205 그 밖의 AuthenticationException
 |             L206 예외에 원래 요청을 담고
 |             L209 lastException 에 보관한 뒤 다음 프로바이더로 계속
 |
 +-- L212 결과가 없고 parent 가 있으면
 |      L215 parent.authenticate(authentication)
 |      L218 ProviderNotFoundException 은 삼킨다
 |      L224 다른 실패는 parentException 과 lastException 에 담는다
 |
 +-- L229 결과가 있으면
 |      L230 eraseCredentialsAfterAuthentication 이고 CredentialsContainer 면
 |             L233 eraseCredentials() -- 비밀번호를 지운다
 |      L239 parentResult 가 null 일 때만
 |             L240 publishAuthenticationSuccess
 |      L243 반환
 |
 +-- L247 보관된 예외가 하나도 없으면
        (아무도 supports 하지 않았거나, supports 한 프로바이더가
         예외 없이 null 만 돌려준 경우)
        L248 ProviderNotFoundException 을 만든다
        L255 parentException 이 없으면 L256 prepareException 으로 실패 이벤트 발행
        L265 던진다
```

```text
 예외 셋을 다르게 다룬다

 AccountStatusException                 계정이 잠겼다, 만료됐다
   --> 즉시 던진다. 다른 프로바이더에게 물어봐도 결과가 같다

 InternalAuthenticationServiceException 시스템 장애
   --> 즉시 던진다
   두 갈래 모두 코드 주석은 같은 말을 한다
     SEC-546: Avoid polling additional providers if auth failure is due to
     invalid account status

 그 밖의 AuthenticationException        비밀번호가 틀렸다 등
   --> 보관만 하고 다음 프로바이더로 넘어간다
       다른 프로바이더가 이 사용자를 알 수도 있다

 끝까지 아무도 성공하지 못하면 마지막 예외를 던진다
```

```text
 부모 매니저

 ProviderManager 는 parent 를 가질 수 있다
 자식이 전부 실패했을 때만 부모에게 물어본다 (L212)

 부모가 성공하면(parentResult != null) 성공 이벤트를 발행하지 않는다 (L239)
 부모 쪽에서 이미 발행했기 때문이다. 같은 로그인이 두 번 기록되지 않는다
```

```text
 자격 증명 지우기

 L230 eraseCredentialsAfterAuthentication 이 켜져 있으면
 결과 토큰이 CredentialsContainer 를 구현한 경우 credentials 를 지운다

 그래서 인증이 끝난 뒤 Authentication.getCredentials() 는 보통 null 이다
 세션에 평문 비밀번호가 남지 않는다
```

## 결과가 쓰이는 곳

```text
 반환한 Authentication
      --> 필터가 받아 SecurityContext 에 담는다
      --> isAuthenticated() 가 true 이고 authorities 가 채워져 있다

 copyDetails
      --> 결과 토큰에 details 가 아직 없을 때만 옮긴다 (L281)
      --> 폼 로그인에서는 프로바이더가 createSuccessAuthentication L231 에서
          이미 details 를 심어 두므로 여기서는 아무 일도 하지 않는다
      --> details 를 챙기지 않는 다른 프로바이더를 위한 안전망이다

 supports 로 거르는 구조
      --> 토큰 타입 하나에 프로바이더 하나가 대응한다
      --> OAuth2, LDAP, remember-me 가 같은 매니저에 함께 등록된다

 ProviderNotFoundException
      --> 아무도 이 토큰 타입을 다루지 못한다는 뜻이다
      --> 설정 실수일 때 나온다. 비밀번호 오류와는 다른 문제다
```

## 하위 메서드

- [03 AbstractUserDetailsAuthenticationProvider.authenticate](../03_AbstractUserDetailsAuthenticationProvider.authenticate/README.md)가 폼 로그인에서 실제로 불리는 프로바이더다.
