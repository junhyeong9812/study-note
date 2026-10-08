# AsyncReadBuffers

상위: [버퍼 관리](../README.md)

**PG18 AIO 읽기 하나를 시작하는 함수다.** 아직 안 읽힌 첫 블록에 대해 `StartBufferIO` 로 읽기 권리를 잡고, 이어지는 블록도 기다리지 않고 잡을 수 있는 데까지 묶어 하나의 vectored read(`smgrstartreadv`)로 AIO 핸들에 실어 보낸다. 첫 블록을 이미 남이 읽어 놓았으면 I/O 없이 hit 으로 센다. 실제 읽기와 완료 처리(체크섬 검증, `BM_VALID` 설정)는 `io_method` 에 따라 IO worker 프로세스, io_uring, 또는 이 backend 자신이 하고, 완료 콜백은 그 실행 주체 쪽에서 돈다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L1772-L1987 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1772-L1987))

## 실제 코드

```c
// bufmgr.c L1772-L1987
static bool
AsyncReadBuffers(ReadBuffersOperation *operation, int *nblocks_progress)
{
	Buffer	   *buffers = &operation->buffers[0];
	int			flags = operation->flags;
	ForkNumber	forknum = operation->forknum;
	char		persistence = operation->persistence;
	int16		nblocks_done = operation->nblocks_done;
	BlockNumber blocknum = operation->blocknum + nblocks_done;
	Buffer	   *io_buffers = &operation->buffers[nblocks_done];
	int			io_buffers_len = 0;
	PgAioHandle *ioh;
	uint32		ioh_flags = 0;
	void	   *io_pages[MAX_IO_COMBINE_LIMIT];
	IOContext	io_context;
	IOObject	io_object;
	bool		did_start_io;

	/*
	 * When this IO is executed synchronously, either because the caller will
	 * immediately block waiting for the IO or because IOMETHOD_SYNC is used,
	 * the AIO subsystem needs to know.
	 */
	if (flags & READ_BUFFERS_SYNCHRONOUSLY)
		ioh_flags |= PGAIO_HF_SYNCHRONOUS;

	if (persistence == RELPERSISTENCE_TEMP)
	{
		io_context = IOCONTEXT_NORMAL;
		io_object = IOOBJECT_TEMP_RELATION;
		ioh_flags |= PGAIO_HF_REFERENCES_LOCAL;
	}
	else
	{
		io_context = IOContextForStrategy(operation->strategy);
		io_object = IOOBJECT_RELATION;
	}

	// ... (L1810-L1830 생략: zero_damaged_pages, ignore_checksum_failure 를 플래그로 옮김)

	// ... (L1832-L1837 생략: 체크섬 실패 통계 준비)

	/*
	 * Get IO handle before ReadBuffersCanStartIO(), as pgaio_io_acquire()
	 * might block, which we don't want after setting IO_IN_PROGRESS.
	 *
	 * If we need to wait for IO before we can get a handle, submit
	 * already-staged IO first, so that other backends don't need to wait.
	 * There wouldn't be a deadlock risk, as pgaio_io_acquire() just needs to
	 * wait for already submitted IO, which doesn't require additional locks,
	 * but it could still cause undesirable waits.
	 *
	 * A secondary benefit is that this would allow us to measure the time in
	 * pgaio_io_acquire() without causing undue timer overhead in the common,
	 * non-blocking, case.  However, currently the pgstats infrastructure
	 * doesn't really allow that, as it a) asserts that an operation can't
	 * have time without operations b) doesn't have an API to report
	 * "accumulated" time.
	 */
	ioh = pgaio_io_acquire_nb(CurrentResourceOwner, &operation->io_return);
	if (unlikely(!ioh))
	{
		pgaio_submit_staged();

		ioh = pgaio_io_acquire(CurrentResourceOwner, &operation->io_return);
	}

	/*
	 * Check if we can start IO on the first to-be-read buffer.
	 *
	 * If an I/O is already in progress in another backend, we want to wait
	 * for the outcome: either done, or something went wrong and we will
	 * retry.
	 */
	if (!ReadBuffersCanStartIO(buffers[nblocks_done], false))
	{
		/*
		 * Someone else has already completed this block, we're done.
		 *
		 * When IO is necessary, ->nblocks_done is updated in
		 * ProcessReadBuffersResult(), but that is not called if no IO is
		 * necessary. Thus update here.
		 */
		operation->nblocks_done += 1;
		*nblocks_progress = 1;

		pgaio_io_release(ioh);
		pgaio_wref_clear(&operation->io_wref);
		did_start_io = false;

		// ... (L1887-L1910 생략: hit 통계)
	}
	else
	{
		instr_time	io_start;

		/* We found a buffer that we need to read in. */
		Assert(io_buffers[0] == buffers[nblocks_done]);
		io_pages[0] = BufferGetBlock(buffers[nblocks_done]);
		io_buffers_len = 1;

		/*
		 * How many neighboring-on-disk blocks can we scatter-read into other
		 * buffers at the same time?  In this case we don't wait if we see an
		 * I/O already in progress.  We already set BM_IO_IN_PROGRESS for the
		 * head block, so we should get on with that I/O as soon as possible.
		 */
		for (int i = nblocks_done + 1; i < operation->nblocks; i++)
		{
			if (!ReadBuffersCanStartIO(buffers[i], true))
				break;
			/* Must be consecutive block numbers. */
			Assert(BufferGetBlockNumber(buffers[i - 1]) ==
				   BufferGetBlockNumber(buffers[i]) - 1);
			Assert(io_buffers[io_buffers_len] == buffers[i]);

			io_pages[io_buffers_len++] = BufferGetBlock(buffers[i]);
		}

		/* get a reference to wait for in WaitReadBuffers() */
		pgaio_io_get_wref(ioh, &operation->io_wref);

		/* provide the list of buffers to the completion callbacks */
		pgaio_io_set_handle_data_32(ioh, (uint32 *) io_buffers, io_buffers_len);

		pgaio_io_register_callbacks(ioh,
									persistence == RELPERSISTENCE_TEMP ?
									PGAIO_HCB_LOCAL_BUFFER_READV :
									PGAIO_HCB_SHARED_BUFFER_READV,
									flags);

		pgaio_io_set_flag(ioh, ioh_flags);

		// ... (L1953-L1961 생략: 시간 측정 주석)
		io_start = pgstat_prepare_io_time(track_io_timing);
		smgrstartreadv(ioh, operation->smgr, forknum,
					   blocknum,
					   io_pages, io_buffers_len);
		// ... (L1966-L1980 생략: I/O 통계와 vacuum 비용)

		*nblocks_progress = io_buffers_len;
		did_start_io = true;
	}

	return did_start_io;
}
```

