# data-engineering/11-data-lineage — 데이터 계보: 데이터셋·잡·실행의 그래프와 영향 분석 — 정리 (힌트)

## 해결하는 문제

세 가지 질문이 매주 들어온다.

```text
  ① "raw.orders.region 컬럼을 지워도 되나요?"          → 누가 이 컬럼을 쓰나? (하류, 영향 범위)
  ② "대시보드 매출이 왜 어제랑 다르죠?"                → 이 숫자는 어디서 왔나? (상류, 원인)
  ③ "user_007의 이메일을 전부 지워 주세요"              → 이 값이 어디까지 복제됐나? (하류, 전파 대상)
```

- 답하려면 "어떤 데이터가 어떤 잡을 거쳐 어떤 데이터가 되었나"를 그래프로 갖고 있어야 한다.
  - *데이터 계보(data lineage)*: 데이터셋과 그것을 만든 잡·실행 사이의 연결을 기록한 그래프. 위 세 질문은 모두 이 그래프의 순회다.
- 계보가 없으면 사람이 SQL 파일을 grep하고, 팀마다 물어보며 며칠을 쓴다. 그 사이 컬럼을 지운 영향은 대시보드가 깨진 뒤에야 알게 된다.

쉬운 예: 수돗물 배관도다.
- 어느 동네 물이 탁하면(②) 배관도를 거슬러 정수장·밸브를 찾는다.
- 밸브 하나를 잠그기 전에(①) 그 밸브 뒤에 어느 동네가 있는지 배관도로 본다.
- 배관도가 "건물 단위"로만 그려져 있으면, 실제로는 상관없는 건물까지 단수 공지를 돌리게 된다.

똑같은 구조다.\
"배관" = 잡, "물탱크" = 데이터셋, "건물 단위 vs 수도꼭지 단위" = 테이블 수준 vs 컬럼 수준 계보다.

## 동작·원리

### 1. 그래프의 세 가지 노드 — 데이터셋, 잡, 실행

```text
        ┌─────────── Job: stg_orders (정의, 코드 위치, SQL) ───────────┐
        │                                                              │
  raw.orders ──input──▶ Run 2026-10-06 (runId, 시작·끝, 상태) ──output──▶ stg.orders
                        Run 2026-10-07 (runId, ...)
        Dataset                    Run = Job의 한 번 실행                 Dataset
```

- OpenLineage 명세(Object Model, 1.53.0 문서) 기준
  - *Job*: 데이터셋을 읽고 쓰는 과정. 네임스페이스 안의 고유한 이름으로 식별한다. 예: 매일 `CREATE TABLE x AS SELECT * FROM y`를 돌리는 cron의 파이썬 스크립트.
  - *Run*: 잡의 한 번 실행. 클라이언트가 UUID `runId`를 만든다(UUIDv7 권장). 매일 도는 잡이면 날마다 Run이 따로 생긴다.
  - *Dataset*: 데이터 한 묶음. DB면 테이블, 객체 저장소면 버킷의 객체·디렉터리. 물리 위치에서 만든 네임스페이스 + 이름으로 식별한다.
  - *facet*: 노드에 붙이는 추가 메타데이터. 예: Dataset의 `schema`·`columnLineage`, Run의 `nominalTime`·`parent`·`errorMessage`, Job의 `sql`(Object Model 페이지는 `sql`을 Run facet 목록에 적지만, facet 정의 문서 "SQL Job Facet"은 `job.facets.sql`에 둔다), 출력의 `outputStatistics`(행 수·바이트).
- Run 상태: `START`·`RUNNING`·`COMPLETE`·`ABORT`·`FAIL`·`OTHER`. `COMPLETE`·`ABORT`·`FAIL`이 끝 상태다(Run Cycle 문서).
- Run을 따로 두는 이유: "어제 실행이 무엇을 읽었나"를 답하기 위해서다. 잡 정의는 같아도 실행마다 읽은 파티션·스키마·행 수가 다르다.

```json
{
  "eventType": "COMPLETE",
  "eventTime": "2026-10-07T00:12:00Z",
  "run": { "runId": "0199b1c2-...-uuidv7" },
  "job": { "namespace": "batch", "name": "stg_orders" },
  "inputs":  [ { "namespace": "postgres://pg:5432", "name": "app.raw.orders" } ],
  "outputs": [ { "namespace": "postgres://pg:5432", "name": "app.stg.orders",
                 "outputFacets": { "outputStatistics": { "rowCount": 400 } } } ]
}
```

