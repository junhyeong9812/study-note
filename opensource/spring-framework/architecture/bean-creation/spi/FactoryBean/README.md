# FactoryBean

상위: [Spring 빈 생성](../../README.md) / [spi](../README.md)

빈 하나가 다른 객체를 만들어 내는 공장 역할을 한다. 컨테이너는 `myBean` 이름으로 조회하면 `getObject()` 결과를, `&myBean` 으로 조회하면 공장 자신을 돌려준다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory` / `FactoryBean.java` L65-L147 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/FactoryBean.java#L65-L147))

```java
// FactoryBean.java L65-L147
public interface FactoryBean<T> {

    String OBJECT_TYPE_ATTRIBUTE = "factoryBeanObjectType";

    @Nullable T getObject() throws Exception;

    @Nullable Class<?> getObjectType();

    default boolean isSingleton() {
        return true;
    }

}
```

## 흐름에서 불리는 자리

```text
 doGetBean --> getObjectForBeanInstance (ABF L1854)
   이름이 &로 시작   --> 공장 객체 그대로 (FactoryBean 이 아니면 BeanIsNotAFactoryException)
   그 밖             --> factoryBean.getObject() 결과
                         싱글톤이면 factoryBeanObjectCache 에 보관
 preInstantiateSingletons (DLBF L1218)
   FactoryBean 이면 먼저 &이름 으로 공장만 생성
   SmartFactoryBean.isEagerInit() 이면 제품까지 미리 생성
```

- [AbstractBeanFactory.doGetBean](../../01_AbstractBeanFactory.doGetBean/README.md)

## 구현 계층

```text
 FactoryBean<T>
   +-- SmartFactoryBean<T>                isEagerInit, isPrototype
   +-- AbstractFactoryBean<T>             싱글톤 캐싱, DisposableBean 연동
   +-- ProxyFactoryBean                   AOP 프록시를 빈으로
   +-- LocalContainerEntityManagerFactoryBean 등 JPA/JDBC 인프라 빈

 주의: getObject() 가 만든 객체는 컨테이너가 만든 빈이 아니다
       BeanPostProcessor 의 초기화 후 콜백만 적용되고(구성에 따라 다름),
       주입과 초기화 콜백은 공장이 직접 책임진다
```
