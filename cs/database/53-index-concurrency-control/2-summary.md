# database/53-index-concurrency-control — 인덱스 동시성 제어: 래치·래치 크래빙·B-link 트리 — 정리 (힌트)

## 해결하는 문제

B+Tree(08번)는 여러 스레드가 동시에 읽고 쓴다. 한 스레드가 노드를 나누는 도중에 다른 스레드가 그 노드를 지나가면 어떻게 될까?

```text
  스레드 A: 키 44를 찾으러 내려간다        스레드 B: 리프 L에 삽입 → L이 꽉 차 분할
  루트에서 "44는 L 쪽" 확인
                                         L의 뒤쪽 절반(40~50)을 새 노드 L'로 옮김
  L에 도착 → 44가 없다!                    부모에 L' 포인터 추가
  → "없음"이라고 틀린 답을 한다
```

- 이것은 **트랜잭션의 논리적 충돌**이 아니다. 자료구조 자체가 잠깐 깨진 모습을 본 **물리적 정합성** 문제다(CMU 15-445 L10).
- 그래서 인덱스 페이지를 짧게 잠그는 **래치**가 필요하다. 문제는 루트부터 잠그면 모든 스레드가 루트에서 줄을 선다는 것이다.

쉬운 예: 여러 사람이 같이 쓰는 서류철이다.
- 누군가 칸막이를 새로 끼우며 서류를 옮기는 중에 다른 사람이 "4번 칸에 있을 거야" 하고 열면 비어 있다.
- 서류철 전체를 한 사람만 쓰게 하면 안전하지만 모두가 기다린다.
- 해법 1: 한 칸을 잡은 채 다음 칸을 잡고, 안전하면 앞 칸을 놓는다(래치 크래빙).
- 해법 2: 칸마다 "이 칸의 마지막 번호"와 "다음 칸 위치"를 적어 둔다. 찾는 번호가 마지막 번호보다 크면 옆 칸으로 가면 된다(B-link 트리).

똑같은 구조다.

실무 예:
- 주문 테이블 PK가 자동 증가다. 동시 삽입이 몰리면 모두 **가장 오른쪽 리프 한 장**에 넣으려 한다. 그 페이지의 래치에서 줄을 선다.
- PostgreSQL `pg_stat_activity`에 `LWLock` / `BufferContent` 대기가 쌓이고, CPU가 남는데 삽입 처리량이 늘지 않는다.

## 동작·원리

### 1. 락(lock)과 래치(latch)

```text
                락 (lock)                          래치 (latch)
  보호 대상      DB 내용: 행·테이블 (논리)              내부 자료구조: 페이지·해시 버킷 (물리)
  누가          트랜잭션                              스레드
  얼마나         트랜잭션 끝까지 (보통)                  연산 하나, 아주 짧게
  모드          S, X, IS, IX, … (15번)                읽기, 쓰기
  교착          DB가 탐지·희생자 롤백                  탐지 없음 — 코딩 규율로 피한다
  보이는 곳      pg_locks, data_locks                  PG wait_event LWLock:*, InnoDB SEMAPHORES
```

- 래치는 교착 탐지를 하지 않는다. 그래서 **잡는 순서를 규칙으로 정해** 교착이 생길 수 없게 만든다(CMU L10).
- 래치 구현(CMU L10): 스핀 래치(CAS로 비트 하나), OS 뮤텍스(리눅스 futex — 사용자 공간에서 먼저 시도하고 실패하면 커널에서 잔다), 읽기-쓰기 래치. 구현 세부는 [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)에서 다룬다.

### 2. 래치 크래빙 (latch crabbing / coupling)

게가 다리 하나를 짚은 채 다음 다리를 옮기듯, **부모를 잡은 채 자식을 잡고**, 자식이 "안전"하면 부모를 놓는다.

