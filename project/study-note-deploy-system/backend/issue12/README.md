# issue12 — 채팅 오케스트레이션: 상태는 서버, 문서는 git, 답은 스트림

- 이슈 #25 · PR: #26·#27·#28·#29

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "backend가 오케스트레이션 맡음"      ──▶   왜 별도 채팅 서버를 안 만들었나 →
>  (한 줄)                                    상태·컨텍스트가 여기 있어서 (서사)
> 구조를 트리 한 덩어리로               ──▶   요청 흐름 ASCII + 각 결정의 문제→선택
> "쿠키엔 id만" 이유를 두 줄로          ──▶   [내용을 쿠키에] ↔ [id만] 나란히 비교
> 0바이트 버그를 문단으로               ──▶   [chunked] ↔ [Content-Length] before/after diff
> "박아" 등 표현                        ──▶   순화 + 실제 커밋 diff로 교체
> ```

---

## 1. 배경 — 채팅의 어려운 부분은 모델 호출이 아니다

문서를 보다가 "이 부분 설명해줘"라고 물으면 답해주는 채팅 기능을 붙이는 게 이 이슈다.
언뜻 "모델(LLM)에 질문을 던지고 답을 받으면 끝" 같지만, 실제로 손이 많이 가는 곳은
모델 호출이 아니라 **그 주변**이다.

- **상태(세션·대화 이력):** 누가 어떤 문서에 대해 무슨 대화를 나눴는지 기억해야 한다.
  두 번째 질문은 첫 질문의 맥락 위에서 답해야 하기 때문이다.
- **컨텍스트 조립:** 모델에게 "이 문서를 근거로 답하라"고 시키려면, 그 문서의 원문 +
  최근 대화 + 새 질문을 하나의 요청으로 엮어 줘야 한다.

이 두 재료 — 문서와 대화 상태 — 가 전부 backend에 있다. 문서는 backend가 git에서 읽고,
대화 이력은 backend가 Redis에 쌓는다. 그래서 **별도 채팅 서버를 새로 만들지 않고**
backend가 오케스트레이션(여러 조각을 순서대로 엮어 하나의 흐름으로 지휘하는 것)을
맡기로 했다. 재료가 여기 있는데 다른 서버로 옮겨 조립하는 건 낭비다.

> 용어 — 오케스트레이션(orchestration): 세션 확인 → 이력 로드 → 문서 로드 → 모델 호출
> → 이력 저장을 순서대로 지휘하는 것. LLM: 대형 언어 모델(여기선 별도 llm 서버가 담당).

---

## 2. 구조 — 요청 하나가 답이 되기까지

`POST /api/chat`에 문서 경로와 질문을 담아 보내면(세션 쿠키 동반) 다음 순서로 흐른다.

```
POST /api/chat {doc_path, question}   (+ chat_session 쿠키)
   │
   ├─(1) 세션: 쿠키 없으면 UUID 발급(HttpOnly)·있으면 형식(36자 uuid) 검증
   │
   ├─(2) 이력: Redis  chat:{session}:{docPath}  리스트에서 최근 대화 로드 (TTL 7일)
   │
   ├─(3) 컨텍스트: git에서 doc_path 원문 로드
   │        → messages = [system(문서 원문) + 최근 10턴 + 새 질문]
   │
   ├─(4) 모델: llm /chat 에 messages 전송 → 토큰을 스트림으로 받음
   │        → ResponseBodyEmitter 로 front에 청크째 중계
   │
   └─(5) 완료 후: 사용자 질문 + 모델 답변을 Redis 이력에 append (TTL 연장)
```

이 흐름에서 내려야 했던 두 개의 설계 결정이 이 이슈의 핵심이다.

### 결정 A — 쿠키에는 "세션 id"만, 대화 내용은 서버(Redis)에

대화 상태를 어디에 둘지가 첫 갈림길이었다.

```
[대안]  대화 내용을 쿠키에 담아 매 요청에 실어 나른다
   문제: (1) 쿠키는 4KB 한계 — 대화가 길어지면 넘침
         (2) 매 요청마다 전체 대화를 왕복 = 낭비
         (3) 클라이언트가 쿠키를 고칠 수 있음 = 변조 가능

