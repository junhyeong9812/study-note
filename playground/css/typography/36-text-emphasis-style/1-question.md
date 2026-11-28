# css/typography/36 — text-emphasis-style — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 채움 키워드 없이 모양만 쓰면 (예측)

```css
/* 질문용 발췌 */
.a { text-emphasis-style: dot; }
.b { text-emphasis-style: filled dot; }
```

- `.a` 와 `.b` 의 글자에 붙는 마크는 서로 어떻게 다른가?

### 2. 두 글자짜리 문자열을 주면 (예측)

```css
/* 질문용 발췌 */
.star { text-emphasis-style: '★☆'; }
```

- `.star` 의 글자마다 붙는 마크는 무엇인가?

### 3. 부모 문단에만 지정했을 때 안쪽 `span` (예측)

```html
<!-- 질문용 발췌 -->
<p style="text-emphasis-style: open circle;">앞 글자 <span>안쪽 글자</span></p>
```

- 「안쪽 글자」에는 어떤 마크가 붙는가?

### 4. `transition` 을 걸어도 모양이 서서히 바뀌지 않는 까닭 (왜)

- `dot` 에서 `circle` 로 바꾸는 hover 효과에 `transition: all 1s` 를 줘도 즉시 바뀌는 까닭은 무엇인가?

### 5. 문자열과 `open` 을 함께 쓸 수 있나 (경계)

- `text-emphasis-style: open '★';` 는 어떻게 처리되는가?

### 6. 키워드 순서와 개수의 한계 (경계)

- `circle open` 처럼 순서를 바꾸거나 `filled open dot` 처럼 채움 키워드를 둘 쓰면 각각 어떻게 되는가?

### 7. 강조된 문단에서 한 낱말만 강조를 빼려면 (연결)

- 이 속성이 상속된다는 사실을 `color` 와 견주어 볼 때, 강조된 문단 안 한 낱말만 마크를 없애려면 어떻게 하는가?

### 8. 밑줄과 강조 마크의 쓰임 구분 (연결)

- `text-decoration` 의 밑줄 대신 `text-emphasis-style` 을 고를 만한 상황은 어떤 것인가?

## 실습

### 실습 1. 세 가지 강조 마크 단락 만들기

**만들 것** — 세 단락에 각각 채워진 점, 비어 있는 원, 별 문자 강조 마크를 붙인 페이지.

**요구 조건**
1. `.filled-dot` 단락의 글자마다 속이 채워진 점 마크가 붙는다.
2. `.open-circle` 단락의 글자마다 속이 빈 원 마크가 붙는다.
3. `.custom` 단락은 키워드가 아닌 문자열로 ★ 를 마크로 쓴다.
4. 각 단락의 글자 크기와 단락 간격은 시작 코드에 채워진 값을 그대로 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-emphasis-style 연습</title>
  <style>
    .filled-dot {
      /* TODO: 채워진 점 마크 */
      font-size: 20px;
      margin-bottom: 12px;
    }

    .open-circle {
      /* TODO: 비어 있는 원 마크 */
      font-size: 20px;
      margin-bottom: 12px;
    }

    .custom {
      /* TODO: 문자열로 ★ 마크 */
      font-size: 20px;
    }
  </style>
</head>
<body>
  <p class="filled-dot">Filled dot ●</p>
  <p class="open-circle">Open circle ○</p>
  <p class="custom">Custom ★</p>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 세 단락의 글자마다 각각 ●, ○, ★ 마크가 붙는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
