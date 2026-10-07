# data-engineering/10-data-quality-and-data-observability — 정답

## 정답

### 1. 초록인데 틀린 이유

- 잡의 성공은 "명령이 오류 없이 끝났다"는 뜻이다. 0행을 넣는 것은 SQL에서 오류가 아니다.
- 실험(PostgreSQL 17.11, psql)

```text
BEGIN
DELETE 0
INSERT 0 0
INSERT 0 1
COMMIT
job day=2026-10-03 exit=0
```

- 상류가 빈 파일을 주거나, 경로·파티션 이름이 바뀌어 아무것도 못 읽어도 같은 모양이 된다. 데이터를 재는 검사가 따로 있어야 한다.

### 2. 관측 5축

| 축 | 재는 것 | PostgreSQL 예 |
|---|---|---|
| 신선도 | 최신 데이터가 언제 것인가 | `now() - max(event_time)` |
| 볼륨 | 몇 행 들어왔나 | 적재 감사 테이블의 행 수, 파티션별 `count(*)` |
| 스키마 | 컬럼·타입 변화 | `information_schema.columns` 스냅숏 diff |
| 분포 | 값이 평소 범위인가 | NULL 비율, `count(DISTINCT ...)`, `pg_stats.null_frac`·`n_distinct` |
| 계보 | 어디서 와서 어디로 가나 | 11번(계보 그래프) |

- Internet Archive 2022-04-25 사본: Freshness·**Distribution**·Volume·Schema·Lineage.
- 2026-09-25 갱신판: Freshness·**Quality**·Volume·Schema·Lineage. Quality 설명이 NULL 비율·고유값 비율·허용 범위라, 옛 Distribution과 재는 대상이 비슷하다(해석).

### 3. dbt 데이터 테스트

- 단언을 반증하는 **실패 행**을 고르는 select다. 0행이면 통과.

```sql
-- unique(order_id) — dbt 기본 매크로처럼 NULL은 빼고 센다
SELECT order_id FROM fct_orders WHERE order_id IS NOT NULL GROUP BY order_id HAVING count(*) > 1;
-- not_null(customer_id)
SELECT * FROM fct_orders WHERE customer_id IS NULL;
-- accepted_values(status: PAID, SHIPPED) — NOT IN은 NULL 행을 고르지 않는다(NULL 금지는 not_null로)
SELECT * FROM fct_orders WHERE status NOT IN ('PAID','SHIPPED');
-- relationships(customer_id → dim_customer.customer_id)
SELECT * FROM fct_orders f WHERE customer_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM dim_customer c WHERE c.customer_id = f.customer_id);
```

- dbt가 실제로 만드는 SQL 문장은 버전·어댑터마다 다를 수 있다. 위는 같은 뜻의 손 SQL이다.

### 4. 합계는 멀쩡, 분포가 틀렸다

- 보이지 않는다. 주문 수·매출은 세 날 모두 400건·559,400이었다.
- 잡은 검사: 일자별 NULL 비율(10-04 40.0%)과 `not_null(customer_id)` 실패 160행.
- 고객 세그먼트별 리포트에서는 "알 수 없음" 고객의 매출이 커지는 모양으로 나타난다.

### 5. 잡 기준 신선도 vs 데이터 기준 신선도

```text
 2026-10-03 | 2026-10-04 09:00:00 | 2026-10-02 06:40:00+00 | 2 days 02:20:00 | STALE
 job_ran_recently = t
```

- 잡 기준: 10-03 잡은 제때 끝났으니 "신선". 실제로는 0행이라 최신 데이터는 여전히 10-02 것이다.
- 데이터 기준: `max(event_time)`이 10-02 06:40에 머물러 지연 2일 2시간 20분 → 30시간 임계 초과 → STALE.
- 잡 기준 신선도는 "잡이 돌았다"만 말한다. 대시보드의 "최근 업데이트: 방금"이 사람을 속이는 이유다.
- 이벤트 시각 기준도 만능은 아니다. 늦게 오는 과거 이벤트·백필만 들어오면 적재는 최신인데 `max(event_time)`은 오래될 수 있다. SLA가 묻는 것에 따라 적재 시각 컬럼을 함께 본다.

### 6. 볼륨 규칙 비교

```text
전일 대비 ±5%                    3 / 21
EWMA 요일별 max(3σ, 15%)         3 / 2
```

- 둘 다 주입한 이상 3건(0행·55%·1.9배)을 모두 잡았다.
- "전일 대비 ±5%"는 정상 39일 중 21일 울렸다. 평일 약 10,000 ↔ 주말 약 6,000 전환마다 울린다.
- 매일 울리는 경보는 무시되고, 진짜 사고가 그 사이에 묻힌다(알람 피로).
- 수치는 합성 데이터(시드 42)·이 매개변수에서 나온 것이다.

### 7. 기준선 오염

```text
day 45 ... rows      0 | ... | 학습판   10484± 6377
day 46 ... rows  11447 | ... | 학습판    8387±13813
```

- 이상값(0)까지 평균·분산 갱신에 넣자 다음 날 3σ 밴드가 ±6,377에서 ±13,813으로 두 배 넘게 넓어졌다. 평균도 10,484에서 8,387로 끌려 내려갔다.
- 밴드는 그 뒤에도 넓게 남았다. 55일에 학습판 기준선은 10,183±8,050이라 반토막(3,842행)이 밴드 안에 들어 경보가 나지 않았다(학습판 탐지 1/3).
- 고치기: 이상으로 판정한 값은 기준선 갱신에서 뺀다(실험의 기본판). 확인된 사고 날짜는 수동 제외 표시. 계절성은 요일별 기준선으로 나눈다.

### 8. 차단 vs 경고

- 차단: 하류가 틀린 결정을 내리는 위반 — 0행, 키 중복(합계 2배), 참조 깨짐(행 누락).
- 경고: 해석이 필요한 변화 — 분포 이동, 새 enum 값, 소폭 볼륨 감소.
- 차단하면 데이터가 늦는다. 그래서 차단된 테이블에는 **신선도 경보**를 같이 걸어야 한다. 아니면 "틀린 숫자는 막았지만 아무도 모르게 늦은" 상태가 된다.
- dbt: `severity: error`(기본) vs `severity: warn`, 실패 행 수 조건 `error_if`·`warn_if`(기본 `!=0`). 예: `warn_if: ">10"`, `error_if: ">1000"`.
  - 단 dbt 테스트는 모델을 만든 뒤 돈다. `error` 실패는 `dbt build`의 하류 노드를 건너뛰게 할 뿐 그 테이블을 되돌리지 않는다. 공개 자체를 막으려면 검증용 테이블에서 검사한 뒤 게시하는 단계를 따로 둔다.

### 9. 다음 축은 계보

- NULL이 어디서 생겼는지는 **계보** 축으로 본다. 그 컬럼을 만든 상류 잡·데이터셋·컬럼을 거슬러 올라가 처음 NULL이 나타난 지점을 찾는다.
- 다루는 노트: 11-data-lineage(상류 BFS·컬럼 수준 계보). 상류 필드 이름 변경이 원인이면 09-data-contracts의 시나리오 1로 이어진다.
