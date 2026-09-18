# Spring 이벤트 발행

`publishEvent(...)` 한 번이 리스너 메서드 실행으로 이어지기까지의 흐름을 위에서 아래로 따라간다. 이벤트 객체를 정규화하고, 타입에 맞는 리스너를 골라내고, 하나씩 호출한다. `@EventListener` 메서드는 어댑터로 감싸져 같은 목록에 들어간다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 이 과정의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 publishEvent(객체 또는 ApplicationEvent)
 |
 +-- [01] AbstractApplicationContext.publishEvent
        |
        | ApplicationEvent 가 아니면 PayloadApplicationEvent 로 감싼다
        |
        +-- 기동 중이라 멀티캐스터가 아직 없음 --> earlyApplicationEvents 버퍼에 적재
        |                                         (registerListeners 에서 한꺼번에 발행)
        |
        +-- [02] SimpleApplicationEventMulticaster.multicastEvent
        |      |
        |      +-- [02-01] getApplicationListeners        이 이벤트를 받을 리스너 선별
        |      |              (이벤트 타입, 소스 타입) 키로 캐시
        |      |              제네릭 타입까지 보고 거르고, @Order 로 정렬
        |      |
        |      +-- [02-02] invokeListener                 리스너 하나 호출
        |             taskExecutor 가 있으면 그 스레드에서, 없으면 발행 스레드에서
        |             errorHandler 가 있으면 예외를 잡아 넘긴다
        |             |
        |             +-- listener.onApplicationEvent(event)
        |                    +-- [03] ApplicationListenerMethodAdapter.processEvent
        |                           @EventListener 메서드용 어댑터
        |                           인자 해석 --> condition(SpEL) 평가 --> 메서드 호출
        |                           반환값이 있으면 그것을 다시 이벤트로 발행
        |
        +-- 부모 컨텍스트가 있으면 부모에도 같은 이벤트를 발행
```

## 단계

1. [AbstractApplicationContext.publishEvent](01_AbstractApplicationContext.publishEvent/README.md)가 이벤트를 정규화하고 멀티캐스터에게 넘긴다.
2. [SimpleApplicationEventMulticaster.multicastEvent](02_SimpleApplicationEventMulticaster.multicastEvent/README.md)가 리스너를 골라 하나씩 호출한다.
3. [ApplicationListenerMethodAdapter.processEvent](03_ApplicationListenerMethodAdapter.processEvent/README.md)가 `@EventListener` 메서드를 실행한다.

## @EventListener 는 언제 등록되는가

애노테이션만으로는 리스너가 되지 않는다. 싱글톤이 모두 만들어진 뒤 `EventListenerMethodProcessor`가 빈을 훑어 어댑터를 만들어 등록한다.

`spring-context` / `org.springframework.context.event` / `EventListenerMethodProcessor.java` L152-L202 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/EventListenerMethodProcessor.java#L152-L202))

```java
// EventListenerMethodProcessor.java L152-L202
private void processBean(final String beanName, final Class<?> targetType) {
    if (!this.nonAnnotatedClasses.contains(targetType) &&
            AnnotationUtils.isCandidateClass(targetType, EventListener.class) &&
            !isSpringContainerClass(targetType)) {

        Map<Method, EventListener> annotatedMethods = null;
        try {
            annotatedMethods = MethodIntrospector.selectMethods(targetType,
                    (MethodIntrospector.MetadataLookup<EventListener>) method ->
                            AnnotatedElementUtils.findMergedAnnotation(method, EventListener.class));
        }
        catch (Throwable ex) {
            // An unresolvable type in a method signature, probably from a lazy bean - let's ignore it.
            if (logger.isDebugEnabled()) {
                logger.debug("Could not resolve methods for bean with name '" + beanName + "'", ex);
            }
        }

        if (CollectionUtils.isEmpty(annotatedMethods)) {
            this.nonAnnotatedClasses.add(targetType);
            if (logger.isTraceEnabled()) {
                logger.trace("No @EventListener annotations found on bean class: " + targetType.getName());
            }
        }
        else {
            // Non-empty set of methods
            ConfigurableApplicationContext context = this.applicationContext;
            Assert.state(context != null, "No ApplicationContext set");
            List<EventListenerFactory> factories = this.eventListenerFactories;
            Assert.state(factories != null, "EventListenerFactory List not initialized");
            for (Method method : annotatedMethods.keySet()) {
                for (EventListenerFactory factory : factories) {
                    if (factory.supportsMethod(method)) {
                        Method methodToUse = AopUtils.selectInvocableMethod(method, context.getType(beanName));
                        ApplicationListener<?> applicationListener =
                                factory.createApplicationListener(beanName, targetType, methodToUse);
                        if (applicationListener instanceof ApplicationListenerMethodAdapter alma) {
                            alma.init(context, this.evaluator);
                        }
                        context.addApplicationListener(applicationListener);
                        break;
                    }
                }
            }
            if (logger.isDebugEnabled()) {
                logger.debug(annotatedMethods.size() + " @EventListener methods processed on bean '" +
                        beanName + "': " + annotatedMethods);
            }
        }
    }
}
```

```text
 [컨테이너 기동] preInstantiateSingletons
   --> EventListenerMethodProcessor.afterSingletonsInstantiated
         모든 빈 이름을 훑어 processBean
           @EventListener 메서드를 찾는다 (없으면 클래스를 nonAnnotatedClasses 에 기록)
           EventListenerFactory 로 ApplicationListener 어댑터 생성
             기본: DefaultEventListenerFactory --> ApplicationListenerMethodAdapter
             @TransactionalEventListener: TransactionalEventListenerFactory --> 트랜잭션 단계 연동 어댑터
           context.addApplicationListener(어댑터)
   = 이 시점 이전에 발행된 이벤트는 @EventListener 가 받지 못한다
