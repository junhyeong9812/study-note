# ai-engineering/21-mcp-protocol — MCP: JSON-RPC 위의 도구 규약, 2026-07-28판 무상태화·discover·캐시·오류 코드 — 정리 (힌트)

## 해결하는 문제

사내에 LLM 애플리케이션이 셋 있고, 각각 주문 조회·재고 조회 도구를 따로 붙였다. 도구 하나를 고치면 세 곳의 연결 코드를 고친다. 다른 팀의 도구를 쓰려면 그 팀의 호출 방식을 다시 익힌다.

- *MCP(Model Context Protocol)*: LLM 애플리케이션(클라이언트)이 외부 서버가 제공하는 **도구(tools)·리소스(resources)·프롬프트(prompts)**를 같은 방식으로 찾고 부르는 규약. 메시지는 JSON-RPC 2.0을 따른다(MCP 명세 2026-07-28 "Overview" — 확인 2026-10-08).
  - *도구*: 모델이 고르고 클라이언트가 실행을 요청하는 함수(예: `get_order`). 이름·설명·입력 JSON 스키마를 가진다.
  - *리소스*: URI로 가리키는 읽을거리(파일·레코드 등). *프롬프트*: 서버가 제공하는 프롬프트 템플릿.
  - 흔한 오해: "MCP = 모델 API" — MCP는 모델을 부르는 규약이 아니라, 모델을 쓰는 애플리케이션이 **도구 쪽**과 말하는 규약이다. 모델 호출은 각 제공자 API([11-llm-api-client-contract](../11-llm-api-client-contract/2-summary.md))가 한다.

쉬운 예: 멀티탭과 플러그 규격.
- 가전마다 콘센트 모양이 다르면 집마다 전용 콘센트를 단다.
- 규격을 정하면 아무 가전이나 아무 콘센트에 꽂는다. 다만 규격이 바뀌는 날(110V → 220V)에는 어느 규격으로 말하는지 서로 확인해야 한다.

똑같은 구조다.\
가전 = 도구 서버, 콘센트 = 애플리케이션, 플러그 규격 = MCP, 전압 확인 = 요청마다 싣는 프로토콜 버전이다.

실무 예:
- 사내 도구를 MCP 서버로 한 번 만들고 여러 에이전트·IDE에서 쓴다.
- 2026-07-28판으로 올리면서 옛 판(2025-11-25)의 초기화·세션에 기대던 코드가 깨진다(⚠ 커리큘럼).
- 버전 불일치 오류(-32022)를 네트워크 오류처럼 재시도한다(⚠).

## 동작·원리

### 1. 메시지 세 종류 — JSON-RPC 2.0

```text
  요청 (Request)        {"jsonrpc":"2.0","id":7,"method":"tools/call","params":{...}}   → 응답 필수
  응답 (Response)       {"jsonrpc":"2.0","id":7,"result":{...}}  또는  {"jsonrpc":"2.0","id":7,"error":{code,message,data}}
  알림 (Notification)   {"jsonrpc":"2.0","method":"notifications/cancelled","params":{...}}  ← id 없음, 응답 없음

  클라이언트 ── id 7 요청 ─►            서버
             ── id 8 요청 ─►
             ◄─ id 8 응답 ──   응답 순서는 요청 순서와 다를 수 있다 → id로 짝을 맞춘다
             ◄─ id 7 응답 ──
```

- JSON-RPC 2.0: `id`가 없는 요청은 알림이고 서버는 응답하면 안 된다(MUST NOT). 그래서 클라이언트는 알림이 실패했는지도 모른다(JSON-RPC 2.0 명세 4.1).
- MCP는 여기에 제약을 더한다: 요청 ID는 문자열이나 정수, **null 금지**, 응답을 아직 못 받은 다른 요청의 ID와 겹치면 안 된다(MCP "Overview" Requests).
- 결과에는 `resultType`이 필수다. 보통 `"complete"`, 추가 입력이 필요하면 `"input_required"`. 옛 서버처럼 이 필드가 없으면 `"complete"`로 취급한다(MUST, 같은 문서).

### 2. 2026-07-28판의 무상태화 — 핸드셰이크가 사라졌다