[채택]  쿠키엔 세션 id(UUID)만, 내용은 Redis에 (서버가 정본)
   쿠키 = 열쇠 하나, Redis = 금고.  변조·용량·왕복 문제 전부 사라짐
```

세션 id 발급도 backend가 중앙에서 한다 — 쿠키가 없거나 형식이 안 맞으면 새로 발급하고,
맞으면 그대로 쓴다.

`src/main/kotlin/xyz/junproject/backend/chat/api/ChatController.kt` (신규)

```kotlin
private val sessionPattern = Regex("^[0-9a-f-]{36}$")

private fun sessionOf(request: HttpServletRequest, response: HttpServletResponse): String {
    val existing = request.cookies?.firstOrNull { it.name == "chat_session" }?.value
    if (existing != null && sessionPattern.matches(existing)) return existing
    val issued = UUID.randomUUID().toString()
    response.addCookie(Cookie("chat_session", issued).apply {
        isHttpOnly = true; path = "/"; maxAge = 60 * 60 * 24 * 30
    })
    return issued
}
```

> 용어 — HttpOnly: 자바스크립트가 이 쿠키를 못 읽게 막는 표시(스크립트로 세션 탈취
> 방지). UUID: 충돌이 사실상 없는 무작위 식별자.

이력은 Redis 리스트에 쌓고, 대화가 이어질 때마다 7일 TTL(수명)을 다시 연장한다.

`src/main/kotlin/xyz/junproject/backend/chat/usecase/ChatService.kt` (신규)

```kotlin
private fun key(sessionId: String, docPath: String) = "chat:$sessionId:$docPath"

private fun append(sessionId: String, docPath: String, message: ChatMessage) {
    val redisKey = key(sessionId, docPath)
    redis.opsForList().rightPush(redisKey, objectMapper.writeValueAsString(message))
    redis.expire(redisKey, TTL)           // 대화가 이어지는 동안 수명 연장
}
```

### 결정 B — 문서는 "경로"만 받고, 내용은 backend가 git에서 읽는다

두 번째 갈림길은 "모델에 줄 문서 원문을 누가 싣느냐"였다.

```
[대안]  front가 문서 내용을 요청 본문에 실어 보낸다
   문제: (1) 문서가 수십 KB — 질문마다 그만큼 왕복 = 낭비
         (2) front가 보낸 "문서"를 믿어야 함 = 변조·주입 가능

[채택]  front는 doc_path(경로)만 보냄, backend가 git에서 직접 읽음
   내용의 정본 = git.  "첫 대화인가"도 Redis 키 존재로 backend가 판단
