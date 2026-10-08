# undo 테이블스페이스와 롤백 세그먼트

상위: [MySQL 아키텍처 지도](../../README.md)

undo 레코드 하나가 **어느 파일의 어느 페이지 어느 바이트에 놓이는가**를 위에서 아래로 내려가며 본다. 계층은 다섯 단이다. undo 테이블스페이스가 롤백 세그먼트(rseg)를 최대 128개 갖고, rseg 헤더 페이지가 undo 슬롯 1024개(16KB 페이지 기준)를 갖고, 슬롯 하나가 undo 로그 세그먼트 하나를 가리키고, 그 세그먼트 안에 undo 로그(트랜잭션 하나 몫)가 있고, 그 로그가 undo 레코드를 쌓는다. 레코드가 이 계층의 어디에 놓였는지는 클러스터드 인덱스 레코드의 7바이트 `DB_ROLL_PTR` 가 기억한다. 흐름 쪽에서 undo 가 **쓰이는** 순간은 [B+Tree 삽입과 분할](../../flows/btree-insert/README.md)의 [04] 와 [커밋과 binlog 2PC](../../flows/commit-2pc/README.md)의 [10] 이 다루고, 이 편은 그 둘이 손대는 **자리의 모양**만 본다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 디스크 쪽 계층 (괄호는 개수 상한, 정의 위치)

 undo 테이블스페이스  undo_001, undo_002 ...      (127개, fsp0types.h L408)
   |                  암묵 2개는 항상 있다           (FSP_IMPLICIT_UNDO_TABLESPACES L413)
   |
   +-- page 3  RSEG_ARRAY 페이지                    (FSP_RSEG_ARRAY_PAGE_NO, fsp0types.h L181)
   |           rseg 헤더 페이지 번호의 배열
   |
   +-- rseg 헤더 페이지 (rseg 하나당 한 장)          (128개, FSP_MAX_ROLLBACK_SEGMENTS L394)
         |  history list 의 base node
         |  undo 슬롯 배열 (슬롯 = 4바이트 페이지 번호)
         |                                          (UNIV_PAGE_SIZE / 16, trx0rseg.h L179)
         v
         undo 로그 세그먼트 (슬롯 하나 = 세그먼트 하나)
         |  첫 페이지에 세그먼트 헤더 (상태, 마지막 로그 위치, 페이지 리스트)
         v
         undo 로그 (트랜잭션 하나의 insert 몫 또는 update 몫)
         |  로그 헤더: trx_id, trx_no, history 노드 ...
         v
         undo 레코드 (행 하나의 변경 하나)
            INSERT_REC / UPD_EXIST_REC / UPD_DEL_REC / DEL_MARK_REC
```

```text
 메모리 쪽 대응 (위 계층의 각 단에 객체가 하나씩 있다)

 undo::spaces           Tablespaces          trx0purge.h L786   undo 테이블스페이스 목록
   +-- undo::Tablespace  m_rsegs (Rsegs *)    trx0purge.h L642   테이블스페이스 하나
         +-- Rsegs        vector<trx_rseg_t*>  trx0types.h L331
               +-- trx_rseg_t                 trx0types.h L214   rseg 헤더 페이지 하나
                     insert_undo_list / insert_undo_cached
                     update_undo_list / update_undo_cached
                       +-- trx_undo_t          trx0undo.h L340    undo 로그 하나
                             id      = 슬롯 번호
                             hdr_page_no, hdr_offset = 로그 헤더의 자리
                             top_page_no, top_offset = 마지막 레코드의 자리

 trx_sys->tmp_rsegs     임시 테이블스페이스의 rseg (redo 를 남기지 않는 쪽)  trx0sys.h L693
```

트랜잭션은 이 계층을 **rseg 하나**와 **undo 로그 최대 둘**로 붙잡는다. 영구 테이블과 임시 테이블을 둘 다 고치면 그 묶음이 두 벌이 된다.

```text
 trx_t 가 붙잡는 것 (trx0trx.h L635-L667, trx->rsegs L1012)

 trx->rsegs
   m_redo     trx_undo_ptr_t    undo 테이블스페이스의 rseg (크래시 후 복구 대상)
     rseg          -> trx_rseg_t
     insert_undo   -> trx_undo_t (TRX_UNDO_INSERT)   첫 INSERT 때 붙는다
     update_undo   -> trx_undo_t (TRX_UNDO_UPDATE)   첫 UPDATE/DELETE 때 붙는다
   m_noredo   trx_undo_ptr_t    임시 테이블스페이스의 rseg (복구 대상 아님)
     (같은 세 칸)

 그래서 트랜잭션 하나가 rseg 하나에서 슬롯을 최대 둘 쓴다
 rseg 하나가 동시에 받을 수 있는 트랜잭션 수가 슬롯 수의 절반인 이유다
   TRX_RSEG_MAX_N_TRXS = TRX_RSEG_N_SLOTS / 2   (trx0rseg.h L182)
```

## undo 테이블스페이스와 rseg 의 개수

개수 상한은 `DB_ROLL_PTR` 의 비트 배치에서 나온다. 주석이 그 계산을 직접 적어 두었다.

`storage` / `innobase` / `include` / `fsp0types.h` L393-L413 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/fsp0types.h#L393-L413))

```cpp
// fsp0types.h L393-L413
/** Max number of rollback segments for each UNDO tablespace */
constexpr size_t FSP_MAX_ROLLBACK_SEGMENTS = 128;

/** The maximum number of non-temporary Undo Tablespaces (implicit + explicit)
that can exist at the same time. The limitation comes from the way we encode
rollback pointer. A rollback pointer has 7 bytes and has the following
information in it
  1 bit   : to indicate INSERT UNDO
  7 bits  : for UNDO num
  4 bytes : for page number
  2 bytes : for offset
Because of 7 bits restriction, we can have maximum 128 UNDO Tablespaces, but the
value 0 is used to indicate the system temporary tablespace which we use for
Undo Logs for changes to temporary tables. This is also the maximum permitted
value for this 7-bit "num" identifier. */
constexpr size_t FSP_MAX_UNDO_TABLESPACES = 127;

