# FilterChainProxy.doFilterInternal

상위: [FilterChainProxy.doFilter](../README.md)

요청을 방화벽으로 감싸고, 이 요청에 맞는 체인을 골라 태운다. 맞는 체인이 없으면 보안 없이 흘려보낸다.

## 위치

`web` / `org.springframework.security.web` / `FilterChainProxy.java` L213-L238 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/FilterChainProxy.java#L213-L238))

## 실제 코드

```java
// FilterChainProxy.java L213-L238
private void doFilterInternal(ServletRequest request, ServletResponse response, FilterChain chain)
        throws IOException, ServletException {
    FirewalledRequest firewallRequest = this.firewall.getFirewalledRequest((HttpServletRequest) request);
    HttpServletResponse firewallResponse = this.firewall.getFirewalledResponse((HttpServletResponse) response);
    List<Filter> filters = getFilters(firewallRequest);
    if (filters == null || filters.isEmpty()) {
        if (logger.isTraceEnabled()) {
            logger.trace(LogMessage.of(() -> "No security for " + requestLine(firewallRequest)));
        }
        firewallRequest.reset();
        this.filterChainDecorator.decorate(chain).doFilter(firewallRequest, firewallResponse);
        return;
    }
    if (logger.isDebugEnabled()) {
        logger.debug(LogMessage.of(() -> "Securing " + requestLine(firewallRequest)));
    }
    FilterChain reset = (req, res) -> {
        if (logger.isDebugEnabled()) {
            logger.debug(LogMessage.of(() -> "Secured " + requestLine(firewallRequest)));
        }
        // Deactivate path stripping as we exit the security filter chain
        firewallRequest.reset();
        chain.doFilter(req, res);
    };
    this.filterChainDecorator.decorate(reset, filters).doFilter(firewallRequest, firewallResponse);
}
```

## 동작 흐름

```text
 doFilterInternal(request, response, chain)
 |
 | L215 firewall.getFirewalledRequest(request)    FirewalledRequest 로 감싼다
 | L216 firewall.getFirewalledResponse(response)  응답도 감싼다
 |
 | L217 getFilters(firewallRequest)   체인 선택
 |
 +-- L218 필터가 없거나 빈 목록이면
 |        L222 firewallRequest.reset()   구현이 건 가공을 해제하는 훅
 |               기본 StrictHttpFirewall 에서는 빈 메서드다
 |        L223 filterChainDecorator.decorate(chain).doFilter(...)
 |               기본 데코레이터는 원래 체인을 그대로 돌려준다
 |               = 보안 필터 0개로 통과
 |        L224 return
 |
 +-- L229 필터가 있으면
        L229 reset 람다를 만든다
               이 람다가 체인의 끝 역할을 한다
               L234 firewallRequest.reset()
               L235 chain.doFilter(req, res)   원래 컨테이너 체인으로
        |
        L237 filterChainDecorator.decorate(reset, filters).doFilter(...)
               VirtualFilterChain 이 만들어져 필터들을 태운다
```

```text
 감싼 요청이 하는 일

 StrictHttpFirewall 이 기본 HttpFirewall 이다
 이름대로 고치지 않고 거부한다

 요청 경로  /admin/../user/me
   L520-522 isNormalized 가 false --> RequestRejectedException
   정규화해서 필터에 넘기는 것이 아니라 요청 자체가 거부된다

 감싼 요청(StrictFirewalledRequest)이 오버라이드하는 것은
   getHeader, getHeaderNames, getDateHeader, getIntHeader, getParameter 계열
 경로 메서드(getRequestURI, getServletPath, getPathInfo)는 손대지 않는다

 경로를 잘라 정규화하는 쪽은 DefaultHttpFirewall 이 쓰는 RequestWrapper 다
 그쪽이 stripPaths 를 켜고, reset() 이 그 가공을 되돌린다
```

```text
 필터가 없다 = 안전하다가 아니다

 어느 SecurityFilterChain 도 matches 하지 않으면 필터 목록은 null 이다
 그러면 이 요청은 인증도 인가도 거치지 않고 통과한다

 permitAll 과는 다르다
   permitAll  체인을 타고 AuthorizationFilter 까지 가서 허용 판정을 받는다
   매칭 없음   체인 자체를 타지 않는다. SecurityContext 도 안 세운다

 설정에서 모든 경로를 덮는 체인을 하나 두는 이유가 이것이다
```

## 결과가 쓰이는 곳

```text
 FirewalledRequest
      --> 체인 안의 모든 필터가 이 감싼 요청을 본다
      --> 기본 구현은 헤더와 파라미터 접근 시점에도 검사를 건다
          그래서 거부가 체인 실행 중에 터질 수도 있다

 reset 람다
      --> 체인의 마지막 필터가 chain.doFilter 를 부르면 여기에 닿는다
      --> reset() 을 부른 뒤 컨테이너 체인으로 넘긴다
      --> 즉 이 람다에 닿았다는 것은 보안 검사를 전부 통과했다는 뜻이다

 FilterChainDecorator
      --> 체인을 감쌀 마지막 기회다
      --> 관측(Observation) 기능이 이 자리에 끼어든다
```

## 하위 메서드

- [01 FilterChainProxy.getFilters](01_FilterChainProxy.getFilters/README.md)
