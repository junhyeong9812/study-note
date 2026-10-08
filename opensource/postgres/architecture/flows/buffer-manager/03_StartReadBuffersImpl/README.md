# StartReadBuffersImpl

상위: [버퍼 관리](../README.md)

**PG18 읽기 API 의 앞쪽 절반이다.** 요청한 블록 범위에 차례로 pin 을 걸다가, 첫 블록이 이미 유효하면 I/O 없이 `false` 를 돌려주고, 아니면 이어진 miss 블록만큼을 한 I/O 로 묶어 시작한 뒤 `true` 를 돌려준다. `true` 를 받은 호출자는 버퍼를 쓰기 전에 반드시 [11] `WaitReadBuffers` 를 불러야 한다. 공개 함수 `StartReadBuffer`(블록 1개)와 `StartReadBuffers`(여러 개)가 이 함수를 감싼다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L1264-L1472 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1264-L1472))

## 실제 코드

앞부분이다. 블록마다 pin 을 걸고, hit 을 만나면 범위를 거기서 자른다.

`src/backend/storage/buffer` / `bufmgr.c` L1264-L1397 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1264-L1397))

```c
// bufmgr.c L1264-L1397
static pg_always_inline bool
StartReadBuffersImpl(ReadBuffersOperation *operation,
					 Buffer *buffers,
					 BlockNumber blockNum,
					 int *nblocks,
					 int flags,
					 bool allow_forwarding)
{
	int			actual_nblocks = *nblocks;
	int			maxcombine = 0;
	bool		did_start_io;

	Assert(*nblocks == 1 || allow_forwarding);
	Assert(*nblocks > 0);
	Assert(*nblocks <= MAX_IO_COMBINE_LIMIT);

	/* see comments in ReadBuffer_common */
	if (operation->rel && RELATION_IS_OTHER_TEMP(operation->rel))
		ereport(ERROR,
				(errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
				 errmsg("cannot access temporary tables of other sessions")));

	for (int i = 0; i < actual_nblocks; ++i)
	{
		bool		found;

		if (allow_forwarding && buffers[i] != InvalidBuffer)
		{
			BufferDesc *bufHdr;

			/*
			 * This is a buffer that was pinned by an earlier call to
			 * StartReadBuffers(), but couldn't be handled in one operation at
			 * that time.  The operation was split, and the caller has passed
			 * an already pinned buffer back to us to handle the rest of the
			 * operation.  It must continue at the expected block number.
			 */
			Assert(BufferGetBlockNumber(buffers[i]) == blockNum + i);

			/*
			 * It might be an already valid buffer (a hit) that followed the
			 * final contiguous block of an earlier I/O (a miss) marking the
			 * end of it, or a buffer that some other backend has since made
			 * valid by performing the I/O for us, in which case we can handle
			 * it as a hit now.  It is safe to check for a BM_VALID flag with
			 * a relaxed load, because we got a fresh view of it while pinning
			 * it in the previous call.
			 *
			 * On the other hand if we don't see BM_VALID yet, it must be an
			 * I/O that was split by the previous call and we need to try to
			 * start a new I/O from this block.  We're also racing against any
			 * other backend that might start the I/O or even manage to mark
			 * it BM_VALID after this check, but StartBufferIO() will handle
			 * those cases.
			 */
			if (BufferIsLocal(buffers[i]))
				bufHdr = GetLocalBufferDescriptor(-buffers[i] - 1);
			else
				bufHdr = GetBufferDescriptor(buffers[i] - 1);
			Assert(pg_atomic_read_u32(&bufHdr->state) & BM_TAG_VALID);
			found = pg_atomic_read_u32(&bufHdr->state) & BM_VALID;
		}
		else
		{
			buffers[i] = PinBufferForBlock(operation->rel,
										   operation->smgr,
										   operation->persistence,
										   operation->forknum,
										   blockNum + i,
										   operation->strategy,
										   &found);
		}

		if (found)
		{
			/*
			 * We have a hit.  If it's the first block in the requested range,
			 * we can return it immediately and report that WaitReadBuffers()
			 * does not need to be called.  If the initial value of *nblocks
			 * was larger, the caller will have to call again for the rest.
			 */
			if (i == 0)
			{
				*nblocks = 1;

// ... (L1349-L1361 생략: assert 빌드 전용 초기화)
				return false;
			}

			/*
			 * Otherwise we already have an I/O to perform, but this block
			 * can't be included as it is already valid.  Split the I/O here.
			 * There may or may not be more blocks requiring I/O after this
			 * one, we haven't checked, but they can't be contiguous with this
			 * one in the way.  We'll leave this buffer pinned, forwarding it
			 * to the next call, avoiding the need to unpin it here and re-pin
			 * it in the next call.
			 */
			actual_nblocks = i;
			break;
		}
		else
		{
			/*
			 * Check how many blocks we can cover with the same IO. The smgr
			 * implementation might e.g. be limited due to a segment boundary.
			 */
			if (i == 0 && actual_nblocks > 1)
			{
				maxcombine = smgrmaxcombine(operation->smgr,
											operation->forknum,
											blockNum);
				if (unlikely(maxcombine < actual_nblocks))
				{
					elog(DEBUG2, "limiting nblocks at %u from %u to %u",
						 blockNum, actual_nblocks, maxcombine);
					actual_nblocks = maxcombine;
				}
			}
		}
	}
	*nblocks = actual_nblocks;
```

