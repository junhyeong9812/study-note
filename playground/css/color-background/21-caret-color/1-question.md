# css/color-background/21 — caret-color — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 부모 form 에만 값을 준 경우 (예측)

```css
/* 질문용 발췌 */
.form { caret-color: #22c55e; }
/* <form class="form"><input type="text"><textarea></textarea></form> */
```

- 안쪽 `input` 과 `textarea` 를 클릭하면 캐럿은 무슨 색인가?

### 2. 글자 색만 정하고 캐럿 색은 그대로 둔 경우 (예측)

```css
/* 질문용 발췌 */
input { color: #3b82f6; }   /* caret-color 는 쓰지 않음 */
```

- 이 입력칸의 캐럿 색은 어디서 정해지나?

### 3. 투명 캐럿 입력칸에 글자 치기 (예측)

```css
/* 질문용 발췌 */
.secret { caret-color: transparent; }
```

- 이 입력칸을 클릭하고 글자를 치면 무엇이 보이고 무엇이 안 보이나?

### 4. `transparent` 를 조심해야 하는 이유 (왜)

- 캐럿을 투명하게 하면 왜 접근성 문제가 되나?

### 5. `caret-color` 가 애니메이션 가능한 이유 (왜)

- 이 속성의 값이 어떤 종류이기에 사이 값을 거쳐 바뀔 수 있나?

### 6. 어떤 요소에서 의미가 있나 (경계)

- 입력칸이 아닌 요소 가운데 `caret-color` 가 캐럿에 보이게 작동하는 것은 무엇이고, 평범한 `div` 에서는 왜 보이는 변화가 없나?

### 7. 마우스 포인터 색 (경계)

- 「커서 색상」을 바꾸려고 `caret-color` 를 줬는데 마우스 화살표가 그대로라면 무엇을 잘못 안 것인가?

### 8. `color` 와 `currentcolor` 와의 다리 (연결)

- `auto` 값이 `color` 속성과 어떻게 이어지며, 캐럿 색을 확실히 정하려면 왜 `auto` 에 기대면 안 되나?

## 실습

### 실습 1. 캐럿 색이 서로 다른 입력칸 세 개

**만들 것** — 같은 꾸밈의 입력칸 세 개(텍스트 input 둘 · textarea 하나)를 두고, 클릭했을 때 캐럿 색이 칸마다 다르게 깜빡이게 한다.

**요구 조건**
1. 텍스트 `input` 두 개와 `textarea` 하나를 위에서 아래로 차례로 둔다.
2. 첫째 `input` 을 클릭하면 캐럿이 빨강으로 깜빡인다.
3. 둘째 `input` 을 클릭하면 캐럿이 파랑으로 깜빡인다.
4. `textarea` 를 클릭하면 캐럿이 초록으로 깜빡인다.
5. 글자 색은 건드리지 않고 캐럿 색만 바꾼다 — 세 칸 모두 같은 테두리 · 여백 꾸밈을 쓰고, `textarea` 만 높이가 고정이다(꾸밈은 시작 코드에 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>caret-color 연습</title>
<style>
  .red-caret {
    /* TODO: 캐럿 색을 빨강(#ef4444)으로 */
    padding: 8px 12px;
    border: 2px solid #e2e8f0;
    border-radius: 6px;
    width: 100%;
    margin-bottom: 8px;
    font-size: 14px;
  }
  .blue-caret {
    /* TODO: 캐럿 색을 파랑(#3b82f6)으로 */
    padding: 8px 12px;
    border: 2px solid #e2e8f0;
    border-radius: 6px;
    width: 100%;
    margin-bottom: 8px;
    font-size: 14px;
  }
  .green-caret {
    /* TODO: 캐럿 색을 초록(#22c55e)으로 */
    padding: 8px 12px;
    border: 2px solid #e2e8f0;
    border-radius: 6px;
    width: 100%;
    height: 60px;
    font-size: 14px;
  }
</style>
</head>
<body>
  <!-- TODO: 빨간 캐럿 input (class="red-caret", placeholder="빨간 커서 (클릭해보세요)") -->
  <!-- TODO: 파란 캐럿 input (class="blue-caret", placeholder="파란 커서 (클릭해보세요)") -->
  <!-- TODO: 초록 캐럿 textarea (class="green-caret", placeholder="초록 커서 (클릭해보세요)") -->
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열고 세 칸을 하나씩 클릭해, 깜빡이는 캐럿이 빨강 · 파랑 · 초록인지, 친 글자 색은 바뀌지 않았는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
