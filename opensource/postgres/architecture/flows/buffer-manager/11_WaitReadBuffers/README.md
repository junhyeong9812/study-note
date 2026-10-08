# WaitReadBuffers

상위: [버퍼 관리](../README.md)

**PG18 읽기 API 의 뒤쪽 절반이다.** [03] 이 `true` 를 돌려준 읽기 작업에 대해, 걸려 있는 AIO 가 끝났는지 보고 안 끝났으면 기다린 다음 결과를 처리한다. 요청한 블록이 전부 유효해질 때까지(`nblocks_done == nblocks`) 돈다. 부분 읽기였거나 `io_method = sync` 라서 아직 I/O 를 시작하지 않았으면 그 자리에서 [10] `AsyncReadBuffers` 를 다시 부른다. 돌아올 때 `operation->buffers` 의 블록은 모두 `BM_VALID` 다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L1640-L1753 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1640-L1753))

## 실제 코드

```c
// bufmgr.c L1640-L1753
void
WaitReadBuffers(ReadBuffersOperation *operation)
{
	PgAioReturn *aio_ret = &operation->io_return;
	IOContext	io_context;
	IOObject	io_object;

	if (operation->persistence == RELPERSISTENCE_TEMP)
	{
		io_context = IOCONTEXT_NORMAL;
		io_object = IOOBJECT_TEMP_RELATION;
	}
	else
	{
		io_context = IOContextForStrategy(operation->strategy);
		io_object = IOOBJECT_RELATION;
	}

	/*
	 * If we get here without an IO operation having been issued, the
	 * io_method == IOMETHOD_SYNC path must have been used. Otherwise the
	 * caller should not have called WaitReadBuffers().
	 *
	 * In the case of IOMETHOD_SYNC, we start - as we used to before the
	 * introducing of AIO - the IO in WaitReadBuffers(). This is done as part
	 * of the retry logic below, no extra code is required.
	 *
	 * This path is expected to eventually go away.
	 */
	if (!pgaio_wref_valid(&operation->io_wref) && io_method != IOMETHOD_SYNC)
		elog(ERROR, "waiting for read operation that didn't read");

	/*
	 * To handle partial reads, and IOMETHOD_SYNC, we re-issue IO until we're
	 * done. We may need multiple retries, not just because we could get
	 * multiple partial reads, but also because some of the remaining
	 * to-be-read buffers may have been read in by other backends, limiting
	 * the IO size.
	 */
	while (true)
	{
		int			ignored_nblocks_progress;

		CheckReadBuffersOperation(operation, false);

		/*
		 * If there is an IO associated with the operation, we may need to
		 * wait for it.
		 */
		if (pgaio_wref_valid(&operation->io_wref))
		{
			// ... (L1691-L1700 생략: 대기 시간을 재기 전에 완료부터 보는 이유 주석)
			if (aio_ret->result.status == PGAIO_RS_UNKNOWN &&
				!pgaio_wref_check_done(&operation->io_wref))
			{
				instr_time	io_start = pgstat_prepare_io_time(track_io_timing);

				pgaio_wref_wait(&operation->io_wref);

				/*
				 * The IO operation itself was already counted earlier, in
				 * AsyncReadBuffers(), this just accounts for the wait time.
				 */
				pgstat_count_io_op_time(io_object, io_context, IOOP_READ,
										io_start, 0, 0);
			}
			else
			{
				Assert(pgaio_wref_check_done(&operation->io_wref));
			}

			/*
			 * We now are sure the IO completed. Check the results. This
			 * includes reporting on errors if there were any.
			 */
			ProcessReadBuffersResult(operation);
		}

		/*
		 * Most of the time, the one IO we already started, will read in
		 * everything.  But we need to deal with partial reads and buffers not
		 * needing IO anymore.
		 */
		if (operation->nblocks_done == operation->nblocks)
			break;

		CHECK_FOR_INTERRUPTS();

		/*
		 * This may only complete the IO partially, either because some
		 * buffers were already valid, or because of a partial read.
		 *
		 * NB: In contrast to after the AsyncReadBuffers() call in
		 * StartReadBuffers(), we do *not* reduce
		 * ReadBuffersOperation->nblocks here, callers expect the full
		 * operation to be completed at this point (as more operations may
		 * have been queued).
		 */
		AsyncReadBuffers(operation, &ignored_nblocks_progress);
	}

	CheckReadBuffersOperation(operation, true);

	/* NB: READ_DONE tracepoint was already executed in completion callback */
}
```

