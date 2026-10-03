# testing/19-testing-in-production — 운영에서 하는 검증: 합성 모니터링·카나리 분석·섀도 트래픽 — 정리 (힌트)

## 해결하는 문제

배포 전 테스트는 테스트 환경에서 돈다. 운영에만 있는 것은 거기 없다.

```text
  테스트 환경에 없는 것                       그래서 생기는 일
  ─────────────────────────────            ─────────────────────────────────────────
  운영 설정·비밀값·피처 플래그 값              설정 누락 → 헬스 체크는 초록인데 결제만 실패
  운영 데이터의 모양·양                       테스트에 없던 입력(옛 레코드·특수 문자)에서 실패
  실제 트래픽 패턴·부하                        특정 시간대·특정 고객에게만 오류
  다른 팀의 실제 판들                          조합에서만 나는 오류
```

- SWE@G 14장: 운영은 "충실도가 가장 높은 테스트 환경"이다. 같은 장은 Google 대형 장애의 첫째 원인이 **설정 변경**이라고 적는다("Configuration changes are the number one reason for our major outages").
- 대가: 운영에서 잡은 문제는 "이미 사용자에게 영향을 주고 있다"(SWE@G 14장). 그래서 운영 검증은 **피해를 작게 만드는 장치**와 같이 쓴다.

쉬운 예: 새 메뉴를 식당에 내는 법.

- 주방에서 맛보기(배포 전 테스트)를 해도, 실제 손님 입맛·재료 상태는 다르다.
- 그래서 ① 직원이 손님인 척 주문해 보고(합성 모니터링) ② 몇 테이블에만 먼저 내고 반응을 기존 메뉴와 비교하고(카나리) ③ 주문이 들어오면 새 레시피로도 몰래 만들어 맛만 비교한다(섀도).

똑같은 구조다.\
운영 검증 = "운영에서만 보이는 결함"을 작은 노출로 먼저 보는 장치들이다.

실무 예:

- 배포 뒤 `/healthz`는 200인데 결제 API는 200 + `{"status":"ERROR"}` — 결제 게이트웨이 URL 설정이 빠졌다. 사용자 문의로 30분 뒤(예시) 안다(커리큘럼 ⚠ 칸 "운영 검증 없이 배포 → 테스트 환경에서 재현 안 되는 장애").

## 동작·원리

### 1. 세 가지 장치 — 무엇을 비교하나

```text
  ① 합성 모니터링(prober)        주기적으로 ──▶ [운영]  ── 응답을 "기대값"과 비교(단언)
     가짜 사용자 = 스크립트

  ② 카나리 분석                  실제 트래픽 ─┬─ 95% ─▶ [기준(baseline) 구판]  ─┐
                                           └─  5% ─▶ [카나리 신판]          ─┴─ 지표를 서로 비교(통계)

  ③ 섀도 트래픽(미러링)            실제 요청 ─┬────────▶ [구판] ── 응답 → 사용자
                                           └─ 복제 ─▶ [신판] ── 응답 버림, 구판과 비교(diff)
```

| | 무엇과 비교 | 사용자 노출 | 잡는 것 |
|---|---|---|---|
| 합성 모니터링 | 스크립트에 박힌 기대값 | 없음(가짜 사용자) | 핵심 여정이 깨졌나 |
| 카나리 분석 | 같은 시각의 기준 집단 | 일부 사용자 | 오류율·지연 회귀 |
| 섀도 트래픽 | 구판의 응답 | 없음(응답 버림) | 같은 입력에 다른 출력 |

