# database/36-data-models-document-graph — 관계·문서·그래프 모델과 스키마 온 리드 — 정리 (힌트)

## 해결하는 문제

관계 모델(01번)은 모든 것을 평평한 표와 조인으로 표현한다. 데이터 모양에 따라 이것이 불편할 때가 있다.

```text
  이력서 한 장                         관계 모델로 쪼개면
  이름: 김철수                         users(user_id, name)
  경력: [A사 2019~, B사 2016~2019]     positions(user_id, company, start, end)
  학력: [C대 2012~2016]                education(user_id, school, start, end)
  연락처: {블로그, 트위터}              contact_info(user_id, type, url)
  → 화면은 한 덩어리로 읽는다           → 한 화면에 여러 번 조회하거나 여러 테이블을 조인
```

- 앱 객체(트리 모양)와 표(평평한 모양) 사이의 변환 부담을 **임피던스 불일치**라 부른다(DDIA 2장).
- 한편 데이터끼리 **얽힌 관계**(누가 누구를 알고, 어디서 태어나 어디에 살고, 그 도시는 어느 주·어느 나라 안에 있는지)는 표와 조인으로 쓰면 쿼리가 길고 깊이를 미리 모른다.

쉬운 예: 편지 한 통은 봉투에 통째로 넣어 두는 게 편하다(문서). 그러나 "이 편지에 나온 사람의 친구의 친구가 사는 동네"를 찾으려면 사람들 사이의 연결 지도(그래프)가 필요하다.

똑같은 구조다.\
데이터가 **한 덩어리로 읽히는 트리(일 대 다)**면 문서 모델이, **많은 것이 서로 이어진 그물(다대다)**이면 관계 또는 그래프 모델이 자연스럽다. 어느 모델을 고르냐가 곧 어떤 쿼리가 쉽고 어떤 쿼리가 어려운지를 정한다.

실무 예:
- 상품 옵션처럼 종류마다 속성이 다른 데이터를 `jsonb` 열에 넣었다. 몇 달 뒤 `age`에 `"unknown"` 문자열이 섞여 평균 계산이 터진다.
- 문서 DB에 회사 이름을 사용자 문서마다 복사해 두었다. 회사가 이름을 바꾸자 일부 문서만 바뀐다.

## 동작·원리

### 1. 같은 데이터, 세 가지 모델

```text
  관계                          문서 (JSON 트리)                     그래프 (정점 + 간선)
  users                         {                                    (Lucy) ─BORN_IN─> (Boise)
  id name                         "name": "Lucy",                    (Boise) ─WITHIN─> (Idaho)
  6  Lucy                         "born_in": "Boise",                (Idaho) ─WITHIN─> (USA)
  places                          "lives_in": "France"               (Lucy) ─LIVES_IN─> (France)
  id name   parent                }                                  (France) ─WITHIN─> (Europe)
  3  Boise  2
  2  Idaho  1                    한 사람 = 한 문서                     관계 자체가 1급 데이터
  1  USA    NULL                 포함 관계 = 중첩                       깊이 제한 없는 탐색
```

- *문서 모델(document model)*: 이름 붙은 필드와 값(스칼라·배열·중첩 문서)의 계층으로 레코드를 저장한다. 요즘 구현은 JSON을 쓴다(CMU L1 §7).
- *그래프 모델(graph model)*: 정점(vertex)과 간선(edge)으로 저장한다. 간선에 종류(label)와 속성을 붙인다(DDIA 2장 속성 그래프).

### 2. 문서 모델 — 트리와 지역성, 그리고 참조의 한계

```text
  일 대 다 = 트리 → 문서 하나로 표현                   다대일·다대다 = 공유되는 것 → 참조가 필요
  user                                              user A ──┐
   ├─ positions[ ]                                            ├──> company "Acme" (id 10)
   ├─ education[ ]                                  user B ──┘
   └─ contact_info{ }                               → 문서에는 id만 두고 읽을 때 해석(조인)해야 한다
```

