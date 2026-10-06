# api-design/06-pagination — offset vs 커서(keyset), 페이지 토큰 계약 — 정리 (힌트)

## 해결하는 문제

목록 API는 결과를 한 번에 다 줄 수 없다. 100만 건을 한 응답에 담으면 서버 메모리·응답 시간·클라이언트 화면이 다 버티지 못한다.\
그래서 잘라서 준다. 문제는 **"다음 쪽"을 어떻게 가리키느냐**다.

```text
 방법 1 "몇 개 건너뛰어"   GET /items?offset=100000&limit=20
 방법 2 "여기 다음부터"    GET /items?page_token=<마지막으로 본 항목의 위치>
```

쉬운 예: 두꺼운 책을 나눠 읽는다.
- 방법 1은 "앞에서 300쪽 넘겨라"다. 누가 앞쪽에 쪽을 끼워 넣으면 어제 읽은 쪽을 또 읽는다. 쪽을 빼면 못 읽은 쪽이 생긴다. 300쪽을 매번 손으로 넘기는 것도 느리다.
- 방법 2는 책갈피다. 앞에 쪽이 끼든 빠지든 책갈피 다음부터 읽는다.

똑같은 구조다.
- 쪽 번호 = `OFFSET`. 책갈피 = 커서(마지막으로 본 행의 정렬 키).

실무 예
- 게시판·주문 목록·알림 목록에서 "더 보기"를 누르면 방금 본 글이 또 나온다. 또는 글 하나가 끝까지 안 보인다.
- 크롤러나 데이터 동기화 배치가 `page=50000`을 요청하면 DB CPU가 튄다.
- 이 노트는 **API 계약**(파라미터·토큰·상한·일관성 약속)을 다룬다. SQL 문법·방언·실행 계획 세부는 [languages/sql/syntax/09](../../../languages/sql/syntax/09-limit-offset-keyset-pagination/2-summary.md), B+Tree 구조는 [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md)에 있다.

## 동작·원리

### 1. 두 방식 — "만들고 버리기" vs "경계부터 읽기"

```text
 인덱스 (created_at DESC, id DESC) 의 잎 노드를 왼쪽부터 읽는다

 offset=100000, limit=20
   [■■■■■■■■■■■■■■■■■■■■ ... 100,000개 읽고 버림 ...■■■■][□□□□ 20개 반환]
    └──────────────── 깊을수록 읽는 양이 늘어난다 ─────────┘

 keyset: WHERE (created_at, id) < (마지막 값)
                                    ▼ B+Tree로 바로 내려감
   [ ............................... ][□□□□ 20개 반환]
```

- *offset 페이지네이션*: "정렬한 결과에서 앞의 N개를 건너뛰고 M개". 페이지 번호로 바로 점프할 수 있다.
  - DB는 건너뛸 N개를 **실제로 만든 뒤 버린다**. 그래서 깊을수록 느리다.
- *keyset(seek) 페이지네이션*: "마지막으로 본 행의 정렬 키보다 뒤에 있는 M개". Winand는 이를 seek method라 부르고, 앞 페이지의 **값**을 경계로 쓴다고 설명한다.
  - 정렬 키에 맞는 인덱스가 있으면 B+Tree로 경계까지 바로 내려가 M개만 읽는다. 깊이와 상관없이 비슷한 비용이다.
  - 대가: 임의 페이지(37쪽)로 점프할 수 없다. 방향을 바꾸려면(이전 페이지) 비교와 정렬을 뒤집어야 한다(Winand).
- *정렬의 결정성*: 같은 정렬 값(동률)을 가진 행들의 순서가 실행마다 바뀌면 페이지 경계에서 중복·누락이 난다. 그래서 유일한 열(보통 `id`)을 마지막 정렬 키로 붙인다(Winand: "Paging requires a deterministic sort order"). 커서에도 그 열이 들어가야 한다.

### 실험 A: offset 깊이에 따른 비용 (PostgreSQL 17)

- 환경: PostgreSQL 17.11 전용 컨테이너(`--cpus=2`, 메모리 1GB), 테이블 `item` 100만 행(57MB), 인덱스 `(created_at DESC, id DESC)`, `VACUUM ANALYZE` 후.
- 같은 20행을 offset과 keyset으로 깊이별 3회씩 `EXPLAIN (ANALYZE, BUFFERS)`. 두 쿼리가 돌려준 `id` 목록이 깊이마다 같은지도 대조했다(5개 깊이 모두 같음).

