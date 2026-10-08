# 온라인 DDL

상위: [MySQL 아키텍처 지도](../../README.md)

`ALTER TABLE` 하나가 **INSTANT, INPLACE, COPY 중 무엇으로 돌지 정해지고, INPLACE 라면 테이블에 쓰기를 막지 않은 채 인덱스를 만들거나 테이블을 다시 짓고, 마지막에 잠깐 테이블을 독점해 새 정의로 바꿔 끼울 때까지**의 흐름이다. 이 흐름의 축은 메타데이터 잠금(MDL)의 세기 변화다. 서버 계층은 `MDL_SHARED_UPGRADABLE` 로 시작해 준비 단계에서 `MDL_EXCLUSIVE` 로 올렸다가, 본 작업 동안 다시 내리고, 커밋 직전에 또 `MDL_EXCLUSIVE` 로 올린다. 내려가 있는 동안 다른 연결의 DML 은 그대로 진행되고, InnoDB 는 그 변경을 **row log** 라는 임시 로그에 쌓았다가 빌드가 끝난 뒤 새 인덱스에 다시 적용한다. 스레드 경계는 없다. ALTER 를 낸 연결 스레드가 처음부터 끝까지 돌고, 동시 DML 은 각자의 연결 스레드에서 row log 에 기록만 남긴다(인덱스 빌드의 정렬 단계는 `ddl::Loader` 가 작업 스레드를 더 띄울 수 있다).

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 ALTER 를 낸 연결 스레드
 ------------------------------------------------------------------
 Sql_cmd_alter_table::execute                       sql_alter.cc L220
 mysql_alter_table                                   sql_table.cc L17285
      +-- COPY 로 못 박는 조건 (old_alter_table, 불가능한 변경)  L17998-L18020
      +-- 엔진에 물어서 고른다                                   L18374-L18548
      |     +-- [02] ha_innobase::check_if_supported_inplace_alter  handler0alter.cc L966
      |           INSTANT / NO_LOCK_AFTER_PREPARE / SHARED_LOCK_AFTER_PREPARE / NOT_SUPPORTED
      +-- INPLACE 또는 INSTANT -> [01] mysql_inplace_alter_table   L14394
      |     +-- MDL 을 X 로 올린다 (준비 단계만, INSTANT 는 안 올림)  L14450
      |     +-- [03] ha_innobase::prepare_inplace_alter_table      handler0alter.cc L1442
      |     |     INSTANT 면 바로 돌아온다. 아니면 새 인덱스와 row log 를 만든다
      |     +-- MDL 을 SU 로 내린다                               L14625  <-- 동시 DML 허용 구간 시작
      |     +-- [04] ha_innobase::inplace_alter_table              handler0alter.cc L1566
      |     |     +-- [05] ddl::Context::build                     ddl0ctx.cc L516
      |     |           +-- [06] ddl::Loader::build_all            ddl0loader.cc L477
      |     |                 클러스터드 인덱스를 훑고, 정렬하고, B+Tree 를 아래에서 위로 쌓는다
      |     |                 +-- Builder::finalize -> [08] row_log_apply   row0log.cc L3816
      |     +-- MDL 을 다시 X 로 올린다                           L14638  <-- 동시 DML 허용 구간 끝
      |     +-- [09] ha_innobase::commit_inplace_alter_table       handler0alter.cc L1602
      |     |     INSTANT 면 여기서 메타데이터만 바꾼다 (Instant_ddl_impl)
      |     +-- DD 에 새 정의 저장, binlog 기록, 커밋              L14716-L14883
      +-- 아니면 COPY: MDL 을 SNW 로 올리고 행을 하나씩 복사      L18550 이하

 동시 DML 을 하는 다른 연결 스레드 (빌드 중)
 ------------------------------------------------------------------
 row_ins_sec_index_entry_low                         row0ins.cc L2899
 row_upd_sec_index_entry_low                         row0upd.cc L2235
      +-- 인덱스 상태가 ONLINE_INDEX_CREATION 이면
            [07] row_log_online_op                   row0log.cc L279
            새 인덱스 트리는 건드리지 않고 row log 에 한 줄을 붙인다
```

알고리즘 이름 셋이 실제로 무엇을 하는지는 아래 표로 정리된다. INSTANT 도 서버 쪽에서는 같은 `mysql_inplace_alter_table` 경로를 지나고, 일을 하는 자리가 [09] 로 옮겨졌을 뿐이다.

```text
 세 알고리즘 (엔진 반환값 기준)

 반환값                              경로                         데이터를 건드리나  동시 DML
 HA_ALTER_INPLACE_INSTANT            [01] -> [09] Instant_ddl     안 건드린다        막지 않는다 (X 는 짧게)
 HA_ALTER_INPLACE_NO_LOCK_AFTER_PREP [01] -> [03]~[09]            인덱스 빌드/재구성  허용 (row log)
 HA_ALTER_INPLACE_SHARED_LOCK_AFTER  [01] -> [03]~[09]            인덱스 빌드/재구성  읽기만 (SNW)
 HA_ALTER_INPLACE_NOT_SUPPORTED      COPY (L18550 이하)           새 테이블에 복사    읽기만 (SNW)

 InnoDB 는 위 네 가지와 HA_ALTER_ERROR 만 돌려준다 (handler0alter.cc L966-L1371)
 NO_LOCK, SHARED_LOCK, EXCLUSIVE_LOCK 은 다른 엔진용이고 InnoDB 경로에는 나오지 않는다
