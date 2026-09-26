# web-api/26 — 응답 본문과 스트리밍: `json()`/`text()`/`blob()` 은 한 번만·`body` 와 `ReadableStream` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — `fetch` 가 언제 이행·거부하나는 [25번 주제](../25-fetch-request-response/1-question.md)가, 본문을 읽는 중의 취소는 [27번 주제](../27-abort-and-timeout/1-question.md)가 정본이다. 여기는 **본문을 몇 번 · 어떤 단위로 읽나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 Fetch·Streams 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 같은 본문을 여러 번 (예측)

```js
// wa24b-26-q1.js
// 질문용 — 실행 대상 아님
const r = await fetch("/status?code=200");
r.bodyUsed; await r.json(); r.bodyUsed; await r.json(); await r.text(); r.clone();   // 각각?
const s = await fetch("/status?code=200"); const 복 = s.clone(); await s.json(); await 복.text();  // ?
const t = await fetch("/status?code=200"); const 읽개 = t.body.getReader();
t.body.locked; t.bodyUsed; await t.text(); 읽개.releaseLock(); await t.text();          // ?
const u = await fetch("/status?code=200"); await u.blob(); await u.arrayBuffer();      // ?
```

- 각 줄의 결과나 예외(이름과 문구 전문)를 적어라.
- 예외 문구는 몇 가지인가? 각각 어느 상태에서 나나?

### 2. 청크를 받을 때마다 서버에게 묻기 (예측)

```js
// wa24b-26-q2.js
// 질문용 — 실행 대상 아님
// 서버 — 헤더는 곧바로 보내고, 청크 다섯(「줄1\n」…)과 끝 표시는 /go 를 하나 받을 때마다 하나씩
const res = await fetch("/chunks?id=s1&n=5");     // 이때 서버가 보낸 청크 수는?
const 읽개 = res.body.getReader();
// /go → read() → 서버에게 「보낸 청크 수 · 끝까지 다 썼나」를 묻는다 — 여섯 번
// read() 마다 받은 바이트와 그때의 서버 상태는?
```

- `fetch` 가 정착할 때 서버가 보낸 청크 수는?
- `read()` 여섯 번 각각에서 받은 것과 그때의 서버 상태는?

### 3. 같은 서버에 `text()` (예측)

```js
// wa24b-26-q3.js
// 질문용 — 실행 대상 아님
// 같은 서버 — 이번에는 res.text() 를 먼저 걸어 두고, /go 를 하나씩 주며 서버가 보냈다고 말할 때마다 본다
const 글 = res.text().then(t => { 정착 = true; return t; });
// 서버가 청크 1…5 를 보낸 뒤마다 정착은? 끝 표시 뒤 text() 가 돌려주는 것은?
```

- 다섯 번의 「정착」 값과 마지막에 돌려주는 글은?

### 4. 글자 중간에서 잘린 조각 (예측)

```js
// wa24b-26-q4.js
// 질문용 — 실행 대상 아님
// 서버가 「가나\n」 일곱 바이트를 2 · 2 · 3 바이트로 쪼개 보낸다
const [갑, 을] = res.body.tee();
// 갑의 조각마다 new TextDecoder().decode(조각) → ?
// 한 TextDecoder 에 decode(조각, { stream: true }) → ?
// 을.pipeThrough(new TextDecoderStream()) 를 끝까지 읽으면 → ?
```

- 세 방법 각각의 배열을 적어라.

### 5. `clone()` 하고 한쪽만 읽으면 (왜)

- 안 읽은 쪽에 무슨 일이 생기나? 명세의 어느 문장이 그것을 말하나? 이 편은 무엇을 봤고 무엇을 안 쟀나?

### 6. `bodyUsed` 와 `locked` (경계)

- 둘이 갈리는 상태를 하나 대라. 그때 `text()` 는?

### 7. `fetch` 가 정착했다는 것 (경계)

- 그 순간 본문은 어디까지 와 있나? 문항 2의 첫 줄이 그것을 어떻게 증명하나 — 왜 흔들리지 않나?

### 8. 다른 주제와 잇기 (연결)

- [25번 주제](../25-fetch-request-response/1-question.md)의 「한 번 쓴 `Request`」와 문항 1은 어떤 같은 규칙인가?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
