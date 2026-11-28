# css/visual/12 — scroll-snap-stop — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 카드 2 에서 멈춘다 — 건너뛰지 못한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
카드 1 에서 아무리 세게 밀어도 바로 다음인 카드 2 에서 멈춘다.
카드 3 으로 곧장 넘어가지 않는다. (코드에서 읽은 것 — 렌더 실측 아님)

**왜 그런가**
모든 카드에 `scroll-snap-stop: always` 가 있어 각 스냅 포인트가 「반드시 서는 정거장」이다.
카드 너비가 컨테이너와 같아 다음 스냅 포인트가 곧 다음 카드다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 2. 중간 카드를 건너뛸 수도 있다 — 칸 수는 정해지지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
세게 밀면 카드 2 를 지나쳐 카드 3 에서 멈출 수 있다.
다만 「반드시 건너뛴다」는 아니다 — 몇 칸을 가는지는 미는 세기와 브라우저에 달려 있다.

**왜 그런가**
`normal` 은 건너뛰기를 허용하는 값일 뿐 건너뛰기를 강제하지 않는다.
근거: 2-summary 「동작 방식 (2)」 · 「구현 세부사항 대 언어 보장」.

### 3. `normal` 처럼 움직인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
빠르게 밀면 스냅 포인트를 건너뛸 수 있다.

**왜 그런가**
`scroll-snap-stop` 의 기본값이 `normal` 이다.
근거: 2-summary 「문법 — 형태와 규칙」의 성질 표.

### 4. 빨리 훑는 목록이 더 흔하고, 하나씩 강제하면 답답하기 때문이다

갤러리나 상품 목록은 사용자가 여러 장을 휙휙 넘겨 원하는 곳으로 가야 한다.
늘 한 칸씩 멈추면 끝까지 가는 데 여러 번 밀어야 해 답답하다.
반대로 튜토리얼 · 이야기형 캐러셀처럼 한 장도 놓치면 안 되는 곳에서만 `always` 로 막으면 된다.
근거: 2-summary 「어디서 틀리나 4」 · 「언제 쓰고 언제 안 쓰나」. (답답함 부분은 원본에 근거 없음 — 추론)

### 5. 막히지 않는다 — 상속되지 않는다

`scroll-snap-stop` 은 상속되지 않는 속성이다.
컨테이너에 쓴 값은 자식 카드에 전해지지 않아 카드들은 기본값 `normal` 그대로다.
카드 선택자에 달아야 한다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 1」.

### 6. 아무 일도 일어나지 않는다

스냅 컨테이너(`scroll-snap-type`)와 스냅 포인트(`scroll-snap-align`)가 없으면 멈출 정거장 자체가 없다.
`scroll-snap-stop` 은 「정거장을 지나칠 수 있나」만 정하므로, 정거장이 없으면 할 일이 없다.
스크롤은 평범한 자유 스크롤로 남는다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 7. `mandatory` 는 「어디에 멈추나」, `always` 는 「지나칠 수 있나」

- `mandatory` — 스크롤이 끝나면 반드시 어떤 스냅 포인트에 맞춰지게 한다. 컨테이너에 단다.
- `always` — 스크롤 도중 그 스냅 포인트를 건너뛰지 못하게 한다. 아이템에 단다.

`mandatory` 만 있으면 끝은 반드시 스냅 포인트지만, 세게 밀면 어느 먼 포인트에서 끝날 수 있다.
`always` 를 더하면 그 끝이 「바로 다음 포인트」로 묶인다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 8. 넘침을 만들고, 「한 칸 = 한 장」이 되게 한다

- `flex-shrink: 0` — flex 가 카드를 줄여 컨테이너 안에 욱여넣지 못하게 한다. 그래서 가로 넘침과 스크롤이 생긴다.
- `min-width` = 컨테이너 너비 — 창에 카드가 한 장만 보이고, 이웃 스냅 포인트 사이가 정확히 카드 한 장이 된다.

이 둘이 있어야 `always` 의 「한 포인트씩 멈춤」이 사용자 눈에 「한 번 밀면 다음 한 장」으로 보인다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

## 실습 정답

