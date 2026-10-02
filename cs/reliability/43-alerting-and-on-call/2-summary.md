# reliability/43-alerting-and-on-call — 증상 기반 경보·번 레이트 경보·온콜 — 정리 (힌트)

## 해결하는 문제

지표(16)가 있어도 누군가 보고 있어야 쓸모가 있다. 새벽 3시에 결제가 멈추면 **사용자보다 먼저** 사람이 알아야 한다. 그것이 경보다.\
그런데 경보를 많이 걸면 반대 사고가 난다. 매일 밤 "CPU 80%"가 울리고, 대부분 아무 일도 아니다. 사람은 경보를 건너뛰기 시작하고, 진짜 장애 경보도 같이 건너뛴다.

```text
 원인마다 경보                                  증상 + 예산 소모 속도로 경보
 CPU>80%, 디스크>70%, GC>1s, 큐>100, 재시도↑     "사용자 요청 실패가 에러 버짓을 빨리 태우고 있다"
 → 밤마다 10건, 사용자 영향 없는 것이 대부분       → 울리면 사용자가 아프다. 드물고, 울리면 움직인다
 → 피로 → 진짜 경보도 무시                        → 원인 지표는 대시보드·티켓으로
```

- *경보(alert)*: 조건이 맞으면 사람에게 보내는 알림. SRE 6장은 받는 곳에 따라 page(호출기)·ticket(작업 대기열)·email로 나눈다.
- *page*: 지금 바로 사람이 움직여야 하는 경보. 잠을 깨운다.
- *온콜(on-call)*: 정해진 기간 동안 page를 받고 정해진 시간 안에 대응하는 당번.

쉬운 예: 화재경보기다. 연기(증상)가 나면 울린다. "주방 온도 25도"(원인 후보)마다 울리면 아무도 경보기를 믿지 않는다.\
똑같은 구조다.\
실무 예: SLO 99.9%인 결제 API. "1시간 동안 에러 버짓의 2%를 썼고 지난 5분에도 계속 쓰고 있다"면 page, "3일 동안 10%"면 ticket. CPU·GC는 대시보드와 원인 조사용으로 남긴다.

## 동작·원리

### 1. 경보가 사람에게 닿기까지

```text
 지표(Prometheus TSDB)
   │ 규칙 평가(예: 1분마다)  expr 참 → pending ─(for 기간 동안 계속 참)→ firing
   ▼
 Alertmanager
   │ 묶기(grouping): 같은 원인으로 동시에 뜬 경보 수백 개 → 알림 1건
   │ 억제(inhibition): "클러스터 접근 불가"가 떴으면 그 아래 경보는 보내지 않음
   │ 침묵(silence): 점검 시간 등 알려진 기간 동안 끔
   │ 라우팅: severity=page → 호출 서비스, ticket → 이슈 대기열
   ▼
 온콜 1차 ─(응답 없음)→ 2차 ─→ 개발 팀 에스컬레이션
   │ 경보에 걸린 런북(44)을 열고 완화 → 사후 조치(26)
```

- `for`: 조건이 이 기간 동안 매 평가에서 참이어야 firing이 된다. 그 전은 pending이다(Prometheus 문서 "Alerting rules").
- Alertmanager 기본값(설정 문서): `group_wait` 30s, `group_interval` 5m, `repeat_interval` 4h.

### 2. 증상 vs 원인

SRE 6장 표 6-1의 예다.

| 증상(무엇이 고장인가) | 원인(왜) |
|---|---|
| HTTP 500·404를 낸다 | DB가 연결을 거절한다 |
| 응답이 느리다 | CPU가 과부하, 또는 케이블 손상으로 부분 패킷 손실 |
| 비공개 콘텐츠가 누구에게나 보인다 | 배포가 ACL을 빠뜨려 모든 요청을 허용 |