```text
  안전한 노드 = 이번 연산으로 분할·병합이 일어나지 않는 노드
     삽입: 꽉 차지 않은 노드        삭제: 절반보다 많이 찬 노드

  삽입 (기본 프로토콜) — 쓰기 래치로 내려간다
     [루트 W] ─잡음─> [내부 W] ─잡음─> [리프 W]
         내부가 안전 → 루트 래치를 놓는다
         리프가 꽉 참(안전 아님) → 내부 래치는 쥔 채 유지 (분할이 부모까지 올라올 수 있다)

  조회 — 읽기 래치로 내려가며 자식을 잡으면 바로 부모를 놓는다
```

- 래치를 늘 **위에서 아래로만** 잡는다. 위로 거슬러 잡는 스레드가 없으니 교착이 생기지 않는다(CMU L10).
- 기본 프로토콜의 문제: 모든 삽입·삭제가 **루트에 쓰기 래치**를 잡는다. 루트가 병목이다.
- **개선된(낙관적) 프로토콜**: 분할은 드물다고 가정한다. 읽기 래치로 크래빙해 리프까지 가서 **리프만** 쓰기 래치를 잡는다. 리프가 안전하지 않으면 전부 놓고 기본 프로토콜로 다시 한다(CMU L10).

### 3. 리프 스캔과 교착 — no-wait

```text
  스레드 1: 리프 L2 쓰기 래치 쥠 → 왼쪽 형제 L1이 필요
  스레드 2: 리프 L1 읽기 래치 쥠 → 범위 스캔으로 오른쪽 L2로 가려 함
  → 서로 반대 방향으로 잡는다 → 교착 가능
```

- 위→아래 규칙은 형제 이동(좌↔우)에는 적용되지 않는다. 래치는 교착 탐지가 없으므로, 형제 래치를 **못 얻으면 기다리지 않고** 쥔 래치를 모두 놓고 연산을 다시 시작하게 짠다(no-wait, CMU L10).

### 4. B-link 트리 (Lehman–Yao 1981) — 분할을 "옆으로 가기"로 견딘다

```text
  각 노드에 두 가지를 더한다
    high key   : 이 노드에 들어올 수 있는 키의 상한
    right-link : 오른쪽 형제 노드 포인터

  분할 전:  [L: 10 20 30 40 44 50 | high=60] ──right──> [M | high=90]

  분할 후:  [L: 10 20 30 | high=40] ──right──> [L': 40 44 50 | high=60] ──right──> [M]
            (부모에 L' 포인터가 아직 안 들어갔을 수 있다)

  스레드 A가 옛 부모를 보고 L에 도착 → 44 > high(40) → right-link를 따라 L'로 → 44 발견
```

- 탐색은 페이지를 **하나씩만** 잡는다. 부모를 쥔 채 자식을 잡는 크래빙이 필요 없다. 도착한 노드의 high key보다 찾는 키가 크면 "그 사이 분할됐다"는 뜻이므로 오른쪽으로 간다(PostgreSQL `nbtree/README`).
- 분할은 두 단계다. 먼저 형제에 절반을 옮기고 right-link를 잇는다. 그다음 부모에 새 포인터를 넣는다. 그 사이에도 트리는 올바르게 탐색된다.
- **PostgreSQL 17의 B-tree**(`src/backend/access/nbtree`)는 Lehman–Yao 알고리즘 구현이다(README 첫 문장). 차이점도 README에 있다.
  - 공유 버퍼를 쓰므로 페이지를 읽는 동안에는 짧은 **읽기 락**을 잡는다. L&Y 원래 논문은 읽기 락이 필요 없다고 가정한다.
  - 역방향 스캔을 위해 left-link도 둔다.
  - 대부분 다음 페이지로 가기 전에 현재 페이지 락을 놓는다. 다음 페이지를 먼저 잡고 현재를 놓는 것은 **오른쪽이나 위로 갈 때만** 안전하다. 왼쪽이나 아래로 그렇게 하면 교착이 생길 수 있다.
  - 분할이 끝나지 않은 페이지에는 `INCOMPLETE_SPLIT` 표시를 두고 다음 삽입이 마무리한다.

