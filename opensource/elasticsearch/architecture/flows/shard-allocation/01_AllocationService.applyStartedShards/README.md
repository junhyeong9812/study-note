# AllocationService.applyStartedShards

상위: [샤드 시작 반영](../README.md)

진입점이다. 스무 줄인데 **호출자에게 요구하는 조건이 javadoc 에 셋** 적혀 있고, 정렬 한 줄이 이 흐름의 가장 미묘한 부분을 막고 있다.

## 위치

`server` / `org.elasticsearch.cluster.routing.allocation` / `AllocationService.java` L147-L173 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/AllocationService.java#L147-L173))

## 실제 코드

javadoc 이 계약을 말한다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `AllocationService.java` L147-L152 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/AllocationService.java#L147-L152))

> Applies the started shards. Note, only initializing ShardRouting instances that exist in the routing table should be provided as parameter and no duplicates should be contained.

> If the same instance of the ClusterState is returned, then no change has been made.

빈 목록이면 그대로 돌려준다.

```java
// AllocationService.java L155-L157
        if (startedShards.isEmpty()) {
            return clusterState;
        }
```

가변 사본을 만들고 정렬한다.

`server` / `org.elasticsearch.cluster.routing.allocation` / `AllocationService.java` L158-L162 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/AllocationService.java#L158-L162))

```java
// AllocationService.java L158-L162
        RoutingAllocation allocation = createMutableRoutingAllocation(clusterState, currentNanoTime());
        // as starting a primary relocation target can reinitialize replica shards, start replicas first
        startedShards = new ArrayList<>(startedShards);
        startedShards.sort(Comparator.comparing(ShardRouting::primary));
        applyStartedShards(allocation, startedShards);
```

그리고 할당기들에게 알린다.

```java
// AllocationService.java L163-L165
        for (final ExistingShardsAllocator allocator : existingShardsAllocators.values()) {
            allocator.applyStartedShards(startedShards, allocation);
        }
```

## 동작 흐름

```text
 L154  assert assertInitialized()
 L155  startedShards 가 비면 => clusterState 를 그대로 돌려준다
 L158  allocation = createMutableRoutingAllocation(clusterState, currentNanoTime())
 L160  목록을 ArrayList 로 복사한다
 L161  ShardRouting::primary 로 정렬한다
 L162  applyStartedShards(allocation, startedShards)      사설 판 L757
 L163  existingShardsAllocators 를 순회하며 알린다
 L166  assert RoutingNodes.assertShardStats(...)
 L167  로그용 문자열을 만든다 (디버그가 켜져 있으면 전체)
 L172  buildResultAndLogHealthChange(clusterState, allocation, reason)
```

```text
 L161 의 정렬이 막는 것

 주석이 이유를 적어 두었다 (L159)
   "as starting a primary relocation target can reinitialize replica shards,
    start replicas first"

 Comparator.comparing(ShardRouting::primary) 이고
 boolean 은 Boolean 으로 박싱돼 compareTo 를 탄다
 false 가 true 보다 작으므로 replica(primary=false)가 앞에 온다

 primary 를 먼저 시작하면 그 자리에서 replica 들이 재초기화되고
 그 뒤에 그 replica 를 시작시키려 하면 이미 다른 객체가 돼 있다
 L764 의 동일성 assert 가 그것을 잡는다
```

```text
 호출자가 목록을 미리 손질한다

 ShardStartedTaskExecutor 가 배치로 모은 태스크를 거른다
   L138  초기화 중이 아니면 제외한다
   L150  이미 본 것이면 제외한다
           주석 L149: "remove duplicate actions as allocation service expects
                       a clean list without duplicates"

 즉 javadoc 의 세 조건(초기화 중 / 라우팅 테이블에 존재 / 중복 없음)을
 호출자 쪽에서 맞춰 준다

 이쪽은 assert 로만 확인한다 (L761-768)
 assert 는 -ea 없이는 안 돈다
```

