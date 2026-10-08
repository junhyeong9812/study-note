# 테이블스페이스와 페이지 레이아웃

상위: [MySQL 아키텍처 지도](../../README.md)

InnoDB 가 디스크에 두는 데이터 파일(`.ibd`, 시스템 테이블스페이스, undo 테이블스페이스)은 **모두 같은 크기의 페이지를 이어 붙인 배열**이다. 페이지 번호에 페이지 크기를 곱하면 파일 안의 바이트 위치가 나온다. 그 위에 두 겹의 묶음이 있다. 연속한 페이지 64개(16KB 페이지 기준 1MB)가 **익스텐트**이고, 익스텐트 여러 개와 낱장 페이지 최대 32장을 묶은 논리 단위가 **세그먼트**다. 인덱스 하나는 세그먼트 두 개(리프용, 비리프용)를 갖는다. 모든 페이지는 38바이트 FIL 헤더와 8바이트 트레일러로 감싸이고, 그 사이의 모양은 페이지 종류(`FIL_PAGE_TYPE`)가 정한다. 이 문서는 그 바이트 자리를 그림으로 정리한다. 페이지 안에 레코드를 넣는 동작은 [B+Tree 삽입과 분할](../../flows/btree-insert/README.md)에, 페이지가 디스크로 나가는 순서는 [페이지 플러시, doublewrite, 체크포인트](../../flows/flush-checkpoint/README.md)에 있다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다. 바이트 오프셋 계산은 기본 페이지 크기 16KB(16384)를 가정한다.

## 전체 그림

```text
 파일 -> 익스텐트 -> 페이지 (물리), 세그먼트 (논리)

 t1.ibd  (페이지 크기 16KB, 익스텐트 = 64 페이지 = 1MB)
 +--------------------------------------------------------------------+
 | 익스텐트 0  page 0 .. 63                                           |
 |   page 0  FSP_HDR   공간 헤더 + 익스텐트 디스크립터(XDES) 배열     |
 |   page 1  IBUF_BITMAP                                              |
 |   page 2  INODE     세그먼트 inode 배열 (세그먼트마다 192바이트)   |
 |   page 3.. 인덱스 페이지, undo 페이지, LOB 페이지 ...              |
 +--------------------------------------------------------------------+
 | 익스텐트 1  page 64 .. 127                                         |
 +--------------------------------------------------------------------+
 | ...                                                                |
 | page 16384  XDES     page 0 의 디스크립터 배열이 여기서 반복된다   |
 | page 16385  IBUF_BITMAP                                            |
 +--------------------------------------------------------------------+

 파일 안의 위치   offset = page_no * page_size        (fil0fil.cc L7754)
 페이지 0,1,2 는 모든 테이블스페이스에 있다              (fsp0types.h L155-L160)
 page 0 과 1 의 자리는 page_size 페이지마다 반복된다     (fsp0types.h L149-L151 주석)
```

```text
 세그먼트는 익스텐트 목록 + 낱장 페이지 배열이다

 INODE 페이지의 inode 하나 (fseg_inode_t, 192바이트)
   FSEG_FREE       이 세그먼트가 가진 빈 익스텐트 목록
   FSEG_NOT_FULL   일부만 찬 익스텐트 목록
   FSEG_FULL       꽉 찬 익스텐트 목록
   FSEG_FRAG_ARR   낱장 페이지 번호 32칸 (FSP_EXTENT_SIZE / 2)
                   세그먼트가 작을 때는 익스텐트를 통째로 주지 않고
                   공간 공용의 FREE_FRAG 익스텐트에서 한 장씩 빌려 준다

 인덱스 하나 = 세그먼트 둘. 루트 페이지의 PAGE 헤더에 두 inode 의 주소가 있다
   PAGE_BTR_SEG_LEAF  리프 페이지 세그먼트   (page0types.h L90)
   PAGE_BTR_SEG_TOP   비리프 페이지 세그먼트 (page0types.h L98)

 익스텐트 하나의 소속은 XDES 의 상태가 말한다 (xdes_state_t, fsp0fsp.h L287-L306)
   XDES_FREE       공간의 빈 익스텐트 목록 (FSP_FREE)
   XDES_FREE_FRAG  공간 공용 낱장 익스텐트, 아직 빈 페이지가 있다
   XDES_FULL_FRAG  공간 공용 낱장 익스텐트, 꽉 찼다
   XDES_FSEG       어떤 세그먼트에 통째로 속한다 (XDES_ID 가 그 세그먼트)
```

```text
 모든 페이지의 겉모양 (16384 바이트)

 offset  size  field                          뜻
 ------  ----  -----------------------------  -----------------------------------
      0     4  FIL_PAGE_SPACE_OR_CHKSUM       체크섬 (새 방식)
      4     4  FIL_PAGE_OFFSET                이 페이지의 page_no
      8     4  FIL_PAGE_PREV                  같은 레벨 이전 페이지 (없으면 FIL_NULL)
     12     4  FIL_PAGE_NEXT                  같은 레벨 다음 페이지
     16     8  FIL_PAGE_LSN                   마지막 수정의 LSN (page LSN)
     24     2  FIL_PAGE_TYPE                  페이지 종류 (INDEX=17855, UNDO_LOG=2 ...)
     26     8  FIL_PAGE_FILE_FLUSH_LSN        시스템 공간 page 0 에서만 의미
     34     4  FIL_PAGE_SPACE_ID              space id
     38        FIL_PAGE_DATA                  여기부터 종류별 본문
   ...
  16376     4  (트레일러 앞 4바이트)          체크섬 (옛 방식, CRC32 면 같은 값)
  16380     4  (트레일러 뒤 4바이트)          FIL_PAGE_LSN 의 하위 4바이트
  16384        끝                             FIL_PAGE_DATA_END = 8
```

