# StrategyGetBuffer

상위: [버퍼 관리](../README.md)

**희생자 후보를 고르는 교체 정책 그 자체다.** 순서는 셋이다. 접근 전략(ring)이 있으면 ring 의 다음 슬롯을, 없거나 못 쓰면 freelist 의 맨 앞을, 그것도 비었으면 clock-sweep 을 돈다. clock-sweep 은 시계바늘(`nextVictimBuffer`)을 하나씩 돌리며 pin 이 없는 버퍼의 `usage_count` 를 1씩 깎고, 0 인 버퍼를 만나면 고른다. 고른 버퍼는 헤더 spinlock 을 쥔 채로 돌려준다. 그래야 돌려받은 쪽이 pin 하기 전에 다른 backend 가 끼어들지 못한다.

## 위치

`src/backend/storage/buffer` / `freelist.c` L195-L357 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/freelist.c#L195-L357))

## 실제 코드

ring, bgwriter 깨우기, freelist 순서다.

`src/backend/storage/buffer` / `freelist.c` L195-L312 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/freelist.c#L195-L312))

```c
// freelist.c L195-L312
BufferDesc *
StrategyGetBuffer(BufferAccessStrategy strategy, uint32 *buf_state, bool *from_ring)
{
	BufferDesc *buf;
	int			bgwprocno;
	int			trycounter;
	uint32		local_buf_state;	/* to avoid repeated (de-)referencing */

	*from_ring = false;

	/*
	 * If given a strategy object, see whether it can select a buffer. We
	 * assume strategy objects don't need buffer_strategy_lock.
	 */
	if (strategy != NULL)
	{
		buf = GetBufferFromRing(strategy, buf_state);
		if (buf != NULL)
		{
			*from_ring = true;
			return buf;
		}
	}

	// ... (L219-L230 생략: bgwriter 깨우기 설명 주석)
	bgwprocno = INT_ACCESS_ONCE(StrategyControl->bgwprocno);
	if (bgwprocno != -1)
	{
		/* reset bgwprocno first, before setting the latch */
		StrategyControl->bgwprocno = -1;

		/*
		 * Not acquiring ProcArrayLock here which is slightly icky. It's
		 * actually fine because procLatch isn't ever freed, so we just can
		 * potentially set the wrong process' (or no process') latch.
		 */
		SetLatch(&ProcGlobal->allProcs[bgwprocno].procLatch);
	}

	/*
	 * We count buffer allocation requests so that the bgwriter can estimate
	 * the rate of buffer consumption.  Note that buffers recycled by a
	 * strategy object are intentionally not counted here.
	 */
	pg_atomic_fetch_add_u32(&StrategyControl->numBufferAllocs, 1);

	// ... (L252-L267 생략: freelist 를 lock 없이 먼저 보는 이유 주석)
	if (StrategyControl->firstFreeBuffer >= 0)
	{
		while (true)
		{
			/* Acquire the spinlock to remove element from the freelist */
			SpinLockAcquire(&StrategyControl->buffer_strategy_lock);

			if (StrategyControl->firstFreeBuffer < 0)
			{
				SpinLockRelease(&StrategyControl->buffer_strategy_lock);
				break;
			}

			buf = GetBufferDescriptor(StrategyControl->firstFreeBuffer);
			Assert(buf->freeNext != FREENEXT_NOT_IN_LIST);

			/* Unconditionally remove buffer from freelist */
			StrategyControl->firstFreeBuffer = buf->freeNext;
			buf->freeNext = FREENEXT_NOT_IN_LIST;

			/*
			 * Release the lock so someone else can access the freelist while
			 * we check out this buffer.
			 */
			SpinLockRelease(&StrategyControl->buffer_strategy_lock);

			/*
			 * If the buffer is pinned or has a nonzero usage_count, we cannot
			 * use it; discard it and retry.  (This can only happen if VACUUM
			 * put a valid buffer in the freelist and then someone else used
			 * it before we got to it.  It's probably impossible altogether as
			 * of 8.3, but we'd better check anyway.)
			 */
			local_buf_state = LockBufHdr(buf);
			if (BUF_STATE_GET_REFCOUNT(local_buf_state) == 0
				&& BUF_STATE_GET_USAGECOUNT(local_buf_state) == 0)
			{
				if (strategy != NULL)
					AddBufferToRing(strategy, buf);
				*buf_state = local_buf_state;
				return buf;
			}
			UnlockBufHdr(buf, local_buf_state);
		}
	}
```

