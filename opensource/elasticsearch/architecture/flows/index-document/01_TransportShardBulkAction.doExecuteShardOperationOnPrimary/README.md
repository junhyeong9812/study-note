# TransportShardBulkAction.doExecuteShardOperationOnPrimary

상위: [문서 색인](../README.md)

**배치로 한꺼번에 색인할지, 한 건씩 돌릴지**를 가르는 자리다. 그 전에 메모리 예약과 리스너 래핑을 해 둔다. 예약이 거절되면 여기서 요청 전체가 끝난다.

## 위치

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L194-L266 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L194-L266))

## 실제 코드

메모리를 예약하고 리스너를 감싼다. 이 블록에서 던지면 회수할 곳이 L174 catch 하나뿐이다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L204-L226 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L204-L226))

```java
// TransportShardBulkAction.java L204-L226
        var pressureExpansionTracker = indexingPressure.trackPrimaryOperationExpansion(
            primaryOperationCount(request),
            getMaxOperationMemoryOverhead(request),
            force(request)
        );
        final var mappingLookup = primary.mapperService().mappingLookup();
        // Pre-resolution prefetches stored fields; skip it when source is rebuilt from doc values instead
        final PreResolvedUpdates preResolvedUpdates = preResolveBulkUpdates
            && mappingLookup.isSourceSynthetic() == false
            && mappingLookup.isSourceColumnarStored() == false
                ? PreResolvedUpdates.resolve(request, primary, updateHelper, threadPool::absoluteTimeInMillis, UPDATE_FETCH_SOURCE_CONTEXT)
                : PreResolvedUpdates.EMPTY;
        var listener = ActionListener.releaseBefore(
            preResolvedUpdates,
            ActionListener.releaseBefore(pressureExpansionTracker, outerListener)
        );
        final BulkPrimaryExecutionContext context = new BulkPrimaryExecutionContext(
            request,
            primary,
            pressureExpansionTracker,
            preResolvedUpdates
        );
        long startBatchTime = System.nanoTime();
```

배치와 순차를 가른다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L227-L265 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L227-L265))

```java
// TransportShardBulkAction.java L227-L265
        if (shardBatchIndexer.canUseBatchIndexing(request)) {
            shardBatchIndexer.performBatchIndexOnPrimary(
                request.items(),
                request.getBulkShardBatch().getBatch(),
                context,
                listener.delegateFailure((delegate, ctx) -> {
                    if (context.hasMoreOperationsToExecute() == false) {
                        primary.getBulkOperationListener().afterBulk(request.totalSizeInBytes(), System.nanoTime() - startBatchTime);
                        delegate.onResponse(
                            new WritePrimaryResult<>(
                                request,
                                context.buildShardResponse(),
                                context.getLocationToSync(),
                                primary,
                                logger,
                                postWriteRefresh
                            )
                        );
                    } else {
                        // Fall through to serial path for remaining items. Inline sources.
                        try {
                            BulkShardBatch.ensureInlineSources(request);
                        } catch (IOException e) {
                            delegate.onFailure(e);
                            return;
                        }
                        performSequentialOnPrimary(request, delegate, context, startBatchTime);
                    }
                })
            );
        } else {
            try {
                BulkShardBatch.ensureInlineSources(request);
            } catch (IOException e) {
                listener.onFailure(e);
                return;
            }
            performSequentialOnPrimary(request, listener, context, startBatchTime);
        }
```

## 동작 흐름

```text
 L199  assert 현재 스레드가 WRITE 계열인지
         WRITE, SYSTEM_WRITE, SYSTEM_CRITICAL_WRITE

 L204  indexingPressure.trackPrimaryOperationExpansion(...)
         메모리 한계를 넘으면 EsRejectedExecutionException
         (IndexingPressure L420-444)
       => 위로 던져져 L174 catch 가 요청 전체를 실패시킨다

 L211  preResolveBulkUpdates 설정이 켜져 있고
       매핑이 synthetic source 가 아니고
       columnar stored 도 아니면
         PreResolvedUpdates.resolve(...)   update 를 미리 풀어 둔다
       아니면 EMPTY

 L216  listener 를 두 겹으로 감싼다
         releaseBefore(preResolvedUpdates, releaseBefore(pressureExpansionTracker, outerListener))
         완료 직전에 둘 다 놓는다

 L220  new BulkPrimaryExecutionContext(request, primary, 트래커, 미리푼것)

 L227  shardBatchIndexer.canUseBatchIndexing(request)
       |
       +-- true
       |     L228  performBatchIndexOnPrimary(...)   동기다
       |           +-- L233  남은 항목이 없으면
       |           |     L234  afterBulk
       |           |     L235  => WritePrimaryResult 로 응답
       |           +-- 남았으면
       |                 L248  ensureInlineSources   IOException => onFailure L250
       |                 L253  performSequentialOnPrimary
       |
       +-- false
             L259  ensureInlineSources   IOException => onFailure L261
             L264  performSequentialOnPrimary
```

```text
 배치가 되는 조건은 셋이다 (ShardBatchIndexer L62-70)

 배치 인덱싱 설정이 켜져 있다
 요청에 배치가 실려 있다
 모든 항목이 INDEX 나 CREATE 다

 마지막 조건 때문에 delete 나 update 가 하나라도 섞이면
 그 bulk 전체가 순차 경로로 간다
```

```text
 배치가 일부만 하고 나머지를 남기는 이유

 ShardBatchIndexer 의 조기 return 세 자리다
   L100-106  abort 된 항목이 하나라도 있다. 아예 시작도 안 한다
   L116-118  매퍼를 못 고른다
   L134-136  5000개 청크 경계에서 다음 청크를 못 만든다

 세 번째만 부분 처리다. 앞의 둘은 한 건도 안 하고 넘긴다

 어느 쪽이든 같은 context 를 순차 경로가 이어받는다
 어디까지 했는지는 context 의 currentIndex 가 안다
```

```text
 배치 실패와 순차 실패는 의미가 다르다

 순차  항목 하나가 실패해도 그 항목만 실패로 기록하고 계속 간다
 배치  예외가 나면 L232 델리게이트가 바깥 리스너로 직행한다
       샤드 요청 전체가 실패한다. 순차로 폴백하지 않는다
```

## 결과가 쓰이는 곳

```text
 BulkPrimaryExecutionContext
      --> 이 흐름 전체가 이 객체 하나를 돌려 쓴다
      --> 배치 경로와 순차 경로가 같은 것을 이어받는다
      --> 항목별 상태와 translog 위치를 모은다

 두 겹 리스너
      --> 완료 직전에 미리 푼 update 와 메모리 예약을 놓는다
      --> 성공이든 실패든 양쪽에서 돈다

 startBatchTime
      --> afterBulk 통계의 기준이다
      --> 배치 종료(L234)와 순차 종료(L415) 양쪽에서 쓴다
```

## 다루지 않는 것

`ShardBatchIndexer` 의 색인 내부(`applyIndexOperationBatchOnPrimary` 이후), `PreResolvedUpdates` 가 update 를 미리 푸는 방식, `IndexingPressure` 의 한계 계산과 설정, `ensureInlineSources` 가 하는 일, `executor(primary)` 가 스레드풀을 고르는 규칙은 같은 뼈대의 곁가지라 요약만 했다.
