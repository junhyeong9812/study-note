# AllocationService.buildResultAndLogHealthChange

상위: [샤드 시작 반영](../README.md)

**할당 결과를 클러스터 상태로 굳히는 공통 출구다.** 이 흐름 전용이 아니라 호출처가 여섯이다. 스무 줄 안에서 라우팅 테이블을 다시 만들고, 쌓인 변경을 메타데이터로 환산하고, 헬스를 두 번 계산한다.

## 위치

`server` / `org.elasticsearch.cluster.routing.allocation` / `AllocationService.java` L175-L195 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/AllocationService.java#L175-L195))

## 실제 코드

라우팅 테이블과 메타데이터를 만든다.

```java
// AllocationService.java L176-L178
        final GlobalRoutingTable newRoutingTable = oldState.globalRoutingTable().rebuild(allocation.routingNodes(), allocation.metadata());
        final Metadata newMetadata = allocation.updateMetadataWithRoutingChanges(newRoutingTable);
        assert newRoutingTable.validate(newMetadata); // validates the routing table is coherent with the cluster state metadata
```

상태를 조립한다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `AllocationService.java` L180-L190 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/AllocationService.java#L180-L190))

```java
// AllocationService.java L180-L190
        final ClusterState.Builder newStateBuilder = ClusterState.builder(oldState).routingTable(newRoutingTable).metadata(newMetadata);
        final RestoreInProgress restoreInProgress = RestoreInProgress.get(allocation.getClusterState());
        RestoreInProgress updatedRestoreInProgress = allocation.updateRestoreInfoWithRoutingChanges(restoreInProgress);
        if (updatedRestoreInProgress != restoreInProgress) {
            ImmutableOpenMap.Builder<String, ClusterState.Custom> customsBuilder = ImmutableOpenMap.builder(
                allocation.getClusterState().getCustoms()
            );
            customsBuilder.put(RestoreInProgress.TYPE, updatedRestoreInProgress);
            newStateBuilder.customs(customsBuilder.build());
        }
        final ClusterState newState = newStateBuilder.build();
```

그리고 헬스 변화를 찍는다.

```java
// AllocationService.java L192-L194
        logClusterHealthStateChange(oldState, newState, reason);

        return newState;
```

## 동작 흐름

```text
 L176  newRoutingTable = oldState.globalRoutingTable()
                            .rebuild(allocation.routingNodes(), allocation.metadata())
 L177  newMetadata = allocation.updateMetadataWithRoutingChanges(newRoutingTable)
 L178  assert newRoutingTable.validate(newMetadata)
 L180  ClusterState.builder(oldState).routingTable(...).metadata(...)
 L181  기존 RestoreInProgress 를 꺼낸다
 L182  updatedRestoreInProgress = allocation.updateRestoreInfoWithRoutingChanges(...)
 L183  객체가 달라졌으면
 L187    customs 에 갈아 끼운다
 L190  newState = build()
 L192  logClusterHealthStateChange(oldState, newState, reason)
 L194  return newState
```

```text
 L176 과 L177 의 순서가 중요하다

 먼저 라우팅 테이블을 만들고
 그 결과를 메타데이터 갱신에 **인자로 넘긴다**

 메타데이터 쪽이 최종 라우팅을 알아야 하기 때문이다
   in-sync 집합을 자를 때 라우팅 항목이 있는 것을 앞에 둔다 (IMU L250)
   실패한 primary 를 되살릴지 최종 활성 샤드 수로 정한다 (IMU L259)

 (주석은 없다. applyChanges 의 시그니처와 그 두 사용처를 보고 내가 판단한 것이다)
```

```text
 updateMetadataWithRoutingChanges 는 둘을 잇는다

 MutableRoutingAllocation L142-146
   Metadata metadata = indexMetadataUpdater.applyChanges(metadata(), newRoutingTable);
   return resizeSourceIndexUpdater.applyChanges(metadata, newRoutingTable);

 즉 관측자 둘이 차례로 메타데이터를 고친다
 앞엣것이 in-sync 와 primary term, 뒤엣것이 resize 원본 설정이다
```

`server` / `org.elasticsearch.cluster.routing.allocation` / `MutableRoutingAllocation.java` L142-L146 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/MutableRoutingAllocation.java#L142-L146))

```java
// MutableRoutingAllocation.java L143-L146
    public Metadata updateMetadataWithRoutingChanges(GlobalRoutingTable newRoutingTable) {
        Metadata metadata = indexMetadataUpdater.applyChanges(metadata(), newRoutingTable);
        return resizeSourceIndexUpdater.applyChanges(metadata, newRoutingTable);
    }
```

