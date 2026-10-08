# ai-engineering/20-agent-loop-and-tool-safety — 에이전트 루프·턴 예산·종료 조건·부작용 도구의 멱등 키 — 정리 (힌트)

## 해결하는 문제

고객 지원 에이전트에 주문 조회 도구와 환불 도구를 붙였다. 어느 밤 주문 조회 API가 503을 돌려주자 에이전트는 인자를 조금씩 바꿔 가며 같은 도구를 수백 번 불렀다. 아침에 보니 모델 호출 비용이 평소의 수십 배였고, 환불 하나는 두 번 나갔다.

- *에이전트(agent)*: 모델이 다음에 부를 도구와 인자를 스스로 고르고, 그 결과를 보고 다시 고르는 **루프**. Anthropic "Building effective agents"(2024-12-19)는 미리 정한 코드 경로로 모델과 도구를 엮는 *워크플로(workflow)*와, 모델이 과정과 도구 사용을 동적으로 지시하는 *에이전트*를 구분한다.
  - 흔한 오해: "에이전트 = 똑똑한 자동화" — 루프의 다음 걸음을 모델이 정할 뿐, 멈추는 조건·쓸 수 있는 돈·되돌릴 수 없는 행동의 경계는 코드가 정하지 않으면 없다.

쉬운 예: 신입에게 법인 카드를 주고 "알아서 처리해"라고 했다.
- 언제 멈출지(예산·마감), 같은 일을 몇 번까지 다시 해 볼지, 어떤 결제는 상사 확인을 받을지 정해 주지 않으면 신입은 성실하게 계속 시도한다.
- 결제 단말이 "응답 없음"을 띄우면 다시 긁는다. 실제로는 첫 결제가 이미 승인됐을 수 있다.

똑같은 구조다.\
신입 = 모델, 카드 한도 = 토큰·턴 예산, 상사 확인 = 사람 확인(human-in-the-loop), 같은 결제를 두 번 긁지 않게 하는 영수증 번호 = 멱등 키다.

실무 예:
- 종료 조건·턴 예산 없이 루프를 돌렸다 → 같은 도구 반복 호출로 비용 폭주(⚠ 커리큘럼).
- 도구 호출이 타임아웃 나서 재시도했다 → 결제·메일 도구가 두 번 실행(⚠).
- 도구 오류 문자열을 그대로 모델에 넘겼다 → 모델이 인자만 바꿔 끝없이 재시도(⚠).
- 사용자 HTTP 요청이 타임아웃으로 끝난 뒤에도 백그라운드 루프가 돌며 부작용을 냈다(⚠).

## 동작·원리

### 1. 루프의 모양 — 모델이 고르고, 코드가 실행하고, 결과를 다시 넣는다

```text
              ┌──────────────────────────── 매 반복 전 확인 (코드가 정하는 불변식) ────────────────────────────┐
              │  턴 < maxTurns   누적 입력 토큰 + 이번 턴 ≤ 예산   now < 마감   같은 호출 반복 ≤ k              │
              └───────────────────────────────────────────────────────────────────────────────────────────┘
 사용자 요청 ─► [모델 호출: 이력 전체 + 도구 목록] ─► 중단 사유?
                     ▲                                 ├─ 최종 답(end_turn 등) ───────────► 답 반환 (DONE)
                     │                                 ├─ 도구 호출(tool_use) ─► [정책 검사] ─► [도구 실행] ─┐
                     │                                 └─ 잘림·거부 등 ─────────────────► 예외 처리         │
                     │                                                                                  │
                     └──────────────── 관측(도구 결과·오류)을 정리해 이력에 덧붙임 ◄──────────────────────────┘
```

