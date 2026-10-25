# issue/cross-cutting/database/add-column-default-shared-value — 정답

태그: `resource-bounding`

## 정답
<!-- 질문 1:1 대응 -->

1. **기존 행은 모두 같은 값 m을 갖고, 그 값은 카탈로그에 하나만 있다.**\
   비휘발 기본값(`now()`도 문장 시각에 한 번 계산되므로 해당)으로 열을 더하면, PostgreSQL은 테이블을 다시 쓰지 않고 그 값을 `pg_attribute.attmissingval`에 두고 `atthasmissing = true`로 표시한다.\
   기존 행을 읽으면 물리적으로 없는 그 열 자리에 카탈로그의 값이 채워진다 — 그래서 기존 행 전부가 같은 `updated_at = m`(열을 더한 트랜잭션의 `now()`)이다.\
   이 덕분에 큰 테이블의 열 추가가 순간에 끝나지만, "행마다 언제 바뀌었나"라는 열의 뜻은 기존 행에서 성립하지 않는다.
   > **빠른 기본값(fast default)** — 비휘발 DEFAULT로 열을 더할 때 행을 다시 쓰지 않고 카탈로그의 값 하나로 기존 행의 값을 대신하는 PostgreSQL 11+의 동작. `atthasmissing`·`attmissingval`에 기록된다.

2. **첫 틱이 기존 행 전부를 후보로 읽는다.**\
   첫 하한 L = 기동 − 60초인데, 열 추가 직후 60초 안에 기동하면 L ≤ m이다 — `updated_at >= L`은 기존 행 전부(이 사례 약 615만 행)를 고른다.\
   후보 조회에 상한이 없고 받은 후보를 한 틱 안에서 정렬·탐지했으므로, 틱 하나의 시간·힙·DB 부하가 기존 데이터 크기에 비례했다.\
   쿼리는 정상이고 결과도 "틀리지" 않다(기존 행을 다 대조할 뿐) — 그래서 오류가 아니라 비용으로만 드러난다.\
   기존 행은 "열 추가 뒤에 바뀐 행"이 아니므로 증분이 읽을 몫도 아니다(그 몫은 전체를 도는 안전망 대조가 맡는다).\
   이 결함은 새 기능을 **기존 데이터가 있는 DB에 처음 배포할 때**만 나타난다 — 빈 테이블에 열을 더하고 행을 넣는 테스트에서는 값이 m인 행이 없어 보이지 않았다(설계 검토에서 발견).\
   고친 뒤 같은 경로의 첫 틱 후보는 2만여 행 · 0.21~0.26초였다(기동 − 60초 뒤 바뀐 행만).

3. **엄격한 하한은 열 추가 락을 기다린 트랜잭션의 변경을 잃는다.**\
   열 추가 트랜잭션보다 **먼저 시작해** 그 `ACCESS EXCLUSIVE` 락을 기다린 뒤 행을 고친 트랜잭션 X를 생각한다.\
   트리거가 쓰는 값은 X의 `now()` = X의 **시작 시각**이므로 X의 표시는 m보다 앞이다.\
   X의 시작이 기동 − 60초 뒤라면 X는 원래 보장 범위 안의 변경인데, 하한을 m으로 올리면 창 밖으로 밀린다.\
   "값이 정확히 m인 행"만 빼면 기존 행만 빠진다 — m을 쓰는 것은 열 추가 트랜잭션 자신뿐이고 그 트랜잭션은 행을 쓰지 않는다(다른 트랜잭션의 시작 시각이 마이크로초까지 m과 같으면 그 행은 안전망 몫).
   > **`now()`** — PostgreSQL에서 현재 **트랜잭션의 시작 시각**. 같은 트랜잭션 안에서는 몇 번 불러도 같다(벽시계는 `clock_timestamp()`).

