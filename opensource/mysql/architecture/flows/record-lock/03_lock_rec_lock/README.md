# lock_rec_lock

상위: [레코드 잠금과 교착](../README.md)

**레코드 잠금 요청이 모두 모이는 갈림길이다.** 읽기 쪽([02], 보조 인덱스의 `lock_sec_rec_read_check_and_lock`)과 수정 쪽(`lock_clust_rec_modify_check_and_lock`)이 모두 이 함수를 부르고, 이 함수는 먼저 [04] 빠른 경로를 시도한 뒤 실패하면 [05] 느린 경로로 넘긴다. 본문은 `switch` 하나지만, 들어오기 전에 지켜져 있어야 하는 조건(페이지 shard 래치, 테이블 의도 잠금)이 `ut_ad` 로 적혀 있다.

## 위치

`storage` / `innobase` / `lock` / `lock0lock.cc` L1864-L1894 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1864-L1894))

## 실제 코드

`storage` / `innobase` / `lock` / `lock0lock.cc` L1864-L1894 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L1864-L1894))

```cpp
// lock0lock.cc L1864-L1894
static dberr_t lock_rec_lock(bool impl, select_mode sel_mode, ulint mode,
                             const buf_block_t *block, ulint heap_no,
                             dict_index_t *index, que_thr_t *thr) {
  ut_ad(locksys::owns_page_shard(block->get_page_id()));
  ut_ad(!srv_read_only_mode);
  ut_ad((LOCK_MODE_MASK & mode) != LOCK_S ||
        lock_table_has(thr_get_trx(thr), index->table, LOCK_IS));
  ut_ad((LOCK_MODE_MASK & mode) != LOCK_X ||
        lock_table_has(thr_get_trx(thr), index->table, LOCK_IX));
  ut_ad((LOCK_MODE_MASK & mode) == LOCK_S || (LOCK_MODE_MASK & mode) == LOCK_X);
  ut_ad(mode - (LOCK_MODE_MASK & mode) == LOCK_GAP ||
        mode - (LOCK_MODE_MASK & mode) == LOCK_REC_NOT_GAP ||
        mode - (LOCK_MODE_MASK & mode) == 0);
  ut_ad(index->is_clustered() || !dict_index_is_online_ddl(index));
  /* Implicit locks are equivalent to LOCK_X|LOCK_REC_NOT_GAP, so we can omit
  creation of explicit lock only if the requested mode was LOCK_REC_NOT_GAP */
  ut_ad(!impl || ((mode & LOCK_REC_NOT_GAP) == LOCK_REC_NOT_GAP));
  /* We try a simplified and faster subroutine for the most
  common cases */
  switch (lock_rec_lock_fast(impl, mode, block, heap_no, index, thr)) {
    case LOCK_REC_SUCCESS:
      return (DB_SUCCESS);
    case LOCK_REC_SUCCESS_CREATED:
      return (DB_SUCCESS_LOCKED_REC);
    case LOCK_REC_FAIL:
      return (
          lock_rec_lock_slow(impl, sel_mode, mode, block, heap_no, index, thr));
    default:
      ut_error;
  }
}
```

`impl` 이 `true` 로 오는 곳은 레코드를 고치는 쪽이다. 잠금을 기다릴 필요가 없으면 명시 잠금을 만들지 않고, 레코드의 `DB_TRX_ID` 가 곧 잠금이 된다.

`storage` / `innobase` / `lock` / `lock0lock.cc` L5293-L5297 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/lock/lock0lock.cc#L5293-L5297))

```cpp
// lock0lock.cc L5293-L5297
    ut_ad(lock_table_has(thr_get_trx(thr), index->table, LOCK_IX));

    err = lock_rec_lock(true, SELECT_ORDINARY, LOCK_X | LOCK_REC_NOT_GAP, block,
                        heap_no, index, thr);

```

## 동작 흐름

```text
 L1867  이 페이지의 lock_sys shard 래치를 이미 쥐고 있어야 한다 ([02] L5446)
 L1869  S 를 원하면 테이블에 IS, X 를 원하면 테이블에 IX 가 이미 있어야 한다
 L1873  모드는 S 나 X 둘 중 하나
 L1874  정밀 모드는 GAP / REC_NOT_GAP / 0(ORDINARY) 중 하나
          INSERT_INTENTION 은 여기로 오지 않는다
          (lock_rec_insert_check_and_lock 이 [06] 과 [07] 을 직접 부른다, L5106-L5122)
 L1880  impl == true 면 REC_NOT_GAP 이어야 한다
          암묵 잠금은 X|REC_NOT_GAP 과 같은 뜻이라서

 L1883  [04] lock_rec_lock_fast
          LOCK_REC_SUCCESS          L1885  DB_SUCCESS             이미 있었다
          LOCK_REC_SUCCESS_CREATED  L1887  DB_SUCCESS_LOCKED_REC  새로 켰다
          LOCK_REC_FAIL             L1890  [05] lock_rec_lock_slow 로
```

```text
 이 함수를 부르는 네 곳 (lock0lock.cc)

 호출 줄  호출자                                    impl   mode            sel_mode
 L5295    lock_clust_rec_modify_check_and_lock      true   X|REC_NOT_GAP   SELECT_ORDINARY
 L5350    lock_sec_rec_modify_check_and_lock        true   X|REC_NOT_GAP   SELECT_ORDINARY
 L5406    lock_sec_rec_read_check_and_lock          false  mode|gap_mode   호출자가 준 값
 L5457    [02] lock_clust_rec_read_check_and_lock   false  mode|gap_mode   호출자가 준 값
```

```text
 반환값의 뜻

 DB_SUCCESS             새 잠금 없음 (이미 충분한 잠금이 있거나, impl 이라 만들지 않았다)
 DB_SUCCESS_LOCKED_REC  이번 호출로 비트를 켰거나 lock_t 를 만들었다
 DB_LOCK_WAIT           [07] 이 기다리는 잠금을 큐에 넣었다
 DB_DEADLOCK            [07] 에서 이미 강제 롤백 대상(TRX_FORCE_ROLLBACK)이었다
 DB_SKIP_LOCKED         SKIP LOCKED 라 충돌을 만나자 기다리지 않고 돌아왔다
 DB_LOCK_NOWAIT         NOWAIT 라 충돌을 만나자 기다리지 않고 돌아왔다
```

## 결과가 쓰이는 곳

```text
 반환값
      --> [02] 를 거쳐 [01] sel_set_rec_lock -> row_search_mvcc 의 switch 로
      --> 수정 쪽은 lock_clust_rec_modify_check_and_lock 을 거쳐 row_upd / row_ins 로
```

## 다루지 않는 것

수정 쪽 두 함수(`lock_clust_rec_modify_check_and_lock`, `lock_sec_rec_modify_check_and_lock`)의 나머지 본문, 공간 인덱스의 `lock_prdt_lock` 은 이 흐름의 곁가지라 요약만 했다.
