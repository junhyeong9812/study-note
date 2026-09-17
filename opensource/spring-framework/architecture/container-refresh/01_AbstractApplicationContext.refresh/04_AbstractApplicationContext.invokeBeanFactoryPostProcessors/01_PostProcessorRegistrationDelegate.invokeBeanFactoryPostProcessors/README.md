# PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors

상위: [AbstractApplicationContext.invokeBeanFactoryPostProcessors](../README.md)

`BeanFactoryPostProcessor`의 실행 순서를 정하는 곳이다. 빈 정의를 **추가**할 수 있는 `BeanDefinitionRegistryPostProcessor`를 먼저, 그중에서도 `PriorityOrdered`, `Ordered`, 나머지 순으로 실행하고, 새 처리기가 더 나오지 않을 때까지 반복한다. 그다음 일반 `BeanFactoryPostProcessor`를 같은 우선순위로 실행한다. 코드 첫머리의 경고 주석대로, 여러 번 도는 구조는 순서 계약을 지키기 위한 의도된 설계다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `PostProcessorRegistrationDelegate.java` L68-L209 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/PostProcessorRegistrationDelegate.java#L68-L209))

```java
// PostProcessorRegistrationDelegate.java L68-L209
public static void invokeBeanFactoryPostProcessors(
        ConfigurableListableBeanFactory beanFactory, List<BeanFactoryPostProcessor> beanFactoryPostProcessors) {

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

    // Invoke BeanDefinitionRegistryPostProcessors first, if any.
    Set<String> processedBeans = new HashSet<>();

    if (beanFactory instanceof BeanDefinitionRegistry registry) {
        List<BeanFactoryPostProcessor> regularPostProcessors = new ArrayList<>();
        List<BeanDefinitionRegistryPostProcessor> registryProcessors = new ArrayList<>();

        for (BeanFactoryPostProcessor postProcessor : beanFactoryPostProcessors) {
            if (postProcessor instanceof BeanDefinitionRegistryPostProcessor registryProcessor) {
                registryProcessor.postProcessBeanDefinitionRegistry(registry);
                registryProcessors.add(registryProcessor);
            }
            else {
                regularPostProcessors.add(postProcessor);
            }
        }

        // Do not initialize FactoryBeans here: We need to leave all regular beans
        // uninitialized to let the bean factory post-processors apply to them!
        // Separate between BeanDefinitionRegistryPostProcessors that implement
        // PriorityOrdered, Ordered, and the rest.
        List<BeanDefinitionRegistryPostProcessor> currentRegistryProcessors = new ArrayList<>();

        // First, invoke the BeanDefinitionRegistryPostProcessors that implement PriorityOrdered.
        String[] postProcessorNames =
                beanFactory.getBeanNamesForType(BeanDefinitionRegistryPostProcessor.class, true, false);
        for (String ppName : postProcessorNames) {
            if (beanFactory.isTypeMatch(ppName, PriorityOrdered.class)) {
                currentRegistryProcessors.add(beanFactory.getBean(ppName, BeanDefinitionRegistryPostProcessor.class));
                processedBeans.add(ppName);
            }
        }
        sortPostProcessors(currentRegistryProcessors, beanFactory);
        registryProcessors.addAll(currentRegistryProcessors);
        invokeBeanDefinitionRegistryPostProcessors(currentRegistryProcessors, registry, beanFactory.getApplicationStartup());
        currentRegistryProcessors.clear();

        // Next, invoke the BeanDefinitionRegistryPostProcessors that implement Ordered.
        postProcessorNames = beanFactory.getBeanNamesForType(BeanDefinitionRegistryPostProcessor.class, true, false);
        for (String ppName : postProcessorNames) {
            if (!processedBeans.contains(ppName) && beanFactory.isTypeMatch(ppName, Ordered.class)) {
                currentRegistryProcessors.add(beanFactory.getBean(ppName, BeanDefinitionRegistryPostProcessor.class));
                processedBeans.add(ppName);
            }
        }
        sortPostProcessors(currentRegistryProcessors, beanFactory);
        registryProcessors.addAll(currentRegistryProcessors);
        invokeBeanDefinitionRegistryPostProcessors(currentRegistryProcessors, registry, beanFactory.getApplicationStartup());
        currentRegistryProcessors.clear();

        // Finally, invoke all other BeanDefinitionRegistryPostProcessors until no further ones appear.
        boolean reiterate = true;
        while (reiterate) {
            reiterate = false;
            postProcessorNames = beanFactory.getBeanNamesForType(BeanDefinitionRegistryPostProcessor.class, true, false);
            for (String ppName : postProcessorNames) {
                if (!processedBeans.contains(ppName)) {
                    currentRegistryProcessors.add(beanFactory.getBean(ppName, BeanDefinitionRegistryPostProcessor.class));
                    processedBeans.add(ppName);
                    reiterate = true;
                }
            }
            sortPostProcessors(currentRegistryProcessors, beanFactory);
            registryProcessors.addAll(currentRegistryProcessors);
            invokeBeanDefinitionRegistryPostProcessors(currentRegistryProcessors, registry, beanFactory.getApplicationStartup());
            currentRegistryProcessors.clear();
        }

        // Now, invoke the postProcessBeanFactory callback of all processors handled so far.
        invokeBeanFactoryPostProcessors(registryProcessors, beanFactory);
        invokeBeanFactoryPostProcessors(regularPostProcessors, beanFactory);
    }

    else {
        // Invoke factory processors registered with the context instance.
        invokeBeanFactoryPostProcessors(beanFactoryPostProcessors, beanFactory);
    }

    // Do not initialize FactoryBeans here: We need to leave all regular beans
    // uninitialized to let the bean factory post-processors apply to them!
    String[] postProcessorNames =
            beanFactory.getBeanNamesForType(BeanFactoryPostProcessor.class, true, false);

    // Separate between BeanFactoryPostProcessors that implement PriorityOrdered,
    // Ordered, and the rest.
    List<BeanFactoryPostProcessor> priorityOrderedPostProcessors = new ArrayList<>();
    List<String> orderedPostProcessorNames = new ArrayList<>();
    List<String> nonOrderedPostProcessorNames = new ArrayList<>();
    for (String ppName : postProcessorNames) {
        if (processedBeans.contains(ppName)) {
            // skip - already processed in first phase above
        }
        else if (beanFactory.isTypeMatch(ppName, PriorityOrdered.class)) {
            priorityOrderedPostProcessors.add(beanFactory.getBean(ppName, BeanFactoryPostProcessor.class));
        }
        else if (beanFactory.isTypeMatch(ppName, Ordered.class)) {
            orderedPostProcessorNames.add(ppName);
        }
        else {
            nonOrderedPostProcessorNames.add(ppName);
        }
    }

    // First, invoke the BeanFactoryPostProcessors that implement PriorityOrdered.
    sortPostProcessors(priorityOrderedPostProcessors, beanFactory);
    invokeBeanFactoryPostProcessors(priorityOrderedPostProcessors, beanFactory);

    // Next, invoke the BeanFactoryPostProcessors that implement Ordered.
    List<BeanFactoryPostProcessor> orderedPostProcessors = new ArrayList<>(orderedPostProcessorNames.size());
    for (String postProcessorName : orderedPostProcessorNames) {
        orderedPostProcessors.add(beanFactory.getBean(postProcessorName, BeanFactoryPostProcessor.class));
    }
    sortPostProcessors(orderedPostProcessors, beanFactory);
    invokeBeanFactoryPostProcessors(orderedPostProcessors, beanFactory);

    // Finally, invoke all other BeanFactoryPostProcessors.
    List<BeanFactoryPostProcessor> nonOrderedPostProcessors = new ArrayList<>(nonOrderedPostProcessorNames.size());
    for (String postProcessorName : nonOrderedPostProcessorNames) {
        nonOrderedPostProcessors.add(beanFactory.getBean(postProcessorName, BeanFactoryPostProcessor.class));
    }
    invokeBeanFactoryPostProcessors(nonOrderedPostProcessors, beanFactory);

    // Clear cached merged bean definitions since the post-processors might have
    // modified the original metadata, for example, replacing placeholders in values...
    beanFactory.clearMetadataCache();
}
```

