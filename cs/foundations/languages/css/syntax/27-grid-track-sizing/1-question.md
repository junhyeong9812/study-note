# css/syntax/27 — Grid 트랙 정의: `fr`·`minmax()`·`repeat()`·`auto-fill`/`auto-fit` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **`getComputedStyle(el).gridTemplateColumns` 가 무엇을 돌려줄지**를 맞힐 수 있는지 묻는다.
> 답은 **px 숫자까지** 적어 보라. 「대충 이쯤」은 이 주제에서 틀린 답이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `fr` 은 무엇을 나누는가 (예측)

```css
.g { display: grid; width: 500px;
     grid-template-columns: 200px 1fr 1fr; }
```

- `getComputedStyle(.g).gridTemplateColumns` 는 무엇을 돌려주는가?
- `200px` 을 `100px` 으로 바꾸면 그 값은 어떻게 되는가?
- `1fr 1fr` 을 `2fr 1fr` 로 바꾸면?
- `fr` 이 나누는 대상을 한 문장으로 말하면 무엇인가?

### 2. 계산값은 선언인가 결과인가 (예측)

```css
.g { display: grid; width: 700px; gap: 10px;
     grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
```

- `getComputedStyle(.g).gridTemplateColumns` 에 `repeat(...)` 이라는 글자가 나오는가?
- 트랙은 몇 개가 되고 각각 몇 px 인가?
- 그 개수를 손으로 세는 식은 무엇인가?
- 같은 선언에서 컨테이너 폭만 320px 로 줄이면 트랙 수는 몇이 되는가?

### 3. `1fr` 인데 왜 안 줄어드나 (예측)

```css
.g { display: grid; width: 300px; grid-template-columns: 1fr 1fr; }
/* 첫 항목의 내용: Supercalifragilisticexpialidocious */
```

- 두 트랙은 150px 씩으로 나뉘는가?
- 그렇지 않다면 `1fr` 의 **숨은 최솟값**은 무엇인가?
- 반반으로 만들려면 선언을 어떻게 고치는가?
- 선언을 안 고치고 **항목 쪽**을 고쳐서 같은 결과를 내는 방법은 무엇인가?
- 이 함정은 flex 의 어느 속성과 같은 모양인가?

### 4. `auto-fill` 과 `auto-fit` (예측)

```css
.fill { grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
.fit  { grid-template-columns: repeat(auto-fit,  minmax(120px, 1fr)); }
/* 둘 다 width: 700px; gap: 10px; 항목은 2개 */
```

- 두 컨테이너의 `gridTemplateColumns` 계산값은 각각 무엇인가?
- 둘이 만드는 **트랙 수**는 다른가?
- 접힌 트랙은 계산값에서 사라지는가?
- 항목을 5개로 늘리면 둘의 결과는 어떻게 되는가?

### 5. 무효한 트랙 정의를 어떻게 잡아내나 (경계)

- `repeat(auto-fill, 1fr)` 은 유효한가, 무효라면 그 사실을 화면에서 알 수 있는가?
- 「진단 3창」의 세 단계는 각각 무엇을 보는가?
- 대조군을 먼저 까는 기법은 그 셋 중 무엇을 대신해 주는가?
- `repeat(auto-fill, minmax(150px, auto))` 는 유효한가, `repeat(auto-fill, minmax(min-content, 1fr))` 은 어떤가?
- 이 둘을 가르는 기준을 한 문장으로 말하면 무엇인가?

### 6. 암묵 트랙 (예측)

```css
.g { display: grid; grid-template-columns: 100px 100px;
     grid-template-rows: 50px; }
/* 항목 4개 */
```

- `gridTemplateRows` 계산값은 무엇인가?
- 그 값에 내가 안 쓴 트랙이 들어 있는가?
- `grid-auto-rows: 80px` 을 더하면 그 값은 어떻게 바뀌는가?
- `grid-auto-rows: 80px 30px` 처럼 값을 둘 주면 암묵 행 셋은 각각 몇 px 인가?

### 7. `minmax()` 의 경계 (경계)

- `minmax(300px, 100px)` 처럼 최대가 최소보다 작으면 어느 쪽이 이기는가?
- `minmax(0, 1fr)` 과 `1fr` 이 결과가 같아지는 경우는 언제인가?
- `minmax(1fr, 2fr)` 은 유효한가, 왜 그런가?
- `fit-content(100px)` 은 내용이 작을 때와 클 때 각각 무엇이 되는가?

### 8. `gap` 은 어디에 끼어드나 (예측)

- `1fr 1fr` 에 `gap: 20px` 을 주면 600px 컨테이너에서 각 트랙은 몇 px 인가?
- `gap` 은 `gridTemplateColumns` 계산값에 나타나는가?
- 계산 순서에서 `gap` 은 고정 트랙보다 먼저 빠지는가 나중에 빠지는가?
- `auto-fit` 이 트랙을 접을 때 그 트랙에 붙어 있던 `gap` 은 어떻게 되는가?

### 9. 내재적 크기 키워드가 트랙 값으로 올 때 (경계)

- `min-content` 트랙과 `max-content` 트랙은 무엇이 다른가?
- `auto` 트랙은 그 둘 중 어느 쪽과 같은가, 아니면 다른가?
- 「내용만큼이되 상한을 두고 싶다」면 무엇을 쓰는가?
- 이 키워드들의 **정의 자체**는 목록의 몇 번 주제가 정본인가?

### 10. 왜 자동 반복에는 `fr` 을 못 쓰는가 (왜)

- `repeat(auto-fill, …)` 이 하는 일의 순서를 두 단계로 말하면 무엇인가?
- 그 첫 단계가 `fr`·`auto`·`min-content` 로는 왜 성립하지 않는가?
- `minmax(150px, auto)` 는 왜 성립하는가?
- 컨테이너 폭이 확정되지 않은 경우(`width: max-content`) 반복 횟수는 몇이 되는가?

### 11. 다른 주제와 잇기 (연결)

- 이 트랙들 **위에 항목을 놓는** 규칙은 목록의 몇 번 주제인가?
- `justify-self` 는 Grid 에 있고 flex 에는 없다 — 그 이유를 「자유 공간」이라는 말로 설명할 수 있는가?
- 카드 여럿의 **내부 줄**을 카드끼리 맞추려면 무엇이 필요한가?
- `gap` 의 정본은 몇 번 주제이고, 이 주제는 `gap` 의 무엇까지만 다루는가?

### 12. 계산값을 믿어도 되는가 (경계)

- 「`fr` 이 남은 공간을 나눈다」는 명세가 보장하는가, 구현이 그렇게 하는 것인가?
- 「계산값에 암묵 트랙이 섞여 온다」는 어느 쪽인가?
- 버전이 올랐을 때 다시 찍어야 하는 칸은 무엇인가?
- 본문의 `12.8906px` 같은 값에서 재현되는 것은 숫자인가 성질인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
