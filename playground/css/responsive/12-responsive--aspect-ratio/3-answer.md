# css/responsive/12 — Aspect Ratio Boxes — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 높이 180px — 폭에서 비율로 계산된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
높이는 320 × 9 ÷ 16 = 180px 이 된다.

**왜 그런가**
폭은 320px 로 정해졌고 높이는 비어 있다.
`aspect-ratio` 는 비어 있는 쪽을 「폭 × 세로비 ÷ 가로비」로 채운다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 400px × 150px — 16:9 가 깨진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
폭 400px, 높이 150px 이 되어 16:9 모양이 유지되지 않는다(400:150 = 8:3).

**왜 그런가**
비율대로라면 높이는 400 × 9 ÷ 16 = 225px 다.
`max-height: 150px` 가 높이를 150px 로 누르지만 폭은 직접 지정된 값이라 줄지 않는다.
원본 팁 「max-height 등으로 제약하면 비율이 깨질 수 있으므로 주의」가 이 경우다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 3. 폭 120px — 높이에서 비율로 계산된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
폭은 90 × 4 ÷ 3 = 120px 이 된다.

**왜 그런가**
원본 팁대로 높이만 지정하면 폭을 계산한다.
계산 방향만 1번과 반대다.
근거: 2-summary 「동작 방식 (2)」.

### 4. 퍼센트 패딩은 폭 기준이고, 56.25% 는 9 ÷ 16 이다

`padding-top` 이 세로 방향 여백이어도 퍼센트일 때는 부모의 폭을 기준으로 계산된다.
그래서 빈 박스의 높이를 패딩만으로 채우면 높이가 늘 폭의 일정 비율이 된다.
16:9 에서 세로는 가로의 9/16 = 0.5625, 곧 56.25% 다(원본 예제 주석 `/* 9/16 = 56.25% */`).
근거: 2-summary 「동작 방식 (4)」. 「퍼센트 패딩이 폭 기준」이라는 설명은 (원본에 근거 없음 — 추론).

### 5. 비율이 크기에 영향을 주지 못한다

`aspect-ratio` 는 정해진 한쪽으로 비어 있는 다른 쪽을 계산하는 규칙이다.
두 쪽이 다 정해져 있으면 채울 자리가 없으므로 지정한 폭과 높이가 그대로 쓰인다.
원본 팁은 「한쪽만 지정했을 때」만 말하므로 이 결론은 그 팁에서 이어 낸 것이다.
근거: 2-summary 「어디서 틀리나 2」 (원본에 근거 없음 — 추론).

### 6. 비율은 바깥 박스가 갖고, 보이는 배경은 안쪽 박스가 칠하기 때문이다

`.ar-box` 의 높이는 비율로 정해지지만 그라데이션 배경은 `.ar-inner` 에 칠해져 있다.
`.ar-inner` 가 `width: 100%; height: 100%` 로 바깥 박스를 꽉 채워야 비율이 정한 모양 그대로 칠해지고, 라벨도 그 한가운데에 놓인다.
원본 주석도 「부모 높이 채움(aspect-ratio가 정한 높이)」이라고 적는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 7. 높이도 같이 늘고 모양은 그대로다

칸 폭은 `minmax(120px, 1fr)` 에 따라 120px 이상에서 컨테이너에 맞춰 바뀐다.
각 박스는 그 폭을 기준으로 높이를 비율로 계산하므로 폭이 늘면 높이도 늘고, 가로세로 비는 유지된다.
칸 수가 바뀌어 칸 폭이 달라져도 같은 원리로 모양은 그대로다.
근거: 2-summary 「동작 방식 (1)」 · 「문법 — 형태와 규칙」.

### 8. 폭 쪽 제약(`max-width` 등)으로 조절한다

폭을 제한하면 높이는 줄어든 폭에서 다시 비율로 계산되므로 모양이 유지된다.
반대로 `max-height` 로 높이를 자르면 폭이 그대로 남아 비율이 깨진다(2번).
근거: 2-summary 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」 (원본에 근거 없음 — 추론).

## 실습 정답

