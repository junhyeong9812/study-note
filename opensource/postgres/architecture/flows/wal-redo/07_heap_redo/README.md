# heap_redo

상위: [WAL redo (복구)](../README.md)

**heap resource manager(`RM_HEAP_ID`)의 `rm_redo` 이고, `xl_info` 의 opcode 3비트로 레코드 종류별 함수에 넘기기만 하는 switch 다.** `xl_info` 의 위 4비트가 heap 몫인데, 그중 3비트가 opcode 이고 남은 1비트(`XLOG_HEAP_INIT_PAGE`)는 "이 페이지를 새로 초기화하라"는 표시다. opcode 가 모자라 prune, freeze, multi-insert 같은 레코드는 두 번째 rmgr `RM_HEAP2_ID` 의 `heap2_redo` 로 갔다(heapam_xlog.h 주석 L48-L52).

## 위치

`src/backend/access/heap` / `heapam_xlog.c` L1306-L1350 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam_xlog.c#L1306-L1350))

## 실제 코드

```c
// heap/heapam_xlog.c L1306-L1350
void
heap_redo(XLogReaderState *record)
{
	uint8		info = XLogRecGetInfo(record) & ~XLR_INFO_MASK;

	/*
	 * These operations don't overwrite MVCC data so no conflict processing is
	 * required. The ones in heap2 rmgr do.
	 */

	switch (info & XLOG_HEAP_OPMASK)
	{
		case XLOG_HEAP_INSERT:
			heap_xlog_insert(record);
			break;
		case XLOG_HEAP_DELETE:
			heap_xlog_delete(record);
			break;
		case XLOG_HEAP_UPDATE:
			heap_xlog_update(record, false);
			break;
		case XLOG_HEAP_TRUNCATE:

			/*
			 * TRUNCATE is a no-op because the actions are already logged as
			 * SMGR WAL records.  TRUNCATE WAL record only exists for logical
			 * decoding.
			 */
			break;
		case XLOG_HEAP_HOT_UPDATE:
			heap_xlog_update(record, true);
			break;
		case XLOG_HEAP_CONFIRM:
			heap_xlog_confirm(record);
			break;
		case XLOG_HEAP_LOCK:
			heap_xlog_lock(record);
			break;
		case XLOG_HEAP_INPLACE:
			heap_xlog_inplace(record);
			break;
		default:
			elog(PANIC, "heap_redo: unknown op code %u", info);
	}
}
```

opcode 와 INIT_PAGE 비트의 정의다.

`src/include/access` / `heapam_xlog.h` L25-L47 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/heapam_xlog.h#L25-L47))

```c
// access/heapam_xlog.h L25-L47


/*
 * WAL record definitions for heapam.c's WAL operations
 *
 * XLOG allows to store some information in high 4 bits of log
 * record xl_info field.  We use 3 for opcode and one for init bit.
 */
#define XLOG_HEAP_INSERT		0x00
#define XLOG_HEAP_DELETE		0x10
#define XLOG_HEAP_UPDATE		0x20
#define XLOG_HEAP_TRUNCATE		0x30
#define XLOG_HEAP_HOT_UPDATE	0x40
#define XLOG_HEAP_CONFIRM		0x50
#define XLOG_HEAP_LOCK			0x60
#define XLOG_HEAP_INPLACE		0x70

#define XLOG_HEAP_OPMASK		0x70
/*
 * When we insert 1st item on new page in INSERT, UPDATE, HOT_UPDATE,
 * or MULTI_INSERT, we can (and we do) restore entire page in redo
 */
#define XLOG_HEAP_INIT_PAGE		0x80
```

## 동작 흐름

```text
 xl_info 1바이트

  7     6   5   4    3   2   1   0
 +----+-----------+--------------+
 |INIT| opcode    | XLR_INFO_MASK|   아래 4비트는 xlogrecord 공용 플래그 (L1309 에서 지운다)
 +----+-----------+--------------+

 info & XLOG_HEAP_OPMASK (0x70)        함수
 0x00  INSERT                          [08] heap_xlog_insert
 0x10  DELETE                          heap_xlog_delete
 0x20  UPDATE                          heap_xlog_update(hot_update = false)
 0x30  TRUNCATE                        아무것도 안 함 (smgr 레코드가 이미 처리, 논리 디코딩 전용)
 0x40  HOT_UPDATE                      heap_xlog_update(hot_update = true)
 0x50  CONFIRM                         heap_xlog_confirm   (speculative insert 확정)
 0x60  LOCK                            heap_xlog_lock
 0x70  INPLACE                         heap_xlog_inplace
```

예를 들어 빈 페이지에 첫 튜플을 넣은 `INSERT` 는 `xl_info` = 0x80 이다. opcode 는 0x00 이라 `heap_xlog_insert` 로 가고, 그 안에서 0x80 비트를 보고 페이지를 디스크에서 읽지 않고 0 으로 초기화한다(heapam_xlog.c L518-L523).

주석 L1311-L1314 대로 이 rmgr 의 레코드는 MVCC 데이터를 덮어쓰지 않으므로 standby 의 쿼리 충돌 처리를 하지 않는다. 충돌 처리가 필요한 prune, freeze 는 `heap2_redo` 쪽에 있다.

## 결과가 쓰이는 곳

```text
 opcode 별 함수
      --> 각자 XLogReadBufferForRedo 로 페이지를 받아 고치고 PageSetLSN, MarkBufferDirty
 알 수 없는 opcode
      --> PANIC "heap_redo: unknown op code" (L1348)
```

## 다루지 않는 것

`heap_xlog_delete`, `heap_xlog_update`, `heap_xlog_lock`, `heap_xlog_inplace`, `heap_xlog_confirm` 의 내부와 `heap2_redo` 는 다루지 않는다. 대표로 [08] heap_xlog_insert 만 따라간다.
