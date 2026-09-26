# web-api/21 — 커스텀 이벤트: `CustomEvent`·`dispatchEvent`·`detail`·`bubbles`/`composed` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 재타기팅과 두 스위치의 첫 측정은 [12번 주제](../12-shadow-dom/1-question.md), 반환값은 [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md)가 정본이다. 여기는 **`CustomEvent` 격자 · 동기성 · 예외 · `detail`** 을 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 DOM 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 그림자 안에서 던진 알림 (예측)

```js
// wa20b-21-q1.js
// 질문용 — 실행 대상 아님
// 호스트 둘(open · closed) 안에 각각 #안쪽. 리스너는 #안쪽 · 호스트 · document 에 있다.
안쪽.dispatchEvent(new CustomEvent('알림', { bubbles, composed }));
// bubbles × composed 네 가지 × open/closed — 각 자리에서 불리나?
// 불리면 그 자리에서 본 e.target 과 e.composedPath().length 는?
```

- 여덟 줄(스위치 넷 × 모드 둘)에서 각 자리가 불리나? 불리면 `target` 과 경로 길이는?
- 문서까지 닿는 줄은 어느 것인가?
- `open` 과 `closed` 는 **무엇이** 다른가 — 닿는 곳인가, 보이는 것인가?

### 2. 앞 · 리스너들 · 뒤 (예측)

```js
// wa20b-21-q2.js
// 질문용 — 실행 대상 아님
단추.addEventListener('가', () => 순.push('리스너 1'));
단추.addEventListener('가', () => { 순.push('리스너 2 — 안에서 나 를 던짐'); 단추.dispatchEvent(new CustomEvent('나')); 순.push('리스너 2 — 나 를 던진 뒤'); });
단추.addEventListener('가', () => 순.push('리스너 3'));
단추.addEventListener('나', () => 순.push('  나 의 리스너'));
단추.addEventListener('가', () => Promise.resolve().then(() => 순.push('리스너 4 가 건 마이크로태스크')));
단추.addEventListener('가', () => 순.push('리스너 5'));
순.push('dispatchEvent 앞');
단추.dispatchEvent(new CustomEvent('가'));
순.push('dispatchEvent 뒤');
// 순 의 아홉 줄을 순서대로 적어라
```

- `순` 의 아홉 줄을 순서대로 적어라.
- 「dispatchEvent 뒤」와 「리스너 4 가 건 마이크로태스크」는 어느 쪽이 먼저인가?

### 3. 리스너가 던지면 (예측)

```js
// wa20b-21-q3.js
// 질문용 — 실행 대상 아님
window.addEventListener('error', e => 오류.push(e.message));
단추.addEventListener('다', () => { 순2.push('리스너 1 — 던지기 직전'); throw new Error('리스너가 터진다'); });
단추.addEventListener('다', () => 순2.push('리스너 2'));
try { 반환 = 단추.dispatchEvent(new CustomEvent('다', { cancelable: true })); }
catch (e) { 잡힘 = e.name; }
// 리스너 2 는 불리나? catch 는 무엇을 잡나? 반환은? 오류 에는 무엇이 들어가나?
```

- 리스너 2 는 불리나? `catch` 는 무엇을 잡나? `반환` 은?
- `오류` 배열에는 무엇이 들어가나? 그것은 명세의 어느 절차에서 오나?

### 4. 건너간 상자 (예측)

```js
// wa20b-21-q4.js
// 질문용 — 실행 대상 아님
const 보낸것 = { 수: 1, 목록: ['가'] };
단추.addEventListener('마', e => { 받은것 = e.detail; e.detail.수 = 2; e.detail.목록.push('나'); });
const ev = new CustomEvent('마', { detail: 보낸것 });
단추.dispatchEvent(ev);
// 받은것 === 보낸것 ? 디스패치 뒤 보낸것 은? new CustomEvent('x').detail 은? e.detail = 5 (엄격 모드) 는?
// ev 의 isTrusted · bubbles · composed · cancelable 은?
```

- `받은것 === 보낸것` · 디스패치 뒤 `보낸것` · 기본 `detail` · 대입 결과는?
- 네 기본값은?

### 5. 같은 객체를 다시 (예측)

```js
// wa20b-21-q5.js
// 질문용 — 실행 대상 아님
const e3 = new CustomEvent('바');
단추.addEventListener('바', () => { 단추.dispatchEvent(e3); });   // ① 리스너 안에서 같은 객체를
단추.dispatchEvent(e3);
단추.dispatchEvent(e3);                                             // ② 끝난 뒤 한 번 더
단추.dispatchEvent(Object.create(CustomEvent.prototype));           // ③ Event 가 아닌 객체
// ① ② ③ 각각 무엇이 나오나?
```

- ①·②·③ 각각 무엇이 나오나? 예외라면 **이름**은?

### 6. 진짜 클릭과 `el.click()` (예측)

```js
// wa20b-21-q6.js
// 질문용 — 실행 대상 아님
단추.addEventListener('click', () => { 순3.push('리스너 1'); Promise.resolve().then(() => 순3.push('리스너 1 이 건 마이크로태스크')); });
단추.addEventListener('click', () => 순3.push('리스너 2'));
// ① 사용자가 진짜로 한 번 누르면 순3 은?
// ② 스크립트가  단추.click(); 순3.push('el.click() 다음 줄');  하면 순3 은?
```

- ①·② 의 `순3` 을 적어라. 어느 자리가 갈리나?

### 7. `composed: true, bubbles: false` 인데 호스트가 받는 이유 (왜)

- 위로 가지 않는 이벤트를 호스트는 왜 받나? 호스트에서 이벤트는 어느 단계인가?
- 같은 이벤트를 문서는 왜 못 받나?

### 8. `closed` 가 막는 것 (경계)

- `closed` 호스트 바깥의 리스너가 본 `composedPath()` 에서 무엇이 빠지나? 그것은 명세의 어느 개념이 하는 일인가?
- 「`closed` 면 이벤트가 바깥으로 안 나간다」는 문장은 참인가?

### 9. 다른 주제와 잇기 (연결)

- [18번 주제](../18-event-delegation/1-question.md)에서 문서 수준 위임이 못 받은 합성 이벤트는 이 편의 격자에서 어느 줄인가?
- [13번 주제](../13-custom-element-lifecycle/1-question.md)의 생성자 예외와 문항 3의 리스너 예외는 어떤 점에서 같은 모양인가?
- [16번 주제](../16-event-propagation-phases/1-question.md)가 잰 생성자 기본값이 이 편의 어느 실수로 이어지나?

### 10. 누가 보장하나 (경계)

- 이 편의 서술 가운데 **예외 문구**와 **예외 이름**은 각각 누구의 것인가?
- 「진짜 클릭에서는 리스너 사이에 마이크로태스크가 돈다」는 이 문서가 **어느 층**으로 적었나? 왜 그런가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
