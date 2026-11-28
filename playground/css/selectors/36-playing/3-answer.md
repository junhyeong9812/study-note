# css/selectors/36 — :playing — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 처음엔 회색, 재생을 누르면 녹색

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
페이지를 연 직후에는 재생 전이라 `.player` 규칙만 걸려 회색(`#d1d5db`) 테두리다.
재생 버튼을 누르면 `.player:playing` 이 걸려 `border-color` 가 녹색(`#22c55e`)으로 덮어써진다.

**왜 그런가**
`:playing` 은 재생 중일 때만 걸리는 의사 클래스다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 회색으로 돌아가고, 되돌리는 코드는 필요 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
일시정지를 누르면 재생 중이 아니게 되어 `:playing` 이 풀리고, 테두리는 기본 규칙의 회색으로 돌아간다.

**왜 그런가**
의사 클래스는 상태가 사라지면 저절로 풀린다.
「되돌리기」를 따로 쓸 필요가 없다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 볼 수 없다 — 불러올 영상이 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`src=""` 라 불러올 미디어가 없으므로 재생이 시작되지 않고, `:playing` 도 걸리지 않는다.
테두리는 회색 그대로다.

**왜 그런가**
`:playing` 은 실제 재생 상태를 따른다.
재생될 것이 없으면 상태도 생기지 않는다.
근거: 2-summary 「어디서 틀리나 3」.

### 4. `transition` 에 `border-color` 만 적혀 있어서다

`transition: border-color 0.3s` 는 테두리 색에만 0.3초를 준다.
`box-shadow` 는 목록에 없으니 전이 없이 바로 켜진다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 5. 기본 규칙의 나머지 값이 그대로 적용되기 때문이다

`.player:playing` 에 걸린 요소는 `.player` 규칙에도 여전히 걸린다.
`:playing` 규칙은 자기가 적은 `border-color` 만 덮어쓰고, 두께 · 선 모양 · 둥근 모서리는 기본 규칙의 값이 남는다.
근거: 2-summary 「동작 방식 (1)」 그림 해설 ④ · 「문법 — 형태와 규칙」.

### 6. 걸리지 않는다

`div` 에는 「재생 중」이라는 상태가 없으므로 `div:playing` 은 걸릴 일이 없다.
재생 상태는 `<audio>` · `<video>` 의 것이다.
근거: 2-summary 「어디서 틀리나 2」 · 「문법 — 형태와 규칙」.

### 7. 화면의 재생 버튼이 없어 사용자가 직접 재생을 시작할 수 없다

`controls` 가 기본 재생 막대를 붙이는 속성이므로, 빼면 재생 버튼이 화면에 없다.
사용자가 재생할 수단이 없으니 `:playing` 을 눈으로 확인할 기회도 없다.
근거: 2-summary 「어디서 틀리나 4」 · 「동작 방식 (1)」의 `controls` 풀이.

### 8. 재생 · 멈춤 때마다 클래스를 붙였다 떼는 일을 하지 않아도 된다

두 의사 클래스가 브라우저의 재생 상태를 그대로 따르므로, 상태별 스타일을 CSS 규칙 두 벌로 나눠 두기만 하면 된다.
원본 팁도 둘을 함께 쓰면 플레이어 상태별 커스텀 UI 를 CSS 로 만들 수 있다고 한다.
근거: 2-summary 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 재생 중에만 녹색으로 빛나는 비디오 플레이어

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 재생 막대가 달린 `.player` 비디오 | `<video class="player" controls width="280">` |
| 2. `<source>` 와 대체 글 | `<source src="" type="video/mp4" />` · `Your browser does not support video.` |
| 3. 기본 상태의 둥근 모서리 · 회색 테두리 | `.player { border-radius: …; border: …; }` |
| 4. 테두리 색 0.3초 전이 | `.player { transition: border-color 0.3s; }` |
| 5. 재생 중일 때만 테두리 색 · 그림자 변경 | `.player:playing { border-color: …; box-shadow: …; }` |
| 6. 멈추면 저절로 기본 상태 | 별도 코드 없음 — `:playing` 이 풀리며 `.player` 규칙만 남는다 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/playing.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:playing - 재생 가능한 요소(audio, video)가 재생 중일 때 적용된다.</title>
<!--
  [선택자] :playing
  설명: 재생 가능한 요소(audio, video)가 재생 중일 때 적용된다.
  구문: selector:playing { }
  팁: :playing과 :paused를 사용하면 미디어 플레이어의 상태에 따라 커스텀 UI를 CSS로 만들 수 있다.
-->
<style>
  /* .player: class 속성에 player를 가진 요소 매칭 */
  .player {
    border-radius: 12px;         /* 12px 둥근 모서리 */
    border: 3px solid #d1d5db;   /* 3px 회색 테두리 */
    transition: border-color 0.3s; /* 테두리 색 0.3초 전이 */
  }
  /* .player:playing: .player가 재생 중인 상태 매칭 */
  .player:playing {
    border-color: #22c55e;       /* 재생 중 녹색 테두리 */
    box-shadow: 0 0 12px rgba(34,197,94,0.3); /* 녹색 후광 효과 */
  }
</style>
</head>
<body>
  <!-- 컨트롤이 있는 비디오 플레이어 -->
  <video class="player" controls width="280">
    <source src="" type="video/mp4" />
    Your browser does not support video.
  </video>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.player { border-radius: 12px; border: 3px solid #d1d5db; transition: border-color 0.3s; }
.player:playing { border-color: #22c55e; box-shadow: 0 0 12px rgba(34,197,94,0.3); }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 핵심은 선택자 한 줄, `.player:playing` 이다.
- `:playing` 규칙에는 바뀌는 속성만 두고, 나머지는 기본 규칙에 맡긴다.
- `controls` 가 없으면 사용자가 재생을 시작할 수 없다.
- 정답 코드의 `src` 는 비어 있어 그대로는 재생되지 않는다 — 녹색 상태를 보려면 실제 영상 경로가 필요하다.
- 후광까지 부드럽게 하려면 `transition` 에 `box-shadow` 도 넣어야 한다(정답 코드는 넣지 않았다).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
