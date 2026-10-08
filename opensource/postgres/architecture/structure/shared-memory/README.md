# 공유 메모리

상위: [PostgreSQL 아키텍처 지도](../../README.md)

PostgreSQL 의 프로세스들이 함께 보는 상태는 **기동 때 한 번 만든 세그먼트 하나**에 다 들어 있다. 버퍼 풀, WAL 버퍼, 잠금 해시, `PGPROC` 배열, `ProcArray`, CLOG 버퍼가 모두 그 안에 있다. 만드는 순서는 세 단계다. 먼저 postmaster 가 모듈마다 `*ShmemSize()` 를 더해 전체 크기를 정한다(`CalculateShmemSize`). 다음에 그 크기로 세그먼트를 한 번에 잡는다. 마지막으로 모듈마다 `*ShmemInit()` 이 `ShmemInitStruct(이름, 크기)` 를 불러 자리를 받는다. 자리는 세그먼트 앞에서부터 cache line 단위로 잘라 주고 **돌려받지 않는다.** 이름과 위치의 대응은 `ShmemIndex` 해시가 기억한다. 자식 프로세스는 `fork` 로 같은 주소의 매핑을 물려받으므로 포인터를 다시 계산하지 않는다. 이 편은 그 세그먼트의 **배치와 크기**를 기본 설정으로 계산해 보이고, 그중 프로세스마다 하나씩 있는 `PGPROC` 의 모양을 본다. 누가 이 세그먼트를 만들고 붙는지는 [프로세스 모델](../process-model/README.md)에 있다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다. 크기 계산은 기본 GUC(`shared_buffers` 128MB = 16384 페이지, `max_connections` 100, `max_locks_per_transaction` 64 등)와 8KB 블록을 쓴다. `sizeof` 값은 이 태그의 헤더를 x86-64 리눅스 gcc 로 컴파일해 찍은 값이다(빌드 옵션은 configure 기본).

## 전체 그림

```text
 세그먼트 안의 배치 (낮은 주소 -> 높은 주소, CreateOrAttachShmemStructs 의 호출 순서)

 +-------------------------------------------------------------+ 0
 | PGShmemHeader  (magic, totalsize, freeoffset, index ...)     |
 | ShmemLock (spinlock)                                         |
 +-------------------------------------------------------------+ 이후 모든 조각은 128 바이트 정렬
 | MainLWLockArray        CreateLWLocks                         |
 | ShmemIndex             이름 -> (location, size) 해시, 64 항목 |
 | dsm, DSM registry                                            |
 | TransamVariables       VarsupShmemInit (nextXid 등)          |
 | XLOG Ctl               XLogCtlData + WAL insert lock 9개     |
 |                        + WAL 버퍼 512 x 8KB = 4MB            |
 | Control File           pg_control 의 메모리 사본             |
 | XLogPrefetch, XLogRecovery                                   |
 | "transaction"  (CLOG)  32 페이지 x 8KB + 제어 = 529,568 B    |
 | commit_timestamp, subtransaction, multixact 의 SLRU          |
 | Buffer Descriptors     16384 x 64 B   = 1MB                  |
 | Buffer Blocks          16384 x 8KB    = 128MB  (4096 정렬)   |
 | Buffer IO CV           16384 x 16 B   = 256KB                |
 | Checkpoint BufferIds   16384 x 20 B   = 320KB                |
 | Shared Buffer Lookup Table (해시, 128 파티션)                |
 | Buffer Strategy Status (clock hand, bgwprocno)               |
 | LOCK hash, PROCLOCK hash  (헤더와 처음 절반만 여기서)        |
 | Fast Path Strong Relation Lock Data                          |
 | predicate lock 구조들                                        |
 | Proc Header (PROC_HDR)                                       |
 | PGPROC structures      174 x 832 B + 조밀 배열 3개           |
 | Fast-Path Lock Array   174 x 288 B                           |
 | Proc Array             pgprocnos[136]                        |
 | KnownAssignedXids, KnownAssignedXidsValid (hot_standby)      |
 | backend status, two-phase, bgworker, sinval, PMSignal,       |
 | ProcSignal, checkpointer, autovacuum, 복제 슬롯, walsender, |
 | walreceiver, ... , AIO                                       |
 +-------------------------------------------------------------+ freeoffset
 | 남은 자리: 해시 표가 자라며 여기서 원소를 더 받는다          |
 |           (ShmemInitHash 의 alloc = ShmemAllocNoError)       |
 +-------------------------------------------------------------+ totalsize
```

```text
 큰 덩어리의 크기 (기본 설정, 바이트)

       bytes  computed as                                            영역
 136,786,512  BufferManagerShmemSize                                 버퍼 풀 전체
 134,221,824    16384 * 8192 + 4096 (PG_IO_ALIGN_SIZE)               Buffer Blocks
   1,048,704    16384 * 64 + 128                                     Buffer Descriptors
     926,000    hash_estimate_size(16384 + 128, 24)                  Shared Buffer Lookup Table
     262,272    16384 * 16 + 128                                     Buffer IO 조건 변수
     327,680    16384 * 20                                           Checkpoint BufferIds
          32    MAXALIGN(28)                                         Buffer Strategy Status
   3,588,217  LockManagerShmemSize                                   잠금 해시 전체
   1,601,616    hash_estimate_size(8704, 152)                        LOCK
   1,660,400    hash_estimate_size(17408, 64)                        PROCLOCK
     326,201    (1,601,616 + 1,660,400) / 10                         여유 10%
   4,194,304  512 * 8192                                             WAL 버퍼
      13,440    512 * 8 + 8192 + 9 * 128                             xlblocks, 정렬 여유, insert lock
                                                                     (XLogCtlData 자체는 세지 않았다)
     529,568  SimpleLruShmemSize(32, 1024)                           CLOG
     196,227  ProcGlobalShmemSize                                    PGPROC 과 ProcGlobal
      44,780  ProcArrayShmemSize                                     ProcArray (hot_standby on)

 이 여섯만 더해도 약 138.6 MiB 다. 나머지 모듈과 100,000 바이트 여유를 더한 뒤
 8192 의 배수로 올린 값이 세그먼트 크기이고, MB 로 올린 값을 shared_memory_size 로 보인다
 (이 태그를 기본 설정으로 initdb 한 클러스터에서 postgres -C shared_memory_size = 150)
```

## 크기를 먼저 정한다 - CalculateShmemSize

세그먼트는 나중에 늘릴 수 없다. 그래서 postmaster 는 세그먼트를 만들기 전에 모든 모듈에게 크기를 묻는다. 큰 것만 정확히 세고, 작아서 세기 귀찮은 것들은 100,000 바이트로 퉁친다고 주석이 적었다.

