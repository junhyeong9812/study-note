# heap_prepare_insert

상위: [행 쓰기와 WAL 기록](../README.md)

**새 행의 헤더에 MVCC 정보를 찍고, 너무 크면 TOAST 로 줄인다.** xmin 에 지금 트랜잭션 ID, cmin 에 이 문장의 command id 를 넣고, xmax 는 "없음"으로 둔다. 이 세 값이 이후 모든 스냅샷이 이 행을 볼지 말지 정하는 근거다. 페이지를 잡기 전에 불리므로, TOAST 처럼 다른 테이블에 쓰는 무거운 일도 여기서 안전하게 할 수 있다.

## 위치

`access` / `heap` / `heapam.c` L2298-L2338 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2298-L2338))

## 실제 코드

`access` / `heap` / `heapam.c` L2291-L2338 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2291-L2338))

```c
// heapam.c L2291-L2338
/*
 * Subroutine for heap_insert(). Prepares a tuple for insertion. This sets the
 * tuple header fields and toasts the tuple if necessary.  Returns a toasted
 * version of the tuple if it was toasted, or the original tuple if not. Note
 * that in any case, the header fields are also set in the original tuple.
 */
static HeapTuple
heap_prepare_insert(Relation relation, HeapTuple tup, TransactionId xid,
					CommandId cid, int options)
{
	/*
	 * To allow parallel inserts, we need to ensure that they are safe to be
	 * performed in workers. We have the infrastructure to allow parallel
	 * inserts in general except for the cases where inserts generate a new
	 * CommandId (eg. inserts into a table having a foreign key column).
	 */
	if (IsParallelWorker())
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_TRANSACTION_STATE),
				 errmsg("cannot insert tuples in a parallel worker")));

	tup->t_data->t_infomask &= ~(HEAP_XACT_MASK);
	tup->t_data->t_infomask2 &= ~(HEAP2_XACT_MASK);
	tup->t_data->t_infomask |= HEAP_XMAX_INVALID;
	HeapTupleHeaderSetXmin(tup->t_data, xid);
	if (options & HEAP_INSERT_FROZEN)
		HeapTupleHeaderSetXminFrozen(tup->t_data);

	HeapTupleHeaderSetCmin(tup->t_data, cid);
	HeapTupleHeaderSetXmax(tup->t_data, 0); /* for cleanliness */
	tup->t_tableOid = RelationGetRelid(relation);

	/*
	 * If the new tuple is too big for storage or contains already toasted
	 * out-of-line attributes from some other relation, invoke the toaster.
	 */
	if (relation->rd_rel->relkind != RELKIND_RELATION &&
		relation->rd_rel->relkind != RELKIND_MATVIEW)
	{
		/* toast table entries should never be recursively toasted */
		Assert(!HeapTupleHasExternal(tup));
		return tup;
	}
	else if (HeapTupleHasExternal(tup) || tup->t_len > TOAST_TUPLE_THRESHOLD)
		return heap_toast_insert_or_update(relation, tup, NULL, options);
	else
		return tup;
}
```

TOAST 를 부르는 기준은 페이지 하나에 행 네 개가 들어가는 크기다.

`src` / `include` / `access` / `heaptoast.h` L23-L26 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/heaptoast.h#L23-L26))

```c
// heaptoast.h L23-L26
#define MaximumBytesPerTuple(tuplesPerPage) \
	MAXALIGN_DOWN((BLCKSZ - \
				   MAXALIGN(SizeOfPageHeaderData + (tuplesPerPage) * sizeof(ItemIdData))) \
				  / (tuplesPerPage))
```

`src` / `include` / `access` / `heaptoast.h` L46-L50 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/heaptoast.h#L46-L50))

```c
// heaptoast.h L46-L50
#define TOAST_TUPLES_PER_PAGE	4

#define TOAST_TUPLE_THRESHOLD	MaximumBytesPerTuple(TOAST_TUPLES_PER_PAGE)

#define TOAST_TUPLE_TARGET		TOAST_TUPLE_THRESHOLD
```