- 위는 예시다(최상위 `producer`·`schemaURL`과 facet마다 붙는 `_producer`·`_schemaURL`은 줄였다). 확인한 것: 출력 데이터셋의 facet 묶음 이름 `outputFacets`(OpenLineage 2-0-2 JSON 스키마), `outputStatistics.rowCount`(Output Statistics facet 문서), PostgreSQL 데이터셋의 네임스페이스 `postgres://{host}:{port}`와 이름 `{database}.{schema}.{table}`(Naming Conventions).

### 2. 테이블 수준 vs 컬럼 수준

```text
  테이블 수준                              컬럼 수준
  raw.orders ─▶ stg.orders ─▶ fct_sales     raw.orders.region ─▶ stg.orders.region ─▶ fct_sales.region
                    └─▶ user_ltv                                                         └▶ daily_revenue.region
  "raw.orders의 무엇을 바꿔도                 raw.orders.amount ─▶ stg.orders.amount ─▶ user_ltv.ltv (AGGREGATION)
   user_ltv가 영향받는다"고 답한다            "region을 지워도 user_ltv는 무관"까지 답한다
```

- 컬럼 수준 계보는 출력 컬럼마다 "어느 입력 컬럼에서 어떻게 왔나"를 적는다. OpenLineage `columnLineage` facet의 분류
  - DIRECT(값이 입력에서 나옴): `IDENTITY`(그대로), `TRANSFORMATION`(한 행의 값을 변환 — 예: 해시), `AGGREGATION`(여러 행을 모음 — 예: count).
  - INDIRECT(값을 만들지는 않지만 결과에 영향): `JOIN`(조인 조건), `FILTER`(WHERE), `GROUP_BY`, `SORT`, `WINDOW`, `CONDITIONAL`(CASE·COALESCE).
  - 각 변환에 `masking` 불리언이 있다 — 변환 중에 값이 가려졌는지(예: 해시).
- INDIRECT를 넣느냐가 답을 바꾼다. `WHERE status <> 'CANCELLED'`의 `status`는 매출 값을 만들지 않지만, 바뀌면 매출 합계가 바뀐다.

### 3. 정적 수집 vs 런타임 수집

```text
  정적(설계 시점)                                  런타임(실행 시점)
  SQL·코드를 파싱해 입력·출력을 추정               실행 중에 엔진·오케스트레이터가 실제 입력·출력을 보고
  + 실행 전에 안다(배포 전 영향 분석)               + 실제로 읽은 테이블·파티션·스키마·행 수
  − SELECT *·동적 SQL·UDF는 스키마 없이 못 푼다     − 한 번은 돌아야 안다, 연동 안 된 도구는 빈칸
  OpenLineage: JobEvent(정적 계보)                OpenLineage: RunEvent
```

- OpenLineage는 둘 다 받는다. RunEvent는 실행 중에, JobEvent·DatasetEvent는 설계 시점에 보낸다(Object Model 문서).
- 둘을 합쳐야 빈칸이 줄어든다. 아래 실험 3이 "SQL 텍스트만으로는 `SELECT *`를 못 푼다"를 보인다.

### 실험: 계보 그래프를 만들고 BFS로 영향 범위 구하기 (Java 모형)

(실험, `Lineage.java`, eclipse-temurin:21-jdk — OpenJDK 21.0.12, `--network none`. 실제 계보 도구가 아니라 제한된 SQL 형태만 정규식으로 읽는 **모형**이다.)

입력은 잡 8개다. 대시보드도 데이터셋 하나로 모형화했다.

```text
stg.orders        ← SELECT o.order_id, o.customer_id, o.region, o.amount FROM raw.orders o WHERE o.status <> 'CANCELLED'
stg.users         ← SELECT u.user_id, u.email, sha256(u.email) AS email_hash, u.region FROM raw.users u
mart.fct_sales    ← SELECT o.order_id, o.amount, o.region, u.region AS user_region FROM stg.orders o JOIN stg.users u ON o.customer_id = u.user_id
mart.daily_revenue← SELECT f.region, sum(f.amount) AS revenue FROM mart.fct_sales f GROUP BY f.region
mart.user_ltv     ← SELECT o.customer_id, sum(o.amount) AS ltv FROM stg.orders o GROUP BY o.customer_id
export.crm_contacts ← SELECT * FROM raw.users u
dash.revenue      ← SELECT d.region, d.revenue FROM mart.daily_revenue d
dash.marketing    ← SELECT c.* FROM export.crm_contacts c
```

