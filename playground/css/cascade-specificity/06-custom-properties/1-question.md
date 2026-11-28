# css/cascade-specificity/06 — CSS Custom Properties (변수) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 다크 카드 안 버튼의 배경과 모서리 (예측)

```css
/* 질문용 발췌 */
:root { --primary: #3b82f6; --radius: 8px; }
.dark { --primary: #60a5fa; }
.card .btn { background: var(--primary); border-radius: var(--radius); }
/* HTML: <div class="card dark"> … <button class="btn">버튼</button> </div> */
```

- 이 버튼의 `background` 는 어느 선언의 `--primary` 값을 쓰는가?
- 이 버튼의 `border-radius` 는 어느 선언에서 온 값인가?

### 2. 정의된 곳 바깥에서 대체값이 있는 참조 (예측)

```css
/* 질문용 발췌 */
.warning { --accent: orange; }
.note { color: var(--accent, crimson); }
/* HTML: <div class="warning">…</div> <p class="note">메모</p>  ← 두 요소는 형제 */
```

- `.note` 문단의 글자색은 무엇이 되는가?

### 3. 변수는 있는데 값이 맞지 않을 때 (예측)

```css
/* 질문용 발췌 */
.box { --gap: red; }
.box { padding: 10px; padding: var(--gap, 20px); }
```

- `.box` 의 `padding` 은 10px · 20px · 그 밖의 값 중 어느 것이 되는가?

### 4. `:root` 에 정의한 변수가 어디서나 보이는 까닭 (왜)
- `:root` 에 한 번 정의한 변수를 문서 깊숙한 `span` 에서도 쓸 수 있는 까닭은 무엇인가?

### 5. 같은 (0,1,0) 인데 다크 카드에서 `.dark` 값이 이기는 까닭 (왜)
- `:root` 와 `.dark` 의 명시도가 같은데도 다크 카드가 `.dark` 의 `--bg` 를 쓰는 까닭은 무엇인가?

### 6. 안쪽 요소에서 덮어쓴 값이 미치는 범위 (경계)
- 두 번째 카드에 선언한 `.dark` 변수 값이 첫 번째 카드와 바깥 컨테이너에는 왜 닿지 않는가?

### 7. `inherits: false` 로 등록한 변수와 `:root` (경계)
- `@property` 로 `inherits: false` 를 준 변수를 `:root` 에만 선언하면 자손 요소는 어떤 값을 보는가?

### 8. 버튼 하나로 테마 바꾸기 (연결)
- 클릭 한 번에 라이트/다크를 바꾸려면 JS 가 무엇을 건드리고, 왜 `.card` 규칙은 고치지 않아도 되는가?

## 실습

### 실습 1. 같은 HTML 로 라이트/다크 카드 나란히 세우기

**만들 것** — 구조가 똑같은 카드 두 장을 나란히 놓고, 변수 정의만 바꿔 하나는 라이트, 하나는 다크 테마로 보이게 한다.

**요구 조건**

1. 1단계 — `:root` 에 다섯 변수 `--bg` · `--text` · `--primary` · `--surface` · `--radius` 를 정의한다(값은 시작 코드의 주석에 있다).
2. 2단계 — `.dark` 에서 `--bg` · `--text` · `--primary` · `--surface` 네 변수만 다시 정의하고, `--radius` 는 다시 정의하지 않는다.
3. 3단계 — `.card` 의 배경 · 글자색 · 모서리 반경 · 테두리 색을 각각 `--bg` · `--text` · `--radius` · `--surface` 변수로 정한다.
4. 4단계 — `.card .btn` 의 배경은 `--primary`, 모서리 반경은 `--radius` 변수로 정한다.
5. 5단계 — 두 번째 카드에만 `dark` 클래스를 붙여, 두 카드의 HTML 구조는 같고 클래스 하나만 다르게 한다.
6. 두 카드는 컨테이너 안에 가로로 같은 너비로 놓인다(시작 코드에 이미 있다).

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>CSS Custom Properties 연습</title>
<style>
  :root {
    /* TODO: 다섯 변수 정의
       --bg #ffffff / --text #1e293b / --primary #3b82f6 / --surface #f1f5f9 / --radius 8px */
  }

  .dark {
    /* TODO: 네 변수만 다시 정의 (--radius 는 그대로 둔다)
       --bg #1e293b / --text #f1f5f9 / --primary #60a5fa / --surface #334155 */
  }

  .theme-demo {
    display: flex;
    gap: 16px;
    padding: 16px;
    background: #f8fafc;
    border-radius: 8px;
  }
  .card {
    flex: 1;
    padding: 20px;
    /* TODO: background · color · border-radius 를 변수로 */
    /* TODO: border 는 1px solid 에 색만 변수로 */
  }
  .card h3 { margin-bottom: 8px; font-size: 18px; }
  .card p { margin-bottom: 16px; font-size: 14px; opacity: 0.8; }
  .card .btn {
    color: white;
    border: none;
    padding: 8px 20px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    /* TODO: background · border-radius 를 변수로 */
  }
</style>
</head>
<body>
  <div class="theme-demo">
    <div class="card">
      <h3>라이트 테마</h3>
      <p>CSS 변수로 테마 전환</p>
      <button class="btn">버튼</button>
    </div>
    <div class="card"><!-- TODO: 이 카드를 다크 테마로 -->
      <h3>다크 테마</h3>
      <p>같은 HTML, 변수만 변경</p>
      <button class="btn">버튼</button>
    </div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 왼쪽 카드는 밝은 배경, 오른쪽 카드는 어두운 배경과 더 밝은 파란 버튼인지, 두 카드의 모서리 둥글기가 같은지 본다; 개발자 도구에서 `.card` 규칙이 한 줄도 다르지 않은지 확인한다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