`storage` / `ipc` / `ipci.c` L88-L161 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/ipci.c#L88-L161))

```c
// storage/ipc/ipci.c L88-L161
Size
CalculateShmemSize(int *num_semaphores)
{
	Size		size;
	int			numSemas;

// ... (L94-L99 생략: 세마포어 수(ProcGlobalSemas)를 호출자에게 돌려준다)

	/*
	 * Size of the Postgres shared-memory block is estimated via moderately-
	 * accurate estimates for the big hogs, plus 100K for the stuff that's too
	 * small to bother with estimating.
	 *
	 * We take some care to ensure that the total size request doesn't
	 * overflow size_t.  If this gets through, we don't need to be so careful
	 * during the actual allocation phase.
	 */
	size = 100000;
	size = add_size(size, PGSemaphoreShmemSize(numSemas));
	size = add_size(size, hash_estimate_size(SHMEM_INDEX_SIZE,
											 sizeof(ShmemIndexEnt)));
	size = add_size(size, dsm_estimate_size());
	size = add_size(size, DSMRegistryShmemSize());
	size = add_size(size, BufferManagerShmemSize());
	size = add_size(size, LockManagerShmemSize());
	size = add_size(size, PredicateLockShmemSize());
	size = add_size(size, ProcGlobalShmemSize());
	size = add_size(size, XLogPrefetchShmemSize());
	size = add_size(size, VarsupShmemSize());
	size = add_size(size, XLOGShmemSize());
	size = add_size(size, XLogRecoveryShmemSize());
	size = add_size(size, CLOGShmemSize());
	size = add_size(size, CommitTsShmemSize());
	size = add_size(size, SUBTRANSShmemSize());
	size = add_size(size, TwoPhaseShmemSize());
	size = add_size(size, BackgroundWorkerShmemSize());
	size = add_size(size, MultiXactShmemSize());
	size = add_size(size, LWLockShmemSize());
	size = add_size(size, ProcArrayShmemSize());
	size = add_size(size, BackendStatusShmemSize());
	size = add_size(size, SharedInvalShmemSize());
	size = add_size(size, PMSignalShmemSize());
	size = add_size(size, ProcSignalShmemSize());
	size = add_size(size, CheckpointerShmemSize());
	size = add_size(size, AutoVacuumShmemSize());
	size = add_size(size, ReplicationSlotsShmemSize());
	size = add_size(size, ReplicationOriginShmemSize());
	size = add_size(size, WalSndShmemSize());
	size = add_size(size, WalRcvShmemSize());
	size = add_size(size, WalSummarizerShmemSize());
	size = add_size(size, PgArchShmemSize());
	size = add_size(size, ApplyLauncherShmemSize());
	size = add_size(size, BTreeShmemSize());
	size = add_size(size, SyncScanShmemSize());
	size = add_size(size, AsyncShmemSize());
	size = add_size(size, StatsShmemSize());
	size = add_size(size, WaitEventCustomShmemSize());
	size = add_size(size, InjectionPointShmemSize());
	size = add_size(size, SlotSyncShmemSize());
	size = add_size(size, AioShmemSize());

	/* include additional requested shmem from preload libraries */
	size = add_size(size, total_addin_request);

	/* might as well round it off to a multiple of a typical page size */
	size = add_size(size, 8192 - (size % 8192));

	return size;
}
```

이 함수는 두 번 불린다. 한 번은 `PostmasterMain` 의 `InitializeShmemGUCs`(postmaster.c L969)가 읽기 전용 GUC `shared_memory_size` 와 `num_os_semaphores` 를 채울 때(ipci.c L357), 한 번은 아래에서 실제로 세그먼트를 만들 때다. 그 전에 `InitializeMaxBackends`(L951)가 `MaxBackends` 를, `InitializeFastPathLocks`(L957)가 fast-path 그룹 수를 정해 둔다. 크기 계산이 이 두 값을 쓰기 때문이다.

```text
 크기 계산에 들어가는 파생 값 (기본 설정)

 value                 computed as                                            where
 MaxBackends    136    100 max_connections + 16 autovacuum_worker_slots       utils/init/postinit.c L560-L561
                       + 8 max_worker_processes + 10 max_wal_senders
                       + 2 NUM_SPECIAL_WORKER_PROCS
 TotalProcs     174    136 + 38 NUM_AUXILIARY_PROCS + 0 max_prepared_xacts    storage/lmgr/proc.c L100-L101
 semaphores     174    MaxBackends + NUM_AUXILIARY_PROCS                      proc.c ProcGlobalSemas
 NLOCKENTS      8704   64 max_locks_per_transaction * (136 + 0)               storage/lmgr/lock.c L56-L57
 fast-path      4 x 16 nextpower2(64) / FP_LOCK_SLOTS_PER_GROUP 16 = 4 groups utils/init/postinit.c L594-L596
 wal_buffers    512    NBuffers / 32, clamp 8 .. 16MB / 8KB = 2048            access/transam/xlog.c L4661-L4665
 CLOG slots     32     16384 / 512, round down to x16, clamp 16 .. 1024     access/transam/slru.c L233-L235
```

## 세그먼트를 만들고 자리를 나눈다

`CreateSharedMemoryAndSemaphores` 가 위 크기로 세그먼트를 만들고, 세마포어를 잡고, 할당기를 초기화한 뒤 모듈 초기화를 차례로 부른다. postmaster 가 기동할 때(postmaster.c L1004)와 crash 뒤 재초기화할 때(L3202) 불린다.

`storage` / `ipc` / `ipci.c` L199-L250 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/ipci.c#L199-L250))

```c
// storage/ipc/ipci.c L199-L250
void
CreateSharedMemoryAndSemaphores(void)
{
	PGShmemHeader *shim;
	PGShmemHeader *seghdr;
	Size		size;
	int			numSemas;

	Assert(!IsUnderPostmaster);

	/* Compute the size of the shared-memory block */
	size = CalculateShmemSize(&numSemas);
	elog(DEBUG3, "invoking IpcMemoryCreate(size=%zu)", size);

	/*
	 * Create the shmem segment
	 */
	seghdr = PGSharedMemoryCreate(size, &shim);

	/*
	 * Make sure that huge pages are never reported as "unknown" while the
	 * server is running.
	 */
	Assert(strcmp("unknown",
				  GetConfigOption("huge_pages_status", false, false)) != 0);

	InitShmemAccess(seghdr);

	/*
	 * Create semaphores.  (This is done here for historical reasons.  We used
	 * to support emulating spinlocks with semaphores, which required
	 * initializing semaphores early.)
	 */
	PGReserveSemaphores(numSemas);

	/*
	 * Set up shared memory allocation mechanism
	 */
	InitShmemAllocation();

	/* Initialize subsystems */
	CreateOrAttachShmemStructs();

	/* Initialize dynamic shared memory facilities. */
	dsm_postmaster_startup(shim);

	/*
	 * Now give loadable modules a chance to set up their shmem allocations
	 */
	if (shmem_startup_hook)
		shmem_startup_hook();
}
```

