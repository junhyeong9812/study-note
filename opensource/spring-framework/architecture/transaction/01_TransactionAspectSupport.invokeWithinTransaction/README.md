# TransactionAspectSupport.invokeWithinTransaction

상위: [Spring 트랜잭션](../README.md)

트랜잭션 경계를 만드는 어라운드 어드바이스의 본체다. 속성을 찾고, 트랜잭션을 열고, 타깃을 부르고, 결과에 따라 커밋하거나 롤백하고, 스레드 상태를 정리한다.

## 진입: TransactionInterceptor.invoke

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionInterceptor.java` L122-L151 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionInterceptor.java#L122-L151))

```java
// TransactionInterceptor.java L122-L151
@Override
public @Nullable Object invoke(MethodInvocation invocation) throws Throwable {
    // Work out the target class: may be {@code null}.
    // The TransactionAttributeSource should be passed the target class
    // as well as the method, which may be from an interface.
    Class<?> targetClass = (invocation.getThis() != null ? AopUtils.getTargetClass(invocation.getThis()) : null);

    // Adapt to TransactionAspectSupport's invokeWithinTransaction...
    return invokeWithinTransaction(invocation.getMethod(), targetClass, new InvocationCallback() {
        @Override
        public @Nullable Object proceedWithInvocation() throws Throwable {
            return invocation.proceed();
        }
        @Override
        public void onRollback(Throwable failure, TransactionExecution execution) {
            MethodRollbackEvent event = new MethodRollbackEvent(invocation, failure, execution);
            logger.trace(event, failure);
            if (applicationEventPublisher != null) {
                try {
                    applicationEventPublisher.publishEvent(event);
                }
                catch (Throwable ex) {
                    if (logger.isWarnEnabled()) {
                        logger.warn("Failed to publish " + event, ex);
                    }
                }
            }
        }
    });
}
```

## 실제 코드

`spring-tx` / `org.springframework.transaction.interceptor` / `TransactionAspectSupport.java` L333-L473 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L333-L473))

```java
// TransactionAspectSupport.java L333-L473
protected @Nullable Object invokeWithinTransaction(Method method, @Nullable Class<?> targetClass,
        final InvocationCallback invocation) throws Throwable {

    // If the transaction attribute is null, the method is non-transactional.
    TransactionAttributeSource tas = getTransactionAttributeSource();
    final TransactionAttribute txAttr = (tas != null ? tas.getTransactionAttribute(method, targetClass) : null);
    final TransactionManager tm = determineTransactionManager(txAttr, targetClass);

    if (this.reactiveAdapterRegistry != null && tm instanceof ReactiveTransactionManager rtm) {
        boolean isSuspendingFunction = KotlinDetector.isSuspendingFunction(method);
        boolean hasSuspendingFlowReturnType = isSuspendingFunction &&
                COROUTINES_FLOW_CLASS_NAME.equals(new MethodParameter(method, -1).getParameterType().getName());

        ReactiveTransactionSupport txSupport = this.transactionSupportCache.computeIfAbsent(method, key -> {
            Class<?> reactiveType =
                    (isSuspendingFunction ? (hasSuspendingFlowReturnType ? Flux.class : Mono.class) : method.getReturnType());
            ReactiveAdapter adapter = this.reactiveAdapterRegistry.getAdapter(reactiveType);
            if (adapter == null) {
                throw new IllegalStateException("Cannot apply reactive transaction to non-reactive return type [" +
                        method.getReturnType() + "] with specified transaction manager: " + tm);
            }
            return new ReactiveTransactionSupport(adapter);
        });

        return txSupport.invokeWithinTransaction(method, targetClass, invocation, txAttr, rtm);
    }

    PlatformTransactionManager ptm = asPlatformTransactionManager(tm);
    final String joinpointIdentification = methodIdentification(method, targetClass, txAttr);

    if (txAttr == null || !(ptm instanceof CallbackPreferringPlatformTransactionManager cpptm)) {
        // Standard transaction demarcation with getTransaction and commit/rollback calls.
        TransactionInfo txInfo = createTransactionIfNecessary(ptm, txAttr, joinpointIdentification);

        Object retVal;
        try {
            // This is an around advice: Invoke the next interceptor in the chain.
            // This will normally result in a target object being invoked.
            retVal = invocation.proceedWithInvocation();
        }
        catch (Throwable ex) {
            // target invocation exception
            completeTransactionAfterThrowing(txInfo, invocation, ex);
            throw ex;
        }
        finally {
            cleanupTransactionInfo(txInfo);
        }

        if (retVal != null && txAttr != null) {
            TransactionStatus status = txInfo.getTransactionStatus();
            if (status != null) {
                if (retVal instanceof Future<?> future && future.isDone()) {
                    try {
                        future.get();
                    }
                    catch (ExecutionException ex) {
                        Throwable cause = ex.getCause();
                        Assert.state(cause != null, "Cause must not be null");
                        if (txAttr.rollbackOn(cause)) {
                            invocation.onRollback(cause, status);
                            status.setRollbackOnly();
                        }
                    }
                    catch (InterruptedException ex) {
                        Thread.currentThread().interrupt();
                    }
                }
                else if (VAVR_PRESENT && VavrDelegate.isVavrTry(retVal)) {
                    // Set rollback-only in case of Vavr failure matching our rollback rules...
                    retVal = VavrDelegate.evaluateTryFailure(invocation, retVal, txAttr, status);
                }
            }
        }

        commitTransactionAfterReturning(txInfo);
        return retVal;
    }

    else {
        Object result;
        final ThrowableHolder throwableHolder = new ThrowableHolder();

        // It's a CallbackPreferringPlatformTransactionManager: pass a TransactionCallback in.
        try {
            result = cpptm.<@Nullable Object> execute(txAttr, status -> {
                TransactionInfo txInfo = prepareTransactionInfo(ptm, txAttr, joinpointIdentification, status);
                try {
                    Object retVal = invocation.proceedWithInvocation();
                    if (retVal != null && VAVR_PRESENT && VavrDelegate.isVavrTry(retVal)) {
                        // Set rollback-only in case of Vavr failure matching our rollback rules...
                        retVal = VavrDelegate.evaluateTryFailure(invocation, retVal, txAttr, status);
                    }
                    return retVal;
                }
                catch (Throwable ex) {
                    if (txAttr.rollbackOn(ex)) {
                        invocation.onRollback(ex, status);
                        // A RuntimeException: will lead to a rollback.
                        if (ex instanceof RuntimeException runtimeException) {
                            throw runtimeException;
                        }
                        else {
                            throw new ThrowableHolderException(ex);
                        }
                    }
                    else {
                        // A normal return value: will lead to a commit.
                        throwableHolder.throwable = ex;
                        return null;
                    }
                }
                finally {
                    cleanupTransactionInfo(txInfo);
                }
            });
        }
        catch (ThrowableHolderException ex) {
            throw ex.getCause();
        }
        catch (TransactionSystemException ex2) {
            if (throwableHolder.throwable != null) {
                logger.error("Application exception overridden by commit exception", throwableHolder.throwable);
                ex2.initApplicationException(throwableHolder.throwable);
            }
            throw ex2;
        }
        catch (Throwable ex2) {
            if (throwableHolder.throwable != null) {
                logger.error("Application exception overridden by commit exception", throwableHolder.throwable);
            }
            throw ex2;
        }

        // Check result state: It might indicate a Throwable to rethrow.
        if (throwableHolder.throwable != null) {
            throw throwableHolder.throwable;
        }
        return result;
    }
}
```

## 동작 흐름

```text
 invokeWithinTransaction(method, targetClass, invocation)
 |
 | L338 txAttr = TransactionAttributeSource.getTransactionAttribute(method, targetClass)
 |        @Transactional 을 찾는다. 클래스 -> 메서드 순으로 병합, 없으면 null
 |        null 이면 아래에서 트랜잭션 없이 그냥 통과한다
 | L339 tm = determineTransactionManager(txAttr)
 |        @Transactional(transactionManager = "이름") 또는 유일한 매니저 빈
 |
 +-- L341 리액티브 매니저 + 리액티브 반환 타입
 |      --> ReactiveTransactionSupport 로 위임 (이 지도의 범위 밖)
 |
 +-- L363 표준 경로
       L365 txInfo = createTransactionIfNecessary(ptm, txAttr, 조인포인트 이름)
       |
       | try  L371 retVal = invocation.proceedWithInvocation()
       |                     = 체인의 다음 인터셉터 또는 타깃 메서드
       |
       | catch L375 completeTransactionAfterThrowing(txInfo, ex) --> 예외 다시 던짐
       |
       | finally L379 cleanupTransactionInfo(txInfo)
       |
       | L382 반환값이 이미 완료된 Future 이고 그 안의 예외가 롤백 대상이면
       |        --> status.setRollbackOnly()
       |
       +-- L408 commitTransactionAfterReturning(txInfo)
              return retVal
