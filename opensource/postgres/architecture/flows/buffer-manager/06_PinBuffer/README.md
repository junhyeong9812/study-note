# PinBuffer

상위: [버퍼 관리](../README.md)

**버퍼를 교체 대상에서 빼는 일, 즉 pin 이다.** 공유 state 의 refcount 를 1 올리고 같은 CAS 안에서 `usage_count` 도 올린다. 기본 전략이면 최대 5까지, ring 전략이면 0 일 때만 1로 올린다. 같은 backend 가 이미 pin 한 버퍼면 공유 state 는 건드리지 않고 backend 지역 카운트만 올린다. pin 은 "내용을 읽어도 된다"는 허락이 아니다. 내용을 보려면 따로 content lock(`LockBuffer`)을 잡아야 하고, 이 문서 끝에서 둘을 나란히 놓는다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L3089-L3176 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L3089-L3176))

## 실제 코드

```c
// bufmgr.c L3089-L3176
static bool
PinBuffer(BufferDesc *buf, BufferAccessStrategy strategy)
{
	Buffer		b = BufferDescriptorGetBuffer(buf);
	bool		result;
	PrivateRefCountEntry *ref;

	Assert(!BufferIsLocal(b));
	Assert(ReservedRefCountEntry != NULL);

	ref = GetPrivateRefCountEntry(b, true);

	if (ref == NULL)
	{
		uint32		buf_state;
		uint32		old_buf_state;

		ref = NewPrivateRefCountEntry(b);

		old_buf_state = pg_atomic_read_u32(&buf->state);
		for (;;)
		{
			if (old_buf_state & BM_LOCKED)
				old_buf_state = WaitBufHdrUnlocked(buf);

			buf_state = old_buf_state;

			/* increase refcount */
			buf_state += BUF_REFCOUNT_ONE;

			if (strategy == NULL)
			{
				/* Default case: increase usagecount unless already max. */
				if (BUF_STATE_GET_USAGECOUNT(buf_state) < BM_MAX_USAGE_COUNT)
					buf_state += BUF_USAGECOUNT_ONE;
			}
			else
			{
				/*
				 * Ring buffers shouldn't evict others from pool.  Thus we
				 * don't make usagecount more than 1.
				 */
				if (BUF_STATE_GET_USAGECOUNT(buf_state) == 0)
					buf_state += BUF_USAGECOUNT_ONE;
			}

			if (pg_atomic_compare_exchange_u32(&buf->state, &old_buf_state,
											   buf_state))
			{
				result = (buf_state & BM_VALID) != 0;

				// ... (L3140-L3147 생략: Valgrind 표시)
				break;
			}
		}
	}
	else
	{
		// ... (L3154-L3168 생략: Valgrind 관련 주석)
		result = (pg_atomic_read_u32(&buf->state) & BM_VALID) != 0;
	}

	ref->refcount++;
	Assert(ref->refcount > 0);
	ResourceOwnerRememberBuffer(CurrentResourceOwner, b);
	return result;
}
```

희생자를 잡을 때는 헤더 spinlock 을 쥔 채 pin 해야 해서 별도 함수를 쓴다. usage_count 는 건드리지 않는다.

`src/backend/storage/buffer` / `bufmgr.c` L3200-L3235 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L3200-L3235))

```c
// bufmgr.c L3200-L3235
static void
PinBuffer_Locked(BufferDesc *buf)
{
	Buffer		b;
	PrivateRefCountEntry *ref;
	uint32		buf_state;

	/*
	 * As explained, We don't expect any preexisting pins. That allows us to
	 * manipulate the PrivateRefCount after releasing the spinlock
	 */
	Assert(GetPrivateRefCountEntry(BufferDescriptorGetBuffer(buf), false) == NULL);

	// ... (L3213-L3218 생략: Valgrind 표시)

	/*
	 * Since we hold the buffer spinlock, we can update the buffer state and
	 * release the lock in one operation.
	 */
	buf_state = pg_atomic_read_u32(&buf->state);
	Assert(buf_state & BM_LOCKED);
	buf_state += BUF_REFCOUNT_ONE;
	UnlockBufHdr(buf, buf_state);

	b = BufferDescriptorGetBuffer(buf);

	ref = NewPrivateRefCountEntry(b);
	ref->refcount++;

	ResourceOwnerRememberBuffer(CurrentResourceOwner, b);
}
```

