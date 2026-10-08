# ai-engineering/11-llm-api-client-contract — 정답

## 정답

### 1. 200이 성공이 아닌 이유

- 스트리밍에서는 상태 코드가 본문보다 먼저 나간다. 그 뒤에 일어난 일은 상태 코드에 반영될 수 없다.
- 200 뒤 실패 경로
  - 스트림 안 `error` 이벤트(Anthropic: 예 `overloaded_error` — 비스트리밍이면 529에 해당). Anthropic Errors 문서: SSE에서는 200을 돌려준 뒤 오류가 날 수 있다.
  - 종료 이벤트 없이 연결이 끊김(네트워크·프록시 유휴 차단 등) — 불완전한 응답.
  - 정상 종료 이벤트지만 중단 사유가 길이 한도(`max_tokens`·`length`·`incomplete`) — 잘린 응답.

### 2. 상태 기계

```text
 [보냄] → 연결 실패·헤더 전 타임아웃 → 재시도 판단
        → [헤더] 상태 ≠ 200 → 429·500·503·529 재시도 판단 / 400·401·402·403·413 영구 실패
                 상태 = 200 → [스트리밍]
                              error 이벤트 → 스트림 오류
                              첫 토큰·이벤트 사이·전체 시간 초과 → 타임아웃(단계별)
                              EOF, 종료 이벤트 없음 → 불완전
                              [종료 이벤트] → 자연 종료(거부 항목 없음) = 성공 / 길이 한도 = 잘림 / 거부 / 도구 호출
```

- 성공은 "200 + 종료 이벤트 + 자연 종료 사유" 하나뿐이다.

### 3. 잘림 신호

| | 잘림 신호 |
|---|---|
| Anthropic Messages | `stop_reason: "max_tokens"` |
| OpenAI Responses | `status: "incomplete"`, `incomplete_details.reason: "max_output_tokens"`(스트리밍이면 종료 이벤트가 `response.incomplete`) |
| OpenAI Chat Completions | `finish_reason: "length"` |

- `model_context_window_exceeded`: Claude 4.5 이상 모델에서 입력 + `max_tokens`가 문맥 창보다 커도 요청을 받은 뒤, 생성이 문맥 창 끝에 닿으면 나온다. 문서는 잘린 응답으로 취급하라고 한다. 이전 모델은 같은 요청을 검증 오류로 거절한다(모두 2026-10-08 확인).

### 4. 스트림 결말 세 가지

| 결말 | 순진한 클라이언트 | 계약 클라이언트 |
|---|---|---|
| 200 뒤 error 이벤트 | 성공으로 저장(토큰 40) | `STREAM_ERROR` |
| 종료 이벤트 없이 끊김 | 성공으로 저장(토큰 20 — 절반) | `INCOMPLETE` |
| `stop_reason=max_tokens` | 성공으로 저장(토큰 40) | `TRUNCATED` |

- 순진한 클라이언트는 텍스트 이벤트만 모으고 종료·오류 이벤트를 보지 않는다. 그래서 세 경우가 정상 응답과 구별되지 않는다.

### 5. 타임아웃 층위

| 서버 | 전체 5초 하나 | 첫 토큰 4초 + 사이 2초 + 전체 60초 |
|---|---|---|
| slowStart | OK(3,804 ms) | OK(3,802 ms) |
| longGen | `TIMEOUT_TOTAL` 5,000 ms, 236토큰에서 끊김 | OK(6,280 ms, 300토큰) |
| stall | `TIMEOUT_TOTAL` 5,000 ms까지 기다림 | `TIMEOUT_IDLE` 2,398 ms |

- 전체 타임아웃 하나는 "정상인데 긴 것"과 "멈춘 것"을 구분하지 못한다. 층위로 나누면 둘을 가른다.

### 6. 긴 생성만 반복 실패

- 원인: 전체 타임아웃 하나가 생성 시간보다 짧다. 그래서 재시도해도 다시 끊기기 쉽다. 실험 모형 서버는 같은 요청에 같은 출력을 보내 매번 같은 곳에서 끊겼다. 실제 LLM은 출력 길이가 요청마다 달라질 수 있어 끊기는 지점도 흔들린다.
- 실험 [5]: 전체 5초 정책으로 처음부터 3번 → 매번 236토큰에서 끊김, 성공 0건, 생성됐다 버려진 출력 토큰 708개.
- 대처
  - 첫 토큰·이벤트 사이·전체 타임아웃으로 나누고, 전체는 `max_tokens`에 맞춰 잡는다.
  - 이미 받은 출력이 있으면 이어 쓰기 요청을 검토한다.
  - 아주 긴 작업은 배치 API 등으로 돌린다(Anthropic 문서는 10분 넘는 요청에 스트리밍·Message Batches를 권함).

