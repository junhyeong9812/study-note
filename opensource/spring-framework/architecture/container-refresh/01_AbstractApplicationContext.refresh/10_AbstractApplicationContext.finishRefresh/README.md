# AbstractApplicationContext.finishRefresh

상위: [AbstractApplicationContext.refresh](../README.md)

기동의 마지막 단계다. 기동 중에 쌓인 캐시를 비우고, `Lifecycle` 빈을 시작하고, `ContextRefreshedEvent`를 발행한다. 이 이벤트가 나가는 순간이 "컨테이너가 준비됐다"는 공식 신호다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L1003-L1018 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L1003-L1018))

```java
// AbstractApplicationContext.java L1003-L1018
protected void finishRefresh() {
    // Reset common introspection caches in Spring's core infrastructure.
    resetCommonCaches();

    // Clear context-level resource caches (such as ASM metadata from scanning).
    clearResourceCaches();

    // Initialize lifecycle processor for this context.
    initLifecycleProcessor();

    // Propagate refresh to lifecycle processor first.
    getLifecycleProcessor().onRefresh();

    // Publish the final event.
    publishEvent(new ContextRefreshedEvent(this));
}
```

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L880-L898 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L880-L898))

```java
// AbstractApplicationContext.java L880-L898
protected void initLifecycleProcessor() {
    ConfigurableListableBeanFactory beanFactory = getBeanFactory();
    if (beanFactory.containsLocalBean(LIFECYCLE_PROCESSOR_BEAN_NAME)) {
        this.lifecycleProcessor = beanFactory.getBean(LIFECYCLE_PROCESSOR_BEAN_NAME, LifecycleProcessor.class);
        if (logger.isTraceEnabled()) {
            logger.trace("Using LifecycleProcessor [" + this.lifecycleProcessor + "]");
        }
    }
    else {
        DefaultLifecycleProcessor defaultProcessor = new DefaultLifecycleProcessor();
        defaultProcessor.setBeanFactory(beanFactory);
        this.lifecycleProcessor = defaultProcessor;
        beanFactory.registerSingleton(LIFECYCLE_PROCESSOR_BEAN_NAME, this.lifecycleProcessor);
        if (logger.isTraceEnabled()) {
            logger.trace("No '" + LIFECYCLE_PROCESSOR_BEAN_NAME + "' bean, using " +
                    "[" + this.lifecycleProcessor.getClass().getSimpleName() + "]");
        }
    }
}
```

## 동작 흐름

```text
 finishRefresh()
 |
 | L1005 resetCommonCaches()        리플렉션, 애노테이션, ResolvableType, 빈 인트로스펙션 캐시 비움
 |                                    (기동에만 쓰인 메타데이터가 메모리에 남지 않게)
 | L1008 clearResourceCaches()      스캔 때 읽은 ASM 메타데이터 캐시 비움
 |
 | L1011 initLifecycleProcessor()
 |         "lifecycleProcessor" 빈 있으면 사용, 없으면 DefaultLifecycleProcessor 생성 + 싱글톤 등록
 |
 | L1014 getLifecycleProcessor().onRefresh()
 |         autoStartup 인 SmartLifecycle 빈을 phase 순서로 start()
 |
 +-- L1017 publishEvent(new ContextRefreshedEvent(this))
           버퍼는 이미 꺼져 있으므로 즉시 멀티캐스트
```

1. [DefaultLifecycleProcessor.onRefresh](01_DefaultLifecycleProcessor.onRefresh/README.md)가 [SmartLifecycle](../../spi/SmartLifecycle/README.md) 빈을 phase 오름차순으로 시작한다.

## 결과가 쓰이는 곳

```text
 lifecycleProcessor
      --> close() 시 onClose() --> Lifecycle 빈을 phase 역순으로 stop()
      --> context.start() / stop() 을 직접 부를 때의 위임 대상
      --> refresh 실패 시 (refresh L635) 이미 시작한 빈 정지

 ContextRefreshedEvent
      --> @EventListener(ContextRefreshedEvent.class) 메서드
      --> ScheduledAnnotationBeanPostProcessor --> @Scheduled 작업 등록 (그 클래스 L654)
      --> FrameworkServlet.ContextRefreshListener --> DispatcherServlet 전략 초기화
      --> 부모 컨텍스트에도 전달 (publishEvent 의 parent 분기)

 시작된 SmartLifecycle 빈 (예)
      --> 메시지 리스너 컨테이너 (JMS, Kafka) 가 수신 시작
      --> Spring Boot 의 내장 웹 서버가 포트를 열고 요청 수락 시작 (WebServerStartStopLifecycle)
```
