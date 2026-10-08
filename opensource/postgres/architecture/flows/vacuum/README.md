# vacuum

상위: [PostgreSQL 아키텍처 지도](../../README.md)

UPDATE 와 DELETE 가 남긴 **죽은 행 버전을 치우고, 오래된 XID 를 얼리고(freeze), 그 결과를 visibility map 과 pg_class 에 남기는** 흐름이다. PostgreSQL 은 행을 고칠 때 옛 버전을 그 자리에 두고 새 버전을 따로 쓰기 때문에, 누군가가 "이제 어떤 스냅샷도 옛 버전을 볼 수 없다"를 판정해 치워야 한다. 그 판정선이 [07] 에서 계산하는 **OldestXmin** 이다. 입구는 수동 `VACUUM` 의 [01] `ExecVacuum` 과 autovacuum worker 의 [04] `do_autovacuum` 둘이고, 둘 다 [02] `vacuum()` → [05] `vacuum_rel()` 을 거쳐 테이블마다 트랜잭션 하나로 [06] `heap_vacuum_rel` 을 돈다. 일은 세 단계다. 힙을 한 번 훑으며 페이지마다 prune·freeze 하고 죽은 TID 를 모으고([08]~[10]), 모은 TID 로 인덱스를 지우고([11]), 힙을 다시 찾아가 그 줄 포인터를 재사용 가능으로 바꾼다([12]). 순서가 이렇게 정해진 이유는 "인덱스가 가리키는 줄 포인터를 먼저 재사용하면 안 된다"는 한 가지 불변식이다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다. `vacuum.c` 는 `commands/`, `vacuumlazy.c`·`pruneheap.c` 는 `access/heap/`, `autovacuum.c` 는 `postmaster/` 에 있다.

## 전체 그림

```text
 수동  VACUUM t;
   standard_ProcessUtility                       tcop/utility.c L862
   +-- [01] ExecVacuum                           vacuum.c L162     옵션 파싱, VacuumParams, ring buffer
         +-- [02] vacuum

 자동  autovacuum
   [03] AutoVacLauncherMain                      autovacuum.c L368  naptime 마다 DB 하나를 고른다
     +-- do_start_worker -> postmaster 가 worker 를 띄운다
   worker: [04] do_autovacuum                    autovacuum.c L1885 pg_class 를 훑어 대상 테이블을 고른다
     +-- autovacuum_do_vac_analyze -> [02] vacuum

 [02] vacuum                vacuum.c L500
   L616  바깥 트랜잭션을 커밋한다 (CommitTransactionCommand)
   L649  테이블마다
   +-- [05] vacuum_rel      vacuum.c L2018
         L2040  StartTransactionCommand          테이블 하나 = 트랜잭션 하나
         L2067  PROC_IN_VACUUM                    남의 OldestXmin 계산에서 빠진다
         L2096  ShareUpdateExclusiveLock          (FULL 이면 AccessExclusiveLock)
         L2317  table_relation_vacuum
         +-- [06] heap_vacuum_rel                 vacuumlazy.c L615
         |     L777  [07] vacuum_get_cutoffs      vacuum.c L1116   OldestXmin, FreezeLimit, aggressive
         |     L833  dead_items_alloc             TidStore, maintenance_work_mem (autovacuum 은 autovacuum_work_mem) 만큼
         |     L839  [08] lazy_scan_heap          vacuumlazy.c L1200
         |     |       visibility map 으로 건너뛸 페이지를 고른다
         |     |       페이지마다 [09] lazy_scan_prune              L1958
         |     |         +-- [10] heap_page_prune_and_freeze        pruneheap.c L350
         |     |       dead_items 가 차면 중간에, 다 돌면 마지막에
         |     |       [11] lazy_vacuum                              L2464
         |     |         +-- lazy_vacuum_all_indexes   ambulkdelete   인덱스에서 TID 를 지운다
         |     |         +-- [12] lazy_vacuum_heap_rel               L2734  LP_DEAD -> LP_UNUSED
         |     |       lazy_cleanup_all_indexes      amvacuumcleanup
         |     L862  lazy_truncate_heap           끝의 빈 페이지를 잘라낸다
         |     L922  [13] vac_update_relstats     vacuum.c L1442   relpages, relfrozenxid
         L2334  CommitTransactionCommand
   L723  vac_update_datfrozenxid                  pg_database.datfrozenxid, pg_xact 잘라내기
         (수동 VACUUM 일 때. autovacuum 은 SKIP_DATABASE_STATS 로 건너뛰고 [04] do_autovacuum L2595 에서 부른다)
```

