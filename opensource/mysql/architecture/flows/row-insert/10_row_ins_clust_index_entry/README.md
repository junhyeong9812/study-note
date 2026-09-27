# row_ins_clust_index_entry

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**클러스터드 인덱스에 엔트리를 넣는 두 번의 시도를 감싼다.** 먼저 리프 페이지 하나만 X 래치로 잡는 `BTR_MODIFY_LEAF` 로 해 보고, 그 페이지에 자리가 없어 `DB_FAIL` 이 오면 트리 전체에 SX 래치를 잡는 `BTR_MODIFY_TREE` 로 다시 한다. 두 시도 앞에 각각 `log_free_check()` 가 있다. 이 함수에서 흐름은 [B+Tree 삽입과 분할](../../btree-insert/README.md)의 `row_ins_clust_index_entry_low` 로 넘어간다.

## 위치

`storage` / `innobase` / `row` / `row0ins.cc` L3119-L3197 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3119-L3197))

## 실제 코드

`storage` / `innobase` / `row` / `row0ins.cc` L3119-L3197 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L3119-L3197))

```cpp
// row0ins.cc L3119-L3197
dberr_t row_ins_clust_index_entry(
    dict_index_t *index, /*!< in: clustered index */
    dtuple_t *entry,     /*!< in/out: index entry to insert */
    que_thr_t *thr,      /*!< in: query thread */
    bool dup_chk_only)
/*!< in: if true, just do duplicate check
and return. don't execute actual insert. */
{
  dberr_t err;
  ulint n_uniq;

  DBUG_TRACE;

  if (!thd_is_sql_fk_checks_enabled() && !index->table->foreign_set.empty()) {
    DBUG_PRINT("fk", ("InnoDB FK on table %s", index->table->name.m_name));
    err = row_ins_check_foreign_constraints(index->table, index, entry, thr);
    if (err != DB_SUCCESS) {
      return err;
    }
  }

  n_uniq = dict_index_is_unique(index) ? index->n_uniq : 0;

  /* Try first optimistic descent to the B-tree */
  uint32_t flags;

  if (!index->table->is_intrinsic()) {
    log_free_check();
    flags = index->table->is_temporary() ? BTR_NO_LOCKING_FLAG : 0;

    /* For intermediate table of copy alter operation,
    skip undo logging and record lock checking for
    insertion operation. */
    if (index->table->skip_alter_undo) {
      flags |= BTR_NO_UNDO_LOG_FLAG | BTR_NO_LOCKING_FLAG;
    }

  } else {
    flags = BTR_NO_LOCKING_FLAG | BTR_NO_UNDO_LOG_FLAG;
  }

  if (index->table->is_intrinsic() && dict_index_is_auto_gen_clust(index)) {
    /* Check if the memory allocated for intrinsic cache*/
    if (!index->last_ins_cur) {
      dict_allocate_mem_intrinsic_cache(index);
    }
    err = row_ins_sorted_clust_index_entry(BTR_MODIFY_LEAF, index, entry, thr);
  } else {
    err = row_ins_clust_index_entry_low(flags, BTR_MODIFY_LEAF, index, n_uniq,
                                        entry, thr, dup_chk_only);
  }

  DEBUG_SYNC(thr_get_trx(thr)->mysql_thd,
             "after_row_ins_clust_index_entry_leaf");

  if (err != DB_FAIL) {
    DEBUG_SYNC_C("row_ins_clust_index_entry_leaf_after");
    return err;
  }

  /* Try then pessimistic descent to the B-tree */
  if (!index->table->is_intrinsic()) {
    log_free_check();
  } else if (!index->last_sel_cur) {
    dict_allocate_mem_intrinsic_cache(index);
    index->last_sel_cur->invalid = true;
  } else {
    index->last_sel_cur->invalid = true;
  }

  if (index->table->is_intrinsic() && dict_index_is_auto_gen_clust(index)) {
    err = row_ins_sorted_clust_index_entry(BTR_MODIFY_TREE, index, entry, thr);
  } else {
    err = row_ins_clust_index_entry_low(flags, BTR_MODIFY_TREE, index, n_uniq,
                                        entry, thr, dup_chk_only);
  }

  return err;
}
```

두 시도 앞의 `log_free_check()` 가 왜 여기 있어야 하는지는 파일 머리의 주석이 말한다.

`storage` / `innobase` / `row` / `row0ins.cc` L69-L77 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/row/row0ins.cc#L69-L77))

```cpp
// row0ins.cc L69-L77
/*************************************************************************
IMPORTANT NOTE: Any operation that generates redo MUST check that there
is enough space in the redo log before for that operation. This is
done by calling log_free_check(). The reason for checking the
availability of the redo log space before the start of the operation is
that we MUST not hold any synchronization objects when performing the
check.
If you make a change in this module make sure that no codepath is
introduced where a call to log_free_check() is bypassed. */
```

