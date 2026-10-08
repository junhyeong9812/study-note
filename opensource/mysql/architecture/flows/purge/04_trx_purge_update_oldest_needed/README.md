# trx_purge_update_oldest_needed

상위: [purge](../README.md)

**purge 가 "어디까지 치워도 되는가"를 새로 정하는 자리다.** 지금 열려 있는 read view 중 가장 오래된 것을 복사해 `purge_sys->view` 로 삼고, 그 view 의 `m_low_limit_no`(이 view 가 필요로 하지 않는 커밋 번호의 상한)와 GTID 영속화가 아직 필요로 하는 커밋 번호 중 작은 쪽을 `m_lowest_needed_trx_no` 로 둔다. history list 의 undo 로그 중 커밋 번호가 이 값보다 작은 것만 [05] 가 꺼내고 [10] 이 잘라낸다. 열린 view 가 하나도 없으면 지금 이 순간을 기준으로 새 view 를 만든다. 둘 다 `purge_sys->latch` 의 X 래치 안에서 바꾸므로, 읽는 쪽([일관 읽기(MVCC)](../../mvcc-read/10_trx_undo_get_undo_rec/README.md))은 S 래치로 일관된 값을 본다.

## 위치

`storage` / `innobase` / `trx` / `trx0purge.cc` L252-L273 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L252-L273))

## 실제 코드

함수와 머리 주석이다. 주석은 GTID 영속화 쪽 값이 시간에 따라 단조롭지 않아 경계가 잠깐 뒤로 갈 수도 있다고 적었다. 호출 순서(view 를 먼저 복사하고 GTID 값을 나중에 읽는다)가 정확성에 중요하다는 설명도 함수 안에 있다.

`storage` / `innobase` / `trx` / `trx0purge.cc` L238-L273 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/trx/trx0purge.cc#L238-L273))

```cpp
// trx0purge.cc L238-L273
/** Updates the purge_sys->view and purge_sys->m_lowest_needed_trx_no, to the
safe, most current estimates which are based on oldest currently open read view
and progress of GTID persistor.
Because the value of lowest needed transaction number returned by
Clone_persist_gtid::get_oldest_trx_no() is not monotone over time, the
m_lowest_needed_trx_no may sometimes get smaller, perhaps smaller than already
purged trx no - when this happens it doesn't mean that we've lost important data
as the value returned by GTID persistor in such cases is lower than really
needed.
The estimates should eventually converge on the right value if system is idle.
This function is called at startup and then periodically by purge thread, to
learn how much can be purged - which is limited by m_lowest_needed_trx_no.
Note that m_lowest_needed_trx_no might be lower than needed by purge_sys->view
in case GTID persistor is lagging. */
static void trx_purge_update_oldest_needed() {
  rw_lock_x_lock(&purge_sys->latch, UT_LOCATION_HERE);
  trx_sys->mvcc->clone_oldest_view(&purge_sys->view);
  const auto needed_by_purge_view = purge_sys->view.low_limit_no();
  /* The Clone_persist_gtid::get_oldest_trx_no() can return TRX_ID_MAX, if there
  are no GTIDs pending to be persisted. It is crucial for correctness, that
  get_oldest_trx_no() must be called after the oldest view was cloned, so that
  in case it returns TRX_ID_MAX, we properly cap it to no more than
  trx_sys->serialisation_min_trx_no seen at an earlier moment (which is an upper
  bound for purge_sys->view->low_limit_no() on the one hand, and at
  the same time a lower bound for trx->no of any trx assigned a new GTID since
  then and at the same time ). If we do that in opposite order, it could be the
  case that new GTIDs were assigned after the get_oldest_trx_no() has returned
  TRX_ID_MAX and we clone an oldest read view even later and thus decide to
  remove all Undo Logs not needed by this read view, including the Undo Log
  Header which stored the newly assigned GTID, before it is persisted.*/
  const auto needed_by_persistor =
      clone_sys->get_gtid_persistor().get_oldest_trx_no();
  purge_sys->m_lowest_needed_trx_no =
      std::min(needed_by_purge_view, needed_by_persistor);
  rw_lock_x_unlock(&purge_sys->latch);
}
```

