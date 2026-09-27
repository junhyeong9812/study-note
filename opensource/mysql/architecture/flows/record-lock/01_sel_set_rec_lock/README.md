# sel_set_rec_lock

상위: [레코드 잠금과 교착](../README.md)

**잠금 읽기가 잠금 계층으로 들어가는 문이다.** `row_search_mvcc` 가 "이 레코드에 어떤 종류(next-key, 레코드만, gap 만)를 걸지" 정해서 넘기면, 이 함수는 인덱스 종류(클러스터드, 보조, 공간)에 맞는 잠금 함수를 고른다. 볼거리는 호출하는 쪽에서 `lock_type` 을 고르는 규칙과, 잠금 개수가 너무 많을 때의 비상 탈출이다.

## 위치

@@loc storage/innobase/row/row0sel.cc 1138 1180@@

## 실제 코드

@@code storage/innobase/row/row0sel.cc 1138 1180@@

호출하는 쪽이다. 레코드가 검색 범위에 들 수 있는지, 레코드 앞 gap 이 범위와 겹치는지 두 질문으로 잠금 종류를 정한다.

@@code storage/innobase/row/row0sel.cc 5226 5254@@

잠금을 기다려야 하면 `row_search_mvcc` 는 mtr 를 커밋해 페이지 래치를 놓은 뒤에 재운다.

@@code storage/innobase/row/row0sel.cc 5926 5944@@

## 동작 흐름

```text
 L1152  trx->lock.trx_locks 가 10000 개를 넘고
 L1153    버퍼 풀이 모자라면 (buf_LRU_buf_pool_running_out)
 L1154    DB_LOCK_TABLE_FULL          잠금 구조체도 버퍼 풀 메모리를 쓰기 때문
                                      --> row_mysql_handle_errors 가 트랜잭션 전체 롤백

 L1158  클러스터드 인덱스   -> [02] lock_clust_rec_read_check_and_lock
 L1163  공간 인덱스         -> GAP / ORDINARY 를 요청하면 오류 (L1164)
                               sel_set_rtr_rec_lock (predicate 잠금, 이 흐름 밖)
 L1172  보조 인덱스         -> lock_sec_rec_read_check_and_lock (lock0lock.cc L5371)
                               [02] 와 같은 모양이고 마지막에 lock_rec_lock 을 부른다
```

`mode` 는 `prebuilt->select_lock_type` 이다. `FOR SHARE` 면 `LOCK_S`, `FOR UPDATE` 와 UPDATE/DELETE 의 스캔이면 `LOCK_X` 가 온다. `type` 은 아래 표로 정해진다.

```text
 row_search_mvcc 가 lock_type 을 고르는 표 (row0sel.cc L5231-L5245)

 row_can_be_in_range  gap_can_intersect_range  lock_type
 true                 true                     LOCK_ORDINARY     next-key
 true                 false                    LOCK_REC_NOT_GAP  레코드만
 false                true                     LOCK_GAP          gap 만
 false                false                    잠그지 않고 DB_RECORD_NOT_FOUND

 예) id 가 유일 키이고 WHERE id = 5 로 정확히 찾으면 gap 이 범위와 안 겹친다
       -> 레코드만 잠근다
     WHERE id BETWEEN 5 AND 9 로 훑으면 레코드와 그 앞 gap 을 같이 잠근다
       -> 범위를 벗어난 첫 레코드에는 gap 만 남는다
```

```text
 sel_mode (L1253)

 prebuilt->select_mode        SKIP LOCKED / NOWAIT / 보통
 semi-consistent 읽기이면     SELECT_SKIP_LOCKED 로 바꿔 넘긴다 (L5248-L5253)
                              기다리지 않고 마지막 커밋 버전을 읽으려고
                              (READ COMMITTED 의 UPDATE 스캔, 클러스터드, 유일 검색 아님)
```

```text
 반환값을 받은 뒤 (row0sel.cc L5256 이후)

 DB_SUCCESS_LOCKED_REC  새 잠금을 만들었다. RC 에서는 new_rec_lock 표시 -> 조건 불일치면 나중에 푼다
 DB_SUCCESS             이미 가진 잠금으로 충분했다
 DB_SKIP_LOCKED         SKIP LOCKED 면 다음 레코드로, semi-consistent 면 커밋된 옛 버전을 만든다
 DB_LOCK_WAIT           lock_wait_or_error -> L5927 mtr_commit -> L5940 row_mysql_handle_errors
                        --> [09] 에서 잠든다
```

## 결과가 쓰이는 곳

```text
 반환값
      --> row_search_mvcc 의 switch 가 레코드를 쓸지, 건너뛸지, 기다릴지 정한다
 DB_LOCK_WAIT
      --> 페이지 래치를 놓은 상태로 잠든다. 깨어나면 저장한 커서 위치로 복원해 다시 찾는다
```

## 다루지 않는 것

`row_compare_row_to_range` 의 범위 판정 세부, `set_also_gap_locks` 와 격리 수준에 따른 gap 생략(`trx->skip_gap_locks`), semi-consistent read 의 옛 버전 구성(`row_sel_build_committed_vers_for_mysql`), 공간 인덱스의 `sel_set_rtr_rec_lock`, 커서 복원(`sel_restore_position_for_mysql`)은 이 흐름의 곁가지라 요약만 했다. 잠금 없는 읽기는 [일관 읽기(MVCC)](../../mvcc-read/README.md)에서 다룬다.
