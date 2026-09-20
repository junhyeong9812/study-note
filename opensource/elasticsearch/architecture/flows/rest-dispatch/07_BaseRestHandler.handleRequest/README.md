# BaseRestHandler.handleRequest

상위: [REST 디스패치](../README.md)

핸들러 쪽의 공통 골격이다. 파라미터를 검증하고, `prepareRequest` 로 **실행할 것**을 만든 다음, `accept` 로 시작한다. `final` 이라 핸들러가 이 순서를 바꿀 수 없다. 여기서 TransportAction 쪽으로 넘어간다.

## 위치

`server` / `org.elasticsearch.rest` / `BaseRestHandler.java` L79-L151 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/BaseRestHandler.java#L79-L151))

## 실제 코드

파라미터 화이트리스트. 선언한 핸들러에만 적용된다.

`server` / `org.elasticsearch.rest` / `BaseRestHandler.java` L81-L96 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/BaseRestHandler.java#L81-L96))

```java
// BaseRestHandler.java L81-L96
        Set<String> supported = allSupportedParameters();
        assert supported == allSupportedParameters() : getName() + ": did not return same instance from allSupportedParameters()";
        if (supported != null) {
            var allSupported = Sets.union(
                RestResponse.RESPONSE_PARAMS,
                ALWAYS_SUPPORTED,
                // these internal parameters cannot be set by end-users, but are used by Elasticsearch internally.
                // they must be accepted by all handlers
                RestRequest.INTERNAL_MARKER_REQUEST_PARAMETERS,
                supported
            );
            if (allSupported.containsAll(request.params().keySet()) == false) {
                Set<String> unsupported = Sets.difference(request.params().keySet(), allSupported);
                throw new IllegalArgumentException(unrecognized(request, unsupported, allSupported, "parameter"));
            }
        }
```

실행할 것은 핸들러가 만든다. L99 가 이것을 try-with-resources 로 부른다.

`server` / `org.elasticsearch.rest` / `BaseRestHandler.java` L259-L259 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/BaseRestHandler.java#L259-L259))

```java
// BaseRestHandler.java L259-L259
    protected abstract RestChannelConsumer prepareRequest(RestRequest request, NodeClient client) throws IOException;
```

만들고 난 뒤에 검사한다. 무엇이 읽혔는지 알아야 하기 때문이다.

`server` / `org.elasticsearch.rest` / `BaseRestHandler.java` L105-L127 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/BaseRestHandler.java#L105-L127))

```java
// BaseRestHandler.java L105-L127
            final SortedSet<String> unconsumedParams = request.unconsumedParams()
                .stream()
                .filter(p -> RestResponse.RESPONSE_PARAMS.contains(p) == false)
                .filter(p -> responseParams(request.getRestApiVersion()).contains(p) == false)
                .collect(Collectors.toCollection(TreeSet::new));

            // validate the non-response params
            if (unconsumedParams.isEmpty() == false) {
                final Set<String> candidateParams = new HashSet<>();
                candidateParams.addAll(request.consumedParams());
                candidateParams.addAll(responseParams(request.getRestApiVersion()));
                throw new IllegalArgumentException(unrecognized(request, unconsumedParams, candidateParams, "parameter"));
            }

            // Chunk consumers may defer reading until accept(), including when an interceptor has already aggregated the stream.
            if (request.hasContent()
                && request.isContentConsumed() == false
                && request.isFullContent()
                && action instanceof RequestBodyChunkConsumer == false) {
                throw new IllegalArgumentException(
                    "request [" + request.method() + " " + request.path() + "] does not support having a body"
                );
            }
```

실행을 시작한다.

`server` / `org.elasticsearch.rest` / `BaseRestHandler.java` L129-L149 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/rest/BaseRestHandler.java#L129-L149))

```java
// BaseRestHandler.java L129-L149
            usageCount.increment();
            if (request.isStreamedContent()) {
                assert action instanceof RequestBodyChunkConsumer;
                var chunkConsumer = (RequestBodyChunkConsumer) action;

                request.contentStream().setHandler(new HttpBody.ChunkHandler() {
                    @Override
                    public void onNext(ReleasableBytesReference chunk, boolean isLast) {
                        chunkConsumer.handleChunk(channel, chunk, isLast);
                    }

                    @Override
                    public void close() {
                        chunkConsumer.streamClose();
                    }
                });
                action.accept(channel);
            } else {
                action.accept(channel);
                request.getHttpRequest().release();
            }
```

