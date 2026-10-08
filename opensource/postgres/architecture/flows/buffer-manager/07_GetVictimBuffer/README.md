# GetVictimBuffer

상위: [버퍼 관리](../README.md)

**새 블록을 담을 빈 버퍼 하나를 만들어 낸다.** [08] `StrategyGetBuffer` 가 고른 후보에 pin 을 걸고, 더러우면 content lock 을 조건부로 잡아 [09] `FlushBuffer` 로 쓰고, 마지막으로 옛 tag 를 해시 테이블에서 지운다. 어느 단계에서든 다른 backend 가 그 버퍼를 건드린 흔적이 보이면 pin 을 풀고 처음(`again:`)으로 돌아가 다른 후보를 받는다. 돌아올 때 버퍼는 이 backend 만 pin 하고 있고 tag 도 플래그도 비어 있다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L2353-L2505 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L2353-L2505))

## 실제 코드

```c
// bufmgr.c L2353-L2505
static Buffer
GetVictimBuffer(BufferAccessStrategy strategy, IOContext io_context)
{
	BufferDesc *buf_hdr;
	Buffer		buf;
	uint32		buf_state;
	bool		from_ring;

	/*
	 * Ensure, while the spinlock's not yet held, that there's a free refcount
	 * entry, and a resource owner slot for the pin.
	 */
	ReservePrivateRefCountEntry();
	ResourceOwnerEnlarge(CurrentResourceOwner);

	/* we return here if a prospective victim buffer gets used concurrently */
again:

	/*
	 * Select a victim buffer.  The buffer is returned with its header
	 * spinlock still held!
	 */
	buf_hdr = StrategyGetBuffer(strategy, &buf_state, &from_ring);
	buf = BufferDescriptorGetBuffer(buf_hdr);

	Assert(BUF_STATE_GET_REFCOUNT(buf_state) == 0);

	/* Pin the buffer and then release the buffer spinlock */
	PinBuffer_Locked(buf_hdr);

	/*
	 * We shouldn't have any other pins for this buffer.
	 */
	CheckBufferIsPinnedOnce(buf);

	/*
	 * If the buffer was dirty, try to write it out.  There is a race
	 * condition here, in that someone might dirty it after we released the
	 * buffer header lock above, or even while we are writing it out (since
	 * our share-lock won't prevent hint-bit updates).  We will recheck the
	 * dirty bit after re-locking the buffer header.
	 */
	if (buf_state & BM_DIRTY)
	{
		LWLock	   *content_lock;

		Assert(buf_state & BM_TAG_VALID);
		Assert(buf_state & BM_VALID);

		/*
		 * We need a share-lock on the buffer contents to write it out (else
		 * we might write invalid data, eg because someone else is compacting
		 * the page contents while we write).  We must use a conditional lock
		 * acquisition here to avoid deadlock.  Even though the buffer was not
		 * pinned (and therefore surely not locked) when StrategyGetBuffer
		 * returned it, someone else could have pinned and exclusive-locked it
		 * by the time we get here. If we try to get the lock unconditionally,
		 * we'd block waiting for them; if they later block waiting for us,
		 * deadlock ensues. (This has been observed to happen when two
		 * backends are both trying to split btree index pages, and the second
		 * one just happens to be trying to split the page the first one got
		 * from StrategyGetBuffer.)
		 */
		content_lock = BufferDescriptorGetContentLock(buf_hdr);
		if (!LWLockConditionalAcquire(content_lock, LW_SHARED))
		{
			/*
			 * Someone else has locked the buffer, so give it up and loop back
			 * to get another one.
			 */
			UnpinBuffer(buf_hdr);
			goto again;
		}

		/*
		 * If using a nondefault strategy, and writing the buffer would
		 * require a WAL flush, let the strategy decide whether to go ahead
		 * and write/reuse the buffer or to choose another victim.  We need a
		 * lock to inspect the page LSN, so this can't be done inside
		 * StrategyGetBuffer.
		 */
		if (strategy != NULL)
		{
			XLogRecPtr	lsn;

			/* Read the LSN while holding buffer header lock */
			buf_state = LockBufHdr(buf_hdr);
			lsn = BufferGetLSN(buf_hdr);
			UnlockBufHdr(buf_hdr, buf_state);

			if (XLogNeedsFlush(lsn)
				&& StrategyRejectBuffer(strategy, buf_hdr, from_ring))
			{
				LWLockRelease(content_lock);
				UnpinBuffer(buf_hdr);
				goto again;
			}
		}

		/* OK, do the I/O */
		FlushBuffer(buf_hdr, NULL, IOOBJECT_RELATION, io_context);
		LWLockRelease(content_lock);

		ScheduleBufferTagForWriteback(&BackendWritebackContext, io_context,
									  &buf_hdr->tag);
	}


	// ... (L2461-L2481 생략: pg_stat_io 의 evict/reuse 집계)

	/*
	 * If the buffer has an entry in the buffer mapping table, delete it. This
	 * can fail because another backend could have pinned or dirtied the
	 * buffer.
	 */
	if ((buf_state & BM_TAG_VALID) && !InvalidateVictimBuffer(buf_hdr))
	{
		UnpinBuffer(buf_hdr);
		goto again;
	}

	/* a final set of sanity checks */
#ifdef USE_ASSERT_CHECKING
	buf_state = pg_atomic_read_u32(&buf_hdr->state);

	Assert(BUF_STATE_GET_REFCOUNT(buf_state) == 1);
	Assert(!(buf_state & (BM_TAG_VALID | BM_VALID | BM_DIRTY)));

	CheckBufferIsPinnedOnce(buf);
#endif

	return buf;
}
```