```

`ChatService`가 문서 원문 + 최근 이력 + 새 질문을 하나의 messages로 조립한다:

```kotlin
private fun buildMessages(docPath: String, historyItems: List<ChatMessage>, question: String):
        List<Map<String, String>> {
    val document = try { source.readFile(docPath).take(DOC_CONTEXT_CHARS) } catch (_: Exception) { "" }
    val system = "너는 공부 노트 위키의 문서 도우미다. 아래 문서를 근거로 한국어로 답한다. " +
        "문서에 없는 내용은 추측하지 말고 문서에 없다고 말한다.\n\n[문서: $docPath]\n$document"
    return buildList {
        add(mapOf("role" to "system", "content" to system))
        historyItems.takeLast(HISTORY_TURNS).forEach {
            add(mapOf("role" to it.role, "content" to it.content))
        }
        add(mapOf("role" to "user", "content" to question))
    }
}
```

`HISTORY_TURNS`(최근 10턴)와 `DOC_CONTEXT_CHARS`(문서 12,000자 상한)는 모델에 싣는 양의
상한으로, 실제 적정값은 `[구현 검증]` 태그로 남겼다.

---

## 3. 답을 스트림으로 흘리기 — ResponseBodyEmitter

모델 답변은 한 번에 완성되지 않고 토큰(글자·단어 조각)이 순차로 나온다. 사용자가 답을
다 만들 때까지 빈 화면을 보게 하지 않으려면, backend가 llm에서 받은 토큰을 **받는 족족
front로 흘려보내야** 한다.

Spring에는 이런 스트리밍을 위한 WebFlux(리액티브)라는 큰 도구가 있지만, 그걸 도입하면
프로젝트 전체를 리액티브로 바꿔야 한다. 여기선 그럴 필요 없이 MVC(기존 방식)의
`ResponseBodyEmitter` 하나로 충분했다 — 백그라운드 스레드에서 토큰을 `send`하면 그대로
front로 나간다.

`src/main/kotlin/xyz/junproject/backend/chat/api/ChatController.kt`

```kotlin
val emitter = ResponseBodyEmitter(180_000L)
streamExecutor.execute {
    try {
        chatService.chat(requestId, sessionId, docPath, question) { token ->
            emitter.send(token, MediaType.TEXT_PLAIN)
        }
        emitter.complete()
    } catch (error: Exception) {
        requestLog.log(requestId, "chat failed: ${error.message?.take(150)}", "error")
        runCatching { emitter.send("\n[오류] 응답 생성에 실패했습니다. 잠시 후 다시 시도해주세요.") }
        emitter.completeWithError(error)   // complete 누락 = 연결·스레드 누수
    }
}
return emitter
```

> 용어 — ResponseBodyEmitter: 응답을 한 번에 다 만들지 않고 여러 번에 나눠 흘려보내는
> Spring MVC 객체. `send`로 조각을 보내고, 끝나면 반드시 `complete()`(또는 오류 시
> `completeWithError`)로 닫아야 한다 — 안 닫으면 연결과 스레드가 새어 나간다.

llm에서 토큰을 실제로 받아오는 쪽은 java `HttpClient`의 스트리밍 바디로 구현했다:

`src/main/kotlin/xyz/junproject/backend/shared/infra/LlmChatStreamClient.kt` (신규)

```kotlin
val response = client.send(request, HttpResponse.BodyHandlers.ofInputStream())
check(response.statusCode() == 200) { "llm chat status ${response.statusCode()}" }
response.body().use { input ->
    val buffer = ByteArray(512)
    while (true) {
        val read = input.read(buffer)
        if (read == -1) break
        onToken(String(buffer, 0, read, Charsets.UTF_8))
    }
}
```

`usecase`는 포트(인터페이스)만 알고, 실제 HTTP 구현은 `shared/infra`에 둔다(DIP — issue8).

`src/main/kotlin/xyz/junproject/backend/chat/usecase/ports.kt` (신규)

```kotlin
interface ChatStreamPort {
    fun stream(requestId: String, messages: List<Map<String, String>>, onToken: (String) -> Unit)
}
interface EscalatePort {
    val available: Boolean
    fun ask(requestId: String, prompt: String): String
}
```

---

## 4. 에스컬레이션 브리지, 그리고 후속 수정 3건

기본 답변은 llm 서버가 하지만, 더 좋은 답이 필요하면 **PC에서 도는 Claude Code로
넘기는(에스컬레이션)** 경로를 하나 더 뒀다. backend가 PC의 파이썬 브리지(`http.server`)에
프롬프트를 POST하는 어댑터다. PC가 오프라인이거나 미설정이면 `available=false`가 되어
호출부가 봉투 오류(`escalate_unavailable`)로 안내한다.

이 배선을 붙인 뒤 후속 커밋 3건에서 실제 문제를 잡았다.

### #27 (3f4c1dd) — 브리지 URL 배선 (미설정 시 우아한 부재)

`docker-compose.yml`에 `CLAUDE_BRIDGE_URL`을 넘기되, 비어 있어도 앱이 죽지 않고
`escalate_unavailable`로 조용히 빠지도록 기본값을 뒀다.

```yaml
CLAUDE_BRIDGE_URL: ${CLAUDE_BRIDGE_URL:-} # 에스컬레이션 브리지(PC 역터널+socat) — 비우면 escalate_unavailable
```

### #28 (44c4f52) — "0바이트 파싱 오류" 사건 (chunked vs Content-Length)

**상황:** backend가 브리지에 `RestClient`로 프롬프트를 POST하는데, 로컬 테스트와 socat
중계까지는 되던 것이 **backend → 브리지 구간에서만** 실패했다.

**로그:**
```
escalate failed: 500 Internal Server Error:
  "{"error": "Expecting value: line 1 column 1 (char 0)"}"
