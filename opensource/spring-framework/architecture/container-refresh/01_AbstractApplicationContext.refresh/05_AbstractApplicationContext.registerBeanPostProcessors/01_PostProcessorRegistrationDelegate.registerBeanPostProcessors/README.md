# PostProcessorRegistrationDelegate.registerBeanPostProcessors

상위: [AbstractApplicationContext.registerBeanPostProcessors](../README.md)

`BeanPostProcessor` 정의를 우선순위 순서로 인스턴스화하고 등록한다. 앞 순위 처리기는 뒤 순위 처리기를 만들 때 이미 적용된다. 마지막에 `MergedBeanDefinitionPostProcessor` 계열(내부 처리기)과 리스너 감지기를 **맨 뒤로 옮긴다.**

## 실제 코드

`spring-context` / `org.springframework.context.support` / `PostProcessorRegistrationDelegate.java` L211-L292 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/PostProcessorRegistrationDelegate.java#L211-L292))

```java
// PostProcessorRegistrationDelegate.java L211-L292
public static void registerBeanPostProcessors(
        ConfigurableListableBeanFactory beanFactory, AbstractApplicationContext applicationContext) {

    // WARNING: Although it may appear that the body of this method can be easily
    // refactored to avoid the use of multiple loops and multiple lists, the use
    // of multiple lists and multiple passes over the names of processors is
    // intentional. We must ensure that we honor the contracts for PriorityOrdered
    // and Ordered processors. Specifically, we must NOT cause processors to be
    // instantiated (via getBean() invocations) or registered in the ApplicationContext
    // in the wrong order.
    //
    // Before submitting a pull request (PR) to change this method, please review the
    // list of all declined PRs involving changes to PostProcessorRegistrationDelegate
    // to ensure that your proposal does not result in a breaking change:
    // https://github.com/spring-projects/spring-framework/issues?q=PostProcessorRegistrationDelegate+is%3Aclosed+label%3A%22status%3A+declined%22

    String[] postProcessorNames = beanFactory.getBeanNamesForType(BeanPostProcessor.class, true, false);

    // Register BeanPostProcessorChecker that logs a warn message when
    // a bean is created during BeanPostProcessor instantiation, i.e. when
    // a bean is not eligible for getting processed by all BeanPostProcessors.
    int beanProcessorTargetCount = beanFactory.getBeanPostProcessorCount() + 1 + postProcessorNames.length;
    beanFactory.addBeanPostProcessor(
            new BeanPostProcessorChecker(beanFactory, postProcessorNames, beanProcessorTargetCount));

    // Separate between BeanPostProcessors that implement PriorityOrdered,
    // Ordered, and the rest.
    List<BeanPostProcessor> priorityOrderedPostProcessors = new ArrayList<>();
    List<BeanPostProcessor> internalPostProcessors = new ArrayList<>();
    List<String> orderedPostProcessorNames = new ArrayList<>();
    List<String> nonOrderedPostProcessorNames = new ArrayList<>();
    for (String ppName : postProcessorNames) {
        if (beanFactory.isTypeMatch(ppName, PriorityOrdered.class)) {
            BeanPostProcessor pp = beanFactory.getBean(ppName, BeanPostProcessor.class);
            priorityOrderedPostProcessors.add(pp);
            if (pp instanceof MergedBeanDefinitionPostProcessor) {
                internalPostProcessors.add(pp);
            }
        }
        else if (beanFactory.isTypeMatch(ppName, Ordered.class)) {
            orderedPostProcessorNames.add(ppName);
        }
        else {
            nonOrderedPostProcessorNames.add(ppName);
        }
    }

    // First, register the BeanPostProcessors that implement PriorityOrdered.
    sortPostProcessors(priorityOrderedPostProcessors, beanFactory);
    registerBeanPostProcessors(beanFactory, priorityOrderedPostProcessors);

    // Next, register the BeanPostProcessors that implement Ordered.
    List<BeanPostProcessor> orderedPostProcessors = new ArrayList<>(orderedPostProcessorNames.size());
    for (String ppName : orderedPostProcessorNames) {
        BeanPostProcessor pp = beanFactory.getBean(ppName, BeanPostProcessor.class);
        orderedPostProcessors.add(pp);
        if (pp instanceof MergedBeanDefinitionPostProcessor) {
            internalPostProcessors.add(pp);
        }
    }
    sortPostProcessors(orderedPostProcessors, beanFactory);
    registerBeanPostProcessors(beanFactory, orderedPostProcessors);

    // Now, register all regular BeanPostProcessors.
    List<BeanPostProcessor> nonOrderedPostProcessors = new ArrayList<>(nonOrderedPostProcessorNames.size());
    for (String ppName : nonOrderedPostProcessorNames) {
        BeanPostProcessor pp = beanFactory.getBean(ppName, BeanPostProcessor.class);
        nonOrderedPostProcessors.add(pp);
        if (pp instanceof MergedBeanDefinitionPostProcessor) {
            internalPostProcessors.add(pp);
        }
    }
    registerBeanPostProcessors(beanFactory, nonOrderedPostProcessors);

    // Finally, re-register all internal BeanPostProcessors.
    sortPostProcessors(internalPostProcessors, beanFactory);
    registerBeanPostProcessors(beanFactory, internalPostProcessors);

    // Re-register post-processor for detecting inner beans as ApplicationListeners,
    // moving it to the end of the processor chain (for picking up proxies etc).
    beanFactory.addBeanPostProcessor(new ApplicationListenerDetector(applicationContext));
}
```

