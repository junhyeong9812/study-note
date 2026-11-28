# css/layout/46 — orphans — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 열 끝에 두 줄 자리만 남았을 때 (예측)

```css
/* 질문용 발췌 */
.cols { column-count: 2; height: 120px; orphans: 3; }
/* 열 1 에 앞 단락이 있고, 다음 단락(전체 5줄)이 시작될 때
   열 1 하단에 남은 자리는 딱 2줄이다 */
```

- 다음 단락의 줄은 열 1 과 열 2 에 몇 줄씩 놓이는가?

### 2. 같은 상황에서 값을 2 로 바꾸면 (예측)

- 1번 상황에서 `orphans: 3` 을 `orphans: 2` 로 바꾸면 단락의 줄은 열 1 과 열 2 에 몇 줄씩 놓이는가?

### 3. `orphans` 값을 바꾸는 전환 (예측)

```css
/* 질문용 발췌 */
.cols { orphans: 2; transition: orphans 1s; }
.cols:hover { orphans: 5; }
```

- 마우스를 올리면 값이 1초에 걸쳐 2 에서 5 로 차례로 바뀌는가?

### 4. 원본 팁이 인쇄 미리보기를 권하는 까닭 (왜)

- 일반 화면의 블록에 `orphans` 를 주어도 변화가 보이지 않는 까닭은 무엇인가?

### 5. 원본 예제의 고정 높이 (왜)

- 원본 예제가 `.multicol` 에 `height: 100px` 를 준 까닭은 무엇인가?

### 6. 0 과 길이 값 (경계)

- `orphans: 0` 과 `orphans: 3px` 는 각각 어떻게 처리되는가?

### 7. 값이 차이를 만들지 못하는 경우 (경계)

- 열 끝에 단락이 이미 4줄 이상 걸리는 배치에서 `orphans` 를 2 에서 3 으로 바꾸면 결과가 달라지는가?

### 8. 바깥 상자에 준 값이 단락에 닿는 길 (연결)

- 원본 예제는 `orphans: 3` 을 `p` 가 아니라 `.multicol` 에 주었는데, 단락의 줄에 이 값이 적용되는 까닭은 무엇인가?

## 실습

### 실습 1. 고아 줄을 막는 2단 상자

**만들 것** — 긴 단락 하나를 두 열로 흘리고, 열 끝에 단락 첫 부분이 3줄 미만으로 남지 않게 하는 상자를 만든다.

**요구 조건**
1. `.multicol` 안의 단락이 두 열로 나뉘어 흐른다.
2. 열 끝에서 단락이 잘릴 때 앞 열 하단에 남는 단락 줄이 3줄 미만이 되지 않게 한다.
3. 2번의 값은 `.multicol` 에 주고, 단락은 상속으로 그 값을 받는다.
4. 단락의 기본 바깥 여백을 없애 열 맨 위에서 바로 글이 시작되게 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>orphans 실습</title>
<style>
  .multicol {
    /* TODO: 두 열로 나눈다 */
    height: 100px;               /* 고정 높이로 분할 유발 */
    /* TODO: 열 끝에 단락 첫 부분이 3줄 미만 남지 않게 한다 */
    background: #f1f5f9;
    padding: 16px;
    border-radius: 4px;
  }
  p {
    /* TODO: 기본 바깥 여백을 없앤다 */
    line-height: 1.6;
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

**확인 방법** — 브라우저로 열어 글이 두 열로 흐르는지 본다. 단락 글을 늘리거나 `height` 를 바꿔 가며 열 1 하단에 단락 줄이 1~2줄만 남는 모양이 생기지 않는지 살핀다. 인쇄 미리보기로도 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
