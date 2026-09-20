# WebSecurity.performBuild

상위: [필터 등록](../README.md)

체인 목록을 완성하고 `FilterChainProxy` 를 만든다. 빌더가 빌더를 부르는 자리다.

## 위치

`config` / `org.springframework.security.config.annotation.web.builders` / `WebSecurity.java` L304-L370 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/config/src/main/java/org/springframework/security/config/annotation/web/builders/WebSecurity.java#L304-L370))

## 실제 코드

```java
// WebSecurity.java L304-L370
@Override
protected Filter performBuild() {
    Assert.state(!this.securityFilterChainBuilders.isEmpty(),
            () -> "At least one SecurityBuilder<? extends SecurityFilterChain> needs to be specified. "
                    + "Typically this is done by exposing a SecurityFilterChain bean. "
                    + "More advanced users can invoke " + WebSecurity.class.getSimpleName()
                    + ".addSecurityFilterChainBuilder directly");
    int chainSize = this.ignoredRequests.size() + this.securityFilterChainBuilders.size();
    List<SecurityFilterChain> securityFilterChains = new ArrayList<>(chainSize);
    RequestMatcherDelegatingAuthorizationManager.Builder builder = RequestMatcherDelegatingAuthorizationManager
        .builder();
    boolean mappings = false;
    for (RequestMatcher ignoredRequest : this.ignoredRequests) {
        WebSecurity.this.logger.warn("You are asking Spring Security to ignore " + ignoredRequest
                + ". This is not recommended -- please use permitAll via HttpSecurity#authorizeHttpRequests instead.");
        SecurityFilterChain securityFilterChain = new DefaultSecurityFilterChain(ignoredRequest);
        securityFilterChains.add(securityFilterChain);
        builder.add(ignoredRequest, SingleResultAuthorizationManager.permitAll());
        mappings = true;
    }
    for (SecurityBuilder<? extends SecurityFilterChain> securityFilterChainBuilder : this.securityFilterChainBuilders) {
        SecurityFilterChain securityFilterChain = securityFilterChainBuilder.build();
        securityFilterChains.add(securityFilterChain);
        mappings = addAuthorizationManager(securityFilterChain, builder) || mappings;
    }
    if (this.privilegeEvaluator == null) {
        AuthorizationManager<HttpServletRequest> authorizationManager = mappings ? builder.build()
                : SingleResultAuthorizationManager.permitAll();
        AuthorizationManagerWebInvocationPrivilegeEvaluator privilegeEvaluator = new AuthorizationManagerWebInvocationPrivilegeEvaluator(
                authorizationManager);
        privilegeEvaluator.setServletContext(this.servletContext);
        if (this.privilegeEvaluatorRequestTransformer != null) {
            privilegeEvaluator.setRequestTransformer(this.privilegeEvaluatorRequestTransformer);
        }
        this.privilegeEvaluator = new RequestMatcherDelegatingWebInvocationPrivilegeEvaluator(
                List.of(new RequestMatcherEntry<>(AnyRequestMatcher.INSTANCE, List.of(privilegeEvaluator))));
    }
    FilterChainProxy filterChainProxy = new FilterChainProxy(securityFilterChains);
    if (this.httpFirewall != null) {
        filterChainProxy.setFirewall(this.httpFirewall);
    }
    if (this.requestRejectedHandler != null) {
        filterChainProxy.setRequestRejectedHandler(this.requestRejectedHandler);
    }
    else if (!this.observationRegistry.isNoop()) {
        CompositeRequestRejectedHandler requestRejectedHandler = new CompositeRequestRejectedHandler(
                new ObservationMarkingRequestRejectedHandler(this.observationRegistry),
                new HttpStatusRequestRejectedHandler());
        filterChainProxy.setRequestRejectedHandler(requestRejectedHandler);
    }
    filterChainProxy.setFilterChainValidator(new WebSecurityFilterChainValidator());
    filterChainProxy.setFilterChainDecorator(getFilterChainDecorator());
    filterChainProxy.afterPropertiesSet();

    Filter result = filterChainProxy;
    if (this.debugEnabled) {
        this.logger.warn("\n\n" + "********************************************************************\n"
                + "**********        Security debugging is enabled.       *************\n"
                + "**********    This may include sensitive information.  *************\n"
                + "**********      Do not use in a production system!     *************\n"
                + "********************************************************************\n\n");
        result = new DebugFilter(filterChainProxy);
    }

    this.postBuildAction.run();
    return result;
}
```