- **지역성(locality)**: 문서 DB에서 한 문서는 보통 하나의 연속된 문자열(JSON·이진 형식)로 저장되므로, 문서 전체를 자주 읽으면 조회 한 번으로 끝난다(DDIA 2장). 이득은 문서 대부분을 같이 쓸 때만이다. 일부만 읽어도 보통 전체를 읽고, 갱신 시 크기가 바뀌면 전체를 다시 쓴다. 그래서 문서를 작게 유지하라고 권한다.
  - 물리 배치는 제품마다 다르다. PostgreSQL의 큰 `jsonb` 값은 TOAST로 별도 테이블에 청크로 나뉘어 저장될 수 있다(PostgreSQL 17 65.2). 논리적으로 한 값이라 한 번에 읽힌다는 뜻이다.
- **다대다가 오면**: DDIA는 문서 DB의 조인 지원이 약하면 앱이 여러 번 조회해 조인을 흉내 내야 하고, 이것이 복잡성을 앱으로 옮기며 보통 DB 안 조인보다 느리다고 적는다. 복제(비정규화)로 피하면 앱이 일관성을 맞춰야 한다.
- 역사는 반복된다: 1960~70년대 계층형 DB(IBM IMS)도 일 대 다에 강하고 다대다에 약했다. 관계 모델은 외래 키, 문서 모델은 **문서 참조**로 같은 문제를 푼다. 둘 다 읽을 때 조인·후속 조회로 해석한다(DDIA 2장).

### 3. 스키마 온 리드 vs 스키마 온 라이트

```text
  스키마 온 라이트 (관계 DB 기본)              스키마 온 리드 ("스키마리스" 문서)
  쓰기 ─► [ 스키마 검사 ] ─► 저장              쓰기 ─► 저장 (아무 모양이나)
            위반이면 거부                     읽기 ─► [ 코드가 모양을 가정하고 해석 ] ─► 실패하거나 조용히 틀림
  ≈ 정적 타입 검사                            ≈ 동적 타입 검사
```

- DDIA: "스키마리스"는 오해를 부르는 말이다. 읽는 코드가 구조를 가정하므로 **암묵적 스키마**가 있고, DB가 강제하지 않을 뿐이다.
- 스키마 온 리드가 나은 경우(DDIA): 객체 종류가 많아 종류마다 테이블을 두기 어려울 때, 구조를 외부 시스템이 정해 언제든 바뀔 수 있을 때. 모든 레코드 구조가 같다면 스키마가 그 구조를 문서화하고 강제하는 좋은 수단이다.
- 스키마 변경: 문서 쪽은 새 모양으로 쓰고 읽는 코드가 옛 모양도 처리한다. 관계 쪽은 `ALTER TABLE` + 백필이다. DDIA 1판은 MySQL `ALTER TABLE`이 테이블 전체를 복사한다고 적었지만, 로컬 재현(MySQL 8.4.10)에서 `ADD COLUMN … ALGORITHM=INSTANT`는 즉시 끝났다. 판에 따른 차이다.

### 4. 관계 DB 안의 문서 — `jsonb`와 MySQL `JSON`

| | PostgreSQL 17 `json` | PostgreSQL 17 `jsonb` | MySQL 8.4 `JSON` |
|---|---|---|---|
| 저장 | 입력 텍스트 그대로 | 분해한 이진 형식 | 최적화된 이진 형식 |
| 쓰기 시 검사 | JSON 문법 | JSON 문법 + 값 제약(`\u0000`·`numeric` 범위 밖 숫자 거부) | JSON 문법(틀리면 오류) |
| 중복 키 | 모두 보존(처리 시 마지막 값) | 마지막 값만 | 마지막 값만 |
| 인덱스 | — | GIN(`@>`, `?` 등) | 생성 열 인덱스, 다중 값 인덱스(15.1.15) |

