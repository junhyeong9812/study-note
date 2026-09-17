# ConfigurationClassPostProcessor.enhanceConfigurationClasses

상위: [PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors](../README.md)

`@Configuration`(full) 클래스의 빈 정의에서 클래스를 **CGLIB 하위 클래스로 바꿔 끼운다.** 이 하위 클래스는 `@Bean` 메서드 호출을 가로채 컨테이너의 싱글톤을 돌려주므로, 설정 클래스 안에서 `@Bean` 메서드를 서로 불러도 객체가 새로 만들어지지 않는다.

## 진입: postProcessBeanFactory

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassPostProcessor.java` L324-L339 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassPostProcessor.java#L324-L339))

```java
// ConfigurationClassPostProcessor.java L324-L339
public void postProcessBeanFactory(ConfigurableListableBeanFactory beanFactory) {
    int factoryId = System.identityHashCode(beanFactory);
    if (this.factoriesPostProcessed.contains(factoryId)) {
        throw new IllegalStateException(
                "postProcessBeanFactory already called on this post-processor against " + beanFactory);
    }
    this.factoriesPostProcessed.add(factoryId);
    if (!this.registriesPostProcessed.contains(factoryId)) {
        // BeanDefinitionRegistryPostProcessor hook apparently not supported...
        // Simply call processConfigurationClasses lazily at this point then.
        processConfigBeanDefinitions((BeanDefinitionRegistry) beanFactory);
    }

    enhanceConfigurationClasses(beanFactory);
    beanFactory.addBeanPostProcessor(new ImportAwareBeanPostProcessor(beanFactory));
}
```

## 실제 코드

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassPostProcessor.java` L514-L586 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassPostProcessor.java#L514-L586))

```java
// ConfigurationClassPostProcessor.java L514-L586
public void enhanceConfigurationClasses(ConfigurableListableBeanFactory beanFactory) {
    StartupStep enhanceConfigClasses = this.applicationStartup.start("spring.context.config-classes.enhance");
    Map<String, AbstractBeanDefinition> configBeanDefs = new LinkedHashMap<>();
    for (String beanName : beanFactory.getBeanDefinitionNames()) {
        BeanDefinition beanDef = beanFactory.getBeanDefinition(beanName);
        Object configClassAttr = beanDef.getAttribute(ConfigurationClassUtils.CONFIGURATION_CLASS_ATTRIBUTE);
        AnnotationMetadata annotationMetadata = null;
        MethodMetadata methodMetadata = null;
        if (beanDef instanceof AnnotatedBeanDefinition annotatedBeanDefinition) {
            annotationMetadata = annotatedBeanDefinition.getMetadata();
            methodMetadata = annotatedBeanDefinition.getFactoryMethodMetadata();
        }
        if ((configClassAttr != null || methodMetadata != null) &&
                (beanDef instanceof AbstractBeanDefinition abd) && !abd.hasBeanClass()) {
            // Configuration class (full or lite) or a configuration-derived @Bean method
            // -> eagerly resolve bean class at this point, unless it's a 'lite' configuration
            // or component class without @Bean methods.
            boolean liteConfigurationCandidateWithoutBeanMethods =
                    (ConfigurationClassUtils.CONFIGURATION_CLASS_LITE.equals(configClassAttr) &&
                        annotationMetadata != null && !ConfigurationClassUtils.hasBeanMethods(annotationMetadata));
            if (!liteConfigurationCandidateWithoutBeanMethods) {
                try {
                    abd.resolveBeanClass(this.beanClassLoader);
                }
                catch (Throwable ex) {
                    throw new IllegalStateException(
                            "Cannot load configuration class: " + beanDef.getBeanClassName(), ex);
                }
            }
        }
        if (ConfigurationClassUtils.CONFIGURATION_CLASS_FULL.equals(configClassAttr)) {
            if (!(beanDef instanceof AbstractBeanDefinition abd)) {
                throw new BeanDefinitionStoreException("Cannot enhance @Configuration bean definition '" +
                        beanName + "' since it is not stored in an AbstractBeanDefinition subclass");
            }
            else if (beanFactory.containsSingleton(beanName)) {
                if (logger.isWarnEnabled()) {
                    logger.warn("Cannot enhance @Configuration bean definition '" + beanName +
                            "' since its singleton instance has been created too early. The typical cause " +
                            "is a non-static @Bean method with a BeanDefinitionRegistryPostProcessor " +
                            "return type: Consider declaring such methods as 'static' and/or marking the " +
                            "containing configuration class as 'proxyBeanMethods=false'.");
                }
            }
            else {
                configBeanDefs.put(beanName, abd);
            }
        }
    }
    if (configBeanDefs.isEmpty()) {
        // nothing to enhance -> return immediately
        enhanceConfigClasses.end();
        return;
    }

    ConfigurationClassEnhancer enhancer = new ConfigurationClassEnhancer();
    for (Map.Entry<String, AbstractBeanDefinition> entry : configBeanDefs.entrySet()) {
        AbstractBeanDefinition beanDef = entry.getValue();
        // If a @Configuration class gets proxied, always proxy the target class
        beanDef.setAttribute(AutoProxyUtils.PRESERVE_TARGET_CLASS_ATTRIBUTE, Boolean.TRUE);
        // Set enhanced subclass of the user-specified bean class
        Class<?> configClass = beanDef.getBeanClass();
        Class<?> enhancedClass = enhancer.enhance(configClass, this.beanClassLoader);
        if (configClass != enhancedClass) {
            if (logger.isTraceEnabled()) {
                logger.trace(String.format("Replacing bean definition '%s' existing class '%s' with " +
                        "enhanced class '%s'", entry.getKey(), configClass.getName(), enhancedClass.getName()));
            }
            beanDef.setBeanClass(enhancedClass);
        }
    }
    enhanceConfigClasses.tag("classCount", () -> String.valueOf(configBeanDefs.keySet().size())).end();
}
```

