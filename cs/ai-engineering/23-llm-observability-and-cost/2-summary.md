# ai-engineering/23-llm-observability-and-cost — OTel GenAI 스팬·지표, 토큰 비용 귀속, 프롬프트 기록과 개인정보 — 정리 (힌트)

## 해결하는 문제

월말에 LLM 청구서가 지난달의 두 배로 왔다. 대시보드에는 "총 토큰"만 있다. 어느 기능이, 어느 고객이, 어느 모델이 늘렸는지 아무도 모른다. 비용 대시보드 숫자도 청구서와 30% 넘게 어긋난다.

```text
  청구서            $ 21.95 (3일째)  ← 무엇이?
  대시보드(태그 없음) 총 토큰 ↑        ← 어디서?
  대시보드(태그 있음) agent 기능 $3.58 → $14.89, summary +$0.29, search 그대로   ← 여기 (실험 C)
```

- *관측(observability)*: 시스템 밖에서 보이는 신호(로그·지표·트레이스)로 안에서 무슨 일이 있었는지 답하는 능력. 공통 원리는 [reliability/15-logging](../../reliability/15-logging/2-summary.md)·[reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md)·[reliability/17-distributed-tracing](../../reliability/17-distributed-tracing/2-summary.md)가 단일 출처다.
- LLM 호출에서 새로 생기는 것은 세 가지다: 비용이 **토큰 종류별**로 다르게 매겨진다, 입력·출력 원문이 **개인정보 덩어리**다, 관측 규약(OpenTelemetry GenAI)이 **아직 Development 상태라 이름이 바뀐다**.

쉬운 예: 공유 법인 카드.
- 카드 명세서에 "합계 200만 원"만 있으면 누가 썼는지 모른다. 결제마다 부서·프로젝트 코드를 적게 하면 원인이 보인다.
- 할인(캐시)이 붙은 결제를 정가로 계산하거나, 할인 전·후 금액을 둘 다 더하면 장부가 틀린다.
- 영수증에 고객 이름·주소가 적혀 있으면 장부를 아무나 보게 둘 수 없다.

똑같은 구조다.\
부서 코드 = 스팬의 기능·테넌트 태그, 할인 = 캐시 읽기 토큰, 영수증 내용 = 프롬프트·응답 원문이다.

실무 예:
- 캐시 읽기 토큰이 입력 토큰에 포함되는지 제공자마다 다른데, 한 규칙으로 계산했다 → 비용 이중 계산·누락(⚠ 커리큘럼).
- 디버깅하려고 프롬프트 원문을 로그에 남겼다 → 개인정보·비밀 유출(⚠).
- 기능·테넌트 태그 없이 토큰만 집계했다 → 비용 급증 원인 추적 불가(⚠).
- 계측 라이브러리를 올렸더니 지표 이름이 바뀌어 대시보드가 조용히 비었다(⚠).

## 동작·원리

### 1. 스팬 하나에 무엇을 싣나 — OTel GenAI 클라이언트 추론 스팬

```text
  [HTTP 요청 스팬: POST /refund-chat] ──────────────────────────────────────────────
     └─ [chat claude-x]  kind=CLIENT     ← gen_ai.client.inference 스팬 (재시도 포함 전체 구간)
          gen_ai.operation.name   = chat              gen_ai.provider.name = anthropic
          gen_ai.request.model    = claude-x          gen_ai.response.model = (실제 응답 모델)
          gen_ai.request.max_tokens / temperature / stream ...
          gen_ai.response.finish_reasons = ["end_turn"]   ← 스트림이 끝 이벤트 전에 끊기면 "error"
          gen_ai.response.time_to_first_chunk = 0.42 s
          gen_ai.usage.input_tokens               = 9200   ← 캐시 토큰 포함 총 입력 (SHOULD)
          gen_ai.usage.cache_read.input_tokens    = 9000
          gen_ai.usage.cache_write.input_tokens   = 0
          gen_ai.usage.output_tokens              = 400
          + 우리 태그: app.feature, app.tenant, prompt 버전
     └─ [execute_tool get_order] ...
```

