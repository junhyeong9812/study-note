# FilterChainProxy.getFilters

상위: [FilterChainProxy.doFilterInternal](../README.md)

등록된 체인을 순서대로 훑어 **처음 맞는 하나**의 필터 목록을 돌려준다. Spring Security 설정에서 순서가 중요한 이유가 이 메서드에 다 들어 있다.

## 위치

`web` / `org.springframework.security.web` / `FilterChainProxy.java` L245-L257 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/FilterChainProxy.java#L245-L257))

## 실제 코드

```java
// FilterChainProxy.java L245-L257
private @Nullable List<Filter> getFilters(HttpServletRequest request) {
    int count = 0;
    for (SecurityFilterChain chain : this.filterChains) {
        if (logger.isTraceEnabled()) {
            logger.trace(LogMessage.format("Trying to match request against %s (%d/%d)", chain, ++count,
                    this.filterChains.size()));
        }
        if (chain.matches(request)) {
            return chain.getFilters();
        }
    }
    return null;
}
```

## 동작 흐름

```text
 getFilters(request)
 |
 +-- L247 for (SecurityFilterChain chain : this.filterChains)
 |        L252 chain.matches(request)
 |        |
 |        +-- true  --> L253 chain.getFilters() 를 반환하고 즉시 끝
 |        +-- false --> 다음 체인으로
 |
 +-- L256 하나도 안 맞으면 null
```

루프 안의 L248-251 은 전부 trace 로그다. 판정에 관여하지 않는다.

```text
 첫 매칭에서 멈춘다

 @Bean SecurityFilterChain apiChain   securityMatcher("/api/**")
 @Bean SecurityFilterChain appChain   (매처 없음 = 모든 요청)

 등록 순서가 [apiChain, appChain] 이면
   /api/x   --> apiChain
   /home    --> apiChain 불일치 --> appChain

 등록 순서가 [appChain, apiChain] 이면
   기동이 실패한다
   매처 없는 체인 뒤에 다른 체인이 오면
   WebSecurityFilterChainValidator 가 UnreachableFilterChainException 을 던진다

 순서를 정하는 것은 @Order 또는 Ordered 다
 둘 다 없으면 빈 등록 순서가 그대로 남는다
 WebSecurityConfiguration 은 받은 목록을 정렬하지 않는다
```

```text
 matches 는 체인이 스스로 판단한다

 SecurityFilterChain 은 matches 와 getFilters 두 메서드뿐인 인터페이스다
 기본 구현 DefaultSecurityFilterChain 은 RequestMatcher 하나를 들고 있고
 설정에서 securityMatcher 를 주지 않으면 모든 요청에 맞는 매처가 들어간다

 즉 "어느 체인이 걸리는가"는 이 목록의 순서와
 각 체인이 들고 있는 매처, 둘만으로 결정된다
```

## 결과가 쓰이는 곳

```text
 반환한 필터 목록
      --> VirtualFilterChain 의 재료가 된다
      --> 이 목록의 순서가 곧 보안 처리 순서다
          (컨텍스트 복원 -> 인증 -> 예외 변환 -> 인가)

 null 반환
      --> 어느 체인도 매칭되지 않았다는 뜻이다
      --> 호출한 쪽에서 "보안 없이 통과"로 이어진다

 빈 목록 반환
      --> null 과 결과는 같지만 경로가 다르다
      --> WebSecurity.ignoring() 으로 제외한 경로가 여기다
          필터가 0개인 DefaultSecurityFilterChain 이 실제로 만들어져 매칭된다

 순서가 만드는 함정
      --> 넓은 매처를 앞에 둔 체인은 뒤 체인을 가린다
      --> 매처 없는 체인이 앞이면 기동 때 막히지만,
          securityMatcher("/**") 는 통과해 런타임에야 드러난다
```

체인 목록이 어떤 순서로 등록되는지는 [필터 등록](../../../../filter-registration/README.md)에 있다.
