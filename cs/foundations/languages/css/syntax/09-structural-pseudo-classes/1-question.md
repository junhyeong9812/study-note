# css/syntax/09 — 구조적 의사 클래스: `:nth-child()`·`:nth-of-type()` 과 `of S` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — **어느 노드가 잡히는지**를 트리에 짚어 가며 답한다.
> 개수만 맞고 노드가 틀리면 틀린 것으로 센다.
> ★ **예측형이 7개로 §2-1 의 상한(6개)을 넘는다.** 이 주제의 독립 실패 모드가 「`An+B` 읽기 · 두 줄서기 · `of S` · 숨긴 형제 · `of` 의 비관대함 · `:empty` · 요소만 세기」로 갈려 있어 묶으면 복합 문항이 된다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

1\~6번은 **트리 T1**, 7\~8번은 **트리 T2** 위에서 답한다.

```html
<!-- T1 -->
<div class="box">
  <h2 id="H">제목</h2>
  <p id="p1">p1</p>
  <p id="p2" class="item">p2</p>
  <p id="p3">p3</p>
  <p id="p4" class="item">p4</p>
  <p id="p5">p5</p>
  <p id="p6" class="item">p6</p>
</div>

<!-- T2 -->
<div class="mix">
  <p    id="A" class="i">A</p>
  <span id="B" class="i">B</span>
  <p    id="C" class="i">C</p>
  <span id="D">D</span>
  <p    id="E" class="i">E</p>
</div>
```

### 1. `An+B` 를 펼칠 수 있는가 (예측)

```css
p:nth-child(2n)    { }
p:nth-child(2n+1)  { }
p:nth-child(-n+3)  { }
p:nth-child(n+3)   { }
p:nth-child(3n+1)  { }
```

- 다섯이 T1 에서 각각 어느 노드를 잡는가?
- `-n+3` 과 `n+3` 을 각각 한 마디로 뭐라고 읽는가?
- `:nth-child(0)` 은 문법 오류인가, 0개인가?
- `odd`·`even` 은 각각 무엇의 별칭인가?

### 2. `odd` 가 p1·p3·p5 가 아닌 이유 (왜)

- T1 에서 `p:nth-child(odd)` 는 어느 셋을 잡는가?
- 왜 눈으로 보이는 "홀수 번째 문단"과 어긋나는가?
- 「홀수 번째 문단」을 원했다면 무엇을 썼어야 하는가?
- 이 어긋남을 만든 노드는 트리의 어느 것인가?

### 3. `:nth-child` 와 `:nth-of-type` 이 갈리는 자리 (예측)

```css
p:nth-child(1)    { }
p:nth-child(2)    { }
p:nth-of-type(1)  { }
p:nth-of-type(2)  { }
p:first-child     { }
p:first-of-type   { }
```

- 여섯이 T1 에서 각각 무엇을 잡는가?
- `p:nth-child(1)` 이 0개인 이유를 한 문장으로 말할 수 있는가?
- 둘 중 마크업 변화에 덜 취약한 것은 어느 쪽이고 왜인가?
- 뒤에서 세는 짝(`:nth-last-child`·`:nth-last-of-type`)은 무엇을 잡는가?

### 4. "첫 `.item`" 을 고르는 선택자 (예측)

```css
.item:nth-of-type(1)     { }
.item:nth-of-type(2)     { }
.item:nth-child(3)       { }
:nth-child(1 of .item)   { }
```

- 넷이 T1 에서 각각 무엇을 잡는가?
- `.item:nth-of-type(1)` 이 **0개**인 이유는 무엇인가?
- `.item:nth-of-type(2)` 가 `p2` 를 맞히는 것이 왜 위험한가?
- 「첫 `.item`」이라는 뜻을 정확히 갖는 것은 넷 중 어느 것인가?

### 5. `of S` 는 무엇을 세는가 (예측)

```css
:nth-child(2n of .item)     { }
:nth-child(2n+1 of .item)   { }
:nth-last-child(1 of .item) { }
```

