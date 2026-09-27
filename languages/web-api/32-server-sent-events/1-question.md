# web-api/32 — 서버 보내기 이벤트: `EventSource`·자동 재연결·`Last-Event-ID` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — `fetch` 의 상태 코드와 서버 요청 로그는 [25번 주제](../25-fetch-request-response/1-question.md), 응답 본문을 직접 청크로 읽는 쪽은 [26번 주제](../26-response-body-streaming/1-question.md)가 물었다. 교차 출처 · 쿠키는 [28번 주제](../28-cors-simple-and-preflight/1-question.md) · [29번 주제](../29-credentials-and-cookies/1-question.md)다. 여기는 **끊겼을 때 누가 다시 붙고, 무엇이 남고 무엇이 사라지나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. **명세 원문은 이 판에서 열지 못했다** — 그래서 정답도 「명세대로」를 판정하지 않는다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 끊긴 뒤 받은 번호와 실려 온 헤더 (예측)

```js
// wa32b-32-q1.js
// 질문용 — 실행 대상 아님
// 서버: 이벤트 1~10 을 보내다 4 번째 뒤에서 연결을 끊는다. 다시 붙으면 아래 방식대로 보낸다
//   (가) 이벤트마다 id: 를 붙이고 · 다시 붙으면 Last-Event-ID 다음 번호부터
//   (나) id: 를 안 붙이고      · 다시 붙으면 Last-Event-ID 다음 번호부터(헤더가 없으면 1 부터)
//   (다) 이벤트마다 id: 를 붙이고 · 다시 붙으면 「끊긴 동안 지나간 둘」을 건너뛰고 현재부터
const es = new EventSource("/sse?...");
const 받음 = [];
es.onmessage = e => 받음.push(Number(e.data));
// 세 경우 각각 — 받음 은? 두 번째 연결의 요청에 Last-Event-ID 헤더가 실렸나, 실렸다면 값은?
```

- 세 경우 각각의 받은 번호 · 두 번째 연결의 `Last-Event-ID` 는?

### 2. `retry:` 와 재연결 간격 (예측)

```js
// wa32b-32-q2.js
// 질문용 — 실행 대상 아님
// 서버가 첫 응답 첫머리에 retry: 200 을 보낸 판과, retry: 를 안 보낸 판
//   retry: 200
//
//   id: 1
//   data: 1
//   ...
// 서버가 연결을 끊은 뒤 다음 연결이 오기까지 — 두 판 각각 1000ms 이상이었나?
```

- 두 판 각각 — 1000ms 이상이었나? 받은 번호는 달라지나?

### 3. 첫 응답의 모양과 다시 붙기 (예측)

```js
// wa32b-32-q3.js
// 질문용 — 실행 대상 아님
// 첫 연결에 대한 서버의 응답 모양 하나씩 — 브라우저가 다시 붙나?
// (같은 칸으로 두 번째 연결이 오면 서버는 칸을 끝내는 응답을 준다)
//   ① 200 text/event-stream — 이벤트 하나 보내고 끊음
//   ② 200 text/event-stream; charset=utf-8
//   ③ 204 No Content
//   ④ 500
//   ⑤ 200 text/plain
//   ⑥ 헤더도 안 보내고 연결을 끊음 — 한 번 · 두 번 연달아 · 세 번 연달아
const es = new EventSource("/sse1?...");
es.onerror = () => console.log(es.readyState);
// 각각 — 서버가 받은 연결 수 · open 이 났나 · error 가 몇 번 · 마지막 readyState 는?
```

- 모양마다 — 서버가 받은 연결 수 · `open` · 마지막 `readyState` 는?

### 4. 한 응답 안의 블록들 (예측)

```js
// wa32b-32-q4.js
// 질문용 — 실행 대상 아님
// 한 응답에 이 바이트가 들어 있고, 마지막 줄 뒤에 빈 줄 없이 서버가 연결을 끊는다
//   : 이 줄은 주석이다
//
//   data: 첫째
//
//   event: tick
//   data: 이름 붙은 것
//
//   data: 한 줄
//   data: 두 줄
//
//   id: 7
//
//   data:앞 공백 없음
//
//   data:  앞 공백 둘
//
//   event: tick
//   id: 8
//   data: 마지막 블록 — 빈 줄 없이 끝난다
es.onmessage = e => 적기("onmessage", e.data, e.lastEventId);
es.addEventListener("tick", e => 적기("tick 리스너", e.data, e.lastEventId));
// 무엇이 몇 번, 어느 리스너로 오나? data 와 lastEventId 는?
```

- 적히는 줄을 순서대로 — 어느 리스너 · `data` · `lastEventId` 는?

### 5. `readyState` 의 수열 (예측)

```js
// wa32b-32-q5.js
// 질문용 — 실행 대상 아님
// q1 의 (가) 한 칸 — 연결 ① 4개 받고 끊김 → 연결 ② 5~10 받고 끊김 → 연결 ③ 204
const es = new EventSource("/sse?...");
const 상태 = [es.readyState];
es.onopen = () => 상태.push(es.readyState);
es.onerror = () => 상태.push(es.readyState);
// 상태 는 어떤 수열이 되나?
```

- `상태` 는?

### 6. 「현재부터」 서버의 칸 (왜)

- 문항 1의 (다)에서 유실이나 중복이 있었다면 그 원인은 브라우저 쪽인가, 서버 쪽인가? `id:` 를 붙이는 것만으로 충분한가?

### 7. `Last-Event-ID` 가 실리는 조건 (경계)

- 두 번째 연결에 헤더가 없는 칸이 있었다면 그 칸들의 공통점은? 그때 「이어 보냄」 서버가 할 수 있는 최선은 무엇인가?

### 8. 「헤더 없이 한 번 끊음」 줄을 두 창으로 읽기 (경계)

- 그 줄에서 서버의 연결 수와 페이지의 이벤트는 같은 이야기를 하나? 갈린다면 이 편은 그 차이를 누가 만들었다고 **주장하나, 안 하나**?

### 9. 멈추게 하는 쪽은 누구인가 (경계)

- 서버가 연결을 닫는 것 · 204 · 500 · 앱의 `es.close()` 중 재연결을 멈춘 것은? `onerror` 에서 새 `EventSource` 를 만드는 코드가 위험한 이유는?

### 10. 다른 주제와 잇기 (연결)

- [26번 주제](../26-response-body-streaming/1-question.md)의 `fetch` 스트리밍으로 같은 알림을 받으면 **앱이 직접 해야 하는 일** 두 가지는?
- [33번 주제](../33-websocket/1-question.md)의 WebSocket 대신 이것을 고를 근거로 이 편이 **댈 수 있는 것과 댈 수 없는 것**은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
