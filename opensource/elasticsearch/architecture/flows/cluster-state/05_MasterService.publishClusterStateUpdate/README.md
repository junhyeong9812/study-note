# MasterService.publishClusterStateUpdate

상위: [클러스터 상태 갱신](../README.md)

상태를 다른 노드에 보내고 결과를 받는다. **마스터 스레드가 여기서 손을 놓고**, 발행이 끝나면 완료가 그 스레드로 되돌아온다. 완료 리스너의 실패 갈래가 셋인데 **태스크에 알리는 것은 하나뿐**이다. 그리고 발행 호출 자체가 동기로 던지는 실패 경로가 바깥에 하나 더 있다(L407-411).

## 위치

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L439-L608 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L439-L608))

## 실제 코드

발행 이벤트를 만든다.

```java
// MasterService.java L456-L463
        final ClusterStatePublicationEvent clusterStatePublicationEvent = new ClusterStatePublicationEvent(
            summary,
            previousClusterState,
            newClusterState,
            task,
            computationTime.millis(),
            publicationStartTime
        );
```

보내기 직전에 초기화를 딴 스레드에 던진다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L480-L483 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L480-L483))

```java
// MasterService.java L480-L483
        logger.debug("publishing cluster state version [{}]", newClusterState.version());
        // initialize routing nodes and the indices lookup concurrently, we will need both of them for the cluster state
        // application and can compute them while we wait for the other nodes during publication
        newClusterState.initializeAsync(threadPool.generic());
```

> initialize routing nodes and the indices lookup concurrently, we will need both of them for the cluster state application and can compute them while we wait for the other nodes during publication

발행의 본체는 `publish` 다. 주석이 스레드 전환을 설명한다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L618-L635 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L618-L635))

```java
// MasterService.java L623-L634
        clusterStatePublisher.publish(
            clusterStatePublicationEvent,
            // Fork the completion of publicationListener back onto the master service thread, mainly for legacy reasons; note that this
            // might be rejected if the MasterService shut down mid-publication. The master service thread remains idle until this listener
            // is completed at the end of the publication, at which point the publicationListener performs various bits of cleanup and then
            // picks up the next waiting task.
            new ThreadedActionListener<>(
                threadPoolExecutor,
                new ContextPreservingActionListener<>(threadPool.getThreadContext().newRestorableContext(false), publicationListener)
            ),
            ackListener
        );
```

> Fork the completion of publicationListener back onto the master service thread, mainly for legacy reasons; note that this might be rejected if the MasterService shut down mid-publication. The master service thread remains idle until this listener is completed at the end of the publication, at which point the publicationListener performs various bits of cleanup and then picks up the next waiting task.

성공하면 태스크에 알리고 실행기에 알린다.

```java
// MasterService.java L503-L506
                    final long notificationStartTime = threadPool.rawRelativeTimeInMillis();
                    for (final var executionResult : executionResults) {
                        executionResult.onPublishSuccess(newClusterState);
                    }
```

```java
// MasterService.java L508-L515
                    try {
                        executor.clusterStatePublished(newClusterState);
                    } catch (Exception e) {
                        logger.error(
                            () -> format("exception thrown while notifying executor of new cluster state publication [%s]", summary),
                            e
                        );
                    }
```

실패를 태스크에 전달하는 것은 이 갈래뿐이다.

```java
// MasterService.java L555-L557
                        for (final var executionResult : executionResults) {
                            executionResult.onPublishFailure(exception);
                        }
```

나머지 둘은 로그와 통계로 끝난다.

```java
// MasterService.java L566-L576
                        assert esRejectedExecutionException.isExecutorShutdown();
                        clusterStateUpdateStatsTracker.onPublicationFailure(
                            threadPool.rawRelativeTimeInMillis(),
                            clusterStatePublicationEvent,
                            0L
                        );
                        final long version = newClusterState.version();
                        logger.debug(
                            () -> format("shut down during publication of cluster state version [%s]: [%s]", version, summary),
                            exception
                        );
```

> TODO also bubble the failure up to the tasks too

```java
// MasterService.java L579-L585
                        assert publicationMayFail() : exception;
                        clusterStateUpdateStatsTracker.onPublicationFailure(
                            threadPool.rawRelativeTimeInMillis(),
                            clusterStatePublicationEvent,
                            0L
                        );
                        handleException(summary, publicationStartTime, newClusterState, exception);
```

그리고 `handleException` 은 로그 한 줄이다.

```java
// MasterService.java L637-L649
    private void handleException(BatchSummary summary, long startTimeMillis, ClusterState newClusterState, Exception e) {
        logger.warn(
            () -> format(
                "took [%s] and then failed to publish updated cluster state (version: %s, uuid: %s) for [%s]:\n%s",
                getTimeSince(startTimeMillis),
                newClusterState.version(),
                newClusterState.stateUUID(),
                summary,
                newClusterState
            ),
            e
        );
    }
```

## 동작 흐름