```sql
-- offset
SELECT id, created_at, title FROM item ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET $N;
-- keyset (앞 페이지의 마지막 행 = N번째 행의 값을 경계로. N=0이면 WHERE 없음)
SELECT id, created_at, title FROM item
 WHERE (created_at, id) < ($ts, $id) ORDER BY created_at DESC, id DESC LIMIT 20;
```

(실험, PostgreSQL 17.11, 2026-10-04 — 경계를 바로잡아 다시 잰 값. 각 3회 중 1회차 출력. `Limit`·자식 노드·실행 시간 줄만 `awk`로 한 줄에 모았다)

```text
offset=0 run1 | Limit (actual time=0.080..0.091 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.078..0.084 rows=20 loops=1) | Execution Time: 0.130 ms
offset=10000 run1 | Limit (actual time=5.925..5.937 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.064..4.780 rows=10020 loops=1) | Execution Time: 5.994 ms
offset=100000 run1 | Limit (actual time=42.779..42.789 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.044..34.556 rows=100020 loops=1) | Execution Time: 42.831 ms
offset=500000 run1 | Limit (actual time=233.045..233.056 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.061..191.293 rows=500020 loops=1) | Execution Time: 233.113 ms
offset=999980 run1 | Limit (actual time=454.310..454.320 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.064..366.179 rows=1000000 loops=1) | Execution Time: 454.388 ms
keyset@0 run1 | Limit (actual time=0.044..0.055 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.042..0.048 rows=20 loops=1) | Execution Time: 0.092 ms
keyset@10000 run1 | Limit (actual time=0.132..0.146 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.128..0.137 rows=20 loops=1) | Execution Time: 0.323 ms
keyset@100000 run1 | Limit (actual time=0.094..0.109 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.091..0.101 rows=20 loops=1) | Execution Time: 0.209 ms
keyset@500000 run1 | Limit (actual time=0.045..0.054 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.044..0.049 rows=20 loops=1) | Execution Time: 0.120 ms
keyset@999980 run1 | Limit (actual time=0.030..0.041 rows=20 loops=1) |   ->  Index Scan using item_created_id on item (actual time=0.028..0.035 rows=20 loops=1) | Execution Time: 0.111 ms
```

3회의 `Execution Time` 범위(위 출력과 같은 실행에서 모은 값):

| 깊이 | offset | keyset |
|---|---|---|
| 0 | 0.092 ~ 0.130 ms | 0.092 ~ 0.102 ms |
| 10,000 | 3.956 ~ 5.994 ms | 0.128 ~ 0.323 ms |
| 100,000 | 39.313 ~ 42.831 ms | 0.145 ~ 0.209 ms |
| 500,000 | 206.104 ~ 233.113 ms | 0.120 ~ 0.201 ms |
| 999,980 | 379.114 ~ 454.388 ms | 0.111 ~ 0.123 ms |

- 관찰 1 — offset은 자식 노드(Index Scan)의 `actual rows`가 `offset + 20`이다. 100만 번째 근처를 보려고 100만 행을 읽었다.
- 관찰 2 — 시간이 깊이에 거의 비례해 늘었다(0.1ms → 약 380~450ms). keyset은 깊이와 무관하게 0.09~0.33ms였다. 앞선 측정 두 번(경계가 한 행 어긋난 판)에서도 offset 999,980은 394.901~515.670ms, keyset은 0.113~0.351ms였다 — 시간은 실행마다 다르고, offset의 `actual rows`는 같다.
- 관찰 3 — 같은 테이블의 `SELECT count(*)`(계획: Parallel Seq Scan, 작업자 2)는 104~139ms(3회)였다. 사실 점검 재실행에서는 62~96ms였다 — 실행마다 다르다. "전체 건수"를 응답마다 주면 첫 페이지도 이만큼 비싸진다(아래 §3의 `total_size`).
- 경계는 앞 페이지의 **마지막 행**(N번째)이어야 한다. offset 페이지의 첫 행(N+1번째)을 경계로 잡으면 `<`가 그 행을 빼서 결과가 한 행 밀린다(맨 끝에서는 19행만 나온다 — 앞선 측정에서 실제로 그랬다).
- 수치는 이 제한 환경(2 CPU, 데이터가 캐시에 있음)의 값이다. 읽을 것은 `actual rows`와 자릿수 차이다.