- *합성 모니터링(synthetic monitoring)·prober*: SWE@G 14장 정의로 prober는 "운영 환경에 대해 단언을 실행하는 기능 테스트"다. 대개 "잘 알려진, 결정적인 읽기 전용 동작"을 한다.
- *카나리(canary)*: SRE Workbook 16장 정의로 "서비스 변경을 일부에, 시간을 정해 배포하고 평가하는 것". 배포 방식(가중치·단계)은 [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md)에서 다뤘다. 이 노트는 **판정**(테스트로서의 카나리)을 본다.
- *섀도 트래픽(shadow traffic)·미러링*: 실제 요청을 복제해 신판에도 보내고 응답은 버린다. SWE@G 14장의 "A/B diff 회귀 테스트"(같은 트래픽을 구·신판에 보내 응답을 비교)와 같은 생각이다.
  - nginx `mirror` 모듈: "미러 하위 요청의 응답은 무시된다."
  - Envoy 라우터 섀도잉: "fire and forget" — 섀도 클러스터 응답을 기다리지 않고, 섀도 요청의 Host 헤더에 `-shadow`를 붙인다.

### 2. 실험: 헬스 체크는 초록, 합성 여정 점검은 빨강

서버(Node)는 두 판이다. v2는 결제 게이트웨이 설정이 빠진 판이다. `/healthz`는 둘 다 200이다.

```js
if (req.url === '/healthz') return res.end('{"status":"UP"}');
if (req.url === '/api/checkout' && req.method === 'POST') {
  const body = V === 'v2' ? { status: 'ERROR', reason: 'payment gateway url not configured' } : { status: 'PAID', orderId: 'synthetic-1' };
  return res.end(JSON.stringify(body));     // 둘 다 HTTP 200
}
```

k6 합성 점검 — 헬스 체크와 "결제 여정"을 같이 돈다.

```js
export const options = { vus: 1, iterations: 5, thresholds: { checks: ['rate==1.0'] } };
export default function () {
  const h = http.get(`${BASE}/healthz`);
  check(h, { 'healthz 200': (r) => r.status === 200 });
  const c = http.post(`${BASE}/api/checkout`, JSON.stringify({ sku: 'SYNTHETIC-TEST', synthetic: true }),
                      { headers: { 'Content-Type': 'application/json', 'X-Synthetic': 'true' } });
  check(c, {
    'checkout 200': (r) => r.status === 200,
    'checkout PAID': (r) => r.json('status') === 'PAID',
  });
}
```

(실험, grafana/k6 1.2.3 · Node 22.23.2, 전용 Docker 네트워크, 2026-10-03)

```text
=== v1
k6 exit=0
    ✓ 'rate==1.0' rate=100.00%
    checks_succeeded...: 100.00% 15 out of 15
    ✓ healthz 200
    ✓ checkout 200
    ✓ checkout PAID
=== v2
k6 exit=99
    ✗ 'rate==1.0' rate=66.66%
    checks_succeeded...: 66.66% 10 out of 15
    checks_failed......: 33.33% 5 out of 15
    ✓ healthz 200
    ✓ checkout 200
    ✗ checkout PAID
      ↳  0% — ✓ 0 / ✗ 5
time="2026-10-03T12:44:21Z" level=error msg="thresholds on metrics 'checks' have been crossed"
```

- 관찰: v2에서 `healthz 200`과 `checkout 200`은 통과했다. **업무 결과를 본 단언**(`checkout PAID`)만 5/5 실패했다.
- k6 문서: 체크가 실패해도 스크립트는 계속 돌고 실패 종료 코드를 내지 않는다. 테스트 전체를 실패시키려면 체크를 **임계값(threshold)** 과 묶어야 한다. 실험에서 임계값을 걸자 종료 코드 99가 나왔다(k6 소스 `errext/exitcodes`: `ThresholdsHaveFailed = 99`).
- 해석: 헬스 체크는 "프로세스가 살아 있다"를, 합성 여정 점검은 "사용자가 일을 끝낼 수 있다"를 본다. 설정 누락처럼 프로세스는 멀쩡한 결함은 후자만 잡는다.

### 3. 실험: 카나리 판정 — 표본 크기와 판정 규칙

기준과 카나리에 각각 n건을 보내고 오류 확률을 정해 1,000번 반복했다(시드 고정 의사난수 mulberry32).

