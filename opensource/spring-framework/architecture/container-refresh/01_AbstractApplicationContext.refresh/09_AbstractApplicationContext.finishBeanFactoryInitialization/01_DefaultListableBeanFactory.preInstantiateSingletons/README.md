# DefaultListableBeanFactory.preInstantiateSingletons

상위: [AbstractApplicationContext.finishBeanFactoryInitialization](../README.md)

등록 순서대로 빈 정의를 돌며 lazy가 아닌 싱글톤을 `getBean`으로 만든다. 백그라운드 초기화로 표시된 빈은 부트스트랩 실행기에서 병렬로 만들고 모두 끝날 때까지 기다린다. 전부 만든 뒤에 [SmartInitializingSingleton](../../../spi/SmartInitializingSingleton/README.md) 콜백을 한 번씩 부른다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultListableBeanFactory.java` L1102-L1151 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultListableBeanFactory.java#L1102-L1151))

```java
// DefaultListableBeanFactory.java L1102-L1151
public void preInstantiateSingletons() throws BeansException {
    if (logger.isTraceEnabled()) {
        logger.trace("Pre-instantiating singletons in " + this);
    }

    // Iterate over a copy to allow for init methods which in turn register new bean definitions.
    // While this may not be part of the regular factory bootstrap, it does otherwise work fine.
    List<String> beanNames = new ArrayList<>(this.beanDefinitionNames);

    // Trigger initialization of all non-lazy singleton beans...
    this.preInstantiationThread.set(PreInstantiation.MAIN);
    if (this.mainThreadPrefix == null) {
        this.mainThreadPrefix = getThreadNamePrefix();
    }
    try {
        List<CompletableFuture<?>> futures = new ArrayList<>();
        for (String beanName : beanNames) {
            RootBeanDefinition mbd = getMergedLocalBeanDefinition(beanName);
            if (!mbd.isAbstract() && mbd.isSingleton()) {
                CompletableFuture<?> future = preInstantiateSingleton(beanName, mbd);
                if (future != null) {
                    futures.add(future);
                }
            }
        }
        if (!futures.isEmpty()) {
            try {
                CompletableFuture.allOf(futures.toArray(new CompletableFuture<?>[0])).join();
            }
            catch (CompletionException ex) {
                ReflectionUtils.rethrowRuntimeException(ex.getCause());
            }
        }
    }
    finally {
        this.mainThreadPrefix = null;
        this.preInstantiationThread.remove();
    }

    // Trigger post-initialization callback for all applicable beans...
    for (String beanName : beanNames) {
        Object singletonInstance = getSingleton(beanName, false);
        if (singletonInstance instanceof SmartInitializingSingleton smartSingleton) {
            StartupStep smartInitialize = getApplicationStartup().start("spring.beans.smart-initialize")
                    .tag("beanName", beanName);
            smartSingleton.afterSingletonsInstantiated();
            smartInitialize.end();
        }
    }
}
```

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultListableBeanFactory.java` L1153-L1199 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultListableBeanFactory.java#L1153-L1199))

