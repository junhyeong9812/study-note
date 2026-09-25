# mtr_t::commit

상위: [mini-transaction과 redo 기록](../README.md)

**이 흐름의 진입점이자 갈림길이다.** 본문은 20줄 남짓이고, 실제 일은 `Command` 객체에 넘긴다. 볼거리는 L672-L673 의 조건이다. redo 레코드가 하나라도 있거나, redo 없는 모드에서 페이지를 바꿨으면 `execute` 로 가고, 아니면 래치만 풀고 끝난다. 읽기만 한 mtr 은 log buffer 에 한 바이트도 닿지 않는다.

## 위치

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L662-L686 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L662-L686))

## 실제 코드

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L662-L686 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L662-L686))

```cpp
// mtr0mtr.cc L662-L686
void mtr_t::commit() {
  ut_ad(is_active());
  ut_ad(!is_inside_ibuf());
  ut_ad(m_impl.m_magic_n == MTR_MAGIC_N);
  m_impl.m_state = MTR_STATE_COMMITTING;

  DBUG_EXECUTE_IF("mtr_commit_crash", DBUG_SUICIDE(););

  Command cmd(this);

  if (has_any_log_record() ||
      (has_modifications() && m_impl.m_log_mode == MTR_LOG_NO_REDO)) {
    ut_ad(!srv_read_only_mode || m_impl.m_log_mode == MTR_LOG_NO_REDO);

    cmd.execute();
  } else {
    cmd.release_all();
    cmd.release_resources();
  }
#ifndef UNIV_HOTBACKUP
  check_nolog_and_unmark();
#endif /* !UNIV_HOTBACKUP */

  ut_d(remove_from_debug_list());
}
```

`Command` 는 mtr 의 내부 상태(`m_impl`)를 넘겨받아 commit 동안만 산다. 소멸자가 `m_impl == nullptr` 을 확인하므로 `release_resources` 를 부르지 않고 끝나면 debug 빌드에서 걸린다.

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L382-L399 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L382-L399))

```cpp
// mtr0mtr.cc L382-L399
class mtr_t::Command {
 public:
  /** Constructor.
  Takes ownership of the mtr->m_impl, is responsible for deleting it.
  @param[in,out]        mtr     Mini-transaction */
  explicit Command(mtr_t *mtr) : m_locks_released() { init(mtr); }

  void init(mtr_t *mtr) {
    m_impl = &mtr->m_impl;
    m_sync = mtr->m_sync;
  }

  /** Destructor */
  ~Command() { ut_ad(m_impl == nullptr); }

  /** Write the redo log record, add dirty pages to the flush list and
  release the resources. */
  void execute();
```

두 갈래가 공통으로 지나는 정리 함수다.

`storage` / `innobase` / `mtr` / `mtr0mtr.cc` L638-L659 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/mtr/mtr0mtr.cc#L638-L659))

```cpp
// mtr0mtr.cc L638-L659
void mtr_t::Command::release_resources() {
  ut_ad(m_impl->m_magic_n == MTR_MAGIC_N);

  /* Currently only used in commit */
  ut_ad(m_impl->m_state == MTR_STATE_COMMITTING);

#ifdef UNIV_DEBUG
  Debug_check release;
  Iterate<Debug_check> iterator(release);

  m_impl->m_memo.for_each_block_in_reverse(iterator);
#endif /* UNIV_DEBUG */

  /* Reset the mtr buffers */
  m_impl->m_log.erase();

  m_impl->m_memo.erase();

  m_impl->m_state = MTR_STATE_COMMITTED;

  m_impl = nullptr;
}
```

## 동작 흐름

```text
 L666  m_state = MTR_STATE_COMMITTING
 L668  (debug) mtr_commit_crash 면 여기서 죽는다
 L670  Command cmd(this)               m_impl 과 m_sync 를 넘겨받는다 (L389-L392)
 L672  has_any_log_record()            m_n_log_recs > 0 (mtr0mtr.h L613)
 L673  || (has_modifications() && m_log_mode == MTR_LOG_NO_REDO)
         참   L676  cmd.execute()      --> [04]
                     예약, 복사, flush list 추가, 래치 해제까지 전부
         거짓 L678  cmd.release_all()          m_memo 의 슬롯을 역순으로 풀어 준다
              L679  cmd.release_resources()    m_log, m_memo erase, COMMITTED
 L682  check_nolog_and_unmark          [01] 에서 건 전역 표시를 거둔다
 L685  (debug) 스레드 지역 목록에서 뺀다
```

```text
 어느 mtr 이 어느 갈래로 가는가

 m_n_log_recs   m_modifications   m_log_mode   갈래
 ------------   ---------------   ----------   -------------------------------
 > 0            any               ALL          execute: redo 를 쓰고 flush list 에
 0              true              NO_REDO      execute: redo 없이 flush list 에만 (lsn 0, 0)
 0              true              ALL          release 만 (레코드 없는 수정은 flush list 에도 안 붙는다)
 0              false             any          release 만 (읽기 전용 mtr)
```

세 번째 줄은 L672-L673 조건에서 바로 읽히는 결과다. 이 경우 페이지는 바뀌었어도 flush list 에 붙지 않는다.

## 결과가 쓰이는 곳

```text
 cmd.execute()
      --> mtr->m_commit_lsn 을 채운다 (mtr0mtr.cc L869)
      --> 트랜잭션 커밋이 mtr->commit_lsn() 으로 읽는다 (trx0trx.cc L2046)  [커밋과 binlog 2PC]

 래치 해제
      --> commit 이 돌아온 순간 다른 스레드가 이 페이지를 잡을 수 있다
      --> 그때 페이지는 이미 flush list 에 있고 newest_modification 이 찍혀 있다
```

## 다루지 않는 것

`Release_all` 이 슬롯 종류별로 부르는 `memo_slot_release`(페이지 래치, 테이블스페이스 래치, buf fix 해제)와 debug 전용 검사(`Debug_check`, `remove_from_debug_list`)는 곁가지라 요약만 했다.
