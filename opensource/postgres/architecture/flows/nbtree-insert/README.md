# nbtree 삽입과 분할

상위: [PostgreSQL 아키텍처 지도](../../README.md)

힙에 행 하나가 들어간 뒤, **그 행을 가리키는 인덱스 튜플 하나가 B-tree 리프에 자리 잡기까지**의 흐름이다. 이 흐름의 뼈대는 Lehman-Yao 알고리즘이다. 페이지마다 high key(키 상한)와 오른쪽 링크가 있어서, 탐색은 부모 잠금을 놓고 내려가도 그 사이 쪼개진 페이지를 오른쪽으로 따라가 찾는다. 삽입은 리프 하나만 쓰기 잠금으로 잡고, 유일 인덱스면 그 잠금을 쥔 채 중복을 검사하며, 진행 중인 트랜잭션의 중복을 만나면 잠금을 놓고 그 트랜잭션이 끝나기를 기다렸다가 처음부터 다시 한다. 공간이 모자라면 먼저 죽은 항목 지우기와 중복 합치기(deduplication)로 분할을 피하고, 그래도 안 되면 분할 지점을 계산해 페이지를 쪼갠 뒤 부모에 downlink 를 넣는다. 부모도 꽉 차면 같은 일이 한 레벨 위에서 되풀이되고, 루트가 쪼개지면 새 루트가 생겨 트리가 한 층 높아진다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 executor
 [01] ExecInsertIndexTuples                       execIndexing.c   L310
      +-- 인덱스마다 checkUnique 결정                               L430
      +-- [02] index_insert                       indexam.c        L213
            +-- rd_indam->aminsert                                  L230
                  [03] btinsert                   nbtree.c         L202
                        +-- index_form_tuple, t_tid = 힙 TID        L212-L213
 ------------------------------------------------------------------------------
 nbtree (아래 줄은 모두 access/nbtree/nbtinsert.c, 따로 적은 것만 다른 파일)
 [04] _bt_doinsert                                                  L102
      +-- _bt_mkscankey  (유일 검사면 scantid = NULL)               L113
      +-- search:
      |   [05] _bt_search_insert                                    L317
      |     +-- 오른쪽 끝 리프 캐시 (fastpath)                       L323
      |     +-- _bt_search                       nbtsearch.c       L107
      |           +-- _bt_moveright  high key < key 면 오른쪽으로    L246  (Lehman-Yao)
      |   [06] _bt_check_unique                                     L408
      |     +-- 같은 키의 힙 TID 마다 SnapshotDirty 로 확인
      |     +-- 진행 중이면 xid 반환 -> 버퍼를 놓고 XactLockTableWait
      |         -> goto search                                      L227-L232
      +-- [07] _bt_findinsertloc                                    L815
      |     +-- _bt_stepright (힙 TID 까지 넣은 자리가 오른쪽이면)   L1027
      |     +-- _bt_delete_or_dedup_one_page                        L2683
      |           simple deletion -> bottom-up deletion -> dedup
      +-- [08] _bt_insertonpg                                       L1105
            +-- 공간 있음: PageAddItem + XLOG_BTREE_INSERT_*        L1280
            +-- 공간 없음:
                  [09] _bt_split                                    L1467
                    +-- [10] _bt_findsplitloc    nbtsplitloc.c     L129
                  [11] _bt_insert_parent                            L2099
                    +-- 루트였으면 [12] _bt_newlevel                 L2444
                    +-- _bt_getstackbuf 로 부모를 찾아               L2319
                        [08] _bt_insertonpg(부모) 로 재귀           L2218
```

한 번의 분할이 남기는 상태 변화는 셋이다. 오른쪽 형제가 생기고, 왼쪽에 새 high key 와 `INCOMPLETE_SPLIT` 이 붙고, 부모 삽입이 그 표시를 지운다. 아래는 `int4` 기본키에 1, 2, 3, ... 을 차례로 넣을 때 [10] 의 규칙으로 계산한 실제 모양이다.

```text
 키 1..407     [블록 1  LEAF | ROOT]  1 .. 407        PageGetFreeSpace = 8 < 16

 키 408        [09] 분할 지점 367 (fillfactor 90 의 오른쪽 끝 분할)
               [12] 새 루트 블록 3

               메타(0) -> [블록 3  ROOT, level 1]
                            ( -inf ) -> 1
                            ( 367  ) -> 2
                           /                \
               [블록 1] 1..366 hikey 367  -->  [블록 2] 367..408

 키 774        블록 2 가 같은 규칙으로 쪼개져 블록 4 가 생기고 [11] 이 루트에 (733 -> 4) 를 넣는다

               [블록 3]  ( -inf ) -> 1 | ( 367 ) -> 2 | ( 733 ) -> 4
               [블록 1] 1..366  -->  [블록 2] 367..732  -->  [블록 4] 733..774
