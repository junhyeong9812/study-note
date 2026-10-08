# 메모리 구조

상위: [MySQL 아키텍처 지도](../../README.md)

InnoDB 가 메모리에 들고 있는 **네 개의 전역 객체**와 그것들이 서로를 가리키는 모양을 본다. 버퍼 풀 `buf_pool_ptr`(페이지), 잠금 시스템 `lock_sys`(레코드와 테이블 잠금), 트랜잭션 시스템 `trx_sys`(활성 트랜잭션과 ReadView 목록), 그리고 그 사이를 오가는 `trx_t` 다. 이 넷은 포인터로 직접 묶여 있지 않다. **잠금은 페이지 번호로, 트랜잭션은 트랜잭션 id 로, 페이지는 (space, page_no) 로** 서로를 찾는다. 이 편은 그 자리와 모양만 보고, 실제로 페이지를 찾아오는 길은 [버퍼 풀 페이지 획득](../../flows/buffer-pool-fetch/README.md), 잠금을 거는 길은 [레코드 잠금과 교착](../../flows/record-lock/README.md), 스냅샷을 만드는 길은 [일관 읽기(MVCC)](../../flows/mvcc-read/README.md)가 다룬다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 전역 객체 넷과 그 사이의 열쇠

 buf_pool_ptr[]  (buf0buf.h L117)             lock_sys  (lock0lock.h L1177)
 buf_pool_t x innodb_buffer_pool_instances     lock_sys_t 하나
   page_hash: (space, page_no) -> buf_page_t   rec_hash: page_id.hash() -> lock_t 체인
   LRU / free / flush_list                     latches: global + page 샤드 512 + table 샤드 512
          ^                                              |
          | page_id (space, page_no)                     | lock_t.trx
          | lock_rec_t.page_id 가 같은 열쇠를 쓴다        v
          +---------------------------------------  trx_t
                                                     id, no, state
                                                     read_view  --> ReadView
                                                     lock.trx_locks --> 내 lock_t 들
                                                     lock.wait_lock --> 기다리는 lock_t
                                                     rsegs --> trx_rseg_t, trx_undo_t
                                                          ^
                                                          | trx_id -> trx_t
 trx_sys  (trx0sys.h L64)                                 |
 trx_sys_t 하나                                           |
   shards[256]  trx_id % 256 -> active_rw_trxs (id -> trx_t)
   rw_trx_list  활성 rw 트랜잭션 (id 큰 순)
   rw_trx_ids   스냅샷이 복사해 가는 활성 id 배열
   mvcc -> MVCC  m_views (활성 ReadView 목록)
   rseg_history_len, next_trx_id_or_no
```

```text
 누가 누구를 직접 가리키고, 누가 열쇠로만 찾는가

 직접 포인터                               열쇠로 찾기
 lock_t.trx            -> trx_t            lock_t  -> 페이지    page_id 로 page_hash 조회
 trx_t.lock.wait_lock  -> lock_t           페이지  -> lock_t    page_id 로 rec_hash 조회
 trx_t.read_view       -> ReadView         레코드  -> trx_t     DB_TRX_ID 로 trx_sys->shards 조회
 trx_t.rsegs.m_redo    -> trx_rseg_t       ReadView -> trx      id 비교만 한다. 포인터 없음
 buf_block_t.page      (첫 필드, 같은 주소)

 잠금은 버퍼 블록을 포인터로 잡지 않고 page_id 와 heap_no 비트만 기억한다
 (lock_rec_t, lock0priv.h L83-L91). 블록을 LRU 에서 내보내는 buf0lru.cc 는
 lock_sys 를 건드리지 않으므로, 페이지가 쫓겨나도 잠금 큐는 rec_hash 에 그대로 남는다
