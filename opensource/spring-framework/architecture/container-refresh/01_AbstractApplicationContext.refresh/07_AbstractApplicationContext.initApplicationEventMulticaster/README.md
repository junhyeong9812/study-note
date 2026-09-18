# AbstractApplicationContext.initApplicationEventMulticaster

상위: [AbstractApplicationContext.refresh](../README.md)

이벤트를 리스너들에게 나눠 주는 `ApplicationEventMulticaster`를 정한다. `applicationEventMulticaster`라는 이름의 빈이 있으면 그것을, 없으면 `SimpleApplicationEventMulticaster`를 쓴다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L854-L871 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L854-L871))

```java
// AbstractApplicationContext.java L854-L871
protected void initApplicationEventMulticaster() {
    ConfigurableListableBeanFactory beanFactory = getBeanFactory();
    if (beanFactory.containsLocalBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME)) {
        this.applicationEventMulticaster =
                beanFactory.getBean(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, ApplicationEventMulticaster.class);
        if (logger.isTraceEnabled()) {
            logger.trace("Using ApplicationEventMulticaster [" + this.applicationEventMulticaster + "]");
        }
    }
    else {
        this.applicationEventMulticaster = new SimpleApplicationEventMulticaster(beanFactory);
        beanFactory.registerSingleton(APPLICATION_EVENT_MULTICASTER_BEAN_NAME, this.applicationEventMulticaster);
        if (logger.isTraceEnabled()) {
            logger.trace("No '" + APPLICATION_EVENT_MULTICASTER_BEAN_NAME + "' bean, using " +
                    "[" + this.applicationEventMulticaster.getClass().getSimpleName() + "]");
        }
    }
}
```

## 동작 흐름

```text
 initApplicationEventMulticaster()
 |
 +-- "applicationEventMulticaster" 빈 정의가 있음
 |     getBean 으로 그 빈 사용
 |       예: taskExecutor 를 설정한 SimpleApplicationEventMulticaster --> 리스너를 비동기로 호출
 |
 +-- 없음
       new SimpleApplicationEventMulticaster(beanFactory)
         taskExecutor 없음 --> 발행한 스레드에서 리스너를 순서대로 동기 호출
       registerSingleton("applicationEventMulticaster", ...)
```

## 결과가 쓰이는 곳

```text
 this.applicationEventMulticaster
      +-- registerListeners
      |     addApplicationListener(객체)          코드로 추가한 리스너
      |     addApplicationListenerBean(빈 이름)   빈 리스너 (아직 생성 안 함)
      |     multicastEvent(초기 이벤트)
      +-- publishEvent (AAC L449)                 refresh 이후 모든 이벤트
      +-- ApplicationListenerDetector             빈 생성 후 리스너 객체를 추가
      +-- close() 의 doClose (AAC L1219-L1226) 멀티캐스터 참조를 비우고 리스너 목록을 기동 전 상태로 되돌림

 이 단계 이전 (01 ~ 06) 에 발행된 이벤트
      --> 멀티캐스터가 없으므로 prepareRefresh 가 만든 버퍼에 쌓여 있음
```

리스너가 이벤트를 받는 쪽의 자세한 흐름(`@EventListener` 포함)은 [이벤트 발행](../../../event-publishing/README.md) 흐름에서 다룬다.
