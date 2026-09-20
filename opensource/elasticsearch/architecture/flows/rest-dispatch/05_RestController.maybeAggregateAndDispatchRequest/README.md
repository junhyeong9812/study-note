# RestController.maybeAggregateAndDispatchRequest

상위: [REST 디스패치](../README.md)

본문을 **다 모아서 넘길지, 흐르는 대로 넘길지** 정하는 단 하나의 분기다. 여기가 이 흐름에서 처음으로 한 스레드로 이어지지 않을 수 있는 자리다.

## 위치

`server` / `org.elasticsearch.rest` / `RestController.java` L511-L529 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/RestController.java#L511-L529))

## 실제 코드

```java
// RestController.java L511-L529
    private void maybeAggregateAndDispatchRequest(
        RestRequest restRequest,
        RestChannel restChannel,
        RestHandler handler,
        MethodHandlers methodHandlers,
        ThreadContext threadContext
    ) throws Exception {
        if (handler.supportsContentStream()) {
            dispatchRequest(restRequest, restChannel, handler, methodHandlers, threadContext);
        } else {
            RestContentAggregator.aggregate(restRequest, (aggregatedRequest) -> {
                try {
                    dispatchRequest(aggregatedRequest, restChannel, handler, methodHandlers, threadContext);
                } catch (Exception e) {
                    throw new ElasticsearchException(e);
                }
            });
        }
    }
```

## 동작 흐름

```text
 L518  handler.supportsContentStream()
       |
       +-- true
       |     +-- L519  dispatchRequest(restRequest, ...)   그대로 넘긴다
       |
       +-- false
             +-- L521  RestContentAggregator.aggregate(restRequest, 콜백)
                       |
                       +-- 본문이 이미 다 와 있으면 (HttpBody.Full)
                       |     RestContentAggregator L33  resultConsumer.accept(restRequest)
                       |     같은 스레드로 바로 L523 이 불린다
                       |
                       ~~> 본문이 스트림이면 (HttpBody.Stream)
                             L35-37  AggregationChunkHandler 를 달고 첫 청크를 요청한다
                             여기서 이 메서드는 끝난다. 나머지는 콜백이 한다

 L524  catch (Exception e)
         L523 이 던진 체크 예외를 ElasticsearchException 으로 감싸 던진다
         Consumer 가 체크 예외를 못 던지기 때문이다
```

```text
 청크가 이어지는 모양 (RestContentAggregator L56-91)

 onNext(chunk, isLast)
   L61  isLast == false  -> chunks 에 담고 stream.next()   다시 onNext 로 온다
   L67  isLast == true   -> 모은 것을 하나로 합쳐 본문을 갈아끼우고
        L78              -> resultConsumer.accept(restRequest)   여기서 [06] 으로

 close()
   L83  아직 끝나지 않았는데 닫히면
        모아 둔 청크만 풀고 끝낸다
        resultConsumer 를 부르지 않는다
```

```text
 예외가 어디로 가는지가 갈린다

 Full 경로    L525 의 예외가 그대로 스택을 타고 올라간다
              tryAllHandlers 를 지나 [01] 의 catch (L429) 가 받는다

 Stream 경로  마지막 청크 콜백은 [01] 이 이미 끝난 뒤에 불린다
              그때 나는 예외는 [01] 의 catch 를 지나칠 수밖에 없다
              HTTP 계층이 받는다

 같은 코드가 상황에 따라 다른 곳으로 예외를 보낸다
```

```text
 스트림을 받는 핸들러는 셋뿐이다

 기본값이 false 다 (RestHandler L49)
 true 로 재정의한 것
   RestBulkAction                     _bulk
   AbstractOTLPRestAction             OTLP 수집
   PrometheusRemoteWriteRestAction    Prometheus remote write

 셋 다 본문이 아주 커질 수 있는 API 다

 단, deprecated 라우트로 등록되면 이야기가 달라진다
 FilterRestHandler 는 위임하는 메서드가 여섯 개인데 (L26-54)
 supportsContentStream 이 거기 없다
 그래서 래핑되면 기본값 false 가 나와 집계 경로로 간다
```

## 결과가 쓰이는 곳

```text
 넘어가는 RestRequest
      --> Full 이면 원래 객체 그대로다
      --> Stream 이었다면 본문이 갈아끼워진 같은 객체다
          replaceBody 가 in-place 로 바꾼다

 한 스레드로 이어지는가
      --> 여기까지가 갈림길이다. 이 뒤로도 [06] 의 인터셉터에서 한 번 더 갈린다
      --> 기본 경로(본문이 다 와 있고 인터셉터가 동기)는 끝까지 한 스레드다

 조용히 끝나는 경우
      --> close() 로 먼저 닫히면 [06] 이 영영 안 불린다
      --> 응답도 나가지 않는다. 연결이 이미 끊어진 상황이다
```

## 다루지 않는 것

`HttpBody` 의 Full/Stream 구분이 정해지는 곳, `RestContentAggregator` 가 청크를 합치는 `CompositeBytesReference` 와 참조 카운팅, `stream.next()` 가 이벤트 루프로 넘어가는 경로(Netty4), `SecurityRestFilter` 가 감사 로깅을 위해 같은 `aggregate` 를 한 번 더 부르는 갈래는 같은 뼈대의 곁가지라 요약만 했다.
