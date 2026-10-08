# heapgettup_pagemode

상위: [MVCC 가시성과 스냅샷](../README.md)

**page 모드 스캔의 바퀴다.** 다음 페이지를 받아 [05] `heap_prepare_pagescan` 으로 보이는 튜플 목록 `rs_vistuples[]` 를 만들고, 그 목록에서 하나씩 꺼내 돌려준다. 이 함수 자신은 버퍼 내용 잠금을 잡지 않고 가시성도 판정하지 않는다.

## 위치

`access/heap` / `heapam.c` L1010-L1094 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L1010-L1094))

## 실제 코드

```c
// heapam.c L996-L1094
/* ----------------
 *		heapgettup_pagemode - fetch next heap tuple in page-at-a-time mode
 *
 *		Same API as heapgettup, but used in page-at-a-time mode
 *
 * The internal logic is much the same as heapgettup's too, but there are some
 * differences: we do not take the buffer content lock (that only needs to
 * happen inside heap_prepare_pagescan), and we iterate through just the
 * tuples listed in rs_vistuples[] rather than all tuples on the page.  Notice
 * that lineindex is 0-based, where the corresponding loop variable lineoff in
 * heapgettup is 1-based.
 * ----------------
 */
static void
heapgettup_pagemode(HeapScanDesc scan,
					ScanDirection dir,
					int nkeys,
					ScanKey key)
{
	HeapTuple	tuple = &(scan->rs_ctup);
	Page		page;
	uint32		lineindex;
	uint32		linesleft;

	if (likely(scan->rs_inited))
	{
		/* continue from previously returned page/tuple */
		page = BufferGetPage(scan->rs_cbuf);

		lineindex = scan->rs_cindex + dir;
		if (ScanDirectionIsForward(dir))
			linesleft = scan->rs_ntuples - lineindex;
		else
			linesleft = scan->rs_cindex;
		/* lineindex now references the next or previous visible tid */

		goto continue_page;
	}

	/*
	 * advance the scan until we find a qualifying tuple or run out of stuff
	 * to scan
	 */
	while (true)
	{
		heap_fetch_next_buffer(scan, dir);

		/* did we run out of blocks to scan? */
		if (!BufferIsValid(scan->rs_cbuf))
			break;

		Assert(BufferGetBlockNumber(scan->rs_cbuf) == scan->rs_cblock);

		/* prune the page and determine visible tuple offsets */
		heap_prepare_pagescan((TableScanDesc) scan);
		page = BufferGetPage(scan->rs_cbuf);
		linesleft = scan->rs_ntuples;
		lineindex = ScanDirectionIsForward(dir) ? 0 : linesleft - 1;

		/* block is the same for all tuples, set it once outside the loop */
		ItemPointerSetBlockNumber(&tuple->t_self, scan->rs_cblock);

		/* lineindex now references the next or previous visible tid */
continue_page:

		for (; linesleft > 0; linesleft--, lineindex += dir)
		{
			ItemId		lpp;
			OffsetNumber lineoff;

			Assert(lineindex < scan->rs_ntuples);
			lineoff = scan->rs_vistuples[lineindex];
			lpp = PageGetItemId(page, lineoff);
			Assert(ItemIdIsNormal(lpp));

			tuple->t_data = (HeapTupleHeader) PageGetItem(page, lpp);
			tuple->t_len = ItemIdGetLength(lpp);
			ItemPointerSetOffsetNumber(&tuple->t_self, lineoff);

			/* skip any tuples that don't match the scan key */
			if (key != NULL &&
				!HeapKeyTest(tuple, RelationGetDescr(scan->rs_base.rs_rd),
							 nkeys, key))
				continue;

			scan->rs_cindex = lineindex;
			return;
		}
	}

	/* end of scan */
	if (BufferIsValid(scan->rs_cbuf))
		ReleaseBuffer(scan->rs_cbuf);
	scan->rs_cbuf = InvalidBuffer;
	scan->rs_cblock = InvalidBlockNumber;
	scan->rs_prefetch_block = InvalidBlockNumber;
	tuple->t_data = NULL;
	scan->rs_inited = false;
}
```

다음 페이지는 read stream 에서 받는다. 앞 페이지의 pin 을 여기서 놓는다.

