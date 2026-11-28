# css/cascade-specificity/07 — Custom Properties scope — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 카드 밖 뱃지의 배경 (예측)

```css
/* 질문용 발췌 */
.card-a  { --accent: #3b82f6; }
.badge   { background: var(--accent, #94a3b8); }
/* HTML: .scope-demo > .card-a > .badge  그리고  .scope-demo > .outside > .badge */
```

- `.outside` 안의 `.badge` 배경은 어떤 값이 되나?

### 2. `:root` 에 같은 이름을 하나 더 두면 (예측)

```css
/* 질문용 발췌 */
:root    { --accent: crimson; }
.card-a  { --accent: #3b82f6; }
.badge   { background: var(--accent, #94a3b8); }
```

- 이때 `.outside` 안의 `.badge` 배경은 무엇인가?
- `.card-a` 안의 `.badge` 배경은 무엇인가?

### 3. 카드 안에 카드를 넣으면 (예측)

```css
/* 질문용 발췌 */
.card-a { --accent: #3b82f6; }
.card-b { --accent: #8b5cf6; }
.bar    { background: var(--accent, #94a3b8); }
/* HTML: .card-a > .card-b > .bar  그리고  .card-a > .bar */
```

- `.card-b` 안의 `.bar` 는 어떤 색이 되나?
- `.card-a` 바로 아래의 `.bar` 는 어떤 색이 되나?

### 4. 규칙 하나가 자리마다 다른 색을 내는 까닭 (왜)

- `.badge` 규칙은 하나뿐인데 카드 A 와 카드 B 에서 색이 다른 까닭은 무엇인가?

### 5. `.badge` 에는 폴백을 달고 `.card-a h4` 에는 달지 않은 까닭 (왜)

- 원본에서 `.badge` · `.bar` 만 폴백을 단 까닭은 무엇인가?

### 6. 형제 컴포넌트의 변수 (경계)

- 카드 B 안의 요소가 카드 A 에 선언된 `--accent-light` 를 읽을 수 있나?

### 7. 「컴포넌트 안에서만 적용」은 어디까지 맞나 (경계)

- 원본 팁의 「해당 컴포넌트 내에서만 적용」이 지켜지지 않는 경우는 어떤 배치인가?

### 8. 변수 선언과 명시도 (연결)

- 한 카드 요소에 `.card-a { --accent: … }` 와 `.card-a.dark { --accent: … }` 가 함께 걸리면 어느 값이 그 카드와 자손에게 내려가나?

## 실습

### 실습 1. 같은 이름의 변수로 두 카드에 다른 강조색 입히기

**만들 것** — 같은 `--accent` 이름을 쓰지만 서로 다른 색을 갖는 두 카드와, 변수가 없는 바깥 영역의 뱃지를 만든다.
바깥 뱃지는 폴백 색으로 칠해져야 한다.

**요구 조건**
1. 문서 루트(`:root`)에 전역 변수 `--global-radius` 를 선언한다.
2. 두 카드와 `.outside` 의 모서리 반경이 `--global-radius` 를 읽게 한다.
3. `.card-a` 에 `--accent` · `--accent-light` 를 파랑 계열로 선언한다 (값은 시작 코드 주석에 있다).
4. `.card-b` 에 같은 이름 두 변수를 보라 계열로 선언한다.
5. 카드의 배경은 `--accent-light`, 테두리 색은 `--accent` 를 읽는다.
6. 카드 안 `h4` 의 글자색은 `--accent` 를 읽는다.
7. `.badge` 와 `.bar` 의 배경은 `--accent` 를 읽되, 없으면 회색 폴백을 쓴다.
8. `.outside` 에는 `--accent` 를 선언하지 않는다 — 그 안의 뱃지가 폴백 색이 되는지 확인한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Custom Properties scope</title>
<style>
  :root {
    /* TODO: 전역 변수 --global-radius (값 6px) */
  }

  .card-a {
    /* TODO: --accent (#3b82f6), --accent-light (#dbeafe) */
  }
  .card-b {
    /* TODO: --accent (#8b5cf6), --accent-light (#ede9fe) */
  }

  .scope-demo {
    display: flex;
    gap: 12px;
    padding: 16px;
    background: #f1f5f9;
    border-radius: 8px;
    flex-wrap: wrap;
  }
  .card-a, .card-b {
    flex: 1;
    min-width: 180px;
    padding: 16px;
    /* TODO: 배경은 --accent-light */
    /* TODO: 테두리 2px solid, 색은 --accent */
    /* TODO: 모서리는 --global-radius */
  }
  .card-a h4, .card-b h4 {
    /* TODO: 글자색은 --accent */
    font-size: 14px;
    margin-bottom: 12px;
  }
  .badge {
    display: inline-block;
    /* TODO: 배경은 --accent, 없으면 폴백 #94a3b8 */
    color: white;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
  }
  .bar {
    height: 6px;
    /* TODO: 배경은 --accent, 없으면 폴백 #94a3b8 */
    border-radius: 3px;
  }
  .outside {
    flex-basis: 100%;
    padding: 12px;
    background: white;
    /* TODO: 모서리는 --global-radius (--accent 는 선언하지 않는다) */
    border: 1px dashed #cbd5e1;
  }
</style>
</head>
<body>
  <div class="scope-demo">
    <div class="card-a">
      <h4>카드 A (--accent: 파랑)</h4>
      <div class="badge">Badge</div>
      <div class="bar"></div>
    </div>
    <div class="card-b">
      <h4>카드 B (--accent: 보라)</h4>
      <div class="badge">Badge</div>
      <div class="bar"></div>
    </div>
    <div class="outside">
      <div class="badge">밖의 Badge (폴백 적용)</div>
    </div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 카드 A 의 제목 · 뱃지 · 바 · 테두리는 파랑, 카드 B 는 보라, 아래 점선 상자 안의 뱃지는 회색인지 본다.
개발자 도구에서 `.outside` 를 골라 계산된 스타일에 `--accent` 가 없는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