리눅스 기본(`shared_memory_type = mmap`)에서 큰 세그먼트는 익명 `mmap` 이고, System V 공유 메모리는 헤더 크기만큼만 잡는다. System V 조각은 데이터 디렉터리를 지키는 interlock 으로만 쓴다(port/sysv_shmem.c L43-L46 주석, 분기는 L737-L747).

모듈 초기화의 순서가 곧 세그먼트 안의 배치 순서다. LWLock 과 `ShmemIndex` 가 먼저다. 이후의 `ShmemInitStruct` 가 둘 다 쓰기 때문이다.

`storage` / `ipc` / `ipci.c` L267-L348 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/ipci.c#L267-L348))

```c
// storage/ipc/ipci.c L267-L348
static void
CreateOrAttachShmemStructs(void)
{
	/*
	 * Now initialize LWLocks, which do shared memory allocation and are
	 * needed for InitShmemIndex.
	 */
	CreateLWLocks();

	/*
	 * Set up shmem.c index hashtable
	 */
	InitShmemIndex();

	dsm_shmem_init();
	DSMRegistryShmemInit();

	/*
	 * Set up xlog, clog, and buffers
	 */
	VarsupShmemInit();
	XLOGShmemInit();
	XLogPrefetchShmemInit();
	XLogRecoveryShmemInit();
	CLOGShmemInit();
	CommitTsShmemInit();
	SUBTRANSShmemInit();
	MultiXactShmemInit();
	BufferManagerShmemInit();

	/*
	 * Set up lock manager
	 */
	LockManagerShmemInit();

	/*
	 * Set up predicate lock manager
	 */
	PredicateLockShmemInit();

	/*
	 * Set up process table
	 */
	if (!IsUnderPostmaster)
		InitProcGlobal();
	ProcArrayShmemInit();
	BackendStatusShmemInit();
	TwoPhaseShmemInit();
	BackgroundWorkerShmemInit();

// ... (L317-L336 생략: sinval, PMSignal, ProcSignal, checkpointer, autovacuum, 복제 슬롯, walsender, walreceiver 등 프로세스 간 신호 모듈)

	/*
	 * Set up other modules that need some shared memory space
	 */
	BTreeShmemInit();
	SyncScanShmemInit();
	AsyncShmemInit();
	StatsShmemInit();
	WaitEventCustomShmemInit();
	InjectionPointShmemInit();
	AioShmemInit();
}
```

## 자리를 받는 법 - ShmemInitStruct 와 ShmemAllocRaw

모듈은 이름과 크기만 넘긴다. 이름이 `ShmemIndex` 에 이미 있으면 그 위치를 돌려주고 `*foundPtr = true` 로 "이미 초기화됐다"고 알린다. 없으면 새로 잘라 주고 `false` 를 알린다. 이 한 함수가 "처음 만드는 postmaster" 와 "붙기만 하는 자식"을 같은 코드로 다루게 해 준다(shmem.c 머리 주석 L34-L49).

`storage` / `ipc` / `shmem.c` L386-L486 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/shmem.c#L386-L486))

```c
// storage/ipc/shmem.c L386-L486
void *
ShmemInitStruct(const char *name, Size size, bool *foundPtr)
{
	ShmemIndexEnt *result;
	void	   *structPtr;

	LWLockAcquire(ShmemIndexLock, LW_EXCLUSIVE);

// ... (L394-L425 생략: ShmemIndex 자신을 만드는 부트스트랩 경로)

	/* look it up in the shmem index */
	result = (ShmemIndexEnt *)
		hash_search(ShmemIndex, name, HASH_ENTER_NULL, foundPtr);

// ... (L431-L438 생략: 해시 항목을 못 만들면 ERROR)

	if (*foundPtr)
	{
// ... (L442-L454 생략: 이미 있는데 크기가 다르면 ERROR)
		structPtr = result->location;
	}
	else
	{
		Size		allocated_size;

		/* It isn't in the table yet. allocate and initialize it */
		structPtr = ShmemAllocRaw(size, &allocated_size);
// ... (L463-L473 생략: 공간이 모자라면 항목을 지우고 ERROR)
		result->size = size;
		result->allocated_size = allocated_size;
		result->location = structPtr;
	}

	LWLockRelease(ShmemIndexLock);

	Assert(ShmemAddrIsValid(structPtr));

	Assert(structPtr == (void *) CACHELINEALIGN(structPtr));

	return structPtr;
}
```

실제 잘라 주는 일은 `ShmemAllocRaw` 다. `freeoffset` 을 cache line 크기(128)로 올려 더할 뿐이고, 해제 함수는 없다. 크기를 미리 다 세어 두었으므로 기동 중에 모자랄 일이 없다는 전제다.

`storage` / `ipc` / `shmem.c` L185-L227 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/shmem.c#L185-L227))

```c
// storage/ipc/shmem.c L185-L227
static void *
ShmemAllocRaw(Size size, Size *allocated_size)
{
	Size		newStart;
	Size		newFree;
	void	   *newSpace;

// ... (L192-L202 생략: 주석: MAXALIGN 으로는 모자라 cache line 에 맞춘다. 구조가 cache line 경계에 걸치지 않게 하려는 것)
	size = CACHELINEALIGN(size);
	*allocated_size = size;

	Assert(ShmemSegHdr != NULL);

	SpinLockAcquire(ShmemLock);

	newStart = ShmemSegHdr->freeoffset;

	newFree = newStart + size;
	if (newFree <= ShmemSegHdr->totalsize)
	{
		newSpace = (char *) ShmemBase + newStart;
		ShmemSegHdr->freeoffset = newFree;
	}
	else
		newSpace = NULL;

	SpinLockRelease(ShmemLock);

	/* note this assert is okay with newSpace == NULL */
	Assert(newSpace == (void *) CACHELINEALIGN(newSpace));

	return newSpace;
}
```

```text
 할당 한 번 (예: "Buffer Descriptors", 요청 16384 * 64 = 1,048,576)

 ShmemInitStruct("Buffer Descriptors", 1048576, &found)
   LWLockAcquire(ShmemIndexLock)
   hash_search(ShmemIndex, name, HASH_ENTER_NULL)     없으면 새 항목
   ShmemAllocRaw(1048576)
     size = CACHELINEALIGN(1048576) = 1048576        이미 128 의 배수
     newStart = freeoffset;  freeoffset += size        ShmemLock 스핀락 안에서
   항목에 size, allocated_size, location 을 적는다
   LWLockRelease
   -> location 을 돌려준다.  found = false 이면 호출자가 내용을 초기화한다

 pg_shmem_allocations 뷰가 이 ShmemIndex 의 항목들을 보여 준다 (pg_get_shmem_allocations, shmem.c L491)
```

