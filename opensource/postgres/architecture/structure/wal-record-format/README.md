# WAL 레코드 형식

상위: [PostgreSQL 아키텍처 지도](../../README.md)

WAL 은 `pg_wal/` 아래 **16MB 세그먼트 파일**들이 이어 붙은 하나의 바이트 열이고, LSN 은 그 바이트 열 안의 64비트 위치다. 그래서 LSN 하나에서 나눗셈과 나머지만으로 세그먼트 번호(파일 이름)와 파일 안 오프셋이 나온다. 세그먼트는 8192바이트 WAL 페이지로 나뉘고, 페이지마다 맨 앞에 헤더가 있다. 세그먼트의 첫 페이지는 40바이트 긴 헤더, 나머지는 24바이트 짧은 헤더다. 레코드는 8바이트 경계에서 시작해 페이지 경계를 넘어 흐를 수 있고, 넘어간 페이지의 헤더가 남은 길이를 적어 둔다. 레코드 하나는 24바이트 고정 헤더(`XLogRecord`) 뒤에 블록 참조 헤더들, 주 데이터 헤더, 그리고 실제 데이터가 차례로 붙은 모양이다. 블록 참조에는 페이지 전체 이미지(FPI)가 실릴 수 있는데, 페이지 가운데의 빈 구멍(hole)을 빼고 싣고, 설정에 따라 압축한다. 레코드를 조립하고 WAL 버퍼에 넣는 동작은 [행 쓰기와 WAL 기록](../../flows/heap-insert-wal/README.md)이, 읽어서 다시 적용하는 동작은 [WAL redo](../../flows/wal-redo/README.md)가 다룬다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이다. 경로는 `src/` 부터 적고, `src/backend/` 아래 파일만 그 뒤부터 적는다. 크기 계산은 기본 빌드 설정(`XLOG_BLCKSZ` 8192, `wal_segment_size` 16MB, `BLCKSZ` 8192)과 x86-64 기준이다.

## 전체 그림

```text
 LSN 공간 (XLogRecPtr, 64비트 바이트 위치)

 0/0          0/1000000        0/2000000        ...    1/2C000000       1/2D000000
 +------------+----------------+----------------+-- --+----------------+----
 | 세그먼트 0 | 세그먼트 1     | 세그먼트 2     |      | 세그먼트 300   |
 | (안 쓴다)  | ...0000000001  | ...0000000002  |      | ...010000002C  |
 +------------+----------------+----------------+-- --+----------------+----
               16MB = 2048 페이지 x 8192

 세그먼트 하나
 +----------------+----------------+----------------+-- ... --+----------------+
 | page 0         | page 1         | page 2         |         | page 2047      |
 | 긴 헤더 40     | 짧은 헤더 24   | 짧은 헤더 24   |         | 짧은 헤더 24   |
 | 레코드들 ...   | 레코드들 ...   |                |         |                |
 +----------------+----------------+----------------+-- ... --+----------------+

 레코드 하나 (MAXALIGN 8 경계에서 시작, 끝은 정렬하지 않고 다음 레코드 시작만 정렬)
 +-----------+-----------------+-----------------+----------------+------------+------------+
 | XLogRecord| BlockHeader 0   | BlockHeader 1   | DataHeader     | block data | main data  |
 | 24        | 4 + [5] + [2]   | ...             | Short 2        | 0, 1 ...   |            |
 |           | + [12] + 4      |                 | 또는 Long 5    |            |            |
 +-----------+-----------------+-----------------+----------------+------------+------------+
   [ ] 는 조건부: [5] 이미지 헤더, [2] 압축+hole 헤더, [12] RelFileLocator (SAME_REL 이면 생략)
   xl_tot_len = 이 전체 길이.  xl_crc = 헤더 뒤 전체 + 헤더의 앞 20바이트
```

## LSN, 세그먼트 번호, 파일 이름

LSN 은 부호 없는 64비트 정수이고, 사람에게는 위 32비트와 아래 32비트를 `/` 로 나눠 16진수로 보여 준다. 0 은 "무효"로 쓰려고 첫 세그먼트를 아예 쓰지 않는다.

`src` / `include` / `access` / `xlogdefs.h` L17-L49 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlogdefs.h#L17-L49))

```c
// src/include/access/xlogdefs.h L17-L49
/*
 * Pointer to a location in the XLOG.  These pointers are 64 bits wide,
 * because we don't want them ever to overflow.
 */
typedef uint64 XLogRecPtr;

/*
 * Zero is used indicate an invalid pointer. Bootstrap skips the first possible
 * WAL segment, initializing the first WAL page at WAL segment size, so no XLOG
 * record can begin at zero.
 */
#define InvalidXLogRecPtr		0
#define XLogRecPtrIsValid(r)	((r) != InvalidXLogRecPtr)
#define XLogRecPtrIsInvalid(r)	((r) == InvalidXLogRecPtr)

// ... (L32-L38 생략: unlogged 릴레이션용 가짜 LSN 의 시작값 FirstNormalUnloggedLSN)
/*
 * Handy macro for printing XLogRecPtr in conventional format, e.g.,
 *
 * printf("%X/%X", LSN_FORMAT_ARGS(lsn));
 */
#define LSN_FORMAT_ARGS(lsn) (AssertVariableIsOfTypeMacro((lsn), XLogRecPtr), (uint32) ((lsn) >> 32)), ((uint32) (lsn))

/*
 * XLogSegNo - physical log file sequence number.
 */
typedef uint64 XLogSegNo;
```

세그먼트 번호는 LSN 을 세그먼트 크기로 나눈 몫, 세그먼트 안 오프셋은 나머지다. 세그먼트 크기가 2의 거듭제곱이라 나머지는 마스크 하나로 구한다.

`src` / `include` / `access` / `xlog_internal.h` L87-L121 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlog_internal.h#L87-L121))