```java
static Map<String, Integer> bfs(Map<String, List<String>> adj, String start) {
    var dist = new LinkedHashMap<String, Integer>();
    var q = new ArrayDeque<String>();
    dist.put(start, 0); q.add(start);
    while (!q.isEmpty()) {
        var u = q.poll();
        for (var v : adj.getOrDefault(u, List.of()))
            if (!dist.containsKey(v)) { dist.put(v, dist.get(u) + 1); q.add(v); }
    }
    dist.remove(start);
    return dist;            // 노드 → 홉 수(몇 단계 하류인가)
}
// 하류 = 간선 방향 그대로, 상류 = 간선을 뒤집은 그래프에서 같은 BFS
```

```text
간선 수: 테이블 9, 컬럼 40

== 1. raw.orders.region 컬럼을 지우면 — 테이블 수준 vs 컬럼 수준 영향
테이블 수준 BFS(raw.orders 하류) 5개: {stg.orders=1, mart.fct_sales=2, mart.user_ltv=2, mart.daily_revenue=3, dash.revenue=4}
컬럼 수준 BFS(직접 파생만) 4개: {stg.orders.region=1, mart.fct_sales.region=2, mart.daily_revenue.region=3, dash.revenue.region=4}
INDIRECT(필터·조인·GROUP BY)까지 넣으면 추가 2개: {mart.daily_revenue.revenue=3, dash.revenue.revenue=4}
```

- 테이블 수준은 `mart.user_ltv`까지 영향이라고 답한다. 컬럼 수준은 `region`을 쓰지 않는 `user_ltv`를 뺀다. 테이블 수준만 있으면 공지·검토 대상이 불필요하게 늘어난다.
- 직접 파생만 보면 `revenue`는 안전해 보인다. 그런데 `daily_revenue`는 `region`으로 GROUP BY 한다. 컬럼이 사라지면 매출 집계 자체가 깨진다. INDIRECT 간선이 이것을 잡았다.

```text
== 2. 'dash.revenue.revenue가 왜 틀렸나' — 상류로 거슬러 BFS
  원천 raw.orders.amount (거리 4)
  원천 raw.orders.status (거리 4)
  원천 raw.orders.customer_id (거리 4)
  원천 raw.users.user_id (거리 4)
  원천 raw.orders.region (거리 4)
  직접 파생만 따라가면 원천: [raw.orders.amount]
```

- 매출 값은 `amount`에서만 오지만, 매출 숫자를 바꿀 수 있는 원천 컬럼은 다섯 개다: 필터(`status`), 조인 키(`customer_id`·`user_id`), 그룹 키(`region`).
- "왜 틀렸나"를 추적할 때는 INDIRECT까지 포함한 상류 집합이 조사 범위다. 조인 키 형식이 바뀌어 행이 빠진 경우(03번 inner join 누락)는 `amount`만 봐서는 찾지 못한다.

```text
== 3. raw.users.email(PII)이 복제된 곳 — 삭제 요청 전파 대상
A(SQL 텍스트만) 경고: [export.crm_contacts: '*'를 펼칠 스키마가 없다 → 컬럼 계보 미상,
                      dash.marketing: 'c.*'를 펼칠 스키마가 없다 → 컬럼 계보 미상]
A 결과: [stg.users.email, stg.users.email_hash]
B(원천 스키마 앎) 경고: []
B 결과: [stg.users.email, stg.users.email_hash, export.crm_contacts.email, dash.marketing.email]
```

- A는 SQL 텍스트만 본다. `SELECT *`의 컬럼 목록을 모르니 CRM 내보내기와 마케팅 대시보드로 간 이메일을 **놓쳤다**. 경고를 무시하면 삭제 요청을 일부만 처리하게 된다(12번).
- B는 원천 스키마(런타임에 카탈로그나 OpenLineage `schema` facet으로 얻을 수 있는 정보)를 알아 `*`를 펼쳤다.
- `email_hash`도 결과에 들어 있다. 해시는 가명화일 뿐 여전히 개인정보일 수 있다(GDPR 전문 26 — 12번). 계보는 변환 종류(`TRANSFORMATION`)까지 기록해 이런 사본을 놓치지 않게 한다.

## 쓰이는 자료구조·알고리즘