```

시작점은 [컨테이너 기동](../container-refresh/README.md)의 [registerListeners](../container-refresh/01_AbstractApplicationContext.refresh/08_AbstractApplicationContext.registerListeners/README.md)와 [preInstantiateSingletons](../container-refresh/01_AbstractApplicationContext.refresh/09_AbstractApplicationContext.finishBeanFactoryInitialization/01_DefaultListableBeanFactory.preInstantiateSingletons/README.md)다.

## 결과가 쓰이는 곳

```text
 동기 발행 (기본)
      --> 리스너가 모두 끝난 뒤에야 publishEvent 가 반환된다
      --> 발행자의 트랜잭션 안에서 리스너가 실행된다 (같은 스레드, 같은 커넥션)

 비동기 발행 (멀티캐스터에 taskExecutor 설정)
      --> 리스너가 다른 스레드에서 실행
      --> 트랜잭션과 ThreadLocal 문맥이 전파되지 않는다

 @TransactionalEventListener
      --> 커밋 시점까지 실행을 미룬다 (트랜잭션 동기화 콜백 사용)
      --> 트랜잭션이 없으면 기본적으로 실행되지 않는다
```

## 다루지 않는 것

`@TransactionalEventListener`가 트랜잭션 단계에 붙는 구체적 경로는 [트랜잭션](../transaction/README.md) 흐름의 `TransactionSynchronization`과 이어진다. 리액티브 반환값 처리(`ReactiveResultHandler`)도 이 지도에서는 요약만 했다.

## 하위 메서드

- [01 AbstractApplicationContext.publishEvent](01_AbstractApplicationContext.publishEvent/README.md)
- [02 SimpleApplicationEventMulticaster.multicastEvent](02_SimpleApplicationEventMulticaster.multicastEvent/README.md)
- [03 ApplicationListenerMethodAdapter.processEvent](03_ApplicationListenerMethodAdapter.processEvent/README.md)
- [spi](spi/README.md) — 발행자, 리스너, 멀티캐스터, 리스너 팩토리
