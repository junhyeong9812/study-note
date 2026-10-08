# purge

상위: [MySQL 아키텍처 지도](../../README.md)

커밋된 트랜잭션의 update undo 가 **더는 아무 read view 에도 필요 없어졌을 때, 그 undo 가 남긴 흔적을 실제로 치우는** 백그라운드 흐름이다. 치우는 것은 세 가지다. 첫째, DELETE 가 비트만 켜 두고 남긴 delete-mark 레코드를 클러스터드 인덱스와 세컨더리 인덱스에서 물리적으로 지운다. 둘째, UPDATE 가 세컨더리 인덱스에 남긴 옛 키 엔트리를 지운다. 셋째, 다 처리한 undo 로그를 history list 에서 떼어 내고 undo 세그먼트를 돌려주며, 너무 커진 undo 테이블스페이스는 통째로 잘라낸다. 기준은 하나다. **가장 오래된 read view 가 이미 보는 트랜잭션까지만** 치운다([04]). 그래서 오래 열린 트랜잭션 하나가 purge 전체를 붙잡는다. 이 흐름에는 **스레드 경계가 두 번** 있다. 커밋하는 사용자 스레드가 undo 를 history list 에 올리는 것이 한 번(그 자리는 [커밋과 binlog 2PC](../commit-2pc/10_trx_commit_low/README.md)에 있다), 코디네이터가 undo 레코드를 테이블별로 묶어 워커 스레드에 나눠 주는 것이 또 한 번이다. 코디네이터도 한 몫을 직접 처리한다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 사용자 스레드 (커밋)                                     --> [커밋과 binlog 2PC] 10
   trx_write_serialisation_history
     trx_serialisation_number_get    trx->no 를 받고 rseg 를 purge_queue 에 넣는다
                                     (그 rseg 의 history 가 비어 있었을 때만, trx0trx.cc L1505)
     trx_purge_add_update_undo_to_history                 trx0purge.cc L352
       flst_add_first(TRX_RSEG_HISTORY)                   L402  새 로그는 history 의 앞에
       rseg_history_len += n                              L406  많으면 purge 를 깨운다 (L409)
 ------------------------------------------------------------------
      스레드 경계 1  (purge_queue, trx_sys->rseg_history_len, SRV_PURGE 슬롯 이벤트)
 ------------------------------------------------------------------
 purge 코디네이터 스레드
 [01] srv_purge_coordinator_thread                        srv0srv.cc L3032
      +-- 할 일이 없었으면 srv_purge_coordinator_suspend  L3066  최대 10ms 씩 기다린다
      +-- [02] srv_do_purge                               L3076  srv0srv.cc L2845
            +-- history 가 늘면 쓸 스레드 수를 하나 올리고, 한가하면 내린다
            +-- rseg_history_len == 0 이면 끝
            +-- [03] trx_purge(n_use_threads, batch_size, do_truncate)   trx0purge.cc L2396
                  +-- trx_purge_dml_delay                 history 가 너무 길면 DML 을 늦춘다
                  +-- [04] trx_purge_update_oldest_needed L252
                  |     clone_oldest_view -> purge_sys->view
                  |     m_lowest_needed_trx_no = min(view.low_limit_no, GTID 영속화)
                  +-- [05] trx_purge_attach_undo_recs     L2243
                  |     history 를 trx->no 순서로 읽어 batch_size 페이지만큼
                  |     m_lowest_needed_trx_no 에 닿으면 멈춘다
                  |     undo 레코드를 table_id 로 묶어 스레드 수만큼의 그룹에
                  +-- n - 1 개 그룹을 srv_que_task_enqueue_low     --> 워커
                  +-- 마지막 1 개는 코디네이터가 que_run_threads   --> [07]
                  +-- trx_purge_wait_for_workers_to_complete
                  +-- do_truncate 면 [10] trx_purge_truncate        trx0purge.cc L2381
                        history 에서 다 처리한 undo 로그를 떼고 세그먼트를 돌려준다
                        커진 undo 테이블스페이스를 잘라낸다
 ------------------------------------------------------------------
      스레드 경계 2  (srv_sys->tasks 큐, SRV_WORKER 슬롯 이벤트, purge_sys->n_completed)
 ------------------------------------------------------------------
 purge 워커 스레드 (innodb_purge_threads - 1 개)
 [06] srv_worker_thread                                   srv0srv.cc L2789
      +-- srv_task_execute -> que_run_threads(thr)
            v
 [07] row_purge_step                                      row0purge.cc L1210
      +-- 그룹의 undo 레코드를 하나씩 row_purge
            +-- row_purge_parse_undo_rec                  테이블을 열고 MDL 을 잡는다
            +-- [08] row_purge_record_func                L1074
                  TRX_UNDO_DEL_MARK_REC
                    [09] row_purge_del_mark               L656
                         세컨더리 엔트리를 지우고 (row_purge_remove_sec_if_poss)
                         클러스터드 레코드를 지운다 (row_purge_remove_clust_if_poss)
                  TRX_UNDO_UPD_EXIST_REC (또는 BLOB 이 바뀐 갱신)
                    row_purge_upd_exist_or_extern         세컨더리의 옛 키 엔트리, 버려진 BLOB
