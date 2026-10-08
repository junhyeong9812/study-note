# 행 쓰기와 WAL 기록

상위: [PostgreSQL 아키텍처 지도](../../README.md)

executor 가 `table_tuple_insert` 로 넘긴 행 하나가 **힙 페이지에 들어가고, 그 변경을 설명하는 WAL 레코드가 공유 WAL 버퍼에 복사되기까지**의 흐름이다. 핵심은 크리티컬 섹션 안의 네 줄 순서다. 페이지에 행을 넣고(`RelationPutHeapTuple`), 버퍼를 더럽다고 표시하고(`MarkBufferDirty`), WAL 레코드를 넣고(`XLogInsert`), 받은 LSN 을 페이지에 찍는다(`PageSetLSN`). 이 사이에 ERROR 가 나면 공유 버퍼에 기록 안 된 변경이 남으므로 PANIC 으로 올라간다. WAL 레코드는 백엔드 지역 메모리에서 조립되고(체크포인트 뒤 첫 변경이면 페이지 전체 이미지를 싣는다), 공유 WAL 버퍼에 넣는 일은 두 단계다. spinlock 아래에서 바이트 위치만 예약하고, 복사는 여덟 개의 WAL 삽입 잠금 중 하나를 쥐고 여러 백엔드가 동시에 한다. 이 흐름에서 WAL 은 아직 메모리에 있다. 디스크에 닿게 하는 `XLogFlush` 는 커밋이나 더러운 페이지 쓰기가 부르며, 이 흐름의 마지막 함수로 함께 둔다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 backend 하나 (호출자: [executor] ExecInsert -> table_tuple_insert, nodeModifyTable.c L1234)
 ------------------------------------------------------------------
 [01] heapam_tuple_insert                              heapam_handler.c L244
      +-- ExecFetchSlotHeapTuple                       L248  슬롯 -> HeapTuple
      +-- [02] heap_insert                             L255   (heapam.c L2081)
      |     +-- GetCurrentTransactionId                L2084  아직 없으면 AssignTransactionId (xact.c L459)
      |     +-- [03] heap_prepare_insert               L2104  xmin, cmin, xmax 를 헤더에. 크면 TOAST
      |     +-- [04] RelationGetBufferForTuple         L2110  빈 자리 있는 페이지를 pin + 배타 잠금
      |     |     +-- 마지막 삽입 블록 -> FSM -> 마지막 블록 -> 확장   hio.c L573-L767
      |     +-- CheckForSerializableConflictIn         L2131
      |     +-- START_CRIT_SECTION                     L2141  ---- 여기부터 ERROR = PANIC ----
      |     |   +-- [05] RelationPutHeapTuple          L2143  PageAddItem, t_self = (블록, 줄)
      |     |   +-- all-visible 이면 VM 비트와 페이지 플래그 지움  L2146-L2155
      |     |   +-- MarkBufferDirty                    L2168
      |     |   +-- RelationNeedsWAL 이면              L2171
      |     |   |     XLogBeginInsert                  L2221
      |     |   |     XLogRegisterData(xl_heap_insert) L2222  주 데이터 3바이트
      |     |   |     XLogRegisterBuffer(0, buffer)    L2233  이 페이지를 바꿨다
      |     |   |     XLogRegisterBufData(헤더, 본문)  L2235, L2238
      |     |   |     [06] XLogInsert(RM_HEAP_ID, info) L2248
      |     |   |       +-- GetFullPageWriteInfo       xloginsert.c L518
      |     |   |       +-- [07] XLogRecordAssemble    L520  헤더 조립, FPI 판정, CRC
      |     |   |       +-- [08] XLogInsertRecord      L523  (xlog.c L748)
      |     |   |       |     +-- WALInsertLockAcquire        L823  8개 중 하나
      |     |   |       |     +-- FPI 가 새로 필요해졌으면 InvalidXLogRecPtr  L848-L858
      |     |   |       |     +-- [09] ReserveXLogInsertLocation   L865  spinlock 아래 위치 예약
      |     |   |       |     +-- xl_prev 넣고 헤더 CRC 마무리      L913-L916
      |     |   |       |     +-- CopyXLogRecordToWAL              L922  WAL 버퍼에 복사
      |     |   |       |     +-- WALInsertLockRelease             L950
      |     |   |       +-- InvalidXLogRecPtr 면 다시 조립  L525
      |     |   +-- PageSetLSN(page, recptr)           L2250  페이지 LSN = 레코드 끝 위치
      |     +-- END_CRIT_SECTION                       L2256  ---------------------------------
      |     +-- UnlockReleaseBuffer                    L2258
      +-- ItemPointerCopy(t_self -> slot->tts_tid)     L256   --> 인덱스 삽입이 쓴다
 ------------------------------------------------------------------
 나중에, 다른 자리에서
 [10] XLogFlush(lsn)                                   xlog.c L2780
      커밋     RecordTransactionCommit -> XLogFlush(XactLastRecEnd)   access/transam/xact.c L1502
      페이지   FlushBuffer -> XLogFlush(page LSN)                     storage/buffer/bufmgr.c L4371
      +-- WaitXLogInsertionsToFinish                   L2845  복사 중인 삽입을 기다린다
      +-- LWLockAcquireOrWait(WALWriteLock)            L2854  못 잡으면 남이 flush 했는지 다시 본다
      +-- XLogWrite -> pg_pwrite, issue_xlog_fsync     L2903
