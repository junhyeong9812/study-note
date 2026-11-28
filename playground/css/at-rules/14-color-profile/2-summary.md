# css/at-rules/14 — @color-profile — 정리 (힌트)

> 출처 — study-site 항목 `css/color-profile`(항목 데이터 `data/css/at-rules.json`) · 정답 코드 study-practice `css/at-rules/reference/color-profile.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`@color-profile` 은 「물감 회사의 색 견본표를 미리 등록해 두는 일」이다.**
같은 「빨강 0.8」이라도 어느 회사 견본표로 읽느냐에 따라 실제 색이 달라진다.
그래서 화가는 먼저 「이 그림은 ○○사 견본표로 칠한다」고 정해 두고, 그 견본표의 번호로 색을 부른다.
CSS 도 똑같은 구조다.
`@color-profile` 로 ICC 파일(견본표)에 이름을 붙여 등록하고, `color()` 함수에서 그 이름과 숫자로 색을 부른다.

> **ICC 프로파일** — 어떤 색 공간에서 숫자가 실제로 어떤 색을 뜻하는지 적어 둔 표준 파일이다.\
> 예: `Display-P3.icc` 는 Display P3 색 공간의 정의를 담는다.

> **색 공간** — 색을 숫자로 나타낼 때 그 숫자가 가리키는 실제 색의 범위와 기준이다.\
> 예: `srgb` · `display-p3` · `rec2020`.

| 비유 | 실체 |
|---|---|
| 물감 회사의 견본표 | ICC 프로파일 파일 |
| 견본표 등록 | `@color-profile --이름 { src: url(…); }` |
| 「○○사 견본표의 3번 물감」 | `color(--이름 숫자…)` |
| 원래 화방에 걸려 있는 기본 견본표 | 내장 색 공간 `display-p3` · `srgb` · `rec2020` |

```text
  ICC 파일 ──(src)──▶ @color-profile --my-space   ← 이름 붙여 등록
                              │
                              ▼
            background: color(--my-space 0.2 0.5 1)   ← 이름으로 불러 씀
```

## 이 주제가 답하려는 질문

1. sRGB 보다 넓은 색 영역(wide gamut)의 색을 CSS 에서 어떻게 지정하나?
2. `@color-profile` 로 만든 색 공간은 어떻게 정의되고 어디서 쓰이나?
3. ICC 파일을 직접 불러오는 것과 내장 색 공간을 쓰는 것 중 무엇이 실용적인가?

> **넓은 색 영역(wide gamut)** — 일반 sRGB 가 담지 못하는 더 선명한 색까지 포함하는 색 범위다.\
> 예: Display P3 는 sRGB 보다 더 진한 빨강 · 초록을 담는다.

## 동작 방식

### (1) 정의 — ICC 파일에 이름을 붙인다

**언제 쓰나** — 내장 색 공간에 없는 특정 색 공간(인쇄용 프로파일 등)으로 색을 지정해야 할 때 쓴다.

```text
@color-profile --brand { src: url('brand.icc'); }
        │                       │
        │                       └─ 프로파일 파일 위치
        └─ 이 이름(-- 로 시작)으로 새 색 공간이 생긴다
        ↓
결과: 아직 화면에는 아무 변화도 없다 (등록만 됨)
```

- `@color-profile` 뒤에 `--` 로 시작하는 이름을 쓴다.
- 블록 안의 `src` 가 ICC 파일 경로를 가리킨다.
- 이 규칙은 색 공간을 「정의」할 뿐이고, 어떤 요소의 색도 직접 바꾸지 않는다.

> **at-규칙(at-rule)** — `@` 로 시작해 스타일시트에 특별한 지시를 내리는 CSS 문장이다.\
> 예: `@media` · `@font-face` · `@color-profile`.

### (2) 사용 — `color()` 에서 이름으로 부른다

**언제 쓰나** — 정의한 색 공간 또는 내장 색 공간의 숫자로 실제 색을 칠할 때 쓴다.

```text
background: color(--brand 0.2 0.5 1)
                    │      └──┬──┘
                    │         └─ 그 색 공간에서의 채널 값
                    └─ (1)에서 등록한 이름과 글자 그대로 같아야 한다
        ↓
