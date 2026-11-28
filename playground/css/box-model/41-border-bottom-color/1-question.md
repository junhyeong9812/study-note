# css/box-model/41 — border-bottom-color — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 글자 색만 정하고 테두리 색은 비웠을 때 (예측)

```css
/* 질문용 발췌 */
.a { color: blue; border-bottom: 3px solid; }
```

- `.a` 의 아래쪽 테두리는 무슨 색으로 그려지나?

### 2. 색을 먼저, 단축 속성을 나중에 (예측)

```css
/* 질문용 발췌 */
.b { color: black; border-bottom-color: red; border-bottom: 4px solid; }
```

- `.b` 의 아래쪽 테두리는 무슨 색인가?

### 3. 색만 있고 다른 테두리 설정이 없을 때 (예측)

```css
/* 질문용 발췌 */
.c { border-bottom-color: red; padding: 16px; }
```

- `.c` 아래에 빨간 선이 보이나?

### 4. 기본값이 `currentcolor` 인 까닭 (왜)

- 기본값이 `currentcolor` 라서 `color` 만 바꾸면 무슨 이득이 생기나?

### 5. 원본 정답 코드가 색을 두 줄로 나눈 까닭 (왜)

- 원본 예제는 왜 `border-bottom: 4px solid;` 다음 줄에 `border-bottom-color` 를 따로 썼나?

### 6. 아래쪽 색 지정의 범위 (경계)

- `border-bottom-color` 를 바꾸면 위 · 왼 · 오른쪽 테두리 색도 영향을 받나?

### 7. 상속 안 되는 속성과 부모의 글자 색 (연결)

- `border-bottom-color` 는 상속되지 않는데, 부모의 `color` 를 바꾸면 자식의 아래쪽 테두리 색이 함께 바뀌는 것은 어떤 연결 때문인가?

### 8. 밑줄 색을 서서히 바꾸기 (연결)

- hover 때 아래쪽 테두리 색이 부드럽게 바뀌게 하려면 이 속성의 어떤 성질과 어떤 CSS 기능을 이어야 하나?

## 실습

### 실습 1. 아래쪽에만 빨간 선이 있는 상자 만들기

**만들 것** — 옅은 배경의 상자 하나에, 아래쪽 테두리만 두께 · 스타일은 단축 속성으로, 색은 `border-bottom-color` 로 따로 지정해 그린다.

**요구 조건**
1. 본문에 `box` 클래스를 가진 `div` 하나를 두고, 그 안의 글자는 `border-bottom-color` 다.
2. `.box` 에 단축 속성 `border-bottom` 으로 아래쪽 테두리의 두께와 실선 스타일만 준다 — 색은 단축 속성에 넣지 않는다(두께는 시작 코드 주석의 값).
3. 같은 규칙에서 단축 속성 **뒤** 줄에 `border-bottom-color` 로 아래쪽 테두리 색을 시작 코드 주석의 빨간색으로 지정한다.
4. 안쪽 여백과 배경색은 시작 코드에 채워 둔 대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>border-bottom-color - 요소의 아래쪽 테두리 색상을 설정</title>
<style>
  .box {
    /* TODO: 단축 속성으로 아래쪽 테두리 — 4px, 실선, 색은 쓰지 않는다 */
    /* TODO: 아래쪽 테두리 색만 따로 — #ef4444 */
    padding: 16px;
    background: #f8fafc;
  }
</style>
</head>
<body>
  <!-- TODO: box 클래스 div 하나, 글자는 border-bottom-color -->
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어, 상자 아래쪽에만 빨간 선이 있는지 본다. 두 TODO 줄의 차례를 바꿔서 선 색이 글자 색으로 돌아가는지도 확인해 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
