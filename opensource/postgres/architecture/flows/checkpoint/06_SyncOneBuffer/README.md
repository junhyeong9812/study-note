# SyncOneBuffer

상위: [체크포인트](../README.md)

**버퍼 하나가 쓸 만한지 헤더만 보고 판단한 뒤, pin 과 share lock 을 잡아 `FlushBuffer` 로 쓰는 함수다.** checkpointer 의 `BufferSync` 와 bgwriter 의 `BgBufferSync` 가 함께 쓴다. 차이는 `skip_recently_used` 하나다. 체크포인트는 `false` 로 불러 최근에 쓰인 버퍼도 쓰고, bgwriter 는 `true` 로 불러 곧 희생자가 될 버퍼(pin 0, usage_count 0)만 쓴다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L3940-L4004 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L3940-L4004))

## 실제 코드

```c
// buffer/bufmgr.c L3940-L4004
static int
SyncOneBuffer(int buf_id, bool skip_recently_used, WritebackContext *wb_context)
{
	BufferDesc *bufHdr = GetBufferDescriptor(buf_id);
	int			result = 0;
	uint32		buf_state;
	BufferTag	tag;

	/* Make sure we can handle the pin */
	ReservePrivateRefCountEntry();
	ResourceOwnerEnlarge(CurrentResourceOwner);

	/*
	 * Check whether buffer needs writing.
	 *
	 * We can make this check without taking the buffer content lock so long
	 * as we mark pages dirty in access methods *before* logging changes with
	 * XLogInsert(): if someone marks the buffer dirty just after our check we
	 * don't worry because our checkpoint.redo points before log record for
	 * upcoming changes and so we are not required to write such dirty buffer.
	 */
	buf_state = LockBufHdr(bufHdr);

	if (BUF_STATE_GET_REFCOUNT(buf_state) == 0 &&
		BUF_STATE_GET_USAGECOUNT(buf_state) == 0)
	{
		result |= BUF_REUSABLE;
	}
	else if (skip_recently_used)
	{
		/* Caller told us not to write recently-used buffers */
		UnlockBufHdr(bufHdr, buf_state);
		return result;
	}

	if (!(buf_state & BM_VALID) || !(buf_state & BM_DIRTY))
	{
		/* It's clean, so nothing to do */
		UnlockBufHdr(bufHdr, buf_state);
		return result;
	}

	/*
	 * Pin it, share-lock it, write it.  (FlushBuffer will do nothing if the
	 * buffer is clean by the time we've locked it.)
	 */
	PinBuffer_Locked(bufHdr);
	LWLockAcquire(BufferDescriptorGetContentLock(bufHdr), LW_SHARED);

	FlushBuffer(bufHdr, NULL, IOOBJECT_RELATION, IOCONTEXT_NORMAL);

	LWLockRelease(BufferDescriptorGetContentLock(bufHdr));

	tag = bufHdr->tag;

	UnpinBuffer(bufHdr);

	/*
	 * SyncOneBuffer() is only called by checkpointer and bgwriter, so
	 * IOContext will always be IOCONTEXT_NORMAL.
	 */
	ScheduleBufferTagForWriteback(wb_context, IOCONTEXT_NORMAL, &tag);

	return result | BUF_WRITTEN;
}
```

## 동작 흐름

```text
 SyncOneBuffer(buf_id, skip_recently_used, wb_context)

 L3949  ReservePrivateRefCountEntry           pin 할 자리를 미리 확보
 L3961  LockBufHdr                            헤더 spinlock 만. content lock 은 아직 아님
 L3963  refcount == 0 && usage_count == 0 ?   -> result |= BUF_REUSABLE
 L3968  아니고 skip_recently_used 면 여기서 return    (bgwriter 경로)
 L3975  BM_VALID 가 없거나 BM_DIRTY 가 없으면 return  깨끗하다
 L3986  PinBuffer_Locked                      헤더 lock 을 쥔 채 pin, 그리고 헤더 lock 해제
 L3987  content lock SHARE
 L3989  FlushBuffer(buf, NULL, IOOBJECT_RELATION, IOCONTEXT_NORMAL)
          XLogFlush(page LSN) -> smgrwrite -> TerminateBufferIO
 L3991  content lock 해제
 L3995  UnpinBuffer
 L4001  ScheduleBufferTagForWriteback         checkpoint_flush_after 단위로 OS 에 writeback 힌트
 L4003  return result | BUF_WRITTEN
```

호출자 둘이 같은 함수를 다르게 쓴다.

```text
 caller              skip_recently_used   result bits                 쓰는 버퍼
 BufferSync L3577    false                BUF_WRITTEN                 BM_DIRTY 면 전부
 BgBufferSync L3865  true                 BUF_REUSABLE, BUF_WRITTEN   pin 0, usage_count 0 인 것만
```

L3975 에서 content lock 없이 `BM_DIRTY` 만 보고 "깨끗하다"고 판단해도 되는 이유는 주석 L3955-L3959 에 있다. 페이지를 고치는 쪽이 `MarkBufferDirty` 를 `XLogInsert` 보다 먼저 부른다는 규칙에 기댄다.

```text
 B = 페이지를 고치는 backend (exclusive content lock), CK = checkpointer

 시각  누가  하는 일
 t1    CK    REDO 레코드 = 0/3D000100
 t2    CK    L3961-L3975  이 버퍼는 BM_DIRTY 아님 -> 깨끗하다고 보고 return
 t3    B     페이지 수정, MarkBufferDirty
 t4    B     XLogInsert -> 레코드는 0/3D0004A8 (REDO 뒤)

 t2 의 판단이 낡았지만 상관없다
 t3 의 변경을 적은 레코드가 REDO 뒤에 있으므로 복구가 그 레코드를 재생한다
 순서가 반대 (XLogInsert 먼저, MarkBufferDirty 나중) 라면 레코드는 REDO 앞, 버퍼는 안 쓰임
 -> 그 변경이 사라질 수 있다. 그래서 규칙이 "dirty 먼저, WAL 나중" 이다
```

## 결과가 쓰이는 곳

```text
 BUF_WRITTEN
      --> [05] BufferSync 의 num_written, buffers_written 통계 (bufmgr.c L3577-L3582)
 BUF_REUSABLE
      --> BgBufferSync 가 "곧 쓸 수 있는 깨끗한 버퍼" 수를 센다
 FlushBuffer 가 남긴 fsync 요청
      --> [08] ProcessSyncRequests
```

## 다루지 않는 것

`FlushBuffer` 내부(WAL-before-data, `BM_JUST_DIRTIED`)는 [버퍼 관리](../../buffer-manager/09_FlushBuffer/README.md)에 있다. `PinBuffer_Locked` 와 `UnpinBuffer` 의 refcount 처리, writeback 힌트(`ScheduleBufferTagForWriteback`)는 요약만 했다.