힙 페이지 하나의 줄 포인터가 VACUUM 한 번 동안 어떻게 바뀌는지가 이 흐름의 뼈대다. 아래는 인덱스가 하나 있는 테이블에서 한 행을 두 번 UPDATE 하고(HOT 이 아닌 경우), 그 두 트랜잭션이 모두 OldestXmin 보다 오래된 경우다.

```text
 page 7, 인덱스 1 개 (버전마다 인덱스 항목이 있다), v1 과 v2 를 지운 트랜잭션은 OldestXmin 보다 오래 전에 커밋

 step               lp1        lp2        lp3        무엇이 바뀌나
 before VACUUM      NORMAL     NORMAL     NORMAL     v1, v2 는 죽은 버전, v3 가 살아 있는 버전
 [10] prune         DEAD       DEAD       NORMAL     v1, v2 의 튜플 공간을 회수, dead_items += (7,1), (7,2)
 [11] index vacuum  DEAD       DEAD       NORMAL     인덱스에서 (7,1), (7,2) 를 가리키는 항목을 지운다
 [12] heap pass 2   UNUSED     UNUSED     NORMAL     lp1, lp2 를 새 행이 다시 쓸 수 있다
                                                     v3 가 모두에게 보이면 visibility map 에 all-visible

 [10] 이 바로 UNUSED 로 만들지 못하는 이유 (vacuumlazy.c L1177-L1187 주석)
   인덱스가 아직 (7,1) 을 가리키는데 lp1 이 재사용되면, 인덱스 스캔이 엉뚱한 새 행에 닿는다
   인덱스가 없는 테이블이면 이 걱정이 없어서 prune 에서 바로 UNUSED (HEAP_PAGE_PRUNE_MARK_UNUSED_NOW)
```

`lazy_scan_heap` 은 이 세 단계를 dead_items 저장소 크기에 맞춰 반복한다. 저장소가 차면 힙 스캔을 멈추고 인덱스와 힙 2차 정리를 한 바퀴 돌린 뒤 이어서 스캔한다.

```text
 dead_items 가 TID 를 다 담을 때
   scan heap        [0 ........................ N)
   vacuum indexes   모든 인덱스를 처음부터 끝까지 1 번       L1542 lazy_vacuum
   vacuum heap      dead TID 가 있는 페이지만
   cleanup indexes                                           L1558

 dead_items 가 k 번째 페이지에서 찼을 때 (L1279)
   scan heap        [0 ...... k)
   vacuum indexes   전체 1 번                                L1295 lazy_vacuum
   vacuum heap      [0, k) 중 dead TID 가 있는 페이지
   scan heap        [k ...... N)
   vacuum indexes   전체를 또 1 번                           L1542 lazy_vacuum
   vacuum heap      [k, N) 중 dead TID 가 있는 페이지
   cleanup indexes

 인덱스는 lazy_vacuum 이 불릴 때마다 처음부터 끝까지 읽는다 (L1189-L1197 주석)
```

## 어디에서 쓰이는가

