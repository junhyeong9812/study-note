# TransportShardBulkAction.handleMappingUpdateRequired

상위: [문서 색인](../README.md)

문서에 **매핑에 없는 필드가 들어 있을 때** 부른다. 마스터에 매핑을 바꿔 달라고 요청하고, 바뀔 때까지 기다렸다가 그 항목을 다시 태운다. 이 흐름에서 `false` 를 돌려주는 유일한 자리이고, 그래서 [루프](../03_TransportShardBulkAction.performOnPrimary/README.md)가 여기서만 나갔다 온다.

## 위치

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L587-L638 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L587-L638))

## 실제 코드

바꿀 것이 없는 갱신이면 그냥 다시 태운다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L597-L609 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L597-L609))

```java
// TransportShardBulkAction.java L597-L609
        final var mapperService = primary.mapperService();
        final long initialMappingVersion = mapperService.mappingVersion();
        try {
            if (mapperService.isNoOpUpdate(result.getRequiredMappingUpdate())) {
                context.resetForNoopMappingUpdateRetry(mapperService.mappingVersion());
                return true;
            }
        } catch (Exception e) {
            logger.info(() -> format("%s mapping update rejected by primary", primary.shardId()), e);
            assert result.getId() != null;
            onComplete(exceptionToResult(e, primary, false, version, result.getId()), context, updateResult);
            return true;
        }
```

마스터에 요청하고 기다린다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L611-L637 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L611-L637))

```java
// TransportShardBulkAction.java L611-L637
        mappingUpdater.updateMappings(result.getRequiredMappingUpdate(), primary.shardId(), new ActionListener<>() {
            @Override
            public void onResponse(Void v) {
                context.markAsRequiringMappingUpdate();
                waitForMappingUpdate.accept(ActionListener.runAfter(new ActionListener<>() {
                    @Override
                    public void onResponse(Void v) {
                        assert context.requiresWaitingForMappingUpdate();
                        context.resetForMappingUpdateRetry();
                    }

                    @Override
                    public void onFailure(Exception e) {
                        context.failOnMappingUpdate(e);
                    }
                }, () -> itemDoneListener.onResponse(null)), initialMappingVersion);
            }

            @Override
            public void onFailure(Exception e) {
                onComplete(exceptionToResult(e, primary, false, version, result.getId()), context, updateResult);
                // Requesting mapping update failed, so we don't have to wait for a cluster state update
                assert context.isInitial();
                itemDoneListener.onResponse(null);
            }
        });
        return false;
```

## 동작 흐름

```text
 L597  mapperService 와 initialMappingVersion 을 잡아 둔다

 L600  isNoOpUpdate 인가 (바꿀 것이 없는 갱신인가)
       +-- 맞으면 L601  resetForNoopMappingUpdateRetry(mappingVersion)
       |          L602  return true    마스터에 안 간다. 그 자리에서 다시
       |
       +-- L604  catch (Exception e)
             L605  logger.info("mapping update rejected by primary")
             L607  onComplete(exceptionToResult(e, ...), context, updateResult)
             L608  return true         그 항목만 실패로 끝낸다

 L611  mappingUpdater.updateMappings(필요한 갱신, shardId, 리스너)
       |
       +-- ~~> onResponse                                  L613
       |     L614  markAsRequiringMappingUpdate()     TRANSLATED -> WAIT_FOR_MAPPING_UPDATE
       |     L615  waitForMappingUpdate.accept(리스너, initialMappingVersion)
       |           +-- onResponse  L617  resetForMappingUpdateRetry()
       |           +-- onFailure   L623  failOnMappingUpdate(e)
       |           +-- runAfter    L626  itemDoneListener.onResponse(null)
       |                                 성공이든 실패든 돈다
       |
       +-- ~~> onFailure                                   L630
             L631  onComplete(exceptionToResult(e, ...), ...)
             L633  assert context.isInitial()
             L634  itemDoneListener.onResponse(null)

 L637  return false      <- 루프가 여기서 빠져나간다
```

```text
 no-op 갱신에 무한 루프 가드가 있다

 resetForNoopMappingUpdateRetry 는 직전에 쓴 매핑 버전을 기억한다
 같은 버전으로 또 no-op 이 나오면 던진다
   BulkPrimaryExecutionContext L256-268
   "On retry, this indexing request resulted in another noop mapping update.
    Failing the indexing operation to prevent an infinite retry loop."

 주석이 원인 후보까지 적어 두었다 (L262-264)
   필드 수 한계를 넘는 동적 매퍼를 만들었는데
   병합에서 무시되어 같은 일이 반복되는 경우

 그 예외는 L599 try 안에서 나므로 L604 catch 가 받는다
 즉 요청 전체가 아니라 그 항목만 실패한다
```

```text
 실패가 재시도가 아니라 종결이다

 L623 failOnMappingUpdate 는 이름과 달리 기록만 하지 않는다
   BulkPrimaryExecutionContext L295-307
   EXECUTED 로 바꾸고 실패 응답을 만든 뒤
   스스로 markAsCompleted 를 불러 COMPLETED 로 넘기고 advance 한다

 그래서 매핑 대기가 타임아웃되거나 노드가 닫혀도
 그 항목만 실패로 끝나고 루프는 다음 항목으로 간다
```

```text
 itemDoneListener 가 루프를 다시 켠다

 실체는 performOnPrimary L395 다
   onMappingUpdateDone = ActionListener.wrap(v -> executor.execute(this), ...)

 L626 과 L634 에서 이것을 부르면
 같은 러너블이 WRITE executor 에 다시 들어가고
 doRun 이 새 스레드에서 처음부터 돈다

 L626 은 runAfter 라 성공 갈래와 실패 갈래 모두에서 돈다
 실패였다면 그 항목은 이미 완료된 뒤라 다음 항목부터 돈다
```

```text
 return false 가 여기 하나뿐이다

 executeBulkItemRequest 의 return 은
   L516 true, L522 true, L584 true
   L571 은 이 메서드의 반환값

 이 메서드의 return 은 L602 true, L608 true, L637 false

 그래서 루프의 "매핑 갱신 대기" 탈출은 L637 에서만 시작된다
```

## 결과가 쓰이는 곳

```text
 initialMappingVersion
      --> waitForMappingUpdate 의 술어가 이것과 비교한다
      --> 매핑 버전이 이 값에서 달라져야 깨어난다
      --> 관계없는 클러스터 상태 변경으로는 안 깨어난다

 markAsRequiringMappingUpdate
      --> 항목 상태를 WAIT_FOR_MAPPING_UPDATE 로 바꾼다
      --> requestToExecute 를 비워 재번역을 강제한다

 마스터에 간 매핑 갱신
      --> 클러스터 상태가 바뀐다. 모든 노드에 전파된다
      --> 그래서 동적 매핑이 많은 색인은 마스터가 병목이 된다

 onComplete 로 가는 두 길 (L607, L631)
      --> 매핑을 못 바꾼 경우다
      --> update 항목이면 거기서 응답 변환까지 탄다
```

## 다루지 않는 것

`MappingUpdatedAction` 이 마스터에 보내는 경로와 세마포어, 마스터가 매핑을 병합하는 규칙과 필드 수 한계, `isNoOpUpdate` 의 판정, `ClusterStateObserver` 의 대기 구현, 동적 매퍼가 만들어지는 문서 파싱 단계는 같은 뼈대의 곁가지라 요약만 했다.
