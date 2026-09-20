# Elasticsearch 아키텍처 지도

소스를 **직접 읽어서** 그린 탑다운 지도다. 구조 여섯 편과 흐름 열 편, 모두 85개 문서로 되어 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 두 갈래로 읽는다

```text
 구조  무엇이 있는가          6편
       샤드·노드 역할·디스크 배치처럼 자리에 관한 것

 흐름  무엇이 일어나는가      10편, 78개 문서
       요청 하나가 지나는 길을 메서드 단위로 따라간다
       폴더 하나 = 메서드 하나
```

## 흐름 열 편

| 흐름 | 진입점 | 문서 |
|---|---|---|
| [REST 디스패치](flows/rest-dispatch/README.md) | `RestController.dispatchRequest` L425 | 9 |
| [트랜스포트 액션](flows/transport-action/README.md) | `TransportAction.execute` L51 | 6 |
| [문서 색인](flows/index-document/README.md) | `TransportShardBulkAction.doExecuteShardOperationOnPrimary` L194 | 8 |
| [엔진 쓰기](flows/engine-write/README.md) | `InternalEngine.index` L1262 | 7 |
| [검색 페이즈](flows/search-phases/README.md) | `AbstractSearchAsyncAction.start` L232 | 10 |
| [페치 페이즈](flows/fetch-phase/README.md) | `FetchSearchPhase.run` L78 | 7 |
| [매핑 병합](flows/mapping-merge/README.md) | `MapperService.merge` L426 | 9 |
| [샤드 시작 반영](flows/shard-allocation/README.md) | `AllocationService.applyStartedShards` L153 | 7 |
| [클러스터 상태 갱신](flows/cluster-state/README.md) | `BatchingTaskQueue.submitTask` L1873 | 8 |
| [노드 기동](flows/node-bootstrap/README.md) | `Elasticsearch.main` L95 | 7 |

## 흐름이 이어지는 자리

```text
 데이터 노드 쪽 - 요청 하나가 지나는 길

 [노드 기동]  먼저 이것이 끝나 있어야 한다

 [REST 디스패치]
      | action.accept
      v
 [트랜스포트 액션]
      | doExecute
      +----------------------------+
      v                            v
 [문서 색인]                  [검색 페이즈]
      | applyIndexOperationOnPrimary   | 페이즈 전이
      v                            v
 [엔진 쓰기]                  [페치 페이즈]
```

```text
 마스터 쪽 - 상태를 바꾸는 길

 [클러스터 상태 갱신]이 바탕이고
 다른 둘이 그 안에서 도는 실행기다

   "put-mapping"    큐   -> [매핑 병합]의 마스터 쪽
                          MetadataMappingService L84-88
                          PutMappingExecutor implements ClusterStateTaskExecutor (L130)

   "shard-started"  큐   -> [샤드 시작 반영]
                          ShardStateAction L314, Priority.URGENT

 즉 흐름 둘은 독립된 길이 아니라 흐름 열의 **안쪽**이다
```

```text
 두 쪽이 만나는 자리

 [문서 색인]이 새 필드를 만나면
   MappingUpdatePerformer.updateMappings 로 마스터에 요청한다
   그것이 "put-mapping" 큐에 들어가 [매핑 병합]이 된다
   병합 결과가 발행되면 데이터 노드가 MapperService.updateMapping 으로 받는다

 [샤드 시작 반영]이 끝나 상태가 발행되면
   clusterStatePublished 가 별도 reroute 를 건다 ([클러스터 상태 갱신] L509)
```

## 구조 여섯 편

| 문서 | 다루는 것 |
|---|---|
| [샤드 모델](structure/shard-model/README.md) | 인덱스가 샤드로 쪼개지고 복제되는 단위 |
| [노드 역할](structure/node-roles/README.md) | 노드가 맡는 역할과 그에 따른 차이 |
| [디스크 배치](structure/disk-layout/README.md) | 데이터 디렉토리의 구조와 잠금 |
| [클러스터 상태](structure/cluster-state/README.md) | 상태 객체가 담는 것과 퍼지는 방식 |
| [쓰기 복제](structure/write-replication/README.md) | 프라이머리와 복제본 사이의 규약 |
| [지속성](structure/durability/README.md) | translog 와 flush 가 보장하는 것 |

## 읽는 순서

```text
 처음이면
   [구조: 샤드 모델] -> [구조: 노드 역할] 로 자리를 잡고
   [REST 디스패치] -> [트랜스포트 액션] 으로 길의 시작을 본다

 쓰기를 알고 싶으면
   [문서 색인] -> [엔진 쓰기] -> [구조: 지속성]

 읽기를 알고 싶으면
   [검색 페이즈] -> [페치 페이즈]

 마스터가 궁금하면
   [클러스터 상태 갱신] 을 먼저 보고
   그 안에서 도는 [샤드 시작 반영] 과 [매핑 병합] 을 본다
```

## 문서의 생김새

```text
 흐름 폴더마다

 README        그 흐름의 전체 그림과 하위 메서드 목록
 NN_클래스.메서드  메서드 하나
 spi           그 흐름의 계약 - 인터페이스, 상태표, 순서 제약

 메서드 문서는 이 차례다

 상위 링크 -> 한 문장 요약 -> 위치 -> 실제 코드
 -> 동작 흐름(아스키) -> 결과가 쓰이는 곳 -> 다루지 않는 것
```

```text
 아스키 그림의 표기

 +--   직접 호출 (호출한 스레드가 그대로 이어서 실행한다)
 ~~>   콜백이나 큐 경계 (여기서 스레드가 갈린다)
 =>    그 갈래를 끝낸다

 인용은 소스 주석 원문이고
 그 아래 한국어 설명은 원문이 이유를 말하지 않을 때 붙인 것이다
 그 구분을 문장 안에 밝혀 두었다
```

## 다루지 않는 것

`Coordinator` 의 합의와 발행 프로토콜, `ClusterApplierService` 의 상태 적용, 스냅샷과 복원, ILM 과 데이터 스트림, 집계와 쿼리 실행의 Lucene 쪽, 플러그인 확장점, x-pack 의 보안·머신러닝, 트랜스포트 계층의 직렬화와 연결 관리는 이 지도의 범위 밖이다. 각 문서의 "다루지 않는 것" 절에 그 흐름에서 생략한 곁가지를 따로 적어 두었다.
