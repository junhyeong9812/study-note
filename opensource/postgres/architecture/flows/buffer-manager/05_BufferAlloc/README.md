# BufferAlloc

상위: [버퍼 관리](../README.md)

**shared buffers 에서 블록의 자리를 찾거나 만든다.** `BufferTag` 의 해시로 128개 분할 중 하나를 골라 그 분할 lock 을 공유로 잡고 조회한다. 있으면 pin 하고 끝, 없으면 lock 을 놓고 희생자를 얻은 다음 배타 lock 으로 새 tag 를 해시에 넣는다. 그 사이에 다른 backend 가 같은 블록을 먼저 넣었으면 자기 희생자를 돌려주고 남의 버퍼를 쓴다. 페이지 내용을 읽지는 않는다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L2008-L2167 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L2008-L2167))

## 실제 코드

조회 단계다. hit 이면 분할 lock 을 쥔 채 pin 하고 바로 놓는다.

`src/backend/storage/buffer` / `bufmgr.c` L2008-L2066 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L2008-L2066))

```c
// bufmgr.c L2008-L2066
static pg_always_inline BufferDesc *
BufferAlloc(SMgrRelation smgr, char relpersistence, ForkNumber forkNum,
			BlockNumber blockNum,
			BufferAccessStrategy strategy,
			bool *foundPtr, IOContext io_context)
{
	BufferTag	newTag;			/* identity of requested block */
	uint32		newHash;		/* hash value for newTag */
	LWLock	   *newPartitionLock;	/* buffer partition lock for it */
	int			existing_buf_id;
	Buffer		victim_buffer;
	BufferDesc *victim_buf_hdr;
	uint32		victim_buf_state;

	/* Make sure we will have room to remember the buffer pin */
	ResourceOwnerEnlarge(CurrentResourceOwner);
	ReservePrivateRefCountEntry();

	/* create a tag so we can lookup the buffer */
	InitBufferTag(&newTag, &smgr->smgr_rlocator.locator, forkNum, blockNum);

	/* determine its hash code and partition lock ID */
	newHash = BufTableHashCode(&newTag);
	newPartitionLock = BufMappingPartitionLock(newHash);

	/* see if the block is in the buffer pool already */
	LWLockAcquire(newPartitionLock, LW_SHARED);
	existing_buf_id = BufTableLookup(&newTag, newHash);
	if (existing_buf_id >= 0)
	{
		BufferDesc *buf;
		bool		valid;

		/*
		 * Found it.  Now, pin the buffer so no one can steal it from the
		 * buffer pool, and check to see if the correct data has been loaded
		 * into the buffer.
		 */
		buf = GetBufferDescriptor(existing_buf_id);

		valid = PinBuffer(buf, strategy);

		/* Can release the mapping lock as soon as we've pinned it */
		LWLockRelease(newPartitionLock);

		*foundPtr = true;

		if (!valid)
		{
			/*
			 * We can only get here if (a) someone else is still reading in
			 * the page, (b) a previous read attempt failed, or (c) someone
			 * called StartReadBuffers() but not yet WaitReadBuffers().
			 */
			*foundPtr = false;
		}

		return buf;
	}
```

miss 단계다. 희생자를 얻고, 새 tag 로 해시 삽입을 시도한다.

`src/backend/storage/buffer` / `bufmgr.c` L2068-L2167 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L2068-L2167))

