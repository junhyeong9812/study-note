# AbstractAutowireCapableBeanFactory.doCreateBean

상위: [AbstractAutowireCapableBeanFactory.createBean](../README.md)

빈 한 개의 생애를 순서대로 실행한다. 인스턴스화, 정의 후처리, 조기 참조 노출, 주입, 초기화, 소멸 등록의 여섯 마디다. 순환 참조 해소와 프록시 교체 검사도 여기서 이뤄진다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L556-L649 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L556-L649))

```java
// AbstractAutowireCapableBeanFactory.java L556-L649
protected Object doCreateBean(String beanName, RootBeanDefinition mbd, @Nullable Object @Nullable [] args)
        throws BeanCreationException {

    // Instantiate the bean.
    BeanWrapper instanceWrapper = null;
    if (mbd.isSingleton()) {
        instanceWrapper = this.factoryBeanInstanceCache.remove(beanName);
    }
    if (instanceWrapper == null) {
        instanceWrapper = createBeanInstance(beanName, mbd, args);
    }
    Object bean = instanceWrapper.getWrappedInstance();
    Class<?> beanType = instanceWrapper.getWrappedClass();
    if (beanType != NullBean.class) {
        mbd.resolvedTargetType = beanType;
    }

    // Allow post-processors to modify the merged bean definition.
    synchronized (mbd.postProcessingLock) {
        if (!mbd.postProcessed) {
            try {
                applyMergedBeanDefinitionPostProcessors(mbd, beanType, beanName);
            }
            catch (Throwable ex) {
                throw new BeanCreationException(mbd.getResourceDescription(), beanName,
                        "Post-processing of merged bean definition failed", ex);
            }
            mbd.markAsPostProcessed();
        }
    }

    // Eagerly cache singletons to be able to resolve circular references
    // even when triggered by lifecycle interfaces like BeanFactoryAware.
    boolean earlySingletonExposure = (mbd.isSingleton() && this.allowCircularReferences &&
            isSingletonCurrentlyInCreation(beanName));
    if (earlySingletonExposure) {
        if (logger.isTraceEnabled()) {
            logger.trace("Eagerly caching bean '" + beanName +
                    "' to allow for resolving potential circular references");
        }
        addSingletonFactory(beanName, () -> getEarlyBeanReference(beanName, mbd, bean));
    }

    // Initialize the bean instance.
    Object exposedObject = bean;
    try {
        populateBean(beanName, mbd, instanceWrapper);
        exposedObject = initializeBean(beanName, exposedObject, mbd);
    }
    catch (Throwable ex) {
        if (ex instanceof BeanCreationException bce && beanName.equals(bce.getBeanName())) {
            throw bce;
        }
        throw new BeanCreationException(mbd.getResourceDescription(), beanName, ex.getMessage(), ex);
    }

    if (earlySingletonExposure) {
        Object earlySingletonReference = getSingleton(beanName, false);
        if (earlySingletonReference != null) {
            if (exposedObject == bean) {
                exposedObject = earlySingletonReference;
            }
            else if (!this.allowRawInjectionDespiteWrapping && hasDependentBean(beanName)) {
                String[] dependentBeans = getDependentBeans(beanName);
                Set<String> actualDependentBeans = CollectionUtils.newLinkedHashSet(dependentBeans.length);
                for (String dependentBean : dependentBeans) {
                    if (!removeSingletonIfCreatedForTypeCheckOnly(dependentBean)) {
                        actualDependentBeans.add(dependentBean);
                    }
                }
                if (!actualDependentBeans.isEmpty()) {
                    throw new BeanCurrentlyInCreationException(beanName,
                            "Bean with name '" + beanName + "' has been injected into other beans [" +
                            StringUtils.collectionToCommaDelimitedString(actualDependentBeans) +
                            "] in its raw version as part of a circular reference, but has eventually been " +
                            "wrapped. This means that said other beans do not use the final version of the " +
                            "bean. This is often the result of over-eager type matching - consider using " +
                            "'getBeanNamesForType' with the 'allowEagerInit' flag turned off, for example.");
                }
            }
        }
    }

    // Register bean as disposable.
    try {
        registerDisposableBeanIfNecessary(beanName, bean, mbd);
    }
    catch (BeanDefinitionValidationException ex) {
        throw new BeanCreationException(
                mbd.getResourceDescription(), beanName, "Invalid destruction signature", ex);
    }

    return exposedObject;
}
```

## 동작 흐름

