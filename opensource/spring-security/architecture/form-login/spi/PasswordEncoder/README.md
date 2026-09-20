# PasswordEncoder

상위: [spi](../README.md)

비밀번호를 해시하고, 보낸 값과 저장된 해시를 대조한다.

## 위치

`crypto` / `org.springframework.security.crypto.password` / `PasswordEncoder.java` L31-L69 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/crypto/src/main/java/org/springframework/security/crypto/password/PasswordEncoder.java#L31-L69))

## 실제 코드

```java
// PasswordEncoder.java L31-L69 (javadoc 생략)
public interface PasswordEncoder {

    @Contract("!null -> !null; null -> null")
    @Nullable String encode(@Nullable CharSequence rawPassword);

    boolean matches(@Nullable CharSequence rawPassword, @Nullable String encodedPassword);

    default boolean upgradeEncoding(@Nullable String encodedPassword) {
        return false;
    }

}
```

## 흐름에서 불리는 자리

```text
 DaoAuthenticationProvider.additionalAuthenticationChecks
   L89 passwordEncoder.get().matches(presentedPassword, userDetails.getPassword())
```

- [DaoAuthenticationProvider.additionalAuthenticationChecks](../../03_AbstractUserDetailsAuthenticationProvider.authenticate/02_DaoAuthenticationProvider.additionalAuthenticationChecks/README.md)

## 구현 계층

```text
 PasswordEncoder
   +-- DelegatingPasswordEncoder   저장된 값의 {접두}를 보고 실제 인코더를 고른다
   +-- BCryptPasswordEncoder
   +-- Argon2PasswordEncoder, Pbkdf2PasswordEncoder, SCryptPasswordEncoder
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 matches
      --> 평문을 같은 방식으로 해시해 비교한다
      --> 저장된 해시를 평문으로 되돌리지 않는다

 encode
      --> 회원 가입이나 비밀번호 변경에서 쓴다
      --> 같은 평문이라도 salt 가 달라 매번 다른 값이 나온다
          그래서 encode 한 값끼리 비교하면 안 된다

 upgradeEncoding
      --> 인터페이스 default 는 false 지만 기본 경로에서는 돌지 않는다
          DelegatingPasswordEncoder 의 상위 AbstractValidatingPasswordEncoder 가
          L57 에서 final 로 오버라이드한다
      --> 저장된 {id} 가 현재 인코딩 id 와 다르면 true 를 돌려준다
      --> 다만 true 라도 기본 설정에서는 재저장이 일어나지 않는다
          DaoAuthenticationProvider L136-138 이 userDetailsPasswordService 가
          NOOP 이 아닐 것을 함께 요구하는데, 그 필드의 기본값이 NOOP 이다 (L71)
          UserDetailsPasswordService 를 등록해야 업그레이드가 동작한다

 {접두} 방식
      --> DelegatingPasswordEncoder 가 {bcrypt}, {noop} 같은 접두를 읽는다
      --> 옛 해시와 새 해시가 한 테이블에 섞여 있어도 함께 검증된다
```
