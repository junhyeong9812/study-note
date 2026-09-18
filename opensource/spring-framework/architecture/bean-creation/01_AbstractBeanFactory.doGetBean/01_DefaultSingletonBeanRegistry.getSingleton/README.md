# DefaultSingletonBeanRegistry.getSingleton

상위: [AbstractBeanFactory.doGetBean](../README.md)

싱글톤 캐시를 관리한다. 조회용과 생성용 두 가지가 있다. 조회용은 세 단계 캐시로 순환 참조 중인 빈의 조기 참조까지 돌려주고, 생성용은 생성 잠금과 "생성 중" 표시를 걸고 팩토리를 호출한 뒤 결과를 캐시에 넣는다.

## 실제 코드 (조회)

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultSingletonBeanRegistry.java` L208-L244 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultSingletonBeanRegistry.java#L208-L244))

```java
// DefaultSingletonBeanRegistry.java L208-L244
protected @Nullable Object getSingleton(String beanName, boolean allowEarlyReference) {
    // Quick check for existing instance without full singleton lock.
    Object singletonObject = this.singletonObjects.get(beanName);
    if (singletonObject == null && isSingletonCurrentlyInCreation(beanName)) {
        singletonObject = this.earlySingletonObjects.get(beanName);
        if (singletonObject == null && allowEarlyReference) {
            if (!this.singletonLock.tryLock()) {
                // Avoid early singleton inference outside of original creation thread.
                return null;
            }
            try {
                // Consistent creation of early reference within full singleton lock.
                singletonObject = this.singletonObjects.get(beanName);
                if (singletonObject == null) {
                    singletonObject = this.earlySingletonObjects.get(beanName);
                    if (singletonObject == null) {
                        ObjectFactory<?> singletonFactory = this.singletonFactories.get(beanName);
                        if (singletonFactory != null) {
                            singletonObject = singletonFactory.getObject();
                            // Singleton could have been added or removed in the meantime.
                            if (this.singletonFactories.remove(beanName) != null) {
                                this.earlySingletonObjects.put(beanName, singletonObject);
                            }
                            else {
                                singletonObject = this.singletonObjects.get(beanName);
                            }
                        }
                    }
                }
            }
            finally {
                this.singletonLock.unlock();
            }
        }
    }
    return singletonObject;
}
```

## 동작 흐름 (조회)

```text
 getSingleton(beanName, allowEarlyReference)
 |
 | [1] singletonObjects           완성된 싱글톤          --> 있으면 반환
 |
 +-- 없고, 이 빈이 "생성 중" 인가?
       [2] earlySingletonObjects  노출된 조기 참조       --> 있으면 반환
       [3] singletonFactories     조기 참조를 만들 팩토리
             allowEarlyReference == false --> 여기서 멈춤 (조기 참조 만들지 않음)
             잠금을 못 잡으면 null 반환   (생성 스레드 밖에서 조기 참조를 만들지 않기 위해)
             팩토리 호출 = getEarlyBeanReference
               --> SmartInstantiationAwareBeanPostProcessor 가 필요하면 프록시를 만들어 돌려줌
             결과를 [2] 로 옮기고 [3] 에서 제거
```

세 단계로 나뉜 이유는 순환 참조 때문이다. A가 B를 주입받고 B가 A를 주입받을 때, A는 아직 초기화 중이지만 B에게 넘길 참조가 필요하다. 이때 [3]의 팩토리가 "지금 시점의 A"(필요하면 프록시)를 만들어 [2]에 올린다.

## 실제 코드 (생성)

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultSingletonBeanRegistry.java` L255-L350 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultSingletonBeanRegistry.java#L255-L350))

