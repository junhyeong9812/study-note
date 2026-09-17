# Spring 컨테이너 기동

`ApplicationContext`가 만들어져 `refresh()`가 끝날 때까지, 설정 클래스가 빈 정의로 바뀌고 싱글톤이 만들어지고 `Lifecycle` 빈이 시작되는 흐름을 위에서 아래로 따라간다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 기동 중간에 끼어드는 확장 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 진입: new AnnotationConfigApplicationContext(AppConfig.class)

`spring-context` / `org.springframework.context.annotation` / `AnnotationConfigApplicationContext.java` L89-L93 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/AnnotationConfigApplicationContext.java#L89-L93))

```java
// AnnotationConfigApplicationContext.java L89-L93
public AnnotationConfigApplicationContext(Class<?>... componentClasses) {
    this();
    register(componentClasses);
    refresh();
}
```

생성자의 `this()`가 만드는 `AnnotatedBeanDefinitionReader`는 생성되자마자 애노테이션 처리용 후처리기들을 **빈 정의로** 등록한다. `@Configuration`, `@Autowired`, `@PostConstruct`, `@EventListener`가 동작하는 이유가 여기서 시작된다.

`spring-context` / `org.springframework.context.annotation` / `AnnotatedBeanDefinitionReader.java` L85-L91 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/AnnotatedBeanDefinitionReader.java#L85-L91))

```java
// AnnotatedBeanDefinitionReader.java L85-L91
public AnnotatedBeanDefinitionReader(BeanDefinitionRegistry registry, Environment environment) {
    Assert.notNull(registry, "BeanDefinitionRegistry must not be null");
    Assert.notNull(environment, "Environment must not be null");
    this.registry = registry;
    this.conditionEvaluator = new ConditionEvaluator(registry, environment, null);
    AnnotationConfigUtils.registerAnnotationConfigProcessors(this.registry);
}
```

`spring-context` / `org.springframework.context.annotation` / `AnnotationConfigUtils.java` L143-L205 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/AnnotationConfigUtils.java#L143-L205))

```java
// AnnotationConfigUtils.java L143-L205
public static Set<BeanDefinitionHolder> registerAnnotationConfigProcessors(
        BeanDefinitionRegistry registry, @Nullable Object source) {

    DefaultListableBeanFactory beanFactory = unwrapDefaultListableBeanFactory(registry);
    if (beanFactory != null) {
        if (!(beanFactory.getDependencyComparator() instanceof AnnotationAwareOrderComparator)) {
            beanFactory.setDependencyComparator(AnnotationAwareOrderComparator.INSTANCE);
        }
        if (!(beanFactory.getAutowireCandidateResolver() instanceof ContextAnnotationAutowireCandidateResolver)) {
            beanFactory.setAutowireCandidateResolver(new ContextAnnotationAutowireCandidateResolver());
        }
    }

    Set<BeanDefinitionHolder> beanDefs = CollectionUtils.newLinkedHashSet(6);

    if (!registry.containsBeanDefinition(CONFIGURATION_ANNOTATION_PROCESSOR_BEAN_NAME)) {
        RootBeanDefinition def = new RootBeanDefinition(ConfigurationClassPostProcessor.class);
        def.setSource(source);
        beanDefs.add(registerPostProcessor(registry, def, CONFIGURATION_ANNOTATION_PROCESSOR_BEAN_NAME));
    }

    if (!registry.containsBeanDefinition(AUTOWIRED_ANNOTATION_PROCESSOR_BEAN_NAME)) {
        RootBeanDefinition def = new RootBeanDefinition(AutowiredAnnotationBeanPostProcessor.class);
        def.setSource(source);
        beanDefs.add(registerPostProcessor(registry, def, AUTOWIRED_ANNOTATION_PROCESSOR_BEAN_NAME));
    }

    // Check for Jakarta Annotations support, and if present add the CommonAnnotationBeanPostProcessor.
    if (JAKARTA_ANNOTATIONS_PRESENT && !registry.containsBeanDefinition(COMMON_ANNOTATION_PROCESSOR_BEAN_NAME)) {
        RootBeanDefinition def = new RootBeanDefinition(CommonAnnotationBeanPostProcessor.class);
        def.setSource(source);
        beanDefs.add(registerPostProcessor(registry, def, COMMON_ANNOTATION_PROCESSOR_BEAN_NAME));
    }

    // Check for JPA support, and if present add the PersistenceAnnotationBeanPostProcessor.
    if (JPA_PRESENT && !registry.containsBeanDefinition(PERSISTENCE_ANNOTATION_PROCESSOR_BEAN_NAME)) {
        RootBeanDefinition def = new RootBeanDefinition();
        try {
            def.setBeanClass(ClassUtils.forName(PERSISTENCE_ANNOTATION_PROCESSOR_CLASS_NAME,
                    AnnotationConfigUtils.class.getClassLoader()));
        }
        catch (ClassNotFoundException ex) {
            throw new IllegalStateException(
                    "Cannot load optional framework class: " + PERSISTENCE_ANNOTATION_PROCESSOR_CLASS_NAME, ex);
        }
        def.setSource(source);
        beanDefs.add(registerPostProcessor(registry, def, PERSISTENCE_ANNOTATION_PROCESSOR_BEAN_NAME));
    }

    if (!registry.containsBeanDefinition(EVENT_LISTENER_PROCESSOR_BEAN_NAME)) {
        RootBeanDefinition def = new RootBeanDefinition(EventListenerMethodProcessor.class);
        def.setSource(source);
        beanDefs.add(registerPostProcessor(registry, def, EVENT_LISTENER_PROCESSOR_BEAN_NAME));
    }

    if (!registry.containsBeanDefinition(EVENT_LISTENER_FACTORY_BEAN_NAME)) {
        RootBeanDefinition def = new RootBeanDefinition(DefaultEventListenerFactory.class);
        def.setSource(source);
        beanDefs.add(registerPostProcessor(registry, def, EVENT_LISTENER_FACTORY_BEAN_NAME));
    }

    return beanDefs;
}
```

