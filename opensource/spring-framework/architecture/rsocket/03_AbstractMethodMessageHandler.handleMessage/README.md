# AbstractMethodMessageHandler.handleMessage

상위: [Spring RSocket](../README.md)

리액티브 쪽 메서드 라우터다. STOMP가 쓰는 명령형 라우터와 이름이 같지만 다른 클래스이고, 반환이 `Mono<Void>`다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.handler.invocation.reactive` / `AbstractMethodMessageHandler.java` L437-L450 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/handler/invocation/reactive/AbstractMethodMessageHandler.java#L437-L450))

```java
// AbstractMethodMessageHandler.java L437-L450
public Mono<Void> handleMessage(Message<?> message) throws MessagingException {
    Match<T> match = null;
    try {
        match = getHandlerMethod(message);
    }
    catch (Exception ex) {
        return Mono.error(ex);
    }
    if (match == null) {
        // handleNoMatch would have been invoked already
        return Mono.empty();
    }
    return handleMatch(match.mapping, match.handlerMethod, message);
}
```

`spring-messaging` / `org.springframework.messaging.handler.invocation.reactive` / `AbstractMethodMessageHandler.java` L452-L455 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/handler/invocation/reactive/AbstractMethodMessageHandler.java#L452-L455))

```java
// AbstractMethodMessageHandler.java L452-L455
protected Mono<Void> handleMatch(T mapping, HandlerMethod handlerMethod, Message<?> message) {
    handlerMethod = handlerMethod.createWithResolvedBean();
    return this.invocableHelper.handleMessage(handlerMethod, message);
}
```

## 동작 흐름

```text
 handleMessage(message)
 |
 | L440 getHandlerMethod(message)
 |        라우트로 직접 조회(destinationLookup)를 먼저 시도하고
 |        없으면 전체 매핑을 훑는다
 |        프레임 타입 조건도 이때 함께 평가된다
 |
 +-- L443 조회 중 예외 --> Mono.error
 |
 +-- L447 매칭 없음 --> Mono.empty()
 |        handleNoMatch 는 조회 과정에서 이미 불렸다
 |        RSocket 구현의 handleNoMatch 는 SETUP, METADATA_PUSH, fireAndForget 만
 |        무시하거나 경고 로그를 남기고 돌아온다
 |
 +-- L449 handleMatch(mapping, handlerMethod, message)
        L453 빈을 실제 객체로 해소한 뒤
        L454 invocableHelper.handleMessage(...)
              인자 리졸버로 인자를 만들고 메서드를 호출한 뒤
              반환값 처리기로 결과를 넘긴다
```

```text
 STOMP 쪽과 이름이 같은 두 클래스

 handler.invocation.AbstractMethodMessageHandler          명령형, void 반환
   SimpAnnotationMethodMessageHandler 가 상속 (STOMP)
 handler.invocation.reactive.AbstractMethodMessageHandler  리액티브, Mono<Void>
   MessageMappingMessageHandler --> RSocketMessageHandler 가 상속

 라우팅 개념은 같지만 반환과 인자 해석이 리액티브로 바뀐다
```

## 결과가 쓰이는 곳

```text
 반환한 Mono<Void>
      --> handleAndReply 가 이것을 구독한 뒤 responseRef 를 읽는다
      --> 즉 "처리 완료" 신호이고, 응답 자체는 아니다

 매칭 실패
      --> SETUP, METADATA_PUSH, fireAndForget 은 조용히 끝나 Mono.empty() 가 된다
      --> 그 밖의 상호작용은 RSocketMessageHandler 의 handleNoMatch 가
          MessageDeliveryException 을 던지고, 그 예외가 L442-L443 에서 잡혀
          Mono.error 로 클라이언트에 전달된다

 destinationLookup 우선 조회
      --> 패턴 없는 정확한 라우트는 맵 조회 한 번으로 끝난다
      --> 패턴 매칭은 그 다음이다

 핸들러 메서드의 반환값
      --> 반환값 처리기 체인으로 간다
      --> RSocket 에서는 그중 RSocketPayloadReturnValueHandler 가 응답을 만든다
```

응답을 만드는 자리는 [RSocketPayloadReturnValueHandler.handleEncodedContent](../04_RSocketPayloadReturnValueHandler.handleEncodedContent/README.md)다.
