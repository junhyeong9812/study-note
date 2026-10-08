# hnswbeginscan

상위: [HNSW 검색](../README.md)

**HNSW 인덱스 스캔 하나의 상태를 만드는 `ambeginscan` 이다.** 아직 검색 값을 모르므로 탐색은 하지 않는다. 타입 정보와 지원 함수를 꺼내 두고, 탐색 중 만드는 후보·방문 집합이 들어갈 메모리 컨텍스트를 만들고, 반복 스캔이 쓸 수 있는 메모리 상한을 계산한다.

## 위치

`src` / `hnswscan.c` L135-L166 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswscan.c#L135-L166))

## 실제 코드

스캔 상태 구조체다.

`src` / `hnsw.h` L410-L428 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.h#L410-L428))

```c
// hnsw.h L397-L428
typedef union
{
	struct pointerhash_hash *pointers;
	struct offsethash_hash *offsets;
	struct tidhash_hash *tids;
}			visited_hash;

typedef union
{
	HnswElement element;
	ItemPointerData indextid;
}			HnswUnvisited;

typedef struct HnswScanOpaqueData
{
	const		HnswTypeInfo *typeInfo;
	bool		first;
	List	   *w;
	visited_hash v;
	pairingheap *discarded;
	HnswQuery	q;
	int			m;
	int64		tuples;
	double		previousDistance;
	Size		maxMemory;
	MemoryContext tmpCtx;

	/* Support functions */
	HnswSupport support;
}			HnswScanOpaqueData;

typedef HnswScanOpaqueData * HnswScanOpaque;
```

```c
// hnswscan.c L132-L166
/*
 * Prepare for an index scan
 */
IndexScanDesc
hnswbeginscan(Relation index, int nkeys, int norderbys)
{
	IndexScanDesc scan;
	HnswScanOpaque so;
	double		maxMemory;

	scan = RelationGetIndexScan(index, nkeys, norderbys);

	so = palloc_object(HnswScanOpaqueData);
	so->typeInfo = HnswGetTypeInfo(index);

	/* Set support functions */
	HnswInitSupport(&so->support, index);

	/*
	 * Use a lower max allocation size than default to allow scanning more
	 * tuples for iterative search before exceeding work_mem
	 */
	so->tmpCtx = AllocSetContextCreate(CurrentMemoryContext,
									   "Hnsw scan temporary context",
									   0, 8 * 1024, 256 * 1024);

	/* Calculate max memory */
	/* Add 256 extra bytes to fill last block when close */
	maxMemory = (double) work_mem * hnsw_scan_mem_multiplier * 1024.0 + 256;
	so->maxMemory = Min(maxMemory, (double) (SIZE_MAX / 2));

	scan->opaque = so;

	return scan;
}
```

## 동작 흐름

```text
 hnswbeginscan(index, nkeys, norderbys)             L135
   L142  RelationGetIndexScan               PostgreSQL 공용 IndexScanDesc
   L144  so = HnswScanOpaqueData
   L145  typeInfo = HnswGetTypeInfo         차원 함수, 정규화 함수
   L148  HnswInitSupport                    거리 함수 = FUNCTION 1, 정규화 판정 = FUNCTION 2
   L154  tmpCtx = AllocSetContext(최소 0, 처음 8KB, 최대 블록 256KB)
           주석 L150-L153: 기본보다 작은 최대 블록으로 반복 스캔이 work_mem 을
           넘기 전에 더 많은 튜플을 훑게 한다
   L160  maxMemory = work_mem(KB) * hnsw.scan_mem_multiplier * 1024 + 256
   L161  SIZE_MAX / 2 에서 자른다
   L163  scan->opaque = so
```

```text
 maxMemory 예

 work_mem = 4MB (4096 KB), scan_mem_multiplier = 1 (기본)
   4096 * 1 * 1024 + 256 = 4,194,560 바이트
 반복 스캔에서 MemoryContextMemAllocated(tmpCtx) 가 이것을 넘으면
   더 탐색하지 않고 버린 후보만 차례로 내준다 (hnswgettuple L264)
```

`HnswScanOpaqueData` 의 방문 집합 `v` 는 공용체다(hnsw.h L397-L402). 디스크 스캔은 원소를 (블록, 오프셋) TID 로 기억하는 `tidhash` 를, 메모리 빌드는 포인터나 오프셋 해시를 쓴다. 스캔은 늘 디스크 모드라 `v.tids` 만 쓴다.

## 결과가 쓰이는 곳

```text
 IndexScanDesc (opaque = HnswScanOpaque)
      --> [02] hnswrescan 이 ORDER BY 키를 채운다
      --> [03] hnswgettuple 이 so->tmpCtx 안에서 탐색한다
      --> hnswendscan (L341) 이 tmpCtx 를 지우고 so 를 해제한다
```

## 다루지 않는 것

`RelationGetIndexScan` 이 채우는 공용 필드(`keyData`, `orderByData` 배열 할당)는 PostgreSQL 쪽이다.
