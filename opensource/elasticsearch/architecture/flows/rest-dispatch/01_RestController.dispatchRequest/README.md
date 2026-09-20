# RestController.dispatchRequest

상위: [REST 디스패치](../README.md)

HTTP 계층이 부르는 진입점이다. 하는 일은 둘뿐이다. 응답 헤더 하나를 달고, [tryAllHandlers](../02_RestController.tryAllHandlers/README.md)를 부르면서 예외를 받아 준다. 같은 클래스에 이름이 같은 [private 5-arg](../06_RestController.dispatchRequest-private/README.md)가 따로 있는데, 실제 검사와 인터셉터는 그쪽이 한다.

## 위치

`server` / `org.elasticsearch.rest` / `RestController.java` L425-L437 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L425-L437))

## 실제 코드

```java
// RestController.java L425-L437
    public void dispatchRequest(RestRequest request, RestChannel channel, ThreadContext threadContext) {
        threadContext.addResponseHeader(ELASTIC_PRODUCT_HTTP_HEADER, ELASTIC_PRODUCT_HTTP_HEADER_VALUE);
        try {
            tryAllHandlers(request, channel, threadContext);
        } catch (Exception e) {
            try {
                sendFailure(channel, e);
            } catch (Exception inner) {
                inner.addSuppressed(e);
                logger.error(() -> "failed to send failure response for uri [" + request.uri() + "]", inner);
            }
        }
    }
```

## 동작 흐름

```text
 L426  addResponseHeader(ELASTIC_PRODUCT_HTTP_HEADER, ...)
         "X-elastic-product: Elasticsearch" 를 응답에 예약한다
         아래에서 무슨 일이 나든 이 헤더는 붙는다

 L428  tryAllHandlers(request, channel, threadContext)
         여기서 핸들러를 찾고 실행까지 간다

 L429  catch (Exception e)
         |
         +-- L431  sendFailure(channel, e)
         |
         +-- L432  그 전송마저 실패하면
                   L433  inner.addSuppressed(e)   원래 예외를 붙여 두고
                   L434  logger.error(...)        로그만 남기고 끝낸다
```

```text
 왜 여기서 예외를 잡는가

 tryAllHandlers 는 throws Exception 으로 선언돼 있다 (L702)
 그 아래의 검사들이 던지는 것을 여기가 다 받는다

 그런데 받을 수 있는 것은 "아직 이 스택 위에 있는" 예외뿐이다
 본문이 스트림이라 콜백으로 넘어간 뒤에 나는 예외는
 이 catch 를 이미 지나쳐 버린 상태다 (05 에서 다룬다)
```

## 결과가 쓰이는 곳

```text
 X-elastic-product 헤더
      --> 클라이언트가 상대가 진짜 Elasticsearch 인지 확인하는 데 쓴다
      --> 오류 응답에도 붙는다. 맨 처음에 달기 때문이다

 여기서 잡힌 예외
      --> sendFailure 가 RestResponse 로 바꿔 내보낸다 (L632-636)
      --> 같은 자리에서 메트릭도 기록한다 (L635)

 잡지 못한 경우
      --> 응답이 나가지 않는다. 로그만 남는다
      --> 클라이언트는 연결이 끊기는 것으로 본다
```

## 다루지 않는 것

`AbstractHttpServerTransport` 가 이 메서드를 부르기 전에 하는 일(스레드 컨텍스트 스택, 잘못된 요청의 조기 분기, 플러그인의 `populatePerRequestThreadContext`), `sendFailure` 가 예외를 상태 코드로 바꾸는 규칙, `RestResponse` 직렬화, 헤더 상수의 값이 정해지는 곳은 같은 뼈대의 곁가지라 요약만 했다.
