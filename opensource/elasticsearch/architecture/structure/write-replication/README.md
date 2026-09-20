# 쓰기 복제

같은 문서가 프라이머리와 레플리카에 **어떤 순서로** 쓰이는가. 이 순서가 "레플리카는 왜 항상 프라이머리보다 뒤에 있는가"를 설명한다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 쓰기 요청이 들어왔을 때

 코디네이터 노드
   [샤드 모델]의 계산으로 어느 샤드인지 정한다
   [클러스터 상태]의 라우팅 테이블에서 그 샤드의 프라이머리 위치를 찾는다
   |
   v
 프라이머리 노드
   먼저 자기 샤드에 쓴다 (Lucene + translog 버퍼, 순번 부여)
   성공하면
   |
   v
 레플리카 노드들
   같은 연산을 보낸다 (ReplicationOperation L193 performOnReplicas)
   |
   v
 모두 끝나면 코디네이터에 응답 (L111-120 RefCountingListener)
```

```text
 "프라이머리가 완전히 끝난 뒤"는 아니다

 L193  performOnReplicas       레플리카로 먼저 보낸다
 L202  runPostReplicationActions  그 뒤에 프라이머리의 fsync/refresh

 TransportWriteAction L282-285 주석이 이유를 적어 두었다
   "We call this after replication because this might wait for a refresh
    and that can take a while.
    This way we wait for the refresh in parallel on the primary and on the replica."

 즉 프라이머리의 fsync 와 refresh 는 레플리카 왕복과 병렬로 돈다
 순서가 있는 것은 "샤드 연산과 순번 부여"까지다
```

```text
 프라이머리가 먼저인 것이 핵심이다

 프라이머리가 연산을 받아들이면서 순번을 매긴다
 레플리카는 그 순번대로 같은 연산을 적용한다

 그래서 두 복제본이 같은 결과에 도달한다
 레플리카가 독자적으로 판단하지 않는다

 프라이머리의 샤드 연산 자체가 실패하면 레플리카에 보내지 않는다
 프라이머리에 없는 것이 레플리카에 생기는 일은 없다

 다만 문서 하나가 실패한 경우는 다르다
 그 문서도 순번을 소비한 no-op 으로 기록되어 복제된다
 (InternalEngine L1350-1359)
```

```text
 응답 시점

 기본은 그 시점에 추적 중인(tracked) 복제본이 모두 끝난 뒤에 응답한다
 그래서 색인 응답을 받으면 레플리카에도 반영돼 있다

 대상에서 빠지는 복제본이 있다 (ReplicationGroup L47-73)
   승격 불가(검색 전용) 복제본은 아예 제외한다
   추적 중이 아닌 복제본은 숫자만 세고 기다리지 않는다

 레플리카 하나가 느리면 그만큼 응답도 늦어진다
 레플리카가 실패하면 마스터에 알려 그 복제본을 떨어뜨린다
```

```text
 읽기는 아무 복제본에서나 온다

 쓰기   프라이머리 -> 레플리카  (순서가 있다)
 읽기   프라이머리와 레플리카 중 아무거나  (부하 분산)

 그래서 레플리카를 늘리면 검색 처리량이 올라간다
 쓰기 처리량은 오히려 내려간다. 복제할 곳이 늘어나기 때문이다
```

## 실제 코드

프라이머리가 끝난 뒤 레플리카로 보내는 호출부.

`server` / `org.elasticsearch.action.support.replication` / `ReplicationOperation.java` L192-L200 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/replication/ReplicationOperation.java#L192-L200))

```java
// ReplicationOperation.java L192-L200
            final PendingReplicationActions pendingReplicationActions = primary.getPendingReplicationActions();
            performOnReplicas(
                replicaRequest,
                globalCheckpoint,
                maxSeqNoOfUpdatesOrDeletes,
                replicationGroup,
                pendingReplicationActions,
                pendingActionsListener
            );
```

레플리카마다 같은 연산을 보내는 루프.

`server` / `org.elasticsearch.action.support.replication` / `ReplicationOperation.java` L265-L277 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/replication/ReplicationOperation.java#L265-L277))

```java
// ReplicationOperation.java L265-L276
        for (final ShardRouting shard : replicationGroup.getReplicationTargets()) {
            if (shard.isSameAllocation(primaryRouting) == false) {
                performOnReplica(
                    shard,
                    replicaRequest,
                    globalCheckpoint,
                    maxSeqNoOfUpdatesOrDeletes,
                    pendingReplicationActions,
                    pendingActionsListener
                );
            }
        }
```

## 어디에서 쓰이는가

```text
 [샤드 모델] 어느 복제본이 프라이머리인지가 입력이다
 [클러스터 상태] 그 정보가 라우팅 테이블에 있다
 [지속성] 프라이머리와 레플리카 각각이 같은 단계를 밟는다
 [노드 역할] 데이터 역할 노드들 사이에서만 일어난다
```

샤드 구조는 [샤드 모델](../shard-model/README.md), 각 노드 안에서 벌어지는 일은 [지속성](../durability/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 프라이머리 우선 순서
      --> 두 복제본의 결과가 갈라지지 않는 근거다
      --> 프라이머리가 순번을 매기고 레플리카가 따른다

 추적 중인 복제본을 기다리는 응답
      --> 응답을 받으면 레플리카에도 있다는 뜻이다
      --> 대신 가장 느린 복제본이 응답 시간을 정한다

 레플리카 실패 처리
      --> 일부 오류는 먼저 재시도한다 (RetryableAction L347-377)
      --> 그래도 안 되면 복제본을 떨어뜨리고 마스터가 다시 할당한다
      --> 이때도 쓰기 자체는 보통 실패하지 않는다
      --> 예외: 떨어뜨리려다 자기가 더 이상 프라이머리가 아님이 드러나면
          전체가 실패한다 (onNoLongerPrimary L424-454)

 레플리카 개수의 트레이드오프
      --> 늘리면 검색 처리량과 내결함성이 올라간다
      --> 쓰기 비용과 디스크 사용량도 함께 올라간다
```

## 다루지 않는 것

`wait_for_active_shards` 로 쓰기 전 조건을 거는 방식, 시퀀스 번호와 프라이머리 텀이 정합성을 지키는 메커니즘, 글로벌 체크포인트 전파, in-sync 할당 집합(`in-sync allocation IDs`), 레플리카 실패 시의 재할당 경로, 프라이머리 승격 절차는 같은 뼈대의 곁가지라 요약만 했다. 실제 호출 경로는 별도 흐름 문서에서 다룬다.
