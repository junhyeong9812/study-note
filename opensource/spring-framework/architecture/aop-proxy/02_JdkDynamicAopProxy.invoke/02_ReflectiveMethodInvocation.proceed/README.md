# ReflectiveMethodInvocation.proceed

상위: [JdkDynamicAopProxy.invoke](../README.md)

인터셉터 체인을 실행한다. 자기 자신을 인터셉터에게 넘기고, 인터셉터가 다시 `proceed()`를 부르면 다음 인터셉터로 넘어간다. 끝에 도달하면 타깃의 실제 메서드를 호출한다.

## 실제 코드

`spring-aop` / `org.springframework.aop.framework` / `ReflectiveMethodInvocation.java` L155-L181 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/ReflectiveMethodInvocation.java#L155-L181))

```java
// ReflectiveMethodInvocation.java L155-L181
public @Nullable Object proceed() throws Throwable {
    // We start with an index of -1 and increment early.
    if (this.currentInterceptorIndex == this.interceptorsAndDynamicMethodMatchers.size() - 1) {
        return invokeJoinpoint();
    }

    Object interceptorOrInterceptionAdvice =
            this.interceptorsAndDynamicMethodMatchers.get(++this.currentInterceptorIndex);
    if (interceptorOrInterceptionAdvice instanceof InterceptorAndDynamicMethodMatcher dm) {
        // Evaluate dynamic method matcher here: static part will already have
        // been evaluated and found to match.
        Class<?> targetClass = (this.targetClass != null ? this.targetClass : this.method.getDeclaringClass());
        if (dm.matcher().matches(this.method, targetClass, this.arguments)) {
            return dm.interceptor().invoke(this);
        }
        else {
            // Dynamic matching failed.
            // Skip this interceptor and invoke the next in the chain.
            return proceed();
        }
    }
    else {
        // It's an interceptor, so we just invoke it: The pointcut will have
        // been evaluated statically before this object was constructed.
        return ((MethodInterceptor) interceptorOrInterceptionAdvice).invoke(this);
    }
}
```

`spring-aop` / `org.springframework.aop.framework` / `ReflectiveMethodInvocation.java` L189-L191 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/framework/ReflectiveMethodInvocation.java#L189-L191))

```java
// ReflectiveMethodInvocation.java L189-L191
protected @Nullable Object invokeJoinpoint() throws Throwable {
    return AopUtils.invokeJoinpointUsingReflection(this.target, this.method, this.arguments);
}
```

## 동작 흐름

```text
 proceed()
 |
 +-- L157 인덱스가 마지막에 도달 --> invokeJoinpoint()
 |                                   = 타깃 메서드를 리플렉션으로 호출
 |
 +-- L162 다음 요소를 꺼낸다 (인덱스 증가)
       |
       +-- InterceptorAndDynamicMethodMatcher (동적 매처)
       |     이번 호출의 인자까지 보고 매칭 검사
       |       성공 --> 인터셉터 invoke(this)
       |       실패 --> 이 인터셉터를 건너뛰고 proceed() 재귀
       |
       +-- 일반 MethodInterceptor --> invoke(this)
```

체인이 [로깅 어드바이스, 트랜잭션 인터셉터]인 경우의 실행 순서다.

```text
 프록시.save()
   proceed()  #0 --> 로깅.invoke(mi)
                       "before" 출력
                       mi.proceed()  #1 --> 트랜잭션.invoke(mi)
                                              트랜잭션 시작
                                              mi.proceed()  #2 --> invokeJoinpoint()
                                                                     타깃.save() 실행
                                              커밋 또는 롤백
                       "after" 출력
   반환
```

트랜잭션 인터셉터가 하는 일은 [트랜잭션](../../../transaction/README.md) 흐름에서 이어진다.

호출 스택이 중첩되므로, 인터셉터는 타깃 호출 **앞**과 **뒤** 모두에서 일할 수 있다. `@Around` 어드바이스가 `proceed()`를 부르지 않으면 타깃은 실행되지 않는다.

## 결과가 쓰이는 곳

```text
 반환값
      --> 가장 바깥 인터셉터를 거쳐 invoke / intercept 로, 다시 호출자에게
      --> 중간 인터셉터가 값을 바꿀 수 있다 (캐시 어드바이스가 캐시 값을 대신 반환 등)

 currentInterceptorIndex
      --> 이 객체는 한 번의 호출 전용. 재사용하지 않는다
      --> 비동기 어드바이스가 invocation 을 다른 스레드로 넘길 때는 복제(invocableClone)를 쓴다

 예외
      --> 타깃이 던진 예외가 체인을 거꾸로 타고 올라간다
          트랜잭션 인터셉터는 이때 롤백 여부를 판단한다
```
