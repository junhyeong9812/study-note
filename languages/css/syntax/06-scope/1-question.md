# css/syntax/06 — `@scope`: 스코프 루트·하한과 근접성(proximity) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 새 판정 단계가 끼어드는 자리라 **색을 맞히는 것**이 인출이다.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 구역은 어디부터 어디까지인가 (예측)

```html
<div class="card">
  <p class="txt">1</p>
  <div class="content"><p class="txt">2</p></div>
</div>
<p class="txt">3</p>
<style>
  @scope (.card) to (.content) { .txt { color: #b91c1c; } }
</style>
```

- 세 문단의 색을 각각 예측하라.
- 하한 요소 `.content` **자신**에 스타일을 걸면 먹는가?
- 스코프 루트 `.card` 자신은 구역 안인가?
- `to (.content)` 를 지우면 무엇이 달라지는가?

### 2. 테마가 중첩되면 (예측)

```html
<div class="theme-light">
  <p class="prox">1</p>
  <div class="theme-dark"><p class="prox">2</p></div>
</div>
<style>
  @scope (.theme-light) { .prox { color: #15803d; } }
  @scope (.theme-dark)  { .prox { color: #1d4ed8; } }
</style>
```

- 두 문단의 색을 각각 예측하라.
- 둘째 문단이 두 규칙에 모두 매치되는데 한쪽이 이기는 기준은 무엇인가?
- 두 `@scope` 블록의 **순서를 바꾸면** 결과가 달라지는가?
- 이 기능이 없으면 같은 결과를 내려고 무엇을 손으로 써야 하는가?

### 3. 근접성 대 명시도 (예측)

```html
<div class="far"><div class="near"><p class="x" id="xid">X</p></div></div>
<style>
  @scope (.far)  { p#xid.x { color: #1d4ed8; } }
  @scope (.near) { .x      { color: #15803d; } }
</style>
```

- 이 문단은 무슨 색인가?
- 근접성과 명시도 중 어느 것이 먼저 판정되는가?
- 이 결과가 `@layer`(05번)와 결정적으로 다른 점은 무엇인가?
- 남의 시트를 덮는 문제를 `@scope` 로 풀 수 있는가?

### 4. 근접성 대 등장 순서 (예측)

```html
<div class="far2"><div class="near2"><p class="y">Y</p></div></div>
<style>
  @scope (.near2) { .y { color: #15803d; } }   /* 가깝다 · 먼저 썼다 */
  @scope (.far2)  { .y { color: #1d4ed8; } }   /* 멀다 · 나중에 썼다 */
</style>
```

- 이 문단은 무슨 색인가?
- 「나중에 쓴 쪽이 이긴다」로 설명하면 어떤 답이 나오고, 왜 틀리는가?
- 근접성이 **같을 때**는 무엇이 정하는가?
- 3번과 4번 두 판이 근접성의 자리를 어떻게 가두는가?

### 5. 스코프 루트 선택자의 명시도 (예측)

```html
<div id="big"><p class="q">Q</p></div>
<style>
  @scope (#big) { .q { color: #15803d; } }
  .q.q { color: #1d4ed8; }
</style>
```

- 이 문단은 무슨 색인가?
- `@scope (#big)` 의 `#big` 은 명시도 세 자리 중 어디에 기여하는가?
- 규칙 안에 `:scope` 를 쓰면 명시도가 얼마나 올라가는가?
- 스코프 **밖** 선언의 근접성은 어떻게 취급되는가?

### 6. 스코프 안에서 루트 자신을 가리키기 (경계)

```css
@scope (.card) { .card { outline: 3px solid red; } }
```

- 이 규칙은 어느 요소에 걸리는가? 바깥 `.card` 인가?
- 루트 자신을 노리려면 무엇을 써야 하는가? 둘을 들라.
- `@scope` 안의 `&` 는 무엇을 가리키는가?
- 규칙 안 선택자가 「상대 선택자」라는 말이 무슨 뜻인가?

### 7. 프렐류드 없는 `@scope` (경계)

```html
<div class="w">
  <p class="t">T</p>
  <style> @scope { .t { color: #b91c1c; } } </style>
</div>
<p class="t">T2</p>
```

- 두 문단의 색을 각각 예측하라.
- 프렐류드가 없을 때 스코프 루트는 무엇인가?
- 이 형태가 어떤 사용 패턴을 위해 있는가?
- 이 `<style>` 을 `<head>` 로 옮기면 무엇이 달라지는가?

### 8. 같은 컴포넌트가 중첩될 때 (예측)

```html
<div class="cardB"><p class="n">B1</p>
  <div class="cardB"><p class="n">B2</p></div>
</div>
<style>
  @scope (.cardB) to (.cardB) { .n { color: #15803d; } }
</style>
```

- 두 문단의 색을 각각 예측하라.
- 바깥 카드에서 출발한 구역은 어디에서 잘리는가?
- 그런데도 안쪽 글자가 칠해진다면 그 색은 **어느 구역**에서 온 것인가?
- 이 관용구가 실제로 막아 주는 사고는 무엇인가?

### 9. 오늘 이것을 써도 되는가 (경계)

- `@scope` 의 Baseline 상태는 무엇이고 언제 그렇게 됐는가?
- 지원하지 않는 브라우저에서 `@scope { … }` 블록은 어떻게 처리되는가?
- 지원 여부를 CSS 안에서 질의하려면 무엇을 쓰는가?
- 「무시됐을 때의 화면」을 같이 설계해야 하는 이유는 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- 캐스케이드 정렬에서 근접성이 들어가는 자리를 앞뒤 단계 이름과 함께 말하라.
- `@layer`·명시도·근접성·등장 순서 넷이 다 걸린 판은 어느 순서로 읽어야 하는가?
- `@scope` 는 그림자 DOM 과 같은 격리를 주는가?
- 스코프 밖이라 아무 선언도 안 걸린 요소의 값은 어디서 오는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
