# web-api/17 — `stopPropagation` 대 `preventDefault`: 전파를 멈추는 것과 기본 동작을 막는 것 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 경로와 세 단계는 [16번 주제](../16-event-propagation-phases/1-question.md), `passive` 에서 `preventDefault` 가 어떻게 되나는 [19번 주제](../19-passive-and-scroll/1-question.md)가 정본이다. 여기는 **멈추기와 막기**만 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 DOM·HTML 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 링크·체크박스·제출 단추를 네 가지 리스너로 누르면 (예측)

```js
// wa16b-17-q1.js
// 질문용 — 실행 대상 아님
// <div id="조상"> 링크(href="#도착") · 체크박스 · <form> 안의 제출 단추 </div>
// 대상 요소의 click 리스너가 부르는 것:  없음 | stopPropagation() | preventDefault() | 둘 다
대상.addEventListener('click', e => {
  if (멈춤) e.stopPropagation();
  if (막음) e.preventDefault();
});
조상.addEventListener('click', () => { 조상불림 = true; });
양식.addEventListener('submit', e => { 제출됨 = true; e.preventDefault(); });
// 사람이 진짜로 누른다 — 12 줄 각각: 조상 리스너가 불렸나? 기본 동작(이동·토글·제출)이 일어났나?
// 같은 격자를 new MouseEvent('click') · el.click() · new Event('click') 로 던지면?
```

- 대상 셋 × 네 줄 = 12 줄의 두 칸(조상 불림 · 기본 동작)을 채워라.
- 대상에 따라 **모양이 다른 줄**이 있는가?
- 같은 격자를 `new MouseEvent('click')` · `el.click()` · `new Event('click')` 로 던지면 **진짜와 갈리는 칸**은 각각 몇 칸이고 어디인가?

### 2. 체크박스 리스너 안에서 `checked` 를 읽으면 (예측)

```js
// wa16b-17-q2.js
// 질문용 — 실행 대상 아님
// <input type="checkbox" id="상자">   처음 checked = false
상자.addEventListener('click', e => {
  읽음 = 상자.checked;          // 리스너 안에서 읽는다
  if (막음) e.preventDefault();
});
// 사람이 누른다 — 막음 이 false 일 때와 true 일 때
// 리스너 안의 읽음 은? 디스패치가 끝난 뒤 상자.checked 는?
```

- 막지 않을 때와 막을 때, **리스너 안의 `읽음`** 과 **끝난 뒤의 `checked`** 를 적어라.
- 두 경우 `e.cancelable` 과 `e.defaultPrevented` 는?
- 「리스너 안에서 `checked` 를 보고 막을지 정한다」는 코드는 무엇을 보게 되나?

### 3. 같은 요소의 리스너 셋에서 둘째가 멈추면 (예측)

```js
// wa16b-17-q3.js
// 질문용 — 실행 대상 아님
// <div id="조상"><button id="단추">단추</button></div>
for (const 표 of ['첫째', '둘째', '셋째']) {
  단추.addEventListener('click', e => {
    로그.push(표);
    if (표 === '둘째') 둘째가_부를_것(e);
  });
}
조상.addEventListener('click', () => 로그.push('조상'));
// 둘째가_부를_것: 없음 | e.stopPropagation() | e.stopImmediatePropagation() | e.cancelBubble = true
// 따로: 조상의 capture 리스너가 e.stopPropagation() 을 부르면
```

- 다섯 경우 각각 `로그` 를 적어라.
- `cancelBubble = true` 는 어느 것과 같은가?
- 조상의 capture 리스너가 멈추면 **대상의 리스너는** 몇 개 불리나?

### 4. 조상이 막거나 조상이 멈추면 체크박스는 (예측)

```js
// wa16b-17-q4.js
// 질문용 — 실행 대상 아님
// <div id="상자조상"><input type="checkbox" id="상자"></div>   처음 checked = false
상자조상.addEventListener('click', e => e.preventDefault());        // ① 조상의 bubble 리스너가 막는다
// 사람이 누른 뒤 상자.checked 는?

상자조상.addEventListener('click', e => e.stopPropagation(), true); // ② 조상의 capture 리스너가 멈춘다
상자.addEventListener('click', () => 불린횟수++);
// 사람이 누른 뒤 상자.checked 는? 불린횟수 는?
```

