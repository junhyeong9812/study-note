# HNSW 검색

상위: [pgvector 아키텍처 지도](../../README.md)

`SELECT ... ORDER BY embedding <-> '[...]' LIMIT 10` 이 HNSW 인덱스 스캔으로 실행될 때, **실행기가 `amgettuple` 을 부를 때마다 가까운 순으로 힙 TID 하나씩을 돌려받기까지**의 흐름이다. 첫 호출에서 한 번에 탐색을 끝낸다. 메타 페이지에서 진입점을 읽고, 위층은 폭 1 로 내려오고, 0층에서 폭 `hnsw.ef_search`(기본 40)로 탐색해 가까운 후보 최대 `ef_search` 개를 목록에 담는다(논문의 Algorithm 5). 이후 호출은 그 목록에서 가장 가까운 것부터 꺼내 줄 뿐이다. 목록이 바닥나면 기본 설정에서는 스캔이 끝난다. 그래서 `ef_search` 보다 큰 `LIMIT` 이나 걸러지는 `WHERE` 가 있으면 행이 모자랄 수 있고, 이것을 메우는 것이 0.8.0 에 들어온 반복 스캔(`hnsw.iterative_scan`, CHANGELOG.md L40)이다. 반복 스캔을 켜면 탐색 중 버린 후보를 따로 모아 두었다가, 목록이 바닥날 때 그 후보들에서 0층 탐색을 이어 간다.

