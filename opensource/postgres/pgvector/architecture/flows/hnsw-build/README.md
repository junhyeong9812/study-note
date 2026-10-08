# HNSW 빌드

상위: [pgvector 아키텍처 지도](../../README.md)

`CREATE INDEX ... USING hnsw (embedding vector_l2_ops)` 하나가 **힙의 모든 행을 읽어 여러 층의 근접 그래프를 메모리에 짓고, 그 그래프를 인덱스 페이지에 옮겨 적기까지**의 흐름이다. 빌드는 두 단계다(hnswbuild.c 머리 주석 L1-L36). 먼저 `maintenance_work_mem` 안에서 그래프 전체를 메모리에 짓고, 다 지으면 한 번에 페이지로 쏟아 낸다(`FlushPages`). 도중에 메모리가 모자라면 그 순간까지의 그래프를 쏟아 낸 뒤, 남은 행은 일반 `INSERT` 와 같은 디스크 삽입 경로로 하나씩 넣는다. 원소 하나를 넣는 알고리즘은 HNSW 논문의 Algorithm 1 이다. 무작위로 층을 정하고, 맨 위 진입점에서 그 층까지는 가장 가까운 하나만 따라 내려오고, 그 층부터 0층까지는 층마다 `ef_construction` 개 후보를 모아 그중 이웃을 고른 뒤, 이웃들의 이웃 목록에도 자기를 넣는다. 빌드 중의 페이지 쓰기는 WAL 을 남기지 않고, 끝에 인덱스 전체를 `log_newpage_range` 로 한 번에 기록한다.

