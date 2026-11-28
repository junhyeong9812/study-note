# css/typography/39 — tab-size — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 공백 8개 너비 — 탭 4칸 × 2

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`b` 앞이 공백 8개만큼 들여쓰여 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`<pre>` 는 공백을 유지하므로 탭 두 개가 그대로 남는다.
정수 `4` 는 탭 하나를 공백 4개 너비로 그리라는 뜻이고, 줄 맨 앞의 탭 두 개는 4 × 2 = 8 이다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 공백 하나처럼 보인다 — `tab-size` 는 아무 일도 하지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`x y` 처럼 공백 한 칸 간격으로 보인다 (코드에서 읽은 것 — 렌더 실측 아님).

**왜 그런가**
`<div>` 의 `white-space` 는 기본값 `normal` 이라 탭이 공백 하나로 접힌다.
그릴 탭이 남지 않으니 `tab-size: 8` 은 효과가 없다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 3. 정수 값을 쓴 `.p` 만 넓어진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`.p` 의 탭 폭은 커지고, `.q` 의 탭 폭은 56px 그대로다.

**왜 그런가**
정수 값의 단위는 공백 하나의 너비이고, 공백 너비는 글자 크기를 따른다.
길이 값은 고정 폭이라 글자 크기와 상관없다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (2)」 · 「어디서 틀리나 4」.

### 4. 기본값 8 이면 들여쓰기가 너무 넓기 때문이다

아무것도 정하지 않으면 탭 하나가 공백 8개 너비라서, 탭으로 여러 단계 들여쓴 코드가 오른쪽으로 크게 밀린다.
`2` 나 `4` 로 줄이면 코드 블록 안에서 들여쓰기가 읽기 좋은 폭이 된다.
근거: 2-summary 「문법 — 형태와 규칙」의 기본값 · 「어디서 틀리나 3」.

### 5. 아무 변화가 없다

`tab-size` 는 탭 문자에만 작용한다.
공백 4개는 탭이 아니므로 몇으로 바꿔도 공백 4개 폭 그대로다.
근거: 2-summary 「문법 — 형태와 규칙」 · 「어디서 틀리나 2」.

### 6. `<pre>` 가 기본으로 `white-space: pre` 를 가지기 때문이다

`tab-size` 는 공백을 유지하는 모드에서만 효과가 난다.
`<pre>` 는 브라우저 기본 스타일로 `white-space: pre` 라서, 탭이 접히지 않고 남아 `tab-size` 대로 그려진다.
근거: 2-summary 「동작 방식 (3)」 · 「구현 세부사항 대 언어 보장」.

### 7. `body` 의 값 2 를 상속받는다

`tab-size` 는 상속되는 속성이다.
`<pre>` 에 따로 값이 없으니 부모 쪽에서 내려온 `2` 를 쓰고, 탭 하나가 공백 2개 너비가 된다.
`<pre>` 에 다른 값을 주면 그 값이 이긴다.
근거: 2-summary 「동작 방식 (4)」.

## 실습 정답

