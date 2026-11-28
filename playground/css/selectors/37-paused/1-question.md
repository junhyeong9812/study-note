# css/selectors/37 — :paused — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 재생 중이던 `.player2` 를 멈추면 (예측)

```css
/* 질문용 발췌 */
.player2 { border: 3px solid #d1d5db; transition: all 0.3s; }
.player2:paused { opacity: 0.7; border-color: #f59e0b; }
```

- 멈춘 순간부터 어떤 속성들이 어떤 값으로 바뀌는가?
- 그 변화는 한순간에 일어나는가, 시간에 걸쳐 일어나는가?

### 2. 멈춤 상태에서 테두리 색이 겹칠 때 (예측)

```css
/* 질문용 발췌 */
.player2 { border: 3px solid #d1d5db; }
.player2:paused { border-color: #f59e0b; }
```

- 멈춘 `.player2` 의 테두리 색과 테두리 두께는 각각 어느 규칙에서 오는가?

### 3. 전이를 기본 규칙에 둔 까닭 (왜)
- `transition` 을 `.player2:paused` 가 아니라 `.player2` 에 둔 것은 왜인가?

### 4. `div:paused` (경계)
- `div` 에 `:paused` 를 붙인 규칙은 언제 적용되는가?

### 5. 피드백을 「흐리게」 주는 까닭 (왜)
- 멈춘 영상을 숨기지 않고 투명도만 낮추는 것이 나은 까닭은 무엇인가?

### 6. `:hover` 와 `:paused` 의 공통점 (연결)
- 두 선택자는 무엇을 기준으로 요소를 고른다는 점에서 같은 무리인가?

### 7. 클래스 토글과 비교하면 (연결)
- JS 로 멈출 때 클래스를 붙이는 방식과 비교해 `:paused` 를 쓰면 무엇이 줄어드는가?

### 8. 상태 규칙에 무엇까지 적나 (경계)
- 원본이 `:paused` 규칙에 `border` 전체 대신 `border-color` 만 적은 것은 어떤 차이를 만드는가?

## 실습

### 실습 1. 멈추면 흐려지고 테두리 색이 바뀌는 비디오 플레이어

**만들 것** — 컨트롤이 달린 비디오 하나를 두고, 일시정지 상태일 때만 흐려지고 테두리 색이 바뀌게 한다.
변화는 멈출 때와 다시 재생할 때 모두 부드럽게 일어나야 한다.

**요구 조건**
1. 클래스 `player2` 를 가진 `video` 요소에 재생 컨트롤을 단다.
2. 비디오 안에 `source` 요소를 두고, 영상을 지원하지 않을 때 보일 대체 문구를 넣는다.
3. 기본 규칙에 모든 속성이 0.3초에 걸쳐 바뀌는 전이를 건다.
4. 일시정지 상태인 `.player2` 만 고르는 선택자를 쓴다.
5. 그 상태에서 불투명도를 0.7 로 낮춘다.
6. 그 상태에서 테두리 두께는 두고 테두리 색만 바꾼다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>:paused 연습</title>
<style>
  .player2 {
    border-radius: 12px;
    border: 3px solid #d1d5db;
    /* TODO: 모든 속성을 0.3초에 걸쳐 바뀌게 */
  }
  /* TODO: 일시정지 상태의 .player2 를 고르는 선택자 */ {
    /* TODO: 70% 불투명 */
    border-color: #f59e0b;
  }
</style>
</head>
<body>
  <!-- TODO: 컨트롤이 있는 video (class="player2", width="280") -->
    <source src="" type="video/mp4" />
    <!-- TODO: 대체 문구 -->
  <!-- TODO: video 닫기 -->
</body>
</html>
```

**확인 방법** — 브라우저로 열어 플레이어가 멈춤 상태일 때 흐리고 주황 테두리인지 본다.
`src` 에 재생 가능한 파일 경로를 넣으면 재생 ↔ 멈춤을 오가며 변화가 부드러운지도 볼 수 있다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
