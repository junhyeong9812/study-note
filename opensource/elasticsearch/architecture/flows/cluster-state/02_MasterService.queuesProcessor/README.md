# MasterService.queuesProcessor

상위: [클러스터 상태 갱신](../README.md)

**한 번에 배치 하나만 돌리는 고리다.** 스스로를 다시 걸어서 큐가 빌 때까지 반복하고, 그 사이 다른 처리기가 끼어들 수 없다. 주석 한 줄이 그 설계를 통째로 말한다.

## 위치

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1480-L1544 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1480-L1544))

## 실제 코드

포크하는 쪽의 주석이 전부를 말한다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1569-L1582 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1569-L1582))

> single-threaded: started when totalQueueSize transitions from 0 to 1 and keeps calling itself until the queue is drained.

배치를 하나 꺼내 돌린다.

```java
// MasterService.java L1505-L1513
                final var nextBatch = takeNextBatch();
                assert currentlyExecutingBatch == nextBatch;
                if (lifecycle.started()) {
                    starvationWatcher.onCurrentBatchPriority(nextBatch.getPriority());
                    nextBatch.run(batchCompletionListener);
                } else {
                    nextBatch.onRejection(new NotMasterException("node closed", getRejectionException()));
                    batchCompletionListener.onResponse(null);
                }
```

끝나면 남은 게 있을 때만 자기를 다시 건다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1524-L1532 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1524-L1532))

```java
// MasterService.java L1524-L1532
        private void onCompletion() {
            currentlyExecutingBatch = null;
            if (totalQueueSize.decrementAndGet() > 0) {
                starvationWatcher.onNonemptyQueue();
                forkQueueProcessor();
            } else {
                starvationWatcher.onEmptyQueue();
            }
        }
```

우선순위 순서로 고른다.

```java
// MasterService.java L1549-L1563
        for (final var queue : queuesByPriority.values()) {
            var batch = queue.queue.poll();
            if (batch != null) {
                queue.queuedBatchCount.getAndDecrement();
                currentlyExecutingBatch = batch;
                if (executionHistory.isEmpty()
                    || executionHistory.peekFirst().incrementCountIfMatching(batch.queueName(), queue.priority) == false) {
                    while (executionHistory.size() >= maxExecutionHistorySize) {
                        executionHistory.removeLast();
                    }
                    executionHistory.addFirst(new ExecutionHistoryEntry(batch.queueName(), queue.priority()));
                }
                return batch;
            }
        }
```

## 동작 흐름

```text
 forkQueueProcessor                               L1569
   L1571  lifecycle 이 안 떴으면 => drainQueueOnRejection
   L1578  스레드 문맥을 저장하고
   L1579  clusterStateUpdateContext 를 복원한 뒤
   L1580  threadPoolExecutor.execute(queuesProcessor)

 queuesProcessor.doRun                            L1482
   L1483  assert 시스템 문맥이다
   L1485  assert 지금 도는 배치가 없다
   L1505  takeNextBatch()
   L1507  lifecycle 이 떠 있으면
   L1509    nextBatch.run(batchCompletionListener)
   L1511  아니면 onRejection 으로 배치를 실패시킨다

 onCompletion                                     L1524
   L1525  currentlyExecutingBatch = null
   L1526  totalQueueSize 를 하나 줄여 남은 게 있으면
   L1528    forkQueueProcessor()      <- 자기를 다시 건다
   L1530  없으면 starvationWatcher 에 빈 큐를 알린다
```

```text
 "하나만 돈다"를 무엇이 보장하는가

 totalQueueSize 가 0 -> 1 로 갈 때만 포크한다 (L1637)
 그리고 배치가 끝날 때 1 씩 줄이면서 남았으면 다시 포크한다 (L1526)

 즉 **포크 횟수 = 배치 수** 이고
 어느 시점에도 대기 중이거나 도는 처리기가 하나다

 assert 가 그것을 확인한다 (L1485)
   assert currentlyExecutingBatch == null;

 스레드풀이 max 1 인 것과는 별개의 장치다
 스레드풀만으로는 처리기가 여럿 큐잉되는 것을 못 막는다
 (주석은 없다. 두 장치를 비교하고 내가 판단한 것이다)
```