unpin 이다. backend 지역 카운트가 0 이 될 때만 공유 refcount 를 내린다.

`src/backend/storage/buffer` / `bufmgr.c` L3290-L3347 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L3290-L3347))

```c
// bufmgr.c L3290-L3347
static void
UnpinBufferNoOwner(BufferDesc *buf)
{
	PrivateRefCountEntry *ref;
	Buffer		b = BufferDescriptorGetBuffer(buf);

	Assert(!BufferIsLocal(b));

	/* not moving as we're likely deleting it soon anyway */
	ref = GetPrivateRefCountEntry(b, false);
	Assert(ref != NULL);
	Assert(ref->refcount > 0);
	ref->refcount--;
	if (ref->refcount == 0)
	{
		uint32		buf_state;
		uint32		old_buf_state;

		// ... (L3308-L3315 생략: Valgrind 표시)

		/* I'd better not still hold the buffer content lock */
		Assert(!LWLockHeldByMe(BufferDescriptorGetContentLock(buf)));

		/*
		 * Decrement the shared reference count.
		 *
		 * Since buffer spinlock holder can update status using just write,
		 * it's not safe to use atomic decrement here; thus use a CAS loop.
		 */
		old_buf_state = pg_atomic_read_u32(&buf->state);
		for (;;)
		{
			if (old_buf_state & BM_LOCKED)
				old_buf_state = WaitBufHdrUnlocked(buf);

			buf_state = old_buf_state;

			buf_state -= BUF_REFCOUNT_ONE;

			if (pg_atomic_compare_exchange_u32(&buf->state, &old_buf_state,
											   buf_state))
				break;
		}

		/* Support LockBufferForCleanup() */
		if (buf_state & BM_PIN_COUNT_WAITER)
			WakePinCountWaiter(buf);

		ForgetPrivateRefCountEntry(ref);
	}
}
```

content lock 이다. 버퍼마다 LWLock 하나가 있고, 임시 테이블 버퍼는 lock 이 없다.

`src/backend/storage/buffer` / `bufmgr.c` L5622-L5641 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L5622-L5641))

```c
// bufmgr.c L5622-L5641
void
LockBuffer(Buffer buffer, int mode)
{
	BufferDesc *buf;

	Assert(BufferIsPinned(buffer));
	if (BufferIsLocal(buffer))
		return;					/* local buffers need no lock */

	buf = GetBufferDescriptor(buffer - 1);

	if (mode == BUFFER_LOCK_UNLOCK)
		LWLockRelease(BufferDescriptorGetContentLock(buf));
	else if (mode == BUFFER_LOCK_SHARE)
		LWLockAcquire(BufferDescriptorGetContentLock(buf), LW_SHARED);
	else if (mode == BUFFER_LOCK_EXCLUSIVE)
		LWLockAcquire(BufferDescriptorGetContentLock(buf), LW_EXCLUSIVE);
	else
		elog(ERROR, "unrecognized buffer lock mode: %d", mode);
}
```

## 동작 흐름

```text
 L3099  ref = GetPrivateRefCountEntry(b)        이 backend 가 이미 pin 했나
 L3101  처음이면
 L3106    NewPrivateRefCountEntry(b)
 L3108    old = state 를 읽는다
 L3109    for (;;)
 L3111      BM_LOCKED 면 풀릴 때까지 기다린다   (헤더 spinlock 쥔 쪽은 CAS 없이 쓰므로)
 L3117      state += BUF_REFCOUNT_ONE
 L3119      strategy == NULL   usage < 5 면 usage += 1
 L3125      strategy != NULL   usage == 0 일 때만 1 로
 L3135      CAS(old -> new) 성공하면 result = BM_VALID 여부, break
              실패하면 old 가 최신 값으로 바뀌어 다시 돈다
 L3152  이미 pin 했으면
 L3169    result = BM_VALID 여부 (lock 없이 읽는다)
 L3172  ref->refcount++                         backend 지역 카운트
 L3174  ResourceOwnerRememberBuffer              에러로 빠져도 풀리게 기록
```

