# database/06-pages-and-tuple-layout — 페이지와 튜플 배치: 힙 파일·슬롯 페이지·튜플 헤더·TOAST — 정리 (힌트)

## 해결하는 문제

테이블은 결국 디스크의 파일이다.\
그런데 디스크는 바이트 하나씩 읽지 않는다. 블록 단위로 읽고 쓴다([storage-media-workload](../../systems/storage-media-workload/2-summary.md)).\
그래서 DB는 파일을 **고정 크기 페이지**로 자르고, 행을 페이지 안에 담는다. 이때 세 가지 문제가 생긴다.

```text
  문제 1  행 길이가 제각각이다          → 페이지 안 어디에 어떻게 놓나
  문제 2  행을 "주소"로 가리켜야 한다    → 인덱스가 행을 찾아가야 한다. 행이 페이지 안에서 움직이면?
  문제 3  한 페이지에 안 들어가는 값    → 10MB짜리 JSON 한 칸은 어디에 두나
```

쉬운 예: 공책 한 쪽(페이지)에 메모(행)를 적는다.
- 쪽 맨 위에 "몇 번 메모는 몇째 줄" 목차를 적어 둔다.
- 메모 위치를 옮겨도 목차만 고치면 된다. 밖에서는 "3쪽 2번 메모"라고 부른다.
- 너무 긴 메모는 부록에 적고 "부록 17쪽 참조"라고만 남긴다.

똑같은 구조다.\
목차 = **슬롯 배열**, "3쪽 2번" = **행 주소**(PostgreSQL `ctid`), 부록 = **TOAST·오버플로 페이지**.

실무 예:
- `SELECT ctid, * FROM t`에 `(0,1)`, `(0,2)`가 보인다. 0번 페이지의 1·2번 슬롯이다.
- 칼럼 하나를 `char(500)`로 넓혔더니 같은 행 수의 테이블이 15배 커지고 풀 스캔이 느려진다.
- 잔액만 반복 UPDATE하는 테이블이 VACUUM 없이 6배로 부푼다.

## 동작·원리

### 1. 파일 → 페이지

```text
  PostgreSQL 17 (기본 빌드)                     MySQL 8.4 InnoDB (기본 설정)
  테이블 1개 = 파일 여러 개                      테이블 1개 = .ibd 파일 1개 (file-per-table)
                                                 (파티션 테이블은 파티션마다 .ibd 1개)
    <filenode>      본 데이터 (main fork)        페이지 16KB (innodb_page_size)
    <filenode>_fsm  여유 공간 지도               행은 기본 키 순서의 B+트리 잎에 산다
    <filenode>_vm   가시성 지도                   (클러스터드 인덱스 = 테이블)
    1GB 넘으면 <filenode>.1, .2 … 로 쪼갠다
  페이지 8KB, 힙 = 순서 없는 페이지 묶음
```

- *힙 파일(heap file)*: 순서 없이 행을 담는 페이지 모음이다. 새 행은 빈자리가 있는 아무 페이지에나 들어간다(CMU 15-445 L3).
  - PostgreSQL의 테이블이 힙이다. 문서는 "테이블에서는 모든 페이지가 논리적으로 동등해, 어떤 행이든 어떤 페이지에나 저장될 수 있다"고 적는다(PG 17 문서 65.6).
- *클러스터드 인덱스*: InnoDB는 테이블 자체가 기본 키 B+트리다. 행 전체가 잎 페이지에 기본 키 순서로 놓인다(MySQL 8.4 17.6.2.1).
  - PK가 없으면 첫 번째 `UNIQUE`(키 칼럼 전부 `NOT NULL`) 인덱스가, 그것도 없으면 숨은 행 ID(`GEN_CLUST_INDEX`)가 클러스터드 키가 된다(17.6.2.1). 자세한 구조는 [08-btree-indexes](../08-btree-indexes/2-summary.md).
