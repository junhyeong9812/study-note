# css/visual/16 — overscroll-behavior-x — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 기본값 `auto` 에서는 바깥 `.page` 로 넘어간다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.strip` 에 `overscroll-behavior-x` 를 걸지 않았으니 기본값 `auto` 다.
`.strip` 이 오른쪽 끝에 닿은 뒤의 입력은 바깥으로 이어져, 가로로 스크롤되는 `.page` 가 대신 움직일 수 있다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`auto` 는 스크롤 체이닝을 막지 않는다.
안쪽 영역이 더 움직일 수 없으면 남은 입력이 바깥 스크롤 영역으로 넘어간다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `contain` 이면 `.page` 는 가만히 있고, `.strip` 의 튕김은 남는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.strip` 이 끝에 닿은 뒤 더 밀어도 `.page` 는 움직이지 않는다.
`.strip` 자신의 끝 효과(바운스 같은 것)는 브라우저가 보여 주는 대로 남는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`contain` 은 가로 스크롤 체이닝만 막는다.
자기 끝 효과까지 없애는 것은 `none` 이다.
근거: 2-summary 「동작 방식 (2)」.

### 3. 둘 다 체이닝을 막고, 바운스는 `none` 만 막는다

`contain` 과 `none` 은 모두 끝에 닿은 뒤의 입력이 바깥으로 넘어가는 것(체이닝)을 막는다.
상자 자신의 튕김(바운스)은 `contain` 에서는 남고 `none` 에서는 사라진다.
근거: 2-summary 「문법 — 형태와 규칙」의 값 표, 「어디서 틀리나 5」.

### 4. 끝에서 더 민 스와이프가 브라우저 뒤로가기 같은 바깥 동작으로 이어지는 일이 사라진다

캐러셀 끝까지 민 뒤 계속 쓸어 넘기면 그 움직임이 바깥으로 넘어가 브라우저의 가로 스와이프(뒤로가기 등)로 받아들여질 수 있다.
체이닝을 끊으면 입력이 캐러셀 안에 갇혀 그런 동작이 일어나지 않는다.
다만 브라우저가 제스처를 어떻게 다루는지는 구현에 달려 있다 (확인 필요).
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」, 「구현 세부사항 대 언어 보장」.

### 5. 상자가 실제로 가로 스크롤되어야 끝에 닿을 일이 생기기 때문이다

`overscroll-behavior-x` 는 「가로 스크롤이 끝에 닿은 뒤」를 다룬다.
`overflow-x: auto` 로 가로 스크롤을 허락하고, `white-space: nowrap` 과 오른쪽 여백으로 콘텐츠를 상자보다 넓게 만들어야 끝이 생긴다.
스크롤되지 않는 상자에는 이 속성이 다룰 상황이 없다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 2」.

### 6. 막히지 않는다 — 상속되지 않는다

`overscroll-behavior-x` 는 상속되지 않으므로 안쪽 스크롤 상자는 여전히 기본값 `auto` 다.
안쪽 상자의 체이닝도 막으려면 그 상자에 따로 건다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 3」.

### 7. 막히지 않는다 — 가로 방향만 다룬다

이름 끝의 `-x` 가 말하듯 이 속성은 가로 끝의 동작만 바꾼다.
세로 끝에서 바깥으로 넘어가는 일은 그대로 일어난다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 4」.

### 8. 한 번에 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
마우스를 올리는 순간 값이 `auto` 에서 `none` 으로 곧바로 바뀐다.
1초에 걸친 중간 단계는 없다.

**왜 그런가**
이 속성은 애니메이션 가능하지 않다(원본 `애니메이션 가능: False`).
`auto` 와 `none` 사이에 사이값이 없으니 `transition` 이 보간할 것이 없다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 6」.

## 실습 정답

### 실습 1. 바깥으로 새지 않는 가로 스크롤 상자 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 가로로 넘치면 스크롤바 | `.scroll-x { overflow-x: auto; }` |
| 2. 줄바꿈 없이 한 줄 | `.scroll-x { white-space: nowrap; }` |
| 3. 인라인 블록으로 자기 너비대로 | `.content { display: inline-block; }` |
| 4. 오른쪽 여백으로 스크롤 길이 확보 | `.content { padding-right: 200px; }` (시작 코드에 있음) |
| 5. 가로 체이닝 차단, 끝 효과는 남김 | `.scroll-x { overscroll-behavior-x: contain; }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/visual/reference/overscroll-behavior-x.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 언어: 한국어 -->
<head>
  <meta charset="utf-8">
  <!-- 문자 인코딩: UTF-8 -->
  <title>overscroll-behavior-x - 가로 방향의 오버스크롤 동작을 제어합니다</title>
  <!--
    [시각 효과] overscroll-behavior-x
    설명: 가로 방향의 오버스크롤 동작을 제어합니다
    구문: overscroll-behavior-x: auto | contain | none
    팁: 가로 스크롤 캐러셀에서 브라우저 뒤로가기 제스처(스와이프)를 방지할 때 유용.
  -->
  <style>
    /* .scroll-x: 가로 스크롤 영역 - 브라우저 가로 스와이프 차단 */
    .scroll-x {
      overscroll-behavior-x: contain;             /* 가로 스크롤 끝나도 부모/페이지로 전파 차단 - 캐러셀에서 뒤로가기 제스처 방지 */
      overflow-x: auto;                           /* 가로 스크롤바 자동 표시 */
      white-space: nowrap;                        /* 줄바꿈 방지 - 가로로 길게 늘어남 */
      background: #ede9fe;                        /* 연보라 배경 */
      padding: 16px;                              /* 안쪽 여백 16px */
      border-radius: 8px;                         /* 모서리 둥글게 */
      width: 220px;                               /* 너비 220px - 콘텐츠보다 작아 스크롤 발생 */
      margin: 30px auto;                          /* 위아래 30px, 가로 중앙 */
      border: 2px solid #8b5cf6;                  /* 보라 테두리 */
    }
    /* .content: 컨테이너보다 넓은 인라인 콘텐츠 */
    .content {
      display: inline-block;                      /* 인라인 블록 - 자기 너비대로 확장 */
      color: #6d28d9;                             /* 짙은 보라 글자 */
      font-size: 14px;                            /* 글자 14px */
      font-weight: 500;                           /* 보통 굵기 */
      padding-right: 200px;                       /* 오른쪽 여백 200px - 가로 스크롤 길이 확보 */
    }
  </style>
