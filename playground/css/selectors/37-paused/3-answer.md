# css/selectors/37 — :paused — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 투명도 0.7 · 테두리 주황 — 0.3초에 걸쳐

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
멈추면 `opacity` 가 1 에서 0.7 로, `border-color` 가 `#d1d5db`(회색)에서 `#f59e0b`(주황)으로 바뀐다.
변화는 0.3초에 걸쳐 일어난다.

**왜 그런가**
멈춤 상태가 되면 `.player2:paused` 가 맞아 두 선언이 걸린다.
기본 규칙의 `transition: all 0.3s` 가 바뀌는 속성 전부를 0.3초 전이로 만든다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」.

### 2. 색은 `:paused` 규칙, 두께는 기본 규칙

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
테두리 색은 `#f59e0b`(상태 규칙), 두께 3px 와 선 모양은 기본 규칙에서 온다.

**왜 그런가**
멈춤 상태에서는 두 규칙이 모두 맞고, 클래스 + 의사 클래스인 `.player2:paused` 가 명시도가 더 높아 `border-color` 다툼에서 이긴다.
상태 규칙에 없는 두께와 선 모양은 다툼이 없으니 기본 규칙 값이 남는다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 멈출 때와 다시 재생할 때 모두 전이가 걸리게 하려고

기본 규칙은 상태와 상관없이 늘 맞으므로 전이 지시가 늘 걸려 있다.
`:paused` 에만 두면 다시 재생할 때 그 규칙이 풀리면서 전이도 사라져 원래 모습으로 툭 돌아간다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 4. 맞을 일이 없다

`div` 는 재생 · 일시정지 상태를 가지지 않으므로 `:paused` 가 맞는 경우가 없다.
`:paused` 는 `audio` · `video` 같은 재생 가능한 요소에 쓰는 것이다.
근거: 2-summary 「어디서 틀리나 1」 · 「문법 — 형태와 규칙」.

### 5. 멈춘 영상도 보이고 다시 조작할 수 있어야 하기 때문

투명도를 낮추면 「멈춤」을 알리면서도 영상과 컨트롤이 그대로 보인다.
숨기면 피드백이 아니라 다시 재생할 수단을 없애는 셈이다 (원본에 근거 없음 — 추론).
원본 팁도 피드백 예로 오버레이 표시와 투명도 낮추기를 든다.
근거: 2-summary 「어디서 틀리나 3」.

### 6. 둘 다 「지금의 상태」로 고르는 의사 클래스다

`:hover` 는 마우스가 올라가 있는 동안, `:paused` 는 재생이 멈춰 있는 동안 맞는다.
상태가 바뀌면 규칙이 걸렸다 풀렸다 한다는 점이 같다.
근거: 2-summary 「한눈에」의 용어 풀이 · 「동작 방식 (1)」.

### 7. 상태를 따라 클래스를 붙였다 떼는 JS 코드가 필요 없다

`:paused` 는 브라우저가 아는 재생 상태를 선택자가 바로 읽으므로, 멈춤 · 재생 사건을 듣고 클래스를 바꾸는 코드가 없어도 된다.
근거: 2-summary 「동작 방식 (1)」 · 「언제 쓰고 언제 안 쓰나」.

### 8. 달라질 색만 바꾸고 두께 · 선 모양은 물려받는다

`border-color` 만 적으면 두께와 선 모양은 기본 규칙 값이 그대로 남는다.
`border` 전체를 다시 적으면 그 세 값을 모두 상태 규칙에서 새로 정해야 하고, 빠뜨린 값은 기본 규칙 값이 아닌 기본값으로 돌아간다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

## 실습 정답

### 실습 1. 멈추면 흐려지고 테두리 색이 바뀌는 비디오 플레이어

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 컨트롤 달린 `video.player2` | `<video class="player2" controls width="280">` |
| 2. `source` 와 대체 문구 | `<source src="" type="video/mp4" />` · `Your browser does not support video.` |
| 3. 모든 속성 0.3초 전이 | `.player2 { transition: all 0.3s; }` |
| 4. 일시정지 상태 선택자 | `.player2:paused` |
| 5. 불투명도 0.7 | `.player2:paused { opacity: 0.7; }` |
| 6. 테두리 색만 바꾸기 | `.player2:paused { border-color: #f59e0b; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/paused.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:paused - 재생 가능한 요소(audio, video)가 일시정지 상태일 때 적용된다.</title>
<!--
  [선택자] :paused
  설명: 재생 가능한 요소(audio, video)가 일시정지 상태일 때 적용된다.
  구문: selector:paused { }
  팁: 일시정지 상태에서 오버레이를 표시하거나 투명도를 낮추는 등의 시각적 피드백을 줄 수 있다.
-->
<style>
  /* .player2: class 속성에 player2를 가진 요소 매칭 */
  .player2 {
    border-radius: 12px;         /* 12px 둥근 모서리 */
    border: 3px solid #d1d5db;   /* 3px 회색 테두리 */
    transition: all 0.3s;        /* 모든 속성 0.3초 전이 */
  }
  /* .player2:paused: .player2가 일시정지 상태일 때 매칭 */
  .player2:paused {
    opacity: 0.7;                /* 일시정지 시 70% 불투명 */
    border-color: #f59e0b;       /* 주황 테두리로 정지 표시 */
  }
</style>
</head>
<body>
  <!-- 컨트롤이 있는 비디오 플레이어 -->
  <video class="player2" controls width="280">
    <source src="" type="video/mp4" />
    Your browser does not support video.
  </video>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.player2 { border-radius: 12px; border: 3px solid #d1d5db; transition: all 0.3s; }
.player2:paused { opacity: 0.7; border-color: #f59e0b; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `:paused` 는 재생 가능한 요소의 일시정지 상태를 선택자로 바로 고른다.
- 전이는 기본 규칙에 두어 멈출 때와 다시 재생할 때 모두 부드럽게 한다.
- 상태 규칙은 명시도가 높아 겹치는 `border-color` 를 이긴다.
- 상태 규칙에는 달라질 부분(`opacity` · `border-color`)만 적는다.
- 피드백은 숨기기가 아니라 흐리게 하는 쪽이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
