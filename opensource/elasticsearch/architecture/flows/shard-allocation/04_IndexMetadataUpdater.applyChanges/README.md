# IndexMetadataUpdater.applyChanges

상위: [샤드 시작 반영](../README.md)

관측자가 라운드 내내 쌓아 둔 것을 **한꺼번에 메타데이터로 환산한다.** 쌓는 쪽이 메서드 넷, 환산하는 쪽이 이 메서드 하나다.

## 위치

`IndexMetadataUpdater.java` `server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L113-L158 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L113-L158))

## 실제 코드

클래스 javadoc 이 범위를 말한다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L40-L45 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L40-L45))

> Observer that tracks changes made to RoutingNodes in order to update the primary terms and in-sync allocation ids in IndexMetadata once the allocation round has completed.

> Primary terms are updated on primary initialization or when an active primary fails.

> Allocation ids are added for shards that become active and removed for shards that stop being active.

쌓는 그릇은 샤드별 `Updates` 다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L373-L379 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L373-L379))

```java
// IndexMetadataUpdater.java L373-L379
    private static class Updates {
        private boolean increaseTerm; // whether primary term should be increased
        private Set<String> addedAllocationIds = new HashSet<>(); // allocation ids that should be added to the in-sync set
        private Set<String> removedAllocationIds = new HashSet<>(); // allocation ids that should be removed from the in-sync set
        private ShardRouting initializedPrimary = null; // primary that was initialized from unassigned
        private ShardRouting firstFailedPrimary = null; // first active primary that was failed
    }
```

샤드가 시작되면 이렇게 쌓인다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L69-L85 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L69-L85))

```java
// IndexMetadataUpdater.java L76-L84
        if (startedShard.isPromotableToPrimary()) {
            Updates updates = changes(startedShard.shardId());
            updates.addedAllocationIds.add(startedShard.allocationId().getId());
            if (startedShard.primary()
                // started shard has to have null recoverySource; have to pick up recoverySource from its initializing state
                && (initializingShard.recoverySource() == RecoverySource.ExistingStoreRecoverySource.FORCE_STALE_PRIMARY_INSTANCE)) {
                updates.removedAllocationIds.add(RecoverySource.ExistingStoreRecoverySource.FORCED_ALLOCATION_ID);
            }
        }
```

환산은 인덱스와 프로젝트로 묶는 것부터다.

```java
// IndexMetadataUpdater.java L114-L121
        final Map<Index, List<Map.Entry<ShardId, Updates>>> changesGroupedByIndex = shardChanges.entrySet()
            .stream()
            .collect(Collectors.groupingBy(e -> e.getKey().getIndex()));

        final Map<ProjectMetadata, List<Index>> indicesByProject = changesGroupedByIndex.keySet()
            .stream()
            .collect(Collectors.groupingBy(oldMetadata::projectFor));
        final Metadata.Builder updatedMetadata = Metadata.builder(oldMetadata);
```

그리고 바뀐 인덱스만 담는다.

```java
// IndexMetadataUpdater.java L151-L153
                if (updatedIndexMetadata != oldIndexMetadata) {
                    updatedIndices.put(updatedIndexMetadata.getIndex().getName(), updatedIndexMetadata.withIncrementedVersion());
                }
```

## 동작 흐름

```text
 쌓는 쪽 (관측자 메서드 넷)

 shardInitialized    L51   primary 면 term++ 하고 initializedPrimary 를 적는다
 shardStarted        L69   승격 가능하면 addedAllocationIds 에 넣는다
 shardFailed         L88   활성 primary 면 firstFailedPrimary 를 적고 term++
 relocationCompleted L100  removeAllocationId 로 removedAllocationIds 에 넣는다

 환산하는 쪽

 L114  shardChanges 를 인덱스별로 묶는다
 L118  인덱스를 프로젝트별로 묶는다
 L122  프로젝트마다
 L128    그 인덱스의 샤드마다
 L131      updateInSyncAllocations(...)
 L142      increaseTerm 이면 primary term 을 올린다
 L151    바뀐 인덱스만 withIncrementedVersion() 해서 담는다
 L155    withAllocationAndTermUpdatesOnly(updatedIndices)
 L157  return updatedMetadata.build()
```

```text
 관측자 열 개 중 넷만 받는다

 RoutingChangesObserver 의 메서드는 열 개다
 IndexMetadataUpdater 가 덮어쓴 것은 넷이다

 안 받는 것 중에 이 흐름에서 실제로 불리는 것이 둘 있다
   relocationStarted                  RNOD L534
   initializedReplicaReinitialized    RNOD L597

 즉 **replica 재초기화는 in-sync 집합을 바꾸지 않는다**
 라우팅 테이블만 바뀌고 메타데이터는 그대로다
 (주석은 없다. 덮어쓴 메서드 목록과 호출 지점을 맞춰 보고 내가 판단한 것이다)