읽기 권리를 잡는 보조 함수다. 이 backend 가 아직 제출하지 않은 I/O 를 쌓아 두었으면, 남을 기다리기 전에 먼저 제출한다.

`src/backend/storage/buffer` / `bufmgr.c` L1572-L1595 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1572-L1595))

```c
// bufmgr.c L1572-L1595
static inline bool
ReadBuffersCanStartIO(Buffer buffer, bool nowait)
{
	/*
	 * If this backend currently has staged IO, we need to submit the pending
	 * IO before waiting for the right to issue IO, to avoid the potential for
	 * deadlocks (and, more commonly, unnecessary delays for other backends).
	 */
	if (!nowait && pgaio_have_staged())
	{
		if (ReadBuffersCanStartIOOnce(buffer, true))
			return true;

		/*
		 * Unfortunately StartBufferIO() returning false doesn't allow to
		 * distinguish between the buffer already being valid and IO already
		 * being in progress. Since IO already being in progress is quite
		 * rare, this approach seems fine.
		 */
		pgaio_submit_staged();
	}

	return ReadBuffersCanStartIOOnce(buffer, nowait);
}
```

I/O 를 제출하기 직전(stage) 버퍼마다 AIO 몫 pin 을 하나 더 건다. 이 backend 가 에러로 자기 pin 을 다 풀어도 I/O 가 끝날 때까지 버퍼가 교체되지 않게 하려는 것이다.

`src/backend/storage/buffer` / `bufmgr.c` L6866-L6882 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L6866-L6882))