page LSN 은 헤더와 트레일러 두 곳에 들어간다. 페이지를 쓰다 중간에 끊기면(torn page) 앞쪽 헤더의 LSN 과 맨 끝 4바이트가 어긋난다. 읽을 때 `BlockReporter::is_corrupted` 가 이 두 4바이트를 먼저 비교해 반쯤 쓰인 페이지를 걸러 낸다(checksum.cc L284-L293).

## FIL 헤더와 트레일러

헤더 필드는 상수 오프셋으로만 정의된다. 구조체는 없고, `mach_read_from_4(page + FIL_PAGE_OFFSET)` 처럼 바이트 배열에 오프셋을 더해 읽는다.

`storage` / `innobase` / `include` / `fil0types.h` L40-L119 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fil0types.h#L40-L119))

```cpp
// include/fil0types.h L40-L119

/** MySQL-4.0.14 space id the page belongs to (== 0) but in later
versions the 'new' checksum of the page */
constexpr uint32_t FIL_PAGE_SPACE_OR_CHKSUM = 0;

/** page offset inside space */
constexpr uint32_t FIL_PAGE_OFFSET = 4;

/** if there is a 'natural' predecessor of the page, its offset.
Otherwise FIL_NULL. This field is not set on BLOB pages, which are stored as a
singly-linked list. See also FIL_PAGE_NEXT. */
constexpr uint32_t FIL_PAGE_PREV = 8;

/** On page 0 of the tablespace, this is the server version ID */
constexpr uint32_t FIL_PAGE_SRV_VERSION = 8;

/** if there is a 'natural' successor of the page, its offset. Otherwise
FIL_NULL. B-tree index pages(FIL_PAGE_TYPE contains FIL_PAGE_INDEX) on the
same PAGE_LEVEL are maintained as a doubly linked list via FIL_PAGE_PREV and
FIL_PAGE_NEXT in the collation order of the smallest user record on each
page. */
constexpr uint32_t FIL_PAGE_NEXT = 12;

/** On page 0 of the tablespace, this is the server version ID */
constexpr uint32_t FIL_PAGE_SPACE_VERSION = 12;

/** lsn of the end of the newest modification log record to the page */
constexpr uint32_t FIL_PAGE_LSN = 16;

/** file page type: FIL_PAGE_INDEX,..., 2 bytes. The contents of this field
can only be trusted in the following case: if the page is an uncompressed
B-tree index page, then it is guaranteed that the value is FIL_PAGE_INDEX.
The opposite does not hold.

In tablespaces created by MySQL/InnoDB 5.1.7 or later, the contents of this
field is valid for all uncompressed pages. */
constexpr uint32_t FIL_PAGE_TYPE = 24;

/** this is only defined for the first page of the system tablespace: the file
has been flushed to disk at least up to this LSN. For FIL_PAGE_COMPRESSED
pages, we store the compressed page control information in these 8 bytes. */
constexpr uint32_t FIL_PAGE_FILE_FLUSH_LSN = 26;

// ... (L83-L103 생략: 압축 페이지가 FIL_PAGE_FILE_FLUSH_LSN 8바이트를 나눠 쓰는 하위 필드)
/** starting from 4.1.x this contains the space id of the page */
constexpr uint32_t FIL_PAGE_ARCH_LOG_NO_OR_SPACE_ID = 34;

/** alias for space id */
constexpr uint32_t FIL_PAGE_SPACE_ID = FIL_PAGE_ARCH_LOG_NO_OR_SPACE_ID;

/** start of the data on the page */
constexpr uint32_t FIL_PAGE_DATA = 38;

/** File page trailer */
/** the low 4 bytes of this are used to store the page checksum, the
last 4 bytes should be identical to the last 4 bytes of FIL_PAGE_LSN */
constexpr uint32_t FIL_PAGE_END_LSN_OLD_CHKSUM = 8;

/** size of the page trailer */
constexpr uint32_t FIL_PAGE_DATA_END = 8;
```

트레일러는 페이지를 쓰기 직전에 채운다. 8바이트 전체에 LSN 을 쓴 뒤 앞 4바이트를 체크섬으로 덮어써서, 뒤 4바이트에 LSN 하위 절반이 남는다.

`storage` / `innobase` / `buf` / `buf0flu.cc` L811-L815 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/buf/buf0flu.cc#L811-L815))

```cpp
// buf0flu.cc L811-L815
  /* Write the newest modification lsn to the page header and trailer */
  mach_write_to_8(page + FIL_PAGE_LSN, newest_lsn);

  mach_write_to_8(page + UNIV_PAGE_SIZE - FIL_PAGE_END_LSN_OLD_CHKSUM,
                  newest_lsn);
```

페이지 종류 값 중 자주 보는 것만 골랐다. 위 `FIL_PAGE_TYPE` 주석대로 압축하지 않은 B-tree 페이지라면 이 칸이 반드시 `FIL_PAGE_INDEX`(17855)이지만, 거꾸로 이 칸이 17855 라고 해서 B-tree 페이지라는 보장은 없다(5.1.7 이전에 만든 공간).

`storage` / `innobase` / `include` / `fil0fil.h` L1246-L1288 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fil0fil.h#L1246-L1288))

