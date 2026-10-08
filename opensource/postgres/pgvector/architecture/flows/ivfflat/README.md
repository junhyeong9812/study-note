# IVFFlat 빌드와 검색

상위: [pgvector 아키텍처 지도](../../README.md)

IVFFlat 은 벡터 공간을 `lists` 개의 칸으로 나누고, 행마다 가장 가까운 칸(리스트)에 넣어 두는 인덱스다. 이 흐름은 **`CREATE INDEX ... USING ivfflat (embedding vector_l2_ops) WITH (lists = 100)` 이 표본으로 k-means 를 돌려 중심점 100 개를 정하고, 모든 행을 가장 가까운 중심점의 리스트 페이지에 몰아 적기까지**, 그리고 **`ORDER BY embedding <-> q` 가 중심점 중 가까운 `ivfflat.probes` 개의 리스트만 훑어 거리 순으로 정렬해 내기까지**를 함께 본다. HNSW 와 달리 그래프가 없다. 빌드의 무거운 일은 k-means 이고, 검색의 일은 "가까운 리스트 고르기 + 그 리스트 전수 비교 + 정렬"이다. 중심점은 빌드 때 표본으로 한 번 정해지고, 이후 INSERT 는 가장 가까운 리스트에 항목을 붙일 뿐 중심점을 고치지 않는다. 표본이 `lists` 보다 적으면 빌드가 "ivfflat index created with little data" NOTICE 로 낮은 재현율을 경고한다(ivfbuild.c L472-L478).

