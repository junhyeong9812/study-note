# 샤드 모델

인덱스가 어떻게 쪼개지고, 그 조각이 어느 노드에 어떤 자격으로 놓이는가. `PUT /my-index/_doc/1` 의 `1` 이 **어느 샤드로 가는지**가 여기서 정해진다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 인덱스 my-index (샤드 3개, 레플리카 1개)
 |
 +-- 샤드 0   프라이머리 @ node-A      레플리카 @ node-B
 +-- 샤드 1   프라이머리 @ node-B      레플리카 @ node-C
 +-- 샤드 2   프라이머리 @ node-C      레플리카 @ node-A

 "레플리카 1개" 는 복제본이 1개 더 있다는 뜻이다
 샤드 하나당 총 2벌 (프라이머리 1 + 레플리카 1)

 같은 샤드의 복제본들은 같은 노드에 놓이지 않는다
 그래야 노드 하나가 죽어도 그 샤드가 살아남는다
 (SameShardAllocationDecider L128-140 이 같은 shardId 에만 NO 를 낸다)
```

```text
 문서가 샤드로 가는 계산 (가장 단순한 경로)

 IndexRouting L398
   routingFunction.shardNum(effectiveRoutingToHash(routing == null ? id : routing))

 effectiveRoutingToHash L240-242
   Murmur3HashFunction.hash(문자열)

 ModuloRoutingFunction L26-31
   Math.floorMod(hash, numberOfShards)

 즉 murmur3(_id) 를 샤드 수로 나눈 나머지다
 routing 파라미터를 주면 _id 대신 그 값을 해싱한다
```

```text
 다만 이 경로가 유일하지는 않다

 해싱 함수가 둘이다 (RoutingFunction 은 sealed, 구현 2종)
   IndexRouting L68-72 가 인덱스 생성 버전으로 고른다
   신규   ModuloRoutingFunction   floorMod(hash, numberOfShards)
   구버전 LegacyRoutingFunction   floorMod(hash, routingNumShards) / routingFactor

 무엇을 해싱할지도 넷으로 갈린다 (IndexRouting.create L85-101)
   ForIndexDimensions  TSDB - 문서의 차원 필드
   ForRoutingPath      routing_path 설정 - 지정한 필드
   Partitioned         routing_partition_size - _id 와 routing 을 함께
   Unpartitioned       위 도식의 기본 경로

 구버전 함수가 해싱 공간(routingNumShards)과 실제 샤드 수를 분리한 것은
 샤드 수를 나중에 바꿀 수 있게 하려는 장치다

 그래서 샤드 수는 그 자리에서 바꿀 수 없고
 바꾸려면 문서를 다시 배치하는 별도 연산이 필요하다 (_split, _shrink, 리샤딩)
```

```text
 샤드 복제본 하나의 상태 (ShardRoutingState L23-46, 상수 선언부만)

 UNASSIGNED    아직 어느 노드에도 배정되지 않았다
 INITIALIZING  배정됐고 데이터를 받아 오는 중이다
 STARTED       정상 동작 중. 읽기와 쓰기를 받는다
 RELOCATING    다른 노드로 옮겨 가는 중이다

 ShardRouting.active() 는 STARTED 이거나 RELOCATING 인 경우다 (L348)
```

```text
 노드 역할과 프라이머리/레플리카 구분은 다른 축이다

 노드 역할        설정으로 정한다. 그 노드가 샤드를 가질 수 있는가
 프라이머리 구분  클러스터 상태가 정한다. 이 복제본이 주인가 사본인가

 참고로 소스의 ShardRouting.Role 은 또 다른 축이다
 DEFAULT / INDEX_ONLY / SEARCH_ONLY 세 값이고 (L1133-1136)
 프라이머리 여부가 아니라 승격 가능 여부와 검색 대상 여부를 가른다

 같은 노드가 어떤 샤드의 프라이머리이면서
 다른 샤드의 레플리카일 수 있다 (위 그림의 node-A, node-B, node-C 가 그렇다)

 그래서 [디스크 배치](../disk-layout/README.md)의 경로에는
 프라이머리 여부가 나타나지 않는다. 경로는 샤드 번호까지만 안다