```cpp
// include/fil0fil.h L1246-L1288
/** File page types (values of FIL_PAGE_TYPE) @{ */
/** B-tree node */
constexpr page_type_t FIL_PAGE_INDEX = 17855;

/** R-tree node */
constexpr page_type_t FIL_PAGE_RTREE = 17854;

/** Tablespace SDI Index page */
constexpr page_type_t FIL_PAGE_SDI = 17853;

// ... (L1256-L1258 생략: 미사용 값)
/** Undo log page */
constexpr page_type_t FIL_PAGE_UNDO_LOG = 2;

/** Index node */
constexpr page_type_t FIL_PAGE_INODE = 3;

// ... (L1265-L1267 생략: insert buffer free list)
/* File page types introduced in MySQL/InnoDB 5.1.7 */
/** Freshly allocated page */
constexpr page_type_t FIL_PAGE_TYPE_ALLOCATED = 0;

/** Insert buffer bitmap */
constexpr page_type_t FIL_PAGE_IBUF_BITMAP = 5;

/** System page */
constexpr page_type_t FIL_PAGE_TYPE_SYS = 6;

/** Transaction system data */
constexpr page_type_t FIL_PAGE_TYPE_TRX_SYS = 7;

/** File space header */
constexpr page_type_t FIL_PAGE_TYPE_FSP_HDR = 8;

/** Extent descriptor page */
constexpr page_type_t FIL_PAGE_TYPE_XDES = 9;

/** Uncompressed BLOB page */
constexpr page_type_t FIL_PAGE_TYPE_BLOB = 10;
```

## 공간 헤더와 익스텐트 디스크립터 (page 0)

page 0 의 FIL 헤더 바로 뒤(오프셋 38)에 공간 헤더 112바이트가 있고, 그 뒤(오프셋 150)부터 익스텐트 디스크립터가 40바이트씩 이어진다. 목록 필드들은 페이지 사이를 잇는 이중 연결 리스트의 **베이스 노드**다.

```text
 page 0 (FIL_PAGE_TYPE_FSP_HDR)

 offset  size  field                    뜻
 ------  ----  -----------------------  ------------------------------------
      0    38  FIL 헤더
     38     4  FSP_SPACE_ID
     42     4  FSP_NOT_USED
     46     4  FSP_SIZE                 현재 공간 크기 (페이지 수)
     50     4  FSP_FREE_LIMIT           이 번호 이상은 아직 목록에 안 올린 빈 페이지
     54     4  FSP_SPACE_FLAGS          페이지 크기, 행 형식, 암호화 등 비트
     58     4  FSP_FRAG_N_USED          FREE_FRAG 목록에서 쓰인 페이지 수
     62    16  FSP_FREE                 빈 익스텐트 목록
     78    16  FSP_FREE_FRAG            낱장용, 빈 칸 있음
     94    16  FSP_FULL_FRAG            낱장용, 꽉 참
    110     8  FSP_SEG_ID               다음에 줄 세그먼트 id
    118    16  FSP_SEG_INODES_FULL      inode 칸이 다 찬 INODE 페이지 목록
    134    16  FSP_SEG_INODES_FREE      inode 칸이 남은 INODE 페이지 목록
    150        XDES_ARR_OFFSET          여기부터 XDES 배열

 XDES 하나 (40바이트, 익스텐트 하나를 설명)
   +0   8  XDES_ID          소속 세그먼트 id
   +8  12  XDES_FLST_NODE   위 목록들 중 하나에 매달리는 노드 (prev 6 + next 6)
   +20  4  XDES_STATE       xdes_state_t
   +24 16  XDES_BITMAP      페이지당 2비트 x 64 페이지 = 128비트
                            비트 0 = 빈 페이지인가 (XDES_FREE_BIT)
                            비트 1 = 쓰지 않음 (XDES_CLEAN_BIT 주석 "currently not used")

 목록 베이스 노드 16바이트 = 길이 4 + first 주소 6 + last 주소 6
 파일 주소 6바이트       = page_no 4 + 페이지 안 byte offset 2   (FIL_ADDR_SIZE)

 page 0 하나가 page_size 개 페이지(16384 장 = 256 익스텐트)를 설명한다
 그래서 다음 디스크립터 페이지는 page 16384 에 있다
```

`storage` / `innobase` / `include` / `fsp0fsp.h` L126-L172 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fsp0fsp.h#L126-L172))

```cpp
// fsp0fsp.h L126-L172
/*                      SPACE HEADER
                        ============

File space header data structure: this data structure is contained in the
first page of a space. The space for this header is reserved in every extent
descriptor page, but used only in the first. */

/*-------------------------------------*/
/** space id */
constexpr uint32_t FSP_SPACE_ID = 0;
/** this field contained a value up to which we know that the modifications in
 the database have been flushed to the file space; not used now */
constexpr uint32_t FSP_NOT_USED = 4;
/** Current size of the space in pages */
constexpr uint32_t FSP_SIZE = 8;
/** Minimum page number for which the  free list has not been initialized: the
 pages >= this limit are, bydefinition, free; note that in a single-table
 tablespace where size < 64 pages, this number is 64, i.e.,we have initialized
 the space about the first extent, but have not physically allocated those
 pages to thefile */
constexpr uint32_t FSP_FREE_LIMIT = 12;
/** fsp_space_t.flags, similar to dict_table_t::flags */
constexpr uint32_t FSP_SPACE_FLAGS = 16;
/** number of used pages in the FSP_FREE_FRAG list */
constexpr uint32_t FSP_FRAG_N_USED = 20;
/** list of free extents */
constexpr uint32_t FSP_FREE = 24;
/** list of partially free extents not belonging to any segment */
constexpr uint32_t FSP_FREE_FRAG = 24 + FLST_BASE_NODE_SIZE;

/** list of full extents not belonging to any segment */
constexpr uint32_t FSP_FULL_FRAG = 24 + 2 * FLST_BASE_NODE_SIZE;

/** 8 bytes which give the first unused segment id */
constexpr uint32_t FSP_SEG_ID = 24 + 3 * FLST_BASE_NODE_SIZE;

/** list of pages containing segment headers, where all the segment inode slots
 are reserved */
constexpr uint32_t FSP_SEG_INODES_FULL = 32 + 3 * FLST_BASE_NODE_SIZE;

/** list of pages containing segment headers, where not all the segment header
 slots are reserved */
constexpr uint32_t FSP_SEG_INODES_FREE = 32 + 4 * FLST_BASE_NODE_SIZE;

/*-------------------------------------*/
/* File space header size */
constexpr uint32_t FSP_HEADER_SIZE = 32 + 5 * FLST_BASE_NODE_SIZE;
```