```text
  2025-11-25 이전 (legacy)                          2026-07-28 (modern)
  ───────────────────────────────                  ──────────────────────────────────────────
  initialize ─► 버전·능력 협상                       (핸드셰이크 없음)
  notifications/initialized                         매 요청 params._meta 에
  Mcp-Session-Id 헤더로 세션 유지                      io.modelcontextprotocol/protocolVersion     (필수)
  tools/call (세션 문맥에 기대어)                        io.modelcontextprotocol/clientCapabilities  (필수)
                                                      io.modelcontextprotocol/clientInfo          (SHOULD)
                                                   서버는 요청 하나만 보고 처리
                                                   여러 요청에 걸친 상태 = 도구 인자로 넘기는 명시적 핸들
```

- Key Changes(2026-07-28 vs 2025-11-25) 주요 변경 1·2: 프로토콜 수준 세션과 `Mcp-Session-Id` 헤더 제거, `initialize`/`notifications/initialized` 핸드셰이크 제거. 요청마다 `_meta`에 버전과 클라이언트 능력을 싣는다.
- "Overview" Statelessness 절: 서버는 같은 연결의 이전 요청으로 문맥(능력·버전·신원)을 세우면 안 된다(MUST NOT). 여러 요청에 걸친 상태는 클라이언트가 매 요청에 넘기는 명시적 식별자로 참조한다(MUST). stdio 프로세스 하나도 "세션"이 아니다.
- 필수 `_meta` 필드가 빠진 요청은 잘못된 요청이다. 서버는 `-32602`(Invalid params)로 거부한다(MUST). HTTP라면 상태 코드 400.
  - *능력(capabilities)*: 클라이언트·서버가 지원하는 기능 목록(예: 서버의 `tools`). 클라이언트가 선언하지 않은 능력이 필요하면 서버는 `-32021`(MissingRequiredClientCapability)을 돌려준다.

### 3. 버전 협상 — 요청마다, 실패하면 고른다

```text
  클라이언트 ─ 요청(_meta.protocolVersion = X) ─► 서버
     ├─ X 지원 ──────────────────────────────► 결과
     └─ X 미지원 ─► error -32022 UnsupportedProtocolVersion
                     data: {"supported": [...], "requested": "X"}
                         └─► 클라이언트: supported 중 하나 골라 **새 ID로** 다시 보냄
                             (공통 버전이 없으면 사용자에게 오류 — 같은 X로 재시도는 무의미)
```

- "Versioning and Compatibility": 협상 핸드셰이크가 없다. 서버는 요청마다 버전을 받아들이거나 거부한다. 미지원이면 `UnsupportedProtocolVersionError`로 지원 버전 목록을 돌려준다(MUST). 클라이언트는 공통 버전을 골라 재시도하거나, 없으면 사용자에게 오류를 보인다(SHOULD).
- `server/discover`: 서버의 구현 의무 RPC(MUST). 지원 버전·능력·신원(`serverInfo`)을 한 번에 돌려준다. 클라이언트가 부르는 것은 선택이다(MAY). stdio에서 옛·새 서버를 모두 상대하는(dual-era) 클라이언트는 다른 요청보다 먼저 `server/discover`로 탐침하라고 권한다(SHOULD, "Discovery"·"stdio" Backward Compatibility). 새 판만 아는 클라이언트에게도 탐침은 RECOMMENDED다 — 옛 서버가 `tools/call`을 옛 의미로 처리해 버리는 대신 결정적으로 실패하게 한다.
  - `serverInfo`는 서버의 자기 신고라 검증되지 않는다. 동작을 바꾸거나 보안 판단에 쓰지 말라고 적는다(SHOULD NOT, "Discovery").
- 판 사이 호환표(같은 문서): 새 클라이언트 × 옛 서버 = 실패, 옛 클라이언트 × 새 서버 = 실패, 양쪽을 다 아는 "dual-era" 구현이 끼면 동작한다. 옛 판에 `initialize`를 보내는 옛 클라이언트에게 새 서버는 지원 버전을 오류에 적어 주라고 권한다(SHOULD).

### 4. 오류 코드 할당 정책

