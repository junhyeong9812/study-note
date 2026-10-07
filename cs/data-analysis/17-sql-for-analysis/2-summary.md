# data-analysis/17-sql-for-analysis — 분석 SQL: 코호트·퍼널·리텐션·세션화, 팬아웃과 날짜 경계 — 정리 (힌트)

## 해결하는 문제

분석 질문의 대부분은 결국 SQL 한 장이 된다. "가입 주별로 몇 %가 다음 주에 돌아왔나", "방문 → 장바구니 → 구매에서 어디서 빠지나", "한 번 들어와서 몇 개를 보나". 문법은 맞는데 **숫자가 틀리는** SQL이 흔하다.

```text
  질문                     SQL 모양                         흔히 틀리는 곳
  구매 전환율              users ⟕ orders ⟕ items          조인이 행을 불려 122%가 나온다
  일별 매출                date_trunc('day', ts)            세션이 UTC면 한국 새벽 매출이 전날로
  주간 리텐션              가입 주 × 경과 주                 아직 안 지난 주를 0%로 그린다
  세션 수                  이벤트 사이 간격 > 30분           평균을 이벤트 단위로 내 세션 크기를 부풀린다
```

쉬운 예: 반 학생 30명에게 "숙제 낸 비율"을 물었다. 숙제 노트를 과목별로 붙여 세면 과목 수만큼 학생이 불어난다. 낸 학생은 20명인데 "낸 기록"은 60개라 200%가 된다.

똑같은 구조다.\
사용자에 주문을, 주문에 품목을 붙이면 **한 행이 무엇인지(grain)**가 바뀐다. 그 상태로 세면 분모·분자의 단위가 어긋난다.

- *grain(그레인, 한 행의 단위)*: 결과 테이블의 한 행이 무엇 하나를 뜻하는지. "사용자 1명", "주문 1건", "주문 품목 1개".

실무 예:
- 마케팅 대시보드의 전환율이 100%를 넘는다. 주문 품목 테이블을 붙인 뒤 `count(*)`로 셌다.
- 월요일 아침 리포트의 "어제 매출"이 앱 관리자 화면과 다르다. 하나는 UTC 자정, 하나는 KST 자정으로 잘랐다.
- 최근 가입 코호트의 리텐션이 급락한 것처럼 보인다. 아직 시간이 안 지난 칸을 0으로 채웠다.

## 동작·원리

이 노트의 실험은 모두 같은 합성 데이터다(PostgreSQL 17.11, 실험 절 참조). 사용자 400명, 방문 1,368회, 이벤트 4,680개, 주문 247건, 주문 품목 488개.

### 1. 조인 팬아웃 — grain이 바뀌면 분모·분자가 어긋난다

```text
  users (400행, grain=사용자)
     │ 1:N
  orders (247행, grain=주문)          사용자 1명 → 주문 0~여러 건
     │ 1:N
  order_items (488행, grain=품목)      주문 1건 → 품목 1~3개

  users ⟕ orders ⟕ order_items = 716행  ← grain이 "사용자×주문×품목"으로 바뀜
```

- *팬아웃(fan-out)*: 1:N 조인 뒤 왼쪽 행이 N번 복제되는 것. 복제된 행에 `count(*)`·`sum()`을 하면 부푼다. 문법·사례 상세는 [languages/sql/syntax/25-join-fan-out](../../../languages/sql/syntax/25-join-fan-out/2-summary.md)에 있다.

실험 결과(쿼리 [1]·[1b]):

```text
 rows_after_join | wrong_rate_count_rows | right_rate_distinct_users
-----------------+-----------------------+---------------------------
             716 |    1.2200000000000000 |    0.43000000000000000000

 inflated_revenue | true_revenue
------------------+--------------
         26575000 |     13635000
```

