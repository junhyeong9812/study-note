# B+Tree 삽입과 분할

상위: [MySQL 아키텍처 지도](../../README.md)

인덱스 엔트리 하나가 **B+Tree 의 알맞은 리프 자리를 찾아 레코드로 들어가기까지**의 흐름이다. 한 번의 시도는 mini-transaction(mtr) 하나다. [01] `row_ins_clust_index_entry_low` 가 mtr 을 열고, [02] 가 루트에서 리프까지 래치를 잡으며 내려가 커서를 "삽입할 자리 바로 앞 레코드"에 세운다. 그 자리에서 **optimistic 삽입**([03])은 페이지 하나 안에서 끝내고, 자리가 모자라면 `DB_FAIL` 로 물러난다. 호출자가 트리 래치를 잡고 다시 부르면 **pessimistic 삽입**([07])이 페이지를 둘로 나누거나([08]) 루트를 한 층 올린다([09]). 두 경로 모두 레코드를 쓰기 직전에 [04] `btr_cur_ins_lock_and_undo` 를 지나며, 여기서 [레코드 잠금](../record-lock/README.md)과 undo 기록([일관 읽기(MVCC)](../mvcc-read/README.md)의 재료)으로 갈라진다. 페이지 안의 실제 쓰기는 [05] [06] 이 하고, 그 변경은 mtr 이 커밋될 때 [mini-transaction과 redo 기록](../mtr-redo/README.md)으로 넘어간다. 스레드 경계는 없다.

