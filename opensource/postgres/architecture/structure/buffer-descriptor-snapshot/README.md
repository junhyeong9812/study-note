# 버퍼 디스크립터와 스냅샷

상위: [PostgreSQL 아키텍처 지도](../../README.md)

backend 가 페이지를 읽을 때 손에 쥐는 두 가지 구조를 본다. 하나는 **어느 페이지가 메모리 어디에 있는가**를 적은 버퍼 디스크립터이고, 다른 하나는 **그 페이지의 튜플 중 무엇이 보이는가**를 정하는 스냅샷이다. 공유 버퍼는 공유 메모리 안의 평행한 배열 넷이다. 64바이트 디스크립터 `NBuffers` 개, 8192바이트 페이지 `NBuffers` 개, I/O 대기용 조건 변수, 체크포인트 정렬용 배열이다. 디스크립터 i 와 페이지 i 는 같은 번호로 짝지어지고, `Buffer` 번호는 i + 1 이다. 디스크립터는 `BufferTag`(테이블스페이스, DB, relfilenode, fork, 블록) 20바이트로 "지금 이 자리에 든 페이지"를 밝히고, pin 수, `usage_count`, 플래그를 32비트 정수 하나(`state`)에 묶어 CAS 로 바꾼다. tag 에서 버퍼 번호를 찾는 해시 테이블은 128개 분할로 나뉘고 분할마다 LWLock 이 하나씩 있다. 스냅샷은 backend 지역 메모리의 `SnapshotData` 다. MVCC 스냅샷이면 `xmin`, `xmax`, 진행 중 xid 배열 `xip`, 하위 트랜잭션 배열 `subxip`, 명령 번호 `curcid` 로 가시성을 정하고, 그 밖의 종류(`SNAPSHOT_SELF`, `SNAPSHOT_DIRTY` 등)는 `snapshot_type` 하나로 판정 규칙을 바꾼다. 버퍼를 찾아 pin 하는 동작은 [버퍼 관리](../../flows/buffer-manager/README.md)가, 스냅샷을 만들고 튜플에 대어 보는 동작은 [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md)이 다룬다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이다. 경로는 `src/` 부터 적고, `src/backend/` 아래 파일만 그 뒤부터 적는다. 구조체 크기와 오프셋은 x86-64 기준이며, 이 태그의 헤더(`buf_internals.h`, `snapshot.h`)를 gcc 로 컴파일해 `offsetof` 로 확인한 값이다.

## 전체 그림

```text
 공유 메모리 (shared_buffers = 128MB 기본 -> NBuffers = 16384, guc_tables.c L2385)

 BufferDescriptors   BufferDescPadded[16384]   64 x 16384  = 1MB        buf_init.c L76
 +-------+-------+-------+-- ... --+-------+
 | id 0  | id 1  | id 2  |         | 16383 |   BufferDesc 하나 = 64바이트 = 캐시 라인 하나
 +-------+-------+-------+-- ... --+-------+
     |       |       |
     v       v       v               같은 번호로 짝 (BufHdrGetBlock, bufmgr.c L72)
 BufferBlocks        char[16384 * 8192]        128MB (+ PG_IO_ALIGN_SIZE)  buf_init.c L82
 +-------+-------+-------+-- ... --+-------+
 | 8KB   | 8KB   | 8KB   |         | 8KB   |
 +-------+-------+-------+-- ... --+-------+
 BufferIOCVArray     ConditionVariable[16384]   I/O 끝을 기다리는 backend 가 잔다
 CkptBufferIds       CkptSortItem[16384]        체크포인트가 쓸 버퍼를 파일 순으로 정렬

 SharedBufHash  "Shared Buffer Lookup Table"   BufferTag -> buf_id
   항목 수 NBuffers + 128 = 16512 (freelist.c L488),  분할 128개
   분할 p 의 잠금 = MainLWLockArray[BUFFER_MAPPING_LWLOCK_OFFSET + p]

 Buffer 번호 (backend 가 들고 다니는 int)
   0          InvalidBuffer
   1..16384   공유 버퍼. buf_id = Buffer - 1
   -1..-N     backend 지역 버퍼 (임시 테이블). LocalBufferDescriptors[-Buffer - 1]
```

```text
 backend 지역 메모리

 static SnapshotData CurrentSnapshotData     GetTransactionSnapshot 이 채운다   snapmgr.c L140
 static SnapshotData SecondarySnapshotData   GetLatestSnapshot                 L141
 static SnapshotData CatalogSnapshotData     GetCatalogSnapshot                L142
        각자 xip[], subxip[] 를 처음 한 번 malloc 해서 계속 재사용 (procarray.c L2206-L2225)
            |
            |  PushActiveSnapshot / RegisterSnapshot 이 CopySnapshot 으로 복사
            v
 TopTransactionContext 의 복사본  [SnapshotData 104][xip xcnt 개][subxip subxcnt 개]
            |                                   |
            v                                   v
 ActiveSnapshot 스택 (active_count)     RegisteredSnapshots pairing heap (regd_count, xmin 순)
```

## BufferTag

tag 는 "이 버퍼에 든 것이 디스크의 어느 블록인가"다. 카탈로그를 보지 않고도 파일을 찾아 쓸 수 있어야 하므로, [디스크 배치](../disk-layout/README.md)의 `RelFileLocator` 세 값에 fork 와 블록 번호를 더한 다섯 값이 전부다. 해시 키로 쓰기 때문에 패딩 바이트가 없어야 한다(주석 L103-L104).

`src` / `include` / `storage` / `buf_internals.h` L94-L113 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf_internals.h#L94-L113))

```c
// src/include/storage/buf_internals.h L94-L113
/*
 * Buffer tag identifies which disk block the buffer contains.
 *
 * Note: the BufferTag data must be sufficient to determine where to write the
 * block, without reference to pg_class or pg_tablespace entries.  It's
 * possible that the backend flushing the buffer doesn't even believe the
 * relation is visible yet (its xact may have started before the xact that
 * created the rel).  The storage manager must be able to cope anyway.
 *
 * Note: if there's any pad bytes in the struct, InitBufferTag will have
 * to be fixed to zero them, since this struct is used as a hash key.
 */
typedef struct buftag
{
	Oid			spcOid;			/* tablespace oid */
	Oid			dbOid;			/* database oid */
	RelFileNumber relNumber;	/* relation file number */
	ForkNumber	forkNum;		/* fork number */
	BlockNumber blockNum;		/* blknum relative to begin of reln */
} BufferTag;
```

```text
 BufferTag  (20바이트, 패딩 없음)

 offset  size  field      예: base/5/16385 의 main fork 블록 200000
 ------  ----  ---------  ------------------------------------------
      0     4  spcOid     1663  (pg_default)
      4     4  dbOid      5
      8     4  relNumber  16385
     12     4  forkNum    0     (MAIN_FORKNUM, enum 이라 4바이트)
     16     4  blockNum   200000
     20

 같은 tag 가 버퍼 해시의 키, 체크포인트 정렬 키(CkptSortItem), WAL 블록 참조(RelFileLocator + BlockNumber)로
 모양만 바꿔 쓰인다
```

