# 페이지 플러시, doublewrite, 체크포인트

상위: [MySQL 아키텍처 지도](../../README.md)

[mini-transaction과 redo 기록](../mtr-redo/README.md)이 flush list 에 남긴 dirty 페이지를 **백그라운드 스레드가 디스크에 쓰고, 그만큼 redo 를 버릴 수 있게 checkpoint LSN 을 앞으로 옮기는** 흐름이다. 두 무리의 스레드가 따로 돈다. page cleaner(코디네이터 하나와 워커들)는 버퍼 풀 인스턴스마다 LRU 꼬리와 flush list 꼬리에서 페이지를 골라 쓰고, log_checkpointer 는 "아직 디스크에 없는 가장 오래된 변경"을 계산해 redo 파일 헤더에 checkpoint 를 적는다. 둘 사이에 호출은 거의 없고 값만 오간다. page cleaner 가 flush list 를 비우면 checkpointer 가 그것을 읽고, checkpointer 가 redo 가 모자라다고 보면 `buf_flush_event` 로 page cleaner 를 재촉한다. 페이지 한 장의 쓰기에는 두 가지 순서 규칙이 걸린다. 쓰기 전에 그 페이지의 redo 가 먼저 디스크에 있어야 하고(WAL), doublewrite 가 켜져 있으면 데이터 파일보다 doublewrite 파일에 먼저 쓴다. 쓰기 완료는 IO 완료 콜백(`buf_page_io_complete`)에서 처리되므로 쓰기를 낸 스레드와 끝내는 스레드가 다르다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 page cleaner 코디네이터 스레드 (buf0flu.cc)
 ------------------------------------------------------------------
 [01] buf_flush_page_coordinator_thread                  L2875
      +-- 워커 스레드 생성 (1 .. n-1, 0 번은 자기 자신)      L2898-L2903
      +-- while (종료 전)                                    L2956
            +-- pc_sleep_if_needed (최대 1초)                L2982
            +-- log_sync_flush_lsn -> is_sync_flush          L3035  redo 가 모자라면 lsn_limit
            +-- log_write_up_to(ready_lsn, true)             L3056  1초마다 redo 를 먼저 내려 둔다
            +-- Adaptive_flush::page_recommendation          L3069, L3076  몇 장 쓸지
            +-- pc_request(n_to_flush, lsn_limit)            L3085  슬롯 = 버퍼 풀 인스턴스
            +-- while (pc_flush_slot() > 0)                  L3090  코디네이터도 한 몫 한다
            +-- pc_wait_finished                             L3105
 ------------------------------------------------------------------
      page_cleaner->is_requested (워커가 깨어나 슬롯을 하나씩 가져간다)
 ------------------------------------------------------------------
 코디네이터 또는 워커, 슬롯 하나 = 버퍼 풀 인스턴스 하나
 [02] pc_flush_slot                                      L2627
      +-- buf_flush_LRU_list(buf_pool)                   L2670  꼬리 쪽 clean 은 free 로, dirty 는 쓰기
      +-- [03] buf_flush_do_batch(BUF_FLUSH_LIST, n, lsn_limit)   L2682
            +-- buf_do_flush_list_batch                  L1635  flush list 꼬리부터 oldest < lsn_limit
            |     +-- buf_flush_page_and_try_neighbors -> buf_flush_try_neighbors
            |           +-- [04] buf_flush_page          L1338  io_fix = WRITE, SX 래치
            |                 +-- [05] buf_flush_write_block_low   L1139
            |                       +-- log_write_up_to(newest_lsn, true)  L966   WAL
            |                       +-- buf_flush_init_for_writing         L998   FIL_PAGE_LSN, 체크섬
            |                       +-- [06] dblwr::write                  L1007
            |                             +-- [07] Double_write::submit  (buf0dblwr.cc L669)
            |                                   enqueue, 배치가 차면
            |                                   doublewrite 파일 write + fsync -> 데이터 파일 AIO
            +-- buf_flush_end -> dblwr::force_flush      L1766  남은 배치를 마저 내보낸다
 ------------------------------------------------------------------
      IO 완료 (AIO 핸들러 스레드)
 ------------------------------------------------------------------
 buf_page_io_complete -> buf_flush_write_complete        buf0buf.cc L6050, buf0flu.cc L668
      +-- buf_flush_remove     flush list 에서 빼고 oldest = 0
      +-- dblwr::write_complete  배치의 마지막 페이지면 fil_flush_file_spaces 후 세그먼트 반납

 log_checkpointer 스레드 (log0chkp.cc)
 ------------------------------------------------------------------
 [08] log_checkpointer                                   L904
      +-- log_consider_sync_flush                        L936   모자라면 page cleaner 를 재촉
      +-- log_consider_checkpoint                        L941
            +-- log_should_checkpoint                    L875   1초마다, 또는 age 가 크면
            +-- [09] log_checkpoint                      L901
                  +-- log_determine_checkpoint_lsn       L457   available_for_checkpoint_lsn
                  +-- buf_flush_fsync                    L465   데이터 파일 fsync
                  +-- [10] log_files_next_checkpoint     L492
                        +-- checkpoint 헤더 write + fsync          L375, L385
                        +-- last_checkpoint_lsn.store              L394
                        +-- m_files_governor_event                 L371  옛 파일 재사용 --> governor
