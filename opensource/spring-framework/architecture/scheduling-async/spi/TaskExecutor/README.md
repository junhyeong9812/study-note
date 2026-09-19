# TaskExecutor

상위: [Spring 스케줄링과 비동기](../../README.md) / [spi](../README.md)

작업 하나를 실행하는 가장 단순한 계약이다. `@Async`가 최종적으로 기대는 곳이고, `AsyncTaskExecutor`가 결과를 받는 제출 메서드를 더한다.

## 실제 코드

`spring-core` / `org.springframework.core.task` / `TaskExecutor.java` L39-L52 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/task/TaskExecutor.java#L39-L52))

```java
// TaskExecutor.java L39-L52
public interface TaskExecutor extends Executor {

    @Override
    void execute(Runnable task);

}
```

`spring-core` / `org.springframework.core.task` / `AsyncTaskExecutor.java` L43-L136 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/task/AsyncTaskExecutor.java#L43-L136))

```java
// AsyncTaskExecutor.java L43-L136
public interface AsyncTaskExecutor extends TaskExecutor {

    @Deprecated(since = "5.3.16")
    long TIMEOUT_IMMEDIATE = 0;

    @Deprecated(since = "5.3.16")
    long TIMEOUT_INDEFINITE = Long.MAX_VALUE;

    @Deprecated(since = "5.3.16")
    default void execute(Runnable task, long startTimeout) {
        execute(task);
    }

    default Future<?> submit(Runnable task) {
        FutureTask<Object> future = new FutureTask<>(task, null);
        execute(future);
        return future;
    }

    default <T extends @Nullable Object> Future<T> submit(Callable<T> task) {
        FutureTask<T> future = new FutureTask<>(task);
        execute(future, TIMEOUT_INDEFINITE);
        return future;
    }

    default CompletableFuture<Void> submitCompletable(Runnable task) {
        return CompletableFuture.runAsync(task, this);
    }

    default <T extends @Nullable Object> CompletableFuture<T> submitCompletable(Callable<T> task) {
        return FutureUtils.callAsync(task, this);
    }

}
```

## 흐름에서 불리는 자리

```text
 AsyncExecutionInterceptor.invoke
   determineAsyncExecutor --> AsyncTaskExecutor
   doSubmit
     submitCompletable(task)  CompletableFuture 반환
     submit(task)             Future 또는 void
```

- [AsyncExecutionInterceptor.invoke](../../03_AsyncExecutionInterceptor.invoke/README.md)

## 구현 계층

```text
 TaskExecutor
   +-- AsyncTaskExecutor                    submit / submitCompletable
   |     +-- ThreadPoolTaskExecutor         ThreadPoolExecutor 기반 (가장 흔함)
   |     +-- SimpleAsyncTaskExecutor        작업마다 새 스레드, 가상 스레드 옵션
   |     +-- ConcurrentTaskExecutor         기존 Executor 를 감싼다
   |     +-- TaskExecutorAdapter            일반 Executor 를 AsyncTaskExecutor 로
   +-- SyncTaskExecutor                     호출 스레드에서 즉시 실행 (테스트용)

 TaskDecorator
   제출 작업을 감싸 문맥(MDC, 보안, 요청)을 복사하는 자리
```
