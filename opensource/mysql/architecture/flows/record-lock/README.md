# 레코드 잠금과 교착

상위: [MySQL 아키텍처 지도](../../README.md)

`SELECT ... FOR UPDATE`, `UPDATE`, `DELETE` 가 레코드 하나에 잠금을 걸고, **충돌하면 대기 큐에 들어가 잠들었다가, 풀리거나 교착 희생자로 뽑히거나 시간이 다 돼서 깨어날 때까지**의 흐름이다. INSERT 쪽 입구(insert intention, [B+Tree 삽입과 분할](../btree-insert/README.md)의 04)도 같은 큐로 들어온다. 이 흐름에는 **스레드 경계가 둘** 있다. 잠금을 요청하고 잠드는 것은 사용자 스레드이고, 교착 탐지와 타임아웃은 백그라운드 스레드 `lock_wait_timeout_thread` 가 하며, 잠든 스레드를 깨우는 것은 잠금을 푸는 다른 트랜잭션의 스레드다. 흐름은 [08] 에서 사용자 스레드가 깨어나 `row_search_mvcc` 로 돌아가 같은 레코드를 다시 찾는 데서 끝난다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 사용자 스레드 A (잠금 요청)
 ------------------------------------------------------------------
 row_search_mvcc                                     row0sel.cc L4431
      +-- 범위와 레코드 관계로 lock_type 을 고른다  L5231-L5245
      |     LOCK_ORDINARY / LOCK_REC_NOT_GAP / LOCK_GAP
      +-- [01] sel_set_rec_lock                      L5251
            +-- [02] lock_clust_rec_read_check_and_lock   lock0lock.cc L5420
                  +-- lock_rec_convert_impl_to_expl         L5441  암묵 잠금을 명시 잠금으로
                  +-- Shard_latch_guard(page_id)            L5446  이 페이지의 shard 만 잡는다
                  +-- [03] lock_rec_lock                    L5457
                        +-- [04] lock_rec_lock_fast         L1883  페이지에 잠금이 없거나 내 것 하나뿐
                        +-- [05] lock_rec_lock_slow         L1890
                              +-- lock_rec_has_expl         L1792  이미 충분히 센 잠금이 있나
                              +-- [06] lock_rec_other_has_conflicting  L1808  호환 판정
                              +-- 충돌 없음 -> lock_rec_add_to_queue   L1839  비트 하나 켜고 끝
                              +-- 충돌 -> [07] RecLock::add_to_waitq   L1825  LOCK_WAIT 잠금 + wait-for 간선
                                          DB_LOCK_WAIT 를 돌려준다

 INSERT 쪽 입구 ([B+Tree 삽입] 04 가 다룬다)
 btr_cur_ins_lock_and_undo                           btr0cur.cc L2597
      +-- lock_rec_insert_check_and_lock             lock0lock.cc L5050
            다음 레코드에 X|GAP|INSERT_INTENTION 으로 [06] -> 충돌이면 [07]  (L5106-L5122)

 DB_LOCK_WAIT 가 올라오면
 row_search_mvcc lock_table_wait:                    row0sel.cc L5927  mtr_commit (페이지 래치를 푼다)
      +-- row_mysql_handle_errors                    row0mysql.cc L653
            +-- [08] lock_wait_suspend_thread        row0mysql.cc L711
                  slot 을 잡고 os_event_wait 로 잠든다   lock0wait.cc L297
 ------------------------------------------------------------------
        스레드 경계 1 (slot->event 를 누가 set 하는가)
 ------------------------------------------------------------------
 스레드 B (잠금을 쥔 트랜잭션, 커밋이나 롤백)
 lock_trx_release_locks -> lock_rec_dequeue_from_page   lock0lock.cc L4151
      +-- lock_rec_grant -> [11] lock_rec_grant_by_heap_no   L2294
            기다리던 잠금을 부여하고 lock_grant -> os_event_set 으로 A 를 깨운다
 ------------------------------------------------------------------
        스레드 경계 2
 ------------------------------------------------------------------
 백그라운드 스레드 (srv0start.cc L1998 에서 생성)
 [09] lock_wait_timeout_thread                       lock0wait.cc L1432
      +-- 1 초마다 lock_wait_check_slots_for_timeouts    L1448  타임아웃이면 DB_LOCK_WAIT_TIMEOUT
      +-- 매번 lock_wait_update_schedule_and_check_for_deadlocks  L1451
            슬롯 스냅샷으로 wait-for 그래프를 만든다
            +-- [10] lock_wait_find_and_handle_deadlocks   L1425
                  순환을 찾아 희생자를 고른다
                  희생자 A 에 was_chosen_as_deadlock_victim, 잠금 취소, os_event_set
