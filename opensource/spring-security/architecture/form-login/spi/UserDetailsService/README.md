# UserDetailsService

상위: [spi](../README.md)

사용자를 어디서 가져올지만 정한다. 비밀번호를 대조하지 않는다.

## 위치

`core` / `org.springframework.security.core.userdetails` / `UserDetailsService.java` L34-L49 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/core/userdetails/UserDetailsService.java#L34-L49))

## 실제 코드

```java
// UserDetailsService.java L34-L49 (javadoc 생략)
public interface UserDetailsService {

    UserDetails loadUserByUsername(String username) throws UsernameNotFoundException;

}
```

## 흐름에서 불리는 자리

```text
 DaoAuthenticationProvider.retrieveUser
   L106 getUserDetailsService().loadUserByUsername(username)
```

- [DaoAuthenticationProvider.retrieveUser](../../03_AbstractUserDetailsAuthenticationProvider.authenticate/01_DaoAuthenticationProvider.retrieveUser/README.md)

## 구현 계층

```text
 UserDetailsService
   +-- InMemoryUserDetailsManager   메모리. 테스트와 예제
   +-- JdbcDaoImpl                  JDBC
   |     +-- JdbcUserDetailsManager  생성/수정까지 더한다
   +-- CachingUserDetailsService    다른 구현을 감싸 캐시한다
   +-- (LDAP 등 모듈별 구현)
   +-- (사용자 구현 -- 실무에서는 보통 이쪽)

 UserDetailsManager 는 이 인터페이스를 확장해
 사용자 생성, 수정, 삭제까지 계약에 넣은 것이다
```

## 결과가 쓰이는 곳

```text
 돌려준 UserDetails
      --> getPassword() 가 비밀번호 대조의 기준값이다
      --> getAuthorities() 가 인가 판정의 입력이 된다
      --> 계정 상태 플래그(잠김, 만료, 활성)를 검사들이 읽는다

 없는 사용자
      --> UsernameNotFoundException 을 던져야 한다
      --> null 을 돌려주면 계약 위반이라
          DaoAuthenticationProvider 가 L108 에서 터뜨린다

 예외가 밖에서 보이지 않는 이유
      --> hideUserNotFoundExceptions 가 기본으로 켜져 있어
          BadCredentialsException 으로 바뀌어 나간다
      --> 어떤 아이디가 존재하는지 흘리지 않는다
```
