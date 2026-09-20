# 샤드 시작 반영

상위: [Elasticsearch 아키텍처 지도](../../README.md)

데이터 노드가 "샤드를 다 열었다"고 알려 왔을 때 마스터가 **그것을 클러스터 상태에 반영하기까지**다. 이름과 달리 **여기서 할당을 하지는 않는다** — 재할당은 새 상태가 발행된 뒤 별도 reroute 가 한다.

전 구간이 마스터의 단일 스레드에서 동기로 돈다. 대신 구조가 특이하다. 라우팅 테이블은 **제자리에서 고치고**, 메타데이터 변경은 **관측자에 쌓았다가 마지막에 한꺼번에 환산한다**. 폴더 하나가 메서드 하나이고, [spi](spi/README.md)에 관측자 계약표가 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 줄 번호는 파일마다 다르므로 각 절에 파일을 밝혔다.

## 전체 그림

```text
 ~~> 데이터 노드가 마스터 태스크 큐에 넣는다
     실행 스레드는 masterService#updateTask 하나다

 ShardStartedTaskExecutor.execute                     SSTE L213
      중복을 걸러 깨끗한 목록을 만든 뒤 한 번 부른다

 [01] AllocationService.applyStartedShards            ALSV L153
      +-- 빈 목록이면 => 같은 인스턴스를 그대로 돌려준다    L155
      +-- 가변 RoutingAllocation 을 만든다                  L158
      +-- replica 가 먼저 오도록 정렬한다                    L161
      +-- 사설 applyStartedShards                           L162 -> L757
      |     +-- [02] RoutingNodes.startShard               RNOD L549
      +-- ExistingShardsAllocator 들에게 알린다             L163-165
      |     (캐시 정리일 뿐 상태를 안 바꾼다)
      +-- [03] buildResultAndLogHealthChange                L172 -> L175
            +-- 라우팅 테이블을 다시 만든다                  L176
            +-- [04] IndexMetadataUpdater.applyChanges      L177 -> IMU L113
            +-- 복원 상태를 갱신한다                         L182
            +-- 새 ClusterState 를 만든다                    L190
            +-- 헬스가 바뀌었으면 로그를 찍는다               L192

 ~~> 발행 후 clusterStatePublished 가 별도 reroute 를 건다  SSTE L292
```

```text
 두 가지 변경이 서로 다른 길로 간다

 라우팅 테이블   제자리에서 고친다
                 ClusterState.mutableRoutingNodes() 가 사본을 준다
                 startShard 가 그 사본을 직접 바꾼다
                 마지막에 rebuild 로 테이블을 다시 만든다      ALSV L176

 메타데이터      쌓았다가 환산한다
                 startShard 가 관측자를 부른다                 RNOD L556 등
                 IndexMetadataUpdater 가 Updates 에 적어 둔다
                 applyChanges 가 그것을 IndexMetadata 로 바꾼다 IMU L113

 왜 나뉘는가 - 메타데이터 갱신이 **최종 라우팅 테이블을 알아야** 하기 때문이다
 in-sync 집합을 자를 때 "라우팅 항목이 있는 것"을 우선하고(IMU L250)
 실패한 primary 를 되살릴지도 최종 활성 샤드 수를 보고 정한다(IMU L259)
 (주석은 없다. applyChanges 가 newRoutingTable 을 인자로 받는 것과
  그 두 사용처를 보고 내가 판단한 것이다)
```

```text
 입력은 건드리지 않는다

 L158  createMutableRoutingAllocation(clusterState, ...)
         ClusterState.mutableRoutingNodes() 가 사본을 만든다

 바뀌는 것은 그 사본과 관측자들이고
 원래 ClusterState 객체는 그대로다

 그래서 예외가 나면 호출자가 initialState 를 그대로 쓴다 (SSTE L211, L237)
```

```text
 같은 인스턴스가 나오는 길은 하나뿐이다

 javadoc 이 계약을 말한다 (ALSV L151)
   "If the same instance of the ClusterState is returned, then no change has been made."

 실제로 그런 경로는 L155-157(빈 목록) 하나다
 ClusterState.Builder.build() 는 언제나 새 객체를 만들기 때문이다
 (ClusterState L1209 이하. 라우팅과 노드가 같으면 routingNodes 캐시만 재사용한다)
```