/** There are exactly two implicit Undo Tablespaces present at any moment
(undo_001 and undo_002), which count against the limit of
FSP_MAX_UNDO_TABLESPACES. */
constexpr size_t FSP_IMPLICIT_UNDO_TABLESPACES = 2;
```

`innodb_rollback_segments` 의 기본값과 최댓값이 둘 다 이 128 이다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L23216-L23226 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L23216-L23226))

```cpp
// ha_innodb.cc L23216-L23226
/*  This is the number of rollback segments per undo tablespace.
This applies to the temporary tablespace, the system tablespace,
and all undo tablespaces. */
static MYSQL_SYSVAR_ULONG(
    rollback_segments, srv_rollback_segments, PLUGIN_VAR_OPCMDARG,
    "Number of rollback segments per tablespace. This applies to the system"
    " tablespace, the temporary tablespace & any undo tablespace.",
    nullptr, innodb_rollback_segments_update,
    FSP_MAX_ROLLBACK_SEGMENTS,     /* Default setting */
    1,                             /* Minimum value */
    FSP_MAX_ROLLBACK_SEGMENTS, 0); /* Maximum value */
```

트랜잭션이 rseg 를 받는 순서는 라운드 로빈이다. 테이블스페이스를 먼저 돌고 rseg 번호를 나중에 올린다. 한 테이블스페이스에 트랜잭션이 몰리지 않게 하는 배치다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L1180-L1192 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L1180-L1192))

```cpp
// trx0trx.cc L1180-L1192
    rseg_counter.fetch_add(1);

    /* Traverse the rsegs like this: (space, rseg_id)
    (0,0), (1,0), ... (n,0), (0,1), (1,1), ... (n,1), ... */
    ulint window =
        current % (target_rollback_segments * target_undo_tablespaces);
    ulint spaces_slot = window % target_undo_tablespaces;
    ulint rseg_slot = window / target_undo_tablespaces;

    current++;

    undo_space = undo::spaces->at(spaces_slot);

```

```text
 get_next_redo_rseg 의 순회 순서 (주석 L1182-L1183)

 (space, rseg)  (0,0) (1,0) ... (n,0)  (0,1) (1,1) ... (n,1)  ...

 비활성(truncate 대상) 테이블스페이스는 건너뛴다  L1199
 받은 rseg 는 trx_ref_count 를 올려 둔다 -> purge 가 그 테이블스페이스를 truncate 하지 못한다
```

## rseg 헤더 페이지

rseg 하나는 디스크에서 페이지 한 장이다. 그 페이지에 history list 의 머리와 undo 슬롯 배열이 같이 있다.

`storage` / `innobase` / `include` / `trx0rseg.h` L178-L211 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0rseg.h#L178-L211))

```cpp
// trx0rseg.h L178-L211
/** Number of undo log slots in a rollback segment file copy */
#define TRX_RSEG_N_SLOTS (UNIV_PAGE_SIZE / 16)

/** Maximum number of transactions supported by a single rollback segment */
#define TRX_RSEG_MAX_N_TRXS (TRX_RSEG_N_SLOTS / 2)

/* Undo log segment slot in a rollback segment header */
/*-------------------------------------------------------------*/
/** Page number of the header page of  an undo log segment */
constexpr uint32_t TRX_RSEG_SLOT_PAGE_NO = 0;
/*-------------------------------------------------------------*/
/** Slot size */
constexpr uint32_t TRX_RSEG_SLOT_SIZE = 4;

/** The offset of the rollback segment header on its page */
constexpr uint32_t TRX_RSEG = FSEG_PAGE_DATA;

/* Transaction rollback segment header */
/*-------------------------------------------------------------*/
/** Maximum allowed size for rollback segment in pages */
constexpr uint32_t TRX_RSEG_MAX_SIZE = 0;
/** Number of file pages occupied by the logs in the history list */
constexpr uint32_t TRX_RSEG_HISTORY_SIZE = 4;
/* The update undo logs for committed transactions */
constexpr uint32_t TRX_RSEG_HISTORY = 8;
/* Header for the file segment where this page is placed */
constexpr uint32_t TRX_RSEG_FSEG_HEADER = 8 + FLST_BASE_NODE_SIZE;
/** Undo log segment slots */
constexpr uint32_t TRX_RSEG_UNDO_SLOTS =
    8 + FLST_BASE_NODE_SIZE + FSEG_HEADER_SIZE;

/** End of undo slots in rollback segment page. */
#define TRX_RSEG_SLOT_END \
  (TRX_RSEG_UNDO_SLOTS + TRX_RSEG_SLOT_SIZE * TRX_RSEG_N_SLOTS)
```

```text
 rseg 헤더 페이지 (16KB 페이지, 오프셋은 페이지 시작 기준)

 0      FIL 헤더 38바이트                      ([테이블스페이스와 페이지])
 38     TRX_RSEG_MAX_SIZE        4    최대 크기(페이지)
 42     TRX_RSEG_HISTORY_SIZE    4    history list 에 묶인 페이지 수
 46     TRX_RSEG_HISTORY        16    history list base node (길이 + 처음 + 끝)
 62     TRX_RSEG_FSEG_HEADER    10    이 페이지가 속한 파일 세그먼트
 72     TRX_RSEG_UNDO_SLOTS   4096    슬롯 1024개 x 4바이트
                                     값 = undo 세그먼트 첫 페이지 번호, 비면 FIL_NULL
 4168   TRX_RSEG_MAX_TRX_NO      8    이 rseg 의 history 에 들어간 가장 큰 trx_no
                                     (trx0rseg.h L213-L216)

 38 = FSEG_PAGE_DATA (fsp0types.h L79), 16 = FLST_BASE_NODE_SIZE (fut0lst.h L50),
 10 = FSEG_HEADER_SIZE (fsp0types.h L94)