## 동작 흐름

```text
 postProcessBeanFactory(beanFactory)             (Registry 처리기 1부 [e] 에서 호출)
 |
 | 같은 팩토리에 두 번 호출 --> IllegalStateException
 | Registry 콜백을 받은 적 없음 (Registry 가 아닌 팩토리) --> 여기서 processConfigBeanDefinitions
 |
 +-- enhanceConfigurationClasses(beanFactory)
 +-- addBeanPostProcessor(ImportAwareBeanPostProcessor)   ImportAware 주입 + 강화 클래스에 BeanFactory 주입

 enhanceConfigurationClasses(beanFactory)
 |
 +-- for 모든 정의                                                 L517-L562
 |     full/lite 설정이거나 @Bean 정의인데 클래스가 아직 로드 안 됨
 |       --> 여기서 클래스 로드 (메서드가 없는 lite 는 제외)
 |     full 인가?
 |       AbstractBeanDefinition 이 아님     --> 오류
 |       이미 싱글톤이 만들어져 있음        --> 경고 로그만 (강화 불가)
 |         흔한 원인: non-static @Bean 이 BeanDefinitionRegistryPostProcessor 를 반환
 |       그 밖                              --> 강화 대상 목록에 추가
 |
 +-- 대상 없음 --> return
 |
 +-- for 대상                                                      L570-L584
       PRESERVE_TARGET_CLASS = true    나중에 AOP 프록시가 붙어도 클래스 기반 프록시로
       enhancedClass = ConfigurationClassEnhancer.enhance(원래 클래스)
       다르면 beanDef.setBeanClass(enhancedClass)      <-- 정의의 클래스 교체
```

```text
 @Configuration
 class AppConfig {
     @Bean A a() { return new A(b()); }     b() 호출이
     @Bean B b() { return new B(); }
 }

 FULL (CGLIB 강화)                         LITE (proxyBeanMethods = false, 또는 @Component)
   AppConfig$$SpringCGLIB$$0 가 실제 인스턴스   AppConfig 그대로
   b() 호출 --> 인터셉터 --> getBean("b")       b() 호출 --> 그냥 new B()
   = 컨테이너의 싱글톤 B                       = 컨테이너의 B 와 다른 새 객체
```

## 결과가 쓰이는 곳

```text
 교체된 beanClass (AppConfig$$SpringCGLIB$$0)
      --> preInstantiateSingletons --> 빈 생성 흐름이 이 하위 클래스를 인스턴스화
      --> 인스턴스 @Bean 정의들의 factoryBean 이 이 강화 객체가 됨

 ImportAwareBeanPostProcessor
      --> 강화 클래스(EnhancedConfiguration) 에 BeanFactory 주입
          인터셉터가 getBean 을 호출할 수 있게 하는 연결 고리
      --> ImportAware 빈에 import 메타데이터 주입

 경고 로그 ("singleton instance has been created too early")
      --> 강화가 빠져 FULL 인데도 LITE 처럼 동작하는 상태 --> @Bean 간 호출이 새 객체를 만든다
```