```

잠금 하나는 "페이지 하나 + 비트맵"이다. 같은 트랜잭션이 같은 페이지에 같은 모드로 잡는 잠금은 `lock_t` 하나를 공유하고 heap_no 비트만 켠다.

```text
 lock_t 의 모양 (lock0priv.h L137, 레코드 잠금일 때)

 +------------------+
 | trx              |  잠금을 가진 트랜잭션
 | trx_locks        |  trx 의 잠금 목록 노드 (커밋 때 이것을 따라 전부 푼다)
 | index            |
 | hash             |  lock_sys->rec_hash 버킷 체인 (키 = page_id)
 | rec_lock.page_id |
 | rec_lock.n_bits  |
 | type_mode        |  LOCK_S/X | LOCK_REC | GAP / REC_NOT_GAP / INSERT_INTENTION | WAIT
 +------------------+
 | bitmap n_bits    |  구조체 바로 뒤에 붙는다 (lock0priv.h L89-L90 주석)
 | 0 1 0 0 1 0 ...  |  켜진 비트 = 잠긴 레코드의 heap_no
 +------------------+

 한 레코드의 대기 큐 = rec_hash 에서 page_id 버킷을 훑으며 heap_no 비트가 켜진 lock_t 들
   부여된(granted) 잠금은 앞에 넣고 (lock_rec_insert_to_granted, prepend  L1213)
   기다리는(waiting) 잠금은 뒤에 붙인다 (lock_rec_insert_to_waiting, append L1200)
```

```text
 type_mode 비트 (lock0lock.h L949-L987)

 값     이름                    뜻
 0-4    LOCK_IS/IX/S/X/AUTO_INC 모드 (LOCK_MODE_MASK 0xF)
 16     LOCK_TABLE
 32     LOCK_REC
 256    LOCK_WAIT               아직 부여되지 않고 큐에서 기다리는 중
 0      LOCK_ORDINARY           next-key: 레코드 + 그 앞 gap
 512    LOCK_GAP                레코드 앞 gap 만
 1024   LOCK_REC_NOT_GAP        레코드만
 2048   LOCK_INSERT_INTENTION   gap 에 넣으려고 기다리는 표시 (LOCK_GAP 과 함께 쓴다)
```

이 비트들의 조합이 서로를 막는 규칙은 [06] 에 있다. 요약하면 gap 잠금끼리는 막지 않고, gap 잠금이 막는 것은 insert intention 뿐이다.

```text
 레코드 잠금 호환 행렬 요약 (모드가 S-X, X-S, X-X 로 충돌할 때, lock0lock.cc L564-L644)

 요청 \ 큐에 있는   GAP   REC_NOT_GAP   ORDINARY   INSERT_INTENTION
 GAP                .     .             .          .
 REC_NOT_GAP        .     W             W          .
 ORDINARY           .     W             W          .
 INSERT_INTENTION   W     .             W          .

 W = 기다린다. S 와 S 는 정밀 모드와 무관하게 언제나 통과한다
```

## 어디에서 쓰이는가

```text
 [일관 읽기(MVCC)]      잠금 읽기(FOR UPDATE, FOR SHARE)와 UPDATE/DELETE 의 행 찾기가
                        row_search_mvcc 에서 [01] 을 부른다. 일반 SELECT 는 잠금 없이 ReadView 로 읽는다
 [행 쓰기]              UPDATE/DELETE 가 고칠 행을 찾는 스캔이 여기를 지난다
 [B+Tree 삽입과 분할]   btr_cur_ins_lock_and_undo -> lock_rec_insert_check_and_lock 이 [06] [07] 을 쓴다
 [커밋과 binlog 2PC]    trx_release_impl_and_expl_locks -> lock_trx_release_locks (trx0trx.cc L1931)
                        이 잠금을 한꺼번에 풀고 [11] 로 기다리던 트랜잭션을 깨운다