### 2. 페이지 사이의 쓰기 — 중복과 누락

```text
 정렬: 최신 글이 맨 앞.  1쪽(offset 0, 3개)을 본 뒤 새 글 X가 들어왔다

 1쪽 읽을 때   [A B C] D E F G
 2쪽 읽을 때   X [A B C] D E F    offset 3 → C D E   ← C가 또 나온다 (중복)

 1쪽을 본 뒤 B가 삭제됐다
 2쪽 읽을 때   A C D [E F G]       offset 3 → E F G   ← D를 못 본다 (누락)

 keyset: "C 다음부터" → D E F      삽입·삭제와 무관하게 이어진다
```

- offset은 "앞에서 몇 번째"라 앞쪽이 늘면 밀리고(중복), 줄면 당겨진다(누락). Winand는 이를 "pages drift"라고 쓴다.
- keyset은 "이 값 다음"이라 앞쪽 변화에 흔들리지 않는다.
- keyset이 못 막는 것
  - 커서보다 **앞쪽**에 새로 들어온 행은 이번 순회에서 안 보인다. 다음 순회(새로 고침)에서 보인다.
  - 정렬 키 자체가 바뀌는 행(예: `updated_at` 정렬에서 순회 중 수정된 글)은 커서 앞뒤로 이동해 중복·누락될 수 있다(해석 — 정렬 키 값 이동에서 나오는 결과다).
  - 시점 고정이 필요하면 스냅샷 방식을 쓴다. Kubernetes 목록 API는 `continue` 토큰에 resourceVersion과 위치를 넣어 한 시점의 일관된 스냅샷을 보여 주고, 토큰은 기본 5분 뒤 만료돼 `410 Gone`을 준다(Kubernetes "API Concepts").

### 3. 페이지 토큰 계약 — 서버가 약속하는 것

```text
 요청  GET /items?page_size=50&filter=status%3Dopen&page_token=<불투명 문자열>
 응답  { "items": [...50개], "next_page_token": "MjAy…open.CPmD…" }
                                         └ 비어 있으면 끝
```

Google AIP-158(목록 페이지네이션 지침)의 규칙:

| 항목 | AIP-158 |
|---|---|
| `page_size` | 필수 아님. 0 또는 생략 → API가 기본값. 상한보다 크면 상한으로 **깎는다**(should). 음수 → `INVALID_ARGUMENT`(must) |
| `page_token` | 필수 아님. 다음 요청에서 `page_size`는 바꿔도 되지만(존중해야 함), 다른 인자가 바뀌면 `INVALID_ARGUMENT`(should) |
| `next_page_token` | 끝이면 비어 있어야(must). 끝이 아니면 있어야(must) |
| 토큰 성질 | **불투명**하고 URL 안전한 문자열, 사용자가 해석할 수 없어야(must not be user-parseable). 위치 표시 외 용도 금지, 권한 부여 수단이 되면 안 된다(must not) |
| 만료 | 보낸 뒤 합리적 시간이 지나면 만료시킬 수 있다(may) |
| `total_size` | 줄 수 있다(may) |

- *불투명 토큰(opaque token)*: 클라이언트가 내용을 해석하거나 만들어 내지 못하게 한 문자열. 서버는 안에 무엇을 넣든(정렬 키·필터·스냅샷 버전) 나중에 바꿀 수 있다.
  - 내용을 그대로 노출하면(`?after_created=2026-01-01T00:39&after_id=998`) 클라이언트가 그 형식에 의존한다. 이후 정렬 키를 바꾸면 그 클라이언트가 깨진다([01-api-as-contract](../01-api-as-contract/2-summary.md)의 Hyrum의 법칙).
  - base64는 인코딩일 뿐 숨기지 않는다(AIP-158 경고: "Base-64 encoding an otherwise-transparent page token is not a sufficient obfuscation mechanism"). 내용을 숨기려면 암호화하고, 조작을 막으려면 서명(HMAC)한다.
- 다른 회사의 관례
  - Stripe: `limit`(1~100, 기본 10), `starting_after`·`ending_before`에 **객체 ID**를 넣는다. 응답의 `has_more`가 false면 끝. 역시간순(Stripe API "Pagination").
  - GitHub REST: 응답 `link` 헤더의 `rel="next"`·`"prev"`·`"first"`·`"last"` URL을 그대로 따라가라고 권한다. `per_page` 상한(대부분 100)을 넘기면 에러 없이 줄인다. 엔드포인트마다 `page`·`before`/`after`·`since`가 다르다(GitHub Docs).

