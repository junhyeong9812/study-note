# PersistenceAnnotationBeanPostProcessor.postProcessProperties

상위: [Spring JPA 연동](../README.md)

`@PersistenceContext`와 `@PersistenceUnit`이 붙은 필드와 메서드를 찾아 값을 꽂는 후처리기다. `@Autowired`를 처리하는 후처리기와 같은 자리에서, 같은 방식(`InjectionMetadata`)으로 동작한다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa.support` / `PersistenceAnnotationBeanPostProcessor.java` L399-L408 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/support/PersistenceAnnotationBeanPostProcessor.java#L399-L408))

```java
// PersistenceAnnotationBeanPostProcessor.java L399-L408
public PropertyValues postProcessProperties(PropertyValues pvs, Object bean, String beanName) {
    InjectionMetadata metadata = findPersistenceMetadata(beanName, bean.getClass(), pvs);
    try {
        metadata.inject(bean, beanName, pvs);
    }
    catch (Throwable ex) {
        throw new BeanCreationException(beanName, "Injection of persistence dependencies failed", ex);
    }
    return pvs;
}
```

무엇을 꽂을지는 애노테이션 종류와 타입이 정한다.

`spring-orm` / `org.springframework.orm.jpa.support` / `PersistenceAnnotationBeanPostProcessor.java` L758-L771 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/support/PersistenceAnnotationBeanPostProcessor.java#L758-L771))

```java
// PersistenceAnnotationBeanPostProcessor.java L758-L771
protected Object getResourceToInject(Object target, @Nullable String requestingBeanName) {
    // Resolves to EntityManagerFactory or EntityManager.
    if (this.persistenceUnit) {
        return resolveEntityManagerFactory(requestingBeanName);
    }
    else if (this.type != null) {
        return (this.type == PersistenceContextType.EXTENDED ?
                resolveExtendedEntityManager(target, requestingBeanName) :
                resolveEntityManager(requestingBeanName));
    }
    else {
        return resolveEntityAgent(requestingBeanName);
    }
}
```

## 동작 흐름

```text
 postProcessProperties(pvs, bean, beanName)
 |
 | L400 findPersistenceMetadata(beanName, 클래스, pvs)
 |        @PersistenceContext / @PersistenceUnit 붙은 멤버를 찾아 캐시한다
 |        (클래스당 한 번만 훑는다)
 |
 +-- L402 metadata.inject(bean, beanName, pvs)
 |        멤버마다 getResourceToInject 로 값을 만들어 리플렉션으로 설정
 |
 +-- L405 예외가 나면 BeanCreationException("Injection of persistence dependencies failed")

 getResourceToInject(target, requestingBeanName)
 |
 +-- L760 @PersistenceUnit  --> resolveEntityManagerFactory
 |        EntityManagerFactory 를 그대로 꽂는다
 |
 +-- L764 @PersistenceContext(type = EXTENDED) --> resolveExtendedEntityManager (L810)
 |        빈에 묶이는 확장 영속성 컨텍스트. 빈이 파괴될 때 닫는다
 |
 +-- L766 @PersistenceContext(기본 TRANSACTION) --> resolveEntityManager (L783)
        SharedEntityManagerCreator 가 만든 공유 프록시를 꽂는다
```

```text
 @Autowired 와 나란히 보기

 AutowiredAnnotationBeanPostProcessor   @Autowired @Value @Inject
 PersistenceAnnotationBeanPostProcessor @PersistenceContext @PersistenceUnit

 둘 다 InstantiationAwareBeanPostProcessor 의 postProcessProperties 단계에서
 InjectionMetadata 를 만들어 주입한다. 다른 것은 "무엇을 꽂느냐"뿐이다
```

1. 꽂히는 프록시가 어떻게 만들어지는지는 [SharedEntityManagerCreator.createSharedEntityManager](01_SharedEntityManagerCreator.createSharedEntityManager/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 꽂힌 EntityManager (공유 프록시)
      --> 싱글톤 리포지터리 빈의 필드로 두어도 안전하다
      --> 프록시가 호출마다 현재 트랜잭션의 진짜 인스턴스를 찾기 때문이다

 꽂힌 EntityManagerFactory
      --> 직접 createEntityManager() 를 부르면 트랜잭션과 무관한 인스턴스가 나온다
      --> 닫는 책임도 호출한 쪽에 있다

 EXTENDED 타입
      --> 빈 하나에 영속성 컨텍스트가 붙어 트랜잭션을 넘어 산다
      --> 상태를 가진 빈에서만 의미가 있고, 싱글톤에 쓰면 위험하다 (소스 주석이 경고한다)

 주입 실패
      --> BeanCreationException 으로 감싸져 기동이 멈춘다
```

주입 단계 전체의 골격은 [빈 생성의 populateBean](../../bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/02_AbstractAutowireCapableBeanFactory.populateBean/README.md)에 있다.

## 하위 메서드

- [01 SharedEntityManagerCreator.createSharedEntityManager](01_SharedEntityManagerCreator.createSharedEntityManager/README.md)
