# btinsert

상위: [nbtree 삽입과 분할](../README.md)

**B-tree 의 `aminsert` 다.** 키 값들로 인덱스 튜플을 만들고, 그 튜플이 가리킬 힙 TID 를 붙여 `_bt_doinsert` 에 넘긴다. 트리를 내려가고 쪼개는 일은 전부 그 아래에서 일어난다.

## 위치

`access` / `nbtree` / `nbtree.c` L202-L220 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtree.c#L202-L220))

## 실제 코드

`access` / `nbtree` / `nbtree.c` L195-L220 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtree.c#L195-L220))

```c
// nbtree.c L195-L220
/*
 *	btinsert() -- insert an index tuple into a btree.
 *
 *		Descend the tree recursively, find the appropriate location for our
 *		new tuple, and put it there.
 */
bool
btinsert(Relation rel, Datum *values, bool *isnull,
		 ItemPointer ht_ctid, Relation heapRel,
		 IndexUniqueCheck checkUnique,
		 bool indexUnchanged,
		 IndexInfo *indexInfo)
{
	bool		result;
	IndexTuple	itup;

	/* generate an index tuple */
	itup = index_form_tuple(RelationGetDescr(rel), values, isnull);
	itup->t_tid = *ht_ctid;

	result = _bt_doinsert(rel, itup, checkUnique, indexUnchanged, heapRel);

	pfree(itup);

	return result;
}
```

튜플 크기는 `index_form_tuple_context` 에서 정해진다. 헤더 뒤에 데이터를 붙이고 전체를 MAXALIGN 한다.

`access` / `common` / `indextuple.c` L154-L164 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/common/indextuple.c#L154-L164))

```c
// indextuple.c L154-L164
	hoff = IndexInfoFindDataOffset(infomask);
#ifdef TOAST_INDEX_HACK
	data_size = heap_compute_data_size(tupleDescriptor,
									   untoasted_values, isnull);
#else
	data_size = heap_compute_data_size(tupleDescriptor,
									   values, isnull);
#endif
	size = hoff + data_size;
	size = MAXALIGN(size);		/* be conservative */

```

## 동작 흐름

```text
 btinsert(rel, values, isnull, ht_ctid, heapRel, checkUnique, indexUnchanged, ...)
   L212  itup = index_form_tuple(desc, values, isnull)    키만 담긴 튜플
   L213  itup->t_tid = *ht_ctid                           힙 튜플 위치를 박는다
   L215  result = _bt_doinsert(...)                       --> [04]
   L217  pfree(itup)
   L219  return result
```

리프의 인덱스 튜플은 "키 + 힙 TID" 한 쌍이다. 아래는 `int4` 열 하나짜리 인덱스에서 튜플 하나가 차지하는 바이트를 소스 규칙대로 센 것이다. 이 16바이트가 뒤의 분할 예시에서 쓰는 크기다.

```text
 int4 키 하나, NULL 없음 (64비트 빌드, MAXALIGN = 8)

 off  크기  내용
 0    6     t_tid (ItemPointerData: 블록 4 + 오프셋 2)    itup.h L37
 6    2     t_info (크기 13비트 + 플래그)                  itup.h L49
 8    4     int4 키 값
 12   4     MAXALIGN 패딩

 hoff = IndexInfoFindDataOffset = MAXALIGN(8) = 8              indextuple.c L154
 size = hoff + data_size = 8 + 4 = 12 -> MAXALIGN -> 16        indextuple.c L162-L163
 페이지에는 여기에 라인 포인터(ItemIdData) 4바이트가 더 붙어 항목 하나 = 20바이트
```

## 결과가 쓰이는 곳

```text
 itup
      --> [04] _bt_doinsert 가 insertion scankey 를 만들고 (_bt_mkscankey)
          itemsz = MAXALIGN(IndexTupleSize(itup)) 로 공간 계산에 쓴다
      --> 리프에 그대로 들어가거나, 중복이면 dedup 으로 posting list 에 합쳐진다

 반환값
      --> UNIQUE_CHECK_PARTIAL 일 때 "확실히 유일한가"
```

## 다루지 않는 것

`index_form_tuple` 의 TOAST 압축과 가변 길이 처리, NULL 비트맵, INCLUDE 열(키가 아닌 열)은 다루지 않는다.
