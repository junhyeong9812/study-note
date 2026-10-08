# 페이지와 튜플 레이아웃

상위: [PostgreSQL 아키텍처 지도](../../README.md)

PostgreSQL 의 테이블 파일과 인덱스 파일은 **8KB 페이지를 이어 붙인 배열**이고, 페이지는 모두 같은 틀의 slotted page 다. 앞에 24바이트 페이지 헤더가 있고, 그 뒤로 4바이트 line pointer(`ItemIdData`) 배열이 아래로 자란다. 튜플은 페이지 끝에서부터 위로 쌓인다. 둘 사이의 빈 공간을 `pd_lower` 와 `pd_upper` 두 오프셋이 가리키고, 맨 끝의 special 영역은 인덱스 같은 접근 방법이 자기 정보를 두는 자리다(heap 은 0 바이트). 튜플을 가리키는 주소 TID 는 `(블록 번호, line pointer 번호)` 다. 바이트 오프셋이 아니라 번호이므로 페이지 안에서 튜플을 옮겨도 TID 는 바뀌지 않는다. heap 튜플은 23바이트 헤더(`HeapTupleHeaderData`)로 시작한다. 헤더에 넣은 트랜잭션(`t_xmin`), 지운 트랜잭션(`t_xmax`), 다음 버전의 위치(`t_ctid`), 상태 비트(`t_infomask`)가 있고, 뒤에 NULL 비트맵과 정렬 패딩, 그리고 열 값이 온다. 이 편은 그 바이트 자리를 소스 상수로 계산해 그림으로 보인다. 튜플이 페이지에 들어가는 길은 [행 쓰기와 WAL 기록](../../flows/heap-insert-wal/README.md)에, 헤더의 xmin/xmax 로 가시성을 판정하는 길은 [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md)에 있다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다. 계산은 기본 블록 크기 `BLCKSZ` 8192 와 64비트 플랫폼의 `MAXIMUM_ALIGNOF` 8 을 쓴다. 바이트 열은 little-endian(x86-64) 기준이다.

## 전체 그림

```text
 heap 페이지 하나 (8192 바이트), 튜플 두 개를 넣은 뒤

 offset
      0  +------------------------------------------------------------+
         | PageHeaderData 24                                          |
         |   pd_lsn 8 | pd_checksum 2 | pd_flags 2 | pd_lower 2 = 32    |
         |   pd_upper 2 = 8128 | pd_special 2 = 8192                  |
         |   pd_pagesize_version 2 = 0x2004 | pd_prune_xid 4          |
     24  +------------------------------------------------------------+
         | lp 1  ItemIdData 4   off 8160, flags NORMAL, len 32        |
     28  | lp 2  ItemIdData 4   off 8128, flags NORMAL, len 28        |
     32  +------------------------------------------------------------+  pd_lower
         |                                                            |
         |              빈 공간  8128 - 32 = 8096 바이트              |
         |      line pointer 는 아래로, 튜플은 위로 자란다            |
         |                                                            |
   8128  +------------------------------------------------------------+  pd_upper
         | 튜플 2  28 바이트 + 패딩 4 (MAXALIGN)                      |
   8160  +------------------------------------------------------------+
         | 튜플 1  32 바이트                                          |
   8192  +------------------------------------------------------------+  pd_special = BLCKSZ
         | special 영역 0 바이트 (heap). nbtree 면 BTPageOpaqueData   |
         +------------------------------------------------------------+

 TID (0,2) -> 블록 0 을 읽고 -> pd_linp[2-1] = lp 2 -> page + 8128 에서 28 바이트
```

```text
 heap 튜플 하나 (위 튜플 1: id int4 = 1, name text = 'abc', NULL 없음)

 offset (튜플 시작 기준)
      0  +-------------------+-------------------+------------------------+
         | t_xmin 4          | t_xmax 4          | t_cid / t_xvac 4       |  t_choice.t_heap 12
     12  +-------------------+-------------------+------------------------+
         | t_ctid 6  (bi_hi 2, bi_lo 2, ip_posid 2)                       |
     18  +--------------------+-------------------+-----------+-----------+
         | t_infomask2 2      | t_infomask 2      | t_hoff 1  | t_bits    |
     23  +--------------------+-------------------+-----------+-----------+
         |  SizeofHeapTupleHeader = 23. NULL 비트맵이 여기서 시작한다      |
     24  +----------------------------------------------------------------+  t_hoff = 24
         | 열 값: id 4 바이트, name 1 바이트 헤더 + 'abc'                 |
     32  +----------------------------------------------------------------+  t_len = 32
```

## 페이지 헤더 - PageHeaderData

헤더는 모든 종류의 페이지(heap, nbtree, hash, GiST ...)가 같이 쓴다. 머리 주석의 그림이 slotted page 모양을 그대로 보여 준다.

`include` / `storage` / `bufpage.h` L25-L48 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/bufpage.h#L25-L48))

