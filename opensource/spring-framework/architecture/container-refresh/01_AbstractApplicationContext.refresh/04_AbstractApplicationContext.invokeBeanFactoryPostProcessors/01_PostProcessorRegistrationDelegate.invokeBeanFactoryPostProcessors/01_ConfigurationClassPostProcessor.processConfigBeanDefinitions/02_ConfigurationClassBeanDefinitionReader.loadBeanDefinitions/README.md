# ConfigurationClassBeanDefinitionReader.loadBeanDefinitions

상위: [ConfigurationClassPostProcessor.processConfigBeanDefinitions](../README.md)

파서가 만든 `ConfigurationClass` 모델을 실제 빈 정의로 바꿔 레지스트리에 넣는다. `@Bean` 메서드 하나는 "이 설정 빈의 이 메서드를 호출해 만든다"는 **팩토리 메서드 정의** 하나가 된다.

## 실제 코드

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassBeanDefinitionReader.java` L121-L126 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassBeanDefinitionReader.java#L121-L126))

```java
// ConfigurationClassBeanDefinitionReader.java L121-L126
public void loadBeanDefinitions(Set<ConfigurationClass> configurationModel) {
    TrackedConditionEvaluator trackedConditionEvaluator = new TrackedConditionEvaluator();
    for (ConfigurationClass configClass : configurationModel) {
        loadBeanDefinitionsForConfigurationClass(configClass, trackedConditionEvaluator);
    }
}
```

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassBeanDefinitionReader.java` L132-L154 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassBeanDefinitionReader.java#L132-L154))

```java
// ConfigurationClassBeanDefinitionReader.java L132-L154
private void loadBeanDefinitionsForConfigurationClass(
        ConfigurationClass configClass, TrackedConditionEvaluator trackedConditionEvaluator) {

    if (trackedConditionEvaluator.shouldSkip(configClass)) {
        String beanName = configClass.getBeanName();
        if (StringUtils.hasLength(beanName) && this.registry.containsBeanDefinition(beanName)) {
            this.registry.removeBeanDefinition(beanName);
        }
        this.importRegistry.removeImportingClass(configClass.getMetadata().getClassName());
        return;
    }

    if (configClass.isImported()) {
        registerBeanDefinitionForImportedConfigurationClass(configClass);
    }
    for (BeanMethod beanMethod : configClass.getBeanMethods()) {
        loadBeanDefinitionsForBeanMethod(beanMethod);
    }

    loadBeanDefinitionsFromImportedResources(configClass.getImportedResources());
    loadBeanDefinitionsFromImportBeanDefinitionRegistrars(configClass.getImportBeanDefinitionRegistrars());
    loadBeanDefinitionsFromBeanRegistrars(configClass.getBeanRegistrars());
}
```

