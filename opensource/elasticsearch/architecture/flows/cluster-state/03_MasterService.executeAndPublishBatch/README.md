# MasterService.executeAndPublishBatch

상위: [클러스터 상태 갱신](../README.md)

배치 하나가 실행되고 **발행할지 말지가 갈리는 자리**다. 가르는 기준이 참조 비교 한 줄인데, 그 한 줄에 실행기의 정상 반환과 예외가 **같이** 걸린다.

## 위치

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L335-L437 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L335-L437))

## 실제 코드

멈춰 있으면 아무것도 안 한다.

```java
// MasterService.java L341-L345
        if (lifecycle.started() == false) {
            logger.debug("processing [{}]: ignoring, master service not started", summary);
            listener.onResponse(null);
            return;
        }
```

마스터가 아니면 태스크를 실패시킨다.

```java
// MasterService.java L350-L358
        if (previousClusterState.nodes().isLocalNodeElectedMaster() == false && executor.runOnlyOnMaster()) {
            logger.debug("failing [{}]: local node is no longer master", summary);
            for (ExecutionResult<T> executionResult : executionResults) {
                executionResult.onBatchFailure(new NotMasterException("no longer master"));
                executionResult.notifyFailure();
            }
            listener.onResponse(null);
            return;
        }
```

실행하고 버전을 붙인다.

```java
// MasterService.java L360-L366
        final long computationStartTime = threadPool.rawRelativeTimeInMillis();
        final var newClusterState = patchVersions(
            previousClusterState,
            executeTasks(previousClusterState, executionResults, executor, summary, threadPool.getThreadContext())
        );
        final TimeValue computationTime = getTimeSince(computationStartTime);
        logExecutionTime(computationTime, "compute cluster state update", summary);
```

그리고 참조 비교로 갈린다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L368-L382 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L368-L382))

```java
// MasterService.java L370-L377
            for (final var executionResult : executionResults) {
                final var contextPreservingAckListener = executionResult.getContextPreservingAckListener();
                if (contextPreservingAckListener != null) {
                    // no need to wait for ack if nothing changed, the update can be counted as acknowledged
                    contextPreservingAckListener.onAckSuccess();
                }
                executionResult.onClusterStateUnchanged(newClusterState);
            }
```

> no need to wait for ack if nothing changed, the update can be counted as acknowledged

## 동작 흐름

```text
 L341  lifecycle 이 안 떴으면 => debug 로그 + listener.onResponse(null)
 L348  previousClusterState = state()
 L350  로컬이 마스터가 아니고 executor.runOnlyOnMaster() 면
 L353    각 태스크에 onBatchFailure(NotMasterException)
 L354    notifyFailure()          <- 여기서 바로 알린다
 L356    => listener.onResponse(null)
 L360  계산 시작 시각
 L363  executeTasks(...)          먼저 평가된다
 L361  patchVersions(previous, 그 결과)
 L365  계산 시간 로그

 L368  previousClusterState == newClusterState 인가
   예
     L370  태스크마다
     L372    ack 리스너가 있으면 onAckSuccess()
     L376    onClusterStateUnchanged(newClusterState)
     L378  통지 시간 로그
     L380  통계
     L381  => listener.onResponse(null)
   아니오
     L384  newTraceContext 로 감싼다
     L387  taskManager 에 발행 태스크를 등록한다
     L405  ActionListener.run(포장된 리스너, l -> publishClusterStateUpdate(..., l))
```

```text
 L361 과 L363 의 순서가 눈에 거슬린다

   patchVersions(previousClusterState, executeTasks(...))

 한 줄에 중첩돼 있어 줄번호가 거꾸로 보인다
 Java 는 인자를 먼저 평가하므로 executeTasks(L363)가 먼저 돌고
 그 결과가 patchVersions(L361)에 들어간다
```

```text
 L368 의 == 에 두 가지가 같이 걸린다

 (가) 실행기가 받은 상태를 그대로 돌려준 경우 - 정상적인 "할 일 없음"

 (나) 실행기가 예외를 던진 경우
      innerExecuteTasks 의 catch 가 모든 태스크에 onBatchFailure 를 하고
      previousClusterState 를 그대로 돌려준다 (L1272)
      그러면 patchVersions 도 아무것도 안 하고 (L652)
      여기 == 가 참이 된다

 즉 **실행기 예외는 "상태가 안 바뀐 것"으로 취급되어 통지된다**
 L376 의 onClusterStateUnchanged 가 소비자 없는 태스크를 보고
 notifyFailure 로 넘기기 때문이다 (L1128-1130)

 (주석은 없다. L1272 의 반환값과 L652, L368 을 이어 보고 내가 판단한 것이다)
```

```text
 L374 의 "즉시 ack" 에 조건이 있다

 L371  contextPreservingAckListener = executionResult.getContextPreservingAckListener()
 L372  null 이 아니면 onAckSuccess()

 그 메서드는 두 경우에 null 을 준다 (L1182)
   실행기가 ack 리스너를 등록하지 않았거나
   그 태스크가 실패했거나

 그래서 "안 바뀌었으니 ack 성공" 은 **성공했고 ack 를 듣는 태스크**에만 해당한다
```

```text
 L350 갈래만 그 자리에서 알린다

 L353  onBatchFailure(...)   기록만 한다
 L354  notifyFailure()       실제로 task.onFailure 를 부른다

 다른 경로는 전부 발행이 끝난 뒤 한 쓸기에서 알린다
 여기만 예외다

 (주석은 없다. onBatchFailure 와 notifyFailure 의 호출 위치를 비교해
  내가 판단한 것이다)
```

```text
 L341 갈래는 아무에게도 안 알린다

 debug 로그 한 줄과 listener.onResponse(null) 뿐이다

 그런데 여기 도달했다는 것은 이미 배치를 꺼냈다는 뜻이고
 그 말은 acquireForExecution 이 taskHolder 를 비웠고
 타임아웃 스케줄도 취소됐다는 뜻이다

 즉 이 갈래에 걸린 태스크는 영원히 통지받지 못한다
 (spi 에 이런 갈래 여섯을 모았다)
```

## 결과가 쓰이는 곳

```text
 newClusterState
      --> 바뀌었으면 publishClusterStateUpdate 로 간다
      --> 안 바뀌었으면 버려진다. previousClusterState 와 같은 객체다

 listener.onResponse(null)
      --> Processor.run 의 runBefore 를 거쳐 (L1985)
      --> queuesProcessor 의 완료 리스너로 가고 (L1489)
      --> onCompletion 이 다음 배치를 건다 (L1524)

 taskManager 등록
      --> _tasks API 에 "publication of cluster state [버전]" 으로 보인다
      --> runAfter 로 반드시 해제된다 (L407)
```

## 다루지 않는 것

`taskManager` 의 태스크 등록과 `_tasks` API, `newTraceContext` 가 만드는 추적 문맥, `ClusterStateUpdateStatsTracker` 가 모으는 지표, `BatchSummary` 의 지연 문자열 생성과 8KiB 절단, `state()`(L317)가 상태를 가져오는 경로는 같은 뼈대의 곁가지라 요약만 했다. 실행기 호출은 [innerExecuteTasks](../04_MasterService.innerExecuteTasks/README.md), 발행은 [publishClusterStateUpdate](../05_MasterService.publishClusterStateUpdate/README.md)에 있다.