- **방향 그래프(DAG)** — 노드 = 데이터셋(또는 컬럼)·잡, 간선 = 읽기·쓰기. 인접 리스트로 저장한다([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)). 순환이 생기면(잡이 자기 출력을 다시 읽음) DAG가 아니게 된다. OpenLineage에서 Dataset은 실행이 바뀌어도 같은 식별자(네임스페이스 + 이름)라, Run 노드만 끼워서는 `Dataset → Run → 같은 Dataset` 순환이 남는다. DAG로 펼치려면 입력·출력을 시점별 데이터셋 버전(예: Dataset `version` facet의 Iceberg 스냅숏 ID)으로 구분해야 한다(해석). 버전을 구분하지 않은 계보 그래프에는 위상 정렬을 그대로 쓸 수 없다.
- **BFS** — 하류(영향 범위)와 상류(원인 후보) 모두 너비 우선 순회. 홉 수가 "몇 단계 떨어졌나"를 준다([algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)). 간선을 뒤집은 그래프에서 같은 BFS가 상류 탐색이다.
- **위상 정렬** — 컬럼 변경 후 영향받은 데이터셋을 어떤 순서로 재계산할지(08번 백필 순서)는 DFS 기반 위상 정렬로 정한다([algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)).
- **간선 종류 필터** — 같은 그래프라도 "직접 파생만"(값 전파: PII·삭제)과 "INDIRECT 포함"(숫자 변화 원인)으로 질문마다 간선 집합을 고른다.
- **SQL 파싱** — 정적 계보는 SQL을 구문 트리로 읽어 SELECT 목록·FROM·JOIN·WHERE의 컬럼 참조를 뽑는다. 실험은 정규식 모형이라 중첩 쿼리·CTE·동적 SQL을 다루지 못한다.

## 적용 — 풀어나가는 법

### 1. 증상별 순회

| 질문 | 시작 노드 | 방향 | 간선 |
|---|---|---|---|
| 이 컬럼을 지워도 되나 | 그 컬럼 | 하류 | DIRECT + INDIRECT |
| 이 숫자가 왜 틀렸나 | 대시보드 지표 컬럼 | 상류 | DIRECT + INDIRECT |
| PII가 어디까지 복제됐나 | PII 컬럼 | 하류 | DIRECT(마스킹 여부 표시) |
| 이 잡이 실패하면 무엇이 늦나 | 잡의 출력 데이터셋 | 하류 | 테이블 수준이면 충분 |

### 2. 계보를 모으는 순서

1. 오케스트레이터·엔진의 런타임 연동을 먼저 켠다(실제로 읽고 쓴 것이 들어온다).
2. 연동이 없는 경로(손 스크립트, 외부 SaaS 내보내기)는 잡 정의에 입력·출력을 선언하게 한다(정적 계보).
3. `SELECT *`와 동적 SQL을 줄인다. 남는 것은 런타임 스키마로 펼친다.
4. 대시보드·리포트도 데이터셋 노드로 등록한다. 계보의 끝이 대시보드가 아니면 "누가 깨지나"에 답할 수 없다.

### 3. DB 안에서 1차 계보 얻기 (PostgreSQL 17)

```sql
-- 뷰가 어떤 테이블·뷰에 기대는지: 뷰 → 의존 대상 (시스템 뷰 제외, 뷰 정의 규칙 _RETURN만)
SELECT DISTINCT v.relname AS view, t.relname AS depends_on
FROM pg_depend d
JOIN pg_rewrite r ON r.oid = d.objid
JOIN pg_class v ON v.oid = r.ev_class
JOIN pg_class t ON t.oid = d.refobjid
WHERE d.classid = 'pg_rewrite'::regclass AND r.rulename = '_RETURN' AND v.relkind IN ('v','m')
  AND v.oid <> t.oid AND t.relkind IN ('r','v','m')
  AND v.relnamespace NOT IN ('pg_catalog'::regnamespace, 'information_schema'::regnamespace)
ORDER BY 1, 2;
```

(실험, PostgreSQL 17.11 — 10번 실험 DB에 뷰 두 개를 만든 뒤)

```text
     view      |  depends_on
 v_daily       | fct_orders
 v_daily_named | dim_customer
 v_daily_named | v_daily

 deps_fct_on_stg      ← fct_orders는 INSERT ... SELECT로 stg_orders에서 채웠지만
               0         pg_depend에는 아무 의존도 남지 않았다
```

