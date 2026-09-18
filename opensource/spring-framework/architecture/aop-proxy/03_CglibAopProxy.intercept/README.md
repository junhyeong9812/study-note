# CglibAopProxy.DynamicAdvisedInterceptor.intercept

상위: [Spring AOP 프록시](../README.md)

CGLIB 프록시(타깃의 하위 클래스)로 들어온 호출을 받는다. 하는 일은 JDK 프록시의 `invoke`와 같다. 인터셉터 체인을 구해 실행하고, 없으면 타깃을 바로 부른다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework` / `CglibAopProxy.java` L715-L756 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/CglibAopProxy.java#L715-L756))

```java
// CglibAopProxy.java L715-L756
public @Nullable Object intercept(Object proxy, Method method, Object[] args, MethodProxy methodProxy) throws Throwable {
    Object oldProxy = null;
    boolean setProxyContext = false;
    Object target = null;
    TargetSource targetSource = this.advised.getTargetSource();
    try {
        if (this.advised.isExposeProxy()) {
            // Make invocation available if necessary.
            oldProxy = AopContext.setCurrentProxy(proxy);
            setProxyContext = true;
        }
        // Get as late as possible to minimize the time we "own" the target, in case it comes from a pool...
        target = targetSource.getTarget();
        Class<?> targetClass = (target != null ? target.getClass() : null);
        List<Object> chain = this.advised.getInterceptorsAndDynamicInterceptionAdvice(method, targetClass);
        Object retVal;
        // Check whether we only have one InvokerInterceptor: that is,
        // no real advice, but just reflective invocation of the target.
        if (chain.isEmpty()) {
            // We can skip creating a MethodInvocation: just invoke the target directly.
            // Note that the final invoker must be an InvokerInterceptor, so we know
            // it does nothing but a reflective operation on the target, and no hot
            // swapping or fancy proxying.
            @Nullable Object[] argsToUse = AopProxyUtils.adaptArgumentsIfNecessary(method, args);
            retVal = AopUtils.invokeJoinpointUsingReflection(target, method, argsToUse);
        }
        else {
            // We need to create a method invocation...
            retVal = new ReflectiveMethodInvocation(proxy, target, method, args, targetClass, chain).proceed();
        }
        return processReturnType(proxy, target, method, args, retVal);
    }
    finally {
        if (target != null && !targetSource.isStatic()) {
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
 intercept(proxy, method, args, methodProxy)
 |
 | L721 exposeProxy 설정이면 AopContext 에 프록시 노출
 | L727 target = targetSource.getTarget()
 | L729 chain = advised.getInterceptorsAndDynamicInterceptionAdvice(method, targetClass)
 |
 +-- L733 체인이 비어 있음 --> 타깃 메서드 리플렉션 호출
 +-- L741 체인이 있음      --> ReflectiveMethodInvocation(...).proceed()
 |
 | L745 processReturnType   this 반환 보정, 원시 타입 null 검사
 |
 +-- finally  타깃 반환(비정적 TargetSource), AopContext 복원
```

JDK 경로와의 차이는 다음과 같다.

```text
 JdkDynamicAopProxy.invoke        InvocationHandler 구현, 인터페이스 메서드만 도착
   equals/hashCode/Advised 계열을 직접 처리

 DynamicAdvisedInterceptor        CGLIB Callback 구현, 오버라이드 가능한 모든 메서드 도착
   equals/hashCode/Advised 계열은 별도 Callback 으로 분리되어 여기에 오지 않는다
   final, private, static 메서드는 오버라이드가 불가능해 가로채지 못한다
```

체인 실행은 JDK 경로와 같은 [ReflectiveMethodInvocation.proceed](../02_JdkDynamicAopProxy.invoke/02_ReflectiveMethodInvocation.proceed/README.md)를 쓰고, 인터셉터 목록도 같은 [getInterceptorsAndDynamicInterceptionAdvice](../02_JdkDynamicAopProxy.invoke/01_AdvisedSupport.getInterceptorsAndDynamicInterceptionAdvice/README.md)로 구한다.

## 결과가 쓰이는 곳

```text
 반환값
      --> processReturnType 을 거쳐 호출자에게

 가로채지 못하는 메서드
      final / private / static --> 어드바이스 없이 타깃 구현이 그대로 실행
      = @Transactional 을 final 메서드에 붙이면 조용히 동작하지 않는다

 타깃 인스턴스
      --> 프록시와 타깃은 서로 다른 객체다
          프록시의 필드는 초기화되지 않은 상태이고, 모든 호출은 타깃으로 위임된다
```