뒷부분이다. `io_method` 가 `sync` 가 아니면 여기서 I/O 를 시작하고, `sync` 면 시작을 `WaitReadBuffers` 로 미룬다.

`src/backend/storage/buffer` / `bufmgr.c` L1398-L1472 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1398-L1472))

```c
// bufmgr.c L1398-L1472

	/* Populate information needed for I/O. */
	operation->buffers = buffers;
	operation->blocknum = blockNum;
	operation->flags = flags;
	operation->nblocks = actual_nblocks;
	operation->nblocks_done = 0;
	pgaio_wref_clear(&operation->io_wref);

	/*
	 * When using AIO, start the IO in the background. If not, issue prefetch
	 * requests if desired by the caller.
	 *
	 * The reason we have a dedicated path for IOMETHOD_SYNC here is to
	 * de-risk the introduction of AIO somewhat. It's a large architectural
	 * change, with lots of chances for unanticipated performance effects.
	 *
	 * Use of IOMETHOD_SYNC already leads to not actually performing IO
	 * asynchronously, but without the check here we'd execute IO earlier than
	 * we used to. Eventually this IOMETHOD_SYNC specific path should go away.
	 */
	if (io_method != IOMETHOD_SYNC)
	{
		/*
		 * Try to start IO asynchronously. It's possible that no IO needs to
		 * be started, if another backend already performed the IO.
		 *
		 * Note that if an IO is started, it might not cover the entire
		 * requested range, e.g. because an intermediary block has been read
		 * in by another backend.  In that case any "trailing" buffers we
		 * already pinned above will be "forwarded" by read_stream.c to the
		 * next call to StartReadBuffers().
		 *
		 * This is signalled to the caller by decrementing *nblocks *and*
		 * reducing operation->nblocks. The latter is done here, but not below
		 * WaitReadBuffers(), as in WaitReadBuffers() we can't "shorten" the
		 * overall read size anymore, we need to retry until done in its
		 * entirety or until failed.
		 */
		did_start_io = AsyncReadBuffers(operation, nblocks);

		operation->nblocks = *nblocks;
	}
	else
	{
		operation->flags |= READ_BUFFERS_SYNCHRONOUSLY;

		if (flags & READ_BUFFERS_ISSUE_ADVICE)
		{
			/*
			 * In theory we should only do this if PinBufferForBlock() had to
			 * allocate new buffers above.  That way, if two calls to
			 * StartReadBuffers() were made for the same blocks before
			 * WaitReadBuffers(), only the first would issue the advice.
			 * That'd be a better simulation of true asynchronous I/O, which
			 * would only start the I/O once, but isn't done here for
			 * simplicity.
			 */
			smgrprefetch(operation->smgr,
						 operation->forknum,
						 blockNum,
						 actual_nblocks);
		}

		/*
		 * Indicate that WaitReadBuffers() should be called. WaitReadBuffers()
		 * will initiate the necessary IO.
		 */
		did_start_io = true;
	}

	CheckReadBuffersOperation(operation, !did_start_io);

	return did_start_io;
}
```

공개 래퍼 둘이다. 다르게 넘기는 것은 forwarding 허용 여부 하나다.

`src/backend/storage/buffer` / `bufmgr.c` L1497-L1530 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1497-L1530))

```c
// bufmgr.c L1497-L1530
bool
StartReadBuffers(ReadBuffersOperation *operation,
				 Buffer *buffers,
				 BlockNumber blockNum,
				 int *nblocks,
				 int flags)
{
	return StartReadBuffersImpl(operation, buffers, blockNum, nblocks, flags,
								true /* expect forwarded buffers */ );
}
// ... (L1507-L1515 생략: StartReadBuffer 앞 주석)
bool
StartReadBuffer(ReadBuffersOperation *operation,
				Buffer *buffer,
				BlockNumber blocknum,
				int flags)
{
	int			nblocks = 1;
	bool		result;

	result = StartReadBuffersImpl(operation, buffer, blocknum, &nblocks, flags,
								  false /* single block, no forwarding */ );
	Assert(nblocks == 1);		/* single block can't be short */

	return result;
}
```

