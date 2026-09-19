# AsyncUncaughtExceptionHandler

상위: [Spring 스케줄링과 비동기](../../README.md) / [spi](../README.md)

`void`를 반환하는 `@Async` 메서드에서 난 예외를 어디로 보낼지 정한다. 호출자에게 전달할 방법이 없기 때문에 필요한 장치다.

## 실제 코드

`spring-aop` / `org.springframework.aop.interceptor` / `AsyncUncaughtExceptionHandler.java` L35-L45 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-aop/src/main/java/org/springframework/aop/interceptor/AsyncUncaughtExceptionHandler.java#L35-L45))

```java
// AsyncUncaughtExceptionHandler.java L35-L45
public interface AsyncUncaughtExceptionHandler {

    void handleUncaughtException(Throwable ex, Method method, @Nullable Object... params);

}
```

## 흐름에서 불리는 자리

```text
 AsyncExecutionAspectSupport.handleError (L306)
   반환 타입이 Future --> 예외를 다시 던져 Future 에 담는다
   void               --> exceptionHandler.handleUncaughtException(ex, method, params)
```

- [AsyncExecutionInterceptor.invoke](../../03_AsyncExecutionInterceptor.invoke/README.md)

## 구현 계층

```text
 AsyncUncaughtExceptionHandler
   +-- SimpleAsyncUncaughtExceptionHandler    오류 로그만 남긴다 (기본)
   +-- (사용자 구현: 알림, 지표 기록 등)

 등록
   AsyncConfigurer.getAsyncUncaughtExceptionHandler()

 알아 둘 점
   void @Async 메서드의 실패는 기본적으로 로그에만 남는다
   실패를 감지해야 한다면 Future 를 반환하거나 핸들러를 등록한다
```
