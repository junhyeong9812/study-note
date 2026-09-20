# BeanRegistrationAotProcessor

상위: [Spring AOT 처리](../../README.md) / [spi](../README.md)

빈 하나에 개입하는 확장점이다. 팩토리 전체를 보는 쪽과 달리, 등록된 빈마다 불린다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.aot` / `BeanRegistrationAotProcessor.java` L51-L90 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/aot/BeanRegistrationAotProcessor.java#L51-L90))

```java
// BeanRegistrationAotProcessor.java L51-L90
public interface BeanRegistrationAotProcessor {

    String IGNORE_REGISTRATION_ATTRIBUTE = "aotProcessingIgnoreRegistration";

    @Nullable BeanRegistrationAotContribution processAheadOfTime(RegisteredBean registeredBean);

    default boolean isBeanExcludedFromAotProcessing() {
        return true;
    }

}
```

## 흐름에서 불리는 자리

```text
 BeanDefinitionMethodGeneratorFactory 가 빈마다 호출한다
   getBeanDefinitionMethodGenerator(registeredBean)
     등록된 BeanRegistrationAotProcessor 들에게 물어
     기여를 모은 뒤 등록 메서드 생성기를 만든다
```

- [BeanRegistrationsAotProcessor.processAheadOfTime](../../03_BeanFactoryInitializationAotContributions.applyTo/01_BeanRegistrationsAotProcessor.processAheadOfTime/README.md)

## 구현 계층

```text
 BeanRegistrationAotProcessor
   +-- KotlinReflectionBeanRegistrationAotProcessor   코틀린 리플렉션 힌트
   +-- BeanValidationBeanRegistrationAotProcessor     빈 검증 제약 힌트
   +-- ScopedProxyBeanRegistrationAotProcessor        스코프 프록시 대상 교체
   +-- TransactionBeanRegistrationAotProcessor        @Transactional 힌트
   +-- PersistenceManagedTypesBeanRegistrationAotProcessor  JPA 관리 타입
   +-- (사용자 구현)

 isBeanExcludedFromAotProcessing()
   기본 true — 이 처리기 빈 자신은 생성 대상에서 빠진다
```

## 결과가 쓰이는 곳

```text
 반환한 BeanRegistrationAotContribution
      --> 그 빈의 등록 코드에 덧붙는다
      --> 주입 코드나 추가 힌트를 그 빈에만 붙일 수 있다

 null 반환
      --> 이 빈에는 개입하지 않는다

 isBeanExcludedFromAotProcessing
      --> 빌드 시점에만 쓰이는 빈이 런타임 생성물에 남지 않게 한다
      --> 기본값이 true 라 대개 신경 쓸 필요가 없다

 팩토리 전체 처리기와의 선택 기준
      --> 빈 하나의 등록 코드를 바꾸고 싶으면 이쪽
      --> 초기화기 전체에 코드를 보태고 싶으면 저쪽
```