## BufferDesc

디스크립터 하나는 64바이트이고, 공유 버퍼 배열에서는 정확히 캐시 라인 하나를 차지하도록 패딩 공용체로 감싼다. 이웃 버퍼의 헤더를 다른 CPU 가 만질 때 같은 캐시 라인을 다투지 않게 하려는 것이다(주석 L273-L291).

`src` / `include` / `storage` / `buf_internals.h` L211-L299 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf_internals.h#L211-L299))

```c
// src/include/storage/buf_internals.h L211-L299
/*
 *	BufferDesc -- shared descriptor/state data for a single shared buffer.
 *
 * Note: Buffer header lock (BM_LOCKED flag) must be held to examine or change
 * tag, state or wait_backend_pgprocno fields.  In general, buffer header lock
 * is a spinlock which is combined with flags, refcount and usagecount into
 * single atomic variable.  This layout allow us to do some operations in a
 * single atomic operation, without actually acquiring and releasing spinlock;
 * for instance, increase or decrease refcount.  buf_id field never changes
 * after initialization, so does not need locking.  freeNext is protected by
 * the buffer_strategy_lock not buffer header lock.  The LWLock can take care
 * of itself.  The buffer header lock is *not* used to control access to the
 * data in the buffer!
 *
 // ... (L225-L256 생략: state 를 잠금 없이 바꿀 때의 규칙(CAS 만 허용), pin 된 버퍼의 tag 는 잠금 없이 읽어도 된다는 예외, cleanup lock 대기자, 지역 버퍼, 크기 상한)
 */
typedef struct BufferDesc
{
	BufferTag	tag;			/* ID of page contained in buffer */
	int			buf_id;			/* buffer's index number (from 0) */

	/* state of the tag, containing flags, refcount and usagecount */
	pg_atomic_uint32 state;

	int			wait_backend_pgprocno;	/* backend of pin-count waiter */
	int			freeNext;		/* link in freelist chain */

	PgAioWaitRef io_wref;		/* set iff AIO is in progress */
	LWLock		content_lock;	/* to lock access to buffer contents */
} BufferDesc;

// ... (L273-L292 생략: 캐시 라인 64바이트로 맞추는 이유와 32비트 예외)
#define BUFFERDESC_PAD_TO_SIZE	(SIZEOF_VOID_P == 8 ? 64 : 1)

typedef union BufferDescPadded
{
	BufferDesc	bufferdesc;
	char		pad[BUFFERDESC_PAD_TO_SIZE];
} BufferDescPadded;
```

```text
 BufferDesc  (64바이트, LOCK_DEBUG 아님)

 offset  size  field                    지키는 잠금
 ------  ----  -----------------------  --------------------------------------------
      0    20  tag                      버퍼 헤더 잠금 (BM_LOCKED). pin 했으면 잠금 없이 읽어도 된다
     20     4  buf_id                   초기화 뒤 바뀌지 않는다
     24     4  state                    아래 32비트 배치. CAS, 또는 BM_LOCKED 를 쥔 쪽이 한 번에 쓴다
     28     4  wait_backend_pgprocno    BM_PIN_COUNT_WAITER 일 때 기다리는 backend
     32     4  freeNext                 freelist 다음 buf_id. -1 끝, -2 목록 밖  (buffer_strategy_lock)
     36    12  io_wref                  진행 중 AIO 핸들 참조 (aio_index, generation_upper, generation_lower)
     48    16  content_lock             LWLock: tranche 2 + (패딩 2) + state 4 + waiters 8
     64

 헤더 잠금(BM_LOCKED)은 디스크립터 메타데이터를, content_lock 은 BufferBlocks 의 페이지 내용을 지킨다
 둘은 다른 잠금이다 (주석 L222-L223 "The buffer header lock is *not* used to control access
 to the data in the buffer!")
```

배열을 만들고 디스크립터를 초기화하는 곳은 공유 메모리 초기화 때 한 번 도는 `BufferManagerShmemInit` 이다. 처음에는 모든 버퍼가 freelist 에 0 -> 1 -> 2 순으로 이어져 있다.

`storage` / `buffer` / `buf_init.c` L67-L145 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/buf_init.c#L67-L145))

```c
// storage/buffer/buf_init.c L67-L145
void
BufferManagerShmemInit(void)
{
	bool		foundBufs,
				foundDescs,
				foundIOCV,
				foundBufCkpt;

	/* Align descriptors to a cacheline boundary. */
	BufferDescriptors = (BufferDescPadded *)
		ShmemInitStruct("Buffer Descriptors",
						NBuffers * sizeof(BufferDescPadded),
						&foundDescs);

	/* Align buffer pool on IO page size boundary. */
	BufferBlocks = (char *)
		TYPEALIGN(PG_IO_ALIGN_SIZE,
				  ShmemInitStruct("Buffer Blocks",
								  NBuffers * (Size) BLCKSZ + PG_IO_ALIGN_SIZE,
								  &foundBufs));

	/* Align condition variables to cacheline boundary. */
	BufferIOCVArray = (ConditionVariableMinimallyPadded *)
		ShmemInitStruct("Buffer IO Condition Variables",
						NBuffers * sizeof(ConditionVariableMinimallyPadded),
						&foundIOCV);

	// ... (L94-L110 생략: 체크포인트 정렬 배열과 EXEC_BACKEND 재부착 확인)
	else
	{
		int			i;

		/*
		 * Initialize all the buffer headers.
		 */
		for (i = 0; i < NBuffers; i++)
		{
			BufferDesc *buf = GetBufferDescriptor(i);

			ClearBufferTag(&buf->tag);

			pg_atomic_init_u32(&buf->state, 0);
			buf->wait_backend_pgprocno = INVALID_PROC_NUMBER;

			buf->buf_id = i;

			pgaio_wref_clear(&buf->io_wref);

			/*
			 * Initially link all the buffers together as unused. Subsequent
			 * management of this list is done by freelist.c.
			 */
			buf->freeNext = i + 1;

			LWLockInitialize(BufferDescriptorGetContentLock(buf),
							 LWTRANCHE_BUFFER_CONTENT);

			ConditionVariableInit(BufferDescriptorGetIOCV(buf));
		}

		/* Correct last entry of linked list */
		GetBufferDescriptor(NBuffers - 1)->freeNext = FREENEXT_END_OF_LIST;
	}
```

`Buffer` 번호와 디스크립터, 페이지 주소 사이의 변환은 덧셈과 곱셈이다.

`src` / `include` / `storage` / `buf.h` L17-L37 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf.h#L17-L37))

