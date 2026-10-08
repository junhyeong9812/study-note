# ai-engineering/13-model-routing-and-fallback — 모델 라우팅과 폴백: LLM 게이트웨이, 비용 라우팅·캐스케이드, 서킷 브레이커, 폴백 모델의 계약 차이 — 정리 (힌트)

## 해결하는 문제

LLM 호출을 모델 하나·제공자 하나에 직접 묶으면 세 가지가 동시에 어렵다.

```text
  앱 ──▶ 제공자 A 모델 X  (하나뿐)
         ├ A가 장애·과부하(529·503·429)면 기능 전체가 멈춘다
         ├ 쉬운 요청도 비싼 모델로 간다 — 비용
         └ 모델을 바꾸려면 앱 코드·프롬프트·파서를 같이 바꿔야 한다
```

- FrugalGPT(Chen 외 2023) 초록: 유료 LLM API들의 가격 구조가 제각각이고, 요금 차이가 두 자릿수 크기(order of magnitude 둘, 약 100배)까지 날 수 있다.
- 그래서 요청마다 **어느 모델로 보낼지**(라우팅), 실패하면 **어디로 돌릴지**(폴백), 망가진 곳에 **언제 그만 보낼지**(서킷 브레이커)를 한곳에서 정한다.
  - *LLM 게이트웨이*: 앱과 LLM 제공자 사이에서 라우팅·폴백·재시도·한도·기록을 맡는 계층. 라이브러리일 수도, 별도 프록시 서비스일 수도 있다.

쉬운 예: 콜센터다.
- 간단한 문의는 일반 상담원, 어려운 문의는 전문 상담원에게 보낸다(라우팅).
- 일반 상담원이 못 풀면 전문 상담원에게 넘긴다(캐스케이드).
- 한 센터가 정전이면 다른 센터로 돌린다(폴백). 정전 센터에 계속 전화를 거는 것은 멈춘다(서킷 브레이커).
- 다른 센터는 매뉴얼이 조금 달라 답변 양식이 다를 수 있다(폴백 모델의 형식 차이).

똑같은 구조다.\
게이트웨이는 API 게이트웨이와 같은 자리에 서지만([api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md)), 하류가 **비결정적이고 형식이 서로 다른 모델**이라는 점이 다르다.

백엔드 실무 예: 고객 문의 분류는 작은 모델, 환불 판단 근거 작성은 큰 모델로 보낸다. 주 제공자가 과부하일 때 다른 제공자의 모델로 넘긴다.

## 동작·원리

### 1. 게이트웨이 안의 흐름

```text
  요청(기능 = "refund-note", 테넌트, 입력 토큰 추정)
    │
    ▼
  [라우터] 규칙·가중·난이도로 후보 순서 결정 ── 결정 기록(요청 모델, 이유)
    │  후보: [A/모델X, B/모델Y]
    ▼
  [서킷 A/X] 열림? ──예──▶ 다음 후보로
    │ 닫힘·반열림
    ▼
  [호출 A/X] ── 성공 ──▶ [출력 검증(14)] ── 통과 ──▶ 응답 + 기록(응답 모델, 폴백 여부, 시도 수)
    │ 실패(529·503·429 일시·타임아웃·스트림 오류)          └ 실패 ──▶ 재요청 1회 또는 다음 후보
    ▼
  [서킷에 실패 기록] ──▶ 재시도 예산 남음? ──▶ 같은 후보 재시도 / 다음 후보(B/Y)
```

- 결과 검증(14)이 게이트웨이 **안**에 있어야 한다. 폴백 모델의 출력은 주 모델과 형식이 다를 수 있기 때문이다(§3).
- 오류 분류(재시도할 것·말 것)는 [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md)가 정한다.

### 2. 라우팅 방식 셋

| 방식 | 어떻게 고르나 | 쓰는 곳 |
|---|---|---|
| 규칙 | 기능·테넌트·입력 길이로 고정 | "요약은 모델 Y", "긴 문서는 문맥 창 큰 모델" |
| 가중 무작위 | 가중치 비율로 무작위(사용자 해시로 고정 가능) | 새 모델 카나리 5%, A/B 비교 |
| 난이도·비용 | 라우터 모델이 강·약 모델 중 선택, 또는 싼 모델부터 시도(캐스케이드) | 쉬운 요청이 많은 기능의 비용 절감 |

