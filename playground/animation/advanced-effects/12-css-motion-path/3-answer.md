# animation/advanced-effects/12 — CSS Motion Path — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. ∞ 가 아니라 위아래 두 곡선이 양 끝에서 만나는 고리다 — 위쪽은 y=40 까지만 오른다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`M 30,100` 에서 출발해 첫 `C` 로 위로 부푼 곡선을 그리며 (270,100) 에 닿는다.
둘째 `C` 는 아래로 부푼 곡선을 그리며 (30,100) 으로 돌아온다.
두 곡선은 양 끝 (30,100) · (270,100) 에서만 만나므로 가운데에서 엇갈리지 않는다.
모양은 가로로 긴 타원에 가까운 닫힌 고리다 (코드에서 읽은 것 — 렌더 실측 아님).
위쪽 곡선의 꼭대기는 (30+90+810+270)÷8 = 150, (100+60+60+100)÷8 = 40 으로 (150,40) 이고, y=20 까지는 가지 않는다.

**왜 그런가**
`C` 의 앞 두 점은 제어점이라 곡선을 끌어당길 뿐 곡선이 지나가지 않는다.
원본 주석의 「∞ 모양」은 경로 문자열과 맞지 않는다 — 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 5」(원본에 근거 없음 — 추론).

### 2. 1초에는 위쪽 꼭대기 (150,40), 2초에는 오른쪽 끝 (270,100)

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
4초에 0% → 100% 를 `linear` 로 가므로 1초는 25%, 2초는 50% 다.
위쪽 곡선과 아래쪽 곡선은 y=100 을 축으로 뒤집은 꼴이라 길이가 같다 — 50% 는 위쪽 곡선의 끝인 (270,100) 이다.
위쪽 곡선은 좌우 대칭이라 그 절반인 25% 는 한가운데 꼭대기 (150,40) 이다.

**왜 그런가**
`offset-distance` 의 % 는 경로 전체 길이의 비율이고, `linear` 면 시간에 비례해 거리가 는다 — 2-summary 「동작 방식 (2)」.

### 3. 위쪽 곡선만 달린 뒤 오른쪽 끝에서 왼쪽 끝으로 순간이동한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
한 주기 4초 동안 로켓은 0% (30,100) 에서 50% (270,100) 까지, 곧 위쪽 곡선만 지나간다.
주기가 끝나면 `offset-distance` 가 0% 로 돌아가므로 로켓은 (270,100) 에서 (30,100) 으로 단번에 건너뛴다.
아래쪽 곡선은 지나가지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
키프레임의 끝 값 50% 는 경로의 끝점이 아니라 오른쪽 끝이고, 이 점은 출발점과 다르다.
반복은 마지막 값에서 첫 값으로 바로 넘어가므로 이음매에서 튄다 — 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 4. 위치는 `offset-path` 가 정하므로 시작 기준을 무대 원점에 두려는 것이다

로켓의 실제 위치는 경로와 `offset-distance` 가 정한다.
`top: 0; left: 0` 은 요소의 기준을 무대(`position: relative`)의 왼쪽 위 모서리에 두어, 경로 좌표의 원점이 무대 원점과 같아지게 한다.
그래야 SVG 가이드의 좌표 (0,0) 과도 맞는다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」(원본 주석 「offset-path가 좌표를 결정하므로 0」).

### 5. 문자열이 다르면 로켓이 점선을 벗어나 엉뚱한 곳을 지나간다

SVG 의 `d` 는 눈에 보이는 선만 그리고, 로켓의 실제 궤적은 `path()` 만 따른다.
두 문자열이 다르면 화면에는 선이 하나 있는데 로켓은 다른 궤적을 달려 가이드와 어긋난다.
같은 문자열이면 같은 좌표계(1 단위 = 1px)에서 같은 곡선이 되어 정확히 겹친다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 1」(원본 팁).

### 6. 겹치지 않는다 — 점선만 두 배로 커지고 로켓은 원래 크기의 고리를 돈다

SVG 는 viewBox `0 0 300 200` 을 600×400 에 맞춰 늘려 그리므로 점선 고리가 두 배로 커진다.
`path()` 의 좌표는 px 그대로라 로켓은 (30,100)~(270,100) 크기의 고리를 무대 왼쪽 위 쪽에서 돈다.
두 선이 겹치는 것은 무대 크기가 viewBox 와 같을 때뿐이다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 2」.

### 7. 100% 에서 0% 로 돌아갈 때 끝점에서 출발점으로 순간이동한다

열린 경로에서는 100% 지점(끝점)과 0% 지점(출발점)이 다른 곳이다.
`infinite` 는 매 주기 끝에서 마지막 값에서 첫 값으로 바로 넘어가므로, 로켓이 끝점에서 사라져 출발점에 다시 나타나는 것처럼 튄다.
원본은 끝점을 출발점 (30,100) 으로 닫아 0% 와 100% 가 같은 점이 되게 해서 이음매를 없앴다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 8. 경로 위를 달리는 빠르기가 바뀐다 — 궤적은 그대로다

timing function 은 다른 속성에서처럼 `offset-distance` 의 진행 비율에 적용된다.
`ease` 면 매 바퀴 출발점 부근에서 천천히 출발해 중간에 빨라졌다가 다시 출발점 부근에서 느려진다.
지나가는 길(경로)은 `offset-path` 가 정하므로 바뀌지 않고, 같은 시각에 경로의 어디쯤 있는지만 달라진다.
`linear` 일 때만 1초 = 25% 같은 비례가 성립한다.
근거: 2-summary 「동작 방식 (2)」.

## 실습 정답

