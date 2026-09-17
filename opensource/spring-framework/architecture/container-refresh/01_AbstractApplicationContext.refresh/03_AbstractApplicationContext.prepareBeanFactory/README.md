# AbstractApplicationContext.prepareBeanFactory

상위: [AbstractApplicationContext.refresh](../README.md)

순수한 빈 팩토리를 "애플리케이션 컨텍스트의 팩토리"로 만든다. `*Aware` 콜백을 처리할 후처리기를 붙이고, `ApplicationContext`나 `ResourceLoader`를 주입받을 수 있게 등록하고, `environment` 같은 기본 싱글톤을 넣는다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L730-L776 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L730-L776))

```java
// AbstractApplicationContext.java L730-L776
protected void prepareBeanFactory(ConfigurableListableBeanFactory beanFactory) {
    // Tell the internal bean factory to use the context's class loader etc.
    beanFactory.setBeanClassLoader(getClassLoader());
    beanFactory.setBeanExpressionResolver(new StandardBeanExpressionResolver(beanFactory.getBeanClassLoader()));
    beanFactory.addPropertyEditorRegistrar(new ResourceEditorRegistrar(this, getEnvironment()));

    // Configure the bean factory with context callbacks.
    beanFactory.addBeanPostProcessor(new ApplicationContextAwareProcessor(this));
    beanFactory.ignoreDependencyInterface(EnvironmentAware.class);
    beanFactory.ignoreDependencyInterface(EmbeddedValueResolverAware.class);
    beanFactory.ignoreDependencyInterface(ResourceLoaderAware.class);
    beanFactory.ignoreDependencyInterface(ApplicationEventPublisherAware.class);
    beanFactory.ignoreDependencyInterface(MessageSourceAware.class);
    beanFactory.ignoreDependencyInterface(ApplicationContextAware.class);
    beanFactory.ignoreDependencyInterface(ApplicationStartupAware.class);

    // BeanFactory interface not registered as resolvable type in a plain factory.
    // MessageSource registered (and found for autowiring) as a bean.
    beanFactory.registerResolvableDependency(BeanFactory.class, beanFactory);
    beanFactory.registerResolvableDependency(ResourceLoader.class, this);
    beanFactory.registerResolvableDependency(ApplicationEventPublisher.class, this);
    beanFactory.registerResolvableDependency(ApplicationContext.class, this);

    // Register early post-processor for detecting inner beans as ApplicationListeners.
    beanFactory.addBeanPostProcessor(new ApplicationListenerDetector(this));

    // Detect a LoadTimeWeaver and prepare for weaving, if found.
    if (!NativeDetector.inNativeImage() && beanFactory.containsBean(LOAD_TIME_WEAVER_BEAN_NAME)) {
        beanFactory.addBeanPostProcessor(new LoadTimeWeaverAwareProcessor(beanFactory));
        // Set a temporary ClassLoader for type matching.
        beanFactory.setTempClassLoader(new ContextTypeMatchClassLoader(beanFactory.getBeanClassLoader()));
    }

    // Register default environment beans.
    if (!beanFactory.containsLocalBean(ENVIRONMENT_BEAN_NAME)) {
        beanFactory.registerSingleton(ENVIRONMENT_BEAN_NAME, getEnvironment());
    }
    if (!beanFactory.containsLocalBean(SYSTEM_PROPERTIES_BEAN_NAME)) {
        beanFactory.registerSingleton(SYSTEM_PROPERTIES_BEAN_NAME, getEnvironment().getSystemProperties());
    }
    if (!beanFactory.containsLocalBean(SYSTEM_ENVIRONMENT_BEAN_NAME)) {
        beanFactory.registerSingleton(SYSTEM_ENVIRONMENT_BEAN_NAME, getEnvironment().getSystemEnvironment());
    }
    if (!beanFactory.containsLocalBean(APPLICATION_STARTUP_BEAN_NAME)) {
        beanFactory.registerSingleton(APPLICATION_STARTUP_BEAN_NAME, getApplicationStartup());
    }
}
```

## 동작 흐름

```text
 prepareBeanFactory(beanFactory)
 |
 | [1] 기본 도구                                                   L732-L734
 |     클래스로더 = 컨텍스트 클래스로더
 |     StandardBeanExpressionResolver     #{...} SpEL 을 @Value 등에서 평가
 |     ResourceEditorRegistrar            "classpath:x.xml" 문자열 -> Resource 변환
 |
 | [2] Aware 처리                                                  L737-L744
 |     addBeanPostProcessor(ApplicationContextAwareProcessor)
 |       빈 초기화 직전에 EnvironmentAware, ResourceLoaderAware,
 |       ApplicationEventPublisherAware, MessageSourceAware, ApplicationContextAware ... 콜백 호출
 |     ignoreDependencyInterface(위 Aware 7종)
 |       setter 자동 주입 대상에서 제외 (콜백으로만 채워지게)
 |
 | [3] 빈이 아닌 주입 대상                                          L748-L751
 |     registerResolvableDependency
 |       BeanFactory               --> 이 팩토리
 |       ResourceLoader            --> 이 컨텍스트
 |       ApplicationEventPublisher --> 이 컨텍스트
 |       ApplicationContext        --> 이 컨텍스트
 |
 | [4] addBeanPostProcessor(ApplicationListenerDetector)          L754
 |       빈으로 만들어진 ApplicationListener 를 멀티캐스터에 붙임 (내부 빈 포함)
 |
 | [5] loadTimeWeaver 빈이 있으면 (네이티브 이미지 제외)            L757-L761
 |       LoadTimeWeaverAwareProcessor + 타입 매칭용 임시 클래스로더
 |
 | [6] 기본 싱글톤 (없을 때만)                                      L764-L775
 |       environment, systemProperties, systemEnvironment, applicationStartup
```

## 결과가 쓰이는 곳

```text
 ApplicationContextAwareProcessor
      --> 빈 생성 흐름의 초기화 단계 (postProcessBeforeInitialization)
          implements ApplicationContextAware 인 빈의 setApplicationContext() 호출

 registerResolvableDependency 로 등록한 4종
      --> @Autowired ApplicationContext ctx 같은 주입 해석
          DefaultListableBeanFactory.findAutowireCandidates 가 빈 목록보다 먼저 이 표를 본다
          = ApplicationContext 는 빈으로 등록되어 있지 않은데도 주입된다

 environment 싱글톤
      --> @Autowired Environment env
      --> finishBeanFactoryInitialization 의 기본 값 해석기
          ${...} 플레이스홀더를 environment 로 해석

 ApplicationListenerDetector (여기서 1번째 등록)
      --> registerBeanPostProcessors 마지막에 다시 등록되어 체인 맨 끝으로 이동
          (프록시가 씌워진 뒤의 리스너 객체를 붙이기 위해)
```

[registerBeanPostProcessors](../05_AbstractApplicationContext.registerBeanPostProcessors/README.md)가 이 처리기들 뒤에 사용자 처리기를 잇는다.
