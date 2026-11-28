# css/units-values/04 — % — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 400px 부모 안 자식의 너비와 위쪽 여백 (예측)

```css
/* 질문용 발췌 */
.parent { width: 400px; height: 1000px; }
.child  { width: 25%; padding-top: 10%; }
```

- `.child` 의 콘텐츠 너비는 몇 px 인가?
- `.child` 의 `padding-top` 은 몇 px 인가?

### 2. 높이를 정하지 않은 부모 안의 `height: 100%` (예측)

```html
<!-- 질문용 발췌 -->
<div class="wrap">
  <div class="box">글자 한 줄</div>
</div>
<style>
  .wrap { width: 300px; }                 /* height 를 쓰지 않았다 */
  .box  { height: 100%; background: #3b82f6; }
</style>
```

- `.box` 의 높이는 무엇으로 정해지나?

### 3. `width: 100%` 에 `padding` 을 함께 준 자식 (예측)

```css
/* 질문용 발척 */
.parent    { width: 300px; padding: 12px; }
.child-100 { width: 100%; padding: 12px; }
```

- `.child-100` 의 테두리 바깥 너비는 몇 px 인가?
- `.child-100` 의 오른쪽 끝은 `.parent` 의 바깥 오른쪽 끝과 비교해 어디에 있나?

### 4. 위아래 여백의 `%` 가 부모 너비를 따르는 까닭 (왜)

- `padding-top` · `margin-bottom` 처럼 세로 방향 여백의 `%` 를 부모 높이가 아니라 부모 너비로 계산하는 까닭은 무엇인가?

### 5. `height: 100%` 가 먹히는 조건 (경계)

- `height: 100%` 가 실제로 부모를 채우려면 부모에 무엇이 있어야 하나?
- 부모의 높이마저 `%` 라면 어디까지 거슬러 올라가 확인해야 하나?

### 6. `font-size` 의 `%` 를 겹겹이 쓸 때 (경계)

- 부모가 `font-size: 20px` 이고 자식과 손자가 모두 `font-size: 150%` 라면 손자의 글자 크기는 몇 px 인가?

### 7. `%` 와 `px` 를 부모 크기 변화 앞에 세우면 (연결)

- 부모 너비가 300px 에서 600px 로 바뀔 때 `width: 50%` 인 자식과 `width: 150px` 인 자식은 각각 어떻게 달라지나?

## 실습

### 실습 1. 부모 너비의 50% · 75% · 100% 막대 쌓기

**만들 것** — 고정 너비 부모 안에 세 막대를 위에서 아래로 쌓고, 각 막대의 너비를 부모 너비에 대한 비율로 정한다.

**요구 조건**
1. 부모 하나 안에 자식 막대 세 개를 위에서 아래로 쌓는다.
2. 첫째 막대는 부모 콘텐츠 너비의 절반을 차지한다.
3. 둘째 막대는 부모 콘텐츠 너비의 4분의 3을 차지한다.
4. 셋째 막대는 부모 콘텐츠 너비를 전부 차지한다.
5. 세 막대의 너비는 모두 `%` 단위로만 쓴다.
6. 각 막대 안에는 자기 비율(`50%` · `75%` · `100%`)을 글자로 적는다.
7. 첫째와 둘째 막대 아래에는 다음 막대와의 간격을 둔다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>% 연습</title>
<style>
.parent {
  width: 300px;              /* 자식 % 의 기준 — 미리 채워 둠 */
  padding: 12px;
  background: #f1f5f9;
  border-radius: 8px;
}
.child-50 {
  /* TODO: 부모 너비의 절반 */
  padding: 12px;
  margin-bottom: 8px;
  background: #3b82f6;
  color: white;
  border-radius: 4px;
  text-align: center;
  font-weight: 600;
}
.child-75 {
  /* TODO: 부모 너비의 4분의 3 */
  padding: 12px;
  margin-bottom: 8px;
  background: #8b5cf6;
  color: white;
  border-radius: 4px;
  text-align: center;
  font-weight: 600;
}
.child-100 {
  /* TODO: 부모 너비 전부 */
  padding: 12px;
  background: #ef4444;
  color: white;
  border-radius: 4px;
  text-align: center;
  font-weight: 600;
}
</style>
</head>
<body>
<div class="parent">
  <!-- TODO: 세 막대를 차례로 넣고 각자 비율을 글자로 적는다 -->
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 세 막대의 길이가 절반 · 4분의 3 · 전부 순서로 늘어나는지 본다. 개발자 도구에서 `.parent` 의 `width` 를 바꿔 막대 길이가 비율대로 따라 바뀌는지도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
