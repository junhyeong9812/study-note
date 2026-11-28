# css/cascade-specificity/01 — Specificity calculation — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 요소+클래스 대 클래스 둘 (예측)

```html
<!-- 질문용 발췌 -->
<p class="text highlight">안녕</p>
<style>
  .text.highlight { color: purple; }
  p.text { color: orange; }
</style>
```

- 두 규칙의 명시도는 각각 무엇이고, 글자는 어떤 색인가?

### 2. 클래스 열한 개와 ID 하나 (예측)

```html
<!-- 질문용 발췌 -->
<p id="x" class="a b c d e f g h i j k">안녕</p>
<style>
  #x { color: blue; }
  .a.b.c.d.e.f.g.h.i.j.k { color: green; }
</style>
```

- 클래스 규칙이 뒤에 있을 때 글자는 어떤 색인가?

### 3. 데모에 `#demo p` 로 색을 더하면 (예측)

```html
<!-- 질문용 발췌 -->
<div id="demo">
  <p class="text highlight" id="target">이 텍스트는 어떤 색일까?</p>
</div>
<style>
  #demo p { color: red; }
  #target { color: #3b82f6; }
</style>
```

- `#demo p` 가 `#target` 보다 앞에 있을 때 글자는 어떤 색인가?

### 4. 명시도를 덧셈으로 세면 안 되는 까닭 (왜)

- 명시도를 ID 100점 · 클래스 10점 · 요소 1점으로 더해 비교하면 왜 틀린 답이 나오나?

### 5. 데모의 `#demo p` 가 글자색 경쟁에 끼지 않는 까닭 (왜)

- `#demo p`(0,1,0,1)는 `#target`(0,1,0,0)보다 명시도가 높은데, 원래 데모에서 글자가 여전히 파랑인 것은 왜인가?

### 6. `:is()` 로 묶은 선택자의 점수 (경계)

- `:is(.a, #b) p` 가 `class="a"` 인 요소 안의 `p` 에 맞았을 때, 이 선택자의 명시도는 무엇인가?

### 7. 콜론 하나와 콜론 둘 (경계)

- `a:hover` 와 `p::before` 의 명시도는 각각 무엇이고, 둘의 칸 배치가 다른 까닭은 무엇인가?

### 8. 인라인 스타일과 메달 순위 (연결)

- `style="color: red"` 를 단 요소에 `#target` 규칙도 맞으면 어느 쪽이 이기고, 이 결과는 메달 순위 비유의 어느 칸과 이어지나?

## 실습

### 실습 1. 다섯 규칙이 겨루는 명시도 데모 만들기

**만들 것** — 한 문단에 다섯 가지 선택자가 모두 맞게 하고, 각각 다른 글자색을 주어 명시도가 가장 높은 규칙의 색이 쓰이는 것을 확인하는 페이지.

**요구 조건**
1. `id="demo"` 컨테이너 안의 문단에 클래스 `text` · `highlight` 와 id `target` 을 단다.
2. 요소 선택자 `p` 로 글자색을 정하는 규칙을 쓴다.
3. 클래스 선택자 `.text` 로 글자색을 정하는 규칙을 쓴다.
4. 요소+클래스 선택자 `p.text` 로 글자색을 정하는 규칙을 쓴다.
5. 클래스 둘을 이은 `.text.highlight` 로 글자색을 정하는 규칙을 쓴다.
6. ID 선택자 `#target` 으로 글자색을 정하는 규칙을 쓴다 — 이 규칙의 색이 최종 색이 되어야 한다.
7. 다섯 규칙은 시작 코드에 적힌 다섯 색을 하나씩 쓰고, 각 규칙 위 주석에 그 선택자의 명시도를 네 칸으로 적는다.
8. 본문 아래에 다섯 선택자의 명시도를 나란히 적은 비교 주석을 두고, 이긴 선택자를 표시한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Specificity calculation</title>
<style>
  /* 쓸 색 (약한 순서로): gray, green, orange, purple, #3b82f6 */

  /* TODO: 요소 선택자 — 명시도 ?,?,?,? */

  /* TODO: 클래스 선택자 — 명시도 ?,?,?,? */

  /* TODO: 요소 + 클래스 — 명시도 ?,?,?,? */

  /* TODO: 클래스 두 개 — 명시도 ?,?,?,? */

  /* TODO: ID 선택자 — 명시도 ?,?,?,? (최종 승자) */

  /* 꾸밈 — 그대로 둔다 (color 는 정하지 않는다) */
  #demo {
    padding: 20px;
    background: #f1f5f9;
    border-radius: 8px;
  }
  #demo p {
    font-size: 20px;
    font-weight: 700;
    text-align: center;
    padding: 16px;
    background: white;
    border-radius: 6px;
    border: 2px solid #e2e8f0;
  }
</style>
</head>
<body>
  <div id="demo">
    <!-- TODO: 클래스 두 개와 id 하나를 단다 -->
    <p>이 텍스트는 어떤 색일까?</p>
  </div>

  <!-- TODO: 명시도 비교 주석 (다섯 선택자 → 명시도, 승자 표시) -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 문장이 파란 글자인지 본다. `#target` 규칙을 지워 보며 다음 승자(보라)로 바뀌는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
