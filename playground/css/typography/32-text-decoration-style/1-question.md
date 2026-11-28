# css/typography/32 — text-decoration-style — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 모양만 지정한 단락 (예측)

```css
/* 질문용 발췌 */
p { text-decoration-style: wavy; }
```

- 이 규칙만 있을 때 단락 글자 아래에는 무엇이 보이는가?

### 2. 모양을 먼저, 단축 속성을 나중에 (예측)

```css
/* 질문용 발췌 */
.note {
  text-decoration-style: dotted;
  text-decoration: underline;
}
```

- `.note` 의 밑줄은 어떤 모양인가?

### 3. 부모의 모양과 자식의 밑줄 (예측)

```css
/* 질문용 발췌 */
.parent { text-decoration-style: double; }
.parent .child { text-decoration: underline; }
```

- `.child` 의 밑줄은 어떤 모양인가?

### 4. `wavy` 가 맞춤법 오류 표시에 쓰이는 까닭 (왜)

- 오류 표시에 실선 밑줄보다 물결선이 어울리는 까닭은 무엇인가?

### 5. 실선에서 물결선으로 전환 효과 (경계)

- `transition` 을 걸고 마우스를 올릴 때 `solid` 를 `wavy` 로 바꾸면 모양이 서서히 변하는가?

### 6. 선 종류와 모양의 나눔 (연결)

- 「어디에 선을 긋나」와 「어떤 모양으로 긋나」는 각각 무엇이 정하고, `text-decoration` 단축 속성은 둘과 어떻게 이어지는가?

### 7. `dotted` 와 `dashed` 의 차이 (경계)

- 두 값이 그리는 선은 무엇으로 이루어져 있는가?

## 실습

### 실습 1. 다섯 가지 밑줄 모양 늘어놓기

**만들 것** — 다섯 단락에 각각 실선 · 이중선 · 점선 · 파선 · 물결선 밑줄을 긋는 페이지.

**요구 조건**
1. 단락 다섯 개에 `solid` · `double` · `dotted` · `dashed` · `wavy` 클래스를 하나씩 단다.
2. 각 클래스는 `text-decoration` 단축 속성 한 줄로 선 종류 `underline` 과 그 클래스 이름의 모양을 함께 정한다.
3. 각 단락의 글자는 자기 밑줄 모양의 이름(영어와 한국어)을 보여 준다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-decoration-style 연습</title>
  <style>
    .solid {
      /* TODO: 실선 밑줄 */
      font-size: 18px;
      margin-bottom: 4px;
    }
    .double {
      /* TODO: 이중선 밑줄 */
      font-size: 18px;
      margin-bottom: 4px;
    }
    .dotted {
      /* TODO: 점선 밑줄 */
      font-size: 18px;
      margin-bottom: 4px;
    }
    .dashed {
      /* TODO: 파선 밑줄 */
      font-size: 18px;
      margin-bottom: 4px;
    }
    .wavy {
      /* TODO: 물결선 밑줄 */
      font-size: 18px;
    }
  </style>
</head>
<body>
  <p class="solid">Solid 실선</p>
  <p class="double">Double 이중선</p>
  <p class="dotted">Dotted 점선</p>
  <p class="dashed">Dashed 파선</p>
  <p class="wavy">Wavy 물결선</p>
</body>
</html>
```

**확인 방법** — 브라우저로 파일을 열어 다섯 단락의 밑줄이 각자 이름과 같은 모양인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
