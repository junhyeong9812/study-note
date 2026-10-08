# trx_purge_attach_undo_recs

상위: [purge](../README.md)

**history list 에서 이번 배치가 처리할 undo 레코드를 꺼내, 테이블별로 묶어 스레드 수만큼의 그룹에 나눠 주는 자리다.** 꺼내는 순서는 커밋 번호(`trx->no`) 순이다. 롤백 세그먼트가 여럿이라 각 세그먼트의 가장 오래된 로그를 우선순위 큐(`purge_queue`)에 넣어 두고 가장 작은 번호부터 고른다. 꺼내기는 두 조건 중 먼저 오는 쪽에서 멈춘다. 다룬 undo 페이지 수가 `innodb_purge_batch_size` 에 닿거나, 다음 로그의 커밋 번호가 [04] 가 정한 `m_lowest_needed_trx_no` 에 닿는다. 모든 undo 레코드를 꺼내지는 않는다. 로그 헤더에 "delete-mark 나 인덱스 키 변경이 없다"고 적힌 로그는 통째로 건너뛰고, 로그 안에서도 purge 할 것이 없는 갱신 레코드는 건너뛴다.

## 위치

`storage` / `innobase` / `trx` / `trx0purge.cc` L2243-L2317 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2243-L2317))

## 실제 코드

함수 전체다. 스레드마다 하나씩 있는 `purge_node_t` 를 준비하고, 레코드를 꺼내 `Purge_groups_t` 에 넣고, 그룹을 노드에 붙인다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L2243-L2317 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2243-L2317))

```cpp
// trx0purge.cc L2243-L2317
static ulint trx_purge_attach_undo_recs(const ulint n_purge_threads,
                                        ulint batch_size) {
  ulint n_pages_handled = 0;

  ut_a(n_purge_threads > 0);
  ut_a(n_purge_threads <= MAX_PURGE_THREADS);

  purge_sys->limit = purge_sys->iter;

  que_thr_t *run_thrs[MAX_PURGE_THREADS];

  /* Validate some pre-requisites and reset done flag. */
  ulint i = 0;

  for (auto thr : purge_sys->query->thrs) {
    if (n_purge_threads <= i) break;
    purge_node_t *node;

    /* Get the purge node. */
    node = static_cast<purge_node_t *>(thr->child);

    ut_a(que_node_get_type(node) == QUE_NODE_PURGE);
    ut_a(node->recs == nullptr);
    ut_a(node->done);

    node->done = false;

    ut_a(!thr->is_active);

    run_thrs[i++] = thr;
  }

  /* There should never be fewer nodes than threads, the inverse
  however is allowed because we only use purge threads as needed. */
  ut_a(i == n_purge_threads);
  ut_ad(trx_purge_check_limit());

  mem_heap_t *heap = purge_sys->heap;

  mem_heap_empty(heap);

  Purge_groups_t purge_groups(n_purge_threads, heap);
  purge_groups.init();

  while (n_pages_handled < batch_size) {
    /* Track the max {trx_id, undo_no} for truncating the
    UNDO logs once we have purged the records. */

    if (trx_purge_check_limit()) {
      purge_sys->limit = purge_sys->iter;
    }

    purge_node_t::rec_t rec;

    /* Fetch the next record, and advance the purge_sys->iter. */
    rec.undo_rec = trx_purge_fetch_next_rec(&rec.modifier_trx_id, &rec.roll_ptr,
                                            &n_pages_handled, heap);

    if (rec.undo_rec == &trx_purge_ignore_rec) {
      continue;

    } else if (rec.undo_rec == nullptr) {
      break;
    }

    purge_groups.add(rec);
  }

  purge_groups.distribute_if_needed();
  purge_groups.assign(run_thrs);

  ut_ad(trx_purge_check_limit());

  return (n_pages_handled);
}
```

레코드 하나를 꺼내는 쪽이다. 다음 로그가 아직 정해지지 않았으면 고르고, 경계에 닿았으면 nullptr 을 돌려준다. 돌려줄 레코드의 위치로 roll_ptr 을 만든다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L2199-L2241 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2199-L2241))