```

```text
 MDL 세기 변화 (ALTER 연결이 쥔 테이블 MDL, 기본 LOCK=DEFAULT, LOCK TABLES 아님,
                InnoDB 가 NO_LOCK_AFTER_PREPARE 를 준 경우)

 단계                    MDL    다른 연결의 SELECT  다른 연결의 DML   줄
 파싱, 테이블 열기       SU     된다                된다              parse_tree_nodes.cc L3726-L3728
 [01] 준비 전 업그레이드 X      대기                대기              sql_table.cc L14450
 [03] prepare            X      대기                대기
 [01] 다운그레이드       SU     된다                된다              sql_table.cc L14625
 [04] inplace (빌드)     SU     된다                된다 (row log)
 [01] 커밋 전 업그레이드 X      대기                대기              sql_table.cc L14638
 [09] commit             X      대기                대기
 DD 저장, binlog, 커밋   X
 문장 끝에 해제

 SHARED_LOCK_AFTER_PREPARE (예: FULLTEXT 인덱스 추가) 이면 다운그레이드가 SU 대신 SNW 라
 빌드 동안 DML 이 막힌다 (sql_table.cc L14620-L14622)
 사용자가 LOCK=SHARED 를 쓰면 같은 자리에서 SNW 로 내리고 (L14621), LOCK=EXCLUSIVE 를 쓰면
 준비 전에 X 를 잡아 커밋까지 내리지 않는다 (L14427-L14428, L14617)
 INSTANT 는 준비 전 업그레이드와 다운그레이드가 없고 L14638 의 X 한 번뿐이다
 X 로 올리는 두 번은 이미 그 테이블을 쓰고 있는 트랜잭션이 끝날 때까지 기다린다
```

## 어디에서 쓰이는가

```text
 [명령 디스패치]        mysql_execute_command 의 lex->m_sql_cmd->execute (sql_parse.cc L4766) 가
                        Sql_cmd_alter_table::execute 로 들어온다
 [행 쓰기]              빌드 중에 들어온 INSERT 의 보조 인덱스 삽입이 [07] 로 빠진다
 [B+Tree 삽입과 분할]   [06] 은 행 단위 삽입이 아니라 정렬된 레코드로 페이지를 아래에서 위로 채운다
 [mtr 와 redo]          [06] 이 쌓는 페이지는 redo 를 남기지 않는다 (btr0load.cc L317 MTR_LOG_NO_REDO)
                        대신 끝에 페이지를 플러시하고 MLOG_INDEX_LOAD 한 줄만 쓴다 (ddl0builder.cc L1937)
```

앞 흐름은 [명령 디스패치](../command-dispatch/README.md)다. 빌드 중 들어오는 동시 쓰기는 [행 쓰기](../row-insert/README.md)와 [B+Tree 삽입과 분할](../btree-insert/README.md)을 지나다가 [07] 로 갈라진다.

## db-engine 에서는

같은 문제(큰 테이블의 스키마를 서비스를 멈추지 않고 바꾸기)를 db-engine 은 "메타데이터만 바꾸는 ADD COLUMN" 하나로 풀었고, 그것은 InnoDB 의 INSTANT 경로와 같은 발상이다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 메타데이터만 바꾸기
   MySQL      INSTANT ADD/DROP COLUMN. 행은 그대로 두고 테이블의 current_row_version 을
              하나 올린다 (dict0inst.cc L258). 최대 MAX_ROW_VERSION = 255 (rem0types.h L46)
              다 쓰면 INPLACE 로 물러난다 (handler0alter.cc L1073-L1083)
   db-engine  OnlineDdl.addColumn 이 TableSchema 에 컬럼을 붙여 다시 등록한다
              옛 행은 읽을 때 빈자리를 null 로 해석한다

 데이터를 건드려야 할 때
   MySQL      INPLACE: 새 인덱스를 따로 빌드하고 그 사이 DML 은 row log 에 쌓았다 적용
              COPY: 새 테이블로 행을 복사, 쓰기는 막는다
   db-engine  NOT NULL 컬럼 추가를 require 로 거부한다. 재작성 경로가 없다

 스키마 버전
   MySQL      행마다 row version 을 기록해 어느 정의로 읽을지 고른다. DD 는 트랜잭션으로 갱신
   db-engine  SchemaVersionLog 가 변경을 순번과 함께 append 한다. 행에는 버전이 없다

 동시성
   MySQL      MDL 업그레이드와 다운그레이드로 짧은 독점 구간 둘만 만든다
   db-engine  catalog.dropTable + registerTable. impl 문서가 다중 스레드 race 를 인정
```