해시 표는 조금 다르다. `ShmemInitHash` 는 해시 헤더만 `ShmemInitStruct` 로 받고, 원소는 `hash_create` 가 `init_size` 만큼 미리 받는다(utils/hash/dynahash.c L572-L580). 그 뒤 표가 자라면 원소를 `ShmemAllocNoError` 로 그때그때 받는다(shmem.c L348-L350). 잠금 해시는 최대치의 절반만 처음에 잡는다(lock.c L454-L455). 그래서 `LockManagerShmemSize` 가 최대치 전체에 10% 를 얹어 세그먼트 크기에 넣어 둔다.

## 버퍼 풀

버퍼 풀은 세그먼트의 대부분이다. 디스크립터 배열, 8KB 블록 배열, 블록마다 I/O 조건 변수 하나, 체크포인트 정렬용 배열, `(BufferTag -> buf_id)` 해시로 나뉜다. 디스크립터와 블록은 같은 `buf_id` 로 짝을 이룬다. 디스크립터 하나의 모양과 쓰임은 [버퍼 관리](../../flows/buffer-manager/README.md)에 있다.

`storage` / `buffer` / `buf_init.c` L161-L188 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/buf_init.c#L161-L188))

```c
// storage/buffer/buf_init.c L161-L188
Size
BufferManagerShmemSize(void)
{
	Size		size = 0;

	/* size of buffer descriptors */
	size = add_size(size, mul_size(NBuffers, sizeof(BufferDescPadded)));
	/* to allow aligning buffer descriptors */
	size = add_size(size, PG_CACHE_LINE_SIZE);

	/* size of data pages, plus alignment padding */
	size = add_size(size, PG_IO_ALIGN_SIZE);
	size = add_size(size, mul_size(NBuffers, BLCKSZ));

	/* size of stuff controlled by freelist.c */
	size = add_size(size, StrategyShmemSize());

	/* size of I/O condition variables */
	size = add_size(size, mul_size(NBuffers,
								   sizeof(ConditionVariableMinimallyPadded)));
	/* to allow aligning the above */
	size = add_size(size, PG_CACHE_LINE_SIZE);

	/* size of checkpoint sort array in bufmgr.c */
	size = add_size(size, mul_size(NBuffers, sizeof(CkptSortItem)));

	return size;
}
```

```text
 버퍼 풀의 다섯 배열 (NBuffers = 16384)

 array                      element                 버퍼 i 에게 그 자리는
 BufferDescriptors[16384]   64 B, cache line 정렬    상태, tag, content lock
 BufferBlocks               8192 B, 4096 정렬        BufferBlocks + i * 8192 의 페이지
 BufferIOCVArray[16384]     16 B                    I/O 끝을 기다리는 프로세스가 자는 조건 변수
 CkptBufferIds[16384]       20 B                    BufferSync 가 정렬에 쓰는 칸
 SharedBufHash              24 B (BufferTag 20 + id) (BufferTag -> buf_id). 항목 NBuffers + 128 개
                                                    128 파티션, 파티션마다 BufMappingLock
```

해시 항목 수가 `NBuffers + NUM_BUFFER_PARTITIONS` 인 이유는 버퍼를 옮길 때 새 항목을 먼저 넣고 옛 항목을 나중에 지우기 때문이다. 파티션마다 동시에 하나씩 겹칠 수 있다(freelist.c L483-L486 주석).

## WAL 버퍼

WAL 버퍼는 `XLOG Ctl` 구조 하나 안에 같이 잡힌다. 기본값 `wal_buffers = -1` 은 버퍼 풀의 1/32 로 정하되, WAL 세그먼트 하나(16MB)를 넘지 않게 한다.

`access` / `transam` / `xlog.c` L4656-L4667 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L4656-L4667))

```c
// access/transam/xlog.c L4656-L4667
static int
XLOGChooseNumBuffers(void)
{
	int			xbuffers;

	xbuffers = NBuffers / 32;
	if (xbuffers > (wal_segment_size / XLOG_BLCKSZ))
		xbuffers = (wal_segment_size / XLOG_BLCKSZ);
	if (xbuffers < 8)
		xbuffers = 8;
	return xbuffers;
}
```

`access` / `transam` / `xlog.c` L4906-L4953 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L4906-L4953))

```c
// access/transam/xlog.c L4906-L4953
XLOGShmemSize(void)
{
	Size		size;

// ... (L4910-L4931 생략: wal_buffers = -1 이면 XLOGChooseNumBuffers 의 값을 GUC 에 써 넣는다)
	Assert(XLOGbuffers > 0);

	/* XLogCtl */
	size = sizeof(XLogCtlData);

	/* WAL insertion locks, plus alignment */
	size = add_size(size, mul_size(sizeof(WALInsertLockPadded), NUM_XLOGINSERT_LOCKS + 1));
	/* xlblocks array */
	size = add_size(size, mul_size(sizeof(pg_atomic_uint64), XLOGbuffers));
	/* extra alignment padding for XLOG I/O buffers */
	size = add_size(size, Max(XLOG_BLCKSZ, PG_IO_ALIGN_SIZE));
	/* and the buffers themselves */
	size = add_size(size, mul_size(XLOG_BLCKSZ, XLOGbuffers));

	/*
	 * Note: we don't count ControlFileData, it comes out of the "slop factor"
	 * added by CreateSharedMemoryAndSemaphores.  This lets us use this
	 * routine again below to compute the actual allocation size.
	 */

	return size;
}
```

기본 설정이면 16384 / 32 = 512 페이지, 4MB 다. 이 버퍼에 레코드를 복사하는 길은 [행 쓰기와 WAL 기록](../../flows/heap-insert-wal/README.md)의 `XLogInsertRecord` 에 있다.

## CLOG 와 SLRU

CLOG(`pg_xact`)는 트랜잭션마다 2비트로 커밋 상태를 적는 파일이고, 그 최근 페이지들을 SLRU(작은 LRU 버퍼)로 공유 메모리에 둔다. `commit_timestamp`, `subtransaction`, `multixact` 도 같은 SLRU 틀을 쓴다. 18 의 SLRU 는 16 슬롯 단위의 bank 로 나뉘고 bank 마다 잠금이 있다.

`access` / `transam` / `clog.c` L767-L784 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/clog.c#L767-L784))

