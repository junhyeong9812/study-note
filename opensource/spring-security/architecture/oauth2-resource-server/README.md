# OAuth2 리소스 서버

`Authorization: Bearer <JWT>` 헤더 하나가 서명 검증과 클레임 검증을 거쳐 인증된 `Authentication` 이 되기까지다. [폼 로그인](../form-login/README.md)과 같은 매니저 위에 다른 프로바이더를 끼운 갈래다. 사용자를 조회하지 않고 토큰만 검증한다는 점이 가장 크게 다르다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 디코더와 변환 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 GET /api/me   Authorization: Bearer eyJhbGc...
 |
 +-- [01] BearerTokenAuthenticationFilter.doFilterInternal
 |        헤더에서 토큰을 꺼내 토큰 객체를 만든다
 |        없으면 체인으로 그냥 흘린다 (401 을 내지 않는다)
 |        성공하면 컨텍스트에 심고 저장소에 저장한다
 |
 +-- [02] JwtAuthenticationProvider.authenticate
 |        디코더로 JWT 를 풀고, 변환기로 권한을 만든다
 |        디코딩 실패의 종류에 따라 예외를 갈라 던진다
 |
 +-- [02-01] NimbusJwtDecoder.decode
          파싱 -> 서명 검증 -> 클레임 검증
          세 단계가 각각 다른 예외를 던진다
```

```text
 폼 로그인과 나란히 보기

 폼 로그인                          리소스 서버
 POST /login 만 가로챈다            모든 요청에서 헤더를 본다
 파라미터에서 아이디/비밀번호        헤더에서 Bearer 토큰
 UsernamePasswordAuthenticationToken BearerTokenAuthenticationToken
 DaoAuthenticationProvider          JwtAuthenticationProvider
 UserDetailsService 로 사용자 조회   토큰 자체에 정보가 들어 있다
 PasswordEncoder.matches            서명 검증 + 클레임 검증
 세션 저장소가 기본            요청 속성 저장소가 기본 (다음 요청에 안 남는다)

 매니저(ProviderManager)와 SecurityContext 계약은 그대로 공유한다
```

```text
 토큰이 없으면 막지 않는다

 L174 authenticationRequest == null 이면
 L176 filterChain.doFilter 로 그냥 흘린다

 즉 이 필터는 "토큰이 있으면 검증한다"만 한다
 인증이 필요한지는 뒤의 인가 필터가 정한다

 그래서 permitAll 경로에 토큰 없이 접근하는 것이 자연스럽게 통과한다
```

```text
 검증이 세 겹이다

 파싱       구조가 JWT 맞는가            BadJwtException
 서명 검증  발급자가 서명한 것이 맞는가   JOSEException -> JwtException
 클레임 검증 typ, 만료(exp), nbf, 인증서 지문        JwtValidationException

 앞의 둘은 NimbusJwtDecoder 안에서,
 셋째는 그 안의 OAuth2TokenValidator 가 한다

 발급자(iss) 검증은 기본 조합에 없다
 issuer-uri 로 디코더를 만들 때 JwtIssuerValidator 가 더해진다
```

## 어디에서 쓰이는가

```text
 [필터 체인] 이 필터가 체인의 한 칸이다
 [보안 컨텍스트] 성공하면 컨텍스트를 만들어 저장소에 저장한다
 [인가] 그 결과의 권한으로 AuthorizationFilter 가 판정한다
 [폼 로그인] 같은 AuthenticationManager 계약 위에 있다
```

같은 매니저 계약은 [폼 로그인](../form-login/README.md), 저장된 컨텍스트의 의미는 [보안 컨텍스트](../security-context/README.md)에 있다.

## 단계

1. [BearerTokenAuthenticationFilter.doFilterInternal](01_BearerTokenAuthenticationFilter.doFilterInternal/README.md)이 토큰을 꺼낸다.
2. [JwtAuthenticationProvider.authenticate](02_JwtAuthenticationProvider.authenticate/README.md)가 검증을 지휘한다.
3. [NimbusJwtDecoder.decode](02_JwtAuthenticationProvider.authenticate/01_NimbusJwtDecoder.decode/README.md)가 JWT 를 푼다.

## 결과가 쓰이는 곳

```text
 인증된 Authentication
      --> principal 이 Jwt 객체다. 클레임을 그대로 들고 있다
      --> 컨트롤러가 @AuthenticationPrincipal Jwt 로 받을 수 있다

 권한(authorities)
      --> 토큰의 scope 나 scp 클레임에서 변환기가 만든다
      --> 기본 접두는 SCOPE_ 다

 저장소에 저장된 컨텍스트
      --> 필터의 기본 저장소는 RequestAttributeSecurityContextRepository 다 (L94)
      --> 요청 속성에 실제로 저장한다. 다만 다음 요청에는 복원되지 않는다
      --> 설정(OAuth2ResourceServerConfigurer)도 이것을 덮어쓰지 않는다

 실패
      --> AuthenticationException 이 실패 핸들러로 간다
      --> 기본 핸들러는 AuthenticationServiceException 만 다시 던지고
          나머지는 진입점으로 보낸다
      --> 진입점은 WWW-Authenticate 헤더를 붙이고
          오류 종류에 따라 400/401/403 을 쓴다
```

## 다루지 않는 것

불투명 토큰(introspection) 경로, `JwtAuthenticationConverter` 의 권한 변환 규칙과 접두 설정, `JwtDecoders` 의 발급자 기반 자동 구성과 JWK 세트 조회·캐싱, `OAuth2TokenValidator` 구현들(`JwtTimestampValidator`, `JwtIssuerValidator`), DPoP 토큰, `AuthenticationManagerResolver` 를 쓰는 멀티 테넌시, 리액티브 판은 같은 뼈대의 곁가지라 요약만 했다. JWT/JOSE 명세와 Nimbus 라이브러리 자체도 범위 밖이다.

## 하위 메서드

- [01 BearerTokenAuthenticationFilter.doFilterInternal](01_BearerTokenAuthenticationFilter.doFilterInternal/README.md)
- [02 JwtAuthenticationProvider.authenticate](02_JwtAuthenticationProvider.authenticate/README.md)
- [spi](spi/README.md) — JWT 디코더, 토큰 검증기
