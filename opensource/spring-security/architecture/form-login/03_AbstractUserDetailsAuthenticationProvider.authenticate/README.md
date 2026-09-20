# AbstractUserDetailsAuthenticationProvider.authenticate

상위: [폼 로그인](../README.md)

사용자를 찾고, 검사를 돌리고, 인증된 토큰을 만든다. 사용자를 어떻게 찾는지와 비밀번호를 어떻게 대조하는지는 하위 클래스에 맡긴다.

## 위치

`core` / `org.springframework.security.authentication.dao` / `AbstractUserDetailsAuthenticationProvider.java` L135-L180 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/dao/AbstractUserDetailsAuthenticationProvider.java#L135-L180))

## 실제 코드

```java
// AbstractUserDetailsAuthenticationProvider.java L135-L180
public Authentication authenticate(Authentication authentication) throws AuthenticationException {
    Assert.isInstanceOf(UsernamePasswordAuthenticationToken.class, authentication,
            () -> this.messages.getMessage("AbstractUserDetailsAuthenticationProvider.onlySupports",
                    "Only UsernamePasswordAuthenticationToken is supported"));
    String username = determineUsername(authentication);
    boolean cacheWasUsed = true;
    UserDetails user = this.userCache.getUserFromCache(username);
    if (user == null) {
        cacheWasUsed = false;
        try {
            user = retrieveUser(username, (UsernamePasswordAuthenticationToken) authentication);
        }
        catch (UsernameNotFoundException ex) {
            this.logger.debug(LogMessage.format("Failed to find user '%s'", username));
            String message = this.messages.getMessage("AbstractUserDetailsAuthenticationProvider.badCredentials",
                    "Bad credentials");
            if (!this.hideUserNotFoundExceptions) {
                throw ex;
            }
            throw new BadCredentialsException(message, ex);
        }
        Assert.notNull(user, "retrieveUser returned null - a violation of the interface contract");
    }
    try {
        performPreCheck(user, (UsernamePasswordAuthenticationToken) authentication);
    }
    catch (AuthenticationException ex) {
        if (!cacheWasUsed) {
            throw ex;
        }
        // There was a problem, so try again after checking
        // we're using latest data (i.e. not from the cache)
        cacheWasUsed = false;
        user = retrieveUser(username, (UsernamePasswordAuthenticationToken) authentication);
        performPreCheck(user, (UsernamePasswordAuthenticationToken) authentication);
    }
    this.postAuthenticationChecks.check(user);
    if (!cacheWasUsed) {
        this.userCache.putUserInCache(user);
    }
    Object principalToReturn = user;
    if (this.forcePrincipalAsString) {
        principalToReturn = user.getUsername();
    }
    return createSuccessAuthentication(principalToReturn, authentication, user);
}
```

검사를 묶은 private 메서드가 바로 아래 있다.

`core` / `org.springframework.security.authentication.dao` / `AbstractUserDetailsAuthenticationProvider.java` L182-L199 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/dao/AbstractUserDetailsAuthenticationProvider.java#L182-L199))

```java
// AbstractUserDetailsAuthenticationProvider.java L182-L199
private void performPreCheck(UserDetails user, UsernamePasswordAuthenticationToken authentication) {
    try {
        this.preAuthenticationChecks.check(user);
    }
    catch (AuthenticationException ex) {
        if (!this.alwaysPerformAdditionalChecksOnUser) {
            throw ex;
        }
        try {
            additionalAuthenticationChecks(user, authentication);
        }
        catch (AuthenticationException ignored) {
            // preserve the original failed check
        }
        throw ex;
    }
    additionalAuthenticationChecks(user, authentication);
}
```

## 동작 흐름