```c
// access/transam/clog.c L767-L784
static int
CLOGShmemBuffers(void)
{
	/* auto-tune based on shared buffers */
	if (transaction_buffers == 0)
		return SimpleLruAutotuneBuffers(512, 1024);

	return Min(Max(16, transaction_buffers), CLOG_MAX_ALLOWED_BUFFERS);
}

/*
 * Initialization of shared memory for CLOG
 */
Size
CLOGShmemSize(void)
{
	return SimpleLruShmemSize(CLOGShmemBuffers(), CLOG_LSNS_PER_PAGE);
}
```

`access` / `transam` / `slru.c` L197-L236 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/slru.c#L197-L236))

```c
// access/transam/slru.c L197-L236
Size
SimpleLruShmemSize(int nslots, int nlsns)
{
	int			nbanks = nslots / SLRU_BANK_SIZE;
	Size		sz;

	Assert(nslots <= SLRU_MAX_ALLOWED_BUFFERS);
	Assert(nslots % SLRU_BANK_SIZE == 0);

	/* we assume nslots isn't so large as to risk overflow */
	sz = MAXALIGN(sizeof(SlruSharedData));
	sz += MAXALIGN(nslots * sizeof(char *));	/* page_buffer[] */
	sz += MAXALIGN(nslots * sizeof(SlruPageStatus));	/* page_status[] */
	sz += MAXALIGN(nslots * sizeof(bool));	/* page_dirty[] */
	sz += MAXALIGN(nslots * sizeof(int64)); /* page_number[] */
	sz += MAXALIGN(nslots * sizeof(int));	/* page_lru_count[] */
	sz += MAXALIGN(nslots * sizeof(LWLockPadded));	/* buffer_locks[] */
	sz += MAXALIGN(nbanks * sizeof(LWLockPadded));	/* bank_locks[] */
	sz += MAXALIGN(nbanks * sizeof(int));	/* bank_cur_lru_count[] */

	if (nlsns > 0)
		sz += MAXALIGN(nslots * nlsns * sizeof(XLogRecPtr));	/* group_lsn[] */

	return BUFFERALIGN(sz) + BLCKSZ * nslots;
}

// ... (L223-L229 생략: SimpleLruAutotuneBuffers 머리 주석)
int
SimpleLruAutotuneBuffers(int divisor, int max)
{
	return Min(max - (max % SLRU_BANK_SIZE),
			   Max(SLRU_BANK_SIZE,
				   NBuffers / divisor - (NBuffers / divisor) % SLRU_BANK_SIZE));
}
```

```text
 CLOG SLRU 의 크기 (transaction_buffers = 0, NBuffers 16384)

 nslots = Min(1024, Max(16, 16384/512 - (16384/512) % 16)) = 32      bank 2 개 (SLRU_BANK_SIZE 16)
 nlsns  = CLOG_LSNS_PER_PAGE = (8192 * 4) / 32 = 1024                  트랜잭션 32 개마다 LSN 하나

 control part
   SlruSharedData                         104
   page_buffer[32]        32 * 8          256
   page_status[32]        32 * 4          128
   page_dirty[32]         32 * 1           32
   page_number[32]        32 * 8          256
   page_lru_count[32]     32 * 4          128
   buffer_locks[32]       32 * 128       4096
   bank_locks[2]          2 * 128         256
   bank_cur_lru_count[2]  MAXALIGN(8)       8
   group_lsn              32 * 1024 * 8  262144
                                         -------
                                          267408 -> BUFFERALIGN(32) -> 267424
 pages                    32 * 8192      262144
 total                                    529568

 페이지 하나 = 8192 * 4 = 32768 트랜잭션. 32 페이지면 최근 1,048,576 개 xid 의 상태가 메모리에 있다
```

## 잠금 해시

heavyweight lock 은 두 해시 표에 산다. `LOCK` 은 잠긴 대상(테이블, 행, 트랜잭션 ...)마다 하나, `PROCLOCK` 은 (대상, 보유 프로세스) 쌍마다 하나다. 최대 항목 수는 `max_locks_per_transaction` 에 프로세스 수를 곱한 값이고, `PROCLOCK` 은 대상 하나에 평균 둘이 붙는다고 보고 두 배로 잡는다(lock.c L471).

`storage` / `lmgr` / `lock.c` L56-L57 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L56-L57))

```c
// storage/lmgr/lock.c L56-L57
#define NLOCKENTS() \
	mul_size(max_locks_per_xact, add_size(MaxBackends, max_prepared_xacts))
```

`storage` / `lmgr` / `lock.c` L3725-L3745 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/lock.c#L3725-L3745))

```c
// storage/lmgr/lock.c L3725-L3745
Size
LockManagerShmemSize(void)
{
	Size		size = 0;
	long		max_table_size;

	/* lock hash table */
	max_table_size = NLOCKENTS();
	size = add_size(size, hash_estimate_size(max_table_size, sizeof(LOCK)));

	/* proclock hash table */
	max_table_size *= 2;
	size = add_size(size, hash_estimate_size(max_table_size, sizeof(PROCLOCK)));

	/*
	 * Since NLOCKENTS is only an estimate, add 10% safety margin.
	 */
	size = add_size(size, size / 10);

	return size;
}
```

```text
 잠금 해시 크기 (MaxBackends 136, max_prepared_transactions 0)

 table     entries  element size                                   allocation               bytes
 LOCK      8704     MAXALIGN(HASHELEMENT 16) + MAXALIGN(152) = 168  182 묶음 * 48 개
 PROCLOCK  17408    16 + MAXALIGN(64) = 80                          342 묶음 * 51 개
                    + 디렉터리, 세그먼트, 헤더를 더해 LOCK 1,601,616, PROCLOCK 1,660,400
 합 3,262,016 에 10% 326,201 을 얹어 3,588,217

 둘 다 16 파티션 (NUM_LOCK_PARTITIONS = 1 << 4). 파티션마다 LWLock 하나
 자기 데이터베이스 테이블의 약한 잠금(ShareUpdateExclusive 미만)은 먼저 PGPROC 의
 fast-path 슬롯 64 개에 넣고 해시는 건너뛴다 (EligibleForRelationFastPath, lock.c L267-L272)
```

잠금을 얻는 길과 fast-path 는 [heavyweight lock](../../flows/heavyweight-lock/README.md) 흐름에 있다.

## PGPROC 배열과 ProcGlobal

**프로세스 하나 = `PGPROC` 하나**다. 공유 메모리에 있는 프로세스의 얼굴이고, 다른 프로세스가 이 프로세스를 찾고 깨우고 기다리게 하는 자리가 모두 여기 있다. 배열은 기동 때 `TotalProcs` 개를 한 번에 만들고, 용도별 빈 목록에 나눠 둔다.

`storage` / `lmgr` / `proc.c` L96-L110 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L96-L110))