db-engine impl 문서의 과제 5번은 "바꿀 곳을 catalog 하나로 줄이면 원자성 문제가 사라진다"고 결론짓는다. InnoDB 의 INSTANT 도 같은 계산이고, 다만 바꿀 곳이 DD 테이블 여러 개라 DD 트랜잭션 커밋 하나로 묶는다. INPLACE 는 그 계산이 안 되는 변경(인덱스 추가, 열 순서 변경, 테이블 재구성)을 위한 경로라 db-engine 에는 대응물이 없다. 챕터: [19-01-online-ddl](../../../../../project/db-engine/19-01-online-ddl/), [19-02-schema-version](../../../../../project/db-engine/19-02-schema-version/).

## 단계

1. [mysql_inplace_alter_table](01_mysql_inplace_alter_table/README.md)이 MDL 을 올리고 내리며 엔진의 세 단계(prepare, inplace, commit)를 차례로 부른다.
2. [ha_innobase.check_if_supported_inplace_alter](02_ha_innobase.check_if_supported_inplace_alter/README.md)가 INSTANT 가능 여부와 온라인 가능 여부를 판정해 알고리즘과 잠금 세기를 정한다.
3. [ha_innobase.prepare_inplace_alter_table](03_ha_innobase.prepare_inplace_alter_table/README.md)이 X 잠금 아래에서 새 인덱스를 사전에 등록하고 row log 를 붙인다.
4. [ha_innobase.inplace_alter_table](04_ha_innobase.inplace_alter_table/README.md)이 격리 수준을 맞추고 `ddl::Context` 를 만들어 빌드를 시작한다.
5. [ddl.Context.build](05_ddl.Context.build/README.md)가 빌드를 돌리고 실패하면 온라인 인덱스를 중단 상태로 표시한다.
6. [ddl.Loader.build_all](06_ddl.Loader.build_all/README.md)이 클러스터드 인덱스를 훑어 정렬하고 B+Tree 를 쌓은 뒤 row log 적용으로 넘긴다.
7. [row_log_online_op](07_row_log_online_op/README.md)가 빌드 중 다른 연결의 보조 인덱스 변경을 row log 에 적는다.
8. [row_log_apply](08_row_log_apply/README.md)가 쌓인 row log 를 새 인덱스에 적용하고 인덱스를 완성 상태로 바꾼다.
9. [ha_innobase.commit_inplace_alter_table](09_ha_innobase.commit_inplace_alter_table/README.md)이 X 잠금 아래에서 사전을 바꾸고, INSTANT 라면 여기서 메타데이터만 고친다.

## 결과가 쓰이는 곳

```text
 새 dd::Table (altered_table_def)
      --> [01] 이 옛 정의를 drop 하고 store 한다 (sql_table.cc L14716, L14732)
      --> 같은 DD 트랜잭션 커밋에 묶여 원자적으로 바뀐다 (L14883)

 새 보조 인덱스
      --> [08] 뒤 ONLINE_INDEX_COMPLETE. 이후 DML 은 row log 를 거치지 않고 트리에 바로 쓴다
      --> [09] 에서 사전에 커밋되어 옵티마이저가 쓸 수 있게 된다

 재구성된 테이블 (ADD PRIMARY KEY, 열 순서 변경 등 need_rebuild)
      --> [09] commit_try_rebuild 가 마지막 row log 를 적용하고 이름을 바꿔 끼운다
      --> 옛 테이블은 임시 이름으로 바뀐 뒤 ddl::drop_table 로 지워진다

 binlog
      --> ALTER 문장 텍스트 하나가 기록된다 (sql_table.cc L14830). 복제본은 같은 ALTER 를 다시 돈다
```

## 다루지 않는 것

COPY 알고리즘의 행 복사(`copy_data_between_tables`), 파티션 테이블의 `ha_innopart` 경로와 `group_commit_ctx`, FULLTEXT 와 공간 인덱스의 빌드(`FTS_SORT_AND_BUILD`, R-Tree 행 단위 삽입), 외래 키 추가와 이름 잠금(`collect_fk_names_for_new_fks`), 테이블 재구성용 row log(`row_log_table_insert` / `update` / `delete` 와 `row_log_table_apply`)의 레코드 형식, `ddl::Merge_file_sort` 의 다단계 병합 세부, DDL 로그(`log_ddl`)를 이용한 크래시 후 정리, 원자적 DDL 을 지원하지 않는 엔진의 분기는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 mysql_inplace_alter_table](01_mysql_inplace_alter_table/README.md)
- [02 ha_innobase.check_if_supported_inplace_alter](02_ha_innobase.check_if_supported_inplace_alter/README.md)
- [03 ha_innobase.prepare_inplace_alter_table](03_ha_innobase.prepare_inplace_alter_table/README.md)
- [04 ha_innobase.inplace_alter_table](04_ha_innobase.inplace_alter_table/README.md)
- [05 ddl.Context.build](05_ddl.Context.build/README.md)
- [06 ddl.Loader.build_all](06_ddl.Loader.build_all/README.md)
- [07 row_log_online_op](07_row_log_online_op/README.md)
- [08 row_log_apply](08_row_log_apply/README.md)
- [09 ha_innobase.commit_inplace_alter_table](09_ha_innobase.commit_inplace_alter_table/README.md)