clock-sweep 이다.

`src/backend/storage/buffer` / `freelist.c` L314-L357 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/freelist.c#L314-L357))

```c
// freelist.c L314-L357
	/* Nothing on the freelist, so run the "clock sweep" algorithm */
	trycounter = NBuffers;
	for (;;)
	{
		buf = GetBufferDescriptor(ClockSweepTick());

		/*
		 * If the buffer is pinned or has a nonzero usage_count, we cannot use
		 * it; decrement the usage_count (unless pinned) and keep scanning.
		 */
		local_buf_state = LockBufHdr(buf);

		if (BUF_STATE_GET_REFCOUNT(local_buf_state) == 0)
		{
			if (BUF_STATE_GET_USAGECOUNT(local_buf_state) != 0)
			{
				local_buf_state -= BUF_USAGECOUNT_ONE;

				trycounter = NBuffers;
			}
			else
			{
				/* Found a usable buffer */
				if (strategy != NULL)
					AddBufferToRing(strategy, buf);
				*buf_state = local_buf_state;
				return buf;
			}
		}
		else if (--trycounter == 0)
		{
			/*
			 * We've scanned all the buffers without making any state changes,
			 * so all the buffers are pinned (or were when we looked at them).
			 * We could hope that someone will free one eventually, but it's
			 * probably better to fail than to risk getting stuck in an
			 * infinite loop.
			 */
			UnlockBufHdr(buf, local_buf_state);
			elog(ERROR, "no unpinned buffers available");
		}
		UnlockBufHdr(buf, local_buf_state);
	}
}
```

시계바늘 한 칸이다. 공유 카운터를 원자적으로 1 올리고 `NBuffers` 로 나눈 나머지를 쓴다. 0 으로 감긴 순간을 만든 backend 가 `completePasses` 를 올린다.

`src/backend/storage/buffer` / `freelist.c` L107-L164 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/freelist.c#L107-L164))

```c
// freelist.c L107-L164
static inline uint32
ClockSweepTick(void)
{
	uint32		victim;

	/*
	 * Atomically move hand ahead one buffer - if there's several processes
	 * doing this, this can lead to buffers being returned slightly out of
	 * apparent order.
	 */
	victim =
		pg_atomic_fetch_add_u32(&StrategyControl->nextVictimBuffer, 1);

	if (victim >= NBuffers)
	{
		uint32		originalVictim = victim;

		/* always wrap what we look up in BufferDescriptors */
		victim = victim % NBuffers;

		/*
		 * If we're the one that just caused a wraparound, force
		 * completePasses to be incremented while holding the spinlock. We
		 * need the spinlock so StrategySyncStart() can return a consistent
		 * value consisting of nextVictimBuffer and completePasses.
		 */
		if (victim == 0)
		{
			uint32		expected;
			uint32		wrapped;
			bool		success = false;

			expected = originalVictim + 1;

			while (!success)
			{
				// ... (L143-L150 생략: spinlock 을 잡는 이유 주석)
				SpinLockAcquire(&StrategyControl->buffer_strategy_lock);

				wrapped = expected % NBuffers;

				success = pg_atomic_compare_exchange_u32(&StrategyControl->nextVictimBuffer,
														 &expected, wrapped);
				if (success)
					StrategyControl->completePasses++;
				SpinLockRelease(&StrategyControl->buffer_strategy_lock);
			}
		}
	}
	return victim;
}
```