```c
// storage/bufpage.h L25-L48
/*
 * A postgres disk page is an abstraction layered on top of a postgres
 * disk block (which is simply a unit of i/o, see block.h).
 *
 * specifically, while a disk block can be unformatted, a postgres
 * disk page is always a slotted page of the form:
 *
 * +----------------+---------------------------------+
 * | PageHeaderData | linp1 linp2 linp3 ...           |
 * +-----------+----+---------------------------------+
 * | ... linpN |									  |
 * +-----------+--------------------------------------+
 * |		   ^ pd_lower							  |
 * |												  |
 * |			 v pd_upper							  |
 * +-------------+------------------------------------+
 * |			 | tupleN ...                         |
 * +-------------+------------------+-----------------+
 * |	   ... tuple3 tuple2 tuple1 | "special space" |
 * +--------------------------------+-----------------+
 *									^ pd_special
 *
 * a page is full when nothing can be added between pd_lower and
 * pd_upper.
```

`include` / `storage` / `bufpage.h` L159-L172 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/bufpage.h#L159-L172))

```c
// storage/bufpage.h L159-L172
typedef struct PageHeaderData
{
	/* XXX LSN is member of *any* block, not only page-organized ones */
	PageXLogRecPtr pd_lsn;		/* LSN: next byte after last byte of xlog
								 * record for last change to this page */
	uint16		pd_checksum;	/* checksum */
	uint16		pd_flags;		/* flag bits, see below */
	LocationIndex pd_lower;		/* offset to start of free space */
	LocationIndex pd_upper;		/* offset to end of free space */
	LocationIndex pd_special;	/* offset to start of special space */
	uint16		pd_pagesize_version;
	TransactionId pd_prune_xid; /* oldest prunable XID, or zero if none */
	ItemIdData	pd_linp[FLEXIBLE_ARRAY_MEMBER]; /* line pointer array */
} PageHeaderData;
```

```text
 PageHeaderData 필드 (offsetof 로 확인, sizeof = SizeOfPageHeaderData = 24)

 offset  size  field                 값의 뜻
 ------  ----  --------------------  -----------------------------------------------
      0     8  pd_lsn                이 페이지를 마지막으로 바꾼 WAL 레코드의 끝 + 1
                                     xlogid(상위 4) + xrecoff(하위 4) 두 uint32 로 나눠 저장
      8     2  pd_checksum           데이터 체크섬. 디스크에 쓸 때 채운다
     10     2  pd_flags              PD_HAS_FREE_LINES 0x1, PD_PAGE_FULL 0x2, PD_ALL_VISIBLE 0x4
     12     2  pd_lower              빈 공간의 시작 = line pointer 배열의 끝
     14     2  pd_upper              빈 공간의 끝 = 가장 앞 튜플의 시작
     16     2  pd_special            special 영역의 시작
     18     2  pd_pagesize_version   페이지 크기 | 레이아웃 버전 = 8192 | 4 = 0x2004
     20     4  pd_prune_xid          정리(prune)할 만한 가장 오래된 xid. 힌트
     24     -  pd_linp[]             line pointer 배열 (헤더 크기에는 넣지 않는다)

 빈 공간 = pd_upper - pd_lower
 불변식  SizeOfPageHeaderData <= pd_lower <= pd_upper <= pd_special <= BLCKSZ
         어기면 PageAddItemExtended 가 PANIC (storage/page/bufpage.c L210-L217)
```

`pd_lsn` 이 WAL 규칙의 열쇠다. 더러운 버퍼는 WAL 이 적어도 그 페이지의 LSN 까지 flush 되기 전에는 디스크에 나갈 수 없다(bufpage.h L128-L130 주석). 이 검사는 [버퍼 관리](../../flows/buffer-manager/README.md)의 `FlushBuffer` 가 한다. 체크섬은 버퍼에 있는 동안에는 채우지 않고, `FlushBuffer` 가 쓰기 직전에 `PageSetChecksumCopy`(bufmgr.c L4386)로 계산한다. 페이지 크기와 버전을 한 필드에 넣는 것은 7.3 이전 페이지를 버전 0 으로 읽기 위해서다. 그래서 페이지 크기는 256 의 배수여야 하고, `lp_off` 와 `lp_len` 이 15비트라 32KB 를 넘을 수 없다(L145-L155 주석).

`include` / `storage` / `bufpage.h` L188-L193 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/bufpage.h#L188-L193))

```c
// storage/bufpage.h L188-L193
#define PD_HAS_FREE_LINES	0x0001	/* are there any unused line pointers? */
#define PD_PAGE_FULL		0x0002	/* not enough free space for new tuple? */
#define PD_ALL_VISIBLE		0x0004	/* all tuples on page are visible to
									 * everyone */

#define PD_VALID_FLAG_BITS	0x0007	/* OR of all valid pd_flags bits */
```

`include` / `storage` / `bufpage.h` L300-L307 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/bufpage.h#L300-L307))

```c
// storage/bufpage.h L300-L307
static inline void
PageSetPageSizeAndVersion(Page page, Size size, uint8 version)
{
	Assert((size & 0xFF00) == size);
	Assert((version & 0x00FF) == version);

	((PageHeader) page)->pd_pagesize_version = size | version;
}
```

새 페이지는 `PageInit` 이 만든다. heap 은 special 크기 0 으로 부른다(access/heap/hio.c L363, L698).

`storage` / `page` / `bufpage.c` L42-L60 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/page/bufpage.c#L42-L60))