- 규칙 A(순진): 카나리 오류율 > 기준 오류율이면 실패.
- 규칙 B(통계): 단측 두 비율 z-검정, z > 1.645(유의수준 5%)이면 실패.

```js
function judge(n, pB, pC) {
  const eB = errors(n, pB), eC = errors(n, pC);
  const naive = eC / n > eB / n;
  const p = (eB + eC) / (2 * n), se = Math.sqrt(p * (1 - p) * 2 / n);
  const z = se === 0 ? 0 : (eC / n - eB / n) / se;
  return { naive, stat: z > 1.645 };
}
```

(실험, Node 22.23.2, 시드 42, 2026-10-03)

```text
n/group  pB     pC     naiveFAIL  zFAIL
200      0.01   0.01    40.7%      5.5%
200      0.01   0.02    71.4%     23.7%
2000     0.01   0.01    46.3%      4.7%
2000     0.01   0.02    99.7%     83.0%
20000    0.01   0.01    50.3%      5.5%
20000    0.01   0.02   100.0%    100.0%
```

시드 7로 다시 돌린 값: n=200 같은 판 6.5%·두 배 25.3%, n=2000 5.3%·82.9%, n=20000 4.7%·100.0%. 순진 규칙의 같은 판 실패율은 41.2~52.5%.

- 같은 판끼리(pC = pB)인데 순진 규칙은 40~53%를 "실패"로 판정했다 — 우연한 차이를 회귀로 본다.
- 통계 규칙은 같은 판에서 약 5%(설계한 거짓 경보율)를 유지했다.
- 오류율이 두 배(1% → 2%)인 나쁜 판을 잡는 비율은 표본에 달렸다: 그룹당 200건이면 약 4분의 1, 2,000건이면 약 83%, 20,000건이면 100%.
- 해석: 카나리를 짧게·적은 트래픽으로 돌리면 나쁜 판을 놓친다. 판정 규칙이 순진하면 좋은 판을 자주 막는다. SRE Workbook 16장이 카나리 크기·기간을 트레이드오프로 다루고, Spinnaker 문서가 지표당 시계열 데이터 50개 이상(대개 여러 시간)을 권하는 이유가 이것이다.
- 이 실험의 z-검정은 단순화한 판정이다. 그룹당 200건·오류 1%면 기대 오류 수가 2건이라 정규 근사가 거칠다(같은 판 거짓 경보가 5.5~6.5%로 5%를 조금 넘은 것도 이 영향일 수 있다 — 해석). 실제 도구(Kayenta의 NetflixACAJudge)는 지표마다 Mann-Whitney U 검정(분포 가정 없음)으로 Pass·High·Low를 분류하고, 통과 지표 비율로 점수를 매긴다(Spinnaker 문서).

### 4. 실험: 섀도 비교 — 차이는 잡지만 부수 효과는 두 배

구판(`Math.round`)과 리팩터링한 신판(`Math.floor` — 의도는 "결과 같음")에 기록된 요청 10,000건을 재생했다.

```js
const v1 = (r, fx) => { const p = Math.round(r.unit * r.qty * (100 - r.couponPct) / 100); fx(); return p; };
const v2 = (r, fx) => { const p = Math.floor(r.unit * r.qty * (1 - r.couponPct / 100)); fx(); return p; };
...
const a = v1(r, sendReceipt);                                   // 사용자 응답
const b = v2(r, shadowEffects ? sendReceipt : () => {});        // 섀도 응답은 버리고 비교만
```

(실험, Node 22.23.2, 2026-10-03)

```text
shadow side effects stubbed : {"requests":10000,"diff":591,"mails":10000,"sample":{"unit":990,"qty":1,"couponPct":15,"v1":842,"v2":841}}
shadow side effects NOT stubbed: {"requests":10000,"diff":591,"mails":20000,"sample":{"unit":990,"qty":1,"couponPct":15,"v1":842,"v2":841}}
```

