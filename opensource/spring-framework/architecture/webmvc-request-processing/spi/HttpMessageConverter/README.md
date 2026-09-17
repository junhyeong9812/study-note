# HttpMessageConverter

상위: [Spring MVC 요청 처리](../../README.md) / [spi](../README.md)

HTTP 본문과 자바 객체를 서로 변환한다. `@RequestBody` 읽기와 `@ResponseBody` 쓰기가 모두 이 인터페이스를 쓴다.

## 실제 코드

`spring-web` / `org.springframework.http.converter` / `HttpMessageConverter.java` L39-L129 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/http/converter/HttpMessageConverter.java#L39-L129))

```java
// HttpMessageConverter.java L39-L129
public interface HttpMessageConverter<T> {

    boolean canRead(Class<?> clazz, @Nullable MediaType mediaType);

    boolean canWrite(Class<?> clazz, @Nullable MediaType mediaType);

    default boolean canWriteRepeatedly(T t, @Nullable MediaType contentType) {
        return false;
    }

    List<MediaType> getSupportedMediaTypes();

    default List<MediaType> getSupportedMediaTypes(Class<?> clazz) {
        return (canRead(clazz, null) || canWrite(clazz, null) ?
                getSupportedMediaTypes() : Collections.emptyList());
    }

    T read(Class<? extends T> clazz, HttpInputMessage inputMessage)
            throws IOException, HttpMessageNotReadableException;

    void write(T t, @Nullable MediaType contentType, HttpOutputMessage outputMessage)
            throws IOException, HttpMessageNotWritableException;

}
```

## 흐름에서 불리는 자리

```text
 쓰기  AbstractMessageConverterMethodProcessor.writeWithMessageConverters
          --> for converter: canWrite(type, selectedMediaType) --> 첫 true로 write
 읽기  AbstractMessageConverterMethodArgumentResolver.readWithMessageConverters
          --> for converter: canRead(type, contentType)       --> 첫 true로 read
```

- [writeWithMessageConverters](../../02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/01_AbstractMessageConverterMethodProcessor.writeWithMessageConverters/README.md)
- [getMethodArgumentValues](../../02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/01_InvocableHandlerMethod.getMethodArgumentValues/README.md)

## 구현 계층

```text
 HttpMessageConverter<T>
   +-- ByteArrayHttpMessageConverter      byte[]
   +-- StringHttpMessageConverter         String, text/*
   +-- ResourceHttpMessageConverter       Resource
   +-- AllEncompassingFormHttpMessageConverter   폼, multipart
   +-- GenericHttpMessageConverter        제네릭 타입 인지 (List<User>)
   +-- SmartHttpMessageConverter          ResolvableType + 힌트
         +-- JacksonJsonHttpMessageConverter    JSON (Jackson 3)
   등록 순서가 우선순위. String 반환이 JSON 따옴표 없이 나가는 이유 = StringHttpMessageConverter가 앞
```