```c
// src/include/storage/buf.h L17-L37
/*
 * Buffer identifiers.
 *
 * Zero is invalid, positive is the index of a shared buffer (1..NBuffers),
 * negative is the index of a local buffer (-1 .. -NLocBuffer).
 */
typedef int Buffer;

#define InvalidBuffer	0

/*
 * BufferIsInvalid
 *		True iff the buffer is invalid.
 */
#define BufferIsInvalid(buffer) ((buffer) == InvalidBuffer)

/*
 * BufferIsLocal
 *		True iff the buffer is local (not visible to other backends).
 */
#define BufferIsLocal(buffer)	((buffer) < 0)
```

`src` / `include` / `storage` / `buf_internals.h` L345-L349 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf_internals.h#L345-L349))

```c
// src/include/storage/buf_internals.h L345-L349
static inline Buffer
BufferDescriptorGetBuffer(const BufferDesc *bdesc)
{
	return (Buffer) (bdesc->buf_id + 1);
}
```

`src` / `include` / `storage` / `bufmgr.h` L383-L392 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/bufmgr.h#L383-L392))

```c
// src/include/storage/bufmgr.h L383-L392
static inline Block
BufferGetBlock(Buffer buffer)
{
	Assert(BufferIsValid(buffer));

	if (BufferIsLocal(buffer))
		return LocalBufferBlockPointers[-buffer - 1];
	else
		return (Block) (BufferBlocks + ((Size) (buffer - 1)) * BLCKSZ);
}
```

```text
 Buffer 1000 의 자리 (BLCKSZ 8192)

 buf_id      = 1000 - 1                      = 999
 descriptor  = BufferDescriptors + 999 * 64  = +63936      GetBufferDescriptor(999)
 page        = BufferBlocks + 999 * 8192     = +8183808    BufferGetBlock(1000)
 io cv       = BufferIOCVArray[999]                        BufferDescriptorGetIOCV
```

## state 32비트

pin 수(refcount), `usage_count`, 플래그를 한 정수에 묶은 이유는 헤더 잠금 없이 CAS 한 번으로 셋을 함께 바꾸기 위해서다(주석 L39-L40). 헤더 잠금 자체도 별도 spinlock 이 아니라 이 정수의 22번 비트(`BM_LOCKED`)다. 비트 배치 그림과 플래그별 뜻은 [버퍼 관리](../../flows/buffer-manager/README.md)의 전체 그림에 있다.

`src` / `include` / `storage` / `buf_internals.h` L32-L92 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf_internals.h#L32-L92))

```c
// src/include/storage/buf_internals.h L32-L92
/*
 * Buffer state is a single 32-bit variable where following data is combined.
 *
 * - 18 bits refcount
 * - 4 bits usage count
 * - 10 bits of flags
 *
 * Combining these values allows to perform some operations without locking
 * the buffer header, by modifying them together with a CAS loop.
 *
 * The definition of buffer state components is below.
 */
#define BUF_REFCOUNT_BITS 18
#define BUF_USAGECOUNT_BITS 4
#define BUF_FLAG_BITS 10

StaticAssertDecl(BUF_REFCOUNT_BITS + BUF_USAGECOUNT_BITS + BUF_FLAG_BITS == 32,
				 "parts of buffer state space need to equal 32");

#define BUF_REFCOUNT_ONE 1
#define BUF_REFCOUNT_MASK ((1U << BUF_REFCOUNT_BITS) - 1)
#define BUF_USAGECOUNT_MASK (((1U << BUF_USAGECOUNT_BITS) - 1) << (BUF_REFCOUNT_BITS))
#define BUF_USAGECOUNT_ONE (1U << BUF_REFCOUNT_BITS)
#define BUF_USAGECOUNT_SHIFT BUF_REFCOUNT_BITS
#define BUF_FLAG_MASK (((1U << BUF_FLAG_BITS) - 1) << (BUF_REFCOUNT_BITS + BUF_USAGECOUNT_BITS))

/* Get refcount and usagecount from buffer state */
#define BUF_STATE_GET_REFCOUNT(state) ((state) & BUF_REFCOUNT_MASK)
#define BUF_STATE_GET_USAGECOUNT(state) (((state) & BUF_USAGECOUNT_MASK) >> BUF_USAGECOUNT_SHIFT)

/*
 * Flags for buffer descriptors
 *
 * Note: BM_TAG_VALID essentially means that there is a buffer hashtable
 * entry associated with the buffer's tag.
 */
#define BM_LOCKED				(1U << 22)	/* buffer header is locked */
#define BM_DIRTY				(1U << 23)	/* data needs writing */
#define BM_VALID				(1U << 24)	/* data is valid */
#define BM_TAG_VALID			(1U << 25)	/* tag is assigned */
#define BM_IO_IN_PROGRESS		(1U << 26)	/* read or write in progress */
#define BM_IO_ERROR				(1U << 27)	/* previous I/O failed */
#define BM_JUST_DIRTIED			(1U << 28)	/* dirtied since write started */
#define BM_PIN_COUNT_WAITER		(1U << 29)	/* have waiter for sole pin */
#define BM_CHECKPOINT_NEEDED	(1U << 30)	/* must write for checkpoint */
#define BM_PERMANENT			(1U << 31)	/* permanent buffer (not unlogged,
											 * or init fork) */
// ... (L79-L86 생략: usage_count 상한이 크면 LRU 에 가까워지지만 clock-sweep 이 최대 상한+1 바퀴 돌 수 있다는 설명)
#define BM_MAX_USAGE_COUNT	5

StaticAssertDecl(BM_MAX_USAGE_COUNT < (1 << BUF_USAGECOUNT_BITS),
				 "BM_MAX_USAGE_COUNT doesn't fit in BUF_USAGECOUNT_BITS bits");
StaticAssertDecl(MAX_BACKENDS_BITS <= BUF_REFCOUNT_BITS,
				 "MAX_BACKENDS_BITS needs to be <= BUF_REFCOUNT_BITS");
```

```text
 state 값 하나를 손으로 풀어 보기

 상황: 두 backend 가 pin, usage_count 3, 내용 유효, tag 있음, 더러움, WAL 대상

 refcount    2                                   = 0x00000002
 usage       3 << 18                             = 0x000C0000
 BM_DIRTY    1 << 23                             = 0x00800000
 BM_VALID    1 << 24                             = 0x01000000
 BM_TAG_VALID 1 << 25                            = 0x02000000
 BM_PERMANENT 1 << 31                            = 0x80000000
 ------------------------------------------------------------
 state                                           = 0x838C0002

 BUF_STATE_GET_REFCOUNT(0x838C0002)   = 0x838C0002 & 0x3FFFF            = 2
 BUF_STATE_GET_USAGECOUNT(0x838C0002) = (0x838C0002 & 0x3C0000) >> 18   = 3

 pin 하나 더: CAS(state, state + BUF_REFCOUNT_ONE)         -> 0x838C0003
             전략 없이 읽고 usage 가 5 미만이면 + BUF_USAGECOUNT_ONE 도  -> 0x83900003
             (전략이 있으면 usage 를 1 넘게 올리지 않는다 - bufmgr.c L3119-L3133)
             (BM_LOCKED 가 켜져 있으면 CAS 를 하지 않고 기다린다 - PinBuffer)
 refcount 18비트 = 최대 262143. MAX_BACKENDS_BITS 가 18 이하여야 한다 (L91-L92 StaticAssert)
```