- 조인 행을 세면 전환율이 122%다. 구매한 사용자 수를 `count(DISTINCT user_id)`로 세면 43%(172명/400명)다.
- 품목을 붙인 뒤 `sum(amount)`를 하면 매출이 1.95배다. 주문 금액은 주문 grain의 값인데 품목 grain에서 더했다.
- 처방: **집계를 먼저 하고 붙인다**(선집계). 또는 세는 대상의 키로 `count(DISTINCT …)`를 쓴다. `sum(DISTINCT amount)`는 금액이 같은 다른 주문을 합쳐 버리므로 처방이 아니다(syntax/25 §5).

### 2. 퍼널 — 단계의 순서를 지키나

```text
  view ──▶ cart ──▶ purchase
  순서 무시: 각 단계를 "한 번이라도 한" 사용자 수
  순서 지킴: 첫 view 뒤의 cart, 그 cart 뒤의 purchase만 인정
```

```text
[2] 순서 무시     viewed 394 | carted 278 | purchased 172
[2b] 순서 지킴    viewed 394 | carted_after_view 278 | purchased_after_cart 90
```

- 이 합성 데이터에서는 구매 이벤트가 장바구니 없이도 나온다(생성 규칙). 그래서 순서를 지키면 구매 단계가 172 → 90으로 줄었다.
- 어느 쪽이 맞는지는 질문이 정한다. "장바구니를 거친 구매만 퍼널로 본다"면 순서를 지켜야 한다. 두 정의를 섞어 쓰면 단계 사이 전환율이 1을 넘을 수도 있다.
- 퍼널의 분모는 보통 사용자(또는 세션)다. 이벤트 수로 세면 1번 문제(grain)가 다시 생긴다.

### 3. 코호트 리텐션 — 다 자라지 않은 칸

```text
              경과 주 →  w0    w1    w2    w3
  가입 주 08-31          ■     ■     ■     ■      관측 끝: 10-08 00:00 KST
  가입 주 09-14          ■     ■     ■     ?      ← w3를 다 지난 사용자가 아직 없다 (w2도 일부만)
  가입 주 09-28          ■     ?     ?     ?      ← w1이 일부 사용자에게 막 시작됐고, 끝난 사용자는 없다
```

- *코호트(cohort)*: 같은 시점(예: 가입 주)에 시작한 사용자 묶음. *리텐션*: 그 묶음 중 N주차에 다시 활동한 비율.
- 관측 끝을 넘은 칸은 "0%"가 아니라 "아직 모름"이다. 분모에서 그 주차가 다 지난 사용자만 남긴다.

실험 결과(쿼리 [3], 숫자는 %):

```text
 [3a] 안 지난 칸도 0으로 셈            [3b] 지난 사용자만 분모(나머지는 NULL)
 cohort  size  w0  w1  w2  w3          cohort  w0  w1  w2  w3  w3_denominator
 08-31     91  92  55  27   4          08-31   92  55  27   4              91
 09-07     88  99  49  15   6          09-07   99  49  15   5              41
 09-14    108  94  61  14   2          09-14   94  61  10                  0
 09-21    104  95  50   4   0          09-21   95  54
 09-28      9 100  33   0   0          09-28  100
```

- 3a에서 09-21 코호트의 w2가 4%로 "급락"해 보인다. 3b에서는 비어 있다. 그 주차를 다 지난 사용자가 없어서다.
- 09-07 코호트의 w3 분모는 88명이 아니라 41명이다. 나머지 47명은 아직 w3가 끝나지 않았다. 같은 칸이 6%(3a)와 5%(3b)로 다르다.
- 가입 주는 `date_trunc('week', signup_at, 'Asia/Seoul')`로 잘랐다. 출력의 08-31·09-07·…은 모두 월요일이다(문서 9.9.1의 `week` 필드 설명: ISO 주는 월요일에 시작).

### 4. 세션화 — gaps-and-islands

```text
  한 사용자의 이벤트 (시각 순, 실험 [4b] user_331 — 앞 셋은 09-09)
  22:31  22:54  23:00 │ 09-11 12:52  12:58  13:05 …
     간격  22분   6분  │ 37시간 52분  6분    7분
  new_session 1   0   0 │    1         0      0
  누적합      1   1   1 │    2         2      2      ← 세션 번호
```

