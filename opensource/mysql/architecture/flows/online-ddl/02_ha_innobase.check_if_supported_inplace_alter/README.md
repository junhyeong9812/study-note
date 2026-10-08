# ha_innobase::check_if_supported_inplace_alter

상위: [온라인 DDL](../README.md)

**InnoDB 가 "이 ALTER 를 어떻게 하겠다"고 서버에 답하는 함수다.** 답은 세 갈래다. 메타데이터만 바꾸면 되면 `HA_ALTER_INPLACE_INSTANT`, 직접 하되 DML 을 받아 줄 수 있으면 `HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE`, 직접 하지만 쓰기를 막아야 하면 `HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE`, 못 하면 `HA_ALTER_INPLACE_NOT_SUPPORTED`(서버가 COPY 로 간다). 어느 쪽이든 끝에 `_AFTER_PREPARE` 가 붙는 것은 InnoDB 가 준비 단계에서는 항상 X 잠금을 원하기 때문이다.

## 위치

`storage` / `innobase` / `handler` / `handler0alter.cc` L966-L1371 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L966-L1371))

## 실제 코드

앞부분은 아예 못 하는 경우를 걸러 낸다. 그 다음 INSTANT 를 먼저 시도한다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L966-L1108 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L966-L1108))

```cpp
// handler0alter.cc L966-L1108
enum_alter_inplace_result ha_innobase::check_if_supported_inplace_alter(
    TABLE *altered_table, Alter_inplace_info *ha_alter_info) {
  DBUG_TRACE;

  // ... (L970-L1003 생략: raw 시스템 테이블스페이스, 읽기 전용, 열 개수 상한, 암호화 속성 변경)
  update_thd();

  if (ha_alter_info->handler_flags &
      ~(INNOBASE_INPLACE_IGNORE | INNOBASE_ALTER_NOREBUILD |
        INNOBASE_ALTER_REBUILD)) {
    if (ha_alter_info->handler_flags &
        Alter_inplace_info::ALTER_STORED_COLUMN_TYPE) {
      if (ha_alter_info->alter_info->requested_algorithm ==
          Alter_info::ALTER_TABLE_ALGORITHM_INSTANT) {
        ha_alter_info->unsupported_reason = innobase_get_err_msg(
            ER_ALTER_OPERATION_NOT_SUPPORTED_REASON_COLUMN_TYPE_INSTANT);
      } else {
        ha_alter_info->unsupported_reason = innobase_get_err_msg(
            ER_ALTER_OPERATION_NOT_SUPPORTED_REASON_COLUMN_TYPE);
      }
    }
    return HA_ALTER_INPLACE_NOT_SUPPORTED;
  }

  // ... (L1023-L1036 생략: 외래 키 검사 중 FK 추가, 비 InnoDB 파티션)

  Instant_Type instant_type = innobase_support_instant(
      ha_alter_info, m_prebuilt->table, this->table, altered_table);

  ha_alter_info->handler_trivial_ctx =
      instant_type_to_int(Instant_Type::INSTANT_IMPOSSIBLE);

  const bool is_instant_requested =
      ha_alter_info->alter_info->requested_algorithm ==
      Alter_info::ALTER_TABLE_ALGORITHM_INSTANT;

  if (!dict_table_is_partition(m_prebuilt->table)) {
    switch (instant_type) {
      case Instant_Type::INSTANT_IMPOSSIBLE:
        break;
      case Instant_Type::INSTANT_ADD_DROP_COLUMN:
        if (ha_alter_info->alter_info->requested_algorithm ==
            Alter_info::ALTER_TABLE_ALGORITHM_INPLACE) {
          /* Still fall back to INPLACE since the behaviour is different */
          break;
        } else if ((ha_alter_info->alter_info->requested_algorithm ==
                    Alter_info::ALTER_TABLE_ALGORITHM_DEFAULT) &&
                   !dict_table_is_discarded(m_prebuilt->table) &&
                   btr_is_index_empty(m_prebuilt->table->first_index())) {
          /* No records: prefer INPLACE to prevent bumping row version */
          break;
        } else if (!((m_prebuilt->table->n_def +
                      get_num_cols_added(ha_alter_info)) <=
                     REC_MAX_N_USER_FIELDS + DATA_N_SYS_COLS)) {
          if (is_instant_requested) {
            my_error(ER_INNODB_INSTANT_ADD_NOT_SUPPORTED_MAX_FIELDS, MYF(0),
                     m_prebuilt->table->name.m_name);
            return HA_ALTER_ERROR;
          }
          /* INSTANT can't be done any more. Fall back to INPLACE. */
          break;
        } else if (!is_valid_row_version(
                       m_prebuilt->table->current_row_version + 1)) {
          ut_ad(is_valid_row_version(m_prebuilt->table->current_row_version));
          if (is_instant_requested) {
            my_error(ER_INNODB_MAX_ROW_VERSION, MYF(0),
                     m_prebuilt->table->name.m_name);
            return HA_ALTER_ERROR;
          }

          /* INSTANT can't be done any more. Fall back to INPLACE. */
          break;
        } else if (!Instant_ddl_impl<dd::Table>::is_instant_add_drop_possible(
                       ha_alter_info, table, altered_table,
                       m_prebuilt->table)) {
          if (is_instant_requested) {
            /* Return error if either max possible row size already crosses max
            permissible row size or may cross it after add. */
            my_error(ER_INNODB_INSTANT_ADD_DROP_NOT_SUPPORTED_MAX_SIZE, MYF(0));
            return HA_ALTER_ERROR;
          }

          /* INSTANT can't be done. Fall back to INPLACE. */
          break;
        } else if (ha_alter_info->error_if_not_empty) {
          /* In this case, it can't be instant because the table
          may not be empty. Have to fall back to INPLACE */
          break;
        }
        [[fallthrough]];
      case Instant_Type::INSTANT_NO_CHANGE:
      case Instant_Type::INSTANT_VIRTUAL_ONLY:
      case Instant_Type::INSTANT_COLUMN_RENAME:
        ha_alter_info->handler_trivial_ctx = instant_type_to_int(instant_type);
        return HA_ALTER_INPLACE_INSTANT;
    }
  }
```