가장 오래된 view 를 고르는 쪽이다. `m_views` 는 새 view 를 앞에 붙이므로 뒤에서부터 훑으면 오래된 것부터 나온다. 닫힌 view 는 건너뛴다. 이미 가진 purge view 보다 앞서지 못하면 바꾸지 않는다.

`storage` / `innobase` / `read` / `read0read.cc` L685-L720 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L685-L720))

```cpp
// read0read.cc L685-L720
void MVCC::clone_oldest_view(ReadView *view) {
  trx_sys_mutex_enter();

  ReadView *oldest_view;
  for (oldest_view = UT_LIST_GET_LAST(m_views); oldest_view != nullptr;
       oldest_view = UT_LIST_GET_PREV(m_view_list, oldest_view)) {
    if (!oldest_view->is_closed()) {
      if (oldest_view->low_limit_no() <= view->low_limit_no()) {
        /* We won't gain anything by switching to oldest_view - as purge will
        not be able to move any further than low_limit_no(). More importantly,
        switching to oldest_view poses a risk of a crash, if it saw a strictly
        smaller subset of transaction than view. Thankfully, we can prove the
        later case happens only when a transaction is considering to reopen the
        oldest_view, but will decide not to do it, so we can - and should! -
        ignore it. See the proof in MVCC::view_open(). In either case not
        updating purge's view is the right decision here. */
        trx_sys_mutex_exit();
        return;
      }
      break;
    }
  }

  if (oldest_view == nullptr) {
    view->prepare(0);

    trx_sys_mutex_exit();

  } else {
    view->copy_prepare(*oldest_view);

    trx_sys_mutex_exit();

    view->copy_complete();
  }
}
```

복사는 두 단계다. 뮤텍스 안에서 값을 옮기고(`copy_prepare`), 뮤텍스 밖에서 그 view 를 만든 트랜잭션 자신의 id 를 `m_ids` 에 넣는다(`copy_complete`).

`storage` / `innobase` / `read` / `read0read.cc` L639-L683 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L639-L683))

```cpp
// read0read.cc L639-L683
/**
Copy state from another view. Must call copy_complete() to finish.
@param other            view to copy from */

void ReadView::copy_prepare(const ReadView &other) {
  ut_ad(&other != this);

  if (!other.m_ids.empty()) {
    const ids_t::value_type *p = other.m_ids.data();

    m_ids.assign(p, p + other.m_ids.size());
  } else {
    m_ids.clear();
  }

  m_up_limit_id = other.m_up_limit_id;

  m_low_limit_no = other.m_low_limit_no;

  m_low_limit_id = other.m_low_limit_id;

  m_creator_trx_id = other.m_creator_trx_id;
}

/**
Complete the copy, insert the creator transaction id into the
m_ids too and adjust the m_up_limit_id, if required */

void ReadView::copy_complete() {
  ut_ad(!trx_sys_mutex_own());

  if (m_creator_trx_id > 0) {
    m_ids.insert(m_creator_trx_id);
  }

  if (!m_ids.empty()) {
    /* The last active transaction has the smallest id. */
    m_up_limit_id = std::min(m_ids.front(), m_up_limit_id);
  }

  ut_ad(m_up_limit_id <= m_low_limit_id);

  /* We added the creator transaction ID to the m_ids. */
  m_creator_trx_id = 0;
}
```

## 동작 흐름