- *gaps-and-islands*: 정렬된 행에서 "끊김(gap)"으로 연속 구간(island)을 나누는 패턴. 단계는 둘이다.
  - ① `lag()`로 직전 행과의 간격을 보고, 경계면 1·아니면 0 표시를 단다.
  - ② 그 표시의 누적 `sum() OVER (… ORDER BY ts)`가 구간 번호가 된다.
- 세션 기준 30분은 이 실험의 선택이다. 기준을 바꾸면 세션 수가 바뀐다.
  - 흔한 오해: "세션"이 표준 정의를 가진다. 도구마다 무활동 기준·자정 끊김 규칙이 다르다 `[?]`(도구별 기본값은 확인하지 않았다).

```text
 events | sessions | per_session | event_weighted
--------+----------+-------------+----------------
   4680 |     1368 |        3.42 |           3.69
```

- 30분 기준으로 나눈 세션 수(1,368)가 생성한 방문 수(1,368)와 같다. 생성 규칙상 한 방문 안의 이벤트 간격은 30분을 넘지 않고(k번째 이벤트 = 시작 + k×7분 + 0~2분), 같은 사용자의 방문끼리는 11시간 넘게 떨어진다(방문 시작은 가입 시각 + d일 + 0~12시간). 기준이 생성 규칙과 맞으면 세션화가 방문을 그대로 되찾는다는 확인이다.
- "세션당 이벤트 수"를 두 방법으로 냈다. 세션 수로 나누면 3.42다. 이벤트 행마다 자기 세션 크기를 붙여 평균하면 3.69다. 큰 세션이 그 크기만큼 여러 번 세져 부푼다. 16번의 "비율 지표 vs 사용자 평균"과 같은 가중치 문제다.

### 5. 연속 일수 — 날짜 − 행 번호

```text
  방문일   10-01  10-02  10-03  10-05  10-06
  row_no      1      2      3      4      5
  일 − row   09-30  09-30  09-30  10-01  10-01   ← 같은 값 = 같은 연속 구간
```

```text
 streak | islands
--------+---------
      1 |     769
      2 |     170
      3 |      49
      4 |      19
      5 |       4
```

- 연속한 날짜에서 행 번호를 빼면 같은 값이 나온다. 그 값으로 묶으면 연속 구간이다. 날짜는 KST로 바꾼 뒤 `::date`로 잘랐다.

### 6. 백분위 — `percentile_cont` vs `percentile_disc`

```text
  값       10   20   30   40   1000
  위치      0   .25  .5   .75   1     (cont: (n−1)×비율 위치에서 보간)

  p50  cont 30   disc 30
  p75  cont 40   disc 40
  p90  cont 616.0000000000001   disc 1000    ← 40과 1000 사이를 0.6만큼 보간
```

- PostgreSQL 17 문서 9.21 표 9.62: `percentile_cont`는 "필요하면 인접 입력 사이를 보간"한다. `percentile_disc`는 "순서상 위치가 지정 비율 이상인 첫 값"을 돌려준다(입력에 있는 값).
- p90 cont = 40 + 0.6×(1000−40) = 616. 부동소수점 계산이라 `616.0000000000001`로 나왔다.
- 백분위의 정의는 도구마다 다르다. Python 3.12 `statistics.quantiles`의 기본 `method='exclusive'`는 위 cont와 다른 값을 줄 수 있다([24-reproducible-analysis](../24-reproducible-analysis/2-summary.md) 실험 E). 지연 분포·병합 문제는 [data-analysis 05](../05-percentiles-and-latency-distributions/2-summary.md)에서 다룬다.

### 7. 날짜 경계

```text
[7] 일별 주문 수
   d   | utc_day | kst_day
-------+---------+---------
 09-10 |      13 |      13
 09-11 |       3 |       6
 09-12 |       7 |       5
 09-13 |      10 |       6
```