`access/heap` / `heapam.c` L647-L682 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L647-L682))

```c
// heapam.c L647-L682
heap_fetch_next_buffer(HeapScanDesc scan, ScanDirection dir)
{
	Assert(scan->rs_read_stream);

	/* release previous scan buffer, if any */
	if (BufferIsValid(scan->rs_cbuf))
	{
		ReleaseBuffer(scan->rs_cbuf);
		scan->rs_cbuf = InvalidBuffer;
	}

// ... (L658-L662 생략: 인터럽트 확인 주석)
	CHECK_FOR_INTERRUPTS();

// ... (L665-L670 생략: 방향 전환 주석)
	if (unlikely(scan->rs_dir != dir))
	{
		scan->rs_prefetch_block = scan->rs_cblock;
		read_stream_reset(scan->rs_read_stream);
	}

	scan->rs_dir = dir;

	scan->rs_cbuf = read_stream_next_buffer(scan->rs_read_stream, NULL);
	if (BufferIsValid(scan->rs_cbuf))
		scan->rs_cblock = BufferGetBlockNumber(scan->rs_cbuf);
}
```

## 동작 흐름

```text
 L1020  rs_inited (이미 페이지 안에서 돌고 있음)
          L1025  lineindex = rs_cindex + dir       직전 위치의 다음 칸
          L1032  goto continue_page                새 페이지를 읽지 않는다

 L1039  while (true)                               새 페이지
 L1041    heap_fetch_next_buffer
            L654  이전 rs_cbuf 를 ReleaseBuffer      (pin 해제)
            L663  CHECK_FOR_INTERRUPTS               페이지마다 한 번
            L679  read_stream_next_buffer           --> [버퍼 관리] pin 된 버퍼
 L1044    버퍼가 없으면 break                       스캔 끝
 L1050    [05] heap_prepare_pagescan               prune, share 잠금, 판정, 잠금 해제
 L1052    linesleft = rs_ntuples                   보이는 튜플 수
 L1053    정방향이면 lineindex = 0

 L1061  for (; linesleft > 0; ...)                 continue_page
 L1067    lineoff = rs_vistuples[lineindex]        보이는 튜플만 돈다
 L1071    tuple->t_data = PageGetItem(...)         페이지 안을 가리킨다 (복사 없음)
 L1076    scan key 가 있으면 HeapKeyTest           SeqScan 은 key 없이 연다 (nodeSeqscan.c L74)
 L1081    rs_cindex 기억, return
          목록을 다 쓰면 while 로 돌아가 다음 페이지

 L1087  끝: rs_cbuf 를 놓고 t_data = NULL          [03] 이 false 를 돌려준다
```

한 페이지 안에서의 시간축을 세우면 잠금과 pin 의 길이가 다르다.

```text
 페이지 P 한 장의 수명 (위에서 아래로)

 단계                                   pin   share 잠금   rs_vistuples
 ------------------------------------   ---   ----------   ------------
 L1041 read_stream_next_buffer          +
 [05] L583 LockBuffer(SHARE)            |     +
 [05] page_collect_tuples               |     |            채움
 [05] L637 LockBuffer(UNLOCK)           |     -            |
 L1061 튜플 1 반환 -> executor          |                  |
 L1061 튜플 2 반환 -> executor          |                  |
 ...                                    |                  |
 다음 L1041 의 L654 ReleaseBuffer       -                  다음 페이지로 덮임

 잠금은 판정하는 동안만, pin 은 페이지를 다 돌려줄 때까지
 그 사이 다른 backend 가 새 튜플을 넣어도 rs_vistuples 는 바뀌지 않는다
```

## 결과가 쓰이는 곳

```text
 scan->rs_ctup
      --> [03] heap_getnextslot 이 슬롯에 담는다
 scan->rs_cindex
      --> 다음 호출이 L1025 에서 이어 간다
```

## 다루지 않는 것

read stream 이 다음 블록 번호를 고르는 콜백(`heap_scan_stream_read_next_serial`, 병렬 쪽)과 `syncscan`, 역방향 스캔의 세부, `HeapKeyTest` 는 요약만 했다. 버퍼를 읽어 오는 과정은 [버퍼 관리](../../buffer-manager/README.md)에 있다.
