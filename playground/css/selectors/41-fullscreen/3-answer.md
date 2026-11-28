# css/selectors/41 — :fullscreen — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 배경은 더 어두워지고 모서리는 각지며 문구가 커진다 — 글자색은 그대로

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 배경: `#0f172a` (더 어두운 남색)
- 모서리: `border-radius: 0` → 각진 모서리
- 글자색: `white` 그대로
- 안내 문구: `32px`

(코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
전체 화면 중에는 `.fs-demo` 와 `.fs-demo:fullscreen` 이 모두 맞고, 부딪히는 `background` · `border-radius` 는 명시도가 높은 전체 화면 규칙이 이긴다.
`color` 는 전체 화면 규칙에 없으므로 평소 값 `white` 가 남는다.
`.fs-demo:fullscreen p` 는 전체 화면인 박스 안의 `p` 에 맞아 글자가 `32px` 이 된다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 2. 적용되지 않는다 — 전체 화면인 것은 `#a` 뿐이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`#b` 안의 `p` 는 평소 글자 크기 그대로다.

**왜 그런가**
`onclick` 안의 `this` 는 클릭된 요소이므로 `#a` 만 `requestFullscreen()` 을 부른다.
`:fullscreen` 은 클래스가 같다고 맞는 것이 아니라 「지금 전체 화면 중인가」를 요소마다 따로 본다.
`#b` 는 전체 화면이 아니므로 `.fs-demo:fullscreen p` 의 바깥 조건부터 거짓이다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「동작 방식 (4)」.

### 3. 명시도가 더 높기 때문이다

`.fs-demo:fullscreen` 은 클래스 하나 + 의사 클래스 하나이고, `.fs-demo` 는 클래스 하나다.
클래스와 의사 클래스는 같은 무게로 세므로 전체 화면 규칙의 점수가 더 높아 같은 속성 싸움에서 이긴다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 선택자는 상태를 읽기만 하고 만들지 못하기 때문이다

`:fullscreen` 은 「이미 전체 화면인 요소」를 고를 뿐이다.
요소를 전체 화면에 넣는 일은 JavaScript 의 Fullscreen API(`requestFullscreen()`)가 한다.
`onclick` 을 지우면 아무도 상태를 만들지 않으므로 규칙이 맞을 요소가 생기지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 저절로 원래 모양으로 돌아가며, 되돌리는 코드는 필요 없다

전체 화면이 끝나면 `:fullscreen` 이 더는 맞지 않아 그 규칙이 빠진다.
남은 `.fs-demo` 규칙만 적용되어 평소 배경 · 둥근 모서리 · 평소 글자 크기로 돌아온다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 6. 바꿀 수 없다 — `::backdrop` 을 쓴다

`.fs-demo:fullscreen` 은 요소 자신을 고르므로 그 `background` 는 요소의 배경이다.
요소 뒤에 깔리는 판은 따로 있는 의사 요소 `::backdrop` 으로 꾸민다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 2」.

### 7. `:fullscreen` 은 상태를, `::backdrop` 은 가상의 부분을 고르기 때문이다

의사 클래스는 요소의 상태로 요소를 고르고 콜론 하나로 쓴다 — `:fullscreen` 은 「전체 화면 중인 요소 자신」이다.
의사 요소는 HTML 에 없는 가상의 부분을 만들고 콜론 둘로 쓴다 — `::backdrop` 은 「요소 뒤의 배경 판」이다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (6)」 · 「어디서 틀리나 3」.

### 8. `:hover` 는 마우스 위치가, `:fullscreen` 은 Fullscreen API 호출이 상태를 만든다

둘 다 의사 클래스라 상태가 참인 동안만 맞고 끝나면 빠진다는 점은 같다.
`:hover` 의 상태는 마우스가 올라가 있는 것만으로 생긴다.
`:fullscreen` 의 상태는 `requestFullscreen()` 같은 JavaScript 호출이 있어야 생긴다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 클릭하면 전체 화면으로 커지는 안내 박스

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 클릭하면 그 박스가 전체 화면이 된다 | `<div class="fs-demo" onclick="this.requestFullscreen()">` |
| 2. 전체 화면일 때만 배경 · 모서리가 바뀐다 | `.fs-demo:fullscreen { background: …; border-radius: 0; }` |
| 3. 전체 화면일 때만 문구가 커진다 | `.fs-demo:fullscreen p { font-size: …; }` |
| 4. 평소에는 원래 모양 | `.fs-demo { … }` 만 적용 — `:fullscreen` 규칙은 상태가 끝나면 빠짐 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/fullscreen.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:fullscreen - 전체 화면 모드로 표시되고 있는 요소에 적용된다.</title>
<!--
  [선택자] :fullscreen
  설명: 전체 화면 모드로 표시되고 있는 요소에 적용된다.
  구문: selector:fullscreen { }
  팁: Fullscreen API와 함께 사용한다. ::backdrop으로 전체 화면 배경 스타일도 지정할 수 있다.
-->
<style>
  /* .fs-demo: class 속성에 fs-demo를 가진 요소 매칭 */
  .fs-demo {
    width: 200px;                /* 너비 200px */
    height: 120px;               /* 높이 120px */
    background: #1e293b;         /* 어두운 남색 배경 */
    color: white;                /* 흰색 텍스트 */
    display: flex;               /* 플렉스 컨테이너 */
    align-items: center;         /* 세로 가운데 정렬 */
    justify-content: center;     /* 가로 가운데 정렬 */
    border-radius: 12px;         /* 12px 둥근 모서리 */
    cursor: pointer;             /* 포인터 커서 */
  }
  /* .fs-demo:fullscreen: .fs-demo가 전체 화면 모드인 상태 매칭 */
  .fs-demo:fullscreen {
    background: #0f172a;         /* 전체 화면 시 더 어두운 배경 */
    border-radius: 0;            /* 둥근 모서리 제거 */
  }
  /* .fs-demo:fullscreen p: 전체 화면 상태인 .fs-demo의 자손 p 매칭 */
  .fs-demo:fullscreen p {
    font-size: 32px;             /* 전체 화면에서 텍스트 32px로 키움 */
  }
</style>
</head>
<body>
  <!-- 클릭으로 전체 화면 모드를 트리거하는 박스 -->
  <div class="fs-demo" onclick="this.requestFullscreen()">
    <!-- 안내 문구 -->
    <p>클릭하면 전체 화면</p>
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.fs-demo { width: 200px; height: 120px; background: #1e293b; color: white; display: flex; align-items: center; justify-content: center; border-radius: 12px; cursor: pointer; }
.fs-demo:fullscreen { background: #0f172a; border-radius: 0; }
.fs-demo:fullscreen p { font-size: 32px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 상태를 만드는 것은 `onclick` 의 `this.requestFullscreen()` 이고, CSS 는 그 상태를 `:fullscreen` 으로 읽는다.
- `this` 를 써서 클릭된 박스 자신을 전체 화면으로 띄운다.
- `.fs-demo:fullscreen` 은 명시도가 높아 평소 규칙의 `background` · `border-radius` 를 덮는다.
- `.fs-demo:fullscreen p` 는 자손 선택자로 상태 조건을 안쪽 `p` 까지 넓힌다.
- 되돌리는 코드가 없어도 전체 화면이 끝나면 평소 모양으로 돌아온다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