backend 하나가 같은 버퍼를 여러 번 pin 해도 공유 refcount 는 1 만 오른다. 나머지 횟수는 backend 지역의 `PrivateRefCount` 가 센다(buf_init.c L53-L57). 그 동작은 [PinBuffer](../../flows/buffer-manager/06_PinBuffer/README.md)에 있다.

## 버퍼 매핑 분할 잠금

tag 에서 버퍼 번호를 찾는 해시 테이블은 공유 메모리의 동적 해시 하나지만, 128개 분할로 나뉘어 분할마다 다른 LWLock 으로 지킨다. 해시 값을 한 번 계산해 분할 번호와 버킷 위치에 함께 쓴다.

`storage` / `buffer` / `buf_table.c` L26-L81 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/buf_table.c#L26-L81))

```c
// storage/buffer/buf_table.c L26-L81
/* entry for buffer lookup hashtable */
typedef struct
{
	BufferTag	key;			/* Tag of a disk page */
	int			id;				/* Associated buffer ID */
} BufferLookupEnt;

static HTAB *SharedBufHash;


/*
 * Estimate space needed for mapping hashtable
 *		size is the desired hash table size (possibly more than NBuffers)
 */
Size
BufTableShmemSize(int size)
{
	return hash_estimate_size(size, sizeof(BufferLookupEnt));
}

/*
 * Initialize shmem hash table for mapping buffers
 *		size is the desired hash table size (possibly more than NBuffers)
 */
void
InitBufTable(int size)
{
	HASHCTL		info;

	/* assume no locking is needed yet */

	/* BufferTag maps to Buffer */
	info.keysize = sizeof(BufferTag);
	info.entrysize = sizeof(BufferLookupEnt);
	info.num_partitions = NUM_BUFFER_PARTITIONS;

	SharedBufHash = ShmemInitHash("Shared Buffer Lookup Table",
								  size, size,
								  &info,
								  HASH_ELEM | HASH_BLOBS | HASH_PARTITION);
}

/*
 * BufTableHashCode
 *		Compute the hash code associated with a BufferTag
 *
 * This must be passed to the lookup/insert/delete routines along with the
 * tag.  We do it like this because the callers need to know the hash code
 * in order to determine which buffer partition to lock, and we don't want
 * to do the hash computation twice (hash_any is a bit slow).
 */
uint32
BufTableHashCode(BufferTag *tagPtr)
{
	return get_hash_value(SharedBufHash, tagPtr);
}
```

`src` / `include` / `storage` / `lwlock.h` L86-L110 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/lwlock.h#L86-L110))

```c
// src/include/storage/lwlock.h L86-L110
/*
 * It's a bit odd to declare NUM_BUFFER_PARTITIONS and NUM_LOCK_PARTITIONS
 * here, but we need them to figure out offsets within MainLWLockArray, and
 * having this file include lock.h or bufmgr.h would be backwards.
 */

/* Number of partitions of the shared buffer mapping hashtable */
#define NUM_BUFFER_PARTITIONS  128

/* Number of partitions the shared lock tables are divided into */
#define LOG2_NUM_LOCK_PARTITIONS  4
#define NUM_LOCK_PARTITIONS  (1 << LOG2_NUM_LOCK_PARTITIONS)

/* Number of partitions the shared predicate lock tables are divided into */
#define LOG2_NUM_PREDICATELOCK_PARTITIONS  4
#define NUM_PREDICATELOCK_PARTITIONS  (1 << LOG2_NUM_PREDICATELOCK_PARTITIONS)

/* Offsets for various chunks of preallocated lwlocks. */
#define BUFFER_MAPPING_LWLOCK_OFFSET	NUM_INDIVIDUAL_LWLOCKS
#define LOCK_MANAGER_LWLOCK_OFFSET		\
	(BUFFER_MAPPING_LWLOCK_OFFSET + NUM_BUFFER_PARTITIONS)
#define PREDICATELOCK_MANAGER_LWLOCK_OFFSET \
	(LOCK_MANAGER_LWLOCK_OFFSET + NUM_LOCK_PARTITIONS)
#define NUM_FIXED_LWLOCKS \
	(PREDICATELOCK_MANAGER_LWLOCK_OFFSET + NUM_PREDICATELOCK_PARTITIONS)
```

`src` / `include` / `storage` / `buf_internals.h` L186-L209 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/buf_internals.h#L186-L209))

```c
// src/include/storage/buf_internals.h L186-L209
/*
 * The shared buffer mapping table is partitioned to reduce contention.
 * To determine which partition lock a given tag requires, compute the tag's
 * hash code with BufTableHashCode(), then apply BufMappingPartitionLock().
 * NB: NUM_BUFFER_PARTITIONS must be a power of 2!
 */
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

static inline LWLock *
BufMappingPartitionLockByIndex(uint32 index)
{
	return &MainLWLockArray[BUFFER_MAPPING_LWLOCK_OFFSET + index].lock;
}
```

```text
 MainLWLockArray 안의 자리 (lwlock.h L104-L110)

 [0 .. NUM_INDIVIDUAL_LWLOCKS)                 개별 잠금 (ProcArrayLock, WALWriteLock ...)
 [BUFFER_MAPPING_LWLOCK_OFFSET, +128)          버퍼 매핑 분할 128
 [LOCK_MANAGER_LWLOCK_OFFSET, +16)             heavyweight lock 테이블 분할 16
 [PREDICATELOCK_MANAGER_LWLOCK_OFFSET, +16)    predicate lock 분할 16

 tag -> 잠금
   hashcode  = BufTableHashCode(&tag)          get_hash_value (buf_table.c L80)
   partition = hashcode % 128                  BufTableHashPartition (L195)
   lock      = MainLWLockArray[BUFFER_MAPPING_LWLOCK_OFFSET + partition]

   LW_SHARED     BufTableLookup(&tag, hashcode)   조회              (buf_table.c L87)
   LW_EXCLUSIVE  BufTableInsert                   희생 버퍼에 새 tag  (L115)
   LW_EXCLUSIVE  BufTableDelete                   희생 버퍼의 옛 tag  (L145)

 한 분할 잠금은 그 분할에 떨어지는 모든 tag 를 한꺼번에 막는다
 서로 다른 분할의 조회와 교체는 동시에 진행된다
```

잠금 순서(분할 잠금 -> 헤더 잠금, 옛 tag 와 새 tag 의 분할이 다를 때)는 [BufferAlloc](../../flows/buffer-manager/05_BufferAlloc/README.md)과 [GetVictimBuffer](../../flows/buffer-manager/07_GetVictimBuffer/README.md)에 있다.