```

## 버퍼 풀

버퍼 풀은 인스턴스 여러 개의 배열이다. 페이지가 어느 인스턴스에 가는지는 페이지 번호의 아래 6비트를 버린 `page_id_t(space, page_no >> 6)` 의 `hash()` 를 인스턴스 수로 나눈 나머지로 정한다. 그래서 page_no 가 64k 부터 64k+63 까지인, 64 로 정렬된 연속 64페이지는 항상 같은 인스턴스에 간다. 주석(L824)이 말하는 `BUF_READ_AHEAD_AREA` 매크로는 이 태그에 없고, 지금은 인스턴스마다 `read_ahead_area = min(BUF_READ_AHEAD_PAGES(64), ...)` 를 둔다(buf0buf.cc L300, L1351-L1353). read-ahead 는 이 크기로 정렬한 구역 `[low, high)` 를 처음에 `buf_pool_get(page_id)` 로 얻은 **인스턴스 하나**의 page_hash 에서만 확인한다(buf0rea.cc L155, L182-L186, L213). 이것이 64페이지 단위로 인스턴스를 묶는 코드상의 근거다.

`storage` / `innobase` / `include` / `buf0buf.ic` L823-L832 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.ic#L823-L832))

```cpp
// buf0buf.ic L823-L832
static inline buf_pool_t *buf_pool_get(const page_id_t &page_id) {
  /* 2log of BUF_READ_AHEAD_AREA (64) */
  page_no_t ignored_page_no = page_id.page_no() >> 6;

  page_id_t id(page_id.space(), ignored_page_no);

  ulint i = id.hash() % srv_buf_pool_instances;

  return (&buf_pool_ptr[i]);
}
```

```text
 buf_pool_get 의 인스턴스 선택 (hash 는 buf0types.h L247-L250)

 page_no      0 ..  63   ->  g = 0  \
 page_no     64 .. 127   ->  g = 1   |  g = page_no >> 6   (L825)
 page_no    128 .. 191   ->  g = 2  /
                               |
                               v
 page_id_t(space, g).hash() = ((space << 20) + space + g) ^ 1653893711
                               |
                               v
 i = hash % srv_buf_pool_instances                      (L829)

 같은 g 의 64페이지는 i 가 같다. 이웃한 g 끼리는 hash 가 1 씩 다른 값의 XOR 이라 보통 다른 인스턴스로 흩어진다
 인스턴스 안의 page_hash 는 원래 page_id 의 hash() 를 쓴다 (g 가 아니다)
```

인스턴스 하나는 해시 하나와 리스트 셋을 갖고, 리스트마다 뮤텍스가 따로 있다.

`storage` / `innobase` / `include` / `buf0buf.h` L2293-L2483 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.h#L2293-L2483))

```cpp
// include/buf0buf.h L2293-L2483
struct buf_pool_t {
  // ... (L2294-L2303 생략: chunks_mutex 설명)
  /** LRU list mutex */
  BufListMutex LRU_list_mutex;

  /** free and withdraw list mutex */
  BufListMutex free_list_mutex;
  // ... (L2309-L2322 생략: buddy, zip 뮤텍스)
  /** Array index of this buffer pool instance */
  ulint instance_no;
  // ... (L2325-L2358 생략: 크기, chunk, read-ahead 필드)
  /** Hash table of buf_page_t or buf_block_t file pages, buf_page_in_file() ==
  true, indexed by (space_id, offset).  page_hash is protected by an array of
  mutexes. */
  hash_table_t *page_hash;
  // ... (L2363-L2392 생략: zip_hash, 통계)
  /** Mutex protecting the flush list access. This mutex protects flush_list and
  bpage::list pointers when the bpage is on flush_list. It also protects writes
  to bpage::oldest_modification and flush_list_hp */
  BufListMutex flush_list_mutex;
  // ... (L2397-L2404 생략: hazard pointer)
  /** Base node of the modified block list */
  UT_LIST_BASE_NODE_T(buf_page_t, list) flush_list;
  // ... (L2407-L2447 생략: flush 상태, LRU scan 플래그)
  /** Base node of the free block list */
  UT_LIST_BASE_NODE_T(buf_page_t, list) free;
  // ... (L2450-L2470 생략: withdraw 목록, LRU 반복자)
  /** Base node of the LRU list */
  UT_LIST_BASE_NODE_T(buf_page_t, LRU) LRU;

  /** Pointer to the about LRU_old_ratio/BUF_LRU_OLD_RATIO_DIV oldest blocks in
  the LRU list; NULL if LRU length less than BUF_LRU_OLD_MIN_LEN; NOTE: when
  LRU_old != NULL, its length should always equal LRU_old_len */
  buf_page_t *LRU_old;
  // ... (L2478-L2482 생략: LRU_old_len 주석)
  ulint LRU_old_len;
```

```text
 buf_pool_t 인스턴스 하나 (buf0buf.h L2293)

  page_hash  (L2362)    (space, page_no) -> buf_page_t
  +-------+             체인 노드는 buf_page_t.hash (L1614)
  | cell  |--> bpage --> bpage --> null
  | cell  |--> bpage
  +-------+             셀 여러 개가 rw_lock (hash_lock) 하나를 나눠 쓴다
                        인스턴스당 srv_n_page_hash_locks 개, 기본 16
                        (srv0srv.cc L432, buf0buf.cc L1366-L1368)

