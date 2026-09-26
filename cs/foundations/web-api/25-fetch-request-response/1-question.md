# web-api/25 — `fetch` 와 `Request`/`Response`: 옵션·헤더·상태 코드가 예외가 아니라는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 단순 요청·프리플라이트 등 CORS 의 규칙은 [목록의 **28번 주제**](../28-cors-simple-and-preflight/)가 정본이다. 여기는 **`fetch` 가 무엇을 이행·거부하나**와 **거부돼도 서버에서 일어난 일**을 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 Fetch 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 여섯 요청 (예측)

```js
// wa24b-25-q1.js
// 질문용 — 실행 대상 아님
// 여섯 요청 — A 200 · A 404 · A 500 · 아무도 안 듣는 포트 · 다른 출처 B 에 POST(허용 헤더 없이) · B 에 POST(Access-Control-Allow-Origin: *)
await fetch(url, init).then(res => /* res.ok · res.status */, err => /* err.name · err.message */);
// 칸마다 then 과 catch 중 무엇이 불리나? res.ok · res.status 는? catch 의 오류 이름과 문구는?
```

- 여섯 칸을 채워라. `catch` 로 가는 칸은 어느 것들인가?
- `catch` 로 간 칸들의 오류는 서로 가를 수 있나?

### 2. 콘솔과 서버 로그 (예측)

```js
// wa24b-25-q2.js
// 질문용 — 실행 대상 아님
// 문항 1 의 여섯 요청을 하는 동안 — 콘솔(CDP Log 도메인)과 서버 두 대의 로그
// 콘솔에는 몇 줄이, 어떤 수준으로 찍히나? 서버 B 의 로그에 「허용 헤더 없음」 POST 가 있나?
```

- 콘솔에 찍히는 줄의 수준과 내용은?
- 서버 B 는 허용 헤더 없는 POST 를 받았나? 받았다면 무엇을 했나?

### 3. `catch` 를 안 단 두 요청 (예측)

```js
// wa24b-25-q3.js
// 질문용 — 실행 대상 아님
addEventListener("unhandledrejection", e => 적기(e.reason));
fetch("/status?code=404").then(res => 적기(res.ok));
fetch(아무도안듣는곳 + "/status?code=200").then(() => 적기("then"));
// catch 를 안 달았다 — 어느 쪽이 unhandledrejection 이 되나? 그 reason 은?
```

- 적히는 줄은? `unhandledrejection` 은 몇 번, 어느 쪽인가?

### 4. `Request`/`Response` 를 값으로 (예측)

```js
// wa24b-25-q4.js
// 질문용 — 실행 대상 아님
new Response('{"n":1}', { status: 404 });           // ok · statusText · type · url 은?
Response.json({ n: 2 });                            // status · Content-Type 은?
new Response("x", { status: 99 });                  // ?
new Response("x", { status: 204 });                 // ?
const 요청 = new Request("/status?code=201", { method: "POST", body: "하나" });
const 복사 = 요청.clone();
await fetch(요청); await fetch(요청); await fetch(복사); // 각각?
```

- 각 줄의 결과나 예외(이름과 문구)를 적어라.

### 5. 헤더를 붙이면 (예측)

```js
// wa24b-25-q5.js
// 질문용 — 실행 대상 아님
document.cookie = "jar=1; path=/";
const 붙임 = { "x-PrObE": "1", "Host": "evil.example", "Cookie": "evil=1", "Origin": "http://evil.example",
               "Referer": "http://evil.example/", "Content-Length": "999", "Connection": "close", "Sec-Probe": "1" };
new Headers(붙임);                 // 담긴 이름은?
new Request("/headers", { headers: 붙임 }).headers;   // 담긴 이름은?
await fetch("/headers", { headers: 붙임 });           // 예외? 서버가 받은 여덟 헤더의 값은? 이름 x-PrObE 의 글자꼴은?
// 응답의 X-Visible · Set-Cookie 를 res.headers.get 으로 읽으면?
```

- 세 자리(빈 `Headers` · `Request` · 서버)에서 각각 무엇이 남나?
- 응답 헤더 둘은 읽히나? 쿠키 통에는?

### 6. 같은 404 를 다른 언어로 (예측)

```js
// wa24b-25-q6.js
// 질문용 — 실행 대상 아님
// 같은 서버 A 의 /status?code=200 · 404 · 500 을 파이썬 urllib.request.urlopen 으로 부른다
// 각각 돌아오나, 예외인가? 예외라면 이름과 문구는?
```

- 세 줄의 결과는? 서버 로그는 `fetch` 때와 다른가?

### 7. 404 에서 `catch` 가 안 도는 이유 (왜)

- Fetch 명세의 어느 두 문장이 이것을 정하나?

### 8. CORS 가 막는 것 (경계)

- CORS 거부에서 **막힌 것**과 **안 막힌 것**을 갈라라. 되돌릴 수 없는 엔드포인트에서 이것이 왜 문제인가?

### 9. 금지 헤더가 사라지는 자리 (경계)

- 페이지가 준 `Cookie` 는 어디서 지워지나? 예외가 없다면 무엇으로 알아채나?

### 10. 다른 주제와 잇기 (연결)

- [JS 37번 주제](../../languages/js/syntax/37-promise-state-model/1-question.md)의 미처리 거부와 문항 3은 어떻게 만나나?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