```text
 꼬리를 여럿이 공유한다

 buildResultAndLogHealthChange 의 호출처가 여섯이다 (ALSV)
   L172  applyStartedShards          <- 이 흐름
   L295  applyFailedShards
   L308  disassociateDeadNodes
   L449  reroute(commands)
   L485  executeWithRoutingAllocation
   L716  rerouteWithResetFailedCounter

 즉 [03] 이하는 이 흐름 전용이 아니다
 할당 결과를 상태로 굳히는 공통 출구다
```

## 어디에서 쓰이는가

```text
 [구조: 클러스터 상태] 결과가 상태로 발행돼 모든 노드에 퍼진다
      --> 데이터 노드는 그것을 받아 자기 샤드를 맞춘다

 [문서 색인] in-sync 집합이 복제 성공 판정의 기준이다
      --> 여기서 갱신된 집합이 다음 쓰기의 대상을 정한다

 [노드 기동] 복구로 연 샤드도 결국 이 경로로 STARTED 가 된다
```

시작된 샤드가 클러스터 상태에 실려 퍼지는 쪽은 [노드 기동](../node-bootstrap/README.md)에 일부 있다.

## 단계

1. [applyStartedShards](01_AllocationService.applyStartedShards/README.md)가 진입점이고 정렬과 뒷정리를 맡는다.
2. [RoutingNodes.startShard](02_RoutingNodes.startShard/README.md)가 실제로 샤드를 옮기고 연쇄를 일으킨다.
3. [buildResultAndLogHealthChange](03_AllocationService.buildResultAndLogHealthChange/README.md)가 결과를 상태로 굳힌다.
4. [IndexMetadataUpdater.applyChanges](04_IndexMetadataUpdater.applyChanges/README.md)가 쌓인 변경을 메타데이터로 바꾼다.
5. [updateInSyncAllocations](05_IndexMetadataUpdater.updateInSyncAllocations/README.md)가 in-sync 집합을 계산한다.

## 결과가 쓰이는 곳

```text
 새 ClusterState
      --> 호출자가 timestamp 범위를 더한 뒤 발행한다 (SSTE L215-229)
      --> 발행 후 clusterStatePublished 가 reroute 를 건다 (SSTE L292)

 in-sync allocation ids
      --> 복제 쓰기의 대상 집합이다
      --> 비면 안 되므로 여러 겹의 안전장치가 걸려 있다

 primary term
      --> 이 흐름에서는 **안 올라간다**
      --> 올리는 것은 primary 초기화와 활성 primary 실패뿐인데 (IMU L54, L95)
          둘 다 이 경로에서 일어나지 않는다

 IndexMetadata 버전
      --> 바뀐 인덱스만 올라간다 (IMU L152)
      --> in-sync 집합이 결과적으로 같으면 안 올라간다

 Metadata·ClusterState 버전
      --> 여기서는 안 바뀐다. 발행 단계에서 붙는다
```

## 다루지 않는 것

실제 할당 결정(`reroute`, `ShardsAllocator`, `AllocationDeciders`), 샤드 실패 처리(`applyFailedShards`)와 죽은 노드 정리(`disassociateDeadNodes`), `GlobalRoutingTable.rebuild` 가 라우팅 테이블을 다시 만드는 과정, `RestoreInProgressUpdater` 와 `ResizeSourceIndexSettingsUpdater` 의 갱신 내용, 데이터 노드가 시작 요청을 보내는 경로(`ShardStateAction`), 클러스터 상태 발행 자체는 같은 뼈대의 곁가지라 요약만 했다. 관측자 계약은 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 applyStartedShards](01_AllocationService.applyStartedShards/README.md)
- [02 RoutingNodes.startShard](02_RoutingNodes.startShard/README.md)
- [03 buildResultAndLogHealthChange](03_AllocationService.buildResultAndLogHealthChange/README.md)
- [04 IndexMetadataUpdater.applyChanges](04_IndexMetadataUpdater.applyChanges/README.md)
- [05 updateInSyncAllocations](05_IndexMetadataUpdater.updateInSyncAllocations/README.md)
- [spi](spi/README.md) — 관측자 계약표