  free  (L2449)         아직 아무 페이지도 담지 않은 블록      free_list_mutex
  LRU   (L2472)         파일 페이지를 담은 모든 블록            LRU_list_mutex
        [ young ............ | old ............ ]
                             ^ LRU_old (L2477)
                               새로 읽은 페이지는 여기 들어간다
  flush_list (L2406)    dirty 블록만. oldest_modification 순    flush_list_mutex

  한 블록은 page_hash 와 LRU 에 동시에 있고, dirty 면 flush_list 에도 있다
  free 에 있는 블록은 page_hash 에도 LRU 에도 없다
```

블록 하나는 `buf_block_t` 이고, 그 첫 필드가 `buf_page_t` 다. 첫 필드라서 `page_hash` 가 `buf_page_t *` 로 들고 있어도 같은 주소로 `buf_block_t` 를 얻는다(주석 L1768-L1769).

`storage` / `innobase` / `include` / `buf0buf.h` L1764-L1774 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.h#L1764-L1774))

```cpp
// include/buf0buf.h L1764-L1774
struct buf_block_t {
  /** @name General fields */
  /** @{ */

  /** page information; this must be the first field, so
  that buf_pool->page_hash can point to buf_page_t or buf_block_t */
  buf_page_t page;

#ifndef UNIV_HOTBACKUP
  /** read-write lock of the buffer frame */
  BPageLock lock;
```

`buf_page_t` 안에서 목록마다 쓰는 노드가 다르다. `list` 노드 하나가 상태에 따라 free 와 flush_list 를 번갈아 맡는 것이 눈여겨볼 자리다.

`storage` / `innobase` / `include` / `buf0buf.h` L1386-L1393 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.h#L1386-L1393))

```cpp
// include/buf0buf.h L1386-L1393
  /** Page id. */
  page_id_t id;

  /** Page size. */
  page_size_t size;

  /** Count of how many fold this block is currently bufferfixed. */
  buf_fix_count_atomic_t buf_fix_count;
```

`storage` / `innobase` / `include` / `buf0buf.h` L1612-L1662 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/buf0buf.h#L1612-L1662))

```cpp
// include/buf0buf.h L1612-L1662
#ifndef UNIV_HOTBACKUP
  /** Node used in chaining to buf_pool->page_hash or buf_pool->zip_hash */
  buf_page_t *hash;
#endif /* !UNIV_HOTBACKUP */

  // ... (L1617-L1620 생략: 섹션 주석)
  /** Based on state, this is a list node, protected by the corresponding list
  mutex, in one of the following lists in buf_pool:

  - BUF_BLOCK_NOT_USED: free, withdraw
  - BUF_BLOCK_FILE_PAGE:        flush_list
  - BUF_BLOCK_ZIP_DIRTY:        flush_list
  - BUF_BLOCK_ZIP_PAGE: zip_clean

  The node pointers are protected by the corresponding list mutex.

  The contents of the list node is undefined if !in_flush_list &&
  state == BUF_BLOCK_FILE_PAGE, or if state is one of
  BUF_BLOCK_MEMORY,
  BUF_BLOCK_REMOVE_HASH or
  BUF_BLOCK_READY_IN_USE. */

  UT_LIST_NODE_T(buf_page_t) list;

 // ... (L1639-L1659 생략: LSN 두 필드와 섹션 주석)

  /** node of the LRU list */
  UT_LIST_NODE_T(buf_page_t) LRU;
```

생략한 L1639-L1659 의 두 LSN 필드는 **소스 주석이 필드와 뒤바뀌어 보인다**. `oldest_modification`(L1646) 바로 위 주석(L1644-L1645)은 "youngest modification" 이라 적었고, oldest 의 실제 뜻("the START of the log entry ... of the oldest modification ... not yet been flushed", L1649-L1653)은 `public:` 아래 필드 없이 떠 있다. 실제 사용처로 확정하면 `newest_modification` 은 고칠 때마다 mtr 의 `end_lsn` 으로 올라가고(`buf_flush_note_modification`, buf0flu.ic L76), `oldest_modification` 은 clean 페이지가 처음 dirty 가 될 때 `start_lsn` 으로 한 번 정해져 그 순간 flush_list 머리에 붙는다(buf0flu.ic L96 -> buf0flu.cc L432, L434). 접근자 주석(buf0buf.h L1358-L1363)도 이 뜻과 같다.

```text
 buf_block_t 한 개의 모양

