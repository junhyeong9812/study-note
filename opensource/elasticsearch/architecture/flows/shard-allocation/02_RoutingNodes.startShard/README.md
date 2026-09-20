# RoutingNodes.startShard

상위: [샤드 시작 반영](../README.md)

**실제로 샤드를 옮기는 곳이다.** 한 줄 짜리 일처럼 보이지만 아니다 — 이동 대상이었으면 원본을 지우고, 그것이 primary 였으면 **초기화 중이던 replica 들을 전부 다시 시작시킨다.**

## 위치

`RoutingNodes.java` `server` / `org.elasticsearch.cluster.routing` / `RoutingNodes.java` L549-L605 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/RoutingNodes.java#L549-L605))

## 실제 코드

javadoc 이 연쇄를 예고한다.

`server` / `org.elasticsearch.cluster.routing` / `RoutingNodes.java` L540-L547 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/RoutingNodes.java#L540-L547))

> Moves the initializing shard to started. If the shard is a relocation target, also removes the relocation source.

> If the started shard is a primary relocation target, this also reinitializes currently initializing replicas as their recovery source changes

본체의 시작은 세 줄이다.

```java
// RoutingNodes.java L554-L556
        ensureMutable();
        ShardRouting startedShard = started(initializingShard, startedExpectedShardSize);
        routingChangesObserver.shardStarted(initializingShard, startedShard);
```

상태를 바꾸는 것은 `started` 다.

`server` / `org.elasticsearch.cluster.routing` / `RoutingNodes.java` L761-L774 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/RoutingNodes.java#L761-L774))

```java
// RoutingNodes.java L763-L772
        if (shard.relocatingNodeId() == null) {
            // if this is not a target shard for relocation, we need to update statistics
            inactiveShardCount--;
            if (shard.primary()) {
                inactivePrimaryCount--;
            }
        }
        removeRecovery(shard);
        ShardRouting startedShard = shard.moveToStarted(expectedShardSize);
        updateAssigned(shard, startedShard);
```

이동 원본을 지운다.

```java
// RoutingNodes.java L568-L569
            remove(relocationSourceShard);
            routingChangesObserver.relocationCompleted(relocationSourceShard);
```

그리고 replica 들을 다시 시작시킨다.

`server` / `org.elasticsearch.cluster.routing` / `RoutingNodes.java` L571-L598 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/RoutingNodes.java#L571-L598))

```java
// RoutingNodes.java L579-L586
                            ShardRouting sourceShard = getByAllocationId(routing.shardId(), routing.allocationId().getRelocationId());
                            // cancel relocation and start relocation to same node again
                            ShardRouting startedReplica = cancelRelocation(sourceShard);
                            remove(routing);
                            routingChangesObserver.shardFailed(
                                routing,
                                new UnassignedInfo(UnassignedInfo.Reason.REINITIALIZED, "primary changed")
                            );
```

```java
// RoutingNodes.java L596-L597
                            ShardRouting reinitializedReplica = reinitReplica(routing);
                            routingChangesObserver.initializedReplicaReinitialized(routing, reinitializedReplica);
```

## 동작 흐름

```text
 L554  ensureMutable()        readOnly 면 IllegalStateException (L1379-1383)
 L555  startedShard = started(initializingShard, expectedShardSize)
 L556  observer.shardStarted(initializingShard, startedShard)

 L558  이동 대상이었나 (relocatingNodeId != null)
   아니오 => L604 그대로 돌려준다
   예
     L560  원본 노드를 찾는다
     L568  remove(relocationSourceShard)
     L569  observer.relocationCompleted(relocationSourceShard)
     L572  시작된 것이 primary 인가
       예  L573  같은 shardId 의 할당된 샤드 목록
           L575  복사해서 순회한다
                   주석 L574: "copy list to prevent ConcurrentModificationException"
           L576  초기화 중인 replica 인가
             L577  그것이 이동 대상인가
               예  L581  cancelRelocation(sourceShard)
                   L582  remove(routing)
                   L583  observer.shardFailed(routing, REINITIALIZED "primary changed")
                   L587  relocateShard(...)  같은 노드로 다시 이동 시작
               아니오  L596 reinitReplica(routing)
                       L597 observer.initializedReplicaReinitialized(...)
 L604  return startedShard
```

```text
 started 가 통계를 조건부로만 고친다 (L761-774)

 L762  assert 초기화 중이어야 한다
 L763  이동 대상이 아니었을 때만
 L765    inactiveShardCount--
 L767    primary 면 inactivePrimaryCount--

 주석이 그 자리를 말한다 (L764)
   "if this is not a target shard for relocation, we need to update statistics"

 이동 대상이었다면 원본이 이미 활성으로 세어져 있다
 여기서 또 빼면 이중으로 빠진다
 (주석은 "왜"를 말하지 않는다. 뒷문장은 내가 붙인 것이다)
```

```text
 L770 removeRecovery 가 연쇄를 하나 더 가진다

 removeRecovery(L217-219) -> updateRecoveryCounts(L225-254)

 L231  이 노드의 incoming 복구 수를 하나 줄인다
 L233  복구원이 PEER 면
 L235    primary 가 미할당이면 => IllegalStateException
           "shard [...] is peer recovering but primary is unassigned"
 L238    primary 노드의 outgoing 수를 하나 줄인다
 L240    **primary 가 이동을 끝낸 경우**
 L250      옛 primary 노드의 outgoing 을 복제본 수만큼 빼고
 L251      새 primary 노드에 그만큼 더한다
           주석 L241: "primary is done relocating, move non-primary recoveries
                       from old primary to new primary"

 즉 이 한 줄 안에 예외 경로와 카운터 이전이 들어 있다
```

