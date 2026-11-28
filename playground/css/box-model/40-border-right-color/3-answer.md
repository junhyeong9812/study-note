# css/box-model/40 — border-right-color — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 오른쪽은 빨간색, 다른 세 변에는 테두리가 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
오른쪽 테두리는 `#ef4444`(빨간색)이다.
위 · 아래 · 왼쪽에는 테두리가 없다.

**왜 그런가**
`border-right` 단축이 먼저 색을 기본값으로 두고, 다음 줄의 `border-right-color` 가 색만 빨간색으로 덮어쓴다.
`border-right` 는 오른쪽 변만 정하므로 나머지 세 변에는 모양이 없다.
근거: 2-summary 「동작 방식 (3)」 입력 A.

### 2. 단축이 뒤에 오면 색은 글자색(navy)이 된다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
오른쪽 테두리는 `navy` 다.

**왜 그런가**
뒤에 쓴 `border-right: 4px solid` 가 생략된 색을 기본값 `currentcolor` 로 되돌린다.
`currentcolor` 는 요소의 `color` 값이므로 `navy` 가 된다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 입력 B.

### 3. 모양이 없어 빨간 선은 보이지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
오른쪽에 빨간 선이 보이지 않는다.

**왜 그런가**
색은 정했지만 `border-right-style` 의 기본값이 `none` 이라 그릴 테두리가 없다.
`border-right-color` 는 이미 있는 테두리의 색만 정한다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 기본값이 `currentcolor` 이기 때문이다

`border-right-color` 의 기본값은 `currentcolor` 이고, 이 키워드는 요소의 현재 텍스트 색상을 가리킨다.
단축 속성이 색을 생략하면 이 기본값이 쓰인다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 1」.

### 5. 아니다 — 상속되지 않는다

`border-right-color` 는 상속되지 않는 속성이다.
자식 테두리에 같은 색을 쓰려면 자식에게도 따로 지정해야 한다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 4」.

### 6. 오른쪽 한 변뿐이다

`border-color` 는 네 변의 색을 모두 바꾸지만, `border-right-color` 는 오른쪽 변 하나만 바꾸고 다른 세 변은 건드리지 않는다.
근거: 2-summary 「동작 방식 (1)」 · 「언제 쓰고 언제 안 쓰나」.

### 7. 테두리 색도 새 글자색으로 바뀐다

기본값 `currentcolor` 는 고정된 색이 아니라 요소의 `color` 를 가리킨다.
그래서 `color` 가 바뀌면 테두리 색도 따라 바뀐다.
근거: 2-summary 「동작 방식 (2)」.

### 8. 그렇다 — 애니메이션 가능한 속성이다

원본 재료에 「애니메이션 가능: True」로 적혀 있다.
색 값이므로 `transition` 으로 두 색 사이를 이어 바꿀 수 있다.
근거: 2-summary 「동작 방식 (5)」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 오른쪽 테두리만 빨간 박스 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 단축으로 두께 · 실선만, 색 생략 | `.box { border-right: 4px solid; }` |
| 색만 따로 지정 | `border-right-color: #ef4444;` |
| 단축 뒤에 색 지정 순서 | `.box` 안에서 `border-right` 다음 줄에 `border-right-color` |
| 박스 안 글자 | `<div class="box">border-right-color</div>` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/box-model/reference/border-right-color.html`

```html
<!DOCTYPE html> <!-- HTML5 문서 선언 -->
<html lang="ko"> <!-- 문서 언어를 한국어로 지정 -->
<head> <!-- 문서 메타정보 영역 -->
<meta charset="utf-8"> <!-- 문자 인코딩 UTF-8 설정 -->
<title>border-right-color - 요소의 오른쪽 테두리 색상을 설정</title> <!-- 브라우저 탭 제목 -->
<!--
  [박스 모델] border-right-color
  설명: 요소의 오른쪽 테두리 색상을 설정
  구문: border-right-color: <color>
  팁: 기본값은 currentcolor.
-->
<style>
  /* .box: 오른쪽 테두리 색상 시연 박스 */
  .box {
    border-right: 4px solid;        /* 오른쪽 테두리 단축. 4px 실선. 색상 미지정 */
    border-right-color: #ef4444;    /* 오른쪽 테두리 색상을 빨간색(#ef4444)으로 별도 지정 */
    padding: 16px;                  /* 박스 내부 사방 16px 여백 */
    background: #f8fafc;            /* 배경색 매우 옅은 회색(#f8fafc) */
  }
</style>
</head>
<body>
  <div class="box">border-right-color</div> <!-- 오른쪽 테두리 색상이 적용된 박스 -->

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.box { border-right: 4px solid; border-right-color: #ef4444; padding: 16px; background: #f8fafc; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- `border-right: 4px solid` 가 오른쪽 테두리의 두께와 모양을 만든다 — 모양이 있어야 색이 보인다.
- 색을 생략한 단축은 색을 기본값 `currentcolor` 로 둔다.
- 다음 줄의 `border-right-color` 가 그 색만 빨간색으로 덮어쓴다.
- 두 줄 순서를 바꾸면 단축이 색을 되돌려 글자색 테두리가 된다.
- `padding` · `background` 는 테두리를 잘 보이게 하는 꾸밈이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
