# AbstractApplicationContext.initMessageSource

상위: [AbstractApplicationContext.refresh](../README.md)

다국어 메시지를 해석할 `MessageSource`를 정한다. 사용자가 `messageSource`라는 이름의 빈을 등록했으면 그것을 쓰고, 없으면 부모 컨텍스트에 위임만 하는 빈 구현을 넣는다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `AbstractApplicationContext.java` L821-L846 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/AbstractApplicationContext.java#L821-L846))

```java
// AbstractApplicationContext.java L821-L846
protected void initMessageSource() {
    ConfigurableListableBeanFactory beanFactory = getBeanFactory();
    if (beanFactory.containsLocalBean(MESSAGE_SOURCE_BEAN_NAME)) {
        this.messageSource = beanFactory.getBean(MESSAGE_SOURCE_BEAN_NAME, MessageSource.class);
        // Make MessageSource aware of parent MessageSource.
        if (this.parent != null && this.messageSource instanceof HierarchicalMessageSource hms &&
                hms.getParentMessageSource() == null) {
            // Only set parent context as parent MessageSource if no parent MessageSource
            // registered already.
            hms.setParentMessageSource(getInternalParentMessageSource());
        }
        if (logger.isTraceEnabled()) {
            logger.trace("Using MessageSource [" + this.messageSource + "]");
        }
    }
    else {
        // Use empty MessageSource to be able to accept getMessage calls.
        DelegatingMessageSource dms = new DelegatingMessageSource();
        dms.setParentMessageSource(getInternalParentMessageSource());
        this.messageSource = dms;
        beanFactory.registerSingleton(MESSAGE_SOURCE_BEAN_NAME, this.messageSource);
        if (logger.isTraceEnabled()) {
            logger.trace("No '" + MESSAGE_SOURCE_BEAN_NAME + "' bean, using [" + this.messageSource + "]");
        }
    }
}
```

## 동작 흐름

```text
 initMessageSource()
 |
 +-- 이 팩토리에 "messageSource" 빈 정의가 있음   (containsLocalBean -- 부모는 안 봄)
 |     messageSource = getBean("messageSource")    <-- 여기서 이 빈만 먼저 생성됨
 |     부모 컨텍스트 있음 + HierarchicalMessageSource + 부모 미설정
 |       --> 부모 컨텍스트의 MessageSource 를 부모로 연결
 |
 +-- 없음
       DelegatingMessageSource 생성   (자기 메시지 없음, 부모에게만 위임)
       부모 = 부모 컨텍스트의 MessageSource
       registerSingleton("messageSource", ...)
```

빈 이름이 정확히 `messageSource`여야 한다. `@Bean MessageSource myMessages()`처럼 다른 이름으로 등록하면 이 단계에서 찾지 못하고 빈 구현이 들어간다.

## 결과가 쓰이는 곳

```text
 this.messageSource
      --> ApplicationContext.getMessage(code, args, locale)   컨텍스트가 이 객체에 위임
      --> MessageSourceAware 빈의 setMessageSource()          (prepareBeanFactory 의 Aware 처리기)
      --> 웹이라면 뷰 템플릿의 메시지 표현식, render 의 locale 과 함께 사용

 registerSingleton 으로 넣은 기본 구현
      --> @Autowired MessageSource 가 항상 성공하는 이유
```
