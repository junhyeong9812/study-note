# HeapTupleSatisfiesVisibility

상위: [MVCC 가시성과 스냅샷](../README.md)

**스냅샷 종류에 따라 판정 함수를 고르는 switch 다.** 일반 질의의 스냅샷은 `SNAPSHOT_MVCC` 라서 [08] `HeapTupleSatisfiesMVCC` 로 간다. 호출자는 버퍼 pin 과 최소 share 잠금을 들고 있어야 하고, 판정 중에 힌트 비트가 바뀌면 버퍼가 dirty 로 표시된다.

## 위치

`access/heap` / `heapam_visibility.c` L1776-L1797 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_visibility.c#L1776-L1797))

## 실제 코드

```c
// heapam_visibility.c L1765-L1797
/*
 * HeapTupleSatisfiesVisibility
 *		True iff heap tuple satisfies a time qual.
 *
 * Notes:
 *	Assumes heap tuple is valid, and buffer at least share locked.
 *
 *	Hint bits in the HeapTuple's t_infomask may be updated as a side effect;
 *	if so, the indicated buffer is marked dirty.
 */
bool
HeapTupleSatisfiesVisibility(HeapTuple htup, Snapshot snapshot, Buffer buffer)
{
	switch (snapshot->snapshot_type)
	{
		case SNAPSHOT_MVCC:
			return HeapTupleSatisfiesMVCC(htup, snapshot, buffer);
		case SNAPSHOT_SELF:
			return HeapTupleSatisfiesSelf(htup, snapshot, buffer);
		case SNAPSHOT_ANY:
			return HeapTupleSatisfiesAny(htup, snapshot, buffer);
		case SNAPSHOT_TOAST:
			return HeapTupleSatisfiesToast(htup, snapshot, buffer);
		case SNAPSHOT_DIRTY:
			return HeapTupleSatisfiesDirty(htup, snapshot, buffer);
		case SNAPSHOT_HISTORIC_MVCC:
			return HeapTupleSatisfiesHistoricMVCC(htup, snapshot, buffer);
		case SNAPSHOT_NON_VACUUMABLE:
			return HeapTupleSatisfiesNonVacuumable(htup, snapshot, buffer);
	}

	return false;				/* keep compiler quiet */
}
```

파일 머리 주석이 함수들을 한 줄씩 요약한다. 이 흐름이 쓰는 것은 첫 줄이다.

`access/heap` / `heapam_visibility.c` L38-L56 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_visibility.c#L38-L56))

```c
// heapam_visibility.c L38-L56
 * Summary of visibility functions:
 *
 *	 HeapTupleSatisfiesMVCC()
 *		  visible to supplied snapshot, excludes current command
 *	 HeapTupleSatisfiesUpdate()
 *		  visible to instant snapshot, with user-supplied command
 *		  counter and more complex result
 *	 HeapTupleSatisfiesSelf()
 *		  visible to instant snapshot and current command
 *	 HeapTupleSatisfiesDirty()
 *		  like HeapTupleSatisfiesSelf(), but includes open transactions
 *	 HeapTupleSatisfiesVacuum()
 *		  visible to any running transaction, used by VACUUM
 *	 HeapTupleSatisfiesNonVacuumable()
 *		  Snapshot-style API for HeapTupleSatisfiesVacuum
 *	 HeapTupleSatisfiesToast()
 *		  visible unless part of interrupted vacuum, used for TOAST
 *	 HeapTupleSatisfiesAny()
 *		  all tuples are visible
```

## 동작 흐름

```text
 snapshot->snapshot_type        판정 함수                         한 줄 요약 (머리 주석)
 SNAPSHOT_MVCC                  [08] HeapTupleSatisfiesMVCC        스냅샷 기준, 현재 명령은 제외
 SNAPSHOT_SELF                  HeapTupleSatisfiesSelf             지금 순간 기준, 현재 명령 포함
 SNAPSHOT_ANY                   HeapTupleSatisfiesAny              전부 보임
 SNAPSHOT_TOAST                 HeapTupleSatisfiesToast            중단된 vacuum 흔적만 제외
 SNAPSHOT_DIRTY                 HeapTupleSatisfiesDirty            Self + 진행 중 트랜잭션 포함
 SNAPSHOT_HISTORIC_MVCC         HeapTupleSatisfiesHistoricMVCC     논리 디코딩
 SNAPSHOT_NON_VACUUMABLE        HeapTupleSatisfiesNonVacuumable    아직 누군가에게 보일 수 있음
```

이 switch 를 지나는 호출자는 page 모드 스캔만이 아니다. 같은 판정이 여러 읽기 경로에서 쓰인다.

```text
 HeapTupleSatisfiesVisibility 를 부르는 곳 (heapam.c, heapam_handler.c)

 heapam.c L531           [06] page_collect_tuples         seqscan page 모드
 heapam.c L955           heapgettup                       seqscan 튜플 모드
 heapam.c L1663          heap_fetch                       TID 로 한 행
 heapam.c L1806          heap_hot_search_buffer           인덱스 스캔이 HOT 체인을 따라갈 때
 heapam.c L1951          heap_get_latest_tid              ctid 를 따라 최신 버전 찾기
 heapam.c L3040          heap_delete 의 crosscheck 스냅샷 (RI 검사용)
 heapam_handler.c L230   heapam_tuple_satisfies_snapshot
 heapam_handler.c L2449  SampleHeapTupleVisible           TABLESAMPLE
 heapam_handler.c L2579  BitmapHeapScanNextBlock          bitmap heap 스캔
```

## 결과가 쓰이는 곳

```text
 bool 반환
      --> true 면 [06] 이 rs_vistuples 에 줄 번호를 넣는다
 힌트 비트 (부수 효과)
      --> t_infomask 와 버퍼 dirty 표시. 다음 방문자는 [10] 의 pg_xact 조회를 건너뛴다
```

## 다루지 않는 것

MVCC 가 아닌 판정 함수 여섯 개의 규칙, UPDATE 와 DELETE 가 쓰는 `HeapTupleSatisfiesUpdate`, vacuum 이 쓰는 `HeapTupleSatisfiesVacuum` 은 이 흐름 밖이다. vacuum 쪽은 [vacuum](../../vacuum/README.md)에서 다룬다.