```c
// src/include/access/xlog_internal.h L87-L121
/* wal_segment_size can range from 1MB to 1GB */
#define WalSegMinSize 1024 * 1024
#define WalSegMaxSize 1024 * 1024 * 1024
/* default number of min and max wal segments */
#define DEFAULT_MIN_WAL_SEGS 5
#define DEFAULT_MAX_WAL_SEGS 64

/* check that the given size is a valid wal_segment_size */
#define IsPowerOf2(x) (x > 0 && ((x) & ((x)-1)) == 0)
#define IsValidWalSegSize(size) \
	 (IsPowerOf2(size) && \
	 ((size) >= WalSegMinSize && (size) <= WalSegMaxSize))

#define XLogSegmentsPerXLogId(wal_segsz_bytes)	\
	(UINT64CONST(0x100000000) / (wal_segsz_bytes))

#define XLogSegNoOffsetToRecPtr(segno, offset, wal_segsz_bytes, dest) \
		(dest) = (segno) * (wal_segsz_bytes) + (offset)

#define XLogSegmentOffset(xlogptr, wal_segsz_bytes)	\
	((xlogptr) & ((wal_segsz_bytes) - 1))

/*
 * Compute a segment number from an XLogRecPtr.
 *
 * For XLByteToSeg, do the computation at face value.  For XLByteToPrevSeg,
 * a boundary byte is taken to be in the previous segment.  This is suitable
 * for deciding which segment to write given a pointer to a record end,
 * for example.
 */
#define XLByteToSeg(xlrp, logSegNo, wal_segsz_bytes) \
	logSegNo = (xlrp) / (wal_segsz_bytes)

#define XLByteToPrevSeg(xlrp, logSegNo, wal_segsz_bytes) \
	logSegNo = ((xlrp) - 1) / (wal_segsz_bytes)
```

파일 이름은 24자리 16진수 셋이다. 타임라인 8자리, 그리고 세그먼트 번호를 "4GB 마다 몇 번째"(`log`)와 "그 안에서 몇 번째"(`seg`)로 나눈 8자리 둘이다. 16MB 세그먼트면 4GB 안에 256개가 들어가므로 `seg` 는 `00` ~ `FF` 만 쓴다.

`src` / `include` / `access` / `xlog_internal.h` L152-L171 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlog_internal.h#L152-L171))

```c
// src/include/access/xlog_internal.h L152-L171
/*
 * These macros encapsulate knowledge about the exact layout of XLog file
 * names, timeline history file names, and archive-status file names.
 */
#define MAXFNAMELEN		64

/* Length of XLog file name */
#define XLOG_FNAME_LEN	   24

/*
 * Generate a WAL segment file name.  Do not use this function in a helper
 * function allocating the result generated.
 */
static inline void
XLogFileName(char *fname, TimeLineID tli, XLogSegNo logSegNo, int wal_segsz_bytes)
{
	snprintf(fname, MAXFNAMELEN, "%08X%08X%08X", tli,
			 (uint32) (logSegNo / XLogSegmentsPerXLogId(wal_segsz_bytes)),
			 (uint32) (logSegNo % XLogSegmentsPerXLogId(wal_segsz_bytes)));
}
```

```text
 LSN 1/2C3D5B58 은 어느 파일의 어디인가 (타임라인 1)

 LSN                 = 0x0000_0001_2C3D_5B58
 segno               = LSN / 0x1000000            = 0x12C = 300        XLByteToSeg
 segment offset      = LSN & 0xFFFFFF             = 0x3D5B58 = 4021080  XLogSegmentOffset

 XLogSegmentsPerXLogId = 0x100000000 / 0x1000000  = 256
 log = 300 / 256 = 1,  seg = 300 % 256 = 44 = 0x2C

 file name   = %08X %08X %08X = 00000001 00000001 0000002C
             = pg_wal/00000001000000010000002C

 page        = 4021080 / 8192 = 490 (0x1EA)      페이지 시작 LSN 1/2C3D4000
 page offset = 4021080 % 8192 = 7000 (0x1B58)
 페이지 490 은 세그먼트 첫 페이지가 아니므로 짧은 헤더 24바이트 뒤에 데이터가 있다

 16MB 세그먼트에서는 파일 이름의 뒤 16자리가 LSN 을 그대로 읽은 것과 같다
   LSN 위 32비트 1          -> 가운데 00000001
   LSN 아래 32비트의 맨 위 바이트 0x2C -> 끝 0000002C
```

## WAL 페이지 헤더

페이지 헤더는 페이지마다 자기 위치(`xlp_pageaddr`)와 타임라인을 적어, 읽는 쪽이 엉뚱한 파일이나 재활용된 옛 내용을 읽었는지 확인하게 한다. 세그먼트 첫 페이지는 여기에 시스템 식별자와 크기 상수를 더한 긴 헤더를 쓴다.

`src` / `include` / `access` / `xlog_internal.h` L31-L85 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlog_internal.h#L31-L85))

```c
// src/include/access/xlog_internal.h L31-L85
/*
 * Each page of XLOG file has a header like this:
 */
#define XLOG_PAGE_MAGIC 0xD118	/* can be used as WAL version indicator */

typedef struct XLogPageHeaderData
{
	uint16		xlp_magic;		/* magic value for correctness checks */
	uint16		xlp_info;		/* flag bits, see below */
	TimeLineID	xlp_tli;		/* TimeLineID of first record on page */
	XLogRecPtr	xlp_pageaddr;	/* XLOG address of this page */

	/*
	 * When there is not enough space on current page for whole record, we
	 * continue on the next page.  xlp_rem_len is the number of bytes
	 * remaining from a previous page; it tracks xl_tot_len in the initial
	 * header.  Note that the continuation data isn't necessarily aligned.
	 */
	uint32		xlp_rem_len;	/* total len of remaining data for record */
} XLogPageHeaderData;

#define SizeOfXLogShortPHD	MAXALIGN(sizeof(XLogPageHeaderData))

typedef XLogPageHeaderData *XLogPageHeader;

/*
 * When the XLP_LONG_HEADER flag is set, we store additional fields in the
 * page header.  (This is ordinarily done just in the first page of an
 * XLOG file.)	The additional fields serve to identify the file accurately.
 */
typedef struct XLogLongPageHeaderData
{
	XLogPageHeaderData std;		/* standard header fields */
	uint64		xlp_sysid;		/* system identifier from pg_control */
	uint32		xlp_seg_size;	/* just as a cross-check */
	uint32		xlp_xlog_blcksz;	/* just as a cross-check */
} XLogLongPageHeaderData;

#define SizeOfXLogLongPHD	MAXALIGN(sizeof(XLogLongPageHeaderData))

typedef XLogLongPageHeaderData *XLogLongPageHeader;

/* When record crosses page boundary, set this flag in new page's header */
#define XLP_FIRST_IS_CONTRECORD		0x0001
/* This flag indicates a "long" page header */
#define XLP_LONG_HEADER				0x0002
/* This flag indicates backup blocks starting in this page are optional */
#define XLP_BKP_REMOVABLE			0x0004
/* Replaces a missing contrecord; see CreateOverwriteContrecordRecord */
#define XLP_FIRST_IS_OVERWRITE_CONTRECORD 0x0008
/* All defined flag bits in xlp_info (used for validity checking of header) */
#define XLP_ALL_FLAGS				0x000F

#define XLogPageHeaderSize(hdr)		\
	(((hdr)->xlp_info & XLP_LONG_HEADER) ? SizeOfXLogLongPHD : SizeOfXLogShortPHD)
```