### 실습 1. 한 장씩만 넘어가는 가로 캐러셀

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 카드들을 가로 한 줄로 | `.snap-container { display: flex; }` |
| 2. 넘친 부분을 가로 스크롤로 | `.snap-container { overflow-x: auto; }` |
| 3. 카드가 줄지 않고 컨테이너 너비만큼 | `.snap-item { flex-shrink: 0; min-width: 180px; }` |
| 4. 가로 축 강제 스냅 | `.snap-container { scroll-snap-type: x mandatory; }` |
| 5. 카드 시작 가장자리가 스냅 포인트 | `.snap-item { scroll-snap-align: start; }` |
| 6. 빠른 스와이프에도 건너뛰기 금지 | `.snap-item { scroll-snap-stop: always; }` |
| 7. 숫자 가운데 놓기 | `.snap-item { display: flex; align-items: center; justify-content: center; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/visual/reference/scroll-snap-stop.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 언어: 한국어 -->
<head>
  <meta charset="utf-8">
  <!-- 문자 인코딩: UTF-8 -->
  <title>scroll-snap-stop - 빠르게 스크롤할 때 스냅 포인트를 건너뛸 수 있는지 설정합니다</title>
  <!--
    [시각 효과] scroll-snap-stop
    설명: 빠르게 스크롤할 때 스냅 포인트를 건너뛸 수 있는지 설정합니다
    구문: scroll-snap-stop: normal | always
    팁: always는 빠른 스와이프에서도 각 아이템을 하나씩 보여줌. 중요한 콘텐츠를 놓치지 않게 할 때 유용.
  -->
  <style>
    /* .snap-container: 가로 스냅 컨테이너 */
    .snap-container {
      scroll-snap-type: x mandatory;              /* 가로 강제 스냅 */
      display: flex;                              /* 가로 배치 */
      overflow-x: auto;                           /* 가로 스크롤 */
      border-radius: 12px;                        /* 모서리 둥글게 */
      width: 180px;                               /* 너비 180px */
      margin: 20px auto;                          /* 위아래 20px, 가로 중앙 */
    }
    /* .snap-item: always로 건너뛰기 차단된 스냅 카드 */
    .snap-item {
      scroll-snap-align: start;                   /* 시작점 스냅 정렬 */
      scroll-snap-stop: always;                   /* 빠른 스와이프에도 한 칸씩만 이동 - 중요 콘텐츠 놓침 방지 (튜토리얼/이야기형 캐러셀에 유용) */
      min-width: 180px;                           /* 최소 너비 180px - 컨테이너와 동일 */
      height: 100px;                              /* 높이 100px */
      display: flex;                              /* 플렉스 */
      align-items: center;                        /* 세로 중앙 */
      justify-content: center;                    /* 가로 중앙 */
      color: white;                               /* 흰 글자 */
      font-size: 32px;                            /* 큰 숫자 32px */
      font-weight: bold;                          /* 굵게 */
      flex-shrink: 0;                             /* 축소 방지 */
    }
  </style>
</head>
<body>
  <!-- scroll-snap-stop: always 데모 -->
  <div class="snap-container">
    <!-- 가로 스냅 컨테이너 -->
    <div class="snap-item" style="background:#ef4444">1</div>
    <!-- 빨강 카드 1 -->
    <div class="snap-item" style="background:#f59e0b">2</div>
    <!-- 주황 카드 2 -->
    <div class="snap-item" style="background:#10b981">3</div>
    <!-- 초록 카드 3 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.snap-container { scroll-snap-type: x mandatory; display: flex; overflow-x: auto; border-radius: 12px; width: 180px; margin: 20px auto; }
.snap-item { scroll-snap-align: start; scroll-snap-stop: always; min-width: 180px; height: 100px; display: flex; align-items: center; justify-content: center; color: white; font-size: 32px; font-weight: bold; flex-shrink: 0; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 핵심 한 줄은 `.snap-item` 의 `scroll-snap-stop: always` 다 — 컨테이너가 아니라 카드에 단다(상속되지 않는다).
- `scroll-snap-type: x mandatory` 와 `scroll-snap-align: start` 가 정거장을 만들어야 `always` 가 의미를 가진다.
- `flex-shrink: 0` 이 빠지면 카드가 줄어 넘침이 사라지고, 스크롤도 스냅도 없어진다.
- `min-width` 를 컨테이너 너비(180px)와 맞춰 「한 칸 이동 = 한 장 넘김」이 되게 한다.
- `always` 를 `normal` 로 바꿔 세게 밀어 보면, 중간 카드를 건너뛸 수 있는 차이를 직접 견줄 수 있다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
