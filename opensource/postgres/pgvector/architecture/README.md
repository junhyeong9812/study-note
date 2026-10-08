# pgvector 아키텍처 지도

소스를 **직접 읽어서** 그리는 탑다운 지도다. 흐름 다섯 편(함수 문서 42편)으로 되어 있다. pgvector 는 PostgreSQL 확장이라 서버 코드를 고치지 않고 SQL 로 타입·연산자·접근 메서드를 등록한 뒤, 접근 메서드 함수 포인터 자리에 자기 함수를 꽂는다. 그래서 이 지도는 "꽂히는 자리"(Index AM 인터페이스)와 "꽂힌 함수의 속"(HNSW 그래프, IVFFlat 클러스터)을 함께 본다.

기준 태그: `v0.8.7` [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/` 아래다. 짝이 되는 서버 쪽은 [PostgreSQL 아키텍처 지도](../../architecture/README.md)(`REL_18_6`)다.

연산자·인덱스 옵션·설정 변수 이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 상위: [pgvector](../README.md)

## 한 갈래로 읽는다

```text
 흐름  무엇이 일어나는가      5편, 함수 문서 42편
       요청 하나가 지나는 길을 함수 단위로 따라간다
       폴더 하나 = 함수 하나

 구조 편은 따로 두지 않았다. 소스가 작고 디스크 모양이 흐름과 붙어 있어서
 페이지와 튜플 배치는 흐름 문서 안에 그렸다
   값의 모양              [확장 로드와 vector 타입]
   HNSW 메타·원소·이웃 튜플  [HNSW 빌드] 09 FlushPages
   IVFFlat 메타·리스트·항목  [IVFFlat 빌드와 검색] 01, 04, 06
```

## 흐름 다섯 편

오른쪽 칸은 같은 문제를 [db-engine](https://github.com/junhyeong9812/db-engine)(직접 만든 교육용 DB 엔진)에서 다루는 챕터다. db-engine 에는 벡터 타입과 근사 최근접 인덱스가 없어서 모두 비어 있다.

| 흐름 | 진입점 | 문서 | db-engine 대응 |
|---|---|---|---|
| [확장 로드와 vector 타입](flows/vector-type/README.md) | `_PG_init` `src/vector.c` L58 | 7 | - |
| [거리 연산자와 Index AM 연결](flows/operators-index-am/README.md) | `hnswhandler` `src/hnsw.c` L267 | 8 | - |
| [HNSW 빌드](flows/hnsw-build/README.md) | `hnswbuild` `src/hnswbuild.c` L1151 | 9 | - |
| [HNSW 검색](flows/hnsw-search/README.md) | `hnswgettuple` `src/hnswscan.c` L194 | 9 | - |
| [IVFFlat 빌드와 검색](flows/ivfflat/README.md) | `ivfflatbuild` `src/ivfbuild.c` L1069 | 9 | - |

## 흐름이 이어지는 자리

```text
 등록과 값 - 무엇이 서버에 꽂히는가

 CREATE EXTENSION vector  (sql/vector.sql)
   CREATE TYPE vector ... / CREATE OPERATOR <-> <#> <=> <+> <~> <%>
   CREATE ACCESS METHOD hnsw, ivfflat / CREATE OPERATOR CLASS ...
      v
 [확장 로드와 vector 타입]   _PG_init -> SIMD 디스패치, HnswInit / IvfflatInit
      |  vector_in / vector_typmod_in -> 값과 차원(typmod)
      v
 [거리 연산자와 Index AM]    hnswhandler / ivfflathandler -> IndexAmRoutine
         amcanorderbyop = true : ORDER BY col <op> const 를 인덱스로
         지원 함수 1 거리, 2 정규화, 3.. 타입 정보 / k-means
```

```text
 HNSW - 그래프

 CREATE INDEX ... USING hnsw
   [HNSW 빌드]  hnswbuild
      |  행마다 층 뽑기 -> HnswFindElementNeighbors -> 양방향 연결 (메모리)
      |  메모리가 차면 FlushPages 후 디스크 삽입으로
      |  끝에 FlushPages -> log_newpage_range
      v
 블록 0 메타 (진입점) / 블록 1.. 원소 튜플 + 이웃 튜플
      ^
   [HNSW 검색]  hnswgettuple
         위층 ef = 1 -> 0층 ef = hnsw.ef_search -> 가까운 순으로 heaptid
         HnswSearchLayer 는 빌드와 검색이 같이 쓴다
```

```text
 IVFFlat - 클러스터

 CREATE INDEX ... USING ivfflat
   [IVFFlat 빌드와 검색]
      빌드  표본 -> k-means (lists 개 중심) -> 리스트 페이지 -> 행 배정, 정렬 -> 항목 페이지
      검색  모든 중심과 거리 -> 가까운 probes 개 리스트 -> 항목 전부 거리 -> 정렬
```

## PostgreSQL 지도와 만나는 자리

pgvector 의 함수는 서버의 같은 자리에서 불리고, 서버의 같은 함수로 페이지를 읽고 WAL 을 쓴다. 상위 지도에서 이어지는 문서는 다음과 같다.

```text
 Index AM 인터페이스
   index_insert -> rd_indam->aminsert           B-tree 는 btinsert
                                                pgvector 는 hnswinsert / ivfflatinsert
   상위 [nbtree 삽입과 분할] 02 index_insert

 버퍼
   새 페이지  ReadBufferExtended(P_NEW)          HnswNewBuffer, IvfflatNewBuffer
   읽기      ReadBuffer + LockBuffer(SHARE)      검색의 원소·이웃·리스트·항목 페이지
   IVFFlat 스캔은 BAS_BULKREAD 링 버퍼          ivfscan.c L321
   상위 [버퍼 관리] 01 ReadBufferExtended

 WAL (소스로 확인한 사용 방식)
   HNSW 빌드     페이지 쓰기마다 WAL 없음 -> 끝에 log_newpage_range   hnswbuild.c L1142
   HNSW INSERT   GenericXLogStart / RegisterBuffer / Finish            hnswinsert.c L194 등
   IVFFlat 빌드  새 페이지마다 GenericXLog (GENERIC_XLOG_FULL_IMAGE)    ivfutils.c L166
                 init fork 만 끝에 log_newpage_range                   ivfbuild.c L1060
   상위 [행 쓰기와 WAL 기록] 06 XLogInsert

 상위 지도에 없는 것
   인덱스 스캔 노드 (ExecIndexScan -> index_getnext_slot -> amgettuple)
   플래너의 인덱스 경로 선택 (amcanorderbyop, amcostestimate 를 읽는 쪽)
```

- [nbtree 삽입과 분할 / index_insert](../../architecture/flows/nbtree-insert/02_index_insert/README.md)
- [버퍼 관리 / ReadBufferExtended](../../architecture/flows/buffer-manager/01_ReadBufferExtended/README.md)
- [행 쓰기와 WAL 기록 / XLogInsert](../../architecture/flows/heap-insert-wal/06_XLogInsert/README.md)

## 읽는 순서

```text
 처음이면
   [확장 로드와 vector 타입] -> [거리 연산자와 Index AM 연결]

 HNSW 를 알고 싶으면
   [HNSW 빌드] (01 -> 05 -> 07 -> 09) -> [HNSW 검색] (03 -> 05 -> 07)
   HnswSearchLayer 는 검색 07 에 있고 빌드 07 이 그것을 부른다

 IVFFlat 을 알고 싶으면
   [IVFFlat 빌드와 검색] 01 -> 03 -> 06 -> 07 -> 09

 왜 결과가 근사인지, 행이 모자란지 궁금하면
   [HNSW 검색] 03 hnswgettuple (ef_search 와 반복 스캔) -> 09 ResumeScanItems
   [IVFFlat 빌드와 검색] 07 ivfflatgettuple (probes 와 max_probes)

 서버와 만나는 자리가 궁금하면
   [거리 연산자와 Index AM 연결] 01 -> 상위 [nbtree 삽입과 분할] 02 index_insert
```

## 흐름별 함수 문서

폴더 하나가 함수 하나다. 곁가지 함수는 가까운 함수 문서 안에서 함께 다룬다.

### [확장 로드와 vector 타입](flows/vector-type/README.md)

- [01__PG_init](flows/vector-type/01__PG_init/README.md)
- [02_vector_in](flows/vector-type/02_vector_in/README.md)
- [03_vector_typmod_in](flows/vector-type/03_vector_typmod_in/README.md)
- [04_vector](flows/vector-type/04_vector/README.md)
- [05_vector_out](flows/vector-type/05_vector_out/README.md)
- [06_vector_recv](flows/vector-type/06_vector_recv/README.md)
- [07_array_to_vector](flows/vector-type/07_array_to_vector/README.md)

### [거리 연산자와 Index AM 연결](flows/operators-index-am/README.md)

- [01_hnswhandler](flows/operators-index-am/01_hnswhandler/README.md)
- [02_ivfflathandler](flows/operators-index-am/02_ivfflathandler/README.md)
- [03_HnswInit](flows/operators-index-am/03_HnswInit/README.md)
- [04_hnswcostestimate](flows/operators-index-am/04_hnswcostestimate/README.md)
- [05_HnswInitSupport](flows/operators-index-am/05_HnswInitSupport/README.md)
- [06_HnswFormIndexValue](flows/operators-index-am/06_HnswFormIndexValue/README.md)
- [07_l2_distance](flows/operators-index-am/07_l2_distance/README.md)
- [08_cosine_distance](flows/operators-index-am/08_cosine_distance/README.md)

### [HNSW 빌드](flows/hnsw-build/README.md)

- [01_hnswbuild](flows/hnsw-build/01_hnswbuild/README.md)
- [02_InitBuildState](flows/hnsw-build/02_InitBuildState/README.md)
- [03_BuildGraph](flows/hnsw-build/03_BuildGraph/README.md)
- [04_InsertTuple](flows/hnsw-build/04_InsertTuple/README.md)
- [05_HnswInitElement](flows/hnsw-build/05_HnswInitElement/README.md)
- [06_InsertTupleInMemory](flows/hnsw-build/06_InsertTupleInMemory/README.md)
- [07_HnswFindElementNeighbors](flows/hnsw-build/07_HnswFindElementNeighbors/README.md)
- [08_UpdateGraphInMemory](flows/hnsw-build/08_UpdateGraphInMemory/README.md)
- [09_FlushPages](flows/hnsw-build/09_FlushPages/README.md)

### [HNSW 검색](flows/hnsw-search/README.md)

- [01_hnswbeginscan](flows/hnsw-search/01_hnswbeginscan/README.md)
- [02_hnswrescan](flows/hnsw-search/02_hnswrescan/README.md)
- [03_hnswgettuple](flows/hnsw-search/03_hnswgettuple/README.md)
- [04_GetScanValue](flows/hnsw-search/04_GetScanValue/README.md)
- [05_GetScanItems](flows/hnsw-search/05_GetScanItems/README.md)
- [06_HnswEntryCandidate](flows/hnsw-search/06_HnswEntryCandidate/README.md)
- [07_HnswSearchLayer](flows/hnsw-search/07_HnswSearchLayer/README.md)
- [08_HnswLoadUnvisitedFromDisk](flows/hnsw-search/08_HnswLoadUnvisitedFromDisk/README.md)
- [09_ResumeScanItems](flows/hnsw-search/09_ResumeScanItems/README.md)

### [IVFFlat 빌드와 검색](flows/ivfflat/README.md)

- [01_ivfflatbuild](flows/ivfflat/01_ivfflatbuild/README.md)
- [02_ComputeCenters](flows/ivfflat/02_ComputeCenters/README.md)
- [03_ElkanKmeans](flows/ivfflat/03_ElkanKmeans/README.md)
- [04_CreateListPages](flows/ivfflat/04_CreateListPages/README.md)
- [05_AddTupleToSort](flows/ivfflat/05_AddTupleToSort/README.md)
- [06_InsertTuples](flows/ivfflat/06_InsertTuples/README.md)
- [07_ivfflatgettuple](flows/ivfflat/07_ivfflatgettuple/README.md)
- [08_GetScanLists](flows/ivfflat/08_GetScanLists/README.md)
- [09_GetScanItems](flows/ivfflat/09_GetScanItems/README.md)

## 다루지 않는 것

INSERT 경로 본문(`hnswinsert`, `ivfflatinsert` — 빌드의 디스크 단계와 같은 알고리즘이라 요약만), VACUUM(`hnswvacuum.c`, `ivfvacuum.c` — 지운 원소의 이웃 재연결과 자리 재사용), 병렬 빌드의 세부, `halfvec`·`sparsevec`·`bit` 의 타입별 입출력과 SIMD 구현은 이 지도에서 다루지 않는다.