```text
 XLogPageHeaderData  (SizeOfXLogShortPHD = MAXALIGN(sizeof) = 24)

 offset  size  field           뜻
 ------  ----  --------------  ------------------------------------------------
      0     2  xlp_magic       0xD118 (XLOG_PAGE_MAGIC). WAL 형식 버전 표시
      2     2  xlp_info        XLP_* 플래그
      4     4  xlp_tli         이 페이지 첫 레코드의 타임라인
      8     8  xlp_pageaddr    이 페이지 시작의 LSN
     16     4  xlp_rem_len     앞 페이지에서 넘어온 레코드의 남은 길이 (없으면 0)
     20     4  (패딩)          구조체 정렬 8 때문에 sizeof = 24
     24        데이터 시작

 XLogLongPageHeaderData  (SizeOfXLogLongPHD = 40)

      0    24  std             위 짧은 헤더 전체 (패딩 포함)
     24     8  xlp_sysid       pg_control 의 system_identifier
     32     4  xlp_seg_size    세그먼트 크기 (교차 확인용)
     36     4  xlp_xlog_blcksz WAL 페이지 크기 (교차 확인용)
     40        데이터 시작

 xlp_info 비트
   0x0001  XLP_FIRST_IS_CONTRECORD           페이지 첫 데이터가 앞 레코드의 이어짐
   0x0002  XLP_LONG_HEADER                   긴 헤더
   0x0004  XLP_BKP_REMOVABLE                 이 페이지에서 시작한 레코드의 FPI 는 빼도 된다
   0x0008  XLP_FIRST_IS_OVERWRITE_CONTRECORD 잃어버린 이어짐을 덮어쓴 자리
```

새 페이지를 WAL 버퍼에 준비하는 `AdvanceXLInsertBuffer` 가 헤더를 채운다. 0 으로 지우고, magic, 타임라인, 자기 주소를 넣고, 백업 중이 아니면 `XLP_BKP_REMOVABLE` 을, 세그먼트 첫 페이지면 긴 헤더를 넣는다. `xlp_rem_len` 과 `XLP_FIRST_IS_CONTRECORD` 는 여기서 넣지 않는다. 레코드를 복사하다 페이지를 넘는 backend 가 나중에 넣는다(xlog.c L1281-L1282, [XLogInsertRecord](../../flows/heap-insert-wal/08_XLogInsertRecord/README.md) 의 `CopyXLogRecordToWAL`).

`access` / `transam` / `xlog.c` L2097-L2141 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L2097-L2141))

```c
// access/transam/xlog.c L2097-L2141
		/*
		 * Be sure to re-zero the buffer so that bytes beyond what we've
		 * written will look like zeroes and not valid XLOG records...
		 */
		MemSet(NewPage, 0, XLOG_BLCKSZ);

		/*
		 * Fill the new page's header
		 */
		NewPage->xlp_magic = XLOG_PAGE_MAGIC;

		/* NewPage->xlp_info = 0; */	/* done by memset */
		NewPage->xlp_tli = tli;
		NewPage->xlp_pageaddr = NewPageBeginPtr;

		/* NewPage->xlp_rem_len = 0; */	/* done by memset */

		// ... (L2114-L2126 생략: XLP_BKP_REMOVABLE 의 뜻 (아카이버가 FPI 를 빼도 되는지))
		if (Insert->runningBackups == 0)
			NewPage->xlp_info |= XLP_BKP_REMOVABLE;

		/*
		 * If first page of an XLOG segment file, make it a long header.
		 */
		if ((XLogSegmentOffset(NewPage->xlp_pageaddr, wal_segment_size)) == 0)
		{
			XLogLongPageHeader NewLongPage = (XLogLongPageHeader) NewPage;

			NewLongPage->xlp_sysid = ControlFile->system_identifier;
			NewLongPage->xlp_seg_size = wal_segment_size;
			NewLongPage->xlp_xlog_blcksz = XLOG_BLCKSZ;
			NewPage->xlp_info |= XLP_LONG_HEADER;
		}
```

레코드가 페이지 끝을 넘으면 남은 바이트는 다음 페이지 헤더 바로 뒤에 이어 쓴다. 이어지는 데이터 앞에는 정렬을 하지 않는다(xlog_internal.h L47).

```text
 xl_tot_len 3498 짜리 레코드가 LSN 1/2C3D5B58 (페이지 490, 페이지 안 7000) 에서 시작

 page 490  1/2C3D4000                                                    1/2C3D6000
 +--------+----------------------------- ... -----+------------------------------+
 | hdr 24 | 앞 레코드들                           | 이 레코드 앞 1192 바이트     |
 +--------+----------------------------- ... -----+------------------------------+
                                                  7000                       8192
 page 491  1/2C3D6000
 +----------------------------------+-----------------------------+--------------+
 | hdr 24                           | 이 레코드 나머지 2306 바이트 | 다음 레코드  |
 | xlp_info = 0x0005                |                             |              |
 |   CONTRECORD | BKP_REMOVABLE     |                             |              |
 | xlp_rem_len = 3498 - 1192 = 2306 |                             |              |
 +----------------------------------+-----------------------------+--------------+
                                    24                       2330  2336
 끝 LSN = 1/2C3D6000 + 24 + 2306 = 1/2C3D691A
 다음 레코드 시작 = MAXALIGN -> 1/2C3D6920  (페이지 안 2336)
 (BKP_REMOVABLE 은 백업이 진행 중이 아닐 때만 켜진다)
```

## XLogRecord 고정 헤더

모든 레코드는 24바이트 헤더로 시작한다. 레코드 전체 길이, 트랜잭션 id, 직전 레코드의 시작 위치, 종류(rmgr 와 info), CRC 가 전부다.

`src` / `include` / `access` / `xlogrecord.h` L20-L91 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlogrecord.h#L20-L91))