```

빈 슬롯은 앞에서부터 처음 만나는 `FIL_NULL` 이다. 1024개가 다 차면 트랜잭션이 `DB_TOO_MANY_CONCURRENT_TRXS` 로 실패한다.

`storage` / `innobase` / `include` / `trx0rseg.ic` L112-L136 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0rseg.ic#L112-L136))

```cpp
// trx0rseg.ic L112-L136
static inline ulint trx_rsegf_undo_find_free(
    trx_rsegf_t *rsegf, /*!< in: rollback segment header */
    mtr_t *mtr)         /*!< in: mtr */
{
  ulint i;
  page_no_t page_no;
  ulint max_slots = TRX_RSEG_N_SLOTS;

#ifdef UNIV_DEBUG
  if (trx_rseg_n_slots_debug) {
    max_slots = std::min(static_cast<ulint>(trx_rseg_n_slots_debug),
                         static_cast<ulint>(TRX_RSEG_N_SLOTS));
  }
#endif

  for (i = 0; i < max_slots; i++) {
    page_no = trx_rsegf_get_nth_undo(rsegf, i, mtr);

    if (page_no == FIL_NULL) {
      return (i);
    }
  }

  return (ULINT_UNDEFINED);
}
```

메모리 쪽 `trx_rseg_t` 는 이 페이지의 자리(`space_id`, `page_no`)와, 그 페이지의 슬롯을 차지한 undo 로그들을 네 목록으로 나눠 든다. history list 에서 **아직 purge 되지 않은 가장 오래된 로그**의 자리도 여기 있다.

`storage` / `innobase` / `include` / `trx0types.h` L255-L313 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0types.h#L255-L313))

```cpp
// include/trx0types.h L255-L313
  /** rollback segment id == the index of its slot in the trx
  system file copy */
  size_t id{};

  /** mutex protecting the fields in this struct except id,space,page_no
  which are constant */
  RsegMutex mutex;

  /** space ID where the rollback segment header is placed */
  space_id_t space_id{};

  /** page number of the rollback segment header */
  page_no_t page_no{};

  /** page size of the relevant tablespace */
  page_size_t page_size;

  /** maximum allowed size in pages */
  page_no_t max_size{};

 private:
  /** current size in pages */
  page_no_t curr_size{};

 public:
  using Undo_list = UT_LIST_BASE_NODE_T_EXTERN(trx_undo_t, undo_list);
  /*--------------------------------------------------------*/
  /* Fields for update undo logs */
  /** List of update undo logs */
  Undo_list update_undo_list;

  /** List of update undo log segments cached for fast reuse */
  Undo_list update_undo_cached;

  /*--------------------------------------------------------*/
  /* Fields for insert undo logs */
  /** List of insert undo logs */
  Undo_list insert_undo_list;

  /** List of insert undo log segments cached for fast reuse */
  Undo_list insert_undo_cached;

  /*--------------------------------------------------------*/

  /** Page number of the last not yet purged log header in the history
  list; FIL_NULL if all list purged */
  page_no_t last_page_no{};

  /** Byte offset of the last not yet purged log header */
  size_t last_offset{};

  /** Transaction number of the last not yet purged log */
  trx_id_t last_trx_no;

  /** true if the last not yet purged log needs purging */
  bool last_del_marks{};

  /** Reference counter to track rseg allocated transactions. */
  std::atomic<size_t> trx_ref_count{};
```

```text
 trx_rseg_t 의 네 목록과 한 꼬리

 insert_undo_list     활성 트랜잭션의 insert undo
 insert_undo_cached   커밋 뒤 재사용 대기 (한 페이지짜리, 3/4 미만 사용)
 update_undo_list     활성 트랜잭션의 update undo
 update_undo_cached   커밋 뒤 재사용 대기

 last_page_no / last_offset / last_trx_no
                      history list 꼬리 = purge 가 다음에 볼 로그
                      trx_purge_add_update_undo_to_history 가 비어 있을 때만 채운다
                      (trx0purge.cc L428-L433)
```

## undo 로그 세그먼트와 undo 로그

슬롯 하나가 가리키는 것은 파일 세그먼트 하나다. 첫 페이지에 세 겹의 헤더가 쌓인다. 페이지 헤더는 모든 undo 페이지에, 세그먼트 헤더는 첫 페이지에만, 로그 헤더는 로그마다 하나씩 있다.

`storage` / `innobase` / `include` / `trx0undo.h` L463-L481 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.h#L463-L481))

```cpp
// trx0undo.h L463-L481
/** The offset of the undo log page header on pages of the undo log */
constexpr uint32_t TRX_UNDO_PAGE_HDR = FSEG_PAGE_DATA;
/*-------------------------------------------------------------*/
/** Transaction undo log page header offsets */
/** @{ */
/** TRX_UNDO_INSERT or TRX_UNDO_UPDATE */
constexpr uint32_t TRX_UNDO_PAGE_TYPE = 0;
/** Byte offset where the undo log records for the LATEST transaction start on
 this page (remember that in an update undo log, the first page can contain
 several undo logs) */
constexpr uint32_t TRX_UNDO_PAGE_START = 2;
/** On each page of the undo log this field contains the byte offset of the
 first free byte on the page */
constexpr uint32_t TRX_UNDO_PAGE_FREE = 4;
/** The file list node in the chain of undo log pages */
constexpr uint32_t TRX_UNDO_PAGE_NODE = 6;
/*-------------------------------------------------------------*/
/** Size of the transaction undo log page header, in bytes */
constexpr uint32_t TRX_UNDO_PAGE_HDR_SIZE = 6 + FLST_NODE_SIZE;
```

`storage` / `innobase` / `include` / `trx0undo.h` L500-L563 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.h#L500-L563))

```cpp
// trx0undo.h L500-L563
/** The offset of the undo log segment header on the first page of the undo
log segment */

constexpr uint32_t TRX_UNDO_SEG_HDR =
    TRX_UNDO_PAGE_HDR + TRX_UNDO_PAGE_HDR_SIZE;
