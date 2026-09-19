# Trigger

상위: [Spring 스케줄링과 비동기](../../README.md) / [spi](../README.md)

다음 실행 시각을 계산한다. cron 스케줄이 이 인터페이스로 표현된다.

## 실제 코드

`spring-context` / `org.springframework.scheduling` / `Trigger.java` L33-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/scheduling/Trigger.java#L33-L60))

```java
// Trigger.java L33-L60
public interface Trigger {

    @Deprecated(since = "6.0")
    default @Nullable Date nextExecutionTime(TriggerContext triggerContext) {
        Instant instant = nextExecution(triggerContext);
        return (instant != null ? Date.from(instant) : null);
    }

    @Nullable Instant nextExecution(TriggerContext triggerContext);

}
```

## 흐름에서 불리는 자리

```text
 processScheduled
   cron 속성 --> CronTrigger 생성 --> CronTask --> registrar.scheduleCronTask
 실행 시마다
   taskScheduler 가 trigger.nextExecution(triggerContext) 로 다음 시각을 묻는다
```

- [postProcessAfterInitialization](../../01_ScheduledAnnotationBeanPostProcessor.postProcessAfterInitialization/README.md)

## 구현 계층

```text
 Trigger
   +-- CronTrigger              cron 식 (초 단위 6필드)
   +-- PeriodicTrigger          고정 지연/주기를 트리거로 표현
   +-- (사용자 구현: 영업일만 실행 등)

 TriggerContext
   마지막 예정 시각, 실제 시작 시각, 완료 시각을 담는다
   fixedRate 와 fixedDelay 의 차이가 여기서 갈린다
```