```c
// src/include/access/xlogrecord.h L20-L91
/*
 * The overall layout of an XLOG record is:
 *		Fixed-size header (XLogRecord struct)
 *		XLogRecordBlockHeader struct
 *		XLogRecordBlockHeader struct
 *		...
 *		XLogRecordDataHeader[Short|Long] struct
 *		block data
 *		block data
 *		...
 *		main data
 *
 * There can be zero or more XLogRecordBlockHeaders, and 0 or more bytes of
 * rmgr-specific data not associated with a block.  XLogRecord structs
 * always start on MAXALIGN boundaries in the WAL files, but the rest of
 * the fields are not aligned.
 *
 * The XLogRecordBlockHeader, XLogRecordDataHeaderShort and
 * XLogRecordDataHeaderLong structs all begin with a single 'id' byte. It's
 * used to distinguish between block references, and the main data structs.
 */
typedef struct XLogRecord
{
	uint32		xl_tot_len;		/* total len of entire record */
	TransactionId xl_xid;		/* xact id */
	XLogRecPtr	xl_prev;		/* ptr to previous record in log */
	uint8		xl_info;		/* flag bits, see below */
	RmgrId		xl_rmid;		/* resource manager for this record */
	/* 2 bytes of padding here, initialize to zero */
	pg_crc32c	xl_crc;			/* CRC for this record */

	/* XLogRecordBlockHeaders and XLogRecordDataHeader follow, no padding */

} XLogRecord;

#define SizeOfXLogRecord	(offsetof(XLogRecord, xl_crc) + sizeof(pg_crc32c))

/*
 * The high 4 bits in xl_info may be used freely by rmgr. The
 * XLR_SPECIAL_REL_UPDATE and XLR_CHECK_CONSISTENCY bits can be passed by
 * XLogInsert caller. The rest are set internally by XLogInsert.
 */
#define XLR_INFO_MASK			0x0F
#define XLR_RMGR_INFO_MASK		0xF0

/*
 * XLogReader needs to allocate all the data of a WAL record in a single
 * chunk.  This means that a single XLogRecord cannot exceed MaxAllocSize
 * in length if we ignore any allocation overhead of the XLogReader.
 *
 * To accommodate some overhead, this value allows for 4M of allocation
 * overhead, that should be plenty enough for what the XLogReader
 * infrastructure expects as extra.
 */
#define XLogRecordMaxSize	(1020 * 1024 * 1024)

/*
 * If a WAL record modifies any relation files, in ways not covered by the
 * usual block references, this flag is set. This is not used for anything
 * by PostgreSQL itself, but it allows external tools that read WAL and keep
 * track of modified blocks to recognize such special record types.
 */
#define XLR_SPECIAL_REL_UPDATE	0x01

/*
 * Enforces consistency checks of replayed WAL at recovery. If enabled,
 * each record will log a full-page write for each block modified by the
 * record and will reuse it afterwards for consistency checks. The caller
 * of XLogInsert can use this value if necessary, but if
 * wal_consistency_checking is enabled for a rmgr this is set unconditionally.
 */
#define XLR_CHECK_CONSISTENCY	0x02
```

```text
 XLogRecord  (SizeOfXLogRecord = offsetof(xl_crc) + 4 = 24)

 offset  size  field        뜻
 ------  ----  -----------  ---------------------------------------------------------
      0     4  xl_tot_len   레코드 전체 길이 (헤더 포함, 정렬 패딩 미포함)
      4     4  xl_xid       트랜잭션 id. 없으면 0
      8     8  xl_prev      직전 레코드의 시작 LSN. 레코드끼리의 뒤 방향 고리
     16     1  xl_info      위 4비트 = rmgr 가 쓴다 (예 XLOG_HEAP_INSERT 0x00)
                            아래 4비트 = XLR_SPECIAL_REL_UPDATE 0x01, XLR_CHECK_CONSISTENCY 0x02
     17     1  xl_rmid      resource manager. RM_XLOG_ID 0, RM_HEAP_ID 10 (rmgrlist.h L28, L38)
     18     2  (패딩, 0)
     20     4  xl_crc       CRC-32C
     24        블록 헤더들이 패딩 없이 바로 이어진다
```

CRC 는 헤더 **뒤**의 바이트 전부를 먼저 넣고, 헤더의 앞 20바이트(`xl_crc` 직전까지)를 마지막에 넣어 계산한다. 조립하는 쪽([XLogRecordAssemble](../../flows/heap-insert-wal/07_XLogRecordAssemble/README.md))이 뒤 부분을 먼저 계산해 두고, `xl_prev` 가 정해진 뒤 헤더를 더해 마무리할 수 있게 한 순서다. 읽는 쪽은 같은 순서로 검증한다.

`access` / `transam` / `xlogreader.c` L1203-L1226 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogreader.c#L1203-L1226))

```c
// access/transam/xlogreader.c L1203-L1226
static bool
ValidXLogRecord(XLogReaderState *state, XLogRecord *record, XLogRecPtr recptr)
{
	pg_crc32c	crc;

	Assert(record->xl_tot_len >= SizeOfXLogRecord);

	/* Calculate the CRC */
	INIT_CRC32C(crc);
	COMP_CRC32C(crc, ((char *) record) + SizeOfXLogRecord, record->xl_tot_len - SizeOfXLogRecord);
	/* include the record header last */
	COMP_CRC32C(crc, (char *) record, offsetof(XLogRecord, xl_crc));
	FIN_CRC32C(crc);

	if (!EQ_CRC32C(record->xl_crc, crc))
	{
		report_invalid_record(state,
							  "incorrect resource manager data checksum in record at %X/%X",
							  LSN_FORMAT_ARGS(recptr));
		return false;
	}

	return true;
}
```

## 블록 참조 헤더

레코드가 바꾼 페이지마다 블록 참조 헤더가 하나씩 붙는다. 4바이트 기본 헤더 뒤에, 조건에 따라 이미지 헤더 5바이트, 압축 hole 헤더 2바이트, `RelFileLocator` 12바이트가 오고, 마지막에 블록 번호 4바이트가 온다. 구조체로 정의돼 있지만 정렬하지 않고 바이트로 이어 붙인다(xlogrecord.h L100-L101).

`src` / `include` / `access` / `xlogrecord.h` L93-L202 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlogrecord.h#L93-L202))

