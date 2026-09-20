# AbstractSearchAsyncAction.executeNextPhase

상위: [검색 페이즈](../README.md)

**다음 페이즈로 넘길지, 여기서 실패로 끝낼지** 정한다. 체인의 모든 전이가 이 메서드를 지나고, 들어오는 입구가 다섯이다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L343-L428 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L343-L428))

## 실제 코드

실패 판정이 먼저다.

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L350-L355 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L350-L355))

```java
// AbstractSearchAsyncAction.java L350-L355
            shardSearchFailures = ExceptionsHelper.groupBy(shardSearchFailures);
            Throwable cause = shardSearchFailures.length == 0
                ? null
                : ElasticsearchException.guessRootCauses(shardSearchFailures[0].getCause())[0];
            logger.debug(() -> "All shards failed for phase: [" + currentPhase + "]", cause);
            onPhaseFailure(currentPhase, "all shards failed", cause);
```

부분 실패는 세 갈래로 더 갈린다.

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L359-L397 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L359-L397))

```java
// AbstractSearchAsyncAction.java L359-L397
            if (allowPartialResults == false && successfulOps.get() != getNumShards()) {
                // check if there are actual failures in the atomic array since
                // successful retries can reset the failures to null
                if (shardSearchFailures.length > 0) {
                    if (logger.isDebugEnabled()) {
                        int numShardFailures = shardSearchFailures.length;
                        shardSearchFailures = ExceptionsHelper.groupBy(shardSearchFailures);
                        Throwable cause = ElasticsearchException.guessRootCauses(shardSearchFailures[0].getCause())[0];
                        logger.debug(() -> format("%s shards failed for phase: [%s]", numShardFailures, currentPhase), cause);
                    }
                    onPhaseFailure(currentPhase, "Partial shards failure", null);
                } else {
                    if (internalCancelledShardCount.get() == results.getNumShards()) {
                        // All shards encountered internal TaskCancelledException, which is not included in shard failures. To prevent a
                        // spurious SERVICE_UNAVAILABLE response due to no shard failures being present, provide a placeholder cause to
                        // onPhaseFailure() which can be filtered out later
                        onPhaseFailure(
                            currentPhase,
                            ALL_SHARDS_FAILED_DUE_TO_INTERNAL_CANCEL,
                            new ElasticsearchException(ALL_SHARDS_FAILED_DUE_TO_INTERNAL_CANCEL)
                        );
                        return;
                    }
                    int discrepancy = getNumShards() - successfulOps.get();
                    assert discrepancy > 0 : "discrepancy: " + discrepancy;
                    if (logger.isDebugEnabled()) {
                        logger.debug(
                            "Partial shards failure (unavailable: {}, successful: {}, skipped: {}, num-shards: {}, phase: {})",
                            discrepancy,
                            successfulOps.get(),
                            skippedCount,
                            getNumShards(),
                            currentPhase
                        );
                    }
                    onPhaseFailure(currentPhase, "Partial shards failure (" + discrepancy + " shards unavailable)", null);
                }
                return;
            }
```

통과하면 다음 페이즈를 만들어 넘긴다.

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L398-L426 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L398-L426))

```java
// AbstractSearchAsyncAction.java L398-L426
            long resultBytes = phaseResultBytesRead.sumThenReset();
            long requestBytes = phaseRequestBytesWritten.sumThenReset();
            // bytes tracked is 0 in the following scenarios:
            // - all requests/responses were local
            // - for the expand phase whose sub-searches are tracked separately
            // - for the result side if all shards failed, which is the only case where remote requests track bytes but results don't
            if (resultBytes > 0) {
                assert requestBytes > 0 : "successful responses from remote nodes must have corresponding request bytes set";
                searchResponseMetrics.recordSearchPhaseShardResultBytes(currentPhase, resultBytes, searchRequestAttributes);
            }
            if (requestBytes > 0) {
                searchResponseMetrics.recordSearchPhaseShardRequestBytes(currentPhase, requestBytes, searchRequestAttributes);
            }
            assert currentPhase.equals(ExpandSearchPhase.NAME) == false || (requestBytes == 0 && resultBytes == 0)
                : "bytes should not be tracked for the expand phase, whose sub-searches are tracked individually";
            var nextPhase = nextPhaseSupplier.get();
            if (logger.isTraceEnabled()) {
                final String resultsFrom = results.getSuccessfulResults()
                    .map(r -> r.getSearchShardTarget().toString())
                    .collect(Collectors.joining(","));
                logger.trace(
                    "[{}] Moving to next phase: [{}], based on results from: {} (cluster state version: {})",
                    currentPhase,
                    nextPhase.getName(),
                    resultsFrom,
                    clusterStateVersion
                );
            }
            executePhase(nextPhase);
```

