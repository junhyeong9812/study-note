# API 역인덱스

상위: [Elasticsearch 아키텍처 지도](README.md)

"이 API 를 부르면 어느 흐름들을 지나는가"를 뒤에서부터 찾는 표다. 흐름 문서가 메서드에서 출발한다면 이 표는 **REST 엔드포인트에서 출발한다.**

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19).

## 범위를 먼저 밝힌다

```text
 REST 핸들러는 이 저장소에 461개 파일이 있다
   (범위: server/src/main, x-pack/plugin/*/src/main, modules/*/src/main
    패턴: extends BaseRestHandler 또는 implements RestHandler)
 server/src/main 만 해도 라우트 선언이 296개다

 이 표는 그것을 전부 담지 않는다
 **흐름 열 편이 실제로 덮는 길**만 적었다

 안 덮는 API 도 아래에 따로 적어 두었다 - 없는 것을 있는 척하지 않으려고
```

## 모든 HTTP 요청이 공유하는 앞단

```text
 HTTP 요청
   |
   v
 [REST 디스패치]   RestController.dispatchRequest
   |  핸들러를 찾고 인터셉터를 태운다
   v
 [트랜스포트 액션]  TransportAction.execute
   |  필터 체인을 태우고 필요하면 스레드를 갈아탄다
   v
 doExecute          여기서부터 API 마다 갈린다
```

## 문서 쓰기

| API | 핸들러 | 뒤이어 지나는 흐름 |
|---|---|---|
| `POST`/`PUT /{index}/_doc/{id}` | `RestIndexAction` | [문서 색인](flows/index-document/README.md) → [엔진 쓰기](flows/engine-write/README.md) |
| `POST`/`PUT /{index}/_create/{id}` | `RestIndexAction` | 〃 |
| `POST /{index}/_doc` | `RestIndexAction` | 〃 |
| `POST`/`PUT /_bulk` | `RestBulkAction` | 〃 |
| `POST`/`PUT /{index}/_bulk` | `RestBulkAction` | 〃 |
| `POST /{index}/_update/{id}` | `RestUpdateAction` | 〃 |
| `DELETE /{index}/_doc/{id}` | `RestDeleteAction` | 〃 |

```text
 단건도 bulk 로 간다

 RestIndexAction 은 client.index(...) 를 부르는데
 그 액션의 구현이 이렇다 (TransportIndexAction L33)

   public class TransportIndexAction extends TransportSingleItemBulkWriteAction<...>

 그리고 클래스 javadoc 이 L30 에 한 줄 적어 두었다
   "Deprecated use TransportBulkAction with a single item instead"

 즉 문서 하나짜리 요청도 bulk 로 감싸여 같은 길을 탄다
 [문서 색인] 흐름이 TransportShardBulkAction 에서 시작하는 이유다
```

```text
 새 필드를 만나면 갈래가 하나 더 생긴다

 [문서 색인]이 매핑에 없는 필드를 보면
   MappingUpdatePerformer.updateMappings 로 마스터에 요청한다
   -> "put-mapping" 큐 -> [클러스터 상태 갱신] -> [매핑 병합]
   -> 발행 -> 데이터 노드가 MapperService.updateMapping 으로 받는다
   -> 그러고 나서 색인을 다시 시도한다

 즉 쓰기 한 번이 마스터를 왕복할 수 있다
```

## 검색

| API | 핸들러 | 뒤이어 지나는 흐름 |
|---|---|---|
| `GET`/`POST /_search` | `RestSearchAction` | [검색 페이즈](flows/search-phases/README.md) → [페치 페이즈](flows/fetch-phase/README.md) |
| `GET`/`POST /{index}/_search` | `RestSearchAction` | 〃 |
| `GET`/`POST /_msearch` | `RestMultiSearchAction` | 〃 |
| `GET`/`POST /{index}/_msearch` | `RestMultiSearchAction` | 〃 |
| `GET`/`POST /_count` | `RestCountAction` | 〃 |
| `GET`/`POST /{index}/_count` | `RestCountAction` | 〃 |

```text
 _count 도 검색 흐름이다

 RestCountAction 이 부르는 것은 client.search(...) 다
 별도의 count 경로가 아니라 size 0 짜리 검색이다

 그리고 검색은 TransportSearchAction 에서 갈린다
   L2275  new SearchQueryThenFetchAsyncAction(...)
 그것이 AbstractSearchAsyncAction 을 상속하므로 [검색 페이즈]로 들어간다
```

## 매핑과 인덱스