- `pg_rewrite`에는 뷰 정의(`_RETURN` 규칙)뿐 아니라 일반 테이블에 건 `CREATE RULE ... ON INSERT` 같은 규칙도 들어간다. 그래서 `_RETURN`·`relkind`로 거른다. 판정 때 다시 돌린 확인(PostgreSQL 17.11): `fct_orders`에 INSERT 규칙을 하나 걸자, 거르지 않은 쿼리는 `fct_orders | audit_log`를 "뷰 의존"으로 더 보였고, 거른 쿼리는 위 세 행만 냈다. 위 출력은 규칙이 없는 DB에서 거르기 전 쿼리로 얻은 것이라 결과가 같다.
- 뷰는 정의가 카탈로그에 있으니 의존이 남는다. 뷰 위의 뷰(`v_daily_named → v_daily → fct_orders`)도 따라갈 수 있다.
- `INSERT ... SELECT`로 옮기는 배치 잡은 의존을 남기지 않는다(실험: 0). 그래서 배치 계보는 실행 쪽 — 오케스트레이터의 잡 정의, 쿼리 로그, OpenLineage 연동 — 에서 모은다.

### 4. 영향 분석을 배포 게이트로

```java
// 스키마 변경 PR에서: 지우거나 이름 바꾸는 컬럼마다 하류를 찾아, 소유자가 다른 노드가 있으면 승인 요구
record Impact(String node, int hops, String owner) {}
List<Impact> impacts = lineage.downstream("raw.orders.region", EdgeKinds.DIRECT_AND_INDIRECT);
var foreign = impacts.stream().filter(i -> !i.owner().equals(myTeam)).toList();
if (!foreign.isEmpty()) failCheck("다른 팀 소유 하류 " + foreign.size() + "개: 계약 변경 절차(09번) 필요");
```

- `lineage.downstream`은 위 BFS를 감싼 가상의 API다. 계보 저장소가 무엇이든 "PR에서 하류를 조회해 막는다"는 구조는 같다.

## 장애 시나리오와 대처

### 1. 컬럼을 지운 영향 범위를 모른다 → 며칠 뒤 대시보드 고장 발견 (⚠ 커리큘럼)

- 현상: 상류가 `region`을 지운 지 사흘 뒤, 지역별 매출 대시보드가 비어 있다는 문의가 온다.
- 보이는 형태: 하류 잡 일부는 컬럼 없음 오류로 실패, 일부는 JSON 경로라 NULL로 성공(09번).
- 원인: 변경 전에 하류 목록을 볼 수 없었다. 테이블 수준 계보만 있었다면 "raw.orders 하류 전부"가 대상이 되어 아무도 검토하지 않았을 수 있다(해석).
- 대처: 컬럼 수준 계보 + PR 게이트(적용 4). INDIRECT 간선까지 본다(실험 1: GROUP BY 키를 지우면 매출 컬럼도 깨진다).

### 2. "이 숫자 왜 틀렸나" 추적에 며칠 (⚠ 커리큘럼)

- 현상: 경영 대시보드의 매출이 재무 시스템보다 3% 낮다. 분석가가 SQL을 하나씩 열어 본다.
- 보이는 형태: 값 전파 경로(`amount`)만 따라가 이상을 못 찾는다.
- 원인 후보: 필터·조인 키·그룹 키 쪽 변화. 실험 2에서 매출 하나에 영향을 주는 원천 컬럼이 다섯 개였다.
- 대처: 상류 BFS를 INDIRECT 포함으로 돌리고, 각 원천 컬럼의 관측 지표(10번 — NULL 비율·고유값 수)를 거리 순으로 본다. Run 단위 계보가 있으면 "숫자가 바뀐 날 처음 바뀐 입력"까지 좁힌다.

### 3. PII가 어디까지 복제됐는지 모른다 → 삭제 요청을 일부만 처리 (⚠ 커리큘럼)

- 현상: 삭제 요청을 처리했다고 답했는데, 마케팅 도구에서 그 사람의 이메일로 메일이 나간다.
- 보이는 형태: 계보 도구에는 `export.crm_contacts`의 컬럼 계보가 "미상"으로 남아 있었다(실험 3의 A).
- 원인: `SELECT *` 내보내기를 정적 파싱이 펼치지 못했다.
- 대처: PII 컬럼 하류를 DIRECT로 순회해 삭제 대상 목록을 만들고, "미상" 노드는 삭제 대상에 보수적으로 포함한다. `*` 사용을 금지하거나 런타임 스키마로 펼친다. 12번의 삭제 전파 절차로 이어진다.

### 4. 계보가 낡았다 — 그래프는 있는데 틀리다