```text
 doCreateBean(beanName, mbd, args)
 |
 | [1] L560-L567 인스턴스화
 |       factoryBeanInstanceCache 에 있던 것 재사용, 없으면 createBeanInstance
 |       bean = 아직 아무것도 주입되지 않은 맨 객체
 |
 | [2] L574-L585 applyMergedBeanDefinitionPostProcessors   (정의당 한 번만)
 |       @Autowired / @Value 필드와 메서드 위치를 스캔해 캐시
 |       @PostConstruct / @PreDestroy 메서드 수집
 |       --> 이후 주입 단계가 리플렉션 탐색을 다시 하지 않도록
 |
 | [3] L589-L597 조기 참조 노출 조건
 |       싱글톤 + 순환 참조 허용 + 지금 생성 중
 |       --> addSingletonFactory(이름, () -> getEarlyBeanReference(bean))
 |           아직 주입도 초기화도 안 된 객체지만, 순환 참조가 생기면 이것이 나간다
 |
 | [4] L602 populateBean         필드/세터 주입
 | [5] L603 initializeBean       Aware, 초기화 콜백, 프록시 --> exposedObject
 |
 | [6] L612-L637 조기 참조 검사
 |       조기 참조가 실제로 나갔는가? (getSingleton(name, false) 로 확인)
 |         exposedObject == bean        --> 최종 객체를 조기 참조로 교체 (같은 객체 유지)
 |         초기화가 객체를 바꿨고(프록시) 이미 다른 빈이 원본을 주입받았음
 |           --> BeanCurrentlyInCreationException
 |               "raw version 이 주입됐는데 결국 래핑됐다" 오류
 |
 +-- [7] L641 registerDisposableBeanIfNecessary
       반환 exposedObject
```

1. [createBeanInstance](01_AbstractAutowireCapableBeanFactory.createBeanInstance/README.md)가 생성자 또는 팩토리 메서드로 객체를 만든다.
2. [populateBean](02_AbstractAutowireCapableBeanFactory.populateBean/README.md)이 의존성을 주입한다.
3. [initializeBean](03_AbstractAutowireCapableBeanFactory.initializeBean/README.md)이 초기화 콜백을 부르고 프록시를 씌운다.
4. [registerDisposableBeanIfNecessary](04_AbstractBeanFactory.registerDisposableBeanIfNecessary/README.md)가 소멸 콜백을 등록한다.

[2]에서 도는 처리기는 [MergedBeanDefinitionPostProcessor](../../../spi/MergedBeanDefinitionPostProcessor/README.md)이고, [3]의 조기 참조는 `SmartInstantiationAwareBeanPostProcessor`가 가공한다.

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L966-L974 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L966-L974))

```java
// AbstractAutowireCapableBeanFactory.java L966-L974
protected Object getEarlyBeanReference(String beanName, RootBeanDefinition mbd, Object bean) {
    Object exposedObject = bean;
    if (!mbd.isSynthetic() && hasInstantiationAwareBeanPostProcessors()) {
        for (SmartInstantiationAwareBeanPostProcessor bp : getBeanPostProcessorCache().smartInstantiationAware) {
            exposedObject = bp.getEarlyBeanReference(exposedObject, beanName);
        }
    }
    return exposedObject;
}
```

## 결과가 쓰이는 곳

```text
 bean (맨 객체)
      --> [3] 조기 참조의 원본
      --> [7] 소멸 등록의 대상 (프록시가 아니라 원본을 파괴 대상으로 등록)

 exposedObject (초기화 후 객체, 보통 프록시)
      --> getSingleton 이 받아 addSingleton --> 싱글톤 캐시
      --> 주입/조회에서 사용자에게 보이는 객체

 순환 참조에서 나간 조기 참조
      --> AOP 가 걸린 빈이면 getEarlyBeanReference 가 미리 프록시를 만들어 노출
          그래서 [6] 의 "원본이 주입됐다" 오류는 보통 발생하지 않는다
          allowRawInjectionDespiteWrapping = true 로 두면 검사 자체를 끈다
```

## 하위 메서드

- [01 createBeanInstance](01_AbstractAutowireCapableBeanFactory.createBeanInstance/README.md)
- [02 populateBean](02_AbstractAutowireCapableBeanFactory.populateBean/README.md)
- [03 initializeBean](03_AbstractAutowireCapableBeanFactory.initializeBean/README.md)
- [04 registerDisposableBeanIfNecessary](04_AbstractBeanFactory.registerDisposableBeanIfNecessary/README.md)
