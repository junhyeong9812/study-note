# OAuth2LoginAuthenticationFilter.attemptAuthentication

상위: [OAuth2 로그인](../README.md)

콜백을 받아 인증한다. `AbstractAuthenticationProcessingFilter` 를 상속하므로 [폼 로그인](../../form-login/README.md)의 `attemptAuthentication` 자리에 해당한다.

## 위치

`oauth2/oauth2-client` / `org.springframework.security.oauth2.client.web` / `OAuth2LoginAuthenticationFilter.java` L166-L214 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/oauth2/oauth2-client/src/main/java/org/springframework/security/oauth2/client/web/OAuth2LoginAuthenticationFilter.java#L166-L214))

## 실제 코드

```java
// OAuth2LoginAuthenticationFilter.java L166-L214
@Override
public Authentication attemptAuthentication(HttpServletRequest request, HttpServletResponse response)
        throws AuthenticationException {
    MultiValueMap<String, String> params = OAuth2AuthorizationResponseUtils.toMultiMap(request.getParameterMap());
    if (!OAuth2AuthorizationResponseUtils.isAuthorizationResponse(params)) {
        OAuth2Error oauth2Error = new OAuth2Error(OAuth2ErrorCodes.INVALID_REQUEST);
        throw new OAuth2AuthenticationException(oauth2Error, oauth2Error.toString());
    }
    OAuth2AuthorizationRequest authorizationRequest = this.authorizationRequestRepository
        .removeAuthorizationRequest(request, response);
    if (authorizationRequest == null) {
        OAuth2Error oauth2Error = new OAuth2Error(AUTHORIZATION_REQUEST_NOT_FOUND_ERROR_CODE);
        throw new OAuth2AuthenticationException(oauth2Error, oauth2Error.toString());
    }
    String registrationId = authorizationRequest.getAttribute(OAuth2ParameterNames.REGISTRATION_ID);
    Assert.hasText(registrationId, "registrationId cannot be empty");
    ClientRegistration clientRegistration = this.clientRegistrationRepository.findByRegistrationId(registrationId);
    if (clientRegistration == null) {
        OAuth2Error oauth2Error = new OAuth2Error(CLIENT_REGISTRATION_NOT_FOUND_ERROR_CODE,
                "Client Registration not found with Id: " + registrationId, null);
        throw new OAuth2AuthenticationException(oauth2Error, oauth2Error.toString());
    }
    // @formatter:off
    String redirectUri = UriComponentsBuilder.fromUriString(UrlUtils.buildFullRequestUrl(request))
            .replaceQuery(null)
            .build()
            .toUriString();
    // @formatter:on
    OAuth2AuthorizationResponse authorizationResponse = OAuth2AuthorizationResponseUtils.convert(params,
            redirectUri);
    Object authenticationDetails = this.authenticationDetailsSource.buildDetails(request);
    OAuth2LoginAuthenticationToken authenticationRequest = new OAuth2LoginAuthenticationToken(clientRegistration,
            new OAuth2AuthorizationExchange(authorizationRequest, authorizationResponse));
    authenticationRequest.setDetails(authenticationDetails);
    OAuth2LoginAuthenticationToken authenticationResult = (OAuth2LoginAuthenticationToken) this
        .getAuthenticationManager()
        .authenticate(authenticationRequest);
    OAuth2AuthenticationToken oauth2Authentication = this.authenticationResultConverter
        .convert(authenticationResult);
    Assert.notNull(oauth2Authentication, "authentication result cannot be null");
    oauth2Authentication.setDetails(authenticationDetails);
    Assert.notNull(authenticationResult.getAccessToken(), "accessToken cannot be null");
    OAuth2AuthorizedClient authorizedClient = new OAuth2AuthorizedClient(
            authenticationResult.getClientRegistration(), oauth2Authentication.getName(),
            authenticationResult.getAccessToken(), authenticationResult.getRefreshToken());

    this.authorizedClientRepository.saveAuthorizedClient(authorizedClient, oauth2Authentication, request, response);
    return oauth2Authentication;
}
```

## 동작 흐름

