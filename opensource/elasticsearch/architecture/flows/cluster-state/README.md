# 클러스터 상태 갱신

마스터가 상태를 바꾸는 유일한 길이다. 태스크를 제출한 순간부터 새 상태가 모든 노드에 발행되고 제출자가 통지받기까지.

지금까지의 흐름들과 결이 다르다. **한 스레드가 처음부터 끝까지 도는 게 아니라, 큐와 콜백으로 네 번 끊긴다.** 그리고 그 스레드는 하나뿐이라 모든 상태 갱신이 여기서 줄을 선다. 폴더 하나가 메서드 하나이고, [spi](spi/README.md)에 실행기 계약과 우선순위표가 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 줄 번호는 별도 표기가 없으면 `MasterService.java` 기준이다.

## 전체 그림

```text
 [01] BatchingTaskQueue.submitTask                    L1873
      +-- 타임아웃이 있으면 스케줄한다                  L1880
      |     ~~> 시간이 되면 generic 스레드에서 돈다
      +-- queue.add(entry)                             L1903
      +-- queueSize 가 0 -> 1 이면 Processor 를 넣는다  L1905
            +-- PerPriorityQueue.execute                L1634
                  totalQueueSize 가 0 -> 1 이면
                  ~~> forkQueueProcessor -> threadPoolExecutor  L1580

 [02] queuesProcessor.doRun                           L1482   마스터 스레드
      +-- takeNextBatch()                              L1505
      +-- nextBatch.run(batchCompletionListener)        L1509
            +-- Processor.run                           L1962
                  +-- 큐를 통째로 비워 태스크를 모은다  L1964-1979
                  +-- batchConsumer.runBatch(...)       L1988

 [03] executeAndPublishBatch                          L335
      +-- [04] executeTasks -> innerExecuteTasks        L363
      +-- patchVersions                                 L361
      +-- previousClusterState == newClusterState 인가  L368
            예   => 발행 없이 통지하고 끝              L370-381
            아니오 -> [05]

 [05] publishClusterStateUpdate                       L439
      ~~> initializeAsync(generic)                      L483   합류하지 않는다
      +-- publish                                       L484 -> L618
            ~~> clusterStatePublisher.publish            L623
                완료는 ThreadedActionListener 로 마스터 스레드에 돌아온다  L629

      완료 후
      +-- [06] ExecutionResult 들에 통지                 L505
      +-- executor.clusterStatePublished                L509
      +-- listener.onResponse(null)                     L599
            -> onCompletion(L1524)이 다음 배치를 건다
```

```text
 끊기는 자리가 넷이다

 1. L1580  큐 처리기를 마스터 스레드에 건다
 2. L1880  타임아웃 핸들러를 generic 스레드에 건다
 3. L483   라우팅 노드 초기화를 generic 스레드에 건다 (합류 없음)
 4. L629   발행 완료를 마스터 스레드로 되돌린다

 그 사이는 전부 동기다
 ActionListener.run / runAfter / runBefore / delegateResponse 는
 스레드를 바꾸지 않는다
```

```text
 마스터 스레드는 하나다

 createThreadPoolExecutor L285-296
   EsExecutors.newScaling(이름, 0, 1, 60, SECONDS, ...)

 core 0, max 1 이다
 즉 "동시에 최대 하나"이지 상주 스레드가 아니다
 60초 놀면 사라지고 다음에 새로 만들어진다

 이름은 MASTER_UPDATE_THREAD_NAME = "masterService#updateTask" (L108)
```

```text
 배칭이 두 겹이다

 겹 1  큐 하나 안에서 태스크를 모은다
       submitTask 가 queueSize 0 -> 1 일 때만 Processor 를 넣는다   L1905
       그래서 큐당 Processor 가 대기열에 하나뿐이다
       Processor.run 이 그 순간 쌓인 것을 통째로 가져간다           L1964

 겹 2  우선순위별 큐에서 배치를 하나씩 꺼낸다
       PerPriorityQueue.execute 가 totalQueueSize 0 -> 1 일 때만
       처리기를 포크한다                                            L1637
       onCompletion 이 남은 게 있을 때만 자기를 다시 건다           L1526

 두 겹 다 "0에서 1로 갈 때만" 다음 단계를 건다
 그래서 처리기가 둘 도는 일이 없다
```

