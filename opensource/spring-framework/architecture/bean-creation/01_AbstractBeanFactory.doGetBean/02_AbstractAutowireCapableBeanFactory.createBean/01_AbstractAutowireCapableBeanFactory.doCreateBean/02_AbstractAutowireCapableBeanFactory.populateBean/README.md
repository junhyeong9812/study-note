# AbstractAutowireCapableBeanFactory.populateBean

상위: [AbstractAutowireCapableBeanFactory.doCreateBean](../README.md)

만들어진 맨 객체에 값을 채운다. `@Autowired` 필드와 메서드 주입은 후처리기가 하고, XML `<property>`나 autowire 모드로 지정한 프로퍼티는 여기서 직접 설정한다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `AbstractAutowireCapableBeanFactory.java` L1390-L1461 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/AbstractAutowireCapableBeanFactory.java#L1390-L1461))

```java
// AbstractAutowireCapableBeanFactory.java L1390-L1461
protected void populateBean(String beanName, RootBeanDefinition mbd, @Nullable BeanWrapper bw) {
    if (bw == null) {
        if (mbd.hasPropertyValues()) {
            throw new BeanCreationException(
                    mbd.getResourceDescription(), beanName, "Cannot apply property values to null instance");
        }
        else {
            // Skip property population phase for null instance.
            return;
        }
    }

    if (bw.getWrappedClass().isRecord()) {
        if (mbd.hasPropertyValues()) {
            throw new BeanCreationException(
                    mbd.getResourceDescription(), beanName, "Cannot apply property values to a record");
        }
        else {
            // Skip property population phase for records since they are immutable.
            return;
        }
    }

    // Give any InstantiationAwareBeanPostProcessors the opportunity to modify the
    // state of the bean before properties are set. This can be used, for example,
    // to support styles of field injection.
    if (!mbd.isSynthetic() && hasInstantiationAwareBeanPostProcessors()) {
        for (InstantiationAwareBeanPostProcessor bp : getBeanPostProcessorCache().instantiationAware) {
            if (!bp.postProcessAfterInstantiation(bw.getWrappedInstance(), beanName)) {
                return;
            }
        }
    }

    PropertyValues pvs = (mbd.hasPropertyValues() ? mbd.getPropertyValues() : null);

    int resolvedAutowireMode = mbd.getResolvedAutowireMode();
    if (resolvedAutowireMode == AUTOWIRE_BY_NAME || resolvedAutowireMode == AUTOWIRE_BY_TYPE) {
        MutablePropertyValues newPvs = new MutablePropertyValues(pvs);
        // Add property values based on autowire by name if applicable.
        if (resolvedAutowireMode == AUTOWIRE_BY_NAME) {
            autowireByName(beanName, mbd, bw, newPvs);
        }
        // Add property values based on autowire by type if applicable.
        if (resolvedAutowireMode == AUTOWIRE_BY_TYPE) {
            autowireByType(beanName, mbd, bw, newPvs);
        }
        pvs = newPvs;
    }
    if (hasInstantiationAwareBeanPostProcessors()) {
        if (pvs == null) {
            pvs = mbd.getPropertyValues();
        }
        for (InstantiationAwareBeanPostProcessor bp : getBeanPostProcessorCache().instantiationAware) {
            PropertyValues pvsToUse = bp.postProcessProperties(pvs, bw.getWrappedInstance(), beanName);
            if (pvsToUse == null) {
                return;
            }
            pvs = pvsToUse;
        }
    }

    boolean needsDepCheck = (mbd.getDependencyCheck() != AbstractBeanDefinition.DEPENDENCY_CHECK_NONE);
    if (needsDepCheck) {
        PropertyDescriptor[] filteredPds = filterPropertyDescriptorsForDependencyCheck(bw, mbd.allowCaching);
        checkDependencies(beanName, mbd, filteredPds, pvs);
    }

    if (pvs != null) {
        applyPropertyValues(beanName, mbd, bw, pvs);
    }
}
```

`@Autowired` 주입을 담당하는 처리기의 진입점이다.

`spring-beans` / `org.springframework.beans.factory.annotation` / `AutowiredAnnotationBeanPostProcessor.java` L490-L502 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/annotation/AutowiredAnnotationBeanPostProcessor.java#L490-L502))

```java
// AutowiredAnnotationBeanPostProcessor.java L490-L502
public PropertyValues postProcessProperties(PropertyValues pvs, Object bean, String beanName) {
    InjectionMetadata metadata = findAutowiringMetadata(beanName, bean.getClass(), pvs);
    try {
        metadata.inject(bean, beanName, pvs);
    }
    catch (BeanCreationException ex) {
        throw ex;
    }
    catch (Throwable ex) {
        throw new BeanCreationException(beanName, "Injection of autowired dependencies failed", ex);
    }
    return pvs;
}
```

## 동작 흐름

```text
 populateBean(beanName, mbd, bw)
 |
 | L1391 인스턴스가 없음 --> 프로퍼티 있으면 오류, 없으면 return
 |       doCreateBean 경로에서는 안 걸리는 방어 코드다
 |       null 을 돌려준 팩토리 메서드는 NullBean 으로 감싸져 들어온다
 |       (SimpleInstantiationStrategy L156-158)
 | L1402 record 타입 --> 프로퍼티 주입 건너뜀 (불변)
 |
 +-- L1416 postProcessAfterInstantiation
 |      InstantiationAware 처리기 중 하나라도 false --> 주입 전체를 건너뛰고 return
 |      (필드 주입을 직접 하는 프레임워크가 표준 주입을 끄는 지점)
 |
 +-- L1426 autowire 모드 (XML byName / byType)
 |      autowireByName : 프로퍼티 이름과 같은 빈을 찾아 값으로
 |      autowireByType : 프로퍼티 타입으로 후보를 찾아 값으로
 |      --> pvs 에 추가
 |
 +-- L1439 postProcessProperties   <-- 애노테이션 주입의 본체
 |      AutowiredAnnotationBeanPostProcessor
 |        정의 후처리 때 캐시한 InjectionMetadata 를 꺼내 inject
 |        필드마다 resolveDependency --> 값 결정 --> field.set (private 이면 접근 허용 설정)
 |        메서드(@Autowired setter)면 파라미터 해석 후 호출
 |      CommonAnnotationBeanPostProcessor
 |        @Resource 를 이름 기준으로 주입
 |      처리기가 null 을 반환하면 이후 단계 생략
 |
 +-- L1452 의존성 검사 설정이 있으면 미충족 프로퍼티 검사
 +-- L1458 applyPropertyValues   pvs 를 실제 세터 호출로 반영 (타입 변환 포함)
```

- 실제 후보 탐색과 판정은 [DefaultListableBeanFactory.resolveDependency](01_DefaultListableBeanFactory.resolveDependency/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 주입된 필드 값
      --> initializeBean 의 초기화 콜백에서 이미 사용 가능
          (@PostConstruct 안에서 의존 빈을 쓸 수 있는 이유)

 주입 과정에서 요청된 다른 빈
      --> getBean 재귀 --> 그 빈이 아직 없으면 여기서 생성됨
      --> 순환 참조면 조기 참조가 반환됨 (doCreateBean [3] 에서 노출한 것)

 InjectionMetadata 캐시
      --> 같은 클래스의 다음 인스턴스(프로토타입 등)는 리플렉션 탐색 없이 주입
```

## 하위 메서드

- [01 DefaultListableBeanFactory.resolveDependency](01_DefaultListableBeanFactory.resolveDependency/README.md)