기준 태그: mysql-9.7.2 [`008e09c283`](https://github.com/mysql/mysql-server/tree/008e09c2834b98143a8c067d4d225c90953050cf). 모든 줄 번호는 이 태그 기준이다.

## 전체 그림

```text
 [행 쓰기] row_ins_clust_index_entry (row0ins.cc L3119)
   mode = BTR_MODIFY_LEAF 로 한 번, DB_FAIL 이면 BTR_MODIFY_TREE 로 한 번 더
      v
 [01] row_ins_clust_index_entry_low                       row0ins.cc L2399
      +-- mtr.start                                       L2439
      +-- pcur.open(PAGE_CUR_LE, mode)                    L2461
      |     +-- [02] btr_cur_search_to_nth_level          btr0cur.cc L619
      |           루트부터 buf_page_get_gen 으로 한 층씩   --> [버퍼 풀 페이지 획득]
      |           page_cur_search_with_match 로 층마다 이진 탐색
      +-- 중복 후보면 row_ins_duplicate_error_in_clust    L2530  (S 또는 X 레코드 잠금)
      +-- 같은 키의 delete-mark 레코드면 by_modify        L2562  (삽입 대신 갱신)
      +-- LEAF  [03] btr_cur_optimistic_insert            L2577  btr0cur.cc L2662
      |           +-- [04] btr_cur_ins_lock_and_undo      L2815  btr0cur.cc L2554
      |           |     +-- lock_rec_insert_check_and_lock   --> [레코드 잠금과 교착]
      |           |     +-- trx_undo_report_row_operation    --> undo (MVCC, 롤백, purge 의 재료)
      |           +-- [05] page_cur_tuple_insert          L2838  page0cur.ic L187
      |                 +-- [06] page_cur_insert_rec_low  page0cur.cc L1229
      |                       레코드 연결 리스트, page directory, redo 기록
      |           자리가 모자라면 DB_FAIL
      +-- TREE  [03] 을 한 번 더 시도하고 DB_FAIL 이면
      |     [07] btr_cur_pessimistic_insert               L2592  btr0cur.cc L2930
      |           +-- [04] btr_cur_ins_lock_and_undo      L2974
      |           +-- fsp_reserve_free_extents            L2987  분할에 쓸 공간 예약
      |           +-- 루트면  [09] btr_root_raise_and_insert   L3021  btr0btr.cc L1482
      |           |             새 페이지로 옮기고 루트를 비운 뒤 [08] 로
      |           +-- 아니면  [08] btr_page_split_and_insert   L3023  btr0btr.cc L2305
      |                         +-- btr_attach_half_pages -> btr_insert_on_non_leaf_level
      |                               부모에 노드 포인터를 넣는다. 부모도 차면 [03] -> [07] 재귀
      +-- mtr.commit                                      L2620  --> [mini-transaction과 redo 기록]
```

트리 모양으로 보면 세 경우가 있다. 분할은 옆으로 넓어지고, 루트 승격만 높이를 한 층 올린다.

```text
 (가) optimistic: 리프 안에 자리가 있다

      [ R: 10 | 50 ]                       [ R: 10 | 50 ]
       /     |     \                        /     |     \
   [1 5] [10 20 30] [50 60]    -->     [1 5] [10 20 25 30] [50 60]
                 ^ 25                        페이지 하나만 바뀐다

 (나) 분할: 리프가 찼다 (부모에는 자리가 있다. 자르는 자리는 예시, 실제는 [08] 이 정한다)

      [ R: 10 | 50 ]                       [ R: 10 | 30 | 50 ]
       /     |     \                        /     |     |     \
   [1 5] [10 20 30 40] [50 60]  -->   [1 5] [10 20 25] [30 40] [50 60]
                 ^ 25                               ^ 새 페이지, 부모에 (30, 새 페이지) 추가
                                       형제 링크 FIL_PAGE_PREV / NEXT 도 다시 잇는다

 (다) 루트 승격: 루트 하나뿐인데 찼다 (루트의 페이지 번호는 바뀌지 않는다. 자르는 자리는 예시)

   [R: 1 5 10 20]         [R: (min) ]              [ R: (min) | 10 ]
         ^ 25       -->         |           -->          /        \
                          [N: 1 5 10 20]           [N: 1 5]     [M: 10 20 25]
                     루트 내용을 새 페이지 N 으로   N 을 분할 ([08]) 하고
                     루트는 level+1 로 비우고       부모인 루트에 노드 포인터 추가
                     N 을 가리키는 포인터 하나
```

## 어디에서 쓰이는가

```text
 [행 쓰기]                  row_ins_clust_index_entry, row_ins_sec_index_entry 가 [01] 과
                            row_ins_sec_index_entry_low 를 LEAF, TREE 두 번 부른다
 [버퍼 풀 페이지 획득]      [02] 가 층마다, [07] [08] 이 새 페이지와 형제 페이지를 가져올 때
 [레코드 잠금과 교착]       [04] 의 lock_rec_insert_check_and_lock (gap 에 insert intention)
                            [03] [07] 끝의 lock_update_insert, [08] 의 lock_update_split_*
 [일관 읽기(MVCC)]          [04] 가 쓴 undo 와 레코드의 DB_ROLL_PTR 을 따라 옛 버전을 만든다
 [mini-transaction과 redo]  [06] 의 page_cur_insert_rec_write_log 가 mtr 에 로그를 쌓고
                            [01] 의 mtr.commit 이 그것을 log buffer 로 보낸다
 [구조: 테이블스페이스와 페이지 레이아웃]  페이지 헤더와 page directory 의 자리
```

## db-engine 에서는

같은 문제(정렬 유지 삽입, 꽉 찬 리프의 분할, 루트 승격)를 db-engine 은 고정 크기 엔트리 배열 하나로 풀었다.

```text
 같은 문제, 두 구현 (위 MySQL / 아래 db-engine)

 페이지 안의 정렬
   MySQL      레코드는 힙에 쌓이는 순서대로 놓이고, next 포인터 연결 리스트가 키 순서를 만든다
              이진 탐색은 page directory 슬롯(4~8 레코드마다 하나)으로 한다
   db-engine  BTreePage 가 (key 8B, value 8B) 16바이트 엔트리를 키 순서로 배열에 둔다
              insertAt 이 뒤쪽을 오른쪽부터 한 칸씩 민다. findSlot 은 배열 이진 탐색

 자리가 모자랄 때
   MySQL      DB_FAIL 로 물러나 트리 래치를 잡고 다시 (LEAF -> TREE 두 번의 mtr)
   db-engine  isFull() 이면 바로 splitLeafAndInsert (03-02). 래치 개념이 없다

 분할 지점
   MySQL      직전 삽입 위치(PAGE_LAST_INSERT)로 순차 삽입을 알아채면 새 레코드 자리에서 자른다
              아니면 가운데 레코드 (page_get_middle_rec)
   db-engine  moveHalfTo 가 언제나 keyCount / 2 에서 자른다

 루트 승격
   MySQL      루트 페이지 번호를 고정한 채 내용을 새 페이지로 옮기고 루트를 비운다 [09]
   db-engine  splitRootLeaf 가 page 0 = root 를 지키려고 copyPageContent 로 옮긴다 (같은 발상)

 부모도 찼을 때
   MySQL      btr_insert_on_non_leaf_level 이 부모에 [03] -> [07] 을 재귀로 부른다
   db-engine  insertIntoParent 가 UnsupportedOperationException (03-02, internal split 없음)

 분할 도중 죽으면
   MySQL      분할의 모든 페이지 변경이 mtr 하나에 쌓이고, 커밋 때 로그 레코드가 여럿이면
              끝에 MLOG_MULTI_REC_END 를 붙여 한 묶음으로 쓴다 (mtr0mtr.cc L801-L804)
   db-engine  impl 과제 4번: rightChild 는 디스크에 있는데 부모가 모르는 상태가 남는다 (WAL 이전)
```

db-engine 03-02 의 ISSUE-001(키가 separator 와 같을 때 왼쪽으로 내려가던 버그)과 같은 자리를 MySQL 은 **삽입 탐색에 `PAGE_CUR_LE` 를 쓰는 것**으로 다룬다. 커서는 "키 이하인 마지막 레코드"에 서고 삽입은 언제나 그 바로 뒤에 한다. 챕터: [03-01-btree-leaf-only](../../../../../project/db-engine/03-01-btree-leaf-only/), [03-02-btree-split](../../../../../project/db-engine/03-02-btree-split/).

## 단계

1. [row_ins_clust_index_entry_low](01_row_ins_clust_index_entry_low/README.md)가 mtr 을 열고 커서를 세운 뒤 중복 검사, 갱신 전환, optimistic / pessimistic 삽입을 고른다.
2. [btr_cur_search_to_nth_level](02_btr_cur_search_to_nth_level/README.md)이 래치 모드에 맞춰 루트에서 리프까지 내려간다.
3. [btr_cur_optimistic_insert](03_btr_cur_optimistic_insert/README.md)가 페이지 하나 안에서 넣거나 `DB_FAIL` 로 물러난다.
4. [btr_cur_ins_lock_and_undo](04_btr_cur_ins_lock_and_undo/README.md)가 gap 잠금을 검사하고 undo 를 쓴 뒤 DB_ROLL_PTR 을 채운다.
5. [page_cur_tuple_insert](05_page_cur_tuple_insert/README.md)가 엔트리를 물리 레코드로 바꿔 페이지에 넘긴다.
6. [page_cur_insert_rec_low](06_page_cur_insert_rec_low/README.md)가 공간을 얻고 연결 리스트와 page directory 를 고치고 redo 를 남긴다.
7. [btr_cur_pessimistic_insert](07_btr_cur_pessimistic_insert/README.md)가 공간을 예약하고 분할이나 루트 승격을 고른다.
8. [btr_page_split_and_insert](08_btr_page_split_and_insert/README.md)가 페이지를 둘로 나누고 부모에 노드 포인터를 넣는다.
9. [btr_root_raise_and_insert](09_btr_root_raise_and_insert/README.md)가 루트를 한 층 올린 뒤 [08] 로 나눈다.

## 결과가 쓰이는 곳

```text
 리프의 새 레코드 (heap_no, next 포인터, n_owned)
      --> 이후 탐색이 page directory 이진 탐색 + 연결 리스트로 찾는다
      --> 레코드 잠금이 (페이지, heap_no) 로 이 레코드를 가리킨다

 insert undo 레코드와 DB_ROLL_PTR
      --> 롤백, [일관 읽기(MVCC)], [purge]

 mtr 의 redo 로그 (레코드 삽입은 MLOG_REC_INSERT, page0cur.cc L976)
      --> [mini-transaction과 redo 기록] 에서 log buffer 로, 크래시 뒤 [크래시 복구] 가 다시 적용

 분할로 생긴 새 페이지와 부모의 노드 포인터
      --> 다음 [02] 탐색이 새 경로로 내려간다
```

## 다루지 않는 것

세컨더리 인덱스의 중복 검사(`row_ins_scan_sec_index_for_duplicate`), 공간 인덱스(R-tree, `rtr_*`), 압축 페이지(`page_zip_*`, `page_cur_insert_rec_zip`), 내부 임시 테이블의 무래치 경로(`btr_cur_search_to_nth_level_with_no_latch`), 적응형 해시 인덱스(`btr_search_guess_on_hash`, `btr_search_update_hash_on_insert`), 외부 저장 열(`big_rec`, `row_ins_index_entry_big_rec`), 온라인 DDL 로그(`row_log_table_insert`), change buffer 는 이 흐름의 곁가지라 이름과 줄만 적었다. 삭제 쪽의 합치기(`btr_compress`)는 [purge](../purge/README.md) 쪽이다.

## 하위 메서드

- [01 row_ins_clust_index_entry_low](01_row_ins_clust_index_entry_low/README.md)
- [02 btr_cur_search_to_nth_level](02_btr_cur_search_to_nth_level/README.md)
- [03 btr_cur_optimistic_insert](03_btr_cur_optimistic_insert/README.md)
- [04 btr_cur_ins_lock_and_undo](04_btr_cur_ins_lock_and_undo/README.md)
- [05 page_cur_tuple_insert](05_page_cur_tuple_insert/README.md)
- [06 page_cur_insert_rec_low](06_page_cur_insert_rec_low/README.md)
- [07 btr_cur_pessimistic_insert](07_btr_cur_pessimistic_insert/README.md)
- [08 btr_page_split_and_insert](08_btr_page_split_and_insert/README.md)
- [09 btr_root_raise_and_insert](09_btr_root_raise_and_insert/README.md)