### 5. InnoDB (MySQL 8.4) — 인덱스 전체 락 + 페이지 래치

```text
  index->lock (인덱스마다 하나, 읽기-쓰기 락 S / SX / X)
       호환성:     S   SX   X
               S   +   +    -
               SX  +   -    -
               X   -   -    -              (storage/innobase/sync/sync0rw.cc)

  낙관적 변경 (BTR_MODIFY_LEAF): index->lock S → 리프 페이지만 쓰기 래치 → 리프 안에서 끝
  비관적 변경 (BTR_MODIFY_TREE): index->lock SX → 분할·병합이 필요한 경로의 페이지들을 X 래치
```

- 소스 `storage/innobase/btr/btr0cur.cc`(mysql-8.4.10)의 `btr_cur_search_to_nth_level`: 트리 변경 모드는 대개 `index->lock`을 **SX**로, 일반 검색은 **S**로 잡는다. 공간 인덱스, 그리고 history list가 길고 읽기 I/O가 밀린 때의 삭제 의도(퍼지) 연산은 X로 잡는다. 내려가는 길의 위쪽 페이지는 X 래치(`upper_rw_latch = RW_X_LATCH`), 일반 검색은 S 래치다.
- SX는 S와 공존한다. 그래서 한 스레드가 분할 중이어도 다른 스레드의 검색은 `index->lock`에서 막히지 않는다. 다만 분할이 X 래치를 쥔 페이지를 지나야 하는 검색은 그 페이지에서 기다린다. 다른 페이지로 가는 검색은 병행한다. 대신 SX끼리는 배타라 **트리 구조 변경은 인덱스당 한 번에 하나**다.
- 삽입은 먼저 낙관적 삽입(`btr_cur_optimistic_insert`)을 시도하고, 리프에 자리가 없으면 비관적 삽입(`btr_cur_pessimistic_insert`)으로 분할한다.

### 6. 단조 증가 키 — 가장 오른쪽 리프 하나에 몰린다

```text
  PK = 1, 2, 3, ... (시퀀스·AUTO_INCREMENT·타임스탬프)

  [루트]
     │
   ... ─> [리프 k] ─> [리프 k+1: 가장 오른쪽]  ← 동시 삽입 전부가 이 한 장에 쓰기 래치를 요청
```

- 새 키가 모두 최댓값이므로 모든 삽입이 같은 리프로 간다. 그 리프의 쓰기 래치에서 줄을 선다.
- PostgreSQL은 이 경우를 위해 **fastpath**를 둔다. 세션이 마지막으로 넣은 가장 오른쪽 리프를 기억해, 다음 삽입 때 트리를 내려가지 않는다(`nbtree/README` "Fastpath For Index Insertion", 루트(fast root) 레벨이 2 이상, 즉 리프까지 두 단계 이상 내려가는 인덱스일 때만 — `nbtinsert.c` `_bt_getrootheight(rel) >= BTREE_FASTPATH_MIN_LEVEL`). 하강 비용은 줄지만 **같은 리프 래치 경합은 그대로**다.
- 대신 좋은 점도 있다. 가장 오른쪽 리프를 나눌 때 PostgreSQL은 왼쪽을 `fillfactor`(B-tree 리프 기본 90)%까지 채우고 나눈다. 증가 키 삽입이 끝나면 페이지가 약 90% 찬다. 이 특례가 없으면 50%다(`nbtsplitloc.c` 주석, `nbtree.h` `BTREE_DEFAULT_FILLFACTOR`).

```text
  로컬 재현 (예시, PostgreSQL 17.11) — 세션 6개가 5초 동안 50행씩 INSERT (synchronous_commit=off)
  0.2초 간격으로 pg_stat_activity의 wait_event를 20번 표본 추출

  bigserial PK (단조 증가)       LWLock:BufferContent  36회     (그 밖 Lock:extend 등 소수)
  uuid PK (gen_random_uuid)      LWLock:BufferContent   0회     (Lock:extend·IO:DataFileExtend 몇 회)
```