/** Undo log segment header */
/** @{ */
/*-------------------------------------------------------------*/
/** TRX_UNDO_ACTIVE, ... */
constexpr uint32_t TRX_UNDO_STATE = 0;
/** Offset of the last undo log header on the segment header page, 0 if none */
constexpr uint32_t TRX_UNDO_LAST_LOG = 2;
/** Header for the file segment which the undo log segment occupies */
constexpr uint32_t TRX_UNDO_FSEG_HEADER = 4;
/** Base node for the list of pages in the undo log segment; defined only on the
 undo log segment's first page */
constexpr uint32_t TRX_UNDO_PAGE_LIST = 4 + FSEG_HEADER_SIZE;
/*-------------------------------------------------------------*/
/** Size of the undo log segment header */
constexpr uint32_t TRX_UNDO_SEG_HDR_SIZE =
    4 + FSEG_HEADER_SIZE + FLST_BASE_NODE_SIZE;
/** @} */

/** The undo log header. There can be several undo log headers on the first
page of an update undo log segment. */
/** @{ */
/*-------------------------------------------------------------*/
/** Transaction id */
constexpr uint32_t TRX_UNDO_TRX_ID = 0;
/** Transaction number of the transaction; defined only if the log is in a
 history list */
constexpr uint32_t TRX_UNDO_TRX_NO = 8;
/** Defined only in an update undo log: true if the transaction may have done
 delete markings of records, and thus purge is necessary */
constexpr uint32_t TRX_UNDO_DEL_MARKS = 16;
/** Offset of the first undo log record  of this log on the header page; purge
 may remove undo log record from the log start, and therefore this is not
 necessarily the same as this log header end offset */
constexpr uint32_t TRX_UNDO_LOG_START = 18;
/** Transaction UNDO flags in one byte. This is backward compatible as earlier
 we were storing either 1 or 0 for TRX_UNDO_XID_EXISTS. */
constexpr uint32_t TRX_UNDO_FLAGS = 20;
/** true if undo log header includes X/Open XA transaction identification XID */
constexpr uint32_t TRX_UNDO_FLAG_XID = 0x01;
/** true if undo log header includes GTID information from replication */
constexpr uint32_t TRX_UNDO_FLAG_GTID = 0x02;
/** true if undo log header includes GTID information for XA PREPARE */
constexpr uint32_t TRX_UNDO_FLAG_XA_PREPARE_GTID = 0x04;
/** true if the transaction is a table create, index create, or drop
 transaction: in recovery the transaction cannot be rolled back in the usual
 way: a 'rollback' rather means dropping the created or dropped table, if it
 still exists */
constexpr uint32_t TRX_UNDO_DICT_TRANS = 21;
/** Id of the table if the preceding field is true. Note: deprecated */
constexpr uint32_t TRX_UNDO_TABLE_ID = 22;
/** Offset of the next undo log header on this page, 0 if none */
constexpr uint32_t TRX_UNDO_NEXT_LOG = 30;
/** Offset of the previous undo log header on this page, 0 if none */
constexpr uint32_t TRX_UNDO_PREV_LOG = 32;
/** If the log is put to the history list, the file list node is here */
constexpr uint32_t TRX_UNDO_HISTORY_NODE = 34;
/*-------------------------------------------------------------*/
/** Size of the undo log header without XID information */
constexpr uint32_t TRX_UNDO_LOG_OLD_HDR_SIZE = 34 + FLST_NODE_SIZE;
```

```text
 undo 세그먼트 첫 페이지 (오프셋은 페이지 시작 기준)

 0    FIL 헤더                                38
 38   TRX_UNDO_PAGE_HDR (모든 undo 페이지)
        +0  PAGE_TYPE   2   TRX_UNDO_INSERT 또는 TRX_UNDO_UPDATE
        +2  PAGE_START  2   이 페이지에서 최신 로그의 레코드가 시작하는 곳
        +4  PAGE_FREE   2   첫 빈 바이트. 다음 레코드가 여기 붙는다
        +6  PAGE_NODE  12   세그먼트 페이지 리스트의 노드
 56   TRX_UNDO_SEG_HDR (첫 페이지에만)
        +0  STATE       2   ACTIVE / CACHED / TO_FREE / TO_PURGE / PREPARED ...
        +2  LAST_LOG    2   이 페이지의 마지막 로그 헤더 오프셋
        +4  FSEG_HEADER 10
        +14 PAGE_LIST  16   세그먼트 페이지 리스트의 base node
 86   첫 undo 로그 헤더
        +0  TRX_ID      8
        +8  TRX_NO      8   history list 에 들어갈 때만 의미가 있다
        +16 DEL_MARKS   2   purge 가 할 일이 있는가
        +18 LOG_START   2   첫 레코드 위치
        +20 FLAGS       1   XID / GTID 가 뒤따르는가
        +21 DICT_TRANS  1
        +22 TABLE_ID    8   (deprecated)
        +30 NEXT_LOG    2   같은 페이지의 다음 로그 헤더
        +32 PREV_LOG    2   같은 페이지의 이전 로그 헤더
        +34 HISTORY_NODE 12 history list 의 노드 <-- rseg 헤더의 TRX_RSEG_HISTORY 가 여기를 잇는다
      (+46 부터 FLAGS 에 따라 XID 와 GTID)
      그 뒤로 undo 레코드들

 56 = 38 + 18 (TRX_UNDO_PAGE_HDR_SIZE), 86 = 56 + 30 (TRX_UNDO_SEG_HDR_SIZE)