```text
 수동 VACUUM
   standard_ProcessUtility -> ExecVacuum                    tcop/utility.c L862

 autovacuum
   launcher -> PMSIGNAL_START_AUTOVAC_WORKER -> postmaster StartAutovacuumWorker (postmaster.c L3783)
   worker   -> do_autovacuum -> autovacuum_do_vac_analyze -> vacuum()   autovacuum.c L3196

 같은 prune 을 쓰는 곳 (VACUUM 이 아닌 일반 읽기)
   heap_prepare_pagescan -> heap_page_prune_opt (heapam.c L576)
     -> heap_page_prune_and_freeze(options = 0)     pruneheap.c L263
     freeze 와 dead_items 수집 없이 페이지 안 정리만 한다
```

## db-engine 에서는

db-engine 에는 이 흐름에 대응하는 기능이 없다. MVCC 를 만든 챕터 두 곳이 그 사실을 직접 적어 두었다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 옛 버전이 쌓이는 곳
   PostgreSQL  힙 페이지 안. UPDATE 마다 새 튜플, 옛 튜플은 xmax 가 찍힌 채 남는다
   db-engine   MVCCStore 의 chains: ConcurrentHashMap<K, MutableList<Version<V>>>  (메모리)

 누가 언제 치우나
   PostgreSQL  VACUUM / autovacuum 이 OldestXmin 보다 오래 죽은 버전을 지운다
               일반 읽기도 heap_page_prune_opt 로 페이지 안을 정리한다
   db-engine   치우는 주체가 없다. 버전 목록은 늘기만 한다

 그 결과
   PostgreSQL  공간이 재사용된다. 대신 OldestXmin 을 붙잡는 오래된 트랜잭션이 있으면 못 치운다
   db-engine   읽기가 버전 목록을 뒤에서부터 선형 탐색 - 갱신 횟수만큼 느려진다
```

impl/10-01-mvcc.md 는 과제 3번 답에서 PostgreSQL 의 VACUUM 과 InnoDB 의 purge 를 설명한 뒤 L267 에 "우리 코드에는 정리 기능이 아예 없다"고 적었고, impl/10-03-mvcc-table-heap.md 는 `MVCCTableHeap` 클래스 주석의 한계 목록(L58)에 "학습 데모 — vacuum 없음, version chain 누적"을 적었다. 그래서 이 흐름은 db-engine 과 일대일로 비교할 코드가 없고, 대신 db-engine 의 선형 탐색 비용(10-01 과제 3번)이 이 흐름이 없을 때 생기는 문제의 모습이다. 챕터: [10-01-mvcc](../../../../../project/db-engine/10-01-mvcc/), [10-03-mvcc-table-heap](../../../../../project/db-engine/10-03-mvcc-table-heap/).

## 단계

1. [ExecVacuum](01_ExecVacuum/README.md)이 VACUUM 옵션을 `VacuumParams` 로 바꾸고 ring buffer 전략을 만든다.
2. [vacuum](02_vacuum/README.md)이 대상 테이블 목록을 만들고, 바깥 트랜잭션을 끊고 테이블마다 `vacuum_rel` 을 부른다.
3. [AutoVacLauncherMain](03_AutoVacLauncherMain/README.md)이 naptime 마다 DB 를 골라 postmaster 에 worker 를 요청한다.
4. [do_autovacuum](04_do_autovacuum/README.md)이 worker 안에서 pg_class 를 훑어 임계값을 넘은 테이블을 `vacuum()` 에 넘긴다.
5. [vacuum_rel](05_vacuum_rel/README.md)이 테이블 하나를 트랜잭션 하나로 열고 잠근 뒤 테이블 AM 의 vacuum 을 부르고, TOAST 테이블로 재귀한다.
6. [heap_vacuum_rel](06_heap_vacuum_rel/README.md)이 cutoff 를 계산하고 dead_items 를 할당한 뒤 세 단계를 돌리고 pg_class 를 갱신한다.
7. [vacuum_get_cutoffs](07_vacuum_get_cutoffs/README.md)가 OldestXmin, FreezeLimit 을 계산하고 이번 VACUUM 이 aggressive 인지 정한다.
8. [lazy_scan_heap](08_lazy_scan_heap/README.md)이 visibility map 으로 건너뛸 페이지를 고르며 힙을 한 번 훑는다.
9. [lazy_scan_prune](09_lazy_scan_prune/README.md)이 페이지 하나를 prune·freeze 하고 dead TID 를 모으고 visibility map 을 켠다.
10. [heap_page_prune_and_freeze](10_heap_page_prune_and_freeze/README.md)가 튜플마다 DEAD/RECENTLY_DEAD 를 판정하고 HOT 체인을 정리하고 얼린다.
11. [lazy_vacuum](11_lazy_vacuum/README.md)이 인덱스 정리를 건너뛸지 정하고, 인덱스마다 ambulkdelete 로 dead TID 를 지운다.
12. [lazy_vacuum_heap_rel](12_lazy_vacuum_heap_rel/README.md)이 dead TID 가 있는 힙 페이지만 다시 찾아가 LP_DEAD 를 LP_UNUSED 로 바꾼다.
13. [vac_update_relstats](13_vac_update_relstats/README.md)가 pg_class 를 제자리 갱신하고, `vac_update_datfrozenxid` 가 DB 단위 최소값을 올린다.

## 결과가 쓰이는 곳

```text
 LP_UNUSED 가 된 줄 포인터, FSM 의 빈 공간
      --> 다음 INSERT/UPDATE 가 RelationGetBufferForTuple 에서 이 페이지를 고른다
          ([행 쓰기와 WAL 기록 04](../heap-insert-wal/04_RelationGetBufferForTuple/README.md))

 visibility map 의 all-visible / all-frozen
      --> index-only scan 이 힙을 읽지 않고 넘어간다 (executor/nodeIndexonlyscan.c L162)
      --> 다음 VACUUM 이 페이지를 건너뛴다 ([08])

 pg_class.relfrozenxid, pg_database.datfrozenxid
      --> autovacuum 의 wraparound 강제 판정 (relation_needs_vacanalyze, do_start_worker)
      --> vac_truncate_clog 가 pg_xact 의 오래된 세그먼트를 지운다

 pg_class.reltuples, relpages, relallvisible
      --> 플래너의 행 수 추정과 index-only scan 비용
