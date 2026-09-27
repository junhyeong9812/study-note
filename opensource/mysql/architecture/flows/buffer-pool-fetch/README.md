# 버퍼 풀 페이지 획득

상위: [MySQL 아키텍처 지도](../../README.md)

InnoDB 안의 모든 코드가 페이지 하나를 손에 넣을 때 지나는 길이다. `(space_id, page_no)` 로 page hash 를 찾아 **적중하면 buf-fix 를 걸고 바로 돌려주고**, 미적중이면 free list 에서 빈 frame 을 얻어 디스크에서 읽은 뒤 다시 찾는다. 흐름은 `buf_page_get_gen` 이 호출자에게 **buf-fix 와 요청한 래치가 걸린 `buf_block_t`** 를 돌려주고, 그 사실을 mini-transaction 의 memo 에 올리는 데서 끝난다. 동기 읽기(`buf_read_page`)는 호출한 스레드가 직접 I/O 를 기다리지만, read-ahead 로 들어간 비동기 읽기는 I/O 핸들러 스레드가 `buf_page_io_complete` 로 끝낸다. 그래서 이 흐름에는 **"읽는 중(BUF_IO_READ)" 페이지를 다른 스레드가 기다리는 자리**가 있고, 그 대기는 frame 의 X 래치를 거쳐 이루어진다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 호출자 스레드 (예: btr_cur_search_to_nth_level, btr0cur.cc L958)
 ------------------------------------------------------------------
 [01] buf_page_get_gen                                         L4449
      +-- mode == NORMAL 이고 임시 테이블스페이스가 아니면     L4488
      |     Buf_fetch_normal 로, 아니면 Buf_fetch_other 로
      +-- [02] Buf_fetch::single_page                          L4299
            +-- for (;;)                                       L4304
            |     +-- [04] Buf_fetch_normal::get               L4305 -> L3713
            |     |     +-- for (;;)                           L3715
            |     |           +-- [03] lookup                  L3722  guess -> page hash
            |     |           |     적중: buf_block_fix        L3737  hash S 락 해제, break
            |     |           +-- 미적중: [05] read_page       L3745  읽고 다시 lookup
            |     |                 +-- buf_read_page          L4118  (buf0rea.cc L288)
            |     |                       +-- [06] buf_read_page_low   buf0rea.cc L66
            |     |                             +-- [07] buf_page_init_for_read  L4880
            |     |                             |     +-- [08] buf_LRU_get_free_block  buf0lru.cc L1311
            |     |                             |     +-- page hash 에 넣고 IO_READ, X 래치
            |     |                             |     +-- [10] buf_LRU_add_block(old=true)  L4979
            |     |                             +-- fil_io (sync)          buf0rea.cc L127
            |     |                             +-- buf_page_io_complete   buf0rea.cc L145
            |     +-- check_state                              L4330  압축 전용이면 풀어서 옮긴다
            +-- 첫 접근이면 access_time 기록                    L4392
            +-- [09] buf_page_make_young_if_needed              L4403  (PEEK, SCAN 제외)
            |     +-- buf_page_peek_if_too_old 이면 LRU 머리로   L3217
            +-- buf_wait_for_read                               L4414  남이 읽는 중이면 기다린다
            +-- mtr_add_page                                    L4427  래치를 걸고 mtr memo 에
            +-- 첫 접근이면 buf_read_ahead_linear               L4434

 [01] [02] [03] [04] [05] [07] [09] 의 줄은 buf0buf.cc,
 [06] 은 buf0rea.cc, [08] [10] 은 buf0lru.cc 의 줄이다
```

페이지 하나에는 두 종류의 "붙잡음"이 따로 있다. 이 흐름을 읽는 열쇠는 둘을 구분하는 것이다.

```text
 buf-fix 와 래치 (buf_block_t 하나에 둘 다 있다)

 붙잡음          필드                          거는 곳                    막는 것
 buf-fix         page.buf_fix_count            [04] L3737 buf_block_fix   교체(evict)와 relocate
 page latch      block->lock (rw_lock_t)       [02] mtr_add_page L4427    다른 스레드의 읽기, 쓰기
 io-fix          page.io_fix = BUF_IO_READ     [07] L4976                 읽는 중인 frame 사용

 buf-fix 는 page hash S 락 안에서 건다. 그래서 hash 락을 놓은 뒤에도
   이 블록이 LRU 에서 쫓겨나거나 다른 페이지로 바뀌지 않는다
 래치는 buf-fix 를 건 뒤, hash 락 없이 건다
 io-fix 가 READ 인 동안은 읽은 스레드가 X 래치를 들고 있다 (L5004)
   남은 기다리려면 S 래치를 한 번 잡았다 놓으면 된다 (buf_wait_for_read L3606)