- `BufferContent`는 "메모리의 데이터 페이지에 접근하려고 기다림"이다(PostgreSQL 17 표 27.12 Wait Events of Type LWLock). 힙 삽입 조건은 두 테이블이 같으므로, 차이는 PK 인덱스의 오른쪽 리프 경합으로 해석했다(추정).
- 같은 재현에서 PK 인덱스 크기는 bigserial 약 245만 행에 52 MB, uuid 약 275만 행에 112 MB였다. 행당 약 1.9배다. 키가 두 배 길고(8 → 16바이트), 중간 리프 분할은 반반으로 나뉘어 페이지가 덜 차기 때문으로 해석한다. 경합을 줄인 대가다. 이 트레이드오프는 08·28번에서 다룬다.

## 쓰이는 자료구조·알고리즘

- **읽기-쓰기 래치** — 읽기끼리는 공존, 쓰기는 배타. 대기 정책(읽기 우선·쓰기 우선·공정)은 구현마다 다르다(CMU L10). [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md)
- **래치 크래빙** — 부모 → 자식 순으로 잡고, 자식이 안전하면 조상을 놓는다. 전순서(위→아래)로 교착을 막는다. 교착 네 조건 중 원형 대기를 깨는 것이다. [os/19-deadlock](../../os/19-deadlock/2-summary.md)
- **B-link 트리** — high key + right-link. 분할 중인 트리도 "오른쪽으로 가기"로 올바르게 탐색한다.
- **해시 테이블 래치** — 페이지 래치(페이지마다 하나) 또는 슬롯 래치(슬롯마다 하나). 모든 스레드가 같은 방향으로 움직여 교착이 없다. 크기를 바꿀 때만 전체 래치를 잡는다(CMU L10). PostgreSQL 해시 인덱스는 두 버킷을 잠글 때 항상 번호가 작은 버킷부터 잠근다(`access/hash/README`). [39-hash-indexes](../39-hash-indexes/2-summary.md)
- **CAS** — 스핀 래치와 래치 없는(latch-free) 자료구조의 바탕이 되는 원자 명령.

## 적용 — 풀어나가는 법

### 1. 증상에서 래치 경합을 알아본다

```sql
-- PostgreSQL 17: 지금 무엇을 기다리나 (몇 초 간격으로 여러 번 표본)
SELECT wait_event_type, wait_event, count(*)
FROM pg_stat_activity
WHERE state = 'active' AND wait_event IS NOT NULL
GROUP BY 1, 2 ORDER BY 3 DESC;
-- LWLock / BufferContent 가 삽입 부하에서 지배적이면 핫 페이지 의심
-- Lock / transactionid, tuple 이면 래치가 아니라 행 락 대기 (15번)
```

```sql
-- MySQL 8.4: 인덱스 트리 락 대기 계측 (기본 꺼짐 → 켜야 모인다)
UPDATE performance_schema.setup_instruments
   SET ENABLED = 'YES', TIMED = 'YES'
 WHERE NAME = 'wait/synch/sxlock/innodb/index_tree_rw_lock';
SELECT EVENT_NAME, COUNT_STAR, SUM_TIMER_WAIT
  FROM performance_schema.events_waits_summary_global_by_event_name
 WHERE EVENT_NAME LIKE 'wait/synch/sxlock/innodb/%';
SHOW ENGINE INNODB STATUS\G   -- SEMAPHORES 절: 어떤 rw-lock에서 누가 기다리나
```

- 로컬 확인(MySQL 8.4.10): `wait/synch/sxlock/innodb/index_tree_rw_lock`·`btr_search_latch`·`hash_table_locks` 계측기가 있고 기본값은 `ENABLED = NO`였다. 소비자 쪽은 최상위 `global_instrumentation`이 꺼져 있으면 아무것도 모이지 않는다(MySQL 8.4 29.4.7, 로컬 확인 기본 YES). 요약 테이블에 `events_waits_current` 같은 개별 이벤트 소비자(기본 NO)까지 필요한지는 확인하지 못했다 [?].

