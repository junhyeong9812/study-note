# ai-engineering/11-llm-api-client-contract — LLM API 클라이언트 계약: 스트림 이벤트, 200 뒤 오류, 중단 사유, 타임아웃 층위, 429와 Retry-After — 정리 (힌트)

## 해결하는 문제

LLM API는 겉보기에 평범한 HTTP API다. 그런데 평범한 HTTP 클라이언트 규칙("200이면 성공, 5xx면 재시도, 타임아웃 하나")을 그대로 쓰면 조용히 틀린다.

```text
  평범한 규칙                     LLM API에서 실제로 일어나는 일
  200 = 성공                      200을 받은 뒤 스트림 안에서 error 이벤트가 온다
  본문을 다 받으면 성공            본문은 끝났는데 출력 한도에 걸려 문장·JSON이 잘렸다
  타임아웃 하나(예: 30초)          긴 생성은 정상인데 끊기고, 처음부터 다시 생성해 다시 과금된다
  429면 잠깐 뒤 재시도              지출 한도 소진 429는 기다려도 안 풀린다 / 실패 요청도 한도를 먹는다
```

쉬운 예: 택배다.
- "배송 출발" 문자(200)를 받았다고 물건이 온 것이 아니다. 중간에 사고(스트림 안 오류)가 날 수 있다.
- 상자가 도착해도 "3상자 중 2상자"(잘린 응답)일 수 있다. 송장에 적힌 상자 수(중단 사유)를 확인해야 한다.
- 큰 짐은 원래 오래 걸린다. "출발 소식이 없음"과 "배송 중인데 오래 걸림"을 구분해야 한다.

똑같은 구조다.\
LLM 호출 클라이언트는 **종료 이벤트와 중단 사유까지 확인한 뒤에야** 성공으로 본다. 타임아웃은 첫 토큰·토큰 사이·전체로 나눈다. 재시도는 오류 종류를 보고 정한다.

백엔드 실무 예: 상담 요약·주문 메모 생성 같은 기능을 Spring 서비스에서 외부 LLM API로 호출한다. 잘린 요약이 DB에 저장되거나, 장애 때 재시도가 비용과 429를 키운다.

## 동작·원리

### 1. 호출 하나의 상태 기계

```text
            ┌──────────── 연결 실패 / 헤더 전 타임아웃 ───────────────▶ [재시도 판단]
  [보냄] ──▶ [헤더 수신]
               │ 상태 ≠ 200 ──▶ 429·500·503·529 → [재시도 판단]   400·401·402·403·413 → [영구 실패]
               │ 상태 = 200
               ▼
            [스트리밍] ── 이벤트(빈 줄로 끝남)마다 마지막 수신 시각 갱신
               │  error 이벤트 ─────────────────────────────▶ [스트림 오류] (200 뒤의 실패)
               │  첫 토큰 전 시간 초과 / 이벤트 사이 시간 초과 / 전체 시간 초과 ──▶ [타임아웃 종류별]
               │  연결이 닫힘(EOF) but 종료 이벤트 없음 ─────────▶ [불완전]
               ▼
            [종료 이벤트] ── 중단 사유 확인
               ├ 자연 종료(end_turn, stop) ──────────────────▶ [성공]
               ├ 길이 한도(max_tokens, length, incomplete) ──▶ [잘림] — 성공 아님
               ├ 거부(refusal, content_filter) ───────────────▶ [거부] — 같은 모델 재시도는 대개 무의미(다른 모델 폴백은 13)
               └ 도구 호출(tool_use, tool_calls) ────────────▶ [도구 실행 후 이어서](14·20)
```

- 성공은 맨 아래 한 칸뿐이다. 나머지 칸을 "받은 만큼 성공"으로 처리하면 잘린 출력이 하류로 간다.
- SSE 와이어 형식(빈 줄 = 이벤트 하나, `event:`·`data:`·`id:`·`:` 주석)은 [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md)가 단일 출처다.

### 2. 스트림 이벤트 — 제공자마다 다르다

| | Anthropic Messages API | OpenAI Responses API | OpenAI Chat Completions |
|---|---|---|---|
| 형식 | 이름 있는 SSE 이벤트 | 의미 이벤트(이름 있는 타입) | `data:`만 있는 SSE, 끝은 `data: [DONE]` |
| 시작 | `message_start` | `response.created` | 첫 청크(`delta.role`) |
| 본문 | `content_block_start` → `content_block_delta` … → `content_block_stop` | `response.output_text.delta` | `choices[].delta.content` |
| 끝 | `message_delta`(stop_reason·usage) → `message_stop` | `response.completed`(잘리면 `response.incomplete`, 실패면 `response.failed`) | `finish_reason`이 든 청크 → (`include_usage`면 `choices`가 빈 사용량 청크) → `[DONE]` |
| 스트림 안 오류 | `event: error` (예: `overloaded_error`) | `error` 이벤트 | — (문서에서 확인 못 함 [?]) |
| 생존 신호 | `ping` 이벤트 | — | — |

