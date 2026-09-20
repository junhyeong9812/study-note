# onShardResult / finishOneShard / onPhaseDone

상위: [검색 페이즈](../README.md)

샤드를 **세어서 페이즈가 끝났는지 판정한다**. 성공도 실패도 같은 카운터로 모이고, 0이 되는 순간 다음 페이즈로 넘어간다. 이름이 같은 `onPhaseDone` 이 다른 클래스에도 둘 더 있는데 서로 무관하다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L558-L578 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L558-L578))

## 실제 코드

결과를 받아 제자리에 넣는다.

```java
// AbstractSearchAsyncAction.java L558-L578
    protected void onShardResult(Result result) {
        assert result.getShardIndex() != -1 : "shard index is not set";
        assert result.getSearchShardTarget() != null : "search shard target must not be null";
        hasShardResponse.set(true);
        if (logger.isTraceEnabled()) {
            logger.trace("got first-phase result from {}", result != null ? result.getSearchShardTarget() : null);
        }
        // clean a previous error on this shard group (note, this code will be serialized on the same shardIndex value level
        // so it's ok concurrency wise to miss potentially the shard failures being created because of another failure
        // in the #addShardFailure, because by definition, it will happen on *another* shardIndex
        AtomicArray<ShardSearchFailure> shardFailures = this.shardFailures.get();
        if (shardFailures != null) {
            shardFailures.set(result.getShardIndex(), null);
        }
        // accumulate the per-shard metrics into the single merged reference before consuming the result
        accumulateDirectoryMetrics(result.getDirectoryMetrics());
        results.consumeResult(result, () -> {
            successfulOps.incrementAndGet();
            finishOneShard();
        });
    }
```

세고, 0이면 페이즈를 끝낸다.

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L480-L486 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L480-L486))

```java
// AbstractSearchAsyncAction.java L480-L486
    private void finishOneShard() {
        final int outstanding = outstandingShards.decrementAndGet();
        assert outstanding >= 0 : "outstanding: " + outstanding;
        if (outstanding == 0) {
            onPhaseDone();
        }
    }
```

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L864-L867 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L864-L867))

```java
// AbstractSearchAsyncAction.java L864-L867
    private void onPhaseDone() {  // as a tribute to @kimchy aka. finishHim()
        searchResponseMetrics.recordSearchPhaseDuration(getName(), System.nanoTime() - phaseStartTimeInNanos, searchRequestAttributes);
        executeNextPhase(getName(), this::getNextPhase);
    }
```

## 동작 흐름

```text
 onShardResult                                            L558
 L561  hasShardResponse.set(true)
 L568  이전에 이 샤드의 실패가 적혀 있으면
       L570  지운다. 재시도로 성공했다는 뜻이다
 L573  accumulateDirectoryMetrics
 L574  results.consumeResult(result, 콜백)
         콜백 L575  successfulOps 증가
              L576  finishOneShard()

 finishOneShard                                           L480
 L481  outstanding = outstandingShards.decrementAndGet()
 L483  0이면 onPhaseDone()

 onPhaseDone                                              L864
 L865  페이즈 소요시간 기록
 L866  executeNextPhase(getName(), this::getNextPhase)    -> [08]
```

```text
 콜백이 항상 즉시 불리는 것은 아니다

 results 의 실체가 무엇이냐에 달렸다
   ArraySearchPhaseResults        L48  next.run() 즉시
   CountOnlyQueryPhaseResultConsumer   즉시
   QueryPhaseResultConsumer       조건부

 마지막 것은 버퍼가 차면 (L568 size >= batchReduceSize)
 병합 작업을 큐에 넣고 executor 로 넘긴다
 그러면 successfulOps 증가와 finishOneShard 가
 리듀스 스레드에서 나중에 돈다

 즉 페이즈 종료가 검색 스레드가 아닌 곳에서 일어날 수 있다
```

```text
 finishOneShard 로 오는 길이 둘이다

 L576  성공
 L476  종국 실패 (재시도까지 소진한 경우)

 재시도 중에는 안 불린다
 그래서 샤드 하나가 카운터를 내리는 것은 정확히 한 번이다

 이 불변식이 깨지면 페이즈가 일찍 끝나거나 영영 안 끝난다
```

```text
 onPhaseDone 이 불리는 곳도 둘이다

 L484  카운터가 0이 됐을 때
 L254  run 시작 시점에 이미 0이었을 때

 둘 다 첫 페이즈에서만이다
 private 이고 호출처가 이 둘뿐이기 때문이다

 두 번째 페이즈부터는 각자 executeNextPhase 를 직접 부른다
```

```text
 이름이 같은 다른 메서드가 둘 더 있다

 ExpandSearchPhase L186   private void onPhaseDone()
 RankFeaturePhase  L189   private void onPhaseDone(...)

 셋 다 private 이고 서로 상속 관계도 아니다
 우연히 이름이 같을 뿐이다

 하는 일은 비슷하다 — 자기 페이즈를 끝내고 다음으로 넘긴다
 다만 이쪽은 executeNextPhase 를 직접 부른다
```

## 결과가 쓰이는 곳

```text
 outstandingShards
      --> 페이즈 종료의 유일한 기준이다
      --> 초기값은 shardsIts.size() (L156)
      --> 되살아나지 않는다. 페이즈가 바뀌어도 리셋이 없다

 successfulOps
      --> executeNextPhase 가 이것과 전체 샤드 수를 비교해
          부분 실패를 판정한다 (L359)
      --> skippedCount 로 시작한다 (L157)

 지워진 실패 기록
      --> 재시도로 성공한 샤드는 최종 실패 목록에서 빠진다
      --> 그래서 응답의 _shards.failed 가 실제 실패 수다

 phaseStartTimeInNanos
      --> 페이즈마다 소요시간이 따로 기록된다
      --> 메트릭에서 어느 단계가 느린지 보인다
```

## 다루지 않는 것

`SearchPhaseResults` 구현들(`QueryPhaseResultConsumer` 의 부분 리듀스와 회로 차단기, `ArraySearchPhaseResults`), `accumulateDirectoryMetrics` 와 저장소 메트릭, `getNextPhase` 구현들(전이 규칙은 [spi](../spi/README.md)에 있다), 다른 클래스의 동명 `onPhaseDone` 내부는 같은 뼈대의 곁가지라 요약만 했다.
