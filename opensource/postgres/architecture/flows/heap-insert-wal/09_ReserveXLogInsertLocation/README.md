# ReserveXLogInsertLocation

상위: [행 쓰기와 WAL 기록](../README.md)

**WAL 에 들어가는 모든 레코드가 줄을 서는 단 하나의 지점이다.** spinlock(`insertpos_lck`) 아래에서 하는 일은 덧셈 한 번과 대입 두 번뿐이다. 이것이 가능한 이유는 위치를 LSN 이 아니라 "쓸 수 있는 바이트 위치"(usable byte position)로 세기 때문이다. 이 위치는 WAL 페이지 헤더를 세지 않으므로 X 바이트 예약이 그냥 `CurrBytePos += X` 가 되고, 페이지 헤더를 끼워 넣어 실제 LSN 으로 바꾸는 계산은 잠금 밖에서 한다(L1124-L1133 주석).

## 위치

`access` / `transam` / `xlog.c` L1111-L1155 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1111-L1155))

## 실제 코드

`access` / `transam` / `xlog.c` L1092-L1155 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1092-L1155))

```c
// xlog.c L1092-L1155
/*
 * Reserves the right amount of space for a record of given size from the WAL.
 * *StartPos is set to the beginning of the reserved section, *EndPos to
 * its end+1. *PrevPtr is set to the beginning of the previous record; it is
 * used to set the xl_prev of this record.
 *
 * This is the performance critical part of XLogInsert that must be serialized
 * across backends. The rest can happen mostly in parallel. Try to keep this
 * section as short as possible, insertpos_lck can be heavily contended on a
 * busy system.
 *
 * NB: The space calculation here must match the code in CopyXLogRecordToWAL,
 * where we actually copy the record to the reserved space.
 *
 * NB: Testing shows that XLogInsertRecord runs faster if this code is inlined;
 * however, because there are two call sites, the compiler is reluctant to
 * inline. We use pg_always_inline here to try to convince it.
 */
static pg_always_inline void
ReserveXLogInsertLocation(int size, XLogRecPtr *StartPos, XLogRecPtr *EndPos,
						  XLogRecPtr *PrevPtr)
{
	XLogCtlInsert *Insert = &XLogCtl->Insert;
	uint64		startbytepos;
	uint64		endbytepos;
	uint64		prevbytepos;

	size = MAXALIGN(size);

	/* All (non xlog-switch) records should contain data. */
	Assert(size > SizeOfXLogRecord);

	/*
	 * The duration the spinlock needs to be held is minimized by minimizing
	 * the calculations that have to be done while holding the lock. The
	 * current tip of reserved WAL is kept in CurrBytePos, as a byte position
	 * that only counts "usable" bytes in WAL, that is, it excludes all WAL
	 * page headers. The mapping between "usable" byte positions and physical
	 * positions (XLogRecPtrs) can be done outside the locked region, and
	 * because the usable byte position doesn't include any headers, reserving
	 * X bytes from WAL is almost as simple as "CurrBytePos += X".
	 */
	SpinLockAcquire(&Insert->insertpos_lck);

	startbytepos = Insert->CurrBytePos;
	endbytepos = startbytepos + size;
	prevbytepos = Insert->PrevBytePos;
	Insert->CurrBytePos = endbytepos;
	Insert->PrevBytePos = startbytepos;

	SpinLockRelease(&Insert->insertpos_lck);

	*StartPos = XLogBytePosToRecPtr(startbytepos);
	*EndPos = XLogBytePosToEndRecPtr(endbytepos);
	*PrevPtr = XLogBytePosToRecPtr(prevbytepos);

	/*
	 * Check that the conversions between "usable byte positions" and
	 * XLogRecPtrs work consistently in both directions.
	 */
	Assert(XLogRecPtrToBytePos(*StartPos) == startbytepos);
	Assert(XLogRecPtrToBytePos(*EndPos) == endbytepos);
	Assert(XLogRecPtrToBytePos(*PrevPtr) == prevbytepos);
}
```

잠금 밖에서 하는 변환이다. 세그먼트 첫 페이지는 긴 헤더(40), 나머지 페이지는 짧은 헤더(24)를 끼워 넣는다.

`src` / `include` / `access` / `xlog_internal.h` L52-L52 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlog_internal.h#L52-L52))

```c
// xlog_internal.h L52-L52
#define SizeOfXLogShortPHD	MAXALIGN(sizeof(XLogPageHeaderData))
```

`access` / `transam` / `xlog.c` L598-L598 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L598-L598))

