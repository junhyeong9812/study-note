# SecurityBuilder

상위: [spi](../README.md)

메서드 하나짜리 계약이다. 무엇을 만드는지는 타입 인자가 정한다.

## 위치

`config` / `org.springframework.security.config.annotation` / `SecurityBuilder.java` L26-L35 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/SecurityBuilder.java#L26-L35))

## 실제 코드

```java
// SecurityBuilder.java L26-L35 (javadoc 생략)
public interface SecurityBuilder<O> {

    O build();

}
```

## 흐름에서 불리는 자리

```text
 사용자의 @Bean 메서드
   return http.build();

 WebSecurityConfiguration
   this.webSecurity.build()   이쪽은 Filter 를 만든다
```

- [AbstractSecurityBuilder.build](../../02_AbstractSecurityBuilder.build/README.md)

## 구현 계층

```text
 SecurityBuilder<O>
   +-- AbstractSecurityBuilder<O>            한 번만 빌드되게 막는다
         +-- AbstractConfiguredSecurityBuilder<O, B>  설정자를 받아 3단계로 돈다
               +-- HttpSecurity         -> DefaultSecurityFilterChain
               +-- WebSecurity          -> Filter (FilterChainProxy)
               +-- AuthenticationManagerBuilder -> AuthenticationManager
```

## 결과가 쓰이는 곳

```text
 타입 인자 O
      --> 같은 뼈대로 전혀 다른 것을 만든다
      --> HttpSecurity 는 체인 하나, WebSecurity 는 그 체인들을 묶은 필터

 build() 하나뿐인 계약
      --> 어떻게 만드는지는 계약에 없다
      --> 3단계(init/configure/performBuild)는 AbstractConfiguredSecurityBuilder 의
          구현 세부이지 이 인터페이스의 약속이 아니다
```
