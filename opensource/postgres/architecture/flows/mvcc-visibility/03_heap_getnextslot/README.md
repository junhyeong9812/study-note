# heap_getnextslot

상위: [MVCC 가시성과 스냅샷](../README.md)

**executor 의 SeqScan 이 "다음 행"을 달라고 할 때 heap 이 받는 입구다.** 스캔이 page-at-a-time 모드면 [04] `heapgettup_pagemode` 로, 아니면 `heapgettup` 으로 갈라 보내고, 받은 튜플을 슬롯에 담아 돌려준다. 스냅샷이 MVCC 가 아니면 page 모드는 처음부터 꺼져 있다.

## 위치

`access/heap` / `heapam.c` L1388-L1415 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L1388-L1415))

## 실제 코드

```c
// heapam.c L1387-L1415
bool
heap_getnextslot(TableScanDesc sscan, ScanDirection direction, TupleTableSlot *slot)
{
	HeapScanDesc scan = (HeapScanDesc) sscan;

	/* Note: no locking manipulations needed */

	if (sscan->rs_flags & SO_ALLOW_PAGEMODE)
		heapgettup_pagemode(scan, direction, sscan->rs_nkeys, sscan->rs_key);
	else
		heapgettup(scan, direction, sscan->rs_nkeys, sscan->rs_key);

	if (scan->rs_ctup.t_data == NULL)
	{
		ExecClearTuple(slot);
		return false;
	}

	/*
	 * if we get here it means we have a new current scan tuple, so point to
	 * the proper return buffer and return the tuple.
	 */

	pgstat_count_heap_getnext(scan->rs_base.rs_rd);

	ExecStoreBufferHeapTuple(&scan->rs_ctup, slot,
							 scan->rs_cbuf);
	return true;
}
```

page 모드를 끄는 곳은 `heap_beginscan` 이다. 스냅샷이 MVCC 계열일 때만 남는다.

`access/heap` / `heapam.c` L1144-L1148 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L1144-L1148))

```c
// heapam.c L1144-L1148
	/*
	 * Disable page-at-a-time mode if it's not a MVCC-safe snapshot.
	 */
	if (!(snapshot && IsMVCCSnapshot(snapshot)))
		scan->rs_base.rs_flags &= ~SO_ALLOW_PAGEMODE;
```

executor 쪽 호출이다. `SeqNext` 가 `estate->es_snapshot` 으로 스캔을 열고 한 행씩 받는다.

`executor` / `nodeSeqscan.c` L66-L83 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeSeqscan.c#L66-L83))

```c
// nodeSeqscan.c L66-L83
	if (scandesc == NULL)
	{
		/*
		 * We reach here if the scan is not parallel, or if we're serially
		 * executing a scan that was planned to be parallel.
		 */
		scandesc = table_beginscan(node->ss.ss_currentRelation,
								   estate->es_snapshot,
								   0, NULL);
		node->ss.ss_currentScanDesc = scandesc;
	}

	/*
	 * get the next tuple from the table
	 */
	if (table_scan_getnextslot(scandesc, direction, slot))
		return slot;
	return NULL;
```

## 동작 흐름

```text
 SeqNext (nodeSeqscan.c)
   L72  table_beginscan(rel, estate->es_snapshot, 0, NULL)    첫 호출에만
          -> heap_beginscan (heapam_handler.c L2621 .scan_begin)
               heapam.c L1147  MVCC 스냅샷이 아니면 SO_ALLOW_PAGEMODE 를 뺀다
   L81  table_scan_getnextslot
          -> rd_tableam->scan_getnextslot (tableam.h L1036)
          -> heap_getnextslot (heapam_handler.c L2624)

 heap_getnextslot
   L1394  SO_ALLOW_PAGEMODE ?
            예   [04] heapgettup_pagemode    페이지 단위로 미리 판정해 둔 목록을 쓴다
            아니오    heapgettup             호출마다 잠그고 튜플마다 판정한다 (heapam.c L955)
   L1399  rs_ctup.t_data == NULL  -> 스캔 끝. 슬롯을 비우고 false
   L1410  pgstat 카운트
   L1412  ExecStoreBufferHeapTuple(&rs_ctup, slot, rs_cbuf)
            슬롯이 버퍼를 참조로 들고 간다 (복사하지 않는다)
```

두 모드의 차이는 "버퍼 잠금을 언제 잡는가"와 "가시성을 언제 판정하는가"다.

```text
 page 모드 (MVCC 스냅샷)
   판정 시점        페이지를 처음 읽을 때 한꺼번에
   share 잠금       [05] 안에서 한 번 잡고 푼다
   결과 보관        rs_vistuples[] (보이는 줄 번호)
   이후 보장        pin 만 들고 있으면 보인 튜플이 유효 ([05] 주석 heapam.c L579-L581)

 튜플 모드 (그 밖의 스냅샷)
   판정 시점        튜플을 돌려줄 때마다
   share 잠금       호출마다 잡고, 튜플 하나를 돌려주기 전에 푼다 (heapam.c L913, L932, L973)
   결과 보관        없음
```

## 결과가 쓰이는 곳

```text
 slot (BufferHeapTupleTableSlot)
      --> SeqNext 가 돌려주고 ExecScan 이 qual 과 projection 을 적용한다 [executor]
      --> 슬롯이 rs_cbuf 를 참조하므로 그 페이지는 pin 이 유지된다
```

## 다루지 않는 것

page 모드가 아닌 `heapgettup`(SnapshotAny, SnapshotDirty 같은 비 MVCC 스캔), 병렬 seqscan 의 블록 배분, TID 범위 스캔 `heap_getnextslot_tidrange`, `ExecStoreBufferHeapTuple` 의 슬롯 내부는 요약만 했다.
