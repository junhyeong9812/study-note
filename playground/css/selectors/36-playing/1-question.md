# css/selectors/36 — :playing — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 재생 버튼을 누르기 전과 누른 뒤의 테두리 (예측)

```css
/* 질문용 발췌 */
.player { border: 3px solid #d1d5db; }
.player:playing { border-color: #22c55e; }
```

- 영상이 정상으로 불러와진다고 할 때, 페이지를 연 직후와 재생 버튼을 누른 뒤 테두리 색은 각각 무엇인가?

### 2. 재생 중에 일시정지를 누르면 (예측)

- 1번의 플레이어가 재생 중일 때 일시정지를 누르면 테두리는 어떻게 되며, 그렇게 되돌리는 코드가 따로 필요한가?

### 3. 원본 예제를 그대로 열고 재생을 누르면 (예측)

```html
<!-- 질문용 발췌 -->
<video class="player" controls width="280">
  <source src="" type="video/mp4" />
  Your browser does not support video.
</video>
```

- 이 마크업에 `.player:playing` 규칙을 붙여 둔 채 재생 버튼을 누르면 녹색 테두리를 볼 수 있는가?

### 4. 테두리 색과 후광이 바뀌는 빠르기가 다른 까닭 (왜)

- 원본 예제에서 재생이 시작될 때 테두리 색은 서서히 바뀌고 후광은 바로 나타나는 까닭은 무엇인가?

### 5. `:playing` 규칙에 바뀌는 속성만 적어도 되는 까닭 (왜)

- `.player:playing` 규칙에 `border-color` 만 적었는데도 두께와 둥근 모서리가 유지되는 까닭은 무엇인가?

### 6. `div` 에 `:playing` 을 붙이면 (경계)

- `div:playing` 처럼 미디어가 아닌 요소에 붙인 규칙은 언제 걸리는가?

### 7. `controls` 를 뺀 비디오 (경계)

- `<video>` 에서 `controls` 를 빼면 사용자가 `:playing` 상태를 만들어 낼 수 있는가?

### 8. `:paused` 와 짝을 지으면 생기는 것 (연결)

- `:playing` 과 `:paused` 를 함께 쓰면 JS 로 클래스를 붙였다 떼는 방식에 비해 무엇을 덜 해도 되는가?

## 실습

### 실습 1. 재생 중에만 녹색으로 빛나는 비디오 플레이어

**만들 것** — 재생 막대가 달린 비디오 한 개를 두고, 재생 중일 때만 테두리가 녹색으로 바뀌고 후광이 생기게 한다.

**요구 조건**
1. `class="player"` 인 `<video>` 에 브라우저 기본 재생 막대를 붙인다.
2. 비디오 안에 `<source>` 하나와, 비디오를 지원하지 않는 브라우저에서 보일 대체 글을 둔다.
3. 기본 상태의 `.player` 는 둥근 모서리와 회색 테두리를 가진다(값은 시작 코드에 있다).
4. 테두리 색이 바뀔 때는 0.3초 동안 서서히 바뀌게 한다.
5. 재생 중인 `.player` 만 고르는 선택자로 규칙을 만들고, 그 규칙은 테두리 색과 그림자만 바꾼다(값은 시작 코드에 있다).
6. 일시정지하면 따로 코드 없이 기본 상태로 돌아가야 한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:playing 연습</title>
<style>
  .player {
    border-radius: 12px;
    border: 3px solid #d1d5db;
    /* TODO: 테두리 색만 0.3초 동안 서서히 바뀌게 한다 */
  }
  /* TODO: 아래 규칙의 선택자를 「재생 중인 .player」로 고친다 */
  .player {
    border-color: #22c55e;
    box-shadow: 0 0 12px rgba(34,197,94,0.3);
  }
</style>
</head>
<body>
  <!-- TODO: 재생 막대가 보이도록 속성을 하나 더한다 -->
  <video class="player" width="280">
    <source src="" type="video/mp4" />
    Your browser does not support video.
  </video>
</body>
</html>
```

**확인 방법** — 파일을 브라우저로 열어 재생 막대가 보이는지 본다. 녹색 테두리까지 보려면 `src` 에 가지고 있는 영상 파일 경로를 넣고 재생 · 일시정지를 번갈아 눌러 테두리가 바뀌는지 본다(브라우저가 `:playing` 을 지원해야 한다).

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