- 페이지 크기
  - PostgreSQL: "보통 8kB, 서버를 컴파일할 때 다른 크기를 고를 수 있다"(65.6). 한 설치 안에서는 한 크기만 쓴다.
  - InnoDB: 기본 16KB, 인스턴스 초기화 때 `innodb_page_size`로 정한다(17.6.2.2). 로컬 확인 `@@innodb_page_size = 16384`(예시, MySQL 8.4.10).

### 2. 슬롯 페이지 — 한 페이지 안의 배치

```text
  PostgreSQL 힙 페이지 8192바이트 (로컬 재현: 행 3개를 넣은 직후, 예시 PostgreSQL 17.11)

  0        24      36                                 8080     8120    8152   8192
  +--------+-------+----------- 빈 공간 --------------+--------+-------+-------+
  | 헤더   | 슬롯  |  ← pd_lower              pd_upper → | 행 3   | 행 2  | 행 1  |
  | 24B    | 1 2 3 |                                    | 34B+6  | 32B   | 34B+6 |
  +--------+-------+------------------------------------+--------+-------+-------+
            | | |                                          ^        ^       ^
            | | +------------------------------------------+        |       |
            | +---------------------------------------------------+        |
            +------------------------------------------------------------+
  슬롯(ItemId) = (오프셋, 길이, 상태) 4바이트.   슬롯은 앞에서 뒤로, 행은 뒤에서 앞으로 자란다.
```

- *슬롯 배열(line pointer, ItemId)*: 페이지 앞쪽의 (오프셋, 길이) 목록이다. 항목당 4바이트다(65.6).
- *pd_lower / pd_upper*: 빈 공간의 시작과 끝이다. 둘이 만나면 페이지가 찬 것이다.
- 로컬 재현 값: `lower = 36 = 24 + 3 × 4`, `upper = 8080`.
  - 행 1은 `8152`에서 34바이트다. `8192 − 34 = 8158`을 8바이트 경계로 내린 자리라 뒤에 6바이트가 빈다.
  - 행 2(32바이트)는 `8152 − 32 = 8120`에 딱 맞는다. 행 3(34바이트)은 `8120 − 34 = 8086`을 8바이트 경계로 내린 `8080`에 놓인다. 그림의 "+6"이 이 정렬 여백이다.
- **행 주소 = (페이지 번호, 슬롯 번호)**. PostgreSQL은 이것을 `ctid`(ItemPointer, 6바이트)라 부른다.
  - 슬롯은 해제될 때까지 움직이지 않는다. 그래서 행 데이터가 페이지 안에서 옮겨져도(빈 공간 압축) 주소는 그대로다(65.6).
  - 이 "한 번 거친 간접 참조"가 슬롯 페이지의 핵심이다. 인덱스는 슬롯을 가리키고, 슬롯이 실제 위치를 가리킨다.

InnoDB 페이지도 같은 생각이지만 모양이 조금 다르다.

```text
  InnoDB 인덱스 페이지 16KB (소스 storage/innobase/include/page0page.h)

  +------------+-----------+-------------------------------------+-------------+-----------+
  | 파일 헤더  | 페이지    | infimum → r1 → r2 → … → supremum    |  빈 공간    | 페이지    |
  | ·페이지    | 헤더      | (레코드는 키 순서의 단일 연결 리스트) |             | 디렉터리  |
  | 헤더       |           |                                     |             | slot slot |
  +------------+-----------+-------------------------------------+-------------+-----------+
                                                          슬롯 하나가 레코드 4~8개를 "소유"(양 끝 슬롯은 예외)
```

- InnoDB 레코드는 페이지 안에서 **키 순서로 연결 리스트**를 이룬다. 양 끝에 가짜 레코드 infimum·supremum이 있다.
- *페이지 디렉터리*: 페이지 끝의 2바이트 슬롯 배열이다. 슬롯마다 레코드 4~8개를 소유한다(`PAGE_DIR_SLOT_MIN_N_OWNED = 4`, `MAX = 8`). 단 첫 슬롯과 마지막 슬롯은 4개보다 적을 수 있다(같은 헤더 주석). 슬롯으로 이진 탐색한 뒤, 그 구간의 리스트를 몇 칸 따라간다.
- PostgreSQL 힙과의 차이: PG 힙 페이지는 **순서가 없고**, InnoDB 페이지는 **키 순서**다. 그래서 InnoDB 행 주소는 슬롯 번호가 아니라 클러스터드 키 값(보통 기본 키)이다(보조 인덱스가 그 키를 담는다, 08번).