```c
// xlog.c L598-L598
#define UsableBytesInPage (XLOG_BLCKSZ - SizeOfXLogShortPHD)
```

`access` / `transam` / `xlog.c` L1855-L1892 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1855-L1892))

```c
// xlog.c L1855-L1892
/*
 * Converts a "usable byte position" to XLogRecPtr. A usable byte position
 * is the position starting from the beginning of WAL, excluding all WAL
 * page headers.
 */
static XLogRecPtr
XLogBytePosToRecPtr(uint64 bytepos)
{
	uint64		fullsegs;
	uint64		fullpages;
	uint64		bytesleft;
	uint32		seg_offset;
	XLogRecPtr	result;

	fullsegs = bytepos / UsableBytesInSegment;
	bytesleft = bytepos % UsableBytesInSegment;

	if (bytesleft < XLOG_BLCKSZ - SizeOfXLogLongPHD)
	{
		/* fits on first page of segment */
		seg_offset = bytesleft + SizeOfXLogLongPHD;
	}
	else
	{
		/* account for the first page on segment with long header */
		seg_offset = XLOG_BLCKSZ;
		bytesleft -= XLOG_BLCKSZ - SizeOfXLogLongPHD;

		fullpages = bytesleft / UsableBytesInPage;
		bytesleft = bytesleft % UsableBytesInPage;

		seg_offset += fullpages * XLOG_BLCKSZ + bytesleft + SizeOfXLogShortPHD;
	}

	XLogSegNoOffsetToRecPtr(fullsegs, seg_offset, wal_segment_size, result);

	return result;
}
```

끝 위치는 페이지 경계에 딱 맞으면 다음 페이지 헤더 앞을 가리킨다.

`access` / `transam` / `xlog.c` L1894-L1938 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L1894-L1938))

```c
// xlog.c L1894-L1938
/*
 * Like XLogBytePosToRecPtr, but if the position is at a page boundary,
 * returns a pointer to the beginning of the page (ie. before page header),
 * not to where the first xlog record on that page would go to. This is used
 * when converting a pointer to the end of a record.
 */
static XLogRecPtr
XLogBytePosToEndRecPtr(uint64 bytepos)
{
	uint64		fullsegs;
	uint64		fullpages;
	uint64		bytesleft;
	uint32		seg_offset;
	XLogRecPtr	result;

	fullsegs = bytepos / UsableBytesInSegment;
	bytesleft = bytepos % UsableBytesInSegment;

	if (bytesleft < XLOG_BLCKSZ - SizeOfXLogLongPHD)
	{
		/* fits on first page of segment */
		if (bytesleft == 0)
			seg_offset = 0;
		else
			seg_offset = bytesleft + SizeOfXLogLongPHD;
	}
	else
	{
		/* account for the first page on segment with long header */
		seg_offset = XLOG_BLCKSZ;
		bytesleft -= XLOG_BLCKSZ - SizeOfXLogLongPHD;

		fullpages = bytesleft / UsableBytesInPage;
		bytesleft = bytesleft % UsableBytesInPage;

		if (bytesleft == 0)
			seg_offset += fullpages * XLOG_BLCKSZ + bytesleft;
		else
			seg_offset += fullpages * XLOG_BLCKSZ + bytesleft + SizeOfXLogShortPHD;
	}

	XLogSegNoOffsetToRecPtr(fullsegs, seg_offset, wal_segment_size, result);

	return result;
}
```

## 동작 흐름

```text
 L1119 size = MAXALIGN(size)                     다음 레코드도 8바이트 경계에서 시작한다
 L1134 SpinLockAcquire(&Insert->insertpos_lck)
 L1136   startbytepos = CurrBytePos
 L1137   endbytepos   = startbytepos + size
 L1138   prevbytepos  = PrevBytePos               직전 레코드의 시작
 L1139   CurrBytePos  = endbytepos
 L1140   PrevBytePos  = startbytepos
 L1142 SpinLockRelease
 L1144 *StartPos = XLogBytePosToRecPtr(startbytepos)
 L1145 *EndPos   = XLogBytePosToEndRecPtr(endbytepos)
 L1146 *PrevPtr  = XLogBytePosToRecPtr(prevbytepos)  --> rechdr->xl_prev

 XLogBytePosToRecPtr(bytepos)                     L1861
   L1869 fullsegs = bytepos / UsableBytesInSegment
   L1872 세그먼트 첫 페이지 안이면 seg_offset = bytesleft + 40
   L1880 아니면 첫 페이지(8152) 를 빼고, 남은 바이트를 8168 단위 페이지로 나눠
   L1886   seg_offset = 8192 + fullpages * 8192 + bytesleft + 24
```

