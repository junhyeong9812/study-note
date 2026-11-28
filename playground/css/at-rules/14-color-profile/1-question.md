# css/at-rules/14 — @color-profile — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 주석을 풀면 바뀌나 (예측)

```css
/* 질문용 발췌 */
@color-profile --display-p3 {
  src: url('https://example.com/Display-P3.icc');
}
.cp-demo { background: color(display-p3 0.2 0.5 1); }
```

- 이 `@color-profile` 규칙이 주석이 아니라 살아 있다면 `.cp-demo` 의 배경은 그 ICC 파일을 기준으로 칠해지나?

### 2. 색 공간 이름만 바꾸면 (예측)

```css
/* 질문용 발췌 */
.a { background: color(display-p3 0.2 0.5 1); }
.b { background: color(srgb 0.2 0.5 1); }
```

- `.a` 와 `.b` 의 배경은 같은 색인가?

### 3. 정의만 있는 스타일시트 (경계)

- `@color-profile --brand { src: url('brand.icc'); }` 만 있고 다른 선언이 없다면 화면의 무엇이 달라지나?

### 4. 내장 색 공간이 더 실용적인 까닭 (왜)

- ICC 파일을 불러오는 것보다 `color(display-p3 …)` 같은 내장 색 공간을 쓰는 편이 왜 더 실용적인가?

### 5. 정의한 이름이 `--` 로 시작하는 까닭 (왜)

- `@color-profile` 의 이름은 왜 `--` 로 시작해야 하나?

### 6. 쓸모가 있는 경우 (경계)

- 내장 색 공간으로 충분하지 않아 `@color-profile` 을 써야 하는 것은 어떤 경우인가?

### 7. `@font-face` 와 닮은 점 (연결)

- `@color-profile` 의 「정의하고 → 이름으로 불러 쓰는」 구조는 `@font-face` 와 어떻게 대응하나?

## 실습

### 실습 1. 넓은 색 영역의 파란 상자 만들기

**만들 것** — Display P3 색 공간의 색으로 칠한 상자 하나와, `@color-profile` 정의 형태를 보이는 주석을 담은 HTML 문서를 만든다.

**요구 조건**
1. `cp-demo` 클래스를 가진 `div` 하나에 `Wide Gamut Color` 글자를 넣는다.
2. 상자의 배경을 `color()` 함수로 내장 `display-p3` 색 공간의 채널 값 `0.2 0.5 1` 로 칠한다.
3. ICC 파일을 `src` 로 불러오는 `@color-profile --display-p3` 규칙을 쓰되, 개념 시연용이므로 주석으로 막아 둔다.
4. 글자는 흰색 굵은 글씨로 상자 안에 보인다(시작 코드에 채워져 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>@color-profile</title>
  <style>
    /* TODO: @color-profile --display-p3 규칙을 src 와 함께 쓰고, 통째로 주석 처리한다 */

    .cp-demo {
      padding: 20px;
      /* TODO: color() 함수로 display-p3 색 공간의 0.2 0.5 1 배경 */
      color: white;
      border-radius: 8px;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <!-- TODO: cp-demo 상자 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 파란 상자 안에 흰 굵은 글씨 `Wide Gamut Color` 가 보이는지, 개발자 도구에서 배경 값이 `color(display-p3 0.2 0.5 1)` 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