```

앞 흐름은 [일관 읽기(MVCC)](../mvcc-read/README.md)와 [B+Tree 삽입과 분할](../btree-insert/README.md)이고, 잠금이 풀리는 시점은 [커밋과 binlog 2PC](../commit-2pc/README.md)에 있다. `lock_t` 와 `lock_sys` 를 한 자리에서 보는 그림은 [메모리 구조](../../structure/memory-structures/README.md)에 있다.

## db-engine 에서는

같은 문제(누가 무엇을 쥐었나, 충돌하면 어떻게 하나, 언제 푸나)를 db-engine 은 "테이블 이름 하나에 S/X, 충돌하면 즉시 예외"로 줄였다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 잠금 단위
   MySQL      레코드(heap_no) + gap. 페이지당 lock_t 하나에 비트맵
              테이블에는 IS/IX 의도 잠금을 먼저 건다 (lock_rec_lock 의 ut_ad L1869-L1872)
   db-engine  자원 이름 문자열(테이블 이름). holders: MutableMap<String, MutableList<Holder>>

 모드
   MySQL      S/X x (ORDINARY, GAP, REC_NOT_GAP, INSERT_INTENTION)
              gap 끼리는 충돌하지 않는다 (rec_lock_check_conflict L580)
   db-engine  Mode { SHARED, EXCLUSIVE }. 같은 tx 의 S -> X 업그레이드는 혼자일 때만

 충돌하면
   MySQL      LOCK_WAIT 잠금을 큐 뒤에 붙이고 잠든다
              교착은 백그라운드 스레드가 wait-for 그래프 순환으로 찾아 희생자를 고른다
   db-engine  acquire 가 LockConflict 를 던진다. 대기가 없으니 교착도 없다

 푸는 시점
   MySQL      커밋 때 trx_locks 목록을 따라 전부 (lock_trx_release_locks)
              풀면서 기다리던 잠금에 schedule_weight 순으로 부여
   db-engine  TransactionWithLock.commit / abort 가 releaseAll(txId)
```

db-engine impl 문서는 "대기를 넣는 순간 교착이 생기고 교착 탐지는 그 자체로 한 단계짜리 주제"라며 즉시 실패를 골랐고, 대기 모델에 필요한 것으로 타임아웃, 대기 그래프 순환 탐지, 잠금 순서 강제를 적어 두었다. InnoDB 는 앞의 둘을 모두 가진다([09] 의 한 스레드가 둘을 돌고, 순환 처리는 [10] 이다). 또 impl 문서가 행 단위 잠금의 한계로 든 "아직 존재하지 않는 행은 잠글 수 없다(팬텀)"를 InnoDB 는 gap 잠금과 insert intention 으로 푼다. 챕터: [09-01-lock-manager](../../../../../project/db-engine/09-01-lock-manager/), [09-02-transaction-lock-integration](../../../../../project/db-engine/09-02-transaction-lock-integration/).

## 단계

1. [sel_set_rec_lock](01_sel_set_rec_lock/README.md)이 잠금 읽기에서 인덱스 종류에 맞는 잠금 함수를 고른다.
2. [lock_clust_rec_read_check_and_lock](02_lock_clust_rec_read_check_and_lock/README.md)이 암묵 잠금을 명시 잠금으로 바꾸고 페이지 shard 를 잡는다.
3. [lock_rec_lock](03_lock_rec_lock/README.md)이 빠른 경로를 먼저 시도하고 실패하면 느린 경로로 간다.
4. [lock_rec_lock_fast](04_lock_rec_lock_fast/README.md)가 페이지에 잠금이 없거나 내 잠금 하나뿐인 경우를 처리한다.
5. [lock_rec_lock_slow](05_lock_rec_lock_slow/README.md)가 이미 가진 잠금, 충돌, 대기 여부를 판정한다.
6. [lock_rec_other_has_conflicting](06_lock_rec_other_has_conflicting/README.md)이 큐를 훑어 기다려야 할 잠금을 찾는다(호환 행렬).
7. [RecLock.add_to_waitq](07_RecLock.add_to_waitq/README.md)가 기다리는 잠금을 큐에 넣고 wait-for 간선을 만든다.
8. [lock_wait_suspend_thread](08_lock_wait_suspend_thread/README.md)가 사용자 스레드를 재우고, 깨어난 이유를 가른다.
9. [lock_wait_timeout_thread](09_lock_wait_timeout_thread/README.md)가 타임아웃을 처리하고 wait-for 그래프를 만든다.
10. [lock_wait_find_and_handle_deadlocks](10_lock_wait_find_and_handle_deadlocks/README.md)가 그래프의 순환을 찾아 희생자를 롤백시킨다.
11. [lock_rec_grant_by_heap_no](11_lock_rec_grant_by_heap_no/README.md)가 풀린 자리에 기다리던 잠금을 부여하고 깨운다.

