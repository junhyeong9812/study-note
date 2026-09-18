# SimpleApplicationEventMulticaster.multicastEvent

상위: [Spring 이벤트 발행](../README.md)

이벤트를 받을 리스너를 골라 하나씩 호출한다. 실행기(`Executor`)가 설정돼 있으면 리스너를 다른 스레드에서 돌리고, 없으면 발행한 스레드에서 순서대로 돌린다.

## 실제 코드

`spring-context` / `org.springframework.context.event` / `SimpleApplicationEventMulticaster.java` L136-L154 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/SimpleApplicationEventMulticaster.java#L136-L154))

```java
// SimpleApplicationEventMulticaster.java L136-L154
@Override
public void multicastEvent(ApplicationEvent event, @Nullable ResolvableType eventType) {
    ResolvableType type = (eventType != null ? eventType : ResolvableType.forInstance(event));
    Executor executor = getTaskExecutor();
    for (ApplicationListener<?> listener : getApplicationListeners(event, type)) {
        if (executor != null && listener.supportsAsyncExecution()) {
            try {
                executor.execute(() -> invokeListener(listener, event));
            }
            catch (RejectedExecutionException ex) {
                // Probably on shutdown -> invoke listener locally instead
                invokeListener(listener, event);
            }
        }
        else {
            invokeListener(listener, event);
        }
    }
}
```

리스너 하나를 부르는 부분이다.

`spring-context` / `org.springframework.context.event` / `SimpleApplicationEventMulticaster.java` L162-L175 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/SimpleApplicationEventMulticaster.java#L162-L175))

```java
// SimpleApplicationEventMulticaster.java L162-L175
protected void invokeListener(ApplicationListener<?> listener, ApplicationEvent event) {
    ErrorHandler errorHandler = getErrorHandler();
    if (errorHandler != null) {
        try {
            doInvokeListener(listener, event);
        }
        catch (Throwable err) {
            errorHandler.handleError(err);
        }
    }
    else {
        doInvokeListener(listener, event);
    }
}
```

`spring-context` / `org.springframework.context.event` / `SimpleApplicationEventMulticaster.java` L178-L202 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/SimpleApplicationEventMulticaster.java#L178-L202))

```java
// SimpleApplicationEventMulticaster.java L178-L202
private void doInvokeListener(ApplicationListener listener, ApplicationEvent event) {
    try {
        listener.onApplicationEvent(event);
    }
    catch (ClassCastException ex) {
        String msg = ex.getMessage();
        if (msg == null || matchesClassCastMessage(msg, event.getClass()) ||
                (event instanceof PayloadApplicationEvent payloadEvent &&
                        matchesClassCastMessage(msg, payloadEvent.getPayload().getClass()))) {
            // Possibly a lambda-defined listener which we could not resolve the generic event type for
            // -> let's suppress the exception.
            Log loggerToUse = this.lazyLogger;
            if (loggerToUse == null) {
                loggerToUse = LogFactory.getLog(getClass());
                this.lazyLogger = loggerToUse;
            }
            if (loggerToUse.isTraceEnabled()) {
                loggerToUse.trace("Non-matching event type for listener: " + listener, ex);
            }
        }
        else {
            throw ex;
        }
    }
}
```

## 동작 흐름

```text
 multicastEvent(event, eventType)
 |
 | L138 타입이 주어지지 않았으면 인스턴스에서 추론
 | L139 executor = getTaskExecutor()      기본은 null (동기 실행)
 |
 +-- L140 for listener in getApplicationListeners(event, type)
       |
       +-- executor 있음 + listener.supportsAsyncExecution()
       |     --> executor.execute(() -> invokeListener(...))
       |         거부되면(종료 중) 그냥 현재 스레드에서 실행
       |
       +-- 그 밖 --> invokeListener(listener, event)
              |
              | L163 errorHandler 가 있으면 try/catch 로 감싸 넘긴다
              |        --> 한 리스너가 실패해도 다음 리스너가 계속 실행된다
              |      없으면 예외가 발행자에게 그대로 전파된다 (기본)
              |
              +-- L180 listener.onApplicationEvent(event)
                     L182 ClassCastException 은 조건부로 삼킨다
                          람다 리스너의 제네릭 타입을 못 풀어 잘못 매칭된 경우
```

1. 리스너 선별은 [getApplicationListeners](01_AbstractApplicationEventMulticaster.getApplicationListeners/README.md)가 한다.
2. `@EventListener` 메서드 리스너는 [ApplicationListenerMethodAdapter.processEvent](../03_ApplicationListenerMethodAdapter.processEvent/README.md)로 이어진다.

## 결과가 쓰이는 곳

```text
 동기 실행 (기본)
      --> 리스너 실행 순서 = @Order 정렬 순서
      --> 리스너의 예외가 발행자에게 전파되어 트랜잭션 롤백까지 이어질 수 있다

 비동기 실행 (taskExecutor 설정)
      --> 발행자는 기다리지 않는다
      --> 리스너 예외는 발행자에게 전달되지 않는다 --> errorHandler 설정이 사실상 필수
      --> supportsAsyncExecution() 이 false 인 리스너는 비동기 대상에서 빠진다
          (@TransactionalEventListener 처럼 문맥에 묶인 리스너)

 errorHandler
      --> 설정하면 "한 리스너 실패가 다른 리스너를 막지 않는" 동작이 된다
```

## 하위 메서드

- [01 AbstractApplicationEventMulticaster.getApplicationListeners](01_AbstractApplicationEventMulticaster.getApplicationListeners/README.md)