## SnapshotData

스냅샷 하나는 모든 종류에 같은 구조체를 쓰고, `snapshot_type` 이 판정 규칙을 고른다. MVCC 스냅샷에서 의미 있는 필드는 `xmin`, `xmax`, `xip`/`xcnt`, `subxip`/`subxcnt`/`suboverflowed`, `curcid` 다. 나머지는 특수 스냅샷의 출력 칸이거나 스냅샷 관리자의 장부다.

`src` / `include` / `utils` / `snapshot.h` L117-L210 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/utils/snapshot.h#L117-L210))

```c
// src/include/utils/snapshot.h L117-L210
typedef struct SnapshotData *Snapshot;

#define InvalidSnapshot		((Snapshot) NULL)

/*
 * Struct representing all kind of possible snapshots.
 *
 * There are several different kinds of snapshots:
 * * Normal MVCC snapshots
 * * MVCC snapshots taken during recovery (in Hot-Standby mode)
 * * Historic MVCC snapshots used during logical decoding
 * * snapshots passed to HeapTupleSatisfiesDirty()
 * * snapshots passed to HeapTupleSatisfiesNonVacuumable()
 * * snapshots used for SatisfiesAny, Toast, Self where no members are
 *	 accessed.
 *
 * TODO: It's probably a good idea to split this struct using a NodeTag
 * similar to how parser and executor nodes are handled, with one type for
 * each different kind of snapshot to avoid overloading the meaning of
 * individual fields.
 */
typedef struct SnapshotData
{
	SnapshotType snapshot_type; /* type of snapshot */

	/*
	 * The remaining fields are used only for MVCC snapshots, and are normally
	 * just zeroes in special snapshots.  (But xmin and xmax are used
	 * specially by HeapTupleSatisfiesDirty, and xmin is used specially by
	 * HeapTupleSatisfiesNonVacuumable.)
	 *
	 * An MVCC snapshot can never see the effects of XIDs >= xmax. It can see
	 * the effects of all older XIDs except those listed in the snapshot. xmin
	 * is stored as an optimization to avoid needing to search the XID arrays
	 * for most tuples.
	 */
	TransactionId xmin;			/* all XID < xmin are visible to me */
	TransactionId xmax;			/* all XID >= xmax are invisible to me */

	/*
	 * For normal MVCC snapshot this contains the all xact IDs that are in
	 * progress, unless the snapshot was taken during recovery in which case
	 * it's empty. For historic MVCC snapshots, the meaning is inverted, i.e.
	 * it contains *committed* transactions between xmin and xmax.
	 *
	 * note: all ids in xip[] satisfy xmin <= xip[i] < xmax
	 */
	TransactionId *xip;
	uint32		xcnt;			/* # of xact ids in xip[] */

	/*
	 * For non-historic MVCC snapshots, this contains subxact IDs that are in
	 * progress (and other transactions that are in progress if taken during
	 * recovery). For historic snapshot it contains *all* xids assigned to the
	 * replayed transaction, including the toplevel xid.
	 *
	 * note: all ids in subxip[] are >= xmin, but we don't bother filtering
	 * out any that are >= xmax
	 */
	TransactionId *subxip;
	int32		subxcnt;		/* # of xact ids in subxip[] */
	bool		suboverflowed;	/* has the subxip array overflowed? */

	bool		takenDuringRecovery;	/* recovery-shaped snapshot? */
	bool		copied;			/* false if it's a static snapshot */

	CommandId	curcid;			/* in my xact, CID < curcid are visible */

	/*
	 * An extra return value for HeapTupleSatisfiesDirty, not used in MVCC
	 * snapshots.
	 */
	uint32		speculativeToken;

	/*
	 * For SNAPSHOT_NON_VACUUMABLE (and hopefully more in the future) this is
	 * used to determine whether row could be vacuumed.
	 */
	struct GlobalVisState *vistest;

	/*
	 * Book-keeping information, used by the snapshot manager
	 */
	uint32		active_count;	/* refcount on ActiveSnapshot stack */
	uint32		regd_count;		/* refcount on RegisteredSnapshots */
	pairingheap_node ph_node;	/* link in the RegisteredSnapshots heap */

	/*
	 * The transaction completion count at the time GetSnapshotData() built
	 * this snapshot. Allows to avoid re-computing static snapshots when no
	 * transactions completed since the last GetSnapshotData().
	 */
	uint64		snapXactCompletionCount;
} SnapshotData;
```

```text
 SnapshotData  (104바이트)

 offset  size  field                    MVCC 스냅샷에서의 뜻
 ------  ----  -----------------------  --------------------------------------------------
      0     4  snapshot_type            SNAPSHOT_MVCC = 0
      4     4  xmin                     이보다 작은 xid 는 모두 끝났다 (보일지는 커밋 여부로)
      8     4  xmax                     이 이상인 xid 는 모두 안 보인다 = latestCompletedXid + 1
     16     8  xip                      진행 중 최상위 xid 배열. xmin <= xip[i] < xmax
     24     4  xcnt
     32     8  subxip                   진행 중 하위 트랜잭션 xid 배열
     40     4  subxcnt
     44     1  suboverflowed            어떤 backend 의 하위 xid 캐시(64)가 넘쳤다 -> pg_subtrans 확인
     45     1  takenDuringRecovery      standby 에서 찍었다. xip 대신 subxip 에 전부 넣는다
     46     1  copied                   false = 정적 스냅샷 (CurrentSnapshotData 등)
     48     4  curcid                   내 트랜잭션에서 이보다 작은 command id 의 변경만 보인다
     52     4  speculativeToken         SNAPSHOT_DIRTY 의 출력
     56     8  vistest                  SNAPSHOT_NON_VACUUMABLE 의 기준
     64     4  active_count             ActiveSnapshot 스택에 몇 번 올라 있나
     68     4  regd_count               RegisteredSnapshots 에 몇 번 등록됐나
     72    24  ph_node                  pairing heap 노드 (포인터 셋)
     96     8  snapXactCompletionCount  이 값이 그대로면 GetSnapshotData 가 재계산을 건너뛴다
    104
```

`xip` 과 `subxip` 은 구조체 밖의 배열이다. 정적 스냅샷은 처음 쓸 때 최대 크기로 한 번 `malloc` 하고 계속 재사용한다. 최대 크기는 프로세스 슬롯 수(`procArray->maxProcs`)와 `(64 + 1) * 슬롯 수`다(procarray.c L2069-L2083, L399-L400).

`storage` / `ipc` / `procarray.c` L2206-L2225 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L2206-L2225))

