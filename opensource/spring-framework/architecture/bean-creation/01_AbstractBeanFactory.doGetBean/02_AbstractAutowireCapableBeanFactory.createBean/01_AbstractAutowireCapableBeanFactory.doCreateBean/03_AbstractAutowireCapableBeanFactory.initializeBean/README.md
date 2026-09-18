# AbstractAutowireCapableBeanFactory.initializeBean

상위: [AbstractAutowireCapableBeanFactory.doCreateBean](../README.md)

주입이 끝난 객체를 "쓸 수 있는 상태"로 만든다. `Aware` 콜백, 초기화 전 후처리기(`@PostConstruct` 포함), 초기화 메서드, 초기화 후 후처리기(AOP 프록시) 순서다. **객체가 바뀔 수 있는 마지막 지점**이다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L1797-L1822 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L1797-L1822))

```java
// AbstractAutowireCapableBeanFactory.java L1797-L1822
protected Object initializeBean(String beanName, Object bean, @Nullable RootBeanDefinition mbd) {
    // Skip initialization of a NullBean
    if (bean.getClass() == NullBean.class) {
        return bean;
    }

    invokeAwareMethods(beanName, bean);

    Object wrappedBean = bean;
    if (mbd == null || !mbd.isSynthetic()) {
        wrappedBean = applyBeanPostProcessorsBeforeInitialization(wrappedBean, beanName);
    }

    try {
        invokeInitMethods(beanName, wrappedBean, mbd);
    }
    catch (Throwable ex) {
        throw new BeanCreationException(
                (mbd != null ? mbd.getResourceDescription() : null), beanName, ex.getMessage(), ex);
    }
    if (mbd == null || !mbd.isSynthetic()) {
        wrappedBean = applyBeanPostProcessorsAfterInitialization(wrappedBean, beanName);
    }

    return wrappedBean;
}
```

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L1824-L1839 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L1824-L1839))

```java
// AbstractAutowireCapableBeanFactory.java L1824-L1839
private void invokeAwareMethods(String beanName, Object bean) {
    if (bean instanceof Aware) {
        if (bean instanceof BeanNameAware beanNameAware) {
            beanNameAware.setBeanName(beanName);
        }
        if (bean instanceof BeanClassLoaderAware beanClassLoaderAware) {
            ClassLoader bcl = getBeanClassLoader();
            if (bcl != null) {
                beanClassLoaderAware.setBeanClassLoader(bcl);
            }
        }
        if (bean instanceof BeanFactoryAware beanFactoryAware) {
            beanFactoryAware.setBeanFactory(AbstractAutowireCapableBeanFactory.this);
        }
    }
}
```

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L421-L433 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L421-L433))

```java
// AbstractAutowireCapableBeanFactory.java L421-L433
public Object applyBeanPostProcessorsBeforeInitialization(Object existingBean, String beanName)
        throws BeansException {

    Object result = existingBean;
    for (BeanPostProcessor processor : getBeanPostProcessors()) {
        Object current = processor.postProcessBeforeInitialization(result, beanName);
        if (current == null) {
            return result;
        }
        result = current;
    }
    return result;
}
```

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L1854-L1877 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L1854-L1877))

```java
// AbstractAutowireCapableBeanFactory.java L1854-L1877
protected void invokeInitMethods(String beanName, Object bean, @Nullable RootBeanDefinition mbd)
        throws Throwable {

    boolean isInitializingBean = (bean instanceof InitializingBean);
    if (isInitializingBean && (mbd == null || !mbd.hasAnyExternallyManagedInitMethod("afterPropertiesSet"))) {
        if (logger.isTraceEnabled()) {
            logger.trace("Invoking afterPropertiesSet() on bean with name '" + beanName + "'");
        }
        ((InitializingBean) bean).afterPropertiesSet();
    }

    if (mbd != null && bean.getClass() != NullBean.class) {
        String[] initMethodNames = mbd.getInitMethodNames();
        if (initMethodNames != null) {
            for (String initMethodName : initMethodNames) {
                if (StringUtils.hasLength(initMethodName) &&
                        !(isInitializingBean && "afterPropertiesSet".equals(initMethodName)) &&
                        !mbd.hasAnyExternallyManagedInitMethod(initMethodName)) {
                    invokeCustomInitMethod(beanName, bean, mbd, initMethodName);
                }
            }
        }
    }
}
```

## 동작 흐름

```text
 initializeBean(beanName, bean, mbd)
 |
 | L1799 NullBean --> 그대로 반환
 |
 | [1] L1803 invokeAwareMethods                         (컨테이너 내부 3종만)
 |       BeanNameAware        --> setBeanName(beanName)
 |       BeanClassLoaderAware --> setBeanClassLoader
 |       BeanFactoryAware     --> setBeanFactory
 |
 | [2] L1807 applyBeanPostProcessorsBeforeInitialization
 |       처리기 체인을 순서대로 호출, null 을 돌려주면 그 앞의 결과로 중단
 |       ApplicationContextAwareProcessor   --> ApplicationContextAware 등 나머지 Aware 콜백
 |       CommonAnnotationBeanPostProcessor  --> @PostConstruct 메서드 호출
 |
 | [3] L1811 invokeInitMethods
 |       InitializingBean.afterPropertiesSet()
 |       정의의 init-method / @Bean(initMethod) 이름으로 메서드 호출
 |       (@PostConstruct 로 이미 처리된 이름은 건너뜀)
 |
 | [4] L1818 applyBeanPostProcessorsAfterInitialization
 |       AbstractAutoProxyCreator --> 필요하면 여기서 프록시로 교체
 |       BeanPostProcessorChecker --> 등록 미완 상태 경고
 |
 +-- 반환 wrappedBean   (프록시가 생겼다면 프록시)
```

초기화 콜백 3종의 순서는 다음과 같다.

```text
 @PostConstruct  (초기화 전 후처리기 단계)
   --> InitializingBean.afterPropertiesSet()
     --> init-method
```

- [1]의 인터페이스는 [Aware](../../../../spi/Aware/README.md), [3]의 인터페이스는 [InitializingBean](../../../../spi/InitializingBean/README.md)에 정리했다.
- 프록시 생성 시점인 [4]는 [BeanPostProcessor](../../../../../container-refresh/spi/BeanPostProcessor/README.md)의 마지막 확장 지점이다.
- [4]에서 프록시가 만들어지는 과정은 [AOP 프록시](../../../../../aop-proxy/README.md) 흐름으로 이어진다.

## 결과가 쓰이는 곳

```text
 반환 객체 (exposedObject)
      --> doCreateBean [6] 조기 참조 검사 --> getSingleton --> 싱글톤 캐시
      --> 다른 빈에 주입되는 것도 이 객체 (프록시면 프록시)

 원본 객체 (bean)
      --> registerDisposableBeanIfNecessary 의 대상
          = 소멸 콜백은 프록시가 아니라 원본에서 찾는다

 [4] 에서 프록시로 바뀐 경우
      --> 자기 자신 호출(this.method())은 프록시를 거치지 않는다
          @Transactional 이 같은 클래스 내부 호출에서 동작하지 않는 이유
```
