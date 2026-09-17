# AbstractApplicationContext.prepareRefresh

상위: [AbstractApplicationContext.refresh](../README.md)

기동 직전의 준비다. 컨텍스트를 활성 상태로 바꾸고, 필수 프로퍼티가 모두 있는지 검증하고, 멀티캐스터가 아직 없는 동안 발행될 이벤트를 모아 둘 버퍼를 만든다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L668-L703 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L668-L703))

```java
// AbstractApplicationContext.java L668-L703
protected void prepareRefresh() {
    // Switch to active.
    this.startupDate = System.currentTimeMillis();
    this.closed.set(false);
    this.active.set(true);

    if (logger.isDebugEnabled()) {
        if (logger.isTraceEnabled()) {
            logger.trace("Refreshing " + this);
        }
        else {
            logger.debug("Refreshing " + getDisplayName());
        }
    }

    // Initialize any placeholder property sources in the context environment.
    initPropertySources();

    // Validate that all properties marked as required are resolvable:
    // see ConfigurablePropertyResolver#setRequiredProperties
    getEnvironment().validateRequiredProperties();

    // Store pre-refresh ApplicationListeners...
    if (this.earlyApplicationListeners == null) {
        this.earlyApplicationListeners = new LinkedHashSet<>(this.applicationListeners);
    }
    else {
        // Reset local application listeners to pre-refresh state.
        this.applicationListeners.clear();
        this.applicationListeners.addAll(this.earlyApplicationListeners);
    }

    // Allow for the collection of early ApplicationEvents,
    // to be published once the multicaster is available...
    this.earlyApplicationEvents = new LinkedHashSet<>();
}
```

## 동작 흐름

```text
 prepareRefresh()
 |
 | L670 startupDate = 현재 시각
 | L671 closed = false
 | L672 active = true                    이 순간부터 getBean 등의 활성 검사를 통과
 |
 | L684 initPropertySources()            빈 훅. 웹 컨텍스트는 ServletContext 기반 프로퍼티 소스로 교체
 |
 | L688 getEnvironment().validateRequiredProperties()
 |        setRequiredProperties("db.url") 로 지정한 키가 없으면
 |        --> MissingRequiredPropertiesException   (기동 실패, 빈 하나 만들기 전)
 |
 +-- L691 earlyApplicationListeners 가 null (첫 refresh)
 |        --> 현재 applicationListeners 를 복사해 보관
 |      그 밖 (재 refresh)
 |        --> applicationListeners 를 보관본으로 되돌림
 |
 +-- L702 earlyApplicationEvents = new LinkedHashSet()   이벤트 버퍼 켜기
```

## 결과가 쓰이는 곳

```text
 active = true
      --> assertBeanFactoryActive() (AAC L1281) 통과 --> 기동 중 getBean 가능

 earlyApplicationEvents (빈 Set)
      --> publishEvent (AAC L445) 가 멀티캐스터 대신 여기에 적재
            기동 중 BeanFactoryPostProcessor / 빈 초기화 코드가 발행한 이벤트
      --> registerListeners 에서 null 로 바꾸고 한꺼번에 발행
          = 리스너가 등록되기 전에 발행된 이벤트도 유실되지 않는다

 earlyApplicationListeners
      --> 같은 컨텍스트를 다시 refresh 할 때 코드로 추가했던 리스너만 남기고
          이전 refresh에서 빈으로 붙은 리스너를 걷어내는 기준
```

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L444-L450 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L444-L450))

```java
// AbstractApplicationContext.java L444-L450
// Multicast right now if possible - or lazily once the multicaster is initialized
if (this.earlyApplicationEvents != null) {
    this.earlyApplicationEvents.add(applicationEvent);
}
else if (this.applicationEventMulticaster != null) {
    this.applicationEventMulticaster.multicastEvent(applicationEvent, eventType);
}
```

[registerListeners](../08_AbstractApplicationContext.registerListeners/README.md)가 이 버퍼를 비운다.