```text
 new AnnotationConfigApplicationContext(AppConfig.class)
 |
 +-- this()
 |     +-- new AnnotatedBeanDefinitionReader(this)
 |     |     registerAnnotationConfigProcessors(registry)       아직 인스턴스가 아니라 "정의"만 등록
 |     |       ConfigurationClassPostProcessor       BeanDefinitionRegistryPostProcessor, PriorityOrdered
 |     |       AutowiredAnnotationBeanPostProcessor  BeanPostProcessor, PriorityOrdered    @Autowired @Value
 |     |       CommonAnnotationBeanPostProcessor     BeanPostProcessor, PriorityOrdered    @PostConstruct @Resource (jakarta 있을 때)
 |     |       PersistenceAnnotationBeanPostProcessor                                     @PersistenceContext (JPA 있을 때)
 |     |       EventListenerMethodProcessor          BeanFactoryPostProcessor + SmartInitializingSingleton  @EventListener
 |     |       DefaultEventListenerFactory
 |     +-- new ClassPathBeanDefinitionScanner(this)
 |
 +-- register(AppConfig.class)     AppConfig 자체를 빈 정의 1개로 등록 (아직 파싱 안 함)
 |
 +-- refresh()                     <-- 여기서부터 이 트리
```

## 전체 그림

```text
 AbstractApplicationContext.refresh()
 |
 +-- [01] prepareRefresh                  active=true, 필수 프로퍼티 검증, 초기 이벤트 버퍼 준비
 +-- [02] obtainFreshBeanFactory          GenericApplicationContext: 기존 팩토리 그대로 (1회만 허용)
 +-- [03] prepareBeanFactory              Aware 처리기, 자동 주입 대상, environment 싱글톤
 +--      postProcessBeanFactory          하위 클래스 훅 (웹 컨텍스트가 scope 등록)
 |
 +-- [04] invokeBeanFactoryPostProcessors ---> BeanFactoryPostProcessor        (spi)
 |          ConfigurationClassPostProcessor
 |            +-- processConfigBeanDefinitions
 |            |     +-- ConfigurationClassParser.parse     @ComponentScan @Import @Bean 읽기
 |            |     +-- ConfigurationClassBeanDefinitionReader.loadBeanDefinitions   @Bean -> 빈 정의
 |            +-- enhanceConfigurationClasses              @Configuration -> CGLIB 하위 클래스
 |          = 빈 정의 목록 완성
 |
 +-- [05] registerBeanPostProcessors ------> BeanPostProcessor               (spi)
 |          = 이후 만들어지는 모든 빈에 적용될 처리기 체인 완성
 |
 +-- [06] initMessageSource
 +-- [07] initApplicationEventMulticaster
 +--      onRefresh                       하위 클래스 훅 (Spring Boot가 내장 웹 서버 생성)
 +-- [08] registerListeners -------------> ApplicationListener              (spi)
 |          버퍼에 쌓인 초기 이벤트 발행
 |
 +-- [09] finishBeanFactoryInitialization
 |          +-- preInstantiateSingletons  lazy 아닌 싱글톤 전부 getBean  (빈 생성 흐름으로 이어짐)
 |                afterSingletonsInstantiated ---> SmartInitializingSingleton (spi)
 |
 +-- [10] finishRefresh
            +-- DefaultLifecycleProcessor.onRefresh ---> SmartLifecycle.start (spi)
            +-- publishEvent(ContextRefreshedEvent)

 예외 --> 시작된 Lifecycle 정지 --> 만든 싱글톤 파괴 --> active=false --> 다시 던짐
```

## 단계

1. [AbstractApplicationContext.refresh](01_AbstractApplicationContext.refresh/README.md)가 위 10단계를 순서대로 부르고, 실패하면 만든 것을 되돌린다.

## 결과가 쓰이는 곳

```text
 refresh()가 끝난 컨텍스트
      +-- getBean(...)                   이미 만들어진 싱글톤을 바로 반환
      +-- publishEvent(...)              멀티캐스터로 즉시 전달 (더 이상 버퍼링 안 함)
      +-- close() / registerShutdownHook
             Lifecycle 정지 (phase 역순) --> 싱글톤 파괴 (@PreDestroy, DisposableBean)
      +-- ContextRefreshedEvent (finishRefresh에서 발행)
             웹이라면 FrameworkServlet.ContextRefreshListener (L1179) 가 받음
             --> DispatcherServlet.onRefresh --> initStrategies   MVC 전략 목록 채우기
```

마지막 가지가 [Spring MVC 요청 처리](../webmvc-request-processing/README.md)의 "기동할 때 준비되는 것"으로 이어지는 연결점이다.

## 다루지 않는 것

`getBean` 안쪽(인스턴스 생성, 의존성 주입, 초기화 콜백, AOP 프록시 적용)은 다음 흐름인 "빈 생성"에서 다룬다. XML 설정(`AbstractRefreshableApplicationContext`)은 [obtainFreshBeanFactory](01_AbstractApplicationContext.refresh/02_AbstractApplicationContext.obtainFreshBeanFactory/README.md)에서 갈림길만 표시했다.

## 하위 메서드

- [01 AbstractApplicationContext.refresh](01_AbstractApplicationContext.refresh/README.md)
- [spi](spi/README.md) — 기동 중간의 확장 인터페이스