```java
// DefaultSingletonBeanRegistry.java L255-L350
public Object getSingleton(String beanName, ObjectFactory<?> singletonFactory) {
    Assert.notNull(beanName, "Bean name must not be null");

    Thread currentThread = Thread.currentThread();
    Boolean lockFlag = isCurrentThreadAllowedToHoldSingletonLock();
    boolean acquireLock = !Boolean.FALSE.equals(lockFlag);
    boolean locked = (acquireLock && this.singletonLock.tryLock());

    try {
        Object singletonObject = this.singletonObjects.get(beanName);
        if (singletonObject == null) {
            if (acquireLock && !locked) {
                if (Boolean.TRUE.equals(lockFlag)) {
                    // Another thread is busy in a singleton factory callback, potentially blocked.
                    // Fallback as of 6.2: process given singleton bean outside of singleton lock.
                    // Thread-safe exposure is still guaranteed, there is just a risk of collisions
                    // when triggering creation of other beans as dependencies of the current bean.
                    this.lenientCreationLock.lock();
                    try {
                        if (logger.isInfoEnabled()) {
                            Set<String> lockedBeans = new HashSet<>(this.singletonsCurrentlyInCreation);
                            lockedBeans.removeAll(this.singletonsInLenientCreation);
                            logger.info("Obtaining singleton bean '" + beanName + "' in thread \"" +
                                    currentThread.getName() + "\" while other thread holds singleton " +
                                    "lock for other beans " + lockedBeans);
                        }
                        this.singletonsInLenientCreation.add(beanName);
                    }
                    finally {
                        this.lenientCreationLock.unlock();
                    }
                }
                else {
                    // No specific locking indication (outside a coordinated bootstrap) and
                    // singleton lock currently held by some other creation method -> wait.
                    this.singletonLock.lock();
                    locked = true;
                    // Singleton object might have possibly appeared in the meantime.
                    singletonObject = this.singletonObjects.get(beanName);
                    if (singletonObject != null) {
                        return singletonObject;
                    }
                }
            }

            if (this.singletonsCurrentlyInDestruction) {
                throw new BeanCreationNotAllowedException(beanName,
                        "Singleton bean creation not allowed while singletons of this factory are in destruction " +
                        "(Do not request a bean from a BeanFactory in a destroy method implementation!)");
            }
            if (logger.isDebugEnabled()) {
                logger.debug("Creating shared instance of singleton bean '" + beanName + "'");
            }

            try {
                beforeSingletonCreation(beanName);
            }
            catch (BeanCurrentlyInCreationException ex) {
                this.lenientCreationLock.lock();
                try {
                    while ((singletonObject = this.singletonObjects.get(beanName)) == null) {
                        Thread otherThread = this.currentCreationThreads.get(beanName);
                        if (otherThread != null && (otherThread == currentThread ||
                                checkDependentWaitingThreads(otherThread, currentThread))) {
                            throw ex;
                        }
                        if (!this.singletonsInLenientCreation.contains(beanName)) {
                            break;
                        }
                        if (otherThread != null) {
                            this.lenientWaitingThreads.put(currentThread, otherThread);
                        }
                        try {
                            this.lenientCreationFinished.await();
                        }
                        catch (InterruptedException ie) {
                            currentThread.interrupt();
                        }
                        finally {
                            if (otherThread != null) {
                                this.lenientWaitingThreads.remove(currentThread);
                            }
                        }
                    }
                }
                finally {
                    this.lenientCreationLock.unlock();
                }
                if (singletonObject != null) {
                    return singletonObject;
                }
                if (locked) {
                    throw ex;
                }
                // Try late locking for waiting on specific bean to be finished.
                this.singletonLock.lock();
```

## 동작 흐름 (생성)

```text
 getSingleton(beanName, singletonFactory)
 |
 | L259 이 스레드가 싱글톤 잠금을 잡아도 되는가   (기동 부트스트랩 병렬 생성 판단)
 |        MAIN 스레드 --> 잡아도 됨 / BACKGROUND --> 잡으면 안 됨
 | L261 tryLock
 |
 +-- L264 singletonObjects 재확인 --> 있으면 반환
 |
 +-- 잠금을 못 잡았고 잠금이 허용된 경우
 |     다른 스레드가 팩토리 콜백 안에서 오래 걸리는 중
 |     --> 6.2 부터는 잠금 밖에서 진행 (lenient creation) + info 로그
 |     허용 여부가 미정이면 --> 잠금을 기다림
 |
 | L300 컨테이너가 파괴 중 --> BeanCreationNotAllowedException
 | L310 beforeSingletonCreation(beanName)
 |        singletonsCurrentlyInCreation 에 추가 (이미 있으면 BeanCurrentlyInCreationException)
 |
 +-- singletonFactory.getObject()      = createBean 호출
 |
 | L399 finally afterSingletonCreation   "생성 중" 표시 제거
 | L404 addSingleton(beanName, 결과)
 |        singletonObjects 에 넣고 singletonFactories / earlySingletonObjects 에서 제거
```

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultSingletonBeanRegistry.java` L159-L173 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultSingletonBeanRegistry.java#L159-L173))

```java
// DefaultSingletonBeanRegistry.java L159-L173
protected void addSingleton(String beanName, Object singletonObject) {
    Object oldObject = this.singletonObjects.putIfAbsent(beanName, singletonObject);
    if (oldObject != null) {
        throw new IllegalStateException("Could not register object [" + singletonObject +
                "] under bean name '" + beanName + "': there is already object [" + oldObject + "] bound");
    }
    this.singletonFactories.remove(beanName);
    this.earlySingletonObjects.remove(beanName);
    this.registeredSingletons.add(beanName);

    Consumer<Object> callback = this.singletonCallbacks.get(beanName);
    if (callback != null) {
        callback.accept(singletonObject);
    }
}
```

## 결과가 쓰이는 곳

```text
 singletonsCurrentlyInCreation 표시
      --> 조회용 getSingleton 의 [2][3] 진입 조건
      --> 같은 빈을 다시 만들려 하면 BeanCurrentlyInCreationException (생성자 순환 참조 감지)

 addSingleton 후의 캐시 상태
      --> 조회용 [1] 에서 즉시 반환
      --> 조기 참조 자료구조는 비워짐 (더 필요 없음)

 조기 참조로 나간 객체 (earlySingletonObjects)
      --> doCreateBean 끝에서 "최종 객체와 다른가" 검사
          다르고 이미 다른 빈에 주입됐으면 BeanCurrentlyInCreationException 으로 실패
          (다른 빈이 프록시가 아닌 원본을 들고 있게 되는 상황 차단)
```
