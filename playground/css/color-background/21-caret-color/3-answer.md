# css/color-background/21 — caret-color — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 둘 다 초록 — 부모 값을 물려받는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`input` 과 `textarea` 모두 초록 캐럿이 깜빡인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`caret-color` 는 상속되는 속성이다.
안쪽 입력칸에 자기 값이 없으니 `.form` 의 값을 물려받는다.
근거: 2-summary 「동작 방식 (3)」.

### 2. `auto` — `currentcolor`(글자 색 파랑) 또는 브라우저 기본값

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
캐럿 색은 기본값 `auto` 로 정해진다.
`auto` 는 `currentcolor` 또는 브라우저 기본값이므로, 많은 경우 글자 색과 같은 파랑이고, 브라우저가 기본값을 고르면 그 색이다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`caret-color` 를 쓰지 않으면 기본값 `auto` 가 적용된다.
`currentcolor` 는 그 요소의 `color` 를 가리키므로 파랑과 이어진다.
어느 쪽을 쓸지는 브라우저가 고른다.
근거: 2-summary 「동작 방식 (2)」, 「구현 세부사항 대 언어 보장」.

### 3. 글자는 보이고 캐럿만 안 보인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
친 글자는 평소처럼 나타나지만, 다음 글자가 들어갈 자리를 가리키는 깜빡이는 막대는 보이지 않는다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`transparent` 는 투명한 색 값이라 캐럿을 투명하게 칠할 뿐이다.
입력 자체를 막는 것이 아니라 표시만 사라진다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 캐럿이 입력 위치를 알려 주는 유일한 표시이기 때문이다

캐럿이 안 보이면 사용자는 글자가 어디에 들어가는지 알 수 없다.
특히 키보드로만 움직이는 사용자나 눈이 불편한 사용자가 길을 잃는다.
그래서 원본 팁도 `transparent` 에 「접근성 주의」를 붙였다.
대신할 표시를 직접 그리지 않는다면 숨기지 않는다.
근거: 2-summary 「어디서 틀리나 1」.

### 5. 값이 색이라서 — 색은 두 색 사이의 값을 계산할 수 있다

`caret-color` 의 값은 `<color>` 다.
색은 빨강에서 파랑으로 가는 중간 색들을 계산할 수 있으므로, 시간에 따라 조금씩 바꿀 수 있다.
속성 정보에서도 애니메이션 가능으로 되어 있다.
근거: 2-summary 「동작 방식 (4)」, 「문법」 (원본에 근거 없음 — 추론: 「값이 색이라서」라는 까닭 부분).

### 6. `contenteditable` 요소 — 평범한 `div` 에는 캐럿이 생기지 않는다

캐럿은 글자를 입력할 수 있는 곳에만 생긴다.
`input` · `textarea` 말고도 `contenteditable` 요소에서 작동한다.
평범한 `div` 는 입력할 수 없어 캐럿이 없으니 칠할 대상이 없다.
다만 상속되므로, 그 `div` 안에 입력칸이 있으면 그쪽 캐럿에 값이 내려간다.
근거: 2-summary 「동작 방식 (1)」, 「어디서 틀리나 3」.

### 7. 캐럿과 마우스 포인터를 헷갈렸다

`caret-color` 는 글자 입력 위치의 막대만 칠한다.
마우스 포인터는 `cursor` 속성이 다루므로 `caret-color` 로는 바뀌지 않는다.
근거: 2-summary 「어디서 틀리나 2」, 「언제 쓰고 언제 안 쓰나」.

### 8. `auto` 는 `currentcolor` 를 통해 `color` 를 따를 수 있지만, 브라우저 기본값을 고를 수도 있다

`currentcolor` 는 그 요소의 `color` 값을 가리키므로 `auto` 는 글자 색과 이어질 수 있다.
그러나 `auto` 는 「`currentcolor` 또는 브라우저 기본값」이고 어느 쪽인지는 브라우저가 고른다.
그래서 특정 색이 꼭 필요하면 `<color>` 를 직접 적는다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 4」.

## 실습 정답