- 세션 `TimeZone`이 UTC일 때 `date_trunc('day', ts)`는 UTC 자정으로 자른다. 한국 00:00~08:59 주문이 전날로 간다. 세 번째 인자 `'Asia/Seoul'`을 주면 KST 자정으로 자른다.
- 원리·9시간 밀림은 [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md)에 있다. 여기서는 "분석 SQL은 날짜를 자르는 모든 곳에 시간대를 적는다"만 기억한다.

### 실험 환경과 데이터

(실험, `setup.sql`·`queries.sql`·`pushdown.sql`, 일회용 컨테이너 `postgres:17` — `PostgreSQL 17.11 (Debian 17.11-1.pgdg13+2)`, `--network none --cpus=2`, `docker exec -i … psql`로 실행. `setseed(0.17)`로 고정, 같은 스키마를 지우고 다시 만들어 돌렸을 때 출력이 같음을 `diff`로 확인.)

```sql
-- 방문: 가입 후 d일째에 확률 0.55*exp(-d/6)로 방문 1회 (관측 끝 2026-10-08 00:00 KST)
CREATE TABLE visits AS
SELECT u.user_id, u.signup_at + d * interval '1 day' + (random() * 12 * 3600) * interval '1 second' AS start_at
FROM users u, generate_series(0, 27) d
WHERE random() + 0 * hashtext(u.user_id) < 0.55 * exp(-d / 6.0);   -- 외부 행을 참조해야 쌍마다 random()이 다시 뽑힌다
```

- 합성 데이터를 만들다 생긴 함정 하나. 처음에는 조건을 `WHERE random() < 0.55 * exp(-d / 6.0)`로 썼다. 이 조건은 `d`만 참조한다. PostgreSQL 17 플래너는 한 테이블(여기서는 함수 스캔)만 참조하는 조건을 그 스캔의 필터로 붙인다. `random()`이 휘발성 함수여도 그랬다(`EXPLAIN`: `Nested Loop` 바깥쪽 `Function Scan on generate_series d` 아래 `Filter: (random() < …)`, 안쪽은 `Materialize` 된 `users`).
  - 그래서 `random()`이 `d` 값마다 한 번(28번)만 뽑혔다. 살아남은 `d`는 7 하나였다. 모든 사용자가 **가입 후 같은 경과일(d = 7)**에만 방문한 데이터가 됐다(`pushdown.sql` [P1]: 400쌍, `d` 값 1개 — 가입일이 달라 달력 날짜로는 28개로 갈린다). 외부 행을 참조하게 바꾸자 조건이 조인 필터(`Join Filter`)로 올라가 쌍마다 평가됐고, 1,399쌍·`d` 값 27개로 퍼졌다([P2]).
  - `LATERAL` 하위 쿼리로 감싸도 `random()` 조건이 `u`를 참조하지 않으면 똑같이 함수 스캔 필터로 내려갔다(같은 `postgres:17` 컨테이너에서 확인: 400쌍·`d` 값 1개). 고치는 열쇠는 조건 자체가 바깥 행을 참조하게 하는 것이다.
  - 교훈: 무작위 합성 데이터도 분포를 한 번 집계해 보고 쓴다.

## 쓰이는 자료구조·알고리즘