옛 tag 를 지우는 보조 함수다. 배타 분할 lock 과 헤더 spinlock 을 둘 다 쥔 채 refcount 와 dirty 를 다시 본다.

`src/backend/storage/buffer` / `bufmgr.c` L2285-L2351 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L2285-L2351))

```c
// bufmgr.c L2285-L2351
static bool
InvalidateVictimBuffer(BufferDesc *buf_hdr)
{
	uint32		buf_state;
	uint32		hash;
	LWLock	   *partition_lock;
	BufferTag	tag;

	Assert(GetPrivateRefCount(BufferDescriptorGetBuffer(buf_hdr)) == 1);

	/* have buffer pinned, so it's safe to read tag without lock */
	tag = buf_hdr->tag;

	hash = BufTableHashCode(&tag);
	partition_lock = BufMappingPartitionLock(hash);

	LWLockAcquire(partition_lock, LW_EXCLUSIVE);

	/* lock the buffer header */
	buf_state = LockBufHdr(buf_hdr);

	/*
	 * We have the buffer pinned nobody else should have been able to unset
	 * this concurrently.
	 */
	Assert(buf_state & BM_TAG_VALID);
	Assert(BUF_STATE_GET_REFCOUNT(buf_state) > 0);
	Assert(BufferTagsEqual(&buf_hdr->tag, &tag));

	/*
	 * If somebody else pinned the buffer since, or even worse, dirtied it,
	 * give up on this buffer: It's clearly in use.
	 */
	if (BUF_STATE_GET_REFCOUNT(buf_state) != 1 || (buf_state & BM_DIRTY))
	{
		Assert(BUF_STATE_GET_REFCOUNT(buf_state) > 0);

		UnlockBufHdr(buf_hdr, buf_state);
		LWLockRelease(partition_lock);

		return false;
	}

	/*
	 * Clear out the buffer's tag and flags and usagecount.  This is not
	 * strictly required, as BM_TAG_VALID/BM_VALID needs to be checked before
	 * doing anything with the buffer. But currently it's beneficial, as the
	 * cheaper pre-check for several linear scans of shared buffers use the
	 * tag (see e.g. FlushDatabaseBuffers()).
	 */
	ClearBufferTag(&buf_hdr->tag);
	buf_state &= ~(BUF_FLAG_MASK | BUF_USAGECOUNT_MASK);
	UnlockBufHdr(buf_hdr, buf_state);

	Assert(BUF_STATE_GET_REFCOUNT(buf_state) > 0);

	/* finally delete buffer from the buffer mapping table */
	BufTableDelete(&tag, hash);

	LWLockRelease(partition_lock);

	Assert(!(buf_state & (BM_DIRTY | BM_VALID | BM_TAG_VALID)));
	Assert(BUF_STATE_GET_REFCOUNT(buf_state) > 0);
	Assert(BUF_STATE_GET_REFCOUNT(pg_atomic_read_u32(&buf_hdr->state)) > 0);

	return true;
}
```

ring 전략이 더러운 버퍼를 거절하는 규칙이다. BULKREAD 에서 ring 이 준 버퍼일 때만 거절한다.

`src/backend/storage/buffer` / `freelist.c` L839-L858 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/freelist.c#L839-L858))

```c
// freelist.c L839-L858
bool
StrategyRejectBuffer(BufferAccessStrategy strategy, BufferDesc *buf, bool from_ring)
{
	/* We only do this in bulkread mode */
	if (strategy->btype != BAS_BULKREAD)
		return false;

	/* Don't muck with behavior of normal buffer-replacement strategy */
	if (!from_ring ||
		strategy->buffers[strategy->current] != BufferDescriptorGetBuffer(buf))
		return false;

	/*
	 * Remove the dirty buffer from the ring; necessary to prevent infinite
	 * loop if all ring members are dirty.
	 */
	strategy->buffers[strategy->current] = InvalidBuffer;

	return true;
}
```

