# AbstractAuthenticationProcessingFilter.successfulAuthentication

상위: [AbstractAuthenticationProcessingFilter.doFilter](../README.md)

인증 결과를 컨텍스트에 심고 저장소에 저장한다. [보안 컨텍스트](../../../security-context/README.md) 흐름에서 "저장은 인증한 쪽이 직접 한다"고 한 그 자리다.

## 위치

`web` / `org.springframework.security.web.authentication` / `AbstractAuthenticationProcessingFilter.java` L393-L407 ([GitHub](https://github.com/spring-projects/spring-security/blob/26b6b2a84fa8fa26991ca0f57282720b48db9f91/web/src/main/java/org/springframework/security/web/authentication/AbstractAuthenticationProcessingFilter.java#L393-L407))

## 실제 코드

```java
// AbstractAuthenticationProcessingFilter.java L393-L407
protected void successfulAuthentication(HttpServletRequest request, HttpServletResponse response, FilterChain chain,
        Authentication authResult) throws IOException, ServletException {
    SecurityContext context = this.securityContextHolderStrategy.createEmptyContext();
    context.setAuthentication(authResult);
    this.securityContextHolderStrategy.setContext(context);
    this.securityContextRepository.saveContext(context, request, response);
    if (this.logger.isDebugEnabled()) {
        this.logger.debug(LogMessage.format("Set SecurityContextHolder to %s", authResult));
    }
    this.rememberMeServices.loginSuccess(request, response, authResult);
    if (this.eventPublisher != null) {
        this.eventPublisher.publishEvent(new InteractiveAuthenticationSuccessEvent(authResult, this.getClass()));
    }
    this.successHandler.onAuthenticationSuccess(request, response, authResult);
}
```

## 동작 흐름

```text
 successfulAuthentication(request, response, chain, authResult)
 |
 | L395 securityContextHolderStrategy.createEmptyContext()
 |        기존 컨텍스트를 고치지 않고 새로 만든다
 | L396 context.setAuthentication(authResult)
 | L397 securityContextHolderStrategy.setContext(context)
 |        ThreadLocal 에 얹는다. 이 요청의 나머지가 이것을 본다
 |
 | L398 securityContextRepository.saveContext(context, request, response)
 |        저장소에 저장한다. 다음 요청에 복원될 근거다
 |
 | L402 rememberMeServices.loginSuccess(request, response, authResult)
 |        기억하기를 켰으면 여기서 토큰을 발급한다
 |
 | L403 eventPublisher 가 있으면
 |        L404 InteractiveAuthenticationSuccessEvent 를 발행한다
 |
 +-- L406 successHandler.onAuthenticationSuccess(request, response, authResult)
          리다이렉트나 응답 본문을 쓴다
```

```text
 빈 컨텍스트를 새로 만든다

 L395 createEmptyContext() 로 새 인스턴스를 만들어 쓴다
 이미 ThreadLocal 에 있던 컨텍스트를 꺼내 고치지 않는다

 레퍼런스 문서가 이유를 밝힌다 --
 getContext().setAuthentication(...) 대신 새 인스턴스를 만들라고 하며,
 여러 스레드 사이의 경쟁 조건을 피하기 위해서라고 적고 있다
 (servlet/authentication/architecture.adoc)
```

```text
 setContext 와 saveContext 는 다른 일이다

 setContext   ThreadLocal 에 얹는다. 이 요청 안에서만 유효하다
 saveContext  저장소에 쓴다. 다음 요청에 복원된다

 둘 다 해야 로그인이 "유지"된다
 직접 인증을 만들어 심는 코드가 saveContext 를 빠뜨리면
 그 요청은 통과하지만 다음 요청에서 다시 로그인 화면으로 간다
```

## 결과가 쓰이는 곳

```text
 ThreadLocal 에 얹힌 컨텍스트
      --> 이 요청의 남은 필터와 컨트롤러가 본다
      --> 필터 체인이 끝나면 SecurityContextHolderFilter 가 지운다

 저장소에 저장된 컨텍스트
      --> 기본 설정에서는 세션과 요청 속성 양쪽에 쓴다
      --> 다음 요청의 SecurityContextHolderFilter 가 이것을 읽는다

 InteractiveAuthenticationSuccessEvent
      --> "사람이 직접 로그인했다"는 뜻의 이벤트다
      --> 마지막 로그인 시각 기록이나 감사 로그가 듣는다

 successHandler
      --> 폼 로그인 기본은 원래 가려던 곳으로 리다이렉트다
      --> REST API 라면 여기를 바꿔 JSON 이나 토큰을 응답한다
```