```text
 L163-165 는 상태를 바꾸지 않는다

 등록돼서 이 루프를 도는 구현은 셋이고 전부 캐시 정리다
   GatewayAllocator L99-104            비동기 페치를 맵에서 빼고 close 한다
   SearchableSnapshotAllocator L358    맵에서 뺀다 (닫지는 않는다)
   StatelessExistingShardsAllocator    빈 몸통

 같은 인터페이스의 구현이 하나 더 있지만 이 루프에는 안 온다
   AllocationService 내부 NotFoundAllocator L962  빈 몸통
   설정된 할당기 이름이 등록돼 있지 않을 때 L900 이 즉석에서 만든다
   existingShardsAllocators 맵에는 안 들어간다

 샤드가 시작됐으니 그 샤드의 페치 결과가 쓸모없어진 것이다
 결과 ClusterState 에는 영향이 없다
 (주석은 없다. 구현을 모두 읽고 등록 경로를 확인해 내가 판단한 것이다)
```

```text
 이 메서드에는 try/catch 가 없다

 예외는 전부 호출자로 올라간다 (SSTE L237-242)
 거기서 태스크를 전부 실패 처리하고 initialState 를 그대로 쓴다

 그리고 L160 이 호출자의 리스트를 복사한다
   startedShards = new ArrayList<>(startedShards);
 파라미터 변수를 재대입하므로 L164 의 할당기들도 정렬된 복사본을 받는다
 호출자가 넘긴 리스트 자체는 안 바뀐다
```

```text
 로그 문자열은 열 개에서 끊는다

 firstListElementsToCommaDelimitedString(L415-429)
 디버그가 꺼져 있으면 앞의 열 개만 찍고
 ", ... [N items in total]" 를 붙인다 (L424-427)

 L170 이 logger.isDebugEnabled() 를 넘기는 것이 그 스위치다
```

```text
 사설 applyStartedShards 는 얇은 고리다 (L757-774)

 L758  assert 목록이 비어 있지 않다
 L760  샤드마다
 L761    assert 초기화 중이다
 L762    assert 인덱스가 메타데이터에 있다
 L764    assert 라우팅 테이블의 **그 객체와 동일하다** (== 비교)
 L769    expectedShardSize 를 고른다
 L772    routingNodes.startShard(startedShard, allocation.changes(), expectedShardSize)

 실제 일은 전부 startShard 가 한다
```

`server` / `org.elasticsearch.cluster.routing.allocation` / `AllocationService.java` L769-L772 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/allocation/AllocationService.java#L769-L772))

```java
// AllocationService.java L769-L772
            long expectedShardSize = routingAllocation.metadata().indexMetadata(startedShard.index()).isSearchableSnapshot()
                ? startedShard.getExpectedShardSize()
                : ShardRouting.UNAVAILABLE_EXPECTED_SHARD_SIZE;
            routingNodes.startShard(startedShard, routingAllocation.changes(), expectedShardSize);
```

```text
 expectedShardSize 는 대부분 버린다

 searchable snapshot 인덱스일 때만 실제 값을 넘기고
 아니면 UNAVAILABLE_EXPECTED_SHARD_SIZE 다

 searchable snapshot 은 원격 저장소에서 읽으므로
 로컬 디스크 사용량 예측이 다르게 필요한 것으로 보인다
 (주석이 없어 이유는 확인하지 못했다)
```

## 결과가 쓰이는 곳

```text
 가변 RoutingAllocation
      --> startShard 가 그 안의 RoutingNodes 를 직접 고친다
      --> 관측자들이 변경을 쌓는다
      --> buildResultAndLogHealthChange 가 둘 다 읽는다

 돌려준 ClusterState
      --> 호출자가 timestamp 범위를 더해 다시 만든다 (SSTE L215-229)
      --> 그 뒤 발행된다

 예외가 났을 때
      --> 호출자가 initialState 를 그대로 쓰고 태스크를 전부 실패 처리한다 (SSTE L237)
```

## 다루지 않는 것

`createMutableRoutingAllocation` 이 만드는 `MutableRoutingAllocation` 의 나머지 기능(시뮬레이션 모드, reconciling 플래그), `assertInitialized` 와 `assertShardStats` 가 검사하는 내용, `ExistingShardsAllocator` 의 나머지 메서드(`allocateUnassigned`, `beforeAllocation`)와 비동기 페치 구조, `firstListElementsToCommaDelimitedString` 의 문자열 생성은 같은 뼈대의 곁가지라 요약만 했다.
