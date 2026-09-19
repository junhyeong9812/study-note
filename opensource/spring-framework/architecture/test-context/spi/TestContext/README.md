# TestContext

상위: [Spring 테스트 컨텍스트](../../README.md) / [spi](../README.md)

테스트 하나가 실행되는 동안의 상태를 담는다. 테스트 클래스, 인스턴스, 메서드, 예외, 그리고 컨텍스트 접근 경로가 여기에 있다.

## 실제 코드

`spring-test` / `org.springframework.test.context` / `TestContext.java` L50-L216 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/TestContext.java#L50-L216))

```java
// TestContext.java L50-L216
public interface TestContext extends AttributeAccessor, Serializable {

    default boolean hasApplicationContext() {
        return false;
    }

    ApplicationContext getApplicationContext();

    default void publishEvent(Function<TestContext, ? extends ApplicationEvent> eventFactory) {
        if (hasApplicationContext()) {
            getApplicationContext().publishEvent(eventFactory.apply(this));
        }
    }

    Class<?> getTestClass();

    Object getTestInstance();

    Method getTestMethod();

    @Nullable Throwable getTestException();

    default void markApplicationContextUnused() {
        /* no-op */
    }

    void markApplicationContextDirty(@Nullable HierarchyMode hierarchyMode);

    void updateState(@Nullable Object testInstance, @Nullable Method testMethod, @Nullable Throwable testException);

    default void setMethodInvoker(MethodInvoker methodInvoker) {
        /* no-op */
    }

    default MethodInvoker getMethodInvoker() {
        return MethodInvoker.DEFAULT_INVOKER;
    }

}
```

## 흐름에서 불리는 자리

```text
 TestContextManager 의 각 콜백
   updateState(instance, method, exception) 로 현재 상태를 갱신
   리스너에게 이 객체를 넘긴다
 리스너가 getApplicationContext() 를 부르면 컨텍스트 로딩이 촉발된다
```

- [TestContextManager.prepareTestInstance](../../01_TestContextManager.prepareTestInstance/README.md)
- [loadContext](../../02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md)

## 구현 계층

```text
 TestContext
   +-- DefaultTestContext        캐시 위임자를 통해 컨텍스트를 얻는다

 담고 있는 것
   테스트 클래스 / 인스턴스 / 메서드 / 발생 예외
   MergedContextConfiguration (캐시 키)
   속성 맵 (리스너들이 상태를 주고받는 자리)
```