```c
// src/include/access/xlogrecord.h L93-L202
/*
 * Header info for block data appended to an XLOG record.
 *
 * 'data_length' is the length of the rmgr-specific payload data associated
 * with this block. It does not include the possible full page image, nor
 * XLogRecordBlockHeader struct itself.
 *
 * Note that we don't attempt to align the XLogRecordBlockHeader struct!
 * So, the struct must be copied to aligned local storage before use.
 */
typedef struct XLogRecordBlockHeader
{
	uint8		id;				/* block reference ID */
	uint8		fork_flags;		/* fork within the relation, and flags */
	uint16		data_length;	/* number of payload bytes (not including page
								 * image) */

	/* If BKPBLOCK_HAS_IMAGE, an XLogRecordBlockImageHeader struct follows */
	/* If BKPBLOCK_SAME_REL is not set, a RelFileLocator follows */
	/* BlockNumber follows */
} XLogRecordBlockHeader;

#define SizeOfXLogRecordBlockHeader (offsetof(XLogRecordBlockHeader, data_length) + sizeof(uint16))

/*
 * Additional header information when a full-page image is included
 * (i.e. when BKPBLOCK_HAS_IMAGE is set).
 *
 // ... (L121-L139 생략: hole 과 wal_compression 의 관계 설명 (아래 hole 절에서 다룬다))
 */
typedef struct XLogRecordBlockImageHeader
{
	uint16		length;			/* number of page image bytes */
	uint16		hole_offset;	/* number of bytes before "hole" */
	uint8		bimg_info;		/* flag bits, see below */

	/*
	 * If BKPIMAGE_HAS_HOLE and BKPIMAGE_COMPRESSED(), an
	 * XLogRecordBlockCompressHeader struct follows.
	 */
} XLogRecordBlockImageHeader;

#define SizeOfXLogRecordBlockImageHeader	\
	(offsetof(XLogRecordBlockImageHeader, bimg_info) + sizeof(uint8))

/* Information stored in bimg_info */
#define BKPIMAGE_HAS_HOLE		0x01	/* page image has "hole" */
#define BKPIMAGE_APPLY			0x02	/* page image should be restored
										 * during replay */
/* compression methods supported */
#define BKPIMAGE_COMPRESS_PGLZ	0x04
#define BKPIMAGE_COMPRESS_LZ4	0x08
#define BKPIMAGE_COMPRESS_ZSTD	0x10

#define	BKPIMAGE_COMPRESSED(info) \
	((info & (BKPIMAGE_COMPRESS_PGLZ | BKPIMAGE_COMPRESS_LZ4 | \
			  BKPIMAGE_COMPRESS_ZSTD)) != 0)

/*
 * Extra header information used when page image has "hole" and
 * is compressed.
 */
typedef struct XLogRecordBlockCompressHeader
{
	uint16		hole_length;	/* number of bytes in "hole" */
} XLogRecordBlockCompressHeader;

#define SizeOfXLogRecordBlockCompressHeader \
	sizeof(XLogRecordBlockCompressHeader)

/*
 * Maximum size of the header for a block reference. This is used to size a
 * temporary buffer for constructing the header.
 */
#define MaxSizeOfXLogRecordBlockHeader \
	(SizeOfXLogRecordBlockHeader + \
	 SizeOfXLogRecordBlockImageHeader + \
	 SizeOfXLogRecordBlockCompressHeader + \
	 sizeof(RelFileLocator) + \
	 sizeof(BlockNumber))

/*
 * The fork number fits in the lower 4 bits in the fork_flags field. The upper
 * bits are used for flags.
 */
#define BKPBLOCK_FORK_MASK	0x0F
#define BKPBLOCK_FLAG_MASK	0xF0
#define BKPBLOCK_HAS_IMAGE	0x10	/* block data is an XLogRecordBlockImage */
#define BKPBLOCK_HAS_DATA	0x20
#define BKPBLOCK_WILL_INIT	0x40	/* redo will re-init the page */
#define BKPBLOCK_SAME_REL	0x80	/* RelFileLocator omitted, same as
									 * previous */
```

```text
 블록 참조 하나의 헤더 부분

 +----+------------+--------------+ +--------+-------------+----------+ +--------------+ +-------------+ +----------+
 | id | fork_flags | data_length  | | length | hole_offset | bimg_info| | hole_length  | | spc|db|rel  | | blockNum |
 | 1  | 1          | 2            | | 2      | 2           | 1        | | 2            | | 4  4  4     | | 4        |
 +----+------------+--------------+ +--------+-------------+----------+ +--------------+ +-------------+ +----------+
  XLogRecordBlockHeader  4           XLogRecordBlockImageHeader  5       CompressHeader   RelFileLocator   BlockNumber
                                     HAS_IMAGE 일 때만                   HAS_HOLE 이고    SAME_REL 이 아닐
                                                                         압축했을 때만    때만

 id          0 ~ 32 (XLR_MAX_BLOCK_ID). 레코드 안에서 증가하는 순서
 fork_flags  아래 4비트 = ForkNumber (0 main, 1 fsm, 2 vm, 3 init)
             0x10 BKPBLOCK_HAS_IMAGE   이미지가 실렸다
             0x20 BKPBLOCK_HAS_DATA    rmgr 데이터가 data_length 만큼 실렸다
             0x40 BKPBLOCK_WILL_INIT   redo 가 페이지를 새로 만든다 (옛 내용 불필요)
             0x80 BKPBLOCK_SAME_REL    RelFileLocator 생략, 앞 블록과 같은 릴레이션
 data_length 이미지를 뺀 rmgr 데이터 길이

 최대 크기 MaxSizeOfXLogRecordBlockHeader = 4 + 5 + 2 + 12 + 4 = 27
 가장 흔한 꼴 (이미지 없음, 첫 블록) = 4 + 12 + 4 = 20
```

헤더를 실제로 쓰는 순서는 [XLogRecordAssemble](../../flows/heap-insert-wal/07_XLogRecordAssemble/README.md)(xloginsert.c L817-L836)에, FPI 가 없는 63바이트 레코드와 FPI 가 있는 3498바이트 레코드의 바이트 배치 예는 같은 문서의 동작 흐름에 있다. 여기서는 읽는 쪽에서 본다. 디코더는 첫 바이트(id)로 블록 참조인지 주 데이터인지를 가리고, 플래그를 보며 다음 필드를 꺼낸다. 플래그와 길이가 서로 맞지 않으면 그 레코드를 거부한다.

`access` / `transam` / `xlogreader.c` L1721-L1915 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlogreader.c#L1721-L1915))