```c
// storage/lmgr/proc.c L96-L110
static Size
PGProcShmemSize(void)
{
	Size		size = 0;
	Size		TotalProcs =
		add_size(MaxBackends, add_size(NUM_AUXILIARY_PROCS, max_prepared_xacts));

	size = add_size(size, mul_size(TotalProcs, sizeof(PGPROC)));
	size = add_size(size, mul_size(TotalProcs, sizeof(*ProcGlobal->xids)));
	size = add_size(size, mul_size(TotalProcs, sizeof(*ProcGlobal->subxidStates)));
	size = add_size(size, mul_size(TotalProcs, sizeof(*ProcGlobal->statusFlags)));

	return size;
}

```

```text
 PGPROC structures 의 배치 (TotalProcs 174, 인덱스 = ProcNumber)

 index range              list                 누구의 자리
 allProcs[0   .. 99 ]     freeProcs            일반 backend (max_connections 100)
 allProcs[100 .. 117]     autovacFreeProcs     autovacuum worker 16 + launcher, slotsync 2
 allProcs[118 .. 125]     bgworkerFreeProcs    bgworker 8
 allProcs[126 .. 135]     walsenderFreeProcs   walsender 10
 allProcs[136 .. 173]     AuxiliaryProcs       보조 프로세스 38 (목록 없이 선형 탐색)
 allProcs[174 .. ]        PreparedXactProcs    max_prepared_transactions 0 개
 174 * 832 = 144,768

 dense array              element              PGPROC 필드의 사본, pgxactoff 로 찾는다
 xids[174]                4 B                  PGPROC.xid
 subxidStates[174]        2 B                  PGPROC.subxidStatus
 statusFlags[174]         1 B                  PGPROC.statusFlags
 174 * (4 + 2 + 1) = 1,218  ->  PGPROC structures 합계 145,986

 Fast-Path Lock Array     174 * (fpLockBits 4*8 + fpRelId 64*4) = 174 * 288 = 50,112
 Proc Header              PROC_HDR 128 B + slock_t 1 B

 나누는 곳: InitProcGlobal (storage/lmgr/proc.c L328-L351), AuxiliaryProcs 포인터 L376
```

`PGPROC` 의 필드는 쓰임별로 묶여 있다. 아래 코드 뒤의 표가 바이트 자리다.

`include` / `storage` / `proc.h` L176-L322 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/proc.h#L176-L322))

```c
// storage/proc.h L176-L322
struct PGPROC
{
	dlist_node	links;			/* list link if process is in a list */
	dlist_head *procgloballist; /* procglobal list that owns this PGPROC */

	PGSemaphore sem;			/* ONE semaphore to sleep on */
	ProcWaitStatus waitStatus;

	Latch		procLatch;		/* generic latch for process */


	TransactionId xid;			/* id of top-level transaction currently being
								 * executed by this proc, if running and XID
								 * is assigned; else InvalidTransactionId.
								 * mirrored in ProcGlobal->xids[pgxactoff] */

	TransactionId xmin;			/* minimal running XID as it was when we were
								 * starting our xact, excluding LAZY VACUUM:
								 * vacuum must not remove tuples deleted by
								 * xid >= xmin ! */

	int			pid;			/* Backend's process ID; 0 if prepared xact */

	int			pgxactoff;		/* offset into various ProcGlobal->arrays with
								 * data mirrored from this PGPROC */

// ... (L202-L207 생략: vxid 주석)
	struct
	{
		ProcNumber	procNumber; /* For regular backends, equal to
								 * GetNumberFromPGProc(proc).  For prepared
								 * xacts, ID of the original backend that
								 * processed the transaction. For unused
								 * PGPROC entries, INVALID_PROC_NUMBER. */
		LocalTransactionId lxid;	/* local id of top-level transaction
									 * currently * being executed by this
									 * proc, if running; else
									 * InvalidLocalTransactionId */
	}			vxid;

	/* These fields are zero while a backend is still starting up: */
	Oid			databaseId;		/* OID of database this backend is using */
	Oid			roleId;			/* OID of role using this backend */

	Oid			tempNamespaceId;	/* OID of temp schema this backend is
									 * using */

	bool		isRegularBackend;	/* true if it's a regular backend. */

// ... (L230-L234 생략: recoveryConflictPending 주석)
	bool		recoveryConflictPending;

	/* Info about LWLock the process is currently waiting for, if any. */
	uint8		lwWaiting;		/* see LWLockWaitState */
	uint8		lwWaitMode;		/* lwlock mode being waited for */
	proclist_node lwWaitLink;	/* position in LW lock wait list */

	/* Support for condition variables. */
	proclist_node cvWaitLink;	/* position in CV wait list */

	/* Info about lock the process is currently waiting for, if any. */
	/* waitLock and waitProcLock are NULL if not currently waiting. */
	LOCK	   *waitLock;		/* Lock object we're sleeping on ... */
	PROCLOCK   *waitProcLock;	/* Per-holder info for awaited lock */
	LOCKMODE	waitLockMode;	/* type of lock we're waiting for */
	LOCKMASK	heldLocks;		/* bitmask for lock types already held on this
								 * lock object by this backend */
	pg_atomic_uint64 waitStart; /* time at which wait for lock acquisition
								 * started */

	int			delayChkptFlags;	/* for DELAY_CHKPT_* flags */

	uint8		statusFlags;	/* this backend's status flags, see PROC_*
								 * above. mirrored in
								 * ProcGlobal->statusFlags[pgxactoff] */

// ... (L261-L266 생략: 동기 복제 대기 주석)
	XLogRecPtr	waitLSN;		/* waiting for this LSN or higher */
	int			syncRepState;	/* wait state for sync rep */
	dlist_node	syncRepLinks;	/* list link if process is in syncrep queue */

// ... (L271-L275 생략: myProcLocks 주석)
	dlist_head	myProcLocks[NUM_LOCK_PARTITIONS];

	XidCacheStatus subxidStatus;	/* mirrored with
									 * ProcGlobal->subxidStates[i] */
	struct XidCache subxids;	/* cache for subtransaction XIDs */

	/* Support for group XID clearing. */
	/* true, if member of ProcArray group waiting for XID clear */
	bool		procArrayGroupMember;
	/* next ProcArray group member waiting for XID clear */
	pg_atomic_uint32 procArrayGroupNext;

	/*
	 * latest transaction id among the transaction's main XID and
	 * subtransactions
	 */
	TransactionId procArrayGroupMemberXid;

	uint32		wait_event_info;	/* proc's wait information */

	/* Support for group transaction status update. */
	bool		clogGroupMember;	/* true, if member of clog group */
	pg_atomic_uint32 clogGroupNext; /* next clog group member */
	TransactionId clogGroupMemberXid;	/* transaction id of clog group member */
	XidStatus	clogGroupMemberXidStatus;	/* transaction status of clog
											 * group member */
	int64		clogGroupMemberPage;	/* clog page corresponding to
										 * transaction id of clog group member */
	XLogRecPtr	clogGroupMemberLsn; /* WAL location of commit record for clog
									 * group member */

	/* Lock manager data, recording fast-path locks taken by this backend. */
	LWLock		fpInfoLock;		/* protects per-backend fast-path state */
	uint64	   *fpLockBits;		/* lock modes held for each fast-path slot */
	Oid		   *fpRelId;		/* slots for rel oids */
	bool		fpVXIDLock;		/* are we holding a fast-path VXID lock? */
	LocalTransactionId fpLocalTransactionId;	/* lxid for fast-path VXID
												 * lock */

	/*
	 * Support for lock groups.  Use LockHashPartitionLockByProc on the group
	 * leader to get the LWLock protecting these fields.
	 */
	PGPROC	   *lockGroupLeader;	/* lock group leader, if I'm a member */
	dlist_head	lockGroupMembers;	/* list of members, if I'm a leader */
	dlist_node	lockGroupLink;	/* my member link, if I'm a member */
};
```