- *라우터(학습형)*: RouteLLM(Ong 외 2024)은 강한 모델과 약한 모델 사이에서 요청마다 고르는 라우터를 사람 선호 데이터로 학습했다. 초록: 일부 경우 응답 품질을 해치지 않고 비용을 2배 넘게 줄였고, 시험 때 강·약 모델을 바꿔도 성능이 유지됐다.
- *캐스케이드(cascade)*: 싼 모델의 답을 먼저 받고, 판정기가 믿을 만하지 않다고 하면 더 비싼 모델로 넘긴다. FrugalGPT는 질의마다 어떤 모델 조합을 쓸지 학습하는 캐스케이드로, 초록에서 최고 단일 모델(예: GPT-4) 성능을 최대 98% 비용 절감으로 맞췄다고 보고한다.

```text
  캐스케이드 기대 비용 (식)
  E[비용] = c_싼 + p_승격 × c_비싼
  예시: c_싼 = 1, c_비싼 = 20, p_승격 = 0.3  →  1 + 0.3 × 20 = 7   (비싼 모델만: 20)
        p_승격 = 0.95 →  1 + 19 = 20    ← 비싼 모델만 쓴 것과 같다(절감 0). 0.95를 넘으면 오히려 손해
  지연도 같은 꼴: 승격된 요청은 두 번 기다린다
```

- 비용 절감 수치는 논문의 데이터·모델에서 나온 것이다. 자기 서비스에서의 효과는 평가셋으로 다시 재야 한다([19-llm-evaluation](../19-llm-evaluation/2-summary.md)).

### 3. 폴백 — 다른 모델은 같은 계약을 지키지 않는다

```text
  주 모델에서 통과하던 요청이 폴백 모델로 가면 달라질 수 있는 것
  ┌─────────────────────┬──────────────────────────────────────────────────────┐
  │ 토크나이저           │ 같은 프롬프트의 토큰 수·비용이 다르다 (04)              │
  │ 문맥 창·출력 한도     │ 주 모델에서 들어가던 긴 입력이 거절되거나 잘린다         │
  │ 구조화 출력 지원 범위 │ 스키마 키워드 지원이 다르다 (14)                         │
  │ 도구 호출 형식        │ tool_use 블록 vs tool_calls 배열 (14)                   │
  │ 중단 사유 이름        │ max_tokens vs length vs incomplete (11)                │
  │ 프롬프트 캐시         │ 캐시가 차갑기 쉽다 → 적중이 낮으면 비용·TTFT 증가 (12)   │
  │ 한도·과금 단위        │ RPM·TPM 계산 방식이 다르다 (11)                         │
  └─────────────────────┴──────────────────────────────────────────────────────┘
```

- 구조화 출력 예(2026-10-08 확인): Anthropic Structured outputs 문서는 숫자 범위(`minimum`·`maximum`)·문자열 길이 제약을 지원하지 않는다고 적는다. OpenAI Structured Outputs 가이드는 `minimum`·`maximum`을 지원 목록에 둔다(미세조정 모델은 미지원). 한쪽에서 API가 막아 주던 범위 검사를 다른 쪽에서는 앱이 해야 한다.
- 폴백은 평소에 거의 안 쓰인다. 그래서 차이가 **장애 때만** 드러난다. 폴백 경로도 주 경로와 같은 계약 테스트를 정기적으로 돌린다.

### 4. 서킷 브레이커 — LLM 호출에서 무엇을 실패로 세나

- 상태 기계(닫힘 → 열림 → 반열림)와 창 계산은 [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)가 단일 출처다.
- LLM 호출에서 실패로 셀 것과 세지 않을 것