```c
// storage/page/bufpage.c L42-L60
PageInit(Page page, Size pageSize, Size specialSize)
{
	PageHeader	p = (PageHeader) page;

	specialSize = MAXALIGN(specialSize);

	Assert(pageSize == BLCKSZ);
	Assert(pageSize > specialSize + SizeOfPageHeaderData);

	/* Make sure all fields of page are zero, as well as unused space */
	MemSet(p, 0, pageSize);

	p->pd_flags = 0;
	p->pd_lower = SizeOfPageHeaderData;
	p->pd_upper = pageSize - specialSize;
	p->pd_special = pageSize - specialSize;
	PageSetPageSizeAndVersion(page, pageSize, PG_PAGE_LAYOUT_VERSION);
	/* p->pd_prune_xid = InvalidTransactionId;		done by above MemSet */
}
```

```text
 PageInit(page, 8192, 0) 직후

 pd_lower   = SizeOfPageHeaderData = 24
 pd_upper   = 8192 - MAXALIGN(0)   = 8192
 pd_special = 8192
 pd_pagesize_version = 8192 | 4    = 0x2004   바이트로 04 20
 나머지 0. 빈 공간 = 8192 - 24 = 8168
```

## line pointer - ItemIdData

line pointer 는 4바이트 하나에 세 값을 비트필드로 넣는다. 오프셋 15비트, 상태 2비트, 길이 15비트다. 비트필드의 실제 비트 순서는 컴파일러가 정한다. x86-64 gcc 에서는 앞의 필드가 낮은 비트에 놓인다(아래 값은 이 태그의 헤더로 컴파일해 확인했다).

`include` / `storage` / `itemid.h` L25-L41 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/itemid.h#L25-L41))

```c
// storage/itemid.h L25-L41
typedef struct ItemIdData
{
	unsigned	lp_off:15,		/* offset to tuple (from start of page) */
				lp_flags:2,		/* state of line pointer, see below */
				lp_len:15;		/* byte length of tuple */
} ItemIdData;

typedef ItemIdData *ItemId;

/*
 * lp_flags has these possible states.  An UNUSED line pointer is available
 * for immediate re-use, the other states are not.
 */
#define LP_UNUSED		0		/* unused (should always have lp_len=0) */
#define LP_NORMAL		1		/* used (should always have lp_len>0) */
#define LP_REDIRECT		2		/* HOT redirect (should have lp_len=0) */
#define LP_DEAD			3		/* dead, may or may not have storage */
```

```text
 ItemIdData 4 바이트의 비트 배치 (x86-64 gcc, uint32 로 읽었을 때)

  31                         17 16 15 14                            0
 +-----------------------------+-----+-------------------------------+
 |        lp_len (15)          |flags|          lp_off (15)          |
 +-----------------------------+-----+-------------------------------+

 lp 1 = off 8160, flags LP_NORMAL(1), len 32
      = 8160 | 1 << 15 | 32 << 17
      = 0x1FE0 | 0x8000 | 0x400000      = 0x00409FE0
      메모리 바이트  e0 9f 40 00
 lp 2 = off 8128, flags 1, len 28
      = 0x1FC0 | 0x8000 | 0x380000      = 0x00389FC0
      메모리 바이트  c0 9f 38 00

 lp_flags 의 네 상태
   0 LP_UNUSED    비어 있다. 재사용 가능. lp_len 0
   1 LP_NORMAL    튜플이 있다. lp_off, lp_len 이 그 자리
   2 LP_REDIRECT  HOT 체인의 다음 line pointer 번호를 lp_off 에 담는다. lp_len 0
   3 LP_DEAD      죽었다. 저장 공간이 있을 수도 없을 수도 있다
```

line pointer 번호는 1 부터 센다(`FirstOffsetNumber`). TID 의 두 번째 값이 이 번호이고, 페이지 안 주소는 `pd_linp[번호 - 1]` 의 `lp_off` 다. 그래서 vacuum 이나 페이지 정리가 튜플을 옮겨 빈칸을 모아도 line pointer 의 `lp_off` 만 고치면 되고 TID 는 그대로다(bufpage.h L64-L70 주석).

## 튜플이 들어가는 자리 - PageAddItemExtended

빈 line pointer 를 찾거나 배열 끝에 하나를 붙이고, 튜플 크기를 MAXALIGN 해 `pd_upper` 에서 뺀다. `lower > upper` 면 자리가 없다. 넣는 일 전체는 [행 쓰기와 WAL 기록](../../flows/heap-insert-wal/README.md)의 `RelationPutHeapTuple` 이 부른다.

`storage` / `page` / `bufpage.c` L303-L355 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/page/bufpage.c#L303-L355))

```c
// storage/page/bufpage.c L303-L355
	/*
	 * Compute new lower and upper pointers for page, see if it'll fit.
	 *
	 * Note: do arithmetic as signed ints, to avoid mistakes if, say,
	 * alignedSize > pd_upper.
	 */
	if (offsetNumber == limit || needshuffle)
		lower = phdr->pd_lower + sizeof(ItemIdData);
	else
		lower = phdr->pd_lower;

	alignedSize = MAXALIGN(size);

	upper = (int) phdr->pd_upper - (int) alignedSize;

	if (lower > upper)
		return InvalidOffsetNumber;

// ... (L321-L346 생략: line pointer 를 옮기고(needshuffle), ItemIdSetNormal(itemId, upper, size) 로 채우고, Valgrind 검사)
	/* copy the item's data onto the page */
	memcpy((char *) page + upper, item, size);

	/* adjust page header */
	phdr->pd_lower = (LocationIndex) lower;
	phdr->pd_upper = (LocationIndex) upper;

	return offsetNumber;
}
```

