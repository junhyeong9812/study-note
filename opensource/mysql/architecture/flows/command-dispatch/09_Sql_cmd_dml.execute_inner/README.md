# Sql_cmd_dml::execute_inner

상위: [명령 디스패치](../README.md)

**잠금이 끝난 문장을 최적화하고, 실행 계획을 반복자(iterator) 트리로 만들고, 그것을 돌리는 기본 구현이다.** SELECT 가 이 구현을 그대로 쓰고, INSERT VALUES, UPDATE, DELETE 는 각자 이 가상 함수를 덮어쓴다. 이 흐름은 여기서 끝나고, 반복자가 부르는 `handler` 호출부터는 [행 쓰기](../../row-insert/README.md)와 [일관 읽기(MVCC)](../../mvcc-read/README.md)의 몫이다.

## 위치

`sql` / `sql_select.cc` L1123-L1159 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L1123-L1159))

## 실제 코드

`sql` / `sql_select.cc` L1115-L1159 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_select.cc#L1115-L1159))

```cpp
// sql_select.cc L1115-L1159
  Execute a DML statement.
  This is the default implementation for a DML statement and uses a
  nested-loop join processor per outer-most query block.
  The implementation is split in two: One for query expressions containing
  a single query block and one for query expressions containing multiple
  query blocks combined with UNION.
*/

bool Sql_cmd_dml::execute_inner(THD *thd) {
  Query_expression *unit = lex->unit;

  if (unit->optimize(thd, /*materialize_destination=*/nullptr,
                     /*finalize_access_paths=*/true))
    return true;

  DBUG_EXECUTE_IF("ast", { unit->DebugPrintQueryPlan(thd, "ast"); });

  // Perform secondary engine optimizations, if needed.
  if (optimize_secondary_engine(thd)) return true;

  // Create iterators for the chosen query plan before execution.
  if (unit->create_iterators(thd)) return true;

  // We know by now that execution will complete (successful or with error)
  lex->set_exec_completed();
  if (lex->is_explain()) {
    for (Table_ref *ref = lex->query_tables; ref != nullptr;
         ref = ref->next_global) {
      if (ref->table != nullptr && ref->table->file != nullptr) {
        handlerton *hton = ref->table->file->ht;
        if (hton->external_engine_explain_check != nullptr) {
          if (hton->external_engine_explain_check(thd)) return true;
        }
      }
    }

    if (explain_query(thd, thd, unit)) return true; /* purecov: inspected */
  } else {
    if (unit->execute(thd)) return true;

    notify_plugins_after_select(thd, lex->m_sql_cmd);
  }

  return false;
}
```

덮어쓰는 문장들의 선언이다.

`sql` / `sql_cmd_dml.h` L199-L199 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_cmd_dml.h#L199-L199))

```cpp
// sql_cmd_dml.h L199-L199
  virtual bool execute_inner(THD *thd);
```

`sql` / `sql_insert.h` L336-L336 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_insert.h#L336-L336))

```cpp
// sql_insert.h L336-L336
  bool execute_inner(THD *thd) override;
```

`sql` / `sql_update.h` L145-L145 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_update.h#L145-L145))

```cpp
// sql_update.h L145-L145
  bool execute_inner(THD *thd) override;
```

`sql` / `sql_delete.h` L57-L57 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/sql_delete.h#L57-L57))

```cpp
// sql_delete.h L57-L57
  bool execute_inner(THD *thd) override;
```

## 동작 흐름

```text
 L1126  unit->optimize(thd, nullptr, finalize_access_paths=true)
          조인 순서, 접근 경로(AccessPath) 선택. 실패면 return true
 L1133  optimize_secondary_engine               보조 엔진으로 보낼 문장이면
 L1136  unit->create_iterators(thd)             AccessPath -> RowIterator 트리
 L1139  lex->set_exec_completed                 이제부터 성공이든 실패든 실행이 끝까지 간다 (주석 L1138)
 L1140  EXPLAIN 이면
 L1151    explain_query                         계획만 보여 주고 행은 읽지 않는다
 L1152  아니면
 L1153    unit->execute(thd)                    반복자를 Read() 로 돌리며 행을 보낸다
 L1155    notify_plugins_after_select
```

반복자 트리의 잎이 handler 를 부르는 자리다. 어떤 접근 경로를 골랐느냐에 따라 InnoDB 에 들어가는 입구가 다르다.

```text
 SELECT 의 반복자와 handler 입구 (예: SELECT * FROM t WHERE k = 5, k 는 unique 가 아닌 인덱스)

 unit->execute
   +-- 결과를 클라이언트로 보내는 루프
         +-- RowIterator::Read() -> DoRead()
               +-- TableScanIterator::DoRead        basic_row_iterators.cc L276   전체 스캔
               |     -> handler::ha_rnd_next                                L279
               +-- RefIterator<false>::DoRead       ref_row_iterators.cc L358     인덱스 조회
                     -> handler::ha_index_read_map                          L381
                     -> ha_innobase::index_read
                     --> [일관 읽기(MVCC)] row_search_mvcc

 INSERT VALUES 는 이 함수를 쓰지 않는다
   Sql_cmd_insert_values::execute_inner (sql_insert.cc L482) -> write_record -> handler::ha_write_row
   --> [행 쓰기]

 기본 키 등호 조회(WHERE id = 5)는 const 테이블이 되어 반복자 실행 전
   최적화 단계의 join_read_const_table (sql_executor.cc L3703) 에서 미리 읽힌다
```

## 결과가 쓰이는 곳

```text
 unit->execute 의 결과 행
      --> Query_result (보통 Query_result_send) 가 클라이언트로 행 패킷을 보낸다
 set_exec_completed
      --> [02] 의 보조 엔진 재시도(check_secondary_engine_statement, sql_parse.cc L1585)가
          실행이 시작된 문장은 결과를 이미 보냈을 수 있어 다시 돌리지 않는다
 행 단위 handler 호출
      --> [일관 읽기(MVCC)] ha_innobase::index_read (ha_innodb.cc L10430)
      --> [행 쓰기] ha_innobase::write_row (ha_innodb.cc L9256)
```

## 다루지 않는 것

옵티마이저(`Query_expression::optimize`, `JOIN::optimize`, hypergraph 옵티마이저), `AccessPath` 와 `create_iterators` 의 변환 규칙, 반복자 종류별 구현, 보조 엔진 최적화, EXPLAIN 출력은 이 지도 범위(InnoDB 와 만나는 자리까지) 밖이라 이름만 적었다.
