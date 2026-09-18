# AbstractAutowireCapableBeanFactory.createBean

상위: [AbstractBeanFactory.doGetBean](../README.md)

빈 클래스를 확정하고, 후처리기에게 "대신 만들 기회"를 한 번 준 뒤, 실제 생성을 `doCreateBean`에 넘긴다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L488-L540 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L488-L540))

```java
// AbstractAutowireCapableBeanFactory.java L488-L540
protected Object createBean(String beanName, RootBeanDefinition mbd, @Nullable Object @Nullable [] args)
        throws BeanCreationException {

    if (logger.isTraceEnabled()) {
        logger.trace("Creating instance of bean '" + beanName + "'");
    }
    RootBeanDefinition mbdToUse = mbd;

    // Make sure bean class is actually resolved at this point, and
    // clone the bean definition in case of a dynamically resolved Class
    // which cannot be stored in the shared merged bean definition.
    Class<?> resolvedClass = resolveBeanClass(mbd, beanName);
    if (resolvedClass != null && !mbd.hasBeanClass() && mbd.getBeanClassName() != null) {
        mbdToUse = new RootBeanDefinition(mbd);
        mbdToUse.setBeanClass(resolvedClass);
        try {
            mbdToUse.prepareMethodOverrides();
        }
        catch (BeanDefinitionValidationException ex) {
            throw new BeanDefinitionStoreException(mbdToUse.getResourceDescription(),
                    beanName, "Validation of method overrides failed", ex);
        }
    }

    try {
        // Give BeanPostProcessors a chance to return a proxy instead of the target bean instance.
        Object bean = resolveBeforeInstantiation(beanName, mbdToUse);
        if (bean != null) {
            return bean;
        }
    }
    catch (Throwable ex) {
        throw new BeanCreationException(mbdToUse.getResourceDescription(), beanName,
                "BeanPostProcessor before instantiation of bean failed", ex);
    }

    try {
        Object beanInstance = doCreateBean(beanName, mbdToUse, args);
        if (logger.isTraceEnabled()) {
            logger.trace("Finished creating instance of bean '" + beanName + "'");
        }
        return beanInstance;
    }
    catch (BeanCreationException | ImplicitlyAppearedSingletonException ex) {
        // A previously detected exception with proper bean creation context already,
        // or illegal singleton state to be communicated up to DefaultSingletonBeanRegistry.
        throw ex;
    }
    catch (Throwable ex) {
        throw new BeanCreationException(
                mbdToUse.getResourceDescription(), beanName, "Unexpected exception during bean creation", ex);
    }
}
```

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L1124-L1140 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L1124-L1140))

```java
// AbstractAutowireCapableBeanFactory.java L1124-L1140
protected @Nullable Object resolveBeforeInstantiation(String beanName, RootBeanDefinition mbd) {
    Object bean = null;
    if (!Boolean.FALSE.equals(mbd.beforeInstantiationResolved)) {
        // Make sure bean class is actually resolved at this point.
        if (!mbd.isSynthetic() && hasInstantiationAwareBeanPostProcessors()) {
            Class<?> targetType = determineTargetType(beanName, mbd);
            if (targetType != null) {
                bean = applyBeanPostProcessorsBeforeInstantiation(targetType, beanName);
                if (bean != null) {
                    bean = applyBeanPostProcessorsAfterInitialization(bean, beanName);
                }
            }
        }
        mbd.beforeInstantiationResolved = (bean != null);
    }
    return bean;
}
```

## 동작 흐름

```text
 createBean(beanName, mbd, args)
 |
 | L499 resolveBeanClass      클래스 이름 문자열을 Class 로 (임시 클래스로더 고려)
 |        동적으로 해석된 경우 정의를 복제해 그 복제본을 사용 (공유 정의 오염 방지)
 | L504 prepareMethodOverrides   lookup-method, replaced-method 검증
 |
 +-- L514 resolveBeforeInstantiation
 |     |
 |     | 정의가 synthetic 이 아니고 InstantiationAware 처리기가 있으면
 |     |   targetType 결정 --> postProcessBeforeInstantiation(targetType, beanName)
 |     |     null 아닌 값을 돌려준 처리기가 있으면
 |     |       --> 그 객체에 초기화 후 콜백만 적용하고 그대로 반환
 |     |       --> 아래 doCreateBean 자체를 건너뜀
 |     |   기록: beforeInstantiationResolved = (대체 여부)
 |     |
 |     +-- 대체 객체 있음 --> createBean 종료
 |
 +-- L525 doCreateBean(beanName, mbdToUse, args)
       예외는 BeanCreationException 으로 감싸 전달
```

- 후처리기가 대신 만드는 경로는 [InstantiationAwareBeanPostProcessor](../../spi/InstantiationAwareBeanPostProcessor/README.md)가 담당한다. `@Configuration` 프록시나 AOP 커스텀 타깃 소스처럼 컨테이너 표준 생성 자체를 대체할 때 쓴다.
- 일반 경로는 [doCreateBean](01_AbstractAutowireCapableBeanFactory.doCreateBean/README.md)이다.

## 결과가 쓰이는 곳

```text
 반환 객체
      --> doGetBean 의 싱글톤/프로토타입/스코프 분기가 받아 캐시 또는 반환

 mbdToUse (복제된 정의)
      --> 동적 클래스 해석 결과가 공유 정의에 남지 않게 함
          = 같은 정의로 여러 번 만들 때 클래스로더가 달라도 안전

 beforeInstantiationResolved 플래그
      --> 같은 정의로 다시 만들 때 before-instantiation 검사를 건너뛰는 최적화
```

## 하위 메서드

- [01 AbstractAutowireCapableBeanFactory.doCreateBean](01_AbstractAutowireCapableBeanFactory.doCreateBean/README.md)