```

한 페이지에 로그 헤더가 여럿일 수 있는 것은 update undo 세그먼트가 **캐시되어 재사용될 때**다. 세그먼트 헤더 주석이 그 경우를 설명한다(trx0undo.h L491-L498). 그래서 `NEXT_LOG` / `PREV_LOG` 가 있다.

메모리 쪽 `trx_undo_t` 는 이 로그 하나의 좌표 묶음이다. 레코드를 붙일 자리와 되돌릴 때 꺼낼 자리를 이 객체가 들고 있다.

`storage` / `innobase` / `include` / `trx0undo.h` L375-L431 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.h#L375-L431))

```cpp
// trx0undo.h L375-L431
  /*-----------------------------*/
  ulint id;        /*!< undo log slot number within the
                   rollback segment */
  ulint type;      /*!< TRX_UNDO_INSERT or
                   TRX_UNDO_UPDATE */
  ulint state;     /*!< state of the corresponding undo log
                   segment */
  bool del_marks;  /*!< relevant only in an update undo
                    log: this is true if the transaction may
                    have delete marked records, because of
                    a delete of a row or an update of an
                    indexed field; purge is then
                    necessary; also true if the transaction
                    has updated an externally stored
                    field */
  trx_id_t trx_id; /*!< id of the trx assigned to the undo
                   log */
  XID xid;         /*!< X/Open XA transaction
                   identification */
  ulint flag;      /*!< flag for current transaction XID and GTID.
                   Persisted in TRX_UNDO_FLAGS flag of undo header. */
  // ... (L396-L400 생략: GTID 저장 칸과 dict_operation)
  trx_rseg_t *rseg;    /*!< rseg where the undo log belongs */
  /*-----------------------------*/
  space_id_t space; /*!< space id where the undo log
                    placed */
  page_size_t page_size;
  page_no_t hdr_page_no;  /*!< page number of the header page in
                          the undo log */
  ulint hdr_offset;       /*!< header offset of the undo log on
                          the page */
  page_no_t last_page_no; /*!< page number of the last page in the
                          undo log; this may differ from
                          top_page_no during a rollback */
  ulint size;             /*!< current size in pages */
  /*-----------------------------*/
  ulint empty;              /*!< true if the stack of undo log
                            records is currently empty */
  page_no_t top_page_no;    /*!< page number where the latest undo
                            log record was catenated; during
                            rollback the page from which the latest
                            undo record was chosen */
  ulint top_offset;         /*!< offset of the latest undo record,
                            i.e., the topmost element in the undo
                            log if we think of it as a stack */
  undo_no_t top_undo_no;    /*!< undo number of the latest record */
  buf_block_t *guess_block; /*!< guess for the buffer block where
                            the top page might reside */
  /*-----------------------------*/
  UT_LIST_NODE_T(trx_undo_t) undo_list;
  /*!< undo log objects in the rollback
  segment are chained into lists */
};
```

## insert undo 와 update undo

두 종류의 차이는 **커밋 뒤에도 누가 그 로그를 필요로 하는가**다. 새로 넣은 행의 이전 버전은 없으니 insert undo 는 롤백에만 쓰이고, 커밋하면 바로 버려진다. update undo 는 이전 버전을 담고 있어서 커밋 뒤에도 그 버전을 볼 수 있는 ReadView 가 남아 있는 동안 지울 수 없다.

`storage` / `innobase` / `include` / `trx0undo.h` L310-L334 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.h#L310-L334))

```cpp
// trx0undo.h L310-L334
/** Types of an undo log segment */
/** contains undo entries for inserts */
constexpr uint32_t TRX_UNDO_INSERT = 1;
/** contains undo entries for updates and delete markings: in short, modifys
 (the name 'UPDATE' is a historical relic) */
constexpr uint32_t TRX_UNDO_UPDATE = 2;

/* States of an undo log segment */
/** contains an undo log of an active  transaction */
constexpr uint32_t TRX_UNDO_ACTIVE = 1;
/** cached for quick reuse */
constexpr uint32_t TRX_UNDO_CACHED = 2;
/** insert undo segment can be freed */
constexpr uint32_t TRX_UNDO_TO_FREE = 3;
/** update undo segment will not be reused: it can be freed in purge when all
 undo data in it is removed */
constexpr uint32_t TRX_UNDO_TO_PURGE = 4;
/** contains an undo log of an prepared transaction for a server version older
 * than 8.0.29 */
constexpr uint32_t TRX_UNDO_PREPARED_80028 = 5;
/** contains an undo log of an prepared transaction */
constexpr uint32_t TRX_UNDO_PREPARED = 6;
/* contains an undo log of a prepared transaction that has been processed by the
 * transaction coordinator */
constexpr uint32_t TRX_UNDO_PREPARED_IN_TC = 7;
```

```text
 두 종류의 수명 (커밋 시점의 갈림은 [커밋과 binlog 2PC] [10])

                 insert undo                    update undo
 담는 레코드     INSERT_REC                     UPD_EXIST_REC, UPD_DEL_REC, DEL_MARK_REC
 쓰는 때         새 행 삽입                     갱신, delete mark
 읽는 이         롤백                           롤백, MVCC 이전 버전, purge
 커밋 뒤 상태    CACHED 또는 TO_FREE            CACHED 또는 TO_PURGE
 커밋 뒤 행방    trx_undo_insert_cleanup        trx_purge_add_update_undo_to_history
                 세그먼트를 바로 해제하거나       history list 머리에 붙는다
                 insert_undo_cached 로          purge 가 다 치운 뒤 해제
                 (trx0undo.cc L1960)             (trx0purge.cc L352)
