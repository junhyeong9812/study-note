# web-api/15 — 리스너 등록과 해제: `addEventListener` 옵션 객체·`removeEventListener` 의 동일성 조건·`handleEvent` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 전파 3단계와 `capture` 가 무엇을 하는지는 [목록의 **16번 주제**](../16-event-propagation-phases/), `stopPropagation` 과 `preventDefault` 는 [목록의 **17번 주제**](../17-stoppropagation-vs-preventdefault/), `passive` 가 왜 생겼나는 [목록의 **19번 주제**](../19-passive-and-scroll/)가 정본이다. 여기는 **리스너를 다는 한 줄과 떼는 한 줄**만 다룬다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> ★ **재지 않은 것이 있다** — `passive` 의 성능 이득과 리스너가 붙드는 메모리는 **하나도 재지 않았다.**
> ★ 선행은 [01번 주제](../01-document-and-node-tree/2-summary.md)(노드 트리)와 JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **07번**(`this` 네 규칙)이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 달고 지운 뒤 던지면 (예측)

```js
// wa12b-15-q1.js
const a = document.createElement('div');
let n = 0;
a.addEventListener('t', () => n++);
a.removeEventListener('t', () => n++);
a.dispatchEvent(new Event('t'));       // n 은?

const b = document.createElement('div');
let m = 0;
const 이름있는것 = () => m++;
b.addEventListener('t', 이름있는것);
b.removeEventListener('t', 이름있는것);
b.dispatchEvent(new Event('t'));       // m 은?

function 원본() {}
원본.bind(null) === 원본.bind(null)     //  ?
```

- 세 값을 적어라.
- 두 익명 함수의 `toString()` 은 같은가? `===` 는?
- **명부가 보는 것은 둘 중 어느 쪽인가**?
- `bind` 로 만든 리스너를 지우려면 어떻게 해야 하는가?

### 2. 같은 것을 두 번 적으면 (예측)

```js
// wa12b-15-q2.js
const c = document.createElement('div');
let k = 0;
const f = () => k++;
c.addEventListener('t', f);
c.addEventListener('t', f);
c.dispatchEvent(new Event('t'));       // k 는?

c.removeEventListener('t', f);
c.dispatchEvent(new Event('t'));       // 그 다음 k 는?

c.addEventListener('t', f, true);
c.addEventListener('t', f, false);
c.dispatchEvent(new Event('t'));       // 이번엔?
```

- 세 값을 적어라.
- **둘째 등록은 예외인가 조용한가**?
- 마지막 줄만 값이 다른 이유는 무엇인가?
- 매번 새 화살표 함수를 넘기면 무슨 일이 나는가?

### 3. 등록 옵션과 해제 옵션을 엇갈리게 주면 (예측)

```js
// wa12b-15-q3.js
// 등록 옵션                                 해제 옵션
undefined                                    undefined
{ capture: true }                            { capture: true }
{ capture: true }                            undefined
undefined                                    { capture: true }
true                                         { capture: true }
{ capture: false }                           true
{ once: true }                               undefined
{ passive: true }                            { passive: false }
{ capture: true, once: true, passive: true } { capture: true }
{ capture: false, once: true }               { capture: true }
```

- **열 줄 각각 지워지는가**?
- **안 지워지는 줄들의 공통점은 무엇인가**?
- 동일성에 들어가는 칸은 몇 개이고 무엇인가?
- 세 번째 인자가 불리언일 때 그것은 무슨 칸인가?

### 4. 콜백 자리에 함수가 아닌 것을 넣으면 (예측)

```js
// wa12b-15-q4.js
const 손잡이 = { 이름: '나는 객체다', handleEvent(e) { /* this.이름 은? */ } };
겉.addEventListener('가', 손잡이);
겉.dispatchEvent(new Event('가'));

const 늦은 = {};                        // handleEvent 가 없다
겉.addEventListener('나', 늦은);
겉.dispatchEvent(new Event('나'));       // 예외인가?
늦은.handleEvent = () => {};             // 나중에 붙이면?
겉.dispatchEvent(new Event('나'));

겉.addEventListener('다', 1);            //  ?
겉.addEventListener('다', null);         //  ?
```

- 여섯 자리의 결과를 적어라.
- **`handleEvent` 를 언제 찾는가** — 등록할 때인가 부를 때인가?
- 그 사실이 만드는 사고는 무엇인가?

### 5. 네 가지 꼴로 달고 `this` 를 찍으면 (예측)

```js
// wa12b-15-q5.js
겉.addEventListener('라', function (e) { /* this 는? */ });
겉.addEventListener('라', (e) => { /* this 는? */ });
겉.addEventListener('라', function () { /* this 는? */ }.bind({ 표: '내가 묶은 것' }));
겉.addEventListener('라', { 표: '객체 자신', handleEvent() { /* this 는? */ } });
```