| 구간·코드 | 뜻 (MCP 2026-07-28 "Overview" Error Codes) |
|---|---|
| `-32700`, `-32600`~`-32603` | JSON-RPC 표준 오류(파싱·잘못된 요청·없는 메서드·잘못된 인자·내부 오류) |
| `-32000`~`-32019` | 예전 구현이 쓰던 구간. 새로 할당 금지, `-32002`를 빼면 받는 쪽은 의미를 가정하면 안 됨 |
| `-32020`~`-32099` | MCP 명세 전용. `-32020` HeaderMismatch · `-32021` MissingRequiredClientCapability · `-32022` UnsupportedProtocolVersion |
| `-32002` | 옛 판의 resource not found. 이 판은 `-32602`를 쓰고 `-32002`를 내보내면 안 됨(받는 쪽은 옛 서버 것으로 계속 받아 줌, SHOULD) |
| 그 밖 | 애플리케이션 정의 오류는 JSON-RPC 예약 구간(`-32768`~`-32000`) 밖에 할당(SHOULD) |

- Key Changes 부 변경 12: 이 초안에서 새로 만든 코드를 재번호했다 — `-32001`→`-32020`, `-32003`→`-32021`, `-32004`→`-32022`. 문서·코드에서 옛 번호를 보면 판을 확인한다.
- SDK 안에서 생긴 로컬 오류(예: 요청 타임아웃)는 명세가 코드를 정하지 않았다. 상대가 보낸 오류로 오인되지 않게 하라고 적는다(같은 절).

### 5. 도구 오류의 두 경로와 캐시 가능한 결과

```text
  tools/call 실패
   ├─ 프로토콜 오류: 모르는 도구, 스키마 위반 요청, 서버 오류   → JSON-RPC error (예: -32602 Unknown tool)
   └─ 도구 실행 오류: API 실패, 입력 값 검증, 업무 규칙         → result { isError: true, content: [설명] }
                                                                 모델이 읽고 인자를 고쳐 재시도할 수 있게
```

- "Tools" Error Handling: 클라이언트는 실행 오류를 모델에 넘겨 스스로 고치게 하는 것이 SHOULD, 프로토콜 오류는 넘겨도 되지만(MAY) 회복 가능성이 낮다. 에이전트 쪽 처리는 [20-agent-loop-and-tool-safety](../20-agent-loop-and-tool-safety/2-summary.md).
- "Caching": `server/discover`·`tools/list`·`prompts/list`·`resources/list`·`resources/templates/list`·`resources/read`의 완료 결과에는 `ttlMs`(밀리초 신선도 힌트)와 `cacheScope`(`"public"`/`"private"`)를 싣는 것이 의무다(MUST, "Caching" Cacheable Results). Key Changes 부 변경 5의 목록에는 `server/discover`가 없지만 "Caching"·"Discovery" 페이지는 `server/discover`도 캐시 대상으로 둔다.
  - 신선 조건: `now < t_received + ttlMs`. `ttlMs`가 없으면 0(바로 오래됨)으로 본다. 음수면 무시하고 0으로(SHOULD).
  - 캐시 키 = 메서드 + 결과에 영향을 주는 인자(`resources/read`의 `uri`, 페이지 `cursor` 등). 다른 인자의 요청에 캐시를 내주면 안 된다(MUST NOT).
  - `"private"` 결과는 같은 인가 문맥(같은 접근 토큰)에서만 재사용한다(MUST NOT 공유). `"public"`이라도 접근 제어를 `cacheScope`에만 맡기면 안 된다(MUST NOT, 보안 고려).
  - TTL은 폴링 주기가 아니다. 필요할 때 신선도를 보고, 오래됐을 때만 다시 가져온다(SHOULD NOT 자동 재조회). 폴링한다면 지터와 백오프 필수(MUST).
  - 목록 변경 알림(`notifications/tools/list_changed`)이 오면 아직 신선한 캐시도 즉시 무효다.

### 6. 전송 — stdio와 Streamable HTTP

- *stdio*: 클라이언트가 서버를 자식 프로세스로 띄우고, 한 줄에 JSON-RPC 메시지 하나(내부 줄바꿈 금지)를 stdin/stdout으로 주고받는다. 서버의 stdout에는 MCP 메시지 외에 아무것도 쓰면 안 되고(MUST NOT), 로그는 stderr로(MAY). 취소는 `notifications/cancelled`로 요청 ID를 지목한다(MUST, "stdio"). stdin이 닫히면 서버가 끝나는 것이 기본 종료 신호다.
- *Streamable HTTP*: 메시지마다 HTTP POST, 응답은 JSON 하나 또는 요청 단위 SSE 스트림("Transports"). 버전은 `MCP-Protocol-Version` 헤더에도 비친다. 취소는 응답 스트림을 닫는 것.
- Key Changes 주요 변경 9: SSE 스트림 재개(`Last-Event-ID`·이벤트 ID)와 메시지 재전달이 제거됐다. 끊긴 응답 스트림의 요청은 잃은 것이고, 클라이언트는 **새 요청 ID로 새 요청**을 보내야 한다(MUST). 부작용 있는 도구라면 그 재요청에 멱등 키가 필요하다([api-design/05-idempotency-keys](../../api-design/05-idempotency-keys/2-summary.md)).
- 모든 요청에 타임아웃을 두고, 시간이 지나면 취소하고 기다림을 멈춘다(SHOULD, "Cancellation"). 진행 알림으로 시계를 늘릴 수는 있어도 최대 타임아웃은 지킨다(SHOULD).

