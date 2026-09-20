# SecurityConfigurer

상위: [spi](../README.md)

빌더에 끼어드는 계약이다. DSL 한 줄이 이 구현 하나에 대응한다.

## 위치

`config` / `org.springframework.security.config.annotation` / `SecurityConfigurer.java` L31-L51 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/SecurityConfigurer.java#L31-L51))

## 실제 코드

```java
// SecurityConfigurer.java L31-L51 (javadoc 생략)
public interface SecurityConfigurer<O, B extends SecurityBuilder<O>> {

    void init(B builder);

    void configure(B builder);

}
```

## 흐름에서 불리는 자리

```text
 AbstractConfiguredSecurityBuilder.doBuild
   L333 init()      -> L371 configurer.init(this)
   L336 configure() -> L386 configurer.configure(this)
```

- [AbstractConfiguredSecurityBuilder.doBuild](../../02_AbstractSecurityBuilder.build/01_AbstractConfiguredSecurityBuilder.doBuild/README.md)

## 구현 계층

```text
 SecurityConfigurer<O, B>
   +-- SecurityConfigurerAdapter        두 메서드에 빈 기본 구현을 준다
         +-- AbstractHttpConfigurer     HttpSecurity 용 공통 뼈대. disable() 을 준다
               +-- CsrfConfigurer, LogoutConfigurer, ExceptionHandlingConfigurer,
                   SessionManagementConfigurer, AuthorizeHttpRequestsConfigurer, ...
               +-- AbstractAuthenticationFilterConfigurer
                     +-- FormLoginConfigurer, ...
   +-- (사용자 구현)

 DSL 메서드 하나가 이 구현 하나를 등록하거나 기존 것을 꺼내 준다
```

## 결과가 쓰이는 곳

```text
 init
      --> 공유 객체를 심고 다른 설정자와 조율한다
      --> 이 단계에서 다른 설정자를 추가할 수도 있다
          빌더가 그것까지 init 해 준다

 configure
      --> 실제 필터를 만들어 addFilter 로 넣는다
      --> init 이 심어 둔 공유 객체를 꺼내 쓴다

 두 메서드로 나뉜 이유
      --> 설정자끼리 서로를 봐야 하기 때문이다
      --> 한 단계뿐이라면 등록 순서가 결과를 좌우하게 된다

 SecurityConfigurerAdapter
      --> 두 메서드에 빈 구현을 줘서 필요한 쪽만 덮어쓰게 한다
      --> 절반 가까이는 configure 만 구현하고, 나머지는 init 도 함께 구현한다
```
