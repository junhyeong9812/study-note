# ConfigurationClassPostProcessor.processConfigBeanDefinitions

상위: [PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors](../README.md)

`@Configuration`, `@Component` 같은 설정 후보 정의를 찾아 파싱하고, 파싱 결과(`@Bean`, `@Import` 등)를 새 빈 정의로 등록한다. 등록한 정의 중에 또 설정 후보가 있으면 더 나오지 않을 때까지 반복한다. 애노테이션 기반 설정이 빈 정의로 바뀌는 곳이 여기다.

## 진입: postProcessBeanDefinitionRegistry

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassPostProcessor.java` L304-L317 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassPostProcessor.java#L304-L317))

```java
// ConfigurationClassPostProcessor.java L304-L317
public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) {
    int registryId = System.identityHashCode(registry);
    if (this.registriesPostProcessed.contains(registryId)) {
        throw new IllegalStateException(
                "postProcessBeanDefinitionRegistry already called on this post-processor against " + registry);
    }
    if (this.factoriesPostProcessed.contains(registryId)) {
        throw new IllegalStateException(
                "postProcessBeanFactory already called on this post-processor against " + registry);
    }
    this.registriesPostProcessed.add(registryId);

    processConfigBeanDefinitions(registry);
}
```

## 실제 코드

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassPostProcessor.java` L389-L506 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassPostProcessor.java#L389-L506))

```java
// ConfigurationClassPostProcessor.java L389-L506
public void processConfigBeanDefinitions(BeanDefinitionRegistry registry) {
    List<BeanDefinitionHolder> configCandidates = new ArrayList<>();
    String[] candidateNames = registry.getBeanDefinitionNames();

    for (String beanName : candidateNames) {
        BeanDefinition beanDef = registry.getBeanDefinition(beanName);
        if (beanDef.getAttribute(ConfigurationClassUtils.CONFIGURATION_CLASS_ATTRIBUTE) != null) {
            if (logger.isDebugEnabled()) {
                logger.debug("Bean definition has already been processed as a configuration class: " + beanDef);
            }
        }
        else if (ConfigurationClassUtils.checkConfigurationClassCandidate(beanDef, this.metadataReaderFactory)) {
            configCandidates.add(new BeanDefinitionHolder(beanDef, beanName));
        }
    }

    // Return immediately if no @Configuration classes were found
    if (configCandidates.isEmpty()) {
        return;
    }

    // Sort by previously determined @Order value, if applicable
    configCandidates.sort((bd1, bd2) -> {
        int i1 = ConfigurationClassUtils.getOrder(bd1.getBeanDefinition());
        int i2 = ConfigurationClassUtils.getOrder(bd2.getBeanDefinition());
        return Integer.compare(i1, i2);
    });

    // Detect any custom bean name generation strategy supplied through the enclosing application context
    SingletonBeanRegistry singletonRegistry = null;
    if (registry instanceof SingletonBeanRegistry sbr) {
        singletonRegistry = sbr;
        BeanNameGenerator configurationGenerator = (BeanNameGenerator) singletonRegistry.getSingleton(
                AnnotationConfigUtils.CONFIGURATION_BEAN_NAME_GENERATOR);
        if (configurationGenerator != null) {
            if (this.localBeanNameGeneratorSet) {
                if (configurationGenerator instanceof ConfigurationBeanNameGenerator &
                        configurationGenerator != this.importBeanNameGenerator) {
                    throw new IllegalStateException("Context-level ConfigurationBeanNameGenerator [" +
                            configurationGenerator + "] must not be overridden with processor-level generator [" +
                            this.importBeanNameGenerator + "]");
                }
            }
            else {
                this.componentScanBeanNameGenerator = configurationGenerator;
                this.importBeanNameGenerator = configurationGenerator;
            }
        }
    }

    if (this.environment == null) {
        this.environment = new StandardEnvironment();
    }

    // Parse each @Configuration class
    ConfigurationClassParser parser = new ConfigurationClassParser(
            this.metadataReaderFactory, this.problemReporter, this.environment,
            this.resourceLoader, this.componentScanBeanNameGenerator, registry);

    Set<BeanDefinitionHolder> candidates = new LinkedHashSet<>(configCandidates);
    Set<ConfigurationClass> alreadyParsed = CollectionUtils.newHashSet(configCandidates.size());
    do {
        StartupStep processConfig = this.applicationStartup.start("spring.context.config-classes.parse");
        parser.parse(candidates);
        parser.validate();

        Set<ConfigurationClass> configClasses = new LinkedHashSet<>(parser.getConfigurationClasses());
        configClasses.removeAll(alreadyParsed);

        // Read the model and create bean definitions based on its content
        if (this.reader == null) {
            this.reader = new ConfigurationClassBeanDefinitionReader(
                    registry, this.sourceExtractor, this.resourceLoader, this.environment,
                    this.importBeanNameGenerator, parser.getImportRegistry());
        }
        this.reader.loadBeanDefinitions(configClasses);
        for (ConfigurationClass configClass : configClasses) {
            this.beanRegistrars.addAll(configClass.getBeanRegistrars());
        }
        alreadyParsed.addAll(configClasses);
        processConfig.tag("classCount", () -> String.valueOf(configClasses.size())).end();

        candidates.clear();
        if (registry.getBeanDefinitionCount() > candidateNames.length) {
            String[] newCandidateNames = registry.getBeanDefinitionNames();
            Set<String> oldCandidateNames = Set.of(candidateNames);
            Set<String> alreadyParsedClasses = CollectionUtils.newHashSet(alreadyParsed.size());
            for (ConfigurationClass configurationClass : alreadyParsed) {
                alreadyParsedClasses.add(configurationClass.getMetadata().getClassName());
            }
            for (String candidateName : newCandidateNames) {
                if (!oldCandidateNames.contains(candidateName)) {
                    BeanDefinition bd = registry.getBeanDefinition(candidateName);
                    if (ConfigurationClassUtils.checkConfigurationClassCandidate(bd, this.metadataReaderFactory) &&
                            !alreadyParsedClasses.contains(bd.getBeanClassName())) {
                        candidates.add(new BeanDefinitionHolder(bd, candidateName));
                    }
                }
            }
            candidateNames = newCandidateNames;
        }
    }
    while (!candidates.isEmpty());

    // Register the ImportRegistry as a bean in order to support ImportAware @Configuration classes
    if (singletonRegistry != null && !singletonRegistry.containsSingleton(IMPORT_REGISTRY_BEAN_NAME)) {
        singletonRegistry.registerSingleton(IMPORT_REGISTRY_BEAN_NAME, parser.getImportRegistry());
    }

    // Store the PropertySourceDescriptors to contribute them Ahead-of-time if necessary
    this.propertySourceDescriptors = parser.getPropertySourceDescriptors();

    if (this.metadataReaderFactory instanceof CachingMetadataReaderFactory cachingMetadataReaderFactory) {
        // Clear cache in externally provided MetadataReaderFactory; this is a no-op
        // for a shared cache since it'll be cleared by the ApplicationContext.
        cachingMetadataReaderFactory.clearCache();
    }
}
```