 buf_block_t
 +-- page : buf_page_t        <- page_hash 가 가리키는 주소
 |     id            (space, page_no)                 L1387
 |     buf_fix_count 지금 이 블록을 쓰고 있는 수        L1393
 |     state         NOT_USED / FILE_PAGE / ...       L1599
 |     buf_pool_index 어느 인스턴스 소속인가           L1606
 |     hash          page_hash 체인                    L1614
 |     list          free 또는 flush_list 노드          L1637
 |     newest_modification / oldest_modification       L1642, L1646
 |       newest = 마지막으로 고친 mtr 의 end_lsn. 고칠 때마다 올라간다
 |       oldest = clean 에서 dirty 가 된 첫 mtr 의 start_lsn. flush_list 에 넣을 때 한 번 정한다
 |       flush_list 는 oldest 순, 0 이면 clean (is_dirty, L1366)
 |     LRU           LRU 노드                           L1662
 |     old           LRU 의 old 구간에 있는가             L1697
 +-- lock : BPageLock (rw_lock)  페이지 내용의 S/X 래치  L1774
 +-- frame -> 16KB 페이지 본문                            L1786
 +-- mutex : BPageMutex                                   L1924
```

## 잠금 시스템

`lock_sys` 는 해시 셋과 래치 묶음이다. 레코드 잠금은 **페이지 단위**로 해시에 들어간다. 같은 페이지의 잠금은 같은 셀에 모이고, 셀 안에서는 `lock_t.hash` 로 이어진다.

`storage` / `innobase` / `include` / `lock0lock.h` L1069-L1081 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/lock0lock.h#L1069-L1081))

```cpp
// lock0lock.h L1069-L1081
struct lock_sys_t {
  /** The latches protecting queues of record and table locks */
  locksys::Latches latches;

  /** The hash table of the record (LOCK_REC) locks, except for predicate
  (LOCK_PREDICATE) and predicate page (LOCK_PRDT_PAGE) locks */
  Locks_hashtable rec_hash;

  /** The hash table of predicate (LOCK_PREDICATE) locks */
  Locks_hashtable prdt_hash;

  /** The hash table of the predicate page (LOCK_PRD_PAGE) locks */
  Locks_hashtable prdt_page_hash;
```

`storage` / `innobase` / `include` / `lock0lock.ic` L48-L50 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/lock0lock.ic#L48-L50))

```cpp
// lock0lock.ic L48-L50
static inline uint64_t lock_rec_hash_value(const page_id_t &page_id) {
  return page_id.hash();
}
```

래치는 두 층이다. 보통은 전역 래치를 S 로 잡고 셀이 속한 샤드의 뮤텍스를 잡는다. 셀 번호를 512 로 나눈 나머지가 샤드라서, 같은 셀에 모인 페이지는 반드시 같은 샤드 뮤텍스로 보호된다.

`storage` / `innobase` / `lock` / `lock0latches.cc` L36-L51 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0latches.cc#L36-L51))

```cpp
// lock0latches.cc L36-L51
size_t Latches::Page_shards::get_shard(const page_id_t &page_id) {
  /* We always use lock_sys->rec_hash regardless of the exact type of the
  lock. It may happen that the lock is a predicate lock, in which case, it would
  make more sense to use hash_calc_cell_id with proper hash table size. The
  current implementation works, because the size of all three hashmaps is always
  the same. This allows an interface with less arguments. */
  ut_ad(lock_sys->rec_hash.get_n_cells() == lock_sys->prdt_hash.get_n_cells());
  ut_ad(lock_sys->rec_hash.get_n_cells() ==
        lock_sys->prdt_page_hash.get_n_cells());
  /* We need a property that if two pages are mapped to the same bucket of the
  hash table, and thus their lock queues are merged, then these two lock queues
  are protected by the same shard. This is why to compute the shard we use the
  cell_id as the input and not the original lock_rec_hash_value's result. */
  return lock_sys->rec_hash.get_cell_id(lock_rec_hash_value(page_id)) %
         SHARDS_COUNT;
}
```

```text
 rec_hash 와 샤드 (lock0latches.h L76-L82 의 그림을 풀어 쓴 것)

 [                global_latch (sharded rw_lock)                  ]   보통 S, 전체 정지 때 X
                              |
 [table shard 0 .. 511]  [page shard 0 .. 511]                         Padded_mutex
                                |
                                | shard = cell_id % 512
                                v
 rec_hash  cell 0 | cell 1 | ... | cell k | ...
                                    |
                                    v
                    lock_t --hash--> lock_t --hash--> null
                    (page A, trx 1)  (page A, trx 2)
                    같은 페이지의 잠금이 대기 순서대로 이어진 것이 "잠금 큐"다
```

`lock_t` 하나는 **한 트랜잭션이 한 페이지에 건 같은 모드의 잠금 전부**다. 레코드마다 객체를 만들지 않고, 구조체 바로 뒤에 붙은 비트맵의 heap_no 번째 비트로 레코드를 가리킨다.

`storage` / `innobase` / `include` / `lock0priv.h` L83-L91 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/lock0priv.h#L83-L91))

```cpp
// lock0priv.h L83-L91
/** Record lock for a page */
struct lock_rec_t {
  /** The id of the page on which records referenced by this lock's bitmap are
  located. */
  page_id_t page_id;
  /** number of bits in the lock bitmap;
  Must be divisible by 8.
  NOTE: the lock bitmap is placed immediately after the lock struct */
  uint32_t n_bits;
```

`storage` / `innobase` / `include` / `lock0priv.h` L136-L171 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/lock0priv.h#L136-L171))

```cpp
// lock0priv.h L136-L171
/** Lock struct; protected by lock_sys latches */
struct alignas(8 /* For efficient Bitmap::find_set */) lock_t {
  /** transaction owning the lock */
  trx_t *trx;