```c
// bufmgr.c L2068-L2167
	/*
	 * Didn't find it in the buffer pool.  We'll have to initialize a new
	 * buffer.  Remember to unlock the mapping lock while doing the work.
	 */
	LWLockRelease(newPartitionLock);

	/*
	 * Acquire a victim buffer. Somebody else might try to do the same, we
	 * don't hold any conflicting locks. If so we'll have to undo our work
	 * later.
	 */
	victim_buffer = GetVictimBuffer(strategy, io_context);
	victim_buf_hdr = GetBufferDescriptor(victim_buffer - 1);

	/*
	 * Try to make a hashtable entry for the buffer under its new tag. If
	 * somebody else inserted another buffer for the tag, we'll release the
	 * victim buffer we acquired and use the already inserted one.
	 */
	LWLockAcquire(newPartitionLock, LW_EXCLUSIVE);
	existing_buf_id = BufTableInsert(&newTag, newHash, victim_buf_hdr->buf_id);
	if (existing_buf_id >= 0)
	{
		BufferDesc *existing_buf_hdr;
		bool		valid;

		/*
		 * Got a collision. Someone has already done what we were about to do.
		 * We'll just handle this as if it were found in the buffer pool in
		 * the first place.  First, give up the buffer we were planning to
		 * use.
		 *
		 * We could do this after releasing the partition lock, but then we'd
		 * have to call ResourceOwnerEnlarge() & ReservePrivateRefCountEntry()
		 * before acquiring the lock, for the rare case of such a collision.
		 */
		UnpinBuffer(victim_buf_hdr);

		/*
		 * The victim buffer we acquired previously is clean and unused, let
		 * it be found again quickly
		 */
		StrategyFreeBuffer(victim_buf_hdr);

		/* remaining code should match code at top of routine */

		existing_buf_hdr = GetBufferDescriptor(existing_buf_id);

		valid = PinBuffer(existing_buf_hdr, strategy);

		/* Can release the mapping lock as soon as we've pinned it */
		LWLockRelease(newPartitionLock);

		*foundPtr = true;

		if (!valid)
		{
			/*
			 * We can only get here if (a) someone else is still reading in
			 * the page, (b) a previous read attempt failed, or (c) someone
			 * called StartReadBuffers() but not yet WaitReadBuffers().
			 */
			*foundPtr = false;
		}

		return existing_buf_hdr;
	}

	/*
	 * Need to lock the buffer header too in order to change its tag.
	 */
	victim_buf_state = LockBufHdr(victim_buf_hdr);

	/* some sanity checks while we hold the buffer header lock */
	Assert(BUF_STATE_GET_REFCOUNT(victim_buf_state) == 1);
	Assert(!(victim_buf_state & (BM_TAG_VALID | BM_VALID | BM_DIRTY | BM_IO_IN_PROGRESS)));

	victim_buf_hdr->tag = newTag;

	/*
	 * Make sure BM_PERMANENT is set for buffers that must be written at every
	 * checkpoint.  Unlogged buffers only need to be written at shutdown
	 * checkpoints, except for their "init" forks, which need to be treated
	 * just like permanent relations.
	 */
	victim_buf_state |= BM_TAG_VALID | BUF_USAGECOUNT_ONE;
	if (relpersistence == RELPERSISTENCE_PERMANENT || forkNum == INIT_FORKNUM)
		victim_buf_state |= BM_PERMANENT;

	UnlockBufHdr(victim_buf_hdr, victim_buf_state);

	LWLockRelease(newPartitionLock);

	/*
	 * Buffer contents are currently invalid.
	 */
	*foundPtr = false;

	return victim_buf_hdr;
}
```

분할 번호는 해시값을 128 로 나눈 나머지다.

`src/include/storage` / `buf_internals.h` L192-L203 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf_internals.h#L192-L203))

```c
// buf_internals.h L192-L203
static inline uint32
BufTableHashPartition(uint32 hashcode)
{
	return hashcode % NUM_BUFFER_PARTITIONS;
}

static inline LWLock *
BufMappingPartitionLock(uint32 hashcode)
{
	return &MainLWLockArray[BUFFER_MAPPING_LWLOCK_OFFSET +
							BufTableHashPartition(hashcode)].lock;
}
```

해시 테이블의 조회와 삽입이다. 삽입은 이미 있으면 그 buffer id 를, 새로 넣었으면 -1 을 돌려준다.

`src/backend/storage/buffer` / `buf_table.c` L89-L105 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/buf_table.c#L89-L105))

```c
// buf_table.c L89-L105
int
BufTableLookup(BufferTag *tagPtr, uint32 hashcode)
{
	BufferLookupEnt *result;

	result = (BufferLookupEnt *)
		hash_search_with_hash_value(SharedBufHash,
									tagPtr,
									hashcode,
									HASH_FIND,
									NULL);

	if (!result)
		return -1;

	return result->id;
}
```

## 동작 흐름