- 출처: Anthropic "Streaming messages", OpenAI "Streaming API responses"·Chat Completions API reference(모두 2026-10-08 확인). 이벤트 이름은 벤더 고유다. 일반 원리로 옮기지 않는다.
- Anthropic 문서는 스트림 안 `overloaded_error`가 비스트리밍이었다면 HTTP 529에 해당한다고 적는다. Errors 문서는 "SSE 응답에서는 API가 200을 돌려준 **뒤에** 오류가 날 수 있다"고 적는다.
- OpenAI Rate limits 문서: 스트리밍 요청의 HTTP 오류 응답은 스트림 시작 **전**에만 해당한다. 시작 뒤 오류는 스트림 이벤트로 올 수 있고, "출력을 소비한 뒤에는 요청을 자동으로 다시 보내지 말라"고 적는다.
- Anthropic `message_delta`의 usage 토큰 수는 누적값이다. 비용 기록은 마지막 값으로 한다.
- OpenAI Chat Completions에서 `stream_options.include_usage`를 켜면 `[DONE]` 직전에 `choices`가 빈 배열인 사용량 청크가 하나 더 온다(API reference, 2026-10-08 확인). 그래서 "맨 마지막 청크"가 아니라 `finish_reason`이 null이 아닌 청크에서 중단 사유를 읽는다. 스트림이 끊기면 이 사용량 청크를 못 받을 수 있다고 문서가 적는다.

### 3. 중단 사유 — 성공처럼 보이는 실패

| 뜻 | Anthropic `stop_reason` | OpenAI Responses | OpenAI Chat `finish_reason` |
|---|---|---|---|
| 자연 종료 | `end_turn`, `stop_sequence` | `status: completed` | `stop` |
| **출력 한도에 잘림** | `max_tokens` | `status: incomplete`, `incomplete_details.reason: max_output_tokens` | `length` |
| **문맥 창이 차서 잘림** | `model_context_window_exceeded` | — | — |
| 거부·필터 | `refusal` | 출력의 refusal 항목(Structured Outputs 가이드) | `message.refusal` 필드, `content_filter`(필터로 내용 생략) |
| 도구 호출 | `tool_use` | 함수 호출 항목 | `tool_calls` |
| 서버 도구 반복 한도 | `pause_turn` | — | — |

- 출처: Anthropic "Stop reasons and fallback"·"Context windows", OpenAI "Structured Outputs" 가이드(incomplete 처리 예)·Chat Completions API reference(모두 2026-10-08 확인).
- **`completed`·`stop`만으로 자연 종료라고 판정하지 않는다.** OpenAI Structured Outputs 가이드의 거부 예시는 Responses `status: "completed"` + 출력의 `refusal` 항목, Chat Completions `finish_reason: "stop"` + `message.refusal`이다. 성공으로 넘기기 전에 거부 항목·필드를 먼저 본다.
- Anthropic Context windows 문서: Claude 4.5 이상 모델은 입력 + `max_tokens`가 문맥 창을 넘어도 요청을 받고, 생성이 창 끝에 닿으면 `model_context_window_exceeded`로 멈춘다. 이전 모델은 검증 오류로 거절한다(베타 헤더로 새 동작을 켤 수 있다). 같은 상황이 모델 세대에 따라 "요청 거부"와 "잘린 200"으로 갈린다.
- Anthropic 문서는 `model_context_window_exceeded`를 "잘린 응답으로 취급하라"고, `max_tokens`에 잘린 `tool_use` 블록은 한도를 올려 다시 요청하라고 적는다.

### 4. 타임아웃 층위 — 무엇을 기다리는지 나눈다

```text
  시간 →
  slowStart  |──── 첫 토큰까지 3초 ────|▌▌▌▌▌▌▌▌ 끝                         정상(프리필·대기열이 김)
  longGen    |▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌▌ 끝  6초     정상(출력이 김)
  stall      |▌▌▌▌▌                    (10초 동안 아무것도 없음)            비정상

  전체 5초 하나:        slowStart 통과 · longGen 오판으로 끊김 · stall 5초 뒤에야 끊김
  첫 토큰 4초 + 이벤트 사이 2초 + 전체 60초:
                       slowStart 통과 · longGen 통과 · stall 2초 만에 끊김
```

- *첫 토큰 타임아웃*: 요청부터 첫 출력 이벤트까지. 대기열·프리필·네트워크가 정한다([10](../10-inference-latency-metrics/2-summary.md)).
- *이벤트 사이(idle) 타임아웃*: 마지막 이벤트 뒤 다음 이벤트까지. 서버가 살아 있는지 본다. Anthropic처럼 `ping` 이벤트를 보내는 제공자에서는 ping도 생존 신호로 센다.
- *전체 타임아웃*: 호출자가 기다려 줄 수 있는 마지막 시각. 생성 길이(`max_tokens`)에 맞춰 넉넉히 잡거나 상위 데드라인에서 받는다.
- 층위별 타임아웃의 일반 원리는 [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md), 데드라인 전파는 [reliability/05](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md)가 단일 출처다.
- JDK `HttpClient`의 요청 `timeout`은 응답 헤더까지만 덮는다([reliability/07](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md) 실험). 토큰 사이·전체 타임아웃은 직접 구현한다.
- Anthropic Errors 문서는 10분이 넘을 수 있는 요청에 스트리밍이나 Message Batches API를 권한다. 일부 네트워크가 유휴 연결을 끊을 수 있다고 적는다.