```text
 빈 페이지에 튜플 둘을 넣을 때의 pd_lower / pd_upper

 step             pd_lower       pd_upper                     line pointer
 PageInit         24             8192
 tuple 1, len 32  24 + 4 = 28    8192 - MAXALIGN(32) = 8160   lp 1 = (8160, NORMAL, 32)
 tuple 2, len 28  28 + 4 = 32    8160 - MAXALIGN(28) = 8128   lp 2 = (8128, NORMAL, 28)

 lp_len 은 MAXALIGN 전의 길이(28)이고, 자리는 MAXALIGN 한 크기(32)만큼 잡는다
 남는 4 바이트(8156..8159)는 PageInit 의 MemSet 이 남긴 0 이다
```

```text
 한 페이지의 상한

 MaxHeapTupleSize     = BLCKSZ - MAXALIGN(SizeOfPageHeaderData + sizeof(ItemIdData))
                      = 8192 - MAXALIGN(24 + 4) = 8192 - 32 = 8160
 MaxHeapTuplesPerPage = (BLCKSZ - SizeOfPageHeaderData) / (MAXALIGN(23) + 4)
                      = (8192 - 24) / (24 + 4) = 8168 / 28 = 291
                        열이 하나도 없는 가장 작은 튜플(24) 만 넣어도 291 개가 끝이다
```

`include` / `access` / `htup_details.h` L615-L616 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L615-L616))

```c
// access/htup_details.h L615-L616
#define MaxHeapTupleSize  (BLCKSZ - MAXALIGN(SizeOfPageHeaderData + sizeof(ItemIdData)))
#define MinHeapTupleSize  MAXALIGN(SizeofHeapTupleHeader)
```

`include` / `access` / `htup_details.h` L629-L631 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L629-L631))

```c
// access/htup_details.h L629-L631
#define MaxHeapTuplesPerPage	\
	((int) ((BLCKSZ - SizeOfPageHeaderData) / \
			(MAXALIGN(SizeofHeapTupleHeader) + sizeof(ItemIdData))))
```

## 튜플 헤더 - HeapTupleHeaderData

헤더는 23바이트다. 앞 12바이트는 디스크의 튜플이면 트랜잭션 정보(`HeapTupleFields`), 메모리의 복합값 Datum 이면 길이와 타입(`DatumTupleFields`)인 union 이다. 테이블에 넣기 직전에 트랜잭션 정보가 Datum 정보를 덮어쓴다(htup_details.h L56-L63 주석).

`include` / `access` / `htup_details.h` L122-L132 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L122-L132))

```c
// access/htup_details.h L122-L132
typedef struct HeapTupleFields
{
	TransactionId t_xmin;		/* inserting xact ID */
	TransactionId t_xmax;		/* deleting or locking xact ID */

	union
	{
		CommandId	t_cid;		/* inserting or deleting command ID, or both */
		TransactionId t_xvac;	/* old-style VACUUM FULL xact ID */
	}			t_field3;
} HeapTupleFields;
```

`include` / `access` / `htup_details.h` L153-L185 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L153-L185))

```c
// access/htup_details.h L153-L185
struct HeapTupleHeaderData
{
	union
	{
		HeapTupleFields t_heap;
		DatumTupleFields t_datum;
	}			t_choice;

	ItemPointerData t_ctid;		/* current TID of this or newer tuple (or a
								 * speculative insertion token) */

	/* Fields below here must match MinimalTupleData! */

#define FIELDNO_HEAPTUPLEHEADERDATA_INFOMASK2 2
	uint16		t_infomask2;	/* number of attributes + various flags */

#define FIELDNO_HEAPTUPLEHEADERDATA_INFOMASK 3
	uint16		t_infomask;		/* various flag bits, see below */

#define FIELDNO_HEAPTUPLEHEADERDATA_HOFF 4
	uint8		t_hoff;			/* sizeof header incl. bitmap, padding */

	/* ^ - 23 bytes - ^ */

#define FIELDNO_HEAPTUPLEHEADERDATA_BITS 5
	bits8		t_bits[FLEXIBLE_ARRAY_MEMBER];	/* bitmap of NULLs */

	/* MORE DATA FOLLOWS AT END OF STRUCT */
};

/* typedef appears in htup.h */

#define SizeofHeapTupleHeader offsetof(HeapTupleHeaderData, t_bits)
```