## 동작 흐름

```text
 L2365-L2366  pin 기록 자리를 미리 확보 (spinlock 을 쥐기 전에)
 again:
 L2375  buf = [08] StrategyGetBuffer(strategy, &state, &from_ring)
          헤더 spinlock 을 쥔 채, refcount == 0 인 버퍼가 온다
 L2381  PinBuffer_Locked                       pin 하고 spinlock 해제

 L2395  BM_DIRTY 면
 L2417    LWLockConditionalAcquire(content_lock, SHARED)
            실패 -> UnpinBuffer, goto again       누가 쥐고 있다. 기다리지 않는다
 L2434    strategy 가 있으면
 L2440      lsn = 페이지 LSN
 L2443      XLogNeedsFlush(lsn) && StrategyRejectBuffer
              -> lock 해제, UnpinBuffer, goto again
 L2453    [09] FlushBuffer                     WAL flush 후 smgrwrite
 L2454    content lock 해제
 L2456    ScheduleBufferTagForWriteback       커널에 writeback 힌트를 모아 둔다

 L2488  BM_TAG_VALID 면 InvalidateVictimBuffer
          false -> UnpinBuffer, goto again
 L2504  return buf                             refcount 1, flags 0, usage 0
```

content lock 을 조건부로만 잡는 이유는 주석 L2402-L2415 에 있다. StrategyGetBuffer 가 돌려준 순간에는 아무도 pin 하지 않았지만, 그 직후 누가 pin 하고 배타 lock 을 잡았을 수 있다. 무조건 기다리면 그쪽이 이쪽을 기다리는 순간 교착이 된다. 두 backend 가 btree 페이지를 동시에 분할할 때 실제로 관찰되었다고 적혀 있다.

```text
 InvalidateVictimBuffer 의 재확인 (L2301-L2326)

 배타 분할 lock (옛 tag 의 분할) -> 헤더 spinlock
   refcount != 1    누가 그 사이에 pin 했다        -> false (포기)
   BM_DIRTY         쓰고 난 뒤 누가 또 더럽혔다    -> false (포기)
   둘 다 아니면
     tag 를 지우고 flags, usage_count 를 0 으로    L2335-L2336
     BufTableDelete(옛 tag)                         L2342
     -> true

 FlushBuffer 를 마친 뒤에도 다시 더러워질 수 있다
   share lock 은 hint bit 갱신을 막지 못한다 (주석 L2389-L2393)
```

```text
 again 으로 돌아가는 네 갈래

 어디서          갈래와 원인
 L2417           content lock 조건부 실패. 누가 내용 lock 을 쥐고 있다
 L2443           ring 의 더러운 버퍼 거절. BULKREAD 가 WAL flush 를 피하려 한다
 L2488           InvalidateVictimBuffer 실패. 쓰는 사이 누가 pin 했거나 다시 더럽혔다
 freelist.c L353 (again 이 아니라) 모든 버퍼가 pin 이면 StrategyGetBuffer 가 ERROR
```

BULKREAD ring 이 더러운 버퍼를 거절하는 데는 조건이 둘 더 붙는다. 그 버퍼를 쓰려면 WAL 까지 flush 해야 하고(`XLogNeedsFlush`), 버퍼가 ring 에서 왔어야 한다. 거절된 버퍼는 ring 슬롯에서 빠지고(`InvalidBuffer`, freelist.c L855), 그 슬롯은 다음에 일반 clock-sweep 으로 채운다. 대량 읽기 한 번이 WAL flush 를 연달아 부르지 않게 하려는 장치다.

## 결과가 쓰이는 곳

```text
 빈 버퍼 (pin 1, tag 없음)
      --> [05] BufferAlloc 이 새 tag 를 해시에 넣고 BM_TAG_VALID | usage 1 을 단다
      --> 경합이면 StrategyFreeBuffer 로 freelist 에 돌아간다
 ScheduleBufferTagForWriteback
      --> backend_flush_after 설정에 따라 모였다가 커널에 writeback 요청으로 나간다
```

## 다루지 않는 것

pg_stat_io 의 `IOOP_EVICT` / `IOOP_REUSE` 집계(L2461-L2481), writeback 제어(`IssuePendingWritebacks`), `CheckBufferIsPinnedOnce` 의 검사, `XLogNeedsFlush` 의 내부는 요약만 했다.
