# HttpSecurity.performBuild

상위: [설정 DSL](../README.md)

모인 필터를 정렬해 `SecurityFilterChain` 하나로 만든다. 설정 DSL 의 마지막 단계다.

## 위치

`config` / `org.springframework.security.config.annotation.web.builders` / `HttpSecurity.java` L1793-L1802 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/web/builders/HttpSecurity.java#L1793-L1802))

## 실제 코드

```java
// HttpSecurity.java L1793-L1802
@SuppressWarnings("unchecked")
@Override
protected DefaultSecurityFilterChain performBuild() {
    this.filters.sort(OrderComparator.INSTANCE);
    List<Filter> sortedFilters = new ArrayList<>(this.filters.size());
    for (Filter filter : this.filters) {
        sortedFilters.add(((OrderedFilter) filter).filter);
    }
    return new DefaultSecurityFilterChain(this.requestMatcher, sortedFilters);
}
```

필터가 목록에 들어가는 자리는 `addFilter` 다.

`config` / `org.springframework.security.config.annotation.web.builders` / `HttpSecurity.java` L1843-L1851 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/web/builders/HttpSecurity.java#L1843-L1851))

```java
// HttpSecurity.java L1843-L1851
public HttpSecurity addFilter(Filter filter) {
    Integer order = this.filterOrders.getOrder(filter.getClass());
    if (order == null) {
        throw new IllegalArgumentException("The Filter class " + filter.getClass().getName()
                + " does not have a registered order and cannot be added without a specified order. Consider using addFilterBefore or addFilterAfter instead.");
    }
    this.filters.add(new OrderedFilter(filter, order));
    return this;
}
```

## 동작 흐름

```text
 performBuild()
 |
 | L1796 filters.sort(OrderComparator.INSTANCE)
 |         OrderedFilter 가 Ordered 를 구현하므로 순번으로 정렬된다
 |
 | L1799 각 OrderedFilter 에서 안에 든 진짜 Filter 를 꺼낸다
 |
 +-- L1801 new DefaultSecurityFilterChain(this.requestMatcher, sortedFilters)

 addFilter(filter)
 |
 | L1844 filterOrders.getOrder(filter.getClass())
 |
 +-- L1845 순번이 없으면
 |      L1846 IllegalArgumentException
 |             addFilterBefore / addFilterAfter 를 쓰라고 안내한다
 |
 +-- L1849 OrderedFilter 로 감싸 목록에 넣는다
```

```text
 순번은 클래스가 정한다

 FilterOrderRegistration 이 필터 클래스별 순번표를 들고 있다
 addFilter 는 거기서 순번을 찾는다

 그래서 등록 순서(DSL 호출 순서)는 대체로 결과에 영향을 주지 않는다
 다만 addFilterAt 으로 같은 자리에 여럿을 넣으면
 그들 사이의 순서는 정해지지 않는다고 javadoc 이 밝힌다

 getOrder 는 상위 클래스를 거슬러 올라가며 찾는다 (L150-157)
 그래서 프레임워크 필터를 상속한 사용자 필터는 addFilter 로 들어간다
 아무것도 상속하지 않은 필터만 순번을 못 찾아 예외가 난다
 그때는 addFilterBefore / addFilterAfter 로 상대 위치를 준다
 (그 메서드들이 그 클래스를 순번표에 등록해 준다)
```

```text
 OrderedFilter 는 감싸개다

 filter 와 order 를 들고 있고
 doFilter 를 그대로 위임한다

 정렬이 끝나면 L1798-1800 에서 벗겨 낸다
 그래서 최종 체인에는 원래 필터만 들어간다
 런타임에는 이 감싸개가 남지 않는다
```

```text
 requestMatcher 가 체인의 조건이다

 아무것도 지정하지 않으면 모든 요청에 맞는 매처가 들어간다
 securityMatcher(...) 를 쓰면 그것이 대신 들어간다

 이 매처가 나중에 FilterChainProxy 의 체인 선택 기준이 된다
```

## 결과가 쓰이는 곳

```text
 DefaultSecurityFilterChain
      --> 매처 하나 + 정렬된 필터 목록
      --> SecurityFilterChain 인터페이스의 유일한 프레임워크 구현이다

 정렬된 필터 목록
      --> 이 순서가 곧 런타임의 보안 처리 순서다
      --> 컨텍스트 복원 -> 헤더/CORS/CSRF -> 인증 -> 예외 변환 -> 인가 순이다

 addFilter 의 예외
      --> 프레임워크 필터를 상속하지도 않고 순번표에도 없는
          필터를 addFilter 로 넣으려 할 때 나온다
      --> 순번을 모르는 필터를 임의 위치에 두지 못하게 막는다
```

이 체인이 어떻게 선택되고 실행되는지는 [필터 체인](../../filter-chain/README.md)에 있다.
