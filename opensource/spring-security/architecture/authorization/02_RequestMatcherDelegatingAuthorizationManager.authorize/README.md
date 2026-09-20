# RequestMatcherDelegatingAuthorizationManager.authorize

상위: [인가](../README.md)

`authorizeHttpRequests` 설정이 그대로 자료구조가 된 것이다. 매처와 매니저 쌍을 순서대로 훑어 처음 맞는 하나에 넘긴다.

## 위치

`web` / `org.springframework.security.web.access.intercept` / `RequestMatcherDelegatingAuthorizationManager.java` L66-L90 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/access/intercept/RequestMatcherDelegatingAuthorizationManager.java#L66-L90))

## 실제 코드

```java
// RequestMatcherDelegatingAuthorizationManager.java L66-L90
@Override
public @Nullable AuthorizationResult authorize(Supplier<? extends @Nullable Authentication> authentication,
        HttpServletRequest request) {
    if (this.logger.isTraceEnabled()) {
        this.logger.trace(LogMessage.format("Authorizing %s", requestLine(request)));
    }
    for (RequestMatcherEntry<AuthorizationManager<? super RequestAuthorizationContext>> mapping : this.mappings) {

        RequestMatcher matcher = mapping.getRequestMatcher();
        MatchResult matchResult = matcher.matcher(request);
        if (matchResult.isMatch()) {
            AuthorizationManager<? super RequestAuthorizationContext> manager = mapping.getEntry();
            if (this.logger.isTraceEnabled()) {
                this.logger.trace(
                        LogMessage.format("Checking authorization on %s using %s", requestLine(request), manager));
            }
            return manager.authorize(authentication,
                    new RequestAuthorizationContext(request, matchResult.getVariables()));
        }
    }
    if (this.logger.isTraceEnabled()) {
        this.logger.trace(LogMessage.of(() -> "Denying request since did not find matching RequestMatcher"));
    }
    return DENY;
}
```

## 동작 흐름

```text
 authorize(authentication, request)
 |
 +-- L72 for (mapping : this.mappings)
 |      |
 |      | L74 mapping.getRequestMatcher()
 |      | L75 matcher.matcher(request)     MatchResult 를 받는다
 |      |
 |      +-- L76 isMatch() 이면
 |             L77 mapping.getEntry()      그 쌍의 매니저
 |             L82 manager.authorize(authentication,
 |             L83     new RequestAuthorizationContext(request, matchResult.getVariables()))
 |             그대로 반환한다 -- 첫 매칭에서 끝난다
 |
 +-- L89 하나도 안 맞으면 DENY
```

L69-71, L78-81, L86-88 은 trace 로그다.

```text
 matches 가 아니라 matcher 를 부른다

 matcher.matcher(request) 는 boolean 이 아니라 MatchResult 를 돌려준다
 거기에 경로 변수가 담겨 있다

 requestMatchers("/user/{id}/**").access(...)
   --> matchResult.getVariables() 에 id 가 들어온다
   --> RequestAuthorizationContext 를 통해 판정식이 그 값을 쓴다

 단순 boolean 이었다면 "본인 것만 수정" 같은 규칙을 쓸 수 없다
```

```text
 하나도 안 맞으면 거부다

 L54 DENY = new AuthorizationDecision(false)
 L89 return DENY

 필터 체인 선택(FilterChainProxy.getFilters)과 반대다
 그쪽은 안 맞으면 보안 없이 통과시킨다
 여기는 안 맞으면 막는다

 생성자가 mappings 가 비어 있는 것도 막는다 (L62)
```

```text
 순서가 전부다

 첫 매칭에서 반환하므로 위에 쓴 규칙이 이긴다

 .requestMatchers("/**").permitAll()
 .requestMatchers("/admin/**").hasRole("ADMIN")   <- 영원히 안 쓰인다

 anyRequest() 를 맨 마지막에 두라는 관례가 여기서 나온다
```

## 결과가 쓰이는 곳

```text
 넘긴 RequestAuthorizationContext
      --> 요청과 경로 변수를 함께 담는다
      --> 표현식 기반 규칙이 이 값을 본다

 반환한 AuthorizationResult
      --> 그대로 필터로 올라간다
      --> 위임받은 매니저가 null 을 돌려주면 그 null 이 그대로 올라가고,
          필터는 그것을 거부로 보지 않는다

 DENY 상수
      --> 인스턴스를 공유한다. 요청마다 만들지 않는다
      --> 거부 이유를 담지 않는 단순한 결과다
```
