# css/units-values/18 — Named colors — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 글자색 · 그림자는 `.swatch.dark`, `font-weight` 는 `.swatch` 의 600

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
글자색은 `#1e293b`(어두운 색), 그림자는 없다(`none`).
`font-weight` 는 `.swatch` 의 `600` 이 그대로 남는다.

**왜 그런가**
이 칸은 `swatch` 와 `dark` 클래스를 모두 가져 두 규칙에 다 걸린다.
`.swatch.dark` 는 클래스 둘이라 `.swatch` 보다 구체적이어서, 둘 다 적은 `color` · `text-shadow` 는 `.swatch.dark` 가 이긴다.
`font-weight` 는 `.swatch.dark` 에 없으므로 덮이지 않는다.
근거: 2-summary 「동작 방식 (3)」.

### 2. 세 칸의 너비는 같다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
세 칸은 같은 너비로 가로에 나란히 놓이고, 칸 사이에만 간격이 있다.

**왜 그런가**
`.row` 가 `display: flex` 라 칸들이 가로로 놓인다.
세 칸 모두 `flex: 1` 이라 남는 너비를 같은 비율로 나눠 갖는다.
`gap` 은 칸 사이에만 간격을 둔다.
근거: 2-summary 「동작 방식 (4)」.

### 3. 인라인 스타일의 `coral` 이 이긴다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
배경은 `coral` 색이 된다.

**왜 그런가**
`style` 속성에 직접 적은 인라인 스타일은 클래스 선택자 규칙보다 우선한다.
그래서 `.swatch { background: gray; }` 는 이 칸에서 덮인다.
근거: 2-summary 「동작 방식 (2)」.

### 4. 매우 옅은 배경에서는 흰 글자가 읽히지 않기 때문이다

`papayawhip` 은 매우 옅은 색이라 흰 글자를 얹으면 글자가 배경에 묻힌다.
나머지 다섯 색은 진해서 흰 글자가 잘 보인다.
그래서 그 칸에만 `.swatch.dark` 를 걸어 어두운 글자로 바꾸고 그림자도 없앤다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 5. 값을 한 곳에 모아야 고치기 쉽고, 쓰임새가 드러나기 때문이다

이름을 여러 곳에 직접 쓰면 색을 바꿀 때 그 모든 곳을 고쳐야 한다.
토큰(변수) 한 곳에 두면 한 줄만 바꾸면 된다.
또 `tomato` 는 「무슨 색」만 말하고, `--color-accent` 같은 토큰은 「무엇에 쓰는 색」까지 말한다.
근거: 2-summary 「어디서 틀리나 1」 · 원본 팁.

### 6. 되지 않는다 — 미리 정의된 목록에서만 고른다

이름 색상은 CSS 가 미리 정의해 둔 이름의 목록이다.
`banana` 처럼 그럴듯한 단어라도 목록에 없으면 색이 되지 않는다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 3」.

### 7. 이름만으로는 안 된다 — 이름 하나는 고정된 색 하나다

이름으로 「조금 더 어둡게」를 줄 수는 없다.
다른 이름을 찾거나, 다른 색 표기로 바꿔야 한다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 4」.

### 8. 이름을 변수의 값으로 한 곳에 두고 `var()` 로 가져다 쓴다

`:root { --color-accent: coral; }` 처럼 이름 색상을 사용자 정의 속성의 값으로 넣는다.
쓰는 곳에서는 `background: var(--color-accent);` 로 가져온다.
색을 바꿀 때는 `:root` 의 한 줄만 고치면 된다.
근거: 2-summary 「문법 — 형태와 규칙」의 최소 예제 · 「용어 풀이」의 디자인 토큰.

## 실습 정답

### 실습 1. 이름 색상 견본판 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 바깥 상자 안에 줄 두 개 | `<div class="named-demo">` 안의 `<div class="row">` 두 개 |
| 2. 여섯 칸의 배경색 | 첫 줄 `tomato` · `cornflowerblue` · `mediumseagreen`, 둘째 줄 `slateblue` · `coral` · `papayawhip` |
| 3. 인라인 `style` 로 배경 | 각 `.swatch` 의 `style="background: …"` |
| 4. 칸 글자 = 색 이름 | 각 `<div class="swatch">` 의 내용 텍스트 |
| 5. 가로 배치 · 칸 사이 간격 | `.row { display: flex; gap: …; }` |
| 6. 같은 너비 | `.swatch { flex: 1; }` |
| 7. 줄 사이 간격 · 마지막 줄 여백 없음 | `.row { margin-bottom: … }` · `.row:last-child { margin-bottom: 0; }` |
| 8. 기본 흰 글자 · 그림자 | `.swatch { color: white; text-shadow: …; }` |
| 9. `papayawhip` 칸만 어두운 글자 | `class="swatch dark"` · `.swatch.dark { color: …; text-shadow: none; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/units-values/reference/named-colors.html`