## 동작 흐름

```text
 L3132  SQL 계층 FK 검사를 쓰지 않고 테이블에 FK 가 있으면
 L3134    row_ins_check_foreign_constraints     InnoDB 가 부모 행 존재를 검사
 L3140  n_uniq = 유니크면 index->n_uniq, 아니면 0     0 이면 중복 검사를 안 한다

 L3145  보통 테이블
 L3146    log_free_check()                       래치를 잡기 전에 redo 여유를 확인
 L3147    임시 테이블이면 BTR_NO_LOCKING_FLAG
 L3152    복사식 ALTER 의 중간 테이블이면 undo 도 잠금도 생략
 L3157  내부 임시 테이블이면 잠금과 undo 를 모두 생략

 1차   L3167  row_ins_clust_index_entry_low(flags, BTR_MODIFY_LEAF, ...)   --> [B+Tree 01]
 L3174  err != DB_FAIL 이면 그대로 반환         성공, 중복, 잠금 대기 모두 여기서 끝
 L3181  log_free_check()                         두 번째 mtr 전에 다시
 2차   L3192  row_ins_clust_index_entry_low(flags, BTR_MODIFY_TREE, ...)   --> [B+Tree 01]
 L3196  return err
```

두 시도는 서로 다른 mini-transaction 이다. 1차의 mtr 은 `DB_FAIL` 을 돌려주기 전에 이미 커밋되어 래치를 모두 놓았고, 2차는 루트부터 다시 내려간다.

```text
 LEAF 시도와 TREE 시도 (한 엔트리 기준)

 index->lock
   LEAF  S. 리프에 닿으면 놓는다 (btr0cur.cc L865, L1149)
   TREE  SX (btr0cur.cc L832). 분할에서 삽입이 들어갈 자리가 확실하면 일찍 놓는다 (btr0btr.cc L2500)
 리프 래치
   LEAF  X, 리프 하나. 리프를 읽을 때 바로 X 로 잡는다 (btr0cur.cc L943)
   TREE  X, 왼쪽 형제, 리프, 오른쪽 형제. 리프를 래치 없이 읽은 뒤 btr_cur_latch_leaves 로 (L1135, L221-L282)
 할 수 있는 것
   LEAF  페이지 안 삽입과 페이지 재구성
   TREE  페이지 분할, 루트 승격, 부모에 노드 포인터 추가
 실패 신호
   LEAF  DB_FAIL (자리 부족) -> 2차로
   TREE  DB_OUT_OF_FILE_SPACE 같은 진짜 오류
 mtr
   두 시도가 각자 새로 시작하고 각자 커밋한다

 래치 모드별 동작은 btr_cur_search_to_nth_level (btr0cur.cc L619) 에서 갈린다
 --> [B+Tree 삽입과 분할] 02
```

```text
 flags 가 정해지는 경우 (L3143-L3158)

 0                                            보통 테이블. 잠금 검사와 undo 를 모두 한다
 BTR_NO_LOCKING_FLAG                          임시 테이블. 잠금 검사를 생략한다
 BTR_NO_UNDO_LOG_FLAG | BTR_NO_LOCKING_FLAG   복사식 ALTER 의 중간 테이블. undo 와 잠금을 생략한다
 BTR_NO_LOCKING_FLAG | BTR_NO_UNDO_LOG_FLAG   내부 임시 테이블. 같은 생략. PK 없으면 경로도 따로 (L3160, L3165)
```

## 결과가 쓰이는 곳

```text
 반환값
      DB_SUCCESS       --> [08] 이 다음 인덱스(첫 세컨더리)로 간다
      DB_DUPLICATE_KEY --> [08] 이 error_index 를 적고 [06] 이 이 행을 savepoint 로 되돌린다
      DB_LOCK_WAIT     --> [06] 이 잠든 뒤 run_again, [08] 이 이 인덱스부터 다시

 flags
      --> [B+Tree 삽입과 분할] 04 btr_cur_ins_lock_and_undo 가 잠금 검사와 undo 기록 여부를 이것으로 정한다
```

## 다루지 않는 것

InnoDB 의 FK 검사(`row_ins_check_foreign_constraints`), 내부 임시 테이블의 정렬 삽입 캐시(`row_ins_sorted_clust_index_entry`, `last_ins_cur`), `log_free_check` 의 대기 조건은 곁가지다. redo 여유 확인은 [mini-transaction과 redo 기록](../../mtr-redo/README.md)의 몫이다.