```text
 HeapTupleHeaderData 필드 (offsetof 로 확인)

 offset  size  field          값의 뜻
 ------  ----  -------------  ------------------------------------------------------
      0     4  t_xmin         넣은 트랜잭션 xid
      4     4  t_xmax         지우거나 잠근 트랜잭션 xid. 없으면 0 (HEAP_XMAX_INVALID 와 함께)
      8     4  t_cid          넣거나 지운 명령 번호 (cmin, cmax, 둘 다면 combo CID)
                 / t_xvac     옛 VACUUM FULL 의 xid. t_cid 와 자리를 같이 쓴다
     12     6  t_ctid         이 버전 또는 더 새 버전의 TID (블록 4 + line pointer 번호 2)
     18     2  t_infomask2    하위 11비트 = 열 수, 상위 3비트 = HOT, key 갱신 표시
     20     2  t_infomask     NULL 유무, 가변 길이 유무, xmin/xmax 상태 힌트 비트
     22     1  t_hoff         헤더 + 비트맵 + 패딩의 길이 = 열 값이 시작하는 오프셋
     23     -  t_bits[]       NULL 비트맵 (HEAP_HASNULL 일 때만)

 가상 필드 다섯(xmin, cmin, xmax, cmax, xvac)을 물리 필드 셋에 담는다
 cmin 과 cmax 는 넣고 지운 트랜잭션 자신에게만 의미가 있어서 한 칸을 같이 쓴다
 (htup_details.h L73-L84 주석)
```

`t_ctid` 는 버전 사슬의 고리다. 튜플을 처음 저장하면 자기 TID 를 넣고(access/heap/hio.c L80), UPDATE 되면 새 버전의 TID 로 바뀐다. 그래서 `t_xmax` 가 비어 있거나 `t_ctid` 가 자기 자신을 가리키면 그 행의 최신 버전이다(htup_details.h L86-L94 주석).

`ItemPointerData` 는 6바이트에 맞추려고 packed 로 선언했다. 블록 번호를 `uint16` 둘로 나눈 것도 4바이트 정렬을 피하려는 것이다.

`include` / `storage` / `itemptr.h` L36-L47 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/itemptr.h#L36-L47))

```c
// storage/itemptr.h L36-L47
typedef struct ItemPointerData
{
	BlockIdData ip_blkid;
	OffsetNumber ip_posid;
}

/* If compiler understands packed and aligned pragmas, use those */
#if defined(pg_attribute_packed) && defined(pg_attribute_aligned)
			pg_attribute_packed()
			pg_attribute_aligned(2)
#endif
ItemPointerData;
```

`include` / `storage` / `block.h` L53-L57 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/block.h#L53-L57))

```c
// storage/block.h L53-L57
typedef struct BlockIdData
{
	uint16		bi_hi;
	uint16		bi_lo;
} BlockIdData;
```

## NULL 비트맵과 t_hoff

NULL 이 하나라도 있으면 23번째 바이트부터 비트맵이 온다. 열 하나에 1비트이고, **비트가 1 이면 NULL 이 아니다.** 비트맵 뒤를 MAXALIGN 으로 올린 자리가 `t_hoff`, 즉 첫 열 값의 자리다.

`access` / `common` / `heaptuple.c` L1151-L1156 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/common/heaptuple.c#L1151-L1156))

```c
// access/common/heaptuple.c L1151-L1156
	len = offsetof(HeapTupleHeaderData, t_bits);

	if (hasnull)
		len += BITMAPLEN(numberOfAttributes);

	hoff = len = MAXALIGN(len); /* align user data safely */
```

`include` / `access` / `htup_details.h` L598-L602 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L598-L602))

```c
// access/htup_details.h L598-L602
static inline int
BITMAPLEN(int NATTS)
{
	return (NATTS + 7) / 8;
}
```

`access` / `common` / `heaptuple.c` L290-L307 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/common/heaptuple.c#L290-L307))

```c
// access/common/heaptuple.c L290-L307
	if (bit != NULL)
	{
		if (*bitmask != HIGHBIT)
			*bitmask <<= 1;
		else
		{
			*bit += 1;
			**bit = 0x0;
			*bitmask = 1;
		}

		if (isnull)
		{
			*infomask |= HEAP_HASNULL;
			return;
		}

		**bit |= *bitmask;
```

`include` / `access` / `tupmacs.h` L20-L29 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/tupmacs.h#L20-L29))

```c
// access/tupmacs.h L20-L29
/*
 * Check a tuple's null bitmap to determine whether the attribute is null.
 * Note that a 0 in the null bitmap indicates a null, while 1 indicates
 * non-null.
 */
static inline bool
att_isnull(int ATT, const bits8 *BITS)
{
	return !(BITS[ATT >> 3] & (1 << (ATT & 0x07)));
}
```

```text
 열 수에 따른 t_hoff (MAXALIGN 8)

 nulls  columns     23 + BITMAPLEN    MAXALIGN = t_hoff   비고
 no     any         23                24
 yes    1 .. 8      23 + 1 = 24       24                  비트맵이 헤더의 패딩 1 바이트에 들어간다
 yes    9 .. 72     23 + 2..9         32
 yes    73 .. 136   23 + 10..17       40

 열 8 개까지는 NULL 비트맵이 공짜다. 23 바이트 헤더의 남는 1 바이트가 그 자리다
```

```text
 튜플 2 의 비트맵 (id = 2, name = NULL, 열 2 개)

 fill_val 이 열마다 bitmask 를 1, 2, 4 ... 로 민다
   id    (열 0) NULL 아님   t_bits[0] |= 0x01
   name  (열 1) NULL        비트를 세우지 않고 t_infomask |= HEAP_HASNULL
 t_bits[0] = 0x01 = 0000 0001
   bit 0  열 0 (id)    1   값 있음
   bit 1  열 1 (name)  0   NULL
 att_isnull(1, t_bits) = !(0x01 & (1 << 1)) = true
```

## t_infomask 와 t_infomask2 의 비트

