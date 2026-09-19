# RSocketExchange

상위: [Spring RSocket](../../README.md) / [spi](../README.md)

인터페이스에 애노테이션만 붙여 RSocket 클라이언트를 만드는 선언형 방식이다. HTTP 쪽 `@HttpExchange`와 짝을 이룬다.

## 실제 코드

`spring-messaging` / `org.springframework.messaging.rsocket.service` / `RSocketExchange.java` L75-L87 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-messaging/src/main/java/org/springframework/messaging/rsocket/service/RSocketExchange.java#L75-L87))

```java
// RSocketExchange.java L75-L87
public @interface RSocketExchange {

    String value() default "";

}
```

## 흐름에서 불리는 자리

```text
 RSocketServiceProxyFactory 가 인터페이스를 프록시로 만든다
   메서드마다 RSocketServiceMethod 를 준비한다
     @RSocketExchange 의 value 가 라우트
     인자는 @Payload, @DestinationVariable, 그리고 값 뒤에 MimeType 을 붙인
       메타데이터로 해석한다 (@Header 는 지원하지 않는다)
     반환 타입이 상호작용을 정한다 (Mono / Flux / void)
   호출 시 RSocketRequester 로 실제 요청을 만든다
```

- [DefaultRSocketRequester.RequestSpec.retrieveMono](../../01_DefaultRSocketRequester.RequestSpec.retrieveMono/README.md)

## 구현 계층

```text
 @RSocketExchange            메서드(또는 타입)에 붙는 애노테이션
 RSocketServiceProxyFactory  인터페이스 --> 프록시
 RSocketServiceMethod        메서드 하나의 호출 규칙
 RSocketServiceArgumentResolver  인자 해석 계약 (등록되는 것은 이 셋뿐이다)
   +-- PayloadArgumentResolver
   +-- DestinationVariableArgumentResolver
   +-- MetadataArgumentResolver
```

```text
 세 가지 클라이언트 방식

 RSocketRequester 직접 호출   가장 낮은 수준, 모든 것을 직접 정한다
 @RSocketExchange 인터페이스  라우트와 타입만 선언, 호출은 프록시가 조립
 RSocket API 직접 사용        스프링을 벗어난다
```

## 결과가 쓰이는 곳

```text
 반환 타입
      --> Mono<T> 면 requestResponse, Flux<T> 면 requestStream
      --> void 나 Mono<Void> 는 페이로드가 있으면 fireAndForget,
          페이로드 없이 메타데이터만 있으면 metadataPush 로 간다

 타입 수준 애노테이션
      --> 라우트 접두를 공유할 때 쓴다
      --> 메서드 값과 이어 붙는다

 AOT 지원
      --> RSocketExchangeBeanRegistrationAotProcessor 가 프록시 인터페이스를
          네이티브 이미지 힌트로 등록한다
```
