# ApplicationListenerMethodAdapter.processEvent

상위: [Spring 이벤트 발행](../README.md)

`@EventListener` 메서드 하나를 감싼 리스너다. 이벤트가 오면 메서드 인자를 만들고, `condition` 식을 평가하고, 메서드를 호출한다. 반환값이 있으면 그것을 다시 이벤트로 발행한다.

## 실제 코드

`spring-context` / `org.springframework.context.event` / `ApplicationListenerMethodAdapter.java` L197-L202 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/ApplicationListenerMethodAdapter.java#L197-L202))

```java
// ApplicationListenerMethodAdapter.java L197-L202
@Override
public void onApplicationEvent(ApplicationEvent event) {
    if (this.defaultExecution) {
        processEvent(event);
    }
}
```

`spring-context` / `org.springframework.context.event` / `ApplicationListenerMethodAdapter.java` L267-L278 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/ApplicationListenerMethodAdapter.java#L267-L278))

```java
// ApplicationListenerMethodAdapter.java L267-L278
public void processEvent(ApplicationEvent event) {
    @Nullable Object[] args = resolveArguments(event);
    if (shouldHandle(event, args)) {
        Object result = doInvoke(args);
        if (result != null) {
            handleResult(result);
        }
        else {
            logger.trace("No result object given - no result to handle");
        }
    }
}
```

`spring-context` / `org.springframework.context.event` / `ApplicationListenerMethodAdapter.java` L290-L301 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/ApplicationListenerMethodAdapter.java#L290-L301))

```java
// ApplicationListenerMethodAdapter.java L290-L301
@Contract("_, null -> false")
private boolean shouldHandle(ApplicationEvent event, @Nullable Object @Nullable [] args) {
    if (args == null) {
        return false;
    }
    if (StringUtils.hasText(this.condition)) {
        Assert.notNull(this.evaluator, "EventExpressionEvaluator must not be null");
        return this.evaluator.condition(
                this.condition, event, this.targetMethod, this.methodKey, args);
    }
    return true;
}
```

타입 판정은 선언된 이벤트 타입과 비교한다.

`spring-context` / `org.springframework.context.event` / `ApplicationListenerMethodAdapter.java` L204-L224 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/ApplicationListenerMethodAdapter.java#L204-L224))

```java
// ApplicationListenerMethodAdapter.java L204-L224
@Override
public boolean supportsEventType(ResolvableType eventType) {
    for (ResolvableType declaredEventType : this.declaredEventTypes) {
        if (eventType.hasUnresolvableGenerics() ?
                declaredEventType.toClass().isAssignableFrom(eventType.toClass()) :
                declaredEventType.isAssignableFrom(eventType)) {
            return true;
        }
        if (PayloadApplicationEvent.class.isAssignableFrom(eventType.toClass())) {
            ResolvableType payloadType = eventType.as(PayloadApplicationEvent.class).getGeneric();
            if (declaredEventType.isAssignableFrom(payloadType)) {
                return true;
            }
            if (payloadType.resolve() == null) {
                // Always accept such event when the type is erased
                return true;
            }
        }
    }
    return false;
}
```

## 동작 흐름

```text
 onApplicationEvent(event)
 |
 | L199 defaultExecution 이 true 일 때만 바로 processEvent      (기본값)
 |        @TransactionalEventListener 는 이 속성을 false 로 덮어쓴다
 |        --> 발행 즉시가 아니라, 트랜잭션 동기화 콜백(커밋 등)에서 processEvent 가 불린다
 |        --> 트랜잭션이 없으면 fallbackExecution=true 가 아닌 한 실행되지 않는다
 |
 +-- processEvent(event)
       |
       | L268 resolveArguments(event)
       |        메서드가 이벤트 타입을 받으면 이벤트 객체
       |        PayloadApplicationEvent 면 페이로드를 꺼내 전달
       |        파라미터가 없으면 빈 배열
       |        타입이 맞지 않으면 null --> 호출하지 않음
       |
       | L269 shouldHandle(event, args)
       |        condition 이 있으면 EventExpressionEvaluator 로 SpEL 평가
       |          #root.event, #root.args, 파라미터 이름 등을 쓸 수 있다
       |        false 면 호출하지 않음
       |
       | L270 doInvoke(args)     리플렉션으로 실제 메서드 호출
       |
       +-- L271 반환값이 있으면 handleResult
              배열 / 컬렉션  --> 각 원소를 publishEvent
              CompletionStage / 리액티브 --> 완료 시 발행
              그 밖         --> 그대로 publishEvent
```

supportsEventType의 판정 규칙이다.

```text
 선언 타입과 이벤트 타입 비교                      L206-L210
   제네릭을 풀 수 없는 이벤트면 raw 타입으로 비교
 PayloadApplicationEvent 인 경우                  L212-L220
   페이로드 제네릭 타입과 선언 타입 비교
   페이로드 타입이 지워졌으면 일단 받아들인다
```

## 결과가 쓰이는 곳

```text
 어댑터 자체
      --> EventListenerMethodProcessor 가 만들어 context.addApplicationListener 로 등록
      --> 멀티캐스터의 리스너 목록에 다른 리스너와 나란히 들어간다

 반환값 발행 (연쇄 이벤트)
      --> 리스너가 이벤트를 반환하면 그것이 다시 발행된다
      --> 같은 스레드에서 이어지므로 순환 발행에 주의해야 한다

 condition 평가
      --> 메서드 호출 자체를 막는다 (인자 해석은 이미 끝난 뒤)
      --> 조건이 자주 false 라면 발행 측에서 거르는 편이 싸다
```