```text
 이 카운터들은 새 상태에 안 실린다

 inactiveShardCount / inactivePrimaryCount / relocatingShards /
 recoveriesPerNode 는 전부 RoutingNodes 사본의 필드다

 마지막에 rebuild 가 만드는 것은 라우팅 테이블이지 RoutingNodes 가 아니다
 사본은 버려진다

 그런데도 정확히 세는 이유는 assertShardStats(ALSV L166)가 재계산해 대조하기 때문이다
 (주석은 없다. 필드의 위치와 assert 의 내용을 맞춰 보고 내가 판단한 것이다)
```

```text
 L568 의 remove 도 그냥 지우는 게 아니다 (L828-844)

 이동 원본은 RELOCATING 상태다
 그래서 L837 의 갈래를 탄다
   failRelocation(shard) -> abortRelocation(shard, true)  L798-806
     relocatingShards--                                    L799
     frozen 노드면 relocatingFrozenShards--                L800-802
     ShardRouting.failRelocation() 이 실패 카운트를 올린 새 객체를 만든다
 그 뒤 assignedShardsRemove(shard) 로 지워진다               L840

 실패 카운트를 올린 객체가 곧바로 사라지므로
 새 라우팅 테이블에는 안 남는다. 남는 실효는 relocatingShards-- 뿐이다
 (주석은 없다. 두 단계를 이어 보고 내가 판단한 것이다)
```

```text
 관측자 메서드가 한 호출에서 다섯 종까지 불린다

 shardStarted                    L556  언제나
 relocationCompleted             L569  이동 대상이었을 때
 shardFailed                     L583  primary 이동 완료 + 이동 대상 replica
 relocationStarted               L587 -> relocateShard L534  같은 조건
 initializedReplicaReinitialized L597  primary 이동 완료 + 보통 replica

 뒤의 셋은 replica 마다 갈리지만
 서로 다른 replica 가 각각 다른 갈래로 갈 수 있다
```

```text
 왜 replica 를 다시 시작시키나

 주석이 말한다 (L571)
   "if this is a primary shard with ongoing replica recoveries,
    reinitialize them as their recovery source changed"

 RoutingChangesObserver 의 javadoc 이 더 직접적이다 (L66-68)
   "Called when an initializing replica is reinitialized. This happens when a
    primary relocation completes, which reinitializes all currently initializing
    replicas as their recovery source node changes"

 복제본은 primary 에서 데이터를 받아 온다
 primary 가 다른 노드로 옮겨 갔으니 받아 오던 곳이 사라진 것이다
```

```text
 이동 중인 replica 는 취소하고 다시 건다

 L581  cancelRelocation(sourceShard)    원본을 STARTED 로 되돌린다
 L582  remove(routing)                  이동 대상을 지운다
 L583  shardFailed(REINITIALIZED, "primary changed")
 L587  relocateShard(startedReplica, sourceShard.relocatingNodeId(), ...)
         사유는 "restarting relocation"

 같은 목적지로 다시 건다 - L589 가 sourceShard.relocatingNodeId() 를 쓴다
 즉 목적지는 그대로고 출발선만 되돌린다
```

```text
 L583 의 shardFailed 는 메타데이터를 안 바꾼다

 IndexMetadataUpdater.shardFailed 의 조건이 이렇다 (IMU L89)
   if (failedShard.active() && failedShard.primary())

 여기서 넘기는 routing 은 초기화 중인 replica 다
 active() 도 primary() 도 거짓이라 걸러진다

 즉 이 shardFailed 는 라우팅 쪽 사건일 뿐이다
 (주석은 없다. 두 조건을 맞춰 보고 내가 판단한 것이다)
```

## 결과가 쓰이는 곳

```text
 바뀐 RoutingNodes
      --> buildResultAndLogHealthChange 가 rebuild 의 입력으로 쓴다 (ALSV L176)

 관측자에 쌓인 변경
      --> IndexMetadataUpdater 가 in-sync 집합과 primary term 으로 환산한다
      --> relocationCompleted 는 원본의 allocation id 를 in-sync 에서 뺀다

 돌려준 startedShard
      --> 사설 applyStartedShards 는 이 반환값을 안 쓴다 (ALSV L772)
      --> 다른 호출처를 위해 있는 반환값이다
```

## 다루지 않는 것

`updateAssigned` 와 `removeRecovery` 가 내부 색인을 갱신하는 방식, `ShardRouting.moveToStarted` / `relocate` / `reinitializeReplicaShard` 가 만드는 새 객체의 필드, `cancelRelocation` 과 `abortRelocation` 의 차이(실패 카운터), `relocateShard` 가 세는 통계(`relocatingShards`, `relocatingFrozenShards`), `RoutingNodes` 의 나머지 변경 메서드들(`failShard`, `promoteAssignedReplicaShardToPrimary` 등)은 같은 뼈대의 곁가지라 요약만 했다. 관측자 목록은 [spi](../spi/README.md)에 있다.
