# trx_assign_read_view

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**트랜잭션에 활성 read view 가 없을 때만 새로 여는, 열 줄짜리 문지기다.** 이미 활성이면 그대로 돌려준다. 그래서 격리 수준의 차이는 이 함수가 아니라 **view 를 언제 닫느냐**에서 생긴다. READ COMMITTED 는 문장이 시작하고 끝날 때 view 를 닫아 두므로 다음 문장의 첫 읽기에서 이 함수가 새 view 를 연다. REPEATABLE READ 는 커밋할 때까지 닫지 않으므로 첫 읽기에서 연 view 하나를 끝까지 쓴다. 실제로 view 를 만드는 일은 `MVCC::view_open` 이 하고, 그 안에서 [04] `ReadView::prepare` 가 값을 채운다.

## 위치

`storage` / `innobase` / `trx` / `trx0trx.cc` L2291-L2305 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2291-L2305))

## 실제 코드

함수 본체다. 주석이 규칙을 그대로 적었다. 같은 트랜잭션의 일관 읽기는 모두 같은 view 를 받는다.

`storage` / `innobase` / `trx` / `trx0trx.cc` L2287-L2305 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0trx.cc#L2287-L2305))

```cpp
// trx0trx.cc L2287-L2305
/** Assigns a read view for a consistent read query. All the consistent reads
 within the same transaction will get the same read view, which is created
 when this function is first called for a new started transaction.
 @return consistent read view */
ReadView *trx_assign_read_view(trx_t *trx) /*!< in/out: active transaction */
{
  ut_ad(trx_can_be_handled_by_current_thread_or_is_hp_victim(trx));
  ut_ad(trx->state.load(std::memory_order_relaxed) == TRX_STATE_ACTIVE);

  if (srv_read_only_mode) {
    ut_ad(trx->read_view == nullptr);
    return (nullptr);

  } else if (!MVCC::is_view_active(trx->read_view)) {
    trx_sys->mvcc->view_open(trx->read_view, trx);
  }

  return (trx->read_view);
}
```

`MVCC::view_open` 이다. 자동 커밋 읽기 전용 트랜잭션은 닫아 둔 view 를 다시 쓸 수 있으면 다시 쓰고, 아니면 `trx_sys->mutex` 를 잡고 [04] 로 새로 채워 `m_views` 목록 맨 앞에 건다.

`storage` / `innobase` / `read` / `read0read.cc` L499-L637 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L499-L637))

```cpp
// read0read.cc L499-L637
void MVCC::view_open(ReadView *&view, trx_t *trx) {
  ut_ad(!srv_read_only_mode);

  /** If no new RW transaction has been started since the last view
  was created then reuse the the existing view. */
  if (view != nullptr) {
    uintptr_t p = reinterpret_cast<uintptr_t>(view);

    view = reinterpret_cast<ReadView *>(p & ~1);

    ut_ad(view->m_closed.load());

    // ... (L511-L604 생략: 재사용이 안전하다는 증명 주석)

    if (trx_is_autocommit_non_locking(trx) && view->empty()) {
      view->m_closed.store(false);
      DEBUG_SYNC_C("after_setting_m_closed_false");
      if (view->m_low_limit_id == trx_sys_get_next_trx_id_or_no()) {
        return;
      } else {
        view->m_closed.store(true);
      }
    }
  }

  trx_sys_mutex_enter();

  if (view != nullptr) {
    UT_LIST_REMOVE(m_views, view);

  } else {
    view = get_view();
  }

  if (view != nullptr) {
    view->prepare(trx->id);

    UT_LIST_ADD_FIRST(m_views, view);

    ut_ad(!view->is_closed());

    ut_ad(validate());
  }

  trx_sys_mutex_exit();
}
```

닫는 쪽이다. 뮤텍스를 쥔 호출자는 view 를 목록에서 빼서 빈 목록(`m_free`)으로 돌린다. 뮤텍스 없이 닫는 자동 커밋 읽기 전용 경로는 포인터의 가장 낮은 비트를 1로 켜서 "닫힘"만 표시하고 객체는 다음 재사용을 위해 남긴다.

`storage` / `innobase` / `read` / `read0read.cc` L741-L774 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L741-L774))