```c
// storage/ipc/procarray.c L2206-L2225
	if (snapshot->xip == NULL)
	{
		/*
		 * First call for this snapshot. Snapshot is same size whether or not
		 * we are in recovery, see later comments.
		 */
		snapshot->xip = (TransactionId *)
			malloc(GetMaxSnapshotXidCount() * sizeof(TransactionId));
		if (snapshot->xip == NULL)
			ereport(ERROR,
					(errcode(ERRCODE_OUT_OF_MEMORY),
					 errmsg("out of memory")));
		Assert(snapshot->subxip == NULL);
		snapshot->subxip = (TransactionId *)
			malloc(GetMaxSnapshotSubxidCount() * sizeof(TransactionId));
		if (snapshot->subxip == NULL)
			ereport(ERROR,
					(errcode(ERRCODE_OUT_OF_MEMORY),
					 errmsg("out of memory")));
	}
```

`xmax` 와 `xmin` 은 이렇게 정해진다. `xmax` 는 마지막으로 끝난 xid 다음이고, `xmin` 은 나를 포함한 진행 중 xid 의 최솟값이다. 내 xid 는 `xmin` 계산에는 들어가지만 `xip` 에는 넣지 않는다(L2288-L2294).

`storage` / `ipc` / `procarray.c` L2247-L2257 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L2247-L2257))

```c
// storage/ipc/procarray.c L2247-L2257
	/* xmax is always latestCompletedXid + 1 */
	xmax = XidFromFullTransactionId(latest_completed);
	TransactionIdAdvance(xmax);
	Assert(TransactionIdIsNormal(xmax));

	/* initialize xmin calculation with xmax */
	xmin = xmax;

	/* take own xid into account, saves a check inside the loop */
	if (TransactionIdIsNormal(myxid) && NormalTransactionIdPrecedes(myxid, xmin))
		xmin = myxid;
```

```text
 스냅샷 하나를 손으로 만들어 보기

 상황   backend A xid 100 진행 중,  backend B xid 103 진행 중,  나는 xid 없음
        latestCompletedXid = 104   (101, 102, 104 는 끝났다)

 xmax = 104 + 1                     = 105        (L2248-L2249)
 xmin = min(105, 100, 103)          = 100        (L2253, L2320-L2321)
 xip  = {100, 103},  xcnt = 2

 xid 축        ... 99 | 100  101  102  103  104 | 105  106 ...
                      ^xmin                      ^xmax
 판정 (그 xid 가 커밋됐다고 할 때)
   xid < 100          visible     xip 를 볼 필요 없음
   100, 103           invisible   xip 에 있다 = 스냅샷 당시 진행 중
   101, 102, 104      visible     범위 안이지만 xip 에 없다
   xid >= 105         invisible   스냅샷 뒤에 시작
 범위 안의 판정은 XidInMVCCSnapshot 이 한다
```

xid 비교 규칙의 실제 코드는 [XidInMVCCSnapshot](../../flows/mvcc-visibility/09_XidInMVCCSnapshot/README.md), 이 값들을 실제로 모으는 루프는 [GetSnapshotData](../../flows/mvcc-visibility/02_GetSnapshotData/README.md)에 있다.

## 스냅샷의 종류

`snapshot_type` 은 일곱 가지다. 이름이 가리키는 의미는 enum 주석에 적혀 있고, 판정 함수와의 짝은 [HeapTupleSatisfiesVisibility](../../flows/mvcc-visibility/07_HeapTupleSatisfiesVisibility/README.md)의 switch 에 있다.

`src` / `include` / `utils` / `snapshot.h` L19-L115 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/utils/snapshot.h#L19-L115))

```c
// src/include/utils/snapshot.h L19-L115
/*
 * The different snapshot types.  We use SnapshotData structures to represent
 * both "regular" (MVCC) snapshots and "special" snapshots that have non-MVCC
 * semantics.  The specific semantics of a snapshot are encoded by its type.
 *
 * The behaviour of each type of snapshot should be documented alongside its
 * enum value, best in terms that are not specific to an individual table AM.
 *
 * The reason the snapshot type rather than a callback as it used to be is
 * that that allows to use the same snapshot for different table AMs without
 * having one callback per AM.
 */
typedef enum SnapshotType
{
	/*-------------------------------------------------------------------------
	 * A tuple is visible iff the tuple is valid for the given MVCC snapshot.
	 *
	 * Here, we consider the effects of:
	 * - all transactions committed as of the time of the given snapshot
	 * - previous commands of this transaction
	 *
	 * Does _not_ include:
	 * - transactions shown as in-progress by the snapshot
	 * - transactions started after the snapshot was taken
	 * - changes made by the current command
	 * -------------------------------------------------------------------------
	 */
	SNAPSHOT_MVCC = 0,

	/*-------------------------------------------------------------------------
	 * A tuple is visible iff the tuple is valid "for itself".
	 *
	 * Here, we consider the effects of:
	 * - all committed transactions (as of the current instant)
	 * - previous commands of this transaction
	 * - changes made by the current command
	 *
	 * Does _not_ include:
	 * - in-progress transactions (as of the current instant)
	 * -------------------------------------------------------------------------
	 */
	SNAPSHOT_SELF,

	/*
	 * Any tuple is visible.
	 */
	SNAPSHOT_ANY,

	/*
	 * A tuple is visible iff the tuple is valid as a TOAST row.
	 */
	SNAPSHOT_TOAST,

	// ... (L72-L97 생략: SNAPSHOT_DIRTY 가 xmin, xmax, speculativeToken 을 출력 칸으로 쓰는 방식의 긴 설명)
	SNAPSHOT_DIRTY,

	/*
	 * A tuple is visible iff it follows the rules of SNAPSHOT_MVCC, but
	 * supports being called in timetravel context (for decoding catalog
	 * contents in the context of logical decoding).
	 */
	SNAPSHOT_HISTORIC_MVCC,

	/*
	 * A tuple is visible iff the tuple might be visible to some transaction;
	 * false if it's surely dead to everyone, i.e., vacuumable.
	 *
	 * For visibility checks snapshot->min must have been set up with the xmin
	 * horizon to use.
	 */
	SNAPSHOT_NON_VACUUMABLE,
} SnapshotType;
```

종류마다 스냅샷 구조체가 놓이는 자리가 다르다. MVCC 스냅샷은 snapmgr.c 의 정적 변수 셋을 채워 돌려주고, 오래 쓸 것은 복사해 스택이나 힙에 올린다. 특수 스냅샷 중 내용이 없는 것은 전역 상수 하나를 모두가 함께 쓰고, 출력 칸이 있는 것(`DIRTY`, `NON_VACUUMABLE`)은 호출자가 지역 변수로 만든다.

`utils` / `time` / `snapmgr.c` L128-L151 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/time/snapmgr.c#L128-L151))