기준 태그: v0.8.7 [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/` 아래다.

## 전체 그림

```text
 index_build -> amroutine->ambuild
 [01] hnswbuild                               hnswbuild.c   L1151
      +-- BuildIndex                                        L1130
      |   +-- [02] InitBuildState                            L686
      |   |     m, ef_construction, dimensions = atttypmod
      |   |     ml = 1/ln(m), maxLevel, memoryTotal = maintenance_work_mem
      |   +-- [03] BuildGraph                                L1091
      |   |     +-- 병렬이면 HnswBeginParallel (공유 메모리에 그래프)  L1104
      |   |     +-- table_index_build_scan(..., BuildCallback)   L1112
      |   |     |     행마다
      |   |     |     [04] InsertTuple                        L485
      |   |     |       +-- HnswFormIndexValue, HnswCheckDim     L500, L504
      |   |     |       +-- 이미 flush 됐으면 -> HnswInsertTupleOnDisk (디스크 단계)
      |   |     |       +-- 메모리 부족이면 NOTICE + FlushPages -> 디스크 단계
      |   |     |       +-- [05] HnswInitElement   층 뽑기       hnswutils.c L245
      |   |     |       +-- [06] InsertTupleInMemory              L437
      |   |     |             +-- entryLock (진입점을 바꿀 원소면 배타)
      |   |     |             +-- [07] HnswFindElementNeighbors  hnswutils.c L1283
      |   |     |             |     위층: HnswSearchLayer(ef = 1)    --> [HNSW 검색] 07
      |   |     |             |     아래층: HnswSearchLayer(ef = ef_construction)
      |   |     |             |             SelectNeighbors(lm)
      |   |     |             +-- [08] UpdateGraphInMemory          L413
      |   |     |                   중복 값이면 heaptid 만 붙이고 끝
      |   |     |                   원소 목록에 연결, 이웃들의 목록 갱신, 진입점 갱신
      |   |     +-- 다 넣었고 아직 flush 전이면 [09] FlushPages       L1119
      |   |           CreateMetaPage -> CreateGraphPages -> WriteNeighborTuples
      |   +-- RelationNeedsWAL 이면 log_newpage_range(0 .. 끝)        L1142
      +-- IndexBuildResult(heap_tuples, index_tuples)
```

그래프는 층마다 이웃 수 상한이 다르다. 0층은 `2m`, 그 위는 `m` 이다(`HnswGetLayerM`, hnsw.h L127). 원소의 층은 `-ln(U) * ml` 로 뽑으므로 `m = 16` 이면 층이 하나 오를 때마다 원소 수가 대략 1/16 로 준다.

```text
 m = 16 인 그래프의 층 (원소 N 개)

 층 2   o-----------o                         약 N/256   이웃 <= 16
        |           |
 층 1   o---o---o---o---o                     약 N/16    이웃 <= 16
        |   |   |   |   |
 층 0   o-o-o-o-o-o-o-o-o-o-o-o-o-o-o-o       N          이웃 <= 32

 원소는 자기 층부터 0층까지 모든 층에 있다 (층 2 원소는 층 1, 0 에도 있다)
 진입점 = 가장 높은 층의 원소 하나 (graph->entryPoint, 메타 페이지 entryBlkno/entryOffno)
```

두 단계가 어떤 경로를 타는지는 메모리에 달려 있다.

```text
 메모리 단계와 디스크 단계

 graph->memoryUsed + margin >= memoryTotal ?  (InsertTuple L533)
   아니오  메모리 단계   HnswInitElement -> InsertTupleInMemory    포인터 그래프에 삽입
   예      FlushPages 한 번 (flushed = true)
           디스크 단계   HnswInsertTupleOnDisk(..., building = true)
                          INSERT 와 같은 알고리즘, 다만 GenericXLog 를 쓰지 않는다
 모두 메모리에 들어가면 디스크 단계는 없다
```

## 어디에서 쓰이는가

```text
 [거리 연산자와 Index AM]  ambuild = hnswbuild, ambuildempty = hnswbuildempty
 [HNSW 검색]              HnswSearchLayer 를 빌드도 그대로 쓴다 (index = NULL 이면 메모리)
                          빌드가 쓴 메타 페이지와 원소/이웃 튜플을 검색이 읽는다
 상위 [버퍼 관리]          새 페이지는 ReadBufferExtended(P_NEW) 로 얻는다 (HnswNewBuffer)
 상위 [행 쓰기와 WAL 기록]  WAL 은 log_newpage_range 로 페이지 통째로 남긴다
```

상위 PostgreSQL 지도의 [ReadBufferExtended](../../../../architecture/flows/buffer-manager/01_ReadBufferExtended/README.md)가 새 인덱스 페이지를 얻는 입구이고, 빌드 끝의 WAL 기록은 [XLogInsert](../../../../architecture/flows/heap-insert-wal/06_XLogInsert/README.md)로 이어진다.

## 단계

1. [hnswbuild](01_hnswbuild/README.md)가 `BuildIndex` 를 불러 그래프를 짓고 WAL 을 남긴다.
2. [InitBuildState](02_InitBuildState/README.md)가 옵션과 차원을 검사하고 `ml`, `maxLevel`, 메모리 상한을 정한다.
3. [BuildGraph](03_BuildGraph/README.md)가 (병렬이면 일꾼을 띄우고) 힙을 훑은 뒤 남은 그래프를 flush 한다.
4. [InsertTuple](04_InsertTuple/README.md)이 행마다 메모리 단계와 디스크 단계를 가른다.
5. [HnswInitElement](05_HnswInitElement/README.md)가 원소를 할당하고 층을 무작위로 정한다.
6. [InsertTupleInMemory](06_InsertTupleInMemory/README.md)가 진입점 잠금을 잡고 이웃 찾기와 그래프 갱신을 부른다.
7. [HnswFindElementNeighbors](07_HnswFindElementNeighbors/README.md)가 층마다 후보를 모아 이웃을 고른다.
8. [UpdateGraphInMemory](08_UpdateGraphInMemory/README.md)가 원소를 그래프에 붙이고 양방향 연결을 만든다.
9. [FlushPages](09_FlushPages/README.md)가 메모리 그래프를 메타 페이지와 원소·이웃 튜플로 옮겨 적는다.

## 결과가 쓰이는 곳

```text
 인덱스 페이지
   블록 0         메타 페이지 (m, ef_construction, dimensions, 진입점, insertPage)
   블록 1 ..      원소 튜플 + 이웃 튜플, nextblkno 로 이어진 한 줄
      --> [HNSW 검색] 이 메타 페이지에서 진입점을 읽고 이웃 튜플을 따라간다
      --> INSERT (hnswinsert) 가 insertPage 부터 빈자리를 찾는다
 IndexBuildResult
      --> pg_class.reltuples 갱신에 쓰인다 (heap_tuples)
```

## 다루지 않는 것

병렬 빌드의 세부(DSM 할당, `HnswParallelBuildMain`, 공유 메모리 안의 상대 포인터 `relptr`), 디스크 단계의 삽입 본문(`HnswInsertTupleOnDisk`, hnswinsert.c L695 — 일반 `INSERT` 경로와 같다), 빌드 진행률 보고(`pgstat_progress_update_param`), `HNSW_MEMORY`·`HNSW_BENCH` 디버그 빌드 분기는 요약만 했다.

## 하위 메서드

- [01 hnswbuild](01_hnswbuild/README.md)
- [02 InitBuildState](02_InitBuildState/README.md)
- [03 BuildGraph](03_BuildGraph/README.md)
- [04 InsertTuple](04_InsertTuple/README.md)
- [05 HnswInitElement](05_HnswInitElement/README.md)
- [06 InsertTupleInMemory](06_InsertTupleInMemory/README.md)
- [07 HnswFindElementNeighbors](07_HnswFindElementNeighbors/README.md)
- [08 UpdateGraphInMemory](08_UpdateGraphInMemory/README.md)
- [09 FlushPages](09_FlushPages/README.md)