```cpp
// read0read.cc L741-L774
/**
Close a view created by the above function.
@param view             view allocated by trx_open.
@param own_mutex        true if caller owns trx_sys_t::mutex */

void MVCC::view_close(ReadView *&view, bool own_mutex) {
  uintptr_t p = reinterpret_cast<uintptr_t>(view);

  /* Note: The assumption here is that AC-NL-RO transactions will
  call this function with own_mutex == false. */
  if (!own_mutex) {
    /* Sanitise the pointer first. */
    ReadView *ptr = reinterpret_cast<ReadView *>(p & ~1);

    /* Note this can be called for a read view that was already closed. */
    if (!ptr->m_closed.load()) {
      ptr->m_closed.store(true);
    }

    /* Set the view as closed. */
    view = reinterpret_cast<ReadView *>(p | 0x1);
  } else {
    view = reinterpret_cast<ReadView *>(p & ~1);

    view->close();

    UT_LIST_REMOVE(m_views, view);
    UT_LIST_ADD_LAST(m_free, view);

    ut_ad(validate());

    view = nullptr;
  }
}
```

READ COMMITTED 이하에서 view 를 버리는 두 자리다. 하나는 문장이 테이블을 처음 잡을 때(`store_lock`), 하나는 문장이 마지막 테이블을 놓을 때(`external_lock` 의 `F_UNLCK`)다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L19752-L19766 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L19752-L19766))

```cpp
// ha_innodb.cc L19752-L19766
  if (lock_type != TL_IGNORE && trx->n_mysql_tables_in_use == 0) {
    trx->isolation_level =
        innobase_trx_map_isolation_level(thd_get_trx_isolation(thd));

    if (trx->isolation_level <= TRX_ISO_READ_COMMITTED &&
        MVCC::is_view_active(trx->read_view)) {
      /* At low transaction isolation levels we let
      each consistent read set its own snapshot */

      mutex_enter(&trx_sys->mutex);

      trx_sys->mvcc->view_close(trx->read_view, true);

      mutex_exit(&trx_sys->mutex);
    }
```

`storage` / `innobase` / `handler` / `ha_innodb.cc` L19149-L19170 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L19149-L19170))

```cpp
// ha_innodb.cc L19149-L19170
  if (trx->n_mysql_tables_in_use == 0) {
    trx->mysql_n_tables_locked = 0;
    m_prebuilt->used_in_HANDLER = false;

    if (!thd_test_options(thd, OPTION_NOT_AUTOCOMMIT | OPTION_BEGIN)) {
      if (trx_is_started(trx)) {
        innobase_commit(ht, thd, true);
      } else {
        /* Since the trx state is TRX_NOT_STARTED,
        trx_commit() will not be called. Reset
        trx->is_dd_trx here */
        ut_d(trx->is_dd_trx = false);
      }

    } else if (trx->isolation_level <= TRX_ISO_READ_COMMITTED &&
               MVCC::is_view_active(trx->read_view)) {
      mutex_enter(&trx_sys->mutex);

      trx_sys->mvcc->view_close(trx->read_view, true);

      mutex_exit(&trx_sys->mutex);
    }
```

SERIALIZABLE 은 자동 커밋이 아니면 잠금 없는 읽기 자체를 공유 잠금 읽기로 바꾼다. 그러면 [02] 가 read view 를 받는 갈래로 가지 않는다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L19079-L19083 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L19079-L19083))

```cpp
// ha_innodb.cc L19079-L19083
      } else if (trx->isolation_level == TRX_ISO_SERIALIZABLE &&
                 m_prebuilt->select_lock_type == LOCK_NONE &&
                 thd_test_options(thd, OPTION_NOT_AUTOCOMMIT | OPTION_BEGIN)) {
        m_prebuilt->select_lock_type = LOCK_S;
        m_stored_select_lock_type = LOCK_S;
```

`START TRANSACTION WITH CONSISTENT SNAPSHOT` 은 첫 읽기를 기다리지 않고 지금 view 를 연다. REPEATABLE READ 가 아니면 경고만 남긴다.

`storage` / `innobase` / `handler` / `ha_innodb.cc` L5928-L5942 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/ha_innodb.cc#L5928-L5942))

```cpp
// ha_innodb.cc L5928-L5942
  /* Assign a read view if the transaction does not have it yet.
  Do this only if transaction is using REPEATABLE READ isolation
  level. */
  trx->isolation_level =
      innobase_trx_map_isolation_level(thd_get_trx_isolation(thd));

  if (trx->isolation_level == TRX_ISO_REPEATABLE_READ) {
    trx_assign_read_view(trx);
  } else {
    push_warning_printf(thd, Sql_condition::SL_WARNING, HA_ERR_UNSUPPORTED,
                        "InnoDB: WITH CONSISTENT SNAPSHOT"
                        " was ignored because this phrase"
                        " can only be used with"
                        " REPEATABLE READ isolation level.");
  }
```

## 동작 흐름