- 네 자리의 `this` 를 각각 적어라.
- 보통 함수의 `this` 는 `target` 인가 `currentTarget` 인가?
- 화살표 함수에서 그 값을 받으려면 어떻게 하는가?
- 한 객체를 두 요소에 등록하면 `this` 와 `currentTarget` 중 무엇이 갈리는가?

### 6. 떼는 세 가지 길 (경계)

```js
// wa12b-15-q6.js
el.addEventListener('d', f, { once: true });
el.dispatchEvent(new Event('d'));  el.dispatchEvent(new Event('d'));

const 지휘 = new AbortController();
el.addEventListener('e', g, { signal: 지휘.signal });
지휘.abort();

const 이미 = new AbortController();  이미.abort();
el.addEventListener('f', h, { signal: 이미.signal });
```

- `once` 는 **부르기 전에 빠지는가 부른 뒤에 빠지는가** — 어떻게 확인하는가?
- `once` 리스너가 예외를 던지면 그 줄은 남는가?
- **이미 `abort()` 된 signal 로 등록하면** 어떻게 되는가?
- 세 길 가운데 **`capture` 를 다시 안 적어도 되는** 것은 무엇인가?

### 7. 리스너 안에서 목록을 건드리면 (예측)

```js
// wa12b-15-q7.js
// ① 더하기
g.addEventListener('바', () => { 로그.push('첫째'); g.addEventListener('바', 뒤늦); });
g.addEventListener('바', () => 로그.push('둘째'));
g.dispatchEvent(new Event('바'));          // 로그는?
g.dispatchEvent(new Event('바'));          // 그 다음 판은?

// ② 지우기
h.addEventListener('사', () => { 로그2.push('첫째'); h.removeEventListener('사', 셋째); });
h.addEventListener('사', () => 로그2.push('둘째'));
h.addEventListener('사', 셋째);
h.dispatchEvent(new Event('사'));          // 로그2 는?

// ③ 지웠다 다시 더하기
i.addEventListener('아', () => { 로그3.push('첫째'); i.removeEventListener('아', 자기); i.addEventListener('아', 자기); });
i.addEventListener('아', 자기);
i.dispatchEvent(new Event('아'));          // 로그3 은?
```

- 네 배열을 적어라.
- **더하기와 지우기가 대칭인가**?
- ③ 이 그렇게 되는 이유를 ①·② 로 설명하라.
- 명세는 디스패치를 시작할 때 무엇을 하는가?

### 8. `passive` 가 무엇을 막나 (경계)

```js
// wa12b-15-q8.js
상자.addEventListener('wheel', e => { e.preventDefault(); /* defaultPrevented 는? */ }, { passive: true });
상자2.addEventListener('wheel', e => { e.preventDefault(); /* defaultPrevented 는? */ }, { passive: false });
```

- 두 값을 적어라.
- **예외가 나는가 경고가 나는가 아무 일도 안 나는가**?
- 그때 `e.cancelable` 은 무엇인가? 그것이 왜 함정인가?
- 「막을 수 있나」를 `cancelable` 로 판정하면 왜 틀리는가?

### 9. 같은 한 줄이 대상에 따라 갈리는 이유 (왜)

- `window` 에 단 `touchstart` 리스너에서 `preventDefault()` 가 안 먹히는데 **평범한 `div` 에서는 먹힌다** — 왜인가?
- 그 규칙이 걸리는 **대상 넷**과 **이벤트 넷**을 대라.
- 되돌리려면 무엇을 적는가?
- 이 규칙을 **코드만 읽어서** 알 수 있는가?

### 10. 왜 창 ④ 가 이 주제의 본체인가 (왜)

- 이 주제에서 **창 ① 과 창 ② 가 부적용인 이유**를 각각 한 줄로 적어라.
- **창 ③ 은 이 주제에서 무엇으로 바뀌었나**? 그 바뀜을 무엇이라 부르는가?
- 창 ④ 가 하는 일을 한 문장으로 적어라.
- 콘솔을 근거로 쓸 때 **믿으면 안 되는 수치**는 무엇인가?

### 11. 이 주제의 실패는 왜 전부 조용한가 (경계)

- 이 주제에서 **예외를 던지는 자리**를 전부 대라.
- 나머지 네 가지 실패를 대고, 각각이 **어떻게 드러나는지** 적어라.
- 그래서 리스너 코드에서 「됐다」를 확인하는 방법은 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- `capture` 가 **무엇을 하는지**의 정본은 어느 주제이고, **이 주제가 맡은 부분**은 무엇인가?
- [12번 주제](../12-shadow-dom/2-summary.md)에서 리스너를 **어디에 다느냐**가 무엇을 바꾸는가?
- `signal` 로 떼는 관용구가 [목록의 **13번 주제**](../13-custom-element-lifecycle/)(커스텀 요소 수명주기)에서 특히 값어치를 내는 이유는?
- 보통 함수의 `this` 규칙이 JS 갈래 목록([`js/syntax/README.md`](../../languages/js/syntax/README.md))의 **07번** 중 어느 규칙인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