등록 도우미와, 처리기 생성 중에 일반 빈이 만들어지는 것을 감시하는 검사기다.

`spring-context` / `org.springframework.context.support` / `PostProcessorRegistrationDelegate.java` L371-L383 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/PostProcessorRegistrationDelegate.java#L371-L383))

```java
// PostProcessorRegistrationDelegate.java L371-L383
private static void registerBeanPostProcessors(
        ConfigurableListableBeanFactory beanFactory, List<? extends BeanPostProcessor> postProcessors) {

    if (beanFactory instanceof AbstractBeanFactory abstractBeanFactory) {
        // Bulk addition is more efficient against our CopyOnWriteArrayList there
        abstractBeanFactory.addBeanPostProcessors(postProcessors);
    }
    else {
        for (BeanPostProcessor postProcessor : postProcessors) {
            beanFactory.addBeanPostProcessor(postProcessor);
        }
    }
}
```

`spring-context` / `org.springframework.context.support` / `PostProcessorRegistrationDelegate.java` L414-L446 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/PostProcessorRegistrationDelegate.java#L414-L446))

```java
// PostProcessorRegistrationDelegate.java L414-L446
@Override
public Object postProcessAfterInitialization(Object bean, String beanName) {
    if (!(bean instanceof BeanPostProcessor) && !isInfrastructureBean(beanName) &&
            this.beanFactory.getBeanPostProcessorCount() < this.beanPostProcessorTargetCount) {
        if (logger.isWarnEnabled()) {
            Set<String> bppsInCreation = new LinkedHashSet<>(2);
            for (String bppName : this.postProcessorNames) {
                if (this.beanFactory.isCurrentlyInCreation(bppName)) {
                    bppsInCreation.add(bppName);
                }
            }
            if (bppsInCreation.size() == 1) {
                String bppName = bppsInCreation.iterator().next();
                if (this.beanFactory.containsBeanDefinition(bppName) &&
                        beanName.equals(this.beanFactory.getBeanDefinition(bppName).getFactoryBeanName())) {
                    logger.warn("Bean '" + beanName + "' of type [" + bean.getClass().getName() +
                            "] is not eligible for getting processed by all BeanPostProcessors " +
                            "(for example: not eligible for auto-proxying). The currently created " +
                            "BeanPostProcessor " + bppsInCreation + " is declared through a non-static " +
                            "factory method on that class; consider declaring it as static instead.");
                    return bean;
                }
            }
            logger.warn("Bean '" + beanName + "' of type [" + bean.getClass().getName() +
                    "] is not eligible for getting processed by all BeanPostProcessors " +
                    "(for example: not eligible for auto-proxying). Is this bean getting eagerly " +
                    "injected/applied to a currently created BeanPostProcessor " + bppsInCreation + "? " +
                    "Check the corresponding BeanPostProcessor declaration and its dependencies/advisors. " +
                    "If this bean does not have to be post-processed, declare it with ROLE_INFRASTRUCTURE.");
        }
    }
    return bean;
}
```

