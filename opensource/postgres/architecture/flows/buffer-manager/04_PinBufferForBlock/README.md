# PinBufferForBlock

상위: [버퍼 관리](../README.md)

**블록 하나에 버퍼를 배정하고 pin 을 거는 갈림길이다.** 임시 테이블이면 backend 자기 메모리의 local buffer 로, 아니면 shared buffers 의 [05] `BufferAlloc` 으로 보낸다. 어느 쪽이든 돌아온 버퍼는 이미 pin 이 걸려 있고 tag 도 이 블록으로 붙어 있으며, `*foundPtr` 가 내용까지 유효한지를 알려 준다. hit 통계는 여기서 센다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L1100-L1176 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1100-L1176))

## 실제 코드

```c
// bufmgr.c L1100-L1176
static pg_always_inline Buffer
PinBufferForBlock(Relation rel,
				  SMgrRelation smgr,
				  char persistence,
				  ForkNumber forkNum,
				  BlockNumber blockNum,
				  BufferAccessStrategy strategy,
				  bool *foundPtr)
{
	BufferDesc *bufHdr;
	IOContext	io_context;
	IOObject	io_object;

	Assert(blockNum != P_NEW);

	/* Persistence should be set before */
	Assert((persistence == RELPERSISTENCE_TEMP ||
			persistence == RELPERSISTENCE_PERMANENT ||
			persistence == RELPERSISTENCE_UNLOGGED));

	if (persistence == RELPERSISTENCE_TEMP)
	{
		io_context = IOCONTEXT_NORMAL;
		io_object = IOOBJECT_TEMP_RELATION;
	}
	else
	{
		io_context = IOContextForStrategy(strategy);
		io_object = IOOBJECT_RELATION;
	}

	// ... (L1131-L1135 생략: dtrace 프로브)

	if (persistence == RELPERSISTENCE_TEMP)
	{
		bufHdr = LocalBufferAlloc(smgr, forkNum, blockNum, foundPtr);
		if (*foundPtr)
			pgBufferUsage.local_blks_hit++;
	}
	else
	{
		bufHdr = BufferAlloc(smgr, persistence, forkNum, blockNum,
							 strategy, foundPtr, io_context);
		if (*foundPtr)
			pgBufferUsage.shared_blks_hit++;
	}
	if (rel)
	{
		/*
		 * While pgBufferUsage's "read" counter isn't bumped unless we reach
		 * WaitReadBuffers() (so, not for hits, and not for buffers that are
		 * zeroed instead), the per-relation stats always count them.
		 */
		pgstat_count_buffer_read(rel);
		if (*foundPtr)
			pgstat_count_buffer_hit(rel);
	}
	if (*foundPtr)
	{
		pgstat_count_io_op(io_object, io_context, IOOP_HIT, 1, 0);
		if (VacuumCostActive)
			VacuumCostBalance += VacuumCostPageHit;

		// ... (L1167-L1172 생략: dtrace 프로브)
	}

	return BufferDescriptorGetBuffer(bufHdr);
}
```

## 동작 흐름

```text
 L1120  persistence == TEMP
          io_context = NORMAL, io_object = TEMP_RELATION
 L1127  그 밖 (PERMANENT, UNLOGGED)
          io_context = IOContextForStrategy(strategy)
                       NULL -> NORMAL, BULKREAD / BULKWRITE / VACUUM ring -> 각 context

 L1137  TEMP      LocalBufferAlloc            backend 전용, lock 없음, 음수 Buffer 번호
                    found 면 local_blks_hit++
 L1143  그 밖     [05] BufferAlloc            shared buffers, 양수 Buffer 번호
                    found 면 shared_blks_hit++

 L1150  rel 이 있으면 pgstat_count_buffer_read, found 면 pgstat_count_buffer_hit
 L1161  found 면 IOOP_HIT 를 세고 vacuum 비용에 VacuumCostPageHit 를 더한다

 L1175  BufferDescriptorGetBuffer(bufHdr)     buf_id + 1
```

여기서 `found` 가 `true` 라고 해서 I/O 가 끝난 것은 아니다. [05] 는 tag 가 해시에 있어도 `BM_VALID` 가 아니면 `found = false` 로 고친다. 그래서 found 가 뜻하는 것은 "이 블록의 내용이 지금 유효하다"이다.

```text
 found 의 세 경우 (shared buffers)

 found = true   해시에 tag 있음, BM_VALID. hit
 found = false  해시에 tag 있음, BM_VALID 아님
                남이 읽는 중이거나, 직전 읽기가 실패했거나,
                누가 StartReadBuffers 만 하고 아직 Wait 전 (BufferAlloc 주석 L2057-L2061)
 found = false  해시에 tag 없음. 희생자를 새로 받아 tag 를 단 직후

 found = false 인 버퍼는 누가 읽을지 [10] 에서 StartBufferIO 로 정한다
```

`shared_blks_read` 는 여기서 올리지 않는다. 실제로 I/O 를 낸 [10] `AsyncReadBuffers` 가 올린다. 주석 L1152-L1155 가 이 차이를 적어 두었다.

## 결과가 쓰이는 곳

```text
 Buffer, *foundPtr
      --> [03] StartReadBuffersImpl 이 hit 이면 바로 끝내고 miss 면 I/O 범위에 넣는다
      --> [02] 의 0 채움 모드는 found 를 ZeroAndLockBuffer 에 넘긴다
 pgBufferUsage.shared_blks_hit
      --> EXPLAIN (BUFFERS) 의 "shared hit"
```

## 다루지 않는 것

`LocalBufferAlloc` 과 local buffer 의 교체(`localbuf.c`), `IOContextForStrategy` 가 쓰는 pg_stat_io 분류, vacuum 비용 지연은 이 흐름 밖이다.