`t_infomask` 의 하위 4비트는 튜플 모양(NULL, 가변 길이, 외부 저장)이고, 상위 12비트(`HEAP_XACT_MASK` 0xFFF0)는 트랜잭션 상태다. 상태 비트 중 `XMIN_COMMITTED` 같은 것은 **힌트**다. 가시성 판정이 pg_xact 를 한 번 읽고 결과를 여기에 적어 두면, 다음 판정은 pg_xact 를 다시 보지 않는다.

`include` / `access` / `htup_details.h` L187-L219 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L187-L219))

```c
// access/htup_details.h L187-L219
/*
 * information stored in t_infomask:
 */
#define HEAP_HASNULL			0x0001	/* has null attribute(s) */
#define HEAP_HASVARWIDTH		0x0002	/* has variable-width attribute(s) */
#define HEAP_HASEXTERNAL		0x0004	/* has external stored attribute(s) */
#define HEAP_HASOID_OLD			0x0008	/* has an object-id field */
#define HEAP_XMAX_KEYSHR_LOCK	0x0010	/* xmax is a key-shared locker */
#define HEAP_COMBOCID			0x0020	/* t_cid is a combo CID */
#define HEAP_XMAX_EXCL_LOCK		0x0040	/* xmax is exclusive locker */
#define HEAP_XMAX_LOCK_ONLY		0x0080	/* xmax, if valid, is only a locker */

 /* xmax is a shared locker */
#define HEAP_XMAX_SHR_LOCK	(HEAP_XMAX_EXCL_LOCK | HEAP_XMAX_KEYSHR_LOCK)

#define HEAP_LOCK_MASK	(HEAP_XMAX_SHR_LOCK | HEAP_XMAX_EXCL_LOCK | \
						 HEAP_XMAX_KEYSHR_LOCK)
#define HEAP_XMIN_COMMITTED		0x0100	/* t_xmin committed */
#define HEAP_XMIN_INVALID		0x0200	/* t_xmin invalid/aborted */
#define HEAP_XMIN_FROZEN		(HEAP_XMIN_COMMITTED|HEAP_XMIN_INVALID)
#define HEAP_XMAX_COMMITTED		0x0400	/* t_xmax committed */
#define HEAP_XMAX_INVALID		0x0800	/* t_xmax invalid/aborted */
#define HEAP_XMAX_IS_MULTI		0x1000	/* t_xmax is a MultiXactId */
#define HEAP_UPDATED			0x2000	/* this is UPDATEd version of row */
#define HEAP_MOVED_OFF			0x4000	/* moved to another place by pre-9.0
										 * VACUUM FULL; kept for binary
										 * upgrade support */
#define HEAP_MOVED_IN			0x8000	/* moved from another place by pre-9.0
										 * VACUUM FULL; kept for binary
										 * upgrade support */
#define HEAP_MOVED (HEAP_MOVED_OFF | HEAP_MOVED_IN)

#define HEAP_XACT_MASK			0xFFF0	/* visibility-related bits */
```

`include` / `access` / `htup_details.h` L288-L298 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/htup_details.h#L288-L298))

```c
// access/htup_details.h L288-L298
/*
 * information stored in t_infomask2:
 */
#define HEAP_NATTS_MASK			0x07FF	/* 11 bits for number of attributes */
/* bits 0x1800 are available */
#define HEAP_KEYS_UPDATED		0x2000	/* tuple was updated and key cols
										 * modified, or tuple deleted */
#define HEAP_HOT_UPDATED		0x4000	/* tuple was HOT-updated */
#define HEAP_ONLY_TUPLE			0x8000	/* this is heap-only tuple */

#define HEAP2_XACT_MASK			0xE000	/* visibility-related bits */
```

```text
 t_infomask (16 비트)

 bit  값      이름                    뜻
  0   0x0001  HEAP_HASNULL            NULL 열이 있다 -> t_bits 가 있다
  1   0x0002  HEAP_HASVARWIDTH        가변 길이 열이 있다
  2   0x0004  HEAP_HASEXTERNAL        TOAST 로 밖에 둔 열이 있다
  3   0x0008  HEAP_HASOID_OLD         옛 OID 열 (더는 만들지 않는다)
  4   0x0010  HEAP_XMAX_KEYSHR_LOCK   xmax 는 FOR KEY SHARE 잠금
  5   0x0020  HEAP_COMBOCID           t_cid 는 combo CID
  6   0x0040  HEAP_XMAX_EXCL_LOCK     xmax 는 배타 잠금
  7   0x0080  HEAP_XMAX_LOCK_ONLY     xmax 는 잠그기만 했다 (지우지 않았다)
              0x0050  = SHR_LOCK      KEYSHR | EXCL 둘 다면 FOR SHARE
  8   0x0100  HEAP_XMIN_COMMITTED     xmin 커밋됨 (힌트)
  9   0x0200  HEAP_XMIN_INVALID       xmin 중단됨 (힌트)
              0x0300  = XMIN_FROZEN   둘 다면 동결: 모든 스냅샷에 보인다
 10   0x0400  HEAP_XMAX_COMMITTED     xmax 커밋됨 (힌트)
 11   0x0800  HEAP_XMAX_INVALID       xmax 없음 또는 중단됨
 12   0x1000  HEAP_XMAX_IS_MULTI      xmax 는 MultiXactId
 13   0x2000  HEAP_UPDATED            UPDATE 로 생긴 새 버전
 14   0x4000  HEAP_MOVED_OFF          9.0 이전 VACUUM FULL 의 흔적 (업그레이드 호환)
 15   0x8000  HEAP_MOVED_IN           "

 t_infomask2 (16 비트)

 bit    값      이름                  뜻
 0-10   0x07FF  HEAP_NATTS_MASK       열 수 (최대 2047, 실제 상한은 MaxTupleAttributeNumber 1664)
 11-12  0x1800                        비어 있다
 13     0x2000  HEAP_KEYS_UPDATED     지워졌거나 key 열이 바뀐 UPDATE
 14     0x4000  HEAP_HOT_UPDATED      HOT 갱신됐다 (새 버전이 같은 페이지, 인덱스 그대로)
 15     0x8000  HEAP_ONLY_TUPLE       HOT 로 생긴 버전. 인덱스가 직접 가리키지 않는다
```

