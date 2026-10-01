# database/48-search-index-sync-and-reindexing — DB → 검색 인덱스 동기화와 무중단 재색인 — 정리 (힌트)

## 해결하는 문제

상품의 원본은 DB에 있다. 검색은 검색 엔진이 한다. 같은 데이터가 두 곳에 있다.

```text
  [주문/상품 DB] ──원본(source of truth)
        │  무엇이 바뀌었는지 어떻게 전하나?
        ▼
  [검색 인덱스] ──파생 데이터(derived data): 언제든 DB에서 다시 만들 수 있어야 한다
```

- DB에서 상품을 지웠는데 검색에는 계속 나온다.
- 가격을 바꿨는데 검색 결과 카드는 옛 가격이다.
- 분석기를 바꾸려면 인덱스를 새로 만들어야 한다([46](../46-full-text-search-and-analyzers/2-summary.md)). 그동안 검색을 멈출 수는 없다.

쉬운 예: 도서관 장서 목록(DB)과 검색용 카드 서랍(인덱스)이다. 책을 들이거나 버릴 때마다 카드를 고쳐야 한다. 사서가 책은 버렸는데 카드를 깜빡하면, 카드를 보고 찾아온 사람은 빈 서가를 본다. 카드 체계를 바꿀 때는 새 서랍을 옆에 다 만든 뒤 이름표만 옮겨 단다.

똑같은 구조다.

- 카드 고치기 = 동기화(이중 쓰기 또는 변경 로그 구독)
- 새 서랍 + 이름표 옮기기 = 새 인덱스로 재색인 + 별칭(alias) 원자 교체

## 동작·원리

### 1. 이중 쓰기 — 앱이 두 곳에 쓴다

```text
  앱:  ① DB UPDATE/DELETE   ② ES index/delete
                │                  │
         성공 ──┘                  └── 실패 (타임아웃·ES 장애·앱 재시작)
  결과: DB에는 삭제됨, ES에는 남아 있음 → 삭제된 상품이 검색에 계속 노출
```

- 두 쓰기를 하나로 묶는 트랜잭션이 없다. 하나만 성공하는 경우를 막을 수 없다.
- 성공하더라도 **순서**가 꼬인다.

```text
  요청 A: 가격 100 → DB 쓰기 ─────────────────────── ES 쓰기(100)  ← 늦게 도착
  요청 B: 가격  90 → DB 쓰기 ── ES 쓰기(90)
  DB 최종 = 90 (B가 나중 커밋)   ES 최종 = 100 (A가 나중 도착)   → 영구 불일치
```

- 기초(outbox·CDC 선택)는 [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md)(distributed `16-outbox-and-dual-write`)에 있다. 여기서는 **검색 인덱스 쪽**에서 생기는 문제를 본다.

### 2. 변경 로그 구독(CDC) — DB의 커밋 순서를 그대로 따른다

```text
  앱 ──쓰기──> [DB] ──커밋 순서대로 로그──> [WAL / binlog]
                                              │ 구독(CDC 커넥터)
                                              ▼
                                        [색인기] ──> [ES]
  앱은 DB에만 쓴다. 색인기는 로그를 처음부터(또는 저장한 위치부터) 재생한다.
```

- *CDC(change data capture)*: DB의 변경 로그에서 행 단위 변경을 뽑아 다른 시스템에 전하는 것이다.
- CDC가 받는 출력(MySQL binlog, PostgreSQL 논리 디코딩 기본 동작)은 커밋된 트랜잭션만, 커밋 순서대로 담는다. 그래서 두 가지가 풀린다.
  - 원시 WAL에는 커밋 전 변경도 있다. 논리 디코딩에서 진행 중 트랜잭션 스트리밍을 켜면 커밋·중단 전 변경이 온다(PostgreSQL 17 47.9). 그때 소비자는 커밋을 확인한 뒤에 적용한다.
  - 한쪽만 성공: 색인기가 죽어도 로그 위치부터 다시 읽는다(적어도 한 번).
  - 순서 꼬임: 같은 행의 변경은 커밋 순서대로 온다.