- 증상은 사용자가 겪는 것이고, 원인은 그 이유(의 후보)다. 원인은 여러 개일 수 있고, 원인이 있어도 증상이 없을 수 있다(재시도로 가려짐·트래픽이 빠진 곳).
- SRE 6장의 page 원칙
  - page가 울릴 때마다 긴박하게 반응할 수 있어야 한다. 그런 반응은 하루에 몇 번만 가능하다.
  - page는 행동할 수 있어야(actionable) 한다. 기계적인 대응만 필요하면 page가 아니다(자동화 대상).
  - 원인보다 증상을 잡는 데 훨씬 많은 노력을 쓴다. 원인은 매우 확실하고 임박한 것만(디스크가 4시간 뒤 찬다 등).
- 다층 시스템에서는 한 사람의 증상이 다른 사람의 원인이다. DB 팀에게 "느린 읽기"는 증상이고, 프런트엔드 팀에게는 원인이다(SRE 6장).

### 3. 번 레이트 — 예산을 얼마나 빨리 태우나

번 레이트의 정의·표 5-8 유도와 "순진한 경보 vs 다중 창" 30일 시뮬레이션은 [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) §5에 있다. 여기서는 경보 설계 관점(감지·해제·재현율)으로 다시 보고, 실제 PromQL 규칙을 promtool로 시험한다.

```text
 SLO 99.9% / 30일 → 에러 버짓 = 요청의 0.1%
 번 레이트 = (지금 오류율) / 0.1%
   번 1    = 0.1% 오류  → 30일에 정확히 소진
   번 10   = 1%   오류  → 3일에 소진
   번 14.4 = 1.44%       → 1시간 지속 시 30일 예산의 2% 사용
   번 1000 = 100% 오류   → 43분에 소진   (SRE Workbook 표 5-4)
 1시간 창에서 예산 2% = 14.4 × 1h / 720h
```

- *에러 버짓(error budget)*: SLO가 허용하는 실패의 양. 99.9%면 0.1%다(02).
- *번 레이트(burn rate)*: SLO 대비 버짓을 쓰는 속도. 1이면 기간 끝에 딱 0이 된다(SRE Workbook 5장).
- 경보 하나가 울리기까지 쓴 예산 비율 ≈ 번 레이트 × 창 길이 / SLO 기간. 요청량이 일정하다고 가정한 근사다. 트래픽이 출렁이면 실제 값은 `창의 실패 요청 수 ÷ (기간 총 요청 수 × 허용 오류율)`로 센다. 그래서 "예산의 몇 %를 쓰면 깨운다"를 먼저 정하고 창과 번 레이트를 역산한다.
- Workbook 5장은 경보 규칙을 네 가지로 평가한다.
  - *정밀도(precision)*: 울린 경보 중 의미 있는 사건의 비율.
  - *재현율(recall)*: 의미 있는 사건 중 경보가 울린 비율.
  - *감지 시간(detection time)*: 사건 시작부터 경보까지.
  - *해제 시간(reset time)*: 사건이 끝난 뒤에도 경보가 계속 울리는 시간.

### 4. 다중 창·다중 번 레이트 (Workbook 5장 방법 6)

| 심각도 | 긴 창 | 짧은 창 | 번 레이트 | 쓴 예산 |
|---|---|---|---|---|
| page | 1시간 | 5분 | 14.4 | 2% |
| page | 6시간 | 30분 | 6 | 5% |
| ticket | 3일 | 6시간 | 1 | 10% |

```text
 긴 창: 의미 있는 양을 썼나? (정밀도)       ─┐
 짧은 창(긴 창의 1/12): 지금도 쓰고 있나?  ─┴─ AND → 끝나면 짧은 창이 먼저 내려가 해제가 빠르다
 여러 (창, 번 레이트) 쌍을 OR → 빠른 대량 소모와 느린 꾸준한 소모를 둘 다 잡는다 (재현율)
```

- Workbook의 그림 5-6 설명: 15% 오류가 10분 이어지면 짧은 창은 즉시, 긴 창은 5분 뒤 임계를 넘어 그때 울린다. 오류가 멈추면 짧은 창이 5분 뒤 내려가 경보가 멈춘다. 긴 창만 쓰면 60분 뒤에야 내려간다.

