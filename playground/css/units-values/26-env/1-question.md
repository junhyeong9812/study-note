# css/units-values/26 — env() — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. inset 이 0으로 정의된 화면에서 fallback 44px (예측)

```css
/* 질문용 발췌 — 브라우저가 safe-area-inset-top 을 0px 로 정의하고 있다고 하자 */
.top { padding-top: env(safe-area-inset-top, 44px); }
```

- `.top` 의 위쪽 안쪽 여백은 몇 px 인가?

### 2. `max()` 안에 넣은 `env()` 의 두 경우 (예측)

```css
/* 질문용 발췌 */
.side { padding-left: max(16px, env(safe-area-inset-left)); }
```

- `safe-area-inset-left` 가 0px 일 때 왼쪽 여백은 몇 px 인가?
- `safe-area-inset-left` 가 44px 일 때 왼쪽 여백은 몇 px 인가?

### 3. `env()` 에 `viewport-fit=cover` meta 태그가 짝으로 필요한 까닭 (왜)

- meta 태그 없이 `padding: env(safe-area-inset-top)` 만 쓰면 왜 노치 대응 효과가 없나?

### 4. 최소 여백을 fallback 대신 `max()` 로 지키는 까닭 (왜)

- 「여백이 최소 16px 은 되어야 한다」를 `env(safe-area-inset-left, 16px)` 로 표현하면 왜 부족한가?

### 5. `env()` 를 모르는 옛 브라우저와 fallback (경계)

- `env()` 를 해석하지 못하는 브라우저에서 `padding-top: env(safe-area-inset-top, 44px);` 의 fallback 은 쓰이나?
- 그런 브라우저에 대비하려면 선언을 어떻게 놓나?

### 6. `env()` 로 읽을 수 있는 이름의 범위 (경계)

- 작성자가 `--notch-gap` 을 만들어 두면 `env(--notch-gap)` 으로 읽을 수 있나?

### 7. `env()` 와 `var()` 의 다리 (연결)

- 두 함수는 「값을 누가 정의하나」에서 어떻게 다른가?

## 실습

### 실습 1. 안전 영역 패딩을 두른 어두운 카드

**만들 것** — 어두운 상자의 네 방향 안쪽 여백을 브라우저의 안전 영역 값으로 채우고, 그 안에 설명 글과 코드 예를 담은 콘텐츠 상자를 둔다.

**요구 조건**
1. `.env-demo` 안에 `.safe-area`, 그 안에 `.content` 가 있고, `.content` 에는 설명 단락과 `env()` 코드 예가 들어 있다.
2. `.safe-area` 의 위 · 아래 · 왼쪽 · 오른쪽 안쪽 여백을 방향별로 따로 선언하고, 각각 `env()` 로 같은 방향의 `safe-area-inset-*` 변수를 읽는다.
3. 네 `env()` 에 모두 fallback 을 준다 — 위 44px, 아래 34px, 왼쪽 · 오른쪽 16px.
4. 색 · 모서리 · 글자 크기 같은 꾸밈은 시작 코드에 있는 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>env() 연습</title>
<style>
.env-demo {
  padding: 16px;
  background: #f1f5f9;
  border-radius: 8px;
}

.safe-area {
  background: #1e293b;
  border-radius: 16px;
  overflow: hidden;
  /* TODO: 위쪽 안쪽 여백 — 위쪽 안전 영역 값, 없으면 44px */
  /* TODO: 아래쪽 안쪽 여백 — 아래쪽 안전 영역 값, 없으면 34px */
  /* TODO: 왼쪽 안쪽 여백 — 왼쪽 안전 영역 값, 없으면 16px */
  /* TODO: 오른쪽 안쪽 여백 — 오른쪽 안전 영역 값, 없으면 16px */
}

.content {
  background: #334155;
  border-radius: 8px;
  padding: 20px;
}

.content p {
  color: white;
  font-size: 14px;
  margin-bottom: 8px;
}

.content code {
  color: #67e8f9;
  font-size: 13px;
  background: #1e293b;
  padding: 4px 8px;
  border-radius: 4px;
}
</style>
</head>
<body>
<div class="env-demo">
  <div class="safe-area">
    <div class="content">
      <p>safe-area-inset을 활용한 레이아웃</p>
      <code>padding: env(safe-area-inset-top, 20px)</code>
    </div>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 어두운 상자 안에 콘텐츠 상자가 놓였는지 보고, 개발자 도구에서 `.safe-area` 의 네 padding 선언이 `env()` 로 적혀 있고 그 계산된 값이 무엇인지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