### 실험: 로컬 stdio 모형 서버·클라이언트

환경: 호스트 Python 3.12.3 표준 라이브러리(`python3 -I client.py` — 클라이언트가 `server.py`를 자식 프로세스로 띄움), 2026-10-08. **MCP 2026-07-28 형식을 흉내 낸 모형**이다 — 공식 SDK가 아니고, 메서드는 `server/discover`·`tools/list`·`tools/call`과 알림만 구현했다.

```python
# server.py 발췌 — 요청마다 _meta를 검사하고, 상태 없이 처리
def handle(m):
    if "id" not in m:              # 알림: 응답하지 않는다
        sys.stderr.write(f"[server] notification {m.get('method')} 받음, 응답 없음\n"); return
    id_ = m["id"]
    if id_ is None or m.get("jsonrpc") != "2.0" or not isinstance(m.get("method"), str):
        return err(None, -32600, "Invalid Request")
    meta = (m.get("params") or {}).get("_meta") or {}
    if m["method"] == "initialize":   # 옛(legacy) 핸드셰이크
        return err(id_, -32601, "Method not found: initialize (modern-only server)", {"supported": SUPPORTED})
    v = meta.get("io.modelcontextprotocol/protocolVersion")
    if v is None or "io.modelcontextprotocol/clientCapabilities" not in meta:
        return err(id_, -32602, "Invalid params: missing required _meta fields")
    if v not in SUPPORTED:
        return err(id_, -32022, "Unsupported protocol version", {"supported": SUPPORTED, "requested": v})
```

(실험, Python 3.12.3, 2026-10-08 — 출력 줄은 160자에서 자름)

