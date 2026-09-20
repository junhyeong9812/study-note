# SockJsMessageCodec

상위: [Spring SockJS](../../README.md) / [spi](../README.md)

메시지 배열과 JSON 문자열 사이를 오간다. SockJS 프로토콜이 메시지를 JSON 배열로 싣기 때문에 필요하다.

## 실제 코드

`spring-websocket` / `org.springframework.web.socket.sockjs.frame` / `SockJsMessageCodec.java` L35-L63 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-websocket/src/main/java/org/springframework/web/socket/sockjs/frame/SockJsMessageCodec.java#L35-L63))

```java
// SockJsMessageCodec.java L35-L63
public interface SockJsMessageCodec {

    String encode(String... messages);

    String @Nullable [] decode(String content) throws IOException;

    String @Nullable [] decodeInputStream(InputStream content) throws IOException;

}
```

## 흐름에서 불리는 자리

```text
 받는 길   readMessages(request) 가 본문 JSON 배열을 String[] 로 푼다
 보내는 길 메시지 프레임 "a[...]" 를 만들 때 배열을 JSON 으로 인코딩한다
```

- [받는 길](../../04_AbstractHttpReceivingTransportHandler.handleRequest/README.md)

## 구현 계층

```text
 SockJsMessageCodec
   +-- AbstractSockJsMessageCodec           JSON 이스케이프 공통 처리
         +-- JacksonJsonSockJsMessageCodec  잭슨 3 기반 (기본)
         +-- Jackson2SockJsMessageCodec     잭슨 2 기반

 SockJsServiceRegistration.setMessageCodec(...) 으로 바꿀 수 있다
```

```text
 왜 전용 코덱이 필요한가

 SockJS 프로토콜은 일부 유니코드 문자를 반드시 \\uXXXX 로 이스케이프하도록 정한다
 (SockJS 프로토콜 규격의 escapable_by_server 목록을 따른다)
 AbstractSockJsMessageCodec 이 그 규칙을 구현한다
```

## 결과가 쓰이는 곳

```text
 decode(String)
      --> 본문 JSON 배열을 String[] 로 만든다
      --> 실패하면 받는 길이 500 과 함께 "Broken JSON encoding." 을 돌려준다

 encode(String...)
      --> 메시지 프레임 본문이 된다
      --> 프레임 포맷("a[...]") 은 SockJsFrame 이 씌운다

 코덱이 없으면
      --> 기동 때는 조용히 null 인 채 넘어간다
      --> 메시지를 주고받는 순간 getMessageCodec 의 Assert.state 가
          IllegalStateException 을 던진다
      --> /info 나 열기 프레임처럼 코덱이 필요 없는 경로는 잭슨 없이도 동작한다
```
