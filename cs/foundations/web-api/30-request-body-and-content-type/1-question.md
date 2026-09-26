# web-api/30 — 요청 본문 만들기: `FormData`·`URLSearchParams`·JSON 과 `Content-Type` 자동 설정 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 폼 마크업이 만드는 본문(`method` × `enctype`)은 [HTML 21번 주제](../../languages/html/syntax/21-form-submission-model/1-question.md)가 물었다. 여기는 **스크립트가 본문을 만들 때 `Content-Type` 이 어떻게 정해지나**를 묻는다. 파일을 그대로 올리는 것은 [31번 주제](../31-blob-file-and-object-url/1-question.md)다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 Fetch·HTML 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 본문 일곱 × 직접 쓰나 (예측)

```js
// wa28b-30-q1.js
// 질문용 — 실행 대상 아님
// 같은 출처 A 의 /echo 에 POST — 본문 일곱 × Content-Type 을 직접 쓰나(안 씀 / 씀)
//   FormData(a=1, b=한)            직접 쓸 때 → multipart/form-data
//   URLSearchParams({a:1, b:"한"})  → application/x-www-form-urlencoded
//   "a=1"                          → text/plain
//   new Blob(['{"a":1}'], {type: "application/json"}) · new Blob(['{"a":1}'])  → application/json
//   JSON.stringify({a:1}) · TextEncoder 로 만든 ArrayBuffer                    → application/json
await fetch("/echo?id=…", { method: "POST", body, ...(씀 ? { headers: { "Content-Type": 쓸것 } } : {}) });
// 14칸마다 서버가 받은 Content-Type 은? 서버가 그 Content-Type 으로 파서를 골라 읽으면 무엇이 되나?
```

- 「안 씀」 일곱 칸에서 서버가 받은 `Content-Type` 을 적어라. 「씀」으로 바꾸면 서버 파싱이 달라지는 본문은?

### 2. 같은 `FormData` 두 번 (예측)

```js
// wa28b-30-q2.js
// 질문용 — 실행 대상 아님
const 만들기 = () => { const f = new FormData(); f.append("a", "1"); return f; };
await fetch("/echo?…", { method: "POST", body: 만들기() });
await fetch("/echo?…", { method: "POST", body: 만들기(), headers: { "Content-Type": "multipart/form-data" } });
// 두 요청의 원문(본문 바이트)은 같은가? 서버가 받은 Content-Type 은? 서버가 칸을 가를 수 있나?
```

- 원문 · `Content-Type` · 서버 파싱을 두 요청 각각 적어라.

### 3. 파일 칸 (예측)

```js
// wa28b-30-q3.js
// 질문용 — 실행 대상 아님
const f = new FormData();
f.append("a", "글");
f.append("b", new Blob(["x"]));
f.append("c", new Blob(["x"], { type: "text/csv" }), "r.csv");
f.append("d", new File(["x"], "n.txt", { type: "text/plain" }));
f.append("e", new File(["x"], "m.bin"));
f.get("b");   // 무엇이 나오나 — 문자열? Blob? 다른 것?
await fetch("/echo", { method: "POST", body: f });
// 원문에서 칸마다 filename 과 Content-Type 줄은?
```

- `f.get("b")` 는? 다섯 칸의 원문 머리(`filename` · `Content-Type`)는?

### 4. 같은 폼, 두 길 (예측)

```js
// wa28b-30-q4.js
// 질문용 — 실행 대상 아님
// <form method="post" enctype="multipart/form-data"> — title="메모" · 체크된 ok · 체크 안 된 no · 파일 f(메모 파일 한 줄)
await fetch("/echo?id=fetch", { method: "POST", body: new FormData(document.forms[0]) });
document.forms[0].requestSubmit();   // 같은 폼을 진짜로 제출
// 두 원문을 경계(boundary)만 가리고 견주면 같은가? 체크 안 된 no 는 실리나?
```

- 두 원문을 견준 결과와 실리는 칸은?

### 5. 파이썬 클라이언트 둘 (예측)

```js
// wa28b-30-q5.js
// 질문용 — 실행 대상 아님
// 대비 — 파이썬 둘
//   urllib.request.Request(url, data=b"a=1&b=%ED%95%9C")                       Content-Type 을 안 줌
//   urllib.request.Request(url, data=b'{"a": 1}')                              Content-Type 을 안 줌
//   urllib.request.Request(url, data=b'{"a": 1}', headers={"Content-Type": "application/json"})
//   requests.post(url, files={"f": ("n.txt", b"x", "text/plain")}, data={"a": "1"})
//   requests.post(… 위와 같이 …, headers={"Content-Type": "multipart/form-data"})
// 다섯 요청이 보낸 Content-Type 은? 서버가 파싱하면?
```

- 다섯 줄의 `Content-Type` 과 서버 파싱은?

### 6. 자동 `Content-Type` 과 직접 쓴 `Content-Type` 이 만나는 자리 (왜)

- Fetch 명세의 어느 두 문장이 문항 2의 결과를 만드나? 그때 본문은 어떻게 되나?

### 7. `Content-Type` 을 맡길 때와 쓸 때 (경계)

- `FormData` · JSON 문자열 · 타입 없는 `Blob`·`ArrayBuffer` 각각에 `Content-Type` 을 직접 써야 하나? 한 기준으로 말하라.

### 8. 파일 칸의 `filename` 은 누가 정하나 (경계)

- 서버는 그 값을 어떻게 다뤄야 하나?

### 9. 다른 주제와 잇기 (연결)

- [28번 주제](../28-cors-simple-and-preflight/1-question.md)의 문항 1 격자에서, `JSON.stringify` 만 넘긴 `POST` 를 다른 출처로 보내면 어느 칸인가? 서버가 `Content-Type` 을 안 보고 JSON 으로 파싱하면?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