```text
== 1. 버전 불일치: 옛 버전으로 요청 → -32022 → supported에서 골라 새 ID로 1회 재요청
  → {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2025-11-25", "io.modelcontextprotocol/clien
  ← {"jsonrpc": "2.0", "id": 1, "error": {"code": -32022, "message": "Unsupported protocol version", "data": {"supported": ["2026-07-28"], "requested": "2025-11-25"
  클라이언트: 같은 버전 재시도는 무의미, 고른 버전 = 2026-07-28
  → {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clien
  ← {"jsonrpc": "2.0", "id": 2, "result": {"resultType": "complete", "tools": [{"name": "get_order", "description": "주문 조회", "inputSchema": {"type": "object", "prop
  결과 tools = ['get_order', 'slow_report'] ttlMs = 300000
== 2. _meta 없음 / 옛 initialize / 모르는 도구 / id=null
  → {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}}
  ← {"jsonrpc": "2.0", "id": 3, "error": {"code": -32602, "message": "Invalid params: missing required _meta fields"}}
  → {"jsonrpc": "2.0", "id": 4, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}}}
  ← {"jsonrpc": "2.0", "id": 4, "error": {"code": -32601, "message": "Method not found: initialize (modern-only server)", "data": {"supported": ["2026-07-28"]}}}
  → {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "delete_everything", "arguments": {}, "_meta": {"io.modelcontextprotocol/protocolVersion"
  ← {"jsonrpc": "2.0", "id": 5, "error": {"code": -32602, "message": "Unknown tool: delete_everything"}}
  → {"jsonrpc": "2.0", "id": null, "method": "tools/list"}
  ← {"jsonrpc": "2.0", "id": null, "error": {"code": -32600, "message": "Invalid Request"}}
  ! 대응하는 요청 없음: None
== 3. 도구 실행 오류(isError=true)는 JSON-RPC 오류가 아니라 결과
  → {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "get_order", "arguments": {"orderId": "42"}, "_meta": {"io.modelcontextprotocol/protocolV
  ← {"jsonrpc": "2.0", "id": 6, "result": {"resultType": "complete", "content": [{"type": "text", "text": "orderId 형식 오류: '42' (예: o-42)"}], "isError": true, "_meta
  isError = True / 'error' 키 있음 = False
== 4. 알림은 응답이 없다 + 응답 순서는 요청 순서와 다를 수 있다
  → {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": "999", "reason": "demo"}}
  → {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "slow_report", "arguments": {}, "_meta": {"io.modelcontextprotocol/protocolVersion": "202
  → {"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "get_order", "arguments": {"orderId": "o-7"}, "_meta": {"io.modelcontextprotocol/protocol
  [stderr] [server] notification notifications/cancelled 받음, 응답 없음
  ← {"jsonrpc": "2.0", "id": 8, "result": {"resultType": "complete", "content": [{"type": "text", "text": "o-7: 배송 중"}], "isError": false, "_meta": {"io.modelcontex
  ← {"jsonrpc": "2.0", "id": 7, "result": {"resultType": "complete", "content": [{"type": "text", "text": "report ready"}], "isError": false, "_meta": {"io.modelcon
  ID 대응: 7 → report ready | 8 → o-7: 배송 중
== 5. ttlMs 캐시: 키 = 메서드 + 결과에 영향을 주는 인자
  → {"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clien
  ← {"jsonrpc": "2.0", "id": 9, "result": {"resultType": "complete", "tools": [{"name": "get_order", "description": "주문 조회", "inputSchema": {"type": "object", "prop
  t=      0ms → 서버
  t= 120000ms → 캐시
  t= 299999ms → 캐시
  → {"jsonrpc": "2.0", "id": 10, "method": "tools/list", "params": {"_meta": {"io.modelcontextprotocol/protocolVersion": "2026-07-28", "io.modelcontextprotocol/clie
  ← {"jsonrpc": "2.0", "id": 10, "result": {"resultType": "complete", "tools": [{"name": "get_order", "description": "주문 조회", "inputSchema": {"type": "object", "pro
  t= 300000ms → 서버
  서버 호출 수(이 절) = 2
server exit code = 0
```

- 1절: `-32022`는 "지금 안 됨"이 아니라 "이 버전으로는 영원히 안 됨"이다. 같은 버전 재시도는 의미가 없고, `data.supported`에서 고른 버전으로 **새 ID**의 요청 하나를 보내 해결됐다.
- 2절: `_meta`가 없으면 `-32602`, 옛 `initialize`는 이 모형 서버에서 `-32601`(명세는 이 경우의 코드를 구현 정의로 둔다 — 호환표 "Legacy × Modern"). 모르는 도구는 프로토콜 오류 `-32602`. `id: null`에 대한 오류 응답도 `id: null`이라 클라이언트는 어느 요청의 것인지 대응할 수 없었다(`! 대응하는 요청 없음`).
- 3절: 형식이 틀린 인자는 `result.isError = true`로 돌아왔다. `error` 키가 없으므로 "JSON-RPC 오류만 실패로 보는" 클라이언트는 이것을 성공으로 처리한다.
- 4절: 알림에는 응답이 없었다(서버 stderr 로그만). 이 모형은 응답 없음만 보이려고 보낸 적 없는 ID `"999"`를 지목했다 — 명세는 취소 알림이 보낸 적 있고 진행 중인 요청만 가리키라고 하며(MUST), 모르는 ID의 취소는 서버가 무시해도 되고(MAY, Behavior Requirements) 무시하는 것이 권장이다(SHOULD, Error Handling — "Cancellation"). 느린 요청 7보다 빠른 요청 8의 응답이 먼저 왔고, 클라이언트는 `id` → 대기 큐 해시맵으로 짝을 맞췄다. stderr 줄의 출력 위치는 실행마다 달라질 수 있다(별도 스트림).
- 5절: `ttlMs: 300000`이면 299,999ms까지 캐시, 300,000ms에 다시 가져왔다(`now < t + ttlMs`). 서버 호출은 4번 필요 중 2번이었다.

## 쓰이는 자료구조·알고리즘

