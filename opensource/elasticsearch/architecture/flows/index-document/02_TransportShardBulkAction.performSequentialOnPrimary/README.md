# TransportShardBulkAction.performSequentialOnPrimary

상위: [문서 색인](../README.md)

하는 일은 **매핑 갱신을 어떻게 요청하고 어떻게 기다릴지 두 람다로 엮어** [performOnPrimary](../03_TransportShardBulkAction.performOnPrimary/README.md)에 넘기는 것뿐이다. 그 두 람다가 나중에 [handleMappingUpdateRequired](../05_TransportShardBulkAction.handleMappingUpdateRequired/README.md)에서 불린다.

## 위치

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L268-L305 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L268-L305))

## 실제 코드

```java
// TransportShardBulkAction.java L268-L305
    private void performSequentialOnPrimary(
        final BulkShardRequest request,
        final ActionListener<PrimaryResult<BulkShardRequest, BulkShardResponse>> listener,
        final BulkPrimaryExecutionContext batchContext,
        long startBatchTime
    ) {
        final IndexShard primary = batchContext.getPrimary();
        final ClusterStateObserver observer = new ClusterStateObserver(
            clusterService,
            request.timeout(),
            logger,
            threadPool.getThreadContext()
        );
        performOnPrimary(request, primary, updateHelper, threadPool::absoluteTimeInMillis, (update, shardId, mappingListener) -> {
            assert update != null;
            assert shardId != null;
            mappingUpdatedAction.updateMappingOnMaster(shardId.getIndex(), update, mappingListener);
        }, (mappingUpdateListener, initialMappingVersion) -> observer.waitForNextChange(new ClusterStateObserver.Listener() {
            @Override
            public void onNewClusterState(ClusterState state) {
                mappingUpdateListener.onResponse(null);
            }

            @Override
            public void onClusterServiceClose() {
                mappingUpdateListener.onFailure(new NodeClosedException(clusterService.localNode()));
            }

            @Override
            public void onTimeout(TimeValue timeout) {
                mappingUpdateListener.onFailure(new MapperException("timed out while waiting for a dynamic mapping update"));
            }
        }, clusterState -> {
            var index = primary.shardId().getIndex();
            var indexMetadata = clusterState.metadata().lookupProject(index).map(p -> p.index(index)).orElse(null);
            return indexMetadata == null || (indexMetadata.mapping() != null && indexMetadata.getMappingVersion() != initialMappingVersion);
        }), listener, executor(primary), postWriteRefresh, documentParsingProvider, batchContext, startBatchTime);
    }
```

## 동작 흐름

```text
 L275  new ClusterStateObserver(clusterService, request.timeout(), ...)
         요청 타임아웃을 그대로 쓴다

 L281  performOnPrimary(...) 에 넘기는 두 람다

 [람다 1] 매핑을 바꿔 달라고 요청한다              L281-284
   mappingUpdatedAction.updateMappingOnMaster(index, update, listener)
   마스터에 보내는 요청이다

 [람다 2] 바뀔 때까지 기다린다                     L285-303
   observer.waitForNextChange(리스너, 술어)
   |
   +-- 리스너 (세 갈래)
   |     L287  onNewClusterState     -> onResponse(null)
   |     L292  onClusterServiceClose -> onFailure(NodeClosedException)
   |     L297  onTimeout             -> onFailure(MapperException("timed out ..."))
   |
   +-- 술어                                          L300-303
         indexMetadata == null
         또는 매핑이 있고 mappingVersion 이 initialMappingVersion 과 다르다
```

```text
 기다린다고 해서 반드시 기다리는 것은 아니다

 ClusterStateObserver.waitForNextChange 는 세 갈래다 (L136-179)
   L138  이미 타임아웃이 지났으면 그 자리에서 onTimeout
   L164  지금 상태가 술어를 만족하면 그 자리에서 onNewClusterState
   L169  그 외에만 리스너를 등록하고 기다린다

 앞의 둘은 호출한 스레드에서 바로 콜백이 돈다
```

```text
 술어가 initialMappingVersion 을 쓴다

 "새 클러스터 상태가 오면 깨어난다"가 아니다
 매핑 버전이 처음 본 값과 달라져야 깨어난다 (L303)

 그 initialMappingVersion 은
 handleMappingUpdateRequired 가 L598 에서 읽어
 L626 에서 이 람다로 넘겨준다

 그래서 관계없는 클러스터 상태 변경으로는 깨어나지 않는다
```

```text
 왜 여기서 엮는가

 performOnPrimary 는 static 이라 clusterService 도 threadPool 도 모른다
 그것들이 필요한 부분만 여기서 람다로 싸서 넘긴다

 덕분에 performOnPrimary 는 테스트에서
 다른 람다를 끼워 넣어 부를 수 있다
```

## 결과가 쓰이는 곳

```text
 두 람다
      --> handleMappingUpdateRequired 가 각각 L611 과 L615 에서 부른다
      --> 앞엣것이 마스터를 바꾸고, 뒤엣것이 바뀐 것을 확인한다

 ClusterStateObserver
      --> 요청 하나에 하나다
      --> 항목마다 새로 만들지 않는다. 같은 것을 계속 쓴다

 타임아웃
      --> 요청의 timeout 이 매핑 대기 시간이 된다
      --> 넘으면 그 항목만 MapperException 으로 실패한다
```

## 다루지 않는 것

`MappingUpdatedAction` 이 마스터에 매핑 갱신을 보내는 내부(세마포어와 `TransportAutoPutMappingAction`), `ClusterStateObserver` 의 리스너 등록과 타임아웃 관리, 마스터가 매핑을 병합하는 경로, `postWriteRefresh` 와 `documentParsingProvider` 가 쓰이는 자리는 같은 뼈대의 곁가지라 요약만 했다.
