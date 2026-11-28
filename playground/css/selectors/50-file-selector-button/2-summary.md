# css/selectors/50 — ::file-selector-button — 정리 (힌트)

> 출처 — study-site 항목 `css/file-selector-button`(항목 데이터 `data/css/selectors.json`) · 정답 코드 study-practice `css/selectors/reference/file-selector-button.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`::file-selector-button` 은 「택배 상자에 붙은 손잡이만 따로 칠하는 붓」이다.**
상자(파일 입력)는 내가 만들었지만, 손잡이(「파일 선택」 버튼)는 공장(브라우저)이 붙여서 보낸다.
손잡이는 내가 쓴 HTML 에 태그로 없으니 클래스를 달 수 없다.
그래서 「이 상자의 손잡이」라고 가리키는 전용 이름이 필요하다.
`<input type="file">` 도 똑같은 구조다.
입력 요소는 내가 썼고, 그 안의 버튼은 브라우저가 그려 넣은 부분이다.

| 비유 | 실체 |
|---|---|
| 택배 상자 | `<input type="file">` 요소 |
| 공장이 붙인 손잡이 | 브라우저가 그리는 「파일 선택」 버튼 |
| 상자에 적힌 송장 글씨 | 버튼 옆의 파일 이름 글자 |
| 손잡이만 칠하는 붓 | `::file-selector-button` |

```text
<input type="file" class="file-input">
┌─────────────────────────────────────────────┐
│ ┌──────────────┐                            │
│ │  파일 선택    │   선택된 파일 없음          │
│ └──────────────┘                            │
│   ↑ ::file-selector-button   ↑ 입력 요소 자신의 글자
└─────────────────────────────────────────────┘
```

## 이 주제가 답하려는 질문

1. HTML 에 태그로 없는 파일 입력의 버튼을 어떻게 골라 꾸미나?
2. 버튼 규칙과 입력 요소 규칙은 각각 화면의 어느 부분에 닿나?
3. 버튼에 마우스를 올렸을 때의 모양은 어떻게 따로 정하나?
4. 브라우저마다 다른 기본 버튼 모양을 어떻게 하나로 맞추나?

## 동작 방식

### (1) 버튼 부분만 고르기

**언제 쓰나** — 파일 입력의 「파일 선택」 버튼을 사이트의 다른 버튼과 같은 모양으로 맞추고 싶을 때 쓴다.

```text
입력 코드                        무엇이 일어나나                     결과
.file-input::file-selector-button  ① .file-input 으로 입력 요소를 찾는다    버튼 부분만
  { background: #3b82f6; }        ② :: 뒤 이름으로 그 안의 버튼 부분을 가리킨다   파란 배경
                                  ③ 선언을 버튼 부분에만 적용한다         (파일 이름 글자는 그대로)
```

- 앞부분(`.file-input` 또는 `input[type="file"]`)이 입력 요소를 고른다.
- `::file-selector-button` 이 그 요소 안의 버튼 부분으로 범위를 좁힌다.
- 그래서 `background` · `padding` · `border-radius` 같은 선언은 버튼 상자에만 닿는다.
- 버튼 옆의 파일 이름 글자는 버튼이 아니므로 이 규칙의 영향을 받지 않는다.

> **의사 요소(pseudo-element)** — 문서에 태그로 쓰지 않았지만 CSS 가 하나의 상자처럼 골라 꾸밀 수 있는 요소의 한 부분. 이름 앞에 콜론 두 개(`::`)를 붙인다.\
> 예: `::file-selector-button` 은 파일 입력 안의 버튼 부분이다.

### (2) 입력 요소 규칙과 버튼 규칙의 몫 나누기

**언제 쓰나** — 버튼과 파일 이름 글자의 크기를 함께 맞추고 싶을 때 쓴다.

```text
.file-input { font-size: 14px; }                       → 입력 요소 전체(파일 이름 글자 포함)
.file-input::file-selector-button { font-size: 14px; } → 버튼 안의 글자
결과: 버튼 글자와 파일 이름 글자가 같은 크기로 나란히 놓인다
```

- 원본 예제는 `font-size` 를 두 번 쓴다 — 입력 요소에 한 번, 버튼에 한 번.
- 입력 요소 규칙은 파일 이름 글자처럼 버튼이 아닌 부분의 모양을 정한다.
- 버튼 규칙은 버튼 안의 글자를 정한다.
- 두 값을 같게 두면 한 줄의 글자 높이가 맞는다.
- 버튼의 `margin-right` 는 버튼 오른쪽 바깥에 빈자리를 만들어 파일 이름 글자를 버튼에서 떼어 놓는다.

### (3) 마우스를 올렸을 때 — 의사 요소 뒤의 `:hover`

**언제 쓰나** — 버튼이 눌릴 수 있다는 것을 보여 주려고 마우스를 올리면 색을 바꿀 때 쓴다.

```text
입력 코드                                       무엇이 일어나나                        결과
.file-input::file-selector-button:hover          ① 버튼 부분을 고른다                     버튼 배경이
  { background: #1d4ed8; }                       ② 그 버튼 위에 마우스가 있을 때만 맞는다    진한 파랑으로
기본 규칙의 transition: background 0.2s          ③ 배경 값이 바뀔 때 0.2초에 걸쳐 바뀐다    서서히 바뀐다
```

- 차례는 「요소 → 의사 요소 → 상태」다: `.file-input::file-selector-button:hover`.
- 기본 규칙의 `transition: background 0.2s` 가 있어 색이 툭 바뀌지 않고 0.2초 동안 이어서 바뀐다.
- `cursor: pointer` 는 버튼 위에서 마우스 모양을 손가락으로 바꾼다.

> **의사 클래스(pseudo-class)** — 요소의 상태(마우스가 올라감 등)에 따라 맞는 선택자. 콜론 하나(`:`)를 붙인다.\
> 예: `:hover` 는 마우스 포인터가 올라가 있는 동안 맞는다.

```html demo
<input type="file" class="file-input" />
<style>
  .file-input { font-size: 14px; }
  .file-input::file-selector-button {
    padding: 10px 20px; background: #3b82f6; color: white;
    border: none; border-radius: 8px; cursor: pointer;
    margin-right: 12px; transition: background 0.2s;
  }
  .file-input::file-selector-button:hover { background: #1d4ed8; }
</style>
```

> **보이는 것** — 둥근 모서리의 파란 버튼과 그 오른쪽에 조금 떨어진 파일 이름 글자, 버튼에 마우스를 올리면 버튼만 진한 파랑으로 서서히 바뀜 (코드에서 읽은 것 — 렌더 실측 아님)

## 문법 — 형태와 규칙

```css
/* 입력 요소 전체 */
input[type="file"] { font-size: 14px; }

/* 입력 안의 버튼 부분 */
input[type="file"]::file-selector-button {
  border: none;          /* 브라우저 기본 테두리를 없앤다 */
  padding: 8px 16px;
  cursor: pointer;
}

/* 버튼 위에 마우스가 있을 때 */
input[type="file"]::file-selector-button:hover {
  background: #e5e7eb;
}
```

- 원본 문법은 `input[type="file"]::file-selector-button { }` 이다.
- 앞부분은 파일 입력을 고르는 아무 선택자여도 된다 — 원본 예제는 클래스 `.file-input` 을 쓴다.
- 의사 요소 이름 앞에는 콜론 두 개 `::` 를 쓴다.
- 상태를 붙일 때는 의사 요소 뒤에 `:hover` 를 붙인다.
- 기본 모양을 지우고 새로 칠하려면 `border: none` 처럼 브라우저 기본값부터 덮어쓴다.

> **속성 선택자** — 속성 값으로 요소를 고르는 선택자.\
> 예: `input[type="file"]` 은 `type` 이 `file` 인 `<input>` 만 고른다.

## 어디서 틀리나

### 1. 기본 버튼은 브라우저마다 다르게 보인다

원본 팁 그대로, 손대지 않은 파일 입력 버튼은 브라우저마다 모양이 다르다.
`::file-selector-button` 으로 테두리 · 배경 · 여백 · 모서리를 직접 정해 주면 통일된 모양을 얻는다.
기본 테두리 같은 값을 `border: none` 으로 먼저 지우지 않으면 브라우저 기본 모양이 섞여 남을 수 있다.

### 2. 버튼에 클래스를 달려고 한다

버튼은 HTML 에 태그로 없으니 `class` 를 붙일 자리가 없다.
버튼을 꾸미는 길은 입력 요소를 고른 뒤 `::file-selector-button` 으로 좁히는 것뿐이다.

### 3. 입력 요소 규칙과 버튼 규칙을 헷갈린다

`.file-input { background: … }` 은 버튼이 아니라 입력 요소 상자를 칠한다.
버튼 색을 바꾸려면 반드시 `::file-selector-button` 규칙에 쓴다.
반대로 파일 이름 글자의 크기는 입력 요소 규칙에서 정한다.

### 4. 파일 입력이 아닌 요소에 쓴다

이 의사 요소는 파일 입력 안의 버튼을 가리킨다.
`<input type="text">` 처럼 버튼 부분이 없는 요소에 써도 고를 것이 없어 아무 일도 일어나지 않는다.

### 5. `:hover` 를 붙이는 자리를 바꾼다

`.file-input:hover::file-selector-button` 은 「입력 요소 어디든 마우스가 올라가면 버튼을 바꾼다」는 뜻이 된다.
버튼 위에 있을 때만 바꾸려면 `.file-input::file-selector-button:hover` 처럼 의사 요소 뒤에 붙인다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 기본 파일 선택 버튼의 모양 | 브라우저마다 다르다 — 구현 세부사항(원본 팁) |
| `::file-selector-button` 이 파일 입력의 버튼 부분을 가리킨다 | CSS 명세 |
| 버튼 옆에 나오는 파일 이름 문구(「선택된 파일 없음」 등)의 글귀 | 브라우저 · 언어 설정에 따른다 — 구현 세부사항 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 파일 선택 버튼을 사이트 버튼과 같은 모양으로 | `::file-selector-button` | 버튼에 클래스 달기(불가능) |
| 버튼 옆 파일 이름 글자의 크기 | 입력 요소 규칙(`.file-input`) | 버튼 규칙 |
| 버튼 위 마우스 반응 | `::file-selector-button:hover` | `.file-input:hover`(입력 전체에 반응) |
| 글자 입력칸 꾸미기 | 입력 요소 선택자 | `::file-selector-button`(고를 버튼이 없다) |

## 핵심 문장

1. **`::file-selector-button` 은 파일 입력 안의, 브라우저가 그린 버튼 부분만 고른다.**
2. **입력 요소 규칙은 파일 이름 글자 쪽을, 의사 요소 규칙은 버튼 쪽을 맡는다.**
3. **상태는 의사 요소 뒤에 붙인다** — `::file-selector-button:hover`.
4. **기본 버튼은 브라우저마다 다르므로 직접 스타일을 줘 통일한다.**

## 관련 자료

- `::placeholder` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/selectors.json` 의 `file-selector-button`

## 용어 풀이

- **의사 요소** — 태그로 없지만 CSS 가 상자처럼 고를 수 있는 요소의 한 부분, `::` 로 쓴다.
- **의사 클래스** — 요소의 상태에 따라 맞는 선택자, `:` 로 쓴다.
- **`:hover`** — 마우스 포인터가 올라가 있는 동안 맞는 의사 클래스.
- **속성 선택자** — `[type="file"]` 처럼 속성 값으로 요소를 고르는 선택자.
- **`transition`** — 속성 값이 바뀔 때 정한 시간 동안 이어서 바뀌게 하는 속성.
- **`cursor: pointer`** — 그 위에서 마우스 모양을 손가락으로 바꾼다.
- **`margin-right`** — 상자 오른쪽 바깥의 빈자리.

## 더 들어가면

- 예전 WebKit 계열 브라우저는 같은 부분을 `::-webkit-file-upload-button` 이라는 접두사 이름으로 불렀다 (확인 필요).
- `::before` 같은 오래된 의사 요소는 콜론 하나로도 통하지만, `::file-selector-button` 은 콜론 둘로만 쓰는 것이 안전하다 (확인 필요).
- 의사 요소 뒤에 붙일 수 있는 의사 클래스는 `:hover` 같은 사용자 동작 계열로 한정된다 (확인 필요).
- 버튼을 아예 숨기고 `<label>` 을 버튼처럼 꾸며 파일 입력과 연결하는 방법도 널리 쓰인다 (확인 필요).