```text
 PGPROC 바이트 배치 (sizeof 832, x86-64)

 offset  size  field                        쓰는 이
 ------  ----  ---------------------------  -----------------------------------------------
      0    16  links                        빈 목록, 잠금 대기 큐의 고리
     16     8  procgloballist               어느 빈 목록 소속인가
     24     8  sem                          세마포어. LWLock 대기에서 잔다
     32     4  waitStatus                   heavyweight lock 대기 결과
     36    16  procLatch                    SetLatch 로 이 프로세스를 깨운다
     52     4  xid                          최상위 트랜잭션 xid (xids[] 에 사본)
     56     4  xmin                         스냅샷의 xmin. vacuum 의 경계
     60     4  pid
     64     4  pgxactoff                    조밀 배열 xids[] 등의 인덱스
     68     8  vxid {procNumber, lxid}       가상 트랜잭션 id
     76    12  databaseId, roleId, tempNamespaceId
     88     4  isRegularBackend, recoveryConflictPending, lwWaiting, lwWaitMode
     92    16  lwWaitLink, cvWaitLink       LWLock 대기 목록, 조건 변수 대기 목록
    112    24  waitLock, waitProcLock, waitLockMode, heldLocks   잠금 대기 중인 대상
    136     8  waitStart                    잠금 대기 시작 시각
    144     8  delayChkptFlags, statusFlags
    152    32  waitLSN, syncRepState, syncRepLinks   동기 복제 대기
    184   256  myProcLocks[16]              파티션별 보유 PROCLOCK 목록 (16 * 16)
    440     2  subxidStatus                 count, overflowed
    444   256  subxids.xids[64]             서브트랜잭션 xid 캐시 64 개
    700    16  procArrayGroup*, wait_event_info   그룹 xid 정리
    716    36  clogGroup*                   그룹 CLOG 갱신
    752    16  fpInfoLock                   fast-path 슬롯을 지키는 LWLock
    768    16  fpLockBits, fpRelId          Fast-Path Lock Array 안을 가리키는 포인터
    784     8  fpVXIDLock, fpLocalTransactionId
    792    40  lockGroupLeader, lockGroupMembers, lockGroupLink   병렬 쿼리 잠금 그룹
```

`xid`, `subxidStatus`, `statusFlags` 는 `PROC_HDR` 의 조밀 배열에도 같은 값이 있다. `GetSnapshotData` 가 모든 프로세스의 xid 를 훑을 때 832 바이트 간격으로 뛰지 않고 4 바이트 배열 하나를 읽게 하려는 것이다. 자주 바뀌는 `xmin` 과 덜 바뀌는 xid 가 같은 cache line 을 더럽히지 않게 하려는 이유도 주석에 있다(proc.h L352-L357). 이 배열을 읽는 쪽은 [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md)의 `GetSnapshotData` 다.

`include` / `storage` / `proc.h` L383-L429 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/proc.h#L383-L429))

```c
// storage/proc.h L383-L429
typedef struct PROC_HDR
{
	/* Array of PGPROC structures (not including dummies for prepared txns) */
	PGPROC	   *allProcs;

	/* Array mirroring PGPROC.xid for each PGPROC currently in the procarray */
	TransactionId *xids;

	/*
	 * Array mirroring PGPROC.subxidStatus for each PGPROC currently in the
	 * procarray.
	 */
	XidCacheStatus *subxidStates;

	/*
	 * Array mirroring PGPROC.statusFlags for each PGPROC currently in the
	 * procarray.
	 */
	uint8	   *statusFlags;

	/* Length of allProcs array */
	uint32		allProcCount;
	/* Head of list of free PGPROC structures */
	dlist_head	freeProcs;
	/* Head of list of autovacuum & special worker free PGPROC structures */
	dlist_head	autovacFreeProcs;
	/* Head of list of bgworker free PGPROC structures */
	dlist_head	bgworkerFreeProcs;
	/* Head of list of walsender free PGPROC structures */
	dlist_head	walsenderFreeProcs;
	/* First pgproc waiting for group XID clear */
	pg_atomic_uint32 procArrayGroupFirst;
	/* First pgproc waiting for group transaction status update */
	pg_atomic_uint32 clogGroupFirst;

	/*
	 * Current slot numbers of some auxiliary processes. There can be only one
	 * of each of these running at a time.
	 */
	ProcNumber	walwriterProc;
	ProcNumber	checkpointerProc;

	/* Current shared estimate of appropriate spins_per_delay value */
	int			spins_per_delay;
	/* Buffer id of the buffer that Startup process waits for pin on, or -1 */
	int			startupBufferPinWaitBufId;
} PROC_HDR;
```

## ProcArray

`ProcArray` 는 "지금 트랜잭션을 돌릴 수 있는 프로세스"의 목록이다. `PGPROC` 배열 전체가 아니라 실제로 들어온 프로세스의 번호만 `pgprocnos[]` 에 촘촘히 담는다. backend 는 `InitProcessPhase2` 에서 여기에 오르고 그때부터 다른 backend 의 스냅샷에 보인다.

`storage` / `ipc` / `procarray.c` L71-L100 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L71-L100))

```c
// storage/ipc/procarray.c L71-L100
typedef struct ProcArrayStruct
{
	int			numProcs;		/* number of valid procs entries */
	int			maxProcs;		/* allocated size of procs array */

	/*
	 * Known assigned XIDs handling
	 */
	int			maxKnownAssignedXids;	/* allocated size of array */
	int			numKnownAssignedXids;	/* current # of valid entries */
	int			tailKnownAssignedXids;	/* index of oldest valid element */
	int			headKnownAssignedXids;	/* index of newest element, + 1 */

// ... (L84-L90 생략: lastOverflowedXid 주석)
	TransactionId lastOverflowedXid;

	/* oldest xmin of any replication slot */
	TransactionId replication_slot_xmin;
	/* oldest catalog xmin of any replication slot */
	TransactionId replication_slot_catalog_xmin;

	/* indexes into allProcs[], has PROCARRAY_MAXPROCS entries */
	int			pgprocnos[FLEXIBLE_ARRAY_MEMBER];
} ProcArrayStruct;
```