```

크리티컬 섹션 안의 순서는 소스 README 의 규칙을 그대로 따른다(access/transam/README L439-L469). 버퍼 잠금 -> 크리티컬 섹션 -> 변경 -> `MarkBufferDirty` -> WAL 삽입과 `PageSetLSN` -> 크리티컬 섹션 끝 -> 잠금 해제다.

```text
 heap_insert 의 크리티컬 섹션 (heapam.c), README 단계 번호와 짝

 README  줄      함수                         이 자리에 있는 이유
 1       L2110   RelationGetBufferForTuple    pin + 배타 잠금. 다른 백엔드가 반쯤 바뀐 페이지를 못 본다
 2       L2141   START_CRIT_SECTION           이후 ERROR 는 PANIC. 기록 안 된 변경이 버퍼에 남으므로
 3       L2143   RelationPutHeapTuple         공간 검사는 [04] 가 크리티컬 섹션 밖에서 이미 끝냈다
 4       L2168   MarkBufferDirty              WAL 삽입보다 먼저 (README L450-L451)
 5       L2248   XLogInsert                   레코드 끝 위치(LSN)를 받는다
 5       L2250   PageSetLSN                   이 페이지를 쓰기 전에 WAL 이 이 LSN 까지 flush 돼야 한다
 6       L2256   END_CRIT_SECTION
 7       L2258   UnlockReleaseBuffer
```

페이지와 WAL 은 LSN 하나로 묶인다. 페이지 LSN 은 "이 페이지에 반영된 마지막 WAL 레코드의 끝"이고, 버퍼 관리자는 페이지를 디스크에 쓰기 전에 WAL 을 그 위치까지 flush 한다(WAL-before-data).

```text
 한 번의 heap_insert 가 남기는 것 (두 메모리, 아직 디스크는 아무것도 없다)

 shared buffers                                WAL 버퍼 (XLogCtl->pages)
 +---------------------------------+           ... | 앞 레코드 | 이 레코드 63바이트 + 패딩 1 | ...
 | t2 블록 7                        |                          ^StartPos               ^EndPos
 | pd_lsn = EndPos  <---------------------------------------------------------------+
 | 줄 3: (xmin = 이 XID, cmin = cid) |
 | BM_DIRTY                         |
 +---------------------------------+

 디스크로 가는 순서
   WAL    [10] XLogFlush(EndPos 이상) -> XLogWrite -> write + fsync
   페이지 체크포인트나 버퍼 교체가 FlushBuffer -> XLogFlush(pd_lsn) 먼저 -> smgrwrite
