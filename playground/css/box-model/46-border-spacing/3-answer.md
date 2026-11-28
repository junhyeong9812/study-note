# css/box-model/46 — border-spacing — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 가로 3군데 24px, 세로 4군데 32px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
가로: 왼쪽 가장자리 · 두 열 사이 · 오른쪽 가장자리 = 3군데 × 8px = 24px.
세로: 위 가장자리 · 행 사이 2군데 · 아래 가장자리 = 4군데 × 8px = 32px.

**왜 그런가**
`border-spacing` 은 셀 사이뿐 아니라 테이블 바깥 가장자리와 맨 바깥 셀 사이에도 들어간다.
그래서 n 칸이면 그 방향의 간격은 n + 1 군데다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 2. 열 사이 4px, 행 사이 12px

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
열과 열 사이(가로)는 4px, 행과 행 사이(세로)는 12px 이다.

**왜 그런가**
값이 둘이면 첫째가 수평, 둘째가 수직 간격이다.
`margin` 의 두 값(위아래, 좌우)과 순서가 반대이니 주의한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 3. 간격이 생기지 않고 테두리가 합쳐진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
셀 사이에 틈이 없다.
이웃 셀의 테두리가 한 줄로 합쳐져 그려지고, `border-spacing: 20px` 은 아무 효과가 없다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`border-spacing` 은 `border-collapse: separate` 일 때만 적용되고, `collapse` 상태에서는 무시된다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 4. 합쳐진 테두리 사이에는 벌릴 틈이 없기 때문이다

`collapse` 에서는 이웃 셀이 테두리 한 줄을 함께 쓴다.
셀마다 따로 그려진 테두리가 있어야 그 둘 사이를 벌릴 수 있는데, 테두리가 하나로 합쳐졌으니 간격을 넣을 경계가 없다.
그래서 속성은 에러 없이 조용히 무시된다.
근거: 2-summary 「동작 방식 (3)」.

### 5. 없다 — 가장자리에도 같은 간격이 들어간다

`border-spacing` 은 셀 사이와 바깥 가장자리에 같은 값을 적용한다.
값 두 개는 가로·세로를 나눌 뿐, 「안쪽」과 「가장자리」를 나누지 않는다.
따라서 이 속성 하나로는 가장자리 간격만 0 으로 만들 수 없다.
근거: 2-summary 「어디서 틀리나 2」 · 「동작 방식 (1)」.

### 6. 문법을 벗어나 무효가 된다

문법이 `<length>{1,2}` 라서 값은 하나 또는 둘만 허용된다.
셋을 쓰면 그 선언 전체가 무효가 되고, 이전 값(다른 규칙의 값이나 기본값)이 쓰인다.
근거: 2-summary 「문법 — 형태와 규칙」.

### 7. `padding` 은 테두리 안쪽, `border-spacing` 은 테두리 바깥 — 배경은 `padding` 까지

`padding` 은 셀 테두리와 글자 사이의 안쪽 여백이고, `border-spacing` 은 셀 테두리와 이웃 셀(또는 표 가장자리) 사이의 바깥 틈이다.
머리 셀의 `background` 는 셀 영역이므로 `padding` 영역까지 칠해지고, `border-spacing` 틈에는 셀 배경이 아니라 테이블 쪽 배경이 보인다.
근거: 2-summary 「어디서 틀리나 4」.

## 실습 정답

### 실습 1. 셀이 서로 떨어진 2열 표 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 2열 3행 표(머리 A·B, 데이터 1·2 / 3·4) | `<table class="table">` 안의 `<tr>` 3개, 첫 행 `<th>`, 나머지 `<td>` |
| 셀 테두리를 셀마다 따로 그리기 | `.table { border-collapse: separate; }` |
| 셀 사이와 가장자리에 가로·세로 같은 간격 | `.table { border-spacing: 8px; }` |
| 표 너비 · 셀 꾸밈은 그대로 | `.table { width: 100%; }` · `.table th, .table td { border; padding; text-align }` · `.table th { background }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-spacing.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-spacing - 테이블 셀 간의 간격을 설정 (border-collapse: separate일 때만 적용)</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-spacing
  설명: 테이블 셀 간의 간격을 설정 (border-collapse: separate일 때만 적용)
  구문: border-spacing: <length>{1,2}
  팁: border-collapse: collapse 상태에서는 무시됨. 테이블 바깥 가장자리에도 간격이 적용됨.
-->
<style>
  /* .table: 셀 간격 시연 테이블 */
  .table {
    border-collapse: separate;   /* 셀 테두리 분리(기본값). border-spacing이 작동하려면 separate여야 함 */
    border-spacing: 8px;         /* 셀 사이 간격 8px. 값 2개 지정 시 가로/세로 간격 분리 가능 */
    width: 100%;                 /* 부모 너비의 100% */
  }
  /* .table th, .table td: 표 머리/데이터 셀 공통 스타일 */
  .table th,
  .table td {
    border: 2px solid #3b82f6;   /* 셀 테두리 단축. 2px 실선 파란색(#3b82f6). 인접 셀과 분리되어 표시 */
    padding: 8px;                /* 셀 내부 사방 8px 여백 */
    text-align: center;          /* 셀 내부 텍스트 가운데 정렬 */
  }
  /* .table th: 표 머리 셀 추가 스타일 */
  .table th {
    background: #eff6ff;         /* 머리 셀 배경 옅은 파랑(#eff6ff) */
  }
</style>
</head>
<body>
  <table class="table"> <!-- 셀 간격을 시연하는 표 -->
    <tr> <!-- 표 머리 행 -->
      <th>A</th> <!-- 머리 셀 A -->
      <th>B</th> <!-- 머리 셀 B -->
    </tr>
    <tr> <!-- 데이터 행 1 -->
      <td>1</td> <!-- 데이터 셀 1 -->
      <td>2</td> <!-- 데이터 셀 2 -->
    </tr>
    <tr> <!-- 데이터 행 2 -->
      <td>3</td> <!-- 데이터 셀 3 -->
      <td>4</td> <!-- 데이터 셀 4 -->
    </tr>
  </table>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.table { border-collapse: separate; border-spacing: 8px; width: 100%; }
.table th, .table td { border: 2px solid #3b82f6; padding: 8px; text-align: center; }
.table th { background: #eff6ff; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `border-spacing` 은 `separate` 일 때만 쓰이므로 `border-collapse: separate` 를 함께 적는다 — 기본값이라 생략해도 되지만 의도를 드러낸다.
- 값 하나(`8px`)라서 가로·세로 간격이 같다.
- 간격은 셀 사이뿐 아니라 표 가장자리와 바깥 셀 사이에도 생긴다.
- 셀 안쪽 여백은 `padding`, 셀 바깥 틈은 `border-spacing` 으로 역할이 나뉜다.
- `collapse` 로 바꾸면 테두리가 합쳐지고 `border-spacing` 은 무시된다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
