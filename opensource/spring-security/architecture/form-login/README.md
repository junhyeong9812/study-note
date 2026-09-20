# 폼 로그인

`POST /login` 하나가 `UserDetails` 조회와 비밀번호 대조를 거쳐 인증된 `Authentication` 이 되기까지다. Spring Security 에서 가장 자주 읽히는 경로이고, 인증의 기본 뼈대가 여기 다 들어 있다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 인증 계약 모음이다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 POST /login  username=jun&password=...
 |
 +-- [01] AbstractAuthenticationProcessingFilter.doFilter
 |        이 요청이 로그인 요청인가부터 본다 (아니면 체인으로 흘린다)
 |        인증을 시도하고, 성공/실패를 각각 처리한다
 |
 +-- [01-01] UsernamePasswordAuthenticationFilter.attemptAuthentication
 |        파라미터에서 username 과 password 를 꺼내
 |        아직 인증되지 않은 토큰을 만들어 매니저에 넘긴다
 |
 +-- [02] ProviderManager.authenticate
 |        등록된 AuthenticationProvider 를 순서대로 물어본다
 |        supports 가 true 인 것만 시도한다
 |        하나가 성공하면 거기서 멈춘다
 |
 +-- [03] AbstractUserDetailsAuthenticationProvider.authenticate
 |        캐시 -> 없으면 retrieveUser 로 사용자를 찾고
 |        검사들을 돌린 뒤 인증된 토큰을 만든다
 |
 +-- [03-01] DaoAuthenticationProvider.retrieveUser
 |        UserDetailsService.loadUserByUsername 을 부른다
 |
 +-- [03-02] DaoAuthenticationProvider.additionalAuthenticationChecks
 |        PasswordEncoder.matches 로 비밀번호를 대조한다  <- 실제 대조 지점
 |
 +-- [01-02] AbstractAuthenticationProcessingFilter.successfulAuthentication
          컨텍스트를 만들어 ThreadLocal 에 얹고
          저장소에 저장하고, 성공 핸들러를 부른다
```

```text
 토큰이 두 번 만들어진다

 unauthenticated  UsernamePasswordAuthenticationToken.unauthenticated(username, password)
                  principal = "jun" (문자열), credentials = 평문 비밀번호
                  isAuthenticated() == false

 authenticated    createSuccessAuthentication 이 만든다
                  principal = UserDetails 객체, authorities 채워짐
                  isAuthenticated() == true

 같은 클래스지만 의미가 다르다
 인증 전 토큰은 "이 사람이라고 주장한다", 인증 후 토큰은 "확인했다"
```

```text
 책임이 네 겹으로 나뉘어 있다

 필터     HTTP 를 안다. 파라미터를 꺼내고 응답을 쓴다
 매니저   누가 처리할지 고른다. HTTP 를 모른다
 프로바이더  인증 방식 하나를 안다 (아이디/비밀번호, LDAP, OAuth2 ...)
 UserDetailsService  사용자를 어디서 가져올지만 안다

 그래서 DB 를 LDAP 으로 바꿔도 필터와 매니저는 그대로다
```

## 어디에서 쓰이는가

```text
 [필터 체인] 이 필터가 체인의 한 칸이다. /login 이 아니면 그냥 흘려보낸다
 [보안 컨텍스트] 성공하면 컨텍스트를 만들어 저장소에 저장한다
 [인가] 그 결과로 만들어진 Authentication 을 AuthorizationFilter 가 읽는다
 [예외 변환] 실패하면 AuthenticationException 이 되어 진입점으로 간다