## 후보 판정과 full / lite

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassUtils.java` L106-L165 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassUtils.java#L106-L165))

```java
// ConfigurationClassUtils.java L106-L165
static boolean checkConfigurationClassCandidate(
        BeanDefinition beanDef, MetadataReaderFactory metadataReaderFactory) {

    String className = beanDef.getBeanClassName();
    if (className == null || beanDef.getFactoryMethodName() != null) {
        return false;
    }

    AnnotationMetadata metadata;
    if (beanDef instanceof AnnotatedBeanDefinition annotatedBd &&
            className.equals(annotatedBd.getMetadata().getClassName())) {
        // Can reuse the pre-parsed metadata from the given BeanDefinition...
        metadata = annotatedBd.getMetadata();
    }
    else if (beanDef instanceof AbstractBeanDefinition abstractBd && abstractBd.hasBeanClass()) {
        // Check already loaded Class if present...
        // since we possibly can't even load the class file for this Class.
        Class<?> beanClass = abstractBd.getBeanClass();
        if (BeanFactoryPostProcessor.class.isAssignableFrom(beanClass) ||
                BeanPostProcessor.class.isAssignableFrom(beanClass) ||
                AopInfrastructureBean.class.isAssignableFrom(beanClass) ||
                EventListenerFactory.class.isAssignableFrom(beanClass)) {
            return false;
        }
        metadata = AnnotationMetadata.introspect(beanClass);
    }
    else {
        try {
            MetadataReader metadataReader = metadataReaderFactory.getMetadataReader(className);
            metadata = metadataReader.getAnnotationMetadata();
        }
        catch (IOException ex) {
            if (logger.isDebugEnabled()) {
                logger.debug("Could not find class file for introspecting configuration annotations: " +
                        className, ex);
            }
            return false;
        }
    }

    Map<String, @Nullable Object> config = metadata.getAnnotationAttributes(Configuration.class.getName());
    if (config != null && !Boolean.FALSE.equals(config.get("proxyBeanMethods"))) {
        beanDef.setAttribute(CONFIGURATION_CLASS_ATTRIBUTE, CONFIGURATION_CLASS_FULL);
    }
    else if (config != null || Boolean.TRUE.equals(beanDef.getAttribute(CANDIDATE_ATTRIBUTE)) ||
            isConfigurationCandidate(metadata)) {
        beanDef.setAttribute(CONFIGURATION_CLASS_ATTRIBUTE, CONFIGURATION_CLASS_LITE);
    }
    else {
        return false;
    }

    // It's a full or lite configuration candidate... Let's determine the order value, if any.
    Integer order = getOrder(metadata);
    if (order != null) {
        beanDef.setAttribute(ORDER_ATTRIBUTE, order);
    }

    return true;
}
```

```text
 checkConfigurationClassCandidate(beanDef)
 |
 +-- 클래스 이름 없음 / 팩토리 메서드로 만드는 정의 (@Bean 결과)   --> 후보 아님
 +-- 클래스가 이미 로드된 정의이고 그 클래스가
 |   BeanFactoryPostProcessor, BeanPostProcessor, AopInfrastructureBean, EventListenerFactory 구현
 |                                                             --> 후보 아님   (L124-L128)
 +-- @Configuration 있고 proxyBeanMethods != false   --> FULL  (나중에 CGLIB 강화 대상)
 +-- @Configuration(proxyBeanMethods=false)
 |   또는 @Component / @ComponentScan / @Import / @ImportResource
 |   또는 @Bean 메서드가 하나라도 있음                  --> LITE  (강화 없음)
 +-- 그 밖                                             --> 후보 아님
 +-- 후보면 @Order 값을 정의 속성에 기록