```

## 실제 코드

문서를 샤드 번호로 바꾸는 계산이다.

`server` / `org.elasticsearch.cluster.routing` / `IndexRouting.java` L240-L242 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/IndexRouting.java#L240-L242))

```java
// IndexRouting.java L240-L242
    private static int effectiveRoutingToHash(String effectiveRouting) {
        return Murmur3HashFunction.hash(effectiveRouting);
    }
```

`server` / `org.elasticsearch.cluster.routing` / `RoutingFunction.java` L26-L31 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/RoutingFunction.java#L26-L31))

```java
// RoutingFunction.java L26-L31
    record ModuloRoutingFunction(int numberOfShards) implements RoutingFunction {
        @Override
        public int shardNum(int hash) {
            return Math.floorMod(hash, numberOfShards);
        }
    }
```

복제본 하나가 가질 수 있는 상태.

`server` / `org.elasticsearch.cluster.routing` / `ShardRoutingState.java` L15-L46 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/ShardRoutingState.java#L15-L46))

```java
// ShardRoutingState.java L23-L46 (javadoc 생략)
    UNASSIGNED((byte) 1),

    INITIALIZING((byte) 2),

    STARTED((byte) 3),

    RELOCATING((byte) 4);
```

한 샤드의 복제본들을 묶어 프라이머리와 레플리카를 구분하는 곳.

`server` / `org.elasticsearch.cluster.routing` / `IndexShardRoutingTable.java` L550-L556 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/routing/IndexShardRoutingTable.java#L550-L556))

```java
// IndexShardRoutingTable.java L550-L556
    public ShardRouting primaryShard() {
        return primary;
    }

    public List<ShardRouting> replicaShards() {
        return this.replicas;
    }
```

## 어디에서 쓰이는가

```text
 [디스크 배치] 샤드 번호가 그대로 디렉터리 이름이 된다
 [노드 역할] canContainData 인 노드에만 샤드를 배정한다
 [클러스터 상태] 어느 복제본이 어느 노드에 있는지는 라우팅 테이블에 있다
 [쓰기 복제] 프라이머리가 먼저 쓰고 레플리카가 따라온다
```

디스크에 놓이는 모양은 [디스크 배치](../disk-layout/README.md), 노드 쪽 조건은 [노드 역할](../node-roles/README.md), 쓰기가 복제되는 순서는 [쓰기 복제](../write-replication/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 계산된 샤드 번호
      --> 코디네이터 노드가 이것으로 어느 노드에 보낼지 정한다
      --> routing 을 주지 않고 라우팅 전략이 같으면
          같은 _id 는 같은 샤드로 간다

 routing 파라미터
      --> _id 대신 다른 값으로 해싱한다
      --> 같은 사용자의 문서를 한 샤드에 모으는 식으로 쓴다
      --> 대신 그 샤드가 커지는 쏠림이 생길 수 있다

 읽기 대상을 고르는 이터레이터
      --> activeInitializingShardsIt 이 고른다 (L230-237)
      --> active(STARTED 와 RELOCATING)를 섞어 앞에 두고
          INITIALIZING 복제본을 맨 뒤에 붙인다
      --> 즉 INITIALIZING 도 빠지지는 않는다. 순서가 맨 뒤일 뿐이다

 프라이머리가 죽은 경우
      --> 승격 가능한(promotable) active 레플리카가 있으면
          마스터가 그중 하나를 승격시킨다 (RoutingNodes L407-416)
      --> 없으면 그 샤드는 UNASSIGNED 가 된다
      --> 그 결정도 클러스터 상태 변경으로 이루어진다
```

## 다루지 않는 것

샤드 분할(`_split`)과 축소(`_shrink`)의 실제 동작, `routing_partition_size` 를 쓰는 부분 라우팅의 계산, 리샤딩 중의 라우팅 전환, 데이터 스트림의 백킹 인덱스 구조, 샤드 크기 권장치와 개수 설계, `IndexShardRoutingTable` 의 선호 노드 선택(preference)은 같은 뼈대의 곁가지라 요약만 했다. 샤드를 실제로 배치하는 알고리즘도 별도 주제다.