### 실험 B: 목록 API를 순회하는 동안 남이 쓴다

- 환경: JDK 21.0.12 `com.sun.net.httpserver` + PostgreSQL 17.11. 테이블 1000행, `created_at`은 10행씩 같은 값(동률), 정렬 `created_at DESC, id DESC`.
- 클라이언트가 50개씩 끝까지 넘긴다. **페이지를 하나 받을 때마다** 다른 사용자가 (a) 새 글 3개 삽입 + 방금 본 글 1개 삭제, 또는 (b) 새 글 1개 삽입 + 본 글 3개 삭제(같은 행을 고르면 0행).
- 셈: 중복 = 같은 ID를 두 번 받은 수. 누락 = 순회 시작부터 끝까지 계속 있었는데 한 번도 못 받은 행 수.

```java
// Page06.java 핵심 — 커서 쪽 SQL과 토큰
"SELECT id, created_at FROM item_api WHERE " + where +
" AND (created_at, id) < (?::timestamptz, ?) ORDER BY created_at DESC, id DESC LIMIT ?"   // size+1개 읽어 "더 있나"를 안다
String payload = base64url(ts + "|" + id + "|" + filter);       // 위치 + 필터
String token = payload + "." + base64url(hmacSha256(payload)[0..12]);
if (!t.filter.equals(filter)) → 400 "page_token does not match request parameters"
```

(실험, JDK 21.0.12 + PostgreSQL 17.11, 2026-10-04 — 같은 결과로 2회 실행. 삭제할 행은 고정 시드 난수로 고른다)

```text
쓰기(페이지마다 삽입 3·삭제 1) offset 페이지  21개, 받은 항목 1040, 중복  40, 누락(처음~끝 내내 있던 행)   0
쓰기(페이지마다 삽입 3·삭제 1) cursor 페이지  20개, 받은 항목 1000, 중복   0, 누락(처음~끝 내내 있던 행)   0
쓰기(페이지마다 삽입 1·삭제 3) offset 페이지  20개, 받은 항목  967, 중복   0, 누락(처음~끝 내내 있던 행)  33
쓰기(페이지마다 삽입 1·삭제 3) cursor 페이지  20개, 받은 항목 1000, 중복   0, 누락(처음~끝 내내 있던 행)   0
```

- 관찰 1 — 앞쪽에 쌓이는 쓰기(a)에서 offset은 페이지마다 2칸씩 밀려 **중복 40개**를 받았다(20쪽 × 순증 2).
- 관찰 2 — 앞쪽이 줄어드는 쓰기(b)에서 offset은 **누락 33개**. 그 33개는 순회 내내 DB에 있었다.
- 관찰 3 — 커서는 두 경우 모두 중복 0·누락 0. 원래 1000행을 정확히 한 번씩 받았다. 순회 중 새로 들어온 글은 커서보다 앞이라 받지 않았다(§2).
- 관찰 4 — (집필 중 관찰, 그 출력은 보존하지 않았다) 처음 작성 때 offset 클라이언트의 종료 조건을 "빈 페이지"로 두자 순회가 끝나지 않았다. 페이지마다 2행이 늘고 끝 페이지가 2행이라, 쫓아가도 끝이 계속 밀렸다. "더 있음"은 서버가 `size + 1`행을 읽어 판단해 알려 주는 것이 안전하다.

토큰 계약 출력(같은 실행):

```text
[토큰 계약]
1쪽(status=open): {"items":[1000,998],"next_page_token":"MjAyNi0wMS0wMSAwMTozOTowMCswMHw5OTh8c3RhdHVzPW9wZW4._UGEeqf2kagfqXSY"}
같은 필터 + 토큰:   {"items":[996,994],"next_page_token":"MjAyNi0wMS0wMSAwMTozOTowMCswMHw5OTR8c3RhdHVzPW9wZW4.CPmDU3a6AD-oMbSz"}
필터를 바꾼 토큰:   400 {"error":"page_token does not match request parameters"}
조작한 토큰:        400 {"error":"invalid page_token"}
page_size=1000:     200 받은 항목 100
page_size=-1:       400 {"error":"page_size must be >= 0"}
```