- Anthropic Messages API에서 클라이언트 도구 루프는 `stop_reason`이 `"tool_use"`인 동안 도구를 실행해 `tool_result`를 돌려보내고, 그 밖의 중단 사유(`end_turn`·`max_tokens`·`stop_sequence`·`refusal`)에서 빠져나오는 `while` 루프다("How tool use works", 2026-10-08 확인).
  - 이 네 개가 전부는 아니다. "Stop reasons and fallback"(같은 날 확인)에는 `model_context_window_exceeded`(문맥 창이 차서 멈춤 — 잘린 응답으로 처리)와 `pause_turn`(서버 도구 루프가 반복 한도에 닿음 — 응답을 그대로 다시 보내 이어 가게 함)도 있다. 루프는 모르는 값을 성공으로 처리하지 않는다.
  - `tool_result`는 `tool_use_id`로 어떤 호출의 결과인지 밝히고, 실행 오류면 `is_error: true`를 붙일 수 있다("Handle tool calls", 같은 날 확인).
- 이 문서도 "모델은 여러분의 코드를 실행할 수 없다"고 적는다. 도구 실행·권한·재시도·예산은 **루프를 도는 애플리케이션의 몫**이다.
- ReAct(Yao 외, ICLR 2023)는 추론 흔적과 행동(도구 호출)을 번갈아 생성하게 하는 방식이다. 위키백과 API와 상호작용해 사고 연쇄만 쓸 때의 환각·오류 전파를 줄였다고 보고한다(초록).
- "Building effective agents"는 각 단계에서 환경으로부터 "실제 결과(ground truth)"를 받아 진행을 판단하고, 완료 시 종료하되 최대 반복 수 같은 중단 조건을 두는 것이 흔하다고 적는다. 자율성은 비용과 오류 누적(compounding errors)을 키운다는 경고도 함께다.

### 2. 비용은 턴 수의 제곱으로 자란다

```text
  턴 1  [시스템 500]                                       = 500
  턴 2  [시스템 500][관측1 300]                            = 800
  턴 3  [시스템 500][관측1 300][관측2 300]                 = 1,100
  ...   매 턴 이력 전체를 다시 보낸다 (예시 크기)
  T턴 누적 입력 토큰 = 500·T + 300·T(T−1)/2               ← T²에 비례
```

- 대화형 API는 대개 상태가 없어 매 호출에 이력 전체를 보낸다. 이력을 자르거나 요약하지 않고 매 턴 일정량이 쌓이면, 한 턴의 입력이 계속 커지므로 누적 비용은 턴 수의 제곱으로 자란다(위 식은 그 모양을 보이는 예시 크기). 오래된 도구 결과를 지우는 문맥 편집이나 요약을 쓰면 이 모양이 깨진다(Anthropic "Manage tool context", 2026-10-08 확인).
- 실험 A에서 이 식 그대로 8턴 12,400토큰, 1000턴 150,350,000토큰이었다. 턴이 125배인데 토큰은 약 12,000배다.
- 제공자 쪽 프롬프트 캐시가 앞부분 재전송 비용을 줄일 수는 있다 → [12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md). 턴 예산을 대신하지는 않는다.

### 실험: 예산·종료 조건이 루프를 어디서 멈추나

환경: eclipse-temurin:21-jdk 컨테이너(JDK 21.0.12, `--network none`), 단일 파일 `java AgentLoop.java`. 모델은 실제 LLM이 아니라 **스텁**이다 — 도구가 실패하면 인자를 세 가지로 돌려 가며 같은 도구를 다시 부른다(⚠의 "인자만 바꿔 재시도" 모양). 턴당 시스템 500·관측 300토큰, 모델 지연 700ms는 (예시) 값이다.

```java
// 실험 코드 발췌 — 매 반복 전 예산 확인
while (true) {
    if (turn >= 1000) { stop = Stop.HARD_CAP; break; }          // 실험 안전장치
    if (turn >= b.maxTurns()) { stop = Stop.MAX_TURNS; break; }
    long thisTurn = SYSTEM_TOKENS + (long) OBS_TOKENS * history.size(); // 매 턴 전체 이력을 다시 보낸다
    if (inputTokens + thisTurn > b.maxInputTokens()) { stop = Stop.TOKEN_BUDGET; break; }
    if (clockMs >= b.deadlineMs()) { stop = Stop.DEADLINE; break; }
    inputTokens += thisTurn; clockMs += 700;                      // (예시) 턴당 모델 지연 700ms
    ToolCall c = stubModel(history, turn);
    turn++;
    if (c == null) { stop = Stop.DONE; break; }
    String sig = c.name() + c.args();
    int n = seen.merge(sig, 1, Integer::sum);
    if (n > b.maxSameCall()) { stop = Stop.REPEAT; break; }
    history.add(toolAlwaysFails ? new Obs(true, "503 upstream") : new Obs(false, "ok"));
}
```

