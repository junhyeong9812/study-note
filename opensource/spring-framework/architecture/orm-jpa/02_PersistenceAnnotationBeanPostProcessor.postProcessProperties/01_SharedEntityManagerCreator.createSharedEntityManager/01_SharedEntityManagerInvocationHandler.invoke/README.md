# SharedEntityManagerInvocationHandler.invoke

상위: [SharedEntityManagerCreator.createSharedEntityManager](../README.md)

공유 프록시에 들어온 호출 하나가 어디로 가는지 정하는 곳이다. 먼저 프록시가 직접 답할 수 있는 메서드를 걸러내고, 그다음 현재 트랜잭션의 `EntityManager`를 찾고, 없으면 임시로 하나 열었다가 닫는다.

## 실제 코드

프록시가 직접 답하는 메서드부터 걸러 낸다.

`spring-orm` / `org.springframework.orm.jpa` / `SharedEntityManagerCreator.java` L317-L366 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/SharedEntityManagerCreator.java#L317-L366))

```java
// SharedEntityManagerCreator.java L317-L366
public @Nullable Object invoke(Object proxy, Method method, @Nullable Object[] args) throws Throwable {
    // Invocation on EntityManager interface coming in...

    switch (method.getName()) {
        case "equals" -> {
            // Only consider equal when proxies are identical.
            return (proxy == args[0]);
        }
        case "hashCode" -> {
            // Use hashCode of EntityManager proxy.
            return hashCode();
        }
        case "toString" -> {
            // Deliver toString without touching a target EntityManager.
            return "Shared EntityManager proxy for target factory [" + this.targetFactory + "]";
        }
        case "getEntityManagerFactory" -> {
            // JPA 2.0: return EntityManagerFactory without creating an EntityManager.
            return this.targetFactory;
        }
        case "getCriteriaBuilder", "getMetamodel" -> {
            // JPA 2.0: return EntityManagerFactory's CriteriaBuilder/Metamodel (avoid creation of EntityManager)
            try {
                return EntityManagerFactory.class.getMethod(method.getName()).invoke(this.targetFactory);
            }
            catch (InvocationTargetException ex) {
                throw ex.getTargetException();
            }
        }
        case "unwrap" -> {
            // JPA 2.0: handle unwrap method - could be a proxy match.
            Class<?> targetClass = (Class<?>) args[0];
            if (targetClass != null && targetClass.isInstance(proxy)) {
                return proxy;
            }
        }
        case "isOpen" -> {
            // Handle isOpen method: always return true.
            return true;
        }
        case "close" -> {
            // Handle close method: suppress, not valid.
            return null;
        }
        case "getTransaction" -> {
            throw new IllegalStateException(
                    "Not allowed to create transaction on shared EntityManager - " +
                    "use Spring transactions or EJB CMT instead");
        }
    }
```

그다음 현재 트랜잭션의 EntityManager 를 찾아 위임한다.

`spring-orm` / `org.springframework.orm.jpa` / `SharedEntityManagerCreator.java` L368-L414 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-orm/src/main/java/org/springframework/orm/jpa/SharedEntityManagerCreator.java#L368-L414))

```java
// SharedEntityManagerCreator.java L368-L413
// Determine current EntityManager: either the transactional one
// managed by the factory or a temporary one for the given invocation.
EntityManager target = EntityManagerFactoryUtils.doGetTransactionalEntityManager(
        this.targetFactory, this.properties, this.synchronizedWithTransaction);

switch (method.getName()) {
    case "getTargetEntityManager" -> {
        // Handle EntityManagerProxy interface.
        if (target == null) {
            throw new IllegalStateException("No transactional EntityManager available");
        }
        return target;
    }
    case "unwrap" -> {
        Class<?> targetClass = (Class<?>) args[0];
        if (targetClass == null) {
            return (target != null ? target : proxy);
        }
        // We need a transactional target now.
        if (target == null) {
            throw new IllegalStateException("No transactional EntityManager available");
        }
    }
    // Still perform unwrap call on target EntityManager.
}

if (transactionRequiringMethods.contains(method.getName())) {
    // We need a transactional target now, according to the JPA spec.
    // Otherwise, the operation would get accepted but remain unflushed...
    if (target == null || (!TransactionSynchronizationManager.isActualTransactionActive() &&
            !target.getTransaction().isActive())) {
        throw new TransactionRequiredException("No EntityManager with actual transaction available " +
                "for current thread - cannot reliably process '" + method.getName() + "' call");
    }
}

// Regular EntityManager operations.
boolean newTarget = false;
if (target == null) {
    logger.debug("Creating new EntityManager for shared EntityManager invocation");
    target = EntityManagerFactoryUtils.createEntityManager(this.targetFactory, this.properties);
    newTarget = true;
}

// Invoke method on current EntityManager.
return invokeMethod(method, args, target, newTarget);
```