```cpp
// trx0purge.cc L2199-L2241
/** Fetches the next undo log record from the history list to purge. It must
 be released with the corresponding release function.
 @return copy of an undo log record or pointer to trx_purge_ignore_rec,
 if the whole undo log can skipped in purge; NULL if none left */
[[nodiscard]] static trx_undo_rec_t *trx_purge_fetch_next_rec(
    trx_id_t *modifier_trx_id,
    /*!< out: modifier trx id. this is the
    trx that created the undo record. */
    roll_ptr_t *roll_ptr,   /*!< out: roll pointer to undo record */
    ulint *n_pages_handled, /*!< in/out: number of UNDO log pages
                            handled */
    mem_heap_t *heap)       /*!< in: memory heap where copied */
{
  if (!purge_sys->next_stored) {
    trx_purge_choose_next_log();

    if (!purge_sys->next_stored) {
      DBUG_PRINT("ib_purge", ("no logs left in the history list"));
      return nullptr;
    }
  }

  if (purge_sys->iter.trx_no >= purge_sys->m_lowest_needed_trx_no) {
    return nullptr;
  }

  /* fprintf(stderr, "Thread %s purging trx %llu undo record %llu\n",
  to_string(std::this_thread::get_id()), iter->trx_no, iter->undo_no); */

  *roll_ptr = trx_undo_build_roll_ptr(false, purge_sys->rseg->space_id,
                                      purge_sys->page_no, purge_sys->offset);

  *modifier_trx_id = purge_sys->iter.modifier_trx_id;

  /* The following call will advance the stored values of the
  purge iterator. */

  return (trx_purge_get_next_rec(n_pages_handled, heap));
}

/** This function runs a purge batch.
@param[in]      n_purge_threads  number of purge threads
@param[in]      batch_size       number of pages to purge
```

다음 로그를 고르는 쪽이다. 우선순위 큐의 top 이 가장 작은 커밋 번호다. 같은 번호의 원소는 하나로 합친다(한 트랜잭션이 redo 와 no-redo 두 세그먼트를 쓴 경우).

`storage` / `innobase` / `trx` / `trx0purge.cc` L109-L189 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L109-L189))

```cpp
// trx0purge.cc L109-L189
const page_size_t TrxUndoRsegsIterator::set_next() {
  mutex_enter(&m_purge_sys->pq_mutex);

  /* Only purge consumes events from the priority queue, user
  threads only produce the events. */

  /* Check if there are more rsegs to process in the
  current element. */
  if (m_iter != m_trx_undo_rsegs.end()) {
    /* We are still processing rollback segment from
    the same transaction and so expected transaction
    number shouldn't increase. Undo increment of
    expected trx_no done by caller assuming rollback
    segments from given transaction are done. */
    m_purge_sys->iter.trx_no = (*m_iter)->last_trx_no;

  } else if (!m_purge_sys->purge_queue->empty()) {
    /* Read the next element from the queue.
    Combine elements if they have same transaction number.
    This can happen if a transaction shares redo rollback segment
    with another transaction that has already added it to purge
    queue and former transaction also needs to schedule non-redo
    rollback segment for purge. */
    m_trx_undo_rsegs = NullElement;

    while (!m_purge_sys->purge_queue->empty()) {
      if (m_trx_undo_rsegs.get_trx_no() == UINT64_UNDEFINED) {
        m_trx_undo_rsegs = purge_sys->purge_queue->top();
      } else if (purge_sys->purge_queue->top().get_trx_no() ==
                 m_trx_undo_rsegs.get_trx_no()) {
        m_trx_undo_rsegs.insert(purge_sys->purge_queue->top());
      } else {
        break;
      }

      m_purge_sys->purge_queue->pop();
    }

    m_iter = m_trx_undo_rsegs.begin();

  } else {
    /* Queue is empty, reset iterator. */
    m_trx_undo_rsegs = NullElement;
    m_iter = m_trx_undo_rsegs.end();

    mutex_exit(&m_purge_sys->pq_mutex);

    m_purge_sys->rseg = nullptr;

    /* return a dummy object, not going to be used by the caller */
    return (univ_page_size);
  }

  m_purge_sys->rseg = *m_iter++;

  mutex_exit(&m_purge_sys->pq_mutex);

  ut_a(m_purge_sys->rseg != nullptr);

  m_purge_sys->rseg->latch();

  ut_a(m_purge_sys->rseg->last_page_no != FIL_NULL);
  ut_ad(m_purge_sys->rseg->last_trx_no == m_trx_undo_rsegs.get_trx_no());

  /* The space_id must be a tablespace that contains rollback segments.
  That includes the system, temporary and all undo tablespaces. */
  ut_a(fsp_is_system_or_temp_tablespace(m_purge_sys->rseg->space_id) ||
       fsp_is_undo_tablespace(m_purge_sys->rseg->space_id));

  const page_size_t page_size(m_purge_sys->rseg->page_size);

  ut_a(purge_sys->iter.trx_no <= purge_sys->rseg->last_trx_no);

  m_purge_sys->iter.trx_no = m_purge_sys->rseg->last_trx_no;
  m_purge_sys->hdr_offset = m_purge_sys->rseg->last_offset;
  m_purge_sys->hdr_page_no = m_purge_sys->rseg->last_page_no;

  m_purge_sys->rseg->unlatch();

  return (page_size);
}
```