```text
 L450  trace 면 상태 전체를, 아니면 버전만 찍는다
 L456  ClusterStatePublicationEvent 를 만든다
 L466  노드 델타가 있으면 info 로 찍는다
 L483  initializeAsync(generic)        합류하지 않는다
 L484  publish(event, ackListener, 완료리스너)
         ackListener = CompositeTaskAckListener      L486-499
           ack 리스너가 **있는** 태스크만 TaskAckListener 로 감싼다 (L489 필터)

 완료 onResponse                        L502
   L504  태스크마다 onPublishSuccess(newClusterState)
   L509  executor.clusterStatePublished(newClusterState)
   L510    거기서 난 예외는 error 로그만
   L516  통지 시간 로그 / L526 통계

 완료 onFailure                         L534
   L535  FailedToCommit 또는 NotMaster 면
   L539    FailedToCommit 은 warn, NotMaster 는 debug
   L555    태스크마다 onPublishFailure(exception)     <- 유일하게 알리는 갈래
   L560    통계 (실측 시간)
   L565  EsRejectedExecutionException 이면
   L567    통계 (0 으로 기록) + debug 로그. 태스크에 안 알린다
   L578  그 외
   L579    assert publicationMayFail()
   L580    통계 (0) + handleException = warn 로그. 태스크에 안 알린다

 L596  runAfter 의 Runnable 이 listener.onResponse(null) 을 부른다
         성공이든 실패든 반드시 돈다
```

```text
 마스터 스레드가 언제 손을 놓는가

 publish(L618) 안에서 clusterStatePublisher.publish 를 부르는데
 완료 리스너를 ThreadedActionListener 로 감싼다 (L629-632)

 그래서 완료는 반드시 executor 큐를 한 번 거친다
 그 사이 마스터 스레드에는 할 일이 없다

 주석의 "remains idle" 은 그 뜻이다
 다만 스레드풀이 core 0 이라 60초를 넘기면 스레드 자체가 사라지고
 완료 시 새로 만들어진다
```

```text
 L565 갈래는 "발행 실패" 가 아닐 수도 있다

 거부된 것은 발행이 아니라 **마스터 스레드로 되돌아오는 포크**다
 주석 L625-626 이 그 상황을 말한다
   "this might be rejected if the MasterService shut down mid-publication"

 즉 상태는 이미 커밋됐을 수 있는데 알릴 스레드가 없는 것이다
 TODO 주석(L577)이 태스크에 못 알리는 것을 인정한다
```

```text
 실패 갈래 셋 중 둘이 침묵한다

 L535  FailedToCommit / NotMaster    onPublishFailure 로 알린다
 L565  EsRejectedExecution           통계만
 L578  그 외                          handleException = warn 로그만

 handleException(L637-649)은 logger.warn 하나가 전부다
 태스크를 건드리지 않는다

 L578 갈래는 assert publicationMayFail() 이 붙어 있는데
 운영에서 publicationMayFail() 은 false 를 돌려주므로 (L610-612)
 그 assert 는 "여기 오면 안 된다"는 표시다
```

```text
 실패한 태스크는 ack 리스너를 아예 못 받는다

 L489  .filter(Objects::nonNull)

 getContextPreservingAckListener 가 null 을 주는 경우가 둘이다 (L1182)
   ack 리스너를 등록 안 했거나
   그 태스크가 실패했거나

 그래서 TaskAckListener 는 성공했고 ack 를 듣는 태스크 것만 만들어진다
```

```text
 L509 는 성공했을 때만 불린다

 onResponse 안에만 있다. onFailure 쪽에는 없다

 그리고 거기서 난 예외는 error 로그로 삼킨다 (L510-515)
 실행기의 후처리가 실패해도 발행은 성공으로 남는다

 [샤드 시작 반영]이 후속 reroute 를 거는 자리가 이것이다
```

## 결과가 쓰이는 곳

```text
 발행된 상태
      --> 다른 노드들이 받아 적용한다
      --> 이 노드도 적용 경로로 들어간다

 태스크 통지
      --> 성공은 onPublishSuccess, 실패는 갈래 하나에서만
      --> 실행기가 실패로 표시해 둔 태스크는 성공 쓸기에서 notifyFailure 로 빠진다

 ack
      --> TaskAckListener 가 노드별 ack 를 모아 집계한다
      --> 다 모이면 onAckSuccess, 타임아웃이면 onAckTimeout

 listener.onResponse(null)
      --> runAfter 로 반드시 돈다 (L596-606)
      --> 그래서 실패해도 다음 배치가 걸린다
```

## 다루지 않는 것

`Coordinator` 와 `PublicationTransportHandler` 가 상태를 전송하고 커밋을 모으는 과정, `ClusterState.initializeAsync` 가 무엇을 언제 계산하는지, `TaskAckListener` 의 카운트다운과 타임아웃 예약, `ContextPreservingAckListener` 의 문맥 복원, `ClusterStateUpdateStatsTracker` 의 지표, `taskManager` 등록·해제는 같은 뼈대의 곁가지라 요약만 했다. 태스크가 통지받는(또는 못 받는) 갈래 전체는 [spi](../spi/README.md)에 표로 모았다.