### 2. 핫 리프를 분산한다

```text
  방법                                  효과                          대가
  해시 파티셔닝 (PG PARTITION BY HASH)   파티션마다 별도 인덱스 → 오른쪽 리프 N장   파티션 관리, 파티션 키 없는 조회는 모든 파티션을 본다
  키 앞에 분산 값 (shard_id, seq)         리프 여러 장에 나뉨                  순차 범위 조회가 흩어짐
  랜덤 키 (UUIDv4)                      경합 분산 (같은 리프에 겹칠 수는 있다)    인덱스 크기·분할·버퍼 적중률 악화 (08·28번)
  배치 삽입 (한 트랜잭션·한 문장에 여러 행)  왕복·커밋 횟수 감소 (리프 래치는 행마다 그대로)  지연 증가
  핫 경로의 보조 인덱스 줄이기             래치 잡을 인덱스 수 감소              조회 성능 (09번)
```

- 먼저 **정말 래치 경합인지** 확인한다. 커밋의 WAL 쓰기·fsync 대기나 행 락 대기가 원인일 수도 있다.
  - `LWLock:WALWrite`: WAL 버퍼를 디스크에 쓰는 락 대기다. 이 락을 쥔 세션이 쓰기와 fsync를 하는 동안 다른 커밋이 여기서 기다린다(`xlog.c` `XLogFlush`).
  - `IO:WalSync`: WAL 파일이 영속 저장소에 닿기를(fsync) 기다리는 것 자체다(PostgreSQL 17 표 27.9 Wait Events of Type IO).
- 로컬 재현에서도 `synchronous_commit`을 끄기 전에는 `WALWrite` 대기가 지배적이었다.

### 3. 앱 쪽

```java
// 자동 커밋으로 한 행씩 insert 1000번 = 왕복 1000번 + 커밋 1000번
// 자동 커밋을 끄고 JDBC 배치로 묶으면 왕복·커밋이 준다 (인덱스 리프 래치는 행마다 잡는다 — PG `_bt_doinsert`는 튜플 하나씩)
conn.setAutoCommit(false);
try (PreparedStatement ps = conn.prepareStatement("INSERT INTO orders(user_id, amount) VALUES (?, ?)")) {
    for (Order o : batch) { ps.setLong(1, o.userId()); ps.setLong(2, o.amount()); ps.addBatch(); }
    ps.executeBatch();
}
conn.commit();
```

- MySQL Connector/J는 `rewriteBatchedStatements=true`(기본 false)일 때 `executeBatch()`의 prepared `INSERT`·`REPLACE`를 다중 값(multi-values) 문장으로 다시 쓴다(Connector/J 문서 Performance Extensions). 드라이버 옵션이지 DB 엔진 동작이 아니다.

## 장애 시나리오와 대처

### 1. 핫 인덱스 페이지 래치 경합 → 단조 증가 키 삽입 병목

- **현상**: 주문·로그 삽입 처리량이 동시 세션을 늘려도 오르지 않는다. CPU는 남는다.
- **보이는 형태**: PostgreSQL `pg_stat_activity`에 `wait_event_type = LWLock`, `wait_event = BufferContent`가 많다(로컬 재현: 20회 표본 중 36건, 랜덤 키에서는 0건). MySQL은 `SHOW ENGINE INNODB STATUS`의 SEMAPHORES 절에 페이지 rw-lock 대기가 보인다 [?].
- **원인**: 단조 증가 키는 모든 삽입을 가장 오른쪽 리프 한 장으로 보낸다. 그 페이지의 쓰기 래치를 한 번에 한 스레드만 쥔다.
- **대처**: 해시 파티셔닝이나 키 분산으로 리프를 여러 장에 나눈다. 배치 삽입은 왕복·커밋을 줄일 뿐 리프 래치 횟수는 그대로다. 랜덤 키는 경합을 크게 줄이지만 인덱스 크기·분할 비용을 늘리므로 마지막 수단이다.