- 토큰 앞부분 `MjAy…`는 base64url이라 디코드하면 `2026-01-01 01:39:00+00|998|status=open`이 보인다. 서명이 조작은 막지만 **내용을 숨기지는 않는다**. 숨겨야 하면 암호화한다.
- 필터를 바꾼 채 옛 토큰을 쓰면 400(AIP-158 "다른 인자가 바뀌면 `INVALID_ARGUMENT`"). 토큰 안의 필터와 요청 필터를 비교했다.
- `page_size=1000` → 상한 100으로 깎아 200, 음수 → 400(AIP-158).

## 쓰이는 자료구조·알고리즘

- **B+Tree 범위 스캔** — keyset = "경계 키까지 루트에서 잎으로 내려가 잎을 따라 M개". 비용이 O(log N + M)이다. offset은 O(N_offset + M)이다. [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md), [data-structure/15-b-tree](../../data-structure/15-b-tree/2-summary.md).
- **행 값 비교(row value comparison)** — `(created_at, id) < (?, ?)`는 사전식 비교다. 복합 인덱스 순서와 정렬 방향이 맞아야 인덱스 경계로 쓰인다. 방향이 섞이면(`a DESC, b ASC`) 행 값 하나로 못 쓰고 `a < ? OR (a = ? AND b > ?)`로 풀어야 한다.
- **커서 인코딩** — 위치(정렬 키 + 동률 깨기 키) + 요청 지문(필터·정렬) → base64url → HMAC 서명. 만료가 필요하면 발급 시각도 넣는다.
- **한 개 더 읽기(lookahead)** — `LIMIT size + 1`로 다음 페이지 존재를 안다. 별도 `count(*)` 없이 `next_page_token` 유무를 정한다.

## 적용 — 풀어나가는 법

### 1. 설계 순서

1. **정렬을 먼저 정한다** — 목록의 기본 정렬과 허용 정렬([12-filtering-sorting-search](../12-filtering-sorting-search/2-summary.md)). 마지막에 유일 키를 붙인다.
2. **인덱스를 정렬에 맞춘다** — `(필터 등호 열, 정렬 열..., id)`. `EXPLAIN`으로 Sort 노드가 없는지 본다.
3. **토큰을 불투명하게** — 응답에 `next_page_token`(또는 `link` 헤더). 내용은 서명, 필요하면 암호화.
4. **토큰에 요청 조건을 묶는다** — 필터·정렬이 다르면 400.
5. **page_size 기본·상한을 문서화** — 상한 초과는 깎고, 음수는 400.
6. **임의 쪽 점프가 꼭 필요하면** offset을 허용하되 최대 깊이를 제한한다(예: 1만 건까지, 예시). 그 너머는 검색·필터로 좁히게 한다.
7. **전체 건수는 선택 기능으로** — 매 요청 `count(*)`를 하지 않는다. 필요하면 근사치나 별도 요청.
8. **일관성 약속을 문서에 쓴다** — "순회 중 추가된 항목은 안 보일 수 있다", 토큰 만료 시간, 만료 시 응답(예: 400 또는 410).

### 2. 서버 코드 모양 (JDBC)

```java
record Cursor(OffsetDateTime createdAt, long id, String filterHash) {}

Page list(String filter, int pageSize, String pageToken) {
    if (pageSize < 0) throw badRequest("page_size must be >= 0");
    int size = pageSize == 0 ? 20 : Math.min(pageSize, 100);     // 기본·상한 (예시 값)
    Cursor c = pageToken == null ? null : tokens.verify(pageToken);   // 서명 불일치 → 400
    if (c != null && !c.filterHash().equals(hash(filter))) throw badRequest("page_token does not match request");
    String sql = """
        SELECT id, created_at, title FROM item
         WHERE status = ?
           AND (?::timestamptz IS NULL OR (created_at, id) < (?, ?))
         ORDER BY created_at DESC, id DESC
         LIMIT ?""";
    List<Item> rows = query(sql, ..., size + 1);
    boolean more = rows.size() > size;
    List<Item> page = more ? rows.subList(0, size) : rows;
    String next = more ? tokens.sign(new Cursor(last(page).createdAt(), last(page).id(), hash(filter))) : "";
    return new Page(page, next);
}
```