- **윈도 함수** — `lag`·`row_number`·누적 `sum() OVER`. 프레임 기본값·평가 시점은 [database/05-window-functions-and-cte](../../database/05-window-functions-and-cte/2-summary.md), 문법은 [languages/sql/syntax/26](../../../languages/sql/syntax/26-window-functions-vs-aggregates/2-summary.md)·[28 프레임](../../../languages/sql/syntax/28-window-frames-rows-range-groups/2-summary.md)·[30 `lag`/`lead`](../../../languages/sql/syntax/30-offset-and-boundary-functions/2-summary.md).
- **gaps-and-islands** — 정렬 + 경계 표시 + 누적합(세션화), 정렬 + 행 번호 차이(연속 일수). 둘 다 정렬 한 번 뒤 선형 스캔이다.
- **조건부 집계** — `count(*) FILTER (WHERE …)`로 퍼널·코호트 칸을 한 번의 스캔에 만든다([languages/sql/syntax/24](../../../languages/sql/syntax/24-conditional-aggregation-filter-case/2-summary.md)). SQL:2003의 선택 기능이며 지원하지 않는 DB에서는 `SUM(CASE WHEN … THEN … END)`로 흉내 낸다(Winand, modern-sql.com).
- **해시 집계·`count(DISTINCT)`** — 팬아웃 처방. 실행 방식은 [database/41-sorting-and-aggregation](../../database/41-sorting-and-aggregation/2-summary.md).
- **순서 통계** — `percentile_cont`/`disc`는 그룹 안을 정렬해 위치를 고른다.

## 적용 — 풀어나가는 법

### 1. 순서

1. **증상**: 비율이 1을 넘는다, 합계가 원천보다 크다, 최근 코호트만 급락, 일별 값이 다른 화면과 다르다.
2. **grain을 적는다**: 결과 한 행 = 무엇. 조인할 때마다 grain이 바뀌는지 본다(1:N이면 바뀐다).
3. **원리로 내려간다**: 분자·분모가 같은 grain인가, 관측 창이 다 지났나, 날짜를 어느 시간대로 잘랐나.
4. **SQL로 대조한다**: 조인 전후 행 수, `count(*)` vs `count(DISTINCT 키)`, 원천 테이블 단독 합계와 비교.

### 2. 팬아웃 점검 쿼리

```sql
-- 조인 전후 행 수와 키 개수를 한 번에 본다: 행 수 > 키 개수면 팬아웃
SELECT count(*) AS rows, count(DISTINCT u.user_id) AS users, count(DISTINCT o.order_id) AS orders
FROM users u LEFT JOIN orders o USING (user_id) LEFT JOIN order_items i USING (order_id);

-- 선집계 후 조인: 주문 grain의 금액은 주문 grain에서 더한다
WITH per_user AS (SELECT user_id, sum(amount) AS revenue, count(*) AS n_orders FROM orders GROUP BY user_id)
SELECT count(*) FILTER (WHERE n_orders > 0)::numeric / count(*) AS conversion, sum(revenue) AS revenue
FROM users u LEFT JOIN per_user p USING (user_id);
```

### 3. 세션화 틀 (PostgreSQL 17)

```sql
WITH g AS (
  SELECT user_id, ts,
         CASE WHEN lag(ts) OVER w IS NULL OR ts - lag(ts) OVER w > interval '30 minutes' THEN 1 ELSE 0 END AS new_session
  FROM events
  WINDOW w AS (PARTITION BY user_id ORDER BY ts)
)
SELECT user_id, ts, sum(new_session) OVER (PARTITION BY user_id ORDER BY ts) AS session_no
FROM g;
```

- 같은 시각 이벤트가 있으면 `ORDER BY ts`만으로는 순서가 매번 달라질 수 있다. 고유 키를 두 번째 정렬 키로 둔다([database/05](../../database/05-window-functions-and-cte/2-summary.md) 장애 3).
- 누적 `sum()`의 기본 프레임은 `ORDER BY`가 있으면 `RANGE … CURRENT ROW`라 같은 `ts` 동률 행이 같은 값을 받는다. 동률이 있으면 `ROWS` 프레임과 고유 정렬 키를 쓴다.

### 4. 코호트 표의 성숙도

```sql
-- 주차 wk가 관측 끝 전에 완전히 지난 사용자만 분모로
WHERE u.signup_at + (wk + 1) * interval '7 days' <= :observation_end
```

- 리포트에 관측 끝 시각을 같이 찍는다. 그래프에서 미성숙 칸은 빈칸으로 둔다(0으로 그리지 않는다).

