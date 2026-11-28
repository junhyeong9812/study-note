# css/responsive/13 — Viewport Units for Full-screen — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 폴백 순서를 뒤집으면 (예측)

```css
/* 질문용 발췌 — dvh 를 아는 최신 모바일 브라우저에서 */
.hero {
  height: 100dvh;
  height: 100vh;
}
```

- 이 `.hero` 의 높이는 두 값 가운데 어느 것으로 정해지는가?

### 2. dvh 를 모르는 브라우저에서 (예측)

```css
/* 질문용 발췌 — dvh 를 모르는 구형 브라우저에서 */
.modal {
  height: 100vh;
  height: 100dvh;
}
```

- 이 브라우저에서 `.modal` 의 높이는 무엇으로 정해지는가?

### 3. 주소창이 숨겨진 순간의 `100dvh` (예측)

- 사용자가 스크롤해 주소창이 숨겨진 상태라면, `100dvh` 는 `100svh` 와 `100lvh` 중 어느 쪽과 같은 높이인가?

### 4. 모바일에서 `100vh` 히어로의 아래가 잘리는 까닭 (왜)

- 데스크톱에서 멀쩡한 `height: 100vh` 히어로 섹션이 모바일 Safari/Chrome 에서 아래가 잘리는 까닭은 무엇인가?

### 5. 폴백 두 줄이 기대는 CSS 규칙 (왜)

- `height: 100vh; height: 100dvh;` 한 쌍이 새 브라우저와 구형 브라우저에서 각각 다른 값을 쓰게 되는 것은 CSS 의 어떤 두 규칙 덕분인가?

### 6. 가로 방향에도 같은 선택지가 있나 (경계)

- 작은 · 큰 · 동적 뷰포트라는 세 기준은 세로 높이에만 있는가, 너비에도 쓸 수 있는가?

### 7. 예제 데모의 폰 모형이 보여 주는 것의 한계 (경계)

- 예제 데모에서 왼쪽 폰의 콘텐츠가 잘리는 것은 실제 `100vh` 계산 때문인가, 다른 무엇 때문인가?

### 8. 이 폴백 패턴을 다른 새 CSS 값에 옮기기 (연결)

- 「옛 값 먼저, 새 값 나중」 두 줄 패턴은 `dvh` 가 아닌 다른 새 CSS 값을 쓸 때도 같은 원리로 통하는가?

## 실습

### 실습 1. 100vh 문제와 100dvh 해결을 나란히 보여 주는 데모 만들기

**만들 것** — 폰 모형 두 개로 「100vh 는 넘쳐 잘리고 100dvh 는 딱 맞는」 모습을 비교하고, 그 아래에 세 뷰포트 단위 설명과 폴백 코드 예시를 놓는 한 쪽짜리 HTML 문서를 만든다.

**요구 조건**

1단계 — 비교 영역
1. 비교 영역(`.vu-problem`)은 폰 모형 · 화살표 · 폰 모형을 가로로 늘어놓고, 가로 · 세로 모두 가운데 정렬하며, 화면이 좁아지면 다음 줄로 넘긴다.
2. 폰 모형(`.vu-phone`)은 위에 주소창 막대(`.vu-address-bar`), 그 아래에 보이는 영역(`.vu-viewport`)을 둔다.
3. 보이는 영역은 고정 높이를 갖고, 그보다 큰 자식은 넘친 부분을 잘라 보이지 않게 한다.
4. 왼쪽 폰의 콘텐츠(`.vu-100vh`)는 보이는 영역보다 일부러 크게 잡아 아래가 잘리게 하고, 「height: 100vh」 라벨과 잘림 경고 뱃지(`.vu-overflow`)를 세로로 가운데 쌓는다.
5. 오른쪽 폰(`.vu-phone fixed`)의 콘텐츠(`.vu-100dvh`)는 보이는 영역과 같은 높이로 잡아 딱 맞게 하고, 「height: 100dvh」 라벨과 정상 뱃지(`.vu-ok`)를 세로로 가운데 쌓는다.
6. 두 폰 사이에 화살표(`.vu-arrow`)를 둔다.

2단계 — 단위 설명 목록
7. 설명 목록(`.vu-units`)은 항목을 세로로 쌓는다.
8. `svh` · `lvh` · `dvh` 세 항목(`.vu-unit`)에 단위 이름(`<strong>`)과 설명(`.vu-desc`)을 넣는다 — 주소창이 보일 때 기준 / 숨겨질 때 기준 / 현재 상태에 따라 동적으로 변경(권장).
9. 권장 단위인 `dvh` 항목에만 `active` 클래스를 달아 강조한다.