```text
 takeNextBatch 는 우선순위 순서로 훑는다 (L1546-1567)

 L1549  queuesByPriority.values() 를 순회한다
 L1550  poll 해서 나오면 그것을 쓴다
 L1552  그 큐의 배치 수를 하나 줄인다
 L1554  실행 이력에 남긴다 (같은 큐가 연속이면 횟수만 올린다)
 L1561  돌려준다

 L1564  하나도 못 찾으면 로그와 assert 후 IllegalStateException
        totalQueueSize 가 0 보다 큰데 큐가 비었다는 뜻이라
        카운터가 어긋난 상태다
```

```text
 배치 하나를 고르고 나면 우선순위는 다시 안 본다

 고른 배치를 끝까지 돌린다
 그 사이 더 높은 우선순위 태스크가 들어와도 끼어들지 못한다

 우선순위가 작동하는 것은 **다음 배치를 고를 때**다
 그래서 긴 배치 하나가 돌고 있으면 그만큼 밀린다
 (주석은 없다. takeNextBatch 의 호출 시점을 보고 내가 판단한 것이다)
```

```text
 셧다운이면 큐를 비운다

 drainQueueOnRejection L1589-1605
   totalQueueSize 가 0 이 될 때까지
   takeNextBatch -> nextBatch.onRejection(e) 를 반복한다

 들어오는 길이 둘이다
   forkQueueProcessor 의 L1572   포크하려는데 이미 멈춰 있다
   queuesProcessor.onRejection L1537  실행기가 거부했다

 예외는 NotMasterException 이고 원인에 거부 예외가 달린다
 Batch 인터페이스의 javadoc 이 왜 그 타입인지 말한다 (L1667-1671)
```

```text
 completion 리스너가 두 갈래인데 하는 일이 같다

 L1489  onResponse  -> onCompletion()
 L1494  onFailure   -> error 로그 + assert false -> onCompletion()

 즉 배치가 어떻게 끝나든 다음 배치는 걸린다
 실패가 고리를 멈추지 않는다

 그런데 L1494 로 오는 예외는 **태스크에 안 알려진다**
 error 로그와 assert false 뿐이다

 여기로 오는 것은 executeAndPublishBatch 안에서도
 L405 ActionListener.run **바깥**에서 난 예외다
 (patchVersions, logExecutionTime, taskManager.register, newTraceContext)
```

```text
 Error 는 이 고리를 아예 빠져나간다

 executeTasks 의 L1206 은 AssertionError 를 무조건 던진다
 ActionListener.run 도 AbstractRunnable 도 catch(Exception) 이라 못 잡는다

 그러면 onCompletion 이 안 돌아
 totalQueueSize 가 안 줄고 currentlyExecutingBatch 도 안 비워진다

 (그 뒤를 스레드풀이 어떻게 처리하는지는 확인하지 못했다)
```

## 결과가 쓰이는 곳

```text
 batchCompletionListener
      --> Processor.run 에 넘어가고 (L1509)
      --> 그것이 runBefore 로 executing 을 비운 뒤 (L1985-1987)
      --> batchConsumer.runBatch 로 이어진다 (L1988)

 currentlyExecutingBatch
      --> pendingTasks / getMaxTaskWaitTime 이 지금 도는 배치를 제외하는 데 쓴다

 실행 이력 (executionHistory)
      --> 같은 큐가 연속으로 잡는지 보는 진단용이다
      --> maxExecutionHistorySize 만큼만 남긴다 (L1556-1558)
```

## 다루지 않는 것

`StarvationWatcher` 가 우선순위 기아를 재는 방식, `ClusterStateUpdateStatsTracker` 의 지표, `pendingTasks`(L741)와 `getMaxTaskWaitTime`(L766)이 큐를 훑는 방법, `clusterStateUpdateContext` 가 보존하는 스레드 문맥의 내용, `EsExecutors.newScaling` 의 큐 구현은 같은 뼈대의 곁가지라 요약만 했다.