```text
 trx_purge_update_oldest_needed   (purge 코디네이터, [03] 의 배치마다 한 번)

 L253  rw_lock_x_lock(&purge_sys->latch)
 L254  trx_sys->mvcc->clone_oldest_view(&purge_sys->view)
         L686  trx_sys_mutex_enter
         L689  m_views 를 뒤에서부터 (오래된 것부터)
                 닫힌 view (자동 커밋 읽기 전용이 닫아 둔 것) 는 건너뛴다
                 처음 만난 열린 view 가 oldest
         L692    oldest.low_limit_no <= 지금 purge view 의 low_limit_no
                   -> 바꾸지 않고 return (경계는 뒤로 가지 않는다)
         L708  열린 view 가 없다   -> view->prepare(0)  지금 이 순간의 view
         L713  있다                -> copy_prepare (뮤텍스 안) -> copy_complete (밖)
 L255  needed_by_purge_view = purge_sys->view.low_limit_no()
 L268  needed_by_persistor  = clone_sys->get_gtid_persistor().get_oldest_trx_no()
 L270  m_lowest_needed_trx_no = min(둘)
 L272  rw_lock_x_unlock
```

purge view 는 두 축의 경계를 모두 가진다. 가시성 판정에는 trx id 축을, 치울 범위에는 trx no 축을 쓴다.

```text
 purge_sys->view 에서 쓰는 값

 축        값                 쓰는 곳
 trx id    m_up_limit_id      changes_visible: "가장 오래된 view 도 이 trx 의 변경을 보는가"
           m_low_limit_id     -> mvcc-read [10] 의 기록 없음 판정
           m_ids
 trx no    m_low_limit_no     -> m_lowest_needed_trx_no -> [05] 의 멈춤, [10] 의 잘라내기 상한

 m_low_limit_no 는 view 를 만들 때의 trx_sys->serialisation_min_trx_no 다
   (mvcc-read [04] ReadView::prepare L451)
 필드 주석 (read0types.h L284-L286): 이 값보다 작은 커밋 번호의 undo 로그는 이 view 가
 볼 필요가 없고, 다른 view 도 필요로 하지 않으면 purge 가 지워도 된다
```

오래된 view 가 purge 를 붙잡는 모습을 시간으로 보면 이렇다.

```text
 시간 ->

 trx A (RR)   BEGIN; SELECT ...  view 생성 (m_low_limit_no = 600) ...... (커밋하지 않음)
 다른 trx들   커밋 no=610, 620, ..., 900  (update undo 가 history 에 쌓인다)
 purge        [04] -> oldest = A 의 view -> m_lowest_needed_trx_no = 600
              [05] -> no < 600 인 것만 꺼낸다. 610 이후는 history 에 남는다
 trx A 커밋   view 가 m_views 에서 빠진다
 purge        [04] -> 다음으로 오래된 view, 없으면 prepare(0) -> 경계가 단번에 앞으로
```

## 결과가 쓰이는 곳

```text
 purge_sys->view
      --> mvcc-read 의 trx_undo_get_undo_rec 가 S 래치로 읽는다
      --> row_vers_must_preserve_del_marked (row0vers.cc L584) 가 delete-mark 된 옛 버전을
          남겨야 하는지 판단할 때 쓴다
 purge_sys->m_lowest_needed_trx_no
      --> [05] trx_purge_fetch_next_rec 의 멈춤 조건 (trx0purge.cc L2221)
      --> [10] trx_purge_truncate_history 의 상한 (trx0purge.cc L1625)
```

## 다루지 않는 것

자동 커밋 읽기 전용 view 의 재사용이 이 복사와 경합해도 안전하다는 증명(read0read.cc L511-L604 주석의 P1, P2), GTID 영속화(`Clone_persist_gtid::get_oldest_trx_no`)가 undo 로그 헤더의 GTID 를 지키려고 경계를 낮추는 이유는 이 흐름의 곁가지라 줄만 적었다. read view 를 여는 쪽은 [일관 읽기(MVCC)](../../mvcc-read/03_trx_assign_read_view/README.md)에 있다.
