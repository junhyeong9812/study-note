# ScheduledAnnotationBeanPostProcessor.postProcessAfterInitialization

상위: [Spring 스케줄링과 비동기](../README.md)

빈이 초기화될 때마다 `@Scheduled` 메서드를 찾아 작업으로 만들어 등록기에 넣는다. 프록시를 만들지 않으므로 빈 객체 자체는 그대로 돌려준다.

## 실제 코드

`spring-context` / `org.springframework.context....scheduling.annotation` / `ScheduledAnnotationBeanPostProcessor.java` L279-L320 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/../scheduling/annotation/ScheduledAnnotationBeanPostProcessor.java#L279-L320))

```java
// ScheduledAnnotationBeanPostProcessor.java L279-L320
@Override
public Object postProcessAfterInitialization(Object bean, String beanName) {
    if (bean instanceof AopInfrastructureBean || bean instanceof TaskScheduler ||
            bean instanceof ScheduledExecutorService) {
        // Ignore AOP infrastructure such as scoped proxies.
        return bean;
    }

    Class<?> targetClass = AopProxyUtils.ultimateTargetClass(bean);
    if (!this.nonAnnotatedClasses.contains(targetClass) &&
            AnnotationUtils.isCandidateClass(targetClass, List.of(Scheduled.class, Schedules.class))) {
        Map<Method, Set<Scheduled>> annotatedMethods = MethodIntrospector.selectMethods(targetClass,
                (MethodIntrospector.MetadataLookup<Set<Scheduled>>) method -> {
                    Set<Scheduled> scheduledAnnotations = AnnotatedElementUtils.getMergedRepeatableAnnotations(
                            method, Scheduled.class, Schedules.class);
                    return (!scheduledAnnotations.isEmpty() ? scheduledAnnotations : null);
                });
        if (annotatedMethods.isEmpty()) {
            this.nonAnnotatedClasses.add(targetClass);
            if (logger.isTraceEnabled()) {
                logger.trace("No @Scheduled annotations found on bean class: " + targetClass);
            }
        }
        else {
            // Non-empty set of methods
            annotatedMethods.forEach((method, scheduledAnnotations) ->
                    scheduledAnnotations.forEach(scheduled -> processScheduled(scheduled, method, bean)));
            if (logger.isTraceEnabled()) {
                logger.trace(annotatedMethods.size() + " @Scheduled methods processed on bean '" + beanName +
                        "': " + annotatedMethods);
            }
            if ((this.beanFactory != null &&
                    (!this.beanFactory.containsBean(beanName) || !this.beanFactory.isSingleton(beanName)) ||
                    (this.beanFactory instanceof SingletonBeanRegistry sbr && sbr.containsSingleton(beanName)))) {
                // Either a prototype/scoped bean or a FactoryBean with a pre-existing managed singleton
                // -> trigger manual cancellation when ContextClosedEvent comes in
                this.manualCancellationOnContextClose.add(bean);
            }
        }
    }
    return bean;
}
```

작업을 만드는 부분이다.

`spring-context` / `org.springframework.context....scheduling.annotation` / `ScheduledAnnotationBeanPostProcessor.java` L328-L360 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/../scheduling/annotation/ScheduledAnnotationBeanPostProcessor.java#L328-L360))

```java
// ScheduledAnnotationBeanPostProcessor.java L328-L360
protected void processScheduled(Scheduled scheduled, Method method, Object bean) {
    Object key = AopProxyUtils.ultimateSingletonTarget(bean);

    // Is the method a Kotlin suspending function? Throws if true and the reactor bridge isn't on the classpath.
    // Does the method return a reactive type? Throws if true and it isn't a deferred Publisher type.
    if (REACTIVE_STREAMS_PRESENT && ScheduledAnnotationReactiveSupport.isReactive(method)) {
        processScheduledAsync(scheduled, method, bean, key);
        return;
    }
    processScheduledSync(scheduled, method, bean, key);
}

/**
 * Process the given {@code @Scheduled} method declaration on the given bean,
 * as a synchronous method. The method must accept no arguments. Its return value
 * is ignored (if any), and the scheduled invocations of the method take place
 * using the underlying {@link TaskScheduler} infrastructure.
 * @param scheduled the {@code @Scheduled} annotation
 * @param method the method that the annotation has been declared on
 * @param bean the target bean instance
 * @param key a cache key for the target bean instance
 */
private void processScheduledSync(Scheduled scheduled, Method method, Object bean, Object key) {
    Runnable task;
    try {
        task = createRunnable(bean, method, scheduled.scheduler());
    }
    catch (IllegalArgumentException ex) {
        throw new IllegalStateException("Could not create recurring task for @Scheduled method '" +
                method.getName() + "': " + ex.getMessage());
    }

    processScheduledTask(scheduled, task, method, key);
```

`spring-context` / `org.springframework.context....scheduling.annotation` / `ScheduledAnnotationBeanPostProcessor.java` L405-L465 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/../scheduling/annotation/ScheduledAnnotationBeanPostProcessor.java#L405-L465))