```text
 L2023-L2024  pin 기록 자리를 미리 확보 (ResourceOwner, PrivateRefCount)
 L2027  newTag = {spcOid, dbOid, relNumber, forkNum, blockNum}
 L2030  newHash = BufTableHashCode(&newTag)
 L2031  newPartitionLock = MainLWLockArray[BUFFER_MAPPING_LWLOCK_OFFSET + newHash % 128]

 ---- 조회 ------------------------------------------------------------
 L2034  LWLockAcquire(partition, LW_SHARED)
 L2035  BufTableLookup
 L2036  찾음
 L2048    valid = [06] PinBuffer(buf, strategy)       분할 lock 을 쥔 채 pin
 L2051    LWLockRelease                                pin 했으니 tag 가 못 바뀐다
 L2053    *foundPtr = true                             (valid 가 false 면 L2062 에서 false 로 고친다)
 L2065    return buf
 L2072  못 찾음 -> LWLockRelease

 ---- 희생자 ----------------------------------------------------------
 L2079  victim = [07] GetVictimBuffer(strategy, io_context)
          lock 없이 돈다. 필요하면 더러운 페이지를 쓰기까지 한다
          돌아올 때 victim 은 pin 1, tag 없음, 해시에 없음

 ---- 삽입 ------------------------------------------------------------
 L2087  LWLockAcquire(partition, LW_EXCLUSIVE)
 L2088  BufTableInsert(&newTag, newHash, victim->buf_id)
 L2089  >= 0 (경합: 누가 먼저 넣었다)
 L2104    UnpinBuffer(victim)
 L2110    StrategyFreeBuffer(victim)                   깨끗한 빈 버퍼라 freelist 앞에 돌려준다
 L2116    PinBuffer(existing)                          이후는 조회 단계와 같다
 L2133    return existing
 L2139  -1 (삽입 성공)
          LockBufHdr
 L2145    victim->tag = newTag
 L2153    state |= BM_TAG_VALID | BUF_USAGECOUNT_ONE  usage_count = 1 로 시작
 L2154    PERMANENT 거나 INIT_FORKNUM 이면 BM_PERMANENT
 L2157    UnlockBufHdr
 L2159  LWLockRelease
 L2164  *foundPtr = false                              BM_VALID 아님. 읽기는 호출자 몫
```

두 backend 가 같은 블록 B 를 동시에 miss 했을 때다. 둘 다 희생자를 얻지만 해시에는 하나만 들어간다.

```text
 시각  backend  하는 일
 t1    P        공유 lock, Lookup(B) = 없음, 해제
 t1    Q        공유 lock, Lookup(B) = 없음, 해제
 t2    P        GetVictimBuffer -> 버퍼 7
 t2    Q        GetVictimBuffer -> 버퍼 9
 t3    P        배타 lock, Insert(B, 7) = -1 (성공), tag(7) = B, BM_TAG_VALID, 해제
 t4    Q        배타 lock, Insert(B, 9) = 7 (경합)
                Unpin(9), StrategyFreeBuffer(9), PinBuffer(7) -> valid = false, 해제
 t5    P        [10] StartBufferIO(7) 성공 -> 읽기
 t5    Q        [10] StartBufferIO(7) -> I/O 진행 중이라 대기
 t6    P        완료, BM_VALID
 t6    Q        깨어나 BM_VALID 확인 -> false 반환 -> hit 처리

 블록 B 를 디스크에서 읽는 것은 한 번뿐이다
```

```text
 분할 lock 이 지키는 것과 지키지 않는 것

 지킨다      해시 테이블의 한 분할 (tag -> buffer id 대응)
             tag 교체와 해시 삽입이 한 덩어리로 보이게 한다 (L2087-L2159)
 지키지 않는다  버퍼 내용 -> content lock (LockBuffer)
             버퍼 state 의 비트 -> 헤더 spinlock (BM_LOCKED) 또는 CAS
             희생자 고르기 -> GetVictimBuffer 는 분할 lock 없이 돈다
```

## 결과가 쓰이는 곳

```text
 BufferDesc (pin 1개 추가, tag = newTag)
      --> [04] PinBufferForBlock 이 Buffer 번호로 바꿔 돌려준다
 *foundPtr == false
      --> [03] 이 I/O 범위에 넣고 [10] AsyncReadBuffers 가 StartBufferIO 로 읽기 권리를 잡는다
 usage_count = 1
      --> [08] clock-sweep 이 한 번 지나가면 0, 두 번째에 희생자 후보가 된다
```

## 다루지 않는 것

`BufTableHashCode` 의 해시 함수(`get_hash_value`, dynahash 의 파티션 해시), `BufTableDelete`, `ResourceOwnerEnlarge` 와 `ReservePrivateRefCountEntry` 의 내부, 임시 테이블의 `LocalBufferAlloc` 은 요약만 했다.
