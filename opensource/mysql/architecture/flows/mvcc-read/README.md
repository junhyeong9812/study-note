# 일관 읽기(MVCC)와 undo 체인

상위: [MySQL 아키텍처 지도](../../README.md)

잠금 없는 `SELECT` 가 **잠금을 하나도 잡지 않고, 다른 트랜잭션이 바꾸는 중인 행에서도 자기 시점의 값을 돌려받기까지**의 흐름이다. 장치는 두 개다. 하나는 **read view** 로, 읽기를 시작한 순간 "아직 커밋되지 않은 트랜잭션 번호들"을 복사해 둔 스냅샷이다. 다른 하나는 **undo 체인**으로, 클러스터드 인덱스 레코드마다 붙은 숨은 열 `DB_TRX_ID`(마지막으로 바꾼 트랜잭션)와 `DB_ROLL_PTR`(그 직전 버전을 만들 undo 레코드의 주소)이다. [02] `row_search_mvcc` 가 레코드를 하나 집으면 [05] 가 그 레코드의 `DB_TRX_ID` 를 read view 에 물어보고([06]), 안 보이면 [08] 이 `DB_ROLL_PTR` 을 따라 undo 를 한 칸씩 거꾸로 적용해 보이는 버전이 나올 때까지 옛 행을 메모리에 다시 만든다([09] [10]). 버퍼 풀의 페이지는 한 바이트도 바뀌지 않는다. 격리 수준은 **read view 를 언제 만들고 언제 버리는가**로만 갈린다([03]). 스레드 경계는 없다. undo 레코드를 쓰는 쪽은 [B+Tree 삽입과 분할](../btree-insert/04_btr_cur_ins_lock_and_undo/README.md)에, undo 를 치우는 쪽은 [purge](../purge/README.md)에 있다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 [명령 디스패치] 의 반복자가 ha_index_read_map / ha_rnd_next 를 부른다
      v
 [01] ha_innobase::index_read                            ha_innodb.cc L10430
      +-- build_template, 검색 키를 InnoDB 형식으로        L10479, L10502
      +-- row_search_mvcc(buf, mode, prebuilt, match_mode, 0)   L10556
            v
 [02] row_search_mvcc                                    row0sel.cc L4431
      PHASE 1  prefetch 캐시에서 꺼낼 수 있으면 꺼낸다    L4528
      PHASE 2  AHI 지름길 (read view 가 이미 있을 때만)   L4650
      PHASE 3  문장의 첫 호출이면                          L4819
      |   select_lock_type == LOCK_NONE  (잠금 없는 읽기)
      |     [03] trx_assign_read_view                    L4838  trx0trx.cc L2291
      |           +-- MVCC::view_open                     read0read.cc L499
      |                 +-- [04] ReadView::prepare        read0read.cc L446
      |                       m_low_limit_id, m_ids, m_up_limit_id 를 채운다
      |   아니면 lock_table(IS / IX)                     L4845  --> [레코드 잠금과 교착]
      PHASE 4  레코드 하나마다 (rec_loop)                  L4947
      |   잠금 읽기   sel_set_rec_lock                    L5251  --> [레코드 잠금과 교착]
      |   잠금 없는 읽기                                  L5323
      |     READ UNCOMMITTED 면 최신 버전 그대로           L5326
      |     클러스터드 인덱스면
      |       [05] lock_clust_rec_cons_read_sees          L5337  lock0lock.cc L236
      |             +-- [06] ReadView::changes_visible    read0types.h L163
      |       안 보이면
      |       [07] row_sel_build_prev_vers_for_mysql      L5341  row0sel.cc L3079
      |             +-- [08] row_vers_build_for_consistent_read   row0vers.cc L1249
      |                   for (;;) 한 버전씩 거꾸로
      |                   +-- [09] trx_undo_prev_version_build    trx0rec.cc L2446
      |                   |     +-- [10] trx_undo_get_undo_rec    trx0rec.cc L2421
      |                   |           purge view 가 이미 본 trx 면 "기록 없음"
      |                   +-- [06] changes_visible 이 true 면 멈춘다
      |     세컨더리 인덱스면 lock_sec_rec_cons_read_sees   L5373  페이지의 max_trx_id 로만 판정
      |       모르면 클러스터드 레코드로 가서 [05] -> [07] (row0sel.cc L3312)
      |   delete-mark 된 버전이면 건너뛴다                L5409
      |   조건을 맞추고 MySQL 행 형식으로 buf 에 쓴다
      PHASE 5  다음 레코드로 커서를 옮긴다                L5805