```

1. [createTransactionIfNecessary](01_TransactionAspectSupport.createTransactionIfNecessary/README.md)가 트랜잭션을 열고 스레드에 정보를 건다.
2. [commitTransactionAfterReturning](02_TransactionAspectSupport.commitTransactionAfterReturning/README.md)이 정상 종료 시 커밋한다.
3. [completeTransactionAfterThrowing](03_TransactionAspectSupport.completeTransactionAfterThrowing/README.md)이 예외 시 롤백 여부를 판단한다.
4. [cleanupTransactionInfo](04_TransactionAspectSupport.cleanupTransactionInfo/README.md)가 ThreadLocal을 되돌린다.

## 결과가 쓰이는 곳

```text
 txAttr == null 인 경우
      --> 트랜잭션 없이 타깃만 실행
      --> "프록시는 씌워졌는데 트랜잭션이 없다" 는 상황의 정체
          (private 메서드, 내부 호출, 애노테이션 위치 오류)

 txInfo (TransactionInfo)
      --> ThreadLocal 스택에 쌓인다 (중첩 호출마다 push/pop)
      --> TransactionAspectSupport.currentTransactionStatus() 로 조회 가능
      --> cleanupTransactionInfo 가 이전 것을 복원

 retVal
      --> 체인을 거꾸로 타고 호출자에게
      --> 커밋은 반환 직전에 일어나므로, 커밋 실패는 호출자에게 예외로 보인다
```

## 하위 메서드

- [01 createTransactionIfNecessary](01_TransactionAspectSupport.createTransactionIfNecessary/README.md)
- [02 commitTransactionAfterReturning](02_TransactionAspectSupport.commitTransactionAfterReturning/README.md)
- [03 completeTransactionAfterThrowing](03_TransactionAspectSupport.completeTransactionAfterThrowing/README.md)
- [04 cleanupTransactionInfo](04_TransactionAspectSupport.cleanupTransactionInfo/README.md)
