# lock_clust_rec_read_check_and_lock

상위: [레코드 잠금과 교착](../README.md)

**잠금을 요청하기 전에 "보이지 않는 잠금"을 먼저 드러낸다.** InnoDB 에서 레코드를 고친 트랜잭션은 잠금 구조체를 만들지 않고 레코드의 `DB_TRX_ID` 만으로 X 잠금을 가진 것으로 친다(암묵 잠금). 다른 트랜잭션이 그 레코드를 잠그려 할 때 이 함수가 암묵 잠금을 명시 잠금 `lock_t` 로 바꿔 큐에 올려야, 뒤에서 충돌 판정과 대기가 가능해진다. 그 다음 페이지 shard 래치를 잡고 [03] 을 부른다.

## 위치

@@loc storage/innobase/lock/lock0lock.cc 5420 5470@@

## 실제 코드

@@code storage/innobase/lock/lock0lock.cc 5420 5470@@

암묵 잠금의 주인을 찾는 쪽이다. 클러스터드 인덱스는 레코드의 trx_id 가 아직 활성인지 본다.

@@code storage/innobase/lock/lock0lock.cc 5212 5252@@

주인이 아직 살아 있고 명시 잠금이 없으면 그 트랜잭션 이름으로 `X | REC_NOT_GAP` 잠금을 만든다.

@@code storage/innobase/lock/lock0lock.cc 5194 5202@@

## 동작 흐름

```text
 L5434  읽기 전용 모드이거나 임시 테이블이면 잠그지 않는다
 L5438  heap_no = page_rec_get_heap_no(rec)     잠금 비트맵의 인덱스가 된다
 L5440  supremum 이 아니면
 L5441    lock_rec_convert_impl_to_expl
            L5226  trx_id = 레코드의 DB_TRX_ID
            L5228  trx_rw_is_active(trx_id, true)   활성이면 참조 카운트를 올려 돌려준다
            L5249  lock_rec_convert_impl_to_expl_for_trx
                     L5196  COMMITTED_IN_MEMORY 가 아니고 명시 X 잠금도 없으면
                     L5201  lock_rec_add_to_queue(LOCK_REC|LOCK_X|LOCK_REC_NOT_GAP, ..., 주인 trx)
                     L5207  참조 카운트를 내린다
 L5446  Shard_latch_guard(page_id)              이 페이지가 속한 lock_sys shard 만 잠근다
 L5448  AT_LEAST_STATEMENT 면 문장 끝까지 풀지 않도록 표시
 L5457  [03] lock_rec_lock(false, sel_mode, mode | gap_mode, ...)
 L5461  (블록 끝) shard 래치 해제
```

아래는 두 트랜잭션이 같은 행을 두고 만나는 순간이다. 명시 잠금으로 바뀌는 것은 B 가 요청할 때이고, A 는 그 사이 아무것도 하지 않는다.

```text
 암묵 잠금이 명시 잠금으로 바뀌는 시간축

 트랜잭션 A                           트랜잭션 B
 UPDATE t SET v=1 WHERE id=5
   레코드의 DB_TRX_ID = A
   lock_t 는 만들지 않는다
   (큐: 비어 있음)
                                      SELECT ... WHERE id=5 FOR UPDATE
                                        [02] L5441 convert_impl_to_expl
                                          A 가 활성 -> A 이름으로 X|REC_NOT_GAP 생성
                                          (큐: A X|REC_NOT_GAP granted)
                                        [03] lock_rec_lock(X|REC_NOT_GAP)
                                          A 와 충돌 -> B 의 X WAIT 를 큐 뒤에
                                          (큐: A granted, B waiting)
                                        --> [09] 잠든다
 COMMIT
   lock_trx_release_locks 가 A 의 lock_t 를 치운다
   --> [11] B 에 부여, B 를 깨운다
```

```text
 참조 카운트가 막는 것 (L5164, L5207)

 trx_rw_is_active(trx_id, true) 가 A 를 돌려준 순간부터
 lock_rec_convert_impl_to_expl_for_trx 가 끝날 때까지 A 는 참조 중이다
 A 의 커밋은 lock_trx_release_locks 에서 참조가 0 이 될 때까지 돈다 (lock0lock.cc L5824-L5834)
 그래서 "A 가 활성인 것을 봤는데 잠금을 만드는 사이 A 가 사라지는" 일이 없다
```

## 결과가 쓰이는 곳

```text
 명시 잠금으로 바뀐 A 의 lock_t
      --> [06] 이 B 의 요청과 충돌을 판정할 대상이 된다
      --> [10] 의 wait-for 그래프에서 B -> A 간선의 끝이 된다
 반환값
      --> [01] sel_set_rec_lock 을 거쳐 row_search_mvcc 로 그대로 올라간다
```

## 다루지 않는 것

보조 인덱스의 암묵 잠금 판정(`lock_sec_rec_some_has_impl`, 페이지의 `PAGE_MAX_TRX_ID` 와 클러스터드 레코드 버전 대조), `lock_duration_t::AT_LEAST_STATEMENT` 를 쓰는 경로, 레코드를 고치는 쪽의 검사 `lock_clust_rec_modify_check_and_lock`(L5295 에서 `impl=true` 로 [03] 을 부른다)은 곁가지라 요약만 했다.
