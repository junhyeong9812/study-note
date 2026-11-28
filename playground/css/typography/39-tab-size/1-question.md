# css/typography/39 — tab-size — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `tab-size: 4` 인 `<pre>` 에서 탭 두 개로 들여쓴 줄 (예측)

```html
<!-- 질문용 발췌 -->
<pre style="tab-size: 4">a
		b</pre>
```

- `b` 앞의 들여쓰기는 공백 몇 개 너비로 보이나?

### 2. 일반 `<div>` 에 건 `tab-size` (예측)

```html
<!-- 질문용 발췌 -->
<div style="tab-size: 8">x	y</div>
```

- `x` 와 `y` 사이(사이에 탭 문자 하나)는 화면에서 어떻게 보이나?

### 3. 글자 크기를 두 배로 키우면 (예측)

```css
/* 질문용 발췌 */
.p { tab-size: 4;    font-size: 14px; }  /* 나중에 28px 로 */
.q { tab-size: 56px; font-size: 14px; }  /* 나중에 28px 로 */
```

- 두 블록의 `font-size` 를 28px 로 바꾸면, 탭 폭이 바뀌는 쪽은 어느 쪽인가?

### 4. 코드 블록에 굳이 `tab-size` 를 주는 까닭 (왜)

- 탭으로 들여쓴 코드를 `<pre>` 에 넣을 때 `tab-size: 2` 나 `4` 를 따로 주는 까닭은 무엇인가?

### 5. 공백 4개로 들여쓴 줄 (경계)

- 들여쓰기가 탭이 아니라 공백 4개로 되어 있는 줄은 `tab-size` 를 8 에서 2 로 바꾸면 어떻게 되나?

### 6. `<pre>` 는 `white-space` 없이도 되는 까닭 (연결)

- 예제는 `<pre>` 에 `white-space` 를 쓰지 않았는데도 `tab-size` 가 먹는 까닭은 무엇인가?

### 7. `body` 에 건 `tab-size` (연결)

- `body { tab-size: 2; }` 만 쓰고 안쪽 `<pre>` 에는 아무 값도 주지 않으면, `<pre>` 의 탭 폭은 어떻게 정해지나?

## 실습

### 실습 1. 탭 크기 2 · 4 · 8 을 나란히 비교하기

**만들 것** — 같은 내용을 담은 코드 블록 셋을 위아래로 놓고, 블록마다 탭 폭을 달리해 들여쓰기 차이를 한눈에 비교한다.

**요구 조건**
1. `<pre>` 블록 세 개를 위에서부터 `.tab2` · `.tab4` · `.tab8` 클래스로 놓는다.
2. 각 블록의 첫 줄은 그 블록의 탭 크기를 적은 글(`tab-size: 2` 등)이고, 둘째 줄은 탭 하나로, 셋째 줄은 탭 두 개로 들여쓴다.
3. `.tab2` 블록에서는 탭이 공백 2개 너비로 그려진다.
4. `.tab4` 블록에서는 탭이 공백 4개 너비로 그려진다.
5. `.tab8` 블록에서는 탭이 공백 8개 너비(기본값과 같은 폭)로 그려진다.
6. 세 블록은 같은 어두운 코드 블록 모양을 쓴다(꾸밈 값은 시작 코드에 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>tab-size 실습</title>
  <style>
    .tab2 {
      /* TODO: 탭 = 공백 2개 너비 */
      background: #1e293b; color: #e2e8f0; padding: 12px;
      border-radius: 4px; margin-bottom: 8px; font-size: 14px;
    }
    .tab4 {
      /* TODO: 탭 = 공백 4개 너비 */
      background: #1e293b; color: #e2e8f0; padding: 12px;
      border-radius: 4px; margin-bottom: 8px; font-size: 14px;
    }
    .tab8 {
      /* TODO: 탭 = 공백 8개 너비 */
      background: #1e293b; color: #e2e8f0; padding: 12px;
      border-radius: 4px; font-size: 14px;
    }
  </style>
</head>
<body>
  <pre class="tab2">tab-size: 2
	indented line
		double indented</pre>
  <!-- TODO: .tab4 블록 — 첫 줄 글, 탭 하나 들여쓴 줄, 탭 두 개 들여쓴 줄 -->
  <!-- TODO: .tab8 블록 — 같은 꼴 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어, 아래 블록으로 갈수록 둘째 · 셋째 줄의 들여쓰기가 넓어지는지 본다. 편집기가 Tab 을 공백으로 바꿔 저장하지 않았는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