(실험, JDK 21 temurin, 2026-10-08)

```text
== A. 실패하는 도구 + 인자만 바꿔 재시도하는 스텁 모델
예산 없음(안전장치 1000턴)                  턴 1000  입력 토큰 150,350,000  가상 시각 700,000ms  종료 HARD_CAP
턴 상한 8                             턴    8  입력 토큰      12,400  가상 시각   5,600ms  종료 MAX_TURNS
입력 토큰 상한 20,000                    턴   10  입력 토큰      18,500  가상 시각   7,000ms  종료 TOKEN_BUDGET
같은 호출 3회 초과 금지                     턴   10  입력 토큰      18,500  가상 시각   7,000ms  종료 REPEAT
마감 5,000ms                         턴    8  입력 토큰      12,400  가상 시각   5,600ms  종료 DEADLINE
정상 도구(첫 호출 성공)                     턴    2  입력 토큰       1,300  가상 시각   1,400ms  종료 DONE
```

- 예산이 없으면 루프를 멈춘 것은 실험의 안전장치뿐이었다. 모델은 실패를 "다른 인자로 다시 해 보라"는 신호로만 받았다.
- 네 가지 예산은 각각 루프를 멈췄다. 어느 하나만으로 충분하지는 않다. 턴은 적어도 한 턴이 거대할 수 있고(토큰), 토큰은 적어도 느린 도구가 마감을 넘길 수 있다(시간).
- 반복 탐지는 **정확히 같은 서명**만 셌다. 인자를 세 가지로 돌리는 스텁은 각 서명이 4번째로 나온 10턴째에야 걸렸다. 인자를 매번 조금씩 바꾸면 정확 일치 탐지는 끝내 못 잡는다 — 도구 이름 단위 횟수 상한이나 연속 실패 횟수 상한을 함께 둔다.
- 정상 도구에서는 2턴(도구 1회 + 최종 답)에 끝났다. 예산은 정상 경로를 방해하지 않는 크기로 잡는다.

### 3. 도구 오류를 어떻게 돌려주나 — "고칠 수 있는 오류"와 "고칠 수 없는 오류"

```text
  도구 실패
   ├─ 모델이 인자를 고쳐서 풀 수 있다 (형식 오류·범위 밖 값·만료된 핸들)  → 결과로 돌려줌 + 무엇을 고칠지 설명
   ├─ 모델이 고쳐도 안 된다 (권한 없음·계속되는 업스트림 장애)          → 결과로 돌려주되 "모델 재시도 금지" 명시, 루프는 실패 횟수 증가
   │    └ 일시적 503·429는 코드가 Retry-After·백오프·마감 예산 안에서 재시도한다
   └─ 프로토콜·스키마 위반 (모르는 도구·잘못된 요청)           → 코드가 처리(루프 종료 또는 사람에게)
```

- MCP 명세 2026-07-28 "Tools"는 두 경로를 나눈다. 모르는 도구·잘못된 요청은 JSON-RPC 오류(프로토콜 오류), API 실패·입력 검증·업무 규칙 오류는 결과 안의 `isError: true`(도구 실행 오류)다. 클라이언트는 실행 오류를 모델에 제공해 스스로 고치게 하는 것이 SHOULD다(Error Handling 절) — 자세한 메시지 형식은 [21-mcp-protocol](../21-mcp-protocol/2-summary.md).
- Anthropic "Handle tool calls"도 `"failed"` 같은 일반 오류 대신 무엇이 잘못됐고 다음에 무엇을 할지 적으라고 권한다(예: 재시도 가능 시각).
- 같은 오류 코드라도 상황에 따라 갈린다. HTTP 503은 일시적 과부하·점검을 뜻하고 `Retry-After`를 보낼 수 있다(RFC 9110 15.6.4). MCP "Tools"는 만료되거나 모르는 핸들에 대한 호출이 그 사실을 적은 실행 오류를 돌려줘 모델이 새 핸들을 만들어 회복하게 하라고 한다(Expiry errors).
- 문제는 "모델이 고쳐도 안 되는" 오류다. 503이 계속되는 업스트림을 모델에게 맡기면 모델은 인자를 바꿔 볼 뿐이다(실험 A). 이 판단은 코드가 한다 — 연속 실패 횟수·서킷 브레이커([reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)).

