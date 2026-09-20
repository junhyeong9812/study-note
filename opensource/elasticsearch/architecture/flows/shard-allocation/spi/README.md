# spi

상위: [샤드 시작 반영](../README.md)

이 흐름의 계약은 `RoutingChangesObserver` 하나다. 라우팅을 고치는 쪽과 메타데이터를 고치는 쪽이 이 인터페이스로만 만난다. 인용은 주석 원문이고, 그 아래 설명은 원문이 이유를 말하지 않을 때 내가 붙인 것이다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19).

## 메서드 열 개

`RoutingChangesObserver.java` `server` / `org.elasticsearch.cluster.routing` / `RoutingChangesObserver.java` L15-L69 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/RoutingChangesObserver.java#L15-L69))

전부 `default` 빈 몸통이다. 구현체는 관심 있는 것만 덮어쓴다.

```java
// RoutingChangesObserver.java L22-L32
    default void shardInitialized(ShardRouting unassignedShard, ShardRouting initializedShard) {}

    /**
     * Called when an initializing shard is started.
     */
    default void shardStarted(ShardRouting initializingShard, ShardRouting startedShard) {}

    /**
     * Called when relocation of a started shard is initiated.
     */
    default void relocationStarted(ShardRouting startedShard, ShardRouting targetRelocatingShard, String reason) {}
```

각 메서드의 javadoc 이 "언제 불리는지"를 적어 둔다.

```text
 shardInitialized                L20-21
   "Called when unassigned shard is initialized.
    Does not include initializing relocation target shards."

 shardStarted                    L25
   "Called when an initializing shard is started."

 relocationStarted               L30
   "Called when relocation of a started shard is initiated."

 unassignedInfoUpdated           L35
 relocationFailureInfoUpdated    L40-41

 shardFailed                     L45
   "Called when a shard is failed or cancelled."

 relocationCompleted             L50
   "Called on relocation source when relocation completes after
    relocation target is started."

 relocationSourceRemoved         L55-56
 replicaPromoted                 L61
   "Called when started replica is promoted to primary."

 initializedReplicaReinitialized L66-68
   "Called when an initializing replica is reinitialized. This happens when a
    primary relocation completes, which reinitializes all currently initializing
    replicas as their recovery source node changes"
```

## 이 흐름이 실제로 부르는 것은 다섯

```text
 shardStarted                    RNOD L556  언제나
 relocationCompleted             RNOD L569  이동 대상이었을 때
 shardFailed                     RNOD L583  primary 이동 완료 + 이동 대상 replica
 relocationStarted               RNOD L535  같은 조건 (relocateShard 안에서)
 initializedReplicaReinitialized RNOD L597  primary 이동 완료 + 보통 replica

 나머지 다섯은 이 경로에서 안 불린다
 특히 shardInitialized 가 안 불리는 것이 primary term 이 안 오르는 이유다
```

## 누가 무엇을 듣는가

관측자는 `DelegatingRoutingChangesObserver` 가 배열 순서대로 돌린다. 이 흐름에서는 여섯이다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `MutableRoutingAllocation.java` L71-L77 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/MutableRoutingAllocation.java#L71-L77))

```java
// MutableRoutingAllocation.java L71-L77
                : new RoutingChangesObserver[] {
                    nodesChangedObserver,
                    indexMetadataUpdater,
                    restoreInProgressUpdater,
                    resizeSourceIndexUpdater,
                    new MaxWriteLoadProportionCacheInvalidator(),
                    shardChangesObserver }
```

| 관측자 | 덮어쓴 개수 | 무엇을 듣나 | 하는 일 |
|---|---|---|---|
| `RoutingNodesChangedObserver` | **10** | 전부 | 변경 플래그 하나를 세운다 |
| `IndexMetadataUpdater` | 4 | `shardInitialized` `shardStarted` `shardFailed` `relocationCompleted` | in-sync 집합과 primary term 을 쌓는다 |
| `RestoreInProgressUpdater` | 4 | `shardStarted` `shardFailed` `shardInitialized` `unassignedInfoUpdated` | 복원 진행 상황을 기록한다 |
| `ResizeSourceIndexSettingsUpdater` | **1** | `shardStarted` | resize 원본 설정을 지울 인덱스를 모은다 |
| `MaxWriteLoadProportionCacheInvalidator` | 2 | `shardStarted` `relocationStarted` | 노드별 캐시를 버린다 |
| `ShardChangesObserver` | 5 | `shardInitialized` `shardStarted` `relocationStarted` `shardFailed` `replicaPromoted` | 로그와 지표를 남긴다 |