### 5. 실험: 경보 규칙 셋의 감지·해제 비교 (시뮬레이션)

- 분당 요청 1000, 평소 오류율 0.02%, SLO 99.9%(30일). 4일째 0시에 사건을 넣고 1분 해상도로 규칙을 평가했다.
- 규칙
  - S1: 10분 오류율 > 0.1% (Workbook 방법 1)
  - S4: 1시간 번 레이트 > 14.4 (방법 4의 한 창. 문서 예는 36이지만 방법 6과 맞추려고 14.4로 뒀다)
  - S6: 방법 6 — page = (1h & 5m > 14.4) or (6h & 30m > 6), ticket = (3d & 6h > 1)

```java
static double ratio(double[] p, int t, int w) { int s = Math.max(0, t + 1 - w); return (p[t + 1] - p[s]) / ((t + 1 - s) * REQ); } // 누적 합으로 창 오류율
String page = run(p, inc, t -> (ratio(p, t, 60) > 14.4 * SLO_ERR && ratio(p, t, 5) > 14.4 * SLO_ERR)
        || (ratio(p, t, 360) > 6 * SLO_ERR && ratio(p, t, 30) > 6 * SLO_ERR));
```

(실험, JDK 21.0.12 temurin 단일 파일 시뮬레이션, 결정적, 2026-10-01 — 2026-10-02 재실행: 평가 구간을 9일로 늘려 2일 사건 뒤 해제까지 보고, 총소모 열 추가)

- *추가소모*: 평시 오류(0.02%)를 뺀, 사건이 더 쓴 예산. *총소모*: 사건 기간에 난 오류 전부가 쓴 예산(30일 예산 대비).

```text
사건                                 추가소모      총소모 | S1 10분>0.1%              | S4 1h 번>14.4             | S6 다중 창(page / ticket)        
전면 장애 100% × 10분                 23.14%   23.15% | 감지 1m, 해제 +9m            | 감지 1m, 해제 +59m           | 감지 1m, 해제 +29m / 감지 4m, 해제 +5h59m
15% 오류 × 10분(워크북 그림 5-6)          3.47%    3.47% | 감지 1m, 해제 +9m            | 감지 6m, 해제 +54m           | 감지 6m, 해제 +4m / 안 울림
2% 오류 × 3시간(번 20)                 8.25%    8.33% | 감지 1m, 해제 +9m            | 감지 44m, 해제 +16m          | 감지 44m, 해제 +21m / 감지 2h55m, 해제 +5h45m
0.5% 오류 × 2일(번 5)                32.00%   33.33% | 감지 2m, 해제 +8m            | 안 울림                     | 안 울림 / 감지 12h00m, 해제 +5h00m
0.3% 오류 × 15분(작은 출렁임)             0.10%    0.10% | 감지 3m, 해제 +7m            | 안 울림                     | 안 울림 / 안 울림
```

- 관찰 1 — S1은 다 빨리 잡지만, 예산 0.10%만 쓴 작은 출렁임에도 울렸다(낮은 정밀도). 번 5인 사건에서는 이틀 내내 울린다.
- 관찰 2 — S4(1시간 창 하나)는 해제가 느리다. 10분 장애가 끝난 뒤 59분 더 울렸다. 번 5인 이틀짜리 사건(예산 약 33%)은 **아예 못 잡았다**(낮은 재현율).
- 관찰 3 — S6 page는 15% × 10분에서 6분에 울리고 끝난 뒤 4분에 멈췄다. Workbook 설명(긴 창이 5분 뒤 넘음, 끝난 뒤 5분에 멈춤)과 맞는다. 1분 해상도라 경계(5.76분)를 넘은 첫 분이 6분째다.
- 관찰 4 — 전면 장애에서 S6 page가 끝난 뒤 29분 더 울렸다. 1h&5m 쌍은 5분 뒤 내려갔지만 6h&30m 쌍이 30분 창을 다 비울 때까지 참이었다.
- 관찰 5 — 번 5 이틀짜리는 page가 울리지 않고 ticket이 12시간째에 잡았다. 설계 의도대로다. 번 6 미만은 업무 시간에 처리할 일로 본다. 대신 그 사이 예산 약 33%(평시 대비 추가 32%)가 나갔다. 사건이 끝난 뒤에도 6h 창에 오류가 남아 ticket은 5시간 더, S1은 8분 더 울렸다. Workbook 방법 6의 규칙 예에는 ticket 쌍 (24h & 2h > 번 3)도 있다. 이 시뮬레이션은 (3d & 6h > 1) 쌍만 넣었다.