```

판정의 핵심은 trx_id 축 위의 세 값이다. read view 는 만들 때 한 번 채워지고 그 뒤로 바뀌지 않는다.

```text
 ReadView 가 trx_id 하나를 판정하는 규칙 ([06] changes_visible, read0types.h L163-L183)

                 m_up_limit_id                        m_low_limit_id
                       |                                     |
 ----------------------+-------------------------------------+---------------->  trx_id
   보인다               |  m_ids 에 있으면 안 보인다           |  안 보인다
   (view 를 만들 때     |  (view 를 만들 때 활성이었다)         |  (view 를 만든 뒤에
    이미 끝난 trx)      |  m_ids 에 없으면 보인다              |   시작한 trx)
                       |  (그 사이에 이미 커밋했다)            |

 m_low_limit_id   view 를 만들 때의 trx_sys->next_trx_id_or_no    ("high water mark")
 m_ids            그 순간 활성이던 RW 트랜잭션 id 들 (정렬, 자기 자신은 뺀다)
 m_up_limit_id    m_ids 의 가장 작은 값, 비었으면 m_low_limit_id   ("low water mark")
 m_creator_trx_id 자기 트랜잭션. 자기가 바꾼 것은 위치와 상관없이 보인다

 경계값  id < m_up_limit_id 만 왼쪽 칸이다. id == m_up_limit_id 는 가운데 칸으로 가고
         m_ids 의 첫 원소이므로 안 보인다 (m_ids 가 비었으면 두 경계가 같아 오른쪽 칸)
         id >= m_low_limit_id 는 오른쪽 칸이다. id == m_low_limit_id 도 안 보인다
```

레코드 하나의 버전들은 undo 레코드로 거꾸로 이어진다. 최신 버전만 페이지에 있고, 나머지는 읽을 때마다 메모리에서 다시 만든다.

```text
 한 행의 버전 체인 (id=1 을 trx 100 이 넣고, 200 과 300 이 차례로 고쳤다)

 클러스터드 인덱스 리프 페이지 (버퍼 풀)
 +------+-------------+---------------+--------+
 | id=1 | DB_TRX_ID   | DB_ROLL_PTR   | v = 30 |   최신 버전
 |      | = 300       | = R3  --+     |        |
 +------+-------------+---------|-----+--------+
                                v
 undo 레코드 R3 (TRX_UNDO_UPD_EXIST_REC, trx 300 의 update undo)
   info_bits, 이전 DB_TRX_ID = 200, 이전 DB_ROLL_PTR = R2, 바뀐 열의 옛 값 v = 20
                                v
 undo 레코드 R2 (trx 200 의 update undo)
   이전 DB_TRX_ID = 100, 이전 DB_ROLL_PTR = R1, v = 10
                                v
 R1 은 insert undo 를 가리킨다 (roll_ptr 의 bit 55 = 1)
   [09] 은 읽지 않고 "처음 넣은 버전"이라며 old_vers = nullptr 을 돌려준다

 [08] 의 걸음: 300 안 보임 -> R3 적용해 (200, R2, v=20) -> 200 안 보임
               -> R2 적용해 (100, R1, v=10) -> 100 보임 -> 이 버전을 돌려준다
```

## 어디에서 쓰이는가

```text
 [명령 디스패치]      Sql_cmd_dml::execute_inner 의 반복자가 handler 의 읽기 함수를 부른다
                      external_lock 에서 select_lock_type 이 정해진다 (ha_innodb.cc L19079-L19083)
 [B+Tree 삽입과 분할] btr_cur_ins_lock_and_undo 가 insert undo 와 DB_ROLL_PTR 을 쓴다
                      UPDATE 와 DELETE 의 update undo 도 같은 trx_undo_report_row_operation 을 지난다
                      (btr_cur_upd_lock_and_undo btr0cur.cc L3121, btr_cur_del_mark_set_clust_rec L4324)
 [레코드 잠금과 교착] 같은 row_search_mvcc 의 잠금 읽기 갈래 (L5226)
 [커밋과 binlog 2PC]  커밋이 trx_erase_lists 에서 read view 를 닫는다 (trx0trx.cc L1817)
 [purge]              purge_sys->view 는 가장 오래된 read view 의 복사본이다
                      [10] 이 그 view 로 "undo 가 이미 지워졌을 수 있는가"를 판정한다
