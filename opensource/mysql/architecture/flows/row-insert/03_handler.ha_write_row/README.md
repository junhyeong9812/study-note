# handler::ha_write_row

상위: [행 쓰기 (handler -> row0ins)](../README.md)

**서버 계층과 스토리지 엔진 사이의 문이다.** 모든 엔진에 공통인 앞뒤 처리를 하고, 가운데서 엔진이 구현한 가상 함수 `write_row` 를 부른다. 볼거리는 순서다. 트랜잭션에 "이 엔진이 썼다"는 표시를 먼저 남기고, 엔진이 성공한 뒤에만 binlog 행 이벤트를 만든다.

## 위치

`sql` / `handler.cc` L8198-L8224 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L8198-L8224))

## 실제 코드

`sql` / `handler.cc` L8198-L8224 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L8198-L8224))

```cpp
// handler.cc L8198-L8224
int handler::ha_write_row(uchar *buf) {
  int error;
  Log_func *log_func = Write_rows_log_event::binlog_row_logging_function;
  assert(table_share->tmp_table != NO_TMP_TABLE || m_lock_type == F_WRLCK);

  DBUG_TRACE;
  DBUG_EXECUTE_IF("inject_error_ha_write_row", return HA_ERR_INTERNAL_ERROR;);
  DBUG_EXECUTE_IF("simulate_storage_engine_out_of_memory",
                  return HA_ERR_SE_OUT_OF_MEMORY;);
  mark_trx_read_write();

  DBUG_EXECUTE_IF(
      "handler_crashed_table_on_usage",
      my_error(HA_ERR_CRASHED, MYF(ME_ERRORLOG), table_share->table_name.str);
      set_my_errno(HA_ERR_CRASHED); return HA_ERR_CRASHED;);

  MYSQL_TABLE_IO_WAIT(PSI_TABLE_WRITE_ROW, MAX_KEY, error,
                      { error = write_row(buf); })

  if (unlikely(error)) return error;

  if (unlikely((error = binlog_log_row(table, nullptr, buf, log_func))))
    return error; /* purecov: inspected */

  DEBUG_SYNC_C("ha_write_row_end");
  return 0;
}
```

엔진이 트랜잭션에 참여 중이면 그 참여 정보에 읽기-쓰기 표시를 단다.

`sql` / `handler.cc` L4865-L4885 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/sql/handler.cc#L4865-L4885))

```cpp
// handler.cc L4865-L4885
void handler::mark_trx_read_write() {
  Ha_trx_info *ha_info = &ha_thd()->get_ha_data(ht->slot)->ha_info[0];
  /*
    When a storage engine method is called, the transaction must
    have been started, unless it's a DDL call, for which the
    storage engine starts the transaction internally, and commits
    it internally, without registering in the ha_list.
    Unfortunately here we can't know for sure if the engine
    has registered the transaction or not, so we must check.
  */
  if (ha_info->is_started()) {
    assert(has_transactions());
    /*
      table_share can be NULL in ha_delete_table(). See implementation
      of standalone function ha_delete_table() in sql_base.cc.
    */
    if (table_share == nullptr || table_share->tmp_table == NO_TMP_TABLE) {
      /* TempTable and Heap tables don't use/support transactions. */
      ha_info->set_trx_read_write();
    }
  }
```

## 동작 흐름

```text
 L8200  log_func = Write_rows_log_event::binlog_row_logging_function
 L8201  임시 테이블이 아니면 쓰기 잠금(F_WRLCK) 상태여야 한다 (assert)
 L8207  mark_trx_read_write()
          L4875  이 엔진이 트랜잭션에 등록되어 있으면 (external_lock 에서 등록)
          L4883  ha_info->set_trx_read_write()
 L8214  MYSQL_TABLE_IO_WAIT(PSI_TABLE_WRITE_ROW, ...)
 L8215    error = write_row(buf)                --> [04] ha_innobase::write_row
 L8217  실패면 그대로 돌려준다. binlog 에는 아무것도 남지 않는다
 L8219  binlog_log_row(table, nullptr, buf, log_func)
          L8061  행 기반 binlog 대상 테이블일 때만
          L8090  add_pke          트랜잭션 write set 에 키 해시 추가
          L8109  write_locked_table_maps   문장의 첫 행이면 Table_map 이벤트부터
          L8120  (*log_func)(...)  Write_rows 이벤트에 이 행을 붙인다
 L8223  return 0
```

`set_trx_read_write` 로 단 표시는 커밋 때 다시 읽힌다. 커밋 쪽은 읽기-쓰기 표시가 붙은 엔진 수를 세어 두 단계 커밋이 필요한지 판단한다.

```text
 표시를 다는 곳과 읽는 곳 (sql/handler.cc)

 L4883  mark_trx_read_write      ha_write_row, ha_update_row, ha_delete_row 앞에서
 L1459  ha_check_and_coalesce_trx_read_only
          is_trx_read_write() 인 엔진마다 ++rw_ha_count
 L1804  ha_commit_trans 가 rw_ha_count 를 받는다       --> [커밋과 binlog 2PC]
```

## 결과가 쓰이는 곳

```text
 write_row 의 반환값 (HA_ERR_*)
      --> [02] write_record 가 중복 키면 REPLACE / UPDATE 로, 아니면 print_error

 Ha_trx_info 의 read-write 표시
      --> [커밋과 binlog 2PC] 의 ha_commit_trans 가 두 단계 커밋 여부를 정한다

 binlog 캐시의 Write_rows 이벤트
      --> 커밋 때 binlog 파일로 flush 된다
```

## 다루지 않는 것

Performance Schema 테이블 I/O 계측(`MYSQL_TABLE_IO_WAIT`), `binlog_row_image`, write set 추출(`add_pke`)과 그룹 복제의 충돌 검사, `Write_rows_log_event` 의 형식은 이 흐름 밖이다.