```c
// bufmgr.c L6866-L6882
		/*
		 * Reflect that the buffer is now owned by the AIO subsystem.
		 *
		 * For local buffers: This can't be done just via LocalRefCount, as
		 * one might initially think, as this backend could error out while
		 * AIO is still in progress, releasing all the pins by the backend
		 * itself.
		 *
		 * This pin is released again in TerminateBufferIO().
		 */
		buf_state += BUF_REFCOUNT_ONE;
		buf_hdr->io_wref = io_ref;

		if (is_temp)
			pg_atomic_unlocked_write_u32(&buf_hdr->state, buf_state);
		else
			UnlockBufHdr(buf_hdr, buf_state);
```

완료 콜백에서 블록마다 부르는 함수의 끝이다. 검증에 실패하지 않았으면 `BM_VALID` 를 켜고 AIO 몫 pin 을 내린다.

`src/backend/storage/buffer` / `bufmgr.c` L7167-L7172 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L7167-L7172))

```c
// bufmgr.c L7167-L7172
	/* Terminate I/O and set BM_VALID. */
	set_flag_bits = failed ? BM_IO_ERROR : BM_VALID;
	if (is_temp)
		TerminateLocalBufferIO(buf_hdr, false, set_flag_bits, true);
	else
		TerminateBufferIO(buf_hdr, false, set_flag_bits, false, true);
```

## 동작 흐름

```text
 L1779  nblocks_done 부터 시작 (재시도면 앞부분은 이미 끝났다)
 L1795  READ_BUFFERS_SYNCHRONOUSLY 면 PGAIO_HF_SYNCHRONOUS
 L1856  ioh = pgaio_io_acquire_nb                  AIO 핸들을 기다리지 않고 얻어 본다
 L1857    없으면 쌓인 I/O 를 제출하고 기다려서 얻는다
          (BM_IO_IN_PROGRESS 를 켠 뒤에 막히지 않게 핸들을 먼저 얻는다, 주석 L1839-L1844)

 L1871  ReadBuffersCanStartIO(buffers[nblocks_done], nowait = false)
          false  남이 이미 읽었다 (진행 중이었으면 끝날 때까지 기다린 뒤)
 L1880      nblocks_done += 1, *nblocks_progress = 1
 L1883      핸들 반납, did_start_io = false
            이 backend 에서는 hit 으로 센다 (주석 L1888-L1890)
          true   이 backend 가 BM_IO_IN_PROGRESS 를 켰다
 L1918      io_pages[0] = 첫 블록의 버퍼 메모리
 L1927      i = nblocks_done+1 부터
 L1929        ReadBuffersCanStartIO(buffers[i], nowait = true)
                false 면 거기서 멈춘다              진행 중인 남의 I/O 를 기다리지 않는다
 L1936        io_pages 에 덧붙인다                   디스크에서 연속인 블록만 (Assert L1932)
 L1940      pgaio_io_get_wref                        WaitReadBuffers 가 기다릴 참조
 L1943      핸들에 버퍼 번호 목록을 싣는다
 L1945      완료 콜백 등록 (PGAIO_HCB_SHARED_BUFFER_READV, 임시면 LOCAL)
 L1963      smgrstartreadv(ioh, ..., blocknum, io_pages, io_buffers_len)
 L1982      *nblocks_progress = io_buffers_len, did_start_io = true
```

```text
 버퍼 하나의 state 가 읽기 동안 바뀌는 순서 (shared buffer, 성공)

 step                   refcount  flags                       누가
 BufferAlloc 직후       1         TAG_VALID                   요청 backend
 StartBufferIO (L1871)  1         TAG_VALID | IO_IN_PROGRESS  요청 backend
 stage (L6876)          2         TAG_VALID | IO_IN_PROGRESS  요청 backend
 readv                  2         TAG_VALID | IO_IN_PROGRESS  아래 실행 주체 표
 complete_one (L7172)   1         TAG_VALID | VALID           실행 주체 쪽 완료 콜백

 complete_one 의 TerminateBufferIO(release_aio = true) 가
   IO_IN_PROGRESS 를 끄고, AIO 몫 pin 을 빼고, condition variable 로 대기자를 깨운다

 검증 실패면 BM_VALID 대신 BM_IO_ERROR (L7168)
   READ_BUFFERS_ZERO_ON_ERROR 면 0 으로 채우고 BM_VALID (L7117-L7121)
```

readv 를 누가 실행하는지는 AIO 계층이 핸들을 stage 할 때 정한다. 아래 줄 번호는 `src/backend/storage/aio/` 아래 파일의 것이다.