- 섀도 비교가 10,000건 중 591건의 차이를 찾았다. 예: 990원 × 1개 × 15% 할인 → 구판 842, 신판 841(반올림 vs 버림).
- 섀도 쪽 부수 효과(영수증 메일)를 막지 않자 메일이 10,000 → 20,000건이 됐다. 섀도는 응답만 버릴 뿐 **신판이 한 일은 그대로 일어난다.** 결제·메일·쓰기는 섀도에서 막아야 한다.

## 쓰이는 자료구조·알고리즘

- **두 표본 검정** — 카나리 vs 기준의 오류율 차이가 우연인지 본다. 비율이면 z-검정, 분포를 가정하지 않으려면 Mann-Whitney U(순위 합). 표본 크기와 검출력(나쁜 판을 잡을 확률)의 관계가 실험 3의 표다. 통계 기초는 data-analysis 09 hypothesis-testing·10 power-and-sample-size — 미작성([data-analysis 영역 표](../../data-analysis/README.md)).
- **차등 비교(diff)** — 같은 입력에 대한 두 출력을 비교한다. 출력에 시각·난수·ID처럼 원래 다른 필드가 있으면 비교 전에 걸러야 한다(정규화).
- **주기 실행 + 임계값** — 합성 점검은 스케줄러가 돌리는 결정적 스크립트다. 단언 결과를 지표(체크 성공률)로 모으고 임계값으로 알림을 낸다.
- **트래픽 분할** — 가중치 라우팅(카나리), 요청 복제(섀도). [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md)의 가중 라운드로빈.

## 적용 — 풀어나가는 법

### 1. 순서

1. **합성 점검부터**: 핵심 여정(로그인·조회·결제 시도)을 읽기 위주의 결정적 스크립트로 만들고, 배포 직후와 주기적으로 돌린다. 업무 결과를 단언한다(HTTP 200만 보지 않는다).
2. **카나리 판정**: 같은 시각·같은 크기의 기준 집단과 비교한다. 지표는 변경에 귀속되는 소수(SRE Workbook: "많아야 열두 개 정도")로 고른다. 판정은 통계 규칙으로, 표본이 모자라면 기간을 늘린다.
3. **섀도·A/B diff**: 읽기 위주 엔드포인트, 계산 로직 리팩터링에 쓴다. 쓰기·외부 호출은 섀도에서 막는다.
4. 각 단계에 **되돌림 조건**을 미리 적는다(체크 실패율, 카나리 점수).

### 2. 합성 점검의 테스트 데이터 규칙

- 테스트 계정·상품을 따로 두고 표시한다(`X-Synthetic: true`, `sku: SYNTHETIC-TEST`). 집계·청구·추천에서 걸러낸다.
- SWE@G 14장의 Webdriver Torso 사례: 유튜브 운영의 영상 처리를 확인하려고 테스트 영상을 자동 업로드하는 채널을 만들었는데, 그 채널이 공개되어 Wired 기사로 퍼졌다. 운영에 넣은 테스트 데이터는 밖에서 보일 수 있다.

### 3. 카나리 비교 대상 (Java로 쓴 판정 골격)

```java
record Counts(long requests, long errors) {
  double rate() { return (double) errors / requests; }
}

/** 단측 두 비율 z-검정. true면 카나리가 기준보다 나쁘다고 판정 */
static boolean canaryWorse(Counts baseline, Counts canary, double zCritical) {
  long n1 = baseline.requests(), n2 = canary.requests();
  double p = (double) (baseline.errors() + canary.errors()) / (n1 + n2);
  double se = Math.sqrt(p * (1 - p) * (1.0 / n1 + 1.0 / n2));
  if (se == 0) return false;
  return (canary.rate() - baseline.rate()) / se > zCritical;   // 예: 1.645 = 단측 5%
}
```

- 비교 대상은 **운영 전체 집단이 아니라 같은 크기·같은 시각에 새로 띄운 기준 집단**이다(Spinnaker 문서: 캐시 예열·힙 크기 같은 환경 차이를 통제).
- 배포 전후(before/after) 비교는 시간대 차이가 섞여 SRE Workbook 16장이 경고한다.