기준 태그: v0.8.7 [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/` 아래다.

## 전체 그림

```text
 실행기 IndexScan -> index_beginscan / index_rescan / index_getnext ...
 [01] hnswbeginscan                         hnswscan.c    L135
      +-- HnswGetTypeInfo, HnswInitSupport
      +-- tmpCtx, maxMemory = work_mem * hnsw.scan_mem_multiplier
 [02] hnswrescan                            hnswscan.c    L171
      +-- first = true, tmpCtx 비우기, ORDER BY 키 복사
 [03] hnswgettuple                          hnswscan.c    L194     (행마다 한 번)
      +-- first 이면
      |     +-- [04] GetScanValue    ORDER BY 의 상수, cosine 이면 정규화   L97
      |     +-- LockPage(HNSW_SCAN_LOCK, Share)                           L233
      |     +-- [05] GetScanItems                                         L25
      |     |     +-- HnswGetMetaPageInfo -> m, dimensions, 진입점
      |     |     +-- [06] HnswEntryCandidate   진입점 원소 읽고 거리     hnswutils.c L614
      |     |     +-- lc = entryLevel .. 1   [07] HnswSearchLayer(ef = 1)
      |     |     +-- lc = 0                 [07] HnswSearchLayer(ef = ef_search)
      |     |                                  +-- [08] HnswLoadUnvisitedFromDisk
      |     |                                        이웃 튜플에서 아직 안 본 TID
      |     +-- UnlockPage
      +-- so->w 의 마지막(가장 가까운) 원소에서 heaptid 하나를 꺼내 반환
      +-- so->w 가 비면
            iterative_scan = off  -> false (스캔 끝)
            그 밖                -> [09] ResumeScanItems  버린 후보에서 0층 탐색 재개
```

탐색이 그래프의 어디를 지나는지를 그리면 다음과 같다.

```text
 m = 16, 진입점 level 2, ef_search = 40

 층 2   [진입점] --가장 가까운 이웃으로 이동, 더 못 가까워지면 멈춤--> p2
 층 1   [p2]    --같은 방식, 폭 1-----------------------------------> p1
 층 0   [p1]    --폭 40: 후보 힙 C 와 결과 힙 W(최대 40) 로 확장------> W
                  확장할 때마다 이웃 튜플 1개 + 이웃 원소 튜플 최대 32개를 읽는다

 W 를 먼 것부터 꺼내 목록 w 에 담는다 -> w 의 끝이 가장 가깝다
 hnswgettuple 은 w 의 끝에서부터 꺼낸다
```

## 어디에서 쓰이는가

```text
 [거리 연산자와 Index AM]  ambeginscan, amrescan, amgettuple, amendscan 자리
                          hnswcostestimate 가 이 경로를 고르게 한다
 [HNSW 빌드]              같은 HnswSearchLayer 를 메모리 모드(index = NULL)로 쓴다
                          빌드가 쓴 메타 페이지·원소 튜플·이웃 튜플을 이 흐름이 읽는다
 상위 [버퍼 관리]          원소와 이웃 튜플을 읽을 때마다 ReadBuffer + LockBuffer(SHARE)
```

상위 PostgreSQL 지도는 인덱스 스캔 노드(`ExecIndexScan`, `index_getnext_slot`)를 따로 다루지 않는다. 페이지를 읽는 쪽은 [버퍼 관리](../../../../architecture/flows/buffer-manager/README.md)로 이어진다.

## 단계

1. [hnswbeginscan](01_hnswbeginscan/README.md)이 스캔 상태와 메모리 상한을 준비한다.
2. [hnswrescan](02_hnswrescan/README.md)이 ORDER BY 키를 받아 스캔을 처음 상태로 되돌린다.
3. [hnswgettuple](03_hnswgettuple/README.md)이 첫 호출에 탐색하고, 호출마다 가장 가까운 힙 TID 하나를 낸다.
4. [GetScanValue](04_GetScanValue/README.md)가 검색 값을 꺼내고 필요하면 정규화한다.
5. [GetScanItems](05_GetScanItems/README.md)가 위층에서 0층까지 내려오며 후보 목록을 만든다.
6. [HnswEntryCandidate](06_HnswEntryCandidate/README.md)가 원소 튜플을 읽어 거리를 잰다.
7. [HnswSearchLayer](07_HnswSearchLayer/README.md)가 한 층에서 후보 힙과 결과 힙으로 탐색한다.
8. [HnswLoadUnvisitedFromDisk](08_HnswLoadUnvisitedFromDisk/README.md)가 이웃 튜플에서 아직 안 본 이웃을 고른다.
9. [ResumeScanItems](09_ResumeScanItems/README.md)가 반복 스캔에서 버린 후보로 0층 탐색을 이어 간다.

## 결과가 쓰이는 곳

```text
 scan->xs_heaptid
      --> 실행기가 힙 튜플을 읽고 MVCC 가시성을 판단한다
          (보이지 않으면 다음 amgettuple 을 부른다)
 xs_recheck = false, xs_recheckorderby = false   (hnswscan.c L329-L330)
      --> 실행기는 거리를 다시 계산해 순서를 고치지 않는다
          반환 순서가 곧 결과 순서이고, 근사다
```

## 다루지 않는 것

병렬 인덱스 스캔(`amcanparallel = false` 라 없다), 비트맵 스캔(`amgetbitmap = NULL`), VACUUM 이 `HNSW_SCAN_LOCK` 을 배타로 잡아 진행 중인 스캔을 기다리는 쪽(hnswvacuum.c), 메모리 그래프 모드의 탐색 세부(`HnswLoadUnvisitedFromMemory`)는 요약만 했다.

## 하위 메서드

- [01 hnswbeginscan](01_hnswbeginscan/README.md)
- [02 hnswrescan](02_hnswrescan/README.md)
- [03 hnswgettuple](03_hnswgettuple/README.md)
- [04 GetScanValue](04_GetScanValue/README.md)
- [05 GetScanItems](05_GetScanItems/README.md)
- [06 HnswEntryCandidate](06_HnswEntryCandidate/README.md)
- [07 HnswSearchLayer](07_HnswSearchLayer/README.md)
- [08 HnswLoadUnvisitedFromDisk](08_HnswLoadUnvisitedFromDisk/README.md)
- [09 ResumeScanItems](09_ResumeScanItems/README.md)
