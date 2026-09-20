# DaoAuthenticationProvider.retrieveUser

상위: [AbstractUserDetailsAuthenticationProvider.authenticate](../README.md)

`UserDetailsService` 를 불러 사용자를 가져온다. 짧지만 타이밍 공격 방어가 끼어 있다.

## 위치

`core` / `org.springframework.security.authentication.dao` / `DaoAuthenticationProvider.java` L101-L123 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authentication/dao/DaoAuthenticationProvider.java#L101-L123))

## 실제 코드

```java
// DaoAuthenticationProvider.java L101-L123
@Override
protected final UserDetails retrieveUser(String username, UsernamePasswordAuthenticationToken authentication)
        throws AuthenticationException {
    prepareTimingAttackProtection();
    try {
        UserDetails loadedUser = this.getUserDetailsService().loadUserByUsername(username);
        if (loadedUser == null) {
            throw new InternalAuthenticationServiceException(
                    "UserDetailsService returned null, which is an interface contract violation");
        }
        return loadedUser;
    }
    catch (UsernameNotFoundException ex) {
        mitigateAgainstTimingAttack(authentication);
        throw ex;
    }
    catch (InternalAuthenticationServiceException ex) {
        throw ex;
    }
    catch (Exception ex) {
        throw new InternalAuthenticationServiceException(ex.getMessage(), ex);
    }
}
```

## 동작 흐름

```text
 retrieveUser(username, authentication)
 |
 | L104 prepareTimingAttackProtection()
 |        더미 비밀번호를 미리 인코딩해 둔다
 |
 +-- L106 getUserDetailsService().loadUserByUsername(username)
 |      |
 |      +-- L107 null 을 돌려주면
 |             L108 InternalAuthenticationServiceException (계약 위반)
 |      +-- L111 정상이면 그대로 반환
 |
 +-- L113 UsernameNotFoundException 이면
 |      L114 mitigateAgainstTimingAttack(authentication)
 |             있지도 않은 사용자에 대해 비밀번호 대조를 한 번 돌린다
 |      L115 예외를 그대로 던진다
 |
 +-- L117 InternalAuthenticationServiceException 이면 L118 그대로
 +-- L120 그 밖의 Exception 은
        L121 InternalAuthenticationServiceException 으로 감싼다
```

```text
 없는 사용자에게도 시간을 쓴다

 사용자가 있으면   조회 + 비밀번호 인코딩 대조  (느리다)
 사용자가 없으면   조회만 하고 바로 실패        (빠르다)

 이 차이를 재면 어떤 아이디가 존재하는지 알 수 있다

 그래서 L114 에서 더미 해시에 대고 matches 를 한 번 돌린다
 두 경우의 응답 시간을 비슷하게 만든다

 메시지를 똑같이 맞추는 hideUserNotFoundExceptions 와 짝을 이룬다
 한쪽은 내용을, 한쪽은 시간을 감춘다
```

```text
 final 메서드다

 L102 protected final UserDetails retrieveUser(...)
 하위 클래스가 이 경로를 덮어쓸 수 없다
 (그 이유는 소스에 적혀 있지 않다)
```

## 결과가 쓰이는 곳

```text
 돌려준 UserDetails
      --> 비밀번호 대조의 기준값(getPassword)이 된다
      --> authorities 가 인가 판정의 입력이 된다
      --> 계정 상태 플래그를 검사들이 읽는다

 UserDetailsService
      --> 사용자를 어디서 가져올지만 정한다
      --> JDBC, LDAP, 인메모리, 직접 구현 무엇이든 여기만 갈아 끼우면 된다

 감싼 예외
      --> DB 장애 같은 것이 InternalAuthenticationServiceException 이 된다
      --> ProviderManager 가 이것을 만나면 즉시 던진다
          다른 프로바이더로 넘어가지 않는다
```