| API | 핸들러 | 뒤이어 지나는 흐름 |
|---|---|---|
| `PUT`/`POST /{index}/_mapping` | `RestPutMappingAction` | [클러스터 상태 갱신](flows/cluster-state/README.md) → [매핑 병합](flows/mapping-merge/README.md) |
| `PUT`/`POST /{index}/_mappings` | `RestPutMappingAction` | 〃 |

```text
 매핑 갱신이 마스터 큐에 들어가는 자리

 RestPutMappingAction
   -> TransportPutMappingAction L184  metadataMappingService.putMapping(...)
   -> MetadataMappingService L276     taskQueue.submitTask(...)

 그 큐의 정체는 생성자에 있다 (MetadataMappingService L84-88)
   clusterService.createTaskQueue("put-mapping", <우선순위 설정>, new PutMappingExecutor(...))

 그리고 PutMappingExecutor 는 ClusterStateTaskExecutor 다 (L130)

 즉 [매핑 병합]은 독립된 길이 아니라
 [클러스터 상태 갱신]의 실행기로 들어가 도는 흐름이다
```

## REST 진입점이 없는 흐름 셋

```text
 [노드 기동]       bin/elasticsearch 가 JVM 을 띄우는 것이 시작이다
                   HTTP 이전의 이야기다

 [샤드 시작 반영]  데이터 노드가 내부 트랜스포트로 마스터에 알린다
                   ShardStateAction 이 "shard-started" 큐에 넣는다 (L314, URGENT)
                   역시 [클러스터 상태 갱신]의 실행기다

 [엔진 쓰기]       [문서 색인] 안쪽이라 밖에서 직접 들어올 길이 없다
```

```text
 그래서 흐름 열 편의 실제 모양이 이렇다

 REST 로 들어오는 것      rest-dispatch, transport-action,
                          index-document, search-phases,
                          mapping-merge(마스터 큐를 거쳐)

 다른 흐름 안쪽           engine-write, fetch-phase

 마스터 큐의 실행기        mapping-merge, shard-allocation

 HTTP 밖                   node-bootstrap
```

## 이 지도가 덮지 않는 API

없는 것을 있는 척하지 않으려고 적어 둔다. 아래는 흐름 문서가 **없는** 길이다.

| API | 핸들러 | 왜 안 덮나 |
|---|---|---|
| `GET`/`HEAD /{index}/_doc/{id}` | `RestGetAction` | `TransportGetAction` 은 `TransportSingleShardAction` 계보다. 흐름 문서가 없다 |
| `GET`/`HEAD /{index}/_source/{id}` | `RestGetSourceAction` | 〃 |
| `GET`/`POST /_mget` | `RestMultiGetAction` | 〃 |
| `GET`/`POST /{index}/_termvectors` | `RestTermVectorsAction` | 〃 |
| `GET`/`POST /_mtermvectors` | `RestMultiTermVectorsAction` | 〃 |
| `GET`/`POST /{index}/_explain/{id}` | `RestExplainAction` | 단일 샤드 경로다 |
| `GET`/`POST /_search/scroll` | `RestSearchScrollAction` | 스크롤은 페이즈 체인과 다른 경로다 |
| `GET /_mapping`, `GET /{index}/_mapping` | `RestGetMappingAction` | 읽기 전용이라 병합 흐름을 안 탄다 |
| `GET /_cluster/health` | `RestClusterHealthAction` | 상태를 읽기만 한다 |
| `GET /_cluster/state` | `RestClusterStateAction` | 〃 |
| `POST /_cluster/reroute` | `RestClusterRerouteAction` | 실제 할당 결정은 [샤드 시작 반영]의 범위 밖이다 |
| `PUT /{index}` | `RestCreateIndexAction` | 인덱스 생성은 `MetadataCreateIndexService` 쪽이다 |

```text
 위 표에서 "흐름 문서가 없다"는 말의 뜻

 그 API 가 [REST 디스패치]와 [트랜스포트 액션]까지는 확실히 지난다
 갈라지는 것은 doExecute 뒤부터다

 그 뒤를 이 지도가 안 그렸다는 뜻이지
 그 길이 없다는 뜻이 아니다
```

## 다루지 않는 것

x-pack 과 modules 의 핸들러 전부(합쳐서 461개 파일 중 대부분), `_cat` API 군, ingest pipeline, ILM 과 데이터 스트림, 스냅샷·복원, 보안과 인증 관련 엔드포인트, `_nodes`·`_tasks` 같은 진단 API 는 이 역인덱스의 범위 밖이다. 라우트 추출은 각 핸들러의 `routes()` 선언에서 기계적으로 뽑았고, 액션 연결은 핸들러가 부르는 클라이언트 메서드와 그 트랜스포트 액션의 상속 관계로 확인했다.