INSERT 는 상태 비트를 모두 지우고 `HEAP_XMAX_INVALID` 하나만 세운다. xmin 에 자기 xid, cmin 에 명령 번호, xmax 에 0 을 넣는다.

`access` / `heap` / `heapam.c` L2312-L2320 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/heap/heapam.c#L2312-L2320))

```c
// access/heap/heapam.c L2312-L2320
	tup->t_data->t_infomask &= ~(HEAP_XACT_MASK);
	tup->t_data->t_infomask2 &= ~(HEAP2_XACT_MASK);
	tup->t_data->t_infomask |= HEAP_XMAX_INVALID;
	HeapTupleHeaderSetXmin(tup->t_data, xid);
	if (options & HEAP_INSERT_FROZEN)
		HeapTupleHeaderSetXminFrozen(tup->t_data);

	HeapTupleHeaderSetCmin(tup->t_data, cid);
	HeapTupleHeaderSetXmax(tup->t_data, 0); /* for cleanliness */
```

## 예시 - 행 두 개의 바이트

같은 트랜잭션(xid 1000)이 `CREATE TABLE t (id int4, name text)` 에 두 문장으로 넣은 결과다. 첫 문장이 명령 번호를 썼으므로 문장 사이의 `CommandCounterIncrement` 가 번호를 올려 두 번째 문장은 cid 1 이다(access/transam/xact.c L1108-L1120). 블록 0 의 첫 두 튜플이다.

```text
 INSERT INTO t VALUES (1, 'abc');   -- 튜플 1, page + 8160, t_len 32

 +0   e8 03 00 00   t_xmin   1000
 +4   00 00 00 00   t_xmax   0
 +8   00 00 00 00   t_cid    0
 +12  00 00 00 00   t_ctid   블록 0 (bi_hi 0, bi_lo 0)
 +16  01 00                  line pointer 1
 +18  02 00         t_infomask2  열 2 개
 +20  02 08         t_infomask   0x0802 = HASVARWIDTH | XMAX_INVALID
 +22  18            t_hoff   24
 +23  00            (비트맵 없음, 패딩)
 +24  01 00 00 00   id = 1       int4, 4 바이트 정렬 자리
 +28  09            name 의 1 바이트 varlena 헤더 = (4 << 1) | 1, 길이 4 (헤더 포함)
 +29  61 62 63      'abc'
 = 32

 INSERT INTO t VALUES (2, NULL);    -- 튜플 2, page + 8128, t_len 28

 +0   e8 03 00 00   t_xmin   1000
 +4   00 00 00 00   t_xmax   0
 +8   01 00 00 00   t_cid    1
 +12  00 00 00 00   t_ctid   블록 0
 +16  02 00                  line pointer 2
 +18  02 00         t_infomask2  열 2 개
 +20  01 08         t_infomask   0x0801 = HASNULL | XMAX_INVALID
 +22  18            t_hoff   24
 +23  01            t_bits[0]    열 0 값 있음, 열 1 NULL
 +24  02 00 00 00   id = 2
 = 28    (name 은 NULL 이라 바이트가 없고 HASVARWIDTH 도 서지 않는다)
```

계산의 근거는 이렇다. `heap_form_tuple` 이 `t_hoff` 를 정하고(heaptuple.c L1151-L1156), `fill_val` 이 값을 채운다. `text` 는 4바이트 헤더 varlena 로 오지만, 저장 방식이 PLAIN 이 아니라서(`attispackable`, access/common/tupdesc.c L74) 1바이트 헤더로 줄여 넣는다. 이때 정렬하지 않는다(heaptuple.c `fill_val` 의 `VARATT_CAN_MAKE_SHORT` 분기). 1바이트 헤더의 값은 little-endian 에서 `(len << 1) | 0x01` 이다(include/varatt.h L236-L237). `t_ctid` 는 `RelationPutHeapTuple` 이 자리를 받은 뒤 `(0, 1)`, `(0, 2)` 로 채운다. 이 트랜잭션이 커밋된 뒤 누군가 튜플 1 을 읽으면 가시성 판정이 `HEAP_XMIN_COMMITTED` 를 세워 `t_infomask` 는 0x0902 가 된다.

## db-engine 에서는

