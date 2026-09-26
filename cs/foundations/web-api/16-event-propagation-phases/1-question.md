# web-api/16 — 전파 3단계: 캡처·타깃·버블과 `target` 대 `currentTarget` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 리스너를 달고 떼는 한 줄은 [15번 주제](../15-listener-registration/1-question.md), 전파를 **멈추는 것**은 [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md), 그림자 경계의 재타기팅은 [12번 주제](../12-shadow-dom/1-question.md)가 정본이다. 여기는 **경로와 세 단계**만 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 DOM·HTML 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 세 겹과 그 위 네 자리에 capture 와 bubble 을 달고 안쪽을 누르면 (예측)

```js
// wa16b-16-q1.js
// 질문용 — 실행 대상 아님
// <div id="바깥"><div id="가운데"><button id="안쪽">누름</button></div></div>
const 자리 = [window, document, document.documentElement, document.body, 바깥, 가운데, 안쪽];
for (const t of 자리) {
  t.addEventListener('click', 기록, true);    // capture 를 먼저
  t.addEventListener('click', 기록);          // 그다음 bubble
}
function 기록(e) {
  줄.push([e.currentTarget, e.eventPhase, e.target, this === e.currentTarget]);
}
// 사람이 #안쪽 을 진짜로 한 번 누른다 — 줄 은 몇 줄이고 어떤 순서인가?
```

- `줄` 은 몇 줄인가? **순서대로** `currentTarget` 과 `eventPhase` 를 적어라.
- `target` 은 줄마다 무엇인가?
- `this === e.currentTarget` 은 줄마다 무엇인가?
- `#안쪽` 에 단 두 리스너의 `eventPhase` 는 각각 무엇인가?

### 2. 타깃 한 자리에 bubble 과 capture 를 번갈아 달면 (예측)

```js
// wa16b-16-q2.js
// 질문용 — 실행 대상 아님
// <p><button id="과녁">과녁</button></p>
과녁.addEventListener('click', () => 로그.push('A'), false);
과녁.addEventListener('click', () => 로그.push('B'), true);
과녁.addEventListener('click', () => 로그.push('C'), false);
과녁.addEventListener('click', () => 로그.push('D'), true);
과녁.parentNode.addEventListener('click', () => 로그.push('부모 capture'), true);
과녁.parentNode.addEventListener('click', () => 로그.push('부모 bubble'));
// 과녁을 누르면 로그 는? 네 리스너의 eventPhase 는?
```

- `로그` 를 순서대로 적어라.
- A·B·C·D 의 `eventPhase` 는 각각 무엇인가?
- 「타깃에서는 등록 순서대로 부른다」는 설명과 맞는가?

### 3. 디스패치가 끝난 뒤 붙들어 둔 이벤트를 읽으면 (예측)

```js
// wa16b-16-q3.js
// 질문용 — 실행 대상 아님
let 붙든것;
안쪽.addEventListener('click', e => { 붙든것 = e; });
// 사람이 #안쪽 을 누른 뒤, 리스너 밖에서
붙든것.target;          //  ?
붙든것.currentTarget;   //  ?
붙든것.eventPhase;      //  ?
```

- 세 값을 적어라.
- 리스너 안에서 `await` 한 뒤 `e.currentTarget` 을 쓰는 코드는 무엇이 문제인가?

### 4. 자식에게 난 아홉 가지 이벤트를 부모·`document`·`window` 가 받나 (예측)

```js
// wa16b-16-q4.js
// 질문용 — 실행 대상 아님
// 자식에게 이벤트가 나게 한다 — 진짜 클릭 · 진짜 포커스 이동 · 진짜 마우스 이동 · 그림 로드 · 요소 스크롤
// 부모·document·window 에는 capture 와 bubble 을 달고, target 이 그 자식인 것만 센다
const 이벤트 = ['click', 'focus', 'blur', 'focusin', 'focusout', 'mouseenter', 'mouseover', 'load', 'scroll'];
// 칸: e.bubbles · 부모 capture · 부모 bubble · document capture · window capture
```

- 아홉 줄 × 다섯 칸을 채워라.
- **부모의 capture 칸과 bubble 칸이 갈리는 줄**은 어느 것이고 공통점은 무엇인가?
- 부모에서 `focus` 를 받는 방법 두 가지를 대라.
- `window capture` 칸은 아홉 줄이 모두 같은가?

### 5. 생성자로 만든 이벤트를 부모가 받나 (예측)

