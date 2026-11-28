# css/visual/17 — overscroll-behavior-y — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `contain` 상자를 끝까지 내린 뒤 더 굴리면 (예측)

```html
<!-- 질문용 발췌 -->
<div class="list" style="overscroll-behavior-y: contain; overflow-y: auto; height: 100px;">
  <p>1</p><p>2</p><p>3</p><p>4</p><p>5</p>
</div>
<div style="height: 2000px;">긴 페이지 내용</div>
```

- `.list` 를 맨 아래까지 내린 뒤 같은 자리에서 마우스 휠을 더 아래로 굴리면 바깥 페이지는 어떻게 되나?

### 2. 같은 상자에서 속성 줄만 지우면 (예측)

```html
<!-- 질문용 발췌 -->
<div class="list" style="overflow-y: auto; height: 100px;">
  <p>1</p><p>2</p><p>3</p><p>4</p><p>5</p>
</div>
<div style="height: 2000px;">긴 페이지 내용</div>
```

- 1번과 똑같이 `.list` 끝에서 휠을 더 굴리면 바깥 페이지는 어떻게 되나?

### 3. 높이 제한이 없는 상자 (예측)

```html
<!-- 질문용 발췌 -->
<div style="overscroll-behavior-y: contain; overflow-y: auto;">
  <p>1</p><p>2</p><p>3</p><p>4</p><p>5</p>
</div>
```

- 이 상자 위에서 휠을 굴리면 `contain` 이 막아 줄 「끝 너머의 스크롤」이 생기나?

### 4. `contain` 과 `none` 을 따로 둔 까닭 (왜)

- 둘 다 바깥으로 넘어가는 것을 막는데, 왜 값이 둘로 나뉘어 있나?

### 5. 정답 코드가 `overflow-y` 와 `height` 를 함께 쓰는 까닭 (왜)

- `overscroll-behavior-y: contain` 한 줄만으로 데모가 되지 않고 왜 두 줄이 더 필요한가?

### 6. 부모에 건 `contain` 과 안쪽 스크롤 상자 (경계)

- 바깥 `div` 에 `overscroll-behavior-y: contain` 을 걸었을 때, 그 안에 든 다른 세로 스크롤 상자의 체이닝도 끊기나?

### 7. 가로 캐러셀 끝에서 (경계)

- 가로로 스크롤되는 상자에 `overscroll-behavior-y: none` 을 걸면 가로 끝에서 바깥으로 넘어가는 것도 막히나?

### 8. 당겨서 새로고침과 이 속성의 다리 (연결)

- 모바일에서 페이지 맨 위를 아래로 당기는 움직임은 이 문서의 어떤 개념에 해당하며, 그래서 원본 팁은 어디에 어떤 값을 걸라고 하나?

## 실습

### 실습 1. 바깥 페이지로 새지 않는 세로 스크롤 상자 만들기

**만들 것** — 문단 셋이 든 작은 상자를 만들어 그 안에서만 세로 스크롤되게 하고, 상자 끝에 닿은 뒤의 세로 스크롤이 바깥 페이지로 넘어가지 않게 한다.

**요구 조건**
1. 클래스 `scroll-y` 인 `div` 하나 안에 문단(`p`) 셋을 넣는다 — 첫째는 영역 소개, 둘째는 「더 스크롤해도 바깥 페이지가 스크롤되지 않는다」는 안내, 셋째는 적용한 속성 이름과 값을 적는다.
2. `.scroll-y` 에 세로 스크롤바가 필요할 때만 나타나게 한다.
3. `.scroll-y` 에 내용보다 낮은 고정 높이를 주어 상자 안에 세로 스크롤이 생기게 한다.
4. `.scroll-y` 가 세로 끝에 닿은 뒤의 스크롤이 바깥 페이지로 전파되지 않게 하되, 체이닝만 막는 값을 쓴다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>overscroll-behavior-y 연습</title>
  <style>
    .scroll-y {
      /* TODO: 세로 끝에서 바깥 페이지로 스크롤이 넘어가지 않게 (체이닝만 막는 값) */
      /* TODO: 세로 스크롤바가 필요할 때만 나타나게 */
      /* TODO: 내용보다 낮은 고정 높이 */
      background: #fef3c7;
      padding: 16px;
      border-radius: 8px;
      width: 220px;
      margin: 30px auto;
      border: 2px solid #f59e0b;
      font-size: 13px;
      color: #92400e;
      line-height: 1.6;
    }
  </style>
</head>
<body>
  <div class="scroll-y">
    <!-- TODO: 문단 셋 (영역 소개 / 바깥이 안 움직인다는 안내 / 적용한 속성 표기) -->
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 노란 상자 안에서 세로 스크롤이 되는지 본다.
바깥 페이지로 새지 않는지 보려면 `body` 끝에 임시로 아주 긴 내용을 붙여 페이지도 스크롤되게 한 뒤, 상자를 끝까지 내리고 휠을 더 굴려 페이지가 그대로인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
