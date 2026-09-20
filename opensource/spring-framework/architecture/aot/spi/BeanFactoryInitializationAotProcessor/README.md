# BeanFactoryInitializationAotProcessor

상위: [Spring AOT 처리](../../README.md) / [spi](../README.md)

빈 팩토리 전체를 보고 "무엇을 생성할지"를 정하는 확장점이다. 메서드 하나뿐이고, 할 일이 없으면 `null`을 돌려준다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.aot` / `BeanFactoryInitializationAotProcessor.java` L48-L64 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/aot/BeanFactoryInitializationAotProcessor.java#L48-L64))

```java
// BeanFactoryInitializationAotProcessor.java L48-L64
public interface BeanFactoryInitializationAotProcessor {

    @Nullable BeanFactoryInitializationAotContribution processAheadOfTime(ConfigurableListableBeanFactory beanFactory);

}
```

## 흐름에서 불리는 자리

```text
 BeanFactoryInitializationAotContributions 생성자
   AotServices 로 구현들을 모아
   processAheadOfTime(beanFactory) 를 각각 부른다
   null 이 아닌 기여만 목록에 담는다
```

- [BeanFactoryInitializationAotContributions.applyTo](../../03_BeanFactoryInitializationAotContributions.applyTo/README.md)

## 구현 계층

```text
 BeanFactoryInitializationAotProcessor
   +-- BeanRegistrationsAotProcessor                   빈 정의 --> 등록 코드
   +-- ReflectiveProcessorBeanFactoryInitializationAotProcessor  @Reflective 처리
   +-- AspectJBeanFactoryInitializationAotProcessor     AspectJ 애스펙트 힌트
   +-- RuntimeHintsBeanFactoryInitializationAotProcessor  RuntimeHintsRegistrar 실행
   +-- ConfigurationClassPostProcessor                  BeanRegistrationAotProcessor 도 겸한다
   +-- (사용자 구현)

 등록 방법
   META-INF/spring/aot.factories 의 BeanFactoryInitializationAotProcessor 키
   또는 빈으로 등록 (AotServices 가 양쪽을 본다)
   RuntimeHintsBeanFactoryInitializationAotProcessor 만 예외로 코드에서 덧붙는다
```

## 결과가 쓰이는 곳

```text
 반환한 기여
      --> applyTo 단계에서 코드와 힌트를 생성한다
      --> 분석과 생성이 나뉘어 있어, 분석만 하고 끝낼 수도 있다

 null 반환
      --> 이 처리기는 기여하지 않는다
      --> 쓰지 않는 기능이 생성물을 늘리지 않게 하는 장치다

 빈 팩토리를 통째로 받는다는 점
      --> 빈 정의를 자유롭게 훑을 수 있다
      --> 다만 빈 인스턴스는 없다. 정의만 있는 상태다

 빈으로 등록된 처리기
      --> 그 빈 자체는 생성 대상에서 제외된다
      --> 빌드 도구용 빈이 런타임 생성물에 섞이지 않는다
```