### 4. 섀도 설정 (nginx 문서 기준)

```nginx
location / {
    mirror /mirror;              # 원 요청을 복제
    proxy_pass http://v1;        # 사용자 응답은 v1
}
location = /mirror {
    internal;
    proxy_pass http://v2$request_uri;   # v2 응답은 무시된다
}
```

- 응답은 버려지므로 비교는 양쪽 로그(요청 ID 기준)를 모아 따로 한다.

## 장애 시나리오와 대처

### 1. ⚠ 운영 검증 없이 배포 → 테스트 환경에서 재현 안 되는 장애

- 현상: 배포 직후 결제가 안 된다는 고객 문의. 대시보드의 헬스 체크·5xx 비율은 정상.
- 보이는 형태: HTTP 200 + 본문 `{"status":"ERROR","reason":"payment gateway url not configured"}`.
- 원인: 운영 설정 누락. 테스트 환경에는 그 값이 있었다. 헬스 체크는 프로세스 생존만 봤다.
- 대처: 업무 결과를 단언하는 합성 점검을 배포 단계에 넣고, 임계값 실패 시 배포를 멈춘다(실험: v2에서 `checkout PAID` 0/5, k6 종료 코드 99).

### 2. 카나리가 통과했는데 전체 배포에서 터진다

- 현상: 카나리 단계 초록, 100% 뒤 오류율 상승.
- 원인: 카나리 표본이 작아 검출력이 낮았다(실험: 그룹당 200건이면 오류율 두 배인 판을 약 4분의 1만 잡음). 또는 트래픽이 적은 시간대였다.
- 대처: 표본·기간을 늘리고 통계 판정을 쓴다. 운영 측면의 대처는 [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) 장애 5.

### 3. 카나리가 좋은 판을 자꾸 막는다

- 현상: 변경과 무관해 보이는데 카나리 실패가 잦아 팀이 판정을 건너뛰기 시작한다.
- 원인: "카나리 오류율 > 기준 오류율" 같은 순진한 규칙(실험: 같은 판끼리 40~53% 실패). 지표가 많을수록 우연히 하나쯤 나빠질 확률이 커진다.
- 대처: 통계 판정, 지표를 변경에 귀속되는 소수로 줄인다.

### 4. 섀도 트래픽이 실제 부수 효과를 일으킨다

- 현상: 고객이 영수증 메일을 두 통 받았다. 외부 결제사 호출이 두 배.
- 원인: 섀도 판이 메일·결제·DB 쓰기를 그대로 실행했다(실험: 메일 10,000 → 20,000).
- 대처: 섀도 판에서 쓰기·외부 호출을 막거나 가짜로 바꾼다. 읽기 위주 경로에만 섀도를 쓴다.

### 5. 합성 테스트 데이터가 사용자·지표에 섞인다

- 현상: 매출 집계에 테스트 주문, 추천에 테스트 상품, 외부에 테스트 콘텐츠 노출.
- 원인: 합성 요청을 표시·필터하지 않았다(Webdriver Torso 사례처럼 공개될 수도 있다).
- 대처: 전용 계정·표시 헤더, 집계 단계 필터, 생성한 데이터 정리 작업.

## 핵심 문장

- 운영은 충실도가 가장 높은 테스트 환경이지만, 거기서 잡은 결함은 이미 사용자에게 닿았을 수 있다 — 그래서 노출을 줄이는 장치와 함께 쓴다.
- 합성 점검은 업무 결과를 단언해야 한다. 실험에서 설정이 빠진 판은 헬스 체크와 HTTP 200을 통과하고 `checkout PAID`만 5/5 실패했다.
- k6의 체크는 실패해도 종료 코드를 바꾸지 않는다. 임계값과 묶어야 배포를 멈출 수 있다(실험에서 종료 코드 99).
- 카나리 판정은 같은 시각의 기준 집단과 통계로 비교한다. 실험에서 순진한 규칙은 같은 판도 40~53% 막았고, 그룹당 200건으로는 오류율 두 배인 판을 약 4분의 1만 잡았다.
- 섀도는 같은 입력에 대한 출력 차이를 찾지만(실험 591/10,000), 응답만 버릴 뿐 부수 효과는 그대로 일어난다.