```
브리지가 요청 본문을 **0바이트로** 읽었다는 뜻이다(그래서 JSON 파싱이 1열 1행에서 실패).

**좁힌 과정:** 같은 요청을 `curl`로 보내면 성공한다 → 서버가 아니라 **클라이언트 차이**다.
Spring `RestClient`에 `Map` 본문을 주면 길이를 미리 못 정하고 **chunked transfer-encoding**
(본문을 길이 없이 조각으로 흘리는 방식)으로 나가는데, 파이썬 기본 `http.server`는
`Content-Length`(본문 길이)를 보고 그만큼만 읽도록 만들어져 있어 **chunked 요청 본문을
읽지 못한다** — 그래서 0바이트로 잡힌 것이다.

> 용어 — chunked transfer-encoding: 본문 전체 길이를 미리 모를 때 조각(chunk) 단위로
> 흘려보내는 HTTP 전송 방식. Content-Length: 본문의 총 바이트 수를 헤더에 명시하는 방식.
> 소박한 서버는 후자만 이해하는 경우가 많다.

**수정:** 본문을 `Map`이 아니라 **바이트 배열**로 만들어 넘긴다 — 그러면 `RestClient`가
길이를 알아 `Content-Length`를 명시하고, chunked로 나가지 않는다.

`src/main/kotlin/xyz/junproject/backend/shared/infra/ClaudeBridgeClient.kt`

```kotlin
// [기존] Map 본문 → chunked 로 나감 → 브리지가 0바이트로 읽음
val response = client.post().uri("/ask")
    .header("Content-Type", "application/json")
    .header("X-Request-Id", requestId)
    .body(mapOf("prompt" to prompt))
    .retrieve().body(Map::class.java) ?: error("bridge: empty response")
```

```kotlin
// [변경] byte[] 본문 → Content-Length 명시 → 브리지가 정상 수신
val payload = objectMapper.writeValueAsBytes(mapOf("prompt" to prompt))
val response = client.post().uri("/ask")
    .header("Content-Type", "application/json; charset=utf-8")
    .header("X-Request-Id", requestId)
    .body(payload)
    .retrieve().body(Map::class.java) ?: error("bridge: empty response")
```

### #29 (b79040f) — 브리지 인증 (codex F2, 원격 실행 표면 차단)

듀얼 리뷰(codex)가 지적한 문제: 브리지는 **인증 없이 원격에서 Claude를 실행**시킬 수
있는 엔드포인트였다. 누구든 그 URL을 알면 PC에서 임의 프롬프트를 돌릴 수 있다. 그래서
backend가 `X-Bridge-Secret`(공유 시크릿)을 함께 보내고, 브리지가 이를 검증하도록 했다.

```kotlin
// ClaudeBridgeClient.kt — 인증 헤더 추가
private val bridgeSecret = System.getenv("BRIDGE_SECRET") ?: ""
...
val response = client.post().uri("/ask")
    .header("Content-Type", "application/json; charset=utf-8")
    .header("X-Request-Id", requestId)
    .header("X-Bridge-Secret", bridgeSecret)   // 원격 실행 표면 차단 (codex F2)
    .body(payload)
```

```yaml
# docker-compose.yml — 시크릿 배선
BRIDGE_SECRET: ${BRIDGE_SECRET:-}          # 브리지 인증
```

브리지 쪽 상수시간 검증 등 상세는 ci-cd issue4 참조.

---

## 5. 결론

문서를 근거로 한 스트리밍 답변 + 세션별 대화 이력 + 필요 시 Claude로의 에스컬레이션이
하나의 흐름으로 관통했다. 설계의 뼈대는 두 가지였다 — **대화 상태의 정본은 서버(Redis),
문서의 정본은 git**, 그래서 쿠키에는 열쇠(세션 id)만, 요청 본문에는 경로만 오간다.
후속 3건은 실제로 붙여 보며 잡은 배선·전송·보안 문제였다. 세션·컨텍스트 상한값은
`[구현 검증]`에 남겼다. PR #26~#29