```

다음 흐름은 [purge](../purge/README.md)다. `ReadView` 와 `trx_t` 를 한 자리에서 보는 그림은 [메모리 구조](../../structure/memory-structures/README.md)에, undo 페이지와 롤백 세그먼트의 바이트 배치는 [undo 테이블스페이스와 롤백 세그먼트](../../structure/undo-segments/README.md)에 둔다.

## db-engine 에서는

같은 문제(읽기가 쓰기를 기다리지 않게 자기 시점의 버전을 보여 주기)를 db-engine 은 키마다 버전 리스트를 메모리에 두고 앞에서부터 고르는 방식으로 풀었다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 버전을 두는 곳
   MySQL      최신 버전 하나만 B+Tree 페이지에. 옛 버전은 undo 레코드로만 남고
              읽을 때마다 [09] 가 undo 를 적용해 메모리에 다시 만든다
   db-engine  MVCCStore 의 chains: ConcurrentHashMap<K, MutableList<Version>>
              모든 버전이 그대로 리스트에 있다. get 은 뒤에서부터 isVisible 로 고른다

 버전에 붙는 번호
   MySQL      DB_TRX_ID 하나 (그 버전을 만든 trx). 끝난 시점은 다음 버전의 DB_TRX_ID 다
   db-engine  xidStart, xidEnd 두 개. insert 가 이전 버전의 xidEnd 를 자기 xid 로 닫는다

 스냅샷
   MySQL      ReadView: m_up_limit_id, m_low_limit_id, m_ids, m_creator_trx_id
   db-engine  Snapshot(xid, active): begin 시점의 활성 xid 집합을 복사한다

 격리 수준
   MySQL      RC 는 문장마다 새 view, RR 은 트랜잭션에 하나, RU 는 view 를 쓰지 않는다
   db-engine  begin 에 한 번 만든 Snapshot 하나뿐. impl 10-02 가 SI 라고 라벨을 붙이고
              lost update 를 못 막는다는 테스트를 남겼다. write skew 도 못 막는다고 표에 적었다

 삭제
   MySQL      delete-mark 비트만 켠다. [02] 가 그 버전을 건너뛴다. 실제 제거는 [purge]
   db-engine  value = null 인 tombstone 버전을 하나 더 쌓는다
```

db-engine 의 `isVisible` 다섯 줄은 `xidStart` 와 `xidEnd` 로 "내 시점에 살아 있던 구간"을 본다. MySQL 은 버전마다 시작 번호(`DB_TRX_ID`)만 들고, 끝은 체인의 한 칸 위 버전이 말해 준다. 그래서 [08] 은 "보이는 첫 버전"에서 멈추면 된다. impl 10-03 은 체인을 메모리에만 두기 때문에 재시작하면 버전 이력이 사라진다고 적었다. MySQL 의 undo 는 redo 로 보호되는 페이지라 재시작 뒤에도 남는다. 챕터: [10-01-mvcc](../../../../../project/db-engine/10-01-mvcc/), [10-02-isolation-anomaly](../../../../../project/db-engine/10-02-isolation-anomaly/), [10-03-mvcc-table-heap](../../../../../project/db-engine/10-03-mvcc-table-heap/).

## 단계