```

```text
 shardStarted 의 조건이 둘이다 (L76-84)

 L76  if (startedShard.isPromotableToPrimary())
        승격 불가능한(검색 전용) 복제본은 in-sync 에 안 들어간다

 L79  primary 이고 복구원이 FORCE_STALE_PRIMARY_INSTANCE 였으면
 L82    가짜 id(FORCED_ALLOCATION_ID)를 removed 에 넣는다

 두 번째는 주석이 사정을 말한다 (L80)
   "started shard has to have null recoverySource;
    have to pick up recoverySource from its initializing state"

 시작된 샤드는 복구원을 잃으므로
 초기화 중이던 쪽에서 읽어야 한다는 뜻이다
```

```text
 Updates 는 필드 다섯짜리 그릇이다 (L373-379)

 increaseTerm          primary term 을 올릴지
 addedAllocationIds    in-sync 에 넣을 id 들
 removedAllocationIds  in-sync 에서 뺄 id 들
 initializedPrimary    unassigned 에서 초기화된 primary
 firstFailedPrimary    처음 실패한 활성 primary

 샤드 하나당 하나이고 computeIfAbsent 로 만든다 (L353-355)
 그래서 아무 일도 없던 샤드에는 항목 자체가 없다
```

```text
 primary term 을 올리는 방식이 둘이다 (L142-149)

 보통    withIncrementedPrimaryTerm(shardId)          L148
 분할 중  withSetPrimaryTerm(shardId, splitPrimaryTerm) L144

 후자는 resharding 분할의 대상 샤드일 때다 (조건 셋이 다 맞아야 한다, L138-141)

 splitPrimaryTerm(L160-167)의 실제 식은 이렇다
   Math.max(원본 샤드의 primaryTerm,
            이 샤드의 primaryTerm + 1)

 주석은 "max of the source and target primary terms" 라고만 말한다 (L161-162)
   "We take the max of the source and target primary terms. This guarantees that
    the target primary term stays greater than or equal to the source."
 코드는 대상 쪽에 +1 을 한다. 주석이 그 +1 을 말하지 않는다
```

```text
 그런데 이 흐름에서는 primary term 이 안 올라간다

 increaseTerm 을 세우는 곳은 둘뿐이다
   shardInitialized  L54
   shardFailed       L95

 그런데 startShard 는 shardInitialized 를 아예 안 부른다
 (그것을 부르는 것은 initializeShard 이고 reroute 쪽 경로다)

 shardFailed 는 부르지만(RNOD L583) 대상이 초기화 중인 replica 라
 L89 의 active() && primary() 조건에 걸린다

 즉 applyStartedShards 만 돈 라운드에서는 term 이 그대로다
 (주석은 없다. 두 호출처와 조건을 맞춰 보고 내가 판단한 것이다)
```

```text
 버전은 바뀐 것만 올라간다 (L151-153)

 if (updatedIndexMetadata != oldIndexMetadata) {
     updatedIndices.put(..., updatedIndexMetadata.withIncrementedVersion());
 }

 여기도 참조 비교다
 updateInSyncAllocations 가 바꿀 게 없으면 받은 것을 그대로 돌려주기 때문이다

 그리고 한 겹 더 있다
 withInSyncAllocationIds 도 집합이 그대로면 this 를 돌려준다 (IndexMetadata L905-907)

 그래서 shardChanges 에 항목이 있어도 버전이 안 오를 수 있다
 이미 in-sync 에 있는 id 를 다시 더한 경우가 그렇다
```

```text
 Metadata 버전은 여기서 안 올라간다

 Metadata.Builder(Metadata) 가 version 을 그대로 복사하고
 build() 도 그대로 넘긴다

 올라가는 것은 IndexMetadata 버전뿐이다 (L152)
 Metadata 와 ClusterState 의 버전은 발행 단계에서 붙는다
```

## 결과가 쓰이는 곳

```text
 새 Metadata
      --> buildResultAndLogHealthChange 가 ClusterState 에 넣는다 (ALSV L180)
      --> 그 전에 resizeSourceIndexUpdater 가 한 번 더 손댄다 (MRAL L145)

 in-sync allocation ids
      --> 복제 쓰기의 대상 집합이다
      --> 다음 할당에서 어느 사본이 primary 가 될 수 있는지도 정한다

 primary term
      --> 오래된 primary 가 보낸 요청을 거르는 기준이다

 IndexMetadata 버전
      --> 바뀐 인덱스만 올라가므로 안 바뀐 인덱스는 재전송에서 빠진다
```

## 다루지 않는 것

`ProjectMetadata.withAllocationAndTermUpdatesOnly` 가 무엇을 제한하는지, `IndexMetadata.withInSyncAllocationIds` / `withIncrementedPrimaryTerm` / `withTimestampRanges` 의 구현, `IndexReshardingMetadata` 의 분할 상태 관리, `removeStaleIdsWithoutRoutings`(같은 클래스의 static 메서드지만 실패 처리 경로다)의 사정은 같은 뼈대의 곁가지라 요약만 했다. in-sync 집합 계산은 [updateInSyncAllocations](../05_IndexMetadataUpdater.updateInSyncAllocations/README.md)에 있다.