- OpenTelemetry GenAI semantic conventions는 별도 저장소(`semantic-conventions-genai`)로 옮겨졌고 상태는 **Development**다(2026-10-08 확인, main 커밋 2026-10-07).
  - *Development 상태*: 안정 버전이 아니어서 이름·의미가 바뀔 수 있다는 표시. 4절의 실제 이름 변경이 그 예다.
- 2026-10-07 기준 클라이언트 추론 스팬은 `gen_ai.client.inference`다("Client Inference" 문서). 이름은 `{gen_ai.operation.name} {gen_ai.request.model}` 형식(SHOULD), 종류는 `CLIENT`(SHOULD).
- GenAI 스팬은 논리적 작업 전체를 덮는다. 일시 오류로 자동 재시도했다면 스팬은 **모든 재시도를 포함한** 시간이다(SHOULD, "Spans"). 재시도마다 따로 보고 싶으면 그 아래 HTTP 스팬을 본다.
- `gen_ai.response.finish_reasons`: 끝 이벤트를 못 받고 스트림이 끊기거나 취소되면 그 자리에 `error`를 넣는다(SHOULD). 잘린 응답·끊긴 스트림을 지표로 셀 수 있는 자리다 → [11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md).
- 지연 지표는 `gen_ai.client.inference.duration`(종단), `gen_ai.client.inference.time_to_first_chunk`, `gen_ai.client.inference.time_per_output_chunk`(첫 청크 이후 청크마다, 스트리밍일 때만) 히스토그램이다. 서버 쪽 TTFT·TPOT과 정의가 어떻게 다른지는 [10-inference-latency-metrics](../10-inference-latency-metrics/2-summary.md).

### 2. 토큰 종류별 비용 — 캐시 토큰이 어디에 들어 있나

```text
  총 입력 9,200 토큰 = [ 캐시 읽기 9,000 ][ 캐시 쓰기 0 ][ 일반 입력 200 ]

  Anthropic Messages usage            OpenAI Responses usage                 OTel 속성 (정규화 목표)
  input_tokens               = 200    input_tokens                 = 9,200   gen_ai.usage.input_tokens = 9,200
  cache_read_input_tokens    = 9,000    input_tokens_details                   gen_ai.usage.cache_read.input_tokens = 9,000
  cache_creation_input_tokens= 0          .cached_tokens           = 9,000   gen_ai.usage.cache_write.input_tokens = 0
                                          .cache_write_tokens      = 0
  └ input_tokens는 캐시 제외           └ input_tokens는 캐시 포함
```

- Anthropic "Prompt caching": `input_tokens`는 마지막 캐시 지점 **뒤의** 토큰만이다. 총 입력 = `cache_read_input_tokens + cache_creation_input_tokens + input_tokens`(2026-10-08 확인).
- OpenAI "Prompt caching": 비용 예제 코드가 `ordinary_input_tokens = input_tokens − cached_tokens − cache_write_tokens`로 계산한다 — `input_tokens`가 캐시 토큰을 **포함**한다는 뜻이다(같은 날 확인).
- OTel은 `gen_ai.usage.input_tokens`가 캐시 토큰을 포함해야 한다고 정하고(SHOULD), Anthropic 세부 규약은 Anthropic의 `input_tokens`에 캐시 읽기·쓰기를 **더해서** 이 값을 만들라고 한다(MUST, "Anthropic" 문서).
- 단가도 종류마다 다르다. Anthropic은 5분 캐시 쓰기 = 기본 입력 단가 1.25배, 1시간 쓰기 = 2배, 캐시 읽기 = 0.1배(일부 모델은 더 낮음)다. OpenAI 문서는 GPT-5.6 이후 모델에서 쓰기 1.25배·읽기 0.1배(GPT-6.1 Sol은 0.05배)이고, 그 이전 모델은 쓰기 추가 요금이 없고 읽기 단가가 모델마다 다르다고 적는다(2026-10-08 확인). 실제 단가는 모델·날짜마다 다르므로 가격표를 설정으로 둔다.
- 요금과 한도는 다른 계산이다. Anthropic "Rate limits"는 대부분 모델에서 캐시 읽기 토큰이 분당 입력 토큰 한도(ITPM)에 들어가지 않는다고 적는다(캐시 인지 ITPM). 비용 대시보드와 한도 대시보드의 "입력 토큰"은 같은 숫자가 아닐 수 있다.

