# web-api/33 — WebSocket: 핸드셰이크·프레임·닫힘 코드와 재연결 설계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 한 방향 · 브라우저가 다시 붙는 쪽은 [32번 주제](../32-server-sent-events/1-question.md)가 물었다. 재시도 간격(지수 · 지터)은 [`ops-patterns/01-retry-backoff`](../../../ops-patterns/01-retry-backoff/1-question.md)가 정본이다. 여기는 **HTTP 가 어떻게 WebSocket 이 되고, 선로에 무엇이 오가고, 끊긴 것을 페이지가 무엇으로 아나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과, 표준 라이브러리로 직접 짠 서버의 선로 덤프다. **명세 원문(WHATWG WebSockets · RFC 6455)은 이 판에서 열지 못했다.** 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 첫 요청의 머리 (예측)

```js
// wa32b-33-q1.js
// 질문용 — 실행 대상 아님
const ws = new WebSocket(`ws://${location.host}/ws`);
// 서버가 받은 첫 요청 — 메서드와 버전 · Connection · Upgrade · Sec-WebSocket-Version 의 값은?
// Sec-WebSocket-Key 는 몇 글자이고, base64 를 풀면 몇 바이트인가? 그 밖에 붙는 Sec- 헤더는?
```

- 요청 줄과 네 헤더의 값 · 키의 길이 · 그 밖의 `Sec-` 헤더는?

### 2. Accept 가 틀린 101 (예측)

```js
// wa32b-33-q2.js
// 질문용 — 실행 대상 아님
// 서버가 101 Switching Protocols 는 주되, Sec-WebSocket-Accept 를 아무 28글자로 준다
const ws = new WebSocket(`ws://${location.host}/ws?s=badaccept`);
ws.onopen = () => 적기("open");
ws.onerror = () => 적기("error · readyState=" + ws.readyState);
ws.onclose = e => 적기(`close · code=${e.code} · wasClean=${e.wasClean}`);
// 무엇이 적히나? 콘솔에는?
```

- 적히는 줄과 콘솔 한 줄은?

### 3. 선로의 프레임 머리 (예측)

```js
// wa32b-33-q3.js
// 질문용 — 실행 대상 아님
// 핸드셰이크 뒤 서버가 먼저 ping 프레임(본문 "p1")을 보낸다. 그다음 글 하나와 바이너리 3바이트
ws.onmessage = e => {
  if (typeof e.data === "string") ws.send("안녕");            // UTF-8 6바이트
  else { ws.send(new Uint8Array([4, 5, 6])); ws.send("x".repeat(200)); }
};
// 페이지의 message 는 몇 번 오나(ping 은)? 서버가 받은 첫 프레임은 무엇인가?
// 서버가 받은 "안녕" 프레임의 첫 두 바이트(16진)는? "x"×200 프레임의 머리는?
```

- 페이지의 `message` 수 · 서버가 받은 첫 프레임 · `"안녕"` 프레임과 200바이트 프레임의 머리는?

### 4. 서버가 먼저 닫을 때 (예측)

```js
// wa32b-33-q4.js
// 질문용 — 실행 대상 아님
// 서버가 먼저 닫는다 — 방법 하나씩
//   close 프레임 코드 1000 · 1001 · 1008 · 4000 (이유 "bye")
//   코드 없는 close 프레임(본문 0바이트)
//   close 프레임 코드 1005 · 1006 (이유 "bye")
//   close 프레임 없이 TCP 를 끊음
ws.onerror = () => 오류++;
ws.onclose = e => 적기(e.code, e.wasClean, e.reason, 오류);
// 각각 — CloseEvent.code · wasClean · reason · error 이벤트 수는? 브라우저가 서버에 돌려준 close 코드는?
```

- 줄마다 `code` · `wasClean` · `error` 수는? 브라우저의 답 코드가 서버가 보낸 코드와 달라지는 줄은?

### 5. 페이지가 고를 수 있는 코드 (예측)

```js
// wa32b-33-q5.js
// 질문용 — 실행 대상 아님 — 연결이 열린 뒤 페이지가 먼저 닫는다
ws.close();
ws.close(1000);
ws.close(1001);
ws.close(3000, "앱");
ws.close(4999);
ws.close(2999);
ws.close(5000);
ws.close(1000, "가".repeat(41));   // UTF-8 123바이트
ws.close(1000, "가".repeat(42));   // UTF-8 126바이트
// 각 줄 — 받아 주나, 던지나(무엇을)? 받아 준 줄에서 서버가 되돌려 준 뒤 CloseEvent.code 는?
```

- 받아 주는 줄과 던지는 줄은?

### 6. 소켓을 연 채 입을 닫은 서버 (예측)

```js
// wa32b-33-q6.js
// 질문용 — 실행 대상 아님
// 핸드셰이크 뒤 서버가 소켓을 연 채 읽지도 쓰지도 않는다
await 쉬기(3000);
적기(ws.readyState, 그동안_온_이벤트);             // ①
ws.send("살아 있나"); await 쉬기(1000);
적기(답이_왔나, ws.readyState, ws.bufferedAmount);  // ②
ws.close(4000, "박동 없음");                       // 서버는 이 close 에 답하지 않고, 조금 뒤 TCP 를 끊는다
// ① ② 는? 마지막 CloseEvent 의 code · wasClean 은? 서버가 나중에 읽어 본 쌓인 프레임 중 브라우저가 스스로 보낸 ping 은?
```

- ① ② 와 마지막 `CloseEvent` 는? 브라우저가 스스로 보낸 ping 은 몇 개인가?

### 7. `Sec-WebSocket-Accept` 는 어떻게 만드나 (왜)

- 키를 base64 로 풀어서 쓰나, 글자 그대로 쓰나? 이 편은 그 GUID 값을 무엇으로 확인했고, 무엇으로는 확인하지 **못했나**?

### 8. 닫힘 코드의 출처 (경계)

- 문항 4에서 페이지가 받은 코드 중 **선로에 실린 적이 없는** 번호가 있었나? 서버가 선로에 1006 을 실으면 무슨 일이 났나?

### 9. `send` 가 돌아왔다는 것 (경계)

- 1 MiB 를 보낸 직후 `bufferedAmount` 는? 선로에서 그 메시지는 몇 개의 프레임이었고, 페이지는 그것을 아나?

### 10. 재연결을 설계한다면 (연결)

- 끊김을 아는 신호는 무엇뿐이었나? 반쯤 열린 연결은 무엇으로 잡나? 다시 붙는 간격은 이 편과 [`ops-patterns/01-retry-backoff`](../../../ops-patterns/01-retry-backoff/1-question.md) 중 어디가 정본인가?
- [32번 주제](../32-server-sent-events/1-question.md)의 SSE 와 비교해 **앱이 더 해야 하는 일** 두 가지는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