ring 의 다음 슬롯이다. 비었거나, pin 되었거나, usage_count 가 1 보다 크면 NULL 을 돌려 일반 경로로 보낸다.

`src/backend/storage/buffer` / `freelist.c` L736-L781 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/freelist.c#L736-L781))

```c
// freelist.c L736-L781
static BufferDesc *
GetBufferFromRing(BufferAccessStrategy strategy, uint32 *buf_state)
{
	BufferDesc *buf;
	Buffer		bufnum;
	uint32		local_buf_state;	/* to avoid repeated (de-)referencing */


	/* Advance to next ring slot */
	if (++strategy->current >= strategy->nbuffers)
		strategy->current = 0;

	/*
	 * If the slot hasn't been filled yet, tell the caller to allocate a new
	 * buffer with the normal allocation strategy.  He will then fill this
	 * slot by calling AddBufferToRing with the new buffer.
	 */
	bufnum = strategy->buffers[strategy->current];
	if (bufnum == InvalidBuffer)
		return NULL;

	/*
	 * If the buffer is pinned we cannot use it under any circumstances.
	 *
	 * If usage_count is 0 or 1 then the buffer is fair game (we expect 1,
	 * since our own previous usage of the ring element would have left it
	 * there, but it might've been decremented by clock sweep since then). A
	 * higher usage_count indicates someone else has touched the buffer, so we
	 * shouldn't re-use it.
	 */
	buf = GetBufferDescriptor(bufnum - 1);
	local_buf_state = LockBufHdr(buf);
	if (BUF_STATE_GET_REFCOUNT(local_buf_state) == 0
		&& BUF_STATE_GET_USAGECOUNT(local_buf_state) <= 1)
	{
		*buf_state = local_buf_state;
		return buf;
	}
	UnlockBufHdr(buf, local_buf_state);

	/*
	 * Tell caller to allocate a new buffer with the normal allocation
	 * strategy.  He'll then replace this ring element via AddBufferToRing.
	 */
	return NULL;
}
```

## 동작 흐름

```text
 L209  strategy 가 있으면 GetBufferFromRing
         current = (current + 1) % nbuffers
         슬롯이 비었음                      -> NULL
         refcount == 0 && usage <= 1        -> 이것 (from_ring = true)
         그 밖 (누가 쓰는 중)               -> NULL
       NULL 이면 아래 일반 경로. 고른 버퍼는 AddBufferToRing 으로 그 슬롯에 들어간다

 L231  bgwriter 가 잠들며 bgwprocno 를 남겼으면 깨운다 (latch)
 L250  numBufferAllocs++                     bgwriter 가 할당 속도를 추정한다

 L268  freelist 가 비지 않았으면 (lock 없이 먼저 본다)
 L273    spinlock, 맨 앞을 뗀다, spinlock 해제
 L302    refcount == 0 && usage == 0 이면 이것
         아니면 버리고 다음 것

 L315  clock-sweep, trycounter = NBuffers
 L318    buf = ClockSweepTick()
 L326    refcount == 0
 L328      usage != 0  -> usage -= 1, trycounter = NBuffers   (상태를 바꿨으니 다시 센다)
 L334      usage == 0  -> 이것
 L343    refcount != 0 (pin 됨)
           --trycounter == 0 -> ERROR "no unpinned buffers available"
```

freelist 는 기동 직후 모든 버퍼가 0 번부터 차례로 들어 있는 목록이다(buf_init.c L135-L144, freelist.c L511-L512). 한 번 빠진 버퍼는 `StrategyFreeBuffer` 를 부르는 곳, 즉 relation drop 같은 `InvalidateBuffer`(bufmgr.c L2273), [05] 의 경합 처리(L2110), 릴레이션 확장이 쓰지 않은 희생자를 돌려줄 때(`ExtendBufferedRelShared`, L2709, L2789)로만 돌아온다. 평상시 희생자는 clock-sweep 이 고른다.