## 장애 시나리오와 대처

### 1. 조인 팬아웃으로 전환율 부풀림 (⚠ 커리큘럼)

- **현상**: 전환율이 비정상적으로 높거나 100%를 넘는다. 매출 합계가 결제 시스템 합계보다 크다.
- **보이는 형태**: 실험에서 전환율 122%(정답 43%), 매출 26,575,000(정답 13,635,000, 1.95배).
- **원인**: 사용자·주문·품목을 붙여 grain이 품목이 된 상태로 `count(*)`·`sum(amount)`를 했다.
- **대처**: grain을 적고, 선집계 후 조인하거나 `count(DISTINCT 키)`를 쓴다. 원천 테이블 단독 합계와 대조하는 검사를 리포트 쿼리 옆에 둔다.

### 2. 시간대 경계에서 날짜가 잘림 (⚠ 커리큘럼)

- **현상**: "어제 매출"이 화면마다 다르다. 자정 근처 주문이 전날로 잡힌다.
- **보이는 형태**: 실험에서 09-11 주문 수가 UTC 기준 3, KST 기준 6.
- **원인**: 세션 `TimeZone`이 UTC인 채로 `date_trunc('day', ts)`·`ts::date`를 썼다.
- **대처**: 날짜를 자르는 모든 곳에 시간대를 적는다(`date_trunc('day', ts, 'Asia/Seoul')`, 범위는 `>= '…+09' AND < '…+09'`). 날짜 이름표는 `(ts AT TIME ZONE 'Asia/Seoul')::date`로 붙인다 — `date_trunc(…, 'Asia/Seoul')::date`는 세션이 UTC면 하루 앞 날짜가 된다([27](../27-da-symptom-index/2-summary.md) 0-2절). 상세는 [database/27](../../database/27-temporal-types-and-session-timezone/2-summary.md).

### 3. 최근 코호트의 리텐션이 급락한 것처럼 보인다

- **현상**: 코호트 표 오른쪽 아래가 0%·한 자릿수로 붉다.
- **보이는 형태**: 실험 3a에서 09-21 코호트 w2 4%, 09-28 코호트 w2·w3 0%.
- **원인**: 관측 끝을 넘은 칸을 0으로 셌다. 분모에 아직 그 주차에 도달하지 않은 사용자가 섞였다.
- **대처**: 주차별로 "다 지난 사용자"만 분모로 두고 나머지는 NULL(3b). 표에 관측 끝 시각을 적는다.

### 4. 세션·퍼널 정의가 리포트마다 다르다

- **현상**: 같은 기간 "세션당 페이지 수"가 3.4와 3.7로 다르다. 퍼널 구매 단계가 172와 90으로 다르다.
- **보이는 형태**: 숫자 차이가 일정하게 유지된다(버그가 아니라 정의 차이).
- **원인**: 평균의 가중(세션 단위 vs 이벤트 단위), 단계 순서 인정 여부, 무활동 기준이 다르다.
- **대처**: 정의(무활동 기준·순서 규칙·분모)를 지표 명세에 적고([16-metrics-design](../16-metrics-design/2-summary.md)) 공용 뷰로 한 번만 구현한다.

### 5. 백분위 값이 도구마다 다르다

- **현상**: SQL의 p90과 Python 노트북의 p90이 다르다.
- **보이는 형태**: 실험에서 같은 다섯 값의 p90이 `percentile_cont` 616, `percentile_disc` 1000.
- **원인**: 보간 방식(연속 vs 이산)과 위치 공식이 도구마다 다르다. 표본이 작을수록 차이가 크다.
- **대처**: 함수·방법을 명세에 적는다(예: "PostgreSQL 17 `percentile_cont`"). 비교하는 두 수치를 같은 정의로 계산한다.

## 핵심 문장

