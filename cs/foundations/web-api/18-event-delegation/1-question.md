# web-api/18 — 이벤트 위임: 조상 하나로 자손 전체 받기·`closest()` 로 되찾기 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 버블 단계는 [16번 주제](../16-event-propagation-phases/1-question.md), `stopPropagation` 은 [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md), 재타기팅은 [12번 주제](../12-shadow-dom/1-question.md)가 정본이다. 여기는 **조상 하나로 받고 되찾는 것**만 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 DOM 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 직접 등록과 위임에 나중에 더한 항목 (예측)

```js
// wa16b-18-q1.js
// 질문용 — 실행 대상 아님
// <ul id="목록"> <li id="항목1"><button class="지움"><span class="표">×</span></button> 첫째</li> … </ul>
for (const b of 목록.querySelectorAll('.지움')) b.addEventListener('click', () => 직접++);  // 직접 등록
목록.addEventListener('click', e => {                                                     // 위임
  찾음 = e.target.closest('li');
});
목록.insertBefore(새항목, …);   // 등록이 끝난 뒤에 #항목3 을 더한다
// 사람이 #항목1 의 × 와 #항목3 의 × 를 누른다 — 직접 은? e.target 은? 찾음 은?
```

- 두 자리 각각 `직접` · `e.target` · `찾음` 을 적어라.
- `e.target` 은 `li` 인가 `button` 인가 다른 것인가?
- 위임이 나중에 더한 항목을 받는 이유를 **경로**로 설명하라.

### 2. 목록의 안쪽 여백을 누르면 (예측)

```js
// wa16b-18-q2.js
// 질문용 — 실행 대상 아님
// <ul id="바깥목록"><li id="바깥항목">바깥 목록의 항목
//   <ul id="목록" style="padding:16px"> <li id="항목1">…</li> … </ul>
// </li></ul>
목록.addEventListener('click', e => {
  const 찾음 = e.target.closest('li');
  const 가드 = 찾음 && 목록.contains(찾음) ? 찾음 : null;
});
// 사람이 #목록 의 안쪽 여백(왼쪽 위 모서리에서 4px)을 누른다 — e.target · 찾음 · 가드 는?
```

- `e.target` · `찾음` · `가드` 를 적어라.
- `closest()` 가 **어디까지** 올라갔는가?
- 이 결과는 `closest()` 의 오작동인가 정의대로인가?

### 3. `pointer-events: none` 을 두 자리에 주면 (예측)

```js
// wa16b-18-q3.js
// 질문용 — 실행 대상 아님
// #항목5 .표 { pointer-events: none; }     — × 글자(span)만
// #항목4     { pointer-events: none; }     — 항목 li 통째로
// 사람이 두 항목의 × 한가운데를 누른다
// 위임 리스너의 e.target · closest('li') · 가드 는? 직접 등록한 단추 리스너는 불리나?
```

- 두 항목 각각 `e.target` · `closest('li')` · 가드 · 직접 등록 리스너의 호출 여부를 적어라.
- 두 결과가 갈리는 이유는 무엇인가?
- 「비활성 항목을 `pointer-events: none` 으로 막는다」의 함정은?

### 4. 그림자 안의 × 를 누르면 (예측)

```js
// wa16b-18-q4.js
// 질문용 — 실행 대상 아님
// <div id="목록"> <div id="열린"></div> <div id="닫힌"></div> </div>
열린.attachShadow({ mode: 'open' }).innerHTML   = '<button class="지움"><span class="표">×</span></button>';
닫힌.attachShadow({ mode: 'closed' }).innerHTML = '<button class="지움"><span class="표">×</span></button>';
목록.addEventListener('click', e => {
  e.target;                                                         //  ?
  e.target.closest('.지움');                                        //  ?
  e.composedPath()[0];                                              //  ?
  e.composedPath().find(n => n instanceof Element && n.matches('.지움'));  //  ?
  e.composedPath().length;                                          //  ?
});
// 그림자 안의 × 를 진짜로 누를 때 · 합성 new MouseEvent('click', { bubbles: true }) · 거기에 composed: true 를 더할 때
```