## 동작 흐름

```text
 invokeBeanFactoryPostProcessors(beanFactory, 코드로 넣은 처리기들)
 |
 | ===== 1부: BeanDefinitionRegistryPostProcessor (정의 추가 가능) =====   L87-L155
 |
 | [a] 코드로 넣은 처리기 중 Registry 처리기 --> 즉시 postProcessBeanDefinitionRegistry
 |
 | [b] 정의에서 찾은 Registry 처리기 중 PriorityOrdered              L108-L119
 |       getBean 으로 생성 --> 정렬 --> postProcessBeanDefinitionRegistry
 |       ConfigurationClassPostProcessor 가 여기서 실행됨
 |         --> @ComponentScan, @Import, @Bean 을 읽어 정의를 대량 추가
 |
 | [c] 다시 찾기 (b에서 정의가 늘었으므로) 중 Ordered                  L122-L132
 |       @Import 로 새로 들어온 Registry 처리기도 여기서 잡힘
 |
 | [d] 남은 것 전부, 새로 나오지 않을 때까지 반복                        L135-L150
 |       Registry 처리기가 또 다른 Registry 처리기 정의를 추가할 수 있으므로
 |
 | [e] 지금까지 실행한 Registry 처리기들의 postProcessBeanFactory      L153
 |       ConfigurationClassPostProcessor --> enhanceConfigurationClasses
 | [f] 코드로 넣은 일반 처리기의 postProcessBeanFactory                L154
 |
 | ===== 2부: 일반 BeanFactoryPostProcessor (정의 수정만) =====        L164-L204
 |
 | 정의에서 BeanFactoryPostProcessor 이름 전부 조회
 |   1부에서 이미 처리한 이름 --> 건너뜀
 |   PriorityOrdered --> 즉시 getBean  (예: PropertySourcesPlaceholderConfigurer)
 |   Ordered         --> 이름만 모음
 |   나머지          --> 이름만 모음   (예: EventListenerMethodProcessor)
 | PriorityOrdered 정렬 후 실행 --> Ordered 생성, 정렬, 실행 --> 나머지 생성, 실행
 |
 +-- L208 clearMetadataCache()     처리기가 정의를 바꿨을 수 있으므로 병합 정의 캐시 무효화
```

