# SmartLifecycle

상위: [Spring 컨테이너 기동](../../README.md) / [spi](../README.md)

시작과 정지가 있는 컴포넌트다. `Lifecycle`은 `start`/`stop`/`isRunning`만 정하고, `SmartLifecycle`은 refresh 때 자동 시작 여부(`isAutoStartup`)와 순서(`getPhase`), 비동기 정지 콜백을 더한다.

## 실제 코드

`spring-context` / `org.springframework.context` / `Lifecycle.java` L50-L86 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/Lifecycle.java#L50-L86))

```java
// Lifecycle.java L50-L86
public interface Lifecycle {

    void start();

    void stop();

    boolean isRunning();

}
```

`spring-context` / `org.springframework.context` / `SmartLifecycle.java` L67-L162 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/SmartLifecycle.java#L67-L162))

```java
// SmartLifecycle.java L67-L162
public interface SmartLifecycle extends Lifecycle, Phased {

    int DEFAULT_PHASE = Integer.MAX_VALUE;

    default boolean isAutoStartup() {
        return true;
    }

    default boolean isPauseable() {
        return true;
    }

    default void stop(Runnable callback) {
        stop();
        callback.run();
    }

    @Override
    default int getPhase() {
        return DEFAULT_PHASE;
    }

}
```

## 흐름에서 불리는 자리

```text
 refresh
   --> finishRefresh
         --> initLifecycleProcessor
         --> DefaultLifecycleProcessor.onRefresh
               autoStartup 인 SmartLifecycle 을 phase 오름차순으로 start()
 close
   --> doClose --> lifecycleProcessor.onClose()
         phase 내림차순으로 stop(callback)
```

- [AbstractApplicationContext.finishRefresh](../../01_AbstractApplicationContext.refresh/10_AbstractApplicationContext.finishRefresh/README.md)
- [DefaultLifecycleProcessor.onRefresh](../../01_AbstractApplicationContext.refresh/10_AbstractApplicationContext.finishRefresh/01_DefaultLifecycleProcessor.onRefresh/README.md)

## 구현 계층

```text
 Lifecycle                           start / stop / isRunning  (refresh 때 자동 시작 안 됨)
   +-- SmartLifecycle                  + isAutoStartup, getPhase (기본 Integer.MAX_VALUE), stop(Runnable)
   |     +-- AbstractJmsListeningContainer 계열   메시지 수신 시작/정지
   |     +-- ThreadPoolTaskScheduler 등           실행기 정지 순서 참여
   |     +-- (Spring Boot 웹 서버 시작/정지)
   +-- LifecycleProcessor              onRefresh / onClose  (DefaultLifecycleProcessor)
```