### 6. 실험: 실제 PromQL 규칙을 promtool로 검증

- Workbook의 1h&5m 규칙과 1h 단독 규칙을 Prometheus 규칙 파일로 쓰고, `promtool test rules`에 합성 시계열을 넣었다.
- 입력: 분당 1000 요청, 120분째부터 10분 동안 전부 5xx, 그 뒤 정상. 각 시각에 "경보 없음"을 기대로 적어 두고, 실패 메시지로 실제 울린 경보를 읽었다.

```yaml
- alert: ErrorBudgetBurnFast
  expr: |
    job:slo_errors_per_request:ratio_rate1h{job="pay"} > (14.4*0.001)
    and
    job:slo_errors_per_request:ratio_rate5m{job="pay"} > (14.4*0.001)
- alert: ErrorBudgetBurn1hOnly
  expr: job:slo_errors_per_request:ratio_rate1h{job="pay"} > (14.4*0.001)
```

(실험, Prometheus 3.15.0 `promtool test rules`, 평가 간격 1분, 확인 시각 120·121·133·134·188·189분, 2026-10-01 — 아래는 그 시각에 울리고 있던 경보 목록)

```text
alertname: ErrorBudgetBurnFast, time: 2h1m
alertname: ErrorBudgetBurn1hOnly, time: 2h1m
alertname: ErrorBudgetBurnFast, time: 2h13m
alertname: ErrorBudgetBurn1hOnly, time: 2h13m
alertname: ErrorBudgetBurn1hOnly, time: 2h14m
alertname: ErrorBudgetBurn1hOnly, time: 3h8m
```

- 관찰: 두 규칙 모두 장애 1분째(2h1m)에 울렸다. 장애는 2h10m에 끝났다.
  - 다중 창 규칙: 2h13m까지 울리고 2h14m에는 없다 → 끝나고 약 4분 뒤 해제.
  - 1h 단독 규칙: 3h8m까지 울리고 3h9m에는 없다 → 약 58분 뒤 해제. Workbook 표 5-5의 "Reset time: 58 minutes"와 같은 값이다.

### 7. 트래픽이 적은 서비스

- 시간당 요청이 10개면 실패 1건이 시간당 오류율 10%다. 번 레이트 경보가 바로 울린다(Workbook 5장 "Low-Traffic Services").
- Workbook의 선택지: 인공 트래픽(프로버)으로 신호를 만든다, 작은 서비스를 묶어 한 단위로 본다, 실패 한 건의 영향을 줄이거나 실패로 셀 기준을 바꾼다.

### 8. 온콜 — 사람이 지속 가능한가

SRE 11장 "Being On-Call"의 수치다.

| 항목 | 내용 |
|---|---|
| 응답 시간 | 합의로 정한다. 흔한 값은 사용자 대면 5분, 덜 급한 시스템 30분 |
| 시간 비중 | 엔지니어링 최소 50%, 온콜 최대 25%, 나머지 운영 업무 최대 25% |
| 사건 한도 | 사건 하나 처리(원인 분석·완화·포스트모템·버그 수정)에 평균 6시간 → 12시간 교대당 최대 2건 |
| 분포 | 페이지는 시간에 고르게, 중앙값 0이 바람직 |
| 인원 | 1차·2차 동시 당번이면 한 사이트 최소 8명(주 단위 교대에 한 달 한 주) |