로컬 재현(예시, MySQL 8.4.10, `binlog_format = ROW`) — 행 하나를 INSERT·UPDATE·DELETE한 뒤 `SHOW BINLOG EVENTS`:

```text
  Pos   Event_type   Info
  237   Query        BEGIN
  311   Table_map    table_id: 408 (w45.product)
  375   Write_rows   table_id: 408 flags: STMT_END_F
  467   Xid          COMMIT /* xid=6879 */
  660   Table_map    table_id: 408 (w45.product)
  724   Update_rows  table_id: 408 flags: STMT_END_F     ← ROW 형식: 변경 전후 행 이미지
  874   Xid          COMMIT /* xid=6880 */
  1058  Table_map    table_id: 408 (w45.product)
  1122  Delete_rows  table_id: 408 flags: STMT_END_F     ← 삭제도 이벤트로 남는다
  1214  Xid          COMMIT /* xid=6881 */
```

- 삭제가 로그에 이벤트로 남는다는 점이 중요하다. "주기적으로 `updated_at > 마지막 시각`을 조회"하는 방식은 **지워진 행을 볼 수 없다**.
- 그 방식은 늦게 커밋된 행도 놓칠 수 있다. `updated_at`은 트랜잭션 안에서 찍히고(PostgreSQL `now()`는 트랜잭션 시작 시각), 커밋은 그 뒤다. 아래 3절의 seq 커서와 같은 문제다.
- PostgreSQL은 논리 디코딩(logical decoding)으로 WAL에서 행 변경을 뽑는다. `wal_level = logical`이어야 한다.

```text
  (예시, PostgreSQL 17.11, wal_level = replica)
  SELECT pg_create_logical_replication_slot('w45_slot','test_decoding');
  ERROR:  logical decoding requires "wal_level" >= "logical"
```

- *복제 슬롯(replication slot)*: 구독자가 어디까지 읽었는지 서버가 기억하는 것이다. 구독자가 멈춰 있어도 슬롯이 필요로 하는 WAL과 시스템 카탈로그 행은 지워지지 않는다. 그래서 저장 공간을 계속 쓴다(PostgreSQL 17 47.2.2). 슬롯 지연을 감시해야 한다.

### 3. outbox 테이블 — 같은 트랜잭션에 "색인해 달라"를 적는다

로그를 직접 구독하기 어려우면 outbox 테이블을 둔다.

```sql
BEGIN;
UPDATE item SET price = 90, version = version + 1 WHERE id = 1;
INSERT INTO search_outbox(product_id, op, version) VALUES (1, 'upsert', 2);
COMMIT;   -- 둘 다 되거나 둘 다 안 된다
```

로컬 재현(예시, PostgreSQL 17.11):

```text
  ROLLBACK한 트랜잭션:  item 0행, outbox 0행, NOTIFY 도착 안 함
  COMMIT한 트랜잭션:    item 1행, outbox 1행
                        Asynchronous notification "search_outbox" with payload "1" received
  outbox의 seq = 2      ← 롤백된 트랜잭션이 1을 가져갔다(시퀀스는 롤백되지 않는다)
```

- `NOTIFY`는 트랜잭션이 커밋될 때만 전달된다(PostgreSQL 17 NOTIFY 문서). 색인기를 깨우는 신호로 쓸 수 있다. 다만 듣고 있지 않던 세션은 받지 못한다. 신호일 뿐 원본은 outbox 테이블이다.
- 시퀀스 값에는 빈틈이 생긴다(문서: 트랜잭션 중단·크래시). 빈틈은 유실이 아니다.

**함정: seq 순서 ≠ 커밋 순서**

로컬 재현(예시, PostgreSQL 17.11) — 세션 A가 seq를 먼저 받고 3초 뒤 커밋, 세션 B는 나중에 받고 바로 커밋:

```text
  t0  A: BEGIN; INSERT outbox → seq 3   (아직 커밋 전)
  t1  B: INSERT outbox → seq 4, 커밋
  t1  폴러: SELECT … WHERE seq > 2  → {4}        ← 3은 아직 안 보인다
          커서를 4로 옮긴다
  t3  A: COMMIT
  t4  폴러: WHERE seq > 4  → {}                  ← 3을 영원히 건너뛴다
      (확인용: WHERE seq > 2 → {3, 4})
```

