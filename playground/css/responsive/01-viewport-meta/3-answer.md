# css/responsive/01 — viewport meta tag — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 980px 너비로 그린 뒤 화면에 맞게 축소한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`<head>` 에 `name="viewport"` 메타 태그가 없다.
그래서 모바일 브라우저는 페이지를 980px 너비로 렌더링한다.
그 그림을 기기 화면 너비에 맞게 통째로 줄여 보여 주므로, 데스크톱 레이아웃이 작게 보이고 글씨를 읽으려면 확대해야 한다.

**왜 그런가**

브라우저는 페이지가 모바일용인지 모르니 데스크톱쯤의 너비를 가정한다.
근거: 2-summary 「동작 방식 (1)」.
980px 라는 숫자는 브라우저 구현 관례다(「구현 세부사항 대 언어 보장」).

### 2. 너비 20px · 높이 15px 로 보인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`.tbox` 는 40px × 30px 이다.
부모 `.tiny-boxes` 에 `scale(0.5)` 가 걸려 있어 자식까지 통째로 절반 크기로 그려진다.
그래서 박스 하나는 화면에서 40 × 0.5 = 20px 너비, 30 × 0.5 = 15px 높이로 보인다.
박스 사이 간격 2px 도 1px 로 보인다.

**왜 그런가**

`transform: scale(0.5)` 는 그려지는 모습을 `transform-origin: center` 를 기준으로 절반으로 줄인다.
레이아웃이 잡아 둔 자리 크기는 그대로다.
근거: 2-summary 「동작 방식 (6)」.

### 3. 확대에 기대는 사람이 글을 키워 읽을 수 없어 접근성을 해친다

`user-scalable=no` 는 핀치줌 자체를 끈다.
시력이 약한 사람 등은 확대해서 글을 읽으므로, 확대를 막으면 그 사람들이 내용을 읽기 어려워진다.
그래서 원본은 이 값을 쓰지 않는 것이 좋다고 하고, `maximum-scale=1` 도 같은 이유로 신중하게 쓰라고 한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 4. 너비와 처음 배율을 각각 정하기 때문이다

`width=device-width` 는 뷰포트 너비를 기기 너비로 정한다 — 980px 가정을 버린다.
`initial-scale=1` 은 페이지를 처음 열 때 배율을 1:1 로 정한다 — 줄이지도 키우지도 않는다.
하나는 「몇 px 로 그릴지」, 다른 하나는 「얼마나 키워 보일지」를 정하므로, 함께 써야 기기 너비로 그린 페이지가 제 크기로 보인다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 5. 보장된 값이 아니라 모바일 브라우저의 구현 관례다

980px 는 원본 팁이 말하는 모바일 브라우저의 동작이다.
HTML · CSS 가 이 숫자를 정해 두지 않았으므로 브라우저마다 다를 수 있다 (확인 필요).
근거: 2-summary 「구현 세부사항 대 언어 보장」.

### 6. 바꾸지 않는다 — 글자로 쓴 소스일 뿐이다

`.meta-tag` 는 `&lt;meta …&gt;` 를 엔티티로 적은 `div` 다.
브라우저는 이것을 `<meta>` 요소로 읽지 않고 글자로만 찍는다.
게다가 이 데모 파일의 `<head>` 에는 viewport 메타 태그가 없다.
뷰포트를 바꾸려면 `<head>` 안에 진짜 `<meta>` 요소를 넣어야 한다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 3」.

### 7. 브라우저가 아는 너비가 980px 라 600px 이하 조건이 맞지 않는다

메타 태그가 없으면 모바일 브라우저는 페이지를 980px 너비로 그린다.
미디어 쿼리는 그 너비를 보고 갈라지므로, `max-width: 600px` 조건은 휴대폰에서도 참이 되지 않는다.
그래서 작은 화면용 규칙이 깨어나지 못하고, 메타 태그가 반응형의 전제 조건이 된다 (원본에 근거 없음 — 추론).
근거: 2-summary 「동작 방식 (5)」.

## 실습 정답

