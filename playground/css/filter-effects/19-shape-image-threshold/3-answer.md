# css/filter-effects/19 — shape-image-threshold — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 좌상단 삼각형이 도형이 되고, 글은 아래로 갈수록 왼쪽에서 시작한다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
도형은 우상단과 좌하단을 잇는 대각선의 좌상단 쪽 직각삼각형이다.
글 줄은 맨 위에서는 상자 오른쪽 끝 가까이에서 시작하고, 아래 줄로 갈수록 시작 위치가 왼쪽으로 옮겨 온다(코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`135deg` 그라데이션은 좌상단 알파 1 에서 우하단 알파 0 으로 고르게 줄어든다.
알파가 같은 점은 진행 방향에 수직인 선 위에 있으므로, 정사각형에서 알파 0.5 인 선은 우상단–좌하단 대각선이다.
임계값 0.5 면 그 선보다 진한 좌상단 쪽만 도형이 된다.
근거: 2-summary 「동작 방식 (2)」.

### 2. 0.0 이면 거의 정사각형 전체, 1.0 이면 거의 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`0.0` 이면 완전 투명한 우하단 끝 근처를 빼고 거의 정사각형 전체가 도형이 되어, 글이 사각형 float 처럼 상자 오른쪽에서 줄을 시작한다.
`1.0` 이면 완전 불투명한 좌상단 끝점 근처만 남아 도형이 거의 없다.
그때 글은 상자 자리를 거의 피하지 않으므로 보이는 cyan 배경 위로 겹쳐 지나간다(코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
임계값이 낮을수록 더 투명한 픽셀까지 도형에 들어가고, 높을수록 진하게 불투명한 픽셀만 남는다.
보이는 `background` 는 도형과 따로이므로 도형이 작아져도 그대로 그려진다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 3. 윤곽은 달라지지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
시작색의 알파가 여전히 1 이므로 1번과 같은 좌상단 삼각형이 도형이 된다.

**왜 그런가**
도형을 정할 때 브라우저는 색이 아니라 알파만 본다.
`rgba` 의 네 번째 숫자가 그대로면 윤곽도 그대로다.
근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (1)」.

### 4. `shape-outside` 의 그라데이션은 화면에 그려지지 않기 때문이다

`shape-outside` 의 그라데이션은 윤곽 계산에만 쓰이고 눈에 보이지 않는다.
도형이 어디쯤인지 사람이 알아보게 하려고 같은 방향의 그라데이션을 `background` 에 따로 칠한다.
둘의 방향이 다르면 보이는 모양과 글이 피해 가는 윤곽이 어긋난다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 5. 아무것도 달라지지 않는다

알파가 0 인 픽셀은 0.2 · 0.8 어느 쪽에도 못 미치고, 알파가 1 인 픽셀은 둘 다 넘는다.
경계 사이에 끼는 중간 알파 픽셀이 없으므로 도형이 같다.
원본 팁이 「그라디언트나 반투명 이미지」를 쓸 때의 속성이라고 한 까닭이다.
근거: 2-summary 「어디서 틀리나 1」.

### 6. 효과가 없다

`shape-image-threshold` 는 `shape-outside` 의 도형을 다듬을 뿐이고, `shape-outside` 는 float 요소에서 동작한다.
float 이 없으면 글이 도형을 감싸지 않으므로 임계값이 보이는 결과를 바꾸지 못한다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 2」.

### 7. 「이상」이면 사각형 전체, 「초과」면 그림 부분만 도형이다

「이상」으로 읽으면 알파 0 인 투명 배경도 0.0 이상이라 도형에 들어가, 이미지의 사각형 전체가 도형이 된다.
「초과」로 읽으면 알파 0 인 픽셀은 빠지고 조금이라도 불투명한 그림 부분만 도형이 된다.
원본은 「이상」으로 적었지만, 명세는 「초과」로 적는다고 기억한다 (확인 필요).
근거: 2-summary 「어디서 틀리나 3」 · 「구현 세부사항 대 언어 보장」.

### 8. `transition` 은 되고, 부모에 준 값은 닿지 않는다

애니메이션 가능한 숫자 속성이라 `transition` 이 0.0 에서 0.5 까지 중간값을 거치며 바꿀 수 있다.
그러면 글이 피해 가는 윤곽이 점점 줄어든다 (원본에 근거 없음 — 추론).
상속되지 않으므로 `.wrap` 에 준 값은 `.shape` 에 넘어가지 않는다 — `.shape` 에 직접 줘야 한다.
근거: 2-summary 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 그라데이션의 진한 쪽만 글이 피해 가는 float 도형 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `.wrap` 안에 `.shape` 와 문단을 차례로 둔다 | `<div class="wrap">` 안의 `<div class="shape">` · `<p>` |
| 왼쪽에 띄워 문단이 오른쪽으로 흐르게 한다 | `.shape { float: left; }` |
| 135deg 알파 그라데이션을 도형으로 쓴다 | `.shape { shape-outside: linear-gradient(135deg, rgba(0,0,0,1), rgba(0,0,0,0)); }` |
| 알파 0.5 를 경계로 도형을 자른다 | `.shape { shape-image-threshold: 0.5; }` |
| 보이는 색은 따로 칠한다 | `.shape { background: linear-gradient(135deg, …); }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/filter-effects/reference/shape-image-threshold.html`

```html
<!DOCTYPE html>
<!-- 문서 타입을 HTML5로 선언 -->
<html lang="ko">
  <!-- 문서 언어를 한국어로 설정 -->
  <head>
    <meta charset="utf-8">
    <!-- 문자 인코딩을 UTF-8로 지정 -->
    <title>shape-image-threshold - 이미지에서 도형을 추출할 때 알파 채널의 임계값을 설정합니다</title>
    <!-- 브라우저 탭 제목 -->
    <!--
      [필터 & 효과] shape-image-threshold
      설명: 이미지에서 도형을 추출할 때 알파 채널의 임계값을 설정합니다
      구문: shape-image-threshold: <number>
      팁: 그라디언트나 반투명 이미지를 shape-outside로 사용할 때, 어느 정도의 투명도까지 도형에 포함할지 결정.
    -->
    <style>
      /* .wrap: shape-outside가 동작할 텍스트 흐름 컨테이너 */
      .wrap {
        max-width: 300px;                           /* 최대 너비 300px */
        margin: 20px auto;                          /* 상하 20px / 수평 중앙 */
        font-size: 14px;                            /* 글자 크기 14px */
        line-height: 1.6;                           /* 줄 간격 1.6배 */
        color: #374151;                             /* 진회색 텍스트 */
      }
      /* .shape: 그라데이션 이미지를 도형으로 사용하는 float 요소 */
      .shape {
        float: left;                                /* 왼쪽 floating (shape-outside가 동작하려면 float 필수) */
        width: 100px;                               /* 너비 100px */
        height: 100px;                              /* 높이 100px */
        shape-outside: linear-gradient(135deg, rgba(0,0,0,1), rgba(0,0,0,0)); /* 그라데이션 알파를 도형으로 사용 (좌상단 불투명→우하단 투명) */
        shape-image-threshold: 0.5;                 /* 알파 0.5 이상인 픽셀만 도형에 포함 (0.5 미만은 빈 공간 취급) */
        background: linear-gradient(135deg, #06b6d4, transparent); /* 시각적 표현용 동일 그라데이션 (실제로 보이는 색) */
        margin-right: 12px;                         /* 텍스트와의 간격 12px */
        border-radius: 8px;                         /* 모서리 둥글게 8px */
      }
    </style>
  </head>
  <body>
    <!-- 그라데이션 도형 주위로 텍스트가 감싸는 레이아웃 -->
    <div class="wrap">
      <!-- 알파 임계값 0.5로 추출된 도형 -->
      <div class="shape"></div>
      <!-- 도형 주위로 흐르는 더미 텍스트 -->
      <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore.</p>
    </div>
  </body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.wrap { max-width: 300px; margin: 20px auto; font-size: 14px; line-height: 1.6; color: #374151; }
.shape { float: left; width: 100px; height: 100px; shape-outside: linear-gradient(135deg, rgba(0,0,0,1), rgba(0,0,0,0)); shape-image-threshold: 0.5; background: linear-gradient(135deg, #06b6d4, transparent); margin-right: 12px; border-radius: 8px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `float: left` 가 있어야 `shape-outside` 가 동작하고, 그래야 임계값도 효과를 낸다.
- `shape-outside` 의 그라데이션은 색이 아니라 알파(1 → 0)로 도형을 정한다.
- `shape-image-threshold: 0.5` 로 알파 0.5 선(우상단–좌하단 대각선)의 좌상단 쪽만 도형이 된다.
- `background` 의 그라데이션은 보이기 위한 것일 뿐이고, 방향을 `shape-outside` 와 맞춰야 보이는 모양과 윤곽이 어긋나지 않는다.
- 임계값을 낮추면 도형이 커지고 높이면 작아진다 — 0.0 · 1.0 으로 바꿔 보며 확인한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
