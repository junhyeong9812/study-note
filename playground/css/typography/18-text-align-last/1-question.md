# css/typography/18 — text-align-last — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `justify` 만 준 문단의 마지막 줄 (예측)

```css
/* 질문용 발췌 */
.p { text-align: justify; max-width: 200px; }
/* 한국어 문단, 세 줄로 나뉜다고 하자 */
```

- 세 번째 줄은 상자 안 어디에 놓이나?

### 2. 문단 한가운데 `<br>` 이 있을 때 (예측)

```html
<!-- 질문용 발췌 -->
<p style="text-align: justify; text-align-last: right; max-width: 200px;">
  두 줄을 넘게 차지하는 긴 첫 부분…<br>두 줄을 넘게 차지하는 긴 둘째 부분…
</p>
```

- `<br>` 바로 앞 줄은 어떻게 놓이나?

### 3. 한 줄뿐인 문단에 두 정렬을 함께 주면 (예측)

```html
<!-- 질문용 발췌 -->
<p style="text-align: left; text-align-last: center; width: 400px;">짧은 글</p>
```

- 「짧은 글」은 왼쪽과 가운데 중 어디에 놓이나?

### 4. 예제가 폭을 좁혀 둔 까닭 (왜)

- 원본 예제가 `max-width` 로 문단 폭을 제한한 것은 왜인가?

### 5. `start` 와 `left` 가 다른 자리가 되는 때 (경계)

- `text-align-last: start` 와 `text-align-last: left` 가 서로 다른 쪽에 줄을 놓는 것은 어떤 글에서인가?

### 6. 마지막 줄에도 `justify` 를 줄 때 (경계)

- 마지막 줄이 몇 글자뿐인 문단에 `text-align-last: justify` 를 주면 어떤 모양이 될 수 있나?

### 7. 부모에 준 값과 자식 문단 (연결)

- `article` 에 `text-align-last: center` 를 주고 안쪽 `<p>` 에는 아무것도 주지 않으면 `<p>` 의 마지막 줄은 어떻게 되나?

### 8. `transition` 과 정렬 바꾸기 (연결)

- `:hover` 에서 `text-align-last` 를 `start` 에서 `center` 로 바꾸고 `transition` 을 걸면 마지막 줄은 어떻게 움직이나?

## 실습

### 실습 1. 양쪽 정렬 문단의 마지막 줄만 가운데 두기

**만들 것** — 여러 줄로 나뉘는 문단 하나를 만들고, 마지막이 아닌 줄은 양쪽 정렬, 마지막 줄만 가운데 정렬이 되게 한다.

**요구 조건**
1. 문서에 `text` 클래스를 단 `<p>` 하나가 있고, 그 안에 여러 줄로 나뉠 만큼 긴 글이 들어 있다.
2. 마지막이 아닌 줄은 양 끝이 상자 가장자리에 맞는다.
3. 마지막 줄만 가운데에 놓인다.
4. 문단의 폭이 제한되어 있어 글이 여러 줄로 나뉜다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-align-last 연습</title>
  <style>
    .text {
      /* TODO: 마지막 줄을 뺀 줄들을 양쪽 정렬 */
      /* TODO: 마지막 줄만 가운데 정렬 */
      font-size: 16px;
      max-width: 300px;
      background: #e2e8f0;
      padding: 12px;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <!-- TODO: text 클래스를 단 문단에 여러 줄이 될 긴 글을 넣는다 -->
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어, 위쪽 줄들의 오른쪽 끝이 상자 가장자리에 반듯이 맞는지, 마지막 줄만 가운데에 놓였는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