- **요청 ID → 대기 슬롯 해시맵**: 보낼 때 등록, 응답의 `id`로 꺼낸다. 응답 순서와 무관하게 O(1) 대응. 타임아웃이 나면 항목을 지우고 취소 알림을 보낸다 — [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md).
- **능력 협상 = 집합 교집합**: 클라이언트 지원 버전 목록과 서버 `supported` 목록의 교집합에서 가장 새 것을 고른다.
- **TTL 캐시**: 키 = (메서드, 영향 인자, 인가 문맥 — `private`일 때), 값 = (받은 시각, 결과). 알림이 오면 무효화. 만료 처리는 [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md)·[data-structure/26-timer-structures](../../data-structure/26-timer-structures/2-summary.md).
- **줄 단위 프레이밍**: stdio는 한 줄 = 한 메시지. 버퍼에서 `\n`까지 읽어 JSON 파싱.

## 적용 — 풀어나가는 법

### 1. 클라이언트를 만들거나 SDK를 올릴 때 — 증상 → 원리 → 코드

1. **증상**: 판 업그레이드 뒤 "Unsupported protocol version"·"missing _meta"·세션 오류, 혹은 도구가 간헐적으로 다른 사용자 문맥으로 동작.
2. **원리**: 요청 하나가 버전·능력·신원을 모두 싣는가 → 버전 오류를 일시 오류와 구분하는가 → 요청 사이 상태를 연결·세션에 두지 않았는가 → 캐시 키에 인가 문맥이 들어가는가.
3. **코드로 확인** — 응답 분류(Java 21, JSON 파싱은 사용하는 라이브러리 몫이라 `Map`으로 받았다고 가정)

```java
sealed interface Outcome permits Done, ToolFailed, PickVersion, Fatal {}
record Done(Map<String, Object> result) implements Outcome {}
record ToolFailed(String text) implements Outcome {}                 // 모델에 돌려줄 실행 오류
record PickVersion(List<String> supported) implements Outcome {}      // 새 ID로 1회 재요청
record Fatal(int code, String message) implements Outcome {}          // 재시도 안 함

@SuppressWarnings("unchecked")
static Outcome classify(Map<String, Object> resp) {
    if (resp.get("error") instanceof Map<?, ?> e) {
        int code = ((Number) e.get("code")).intValue();
        if (code == -32022) {                                         // UnsupportedProtocolVersion (2026-07-28)
            var data = (Map<String, Object>) e.get("data");
            return new PickVersion((List<String>) data.get("supported"));
        }
        return new Fatal(code, String.valueOf(e.get("message")));   // -32602 등: 요청을 고쳐야 함
    }
    var result = (Map<String, Object>) resp.get("result");
    String type = (String) result.getOrDefault("resultType", "complete");   // 없으면 complete (옛 서버)
    if (!type.equals("complete")) return new Fatal(0, "unsupported resultType: " + type); // MRTR 미구현이면
    if (Boolean.TRUE.equals(result.get("isError"))) return new ToolFailed(String.valueOf(result.get("content")));
    return new Done(result);
}
```

(실험, JDK 21 temurin, 2026-10-08 — 실험 1·3절과 같은 모양의 응답 맵 세 개를 넣어 실행. 입력을 `Map.of`로 만들어 맵 출력의 키 순서는 JVM 실행마다 바뀐다 — 재실행 4회 중 3회는 `{tools=[], resultType=complete}` 순서)

```text
PickVersion[supported=[2026-07-28]]
ToolFailed[text=[{type=text, text=orderId 형식 오류}]]
Done[result={resultType=complete, tools=[]}]
```

- 이 분류가 없으면 `-32022`는 "오류 → 지수 백오프 재시도"로 흘러가 같은 버전을 계속 보낸다(⚠). `isError`는 성공으로 흘러가 모델이 오류 문자열을 정답처럼 쓴다.
- 인식하지 못한 `resultType`은 무효로 취급해야 한다(MUST, "Overview" ResultType). 위 코드는 다중 왕복(MRTR)을 구현하지 않은 클라이언트라 `input_required`도 처리하지 않고 실패로 끝낸다.

### 2. 서버를 만들 때 점검표

