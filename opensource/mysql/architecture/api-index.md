# API 역인덱스

상위: [MySQL 아키텍처 지도](README.md)

"이 SQL 문·시스템 변수를 쓰면 어느 흐름들을 지나는가"를 뒤에서부터 찾는 표다. 흐름 문서가 함수에서 출발한다면 이 표는 **SQL 문과 시스템 변수 이름에서 출발한다.**

기준 태그: `mysql-9.7.2` [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 경로는 `sql/` 로 시작하지 않으면 `storage/innobase/` 아래다.

## 범위를 먼저 밝힌다

```text
 이 표는 SQLCOM_ 명령과 시스템 변수를 전부 담지 않는다
 흐름 열두 편이 실제로 덮는 길만 적었다

 안 덮는 API 도 아래에 따로 적어 두었다 - 없는 것을 있는 척하지 않으려고
```

## 모든 SQL 이 공유하는 앞단

```text
 클라이언트 패킷
   |
   v
 [연결과 스레드]   handle_connection -> do_command (sql_parse.cc L1347)
   v
 [명령 디스패치]   dispatch_command (L1752), COM_QUERY (L2095)
   |  dispatch_sql_command (L5307) -> parse_sql (L7208)
   |  -> mysql_execute_command (L3031) 의 switch (lex->sql_command) (L3486)
   v
 대부분의 DML 과 DDL 은 lex->m_sql_cmd->execute(thd) 로 넘어가
 거기서부터 명령마다 갈린다
```

## 읽기와 쓰기 (DML)

case 줄은 모두 `sql/sql_parse.cc` 기준이다.

| SQL | case 줄 | 다음 단계 | 뒤이어 지나는 흐름 |
|---|---|---|---|
| `SELECT` | L4697 | `Sql_cmd_dml::execute` (sql_select.cc L685) | 명령 디스패치 -> 일관 읽기(MVCC) -> 버퍼 풀. `FOR UPDATE`/`FOR SHARE` 면 + 레코드 잠금 |
| `INSERT` / `REPLACE` | L3788 / L3787 | `Sql_cmd_insert_values::execute_inner` (sql_insert.cc L482) | 행 쓰기 -> B+Tree 삽입과 분할 -> mini-transaction과 redo 기록 |
| `UPDATE` | L3793 | `ha_innobase::update_row` (handler/ha_innodb.cc L10010) -> `row_update_for_mysql` (row/row0mysql.cc L2436) | 행 쓰기(update 변형) -> 레코드 잠금 -> redo. undo 는 MVCC 와 purge 의 재료 |
| `DELETE` | L3791 | `ha_innobase::delete_row` (handler/ha_innodb.cc L10168) | 레코드 잠금 -> redo -> purge (delete-mark 만 하고 실제 제거는 purge) |

```text
 DELETE 는 지우지 않는다

 ha_innobase::delete_row 도 row_update_for_mysql 을 부른다 (ha_innodb.cc L10205)
 레코드에 delete-mark 만 찍고, 진짜로 빼는 것은 나중에 [purge] 다
 다른 트랜잭션의 read view 가 아직 그 행을 봐야 할 수 있기 때문이다
```

## 트랜잭션

| SQL | case 줄 | 다음 단계 | 뒤이어 지나는 흐름 |
|---|---|---|---|
| `BEGIN` | L4337 | `trans_begin` (sql/transaction.cc L125) | 커밋과 binlog 2PC (시작 쪽). `WITH CONSISTENT SNAPSHOT` 이면 일관 읽기(read view 를 바로 연다) |
| `COMMIT` | L4341 | `trans_commit` (transaction.cc L233) -> `ha_commit_trans` (sql/handler.cc L1686) | 커밋과 binlog 2PC -> mini-transaction과 redo 기록(`log_write_up_to`) -> purge |
| `XA PREPARE` / `XA COMMIT` | L4687 / L4688 | `Sql_cmd_xa_*` | 커밋과 binlog 2PC |
| `LOCK TABLES` | L3932 | `lock_tables` -> `external_lock` | 명령 디스패치 -> 레코드 잠금(테이블 잠금 `lock_table` lock/lock0lock.cc L3534) |

```text
 binlog 를 켜면 커밋은 두 번 기록된다

 ha_commit_trans
   tc_log->prepare   InnoDB 가 prepared 상태로 redo 를 남긴다
   tc_log->commit    ordered_commit
                       FLUSH  binlog 캐시를 파일로
                       SYNC   sync_binlog 에 따라 fsync
                       COMMIT InnoDB 커밋 (trx_commit_low)
 크래시가 prepared 와 COMMIT 사이에서 나면
   [크래시 복구] 의 Binlog_recovery 가 binlog 에 XID 가 있는지로 커밋/롤백을 정한다
```

## DDL

| SQL | case 줄 | 다음 단계 | 뒤이어 지나는 흐름 |
|---|---|---|---|
| `ALTER TABLE` | L4668 | `Sql_cmd_alter_table::execute` (sql/sql_alter.cc L220) -> `mysql_inplace_alter_table` (sql/sql_table.cc L14394) | 온라인 DDL(열세 번째 후보) -> redo |
| `CREATE INDEX` / `DROP INDEX` | L3796 / L3797 | `mysql_alter_table` 로 합류 | 〃 |

## 시스템 변수

InnoDB 변수는 `handler/ha_innodb.cc`, 서버 변수는 `sql/sys_vars.cc` 에 정의가 있다. 줄은 `MYSQL_SYSVAR_*` / `Sys_var_*` 정의가 시작하는 줄이다.

| 변수 | 정의 | 흐름 |
|---|---|---|
| `innodb_buffer_pool_size` | ha_innodb.cc L22544 | 버퍼 풀 페이지 획득 |
| `innodb_buffer_pool_instances` | ha_innodb.cc L22615 | 버퍼 풀 페이지 획득 |
| `innodb_flush_log_at_trx_commit` | ha_innodb.cc L22364 (읽는 자리 trx/trx0trx.cc L1735) | 커밋과 binlog 2PC -> redo |
| `innodb_flush_method` | ha_innodb.cc L22371 | redo, 플러시 |
| `innodb_log_buffer_size` | ha_innodb.cc L22835 | mini-transaction과 redo 기록 |
| `innodb_redo_log_capacity` | ha_innodb.cc L22842 | redo, 체크포인트 |
| `innodb_doublewrite` | ha_innodb.cc L22584 | 플러시·doublewrite, 크래시 복구 |
| `innodb_io_capacity` | ha_innodb.cc L22253 | 플러시 |
| `innodb_page_cleaners` | ha_innodb.cc L22388 | 플러시 |
| `innodb_lock_wait_timeout` | ha_innodb.cc L1106 | 레코드 잠금 |
| `innodb_deadlock_detect` | ha_innodb.cc L22722 | 레코드 잠금 |
| `innodb_purge_threads` | ha_innodb.cc L22326 | purge |
| `innodb_max_purge_lag` | ha_innodb.cc L22425 | purge |
| `innodb_autoinc_lock_mode` | ha_innodb.cc L23233 | 행 쓰기 |
| `sync_binlog` | sys_vars.cc L6276 | 커밋과 binlog 2PC (SYNC 단계) |
| `binlog_group_commit_sync_delay` | sys_vars.cc L1325 | 커밋과 binlog 2PC |
| `binlog_order_commits` | sys_vars.cc L1745 | 커밋과 binlog 2PC |
| `binlog_format` | sys_vars.cc L1562 | 행 쓰기 (`binlog_log_row`) |
| `log_bin` | sys_vars.cc L2392 | 커밋과 binlog 2PC |
| `transaction_isolation` | sys_vars.cc L5058 | 일관 읽기(read view 시점), 레코드 잠금(gap 여부) |
| `autocommit` | sys_vars.cc L5371 | 커밋과 binlog 2PC |
| `lock_wait_timeout` | sys_vars.cc L2378 | 명령 디스패치 (서버 MDL. InnoDB 잠금과 다른 변수) |
| `thread_handling` / `max_connections` | sys_vars.cc L3923 / L2854 | 연결과 스레드 |

## 흐름이 덮지 않는 것

```text
 PREPARE / EXECUTE (앞단만 다르고 뒤는 같다)
 ROLLBACK · SAVEPOINT (undo 를 적용하는 흐름이 없다)
 CREATE / DROP TABLE · TRUNCATE · 데이터 딕셔너리 · 원자적 DDL
 복제 명령 (CHANGE REPLICATION SOURCE, START REPLICA) · Group Replication
 PURGE BINARY LOGS · FLUSH · KILL · SHOW ENGINE INNODB STATUS
 옵티마이저와 실행기 내부 (JOIN::optimize, 이터레이터) - handler 경계까지만 본다
 FTS · 공간 인덱스 · change buffer · adaptive hash index 내부
 압축 페이지 · 암호화 · clone · 파티션 · thread pool
```