- 같은 장은 운영 과부하의 흔한 원인으로 **잘못 설정된 모니터링**을 꼽는다. 페이지 경보는 SLO를 위협하는 증상과 맞춰야 하고, 행동 가능해야 한다.
- 과부하의 측정 예: 교대당 페이지 수 < 2, 하루 티켓 < 5(SRE 11장 "Operational Overload").

## 쓰이는 자료구조·알고리즘

- **슬라이딩 윈도 비율** — 창 오류 수 / 창 요청 수. 시뮬레이션은 누적 합 두 번 빼기로 O(1)에 구했다. Prometheus는 `rate(x[1h])`. [algorithm/09-sliding-window](../../algorithm/09-sliding-window/2-summary.md) · [algorithm/10-prefix-sum](../../algorithm/10-prefix-sum/2-summary.md).
- **다중 창 AND / OR 결합** — 긴 창(양), 짧은 창(현재성), 여러 쌍의 OR(재현율).
- **경보 상태 기계** — inactive → pending(`for` 대기) → firing → (조건 거짓) → inactive. `keep_firing_for`로 해제를 늦출 수도 있다.
- **레이블 해시 그룹핑·중복 제거** — Alertmanager가 `group_by` 레이블 값으로 경보를 묶는다.
- **라우팅 트리** — Alertmanager `route`는 레이블 일치로 내려가는 트리다.
- **교대표(라운드 로빈)·에스컬레이션 대기열** — 1차가 응답하지 않으면 다음 단계로.

## 적용 — 풀어나가는 법

### 1. 순서