- `open` · `closed` 두 호스트에 대해 진짜 클릭 · 합성 `composed:false` · 합성 `composed:true` 의 다섯 값을 채워라.
- 그림자 안의 `span.표` 에서 `closest('.지움')` · `closest('#열린')` · `closest('#목록')` 을 부르면?
- `closed` 에서 바깥의 위임 리스너가 「무엇을 눌렀나」를 되찾을 방법이 있는가?

### 5. `focus` 를 위임하면 (예측)

```js
// wa16b-18-q5.js
// 질문용 — 실행 대상 아님
// <li id="항목6"><input id="칸6"> 여섯째</li>  — 목록 안
목록.addEventListener('focus',   e => 기록('focus', e.target.closest('li')));
목록.addEventListener('focus',   e => 기록('focus(capture)', e.target.closest('li')), true);
목록.addEventListener('focusin', e => 기록('focusin', e.target.closest('li')));
// 사람이 #칸6 을 눌러 포커스를 준다 — 세 리스너 각각 불리나, 무엇을 찾나?
```

- 세 리스너 각각 불리나? 불리면 무엇을 찾나?
- 셋이 갈리는 이유를 [16번 주제](../16-event-propagation-phases/1-question.md)의 격자로 설명하라.

### 6. `mouseenter` 와 `mouseover` 를 위임하면 (예측)

```js
// wa16b-18-q6.js
// 질문용 — 실행 대상 아님
// <ul id="목록"> <li id="항목1">첫째 항목 <button id="단추1">단추</button></li> <li id="항목2">…</li> </ul>
목록.addEventListener('mouseenter', e => 로그1.push(e.target));
목록.addEventListener('mouseover',  e => 로그2.push(e.target.closest('li')));
목록.addEventListener('mouseover',  e => {
  const li = e.target.closest('li');
  if (li && 목록.contains(li) && !(e.relatedTarget && li.contains(e.relatedTarget))) 로그3.push(li);
});
// 마우스: 목록 밖 → 항목1 글자 → 단추1 → 항목1 글자 → 항목2 글자 → 단추2
// 로그1 · 로그2 · 로그3 은?
```

- `로그1` · `로그2` · `로그3` 을 적어라.
- `로그2` 에 같은 항목이 여러 번 들어가는 이유는?
- `로그3` 의 가드가 보는 `relatedTarget` 은 무엇인가?

### 7. 위임이 성립하는 조건 (왜)

- 위임 리스너가 자손의 이벤트를 받으려면 **이벤트가 무엇을 해야** 하나?
- 그 조건이 **깨지는 자리**를 넷 대라.
- 각 자리의 처방을 한 줄씩 적어라.

### 8. `stopPropagation` 한 자손 (경계)

- 자손이 `stopPropagation()` 을 부르면 그 자손의 직접 리스너와 위임 리스너는 각각 불리나?
- [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md)의 격자에서 어느 칸이 바뀐 것인가?
- 자손 쪽이 원래 하려던 일이 「기본 동작을 막기」였다면 무엇을 불렀어야 했나?

### 9. `closest()` 와 `contains()` 의 한 줄 가드 (왜)

- `closest()` 는 명세상 어디서부터 어디까지 보나? **멈출 자리를 줄 수 있나**?
- 가드가 없으면 어떤 사고가 **예외 없이** 나나?
- `matches()` · `closest()` · `querySelector()` 는 각각 어느 쪽을 보나?

### 10. 위임을 안 쓰는 편이 나은 자리 (경계)

- 위임이 **이득이 없는** 경우를 대라.
- 위임 조상 안에 그림자 컴포넌트가 있을 때 **컴포넌트 쪽**이 해야 할 일은?
- 이 편이 **재지 않은 것**은 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- [12번 주제](../12-shadow-dom/1-question.md)가 합성 이벤트로 잰 `composedPath()` 칸 수와 이 편의 진짜 클릭 칸 수가 **다른 이유**는? 빠진 칸의 **성질**은 같은가?
- `closest()` 가 받는 인자의 문법은 CSS 갈래의 몇 번 주제가 정본인가?
- 위임 리스너 하나를 **떼는** 법은 어느 주제에 있나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