INSTANT 가 안 되면 INPLACE 로 할 수 있는지, 그리고 온라인으로 할 수 있는지를 본다. `online` 을 `false` 로 바꾸는 이유가 곧 `LOCK=NONE` 이 거부되는 이유다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L1186-L1371 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L1186-L1371))

```cpp
// handler0alter.cc L1186-L1371
  /* We should be able to do the operation in-place.
  See if we can do it online (LOCK=NONE). */
  bool online = true;

  // ... (L1190-L1192 생략: 반복자 준비)
  /* Fix the key parts. */
  for (KEY *new_key = ha_alter_info->key_info_buffer;
       new_key < ha_alter_info->key_info_buffer + ha_alter_info->key_count;
       new_key++) {
    // ... (L1197-L1205 생략: FULLTEXT 와 가상 열 동시 변경 거부)
    for (KEY_PART_INFO *key_part = new_key->key_part;
         key_part < new_key->key_part + new_key->user_defined_key_parts;
         key_part++) {
      // ... (L1209-L1247 생략: key_part 를 altered_table 필드에 맞추고, 기존 열이면 continue, 숨은 FTS_DOC_ID 교체를 막는다)
      if (key_part->field->is_flag_set(AUTO_INCREMENT_FLAG)) {
        /* We cannot assign an AUTO_INCREMENT
        column values during online ALTER. */
        assert(key_part->field == altered_table->found_next_number_field);
        ha_alter_info->unsupported_reason = innobase_get_err_msg(
            ER_ALTER_OPERATION_NOT_SUPPORTED_REASON_AUTOINC);
        online = false;
      }

      if (key_part->field->is_virtual_gcol()) {
        /* Do not support adding index on newly added
        virtual column, while there is also a drop
        virtual column in the same clause */
        if (ha_alter_info->handler_flags &
            Alter_inplace_info::DROP_VIRTUAL_COLUMN) {
          ha_alter_info->unsupported_reason = innobase_get_err_msg(
              ER_UNSUPPORTED_ALTER_INPLACE_ON_VIRTUAL_COLUMN);

          return HA_ALTER_INPLACE_NOT_SUPPORTED;
        }

        ha_alter_info->unsupported_reason =
            innobase_get_err_msg(ER_UNSUPPORTED_ALTER_ONLINE_ON_VIRTUAL_COLUMN);
        online = false;
      }
    }
  }

  // ... (L1276-L1280 생략: 단정)
  if (ha_alter_info->handler_flags & Alter_inplace_info::ADD_SPATIAL_INDEX) {
    ha_alter_info->unsupported_reason =
        innobase_get_err_msg(ER_ALTER_OPERATION_NOT_SUPPORTED_REASON_GIS);
    online = false;
  }

  // ... (L1287-L1319 생략: FULLTEXT 가 남아 있을 때 FTS_DOC_ID 삭제와 이름 변경을 막는다)
  m_prebuilt->trx->will_lock++;

  if (!online) {
    /* We already determined that only a non-locking
    operation is possible. */
  } else if (((ha_alter_info->handler_flags &
               Alter_inplace_info::ADD_PK_INDEX) ||
              innobase_need_rebuild(ha_alter_info)) &&
             (innobase_fulltext_exist(altered_table) ||
              innobase_spatial_exist(altered_table))) {
    /* Refuse to rebuild the table online, if
    FULLTEXT OR SPATIAL indexes are to survive the rebuild. */
    online = false;
    /* If the table already contains fulltext indexes,
    refuse to rebuild the table natively altogether. */
    if (m_prebuilt->table->fts) {
      ha_alter_info->unsupported_reason =
          innobase_get_err_msg(ER_INNODB_FT_LIMIT);
      return HA_ALTER_INPLACE_NOT_SUPPORTED;
    }

    if (innobase_spatial_exist(altered_table)) {
      ha_alter_info->unsupported_reason =
          innobase_get_err_msg(ER_ALTER_OPERATION_NOT_SUPPORTED_REASON_GIS);
    } else {
      ha_alter_info->unsupported_reason =
          innobase_get_err_msg(ER_ALTER_OPERATION_NOT_SUPPORTED_REASON_FTS);
    }
  } else if ((ha_alter_info->handler_flags & Alter_inplace_info::ADD_INDEX)) {
    /* Building a full-text index requires a lock.
    We could do without a lock if the table already contains
    an FTS_DOC_ID column, but in that case we would have
    to apply the modification log to the full-text indexes. */

    for (uint i = 0; i < ha_alter_info->index_add_count; i++) {
      const KEY *key =
          &ha_alter_info->key_info_buffer[ha_alter_info->index_add_buffer[i]];
      if (key->flags & HA_FULLTEXT) {
        assert(!(key->flags & HA_KEYFLAG_MASK &
                 ~(HA_FULLTEXT | HA_PACK_KEY | HA_GENERATED_KEY |
                   HA_BINARY_PACK_KEY)));
        ha_alter_info->unsupported_reason =
            innobase_get_err_msg(ER_ALTER_OPERATION_NOT_SUPPORTED_REASON_FTS);
        online = false;
        break;
      }
    }
  }

  return online ? HA_ALTER_INPLACE_NO_LOCK_AFTER_PREPARE
                : HA_ALTER_INPLACE_SHARED_LOCK_AFTER_PREPARE;
}
```