```

checkpoint LSN 이 정해지는 식은 하나다. 세 값 가운데 가장 작은 것이고, 이전 checkpoint 보다 뒤로 가지는 않는다.

```text
 checkpoint LSN 을 정하는 세 상한 (log_compute_available_for_checkpoint_lsn, log0chkp.cc L181)

   lsn = min( oldest_lwm,  smallest_not_added_lsn,  flushed_to_disk_lsn )
         oldest_lwm = 모든 flush list 꼬리의 oldest_modification 최솟값 - order_lag
   lsn = max( lsn, last_checkpoint_lsn )

 ----+--------------+------------------+-------------+----------------+------> lsn
     |              |                  |             |                |
  last_checkpoint  oldest_lwm        smallest_      flushed_to_     current lsn
  (이미 적힌 값)   (아직 안 쓴 가장   not_added_lsn  disk_lsn        (log.sn)
                   오래된 변경)      (flush list 에
                                     아직 안 붙은 mtr)
     |<-- 여기까지 redo 를 버릴 수 있다 -->|
         new checkpoint = oldest_lwm (이 그림에서는 가장 작은 값)

 [10] 이 이 값을 헤더에 적으면 그 앞의 redo 파일은 governor 가 소비됨으로 표시하고
 재사용하거나 지운다
```

## 어디에서 쓰이는가

```text
 [mini-transaction과 redo 기록]  flush list, oldest / newest_modification, buf_flush_list_added,
                                 flushed_to_disk_lsn 을 이 흐름이 소비한다
                                 log_writer 는 checkpoint 가 막히면 쓰기를 멈춘다
 [버퍼 풀 페이지 획득]           free 가 모자라면 buf_LRU_get_free_block 이
                                 buf_flush_single_page_from_LRU 로 직접 한 장 쓴다 (buf0lru.cc L1424)
 [크래시 복구]                   checkpoint 헤더의 lsn 에서 redo 를 다시 읽고,
                                 찢어진 페이지는 doublewrite 사본으로 되살린다 (buf0dblwr.cc L3022)
```

앞 흐름은 [mini-transaction과 redo 기록](../mtr-redo/README.md), 다음 흐름은 [크래시 복구](../crash-recovery/README.md)다. page cleaner 와 log 스레드를 한 자리에서 보는 그림은 [스레드 구성](../../structure/threads/README.md)에 둔다.

## db-engine 에서는

db-engine 의 checkpoint 는 dirty 페이지와 연결되지 않은 "LSN 스냅샷 레코드"다. MySQL 에서 checkpoint LSN 을 정하는 재료(가장 오래된 dirty 페이지)가 db-engine 에는 없다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 checkpoint 가 적는 것
   MySQL      redo 파일 헤더 두 칸 중 하나에 checkpoint_lsn 하나 (HEADER_1 / HEADER_2 번갈아)
   db-engine  WAL 안에 Checkpoint(checkpointLsn, activeTxs) 레코드를 append 하고 sync

 checkpoint LSN 을 무엇으로 정하나
   MySQL      min(flush list 의 가장 오래된 oldest_modification - lag,
                  smallest_not_added_lsn, flushed_to_disk_lsn)
   db-engine  CheckpointManager.checkpoint 호출 시점의 logManager.currentLsn()

 checkpoint 전에 페이지를 쓰나
   MySQL      page cleaner 가 계속 쓰고, checkpoint 는 이미 쓴 만큼만 앞으로 간다
              checkpoint 직전 buf_flush_fsync 로 데이터 파일을 fsync
   db-engine  페이지 flush 와 묶여 있지 않다. Recovery 는 Checkpoint 레코드를 무시한다

 로그를 버리나
   MySQL      checkpoint 앞의 redo 파일을 governor 가 재사용하거나 지운다
   db-engine  버리지 않는다. 재적용을 막는 것은 recovery.meta 의 lastAppliedLsn

 찢어진 페이지
   MySQL      doublewrite 파일에 먼저 쓰고 복구 때 사본으로 되살린다
   db-engine  다루지 않는다
```

