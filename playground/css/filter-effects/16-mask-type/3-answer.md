# css/filter-effects/16 — mask-type — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 가운데에 원 모양 구멍이 뚫린 사각형

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
사각형 대부분은 붉게 보이고, 가운데 원 자리만 가려져 구멍처럼 보인다.

**왜 그런가**
`mask-type` 을 쓰지 않았으므로 기본값 `luminance` 로 읽는다.
흰 사각형 자리는 밝아서 보이고, 검은 원 자리는 어두워서 가려진다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 구멍이 사라지고 온전한 사각형이 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
붉은 사각형 전체가 구멍 없이 보인다.

**왜 그런가**
`alpha` 모드는 색을 무시하고 불투명도만 본다.
흰 사각형도 검은 원도 불투명하게 칠해져 있으므로 모든 자리가 「보임」이다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」.

### 3. 그 사이 — 일부만 비친다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
붉은 사각형이 완전히 보이지도, 완전히 가려지지도 않고 반쯤 흐리게 비친다.

**왜 그런가**
기본값 `luminance` 에서 회색은 흰색과 검은색 사이의 밝기다.
그래서 「그 사이만큼 비침」이 된다.
정확히 얼마나 비치는지는 이 문서가 다루지 않는다.
근거: 2-summary 「동작 방식 (1)」의 그림.

### 4. 아무것도 달라지지 않는다

`mask-type` 은 SVG `<mask>` 요소 전용 속성이라 일반 `div` 에는 효과가 없다.
근거: 2-summary 「어디서 틀리나 1」 · 「문법 — 형태와 규칙」의 적용 대상.

### 5. 기본값 `luminance` 로 동작한다

`mask-type` 은 상속되지 않는다.
`<svg>` 에 쓴 값은 안쪽 `<mask>` 로 내려가지 않으므로, `<mask>` 는 자기 값인 기본값 `luminance` 를 쓴다.
근거: 2-summary 「문법 — 형태와 규칙」의 규칙 불릿.

### 6. 색마다 밝기가 달라 `luminance` 로는 얼룩지기 때문이다

`luminance` 는 색의 밝기로 보일 정도를 정한다.
여러 색이 섞인 아이콘은 색마다 밝기가 달라 어떤 부분은 많이, 어떤 부분은 적게 비친다.
`alpha` 는 색을 무시하고 칠한 곳을 모두 「보임」으로 읽으므로 모양만 깨끗하게 따낸다.
근거: 2-summary 「동작 방식 (2)」 · 「언제 쓰고 언제 안 쓰나」.

### 7. SVG 맥락 밖에서는 보여 줄 효과가 없기 때문이다

`mask-type` 은 SVG `<mask>` 요소에서만 동작한다.
일반 HTML 박스에 걸어 봐야 달라지는 것이 없으므로, 예제는 안내 문장으로 대신한다.
근거: 2-summary 「어디서 틀리나 1」.

### 8. 둘 다 알파 / 휘도를 고르지만 적용 대상이 다르다

두 속성 모두 마스크를 알파로 읽을지 휘도로 읽을지 고른다.
`mask-mode` 는 CSS 쪽 마스크에, `mask-type` 은 SVG `<mask>` 요소에 쓴다.
근거: 2-summary 「어디서 틀리나 3」 · 「핵심 문장 5」.

## 실습 정답

### 실습 1. `mask-type` 안내 박스 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| HTML5 · 한국어 · UTF-8 | `<!DOCTYPE html>` · `<html lang="ko">` · `<meta charset="utf-8">` |
| 탭 제목 | `<title>mask-type - …</title>` |
| `info` 클래스 `div` 하나 | `<div class="info">` |
| `<mask>` 를 글자 그대로 | `&lt;mask&gt;` |
| 글자 가운데 정렬 | `.info { text-align: center; }` |
| 가로 가운데 + 위아래 여백 | `.info { margin: 30px auto; }` (`width` 와 함께) |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/filter-effects/reference/mask-type.html`

```html
<!DOCTYPE html>
<!-- 문서 타입을 HTML5로 선언 -->
<html lang="ko">
  <!-- 문서 언어를 한국어로 설정 -->
  <head>
    <meta charset="utf-8">
    <!-- 문자 인코딩을 UTF-8로 지정 -->
    <title>mask-type - SVG <mask> 요소의 마스크 타입을 설정합니다</title>
    <!-- 브라우저 탭 제목 -->
    <!--
      [필터 & 효과] mask-type
      설명: SVG <mask> 요소의 마스크 타입을 설정합니다
      구문: mask-type: luminance | alpha
      팁: SVG <mask> 요소 전용 속성. CSS mask-mode와 유사하지만 SVG 컨텍스트에서만 사용.
    -->
    <style>
      /* .info: 안내문 박스 (mask-type은 SVG 컨텍스트에서만 동작하므로 일반 데모 대신 안내) */
      .info {
        background: #f8fafc;                        /* 매우 옅은 회색 배경 */
        border: 2px solid #e2e8f0;                  /* 옅은 회색 테두리 */
        color: #475569;                             /* 진회색 텍스트 */
        padding: 24px;                              /* 안쪽 여백 24px */
        text-align: center;                         /* 텍스트 가운데 정렬 */
        border-radius: 8px;                         /* 모서리 둥글게 8px */
        width: 260px;                               /* 너비 260px */
        margin: 30px auto;                          /* 상하 30px / 수평 중앙 */
        font-size: 14px;                            /* 글자 크기 14px */
      }
      /* 정리: CSS의 mask-mode와 SVG의 mask-type 모두 알파/휘도 모드를 선택하지만 적용 대상이 다름 */
    </style>
  </head>
  <body>
    <!-- SVG <mask> 전용 속성임을 알리는 안내 박스 -->
    <div class="info">SVG &lt;mask&gt; 요소에 적용되는 속성입니다</div>
  </body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.info { background: #f8fafc; border: 2px solid #e2e8f0; color: #475569; padding: 24px; text-align: center; border-radius: 8px; width: 260px; margin: 30px auto; font-size: 14px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- 본문에서 `<mask>` 를 그대로 쓰면 브라우저가 태그로 해석한다 — `&lt;` · `&gt;` 로 바꿔 써야 글자로 보인다.
- `margin` 의 좌우 `auto` 는 너비가 정해진 블록 박스를 가로 가운데로 보낸다 — 그래서 `width` 가 함께 있어야 한다.
- `text-align: center` 는 박스 자체가 아니라 박스 **안의 글자**를 가운데로 놓는다.
- 이 정답 코드에는 `mask-type` 선언이 없다 — 이 속성은 SVG `<mask>` 요소에서만 효과가 있어 일반 박스로는 보여 줄 수 없기 때문이다.
- 실제 효과를 보려면 2-summary 「동작 방식 (3)」처럼 `<svg>` 안의 `<mask>` 에 써야 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