```

이 필터가 체인의 어디에 있는지는 [필터 체인](../filter-chain/README.md), 저장된 컨텍스트가 다음 요청에 어떻게 복원되는지는 [보안 컨텍스트](../security-context/README.md)에 있다.

## 단계

1. [AbstractAuthenticationProcessingFilter.doFilter](01_AbstractAuthenticationProcessingFilter.doFilter/README.md)가 로그인 요청을 받는다.
2. [UsernamePasswordAuthenticationFilter.attemptAuthentication](01_AbstractAuthenticationProcessingFilter.doFilter/01_UsernamePasswordAuthenticationFilter.attemptAuthentication/README.md)이 토큰을 만든다.
3. [ProviderManager.authenticate](02_ProviderManager.authenticate/README.md)가 프로바이더를 고른다.
4. [AbstractUserDetailsAuthenticationProvider.authenticate](03_AbstractUserDetailsAuthenticationProvider.authenticate/README.md)가 사용자를 찾고 검사한다.
5. [DaoAuthenticationProvider.additionalAuthenticationChecks](03_AbstractUserDetailsAuthenticationProvider.authenticate/02_DaoAuthenticationProvider.additionalAuthenticationChecks/README.md)가 비밀번호를 대조한다.
6. [AbstractAuthenticationProcessingFilter.successfulAuthentication](01_AbstractAuthenticationProcessingFilter.doFilter/02_AbstractAuthenticationProcessingFilter.successfulAuthentication/README.md)이 결과를 저장한다.

## 결과가 쓰이는 곳

```text
 인증된 Authentication
      --> SecurityContext 에 담겨 ThreadLocal 에 얹힌다
      --> 저장소에도 저장되어 다음 요청에 복원된다
      --> getAuthorities() 가 인가 판정의 입력이 된다

 principal 에 담긴 UserDetails
      --> 컨트롤러의 @AuthenticationPrincipal 이 이것을 받는다
      --> eraseCredentials 가 기본으로 켜져 있어 비밀번호는 지워진다

 실패 시 AuthenticationException
      --> 실패 핸들러가 받아 리다이렉트나 401 을 만든다
      --> 사용자 없음도 기본 설정에서는 BadCredentialsException 이 된다
          (존재 여부를 흘리지 않기 위한 hideUserNotFoundExceptions)

 발행되는 이벤트
      --> 성공하면 둘이 순서대로 발행된다
          ProviderManager L240  AuthenticationSuccessEvent
          필터 L404            InteractiveAuthenticationSuccessEvent
      --> 뒤의 것은 앞의 것을 상속하지 않는다.
          javadoc 이 중복 발행을 피하기 위해서라고 밝힌다
      --> 실패하면 prepareException 이 AbstractAuthenticationFailureEvent 를 발행한다
      --> 로그인 감사나 마지막 로그인 시각 기록이 이것들을 듣는다
```

## 다루지 않는 것

`RememberMeServices`의 토큰 발급과 복원, `SessionAuthenticationStrategy`의 세션 고정 방어, `AuthenticationSuccessHandler` / `AuthenticationFailureHandler`의 구현별 리다이렉트 규칙, `UserCache`의 캐시 전략, MFA(`mfaEnabled`) 분기의 세부, 유출 비밀번호 검사(`CompromisedPasswordChecker`), 비밀번호 인코딩 업그레이드(`UserDetailsPasswordService`), 기본 로그인 페이지 생성(`DefaultLoginPageConfigurer`)은 같은 뼈대의 곁가지라 요약만 했다. HTTP Basic, OAuth2, LDAP 등 다른 인증 방식은 같은 매니저 위에 다른 프로바이더를 끼운 갈래다.

## 하위 메서드

- [01 AbstractAuthenticationProcessingFilter.doFilter](01_AbstractAuthenticationProcessingFilter.doFilter/README.md)
- [02 ProviderManager.authenticate](02_ProviderManager.authenticate/README.md)
- [03 AbstractUserDetailsAuthenticationProvider.authenticate](03_AbstractUserDetailsAuthenticationProvider.authenticate/README.md)
- [spi](spi/README.md) — 인증 매니저, 프로바이더, 사용자 조회, 비밀번호 인코더