- 분석 SQL은 결과 한 행이 무엇인지(grain)부터 적는다. 1:N 조인은 grain을 바꾸고, 바뀐 grain에서 센 값은 부푼다.
- 분자와 분모는 같은 단위여야 한다. 전환율이 1을 넘으면 팬아웃부터 의심한다 — 먼저 조인 전후 행 수를 본다.
- 코호트 표의 미래 칸은 0이 아니라 "아직 모름"이다. 그 주차를 다 지난 사용자만 분모로 둔다.
- 세션화와 연속 일수는 둘 다 gaps-and-islands다. 경계 표시의 누적합, 또는 날짜에서 행 번호를 뺀 값으로 묶는다.
- 날짜를 자르는 모든 곳에 시간대를 적는다. 백분위는 함수 이름(cont/disc)까지 적는다.

## 관련 주제·근거

- 선행
  - [database/05-window-functions-and-cte](../../database/05-window-functions-and-cte/2-summary.md) — 윈도 함수·CTE
  - [database/04-sql-joins-and-aggregation](../../database/04-sql-joins-and-aggregation/2-summary.md) — 조인·집계
- 후속·연결
  - [languages/sql/syntax/25-join-fan-out](../../../languages/sql/syntax/25-join-fan-out/2-summary.md) · [26](../../../languages/sql/syntax/26-window-functions-vs-aggregates/2-summary.md) · [28](../../../languages/sql/syntax/28-window-frames-rows-range-groups/2-summary.md) · [30](../../../languages/sql/syntax/30-offset-and-boundary-functions/2-summary.md) · [32 CTE](../../../languages/sql/syntax/32-cte-with-clause/2-summary.md) — 문법 상세(커리큘럼 '연결': syntax/26~33)
  - [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md) — 날짜 경계
  - [data-engineering/03-dimensional-modeling](../../data-engineering/03-dimensional-modeling/2-summary.md) — 팩트 테이블의 grain
  - [16-metrics-design](../16-metrics-design/2-summary.md) — 지표 정의(분자·분모·단위)
  - [18-data-cleaning-and-quality](../18-data-cleaning-and-quality/2-summary.md) — 중복·시간대 혼합 정제
  - [24-reproducible-analysis](../24-reproducible-analysis/2-summary.md) — 쿼리를 스크립트로 남기기
  - [data-analysis 05](../05-percentiles-and-latency-distributions/2-summary.md) 백분위, [27](../27-da-symptom-index/2-summary.md) 증상 색인
- 근거
  - PostgreSQL 17 문서 9.21 Aggregate Functions, 표 9.62 Ordered-Set Aggregate Functions — `percentile_cont`(보간), `percentile_disc`(위치가 비율 이상인 첫 값) <https://www.postgresql.org/docs/17/functions-aggregate.html>
  - PostgreSQL 17 문서 9.22 Window Functions <https://www.postgresql.org/docs/17/functions-window.html> · 9.9 `date_trunc`(시간대 인자)
  - Markus Winand, modern-sql.com "The FILTER clause" — SQL:2003 선택 기능 T612, `CASE`로 흉내 내기 <https://modern-sql.com/feature/filter>
  - 커리큘럼 📚 칸의 "Mode" 자료는 열람하지 않았다 `[?]`
- 실험 목록
  - `setup.sql` — 합성 사용자·방문·이벤트·주문·품목 생성(`setseed(0.17)`), `queries.sql` — [1] 팬아웃 전환율·매출, [2] 퍼널 순서 무시/지킴, [3] 코호트 리텐션 미성숙 칸, [4] 30분 세션화와 평균 가중, [5] 연속 일수, [6] `percentile_cont`/`disc`, [7] UTC/KST 일별 집계. `pushdown.sql` — `random()` 필터 내림으로 합성 데이터가 뭉치는 현상(고친 판의 `EXPLAIN` `Join Filter`, `LATERAL`로 감싼 판도 같은 환경에서 확인). 환경: `postgres:17`(17.11) 일회용 컨테이너, `--network none`, 재실행 `diff` 동일.
