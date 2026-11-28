# css/responsive/13 — Viewport Units for Full-screen — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `100vh` 가 이긴다 — `dvh` 의 효과가 사라진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

이 브라우저는 두 선언을 모두 해석할 수 있으므로 둘 다 유효하다.
같은 속성이 한 규칙 안에 두 번 나오면 나중 선언을 쓰므로 `height: 100vh` 가 적용된다.
그래서 모바일에서는 여전히 주소창 때문에 아래가 잘린다.

**왜 그런가**

폴백 패턴은 「옛 값 먼저, 새 값 나중」일 때만 새 브라우저가 새 값을 쓴다.
순서를 뒤집으면 새 브라우저에서도 옛 값이 마지막에 남는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 2. `100vh` 로 정해진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

이 브라우저는 `100dvh` 를 해석하지 못하므로 두 번째 선언을 통째로 버린다.
남은 첫 번째 선언 `height: 100vh` 가 적용된다.

**왜 그런가**

CSS 는 해석하지 못하는 값이 든 선언을 무시하고 앞 선언을 그대로 둔다.
그래서 높이가 비지 않고 폴백인 `100vh` 가 쓰인다.
근거: 2-summary 「동작 방식 (3)」.

### 3. `100lvh` 와 같다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`dvh` 는 현재 상태에 따라 바뀌고, 지금은 주소창이 숨겨진 상태다.
주소창이 숨겨질 때를 기준으로 한 단위는 `lvh` 이므로 `100dvh` 는 `100lvh` 와 같은 높이가 된다.

**왜 그런가**

`svh` 는 주소창이 보일 때(가장 작은 뷰포트), `lvh` 는 숨겨질 때(가장 큰 뷰포트)의 기준이다.
`dvh` 는 두 상태 사이를 지금 상태에 맞춰 오가므로, 숨겨진 순간에는 큰 쪽을 따른다.
근거: 2-summary 「동작 방식 (2)」.

### 4. `100vh` 가 주소창이 차지한 자리를 고려하지 않기 때문이다

모바일 Safari/Chrome 에서 `100vh` 는 주소창 자리를 빼지 않은 높이로 잡힌다.
주소창이 화면 위를 차지하면 실제로 보이는 영역은 그보다 작다.
요소가 보이는 영역보다 크므로 넘친 아래쪽이 화면 밖으로 밀려 잘린다.
근거: 2-summary 「동작 방식 (1)」.
원본의 팁(「주소창을 포함하지 않아」)과 코드 주석(「주소창 포함」)은 글자로는 엇갈리지만 같은 현상을 가리킨다 — 2-summary 「어디서 틀리나 4」.

### 5. 「나중 선언이 이긴다」와 「모르는 값의 선언은 무시된다」

- 새 브라우저: 두 선언이 모두 유효하므로 나중 선언 `100dvh` 가 이긴다.
- 구형 브라우저: `100dvh` 선언을 해석하지 못해 버리므로 앞의 `100vh` 만 남는다.

근거: 2-summary 「동작 방식 (3)」 · 「구현 세부사항 대 언어 보장」(둘 다 CSS 명세가 정한 규칙이다).

### 6. 너비에도 쓸 수 있다 — `svw` · `lvw` · `dvw`

원본 팁에 따르면 `svw` · `lvw` · `dvw` 가 같은 원리로 가로에 적용된다.
작은 · 큰 · 동적 뷰포트라는 세 기준이 그대로 너비 단위로 옮겨진 것이다.
근거: 2-summary 「동작 방식 (4)」.

### 7. 실제 `100vh` 계산이 아니라 고정 px 높이와 `overflow: hidden` 때문이다

