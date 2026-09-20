# IndexMetadataUpdater.updateInSyncAllocations

상위: [샤드 시작 반영](../README.md)

샤드 하나의 in-sync 집합을 계산한다. 백 줄인데 **절반이 "이 집합이 비면 안 된다"를 지키는 장치**다. 비는 순간 다음 할당이 빈 primary 를 만들어 버리기 때문이다.

## 위치

`IndexMetadataUpdater.java` `server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L172-L273 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L172-L273))

## 실제 코드

보통 경로는 더하고 빼는 것부터다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L219-L223 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L219-L223))

```java
// IndexMetadataUpdater.java L221-L223
            Set<String> inSyncAllocationIds = new HashSet<>(oldInSyncAllocationIds);
            inSyncAllocationIds.addAll(updates.addedAllocationIds);
            inSyncAllocationIds.removeAll(updates.removedAllocationIds);
```

무한히 커지는 것을 막는다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L229-L241 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L229-L241))

```java
// IndexMetadataUpdater.java L229-L234
            // Prevent set of inSyncAllocationIds to grow unboundedly. This can happen for example if we don't write to a primary
            // but repeatedly shut down nodes that have active replicas.
            // We use number_of_replicas + 1 (= possible active shard copies) to bound the inSyncAllocationIds set
            // Only trim the set of allocation ids when it grows, otherwise we might trim too eagerly when the number
            // of replicas was decreased while shards were unassigned.
            int maxActiveShards = oldIndexMetadata.getNumberOfReplicas() + 1; // +1 for the primary
```

> Prevent set of inSyncAllocationIds to grow unboundedly. This can happen for example if we don't write to a primary but repeatedly shut down nodes that have active replicas.

> We use number_of_replicas + 1 (= possible active shard copies) to bound the inSyncAllocationIds set

> Only trim the set of allocation ids when it grows, otherwise we might trim too eagerly when the number of replicas was decreased while shards were unassigned.

자를 때는 라우팅 항목이 있는 것을 살린다.

```java
// IndexMetadataUpdater.java L250-L253
                inSyncAllocationIds = inSyncAllocationIds.stream()
                    .sorted(Comparator.comparing(assignedAllocations::contains).reversed()) // values with routing entries first
                    .limit(maxActiveShards)
                    .collect(Collectors.toSet());
```

실패한 primary 는 되살린다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `IndexMetadataUpdater.java` L256-L262 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/IndexMetadataUpdater.java#L256-L262))

```java
// IndexMetadataUpdater.java L259-L262
            if (newShardRoutingTable.activeShards().isEmpty() && updates.firstFailedPrimary != null) {
                // add back allocation id of failed primary
                inSyncAllocationIds.add(updates.firstFailedPrimary.allocationId().getId());
            }
```

> only remove allocation id of failed active primary if there is at least one active shard remaining. Assume for example that the primary fails but there is no new primary to fail over to. If we were to remove the allocation id of the primary from the in-sync set, this could create an empty primary on the next allocation.

마지막 안전장치가 하나 더 있다.

```java
// IndexMetadataUpdater.java L267-L270
            // be extra safe here and only update in-sync set if it is non-empty
            if (inSyncAllocationIds.isEmpty() == false) {
                updatedIndexMetadata = updatedIndexMetadata.withInSyncAllocationIds(shardId.id(), inSyncAllocationIds);
            }
```

## 동작 흐름

```text
 L188  강제 초기화인가
         initializedPrimary 가 있고
         기존 in-sync 가 비어 있지 않은데
         그 primary 의 id 가 기존 in-sync 에 없다

   예 (빈 primary 또는 stale primary 강제 할당)
     L199  빈 primary 면 => in-sync 를 빈 집합으로 (L201)
     L202  stale primary 면
       L205  FORCE_STALE 이면 가짜 id 하나짜리 집합 + timestamp 범위에서 그 샤드 제거
       L211  아니면 그 primary 의 실제 id 하나짜리 집합
       L217  둘 다 Set.of(allocationId) 로 덮는다

   아니오 (보통 경로)
     L221  기존 집합 복사 -> added 더하기 -> removed 빼기
     L234  maxActiveShards = **기존** IndexMetadata 의 복제본 수 + 1
             갱신 중인 쪽이 아니라 oldIndexMetadata 를 본다
     L241  커졌고 **그리고** 한도를 넘었으면 자른다
     L259  라우팅에 활성 샤드가 없고 실패한 primary 가 있으면 그 id 를 되넣는다
     L268  결과가 비지 않았을 때만 갱신한다
 L272  return updatedIndexMetadata
