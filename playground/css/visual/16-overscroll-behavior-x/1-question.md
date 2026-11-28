# css/visual/16 — overscroll-behavior-x — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 기본값인 가로 상자를 끝까지 민 뒤 더 밀면 (예측)

```css
/* 질문용 발췌 */
.page { overflow-x: auto; }
.page .strip { width: 220px; overflow-x: auto; white-space: nowrap; }
```

- `.strip` 을 오른쪽 끝까지 스크롤한 뒤 같은 방향으로 계속 밀면, 그 움직임은 어디로 가는가?

### 2. 같은 상자에 `contain` 을 걸면 (예측)

```css
/* 질문용 발췌 */
.page { overflow-x: auto; }
.page .strip { width: 220px; overflow-x: auto; white-space: nowrap; overscroll-behavior-x: contain; }
```

- 1번과 같은 조작을 하면 바깥 `.page` 는 어떻게 되는가?
- `.strip` 자신의 끝 효과(튕김)는 남는가?

### 3. `contain` 과 `none` 이 갈리는 지점 (경계)

- 두 값이 똑같이 막는 것과 하나만 막는 것은 각각 무엇인가?

### 4. 가로 캐러셀에 이 속성을 거는 까닭 (왜)

- 가로 캐러셀에서 체이닝을 끊으면 사용자에게 어떤 문제가 사라지는가?

### 5. 예제가 콘텐츠를 일부러 넓게 만드는 까닭 (연결)

- 예제가 `overflow-x: auto` · `white-space: nowrap` · 오른쪽 여백을 함께 두는 것은 `overscroll-behavior-x` 와 어떻게 이어지는가?

### 6. 부모에만 걸었을 때 안쪽 스크롤 상자 (경계)

- `.scroll-x` 에 `contain` 을 걸었을 때, 그 안에 든 또 다른 가로 스크롤 상자도 체이닝이 막히는가?

### 7. 세로로 끝까지 밀었을 때 (경계)

- `overscroll-behavior-x: none` 을 건 상자가 세로로도 스크롤된다면, 세로 끝에서 바깥으로 넘어가는 일도 막히는가?

### 8. 호버에서 값을 바꾸고 전환을 걸면 (예측)

```css
/* 질문용 발췌 */
.strip { overscroll-behavior-x: auto; transition: overscroll-behavior-x 1s; }
.strip:hover { overscroll-behavior-x: none; }
```

- 마우스를 올렸을 때 값은 1초에 걸쳐 바뀌는가, 한 번에 바뀌는가?

## 실습

### 실습 1. 바깥으로 새지 않는 가로 스크롤 상자 만들기

**만들 것** — 상자보다 긴 한 줄짜리 글을 가로로 스크롤해 보는 상자를 만든다.
스크롤이 끝에 닿은 뒤 더 밀어도 움직임이 바깥 페이지로 넘어가지 않게 한다.

**요구 조건**

1. `.scroll-x` 상자는 가로로 넘치는 콘텐츠가 있을 때 가로 스크롤바가 생기게 한다.
2. `.scroll-x` 안의 글은 줄바꿈 없이 한 줄로 이어지게 한다.
3. `.content` 는 인라인 블록으로 놓여 자기 너비대로 늘어나게 한다.
4. `.content` 오른쪽에 여백을 두어 가로 스크롤 길이를 확보한다(여백 값은 시작 코드에 있다).
5. `.scroll-x` 의 가로 스크롤이 끝에 닿은 뒤의 입력이 부모 · 페이지로 넘어가지 않게 하되, 상자 자신의 끝 효과는 남긴다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>overscroll-behavior-x 연습</title>
  <style>
    .scroll-x {
      /* TODO: 가로 스크롤 끝에서 바깥으로 넘어가지 않게 (끝 효과는 남김) */
      /* TODO: 가로로 넘치면 스크롤바가 생기게 */
      /* TODO: 줄바꿈하지 않게 */
      background: #ede9fe;
      padding: 16px;
      border-radius: 8px;
      width: 220px;
      margin: 30px auto;
      border: 2px solid #8b5cf6;
    }
    .content {
      /* TODO: 인라인 블록으로 놓아 자기 너비대로 늘어나게 */
      color: #6d28d9;
      font-size: 14px;
      font-weight: 500;
      padding-right: 200px;
    }
  </style>
</head>
<body>
  <div class="scroll-x">
    <div class="content">← 가로 스크롤 → 오버스크롤이 제한됩니다. 더 많은 콘텐츠가 이어집니다.</div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 상자 안 글이 한 줄로 이어지고 가로 스크롤이 되는지 본다.
터치패드나 터치 화면에서 상자를 가로 끝까지 민 뒤 계속 밀어, 페이지가 따라 움직이지 않는지 살핀다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