```

history list 는 롤백 세그먼트마다 하나씩 있는 파일 위의 연결 리스트다. 커밋은 앞에 붙이고, purge 는 뒤에서부터 읽고 뒤에서부터 떼어 낸다.

```text
 롤백 세그먼트 하나 (rseg 헤더 페이지의 TRX_RSEG_HISTORY, 파일 기반 이중 연결 리스트)

 first                                                                    last
   |                                                                        |
   v                                                                        v
 [no=900] <-> [no=870] <-> [no=760] <-> ... <-> [no=520] <-> [no=500]
   ^ 방금 커밋 (L402 flst_add_first)                      ^ 가장 오래된 커밋
                                                          purge 가 여기부터 읽는다 (rseg->last_page_no)
                                                          다 읽으면 flst_get_prev_addr 로 앞(더 새 것)으로

 각 칸 = update undo 로그 헤더 하나 (트랜잭션 하나의 update undo)
         TRX_UNDO_TRX_NO (= trx->no), TRX_UNDO_DEL_MARKS, 그 아래 undo 레코드들

 rseg 가 여럿이므로 "다음에 읽을 rseg" 는 purge_queue 가 정한다
   purge_queue  = trx->no 가 가장 작은 것이 top 인 우선순위 큐 (비교자 trx0types.h L610-L612)
   원소         = (rseg 의 last_trx_no, rseg)
```

치울 수 있는 범위는 가장 오래된 read view 하나가 정한다. 이 경계 너머는 history list 가 아무리 길어도 손대지 않는다.

```text
 purge 의 경계 (trx->no 축, 작은 쪽이 왼쪽)

 history:   500   520   ...   600   610   ...   870   900
            |<------ 치울 수 있다 ------>|<------ 남긴다 ---------------->|
                                        ^
                       m_lowest_needed_trx_no = min(purge view 의 m_low_limit_no,
                                                   GTID 영속화가 아직 필요한 trx no)  [04]

 [05] 는 iter.trx_no >= m_lowest_needed_trx_no 면 더 꺼내지 않는다     (trx0purge.cc L2221)
 [10] 은 그 값을 넘어서는 undo 로그를 history 에서 떼지 않는다          (trx0purge.cc L1625)

 RR 트랜잭션 하나가 BEGIN 뒤 SELECT 하고 한 시간 동안 커밋하지 않으면
   그 view 의 m_low_limit_no 가 한 시간 동안 그대로다
   -> 그 뒤 커밋된 모든 update undo 와 delete-mark 레코드가 남는다
   -> rseg_history_len 이 늘고, [일관 읽기(MVCC)] 의 체인도 길어진다
