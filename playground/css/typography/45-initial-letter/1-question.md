# css/typography/45 — initial-letter — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 첫 글자에 `initial-letter: 3` 을 주면 (예측)

```css
/* 질문용 발췌 */
.dropcap::first-letter { initial-letter: 3; font-weight: bold; }
.dropcap { font-size: 16px; line-height: 1.6; max-width: 320px; }
```

- 첫 글자는 본문 몇 줄 높이로 보이고, 본문 글줄은 그 둘레를 어떻게 흐르나?

### 2. 값을 숫자 둘로 바꾸면 (예측)

```css
/* 질문용 발췌 */
.dropcap::first-letter { initial-letter: 3 2; }
```

- 첫 글자의 크기와 본문 안으로 가라앉는 깊이는 각각 어떻게 되나?

### 3. 단락 자체에 적으면 (예측)

```css
/* 질문용 발췌 */
.dropcap { initial-letter: 3; font-size: 16px; line-height: 1.6; }
```

- 이 단락의 첫 글자는 드롭캡으로 보이나?

### 4. 첫 글자 크기를 `font-size` 로 정하지 않는 까닭 (왜)
- 드롭캡 크기를 픽셀이 아니라 줄 수로 적게 한 것은 무엇을 맞추려는 것인가?

### 5. 본문 `line-height` 를 키우면 드롭캡도 커지는 까닭 (왜)
- `initial-letter` 값은 그대로인데 왜 첫 글자 크기가 달라지나?

### 6. `transition` 으로 드롭캡을 부드럽게 키우기 (경계)
- `initial-letter` 를 `normal` 에서 `3` 으로 바꿀 때 `transition` 을 걸면 어떻게 바뀌나?

### 7. 지원하지 않는 브라우저에서 남는 것 (경계)
- 정답 코드 꼴의 규칙이 이 속성을 모르는 브라우저에 가면 첫 글자는 어떻게 보이나?

### 8. `::first-letter` 와 짝을 이루는 이유 (연결)
- `initial-letter` 가 일하려면 왜 `::first-letter` 라는 의사 요소가 먼저 필요한가?

## 실습

### 실습 1. 잡지 꼴 드롭캡 단락 만들기

**만들 것** — 영어 단락 하나의 첫 글자를 본문 3줄 높이의 굵은 강조색 드롭캡으로 만든다.

**요구 조건**
1. `dropcap` 클래스 단락의 첫 글자만 고르는 선택자로 규칙을 쓴다.
2. 그 첫 글자가 본문 3줄 높이를 차지하는 드롭캡이 되게 한다.
3. 같은 첫 글자 규칙에 시작 코드에 채워진 굵기 · 강조색 · 오른쪽 여백을 그대로 둔다.
4. 단락 본문의 글자 크기 · 줄 간격 · 폭 제한은 시작 코드의 값을 그대로 쓴다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>initial-letter 연습</title>
  <style>
    .dropcap /* TODO: 첫 글자만 고르는 의사 요소를 붙인다 */ {
      /* TODO: 첫 글자가 본문 3줄 높이를 차지하게 한다 */
      font-weight: bold;
      color: #3b82f6;
      margin-right: 4px;
    }

    .dropcap {
      font-size: 16px;
      line-height: 1.6;
      max-width: 320px;
    }
  </style>
</head>
<body>
  <p class="dropcap">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation.</p>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 첫 글자 L 만 굵고 파랗게, 본문 3줄 높이로 커져 본문 첫 3줄이 그 오른쪽으로 비켜 흐르는지 본다. 이 속성을 지원하지 않는 브라우저라면 L 이 굵고 파랗기만 하고 크기는 그대로다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
