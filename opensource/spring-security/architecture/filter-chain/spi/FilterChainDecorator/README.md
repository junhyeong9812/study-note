# FilterChainDecorator

상위: [spi](../README.md)

고른 필터 목록을 서블릿 `FilterChain` 으로 바꾸는 자리다. 체인을 감쌀 마지막 지점이라 관측 기능이 여기에 끼어든다.

## 위치

`web` / `org.springframework.security.web` / `FilterChainProxy.java` L413-L435 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/FilterChainProxy.java#L413-L435))

## 실제 코드

```java
// FilterChainProxy.java L413-L435 (javadoc 생략)
public interface FilterChainDecorator {

    default FilterChain decorate(FilterChain original) {
        return decorate(original, Collections.emptyList());
    }

    FilterChain decorate(FilterChain original, List<Filter> filters);

}
```

## 흐름에서 불리는 자리

```text
 FilterChainProxy.doFilterInternal
   필터가 없으면  decorate(chain)          원래 체인을 그대로
   필터가 있으면  decorate(reset, filters) VirtualFilterChain 생성
```

- [FilterChainProxy.doFilterInternal](../../01_FilterChainProxy.doFilter/01_FilterChainProxy.doFilterInternal/README.md)

## 구현 계층

```text
 FilterChainDecorator
   +-- VirtualFilterChainDecorator   기본. VirtualFilterChain 을 만든다
   +-- ObservationFilterChainDecorator  필터 실행을 계측해 감싼다
   +-- (사용자 구현)

 decorate(FilterChain) 는 default 메서드로
   decorate(original, 빈 목록) 을 부르게 되어 있다
   VirtualFilterChainDecorator 는 이것을 오버라이드해
   original 을 그대로 돌려준다 (감싸지 않는다)
```

## 결과가 쓰이는 곳

```text
 돌려준 FilterChain
      --> 이 위에서 보안 필터 전체가 실행된다
      --> 여기를 감싸면 모든 필터의 실행을 한 곳에서 계측할 수 있다

 @since 6.0
      --> 필터 체인 흐름에서 비교적 늦게 열린 확장점이다