### 5. 429·529/503과 Retry-After — 기다리면 풀리는 것과 아닌 것

```text
  응답                            기다리면 풀리나   할 일
  429 + retry-after               예               retry-after 이상 기다림(최솟값으로 취급) + 지터
  429, 제공자가 일시 한도라고 표시  예               지수 백오프 + 지터, 시도 횟수·총 시간 상한
  429 지출·크레딧 한도 소진         아니오           재시도 금지 → 경보·관리자 조치
  529(Anthropic)/503 과부하        대개 예          retry-after가 있으면 따름, 없으면 백오프
  400·401·402·403·413             아니오           요청·키·결제를 고친다
  200 뒤 스트림 error(overloaded)  대개 예          받은 출력은 버리거나 이어 쓰기(아래), 재시도는 예산 안에서
```

- *Retry-After*: 다시 시도하기 전 기다릴 시간(초) 또는 시각을 알려 주는 응답 헤더(RFC 9110 10.2.3). 429에 붙일 수 있다(RFC 6585 4절 — MAY).
- 제공자별 차이(2026-10-08 확인)
  - Anthropic: 한도는 토큰 버킷으로 연속 보충된다. RPM·ITPM·OTPM 중 하나를 넘으면 429와 `retry-after`. 사용 등급의 월 지출 상한에 닿은 429는 오류 type이 일시 한도와 **같은** `rate_limit_error`다. 대신 `retry-after`가 **없고** Messages API에서는 `error.details.error_code`가 `enforced_spend_limit_reached`다. 접근이 풀릴 때까지 계속 실패한다(SDK 자동 재시도도 실패). 조직·워크스페이스 지출 한도는 400으로 온다. 과부하는 529. 60 RPM이 초당 1건으로 집행될 수 있다.
  - OpenAI: 429에 일시 한도(`Rate limit reached`, `Slow down`)와 결제·한도 소진(`Organization spend limit reached`·`Credit balance exhausted`·`Organization usage limit reached` 등)이 섞인다. 과부하는 503(`server_is_overloaded`). `error.code`로 구분한다. Retry-After는 최솟값으로 취급하고 작은 무작위 지연을 더하라고 한다. "실패한 요청도 분당 한도에 포함된다". 한도 계산은 `max_tokens`와 글자 수 기반 추정 토큰 중 큰 값이다.
  - Gemini API: 429 `RESOURCE_EXHAUSTED`·503 `UNAVAILABLE`에 지수 백오프, 400·402·403은 재시도하지 말라고 적는다. 한도는 API 키가 아니라 프로젝트 단위다.
- 공식 SDK도 재시도한다(Anthropic SDK 기본 2회, OpenAI 공식 SDK는 429·503을 SDK 설정에 따라, Gemini Python SDK는 재시도 최대 4회 — 각 문서, 2026-10-08 확인). 앱 재시도와 곱해지므로 한쪽을 끄거나 합산해 상한을 잡는다([13-model-routing-and-fallback](../13-model-routing-and-fallback/2-summary.md)).
- 백오프·지터·재시도 예산의 일반 원리는 [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md), 토큰 버킷은 [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md), 한도 계약 설계는 [api-design/14-rate-limit-and-quota-contracts](../../api-design/14-rate-limit-and-quota-contracts/2-summary.md)가 단일 출처다.

### 6. 끊긴 스트림을 어떻게 다시 하나

- 일반 SSE는 `Last-Event-ID`로 이어 받기를 할 수 있다(WHATWG HTML 9.2.4). 하지만 이것은 **서버가 이어 보내기를 구현할 때만** 된다([network/38](../../network/38-websocket-sse-long-lived/2-summary.md)).
- Anthropic "Streaming messages"(2026-10-08 확인)는 이어 받기 대신 **이어 쓰기 요청**을 안내한다. 받은 부분 응답을 새 요청에 넣어 나머지를 생성하게 한다.
  - 4.5 이하 모델: 부분 응답을 assistant 메시지의 시작으로 넣는다.
  - 4.6 이후 모델: 부분 응답을 담은 user 메시지로 "끊긴 곳부터 이어 쓰라"고 지시한다.
  - 도구 호출·extended thinking 블록은 부분 복구가 안 된다. 마지막 텍스트 블록부터 이어 쓴다.