아래는 `NBuffers = 4` 로 줄인 예다(기본값은 16384, globals.c L142). 시계바늘은 0 에서 시작하고 freelist 는 비었다.

```text
 start         buf 0      buf 1      buf 2      buf 3
 (ref, usage)  (0, 1)     (2, 5)     (0, 2)     (0, 1)

 tick  fetch_add  victim  ref  usage   trycounter  판정
 1     0          0       0    1 -> 0  4           usage 를 깎고 리셋
 2     1          1       2    5       3           pin 됨
 3     2          2       0    2 -> 1  4           usage 를 깎고 리셋
 4     3          3       0    1 -> 0  4           usage 를 깎고 리셋
 5     4          0       0    0       4           희생자

 tick 5: fetch_add 가 4 를 돌려줬다 -> 4 >= NBuffers 라 victim = 4 % 4 = 0
         victim == 0 이므로 이 backend 가 감김을 처리한다
         nextVictimBuffer 를 5 에서 5 % 4 = 1 로 CAS, completePasses++
 결과   buf 0 을 헤더 spinlock 을 쥔 채 돌려준다. 다음 바늘 위치는 1

 end           buf 0      buf 1      buf 2      buf 3
 (ref, usage)  (0, 0)*    (2, 5)     (0, 1)     (0, 0)
 * 이 직후 GetVictimBuffer 가 PinBuffer_Locked 로 ref 1 을 건다
```

```text
 usage_count 가 뜻하는 것

 PinBuffer 한 번 (기본 전략)     +1, 최대 5
 clock-sweep 이 지나갈 때         -1 (pin 이 없을 때만)
 새 블록을 받은 버퍼              1 로 시작 (BufferAlloc L2153)

 usage 5 인 버퍼는 아무도 다시 pin 하지 않으면 바늘이 다섯 번 지나간 뒤 여섯 번째에 뽑힌다
 그래서 빈 버퍼를 찾는 데 최대 BM_MAX_USAGE_COUNT + 1 바퀴가 걸릴 수 있다
   (buf_internals.h L80-L86 주석)
```

```text
 trycounter 가 지키는 것

 usage 를 하나라도 깎으면 NBuffers 로 리셋한다. 다음 바퀴에 0 이 될 버퍼가 생겼기 때문이다
 pin 된 버퍼만 연달아 NBuffers 개를 보면, 즉 한 바퀴 내내 아무 상태도 못 바꾸면 ERROR
 무한 루프 대신 실패를 고른 이유는 주석 L345-L351 에 있다
```

ring 크기는 전략마다 다르다. `BAS_BULKREAD` 는 256kB 에서 시작해 `io_combine_limit * effective_io_concurrency` 만큼 키우되 pin 한도를 넘지 않게 자르고(freelist.c L574-L599), `BAS_BULKWRITE` 는 16MB(L603), `BAS_VACUUM` 은 2048kB(L606)다.

## 결과가 쓰이는 곳

```text
 후보 버퍼 (헤더 spinlock 쥔 채, refcount 0)
      --> [07] GetVictimBuffer 가 PinBuffer_Locked 로 pin 하고 lock 을 푼다
 from_ring
      --> [07] 의 StrategyRejectBuffer 판정과 pg_stat_io 의 reuse/evict 구분
 nextVictimBuffer, completePasses, numBufferAllocs
      --> bgwriter 의 BgBufferSync 가 StrategySyncStart 로 읽어
          바늘보다 앞서 더러운 버퍼를 미리 쓴다
```

## 다루지 않는 것

bgwriter 쪽 계산(`BgBufferSync` 의 할당 속도 추정과 `bgwriter_lru_multiplier`), `StrategyNotifyBgWriter`, ring 객체 생성(`GetAccessStrategy`, `GetAccessStrategyWithSize`), `StrategyFreeBuffer` 와 `InvalidateBuffer` 의 freelist 반환 경로, `StrategyInitialize` 는 요약만 했다.