## 동작 흐름

```text
 L81  supported = allSupportedParameters()
        기본값은 null 이다 (RestHandler L114)
 L83  supported != null 인 핸들러만
        L84  기본 허용 목록과 합쳐
        L92  요청 파라미터가 전부 그 안에 있는지 본다
        L94  아니면 IllegalArgumentException

 L99  try (var action = prepareRequest(request, client))
        핸들러가 구현하는 추상 메서드다 (L259)
        여기서 TransportRequest 를 만들고, 그것을 보낼 동작을 담아 돌려준다
        블록을 나가면 action.close() 가 불린다

 L105 소비되지 않은 파라미터를 모은다
 L112 남아 있으면 IllegalArgumentException
        오타 난 파라미터를 조용히 무시하지 않겠다는 뜻이다

 L120 본문이 있는데 아무도 안 읽었고, 다 와 있고,
      청크 소비자도 아니면
        L124  "이 요청은 본문을 받지 않는다" 예외

 L129 usageCount.increment()

 L130 request.isStreamedContent()
      |
      +-- true
      |     L134  contentStream().setHandler(ChunkHandler)   등록만 한다
      |           ~~> L137  onNext  -> chunkConsumer.handleChunk   청크마다
      |           ~~> L142  close   -> chunkConsumer.streamClose
      |     L145  action.accept(channel)                     여기서 실행이 시작된다
      |
      +-- false
            L147  action.accept(channel)                     여기서 실행이 시작된다
            L148  request.getHttpRequest().release()
```

```text
 두 단계로 나눈 이유

 prepareRequest  요청을 읽어 TransportRequest 를 만든다. 파라미터를 소비한다
 accept          만들어 둔 것을 실제로 보낸다

 사이에 검사가 들어간다 (L105-127)
 prepareRequest 가 무엇을 읽었는지 알아야
 "안 읽힌 파라미터"를 판정할 수 있기 때문이다

 순서를 뒤집으면 오타 난 파라미터를 걸러낼 수 없다
```

```text
 close 가 accept 직후에 불린다

 javadoc 이 직접 적어 두었다 (L211-215)
   "실행이 막 시작된 직후에 불린다. 대개 실행이 끝나기 훨씬 전이다"

 그래서 close 는 "끝났으니 정리한다"가 아니다
 prepareRequest 가 만들면서 잡은 참조를 놓는 자리다

 기본 구현은 아무 것도 하지 않는다 (L217)
```

```text
 release 가 한쪽에만 있다

 L148  비스트리밍  request.getHttpRequest().release()
 L145  스트리밍    없다

 스트리밍은 청크를 아직 받는 중이라
 여기서 요청 본문을 놓아 버릴 수 없다
```

## 결과가 쓰이는 곳

```text
 action.accept(channel)
      --> 이 한 줄 뒤가 transport action 흐름이다
      --> 대개 client.execute(...) 를 부르고 응답 리스너를 채널에 연결한다

 파라미터 검사 두 가지
      --> 화이트리스트(L83)는 선언한 핸들러만 받는다
      --> 미소비 검사(L112)는 모든 핸들러가 받는다
      --> 그래서 오타 난 파라미터는 400 으로 돌아온다

 usageCount
      --> _nodes/usage API 가 핸들러별 호출 수를 보여 준다
      --> 등록 때 usageService 에 담아 둔 것이다 (RestController L239-241)

 청크 소비자
      --> 스트리밍 핸들러만 RequestBodyChunkConsumer 를 돌려준다
      --> 본문은 accept 이후에 콜백으로 들어온다
```

## 다루지 않는 것

`prepareRequest` 구현들(핸들러마다 다르다), `RestChannelConsumer` 와 `Releasable` 의 참조 수명, `unrecognized` 가 오타에 가까운 이름을 제안하는 방식, `responseParams` 와 응답 전용 파라미터, `HttpBody.ChunkHandler` 의 배압 처리, `usageService` 통계 집계는 같은 뼈대의 곁가지라 요약만 했다.
