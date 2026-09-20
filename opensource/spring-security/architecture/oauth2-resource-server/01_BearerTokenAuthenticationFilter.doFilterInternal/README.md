# BearerTokenAuthenticationFilter.doFilterInternal

상위: [OAuth2 리소스 서버](../README.md)

헤더에서 토큰을 꺼내 인증하고, 성공하면 컨텍스트에 심는다. `OncePerRequestFilter` 를 상속해 요청당 한 번 돈다.

## 위치

`oauth2/oauth2-resource-server` / `org.springframework.security.oauth2.server.resource.web.authentication` / `BearerTokenAuthenticationFilter.java` L161-L216 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-resource-server/src/main/java/org/springframework/security/oauth2/server/resource/web/authentication/BearerTokenAuthenticationFilter.java#L161-L216))

## 실제 코드

```java
// BearerTokenAuthenticationFilter.java L161-L216
@Override
protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
        throws ServletException, IOException {
    Authentication authenticationRequest;
    try {
        authenticationRequest = this.authenticationConverter.convert(request);
    }
    catch (OAuth2AuthenticationException invalid) {
        this.logger.trace("Sending to authentication entry point since failed to resolve bearer token", invalid);
        this.authenticationEntryPoint.commence(request, response, invalid);
        return;
    }

    if (authenticationRequest == null) {
        this.logger.trace("Did not process request since did not find bearer token");
        filterChain.doFilter(request, response);
        return;
    }

    try {
        AuthenticationManager authenticationManager = this.authenticationManagerResolver.resolve(request);
        Authentication authenticationResult = authenticationManager.authenticate(authenticationRequest);
        if (isDPoPBoundAccessToken(authenticationResult)) {
            // Prevent downgraded usage of DPoP-bound access tokens,
            // by rejecting a DPoP-bound access token received as a bearer token.
            BearerTokenError error = BearerTokenErrors.invalidToken("Invalid bearer token");
            throw new OAuth2AuthenticationException(error);
        }
        Authentication current = this.securityContextHolderStrategy.getContext().getAuthentication();
        if (current != null && current.isAuthenticated() && declaresToBuilder(authenticationResult)) {
            authenticationResult = authenticationResult.toBuilder().authorities((a) -> {
                Set<String> newAuthorities = a.stream()
                    .map(GrantedAuthority::getAuthority)
                    .collect(Collectors.toUnmodifiableSet());
                for (GrantedAuthority currentAuthority : current.getAuthorities()) {
                    if (!newAuthorities.contains(currentAuthority.getAuthority())) {
                        a.add(currentAuthority);
                    }
                }
            }).build();
        }
        SecurityContext context = this.securityContextHolderStrategy.createEmptyContext();
        context.setAuthentication(authenticationResult);
        this.securityContextHolderStrategy.setContext(context);
        this.securityContextRepository.saveContext(context, request, response);
        if (this.logger.isDebugEnabled()) {
            this.logger.debug(LogMessage.format("Set SecurityContextHolder to %s", authenticationResult));
        }
        filterChain.doFilter(request, response);
    }
    catch (AuthenticationException failed) {
        this.securityContextHolderStrategy.clearContext();
        this.logger.trace("Failed to process authentication request", failed);
        this.authenticationFailureHandler.onAuthenticationFailure(request, response, failed);
    }
}
```

## 동작 흐름

```text
 doFilterInternal(request, response, filterChain)
 |
 +-- L166 authenticationConverter.convert(request)
 |      |
 |      +-- L168 OAuth2AuthenticationException 이면
 |             L170 진입점을 부르고 L171 return
 |             (토큰이 있는데 형식이 틀린 경우다)
 |
 +-- L174 결과가 null 이면 (토큰이 아예 없다)
 |      L176 filterChain.doFilter 로 흘리고 L177 return
 |
 | try (L180)
 |   L181 authenticationManagerResolver.resolve(request)
 |   L182 authenticationManager.authenticate(authenticationRequest)
 |
 |   L183 DPoP 로 묶인 토큰을 Bearer 로 받았으면
 |          L186-187 invalid_token 으로 거부한다
 |
 |   L189 현재 컨텍스트의 인증을 꺼내
 |   L190 이미 인증돼 있고 결과가 toBuilder 를 선언했으면
 |          L191-200 기존 권한 중 새 결과에 없는 것을 더한다
 |
 |   L202 createEmptyContext()
 |   L203 setAuthentication(결과)
 |   L204 setContext(컨텍스트)
 |   L205 securityContextRepository.saveContext(...)
 |   L209 filterChain.doFilter
 |
 catch (L211) AuthenticationException
     L212 컨텍스트를 비우고
     L214 실패 핸들러를 부른다
```

```text
 없는 것과 틀린 것을 다르게 다룬다

 토큰이 아예 없다        L174 -> 체인으로 그냥 통과
 토큰이 있는데 형식 오류  L168 -> 진입점으로
                          invalid_token 이면 401, invalid_request 면 400
 토큰이 있고 검증 실패    L211 -> 실패 핸들러로

 첫째가 통과인 것이 중요하다
 permitAll 경로에 토큰 없이 접근하는 것을 막지 않는다
 "인증이 필요한가"는 뒤의 인가 필터가 정한다
```

```text
 폼 로그인과 같은 저장 절차

 L202-205 는 AbstractAuthenticationProcessingFilter.successfulAuthentication 과
 같은 네 줄이다
   빈 컨텍스트 생성 -> 인증 심기 -> 홀더에 얹기 -> 저장소에 저장

 다만 기본 저장소가 다르다
 폼 로그인은 세션을 쓰는 저장소를 받고,
 이 필터의 기본값은 RequestAttributeSecurityContextRepository 다 (L94)
 요청 속성에 저장하므로 다음 요청에는 복원되지 않는다
```

```text
 권한 병합 분기 (L190-201)

 이미 인증된 상태에서 Bearer 토큰이 또 들어오면
 기존 권한 중 새 결과에 없는 것을 더해 준다

 폼 로그인의 MFA 분기와 비슷한 모양이지만 관문이 둘 적다
 이쪽 조건은 셋이다 -- 현재 인증이 있고, authenticated 이고,
 결과 토큰이 toBuilder 를 선언했을 것

 폼 로그인 쪽에는 mfaEnabled 플래그와
 현재 사용자 이름이 결과와 같은지 보는 검사가 더 있다
 즉 여기서는 이름이 다른 주체의 권한도 병합된다
```

## 결과가 쓰이는 곳

```text
 컨버터가 만든 토큰
      --> BearerTokenAuthenticationToken 이다
      --> JwtAuthenticationProvider 의 supports 가 이 타입을 본다

 authenticationManagerResolver
      --> 요청마다 다른 매니저를 고를 수 있다
      --> 멀티 테넌시에서 발급자별로 다른 검증을 걸 때 쓴다

 실패 시 컨텍스트 비우기 (L212)
      --> 이전 인증이 남아 있지 않게 한다
      --> 폼 로그인의 unsuccessfulAuthentication 과 같은 처리다

 DPoP 검사 (L183-188)
      --> DPoP 로 발급된 토큰을 그냥 Bearer 로 쓰는 것을 막는다
      --> 코드 주석이 "다운그레이드 사용 방지"라고 밝힌다
```