완료된 I/O 의 결과를 읽는다. 성공한 블록 수만큼 `nblocks_done` 을 올리고, 에러면 ERROR 를 낸다.

`src/backend/storage/buffer` / `bufmgr.c` L1601-L1638 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1601-L1638))

```c
// bufmgr.c L1601-L1638
static void
ProcessReadBuffersResult(ReadBuffersOperation *operation)
{
	PgAioReturn *aio_ret = &operation->io_return;
	PgAioResultStatus rs = aio_ret->result.status;
	int			newly_read_blocks = 0;

	Assert(pgaio_wref_valid(&operation->io_wref));
	Assert(aio_ret->result.status != PGAIO_RS_UNKNOWN);

	/*
	 * SMGR reports the number of blocks successfully read as the result of
	 * the IO operation. Thus we can simply add that to ->nblocks_done.
	 */

	if (likely(rs != PGAIO_RS_ERROR))
		newly_read_blocks = aio_ret->result.result;

	if (rs == PGAIO_RS_ERROR || rs == PGAIO_RS_WARNING)
		pgaio_result_report(aio_ret->result, &aio_ret->target_data,
							rs == PGAIO_RS_ERROR ? ERROR : WARNING);
	else if (aio_ret->result.status == PGAIO_RS_PARTIAL)
	{
		/*
		 * We'll retry, so we just emit a debug message to the server log (or
		 * not even that in prod scenarios).
		 */
		pgaio_result_report(aio_ret->result, &aio_ret->target_data, DEBUG1);
		elog(DEBUG3, "partial read, will retry");
	}

	Assert(newly_read_blocks > 0);
	Assert(newly_read_blocks <= MAX_IO_COMBINE_LIMIT);

	operation->nblocks_done += newly_read_blocks;

	Assert(operation->nblocks_done <= operation->nblocks);
}
```

같은 버퍼를 다른 backend 가 읽고 있을 때 기다리는 함수다. [10] 의 `StartBufferIO` 가 `nowait = false` 로 부르면 여기로 온다. AIO 면 그 I/O 의 참조로, 아니면 버퍼의 condition variable 로 기다린다.

`src/backend/storage/buffer` / `bufmgr.c` L5981-L6035 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L5981-L6035))

```c
// bufmgr.c L5981-L6035
static void
WaitIO(BufferDesc *buf)
{
	ConditionVariable *cv = BufferDescriptorGetIOCV(buf);

	ConditionVariablePrepareToSleep(cv);
	for (;;)
	{
		uint32		buf_state;
		PgAioWaitRef iow;

		/*
		 * It may not be necessary to acquire the spinlock to check the flag
		 * here, but since this test is essential for correctness, we'd better
		 * play it safe.
		 */
		buf_state = LockBufHdr(buf);

		/*
		 * Copy the wait reference while holding the spinlock. This protects
		 * against a concurrent TerminateBufferIO() in another backend from
		 * clearing the wref while it's being read.
		 */
		iow = buf->io_wref;
		UnlockBufHdr(buf, buf_state);

		/* no IO in progress, we don't need to wait */
		if (!(buf_state & BM_IO_IN_PROGRESS))
			break;

		/*
		 * The buffer has asynchronous IO in progress, wait for it to
		 * complete.
		 */
		if (pgaio_wref_valid(&iow))
		{
			pgaio_wref_wait(&iow);

			// ... (L6019-L6026 생략: AIO 가 CV 등록을 풀 수 있다는 주석)
			ConditionVariablePrepareToSleep(cv);
			continue;
		}

		/* wait on BufferDesc->cv, e.g. for concurrent synchronous IO */
		ConditionVariableSleep(cv, WAIT_EVENT_BUFFER_IO);
	}
	ConditionVariableCancelSleep();
}
```

## 동작 흐름

```text
 L1647  io_context, io_object 를 정한다 (pg_stat_io 용)
 L1669  I/O 참조가 없는데 io_method != sync 면 ERROR      호출 규약 위반

 L1679  while (true)
 L1689    io_wref 가 있으면 (I/O 를 하나 걸어 둠)
 L1701      결과가 아직 UNKNOWN 이고 끝나지도 않았으면
 L1706        pgaio_wref_wait                             여기서 실제로 잠든다
 L1712        기다린 시간만 IOOP_READ 에 더한다           I/O 횟수는 [10] 이 이미 셌다
 L1724      ProcessReadBuffersResult
              ERROR / WARNING 보고, 부분 읽기면 DEBUG
              nblocks_done += 읽은 블록 수
 L1732    nblocks_done == nblocks 면 break                 다 끝났다
 L1735    CHECK_FOR_INTERRUPTS
 L1747    [10] AsyncReadBuffers(operation, &ignored)       남은 블록부터 I/O 를 다시 건다
            nblocks 는 줄이지 않는다. 호출자는 전체가 끝나기를 기대한다 (주석 L1741-L1745)
 L1750  CheckReadBuffersOperation(complete = true)
```

