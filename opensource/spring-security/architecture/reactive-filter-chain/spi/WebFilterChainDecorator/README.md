# WebFilterChainDecorator

상위: [spi](../README.md)

고른 필터들을 실제 `WebFilterChain` 으로 만든다. 서블릿 판의 `FilterChainDecorator` 와 같은 자리다.

## 위치

`web` / `org.springframework.security.web.server` / `WebFilterChainProxy.java` L122-L144 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/server/WebFilterChainProxy.java#L122-L144))

## 실제 코드

```java
// WebFilterChainProxy.java L122-L144 (javadoc 생략)
public interface WebFilterChainDecorator {

    default WebFilterChain decorate(WebFilterChain original) {
        return decorate(original, Collections.emptyList());
    }

    WebFilterChain decorate(WebFilterChain original, List<WebFilter> filters);

}
```

## 흐름에서 불리는 자리

```text
 WebFilterChainProxy.filterFirewalledExchange
   L75 decorate(chain)            매칭되는 체인이 없을 때
   L77 decorate(chain, filters)   있을 때
```

- [WebFilterChainProxy.filterFirewalledExchange](../../01_WebFilterChainProxy.filter/01_WebFilterChainProxy.filterFirewalledExchange/README.md)

## 구현 계층

```text
 WebFilterChainDecorator
   +-- DefaultWebFilterChainDecorator   기본. DefaultWebFilterChain 을 만든다
   +-- (관측용 데코레이터)
   +-- (사용자 구현)

 decorate(WebFilterChain) 는 default 메서드로
 decorate(original, 빈 목록) 을 부르게 되어 있다
 기본 구현은 이것을 오버라이드해 original 을 그대로 돌려준다
```

## 결과가 쓰이는 곳

```text
 돌려준 WebFilterChain
      --> 이 위에서 보안 필터 전체가 실행된다
      --> 여기를 감싸면 모든 필터의 실행을 한 곳에서 계측할 수 있다

 서블릿 판과 같은 구조
      --> 두 갈래(필터 있음/없음)도, default 메서드 모양도 같다
      --> 둘 다 @since 6.0 에 열린 확장점이다
```
