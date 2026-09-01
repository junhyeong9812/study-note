# issue6 — /chat: 대화를 스트림으로 흘려보내기

- 이슈 #16 · PR: #17

## 1. 배경

rewrite는 "한 번에 JSON 하나"였지만 채팅은 다르다 — 답이 완성될 때까지 기다리면 사용자는
수십 초 빈 화면을 본다. ChatGPT처럼 **토큰이 생기는 대로 흘려보내는** 스트리밍이 필요.

## 2. 방식 — Ollama stream:true 청크 중계

```python
async with client.stream("POST", "/api/chat", json={..., "stream": True,
                         "think": False, "options": {"num_predict": 1024}}) as response:
    async for line in response.aiter_lines():        # Ollama는 줄당 JSON 하나(NDJSON)
        token = json.loads(line).get("message", {}).get("content", "")
        if token: yield token                        # 토큰만 뽑아 흘림
        if json.loads(line).get("done"): break
```

- rewrite와 같은 세마포어(동시 2)·think:false·num_predict 상한(폭주 가드레일 — 그 실측 교훈).
- **오류 계약의 경계**: 스트림이 시작되기 전(포화·검증)은 봉투 JSON(503/422), 시작된
  뒤에는 텍스트 청크가 곧 계약 — 도중 오류는 로그만 남고 연결이 끊긴다. HTTP는 200
  헤더를 이미 보낸 뒤엔 상태코드를 못 바꾸기 때문(스트리밍의 본질적 제약).

## 3. 결론

`StreamingResponse(media_type="text/plain")`로 노출. 실기동 "안녕하세요!" 스트림 확인. PR #17
