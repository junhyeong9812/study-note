# TestExecutionListener

상위: [Spring 테스트 컨텍스트](../../README.md) / [spi](../README.md)

테스트 생애 주기의 각 지점에 끼어드는 훅이다. 주입, 트랜잭션, 스크립트 실행, 빈 오버라이드가 모두 이 인터페이스의 구현이다.

## 실제 코드

`spring-test` / `org.springframework.test.context` / `TestExecutionListener.java` L126-L287 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-test/src/main/java/org/springframework/test/context/TestExecutionListener.java#L126-L287))

```java
// TestExecutionListener.java L126-L287
public interface TestExecutionListener {

    default void beforeTestClass(TestContext testContext) throws Exception {
    }

    default void prepareTestInstance(TestContext testContext) throws Exception {
    }

    default void beforeTestMethod(TestContext testContext) throws Exception {
    }

    default void beforeTestExecution(TestContext testContext) throws Exception {
    }

    default void afterTestExecution(TestContext testContext) throws Exception {
    }

    default void afterTestMethod(TestContext testContext) throws Exception {
    }

    default void afterTestClass(TestContext testContext) throws Exception {
    }

}
```

## 흐름에서 불리는 자리

```text
 TestContextManager 가 콜백마다 등록된 리스너를 순서대로 호출
   beforeTestClass -> prepareTestInstance -> beforeTestMethod
   -> (테스트 실행) -> afterTestMethod -> afterTestClass
 하나가 예외를 던지면 그 콜백의 남은 리스너는 호출되지 않는다
```

- [TestContextManager.prepareTestInstance](../../01_TestContextManager.prepareTestInstance/README.md)

## 구현 계층

```text
 기본 등록 리스너 (spring.factories, @Order 순)
   ServletTestExecutionListener            목 서블릿 문맥 설정
   DirtiesContextBeforeModesTestExecutionListener
   ApplicationEventsTestExecutionListener  @RecordApplicationEvents
   BeanOverrideTestExecutionListener       @MockitoBean 등 주입
   DependencyInjectionTestExecutionListener  테스트 인스턴스 주입
   MicrometerObservationRegistryTestExecutionListener
   DirtiesContextTestExecutionListener     컨텍스트 폐기
   TransactionalTestExecutionListener      테스트 트랜잭션 시작/롤백
   SqlScriptsTestExecutionListener         @Sql
   EventPublishingTestExecutionListener    테스트 생애 이벤트 발행

 사용자 정의
   @TestExecutionListeners 로 추가/교체
```