```

레코드 크기 63바이트는 아래 [07] 의 계산(정수 열 두 개짜리 행, FPI 없음)이다.

## 어디에서 쓰이는가

```text
 [executor]            ExecInsert 가 table_tuple_insert 로 이 흐름의 [01] 을 부른다
 COPY FROM             table_multi_insert -> heap_multi_insert (commands/copyfrom.c L554)
 카탈로그 쓰기         CatalogTupleInsert -> simple_heap_insert -> heap_insert
                       (catalog/indexing.c L241, access/heap/heapam.c L2772)
 [nbtree 삽입과 분할]  [01] 이 slot->tts_tid 에 넣은 TID 를 인덱스 항목이 가리킨다
                       인덱스도 같은 순서(크리티컬 섹션, XLogInsert, PageSetLSN)로 자기 WAL 을 쓴다
 [커밋]                RecordTransactionCommit 이 commit 레코드를 XLogInsert 하고 [10] XLogFlush
 [버퍼 관리]           FlushBuffer 가 페이지를 쓰기 전에 [10] XLogFlush(page LSN)
 [WAL redo]            여기서 쓴 XLOG_HEAP_INSERT 를 heap_xlog_insert 가 되감는다
```

다음 흐름은 [nbtree 삽입과 분할](../nbtree-insert/README.md), 그리고 [커밋](../commit/README.md)이다.

## db-engine 에서는

같은 문제(변경을 로그에 먼저 남기고 순번을 매기기)를 db-engine 은 "로그만 쓰고 페이지는 커밋 뒤에 바꾸는" deferred-apply 로 풀었다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 페이지와 로그의 순서
   PostgreSQL  페이지를 먼저 바꾸고(메모리) 같은 크리티컬 섹션에서 WAL 을 넣는다
               페이지는 dirty 로 남고, 쓸 때 XLogFlush(page LSN) 가 WAL-before-data 를 지킨다
   db-engine   Transaction.insert 는 InsertRow 를 append 만 한다. heap 은 commit 뒤에 바꾼다

 로그 레코드
   PostgreSQL  rmgr 별 이진 레코드. 헤더 24바이트 + 블록 참조 + 주 데이터, CRC32C
               체크포인트 뒤 첫 변경이면 페이지 전체 이미지(FPI)를 싣는다 (torn page 대비)
   db-engine   LogRecord (BeginTx / InsertRow / CommitTx / AbortTx / Checkpoint), 길이 접두사

 순번 (LSN)
   PostgreSQL  WAL 바이트 위치. spinlock 아래 CurrBytePos += size 로 예약
   db-engine   레코드 개수. append 가 nextLsn 을 1 올린다

 동시 쓰기
   PostgreSQL  위치 예약만 직렬, 복사는 WAL 삽입 잠금 8개로 병렬
   db-engine   file.seek(file.length()) 후 write. 동시성 장치 없음

 내구성
   PostgreSQL  XLogFlush 가 WALWriteLock 아래 write + fsync, 여러 백엔드의 요청을 한 번에
   db-engine   commit 이 CommitTx 를 append 한 뒤 logManager.sync()

 되돌리기
   PostgreSQL  abort 해도 힙 행은 남고, xmin 이 abort 된 행이라 보이지 않는다 (vacuum 이 치운다)
   db-engine   heap 을 건드리지 않았으므로 되돌릴 것이 없다 (undo 없음)
```

db-engine 은 heap 을 커밋 뒤에만 바꾸므로 "로그보다 페이지가 먼저 디스크에 간다"는 상황이 생기지 않는다. PostgreSQL 은 페이지를 먼저 바꾸므로 페이지 LSN 과 `FlushBuffer` 의 `XLogFlush` 로 그 규칙을 따로 지킨다. 페이지 전체 이미지(FPI)도 db-engine 에는 없다. db-engine 의 레코드는 페이지가 아니라 행을 다시 넣는 논리 레코드라 찢어진 페이지 문제를 다루지 않는다. 챕터: [06-01-table-seqscan](../../../../../project/db-engine/06-01-table-seqscan/), [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/).

## 단계

