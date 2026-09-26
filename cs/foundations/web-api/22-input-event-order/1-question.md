# web-api/22 — 입력 이벤트의 순서: `keydown`→`beforeinput`→`input`→`change` 와 IME 조합 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★ **이웃 주제와의 경계** — 키보드가 `click` 을 만드는 것과 Enter 의 암묵 제출은 [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md)가 정본이다. 여기는 **한 번 타이핑의 이벤트 순서와 조합**을 묻는다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰과 명세 문장이다. 이식성은 주장 범위 밖이다.
> ★★★ **조합(IME)을 묻는 문항은 CDP 의 흉내를 전제로 한다** — 실제 입력기의 순서는 이 편이 **못 쟀다.**
> ★ 아래 코드 조각은 **질문용 발췌**다 — 실제로 돌린 전문은 [2-summary.md](2-summary.md)에 있다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 빈 칸에 `a` 하나, 그리고 떠나기 (예측)

```js
// wa20b-22-q1.js
// 질문용 — 실행 대상 아님
// 빈 <input> 에 포커스 · 진짜 키 a 를 한 번 누르고 뗀다 · 그다음 바깥 단추를 진짜로 누른다
// input 에 단 리스너: keydown keypress beforeinput textInput input keyup change blur
//                    compositionstart compositionupdate compositionend paste
// 몇 줄이 어떤 순서로 찍히나? 각 줄의 inputType · data · 그때 value 는?
```

- 찍히는 줄을 순서대로 적어라.
- 값이 `""` 에서 `"a"` 로 바뀐 것을 처음 보는 이벤트는 어느 것인가?
- `change` 와 `blur` 는 어느 쪽이 먼저인가?

### 2. Backspace · Enter · 붙여넣기 (예측)

```js
// wa20b-22-q2.js
// 질문용 — 실행 대상 아님 · 리스너는 문항 1 과 같다
// ② 값 "ab" · 캐럿 끝 · Backspace 를 누르고 뗀다
// ③ 값 "ab" · 캐럿 끝 · c 를 누르고 뗀다 → Enter 를 누르고 뗀다(폼 없음) → 다른 칸으로 포커스가 간다
// ④ 빈 값 · Ctrl+V (클립보드에 "붙일글")
// 각각 어떤 줄이 찍히나? input 이 안 오는 경우는? change 는 어디서 오나?
```

- ②·③·④ 각각 `keypress` 가 오나?
- ③ 에서 Enter 의 `input` 은 오나? `change` 는 어느 줄에서 오고, 떠날 때 또 오나?
- ④ 의 `paste` 와 `beforeinput` 의 순서, 그리고 `inputType` 은?

### 3. CDP 로 흉내 낸 조합 (예측)

```js
// wa20b-22-q3.js
// 질문용 — 실행 대상 아님 · 리스너는 문항 1 과 같다
// CDP 로 조합을 흉내 낸다 — 키 이벤트는 넣지 않는다
Input.imeSetComposition({ text: 'ㅎ' })
Input.imeSetComposition({ text: '하' })
Input.imeSetComposition({ text: '한' })
Input.insertText({ text: '한' })
// 그다음 바깥 단추를 진짜로 누른다 — 찍히는 줄과 각 줄의 isComposing · inputType · 그때 value 는?
```

- 키 이벤트가 찍히나?
- `input` 은 몇 번 오고, 그때마다 `value` 는 무엇인가?
- `compositionupdate` 와 `beforeinput` 은 어느 쪽이 먼저인가? 명세 표와 같은가?

### 4. 세 가지 칸에 같은 네 입력 (예측)

```js
// wa20b-22-q4.js
// 질문용 — 실행 대상 아님
// 세 칸 <input> · <textarea> · <div contenteditable> — 처음 내용 "ab" · 캐럿 끝
// 네 입력 — 글자 c · Backspace · Enter · Ctrl+V("붙일글")
// 열두 칸 각각 beforeinput 의 inputType, input 이 오나, 끝 내용은?
```

- 열두 칸을 채워라. `<input>` 과 **갈리는** 칸은 어디인가?

### 5. `beforeinput` 에서 막으면 (예측)

```js
// wa20b-22-q5.js
// 질문용 — 실행 대상 아님
칸.addEventListener('beforeinput', e => { e.preventDefault(); });   // ① ② ④
칸.addEventListener('keydown', e => { e.preventDefault(); });       // ③
// ① 글자 a   ② Ctrl+V   ③ 글자 a(keydown 에서 막음)   ④ CDP 조합 흉내 ㅎ → 한 → 확정
// 각각 beforeinput 의 cancelable · defaultPrevented · 그 밖에 온 이벤트 · 끝 value 는?
```

- 네 경우 각각 `cancelable` · `defaultPrevented` · 그 밖에 온 이벤트 · 끝 value 는?
- ④ 에서 막히나?

### 6. Enter 처리기 둘 (예측)

```js
// wa20b-22-q6.js
// 질문용 — 실행 대상 아님
칸.addEventListener('keydown', e => {
  if (e.key === 'Enter') 보내기A(칸.value);                                       // 처리기 A
  if (!(e.isComposing || e.keyCode === 229) && e.key === 'Enter') 보내기B(칸.value); // 처리기 B
});
폼.addEventListener('submit', e => { e.preventDefault(); 제출++; });
// ① 조합 없이 a → Enter
// ② CDP 조합 흉내 '한' 중에 keyDown(key=Enter, 13) → 확정 → keyUp
// ③ CDP 조합 흉내 중에 keyDown(key=Process, 229)
// ④ 조합이 끝난 뒤 Enter
// 각각 keydown 이 보는 key/keyCode/isComposing · A · B 가 보낸 값 · submit 횟수는?
```

- 네 경우 각각 `keydown` 이 보는 값, A · B 가 보낸 값, `submit` 횟수는?
- ② 에서 `isComposing` 은 누가 정한 값인가? ③ 의 `"Process"`/229 는?

### 7. 조합 중 `input` 값을 믿으면 안 되는 이유 (왜)

- 검색창이 `input` 마다 요청을 보내면 한글에서 무엇이 가나?
- 그것을 막는 가드 두 줄을 적어라.

### 8. `change` 는 언제 오나 (왜)

- `input` 과 `change` 의 차이를 한 문장으로 말하라.
- HTML 이 정한 것과 이 판에서 관찰한 것을 가르면?

### 9. CDP 흉내가 못 보는 것 (경계)

- CDP 의 조합 호출이 내는 이벤트 목록과 UI Events 3.6.5·3.6.6 의 표를 견주면 무엇이 다른가?
- 조합 중 `keydown` 의 `key`·`keyCode` 에 대해 이 편이 **적을 수 있는 것과 없는 것**은 무엇인가? 문항 6의 ②와 ③을 나란히 놓고 답하라.
- 실제 입력기의 순서를 재려면 무엇이 필요한가?

### 10. 옛 이벤트 둘 (경계)

- `keypress` 와 `textInput` 은 각각 어느 층(명세의 옛 이벤트 / 구현)인가?
- `keypress` 로 「입력이 있었나」를 잡으면 무엇을 놓치나?

### 11. 다른 주제와 잇기 (연결)

- [17번 주제](../17-stoppropagation-vs-preventdefault/1-question.md)의 「Enter 의 암묵 제출」은 문항 6의 어느 칸에서 다시 보였나? 어느 칸에서는 왜 안 보였나?
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **22번**(텍스트 계열 `<input>`)과 이 편은 무엇을 나눠 맡나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
