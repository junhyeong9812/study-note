# web-api/20 — 리스너 수명: `once`·`signal` 로 해제하기와 누수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 동일성 키 · `once` · `signal` 의 **호출 횟수**는 [15번 주제](../15-listener-registration/1-question.md)가 정본이다. 여기는 **「리스너가 무엇을 붙드나」를 회수 여부로** 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★★ **이 편은 바이트를 재지 않았다** — 「얼마나 새나」를 묻는 문항은 없다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 떼어 내기 전에 해 둔 한 가지 (예측)

```js
// wa20b-20-q1.js
// 질문용 — 실행 대상 아님
// 노드 n 을 문서에 붙였다가 떼고, n 에 FinalizationRegistry 를 걸고 gc() 를 부른다(10판)
// 떼기 전에 칸마다 다음 한 가지만 해 둔다 — 콜백이 불리는 칸은 어디인가?
①  (아무것도 안 함)
②  n.addEventListener(형, () => n.textContent);
③  addEventListener(형, () => n.textContent);                        // window 에
④  addEventListener(형, () => n.textContent, { once: true }); dispatchEvent(new Event(형));
⑤  addEventListener(형, () => n.textContent, { once: true });
⑥  const c = new AbortController(); addEventListener(형, () => n.textContent, { signal: c.signal }); c.abort();
⑦  const f = () => n.textContent; addEventListener(형, f); removeEventListener(형, f);
⑧  const f = () => n.textContent; addEventListener(형, f, true); removeEventListener(형, f);
```

- 여덟 칸 각각 콜백이 불리나(10판 중 몇 판)?
- ②와 ③은 클로저가 같다. 답이 같은가?
- ④와 ⑤를 가르는 것은 무엇인가?

### 2. 나머지 칸과 부모 상자 (예측)

```js
// wa20b-20-q2.js
// 질문용 — 실행 대상 아님
// 같은 격자의 나머지 칸
⑨  addEventListener(형, () => n.textContent, { signal: AbortSignal.abort() });
⑩  const id = n.id; addEventListener(형, () => document.getElementById(id));
⑪  const f = () => n.textContent; n.addEventListener(형, f); 전역배열.push(f);
⑫  전역배열.push(n);
// 부모 상자를 떼어 내고 「부모」에 콜백을 건다 — 리스너의 클로저는 자식 하나만 가리킨다
⑬  addEventListener(형, () => 자식.textContent);
```

- ⑨\~⑫ 각각 콜백이 불리나?
- ⑬ 에서 콜백을 건 것은 **부모**다. 리스너가 가리키는 것은 자식 하나다. 부모는 회수되나?

### 3. 신호 하나로 여러 리스너를 (예측)

```js
// wa20b-20-q3.js
// 질문용 — 실행 대상 아님
const 지휘 = new AbortController();
for (const t of [겉, 속, document, window]) t.addEventListener('가', () => 셈++, { signal: 지휘.signal });
겉.addEventListener('나', () => 셈++, { signal: 지휘.signal });
// ① abort 전에 네 대상에 가, 겉에 나 를 던지면 셈은?   ② 지휘.abort() 뒤 같은 것을 던지면?
// ③ 이제 이미 abort 된 지휘.signal 로 하나 더 등록하면 addEventListener 는 무엇을 하나? 던지면 불리나?
겉.addEventListener('다', () => z++, { signal: 지휘.signal });
```

- ①·② 의 셈은?
- ③ 에서 `addEventListener` 는 예외를 던지나? 무엇을 돌려주나? 던지면 `z` 는?

### 4. `abort` 이벤트 안에서 던지면 (예측)

```js
// wa20b-20-q4.js
// 질문용 — 실행 대상 아님
const 둘 = new AbortController();
겉.addEventListener('라', () => w++, { signal: 둘.signal });
둘.signal.addEventListener('abort', () => { w = 0; 겉.dispatchEvent(new Event('라')); 안에서 = w; });
둘.abort();
// 안에서 는 몇인가?
```

- `안에서` 는 몇인가? 왜 그런가?

### 5. `any` 와 `timeout` (예측)

```js
// wa20b-20-q5.js
// 질문용 — 실행 대상 아님
const 갑 = new AbortController(), 을 = new AbortController();
const 합 = AbortSignal.any([갑.signal, 을.signal]);
겉.addEventListener('마', () => a++, { signal: 합 });
갑.abort();
// 던지면 불리나? 합.aborted · 을.signal.aborted · 합.reason === 갑.signal.reason 은?

const 시한 = AbortSignal.timeout(0);
겉.addEventListener('바', () => b++, { signal: 시한 });
// 같은 잡에서 시한.aborted 는? abort 이벤트 뒤 reason.name 은? 그때 던지면 불리나?
```

- `갑.abort()` 뒤 던지면 불리나? `합.aborted` · `을.signal.aborted` · 두 `reason` 이 같은 객체인가?
- `timeout(0)` 인데도 같은 잡에서 `aborted` 는 무엇인가? 그 이유는 명세의 어느 말에 있나?

### 6. 화살표를 그려라 (왜)

```js
// wa20b-20-q6.js
// 질문용 — 실행 대상 아님
// 문항 1 의 칸 ② 와 칸 ③ — 클로저도 같고 n 도 같다. 리스너를 단 자리만 다르다
②  n.addEventListener(형, () => n.textContent);
③  window.addEventListener(형, () => n.textContent);
// 떼어 낸 n 에서 출발해 「누가 누구를 붙드나」 화살표를 그려라
```

- 두 칸의 참조 그래프를 그리고, 한쪽만 회수되지 않는 이유를 「뿌리에서 닿는 길」로 설명하라.

### 7. `once` 는 해제 도구인가 (경계)

- `once` 가 리스너를 풀어 주는 조건은 무엇인가? 그 조건이 안 서는 흔한 경우를 하나 대라.
- 「`once` 를 썼으니 새지 않는다」는 문장은 어디서 틀리나?

### 8. 조용한 실패 두 가지 (경계)

- `capture` 를 안 맞춘 `removeEventListener` 는 호출 횟수 쪽에서 어떻게 보였고([15번 주제](../15-listener-registration/1-question.md)), 메모리 쪽에서 어떻게 보이나?
- abort 한 컨트롤러를 다음 마운트에 다시 쓰면 무엇이 일어나고, 왜 알아채기 어려운가?

### 9. 이 격자를 무엇으로 읽나 (왜)

- `0/10` 칸과 `10/10` 칸 가운데 **명세가 보장하는** 쪽은 어느 것인가?
- 「몇 번째 틱에 불렸나」 블록을 따로 뗀 이유는?
- 이 편이 **못 재는** 것 두 가지를 대라.

### 10. 다른 주제와 잇기 (연결)

- [13번 주제](../13-custom-element-lifecycle/1-question.md)의 연결·분리 콜백에 `signal` 을 쓰는 관용구를 적고, 컨트롤러를 **언제** 새로 만들어야 하는지 말하라.
- [18번 주제](../18-event-delegation/1-question.md)의 위임은 이 편의 누수 모양과 어떤 관계인가?
- [JS 갈래 23번 주제](../../languages/js/syntax/23-map-set-and-weak-collections/1-question.md)는 같은 창을 어디서 열었고, 이 편은 어디서 열었나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