열 개를 다 듣는 것은 `RoutingNodesChangedObserver` 하나뿐이다. 하는 일이 플래그 하나라서 그렇다. 나머지는 자기가 필요한 것만 덮어쓴다.

```text
 시뮬레이션이면 다섯이다 (MRAL L64-70)

 빠지는 것은 마지막 shardChangesObserver 다
 호출자가 생성자 인자로 준 것이다 (MRAL L55)

 그런데 이 흐름에서는 그럴 일이 없다
 AllocationService L817 이 isSimulating 자리에 상수 false 를 넘긴다
 다섯 개 구성은 desired-balance 계산 쪽에서만 나온다
```

```text
 MaxWriteLoadProportionCacheInvalidator 는 둘만 듣는다

 javadoc 이 왜 둘만인지 적어 두었다 (MRAL L192-194)
   "Note that there are other transitions which would affect this number
    (e.g., shard failures, relocation failures), but they don't occur in
    desired balance computation or reconciliation, so we don't handle them."

 즉 "안 일어나니까 안 다룬다" 고 명시한 것이다
```

## 위임되지 않는 것이 하나 있다

```text
 DelegatingRoutingChangesObserver 가 덮어쓴 메서드는 아홉이다
   L80  shardInitialized
   L87  shardStarted
   L94  relocationStarted
   L101 unassignedInfoUpdated
   L108 shardFailed
   L115 relocationCompleted
   L122 relocationSourceRemoved
   L129 replicaPromoted
   L136 initializedReplicaReinitialized

 빠진 것: relocationFailureInfoUpdated (L42 선언)

 그래서 그 메서드를 위임 관측자에게 부르면
 인터페이스의 빈 default 가 먹고 배열의 여섯에게 안 간다

 다만 지금은 아무도 그것을 부르지 않는다
 (grep 범위: server/src, x-pack, modules 의 *.java -
  L42 선언과 RoutingNodesChangedObserver L59 구현만 있고 호출처가 0건이다)
 즉 현재 트리에서는 드러나지 않는다
```

## 쌓은 것을 꺼내는 방법

```text
 관측자는 쌓기만 하고 스스로 아무것도 반영하지 않는다
 꺼내는 자리는 RoutingAllocation 의 메서드 셋이다

 updateMetadataWithRoutingChanges   MRAL L143
      indexMetadataUpdater.applyChanges 뒤에
      resizeSourceIndexUpdater.applyChanges 를 이어 붙인다

 updateRestoreInfoWithRoutingChanges MRAL L152
      restoreInProgressUpdater.applyChanges

 routingNodesChanged                 MRAL L160
      nodesChangedObserver.isChanged

 셋 다 buildResultAndLogHealthChange 가 부른다 (ALSV L177, L182)
 - 다만 routingNodesChanged 는 이 흐름에서 안 쓰인다.
   그것을 보는 것은 executeWithRoutingAllocation 의 조기 반환이다 (ALSV L482)
```

## 결과가 쓰이는 곳

```text
 관측자에 쌓인 변경
      --> 메타데이터 갱신의 유일한 입력이다
      --> 라우팅 테이블은 따로 rebuild 된다. 두 길이 여기서 갈린다

 안 듣는 관측자
      --> 그 사건은 라우팅에만 남고 메타데이터에는 안 간다
      --> replica 재초기화가 그 예다

 배열 순서
      --> DelegatingRoutingChangesObserver 가 순서대로 부른다
      --> 서로 상태를 공유하지 않으므로 순서에 의존하지 않는다
          (각 구현이 자기 필드만 만지는 것을 보고 내가 판단한 것이다)
```

## 다루지 않는 것

`RoutingNodesChangedObserver` 의 assert 들, `ShardChangesObserver` 가 남기는 지표의 이름과 의미, `RestoreService.RestoreInProgressUpdater` 가 복원 상태를 바꾸는 규칙, `ResizeSourceIndexSettingsUpdater` 가 지우는 설정 키와 조건, 이 인터페이스를 쓰는 다른 흐름(`applyFailedShards`, `reroute`)에서 불리는 나머지 다섯 메서드는 같은 뼈대의 곁가지라 요약만 했다.