```c
// utils/time/snapmgr.c L128-L151
/*
 * CurrentSnapshot points to the only snapshot taken in transaction-snapshot
 * mode, and to the latest one taken in a read-committed transaction.
 * SecondarySnapshot is a snapshot that's always up-to-date as of the current
 * instant, even in transaction-snapshot mode.  It should only be used for
 * special-purpose code (say, RI checking.)  CatalogSnapshot points to an
 * MVCC snapshot intended to be used for catalog scans; we must invalidate it
 * whenever a system catalog change occurs.
 *
 * These SnapshotData structs are static to simplify memory allocation
 * (see the hack in GetSnapshotData to avoid repeated malloc/free).
 */
static SnapshotData CurrentSnapshotData = {SNAPSHOT_MVCC};
static SnapshotData SecondarySnapshotData = {SNAPSHOT_MVCC};
static SnapshotData CatalogSnapshotData = {SNAPSHOT_MVCC};
SnapshotData SnapshotSelfData = {SNAPSHOT_SELF};
SnapshotData SnapshotAnyData = {SNAPSHOT_ANY};
SnapshotData SnapshotToastData = {SNAPSHOT_TOAST};

/* Pointers to valid snapshots */
static Snapshot CurrentSnapshot = NULL;
static Snapshot SecondarySnapshot = NULL;
static Snapshot CatalogSnapshot = NULL;
static Snapshot HistoricSnapshot = NULL;
```

`src` / `include` / `utils` / `snapmgr.h` L27-L57 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/utils/snapmgr.h#L27-L57))

```c
// src/include/utils/snapmgr.h L27-L57
/* Variables representing various special snapshot semantics */
extern PGDLLIMPORT SnapshotData SnapshotSelfData;
extern PGDLLIMPORT SnapshotData SnapshotAnyData;
extern PGDLLIMPORT SnapshotData SnapshotToastData;

#define SnapshotSelf		(&SnapshotSelfData)
#define SnapshotAny			(&SnapshotAnyData)

/* Use get_toast_snapshot() for the TOAST snapshot */

/*
 * We don't provide a static SnapshotDirty variable because it would be
 * non-reentrant.  Instead, users of that snapshot type should declare a
 * local variable of type SnapshotData, and initialize it with this macro.
 */
#define InitDirtySnapshot(snapshotdata)  \
	((snapshotdata).snapshot_type = SNAPSHOT_DIRTY)

/*
 * Similarly, some initialization is required for a NonVacuumable snapshot.
 * The caller must supply the visibility cutoff state to use (c.f.
 * GlobalVisTestFor()).
 */
#define InitNonVacuumableSnapshot(snapshotdata, vistestp)  \
	((snapshotdata).snapshot_type = SNAPSHOT_NON_VACUUMABLE, \
	 (snapshotdata).vistest = (vistestp))

/* This macro encodes the knowledge of which snapshots are MVCC-safe */
#define IsMVCCSnapshot(snapshot)  \
	((snapshot)->snapshot_type == SNAPSHOT_MVCC || \
	 (snapshot)->snapshot_type == SNAPSHOT_HISTORIC_MVCC)
```

```text
 snapshot_type              struct                       made by / used at        뜻
 -------------------------  ---------------------------  -----------------------  ------------------------------
 SNAPSHOT_MVCC           0  CurrentSnapshotData static   GetTransactionSnapshot   문장 / 트랜잭션 스냅샷
                            SecondarySnapshotData static GetLatestSnapshot        지금 순간 (RI 검사 등)
                            CatalogSnapshotData static   GetCatalogSnapshot       카탈로그 스캔
                            copy (TopTransactionContext) PushActiveSnapshot,      오래 쓸 복사본
                                                         RegisterSnapshot
 SNAPSHOT_SELF           1  SnapshotSelfData global      nbtinsert.c L619         고유성 검사 중 확인
 SNAPSHOT_ANY            2  SnapshotAnyData global       nbtsort.c L1437          인덱스 생성. 가시성은 직접 판정
 SNAPSHOT_TOAST          3  SnapshotToastData global     get_toast_snapshot       TOAST 값 읽기
                                                         (toast_internals.c L638)
 SNAPSHOT_DIRTY          4  local + InitDirtySnapshot    nbtinsert.c L430         _bt_check_unique 의 진행 중 중복
 SNAPSHOT_HISTORIC_MVCC  5  HistoricSnapshot             logical decoding         xip 의 뜻이 "커밋된 것"으로 뒤집힌다
 SNAPSHOT_NON_VACUUMABLE 6  local + InitNonVacuumable    heapam.c L8404,          아직 누군가에게 보일 수 있나
                            Snapshot(vistest)            selfuncs.c L6860

 IsMVCCSnapshot = MVCC 또는 HISTORIC_MVCC (snapmgr.h L55-L57)
 특수 스냅샷은 등록하거나 ActiveSnapshot 스택에 올릴 수 없다 (snapmgr.c L25-L28)
```

정적 스냅샷은 다음 스냅샷 관련 호출에 덮어써질 수 있다. 그래서 계속 쓸 스냅샷은 `PushActiveSnapshot`(활성 스택) 이나 `RegisterSnapshot`(resource owner 에 등록) 으로 복사본을 만들어 쓴다(snapmgr.c L14-L23). 복사본은 구조체 바로 뒤에 `xip` 과 `subxip` 을 붙인 한 덩어리다.

`utils` / `time` / `snapmgr.c` L605-L655 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/time/snapmgr.c#L605-L655))

```c
// utils/time/snapmgr.c L605-L655
static Snapshot
CopySnapshot(Snapshot snapshot)
{
	Snapshot	newsnap;
	Size		subxipoff;
	Size		size;

	Assert(snapshot != InvalidSnapshot);

	/* We allocate any XID arrays needed in the same palloc block. */
	size = subxipoff = sizeof(SnapshotData) +
		snapshot->xcnt * sizeof(TransactionId);
	if (snapshot->subxcnt > 0)
		size += snapshot->subxcnt * sizeof(TransactionId);

	newsnap = (Snapshot) MemoryContextAlloc(TopTransactionContext, size);
	memcpy(newsnap, snapshot, sizeof(SnapshotData));

	newsnap->regd_count = 0;
	newsnap->active_count = 0;
	newsnap->copied = true;
	newsnap->snapXactCompletionCount = 0;

	/* setup XID array */
	if (snapshot->xcnt > 0)
	{
		newsnap->xip = (TransactionId *) (newsnap + 1);
		memcpy(newsnap->xip, snapshot->xip,
			   snapshot->xcnt * sizeof(TransactionId));
	}
	else
		newsnap->xip = NULL;

	/*
	 * Setup subXID array. Don't bother to copy it if it had overflowed,
	 * though, because it's not used anywhere in that case. Except if it's a
	 * snapshot taken during recovery; all the top-level XIDs are in subxip as
	 * well in that case, so we mustn't lose them.
	 */
	if (snapshot->subxcnt > 0 &&
		(!snapshot->suboverflowed || snapshot->takenDuringRecovery))
	{
		newsnap->subxip = (TransactionId *) ((char *) newsnap + subxipoff);
		memcpy(newsnap->subxip, snapshot->subxip,
			   snapshot->subxcnt * sizeof(TransactionId));
	}
	else
		newsnap->subxip = NULL;

	return newsnap;
}
```

