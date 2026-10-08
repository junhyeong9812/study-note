# XactLogCommitRecord

상위: [커밋](../README.md)

**commit 레코드의 본문을 조립해 `XLogInsert` 에 넘긴다.** 레코드의 고정 부분은 커밋 시각 8 바이트뿐이고, 나머지(서브 XID 목록, 커밋하면 지울 파일, 무효화 메시지, 2PC 정보, 복제 origin)는 있을 때만 붙는다. 무엇이 붙었는지는 `xinfo` 비트로 표시하고, `xinfo` 가 0 이 아니면 그 4 바이트도 레코드에 넣는다. 복구와 standby 는 이 레코드 하나만 읽고 pg_xact 갱신, 파일 삭제, 캐시 무효화를 똑같이 재연한다.

## 위치

`access` / `transam` / `xact.c` L5813-L5977 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L5813-L5977))

## 실제 코드

`access` / `transam` / `xact.c` L5813-L5977 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xact.c#L5813-L5977))

```c
// xact.c L5813-L5977
XLogRecPtr
XactLogCommitRecord(TimestampTz commit_time,
					int nsubxacts, TransactionId *subxacts,
					int nrels, RelFileLocator *rels,
					int ndroppedstats, xl_xact_stats_item *droppedstats,
					int nmsgs, SharedInvalidationMessage *msgs,
					bool relcacheInval,
					int xactflags, TransactionId twophase_xid,
					const char *twophase_gid)
{
	xl_xact_commit xlrec;
	xl_xact_xinfo xl_xinfo;
	xl_xact_dbinfo xl_dbinfo;
	xl_xact_subxacts xl_subxacts;
	xl_xact_relfilelocators xl_relfilelocators;
	xl_xact_stats_items xl_dropped_stats;
	xl_xact_invals xl_invals;
	xl_xact_twophase xl_twophase;
	xl_xact_origin xl_origin;
	uint8		info;

	Assert(CritSectionCount > 0);

	xl_xinfo.xinfo = 0;

	/* decide between a plain and 2pc commit */
	if (!TransactionIdIsValid(twophase_xid))
		info = XLOG_XACT_COMMIT;
	else
		info = XLOG_XACT_COMMIT_PREPARED;

	/* First figure out and collect all the information needed */

	xlrec.xact_time = commit_time;

	if (relcacheInval)
		xl_xinfo.xinfo |= XACT_COMPLETION_UPDATE_RELCACHE_FILE;
	if (forceSyncCommit)
		xl_xinfo.xinfo |= XACT_COMPLETION_FORCE_SYNC_COMMIT;
	if ((xactflags & XACT_FLAGS_ACQUIREDACCESSEXCLUSIVELOCK))
		xl_xinfo.xinfo |= XACT_XINFO_HAS_AE_LOCKS;

	/*
	 * Check if the caller would like to ask standbys for immediate feedback
	 * once this commit is applied.
	 */
	if (synchronous_commit >= SYNCHRONOUS_COMMIT_REMOTE_APPLY)
		xl_xinfo.xinfo |= XACT_COMPLETION_APPLY_FEEDBACK;

	/*
	 * Relcache invalidations requires information about the current database
	 * and so does logical decoding.
	 */
	if (nmsgs > 0 || XLogLogicalInfoActive())
	{
		xl_xinfo.xinfo |= XACT_XINFO_HAS_DBINFO;
		xl_dbinfo.dbId = MyDatabaseId;
		xl_dbinfo.tsId = MyDatabaseTableSpace;
	}

	if (nsubxacts > 0)
	{
		xl_xinfo.xinfo |= XACT_XINFO_HAS_SUBXACTS;
		xl_subxacts.nsubxacts = nsubxacts;
	}

	if (nrels > 0)
	{
		xl_xinfo.xinfo |= XACT_XINFO_HAS_RELFILELOCATORS;
		xl_relfilelocators.nrels = nrels;
		info |= XLR_SPECIAL_REL_UPDATE;
	}

	// ... (L5886-L5915 생략: dropped stats, 무효화 메시지, 2PC, origin 비트 (위와 같은 꼴))

	if (xl_xinfo.xinfo != 0)
		info |= XLOG_XACT_HAS_INFO;

	/* Then include all the collected data into the commit record. */

	XLogBeginInsert();

	XLogRegisterData(&xlrec, sizeof(xl_xact_commit));

	if (xl_xinfo.xinfo != 0)
		XLogRegisterData(&xl_xinfo.xinfo, sizeof(xl_xinfo.xinfo));

	if (xl_xinfo.xinfo & XACT_XINFO_HAS_DBINFO)
		XLogRegisterData(&xl_dbinfo, sizeof(xl_dbinfo));

	if (xl_xinfo.xinfo & XACT_XINFO_HAS_SUBXACTS)
	{
		XLogRegisterData(&xl_subxacts,
						 MinSizeOfXactSubxacts);
		XLogRegisterData(subxacts,
						 nsubxacts * sizeof(TransactionId));
	}

	// ... (L5940-L5971 생략: 나머지 하위 레코드 등록 (위와 같은 꼴))

	/* we allow filtering by xacts */
	XLogSetRecordFlags(XLOG_INCLUDE_ORIGIN);

	return XLogInsert(RM_XACT_ID, info);
}
```

