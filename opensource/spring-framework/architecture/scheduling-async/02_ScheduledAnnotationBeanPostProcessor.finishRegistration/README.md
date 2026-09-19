# ScheduledAnnotationBeanPostProcessor.finishRegistration

상위: [Spring 스케줄링과 비동기](../README.md)

모아 둔 작업을 실제로 스케줄에 올린다. 쓸 스케줄러를 정하고, `SchedulingConfigurer` 빈들에게 조정할 기회를 준 뒤, 등록기를 초기화한다.

## 실제 코드

`spring-context` / `org.springframework.scheduling.annotation` / `ScheduledAnnotationBeanPostProcessor.java` L235-L244 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/scheduling/annotation/ScheduledAnnotationBeanPostProcessor.java#L235-L244))

```java
// ScheduledAnnotationBeanPostProcessor.java L235-L244
@Override
public void afterSingletonsInstantiated() {
    // Remove resolved singleton classes from cache
    this.nonAnnotatedClasses.clear();

    if (this.applicationContext == null) {
        // Not running in an ApplicationContext -> register tasks early...
        finishRegistration();
    }
}
```

`spring-context` / `org.springframework.scheduling.annotation` / `ScheduledAnnotationBeanPostProcessor.java` L246-L267 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/scheduling/annotation/ScheduledAnnotationBeanPostProcessor.java#L246-L267))

```java
// ScheduledAnnotationBeanPostProcessor.java L246-L267
private void finishRegistration() {
    if (this.scheduler != null) {
        this.registrar.setScheduler(this.scheduler);
    }
    else {
        this.localScheduler = new TaskSchedulerRouter();
        this.localScheduler.setBeanName(this.beanName);
        this.localScheduler.setBeanFactory(this.beanFactory);
        this.registrar.setTaskScheduler(this.localScheduler);
    }

    if (this.beanFactory instanceof ListableBeanFactory lbf) {
        Map<String, SchedulingConfigurer> beans = lbf.getBeansOfType(SchedulingConfigurer.class);
        List<SchedulingConfigurer> configurers = new ArrayList<>(beans.values());
        AnnotationAwareOrderComparator.sort(configurers);
        for (SchedulingConfigurer configurer : configurers) {
            configurer.configureTasks(this.registrar);
        }
    }

    this.registrar.afterPropertiesSet();
}
```

등록기가 실제로 스케줄하는 지점이다.

`spring-context` / `org.springframework.scheduling.config` / `ScheduledTaskRegistrar.java` L427-L430 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/scheduling/config/ScheduledTaskRegistrar.java#L427-L430))

```java
// ScheduledTaskRegistrar.java L427-L430
@Override
public void afterPropertiesSet() {
    scheduleTasks();
}
```

`spring-context` / `org.springframework.scheduling.config` / `ScheduledTaskRegistrar.java` L436-L481 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/scheduling/config/ScheduledTaskRegistrar.java#L436-L481))

```java
// ScheduledTaskRegistrar.java L436-L481
protected void scheduleTasks() {
    if (this.taskScheduler == null) {
        this.localExecutor = Executors.newSingleThreadScheduledExecutor();
        this.taskScheduler = new ConcurrentTaskScheduler(this.localExecutor);
    }
    if (this.triggerTasks != null) {
        for (TriggerTask task : this.triggerTasks) {
            addScheduledTask(scheduleTriggerTask(task));
        }
    }
    if (this.cronTasks != null) {
        for (CronTask task : this.cronTasks) {
            addScheduledTask(scheduleCronTask(task));
        }
    }
    if (this.fixedRateTasks != null) {
        for (IntervalTask task : this.fixedRateTasks) {
            if (task instanceof FixedRateTask fixedRateTask) {
                addScheduledTask(scheduleFixedRateTask(fixedRateTask));
            }
            else {
                addScheduledTask(scheduleFixedRateTask(new FixedRateTask(task)));
            }
        }
    }
    if (this.fixedDelayTasks != null) {
        for (IntervalTask task : this.fixedDelayTasks) {
            if (task instanceof FixedDelayTask fixedDelayTask) {
                addScheduledTask(scheduleFixedDelayTask(fixedDelayTask));
            }
            else {
                addScheduledTask(scheduleFixedDelayTask(new FixedDelayTask(task)));
            }
        }
    }
    if (this.oneTimeTasks != null) {
        for (DelayedTask task : this.oneTimeTasks) {
            if (task instanceof OneTimeTask oneTimeTask) {
                addScheduledTask(scheduleOneTimeTask(oneTimeTask));
            }
            else {
                addScheduledTask(scheduleOneTimeTask(new OneTimeTask(task)));
            }
        }
    }
}
```

## 동작 흐름

```text
 언제 불리나
   afterSingletonsInstantiated (L236)
     ApplicationContext 밖에서 쓰일 때만 즉시 등록
   onApplicationEvent(ContextRefreshedEvent) (L654)
     컨텍스트 안이면 refresh 완료 이벤트를 받고 등록
     --> 다른 ContextRefreshedEvent 리스너와 같은 시점에 일을 할 수 있게 미룬다

 finishRegistration()
 |
 +-- L247 scheduler 가 명시 설정돼 있으면 그것을 사용
 |      없으면 TaskSchedulerRouter 를 만들어 registrar 에 설정
 |        호출 시점에 빈 팩토리에서 TaskScheduler 를 찾아 라우팅한다
 |        (이름/타입으로 찾고, 없으면 단일 스레드 기본 스케줄러)
 |
 | L257 SchedulingConfigurer 빈들을 @Order 순으로 호출
 |        registrar 에 작업을 추가하거나 스케줄러를 바꿀 마지막 기회
 |
 +-- L266 registrar.afterPropertiesSet() --> scheduleTasks()
        보관해 둔 cron/fixedDelay/fixedRate 작업을 스케줄러에 올린다
        이 순간부터 주기 실행이 시작된다
```

## 결과가 쓰이는 곳

```text
 스케줄된 작업
      --> TaskScheduler 가 트리거에 따라 실행
      --> fixedRate 는 시작 시각 기준, fixedDelay 는 종료 시각 기준

 등록 시점이 refresh 이후라는 점
      --> 기동 중에는 스케줄이 돌지 않는다 (빈이 아직 준비되지 않았을 수 있으므로)
      --> 기동이 끝나야 첫 실행이 시작된다

 TaskSchedulerRouter
      --> @Scheduled(scheduler = "이름") 으로 작업별 스케줄러를 고를 수 있게 한다
      --> 지정이 없으면 공용 스케줄러 하나를 공유하므로
          긴 작업이 다른 작업을 미루게 된다 (풀 크기 설정이 필요한 이유)
```