### 3. 튜플 헤더 — 행 앞에 붙는 메타데이터

```text
  PostgreSQL 힙 튜플 (65.6 표 65.4)
  +---------+---------+-------+---------+-------------+-----------+--------+----------+-----------+
  | t_xmin  | t_xmax  | t_cid | t_ctid  | t_infomask2 | t_infomask| t_hoff | null 비트 | 칼럼 값…  |
  | 4B      | 4B      | 4B    | 6B      | 2B          | 2B        | 1B     | (선택)    |           |
  +---------+---------+-------+---------+-------------+-----------+--------+----------+-----------+
  |<-------------------- 고정 23바이트 (대부분의 기계) ------------------->|
  넣은 트랜잭션 · 지운(갱신한) 트랜잭션 · 다음 버전 주소 · 플래그 · 데이터 시작 오프셋(MAXALIGN 배수)
```

- 로컬 재현의 `t_hoff = 24`: 23바이트 헤더를 8바이트 경계로 올린 값이다(NULL 없는 행).
  - 행 1 = 24 + int 4 + `'alice'`(1바이트 짧은 길이 헤더 + 5) = 34바이트. 짧은 가변 길이 값은 1바이트 헤더를 쓴다(65.2).
- *null 비트맵*: NULL이 있는 행에만 붙는다. 칼럼당 1비트, 1 = NULL 아님(65.6).
- 헤더의 `t_xmin`·`t_xmax`가 MVCC 가시성의 재료다. 해석은 16번 mvcc가 다룬다.
- InnoDB는 행마다 숨은 필드를 붙인다(MySQL 8.4 17.3).
  - `DB_TRX_ID` 6바이트: 마지막으로 넣거나 고친 트랜잭션.
  - `DB_ROLL_PTR` 7바이트: undo 로그 레코드를 가리킨다. 옛 버전은 거기서 재구성한다.
  - `DB_ROW_ID` 6바이트: PK가 없어 InnoDB가 숨은 클러스터드 인덱스(`GEN_CLUST_INDEX`)를 만들 때만 인덱스에 쓰인다.

**칼럼 순서와 정렬 패딩.** PostgreSQL은 고정 길이 값을 타입의 정렬 경계에 맞춰 놓는다(65.6 "make sure you have the right alignment").

```text
  로컬 재현(예시, PostgreSQL 17.11) — 같은 값, 칼럼 순서만 다름
  (a bool, b bigint, c bool, d bigint)  →  행 56바이트   24 + 1+7(패딩) + 8 + 1+7(패딩) + 8
  (b bigint, d bigint, a bool, c bool)  →  행 42바이트   24 + 8 + 8 + 1 + 1
```

### 4. UPDATE는 어디에 쓰이나 — 두 엔진이 반대다

```text
  PostgreSQL: 새 버전을 새 자리에                    InnoDB: 제자리 + 옛 값은 undo로
  (로컬 재현: id=2를 'bob' → 'bobby')

  슬롯 2 → [bob   xmin=1346 xmax=1347 ctid=(0,4)]    클러스터드 레코드 [bobby, TRX_ID=새, ROLL_PTR]──┐
  슬롯 4 → [bobby xmin=1347 xmax=0    ctid=(0,4)]                                                  v
  옛 버전은 페이지에 남는다(죽은 튜플) → VACUUM이 치운다   undo 로그 [bob ...]  → purge가 치운다
```