  /** list of the locks of the transaction */
  UT_LIST_NODE_T(lock_t) trx_locks;

  /** Index for a record lock */
  dict_index_t *index;

  /** Hash chain node for a record lock. The link node in a singly
  linked list, used by the hash table. */
  lock_t *hash;

  union {
    /** Table lock */
    lock_table_t tab_lock;

    /** Record lock */
    lock_rec_t rec_lock;
  };

// ... (L159-L168 생략: Performance Schema 필드)
  /** The lock type and mode bit flags.
  LOCK_GAP or LOCK_REC_NOT_GAP, LOCK_INSERT_INTENTION, wait flag, ORed */
  uint32_t type_mode;
```

```text
 lock_t 한 개의 바이트 배치 (레코드 잠금일 때)

 +---------------------------------------------+
 | trx          -> trx_t (소유자)                |
 | trx_locks    트랜잭션의 잠금 목록 노드         |  trx->lock.trx_locks 에 걸린다
 | index        -> dict_index_t                 |
 | hash         -> 같은 셀의 다음 lock_t          |  rec_hash 체인
 | rec_lock     page_id, n_bits                 |  union (테이블 잠금이면 tab_lock)
 | type_mode    모드 | 타입 | 플래그              |
 +---------------------------------------------+
 | 비트맵 n_bits 비트                            |  구조체 바로 뒤 (L90 주석)
 |  bit[heap_no] = 1 이면 그 레코드에 이 잠금     |  heap_no 0 infimum, 1 supremum (page0types.h L131-L133)
 +---------------------------------------------+

 type_mode 비트 (lock0lock.h L949-L987, lock0types.h L54-L58)

   0-3   모드     LOCK_IS 0, LOCK_IX 1, LOCK_S 2, LOCK_X 3, LOCK_AUTO_INC 4
   4-7   타입     LOCK_TABLE 16, LOCK_REC 32
   8     LOCK_WAIT 256            아직 허가되지 않은 대기 요청
   9     LOCK_GAP 512             레코드 앞 gap 만
   10    LOCK_REC_NOT_GAP 1024    레코드만
   11    LOCK_INSERT_INTENTION 2048
         GAP 도 NOT_GAP 도 아니면 next-key (LOCK_ORDINARY 0)
```

## 트랜잭션 시스템과 trx_t

`trx_sys` 는 활성 트랜잭션을 세 가지 방식으로 들고 있다. 목록(`rw_trx_list`), 정렬된 id 배열(`rw_trx_ids`), id 로 찾는 샤드 맵(`shards`)이다. 쓰는 이가 다르다. 스냅샷은 배열을 복사하고, 레코드의 `DB_TRX_ID` 로 트랜잭션을 찾는 쪽은 샤드를 본다. 후자의 입구가 `trx_rw_is_active`(trx0sys.ic L143, 샤드 조회 L186)이고, 암묵 잠금을 명시 잠금으로 바꾸는 `lock_rec_convert_impl_to_expl`(lock0lock.cc L5228)이 이것을 부른다.

`storage` / `innobase` / `include` / `trx0sys.h` L679-L777 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0sys.h#L679-L777))

```cpp
// trx0sys.h L679-L777
struct trx_sys_t {
  // ... (L680-L686 생략: 패딩과 그룹 주석)
  MVCC *mvcc;
  // ... (L688-L696 생략: 임시 테이블스페이스의 rseg 목록 tmp_rsegs)
  std::atomic<uint64_t> rseg_history_len;
  // ... (L698-L714 생략: 그룹 구분과 next_trx_id_or_no 주석)
  std::atomic<trx_id_t> next_trx_id_or_no;
  // ... (L716-L750 생략: serialisation 목록과 패딩)
  TrxSysMutex mutex;
  // ... (L752-L756 생략: 패딩과 rw_trx_list 주석)
  UT_LIST_BASE_NODE_T(trx_t, trx_list) rw_trx_list;
  // ... (L758-L765 생략: 패딩과 mysql_trx_list 주석)
  UT_LIST_BASE_NODE_T(trx_t, mysql_trx_list) mysql_trx_list;
  // ... (L767-L771 생략: rw_trx_ids 주석)
  trx_ids_t rw_trx_ids;
  // ... (L773-L776 생략: 패딩과 shards 주석)
  Trx_shard shards[TRX_SHARDS_N];
```

`storage` / `innobase` / `include` / `trx0sys.h` L337-L345 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0sys.h#L337-L345))

```cpp
// trx0sys.h L337-L345
constexpr size_t TRX_SHARDS_N = 256;

/** Computes shard number for a given trx_id.
@param[in]  trx_id  trx_id for which shard_no should be computed
@return the computed shard number (number in range 0..TRX_SHARDS_N-1) */
inline size_t trx_get_shard_no(trx_id_t trx_id) {
  ut_ad(trx_id != 0);
  return trx_id % TRX_SHARDS_N;
}
```

```text
 trx_sys 안의 세 가지 색인

