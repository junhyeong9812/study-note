# cs/issue/network/http-streaming-status-locked — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **응답 순서와 상태 잠김.** HTTP 응답은 **상태줄(`HTTP/1.1 200 OK`) → 헤더들 → 빈 줄 → 본문** 순으로 바이트가 나간다. 상태코드는 맨 앞 상태줄에 있고, 이건 본문보다 먼저 전송된다. 네트워크로 이미 나간 바이트는 회수할 수 없으므로, **헤더가 커밋(flush)되는 순간 — 늦어도 본문의 첫 조각을 보내는 순간 — 상태코드는 이미 상대에게 전송·확정**되어 되돌릴 수 없다(서버가 헤더를 언제 flush하는지는 구현·버퍼 크기에 따라 다르다). "200 헤더를 보내는 순간 확정된다"는 말은 이 전송 순서의 필연이다.

2. **오류 계약의 시간분할.** 스트리밍은 최종 결과를 알기 전에 본문을 흘리기 시작한다. 도중에 오류가 나도 이미 200을 보냈으니 "사실 503이었다"고 못 바꾼다. 그래서 **오류 계약을 시간으로 나눈다** — 경계는 "스트림(본문 전송) 시작 시점". 시작 전에 잡히는 실패는 아직 헤더를 안 보냈으니 상태코드를 자유롭게 줄 수 있고(봉투 JSON), 시작 후의 실패는 상태코드가 잠겼으니 본문 채널(텍스트 청크)과 서버 로그로 처리한다.
   > **봉투(envelope)** — `{success, data, error}` 형태로 성공/실패를 본문에 담는 공통 응답 규약.

3. **전 vs 후.** 시작 **전**에 판정 가능: 세마포어 포화(동시 처리 한도 초과 → 503 `busy`), 입력 검증 실패(role/개수/길이 위반 → 422). 이건 모델 호출을 시작하기도 전에 알 수 있으니 상태코드 있는 봉투로 정직하게 거절한다. 시작 **후**에만 알 수 있음: 모델이 토큰을 흘리다 끊김, 상류 타임아웃. 이건 이미 200을 보낸 뒤라 상태코드로 못 알리니 **텍스트 청크가 곧 계약**이고 오류는 로그만 남기고 연결이 끊긴다. "판정 시점"이 전송 시점보다 앞서면 상태코드를, 뒤면 본문 채널을 쓴다.

4. **클라이언트는 미완을 어떻게 아는가.** 상태코드로는 못 안다(200을 이미 받음). 대신 **본문 채널의 종료 규약**으로 안다 — 정상 종료라면 서버가 약속된 완료 신호를 준다(예: Ollama의 `done` 플래그, 종료 토큰, 정상적인 스트림 close). 그 완료 표식 없이 연결이 끊기면 클라이언트는 "미완"으로 해석한다. 즉 완결성 판정이 **상태코드 계층에서 본문 프로토콜 계층으로 내려간다**. (설계상 정상 완료와 중단을 본문에서 구분할 수 있어야 하며, 그렇지 않으면 잘린 응답을 완성으로 오인할 수 있다.)

5. **왜 본질적 제약인가.** 상태코드를 오류로 주려면 헤더 전송 전에 결과를 알아야 한다 = **응답을 다 만들 때까지 헤더/본문 전송을 미룸** = 버퍼링. 그런데 스트리밍의 존재 이유가 바로 "완성 전에 첫 글자를 빨리 보내기"다. 오류를 상태코드로 알리려고 헤더를 미루면 스트리밍 자체를 포기하는 것이라, 둘은 양립 불가다. 그래서 이건 게으른 우회가 아니라 **"조기 전송 vs 사후 상태변경"이 근본적으로 상충**하는 데서 오는 제약이다.

