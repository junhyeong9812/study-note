# heapam_tuple_insert

상위: [행 쓰기와 WAL 기록](../README.md)

**executor 의 슬롯 세계와 힙의 튜플 세계를 잇는 table AM 콜백이다.** executor 는 테이블 종류를 모른 채 `table_tuple_insert` 를 부르고, 힙 테이블이면 함수 포인터가 이 함수로 간다. 슬롯에서 `HeapTuple` 을 꺼내 `heap_insert` 에 넘기고, 힙이 정한 위치(TID)를 슬롯에 되돌려 적는다.

## 위치

`access` / `heap` / `heapam_handler.c` L244-L260 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_handler.c#L244-L260))

## 실제 코드

executor 쪽 입구는 `tableam.h` 의 인라인 함수다. 릴레이션의 table AM 함수 표에서 `tuple_insert` 를 부른다.

`src` / `include` / `access` / `tableam.h` L1366-L1372 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/tableam.h#L1366-L1372))

```c
// tableam.h L1366-L1372
static inline void
table_tuple_insert(Relation rel, TupleTableSlot *slot, CommandId cid,
				   int options, struct BulkInsertStateData *bistate)
{
	rel->rd_tableam->tuple_insert(rel, slot, cid, options,
								  bistate);
}
```

힙 AM 의 함수 표에 이 함수가 등록되어 있다.

`access` / `heap` / `heapam_handler.c` L2638-L2639 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_handler.c#L2638-L2639))

```c
// heapam_handler.c L2638-L2639
	.tuple_insert = heapam_tuple_insert,
	.tuple_insert_speculative = heapam_tuple_insert_speculative,
```

본체다.

`access` / `heap` / `heapam_handler.c` L243-L260 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_handler.c#L243-L260))

```c
// heapam_handler.c L243-L260
static void
heapam_tuple_insert(Relation relation, TupleTableSlot *slot, CommandId cid,
					int options, BulkInsertState bistate)
{
	bool		shouldFree = true;
	HeapTuple	tuple = ExecFetchSlotHeapTuple(slot, true, &shouldFree);

	/* Update the tuple with table oid */
	slot->tts_tableOid = RelationGetRelid(relation);
	tuple->t_tableOid = slot->tts_tableOid;

	/* Perform the insertion, and copy the resulting ItemPointer */
	heap_insert(relation, tuple, cid, options, bistate);
	ItemPointerCopy(&tuple->t_self, &slot->tts_tid);

	if (shouldFree)
		pfree(tuple);
}
```

## 동작 흐름

```text
 table_tuple_insert(rel, slot, cid, options, bistate)          tableam.h L1367
   L1370  rel->rd_tableam->tuple_insert(...)                   힙이면 heapam_tuple_insert

 heapam_tuple_insert
   L248  tuple = ExecFetchSlotHeapTuple(slot, true, &shouldFree)
           슬롯이 이미 힙 튜플을 들고 있으면 그것, 아니면 새로 만들어 준다
           (shouldFree = true 면 이 함수가 만든 사본이다)
   L251  slot->tts_tableOid = 이 릴레이션 OID
   L252  tuple->t_tableOid  = 같은 값
   L255  heap_insert(relation, tuple, cid, options, bistate)    --> [02]
           돌아오면 tuple->t_self = (블록 번호, 줄 번호)
   L256  ItemPointerCopy(&tuple->t_self, &slot->tts_tid)
   L258  사본이었으면 pfree
```

executor 가 보는 결과는 슬롯의 `tts_tid` 하나다. 이 값이 다음 단계인 인덱스 삽입의 입력이 된다.

```text
 executor 와 힙 사이에서 오가는 것

 executor (nodeModifyTable.c)              table AM 경계                  힙 (heapam.c)
 ----------------------------              -------------                  -------------
 slot (values, tts_tableOid)      ---->    ExecFetchSlotHeapTuple  ---->  HeapTuple (t_data, t_len)
 estate->es_output_cid            ---->    cid                     ---->  cmin 으로 찍힌다 ([03])
 options = 0, bistate = NULL      ---->                            ---->  FSM 사용, 일반 버퍼 전략
                                                                          t_self = (7, 3)
 slot->tts_tid = (7, 3)           <----    ItemPointerCopy         <----
 ExecInsertIndexTuples(slot)      ---->    인덱스 항목이 (7, 3) 을 가리킨다
```

## 결과가 쓰이는 곳

```text
 slot->tts_tid
      --> [executor] ExecInsert L1240 의 ExecInsertIndexTuples (execIndexing.c L319)
      --> RETURNING ctid, AFTER ROW 트리거의 NEW 행 위치
 slot->tts_tableOid
      --> RETURNING tableoid, 파티션 테이블에서 실제로 들어간 파티션
```

## 다루지 않는 것

table AM 인터페이스 전체(`TableAmRoutine` 의 다른 콜백), 슬롯 종류별 `ExecFetchSlotHeapTuple` 동작(virtual, heap, buffer heap 슬롯), `bistate`(대량 삽입 상태)와 `options` 플래그(`TABLE_INSERT_SKIP_FSM`, `TABLE_INSERT_FROZEN`)는 AM 경계의 곁가지라 요약만 했다.