- 현상: 계보 화면에 이미 없어진 잡이 보이고, 새 잡은 없다.
- 원인: 정적 선언만 쓰고 갱신하지 않았다. 또는 런타임 연동이 일부 도구에만 있다.
- 대처: Run 이벤트가 일정 기간 없는 잡·데이터셋을 "비활성"으로 표시한다. 계보 수집 여부 자체를 관측 지표로 둔다(연동된 잡 비율).

## 핵심 문장

- 계보는 데이터셋·잡·실행을 잇는 그래프다. 영향 범위는 하류 BFS, 원인 후보는 상류 BFS다.
- 테이블 수준 계보는 영향 범위를 부풀리고, 컬럼 수준 계보는 실제로 쓰는 하류만 남긴다.
- 값을 만들지 않는 필터·조인·그룹 키(INDIRECT)도 숫자를 바꾼다. "왜 틀렸나"를 추적할 때는 INDIRECT까지 순회한다.
- 정적 계보는 실행 전에 답하지만 `SELECT *`·동적 SQL을 못 푼다. 런타임 계보로 빈칸을 메운다.
- PII 삭제 범위는 계보의 하류 순회로 정한다. "미상" 노드를 빼면 삭제 요청을 일부만 처리하게 된다.

## 관련 주제·근거

- 선행
  - [08-idempotent-pipelines-and-backfill](../08-idempotent-pipelines-and-backfill/2-summary.md) — 잡과 파티션 DAG
  - [10-data-quality-and-data-observability](../10-data-quality-and-data-observability/2-summary.md) — 관측 5축의 하나로서의 계보
- 후속·연결
  - [12-data-retention-and-erasure](../12-data-retention-and-erasure/2-summary.md) — 계보로 찾은 사본에 삭제 전파
  - [09-data-contracts-and-schema-registry](../09-data-contracts-and-schema-registry/2-summary.md) — 스키마 변경 전 소비자 목록
  - [15-data-mesh-and-data-products](../15-data-mesh-and-data-products/2-summary.md) — 데이터 제품 간 의존
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md), [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)(위상 정렬)
  - [reliability/17-distributed-tracing](../../reliability/17-distributed-tracing/2-summary.md) — 요청 하나의 경로(트레이스)와 데이터 하나의 경로(계보)의 대응
  - [security/27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md) — PII 분류
- 근거
  - OpenLineage "Object Model"(문서 1.53.0) — Job·Run·Dataset, RunEvent·JobEvent·DatasetEvent, facet 목록 <https://openlineage.io/docs/spec/object-model>
  - OpenLineage "SQL Job Facet"(1.53.0) — `job.facets.sql` <https://openlineage.io/docs/spec/facets/job-facets/sql/>
  - PostgreSQL 17 `pg_rewrite`(테이블·뷰의 재작성 규칙 카탈로그) <https://www.postgresql.org/docs/17/catalog-pg-rewrite.html> · 39.2 Views and the Rule System(뷰 = `ON SELECT DO INSTEAD` 규칙, 관례상 이름 `_RETURN`) <https://www.postgresql.org/docs/17/rules-views.html>
  - OpenLineage "The Run Cycle" — 상태 6종, 끝 상태, BATCH·STREAMING·SERVICE <https://openlineage.io/docs/spec/run-cycle>
  - OpenLineage "Column Level Lineage Dataset Facet" — DIRECT(IDENTITY·TRANSFORMATION·AGGREGATION)·INDIRECT(JOIN·GROUP_BY·FILTER·SORT·WINDOW·CONDITIONAL), `masking` <https://openlineage.io/docs/spec/facets/dataset-facets/column_lineage_facet>
- 실험 목록
  - 제한된 SQL 8개 → 테이블·컬럼 계보 그래프, 하류·상류 BFS, `SELECT *` 미해결(SQL 텍스트만 vs 원천 스키마) — `Lineage.java`, eclipse-temurin:21-jdk(OpenJDK 21.0.12), `--network none`
  - `pg_depend`·`pg_rewrite`로 뷰 의존 조회, `INSERT ... SELECT`는 의존 0 — postgres:17(PostgreSQL 17.11) 일회용 컨테이너, `--network none`
  - (판정 때 추가) 일반 테이블 INSERT 규칙이 `pg_rewrite` 뷰 의존 쿼리에 섞이는지, `_RETURN`·`relkind` 거르기 전후 — postgres:17(PostgreSQL 17.11) 일회용 컨테이너, `--network none`