결과: brand 색 공간 기준의 색으로 배경이 칠해진다
```

- `color()` 의 첫 자리에 색 공간 이름이 온다.
- 이름이 `--brand` 면 `@color-profile --brand` 로 정의한 색 공간을 쓴다.
- 이름이 `display-p3` 처럼 `--` 없이 오면 브라우저에 미리 들어 있는 내장 색 공간을 쓴다.
- 그래서 `--display-p3` 과 `display-p3` 은 서로 다른 이름이다.

### (3) 숫자의 뜻은 색 공간이 정한다

**언제 쓰나** — 같은 숫자를 다른 색 공간으로 바꿔 쓸 때 결과를 예상해야 할 때 생각한다.

```text
color(srgb       0.2 0.5 1)  ─┐
                              ├─ 숫자는 같지만 기준표가 다르다
color(display-p3 0.2 0.5 1)  ─┘
        ↓
결과: 두 색은 같은 색이 아니다
```

- 채널 값 `0.2 0.5 1` 은 「그 색 공간의 빨강 · 초록 · 파랑 성분 비율」이다.
- 기준이 되는 색 공간이 넓으면 같은 숫자라도 더 진한 색을 가리킬 수 있다.
- 원본 예제의 `color(display-p3 0.2 0.5 1)` 은 Display P3 기준의 파란색이다.

```html demo
<div style="padding:20px; background: color(display-p3 0.2 0.5 1); color:white; font-weight:bold;">P3</div>
<div style="padding:20px; background: color(srgb 0.2 0.5 1); color:white; font-weight:bold;">sRGB</div>
```

> **보이는 것** — 파란 상자 두 개가 위아래로 놓이고, 넓은 색 영역 화면에서는 위 상자가 조금 더 진해 보일 수 있다 (코드에서 읽은 것 — 렌더 실측 아님)

### (4) `rendering-intent` — 담기지 않는 색을 어떻게 맞추나

**언제 쓰나** — 프로파일의 색이 목표 영역에 다 담기지 않을 때 어떤 방식으로 맞출지 정하고 싶을 때 쓴다.

```text
@color-profile --brand {
  src: url('brand.icc');
  rendering-intent: perceptual;   ← 색을 옮기는 방식
}
        ↓
결과: 색을 변환할 때 지정한 방식(relative-colorimetric, perceptual 등)을 따른다
```

- `rendering-intent` 는 색상 렌더링 방식을 고르는 설명자다.
- 원본이 드는 값은 `relative-colorimetric` · `perceptual` 등이다.

## 문법 — 형태와 규칙

```css
/* 1) 정의: ICC 파일에 이름을 붙인다 */
@color-profile --print-space {
  src: url('print.icc');
  rendering-intent: relative-colorimetric;
}

/* 2) 사용: 정의한 이름으로 색을 부른다 */
.label { color: color(--print-space 0.1 0.3 0.8); }

/* 3) 내장 색 공간은 정의 없이 바로 쓴다 */
.box { background: color(display-p3 0.2 0.5 1); }
```

- 꼴: `@color-profile --<name> { src: url(<icc-file>); }`
- 이름은 `--` 로 시작한다.
- 이 규칙은 정의만 하고, 쓰임은 `color(--<name> …)` 에서 일어난다.

| 설명자 | 뜻 | 값 |
|---|---|---|
| `src` | ICC 프로파일 파일 경로 | `url(…)` |
| `rendering-intent` | 색상 렌더링 방식 | `relative-colorimetric` · `perceptual` 등 |

## 어디서 틀리나

### 1. 정의한 이름과 쓰는 이름이 다르다

원본 예제는 주석 속에서 `@color-profile --display-p3` 을 정의하지만, 실제 배경은 `color(display-p3 …)` 로 내장 색 공간을 부른다.
`--` 가 없으므로 주석을 풀어도 배경은 그 프로파일을 쓰지 않는다.
직접 정의한 색 공간을 쓰려면 `color(--display-p3 …)` 처럼 `--` 까지 똑같이 적어야 한다.

### 2. 정의만 하고 화면이 바뀌기를 기대한다

`@color-profile` 은 색 공간을 등록할 뿐이다.
`color()` 에서 그 이름을 부르는 선언이 없으면 화면에는 아무 차이가 없다.

### 3. ICC 파일을 굳이 불러온다 (원본의 팁)

ICC 프로파일을 직접 로드하는 대신 CSS 의 내장 색 공간(`display-p3`, `srgb`, `rec2020` 등)과 `color()` 함수를 쓰는 것이 더 실용적이다.
내장 색 공간은 파일을 내려받을 필요도, 경로가 맞는지 신경 쓸 필요도 없다.
원본 예제도 이 팁대로 `@color-profile` 은 주석으로 남기고 내장 `display-p3` 을 쓴다.

### 4. 예시 주소를 그대로 둔다

원본의 `https://example.com/Display-P3.icc` 는 개념을 보이기 위한 자리표시용 주소다.
실제로 쓰려면 진짜 ICC 파일 경로로 바꿔야 한다.