데모의 보이는 영역(`.vu-viewport`)은 140px 고정 높이에 `overflow: hidden` 이다.
왼쪽 콘텐츠(`.vu-100vh`)를 160px 로 일부러 크게 잡아 넘친 아래 20px 이 잘리게 만들었다.
오른쪽 콘텐츠(`.vu-100dvh`)는 140px 로 영역과 같게 잡았을 뿐이다.
즉 데모는 문제를 그림으로 흉내 낸 것이고, 실제 단위의 측정이 아니다.
또 경고 뱃지는 주소창 모형 뒤가 아니라 폰 모형 아래쪽에서 잘린다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 8. 통한다 — 기대는 두 규칙이 `dvh` 에 묶여 있지 않기 때문이다

「나중 선언이 이긴다」와 「모르는 값의 선언은 무시된다」는 CSS 전체에 적용되는 규칙이다.
그래서 어떤 새 CSS 값이든 옛 브라우저가 아는 값을 먼저, 새 값을 나중에 적으면 같은 방식으로 고르게 된다.
근거: 2-summary 「동작 방식 (3)」 마지막 불릿 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 100vh 문제와 100dvh 해결을 나란히 보여 주는 데모 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 비교 영역 가로 배치 · 가운데 정렬 · 줄바꿈 | `.vu-problem { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; }` |
| 2. 폰 모형 = 주소창 막대 + 보이는 영역 | `<div class="vu-phone">` 안의 `.vu-address-bar` · `.vu-viewport` |
| 3. 보이는 영역 고정 높이 · 넘침 자르기 | `.vu-viewport { height: 140px; overflow: hidden; }` |
| 4. 왼쪽 콘텐츠를 크게 잡아 잘림 · 라벨과 경고 뱃지 세로 가운데 | `.vu-100vh { height: 160px; display: flex; flex-direction: column; align-items: center; justify-content: center; }` · `.vu-overflow` |
| 5. 오른쪽 콘텐츠를 영역과 같은 높이로 · 라벨과 정상 뱃지 | `.vu-phone.fixed .vu-viewport { overflow: hidden; }` · `.vu-100dvh { height: 140px; … }` · `.vu-ok` |
| 6. 두 폰 사이 화살표 | `<div class="vu-arrow">→</div>` |
| 7. 설명 목록 세로 쌓기 | `.vu-units { display: flex; flex-direction: column; }` |
| 8. svh · lvh · dvh 세 항목 | `.vu-unit` 셋, 각각 `<strong>` + `.vu-desc` |
| 9. dvh 만 강조 | `<div class="vu-unit active">` · `.vu-unit.active` |
| 10. 코드 줄바꿈 · 들여쓰기 보존 | `.vu-code code { white-space: pre; display: block; }` |
| 11. 문제 코드와 해결(폴백 + dvh) 코드 | `.vu-code` 안 `<code>` 의 내용 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/responsive/reference/viewport-units-fullscreen.html`

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
<title>Viewport Units for Full-screen - 100vh의 모바일 주소창 문제와 dvh(dynamic viewport height) 등 새로운 뷰포트 단위로 해결하는 방법.</title>
<!--
  [반응형 디자인] Viewport Units for Full-screen
  설명: 100vh의 모바일 주소창 문제와 dvh(dynamic viewport height) 등 새로운 뷰포트 단위로 해결하는 방법.

  팁: 모바일 Safari/Chrome에서 100vh는 주소창을 포함하지 않아 콘텐츠가 잘린다. 100dvh를 사용하되, 구형 브라우저를 위해 100vh를 폴백으로 먼저 선언한다. 히어로 섹션, 풀스크린 모달 등에서 특히 중요하다. svw/lvw/dvw도 동일한 원리로 가로에 적용된다.
-->
<style>
  /* .vu-demo: 데모 루트 */
  .vu-demo {
    font-family: system-ui, sans-serif;   /* 시스템 폰트 */
  }
  /* .vu-problem: 100vh 문제 vs 100dvh 해결 비교 영역 */
  .vu-problem {
    display: flex;                        /* flex */
    gap: 12px;                            /* 항목 간격 */
    align-items: center;                  /* 세로 중앙 */
    justify-content: center;              /* 가로 중앙 */
    flex-wrap: wrap;                      /* 좁아지면 줄바꿈 */
    margin-bottom: 16px;                  /* 다음 영역과 간격 */
  }
  /* .vu-phone: 폰 모형 */
  .vu-phone {
    width: 120px;                         /* 폰 폭 */
    border: 3px solid #374151;            /* 베젤 */
    border-radius: 14px;                  /* 둥근 모서리 */
    overflow: hidden;                     /* 자식이 모서리 밖으로 나가지 않게 */
    background: #f8fafc;                  /* 옅은 배경 */
  }
  /* .vu-address-bar: 모바일 주소창 모형 */
  .vu-address-bar {
    background: #e2e8f0;                  /* 옅은 회색 */
    padding: 4px;                         /* 패딩 */
    text-align: center;                   /* 중앙 정렬 */
    font-size: 9px;                       /* 매우 작은 폰트 */
    color: #64748b;                       /* 회색 */
    font-weight: 600;                     /* 약간 굵게 */
  }
  /* .vu-viewport: 폰 안의 보이는 뷰포트 영역 */
  .vu-viewport {
    height: 140px;                        /* 뷰포트 높이 */
    position: relative;                   /* 자식 absolute 기준 */
    overflow: hidden;                     /* 넘치는 부분 자르기 */
  }
  /* .vu-100vh: 100vh로 설정된 콘텐츠 - 뷰포트보다 크게 그려져 잘림 시뮬레이션 */
  .vu-100vh {
    height: 160px;                        /* 의도적으로 뷰포트보다 큼 - 100vh 잘림 문제 표현 */
    background: linear-gradient(to bottom, #bfdbfe, #3b82f6); /* 파랑 그라데이션 */
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    align-items: center;                  /* 가로 중앙 */
    justify-content: center;              /* 세로 중앙 */
    gap: 8px;                             /* 자식 간격 */
  }
  /* .vu-100vh span: 100vh 콘텐츠 안 라벨 */
  .vu-100vh span {
    font-size: 10px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    color: white;                         /* 흰 글자 */
  }
  /* .vu-overflow: 잘림 발생 경고 뱃지 */
  .vu-overflow {
    background: #ef4444;                  /* 빨강 */
    padding: 2px 6px;                     /* 패딩 */
    border-radius: 4px;                   /* 둥근 모서리 */
    font-size: 8px;                       /* 매우 작음 */
  }
  /* .vu-phone.fixed .vu-viewport: 고정(해결됨) 폰의 뷰포트 - 동일하게 자르기 */
  .vu-phone.fixed .vu-viewport {
    overflow: hidden;                     /* 자르기 */
  }
  /* .vu-100dvh: 100dvh로 설정된 콘텐츠 - 뷰포트와 정확히 같은 크기 */
  .vu-100dvh {
    height: 140px;                        /* 뷰포트와 동일 - dvh 정확히 맞음 */
    background: linear-gradient(to bottom, #bbf7d0, #22c55e); /* 초록 그라데이션 */
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    align-items: center;                  /* 가로 중앙 */
    justify-content: center;              /* 세로 중앙 */
    gap: 8px;                             /* 자식 간격 */
  }
  /* .vu-100dvh span: 100dvh 콘텐츠 안 라벨 */
  .vu-100dvh span {
    font-size: 10px;                      /* 작은 폰트 */
    font-weight: 700;                     /* 굵게 */
    color: white;                         /* 흰 글자 */
  }
  /* .vu-ok: 정상 동작 뱃지 */
  .vu-ok {
    background: #166534;                  /* 진한 초록 */
    padding: 2px 6px;                     /* 패딩 */
    border-radius: 4px;                   /* 둥근 모서리 */
    font-size: 8px;                       /* 매우 작음 */
  }
  /* .vu-arrow: 비교 화살표 */
  .vu-arrow {
    font-size: 24px;                      /* 큰 폰트 */
    color: #94a3b8;                       /* 회색 */
  }
  /* .vu-units: 뷰포트 단위 설명 목록 */
  .vu-units {
    display: flex;                        /* flex */
    flex-direction: column;               /* 세로 정렬 */
    gap: 6px;                             /* 항목 간격 */
    margin-bottom: 12px;                  /* 코드와 간격 */
  }
  /* .vu-unit: 단위 설명 항목(svh/lvh/dvh) */
  .vu-unit {
    padding: 8px 12px;                    /* 패딩 */
    background: #f1f5f9;                  /* 옅은 배경 */
    border-radius: 6px;                   /* 둥근 모서리 */
    font-size: 12px;                      /* 폰트 */
    border-left: 3px solid #cbd5e1;       /* 기본 좌측 띠 */
  }
  /* .vu-unit.active: 권장 단위(dvh) 강조 */
  .vu-unit.active {
    border-left-color: #22c55e;           /* 좌측 띠 초록 */
    background: #f0fdf4;                  /* 옅은 초록 배경 */
  }
  /* .vu-unit strong: 단위 이름 강조 */
  .vu-unit strong {
    color: #1e293b;                       /* 어두운 색 */
  }
  /* .vu-desc: 단위 설명 텍스트 */
  .vu-desc {
    font-size: 11px;                      /* 작은 폰트 */
    color: #64748b;                       /* 회색 */
    margin-top: 2px;                      /* 위쪽 간격 */
  }
  /* .vu-code: 코드 박스(다크) */
  .vu-code {
    background: #1e293b;                  /* 어두운 배경 */
    border-radius: 8px;                   /* 둥근 모서리 */
    padding: 14px;                        /* 내부 여백 */
  }
  /* .vu-code code: 코드 텍스트 */
  .vu-code code {
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
<div class="vu-demo">
  <!-- 100vh 문제 vs 100dvh 해결 비교 -->
  <div class="vu-problem">
    <!-- 왼쪽: 100vh 문제(잘림) -->
    <div class="vu-phone">
      <!-- 주소창 -->
      <div class="vu-address-bar">주소창</div>
      <!-- 뷰포트 영역 -->
      <div class="vu-viewport">
        <!-- 100vh 콘텐츠(잘림 발생) -->
        <div class="vu-100vh">
          <!-- 라벨 -->
          <span>height: 100vh</span>
          <!-- 잘림 경고 -->
          <span class="vu-overflow">이 부분이 주소창 뒤로 숨음!</span>
        </div>
      </div>
    </div>
    <!-- 비교 화살표 -->
    <div class="vu-arrow">→</div>
    <!-- 오른쪽: 100dvh 해결 -->
    <div class="vu-phone fixed">
      <!-- 주소창 -->
      <div class="vu-address-bar">주소창</div>
      <!-- 뷰포트 영역 -->
      <div class="vu-viewport">
        <!-- 100dvh 콘텐츠(딱 맞음) -->
        <div class="vu-100dvh">
          <!-- 라벨 -->
          <span>height: 100dvh</span>
          <!-- 정상 뱃지 -->
          <span class="vu-ok">주소창 고려하여 딱 맞음</span>
        </div>
      </div>
    </div>
  </div>
  <!-- 뷰포트 단위 설명 목록 -->
  <div class="vu-units">
    <!-- svh: 가장 작은 뷰포트(주소창 보일 때) -->
    <div class="vu-unit">
      <!-- 단위명 -->
      <strong>svh</strong> (Small Viewport)
      <!-- 설명 -->
      <div class="vu-desc">주소창이 보일 때 기준 (가장 작은 뷰포트)</div>
    </div>
    <!-- lvh: 가장 큰 뷰포트(주소창 숨겨질 때) -->
    <div class="vu-unit">
      <!-- 단위명 -->
      <strong>lvh</strong> (Large Viewport)
      <!-- 설명 -->
      <div class="vu-desc">주소창이 숨겨질 때 기준 (가장 큰 뷰포트)</div>
    </div>
    <!-- dvh: 동적(권장) -->
    <div class="vu-unit active">
      <!-- 단위명 -->
      <strong>dvh</strong> (Dynamic Viewport)
      <!-- 설명 -->
      <div class="vu-desc">현재 상태에 따라 동적으로 변경 (권장)</div>
    </div>
  </div>
  <!-- 코드 예시 박스 -->
  <div class="vu-code">
    <code>/* 문제: 모바일에서 100vh가 주소창 포함 */
.hero { height: 100vh; } /* 오버플로우 발생 */

/* 해결: dvh 사용 (fallback 포함) */
.hero {
  height: 100vh;   /* 폴백 */
  height: 100dvh;  /* 동적 뷰포트 높이 */
}</code>
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.vu-demo { font-family: system-ui, sans-serif; }
.vu-problem { display: flex; gap: 12px; align-items: center; justify-content: center; flex-wrap: wrap; margin-bottom: 16px; }
.vu-phone { width: 120px; border: 3px solid #374151; border-radius: 14px; overflow: hidden; background: #f8fafc; }
.vu-address-bar { background: #e2e8f0; padding: 4px; text-align: center; font-size: 9px; color: #64748b; font-weight: 600; }
.vu-viewport { height: 140px; position: relative; overflow: hidden; }
.vu-100vh { height: 160px; background: linear-gradient(to bottom, #bfdbfe, #3b82f6); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; }
.vu-100vh span { font-size: 10px; font-weight: 700; color: white; }
.vu-overflow { background: #ef4444; padding: 2px 6px; border-radius: 4px; font-size: 8px; }
.vu-phone.fixed .vu-viewport { overflow: hidden; }
.vu-100dvh { height: 140px; background: linear-gradient(to bottom, #bbf7d0, #22c55e); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; }
.vu-100dvh span { font-size: 10px; font-weight: 700; color: white; }
.vu-ok { background: #166534; padding: 2px 6px; border-radius: 4px; font-size: 8px; }
.vu-arrow { font-size: 24px; color: #94a3b8; }
.vu-units { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.vu-unit { padding: 8px 12px; background: #f1f5f9; border-radius: 6px; font-size: 12px; border-left: 3px solid #cbd5e1; }
.vu-unit.active { border-left-color: #22c55e; background: #f0fdf4; }
.vu-unit strong { color: #1e293b; }
.vu-desc { font-size: 11px; color: #64748b; margin-top: 2px; }
.vu-code { background: #1e293b; border-radius: 8px; padding: 14px; }
.vu-code code { font-size: 11px; color: #e2e8f0; white-space: pre; line-height: 1.5; display: block; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 데모의 핵심은 「고정 높이 + `overflow: hidden`」 상자 안에 그보다 큰 자식과 같은 자식을 넣어 비교하는 것이다.
- 160px 과 140px 의 차이가 「주소창 때문에 넘친 만큼」을 흉내 낸다 — 실제 `vh` · `dvh` 계산값은 아니다.
- 두 콘텐츠 상자는 모두 `flex-direction: column` 과 두 축 가운데 정렬로 라벨과 뱃지를 세로 한가운데에 쌓는다.
- `active` 클래스 하나로 권장 단위 `dvh` 만 강조한다.
- 코드 상자는 `white-space: pre` 로 폴백 두 줄의 순서와 들여쓰기를 그대로 보여 준다 — 이 순서(옛 값 먼저)가 이 주제의 실제 해법이다.
- `.vu-phone.fixed .vu-viewport` 의 `overflow: hidden` 은 이미 `.vu-viewport` 에 있는 값의 되풀이다. (원본에 근거 없음 — 추론)

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
