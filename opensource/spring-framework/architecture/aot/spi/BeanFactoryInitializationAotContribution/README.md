# BeanFactoryInitializationAotContribution

상위: [Spring AOT 처리](../../README.md) / [spi](../README.md)

실제로 코드와 힌트를 만드는 쪽이다. 처리기가 "무엇을"을 정했다면, 기여는 "어떻게"를 담는다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.aot` / `BeanFactoryInitializationAotContribution.java` L34-L44 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/aot/BeanFactoryInitializationAotContribution.java#L34-L44))

```java
// BeanFactoryInitializationAotContribution.java L34-L44
public interface BeanFactoryInitializationAotContribution {

    void applyTo(GenerationContext generationContext,
            BeanFactoryInitializationCode beanFactoryInitializationCode);

}
```

## 흐름에서 불리는 자리

```text
 BeanFactoryInitializationAotContributions.applyTo  L93
   contribution.applyTo(generationContext, beanFactoryInitializationCode)
     생성 컨텍스트로 힌트와 생성 파일에 닿고
     초기화 코드에 메서드를 보탠다
```

- [BeanFactoryInitializationAotContributions.applyTo](../../03_BeanFactoryInitializationAotContributions.applyTo/README.md)

## 구현 계층

```text
 BeanFactoryInitializationAotContribution
   +-- BeanRegistrationsAotContribution   빈마다 등록 메서드를 생성한다
   +-- (힌트만 보태는 람다형 기여들)
   +-- (사용자 구현)

 받는 두 인자
   GenerationContext              RuntimeHints, 생성 파일, 클래스 이름 생성기
   BeanFactoryInitializationCode  초기화기 코드에 메서드를 등록하는 통로
```

## 결과가 쓰이는 곳

```text
 생성한 메서드
      --> 초기화기 클래스의 본문이 된다
      --> 여러 기여가 각자 메서드를 보태 하나의 클래스로 합쳐진다

 보탠 힌트
      --> generationContext.getRuntimeHints() 에 누적된다
      --> 리플렉션, 리소스, 프록시, 직렬화 종류별로 나뉘어 있다

 기여가 아무것도 하지 않아도 된다
      --> 분석 결과 할 일이 없으면 빈 구현이어도 된다
      --> 다만 그런 경우 처리기가 애초에 null 을 돌려주는 편이 낫다
```