6. **다른 프로토콜의 해법 — 본문 뒤에 상태 자리 만들기.** 공통 아이디어는 "본문 다음에 상태를 덧붙일 자리"를 프로토콜에 마련하는 것이다. **HTTP chunked trailer** — chunked 본문의 마지막 0-크기 조각 뒤에 트레일러 헤더를 실어 사후 메타데이터를 준다(단 브라우저 fetch API는 트레일러를 노출하지 않고 중간 프록시가 버리기도 해, 범용 클라이언트용 오류 채널로는 약하다). **SSE(Server-Sent Events)** — 본문을 `event:`/`data:` 이벤트 스트림으로 규약화해 `event: error` 같은 타입 이벤트로 도중 오류를 본문 안에서 구조적으로 전달한다. **gRPC** — 응답 메시지 스트림 뒤에 **trailing status**(grpc-status 트레일러)를 두어, 본문을 다 보낸 뒤에도 성공/실패 코드를 정식으로 붙인다. 셋 다 "상태코드는 앞에서 잠기니, 상태를 본문 이후 계층에 별도로 둔다"는 같은 전략이다.
   > **trailer** — 본문 전송이 끝난 뒤에 붙이는 헤더. 스트림 시작 시점엔 몰랐던 값을 나중에 실을 수 있다.

7. **프록시 패스스루와의 연결 — 겹치지만 완전히 같은 뿌리는 아니다.** 중간 프록시가 상류의 200을 받아 이미 클라이언트로 흘리기 시작했다면, 프록시도 "한 번 나간 헤더는 불변"이라 사후에 상태코드를 못 바꾼다 — 스트리밍 중계에선 같은 제약이 프록시에도 그대로 걸린다(*상태코드는 응답의 맨 앞에서 한 번만 결정된다*). 반면 버퍼링하는 프록시가 봉투를 열어 재포장하며 상태를 뭉개는(422→500) 문제는 기술적으로는 바꿀 수 있는데 **바꾸면 정보가 손실**되기 때문에 금지하는 것이다 — "상태를 원형 보존" 규칙의 근거는 불변성보다 정보 보존 쪽이고, 두 규칙은 "상태는 확정한 쪽의 판정을 그대로 전달한다"에서 만난다. (프록시 패스스루는 [proxy-passthrough](../proxy-passthrough/) 참조.)

## 문제 구조 (추상화 코드)

### 변형 A — 스트림 도중 오류를 상태코드로 알리려 함 → 오류 계약의 시간분할
① 문제 코드
```python
@router.post("/chat")
async def chat(body: ChatIn):
    async def tokens():
        async for t in model.stream(body.messages):   # 도중 실패 시 이미 200 전송 후
            yield t
    return StreamingResponse(tokens())                 # 포화·입력 오류도 스트림 안에서 터짐
```
② 고친 코드
```python
@router.post("/chat")
async def chat(body: ChatIn, request: Request):
    if request.app.state.sem.locked():                 # 시작 전 → 상태코드 자유
        return JSONResponse(fail("busy", retry_after=2), status_code=503)
    # locked() 검사는 빠른 거절용 — 실제 획득은 tokens() 안에서 해야 하고, 검사와 획득 사이 경쟁으로
    # 소수 요청이 대기할 수 있다(엄격하면 획득을 스트림 시작 전에 시도하고, 스트림 종료 시 해제)
    # 입력 검증 실패는 스트림 전에 422 봉투

    async def tokens():
        try:
            async for t in model.stream(body.messages):
                yield t                                # 시작 = 200 확정, 텍스트 청크가 곧 계약
        except Exception as e:                         # 시작 후 → 로그 + 연결 끊김
            await log(body.request_id, f"stream error: {type(e).__name__}", "error")
            raise                                      # 삼키고 정상 return하면 chunked 종료 표식이 나가
                                                       # 잘린 응답이 '정상 완료'로 보인다 → 다시 던져 비정상 종료시킨다
    return StreamingResponse(tokens(), media_type="text/plain; charset=utf-8")
```
무엇이 깨졌나: 이미 커밋된 상태코드를 사후에 바꿀 수 있다고 가정했다.

### 변형 B — 스트림을 중계하는 쪽이 도중 오류에서 스트림을 닫지 않음
① 문제 코드
```kotlin
val emitter = ResponseBodyEmitter(TIMEOUT)
executor.execute {
    try { upstream.stream(req) { token -> emitter.send(token) }; emitter.complete() }
    catch (e: Exception) { log.error(e) }             // complete 누락 → 비동기 요청이 타임아웃까지 열린 채 남음(연결 누수)
}
return emitter
```
② 고친 코드
```kotlin
executor.execute {
    try { upstream.stream(req) { token -> emitter.send(token) }; emitter.complete() }
    catch (e: Exception) {
        requestLog.log(requestId, "chat failed: ${e.message?.take(150)}", "error")
        runCatching { emitter.send("\n[오류] 응답 생성에 실패했습니다.") }   // 본문 채널로 알림
        emitter.completeWithError(e)                                        // 반드시 닫는다
    }
}
```
무엇이 깨졌나: 상태코드로 못 알리는 오류를 본문 채널로도 닫지 않아 연결이 새었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기존 방안은 **보내는 쪽**이 상태 잠김을 전제로 오류 계약을 시간으로 나누는 것이다. 같은 원리(커밋 뒤 status는 확정·불변)를 **관측하는 쪽**에서 다룬 방안이 있다 — 최종 상태를 보려면 확정 시점을 감싸는 가장 바깥 계층에서 기록한다.