db-engine 의 페이지는 4096바이트 배열이고 공통 헤더가 없다. 06-01 의 `TableHeap` 이 그 위에 자기 틀을 얹는다. 앞 8바이트에 튜플 수와 다음 쓰기 자리를 두고, 튜플을 `[길이 4][바이트]` 로 앞에서부터 이어 붙인다. 튜플 형식은 04-01 의 `Tuple.encode` 다.

```text
 같은 문제(행을 고정 크기 페이지에 담기), 두 구현 (위 PostgreSQL / 아래 db-engine)

 페이지 틀
   PostgreSQL  24 B 공통 헤더 + line pointer 배열(앞) + 튜플(뒤에서부터) + special
   db-engine   [tupleCount 4][freeOffset 4][len 4][tuple][len 4][tuple]...  앞에서부터 append

 행 주소
   PostgreSQL  TID = (블록, line pointer 번호). 튜플이 페이지 안에서 옮겨져도 그대로
   db-engine   (페이지, 순서). 페이지 안 재배치와 빈칸 재사용이 없다 (slot directory 미채택)

 행 헤더
   PostgreSQL  23 B: t_xmin, t_xmax, t_cid, t_ctid, t_infomask2, t_infomask, t_hoff
   db-engine   없음. 버전 정보는 행에 붙지 않는다

 NULL 표시
   PostgreSQL  비트맵 ceil(N/8) B, NULL 이 하나라도 있을 때만. 비트 1 = 값 있음
   db-engine   비트맵 ceil(N/8) B, 항상. 비트 1 = NULL

 값의 모양
   PostgreSQL  타입 정렬(int4 는 4 B 경계), 짧은 문자열은 1 B 헤더, 바이트 순서는 CPU 그대로
   db-engine   ByteBuffer 기본 big-endian, INT 4 B, STRING = 길이 4 B + UTF-8, 정렬 없음

 큰 행
   PostgreSQL  TOAST 로 밖에 둔다 (MaxHeapTupleSize 8160)
   db-engine   페이지보다 크면 거부 (06-01 의 CI-4)
```

db-engine 04-01 이 "값 자리를 비우면 그 뒤 컬럼의 위치가 밀린다. 그래서 **NULL bitmap**을 맨 앞에 둔다." 고 적은 자리를 PostgreSQL 도 같은 방법으로 푼다. 다른 점은 비트의 뜻이 반대라는 것, NULL 이 없으면 비트맵을 아예 두지 않는다는 것, 그리고 열 8 개까지는 헤더의 패딩 1 바이트에 넣어 공간을 쓰지 않는다는 것이다. 페이지 쪽에서는 db-engine 02-01 이 페이지 안에 "내가 누구인가" 를 적지 않는 반면, PostgreSQL 은 `pd_lsn` 과 `pd_checksum` 을 모든 페이지에 둔다. 챕터: [02-01-page-pagedfile](../../../../../project/db-engine/02-01-page-pagedfile/), [04-01-catalog](../../../../../project/db-engine/04-01-catalog/), 비교에 쓴 다른 장은 [06-01-table-seqscan](../../../../../project/db-engine/06-01-table-seqscan/).

## 어디에서 쓰이는가

```text
 [행 쓰기와 WAL 기록]    heap_prepare_insert 가 헤더를 채우고 RelationPutHeapTuple -> PageAddItem
                         WAL 레코드에 넣는 것은 t_infomask2, t_infomask, t_hoff 와 데이터 (xl_heap_header)
 [MVCC 가시성과 스냅샷]  page_collect_tuples 가 lp 를 훑고 HeapTupleSatisfiesMVCC 가 t_xmin, t_xmax,
                         t_infomask 의 힌트 비트를 본다
 [버퍼 관리]             FlushBuffer 가 pd_lsn 까지 XLogFlush 하고 체크섬을 채워 쓴다
 [nbtree 삽입과 분할]    같은 PageHeaderData 와 line pointer 위에 IndexTuple, special 에 BTPageOpaqueData
 [vacuum]                LP_DEAD, LP_REDIRECT, LP_UNUSED 로 line pointer 를 바꾼다. pruning 이 pd_prune_xid 를 다시 정한다
```

흐름 문서: [행 쓰기와 WAL 기록](../../flows/heap-insert-wal/README.md), [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md), [버퍼 관리](../../flows/buffer-manager/README.md), [nbtree 삽입과 분할](../../flows/nbtree-insert/README.md), [vacuum](../../flows/vacuum/README.md). 이 페이지가 메모리에 올라오는 자리는 [공유 메모리](../shared-memory/README.md)의 버퍼 풀이다.

## 다루지 않는 것

TOAST 의 외부 저장 형식(`varatt_external`, `TOAST_TUPLE_THRESHOLD`)과 압축, `MinimalTuple`(executor 의 헤더 없는 튜플), 인덱스 튜플(`IndexTupleData`)과 nbtree special 영역의 필드, HOT 체인의 따라가기와 page pruning(`heap_page_prune_and_freeze`), 동결(freeze)과 `HEAP_XMIN_FROZEN` 을 세우는 조건, MultiXact 의 구조, combo CID 의 대응표(`combocid.c`), 체크섬 알고리즘(`pg_checksum_page`), visibility map 과 free space map 의 페이지 형식, 열의 정렬 규칙 전체(`att_align_nominal`, `typalign`)는 같은 뼈대의 곁가지라 요약만 했다.
