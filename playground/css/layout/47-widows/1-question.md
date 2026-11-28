# css/layout/47 — widows — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 예제에서 `widows: 2` 한 줄을 지우면 (예측)

```css
/* 질문용 발췌 */
.multicol {
  column-count: 2;
  height: 100px;
  widows: 2;   /* 이 줄을 지운다 */
}
p { margin: 0; line-height: 1.6; }
```

- 이 줄을 지운 뒤 두 열에 나뉘는 줄의 배치는 지우기 전과 비교해 어떻게 되나?

### 2. 새 열 맨 위에 끝 한 줄만 넘어갈 상황 (예측)

- 문단을 공간대로 채우면 다음 열 맨 위에 끝 줄 하나만 넘어가게 될 때, `widows: 2` 인 브라우저는 무엇을 하나?

### 3. 컨테이너에 적었는데 문단에 효과가 닿는 이유 (왜)

- `widows` 를 `<p>` 가 아니라 `.multicol` 에 적었는데도 `<p>` 의 줄 나눔에 효과가 미치는 까닭은 무엇인가?

### 4. `widows: 0` 이나 `widows: -1` 을 적으면 (경계)

- 이 선언은 어떻게 처리되고, 그 결과 문단에 적용되는 `widows` 값은 무엇이 되나?

### 5. 다단도 인쇄도 아닌 보통 블록에 `widows: 5` (경계)

- 화면에 보통 블록으로 놓인 문단에 이 값을 주면 무엇이 달라지나?

### 6. `transition` 으로 `widows` 를 2에서 5로 (경계)

- `transition` 을 걸어 값을 바꾸면 3, 4 를 거쳐 서서히 바뀌나?

### 7. `orphans` 와의 관계 (연결)

- `widows` 와 `orphans` 는 분절 지점의 어느 쪽을 각각 지키나?

### 8. 3줄 문단에 `widows: 2` 와 `orphans: 2` (경계)

- 이 문단을 두 조건을 모두 지키면서 두 조각으로 나눌 수 있나, 없다면 어떤 결과가 나올 수 있나?

## 실습

### 실습 1. 2단 상자에서 새 열 상단 최소 줄 수 지정하기

**만들 것** — 한 문단을 두 열로 나누어 보여 주는 상자를 만들고, 새 열 맨 위에 문단 끝부분이 2줄 미만으로 남지 않도록 규칙을 건다.

**요구 조건**

1. `.multicol` 의 내용이 두 열로 나뉜다.
2. `.multicol` 의 높이를 고정해 열 높이를 묶는다(값은 100px).
3. 열이 나뉠 때 새 열 상단에 단락 끝부분이 2줄 미만으로 남지 않게 `.multicol` 에 규칙을 건다.
4. 단락(`p`)의 기본 바깥 여백을 없앤다.
5. 단락의 줄 높이를 글자 크기의 1.6배로 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>widows 연습</title>
<style>
  .multicol {
    /* TODO: 두 열로 나눈다 */
    /* TODO: 높이를 고정한다 */
    /* TODO: 새 열 상단 최소 줄 수 */
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  p {
    /* TODO: 기본 마진 제거 */
    /* TODO: 줄 높이 */
  }
</style>
</head>
<body>
<div class="multicol">
  <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco.</p>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 문단이 두 열로 나뉘는지 보고, `widows` 값을 3 · 4 로 바꿔 가며 오른쪽 열 맨 위의 줄 수와 왼쪽 열 아래의 빈 공간이 달라지는지 비교한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