3단계 — 코드 예시
10. 코드 상자(`.vu-code`) 안의 `<code>` 는 줄바꿈과 들여쓰기를 그대로 보존해 보여 준다.
11. 코드 예시에는 「문제: `.hero { height: 100vh; }`」 와 「해결: `height: 100vh;` 폴백 다음에 `height: 100dvh;`」 를 적는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Viewport Units for Full-screen</title>
<style>
  .vu-demo { font-family: system-ui, sans-serif; }
  .vu-problem {
    gap: 12px;
    margin-bottom: 16px;
    /* TODO: 가로로 늘어놓기, 세로·가로 가운데 정렬, 좁으면 줄바꿈 */
  }
  .vu-phone { width: 120px; border: 3px solid #374151; border-radius: 14px; overflow: hidden; background: #f8fafc; }
  .vu-address-bar { background: #e2e8f0; padding: 4px; text-align: center; font-size: 9px; color: #64748b; font-weight: 600; }
  .vu-viewport {
    position: relative;
    /* TODO: 보이는 영역 높이 140px 고정, 넘치는 부분 자르기 */
  }
  .vu-100vh {
    background: linear-gradient(to bottom, #bfdbfe, #3b82f6);
    gap: 8px;
    /* TODO: 보이는 영역보다 큰 높이 160px — 잘림 흉내 */
    /* TODO: 자식을 세로로 쌓고 가로·세로 가운데 */
  }
  .vu-100vh span { font-size: 10px; font-weight: 700; color: white; }
  .vu-overflow { background: #ef4444; padding: 2px 6px; border-radius: 4px; font-size: 8px; }
  .vu-phone.fixed .vu-viewport {
    /* TODO: 해결 쪽 폰도 같은 방식으로 자르기 */
  }
  .vu-100dvh {
    background: linear-gradient(to bottom, #bbf7d0, #22c55e);
    gap: 8px;
    /* TODO: 보이는 영역과 같은 높이 140px — 딱 맞음 흉내 */
    /* TODO: 자식을 세로로 쌓고 가로·세로 가운데 */
  }
  .vu-100dvh span { font-size: 10px; font-weight: 700; color: white; }
  .vu-ok { background: #166534; padding: 2px 6px; border-radius: 4px; font-size: 8px; }
  .vu-arrow { font-size: 24px; color: #94a3b8; }
  .vu-units {
    gap: 6px;
    margin-bottom: 12px;
    /* TODO: 항목을 세로로 쌓기 */
  }
  .vu-unit { padding: 8px 12px; background: #f1f5f9; border-radius: 6px; font-size: 12px; border-left: 3px solid #cbd5e1; }
  .vu-unit.active { border-left-color: #22c55e; background: #f0fdf4; }
  .vu-unit strong { color: #1e293b; }
  .vu-desc { font-size: 11px; color: #64748b; margin-top: 2px; }
  .vu-code { background: #1e293b; border-radius: 8px; padding: 14px; }
  .vu-code code {
    font-size: 11px; color: #e2e8f0; line-height: 1.5; display: block;
    /* TODO: 공백·줄바꿈 보존 */
  }
</style>
</head>
<body>
<div class="vu-demo">
  <div class="vu-problem">
    <div class="vu-phone">
      <div class="vu-address-bar">주소창</div>
      <!-- TODO: 보이는 영역 안에 100vh 콘텐츠(라벨 + 잘림 경고 뱃지) -->
    </div>
    <!-- TODO: 화살표 -->
    <div class="vu-phone fixed">
      <div class="vu-address-bar">주소창</div>
      <!-- TODO: 보이는 영역 안에 100dvh 콘텐츠(라벨 + 정상 뱃지) -->
    </div>
  </div>
  <div class="vu-units">
    <!-- TODO: svh / lvh / dvh 세 항목, dvh 에만 active -->
  </div>
  <div class="vu-code">
    <code><!-- TODO: 문제(100vh)와 해결(폴백 + 100dvh) 코드 예시 --></code>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 왼쪽 폰의 파란 콘텐츠는 아래가 잘려 경고 뱃지 쪽이 덜 보이고, 오른쪽 폰의 초록 콘텐츠는 영역에 딱 맞는지, 단위 목록에서 `dvh` 만 강조되는지, 코드 상자의 줄바꿈 · 들여쓰기가 그대로인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