```c
// access/transam/xlogreader.c L1721-L1915
	/* Decode the headers */
	datatotal = 0;
	while (remaining > datatotal)
	{
		COPY_HEADER_FIELD(&block_id, sizeof(uint8));

		if (block_id == XLR_BLOCK_ID_DATA_SHORT)
		{
			/* XLogRecordDataHeaderShort */
			uint8		main_data_len;

			COPY_HEADER_FIELD(&main_data_len, sizeof(uint8));

			decoded->main_data_len = main_data_len;
			datatotal += main_data_len;
			break;				/* by convention, the main data fragment is
								 * always last */
		}
		else if (block_id == XLR_BLOCK_ID_DATA_LONG)
		{
			/* XLogRecordDataHeaderLong */
			uint32		main_data_len;

			COPY_HEADER_FIELD(&main_data_len, sizeof(uint32));
			decoded->main_data_len = main_data_len;
			datatotal += main_data_len;
			break;				/* by convention, the main data fragment is
								 * always last */
		}
		else if (block_id == XLR_BLOCK_ID_ORIGIN)
		{
			COPY_HEADER_FIELD(&decoded->record_origin, sizeof(RepOriginId));
		}
		else if (block_id == XLR_BLOCK_ID_TOPLEVEL_XID)
		{
			COPY_HEADER_FIELD(&decoded->toplevel_xid, sizeof(TransactionId));
		}
		else if (block_id <= XLR_MAX_BLOCK_ID)
		{
			/* XLogRecordBlockHeader */
			DecodedBkpBlock *blk;
			uint8		fork_flags;

			// ... (L1764-L1777 생략: 건너뛴 block id 를 미사용으로 표시하고, block id 가 증가하는지 확인)
			blk = &decoded->blocks[block_id];
			blk->in_use = true;
			blk->apply_image = false;

			COPY_HEADER_FIELD(&fork_flags, sizeof(uint8));
			blk->forknum = fork_flags & BKPBLOCK_FORK_MASK;
			blk->flags = fork_flags;
			blk->has_image = ((fork_flags & BKPBLOCK_HAS_IMAGE) != 0);
			blk->has_data = ((fork_flags & BKPBLOCK_HAS_DATA) != 0);

			blk->prefetch_buffer = InvalidBuffer;

			COPY_HEADER_FIELD(&blk->data_len, sizeof(uint16));
			// ... (L1791-L1806 생략: HAS_DATA 와 data_length 가 맞는지 확인)
			datatotal += blk->data_len;

			if (blk->has_image)
			{
				COPY_HEADER_FIELD(&blk->bimg_len, sizeof(uint16));
				COPY_HEADER_FIELD(&blk->hole_offset, sizeof(uint16));
				COPY_HEADER_FIELD(&blk->bimg_info, sizeof(uint8));

				blk->apply_image = ((blk->bimg_info & BKPIMAGE_APPLY) != 0);

				if (BKPIMAGE_COMPRESSED(blk->bimg_info))
				{
					if (blk->bimg_info & BKPIMAGE_HAS_HOLE)
						COPY_HEADER_FIELD(&blk->hole_length, sizeof(uint16));
					else
						blk->hole_length = 0;
				}
				else
					blk->hole_length = BLCKSZ - blk->bimg_len;
				datatotal += blk->bimg_len;

				// ... (L1828-L1887 생략: hole, 압축 플래그와 길이의 교차 확인 (아래 표))
			}
			if (!(fork_flags & BKPBLOCK_SAME_REL))
			{
				COPY_HEADER_FIELD(&blk->rlocator, sizeof(RelFileLocator));
				rlocator = &blk->rlocator;
			}
			else
			{
				// ... (L1896-L1902 생략: SAME_REL 인데 앞 릴레이션이 없으면 오류)

				blk->rlocator = *rlocator;
			}
			COPY_HEADER_FIELD(&blk->blkno, sizeof(BlockNumber));
		}
		// ... (L1908-L1914 생략: 알 수 없는 block_id 오류)
	}
```

```text
 이미지 길이와 hole 의 관계 (DecodeXLogRecord L1817-L1825, L1828-L1887 의 교차 확인)

 HAS_HOLE  COMPRESSED  length               hole_length 를 아는 방법
 --------  ----------  -------------------  ---------------------------------------
 0         0           8192                 0
 1         0           8192 - hole_length   8192 - length 로 계산
 0         1           < 8192               0
 1         1           < 8192               CompressHeader 2바이트에 따로 적는다
```

## hole 과 압축

FPI 는 페이지를 통째로 싣지만, 표준 페이지의 `pd_lower` 와 `pd_upper` 사이 빈 구멍은 0 으로만 차 있으므로 빼고 싣는다. 압축하면 실린 길이만 보고는 hole 길이를 알 수 없어서 2바이트를 더 적는다. 압축해도 그 2바이트를 아끼지 못하면 압축하지 않은 원본을 싣는다.

`access` / `transam` / `xloginsert.c` L943-L1017 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xloginsert.c#L943-L1017))

```c
// access/transam/xloginsert.c L943-L1017
static bool
XLogCompressBackupBlock(const PageData *page, uint16 hole_offset, uint16 hole_length,
						void *dest, uint16 *dlen)
{
	int32		orig_len = BLCKSZ - hole_length;
	int32		len = -1;
	int32		extra_bytes = 0;
	const void *source;
	PGAlignedBlock tmp;

	if (hole_length != 0)
	{
		/* must skip the hole */
		memcpy(tmp.data, page, hole_offset);
		memcpy(tmp.data + hole_offset,
			   page + (hole_offset + hole_length),
			   BLCKSZ - (hole_length + hole_offset));
		source = tmp.data;

		/*
		 * Extra data needs to be stored in WAL record for the compressed
		 * version of block image if the hole exists.
		 */
		extra_bytes = SizeOfXLogRecordBlockCompressHeader;
	}
	else
		source = page;

	// ... (L971-L1003 생략: pglz, lz4, zstd 중 wal_compression 이 고른 것으로 압축)

	/*
	 * We recheck the actual size even if compression reports success and see
	 * if the number of bytes saved by compression is larger than the length
	 * of extra data needed for the compressed version of block image.
	 */
	if (len >= 0 &&
		len + extra_bytes < orig_len)
	{
		*dlen = (uint16) len;	/* successful compression */
		return true;
	}
	return false;
}
```

```text
 같은 페이지의 FPI 세 가지 꼴 (pd_lower 404, pd_upper 5152 -> hole_offset 404, hole_length 4748)

 1. wal_compression = off
    이미지 헤더  length 3444, hole_offset 404, bimg_info 0x03 (HAS_HOLE | APPLY)
    실린 바이트  page[0, 404) + page[5152, 8192)          = 404 + 3040 = 3444

 2. wal_compression = lz4, 압축 결과를 1200 바이트라고 하면 (가정한 값)
    조건  1200 + 2 < 3444  (len + extra_bytes < orig_len, L1010-L1011)  -> 압축본을 싣는다
    이미지 헤더  length 1200, hole_offset 404, bimg_info 0x0B (HAS_HOLE | APPLY | COMPRESS_LZ4)
    CompressHeader  hole_length 4748
    블록 헤더 부분 = 4 + 5 + 2 + 12 + 4 = 27,  실린 바이트 1200

 3. 압축 결과가 3443 바이트라면 (가정한 값)
    3443 + 2 < 3444 가 거짓 -> 1 과 같은 꼴로 원본을 싣는다

 redo 는 길이 3444 짜리를 [0, 404) 와 [5152, 8192) 로 펼치고 가운데를 0 으로 채운다
   (RestoreBlockImage, xlogreader.c L2165-L2178)
 APPLY(0x02) 가 없는 이미지는 wal_consistency_checking 용이라 redo 가 페이지에 쓰지 않는다
```

