# web-api/23 — 포인터 이벤트: `pointerdown` 계열·마우스/터치/펜 통합·`setPointerCapture` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — `touch-action` 과 터치 스크롤의 첫 측정은 [19번 주제](../19-passive-and-scroll/1-question.md)(`touchmove` 쪽)가 정본이다. 여기는 **포인터 쪽의 순서 · 캡처 · `pointercancel`** 을 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 Pointer Events 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 마우스로 한 번 누르기 (예측)

```js
// wa20b-23-q1.js
// 질문용 — 실행 대상 아님
// 상자에 pointer* · mouse* · touch* · gotpointercapture · lostpointercapture · click 리스너
// 진짜 마우스를 상자 위로 옮기고 → 누르고 → 떼고 → 바깥으로 옮긴다
// 찍히는 줄을 순서대로 — 각 줄의 생성자 · pointerType · isPrimary · button · buttons 는?
// 같은 동작을 pointerType: 'pen' 으로 하면 무엇이 달라지나?
```

- 찍히는 줄을 순서대로 적어라. 포인터와 호환 마우스는 어떻게 섞이나?
- `click` 의 생성자와 `isPrimary` 는?
- 펜으로 하면 무엇이 달라지나?

### 2. 손가락으로 한 번 대기 (예측)

```js
// wa20b-23-q2.js
// 질문용 — 실행 대상 아님 · 리스너는 문항 1 과 같다
// 진짜 터치로 상자를 댔다 뗀다(끌지 않는다)
// 몇 줄이 어떤 순서로? 캡처 이벤트는 누가 부르지도 않았는데 오나? mouse* 는 어디에 끼나? click 의 pointerType 은?
```

- 찍히는 줄을 순서대로 적어라.
- 누가 부르지 않은 이벤트가 끼어 있나?
- `mousedown` 은 어디에 오나?

### 3. 밖으로 끌기 — 장치 × 캡처 방식 (예측)

```js
// wa20b-23-q3.js
// 질문용 — 실행 대상 아님
상자.addEventListener('pointerdown', e => {
  if (방식 === 'setPointerCapture') 상자.setPointerCapture(e.pointerId);
  if (방식 === 'releasePointerCapture') 상자.releasePointerCapture(e.pointerId);
});
// 상자(touch-action: none)에서 누르고 → 상자 밖 세 점으로 옮기고 → 밖에서 뗀다
// 장치 셋(mouse · pen · touch) × 방식 셋(아무것도 안 함 · set · release)
// 아홉 칸 각각 상자가 밖에서 받은 pointermove 수 · got/lost · pointerup 의 target 은?
```

- 아홉 칸을 채워라.
- 마우스와 터치의 「아무것도 안 함」 칸이 같은가?

### 4. `pointerdown` 에서 막으면 (예측)

```js
// wa20b-23-q4.js
// 질문용 — 실행 대상 아님
상자.addEventListener('pointerdown', e => { if (막기) e.preventDefault(); });
// 마우스 클릭 · 터치 탭 × 막기 false/true — 상자가 받는 이벤트 줄은?
// (mouseover · mousedown · mousemove · mouseup · click 가운데 무엇이 남나)
```

- 네 경우 각각 상자가 받는 이벤트 줄은?
- `click` 은 남나?

### 5. 골라 둔 글자를 끌면 (예측)

```js
// wa20b-23-q5.js
// 질문용 — 실행 대상 아님
// 글상자(user-select 기본)의 글자를 스크립트로 미리 골라 둔 뒤, 그 위에서 마우스로 누르고 오른쪽으로 끈다
// ① 그대로   ② pointerdown 에서 preventDefault   ③ 글상자에 user-select: none
// 각각 글상자가 받는 이벤트 줄은? pointerup 은 오나?
```

- 세 경우 각각 글상자가 받는 이벤트 줄은? `dragstart` 와 `pointercancel` 은 어디서 나나?

### 6. `touch-action` 과 끄는 방향 (예측)

```js
// wa20b-23-q6.js
// 질문용 — 실행 대상 아님
상자.style.touchAction = ta;   // auto · none · pan-y · pan-x · manipulation
// 터치로 상자를 위로 / 왼쪽으로 100 끈다(다섯 번 움직임) — 문서는 두 방향 다 스크롤할 수 있다
// 열 칸 각각 상자가 받은 pointermove · pointercancel · pointerup 과 「문서가 움직였나」는?
```

- 열 칸 각각 `pointermove` · `pointercancel` · `pointerup` · 「문서가 움직였나」는?
- `pan-y` 와 `pan-x` 는 어떻게 갈리나?

### 7. `pointercancel` 은 왜 오나 (왜)

- 명세는 어떤 경우에 포인터 스트림을 끊으라고 하나? 이 편에서 본 두 경우는?
- `pointercancel` 뒤에 `pointerup` 이 오나? 끝 처리를 어디에 둬야 하나?

### 8. 끌기와 장치 (경계)

- 끌기가 요소 밖에서 끊기는 것이 장치마다 다른 이유는?
- 터치에서 캡처를 **풀면** 무엇이 되나?

### 9. `pointerdown` 의 `preventDefault()` 가 닿는 범위 (경계)

- `pointerdown` 의 `preventDefault()` 가 **막지 않는** 이벤트를 명세 문장으로 대라.
- 그래서 `click` 을 막으려면 어디서 막나?

### 10. 다른 주제와 잇기 (연결)

- [19번 주제](../19-passive-and-scroll/1-question.md)의 「`touch-action: none` 이면 리스너 없이 안 움직인다」와 문항 6은 같은 사실의 어느 두 면인가?
- [18번 주제](../18-event-delegation/1-question.md)의 `mouseenter`/`mouseover` 차이는 포인터 쪽에서 어떤 짝으로 다시 나오나?
- 이 편의 **도구가 못 보는 것** 두 가지를 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