```text
 이 흐름이 앞 흐름들과 만나는 자리 셋

 L368   previousClusterState == newClusterState
        [샤드 시작 반영]의 javadoc 이 말한 "같은 인스턴스면 변경 없음"
        계약을 여기서 소비한다

 L1246  versionNumbersPreserved 검사
        실행기가 버전을 건드렸으면 예외를 던진다
        앞 흐름에서 "버전은 발행 단계에서 붙는다" 고 한 것의 강제 장치다

 L509   executor.clusterStatePublished(newClusterState)
        [샤드 시작 반영]이 후속 reroute 를 거는 자리다
```

## 어디에서 쓰이는가

```text
 [샤드 시작 반영] 그 실행기가 이 큐에서 돈다
      --> 결과가 여기서 발행되고 clusterStatePublished 로 되돌아간다

 [매핑 병합] 마스터 쪽 병합도 이 경로로 상태에 실린다

 [구조: 노드 역할] 노드 합류·이탈도 상태 갱신 태스크다
```

시작된 샤드를 상태에 반영하는 쪽은 [샤드 시작 반영](../shard-allocation/README.md)에 있다.

## 단계

1. [submitTask](01_BatchingTaskQueue.submitTask/README.md)가 태스크를 큐에 넣고 타임아웃을 건다.
2. [queuesProcessor](02_MasterService.queuesProcessor/README.md)가 배치를 하나씩 꺼내 돌린다.
3. [executeAndPublishBatch](03_MasterService.executeAndPublishBatch/README.md)가 실행하고 발행 여부를 가른다.
4. [innerExecuteTasks](04_MasterService.innerExecuteTasks/README.md)가 실행기를 부르고 버전을 검사한다.
5. [publishClusterStateUpdate](05_MasterService.publishClusterStateUpdate/README.md)가 발행하고 결과를 받는다.
6. [ExecutionResult](06_MasterService.ExecutionResult/README.md)가 태스크 하나의 운명을 담는다.

## 결과가 쓰이는 곳

```text
 발행된 ClusterState
      --> 모든 노드가 받아 적용한다
      --> 이 노드도 ClusterApplierService 를 거쳐 적용한다

 태스크 통지
      --> 성공·실패 모두 발행이 끝난 뒤 한 쓸기에서 나간다
      --> 그 자리에서 알리는 것은 "마스터가 아님" 갈래뿐이다 (L353-354)
      --> 아무 소식도 못 받는 갈래가 여섯 있다 (spi 에 표로 모았다)

 ack
      --> 다른 노드가 상태를 적용했다고 알려 오면 ack 리스너가 받는다
      --> 상태가 안 바뀌었으면 즉시 성공 처리한다 (L374)

 다음 배치
      --> listener.onResponse 가 onCompletion 으로 이어지고
          남은 배치가 있으면 처리기를 다시 건다
```

## 다루지 않는 것

`Coordinator` 와 `PublicationTransportHandler` 가 실제로 상태를 다른 노드에 보내고 커밋을 모으는 과정, `ClusterApplierService` 가 받은 상태를 적용하는 경로, `ClusterStateAckListener` 와 `TaskAckListener` 가 ack 를 집계하는 방식, `StarvationWatcher` 와 `ClusterStateUpdateStatsTracker` 의 지표, `submitUnbatchedStateUpdateTask`(L700)의 예전 경로, 39개 실행기 각각의 사정은 같은 뼈대의 곁가지라 요약만 했다. 실행기 계약과 우선순위는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 submitTask](01_BatchingTaskQueue.submitTask/README.md)
- [02 queuesProcessor](02_MasterService.queuesProcessor/README.md)
- [03 executeAndPublishBatch](03_MasterService.executeAndPublishBatch/README.md)
- [04 innerExecuteTasks](04_MasterService.innerExecuteTasks/README.md)
- [05 publishClusterStateUpdate](05_MasterService.publishClusterStateUpdate/README.md)
- [06 ExecutionResult](06_MasterService.ExecutionResult/README.md)
- [spi](spi/README.md) — 실행기 계약과 우선순위