- 시퀀스는 호출 순서로 번호를 준다. 커밋은 그 뒤 제각각 끝난다. "마지막 본 seq보다 큰 것"으로 폴링하면 늦게 커밋된 행을 놓친다.
- 대처
  - 처리한 행을 표시(또는 삭제)하고 "미처리 전부"를 읽는다. 커서를 쓰지 않는다.
  - 커서를 꼭 쓰면 "지금 진행 중인 가장 오래된 트랜잭션보다 앞"까지만 읽어야 한다. 다만 `pg_snapshot_xmin(pg_current_snapshot())`이 주는 것은 트랜잭션 ID라, `seq`만 저장한 위 스키마로는 안전한 seq 위치를 알 수 없다. 행마다 트랜잭션 ID 같은 정보를 더 적어야 해서 구현이 까다롭다.
  - 또는 로그 기반 CDC를 쓴다. 로그는 커밋 순서다.

### 4. 검색 쪽에서 순서를 지키는 법 — 외부 버전

```text
  색인기 A (늦음): PUT products/_doc/1?version=2&version_type=external   (가격 100)
  색인기 B (빠름): PUT products/_doc/1?version=3&version_type=external   (가격 90)  → 저장
  A 도착: version 2 ≤ 저장된 3 → 버전 충돌로 거부 → 최신 값 90 유지
```

- `version_type: external`: "지정한 버전이 저장된 문서의 버전보다 **엄격히 클 때만**(또는 문서가 없을 때) 색인한다"(elasticsearch-specification `VersionType`).
- 버전은 DB에서 단조 증가하는 값을 쓴다(행의 `version` 열, 로그 위치 등).
- 한계: 삭제된 문서의 버전 번호는 `index.gc_deletes`(기본 60초) 동안만 남는다(ES Index settings). 그보다 늦게 도착한 옛 upsert는 막지 못하고 삭제된 문서를 되살릴 수 있다. 삭제는 소프트 삭제 필드(예: `deleted: true` + 버전)로 두는 방법이 있다.

### 5. 무중단 재색인 — 새 인덱스 + 별칭 교체

```text
  단계 0  alias "products" ──> products_v1 (옛 매핑)
  단계 1  products_v2 생성 (새 매핑·분석기)
  단계 2  products_v1 → products_v2 복사 (Reindex API, 또는 DB에서 전체 다시 색인)
          이 사이에도 변경은 계속 들어온다 ─┐
  단계 3  재색인 시작 시점 이후 변경을 v2에 따라잡기 ◀─┘  (CDC 위치를 기록해 두고 재생)
  단계 4  POST _aliases { remove v1, add v2 }   ← 한 요청 = 원자적
          alias "products" ──> products_v2
  단계 5  검증 뒤 v1 삭제
```

- *별칭(alias)*: 인덱스를 가리키는 이름이다. 앱은 별칭으로만 읽고 쓴다.
- ES 문서: 여러 동작을 **한 번의 원자적 연산**으로 한다. 교체 중 별칭은 끊기지 않고, 두 대상을 동시에 가리키지도 않는다.
- 별칭이 여러 인덱스를 가리키고 `is_write_index`가 없으면 쓰기가 거부된다. 교체 과정에서 쓰기 대상을 명시한다.
- Reindex API 사실(ES 문서·스펙)
  - 원본의 `_source`가 켜져 있어야 한다. 대상 인덱스의 매핑·샤드 수는 **미리** 만들어 둔다. 설정을 복사하지 않는다.
  - `slices`를 쓰면 하위 요청마다 원본의 **스냅숏**을 조금씩 다른 시점에 잡는다. 즉 재색인은 시작 무렵의 원본 상태를 복사한다. 그 뒤의 변경은 따로 따라잡아야 한다.
  - `version_type: external`로 하면 원본 버전을 보존하고, 대상에 더 오래된 버전만 덮어쓴다.
  - 버전 충돌은 기본적으로 재색인을 중단시킨다(`conflicts: proceed`로 계속).
- 기존 필드의 타입은 바꿀 수 없다. 새 인덱스를 만들고 재색인한다(ES "Update mapping" 문서). `analyzer` 설정도 기존 필드에서 못 바꾼다.