### 실험: 정규화·비용·태그·이름 변경

환경: 호스트 Python 3.12.3 표준 라이브러리(`python3 -I obs.py`), 2026-10-08. 가격은 설명용 **(예시)** 값 — 입력 $3/100만 토큰, 캐시 읽기 0.1배, 쓰기 1.25배, 출력 $15/100만 토큰. 제공자 usage의 **필드 이름**은 위 문서에서 확인했고 값은 예시다.

```python
def norm_anthropic(u):  # Anthropic input_tokens는 캐시 토큰 제외 → 더해야 총 입력
    return {"gen_ai.usage.input_tokens": u["input_tokens"] + u["cache_read_input_tokens"] + u["cache_creation_input_tokens"],
            "gen_ai.usage.cache_read.input_tokens": u["cache_read_input_tokens"],
            "gen_ai.usage.cache_write.input_tokens": u["cache_creation_input_tokens"],
            "gen_ai.usage.output_tokens": u["output_tokens"]}
def norm_openai(u):     # OpenAI Responses input_tokens는 캐시 토큰 포함
    d = u["input_tokens_details"]
    return {"gen_ai.usage.input_tokens": u["input_tokens"],
            "gen_ai.usage.cache_read.input_tokens": d["cached_tokens"],
            "gen_ai.usage.cache_write.input_tokens": d["cache_write_tokens"],
            "gen_ai.usage.output_tokens": u["output_tokens"]}
def cost(a):
    total, cr, cw = a["gen_ai.usage.input_tokens"], a["gen_ai.usage.cache_read.input_tokens"], a["gen_ai.usage.cache_write.input_tokens"]
    ordinary = total - cr - cw
    w = ordinary + cr * PRICE["cache_read_mult"] + cw * PRICE["cache_write_mult"]
    return (w * PRICE["input"] + a["gen_ai.usage.output_tokens"] * PRICE["output"]) / 1_000_000
```

(실험, Python 3.12.3, 2026-10-08)

```text
== A. 같은 요청(총 입력 9,200, 캐시 읽기 9,000, 출력 400)의 정규화와 비용
  Anthropic 올바른 정규화                  input=  9200 일반=   200 비용=$0.009300
  OpenAI 올바른 정규화                     input=  9200 일반=   200 비용=$0.009300
  Anthropic 착각: input=200을 총량으로      input=   200 일반= -8800 비용=$-0.017700
  OpenAI 착각: cached를 또 더함            input= 18200 일반=  9200 비용=$0.036300
  캐시 할인 무시                           input=  9200 일반=  9200 비용=$0.033600
```

- 같은 요청이 제공자별 규칙대로 정규화하면 둘 다 $0.009300이었다(일반 200×3 + 캐시 9,000×0.3 + 출력 400×15 = 9,300 → ÷100만).
- Anthropic의 `input_tokens`를 총량으로 착각하면 "일반 입력"이 −8,800, 비용이 음수가 됐다. 음수 비용은 정규화가 틀렸다는 가장 싼 경보다.
- OpenAI 쪽에 캐시 토큰을 또 더하면 3.9배($0.036300)로 부풀었다(이중 계산). 캐시 할인을 모르고 전부 정가로 치면 3.6배였다.

```text
== C. 태그별 비용 집계 (합성 요청 3,000건, seed 23)
  day0 합계 $10.51  |  search $3.65  summary $3.33  agent $3.52
  day1 합계 $10.34  |  search $3.45  summary $3.31  agent $3.58
  day2 합계 $21.95  |  search $3.45  summary $3.60  agent $14.89
```

