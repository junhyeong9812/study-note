# performPhaseOnShard / doPerformPhaseOnShard

상위: [검색 페이즈](../README.md)

샤드 하나에 **실제로 요청을 보낸다**. 노드당 동시 요청 제한이 있으면 그 관문을 먼저 지나고, 응답을 받을 리스너를 달아 전송한다. [재시도](../06_AbstractSearchAsyncAction.onShardFailure/README.md)도 이 메서드로 되돌아온다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L280-L319 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L280-L319))

## 실제 코드

노드당 제한이 있으면 관문을 지난다.

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L280-L291 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L280-L291))

```java
// AbstractSearchAsyncAction.java L280-L291
    protected final void performPhaseOnShard(final int shardIndex, final SearchShardIterator shardIt, final SearchShardTarget shard) {
        var pendingExecutionsPerNode = this.pendingExecutionsPerNode;
        if (pendingExecutionsPerNode != null) {
            var pendingExecutions = pendingExecutionsPerNode.computeIfAbsent(
                shard.getNodeId(),
                n -> new PendingExecutions(maxConcurrentRequestsPerNode)
            );
            pendingExecutions.submit(l -> doPerformPhaseOnShard(shardIndex, shardIt, shard, l));
        } else {
            doPerformPhaseOnShard(shardIndex, shardIt, shard, () -> {});
        }
    }
```

리스너를 달고 보낸다.

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L293-L319 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L293-L319))

```java
// AbstractSearchAsyncAction.java L293-L319
    private void doPerformPhaseOnShard(int shardIndex, SearchShardIterator shardIt, SearchShardTarget shard, Releasable releasable) {
        var shardListener = new SearchActionListener<Result>(shard, shardIndex) {
            @Override
            public void innerOnResponse(Result result) {
                try {
                    releasable.close();
                    onShardResult(result);
                } catch (Exception exc) {
                    onShardFailure(shardIndex, shard, shardIt, exc);
                }
            }

            @Override
            public void onFailure(Exception e) {
                releasable.close();
                onShardFailure(shardIndex, shard, shardIt, e);
            }
        };
        final Transport.Connection connection;
        try {
            connection = getConnection(shard.getClusterAlias(), shard.getNodeId());
        } catch (Exception e) {
            shardListener.onFailure(e);
            return;
        }
        executePhaseOnShard(shardIt, connection, shardListener);
    }
```

## 동작 흐름

```text
 L282  pendingExecutionsPerNode != null
       +-- L283  노드별 PendingExecutions 를 꺼내거나 만든다
       +-- L287  submit(l -> doPerformPhaseOnShard(...))
 L288  아니면
       +-- L289  doPerformPhaseOnShard(..., () -> {})

 doPerformPhaseOnShard                                    L293
 L294  shardListener 를 만든다
         성공 L296  releasable.close() 후 onShardResult      -> [07]
                    그 안에서 예외가 나면 onShardFailure       -> [06]
         실패 L306  releasable.close() 후 onShardFailure       -> [06]
 L313  getConnection(clusterAlias, nodeId)
       +-- L314  실패하면 shardListener.onFailure(e) 후 return
 L318  executePhaseOnShard(shardIt, connection, shardListener)   추상 L332
```

```text
 제한 관문이 항상 경계는 아니다

 PendingExecutions.submit (L945-957)
   L946  semaphore.tryAcquire() 가 성공하면
         L947  executeAndRelease(task) 로 그 자리에서 실행한다
   실패하면 큐에 넣는다

 executeAndRelease (L959-984)
   L963  앞 작업이 이미 끝나 있으면 다음 것을 같은 스레드에서 계속한다
   아니면 리스너를 걸고 돌아간다

 즉 여유가 있으면 스레드가 안 바뀐다
 꽉 찼을 때만 나중에 다른 스레드가 이어받는다
```

```text
 전송도 항상 비동기는 아니다

 executePhaseOnShard 구현은 셋이다
   SearchQueryThenFetchAsyncAction L164
   SearchDfsQueryThenFetchAsyncAction L110
   TransportOpenPointInTimeAction L433
 셋 다 transportService.sendChildRequest 를 쓴다

 원격 노드면 네트워크 스레드가 응답을 처리한다. 경계가 맞다

 로컬 노드는 다르다
   핸들러 executor 가 DIRECT 라 호출 스레드에서 처리되고
   canReturnNullResponseIfMatchNoDocs 이고 canMatch 가 false 면
   SearchService 가 그 자리에서 null 결과로 응답한다
   그러면 onShardResult 가 doRun 루프와 같은 스레드에서 돈다
```

```text
 getConnection 실패는 끝이 아니다

 L315 가 shardListener.onFailure 를 부르고 return 한다
 그런데 그 리스너는 onShardFailure 로 간다 (L308)

 거기서 재시도 판정을 하고, 안 되면 finishOneShard 로 간다
 그것이 마지막 샤드였으면 onPhaseDone 까지 같은 스택에서 이어진다

 즉 "여기서 끝난다"가 아니라 실패 사슬로 들어가는 것이다
```

```text
 releasable 을 닫는 자리가 둘이다

 L298 성공, L307 실패
 둘 다 결과를 처리하기 전에 닫는다

 닫아야 노드당 제한의 허가가 돌아가고
 큐에 기다리던 다음 샤드가 나갈 수 있다
```

## 결과가 쓰이는 곳

```text
 shardListener
      --> SearchActionListener 라 응답에 shardIndex 와 타겟을 먼저 새긴다
      --> 그 번호로 결과가 제자리에 들어간다

 노드당 제한
      --> 한 노드에 요청이 몰리는 것을 막는다
      --> 재시도도 이 관문을 다시 지난다

 onShardResult / onShardFailure
      --> 둘 다 outstandingShards 회계로 이어진다
      --> 다만 실패는 재시도를 거칠 수 있어 바로 줄지 않는다
```

## 다루지 않는 것

`PendingExecutions` 의 큐 관리와 허가 반납, `executePhaseOnShard` 구현 셋의 요청 조립(`ShardSearchRequest`, `bottomSortCollector` 재작성 등), `SearchTransportService` 와 전송 계층, 샤드 쪽 실행(`SearchService.executeQueryPhase`), `SearchActionListener` 의 래핑은 같은 뼈대의 곁가지라 요약만 했다.
