# ReadBufferExtended

상위: [버퍼 관리](../README.md)

**버퍼 관리 흐름의 공개 진입점이다.** 릴레이션, fork, 블록 번호, 읽기 모드, 접근 전략을 받아 `ReadBuffer_common` 으로 넘기고, pin 된 `Buffer` 번호를 그대로 돌려준다. 자주 쓰는 `ReadBuffer` 는 이 함수에 `MAIN_FORKNUM`, `RBM_NORMAL`, 전략 없음을 채워 부르는 한 줄짜리다.

## 위치

`src/backend/storage/buffer` / `bufmgr.c` L804-L819 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L804-L819))

## 실제 코드

본체는 한 줄이다. 세 번째 인자 `0` 은 `smgr_persistence` 인데, `rel` 이 있으면 `ReadBuffer_common` 이 `rel->rd_rel->relpersistence` 를 대신 쓴다.

```c
// bufmgr.c L804-L819
inline Buffer
ReadBufferExtended(Relation reln, ForkNumber forkNum, BlockNumber blockNum,
				   ReadBufferMode mode, BufferAccessStrategy strategy)
{
	Buffer		buf;

	/*
	 * Read the buffer, and update pgstat counters to reflect a cache hit or
	 * miss.  The other-session temp-relation check is enforced by
	 * ReadBuffer_common().
	 */
	buf = ReadBuffer_common(reln, RelationGetSmgr(reln), 0,
							forkNum, blockNum, mode, strategy);

	return buf;
}
```

가장 흔한 호출 형태다. 모드와 전략을 기본값으로 채운다.

`src/backend/storage/buffer` / `bufmgr.c` L757-L761 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/buffer/bufmgr.c#L757-L761))

```c
// bufmgr.c L757-L761
Buffer
ReadBuffer(Relation reln, BlockNumber blockNum)
{
	return ReadBufferExtended(reln, MAIN_FORKNUM, blockNum, RBM_NORMAL, NULL);
}
```

모드는 다섯 가지다. 이 흐름은 `RBM_NORMAL` 을 따라간다.

`src/include/storage` / `bufmgr.h` L43-L54 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/bufmgr.h#L43-L54))

```c
// bufmgr.h L43-L54
/* Possible modes for ReadBufferExtended() */
typedef enum
{
	RBM_NORMAL,					/* Normal read */
	RBM_ZERO_AND_LOCK,			/* Don't read from disk, caller will
								 * initialize. Also locks the page. */
	RBM_ZERO_AND_CLEANUP_LOCK,	/* Like RBM_ZERO_AND_LOCK, but locks the page
								 * in "cleanup" mode */
	RBM_ZERO_ON_ERROR,			/* Read, but return an all-zeros page on error */
	RBM_NORMAL_NO_LOG,			/* Don't log page as invalid during WAL
								 * replay; otherwise same as RBM_NORMAL */
} ReadBufferMode;
```

## 동작 흐름

```text
 호출자                                  넘기는 값
 ReadBuffer(rel, blk)            L760    MAIN_FORKNUM, RBM_NORMAL, strategy = NULL
 ReadBufferBI (hio.c L95)                bulk insert 가 아니면 strategy = NULL
 ReadBufferBI (hio.c L119)               bulk insert 면 bistate->strategy (BAS_BULKWRITE ring)
         |
         v
 [01] ReadBufferExtended         L805
         |  RelationGetSmgr(reln)        relcache 가 들고 있는 smgr 핸들
         v
 [02] ReadBuffer_common          L815
         |
         v
 Buffer  (pin 1개를 더 가진 채로 돌아온다)
```

```text
 모드별로 이 흐름에서 갈리는 곳 (모두 [02] 안)

 RBM_NORMAL, RBM_NORMAL_NO_LOG   StartReadBuffer -> 필요하면 WaitReadBuffers
 RBM_ZERO_ON_ERROR               위와 같고 READ_BUFFERS_ZERO_ON_ERROR 플래그만 더한다
                                 페이지 검증이 실패하면 0 으로 채운다
 RBM_ZERO_AND_LOCK               디스크를 읽지 않는다. pin 하고 0 으로 채운 뒤 배타 lock
 RBM_ZERO_AND_CLEANUP_LOCK       위와 같고 cleanup lock
```

## 결과가 쓰이는 곳

```text
 Buffer
      --> 호출자가 LockBuffer 로 content lock 을 잡고 BufferGetPage 로 페이지를 읽는다
      --> 끝나면 ReleaseBuffer 로 pin 을 돌려준다
 pgstat (rel 단위 blks_read / blks_hit)
      --> [04] PinBufferForBlock 이 센다 (주석 L810-L814 가 말하는 "update pgstat counters")
```

## 다루지 않는 것

`ReadBufferWithoutRelcache`(relcache 없이 `RelFileLocator` 로 읽는 경로, WAL redo 가 쓴다), `ExtendBufferedRel` 계열, `RelationGetSmgr` 의 smgr 캐시는 이 흐름 밖이다.