1. [heapam_tuple_insert](01_heapam_tuple_insert/README.md)가 슬롯을 `HeapTuple` 로 바꿔 `heap_insert` 에 넘기고, 받은 TID 를 슬롯에 적는다.
2. [heap_insert](02_heap_insert/README.md)가 페이지를 구하고, 크리티컬 섹션 안에서 행을 넣고 WAL 레코드를 쓴다.
3. [heap_prepare_insert](03_heap_prepare_insert/README.md)가 튜플 헤더에 xmin, cmin 을 찍고 필요하면 TOAST 로 줄인다.
4. [RelationGetBufferForTuple](04_RelationGetBufferForTuple/README.md)이 빈 자리가 있는 페이지를 찾아 배타 잠금으로 돌려준다.
5. [RelationPutHeapTuple](05_RelationPutHeapTuple/README.md)이 페이지에 행을 붙이고 위치를 `t_self` 와 `t_ctid` 에 적는다.
6. [XLogInsert](06_XLogInsert/README.md)가 등록된 데이터로 레코드를 조립하고 삽입하며, 조건이 바뀌면 다시 조립한다.
7. [XLogRecordAssemble](07_XLogRecordAssemble/README.md)이 블록마다 페이지 이미지가 필요한지 정하고 헤더와 CRC 를 만든다.
8. [XLogInsertRecord](08_XLogInsertRecord/README.md)가 WAL 삽입 잠금을 쥐고 위치를 예약해 WAL 버퍼에 복사한다.
9. [ReserveXLogInsertLocation](09_ReserveXLogInsertLocation/README.md)이 spinlock 아래에서 바이트 위치를 늘려 시작과 끝, 이전 레코드 위치를 정한다.
10. [XLogFlush](10_XLogFlush/README.md)가 주어진 위치까지 WAL 이 디스크에 닿게 하고, 기다리는 다른 백엔드 몫까지 한 번에 쓴다.

## 결과가 쓰이는 곳

```text
 힙 페이지의 새 행 (xmin = 이 XID)
      --> 커밋 전에는 다른 스냅샷에 안 보인다 --> [MVCC 가시성과 스냅샷]
      --> slot->tts_tid --> [nbtree 삽입과 분할] 의 인덱스 항목
 페이지 LSN (pd_lsn)
      --> [버퍼 관리] FlushBuffer 의 XLogFlush(recptr)
      --> 다음 XLogRecordAssemble 이 "체크포인트 뒤 첫 변경인가" 를 볼 때 RedoRecPtr 와 비교
 WAL 레코드 (XLOG_HEAP_INSERT)
      --> [WAL redo] heap_xlog_insert, [스트리밍 복제] walsender
 XactLastRecEnd (= 레코드 끝)
      --> [커밋] 이 commit 레코드 뒤 XLogFlush 로 기다리는 위치
```

## 다루지 않는 것

TOAST 의 세부(`heap_toast_insert_or_update`), 여러 행을 한 레코드로 쓰는 `heap_multi_insert`, `INSERT ... ON CONFLICT` 의 추측 삽입 토큰, 논리 디코딩용 정보(`log_heap_new_cid`, `XLH_INSERT_CONTAINS_NEW_TUPLE`), visibility map 비트의 의미, FSM 의 구조, 릴레이션 확장(`RelationAddBlocks`), WAL 버퍼 페이지 교체(`AdvanceXLInsertBuffer`, `GetXLogBuffer`), WAL 압축(`wal_compression`), 비동기 커밋과 WAL writer, `XLogWrite` 의 세그먼트 전환은 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 heapam_tuple_insert](01_heapam_tuple_insert/README.md)
- [02 heap_insert](02_heap_insert/README.md)
- [03 heap_prepare_insert](03_heap_prepare_insert/README.md)
- [04 RelationGetBufferForTuple](04_RelationGetBufferForTuple/README.md)
- [05 RelationPutHeapTuple](05_RelationPutHeapTuple/README.md)
- [06 XLogInsert](06_XLogInsert/README.md)
- [07 XLogRecordAssemble](07_XLogRecordAssemble/README.md)
- [08 XLogInsertRecord](08_XLogInsertRecord/README.md)
- [09 ReserveXLogInsertLocation](09_ReserveXLogInsertLocation/README.md)
- [10 XLogFlush](10_XLogFlush/README.md)