| 항목 | 2026-07-28 기준 |
|---|---|
| 요청마다 `_meta` 검사 | 버전·능력 필수 필드 없으면 `-32602` |
| 미지원 버전 | `-32022` + `data.supported`·`requested` |
| `server/discover` | 구현 필수, `ttlMs`·`cacheScope` 포함 |
| 목록·읽기 결과 | `ttlMs`·`cacheScope` 필수, `tools/list`는 결정적 순서(SHOULD — 프롬프트 캐시 적중에도 유리) |
| 상태 | 연결·프로세스에 두지 않음, 필요하면 명시적 핸들을 도구 인자로 |
| 도구 오류 | 실행 오류는 `isError`, 프로토콜 오류는 JSON-RPC error |
| stdio | stdout엔 MCP 메시지만, 로그는 stderr |
| 보안 | 모든 입력 검증, 접근 제어, 호출 레이트 리밋, 출력 정제(MUST, "Tools" Security Considerations) |

- 버전·호환 설계 일반론은 [api-design/07-versioning-and-compatibility](../../api-design/07-versioning-and-compatibility/2-summary.md), 스트리밍 RPC 비교는 [api-design/16-grpc-streaming-modes](../../api-design/16-grpc-streaming-modes/2-summary.md).

## 장애 시나리오와 대처

### 1. -32022를 일시 오류로 보고 재시도 반복 (⚠)

- 현상: 서버 업그레이드 뒤 특정 클라이언트의 도구 호출이 전부 실패, 재시도 로그가 쌓인다.
- 보이는 형태: 같은 `protocolVersion`으로 같은 오류 `-32022`가 백오프 간격으로 반복된다.
- 원인: 재시도 분류가 "오류 = 재시도"였다. 버전 불일치는 기다려도 풀리지 않는다.
- 대처: `-32022`는 `data.supported`에서 버전을 골라 새 ID로 1회 재요청, 공통 버전이 없으면 즉시 사용자 오류. 재시도 분류는 [reliability/06-retry-backoff-jitter](../../reliability/06-retry-backoff-jitter/2-summary.md)의 "재시도해도 되는 오류인가" 질문부터.

### 2. 옛 판의 세션에 기대던 코드와 혼용 → 요청 사이 상태 유실 (⚠)

- 현상: 2026-07-28 서버로 옮긴 뒤 "앞에서 고른 주문"을 다음 도구 호출이 모른다.
- 보이는 형태: 같은 연결에서 연달아 부른 도구가 서로의 결과를 못 본다. 부하 분산기 뒤에서는 더 자주.
- 원인: 옛 판의 `Mcp-Session-Id`·연결 문맥에 상태를 뒀다. 새 판은 세션을 없앴고 서버는 이전 요청에 기대면 안 된다.
- 대처: 상태가 필요하면 서버가 핸들(예: `cartId`)을 발급하고 클라이언트가 도구 인자로 매번 넘긴다(Key Changes 주요 변경 1). 옛·새 서버를 모두 상대해야 하면 dual-era로 만들고 stdio에선 `server/discover`로 탐침.

### 3. 끊긴 스트림의 재개를 기다림 (⚠)

- 현상: 네트워크가 잠깐 끊긴 뒤 긴 도구 호출의 결과가 영영 오지 않는다.
- 보이는 형태: 클라이언트가 `Last-Event-ID`로 재연결을 시도하지만 서버는 이어 주지 않는다.
- 원인: 2026-07-28판에서 SSE 재개·재전달이 제거됐다. 끊긴 요청은 잃은 것이다.
- 대처: 새 요청 ID로 다시 보낸다(MUST). 부작용 도구면 멱등 키를 인자에 넣어 중복 실행을 막는다. 아주 긴 작업은 tasks 확장 같은 비동기 패턴을 검토한다(Key Changes 주요 변경 6 — 이 노트에서는 다루지 않음).

### 4. 신뢰하지 않은 서버의 annotations를 믿고 확인 생략 (⚠)

- 현상: "읽기 전용" 표시가 붙은 도구라 사용자 확인 없이 실행했는데 데이터가 바뀌었다.
- 보이는 형태: 도구 정의의 `annotations`에 `readOnlyHint: true`, 실제 동작은 쓰기.
- 원인: annotations는 서버의 자기 설명이다. 명세는 신뢰한 서버가 아니면 annotations를 신뢰할 수 없는 것으로 보라고 한다(MUST, "Tools"). `serverInfo`도 같은 이유로 보안 판단에 쓰지 않는다.
- 대처: 확인 여부는 클라이언트 쪽 정책(서버별 신뢰 등급·도구 허용 목록)으로 정한다. 인젝션·권한 경계는 [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md).

### 5. public 캐시에 사용자별 목록이 섞임