```text
 위 예의 스냅샷 (xcnt 2, subxcnt 0) 을 PushActiveSnapshot 하면

 TopTransactionContext
 +-----------------------------------+------------+
 | SnapshotData 104                  | xip 8      |   size = 104 + 2 * 4 = 112   (L615-L618)
 | xip = (newsnap + 1) ------------->| 100 | 103  |   L631
 | subxip = NULL                     |            |   subxcnt 0                   L651-L652
 | copied = true, active_count 1     |            |
 +-----------------------------------+------------+
        |
        v
 ActiveSnapshot -> {as_snap, as_level, as_next}  (snapmgr.c L172-L180)

 RegisterSnapshot 이면 regd_count 1 이 되고 RegisteredSnapshots 힙에 xmin 순으로 들어간다 (L182-L189)
 등록된 스냅샷이 모두 없어지면 MyProc->xmin 을 비우고, 가장 오래된 것이 풀리면 앞으로 민다 (L89-L94)
 PushActiveSnapshot 은 정적이거나 복사본이 아닌 스냅샷만 복사한다 (L707-L711), RegisterSnapshot 도 같다 (L843)
```

`utils` / `time` / `snapmgr.c` L164-L189 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/time/snapmgr.c#L164-L189))

```c
// utils/time/snapmgr.c L164-L189
/*
 * Elements of the active snapshot stack.
 *
 * Each element here accounts for exactly one active_count on SnapshotData.
 *
 * NB: the code assumes that elements in this list are in non-increasing
 * order of as_level; also, the list must be NULL-terminated.
 */
typedef struct ActiveSnapshotElt
{
	Snapshot	as_snap;
	int			as_level;
	struct ActiveSnapshotElt *as_next;
} ActiveSnapshotElt;

/* Top of the stack of active snapshots */
static ActiveSnapshotElt *ActiveSnapshot = NULL;

/*
 * Currently registered Snapshots.  Ordered in a heap by xmin, so that we can
 * quickly find the one with lowest xmin, to advance our MyProc->xmin.
 */
static int	xmin_cmp(const pairingheap_node *a, const pairingheap_node *b,
					 void *arg);

static pairingheap RegisteredSnapshots = {&xmin_cmp, NULL, NULL};
```

## db-engine 에서는

db-engine 의 버퍼 풀은 `LinkedHashMap<PageId, Page>` 하나다. 페이지 객체 자체가 `pinCount` 와 `isDirty` 를 들고, 접근 순서가 곧 LRU 순서다. 스냅샷은 `Snapshot(xid, active)` 두 필드다.

```text
 같은 문제(버퍼 헤더와 스냅샷의 모양), 두 구현

 버퍼
   PostgreSQL  BufferDesc[16384] 64바이트 고정 배열 + 페이지 배열 + 해시(128 분할)
               tag 20바이트, state 32비트 = refcount 18 | usage 4 | flags 10
               pin 은 CAS 한 번, 페이지 내용은 content_lock 으로 따로
   db-engine   LinkedHashMap(capacity, 0.75f, accessOrder = true)  키 PageId(fileId, pageNumber)
               Page { id, data[4096], isDirty, pinCount }
               잠금 없음 (단일 스레드 전제), 교체는 iteration 첫 unpinned = LRU

 교체 기준
   PostgreSQL  clock-sweep 이 usage_count 를 1 씩 깎다가 0 이고 refcount 0 인 버퍼
   db-engine   가장 오래 안 쓴 것 중 pinCount == 0

 스냅샷
   PostgreSQL  xmin, xmax, xip[], subxip[], curcid   (104바이트 + 배열)
               xid < xmin 이면 xip 를 보지 않고 결정
   db-engine   Snapshot(xid, active: Set<Long>)
               isVisible: xidStart > xid 이거나 xidStart in active 면 안 보임
               xmin 이 없어 매번 Set 조회, 명령 번호(curcid) 가 없어 같은 트랜잭션 안 구분 없음
```

db-engine 의 `Snapshot.xid` 는 자기 xid 이자 사실상 `xmax` 역할(이보다 큰 xid 는 안 보임)을 겸하고, `active` 가 `xip` 에 해당한다. PostgreSQL 은 xid 를 쓰기 시작할 때만 배정하므로 읽기만 하는 트랜잭션의 스냅샷은 자기 xid 없이 `xmax` 로 경계를 정한다. 챕터: [02-02-buffer-pool](../../../../../project/db-engine/02-02-buffer-pool/), [10-01-mvcc](../../../../../project/db-engine/10-01-mvcc/).

## 어디에서 쓰이는가

```text
 [버퍼 관리]          BufferAlloc 이 tag 로 분할 잠금 -> BufTableLookup -> PinBuffer (state CAS)
                      GetVictimBuffer 가 state 의 refcount, usage_count 를 보며 희생자를 고른다
                      FlushBuffer 가 BM_DIRTY 를 보고 쓰고, BM_JUST_DIRTIED 로 쓰는 중 재오염을 잡는다
 [체크포인트]         BufferSync 가 BM_DIRTY 버퍼에 BM_CHECKPOINT_NEEDED 를 켜고
                      CkptBufferIds 에 tag 를 복사해 파일 순으로 정렬한다
 [MVCC 가시성]        GetSnapshotData 가 CurrentSnapshotData 를 채우고
                      HeapTupleSatisfiesMVCC 가 xmin, xmax, xip, curcid 로 튜플마다 판정한다
 [nbtree 삽입과 분할] _bt_check_unique 가 SNAPSHOT_DIRTY 로 진행 중인 중복을 찾는다
 [vacuum]             backend 마다의 MyProc->xmin 을 ComputeXidHorizons 가 모아 (procarray.c L1802)
                      죽은 튜플을 지워도 되는 경계를 정한다
```

흐름 문서: [버퍼 관리](../../flows/buffer-manager/README.md), [체크포인트](../../flows/checkpoint/README.md), [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md), [nbtree 삽입과 분할](../../flows/nbtree-insert/README.md), [vacuum](../../flows/vacuum/README.md). 공유 메모리 안에서 이 배열들이 자리 잡는 순서는 [공유 메모리](../shared-memory/README.md)에, 페이지 8192바이트의 내부는 [페이지와 튜플 레이아웃](../page-tuple-layout/README.md)에 있다.

## 다루지 않는 것

backend 지역 버퍼(`localbuf.c`)의 할당과 교체, `PrivateRefCount` 배열과 해시의 구조, 버퍼 접근 전략(ring buffer, `BufferAccessStrategyData`), AIO 핸들(`PgAioHandle`)의 내부, LWLock 의 `state` 비트 배치, 스냅샷 내보내기와 가져오기(`pg_export_snapshot`, `pg_snapshots/`), 논리 디코딩의 historic 스냅샷을 만드는 `snapbuild.c`, `GlobalVisState` 의 경계 계산은 곁가지라 다루지 않았다.