로그 안에서 다음으로 purge 할 레코드를 찾는 쪽이다. delete-mark, 외부 저장 열, 인덱스 키를 바꾼 갱신만 멈추는 자리다. 지금 위치의 레코드를 복사해 돌려주고, 찾은 다음 자리를 기억해 둔다. 오프셋 0 은 "이 로그는 purge 할 것이 없다"는 표시다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L1884-L2000 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L1884-L2000))

```cpp
// trx0purge.cc L1884-L2000
static trx_undo_rec_t *trx_purge_get_next_rec(
    ulint *n_pages_handled, /*!< in/out: number of UNDO pages
                            handled */
    mem_heap_t *heap)       /*!< in: memory heap where copied */
{
  // ... (L1889-L1897 생략: 지역 변수 선언)

  ut_ad(purge_sys->next_stored);
  ut_ad(purge_sys->iter.trx_no < purge_sys->m_lowest_needed_trx_no);

  space = purge_sys->rseg->space_id;
  page_no = purge_sys->page_no;
  offset = purge_sys->offset;

  const page_size_t page_size(purge_sys->rseg->page_size);

  if (offset == 0) {
    /* It is the dummy undo log record, which means that there is no need to
    purge this undo log */

    trx_purge_rseg_get_next_history_log(purge_sys->rseg, n_pages_handled);

    /* Look for the next undo log and record to purge */

    trx_purge_choose_next_log();

    return (&trx_purge_ignore_rec);
  }

  mtr_start(&mtr);

  undo_page =
      trx_undo_page_get_s_latched(page_id_t(space, page_no), page_size, &mtr);

  rec = undo_page + offset;

  rec2 = rec;

  for (;;) {
    ulint type;
    trx_undo_rec_t *next_rec;
    ulint cmpl_info;

    /* Try first to find the next record which requires a purge operation from
    the same page of the same undo log */

    next_rec = trx_undo_page_get_next_rec(rec2, purge_sys->hdr_page_no,
                                          purge_sys->hdr_offset);

    if (next_rec == nullptr) {
      rec2 = trx_undo_get_next_rec(rec2, purge_sys->hdr_page_no,
                                   purge_sys->hdr_offset, &mtr);
      break;
    }

    rec2 = next_rec;

    type = trx_undo_rec_get_type(rec2);

    if (type == TRX_UNDO_DEL_MARK_REC) {
      break;
    }

    cmpl_info = trx_undo_rec_get_cmpl_info(rec2);

    if (trx_undo_rec_get_extern_storage(rec2)) {
      break;
    }

    if ((type == TRX_UNDO_UPD_EXIST_REC) &&
        !(cmpl_info & UPD_NODE_NO_ORD_CHANGE)) {
      break;
    }
  }

  if (rec2 == nullptr) {
    mtr_commit(&mtr);

    trx_purge_rseg_get_next_history_log(purge_sys->rseg, n_pages_handled);

    /* Look for the next undo log and record to purge */

    trx_purge_choose_next_log();

    mtr_start(&mtr);

    undo_page =
        trx_undo_page_get_s_latched(page_id_t(space, page_no), page_size, &mtr);

  } else {
    page = page_align(rec2);

    purge_sys->offset = rec2 - page;
    purge_sys->page_no = page_get_page_no(page);
    purge_sys->iter.undo_no = trx_undo_rec_get_undo_no(rec2);
    purge_sys->iter.undo_rseg_space = space;

    if (undo_page != page) {
      /* We advance to a new page of the undo log: */
      (*n_pages_handled)++;
    }
  }

  rec_copy = trx_undo_rec_copy(undo_page, static_cast<uint32_t>(offset), heap);

  mtr_commit(&mtr);

  return (rec_copy);
}
```

