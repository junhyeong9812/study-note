# web-api/27 — `AbortController` 로 취소와 타임아웃: `AbortSignal.timeout()`/`any()` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — `AbortSignal` 로 **리스너**를 떼는 것과 `any`·`timeout` 의 신호 쪽 성질은 [20번 주제](../20-listener-lifetime/1-question.md)가 정본이다. 여기는 **`fetch` 를 끊으면 페이지와 서버에서 각각 무엇이 남나**를 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 Fetch·DOM 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 취소 일곱 칸 (예측)

```js
// wa24b-27-q1.js
// 질문용 — 실행 대상 아님
// 서버 /work — 도착하면 「처리 시작」, 페이지가 /go 를 줄 때 「처리 끝(주문을 기록했다)」, 그다음 응답을 쓴다
// 페이지는 취소를 받은 뒤 서버가 연결 닫힘을 알아챌 때까지 기다렸다가 /go 를 준다
fetch("/work", { signal: AbortSignal.abort() });                                  // 가
fetch("/work", { signal: c.signal }); /* 서버 도착 뒤 */ c.abort();                // 나
fetch("/work", { signal: c.signal }); /* 서버 도착 뒤 */ c.abort("그만");          // 다
fetch("/work", { signal: AbortSignal.timeout(1000) });                           // 라
fetch("/work", { signal: AbortSignal.any([c.signal, AbortSignal.timeout(60000)]) }); /* 도착 뒤 */ c.abort();  // 마
fetch("/work", { signal: AbortSignal.any([c.signal, AbortSignal.timeout(1000)]) });  // 바 — 아무도 안 누름
fetch("/work", { signal: c.signal });                                            // 사 — abort 없음
// 칸마다 페이지가 받은 것(then/catch · 이름 · 문구)과 서버의 도착 · 처리 끝 · 연결 닫힘을 앎 · 응답 쓰기는?
```

- 칸마다 페이지가 받은 것과 서버의 네 열을 채워라.
- 서버에서 「처리 끝」이 된 칸은 어느 것들인가?

### 2. 응답을 받은 뒤의 취소 (예측)

```js
// wa24b-27-q2.js
// 질문용 — 실행 대상 아님
// 가. 청크 스트림에서 첫 read() 뒤 abort() → 둘째 read() 는? 그 오류 === signal.reason ?
// 나. 서버가 본문을 끝까지 쓴 뒤, 아직 안 읽은 채 abort() → text() 는? 그 오류 === signal.reason ?
// 다. 서버 도착 뒤 abort() → fetch 의 거부 === signal.reason ?
// 라. text() 로 다 읽은 뒤 abort() → 이미 받은 글은?
```

- 네 경우 각각 페이지가 받는 것(이름·문구)과 `=== signal.reason` 은?

### 3. 부르자마자 취소 (예측)

```js
// wa24b-27-q3.js
// 질문용 — 실행 대상 아님
for (let k = 0; k < 100; k++) {
  const c = new AbortController();
  const p = fetch(`/work?id=r${k}`, { signal: c.signal });
  c.abort();                                  // 부른 바로 그 잡에서
  try { await p; } catch (e) { /* e.name */ }
}
// AbortError 로 거부된 판은 몇 판? 서버에 도착한 판은?
```

- 거부된 판과 서버에 도착한 판은 각각 몇인가? 다시 돌리면 같은가?

### 4. `abort("그만")` 을 `e.name` 으로 거르면 (예측)

- 문항 1 의 「다」 칸에서 `catch (e) { if (e.name === "AbortError") … }` 는 무엇을 하나? 왜?

### 5. 취소가 요청을 없던 일로 만들지 않는 이유 (왜)

- Fetch 명세의 「abort the fetch() call」은 무엇을 끝내나? 무엇에 대해서는 아무 단계가 없나?

### 6. 재시도해도 되는 오류 (경계)

- `TimeoutError` 를 받고 같은 주문을 다시 보내면 무엇이 생길 수 있나? 무엇으로 막나?

### 7. 「보내지 않음」을 확실히 만드는 법 (경계)

- 문항 1 과 3 에서 서버에 **안 닿은** 것이 확실한 경우는 어느 것인가? 왜 그것만 확실한가?

### 8. 다른 주제와 잇기 (연결)

- [20번 주제](../20-listener-lifetime/1-question.md)가 잰 「이미 abort 된 signal 로 등록하면 호출 0회」와 문항 1 의 첫 칸은 어떤 같은 규칙인가?
- [JS 41번 주제](../../languages/js/syntax/41-cancellation-and-timeouts/1-question.md)가 node 안의 서버로 잰 것에 이 편이 더한 것은 무엇인가?
- [Go 34번 주제](../../languages/go/syntax/34-context-cancellation-deadlines-and-values/1-question.md)의 `context` 는 이 편의 서버에 없던 무엇을 주나?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
