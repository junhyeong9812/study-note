# css/syntax/10 — 상태·폼 의사 클래스: `:hover`·`:focus-visible`·`:checked`·`:disabled` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**이고, 예측의 축이 하나 더 있다 — **어떤 입력을 넣었을 때**인가.
> 답할 때 「마우스로」·「Tab 으로」·「입력 후 빠져나온 뒤」를 **반드시 구분해서** 적는다.
> ★ **예측형이 7개로 §2-1 의 상한(6개)을 넘는다.** 「입력 방식」이라는 축이 하나 더 있어 같은 선택자도 조작마다 독립된 실패 모드가 된다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 포인터가 만드는 세 상태 (예측)

```html
<button id="btn">버튼</button>
```

- 마우스를 버튼 **위로 옮기기만** 했을 때 버튼이 맞는 선택자는 무엇인가?
- 마우스 버튼을 **누른 채** 있을 때는 무엇 무엇이 맞는가?
- **뗀 직후**에 목록에서 빠지는 것은 무엇인가?
- 이 셋을 스크린샷만으로 확인할 수 있는가, 없다면 무엇이 필요한가?

### 2. `:focus` 와 `:focus-visible` 이 갈리는 자리 (예측) ★

```html
<button id="btn">버튼</button>
<input id="txt" type="text">
```

- **Tab 키**로 버튼에 포커스했을 때 버튼이 맞는 것은 무엇 무엇인가?
- **마우스 클릭**으로 버튼에 포커스했을 때는 무엇이 맞고 무엇이 안 맞는가?
- **마우스 클릭**으로 텍스트 입력칸에 포커스했을 때는 어떤가, 버튼과 답이 같은가?
- 두 요소의 답이 갈리는 기준을 한 문장으로 말할 수 있는가?

### 3. 포커스 링을 지우는 코드 (왜)

```css
button:focus { outline: none; }
```

- 이 줄이 무엇을 망가뜨리는가?
- 마우스 클릭의 링만 없애려면 어떻게 써야 하는가?
- `:focus-visible` 이 언제 켜지는지를 **명세가 정하는가, UA 가 정하는가**?
- 그러면 이 문서의 실측은 무엇에 대한 근거인가?

### 4. `:focus-within` 은 누구에게 거는가 (경계)

```html
<div id="wrap"><input id="inner" type="text"></div>
```

- `#inner` 에 포커스가 갔을 때 `#wrap` 은 `:focus-within` 에 맞는가?
- `#wrap` 을 `:focus` 로 걸면 같은 효과가 나는가?
- `:focus-within` 과 `:has(:focus)` 는 무슨 관계인가?
- `:focus-within` 과 `:has(:focus-visible)` 은 무엇이 다른가?

### 5. 폼이 뜨자마자 무엇이 켜져 있는가 (예측)

```html
<input id="txt"  type="text"  required placeholder="이메일">
<input id="opt"  type="text"  value="ok">
<input id="dis"  type="text"  disabled value="x">
<input id="ro"   type="text"  readonly required value="v">
```

- 페이지가 뜬 직후(입력 0), 넷은 각각 어떤 의사 클래스에 맞는가?
- `#dis` 는 `:valid` 인가 `:invalid` 인가?
- `#ro` 는 어떤가, 그 이유는 무엇인가?
- `:placeholder-shown` 은 넷 중 어디에 맞는가?

### 6. `:invalid` 와 `:user-invalid` 의 시점 (예측) ★

```html
<input id="mail" type="email" required placeholder="이메일">
```

- 로드 직후 `#mail` 은 `:invalid` 인가, `:user-invalid` 인가?
- 클릭해서 `ab` 를 치고 **아직 그 칸에 있을 때**는 어떤가?
- **칸 밖으로 나온 뒤**에는 어떤가?
- 스크립트로 `element.value = 'zzz'` 만 넣으면 `:user-invalid` 가 켜지는가?

### 7. `[checked]` 와 `:checked` (예측)

```html
<input id="c1" type="checkbox" checked>
<input id="c2" type="checkbox">
```

- 사용자가 `c1` 을 **끄고** `c2` 를 **켠** 뒤, 넷(속성 둘 · 상태 둘)은 각각 어떻게 되는가?
- 왜 `[checked]` 는 그대로 남는가?
- `option[selected]` 와 `option:checked` 도 같은 관계인가?
- `:default` 는 무엇을 가리키는가?

### 8. `:disabled` 는 어디서 오는가 (경계)

```html
<fieldset id="fs" disabled>
  <input id="fi" type="text"><button id="fb">b</button>
</fieldset>
```

- `#fi` 와 `#fb` 는 `:disabled` 인가?
- 그 둘에 `disabled` 속성이 있는가?
- 그래서 `[disabled]` 와 `:disabled` 중 어느 쪽을 써야 하는가?
- `:disabled` 인 칸은 `form:invalid` 판정에 영향을 주는가?

### 9. `:read-only` 는 무엇을 잡는가 (경계)

- `<fieldset>`·라디오 버튼·`<option>` 은 `:read-only` 인가?
- `:read-only` 를 "readonly 속성이 있다"로 읽으면 어디서 틀리는가?
- `:read-write` 는 무엇에 맞는가?
- `:required` 는 `<div required>` 에 맞는가?

### 10. 링크 스타일이 안 먹는다 (예측) ★

```css
a:hover { color: red; }
a:link  { color: blue; }
```

- 이 링크에 마우스를 올리면 무슨 색인가?
- 두 선택자의 명시도는 각각 얼마인가?
- 승부를 정한 것은 캐스케이드의 몇 단계인가?
- 고치려면 무엇을 어떻게 바꾸는가, 그 순서의 이름은 무엇인가?

### 11. `:hover` 의 범위 (경계)

```html
<div id="par"><a id="a1" href="#">링크</a></div>
```

- `#a1` 위에 마우스가 있을 때 `#par` 은 `:hover` 인가?
- `body` 는 어떤가?
- 터치 기기에서 `:hover` 는 어떻게 되는가?
- 그래서 `:hover` 에만 담으면 안 되는 것은 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- 상태 의사 클래스는 명시도의 어느 자리에 들어가고, 그 정본은 어느 주제인가?
- `:hover` 와 `:nth-child` 는 같은 「의사 클래스」인데 무엇이 다른가?
- `:placeholder-shown` 과 `::placeholder` 는 무엇이 다른가?
- 「사용자가 아직 아무것도 안 했을 때 무엇이 켜져 있나」를 먼저 묻는 이유는 무엇인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