로그 하나를 다 읽었을 때다. 같은 롤백 세그먼트의 history 에서 한 칸 앞(더 최근 커밋)의 로그 헤더를 읽어 그 세그먼트의 다음 후보로 큐에 다시 넣는다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L1775-L1811 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L1775-L1811))

```cpp
// trx0purge.cc L1775-L1811
  /* Read the trx number and del marks from the previous log header */
  mtr_start(&mtr);

  log_hdr =
      trx_undo_page_get_s_latched(page_id_t(rseg->space_id, prev_log_addr.page),
                                  rseg->page_size, &mtr) +
      prev_log_addr.boffset;

  trx_id_t trx_no = mach_read_from_8(log_hdr + TRX_UNDO_TRX_NO);

  auto del_marks = mach_read_from_2(log_hdr + TRX_UNDO_DEL_MARKS);

  mtr_commit(&mtr);

  rseg->latch();

  rseg->last_page_no = prev_log_addr.page;
  rseg->last_offset = prev_log_addr.boffset;
  rseg->last_trx_no = trx_no;
  rseg->last_del_marks = del_marks;

  TrxUndoRsegs elem(rseg->last_trx_no);
  elem.insert(rseg);

  /* Purge can also produce events, however these are already ordered in the
  rollback segment and any user generated event will be greater than the events
  that Purge produces. ie. Purge can never produce
  events from an empty rollback segment. */

  mutex_enter(&purge_sys->pq_mutex);

  purge_sys->purge_queue->push(std::move(elem));

  mutex_exit(&purge_sys->pq_mutex);

  rseg->unlatch();
}
```

그룹에 넣는 쪽이다. 같은 `table_id` 는 같은 그룹으로, 처음 보는 테이블은 가장 작은 그룹으로 간다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L2052-L2067 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L2052-L2067))

```cpp
// trx0purge.cc L2052-L2067
  void add(purge_node_t::rec_t &rec) {
    /* Identify the table id */
    const table_id_t id = trx_undo_rec_get_table_id(rec.undo_rec);
    std::size_t grpid;

    GroupBy::iterator lb = m_grpid_umap.find(id);
    if (lb != m_grpid_umap.end()) {
      grpid = lb->second;
    } else {
      grpid = find_smallest_group();
      m_grpid_umap.insert(std::make_pair(id, grpid));
    }

    m_groups[grpid]->push_back(rec);
    m_total_rec++;
  }
```

## 동작 흐름

```text
 trx_purge_attach_undo_recs(n_purge_threads, batch_size)

 L2250  purge_sys->limit = purge_sys->iter
 L2257  query thread 를 n 개 고르고 노드마다 done = false
 L2284  Purge_groups_t(n) 초기화 (그룹 n 개, 힙은 purge_sys->heap)
 L2287  while (n_pages_handled < batch_size)
 L2291    limit = iter (trx_purge_check_limit 가 맞으면)
 L2298    rec.undo_rec = trx_purge_fetch_next_rec(&modifier_trx_id, &roll_ptr, &n_pages, heap)
            L2212  다음 로그가 안 정해졌으면 trx_purge_choose_next_log
                     TrxUndoRsegsIterator::set_next -> purge_queue.top() (가장 작은 trx->no)
                     trx_purge_read_undo_rec: 로그 헤더의 del_marks 가 false 면 offset = 0
            L2221  iter.trx_no >= m_lowest_needed_trx_no  -> nullptr (여기서 멈춘다)
            L2228  roll_ptr = (rseg space, page_no, offset) 로 만든다
            L2236  trx_purge_get_next_rec
                     offset == 0       -> 로그를 통째로 건너뛰고 trx_purge_ignore_rec
                     아니면 현재 레코드를 복사하고, 같은 로그에서 다음 purge 대상을 찾아 기억
                     로그 끝이면 trx_purge_rseg_get_next_history_log -> 다음 로그
 L2301    ignore_rec 면 continue,  nullptr 이면 break
 L2308    purge_groups.add(rec)              table_id 로 그룹 고르기
 L2311  distribute_if_needed                history 가 max_purge_lag 를 넘으면 그룹 크기를 고르게
 L2312  assign(run_thrs)                    그룹 i -> 노드 i 의 recs
 L2316  return n_pages_handled
```