```

## 어디에서 쓰이는가

```text
 [executor]            ExecInsert 가 table_tuple_insert 다음에 ExecInsertIndexTuples 를 부른다
                       (nodeModifyTable.c L1234, L1240). UPDATE 도 새 버전마다 같은 길을 간다
 [행 쓰기와 WAL 기록]  인덱스 튜플이 가리키는 힙 TID 는 그 흐름이 정한다
 [heavyweight lock]    유일성 대기는 XactLockTableWait -> 상대 xid 에 ShareLock (lmgr.c L697)
 [버퍼 관리]           모든 페이지 접근이 _bt_getbuf / _bt_relandgetbuf -> ReadBuffer + LockBuffer
 [WAL redo]            XLOG_BTREE_INSERT_* / SPLIT_* / NEWROOT 레코드를 btree_redo 가 되감는다
```

이 흐름이 대기하는 자리는 [heavyweight lock](../heavyweight-lock/README.md) 흐름이 이어 받는다. 인덱스 튜플이 가리키는 힙 쪽은 [행 쓰기와 WAL 기록](../heap-insert-wal/README.md), 페이지를 읽고 잠그는 바닥은 [버퍼 관리](../buffer-manager/README.md)다.

## db-engine 에서는

db-engine 의 B+tree 는 같은 세 가지 일(쪼개고, 잇고, 부모에 올린다)을 단일 스레드 전제로 한다. 그래서 high key 와 right link 를 따라가는 동시성 장치가 없고, 루트는 0 번 페이지에 고정되어 있다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 동시 분할
   PG         페이지마다 high key + right link. 탐색은 부모를 놓고 내려가도 _bt_moveright 로 따라간다
   db-engine  잠금도 high key 도 없다. 부모 포인터(parentPage) 를 페이지에 저장한다

 분할 지점
   PG         후보 전체를 계산해 고른다. 오른쪽 끝 리프는 왼쪽 90%, 그 밖은 50:50 근처
              suffix truncation 으로 구분 키를 짧게
   db-engine  moveHalfTo: total / 2 에서 자른다. 구분 키 = 오른쪽 첫 키

 루트 분할
   PG         새 블록을 루트로 만들고 메타페이지의 btm_root 를 바꾼다. 옛 루트는 그대로 왼쪽 자식
   db-engine  루트는 0 번 페이지 고정. 루트 내용을 새 왼쪽 자식으로 복사하고 0 번을 INTERNAL 로 다시 씀

 중복과 유일성
   PG         힙을 먼저 넣고, 인덱스 삽입 중에 리프 쓰기 잠금을 쥔 채 검사. 진행 중이면 기다림
              비유일 인덱스는 힙 TID 를 키의 마지막 열로 쳐서 중복도 자리가 하나
   db-engine  BTreeIndex 는 중복 키를 require 로 거부. IndexedTableHeap 은 인덱스로 먼저 검사하고
              힙, 인덱스 순으로 넣는다

 분할 중 장애
   PG         SPLIT 과 부모 INSERT 를 따로 WAL 에 남기고, 끊기면 INCOMPLETE_SPLIT 으로 다음 삽입자가 마무리
   db-engine  부모 삽입 전에 죽으면 오른쪽 leaf 가 도달 불가 (impl 문서 과제 4번의 답)
```

db-engine 의 03-02 는 부모가 꽉 차면 `UnsupportedOperationException` 을 던져 높이가 2 에서 멈춘다. PostgreSQL 에서는 같은 자리가 [11] 에서 [08] 로 재귀해 부모를 쪼갠다. db-engine 의 03-02 과제 2번(분할 지점을 `total - 1` 로)과 과제 4번(부모 삽입 전 장애)은 PostgreSQL 이 각각 오른쪽 끝 fillfactor 분할과 `INCOMPLETE_SPLIT` 으로 답한 문제다. 챕터: [03-01-btree-leaf-only](../../../../../project/db-engine/03-01-btree-leaf-only/), [03-02-btree-split](../../../../../project/db-engine/03-02-btree-split/), [06-04-indexed-table-heap](../../../../../project/db-engine/06-04-indexed-table-heap/).