```

커밋할 때 세 상태 가운데 하나를 고르는 곳이다. 재사용 조건(한 페이지이고 3/4 미만 사용)이 종류보다 먼저 걸린다.

`storage` / `innobase` / `trx` / `trx0undo.cc` L1811-L1829 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0undo.cc#L1811-L1829))

```cpp
// trx0undo.cc L1811-L1829
page_t *trx_undo_set_state_at_finish(trx_undo_t *undo, mtr_t *mtr) {
  ut_a(undo->id < TRX_RSEG_N_SLOTS);

  page_t *undo_page = trx_undo_page_get(
      page_id_t(undo->space, undo->hdr_page_no), undo->page_size, mtr);

  trx_usegf_t *seg_hdr = undo_page + TRX_UNDO_SEG_HDR;
  trx_upagef_t *page_hdr = undo_page + TRX_UNDO_PAGE_HDR;

  ulint state;
  if (trx_undo_reusable(undo, page_hdr)) {
    state = TRX_UNDO_CACHED;
  } else if (undo->type == TRX_UNDO_INSERT) {
    state = TRX_UNDO_TO_FREE;
  } else {
    state = TRX_UNDO_TO_PURGE;
  }

  undo->state = state;
```

undo 로그를 처음 붙일 때는 캐시부터 본다. 캐시가 비어 있을 때만 슬롯을 새로 찾아 세그먼트를 만든다.

`storage` / `innobase` / `trx` / `trx0undo.cc` L1747-L1772 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0undo.cc#L1747-L1772))

```cpp
// trx0undo.cc L1747-L1772
  undo =
// ... (L1748-L1752 생략: 디버그 빌드의 슬롯 고갈 주입)
          trx_undo_reuse_cached(rseg, type, trx->id, trx->xid, gtid_storage,
                                &mtr);

  if (undo == nullptr) {
    err = trx_undo_create(rseg, type, trx->id, trx->xid, gtid_storage, &undo,
                          &mtr);
    if (err != DB_SUCCESS) {
      goto func_exit;
    }
  }

  if (type == TRX_UNDO_INSERT) {
    UT_LIST_ADD_FIRST(rseg->insert_undo_list, undo);
    ut_ad(undo_ptr->insert_undo == nullptr);
    undo_ptr->insert_undo = undo;
  } else {
    UT_LIST_ADD_FIRST(rseg->update_undo_list, undo);
    ut_ad(undo_ptr->update_undo == nullptr);
    undo_ptr->update_undo = undo;
  }
```

## undo 레코드

레코드는 페이지 안의 이중 연결이다. 앞 2바이트가 다음 레코드 오프셋, 끝 2바이트가 자기 시작 오프셋이다. 그 시작 오프셋이 곧 `DB_ROLL_PTR` 의 offset 칸이 된다.

`storage` / `innobase` / `include` / `trx0rec.h` L293-L319 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0rec.h#L293-L319))

```cpp
// trx0rec.h L293-L319

/* Types of an undo log record: these have to be smaller than 16, as the
compilation info multiplied by 16 is ORed to this value in an undo log
record */

/** fresh insert into clustered index */
constexpr uint32_t TRX_UNDO_INSERT_REC = 11;
/** update of a non-delete-marked  record */
constexpr uint32_t TRX_UNDO_UPD_EXIST_REC = 12;
/** update of a delete marked record to a not delete marked record; also the
fields of the record can change */
constexpr uint32_t TRX_UNDO_UPD_DEL_REC = 13;
/* delete marking of a record; fields do not change */
constexpr uint32_t TRX_UNDO_DEL_MARK_REC = 14;
/** compilation info is multiplied by this and ORed to the type above */
constexpr uint32_t TRX_UNDO_CMPL_INFO_MULT = 16;
/** If this bit is set in type_cmpl,  then the undo log record has support for
 partial update of BLOBs. Also to  make the undo log format extensible,
 introducing a new flag next to the  type_cmpl flag. */
constexpr uint32_t TRX_UNDO_MODIFY_BLOB = 64;
/* This bit can be ORed to type_cmpl to denote that we updated external storage
 fields: used by purge to free the external storage */
constexpr uint32_t TRX_UNDO_UPD_EXTERN = 128;

/** Operation type flags used in trx_undo_report_row_operation */
constexpr uint32_t TRX_UNDO_INSERT_OP = 1;
constexpr uint32_t TRX_UNDO_MODIFY_OP = 2;
```

```text
 undo 레코드 한 개 (가변 길이, 숫자는 바이트)

 INSERT_REC  (trx_undo_page_report_insert, trx0rec.cc L483)
   next  2 | type 1 | undo_no (압축) | table_id (압축) | 유일 키 필드들 (길이+값) | start 2
                                                       PK 만 있으면 롤백 때 지울 행을 찾는다

 UPD_EXIST_REC / UPD_DEL_REC / DEL_MARK_REC  (trx_undo_page_report_modify, L1153)
   next  2 | type_cmpl 1 | flag 1 | undo_no | table_id
           | info_bits 1 | 옛 DB_TRX_ID | 옛 DB_ROLL_PTR    L1250, L1266, L1272
           | 유일 키 필드들                                  L1275
           | 바뀐 필드의 옛 값들                              L1303
           | start 2

 옛 DB_ROLL_PTR 를 담는 칸이 이전 버전으로 가는 다리다
 MVCC 는 이 칸을 따라 한 단계씩 과거로 간다
```

```text
 페이지 안의 연결 (trx_undo_page_set_next_prev_and_add, trx0rec.cc L184)

   PAGE_FREE = f
   [next][ ... 레코드 본문 ... ][prev=f]
   ^ f                                  ^ end_of_rec
   1. 레코드 끝에 시작 오프셋 f 를 쓴다            L209
   2. 레코드 앞 2바이트(f 자리)에 end_of_rec 을 쓴다 L215
   3. PAGE_FREE 를 end_of_rec 으로 옮긴다          L218
   4. f 를 돌려준다 -> roll_ptr 의 offset 이 된다  L223
```

## DB_ROLL_PTR - 레코드에서 undo 로 가는 주소

클러스터드 인덱스 레코드의 숨은 열 `DB_ROLL_PTR` 7바이트(`DATA_ROLL_PTR_LEN`, data0type.h L191)가 이 계층의 좌표다. **rseg 번호는 들어 있지 않다.** 테이블스페이스 번호와 페이지, 오프셋만으로 레코드를 찾는다.

`storage` / `innobase` / `include` / `trx0undo.ic` L45-L73 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0undo.ic#L45-L73))

```cpp
// trx0undo.ic L45-L73
inline roll_ptr_t trx_undo_build_roll_ptr(bool is_insert, space_id_t space_id,
                                          page_no_t page_no, ulint offset) {
  ut_ad(offset < 65536);

  ulint id = (fsp_is_undo_tablespace(space_id) ? undo::id2num(space_id) : 0);

  roll_ptr_t roll_ptr = (roll_ptr_t)is_insert << 55 | (roll_ptr_t)id << 48 |
                        (roll_ptr_t)page_no << 16 | offset;
  return (roll_ptr);
}

/** Decodes a roll pointer.
param[in]  roll_ptr   roll pointer
param[out] is_insert  true if insert undo log
param[out] undo_num   undo number
param[out] page_no    page number
param[out] offset     offset of the undo entry within page */
inline void trx_undo_decode_roll_ptr(roll_ptr_t roll_ptr, bool *is_insert,
                                     ulint *undo_num, page_no_t *page_no,
                                     ulint *offset) {
  ut_ad(roll_ptr < (1ULL << 56));
  *offset = (ulint)roll_ptr & 0xFFFF;
  roll_ptr >>= 16;
  *page_no = (ulint)roll_ptr & 0xFFFFFFFF;
  roll_ptr >>= 32;
  *undo_num = (ulint)roll_ptr & 0x7F;
  roll_ptr >>= 7;
  *is_insert = roll_ptr; /* true==1 */
}
```

```text
 roll_ptr 비트 배치 (56비트를 7바이트로)

  55     54 ......... 48  47 ................. 16  15 ........... 0
 +------+---------------+-----------------------+-----------------+
 |insert| undo space num|       page_no         |     offset      |
 | 1bit |    7 bits     |       32 bits         |     16 bits     |
 +------+---------------+-----------------------+-----------------+
   |         |                  |                     |
   |         |                  |                     +-- 레코드 시작 (위의 f)
   |         |                  +-- undo 페이지 번호
   |         +-- undo::id2num(space_id). 임시 테이블스페이스면 0
   +-- insert undo 인가. 1 이면 이 레코드가 처음 넣은 버전이라 더 과거가 없다
       (trx_undo_prev_version_build, trx0rec.cc L2479-L2482)

 7비트 = 0 은 임시 테이블스페이스 몫이라 실제 undo 테이블스페이스는 1..127
   -> FSP_MAX_UNDO_TABLESPACES = 127 의 근거 (fsp0types.h L396-L407)
```

## history list 에 붙는 자리

history list 는 **rseg 마다 하나**인 디스크 위의 연결 리스트다. 머리는 rseg 헤더의 `TRX_RSEG_HISTORY`, 노드는 각 update undo 로그 헤더의 `TRX_UNDO_HISTORY_NODE` 다. 커밋한 트랜잭션의 update undo 는 **머리**에 붙고, purge 는 꼬리(가장 오래된 trx_no)부터 읽는다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L376-L434 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L376-L434))

```cpp
// trx0purge.cc L376-L434
  if (undo->state != TRX_UNDO_CACHED) {
    ulint hist_size;
#ifdef UNIV_DEBUG
    trx_usegf_t *seg_header = undo_page + TRX_UNDO_SEG_HDR;
#endif /* UNIV_DEBUG */

    /* The undo log segment will not be reused */

    if (UNIV_UNLIKELY(undo->id >= TRX_RSEG_N_SLOTS)) {
      ib::fatal(UT_LOCATION_HERE, ER_IB_MSG_1165) << "undo->id is " << undo->id;
    }

    trx_rsegf_set_nth_undo(rseg_header, undo->id, FIL_NULL, mtr);

    MONITOR_DEC(MONITOR_NUM_UNDO_SLOT_USED);

    hist_size =
        mtr_read_ulint(rseg_header + TRX_RSEG_HISTORY_SIZE, MLOG_4BYTES, mtr);

    ut_ad(undo->size == flst_get_len(seg_header + TRX_UNDO_PAGE_LIST));

    mlog_write_ulint(rseg_header + TRX_RSEG_HISTORY_SIZE,
                     hist_size + undo->size, MLOG_4BYTES, mtr);
  }

  /* Add the log as the first in the history list */
  flst_add_first(rseg_header + TRX_RSEG_HISTORY,
                 undo_header + TRX_UNDO_HISTORY_NODE, mtr);

  if (update_rseg_history_len) {
    trx_sys->rseg_history_len.fetch_add(n_added_logs);
    if (trx_sys->rseg_history_len.load() >
        srv_n_purge_threads * srv_purge_batch_size) {
      srv_wake_purge_thread_if_not_active();
    }
  }

  /* Update maximum transaction number for this rollback segment. */
  mlog_write_ull(rseg_header + TRX_RSEG_MAX_TRX_NO, trx->no, mtr);

  /* Write the trx number to the undo log header */
  mlog_write_ull(undo_header + TRX_UNDO_TRX_NO, trx->no, mtr);

  /* Write information about delete markings to the undo log header */

  if (!undo->del_marks) {
    mlog_write_ulint(undo_header + TRX_UNDO_DEL_MARKS, false, MLOG_2BYTES, mtr);
  }

  /* Write GTID information if there. */
  trx_undo_gtid_write(trx, undo_header, undo, mtr, false);

  if (rseg->last_page_no == FIL_NULL) {
    rseg->last_page_no = undo->hdr_page_no;
    rseg->last_offset = undo->hdr_offset;
    rseg->last_trx_no = trx->no;
    rseg->last_del_marks = undo->del_marks;
  }
}
```

```text
 rseg 하나의 history list (trx0purge.cc L376-L433)

 rseg 헤더 페이지
   TRX_RSEG_HISTORY  [len | first | last]
                        |        |
                        v        v
   undo 로그 헤더 (trx_no=105) <-> (trx_no=98) <-> ... <-> (trx_no=41)
   방금 커밋 = 머리                                         꼬리 = rseg->last_*
   flst_add_first L402                                       purge 가 여기서 시작

 붙일 때 같이 바뀌는 것
   L388  세그먼트를 재사용하지 않을 거면 슬롯을 FIL_NULL 로 비운다
         -> 슬롯은 커밋 즉시 돌아오고, 페이지는 history 가 붙잡는다
   L397  TRX_RSEG_HISTORY_SIZE += 세그먼트 페이지 수
   L406  trx_sys->rseg_history_len += n_added_logs  (SHOW ENGINE INNODB STATUS 의 History list length)
       보통 1. 영구와 임시 update undo 가 둘 다 있으면 임시 쪽 호출이 2 를 한 번에 더한다
       (trx0trx.cc L1631)
   L409  길이가 purge 스레드 수 x 배치 크기를 넘으면 purge 를 깨운다
   L414  TRX_RSEG_MAX_TRX_NO = trx->no
   L417  로그 헤더 TRX_UNDO_TRX_NO = trx->no
