# SharedEntityManagerCreator.createSharedEntityManager

상위: [PersistenceAnnotationBeanPostProcessor.postProcessProperties](../README.md)

`@PersistenceContext`가 꽂아 주는 것은 진짜 `EntityManager`가 아니라 JDK 동적 프록시다. 싱글톤 빈의 필드에 두어도 되는 이유가 이 한 메서드에 있다.

## 실제 코드

`spring-orm` / `org.springframework.orm.jpa` / `SharedEntityManagerCreator.java` L165-L178 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/SharedEntityManagerCreator.java#L165-L178))

```java
// SharedEntityManagerCreator.java L165-L178
public static EntityManager createSharedEntityManager(EntityManagerFactory emf, @Nullable Map<?, ?> properties,
        boolean synchronizedWithTransaction, Class<?>... entityManagerInterfaces) {

    ClassLoader cl = null;
    if (emf instanceof EntityManagerFactoryInfo emfInfo) {
        cl = emfInfo.getBeanClassLoader();
    }
    Class<?>[] ifcs = new Class<?>[entityManagerInterfaces.length + 1];
    System.arraycopy(entityManagerInterfaces, 0, ifcs, 0, entityManagerInterfaces.length);
    ifcs[entityManagerInterfaces.length] = EntityManagerProxy.class;
    return (EntityManager) Proxy.newProxyInstance(
            (cl != null ? cl : SharedEntityManagerCreator.class.getClassLoader()),
            ifcs, new SharedEntityManagerInvocationHandler(emf, properties, synchronizedWithTransaction));
}
```

## 동작 흐름

```text
 createSharedEntityManager(emf, properties, synchronizedWithTransaction, 인터페이스들)
 |
 +-- L169 emf 가 EntityManagerFactoryInfo 면 그 빈 클래스로더를 쓴다 (L170)
 |        (벤더 인터페이스까지 프록시에 얹으려면 같은 로더여야 한다)
 |
 | L172 프록시가 구현할 인터페이스 배열을 만든다
 |        전달받은 EntityManager 계열 인터페이스 + EntityManagerProxy
 |        = em.unwrap 이나 벤더 타입 캐스팅이 되는 이유
 |
 +-- L175 Proxy.newProxyInstance(로더, 인터페이스들, SharedEntityManagerInvocationHandler)
        상태가 없는 프록시 하나를 만든다. 실제 EntityManager 는 아직 없다
```

```text
 무엇이 "공유"인가

 프록시 인스턴스           빈 필드에 한 번 꽂히고 계속 그대로 (스레드 공유)
 뒤에 있는 EntityManager   호출 시점마다 현재 스레드의 것을 찾는다 (스레드마다 다름)

 그래서
   프록시는 상태가 없어 스레드 안전하고
   영속성 컨텍스트는 트랜잭션마다 분리된다
```

1. 호출을 실제로 가로채는 지점은 [SharedEntityManagerInvocationHandler.invoke](01_SharedEntityManagerInvocationHandler.invoke/README.md)다.

## 결과가 쓰이는 곳

```text
 반환한 프록시
      --> @PersistenceContext 필드에 주입된다
      --> SharedEntityManagerBean 이나 JPA 리포지터리 구현도 같은 것을 쓴다

 EntityManagerProxy 인터페이스를 함께 구현하는 덕분에
      --> getTargetEntityManager() 로 현재 뒤에 있는 진짜 인스턴스를 꺼낼 수 있다
      --> 벤더 전용 API 가 필요할 때 탈출구가 된다

 synchronizedWithTransaction = false 로 만들면
      --> 진행 중인 트랜잭션에 자동으로 참여하지 않는 EntityManager 를 요구한다
      --> @PersistenceContext(synchronization = UNSYNCHRONIZED) 가 이 경로다
```