db-engine 은 멱등성을 "어디까지 적용했나"를 적은 별도 파일로 얻는다. MySQL 은 같은 역할을 페이지마다 찍힌 `FIL_PAGE_LSN` 이 하고, 로그를 버릴 수 있는 지점은 dirty 페이지가 정한다. impl 문서가 "다음 한계"로 남긴 crash 시뮬레이션은 08-03 에 있다. 챕터: [08-02-lsn-checkpoint](../../../../../project/db-engine/08-02-lsn-checkpoint/).

## 단계

1. [buf_flush_page_coordinator_thread](01_buf_flush_page_coordinator_thread/README.md)가 1초 주기로 몇 장을 어디까지 쓸지 정하고 워커에게 나눠 준다.
2. [pc_flush_slot](02_pc_flush_slot/README.md)이 버퍼 풀 인스턴스 하나를 맡아 LRU 배치와 flush list 배치를 돈다.
3. [buf_flush_do_batch](03_buf_flush_do_batch/README.md)가 배치를 열고, flush list 꼬리부터 고르고, 닫으면서 doublewrite 를 비운다.
4. [buf_flush_page](04_buf_flush_page/README.md)가 페이지에 쓰기 IO 고정을 걸고 SX 래치를 잡는다.
5. [buf_flush_write_block_low](05_buf_flush_write_block_low/README.md)가 redo 를 먼저 맞추고 페이지에 LSN 과 체크섬을 찍는다.
6. [dblwr.write](06_dblwr.write/README.md)가 doublewrite 를 탈지, 비동기 배치인지 동기 단일인지 가른다.
7. [Double_write.submit](07_Double_write.submit/README.md)이 배치에 쌓았다가 doublewrite 파일, 데이터 파일 순서로 쓴다.
8. [log_checkpointer](08_log_checkpointer/README.md)가 동기 flush 가 필요한지, checkpoint 를 쓸 때인지 본다.
9. [log_checkpoint](09_log_checkpoint/README.md)가 checkpoint LSN 을 정하고 데이터 파일을 fsync 한다.
10. [log_files_next_checkpoint](10_log_files_next_checkpoint/README.md)가 헤더에 적고 redo 공간을 돌려준다.

## 결과가 쓰이는 곳

```text
 디스크의 데이터 페이지 (FIL_PAGE_LSN = newest_modification)
      --> 복구가 레코드를 적용할지 이 값으로 가른다        [크래시 복구]

 doublewrite 파일의 사본
      --> 복구 초기에 찢어진 데이터 페이지를 덮어쓴다      [크래시 복구]

 last_checkpoint_lsn
      --> 복구의 출발점                                     [크래시 복구]
      --> log_writer 의 hard_limited_lsn = checkpoint + capacity  [mtr-redo 09]
      --> governor 가 그 앞의 redo 파일을 consumed 로 표시

 free list 의 빈 블록 (LRU 배치의 결과)
      --> buf_LRU_get_free_block 이 가져간다               [버퍼 풀 페이지 획득]
```

## 다루지 않는 것

adaptive flushing 의 계산식(`Adaptive_flush::page_recommendation`, `lsn_avg_rate`, `innodb_io_capacity`), 이웃 페이지 flush(`buf_flush_try_neighbors` 와 `innodb_flush_neighbors`), 압축 페이지와 `unzip_LRU`, reduced doublewrite(`DETECT_ONLY`, `.bdblwr` 파일), 레거시 v1 doublewrite(시스템 테이블스페이스 안), 페이지 아카이브(`arch_page_sys`), 복구 중의 flush 요청 처리(L2905-L2943), 종료 단계별 flush 루프, `log_files_governor` 의 파일 생성과 재사용 세부, sharp checkpoint(`log_make_latest_checkpoint`)는 요약만 했다.

## 하위 메서드

- [01 buf_flush_page_coordinator_thread](01_buf_flush_page_coordinator_thread/README.md)
- [02 pc_flush_slot](02_pc_flush_slot/README.md)
- [03 buf_flush_do_batch](03_buf_flush_do_batch/README.md)
- [04 buf_flush_page](04_buf_flush_page/README.md)
- [05 buf_flush_write_block_low](05_buf_flush_write_block_low/README.md)
- [06 dblwr.write](06_dblwr.write/README.md)
- [07 Double_write.submit](07_Double_write.submit/README.md)
- [08 log_checkpointer](08_log_checkpointer/README.md)
- [09 log_checkpoint](09_log_checkpoint/README.md)
- [10 log_files_next_checkpoint](10_log_files_next_checkpoint/README.md)