- PostgreSQL: 옛 튜플의 `t_xmax`에 갱신 트랜잭션을 적고, `t_ctid`를 새 버전 `(0,4)`로 돌린다. 새 튜플은 새 슬롯에 들어간다. 로컬 재현에서 `pd_lower`가 36→40, `pd_upper`가 8080→8040으로 움직였다.
- *HOT(heap-only tuple)*: 두 조건이 맞으면 인덱스에 새 항목을 넣지 않는다(65.7).
  - 인덱스가 참조하는 칼럼을 바꾸지 않는다(BRIN 같은 요약 인덱스는 예외).
  - 옛 행이 있는 **같은 페이지**에 새 버전이 들어갈 자리가 있다.
  - 자리를 남겨 두려면 테이블 `fillfactor`를 낮춘다(65.7).
- InnoDB: 클러스터드 인덱스 레코드는 **제자리**에서 고친다. 옛 버전을 만들 정보는 undo 로그(rollback segment)에 둔다(17.3). 보조 인덱스는 제자리 수정을 하지 않는다. 보조 인덱스 칼럼이 바뀌는 UPDATE면 옛 레코드에 삭제 표시를 하고 새 레코드를 넣는다(17.3).
- 그래서 "갱신이 테이블을 부풀린다"의 모양이 다르다. PG는 **힙 페이지**가, InnoDB는 **undo**와 보조 인덱스의 삭제 표시 레코드가 purge 전까지 쌓인다.

### 5. 한 페이지에 안 들어가는 값 — TOAST와 오버플로 페이지

```text
  PostgreSQL TOAST (65.2)                               InnoDB DYNAMIC 행 형식 (17.10)

  행이 TOAST_TUPLE_THRESHOLD(보통 2kB)보다 크면         행이 최대 행 길이(16KB 페이지에서 8KB 조금 못 미침)를 넘으면
   1) 압축 시도 (기본 pglz)                              가장 긴 가변 길이 칼럼부터 페이지 밖으로
   2) 그래도 크면 칼럼 값을 TOAST 테이블로                 클러스터드 레코드에는 20바이트 포인터만
      ~2000바이트 청크로 잘라 (chunk_id, chunk_seq)       값은 오버플로 페이지의 단일 연결 리스트
      본 행에는 18바이트 TOAST 포인터만                   TEXT·BLOB이 40바이트 이하면 행 안에 둔다
   목표: 행이 TOAST_TUPLE_TARGET(보통 2kB) 아래로
```

로컬 재현(예시, PostgreSQL 17.11) — `body text`에 세 값을 넣었다.

```text
  id | 원래 길이 | 저장 크기 | 압축  | 힙 행 길이(lp_len)
   1 |       5  |       6  |       |   34    ← 그대로 행 안
   2 |   10000  |     125  | pglz  |  153    ← 'aaaa…'는 잘 압축돼 행 안에 남음
   3 |    9600  |    9600  |       |   46    ← md5 문자열은 압축 안 됨 → TOAST 테이블로, 행엔 18B 포인터
```

- 네 가지 칼럼 전략(65.2): `PLAIN`(압축·밖으로 둘 다 안 함) · `EXTENDED`(둘 다, 대부분 타입의 기본) · `EXTERNAL`(밖으로만) · `MAIN`(압축 위주, 밖은 최후 수단).
- TOAST 가능한 값의 논리 크기 상한은 1GB다(가변 길이 헤더 2비트를 TOAST가 쓰기 때문, 65.2).
- UPDATE가 TOAST된 칼럼을 바꾸지 않으면 TOAST 비용은 없다(65.2).
- InnoDB의 한계는 행 단위로 드러난다. 로컬 재현(예시, MySQL 8.4.10)에서 `CHAR(255) latin1` 40개짜리 테이블을 만들자 `ERROR 1118 (42000): Row size too large (> 8126)`이 났다. 255바이트짜리 고정 길이 칼럼은 밖으로 뺄 수 없기 때문이다(768바이트 이상인 고정 길이 칼럼만 가변 길이로 인코딩돼 밖으로 나갈 수 있다, 17.10).

