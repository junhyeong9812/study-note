# FilterChainValidator

상위: [spi](../README.md)

완성된 `FilterChainProxy` 를 기동 시점에 검사한다. `FilterChainProxy` 안의 중첩 인터페이스다.

## 위치

`web` / `org.springframework.security.web` / `FilterChainProxy.java` L392-L396 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/FilterChainProxy.java#L392-L396))

## 실제 코드

```java
// FilterChainProxy.java L392-L396
public interface FilterChainValidator {

    void validate(FilterChainProxy filterChainProxy);

}
```

## 흐름에서 불리는 자리

```text
 WebSecurity.performBuild
   L354 filterChainProxy.setFilterChainValidator(new WebSecurityFilterChainValidator())
   L356 filterChainProxy.afterPropertiesSet()   여기서 validate 가 돈다
```

- [WebSecurity.performBuild](../../02_WebSecurity.performBuild/README.md)

## 구현 계층

```text
 FilterChainProxy.FilterChainValidator
   +-- NullFilterChainValidator        기본. 아무것도 하지 않는다
   +-- WebSecurityFilterChainValidator Java 설정 경로가 꽂는다
   +-- DefaultFilterChainValidator     XML 네임스페이스 경로가 꽂는다
```

## 결과가 쓰이는 곳

```text
 기본이 NullFilterChainValidator 인 점
      --> FilterChainProxy 를 직접 만들면 검증이 없다
      --> Java 설정과 XML 네임스페이스는 각자 실제 검증기를 꽂는다
      --> 직접 new FilterChainProxy 를 하는 경로에서만 검증이 없다

 WebSecurityFilterChainValidator 가 하는 검사 셋 (L49-53)
      --> 매처 없는 체인(AnyRequestMatcher) 뒤에 다른 체인이 오는 경우
          UnreachableFilterChainException 으로 기동을 멈춘다
      --> 같은 매처가 중복되는 경우도 예외로 막는다
      --> 인가 필터 구성도 살피는데, 이쪽은 예외가 아니라 경고 로그만 남긴다

 기동 시점에 도는 점
      --> 요청이 오기 전에 설정 실수를 드러낸다
      --> 다만 securityMatcher("/**") 처럼 넓지만 AnyRequestMatcher 가
          아닌 매처는 걸러내지 못한다
```

체인 선택이 실제로 어떻게 도는지는 [필터 체인](../../../filter-chain/01_FilterChainProxy.doFilter/01_FilterChainProxy.doFilterInternal/01_FilterChainProxy.getFilters/README.md)에 있다.