`storage` / `innobase` / `include` / `fsp0fsp.h` L260-L321 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fsp0fsp.h#L260-L321))

```cpp
// fsp0fsp.h L260-L321
/*                      EXTENT DESCRIPTOR
                        =================

File extent descriptor data structure: contains bits to tell which pages in
the extent are free and which contain old tuple version to clean. */

/*-------------------------------------*/
/** The identifier of the segment to which this extent belongs */
constexpr uint32_t XDES_ID = 0;
/** The list node data structure for the descriptors */
constexpr uint32_t XDES_FLST_NODE = 8;
/** contains state information of the extent */
constexpr uint32_t XDES_STATE = FLST_NODE_SIZE + 8;
/** Descriptor bitmap of the pages in the extent */
constexpr uint32_t XDES_BITMAP = FLST_NODE_SIZE + 12;

/*-------------------------------------*/

/** How many bits are there per page */
constexpr uint32_t XDES_BITS_PER_PAGE = 2;
/** Index of the bit which tells if the page is free */
constexpr uint32_t XDES_FREE_BIT = 0;
/** NOTE: currently not used! Index of the bit which tells if  there are old
versions of tuples on the page */
constexpr uint32_t XDES_CLEAN_BIT = 1;

/** States of a descriptor */
enum xdes_state_t {

  /** extent descriptor is not initialized */
  XDES_NOT_INITED = 0,

  /** extent is in free list of space */
  XDES_FREE = 1,

  /** extent is in free fragment list of space */
  XDES_FREE_FRAG = 2,

  /** extent is in full fragment list of space */
  XDES_FULL_FRAG = 3,

  /** extent belongs to a segment */
  XDES_FSEG = 4,

  /** fragment extent leased to segment */
  XDES_FSEG_FRAG = 5
};

/** File extent data structure size in bytes. */
#define XDES_SIZE \
  (XDES_BITMAP + UT_BITS_IN_BYTES(FSP_EXTENT_SIZE * XDES_BITS_PER_PAGE))

// ... (L312-L319 생략: XDES_SIZE 의 최대, 최소 페이지 크기 변형)
/** Offset of the descriptor array on a descriptor page */
constexpr uint32_t XDES_ARR_OFFSET = FSP_HEADER_OFFSET + FSP_HEADER_SIZE;
```

## 세그먼트 inode (page 2)

INODE 페이지는 FIL 헤더 뒤에 자기 자신을 INODE 페이지 목록에 매다는 노드 12바이트를 두고, 오프셋 50부터 inode 를 192바이트씩 채운다. 16KB 페이지면 (16384 - 50 - 10) / 192 = 85개다(`FSP_SEG_INODES_PER_PAGE`).

```text
 inode 하나 (FSEG_INODE_SIZE = 16 + 3*16 + 32*4 = 192바이트)

   +0    8  FSEG_ID                0 이면 빈 칸
   +8    4  FSEG_NOT_FULL_N_USED   NOT_FULL 목록 익스텐트에서 쓰인 페이지 수
   +12  16  FSEG_FREE              이 세그먼트의 빈 익스텐트 목록
   +28  16  FSEG_NOT_FULL
   +44  16  FSEG_FULL
   +60   4  FSEG_MAGIC_N           97937874
   +64 128  FSEG_FRAG_ARR          낱장 page_no 32칸 (FIL_NULL = 빈 칸)

 다른 페이지가 inode 를 가리킬 때는 10바이트 세그먼트 헤더를 쓴다
   FSEG_HDR_SPACE 4 + FSEG_HDR_PAGE_NO 4 + FSEG_HDR_OFFSET 2    (fsp0types.h L88-L94)
   인덱스 루트의 PAGE_BTR_SEG_LEAF / PAGE_BTR_SEG_TOP 가 이 10바이트다
```

`storage` / `innobase` / `include` / `fsp0fsp.h` L186-L225 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fsp0fsp.h#L186-L225))