`@Bean` 메서드 하나를 정의로 바꾸는 부분이다.

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassBeanDefinitionReader.java` L190-L315 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassBeanDefinitionReader.java#L190-L315))

```java
// ConfigurationClassBeanDefinitionReader.java L190-L315
private void loadBeanDefinitionsForBeanMethod(BeanMethod beanMethod) {
    ConfigurationClass configClass = beanMethod.getConfigurationClass();
    MethodMetadata metadata = beanMethod.getMetadata();
    String methodName = metadata.getMethodName();

    // Do we need to mark the bean as skipped by its condition?
    if (this.conditionEvaluator.shouldSkip(metadata, ConfigurationPhase.REGISTER_BEAN)) {
        configClass.skippedBeanMethods.add(methodName);
        return;
    }
    if (configClass.skippedBeanMethods.contains(methodName)) {
        return;
    }

    AnnotationAttributes bean = AnnotationConfigUtils.attributesFor(metadata, Bean.class);
    Assert.state(bean != null, "No @Bean annotation attributes");

    // Consider name and any aliases.
    String[] explicitNames = bean.getStringArray("name");
    String beanName = (explicitNames.length > 0 && StringUtils.hasText(explicitNames[0])) ? explicitNames[0] : null;
    String localBeanName = defaultBeanName(beanName, methodName);
    beanName = (this.importBeanNameGenerator instanceof ConfigurationBeanNameGenerator cbng ?
            cbng.deriveBeanName(metadata, beanName) : localBeanName);
    if (!localBeanName.equals(beanName) && !this.registry.containsBeanDefinition(localBeanName) &&
            !this.registry.isAlias(localBeanName)) {
        // Register original name as alias unless registered already.
        this.registry.registerAlias(beanName, localBeanName);
    }
    if (explicitNames.length > 0) {
        // Register aliases even when overridden below.
        for (int i = 1; i < explicitNames.length; i++) {
            this.registry.registerAlias(beanName, explicitNames[i]);
        }
    }

    ConfigurationClassBeanDefinition beanDef =
            new ConfigurationClassBeanDefinition(configClass, metadata, localBeanName);
    beanDef.setSource(this.sourceExtractor.extractSource(metadata, configClass.getResource()));

    // Has this effectively been overridden before (for example, via XML)?
    if (isOverriddenByExistingDefinition(beanMethod, beanName, beanDef)) {
        if (beanName.equals(beanMethod.getConfigurationClass().getBeanName())) {
            throw new BeanDefinitionStoreException(beanMethod.getConfigurationClass().getResource().getDescription(),
                    beanName, "Bean name derived from @Bean method '" + beanMethod.getMetadata().getMethodName() +
                    "' clashes with bean name for containing configuration class; please make those names unique!");
        }
        return;
    }

    if (metadata.isStatic()) {
        // static @Bean method
        if (configClass.getMetadata() instanceof StandardAnnotationMetadata sam) {
            beanDef.setBeanClass(sam.getIntrospectedClass());
        }
        else {
            beanDef.setBeanClassName(configClass.getMetadata().getClassName());
        }
        beanDef.setUniqueFactoryMethodName(methodName);
    }
    else {
        // instance @Bean method
        beanDef.setFactoryBeanName(configClass.getBeanName());
        beanDef.setUniqueFactoryMethodName(methodName);
    }

    if (metadata instanceof StandardMethodMetadata smm &&
            configClass.getMetadata() instanceof StandardAnnotationMetadata sam) {
        Method method = ClassUtils.getMostSpecificMethod(smm.getIntrospectedMethod(), sam.getIntrospectedClass());
        if (method == smm.getIntrospectedMethod()) {
            beanDef.setResolvedFactoryMethod(method);
        }
    }

    beanDef.setAutowireMode(AbstractBeanDefinition.AUTOWIRE_CONSTRUCTOR);
    AnnotationConfigUtils.processCommonDefinitionAnnotations(beanDef, metadata);

    boolean autowireCandidate = bean.getBoolean("autowireCandidate");
    if (!autowireCandidate) {
        beanDef.setAutowireCandidate(false);
    }

    boolean defaultCandidate = bean.getBoolean("defaultCandidate");
    if (!defaultCandidate) {
        beanDef.setDefaultCandidate(false);
    }

    Bean.Bootstrap instantiation = bean.getEnum("bootstrap");
    if (instantiation == Bean.Bootstrap.BACKGROUND) {
        beanDef.setBackgroundInit(true);
    }

    String initMethodName = bean.getString("initMethod");
    if (StringUtils.hasText(initMethodName)) {
        beanDef.setInitMethodName(initMethodName);
    }

    String destroyMethodName = bean.getString("destroyMethod");
    beanDef.setDestroyMethodName(destroyMethodName);

    // Consider scoping
    ScopedProxyMode proxyMode = ScopedProxyMode.NO;
    AnnotationAttributes attributes = AnnotationConfigUtils.attributesFor(metadata, Scope.class);
    if (attributes != null) {
        beanDef.setScope(attributes.getString("value"));
        proxyMode = attributes.getEnum("proxyMode");
        if (proxyMode == ScopedProxyMode.DEFAULT) {
            proxyMode = ScopedProxyMode.NO;
        }
    }

    // Replace the original bean definition with the target one, if necessary
    BeanDefinition beanDefToRegister = beanDef;
    if (proxyMode != ScopedProxyMode.NO) {
        BeanDefinitionHolder proxyDef = ScopedProxyCreator.createScopedProxy(
                new BeanDefinitionHolder(beanDef, beanName), this.registry,
                proxyMode == ScopedProxyMode.TARGET_CLASS);
        beanDefToRegister = new ConfigurationClassBeanDefinition(
                (RootBeanDefinition) proxyDef.getBeanDefinition(), configClass, metadata, localBeanName);
    }

    if (logger.isTraceEnabled()) {
        logger.trace("Registering bean definition for @Bean method %s.%s() with bean name '%s'"
                .formatted(configClass.getMetadata().getClassName(), methodName, beanName));
    }
    this.registry.registerBeanDefinition(beanName, beanDefToRegister);
}
```

## 동작 흐름

```text
 loadBeanDefinitions(configClasses)
 |
 +-- for configClass
       loadBeanDefinitionsForConfigurationClass(configClass, trackedConditionEvaluator)
       |
       | L135 @Conditional (REGISTER_BEAN 단계) 불만족
       |        또는 이 클래스를 import 한 클래스가 모두 건너뛰어짐
       |        --> 이미 있는 정의 제거, import 기록 제거, return
       |
       | L144 import 로 들어온 설정 클래스 --> 그 클래스 자신의 정의 등록
       |
       | L147 for beanMethod --> loadBeanDefinitionsForBeanMethod
       |
       | L151 @ImportResource            --> XML 등 리더로 읽어 등록
       | L152 ImportBeanDefinitionRegistrar --> registerBeanDefinitions(메타데이터, registry)
       +-- L153 BeanRegistrar              --> 등록 호출

 loadBeanDefinitionsForBeanMethod(beanMethod)
 |
 | L196 메서드의 @Conditional 불만족 --> 건너뜀 (이름을 기록해 오버로드도 건너뜀)
 |
 | L208-L223 이름 결정
 |        @Bean(name) 첫 값 또는 메서드 이름, 나머지 이름은 별칭
 |
 | L225 new ConfigurationClassBeanDefinition(configClass, 메서드 메타데이터)
 |
 | L230 같은 이름의 정의가 이미 있고 그것을 우선해야 하면 (XML 정의 등) --> 건너뜀
 |        이름이 설정 클래스 빈 이름과 같으면 --> BeanDefinitionStoreException
 |
 +-- L239 static @Bean
 |        beanClass = 설정 클래스, factoryMethodName = 메서드 이름
 |        --> 설정 클래스 인스턴스 없이 정적 호출
 |
 +-- L249 인스턴스 @Bean
          factoryBeanName = 설정 클래스 빈 이름, factoryMethodName = 메서드 이름
          --> 설정 빈을 먼저 만든 뒤 그 인스턴스의 메서드 호출

   이어서 L263 autowire 모드 = 생성자 주입 (@Bean 메서드 파라미터가 자동 주입되는 이유)
          L264 @Lazy / @Primary / @Fallback / @DependsOn / @Role / @Description 을 정의에 옮김
          L266-L287 autowireCandidate, initMethod, destroyMethod
          L290 이후 @Scope 와 scoped proxy 처리 --> registry.registerBeanDefinition
```

## 결과가 쓰이는 곳

```text
 @Bean 정의의 factoryBeanName / factoryMethodName
      --> 빈 생성 흐름의 instantiateUsingFactoryMethod
          인스턴스 @Bean : getBean(설정 클래스) --> 그 객체.메서드(인자 자동 주입)
          static @Bean   : 설정 클래스.메서드(...)  -- 설정 클래스 인스턴스를 만들지 않음
      --> 설정 클래스가 FULL(CGLIB) 이면 "그 객체" 가 강화된 하위 클래스이므로
          @Bean 메서드끼리의 호출이 컨테이너의 싱글톤으로 돌아온다 (enhanceConfigurationClasses)

 registrar 가 추가한 정의
      --> processConfigBeanDefinitions L472 "정의 개수가 늘었나" 검사에 잡혀
          설정 후보면 다음 반복에서 파싱됨
```
