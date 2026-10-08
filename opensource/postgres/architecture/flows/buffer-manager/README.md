# 버퍼 관리

상위: [PostgreSQL 아키텍처 지도](../../README.md)

backend 가 "이 릴레이션의 이 블록"을 달라고 할 때 **shared buffers 안에서 그 블록을 찾아 pin 을 걸어 돌려주고, 없으면 자리 하나를 비워 디스크에서 읽어 오는** 흐름이다. 찾는 일은 `BufferTag`(테이블스페이스, DB, 릴레이션, fork, 블록 번호) 해시 테이블 한 번이고, 자리를 비우는 일은 clock-sweep 이 `usage_count` 를 깎으며 고른 희생자를 내쫓는 것이다. 희생자가 더러우면 내쫓기 전에 그 페이지의 LSN 까지 WAL 을 먼저 flush 한다(WAL-before-data). PG18 에서는 읽기 경로가 `StartReadBuffer` 와 `WaitReadBuffers` 둘로 갈라졌다. 앞쪽이 pin 과 I/O 시작까지, 뒤쪽이 완료 대기까지 맡고, 그 사이를 `io_method`(`sync`, `worker`, `io_uring`)가 채운다. 흐름은 pin 된 `Buffer` 번호를 돌려주는 데서 끝나고, 페이지 내용을 읽거나 바꾸려면 호출자가 따로 `LockBuffer` 로 content lock 을 잡는다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 backend 하나 (호출자 예: heap_fetch, _bt_getbuf, ReadBufferBI)
 ------------------------------------------------------------------
 [01] ReadBufferExtended                                bufmgr.c L805
      +-- [02] ReadBuffer_common                        L815
            +-- 다른 세션의 임시 테이블이면 ERROR       L1201
            +-- P_NEW 면 ExtendBufferedRel 로 확장      L1223
            +-- RBM_ZERO_AND_LOCK 류면 pin 만 하고 0 채움  L1236-L1238
            +-- flags = READ_BUFFERS_SYNCHRONOUSLY      L1247  바로 기다릴 것이라 알린다
            +-- [03] StartReadBuffer -> StartReadBuffersImpl   L1255, L1525
            |     +-- [04] PinBufferForBlock            L1328
            |     |     +-- [05] BufferAlloc            L1145
            |     |           +-- BufTableLookup (분할 lock 공유)  L2035
            |     |           +-- 있으면 [06] PinBuffer            L2048  refcount+1, usage_count+1
            |     |           +-- 없으면 [07] GetVictimBuffer      L2079
            |     |           |     +-- [08] StrategyGetBuffer    L2375  ring -> freelist -> clock-sweep
            |     |           |     +-- 더러우면 [09] FlushBuffer  L2453
            |     |           |     |     +-- XLogFlush(page LSN)  L4371  WAL 먼저
            |     |           |     |     +-- smgrwrite            L4393  그 다음 데이터
            |     |           |     +-- InvalidateVictimBuffer      L2488  옛 tag 를 해시에서 지운다
            |     |           +-- BufTableInsert (분할 lock 배타)  L2088
            |     |           +-- tag 교체, BM_TAG_VALID           L2145, L2153
            |     +-- 첫 블록이 이미 유효하면 false         L1362  I/O 없음 (hit)
            |     +-- io_method != sync 면 [10] AsyncReadBuffers  L1437  여기서 I/O 시작
            +-- true 면 [11] WaitReadBuffers           L1259
                  +-- pgaio_wref_wait                   L1706  완료를 기다린다
                  +-- ProcessReadBuffersResult          L1724  부분 읽기면 L1747 에서 다시 시작
 ------------------------------------------------------------------
 돌려받은 Buffer 로 호출자가 LockBuffer(SHARE | EXCLUSIVE)        bufmgr.c L5623

 [08] 의 줄은 storage/buffer/freelist.c, 나머지는 storage/buffer/bufmgr.c 의 줄이다
```

버퍼 하나의 상태는 32비트 정수 하나(`BufferDesc.state`)에 모여 있다. pin 수, `usage_count`, 플래그를 한 번의 CAS 로 같이 바꾸려고 묶었다(buf_internals.h L32-L41 주석).

```text
 BufferDesc.state (include/storage/buf_internals.h L44-L77)

  31                     22 21    18 17                          0
 +-------------------------+--------+-----------------------------+
 | flags 10비트            | usage  | refcount 18비트             |
 |                         | 4비트  |  (pin 한 backend 수)        |
 +-------------------------+--------+-----------------------------+
 BUF_REFCOUNT_ONE   = 1          BUF_USAGECOUNT_ONE = 1 << 18
 BM_MAX_USAGE_COUNT = 5 (L87)

 flag 비트                 뜻
 22  BM_LOCKED             헤더 spinlock (별도 slock_t 가 아니라 이 비트다)
 23  BM_DIRTY              써야 한다
 24  BM_VALID              내용이 유효하다
 25  BM_TAG_VALID          tag 가 붙어 있고 해시 테이블에 있다
 26  BM_IO_IN_PROGRESS     읽기나 쓰기가 진행 중
 27  BM_IO_ERROR           직전 I/O 실패
 28  BM_JUST_DIRTIED       쓰는 도중에 다시 더러워졌다
 29  BM_PIN_COUNT_WAITER   cleanup lock 대기자가 있다
 30  BM_CHECKPOINT_NEEDED  체크포인트가 써야 한다
 31  BM_PERMANENT          WAL 대상 (unlogged 가 아니거나 init fork)
