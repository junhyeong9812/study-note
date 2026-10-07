# data-engineering/11-data-lineage — 정답

## 정답

### 1. 세 질문과 순회 방향

| 질문 | 시작 | 방향 |
|---|---|---|
| 이 컬럼을 지워도 되나(영향 범위) | 그 컬럼 | 하류 |
| 이 숫자가 왜 틀렸나(원인 후보) | 대시보드 지표 | 상류(간선을 뒤집은 그래프) |
| PII가 어디까지 복제됐나(삭제 전파 대상) | PII 컬럼 | 하류 |

- 셋 다 같은 그래프의 BFS다. 질문마다 시작 노드·방향·포함할 간선 종류만 다르다.

### 2. Job·Run·Dataset

- Job: 데이터셋을 읽고 쓰는 과정의 정의. 네임스페이스 안의 고유 이름으로 식별.
- Run: 잡의 한 번 실행. 클라이언트가 만든 UUID `runId`(UUIDv7 권장).
- Dataset: 테이블·객체·디렉터리 같은 데이터 묶음. 물리 위치 기반 네임스페이스 + 이름.
- Run을 따로 두는 이유: 실행마다 읽은 파티션·스키마·행 수가 다르다. "어제 실행이 무엇을 읽어 무엇을 썼나"를 답하려면 실행 단위 기록이 필요하다.
- 끝 상태: `COMPLETE`, `ABORT`, `FAIL`(OpenLineage Run Cycle).

### 3. 테이블 수준 vs 컬럼 수준

```text
테이블 수준 BFS(raw.orders 하류) 5개: {stg.orders=1, mart.fct_sales=2, mart.user_ltv=2, mart.daily_revenue=3, dash.revenue=4}
컬럼 수준 BFS(직접 파생만) 4개: {stg.orders.region=1, mart.fct_sales.region=2, mart.daily_revenue.region=3, dash.revenue.region=4}
```

- 테이블 수준 5개, 컬럼 수준 4개(컬럼 노드).
- 차이: `mart.user_ltv`. 테이블 수준은 `raw.orders`를 읽는다는 이유로 넣지만, `user_ltv`는 `customer_id`·`amount`만 쓴다. 컬럼 수준은 이를 뺀다.

### 4. DIRECT vs INDIRECT

- DIRECT: 출력 값이 입력 값에서 나온다 — `IDENTITY`·`TRANSFORMATION`·`AGGREGATION`.
- INDIRECT: 출력 값을 만들지는 않지만 결과에 영향을 준다 — `JOIN`·`FILTER`·`GROUP_BY`·`SORT`·`WINDOW`·`CONDITIONAL`.
- 실험에서 INDIRECT를 넣자 `mart.daily_revenue.revenue`(거리 3)와 `dash.revenue.revenue`(거리 4)가 추가됐다.
- 이유: `daily_revenue`는 `GROUP BY f.region`으로 매출을 모은다. `region`이 사라지면 그룹 키가 없어져 쿼리가 실패하거나(컬럼 참조 오류), JSON 경로처럼 NULL이 되면 매출이 한 그룹으로 뭉친다. 값은 `amount`에서 오지만 숫자는 `region`에 달려 있다.

### 5. 상류 추적

```text
  원천 raw.orders.amount · raw.orders.status · raw.orders.customer_id · raw.users.user_id · raw.orders.region (모두 거리 4)
  직접 파생만 따라가면 원천: [raw.orders.amount]
```

- INDIRECT 포함 5개, 직접 파생만 1개.
- "매출이 3% 낮다"는 INDIRECT 포함으로 조사한다. 필터(`status` 값 변화), 조인 키(`customer_id`·`user_id` 형식 변화로 inner join 누락), 그룹 키(`region`)가 모두 합계를 바꿀 수 있다. `amount`만 보면 이 원인들을 놓친다.

### 6. 정적 vs 런타임

| | 정적(SQL·코드 파싱) | 런타임(실행 중 수집) |
|---|---|---|
| 장점 | 실행 전에 안다 → 배포 전 영향 분석 | 실제로 읽은 테이블·파티션·스키마·행 수 |
| 단점 | `SELECT *`·동적 SQL·UDF를 스키마 없이 못 푼다 | 한 번은 돌아야 안다, 연동 안 된 도구는 빈칸 |

- A가 놓친 것: `export.crm_contacts.email`, `dash.marketing.email`.
- 원인: `export.crm_contacts`가 `SELECT * FROM raw.users`라서, SQL 텍스트만으로는 `raw.users`의 컬럼 목록을 모른다. 그 뒤 `dash.marketing`의 `c.*`도 연쇄로 못 풀었다. 원천 스키마를 아는 B는 둘 다 찾았다.

### 7. 삭제 후에도 메일이 나간다

- 확인: PII 컬럼(`raw.users.email`)의 하류를 DIRECT 간선으로 순회한 목록에 마케팅 쪽 데이터셋이 있는지, 그리고 컬럼 계보가 "미상"인 노드가 경로에 있는지(실험 A의 경고).
- "미상" 노드는 삭제 대상에 **보수적으로 포함**한다. 확인 전까지 PII가 있다고 가정하고 조사한다.
- 근본 대처: `SELECT *` 내보내기를 없애거나 런타임 스키마로 펼친다. 해시 사본(`email_hash`)도 목록에 넣는다 — 가명화된 값도 개인정보일 수 있다(12번).

### 8. `pg_depend`의 범위

- 얻을 수 있는 것: 뷰(·머티리얼라이즈드 뷰) 정의에 박힌 의존. 실험: `v_daily → fct_orders`, `v_daily_named → v_daily, dim_customer`.
- 얻을 수 없는 것: `INSERT ... SELECT`·`COPY`·앱 코드로 옮기는 배치 잡의 의존. 실험에서 `fct_orders`와 `stg_orders` 사이 의존은 **0개**였다.
- 그래서 배치 계보는 오케스트레이터 잡 정의·쿼리 로그·OpenLineage 연동 같은 실행 쪽에서 모은다.

### 9. 재계산 순서 — 위상 정렬

- 영향받은 데이터셋을 다시 계산할 때는 상류가 먼저 끝나야 한다. DAG의 위상 정렬(DFS 후위 순서의 역순, 또는 진입 차수 기반)로 순서를 정한다.
- 이어지는 작업: 08 idempotent-pipelines-and-backfill의 백필 — 파티션 DAG를 위상 순서로 다시 돌리고, 파티션 덮어쓰기로 재실행을 안전하게 만든다.