### 방안 2 — 최종 status 확정 지점(필터 최전방)에서 기록
① 문제 코드
```kotlin
class UsageInterceptor : HandlerInterceptor {          // 보안 필터 체인 뒤 → 401/403은 도달 안 함
    override fun afterCompletion(req: HttpServletRequest, resp: HttpServletResponse, h: Any, ex: Exception?) {
        runCatching { usageLog.save(req, resp.status) }  // 예외→/error 디스패치 전이라 500을 200으로
    }                                                     // 기록 실패는 무음 (SSE 콜백 중복은 필터 이전 1차안에서 재검출)
}
```
② 고친 코드
```kotlin
@Order(Ordered.HIGHEST_PRECEDENCE)                     // 보안 필터보다 앞 = 가장 바깥
class UsageFilter : OncePerRequestFilter() {
    override fun doFilterInternal(req: HttpServletRequest, resp: HttpServletResponse, chain: FilterChain) {
        val recorded = AtomicBoolean(false)
        var failed = false
        try { chain.doFilter(req, resp) } catch (e: Exception) { failed = true; throw e }
        finally {
            // 비동기(SSE)면 완료 리스너에서 같은 record 호출 (경합 IllegalStateException은 catch)
            record(recorded, req, resp, failed)
        }
    }
    private fun record(recorded: AtomicBoolean, req: HttpServletRequest, resp: HttpServletResponse, failed: Boolean) {
        if (!recorded.compareAndSet(false, true)) return                 // 한 요청 한 행
        val status = if (failed && !resp.isCommitted && resp.status < 400) 500 else resp.status   // 커밋된 status는 그대로
        try { usageLog.save(req, status) } catch (e: Exception) { logger.warn("usage log failed", e) }   // 무음화 제거
    }
}
```
무엇이 깨졌나: 관측 지점이 최종 status가 확정되기 전·거부 경로 밖에 있어, 기록된 상태가 실제 응답과 달랐다.\
같은 구조: 컨트롤러 AOP로 레이턴시·상태를 재면 필터 체인·직렬화·예외 처리 시간이 빠지고, 커밋 전 status는 아직 확정값이 아니다(구현에 따라 기본값 200이나 미설정 값으로 읽힌다) → 접근 로그 필터를 요청 ID 필터 바로 뒤(`HIGHEST_PRECEDENCE + 1`, MDC에 요청 ID가 있는 상태)에 두어 요청 전체 수명을 감싼다. 비동기 프레임워크에선 미들웨어 등록 순서로 접근 로그를 가장 바깥에 둔다(등록 순서와 바깥/안쪽의 대응은 프레임워크마다 다르므로 실측 확인).

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 1. 오류 계약 시간분할(송신 측) | 오류를 클라이언트에 알려야 한다 | 시작 전 검증 분리·본문 규약 | 시작 후 오류를 본문으로 구분 못 하면 잘린 응답을 완성으로 오인 | 스트리밍 응답을 만드는 서버 |
| 2. 바깥 계층 기록(관측 측) | 최종 status를 정확히 기록해야 한다 | 필터 순서 설계·중복 방지 | 필터가 보안 체인 뒤에 있으면 거부 요청 누락, 비동기 콜백 중복 | 사용 로그·접근 로그·레이턴시 계측 |

**결론**: 두 방안은 대체가 아니라 짝이다.\
**보내는 쪽**은 status가 잠기기 전에 판정 가능한 실패를 상태코드로, 이후 실패를 본문 채널로 나눈다(1).\
**보는 쪽**은 status가 확정되는 지점을 감싸는 **가장 바깥**에서 한 번만 기록하고, 이미 커밋된 status는 덮어쓰지 않는다(2).