### 2. 분할 폭주 중 인덱스 전체가 느려짐 (InnoDB)

- **현상**: 대량 삽입·삭제 중 같은 테이블의 다른 쓰기가 일제히 느려진다.
- **보이는 형태**: SEMAPHORES 절에 `index->lock`(계측기 `index_tree_rw_lock`) SX 대기가 늘어난다 [?].
- **원인**: 트리 구조를 바꾸는 비관적 연산은 `index->lock`을 SX로 잡는다. SX끼리는 배타라 한 인덱스의 구조 변경은 한 번에 하나다(`btr0cur.cc`, `sync0rw.cc` 호환성 표). 랜덤 키 대량 삽입처럼 분할이 잦으면 이 락에서 줄을 선다.
- **대처**: 적재는 PK 순서로 정렬해 넣는다(분할 감소). 대량 삭제는 작은 묶음으로 나눈다(34번). 보조 인덱스는 적재 뒤 만든다.

### 3. "교착처럼" 멈췄는데 DB 교착 탐지가 조용함

- **현상**: 특정 부하에서 쿼리가 짧게 멈췄다 풀리기를 반복한다. `deadlock detected`도 `ERROR 1213`도 없다.
- **보이는 형태**: `pg_locks`에는 대기 행이 없는데 `pg_stat_activity`에는 `LWLock` 대기가 있다.
- **원인**: 래치 대기는 락 관리자(`pg_locks`, `data_locks`)에 나오지 않는다. 래치에는 교착 탐지가 없다. 설계상 교착이 없도록 순서를 지키고, 대기는 짧게 끝난다. 길게 보이면 경합이다.
- **대처**: 락(15번)과 래치를 구분해 진단한다. 락 뷰가 비어 있으면 대기 이벤트(LWLock)와 InnoDB SEMAPHORES를 본다. 래치 교착이 실제로 의심되면 DB 버그 영역이다. 스택(`gdb`, `pstack`)과 버전을 모아 제보한다.

### 4. 해시 인덱스 분할이 스캔 때문에 미뤄짐 (PostgreSQL)

- **현상**: 해시 인덱스가 커질 때 버킷 분할이 안 되고 오버플로 체인이 길어진다.
- **보이는 형태**: `pgstathashindex`의 `overflow_pages`가 는다.
- **원인**: 분할에는 옛·새 버킷의 클린업 락(배타 + 다른 핀 없음)이 필요하다. 그 버킷을 스캔하는 세션이 핀을 쥐고 있으면 분할을 포기한다(`hashpage.c`). 래치 설계가 성능 특성으로 드러나는 예다.
- **대처**: 39번의 대처(적재 후 생성, 필요하면 `REINDEX`, B-tree 선택)를 따른다.

## 핵심 문장

- 락은 트랜잭션이 DB 내용을 오래 보호하고, 래치는 스레드가 내부 자료구조를 아주 짧게 보호한다. 래치에는 교착 탐지가 없다.
- 래치 크래빙은 부모를 쥔 채 자식을 잡고, 자식이 안전하면 부모를 놓는다. 위→아래로만 잡아서 교착이 없다.
- 낙관적 크래빙은 읽기 래치로 내려가 리프만 쓰기로 잡는다. 분할이 필요할 때만 다시 한다.
- B-link 트리는 high key와 오른쪽 링크로 "분할됐으면 오른쪽으로 가라"를 가능하게 해 탐색이 부모를 쥐지 않는다. PostgreSQL B-tree가 이 방식이다.
- InnoDB는 인덱스별 `index->lock`(S/SX/X)과 페이지 래치를 섞는다. 트리 구조 변경은 SX라 인덱스당 한 번에 하나다.
- 단조 증가 키는 가장 오른쪽 리프 한 장에 삽입을 몰아 래치 경합을 만든다. 분산하면 경합은 줄지만 지역성을 잃는다.

