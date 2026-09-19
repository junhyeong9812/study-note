# Resource

상위: [Spring 리소스와 환경](../../README.md) / [spi](../README.md)

읽을 수 있는 자원 하나의 핸들이다. 파일, 클래스패스 항목, URL, 바이트 배열이 같은 타입으로 다뤄진다.

## 실제 코드

`spring-core` / `org.springframework.core.io` / `Resource.java` L59-L140 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-core/src/main/java/org/springframework/core/io/Resource.java#L59-L140))

```java
// Resource.java L59-L140
public interface Resource extends InputStreamSource {

    boolean exists();

    default boolean isReadable() {
        return exists();
    }

    default boolean isOpen() {
        return false;
    }

    default boolean isFile() {
        return false;
    }

    URL getURL() throws IOException;

    URI getURI() throws IOException;

    File getFile() throws IOException;

```

## 흐름에서 불리는 자리

```text
 getResource(location) 이 만들어 반환
 실제 접근은 나중에
   exists() / isReadable() / getInputStream() / getFile() / getURL()
```

- [DefaultResourceLoader.getResource](../../01_DefaultResourceLoader.getResource/README.md)

## 구현 계층

```text
 Resource
   +-- AbstractResource
         +-- AbstractFileResolvingResource       URL 을 파일로 풀어 볼 수 있는 계열
         |     +-- ClassPathResource             클래스패스 (classpath:)
         |     +-- UrlResource                   URL (http:, jar: ...)
         |     |     +-- FileUrlResource         file: URL
         |     +-- ServletContextResource        웹 애플리케이션 루트 기준
         +-- FileSystemResource                  파일 시스템
         +-- PathResource                        java.nio.file.Path 기반
         +-- ByteArrayResource                   메모리
         +-- InputStreamResource                 이미 열린 스트림 (한 번만 읽을 수 있다)

 주의
   getFile() 은 jar 안의 항목에서 실패한다 --> getInputStream() 을 쓴다
```