```cpp
// fsp0fsp.h L186-L225
/*                      FILE SEGMENT INODE
                        ==================

Segment inode which is created for each segment in a tablespace. NOTE: in
purge we assume that a segment having only one currently used page can be
freed in a few steps, so that the freeing cannot fill the file buffer with
bufferfixed file pages. */

typedef byte fseg_inode_t;

constexpr uint32_t FSEG_INODE_PAGE_NODE = FSEG_PAGE_DATA;
/* the list node for linking
segment inode pages */

constexpr uint32_t FSEG_ARR_OFFSET = FSEG_PAGE_DATA + FLST_NODE_SIZE;
/*-------------------------------------*/
/* 8 bytes of segment id: if this is 0,  it means that the header is unused */
constexpr uint32_t FSEG_ID = 0;
/** number of used segment pages in the FSEG_NOT_FULL list */
constexpr uint32_t FSEG_NOT_FULL_N_USED = 8;
/** list of free extents of this segment */
constexpr uint32_t FSEG_FREE = 12;
/** list of partially free extents */
constexpr uint32_t FSEG_NOT_FULL = 12 + FLST_BASE_NODE_SIZE;
/** list of full extents */
constexpr uint32_t FSEG_FULL = 12 + 2 * FLST_BASE_NODE_SIZE;
/** magic number used in debugging */
constexpr uint32_t FSEG_MAGIC_N = 12 + 3 * FLST_BASE_NODE_SIZE;
/** array of individual pages belonging to this segment in fsp fragment extent
 lists */
constexpr uint32_t FSEG_FRAG_ARR = 16 + 3 * FLST_BASE_NODE_SIZE;
/* number of slots in the array for the fragment pages */
#define FSEG_FRAG_ARR_N_SLOTS (FSP_EXTENT_SIZE / 2)
/** a fragment page slot contains its  page number within space, FIL_NULL means
 that the slot is not in use */
constexpr uint32_t FSEG_FRAG_SLOT_SIZE = 4;

/*-------------------------------------*/
#define FSEG_INODE_SIZE \
  (16 + 3 * FLST_BASE_NODE_SIZE + FSEG_FRAG_ARR_N_SLOTS * FSEG_FRAG_SLOT_SIZE)
```

고정 페이지 번호와 익스텐트 크기는 `fsp0types.h` 에 있다. page 3 부터 7 까지의 고정 자리(ibuf, 트랜잭션 시스템, 첫 롤백 세그먼트, 데이터 사전)는 시스템 테이블스페이스(space 0)에만 있고, undo 테이블스페이스는 page 3 에 롤백 세그먼트 디렉터리(`FSP_RSEG_ARRAY_PAGE_NO`)를 둔다.

`storage` / `innobase` / `include` / `fsp0types.h` L55-L69 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fsp0types.h#L55-L69))

```cpp
// fsp0types.h L55-L69
/** File space extent size in pages
page size | file space extent size
----------+-----------------------
   4 KiB  | 256 pages = 1 MiB
   8 KiB  | 128 pages = 1 MiB
  16 KiB  |  64 pages = 1 MiB
  32 KiB  |  64 pages = 2 MiB
  64 KiB  |  64 pages = 4 MiB
*/
#define FSP_EXTENT_SIZE                                                 \
  static_cast<page_no_t>(                                               \
      ((UNIV_PAGE_SIZE <= (16384)                                       \
            ? (1048576 / UNIV_PAGE_SIZE)                                \
            : ((UNIV_PAGE_SIZE <= (32768)) ? (2097152 / UNIV_PAGE_SIZE) \
                                           : (4194304 / UNIV_PAGE_SIZE)))))
```

`storage` / `innobase` / `include` / `fsp0types.h` L149-L181 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fsp0types.h#L149-L181))

```cpp
// fsp0types.h L149-L181
/** @name The space low address page map
The pages at FSP_XDES_OFFSET and FSP_IBUF_BITMAP_OFFSET are repeated
every XDES_DESCRIBED_PER_PAGE pages in every tablespace. */
/** @{ */
/*--------------------------------------*/
/** extent descriptor */
constexpr uint32_t FSP_XDES_OFFSET = 0;
/** insert buffer bitmap; The ibuf bitmap pages are the ones whose page number
is the number above plus a multiple of XDES_DESCRIBED_PER_PAGE */
constexpr uint32_t FSP_IBUF_BITMAP_OFFSET = 1;
/** in every tablespace */
constexpr uint32_t FSP_FIRST_INODE_PAGE_NO = 2;

/** The following pages exist in the system tablespace (space 0). */
/** insert buffer header page, in tablespace 0 */
constexpr uint32_t FSP_IBUF_HEADER_PAGE_NO = 3;
/** insert buffer B-tree root page in tablespace 0;
The ibuf tree root page number in tablespace 0; its fseg inode is on the page
number FSP_FIRST_INODE_PAGE_NO */
constexpr uint32_t FSP_IBUF_TREE_ROOT_PAGE_NO = 4;
/** transaction system header, in tablespace 0 */
constexpr uint32_t FSP_TRX_SYS_PAGE_NO = 5;
/** first rollback segment page, in tablespace 0 */
constexpr uint32_t FSP_FIRST_RSEG_PAGE_NO = 6;
/** data dictionary header page, in tablespace 0 */
constexpr uint32_t FSP_DICT_HDR_PAGE_NO = 7;

/* The following page exists in each v8 Undo Tablespace.
(space_id = SRV_LOG_SPACE_FIRST_ID - undo_space_num)
(undo_space_num = rseg_array_slot_num + 1) */

/** rollback segment directory page number in each undo tablespace */
constexpr uint32_t FSP_RSEG_ARRAY_PAGE_NO = 3;
```

## 인덱스 페이지 (FIL_PAGE_INDEX)

인덱스 페이지는 위에서 아래로 자라는 레코드 heap 과, 아래에서 위로 자라는 page directory 사이에 빈 공간을 둔다. 레코드는 heap 에 **삽입 순서대로** 쌓이고, 키 순서는 레코드마다 있는 next 포인터 연결 리스트가 만든다.

