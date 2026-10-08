# ReadView::prepare

상위: [일관 읽기(MVCC)와 undo 체인](../README.md)

**`trx_sys->mutex` 를 쥔 채로 "지금 이 순간 어떤 트랜잭션이 아직 끝나지 않았는가"를 복사해 read view 의 네 값을 채우는 자리다.** 다음에 줄 트랜잭션 번호가 `m_low_limit_id` 가 되고, 활성 RW 트랜잭션 목록(`trx_sys->rw_trx_ids`)에서 자기 자신을 뺀 것이 `m_ids` 가 되고, 그중 가장 작은 값이 `m_up_limit_id` 가 된다. 여기에 purge 용 값 `m_low_limit_no` 가 하나 더 붙는다. 뮤텍스 안에서 복사하기 때문에 그 사이에 트랜잭션이 시작하거나 끝날 수 없고, 이 순간이 곧 스냅샷 시점이다.

## 위치

`storage` / `innobase` / `read` / `read0read.cc` L446-L469 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L446-L469))

## 실제 코드

본체다. 네 값을 차례로 채우고 순서 관계를 `ut_a` 로 확인한다.

`storage` / `innobase` / `read` / `read0read.cc` L446-L469 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L446-L469))

```cpp
// read0read.cc L446-L469
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
}
```

`m_ids` 를 채우는 복사다. 원본이 정렬되어 있으므로 자기 id 의 자리를 이진 탐색으로 찾고, 그 앞과 뒤를 `memmove` 두 번으로 옮긴다.

`storage` / `innobase` / `read` / `read0read.cc` L353-L407 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/read/read0read.cc#L353-L407))

```cpp
// read0read.cc L353-L407
void ReadView::copy_trx_ids(const trx_ids_t &trx_ids) {
  ut_ad(trx_sys_mutex_own());

  ulint size = trx_ids.size();

  if (m_creator_trx_id > 0) {
    ut_ad(size > 0);
    --size;
  }

  if (size == 0) {
    m_ids.clear();
    return;
  }

  m_ids.reserve(size);
  m_ids.resize(size);

  ids_t::value_type *p = m_ids.data();

  /* Copy all the trx_ids except the creator trx id */

  if (m_creator_trx_id > 0) {
    /* Note: We go through all this trouble because it is
    unclear whether std::vector::resize() will cause an
    overhead or not. We should test this extensively and
    if the vector to vector copy is fast enough then get
    rid of this code and replace it with more readable
    and obvious code. The code below does exactly one copy,
    and filters out the creator's trx id. */

    trx_ids_t::const_iterator it =
        std::lower_bound(trx_ids.begin(), trx_ids.end(), m_creator_trx_id);

    ut_ad(it != trx_ids.end() && *it == m_creator_trx_id);

    ulint i = std::distance(trx_ids.begin(), it);
    ulint n = i * sizeof(trx_ids_t::value_type);

    ::memmove(p, &trx_ids[0], n);

    n = (trx_ids.size() - i - 1) * sizeof(trx_ids_t::value_type);

    ut_ad(i + (n / sizeof(trx_ids_t::value_type)) == m_ids.size());

    if (n > 0) {
      ::memmove(p + i, &trx_ids[i + 1], n);
    }
  } else {
    ulint n = size * sizeof(trx_ids_t::value_type);

    ::memmove(p, &trx_ids[0], n);
  }

  m_up_limit_id = m_ids.front();
```

복사 원본이 되는 두 전역 값이다. 둘 다 원자 변수를 읽기만 한다.

`storage` / `innobase` / `include` / `trx0sys.ic` L236-L244 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/trx0sys.ic#L236-L244))

```cpp
// trx0sys.ic L236-L244
/** Reads trx->no up to which all transactions have been serialised.
 @return minimum value which is still possibly not serialised */
static inline trx_id_t trx_get_serialisation_min_trx_no(void) {
  return (trx_sys->serialisation_min_trx_no.load());
}

inline trx_id_t trx_sys_get_next_trx_id_or_no() {
  return trx_sys->next_trx_id_or_no.load();
}
```

필드 선언과 주석이다. 주석이 두 경계를 각각 "high water mark", "low water mark" 라고 부른다.

`storage` / `innobase` / `include` / `read0types.h` L267-L290 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/include/read0types.h#L267-L290))

```cpp
// read0types.h L267-L290
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
```

## 동작 흐름