기준 태그: v0.8.7 [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/` 아래다.

## 전체 그림

```text
 빌드  index_build -> ambuild
 [01] ivfflatbuild                            ivfbuild.c   L1069
      +-- BuildIndex                                       L1046
          +-- InitBuildState   lists, dimensions, 지원 함수, 정렬용 튜플 모양
          +-- [02] ComputeCenters                          L440
          |     +-- 표본 수 = max(lists * 50, 10000), 최대 블록 수 * MaxHeapTuplesPerPage
          |     +-- SampleRows -> AddSample   ANALYZE 와 같은 블록 표본 + 저수지 표본
          |     +-- [03] IvfflatKmeans -> ElkanKmeans      ivfkmeans.c L553 / L246
          |           k-means++ 로 시작점, 최대 500 회 반복
          +-- CreateMetaPage                  블록 0
          +-- [04] CreateListPages            블록 1 부터, 중심점마다 리스트 튜플
          +-- CreateEntryPages                             L1023
                +-- AssignTuples -> [05] AddTupleToSort    행마다 가장 가까운 리스트 번호
                +-- tuplesort_performsort     리스트 번호 순 정렬
                +-- [06] InsertTuples         리스트마다 항목 페이지 체인을 쓰고
                                              리스트 튜플의 startPage, insertPage 갱신
 ------------------------------------------------------------------------------
 검색  ambeginscan -> amrescan -> amgettuple ...
 [07] ivfflatgettuple                         ivfscan.c    L363
      +-- 첫 호출: GetScanValue (정규화, 차원 검사)
      +-- [08] GetScanLists    모든 리스트 튜플의 중심점과 거리, 가까운 maxProbes 개
      +-- [09] GetScanItems    가까운 probes 개 리스트의 모든 항목 -> 거리로 tuplesort
      +-- tuplesort 에서 하나씩 꺼내 힙 TID 반환
      +-- 다 꺼냈고 반복 스캔이면 다음 probes 개 리스트로 [09] 다시
```

인덱스 파일의 모양은 이렇다. 리스트 튜플이 리스트마다 "첫 항목 페이지"와 "새 항목을 넣을 페이지"를 가리킨다.

```text
 lists = 3 인 IVFFlat 인덱스

 블록 0   메타   magic 0x14FF1A7, version 1, dimensions, lists 3
 블록 1   리스트 페이지 (nextblkno 로 이어짐)
          [L0: startPage 2, insertPage 3, center c0]
          [L1: startPage 4, insertPage 4, center c1]
          [L2: startPage 5, insertPage 5, center c2]
 블록 2   L0 항목 페이지   IndexTuple(벡터, t_tid = 힙 TID) ... --nextblkno--> 블록 3
 블록 3   L0 항목 페이지 (insertPage)
 블록 4   L1 항목 페이지
 블록 5   L2 항목 페이지

 검색 (probes = 1)   q 와 c0, c1, c2 의 거리 -> 가장 가까운 c1
                     블록 4 의 항목 전부와 거리 -> 정렬 -> 하나씩
```

## 어디에서 쓰이는가

```text
 [거리 연산자와 Index AM]  ivfflathandler 의 ambuild, aminsert, ambeginscan, amgettuple
                          FUNCTION 3, 4 (k-means 용) 는 이 흐름의 [03] 에서만 쓰인다
 INSERT (ivfflatinsert)    리스트 튜플을 모두 훑어 가장 가까운 중심점의 insertPage 에
                          항목을 붙인다. 중심점은 바꾸지 않는다 (ivfinsert.c L189, 범위 밖)
 상위 [버퍼 관리]          리스트·항목 페이지 읽기, 스캔은 BAS_BULKREAD 링 버퍼 (ivfscan.c L321)
 상위 [행 쓰기와 WAL 기록]  빌드의 모든 페이지 쓰기가 GenericXLog
                          (새 페이지는 전체 이미지, 리스트 튜플 갱신 IvfflatUpdateList 는 flags 0)
```

WAL 은 HNSW 와 다르게 남긴다. IVFFlat 빌드는 새 페이지를 만들 때마다 `GenericXLogStart` 와 `GENERIC_XLOG_FULL_IMAGE` 로 등록하고 `GenericXLogFinish` 로 기록한다(ivfutils.c L162-L178). 빌드 끝에 `log_newpage_range` 를 하는 것은 init fork 일 때뿐이다(ivfbuild.c L1059-L1061, 주석: GenericXLog 함수가 init fork 는 기록하지 않는다). 상위 지도의 [XLogInsert](../../../../architecture/flows/heap-insert-wal/06_XLogInsert/README.md)가 그 아래에서 레코드를 만든다.

## 단계

1. [ivfflatbuild](01_ivfflatbuild/README.md)가 중심점 계산, 메타·리스트·항목 페이지 생성을 차례로 부른다.
2. [ComputeCenters](02_ComputeCenters/README.md)가 표본 수를 정하고 표본을 뽑는다.
3. [ElkanKmeans](03_ElkanKmeans/README.md)가 k-means++ 로 시작해 Elkan 방식으로 중심점을 다듬는다.
4. [CreateListPages](04_CreateListPages/README.md)가 중심점마다 리스트 튜플을 쓴다.
5. [AddTupleToSort](05_AddTupleToSort/README.md)가 행마다 가장 가까운 리스트를 골라 정렬기에 넣는다.
6. [InsertTuples](06_InsertTuples/README.md)가 정렬된 행을 리스트별 항목 페이지 체인으로 쓴다.
7. [ivfflatgettuple](07_ivfflatgettuple/README.md)이 첫 호출에 리스트를 고르고 항목을 정렬한 뒤 하나씩 낸다.
8. [GetScanLists](08_GetScanLists/README.md)가 모든 중심점과의 거리로 가까운 리스트를 고른다.
9. [GetScanItems](09_GetScanItems/README.md)가 고른 리스트의 항목을 모두 거리와 함께 정렬기에 넣는다.

## 결과가 쓰이는 곳

```text
 메타 페이지 (lists, dimensions)
      --> ivfflatbeginscan, ivfflatcostestimate, ivfflatinsert
 리스트 튜플 (center, startPage, insertPage)
      --> 검색 [08] 이 중심점을, [09] 가 startPage 를 쓴다
      --> INSERT 가 insertPage 를 쓰고 페이지가 차면 갱신한다
 항목 튜플 (IndexTuple: 벡터 + 힙 TID)
      --> 검색 [09] 가 거리를 다시 계산한다
```

## 다루지 않는 것

병렬 빌드(`IvfflatBeginParallel`: 일꾼이 같은 중심점으로 행을 배정하고 공유 정렬기에 넣는다, L836), INSERT 본문(ivfinsert.c), VACUUM(ivfvacuum.c), 디버그 빌드의 k-means 지표(`PrintKmeansMetrics`)는 요약만 했다. `halfvec` 과 `bit` 은 타입 정보(`ivfflat_halfvec_support`, `ivfflat_bit_support`)로 중심점 계산만 달리한다.

## 하위 메서드

- [01 ivfflatbuild](01_ivfflatbuild/README.md)
- [02 ComputeCenters](02_ComputeCenters/README.md)
- [03 ElkanKmeans](03_ElkanKmeans/README.md)
- [04 CreateListPages](04_CreateListPages/README.md)
- [05 AddTupleToSort](05_AddTupleToSort/README.md)
- [06 InsertTuples](06_InsertTuples/README.md)
- [07 ivfflatgettuple](07_ivfflatgettuple/README.md)
- [08 GetScanLists](08_GetScanLists/README.md)
- [09 GetScanItems](09_GetScanItems/README.md)
