# AbstractApplicationContext.refresh

상위: [Spring 컨테이너 기동](../README.md)

컨테이너 기동의 템플릿 메서드다. 순서가 고정된 단계를 차례로 부르고, 하위 클래스는 비어 있는 훅(`postProcessBeanFactory`, `onRefresh`)으로만 끼어든다. 중간에 실패하면 이미 시작한 것과 이미 만든 것을 되돌린 뒤 예외를 다시 던진다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L582-L662 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L582-L662))

```java
// AbstractApplicationContext.java L582-L662
public void refresh() throws BeansException, IllegalStateException {
    this.startupShutdownLock.lock();
    try {
        this.startupShutdownThread = Thread.currentThread();

        StartupStep contextRefresh = this.applicationStartup.start("spring.context.refresh");

        // Prepare this context for refreshing.
        prepareRefresh();

        // Tell the subclass to refresh the internal bean factory.
        ConfigurableListableBeanFactory beanFactory = obtainFreshBeanFactory();

        // Prepare the bean factory for use in this context.
        prepareBeanFactory(beanFactory);

        try {
            // Allows post-processing of the bean factory in context subclasses.
            postProcessBeanFactory(beanFactory);

            StartupStep beanPostProcess = this.applicationStartup.start("spring.context.beans.post-process");
            // Invoke factory processors registered as beans in the context.
            invokeBeanFactoryPostProcessors(beanFactory);
            // Register bean processors that intercept bean creation.
            registerBeanPostProcessors(beanFactory);
            beanPostProcess.end();

            // Initialize message source for this context.
            initMessageSource();

            // Initialize event multicaster for this context.
            initApplicationEventMulticaster();

            // Initialize other special beans in specific context subclasses.
            onRefresh();

            // Check for listener beans and register them.
            registerListeners();

            // Instantiate all remaining (non-lazy-init) singletons.
            finishBeanFactoryInitialization(beanFactory);

            // Last step: publish corresponding event.
            finishRefresh();
        }

        catch (RuntimeException | Error ex) {
            if (logger.isWarnEnabled()) {
                logger.warn("Exception encountered during context initialization - " +
                        "cancelling refresh attempt: " + ex);
            }

            // Stop already started Lifecycle beans to avoid dangling resources.
            if (this.lifecycleProcessor != null && this.lifecycleProcessor.isRunning()) {
                try {
                    this.lifecycleProcessor.stop();
                }
                catch (Throwable ex2) {
                    logger.warn("Exception thrown from LifecycleProcessor on cancelled refresh", ex2);
                }
            }

            // Destroy already created singletons to avoid dangling resources.
            destroyBeans();

            // Reset 'active' flag.
            cancelRefresh(ex);

            // Propagate exception to caller.
            throw ex;
        }

        finally {
            contextRefresh.end();
        }
    }
    finally {
        this.startupShutdownThread = null;
        this.startupShutdownLock.unlock();
    }
}
```

## 동작 흐름

```text
 refresh()
 |
 | L583 startupShutdownLock.lock()      refresh와 close가 동시에 돌지 않게
 | L587 StartupStep "spring.context.refresh" 시작   (기동 시간 측정용)
 |
 | L590 prepareRefresh()
 | L593 beanFactory = obtainFreshBeanFactory()
 | L596 prepareBeanFactory(beanFactory)
 |
 +-- try
 |     L600 postProcessBeanFactory(beanFactory)     빈 훅. 웹 컨텍스트는 request/session scope 등록
 |     L604 invokeBeanFactoryPostProcessors         빈 "정의"를 완성하는 단계
 |     L606 registerBeanPostProcessors              빈 "인스턴스"를 가공할 처리기 등록
 |     L610 initMessageSource
 |     L613 initApplicationEventMulticaster
 |     L616 onRefresh()                             빈 훅. Spring Boot는 여기서 내장 웹 서버 생성
 |     L619 registerListeners
 |     L622 finishBeanFactoryInitialization         싱글톤 생성
 |     L625 finishRefresh                           Lifecycle 시작 + ContextRefreshedEvent
 |
 +-- catch RuntimeException | Error
 |     L635 lifecycleProcessor가 이미 running 이면 stop()
 |     L645 destroyBeans()          지금까지 만든 싱글톤 파괴 (@PreDestroy 호출)
 |     L648 cancelRefresh(ex)       active=false, 공통 캐시 초기화
 |     L651 throw ex
 |
 +-- finally  StartupStep 종료, lock 해제
```