### 6. 행 너비 → 페이지당 행 수 → 스캔 I/O

```text
  로컬 재현(예시, PostgreSQL 17.11) — 10만 행, sum(v) 풀 스캔
  테이블                         페이지   페이지당 행   크기      읽은 버퍼
  narrow (id int, v int)          443       226        3.5MB      443
  wide   (id int, v int,         6667        15        52MB      6667
          pad char(500))
```

- 필요한 칼럼은 `v` 하나인데 wide는 15배 많은 페이지를 읽는다. 행 저장은 **행 전체를 한 덩어리로** 읽기 때문이다. 이 한계가 37번 컬럼 저장의 출발점이다.

## 쓰이는 자료구조·알고리즘

- **슬롯 배열(간접 참조 테이블)**: 바깥 주소(페이지, 슬롯)와 안쪽 위치(오프셋)를 떼어 놓는다. 가상 메모리의 페이지 테이블과 같은 발상이다([os/10-paging-and-tlb](../../os/10-paging-and-tlb/2-summary.md)).
- **양끝에서 자라는 두 영역**: 슬롯은 앞에서, 데이터는 뒤에서 자란다. 스택과 힙이 마주 자라는 주소 공간 배치와 같다.
- **정렬 연결 리스트 + 희소 디렉터리**(InnoDB): 레코드는 키 순서 리스트, 디렉터리는 4~8개마다 하나. 이진 탐색으로 구간을 찾고 선형으로 마무리한다. 스킵 리스트의 한 층만 쓴 모양이다([data-structure/12-skip-list](../../data-structure/12-skip-list/2-summary.md)).
- **여유 공간 지도(FSM)**: PostgreSQL은 새 행이 들어갈 페이지를 찾으려고 페이지별 여유 공간을 별도 포크(`_fsm`)에 적어 둔다(65.1).
- **청크 분할 + 인덱스**(TOAST): 큰 값을 `(chunk_id, chunk_seq)`로 잘라 저장하고, 그 쌍의 유니크 인덱스로 순서대로 다시 붙인다(65.2).
- **압축**: pglz(기본) 또는 lz4(빌드에 포함됐을 때). 로컬 확인 `default_toast_compression = pglz`.

## 적용 — 풀어나가는 법

**1) 행이 실제로 어디 있는지 본다 (PostgreSQL).**

```sql
-- PostgreSQL 17: 행 주소
SELECT ctid, * FROM t WHERE id = 2;

-- 페이지 내부 (pageinspect 확장, 슈퍼유저)
CREATE EXTENSION pageinspect;
SELECT lower, upper, special, pagesize FROM page_header(get_raw_page('t', 0));
SELECT lp, lp_off, lp_len, t_xmin, t_xmax, t_ctid, t_hoff
FROM heap_page_items(get_raw_page('t', 0));
```

**2) 테이블이 몇 페이지이고 얼마나 비었는지 본다.**

```sql
-- PostgreSQL
SELECT relpages, reltuples, pg_size_pretty(pg_relation_size('acct'))   -- relpages는 ANALYZE/VACUUM 때 갱신
FROM pg_class WHERE relname = 'acct';
SELECT * FROM pgstattuple('acct');     -- dead_tuple_percent, free_percent (테이블 전체를 읽는다)
SELECT n_live_tup, n_dead_tup, n_tup_upd, n_tup_hot_upd
FROM pg_stat_user_tables WHERE relname = 'acct';

-- MySQL 8.4
SELECT data_length, data_length/16384 AS pages, table_rows, avg_row_length
FROM information_schema.tables WHERE table_schema = 'w06' AND table_name = 'o_seq';   -- 추정값, ANALYZE TABLE 후 갱신
```