## 동작 흐름

```text
 invoke(proxy, method, args)
 |
 +-- [1] 프록시가 직접 답하는 메서드 (대상 EntityManager 를 열지 않는다)
 |      L321 equals        프록시 동일성으로만 판정
 |      L325 hashCode      프록시의 해시
 |      L329 toString      "Shared EntityManager proxy for target factory [...]"
 |      L333 getEntityManagerFactory   팩토리를 그대로 반환
 |      L337 getCriteriaBuilder / getMetamodel   팩토리에 물어 본다
 |      L353 isOpen        항상 true
 |      L357 close         무시 (프록시는 닫는 대상이 아니다)
 |      L361 getTransaction  IllegalStateException
 |             = 공유 프록시에서 직접 트랜잭션을 열 수 없다. 스프링 트랜잭션을 쓰라는 뜻
 |
 | [2] L370 doGetTransactionalEntityManager(팩토리, 프로퍼티, 동기화 여부)
 |        지금 트랜잭션에 묶인 EntityManager 를 찾는다 (없으면 null)
 |
 +-- [3] L374 getTargetEntityManager   null 이면 IllegalStateException
 |      L381 unwrap                    대상이 필요하면 같은 검사
 |
 +-- [4] L394 트랜잭션이 필요한 메서드인데 (persist, flush 등)
 |        대상이 없거나 실제 트랜잭션이 없으면
 |        --> TransactionRequiredException
 |            "빠져나갔지만 flush 되지 않는" 조용한 유실을 막는다
 |
 +-- [5] L404 그 밖의 호출
        대상이 없으면 L408 임시 EntityManager 를 새로 연다 (newTarget = true)
        L413 invokeMethod 로 위임하고, 임시로 연 것이면 호출 뒤 닫는다
        단 반환값이 Query 면 닫기를 미룬다. DeferredQueryInvocationHandler 로 감싸
        결과를 꺼내는 시점까지 EntityManager 를 살려 둔다 (L259-L277)
```

```text
 트랜잭션 유무가 만드는 차이

 트랜잭션 안
   같은 EntityManager 를 계속 쓴다 --> 1차 캐시, 더티 체킹, 지연 로딩이 성립

 트랜잭션 밖
   조회 메서드는 호출마다 새 EntityManager 를 열고 바로 닫는다
     --> 같은 엔티티를 두 번 조회해도 다른 인스턴스가 나온다
     --> 반환된 엔티티는 즉시 준영속. 지연 로딩을 건드리면 예외
   쓰기 메서드는 아예 TransactionRequiredException
```

## 결과가 쓰이는 곳

```text
 위임 대상 EntityManager
      --> EntityManagerFactoryUtils 가 스레드 바인딩에서 찾아 준다
      --> 그 바인딩을 만드는 쪽이 JpaTransactionManager.doBegin 이다

 close 를 무시하는 이유
      --> 공유 프록시를 애플리케이션 코드가 닫아 버리면 다른 호출이 깨진다
      --> 진짜 인스턴스를 닫는 책임은 트랜잭션 매니저에 있다

 isOpen 이 항상 true 인 이유
      --> 프록시 자체는 언제나 쓸 수 있다는 뜻이다
      --> 뒤에 붙는 인스턴스가 매번 달라도 호출자는 신경 쓰지 않아도 된다
```

1. 대상을 찾는 조회 지점은 [EntityManagerFactoryUtils.doGetTransactionalEntityManager](../../../03_JpaTransactionManager.doBegin/01_EntityManagerFactoryUtils.doGetTransactionalEntityManager/README.md)에 있다.