- 처음부터 다시 요청하면 이미 받은 출력 토큰을 다시 생성하고 다시 과금된다. 끊긴 첫 시도의 생성분이 과금되는지는 제공자 문서에서 확인하지 못했다 [?].

### 실험: 모형 서버로 보는 계약 클라이언트

JDK `HttpServer` 모형 서버가 Anthropic 이벤트 이름을 본떠 응답한다. 시나리오는 쿼리 문자열로 고른다(429 횟수·`retry-after`·오류 type, 대기·프리필·토큰 간격, 스트림 결말 `normal`·`error`·`drop`·`max_tokens`, 멈춤).\
계약 클라이언트의 핵심:

```java
// 이벤트 읽기는 가상 스레드가, 시간 판정은 호출 스레드가 한다 — 막힌 read()를 기다리지 않는다
long limit = Math.min(deadline, tokens == 0 ? firstDeadline : lastEvent + to.idle().toNanos());
Object o = lines.poll(Math.max(0, limit - System.nanoTime()), TimeUnit.NANOSECONDS);
if (o == null) {
    Kind k = System.nanoTime() >= deadline ? Kind.TIMEOUT_TOTAL
           : tokens == 0 ? Kind.TIMEOUT_FIRST_TOKEN : Kind.TIMEOUT_IDLE;
    return new Result(k, "받은 토큰 " + tokens, tokens, ms(t0), null);
}
// … 빈 줄이면 이벤트 하나 완성: lastEvent 갱신, 이벤트 이름별 처리 …
case "error" -> { return new Result(Kind.STREAM_ERROR, "HTTP 200 뒤 " + type, tokens, ms(t0), null); }
// 스트림이 끝난 뒤
if (!sawStop) return new Result(Kind.INCOMPLETE, "종료 이벤트 없음", tokens, ms(t0), null);
// 모형 서버는 end_turn·max_tokens만 보내서 이 두 갈래로 충분했다(실제 클라이언트는 아래 글머리처럼 사유별로 나눈다)
if (!"end_turn".equals(stop)) return new Result(Kind.TRUNCATED, "stop_reason=" + stop, tokens, ms(t0), null);
```

```java
// 재시도: retry-after가 있으면 그 이상 + 지터, 없으면 Full Jitter. 한도 소진은 재시도하지 않는다
boolean retryable = (status == 429 || status == 503 || status == 529) && !type.equals("billing_limit");
long backoff = (long) (rnd.nextDouble() * Math.min(8000, 500L << (attempt - 1)));
long wait = r.retryAfter() != null ? r.retryAfter().toMillis() + (long) (rnd.nextDouble() * 250) : backoff;
```

- 위 중단 사유 판정은 모형 서버에 맞춘 단순화다. 실제 Anthropic 클라이언트는 `stop_reason`별로 나눈다 — `end_turn`·`stop_sequence`는 자연 종료, `max_tokens`·`model_context_window_exceeded`는 잘림, `tool_use`·`pause_turn`은 이어서 처리(14·20), `refusal`은 거부("Stop reasons and fallback", 2026-10-08 확인). 그대로 옮기면 `stop_sequence`·`tool_use`까지 잘림으로 분류된다.
- `billing_limit`은 이 모형의 이름이다. 실제로는 제공자 문서의 신호로 가른다(§5). Anthropic은 지출 상한 429도 type이 `rate_limit_error`라서, type만 보는 클라이언트는 [2b]처럼 계속 두드린다 — `retry-after` 유무와 `error.details.error_code`를 함께 본다.
- 순진한 클라이언트: 받은 `text_delta`를 모두 모아 "성공"으로 돌려준다.

(실험, eclipse-temurin:21-jdk OpenJDK 21.0.12, `--network none --cpus=2`, 서버·클라이언트 모두 컨테이너 안 127.0.0.1, `Random(42)`, 2026-10-08)