```text
 복원 상태는 참조 비교로 판정한다

 L183  if (updatedRestoreInProgress != restoreInProgress)

 == 이 아니라 != 로 **객체 동일성**을 본다
 갱신기가 바뀐 게 없으면 같은 객체를 돌려준다는 뜻이다
 (RestoreInProgressUpdater 는 열지 않아 그 규약은 확인하지 못했다)
```

```text
 헬스를 매번 두 번 센다

 L535  previousHealth = getHealthStatus(previousState)
 L536  currentHealth  = getHealthStatus(newState)
 L538  다를 때만 info 로 찍는다

 getHealthStatus(L549-583)는 프로젝트 x 인덱스 x 샤드를 순회한다
 즉 할당 라운드마다 클러스터 전체를 두 번 훑는다

 빠른 탈출이 둘 있다
   L550  SERVICE_UNAVAILABLE 전역 블록이면 즉시 RED
   L562  인덱스의 모든 샤드가 활성이면 그 인덱스를 통째로 건너뛴다

 (비용에 대한 주석은 없다. 두 호출과 본문을 보고 내가 판단한 것이다)
```

```text
 rebuild 는 프로젝트마다 조건부로 갈아 끼운다

 GlobalRoutingTable.rebuild L53-87 이 세 곳에서 샤드를 모은다
   노드 위의 샤드       L56-65
   unassigned 샤드      L66-68
   ignored 샤드         L69-71

 그리고 만든 결과를 옛것과 비교해 다를 때만 넣는다 (L79-84)
 주석이 이유를 적어 두었다 (L80-82)
   "Only use the replacement routing table if it is different - this causes diffs
    to be smaller. This is necessary because RoutingTable instances with the same
    state are not considered "equal" (unless they are the same instance)."

 이동 중인 샤드는 항목이 둘이라 대상 쪽을 건너뛴다
   주석 L59-62: "every relocating shard has a double entry, ignore the target one."
```

```text
 버전과 UUID 는 여기서 안 바뀐다

 ClusterState.builder(oldState) 가 version 과 stateUUID 를 복사하고
 build() 는 uuid 가 UNKNOWN_UUID 일 때만 새로 만든다

 즉 이 메서드가 돌려주는 상태는 옛 상태와 같은 version·stateUUID 를 가진다
 올리는 것은 MasterService 가 발행하면서 한다

 그래서 "새 객체지만 아직 새 버전은 아니다"
```

```text
 L178 의 assert 안에서 예외가 난다

 newRoutingTable.validate(newMetadata) 는 boolean 을 돌려주는 게 아니라
 맞지 않으면 IllegalStateException 을 던진다 (GlobalRoutingTable L267-290)
   프로젝트 개수가 안 맞거나
   라우팅에만 있는 프로젝트가 있으면

 assert 가 꺼져 있으면 아예 안 돌고
 켜져 있으면 AssertionError 가 아니라 그 예외가 올라간다
```

```text
 같은 인스턴스는 여기서 절대 안 나온다

 L190  newStateBuilder.build()

 ClusterState.Builder.build() 는 언제나 새 객체를 만든다 (ClusterState L1209 이하)
 이전 상태와 라우팅·노드가 같으면 routingNodes 캐시만 재사용한다

 그래서 applyStartedShards 의 "같은 인스턴스" 계약을 만족시키는 길은
 이 메서드에 들어오기 전에 돌아가는 것뿐이다 (ALSV L155-157)
```

## 결과가 쓰이는 곳

```text
 새 ClusterState
      --> 호출자가 그대로 돌려주거나 더 손본다
      --> 이 흐름에서는 SSTE 가 timestamp 범위를 더한다

 헬스 로그
      --> 상태가 바뀔 때만 info 로 나간다
      --> reason 문자열이 어느 호출처에서 왔는지 알려 준다

 갱신된 RestoreInProgress
      --> customs 에 실려 복원 진행 상황이 따라온다
```

## 다루지 않는 것

`GlobalRoutingTable.rebuild` 가 변경된 `RoutingNodes` 로부터 라우팅 테이블을 다시 만드는 방식, `newRoutingTable.validate` 가 검사하는 정합성 조건, `ResizeSourceIndexSettingsUpdater` 와 `RestoreService.RestoreInProgressUpdater` 의 갱신 규칙, `ClusterState.Builder` 의 나머지 조립, `getInactivePrimaryHealth` 가 비활성 primary 를 등급으로 바꾸는 기준은 같은 뼈대의 곁가지라 요약만 했다. 메타데이터 환산은 [applyChanges](../04_IndexMetadataUpdater.applyChanges/README.md)에 있다.