단계 순서의 핵심은 **정의 -> 처리기 -> 인스턴스**다. 04에서 빈 정의가 모두 모인 뒤, 05에서 그 정의 중 `BeanPostProcessor`만 먼저 인스턴스로 만들고, 09에서 나머지 빈을 만들 때 05의 처리기가 전부 적용된다.

1. [prepareRefresh](01_AbstractApplicationContext.prepareRefresh/README.md)가 활성 플래그를 켜고 필수 프로퍼티를 검증한다.
2. [obtainFreshBeanFactory](02_AbstractApplicationContext.obtainFreshBeanFactory/README.md)가 작업할 `DefaultListableBeanFactory`를 돌려준다.
3. [prepareBeanFactory](03_AbstractApplicationContext.prepareBeanFactory/README.md)가 컨텍스트 공통 설정(Aware 처리, 자동 주입 대상)을 넣는다.
4. [invokeBeanFactoryPostProcessors](04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/README.md)가 [BeanFactoryPostProcessor](../spi/BeanFactoryPostProcessor/README.md)를 실행해 `@Configuration`을 빈 정의로 펼친다.
5. [registerBeanPostProcessors](05_AbstractApplicationContext.registerBeanPostProcessors/README.md)가 [BeanPostProcessor](../spi/BeanPostProcessor/README.md)를 순서대로 등록한다.
6. [initMessageSource](06_AbstractApplicationContext.initMessageSource/README.md)가 메시지 소스를 준비한다.
7. [initApplicationEventMulticaster](07_AbstractApplicationContext.initApplicationEventMulticaster/README.md)가 이벤트 전달자를 준비한다.
8. [registerListeners](08_AbstractApplicationContext.registerListeners/README.md)가 [ApplicationListener](../spi/ApplicationListener/README.md)를 연결하고 밀린 이벤트를 발행한다.
9. [finishBeanFactoryInitialization](09_AbstractApplicationContext.finishBeanFactoryInitialization/README.md)이 싱글톤을 모두 만든다.
10. [finishRefresh](10_AbstractApplicationContext.finishRefresh/README.md)가 [SmartLifecycle](../spi/SmartLifecycle/README.md) 빈을 시작하고 완료 이벤트를 발행한다.

## 결과가 쓰이는 곳

```text
 beanFactory (L593에서 얻은 것)
      --> 03 ~ 09 모든 단계의 작업 대상. 같은 인스턴스가 끝까지 전달된다

 성공한 refresh
      --> active = true 유지 --> getBean 허용 (assertBeanFactoryActive 통과)
      --> 이후 publishEvent는 버퍼 없이 즉시 전달

 실패한 refresh
      --> 이미 만든 싱글톤의 소멸 콜백이 실행됨 --> DB 풀, 스레드 등이 새지 않음
      --> active = false --> 이 컨텍스트로 getBean 하면 IllegalStateException
      --> GenericApplicationContext 는 refresh 재시도도 불가 (obtainFreshBeanFactory 참고)
```

## 하위 메서드

- [01 prepareRefresh](01_AbstractApplicationContext.prepareRefresh/README.md)
- [02 obtainFreshBeanFactory](02_AbstractApplicationContext.obtainFreshBeanFactory/README.md)
- [03 prepareBeanFactory](03_AbstractApplicationContext.prepareBeanFactory/README.md)
- [04 invokeBeanFactoryPostProcessors](04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/README.md)
- [05 registerBeanPostProcessors](05_AbstractApplicationContext.registerBeanPostProcessors/README.md)
- [06 initMessageSource](06_AbstractApplicationContext.initMessageSource/README.md)
- [07 initApplicationEventMulticaster](07_AbstractApplicationContext.initApplicationEventMulticaster/README.md)
- [08 registerListeners](08_AbstractApplicationContext.registerListeners/README.md)
- [09 finishBeanFactoryInitialization](09_AbstractApplicationContext.finishBeanFactoryInitialization/README.md)
- [10 finishRefresh](10_AbstractApplicationContext.finishRefresh/README.md)