### 4. 부작용 도구 — 멱등 키는 "시도"가 아니라 "의도한 행동"마다

```text
  루프: run-7 / step-3 "환불 12,000원" 결정
     시도1 ──► charge(key) ──► 결제 처리됨 ──X 응답 유실 (타임아웃)
     시도2 ──► charge(key) ──► 같은 key → 저장된 결과 재생, 새 결제 없음
                         key = "run-7:step-3"  (시도마다 새 UUID면 서버는 다른 요청으로 본다)
```

(실험 B — 같은 `AgentLoop.java`, 결제 도구가 첫 응답을 잃는다)

```text
== B. 결제 도구 응답 유실 뒤 재시도
멱등 키 없음                        실제 청구 2회, 마지막 결과: charge#2 amount=12000
시도마다 새 키                       실제 청구 2회, 마지막 결과: charge#2 amount=12000
행동마다 고정 키(run:step)            실제 청구 1회, 마지막 결과: charge#1 amount=12000 (재생)
```

- 타임아웃은 "실패"가 아니라 "모름"이다. 첫 시도가 처리됐는지 클라이언트는 알 수 없다. 키 저장소·판정 순서·결과 재생은 [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md), HTTP 계약은 [api-design/05-idempotency-keys](../../api-design/05-idempotency-keys/2-summary.md)가 단일 출처다.
- 에이전트에서 새로 생기는 함정은 **키를 어디서 얻나**다.
  - 시도마다 새로 만든 키는 키가 없는 것과 같았다(실험 B 둘째 줄).
  - 도구 호출 블록의 ID(Anthropic `tool_use` 블록의 `id` 등)를 키로 쓰면 같은 호출의 실행 재시도는 막는다. 그러나 모델 호출 자체를 다시 하면 모델이 새 ID로 같은 행동을 다시 제안할 수 있다(해석). 업무 의미의 키를 함께 쓴다. 단 **의도 하나**를 가리켜야 한다 — 한 주문에 부분 환불이 여러 번 가능하면 주문 ID + 행동 종류만으로는 별개의 환불이 합쳐진다. 환불 요청 ID처럼 의도마다 다른 값을 넣는다.
- 되돌릴 수 없는 행동은 실행 전에 사람 확인을 둔다. MCP "Tools"는 도구 호출을 거부할 수 있는 사람이 루프 안에 있어야 한다고 SHOULD로 적고, 민감한 작업에 사용자 확인을 띄우라고 권한다. OWASP LLM06(과도한 에이전시)도 고위험 행동의 사람 승인과 하류 시스템에서의 권한 검사(complete mediation)를 권한다 → [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md).

### 5. 사용자 요청이 끝난 뒤의 루프 — 취소 전파

(실험 C — 모델 한 턴 700ms(예시), 사용자 요청 마감 2000ms, 턴마다 부작용 도구 1회)

```text
== C. 사용자 요청 마감 뒤에도 루프가 도는가
마감 확인 false 부작용 6회 중 마감(2000ms) 뒤 4회
마감 확인 true  부작용 2회 중 마감(2000ms) 뒤 0회
```

- HTTP 요청은 2초에 타임아웃으로 끝났는데, 루프가 마감을 모르면 그 뒤에도 부작용 4회를 냈다. 사용자는 "실패"를 봤고 시스템은 "성공"을 남겼다.
- 마감 시각을 루프에 넘기고 **도구 실행 직전**에 확인하면 마감 뒤 부작용이 0이었다. 진행 중인 모델 호출·도구 호출을 실제로 끊는 법은 [reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md), 긴 작업을 요청 밖으로 빼는 법은 [reliability/32-batch-and-job-time-bounds](../../reliability/32-batch-and-job-time-bounds/2-summary.md)·[api-design/13-long-running-operations](../../api-design/13-long-running-operations/2-summary.md).