## 주 데이터 헤더와 특수 id

블록 참조 헤더들이 끝나면, 블록에 묶이지 않은 rmgr 데이터(주 데이터)의 길이를 알리는 헤더가 온다. 255바이트 이하면 짧은 꼴(id 255 + 길이 1바이트), 넘으면 긴 꼴(id 254 + 길이 4바이트)이다. 주 데이터 헤더는 항상 헤더 부분의 마지막이다.

`src` / `include` / `access` / `xlogrecord.h` L204-L246 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlogrecord.h#L204-L246))

```c
// src/include/access/xlogrecord.h L204-L246
/*
 * XLogRecordDataHeaderShort/Long are used for the "main data" portion of
 * the record. If the length of the data is less than 256 bytes, the short
 * form is used, with a single byte to hold the length. Otherwise the long
 * form is used.
 *
 * (These structs are currently not used in the code, they are here just for
 * documentation purposes).
 */
typedef struct XLogRecordDataHeaderShort
{
	uint8		id;				/* XLR_BLOCK_ID_DATA_SHORT */
	uint8		data_length;	/* number of payload bytes */
}			XLogRecordDataHeaderShort;

#define SizeOfXLogRecordDataHeaderShort (sizeof(uint8) * 2)

typedef struct XLogRecordDataHeaderLong
{
	uint8		id;				/* XLR_BLOCK_ID_DATA_LONG */
	/* followed by uint32 data_length, unaligned */
}			XLogRecordDataHeaderLong;

#define SizeOfXLogRecordDataHeaderLong (sizeof(uint8) + sizeof(uint32))

/*
 * Block IDs used to distinguish different kinds of record fragments. Block
 * references are numbered from 0 to XLR_MAX_BLOCK_ID. A rmgr is free to use
 * any ID number in that range (although you should stick to small numbers,
 * because the WAL machinery is optimized for that case). A few ID
 * numbers are reserved to denote the "main" data portion of the record,
 * as well as replication-supporting transaction metadata.
 *
 * The maximum is currently set at 32, quite arbitrarily. Most records only
 * need a handful of block references, but there are a few exceptions that
 * need more.
 */
#define XLR_MAX_BLOCK_ID			32

#define XLR_BLOCK_ID_DATA_SHORT		255
#define XLR_BLOCK_ID_DATA_LONG		254
#define XLR_BLOCK_ID_ORIGIN			253
#define XLR_BLOCK_ID_TOPLEVEL_XID	252
```

```text
 블록 헤더 자리의 첫 바이트(id) 로 가른다

 id        name                        follows             뜻
 --------  --------------------------  ------------------  ----------------------------------------
 0 ~ 32    (block reference)           fork_flags 1, ...   블록 참조
 252       XLR_BLOCK_ID_TOPLEVEL_XID   TransactionId 4     상위 트랜잭션 id. wal_level=logical 에서
                                                           아직 안 남긴 하위 트랜잭션 (xact.c L554-L556)
 253       XLR_BLOCK_ID_ORIGIN         RepOriginId 2       복제 origin 이 설정된 세션
 254       XLR_BLOCK_ID_DATA_LONG      uint32 4            주 데이터 길이 (256 이상)
 255       XLR_BLOCK_ID_DATA_SHORT     uint8 1             주 데이터 길이 (1 ~ 255)

 헤더 부분이 끝난 뒤의 데이터 순서
   block 0 image, block 0 data, ... block N image, block N data, main data
   (블록마다 이미지가 먼저, 데이터가 다음. DecodeXLogRecord L1931-L1957)
   (디코더는 헤더에서 모은 길이 합 datatotal 이 남은 바이트와 같은지 확인한다, L1917)
```

## 바이트 하나하나 - initdb 의 첫 레코드

모든 바이트를 소스로 정할 수 있는 레코드가 하나 있다. initdb 가 만드는 첫 WAL 레코드, 곧 bootstrap 종료 체크포인트다. 0/0 세그먼트를 쓰지 않으므로 첫 페이지 주소는 세그먼트 크기 `0/1000000` 이고, 레코드는 긴 헤더 40바이트 바로 뒤에 놓인다.

`access` / `transam` / `xlog.c` L5143-L5173 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L5143-L5173))

```c
// access/transam/xlog.c L5143-L5173
	/* Set up the XLOG page header */
	page->xlp_magic = XLOG_PAGE_MAGIC;
	page->xlp_info = XLP_LONG_HEADER;
	page->xlp_tli = BootstrapTimeLineID;
	page->xlp_pageaddr = wal_segment_size;
	longpage = (XLogLongPageHeader) page;
	longpage->xlp_sysid = sysidentifier;
	longpage->xlp_seg_size = wal_segment_size;
	longpage->xlp_xlog_blcksz = XLOG_BLCKSZ;

	/* Insert the initial checkpoint record */
	recptr = ((char *) page + SizeOfXLogLongPHD);
	record = (XLogRecord *) recptr;
	record->xl_prev = 0;
	record->xl_xid = InvalidTransactionId;
	record->xl_tot_len = SizeOfXLogRecord + SizeOfXLogRecordDataHeaderShort + sizeof(checkPoint);
	record->xl_info = XLOG_CHECKPOINT_SHUTDOWN;
	record->xl_rmid = RM_XLOG_ID;
	recptr += SizeOfXLogRecord;
	/* fill the XLogRecordDataHeaderShort struct */
	*(recptr++) = (char) XLR_BLOCK_ID_DATA_SHORT;
	*(recptr++) = sizeof(checkPoint);
	memcpy(recptr, &checkPoint, sizeof(checkPoint));
	recptr += sizeof(checkPoint);
	Assert(recptr - (char *) record == record->xl_tot_len);

	INIT_CRC32C(crc);
	COMP_CRC32C(crc, ((char *) record) + SizeOfXLogRecord, record->xl_tot_len - SizeOfXLogRecord);
	COMP_CRC32C(crc, (char *) record, offsetof(XLogRecord, xl_crc));
	FIN_CRC32C(crc);
	record->xl_crc = crc;
```