4. **`<> m`은 인덱스 범위가 아니라 걸러내기라 m 묶음을 다 훑는다.**\
   `updated_at >= L`만 인덱스 범위로 쓰이고, `<> m`은 찾은 항목마다 버리는 조건이 된다 — 버릴 m 묶음(기존 행 전부)을 인덱스와 힙에서 다 읽은 뒤 버린다.\
   `[L, m)`와 `(m, ∞)` 두 범위로 나누면 둘 다 인덱스 범위 탐색이라 m 묶음을 건너뛴다.\
   한 틱이 두 범위를 읽을 때는 A를 먼저 읽고, 상한이 남으면 같은 틱에서 B를 잇는다(행 수 합이 상한).

5. **테이블을 다시 쓰면 사라진다 — 기동 때 읽어 기억하고, 없으면 WARN으로 남긴다.**\
   `VACUUM FULL`·`CLUSTER`·재작성을 일으키는 `ALTER`는 빠진 열 값을 행에 물리로 써 넣고 카탈로그 값을 지운다 — PostgreSQL 16에서 `VACUUM FULL` 뒤 `atthasmissing = false`를 실측했다.\
   반대로 **빈 테이블**에 같은 문장으로 열을 더해도 `atthasmissing = true`였다(설계 때는 "없을 수도 있다"로 두었던 것을 실측으로 확인).\
   행에는 m이 물리로 남으므로, 기동 때 한 번 읽어 메모리에 둔 m으로 계속 빼면 기동 뒤 재작성이 일어나도 규칙이 유지된다.\
   기동 때 이미 값이 없으면 제외 없이 원래 문장으로 돌고, 기동 WARN과 재시작 기록에 "m 없음"을 남긴다 — 그때 기존 행이 첫 창에 드는 경우(재작성이 기동 60초 안 — 드묾)의 비용은 페이지 상한이 맡는다(6번의 예외 있음).

6. **단일 열 인덱스는 같은 값 묶음 안의 키셋 위치를 찾지 못한다.**\
   키셋 조건 `(updated_at, k1, k2) > ($t, $a, $b) ORDER BY updated_at, k1, k2 LIMIT N`은 인덱스가 `(updated_at, k1, k2)` 순서를 가질 때 마지막 위치에서 바로 이어 읽는다.\
   인덱스가 `(updated_at)`뿐이면 `updated_at = $t`인 묶음 안에서 `(k1, k2)` 위치를 인덱스로 찾을 수 없어 묶음 전체를 읽고 정렬한 뒤 N개를 고른다.\
   "m 없음" 경로(재작성 뒤 기존 행이 한 값으로 물질화)에서 그 묶음은 기존 행 전부라, 상한 N이 틱 비용을 묶지 못한다.\
   이 사례는 인덱스를 정의한 기존 마이그레이션 파일을 바꾸지 않는다는 제약이 있어 동작을 바꾸지 않고, 기동 WARN 문구와 문서에 한계로 적었다(리뷰에서 발견 — 받아들인 한계).
   > **키셋 페이지(keyset pagination)** — 오프셋 대신 "마지막으로 읽은 키보다 큰 것"으로 다음 페이지를 읽는 방식. 정렬 키 전체가 인덱스 순서와 같을 때만 페이지 비용이 크기 N으로 묶인다.

## 문제 구조 (추상화 코드)

### 변형 A — 첫 창이 열 추가 시각을 덮어 기존 행 전부를 읽음
① 문제 코드
```sql
-- 마이그레이션
ALTER TABLE items ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();   -- 기존 행 전부 = m
CREATE INDEX idx_items_updated_at ON items (updated_at);
```
```kotlin
// 증분 대조 — 기동 시 첫 하한
var lower = dbNow() - startLookback                       // 열 추가 직후면 lower ≤ m

fun tick() {
    val rows = jdbc.query("SELECT k1, k2 FROM items WHERE updated_at >= ?", lower)   // 상한 없음
    rows.sortedWith(keyOrder).chunked(chunk).forEach(::detectAndRepair)              // 한 틱에 N행
    lower = nextLower()
}
```
② 고친 코드
```kotlin
// 기동 때 1회 — 카탈로그의 빠른 기본값
val m: Instant? = jdbc.queryForObject("""
    SELECT (a.attmissingval::text::timestamptz[])[1]
      FROM pg_attribute a
     WHERE a.attrelid = 'items'::regclass AND a.attname = 'updated_at' AND a.atthasmissing""") // 없으면 null
if (m == null) log.warn("updated_at 빠른 기본값 없음(m 없음) — 첫 창 제외 없이 진행")

fun candidates(lower: Instant, after: Key?, limit: Int): List<Key> {
    if (m == null || lower > m) return rangeQuery("updated_at >= ?", listOf(lower), after, limit)
    val a = rangeQuery("updated_at >= ? AND updated_at < ?", listOf(lower, m), after, limit)   // 범위 A
    if (a.size == limit) return a                                                             // 찬 페이지
    return a + rangeQuery("updated_at > ?", listOf(m), after, limit - a.size)                 // 범위 B — 남은 몫
}

// rangeQuery: … AND (updated_at, k1, k2) > (?, ?, ?) ORDER BY updated_at, k1, k2 LIMIT ?
// 페이지가 차면 lower를 고정하고 마지막 키를 기억해 다음 틱이 이어 읽는다
```
무엇이 깨졌나: "그 열 값 ≥ 하한 = 하한 뒤에 바뀐 행"이라는 등식이, 빠른 기본값으로 같은 값을 받은 기존 행에서 성립하지 않았다.

