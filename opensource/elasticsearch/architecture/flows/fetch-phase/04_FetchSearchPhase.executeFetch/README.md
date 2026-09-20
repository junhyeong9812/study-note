# FetchSearchPhase.executeFetch

상위: [페치 페이즈](../README.md)

샤드 하나에 **페치 요청을 보낸다**. 응답 리스너가 성공과 실패를 각각 카운터로 넘기고, 실패 쪽은 검색 컨텍스트도 닫아 준다. 다만 연결이 끊긴 경우에는 그 정리마저 실패한다.

## 위치

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L201-L269 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L201-L269))

## 실제 코드

응답을 받을 리스너를 만든다.

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L208-L237 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L208-L237))

```java
// FetchSearchPhase.java L208-L237
        final SearchShardTarget shardTarget = shardPhaseResult.getSearchShardTarget();
        final int shardIndex = shardPhaseResult.getShardIndex();
        final ShardSearchContextId contextId = shardPhaseResult.queryResult() != null
            ? shardPhaseResult.queryResult().getContextId()
            : shardPhaseResult.rankFeatureResult().getContextId();
        var listener = new SearchActionListener<FetchSearchResult>(shardTarget, shardIndex) {
            @Override
            public void innerOnResponse(FetchSearchResult result) {
                try {
                    progressListener.notifyFetchResult(shardIndex);
                    counter.onResult(result);
                } catch (Exception e) {
                    context.onPhaseFailure(NAME, "", e);
                }
            }

            @Override
            public void onFailure(Exception e) {
                try {
                    logger.debug(() -> "[" + contextId + "] Failed to execute fetch phase", e);
                    progressListener.notifyFetchFailure(shardIndex, shardTarget, e);
                    counter.onFailure(shardIndex, shardTarget, e);
                } finally {
                    // the search context might not be cleared on the node where the fetch was executed for example
                    // because the action was rejected by the thread pool. in this case we need to send a dedicated
                    // request to clear the search context.
                    releaseIrrelevantSearchContext(shardPhaseResult, context);
                }
            }
        };
```

연결을 잡고 요청을 보낸다. 두 번째 줄부터는 try 밖이다.

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L239-L268 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L239-L268))

```java
// FetchSearchPhase.java L239-L268
        final Transport.Connection connection;
        try {
            connection = context.getConnection(shardTarget.getClusterAlias(), shardTarget.getNodeId());
        } catch (Exception e) {
            listener.onFailure(e);
            return;
        }
        ShardSearchRequest fetchShardSearchRequest = context.buildShardSearchRequest(
            context.shardIterators[shardPhaseResult.getShardIndex()],
            shardPhaseResult.getShardIndex()
        );
        context.getSearchTransport()
            .sendExecuteFetch(
                connection,
                new ShardFetchSearchRequest(
                    context.getOriginalIndices(shardPhaseResult.getShardIndex()),
                    contextId,
                    fetchShardSearchRequest,
                    entry,
                    rankDocs,
                    lastEmittedDocForShard,
                    shardPhaseResult.getRescoreDocIds(),
                    aggregatedDfs
                ),
                context,
                shardTarget,
                listener,
                context::trackPhaseResultBytesRead,
                context::trackPhaseRequestBytesWritten
            );
```

## 동작 흐름

```text
 L210  contextId 를 꺼낸다
         queryResult() 가 있으면 거기서
         없으면 rankFeatureResult() 에서
         둘 다 null 이면 NPE. 가드가 없다

 L213  리스너
       성공 innerOnResponse                      L215
         L217  notifyFetchResult
         L218  counter.onResult(result)
         L219  catch -> context.onPhaseFailure    L220
       실패 onFailure                             L225
         L228  notifyFetchFailure
         L229  counter.onFailure(shardIndex, shardTarget, e)
         L234  finally releaseIrrelevantSearchContext

 L240  try
       L241  getConnection
       L242  실패하면 listener.onFailure(e)       L243
             후 return                            L244

 L246  buildShardSearchRequest      try 가 L245 에서 닫혔다. 여기는 밖이다
 L250  sendExecuteFetch(...)
         ~~> 응답이 오면 위 리스너로
```

```text
 try 가 getConnection 만 감싼다

 L240 의 try 는 L245 에서 닫힌다
 그 아래 L246 buildShardSearchRequest 와 L250 sendExecuteFetch 는 밖이다

 그래서 요청 조립이 실패하면
 이 메서드를 뚫고 나가 [03] 의 루프를 중단시킨다
 남은 샤드는 요청도 못 받고 카운트도 안 된다

 그 예외는 결국 [01] 의 onFailure 가 받아 페이즈를 실패시킨다
```

```text
 컨텍스트가 새는 길

 getConnection 이 실패하면 (L241-243)
   listener.onFailure -> L234 finally -> releaseIrrelevantSearchContext
   그런데 그 안이 같은 getConnection 을 다시 부른다 (SearchPhase L87)
   같은 이유로 또 실패하고 catch 가 삼킨다 (SearchPhase L89-91)

 그 뒤 페이즈가 실패하면 raisePhaseFailure 도 getConnection 을 쓴다
   (AbstractSearchAsyncAction L834)

 노드에 닿지 못하는 상황이면 세 번 다 실패한다
 데이터 노드 쪽 컨텍스트는 keep-alive 만료까지 남는다
```

```text
 실패 쪽에서 컨텍스트를 닫는 이유

 주석이 적어 두었다 (L231-233)
   페치를 실행한 노드에서 검색 컨텍스트가 정리되지 않았을 수 있다
   예를 들어 스레드풀이 요청을 거부한 경우다
   그런 때를 위해 별도 요청을 보내 정리한다

 즉 데이터 노드가 보통은 알아서 닫지만
 요청이 실행조차 안 된 경우를 대비한 이중 안전장치다
```

```text
 진행 상황 알림은 예외를 삼킨다

 notifyFetchResult 와 notifyFetchFailure 는
 안에서 try/catch 로 예외를 잡고 warn 로그만 남긴다

 그래서 L219 의 catch 가 실제로 잡는 것은
 counter.onResult 쪽 예외다
   결과 저장, 참조 수 증가, 그리고
   마지막 countDown 이 불러낸 merge 까지
```

## 결과가 쓰이는 곳

```text
 counter.onResult / onFailure
      --> 둘 다 countDown 으로 이어진다
      --> 0이 되면 moveToNextPhase 가 돈다

 contextId
      --> 데이터 노드가 이것으로 아까 그 검색 컨텍스트를 찾는다
      --> 쿼리 결과와 rank 결과가 같은 id 를 쓴다

 ShardFetchSearchRequest
      --> 가져올 문서 번호, rank 정보, 스크롤 위치를 담는다
      --> 바이트 추적 콜백이 붙어 페이즈별 전송량이 기록된다

 3-arg onShardFailure
      --> counter.onFailure 가 이것을 부른다
      --> 재시도가 없는 쪽이다. 실패를 기록만 한다
```

## 다루지 않는 것

`SearchTransportService.sendExecuteFetch` 의 청크 경로 분기와 그 조건, `ShardFetchSearchRequest` 의 내용, 데이터 노드 쪽 페치 실행과 컨텍스트 해제(`SearchService`), `buildShardSearchRequest` 의 요청 조립, `SearchProgressListener` 의 알림 처리는 같은 뼈대의 곁가지라 요약만 했다.