```

## 어디에서 쓰이는가

```text
 [커밋과 binlog 2PC]   trx_commit_low 가 update undo 를 history list 에 올리고 rseg 를 purge_queue 에 넣는다 (history 가 빈 rseg 만)
 [일관 읽기(MVCC)]     clone_oldest_view 가 trx_sys->mvcc->m_views 를 읽는다
                       읽는 쪽은 purge_sys->view 로 "이 undo 는 지워졌을 수 있다"를 판정한다
 [B+Tree 삽입과 분할]  [09] 의 레코드 삭제가 btr_cur_optimistic_delete / pessimistic_delete 로 간다
                       페이지가 비면 btr_cur_compress_if_useful 로 합친다 (btr0cur.cc L4811)
 [레코드 잠금과 교착]  지워지는 레코드의 잠금을 다음 레코드가 gap 잠금으로 물려받는다
                       (lock_update_delete lock0lock.cc L3175, btr0cur.cc L4573 / L4729 에서 부른다)
 [크래시 복구]         srv_start 가 trx_purge_sys_initialize 로 purge_queue 를 다시 만들고
                       srv_start_purge_threads 가 스레드를 띄운다 (srv0start.cc L2169)
```

앞 흐름은 [일관 읽기(MVCC)와 undo 체인](../mvcc-read/README.md)과 [커밋과 binlog 2PC](../commit-2pc/README.md)다. 롤백 세그먼트와 undo 로그 헤더의 바이트 배치는 [undo 테이블스페이스와 롤백 세그먼트](../../structure/undo-segments/README.md)에, 코디네이터와 워커를 서버 전체 스레드 사이에서 보는 그림은 [스레드 구성](../../structure/threads/README.md)에 둔다.

## db-engine 에서는

db-engine 에는 이 흐름에 대응하는 챕터가 없다. MVCC 를 다루는 두 챕터가 스스로 정리 기능이 없다고 적어 두었고(10-01 "정리 기능이 아예 없다", 10-03 "vacuum 없음"), 그 빈자리가 MySQL 에서는 이 흐름이다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 옛 버전이 쌓이는 곳
   MySQL      undo 로그 (history list). 페이지에는 최신 버전과 delete-mark 레코드만
   db-engine  MVCCStore.chains 의 리스트. insert 와 delete 가 Version 을 add 할 뿐 지우지 않는다

 누가 치우는가
   MySQL      purge 코디네이터 + 워커. 가장 오래된 read view 까지
   db-engine  없음. impl 10-01 7절 과제 3: "우리 코드에는 정리 기능이 아예 없다"
              impl 10-03 MVCCTableHeap 의 KDoc Limitations: "vacuum 없음, version chain 누적"

 삭제의 끝
   MySQL      DELETE 는 delete-mark. [09] 가 나중에 B+Tree 에서 실제로 지운다
   db-engine  tombstone 버전을 하나 더 쌓는다. TableHeap 에는 삭제 API 가 없다 (10-03 과제 3)

 읽기 비용
   MySQL      체인 길이 = 아직 purge 되지 않은 갱신 수. purge 가 따라가면 짧게 유지된다
   db-engine  get 이 리스트를 뒤에서부터 선형 탐색. 오래된 snapshot 일수록 O(버전 수)
```

impl 10-01 의 과제 3 답은 PostgreSQL 의 VACUUM 과 InnoDB 의 "undo log + purge" 를 해법으로 들고, 둘의 공통점을 "가장 오래된 활성 snapshot 을 알아야 한다"로 정리했다. MySQL 에서 그 값이 [04] 의 `purge_sys->view` 와 `m_lowest_needed_trx_no` 다. impl 10-03 의 과제 4 답은 버전을 디스크에 제대로 얹으려면 "저장, 인덱스, 정리 세 계층을 함께 바꾸는 일"이라고 적었는데, [09] 가 세컨더리 인덱스 엔트리를 먼저 지우고 클러스터드 레코드를 지우는 순서가 그 셋째 계층의 실제 모습이다. 두 챕터의 "다음 한계" 절은 정리 대신 isolation 라벨(10-02)과 옵티마이저(단계 11)로 넘어간다. 챕터: [10-01-mvcc](../../../../../project/db-engine/10-01-mvcc/), [10-03-mvcc-table-heap](../../../../../project/db-engine/10-03-mvcc-table-heap/).

## 단계