```

LRU 리스트는 한 줄이지만 `LRU_old` 포인터가 그것을 young 과 old 두 구간으로 나눈다. 디스크에서 막 읽은 페이지는 머리가 아니라 **old 구간의 머리(midpoint)** 에 들어간다.

```text
 buf_pool->LRU (innodb_old_blocks_pct 기본 37, ha_innodb.cc L23114)

   머리 (MRU)                                                    꼬리 (LRU)
   [y][y][y][y][y][y][y][y][y][y][y][y][o][o][o][o][o][o][o][o][o][o]
   <---------- young 약 5/8 ----------> ^ <------ old 약 3/8 ------->
                                        |
                                    LRU_old (old=true 인 첫 블록)

   read in      buf_LRU_add_block(bpage, true)  -> LRU_old 바로 뒤 (buf0lru.cc L1678)
   make_young   buf_LRU_make_block_young         -> 머리 (L1736, add_block_low(false))
   evict scan   lru_scan_itr.start()             -> 꼬리부터 (buf0buf.cc L2972)

   LRU 길이가 BUF_LRU_OLD_MIN_LEN(512) 보다 짧으면 old 구간이 없고
   모두 머리에 넣는다 (buf0lru.cc L1664)
```

## 어디에서 쓰이는가

```text
 [B+Tree 삽입과 분할]   btr_cur_search_to_nth_level 이 레벨마다 buf_page_get_gen 을 부른다
                        루트는 index->search_info->root_guess 를 guess 로 넘긴다 (btr0cur.cc L958-L961)
 [일관 읽기(MVCC)]      row_search_mvcc 의 커서 이동과 undo 페이지 읽기
 [mini-transaction]     mtr_add_page 가 올린 memo 가 mtr_t::commit 에서 래치를 풀고
                        dirty 페이지를 flush list 에 붙인다
 [크래시 복구]          복구 중 읽은 페이지는 buf_page_io_complete 에서
                        recv_recover_page 로 redo 가 적용된다 (buf0buf.cc L5960)
 [페이지 플러시]        free list 가 비면 buf_flush_single_page_from_LRU 로 한 장을 쓰고 비운다
```

연결 흐름: [B+Tree 삽입과 분할](../btree-insert/README.md), [일관 읽기(MVCC)와 undo 체인](../mvcc-read/README.md), [mini-transaction과 redo 기록](../mtr-redo/README.md), [크래시 복구](../crash-recovery/README.md), [페이지 플러시, doublewrite, 체크포인트](../flush-checkpoint/README.md). 자료구조는 [메모리 구조](../../structure/memory-structures/README.md)에 모아 둔다.

## db-engine 에서는

db-engine 은 같은 문제(캐시 적중, 교체 대상 고르기, 쓰는 중 교체 막기)를 `LinkedHashMap` 하나와 `pinCount` 하나로 풀었다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 찾기
   MySQL      page_hash (셀별 rw_lock) + guess 블록. 인스턴스는 page_no>>6 해시로 고른다
   db-engine  pages: LinkedHashMap<PageId, Page>(capacity, 0.75f, true)

 적중
   MySQL      buf_block_fix 로 buf_fix_count++, 래치는 따로 mtr_add_page 에서
   db-engine  cached.pin() 후 반환. 래치 없음 (동시성은 단계 9로 미룸)

 미적중
   MySQL      free list 에서 frame -> page hash 에 먼저 등록(IO_READ) -> 읽기
              같은 페이지를 동시에 찾는 스레드는 등록된 블록을 보고 기다린다
   db-engine  자리가 없으면 evictOne() -> pagedFile.readPage(id) -> pages[id] = loaded

 교체 대상
   MySQL      LRU 꼬리부터 buf_flush_ready_for_replace 인 블록. dirty 면 건너뛰고
              안 되면 buf_flush_single_page_from_LRU 로 한 장을 써서 비운다
   db-engine  pages.values.firstOrNull { it.pinCount == 0 }, dirty 면 그 자리에서 writePage
              없으면 StorageError.AllPagesPinned

 순서 정책
   MySQL      midpoint insertion. 새 페이지는 old 구간, 오래 머문 뒤 다시 쓰일 때만 young
   db-engine  access-order LinkedHashMap. get() 한 번이면 가장 뒤(최근)로 간다
```

