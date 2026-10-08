# index_insert

상위: [nbtree 삽입과 분할](../README.md)

**인덱스 AM 이 무엇이든 같은 모양으로 부르는 얇은 분기점이다.** 관계 검사를 하고, AM 이 술어 잠금(predicate lock)을 스스로 다루지 않으면 여기서 SSI 충돌 검사를 대신 한 뒤, `rd_indam->aminsert` 함수 포인터로 넘긴다. B-tree 에서 그 포인터는 `btinsert` 다.

## 위치

`access` / `index` / `indexam.c` L213-L234 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/index/indexam.c#L213-L234))

## 실제 코드

`access` / `index` / `indexam.c` L213-L234 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/index/indexam.c#L213-L234))

```c
// indexam.c L213-L234
index_insert(Relation indexRelation,
			 Datum *values,
			 bool *isnull,
			 ItemPointer heap_t_ctid,
			 Relation heapRelation,
			 IndexUniqueCheck checkUnique,
			 bool indexUnchanged,
			 IndexInfo *indexInfo)
{
	RELATION_CHECKS;
	CHECK_REL_PROCEDURE(aminsert);

	if (!(indexRelation->rd_indam->ampredlocks))
		CheckForSerializableConflictIn(indexRelation,
									   (ItemPointer) NULL,
									   InvalidBlockNumber);

	return indexRelation->rd_indam->aminsert(indexRelation, values, isnull,
											 heap_t_ctid, heapRelation,
											 checkUnique, indexUnchanged,
											 indexInfo);
}
```

B-tree 핸들러가 함수 포인터를 채우는 곳이다.

`access` / `nbtree` / `nbtree.c` L135-L135 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtree.c#L135-L135))

```c
// nbtree.c L135-L135
	amroutine->ampredlocks = true;
```

`access` / `nbtree` / `nbtree.c` L147-L147 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/nbtree/nbtree.c#L147-L147))

```c
// nbtree.c L147-L147
	amroutine->aminsert = btinsert;
```

## 동작 흐름

```text
 index_insert(indexRelation, values, isnull, heap_t_ctid, ...)
   RELATION_CHECKS              L75-L84 매크로. REINDEX 중인 인덱스면 에러
   CHECK_REL_PROCEDURE(aminsert) L93-L98 매크로. 포인터가 비었으면 에러

   ampredlocks?
     false -> CheckForSerializableConflictIn(index, NULL, InvalidBlockNumber)
              인덱스 전체를 하나의 단위로 보고 SSI 충돌을 검사한다
     true  -> 건너뜀. B-tree 는 true 라서 (nbtree.c L135)
              [04] _bt_doinsert 가 실제로 넣을 리프 블록으로 검사한다

   rd_indam->aminsert(...)       B-tree 면 btinsert (nbtree.c L147)  --> [03]
```

```text
 AM 별 aminsert (같은 자리에 다른 함수가 꽂힌다, 줄은 amroutine->aminsert 대입)

 B-tree   btinsert      access/nbtree/nbtree.c    L147
 hash     hashinsert    access/hash/hash.c        L90
 GiST     gistinsert    access/gist/gist.c        L91
 GIN      gininsert     access/gin/ginutil.c      L70
 BRIN     brininsert    access/brin/brin.c        L282
 SP-GiST  spginsert     access/spgist/spgutils.c  L76
```

이 흐름은 B-tree 줄만 따라간다.

## 결과가 쓰이는 곳

```text
 반환값 bool
      --> UNIQUE_CHECK_PARTIAL 일 때만 의미가 있다
          false 면 [01] 이 이 인덱스를 재검사 목록에 넣는다
```

## 다루지 않는 것

다른 AM 의 삽입 함수, SSI(직렬화 가능 격리)의 술어 잠금 자료구조, 인덱스를 다 넣은 뒤 부르는 `index_insert_cleanup` 은 다루지 않는다.