**3) 넓은 테이블을 설계할 때.**
- 자주 읽는 좁은 칼럼과 가끔 읽는 큰 칼럼(본문·JSON·이미지)을 나눈다. PG는 큰 값을 TOAST가 이미 압축하거나 밖으로 빼므로, 문제는 주로 **고정 길이로 넓은 칼럼**(`char(n)`, 큰 칼럼 여럿)에서 생긴다.
- `SELECT *`를 피한다. TOAST된 값은 선택될 때만 꺼내 온다(65.2).
- PG에서 칼럼 순서를 `bigint`·`timestamptz` 같은 8바이트 → 4바이트 → 가변 길이·`bool` 순으로 두면 패딩이 준다(위 56 vs 42바이트).

**4) 갱신이 잦은 테이블 (PostgreSQL).**

```sql
-- 같은 페이지에 새 버전 자리를 남겨 HOT 확률을 높인다
CREATE TABLE acct2 (id int PRIMARY KEY, bal int) WITH (fillfactor = 70);   -- 값은 예시
ALTER TABLE acct SET (fillfactor = 70);   -- 이후 새로 채워지는 페이지부터 적용
-- 자주 바뀌는 칼럼에는 인덱스를 걸지 않는다(걸면 HOT 불가)
```

**5) 앱에서 보는 모양 (Java).** 드라이버는 페이지를 모른다. 차이는 가져오는 칼럼 수에서 난다.

```java
// JPA: 큰 칼럼을 기본 로딩에서 빼고 싶을 때 — 엔티티를 나누거나 DTO 프로젝션으로 필요한 칼럼만
record OrderRow(long id, int amount) {}
List<OrderRow> rows = em.createQuery(
    "select new com.example.OrderRow(o.id, o.amount) from Order o where o.status = :s", OrderRow.class)
  .setParameter("s", "PAID").getResultList();   // body(대형 TEXT)는 읽지 않는다
```

## 장애 시나리오와 대처

**1) 넓은 행 → 페이지당 행 수 감소 → 스캔 I/O 증가 (⚠)**
- 현상: 행 수는 그대로인데 리포트 쿼리가 몇 배 느려졌다. 칼럼을 추가·확장한 배포 직후부터다.
- 보이는 형태: `EXPLAIN (ANALYZE, BUFFERS)`의 `Buffers: shared read=`가 크게 늘었다. 로컬 재현에서 443 → 6667 버퍼, `relpages` 443 → 6667.
- 원인: 행 저장은 행 전체를 한 덩어리로 읽는다. 행이 넓어지면 같은 행을 읽으려고 더 많은 페이지를 읽는다. 버퍼 풀에 올라가는 행 수도 준다(07번).
- 대처: 큰 칼럼을 별도 테이블로 나눈다. 고정 길이 `char(n)`을 가변 길이로 바꾼다. 분석 쿼리는 컬럼 저장으로 보낸다(37번).

**2) UPDATE 반복 → 페이지 부풀림(bloat) (⚠)**
- 현상: 행 수는 1만 개 그대로인데 테이블 파일이 계속 커진다. 풀 스캔이 느려진다.
- 보이는 형태: 로컬 재현(예시, PostgreSQL 17.11, autovacuum 끔) — 1만 행에 `UPDATE … SET bal = bal + 1` 5번.
  - 힙 368,640 → 2,179,072바이트(45 → 266페이지, 약 6배). PK 인덱스 245,760 → 909,312바이트.
  - `pgstattuple`: `dead_tuple_percent 73.43`. `n_dead_tup 50000`, `n_tup_hot_upd 0`.