### 실습 1. 네 가지 비율 박스와 코드 예시 판 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 반응형 그리드 배치 | `.ar-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }` |
| 2. 16:9 · 4:3 · 21:9 를 `가로 / 세로` 로 | `.ratio-16-9 { aspect-ratio: 16 / 9; }` · `.ratio-4-3 { aspect-ratio: 4 / 3; }` · `.ratio-21-9 { aspect-ratio: 21 / 9; }` |
| 3. 1:1 을 숫자 하나로 | `.ratio-1-1 { aspect-ratio: 1; }` |
| 4. 라벨이 박스를 채우고 가운데 정렬 | `.ar-inner { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }` |
| 5. 둥근 모서리 밖 자르기 | `.ar-box { overflow: hidden; }` |
| 6. 코드 판의 공백 · 줄바꿈 보존 | `.ar-code code { white-space: pre; }` 와 `<code>` 안의 `.video` · `.thumbnail` · `.avatar` · `.old-ratio` 예 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/responsive--aspect-ratio.html`

```html
<!-- DOCTYPE: HTML5 -->
<!DOCTYPE html>
<!-- 한국어 문서 -->
<html lang="ko">
<!-- 메타데이터 -->
<head>
<!-- UTF-8 -->
<meta charset="utf-8">
<!-- 탭 제목 -->
<title>Aspect Ratio Boxes - aspect-ratio 속성으로 요소의 가로세로 비율을 유지한다. 비디오 임베드, 이미지 카드, 썸네일 등에 필수.</title>
<!--
  [반응형 디자인] Aspect Ratio Boxes
  설명: aspect-ratio 속성으로 요소의 가로세로 비율을 유지한다. 비디오 임베드, 이미지 카드, 썸네일 등에 필수.

  팁: aspect-ratio는 width만 지정하면 height를 자동 계산하고, height만 지정하면 width를 계산한다. max-height 등으로 제약하면 비율이 깨질 수 있으므로 주의. 이전에는 padding-top 퍼센트 핵을 사용했지만 이제 aspect-ratio가 모든 모던 브라우저에서 지원된다.