## 동작 흐름

```text
 performBuild()
 |
 +-- L306 빌더가 하나도 없으면 상태 예외
 |        "SecurityFilterChain 빈을 노출하라"고 안내한다
 |
 +-- L316 ignoredRequests 마다
 |      L317 권장하지 않는다는 경고 로그를 남기고
 |      L319 필터 0개짜리 DefaultSecurityFilterChain 을 만든다
 |      L321 인가 매니저에는 permitAll 을 등록한다
 |
 +-- L324 각 빌더마다
 |      L325 securityFilterChainBuilder.build()   HttpSecurity.build() 가 여기서
 |      L326 결과를 목록에 담고
 |      L327 그 체인의 인가 규칙을 매니저 빌더에 모은다
 |
 +-- L329 privilegeEvaluator 가 없으면 만들어 둔다 (L330-339)
 |
 | L341 new FilterChainProxy(securityFilterChains)
 | L342 httpFirewall 을 줬으면 설정
 | L345 requestRejectedHandler 를 줬으면 설정
 | L348 아니고 관측이 켜져 있으면 합성 핸들러를 설정
 | L354 WebSecurityFilterChainValidator 를 설정
 | L355 FilterChainDecorator 를 설정
 | L356 afterPropertiesSet()   여기서 검증기가 돈다
 |
 +-- L359 debugEnabled 면 L365 DebugFilter 로 감싼다
 | L368 postBuildAction 실행
 +-- L369 반환
```

```text
 ignoring 은 우회가 아니라 빈 체인이다

 L319 new DefaultSecurityFilterChain(ignoredRequest)
 필터를 하나도 주지 않는다

 그래서 그 경로는 체인 선택에는 걸리지만 검사는 하나도 없다
 FilterChainProxy 쪽에서 보면 "필터 목록이 빈 경우"다

 L317-318 이 경고 로그로 permitAll 을 권한다
 permitAll 은 체인을 타고 인가 판정까지 가지만
 ignoring 은 SecurityContext 조차 세우지 않기 때문이다
```

```text
 검증이 여기서 돈다

 L354 에서 WebSecurityFilterChainValidator 를 꽂고
 L356 afterPropertiesSet() 이 그것을 실행한다

 매처 없는 체인 뒤에 다른 체인이 오면 여기서 기동이 실패한다
 요청이 오기 전에 잡아 준다
```

```text
 순서에 민감한 자리

 L341 에서 프록시를 만든 뒤 L342-355 로 설정을 붙이고
 L356 에서야 afterPropertiesSet 을 부른다

 검증기를 붙이기 전에 검증을 돌리면 아무것도 검사하지 않게 된다
```

## 결과가 쓰이는 곳

```text
 FilterChainProxy
      --> 필터 체인 흐름의 시작점이다
      --> 체인 목록, 방화벽, 거부 핸들러, 데코레이터를 모두 들고 있다

 모은 인가 매니저
      --> WebInvocationPrivilegeEvaluator 를 만드는 데 쓴다
      --> 뷰에서 "이 링크를 보여줄까"를 물을 때 쓰이는 경로다

 DebugFilter
      --> 보통 @EnableWebSecurity(debug = true) 로 켠다
      --> WebSecurity.debug(true) 도 public 이라 커스터마이저에서도 켤 수 있다
      --> 경고 로그가 운영에서 쓰지 말라고 못박는다

 postBuildAction
      --> 빌드가 끝난 뒤 실행할 일을 예약하는 자리다
```
