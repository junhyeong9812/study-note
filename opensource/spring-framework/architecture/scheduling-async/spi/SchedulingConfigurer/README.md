# SchedulingConfigurer

상위: [Spring 스케줄링과 비동기](../../README.md) / [spi](../README.md)

스케줄이 시작되기 직전에 등록기를 손볼 기회를 준다. 코드로 작업을 추가하거나 스케줄러를 바꿀 때 쓴다.

## 실제 코드

`spring-context` / `org.springframework.scheduling.annotation` / `SchedulingConfigurer.java` L40-L50 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/scheduling/annotation/SchedulingConfigurer.java#L40-L50))

```java
// SchedulingConfigurer.java L40-L50
public interface SchedulingConfigurer {

    void configureTasks(ScheduledTaskRegistrar taskRegistrar);

}
```

## 흐름에서 불리는 자리

```text
 finishRegistration L257
   컨텍스트의 SchedulingConfigurer 빈을 @Order 순으로 호출
   configureTasks(registrar) 안에서
     registrar.setScheduler(...)
     registrar.addCronTask(...) 등
   그 뒤 registrar.afterPropertiesSet() 로 스케줄 시작
```

- [finishRegistration](../../02_ScheduledAnnotationBeanPostProcessor.finishRegistration/README.md)

## 구현 계층

```text
 쓰임새
   동적 cron (설정값에 따라 런타임에 결정)
   작업별 스케줄러 분리
   테스트에서 스케줄 비활성화

 대응물
   비동기 쪽은 AsyncConfigurer (기본 실행기와 예외 처리기 지정)
```