```java
// DefaultListableBeanFactory.java L1153-L1199
private @Nullable CompletableFuture<?> preInstantiateSingleton(String beanName, RootBeanDefinition mbd) {
    if (mbd.isBackgroundInit()) {
        Executor executor = getBootstrapExecutor();
        if (executor != null) {
            // Force initialization of depends-on beans in mainline thread.
            String[] dependsOn = mbd.getDependsOn();
            if (dependsOn != null) {
                for (String dep : dependsOn) {
                    getBean(dep);
                }
            }
            // Force initialization of factory reference in mainline thread.
            String factoryBeanName = mbd.getFactoryBeanName();
            if (factoryBeanName != null) {
                getBean(factoryBeanName);
            }
            // Instantiate current bean in background thread.
            CompletableFuture<?> future = CompletableFuture.runAsync(
                    () -> instantiateSingletonInBackgroundThread(beanName), executor);
            addSingletonFactory(beanName, () -> {
                try {
                    future.join();
                }
                catch (CompletionException ex) {
                    ReflectionUtils.rethrowRuntimeException(ex.getCause());
                }
                return future;  // not to be exposed, just to lead to ClassCastException in case of mismatch
            });
            return (!mbd.isLazyInit() ? future : null);
        }
        else if (logger.isInfoEnabled()) {
            logger.info("Bean '" + beanName + "' marked for background initialization " +
                    "without bootstrap executor configured - falling back to mainline initialization");
        }
    }

    if (!mbd.isLazyInit()) {
        try {
            instantiateSingleton(beanName);
        }
        catch (BeanCurrentlyInCreationException ex) {
            logger.info("Bean '" + beanName + "' marked for pre-instantiation (not lazy-init) " +
                    "but currently initialized by other thread - skipping it in mainline thread");
        }
    }
    return null;
}
```

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultListableBeanFactory.java` L1217-L1227 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultListableBeanFactory.java#L1217-L1227))

```java
// DefaultListableBeanFactory.java L1217-L1227
private void instantiateSingleton(String beanName) {
    if (isFactoryBean(beanName)) {
        Object bean = getBean(FACTORY_BEAN_PREFIX + beanName);
        if (bean instanceof SmartFactoryBean<?> smartFactoryBean && smartFactoryBean.isEagerInit()) {
            getBean(beanName);
        }
    }
    else {
        getBean(beanName);
    }
}
```

## 동작 흐름

```text
 preInstantiateSingletons()
 |
 | L1109 beanNames = 정의 이름 복사본   (초기화 중 정의가 추가돼도 안전하게 순회)
 | L1112 현재 스레드 = MAIN 부트스트랩
 |
 +-- for beanName in beanNames                                     L1118-L1126
 |     mbd = 병합된 정의 (부모 정의 상속 반영)
 |     추상이 아니고 싱글톤이면 --> preInstantiateSingleton(beanName, mbd)
 |       |
 |       +-- backgroundInit + bootstrapExecutor 있음
 |       |     depends-on 빈과 factoryBean 은 메인 스레드에서 먼저 getBean
 |       |     CompletableFuture.runAsync(instantiateSingleton)   병렬 생성
 |       |     싱글톤 팩토리로 "future 가 끝나면" 을 등록 (다른 빈이 먼저 요청하면 기다림)
 |       |     lazy 가 아니면 future 반환
 |       |
 |       +-- lazy 아님 --> instantiateSingleton(beanName)
 |             FactoryBean 이면
 |               getBean("&" + 이름)  = FactoryBean 자신만 생성
 |               SmartFactoryBean.isEagerInit() 이면 getBean(이름) 으로 제품까지 생성
 |             일반 빈 --> getBean(이름)        <-- 빈 생성 흐름으로 진입
 |
 | L1127 모아 둔 future 전부 join   (하나라도 실패하면 원래 예외로 다시 던짐)
 | L1136 finally  스레드 표시 제거
 |
 +-- for beanName in beanNames                                     L1142-L1150
       싱글톤 인스턴스가 SmartInitializingSingleton 이면
         afterSingletonsInstantiated()
```

getBean 안쪽은 [빈 생성](../../../../bean-creation/README.md) 흐름에서 이어진다.

## 결과가 쓰이는 곳

```text
 getBean(이름) 으로 만들어진 싱글톤
      --> 싱글톤 캐시에 등록 --> 이후 getBean 즉시 반환
      --> 만드는 과정에서 registerBeanPostProcessors 의 체인이 모두 적용됨
          (주입, @PostConstruct, AOP 프록시)
      --> 파괴 콜백이 있으면 disposableBeans 에 등록 --> close() 또는 refresh 실패 시 호출

 afterSingletonsInstantiated() 를 구현한 대표 빈
      EventListenerMethodProcessor
        --> 모든 빈의 @EventListener 메서드를 찾아 ApplicationListener 어댑터로 등록
            = @EventListener 는 싱글톤이 다 만들어진 뒤에야 이벤트를 받기 시작한다
      ScheduledAnnotationBeanPostProcessor (컨텍스트 밖에서 쓰일 때)
        --> @Scheduled 작업 등록
            (컨텍스트 안에서는 ContextRefreshedEvent 를 받아 등록)

 lazy 빈
      --> 여기서 만들어지지 않음 --> 처음 getBean / 주입될 때 생성
```

"다 만든 뒤 한 번"이라는 시점이 필요한 초기화(다른 빈 전체를 훑어야 하는 작업)는 `@PostConstruct` 대신 `SmartInitializingSingleton`에 둔다.