- 3일째 합계가 두 배가 됐다. 기능 태그로 나누면 agent 기능이 $3.58 → $14.89로 증가분 대부분이었고, summary는 $3.31 → $3.60(+$0.29)로 조금 올랐고 search는 그대로였다(합성 데이터 — 3일째 agent 요청의 입력을 8배로 만든 예시 사고).
- 태그가 없으면 "합계가 두 배"까지만 알 수 있다.

```text
== D. 지표 이름이 바뀐 뒤의 대시보드 질의 (t=5에 계측 라이브러리 업그레이드)
  옛 이름: [1000, 1000, 1000, 1000, 1000, None, None, None, None, None]
  새 이름: [None, None, None, None, None, 1000, 1000, 1000, 1000, 1000]
  임계값 경보(값<100) 발화 시점: 없음 | absent 경보 발화 시점: [5, 6, 7, 8, 9]
```

- 이름이 바뀌면 옛 이름의 시계열은 0이 아니라 **데이터 없음**이 된다. "값 < 100" 같은 임계값 경보는 표본이 있어야 평가되므로 울리지 않았다. "시계열이 없어짐(absent)" 경보만 울렸다.
- 실제 변경(4절)에서 이 모양이 생긴다.

### 3. 프롬프트·응답 원문 — 기본은 기록하지 않는다

```text
  선택지 (OTel GenAI "Capturing instructions, inputs, and outputs")
  1. [기본] 기록하지 않음
  2. 스팬 속성에 기록: gen_ai.system_instructions / gen_ai.input.messages / gen_ai.output.messages (Opt-In)
     → 텔레메트리 양이 감당되고 개인정보 규제가 적용되지 않거나 저장소가 규제를 지킬 때(예: 운영 전 환경)
  3. 외부 저장소에 저장하고 스팬에는 참조만
     → 운영 환경 권장. 별도 접근 통제 가능
```

- OTel GenAI 문서는 지시·사용자 메시지·모델 출력을 민감하고 큰 데이터로 보고, 계측 라이브러리가 **기본으로 기록하지 말고** 사용자가 켜는 옵션을 주라고 한다(SHOULD NOT / SHOULD). `gen_ai.input.messages`에는 사용자 개인정보가 들어 있을 가능성이 높다는 경고가 붙어 있다.
(실험 B, Python 3.12.3, 2026-10-08 — `obs.py`가 만든 스팬 JSON. 합성 프롬프트 "고객 A의 주문 o-42 환불 문의")

```text
== B. 스팬 JSON (gen_ai.client.inference — semantic-conventions-genai main 2026-10-07 기준 이름)
{
 "name": "chat claude-x",
 "kind": "CLIENT",
 "attributes": {
  "gen_ai.operation.name": "chat",
  "gen_ai.provider.name": "anthropic",
  "gen_ai.request.model": "claude-x",
  "gen_ai.request.max_tokens": 1024,
  "gen_ai.request.stream": true,
  "gen_ai.response.finish_reasons": [
   "end_turn"
  ],
  "gen_ai.response.time_to_first_chunk": 0.42,
  "gen_ai.usage.input_tokens": 9200,
  "gen_ai.usage.cache_read.input_tokens": 9000,
  "gen_ai.usage.cache_write.input_tokens": 0,
  "gen_ai.usage.output_tokens": 400,
  "app.feature": "refund-assistant",
  "app.tenant": "t-17",
  "app.prompt.sha256_8": "d70eb9a7",
  "app.prompt.chars": 19
 }
}
```

- 이 스팬은 원문 대신 길이와 해시 앞 8자리(`app.prompt.sha256_8`, `app.prompt.chars`)만 실었다. 같은 프롬프트가 반복되는지·길이가 튀는지는 보이고, 내용은 남지 않는다. `app.*`는 우리 쪽 이름이다(규약 속성 아님).
  - 해시도 짧은 입력이나 추측 가능한 입력이면 역추적될 수 있다. 원문이 꼭 필요하면 3번(외부 저장소 + 접근 통제 + 보존 기간)으로 간다 → [security/27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md).
