# lock_rec_lock_fast

상위: [레코드 잠금과 교착](../README.md)

**가장 흔한 두 경우를 큐를 훑지 않고 끝낸다.** 페이지에 잠금이 하나도 없으면 새 `lock_t` 를 만들고, 페이지에 잠금이 딱 하나 있는데 그게 내 것이고 모드가 같으면 비트 하나만 켠다. 그 밖의 모든 경우는 `LOCK_REC_FAIL` 로 [05] 에 넘긴다. 이 함수는 충돌 판정을 하지 않는다. "다른 잠금이 없다"는 사실만으로 충돌이 없음을 보장받는다.

## 위치

`storage` / `innobase` / `lock` / `lock0lock.cc` L1617-L1693 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1617-L1693))

## 실제 코드

`storage` / `innobase` / `lock` / `lock0lock.cc` L1617-L1693 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1617-L1693))

```cpp
// lock0lock.cc L1617-L1693
static inline lock_rec_req_status lock_rec_lock_fast(
    bool impl,                /*!< in: if true, no lock is set
                              if no wait is necessary: we
                              assume that the caller will
                              set an implicit lock */
    ulint mode,               /*!< in: lock mode: LOCK_X or
                              LOCK_S possibly ORed to either
                              LOCK_GAP or LOCK_REC_NOT_GAP */
    const buf_block_t *block, /*!< in: buffer block containing
                              the record */
    ulint heap_no,            /*!< in: heap number of record */
    dict_index_t *index,      /*!< in: index of record */
    que_thr_t *thr)           /*!< in: query thread */
{
  // ... (L1631-L1645 생략: ut_ad 로 입력 모드 검사, [03] 과 같은 조건)
  lock_t *lock = nullptr;
  lock_t *other_lock =
      lock_sys->rec_hash.find_on_block(block, [&](lock_t *seen) {
        if (lock != nullptr) {
          return true;
        }
        lock = seen;
        return false;
      });

  trx_t *trx = thr_get_trx(thr);
  ut_ad(!trx_mutex_own(trx));

  lock_rec_req_status status = LOCK_REC_SUCCESS;

  if (lock == nullptr) {
    if (!impl) {
      RecLock rec_lock(index, block, heap_no, mode);

      trx_mutex_enter(trx);
      rec_lock.create(trx);
      trx_mutex_exit(trx);

      status = LOCK_REC_SUCCESS_CREATED;
    }
  } else {
    trx_mutex_enter(trx);

    if (other_lock != nullptr || lock->trx != trx ||
        lock->type_mode != (mode | LOCK_REC) ||
        lock_rec_get_n_bits(lock) <= heap_no) {
      status = LOCK_REC_FAIL;
    } else if (!impl) {
      /* If the nth bit of the record lock is already set
      then we do not set a new lock bit, otherwise we do
      set */
      if (!lock_rec_get_nth_bit(lock, heap_no)) {
        lock_rec_set_nth_bit(lock, heap_no);
        status = LOCK_REC_SUCCESS_CREATED;
      }
    }

    trx_mutex_exit(trx);
  }
  ut_ad(status == LOCK_REC_SUCCESS || status == LOCK_REC_SUCCESS_CREATED ||
        status == LOCK_REC_FAIL);
  return (status);
}
```

빠른 경로가 쓰는 `rec_hash.find_on_block` 은 페이지 단위로 훑는다. 람다가 두 번째 잠금에서 `true` 를 돌려주므로 순회는 많아야 두 칸에서 멈춘다.

## 동작 흐름

```text
 L1647  rec_hash.find_on_block(block, 람다)
          첫 번째 lock_t  -> lock 에 담고 계속 (L1652)
          두 번째 lock_t  -> 여기서 멈추고 other_lock 으로 돌려준다 (L1649)
        결과는 세 가지다
          lock == nullptr                        페이지에 잠금이 없다
          lock != nullptr, other_lock == nullptr  딱 하나
          other_lock != nullptr                   둘 이상

 L1661  lock == nullptr (페이지가 비었다)
 L1662    impl 이면 아무것도 만들지 않는다       -> LOCK_REC_SUCCESS
 L1663    아니면 RecLock(index, block, heap_no, mode)
 L1666    rec_lock.create(trx)                  lock_t 를 할당하고 큐 앞에 넣는다 (L1287)
 L1669    -> LOCK_REC_SUCCESS_CREATED

 L1671  lock != nullptr
 L1674    다음 넷 중 하나라도 맞으면 LOCK_REC_FAIL -> [05]
            other_lock != nullptr                둘 이상
            lock->trx != trx                     남의 잠금
            lock->type_mode != (mode | LOCK_REC) 모드나 정밀 모드가 다르다 (WAIT 비트 포함)
            n_bits <= heap_no                    비트맵이 이 레코드를 담지 못한다
 L1678    impl 이면 아무것도 하지 않는다        -> LOCK_REC_SUCCESS
 L1682    비트가 꺼져 있으면 켠다               -> LOCK_REC_SUCCESS_CREATED
          이미 켜져 있으면                      -> LOCK_REC_SUCCESS
```

같은 트랜잭션이 한 페이지를 차례로 훑을 때 이 경로가 빛난다. 첫 레코드에서 `lock_t` 하나를 만들고, 나머지 레코드는 같은 구조체에 비트만 켠다.

```text
 트랜잭션 T 가 페이지 P 를 FOR UPDATE 로 훑을 때 (모드 X, ORDINARY)

 heap  경로          결과                        그때 페이지 P 의 잠금
 2     L1661 create  lock_t#1 {T, X, bits: 2}    없음
 3     L1682 set     lock_t#1 {T, X, bits: 2 3}  lock_t#1 하나, T 의 것, 같은 모드
 4     L1682 set     lock_t#1 {T, X, bits: 2-4}  lock_t#1 하나, T 의 것, 같은 모드

 다른 트랜잭션 U 가 P 에 잠금 하나를 걸어 두었다면
 2     L1674 FAIL    [05] 로 넘긴다              lock_t#U 하나, 남의 것 (충돌 판정은 [05] 에서)
```

```text
 왜 충돌 판정 없이 부여해도 되는가

 페이지에 잠금이 없다        -> 이 레코드에 누가 쥔 것도, 기다리는 것도 없다
 잠금이 하나뿐이고 내 것이다 -> 남의 잠금이 없으니 충돌할 상대가 없다
 그리고 이 판단은 페이지 shard 래치 아래에서 한다 ([02] L5446)
   판단과 부여 사이에 다른 트랜잭션이 같은 페이지에 잠금을 넣을 수 없다
 단, 암묵 잠금은 보지 않는다 (함수 주석 L1612)
   그래서 호출자 [02] 가 먼저 lock_rec_convert_impl_to_expl 로 드러내 둔다
```

## 결과가 쓰이는 곳

```text
 LOCK_REC_SUCCESS / LOCK_REC_SUCCESS_CREATED
      --> [03] 이 DB_SUCCESS / DB_SUCCESS_LOCKED_REC 로 바꿔 돌려준다
 LOCK_REC_FAIL
      --> [03] L1890 이 [05] lock_rec_lock_slow 를 부른다
 새 lock_t
      --> trx->lock.trx_locks 끝에 붙는다 (add_to_trx_locks L1226)
          커밋 때 [11] 쪽 해제 경로가 이 목록을 따라간다
```

## 다루지 않는 것

`RecLock` 생성자가 비트맵 크기(`m_size`)를 정하는 방식과 `lock_alloc` 이 트랜잭션 전용 풀에서 메모리를 얻는 과정, Performance Schema 용 필드 기록은 이 흐름의 곁가지라 요약만 했다.