## 관련 주제·근거

- 선행
  - [reliability/23-deployment-strategies](../../reliability/23-deployment-strategies/2-summary.md) — 카나리·롤링·블루그린의 배포 방식과 공존 구간.
  - [18-e2e-and-ui-testing](../18-e2e-and-ui-testing/2-summary.md) — 합성 점검은 운영에서 도는 E2E다.
  - [13-contract-testing](../13-contract-testing/2-summary.md) — 배포 전 서비스 사이 호환 확인.
- 후속·연결
  - [reliability/24-feature-flag-lifecycle](../../reliability/24-feature-flag-lifecycle/2-summary.md) — 플래그로 노출 범위를 좁히는 다크 런치.
  - [reliability/45-chaos-and-resilience-testing](../../reliability/45-chaos-and-resilience-testing/2-summary.md) — 운영에서 하는 또 다른 실험.
  - [reliability/02-slo-sli-error-budget](../../reliability/02-slo-sli-error-budget/2-summary.md), [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md), [reliability/43-alerting-and-on-call](../../reliability/43-alerting-and-on-call/2-summary.md)
  - [20-test-symptom-index](../20-test-symptom-index/2-summary.md), [21-test-incidents](../21-test-incidents/2-summary.md).
- 교재·문서
  - SWE@G 14장 "Larger Testing" — Fidelity(운영 = 최고 충실도), Configuration issues, A/B Diff Regression Testing, Probers and Canary Analysis, Webdriver Torso 사례, Verification(수동·단언·A/B 비교) <https://abseil.io/resources/swe-book/html/ch14.html>
  - Google SRE Workbook 16장 "Canarying Releases"(Warner·Davidovič 외) — 정의, 지표 선택(귀속·소수), 크기·기간 트레이드오프, before/after 비교 경고 <https://sre.google/workbook/canarying-releases/>
  - Spinnaker 문서 — Canary Best Practices(같은 시각·같은 크기 기준 집단, 지표당 50개 이상 시계열) <https://spinnaker.io/docs/guides/user/canary/best-practices/>, How the NetflixACAJudge works(Mann-Whitney U, Pass·High·Low, 점수) <https://spinnaker.io/docs/guides/user/canary/judge/>
  - k6 문서 — Checks(실패해도 종료 상태를 바꾸지 않음, 임계값과 결합) <https://grafana.com/docs/k6/latest/using-k6/checks/>, k6 소스 `errext/exitcodes/codes.go`(`ThresholdsHaveFailed = 99`) <https://github.com/grafana/k6>
  - nginx `ngx_http_mirror_module`(1.13.4, 미러 응답 무시) <https://nginx.org/en/docs/http/ngx_http_mirror_module.html>, Envoy route `request_mirror_policies`(fire and forget, `-shadow`) <https://www.envoyproxy.io/docs/envoy/latest/api-v3/config/route/v3/route_components.proto>
- 실험 목록
  - `server.js` + `probe.js` — Node 서버 v1/v2(설정 누락)에 k6 1.2.3 합성 점검(`healthz 200`·`checkout 200`·`checkout PAID`, 임계값 `checks rate==1.0`). 전용 Docker 네트워크, 2026-10-03.
  - `canary.js` — 두 비율 판정 시뮬레이션(n = 200·2,000·20,000, pB 0.01, pC 0.01·0.02, 1,000회, 시드 42·7).
  - `shadow.js` — 기록 요청 10,000건 재생, 구판 round vs 신판 floor 차이, 섀도 부수 효과 차단 유무.
