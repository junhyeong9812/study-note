# css/syntax/15 — 박스 모델과 `box-sizing` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **화면에서 몇 px 이 될지 맞힐 수 있는지**를 묻는다.
> ★ **답을 px 숫자로 적어라.** "넓어진다"는 답이 아니다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이 상자는 화면에서 몇 px 을 차지하는가 (예측)

```css
.a { width: 300px; padding: 20px; border: 5px solid #000; }
.b { box-sizing: border-box; width: 300px; padding: 20px; border: 5px solid #000; }
```

- `.a` 의 `getBoundingClientRect().width` 는 몇인가?
- `.b` 는 몇인가?
- `.b` 안에 글자가 실제로 놓이는 칸(content 폭)은 몇인가?
- 두 상자의 **높이**는 같은가 다른가?

### 2. 네 겹 중 어디까지 배경이 칠해지나 (경계)

- `content` · `padding` · `border` · `margin` 중 배경색이 칠해지는 칸은 어디까지인가?
- `getBoundingClientRect().width` 는 네 칸 중 어느 칸의 폭인가?
- `clientWidth` 는 어느 칸의 폭인가?
- 상자 둘 사이가 벌어져 보이는데 배경이 안 칠해져 있다면 그 빈 자리는 무엇인가?

### 3. `border-box` 인데 부모를 뚫고 나간다 (예측)

```css
.parent { width: 300px; }
.child  { box-sizing: border-box; width: 100%; padding: 10px; margin: 8px 20px; }
```

- `.child` 의 `rect.width` 는 몇인가?
- `.child` 의 오른쪽 끝은 `.parent` 의 오른쪽 끝보다 몇 px 밖에 있는가?
- `box-sizing: border-box` 가 이것을 막아 주지 못하는 이유는 무엇인가?
- 이 상황을 고치는 방법을 **두 가지** 대 보라.

### 4. `box-sizing` 을 바꿨는데 아무 일도 안 일어난다 (예측)

```css
.box { width: 320px; }
.box > div { padding: 20px; border: 5px solid #000; }   /* width 선언 없음 */
```

- 이 자식에 `box-sizing: border-box` 를 줬을 때와 안 줬을 때 `rect.width` 는 각각 몇인가?
- 그 이유를 `width: auto` 의 계산 방식으로 설명할 수 있는가?
- 그렇다면 `* { box-sizing: border-box }` 리셋은 **무엇을 건드리고 무엇을 안 건드리는가?**

### 5. 선언한 `width` 가 무시되는 경우 (경계)

```css
.small { box-sizing: border-box; width: 40px; padding: 20px; border: 5px solid #000; }
```

- 이 상자의 `rect.width` 는 몇인가?
- content 폭은 몇인가?
- 선언한 40px 은 어디로 갔는가 — 에러나 경고가 나오는가?

### 6. `min-width` 는 어느 칸을 재는가 (예측)

```css
.p { width: 100px; min-width: 200px; padding: 20px; border: 5px solid #000; }
/* 같은 선언에 box-sizing 만 content-box / border-box 로 갈라 본다 */
```

- `content-box` 일 때 `rect.width` 는 몇인가?
- `border-box` 일 때는 몇인가?
- 프로젝트 중간에 `border-box` 리셋을 새로 넣으면 기존 `max-width` 선언들에 무슨 일이 일어나는가?

### 7. 계산값 API 를 믿어도 되는가 (왜)

- `box-sizing: border-box; width: 300px; padding: 20px; border: 5px` 인 요소에서 `getComputedStyle(el).width` 는 무엇을 돌려주는가?
- 그 값은 실제 content 폭과 같은가?
- 치수를 확인할 때 어느 API 둘을 함께 읽는 것이 안전한가, 왜 그런가?

### 8. `%` 와 다른 주제로 잇기 (연결)

- `padding-top: 10%` 는 **무엇의** 10% 인가 — 부모의 높이인가 폭인가?
- `padding-top: 100%` 로 정사각형을 만들던 관용구는 오늘 무엇으로 대체되고, 그것은 목록의 몇 번 주제인가?
- `outline` 은 네 겹 중 어디에 속하는가?
- 이 상자가 **바깥에서 어떻게 보이고 안을 어떻게 배치하는지**는 목록의 몇 번 주제인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