## 동작 흐름

```text
 L348  shardSearchFailures = buildShardFailures()

 L349  실패 수 == 전체 샤드 수
       => onPhaseFailure("all shards failed")              L355

 L356  아니면
       L359  부분 결과를 허용하지 않는데 성공 수가 모자라면
             L362  실패 기록이 있으면
                   => onPhaseFailure("Partial shards failure")      L369
             L370  없으면
                   L371  전부 내부 취소였으면
                         => onPhaseFailure(...)                     L375
                   L382  아니면 모자란 수를 세어
                         => onPhaseFailure("... shards unavailable") L394
             L396  return

       L398  바이트 메트릭을 기록하고 리셋한다
       L413  nextPhase = nextPhaseSupplier.get()
       L426  executePhase(nextPhase)
```

```text
 들어오는 입구가 다섯이다

 ASAA.onPhaseDone      L866   1회차만
 DfsQueryPhase         L135
 RankFeaturePhase      L278
 FetchSearchPhase      L278
 ExpandSearchPhase     L187

 첫 넷은 서플라이어가 다 다르다
   1회차는 this::getNextPhase
   나머지는 각 페이즈가 넘기는 람다

 그래서 "다음 페이즈를 누가 정하는가"가 페이즈마다 다르다
```

```text
 서플라이어가 이 try 밖이다

 L413 의 nextPhaseSupplier.get() 은 executePhase 의 try 안이 아니다
 executePhase 는 L426 에서야 불린다

 FetchSearchPhase 의 서플라이어는 안에서 결과 병합을 한다 (L279)
 거기서 예외가 나면 executePhase 의 catch 가 못 받는다
 이 메서드를 부른 쪽으로 올라간다
```

```text
 실패 판정의 순서가 의미를 갖는다

 1. 전부 실패했나            L349
 2. 부분 실패를 허용하나      L359
    2a. 실패 기록이 있나      L362
    2b. 전부 내부 취소인가    L371
    2c. 그 외 (샤드를 못 구함) L382

 2b 가 2a 의 else 안에 있다
 내부 취소는 실패 기록에 안 들어가기 때문이다
 그래서 "실패는 없는데 성공도 모자란" 상황이 되고
 주석이 그 사정을 적어 두었다 (L372-374)
```

```text
 L371 이 getNumShards() 가 아니다

 L371  internalCancelledShardCount.get() == results.getNumShards()

 getNumShards() 는 results.getNumShards() + skippedCount 다 (L613)
 여기서는 skipped 를 뺀 쪽과 비교한다

 can_match 로 걸러진 샤드는 취소될 일이 없으므로
 분모에서 빼는 것이 맞다
```

```text
 바이트 메트릭이 페이즈마다 리셋된다

 L398  sumThenReset()

 그래서 각 페이즈가 주고받은 바이트가 따로 기록된다
 누적이 아니다

 expand 페이즈는 하위 검색을 따로 세므로
 여기서는 0이어야 한다고 assert 가 확인한다 (L411)
```

## 결과가 쓰이는 곳

```text
 다음 페이즈 객체
      --> 매번 새로 만들어진다. 같은 객체가 다시 오지 않는다
      --> 그래서 체인이고 사이클이 아니다

 executePhase(nextPhase)
      --> 중첩 호출이라 스택이 쌓인다
      --> 다만 fetch 와 rank-feature 는 run 첫 줄에서 포크해 스택을 푼다

 onPhaseFailure
      --> 네 갈래 중 하나로 체인이 끊긴다
      --> 하지만 종료 지점이 이 넷만은 아니다
          각 페이즈가 직접 부르는 곳이 아홉 군데 더 있다

 페이즈 소요시간과 바이트
      --> 어느 단계가 느리고 무거운지 나눠서 보인다
```

## 다루지 않는 것

`buildShardFailures` 와 실패 배열 조립, `ExceptionsHelper.groupBy` 와 원인 추정, `onPhaseFailure` / `raisePhaseFailure` 의 응답 조립, 각 페이즈가 넘기는 서플라이어의 내용(전이 규칙은 [spi](../spi/README.md)에 있다), 검색 메트릭 항목은 같은 뼈대의 곁가지라 요약만 했다.
