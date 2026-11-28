# animation/advanced-effects/12 — CSS Motion Path — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 이 경로 문자열이 그리는 모양 (예측)

```css
/* 질문용 발췌 */
offset-path: path('M 30,100 C 30,20 270,20 270,100 C 270,180 30,180 30,100');
```

- 이 경로를 따라가면 선이 가운데에서 엇갈리는 ∞ 꼴인가, 아니면 다른 꼴인가?
- 위쪽 곡선은 y=20 까지 올라가는가?

### 2. 1초와 2초 시점의 로켓 위치 (예측)

```css
/* 질문용 발췌 */
offset-path: path('M 30,100 C 30,20 270,20 270,100 C 270,180 30,180 30,100');
animation: followPath 4s linear infinite;
@keyframes followPath { from { offset-distance: 0%; } to { offset-distance: 100%; } }
```

- 애니메이션 시작 후 1초 시점에 로켓은 대략 어느 좌표에 있는가?
- 2초 시점에는 어느 좌표에 있는가?

### 3. 키프레임 끝을 50% 로 줄이면 (예측)

```css
/* 질문용 발췌 */
@keyframes followPath {
  from { offset-distance: 0%; }
  to   { offset-distance: 50%; }
}
```

- 같은 경로 · `4s linear infinite` 에서 한 주기가 끝나 다음 주기로 넘어갈 때 로켓은 어떻게 움직이는가?

### 4. 이동 요소의 `top: 0; left: 0` (왜)

- 로켓이 경로를 따라 여기저기 다니는데도 `top` 과 `left` 를 0 으로 두는 까닭은 무엇인가?

### 5. `path()` 문자열과 SVG `d` 를 똑같이 쓰는 까닭 (왜)

- 이동 경로와 점선 가이드를 같은 문자열로 맞추지 않으면 화면에서 무슨 일이 생기는가?

### 6. 무대를 600×400 으로 키우고 viewBox 는 그대로 둘 때 (경계)

- 점선 가이드와 로켓의 궤적은 여전히 겹치는가?

### 7. 끝점이 출발점과 다른 경로에 `infinite` (경계)

- 끝점을 (270,100) 에서 멈추는 열린 경로로 바꾸면 반복의 이음매에서 어떤 일이 생기는가?

### 8. `linear` 를 `ease` 로 바꾸면 (연결)

- 다른 속성의 애니메이션에서 배운 timing function 이 `offset-distance` 애니메이션에서는 로켓의 무엇을 바꾸는가?

## 실습

### 실습 1. 점선 고리를 따라 도는 로켓 만들기

**만들 것** — 점선으로 그린 닫힌 고리 위를 로켓 이모지가 진행 방향을 바라보며 4초에 한 바퀴씩 끝없이 도는 화면을 만든다.

**요구 조건**
1. 무대(`.motion-path-demo`)는 안에 든 SVG 와 로켓의 절대 위치 기준점이 되고, 무대 밖으로 나간 부분은 숨긴다.
2. SVG 가이드(`.motion-path-svg`)는 무대에 겹쳐 놓이고 무대를 상하좌우로 꽉 채운다.
3. 로켓(`.motion-element`)은 무대 기준으로 절대 배치하고, 시작 기준을 무대의 왼쪽 위 모서리(`top` · `left` 0)에 둔다.
4. 로켓의 이동 경로는 SVG 가이드 `<path>` 의 `d` 와 글자까지 같은 문자열로 정한다.
5. 로켓은 경로의 진행 방향에 맞춰 저절로 회전한다.
6. `followPath` 키프레임은 경로 위의 위치를 시작점(0%)에서 끝점(100%)까지 옮긴다.
7. 로켓은 `followPath` 를 4초 동안 등속으로, 끝없이 반복한다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>CSS Motion Path 연습</title>
  <style>
    .motion-path-demo {
      /* TODO: 자식의 절대 위치 기준점 */
      width: 300px;
      height: 200px;
      background: #f8fafc;
      border-radius: 8px;
      /* TODO: 밖으로 나간 부분 숨기기 */
    }
    .motion-path-svg {
      /* TODO: 무대에 겹쳐 놓고 꽉 채우기 */
    }
    .motion-element {
      /* TODO: 무대 기준 절대 배치, 시작 기준은 왼쪽 위 모서리 */
      font-size: 24px;
      /* TODO: 이동 경로 (SVG d 와 같은 문자열) */
      /* TODO: 진행 방향에 맞춰 회전 */
      /* TODO: followPath 를 4초 등속 무한 반복 */
    }
    @keyframes followPath {
      /* TODO: 경로 위의 위치를 0% → 100% */
    }
  </style>
</head>
<body>
  <div class="motion-path-demo">
    <svg class="motion-path-svg" viewBox="0 0 300 200">
      <path d="M 30,100 C 30,20 270,20 270,100 C 270,180 30,180 30,100" fill="none" stroke="#334155" stroke-width="1" stroke-dasharray="4 4" />
    </svg>
    <div class="motion-element">🚀</div>
  </div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 로켓이 점선 고리 위를 벗어나지 않고 4초에 한 바퀴씩 돌며, 고리를 한 바퀴 다 돌고 다시 시작할 때 튀지 않는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