```text
 authenticate(authentication)
 |
 | L136 UsernamePasswordAuthenticationToken 인지 확인한다
 | L139 determineUsername(authentication)
 |
 +-- L141 userCache.getUserFromCache(username)
 |      |
 |      +-- L142 캐시에 없으면
 |             L143 cacheWasUsed = false
 |             L145 retrieveUser(username, token)   하위 클래스가 구현
 |             |
 |             +-- L147 UsernameNotFoundException 이면
 |                    L151 hideUserNotFoundExceptions 가 꺼져 있으면 L152 그대로 던지고
 |                    L154 켜져 있으면 BadCredentialsException 으로 바꿔 던진다
 |             L156 null 을 돌려주면 계약 위반이므로 터뜨린다
 |
 +-- L159 performPreCheck(user, token)
 |      |
 |      +-- L161 여기서 실패했는데 L162 캐시를 쓴 것이었다면
 |             L167 캐시를 버리고 L168 다시 조회해
 |             L169 한 번 더 검사한다
 |             캐시가 낡아서 생긴 실패를 구제한다
 |
 | L171 postAuthenticationChecks.check(user)
 | L172 캐시를 안 썼으면 L173 캐시에 넣는다
 |
 | L175 principalToReturn = user
 | L176 forcePrincipalAsString 이면 L177 이름 문자열로 바꾼다
 |
 +-- L179 createSuccessAuthentication(principalToReturn, authentication, user)
```

```text
 performPreCheck 가 검사 둘을 묶는다 (L182-199)

 L184 preAuthenticationChecks.check(user)
        계정 잠김, 비활성, 만료를 본다
 L198 additionalAuthenticationChecks(user, authentication)
        비밀번호 대조. 하위 클래스가 구현한다

 pre 검사가 실패하면 (L186)
   L187 alwaysPerformAdditionalChecksOnUser 가 꺼져 있으면 L188 바로 던진다
   켜져 있으면 L191 비밀번호 대조도 해 보고
   L193 그 결과와 무관하게 L196 원래 실패를 던진다

 alwaysPerformAdditionalChecksOnUser 는 기본 true 다 (L100)
 setter 의 javadoc 이 이유를 밝힌다 -- 계정 상태와 무관하게
 인증에 걸리는 시간을 같게 만들기 위해서다 (L347-350)
```

```text
 검사 세 자리

 preAuthenticationChecks   계정 상태 (잠김, 비활성, 만료)
 additionalAuthenticationChecks  비밀번호  <- DaoAuthenticationProvider
 postAuthenticationChecks  비밀번호 만료 (isCredentialsNonExpired)

 앞의 둘은 performPreCheck 안에서, 마지막은 L171 에서 따로 돈다
 즉 비밀번호 대조가 끝난 뒤에 만료 검사가 온다
```

## 결과가 쓰이는 곳

```text
 createSuccessAuthentication 의 결과
      --> principal 이 UserDetails 객체다 (forcePrincipalAsString 이 아니면)
      --> authorities 는 authoritiesMapper 가 매핑한 UserDetails 권한에
          FACTOR_PASSWORD 권한을 하나 더한 것이다 (L226-228)
          기본 매퍼는 NullAuthoritiesMapper 라 매핑 자체는 그대로 통과시킨다
      --> ProviderManager 가 이것을 받아 필터로 돌려준다

 hideUserNotFoundExceptions
      --> 기본으로 켜져 있어 "없는 사용자"가 "비밀번호 틀림"으로 나간다
      --> 어떤 아이디가 존재하는지 알아내는 것을 막는다

 UserCache
      --> 기본은 NullUserCache 로 아무것도 캐시하지 않는다
      --> 캐시를 붙이면 매 로그인마다 DB 를 치지 않는다
          대신 낡은 데이터 문제가 생겨 L162-169 의 재조회 경로가 필요해진다
```

## 하위 메서드

- [01 DaoAuthenticationProvider.retrieveUser](01_DaoAuthenticationProvider.retrieveUser/README.md)
- [02 DaoAuthenticationProvider.additionalAuthenticationChecks](02_DaoAuthenticationProvider.additionalAuthenticationChecks/README.md)