### 변형 B — 카탈로그 값이 테이블 재작성으로 사라짐
① 문제 코드
```kotlin
fun tick() {
    val m = readMissingValue()          // 매 틱 읽기 — VACUUM FULL 뒤에는 null
    val q = if (m != null) twoRanges(m) else oneRange()   // 재작성 직후부터 기존 행 묶음을 다시 읽기 시작
}
```
② 고친 코드
```kotlin
private val m = readMissingValue()     // 기동 때 1회 — 행에는 m이 물리로 남으므로 기억한 값이 계속 맞다
init { if (m == null) { log.warn("m 없음"); recordRestart(detail = "m 없음") } }   // 조용히 넘어가지 않는다
```
무엇이 깨졌나: 행의 값은 물리로 남는데 그 값의 출처(카탈로그)는 재작성으로 사라진다 — 출처를 매번 다시 읽으면 규칙이 재작성 시점에 조용히 꺼진다.

### 변형 C — 단일 열 인덱스와 같은 값 묶음 (받아들인 한계)
```sql
CREATE INDEX idx_items_updated_at ON items (updated_at);     -- 키셋 열 (updated_at, k1, k2) 중 첫 열만

SELECT k1, k2 FROM items
 WHERE updated_at >= $1 AND (updated_at, k1, k2) > ($2, $3, $4)
 ORDER BY updated_at, k1, k2 LIMIT $5;
-- updated_at = $2 묶음이 크면: 묶음 전체 읽기 + 정렬 → LIMIT이 비용을 못 묶는다
-- 정석: CREATE INDEX … ON items (updated_at, k1, k2)   (이 사례는 기존 마이그레이션 무변경 제약으로 적용하지 않음)
```
무엇이 깨졌나: 페이지 상한은 "인덱스가 정렬 키 전체를 덮는다"는 전제 위에서만 비용 상한이다.

## 검증 기록
- 2026-10-26: 사건 기록 대조·추상화(Claude 초안) — 변형 A·C는 설계·코드 리뷰에서 발견, 변형 B의 `VACUUM FULL` 뒤 소실·빈 테이블의 `atthasmissing = true`는 PostgreSQL 16 실측. 약 615만 행·고친 뒤 첫 틱 수치는 측정 기록에서 옮김.

## 관련 카드
- [hot-update-and-indexed-columns](../hot-update-and-indexed-columns/) — 같은 변경 추적 열(`updated_at` + 트리거 + 인덱스)이 쓰기 쪽에 매기는 비용 — 이 카드는 열을 처음 더할 때 읽기 쪽에 생기는 비용.
- [pagination-cursor-integrity](../../data/pagination-cursor-integrity/) — 커서가 이어받는 집합의 무결성 — 이 카드의 키셋은 같은 값 묶음에서 비용이 깨진다.
- [periodic-full-scan-cost-growth](../periodic-full-scan-cost-growth/) — 전체 훑기 비용은 행 수에 비례한다 — 이 결함은 증분이 첫 틱에 우연한 전체 훑기가 되는 경우.
