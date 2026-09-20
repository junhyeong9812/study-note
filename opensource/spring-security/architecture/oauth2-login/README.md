# OAuth2 로그인

"구글로 로그인"이 눌린 뒤 벌어지는 일이다. 한 번의 요청으로 끝나는 [폼 로그인](../form-login/README.md)과 달리 **요청이 두 번 오간다** — 인가 서버로 보내는 리다이렉트, 그리고 돌아오는 콜백. 그래서 필터도 둘이다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 클라이언트 등록과 요청 저장 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [1단계] 나가는 길

 GET /oauth2/authorization/google
 |
 +-- [01] OAuth2AuthorizationRequestRedirectFilter.doFilterInternal
          리졸버가 인가 요청을 만들면 리다이렉트하고 끝낸다
          만들지 못하면 체인을 계속 태운다
          체인 안에서 "인가가 필요하다"는 예외가 올라와도
          같은 리다이렉트를 건다

 [2단계] 돌아오는 길

 GET /login/oauth2/code/google?code=...&state=...
 |
 +-- [02] OAuth2LoginAuthenticationFilter.attemptAuthentication
          저장해 둔 인가 요청을 꺼낸다 (없으면 거부)
          매니저에게 넘겨 코드를 토큰으로 바꾸게 한다
          결과를 인증 토큰으로 바꾸고 인가된 클라이언트를 저장한다
```

```text
 폼 로그인과 나란히 보기

 폼 로그인                        OAuth2 로그인
 요청 한 번                       요청 두 번 (리다이렉트 + 콜백)
 필터 하나                        필터 둘
 비밀번호를 우리가 받는다          비밀번호를 우리가 보지 않는다
 UserDetailsService 로 조회        인가 서버가 토큰을 준다
 -                                인가 요청을 저장해 뒀다 꺼낸다

 둘째 필터는 AbstractAuthenticationProcessingFilter 를 상속한다
 그래서 성공 처리와 컨텍스트 저장은 폼 로그인과 같은 코드를 쓴다
```

```text
 왜 인가 요청을 저장하는가

 나갈 때   state, redirect_uri, registrationId 를 만들어 저장한다
           공개 클라이언트이거나 PKCE 를 요구하도록 설정했으면 PKCE 검증값이,
           openid 스코프면 nonce 가 함께 들어간다
 돌아올 때 저장한 것을 꺼낸다

 짝이 없으면 authorization_request_not_found 로 거부한다
 state 비교 자체는 기본 저장소 구현과 프로바이더가 한다

 기본 저장소는 세션을 쓴다 (두 필터의 필드 기본값)
```

```text
 두 번째 필터가 하는 일이 셋이다

 1. 짝 확인        저장된 인가 요청을 꺼낸다. 없으면 거부
 2. 토큰 교환      매니저가 code 를 access token 으로 바꾼다
 3. 클라이언트 저장 받은 토큰을 OAuth2AuthorizedClient 로 저장한다

 세 번째가 폼 로그인에는 없는 단계다
 이후 그 사용자를 대신해 API 를 호출할 때 이 토큰을 꺼내 쓴다
```

## 어디에서 쓰이는가

```text
 [필터 체인] 두 필터가 각각 체인의 한 칸이다
 [폼 로그인] 둘째 필터가 같은 추상 클래스를 상속한다
 [보안 컨텍스트] 성공 처리와 저장은 폼 로그인과 같은 경로다
 [실패 처리] 두 필터 모두 예외를 스스로 잡아 실패 핸들러에 넘긴다
   진입점으로 올라가지 않는다
```

성공 이후의 공통 처리는 [폼 로그인](../form-login/README.md), 저장된 컨텍스트의 의미는 [보안 컨텍스트](../security-context/README.md)에 있다.

## 단계

1. [OAuth2AuthorizationRequestRedirectFilter.doFilterInternal](01_OAuth2AuthorizationRequestRedirectFilter.doFilterInternal/README.md)이 인가 서버로 보낸다.
2. [OAuth2LoginAuthenticationFilter.attemptAuthentication](02_OAuth2LoginAuthenticationFilter.attemptAuthentication/README.md)이 콜백을 받아 인증한다.

## 결과가 쓰이는 곳

```text
 저장된 인가 요청
      --> 콜백에서 꺼낸다. 없으면 거부다
      --> 기본 저장소가 꺼낼 때 state 를 비교하고, 프로바이더가 한 번 더 본다
      --> 꺼내면서 지운다. 한 번만 쓸 수 있다

 OAuth2AuthenticationToken
      --> principal 이 OAuth2User 다. 인가 서버가 준 속성을 들고 있다
      --> 권한은 사용자 속성 권한과 스코프마다 붙는 SCOPE_ 권한이고,
          거기에 매퍼 결과와 인증 팩터 권한이 더해진다

 OAuth2AuthorizedClient
      --> access token 과 refresh token 을 담아 저장한다
      --> 나중에 그 사용자를 대신해 API 를 호출할 때 쓴다
      --> 인증 정보와 별도로 보관된다

 실패
      --> 첫째 필터는 OAuth2AuthorizationRequestException(내부 클래스),
          둘째 필터는 OAuth2AuthenticationException 을 실패 핸들러로 넘긴다
      --> 오류 코드가 무엇이 틀렸는지 알려 준다
```

## 다루지 않는 것

코드-토큰 교환의 세부(`OAuth2AuthorizationCodeAuthenticationProvider`, `OAuth2AccessTokenResponseClient`), `OidcAuthorizationCodeAuthenticationProvider`와 ID 토큰 검증, `OAuth2UserService` 가 사용자 정보를 가져오는 경로, PKCE 와 `state` 생성 규칙, `OAuth2AuthorizedClientManager` 의 토큰 갱신, 리액티브 판은 같은 뼈대의 곁가지라 요약만 했다. OAuth2/OIDC 명세 자체도 범위 밖이다.

## 하위 메서드

- [01 OAuth2AuthorizationRequestRedirectFilter.doFilterInternal](01_OAuth2AuthorizationRequestRedirectFilter.doFilterInternal/README.md)
- [02 OAuth2LoginAuthenticationFilter.attemptAuthentication](02_OAuth2LoginAuthenticationFilter.attemptAuthentication/README.md)
- [spi](spi/README.md) — 클라이언트 등록 저장소, 인가 요청 저장소
