# page_collect_tuples

상위: [MVCC 가시성과 스냅샷](../README.md)

**페이지의 줄 포인터를 1번부터 끝까지 돌며 보이는 튜플의 줄 번호만 모으는 반복문이다.** 튜플마다 [07] `HeapTupleSatisfiesVisibility` 를 부르고, 페이지 전체가 all-visible 이면 부르지 않는다. 인자 두 개를 상수로 받게 떼어 낸 함수라 컴파일러가 네 가지 버전을 따로 만든다.

## 위치

`access/heap` / `heapam.c` L506-L547 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L506-L547))

## 실제 코드

```c
// heapam.c L499-L547
/*
 * Per-tuple loop for heap_prepare_pagescan(). Pulled out so it can be called
 * multiple times, with constant arguments for all_visible,
 * check_serializable.
 */
pg_always_inline
static int
page_collect_tuples(HeapScanDesc scan, Snapshot snapshot,
					Page page, Buffer buffer,
					BlockNumber block, int lines,
					bool all_visible, bool check_serializable)
{
	int			ntup = 0;
	OffsetNumber lineoff;

	for (lineoff = FirstOffsetNumber; lineoff <= lines; lineoff++)
	{
		ItemId		lpp = PageGetItemId(page, lineoff);
		HeapTupleData loctup;
		bool		valid;

		if (!ItemIdIsNormal(lpp))
			continue;

		loctup.t_data = (HeapTupleHeader) PageGetItem(page, lpp);
		loctup.t_len = ItemIdGetLength(lpp);
		loctup.t_tableOid = RelationGetRelid(scan->rs_base.rs_rd);
		ItemPointerSet(&(loctup.t_self), block, lineoff);

		if (all_visible)
			valid = true;
		else
			valid = HeapTupleSatisfiesVisibility(&loctup, snapshot, buffer);

		if (check_serializable)
			HeapCheckForSerializableConflictOut(valid, scan->rs_base.rs_rd,
												&loctup, buffer, snapshot);

		if (valid)
		{
			scan->rs_vistuples[ntup] = lineoff;
			ntup++;
		}
	}

	Assert(ntup <= MaxHeapTuplesPerPage);

	return ntup;
}
```

## 동작 흐름

```text
 L514  for lineoff = 1 .. lines                         FirstOffsetNumber = 1
 L516    lpp = PageGetItemId(page, lineoff)
 L520    !ItemIdIsNormal(lpp) -> 건너뜀                  LP_UNUSED, LP_REDIRECT, LP_DEAD
 L523    loctup.t_data = 페이지 안의 튜플 헤더           복사하지 않는다
 L526    t_self = (block, lineoff)
 L528    all_visible ? true : [07] HeapTupleSatisfiesVisibility
 L533    check_serializable 이면 HeapCheckForSerializableConflictOut
           보이지 않은 튜플도 넘긴다 (valid 를 인자로)
 L537    valid 면 rs_vistuples[ntup++] = lineoff
 L546  return ntup
```

예로 줄 포인터 다섯 개짜리 페이지를 [02] 의 스냅샷 `{xmin 100, xmax 105, xip [100, 103]}` 으로 훑는다. 각 줄의 판정은 [08] 의 규칙을 따른다.

```text
 lineoff  lp      t_xmin  t_xmax  rs_vistuples  판정
 1        NORMAL  90      0       [1]           xmin 끝남(커밋), xmax 없음
 2        DEAD    -       -       [1]           L520 건너뜀
 3        NORMAL  101     103     [1, 3]        xmin 커밋, xmax 103 진행 중 -> 보임
 4        NORMAL  103     0       [1, 3]        xmin 103 진행 중 -> 안 보임
 5        NORMAL  104     0       [1, 3, 5]     xmin 104 커밋

 rs_ntuples = 3
 lineoff 3 은 103 이 지우는 중인 행이다. 103 이 커밋해도 이 스냅샷에는 계속 보인다
```

## 결과가 쓰이는 곳

```text
 반환값 ntup        --> [05] 가 scan->rs_ntuples 에 넣는다
 rs_vistuples[]     --> [04] 가 이 줄 번호들로 튜플을 꺼낸다
```

## 다루지 않는 것

줄 포인터(`ItemIdData`)의 비트 배치와 `LP_*` 상태 전이는 페이지 구조 편 몫이다. SERIALIZABLE 의 `HeapCheckForSerializableConflictOut` 은 요약만 했다.
