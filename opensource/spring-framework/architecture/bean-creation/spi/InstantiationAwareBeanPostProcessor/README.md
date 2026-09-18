# InstantiationAwareBeanPostProcessor

상위: [Spring 빈 생성](../../README.md) / [spi](../README.md)

`BeanPostProcessor`를 확장해 **인스턴스화 이전**과 **주입 단계**에 끼어든다. 하위 인터페이스 `SmartInstantiationAwareBeanPostProcessor`는 생성자 선택과 순환 참조용 조기 참조까지 맡는다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.config` / `InstantiationAwareBeanPostProcessor.java` L44-L111 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/config/InstantiationAwareBeanPostProcessor.java#L44-L111))

```java
// InstantiationAwareBeanPostProcessor.java L44-L111
public interface InstantiationAwareBeanPostProcessor extends BeanPostProcessor {

    default @Nullable Object postProcessBeforeInstantiation(Class<?> beanClass, String beanName) throws BeansException {
        return null;
    }

    default boolean postProcessAfterInstantiation(Object bean, String beanName) throws BeansException {
        return true;
    }

    default @Nullable PropertyValues postProcessProperties(PropertyValues pvs, Object bean, String beanName)
            throws BeansException {

        return pvs;
    }

}
```

`spring-beans` / `org.springframework.beans.factory.config` / `SmartInstantiationAwareBeanPostProcessor.java` L37-L109 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/config/SmartInstantiationAwareBeanPostProcessor.java#L37-L109))

```java
// SmartInstantiationAwareBeanPostProcessor.java L37-L109
public interface SmartInstantiationAwareBeanPostProcessor extends InstantiationAwareBeanPostProcessor {

    default @Nullable Class<?> predictBeanType(Class<?> beanClass, String beanName) throws BeansException {
        return null;
    }

    default Class<?> determineBeanType(Class<?> beanClass, String beanName) throws BeansException {
        return beanClass;
    }

    default Constructor<?> @Nullable [] determineCandidateConstructors(Class<?> beanClass, String beanName)
            throws BeansException {

        return null;
    }

    default Object getEarlyBeanReference(Object bean, String beanName) throws BeansException {
        return bean;
    }

}
```

## 흐름에서 불리는 자리

```text
 createBean --> resolveBeforeInstantiation
   postProcessBeforeInstantiation   null 아닌 값을 주면 컨테이너 생성을 건너뛴다
 createBeanInstance
   determineCandidateConstructors   (Smart) 쓸 생성자 선택
 doCreateBean --> addSingletonFactory
   getEarlyBeanReference            (Smart) 순환 참조 때 노출할 객체
 populateBean
   postProcessAfterInstantiation    false 면 주입 단계 중단
   postProcessProperties            실제 애노테이션 주입
```

- [AbstractAutowireCapableBeanFactory.createBean](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/README.md)
- [createBeanInstance](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/01_AbstractAutowireCapableBeanFactory.createBeanInstance/README.md)
- [populateBean](../../01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/02_AbstractAutowireCapableBeanFactory.populateBean/README.md)

## 구현 계층

```text
 BeanPostProcessor
   +-- InstantiationAwareBeanPostProcessor
         +-- SmartInstantiationAwareBeanPostProcessor
         |     +-- AutowiredAnnotationBeanPostProcessor   @Autowired 생성자 선택 + 필드/메서드 주입
         |     +-- AbstractAutoProxyCreator               조기 참조 프록시, 초기화 후 프록시
         +-- CommonAnnotationBeanPostProcessor            @Resource 주입
         +-- ConfigurationClassPostProcessor 의 ImportAwareBeanPostProcessor
```
