# ReadBuffer_common

상위: [버퍼 관리](../README.md)

**모든 `ReadBuffer` 변형이 모이는 자리다.** 다른 세션 임시 테이블 거절, `P_NEW` 확장, 0 채움 모드를 먼저 걸러 내고, 남은 보통 읽기는 `StartReadBuffer` 한 번과 필요하면 `WaitReadBuffers` 한 번으로 끝낸다. PG18 에서 이 함수는 AIO 읽기 API 의 단일 블록 사용자가 되었다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L1183-L1262 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L1183-L1262))

## 실제 코드

```c
// bufmgr.c L1183-L1262
static pg_always_inline Buffer
ReadBuffer_common(Relation rel, SMgrRelation smgr, char smgr_persistence,
				  ForkNumber forkNum,
				  BlockNumber blockNum, ReadBufferMode mode,
				  BufferAccessStrategy strategy)
{
	ReadBuffersOperation operation;
	Buffer		buffer;
	int			flags;
	char		persistence;

	/*
	 * Reject attempts to read non-local temporary relations; we would be
	 * likely to get wrong data since we have no visibility into the owning
	 * session's local buffers.  This is the canonical place for the check,
	 * covering the ReadBufferExtended() entry point and any other caller that
	 * supplies a Relation.
	 */
	if (rel && RELATION_IS_OTHER_TEMP(rel))
		ereport(ERROR,
				(errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
				 errmsg("cannot access temporary tables of other sessions")));

	/*
	 * Backward compatibility path, most code should use ExtendBufferedRel()
	 * instead, as acquiring the extension lock inside ExtendBufferedRel()
	 * scales a lot better.
	 */
	if (unlikely(blockNum == P_NEW))
	{
		uint32		flags = EB_SKIP_EXTENSION_LOCK;

		/*
		 * Since no-one else can be looking at the page contents yet, there is
		 * no difference between an exclusive lock and a cleanup-strength
		 * lock.
		 */
		if (mode == RBM_ZERO_AND_LOCK || mode == RBM_ZERO_AND_CLEANUP_LOCK)
			flags |= EB_LOCK_FIRST;

		return ExtendBufferedRel(BMR_REL(rel), forkNum, strategy, flags);
	}

	if (rel)
		persistence = rel->rd_rel->relpersistence;
	else
		persistence = smgr_persistence;

	if (unlikely(mode == RBM_ZERO_AND_CLEANUP_LOCK ||
				 mode == RBM_ZERO_AND_LOCK))
	{
		bool		found;

		buffer = PinBufferForBlock(rel, smgr, persistence,
								   forkNum, blockNum, strategy, &found);
		ZeroAndLockBuffer(buffer, mode, found);
		return buffer;
	}

	/*
	 * Signal that we are going to immediately wait. If we're immediately
	 * waiting, there is no benefit in actually executing the IO
	 * asynchronously, it would just add dispatch overhead.
	 */
	flags = READ_BUFFERS_SYNCHRONOUSLY;
	if (mode == RBM_ZERO_ON_ERROR)
		flags |= READ_BUFFERS_ZERO_ON_ERROR;
	operation.smgr = smgr;
	operation.rel = rel;
	operation.persistence = persistence;
	operation.forknum = forkNum;
	operation.strategy = strategy;
	if (StartReadBuffer(&operation,
						&buffer,
						blockNum,
						flags))
		WaitReadBuffers(&operation);

	return buffer;
}
```

## 동작 흐름

```text
 L1201  rel 이 다른 세션의 임시 테이블이면 ERROR
          그 세션의 local buffer 를 볼 수 없어서다 (주석 L1195-L1199)
 L1211  blockNum == P_NEW
          L1213  flags = EB_SKIP_EXTENSION_LOCK
          L1220  0 채움 모드면 EB_LOCK_FIRST 를 더한다
          L1223  ExtendBufferedRel 로 한 블록 늘려 돌려준다          (이 흐름 밖)

 L1226  persistence = rel 의 relpersistence, 없으면 인자로 받은 값

 L1231  RBM_ZERO_AND_LOCK / RBM_ZERO_AND_CLEANUP_LOCK
          L1236  [04] PinBufferForBlock     pin 과 tag 까지만, 읽기 없음
          L1238  ZeroAndLockBuffer          0 으로 채우고 lock

 L1247  flags = READ_BUFFERS_SYNCHRONOUSLY
 L1248  RBM_ZERO_ON_ERROR 면 READ_BUFFERS_ZERO_ON_ERROR
 L1250-L1254  operation 을 스택에 채운다 (smgr, rel, persistence, forknum, strategy)
 L1255  [03] StartReadBuffer(&operation, &buffer, blockNum, flags)
          false  hit. buffer 는 이미 유효하다
          true   L1259 [11] WaitReadBuffers(&operation)
 L1261  return buffer
```

`READ_BUFFERS_SYNCHRONOUSLY` 를 켜는 이유는 주석 L1242-L1246 에 있다. 시작하자마자 기다릴 것이라 비동기로 돌려 봐야 분배 비용만 늘기 때문이다. 이 플래그는 [10] `AsyncReadBuffers` 에서 `PGAIO_HF_SYNCHRONOUS` 로 바뀌어 AIO 계층에 전달되고, AIO 계층은 이 플래그를 보면 `io_method` 와 상관없이 이 backend 안에서 바로 읽는다(`storage/aio/aio.c` L493-L494). `io_method` 가 `worker` 나 `io_uring` 이면 그래서 [03] 의 `AsyncReadBuffers`(bufmgr.c L1437)에서 이미 I/O 가 끝나고, [11] 은 끝난 결과를 확인만 한다. `io_method = sync` 면 [03] 은 I/O 를 시작하지 않고(L1441-L1466), [11] 이 루프 안에서 `AsyncReadBuffers`(L1747)를 불러 같은 동기 읽기를 한다.

```text
 같은 API, 두 사용자

 ReadBuffer_common (이 함수)
   블록       1개
   시작       StartReadBuffer
   대기       바로 WaitReadBuffers
   플래그     READ_BUFFERS_SYNCHRONOUSLY
   호출자     ReadBuffer, ReadBufferBI

 read_stream (storage/aio/read_stream.c)
   블록       여러 개를 미리 요청 (look-ahead)
   시작       StartReadBuffers (L356), 빠른 경로는 StartReadBuffer (L855)
   대기       버퍼를 돌려줄 차례가 되어서야 WaitReadBuffers (L931)
   플래그     없음 -> I/O 가 진짜로 겹친다
   호출자     heap seqscan 등 (heapam.c L1221, L1232 의 read_stream_begin_relation)
```

## 결과가 쓰이는 곳

```text
 operation (스택 변수)
      --> StartReadBuffer 와 WaitReadBuffers 사이에서만 산다
      --> io_wref, io_return 에 AIO 핸들 참조와 결과가 담긴다
 buffer
      --> [01] 이 그대로 호출자에게 돌려준다
```

## 다루지 않는 것

`ExtendBufferedRel` 의 확장 경로(확장 lock, `smgrzeroextend`), `ZeroAndLockBuffer` 의 내부, `RELATION_IS_OTHER_TEMP` 의 판정 매크로는 요약만 했다.