```text
 인덱스 페이지 (COMPACT, 16384 바이트)

 offset
      0  +---------------------------------------------+
         | FIL 헤더 38                                 |
     38  +---------------------------------------------+
         | PAGE 헤더 56  (PAGE_HEADER = 38)            |
     94  +---------------------------------------------+  PAGE_DATA
         | infimum   extra 5 (94..98) + "infimum\0"    |  origin 99  (PAGE_NEW_INFIMUM)
    107  |           extra 5 (107..111)                |
    112  | supremum  "supremum" (112..119)             |  origin 112 (PAGE_NEW_SUPREMUM)
    120  +---------------------------------------------+  PAGE_NEW_SUPREMUM_END
         | 사용자 레코드 heap  (삽입 순서로 쌓인다)    |
         |   rec A  rec C  rec B  (지운 것은 PAGE_FREE |
         |   목록으로 간다)                            |
         +---------------------------------------------+  PAGE_HEAP_TOP
         |                                             |
         |            빈 공간                          |
         |                                             |
         +---------------------------------------------+
         | slot n-1  -> supremum                       |  아래로 자란다
         | ...                                         |
  16372  | slot 1                                      |  (빈 페이지: supremum)
  16374  | slot 0    -> infimum                        |
  16376  +---------------------------------------------+
         | FIL 트레일러 8                              |
  16384  +---------------------------------------------+

 slot n 의 주소 = page + page_size - PAGE_DIR - (n+1) * 2   (page0page.h L310-L311)
 슬롯은 레코드의 페이지 안 오프셋 2바이트다
```

```text
 next 포인터 리스트와 page directory 의 관계

 heap 순서     infimum  supremum  A(10)  C(30)  B(20)  D(40)  E(50) ...
 next 리스트   infimum -> A -> B -> C -> D -> E -> ... -> supremum

 directory     slot 0 --> infimum   n_owned 1    (첫 슬롯은 늘 1)
               slot 1 --> D         n_owned 4    A, B, C, D 를 "소유"
               slot 2 --> supremum  n_owned 1..8

 슬롯이 가리키는 레코드의 n_owned (레코드 헤더 4비트) 가
 직전 슬롯 다음부터 자기까지의 레코드 수다
 4 ~ 8 범위를 지키고, 8 을 넘으면 슬롯을 둘로 나눈다 (PAGE_DIR_SLOT_MAX_N_OWNED)

 검색 = 슬롯 배열 이분 탐색 -> 그 구간에서 next 를 따라 최대 8개 선형 탐색
```

이 정책은 `page0page.cc` 머리 주석(L50-L90)이 설명한다. 슬롯 하나가 대략 여섯 번째 레코드마다 하나씩 놓이고, 삽입 대부분은 heap 에 쌓기만 하면 되어 8번에 한 번만 슬롯 배열을 움직인다. 삽입 때 슬롯이 실제로 갈라지는 코드는 [page_cur_insert_rec_low](../../flows/btree-insert/06_page_cur_insert_rec_low/README.md)의 7, 8단계다.

```text
 PAGE 헤더 (페이지 오프셋 = 38 + 표의 offset)

 offset  size  field                  뜻
 ------  ----  ---------------------  ----------------------------------------
      0     2  PAGE_N_DIR_SLOTS       슬롯 수 (빈 페이지 2)
      2     2  PAGE_HEAP_TOP          heap 꼭대기의 오프셋
      4     2  PAGE_N_HEAP            heap 레코드 수, 최상위 비트 = COMPACT
      6     2  PAGE_FREE              지운 레코드 free list 머리
      8     2  PAGE_GARBAGE           지운 레코드 바이트 합
     10     2  PAGE_LAST_INSERT       마지막 삽입 레코드
     12     2  PAGE_DIRECTION         마지막 삽입 방향 (LEFT, RIGHT ...)
     14     2  PAGE_N_DIRECTION       같은 방향 연속 삽입 수
     16     2  PAGE_N_RECS            사용자 레코드 수
     18     8  PAGE_MAX_TRX_ID        보조 인덱스에서만 의미
     26     2  PAGE_LEVEL             리프 = 0
     28     8  PAGE_INDEX_ID          이 페이지가 속한 인덱스
     36    10  PAGE_BTR_SEG_LEAF      루트에서만: 리프 세그먼트 헤더
     46    10  PAGE_BTR_SEG_TOP       루트에서만: 비리프 세그먼트 헤더
     56        PAGE_DATA (= 38 + 56 = 94)
```

`PAGE_LAST_INSERT` 는 분할 지점을 고를 때 쓰인다. 직전 삽입 바로 뒤에 또 넣는 순차 삽입이면 반으로 나누지 않고 삽입 지점 근처에서 나눈다(btr0btr.cc L1679, L1720, [btr_page_split_and_insert](../../flows/btree-insert/08_btr_page_split_and_insert/README.md)). `PAGE_DIRECTION` 과 `PAGE_N_DIRECTION` 은 오른쪽 연속 삽입이 3번을 넘었을 때 페이지 안 검색을 마지막 삽입 위치에서 바로 시작하는 지름길에 쓰인다(page0cur.cc L374-L378).

`storage` / `innobase` / `include` / `page0types.h` L52-L137 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/page0types.h#L52-L137))

