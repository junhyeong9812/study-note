# Spring 스케줄링과 비동기

`@Scheduled` 메서드가 주기적으로 실행되도록 등록되는 흐름과, `@Async` 메서드 호출이 다른 스레드로 넘어가는 흐름을 함께 다룬다. 둘은 서로 다른 장치다. 스케줄링은 **후처리기가 빈을 훑어 작업을 등록**하고, 비동기는 **AOP 인터셉터가 호출을 가로채 실행기에 넘긴다**. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 두 흐름의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [A] @Scheduled  (프록시 없음)

 @EnableScheduling --> @Import(SchedulingConfiguration)
   @Bean ScheduledAnnotationBeanPostProcessor
 |
 +-- [01] postProcessAfterInitialization        빈이 만들어질 때마다
 |      @Scheduled 메서드를 찾아 processScheduled
 |        cron / fixedDelay / fixedRate 중 하나로 Task 를 만들어
 |        ScheduledTaskRegistrar 에 등록 (아직 실행되지는 않는다)
 |
 +-- [02] finishRegistration                    컨텍스트 준비가 끝난 뒤
        TaskScheduler 결정 --> SchedulingConfigurer 들에게 기회를 준 뒤
        registrar.afterPropertiesSet() --> 실제 스케줄 시작

 [B] @Async  (AOP 프록시)

 @EnableAsync --> AsyncConfigurationSelector --> ProxyAsyncConfiguration
   @Bean AsyncAnnotationBeanPostProcessor (어드바이저 + AsyncExecutionInterceptor)
 |
 +-- 프록시.메서드() --> ReflectiveMethodInvocation.proceed
        |
        +-- [03] AsyncExecutionInterceptor.invoke
               실행기 결정 (@Async("qualifier") 는 AnnotationAsyncExecutionInterceptor 가 읽는다)
               invocation.proceed() 를 Callable 로 감싸 executor 에 제출
               반환 타입에 따라 Future / CompletableFuture / void
```

두 흐름의 성격 차이는 다음과 같다.

```text
 @Scheduled                                @Async
 프록시를 만들지 않는다                     AOP 프록시가 필요하다
 빈 후처리기가 메서드를 등록                인터셉터가 호출을 가로챈다
 호출자가 없다 (스케줄러가 부른다)          호출자가 있다 (즉시 반환)
 반환값은 무시된다                          Future 로 결과를 받을 수 있다
 private/final 이어도 동작한다              프록시 제약을 받는다 (자기 호출 불가)
```

## 단계

1. [ScheduledAnnotationBeanPostProcessor.postProcessAfterInitialization](01_ScheduledAnnotationBeanPostProcessor.postProcessAfterInitialization/README.md)이 `@Scheduled` 메서드를 작업으로 만들어 등록한다.
2. [ScheduledAnnotationBeanPostProcessor.finishRegistration](02_ScheduledAnnotationBeanPostProcessor.finishRegistration/README.md)이 스케줄러를 확정하고 실제 스케줄을 시작한다.
3. [AsyncExecutionInterceptor.invoke](03_AsyncExecutionInterceptor.invoke/README.md)가 `@Async` 호출을 실행기로 넘긴다.

## 결과가 쓰이는 곳

```text
 등록된 ScheduledTask
      --> TaskScheduler 가 주기에 맞춰 실행
      --> 컨텍스트 종료 시 취소 (ScheduledAnnotationBeanPostProcessor.destroy)

 @Async 제출
      --> 호출자는 즉시 반환값을 받는다 (void 면 null)
      --> 예외는 호출자에게 전달되지 않는다
          Future 반환이면 get() 에서, void 면 AsyncUncaughtExceptionHandler 로

 스레드 문맥
      --> 다른 스레드로 넘어가므로 ThreadLocal(트랜잭션, 보안 문맥, 요청 문맥)이 전파되지 않는다
      --> 필요하면 TaskDecorator 로 복사해야 한다
```

## 다루지 않는 것

`@Scheduled`의 cron 식 파싱(`CronExpression`)과 스케줄러 구현(`ThreadPoolTaskScheduler`)의 내부는 범위 밖이다. 가상 스레드 설정도 실행기 구현 쪽 주제다.

## 하위 메서드

- [01 postProcessAfterInitialization](01_ScheduledAnnotationBeanPostProcessor.postProcessAfterInitialization/README.md)
- [02 finishRegistration](02_ScheduledAnnotationBeanPostProcessor.finishRegistration/README.md)
- [03 AsyncExecutionInterceptor.invoke](03_AsyncExecutionInterceptor.invoke/README.md)
- [spi](spi/README.md) — 스케줄러, 트리거, 실행기, 예외 처리기
