# AbstractApplicationContext.registerListeners

상위: [AbstractApplicationContext.refresh](../README.md)

멀티캐스터에 리스너를 연결하고, 그동안 버퍼에 모아 둔 초기 이벤트를 발행한다. 빈 리스너는 **이름만** 등록하고 아직 만들지 않는다. 빈을 여기서 만들면 그 빈이 뒤에 등록될 후처리기의 적용을 받지 못하기 때문이다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L915-L936 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L915-L936))

```java
// AbstractApplicationContext.java L915-L936
protected void registerListeners() {
    // Register statically specified listeners first.
    for (ApplicationListener<?> listener : getApplicationListeners()) {
        getApplicationEventMulticaster().addApplicationListener(listener);
    }

    // Do not initialize FactoryBeans here: We need to leave all regular beans
    // uninitialized to let post-processors apply to them!
    String[] listenerBeanNames = getBeanNamesForType(ApplicationListener.class, true, false);
    for (String listenerBeanName : listenerBeanNames) {
        getApplicationEventMulticaster().addApplicationListenerBean(listenerBeanName);
    }

    // Publish early application events now that we finally have a multicaster...
    Set<ApplicationEvent> earlyEventsToProcess = this.earlyApplicationEvents;
    this.earlyApplicationEvents = null;
    if (!CollectionUtils.isEmpty(earlyEventsToProcess)) {
        for (ApplicationEvent earlyEvent : earlyEventsToProcess) {
            getApplicationEventMulticaster().multicastEvent(earlyEvent);
        }
    }
}
```

## 동작 흐름

```text
 registerListeners()
 |
 | L917 코드로 추가한 리스너 (context.addApplicationListener(...))
 |        --> multicaster.addApplicationListener(객체)
 |
 | L923 getBeanNamesForType(ApplicationListener, true, false)
 |        allowEagerInit = false  --> FactoryBean 을 만들어 타입을 확인하지 않음
 |        --> multicaster.addApplicationListenerBean(이름)   인스턴스는 나중에 필요할 때
 |
 | L929 early = earlyApplicationEvents
 | L930 earlyApplicationEvents = null     <-- 버퍼 끄기. 이후 publishEvent 는 즉시 전달
 |
 +-- L931 early 가 비어 있지 않으면
          각 이벤트 multicastEvent(event)
            --> 이름으로 등록된 리스너 빈이 이 시점에 getBean 되어 생성될 수 있음
```

## 결과가 쓰이는 곳

```text
 addApplicationListenerBean(이름)
      --> 이벤트가 올 때 멀티캐스터가 getBean(이름) 으로 꺼냄
      --> 보통은 finishBeanFactoryInitialization 에서 이미 만들어진 싱글톤을 받는다

 earlyApplicationEvents = null
      --> publishEvent (AAC L445) 의 분기가 버퍼 적재에서 즉시 multicast 로 바뀜

 초기 이벤트를 받은 리스너
      --> 아직 싱글톤 생성 전이라, 리스너 빈이 이 순간 먼저 만들어진다
          그 빈이 의존하는 빈도 함께 일찍 만들어진다 (후처리기는 이미 등록돼 있어 적용됨)
```

`@EventListener` 메서드는 여기서 등록되지 않는다. 싱글톤이 모두 만들어진 뒤 `EventListenerMethodProcessor.afterSingletonsInstantiated`가 어댑터 리스너로 등록한다([preInstantiateSingletons](../09_AbstractApplicationContext.finishBeanFactoryInitialization/01_DefaultListableBeanFactory.preInstantiateSingletons/README.md) 참고).
