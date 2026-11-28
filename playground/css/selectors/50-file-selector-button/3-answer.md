# css/selectors/50 — ::file-selector-button — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 버튼 부분만 파래진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
입력 요소 안의 「파일 선택」 버튼 상자만 파란 배경에 흰 글자가 된다.
옆의 파일 이름 글자 쪽은 배경이 칠해지지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`.file-input` 이 입력 요소를 고르고 `::file-selector-button` 이 그 안의 버튼 부분으로 범위를 좁히므로 선언은 버튼에만 닿는다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 진한 파랑으로 0.2초에 걸쳐 바뀐다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
배경이 `#3b82f6` 에서 `#1d4ed8` 로 0.2초 동안 서서히 바뀐다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`:hover` 가 붙은 규칙은 버튼 위에 마우스가 있을 때만 맞아 배경 값을 덮어쓴다.
기본 규칙의 `transition: background 0.2s` 가 그 값 변화를 0.2초에 걸쳐 잇는다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 버튼 색은 그대로다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
파일 이름 글자 위에서는 버튼 배경이 바뀌지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`:hover` 가 의사 요소 뒤에 붙어 있으므로 「버튼 부분 위에 마우스가 있을 때」만 맞는다.
입력 요소의 다른 부분에 올라간 것은 이 조건을 채우지 않는다.
근거: 2-summary 「어디서 틀리나 5」.

### 4. 버튼은 HTML 에 태그로 없는 부분이라서

버튼은 브라우저가 파일 입력 안에 그려 넣은 부분이라 내가 쓴 HTML 에 태그가 없고, 그래서 `class` 를 붙일 자리가 없다.
태그 없는 부분을 상자처럼 고르는 수단이 의사 요소이고, 이 버튼을 가리키는 이름이 `::file-selector-button` 이다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 5. 두 규칙이 맡는 부분이 다르기 때문

입력 요소 규칙은 파일 이름 글자처럼 버튼이 아닌 부분을, 버튼 규칙은 버튼 안의 글자를 맡는다.
두 곳에 같은 값을 주어 버튼 글자와 파일 이름 글자의 크기를 맞춘다.
근거: 2-summary 「동작 방식 (2)」. (원본에 근거 없음 — 추론: 원본은 두 줄을 쓸 뿐 까닭을 적지 않았다)

### 6. 아무것도 바뀌지 않는다

글자 입력칸에는 「파일 선택」 버튼 부분이 없으므로 이 의사 요소가 고를 것이 없다.
근거: 2-summary 「어디서 틀리나 4」.

### 7. 입력 전체에 올렸을 때 대 버튼에 올렸을 때

`.file-input:hover::file-selector-button` 은 입력 요소 어디든 마우스가 올라가 있으면 버튼을 고른다.
`.file-input::file-selector-button:hover` 는 버튼 부분 위에 마우스가 있을 때만 맞는다.
의사 클래스가 앞(요소)에 붙느냐 뒤(의사 요소)에 붙느냐가 상태를 따질 대상을 정한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 5」.

### 8. 브라우저 기본 모양을 먼저 지우는 몫

기본 버튼은 브라우저마다 다르게 그려지므로, 그 기본 테두리를 `border: none` 으로 지워야 직접 정한 배경 · 둥근 모서리만 남아 어느 브라우저에서나 같은 모양에 가까워진다.
근거: 2-summary 「어디서 틀리나 1」 · 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. 파일 선택 버튼을 파란 버튼으로 꾸미기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 파일 선택 입력에 `file-input` 클래스 | `<input type="file" class="file-input" />` |
| 입력 요소 전체 글자 크기 | `.file-input { font-size: … }` |
| 버튼 부분에만 여백 · 배경 · 글자색 · 테두리 제거 · 모서리 · 커서 · 글자 크기 · 오른쪽 여백 · 전이 | `.file-input::file-selector-button { … }` |
| 버튼 위 마우스일 때만 진한 배경 | `.file-input::file-selector-button:hover { background: … }` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/selectors/reference/file-selector-button.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<head>
<meta charset="utf-8">
<title>::file-selector-button - 파일 입력(<input type="file">)의 버튼 부분을 스타일링한다.</title>
<!--
  [선택자] ::file-selector-button
  설명: 파일 입력(<input type="file">)의 버튼 부분을 스타일링한다.
  구문: input[type="file"]::file-selector-button { }
  팁: 기본 파일 입력 버튼은 브라우저마다 다르게 보인다. ::file-selector-button으로 통일된 스타일을 적용할 수 있다.
-->
<style>
  /* .file-input: class 속성에 file-input을 가진 요소 매칭 */
  .file-input {
    font-size: 14px;             /* 글자 크기 14px */
  }
  /* .file-input::file-selector-button: 파일 입력의 내부 '파일 선택' 버튼 매칭 */
  .file-input::file-selector-button {
    padding: 10px 20px;          /* 안쪽 여백 위아래 10, 좌우 20 */
    background: #3b82f6;         /* 파란 배경 */
    color: white;                /* 흰색 텍스트 */
    border: none;                /* 테두리 제거 */
    border-radius: 8px;          /* 8px 둥근 모서리 */
    cursor: pointer;             /* 포인터 커서 */
    font-size: 14px;             /* 글자 크기 14px */
    margin-right: 12px;          /* 오른쪽 여백 12px */
    transition: background 0.2s; /* 배경 0.2초 전이 */
  }
  /* .file-input::file-selector-button:hover: 파일 입력 버튼에 마우스 오버 상태 매칭 */
  .file-input::file-selector-button:hover {
    background: #1d4ed8;         /* 호버 시 더 진한 파랑 */
  }
</style>
</head>
<body>
  <!-- 파일 선택 입력 -->
  <input type="file" class="file-input" />

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.file-input { font-size: 14px; }
.file-input::file-selector-button { padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; margin-right: 12px; transition: background 0.2s; }
.file-input::file-selector-button:hover { background: #1d4ed8; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 입력 요소는 클래스로, 그 안의 버튼은 `::file-selector-button` 으로 고른다.
- 파일 이름 글자 쪽은 입력 요소 규칙이, 버튼 쪽은 의사 요소 규칙이 맡는다.
- `border: none` 으로 브라우저 기본 테두리를 지워 통일된 모양을 만든다.
- `:hover` 는 의사 요소 뒤에 붙여 버튼 위에서만 반응하게 한다.
- `transition: background 0.2s` 를 기본 규칙에 두어 색 변화를 부드럽게 한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