```text
[1] 429 + retry-after: 2 두 번, 그다음 정상
    시도 1 @    1ms → HTTP_RETRYABLE 429 rate_limit_error
    시도 2 @ 2669ms → HTTP_RETRYABLE 429 rate_limit_error
    시도 3 @ 4749ms → OK             stop_reason=end_turn
[2] retry-after 없는 429, 오류 type=billing_limit (한도 소진 모형) — 계속 실패
    시도 1 @    0ms → HTTP_FATAL     429 billing_limit
[2b] 같은 상황에서 type만 rate_limit_error인 429 — 백오프 재시도, 예산 5회에서 멈춤
    시도 1 @    0ms → HTTP_RETRYABLE 429 rate_limit_error
    시도 2 @  385ms → HTTP_RETRYABLE 429 rate_limit_error
    시도 3 @ 1295ms → HTTP_RETRYABLE 429 rate_limit_error
    시도 4 @ 2040ms → HTTP_RETRYABLE 429 rate_limit_error
    시도 5 @ 3148ms → HTTP_RETRYABLE 429 rate_limit_error
[3] 스트림 결말 3종: 순진한 클라이언트 vs 계약 클라이언트
  HTTP 200 뒤 error 이벤트       순진: 성공으로 저장 (토큰 40)        | 계약: STREAM_ERROR
  종료 이벤트 없이 연결 끊김            순진: 성공으로 저장 (토큰 20)        | 계약: INCOMPLETE
  stop_reason=max_tokens     순진: 성공으로 저장 (토큰 40)        | 계약: TRUNCATED
[4] 타임아웃 층위: 전체 5초 하나 vs 첫 토큰 4초 + 이벤트 간 2초 + 전체 60초
  slowStart  전체만: OK              3804ms 토큰  40 | 층위: OK                   3802ms 토큰  40
  longGen    전체만: TIMEOUT_TOTAL   5000ms 토큰 236 | 층위: OK                   6280ms 토큰 300
  stall      전체만: TIMEOUT_TOTAL   5000ms 토큰  10 | 층위: TIMEOUT_IDLE         2398ms 토큰  10
[5] longGen을 '전체 5초' 정책으로 처음부터 3번 재시도하면
    시도 1 → TIMEOUT_TOTAL, 받고 버린 토큰 236
    시도 2 → TIMEOUT_TOTAL, 받고 버린 토큰 236
    시도 3 → TIMEOUT_TOTAL, 받고 버린 토큰 236
    합계: 성공 0, 생성됐다 버려진 출력 토큰 708
```

- 두 번째 실행과 점검 재실행도 분류·토큰 수가 모두 같았다. 시각만 달랐다([1]의 시도 2·3이 2620·4698 ms와 2422·4500 ms, stall 층위 2389·2388 ms). [1]의 시각은 지터(0~250 ms)와 첫 연결 준비 때문에 수백 ms 범위로 흔들린다.
- [1] 시도 간격이 2초 이상이다. `retry-after`를 지켰다. 첫 시도는 연결 수립·JIT 준비로 수백 ms가 더 걸렸다.
- [2] 한도 소진 429는 한 번에 멈췄다. 같은 429라도 오류 type만 다른 [2b]는 예산 5회를 다 쓰고 실패했다. 소진 429를 일시 429로 다루면 이렇게 계속 두드린다. OpenAI 문서대로라면 그 실패 요청들도 분당 한도를 먹는다.
- [3] 순진한 클라이언트는 세 경우를 모두 성공으로 저장했다. 연결 끊김에서는 토큰 20개, 즉 응답의 절반이다.
- [4] 전체 5초 하나는 정상인 긴 생성(longGen)을 236토큰에서 끊었고, 진짜 멈춘 stall은 5초까지 기다렸다. 층위 타임아웃은 longGen을 끝까지 받고 stall은 2.4초에 끊었다.
- [5] 같은 정책으로 처음부터 재시도하면 이 모형에서는 매번 같은 곳에서 끊긴다(모형 서버는 같은 요청에 같은 출력을 보낸다). 성공 0건에 출력 토큰 708개를 생성시켰다.

## 쓰이는 자료구조·알고리즘