### 5. 같은 숫자면 같은 색이라고 여긴다

`color(srgb 0.2 0.5 1)` 과 `color(display-p3 0.2 0.5 1)` 은 숫자만 같다.
숫자의 뜻은 색 공간이 정하므로 색이 다르다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `color()` 의 첫 자리 이름으로 색 공간이 정해진다 | CSS 명세 |
| `@color-profile` 로 정의한 이름은 `--` 로 시작한다 | CSS 명세 (원본 문법) |
| P3 색이 화면에서 더 선명하게 보인다 | 화면 하드웨어와 브라우저 — 넓은 영역을 못 내는 화면에서는 차이가 없을 수 있다 |
| `color(display-p3 0.2 0.5 1)` 은 sRGB 영역을 넘는 파랑이다 (원본 주석) | 원본의 주장 → P3 의 파랑 기준점은 sRGB 와 거의 같아서, 이 색이 sRGB 밖으로 얼마나 나가는지는 계산해 봐야 한다 (확인 필요) |
| `@color-profile` 을 브라우저가 실제로 처리한다 | 브라우저 구현 — 지원 범위는 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 넓은 영역의 선명한 색을 쓰고 싶다 | `color(display-p3 …)` · `color(rec2020 …)` | 굳이 P3 용 ICC 파일 로드 |
| 내장 목록에 없는 특정 프로파일이 꼭 필요하다 | `@color-profile --이름` + `color(--이름 …)` | 내장 색 공간으로 흉내 내기 |
| 일반적인 웹 색 | `#hex` · `rgb()` · `color(srgb …)` | `@color-profile` |

## 핵심 문장

1. **`@color-profile` 은 ICC 파일에 `--이름` 을 붙여 새 색 공간을 정의한다** — 그 자체로는 아무것도 칠하지 않는다.
2. **정의한 색 공간은 `color(--이름 …)` 에서 쓰인다** — `--` 가 빠지면 내장 색 공간을 가리킨다.
3. **`color()` 의 숫자는 색 공간에 따라 뜻이 달라진다.**
4. **대부분은 내장 색 공간(`display-p3` · `srgb` · `rec2020`)과 `color()` 로 충분하고 더 실용적이다.**

## 관련 자료

- `color()` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/at-rules.json` 의 `color-profile`

## 용어 풀이

- **at-규칙** — `@` 로 시작하는 CSS 지시문이다.
- **ICC 프로파일** — 색 공간의 정의를 담은 표준 파일이다.
- **색 공간** — 색 숫자가 가리키는 실제 색의 범위와 기준이다.
- **넓은 색 영역(wide gamut)** — sRGB 보다 넓은 색 범위다.
- **`color()` 함수** — 색 공간 이름과 채널 값으로 색을 지정하는 CSS 함수다.
- **`src`** — ICC 파일 경로를 적는 설명자다.
- **`rendering-intent`** — 색을 옮길 때 렌더링 방식을 고르는 설명자다.
- **설명자(descriptor)** — at-규칙 블록 안에서만 쓰이는 이름-값 쌍이다.

## 더 들어가면

- `rendering-intent` 에는 `perceptual` · `relative-colorimetric` 말고도 `saturation` · `absolute-colorimetric` 이 있다 (확인 필요).
- 목표 화면이 담지 못하는 색은 브라우저가 담을 수 있는 가까운 색으로 맞춘다(gamut mapping) — 방식은 브라우저마다 다를 수 있다 (확인 필요).
- 이름 자리에 `--` 이름 말고 `device-cmyk` 를 쓰는 형태도 명세에 있다 (확인 필요).
- 미디어 쿼리 `@media (color-gamut: p3)` 로 넓은 영역 화면에서만 P3 색을 쓰게 나눌 수 있다 (확인 필요).