- PostgreSQL 17 8.14: `json`은 입력을 그대로 저장해 처리할 때마다 다시 파싱한다. `jsonb`는 입력이 조금 느리고 처리가 훨씬 빠르며 인덱스를 지원한다.
- **어느 쪽도 문서의 모양(필드 존재·타입)은 검사하지 않는다.** 문법(과 `jsonb`의 값 제약)만 본다. 로컬 재현(예시)
  - PostgreSQL 17.11: `'{"name":"lee","age":"unknown"}'`이 들어갔다.
  - MySQL 8.4.10: `'{bad json'`은 `ERROR 3140 (22032): Invalid JSON text`로 거부됐지만, `"age":"unknown"`은 들어갔다.
- PostgreSQL 문서의 권고(8.14.2): 유연성이 필요해도 문서에 **어느 정도 고정된 구조**를 두라. 또 갱신은 행 전체에 행 락을 걸므로, 동시 갱신 경합을 줄이려면 문서를 다룰 만한 크기로 제한하라.

### 5. 그래프 모델 — 정점·간선, 그리고 가변 길이 탐색

```text
  속성 그래프 (DDIA 2장)
  정점: id, 나가는 간선들, 들어오는 간선들, 속성(키-값)
  간선: id, 꼬리 정점, 머리 정점, 라벨, 속성(키-값)

  관계 DB에 담으면 테이블 두 개 (DDIA 예 2-2)
  vertices(vertex_id PK, properties)
  edges(edge_id PK, tail_vertex FK, head_vertex FK, label, properties)
  + INDEX(tail_vertex), INDEX(head_vertex)   <- 정점의 나가는/들어오는 간선을 빨리 찾기 위해
```

- 어떤 정점도 어떤 정점과 이어질 수 있다. 스키마가 "무엇과 무엇이 관계 맺을 수 있나"를 제한하지 않는다.
- 핵심 쿼리: "미국에서 태어나 유럽에 사는 사람". 출생지가 도시일 수도, 주일 수도 있어 `WITHIN`을 **몇 번** 따라가야 할지 모른다.

```text
  Cypher (Neo4j) — DDIA 예 2-4
  MATCH
    (person) -[:BORN_IN]->  () -[:WITHIN*0..]-> (us:Location {name:'United States'}),
    (person) -[:LIVES_IN]-> () -[:WITHIN*0..]-> (eu:Location {name:'Europe'})
  RETURN person.name
      WITHIN*0.. = "WITHIN 간선을 0번 이상" (정규식의 * 와 같다)
```

- SQL로는 재귀 CTE(05번)로 쓴다. DDIA는 같은 질의가 Cypher 4줄, SQL 29줄이라고 비교한다. 데이터 모델마다 쉬운 질의가 다르다는 예다.
- 로컬 재현(예시, PostgreSQL 17.11): `vertices`·`edges` 두 테이블과 `WITH RECURSIVE in_usa … in_eu …` 두 개로 같은 질의를 돌려 `Lucy`를 얻었다(Boise → Idaho → USA, France → Europe).
- *트리플 저장소(triple store)*: 모든 사실을 (주어, 서술어, 목적어) 세 쌍으로 저장한다. 속성 그래프와 본질은 같고 말만 다르다. SPARQL로 질의한다(DDIA 2장).
- SQL 표준에도 속성 그래프 질의가 들어갔다(SQL:2023 Property Graph Queries, CMU L2 §1). PostgreSQL 17과 MySQL 8.4는 이를 지원하지 않는다. 로컬 재현(PostgreSQL 17.11·MySQL 8.4.10)에서 `CREATE PROPERTY GRAPH`가 두 제품 모두 문법 오류(`syntax error at or near "PROPERTY"`, `ERROR 1064`)였다.

## 쓰이는 자료구조·알고리즘