## 단계

1. [ExecInsertIndexTuples](01_ExecInsertIndexTuples/README.md)가 인덱스마다 유일성 검사 방식을 정하고 `index_insert` 를 부른다.
2. [index_insert](02_index_insert/README.md)가 AM 의 `aminsert` 함수 포인터로 넘긴다.
3. [btinsert](03_btinsert/README.md)가 키와 힙 TID 로 인덱스 튜플을 만든다.
4. [_bt_doinsert](04__bt_doinsert/README.md)가 찾기, 유일성 검사와 대기, 삽입을 지휘한다.
5. [_bt_search_insert](05__bt_search_insert/README.md)가 fastpath 나 `_bt_search` 로 리프를 찾아 쓰기 잠금을 잡는다. Lehman-Yao 의 `_bt_moveright` 도 여기서 다룬다.
6. [_bt_check_unique](06__bt_check_unique/README.md)가 같은 키의 힙 튜플을 확인해 에러를 내거나 기다릴 xid 를 돌려준다.
7. [_bt_findinsertloc](07__bt_findinsertloc/README.md)가 넣을 페이지와 오프셋을 정하고, 공간이 모자라면 삭제와 dedup 으로 분할을 피한다.
8. [_bt_insertonpg](08__bt_insertonpg/README.md)가 페이지에 넣고 WAL 을 남기거나, 분할과 부모 삽입으로 넘어간다.
9. [_bt_split](09__bt_split/README.md)이 페이지를 왼쪽과 오른쪽으로 나눈다.
10. [_bt_findsplitloc](10__bt_findsplitloc/README.md)이 분할 지점을 계산한다.
11. [_bt_insert_parent](11__bt_insert_parent/README.md)가 부모를 다시 찾아 downlink 를 넣는다.
12. [_bt_newlevel](12__bt_newlevel/README.md)이 루트 분할 뒤 새 루트를 만든다.

## 결과가 쓰이는 곳

```text
 리프의 인덱스 튜플 (키 + 힙 TID, 또는 posting list)
      --> 인덱스 스캔(_bt_first, _bt_readpage)이 찾아 힙 TID 로 힙을 읽는다
      --> vacuum 의 btbulkdelete 가 죽은 힙 TID 를 가리키는 항목을 지운다

 페이지 구조 변화 (새 형제, 새 pivot, 새 루트)
      --> 이후 모든 탐색이 따라가는 경로가 된다
      --> 메타페이지의 btm_root, btm_fastroot 는 _bt_getroot 의 출발점

 WAL 레코드 (RM_BTREE_ID)
      --> 크래시 복구와 스트리밍 복제 standby 가 같은 변경을 되풀이한다

 LP_DEAD 표시와 RelationSetTargetBlock 캐시
      --> 다음 삽입이 분할을 피하거나 루트부터 내려가지 않는 데 쓴다
```

## 다루지 않는 것

인덱스 스캔 쪽(`_bt_first`, `_bt_readpage`, 뒤로 가는 스캔의 move-left), 페이지 삭제와 재활용(`_bt_pagedel`, vacuum 의 `btvacuumscan`), `CREATE INDEX` 의 정렬 기반 일괄 생성(`nbtsort.c`), dedup 과 bottom-up 삭제의 내부(`nbtdedup.c`), WAL 복구 함수(`nbtxlog.c`), SSI 술어 잠금, pg_upgrade 로 남은 버전 2, 3 인덱스(`!heapkeyspace`)의 차이는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 ExecInsertIndexTuples](01_ExecInsertIndexTuples/README.md)
- [02 index_insert](02_index_insert/README.md)
- [03 btinsert](03_btinsert/README.md)
- [04 _bt_doinsert](04__bt_doinsert/README.md)
- [05 _bt_search_insert](05__bt_search_insert/README.md)
- [06 _bt_check_unique](06__bt_check_unique/README.md)
- [07 _bt_findinsertloc](07__bt_findinsertloc/README.md)
- [08 _bt_insertonpg](08__bt_insertonpg/README.md)
- [09 _bt_split](09__bt_split/README.md)
- [10 _bt_findsplitloc](10__bt_findsplitloc/README.md)
- [11 _bt_insert_parent](11__bt_insert_parent/README.md)
- [12 _bt_newlevel](12__bt_newlevel/README.md)
