# HnswLoadUnvisitedFromDisk

상위: [HNSW 검색](../README.md)

**펼쳐 볼 원소 하나의 이웃 튜플을 읽어, 그 층의 이웃 중 아직 방문하지 않은 것의 인덱스 TID 를 모으는 함수다.** 이웃 튜플은 원소 튜플과 따로 있으므로 원소마다 페이지를 한 번 더 읽는다. 읽기 전에 이웃 튜플의 세대(`version`)와 칸 수가 원소와 맞는지 확인해, 그사이 VACUUM 이 그 자리를 다른 원소로 바꿔 놓았으면 이웃이 없는 것으로 친다.

## 위치

`src` / `hnswutils.c` L799-L822 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L799-L822))

## 실제 코드

```c
// hnswutils.c L796-L822
/*
 * Load unvisited neighbors from disk
 */
static void
HnswLoadUnvisitedFromDisk(HnswElement element, HnswUnvisited * unvisited, int *unvisitedLength, visited_hash * v, Relation index, int m, int lm, int lc)
{
	ItemPointerData indextids[HNSW_MAX_M * 2];

	*unvisitedLength = 0;

	if (!HnswLoadNeighborTids(element, indextids, index, m, lm, lc))
		return;

	for (int i = 0; i < lm; i++)
	{
		ItemPointer indextid = &indextids[i];
		bool		found;

		if (!ItemPointerIsValid(indextid))
			break;

		tidhash_insert(v->tids, *indextid, &found);

		if (!found)
			unvisited[(*unvisitedLength)++].indextid = *indextid;
	}
}
```

이웃 튜플에서 한 층의 칸만 잘라 오는 함수다. INSERT 의 이웃 갱신도 이것을 쓴다.

`src` / `hnswutils.c` L764-L794 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L764-L794))

```c
// hnswutils.c L761-L794
/*
 * Load neighbor index TIDs
 */
bool
HnswLoadNeighborTids(HnswElement element, ItemPointerData *indextids, Relation index, int m, int lm, int lc)
{
	Buffer		buf;
	Page		page;
	HnswNeighborTuple ntup;
	Size		start;

	buf = ReadBuffer(index, element->neighborPage);
	LockBuffer(buf, BUFFER_LOCK_SHARE);
	page = BufferGetPage(buf);

	ntup = (HnswNeighborTuple) PageGetItem(page, PageGetItemId(page, element->neighborOffno));

	/*
	 * Ensure the neighbor tuple has not been deleted or replaced between
	 * index scan iterations
	 */
	if (ntup->version != element->version || ntup->count != (element->level + 2) * m)
	{
		UnlockReleaseBuffer(buf);
		return false;
	}

	/* Copy to minimize lock time */
	start = mul_size(element->level - lc, m);
	memcpy(indextids, ntup->indextids + start, mul_size(sizeof(ItemPointerData), lm));

	UnlockReleaseBuffer(buf);
	return true;
}
```

## 동작 흐름

```text
 HnswLoadUnvisitedFromDisk(element, unvisited, &len, v, index, m, lm, lc)    L799
   L802  indextids[HNSW_MAX_M * 2]           스택에 200 칸
   L806  HnswLoadNeighborTids                L764
           L772  ReadBuffer(element->neighborPage), SHARE
           L776  ntup = PageGetItem(neighborOffno)
           L782  ntup->version != element->version
                 또는 ntup->count != (level + 2) * m    -> false (이웃 없음 취급)
           L789  start = (level - lc) * m
           L790  indextids 에 lm 칸 복사                잠금 시간을 줄이려고 복사 (주석 L788)
           L792  UnlockReleaseBuffer
   L809  i = 0 .. lm-1
           L814  무효 TID 면 break                    빈칸부터는 끝
           L817  tidhash_insert(v->tids, tid, &found)
           L819  처음 보는 것이면 unvisited 에 추가
```

```text
 level 2 원소의 0층 이웃을 읽을 때 (m = 16, lm = 32)

 이웃 튜플 indextids (count = (2 + 2) * 16 = 64)
 [ 0 .. 15 ]  [ 16 .. 31 ]  [ 32 .. 63 ]
   2층          1층           0층
 start = (2 - 0) * 16 = 32  -> [32 .. 63] 32칸을 복사
 앞에서부터 무효 TID 를 만날 때까지 = 실제 이웃 수
```

`HnswSearchLayer` 는 이렇게 모은 TID 마다 `HnswLoadElementImpl` 로 원소 튜플을 다시 읽으므로, 원소 하나를 펼칠 때 읽는 페이지는 "이웃 튜플 1 + 안 본 이웃 원소 최대 lm" 이다. 원소 튜플과 이웃 튜플이 같은 페이지에 있으면 빌드의 배치([HNSW 빌드] 09) 덕에 같은 버퍼를 다시 읽게 된다.

## 결과가 쓰이는 곳

```text
 unvisited[].indextid, unvisitedLength
      --> [07] HnswSearchLayer 가 각각의 거리를 재서 C, W 에 넣을지 정한다
 v->tids (방문 해시)
      --> 같은 원소를 두 번 펼치지 않는다. 반복 스캔이 이어 쓴다
```

## 다루지 않는 것

메모리 모드 판 `HnswLoadUnvisitedFromMemory`(L736)는 원소의 LWLock 을 공유로 잡고 이웃 배열을 지역 메모리로 복사한 뒤 같은 일을 한다. 버전이 바뀌는 상황(VACUUM 이 지운 원소 자리를 INSERT 가 재사용, hnswinsert.c `HnswFreeOffset` L44)은 범위 밖이다.
