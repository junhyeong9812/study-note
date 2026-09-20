# ApplicationContextAotGenerator.processAheadOfTime

상위: [ContextAotProcessor.performAotProcessing](../README.md)

AOT 생성의 중심이다. 짧지만 이 흐름 전체의 골격이 여기 다 들어 있다.

## 실제 코드

`spring-context` / `org.springframework.context.aot` / `ApplicationContextAotGenerator.java` L51-L62 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/aot/ApplicationContextAotGenerator.java#L51-L62))

```java
// ApplicationContextAotGenerator.java L51-L62
public ClassName processAheadOfTime(GenericApplicationContext applicationContext,
        GenerationContext generationContext) {

    return withCglibClassHandler(new CglibClassHandler(generationContext), () -> {
        applicationContext.refreshForAotProcessing(generationContext.getRuntimeHints());
        ApplicationContextInitializationCodeGenerator codeGenerator =
                new ApplicationContextInitializationCodeGenerator(applicationContext, generationContext);
        DefaultListableBeanFactory beanFactory = applicationContext.getDefaultListableBeanFactory();
        new BeanFactoryInitializationAotContributions(beanFactory).applyTo(generationContext, codeGenerator);
        return codeGenerator.getClassName();
    });
}
```

CGLIB 클래스를 가로채는 부분은 바로 아래에 있다.

`spring-context` / `org.springframework.context.aot` / `ApplicationContextAotGenerator.java` L64-L74 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/aot/ApplicationContextAotGenerator.java#L64-L74))

```java
// ApplicationContextAotGenerator.java L64-L74
private <T> T withCglibClassHandler(CglibClassHandler cglibClassHandler, Supplier<T> task) {
    try {
        ReflectUtils.setLoadedClassHandler(cglibClassHandler::handleLoadedClass);
        ReflectUtils.setGeneratedClassHandler(cglibClassHandler::handleGeneratedClass);
        return task.get();
    }
    finally {
        ReflectUtils.setLoadedClassHandler(null);
        ReflectUtils.setGeneratedClassHandler(null);
    }
}
```

## 동작 흐름

```text
 processAheadOfTime(applicationContext, generationContext)
 |
 +-- L54 withCglibClassHandler(...) 로 감싼다
 |        L66-67 ReflectUtils 에 로드 핸들러와 생성 핸들러를 건다
 |        생성된 클래스는 힌트 등록 + 바이트코드를 파일로 저장
 |        이미 로드된 클래스는 힌트만 등록한다 (파일은 이미 있다)
 |        L70 finally 에서 핸들러를 되돌린다
 |
 | L55 applicationContext.refreshForAotProcessing(runtimeHints)
 |        빈 정의를 확정한다 (싱글톤은 만들지 않는다)
 |
 | L56 ApplicationContextInitializationCodeGenerator 를 만든다
 |        생성될 초기화기 코드의 뼈대다
 |
 | L58 컨텍스트의 DefaultListableBeanFactory 를 꺼내
 | L59 BeanFactoryInitializationAotContributions(beanFactory).applyTo(...)
 |        기여자들을 모아 코드 생성기에 적용한다
 |
 +-- L60 생성된 클래스 이름을 반환
```

```text
 CGLIB 핸들러가 필요한 이유

 @Configuration 클래스는 런타임에 CGLIB 로 서브클래싱된다
 네이티브 이미지에서는 런타임 바이트코드 생성이 불가능하다
 그래서 AOT 처리 중에 생기는 프록시 클래스를 가로채 파일로 저장해 둔다
 런타임에는 그 클래스를 그냥 로드한다
```

1. 빈 정의를 확정하는 단계는 [refreshForAotProcessing](../../02_GenericApplicationContext.refreshForAotProcessing/README.md)에 있다.
2. 기여자 적용은 [BeanFactoryInitializationAotContributions.applyTo](../../03_BeanFactoryInitializationAotContributions.applyTo/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 생성된 초기화기 클래스
      --> ApplicationContextInitializer 를 구현한다
      --> 런타임에 이것을 적용하면 빈 정의가 곧바로 등록된다

 저장된 CGLIB 클래스
      --> 네이티브 이미지에 포함된다
      --> 런타임 프록시 생성이 없어 @Configuration 의 빈 메서드 가로채기가 유지된다

 RuntimeHints
      --> 생성 컨텍스트에 누적된다. 각 기여자가 필요한 힌트를 보탠다
      --> 마지막에 JSON 파일로 쓰인다

 이 메서드가 짧은 이유
      --> 실제 작업은 전부 기여자들이 나눠 맡는다
      --> 새 기능이 AOT 를 지원하려면 기여자를 추가하면 된다
```
