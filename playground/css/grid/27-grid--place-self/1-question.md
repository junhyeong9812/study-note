# css/grid/27 — place-self — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 2열 그리드의 셋째 아이템에 `place-self: end` (예측)

```css
/* 질문용 발췌 */
.grid { display: grid; grid-template-columns: 1fr 1fr; grid-auto-rows: 100px; }
.item-3 { place-self: end; }
```

- 셋째 아이템은 몇째 행 · 몇째 열 셀에 있고, 그 셀 안의 어느 모서리에 놓이나?

### 2. 값 둘을 준 `place-self` (예측)

```css
/* 질문용 발췌 */
.badge { place-self: center end; }
```

- 이 아이템은 셀 안에서 세로로 어디, 가로로 어디에 놓이나?

### 3. 부모 규칙과 자기 값이 섞이면 (예측)

```css
/* 질문용 발췌 */
.grid { display: grid; place-items: center; }
.a { }
.b { place-self: start; }
```

- `.a` 와 `.b` 는 각자 셀 안의 어디에 놓이나?

### 4. `center` 아이템은 작아지고 `stretch` 아이템은 셀을 채우는 까닭 (왜)
- 두 값을 준 아이템의 크기가 왜 다르게 보이나?

### 5. 두 값의 순서가 「세로 가로」인 까닭 (왜)
- 왜 첫째 값이 세로, 둘째 값이 가로를 맡나?

### 6. `place-self` 로 할 수 없는 것 (경계)
- `place-self` 값을 바꿔서 아이템을 이웃 셀로 옮길 수 있나?

### 7. 「상속: 아니오」인데 `auto` 가 부모 값을 따르는 관계 (연결)
- `auto` 가 부모의 `place-items` 를 따르는 것은 CSS 상속과 무엇이 다른가?

## 실습

### 실습 1. 네 아이템을 각자 다르게 셀 안에 놓기

**만들 것** — 2열 그리드에 아이템 넷을 두고, 컨테이너 정렬은 건드리지 않은 채 아이템마다 다른 `place-self` 로 셀 안의 위치와 크기가 달라지게 만든다.

**요구 조건**
1. 컨테이너는 같은 너비의 2열 그리드이고 행 높이가 고정되어 있다(시작 코드에 준비됨) — 컨테이너에는 정렬 속성을 넣지 않는다.
2. 아이템 공통 스타일에는 너비 · 높이를 주지 않는다(시작 코드에 준비됨).
3. 1번 아이템은 자기 셀의 양 축 시작 쪽(좌상단)에 놓인다.
4. 2번 아이템은 자기 셀의 정중앙에 놓인다.
5. 3번 아이템은 자기 셀의 양 축 끝 쪽(우하단)에 놓인다.
6. 4번 아이템은 자기 셀 전체를 채운다.
7. 각 줄은 단축 속성 하나로 쓴다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>place-self 연습</title>
<style>
  .grid-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-auto-rows: 100px;
    gap: 8px;
    padding: 16px;
    background: #f1f5f9;
    border-radius: 8px;
  }
  .item {
    padding: 12px 16px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 13px;
    color: white;
  }
  .item-1 { background: #3b82f6; /* TODO: 좌상단 */ }
  .item-2 { background: #8b5cf6; /* TODO: 정중앙 */ }
  .item-3 { background: #ec4899; /* TODO: 우하단 */ }
  .item-4 { background: #f59e0b; /* TODO: 셀 전체 */ }
</style>
</head>
<body>
  <div class="grid-container">
    <div class="item item-1">1</div>
    <div class="item item-2">2 (place-self: center)</div>
    <div class="item item-3">3</div>
    <div class="item item-4">4</div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 1·2·3번 상자가 글자 크기만큼만 각각 좌상단 · 정중앙 · 우하단에 있고, 4번 상자만 셀을 꽉 채우는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