```html
<!DOCTYPE html>                              <!-- HTML5 문서 타입 선언 -->
<html lang="ko">                              <!-- 문서 언어를 한국어로 지정 -->
<head>
<meta charset="utf-8">                       <!-- 문자 인코딩을 UTF-8로 설정 -->
<title>Named colors - CSS에서 이름으로 사용할 수 있는 148개의 미리 정의된 색상. red, blue, tomato, cornflowerblue 등</title>
<!--
  [CSS 단위 & 값] Named colors
  설명: CSS에서 이름으로 사용할 수 있는 148개의 미리 정의된 색상. red, blue, tomato, cornflowerblue 등
  구문: <color-name>
  팁: 프로토타이핑이나 학습용으로 편리하지만, 프로덕션에서는 디자인 토큰(변수)을 사용하는 것이 유지보수에 유리.
-->
<style>
/* .named-demo: 명명된 색상 시연 컨테이너 */
.named-demo {
  padding: 16px;                              /* 안쪽 여백 */
  background: #f1f5f9;                        /* 연한 배경 */
  border-radius: 8px;                         /* 모서리 둥글기 */
}

/* .row: 색상 행 */
.row {
  display: flex;                              /* 가로 정렬 */
  gap: 8px;                                   /* 자식 간 간격 */
  margin-bottom: 8px;                         /* 아래 간격 */
}

/* .row:last-child: 마지막 행은 아래 마진 제거 */
.row:last-child {
  margin-bottom: 0;                           /* 마지막 행 마진 제거 */
}

/* .swatch: 색상 스와치 공통 스타일 */
.swatch {
  flex: 1;                                    /* 동등 분배 */
  padding: 16px 8px;                          /* 안쪽 여백 */
  border-radius: 6px;                         /* 모서리 둥글기 */
  color: white;                               /* 흰 글자 (밝은 배경엔 .dark로 오버라이드) */
  font-weight: 600;                           /* 굵은 글자 */
  font-size: 13px;                            /* 글자 크기 */
  text-align: center;                         /* 가운데 정렬 */
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);     /* 그림자 */
}

/* .swatch.dark: 옅은 색상에는 어두운 글자 */
.swatch.dark {
  color: #1e293b;                             /* 어두운 글자색 */
  text-shadow: none;                          /* 그림자 제거 */
}
</style>
</head>
<body>
<div class="named-demo">                      <!-- 명명된 색상 시연 -->
  <div class="row">                           <!-- 첫 번째 행 -->
    <div class="swatch" style="background: tomato">tomato</div>                       <!-- 토마토 빨강 -->
    <div class="swatch" style="background: cornflowerblue">cornflowerblue</div>       <!-- 수레국화 파랑 -->
    <div class="swatch" style="background: mediumseagreen">mediumseagreen</div>       <!-- 중간 바다초록 -->
  </div>
  <div class="row">                           <!-- 두 번째 행 -->
    <div class="swatch" style="background: slateblue">slateblue</div>                 <!-- 슬레이트 파랑 -->
    <div class="swatch" style="background: coral">coral</div>                         <!-- 산호색 -->
    <div class="swatch dark" style="background: papayawhip">papayawhip</div>          <!-- 매우 옅은 색 → dark 텍스트 -->
  </div>
</div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.named-demo { padding: 16px; background: #f1f5f9; border-radius: 8px; }
.row { display: flex; gap: 8px; margin-bottom: 8px; }
.row:last-child { margin-bottom: 0; }
.swatch { flex: 1; padding: 16px 8px; border-radius: 6px; color: white; font-weight: 600; font-size: 13px; text-align: center; text-shadow: 0 1px 2px rgba(0,0,0,0.2); }
.swatch.dark { color: #1e293b; text-shadow: none; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 색은 칸마다 다르므로 공통 규칙이 아니라 인라인 `style` 에 이름 색상으로 준다.
- `display: flex` 와 `flex: 1` 이 짝을 이뤄 칸을 가로로 같은 너비로 나눈다.
- `.row:last-child` 로 마지막 줄의 아래 여백만 없애, 바깥 상자의 안쪽 여백과 겹치지 않게 한다.
- 글자색은 흰색을 기본으로 두고, 옅은 칸 하나만 더 구체적인 `.swatch.dark` 로 덮는다.
- `dark` 는 `swatch` 와 함께 붙여야 `.swatch.dark` 규칙에 걸린다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