### 6. 에이전트를 쓸지 — 고정 경로와의 선택

| | 고정 경로(워크플로) | 에이전트 루프 |
|---|---|---|
| 다음 단계 결정 | 코드 | 모델 |
| 비용·지연 | 단계 수로 예측 가능 | 턴 수에 따라 변동(제곱으로 자랄 수 있음) |
| 테스트 | 경로별 단위 테스트 | 시나리오 평가 + 예산·정책 테스트 |
| 맞는 곳 | 단계가 정해진 작업(분류 → 조회 → 답) | 단계 수를 미리 알 수 없는 작업 |

- "Building effective agents"는 가능한 가장 단순한 해법에서 시작해 필요할 때만 복잡도를 올리라고 권한다. 많은 애플리케이션에서는 검색과 예시를 곁들인 단일 LLM 호출 최적화로 충분하다고 적는다.
- 같은 글 머리에는 2024년 12월 이후 도구 환경이 많이 바뀌었다는 고지가 있다(2026-10-08 확인). 구체적인 프레임워크 언급은 날짜를 감안해 읽는다.

## 쓰이는 자료구조·알고리즘

- **상태 기계와 루프 불변식**: 상태(턴·누적 토큰·시각·호출 횟수표)와 종료 상태(DONE·MAX_TURNS·TOKEN_BUDGET·REPEAT·DEADLINE). 불변식은 "다음 모델 호출 전에 모든 예산이 남아 있다".
- **해시맵 두 개**: 호출 서명 → 횟수(반복 탐지), 멱등 키 → 저장된 결과(중복 억제) — [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **예산 카운터**: 단조 증가 카운터와 상한 비교. 시간 예산은 마감 시각(시각 값)으로 넘긴다(상대 타임아웃을 단계마다 새로 재지 않는다 — [reliability/08-time-budget-allocation](../../reliability/08-time-budget-allocation/2-summary.md)).
- **허용 목록**: 루프가 이번 작업에서 부를 수 있는 도구 집합(집합 포함 검사).

## 적용 — 풀어나가는 법

### 1. 루프를 만들 때의 순서

1. 이 작업이 고정 경로로 되는지 먼저 본다. 되면 워크플로로 만든다.
2. 도구를 분류한다: 읽기 전용 / 되돌릴 수 있는 쓰기 / 되돌릴 수 없는 쓰기. 쓰기 도구에는 멱등 키, 되돌릴 수 없는 쓰기에는 사람 확인.
3. 예산 네 가지를 정한다: 턴, 누적 토큰(또는 비용), 마감 시각(시각 값), 같은 도구·연속 실패 횟수.
4. 도구 오류를 분류해 돌려준다: 고칠 수 있음(설명 포함) / 재시도 무의미(루프가 센다) / 프로토콜 오류(코드가 처리).
5. 중단 사유를 기록한다(어느 예산에 걸렸나) — 관측 지표가 된다([23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md)).

### 2. 부작용 도구 래퍼 (Java 21 — 실험 B의 결제 도구 발췌)

```java
static final class PaymentTool {
    final Map<String, String> idem = new HashMap<>();
    int charges = 0;
    boolean dropNextAck = true; // 첫 응답을 잃는다(타임아웃) — 실제로는 처리됐다
    String charge(String idemKey, int amount) throws Exception {
        if (idemKey != null && idem.containsKey(idemKey)) return idem.get(idemKey) + " (재생)";
        charges++;
        String result = "charge#" + charges + " amount=" + amount;
        if (idemKey != null) idem.put(idemKey, result);
        if (dropNextAck) { dropNextAck = false; throw new java.net.SocketTimeoutException("ack lost"); }
        return result;
    }
}
```

- 실험용이라 메모리 해시맵이다. 운영에서는 키 저장과 처리의 원자성, 같은 키 다른 본문, 보존 기간을 [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) 순서대로 처리한다.
- 키는 루프가 행동을 결정한 시점에 만든다: `runId + ":" + stepId`, 또는 의도 하나를 가리키는 업무 키(`refund:order-42:req-7` — 부분 환불이 여러 번 가능하므로 환불 요청 ID까지). 같은 키에 다른 금액이 오면 재생하지 말고 오류로 거절한다(Stripe 멱등 요청 문서도 매개변수가 다르면 오류, 2026-10-08 확인). 아래 실험용 `PaymentTool`은 이 검사를 생략했다.

### 3. 진단 — 비용이 튄 루프를 볼 때

| 증상 | 볼 것 |
|---|---|
| 요청 하나의 모델 호출 수가 수십~수백 | 중단 사유 분포(DONE이 아닌 비율), 같은 도구 연속 호출 수 |
| 토큰이 턴 수보다 훨씬 빨리 늘어남 | 관측 크기(도구 결과를 자르지 않고 통째로 넣는가) |
| 결제·메일이 두 번 | 도구 호출 로그에 같은 업무 키가 두 번, 멱등 키 유무 |
| 사용자 실패 후에도 부작용 | 요청 종료 시각 이후의 도구 실행 기록 |

## 장애 시나리오와 대처

### 1. 종료 조건 없는 루프의 비용 폭주 (⚠)

- 현상: 업스트림 장애 한 시간 동안 모델 비용이 평소의 수십 배.
- 보이는 형태: 요청 하나에 같은 도구 호출이 수백 건, 매 호출의 입력 토큰이 계속 커진다.
- 원인: 턴·토큰·시간 예산과 반복 탐지가 없다. 이력을 자르지 않으면 누적 입력은 턴 수의 제곱으로 자란다(실험 A: 1000턴 1.5억 토큰).
- 대처: 네 가지 예산을 코드로 강제하고, 도구 이름 단위·연속 실패 횟수 상한을 둔다. 중단 사유를 지표로 남긴다.

### 2. 재시도로 결제·메일 도구가 두 번 실행 (⚠)

- 현상: 고객에게 환불이 두 번, 같은 메일이 두 통.
- 보이는 형태: 도구 실행 로그에 같은 주문의 환불이 두 줄, 첫 줄은 "timeout".
- 원인: 첫 실행은 처리됐는데 응답을 잃었다. 멱등 키가 없거나 시도마다 새로 만들었다(실험 B).
- 대처: 행동 단위 고정 키(실행 ID + 단계 ID 또는 업무 키)로 서버 쪽 중복 억제. 되돌릴 수 없는 행동은 사람 확인.

### 3. 도구 오류를 그대로 넘겨 끝없는 재시도 (⚠)

- 현상: 권한 없음·대상 없음 오류인데 모델이 인자를 바꿔 계속 부른다.
- 보이는 형태: 같은 도구가 매번 다른 인자로 실패. 반복 탐지(정확 일치)에 안 걸린다.
- 원인: 오류가 "고칠 수 있음/없음"을 구분하지 않아 모델이 다시 해 볼 이유만 받는다.
- 대처: 오류를 분류해 "재시도 무의미"를 명시하고, 그런 오류는 루프가 세서 멈춘다. 업스트림 장애는 서킷 브레이커로 루프 밖에서 끊는다.

### 4. 사용자 요청이 끝난 뒤의 부작용 (⚠)

- 현상: 사용자는 타임아웃 오류를 봤는데 주문이 변경되어 있다.
- 보이는 형태: 요청 종료 시각 뒤에 찍힌 도구 실행 기록(실험 C: 6회 중 4회).
- 원인: 마감·취소 신호가 루프와 도구까지 전파되지 않았다.
- 대처: 마감 시각(시각 값)을 루프에 넘기고 도구 실행 직전에 확인한다. 길어질 작업은 비동기 작업으로 분리하고 상태 조회 API를 준다.

### 5. 정확 일치 반복 탐지를 피해 가는 루프

- 현상: 반복 탐지를 넣었는데도 비용이 튄다.
- 보이는 형태: 같은 도구가 인자만 조금씩 다르게(페이지 번호·철자) 계속 호출된다.
- 원인: 서명 = 이름 + 인자 전체여서 인자가 바뀌면 다른 호출로 센다(실험 A에서 3가지 인자를 돌리는 스텁은 10턴째에야 걸림).
- 대처: 도구 이름 단위 횟수·연속 실패 횟수·토큰 예산을 함께 둔다. 인자는 정규화한 뒤 비교한다.

## 핵심 문장

- 에이전트는 모델이 다음 도구 호출을 고르는 루프다. 멈춤·예산·권한은 루프를 도는 코드가 정한다.
- 매 턴 이력 전체를 자르지 않고 다시 보내면 누적 입력 토큰은 턴 수의 제곱으로 자란다. 턴·토큰·마감·반복 횟수 예산을 함께 둔다.
- 도구 오류는 "모델이 고칠 수 있는 것"과 "모델이 고쳐도 안 되는 것"을 나눠 돌려준다. 후자는 코드가 세서 멈춘다.
- 부작용 도구의 멱등 키는 시도마다가 아니라 의도한 행동마다 하나다. 되돌릴 수 없는 행동은 사람 확인을 거친다.
- 사용자 요청의 마감은 루프와 도구까지 전파하고, 도구 실행 직전에 확인한다.
- 고정 경로로 풀리는 작업은 워크플로로 만든다. 에이전트는 단계 수를 미리 알 수 없을 때 고른다.

## 관련 주제·근거

- 선행
  - [14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md) — 도구 호출 계약(이름·인자 스키마·결과)
  - [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md) — 멱등 키 저장소(단일 출처)
- 후속·연결
  - [21-mcp-protocol](../21-mcp-protocol/2-summary.md) — 도구를 표준 규약으로 노출
  - [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md) — 과도한 에이전시·간접 인젝션
  - [23-llm-observability-and-cost](../23-llm-observability-and-cost/2-summary.md) — 중단 사유·토큰 비용 관측
  - [reliability/09-cancellation-propagation](../../reliability/09-cancellation-propagation/2-summary.md) · [reliability/32-batch-and-job-time-bounds](../../reliability/32-batch-and-job-time-bounds/2-summary.md) · [api-design/05-idempotency-keys](../../api-design/05-idempotency-keys/2-summary.md) · [reliability/10-circuit-breaker](../../reliability/10-circuit-breaker/2-summary.md)
- 논문·문서(2026-10-08 확인)
  - Yao 외, "ReAct: Synergizing Reasoning and Acting in Language Models" (arXiv 2210.03629, v3 = ICLR 카메라 레디) — 초록: 추론과 행동 교차 생성, ALFWorld·WebShop 성공률 +34%p·+10%p(absolute) <https://arxiv.org/abs/2210.03629>
  - Anthropic, "Building effective agents" (2024-12-19) — 워크플로·에이전트 구분, 가장 단순한 해법부터, 매 단계 ground truth, 최대 반복 수 같은 중단 조건, 비용·오류 누적 경고 <https://www.anthropic.com/engineering/building-effective-agents>
  - Anthropic 문서 "How tool use works"(`stop_reason == "tool_use"` 동안의 `while` 루프), "Handle tool calls"(`tool_use_id`·`is_error`, 구체적 오류 메시지 권고), "Stop reasons and fallback"(중단 사유 표) <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works> <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls> <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
  - MCP 명세 2026-07-28 "Tools" — 사람이 도구 호출을 거부할 수 있어야 함(SHOULD), 민감한 작업 사용자 확인, 프로토콜 오류 vs `isError`, 클라이언트는 도구 호출 타임아웃·감사 로그(SHOULD) <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
  - OWASP Top 10 for LLM Applications 2025 — LLM06 Excessive Agency(과도한 기능·권한·자율성, 사람 승인, complete mediation, 레이트 리밋) <https://genai.owasp.org/llmrisk/llm062025-excessive-agency/>
- 실험 목록(eclipse-temurin:21-jdk 컨테이너, JDK 21.0.12, `--network none`, 결정적 — 난수 없음)
  - A. 스텁 모델 + 실패 도구에서 예산 없음·턴 8·입력 토큰 20,000·같은 호출 3회·마감 5,000ms의 종료 지점과 누적 토큰
  - B. 응답 유실 결제 도구 — 키 없음·시도마다 새 키·행동마다 고정 키의 실제 청구 횟수
  - C. 사용자 요청 마감 2,000ms 뒤 부작용 횟수 — 마감 확인 유무