- 현상: 게이트웨이를 거친 뒤 어떤 사용자에게 권한 없는 도구가 목록에 보인다.
- 보이는 형태: `tools/list`가 인가 범위에 따라 달라지는 서버인데 결과의 `cacheScope`가 `"public"`.
- 원인: 공유 캐시가 다른 인가 문맥의 결과를 내줬다. 명세는 `tools/list`가 요청의 인가에 따라 달라질 수 있다고 허용한다("Tools" Capabilities).
- 대처: 사용자별로 달라지는 결과는 `"private"`, 캐시 키에 인가 문맥을 넣는다. 서버는 `cacheScope`와 별개로 도구 호출마다 접근 제어를 한다(MUST).

## 핵심 문장

- MCP는 LLM 애플리케이션이 도구·리소스·프롬프트를 같은 방식으로 찾고 부르는 JSON-RPC 2.0 규약이다.
- 2026-07-28판은 초기화 핸드셰이크와 세션을 없앴다. 요청마다 `_meta`에 버전·능력을 싣고, 요청 사이 상태는 명시적 핸들로 넘긴다.
- `-32022` UnsupportedProtocolVersion은 일시 오류가 아니다. `supported`에서 골라 새 ID로 한 번 다시 보낸다.
- 도구 실행 오류는 `isError: true` 결과로, 프로토콜 오류는 JSON-RPC error로 온다. 둘을 다르게 처리한다.
- 목록·읽기 결과의 `ttlMs`·`cacheScope`는 신선도와 공유 범위 힌트다. 사용자별 결과는 private로 두고 접근 제어는 따로 한다.
- 끊긴 스트림은 재개되지 않는다(2026-07-28). 새 요청 ID로 다시 보내고, 부작용 도구는 멱등 키로 지킨다.

## 관련 주제·근거

- 선행
  - [14-structured-output-and-tool-calling](../14-structured-output-and-tool-calling/2-summary.md) — 도구 계약과 JSON 스키마
  - [api-design/01-api-as-contract](../../api-design/01-api-as-contract/2-summary.md)
- 후속·연결
  - [20-agent-loop-and-tool-safety](../20-agent-loop-and-tool-safety/2-summary.md) · [22-prompt-injection-and-llm-security](../22-prompt-injection-and-llm-security/2-summary.md)
  - [api-design/07-versioning-and-compatibility](../../api-design/07-versioning-and-compatibility/2-summary.md) · [api-design/16-grpc-streaming-modes](../../api-design/16-grpc-streaming-modes/2-summary.md) · [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md)
- 명세(모두 2026-10-08 확인, 현재 판 = 2026-07-28 — "Versioning" 페이지)
  - MCP 2026-07-28 Key Changes — 주요 변경 1(세션 제거)·2(핸드셰이크 제거, `_meta`)·3(`server/discover`)·8(`resultType`)·9(SSE 재개 제거, 새 ID 재발행 MUST), 부 변경 5(`ttlMs`·`cacheScope`)·6(`-32002`→`-32602`)·12(오류 코드 구간·재번호) <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
  - MCP 2026-07-28 Overview(Messages·Error Codes·Statelessness·`_meta`) <https://modelcontextprotocol.io/specification/2026-07-28/basic>
  - MCP 2026-07-28 Versioning and Compatibility(요청별 협상·호환표) <https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning>
  - MCP 2026-07-28 Discovery <https://modelcontextprotocol.io/specification/2026-07-28/server/discover> · Caching <https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching> · Tools <https://modelcontextprotocol.io/specification/2026-07-28/server/tools> · stdio <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio> · Cancellation <https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation>
  - JSON-RPC 2.0 Specification — 4.1 Notification, 5.1 Error object(예약 구간 `-32768`~`-32000`) <https://www.jsonrpc.org/specification>
- 실험 목록(2026-10-08)
  - MCP 형식 모형 stdio 서버·클라이언트(호스트 Python 3.12.3 표준 라이브러리, `python3 -I`) — 버전 오류 처리, `_meta` 누락·옛 `initialize`·모르는 도구·`id: null`, `isError` 결과, 알림 무응답과 순서 뒤바뀐 응답의 ID 대응, `ttlMs` 캐시 경계(299,999 / 300,000ms)
  - 적용 1절 `classify` 실행(eclipse-temurin:21-jdk 컨테이너, JDK 21.0.12, 네트워크 없음)