레코드 본문의 꼴은 헤더에 주석으로 적혀 있다.

`src` / `include` / `access` / `xact.h` L320-L333 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xact.h#L320-L333))

```c
// xact.h L320-L333
typedef struct xl_xact_commit
{
	TimestampTz xact_time;		/* time of commit */

	/* xl_xact_xinfo follows if XLOG_XACT_HAS_INFO */
	/* xl_xact_dbinfo follows if XINFO_HAS_DBINFO */
	/* xl_xact_subxacts follows if XINFO_HAS_SUBXACT */
	/* xl_xact_relfilelocators follows if XINFO_HAS_RELFILELOCATORS */
	/* xl_xact_stats_items follows if XINFO_HAS_DROPPED_STATS */
	/* xl_xact_invals follows if XINFO_HAS_INVALS */
	/* xl_xact_twophase follows if XINFO_HAS_TWOPHASE */
	/* twophase_gid follows if XINFO_HAS_GID. As a null-terminated string. */
	/* xl_xact_origin follows if XINFO_HAS_ORIGIN, stored unaligned! */
} xl_xact_commit;
```

## 동작 흐름

```text
 XactLogCommitRecord
 L5834  Assert(CritSectionCount > 0)                    [06] 의 critical section 안에서만
 L5840  info = XLOG_XACT_COMMIT (0x00)
 L5846  xlrec.xact_time = 커밋 시각
        xinfo 비트를 모은다
          forceSyncCommit                      -> XACT_COMPLETION_FORCE_SYNC_COMMIT
          XACT_FLAGS_ACQUIREDACCESSEXCLUSIVELOCK -> XACT_XINFO_HAS_AE_LOCKS          standby 가 잠금을 풀 때 쓴다
          synchronous_commit >= remote_apply   -> XACT_COMPLETION_APPLY_FEEDBACK   L5859
          nsubxacts > 0                        -> XACT_XINFO_HAS_SUBXACTS          L5873
          nrels > 0                            -> HAS_RELFILELOCATORS, info |= XLR_SPECIAL_REL_UPDATE  L5879
 L5917  xinfo != 0 이면 info |= XLOG_XACT_HAS_INFO (0x80)
 L5922  XLogBeginInsert, XLogRegisterData ... (있는 것만 순서대로)
 L5974  XLogSetRecordFlags(XLOG_INCLUDE_ORIGIN)
 L5976  XLogInsert(RM_XACT_ID, info)                    -> 반환 LSN, XactLastRecEnd 갱신
```

본문 크기를 두 경우로 계산하면 "있을 때만 붙는다"가 어떻게 작동하는지 보인다. 둘 다 `wal_level = replica`, `synchronous_commit = on`, 보통 테이블에 INSERT 만 한 경우다(카탈로그를 안 건드리니 무효화 메시지가 없다).

```text
 A. INSERT 하나 후 COMMIT
    xinfo = 0
    main data: xl_xact_commit.xact_time                    8 bytes
    info = XLOG_XACT_COMMIT = 0x00
    합계 8 bytes

 B. SAVEPOINT 두 번 안에서 각각 INSERT 후 COMMIT (서브 XID 2 개)
    xinfo = XACT_XINFO_HAS_SUBXACTS = 1 << 1 = 0x02
    main data: xact_time                                    8
               xinfo                                        4
               xl_xact_subxacts.nsubxacts                   4   (MinSizeOfXactSubxacts)
               subxacts[2]                                  2 * 4 = 8
    info = 0x00 | XLOG_XACT_HAS_INFO = 0x80
    합계 24 bytes
```

## 결과가 쓰이는 곳

```text
 반환 LSN, XactLastRecEnd
      --> [06] 이 XLogFlush(XactLastRecEnd), SyncRepWaitForLSN 에 쓴다
 레코드 본문
      --> 복구와 standby 의 xact_redo (xact.c L6363) -> xact_redo_commit
            pg_xact 비트, 서브 XID, 파일 삭제, 무효화 재생
      --> 논리 디코딩이 커밋 경계와 무효화로 읽는다
```

## 다루지 않는 것

2PC 커밋(`XLOG_XACT_COMMIT_PREPARED`, GID), 복제 origin 하위 레코드, dropped stats 항목의 의미, `XLogInsert` 이후 WAL 버퍼에 들어가는 과정([행 쓰기와 WAL 기록 06](../../heap-insert-wal/06_XLogInsert/README.md))은 다루지 않았다.