INSTANT 가 가능한 종류를 고르는 쪽이다. 바뀌는 것의 비트(`handler_flags`)가 허용 목록 안에 있어야 한다.

`storage` / `innobase` / `handler` / `handler0alter.cc` L829-L915 ([GitHub](https://github.com/mysql/mysql-server/blob/008e09c2834b98143a8c067d4d225c90953050cf/storage/innobase/handler/handler0alter.cc#L829-L915))

```cpp
// handler0alter.cc L829-L915
static inline Instant_Type innobase_support_instant(
    const Alter_inplace_info *ha_alter_info, const dict_table_t *table,
    const TABLE *old_table, const TABLE *altered_table) {
  if (!(ha_alter_info->handler_flags & ~INNOBASE_INPLACE_IGNORE)) {
    return (Instant_Type::INSTANT_NO_CHANGE);
  }

  Alter_inplace_info::HA_ALTER_FLAGS alter_inplace_flags =
      ha_alter_info->handler_flags & ~INNOBASE_INPLACE_IGNORE;

  if (alter_inplace_flags & ~INNOBASE_INSTANT_ALLOWED) {
    return (Instant_Type::INSTANT_IMPOSSIBLE);
  }

  /* During upgrade, if columns are added in system tables, avoid instant */
  if (current_thd->is_server_upgrade_thread()) {
    return (Instant_Type::INSTANT_IMPOSSIBLE);
  }

  // ... (L848-L858 생략: enum 정의)
  enum INSTANT_OPERATION op = INSTANT_OPERATION::NONE;

  if (!(alter_inplace_flags & ~Alter_inplace_info::ALTER_COLUMN_NAME)) {
    op = INSTANT_OPERATION::COLUMN_RENAME_ONLY;
  } else if (!(alter_inplace_flags &
               ~(Alter_inplace_info::ADD_VIRTUAL_COLUMN |
                 Alter_inplace_info::DROP_VIRTUAL_COLUMN))) {
    op = INSTANT_OPERATION::VIRTUAL_ADD_DROP_ONLY;
  } else if (!(alter_inplace_flags &
               ~(Alter_inplace_info::ADD_VIRTUAL_COLUMN |
                 Alter_inplace_info::DROP_VIRTUAL_COLUMN |
                 Alter_inplace_info::ALTER_COLUMN_NAME))) {
    op = INSTANT_OPERATION::VIRTUAL_ADD_DROP_WITH_RENAME;
  } else if (alter_inplace_flags & Alter_inplace_info::ADD_STORED_BASE_COLUMN &&
             !(alter_inplace_flags & Alter_inplace_info::DROP_VIRTUAL_COLUMN)) {
    op = INSTANT_OPERATION::INSTANT_ADD;
  } else if (alter_inplace_flags & Alter_inplace_info::DROP_STORED_COLUMN) {
    op = INSTANT_OPERATION::INSTANT_DROP;
  }

  switch (op) {
    case INSTANT_OPERATION::COLUMN_RENAME_ONLY: {
      bool report_error = (ha_alter_info->alter_info->requested_algorithm ==
                           Alter_info::ALTER_TABLE_ALGORITHM_INSTANT);
      if (ok_to_rename_column(ha_alter_info, old_table, altered_table, table,
                              true, report_error)) {
        return (Instant_Type::INSTANT_COLUMN_RENAME);
      }
    } break;
    case INSTANT_OPERATION::VIRTUAL_ADD_DROP_ONLY:
      if (check_v_col_in_order(old_table, altered_table, ha_alter_info)) {
        return (Instant_Type::INSTANT_VIRTUAL_ONLY);
      }
      break;
    case INSTANT_OPERATION::VIRTUAL_ADD_DROP_WITH_RENAME:
      /* Not supported yet in INPLACE. So not supporting here as well. */
      break;
    case INSTANT_OPERATION::INSTANT_DROP:
      if (!check_v_col_in_order(old_table, altered_table, ha_alter_info)) {
        break;
      }
      [[fallthrough]];
    case INSTANT_OPERATION::INSTANT_ADD:
      /* If it's an ADD COLUMN without changing existing stored column orders
      (change trailing virtual column orders is fine, especially for supporting
      adding stored columns to a table with functional indexes), or including
      ADD VIRTUAL COLUMN */
      if (table->support_instant_add_drop()) {
        return (Instant_Type::INSTANT_ADD_DROP_COLUMN);
      }
      break;
    case INSTANT_OPERATION::NONE:
      break;
  }

  return (Instant_Type::INSTANT_IMPOSSIBLE);
}
```

## 동작 흐름

```text
 L970-L1002   못 하는 경우                               반환
              raw 시스템 테이블스페이스                  NOT_SUPPORTED
              read only / force_recovery                 ERROR
              열이 REC_MAX_N_USER_FIELDS 초과             NOT_SUPPORTED
              암호화 속성 변경                           NOT_SUPPORTED
 L1006        InnoDB 가 모르는 변경 비트                 NOT_SUPPORTED (열 타입 변경 등)
 L1025        foreign_key_checks=1 에서 FK 추가          NOT_SUPPORTED

 L1038        innobase_support_instant  --> instant_type
 L1048        파티션이 아니면 instant_type 으로
                INSTANT_NO_CHANGE / VIRTUAL_ONLY / COLUMN_RENAME   --> INSTANT (L1106)
                INSTANT_ADD_DROP_COLUMN 인데 아래면 INPLACE 로 물러난다
                  ALGORITHM=INPLACE 명시                           L1053
                  ALGORITHM 기본값이고 테이블이 비어 있음          L1057  row version 을 아끼려고
                  열 수 상한 초과                                  L1063
                  row version 이 다 참 (255)                       L1073
                  행 크기 상한 초과 가능                           L1084
                  error_if_not_empty                               L1096
                  (INSTANT 명시였으면 L1063 L1073 L1084 는 물러나지 않고 ERROR,
                   L1096 은 INPLACE 쪽 값을 돌려주고 서버가 L18455 에서 오류)
                그 외                                              --> INSTANT

 L1114-L1184  INPLACE 로도 못 하는 경우                 NOT_SUPPORTED
              비 strict 모드의 NULL -> NOT NULL          (COPY 가 값을 바꿔 넣는다)
              ADD 없이 DROP PRIMARY KEY
              PK 없는 테이블의 NOT NULL -> NULL
              가상 열 추가/삭제에 다른 변경이 섞임

 L1188        online = true 로 시작
 L1254        새 인덱스에 AUTO_INCREMENT 새 열            online = false
 L1271        새 가상 열에 인덱스                         online = false
 L1284        공간 인덱스 추가                            online = false
 L1325        재구성(ADD PK 포함)인데 FULLTEXT/공간 인덱스가 남는다
                                                          online = false (FTS 가 이미 있으면 NOT_SUPPORTED)
 L1348        FULLTEXT 인덱스 추가                        online = false

 L1369        online ? NO_LOCK_AFTER_PREPARE : SHARED_LOCK_AFTER_PREPARE
```

INSTANT 가 가능한지는 바뀌는 것의 종류로 정해진다. 아래 표의 "조건" 이 맞아야 해당 `Instant_Type` 이 나온다.

```text
 innobase_support_instant 의 분류 (L861-L912)

 바뀌는 것 (handler_flags)                       조건                         Instant_Type
 INNOBASE_INPLACE_IGNORE 밖의 비트 없음          -                            INSTANT_NO_CHANGE   L833
 INNOBASE_INSTANT_ALLOWED 밖의 비트 있음         -                            INSTANT_IMPOSSIBLE  L840
 열 이름만                                       ok_to_rename_column          INSTANT_COLUMN_RENAME
 가상 열 ADD/DROP 만                             가상 열 순서 유지            INSTANT_VIRTUAL_ONLY
 가상 열 ADD/DROP + 이름 변경                    -                            INSTANT_IMPOSSIBLE  L894
 저장 열 ADD (가상 열 DROP 없음)                 support_instant_add_drop     INSTANT_ADD_DROP_COLUMN
 저장 열 DROP                                    가상 열 순서 유지 + 위 조건  INSTANT_ADD_DROP_COLUMN

 시스템 테이블에 열을 더하는 업그레이드 스레드는 항상 INSTANT_IMPOSSIBLE (L844)
```

```text
 반환값과 서버의 해석 (서버 쪽은 sql_table.cc L18465-L18533, [01])

 InnoDB 반환                         LOCK=DEFAULT       LOCK=NONE   LOCK=SHARED  ALGORITHM=INPLACE
 INSTANT                             INSTANT            INSTANT     INSTANT      INSTANT 로 실행 (주석 L18497)
 NO_LOCK_AFTER_PREPARE               INPLACE 온라인     INPLACE     INPLACE+SNW  INPLACE
 SHARED_LOCK_AFTER_PREPARE           INPLACE+SNW        오류        INPLACE+SNW  INPLACE+SNW
 NOT_SUPPORTED                       COPY               오류        COPY         오류
 ERROR                               오류

 ALGORITHM=INSTANT 에 LOCK= 을 같이 쓰면 그 자체로 오류다 (sql_table.cc L17361)
```

## 결과가 쓰이는 곳

```text
 반환값 inplace_supported
      --> [01] 이 MDL 을 언제 올리고 내릴지, ha_alter_info->online 을 켤지 정한다
 ha_alter_info->handler_trivial_ctx (Instant_Type)
      --> is_instant (L922) 로 [03] [04] 는 바로 돌아가고
      --> [09] 가 Instant_ddl_impl::commit_instant_ddl 에서 종류별로 메타데이터를 고친다
 ha_alter_info->unsupported_reason
      --> 서버가 ALGORITHM/LOCK 요청을 거절할 때 오류 메시지에 들어간다
```

## 다루지 않는 것

`INNOBASE_INSTANT_ALLOWED`, `INNOBASE_ALTER_REBUILD` 같은 비트 묶음의 정의, `Instant_ddl_impl::is_instant_add_drop_possible` 의 행 크기 계산, `ok_to_rename_column` 과 `check_v_col_in_order` 의 세부, 파티션 테이블(`ha_innopart::check_if_supported_inplace_alter`)의 판정은 이 흐름의 곁가지라 요약만 했다.
