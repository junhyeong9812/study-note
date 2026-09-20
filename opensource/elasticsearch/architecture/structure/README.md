# 구조

호출 흐름이 아니라 **구조**를 다루는 문서 묶음이다. 흐름 문서가 "요청 하나가 어떤 메서드를 거치는가"를 따라간다면, 여기는 "그 요청이 닿는 대상이 어떻게 생겼는가"를 그린다. 클러스터가 어떻게 나뉘고, 데이터가 어디에 놓이고, 언제부터 안전한가.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 PUT /my-index/_doc/1  하나가 닿는 구조들

 [노드 역할]      요청을 받은 노드가 무엇을 할 수 있는가
      |           역할은 설정이 정하고 클러스터 상태에 실린다
      v
 [클러스터 상태]  어떤 인덱스가 있고 샤드가 어디 있는가
      |           마스터만 바꾸고 모든 노드가 사본을 든다
      v
 [샤드 모델]      _id 가 어느 샤드로 가는가
      |           murmur3(_id) 를 샤드 수로 나눈 나머지
      v
 [쓰기 복제]      프라이머리가 먼저, 레플리카가 뒤따른다
      |           순번을 프라이머리가 매겨 결과가 갈라지지 않는다
      v
 [지속성]         언제부터 검색되고 언제부터 안전한가
      |           refresh 와 flush 는 다른 축이다
      v
 [디스크 배치]    결국 어느 파일로 놓이는가
                  ${path.data}/indices/{uuid}/{shard}/{index,translog,_state}
```

```text
 읽는 순서

 위에서 아래가 요청이 닿는 순서다
 다만 이해 순서는 반대로 가도 좋다

 디스크 배치부터 읽으면   "결국 파일이 어떻게 생겼나"가 먼저 잡히고
 노드 역할부터 읽으면     "누가 무엇을 하나"가 먼저 잡힌다

 [클러스터 상태]는 나머지 다섯 개가 전부 참조하는 축이다
 어느 쪽에서 시작하든 여기는 한 번 거치게 된다
```

## 문서

| 문서 | 중심 클래스 | 내용 |
|------|-------------|------|
| [노드 역할](node-roles/README.md) | `DiscoveryNodeRole` | 내장 역할 14종, `canContainData`, "마스터-슬레이브"가 아닌 이유 |
| [클러스터 상태](cluster-state/README.md) | `ClusterState` | 필드 아홉 개, 마스터만 버전을 올린다, (term, version) 으로 최신을 판정한다 |
| [샤드 모델](shard-model/README.md) | `IndexRouting` | `floorMod(murmur3(_id), 샤드수)`, 해싱 전략 네 갈래, 복제본 상태 4종 |
| [쓰기 복제](write-replication/README.md) | `ReplicationOperation` | 프라이머리 우선, 프라이머리의 fsync 는 레플리카 왕복과 병렬 |
| [지속성](durability/README.md) | `Translog.Durability` | 버퍼 -> translog -> fsync -> refresh -> flush, 검색과 안전은 다른 축 |
| [디스크 배치](disk-layout/README.md) | `NodeEnvironment` | UUID 기반 경로, `_state` 가 세 층위에서 반복된다 |

## 다루지 않는 것

마스터 선출과 정족수, 피어 복구와 스냅샷 복구, 샤드 할당 알고리즘(`DesiredBalance`), 세그먼트 머지 정책, 검색 단계(query/fetch)의 분산 실행, 스테이트리스 구성은 각 문서의 "다루지 않는 것"에 적어 두었다. 이 묶음은 구조만 다루고, 실제 호출 경로는 흐름 문서의 몫이다.
