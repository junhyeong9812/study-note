# css/responsive/10 — Responsive Grid Layout — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 400px 컨테이너에 `auto-fill` 과 아이템 셋 (예측)

```css
/* 질문용 발췌 — 컨테이너 안쪽 너비는 400px 라고 가정한다 */
.grid { display: grid; gap: 8px;
        grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); }
/* 아이템: 1, 2, 3 */
```

- 열은 몇 개 생기고, 아이템 하나의 너비는 몇 px 인가?

### 2. 같은 조건에서 `auto-fit` 으로 바꾸면 (예측)

```css
/* 질문용 발췌 — 컨테이너 안쪽 너비는 400px 라고 가정한다 */
.grid { display: grid; gap: 8px;
        grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); }
/* 아이템: 1, 2, 3 */
```

- 아이템 하나의 너비는 몇 px 인가?

### 3. 아이템을 열 개로 늘리면 (예측)

- 1·2번과 같은 400px 컨테이너에 아이템이 10개라면, `auto-fill` 과 `auto-fit` 의 모습은 어떻게 다른가?

### 4. 미디어 쿼리 없이 열 개수가 바뀌는 까닭 (왜)

- `@media` 를 하나도 쓰지 않았는데 창을 좁히면 열이 줄어드는 이유는 무엇인가?

### 5. 반복 횟수를 셀 때 `1fr` 이 아닌 최소값을 쓰는 까닭 (왜)

- `minmax(80px, 1fr)` 에서 열 개수를 셀 때 왜 `80px` 쪽을 잣대로 삼는가?

### 6. 컨테이너가 최소값보다 좁아지면 (경계)

- 컨테이너가 60px 일 때 `minmax(80px, 1fr)` 과 `minmax(min(80px, 100%), 1fr)` 은 각각 어떻게 되는가?

### 7. 미디어 쿼리와 무엇을 기준으로 삼는가 (연결)

- 같은 화면에서 그리드를 좁은 사이드바 안에 넣으면, 미디어 쿼리 방식과 이 방식은 열 개수가 어떻게 달라지는가?

## 실습

### 실습 1. `auto-fill` 과 `auto-fit` 을 나란히 비교하는 데모

**만들 것** — 같은 아이템 세 개를 담은 그리드 두 개(`auto-fill` 하나, `auto-fit` 하나)와 반응형 그리드 예시 코드 상자를 세로로 쌓은 페이지를 만든다.

**요구 조건**

1. 데모 루트 `.rg-demo` 는 두 섹션과 코드 상자를 세로로 쌓고 그 사이를 띄운다.
2. 각 섹션(`.rg-section`)에는 라벨(`.rg-label`)과 그리드가 들어가고, 그리드마다 `1`·`2`·`3` 이라 적힌 아이템(`.rg-item`) 세 개를 둔다.
3. 그리드 공통 클래스 `.rg-grid` 는 그리드 컨테이너가 되고 칸 사이에 간격을 둔다.
4. 두 그리드 모두 열의 최소 너비는 80px, 최대는 남는 공간을 나눠 갖는 `1fr` 이다.
5. `.rg-grid.auto-fill` 은 들어가는 만큼 열을 만들고 빈 열을 남긴다.
6. `.rg-grid.auto-fit` 은 들어가는 만큼 열을 만들되 빈 열을 접어 아이템이 공간을 채우게 한다.
7. 코드 상자(`.rg-code`)는 미디어 쿼리 없는 반응형 그리드 예시 코드를 공백과 줄바꿈 그대로 보여 준다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Responsive Grid Layout</title>
<style>
  .rg-demo {
    font-family: system-ui, sans-serif;
    /* TODO: 섹션들을 세로로 쌓고 사이를 14px 띄운다 */
  }
  .rg-section { background: #f1f5f9; border-radius: 8px; padding: 12px; }
  .rg-label { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 8px; }
  .rg-grid {
    /* TODO: 그리드 컨테이너로 만들고 칸 사이 간격(8px)을 둔다 */
  }
  .rg-grid.auto-fill {
    /* TODO: 빈 열을 남기는 반복 + 최소 80px · 최대 1fr */
  }
  .rg-grid.auto-fit {
    /* TODO: 빈 열을 접는 반복 + 최소 80px · 최대 1fr */
  }
  .rg-item { background: #3b82f6; color: white; padding: 16px; border-radius: 6px;
             text-align: center; font-weight: 700; font-size: 14px; }
  .rg-code { background: #1e293b; border-radius: 8px; padding: 14px; }
  .rg-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
</style>
</head>
<body>
<div class="rg-demo">
  <div class="rg-section">
    <div class="rg-label">auto-fill: 빈 트랙 유지</div>
    <div class="rg-grid auto-fill">
      <!-- TODO: 아이템 1, 2, 3 -->
    </div>
  </div>
  <div class="rg-section">
    <div class="rg-label">auto-fit: 빈 트랙 축소 → 아이템 확장</div>
    <div class="rg-grid auto-fit">
      <!-- TODO: 아이템 1, 2, 3 -->
    </div>
  </div>
  <div class="rg-code">
    <code>/* 미디어 쿼리 없이 반응형 그리드 */
.grid {
  display: grid;
  grid-template-columns:
    repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}</code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열고 창을 넓혔다 좁혔다 한다.
넓은 창에서 위 그리드는 오른쪽에 빈 공간이 남고 아래 그리드는 세 칸이 한 줄을 꽉 채우는지, 창을 좁히면 두 그리드 모두 열이 줄어 아이템이 다음 줄로 넘어가는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
