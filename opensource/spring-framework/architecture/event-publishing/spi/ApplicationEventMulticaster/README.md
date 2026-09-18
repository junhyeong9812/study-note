# ApplicationEventMulticaster

상위: [Spring 이벤트 발행](../../README.md) / [spi](../README.md)

리스너 목록을 관리하고 이벤트를 나눠 주는 쪽이다. 컨텍스트는 발행만 하고 전달 방식은 이 구현이 정한다.

## 실제 코드

`spring-context` / `org.springframework.context.event` / `ApplicationEventMulticaster.java` L40-L134 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/ApplicationEventMulticaster.java#L40-L134))

```java
// ApplicationEventMulticaster.java L40-L134
public interface ApplicationEventMulticaster {

    void addApplicationListener(ApplicationListener<?> listener);

    void addApplicationListenerBean(String listenerBeanName);

    void removeApplicationListener(ApplicationListener<?> listener);

    void removeApplicationListenerBean(String listenerBeanName);

    void removeApplicationListeners(Predicate<ApplicationListener<?>> predicate);

    void removeApplicationListenerBeans(Predicate<String> predicate);

    void removeAllListeners();

    void multicastEvent(ApplicationEvent event);

    void multicastEvent(ApplicationEvent event, @Nullable ResolvableType eventType);

}
```

## 흐름에서 불리는 자리

```text
 준비
   initApplicationEventMulticaster
     "applicationEventMulticaster" 빈이 있으면 그것, 없으면 SimpleApplicationEventMulticaster
 등록
   registerListeners --> addApplicationListener / addApplicationListenerBean
 발행
   publishEvent --> multicastEvent
```

- [AbstractApplicationContext.publishEvent](../../01_AbstractApplicationContext.publishEvent/README.md)
- [컨테이너 기동의 initApplicationEventMulticaster](../../../container-refresh/01_AbstractApplicationContext.refresh/07_AbstractApplicationContext.initApplicationEventMulticaster/README.md)

## 구현 계층

```text
 ApplicationEventMulticaster
   +-- AbstractApplicationEventMulticaster     리스너 보관, 타입별 선별과 캐시
         +-- SimpleApplicationEventMulticaster 동기/비동기 실행, errorHandler

 바꿔 끼우는 방법
   "applicationEventMulticaster" 라는 이름으로 빈을 등록한다
   예: taskExecutor 를 설정해 모든 이벤트를 비동기로
```
