# WebSecurityCustomizer

상위: [spi](../README.md)

`WebSecurity` 를 직접 만지는 두 공개 통로 중 하나다. 다른 하나는 `WebSecurityConfigurer` 다.

## 위치

`config` / `org.springframework.security.config.annotation.web.configuration` / `WebSecurityCustomizer.java` L39-L48 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/web/configuration/WebSecurityCustomizer.java#L39-L48))

## 실제 코드

```java
// WebSecurityCustomizer.java L39-L48 (javadoc 생략)
@FunctionalInterface
public interface WebSecurityCustomizer {

    void customize(WebSecurity web);

}
```

## 흐름에서 불리는 자리

```text
 WebSecurityConfiguration.springSecurityFilterChain
   L128 커스터마이저마다
   L129 customize(webSecurity)
   L131 그 뒤에 build()
```

- [WebSecurityConfiguration.springSecurityFilterChain](../../01_WebSecurityConfiguration.springSecurityFilterChain/README.md)

## 구현 계층

```text
 WebSecurityCustomizer (@FunctionalInterface)
   +-- (프레임워크 구현 0건. 사용자가 @Bean 으로 등록한다)
```

## 결과가 쓰이는 곳

```text
 customize 안에서 할 수 있는 일
      --> ignoring() 으로 경로를 체인에서 빼기
      --> httpFirewall, requestRejectedHandler, debug 설정
      --> privilegeEvaluator 교체

 ignoring 을 권하지 않는 이유
      --> WebSecurity.performBuild 가 경고 로그를 남긴다
      --> 필터 0개 체인이라 SecurityContext 조차 세우지 않는다
      --> 대신 authorizeHttpRequests 의 permitAll 을 권한다

 호출 시점
      --> 체인 빌더들이 다 등록된 뒤, build() 직전이다
      --> 체인을 더 등록할 수는 있지만, 등록된 목록을 읽는 API 는 없다
```
