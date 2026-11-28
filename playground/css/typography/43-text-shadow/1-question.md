# css/typography/43 — text-shadow — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 색을 뺀 그림자 (예측)

```css
/* 질문용 발췌 */
.title { color: navy; text-shadow: 3px 3px; }
```

- 그림자는 무슨 색이고, 글자에서 어느 방향에 놓이는가?
- 그림자 가장자리는 선명한가, 흐린가?

### 2. 세 색 그림자의 쌓임 (예측)

```css
/* 질문용 발췌 */
.multi { text-shadow: 1px 1px #ef4444, 2px 2px #3b82f6, 3px 3px #22c55e; }
```

- 세 그림자 가운데 글자에 가장 가까운 층(맨 위)에 그려지는 것은 무슨 색인가?

### 3. 부모에 건 그림자 (예측)

```html
<!-- 질문용 발췌 -->
<div style="text-shadow: 1px 1px gray;">
  <p>첫 문단</p>
  <p>둘째 문단 <span style="text-shadow: none;">끝</span></p>
</div>
```

- 「첫 문단」 · 「둘째 문단」 · 「끝」 가운데 그림자가 없는 글자는 무엇인가?

### 4. 네온이 빛나 보이는 까닭 (왜)

- 네온 예제는 오프셋이 0 인데 어째서 글자 둘레가 빛나 보이는가?

### 5. 같은 색을 세 번 겹치는 까닭 (왜)

- 네온 예제가 같은 색 그림자를 흐림만 10 · 20 · 40px 로 바꿔 세 번 겹치는 까닭은 무엇인가?

### 6. 오프셋 0 에 흐림을 뺀 그림자 (경계)

- `text-shadow: 0 0 red;` 는 화면에 무엇을 남기는가?

### 7. 그림자와 이웃 요소 (경계)

- 큰 흐림을 준 그림자는 레이아웃에서 자리를 차지하는가, 그렇지 않다면 어떤 문제가 생길 수 있는가?

### 8. 카드 전체에 그림자를 주고 싶을 때 (연결)

- 카드 박스 자체에 그림자를 주려면 `text-shadow` 대신 무엇을 써야 하고, 왜 그런가?

## 실습

### 실습 1. 네 가지 글자 그림자 견본 만들기

**만들 것** — 굵고 큰 글자 네 줄에 각각 기본 그림자 · 흐린 그림자 · 여러 겹 그림자 · 네온 발광을 입힌 견본 페이지를 만든다.

**요구 조건**

1. 1단계 — `.basic` 문단은 오른쪽 아래로 비낀, 흐림 없는 회색 그림자 한 장을 가진다.
2. 2단계 — `.blur` 문단은 같은 방향으로 비낀 그림자에 흐림 반경을 주고, 반투명 검정으로 칠한다.
3. 3단계 — `.multi` 문단은 서로 다른 색 그림자 세 장을 쉼표로 잇고, 오프셋을 한 단계씩 늘려 계단처럼 겹친다.
4. 4단계 — `.neon` 문단은 오프셋 0 인 같은 색 그림자 세 장을 흐림만 점점 크게 해서 겹친다.
5. 글자 크기 · 굵기 · 문단 간격 · 네온 글자색은 시작 코드에 채워 둔 값을 그대로 쓴다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>text-shadow 연습</title>
  <style>
    .basic {
      /* TODO: text-shadow — 가로 2px, 세로 2px, 흐림 없음, 색 #94a3b8 */
      font-size: 28px;
      font-weight: bold;
      margin-bottom: 8px;
    }
    .blur {
      /* TODO: text-shadow — 가로 2px, 세로 2px, 흐림 4px, 색 rgba(0,0,0,0.3) */
      font-size: 28px;
      font-weight: bold;
      margin-bottom: 8px;
    }
    .multi {
      /* TODO: text-shadow — 세 장: 1px #ef4444 / 2px #3b82f6 / 3px #22c55e (가로 · 세로 같은 값) */
      font-size: 28px;
      font-weight: bold;
      margin-bottom: 8px;
    }
    .neon {
      /* TODO: text-shadow — 오프셋 0, 색 #8b5cf6, 흐림 10px / 20px / 40px 세 장 */
      font-size: 28px;
      font-weight: bold;
      color: #c4b5fd;
    }
  </style>
</head>
<body>
  <p class="basic">Basic Shadow</p>
  <p class="blur">Blurred Shadow</p>
  <p class="multi">Multiple Shadows</p>
  <p class="neon">Neon Glow</p>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 네 줄의 그림자가 각각 선명한 회색 · 흐린 회색 · 세 색 계단 · 보라 빛무리로 보이는지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