- `(? IS NULL OR …)` 한 문장으로 첫 쪽과 다음 쪽을 합치면 PostgreSQL이 일반 계획(generic plan)에서 인덱스 경계를 못 쓸 수 있다. 첫 쪽과 다음 쪽 SQL을 나누는 편이 계획이 단순하다(설계 판단, 실측하지 않음).

### 3. 진단

```sql
-- 느린 목록 요청의 깊이를 본다: 계획의 자식 노드 actual rows가 offset+limit이면 깊은 offset
EXPLAIN (ANALYZE, BUFFERS) SELECT ... ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 500000;
```

- 접근 로그에서 `offset`·`page` 값 분포를 본다. 상위 0.1%가 수십만이면 크롤러·동기화 배치다.
- 클라이언트 쪽 증상 탐지: 순회 결과의 ID 중복 수를 센다(실험 B 방식).

## 장애 시나리오와 대처

### 1. 깊은 offset → DB가 사실상 풀스캔 (⚠)

- **현상**: 평소 빠른 목록 API가 특정 시간대에 수백 ms~초 단위로 느려지고 DB CPU가 오른다.
- **보이는 형태**: 느린 쿼리 로그에 `OFFSET 500000` 같은 큰 값. `EXPLAIN ANALYZE`에서 자식 노드 `actual rows=500020`(실험 A: 0.1ms → 약 200ms).
- **원인**: offset은 건너뛸 행을 만들고 버린다. 깊은 페이지를 순회하는 크롤러·배치가 있다.
- **대처**: 커서 페이지네이션으로 바꾸고, offset은 최대 깊이를 둔다. 전체 내보내기는 별도 배치 API로.

### 2. 페이지 사이 삽입·삭제 → 중복·누락 (⚠)

- **현상**: 무한 스크롤에서 같은 글이 두 번 나온다. 동기화 배치가 일부 행을 빠뜨린다.
- **보이는 형태**: 클라이언트가 받은 ID 목록에 중복. 원천과 사본의 건수 차이.
- **원인**: offset 기준이라 앞쪽 변화에 밀린다(실험 B: 중복 40·누락 33).
- **대처**: 커서로 바꾼다. 동기화라면 "변경 시각 + id" 커서나 변경 로그(CDC)를 쓴다. 정렬 키가 바뀌는 행이 있으면 그 사실을 문서화하거나 스냅샷 방식으로.

### 3. 동률 정렬 → 페이지 경계에서 흔들림

- **현상**: 같은 시각에 만든 항목들이 페이지를 넘길 때 섞여서 하나가 두 번, 하나는 안 나온다. 데이터가 바뀌지 않았는데도 그렇다.
- **보이는 형태**: 같은 `created_at` 값을 가진 행들 근처에서만 중복·누락.
- **원인**: `ORDER BY created_at`만으로는 동률 행 순서가 정해지지 않는다. 커서에도 `created_at`만 넣었다.
- **대처**: 정렬과 커서에 유일 키(`id`)를 붙인다.

### 4. 클라이언트가 토큰 내용에 의존

- **현상**: 서버가 커서 형식을 바꾼(정렬 키 추가) 배포 뒤 일부 파트너 연동이 400을 받는다.
- **보이는 형태**: 파트너가 토큰을 직접 만들어 보낸 흔적(형식은 맞지만 서명이 없거나 옛 형식).
- **원인**: 토큰이 읽을 수 있는 형식(쿼리 파라미터 값이나 서명 없는 base64)이라 클라이언트가 해석·생성했다.
- **대처**: 서명·암호화로 불투명하게 만들고, 문서에 "토큰을 해석하지 말라"를 쓴다(AIP-158). 바꾸기 전 옛 형식 토큰을 일정 기간 받아 준다.

### 5. 상한 없는 page_size·매번 전체 건수

- **현상**: 한 클라이언트가 `page_size=100000`을 보내 서버 메모리가 튄다. 또는 목록 응답이 전반적으로 느리다.
- **보이는 형태**: 큰 응답 크기, GC 증가. 목록 쿼리마다 `count(*)`가 같이 돈다(실험 A의 count 62~139ms, 실행마다 다르다).
- **원인**: 상한 검사 없음. UI 요구로 매 요청 전체 건수를 계산.
- **대처**: 상한으로 깎는다(AIP-158, GitHub). 전체 건수는 선택 기능·근사치·캐시로.