```text
 pin 한 번이 state 에 하는 일 (기본 전략, 예시)

 시점                 usage  refcount  설명
 before               3      2         다른 backend 둘이 pin 중, BM_VALID
 PinBuffer            4      3         CAS 한 번
 PinBuffer (또, 같은 backend)
                      4      3         공유 state 는 그대로, PrivateRefCount 만 2

 usage 가 5 면 더 오르지 않는다 (BM_MAX_USAGE_COUNT, buf_internals.h L87)
 ring 전략이면 usage 3 인 버퍼를 pin 해도 3 그대로다. 0 일 때만 1 이 된다
```

주석 L3069-L3075 가 ring 의 규칙을 설명한다. 대량 순차 읽기가 usage_count 를 부풀려 다른 버퍼를 몰아내면 안 되지만, 0 으로 두면 다른 backend 가 ring 의 버퍼를 바로 빼앗아 간다. 그래서 1 까지만 올린다.

```text
 unpin 의 두 층 (UnpinBufferNoOwner)

 L3302  ref->refcount--                   backend 지역
 L3303  0 이 되었을 때만
 L3326    CAS 루프로 state -= BUF_REFCOUNT_ONE   공유 (L3326-L3339)
 L3342    BM_PIN_COUNT_WAITER 면 WakePinCountWaiter  (cleanup lock 대기자)
 L3345    ForgetPrivateRefCountEntry

 한 backend 가 같은 버퍼를 열 번 pin 해도 공유 refcount 는 1 만 오른다
 그래서 refcount 18비트는 "pin 한 backend 수"를 센다 (MAX_BACKENDS_BITS <= 18, buf_internals.h L91)
 예외: AIO 가 버퍼를 맡는 동안 AIO 몫 pin 1 이 더해진다 (bufmgr.c L6876, 완료 때 TerminateBufferIO 가 뺀다)
```

pin 과 content lock 은 지키는 대상이 다르다. 둘을 같이 쥐어야 페이지 내용을 안전하게 읽는다.

```text
 pin
   함수         PinBuffer / UnpinBuffer
   자료         state 의 refcount 18비트
   막는 것      교체 (tag 가 바뀌는 것)
   쥐는 시간    버퍼를 들고 있는 동안 내내
   공유 / 배타  구분 없음
   임시 테이블  LocalRefCount
   순서         먼저

 content lock
   함수         LockBuffer(SHARE | EXCLUSIVE | UNLOCK)
   자료         BufferDesc 의 LWLock (content_lock)
   막는 것      내용 동시 읽기/쓰기
   쥐는 시간    페이지를 실제로 만지는 동안만
   공유 / 배타  SHARE 여럿, EXCLUSIVE 하나
   임시 테이블  없음 (L5628 바로 return)
   순서         pin 한 뒤에만 (Assert BufferIsPinned, L5627)
```

## 결과가 쓰이는 곳

```text
 반환값 (BM_VALID 여부)
      --> [05] BufferAlloc 이 *foundPtr 로 옮긴다
 usage_count
      --> [08] StrategyGetBuffer 의 clock-sweep 이 깎는다
 refcount > 0
      --> [08] 은 refcount 가 0 이 아닌 버퍼를 건너뛴다
      --> [07] InvalidateVictimBuffer 는 refcount 가 1(자기 것)이 아니면 포기한다
 content lock
      --> [07] GetVictimBuffer 는 쓰기 전에 SHARE 를 조건부로 잡는다
      --> MarkBufferDirty 는 EXCLUSIVE 를 쥔 상태를 요구한다 (L2988)
```

## 다루지 않는 것

`PrivateRefCountArray` 와 오버플로 해시(`GetPrivateRefCountEntry`, `ReservePrivateRefCountEntry`), ResourceOwner 의 버퍼 추적, cleanup lock(`LockBufferForCleanup`, `BM_PIN_COUNT_WAITER`), `ConditionalLockBuffer`, LWLock 자체의 구현은 요약만 했다.