```text
 pg_wal/000000010000000000000001  (xlp_pageaddr = wal_segment_size = 0x1000000, xlog.c L5147)

 파일 offset  LSN        바이트 (리틀엔디언)              필드
 -----------  ---------  -------------------------------  ----------------------------------
           0  0/1000000  18 D1                            xlp_magic 0xD118
           2             02 00                            xlp_info = XLP_LONG_HEADER
           4             01 00 00 00                      xlp_tli = 1 (BootstrapTimeLineID)
           8             00 00 00 01 00 00 00 00          xlp_pageaddr = 0x1000000
          16             00 00 00 00                      xlp_rem_len = 0
          20             00 00 00 00                      (패딩)
          24             (8바이트)                        xlp_sysid = system_identifier
          32             00 00 00 01                      xlp_seg_size = 16777216
          36             00 20 00 00                      xlp_xlog_blcksz = 8192
          40  0/1000028  72 00 00 00                      xl_tot_len = 24 + 2 + 88 = 114
          44             00 00 00 00                      xl_xid = 0
          48             00 00 00 00 00 00 00 00          xl_prev = 0 (첫 레코드)
          56             00                               xl_info = XLOG_CHECKPOINT_SHUTDOWN
          57             00                               xl_rmid = RM_XLOG_ID
          58             00 00                            (패딩)
          60             (4바이트)                        xl_crc
          64             FF                               XLR_BLOCK_ID_DATA_SHORT
          65             58                               주 데이터 길이 = sizeof(CheckPoint) = 88
          66             (88바이트)                       CheckPoint. redo = 0/1000028 (L5115)
                                                          (88 = x86-64 의 sizeof(CheckPoint))
         154             끝 LSN 0/100009A

 블록 참조가 없는 레코드라 헤더 뒤에 곧바로 주 데이터 헤더가 온다
 이 레코드의 LSN 0/1000028 이 pg_control 의 checkPoint 에 들어간다
```

## db-engine 에서는

db-engine 의 WAL 은 파일 하나에 `[길이 4][tag 1][txId 8][본문]` 레코드를 이어 붙인다. 페이지도 세그먼트도 없고, 체크섬도 없다. 레코드는 "어느 테이블에 어떤 튜플을 넣었다"는 논리 연산이라 페이지 이미지가 없다.

```text
 같은 문제(로그 레코드의 모양과 위치), 두 구현

 파일
   PostgreSQL  pg_wal/<TLI><log><seg> 16MB 파일 여러 개, 8192 페이지마다 헤더 24/40
               레코드가 페이지 경계를 넘어 흐른다
   db-engine   wal 파일 하나, 계속 append. 페이지 없음

 LSN
   PostgreSQL  바이트 위치 (페이지 헤더 포함). LSN -> 파일, 오프셋은 나눗셈
   db-engine   레코드 순번 1, 2, 3 ... reopen 때 레코드 수를 세어 nextLsn 복원

 레코드 머리
   PostgreSQL  [XLogRecord 24] xl_tot_len, xl_xid, xl_prev, xl_info, xl_rmid, xl_crc
   db-engine   [len 4][tag 1 (BEGIN/INSERT/COMMIT/ABORT/CHECKPOINT)][txId 8]

 바꾼 대상
   PostgreSQL  [블록 참조 헤더 x N] (rel, fork, blk) + FPI (hole 제거, 압축) + rmgr 주 데이터
   db-engine   [nameLen 4][테이블 이름][tupleLen 4][tuple]. 페이지가 아니라 논리 연산

 무결성
   PostgreSQL  레코드마다 CRC-32C, xl_prev 로 앞 레코드와 이어졌는지 확인
   db-engine   없음. readInt 가 EOF 를 만나면 끝

 체크포인트
   PostgreSQL  WAL 레코드 + 그 위치를 pg_control 에
   db-engine   Checkpoint 레코드를 로그 안에 append, 마지막 적용 LSN 은 recovery.meta
```

PostgreSQL 의 레코드는 페이지 단위 물리 변경을 적으므로 redo 가 페이지 LSN 과 레코드 LSN 을 비교해 이미 적용된 변경을 건너뛸 수 있다. db-engine 은 페이지에 LSN 을 찍지 않고 "어디까지 적용했나"를 별도 파일 `recovery.meta` 에 둔다. 08-02 는 이것을 page header 의 pageLSN 을 건너뛴 학습용 단순화라고 적는다. 챕터: [08-01-wal-recovery](../../../../../project/db-engine/08-01-wal-recovery/), [08-02-lsn-checkpoint](../../../../../project/db-engine/08-02-lsn-checkpoint/).

## 어디에서 쓰이는가

```text
 [행 쓰기와 WAL 기록]  XLogRecordAssemble 이 이 형식으로 헤더를 hdr_scratch 에 쓰고 CRC 를 계산한다
                       ReserveXLogInsertLocation 이 페이지 헤더를 건너뛴 바이트 위치를 LSN 으로 바꾼다
                       CopyXLogRecordToWAL 이 페이지를 넘을 때 xlp_rem_len, CONTRECORD 를 넣는다
 [커밋]                커밋 레코드도 같은 형식 (rmid = RM_XACT_ID)
 [체크포인트]          XLOG_CHECKPOINT_REDO / ONLINE 레코드, 그 LSN 을 pg_control 에
                       REDO 지점보다 앞선 세그먼트 파일을 이름으로 골라 지우거나 재활용한다
 [WAL redo]            페이지 헤더 검증 -> xl_crc 검증 -> DecodeXLogRecord -> rmgr 의 redo
                       블록 참조의 FPI 가 있으면 페이지를 이미지로 덮는다
 [스트리밍 복제]       walsender 가 세그먼트 파일의 바이트를 LSN 범위로 그대로 보낸다
```

흐름 문서: [행 쓰기와 WAL 기록](../../flows/heap-insert-wal/README.md)(조립은 [XLogRecordAssemble](../../flows/heap-insert-wal/07_XLogRecordAssemble/README.md), 바이트 위치와 LSN 의 변환은 [ReserveXLogInsertLocation](../../flows/heap-insert-wal/09_ReserveXLogInsertLocation/README.md)), [커밋](../../flows/commit/README.md), [체크포인트](../../flows/checkpoint/README.md), [WAL redo](../../flows/wal-redo/README.md), [스트리밍 복제](../../flows/streaming-replication/README.md). WAL 파일이 놓이는 디렉터리와 `pg_control` 은 [디스크 배치](../disk-layout/README.md)에 있다.

## 다루지 않는 것

rmgr 마다 다른 주 데이터와 블록 데이터의 형식(`xl_heap_insert` 등은 각 rmgr 의 `*_xlog.h`), 세그먼트 전환 레코드 `XLOG_SWITCH` 가 남은 공간을 채우는 방식, 타임라인 history 파일(`<TLI>.history`)과 `.partial` 파일, `archive_status/` 의 `.ready`/`.done` 표시, `XLP_FIRST_IS_OVERWRITE_CONTRECORD` 를 쓰는 복구 경로(`CreateOverwriteContrecordRecord`), 레코드 최대 크기 `XLogRecordMaxSize` 의 근거, WAL summarizer 의 `pg_wal/summaries/` 형식은 곁가지라 다루지 않았다.
