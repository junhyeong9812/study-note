# RSocketStrategies

상위: [Spring RSocket](../../README.md) / [spi](../README.md)

연결 양쪽이 공유해야 하는 설정 묶음이다. 인코더와 디코더, 라우트 매처, 메타데이터 추출기가 한 객체에 모여 있다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket` / `RSocketStrategies.java` L43-L70 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/RSocketStrategies.java#L43-L70))

```java
// RSocketStrategies.java L43-L70
public interface RSocketStrategies {

    List<Encoder<?>> encoders();

    @SuppressWarnings("unchecked")
    default <T> Encoder<T> encoder(ResolvableType elementType, @Nullable MimeType mimeType) {
        for (Encoder<?> encoder : encoders()) {
            if (encoder.canEncode(elementType, mimeType)) {
                return (Encoder<T>) encoder;
            }
        }
        throw new IllegalArgumentException("No encoder for " + elementType);
    }

```

## 흐름에서 불리는 자리

```text
 요청자   strategies.decoder(타입, dataMimeType) 로 응답을 디코딩
 서버     RSocketMessageHandler 가 인코더/디코더를 인자·반환값 처리기에 넘긴다
 양쪽     metadataExtractor 로 라우트를 꺼내고, routeMatcher 로 매핑을 비교한다
```

- [DefaultRSocketRequester.RequestSpec.retrieveMono](../../01_DefaultRSocketRequester.RequestSpec.retrieveMono/README.md)
- [MessagingRSocket.handleAndReply](../../02_MessagingRSocket.requestResponse/01_MessagingRSocket.handleAndReply/README.md)

## 구현 계층

```text
 RSocketStrategies
   +-- DefaultRSocketStrategies                 유일한 구현 (package-private)
         DefaultRSocketStrategiesBuilder        builder() 가 돌려주는 빌더

 담고 있는 것
   encoders / decoders      코덱 목록 (WebFlux 코덱과 같은 계열)
   routeMatcher             라우트 패턴 비교
                            기본은 SimpleRouteMatcher + AntPathMatcher(구분자 ".")
                            더 빠른 PathPatternRouteMatcher(spring-web)로 바꿀 수 있다
   metadataExtractor        메타데이터 --> 헤더 값
   reactiveAdapterRegistry  리액티브 타입 변환
   dataBufferFactory        버퍼 할당
```

## 결과가 쓰이는 곳

```text
 양쪽이 주고받는 타입을 처리할 코덱을 각자 갖고 있어야 한다
      --> 같은 인스턴스일 필요는 없다. 없으면 "No encoder for ..." 로 실패한다
      --> 같은 애플리케이션 안이라면 빈 하나를 공유하는 것이 보통이다

 encoder / decoder 조회
      --> 타입과 MimeType 으로 고른다. 없으면 예외가 난다
      --> dataMimeType 은 연결 수립 때 정해져 연결 내내 고정이다

 routeMatcher
      --> @MessageMapping("greet.{name}") 의 패턴 비교 규칙을 정한다
      --> 기본 구분자가 "." 라 라우트를 점으로 나누는 관례가 여기서 온다

 metadataExtractor
      --> 기본 구현은 라우트와 몇 가지 표준 메타데이터를 꺼낸다
      --> 커스텀 메타데이터는 등록해야 헤더로 올라온다
```