| 결과 | 실패로 셀까 | 이유 |
|---|---|---|
| 529·503 과부하, 500, 연결 실패, 첫 토큰 타임아웃 | 센다 | 제공자 쪽 문제 |
| 200 뒤 스트림 안 과부하 오류 | 센다 | 상태 코드는 200이지만 제공자 문제([11](../11-llm-api-client-contract/2-summary.md)) |
| 429 일시 한도 | 따로 센다 | 제공자는 멀쩡하고 **내 한도**가 찼다. 회로보다 클라이언트 쪽 한도 조절이 맞다 |
| 400·413, 거부(refusal), 스키마 위반 | 세지 않는다 | 요청이나 출력 내용 문제다. 세면 멀쩡한 제공자를 끊는다 |

- 회로는 제공자 + 모델(+ 리전) 단위로 둔다. 같은 제공자라도 모델마다 과부하가 따로 온다.

### 5. 재시도 층 중첩

```text
  사용자 요청 1건
   └ 게이트웨이 재시도 2회 시도
       └ 앱 재시도 3회 시도
           └ SDK 자동 재시도 (Anthropic SDK 기본: 실패 후 2회 → 3회 시도)
  전면 장애면 제공자 호출 = 3 × 3 × 2 = 18회
```

- 공식 SDK도 재시도한다(2026-10-08 확인): Anthropic SDK는 연결 오류·429·5xx를 기본 2회 재시도하고, Gemini Python SDK는 일시 오류를 최대 4회 재시도한다(문서 "Troubleshooting"). OpenAI 문서는 앱에서 재시도를 관리하면 SDK 재시도를 끄거나 한도에 합산하라고 적는다.
- 계층마다 곱해지는 원리와 재시도 예산은 [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)가 단일 출처다.

### 실험: 재시도 증폭과 라우터·서킷·폴백 상태 기계

Python 표준 라이브러리 모형이다. 제공자 A(주)·B(폴백)는 가상이고 수치는 예시다.

```python
def with_retry(fn, attempts):          # 층 하나 = 시도 횟수 attempts
    def wrapped(down):
        for _ in range(attempts):
            if fn(down):
                return True
        return False
    return wrapped

stack = with_retry(with_retry(with_retry(provider, sdk), app), gw)

# 라우터: 서킷이 허용하면 A, 아니면(또는 A 실패면) B
if (not use_breaker) or br.allow(t):
    ok = (not a_down) and rnd.random() > 0.01        # 평소 A 실패율 1%
    if use_breaker: br.record(ok, t)
    if ok: served, outcome = 'A', 'ok'
if served is None:                                   # 폴백 B는 스키마 검증 실패 8%(예시)
    served = 'B'; outcome = 'parse_fail' if rnd.random() < 0.08 else 'ok'
log.append((t, served, outcome))                     # 응답한 모델을 기록한다
```

서킷: 최근 20건 중 실패 50% 이상이면 열림, 50건 동안 즉시 거절, 반열림 시험 5건. 요청 1,000건 중 t=300~599 동안 A 전면 장애, 시드 7·8·9.

(실험, python:3.12-slim Python 3.12.14, `--network none --cpus=2`, 2026-10-08)

