# TransportType

상위: [Spring SockJS](../../README.md) / [spi](../README.md)

전송 방식의 목록이자, 각 방식이 쓰는 HTTP 메서드와 CORS 지원 여부를 담은 열거형이다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.transport` / `TransportType.java` L35-L60 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/transport/TransportType.java#L35-L60))

```java
// TransportType.java L35-L60
public enum TransportType {

    WEBSOCKET("websocket", HttpMethod.GET, "origin"),

    XHR("xhr", HttpMethod.POST, "cors", "jsessionid", "no_cache"),

    XHR_SEND("xhr_send", HttpMethod.POST, "cors", "jsessionid", "no_cache"),

    XHR_STREAMING("xhr_streaming", HttpMethod.POST, "cors", "jsessionid", "no_cache"),

    EVENT_SOURCE("eventsource", HttpMethod.GET, "origin", "jsessionid", "no_cache"),

    HTML_FILE("htmlfile", HttpMethod.GET, "cors", "jsessionid", "no_cache");

    private static final Map<String, TransportType> TRANSPORT_TYPES =
            Arrays.stream(values()).collect(Collectors.toUnmodifiableMap(type -> type.value, type -> type));

    public static @Nullable TransportType fromValue(String value) {
        return TRANSPORT_TYPES.get(value);
    }

    private final String value;

```

## 흐름에서 불리는 자리

```text
 TransportHandlingSockJsService.handleTransportRequest
   L245 TransportType.fromValue(transport)   URL 의 마지막 조각을 열거형으로
   L267 transportType.getHttpMethod()        기대 메서드와 실제 메서드 비교
        transportType.supportsCors()         OPTIONS 응답 여부 결정
```

- [TransportHandlingSockJsService.handleTransportRequest](../../02_TransportHandlingSockJsService.handleTransportRequest/README.md)

## 구현 계층

```text
 TransportType (열거형)
   WEBSOCKET          websocket        GET
   XHR                xhr              POST
   XHR_SEND           xhr_send         POST
   XHR_STREAMING      xhr_streaming    POST
   EVENT_SOURCE       eventsource      GET
   HTML_FILE          htmlfile         GET

 값 문자열이 URL 의 마지막 조각과 그대로 대응한다
```

## 결과가 쓰이는 곳

```text
 getHttpMethod()
      --> 메서드가 다르면 405 를 돌려준다
      --> 같은 URL 이라도 GET 과 POST 가 다른 전송이라는 뜻이다

 supportsCors()
      --> true 인 전송만 OPTIONS 프리플라이트에 응답한다
      --> websocket 과 eventsource 는 "origin" 힌트만 있어 false 다

 fromValue(문자열)
      --> 모르는 값이면 null. 호출자가 404 로 처리한다
```