### 실습 1. viewport 미설정 · 설정 비교 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 세 덩어리를 가로로, 가운데 맞춤, 좁으면 줄바꿈 | `.device { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; }` |
| 2. 라벨과 콘텐츠를 세로로 쌓기 | `.screen { display: flex; flex-direction: column; }` |
| 3. 콘텐츠가 남은 높이 차지 · 세로로 · 세로 가운데 | `.content { flex: 1; display: flex; flex-direction: column; justify-content: center; }` |
| 4. 빨강 · 초록 라벨 | `.without .label` · `.with .label` 과 두 `.label` 요소의 글자 |
| 5. 왼쪽 박스를 가로로 놓고 중심 기준 절반 축소 | `.tiny-boxes { display: flex; justify-content: center; transform: scale(0.5); transform-origin: center; }` |
| 6. 오른쪽 박스를 축소 없이 가로로 | `.fit-boxes { display: flex; justify-content: center; }` |
| 7. 메타 태그 소스를 글자로 세 줄 | `.meta-tag` 안의 `&lt;meta name="viewport"<br>content="width=device-width,<br>initial-scale=1"&gt;` |
| 8. 속성 설명을 세로로 | `.attrs { display: flex; flex-direction: column; }` 와 네 `.attr` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/viewport-meta.html`

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
<title>viewport meta tag - <meta name="viewport"> 태그를 통해 모바일 브라우저의 뷰포트 크기와 스케일링을 제어한다. 반응형 디자인의 필수 전제 조건.</title>
<!--
  [반응형 디자인] viewport meta tag
  설명: <meta name="viewport"> 태그를 통해 모바일 브라우저의 뷰포트 크기와 스케일링을 제어한다. 반응형 디자인의 필수 전제 조건.

  팁: viewport 메타 태그 없이는 모바일 브라우저가 페이지를 980px 너비로 렌더링한 뒤 축소한다. user-scalable=no는 접근성을 해치므로 사용하지 않는 것이 좋다. maximum-scale=1도 같은 이유로 신중하게 사용해야 한다.
-->
<style>
  /* .demo: 데모 루트 */
  .demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
  }
  /* .device: 디바이스 모형들을 가로 배치하는 컨테이너 */
  .device {
    display: flex;                        /* flex */
    gap: 16px;                            /* 화면 간격 */
    align-items: center;                  /* 세로 중앙 */
    justify-content: center;              /* 가로 중앙 */
    flex-wrap: wrap;                      /* 좁아지면 줄바꿈 */
    margin-bottom: 16px;                  /* 다음 영역과 간격 */
  }
  /* .screen: 디바이스 화면 모형 공통 */
  .screen {
    width: 140px;                         /* 화면 폭 */
    height: 200px;                        /* 화면 높이 */
    border: 3px solid #374151;            /* 진한 베젤 */
    border-radius: 12px;                  /* 둥근 모서리 */
    padding: 8px;                         /* 내부 여백 */
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 6px;                             /* 자식 간격 */
    background: #f8fafc;                  /* 옅은 배경 */
  }
  /* .label: 화면 상단 라벨 공통 */
  .label {
    font-size: 11px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    text-align: center;                   /* 중앙 정렬 */
    padding: 4px;                         /* 패딩 */
    border-radius: 4px;                   /* 둥근 모서리 */
  }
  /* .without .label: viewport 미설정 라벨(빨강) */
  .without .label {
    background: #fecaca;                  /* 옅은 빨강 */
    color: #991b1b;                       /* 진한 빨강 */
  }
  /* .with .label: viewport 설정됨 라벨(초록) */
  .with .label {
    background: #bbf7d0;                  /* 옅은 초록 */
    color: #166534;                       /* 진한 초록 */
  }
  /* .content: 화면 콘텐츠 영역 */
  .content {
    flex: 1;                              /* 남은 공간 차지 */
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    justify-content: center;              /* 세로 중앙 */
    gap: 8px;                             /* 자식 간격 */
  }
  /* .text: 화면 안 설명 텍스트 */
  .text {
    font-size: 9px;                       /* 매우 작은 폰트 */
    color: #64748b;                       /* 회색 */
    text-align: center;                   /* 중앙 정렬 */
  }
  /* .tiny-boxes: viewport 미설정 시 축소된 박스들 컨테이너 */
  .tiny-boxes {
    display: flex;                        /* flex */
    gap: 2px;                             /* 박스 간격 */
    justify-content: center;              /* 가로 중앙 */
    transform: scale(0.5);                /* 50%로 축소 - 데스크톱 레이아웃이 작게 보이는 모습 시뮬레이션 */
    transform-origin: center;             /* 중심 기준 축소 */
  }
  /* .tbox: 축소된 작은 박스 */
  .tbox {
    width: 40px;                          /* 폭 */
    height: 30px;                         /* 높이 */
    background: #94a3b8;                  /* 회색 */
    border-radius: 2px;                   /* 살짝 둥글게 */
  }
  /* .fit-boxes: viewport 설정 시 적절히 들어맞는 박스들 컨테이너 */
  .fit-boxes {
    display: flex;                        /* flex */
    gap: 4px;                             /* 박스 간격 */
    justify-content: center;              /* 가로 중앙 */
  }
  /* .fbox: 잘 맞는 박스 */
  .fbox {
    width: 35px;                          /* 폭 */
    height: 30px;                         /* 높이 */
    background: #3b82f6;                  /* 파란색 */
    border-radius: 4px;                   /* 둥근 모서리 */
  }
  /* .meta-tag: viewport 메타 태그 코드 표시 */
  .meta-tag {
    font-family: monospace;               /* 고정폭 폰트(코드 느낌) */
    font-size: 11px;                      /* 작은 폰트 */
    background: #1e293b;                  /* 어두운 배경 */
    color: #a5f3fc;                       /* 시안 톤 */
    padding: 10px;                        /* 내부 여백 */
    border-radius: 8px;                   /* 둥근 모서리 */
    text-align: center;                   /* 중앙 정렬 */
    line-height: 1.6;                     /* 줄 간격 */
  }
  /* .attrs: 속성 설명 목록 */
  .attrs {
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 6px;                             /* 항목 간격 */
    font-size: 12px;                      /* 폰트 */
  }
  /* .attr: 개별 속성 설명 항목 */
  .attr {
    padding: 6px 10px;                    /* 패딩 */
    background: #f1f5f9;                  /* 옅은 배경 */
    border-left: 3px solid #3b82f6;       /* 좌측 파란 띠 */
    border-radius: 0 4px 4px 0;           /* 우측만 둥글게 */
  }
</style>
</head>
<body>
<!-- 데모 루트 -->
<div class="demo">
  <!-- 디바이스 비교 영역 -->
  <div class="device">
    <!-- viewport 미설정 화면(왼쪽) -->
    <div class="screen without">
      <!-- 라벨: 미설정 -->
      <div class="label">viewport 미설정</div>
      <!-- 화면 안 콘텐츠 -->
      <div class="content">
        <!-- 설명 텍스트 -->
        <div class="text">데스크톱 레이아웃이 축소되어 보임</div>
        <!-- 축소된 박스들 -->
        <div class="tiny-boxes">
          <!-- 박스 1 -->
          <div class="tbox"></div>
          <!-- 박스 2 -->
          <div class="tbox"></div>
          <!-- 박스 3 -->
          <div class="tbox"></div>
        </div>
      </div>
    </div>
    <!-- 메타 태그 코드 표시(가운데) -->
    <div class="meta-tag">&lt;meta name="viewport"<br>content="width=device-width,<br>initial-scale=1"&gt;</div>
    <!-- viewport 설정됨 화면(오른쪽) -->
    <div class="screen with">
      <!-- 라벨: 설정됨 -->
      <div class="label">viewport 설정됨</div>
      <!-- 화면 콘텐츠 -->
      <div class="content">
        <!-- 설명 텍스트 -->
        <div class="text">디바이스 너비에 맞게 렌더링</div>
        <!-- 잘 맞는 박스들 -->
        <div class="fit-boxes">
          <!-- 박스 1 -->
          <div class="fbox"></div>
          <!-- 박스 2 -->
          <div class="fbox"></div>
          <!-- 박스 3 -->
          <div class="fbox"></div>
        </div>
      </div>
    </div>
  </div>
  <!-- viewport 속성 설명 목록 -->
  <div class="attrs">
    <!-- width=device-width 설명 -->
    <div class="attr"><strong>width=device-width</strong> — 뷰포트 너비를 기기 너비에 맞춤</div>
    <!-- initial-scale=1 설명 -->
    <div class="attr"><strong>initial-scale=1</strong> — 초기 확대/축소 비율 1:1</div>
    <!-- maximum-scale=1 설명 -->
    <div class="attr"><strong>maximum-scale=1</strong> — 최대 확대 제한 (접근성 주의)</div>
    <!-- user-scalable=no 설명 -->
    <div class="attr"><strong>user-scalable=no</strong> — 핀치줌 비활성화 (비권장)</div>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.demo { font-family: system-ui, sans-serif; }
.device { display: flex; gap: 16px; align-items: center; justify-content: center; flex-wrap: wrap; margin-bottom: 16px; }
.screen { width: 140px; height: 200px; border: 3px solid #374151; border-radius: 12px; padding: 8px; display: flex; flex-direction: column; gap: 6px; background: #f8fafc; }
.label { font-size: 11px; font-weight: 700; text-align: center; padding: 4px; border-radius: 4px; }
.without .label { background: #fecaca; color: #991b1b; }
.with .label { background: #bbf7d0; color: #166534; }
.content { flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 8px; }
.text { font-size: 9px; color: #64748b; text-align: center; }
.tiny-boxes { display: flex; gap: 2px; justify-content: center; transform: scale(0.5); transform-origin: center; }
.tbox { width: 40px; height: 30px; background: #94a3b8; border-radius: 2px; }
.fit-boxes { display: flex; gap: 4px; justify-content: center; }
.fbox { width: 35px; height: 30px; background: #3b82f6; border-radius: 4px; }
.meta-tag { font-family: monospace; font-size: 11px; background: #1e293b; color: #a5f3fc; padding: 10px; border-radius: 8px; text-align: center; line-height: 1.6; }
.attrs { display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
.attr { padding: 6px 10px; background: #f1f5f9; border-left: 3px solid #3b82f6; border-radius: 0 4px 4px 0; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 데모는 실제 뷰포트를 바꾸지 않고, 화면 모형 두 개로 차이를 흉내 낸다.
- 「축소되어 보이는 모습」의 핵심 한 줄은 `transform: scale(0.5)` 이고, `transform-origin: center` 로 가운데를 기준 삼는다.
- `.content` 의 `flex: 1` 이 라벨 아래 남은 높이를 채워야 `justify-content: center` 로 세로 가운데가 된다.
- 꺾쇠를 글자로 보이려면 `&lt;` · `&gt;` 엔티티를 쓴다 — 그대로 `<meta>` 를 쓰면 글자가 아니라 요소가 된다.
- 실제 페이지에서 효과를 내려면 `<head>` 안에 `<meta name="viewport" content="width=device-width, initial-scale=1">` 를 넣는다 — 이 데모 파일 자체에는 들어 있지 않다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
