# BeanFactoryInitializationAotContributions.applyTo

상위: [Spring AOT 처리](../README.md)

모아 둔 기여자들을 차례로 적용하는 자리다. AOT가 확장 가능한 구조라는 사실이 이 짧은 루프에 드러난다.

## 실제 코드

`spring-context` / `org.springframework.context.aot` / `BeanFactoryInitializationAotContributions.java` L50-L52 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/aot/BeanFactoryInitializationAotContributions.java#L50-L52))

```java
// BeanFactoryInitializationAotContributions.java L50-L52
BeanFactoryInitializationAotContributions(DefaultListableBeanFactory beanFactory, AotServices.Loader loader) {
    this.contributions = getContributions(beanFactory, getProcessors(loader));
}
```

`spring-context` / `org.springframework.context.aot` / `BeanFactoryInitializationAotContributions.java` L90-L96 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/aot/BeanFactoryInitializationAotContributions.java#L90-L96))

```java
// BeanFactoryInitializationAotContributions.java L90-L96
void applyTo(GenerationContext generationContext,
        BeanFactoryInitializationCode beanFactoryInitializationCode) {

    for (BeanFactoryInitializationAotContribution contribution : this.contributions) {
        contribution.applyTo(generationContext, beanFactoryInitializationCode);
    }
}
```

## 동작 흐름

```text
 생성자 (beanFactory, loader)
 |
 | AotServices 로 BeanFactoryInitializationAotProcessor 구현들을 모은다
 |   META-INF/spring/aot.factories 와 빈 정의 양쪽에서 찾는다
 |   그 뒤에 RuntimeHintsBeanFactoryInitializationAotProcessor 를 코드로 덧붙인다
 |     (L55-60. 등록 파일을 거치지 않아 항상 마지막이다)
 | 각 처리기의 processAheadOfTime(beanFactory) 를 불러
 |   null 이 아닌 기여(contribution)만 목록에 담는다
 |
 applyTo(generationContext, beanFactoryInitializationCode)
 |
 +-- L93 기여마다 contribution.applyTo(생성 컨텍스트, 코드)
        각 기여가 자기 몫의 코드와 힌트를 보탠다
```

```text
 기본으로 참여하는 기여자들

 BeanRegistrationsAotProcessor              빈 정의를 등록 코드로
 ReflectiveProcessorBeanFactoryInitializationAotProcessor
                                            @Reflective 표시를 힌트로
 AspectJBeanFactoryInitializationAotProcessor  AspectJ 애스펙트 힌트
 RuntimeHintsBeanFactoryInitializationAotProcessor
                                            RuntimeHintsRegistrar 들을 실행 (코드로 덧붙는다)

 두 단계로 나뉜다
   처리기(Processor)  분석해서 기여를 만든다 (빈 팩토리를 본다)
   기여(Contribution) 코드와 힌트를 실제로 생성한다
```

1. 빈 등록 코드를 준비하는 처리기는 [BeanRegistrationsAotProcessor.processAheadOfTime](01_BeanRegistrationsAotProcessor.processAheadOfTime/README.md)이다.

## 결과가 쓰이는 곳

```text
 보태진 코드
      --> ApplicationContextInitializationCodeGenerator 가 하나의 초기화기로 합친다
      --> 그 클래스가 런타임에 적용된다

 보태진 힌트
      --> 생성 컨텍스트의 RuntimeHints 에 누적된다
      --> 마지막에 JSON 파일로 쓰인다

 처리기와 기여를 나눈 이유
      --> 분석과 생성을 분리해, 분석 결과가 없으면(null) 아무 코드도 만들지 않는다
      --> 쓰지 않는 기능이 생성물을 늘리지 않는다

 새 기능이 AOT 를 지원하는 방법
      --> BeanFactoryInitializationAotProcessor 또는 BeanRegistrationAotProcessor 를
          구현해 META-INF/spring/aot.factories 에 등록하면 된다
```
