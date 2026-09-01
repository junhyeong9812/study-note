# issue12 — 채팅 오케스트레이션: 상태는 서버, 문서는 git, 답은 스트림

- 이슈 #25 · PR: #26·#27·#28·#29

## 1. 배경·구조

채팅의 어려운 부분은 모델 호출이 아니라 **상태(세션·기록)와 컨텍스트 조립**이다. 그래서
backend가 오케스트레이션을 맡는다(별도 채팅 서버 안 만듦 — 재료가 여기 있다).

```
POST /api/chat {doc_path, question}  (+ chat_session 쿠키)
   ├─ 세션: 쿠키 없으면 UUID 발급(HttpOnly, 중앙 발급 규약)·있으면 형식 검증
   ├─ 기록: Redis chat:{sid}:{docPath} 리스트 (TTL 7일, 대화마다 연장)
   ├─ 컨텍스트: 첫 대화면 git에서 doc_path 원문 로드 → system + 최근 10턴 + 새 질문
   └─ llm /chat 스트림 → ResponseBodyEmitter로 청크 중계 (MVC — webflux 불필요)
```

**왜 이렇게** (설계 결정):
- **쿠키엔 세션 id만** — 대화 내용을 쿠키에 넣으면 4KB 한계·매 요청 왕복·변조 가능.
  내용은 Redis(서버가 정본), 쿠키는 열쇠.
- **문서는 경로만 받음** — front가 내용을 실어 나르면 수십 KB 낭비 + 변조 주입 가능.
  backend가 git에서 직접 읽는다. "첫 대화" 판정도 Redis 키 존재로 backend가.

## 2. 구현 중 마주친 문제

### 문제 — 에스컬레이션이 "0바이트 파싱 오류"로 실패

**상황**: backend가 Claude 브리지(PC의 파이썬 http.server)에 `RestClient`로 프롬프트를
POST. 로컬·socat까지는 됐는데 backend→브리지에서만 실패.

**문제(로그)**:
```
escalate failed: 500 Internal Server Error: "{"error": "Expecting value: line 1 column 1 (char 0)"}"
```
브리지가 요청 본문을 **0바이트로** 읽었다.

**접근**: 같은 요청을 curl로 하면 성공 → 클라이언트 차이. Spring `RestClient`에 Map
본문을 주면 Content-Length 대신 **chunked transfer-encoding**으로 나가는데, 파이썬
기본 `http.server`는 `Content-Length`만 읽고 **chunked 요청 본문을 못 읽는다**(rfile을
길이 기반으로만 읽음).

**결론(수정)**: 본문을 `objectMapper.writeValueAsBytes(...)` 바이트 배열로 전달 →
RestClient가 Content-Length를 명시 → 브리지가 정상 수신.
```kotlin
val payload = objectMapper.writeValueAsBytes(mapOf("prompt" to prompt))
client.post().uri("/ask").body(payload)   // Map 대신 byte[]
```
**배경**: HTTP 본문 인코딩(chunked vs Content-Length)은 클라이언트가 자동 결정하고,
서버 구현마다 지원 범위가 다르다 — 소박한 서버와 붙을 땐 Content-Length를 강제한다.

## 3. 리뷰 반영 (codex F2 — 브리지 인증)

브리지가 인증 없는 원격 Claude 실행 엔드포인트였다 → backend가 `X-Bridge-Secret`
공유 시크릿을 보내고 브리지가 상수시간 검증(PR #29). 상세는 ci-cd issue4.

## 4. 결론

문서 근거 스트림 답변 + 세션 이력 + 에스컬레이션 관통. 세션·컨텍스트 상한은
[구현 검증]에. PR #26~#29