 rw_trx_list   trx_t <-> trx_t <-> trx_t      trx_t.trx_list 노드      id 큰 순
 rw_trx_ids    [ 41, 57, 98, 105 ]           trx_ids_t (정렬)          ReadView 가 복사
 shards[256]   shards[id % 256].active_rw_trxs : id -> trx_t           DB_TRX_ID 로 조회
               각 샤드가 자기 뮤텍스를 갖는다 (Trx_shard, trx0sys.h L670)

 serialisation_list   trx->no 를 받았지만 커밋 mtr 이 아직 안 끝난 trx_t
                      ReadView 의 m_low_limit_no 가 이 목록의 최솟값이다
```

`trx_t` 는 위 객체들을 잇는 매듭이다. 자기 잠금, 자기 스냅샷, 자기 undo 를 모두 여기서 붙잡는다.

`storage` / `innobase` / `include` / `trx0trx.h` L727-L822 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0trx.h#L727-L822))

```cpp
// trx0trx.h L727-L822
  trx_id_t id; /*!< transaction id */

  trx_id_t no; /*!< transaction serialization number:
               max trx id shortly before the
               transaction is moved to
               COMMITTED_IN_MEMORY state.
               Protected by trx_sys_t::mutex
               when trx->in_rw_trx_list. Initially
               set to TRX_ID_MAX. */
  // ... (L736-L799 생략: state 의 전이 규칙 주석)
  std::atomic<trx_state_t> state;
  // ... (L801-L808 생략: skip_lock_inheritance)
  ReadView *read_view; /*!< consistent read view used in the
                       transaction, or NULL if not yet set */

  UT_LIST_NODE_T(trx_t)
  trx_list; /*!< list of transactions;
            protected by trx_sys->mutex. */
  UT_LIST_NODE_T(trx_t)
  no_list; /*!< Required during view creation
           to check for the view limit for
           transactions that are committing */
  // ... (L819-L821 생략: lock 주석)
  trx_lock_t lock;
```

`storage` / `innobase` / `include` / `trx0trx.h` L439-L538 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0trx.h#L439-L538))

```cpp
// trx0trx.h L439-L538
  std::atomic<trx_t *> blocking_trx;
  // ... (L440-L459 생략: wait_lock 의 래치 규칙 주석)
  std::atomic<lock_t *> wait_lock;
  // ... (L461-L537 생략: 대기 관련 통계, 잠금 풀, 힙)
  trx_lock_list_t trx_locks;
```

```text
 trx_t 한 개가 붙잡는 것

 trx_t
   id          rw 가 되는 순간 받는다. 읽기 전용이면 0
   no          커밋 직전에 받는 직렬화 번호 (history list 순서)
   state       NOT_STARTED / ACTIVE / PREPARED / COMMITTED_IN_MEMORY
   read_view ------------------------------> ReadView (trx_sys->mvcc 의 m_views 에도 걸림)
   trx_list    rw_trx_list 노드
   no_list     serialisation_list 노드
   lock
     trx_locks ---> lock_t --> lock_t --> ...   내가 가진/기다리는 모든 잠금
     wait_lock ---> lock_t (LOCK_WAIT)          지금 기다리는 하나
     blocking_trx -> trx_t                      나를 막고 있는 트랜잭션 (교착 검사용)
   rsegs.m_redo / m_noredo ---> trx_rseg_t, trx_undo_t   ([undo 테이블스페이스와 롤백 세그먼트])
   mysql_thd -----> THD                         서버 쪽 연결 (trx0trx.h L932)
```

## ReadView

ReadView 는 **포인터가 하나도 없는 숫자 묶음**이다. 다른 트랜잭션을 가리키지 않고, 만들 때 `trx_sys` 에서 숫자를 복사해 온다. 그래서 만든 뒤에는 `trx_sys` 를 잡지 않고 가시성을 판정한다.

`storage` / `innobase` / `include` / `read0types.h` L266-L296 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/read0types.h#L266-L296))

```cpp
// read0types.h L266-L296
 private:
  /** The read should not see any transaction with trx id >= this
  value. In other words, this is the "high water mark". */
  trx_id_t m_low_limit_id;