- 원인: PG의 UPDATE는 새 버전을 새 자리에 쓴다(4절). 옛 버전은 VACUUM이 치울 때까지 자리를 차지한다. 페이지가 꽉 차 HOT도 못 해 인덱스까지 커졌다.
- 대처
  - autovacuum이 따라가는지 본다(`n_dead_tup`, `last_autovacuum`). 긴 트랜잭션이 옛 스냅숏을 붙들면 VACUUM도 못 치운다(16번).
  - 일반 `VACUUM`은 공간을 **재사용 가능으로 표시**만 한다. 파일 크기는 그대로다(끝 페이지가 통째로 빈 경우만 예외, PG 17 문서 24.1.2). 로컬 재현에서도 VACUUM 뒤 `free_percent 83.09`, 크기 2,179,072 그대로. 이어서 UPDATE 1회를 해도 파일이 커지지 않았다.
  - 줄여야 하면 `VACUUM FULL`(368,640바이트로 복귀). 단 `ACCESS EXCLUSIVE` 락과 테이블 크기만큼의 추가 디스크가 든다(24.1.2).
  - fillfactor를 낮추고, 자주 바뀌는 칼럼에서 인덱스를 뺀다. 로컬 재현에서 `fillfactor = 50`이면 5만 번 중 30,056번이 HOT였고 인덱스는 688,128바이트로 덜 컸다.
- MySQL InnoDB의 같은 증상: 힙이 아니라 undo가 쌓인다. 긴 트랜잭션이 있으면 update undo를 버리지 못해 undo 테이블스페이스가 커진다(17.3). `SHOW ENGINE INNODB STATUS`의 `History list length`를 본다. 삭제·삽입이 같은 속도로 계속되면 purge가 밀려 테이블이 커질 수 있다(17.3, `innodb_max_purge_lag`).

**3) 칼럼을 추가했더니 `Row size too large`**
- 현상: MySQL에서 `CREATE TABLE`·`ALTER TABLE ADD COLUMN`이 실패한다.
- 보이는 형태: `ERROR 1118 (42000): Row size too large (> 8126). Changing some columns to TEXT or BLOB may help.`(로컬 재현, MySQL 8.4.10, `innodb_strict_mode = ON`)
- 원인: InnoDB 최대 행 길이는 페이지의 절반 조금 아래다(16KB 페이지면 8KB 조금 아래, 17.11.2). 가변 길이 칼럼(과 가변 길이로 인코딩되는 768바이트 이상 고정 길이 칼럼, 17.10)만 페이지 밖으로 나갈 수 있다. 768바이트 미만 고정 길이 칼럼이 많으면 밖으로 뺄 것이 없다.
- 대처: 큰 고정 길이 칼럼을 `VARCHAR`·`TEXT`로 바꾸거나 테이블을 나눈다. 칼럼 수 자체를 줄이는 설계(속성 테이블·JSON 칼럼)를 검토한다.

**4) 대형 값이 든 테이블에서 `SELECT *`가 느리다**
- 현상: 목록 API 한 번에 수 MB가 오간다. DB CPU와 네트워크가 튄다.
- 보이는 형태: 같은 쿼리를 칼럼만 줄여 돌리면 빨라진다. PG에서 `pg_column_size(body)`가 크고 TOAST 테이블(`pg_class.reltoastrelid`) 크기가 본 테이블보다 크다.
- 원인: TOAST 값은 선택되면 TOAST 테이블에서 청크를 읽어 붙이고 압축을 푼다(65.2). 목록 화면에는 필요 없는 일이다.
- 대처: 목록 쿼리는 필요한 칼럼만 고른다(DTO 프로젝션). 본문은 상세 조회에서만 읽는다.

## 핵심 문장

- DB는 파일을 고정 크기 페이지(PostgreSQL 기본 8KB, InnoDB 기본 16KB)로 나누고, 페이지 안은 슬롯 배열로 행을 가리킨다.
- 행 주소는 (페이지, 슬롯)이다. 슬롯이 한 번 간접 참조를 해 주므로 행이 페이지 안에서 움직여도 주소는 그대로다.
- PostgreSQL 튜플은 23바이트 헤더(`xmin`·`xmax`·`ctid` 등)를 달고, InnoDB 행은 숨은 `DB_TRX_ID`·`DB_ROLL_PTR`를 단다. 둘 다 MVCC의 재료다.
- PostgreSQL UPDATE는 새 버전을 새 자리에 쓰고 VACUUM이 치운다. InnoDB는 제자리에 쓰고 옛 값은 undo에 둔다. 부풀어 오르는 곳이 다르다.
- 한 페이지에 안 들어가는 값은 PG는 TOAST(2kB 기준·압축 우선), InnoDB는 오버플로 페이지(20바이트 포인터)로 뺀다.
- 행이 넓으면 페이지당 행 수가 줄어 스캔 I/O가 늘어난다. 칼럼 하나만 필요해도 행 전체를 읽는 것이 행 저장의 한계다.