```java
// ScheduledAnnotationBeanPostProcessor.java L405-L465
boolean processedSchedule = false;
String errorMessage = "Exactly one of the 'cron', 'fixedDelay' or 'fixedRate' attributes is required";

Set<ScheduledTask> tasks = new LinkedHashSet<>(4);

// Determine initial delay
Duration initialDelay = toDuration(scheduled.initialDelay(), scheduled.timeUnit());
String initialDelayString = scheduled.initialDelayString();
if (StringUtils.hasText(initialDelayString)) {
    Assert.isTrue(initialDelay.isNegative(), "Specify 'initialDelay' or 'initialDelayString', not both");
    if (this.embeddedValueResolver != null) {
        initialDelayString = this.embeddedValueResolver.resolveStringValue(initialDelayString);
    }
    if (StringUtils.hasLength(initialDelayString)) {
        try {
            initialDelay = toDuration(initialDelayString, scheduled.timeUnit());
        }
        catch (RuntimeException ex) {
            throw new IllegalArgumentException(
                    "Invalid initialDelayString value \"" + initialDelayString + "\"; " + ex);
        }
    }
}

// Check cron expression
String cron = scheduled.cron();
if (StringUtils.hasText(cron)) {
    String zone = scheduled.zone();
    if (this.embeddedValueResolver != null) {
        cron = this.embeddedValueResolver.resolveStringValue(cron);
        zone = this.embeddedValueResolver.resolveStringValue(zone);
    }
    if (StringUtils.hasLength(cron)) {
        Assert.isTrue(initialDelay.isNegative(), "'initialDelay' not supported for cron triggers");
        processedSchedule = true;
        if (!Scheduled.CRON_DISABLED.equals(cron)) {
            CronTrigger trigger;
            if (StringUtils.hasText(zone)) {
                trigger = new CronTrigger(cron, StringUtils.parseTimeZoneString(zone));
            }
            else {
                trigger = new CronTrigger(cron);
            }
            tasks.add(Objects.requireNonNull(
                    this.registrar.scheduleCronTask(new CronTask(runnable, trigger))));
        }
    }
}

// At this point we don't need to differentiate between initial delay set or not anymore
Duration delayToUse = (initialDelay.isNegative() ? Duration.ZERO : initialDelay);

// Check fixed delay
Duration fixedDelay = toDuration(scheduled.fixedDelay(), scheduled.timeUnit());
if (!fixedDelay.isNegative()) {
    Assert.isTrue(!processedSchedule, errorMessage);
    processedSchedule = true;
    tasks.add(Objects.requireNonNull(
            this.registrar.scheduleFixedDelayTask(new FixedDelayTask(runnable, fixedDelay, delayToUse))));
}
String fixedDelayString = scheduled.fixedDelayString();
```

## 동작 흐름

```text
 postProcessAfterInitialization(bean, beanName)
 |
 | L281 AOP 인프라 빈, TaskScheduler, ScheduledExecutorService --> 건너뜀
 | L287 타깃 클래스 확정 (프록시면 그 안쪽)
 | L288 후보 클래스인지 빠르게 확인, 이미 검사한 클래스는 재검사하지 않음
 |
 +-- L290 @Scheduled / @Schedules 가 붙은 메서드 수집
 |      없으면 nonAnnotatedClasses 에 기록하고 끝
 |
 +-- L304 메서드마다 processScheduled(scheduled, method, bean)
        |
        | L353 createRunnable(bean, method)      리플렉션 호출을 감싼 Runnable
        | L411 initialDelay 해석 (숫자 또는 문자열 + 플레이스홀더)
        |
        +-- L430 cron 이 있으면
        |      zone 적용 --> CronTrigger --> registrar.scheduleCronTask
        |      cron 에 initialDelay 를 함께 쓰면 예외
        |      "-" (CRON_DISABLED) 이면 등록하지 않는다
        |
        +-- L458 fixedDelay --> FixedDelayTask
        +--      fixedRate  --> FixedRateTask
        |      문자열 버전(fixedDelayString 등)도 플레이스홀더 해석 후 같은 경로
        |      세 가지 중 정확히 하나만 지정해야 한다 (아니면 예외)
        |
        +-- 만들어진 ScheduledTask 를 빈별 목록에 보관 (나중에 취소하기 위해)
```

1. 등록된 작업이 실제로 돌기 시작하는 시점은 [finishRegistration](../02_ScheduledAnnotationBeanPostProcessor.finishRegistration/README.md)이다.

## 결과가 쓰이는 곳

```text
 ScheduledTaskRegistrar 의 작업 목록
      --> finishRegistration 에서 스케줄러에 올린다
      --> 이미 스케줄러가 준비된 뒤(런타임 빈 생성)라면 즉시 스케줄된다

 빈별 ScheduledTask 목록
      --> 빈이 파괴되거나 컨텍스트가 닫힐 때 취소
      --> 프로토타입 빈의 @Scheduled 가 누수되지 않게 하는 장치

 프록시를 만들지 않는다는 점
      --> 호출자가 없으므로 @Async 와 달리 "자기 호출" 문제가 없다
      --> ScheduledMethodRunnable 이 makeAccessible 을 부르므로 private 메서드도 실행된다
      --> 단 인자는 없어야 한다 (createRunnable L547 에서 단언)
```
