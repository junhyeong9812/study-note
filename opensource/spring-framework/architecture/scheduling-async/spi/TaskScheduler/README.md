# TaskScheduler

상위: [Spring 스케줄링과 비동기](../../README.md) / [spi](../README.md)

시각과 주기를 알고 작업을 실행하는 쪽이다. 단순 실행만 하는 `TaskExecutor`와 달리 "언제"를 다룬다.

## 실제 코드

`spring-context` / `org.springframework.scheduling` / `TaskScheduler.java` L51-L247 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/scheduling/TaskScheduler.java#L51-L247))

```java
// TaskScheduler.java L51-L247
public interface TaskScheduler {

    default Clock getClock() {
        return Clock.systemDefaultZone();
    }

    @Nullable ScheduledFuture<?> schedule(Runnable task, Trigger trigger);

    ScheduledFuture<?> schedule(Runnable task, Instant startTime);

    @Deprecated(since = "6.0")
    default ScheduledFuture<?> schedule(Runnable task, Date startTime) {
        return schedule(task, startTime.toInstant());
    }

    ScheduledFuture<?> scheduleAtFixedRate(Runnable task, Instant startTime, Duration period);

    @Deprecated(since = "6.0")
    default ScheduledFuture<?> scheduleAtFixedRate(Runnable task, Date startTime, long period) {
        return scheduleAtFixedRate(task, startTime.toInstant(), Duration.ofMillis(period));
    }

    ScheduledFuture<?> scheduleAtFixedRate(Runnable task, Duration period);

    @Deprecated(since = "6.0")
    default ScheduledFuture<?> scheduleAtFixedRate(Runnable task, long period) {
        return scheduleAtFixedRate(task, Duration.ofMillis(period));
    }

    ScheduledFuture<?> scheduleWithFixedDelay(Runnable task, Instant startTime, Duration delay);

    @Deprecated(since = "6.0")
    default ScheduledFuture<?> scheduleWithFixedDelay(Runnable task, Date startTime, long delay) {
        return scheduleWithFixedDelay(task, startTime.toInstant(), Duration.ofMillis(delay));
    }

    ScheduledFuture<?> scheduleWithFixedDelay(Runnable task, Duration delay);

    @Deprecated(since = "6.0")
    default ScheduledFuture<?> scheduleWithFixedDelay(Runnable task, long delay) {
        return scheduleWithFixedDelay(task, Duration.ofMillis(delay));
    }

}
```

## 흐름에서 불리는 자리

```text
 finishRegistration
   scheduler 지정이 있으면 그것, 없으면 TaskSchedulerRouter
 ScheduledTaskRegistrar.scheduleTasks
   taskScheduler.schedule(작업, 트리거)          cron
   scheduleWithFixedDelay / scheduleAtFixedRate  고정 지연/주기
```

- [finishRegistration](../../02_ScheduledAnnotationBeanPostProcessor.finishRegistration/README.md)

## 구현 계층

```text
 TaskScheduler
   +-- ThreadPoolTaskScheduler        ScheduledThreadPoolExecutor 기반 (가장 흔함)
   +-- SimpleAsyncTaskScheduler       작업마다 새 스레드 (가상 스레드 지원)
   +-- ConcurrentTaskScheduler        기존 ScheduledExecutorService 를 감싼다
   +-- TaskSchedulerRouter            @Scheduled(scheduler = "이름") 라우팅
   +-- DefaultManagedTaskScheduler    JNDI (Jakarta EE)

 기본값 주의
   전용 빈이 없으면 단일 스레드 스케줄러가 쓰인다
   작업 하나가 길어지면 다른 작업이 밀린다 --> poolSize 설정
```
