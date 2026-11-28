# css/units-values/26 — env() — 정리 (힌트)

> 출처 — study-site 항목 `css/env`(항목 데이터 `data/css/units-values.json`) · 정답 코드 study-practice `css/units-values/reference/env.html`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 브라우저 화면에서 결과를 보는 예제다 — 글로 옮길 출력이 없다.

## 한눈에 — 쉽게 말하면

**`env()` 는 「건물 관리실에 붙은 안내판의 숫자를 읽어 오는 것」이다.**
가게(웹 페이지)는 건물(기기 화면)의 기둥이나 계단 위치를 스스로 정할 수 없다.
관리실(브라우저)이 「입구 쪽 기둥 폭은 얼마」처럼 안내판에 적어 두면, 가게는 그 숫자만큼 진열대를 안쪽으로 들여 놓는다.
안내판에 그 항목이 없으면 가게가 미리 정한 기본 폭(fallback)을 쓴다.
CSS 의 `env()` 도 똑같은 구조다.
브라우저가 정의해 둔 환경 변수를 이름으로 읽어 와서 속성 값으로 쓴다.

| 비유 | 실체 |
|---|---|
| 건물 관리실 | 사용자 에이전트(브라우저) |
| 안내판의 항목 이름 | 환경 변수 이름 (`safe-area-inset-top` 등) |
| 안내판에 적힌 숫자 | 그 변수의 값 (길이) |
| 기둥 · 계단 | 노치 · 둥근 모서리 · 홈 표시줄 |
| 가게가 미리 정한 기본 폭 | `env()` 의 두 번째 인자(fallback) |

```text
  브라우저(관리실)                      CSS(가게)
  ┌───────────────────────────┐        padding-top: env(safe-area-inset-top, 44px);
  │ safe-area-inset-top    = ?│ ──읽기──▶          │
  │ safe-area-inset-bottom = ?│                    ▼
  │ safe-area-inset-left   = ?│        정의돼 있으면 그 값, 없으면 44px
  │ safe-area-inset-right  = ?│
  └───────────────────────────┘
```

> **사용자 에이전트** — 사용자를 대신해 웹 페이지를 받아 그려 주는 프로그램이다.\
> 예: Chrome, Safari 같은 브라우저.

## 이 주제가 답하려는 질문

1. 페이지가 스스로 알 수 없는 기기 정보(노치에 가리는 폭 등)를 CSS 값으로 어떻게 가져오나?
2. 그 정보가 없을 때는 어떤 값이 쓰이나?
3. 가져온 값이 너무 작거나 0일 때 최소 여백은 어떻게 지키나?

## 동작 방식

### (1) `env()` 가 값을 고르는 차례

**언제 쓰나** — 브라우저가 알려 주는 값을 속성 값 자리에 넣고 싶을 때 쓴다.
그 값이 없을 경우를 대비해 기본값을 함께 적는다.

```text
padding-top: env(safe-area-inset-top, 44px);
        │
        ▼
브라우저가 safe-area-inset-top 을 정의하고 있나?
   ├─ 예  ──▶ 그 값을 쓴다 (0px 이어도 그 0px 을 쓴다)
   └─ 아니오 ─▶ 두 번째 인자 44px 을 쓴다
        │
        ▼
padding-top 의 계산된 값 결정
```

- 첫째 줄은 변수 이름과 fallback 을 함께 적은 선언이다.
- 브라우저는 먼저 그 이름의 환경 변수가 정의돼 있는지 본다.
- 정의돼 있으면 값의 크기와 상관없이 그 값을 쓴다.
- 정의돼 있지 않을 때만 fallback 이 쓰인다.
- fallback 은 「값이 작을 때의 최소값」이 아니라 「변수가 없을 때의 대체값」이다.

> **fallback** — 원래 값을 얻지 못했을 때 대신 쓰는 값이다.\
> 예: `env(safe-area-inset-left, 16px)` 의 `16px`.

### (2) safe-area-inset 네 변수와 `viewport-fit=cover`

**언제 쓰나** — 노치나 둥근 모서리가 있는 모바일 화면에서 콘텐츠가 가려지지 않게 할 때 쓴다.

```text
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
        │  페이지가 화면 가장자리(노치 아래까지)를 덮겠다고 알린다
        ▼
┌──────[ 노치 ]──────┐  ◀─ safe-area-inset-top    : 가려지는 위쪽 폭
│                    │
│   안전 영역(safe)   │  ◀─ inset-left / inset-right : 둥근 모서리 · 가로 모드의 노치
│                    │
└────[ 홈 표시줄 ]────┘  ◀─ safe-area-inset-bottom : 가려지는 아래쪽 폭
        │
        ▼
padding 에 env(safe-area-inset-*) 을 넣어 콘텐츠를 안전 영역 안으로 민다
```

