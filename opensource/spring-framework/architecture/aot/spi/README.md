# spi

상위: [Spring AOT 처리](../README.md)

AOT 처리에 끼어드는 확장점이다. 분석하는 쪽(처리기)과 생성하는 쪽(기여)이 나뉘어 있고, 힌트만 보태는 간단한 길도 따로 있다.

```text
 빌드 시점 확장
   BeanFactoryInitializationAotProcessor  빈 팩토리 전체를 보고 기여를 만든다
   BeanRegistrationAotProcessor           빈 하나에 개입해 기여를 만든다
   BeanFactoryInitializationAotContribution  실제 코드와 힌트를 생성한다
   RuntimeHintsRegistrar                  힌트만 보태는 가장 간단한 길

 런타임
   AotApplicationContextInitializer       생성된 초기화기를 찾아 적용한다
```

## 하위 인터페이스

- [BeanFactoryInitializationAotProcessor](BeanFactoryInitializationAotProcessor/README.md) — 팩토리 전체 분석
- [BeanRegistrationAotProcessor](BeanRegistrationAotProcessor/README.md) — 빈 하나 분석
- [BeanFactoryInitializationAotContribution](BeanFactoryInitializationAotContribution/README.md) — 코드와 힌트 생성
- [RuntimeHintsRegistrar](RuntimeHintsRegistrar/README.md) — 힌트 등록
- [AotApplicationContextInitializer](AotApplicationContextInitializer/README.md) — 런타임 적용