## 핵심 문장

- offset은 건너뛸 행을 만들고 버린다. 실험에서 100만 행 끝 근처 페이지는 100만 행을 읽었고 keyset은 깊이와 무관하게 20행만 읽었다.
- offset은 앞쪽이 늘면 중복, 줄면 누락이 난다. 커서(keyset)는 "이 값 다음"이라 앞쪽 변화에 흔들리지 않는다.
- 정렬과 커서에는 유일 키를 붙인다. 동률이 있으면 페이지 경계가 흔들린다.
- 페이지 토큰은 불투명해야 한다. 서명은 조작을, 암호화는 해석을 막는다. 토큰에 필터를 묶어 조건이 바뀌면 400을 준다.
- page_size는 기본·상한을 두고, 전체 건수는 선택 기능으로 둔다.

## 관련 주제·근거

- 선행
  - [02-rest-and-resource-modeling](../02-rest-and-resource-modeling/2-summary.md) — 컬렉션 자원
  - [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md) · [database/09-index-design](../../database/09-index-design/2-summary.md) — 복합 인덱스와 정렬
  - [languages/sql/syntax/09-limit-offset-keyset-pagination](../../../languages/sql/syntax/09-limit-offset-keyset-pagination/2-summary.md) — SQL 문법·방언, PG·MySQL 계획 비교
- 후속·연결
  - [12-filtering-sorting-search](../12-filtering-sorting-search/2-summary.md) — 정렬·필터 파라미터와 인덱스
  - [01-api-as-contract](../01-api-as-contract/2-summary.md) — 토큰 형식에 대한 의존(Hyrum)
  - 사례 [25-case-settlement-report](../25-case-settlement-report/2-summary.md) — 대용량 조회
  - [database/12-query-optimizer-and-explain](../../database/12-query-optimizer-and-explain/2-summary.md) — EXPLAIN 읽기
  - [security/16-identifiers-and-enumeration](../../security/16-identifiers-and-enumeration/2-summary.md) — 토큰·ID 열거
- 근거
  - Google AIP-158 Pagination(`page_size`·`page_token`·`next_page_token`, 상한으로 깎기, 음수 `INVALID_ARGUMENT`, 다른 인자 변경 시 `INVALID_ARGUMENT`, 불투명·URL 안전·해석 불가, 권한 부여 금지, 만료 가능, `total_size`, `skip`) <https://google.aip.dev/158>
  - Markus Winand, "Paging Through Results", Use The Index, Luke!(offset의 두 단점: 페이지 drift·깊을수록 느림, seek method, 결정적 정렬, 행 값, 임의 페이지 불가) <https://use-the-index-luke.com/sql/partial-results/fetch-next-page>
  - Stripe API "Pagination"(`limit` 1~100 기본 10, `starting_after`·`ending_before`, `has_more`, 역시간순) <https://docs.stripe.com/api/pagination>
  - GitHub Docs "Using pagination in the REST API"(`link` 헤더 rel, `per_page` 최대 대부분 100·초과 시 조용히 줄임, `page`·`before`/`after`·`since`) <https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api>
  - Kubernetes "API Concepts"(`limit`·`continue`, 일관된 스냅샷, 토큰 기본 5분 뒤 만료 → `410 Gone`) <https://kubernetes.io/docs/reference/using-api/api-concepts/>
  - RFC 8288 Web Linking(`Link` 헤더) <https://www.rfc-editor.org/rfc/rfc8288>
- 실험 목록
  - 실험 A: offset 깊이(0·1만·10만·50만·999,980) vs keyset `EXPLAIN (ANALYZE, BUFFERS)` 각 3회 + `count(*)` 3회 — `page06.sql`·`page06-explain.sh`, PostgreSQL 17.11 전용 컨테이너, 100만 행. 판정자 재측정(2026-10-04): keyset 경계를 `OFFSET N-1 LIMIT 1`(앞 페이지의 마지막 행)로 바로잡고 두 쿼리의 `id` 목록이 같은지 대조 — 본문 출력·표는 이 재측정 값
  - 실험 B: 순회 중 쓰기(삽입3·삭제1 / 삽입1·삭제3)에서 offset vs 커서의 중복·누락, 토큰 계약(필터 변경·조작·상한·음수) — `Page06.java`, JDK 21.0.12 + PostgreSQL 17.11, 2회