### 7. 429 세 경우

- `retry-after` 있음: 그 시간 이상 기다린다. OpenAI 문서는 최솟값으로 취급하고 작은 무작위 지연을 더하라고 한다.
- `retry-after` 없음, 일시 한도: 지수 백오프 + 지터, 시도 횟수와 총 시간 예산.
- 지출·쿼터 소진: 재시도하지 않는다. 경보를 내고 기능을 축소하거나 폴백한다.
- 제공자 표시(2026-10-08 확인)
  - Anthropic: 사용 등급 월 지출 상한의 429는 type이 `rate_limit_error`로 같지만 `retry-after`가 없고, Messages API에서는 `error.details.error_code`가 `enforced_spend_limit_reached`다. 접근이 풀릴 때까지 계속 실패한다. type만 보고 분류하면 일시 한도로 오판한다. 조직·워크스페이스 지출 한도는 400.
  - OpenAI: 429 안에 `Organization spend limit reached`(`organization_spend_limit_exceeded`)·`Credit balance exhausted`(`credit_balance_exhausted`) 등이 있고, `error.code`로 구분한다. 결제·쿼터 오류 재시도는 접근을 복구하지 못한다고 적는다.

### 8. 끝나지 않는 429

- 문서: OpenAI "Rate limits" — "unsuccessful requests contribute to your per-minute limit". 실패한 요청도 한도를 먹으므로 즉시 재시도가 한도를 계속 채운다.
- 곱셈 요인: 공식 SDK의 자동 재시도(Anthropic 기본 2회 등)와 앱 재시도가 겹친다.
- 바꿀 것: `retry-after` 준수 + 지터, 시도·시간 예산, SDK 재시도와 합산한 상한, 클라이언트 쪽 토큰 버킷으로 한도 근처에서 미리 줄이기([reliability/11](../../reliability/11-rate-limiter/2-summary.md)).

### 9. 이어 받기 vs 이어 쓰기

- `Last-Event-ID`(WHATWG 9.2.4): 클라이언트가 마지막 이벤트 ID를 보내고, **서버가** 그 뒤부터 다시 보낸다. 서버가 구현해야만 된다.
- Anthropic 안내: 서버가 이어 보내는 것이 아니라, 클라이언트가 받은 부분 응답을 넣은 **새 요청**으로 나머지를 생성하게 한다. 4.5 이하 모델은 부분 응답을 assistant 메시지 시작으로, 4.6 이후 모델은 user 메시지에 넣고 이어 쓰라고 지시한다. 도구 호출·thinking 블록은 부분 복구가 안 된다.
- 비용: 처음부터 다시 요청하면 받은 부분까지 다시 생성한다. 이어 쓰기는 남은 부분만 생성한다(부분 응답은 새 요청의 입력 토큰이 된다).

### 10. JDK `HttpClient` timeout의 한계

- JDK `HttpRequest.Builder.timeout`은 응답 헤더까지만 덮는다([reliability/07](../../reliability/07-timeout-taxonomy-by-layer/2-summary.md) 실험). 스트림 본문이 흐르는 동안의 멈춤·전체 시간은 막지 못한다.
- 또 막힌 `read()`는 데이터가 오기 전까지 돌아오지 않아, 읽는 루프 안에서 시간을 검사할 수 없다.
- 실험 클라이언트: 가상 스레드가 줄을 읽어 큐에 넣고, 호출 스레드가 `poll(남은 시간)`으로 꺼낸다. 남은 시간은 `min(전체 데드라인, 첫 토큰 전이면 첫 토큰 데드라인 / 아니면 마지막 이벤트 + idle)`이다. 시간이 다 되면 어느 데드라인이 먼저였는지로 `TIMEOUT_TOTAL`·`TIMEOUT_FIRST_TOKEN`·`TIMEOUT_IDLE`를 가르고, 스트림을 닫는다.
