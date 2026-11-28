# css/responsive/01 — viewport meta tag — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 메타 태그 없는 페이지를 휴대폰에서 열면 (예측)

```html
<!-- 질문용 발췌 -->
<head>
  <meta charset="utf-8">
  <title>내 페이지</title>
</head>
```

- 모바일 브라우저는 이 페이지를 어떤 너비로 그리고, 화면에는 어떻게 보여 주는가?

### 2. 데모의 줄어든 박스 하나의 크기 (예측)

```css
/* 질문용 발췌 */
.tiny-boxes { display: flex; gap: 2px; transform: scale(0.5); transform-origin: center; }
.tbox { width: 40px; height: 30px; }
```

- 박스 하나는 화면에서 너비와 높이가 각각 얼마로 보이는가?

### 3. `user-scalable=no` 를 피하라는 까닭 (왜)

- 핀치줌을 끄는 것이 왜 문제가 되는가?

### 4. `width=device-width` 와 `initial-scale=1` 을 짝으로 쓰는 까닭 (왜)

- 두 값은 각각 무엇을 정하기에 함께 쓰는가?

### 5. 980px 라는 숫자의 출처 (경계)

- 메타 태그가 없을 때의 980px 는 HTML · CSS 가 보장하는 값인가, 누가 정한 값인가?

### 6. 데모 가운데 상자의 효과 (경계)

- 예제의 `.meta-tag` 상자는 이 데모 페이지의 뷰포트를 바꾸는가?

### 7. 메타 태그와 미디어 쿼리 (연결)

- 메타 태그 없이 `@media (max-width: 600px)` 규칙만 둔 페이지를 휴대폰에서 열면 그 규칙은 왜 뜻대로 움직이지 않는가?

## 실습

### 실습 1. viewport 미설정 · 설정 비교 데모 만들기

**만들 것** — 화면 모형 두 개로 「메타 태그가 없을 때 축소되어 보이는 모습」과 「기기 너비에 맞게 그려진 모습」을 나란히 보여 주고, 가운데에 메타 태그 소스를, 아래에 속성 설명 목록을 놓는다.

**요구 조건**

1. `.device` 안에 왼쪽 화면 모형(`.screen.without`), 가운데 메타 태그 상자(`.meta-tag`), 오른쪽 화면 모형(`.screen.with`)을 가로로 늘어놓는다 — 가로 · 세로 모두 가운데 맞추고, 폭이 좁아지면 줄을 바꾼다.
2. 각 화면 모형은 위의 라벨과 아래의 콘텐츠(`.content`)를 세로로 쌓는다.
3. `.content` 는 라벨을 뺀 남은 높이를 모두 차지하고, 그 안의 설명 글과 박스 묶음을 세로로 쌓아 세로 가운데에 놓는다.
4. 왼쪽 라벨은 「viewport 미설정」을 빨강 계열로, 오른쪽 라벨은 「viewport 설정됨」을 초록 계열로 보여 준다.
5. 왼쪽 박스 셋(`.tiny-boxes`)은 가로로 가운데 맞춰 놓되, `transform` 으로 중심을 기준 삼아 절반 크기로 줄여 「축소된 데스크톱 레이아웃」을 흉내 낸다.
6. 오른쪽 박스 셋(`.fit-boxes`)은 축소 없이 가로로 가운데 맞춰 놓는다.
7. 가운데 상자에 `<meta name="viewport" content="width=device-width, initial-scale=1">` 소스를 꺾쇠까지 글자로 보이게 세 줄로 나눠 적는다(진짜 태그가 아니라 글자로).
8. 아래 `.attrs` 에 네 값(`width=device-width` · `initial-scale=1` · `maximum-scale=1` · `user-scalable=no`)의 설명을 세로로 쌓는다.

**시작 코드**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>viewport meta tag</title>
<style>
  .demo { font-family: system-ui, sans-serif; }
  .device {
    gap: 16px; margin-bottom: 16px;
    /* TODO: 가로 배치 · 세로 가운데 · 가로 가운데 · 좁으면 줄바꿈 */
  }
  .screen {
    width: 140px; height: 200px; border: 3px solid #374151; border-radius: 12px;
    padding: 8px; gap: 6px; background: #f8fafc;
    /* TODO: 라벨과 콘텐츠를 세로로 쌓기 */
  }
  .label { font-size: 11px; font-weight: 700; text-align: center; padding: 4px; border-radius: 4px; }
  .without .label { background: #fecaca; color: #991b1b; }
  .with .label { background: #bbf7d0; color: #166534; }
  .content {
    gap: 8px;
    /* TODO: 남은 높이 차지 · 세로로 쌓기 · 세로 가운데 */
  }
  .text { font-size: 9px; color: #64748b; text-align: center; }
  .tiny-boxes {
    gap: 2px;
    /* TODO: 가로 배치 · 가로 가운데 · 중심 기준 절반 축소 */
  }
  .tbox { width: 40px; height: 30px; background: #94a3b8; border-radius: 2px; }
  .fit-boxes {
    gap: 4px;
    /* TODO: 가로 배치 · 가로 가운데 */
  }
  .fbox { width: 35px; height: 30px; background: #3b82f6; border-radius: 4px; }
  .meta-tag { font-family: monospace; font-size: 11px; background: #1e293b; color: #a5f3fc; padding: 10px; border-radius: 8px; text-align: center; line-height: 1.6; }
  .attrs {
    gap: 6px; font-size: 12px;
    /* TODO: 설명 항목을 세로로 쌓기 */
  }
  .attr { padding: 6px 10px; background: #f1f5f9; border-left: 3px solid #3b82f6; border-radius: 0 4px 4px 0; }
</style>
</head>
<body>
<div class="demo">
  <div class="device">
    <div class="screen without">
      <div class="label">viewport 미설정</div>
      <div class="content">
        <div class="text">데스크톱 레이아웃이 축소되어 보임</div>
        <div class="tiny-boxes">
          <div class="tbox"></div><div class="tbox"></div><div class="tbox"></div>
        </div>
      </div>
    </div>
    <div class="meta-tag"><!-- TODO: 메타 태그 소스를 꺾쇠까지 글자로, 세 줄로 --></div>
    <div class="screen with">
      <div class="label">viewport 설정됨</div>
      <div class="content">
        <div class="text">디바이스 너비에 맞게 렌더링</div>
        <div class="fit-boxes">
          <div class="fbox"></div><div class="fbox"></div><div class="fbox"></div>
        </div>
      </div>
    </div>
  </div>
  <div class="attrs">
    <div class="attr"><strong>width=device-width</strong> — 뷰포트 너비를 기기 너비에 맞춤</div>
    <div class="attr"><strong>initial-scale=1</strong> — 초기 확대/축소 비율 1:1</div>
    <div class="attr"><strong>maximum-scale=1</strong> — 최대 확대 제한 (접근성 주의)</div>
    <div class="attr"><strong>user-scalable=no</strong> — 핀치줌 비활성화 (비권장)</div>
  </div>
</div>
</body>
</html>
```

**확인 방법** — 브라우저로 열어 왼쪽 화면 모형의 회색 박스들이 오른쪽 파란 박스들보다 작게 줄어 있는지, 가운데 상자에 `<meta …>` 소스가 글자로 세 줄에 찍히는지, 창을 좁히면 세 덩어리가 줄을 바꾸는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
