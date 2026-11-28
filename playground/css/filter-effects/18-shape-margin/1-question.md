# css/filter-effects/18 — shape-margin — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `float` 를 지우면 (예측)

```css
/* 질문용 발췌 */
.shape {
  width: 80px; height: 80px;
  shape-outside: circle(50%);
  shape-margin: 16px;
  clip-path: circle(50%);
  background: #8b5cf6;
}
```

- 뒤따르는 문단의 글은 원 옆으로 흐르나, 아니면 어디에 놓이나?

### 2. `clip-path` 를 지우면 보이는 모양 (예측)

```css
/* 질문용 발췌 */
.shape {
  float: left; width: 80px; height: 80px;
  shape-outside: circle(50%);
  shape-margin: 16px;
  background: #8b5cf6;
}
```

- 보라색 박스는 눈에 어떤 모양으로 보이고, 글은 어떤 경계를 따라 흐르나?

### 3. 원 한가운데 높이에서 원과 글 사이의 틈 (예측)

```css
/* 질문용 발췌 */
.shape {
  float: left; width: 80px; height: 80px;
  shape-outside: circle(50%);
  shape-margin: 16px;
  margin-right: 8px;
}
```

- 원의 오른쪽 가장자리에서 글이 시작하는 곳까지는 대략 몇 px 인가?

### 4. `shape-outside` 와 `clip-path` 를 함께 쓰는 까닭 (왜)

- 원을 보이게 하고 글도 원을 따라 흐르게 하려면 왜 두 속성이 모두 필요한가?

### 5. 보통의 `margin` 대신 `shape-margin` 을 쓰는 까닭 (왜)

- 원 둘레에 고른 틈을 줄 때 왜 `margin` 만으로는 부족한가?

### 6. `shape-outside` 없이 `shape-margin` 만 준 float (경계)

- 이 경우 글과 박스 사이의 간격은 달라지나?

### 7. 마우스를 올리면 틈이 서서히 넓어지게 (연결)

- `transition` 과 `shape-margin` 으로 이 효과를 만들 수 있나, 그리고 부모에 `shape-margin` 을 줘서 자식 float 에 적용할 수 있나?

## 실습

### 실습 1. 원형 도형을 여유 있게 감싸 흐르는 문단 만들기

**만들 것** — 보라색 원 옆으로 글이 원의 곡선을 따라 흐르되, 원과 글 사이에 여유가 있는 문단을 만든다.

**요구 조건**
1. 컨테이너 안에 도형 블록과 문단을 차례로 둔다.
2. 도형 블록을 왼쪽에 띄워 문단 글이 그 오른쪽으로 흐르게 한다.
3. 글이 흐르는 경계를 박스 크기에 맞춘 원으로 만든다.
4. 글이 원에 바짝 붙지 않도록 원 경계를 바깥으로 16px 넓힌다.
5. 박스도 눈에 원으로 보이도록 잘라 낸다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <title>shape-margin 연습</title>
    <style>
      .wrap {
        max-width: 300px;
        margin: 20px auto;
        font-size: 14px;
        line-height: 1.6;
        color: #374151;
      }
      .shape {
        /* TODO: 왼쪽에 띄운다 */
        width: 80px;
        height: 80px;
        /* TODO: 글이 흐를 경계를 원으로 */
        /* TODO: 원 경계를 바깥으로 넓힌다 */
        /* TODO: 눈에도 원으로 보이게 자른다 */
        background: #8b5cf6;
        margin-right: 8px;
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <!-- TODO: 도형 블록 -->
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
    </div>
  </body>
</html>
```

**확인 방법** — 브라우저로 열어 보라색이 원으로 보이는지, 글줄의 왼쪽 끝이 원의 곡선을 따라 휘는지, 원과 글 사이에 틈이 있는지 본다. `shape-margin` 값을 `0` 으로 바꿔 틈이 줄어드는지도 비교한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