### 실습 1. 캐럿 색이 서로 다른 입력칸 세 개

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| input 둘 · textarea 하나를 차례로 둔다 | `<body>` 안의 `input.red-caret` · `input.blue-caret` · `textarea.green-caret` |
| 첫째 input 캐럿 빨강 | `.red-caret { caret-color: #ef4444; }` |
| 둘째 input 캐럿 파랑 | `.blue-caret { caret-color: #3b82f6; }` |
| textarea 캐럿 초록 | `.green-caret { caret-color: #22c55e; }` |
| 글자 색은 그대로, 같은 꾸밈, textarea 만 높이 고정 | `color` 를 쓰지 않음 · 세 규칙의 `padding` · `border` · `width` 등 · `.green-caret` 의 `height` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/color-background/reference/caret-color.html`

```html
<!DOCTYPE html>
<!-- 문서 타입 선언: HTML5 -->
<html lang="ko">
<!-- 문서 루트: 한국어 페이지 -->
<head>
<!-- 메타 영역 시작 -->
<meta charset="utf-8">
<!-- 문자 인코딩: UTF-8 -->
<title>caret-color - 텍스트 입력 커서(캐럿)의 색상을 설정</title>
<!-- 브라우저 탭 제목 -->
<!--
  [색상 & 배경] caret-color
  설명: 텍스트 입력 커서(캐럿)의 색상을 설정
  구문: caret-color: auto | <color>
  팁: contenteditable 요소에서도 작동. transparent로 설정하면 커서가 보이지 않음 (접근성 주의).
-->
<style>
  /* .red-caret: 빨간 캐럿(입력 커서) 스타일 */
  .red-caret {
    caret-color: #ef4444;          /* 입력 커서 색상을 빨강으로 */
    padding: 8px 12px;             /* 상하 8px, 좌우 12px 패딩 */
    border: 2px solid #e2e8f0;     /* 회색 실선 2px */
    border-radius: 6px;            /* 모서리 둥글기 6px */
    width: 100%;                   /* 가로 100% */
    margin-bottom: 8px;            /* 아래 여백 8px */
    font-size: 14px;               /* 글자 크기 14px */
  }
  /* .blue-caret: 파란 캐럿 스타일 */
  .blue-caret {
    caret-color: #3b82f6;          /* 입력 커서 색상을 파랑으로 */
    padding: 8px 12px;             /* 패딩 */
    border: 2px solid #e2e8f0;     /* 회색 실선 2px */
    border-radius: 6px;            /* 모서리 둥글기 6px */
    width: 100%;                   /* 가로 100% */
    margin-bottom: 8px;            /* 아래 여백 8px */
    font-size: 14px;               /* 글자 크기 14px */
  }
  /* .green-caret: 초록 캐럿(textarea용) */
  .green-caret {
    caret-color: #22c55e;          /* 입력 커서 색상을 초록으로 */
    padding: 8px 12px;             /* 패딩 */
    border: 2px solid #e2e8f0;     /* 회색 실선 2px */
    border-radius: 6px;            /* 모서리 둥글기 6px */
    width: 100%;                   /* 가로 100% */
    height: 60px;                  /* 고정 높이 60px */
    font-size: 14px;               /* 글자 크기 14px */
  }
</style>
</head>
<body>
  <!-- 빨간 커서 input -->
  <input type="text" class="red-caret" placeholder="빨간 커서 (클릭해보세요)">
  <!-- 파란 커서 input -->
  <input type="text" class="blue-caret" placeholder="파란 커서 (클릭해보세요)">
  <!-- 초록 커서 textarea -->
  <textarea class="green-caret" placeholder="초록 커서 (클릭해보세요)"></textarea>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.red-caret { caret-color: #ef4444; padding: 8px 12px; border: 2px solid #e2e8f0; border-radius: 6px; width: 100%; margin-bottom: 8px; font-size: 14px; }
.blue-caret { caret-color: #3b82f6; padding: 8px 12px; border: 2px solid #e2e8f0; border-radius: 6px; width: 100%; margin-bottom: 8px; font-size: 14px; }
.green-caret { caret-color: #22c55e; padding: 8px 12px; border: 2px solid #e2e8f0; border-radius: 6px; width: 100%; height: 60px; font-size: 14px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 칸마다 바뀌는 줄은 `caret-color` 하나뿐이고, 나머지 꾸밈은 세 규칙이 같다.
- `color` 를 건드리지 않았으니 친 글자 색은 브라우저 기본 그대로이고 캐럿만 칠해진다.
- `textarea` 에도 `input` 과 똑같이 작동한다 — 캐럿이 생기는 입력 요소면 된다.
- 세 칸 모두에 같은 색을 줄 생각이었다면 부모 하나에 주어 상속시키는 편이 짧다.
- 값을 `transparent` 로 바꿔 보면 캐럿이 사라지는 것을 볼 수 있지만, 실제 화면에서는 접근성 때문에 피한다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
