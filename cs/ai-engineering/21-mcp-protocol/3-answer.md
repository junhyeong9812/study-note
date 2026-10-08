# ai-engineering/21-mcp-protocol — 정답

## 정답

### 1. 무엇 사이의 규약

- LLM 애플리케이션(클라이언트)과, 도구·리소스·프롬프트를 제공하는 서버 사이의 규약이다. 메시지는 JSON-RPC 2.0을 따른다(MCP 2026-07-28 "Overview").
- 모델 API(예: Anthropic Messages, OpenAI Responses)는 애플리케이션이 모델을 부르는 규약이다. MCP는 애플리케이션이 도구 쪽과 말하는 규약이라, 모델 호출과 도구 호출이 서로 다른 계약을 따른다.

### 2. 메시지 세 종류

- 요청: `id`와 `method`가 있고, 받는 쪽은 응답할 의무가 있다(알림이 아니면 Response MUST). 응답: 같은 `id`에 `result` 또는 `error`. 알림: `id`가 없고 받는 쪽은 응답하면 안 된다(JSON-RPC 2.0 4.1).
- MCP 제약: 요청 ID는 문자열·정수, null 금지, 아직 응답을 못 받은 다른 요청과 겹치면 안 된다("Overview" Requests).
- 알림은 응답이 없으므로 보낸 쪽은 실패를 모른다. 실험 4절에서 `notifications/cancelled`는 서버 stderr 로그만 남겼다.

### 3. 무상태화

- 사라진 것: `initialize`/`notifications/initialized` 핸드셰이크, 프로토콜 세션과 `Mcp-Session-Id` 헤더(Key Changes 주요 변경 1·2).
- 대신: 매 요청 `_meta`에 `io.modelcontextprotocol/protocolVersion`·`clientCapabilities`(필수), `clientInfo`(SHOULD). `server/discover` RPC 추가.
- "Overview" Statelessness: 서버는 이전 요청으로 문맥을 세우면 안 되고(MUST NOT), 여러 요청에 걸친 상태는 클라이언트가 매번 넘기는 명시적 식별자로 참조한다(MUST). 연결·프로세스는 세션이 아니다. 부하 분산·재시작·여러 대화의 섞임에서 연결 상태는 믿을 수 없다(해석).

### 4. 옛 버전 요청

- `-32022` UnsupportedProtocolVersion 오류와 `data: {"supported": ["2026-07-28"], "requested": "2025-11-25"}`(실험 1절 출력과 같음).
- 클라이언트는 `supported`에서 자기도 아는 버전을 골라 **새 ID**로 다시 보낸다. 공통 버전이 없으면 사용자에게 오류를 보인다("Versioning", SHOULD). 실험에서는 ID 2의 재요청 한 번으로 해결됐다.

### 5. -32022 재시도 폭주

- 버전 불일치를 일시 오류로 분류해 같은 버전으로 지수 백오프 재시도했다. 기다려도 서버의 지원 버전은 바뀌지 않는다.
- 대처: 응답 분류에서 `-32022`를 따로 처리해 버전을 고르거나 즉시 실패한다(적용 1절 `classify`의 `PickVersion`). 일반 재시도 정책에는 "재시도해서 결과가 달라질 오류인가"를 먼저 묻는다.

### 6. 두 종류의 실패

- 인자 형식 오류(도구 실행 오류): `result`에 `isError: true`와 설명 `content`가 온다. `error` 키는 없다(실험 3절).
- 없는 도구(프로토콜 오류): JSON-RPC `error`, 코드 `-32602`, 메시지 "Unknown tool: …"(실험 2절, "Tools" Error Handling).
- `error`만 실패로 보는 클라이언트는 `isError` 결과를 성공으로 처리한다. 모델에게 오류 설명을 돌려줘 스스로 고치게 하는 경로(SHOULD)도 놓친다.

### 7. ttlMs 경계

- 신선 조건은 `now < t_received + ttlMs`. 299,999ms는 캐시, 300,000ms는 서버(실험 5절 출력과 같음).
- 그 사이 목록 변경 알림이 오면 아직 신선한 캐시라도 즉시 무효가 된다("Caching" Interaction with Notifications). 캐시 키는 메서드 + 결과에 영향을 주는 인자이고, `private` 결과면 인가 문맥도 키에 들어간다.

### 8. 끊긴 스트림

- 2026-07-28판은 SSE 재개(`Last-Event-ID`·이벤트 ID)와 재전달을 제거했다. 끊긴 요청은 잃은 것이고, 클라이언트는 **새 요청 ID로 새 요청**을 보내야 한다(MUST, Key Changes 주요 변경 9).
- 챙길 것: 그 도구가 부작용을 낸다면 첫 요청이 이미 처리됐을 수 있다. 멱등 키를 인자에 넣어 중복 실행을 막는다([api-design/05-idempotency-keys](../../api-design/05-idempotency-keys/2-summary.md)). 모든 요청에는 최대 타임아웃을 둔다("Cancellation" Timeouts, SHOULD).

### 9. annotations

- "Tools": 클라이언트는 신뢰한 서버에서 온 것이 아니면 도구 annotations를 신뢰할 수 없는 것으로 봐야 한다(MUST). annotations는 서버의 자기 설명일 뿐 강제가 아니다.
- 같은 이유로 `serverInfo`도 보안 판단에 쓰지 않는다("Discovery", SHOULD NOT).
- 사용자 확인 여부는 클라이언트 쪽 정책(서버 신뢰 등급·도구 허용 목록)으로 정하고, 도구 호출을 거부할 수 있는 사람을 루프에 둔다("Tools", SHOULD).