```cpp
// page0types.h L52-L137
/** index page header starts at this offset */
constexpr uint32_t PAGE_HEADER = FSEG_PAGE_DATA;

/*-----------------------------*/
/** number of slots in page directory */
constexpr uint32_t PAGE_N_DIR_SLOTS = 0;
/** pointer to record heap top */
constexpr uint32_t PAGE_HEAP_TOP = 2;
/** number of records in the heap, bit 15=flag: new-style compact page format */
constexpr uint32_t PAGE_N_HEAP = 4;
/** pointer to start of page free record list */
constexpr uint32_t PAGE_FREE = 6;
/** number of bytes in deleted records */
constexpr uint32_t PAGE_GARBAGE = 8;
/** pointer to the last inserted record, or NULL if this info has been reset by
 a delete, for example */
constexpr uint32_t PAGE_LAST_INSERT = 10;
/** last insert direction: PAGE_LEFT, ... */
constexpr uint32_t PAGE_DIRECTION = 12;
/** number of consecutive inserts to the same direction */
constexpr uint32_t PAGE_N_DIRECTION = 14;
/** number of user records on the page */
constexpr uint32_t PAGE_N_RECS = 16;
/** highest id of a trx which may have modified a record on the page; trx_id_t;
defined only in secondary indexes and in the insert buffer tree */
constexpr uint32_t PAGE_MAX_TRX_ID = 18;
/** end of private data structure of the page header which are set in a page
create */
constexpr uint32_t PAGE_HEADER_PRIV_END = 26;
/*----*/
/** level of the node in an index tree; the leaf level is the level 0.
This field should not be written to after page creation. */
constexpr uint32_t PAGE_LEVEL = 26;
/** index id where the page belongs. This field should not be written to after
 page creation. */
constexpr uint32_t PAGE_INDEX_ID = 28;
/** file segment header for the leaf pages in a B-tree: defined only on the root
 page of a B-tree, but not in the root of an ibuf tree */
constexpr uint32_t PAGE_BTR_SEG_LEAF = 36;
constexpr uint32_t PAGE_BTR_IBUF_FREE_LIST = PAGE_BTR_SEG_LEAF;
constexpr uint32_t PAGE_BTR_IBUF_FREE_LIST_NODE = PAGE_BTR_SEG_LEAF;
/* in the place of PAGE_BTR_SEG_LEAF and _TOP
there is a free list base node if the page is
the root page of an ibuf tree, and at the same
place is the free list node if the page is in
a free list */
constexpr uint32_t PAGE_BTR_SEG_TOP = 36 + FSEG_HEADER_SIZE;
/* file segment header for the non-leaf pages
in a B-tree: defined only on the root page of
a B-tree, but not in the root of an ibuf
tree */
/*----*/
/** start of data on the page */
constexpr uint32_t PAGE_DATA = PAGE_HEADER + 36 + 2 * FSEG_HEADER_SIZE;

/** offset of the page infimum record on an
old-style page */
#define PAGE_OLD_INFIMUM (PAGE_DATA + 1 + REC_N_OLD_EXTRA_BYTES)

/** offset of the page supremum record on an
old-style page */
#define PAGE_OLD_SUPREMUM (PAGE_DATA + 2 + 2 * REC_N_OLD_EXTRA_BYTES + 8)

/** offset of the page supremum record end on an old-style page */
#define PAGE_OLD_SUPREMUM_END (PAGE_OLD_SUPREMUM + 9)

/** offset of the page infimum record on a new-style compact page */
#define PAGE_NEW_INFIMUM (PAGE_DATA + REC_N_NEW_EXTRA_BYTES)

/** offset of the page supremum record on a new-style compact page */
#define PAGE_NEW_SUPREMUM (PAGE_DATA + 2 * REC_N_NEW_EXTRA_BYTES + 8)

/** offset of the page supremum record end on a new-style compact page */
#define PAGE_NEW_SUPREMUM_END (PAGE_NEW_SUPREMUM + 8)

/*-----------------------------*/

/* Heap numbers */
/** Page infimum */
constexpr ulint PAGE_HEAP_NO_INFIMUM = 0;
/** Page supremum */
constexpr ulint PAGE_HEAP_NO_SUPREMUM = 1;

/** First user record in creation (insertion) order, not necessarily collation
order; this record may have been deleted */
constexpr ulint PAGE_HEAP_NO_USER_LOW = 2;
```

빈 페이지를 만들 때 infimum 과 supremum 을 미리 써 두고 슬롯 두 개를 건다. infimum 의 next 값 `0x000d` 는 13 이고, infimum origin 99 에서 13 을 더하면 supremum origin 112 다. COMPACT 의 next 포인터가 **상대 오프셋**이라는 것이 이 바이트에서 보인다.

`storage` / `innobase` / `page` / `page0page.cc` L295-L302 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/page/page0page.cc#L295-L302))

```cpp
// page0page.cc L295-L302
/** The page infimum and supremum of an empty page in ROW_FORMAT=COMPACT */
static const byte infimum_supremum_compact[] = {
    /* the infimum record */
    0x01 /*n_owned=1*/, 0x00, 0x02 /* heap_no=0, REC_STATUS_INFIMUM */, 0x00,
    0x0d /* pointer to supremum */, 'i', 'n', 'f', 'i', 'm', 'u', 'm', 0,
    /* the supremum record */
    0x01 /*n_owned=1*/, 0x00, 0x0b /* heap_no=1, REC_STATUS_SUPREMUM */, 0x00,
    0x00 /* end of record list */, 's', 'u', 'p', 'r', 'e', 'm', 'u', 'm'};
```

`storage` / `innobase` / `page` / `page0page.cc` L326-L341 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/page/page0page.cc#L326-L341))

```cpp
// page0page.cc L326-L341

  memset(page + PAGE_HEADER, 0, PAGE_HEADER_PRIV_END);
  page[PAGE_HEADER + PAGE_N_DIR_SLOTS + 1] = 2;
  page[PAGE_HEADER + PAGE_DIRECTION + 1] = PAGE_NO_DIRECTION;

  if (comp) {
    page[PAGE_HEADER + PAGE_N_HEAP] = 0x80; /*page_is_comp()*/
    page[PAGE_HEADER + PAGE_N_HEAP + 1] = PAGE_HEAP_NO_USER_LOW;
    page[PAGE_HEADER + PAGE_HEAP_TOP + 1] = PAGE_NEW_SUPREMUM_END;
    memcpy(page + PAGE_DATA, infimum_supremum_compact,
           sizeof infimum_supremum_compact);
    memset(page + PAGE_NEW_SUPREMUM_END, 0,
           UNIV_PAGE_SIZE - PAGE_DIR - PAGE_NEW_SUPREMUM_END);
    page[UNIV_PAGE_SIZE - PAGE_DIR - PAGE_DIR_SLOT_SIZE * 2 + 1] =
        PAGE_NEW_SUPREMUM;
    page[UNIV_PAGE_SIZE - PAGE_DIR - PAGE_DIR_SLOT_SIZE + 1] = PAGE_NEW_INFIMUM;
```

