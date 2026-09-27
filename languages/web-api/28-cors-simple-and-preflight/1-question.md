# web-api/28 — CORS: 단순 요청과 프리플라이트, 막는 것과 못 막는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 「허용 헤더 없는 단순 `POST` 도 서버에서는 처리된다」는 [25번 주제](../25-fetch-request-response/1-question.md)가 이미 물었다. 여기는 **무엇이 프리플라이트를 부르나**와 **프리플라이트가 붙으면 서버에서 무엇이 달라지나**를 묻는다. 쿠키가 붙는 요청은 [29번 주제](../29-credentials-and-cookies/1-question.md)다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 Fetch 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 메서드 · Content-Type · 헤더 32칸 (예측)

```js
// wa28b-28-q1.js
// 질문용 — 실행 대상 아님
// 페이지 출처 A 에서 다른 출처 B 로 — 메서드 4 × Content-Type 4 × 커스텀 헤더(없음 / X-A: 1) = 32칸
// B 의 OPTIONS 답은 넉넉하다(메서드 넷 · 헤더 content-type, x-a 허용). GET 이 아니면 본문 "x"
await fetch(B + "/cors?id=" + id, { method, headers: { "Content-Type": 종류, ...(헤더 ? { "X-A": "1" } : {}) }, body });
// 칸마다 B 가 받은 순서는? (OPTIONS 가 먼저 오나, 본 요청만 오나)
```

- OPTIONS 가 먼저 오는 칸과 안 오는 칸을 갈라라. 안 오는 칸의 공통점은?
- 페이지가 받은 `status` 만 보고 두 부류를 가를 수 있나?

### 2. 격자 밖의 여덟 칸 (예측)

```js
// wa28b-28-q2.js
// 질문용 — 실행 대상 아님
// 다른 출처 B 에 POST 하나씩 — B 가 받은 순서와 페이지가 받은 것은?
{ headers: { "Content-Type": "text/plain;charset=UTF-8" }, body: "x" }
{ headers: { "Content-Type": "TEXT/PLAIN" }, body: "x" }
{ headers: { "Content-Type": "text/plain; p=" + "a".repeat(115) }, body: "x" }   // 값이 129바이트
{ headers: { "Accept": "application/json" }, body: "x" }
{ headers: { "Accept-Language": "ko" }, body: "x" }
{ body: new ReadableStream(…) }                                  // duplex 없이
{ body: new ReadableStream(…), duplex: "half" }
{ body: new ReadableStream(…), duplex: "half", mode: "no-cors" }
```

- 칸마다 B 가 받은 순서는? 스트림 본문 칸들에서 페이지는 무엇을 받나?

### 3. 프리플라이트의 답 셋 (예측)

```js
// wa28b-28-q3.js
// 질문용 — 실행 대상 아님
// 다른 출처 B 에 PUT 「주문」 — 프리플라이트(OPTIONS)에 B 가 세 가지로 답한다
//   가. ACAO: 출처 · Allow-Methods: GET, POST, PUT, DELETE
//   나. Access-Control-Allow-Origin 없음
//   다. ACAO: 출처 · Allow-Methods: GET
await fetch(B + 길, { method: "PUT", body: "주문" });
// 페이지는 then 인가 catch 인가? B 의 서버 로그에는 무엇이 남나 — PUT 은 B 에 닿나?
```

- 세 칸의 페이지 결과와 서버 로그를 적어라. [25번 주제](../25-fetch-request-response/1-question.md)의 문항 2와 무엇이 다른가?

### 4. 같은 PUT 두 번 (예측)

```js
// wa28b-28-q4.js
// 질문용 — 실행 대상 아님
// 같은 주소에 같은 PUT 을 두 번 연달아 — B 의 OPTIONS 답에 붙는 Access-Control-Max-Age 를 세 가지로
//   600 · 0 · (헤더 없음)
for (let k = 0; k < 2; k++) await fetch(B + "/cors?id=m&…", { method: "PUT", body: "x" });
// 세 경우 각각 B 는 OPTIONS 를 몇 번 받나? 하네스를 세 번 새로 띄워도 같은가?
```

- 세 경우의 OPTIONS 횟수는?

### 5. 도착한 응답 헤더 (예측)

```js
// wa28b-28-q5.js
// 질문용 — 실행 대상 아님
// B 의 응답에는 X-Secret · Content-Language · Content-Type · Content-Length 가 실려 온다(ACAO: 출처)
//   가. Access-Control-Expose-Headers 없음  나. …: X-Secret  다. …: *
res.headers.get("x-secret"); res.headers.get("content-language"); [...res.headers.keys()];
// 세 경우 각각 get 의 값과 순회되는 이름은?
```

- 세 경우 각각의 `get` 값과 순회 이름 목록은?

### 6. `no-cors` 로 보내면 (예측)

```js
// wa28b-28-q6.js
// 질문용 — 실행 대상 아님
// 허용 헤더를 하나도 안 주는 B 에 — mode: 'no-cors'
const res = await fetch(B + "/cors?acao=none", { method: "POST", mode: "no-cors", body: "주문 3건", headers: { "X-A": "1" } });
res.type; res.status; res.ok; [...res.headers.keys()]; await res.text();
await fetch(B + "/cors?acao=none", { method: "PUT", mode: "no-cors", body: "x" });
// 각 값은? B 는 POST 를 받나 — 받는다면 X-A 는 실려 오나? PUT 은?
```

- 각 값과 서버 로그는?

### 7. 명세에서 프리플라이트의 실패가 닿는 자리 (왜)

- 문항 3의 서버 로그를 Fetch 명세의 어느 단계가 정하나? 단순 요청(25편 문항 2)과는 어느 단계에서 갈리나?

### 8. 리다이렉트와 프리플라이트 (경계)

- 프리플라이트가 붙는 `PUT` 의 **본 요청**이 307 을 받으면 브라우저는 새 주소에 무엇을 보내나? 다른 출처를 거쳐 페이지 출처로 돌아오면 `Origin` 은? **프리플라이트 자체**가 307 을 받으면?

### 9. CORS 가 못 막는 것 (경계)

- 같은 서버 B 에 Go `net/http` 클라이언트로 같은 `POST` 를 보내면? 그래서 CORS 는 누구를 위한 규칙인가?

### 10. 다른 주제와 잇기 (연결)

- [30번 주제](../30-request-body-and-content-type/1-question.md)에서 `JSON.stringify` 만 넘긴 본문의 `Content-Type` 은 무엇이었고, 그것을 다른 출처로 보내면 문항 1의 어느 칸에 해당하나?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