```text
[A] 제공자 전면 장애 때 사용자 요청 1건이 만드는 제공자 호출 수
  SDK 시도 1 × 앱 시도 1 × 게이트웨이 시도 1 → 1회
  SDK 시도 3 × 앱 시도 1 × 게이트웨이 시도 1 → 3회
  SDK 시도 3 × 앱 시도 3 × 게이트웨이 시도 1 → 9회
  SDK 시도 3 × 앱 시도 3 × 게이트웨이 시도 2 → 18회
  SDK 시도 1 × 앱 시도 3 × 게이트웨이 시도 1 → 3회
[B] 요청 1000건, t=300~599 동안 A 전면 장애, 폴백 B의 파싱 실패율 8%(예시)
  seed 7 브레이커 없음: A 호출 1000(장애 중 실패 300), 파싱 실패율 장애 전 0.0% · 장애 중 10.3% · 장애 후 0.0%
    모델별 집계 {('A', 'ok'): 693, ('B', 'ok'): 276, ('B', 'parse_fail'): 31}
  seed 7 브레이커 있음: A 호출 700(장애 중 실패 35), 파싱 실패율 장애 전 0.0% · 장애 중 10.3% · 장애 후 0.2%
    모델별 집계 {('A', 'ok'): 658, ('B', 'ok'): 310, ('B', 'parse_fail'): 32}
    상태 전이 [(309, 'CLOSED', 'OPEN'), (359, 'OPEN', 'HALF_OPEN'), (364, 'HALF_OPEN', 'OPEN'), (414, 'OPEN', 'HALF_OPEN'), (419, 'HALF_OPEN', 'OPEN'), (469, 'OPEN', 'HALF_OPEN'), (474, 'HALF_OPEN', 'OPEN'), (524, 'OPEN', 'HALF_OPEN'), (529, 'HALF_OPEN', 'OPEN'), (579, 'OPEN', 'HALF_OPEN'), (584, 'HALF_OPEN', 'OPEN'), (634, 'OPEN', 'HALF_OPEN'), (639, 'HALF_OPEN', 'CLOSED')]
  seed 8 브레이커 없음: A 호출 1000(장애 중 실패 300), 파싱 실패율 장애 전 0.0% · 장애 중 4.7% · 장애 후 0.0%
  seed 8 브레이커 있음: A 호출 700(장애 중 실패 35), 파싱 실패율 장애 전 0.0% · 장애 중 4.7% · 장애 후 0.5%
  seed 9 브레이커 없음: A 호출 1000(장애 중 실패 300), 파싱 실패율 장애 전 0.0% · 장애 중 9.7% · 장애 후 0.2%
  seed 9 브레이커 있음: A 호출 700(장애 중 실패 35), 파싱 실패율 장애 전 0.0% · 장애 중 9.7% · 장애 후 0.5%
```

- [A] 층마다 시도 횟수가 곱해진다. SDK 3 × 앱 3 × 게이트웨이 2 = 18회. 재시도를 한 층(앱 3회)에만 두면 3회다.
- [B] 파싱 실패는 **장애 중에 몰렸다**(4.7~10.3%). 장애 후에도 0.0~0.5%가 남았는데, 이유는 아래 "대가"에 적었다. 전체 집계만 보면 원인이 안 보이지만, 응답 모델별로 모으면 실패가 모두 B에서 나왔다(seed 7: B 307건 중 31건, A 0건).
- 서킷이 있으면 장애 중 A로 간 실패 호출이 300 → 35건으로 줄었다. 실제 서비스라면 그 300번이 각각 타임아웃 대기였다.
- 대가도 보인다. 장애가 t=600에 끝났지만 회로는 t=639에야 닫혔다. 그동안 요청이 B로 가서 "장애 후" 파싱 실패율이 0.2~0.5%로 남았다(브레이커 없이도 A의 평소 실패 1%가 B로 넘어가 0.0~0.2%는 생긴다). 열림 유지 시간이 길수록 폴백에 오래 머문다.

### 6. 라우팅 결정을 기록한다

- 요청할 때 지정한 모델과 실제로 응답한 모델을 둘 다 남긴다. OpenTelemetry GenAI 규약에는 `gen_ai.request.model`과 `gen_ai.response.model`이 따로 있다(상태 Development, 2026-10-08 확인).
- 같이 남길 것: 라우팅 이유(규칙·가중·캐스케이드 승격), 폴백 여부, 시도 번호, 제공자·리전.
- 해석: 사용자를 같은 경로로 고정하는(sticky) 라우팅은 문제를 일부 사용자에게 몰아준다. Anthropic의 2025-09-17 사후 분석은 문맥 창 라우팅 오류에서 라우팅이 sticky라 잘못된 서버로 간 사용자의 후속 요청도 같은 서버로 갔다고 적는다. 경로별로 품질 지표를 나눠 보지 않으면 "일부 사용자만 이상하다"는 신고가 원인과 이어지지 않는다.

## 쓰이는 자료구조·알고리즘