```

rseg 가 여러 개라 history list 도 여러 개다. purge 는 rseg 들 사이에서 **가장 작은 trx_no** 를 고르기 위해 rseg 를 trx_no 순 큐에 넣어 둔다. 그 큐에 넣는 일은 커밋의 `trx_serialisation_number_get` 이 한다([커밋과 binlog 2PC](../../flows/commit-2pc/10_trx_commit_low/README.md) 의 L1596 주석 "Will set trx->no and will add rseg to purge queue").

## db-engine 에서는

db-engine 은 이전 버전을 **같은 키의 버전 리스트**에 함께 쌓는다. MySQL 은 최신 버전만 페이지에 두고 이전 버전을 별도 공간(undo)에 둔다.

```text
 같은 문제(이전 버전을 어디에 두는가), 두 구현 (위 MySQL / 아래 db-engine)

 이전 버전의 자리
   MySQL      undo 테이블스페이스 -> rseg -> 슬롯 -> undo 로그 -> undo 레코드
              클러스터드 레코드에는 최신 값 + DB_TRX_ID + DB_ROLL_PTR 만 남는다
   db-engine  MVCCStore.chains: ConcurrentHashMap<K, MutableList<Version<V>>>
              Version(value, xidStart, xidEnd) 가 전부 메모리 리스트에 있다

 버전 사이의 연결
   MySQL      undo 레코드 안의 옛 DB_ROLL_PTR -> 한 단계 이전 undo 레코드
   db-engine  리스트 인덱스. get() 이 뒤에서부터 선형 탐색

 삭제
   MySQL      delete mark + DEL_MARK_REC. 실제 삭제는 purge 가 한다
   db-engine  tombstone 버전 Version(null, xid) 를 하나 더 쌓는다

 정리
   MySQL      update undo 는 history list 로, purge 가 trx_no 순으로 치운다
   db-engine  없음. 10-01 은 "in-memory 데모", 10-03 은 "vacuum 없음, version chain 누적"