- ①·② 각각 `상자.checked` 는? `change` 이벤트는 몇 번 나나?
- ② 에서 체크박스 자신의 click 리스너는 몇 번 불리나?
- 이 두 결과가 말해 주는 「기본 동작이 도는 시점」은?

### 5. `cancelable` 과 반환값 (예측)

```js
// wa16b-17-q5.js
// 질문용 — 실행 대상 아님
단추.addEventListener('x', e => { e.preventDefault(); 읽음 = e.defaultPrevented; });
단추.dispatchEvent(new Event('x', { cancelable: false }));   // 읽음 은? 반환값은?
단추.dispatchEvent(new Event('x', { cancelable: true }));    // 읽음 은? 반환값은?
// 리스너를 바꿔서
단추.addEventListener('x', e => { e.returnValue = false; 읽음 = e.defaultPrevented; });
단추.dispatchEvent(new Event('x', { cancelable: true }));    // 읽음 은?
```

- 세 번의 `읽음` 과 두 번의 반환값을 적어라.
- `addEventListener` 로 단 리스너가 `false` 를 돌려주면 `dispatchEvent` 의 반환값은?
- `onclick = () => false` 로 단 핸들러라면?

### 6. 키보드로 누르면 (예측)

```js
// wa16b-17-q6.js
// 질문용 — 실행 대상 아님
링크.addEventListener('click', e => { 로그.push(e.isTrusted + ' ' + e.detail); if (막음) e.preventDefault(); });
상자.addEventListener('click', e => { 로그.push(e.isTrusted + ' ' + e.detail); if (막음) e.preventDefault(); });
// 상자.focus() 뒤 진짜 Space 키 / 링크.focus() 뒤 진짜 Enter 키
// click 리스너가 불리나? 막음 이 true 면 체크가 바뀌나, 링크가 이동하나?
```

- 진짜 Space · 진짜 Enter 에서 click 리스너가 불리나? `isTrusted` 와 `detail` 은?
- `막음` 이 `true` 면 체크가 바뀌나? 링크가 이동하나?
- 「마우스 클릭만 막으려고 `click` 에서 막는다」는 코드의 부작용은?

### 7. activation target 을 잡는 조건 (왜)

- DOM 표준의 dispatch 는 **무엇을 보고** activation target 을 잡나?
- 그 조건에 `isTrusted` 가 들어 있나?
- 그래서 문항 1의 세 합성 던지기(`new MouseEvent` · `el.click()` · `new Event`)는 각각 그 조건에 맞는가?
- [14번 주제](../14-dialog-popover-scripting/1-question.md)의 가벼운 닫기와 이 편의 결과를 **같은 규칙으로 외우면** 무엇이 틀리나?

### 8. legacy-pre-activation 과 legacy-canceled-activation (왜)

- HTML 표준의 **legacy-pre-activation behavior** 와 **legacy-canceled-activation behavior** 는 각각 **언제** 무엇을 하나?
- 그 둘로 문항 2의 네 값을 설명하라.
- 링크에는 그런 「먼저 바꾸기」가 있나? 무엇으로 확인했나?

### 9. 두 표시를 읽는 절차 (왜)

- `stopPropagation` 이 세우는 표시는 명세의 **어느 절차**만 읽나?
- `preventDefault` 가 세우는 표시는 **어느 절차**만 읽나?
- 그래서 「둘 다」는 언제 필요하고, 습관처럼 둘 다 부르면 무엇이 조용히 깨지나?

### 10. 「막을 수 있나」와 「막혔나」 (경계)

- 둘을 각각 어느 속성으로 읽나?
- `passive` 리스너 안에서는 두 값이 어떻게 갈리나? (규칙은 [15번 주제](../15-listener-registration/1-question.md), 진짜 입력은 [19번 주제](../19-passive-and-scroll/1-question.md))
- 명세의 set the canceled flag 는 **두 가지 조건**이 다 맞을 때만 표시를 세운다 — 무엇인가?

### 11. 다른 주제와 잇기 (연결)

- [16번 주제](../16-event-propagation-phases/1-question.md)의 경로 그림에서 `stopPropagation` 은 **어디를** 끊나? capture 단계에서 부르면?
- [18번 주제](../18-event-delegation/1-question.md)의 위임이 `stopPropagation` 한 자식 때문에 깨지는 모양을 이 편의 격자로 설명하라.
- 막을 **기본 동작 자체**의 정본은 어디인가(HTML 갈래)?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