`io_method` 별로 이 루프가 몇 바퀴 도는지가 다르다. 블록 10, 11 두 개짜리 작업이고 둘 다 한 번에 읽히는 경우다.

```text
 io_method = worker, io_uring (read_stream 처럼 플래그 없이 부른 경우)
   [03] 에서 이미 AsyncReadBuffers 가 I/O 를 제출했다 (io_wref 있음)
   바퀴 1  L1706 wait -> L1724 nblocks_done = 2 -> L1732 break

 io_method = sync, 또는 READ_BUFFERS_SYNCHRONOUSLY (ReadBuffer_common)
   sync 는 [03] 이 I/O 를 시작하지 않았다 (io_wref 없음)
     바퀴 1  L1689 건너뜀 -> L1732 0 != 2 -> L1747 AsyncReadBuffers (동기로 읽고 완료까지)
     바퀴 2  L1689 io_wref 있음, 이미 완료 -> L1724 nblocks_done = 2 -> break
   worker, io_uring 에서 READ_BUFFERS_SYNCHRONOUSLY 면 [03] 의 AsyncReadBuffers 가 이미 동기로 끝냈다
     바퀴 1  L1689 io_wref 있음, 이미 완료 (L1717) -> L1724 -> break
```

부분 읽기는 읽은 블록 수가 요청보다 적은 경우로, `md.c` 의 완료 콜백이 `PGAIO_RS_PARTIAL` 로 표시한다(`src/backend/storage/smgr/md.c` L2027-L2033). 남은 블록은 다음 바퀴에 다시 건다.

```text
 블록 10~13 (4개) 작업, 첫 I/O 가 2 블록만 읽은 경우

 바퀴 1  wait, ProcessReadBuffersResult: PGAIO_RS_PARTIAL, result = 2
           DEBUG 로그 "partial read, will retry" (L1629)
           nblocks_done = 0 + 2 = 2
         2 != 4 -> AsyncReadBuffers: blocknum = 10 + 2 = 12 부터 (L1780)
 바퀴 2  wait, result = 2 -> nblocks_done = 4 -> break

 그 사이 다른 backend 가 12 를 다 읽었다면
   AsyncReadBuffers 의 StartBufferIO(12) 가 false -> nblocks_done += 1 (L1880), I/O 없음
   다음 바퀴에서 13 부터 다시 건다
```

```text
 WaitIO 가 기다리는 두 방법 (L5987-L6033)

 헤더 spinlock 아래에서 state 와 io_wref 를 복사
   IO_IN_PROGRESS 아님          -> 끝
   io_wref 있음 (AIO 진행 중)    -> pgaio_wref_wait, 다시 확인
   io_wref 없음 (동기 I/O 진행 중) -> ConditionVariableSleep(버퍼의 CV, BUFFER_IO 대기 이벤트)
                                    TerminateBufferIO 의 broadcast 가 깨운다
```

## 결과가 쓰이는 곳

```text
 operation->buffers[0 .. nblocks-1]  (모두 pin, 모두 BM_VALID)
      --> [02] ReadBuffer_common 이 buffer 를 호출자에게 돌려준다
      --> read_stream_next_buffer 가 하나씩 꺼내 준다 (read_stream.c L931 뒤)
 에러
      --> 페이지 검증 실패는 ProcessReadBuffersResult 의 pgaio_result_report 에서 ERROR
          0 으로 채웠거나 체크섬 실패를 무시했으면 WARNING (상태 결정은 bufmgr.c L7014-L7017)
 pg_stat_io 의 read_time
      --> L1712 에서 기다린 시간만 더한다
```

## 다루지 않는 것

`pgaio_wref_wait` 와 `pgaio_wref_check_done` 의 내부(핸들 세대 번호, 완료 상태 전이), `pgaio_result_report` 의 메시지 구성, read_stream 이 기다린 뒤 look-ahead 거리를 두 배로 늘리는 규칙(read_stream.c L938-L940)은 요약만 했다.