```text
 ReadView::prepare(id)   호출자 view_open 이 trx_sys_mutex 를 쥐고 있다 (L447 ut_ad)

 L449  m_creator_trx_id = id                    읽기 전용이면 0
 L451  m_low_limit_no = serialisation_min_trx_no 아직 직렬화(커밋 번호 부여)가 덜 끝난 가장 작은 trx->no
 L453  m_low_limit_id = next_trx_id_or_no        다음에 나갈 번호. 이 이상은 "미래"
 L455  ut_a(m_low_limit_no <= m_low_limit_id)
 L457  rw_trx_ids 가 비어 있지 않으면 copy_trx_ids
         L358  자기 id 가 목록에 있으면 하나 덜 복사한다
         L384  lower_bound 로 자기 자리 i 를 찾아
         L392  [0, i) 를 memmove,  L399  [i+1, end) 를 memmove
         L407  m_up_limit_id = m_ids.front()
       비어 있으면 m_ids.clear()
 L464  m_up_limit_id = m_ids 가 있으면 front, 없으면 m_low_limit_id
 L466  ut_a(m_up_limit_id <= m_low_limit_id)
 L468  m_closed = false
```

예를 들어 보자. 트랜잭션 번호 100 부터 104 까지가 시작했고 101 과 103 만 커밋했다. 102 가 view 를 연다.

```text
 rw_trx_ids = [100, 102, 104]   (정렬, 활성 RW 만. 101 과 103 은 커밋해서 빠졌다)
 next_trx_id_or_no = 107        (101 과 103 이 커밋하며 105, 106 을 trx->no 로 가져갔다.
                                 id 와 no 는 같은 계수기에서 나온다)
 view 를 여는 trx = 102

 copy_trx_ids  lower_bound(102) -> i = 1
               [100] + [104]  ->  m_ids = [100, 104]

 m_creator_trx_id = 102
 m_low_limit_id   = 107
 m_up_limit_id    = 100           (m_ids.front())

          100      101      102      103      104      107 ...
 ---------+--------+--------+--------+--------+--------+-------------> trx_id
   < 100  | m_ids  | 커밋   | 자기   | 커밋   | m_ids  | >= 107
   보인다  | 안 보임 | 보인다  | 보인다  | 보인다  | 안 보임 | 안 보인다
```

```text
 trx 번호 하나에 두 가지 쓰임 (trx_sys->next_trx_id_or_no 하나에서 나온다)

 trx->id   트랜잭션이 RW 로 시작할 때 받는다. 레코드의 DB_TRX_ID 에 찍힌다
           read view 의 m_ids, m_up_limit_id, m_low_limit_id 가 이 축이다
 trx->no   커밋할 때 받는다 (직렬화 번호). undo 로그 헤더와 history list 의 순서다
           read view 의 m_low_limit_no 가 이 축이다
           purge 는 "trx->no 가 m_low_limit_no 보다 작은 undo 는 이 view 에 필요 없다"고 본다
           (read0types.h L284-L286 주석)
```

## 결과가 쓰이는 곳

```text
 m_low_limit_id, m_up_limit_id, m_ids, m_creator_trx_id
      --> [06] changes_visible 의 판정 재료. view 가 닫힐 때까지 바뀌지 않는다

 m_low_limit_no
      --> purge 가 clone_oldest_view 로 가장 오래된 view 를 복사해
          그 값까지의 undo 만 치운다  --> [purge] 04 trx_purge_update_oldest_needed

 trx_sys->mvcc->m_views 의 맨 앞
      --> 목록 순서가 곧 m_low_limit_no 순서다 (validate 의 ViewCheck 가 앞에서 뒤로 m_low_limit_no 가 커지지 않음을 확인한다, read0read.cc L192)
```

## 다루지 않는 것

`ids_t` 의 메모리 관리(`reserve` 가 최소 32 개를 잡는다, `MIN_TRX_IDS`), 디버그 빌드에서 100 번에 한 번 `m_ids` 의 모든 id 가 실제로 활성인지 확인하는 코드(L409-L438), purge 용 복사(`copy_prepare` 와 `copy_complete`)는 이 흐름의 곁가지라 줄만 적었다. 뒤의 둘은 [purge](../../purge/04_trx_purge_update_oldest_needed/README.md)에서 다룬다. `trx->no` 를 주는 자리(`trx_serialisation_number_get`)는 [커밋과 binlog 2PC](../../commit-2pc/10_trx_commit_low/README.md)에 있다.
