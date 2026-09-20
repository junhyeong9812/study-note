# RuntimeHintsRegistrar

상위: [Spring AOT 처리](../../README.md) / [spi](../README.md)

네이티브 이미지에 필요한 힌트만 보태는 가장 간단한 확장점이다. 코드를 생성하지 않고 힌트만 등록한다.

## 실제 코드

`spring-core` / `org.springframework.aot.hint` / `RuntimeHintsRegistrar.java` L37-L46 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/aot/hint/RuntimeHintsRegistrar.java#L37-L46))

```java
// RuntimeHintsRegistrar.java L37-L46
public interface RuntimeHintsRegistrar {

    void registerHints(RuntimeHints hints, @Nullable ClassLoader classLoader);

}
```

## 흐름에서 불리는 자리

```text
 RuntimeHintsBeanFactoryInitializationAotProcessor
   META-INF/spring/aot.factories 와 @ImportRuntimeHints 로 등록된 구현들을 모아
   registerHints(hints, classLoader) 를 부른다
```

- [BeanFactoryInitializationAotContributions.applyTo](../../03_BeanFactoryInitializationAotContributions.applyTo/README.md)

## 구현 계층

```text
 RuntimeHintsRegistrar
   +-- (프레임워크 모듈들의 구현)
         각 모듈이 자기 리플렉션 대상과 리소스를 등록한다
   +-- (사용자 구현)

 등록 방법
   META-INF/spring/aot.factories 의 RuntimeHintsRegistrar 키
   또는 @ImportRuntimeHints 를 설정 클래스나 빈에 붙인다
```

```text
 힌트의 종류

 reflection  클래스, 생성자, 메서드, 필드를 리플렉션으로 쓸 수 있게
 resources   클래스패스 리소스를 이미지에 포함
 serialization  직렬화 대상
 proxies     JDK 동적 프록시 인터페이스 조합
```

## 결과가 쓰이는 곳

```text
 등록한 힌트
      --> 생성 컨텍스트의 RuntimeHints 에 누적된다
      --> reachability-metadata.json 으로 쓰여 GraalVM 이 읽는다

 힌트가 없으면
      --> 네이티브 이미지에서 그 리플렉션이 런타임에 실패한다
      --> JVM 에서는 잘 되던 코드가 네이티브에서만 깨지는 전형적인 이유다

 classLoader 인자
      --> 조건부 등록에 쓴다. 특정 클래스가 있을 때만 힌트를 보태는 식이다

 코드를 생성하지 않는다는 점
      --> 기여를 만들지 않아도 되니 구현이 가장 가볍다
      --> 라이브러리가 네이티브를 지원하는 가장 흔한 방법이다
```
