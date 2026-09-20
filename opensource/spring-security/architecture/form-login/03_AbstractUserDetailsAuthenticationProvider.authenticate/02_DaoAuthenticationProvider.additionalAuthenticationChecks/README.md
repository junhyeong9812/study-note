# DaoAuthenticationProvider.additionalAuthenticationChecks

상위: [AbstractUserDetailsAuthenticationProvider.authenticate](../README.md)

비밀번호를 실제로 대조하는 곳이다. 폼 로그인 전체에서 "맞다/틀리다"가 갈리는 한 줄이 여기 있다.

## 위치

`core` / `org.springframework.security.authentication.dao` / `DaoAuthenticationProvider.java` L80-L94 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/dao/DaoAuthenticationProvider.java#L80-L94))

## 실제 코드

```java
// DaoAuthenticationProvider.java L80-L94
@Override
protected void additionalAuthenticationChecks(UserDetails userDetails,
        UsernamePasswordAuthenticationToken authentication) throws AuthenticationException {
    if (authentication.getCredentials() == null) {
        this.logger.debug("Failed to authenticate since no credentials provided");
        throw new BadCredentialsException(this.messages
            .getMessage("AbstractUserDetailsAuthenticationProvider.badCredentials", "Bad credentials"));
    }
    String presentedPassword = authentication.getCredentials().toString();
    if (!this.passwordEncoder.get().matches(presentedPassword, userDetails.getPassword())) {
        this.logger.debug("Failed to authenticate since password does not match stored value");
        throw new BadCredentialsException(this.messages
            .getMessage("AbstractUserDetailsAuthenticationProvider.badCredentials", "Bad credentials"));
    }
}
```

## 동작 흐름

```text
 additionalAuthenticationChecks(userDetails, authentication)
 |
 +-- L83 authentication.getCredentials() 가 null 이면
 |        L85 BadCredentialsException
 |
 | L88 presentedPassword = credentials.toString()   사용자가 보낸 평문
 |
 +-- L89 passwordEncoder.get().matches(presentedPassword, userDetails.getPassword())
 |        false 면 L91 BadCredentialsException
 |
 +-- 통과하면 아무것도 하지 않고 끝난다 (예외 없음 = 성공)
```

```text
 matches 이지 equals 가 아니다

 저장된 값    {bcrypt}$2a$10$....   해시
 보낸 값      평문

 matches(평문, 해시) 가 평문을 같은 방식으로 해시해 비교한다
 저장된 해시를 되돌리지 않는다. 되돌릴 수 없다

 앞의 {bcrypt} 접두가 어떤 알고리즘으로 대조할지 알려 준다
 DelegatingPasswordEncoder 가 그 접두를 보고 실제 인코더를 고른다
```

```text
 두 실패의 메시지가 같다

 L85 자격 증명이 아예 없음
 L91 비밀번호가 틀림

 둘 다 같은 메시지 키를 쓴다
   AbstractUserDetailsAuthenticationProvider.badCredentials

 사용자 없음도 상위에서 같은 예외로 바뀐다
 즉 아이디가 틀렸는지 비밀번호가 틀렸는지 밖에서는 구분할 수 없다
```

## 결과가 쓰이는 곳

```text
 예외를 던지지 않음
      --> 성공이라는 뜻이다. 반환값이 없다
      --> 호출한 performPreCheck 가 그대로 빠져나간다

 던진 BadCredentialsException
      --> AbstractUserDetailsAuthenticationProvider 를 거쳐
      --> ProviderManager 가 보관했다가 마지막에 던진다
      --> 필터의 unsuccessfulAuthentication 이 받는다

 PasswordEncoder
      --> 이 자리를 바꾸면 해시 방식이 바뀐다
      --> 기본은 DelegatingPasswordEncoder 라
          저장된 값의 접두를 보고 알고리즘을 고른다
          옛 해시와 새 해시가 섞여 있어도 함께 검증된다
```

비밀번호 저장 형식을 업그레이드하는 경로(`upgradeEncoding`, `UserDetailsPasswordService`)는 `createSuccessAuthentication` 안에 있고, 이 문서에서는 다루지 않는다.
