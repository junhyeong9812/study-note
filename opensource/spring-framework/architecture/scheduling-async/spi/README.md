# spi

상위: [Spring 스케줄링과 비동기](../README.md)

두 흐름이 기대는 인터페이스다. 스케줄링은 "언제"(TaskScheduler, Trigger)를, 비동기는 "어디서"(TaskExecutor)를 다루고, 각각 설정 훅과 오류 정책이 붙는다.

```text
 @Scheduled
   등록 ............ SchedulingConfigurer (마지막 조정 기회)
   주기 계산 ....... Trigger
   실행 ............ TaskScheduler
 @Async
   실행 ............ TaskExecutor / AsyncTaskExecutor
   오류 ............ AsyncUncaughtExceptionHandler (void 반환일 때)
```

## 하위 인터페이스

- [TaskScheduler](TaskScheduler/README.md)
- [Trigger](Trigger/README.md)
- [TaskExecutor](TaskExecutor/README.md)
- [AsyncUncaughtExceptionHandler](AsyncUncaughtExceptionHandler/README.md)
- [SchedulingConfigurer](SchedulingConfigurer/README.md)