`storage` / `ipc` / `procarray.c` L376-L412 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/procarray.c#L376-L412))

```c
// storage/ipc/procarray.c L376-L412
ProcArrayShmemSize(void)
{
	Size		size;

	/* Size of the ProcArray structure itself */
#define PROCARRAY_MAXPROCS	(MaxBackends + max_prepared_xacts)

	size = offsetof(ProcArrayStruct, pgprocnos);
	size = add_size(size, mul_size(sizeof(int), PROCARRAY_MAXPROCS));

// ... (L386-L398 생략: KnownAssignedXids 주석: hot standby 용 구조는 시작 때 미리 잡는다)
#define TOTAL_MAX_CACHED_SUBXIDS \
	((PGPROC_MAX_CACHED_SUBXIDS + 1) * PROCARRAY_MAXPROCS)

	if (EnableHotStandby)
	{
		size = add_size(size,
						mul_size(sizeof(TransactionId),
								 TOTAL_MAX_CACHED_SUBXIDS));
		size = add_size(size,
						mul_size(sizeof(bool), TOTAL_MAX_CACHED_SUBXIDS));
	}

	return size;
}
```

```text
 ProcArray 의 크기 (PROCARRAY_MAXPROCS = MaxBackends 136 + max_prepared_xacts 0)

 part                                   computed as                   bytes
 offsetof(ProcArrayStruct, pgprocnos)   9 * 4                            36
 pgprocnos[136]                         136 * 4                         544
 KnownAssignedXids                      (64 + 1) * 136 * 4 = 8840 * 4   35,360
 KnownAssignedXidsValid                 8840 * 1                         8,840
                                                                      -------
                                                                       44,780

 KnownAssigned 둘은 hot_standby 가 켜져 있으면(기본) primary 에서도 잡는다
```

## db-engine 에서는

db-engine 의 버퍼 풀은 JVM 힙 안의 `LinkedHashMap<PageId, Page>` 하나이고, 프로세스가 하나라 "공유" 할 대상이 없다. 크기도 미리 정하지 않는다. 페이지가 필요할 때 `ByteArray(4096)` 를 새로 만들고, 쫓겨난 페이지는 GC 가 치운다.

```text
 같은 문제(디스크 페이지를 메모리에 붙잡아 두기), 두 구현 (위 PostgreSQL / 아래 db-engine)

 자리
   PostgreSQL  공유 메모리 세그먼트. 기동 때 크기를 다 세어 한 번에 잡는다
               BufferBlocks 16384 * 8KB 는 처음부터 다 있고, 빈 버퍼는 tag 가 비었을 뿐이다
   db-engine   JVM 힙. newPage / fetchPage 마다 Page 객체를 만든다. capacity 256 * 4KB = 1MB

 찾기
   PostgreSQL  SharedBufHash (BufferTag -> buf_id), 128 파티션 잠금
   db-engine   LinkedHashMap 의 get. 잠금 없음 (단일 스레드 가정)

 상태
   PostgreSQL  BufferDesc 의 state 원자 변수 하나에 refcount, usage_count, 플래그
   db-engine   Page 의 pinCount, isDirty 필드

 쫓아낼 것 고르기
   PostgreSQL  clock sweep. nextVictimBuffer 가 배열을 돌며 usage_count 를 깎는다
   db-engine   access-order LinkedHashMap 의 맨 앞에서 pinCount == 0 인 첫 페이지 (LRU)

 다른 프로세스가 보나
   PostgreSQL  fork 로 같은 매핑을 물려받아 모든 backend 가 같은 버퍼를 본다
   db-engine   한 프로세스뿐
```

db-engine 02-02 는 "dirty page를 evict할 때 반드시 먼저 디스크에 쓴다."를 불변식 CI-2 로 못 박았다. PostgreSQL 은 같은 규칙에 하나를 더 얹는다. 페이지를 쓰기 전에 그 페이지의 LSN 까지 WAL 을 먼저 flush 한다(`FlushBuffer` 의 `XLogFlush`). 챕터: [02-02-buffer-pool](../../../../../project/db-engine/02-02-buffer-pool/).

## 어디에서 쓰이는가

```text
 [버퍼 관리]             BufferDescriptors, BufferBlocks, SharedBufHash, StrategyControl
 [행 쓰기와 WAL 기록]    XLOG Ctl 의 WAL 버퍼와 insert lock
 [MVCC 가시성과 스냅샷]  ProcArray 와 ProcGlobal->xids[]. CLOG SLRU 에서 커밋 여부
 [heavyweight lock]      LOCK / PROCLOCK 해시, PGPROC 의 fast-path 슬롯, myProcLocks
 [커밋]                  ProcArrayEndTransaction 이 PGPROC.xid 와 xids[] 를 지운다
 [연결과 backend 기동]   InitProcess 가 freeProcs 에서 PGPROC 하나를 꺼낸다
 [프로세스 모델]         PGPROC.procLatch 로 서로 깨우고, PMSignal 플래그로 postmaster 를 부른다
```

흐름 문서: [버퍼 관리](../../flows/buffer-manager/README.md), [행 쓰기와 WAL 기록](../../flows/heap-insert-wal/README.md), [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md), [heavyweight lock](../../flows/heavyweight-lock/README.md), [커밋](../../flows/commit/README.md), [연결과 backend 기동](../../flows/connection-startup/README.md). 버퍼 블록 안의 페이지 모양은 [페이지와 튜플 레이아웃](../page-tuple-layout/README.md)에 있다.

## 다루지 않는 것

동적 공유 메모리(DSM, `dsm.c`, DSA, `DSMRegistry`)와 병렬 쿼리의 세그먼트, huge pages 크기 계산(`CreateAnonymousSegment` 의 `MAP_HUGETLB`), `EXEC_BACKEND` 의 `AttachSharedMemoryStructs`, `shared_preload_libraries` 의 `RequestAddinShmemSpace` 와 `shmem_startup_hook`, LWLock 배열과 tranche 의 크기, predicate lock(SSI) 구조, multixact 와 subtrans SLRU 의 크기, 공유 통계(`StatsShmemInit`), AIO 공유 구조, `XLogCtlData` 필드, NUMA 관련 함수(`pg_get_shmem_allocations_numa`)는 같은 뼈대의 곁가지라 요약만 했다.