```text
 trx_assign_read_view (trx0trx.cc L2291)
   srv_read_only_mode                      -> nullptr (읽기 전용 서버는 view 를 쓰지 않는다)
   MVCC::is_view_active(trx->read_view)     -> 그대로 돌려준다  (포인터가 nullptr 도 아니고 bit 0 도 아님)
   아니면 trx_sys->mvcc->view_open(trx->read_view, trx)

 MVCC::view_open (read0read.cc L499)
   L504  view != nullptr (닫힘 표시된 옛 view 가 남아 있다)
           L507  bit 0 을 지운다
           L606  자동 커밋 읽기 전용이고 m_ids 가 비어 있었고
                 L609  그 뒤로 새 trx id 가 하나도 안 나갔으면 (m_low_limit_id 가 그대로)
                       m_closed = false 로 되살리고 끝. 뮤텍스를 잡지 않는다
   L617  trx_sys_mutex_enter
   L619  옛 view 가 있으면 m_views 에서 빼고, 없으면 get_view (m_free 에서 꺼내거나 new)
   L627  [04] view->prepare(trx->id)
   L629  UT_LIST_ADD_FIRST(m_views, view)       새 view 가 앞, 오래된 view 가 뒤
   L636  trx_sys_mutex_exit
```

view 는 트랜잭션 수명과 다르게 산다. 격리 수준마다 열고 닫는 자리를 한 그림에 모으면 이렇다.

```text
 read view 의 수명 (O = 연다, X = 닫는다)

 시간 ->      BEGIN    SELECT 1           SELECT 2           COMMIT
              |        |                  |                  |
 RU           |   X    O ......... X   X  O ......... X       X
              |   RC 와 같은 자리에서 열고 닫는다 (TRX_ISO_READ_UNCOMMITTED < RC)
              |   만들기는 하지만 [02] L5326 이 view 를 보지 않는다
 RC           |   X    O ......... X   X  O ......... X       X
              |   store_lock L19763      store_lock          external_lock L19167
              |   (문장 시작)            external_lock (문장 끝, 자동 커밋이 아닐 때)
 RR           |        O ........................................ X
              |        첫 잠금 없는 읽기 (L4838)                  커밋 (trx_erase_lists L1817)
 RR + WITH    O ......................................................... X
 CONSISTENT   ha_innodb.cc L5935
 SNAPSHOT
 SERIALIZABLE |  자동 커밋이 아니면 SELECT 가 LOCK_S 잠금 읽기가 된다 (L19082)
              |  view 를 열지 않는다. 자동 커밋 SELECT 는 RR 과 같은 길을 간다

 문장마다 [02] 가 다시 L4838 에 오는 것은 external_lock 이 sql_stat_start = true 로 되돌리기 때문이다
 (ha_innodb.cc L18969)
```

커밋 쪽에서 view 를 닫는 자리는 트랜잭션 종류마다 다르다.

```text
 커밋에서 view 를 닫는 자리 (trx0trx.cc)

 RW 트랜잭션                 trx_erase_lists  L1817   view_close(own_mutex = true)
                                                       목록에서 빼서 m_free 로
 자동 커밋 읽기 전용 (AC-NL-RO)  trx_commit_in_memory L1973  view_close(own_mutex = false)
                                                       bit 0 만 켠다. 다음 SELECT 가 재사용 시도
 그 밖의 읽기 전용             trx_commit_in_memory L1996  view_close(own_mutex = false)
 세션 분리 (XA PREPARE 등)     trx_disconnect_from_mysql L653
```

## 결과가 쓰이는 곳

```text
 trx->read_view
      --> [02] 가 레코드마다 [05] 에 넘긴다
      --> trx_sys->mvcc->m_views 의 맨 앞에 걸린다
            purge 의 MVCC::clone_oldest_view 가 이 목록을 뒤에서부터 훑어 닫히지 않은
            가장 오래된 view 를 복사한다 (read0read.cc L685)  --> [purge]
      --> 오래 열린 RR view 하나가 purge 의 기준을 붙잡는다
```

## 다루지 않는 것

자동 커밋 읽기 전용 view 재사용이 purge 와 경합해도 안전하다는 증명(read0read.cc L511-L604 주석, P1 과 P2), `MVCC::get_view` 의 `m_free` 관리, `trx_start_low` 가 트랜잭션에 id 를 줄지 정하는 규칙(읽기 전용으로 시작하면 id 가 0 이다, trx0trx.cc L1395. 그러면 `m_creator_trx_id` 도 0), 격리 수준 매핑(`innobase_trx_map_isolation_level`)은 이 흐름의 곁가지라 줄만 적었다.
