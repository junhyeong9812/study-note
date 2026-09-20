# AbstractSearchAsyncAction.onShardFailure

상위: [검색 페이즈](../README.md)

샤드가 실패했을 때 **다음 복제본으로 다시 해볼지, 접을지**를 정한다. 이름이 같은 메서드가 둘인데 하는 일이 다르다 — 4-arg 가 재시도를 결정하고, 3-arg 는 기록만 한다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L454-L478 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L454-L478))

## 실제 코드

재시도를 결정한다.

```java
// AbstractSearchAsyncAction.java L454-L478
    protected final void onShardFailure(final int shardIndex, SearchShardTarget shard, final SearchShardIterator shardIt, Exception e) {
        // we always add the shard failure for a specific shard instance
        // we do make sure to clean it on a successful response from a shard
        onShardFailure(shardIndex, shard, e);
        final SearchShardTarget nextShard = shardIt.nextOrNull();
        final boolean lastShard = nextShard == null;
        final boolean retriable = TransportActions.isRetriableShardLevelException(e);
        logger.debug(() -> format("%s: Failed to execute [%s] lastShard [%s] retriable [%s]", shard, request, lastShard, retriable), e);
        if (lastShard == false && retriable) {
            logger.debug("Retrying shard [{}] with target [{}]", shard.getShardId(), nextShard);
            performPhaseOnShard(shardIndex, shardIt, nextShard);
        } else {
            if (request.allowPartialSearchResults() == false) {
                if (internalCancelTriggered.compareAndSet(false, true)) {
                    try {
                        searchTransportService.cancelSearchTask(task, INTERNAL_PARTIAL_RESULTS_CANCEL_REASON);
                    } catch (Exception cancelFailure) {
                        logger.debug("Failed to cancel search request", cancelFailure);
                    }
                }
            }
            onShardGroupFailure(shardIndex, shard, e);
            finishOneShard();
        }
    }
```

기록만 하는 쪽이다. 실패 배열을 만들고 채운다.

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L506-L544 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L506-L544))

```java
// AbstractSearchAsyncAction.java L506-L544
    void onShardFailure(final int shardIndex, SearchShardTarget shardTarget, Exception e) {
        if (TransportActions.isShardNotAvailableException(e)) {
            // Groups shard not available exceptions under a generic exception that returns a SERVICE_UNAVAILABLE(503)
            // temporary error.
            e = NoShardAvailableActionException.forOnShardFailureWrapper(e.getMessage());
        }
        // we don't aggregate shard on failures due to the internal cancellation,
        // but do keep the header counts right
        if (isInternalCancel(e) == false) {
            AtomicArray<ShardSearchFailure> shardFailures = this.shardFailures.get();
            // lazily create shard failures, so we can early build the empty shard failure list in most cases (no failures)
            if (shardFailures == null) { // this is double checked locking but it's fine since SetOnce uses a volatile read internally
                synchronized (this.shardFailures) {
                    shardFailures = this.shardFailures.get(); // read again otherwise somebody else has created it?
                    if (shardFailures == null) { // still null so we are the first and create a new instance
                        shardFailures = new AtomicArray<>(getNumShards());
                        this.shardFailures.set(shardFailures);
                    }
                }
            }
            ShardSearchFailure failure = shardFailures.get(shardIndex);
            if (failure == null) {
                shardFailures.set(shardIndex, new ShardSearchFailure(e, shardTarget));
            } else {
                // the failure is already present, try and not override it with an exception that is less meaningless
                // for example, getting illegal shard state
                if (TransportActions.isReadOverrideException(e) && (e instanceof SearchContextMissingException == false)) {
                    shardFailures.set(shardIndex, new ShardSearchFailure(e, shardTarget));
                }
            }

            if (results.hasResult(shardIndex)) {
                assert failure == null : "shard failed before but shouldn't: " + failure;
                successfulOps.decrementAndGet(); // if this shard was successful before (initial phase) we have to adjust the counter
            }
        } else {
            internalCancelledShardCount.incrementAndGet();
        }
    }
```

## 동작 흐름

