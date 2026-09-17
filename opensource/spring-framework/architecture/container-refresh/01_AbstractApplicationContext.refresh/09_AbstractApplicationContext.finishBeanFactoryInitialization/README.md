# AbstractApplicationContext.finishBeanFactoryInitialization

상위: [AbstractApplicationContext.refresh](../README.md)

남은 싱글톤을 모두 만들기 직전에 팩토리 설정을 마무리한다. 변환 서비스와 기본 값 해석기를 넣고, 먼저 만들어야 할 빈을 만들고, 빈 정의를 **동결**한 뒤, 싱글톤 생성을 시작한다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L943-L996 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L943-L996))

```java
// AbstractApplicationContext.java L943-L996
protected void finishBeanFactoryInitialization(ConfigurableListableBeanFactory beanFactory) {
    // Mark current thread for singleton instantiation with applied bootstrap locking.
    beanFactory.prepareSingletonBootstrap();

    // Initialize bootstrap executor for this context.
    if (beanFactory.containsBean(BOOTSTRAP_EXECUTOR_BEAN_NAME) &&
            beanFactory.isTypeMatch(BOOTSTRAP_EXECUTOR_BEAN_NAME, Executor.class)) {
        beanFactory.setBootstrapExecutor(
                beanFactory.getBean(BOOTSTRAP_EXECUTOR_BEAN_NAME, Executor.class));
    }

    // Initialize conversion service for this context.
    if (beanFactory.containsBean(CONVERSION_SERVICE_BEAN_NAME) &&
            beanFactory.isTypeMatch(CONVERSION_SERVICE_BEAN_NAME, ConversionService.class)) {
        beanFactory.setConversionService(
                beanFactory.getBean(CONVERSION_SERVICE_BEAN_NAME, ConversionService.class));
    }

    // Register a default embedded value resolver if no BeanFactoryPostProcessor
    // (such as a PropertySourcesPlaceholderConfigurer bean) registered any before:
    // at this point, primarily for resolution in annotation attribute values.
    if (!beanFactory.hasEmbeddedValueResolver()) {
        beanFactory.addEmbeddedValueResolver(strVal -> getEnvironment().resolvePlaceholders(strVal));
    }

    // Call BeanFactoryInitializer beans early to allow for initializing specific other beans early.
    String[] initializerNames = beanFactory.getBeanNamesForType(BeanFactoryInitializer.class, false, false);
    for (String initializerName : initializerNames) {
        beanFactory.getBean(initializerName, BeanFactoryInitializer.class).initialize(beanFactory);
    }

    // Initialize LoadTimeWeaverAware beans early to allow for registering their transformers early.
    String[] weaverAwareNames = beanFactory.getBeanNamesForType(LoadTimeWeaverAware.class, false, false);
    for (String weaverAwareName : weaverAwareNames) {
        try {
            beanFactory.getBean(weaverAwareName, LoadTimeWeaverAware.class);
        }
        catch (BeanNotOfRequiredTypeException ex) {
            if (logger.isDebugEnabled()) {
                logger.debug("Failed to initialize LoadTimeWeaverAware bean '" + weaverAwareName +
                        "' due to unexpected type mismatch: " + ex.getMessage());
            }
        }
    }

    // Stop using the temporary ClassLoader for type matching.
    beanFactory.setTempClassLoader(null);

    // Allow for caching all bean definition metadata, not expecting further changes.
    beanFactory.freezeConfiguration();

    // Instantiate all remaining (non-lazy-init) singletons.
    beanFactory.preInstantiateSingletons();
}
```

## 동작 흐름

```text
 finishBeanFactoryInitialization(beanFactory)
 |
 | L945 prepareSingletonBootstrap()       메인 스레드 이름 접두어를 기록 (DLBF L1097)
 |                                       싱글톤 잠금 판단 (DLBF L1059) 이 "부트스트랩 단계인가, 메인과 같은 스레드 풀인가" 를 가리는 기준
 |
 | L948 "bootstrapExecutor" 빈 (Executor) 이 있으면
 |        --> 팩토리에 설정   (@Bean(bootstrap = Bootstrap.BACKGROUND) 빈을 병렬 생성할 때 사용)
 |
 | L955 "conversionService" 빈 (ConversionService) 이 있으면
 |        --> 팩토리에 설정   (프로퍼티 값 변환, @Value 변환에 사용)
 |
 | L964 등록된 값 해석기가 하나도 없으면
 |        --> ${...} 를 environment 로 해석하는 기본 해석기 추가
 |            (PropertySourcesPlaceholderConfigurer 가 없어도 @Value("${x}") 가 동작하는 이유)
 |
 | L969 BeanFactoryInitializer 빈들 먼저 생성 + initialize(beanFactory)
 | L975 LoadTimeWeaverAware 빈들 먼저 생성   (클래스 변환기를 일반 클래스 로드 전에 등록)
 |
 | L989 임시 클래스로더 제거
 | L992 freezeConfiguration()             빈 정의 메타데이터 캐시 허용, 이후 변경 없다고 가정
 |
 +-- L995 preInstantiateSingletons()      lazy 가 아닌 싱글톤 전부 생성
```

1. [DefaultListableBeanFactory.preInstantiateSingletons](01_DefaultListableBeanFactory.preInstantiateSingletons/README.md)가 정의 목록을 순회하며 싱글톤을 만들고, 다 만든 뒤 [SmartInitializingSingleton](../../spi/SmartInitializingSingleton/README.md) 콜백을 부른다.

## 결과가 쓰이는 곳

```text
 conversionService
      --> 빈 생성 흐름의 프로퍼티 주입, @Value 문자열 -> 대상 타입 변환

 기본 값 해석기 (embedded value resolver)
      --> @Value("${...}") 해석, 애노테이션 속성의 플레이스홀더 해석

 freezeConfiguration
      --> getBeanNamesForType 결과를 캐시할 수 있게 됨 (allBeanNamesByType 캐시)
          이후 조회 성능 향상

 만들어진 싱글톤들
      --> 싱글톤 캐시에 저장 --> refresh 이후 getBean 은 캐시에서 바로 반환
```

## 하위 메서드

- [01 DefaultListableBeanFactory.preInstantiateSingletons](01_DefaultListableBeanFactory.preInstantiateSingletons/README.md)
