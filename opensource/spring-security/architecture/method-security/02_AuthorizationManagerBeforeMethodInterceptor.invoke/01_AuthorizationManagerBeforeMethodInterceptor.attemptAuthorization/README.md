# AuthorizationManagerBeforeMethodInterceptor.attemptAuthorization

상위: [AuthorizationManagerBeforeMethodInterceptor.invoke](../README.md)

판정하고, 거부면 핸들러로 보내고, 허용이면 원래 메서드를 부른다.

## 위치

`core` / `org.springframework.security.authorization.method` / `AuthorizationManagerBeforeMethodInterceptor.java` L248-L267 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/AuthorizationManagerBeforeMethodInterceptor.java#L248-L267))

## 실제 코드

```java
// AuthorizationManagerBeforeMethodInterceptor.java L248-L267
private @Nullable Object attemptAuthorization(MethodInvocation mi) throws Throwable {
    this.logger.debug(LogMessage.of(() -> "Authorizing method invocation " + mi));
    AuthorizationResult result;
    try {
        result = this.authorizationManager.authorize(this::getAuthentication, mi);
    }
    catch (AuthorizationDeniedException denied) {
        return handle(mi, denied);
    }
    if (result != null) {
        this.eventPublisher.publishAuthorizationEvent(this::getAuthentication, mi, result);
    }
    if (result != null && !result.isGranted()) {
        this.logger.debug(LogMessage.of(() -> "Failed to authorize " + mi + " with authorization manager "
                + this.authorizationManager + " and result " + result));
        return handle(mi, result);
    }
    this.logger.debug(LogMessage.of(() -> "Authorized method invocation " + mi));
    return proceed(mi);
}
```

원래 메서드를 부르는 부분도 따로 있다.

`core` / `org.springframework.security.authorization.method` / `AuthorizationManagerBeforeMethodInterceptor.java` L269-L279 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/core/src/main/java/org/springframework/security/authorization/method/AuthorizationManagerBeforeMethodInterceptor.java#L269-L279))

```java
// AuthorizationManagerBeforeMethodInterceptor.java L269-L279
private @Nullable Object proceed(MethodInvocation mi) throws Throwable {
    try {
        return mi.proceed();
    }
    catch (AuthorizationDeniedException ex) {
        if (this.authorizationManager instanceof MethodAuthorizationDeniedHandler handler) {
            return handler.handleDeniedInvocation(mi, ex);
        }
        return this.defaultHandler.handleDeniedInvocation(mi, ex);
    }
}
```

## 동작 흐름

```text
 attemptAuthorization(mi)
 |
 | L252 authorizationManager.authorize(this::getAuthentication, mi)
 |
 +-- L254 그 과정에서 AuthorizationDeniedException 이 나오면
 |        L255 handle(mi, denied) 로 넘기고 끝
 |
 +-- L257 결과가 null 이 아니면
 |        L258 인가 이벤트를 발행한다
 |
 +-- L260 결과가 null 이 아니고 granted 가 아니면
 |        L263 handle(mi, result)
 |
 +-- L266 그 밖에는 proceed(mi)
          L271 mi.proceed()   원래 메서드가 여기서 실행된다
```

```text
 null 은 거부가 아니다

 L260 if (result != null && !result.isGranted())

 웹 쪽 AuthorizationFilter 와 같은 판정이다
 애노테이션이 없어 매니저가 null 을 돌려주면 그냥 통과한다

 이벤트 발행도 null 이면 건너뛴다 (L257)
```

```text
 거부를 예외로만 표현하지 않는다

 웹 인가     AuthorizationDeniedException 을 던지는 것이 전부다
 메서드 보안 handle(...) 이 값을 돌려줄 수 있다

 그래서 @PreAuthorize 가 거부됐을 때
 예외 대신 빈 목록이나 마스킹된 값을 돌려주게 만들 수 있다
 반환 타입이 있는 메서드라서 가능한 선택지다
```

```text
 proceed 에도 방어가 있다 (L269-279)

 원래 메서드 실행 중에 AuthorizationDeniedException 이 나올 수 있다
 안쪽에서 또 다른 보안 검사가 걸리는 경우다

 L273-276 그때 매니저가 MethodAuthorizationDeniedHandler 이면
 그 핸들러에게 처리를 넘긴다
 밖으로 그냥 던지지 않고 같은 규칙으로 다룬다
```

## 결과가 쓰이는 곳

```text
 mi.proceed()
      --> 원래 메서드가 실행되는 유일한 지점이다
      --> 여기 닿지 못하면 메서드는 아예 실행되지 않는다

 handle 의 반환값
      --> 그대로 호출자에게 돌아간다
      --> 기본 핸들러는 예외를 던지지만, 바꿀 수 있다

 발행되는 인가 이벤트
      --> 웹 인가와 같은 AuthorizationEventPublisher 계약이다
      --> 허용과 거부를 모두 발행한다

 Supplier 로 넘기는 Authentication
      --> 웹 쪽과 같은 방식이다
      --> 표현식이 인증을 쓰지 않으면 꺼내지 않는다
```
