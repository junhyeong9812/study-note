# css/at-rules/12 — @counter-style — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 기호 넷 · 항목 여섯에 `cyclic` (예측)

```css
/* 질문용 발췌 — 목록에는 <li> 가 6개 있다 */
@counter-style emoji-counter {
  system: cyclic;
  symbols: '🔴' '🟡' '🟢' '🔵';
  suffix: ' ';
}
ol { list-style-type: emoji-counter; }
```

- 다섯째 항목과 여섯째 항목의 마커는 각각 무엇인가?

### 2. 같은 목록에서 `system` 만 `fixed` 로 바꾸면 (예측)

```css
/* 질문용 발췌 — 목록에는 <li> 가 6개 있다 */
@counter-style emoji-counter {
  system: fixed;
  symbols: '🔴' '🟡' '🟢' '🔵';
  suffix: ' ';
}
ol { list-style-type: emoji-counter; }
```

- 다섯째 항목의 마커는 누가 만드는가?

### 3. `prefix` 와 `suffix` 를 함께 주면 (예측)

```css
/* 질문용 발췌 */
@counter-style boxed {
  system: cyclic;
  symbols: '🔴' '🟡';
  prefix: '[';
  suffix: '] ';
}
ol { list-style-type: boxed; }
```

- 첫째 항목 앞에 붙는 마커 문자열 전체는 무엇인가?

### 4. `@counter-style` 블록만 써 두면 목록이 그대로인 이유 (왜)

- 카운터 스타일을 정의만 하고 `list-style-type` 에 이름을 적지 않으면 왜 목록 모양이 바뀌지 않는가?

### 5. 원본 예제가 목록에 왼쪽 여백을 넉넉히 준 이유 (왜)

- 원본 예제가 `.custom-counter` 에 `padding-left` 를 준 까닭은 무엇인가?

### 6. 항목 수가 기호 수를 넘을 때 (경계)

- 항목이 몇 개가 될지 모르는 장식 목록에서 끝까지 직접 정한 기호만 나오게 하려면 `cyclic` 과 `fixed` 중 무엇을 골라야 하는가?
- 그렇게 골랐을 때 마커만 보고 몇 번째 항목인지 알 수 있는가?

### 7. 이모지 마커의 생김새 (경계)

- `symbols` 에 이모지를 적었을 때 그 이모지가 어떤 모양으로 보일지는 CSS 가 보장하는가?

### 8. `@counter-style` 과 `list-style-type` 의 관계 (연결)

- 두 가지는 각각 무엇을 맡고, 무엇으로 서로 이어지는가?

## 실습

### 실습 1. 이모지 네 개를 돌려 쓰는 목록 마커 만들기

**만들 것** — 네 항목짜리 번호 목록의 마커를 숫자 대신 이모지 네 개가 차례로 돌아가며 붙는 사용자 정의 카운터로 바꾼다.

**요구 조건**
1. `@counter-style` 로 `emoji-counter` 라는 이름의 카운터 스타일을 정의한다.
2. 이 카운터 스타일은 심볼을 순환 반복하는 알고리즘을 쓴다.
3. 심볼은 🔴 🟡 🟢 🔵 넷을 이 차례로 쓴다.
4. 마커 뒤에 공백 한 칸을 붙여 마커와 항목 글자를 떨어뜨린다.
5. `.custom-counter` 목록이 `emoji-counter` 를 마커 스타일로 쓰게 한다.
6. 목록의 네 항목은 차례로 빨강 · 노랑 · 초록 · 파랑 마커를 받는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>@counter-style 실습</title>
  <style>
    @counter-style emoji-counter {
      /* TODO: 심볼을 순환 반복하는 알고리즘 */
      /* TODO: 🔴 🟡 🟢 🔵 네 심볼 */
      /* TODO: 마커 뒤 공백 한 칸 */
    }

    .custom-counter {
      /* TODO: 위에서 정의한 카운터 스타일을 마커로 쓴다 */
      padding-left: 40px;
    }

    .custom-counter li {
      padding: 6px 0;
      font-size: 16px;
    }
  </style>
</head>
<body>
  <ol class="custom-counter">
    <li>첫 번째</li>
    <li>두 번째</li>
    <li>세 번째</li>
    <li>네 번째</li>
  </ol>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 네 항목 앞에 숫자 대신 🔴 🟡 🟢 🔵 가 차례로 붙고, 마커와 글자 사이에 간격이 있는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