`xl_prev` 는 레코드끼리의 뒤 방향 고리다. 예약과 같은 잠금 안에서 `PrevBytePos` 를 넘겨받으므로, 동시에 들어온 레코드들이 어떤 순서로 복사되든 고리는 예약 순서대로 이어진다.

```text
 백엔드 셋이 거의 동시에 예약 (CurrBytePos = P, PrevBytePos = Q 에서 시작)

 순서  백엔드  size   startbytepos  endbytepos   xl_prev 가 가리키는 곳
 1     A       64     P             P + 64       Q        (A 보다 앞 레코드)
 2     B       3504   P + 64        P + 3568     P        (A)
 3     C       64     P + 3568      P + 3632     P + 64   (B)

 끝난 뒤 CurrBytePos = P + 3632, PrevBytePos = P + 3568
 복사는 [08] 에서 A, B, C 가 동시에 한다. 순서가 정해지는 곳은 여기뿐이다
```

바이트 위치와 LSN 의 차이는 페이지 헤더다. 기본 설정(WAL 세그먼트 16MB, XLOG_BLCKSZ 8192)으로 [08] 의 페이지 경계 예를 계산하면 다음과 같다.

```text
 상수
   SizeOfXLogLongPHD  = 40   (세그먼트 첫 페이지 헤더)
   SizeOfXLogShortPHD = 24   (나머지 페이지)
   UsableBytesInPage  = 8192 - 24 = 8168                                   L598
   UsableBytesInSegment = 2048 * 8168 - (40 - 24) = 16728064 - 16 = 16728048   L4566-L4568
   세그먼트 첫 페이지에 쓸 수 있는 바이트 = 8192 - 40 = 8152

 예약: size 63 -> MAXALIGN 64, 세그먼트 6 의 첫 페이지 안 bytesleft 8112 에서 시작
   startbytepos = 6 * 16728048 + 8112 = 100376400
   endbytepos   = 100376400 + 64      = 100376464

 StartPos = XLogBytePosToRecPtr(100376400)
   bytesleft 8112 < 8152                 -> 첫 페이지 안
   seg_offset = 8112 + 40 = 8152 = 0x1FD8
   LSN = 세그먼트 6 의 시작 0/6000000 + 0x1FD8 = 0/6001FD8

 EndPos = XLogBytePosToEndRecPtr(100376464)
   bytesleft = 8176 >= 8152              -> 첫 페이지를 넘는다
   seg_offset = 8192, bytesleft = 8176 - 8152 = 24
   fullpages = 24 / 8168 = 0, bytesleft = 24
   seg_offset = 8192 + 0 + 24 + 24 = 8240 = 0x2030
   LSN = 0/6002030

 바이트 위치로는 64바이트 차이, LSN 으로는 0x2030 - 0x1FD8 = 88 바이트 차이
   88 = 64 + 다음 페이지 짧은 헤더 24
```

`XLogBytePosToEndRecPtr` 가 따로 있는 이유는 L1894-L1899 주석에 있다. 끝 위치가 페이지 경계에 딱 걸리면, 다음 페이지 헤더 뒤가 아니라 다음 페이지의 시작(헤더 앞)을 돌려준다. 레코드 끝 위치를 LSN 으로 바꿀 때 쓰는 변환이다(L1897-L1898 "used when converting a pointer to the end of a record").

## 결과가 쓰이는 곳

```text
 *StartPos, *EndPos
      --> [08] CopyXLogRecordToWAL 이 그 구간에 복사하고, 끝에서 EndPos 와 맞는지 확인한다 (L1364)
      --> EndPos 가 XLogInsert 의 반환값 = 페이지 LSN
 *PrevPtr -> rechdr->xl_prev
      --> [WAL redo] 의 레코드 읽기가 xl_prev 로 앞 레코드와 이어지는지 확인한다
          (access/transam/xlogreader.c L1179)
 Insert->CurrBytePos
      --> [10] WaitXLogInsertionsToFinish 가 "예약된 끝" 으로 읽는다 (L1529)
```

## 다루지 않는 것

XLOG_SWITCH 의 세그먼트 나머지 예약(`ReserveXLogSwitch`), 반대 방향 변환(`XLogRecPtrToBytePos`), `insertpos_lck` 와 `XLogCtlInsert` 구조체의 배치(캐시 라인 패딩)는 위치 예약의 곁가지라 요약만 했다.
