# JdkDynamicAopProxy.invoke

상위: [Spring AOP 프록시](../README.md)

JDK 동적 프록시의 모든 메서드 호출이 도착하는 곳이다. 특수 메서드를 먼저 처리하고, 타깃을 얻고, 이 메서드에 적용할 인터셉터 체인을 구해 실행한다. 체인이 비어 있으면 타깃을 바로 부른다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework` / `JdkDynamicAopProxy.java` L165-L255 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/JdkDynamicAopProxy.java#L165-L255))

```java
// JdkDynamicAopProxy.java L165-L255
@Override
public @Nullable Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
    Object oldProxy = null;
    boolean setProxyContext = false;

    TargetSource targetSource = this.advised.targetSource;
    Object target = null;

    try {
        if (!this.cache.equalsDefined && AopUtils.isEqualsMethod(method)) {
            // The target does not implement the equals(Object) method itself.
            return equals(args[0]);
        }
        else if (!this.cache.hashCodeDefined && AopUtils.isHashCodeMethod(method)) {
            // The target does not implement the hashCode() method itself.
            return hashCode();
        }
        else if (method.getDeclaringClass() == DecoratingProxy.class) {
            // There is only getDecoratedClass() declared -> dispatch to proxy config.
            return AopProxyUtils.ultimateTargetClass(this.advised);
        }
        else if (!this.advised.isOpaque() && method.getDeclaringClass().isInterface() &&
                method.getDeclaringClass().isAssignableFrom(Advised.class)) {
            // Service invocations on ProxyConfig with the proxy config...
            return AopUtils.invokeJoinpointUsingReflection(this.advised, method, args);
        }

        Object retVal;

        if (this.advised.isExposeProxy()) {
            // Make invocation available if necessary.
            oldProxy = AopContext.setCurrentProxy(proxy);
            setProxyContext = true;
        }

        // Get as late as possible to minimize the time we "own" the target,
        // in case it comes from a pool.
        target = targetSource.getTarget();
        Class<?> targetClass = (target != null ? target.getClass() : null);

        // Get the interception chain for this method.
        List<Object> chain = this.advised.getInterceptorsAndDynamicInterceptionAdvice(method, targetClass);

        // Check whether we have any advice. If we don't, we can fall back on direct
        // reflective invocation of the target, and avoid creating a MethodInvocation.
        if (chain.isEmpty()) {
            // We can skip creating a MethodInvocation: just invoke the target directly
            // Note that the final invoker must be an InvokerInterceptor so we know it does
            // nothing but a reflective operation on the target, and no hot swapping or fancy proxying.
            @Nullable Object[] argsToUse = AopProxyUtils.adaptArgumentsIfNecessary(method, args);
            retVal = AopUtils.invokeJoinpointUsingReflection(target, method, argsToUse);
        }
        else {
            // We need to create a method invocation...
            MethodInvocation invocation =
                    new ReflectiveMethodInvocation(proxy, target, method, args, targetClass, chain);
            // Proceed to the joinpoint through the interceptor chain.
            retVal = invocation.proceed();
        }

        // Massage return value if necessary.
        Class<?> returnType = method.getReturnType();
        if (retVal != null && retVal == target &&
                returnType != Object.class && returnType.isInstance(proxy) &&
                !RawTargetAccess.class.isAssignableFrom(method.getDeclaringClass())) {
            // Special case: it returned "this" and the return type of the method
            // is type-compatible. Note that we can't help if the target sets
            // a reference to itself in another returned object.
            retVal = proxy;
        }
        else if (retVal == null && returnType != void.class && returnType.isPrimitive()) {
            throw new AopInvocationException(
                    "Null return value from advice does not match primitive return type for: " + method);
        }
        if (COROUTINES_REACTOR_PRESENT && KotlinDetector.isSuspendingFunction(method)) {
            return COROUTINES_FLOW_CLASS_NAME.equals(new MethodParameter(method, -1).getParameterType().getName()) ?
                    CoroutinesUtils.asFlow(retVal) : CoroutinesUtils.awaitSingleOrNull(retVal, args[args.length - 1]);
        }
        return retVal;
    }
    finally {
        if (target != null && !targetSource.isStatic()) {
            // Must have come from TargetSource.
            targetSource.releaseTarget(target);
        }
        if (setProxyContext) {
            // Restore old proxy.
            AopContext.setCurrentProxy(oldProxy);
        }
    }
}
```

## 동작 흐름

```text
 invoke(proxy, method, args)
 |
 | [1] 특수 메서드                                          L174-L190
 |       equals / hashCode 가 프록시 대상 인터페이스에 선언돼 있지 않으면 프록시가 처리
 |       DecoratingProxy.getDecoratedClass --> 타깃 클래스
 |       Advised 계열 인터페이스 호출      --> 프록시 설정 객체로 위임
 |
 | [2] L194 exposeProxy 설정이면 AopContext 에 현재 프록시를 넣는다
 |       --> 타깃 코드에서 AopContext.currentProxy() 로 자기 프록시를 얻어
 |           내부 호출도 어드바이스를 태울 수 있다
 |
 | [3] L202 target = targetSource.getTarget()
 |       가능한 늦게 얻는다 (풀링 타깃 소스를 오래 점유하지 않기 위해)
 |
 | [4] L206 chain = advised.getInterceptorsAndDynamicInterceptionAdvice(method, targetClass)
 |
 +-- [5] 체인이 비어 있음                                    L210
 |       --> 타깃 메서드를 리플렉션으로 바로 호출 (MethodInvocation 객체를 만들지 않음)
 |
 +-- [6] 체인이 있음                                         L217
 |       ReflectiveMethodInvocation 생성 --> proceed()
 |
 | [7] 반환값 보정                                           L226-L238
 |       타깃이 this 를 반환했고 타입이 맞으면 --> 프록시로 바꿔 반환
 |         (체이닝 API 가 프록시를 벗어나지 않게)
 |       원시 타입 반환인데 null --> AopInvocationException
 |
 +-- finally  타깃 반환(풀), AopContext 복원
```

1. 인터셉터 목록 구성은 [getInterceptorsAndDynamicInterceptionAdvice](01_AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice/README.md)가 한다.
2. 체인 실행은 [ReflectiveMethodInvocation.proceed](02_ReflectiveMethodInvocation.proceed/README.md)가 한다.

## 결과가 쓰이는 곳

```text
 반환값
      --> 호출한 쪽이 받는 값. 어드바이스가 바꿨다면 바뀐 값

 [5] 의 지름길
      --> 어드바이스가 맞지 않는 메서드는 프록시 비용이 거의 없다
          (프록시가 씌워졌다고 모든 메서드가 느려지지 않는 이유)

 [2] 의 AopContext
      --> 기본값은 꺼져 있다
          그래서 같은 객체 안에서 this.otherMethod() 를 부르면
          프록시를 거치지 않아 @Transactional 이 적용되지 않는다
```

## 하위 메서드

- [01 AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice](01_AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice/README.md)
- [02 ReflectiveMethodInvocation.proceed](02_ReflectiveMethodInvocation.proceed/README.md)
