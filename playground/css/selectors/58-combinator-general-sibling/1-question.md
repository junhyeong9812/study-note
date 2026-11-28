# css/selectors/58 — ~ 일반 형제 결합자 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 원본 예제에서 강조되는 요소 (예측)

```html
<!-- 질문용 발췌 -->
<div class="gen-demo">
  <h3>제목</h3>
  <span>중간 요소</span>
  <p>형제 단락 1</p>
  <p>형제 단락 2</p>
</div>
<style>.gen-demo h3 ~ p { background: #ede9fe; }</style>
```

- 네 요소 중 연보라 배경을 받는 것은 어느 것인가?

### 2. 제목보다 앞에 놓인 단락 (예측)

```html
<!-- 질문용 발췌 -->
<div>
  <p>단락 0</p>
  <h3>제목</h3>
  <p>단락 1</p>
</div>
<style>h3 ~ p { color: purple; }</style>
```

- `단락 0` 과 `단락 1` 의 글자색은 각각 어떻게 되는가?

### 3. 형제 상자 안에 들어 있는 단락 (예측)

```html
<!-- 질문용 발췌 -->
<div>
  <h3>제목</h3>
  <section>
    <p>안쪽 단락</p>
  </section>
  <p>바깥 단락</p>
</div>
<style>h3 ~ p { color: purple; }</style>
```

- 두 단락 중 보라색이 되는 것은 어느 것인가?

### 4. 체크박스가 패널보다 앞에 있어야 하는 까닭 (왜)

- `input:checked ~ .panel` 트릭에서 `input` 을 `.panel` 보다 뒤에 두면 왜 동작하지 않는가?

### 5. `h3 ~ p` 의 색이 `.gen-demo p` 를 이기는 까닭 (왜)

- 원본 예제의 두 규칙이 같은 `p` 에 걸릴 때 `.gen-demo h3 ~ p` 의 `color` 가 적용되는 까닭은 무엇인가?

### 6. 기준 요소와 다른 부모의 요소 (경계)

- `h3 ~ p` 에서 `h3` 자신과, 다른 `div` 안에 있는 `p` 는 각각 선택되는가?

### 7. `+` 로 바꾸면 (연결)

- 원본 예제의 `h3 ~ p` 를 `h3 + p` 로 바꾸면 결과가 어떻게 달라지고, 두 결합자는 어떤 관계인가?

### 8. 자손 결합자와의 차이 (연결)

- `.gen-demo p`(공백)와 `.gen-demo h3 ~ p` 는 각각 어떤 관계를 기준으로 요소를 고르는가?

## 실습

### 실습 1. 제목 뒤의 형제 단락만 강조하기

**만들 것** — 제목 · 중간 요소 · 단락 둘이 든 상자를 만들고, 제목 뒤에 오는 형제 단락만 강조 색으로 꾸민다.

**요구 조건**
1. `.gen-demo` 상자 안에 `h3`(제목) → `span`(중간 요소) → `p` → `p` 순서로 형제 요소를 둔다.
2. `h3` · `span` · `p` 의 기본 꾸밈 규칙은 시작 코드에 있는 그대로 둔다(`span` 은 블록으로 표시된다).
3. 일반 형제 결합자를 써서 `.gen-demo` 안에서 `h3` 뒤에 오는 모든 형제 `p` 를 고르는 선택자를 완성한다.
4. 그 선택자로 두 단락에만 강조 배경과 강조 글자색이 들어가게 한다 — `h3` 과 `span` 은 강조를 받지 않는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>~ 일반 형제 결합자</title>
<style>
  .gen-demo h3 {
    margin: 0 0 4px;
    color: #1f2937;
  }
  .gen-demo span {
    display: block;
    padding: 4px 8px;
    color: #6b7280;
  }
  .gen-demo p {
    margin: 4px 0;
    padding: 8px;
    border-radius: 4px;
  }
  /* TODO: .gen-demo 안에서 h3 뒤에 오는 모든 형제 p 를 고르는 선택자를 쓴다 */
  /* TODO_SELECTOR */ {
    background: #ede9fe;
    color: #5b21b6;
  }
</style>
</head>
<body>
  <div class="gen-demo">
    <h3>제목</h3>
    <span>중간 요소</span>
    <!-- TODO: 형제 단락 두 개를 넣는다 -->
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 두 단락에만 연보라 배경과 보라 글자가 들어가는지 본다. 단락 하나를 `h3` 위로 옮겨 그 단락의 강조가 사라지는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