### 실습 1. 탭 크기 2 · 4 · 8 을 나란히 비교하기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| `<pre>` 세 개를 `.tab2` · `.tab4` · `.tab8` 로 | `<pre class="tab2">` · `<pre class="tab4">` · `<pre class="tab8">` |
| 첫 줄 글 · 탭 하나 줄 · 탭 두 개 줄 | 각 `<pre>` 안의 `tab-size: N` / `indented line` / `double indented` |
| `.tab2` 탭 = 공백 2개 | `.tab2 { tab-size: 2; }` |
| `.tab4` 탭 = 공백 4개 | `.tab4 { tab-size: 4; }` |
| `.tab8` 탭 = 공백 8개 | `.tab8 { tab-size: 8; }` |
| 같은 코드 블록 모양 | 세 규칙의 `background` · `color` · `padding` · `border-radius` · `font-size` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`css/typography/reference/tab-size.html`

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <title>tab-size - 탭 문자(U+0009)의 표시 너비를 설정</title>
  <!--
    [타이포그래피] tab-size
    설명: 탭 문자(U+0009)의 표시 너비를 설정
    구문: tab-size: <integer> | <length>
    팁: white-space가 pre, pre-wrap 등 공백을 유지하는 모드일 때만 효과. 코드 표시에서 유용.
  -->
  <style>
    /* .tab2: 탭 = 공백 2칸 */
    .tab2 {
      tab-size: 2;            /* 탭 문자를 공백 2개 너비로 렌더링 (정수=공백 개수) */
      background: #1e293b;    /* 어두운 배경(코드 블록 느낌) */
      color: #e2e8f0;         /* 밝은 글자색(대비) */
      padding: 12px;          /* 안쪽 여백 */
      border-radius: 4px;     /* 모서리 둥글게 */
      margin-bottom: 8px;     /* 다음 블록과 간격 */
      font-size: 14px;        /* 코드용 크기 */
    }

    /* .tab4: 탭 = 공백 4칸 (가장 일반적) */
    .tab4 {
      tab-size: 4;            /* 탭 4공백 — 많은 언어의 권장 들여쓰기 */
      background: #1e293b;    /* 동일 배경 */
      color: #e2e8f0;         /* 동일 글자색 */
      padding: 12px;          /* 안쪽 여백 */
      border-radius: 4px;     /* 모서리 둥글게 */
      margin-bottom: 8px;     /* 다음 블록과 간격 */
      font-size: 14px;        /* 코드용 크기 */
    }

    /* .tab8: 탭 = 공백 8칸 (브라우저 기본값) */
    .tab8 {
      tab-size: 8;            /* 탭 8공백 — <pre>의 브라우저 기본 */
      background: #1e293b;    /* 동일 배경 */
      color: #e2e8f0;         /* 동일 글자색 */
      padding: 12px;          /* 안쪽 여백 */
      border-radius: 4px;     /* 모서리 둥글게 */
      font-size: 14px;        /* 코드용 크기 */
    }
  </style>
</head>
<body>
  <!-- tab-size: 2 (탭이 공백 2개로 표시) -->
  <pre class="tab2">tab-size: 2
	indented line
		double indented</pre>
  <!-- tab-size: 4 (탭이 공백 4개로 표시) -->
  <pre class="tab4">tab-size: 4
	indented line
		double indented</pre>
  <!-- tab-size: 8 (탭이 공백 8개로 표시) -->
  <pre class="tab8">tab-size: 8
	indented line
		double indented</pre>

</body>
</html>
```

원본 예제의 나머지 조각(study-practice 에는 없고 study-site 항목 데이터에만 있다):

```css
.tab2 { tab-size: 2; background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 4px; margin-bottom: 8px; font-size: 14px; }
.tab4 { tab-size: 4; background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 4px; margin-bottom: 8px; font-size: 14px; }
.tab8 { tab-size: 8; background: #1e293b; color: #e2e8f0; padding: 12px; border-radius: 4px; font-size: 14px; }
```

**실행 결과** — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

**풀이 요점**
- 배울 줄은 `tab-size: 2` · `4` · `8` 세 줄뿐이고, 나머지는 꾸밈이다.
- `<pre>` 는 기본으로 공백을 유지하므로 `white-space` 를 따로 쓰지 않아도 된다.
- `.tab8` 은 기본값과 같은 폭이라, 클래스에서 `tab-size` 를 빼도 같은 모양일 것이다 (원본에 근거 없음 — 추론).
- `<pre>` 안의 들여쓰기는 반드시 진짜 탭 문자여야 한다 — 공백이면 세 블록이 똑같이 보인다.
- `<pre>` 안에 HTML 주석을 넣으면 공백 처리가 엉킬 수 있으니, 주석은 블록 바깥에 둔다 (원본에 근거 없음 — 추론).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