- **가중 무작위 선택** — 가중치 누적합을 만들고 `[0, 합)`의 난수가 떨어지는 칸을 고른다. 사용자 고정이 필요하면 난수 대신 사용자 ID 해시를 쓴다([math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md), [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md)).
- **캐스케이드** — 조건부 순차 호출. 판정기 점수 ≥ 임계면 멈추고, 아니면 다음 모델.
- **서킷 브레이커 상태 기계 + 개수 기반 창** — 최근 N건 결과를 원형 배열로 유지한다([reliability/10](../../reliability/10-circuit-breaker/2-summary.md), [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md)).
- **재시도 예산** — 전체 중 재시도 비율의 상한([reliability/06](../../reliability/06-retry-backoff-jitter/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 게이트웨이 코드의 뼈대 (Java 21)

```java
record Candidate(String provider, String model) {}
record RouteDecision(String feature, List<Candidate> order, String reason) {}
record Served(Candidate by, int attempt, boolean fallback, LlmResult result) {}

Served call(Request req) {
    RouteDecision d = router.decide(req);                  // 규칙·가중·캐스케이드
    int attempt = 0;
    for (int i = 0; i < d.order().size(); i++) {
        Candidate c = d.order().get(i);
        CircuitBreaker cb = breakers.get(c);                // 제공자 + 모델 단위
        if (!cb.tryAcquirePermission()) continue;           // 열림 → 다음 후보
        attempt++;
        LlmResult r = clients.get(c.provider()).call(c.model(), req, deadline);   // SDK 재시도는 끔
        cb.onResult(countsAsFailure(r));                    // 429·400·거부는 세지 않음(§4)
        if (r instanceof Completed done && validator.accepts(done)) {            // 폴백 출력도 같은 검증
            Served s = new Served(c, attempt, i > 0, r);
            log.info("llm route feature={} requested={} served={} reason={} fallback={} attempt={}",
                    d.feature(), d.order().get(0).model(), c.model(), d.reason(), i > 0, attempt);
            return s;
        }
        if (!retryableAcrossCandidates(r)) break;           // 잘못된 요청(400)은 다른 모델로 돌려도 같다. 거부는 정책에 따라(아래)
    }
    throw new LlmUnavailableException(d.feature());
}
```

- 재시도는 한 층(여기서는 게이트웨이의 후보 순회)에서만 하고, SDK 자동 재시도는 끈다(OpenAI 문서 권고와 같은 이유).
- 400은 다른 후보로 돌리지 않는다. 요청 형식·내용 문제는 모델을 바꿔도 대개 그대로다.
- 거부(refusal)는 400과 따로 다룬다. Anthropic "Stop reasons and fallback"(2026-10-08 확인)은 `refusal`이면 `stop_details`를 읽고 다른 모델로 재시도하라고 안내하고, 일부 모델의 거부는 다른 Claude 모델로 재시도하면 대개 처리된다고 적는다. 같은 모델 재시도는 의미가 적다. 다른 모델로 돌릴지는 서비스 정책과 거부 사유로 정한다.

### 2. 폴백 경로 점검표

```text
  [ ] 폴백 모델에 같은 계약 테스트(스키마·도구·중단 사유 처리)를 매일 돌린다
  [ ] 폴백 모델의 문맥 창·출력 한도로 주 경로의 최대 입력을 받을 수 있나
  [ ] 폴백 모델용 프롬프트·스키마 변형이 필요한가(지원 키워드 차이)
  [ ] 폴백 때 비용·한도: 폴백 쪽 RPM·TPM이 주 트래픽을 받을 만한가
  [ ] 로그·지표에 응답 모델·폴백 여부가 남나
```

### 3. 비용 라우팅을 켜기 전

- 평가셋으로 "싼 모델만 / 비싼 모델만 / 라우팅" 세 가지를 같은 문항에 돌려 품질 차이와 비용을 잰다([19](../19-llm-evaluation/2-summary.md)).
- 캐스케이드면 승격률 `p_승격`을 지표로 둔다. 승격률이 오르면 비용 절감이 사라지고 지연이 늘어난다(§2 식).

## 장애 시나리오와 대처

### 1. 폴백 모델의 형식·한도 차이로 장애 때만 파싱 오류 급증 (⚠ 커리큘럼)

- 현상: 주 제공자 장애 시간대에만 JSON 파싱·스키마 검증 실패와 "입력이 너무 김" 오류가 늘어난다.
- 보이는 형태: 실험 [B]에서 파싱 실패율이 장애 전·후 0.0~0.5%, 장애 중 4.7~10.3%.
- 원인: 폴백 모델의 토크나이저·문맥 창·구조화 출력 지원 범위·도구 호출 형식이 다르다. 폴백 경로는 평소에 거의 안 쓰여 차이가 숨어 있었다.
- 대처: 폴백 출력도 같은 검증기를 지나게 한다. 폴백 경로 계약 테스트를 정기적으로 돌린다. 폴백 모델용 스키마·프롬프트 변형을 따로 두거나, 그 기능은 폴백 대신 "잠시 불가"로 응답한다.

### 2. SDK × 앱 × 게이트웨이 재시도 중첩 → 요청 증폭 (⚠ 커리큘럼)

- 현상: 제공자 장애 순간 호출 수가 평소의 수 배로 치솟고, 회복 뒤에도 429가 이어진다.
- 보이는 형태: 사용자 요청 수 대비 제공자 호출 수 비율이 급등. 실험 [A]에서 3 × 3 × 2 = 18배.
- 원인: 층마다 독립적으로 재시도한다. 공식 SDK도 기본 재시도를 한다(Anthropic 2회 등). 실패 요청도 한도를 먹는다([11](../11-llm-api-client-contract/2-summary.md)).
- 대처: 재시도는 한 층에서만 하고 나머지 층은 끈다. 재시도 예산(전체 중 재시도 비율 상한)을 둔다. 서킷이 열리면 재시도하지 않고 바로 폴백한다.

### 3. 어느 모델로 라우팅됐는지 기록 안 함 → 품질 회귀 원인 추적 불가 (⚠ 커리큘럼)

- 현상: "일부 사용자만 답이 이상하다"는 신고가 오는데 재현이 안 된다.
- 보이는 형태: 품질 지표 전체 평균은 조금 나빠졌을 뿐이다. 실험 [B]의 전체 집계로는 실패가 B에서만 나왔다는 것이 안 보인다.
- 원인: 응답 모델·폴백 여부·라우팅 이유를 남기지 않았다. sticky 라우팅이면 문제가 일부 사용자에게 몰린다(Anthropic 2025-09-17 사후 분석의 라우팅 오류 사례).
- 대처: 요청 모델·응답 모델·라우팅 이유·폴백 여부·시도 번호를 매 호출 기록하고, 품질·오류 지표를 응답 모델별로 나눠 본다([23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md)).

### 4. 429·400·거부를 서킷 실패로 세서 멀쩡한 주 모델을 끊는다

- 현상: 트래픽이 몰린 순간 회로가 열려 전부 폴백으로 간다. 주 제공자 상태 페이지는 정상이다.
- 보이는 형태: 회로 열림 직전 오류의 대부분이 429 또는 400.
- 원인: 내 한도 초과(429)나 요청 내용 문제(400·거부)를 제공자 장애로 셌다.
- 대처: §4 표대로 실패를 분류한다. 일시 한도 429는 클라이언트 쪽 한도 조절로 다루고, 400·거부는 세지 않는다. 지출 한도 429는 기다려도 안 풀리므로 code·`retry-after` 유무로 따로 가른다([11](../11-llm-api-client-contract/2-summary.md) §5).

### 5. 회로가 늦게 닫혀 장애 뒤에도 폴백에 머문다

- 현상: 주 제공자가 회복됐는데 한동안 폴백 비용·형식 오류가 이어진다.
- 보이는 형태: 실험 [B]에서 장애가 t=600에 끝났는데 회로는 t=639에 닫혔고, 그동안 파싱 실패가 0.2~0.5% 남았다.
- 원인: 열림 유지 시간과 반열림 시험 주기가 회복을 늦게 감지한다.
- 대처: 열림 유지 시간을 회복 감지와 재장애 위험 사이에서 정한다. 반열림 시험 결과를 지표로 두고, 폴백 체류 시간을 경보 대상으로 둔다.

## 핵심 문장

- 게이트웨이는 라우팅·폴백·서킷·재시도·기록을 한곳에 모아, 모델을 바꿔도 앱 코드가 바뀌지 않게 한다.
- 비용 라우팅과 캐스케이드는 쉬운 요청을 싼 모델로 보낸다. 효과는 자기 평가셋으로 다시 재고, 승격률을 지표로 둔다.
- 폴백 모델은 토크나이저·문맥 한도·구조화 출력·도구 형식이 다르다. 그 차이는 장애 때만 드러나므로 폴백 출력도 같은 검증을 지나게 한다.
- 재시도는 SDK·앱·게이트웨이에서 곱해진다. 한 층에서만 하고 예산을 둔다.
- 매 호출마다 요청 모델·응답 모델·라우팅 이유·폴백 여부를 기록해야 품질 회귀를 경로별로 추적할 수 있다.

## 관련 주제·근거

- 선행
  - [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md) — 오류 분류, 재시도할 것·말 것
  - [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md) — 서킷 상태 기계(단일 출처)
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) — 재시도 증폭·예산(단일 출처)
- 후속·연결
  - [12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md) — 폴백 모델 쪽 프롬프트 캐시는 차갑기 쉽다
  - [14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md) — 모델마다 다른 구조화 출력 지원
  - [19-llm-evaluation](../19-llm-evaluation/2-summary.md) — 라우팅 품질 평가
  - [23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md) — 모델별 비용·품질 집계
  - [26-ai-incidents](../26-ai-incidents/2-summary.md) — Anthropic 2025-09-17 사후 분석(문맥 창 라우팅 오류·sticky 라우팅) 사례
  - [api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md), [reliability/28-bulkhead](../../reliability/28-bulkhead/2-summary.md)
- 논문
  - Chen·Zaharia·Zou, "FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance", arXiv 2023-05-09 — 요금 차이 두 자릿수 크기(약 100배), 프롬프트 적응·LLM 근사·LLM 캐스케이드, 최대 98% 비용 절감 <https://arxiv.org/abs/2305.05176>
  - Ong 외, "RouteLLM: Learning to Route LLMs with Preference Data", arXiv 2024-06-26 — 사람 선호 데이터로 학습한 강·약 라우터, 일부 경우 2배 넘는 비용 절감 <https://arxiv.org/abs/2406.18665>
- 문서(모두 2026-10-08 확인)
  - OpenAI "Rate limits" — SDK 자동 재시도(429·503)와 앱 재시도 합산, SDK 재시도를 끄거나 한도에 포함 <https://developers.openai.com/api/docs/guides/rate-limits>
  - Anthropic "Errors" — SDK 기본 2회 재시도(연결 오류·429·5xx), `max_retries` <https://platform.claude.com/docs/en/api/errors>
  - Gemini API "Troubleshooting" — Python SDK 일시 오류 재시도 최대 4회 <https://ai.google.dev/gemini-api/docs/troubleshooting>
  - Anthropic "Structured outputs"(숫자·문자열 제약 미지원) <https://platform.claude.com/docs/en/build-with-claude/structured-outputs> · OpenAI "Structured Outputs"(minimum·maximum 지원) <https://developers.openai.com/api/docs/guides/structured-outputs>
  - OpenTelemetry GenAI semantic conventions — metrics(`gen_ai.request.model`·`gen_ai.response.model`, 상태 Development) <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-metrics.md>
  - Anthropic, "A postmortem of three recent issues", 2025-09-17 — 문맥 창 라우팅 오류(08-05 Sonnet 4 요청의 0.8% → 08-29 부하 분산 변경 → 08-31 최악 시간대 Sonnet 4 요청의 16%), sticky 라우팅 <https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues>
- 실험 목록 (코드: scratchpad `ai/09/routing_sim.py`, `python:3.12-slim` Python 3.12.14, `--network none --cpus=2`, 2026-10-08)
  - [A] SDK·앱·게이트웨이 시도 횟수 조합 5가지의 전면 장애 시 제공자 호출 수
  - [B] 요청 1,000건, A 장애 t=300~599, 서킷(20건 창·50%·열림 50건·반열림 5건) 유무 × 시드 7·8·9 — A 호출 수, 장애 중 A 실패 호출, 구간별 파싱 실패율, 모델별 집계, 상태 전이