- **SSE 줄 파서 = 상태 기계** — 줄을 모으다 빈 줄에서 이벤트 하나를 내보낸다. 끝난 줄 없이 EOF가 오면 미완성 이벤트는 버린다([network/38](../../network/38-websocket-sse-long-lived/2-summary.md)).
- **호출 상태 기계** — §1 그림. 종료 상태마다 할 일(성공·재시도·잘림 처리·영구 실패)이 정해져 있다.
- **토큰 버킷** — 제공자 한도(Anthropic 문서가 명시)와 클라이언트 쪽 자체 제한([reliability/11](../../reliability/11-rate-limiter/2-summary.md)).
- **지수 백오프 + 지터, 재시도 예산** — [reliability/06](../../reliability/06-retry-backoff-jitter/2-summary.md).
- **생산자-소비자 큐** — 읽기 스레드가 줄을 넣고 호출 스레드가 시간 제한을 걸고 꺼낸다([data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 증상에서 칸을 찾는다

| 증상 | 원인 칸(§1) | 확인 |
|---|---|---|
| 요약 끝이 문장 중간에서 끊겨 저장됨 | 잘림 | 저장된 행의 `stop_reason`/`finish_reason`/`status` |
| 가끔 응답이 절반만 저장됨, 오류 로그 없음 | 스트림 오류·불완전 | 종료 이벤트 수신 여부, 스트림 안 `error` 이벤트 로그 |
| 긴 보고서 생성만 계속 타임아웃, 재시도해도 같음 | 전체 타임아웃이 생성 시간보다 짧음 | 끊길 때까지 받은 토큰 수, `max_tokens` |
| 429가 몇 분째 안 끝남 | 한도 소진 429 또는 재시도 폭주 | `retry-after` 유무, 오류 type·code, 실패 요청 수 |
| 비용이 트래픽보다 빨리 늚 | 처음부터 재시도, 중첩 재시도 | 요청 ID별 시도 수, 시도별 출력 토큰 |

### 2. 계약을 코드로 고정한다

```java
sealed interface LlmResult permits Completed, Truncated, Refused, StreamFailed, TimedOut, Rejected {}
record Completed(String text, Usage usage) implements LlmResult {}
record Truncated(String partial, String reason, Usage usage) implements LlmResult {}   // max_tokens·length·incomplete
record Refused(String reason) implements LlmResult {}
record StreamFailed(String errorType, String partial, boolean retryable) implements LlmResult {}
record TimedOut(String phase, int tokensReceived) implements LlmResult {}              // first_token·idle·total
record Rejected(int status, String errorType, Duration retryAfter) implements LlmResult {}

String summaryOrFail(LlmResult r) {
    return switch (r) {
        case Completed c -> c.text();
        case Truncated t -> throw new IllegalStateException("잘린 응답 — 저장하지 않음: " + t.reason());
        case Refused f -> throw new IllegalStateException("거부: " + f.reason());
        case StreamFailed s -> throw s.retryable() ? new RetryableException(s.errorType())   // 과부하 같은 일시 오류만, 받은 출력은 버리거나 이어 쓰기(§6)
                                                   : new IllegalStateException(s.errorType());
        case TimedOut to -> throw new RetryableException("timeout:" + to.phase());
        case Rejected rj -> throw isTransient(rj) ? new RetryableException(rj.errorType()) : new IllegalStateException(rj.errorType());
        // isTransient: 상태·오류 code로 판정(§5 표) — retry-after 유무로 정하지 않는다. 일시 429·503도 헤더가 없을 수 있다(없으면 백오프)
    };
}
```

- 호출 결과를 문자열 하나로 돌려주지 않는다. 잘림·거부·부분 실패를 타입으로 드러내면 호출자가 "성공처럼 저장"할 길이 없어진다.
- `sealed` + 패턴 `switch`는 빠진 경우를 컴파일러가 잡는다(Java 21).

### 3. 비용·한도 상한을 요청 앞에 둔다

```text
  요청 전   입력 토큰 추정(토큰 카운트 API나 토크나이저 — 04) + max_tokens ≤ 기능별 상한
           max_tokens는 실제 필요에 맞게 — OpenAI는 한도 계산에 max_tokens를 쓴다
  요청 중   첫 토큰 / 이벤트 사이 / 전체 타임아웃, 스트림 오류 감시
  요청 후   usage(입력·출력·캐시 토큰) 기록, 시도 번호와 함께 → 재시도가 만든 비용을 분리해 본다
```

- 토큰 추정과 언어별 차이는 [04-tokenization-and-token-cost](../04-tokenization-and-token-cost/2-summary.md)가 단일 출처다.
- 비용 귀속·관측은 [23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md).

### 4. 재시도 규칙 한 장

```text
  재시도 한다    429(일시 한도) · 500 · 503 · 529 · 첫 토큰 전 타임아웃 · 스트림 안 overloaded
                → retry-after 우선, 없으면 Full Jitter, 시도 횟수와 총 시간 예산, SDK 재시도와 합산
  재시도 안 한다  지출·크레딧·쿼터 소진 · 400·401·402·403·413 · 거부(refusal — 같은 모델로는. 다른 모델 폴백은 13)
  조건부        잘림 → max_tokens를 올리거나 이어 쓰기 요청(같은 요청 반복은 같은 결과)
               토큰을 받은 뒤 끊김 → 이어 쓰기 요청, 또는 처음부터(비용 기록과 함께)
```

## 장애 시나리오와 대처

### 1. HTTP 200 뒤 스트림 안 error 이벤트를 무시 → 반쪽 응답을 정상 처리 (⚠ 커리큘럼)

- 현상: 과부하 시간대에 일부 응답이 내용 없이 짧거나 중간에서 끊긴 채 저장된다.
- 보이는 형태: HTTP 상태 로그는 전부 200. 실험 [3]에서 순진한 클라이언트는 error 이벤트가 온 응답을 "성공(토큰 40)"으로 저장했다.
- 원인: 스트리밍에서는 200을 보낸 뒤에도 오류가 난다(Anthropic Errors 문서). 클라이언트가 `error` 이벤트를 처리하지 않았다.
- 대처: 스트림 안 `error` 이벤트를 실패로 바꾸고, 종료 이벤트를 받기 전에는 성공으로 처리하지 않는다. 과부하 오류는 재시도 예산 안에서 다시 한다.

### 2. 중단 사유를 확인하지 않아 잘린 문장·JSON을 성공으로 저장 (⚠ 커리큘럼)

- 현상: 요약이 문장 중간에서 끝나 있다. 구조화 출력이면 하류 파싱 오류.
- 보이는 형태: `stop_reason: "max_tokens"`, `finish_reason: "length"`, `status: "incomplete"`. 실험 [3]에서 순진한 클라이언트는 `max_tokens` 응답도 성공으로 저장했다.
- 원인: 출력 한도(또는 문맥 창)에 닿아 생성이 멈췄다. HTTP 관점에서는 정상 응답이다.
- 대처: 자연 종료만 성공으로 본다. 잘림은 `max_tokens`를 올려 다시 요청하거나 이어 쓰기, 또는 실패로 처리한다. 잘린 JSON은 부분 파싱하지 않는다([14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md)).

### 3. 전체 타임아웃 하나로 긴 생성을 끊고 처음부터 재시도 → 출력 토큰을 다시 생성·과금 (⚠ 커리큘럼)

- 현상: 긴 보고서 생성만 매번 실패하고, 비용은 성공 건수에 비해 크게 늘어난다.
- 보이는 형태: 타임아웃 로그가 매번 비슷한 경과 시간·토큰 수에서 찍힌다. 실험 [5]에서 3번 재시도로 성공 0건, 버린 출력 토큰 708개.
- 원인: 정상인 긴 생성과 멈춘 스트림을 구분하지 못하는 단일 타임아웃. 생성 시간이 타임아웃보다 긴 요청은 재시도해도 다시 끊기기 쉽다. 실험 모형 서버는 같은 요청에 같은 길이를 보내서 매번 236토큰에서 끊겼다. 실제 LLM은 같은 요청도 출력이 달라질 수 있어(OpenAI "Advanced usage": 기본 비결정적, 2026-10-08 확인) 끊기는 지점도 흔들린다.
- 대처: 첫 토큰·이벤트 사이·전체 타임아웃으로 나눈다(실험 [4]). 전체 타임아웃은 `max_tokens`에 맞춰 잡는다. 이미 토큰을 받았다면 처음부터가 아니라 이어 쓰기 요청을 검토한다. 아주 긴 작업은 스트리밍이나 배치 API로 돌린다(Anthropic 문서는 10분 넘는 요청에 권함).

### 4. 실패 요청도 분당 한도에 포함 → 즉시 재시도 폭주로 429가 계속된다 (⚠ 커리큘럼)

- 현상: 429가 한 번 나기 시작하면 몇 분째 끝나지 않는다.
- 보이는 형태: 429 비율이 계속 높고, 요청 수가 평소보다 많다(재시도분).
- 원인: OpenAI 문서는 실패한 요청도 분당 한도에 들어간다고 적는다. 기다림 없이 다시 보내면 한도를 스스로 계속 채운다. SDK 재시도와 앱 재시도가 겹치면 더 빨리 찬다.
- 대처: `retry-after`를 최솟값으로 지키고 지터를 더한다. 시도 횟수·총 시간 예산을 둔다. 앱 쪽에 클라이언트 측 토큰 버킷을 두어 한도 근처에서 미리 줄인다.

### 5. 지출 한도 도달 429를 일시 오류로 재시도 → 영원히 안 풀린다 (⚠ 커리큘럼)

- 현상: 어느 순간부터 모든 LLM 호출이 실패하고, 재시도 로그만 쌓인다.
- 보이는 형태: 429인데 `retry-after`가 없고 type은 `rate_limit_error` 그대로, `error.details.error_code: "enforced_spend_limit_reached"`(Anthropic 사용 등급 지출 상한). OpenAI는 `error.code`가 결제·한도 계열(`organization_spend_limit_exceeded`·`credit_balance_exhausted` 등). 실험 [2b]처럼 예산을 다 쓰고 실패한다.
- 원인: 지출·쿼터 한도는 시간이 지나도 풀리지 않는다. 관리자가 한도를 바꾸거나 기간이 바뀌어야 풀린다.
- 대처: type만이 아니라 제공자가 주는 code·`retry-after` 유무로 분류해 재시도하지 않고(실험 [2]), 즉시 경보를 낸다. 기능을 축소 모드로 돌리거나 다른 계정·제공자로 폴백할지는 [13](../13-model-routing-and-fallback/2-summary.md)에서 정한다.

## 핵심 문장

- LLM 호출의 성공은 "200 + 종료 이벤트 + 자연 종료 사유"를 모두 확인한 뒤다.
- 스트리밍에서는 200 뒤에도 오류가 온다. 종료 이벤트 없이 끊긴 스트림은 불완전한 응답이다.
- 출력 한도·문맥 창에 닿은 응답은 HTTP로는 정상이지만 잘린 것이다. 저장하지 말고 한도를 올리거나 이어 쓰게 한다.
- 타임아웃은 첫 토큰·이벤트 사이·전체로 나눈다. 단일 전체 타임아웃은 정상인 긴 생성을 끊고, 재시도할 때마다 같은 출력을 다시 생성시킨다.
- 429는 종류가 다르다. 일시 한도는 `retry-after`와 지터로 기다리고, 지출·쿼터 소진은 재시도하지 않는다. 실패 요청도 한도를 먹는다.
- 이벤트 이름·오류 코드·헤더·중단 사유는 제공자마다 다르다. 일반 원리로 옮기지 말고 문서와 날짜를 적는다.

## 관련 주제·근거

- 선행
  - [04-tokenization-and-token-cost](../04-tokenization-and-token-cost/2-summary.md) — 토큰 = 과금·한도·시간 단위
  - [07-decoding-and-nondeterminism](../07-decoding-and-nondeterminism/2-summary.md) — 같은 요청을 다시 보내도 같은 출력이 아니다
  - [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md) — SSE 와이어 형식·재연결(단일 출처)
  - [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md) — 백오프·지터·예산(단일 출처)
- 후속·연결
  - [10-inference-latency-metrics](../10-inference-latency-metrics/2-summary.md) — TTFT·ITL 측정
  - [12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md) — 캐시 토큰과 한도(Anthropic 캐시 인지 ITPM)
  - [13-model-routing-and-fallback](../13-model-routing-and-fallback/2-summary.md) — 재시도 중첩·폴백
  - [14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md) — 잘린 JSON·거부 처리
  - [reliability/05-timeouts-and-deadline-propagation](../../reliability/05-timeouts-and-deadline-propagation/2-summary.md), [reliability/07-timeout-taxonomy-by-layer](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md), [reliability/11-rate-limiter](../../reliability/11-rate-limiter/2-summary.md), [api-design/14-rate-limit-and-quota-contracts](../../api-design/14-rate-limit-and-quota-contracts/2-summary.md)
- 명세
  - WHATWG HTML Living Standard 9.2 Server-sent events — `text/event-stream`, 재연결, 9.2.4 `Last-Event-ID` <https://html.spec.whatwg.org/multipage/server-sent-events.html>
  - RFC 6585 4절 429 Too Many Requests(Retry-After MAY) <https://www.rfc-editor.org/rfc/rfc6585> · RFC 9110 10.2.3 Retry-After(HTTP-date 또는 초) <https://www.rfc-editor.org/rfc/rfc9110>
- 제공자 문서(모두 2026-10-08 확인)
  - Anthropic "Streaming messages" — 이벤트 흐름, `ping`, 스트림 안 `error`(`overloaded_error` ↔ 529), usage 누적, 오류 복구(이어 쓰기, 4.5 이하/4.6 이후) <https://platform.claude.com/docs/en/build-with-claude/streaming>
  - Anthropic "Errors" — 400·401·402·403·413·429·500·504·529, 500은 백오프 재시도 권장, 지출 상한 429의 retry-after 없음, 200 뒤 오류, request-id, SDK 기본 2회 재시도, 10분 넘는 요청 <https://platform.claude.com/docs/en/api/errors>
  - Anthropic "Rate limits" — 토큰 버킷, RPM·ITPM·OTPM, `retry-after`, 60 RPM → 초당 1, "Reaching your spend cap"(type `rate_limit_error` + `enforced_spend_limit_reached`, retry-after 없음) <https://platform.claude.com/docs/en/api/rate-limits>
  - Anthropic "Stop reasons and fallback"·"Context windows" — `stop_reason` 값과 처리, `model_context_window_exceeded` <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons> · <https://platform.claude.com/docs/en/build-with-claude/context-windows>
  - OpenAI "Streaming API responses" — Responses 의미 이벤트, Chat Completions data-only SSE <https://developers.openai.com/api/docs/guides/streaming-responses> · Chat Completions API reference — `finish_reason`, `data: [DONE]` <https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create>
  - OpenAI "Rate limits" — 429 `slow_down`·503 `server_is_overloaded` 구분, Retry-After 최솟값 + 지터, SDK 자동 재시도와 합산, 실패 요청도 한도 포함, 스트림 시작 뒤 오류는 이벤트, `max_tokens` 기반 한도 계산 <https://developers.openai.com/api/docs/guides/rate-limits> · "Error codes" <https://developers.openai.com/api/docs/guides/error-codes>
  - Gemini API "Troubleshooting" — 429·503 백오프, 400·402·403 재시도 금지, Python SDK 최대 4회 <https://ai.google.dev/gemini-api/docs/troubleshooting> · "Rate limits"(프로젝트 단위) <https://ai.google.dev/gemini-api/docs/rate-limits>
- 실험 목록 (코드: scratchpad `ai/09/Mock.java`·`ai/09/Client11.java`)
  - `eclipse-temurin:21-jdk`(OpenJDK 21.0.12), `--network none --cpus=2`, 한 컨테이너 안 127.0.0.1, `Random(42)`, 2026-10-08, 2회 실행. 명령: `java Mock.java 18080 & java Client11.java 18080`
  - [1] 429 + retry-after 2초 ×2 → 성공 · [2] 한도 소진 모형 429 → 즉시 중단 · [2b] 일시 429 계속 → 예산 5회 · [3] error 이벤트·연결 끊김·max_tokens에서 순진 vs 계약 · [4] 전체 5초 vs 층위(4초·2초·60초) × slowStart·longGen·stall · [5] 전체 5초로 처음부터 3번 재시도한 버린 토큰
