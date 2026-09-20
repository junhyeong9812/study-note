# ContextAotProcessor.performAotProcessing

상위: [Spring AOT 처리](../README.md)

빌드 시점 파이프라인의 조율 지점이다. 생성 컨텍스트를 만들고, 생성기를 돌리고, 결과를 파일로 쓴다.

## 실제 코드

`spring-context` / `org.springframework.context.aot` / `ContextAotProcessor.java` L81-L86 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/aot/ContextAotProcessor.java#L81-L86))

```java
// ContextAotProcessor.java L81-L86
protected ClassName doProcess() {
    deleteExistingOutput();
    try (GenericApplicationContext applicationContext = prepareApplicationContext(getApplicationClass())) {
        return performAotProcessing(applicationContext);
    }
}
```

`spring-context` / `org.springframework.context.aot` / `ContextAotProcessor.java` L103-L122 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/aot/ContextAotProcessor.java#L103-L122))

```java
// ContextAotProcessor.java L103-L122
    FileSystemGeneratedFiles generatedFiles = createFileSystemGeneratedFiles();
    DefaultGenerationContext generationContext = new DefaultGenerationContext(
            createClassNameGenerator(), generatedFiles);
    ApplicationContextAotGenerator generator = new ApplicationContextAotGenerator();
    ClassName generatedInitializerClassName = generator.processAheadOfTime(applicationContext, generationContext);
    registerEntryPointHint(generationContext, generatedInitializerClassName);
    generationContext.writeGeneratedContent();
    writeHints(generationContext.getRuntimeHints());
    writeNativeImageProperties(getDefaultNativeImageArguments(getApplicationClass().getName()));
    return generatedInitializerClassName;
}

/**
 * Callback to customize the {@link ClassNameGenerator}.
 * <p>By default, a standard {@link ClassNameGenerator} using the configured
 * {@linkplain #getApplicationClass() application entry point} as the default
 * target is used.
 * @return the class name generator
 */
protected ClassNameGenerator createClassNameGenerator() {
```

## 동작 흐름

```text
 doProcess()
 |
 | L82 기존 출력물을 지운다 (증분 생성이 아니라 매번 새로 만든다)
 | L83 prepareApplicationContext(애플리케이션 클래스)
 |       refresh 하지 않은 컨텍스트를 만든다 (하위 구현이 채운다)
 +-- L84 performAotProcessing(컨텍스트)

 performAotProcessing(applicationContext)
 |
 | L103 FileSystemGeneratedFiles   생성물을 어디에 쓸지
 | L104 DefaultGenerationContext   클래스 이름 생성기 + 생성 파일
 |
 | L107 ApplicationContextAotGenerator.processAheadOfTime(컨텍스트, 생성 컨텍스트)
 |        --> 생성된 초기화기 클래스 이름을 돌려준다
 |
 | L108 registerEntryPointHint(...)   진입점 클래스에 대한 힌트 등록
 | L109 generationContext.writeGeneratedContent()   소스/리소스/클래스 파일로
 | L110 writeHints(runtimeHints)      reachability-metadata.json 으로
 | L111 writeNativeImageProperties(...)  native-image.properties 로
 |
 +-- L112 생성된 초기화기 클래스 이름을 반환
```

```text
 세 가지 출력물

 생성 소스    빈 등록과 초기화를 담은 자바 코드 (컴파일 대상)
 생성 클래스  CGLIB 프록시처럼 바이트코드로만 만들어지는 것
 힌트 파일    GraalVM 이 읽는 reachability-metadata.json. 리플렉션 허용 목록에 가깝다

 셋 다 빌드 산출물이다. 런타임에 다시 만들지 않는다
```

1. 실제 생성은 [ApplicationContextAotGenerator.processAheadOfTime](01_ApplicationContextAotGenerator.processAheadOfTime/README.md)이 지휘한다.

## 결과가 쓰이는 곳

```text
 반환한 클래스 이름
      --> 빌드 도구가 이 이름을 런타임 설정에 심는다
      --> 런타임에 AotApplicationContextInitializer 가 그 클래스를 찾아 적용한다

 deleteExistingOutput
      --> 이전 빌드의 잔재가 섞이지 않게 한다
      --> 그래서 AOT 처리는 항상 전체 생성이다

 진입점 힌트
      --> 애플리케이션 클래스 자체도 리플렉션 대상이 될 수 있어 따로 등록한다

 native-image.properties
      --> 네이티브 빌드에 넘길 기본 인자를 담는다
      --> 기본값은 -H:Class=<애플리케이션 클래스> 와 --no-fallback 둘뿐이다 (L136-141)
```