1. [srv_purge_coordinator_thread](01_srv_purge_coordinator_thread/README.md)가 할 일이 생길 때까지 자고, 깨면 `srv_do_purge` 를 돌린다.
2. [srv_do_purge](02_srv_do_purge/README.md)가 history 길이를 보며 쓸 스레드 수를 정하고 배치를 반복한다.
3. [trx_purge](03_trx_purge/README.md)가 배치 하나를 지휘한다. 기준을 갱신하고, 레코드를 모아 나눠 주고, 끝나기를 기다린다.
4. [trx_purge_update_oldest_needed](04_trx_purge_update_oldest_needed/README.md)가 가장 오래된 read view 를 복사해 purge 의 경계를 정한다.
5. [trx_purge_attach_undo_recs](05_trx_purge_attach_undo_recs/README.md)가 history 를 trx->no 순서로 읽어 undo 레코드를 테이블별 그룹으로 나눈다.
6. [srv_worker_thread](06_srv_worker_thread/README.md)가 작업 큐에서 그룹 하나를 꺼내 실행한다.
7. [row_purge_step](07_row_purge_step/README.md)이 그룹의 undo 레코드를 하나씩 해석하고 테이블을 연다.
8. [row_purge_record_func](08_row_purge_record_func/README.md)이 undo 종류에 따라 지울 대상을 고른다.
9. [row_purge_del_mark](09_row_purge_del_mark/README.md)가 delete-mark 된 행의 세컨더리 엔트리와 클러스터드 레코드를 지운다.
10. [trx_purge_truncate](10_trx_purge_truncate/README.md)가 다 처리한 undo 로그를 history 에서 떼고, 커진 undo 테이블스페이스를 잘라낸다.

## 결과가 쓰이는 곳

```text
 B+Tree 에서 사라진 delete-mark 레코드와 옛 세컨더리 엔트리
      --> 페이지에 빈자리가 생긴다. 이후 삽입이 [B+Tree 삽입과 분할] 에서 그 자리를 쓴다
      --> 스캔이 건너뛸 delete-mark 레코드가 줄어든다

 rseg_history_len (SHOW ENGINE INNODB STATUS 의 History list length, lock0lock.cc L4436)
      --> [02] 의 스레드 수 조절, [03] 의 DML 지연(innodb_max_purge_lag) 판단

 돌려받은 undo 세그먼트와 잘라낸 undo 테이블스페이스
      --> 새 트랜잭션의 undo 가 다시 쓴다

 purge_sys->view
      --> [일관 읽기(MVCC)] 의 trx_undo_get_undo_rec 가 "기록 없음" 판정에 쓴다
```

## 다루지 않는 것

갱신 purge(`row_purge_upd_exist_or_extern`)의 세부와 외부 저장 열(BLOB, LOB) 해제(`row_purge_upd_exist_or_extern_func`, `free_lob_pages`), 가상 열과 다중 값 인덱스, 전문 검색 인덱스의 보조 테이블, change buffer 를 거치는 세컨더리 삭제, `innodb_purge_rseg_truncate_frequency` 와 `SET INACTIVE` 로 명시한 undo 테이블스페이스의 상태 전이 세부, GTID 영속화(`Clone_persist_gtid`)가 경계를 낮추는 이유, 임시 테이블의 no-redo 롤백 세그먼트, 느린 종료(`innodb_fast_shutdown=0`)의 끝까지 purge, purge 중지와 재개(`trx_purge_stop`, `trx_purge_run`)는 이 흐름의 곁가지라 줄만 적었다.

## 하위 메서드

- [01 srv_purge_coordinator_thread](01_srv_purge_coordinator_thread/README.md)
- [02 srv_do_purge](02_srv_do_purge/README.md)
- [03 trx_purge](03_trx_purge/README.md)
- [04 trx_purge_update_oldest_needed](04_trx_purge_update_oldest_needed/README.md)
- [05 trx_purge_attach_undo_recs](05_trx_purge_attach_undo_recs/README.md)
- [06 srv_worker_thread](06_srv_worker_thread/README.md)
- [07 row_purge_step](07_row_purge_step/README.md)
- [08 row_purge_record_func](08_row_purge_record_func/README.md)
- [09 row_purge_del_mark](09_row_purge_del_mark/README.md)
- [10 trx_purge_truncate](10_trx_purge_truncate/README.md)