```

## 동작 흐름

```text
 processConfigBeanDefinitions(registry)
 |
 | L391-L403 등록된 모든 정의를 훑어 후보 수집
 |            이미 FULL/LITE 표시가 있으면 건너뜀 (이전에 처리됨)
 | L406      후보 없음 --> return
 | L411      @Order 값으로 정렬
 | L418-L437 컨텍스트가 지정한 BeanNameGenerator 가 있으면 채택
 |
 | L444 parser = new ConfigurationClassParser(...)
 |
 | do {                                                             L450
 |   L452 parser.parse(candidates)          후보 -> ConfigurationClass 모델
 |          @ComponentScan 은 여기서 즉시 스캔 + 스캔 결과 정의 등록
 |   L453 parser.validate()                 규칙 위반 검사 (ConfigurationClass L245)
 |          프록시가 필요한 @Configuration 이 final / @Bean 메서드 규칙 / 같은 이름 @Bean 오버로딩
 |   L455 configClasses = 파싱된 모델 - 이미 처리한 것
 |   L464 reader.loadBeanDefinitions(configClasses)
 |          @Bean, @Import 된 설정, @ImportResource, Registrar -> 빈 정의 등록
 |   L472 정의 개수가 늘었으면
 |          새로 생긴 정의 중 후보이면서 아직 파싱 안 한 클래스 --> candidates
 | } while (candidates 비어 있지 않음)                                L491
 |
 | L494 ImportRegistry 를 싱글톤으로 등록     ImportAware 지원용
 | L499 @PropertySource 기술자 보관           AOT 용
 +-- L501 메타데이터 리더 캐시 비우기
```

1. [ConfigurationClassParser.parse](01_ConfigurationClassParser.parse/README.md)가 설정 클래스를 읽어 `ConfigurationClass` 모델을 만든다.
2. [ConfigurationClassBeanDefinitionReader.loadBeanDefinitions](02_ConfigurationClassBeanDefinitionReader.loadBeanDefinitions/README.md)가 모델을 빈 정의로 바꿔 등록한다.

## 결과가 쓰이는 곳

```text
 정의 속성 CONFIGURATION_CLASS_ATTRIBUTE = full | lite
      --> enhanceConfigurationClasses 가 full 만 CGLIB 강화
      --> 다음 반복/다음 호출에서 "이미 처리됨" 판정

 새로 등록된 빈 정의
      +-- @ComponentScan 결과 (ScannedGenericBeanDefinition)
      +-- @Bean 메서드 (ConfigurationClassBeanDefinition, factoryMethod 기반)
      +-- @Import 한 설정 클래스 자신
      --> PostProcessorRegistrationDelegate 1부 [c][d] 에서 새 Registry 처리기 탐색 대상
      --> preInstantiateSingletons 에서 인스턴스화

 ImportRegistry 싱글톤
      --> ImportAwareBeanPostProcessor 가 ImportAware 빈에 "나를 import 한 클래스의 메타데이터" 주입
          (@EnableXxx 의 속성을 읽는 방법)
```

## 하위 메서드

- [01 ConfigurationClassParser.parse](01_ConfigurationClassParser.parse/README.md)
- [02 ConfigurationClassBeanDefinitionReader.loadBeanDefinitions](02_ConfigurationClassBeanDefinitionReader.loadBeanDefinitions/README.md)