```

한 블록을 찾는 길은 hit, miss, 경합 셋으로 갈린다. 해시 테이블은 128개 분할(`NUM_BUFFER_PARTITIONS`, lwlock.h L93)로 나뉘어 있고, 분할 lock 은 조회에 공유, 삽입에 배타로 잡는다.

```text
 BufferTag -> buffer id (buf_table.c 의 SharedBufHash)

 tag = {spcOid, dbOid, relNumber, forkNum, blockNum}
 hash = BufTableHashCode(tag)           분할 = hash % 128

  hit       공유 lock -> Lookup 성공 -> PinBuffer -> lock 해제     디스크 I/O 없음
  miss      공유 lock -> Lookup 실패 -> lock 해제
            -> GetVictimBuffer (lock 없이, 필요하면 쓰기까지)
            -> 배타 lock -> Insert 성공 -> tag 교체 -> lock 해제 -> 읽기 시작
  경합      miss 와 같지만 Insert 가 "이미 있다"를 돌려준다
            -> 방금 얻은 희생자를 freelist 에 돌려주고 남의 버퍼를 pin (BufferAlloc L2104-L2116)
```

## 어디에서 쓰이는가

```text
 [행 쓰기와 WAL 기록]   RelationGetBufferForTuple -> ReadBufferBI -> ReadBufferExtended
                        (access/heap/hio.c L95, L119)
 [MVCC 가시성과 스냅샷] heap seqscan 은 read_stream 으로 읽는다
                        heap_fetch_next_buffer -> read_stream_next_buffer (heapam.c L679)
                        -> StartReadBuffer(s) / WaitReadBuffers (read_stream.c L356, L855, L931)
                        index scan 의 heap 방문은 ReleaseAndReadBuffer (heapam_handler.c L133)
 [nbtree 삽입과 분할]   _bt_getbuf -> ReadBuffer (access/nbtree/nbtpage.c L852)
 [체크포인트]           SyncOneBuffer -> FlushBuffer (bufmgr.c L3989)  같은 WAL-before-data 규칙
```

다음에 읽을 흐름은 이 버퍼 위에서 튜플을 고르는 [MVCC 가시성과 스냅샷](../mvcc-visibility/README.md)이다. 더러운 버퍼를 희생자 선택과 따로 내려 쓰는 쪽은 [체크포인트](../checkpoint/README.md)다.

## db-engine 에서는

같은 세 결정(무엇을 내보낼지, 내보내도 되는지, 내보내기 전에 써야 하는지)을 db-engine 의 `BufferPool` 은 `LinkedHashMap` 하나로 푼다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 찾기
   PostgreSQL  BufferTag 해시, 128개 분할 LWLock
   db-engine   LinkedHashMap<PageId, Page>(capacity, 0.75f, true) 하나, lock 없음

 교체 정책
   PostgreSQL  clock-sweep. pin 될 때 usage_count+1 (최대 5), 시계바늘이 지나며 -1, 0 이면 희생자
               대량 읽기, VACUUM 은 작은 ring 안에서만 돈다 (BufferAccessStrategy)
   db-engine   access-order LRU. evictOne 이 iteration 첫 unpinned page 를 고른다

 내보내도 되는가
   PostgreSQL  refcount == 0 (공유 state 의 18비트) + backend 별 PrivateRefCount
   db-engine   Page.pinCount == 0. 전부 pin 이면 AllPagesPinned
               PostgreSQL 은 pin 된 버퍼만 연달아 NBuffers 개(한 바퀴) 만나면 "no unpinned buffers available"

 내보내기 전에
   PostgreSQL  BM_DIRTY 면 XLogFlush(page LSN) -> smgrwrite. WAL 이 먼저 간다
   db-engine   isDirty 면 pagedFile.writePage. WAL 순서 검사는 없다

 읽기
   PostgreSQL  StartReadBuffer 로 pin 과 I/O 시작, WaitReadBuffers 로 완료 대기 (AIO)
   db-engine   fetchPage 안에서 pagedFile.readPage 를 동기로 부른다
```

