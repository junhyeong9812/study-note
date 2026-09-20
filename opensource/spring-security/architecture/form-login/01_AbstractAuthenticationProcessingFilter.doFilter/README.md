# AbstractAuthenticationProcessingFilter.doFilter

상위: [폼 로그인](../README.md)

인증 필터들의 공통 뼈대다. 폼 로그인뿐 아니라 OAuth2 로그인도 이 클래스를 상속한다.

## 위치

`web` / `org.springframework.security.web.authentication` / `AbstractAuthenticationProcessingFilter.java` L243-L291 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/AbstractAuthenticationProcessingFilter.java#L243-L291))

## 실제 코드

public 진입점은 캐스팅만 한다.

```java
// AbstractAuthenticationProcessingFilter.java L237-L241
@Override
public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    doFilter((HttpServletRequest) request, (HttpServletResponse) response, chain);
}
```

```java
// AbstractAuthenticationProcessingFilter.java L243-L291
private void doFilter(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    if (!requiresAuthentication(request, response)) {
        chain.doFilter(request, response);
        return;
    }
    try {
        Authentication authenticationResult = attemptAuthentication(request, response);
        if (authenticationResult == null) {
            if (this.continueChainWhenNoAuthenticationResult) {
                chain.doFilter(request, response);
                return;
            }
            // return immediately as subclass has indicated that it hasn't completed
            return;
        }
        Authentication current = this.securityContextHolderStrategy.getContext().getAuthentication();
        if (shouldPerformMfa(current, authenticationResult)) {
            authenticationResult = authenticationResult.toBuilder()
            // @formatter:off
                .authorities((a) -> {
                    Set<String> newAuthorities = a.stream()
                        .map(GrantedAuthority::getAuthority)
                        .collect(Collectors.toUnmodifiableSet());
                    for (GrantedAuthority currentAuthority : current.getAuthorities()) {
                        if (!newAuthorities.contains(currentAuthority.getAuthority())) {
                            a.add(currentAuthority);
                        }
                    }
                })
                .build();
                // @formatter:on
        }
        this.sessionStrategy.onAuthentication(authenticationResult, request, response);
        // Authentication success
        if (this.continueChainBeforeSuccessfulAuthentication) {
            chain.doFilter(request, response);
        }
        successfulAuthentication(request, response, chain, authenticationResult);
    }
    catch (InternalAuthenticationServiceException failed) {
        this.logger.error("An internal error occurred while trying to authenticate the user.", failed);
        unsuccessfulAuthentication(request, response, failed);
    }
    catch (AuthenticationException ex) {
        // Authentication failed
        unsuccessfulAuthentication(request, response, ex);
    }
}
```

## 동작 흐름

```text
 doFilter(request, response, chain)
 |
 +-- L245 requiresAuthentication(request, response)
 |        RequestMatcher 로 판단한다. 기본은 POST /login
 |        아니면 L246 chain.doFilter 로 흘리고 L247 return
 |
 +-- L249 try
        L250 attemptAuthentication(request, response)
        |      하위 클래스가 오버라이드하거나, 안 하면 L358-369 의 기본 구현
        |
        +-- L251 결과가 null 이면
        |      L252 continueChainWhenNoAuthenticationResult 가 켜져 있으면
        |             L253 체인을 계속 태우고 L254 return
        |      L257 아니면 그냥 return (응답은 하위 클래스가 이미 썼다)
        |
        L259 현재 컨텍스트의 Authentication 을 꺼낸다
        L260 shouldPerformMfa 면 기존 권한을 새 결과에 합친다 (L261-275)
        |
        L276 sessionStrategy.onAuthentication(...)
        |      세션 고정 방어 등이 여기서 돈다
        |
        L278 continueChainBeforeSuccessfulAuthentication 이면
        |      L279 체인을 먼저 태운다
        |
        L281 successfulAuthentication(request, response, chain, result)

 catch L283 InternalAuthenticationServiceException
        L284 error 로 로깅하고 L285 unsuccessfulAuthentication
 catch L287 AuthenticationException
        L289 unsuccessfulAuthentication
```

```text
 예외를 두 갈래로 잡는 이유

 InternalAuthenticationServiceException  시스템 문제 (DB 장애 등)
        L284 에서 error 레벨로 남긴다. 운영자가 봐야 할 일이다
 AuthenticationException                 인증 실패 (비밀번호 틀림 등)
        catch 에서는 따로 남기지 않는다

 둘 다 unsuccessfulAuthentication 으로 간다
 거기서 trace 로 세 줄 남는다 (L423-425)
 즉 실패는 trace 에만, 시스템 문제는 error 에도 남는다
```

```text
 attemptAuthentication 이 더 이상 abstract 가 아니다

 이 클래스에 기본 구현이 있다 (L358-369)
   authenticationConverter.convert(request) 로 토큰을 만들고
   authenticationManager.authenticate(...) 를 부른다

 UsernamePasswordAuthenticationFilter 는 이것을 오버라이드한다
 즉 하위 클래스는 컨버터를 끼우거나 메서드를 덮어쓰거나 둘 중 하나를 고른다
```

```text
 MFA 분기 (L260, mfaEnabled 가 켜졌을 때만)

 shouldPerformMfa 는 넷을 모두 만족해야 true 다 (L294-305)
   mfaEnabled 가 켜져 있고
   현재 인증이 있고 authenticated 이며
   결과 토큰에 무인자 toBuilder() 메서드가 선언돼 있고
   현재 사용자 이름과 결과의 이름이 같다

 만족하면 기존 권한 중 새 결과에 없는 것을 더해 준다
 이름이 같은지 확인하는 L304 로 미루어, 같은 사용자가
 두 번째 수단을 통과한 경우를 다루는 것으로 보인다
 (소스에 그 설명이 적혀 있지는 않다)
```

## 결과가 쓰이는 곳

```text
 attemptAuthentication 의 반환
      --> null 이면 "아직 안 끝났다"는 뜻이다
      --> OAuth2 처럼 리다이렉트로 이어지는 방식이 이 값을 쓴다

 sessionStrategy.onAuthentication
      --> 인증 직후, 컨텍스트를 저장하기 전에 불린다
      --> 세션 ID 를 갈아 끼우는 세션 고정 방어가 이 자리다

 successfulAuthentication
      --> 컨텍스트 저장과 성공 핸들러 호출이 전부 여기서 일어난다

 unsuccessfulAuthentication
      --> L422 컨텍스트를 비우고
      --> L426 rememberMeServices.loginFail
      --> L427 실패 핸들러를 부른다
```

## 하위 메서드

- [01 UsernamePasswordAuthenticationFilter.attemptAuthentication](01_UsernamePasswordAuthenticationFilter.attemptAuthentication/README.md)
- [02 AbstractAuthenticationProcessingFilter.successfulAuthentication](02_AbstractAuthenticationProcessingFilter.successfulAuthentication/README.md)