db-engine 의 access-order LRU 는 한 번 훑고 지나가는 큰 스캔이 캐시 전체를 밀어낸다. MySQL 은 이것을 막으려고 새 페이지를 old 구간에 넣고, `innodb_old_blocks_time`(기본 1000ms) 이 지나기 전의 재접근은 young 으로 올리지 않는다(buf0buf.ic L188-L199). 반면 db-engine 은 교체 대상이 dirty 면 호출자 스레드가 곧바로 쓰고, MySQL 은 dirty 블록을 교체 후보에서 빼고 플러시 쪽에 맡긴다. 챕터: [02-01-page-pagedfile](../../../../../project/db-engine/02-01-page-pagedfile/), [02-02-buffer-pool](../../../../../project/db-engine/02-02-buffer-pool/).

## 단계

1. [buf_page_get_gen](01_buf_page_get_gen/README.md)이 모드를 보고 일반 경로와 그 밖의 경로 중 하나를 고른다.
2. [Buf_fetch.single_page](02_Buf_fetch.single_page/README.md)가 블록을 얻은 뒤 접근 시각, LRU 위치, 래치, read-ahead 를 처리한다.
3. [Buf_fetch.lookup](03_Buf_fetch.lookup/README.md)이 guess 블록과 page hash 로 블록을 찾는다.
4. [Buf_fetch_normal.get](04_Buf_fetch_normal.get/README.md)이 적중할 때까지 찾기와 읽기를 되풀이한다.
5. [Buf_fetch.read_page](05_Buf_fetch.read_page/README.md)가 동기 읽기를 걸고 random read-ahead 를 시도한다.
6. [buf_read_page_low](06_buf_read_page_low/README.md)가 블록을 준비하고 `fil_io` 로 읽는다.
7. [buf_page_init_for_read](07_buf_page_init_for_read/README.md)가 빈 블록을 page hash 와 LRU 에 먼저 올리고 IO_READ 로 잠근다.
8. [buf_LRU_get_free_block](08_buf_LRU_get_free_block/README.md)이 free list, LRU 꼬리 스캔, 한 장 플러시 순으로 빈 블록을 만든다.
9. [buf_page_make_young_if_needed](09_buf_page_make_young_if_needed/README.md)가 오래된 페이지만 LRU 머리로 옮긴다.
10. [buf_LRU_add_block](10_buf_LRU_add_block/README.md)이 블록을 young 머리나 old 머리에 넣고 `LRU_old` 를 맞춘다.

## 결과가 쓰이는 곳

```text
 buf_block_t (buf-fix + 래치)
      --> 호출자가 block->frame 으로 페이지 내용을 읽고 쓴다
      --> mtr memo 에 MTR_MEMO_PAGE_S_FIX / SX_FIX / X_FIX / BUF_FIX 로 올라
          mtr_t::commit 이 한꺼번에 푼다

 LRU 위치와 freed_page_clock
      --> 다음 buf_page_peek_if_young 판정의 기준이 된다
      --> LRU 꼬리 스캔이 교체 대상을 고를 때 순서가 된다

 통계 (buf_pool->stat)
      --> m_n_page_gets, n_pages_read, n_pages_made_young, n_pages_not_made_young
          SHOW ENGINE INNODB STATUS 와 INNODB_BUFFER_POOL_STATS 의 재료
```

## 다루지 않는 것

압축 페이지의 `zip_page_handler`(unzip_LRU 와 buddy 할당), `Buf_fetch_other` 의 watch(`IF_IN_POOL_OR_WATCH`, change buffer 용), 임시 테이블스페이스의 `temp_space_page_handler`, stale 페이지 정리(`buf_page_free_stale`), read-ahead 의 판정 규칙(`buf_read_ahead_random`, `buf_read_ahead_linear`), 비동기 I/O 완료 쪽의 체크섬 검사 세부(`buf_page_io_complete` 의 `BlockReporter`), 적응형 해시 인덱스(AHI), 버퍼 풀 크기 조정(withdraw), `buf_page_optimistic_get` 은 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 buf_page_get_gen](01_buf_page_get_gen/README.md)
- [02 Buf_fetch.single_page](02_Buf_fetch.single_page/README.md)
- [03 Buf_fetch.lookup](03_Buf_fetch.lookup/README.md)
- [04 Buf_fetch_normal.get](04_Buf_fetch_normal.get/README.md)
- [05 Buf_fetch.read_page](05_Buf_fetch.read_page/README.md)
- [06 buf_read_page_low](06_buf_read_page_low/README.md)
- [07 buf_page_init_for_read](07_buf_page_init_for_read/README.md)
- [08 buf_LRU_get_free_block](08_buf_LRU_get_free_block/README.md)
- [09 buf_page_make_young_if_needed](09_buf_page_make_young_if_needed/README.md)
- [10 buf_LRU_add_block](10_buf_LRU_add_block/README.md)