```js
// wa16b-16-q5.js
// 질문용 — 실행 대상 아님
// <div id="부모"><p id="문단">…</p></div> — 부모에 bubble 리스너만 단다
문단.dispatchEvent(new CustomEvent('시험'));                        // 부모가 받나?
문단.dispatchEvent(new MouseEvent('click'));                        // 부모가 받나?
문단.dispatchEvent(new MouseEvent('click', { bubbles: true }));     // 부모가 받나?
```

- 세 줄 각각 부모가 받는가? 각 이벤트의 `bubbles` 는?
- 사람의 진짜 클릭이라면?
- 이 차이가 테스트에서 만드는 사고는 무엇인가?

### 6. 문서 밖의 나무에서 던질 때와 글자 위를 누를 때 (예측)

```js
// wa16b-16-q6.js
// 질문용 — 실행 대상 아님
const 떼어둔 = document.createElement('section');
const 아이 = document.createElement('span');
떼어둔.append(아이);
아이.addEventListener('시험2', e => e.composedPath());    // 경로는?
아이.dispatchEvent(new Event('시험2', { bubbles: true }));

// <p id="문단">그냥 글자 <b id="굵게">굵은 글자</b></p>
// 사람이 「그냥 글자」 위를 누르면 document 리스너가 보는 e.target 은? 「굵은 글자」 위는?
```

- 떼어 둔 나무의 `composedPath()` 를 적어라. 문서 안에서 던지면 무엇이 더 붙는가?
- 두 자리를 눌렀을 때의 `e.target` 을 적어라.
- `e.target` 이 텍스트 노드인 경우가 있었는가?

### 7. 디스패치 도중에 경로와 리스너를 바꾸면 (경계)

- 내려가는 길의 `#바깥` 이 capture 리스너 안에서 **아직 안 지난 `#가운데`** 에 bubble 리스너를 더하면 **이번 디스패치에서 불리는가**?
- 그 답은 [15번 주제](../15-listener-registration/1-question.md)의 「리스너 안에서 더한 것은 이번 판에 안 들어온다」와 어떻게 함께 성립하는가?
- 타깃이 자기 capture 리스너에서 **자기를 다른 부모로 옮기면** 올라오는 길은 **옛 조상**을 지나는가 **새 부모**를 지나는가?

### 8. 같은 클릭을 세 가지로 던지면 (경계)

- `new MouseEvent('click', { bubbles: true })` · `el.click()` · 사람의 진짜 클릭 — 순서표는 같은가?
- 셋이 **반드시 다른 값**을 내는 속성 하나를 대라.
- 「그러니 합성 이벤트로 테스트해도 된다」가 **틀리는 자리**를 둘 대라.

### 9. 명세의 dispatch 는 경로를 몇 번 훑나 (왜)

- 명세의 dispatch 가 경로를 훑는 **두 번**을 방향과 함께 적어라.
- 각 번에서 **어떤 리스너를 건너뛰나**?
- 그 두 규칙으로 문항 2의 순서를 설명하라.
- 버블하지 않는 이벤트인데 **타깃 자신의 bubble 리스너는 불리는** 이유는?

### 10. `Document` 의 「get the parent」 한 문장 (왜)

- HTML 표준은 `Document` 의 get the parent 를 어떻게 정하나?
- 그 문장이 문항 4의 어느 칸을 만드는가?
- 이 장치가 **막으려는 사고**는 무엇인가?

### 11. 왜 이 편의 본체는 「호출 순서 로그」인가 (왜)

- 창 ①(트리)이 **부적용**인 이유는?
- [15번 주제](../15-listener-registration/1-question.md)의 창 ④(몇 번 불렸나)로는 **왜 모자라나**?
- 창 ③ 은 이 편에서 무엇으로 바뀌었나? 그 바뀜을 무엇이라 부르나?
- `focus`·`mouseenter` 를 합성 이벤트가 아니라 진짜 입력으로 일으킨 이유는?

### 12. 다른 주제와 잇기 (연결)

- [12번 주제](../12-shadow-dom/1-question.md)에서 `e.target` 이 **보는 자리에 따라 바뀐** 것은 이 편의 「`target` 은 한 디스패치 내내 같다」와 어떻게 함께 성립하는가?
- [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md)의 `stopPropagation` 은 이 편의 경로에서 **무엇을 끊나**?
- [18번 주제](../18-event-delegation/1-question.md)의 위임은 이 편의 어느 단계에 기대나? 문항 4의 격자가 위임에 무엇을 경고하나?
- 리스너의 `this` 는 JS 갈래 [07번 주제](../../languages/js/syntax/07-this-binding-four-rules/1-question.md)의 네 규칙 중 **어디에** 속하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
