# InvocableHandlerMethod.doInvoke

상위: [ServletInvocableHandlerMethod.invokeAndHandle](../README.md)

여기서 비로소 사용자가 작성한 컨트롤러 메서드가 실행된다. 리플렉션(`Method.invoke`)으로 부르고, 리플렉션이 감싼 예외를 벗겨 원래 예외를 그대로 던진다.

## 실제 코드

`spring-web` / `org.springframework.web.method.support` / `InvocableHandlerMethod.java` L243-L276 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/web/method/support/InvocableHandlerMethod.java#L243-L276))

```java
// InvocableHandlerMethod.java L243-L276
protected @Nullable Object doInvoke(@Nullable Object... args) throws Exception {
    Method method = getBridgedMethod();
    try {
        if (KOTLIN_REFLECT_PRESENT && KotlinDetector.isKotlinType(method.getDeclaringClass())) {
            if (KotlinDetector.isSuspendingFunction(method)) {
                return invokeSuspendingFunction(method, getBean(), args);
            }
            return KotlinDelegate.invokeFunction(method, getBean(), args);
        }
        return method.invoke(getBean(), args);
    }
    catch (IllegalArgumentException ex) {
        assertTargetBean(method, getBean(), args);
        String text = (ex.getMessage() == null || ex.getCause() instanceof NullPointerException) ?
                "Illegal argument" : ex.getMessage();
        throw new IllegalStateException(formatInvokeError(text, args), ex);
    }
    catch (InvocationTargetException ex) {
        // Unwrap for HandlerExceptionResolvers ...
        Throwable targetException = ex.getCause();
        if (targetException instanceof RuntimeException runtimeException) {
            throw runtimeException;
        }
        else if (targetException instanceof Error error) {
            throw error;
        }
        else if (targetException instanceof Exception exception) {
            throw exception;
        }
        else {
            throw new IllegalStateException(formatInvokeError("Invocation failure", args), targetException);
        }
    }
}
```

## 동작 흐름

```text
 doInvoke(args)
 |
 | L244 method = getBridgedMethod()     제네릭 브리지 메서드면 실제 구현 메서드로
 |
 +-- Kotlin 클래스인가?  (kotlin-reflect가 클래스패스에 있을 때만 검사)
 |     suspend 함수 --> invokeSuspendingFunction --> 코루틴을 Mono로 감싸 반환 --> 비동기 처리
 |     일반 함수    --> KotlinDelegate.invokeFunction  (선택 인자 생략, inline value class 처리)
 |
 +-- L252 method.invoke(bean, args)     <-- 사용자 컨트롤러 코드 실행
 |
 +-- catch IllegalArgumentException     인자 타입/개수가 안 맞음
 |     assertTargetBean()   (HandlerMethod L417)
 |       빈이 컨트롤러 클래스의 인스턴스가 아님  (JDK 인터페이스 프록시인 경우)
 |       --> IllegalStateException("... please use class-based proxying")
 |     그 밖 --> IllegalStateException("Illegal argument" + 인자 목록)
 |
 +-- catch InvocationTargetException    컨트롤러 안에서 던진 예외
       getCause() 를 꺼내서
         RuntimeException --> 그대로 던짐
         Error            --> 그대로 던짐
         checked Exception --> 그대로 던짐
         그 밖 Throwable  --> IllegalStateException으로 감쌈
```

## 결과가 쓰이는 곳

```text
 반환값
      --> invokeForRequest --> (반환값 검증) --> invokeAndHandle의 returnValue
                                             --> handleReturnValue

 벗겨서 던진 원래 예외 (예: 컨트롤러의 throw new UserNotFoundException())
      --> invokeAndHandle 밖으로 --> invokeHandlerMethod --> ha.handle --> doDispatch
      --> dispatchException
      --> ExceptionHandlerExceptionResolver가 "UserNotFoundException"으로 @ExceptionHandler 검색
          (InvocationTargetException으로 감싼 채 던졌다면 타입 매칭이 안 됐을 것)
```

`@Transactional` 같은 AOP가 걸린 컨트롤러면 `bean`은 프록시이고, `method.invoke`는 프록시를 거쳐 실제 객체에 도달한다.