```text
 4-arg  onShardFailure(shardIndex, shard, shardIt, e)     L454
 L457  3-arg 를 먼저 불러 실패를 기록한다
 L458  nextShard = shardIt.nextOrNull()
 L459  lastShard = nextShard == null
 L460  retriable = TransportActions.isRetriableShardLevelException(e)
 |
 L462  마지막이 아니고 재시도 가능하면
 |     L464  performPhaseOnShard(shardIndex, shardIt, nextShard)   -> [05] 로 되돌아감
 |
 L465  아니면
       L466  부분 결과를 허용하지 않으면
             L467  처음 한 번만
             L469  검색 태스크를 취소한다
       L475  onShardGroupFailure(shardIndex, shard, e)
       L476  finishOneShard()                                       -> [07] 회계로

 3-arg  onShardFailure(shardIndex, shardTarget, e)         L506
 L507  샤드가 없어서 난 예외면 NoShardAvailable 로 감싼다
 L514  내부 취소가 아니면
       L517  shardFailures 배열을 처음이면 만든다 (이중 검사 락)
       L527  그 자리가 비었으면 넣는다
       L532  아니면 특정 조건일 때만 덮어쓴다
       L537  이미 성공한 결과가 있었으면 successfulOps 를 하나 줄인다
 L541  내부 취소면 internalCancelledShardCount 를 올린다
```

```text
 재시도가 카운터를 건드리지 않는다

 finishOneShard 는 L476 에서만 불린다. 재시도 갈래에는 없다

 그래서 샤드 하나는 복제본이 몇 개든
 성공하거나 마지막 복제본까지 소진할 때까지
 outstandingShards 를 내리지 않는다

 이것이 [07] 의 "0이 되면 페이즈 끝"이 성립하는 근거다
 재시도가 카운터를 건드리면 페이즈가 일찍 끝나 버린다
```

```text
 재시도는 첫 페이즈에만 있다

 4-arg 를 부르는 곳은 [05] 의 리스너와 배치 경로뿐이다

 두 번째 이후 페이즈들은 CountedCollector 를 통해
 3-arg 만 부른다 (CountedCollector L60)
 거기에는 shardIt 도 없고 finishOneShard 도 없다

 DfsQueryPhase 의 클래스 주석이 그것을 적어 두었다 (L38-40)
   샤드가 실패해도 다른 샤드에서 재시도하지 않는다
```

```text
 성공이 실패 기록을 지운다

 3-arg 가 shardFailures 배열에 실패를 적는데
 나중에 그 샤드가 재시도로 성공하면
 onShardResult L570 이 그 자리를 null 로 지운다

 그래서 최종 실패 목록에는
 "끝내 실패한 샤드"만 남는다
```

```text
 successfulOps 가 줄어들 수 있다

 L537-540  results.hasResult(shardIndex) 이면 감소시킨다

 앞 페이즈에서 성공했던 샤드가
 뒤 페이즈에서 실패하는 경우다
 fetch 단계에서 검색 컨텍스트가 사라졌을 때가 그렇다
```

## 결과가 쓰이는 곳

```text
 재시도
      --> performPhaseOnShard 로 되돌아가므로
          노드당 제한 관문을 다시 지난다
      --> shardIndex 는 그대로라 결과 자리가 바뀌지 않는다

 shardFailures
      --> buildShardFailures 가 이것을 모아 (L441)
          executeNextPhase 의 실패 판정에 쓴다
      --> 응답의 _shards.failures 가 이 배열이다

 internalCancelledShardCount
      --> executeNextPhase L371 이 results.getNumShards() 와 비교한다
      --> 전부 내부 취소면 다른 실패 메시지를 낸다

 검색 태스크 취소
      --> 부분 결과를 허용하지 않는 요청에서만
      --> 한 번만 보낸다. 나머지 샤드의 작업을 멈추기 위해서다
```

## 다루지 않는 것

`TransportActions.isRetriableShardLevelException` 의 판정 규칙, `SearchShardIterator` 가 복제본을 내놓는 순서, `onShardGroupFailure` 의 오버라이드(진행 상황 알림), `CountedCollector` 가 뒤 페이즈의 실패를 세는 방식, 검색 태스크 취소가 샤드에 전파되는 경로는 같은 뼈대의 곁가지라 요약만 했다.