1. SLI·SLO를 먼저 정한다(02). 경보는 SLO를 지키는 도구다.
2. page는 증상 + 번 레이트를 기본으로 건다(위 표 5-8을 출발점으로).
3. 원인 지표(CPU·GC·큐)는 대시보드와 ticket으로. 단 매우 확실하고 임박한 원인(디스크가 몇 시간 안에 참, N+0 중복도)은 예외로 page.
4. page마다 런북 링크를 단다(44). 런북에 "확인 명령 → 완화 → 에스컬레이션"이 있다.
5. 경보 경로 자체를 감시한다: 계속 울리도록 만든 경보가 끊기면 다른 경로로 알린다(dead man's switch).
6. 분기마다 페이지 통계(교대당 사건 수, 행동 없이 닫힌 페이지 비율)를 보고 규칙을 줄이거나 고친다.

### 2. 규칙 (Prometheus, SRE Workbook 5장 방법 6)

```yaml
groups:
- name: slo-pay
  rules:
  - record: job:slo_errors_per_request:ratio_rate5m
    expr: sum by (job) (rate(http_requests_total{code=~"5.."}[5m])) / sum by (job) (rate(http_requests_total[5m]))
  # ratio_rate30m · 1h · 2h · 6h · 1d · 3d 도 같은 모양으로
  - alert: PayErrorBudgetBurn
    expr: |
        (job:slo_errors_per_request:ratio_rate1h{job="pay"} > (14.4*0.001)
         and job:slo_errors_per_request:ratio_rate5m{job="pay"} > (14.4*0.001))
      or
        (job:slo_errors_per_request:ratio_rate6h{job="pay"} > (6*0.001)
         and job:slo_errors_per_request:ratio_rate30m{job="pay"} > (6*0.001))
    labels: { severity: page }
    annotations:
      summary: "결제 API가 에러 버짓을 빠르게 소모 중"
      runbook_url: "https://runbooks.example.com/pay/error-budget-burn"
```

### 3. 묶기·억제 (Alertmanager, 설정 예)

```yaml
route:
  receiver: ticket-queue
  group_by: [alertname, job]
  routes:
    - matchers: [ severity="page" ]
      receiver: oncall-pager
inhibit_rules:
  - source_matchers: [ alertname="ClusterUnreachable" ]
    target_matchers: [ severity="page" ]
    equal: [ cluster ]
```

### 4. 경보를 코드로 시험하기

```bash
# 규칙 문법 검사와 단위 테스트 (위 실험과 같은 방식)
promtool check rules rules.yml
promtool test rules test.yml
```

## 장애 시나리오와 대처

### 1. 원인 기반 경보 남발 → 알람 피로로 진짜 장애를 놓침

- 현상: 밤마다 "CPU 80%", "GC 1초", "큐 100" page가 온다. 대부분 사용자 영향이 없다. 어느 날 진짜 결제 장애 page를 30분 늦게 봤다.
- 보이는 형태: 페이지 대부분이 행동 없이 닫힌다. 교대당 사건 수가 SRE 11장 한도(12시간당 2건)를 넘는다. 확인(ack)까지 걸리는 시간이 점점 길어진다.
- 원인: 원인 후보마다 page를 걸었다. 증상 없는 원인 경보는 정밀도가 낮다(SRE 6장 "Every page should be actionable").
- 대처: page는 증상·번 레이트를 기본으로(매우 확실하고 임박한 원인만 예외). 원인 경보는 ticket·대시보드로 내린다. 행동 없이 닫힌 page 비율을 정기적으로 보고 규칙을 지운다. 기계적 대응만 필요한 page는 자동화한다.

### 2. 짧은 창·고정 임계 경보가 출렁임마다 울린다

- 현상: 몇 분짜리 작은 오류 출렁임마다 page가 온다. 막상 깨서 보면 이미 끝났다.
- 보이는 형태: 위 실험의 S1 — 예산 0.10%만 쓴 0.3% × 15분에도 울림.
- 원인: 예산 소모량과 무관한 임계(10분 오류율 > SLO).
- 대처: 번 레이트 + 긴 창으로 "의미 있는 양을 썼을 때만" 울리게 한다(Workbook 방법 4~6).

### 3. 한 창 번 레이트만 → 느린 소모를 놓치고, 해제는 늦다

- 현상: 이틀 동안 오류율 0.5%가 이어져 월 예산의 3분의 1이 사라졌는데 page가 한 번도 없었다. 반대로 10분 장애가 끝난 뒤에도 경보가 한 시간 가까이 울려 "아직 안 끝났나" 혼란이 생겼다.
- 보이는 형태: 위 실험 S4 — 번 5 사건 "안 울림", 10분 장애 해제 +59m. promtool 실험에서 1h 단독 규칙은 끝난 뒤 약 58분 더 울렸다.
- 원인: 하나의 (창, 번 레이트)로는 빠른 소모와 느린 소모를 함께 잡을 수 없다. 긴 창 하나는 해제가 느리다.
- 대처: 여러 쌍의 OR(재현율) + 짧은 창 AND(해제 시간) — 방법 6.

### 4. 트래픽이 적은 시간·서비스에서 실패 한 건이 page

- 현상: 새벽에 요청이 거의 없을 때 실패 1~2건으로 page가 온다.
- 보이는 형태: 분모(요청 수)가 작은 시간대에 오류율이 10%·50%로 튄다.
- 원인: 비율 경보는 분모가 작으면 불안정하다(Workbook "Low-Traffic Services").
- 대처: 프로버로 인공 트래픽을 만든다. 작은 서비스를 묶어 본다. 최소 요청 수 조건(`and sum(rate(requests[1h])) > N`)을 더한다. 실패 한 건이 중요하면 경보가 아니라 건별 처리 절차로 다룬다.

### 5. 경보 경로가 죽었는데 아무도 모른다

- 현상: Prometheus·Alertmanager가 멈춘 동안 장애가 났고 page가 오지 않았다.
- 보이는 형태: 경보 이력이 그 기간 비어 있다. "조용한 밤"으로 보였다.
- 원인: 경보 시스템 자신을 감시하지 않았다. 경보가 없다는 것과 경보 시스템이 없다는 것을 구분하지 못했다.
- 대처: 계속 울리도록 만든 경보를 외부 서비스가 받게 하고, 그것이 끊기면 다른 경로로 알린다(dead man's switch). 경보 시스템을 이중화하고, 블랙박스 프로버를 다른 위치에서 돌린다.

## 핵심 문장

- page는 사람을 깨우는 비싼 신호다. 사용자가 겪는 증상에만 걸고, 행동할 수 있어야 한다. 원인은 대시보드와 ticket으로 보낸다.
- 번 레이트는 에러 버짓을 쓰는 속도다. "예산의 몇 %를 쓰면 깨운다"를 정하고 창과 번 레이트를 역산한다(1시간 2% → 14.4).
- 긴 창은 정밀도를, 짧은 창(1/12)은 빠른 해제를, 여러 쌍의 OR는 재현율을 준다. 실험에서 1시간 단독 규칙은 장애가 끝나고 약 58분 더 울렸고, 1h&5m 규칙은 약 4분 뒤 멈췄다.
- 한 창 경보는 느린 소모를 놓친다. 시뮬레이션에서 번 5 이틀짜리 사건(예산 약 33%)을 1시간 번 14.4 규칙은 잡지 못했다.
- 온콜은 사람의 용량이 한도다. SRE 11장은 12시간 교대당 사건 2건, 온콜 시간 25%를 상한으로 둔다.

## 관련 주제·근거

- 선행
  - [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) — SLI·SLO·에러 버짓·번 레이트 기초
  - [16-metrics-and-golden-signals](../16-metrics-and-golden-signals/2-summary.md) — 경보의 재료(골든 시그널·히스토그램)
- 후속·연결
  - [15-logging](../15-logging/2-summary.md) · [17-distributed-tracing](../17-distributed-tracing/2-summary.md) — 경보를 받은 뒤 조사
  - 원본 [systems/server-design/08-deployment-ops](../../systems/server-design/08-deployment-ops.md) §5 「알림 설계」 — 증상에 알림, 행동 가능한 알림, 버짓 소진 속도
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) — page 이후의 사고 지휘
  - [44-runbooks-and-operational-readiness](../44-runbooks-and-operational-readiness/2-summary.md) — 경보에 거는 런북
  - [33-hysteresis-and-flapping](../33-hysteresis-and-flapping/2-summary.md)
- 책·문서
  - Google SRE 책 6장 "Monitoring Distributed Systems" — 증상 vs 원인(표 6-1), page 원칙, Bigtable·Gmail 사례 <https://sre.google/sre-book/monitoring-distributed-systems/>
  - Google SRE 책 11장 "Being On-Call" — 응답 시간 5분/30분, 50%·25% 규칙, 사건당 6시간 → 12시간 교대당 2건, Operational Overload <https://sre.google/sre-book/being-on-call/>
  - Google SRE Workbook 5장 "Alerting on SLOs" — 정밀도·재현율·감지·해제, 방법 1~6, 표 5-4·5-6·5-8, 1/12 짧은 창, 저트래픽 서비스 <https://sre.google/workbook/alerting-on-slos/>
  - Prometheus "Alerting rules"(`for`·pending·`keep_firing_for`), Alertmanager 문서(Grouping·Inhibition·Silences, `group_wait` 30s·`group_interval` 5m·`repeat_interval` 4h)
- 실험 목록
  - A: 경보 규칙 S1·S4·S6 시뮬레이션 — 사건 5종의 감지·해제 시간과 버짓 소모(JDK 21.0.12, scratchpad `rel/15/Burn43.java`, 결정적. 2026-10-02 판정에서 평가 구간 9일·총소모 열을 더한 `rel/fa-36/Burn43.java`로 재실행 — 위 표가 그 출력)
  - B: Prometheus 3.15.0 `promtool test rules` — 10분 전면 장애에서 1h&5m 규칙 vs 1h 단독 규칙의 발화·해제 시각(scratchpad `rel/15/p43/rules.yml`·`test.yml`, 일회용 컨테이너)