</head>
<body>
  <!-- 가로 스크롤 시 페이지 전파 차단 데모 -->
  <div class="scroll-x">
    <!-- contain으로 오버스크롤 격리된 가로 영역 -->
    <div class="content">← 가로 스크롤 → 오버스크롤이 제한됩니다. 더 많은 콘텐츠가 이어집니다.</div>
    <!-- 컨테이너보다 긴 콘텐츠 -->
  </div>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.scroll-x { overscroll-behavior-x: contain; overflow-x: auto; white-space: nowrap; background: #ede9fe; padding: 16px; border-radius: 8px; width: 220px; margin: 30px auto; border: 2px solid #8b5cf6; }
.content { display: inline-block; color: #6d28d9; font-size: 14px; font-weight: 500; padding-right: 200px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**

- `overflow-x: auto` 가 없으면 상자가 가로로 스크롤되지 않아 `overscroll-behavior-x` 가 할 일이 없다.
- `white-space: nowrap` · `display: inline-block` · `padding-right` 가 함께 콘텐츠를 상자(220px)보다 넓게 만들어 가로 끝을 만든다.
- 끝 효과는 남기고 체이닝만 막는 값은 `contain` 이다 — `none` 은 튕김까지 없앤다.
- 속성은 스크롤되는 `.scroll-x` 에 건다; 자식 `.content` 에 걸어도 상속 구조상 의미가 없다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