INSERT 가 gap 을 검사하는 `lock_rec_insert_check_and_lock` 은 [B+Tree 삽입과 분할의 btr_cur_ins_lock_and_undo](../btree-insert/04_btr_cur_ins_lock_and_undo/README.md)에서 다룬다. 이 흐름의 [06] 과 [07] 을 그대로 부른다.

## 결과가 쓰이는 곳

```text
 DB_SUCCESS / DB_SUCCESS_LOCKED_REC
      --> row_search_mvcc 가 레코드를 돌려준다. LOCKED_REC 면 READ COMMITTED 에서
          조건에 안 맞는 행을 나중에 풀 수 있도록 new_rec_lock 에 표시한다 (row0sel.cc L5258-L5263)

 DB_LOCK_WAIT
      --> [08] 에서 잠들었다가 깨어나 lock_state 를 되돌리고 같은 자리부터 다시 찾는다

 DB_DEADLOCK
      --> row_mysql_handle_errors 가 trx_rollback_to_savepoint(trx, nullptr) 로
          트랜잭션 전체를 롤백한다 (row0mysql.cc L723-L729)

 DB_LOCK_WAIT_TIMEOUT
      --> innodb_rollback_on_timeout 이 아니면 문장만 롤백 (row0mysql.cc L672-L675)

 trx->lock.trx_locks
      --> 커밋 때 lock_trx_release_locks 가 이 목록을 뒤에서부터 따라가며 전부 푼다
```

## 다루지 않는 것

테이블 잠금(`lock_table`, IS/IX, AUTO_INC), 공간 인덱스의 predicate 잠금(`lock_prdt_*`, `sel_set_rtr_rec_lock`), 페이지 분할과 병합 때 잠금을 옮기는 `lock_update_split_right` 류와 gap 잠금 상속(`lock_rec_inherit_to_gap`), 보조 인덱스의 암묵 잠금 판정(`lock_sec_rec_some_has_impl`), high priority 트랜잭션(그룹 복제)과 `trx_kill_blocking`, READ COMMITTED 의 semi-consistent read 세부, `lock_sys` 의 전역 래치와 shard 래치 설계(`locksys::Latches`), `SHOW ENGINE INNODB STATUS` 의 교착 출력(`lock_notify_about_deadlock`), Performance Schema `data_locks` 는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 sel_set_rec_lock](01_sel_set_rec_lock/README.md)
- [02 lock_clust_rec_read_check_and_lock](02_lock_clust_rec_read_check_and_lock/README.md)
- [03 lock_rec_lock](03_lock_rec_lock/README.md)
- [04 lock_rec_lock_fast](04_lock_rec_lock_fast/README.md)
- [05 lock_rec_lock_slow](05_lock_rec_lock_slow/README.md)
- [06 lock_rec_other_has_conflicting](06_lock_rec_other_has_conflicting/README.md)
- [07 RecLock.add_to_waitq](07_RecLock.add_to_waitq/README.md)
- [08 lock_wait_suspend_thread](08_lock_wait_suspend_thread/README.md)
- [09 lock_wait_timeout_thread](09_lock_wait_timeout_thread/README.md)
- [10 lock_wait_find_and_handle_deadlocks](10_lock_wait_find_and_handle_deadlocks/README.md)
- [11 lock_rec_grant_by_heap_no](11_lock_rec_grant_by_heap_no/README.md)
