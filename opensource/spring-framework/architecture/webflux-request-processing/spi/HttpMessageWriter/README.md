# HttpMessageWriter

상위: [Spring WebFlux 요청 처리](../../README.md) / [spi](../README.md)

객체 스트림을 HTTP 본문 바이트로 바꾼다. MVC의 `HttpMessageConverter` 쓰기 쪽에 대응하며, 내부적으로 `Encoder`를 감싼다.

## 실제 코드

`spring-web` / `org.springframework.http.codec` / `HttpMessageWriter.java` L44-L113 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-web/src/main/java/org/springframework/http/codec/HttpMessageWriter.java#L44-L113))

```java
// HttpMessageWriter.java L44-L113
public interface HttpMessageWriter<T> {

    List<MediaType> getWritableMediaTypes();

    default List<MediaType> getWritableMediaTypes(ResolvableType elementType) {
        return (canWrite(elementType, null) ? getWritableMediaTypes() : Collections.emptyList());
    }

    boolean canWrite(ResolvableType elementType, @Nullable MediaType mediaType);

    Mono<Void> write(Publisher<? extends T> inputStream, ResolvableType elementType,
            @Nullable MediaType mediaType, ReactiveHttpOutputMessage message, Map<String, Object> hints);

    default Mono<Void> write(Publisher<? extends T> inputStream, ResolvableType actualType,
            ResolvableType elementType, @Nullable MediaType mediaType, ServerHttpRequest request,
            ServerHttpResponse response, Map<String, Object> hints) {

        return write(inputStream, elementType, mediaType, response, hints);
    }

}
```

## 흐름에서 불리는 자리

```text
 AbstractMessageWriterResultHandler.writeBody
   반환 타입을 Publisher 로 정규화
   미디어 타입 선택
   canWrite(elementType, mediaType) 인 첫 writer 로 write
     --> Encoder 가 요소를 DataBuffer 로 인코딩해 응답에 흘려보낸다
```

- [HandlerResultHandler.handleResult](../../02_DispatcherHandler.handle/02_HandlerResultHandler.handleResult/README.md)

## 구현 계층

```text
 HttpMessageWriter<T>
   +-- EncoderHttpMessageWriter          Encoder 를 감싼 일반 구현
   |     +-- (JacksonJsonEncoder, CharSequenceEncoder, ByteBufferEncoder ...)
   +-- ServerSentEventHttpMessageWriter  text/event-stream
   +-- MultipartHttpMessageWriter
   +-- ResourceHttpMessageWriter

 등록
   CodecConfigurer (@EnableWebFlux 의 configureHttpMessageCodecs)
   MVC 의 컨버터 목록에 해당
```