```

db-engine 10-03 은 디스크 `TableHeap` 위에 버전 체인을 얹되 체인은 메모리에 두어서, 재시작하면 버전 정보가 사라진다고 스스로 적었다. MySQL 의 undo 는 페이지에 있고 redo 로 보호되므로 크래시 뒤에도 남는다. 그래서 [크래시 복구](../../flows/crash-recovery/README.md)가 undo 를 읽어 미완료 트랜잭션을 되돌릴 수 있다. 챕터: [10-01-mvcc](../../../../../project/db-engine/10-01-mvcc/), [10-03-mvcc-table-heap](../../../../../project/db-engine/10-03-mvcc-table-heap/).

## 어디에서 쓰이는가

```text
 [B+Tree 삽입과 분할] [04] btr_cur_ins_lock_and_undo
     trx_undo_report_row_operation 이 insert undo 를 쓰고 roll_ptr 를 받는다
 [커밋과 binlog 2PC] [10] trx_commit_low
     insert undo 는 해제/캐시, update undo 는 history list 머리로
 [일관 읽기(MVCC)]   레코드의 DB_ROLL_PTR 를 따라 undo 레코드에서 이전 버전을 만든다
 [purge]             rseg 들의 history list 꼬리부터 읽어 delete mark 된 행을 지운다
 [크래시 복구]       trx_resurrect 가 rseg 의 insert/update undo 목록에서
                     미완료 트랜잭션을 되살린다 (trx0trx.cc L1111-L1113)
 [메모리 구조]       trx_t 의 rsegs, trx_sys 의 rseg_history_len 이 이 계층을 붙잡는다
```

쓰는 순간은 [B+Tree 삽입과 분할](../../flows/btree-insert/04_btr_cur_ins_lock_and_undo/README.md), history 로 넘어가는 순간은 [trx_commit_low](../../flows/commit-2pc/10_trx_commit_low/README.md)에 있다. 읽는 쪽은 [일관 읽기(MVCC)](../../flows/mvcc-read/README.md)와 [purge](../../flows/purge/README.md)다. undo 페이지가 놓이는 파일과 FIL 헤더는 [테이블스페이스와 페이지 레이아웃](../tablespace-page/README.md), `DB_ROLL_PTR` 가 레코드 안 어디에 있는지는 [레코드 포맷](../record-format/README.md), 메모리 객체끼리의 연결은 [메모리 구조](../memory-structures/README.md)에 있다.

## 다루지 않는 것

시스템 테이블스페이스의 rseg 0(`TRX_SYS_SYSTEM_RSEG_ID`, page 6)과 업그레이드 경로, undo 테이블스페이스 truncate(`innodb_undo_log_truncate`, `undo::Truncate`)와 `CREATE/DROP UNDO TABLESPACE` 의 상태 전이(`Rsegs` 의 ACTIVE / INACTIVE_IMPLICIT / INACTIVE_EXPLICIT / EMPTY), undo 테이블스페이스 space_id 의 예약 범위 계산(`undo::num2id`, `id2num`), 로그 헤더 뒤 XID 와 GTID 영역의 세부, LOB 부분 갱신의 undo(`TRX_UNDO_MODIFY_BLOB`, `lob::undo_vers_t`), 가상 열의 undo, 압축 정수 인코딩(`mach_u64_write_much_compressed`), undo 암호화는 이 편의 곁가지라 요약만 했다.