  /** The read should see all trx ids which are strictly
  smaller (<) than this value.  In other words, this is the
  low water mark". */
  trx_id_t m_up_limit_id;

  /** trx id of creating transaction, set to TRX_ID_MAX for free
  views. */
  trx_id_t m_creator_trx_id;

  /** Set of RW transactions that was active when this snapshot
  was taken */
  ids_t m_ids;

  /** The view does not need to see the undo logs for transactions
  whose transaction number is strictly smaller (<) than this value:
  they can be removed in purge if not needed by other views */
  trx_id_t m_low_limit_no;

  /** AC-NL-RO transaction view that has been "closed". */
  std::atomic_bool m_closed;

  typedef UT_LIST_NODE_T(ReadView) node_t;

  /** List of read views in trx_sys */
  byte pad1[64 - sizeof(node_t)];
  node_t m_view_list;
```

다섯 숫자를 채우는 곳이다. 셋은 `trx_sys` 의 현재 값이고, 하나는 배열 복사, 하나는 그 배열의 첫 값이다.

`storage` / `innobase` / `read` / `read0read.cc` L446-L468 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L446-L468))

```cpp
// read0read.cc L446-L468
void ReadView::prepare(trx_id_t id) {
  ut_ad(trx_sys_mutex_own());

  m_creator_trx_id = id;

  m_low_limit_no = trx_get_serialisation_min_trx_no();

  m_low_limit_id = trx_sys_get_next_trx_id_or_no();

  ut_a(m_low_limit_no <= m_low_limit_id);

  if (!trx_sys->rw_trx_ids.empty()) {
    copy_trx_ids(trx_sys->rw_trx_ids);
  } else {
    m_ids.clear();
  }

  /* The first active transaction has the smallest id. */
  m_up_limit_id = !m_ids.empty() ? m_ids.front() : m_low_limit_id;

  ut_a(m_up_limit_id <= m_low_limit_id);

  m_closed.store(false);
```

```text
 ReadView 의 숫자와 출처 (ReadView::prepare, read0read.cc L446)

 m_creator_trx_id  = 만든 트랜잭션의 id                          L449
 m_low_limit_no    = serialisation_list 의 최소 trx->no          L451   purge 경계
 m_low_limit_id    = trx_sys->next_trx_id_or_no                  L453   이 이상은 안 보인다
 m_ids             = trx_sys->rw_trx_ids 복사                    L458   만들 때 활성이던 id
 m_up_limit_id     = m_ids 의 첫 값 (없으면 m_low_limit_id)       L464   이 미만은 보인다

 판정 changes_visible(id)  (read0types.h L163-L183)

   id < m_up_limit_id 또는 id == m_creator_trx_id  -> 보인다
   id >= m_low_limit_id                            -> 안 보인다
   그 사이                                          -> m_ids 에 있으면 안 보인다 (이진 탐색)

         보인다            m_ids 에 따라             안 보인다
   ---------------| m_up_limit_id ........ m_low_limit_id |---------------> trx id
```

ReadView 들은 `trx_sys->mvcc` 가 목록으로 들고 있다. purge 는 이 목록에서 가장 오래된 뷰를 `clone_oldest_view`(read0read.cc L685)로 복제해 "어디까지 지워도 되는가"를 정한다(trx0purge.cc L254).

`storage` / `innobase` / `include` / `read0read.h` L124-L133 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/read0read.h#L124-L133))

```cpp
// read0read.h L124-L133
 private:
  typedef UT_LIST_BASE_NODE_T(ReadView, m_view_list) view_list_t;

  /** Free views ready for reuse. */
  view_list_t m_free;

  /** Active and closed views, the closed views will have the
  creator trx id set to TRX_ID_MAX */
  view_list_t m_views;
};
```

## db-engine 에서는

db-engine 은 버퍼 풀과 잠금 관리자를 **각각 맵 하나**로 만들었다. MySQL 은 같은 두 자리를 여러 인스턴스, 여러 리스트, 샤드 래치로 쪼갰다.

```text
 같은 두 문제, 두 구현 (위 MySQL / 아래 db-engine)