여러 롤백 세그먼트의 history 가 하나의 커밋 번호 순서로 합쳐지는 모습이다.

```text
 rseg 1 history (last 부터)   no=500 -> 530 -> 610 -> ...
 rseg 2 history               no=510 -> 520 -> 700 -> ...
 rseg 3 history               no=540 -> ...

 purge_queue (작은 trx->no 가 top)   처음: {500:rseg1, 510:rseg2, 540:rseg3}

 꺼내는 순서     queue top   읽는 로그        다 읽은 뒤 queue 에 넣는 것
 1               500         rseg1 의 500     530:rseg1  (trx_purge_rseg_get_next_history_log)
 2               510         rseg2 의 510     520:rseg2
 3               520         rseg2 의 520     700:rseg2
 4               530         rseg1 의 530     610:rseg1
 5               540         rseg3 의 540     ...
 m_lowest_needed_trx_no = 600 이면 6 번째(610)에서 멈춘다

 rseg 가 큐에 처음 들어가는 것은 커밋 때다 (trx_serialisation_number_get, [커밋과 binlog 2PC] 10)
```

로그 안에서 무엇을 건너뛰는지는 undo 레코드 종류와 로그 헤더의 플래그로 정해진다.

```text
 로그 단위: TRX_UNDO_DEL_MARKS (undo 로그 헤더)
   쓰는 쪽에서 true 가 되는 경우 (trx0rec.cc)
     delete-mark 를 했다, 또는 인덱스 키 열을 바꾼 갱신이다   L1504
     외부 저장 열을 바꿨다 (옛 BLOB 을 나중에 풀어야 한다)     L1418
   false 면 그 로그는 offset = 0 -> 통째로 건너뛴다 (trx_purge_read_undo_rec L1827)

 레코드 단위: trx_purge_get_next_rec 가 멈추는 자리 (L1930-L1965)
   TRX_UNDO_DEL_MARK_REC                       멈춘다  -> [09] 가 행을 지운다
   외부 저장 플래그가 있다                      멈춘다  -> 옛 BLOB 해제
   TRX_UNDO_UPD_EXIST_REC 이고 키 열을 바꿨다   멈춘다  -> 세컨더리의 옛 키 엔트리 삭제
   그 밖 (키를 안 바꾼 갱신 등)                건너뛴다 (복사하지도 않는다)
```

## 결과가 쓰이는 곳

```text
 purge_node_t::recs (노드마다 그룹 하나)
      --> [03] 이 n-1 개 노드를 워커 큐에 넣고 하나는 직접 돌린다 --> [07]
 purge_sys->iter, purge_sys->limit
      --> [10] 이 이 위치까지 history 를 잘라낸다
 n_pages_handled
      --> [03] 의 반환값
```

## 다루지 않는 것

`trx_purge_check_limit` 의 조건, `Purge_groups_t::distribute` 가 그룹 사이로 레코드를 옮기는 두 번의 패스, `trx_undo_get_next_rec` 가 undo 로그의 다음 페이지로 넘어가는 방법, temp 롤백 세그먼트와 redo 롤백 세그먼트를 한 트랜잭션 번호로 묶는 `TrxUndoRsegs` 의 구조는 이 흐름의 곁가지라 줄만 적었다.
