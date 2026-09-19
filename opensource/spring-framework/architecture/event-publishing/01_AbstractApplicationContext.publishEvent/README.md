# AbstractApplicationContext.publishEvent

상위: [Spring 이벤트 발행](../README.md)

발행 요청을 받아 이벤트를 정규화하고 전달 대상을 정한다. 임의 객체는 `PayloadApplicationEvent`로 감싸고, 기동 중이라 멀티캐스터가 없으면 버퍼에 모아 둔다. 부모 컨텍스트에도 같은 이벤트를 올려보낸다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L415-L461 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L415-L461))

```java
// AbstractApplicationContext.java L415-L461
protected void publishEvent(Object event, @Nullable ResolvableType typeHint) {
    Assert.notNull(event, "Event must not be null");
    ResolvableType eventType = null;

    // Decorate event as an ApplicationEvent if necessary
    ApplicationEvent applicationEvent;
    if (event instanceof ApplicationEvent applEvent) {
        applicationEvent = applEvent;
        eventType = typeHint;
    }
    else {
        ResolvableType payloadType = null;
        if (typeHint != null && ApplicationEvent.class.isAssignableFrom(typeHint.toClass())) {
            eventType = typeHint;
        }
        else {
            payloadType = typeHint;
        }
        applicationEvent = new PayloadApplicationEvent<>(this, event, payloadType);
    }

    // Determine event type only once (for multicast and parent publish)
    if (eventType == null) {
        eventType = ResolvableType.forInstance(applicationEvent);
        if (typeHint == null) {
            typeHint = eventType;
        }
    }

    // Multicast right now if possible - or lazily once the multicaster is initialized
    if (this.earlyApplicationEvents != null) {
        this.earlyApplicationEvents.add(applicationEvent);
    }
    else if (this.applicationEventMulticaster != null) {
        this.applicationEventMulticaster.multicastEvent(applicationEvent, eventType);
    }

    // Publish event via parent context as well...
    if (this.parent != null) {
        if (this.parent instanceof AbstractApplicationContext abstractApplicationContext) {
            abstractApplicationContext.publishEvent(event, typeHint);
        }
        else {
            this.parent.publishEvent(event);
        }
    }
}
```

## 동작 흐름

```text
 publishEvent(event, typeHint)
 |
 | [1] 이벤트 정규화                                       L421-L434
 |       ApplicationEvent 면 그대로
 |       임의 객체면 PayloadApplicationEvent<T> 로 감싼다
 |         --> 타입 힌트가 ApplicationEvent 타입이면 이벤트 타입으로 쓰고,
 |             그 밖이면 페이로드 제네릭 타입으로 쓴다 (L427-L431)
 |
 | [2] L437 이벤트 타입 확정 (ResolvableType)
 |       리스너 선별에서 제네릭까지 비교하기 위한 값
 |
 +-- [3] L445 earlyApplicationEvents 가 아직 살아 있음 (기동 중)
 |       --> 버퍼에 적재하고 멀티캐스트만 건너뛴다 (부모 전파는 이어진다)
 |           registerListeners 가 리스너를 붙인 뒤 한꺼번에 발행한다
 |
 +-- [4] L448 멀티캐스터가 있음
 |       --> multicastEvent(applicationEvent, eventType)
 |
 +-- [5] L453 부모 컨텍스트가 있으면 부모에도 발행
         부모가 AbstractApplicationContext 면 타입 힌트를 유지해 전달
```

1. 실제 전달은 [SimpleApplicationEventMulticaster.multicastEvent](../02_SimpleApplicationEventMulticaster.multicastEvent/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 PayloadApplicationEvent 로 감싼 결과
      --> @EventListener 메서드가 OrderCreated 같은 도메인 객체를 직접 받을 수 있는 이유
      --> 리스너 선별에서 페이로드의 제네릭 타입까지 비교된다

 [3] 의 버퍼
      --> prepareRefresh 가 만들고 registerListeners 가 비운다
      --> 기동 중 발행된 이벤트가 유실되지 않는 장치

 [5] 의 부모 전파
      --> 자식(웹) 컨텍스트의 이벤트를 부모(루트)의 리스너도 받는다
      --> 반대 방향(부모 -> 자식)은 전파되지 않는다
```

`publishEvent`는 리스너가 모두 끝난 뒤 반환된다. 발행은 기본적으로 동기이고, 호출자의 트랜잭션과 스레드를 그대로 쓴다.