- **트리(문서)**: 문서는 루트가 하나인 트리다. 일 대 다 관계가 중첩으로 드러난다. 경로(`doc->'company'->>'name'`, `$.company.name`)가 트리의 루트-노드 경로다.
- **그래프와 인접 리스트**: `edges(tail_vertex, head_vertex)` + 두 방향 인덱스는 정점마다 나가는·들어오는 간선 목록, 즉 인접 리스트다. [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- **가변 길이 탐색 ≈ BFS**: `UNION`을 쓴 재귀 CTE는 층별 BFS처럼 "도달 가능한 정점 집합"을 구한다. 방문한 정점을 다시 넣지 않아야 끝난다(`UNION`).
  - Cypher `WITHIN*0..`는 반복 횟수만 적는 **패턴**이다. 경로마다 매치하고(기본: 한 경로 안에서 같은 간선은 다시 안 지나지만 정점은 다시 올 수 있다), 어떤 탐색으로 찾을지는 엔진이 정한다(Neo4j Cypher Manual "Paths with unique relationships"). [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)
- **역색인(GIN)**: PostgreSQL `jsonb`의 GIN 인덱스는 문서 안의 키·값 → 그 값을 가진 행 목록을 저장한다. `@>`(포함), `?`(키 존재) 질의를 이 인덱스로 푼다(PostgreSQL 17 8.14.4). [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 모델 고르기 — 관계의 모양을 먼저 본다

```text
  데이터가 주로…                               고를 모델
  한 덩어리로 읽는 트리, 공유되는 것이 적다     → 문서 (또는 관계 DB의 jsonb 열)
  다대일·다대다가 많고 조인이 잦다              → 관계
  연결이 복잡하고 깊이를 모르는 탐색이 핵심      → 그래프 (또는 관계 DB + 재귀 CTE, 규모를 보고)
  종류마다 속성이 제각각인 일부 필드            → 관계 테이블 + jsonb 열 (혼합)
```

- DDIA: 관계 모델과 문서 모델의 혼합이 좋은 방향이다. 관계 DB는 JSON을 지원하고, 문서 DB는 조인을 지원해 가고 있다.

### 2. 혼합 설계 — 핵심 필드는 열, 가변 필드는 jsonb + 제약

```sql
CREATE TABLE product (
  id       bigint PRIMARY KEY,
  name     text   NOT NULL,                      -- 모든 상품 공통 → 열
  price    numeric NOT NULL CHECK (price >= 0),
  company_id bigint NOT NULL REFERENCES company, -- 공유되는 것 → 참조(FK), 복사하지 않는다
  attrs    jsonb  NOT NULL DEFAULT '{}'
           CHECK (jsonb_typeof(attrs) = 'object') -- 최소한의 모양은 쓰기 때 검사
);
CREATE INDEX ON product USING gin (attrs);        -- attrs @> '{"color":"red"}' 검색
```

- 로컬 재현(예시, PostgreSQL 17.11): `CHECK (jsonb_typeof(doc->'age') = 'number' AND doc ? 'name')`를 건 테이블은 `"age":"unknown"` 문서와 `name` 없는 문서를 둘 다 `23514`로 거부했다.
  - 단, `age` 키가 **없는** 문서는 통과했다. `jsonb_typeof(NULL)`이 NULL이고, CHECK는 NULL을 통과로 본다(PostgreSQL 17 5.5.1). 필수 필드면 `doc ? 'age' AND …`처럼 존재 검사도 넣는다. 스키마 온 리드 데이터에도 **꼭 필요한 부분만** 스키마 온 라이트를 걸 수 있다.
- 이미 쌓인 데이터에 같은 CHECK를 추가하면 기존 위반 행 때문에 실패한다(로컬 재현: `check constraint "age_is_number" … is violated by some row`). `NOT VALID`로 걸고 정리 후 검증한다(02번).

### 3. 읽는 쪽은 옛 모양도 처리한다

```ts
// TS: 스키마 온 리드 데이터를 읽는 쪽의 방어 — 모양을 확인하고, 모르는 모양은 드러낸다
type Profile = { name: string; age: number };
function parseProfile(doc: unknown): Profile {
  const d = doc as Record<string, unknown>;
  const name = typeof d.name === "string" ? d.name
             : typeof d.fullname === "string" ? d.fullname      // 옛 키 이름 호환
             : undefined;
  if (name === undefined || typeof d.age !== "number") {
    throw new Error(`profile shape invalid: ${JSON.stringify(doc)}`);   // 조용히 넘기지 않는다
  }
  return { name, age: d.age };
}
```

### 4. 관계 DB에서 그래프 질의

```sql
WITH RECURSIVE in_usa(id) AS (
    SELECT vertex_id FROM vertices WHERE properties->>'name' = 'USA'
  UNION                                          -- 방문한 정점은 다시 넣지 않는다 → 순환에도 끝남
    SELECT e.tail_vertex FROM edges e JOIN in_usa ON e.head_vertex = in_usa.id WHERE e.label = 'within'
)
SELECT * FROM in_usa;
```

- `edges(head_vertex, label)`·`edges(tail_vertex, label)` 인덱스가 있어야 한 단계마다 인덱스 조회로 끝난다.

### 5. 진단

```sql
-- PostgreSQL: 문서 모양 분포 점검
SELECT jsonb_typeof(doc->'age') AS t, count(*) FROM profile GROUP BY 1;
SELECT count(*) FROM profile WHERE NOT doc ? 'name';
-- MySQL
SELECT JSON_TYPE(doc->'$.age') AS t, count(*) FROM profile GROUP BY t;
SHOW WARNINGS;                                    -- 조용한 형 변환 경고 확인
```

- 문법 세부는 [sql/41 JSON 타입과 함수](../../../languages/sql/syntax/41-json-types-and-functions/2-summary.md), 재귀 CTE는 [05번](../05-window-functions-and-cte/2-summary.md).

## 장애 시나리오와 대처

### 1. 문서 모델에 다대다 → 앱에서 조인 → 불일치 (⚠ 커리큘럼)

- **현상**: 회사가 이름을 바꿨는데 일부 사용자 화면에는 옛 이름이 나온다.
- **보이는 형태**: 에러 없음. 로컬 재현(예시, PostgreSQL 17.11 `jsonb`): 회사 테이블 이름을 `Acme Corp`로 바꾸고 사용자 1의 내장 사본만 고치자, 조회 결과가 `1 | Acme Corp | Acme Corp`, `2 | Acme | Acme Corp`로 갈렸다.
- **원인**: 여러 사용자가 공유하는 회사(다대일)를 각 문서에 복사했다. 복사본 갱신은 앱 책임인데 한 경로가 일부만 고쳤다. 참조로 두면 앱이 여러 번 조회해 조인을 흉내 내야 한다(DDIA 2장).
- **대처**
  - 공유되는 것은 id로 참조하고 읽을 때 해석한다. 관계 DB라면 FK와 조인을 쓴다.
  - 복사가 필요하면(읽기 성능) 원본 변경 이벤트로 복사본을 갱신하는 경로를 하나로 모으고, 불일치 점검 쿼리를 둔다(03번 반정규화와 같은 원칙).

### 2. 스키마 없는 쓰기 → 읽기 시 파싱 실패 (⚠ 커리큘럼)

- **현상**: 통계 배치가 어느 날부터 실패한다.
- **보이는 형태**: PostgreSQL 17.11 로컬 재현 `SELECT avg((doc->>'age')::int) FROM profile` → `ERROR 22P02: invalid input syntax for type integer: "unknown"`. 배치 로그에 이 SQLSTATE가 찍힌다.
- **원인**: 쓰기 때 모양을 검사하지 않아 다른 타입 값이 섞였다. 스키마가 사라진 게 아니라, 검사가 쓰기 시점에서 읽기 시점(가장 늦은 곳)으로 옮겨 갔다.
- **대처**
  - 당장: 모양이 맞는 행만 읽고(`WHERE jsonb_typeof(doc->'age') = 'number'`, 로컬 재현 평균 35.5), 나머지는 격리 목록으로 뽑는다.
  - 근본: 꼭 필요한 필드에 CHECK를 건다(적용 2). 쓰는 앱에서 스키마 검증(JSON Schema 등)을 한다.

### 3. MySQL에서는 실패하지 않고 조용히 틀린다

- **현상**: 같은 데이터로 MySQL 대시보드의 평균 나이가 이상하게 낮다.
- **보이는 형태**: 로컬 재현(예시, MySQL 8.4.10): `SELECT avg(doc->'$.age') FROM profile` → `23.666666666666668`, `1 warning`. `SHOW WARNINGS`에 `3156 Invalid JSON value for CAST to DOUBLE from column json_extract at row 1`. 31, "unknown", 40에서 "unknown"이 0으로 계산됐다((31 + 0 + 40) / 3).
- **원인**: 형 변환 실패가 오류가 아니라 경고로 처리되고 값이 0이 되었다. 드라이버·앱이 경고를 보지 않으면 드러나지 않는다.
- **대처**: `JSON_TYPE(doc->'$.age') = 'INTEGER'`처럼 타입을 먼저 거른다. 집계 결과와 함께 건수·제외 건수를 같이 낸다. 쓰기 때 막으려면 CHECK를 건다. 로컬 재현(MySQL 8.4.10): `CHECK (JSON_TYPE(doc->'$.age') IN ('INTEGER','DOUBLE','DECIMAL'))`가 `"age":"unknown"`을 `ERROR 3819`로 거부했다.

### 4. 키 이름이 바뀐 옛 문서 → 조용히 NULL

- **현상**: 일부 사용자의 이름이 빈칸으로 보인다.
- **보이는 형태**: 에러 없음. 로컬 재현: `doc->>'name'`이 `{"fullname":"park"}` 문서에서 NULL(PostgreSQL), `doc->>'$.name'`도 NULL(MySQL).
- **원인**: 앱이 필드 이름을 `fullname`에서 `name`으로 바꿨지만 옛 문서는 그대로다. 없는 경로는 오류가 아니라 NULL이다.
- **대처**: 읽는 코드가 옛 모양을 명시적으로 처리하거나(적용 3), 백필로 옛 문서를 새 모양으로 옮긴다. 키 존재 비율을 점검 쿼리로 추적한다.

### 5. 큰 문서의 작은 갱신이 경합을 부른다

- **현상**: 사용자 설정 문서(수백 KB)의 필드 하나를 여러 요청이 동시에 바꾸면 대기가 늘고, 갱신마다 쓰기량이 크다.
- **보이는 형태**: PostgreSQL `pg_stat_activity`의 `wait_event_type = Lock`(행 락 대기). 갱신 건수에 비해 큰 WAL 생성량. 로컬 재현(예시, PostgreSQL 17.11): `pg_column_size` 약 384KB인 `jsonb` 문서에서 `jsonb_set`으로 필드 하나만 바꾸자 `pg_wal_lsn_diff` 기준 WAL이 약 422KB 생겼다(체크포인트 직후가 아닌 두 번째 갱신 기준).
- **원인**: PostgreSQL 문서(8.14.2)대로 갱신은 행 전체에 행 락을 건다. 문서의 작은 부분만 바꿔도 행 단위로 경합한다. DDIA도 문서 갱신은 보통 전체를 다시 쓴다고 적는다.
- **대처**: 독립적으로 갱신되는 부분은 별도 행·테이블로 뗀다. 문서를 다룰 만한 크기로 유지한다.

## 핵심 문장

- 문서 모델은 일 대 다 트리를 한 덩어리로 담아 지역성이 좋고, 다대일·다대다에서는 참조와 앱 쪽 조인 또는 복제가 필요해진다.
- 관계 모델은 조인과 외래 키로 다대다를 잘 다루고, 그래프 모델은 깊이를 모르는 연결 탐색을 짧게 쓴다. 모델 선택이 곧 어떤 질의가 쉬운지를 정한다.
- "스키마리스"는 스키마가 없다는 뜻이 아니라 스키마 검사가 쓰기 시점에서 읽기 시점으로 옮겨 간다는 뜻이다.
- JSON 타입은 문법(과 `jsonb`의 일부 값 제약)만 검사하고 필드 모양은 보지 않는다. 필드 존재·타입이 중요하면 CHECK 등으로 그 부분만 쓰기 때 강제한다.
- 같은 모양 오류도 PostgreSQL은 오류(22P02)로, MySQL은 경고와 0으로 드러날 수 있다. 경고를 보지 않으면 조용히 틀린다.

## 관련 주제·근거

- 선행: [01-relational-model-and-algebra](../01-relational-model-and-algebra/2-summary.md)
- 연결
  - [02-keys-and-constraints](../02-keys-and-constraints/2-summary.md) — CHECK·`NOT VALID`
  - [03-normalization](../03-normalization/2-summary.md) — 복제와 갱신 이상
  - [05-window-functions-and-cte](../05-window-functions-and-cte/2-summary.md) — 재귀 CTE로 그래프 탐색
  - [37-row-vs-column-storage](../37-row-vs-column-storage/2-summary.md) · [40-filters-and-specialized-indexes](../40-filters-and-specialized-indexes/2-summary.md)
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md) · [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- 교재
  - Kleppmann 『Designing Data-Intensive Applications』 1판 2장 "Data Models and Query Languages" — 임피던스 불일치, 이력서 예(그림 2-1·2-2), 지역성, 다대일·다대다, IMS·CODASYL, 문서 참조, 스키마 온 리드/라이트(동적/정적 타입 비유), 속성 그래프(예 2-2 테이블 두 개), Cypher `WITHIN*0..`(예 2-4), 4줄 vs 29줄, 트리플 저장소·SPARQL, 관계·문서 혼합 (중국어 번역본 Vonng/ddia `ch2`로 대조)
  - CMU 15-445 Fall 2024 Lecture #01 §7 Other Data Models(문서 모델) <https://15445.courses.cs.cmu.edu/fall2024/notes/01-relationalmodel.pdf> · Lecture #02 §1(SQL:2023 Property Graph Queries) <https://15445.courses.cs.cmu.edu/fall2024/notes/02-modernsql.pdf>
  - Silberschatz 7판 8장 슬라이드 "Semi-Structured Data"
- 공식 문서
  - PostgreSQL 17 8.14 JSON Types — json vs jsonb, 8.14.2 문서 설계(고정 구조 권장, 행 락), jsonb의 `\u0000`·numeric 범위 거부, 8.14.4 jsonb GIN 인덱스 <https://www.postgresql.org/docs/17/datatype-json.html>
  - PostgreSQL 17 5.5.1 Check Constraints(NULL이면 통과) <https://www.postgresql.org/docs/17/ddl-constraints.html> · 65.2 TOAST <https://www.postgresql.org/docs/17/storage-toast.html>
  - Neo4j Cypher Manual — Paths with unique relationships(기본: 한 경로에서 같은 관계 재사용 안 함) <https://neo4j.com/docs/cypher-manual/current/patterns/reference/>
  - MySQL 8.4 13.5 The JSON Data Type(자동 검증, 이진 저장, 마지막 중복 키 우선) <https://dev.mysql.com/doc/refman/8.4/en/json.html> · 15.1.15 CREATE INDEX(JSON 열 다중 값 인덱스)
- 로컬 재현(PostgreSQL 17.11, MySQL 8.4.10): `CREATE PROPERTY GRAPH` 미지원(두 제품), MySQL JSON 타입 CHECK 3819, 큰 `jsonb` 한 필드 갱신의 WAL 양, 문서 필드 누락 NULL(두 제품), PG 22P02 캐스트 실패와 타입 필터 후 평균 35.5, 기존 위반 행이 있는 CHECK 추가 실패, CHECK로 모양 강제(23514), MySQL 잘못된 JSON 3140 거부·타입 불일치는 경고 3156과 평균 23.67, MySQL `ALGORITHM=INSTANT` 열 추가, 내장 복사본 불일치(`Acme` vs `Acme Corp`), vertices/edges + 재귀 CTE 그래프 질의(`Lucy`)
