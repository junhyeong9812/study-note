# TestContextManager.prepareTestInstance

상위: [Spring 테스트 컨텍스트](../README.md)

테스트 인스턴스가 만들어진 직후에 불려, 등록된 [TestExecutionListener](../spi/TestExecutionListener/README.md)들에게 준비할 기회를 준다. `@Autowired` 필드가 채워지는 지점이 여기다.

## 실제 코드

`spring-test` / `org.springframework.test.context` / `TestContextManager.java` L251-L284 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/TestContextManager.java#L251-L284))

```java
// TestContextManager.java L251-L284
public void prepareTestInstance(Object testInstance) throws Exception {
    try {
        if (logger.isTraceEnabled()) {
            logger.trace("prepareTestInstance(): instance [" + testInstance + "]");
        }
        getTestContext().updateState(testInstance, null, null);

        for (TestExecutionListener testExecutionListener : getTestExecutionListeners()) {
            try {
                testExecutionListener.prepareTestInstance(getTestContext());
            }
            catch (Throwable ex) {
                if (isSkippedException(ex)) {
                    if (logger.isInfoEnabled()) {
                        logger.info("""
                                Caught exception while allowing TestExecutionListener [%s] to \
                                prepare test instance [%s]"""
                                    .formatted(typeName(testExecutionListener), testInstance), ex);
                    }
                }
                else if (logger.isWarnEnabled()) {
                    logger.warn("""
                        Caught exception while allowing TestExecutionListener [%s] to \
                        prepare test instance [%s]"""
                            .formatted(typeName(testExecutionListener), testInstance), ex);
                }
                ReflectionUtils.rethrowException(ex);
            }
        }
    }
    finally {
        resetMethodInvoker();
    }
}
```

클래스 단위 콜백도 같은 모양이다.

`spring-test` / `org.springframework.test.context` / `TestContextManager.java` L210-L231 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/TestContextManager.java#L210-L231))

```java
// TestContextManager.java L210-L231
public void beforeTestClass() throws Exception {
    try {
        Class<?> testClass = getTestContext().getTestClass();
        if (logger.isTraceEnabled()) {
            logger.trace("beforeTestClass(): class [" + typeName(testClass) + "]");
        }
        getTestContext().updateState(null, null, null);

        for (TestExecutionListener testExecutionListener : getTestExecutionListeners()) {
            try {
                testExecutionListener.beforeTestClass(getTestContext());
            }
            catch (Throwable ex) {
                logException(ex, "beforeTestClass", testExecutionListener, testClass);
                ReflectionUtils.rethrowException(ex);
            }
        }
    }
    finally {
        resetMethodInvoker();
    }
}
```

## 동작 흐름

```text
 JUnit 5 기준 호출 순서 (SpringExtension 이 위임)

 beforeAll         --> beforeTestClass
 테스트 인스턴스 생성
 postProcessTestInstance --> prepareTestInstance     <-- 의존성 주입
 beforeEach        --> beforeTestMethod
 테스트 메서드 실행
 afterEach         --> afterTestMethod
 afterAll          --> afterTestClass

 prepareTestInstance(testInstance)
 |
 | L256 testContext.updateState(testInstance, null, null)
 |        현재 테스트 인스턴스를 컨텍스트에 기록
 |
 +-- L258 등록된 리스너를 순서대로 호출
       DependencyInjectionTestExecutionListener
         testContext.getApplicationContext() 로 컨텍스트를 얻고
         AutowireCapableBeanFactory.autowireBeanProperties 로 필드 주입
         = 이 호출이 컨텍스트 로딩을 촉발한다
       그 밖 리스너들 (Mockito 빈 오버라이드, 서블릿 목 설정 등)
       |
       +-- 리스너가 예외를 던지면 남은 리스너는 호출되지 않는다
           (건너뛰기 예외는 로그만 남기고 전파)
```

## 결과가 쓰이는 곳

```text
 주입된 테스트 인스턴스
      --> 테스트 메서드가 필드의 빈을 그대로 쓴다

 컨텍스트 로딩 시점
      --> 첫 테스트 인스턴스 준비 때 (또는 그 전에 컨텍스트를 요구한 리스너에서)
      --> 캐시에 있으면 즉시 반환되므로 두 번째 테스트 클래스부터는 빠르다

 리스너 순서
      --> @Order 또는 @TestExecutionListeners 로 지정
      --> 주입 리스너가 트랜잭션 리스너보다 앞에 있어야 한다
          (주입된 빈으로 트랜잭션을 시작하므로)
```