- meta 태그의 `viewport-fit=cover` 는 페이지가 화면 전체를 덮겠다는 선언이다.
- 이렇게 하면 페이지의 가장자리가 노치 · 홈 표시줄 밑까지 들어간다.
- 그래서 가려지는 폭만큼 안쪽으로 밀어 줄 값이 필요해지고, 그 값이 네 `safe-area-inset-*` 변수다.
- `padding` 에 그 값을 넣으면 배경은 화면 끝까지 칠해지고 글자는 안전 영역 안에 남는다.
- 원본의 팁대로 `env()` 는 이 meta 태그와 함께 써야 동작한다 — 이 선언이 없으면 페이지가 처음부터 안전 영역 안에만 놓여 밀어 줄 폭이 생기지 않는다(원본에 근거 없음 — 추론).

> **safe area(안전 영역)** — 화면에서 노치 · 둥근 모서리 · 시스템 표시줄에 가리지 않는 사각형 부분이다.\
> 예: 노치 아래부터 홈 표시줄 위까지.

> **`viewport-fit`** — 페이지를 안전 영역 안에만 놓을지, 화면 전체를 덮을지 정하는 viewport meta 의 항목이다.\
> 예: `viewport-fit=cover`.

### (3) `min()` · `max()` · `calc()` 와 묶기

**언제 쓰나** — 안전 영역 값이 0일 때도 최소 여백을 지키거나, 그 값에 여백을 더 얹고 싶을 때 쓴다.

```text
padding-left: max(16px, env(safe-area-inset-left));

  inset-left = 0px   ──▶ max(16px, 0px)  ──▶ 16px
  inset-left = 44px  ──▶ max(16px, 44px) ──▶ 44px
```

- `env()` 는 길이를 돌려주므로 `max()` 의 인자로 넣을 수 있다.
- 안전 영역 값이 0이면 `max()` 가 16px 을 골라 최소 여백이 남는다.
- 안전 영역 값이 16px 보다 크면 그 값이 골라져 노치를 피한다.
- `calc(env(safe-area-inset-bottom) + 12px)` 처럼 더해서 「가려지는 폭 + 내 여백」을 만들 수도 있다.

## 문법 — 형태와 규칙

```html demo
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
  .bar {
    background: #1e293b;
    color: white;
    padding-top: env(safe-area-inset-top, 20px);
    padding-left: max(16px, env(safe-area-inset-left));
    padding-right: max(16px, env(safe-area-inset-right));
    padding-bottom: calc(env(safe-area-inset-bottom, 0px) + 12px);
  }
</style>
<div class="bar">상단 막대</div>
```

> **보이는 것** — 어두운 막대 안에 흰 글자가 놓이고, 좌우로는 최소 16px, 아래로는 최소 12px 여백이 생긴다. 위 여백은 브라우저가 정의한 위쪽 inset 값이며, 그 변수가 없을 때만 20px 이다 (코드에서 읽은 것 — 렌더 실측 아님)

| 부분 | 뜻 |
|---|---|
| `env(` … `)` | 환경 변수를 읽는 함수 |
| `<variable>` | 브라우저가 정의한 변수 이름 — 따옴표 없이 쓴다 |
| `, <fallback>` | 생략 가능. 변수가 정의돼 있지 않을 때 쓸 값 |
| `safe-area-inset-top` | 위쪽 안전 영역 폭 |
| `safe-area-inset-right` | 오른쪽 안전 영역 폭 |
| `safe-area-inset-bottom` | 아래쪽 안전 영역 폭 |
| `safe-area-inset-left` | 왼쪽 안전 영역 폭 |

- 변수 이름은 브라우저가 정한다 — 작성자가 새 이름을 만들어 쓰는 함수가 아니다.
- fallback 은 생략할 수 있다: `env(safe-area-inset-top)`.
- `env()` 는 값 자리에 쓰므로 `max()` · `min()` · `calc()` 안에 넣을 수 있다.
- 네 방향은 각각 따로 읽는다 — 한 번에 네 값을 돌려주는 변수는 없다.

## 어디서 틀리나

### 1. meta 태그 없이 `env()` 만 쓴다

원본 팁: `viewport-fit=cover` 메타 태그와 함께 써야 동작한다.
meta 태그가 없으면 페이지가 안전 영역 안에만 그려져서 `env()` 로 밀어 줄 여백이 생기지 않는다.
CSS 만 고치고 「노치 대응이 안 된다」고 헤매는 흔한 경우다.

### 2. fallback 을 「최소값」으로 오해한다

fallback 은 변수가 **정의돼 있지 않을 때만** 쓰인다.
변수가 0px 으로 정의돼 있으면 결과는 0px 이다.
최소 여백을 지키려면 원본 팁처럼 `max(16px, env(safe-area-inset-left))` 로 쓴다.

