# SecurityFilterChain

상위: [spi](../README.md)

체인 하나를 나타내는 계약이다. 메서드가 둘뿐이다.

## 위치

`web` / `org.springframework.security.web` / `SecurityFilterChain.java` L33-L39 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/SecurityFilterChain.java#L33-L39))

## 실제 코드

```java
// SecurityFilterChain.java L33-L39
public interface SecurityFilterChain {

    boolean matches(HttpServletRequest request);

    List<Filter> getFilters();

}
```

## 흐름에서 불리는 자리

```text
 FilterChainProxy.getFilters
   등록된 체인을 순서대로 돌며 matches(request) 를 묻고
   true 인 첫 체인의 getFilters() 를 가져간다
```

- [FilterChainProxy.getFilters](../../01_FilterChainProxy.doFilter/01_FilterChainProxy.doFilterInternal/01_FilterChainProxy.getFilters/README.md)

## 구현 계층

```text
 SecurityFilterChain
   +-- DefaultSecurityFilterChain   RequestMatcher 하나 + 필터 목록
   |     HttpSecurity.performBuild 가 만드는 것이 이것이다
   +-- (사용자 구현)
```

## 결과가 쓰이는 곳

```text
 matches
      --> 체인 선택의 유일한 기준이다
      --> 설정의 securityMatcher 가 이 매처가 된다
      --> 주지 않으면 모든 요청에 맞는 매처가 들어간다

 getFilters
      --> 이 목록의 순서가 곧 보안 처리 순서다
      --> 빈 목록을 돌려주면 그 요청은 보안 없이 통과한다
