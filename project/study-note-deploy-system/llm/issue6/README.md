# issue6 — /chat: 대화를 토큰이 생기는 대로 흘려보내기

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #16 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/17

---

## 1. 무엇이 문제였나 — 채팅은 rewrite와 리듬이 다르다

rewrite는 "한 번 요청 → JSON 하나"로 끝난다. 답이 짧고 정형이라 완성될 때까지 기다려도
1초 남짓이다. 하지만 채팅은 다르다 — 답이 길고, 완성될 때까지 기다리면 사용자는 수십 초
동안 빈 화면을 본다. ChatGPT처럼 **토큰이 생기는 대로 화면에 흘려보내는** 스트리밍이 필요하다.

> 용어 — 스트리밍(streaming): 응답을 한 덩어리로 다 만든 뒤 보내는 게 아니라, 만들어지는
> 조각(토큰)을 그때그때 조금씩 내보내는 것. 사용자는 첫 글자를 훨씬 빨리 본다.

---

## 2. 무엇을 고민했나 — 스트림 중간에 난 오류를 어떻게 알릴까

Ollama 자체가 `stream:true`로 부르면 줄 단위 JSON(NDJSON)을 흘려준다. 그러니 래퍼는 그걸
받아 **토큰만 뽑아 중계**하면 된다. 진짜 고민은 오류 계약이었다.

```
HTTP는 응답을 시작하는 순간(200 헤더 전송) 상태코드가 확정된다
  → 스트림이 이미 시작된 뒤에는 "사실 이거 503이었어"라고 못 바꾼다
  → 그러면 스트림 도중 난 오류는 어떻게 알리나?
```

결론: **오류 계약을 시간으로 나눈다.**

```
스트림 시작 전 (포화·입력 검증)  → 봉투 JSON (503/422) — issue4의 그 봉투 재사용
스트림 시작 후 (도중 오류)       → 텍스트 청크가 곧 계약. 오류는 로그만 남고 연결이 끊긴다
```

이건 회피가 아니라 HTTP 스트리밍의 본질적 제약이다 — 헤더를 이미 보낸 뒤엔 상태코드를
바꿀 수 없다. 그래서 "시작 전에 걸러낼 수 있는 것은 봉투로, 그 이후는 텍스트로"가 최선이다.

---

## 3. 그래서 이렇게

```
POST /chat {request_id, messages[]}
  ▼
api.py
  ├─ 세마포어 꽉 찼나? ──(예)──▶ 즉시 503 봉투 {"error":"busy"}   (시작 전)
  │
  └─(아니오)─▶ StreamingResponse(text/plain)
                 async for token in chat.stream(...):
                     yield token          ← 토큰 생기는 대로 흘림
                 (도중 오류는 로그만, 연결 끊김)
```

rewrite와 **같은 세마포어(동시 2)·같은 think:false·같은 num_predict 상한**(폭주 가드레일 —
issue1에서 31k 토큰을 실측한 그 교훈)을 그대로 재사용한다.

---

## 4. 코드 — 실제 커밋에서 (`feat b935122`)

**스트림 유즈케이스** (`wrapper/src/app/usecase/chat.py` 신규):

```python
MAX_PREDICT = 1024      # 폭주 가드레일 (rewrite 실측 교훈 — 서버측 상한이 유일한 방어선)

async def stream(request_id, messages, *, client, sem, model):
    if sem.locked():
        raise Busy()                              # rewrite와 동일한 거절 계약 재사용
    async with sem:
        async with client.stream("POST", "/api/chat", json={
            "model": model, "messages": messages,
            "stream": True, "think": False,
            "options": {"temperature": 0.3, "num_predict": MAX_PREDICT},
        }, timeout=httpx.Timeout(connect=5, read=120, write=10, pool=5)) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():   # Ollama는 줄당 JSON 하나(NDJSON)
                if not line:
                    continue
                data = json.loads(line)
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token                          # 토큰만 뽑아 흘림
                if data.get("done"):
                    break
```

**라우터 — 시작 전 오류만 봉투, 시작 후는 스트림** (`wrapper/src/app/api.py`):

```python
@router.post("/chat")
async def post_chat(body: ChatIn, request: Request):
    state = request.app.state
    if state.sem.locked():                          # 시작 전 포화 → 봉투 503
        await log(body.request_id, "chat rejected: busy", "warning")
        return JSONResponse(fail("busy", retry_after=2), status_code=503, ...)

    async def token_stream():
        count = 0
        try:
            async for token in chat.stream(body.request_id,
                    [m.model_dump() for m in body.messages], ...):
                count += 1
                yield token
            await log(body.request_id, f"chat ok tokens~{count}")
        except Exception as error:                  # 스트림 도중 오류 — 로그만 (연결은 끊김)
            await log(body.request_id, f"chat stream error: {type(error).__name__}", "error")

    return StreamingResponse(token_stream(), media_type="text/plain; charset=utf-8")
```

입력 계약도 rewrite처럼 엄격하게 잠갔다 — `role`은 system|user|assistant만, messages는
1~40개, 각 content는 1~20,000자(`ChatMessage`·`ChatIn`의 `extra="forbid"` + `Field` 제약).

---

## 5. 결론

`StreamingResponse(media_type="text/plain")`로 노출. 실기동에서 "안녕하세요!" 스트림이
토큰 단위로 흘러오는 것을 확인했다. 오류 계약을 "스트림 시작 전/후"로 나눈 것이 이 이슈의
핵심 설계 결정이다. PR: #17.