## 관련 주제·근거

- 선행
  - [01-relational-model-and-algebra](../01-relational-model-and-algebra/2-summary.md) — 릴레이션·튜플
  - [architecture/16 storage-media-workload](../../architecture/16-storage-media-workload/2-summary.md) — 블록 단위 I/O, 순차/랜덤
- 후속·연결
  - [07-buffer-pool](../07-buffer-pool/2-summary.md) — 페이지를 메모리에 올리는 층
  - [08-btree-indexes](../08-btree-indexes/2-summary.md) — InnoDB 클러스터드 인덱스, 인덱스가 가리키는 행 주소
  - [37-row-vs-column-storage](../37-row-vs-column-storage/2-summary.md) — 행 전체를 읽는 한계와 컬럼 저장
  - [16-mvcc](../16-mvcc/2-summary.md) — `xmin`·`xmax` 가시성, VACUUM
  - [os/22-file-system-implementation](../../os/22-file-system-implementation/2-summary.md) — 블록·간접 참조
- 문서
  - PostgreSQL 17 문서 65.1 Database File Layout(1GB 세그먼트, `_fsm`·`_vm`) <https://www.postgresql.org/docs/17/storage-file-layout.html>
  - PostgreSQL 17 문서 65.2 TOAST(2kB 기준, 청크 약 2000바이트, 18바이트 포인터, 4 전략, 1GB 상한) <https://www.postgresql.org/docs/17/storage-toast.html>
  - PostgreSQL 17 문서 65.6 Database Page Layout(페이지 헤더 24바이트, ItemId 4바이트, 튜플 헤더 23바이트, null 비트맵) <https://www.postgresql.org/docs/17/storage-page-layout.html>
  - PostgreSQL 17 문서 65.7 Heap-Only Tuples <https://www.postgresql.org/docs/17/storage-hot.html>
  - PostgreSQL 17 문서 24.1.2 Recovering Disk Space(VACUUM vs VACUUM FULL) <https://www.postgresql.org/docs/17/routine-vacuuming.html>
  - MySQL 8.4 Reference Manual 17.3 InnoDB Multi-Versioning(`DB_TRX_ID` 6B·`DB_ROLL_PTR` 7B·`DB_ROW_ID` 6B, undo, purge) <https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html>
  - MySQL 8.4 17.6.2.1 Clustered and Secondary Indexes · 17.6.2.2 Physical Structure(16KB) <https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html>
  - MySQL 8.4 17.10 InnoDB Row Formats(DYNAMIC 기본, 20바이트 포인터, 40바이트 이하 인라인) <https://dev.mysql.com/doc/refman/8.4/en/innodb-row-format.html>
  - MySQL 8.4 17.11.2 File Space Management(최대 행 길이 ≈ 페이지 절반) <https://dev.mysql.com/doc/refman/8.4/en/innodb-file-space.html>
- 소스
  - mysql/mysql-server `storage/innobase/include/page0page.h` — `PAGE_DIR_SLOT_MIN_N_OWNED = 4`, `MAX = 8`, infimum·supremum
- 강의: CMU 15-445 Fall 2024 L3 Database Storage I(힙 파일, 슬롯 페이지, 레코드 ID) · L4 Database Storage II(단편화, 오버플로 페이지)
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `pageinspect`로 슬롯·튜플 헤더·UPDATE 전후, narrow vs wide 페이지 수, UPDATE 5회 bloat와 VACUUM/VACUUM FULL, fillfactor 50의 HOT 수, TOAST 세 값, 칼럼 순서 패딩, InnoDB `ERROR 1118`