db-engine 의 `BufferPool` 은 동기화 없이 쓰여 있어(테스트도 단일 스레드다) pin 이 객체 필드 하나로 끝나지만, PostgreSQL 은 여러 프로세스가 같은 버퍼를 보므로 pin 과 tag 교체를 CAS 와 분할 lock 으로 쪼개야 했다. db-engine 은 페이지에 `pageLSN` 을 두지 않는다고 [08-02-lsn-checkpoint](../../../../../project/db-engine/08-02-lsn-checkpoint/) 가 적어 두었다. 그래서 희생자를 쓸 때 "이 페이지를 바꾼 WAL 이 이미 디스크에 있는가"를 물을 근거가 없고, PostgreSQL 의 `FlushBuffer` L4370-L4371 에 해당하는 줄이 없다. 챕터: [02-01-page-pagedfile](../../../../../project/db-engine/02-01-page-pagedfile/), [02-02-buffer-pool](../../../../../project/db-engine/02-02-buffer-pool/).

## 단계

1. [ReadBufferExtended](01_ReadBufferExtended/README.md)가 진입점이다. `ReadBuffer_common` 으로 넘기기만 한다.
2. [ReadBuffer_common](02_ReadBuffer_common/README.md)이 모드를 가르고 `StartReadBuffer` 와 `WaitReadBuffers` 를 차례로 부른다.
3. [StartReadBuffersImpl](03_StartReadBuffersImpl/README.md)이 블록마다 pin 을 걸고, hit 이면 바로 끝내고, 아니면 I/O 를 시작한다.
4. [PinBufferForBlock](04_PinBufferForBlock/README.md)이 임시 테이블과 공유 버퍼를 가르고 hit 통계를 센다.
5. [BufferAlloc](05_BufferAlloc/README.md)이 tag 해시를 조회하고, 없으면 희생자를 얻어 새 tag 를 단다.
6. [PinBuffer](06_PinBuffer/README.md)가 CAS 로 refcount 와 usage_count 를 올린다. pin 과 content lock(`LockBuffer`)의 차이도 여기서 본다.
7. [GetVictimBuffer](07_GetVictimBuffer/README.md)가 후보를 받아 더러우면 쓰고, 옛 tag 를 지운다.
8. [StrategyGetBuffer](08_StrategyGetBuffer/README.md)가 ring, freelist, clock-sweep 순서로 후보를 고른다.
9. [FlushBuffer](09_FlushBuffer/README.md)가 WAL 을 먼저 flush 하고 페이지를 쓴다.
10. [AsyncReadBuffers](10_AsyncReadBuffers/README.md)가 이웃 블록을 묶어 AIO 읽기를 하나 시작한다.
11. [WaitReadBuffers](11_WaitReadBuffers/README.md)가 완료를 기다리고, 부분 읽기면 남은 블록을 다시 시작한다.

## 결과가 쓰이는 곳

```text
 pin 된 Buffer 번호 (1 부터, 임시 테이블은 음수)
      --> BufferGetPage 로 페이지 포인터를 얻는다
      --> 내용을 보려면 LockBuffer(SHARE), 바꾸려면 LockBuffer(EXCLUSIVE)
      --> 바꿨으면 MarkBufferDirty 가 BM_DIRTY | BM_JUST_DIRTIED 를 켠다 (bufmgr.c L3000)
      --> 다 쓰면 ReleaseBuffer -> UnpinBuffer 가 refcount 를 내린다

 usage_count
      --> 다음 clock-sweep 이 이 버퍼를 몇 바퀴 더 살려 둘지 정한다

 BM_DIRTY 버퍼
      --> 희생자로 뽑히면 [09] FlushBuffer
      --> 체크포인트의 BufferSync, bgwriter 의 BgBufferSync 가 미리 내려 쓴다
```

## 다루지 않는 것

임시 테이블의 local buffer(`localbuf.c`, `LocalBufferAlloc`), 릴레이션 확장(`ExtendBufferedRelBy`, `ExtendBufferedRelTo`), `RBM_ZERO_AND_LOCK` 의 `ZeroAndLockBuffer`, cleanup lock(`LockBufferForCleanup`), AIO 하위 계층(`pgaio_io_acquire`, IO worker 프로세스, io_uring 제출 경로, `md.c` 의 `mdstartreadv`), `read_stream.c` 의 look-ahead 거리 조절, bgwriter 의 `BgBufferSync` 와 writeback 제어(`ScheduleBufferTagForWriteback`), 체크섬 검증(`PageIsVerified`) 내부는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 ReadBufferExtended](01_ReadBufferExtended/README.md)
- [02 ReadBuffer_common](02_ReadBuffer_common/README.md)
- [03 StartReadBuffersImpl](03_StartReadBuffersImpl/README.md)
- [04 PinBufferForBlock](04_PinBufferForBlock/README.md)
- [05 BufferAlloc](05_BufferAlloc/README.md)
- [06 PinBuffer](06_PinBuffer/README.md)
- [07 GetVictimBuffer](07_GetVictimBuffer/README.md)
- [08 StrategyGetBuffer](08_StrategyGetBuffer/README.md)
- [09 FlushBuffer](09_FlushBuffer/README.md)
- [10 AsyncReadBuffers](10_AsyncReadBuffers/README.md)
- [11 WaitReadBuffers](11_WaitReadBuffers/README.md)