Ordered와 나머지를 이름으로만 모았다가 뒤에 만드는 이유는, `PriorityOrdered` 처리기(예: 플레이스홀더 치환기)가 먼저 정의를 고친 뒤에 그 정의로 인스턴스를 만들어야 하기 때문이다.

- 1부 [b]에서 실행되는 [ConfigurationClassPostProcessor.processConfigBeanDefinitions](01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/README.md)가 설정 클래스를 빈 정의로 펼친다.
- 1부 [e]에서 실행되는 [ConfigurationClassPostProcessor.enhanceConfigurationClasses](02_ConfigurationClassPostProcessor.enhanceConfigurationClasses/README.md)가 `@Configuration` 클래스를 CGLIB 하위 클래스로 바꾼다.

## 결과가 쓰이는 곳

```text
 processedBeans (1부에서 실행한 처리기 이름)
      --> 2부에서 중복 실행 방지

 1부가 추가한 빈 정의
      --> 2부의 BeanFactoryPostProcessor 조회 대상에 포함
          = @Bean static PropertySourcesPlaceholderConfigurer 가 동작하는 이유

 이 단계에서 getBean 으로 만든 처리기 인스턴스
      --> 아직 BeanPostProcessor 가 등록되기 전이라 @Autowired 등이 적용되지 않는다
          그래서 BeanFactoryPostProcessor 를 반환하는 @Bean 은 static 으로 선언하라고 권장한다
          (non-static 이면 설정 클래스 인스턴스까지 일찍 만들어져 같은 문제를 겪는다)
```

## 하위 메서드

- [01 ConfigurationClassPostProcessor.processConfigBeanDefinitions](01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/README.md)
- [02 ConfigurationClassPostProcessor.enhanceConfigurationClasses](02_ConfigurationClassPostProcessor.enhanceConfigurationClasses/README.md)