**원본의 주장 → 왜 의심스러운가**
원본 정답 코드의 주석은 `env(safe-area-inset-top, 44px)` 를 「없으면 44px」로 설명한다.
그러나 `safe-area-inset-*` 를 정의해 두는 브라우저라면, 노치가 없는 사각형 화면에서는 그 값이 0으로 정의된다는 설명이 있다(확인 필요).
그렇다면 일반 데스크톱 브라우저에서 이 데모의 위 여백은 44px 이 아니라 0일 수 있다.
「없으면」은 「변수가 정의되지 않았으면」으로 읽어야 한다.

### 3. `env()` 를 아예 모르는 옛 브라우저

`env()` 를 해석하지 못하는 브라우저에서는 그 선언 전체가 버려진다.
이때 fallback 도 함께 버려지므로, fallback 이 옛 브라우저를 구해 주지 않는다.
대비하려면 `env()` 선언 **앞에** 평범한 값을 한 줄 먼저 적어 둔다(확인 필요).

### 4. `var()` 처럼 직접 정의하려 한다

`env()` 의 변수는 브라우저가 정의한 것이다.
`--my-gap` 처럼 작성자가 만든 사용자 정의 속성은 `var()` 로 읽는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `env(<variable>, <fallback>?)` 문법, 변수가 없을 때 fallback 사용 | CSS 명세 (CSS Environment Variables) |
| `safe-area-inset-*` 네 변수의 실제 값(몇 px 인지) | 기기 · 브라우저 — 화면 모양에 따라 다르다 |
| 사각형 화면에서 inset 값이 0으로 정의됨 | 명세의 설명으로 알려져 있으나 브라우저마다 확인 필요(확인 필요) |
| `viewport-fit=cover` 가 있어야 inset 이 의미를 가짐 | viewport meta 를 처리하는 브라우저의 동작 (원본 팁) |
| 모르는 함수가 든 선언은 버려짐 | CSS 의 일반 파싱 규칙 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 노치 · 홈 표시줄이 있는 화면에서 콘텐츠 보호 | `viewport-fit=cover` + `padding: env(safe-area-inset-*)` | 기기별 고정 px |
| 노치가 없어도 최소 여백 유지 | `max(16px, env(safe-area-inset-left))` | fallback 만 믿기 |
| 「가려지는 폭 + 내 여백」 | `calc(env(...) + 12px)` | inset 을 무시한 고정 값 |
| 작성자가 정한 값을 재사용 | `var(--이름)` | `env()` |

## 핵심 문장

1. **`env()` 는 브라우저가 정의한 환경 변수를 읽어 속성 값으로 쓰는 함수다.**
2. **fallback 은 변수가 정의되지 않았을 때만 쓰인다** — 값이 0이어도 그 0이 쓰인다.
3. **안전 영역 대응은 `viewport-fit=cover` meta 태그와 짝이다.**
4. **최소 여백은 `max()` 로 지킨다** — `max(16px, env(safe-area-inset-left))`.

## 관련 자료

- `var` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `max` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `calc` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/css/units-values.json` 의 `env`
## 용어 풀이

- **사용자 에이전트** — 페이지를 받아 그려 주는 프로그램, 곧 브라우저.
- **환경 변수(`env()` 의)** — 브라우저가 정의해 두고 CSS 가 이름으로 읽는 값.
- **fallback** — 변수가 정의되지 않았을 때 대신 쓰는 값.
- **safe area(안전 영역)** — 노치 · 둥근 모서리 · 시스템 표시줄에 가리지 않는 화면 부분.
- **노치** — 화면 위쪽에 카메라 등을 위해 파인 부분.
- **`safe-area-inset-*`** — 화면 가장자리에서 안전 영역까지의 네 방향 폭.
- **`viewport-fit=cover`** — 페이지가 화면 전체를 덮겠다고 알리는 viewport meta 항목.
- **`max()` / `min()`** — 인자 가운데 가장 큰 / 가장 작은 값을 고르는 CSS 함수.
- **사용자 정의 속성** — `--이름` 으로 작성자가 만드는 속성, `var()` 로 읽는다.

## 더 들어가면

- 명세에는 `safe-area-inset-*` 말고도 다른 환경 변수(예: 키보드 영역 · 창 제목 표시줄 관련)가 제안 · 추가돼 왔다(확인 필요).
- `env()` 는 `var()` 와 달리 상속 · 캐스케이드를 따르지 않고 문서 전체에서 같은 값을 돌려준다(확인 필요).
- 명세는 `env()` 를 미디어 쿼리 안에서도 쓸 수 있게 의도했지만 지원은 제한적일 수 있다(확인 필요).
- `env()` 를 지원하는 브라우저에서 변수가 없고 fallback 도 없으면 선언이 계산 시점에 무효가 되어 `unset` 처럼 처리된다(확인 필요).
- iOS Safari 의 초기 버전은 `constant()` 라는 이름으로 같은 기능을 먼저 제공했다(확인 필요).
