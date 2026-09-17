# AbstractApplicationContext.obtainFreshBeanFactory

상위: [AbstractApplicationContext.refresh](../README.md)

기동에 쓸 빈 팩토리를 하위 클래스에게 받아 온다. 컨텍스트 계열에 따라 "이미 가진 팩토리를 그대로 쓰는 쪽"과 "매번 새 팩토리를 만들고 설정 파일을 다시 읽는 쪽"으로 갈린다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L720-L723 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L720-L723))

```java
// AbstractApplicationContext.java L720-L723
protected ConfigurableListableBeanFactory obtainFreshBeanFactory() {
    refreshBeanFactory();
    return getBeanFactory();
}
```

`refreshBeanFactory`는 추상 메서드이고, 구현이 두 갈래다.

`spring-context` / `org.springframework.context.support` / `GenericApplicationContext.java` L296-L302 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/GenericApplicationContext.java#L296-L302))

```java
// GenericApplicationContext.java L296-L302
protected final void refreshBeanFactory() throws IllegalStateException {
    if (!this.refreshed.compareAndSet(false, true)) {
        throw new IllegalStateException(
                "GenericApplicationContext does not support multiple refresh attempts: just call 'refresh' once");
    }
    this.beanFactory.setSerializationId(getId());
}
```

`spring-context` / `org.springframework.context.support` / `AbstractRefreshableApplicationContext.java` L119-L135 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractRefreshableApplicationContext.java#L119-L135))

```java
// AbstractRefreshableApplicationContext.java L119-L135
protected final void refreshBeanFactory() throws BeansException {
    if (hasBeanFactory()) {
        destroyBeans();
        closeBeanFactory();
    }
    try {
        DefaultListableBeanFactory beanFactory = createBeanFactory();
        beanFactory.setSerializationId(getId());
        beanFactory.setApplicationStartup(getApplicationStartup());
        customizeBeanFactory(beanFactory);
        loadBeanDefinitions(beanFactory);
        this.beanFactory = beanFactory;
    }
    catch (IOException ex) {
        throw new ApplicationContextException("I/O error parsing bean definition source for " + getDisplayName(), ex);
    }
}
```

## 동작 흐름

```text
 obtainFreshBeanFactory()
 |
 +-- refreshBeanFactory()
 |     |
 |     +-- GenericApplicationContext 계열
 |     |     (AnnotationConfigApplicationContext, GenericWebApplicationContext, Spring Boot 컨텍스트)
 |     |     refreshed CAS false -> true
 |     |       실패 (두 번째 refresh) --> IllegalStateException("does not support multiple refresh attempts")
 |     |     serializationId 설정
 |     |     팩토리는 생성자에서 이미 만들어져 있고, 빈 정의도 register()/scan()으로 이미 들어 있음
 |     |
 |     +-- AbstractRefreshableApplicationContext 계열
 |           (ClassPathXmlApplicationContext, XmlWebApplicationContext)
 |           기존 팩토리 있음 --> destroyBeans + closeBeanFactory
 |           createBeanFactory()            새 DefaultListableBeanFactory
 |           customizeBeanFactory()         덮어쓰기/순환참조 허용 여부
 |           loadBeanDefinitions()          XML 등 설정을 읽어 빈 정의 등록   <-- 여기서 정의가 들어옴
 |
 +-- return getBeanFactory()
```

## 결과가 쓰이는 곳

```text
 ConfigurableListableBeanFactory (실체는 DefaultListableBeanFactory)
      --> refresh L596 prepareBeanFactory 부터 L622 finishBeanFactoryInitialization 까지의 작업 대상

 이 시점의 빈 정의 목록
      +-- Generic 계열  : register(AppConfig) 한 것 + 애노테이션 처리기 정의 몇 개뿐
      |                   @Bean, @ComponentScan 결과는 아직 없음 --> invokeBeanFactoryPostProcessors 에서 채워짐
      +-- Refreshable 계열: XML에 적힌 <bean> 전부

 refreshed 플래그 (Generic 계열)
      --> 같은 컨텍스트 객체로 refresh 를 두 번 부를 수 없는 이유
          (실패 후 재시도도 마찬가지 -- 새 컨텍스트 객체를 만들어야 한다)
```