 페이지 찾기
   MySQL      buf_pool_ptr[hash(space, page_no>>6) % N] 의 page_hash
   db-engine  BufferPool.pages: LinkedHashMap<PageId, Page> 하나

 교체 순서
   MySQL      LRU 리스트 + LRU_old 경계 (young / old 두 구간), free 리스트 따로
   db-engine  LinkedHashMap(capacity, 0.75f, true) 의 access-order 가 곧 LRU
              evictOne 이 pinCount == 0 인 첫 항목을 고른다

 사용 중 표시와 dirty
   MySQL      buf_fix_count, 블록 rw_lock, dirty 면 flush_list 에 올라간다
   db-engine  Page.pinCount, Page.isDirty. dirty 목록은 따로 없다

 잠금의 자리
   MySQL      rec_hash: 페이지 -> lock_t 체인. lock_t 하나 = 한 trx 의 한 페이지 한 모드
              레코드는 비트맵의 heap_no 비트
   db-engine  LockManager.holders: MutableMap<String, MutableList<Holder>>
              자원 문자열 하나마다 (txId, mode) 목록

 충돌하면
   MySQL      LOCK_WAIT 플래그를 단 lock_t 를 큐에 넣고 기다린다 (trx->lock.wait_lock)
   db-engine  LockConflict 를 던진다. 대기 큐가 없다

 동시성 보호
   MySQL      리스트별 뮤텍스, 해시 셀별 rw_lock, 잠금은 global + 512 샤드
   db-engine  LockManager 는 @Synchronized 하나
```

db-engine 09-01 은 행 단위 잠금이 "행 하나당 엔트리"를 만들어 락 개수가 폭발한다고 적었다. MySQL 이 레코드마다 객체를 만들지 않고 **페이지당 객체 하나 + 비트맵**으로 가는 것이 그 비용을 줄이는 방식이다. 챕터: [02-02-buffer-pool](../../../../../project/db-engine/02-02-buffer-pool/), [09-01-lock-manager](../../../../../project/db-engine/09-01-lock-manager/).

## 어디에서 쓰이는가

```text
 [버퍼 풀 페이지 획득]  page_hash 조회, free 에서 블록 얻기, LRU 에 붙이기, young 으로 옮기기
 [mini-transaction과 redo 기록]  mtr commit 이 dirty 블록을 flush_list 에 붙인다
 [페이지 플러시, doublewrite, 체크포인트]  flush_list 와 LRU 꼬리에서 내려쓴다
 [레코드 잠금과 교착]   rec_hash 에 lock_t 를 넣고, 충돌하면 wait_lock 을 걸고 잔다
 [일관 읽기(MVCC)]      trx_sys 의 숫자로 ReadView 를 만들고 changes_visible 로 판정한다
 [커밋과 binlog 2PC]    trx->no 를 받고, rw_trx_ids 에서 빠지고, 잠금을 푼다
 [purge]                mvcc 의 가장 오래된 뷰를 복제해 지울 범위를 정한다
```

페이지를 찾는 길은 [버퍼 풀 페이지 획득](../../flows/buffer-pool-fetch/README.md), dirty 블록이 flush_list 에 붙는 순간은 [mini-transaction과 redo 기록](../../flows/mtr-redo/README.md), 잠금 큐에 들어가는 길은 [레코드 잠금과 교착](../../flows/record-lock/README.md)에 있다. 커밋이 이 객체들을 정리하는 순서는 [trx_commit_low](../../flows/commit-2pc/10_trx_commit_low/README.md), undo 쪽 객체는 [undo 테이블스페이스와 롤백 세그먼트](../undo-segments/README.md), 이 객체들을 만지는 백그라운드 스레드는 [스레드 구성](../threads/README.md)에 있다.

## 다루지 않는 것

버퍼 풀 크기 조정(chunk, withdraw 목록, `buf_resize_thread`), 압축 페이지(`zip_hash`, buddy 할당자, `unzip_LRU`), 적응형 해시 인덱스(`buf_block_t::ahi`), hazard pointer(`flush_hp`, `lru_hp`)와 LRU 반복자, 테이블 잠금(`lock_table_t`)과 AUTO_INC 잠금, 술어 잠금(`prdt_hash`, `prdt_page_hash`), `lock_sys` 크기 조정, `trx_t` 의 상태 전이 규칙 전문(trx0trx.h L737-L798 주석), 읽기 전용 트랜잭션의 `mysql_trx_list` 와 trx 풀, `MVCC` 의 뷰 재사용(`m_free`)과 AC-NL-RO 뷰의 닫힘(`m_closed`)은 같은 뼈대의 곁가지라 요약만 했다.
