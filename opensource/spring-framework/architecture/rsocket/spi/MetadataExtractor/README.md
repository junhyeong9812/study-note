# MetadataExtractor

상위: [Spring RSocket](../../README.md) / [spi](../README.md)

프레임의 메타데이터를 헤더로 쓸 수 있는 맵으로 바꾼다. RSocket에는 HTTP 헤더 같은 것이 없으므로, 라우트조차 이 경로로 꺼낸다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket` / `MetadataExtractor.java` L37-L56 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/MetadataExtractor.java#L37-L56))

```java
// MetadataExtractor.java L37-L56
public interface MetadataExtractor {

    String ROUTE_KEY = "route";

    Map<String, Object> extract(Payload payload, MimeType metadataMimeType);

}
```

## 흐름에서 불리는 자리

```text
 MessagingRSocket.createHeaders
   metadataExtractor.extract(payload, metadataMimeType)
     ROUTE_KEY 가 있으면 라우트로 파싱해 헤더에 싣는다
     없으면 빈 문자열을 기본값으로 넣는다
```

- [MessagingRSocket.handleAndReply](../../02_MessagingRSocket.requestResponse/01_MessagingRSocket.handleAndReply/README.md)

## 구현 계층

```text
 MetadataExtractor
   +-- DefaultMetadataExtractor    MetadataExtractorRegistry 도 함께 구현한다
         메타데이터 MimeType 마다 꺼내는 방법을 등록해 둔다
         복합 메타데이터(composite)면 항목별로 나눠 처리한다

 ROUTE_KEY
   추출 결과 맵에서 라우트를 담는 표준 키다
```

## 결과가 쓰이는 곳

```text
 추출된 맵
      --> 그대로 MessageHeaders 에 올라간다
      --> @Header 로 핸들러 메서드 인자에 받을 수 있다

 라우트가 없을 때
      --> 빈 문자열이 기본값이 된다
      --> 빈 라우트에 매핑된 메서드가 있으면 그쪽이 불린다

 커스텀 메타데이터
      --> MetadataExtractorRegistry 로 (MimeType, 키, 디코딩 방법)을 등록한다
      --> 등록하지 않으면 헤더에 올라오지 않는다

 메타데이터 MimeType
      --> 연결 수립 때 정해진다. 복합 메타데이터가 기본 선택이다
```
