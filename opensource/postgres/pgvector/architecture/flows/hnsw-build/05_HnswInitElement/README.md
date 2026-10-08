# HnswInitElement

상위: [HNSW 빌드](../README.md)

**그래프 원소 하나를 할당하고 그 원소가 올라갈 가장 높은 층을 무작위로 정하는 함수다.** 층은 균등 난수 U 로 `floor(-ln(U) * ml)` 이고 `maxLevel` 에서 자른다. 층이 정해지면 0층부터 그 층까지 층마다 이웃 배열을 하나씩 할당한다. 0층 배열은 `2m` 칸, 위층은 `m` 칸이다. 빌드와 INSERT 가 같은 함수를 쓴다.

## 위치

`src` / `hnswutils.c` L245-L270 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L245-L270))

## 실제 코드

원소 구조체와 이웃 배열이다.

`src` / `hnsw.h` L182-L214 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.h#L182-L214))

```c
// hnsw.h L182-L214
struct HnswElementData
{
	HnswElementPtr next;
	ItemPointerData heaptids[HNSW_HEAPTIDS];
	uint8		heaptidsLength;
	uint8		level;
	uint8		deleted;
	uint8		version;
	uint32		hash;
	HnswNeighborsPtr neighbors;
	BlockNumber blkno;
	OffsetNumber offno;
	OffsetNumber neighborOffno;
	BlockNumber neighborPage;
	DatumPtr	value;
	LWLock		lock;
};

typedef HnswElementData * HnswElement;

typedef struct HnswCandidate
{
	HnswElementPtr element;
	float		distance;
	bool		closer;
}			HnswCandidate;

struct HnswNeighborArray
{
	int			length;
	bool		closerSet;
	HnswCandidate items[FLEXIBLE_ARRAY_MEMBER];
};
```

```c
// hnswutils.c L202-L279
/*
 * Allocate a neighbor array
 */
HnswNeighborArray *
HnswInitNeighborArray(int lm, HnswAllocator * allocator)
{
	HnswNeighborArray *a = HnswAlloc(allocator, HNSW_NEIGHBOR_ARRAY_SIZE(lm));

	a->length = 0;
	a->closerSet = false;
	return a;
}

/*
 * Allocate neighbors
 */
void
HnswInitNeighbors(char *base, HnswElement element, int m, HnswAllocator * allocator)
{
	int			level = element->level;
	HnswNeighborArrayPtr *neighborList = (HnswNeighborArrayPtr *) HnswAlloc(allocator, mul_size(sizeof(HnswNeighborArrayPtr), add_size(level, 1)));

	HnswPtrStore(base, element->neighbors, neighborList);

	for (int lc = 0; lc <= level; lc++)
		HnswPtrStore(base, neighborList[lc], HnswInitNeighborArray(HnswGetLayerM(m, lc), allocator));
}

/*
 * Allocate memory from the allocator
 */
void *
HnswAlloc(HnswAllocator * allocator, Size size)
{
	if (allocator)
		return (*(allocator)->alloc) (size, (allocator)->state);

	return palloc(size);
}

/*
 * Allocate an element
 */
HnswElement
HnswInitElement(char *base, ItemPointer heaptid, int m, double ml, int maxLevel, HnswAllocator * allocator)
{
	HnswElement element = HnswAlloc(allocator, sizeof(HnswElementData));

	double		uniform = RandomDouble();
	int			level = uniform == 0.0 ? maxLevel : (int) (-log(uniform) * ml);

	/* Cap level */
	if (level > maxLevel)
		level = maxLevel;

	element->heaptidsLength = 0;
	HnswAddHeapTid(element, heaptid);

	element->level = level;
	element->deleted = 0;
	/* Start at one to make it easier to find issues */
	element->version = 1;

	HnswInitNeighbors(base, element, m, allocator);

	HnswPtrStore(base, element->value, (char *) NULL);

	return element;
}

/*
 * Add a heap TID to an element
 */
void
HnswAddHeapTid(HnswElement element, ItemPointer heaptid)
{
	element->heaptids[element->heaptidsLength++] = *heaptid;
}
```

## 동작 흐름

```text
 HnswInitElement(base, heaptid, m, ml, maxLevel, allocator)    L245
   L248  element = HnswAlloc(sizeof(HnswElementData))
   L250  uniform = RandomDouble()          [0, 1)
   L251  level = uniform == 0 ? maxLevel : (int)(-ln(uniform) * ml)
   L254  level > maxLevel 이면 maxLevel
   L257  heaptidsLength = 0, HnswAddHeapTid(heaptid)   heaptids[0] = 이 행
   L260  level, deleted = 0, version = 1
   L265  HnswInitNeighbors                              L218
           neighborList = 포인터 (level + 1) 개
           lc = 0      HnswInitNeighborArray(2m)    length 0
           lc = 1..L   HnswInitNeighborArray(m)
   L267  value = NULL                    값은 호출자가 채운다 (InsertTuple L568)
```

`m = 16`, `ml = 1/ln(16) = 0.3607` 에서 난수가 층을 정하는 모습이다.

```text
 U        -ln(U)   * ml      level   이 층 이상일 확률
 0.5      0.693    0.250     0       1
 0.06     2.813    1.015     1       16^-1 = 0.0625
 0.003    5.809    2.095     2       16^-2 = 0.0039
 0.0001   9.210    3.322     3       16^-3 = 0.00024

 P(level >= l) = P(-ln(U) * ml >= l) = P(U <= e^(-l/ml)) = e^(-l * ln 16) = 16^-l
```

```text
 level 2 원소의 메모리 모양 (m = 16)

 HnswElementData
 +-------------------------------+
 | heaptids[10]  heaptidsLength 1|
 | level 2  version 1  deleted 0 |
 | neighbors ---------------------+---> [0] ---> HnswNeighborArray  items[32]  length 0
 | value  -> 벡터 복사본          |     [1] ---> HnswNeighborArray  items[16]  length 0
 | lock (LWLock)                 |     [2] ---> HnswNeighborArray  items[16]  length 0
 | next  (원소 목록 연결)          |
 +-------------------------------+
 HnswCandidate = { element 포인터, distance, closer }
```

`heaptids` 는 배열이다. 값이 같은 행이 이웃으로 발견되면 새 원소를 그래프에 붙이지 않고 기존 원소에 힙 TID 를 붙인다([08] `FindDuplicateInMemory`). 상한은 `HNSW_HEAPTIDS` 10 이고, 헤더 주석은 그 목적을 "Make graph robust against non-HOT updates"(hnsw.h L68)라고 적는다.

## 결과가 쓰이는 곳

```text
 HnswElement
      --> [06] InsertTupleInMemory, [07] 의 이웃 찾기 대상
      --> level 은 [09] 에서 이웃 튜플 크기 (level + 2) * m 칸을 정한다
      --> INSERT 에서는 같은 함수가 allocator = NULL(palloc) 로 불린다 (hnswinsert.c L720)
```

## 다루지 않는 것

`RandomDouble` 의 구현(PostgreSQL 15 이상 `pg_prng_double`, 그 아래는 `random()`, hnsw.h L104-L110), 원소의 `hash` 칸(방문 집합 해시를 미리 계산해 두는 자리, `PrecomputeHash` hnswutils.c L1267)은 요약만 했다.