- 셋이 T1 에서 각각 무엇을 잡는가?
- `of S` 가 적용되는 순서 세 단계를 말할 수 있는가?
- `of` 뒤에 선택자를 **여러 개** 쓸 수 있는가?
- `of S` 를 붙일 수 있는 의사 클래스는 무엇과 무엇인가?

### 6. 숨긴 행이 번호를 차지하는가 (예측)

```html
<li>1행</li><li hidden>2행</li><li>3행</li>
<li>4행</li><li hidden>5행</li><li>6행</li>
```

- `li:nth-child(2n+1)` 은 여섯 중 어느 것을 잡는가?
- 화면에 **보이는** 줄만 보면 줄무늬가 어떻게 되는가?
- `li:nth-child(2n+1 of :not([hidden]))` 은 어느 것을 잡는가?
- 이 사고를 스크린샷만으로 원인까지 진단할 수 있는가?

### 7. `of S` 와 `:nth-of-type` 이 갈리는 자리 (예측)

```css
:nth-child(2 of .i)   { }
.i:nth-of-type(2)     { }
p:nth-child(2 of .i)  { }
```

- 셋이 T2 에서 각각 무엇을 잡는가?
- 앞의 둘이 서로 다른 노드를 잡는 이유는 무엇인가?
- `p:nth-child(2 of .i)` 가 0개인 것이 무엇을 증명하는가?
- T2 에서 `:nth-of-type(2)` 는 몇 개를 잡는가?

### 8. `:nth-of-type` 에 `of` 를 붙이면 (경계)

```css
p:nth-of-type(2n of .item)   { }
p:nth-child(2n of :unknownzz){ }
```

- 두 규칙은 `cssRules` 에 담기는가?
- `document.querySelectorAll('p:nth-of-type(2n of .item)')` 은 무엇을 돌려주는가?
- `of` 안의 목록이 "관대하다"는 것은 무슨 뜻이고, `of` 는 그런가?
- 관대한 것과 관대하지 않은 것의 정본은 어느 주제인가?

### 9. `:empty` 는 무엇을 잡는가 (경계)

```html
<p id="e1"></p>
<p id="e2"> </p>
<p id="e3"><!--c--></p>
<p id="e4">x</p>
```

- `p:empty` 는 넷 중 무엇을 잡는가?
- 주석과 공백은 각각 세는가?
- 소스를 예쁘게 들여쓰기하면 이 선택자에 무슨 일이 생기는가?
- `:empty` 를 "내용이 없어 보이는 것"으로 읽으면 어디서 틀리는가?

### 10. `:nth-child` 가 세는 것은 무엇인가 (경계)

```html
<div class="b1">텍스트만 있는 형제<p id="q1">q1</p><!--주석--><p id="q2">q2</p></div>
```

- `.b1 :nth-child(1)` 은 무엇을 잡는가?
- 앞에 텍스트 노드가 있는데 왜 `q1` 이 1번인가?
- `#q1:first-child` 는 맞는가?
- 이것은 브라우저 구현 사정인가 명세 보장인가?

### 11. 명시도는 어떻게 되는가 (연결)

- `p:nth-child(1)` 의 `(A, B, C)` 는 얼마인가?
- `p:nth-child(1 of .c1)` 은 얼마인가, `of` 가 무엇을 보태는가?
- 그 계산의 정본은 어느 주제인가?
- `:root` 가 `html` 보다 센 이유는 무엇인가?

### 12. 다른 주제와 잇기 (연결)

- "n 번째 자식을 가진 부모"를 고르려면 어느 문법이 필요한가?
- 번호로 거는 스타일이 마크업 변경에 약한 이유는 무엇인가?
- 「줄무늬가 두 줄 붙었다」를 보고 원인을 어디서 찾아야 하는가?
- flex 의 `order` 로 그림 순서를 바꾸면 `:nth-child` 번호도 바뀌는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