```

```text
 "비면 안 된다"를 지키는 장치가 넷이다

 1. L241 의 조건이 둘 다여야 한다
      inSyncAllocationIds.size() > oldInSyncAllocationIds.size()
      && inSyncAllocationIds.size() > maxActiveShards
    커졌을 때만 자른다. 주석 L232-233 이 이유를 적어 두었다 -
    복제본 수를 줄인 동안 샤드가 unassigned 였으면 너무 일찍 잘릴 수 있다

 2. L250 의 정렬
      라우팅 항목이 있는 id 를 앞으로 보내고 limit 한다
      즉 실제로 존재하는 사본을 먼저 살린다

 3. L259 의 되넣기
      최종 라우팅에 활성 샤드가 하나도 없으면
      방금 실패한 primary 의 id 를 도로 넣는다

 4. L268 의 최종 확인
      결과가 비었으면 아예 갱신하지 않는다
      주석 L267: "be extra safe here and only update in-sync set if it is non-empty"

 넷 다 같은 사고를 막는다 - 빈 in-sync 는 다음 할당에서 빈 primary 를 만든다
```

```text
 L250 의 정렬 표현이 뒤집혀 있다

 .sorted(Comparator.comparing(assignedAllocations::contains).reversed())

 Boolean 오름차순은 false 가 앞이므로
 reversed() 를 붙여야 true(라우팅 항목이 있는 것)가 앞으로 온다

 주석도 그렇게 적혀 있다 (L251)
   "values with routing entries first"
```

```text
 강제 할당 갈래는 이 흐름에서 안 온다

 L188 의 조건에 initializedPrimary 가 필요하다
 그것을 채우는 것은 shardInitialized 다 (L64)

 그런데 이 흐름은 이미 초기화된 샤드를 **시작**시킨다
 초기화 자체는 reroute 쪽에서 일어난다

 그래서 applyStartedShards 만 돈 라운드에서는 보통 경로로 간다
 (L196 의 assert 도 그 가정을 적는다 -
  "primary is not force-initialized in same allocation round where shards are started")
```

```text
 L241 과 L259 가 최종 라우팅 테이블을 본다

 newShardRoutingTable = newRoutingTable.shardRoutingTable(shardId)   L235

 그래서 buildResultAndLogHealthChange 가
 L176 에서 테이블을 먼저 만들고 L177 에서 이것을 부른다

 순서를 바꾸면 자를 대상과 되살릴 조건을 잘못 판정한다
 (주석은 없다. 두 사용처와 호출 순서를 맞춰 보고 내가 판단한 것이다)
```

## 결과가 쓰이는 곳

```text
 갱신된 IndexMetadata
      --> applyChanges 가 다음 샤드로 누적해 간다 (IMU L131)
      --> 마지막에 버전이 올라가 상태에 실린다

 in-sync 집합
      --> 복제 쓰기가 이 집합을 대상으로 한다
      --> 다음 할당에서 어느 사본이 primary 가 될 수 있는지 정한다
      --> 비면 빈 primary 가 만들어진다. 그래서 장치가 넷이다

 바뀐 게 없으면
      --> 받은 updatedIndexMetadata 를 그대로 돌려준다
      --> 호출자의 참조 비교(L151)가 그것을 보고 버전을 안 올린다
```

## 다루지 않는 것

`RecoverySource` 의 종류별 의미(`EMPTY_STORE`, `FORCE_STALE_PRIMARY_INSTANCE`, `SnapshotRecoverySource`)와 강제 할당 명령(`AllocateEmptyPrimaryAllocationCommand`, `AllocateStalePrimaryAllocationCommand`), `isStatelessIndexRecovery` 가 stateless 배치를 판정하는 기준, `IndexLongFieldRange.removeShard` 의 timestamp 범위 조정, `IndexShardRoutingTable` 의 `activeShards` / `assignedShards` 계산은 같은 뼈대의 곁가지라 요약만 했다.