```text
 실행 주체 결정 (aio.c L455-L477)

 pgaio_io_needs_synchronous_execution (aio.c L483-L501)
   PGAIO_HF_SYNCHRONOUS 가 켜져 있다       -> 동기     (L493-L494)
   아니면 io_method 의 판정을 따른다

 동기   pgaio_io_perform_synchronously (aio_io.c L116-L146)
          이 backend 가 pg_preadv 로 읽고 바로 pgaio_io_process_completion -> 완료 콜백
 비동기 staged_ios 에 쌓았다가 pgaio_submit_staged 로 제출 (aio.c L463-L471)

 io_method = sync
   동기 조건   항상 (method_sync.c L36-L38)
 io_method = worker
   동기 조건   postmaster 자식이 아님, 임시 테이블 (PGAIO_HF_REFERENCES_LOCAL),
               파일을 다시 열 수 없는 I/O (method_worker.c L235-L240)
   비동기      큐에 넣고 쉬는 worker 의 latch 를 깨운다 (method_worker.c L270-L282)
               worker 가 pgaio_io_perform_synchronously 로 읽고 콜백도 worker 에서 (L565)
               큐가 차서 못 넣은 것은 제출한 backend 가 동기로 (L284-L290)
 io_method = io_uring
   동기 조건   PGAIO_HF_SYNCHRONOUS 일 때만 (method 판정 함수가 없다)
   비동기      커널이 읽고, 완료 큐(CQE)를 걷는 프로세스가
               pgaio_io_process_completion 을 부른다 (method_io_uring.c L559-L569)

 그래서 ReadBuffer_common 의 단일 블록 읽기는 (READ_BUFFERS_SYNCHRONOUSLY -> PGAIO_HF_SYNCHRONOUS)
 io_method 와 상관없이 이 backend 안에서 smgrstartreadv 를 지나며 바로 끝난다
 진짜로 겹치는 읽기는 플래그 없이 부르는 read_stream 쪽이다

 콜백이 다른 프로세스에서 돌 수 있으므로
   zero_damaged_pages, ignore_checksum_failure 를 GUC 대신 플래그로 넘긴다 (주석 L1811-L1816)
   검증 실패 로그를 콜백에서 바로 서버 로그로만 남긴다 (주석 L7138-L7148)
```

```text
 블록 10~13 (모두 miss) 을 요청했는데 12 는 다른 backend 가 지금 읽는 중인 경우

 L1871  buffers[0] = 10  StartBufferIO(nowait=false) 성공    io_pages = [10]
 L1929  buffers[1] = 11  StartBufferIO(nowait=true)  성공    io_pages = [10, 11]
 L1929  buffers[2] = 12  StartBufferIO(nowait=true)  false   멈춤 (진행 중)
 L1963  smgrstartreadv(blocknum = 10, 2 블록)
        *nblocks_progress = 2

 StartReadBuffersImpl 에서 불렸으면 operation->nblocks = 2 로 줄고 12, 13 은 다음 호출로 넘어간다
 WaitReadBuffers 에서 불렸으면 nblocks 는 그대로 두고, 다음 바퀴에서 12 부터 다시 부른다
```

## 결과가 쓰이는 곳

```text
 operation->io_wref
      --> [11] WaitReadBuffers 가 pgaio_wref_wait 로 기다린다
 operation->io_return
      --> 완료 뒤 ProcessReadBuffersResult 가 읽은 블록 수와 에러를 본다
 BM_VALID (완료 콜백이 켬)
      --> 같은 블록을 찾던 다른 backend 의 StartBufferIO 가 false 를 돌려받아 hit 으로 처리한다
 shared_blks_read
      --> EXPLAIN (BUFFERS) 의 "read". 기다린 시간이 아니라 I/O 를 낸 시점에 센다
```

## 다루지 않는 것

AIO 하위 계층 전부(`pgaio_io_acquire`, 핸들 상태 기계, 제출 배치 `pgaio_submit_staged`, IO worker 의 큐, io_uring 링), `smgrstartreadv` 아래 `mdstartreadv`, 완료 콜백의 에러 인코딩(`buffer_readv_encode_error`, `buffer_readv_report`), 임시 테이블의 `StartLocalBufferIO` 는 이 흐름의 곁가지라 요약만 했다.