1. [ha_innobase.index_read](01_ha_innobase.index_read/README.md)가 검색 키를 InnoDB 형식으로 바꾸고 `row_search_mvcc` 를 부른다.
2. [row_search_mvcc](02_row_search_mvcc/README.md)가 커서를 열고 레코드마다 잠금 읽기와 잠금 없는 읽기로 갈라진다.
3. [trx_assign_read_view](03_trx_assign_read_view/README.md)가 트랜잭션에 read view 가 없을 때만 새로 연다. 격리 수준별로 열고 닫는 자리가 여기 모인다.
4. [ReadView.prepare](04_ReadView.prepare/README.md)가 활성 트랜잭션 목록을 복사해 세 경계를 정한다.
5. [lock_clust_rec_cons_read_sees](05_lock_clust_rec_cons_read_sees/README.md)가 레코드의 `DB_TRX_ID` 를 꺼내 read view 에 묻는다.
6. [ReadView.changes_visible](06_ReadView.changes_visible/README.md)이 trx_id 하나가 보이는지 판정한다.
7. [row_sel_build_prev_vers_for_mysql](07_row_sel_build_prev_vers_for_mysql/README.md)가 옛 버전을 담을 힙을 준비하고 버전 만들기로 넘긴다.
8. [row_vers_build_for_consistent_read](08_row_vers_build_for_consistent_read/README.md)가 보이는 버전이 나올 때까지 체인을 거슬러 오른다.
9. [trx_undo_prev_version_build](09_trx_undo_prev_version_build/README.md)가 undo 레코드 하나를 적용해 바로 앞 버전을 만든다.
10. [trx_undo_get_undo_rec](10_trx_undo_get_undo_rec/README.md)가 purge 가 지웠을 수 있는 undo 인지 보고, 아니면 undo 페이지에서 레코드를 복사한다.

## 결과가 쓰이는 곳

```text
 buf (MySQL 행 형식)
      --> 서버 계층의 반복자가 WHERE, 조인, 정렬에 쓴다

 trx->read_view
      --> RR 에서는 같은 트랜잭션의 다음 SELECT 가 그대로 쓴다
      --> trx_sys->mvcc->m_views 목록에 걸려 있어 purge 가 가장 오래된 것을 복사한다
          (MVCC::clone_oldest_view, read0read.cc L685)

 옛 버전 (prebuilt->old_vers_heap)
      --> 다음 레코드의 옛 버전을 만들 때 mem_heap_empty 로 비운다 (row0sel.cc L3088-L3092)

 DB_MISSING_HISTORY
      --> purge 가 이미 지운 undo 를 만났다는 뜻. row_search_mvcc 가 오류로 올린다
```

## 다루지 않는 것

잠금 읽기(`SELECT ... FOR UPDATE`, `FOR SHARE`)와 gap 잠금은 [레코드 잠금과 교착](../record-lock/README.md)에서 다룬다. prefetch 캐시(`row_sel_dequeue_cached_row_for_mysql`, `row_sel_enqueue_cache_row_for_mysql`), 적응형 해시 인덱스 지름길(`row_sel_try_search_shortcut_for_mysql`), index condition pushdown(`row_search_idx_cond_check`), semi-consistent read(`row_vers_build_for_semi_consistent_read`), 가상 열(`vrow`)과 LOB 의 옛 버전(`lob::undo_vers_t`), 공간 인덱스, 내부 임시 테이블의 `row_search_no_mvcc`, 읽기 전용 자동 커밋 트랜잭션의 view 재사용 증명(read0read.cc L511-L604 주석)은 이 흐름의 곁가지라 줄만 적었다.

## 하위 메서드

- [01 ha_innobase.index_read](01_ha_innobase.index_read/README.md)
- [02 row_search_mvcc](02_row_search_mvcc/README.md)
- [03 trx_assign_read_view](03_trx_assign_read_view/README.md)
- [04 ReadView.prepare](04_ReadView.prepare/README.md)
- [05 lock_clust_rec_cons_read_sees](05_lock_clust_rec_cons_read_sees/README.md)
- [06 ReadView.changes_visible](06_ReadView.changes_visible/README.md)
- [07 row_sel_build_prev_vers_for_mysql](07_row_sel_build_prev_vers_for_mysql/README.md)
- [08 row_vers_build_for_consistent_read](08_row_vers_build_for_consistent_read/README.md)
- [09 trx_undo_prev_version_build](09_trx_undo_prev_version_build/README.md)
- [10 trx_undo_get_undo_rec](10_trx_undo_get_undo_rec/README.md)