```text
 attemptAuthentication(request, response)
 |
 | L169 파라미터를 MultiValueMap 으로 모은다
 |
 +-- L170 인가 응답 형태가 아니면
 |        L172 invalid_request 로 거부
 |
 | L174 authorizationRequestRepository.removeAuthorizationRequest(...)
 |        꺼내면서 지운다
 |
 +-- L176 저장된 것이 없으면
 |        L178 authorization_request_not_found 로 거부
 |
 | L180 저장된 인가 요청에서 registrationId 를 꺼내
 | L182 clientRegistrationRepository.findByRegistrationId(...)
 |
 +-- L183 등록 정보가 없으면
 |        L186 client_registration_not_found 로 거부
 |
 | L189 현재 URL 에서 쿼리를 떼어 redirectUri 를 만든다
 | L194 파라미터와 redirectUri 로 인가 응답 객체를 만든다
 | L196 요청 details 를 만든다
 |
 | L197 OAuth2LoginAuthenticationToken 을 만든다
 |        등록 정보 + (인가 요청, 인가 응답) 쌍을 담는다
 | L200 getAuthenticationManager().authenticate(...)
 |        여기서 code 가 access token 으로 바뀐다
 |
 | L203 authenticationResultConverter.convert(결과)
 |        OAuth2AuthenticationToken 으로 바꾼다
 | L206 details 를 옮긴다
 |
 | L208 OAuth2AuthorizedClient 를 만든다
 |        등록 정보, 사용자 이름, access token, refresh token
 | L212 authorizedClientRepository.saveAuthorizedClient(...)
 |
 +-- L213 인증 토큰을 반환
```

```text
 거부가 세 갈래다

 L170 인가 응답 형태가 아님        invalid_request
 L176 저장된 인가 요청이 없음      authorization_request_not_found
 L183 클라이언트 등록이 없음       client_registration_not_found

 둘째는 이 필터가 state 를 대조해서가 아니다
 이 필터는 "저장된 짝이 있느냐"만 본다 (L176 의 null 검사)

 실제 대조는 두 군데서 일어난다
   기본 저장소 HttpSessionOAuth2AuthorizationRequestRepository L50-56 이
     요청의 state 와 저장된 state 를 비교해 다르면 null 을 준다
   프로바이더가 다시 비교해 invalid_state_parameter 를 낸다

 즉 여기서 걸리는 것은 기본 구현에 기댄 결과이지 계약의 보장이 아니다
```

```text
 꺼내면서 지운다 (L174)

 remove 라는 이름 그대로 조회와 삭제가 한 번에 일어난다
 기본 구현은 load 한 뒤 세션 속성을 지운다
 그래서 같은 콜백을 두 번 쓸 수 없다
```

```text
 토큰 두 종류가 각자의 자리로 간다

 인증 정보   OAuth2AuthenticationToken -> SecurityContext (L213 반환 후)
 접근 토큰   OAuth2AuthorizedClient    -> 인가된 클라이언트 저장소 (L212)

 클래스 javadoc 이 이 두 갈래를 그대로 적고 있다

 폼 로그인에는 둘째가 없다
```

```text
 반환한 뒤는 폼 로그인과 같다

 이 메서드는 AbstractAuthenticationProcessingFilter.doFilter 가 부른다
 반환값을 받아 successfulAuthentication 이 컨텍스트를 만들고 저장한다

 즉 이 아래 절차는 폼 로그인과 글자 그대로 같은 코드다
```

## 결과가 쓰이는 곳

```text
 반환한 OAuth2AuthenticationToken
      --> principal 이 OAuth2User 다
      --> 인가 서버가 준 속성(이름, 이메일 등)을 들고 있다

 저장된 OAuth2AuthorizedClient
      --> 나중에 그 사용자를 대신해 API 를 호출할 때 꺼내 쓴다
      --> refresh token 이 있으면 만료 시 갱신할 수 있다

 authenticationResultConverter
      --> 인증 결과를 최종 토큰 타입으로 바꾸는 자리다
      --> 기본 구현(L241-245)은 principal, 권한, registrationId 를 옮겨 담기만 한다
      --> 권한을 만드는 곳은 프로바이더와 OAuth2UserService 쪽이다

 details
      --> L196 에서 한 번 만들어 요청 토큰(L199)과 결과 토큰(L206) 양쪽에 심는다
      --> 매니저는 details 를 넘겨준다. 끊기는 곳은 컨버터다
          L241-245 가 새 토큰을 만들면서 details 를 가져가지 않는다
```