### 6. 지연과 불일치 감지

```text
  끝에서 끝까지 지연 = DB 커밋 → 로그 읽기 → 색인 요청 → refresh(Elastic Stack 기본 1초) → 검색에 보임
```

- ES는 기본적으로 1초마다 refresh한다(Elastic Stack 기준. Elastic Cloud Serverless는 기본·최솟값 5초 — ES Index settings `index.refresh_interval`). 단, 최근 30초 동안 검색 요청이 없던 샤드는 refresh를 미룬다(ES near real-time 문서, `index.refresh_interval`). 색인 직후 검색되지 않는 것은 정상이다.
- 감시 항목
  - CDC 지연: 구독자가 읽은 위치와 DB 현재 위치의 차이(PostgreSQL `pg_replication_slots`의 `confirmed_flush_lsn` vs `pg_current_wal_lsn()`)
  - outbox 미처리 행 수와 가장 오래된 미처리 행의 나이
  - 대조(reconciliation): 주기적으로 DB와 인덱스의 건수·ID 집합·버전을 비교한다

## 쓰이는 자료구조·알고리즘

- **추가 전용 로그 재생** — WAL·binlog는 위치(LSN·파일+오프셋)부터, outbox는 미처리 표시로 다시 읽는다(seq는 커밋 순서가 아니다). 결과는 멱등 적용(같은 ID 덮어쓰기)이어야 한다. database [19-wal-and-logging](../19-wal-and-logging/2-summary.md)
- **단조 버전 비교** — 외부 버전 `>` 검사로 늦게 온 옛 변경을 버린다. 낙관적 동시성 제어와 같은 모양이다. [17-occ-and-timestamp-ordering](../17-occ-and-timestamp-ordering/2-summary.md)
- **포인터 원자 교체** — 별칭은 "현재 인덱스"를 가리키는 포인터다. 새 구조를 옆에 다 만든 뒤 포인터만 바꾼다(복사 후 교체).
- **집합 대조** — DB ID 집합과 인덱스 ID 집합의 차집합으로 누락·유령 문서를 찾는다. 크면 ID 범위별 해시로 먼저 비교한다(Merkle 트리 발상). [data-structure/27-merkle-tree](../../data-structure/27-merkle-tree/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 방식 고르기

```text
  규모 작고 지연 몇 분 허용, 삭제는 소프트 삭제 → 주기 배치(updated_at 기준) + 소프트 삭제 필드
  이미 트랜잭션으로 쓰는 앱이 있다              → outbox + 색인 워커 (미처리 행 방식)
  여러 소비자, 낮은 지연, 운영 역량 있음        → 로그 기반 CDC(논리 디코딩/binlog) → 큐 → 색인기
  어떤 방식이든                                → 외부 버전 + 정기 대조 + 전체 재색인 경로
```

- 어떤 방식이든 전체 재색인 경로가 있어야 한다. 파생 데이터는 "언제든 원본에서 다시 만들 수 있다"는 것이 전제다.

### 2. outbox 색인 워커 (Java, JDBC)

```java
// 미처리 행을 잠그고 가져온다. 여러 워커가 같은 행을 잡지 않게 SKIP LOCKED (PostgreSQL 9.5+ / MySQL 8.0+)
String pick = """
    SELECT seq, product_id, op, version FROM search_outbox
    WHERE processed_at IS NULL
    ORDER BY seq LIMIT 100
    FOR UPDATE SKIP LOCKED""";
conn.setAutoCommit(false);
List<Row> rows = query(conn, pick);
for (Row r : rows) {
    Product p = loadCurrent(conn, r.productId());      // 이벤트 내용이 아니라 DB의 현재 상태를 읽는다
    if (p == null || p.deleted()) es.delete("products", r.productId(), r.version(), "external");
    else es.index("products", p, r.version(), "external");  // 늦게 온 옛 버전은 ES가 거부
    // es.delete·es.index는 예시 래퍼. 409(version_conflict)는 "이미 같거나 새 버전이 있다"는 뜻 → 처리 완료로 본다
}
markProcessed(conn, rows);                               // UPDATE … SET processed_at = now()
conn.commit();
```

- 커서(`seq > last`)를 쓰지 않고 `processed_at IS NULL`로 읽는다. 로컬 재현의 "늦게 커밋된 seq 3을 건너뛰는" 문제가 없다.
- ES 쓰기가 성공하고 `commit()` 전에 워커가 죽으면 같은 행을 다시 처리한다(적어도 한 번). 외부 버전은 같은 버전도 409 충돌로 거부한다("엄격히 클 때만"). 그래서 재시도는 ES 상태를 바꾸지 않지만, 위 주석처럼 409를 성공으로 처리해야 워커가 그 행에서 막히지 않는다.
- `outbox`가 계속 커지지 않게 처리된 행을 주기적으로 지운다.
- 이 테이블 컬럼(`processed_at`)은 로컬 재현 테이블에는 없다. 예시 스키마다.

### 3. 무중단 재색인 절차

```text
  1. 새 인덱스 products_v2 생성 (매핑·분석기·샤드 수)
  2. 색인기를 "두 인덱스에 모두 쓰기"로 바꾸거나, 지금 CDC 위치 P(커밋 순서인 LSN·binlog 위치)를 기록한다
     (outbox seq는 커밋 순서가 아니라 P로 쓸 수 없다. outbox면 v2용 미처리 표시로 재생한다)
  3. 전체 복사: _reindex(v1 → v2, version_type external, conflicts: proceed) 또는 DB에서 전체 색인
     (이중 쓰기가 v2에 새 버전을 먼저 넣으면 옛 버전 복사가 충돌한다. 기본값은 재색인 중단이다)
  4. P 이후 변경을 v2에 재생해 따라잡는다 (외부 버전이라 겹쳐도 옛 값이 새 값을 덮지 않는다)
     재생(또는 이중 쓰기)은 별칭 교체 뒤까지 계속한다. 따라잡은 직후 멈추면 교체 전까지의 변경이 v2에서 빠진다
  5. 대조: 건수·표본 문서·주요 질의 결과를 v1과 비교
  6. POST _aliases { remove v1, add v2 (is_write_index) } — 한 요청
  7. 지켜본 뒤 v1 삭제 (되돌릴 수 있게 한동안 둔다)
```

```json
POST _aliases
{ "actions": [
    { "remove": { "index": "products_v1", "alias": "products" } },
    { "add":    { "index": "products_v2", "alias": "products", "is_write_index": true } } ] }
```

### 4. 불일치 감지 쿼리

```sql
-- outbox 적체 (PostgreSQL)
SELECT count(*) AS pending, now() - min(created_at) AS oldest_age
FROM search_outbox WHERE processed_at IS NULL;

-- 논리 복제 슬롯 지연 (PostgreSQL, wal_level = logical 일 때)
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)) AS lag
FROM pg_replication_slots WHERE slot_type = 'logical';
```

- 위 `lag`는 구독자 확인 위치 기준이다. 슬롯이 실제로 붙잡는 WAL 양은 `restart_lsn` 기준으로 본다(`pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)`, 그리고 `wal_status` 열).
- 대조 배치: DB에서 `id, version`을 ID 범위로 읽고, ES에서 같은 범위를 `_source: false` + `version: true`로 읽어 비교한다. 차이는 재색인 대기열에 넣는다.

## 장애 시나리오와 대처

### 1. 이중 쓰기 중 검색 쪽 실패 → 삭제된 상품이 계속 노출

- **현상**: 판매 중지된 상품이 검색에 나온다. 눌러 보면 404다.
- **보이는 형태**: 앱 로그에 ES 호출 타임아웃·5xx가 DB 커밋 뒤에 찍혀 있다. DB `SELECT … WHERE id = ?`는 0행, ES `GET products/_doc/{id}`는 문서가 있다.
- **원인**: DB 삭제는 커밋됐고 ES 삭제는 실패했다. 재시도가 없거나 재시도 전에 프로세스가 죽었다.
- **대처**: 긴급 — 대조 배치로 유령 문서를 찾아 지운다. 검색 결과를 보여 주기 전에 DB 상태로 한 번 거르는 방어도 쓸 수 있다(비용이 든다). 근본 — outbox 또는 CDC로 바꿔 "DB 커밋 = 색인 요청 기록"을 한 트랜잭션으로 묶는다.

### 2. 매핑 변경을 제자리 재색인 → 검색 공백

- **현상**: 분석기를 바꾸려고 인덱스를 지우고 같은 이름으로 다시 만들었다. 그동안 검색이 0건이거나 일부만 나온다.
- **보이는 형태**: 재색인 시간 동안 검색 결과 수가 0에서 서서히 오른다. 에러 대신 빈 결과라 알람이 늦다.
- **원인**: 앱이 인덱스 이름을 직접 쓴다. 새 인덱스가 다 차기 전에 읽기가 들어온다.
- **대처**: 앱은 별칭만 쓰게 한다. 새 인덱스를 옆에 만들어 다 채우고 검증한 뒤 `_aliases`로 한 번에 교체한다. 옛 인덱스는 되돌리기용으로 잠시 남긴다.

### 3. 재색인 중 들어온 변경 유실

- **현상**: 재색인 후 별칭을 바꿨더니 최근 몇 시간의 가격 변경·삭제가 반영돼 있지 않다.
- **보이는 형태**: 대조에서 v2의 버전이 DB보다 낮은 문서, v2에만 있는 삭제된 문서가 나온다.
- **원인**: Reindex는 시작 무렵의 원본 스냅숏을 복사한다. 색인기는 계속 v1에만 썼다.
- **대처**: 재색인 시작 전에 CDC 위치(커밋 순서)를 기록하고, 복사가 끝나면 그 위치부터 v2에 재생한다(outbox면 seq 위치 대신 미처리 표시). 또는 재색인 기간에 색인기가 v1·v2 둘 다에 쓴다. 어느 쪽이든 v2 적용은 별칭 교체 뒤까지 계속한다. 외부 버전을 써서 복사와 재생이 겹쳐도 옛 값이 새 값을 덮지 않게 한다(이때 `_reindex`는 `conflicts: proceed`).

### 4. 폴링 커서가 늦게 커밋된 변경을 건너뛴다

- **현상**: 드물게 특정 상품만 검색에 반영되지 않는다. 재현이 어렵다.
- **보이는 형태**: 해당 outbox 행은 있는데 색인 로그에 처리 기록이 없다. seq가 이미 처리한 최댓값보다 작다.
- **원인**: "마지막 seq보다 큰 것" 폴링. 시퀀스는 커밋 순서가 아니다(로컬 재현: 3이 4보다 늦게 커밋되어 건너뜀).
- **대처**: 미처리 표시 방식으로 바꾼다. 또는 행에 트랜잭션 ID를 함께 적고 진행 중 트랜잭션의 최소 xmin 뒤는 읽지 않는다(seq만으로는 안 된다). 또는 로그 기반 CDC로 옮긴다.

### 5. CDC 슬롯이 멈춰 DB 디스크가 찬다

- **현상**: 색인기를 며칠 내려 둔 사이 DB 서버 디스크 사용량이 계속 오른다.
- **보이는 형태**: `pg_replication_slots`에서 `active = f`인 논리 슬롯의 지연이 수십 GB. `pg_wal` 디렉터리가 커진다.
- **원인**: 슬롯은 구독자가 확인하지 않은 WAL을 지우지 못하게 잡는다.
- **대처**: 슬롯 지연 알람을 둔다. `max_slot_wal_keep_size`로 슬롯이 붙잡을 WAL 양에 상한을 둔다(PostgreSQL 17 기본 -1 = 무제한). 상한을 넘으면 필요한 WAL이 지워져 그 슬롯의 구독자는 더 이어 가지 못할 수 있다. 그때는 전체 재동기화(재색인)로 복구한다. 버릴 슬롯은 `pg_drop_replication_slot`으로 지운다.

## 핵심 문장

- 검색 인덱스는 파생 데이터다. DB가 원본이고, 인덱스는 언제든 원본에서 다시 만들 수 있어야 한다.
- 이중 쓰기는 "한쪽만 성공"과 "순서 꼬임"을 피할 수 없다. 커밋 순서를 담은 로그(CDC)나 같은 트랜잭션의 outbox로 옮긴다.
- 시퀀스 번호는 커밋 순서가 아니므로 "마지막 seq보다 큰 것" 폴링은 늦게 커밋된 행을 놓친다.
- 외부 버전(`version_type: external`)은 늦게 도착한 옛 변경을 검색 쪽에서 거부하게 한다.
- 무중단 재색인은 새 인덱스를 옆에 만들고, 재색인 중 변경을 따라잡은 뒤, 별칭을 한 요청으로 원자 교체하는 것이다.

## 관련 주제·근거

버전 기준: PostgreSQL 17(로컬 17.11), MySQL 8.4(로컬 8.4.10), Elasticsearch 현행 문서와 elasticsearch-specification(2026-10 확인). Elasticsearch 서버는 로컬에 없다.

- 선행
  - [46-full-text-search-and-analyzers](../46-full-text-search-and-analyzers/2-summary.md) — 분석기 변경 = 재색인
  - distributed `16-outbox-and-dual-write` → [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md)
- 연결
  - data-engineering `05-change-data-capture`(초기 스냅숏·증분 스냅숏·DDL) — 미작성, [data-engineering/README](../../data-engineering/README.md)
  - [47-autocomplete-and-typeahead](../47-autocomplete-and-typeahead/2-summary.md) — completion weight 갱신 = 재색인
  - [systems/outbox-vs-dispatch-log](../../systems/outbox-vs-dispatch-log/2-summary.md)
  - [34-large-backfill-and-batch-dml](../34-large-backfill-and-batch-dml/2-summary.md) — 전체 재색인의 청크·스로틀
- Elasticsearch 문서·스펙
  - Aliases — "multiple actions in a single atomic operation", `is_write_index` <https://www.elastic.co/guide/en/elasticsearch/reference/current/aliases.html>
  - Reindex API — `_source` 필요, 대상 매핑 사전 생성, `version_type`·`op_type`·`conflicts`, `slices`별 스냅숏 <https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-reindex.html> · elasticsearch-specification `specification/_global/reindex/ReindexRequest.ts`
  - `specification/_types/common.ts` `VersionType`(internal·external·external_gte)
  - Update mapping("You cannot change the field type of an existing field") · Index settings(`index.refresh_interval` Elastic Stack 1s·Serverless 5s, `index.gc_deletes` 60s) <https://www.elastic.co/docs/reference/elasticsearch/index-settings/index-modules> · Delete API(`version`·`version_type`) <https://www.elastic.co/docs/api/doc/elasticsearch/operation/operation-delete> · Near real-time search
- PostgreSQL 17 문서
  - 47 Logical Decoding — 47.2 개념(복제 슬롯, WAL 보존) <https://www.postgresql.org/docs/17/logicaldecoding-explanation.html> · 47.9 진행 중 트랜잭션 스트리밍 <https://www.postgresql.org/docs/17/logicaldecoding-streaming.html>
  - 9.27 System Information Functions — `pg_snapshot_xmin`은 트랜잭션 ID를 돌려준다 <https://www.postgresql.org/docs/17/functions-info.html>
  - NOTIFY — 커밋 시에만 전달 <https://www.postgresql.org/docs/17/sql-notify.html> · LISTEN
  - 9.17 Sequence Manipulation Functions — 중단·크래시로 인한 빈틈 <https://www.postgresql.org/docs/17/functions-sequence.html>
  - 19.6 Replication — `max_slot_wal_keep_size`
- MySQL 8.4 Reference Manual — `SHOW BINLOG EVENTS`, `binlog_format`(ROW)
- Kleppmann 『Designing Data-Intensive Applications』 1판 11장 "Stream Processing" — Keeping Systems in Sync(이중 쓰기 경쟁), Change Data Capture (원문 미열람, 장 제목 기준)
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): NOTIFY 롤백/커밋 전달 차이와 시퀀스 빈틈, 두 세션 seq 순서 ≠ 커밋 순서 폴링 누락, `wal_level = replica`에서 논리 슬롯 생성 에러, MySQL ROW binlog의 Write/Update/Delete_rows 이벤트