```

## 다루지 않는 것

`VACUUM FULL`(`cluster_rel` 로 테이블을 새로 쓴다), `ANALYZE`(`analyze_rel`), 병렬 인덱스 vacuum(`vacuumparallel.c`), wraparound failsafe 의 세부(`lazy_check_wraparound_failsafe`), eager scan 알고리즘(`heap_vacuum_eager_scan_setup`), 비용 기반 지연(`vacuum_delay_point`), 힙 끝 잘라내기(`lazy_truncate_heap`), MultiXact freeze 는 이름만 짚었다. B-tree 의 bulk delete 내부(`btbulkdelete`, `btvacuumscan`)는 인덱스 쪽 흐름의 몫이다.

## 하위 메서드

- [01 ExecVacuum](01_ExecVacuum/README.md)
- [02 vacuum](02_vacuum/README.md)
- [03 AutoVacLauncherMain](03_AutoVacLauncherMain/README.md)
- [04 do_autovacuum](04_do_autovacuum/README.md)
- [05 vacuum_rel](05_vacuum_rel/README.md)
- [06 heap_vacuum_rel](06_heap_vacuum_rel/README.md)
- [07 vacuum_get_cutoffs](07_vacuum_get_cutoffs/README.md)
- [08 lazy_scan_heap](08_lazy_scan_heap/README.md)
- [09 lazy_scan_prune](09_lazy_scan_prune/README.md)
- [10 heap_page_prune_and_freeze](10_heap_page_prune_and_freeze/README.md)
- [11 lazy_vacuum](11_lazy_vacuum/README.md)
- [12 lazy_vacuum_heap_rel](12_lazy_vacuum_heap_rel/README.md)
- [13 vac_update_relstats](13_vac_update_relstats/README.md)