### 실습 1. 점선 고리를 따라 도는 로켓 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 무대가 절대 위치 기준점 · 밖은 숨김 | `.motion-path-demo { position: relative; overflow: hidden; }` |
| 2. SVG 가 무대를 꽉 채움 | `.motion-path-svg { position: absolute; inset: 0; width: 100%; height: 100%; }` |
| 3. 로켓 절대 배치 · 시작 기준 왼쪽 위 | `.motion-element { position: absolute; top: 0; left: 0; }` |
| 4. 이동 경로 = SVG `d` | `offset-path: path('M 30,100 C 30,20 270,20 270,100 C 270,180 30,180 30,100');` |
| 5. 진행 방향 회전 | `offset-rotate: auto;` |
| 6. 위치 0% → 100% | `@keyframes followPath { from { offset-distance: 0%; } to { offset-distance: 100%; } }` |
| 7. 4초 등속 무한 반복 | `animation: followPath 4s linear infinite;` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`animation/advanced-effects/reference/css-motion-path.html`

```html
<!-- HTML5 문서 선언 -->
<!DOCTYPE html>
<!-- 한국어 페이지 -->
<html lang="ko">
<head>
  <!-- 문자 인코딩 -->
  <meta charset="utf-8">
  <!-- 브라우저 탭 제목 -->
  <title>CSS Motion Path - offset-path로 정의한 SVG 경로를 따라 요소가 이동하는 CSS 모션 패스. offset-distance를 애니메이션한다.</title>
  <!--
    [고급 이펙트] CSS Motion Path
    설명: offset-path로 정의한 SVG 경로를 따라 요소가 이동하는 CSS 모션 패스. offset-distance를 애니메이션한다.

    팁: offset-path의 path()와 SVG의 d 속성을 동일하게 맞추면 가이드라인과 정확히 일치한다. offset-rotate: auto로 진행 방향에 맞게 회전.
  -->
  <style>
    /* .motion-path-demo: 경로와 이동 요소를 담는 무대(부모) */
    .motion-path-demo {
      position: relative;            /* SVG/요소 absolute 기준점 */
      width: 300px;                  /* 무대 너비 */
      height: 200px;                 /* 무대 높이 */
      background: #f8fafc;           /* 밝은 회색 배경 */
      border-radius: 8px;            /* 모서리 둥글게 */
      overflow: hidden;              /* 경로 밖으로 나가는 부분 숨김 */
    }
    /* .motion-path-svg: 경로 가이드를 그리는 SVG (점선으로 표시) */
    .motion-path-svg {
      position: absolute;            /* 무대에 겹쳐 배치 */
      inset: 0;                      /* 상하좌우 0 */
      width: 100%;                   /* 무대 가득 채움 */
      height: 100%;                  /* 무대 가득 채움 */
    }
    /* .motion-element: 경로를 따라 이동하는 이모지 요소 */
    .motion-element {
      position: absolute;            /* 무대 기준 절대 위치 */
      top: 0;                        /* offset-path가 좌표를 결정하므로 0 */
      left: 0;                       /* offset-path가 좌표를 결정하므로 0 */
      font-size: 24px;               /* 이모지 크기 */
      offset-path: path('M 30,100 C 30,20 270,20 270,100 C 270,180 30,180 30,100');  /* 이동 경로: 가로로 누운 무한대(∞) 모양 */
      offset-rotate: auto;           /* 진행 방향에 맞춰 자동 회전 (자연스러움) */
      animation: followPath 4s linear infinite;  /* followPath 키프레임을 4초 등속으로 무한 반복 */
    }
    /* @keyframes followPath: offset-distance를 0%→100%로 증가시켜 경로 위를 진행 */
    @keyframes followPath {
      /* 시작: 경로의 0% 지점 */
      from {
        offset-distance: 0%;          /* 경로의 시작점 */
      }
      /* 끝: 경로의 100% 지점 (한 바퀴 완료) */
      to {
        offset-distance: 100%;        /* 경로의 끝점 (시작과 동일하게 닫힌 경로) */
      }
    }
  </style>
</head>
<body>
  <!-- 모션 패스 데모 컨테이너 -->
  <div class="motion-path-demo">
    <!-- 점선 가이드 경로 SVG (실제 이동과 동일한 path) -->
    <svg class="motion-path-svg" viewBox="0 0 300 200">
      <path d="M 30,100 C 30,20 270,20 270,100 C 270,180 30,180 30,100" fill="none" stroke="#334155" stroke-width="1" stroke-dasharray="4 4" />
    </svg>
    <!-- 경로를 따라 움직이는 로켓 이모지 -->
    <div class="motion-element">🚀</div>
  </div>
</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.motion-path-demo {
  position: relative;
  width: 300px;
  height: 200px;
  background: #f8fafc;
  border-radius: 8px;
  overflow: hidden;
}
.motion-path-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.motion-element {
  position: absolute;
  top: 0;
  left: 0;
  font-size: 24px;
  offset-path: path('M 30,100 C 30,20 270,20 270,100 C 270,180 30,180 30,100');
  offset-rotate: auto;
  animation: followPath 4s linear infinite;
}
@keyframes followPath {
  from { offset-distance: 0%; }
  to { offset-distance: 100%; }
}
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 애니메이션하는 값은 `offset-distance` 하나이고, 궤적은 `offset-path` 가 맡는다.
- `path()` 문자열을 SVG `d` 에서 그대로 복사해야 점선과 로켓이 겹친다.
- viewBox `0 0 300 200` 과 무대 300×200 이 같아서 SVG 1 단위가 1px 이 되고, `path()` 의 px 좌표와 맞는다.
- 경로가 (30,100) 에서 시작해 (30,100) 에서 끝나는 닫힌 경로라 `infinite` 반복의 이음매에서 튀지 않는다.
- `linear` 이므로 로켓은 경로 위를 같은 빠르기로 달린다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