## 동작 흐름

```text
 L1281  다른 세션 임시 테이블이면 ERROR

 L1286  for i in 0 .. actual_nblocks-1
 L1290    forwarding 된 버퍼가 들어 있으면   (StartReadBuffers 만)
 L1324      pin 은 이미 있다. BM_VALID 만 다시 본다
 L1328    아니면 [04] PinBufferForBlock(blockNum + i)
 L1337    found (이미 유효)
 L1345      i == 0  -> *nblocks = 1, return false        hit. I/O 없음
 L1374      i > 0   -> actual_nblocks = i, break        여기서 I/O 범위를 자른다
                       이 버퍼는 pin 을 쥔 채 다음 호출로 넘긴다 (forwarding)
 L1383    miss 이고 i == 0 이면 smgrmaxcombine 으로 상한을 본다
                       세그먼트 파일 경계를 넘는 I/O 는 묶을 수 없다

 L1397  *nblocks = actual_nblocks
 L1400-L1405  operation 에 buffers, blocknum, flags, nblocks, nblocks_done = 0 을 적는다

 L1419  io_method != IOMETHOD_SYNC
 L1437    did_start_io = [10] AsyncReadBuffers(operation, nblocks)
 L1439    operation->nblocks = *nblocks      AIO 가 범위를 더 줄였을 수 있다
 L1441  io_method == IOMETHOD_SYNC
 L1443    READ_BUFFERS_SYNCHRONOUSLY 를 켠다
 L1445    READ_BUFFERS_ISSUE_ADVICE 면 smgrprefetch (posix_fadvise 류 힌트)
 L1466    did_start_io = true                 I/O 는 WaitReadBuffers 가 시작한다
 L1471  return did_start_io
```

블록 10~13 네 개를 요청했는데 12 만 이미 shared buffers 에 유효하게 있는 경우다.

```text
 StartReadBuffers(blockNum = 10, *nblocks = 4)

 i  block  found  처리
 0  10     false  pin, 새 tag. smgrmaxcombine(10) >= 4 라고 하자
 1  11     false  pin, 새 tag
 2  12     true   pin (hit). i > 0 -> actual_nblocks = 2, break
 3  13     -      보지 않음

 *nblocks = 2   이번 I/O 는 10, 11 두 블록
 buffers[2] = 12 의 버퍼 (pin 유지, forwarded)
 read_stream 은 다음 StartReadBuffers 를 블록 12 부터, buffers[2] 를 그대로 넘겨 부른다
   -> L1290 경로에서 BM_VALID 를 보고 i == 0 hit 으로 처리된다
```

```text
 io_method 에 따라 I/O 가 실제로 나가는 시점

 io_method = sync
   StartReadBuffers 안   pin, READ_BUFFERS_ISSUE_ADVICE 면 smgrprefetch
   WaitReadBuffers 안    AsyncReadBuffers -> 동기 읽기 -> 완료
 io_method = worker, io_uring
   StartReadBuffers 안   pin, AsyncReadBuffers 로 제출
   WaitReadBuffers 안    pgaio_wref_wait 로 완료 대기

 위 표는 read_stream 처럼 플래그 없이 부를 때다
 ReadBuffer_common 처럼 READ_BUFFERS_SYNCHRONOUSLY 를 켜면 worker, io_uring 에서도
   AsyncReadBuffers 안에서 이 backend 가 바로 읽는다 ([10] 의 실행 주체 표)
 기본값은 worker (include/storage/aio.h L42 DEFAULT_IO_METHOD)
 io_uring 은 liburing 으로 빌드했고 EXEC_BACKEND 가 아닐 때만 있다 (aio.h L26-L28)
 sync 경로는 AIO 도입 위험을 줄이려 남긴 것이고 언젠가 없앤다고 주석이 적었다 (L1411-L1417)
```

## 결과가 쓰이는 곳

```text
 반환값
      false  --> buffers[0] 은 유효하다. 바로 쓴다
      true   --> [11] WaitReadBuffers(operation) 를 부른 뒤에야 쓸 수 있다
 *nblocks
      --> read_stream 이 이번 I/O 에 들어간 블록 수로 쓰고, 나머지는 다음 호출로 넘긴다
 operation
      --> [11] 이 nblocks_done 이 nblocks 가 될 때까지 다시 I/O 를 건다
```

## 다루지 않는 것

`read_stream.c` 가 forwarding 버퍼와 look-ahead 거리를 관리하는 방식, `smgrmaxcombine` 과 `smgrprefetch` 의 `md.c` 구현, `CheckReadBuffersOperation` 의 assert 검사는 요약만 했다.