-->
<style>
  /* .ar-demo: 데모 루트 */
  .ar-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
  }
  /* .ar-grid: 비율 박스들의 그리드 컨테이너 */
  .ar-grid {
    display: grid;                        /* 그리드 */
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); /* 120px 이상 자동 배치, 폭이 늘면 더 채움 */
    gap: 12px;                            /* 박스 간격 */
    margin-bottom: 12px;                  /* 코드와 간격 */
  }
  /* .ar-box: 비율 박스 공통 컨테이너 */
  .ar-box {
    border-radius: 8px;                   /* 둥근 모서리 */
    overflow: hidden;                     /* 자식이 모서리 밖으로 나가지 않게 */
  }
  /* .ratio-16-9: 16:9 비율(영상/유튜브 표준) */
  .ratio-16-9 {
    aspect-ratio: 16 / 9;                 /* 가로:세로 = 16:9 - height 자동 계산 */
  }
  /* .ratio-4-3: 4:3 비율(클래식 사진) */
  .ratio-4-3 {
    aspect-ratio: 4 / 3;                  /* 가로:세로 = 4:3 */
  }
  /* .ratio-1-1: 1:1 정사각형(아바타/썸네일) */
  .ratio-1-1 {
    aspect-ratio: 1;                      /* 정사각형 (1:1과 동일) */
  }
  /* .ratio-21-9: 21:9 울트라와이드 */
  .ratio-21-9 {
    aspect-ratio: 21 / 9;                 /* 시네마/울트라와이드 비율 */
  }
  /* .ar-inner: 박스 내부(라벨 표시용) */
  .ar-inner {
    width: 100%;                          /* 부모 폭 채움 */
    height: 100%;                         /* 부모 높이 채움(aspect-ratio가 정한 높이) */
    display: flex;                        /* 라벨 가운데 정렬 */
    align-items: center;                  /* 세로 중앙 */
    justify-content: center;              /* 가로 중앙 */
    font-weight: 700;                     /* 굵게 */
    font-size: 14px;                      /* 라벨 폰트 */
    color: white;                         /* 흰색 */
  }
  /* .ratio-16-9 .ar-inner: 16:9 박스 그라데이션 */
  .ratio-16-9 .ar-inner {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8); /* 파랑 톤 그라데이션 */
  }
  /* .ratio-4-3 .ar-inner: 4:3 박스 그라데이션 */
  .ratio-4-3 .ar-inner {
    background: linear-gradient(135deg, #8b5cf6, #6d28d9); /* 보라 톤 그라데이션 */
  }
  /* .ratio-1-1 .ar-inner: 1:1 박스 그라데이션 */
  .ratio-1-1 .ar-inner {
    background: linear-gradient(135deg, #10b981, #059669); /* 초록 톤 그라데이션 */
  }
  /* .ratio-21-9 .ar-inner: 21:9 박스 그라데이션 */
  .ratio-21-9 .ar-inner {
    background: linear-gradient(135deg, #f59e0b, #d97706); /* 호박/주황 톤 그라데이션 */
  }
  /* .ar-code: 코드 박스(다크) */
  .ar-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .ar-code code: 코드 텍스트 */
  .ar-code code {
    font-size: 11px;                      /* 작은 폰트 */
    color: #e2e8f0;                       /* 밝은 글자 */
    white-space: pre;                     /* 공백/개행 보존 */
    line-height: 1.5;                     /* 줄 간격 */
    display: block;                       /* 블록 */
  }
</style>
</head>
<body>
<!-- 데모 루트 -->
<div class="ar-demo">
  <!-- 비율 박스 그리드 -->
  <div class="ar-grid">
    <!-- 16:9 박스 -->
    <div class="ar-box ratio-16-9">
      <!-- 라벨 -->
      <div class="ar-inner">16 : 9</div>
    </div>
    <!-- 4:3 박스 -->
    <div class="ar-box ratio-4-3">
      <!-- 라벨 -->
      <div class="ar-inner">4 : 3</div>
    </div>
    <!-- 1:1 정사각형 -->
    <div class="ar-box ratio-1-1">
      <!-- 라벨 -->
      <div class="ar-inner">1 : 1</div>
    </div>
    <!-- 21:9 울트라와이드 -->
    <div class="ar-box ratio-21-9">
      <!-- 라벨 -->
      <div class="ar-inner">21 : 9</div>
    </div>
  </div>
  <!-- 코드 예시 박스 -->
  <div class="ar-code">
    <code>/* aspect-ratio 속성 */
.video { aspect-ratio: 16 / 9; }
.thumbnail { aspect-ratio: 4 / 3; }
.avatar { aspect-ratio: 1; }  /* 정사각형 */

/* 이전 방식 (padding-top hack) */
.old-ratio {
  padding-top: 56.25%; /* 9/16 = 56.25% */
  position: relative;
}</code>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.ar-demo { font-family: system-ui, sans-serif; }
.ar-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; margin-bottom: 12px; }
.ar-box { border-radius: 8px; overflow: hidden; }
.ratio-16-9 { aspect-ratio: 16 / 9; }
.ratio-4-3 { aspect-ratio: 4 / 3; }
.ratio-1-1 { aspect-ratio: 1; }
.ratio-21-9 { aspect-ratio: 21 / 9; }
.ar-inner { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; color: white; }
.ratio-16-9 .ar-inner { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.ratio-4-3 .ar-inner { background: linear-gradient(135deg, #8b5cf6, #6d28d9); }
.ratio-1-1 .ar-inner { background: linear-gradient(135deg, #10b981, #059669); }
.ratio-21-9 .ar-inner { background: linear-gradient(135deg, #f59e0b, #d97706); }
.ar-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.ar-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 박스들에는 `height` 가 한 줄도 없다 — 높이는 그리드 칸 폭과 `aspect-ratio` 가 함께 정한다.
- `aspect-ratio: 1` 은 `1 / 1` 과 같아 정사각형이 된다.
- 비율은 바깥 `.ar-box` 가, 배경과 라벨은 안쪽 `.ar-inner` 가 맡는다 — 안쪽이 `100%` 로 채워야 비율이 눈에 보인다.
- 코드 판의 `.old-ratio` 예는 같은 16:9 를 `padding-top: 56.25%` 로 만들던 옛 방식을 나란히 보여 준다.
- 창 폭을 바꾸면 칸 수와 크기는 바뀌어도 네 박스의 모양은 그대로다 (코드에서 읽은 것 — 렌더 실측 아님).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