- 시스템 프롬프트에 비밀을 넣지 않아야 하는 이유가 여기서도 하나 더 생긴다. 원문 기록을 켜는 순간 텔레메트리 저장소가 비밀 저장소가 된다([22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md)).

### 4. 이름이 바뀐다 — Development 규약의 실제 변경

| 시점 | 토큰 지표 | 추론 지연 지표 |
|---|---|---|
| `semantic-conventions` v1.37.0 태그 | `gen_ai.client.token.usage` 히스토그램 + `gen_ai.token.type`(`input`/`output`) | `gen_ai.client.operation.duration` |
| `semantic-conventions-genai` main (2026-10-07) | `gen_ai.client.inference.usage.input_tokens`·`.output_tokens`·`.cache_read.input_tokens`·`.cache_write.input_tokens`·`.reasoning.output_tokens` **카운터** + 분포용 `gen_ai.client.inference.operation.*` 히스토그램 | `gen_ai.client.inference.duration` |

- 2026-09-22 커밋(#374)이 토큰 지표를 종류별 카운터로 나눴고, 2026-10-06 커밋(#521)이 추론에는 `gen_ai.client.operation.duration` 대신 `gen_ai.client.inference.duration`을 쓰도록 바꿨다(저장소 커밋 기록, 2026-10-08 확인). 앞으로도 바뀔 수 있다.
- 새 문서는 사용량 카운터를 총 사용량·비용 근사용으로, 작업별 히스토그램은 백분위·이상치용으로만 쓰라고 구분한다. 히스토그램으로 총 비용을 계산하지 말라고 적는다("Inference Token Metrics").
- 대처는 세 가지다. 계측 라이브러리 버전을 고정하고 올릴 때 지표 이름 diff를 본다, 대시보드에 "데이터 없음" 경보를 둔다(실험 D), 비용 계산처럼 중요한 집계는 우리가 정한 이름(예: `app.llm.cost_usd`)으로 한 번 더 남긴다.

### 5. 품질 신호 — 비용만 보면 안 되는 이유

- 비용·지연은 쉽게 잰다. 품질은 그렇지 않다. 운영에서 볼 수 있는 대리 신호를 함께 남긴다: 중단 사유 분포(잘림·거부·오류 비율), 구조화 출력 검증 실패율, 에이전트 루프 중단 사유([20-agent-loop-and-tool-safety](../20-agent-loop-and-tool-safety/2-summary.md)), 사용자 피드백·재질문 비율.
- 모델·프롬프트 버전을 스팬에 남겨야(`gen_ai.response.model`, `gen_ai.prompt.version`) 품질 회귀를 버전과 맞춰 볼 수 있다. 오프라인 평가와의 연결은 [19-llm-evaluation](../19-llm-evaluation/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **카운터와 히스토그램**: 토큰·비용은 단조 증가 카운터(합·비율), 지연·요청당 토큰은 히스토그램(분위). 버킷 경계는 OTel 문서가 지수 경계를 권한다(0.01 ~ 81.92초). 분위 계산은 [data-analysis/05-percentiles-and-latency-distributions](../../data-analysis/05-percentiles-and-latency-distributions/2-summary.md).
- **태그별 집계 = 해시맵**: 키 (일자, 기능, 테넌트, 모델) → 합계. 태그 값이 너무 다양하면(사용자 ID) 시계열 수가 폭발한다 — 지표에는 낮은 카디널리티 태그만, 높은 카디널리티는 스팬·로그로([reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md)).
- **샘플링**: 스팬은 비용 때문에 샘플링하지만, 비용 집계용 카운터는 샘플링하지 않은 전수 값이어야 청구서와 맞는다. 오류·느린 요청은 꼬리 샘플링으로 남긴다([reliability/17-distributed-tracing](../../reliability/17-distributed-tracing/2-summary.md)).
- **해시(SHA-256 앞자리)**: 원문 대신 동일성만 남기는 지문.

## 적용 — 풀어나가는 법

### 1. 계측을 붙일 때의 순서

1. 제공자별 usage → OTel 속성 **정규화 함수**를 하나 두고 테스트한다(Anthropic은 더하고, OpenAI는 그대로). 음수 "일반 입력"이 나오면 예외.
2. 가격표를 설정으로 두고 (모델, 토큰 종류) → 단가로 비용을 계산해 카운터로 남긴다.
3. 스팬·지표에 기능·테넌트·프롬프트 버전·모델 태그를 붙인다(지표에는 낮은 카디널리티만).
4. 원문 기록은 기본 끔. 필요하면 외부 저장소 + 접근 통제 + 보존 기간.
5. 계측 라이브러리 버전 고정, "데이터 없음" 경보, 월 1회 청구서와 대시보드 합계 대조.

### 2. 정규화와 비용 (Java 21)

```java
import java.util.Map;

public class LlmCost {
    record Usage(long input, long cacheRead, long cacheWrite, long output) {   // OTel 의미: input은 캐시 포함 총량
        Usage {
            if (input - cacheRead - cacheWrite < 0) throw new IllegalStateException("정규화 오류: 일반 입력 < 0");
        }
    }
    record Price(double inputPerM, double readMult, double writeMult, double outputPerM) {}

    static Usage fromAnthropic(Map<String, Long> u) {          // input_tokens는 캐시 제외
        long r = u.get("cache_read_input_tokens"), w = u.get("cache_creation_input_tokens");
        return new Usage(u.get("input_tokens") + r + w, r, w, u.get("output_tokens"));
    }
    static Usage fromOpenAi(long inputTokens, long cached, long cacheWrite, long output) {  // input_tokens는 캐시 포함
        return new Usage(inputTokens, cached, cacheWrite, output);
    }
    static double cost(Usage u, Price p) {
        double weighted = (u.input() - u.cacheRead() - u.cacheWrite())
                + u.cacheRead() * p.readMult() + u.cacheWrite() * p.writeMult();
        return (weighted * p.inputPerM() + u.output() * p.outputPerM()) / 1_000_000;
    }

    public static void main(String[] args) {
        Price p = new Price(3.00, 0.1, 1.25, 15.00);           // (예시) 가격
        Usage a = fromAnthropic(Map.of("input_tokens", 200L, "cache_read_input_tokens", 9000L,
                                       "cache_creation_input_tokens", 0L, "output_tokens", 400L));
        Usage o = fromOpenAi(9200, 9000, 0, 400);
        System.out.printf("anthropic %s $%.6f%nopenai    %s $%.6f%n", a, cost(a, p), o, cost(o, p));
        try { fromOpenAi(200, 9000, 0, 400); }                 // Anthropic 값을 OpenAI 규칙으로 넣은 실수
        catch (IllegalStateException e) { System.out.println("거부: " + e.getMessage()); }
    }
}
```

(실험, JDK 21 temurin, 2026-10-08)

```text
anthropic Usage[input=9200, cacheRead=9000, cacheWrite=0, output=400] $0.009300
openai    Usage[input=9200, cacheRead=9000, cacheWrite=0, output=400] $0.009300
거부: 정규화 오류: 일반 입력 < 0
```

- 제공자 규칙을 섞으면 음수 일반 입력이 생기는 경우가 많다. 생성자에서 거부하면 대시보드에 들어가기 전에 잡힌다. 반대 방향 실수(이미 포함된 캐시를 또 더함)는 음수가 생기지 않으므로 청구서 대조로 잡는다.

### 3. 진단 표

| 증상 | 볼 것 |
|---|---|
| 대시보드 비용 ≠ 청구서 | 제공자별 정규화 규칙, 캐시 토큰 이중 계산·누락, 샘플링된 스팬으로 비용을 합쳤나 |
| 비용 급증 원인 불명 | 기능·테넌트·모델·프롬프트 버전별 분해, 요청당 입력 토큰 분위(p99) |
| 대시보드가 갑자기 빔 | 계측 라이브러리 버전 변경, 지표 이름 diff, absent 경보 |
| 로그에 고객 문장 | 원문 기록 옵션(Opt-In)이 켜졌나, 로그 저장소 접근 범위 |

## 장애 시나리오와 대처

### 1. 캐시 토큰 규칙 혼동 → 이중 계산·누락 (⚠)

- 현상: 비용 대시보드가 청구서보다 크거나 작다. 제공자를 바꾼 달부터 어긋난다.
- 보이는 형태: 같은 요청인데 제공자별로 "입력 토큰"이 20배 넘게 차이(200 vs 9,200), 음수 비용.
- 원인: Anthropic `input_tokens`는 캐시 제외, OpenAI `input_tokens`는 캐시 포함인데 한 규칙으로 계산했다(실험 A: 음수 비용 또는 3.9배).
- 대처: 제공자별 정규화 함수 + OTel 의미(총량에 캐시 포함)로 통일, 음수 검사, 월 1회 청구서 대조.

### 2. 프롬프트 원문 로그로 개인정보·비밀 유출 (⚠)

- 현상: 로그 검색 도구에서 고객 주소·전화번호·내부 키가 검색된다.
- 보이는 형태: 스팬 속성 `gen_ai.input.messages`나 앱 로그에 대화 원문.
- 원인: 디버깅용으로 원문 기록을 켰다. OTel은 기본으로 기록하지 말라고 한다(SHOULD NOT).
- 대처: 기본 끔, 필요하면 외부 저장소 + 접근 통제 + 보존 기간. 평소에는 길이·해시·버전만. 이미 남은 로그는 보존 정책에 따라 삭제한다.

### 3. 태그 없는 집계로 원인 추적 불가 (⚠)

- 현상: 비용이 두 배인데 어느 기능인지 모른다.
- 보이는 형태: 총 토큰 그래프 하나뿐.
- 원인: 기능·테넌트·모델 태그를 스팬·지표에 남기지 않았다.
- 대처: 요청 진입점에서 기능·테넌트를 컨텍스트에 넣고 LLM 스팬의 속성으로 남긴다. baggage로 전파한다면 자동 계측이 baggage를 대부분의 나가는 HTTP 요청 헤더에 실어 외부 API(LLM 제공자 포함)로 보낼 수 있다(OpenTelemetry "Baggage" 보안 고려사항, 2026-10-08 확인) — 테넌트 ID 같은 값은 외부 제공자 호출 전에 baggage에서 빼거나 그 호출의 전파를 막는다. 실험 C처럼 분해하면 한 기능이 바로 보인다.

### 4. 규약 이름 변경으로 대시보드가 조용히 빈다 (⚠)

- 현상: 계측 라이브러리 업그레이드 다음 날부터 토큰 그래프가 비었는데 경보가 없다.
- 보이는 형태: 옛 지표 이름은 데이터 없음, 새 이름은 아무도 안 보는 곳에 쌓임.
- 원인: Development 상태 규약의 이름 변경(예: `gen_ai.client.token.usage` → `gen_ai.client.inference.usage.*`, `gen_ai.client.operation.duration` → 추론은 `gen_ai.client.inference.duration`). 임계값 경보는 데이터가 없으면 평가되지 않는다(실험 D).
- 대처: 버전 고정, 업그레이드 때 이름 diff 확인, absent 경보, 핵심 비용 지표는 자체 이름으로 이중 기록.

### 5. 샘플링된 스팬으로 비용 합계

- 현상: 비용이 청구서의 10% 근처로 나온다.
- 보이는 형태: 비용 대시보드가 트레이스 백엔드에서 스팬 속성 합으로 계산된다.
- 원인: 트레이스는 10%만 남기도록 샘플링되어 있었다.
- 대처: 비용은 샘플링하지 않는 카운터(지표)로 집계하고, 스팬은 원인 조사용으로 쓴다.

## 핵심 문장

- LLM 비용은 토큰 종류(일반 입력·캐시 읽기·캐시 쓰기·출력)마다 단가가 다르다. 제공자 usage를 한 의미로 정규화한 뒤 계산한다.
- Anthropic `input_tokens`는 캐시 토큰을 빼고, OpenAI `input_tokens`는 포함한다. OTel `gen_ai.usage.input_tokens`는 포함한 총량이다.
- 비용 급증은 기능·테넌트·모델·프롬프트 버전 태그가 있어야 원인까지 내려간다. 비용 합계는 샘플링하지 않은 카운터로 낸다.
- 프롬프트·응답 원문은 기본으로 기록하지 않는다. 필요하면 외부 저장소와 접근 통제·보존 기간을 둔다.
- OTel GenAI 규약은 Development 상태라 이름이 바뀐다. 버전을 고정하고 "데이터 없음" 경보를 둔다.

## 관련 주제·근거

- 선행
  - [10-inference-latency-metrics](../10-inference-latency-metrics/2-summary.md) — TTFT·TPOT 정의
  - [19-llm-evaluation](../19-llm-evaluation/2-summary.md) — 오프라인 품질 측정
  - [reliability/17-distributed-tracing](../../reliability/17-distributed-tracing/2-summary.md) — 스팬·전파·샘플링(단일 출처)
- 후속·연결
  - [reliability/15-logging](../../reliability/15-logging/2-summary.md) · [reliability/16-metrics-and-golden-signals](../../reliability/16-metrics-and-golden-signals/2-summary.md)
  - [12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md) — 캐시 적중이 비용에 주는 효과
  - [20-agent-loop-and-tool-safety](../20-agent-loop-and-tool-safety/2-summary.md) · [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md) · [security/27-pii-classification-masking-retention](../../security/27-pii-classification-masking-retention/2-summary.md)
- 문서(모두 2026-10-08 확인)
  - OpenTelemetry GenAI semantic conventions(`semantic-conventions-genai` 저장소, main 2026-10-07, 상태 Development) — "Client Inference"(`gen_ai.client.inference` 스팬·지표, `finish_reasons`의 `error`, usage 각주) <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md> · "GenAI Spans"(재시도 포함 구간, 원문 기록 선택지) <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md> · "Inference Token Metrics" <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-token-metrics.md> · "Anthropic"(input 합산 MUST) <https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/anthropic.md>
  - 옛 정의: `open-telemetry/semantic-conventions` v1.37.0 `docs/gen-ai/gen-ai-metrics.md`(`gen_ai.client.token.usage`) <https://github.com/open-telemetry/semantic-conventions/blob/v1.37.0/docs/gen-ai/gen-ai-metrics.md>, 변경 커밋 #374(2026-09-22)·#521(2026-10-06)
  - Anthropic "Prompt caching"(usage 필드, 총 입력 식, 캐시 쓰기 1.25배·2배, 읽기 0.1배) <https://platform.claude.com/docs/en/build-with-claude/prompt-caching> · "Rate limits"(캐시 인지 ITPM) <https://platform.claude.com/docs/en/api/rate-limits>
  - OpenAI "Prompt caching"(`input_tokens_details.cached_tokens`·`cache_write_tokens`, 입력 비용 계산 예) <https://developers.openai.com/api/docs/guides/prompt-caching>
- 실험 목록(2026-10-08)
  - `obs.py`(호스트 Python 3.12.3 표준 라이브러리) — A. 제공자별 usage 정규화와 오정규화 세 가지의 비용, B. 스팬 JSON(원문 대신 길이·해시), C. 합성 요청 3,000건의 기능별 비용(seed 23), D. 지표 이름 변경 후 임계값 경보 vs absent 경보
  - `LlmCost.java`(eclipse-temurin:21-jdk 컨테이너, JDK 21.0.12, 네트워크 없음) — 정규화·비용·음수 거부