## 관련 주제·근거

- 선행
  - [08-btree-indexes](../08-btree-indexes/2-summary.md)
  - [os/16-locks-and-spinlocks](../../os/16-locks-and-spinlocks/2-summary.md) — 스핀락·futex·읽기-쓰기 락
- 연결
  - [15-two-phase-locking-and-deadlock](../15-two-phase-locking-and-deadlock/2-summary.md)(락과 교착 탐지) · [28-key-strategy-surrogate-natural-public-id](../28-key-strategy-surrogate-natural-public-id/2-summary.md)(UUID vs 순차 키) · [33-partitioning-and-sharding](../33-partitioning-and-sharding/2-summary.md) · [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md)
  - [39-hash-indexes](../39-hash-indexes/2-summary.md) · [09-index-design](../09-index-design/2-summary.md)
  - [os/19-deadlock](../../os/19-deadlock/2-summary.md) — 락 순서로 원형 대기 깨기
  - [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md)
- 강의·논문
  - CMU 15-445 Fall 2024 L10 "Index Concurrency Control"(락 vs 래치, 래치 구현, 해시 테이블 래치, 래치 크래빙 기본·개선, 리프 스캔 no-wait) <https://15445.courses.cs.cmu.edu/fall2024/notes/10-indexconcurrency.pdf>
  - P. Lehman, S. Yao, "Efficient Locking for Concurrent Operations on B-Trees", ACM TODS 6(4), 1981 — PostgreSQL `nbtree/README` 경유, 원문 미열람
- 소스
  - PostgreSQL REL_17_STABLE `src/backend/access/nbtree/README`(L&Y 구현·차이점·fastpath·INCOMPLETE_SPLIT) · `nbtinsert.c`(`BTREE_FASTPATH_MIN_LEVEL` 2) · `nbtsplitloc.c`(가장 오른쪽 분할 fillfactor) · `src/include/access/nbtree.h`(`BTREE_DEFAULT_FILLFACTOR` 90) · `src/backend/access/hash/README`(버킷 락 순서) <https://github.com/postgres/postgres/blob/REL_17_STABLE/src/backend/access/nbtree/README>
  - mysql-server mysql-8.4.10 `storage/innobase/btr/btr0cur.cc`(`index->lock` S/SX/X, `BTR_MODIFY_LEAF`/`BTR_MODIFY_TREE`, 낙관적·비관적 삽입) · `storage/innobase/sync/sync0rw.cc`(S/SX/X 호환성 표) <https://github.com/mysql/mysql-server/blob/mysql-8.4.10/storage/innobase/btr/btr0cur.cc>
- 문서
  - PostgreSQL 17 27.2 The Cumulative Statistics System — 표 27.12 Wait Events of Type LWLock(`BufferContent`: "Waiting to access a data page in memory") <https://www.postgresql.org/docs/17/monitoring-stats.html>
  - MySQL 8.4 performance_schema `setup_instruments`(`wait/synch/sxlock/innodb/*`) · 29.4.7 Pre-Filtering by Consumer · 17.17.3 InnoDB Standard Monitor and Lock Monitor Output(`SHOW ENGINE INNODB STATUS`) · MySQL Connector/J Performance Extensions(`rewriteBatchedStatements`) <https://dev.mysql.com/doc/connector-j/en/connector-j-connp-props-performance-extensions.html>
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): pgbench 6세션 5초 — bigserial PK vs uuid PK 삽입 중 `pg_stat_activity` 대기 이벤트 표본(BufferContent 36 vs 0), 커밋 fsync가 지배하는 경우(WALWrite), 두 PK 인덱스 크기; MySQL InnoDB sxlock 계측기 존재·기본 꺼짐 확인