## 동작 흐름

```text
 registerBeanPostProcessors(beanFactory, context)
 |
 | L227 postProcessorNames = BeanPostProcessor 타입 정의 이름 전부
 |
 | L232 targetCount = 현재 처리기 수 + 1 (검사기) + 이름 수
 | L233 addBeanPostProcessor(BeanPostProcessorChecker)
 |
 | L242-L256 이름 분류
 |   PriorityOrdered --> 즉시 getBean   (Autowired..., Common... 처리기)
 |                       MergedBeanDefinitionPostProcessor 면 internal 목록에도
 |   Ordered         --> 이름만
 |   나머지          --> 이름만
 |
 | L259 PriorityOrdered 정렬 --> 등록
 | L263 Ordered 생성 (이제 PriorityOrdered 처리기가 적용됨) --> 정렬 --> 등록
 |        예: AOP 프록시 생성기 (Ordered)
 | L275 나머지 생성 (PriorityOrdered + Ordered 적용됨) --> 등록
 |
 | L286 internal 목록 정렬 --> 다시 등록
 |        addBeanPostProcessors(목록) 은 기존 위치에서 빼고 맨 뒤에 붙인다 (AbstractBeanFactory L997-L1003)
 |        = 내부 처리기들이 체인 끝으로 이동
 |
 +-- L291 addBeanPostProcessor(new ApplicationListenerDetector(context))
          같은 컨텍스트면 equals 가 true (ApplicationListenerDetector L119)
          --> addBeanPostProcessor (L981) 가 prepareBeanFactory 때 넣은 것을 빼고 맨 뒤에 붙임
          프록시가 씌워진 최종 객체를 리스너로 등록하기 위해
```

```text
 BeanPostProcessorChecker.postProcessAfterInitialization(bean)
 |
 +-- bean 이 처리기가 아니고, 인프라 빈이 아니고,
     현재 등록된 처리기 수 < targetCount   (= 아직 등록이 끝나지 않았는데 일반 빈이 만들어졌다)
       --> 경고 "is not eligible for getting processed by all BeanPostProcessors"
           처리기를 만드는 non-static 팩토리 메서드의 설정 클래스라면 static 으로 바꾸라는 안내
```

## 결과가 쓰이는 곳

```text
 최종 처리기 체인 순서 (대략)
      ApplicationContextAwareProcessor          (prepareBeanFactory)
      ImportAwareBeanPostProcessor              (ConfigurationClassPostProcessor.postProcessBeanFactory)
      BeanPostProcessorChecker
      PriorityOrdered 처리기들 (정렬)            Autowired/Common 처리기는 internal 이라 아래로 이동
      Ordered 처리기들 (정렬)                    AOP 프록시 생성기 등
      나머지 처리기들
      internal (MergedBeanDefinitionPostProcessor) 처리기들 (정렬, 뒤로 이동)
      ApplicationListenerDetector               (맨 끝)
      --> 빈 생성 흐름에서 각 확장 지점이 이 순서로 처리기를 순회

 경고가 뜬 빈
      --> 뒤 순위 처리기(AOP 프록시 생성기 등)가 적용되지 않은 상태로 싱글톤이 됨
          @Transactional, @Async 가 그 빈에서 조용히 동작하지 않는 흔한 원인
```