## 동작 흐름

```text
 L2307  병렬 워커 안이면 ERROR             새 command id 가 필요한 경우를 워커가 처리 못 한다 (L2301-L2306)

 L2312  t_infomask  &= ~HEAP_XACT_MASK     가시성 관련 비트 (0xFFF0) 를 모두 지운다
 L2313  t_infomask2 &= ~HEAP2_XACT_MASK    (0xE000)
 L2314  t_infomask  |= HEAP_XMAX_INVALID   "xmax 없음"을 힌트로 미리 박는다
 L2315  xmin = xid
 L2316  HEAP_INSERT_FROZEN 이면 xmin 을 frozen 으로   (COPY FREEZE)
 L2319  cmin = cid                         estate->es_output_cid
 L2320  xmax = 0
 L2321  t_tableOid = 릴레이션 OID

 L2327  일반 테이블도 matview 도 아니면 (TOAST 테이블 자신 등)   그대로 돌려준다
 L2334  외부 저장 값이 있거나 t_len > TOAST_TUPLE_THRESHOLD 면
 L2335    heap_toast_insert_or_update      줄인 사본을 돌려준다
 L2337  아니면 원본 그대로
```

L2294-L2295 주석대로, TOAST 를 해서 사본을 돌려주더라도 헤더 필드는 원본에도 찍힌다. 그래서 [02] 는 끝에서 `t_self` 만 원본에 복사하면 된다.

```text
 헤더에 찍히는 값 (트랜잭션 XID 1000 의 두 번째 문장, command id 1)

 필드          값              다음 단계에서 쓰는 곳
 t_xmin        1000            다른 스냅샷: 1000 이 커밋됐나, 스냅샷 이전인가
 t_cmin        1               같은 트랜잭션: 이 행은 command 1 이 만들었다
                               command 1 의 스냅샷 자신은 이 행을 보지 않는다
                               (cmin >= curcid, heapam_visibility.c L1023)
 t_xmax        0
 t_infomask    XMAX_INVALID    가시성 검사가 xmax 를 확인하지 않고 지나간다 (같은 파일 L1086)
               (XMIN_COMMITTED 는 아직 없다. 커밋 뒤 누군가 처음 확인할 때 힌트로 찍힌다)
```

TOAST 기준은 소스 규칙으로 계산할 수 있다. 기본 빌드(BLCKSZ 8192, MAXALIGN 8)에서는 2032 바이트다.

```text
 TOAST_TUPLE_THRESHOLD = MaximumBytesPerTuple(4)        heaptoast.h L48

   SizeOfPageHeaderData + 4 * sizeof(ItemIdData) = 24 + 16 = 40      MAXALIGN(40) = 40
   (8192 - 40) / 4 = 2038
   MAXALIGN_DOWN(2038) = 2032

 t_len 2000   -> 그대로
 t_len 2040   -> heap_toast_insert_or_update 가 열을 압축하거나 TOAST 테이블로 옮겨 줄인다
```

## 결과가 쓰이는 곳

```text
 heaptup (원본 또는 TOAST 된 사본)
      --> [02] 가 heaptup->t_len 으로 [04] 에 공간을 요청한다
      --> [05] 가 그 바이트를 페이지에 복사한다
 t_xmin, t_cmin, t_infomask
      --> [MVCC 가시성과 스냅샷] HeapTupleSatisfiesMVCC 가 읽는다
      --> [02] 의 xl_heap_header 에 t_infomask, t_infomask2 가 실린다 (xmin 은 레코드의 xl_xid 로)
```

## 다루지 않는 것

TOAST 의 압축과 외부 저장 절차(`heap_toast_insert_or_update`, `toast_save_datum`), combo CID(같은 행을 같은 트랜잭션이 지울 때 cmin 과 cmax 를 겹쳐 쓰는 방식), 힌트 비트를 나중에 찍는 `SetHintBits` 는 헤더 준비의 곁가지라 요약만 했다.