`storage` / `innobase` / `include` / `page0page.h` L58-L74 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/page0page.h#L58-L74))

```cpp
// include/page0page.h L58-L74
/* Offset of the directory start down from the page end. We call the
slot with the highest file address directory start, as it points to
the first record in the list of records. */
constexpr uint32_t PAGE_DIR = FIL_PAGE_DATA_END;

/* We define a slot in the page directory as two bytes */
constexpr uint32_t PAGE_DIR_SLOT_SIZE = 2;

/* The offset of the physically lower end of the directory, counted from
page end, when the page is empty */
constexpr uint32_t PAGE_EMPTY_DIR_START = PAGE_DIR + 2 * PAGE_DIR_SLOT_SIZE;

/* The maximum and minimum number of records owned by a directory slot. The
number may drop below the minimum in the first and the last slot in the
directory. */
constexpr uint32_t PAGE_DIR_SLOT_MAX_N_OWNED = 8;
constexpr uint32_t PAGE_DIR_SLOT_MIN_N_OWNED = 4;
```

## 어디에서 쓰이는가

```text
 [버퍼 풀 페이지 획득]   buf_page_get_gen 이 (space_id, page_no) 로 이 페이지를 메모리에 올린다
                         offset = page_no * page_size 로 파일을 읽는다
 [B+Tree 삽입과 분할]    PAGE_FREE / PAGE_HEAP_TOP 에서 자리를 받고, next 리스트와 슬롯을 고친다
                         분할 때 fseg_alloc_free_page 가 세그먼트 -> 익스텐트 -> XDES 비트를 따라간다
 [mini-transaction...]   위 필드를 바꿀 때마다 (space_id, page_no, offset) 로 redo 를 남긴다
 [페이지 플러시...]      쓰기 직전 FIL_PAGE_LSN, 트레일러, 체크섬을 채운다
 [크래시 복구]           page LSN 과 redo LSN 을 비교해 이미 반영된 레코드를 건너뛴다
```

흐름 문서: [버퍼 풀 페이지 획득](../../flows/buffer-pool-fetch/README.md), [B+Tree 삽입과 분할](../../flows/btree-insert/README.md), [페이지 플러시, doublewrite, 체크포인트](../../flows/flush-checkpoint/README.md), [크래시 복구](../../flows/crash-recovery/README.md). 레코드 한 개의 바이트 모양은 [레코드 포맷](../record-format/README.md)에 있다.

## db-engine 에서는

db-engine 의 `Page` 는 4096바이트 배열이고 헤더가 없다. 파일 위치 계산(`pageNumber * PAGE_SIZE`)은 같지만, 페이지 안에 "내가 누구인가"를 적지 않는다.

```text
 같은 문제(파일을 고정 크기 조각으로 자르기), 두 구현 (위 MySQL / 아래 db-engine)

 조각 크기
   MySQL      16KB 기본 (4K ~ 64K 선택). 64장이 익스텐트, 그 위에 세그먼트
   db-engine  4096 고정 (Page.PAGE_SIZE). 묶음 단위 없음

 위치 계산
   MySQL      page_no * page_size.physical()            (fil0fil.cc L7754)
   db-engine  id.pageNumber.toLong() * Page.PAGE_SIZE   (PagedFile.readPage)

 페이지가 자기를 아는가
   MySQL      FIL 헤더에 space_id, page_no, type, page LSN, 체크섬
   db-engine  없음. PageId 는 메모리의 Page 객체에만 있다

 빈 공간 관리
   MySQL      XDES 비트맵 (페이지당 2비트) + 익스텐트 목록 + 세그먼트 inode
   db-engine  allocatePage 가 파일 끝에 0 으로 채운 페이지를 붙인다

 깨진 쓰기 감지
   MySQL      헤더 LSN 과 트레일러 하위 4바이트 비교, 체크섬, doublewrite
   db-engine  없음 (impl 의 과제 1 답이 torn write 위험을 짚는다)
```

db-engine 은 페이지 안에 LSN 이 없어서 08-02 에서 "마지막 적용 LSN"을 별도 메타 파일에 둔다. MySQL 은 그 값을 페이지마다 `FIL_PAGE_LSN` 에 들고 있다. 챕터: [02-01-page-pagedfile](../../../../../project/db-engine/02-01-page-pagedfile/).

## 다루지 않는 것

압축 페이지(`page_zip`, `FIL_PAGE_COMPRESSED`)와 투명 압축 하위 필드, 페이지 암호화, R-tree 와 SDI 페이지의 차이, `FSP_SPACE_FLAGS` 비트 배치(fsp0types.h L226 부터), 공간 확장 규칙(`fsp_get_pages_to_extend_ibd`), 세그먼트 예약 비율(`FSEG_RESERVE_PCT_DFLT`), REDUNDANT 형식의 infimum/supremum, LOB 페이지 레이아웃, undo 페이지 레이아웃([undo 테이블스페이스와 롤백 세그먼트](../undo-segments/README.md)), doublewrite 파일의 모양은 이 문서의 곁가지라 다루지 않았다.
