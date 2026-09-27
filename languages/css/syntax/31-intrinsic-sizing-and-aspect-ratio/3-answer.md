# css/syntax/31 — 내재적 크기(`min-content`/`max-content`/`fit-content`)와 `aspect-ratio` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 치수는 Google Chrome 151.0.7922.173 headless 에서 실제로 렌더해 `getBoundingClientRect()` 로 잰 값**이다. 단위는 px, 글꼴은 별말이 없으면 `16px monospace` 다.\
> **선언이 담겼는지**는 `document.styleSheets[…].cssRules` 로 따로 확인했다 — 계산값만 읽으면 「안 쓴 것」과 「썼는데 버려진 것」이 구분되지 않기 때문이다.\
> 규칙은 [CSS Box Sizing Level 3](https://drafts.csswg.org/css-sizing-3/)·[Level 4](https://drafts.csswg.org/css-sizing-4/) 로, 지원 상태는 `api.webstatus.dev` 의 Baseline 데이터로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 같은 글, 네 가지 폭

**실행 결과** (Chrome 151 headless — 글 `hi javascript ok`, 부모 400px)

```text
선언                  폭        높이
width: min-content    80.00    72.00     세 줄로 접혔다
width: max-content   128.02    24.00     한 줄
width: fit-content   128.02    24.00     한 줄
width: auto          400.00    24.00     부모를 채웠다

부모를 80px 로 줄인 판
width: fit-content    80.00    48.00     두 줄
width: auto           80.00    48.00     두 줄

낱말 폭을 따로 재면  "hi"=16.02  "javascript"=80.02  "ok"=16.02  전체=128.02
```

**큰 순서**

- **`auto`(400.00) > `max-content` = `fit-content`(128.02) > `min-content`(80.00).**
- 단 `auto` 가 가장 큰 것은 **이 부모가 넓기 때문**이다. 부모가 80px 면 `auto` 가 가장 작아진다.

**`.a` 의 줄 수**

- **세 줄**(`hi` / `javascript` / `ok`). 높이 72.00 = 24 × 3.

**`.c` 와 `.b` 의 폭이 같은 이유**

- `fit-content` = `min(max-content, max(min-content, 쓸 수 있는 공간))` 이고,\
  **쓸 수 있는 공간(400)이 `max-content`(128.02)보다 커서** 공식이 `max-content` 에서 잘린다.

**부모를 80px 로 줄이면**

- `min-content` 80.00(그대로 — **내재적이라 부모와 무관**) · `max-content` 128.02(그대로, **부모를 뚫는다**)
- `fit-content` **80.00**(공간이 둘 사이라 공간 값이 된다) · `auto` **80.00**(부모를 채운다)
- ★ **부모를 바꿨을 때 안 움직이는 둘이 내재적 크기**다. 이 실험이 내재적/외재적의 정의를 그대로 보여 준다.

### 2. `fit-content` 의 공식

**공식**

```text
fit-content = min( max-content , max( min-content , 쓸 수 있는 공간 ) )
```

**`max-content` 보다 커질 수 있는가**

- **없다.** 바깥 `min()` 이 `max-content` 에서 자른다. 「내용보다 넓어지지 않는 상자」가 이 값의 쓸모다.

**`min-content` 보다 작아질 수 있는가**

- **없다.** 안쪽 `max()` 가 `min-content` 를 바닥으로 삼는다. 부모가 그보다 좁으면 **뚫는다.**

**부모 크기에 영향받는 것**

- **`fit-content` 하나뿐이다.** `min-content`·`max-content` 는 내재적이라 부모가 바뀌어도 그대로다(1번의 80px 판이 그 근거다).

### 3. `min-content` 를 정하는 것

**실행 결과** (Chrome 151 headless — 각각 `width: min-content` 상자에 담아 쟀다)

```text
① "hi javascript ok"                       min-content =  80.00   (높이 72 — 세 줄)
② "hi flex-basis ok"                       min-content =  40.00   (높이 96 — 네 줄)
③ <pre>GET /api/v1/users/12345/preferences</pre>
                                           min-content = 280.02
                                           max-content = 280.02

조각 폭을 따로 재면
  "javascript" = 80.02      "flex-" = 40.02      "basis" = 40.02
```

**셋의 `min-content` 와 기준 조각**

- ① **80.00** — 가장 긴 낱말 `javascript`.
- ② **40.00** — 낱말이 아니라 **`flex-`**(또는 `basis`).
- ③ **280.02** — 조각이 아니라 **한 줄 전체**.

**②가 ①보다 작은 이유**

- **하이픈이 줄바꿈 기회이기 때문**이다. `flex-basis` 는 `flex-` 와 `basis` 로 쪼개진다.
- 그래서 네 줄(`hi` / `flex-` / `basis` / `ok`)이 됐고 높이가 96 이다.

**③의 두 값이 같은 이유**

- `<pre>` 는 `white-space: pre` 라 **줄바꿈 기회가 하나도 없다.** 쪼갤 수 없으니 접어도 편 것과 같다.
- ★ **`min-content` = `max-content` 는 「쪼갤 수 없다」의 신호**다. [25번](../25-flex-shorthand-and-sizing/)의 사고를 진단하는 가장 빠른 방법이다.

**「가장 긴 낱말」이 틀리는 두 경우**

1. **하이픈·구두점에서 쪼개지는 경우**(②) — 실제 `min-content` 가 더 작다.
2. **줄바꿈 기회가 없는 경우**(③, `white-space: pre`/`nowrap`) — 훨씬 크다.
- 덧붙여, 글이 아닌 것(이미지·인라인 블록·표)이 섞이면 **낱말이 아닌 것이 최댓값**이 될 수도 있다.

### 4. ★ 25번의 사고가 여기서 풀린다

**실행 결과** (Chrome 151 headless — 같은 `<div>` 를 세 문맥에 넣고 계산값을 읽었다)

```text
flex 항목    min-width = auto   min-height = auto
grid 항목    min-width = auto   min-height = auto
블록 자식     min-width = 0px    min-height = 0px
```

**세 기본값**

- 블록 자식 **`0px`** · flex 항목 **`auto`** · grid 항목 **`auto`**.

**flex 항목에서 `auto` 가 풀리는 값**

- **자동 최소 크기** — 대개 **`min-content`** 다.
- 다만 **`overflow` 가 `visible` 이 아니면 적용되지 않는다**([25번](../25-flex-shorthand-and-sizing/) 10번의 실측).

**`<pre>` 를 담은 flex 항목이 안 줄어드는 이유 — 한 줄로**

- **바닥이 `min-content` 인데 `<pre>` 의 `min-content` 가 한 줄 전체(280.02)라, `flex-shrink` 가 내려갈 수 있는 자리가 없다.**

**고치는 두 갈래**

| 갈래 | 방법 | 대가 |
|---|---|---|
| 바닥을 내린다 | `min-width: 0` · `overflow: hidden`/`auto` | 내용이 넘치거나 잘린다 |
| **내용의 `min-content` 를 줄인다** | `overflow-wrap: anywhere` 등 | 글이 아무 데서나 쪼개지고 **높이가 는다** |

- *(실측 — 컨테이너 300 · 사이드바 100 · 본문 `flex: 1` 에 긴 URL 한 줄: 기본은 본문 248.00 에 오른끝 348.00(뚫는다), 본문에 `overflow-wrap: anywhere` 만 더하면 **200.00 · 오른끝 300.00** 이고 높이가 48 → 72 로 는다.)*
- 즉 **바닥을 그대로 두고도 고칠 수 있다.** 어느 쪽을 고를지는 「넘치게 둘까 / 아무 데서나 쪼갤까」의 문제다.

### 5. ★★ `fit-content(150px)` 는 되는가

**실행 결과** (Chrome 151 headless)

```text
진단 3창의 첫째 창 — cssRules 로 읽은 규칙 본문
  #a5 { }                       <- width: fit-content(150px)    버려졌다
  #a6 { }                       <- width: bogus-content         버려졌다 (대조군)
  #mc { width: min-content; }   <- width: min-content           담겼다

실제 렌더 (부모 400px)
  fit-content(150px) -> 400.00      fit-content(600px) -> 400.00
  fit-content(50px)  -> 400.00      width: auto        -> 400.00
```

**동작하는가**

- **안 한다.**

**어느 단계에서 실패하나**

- **가장 앞 단계 — 파싱이다.** 규칙 상자가 비어 있으므로 **선언이 아예 안 담겼다.**
- 진단 3창 중 **첫째 창(`cssRules`)** 이 답한다. 둘째·셋째 창은 볼 필요도 없다.
- ★ **존재하지 않는 값 `bogus-content` 와 구분되지 않는다.** 「미지원」이 아니라 「모르는 값」으로 처리된 것이다.

**`getComputedStyle` 로 진단되는가**

- **안 된다.** `400px` 라는 **그럴듯한 숫자**가 돌아와 「선언을 안 쓴 것」과 구분이 안 된다.
- 게다가 `fit-content(600px)`·`fit-content(50px)` 가 **전부 같은 400.00** 이다 — 값을 바꿔 봐도 아무 단서가 없다.

**Baseline 은 무엇이라 하나**

- `api.webstatus.dev` 조회: **`fit-content()` = `limited`**(newly 날짜 없음). 키워드 `fit-content` 는 **`widely`**(2021-11-02 → 2024-05-02).
- **근거가 둘이다** — 실행 결과와 Baseline 데이터가 같은 말을 한다.

**같은 의도를 지금 표현하는 두 줄**

```css
.x { width: fit-content; max-width: 150px; }
```

- Grid 트랙에서의 `fit-content()` 는 **다른 자리**이고 지원 상황도 다르다 — [목록의 **27번 주제**](../27-grid-track-sizing/).

### 6. `width: auto` 와 `fit-content`

**실행 결과** (Chrome 151 headless — 같은 글·같은 부모(400px), 상자 종류만 다르다)

```text
display: block        width: auto  ->  400.00
float: left           width: auto  ->  128.02
position: absolute    width: auto  ->  128.02
display: inline-block width: auto  ->  128.02

같은 글의 fit-content = 128.02
```

**네 상자의 폭**

- **400.00 / 128.02 / 128.02 / 128.02.**

**왜 첫째만 다른가**

- **`auto` 의 뜻이 상자 종류마다 다르기 때문**이다.
- 블록 — **「남은 폭을 전부 채워라」**(채움).
- float · absolute · inline-block — **「쥐어짜서 맞춰라」**(축소 맞춤) = **`fit-content` 공식 그 자체**.
- 그래서 **`width: auto` 는 하나의 규칙이 아니다.** 상자 종류를 바꾸는 순간 뜻이 바뀐다.

**블록으로 「글자만큼만 넓은 배지」**

- **`width: fit-content`.** 상자 종류와 무관하게 늘 축소 맞춤이다.

**`display: inline-block` 관용구가 대신하던 것**

- **축소 맞춤**이다. 「내용만큼 넓게」를 얻으려고 **상자 종류를 바꾸는 부작용**(줄 안에 끼는 것·`vertical-align` 영향)을 감수한 것이다.
- `fit-content` 는 **부작용 없이 크기만** 바꾼다. Baseline widely 이후로는 관용구를 쓸 이유가 없다.

### 7. `aspect-ratio` 는 어느 축을 기준으로 하나

**실행 결과** (Chrome 151 headless — 부모 400px)

```text
aspect-ratio: 16/9; width: 320px              320.00 × 180.00   w/h 1.778  ✓
aspect-ratio: 16/9; height: 90px; width: auto 160.00 ×  90.00   w/h 1.778  ✓
aspect-ratio: 16/9  (블록, 둘 다 auto)          400.00 × 225.00   w/h 1.778  ✓
aspect-ratio: 16/9; width:320px; height:200px 320.00 × 200.00   w/h 1.600  ✗
aspect-ratio: auto (초기값)                     400.00 ×  24.00   —
```

**넷의 치수**

- 320×180 · 160×90 · 400×225 · **320×200**(비율 1.600 — 안 지켜졌다).

**`.r4` 에서 비율은 지켜지나**

- **아니다. 무시된다.** 두 축이 다 지정되면 `aspect-ratio` 가 할 일이 없다.
- ★ 그런데 **`getComputedStyle().aspectRatio` 는 `16 / 9` 로 그대로 남는다.** 계산값만 보면 「썼는데 왜 안 되지」가 된다.

**둘 다 `auto` 인 블록에서 먼저 정해지는 축**

- **가로(`width`)** 다. 블록의 `width: auto` 가 부모를 채워 400 이 되고, 높이가 400 ÷ (16/9) = **225** 로 따라온다.
- 상자가 블록이 아니면(예: `float`) 가로가 축소 맞춤으로 먼저 정해지고 세로가 따라온다.

### 8. ★ 비율은 언제 깨지는가

**실행 결과** (Chrome 151 headless — `aspect-ratio: 1/1; width: 120px`, 내용 길이만 바꿨다)

```text
내용                        폭 × 높이          w/h     scrollHeight
짧은 내용                   120.00 × 120.00   1.000   120
아주 긴 내용                 120.00 × 168.00   0.714   168      <- 깨졌다
  + min-height: 0          120.00 × 120.00   1.000   168
  + overflow: hidden       120.00 × 120.00   1.000   168
  + overflow: auto         120.00 × 120.00   1.000   192
  + min-height: 200px      120.00 × 200.00   0.600   —        <- min-height 가 이겼다
```

**짧을 때와 길 때의 높이**

- **120.00 과 168.00.** 같은 선언인데 내용만으로 48px 가 늘었다.

**깨지는 이유 — 「내용 기반 최소 크기」로**

- `aspect-ratio` 로 **정해지는 축**(여기서는 높이)에는 **내용 기반 최소 크기**가 걸린다.
- 내용이 그 최소보다 크면 **최소 크기가 비율을 이긴다.** 명세가 그렇게 정의한 것이지 버그가 아니다.
- ★ **[25번](../25-flex-shorthand-and-sizing/)의 `min-width: auto` 와 같은 뿌리**다 — 「내용 기반 최소 크기가 지정 크기를 이긴다」는 규칙 하나가 flex 에서는 가로로, 비율 상자에서는 세로로 나타난 것이다.

**고치는 셋과 부작용**

| 고침 | 결과 | 부작용 |
|---|---|---|
| `min-height: 0` | 120×120 | 넘친 글자가 **상자 밖으로 보인다** |
| `overflow: hidden` | 120×120 | 넘친 글자가 **잘린다** |
| `overflow: auto` | 120×120 | **스크롤바**가 생긴다(그래서 `scrollHeight` 가 192 로 더 크다) |

**고친 뒤 `scrollHeight`**

- **168 로 120 보다 크다.** 뜻은 **「내용은 여전히 넘치고 상자만 비율을 지킨 것」** 이다.
- 비율과 내용 수용은 **둘 다 가질 수 없다.** 어느 쪽을 버릴지 고르는 문제다.

**`min-height: 200px` 를 같이 주면**

- **120.00 × 200.00**(비율 0.600). **`min-height` 가 비율을 이긴다.**
- 「비율을 지키되 최소 높이도」는 성립하지 않는다.

**실서비스에서 늦게 발견되는 이유**

- **짧은 내용에서는 안 깨지기 때문**이다. 개발 중 더미 텍스트로는 정상으로 보이고, 실데이터가 길어진 뒤에야 드러난다.
- 게다가 **에러도 경고도 없고 계산값도 `1 / 1` 그대로**다. `getBoundingClientRect()` 로 재야만 보인다.

### 9. 유효하지 않은 값

**실행 결과** (Chrome 151 headless — `cssRules` 로 읽은 규칙 본문)

```text
#a1 { aspect-ratio: 0 / 1; }     <- 담긴다
#a2 { }                          <- aspect-ratio: -1        버려졌다
#a3 { aspect-ratio: 16 / 9; }
#a4 { aspect-ratio: 1.5 / 1; }   <- 한 값을 써도 "/ 1" 이 붙어 저장된다
#a5 { }                          <- width: fit-content(150px)  버려졌다
#a6 { }                          <- width: bogus-content       버려졌다

aspect-ratio: 0 / 1; width: 120px 인 상자의 실제 크기
  120.00 × 24.00   (글 한 줄 높이 — 비율이 아무 일도 안 했다)   계산값 "0 / 1"
```

**담기는 것**

- **`aspect-ratio: 0 / 1` 과 `aspect-ratio: 1.5`.** 음수와 `fit-content()` 는 버려진다.

**담기고도 아무 일도 안 하는 것**

- **`aspect-ratio: 0 / 1`.** 문법상 유효해서 담기지만 **퇴화한 비율**이라 레이아웃에서 쓰이지 않는다.
- 7번의 `.r4`(두 축을 다 준 경우)도 같은 성격이다 — 담기고 안 먹는다.

**`.a3` 의 계산값**

- **`1.5 / 1`.** 한 값으로 써도 두 값 형태로 정규화된다.

**「담겼다」와 「먹었다」를 가르는 법**

```text
cssRules 로 읽는다      ->  비어 있으면  : 파싱에서 버려졌다 (fit-content(150px))
계산값을 읽는다          ->  남아 있으면  : 담기긴 했다
getBoundingClientRect ->  기대와 다르면 : 담겼는데 안 먹은 것 (0/1, 두 축 지정)
```

- ★ **이 셋을 안 가르면 증상이 전부 같다** — 「썼는데 안 되네」 하나로 보인다.

### 10. 다른 주제와 잇기

**`fr` 과 `minmax()`**

- [목록의 **27번 주제**](../27-grid-track-sizing/)(Grid 트랙 정의). 트랙에서의 `fit-content()` 도 거기다. **이 문서는 내재적 크기 키워드까지만** 다룬다.

**`width` 가 재는 칸**

- [15번](../15-box-model-and-box-sizing/)(박스 모델과 `box-sizing`)이 정본이다. `min-content` 같은 값도 **그 칸에 들어가는 값**이다.

**「어디서 줄바꿈되는가」**

- [목록의 **51번 주제**](../51-text-wrapping-and-decoration/)(텍스트 줄바꿈·서식·장식). 3번의 하이픈 실측이 그쪽에 기댄다.

**`min-content` 를 실제로 줄이는 것**

**실행 결과** (Chrome 151 headless — `hi javascript ok` 를 `width: min-content` 상자에)

```text
기본                       80.00  (높이 72)
overflow-wrap: anywhere     8.02  (높이 336)   <- 줄인다
word-break: break-word      8.02  (높이 336)   <- 줄인다
word-break: break-all       8.02  (높이 336)   <- 줄인다
overflow-wrap: break-word  80.00  (높이 72)    <- 안 줄인다
```

- **`overflow-wrap: anywhere` 가 줄이고 `overflow-wrap: break-word` 는 안 줄인다.**
- `anywhere` 는 **내재적 크기 계산에 반영되고**, `break-word` 는 **넘칠 때만 쪼갠다.** 이름이 한 쌍처럼 생겼는데 성질이 반대다.

**25번의 사고를 `min-width: 0` 없이 고칠 수 있는가**

- **있다.** 4번의 실측대로 본문에 `overflow-wrap: anywhere` 한 줄이면 200.00 · 오른끝 300.00 이 된다.
- **잃는 것은 높이와 가독성**이다 — 글이 아무 데서나 쪼개지고 줄 수가 는다(48 → 72). `<pre>` 처럼 줄바꿈이 의미를 갖는 내용에는 못 쓴다.

## 실행 검증

| 무엇을 | 어떻게 | 몇 번 | 결과 |
|---|---|---|---|
| 세 키워드 + `auto` 의 폭 | 같은 글, 부모 400px / 80px 두 판 | 2 | 1번 표 |
| 낱말·조각 폭 | `position: absolute; white-space: pre` 인 `<span>` 으로 따로 | 2 | 1·3번 표 |
| 하이픈이 `min-content` 를 줄이는가 | `hi javascript ok` 대 `hi flex-basis ok` | 1 | 3번 표 |
| `<pre>` 의 `min-content` = `max-content` | 같은 요소를 두 키워드로 | 1 | 3번 표 |
| `min-width` 기본값 세 문맥 | flex·grid·블록 자식 | 1 | 4번 표 |
| `overflow-wrap`/`word-break` 다섯 값 | `width: min-content` 상자에 한 줄씩 | 1 | 10번 표 |
| 그것으로 25번 사고 고치기 | 컨테이너 300 · 사이드바 100 · 긴 URL | 1 | 4·10번 |
| `fit-content()` 의 파싱 | `cssRules` + `bogus-content` 대조군 | 1 | 5번 표 |
| `fit-content()` 의 렌더 | 150px·600px·50px 세 인자 | 1 | 5번 표 |
| `auto` 대 `fit-content` 상자 넷 | 같은 부모·같은 글 | 1 | 6번 표 |
| `aspect-ratio` 다섯 조합 | 한 축·둘 다·둘 다 auto·`auto` | 1 | 7번 표 |
| 비율이 깨지는 조건과 고침 셋 | 내용 길이만 바꿔 여섯 판 | 2 | 8번 표 |
| 유효하지 않은 값 | `cssRules` 로 여섯 규칙 | 1 | 9번 표 |
| Baseline | `api.webstatus.dev` feature API 조회 | 1 | `min-max-content` widely · `fit-content` widely · **`fit-content-function` limited** · `aspect-ratio` widely |
| `demo` 블록 3개 | 완성된 문서에서 `extract-demo-blocks.py --render` 로 재추출해 재실행 | 1 | 수치 일치 |

**구현에 의존하는 항목** — 모든 픽셀값이 글꼴(`monospace` 의 실제 글꼴)과 글꼴 크기에 달렸다. `128.02` 의 `.02` 같은 잔차도 그렇다.
**명세와 구현이 갈린 자리** — `fit-content()` 는 css-sizing-4 에 있지만 **이 Chrome 은 값을 모른다.** 명세를 읽은 것은 확인한 것이 아니다.
**엔진은 Chrome 하나다** — Firefox 는 이 환경에서 headless 스크린샷이 산출되지 않아 엔진 차이를 주장하지 않았다.

## 이 주제가 답하려는 질문

1. 「내용만큼」의 두 가지 뜻은 수치로 얼마나 다른가 — 같은 글에서 **80.00 대 128.02** 였고, 그 차이를 만드는 것은 **줄바꿈 기회**다(1·3번).
2. `width: auto` 와 `fit-content` 는 언제 갈리나 — **블록에서만 갈린다.** `float`·`absolute`·`inline-block` 에서는 같다(6번).
3. `aspect-ratio` 는 언제 깨지나 — **두 축을 다 주면 무시되고, 내용이 넘치면 내용 기반 최소 크기가 이긴다**(7·8번).

## 구현 세부사항 대 언어 보장

- **명세가 보장하는 것** — `min ≤ fit ≤ max` 와 `fit-content` 공식 · 블록의 `auto` 는 채움이고 float/absolute/inline-block 은 축소 맞춤인 것 · flex·grid 항목의 `min-*: auto` 가 자동 최소 크기인 것 · 두 축이 다 지정되면 `aspect-ratio` 가 무시되는 것 · 비율로 정해지는 축에 내용 기반 최소 크기가 걸리는 것.
- **이 Chrome 의 관찰인 것** — 모든 구체 픽셀값 · `1.5` 가 `1.5 / 1` 로 정규화되는 표현 형식 · `word-break: break-word` 가 `min-content` 를 줄인 것 · 버려진 선언이 `cssRules` 에서 빈 상자로 보이는 것.
- **명세에 있는데 구현이 없는 것** — `fit-content()`. Baseline `limited` 와 실측이 일치한다.
- **관찰을 보장으로 적지 않았다** — 특히 8번은 **같은 선언이 내용에 따라 결과가 갈리는** 자리라 「한 번 돌려 보고 지켜진다」고 말할 수 없다. 짧은 내용 판과 긴 내용 판을 **둘 다** 실었다.

## 용어 풀이

- **내재적 크기(intrinsic size)** — 부모 크기와 무관하게 내용만으로 정해지는 크기. 부모를 바꿔도 안 움직인다.
- **외재적 크기(extrinsic size)** — 부모가 준 공간을 기준으로 정해지는 크기. `width: auto`·`50%`.
- **`min-content`** — 쪼갤 수 있는 만큼 다 쪼갰을 때의 크기. 「가장 긴 낱말」이 아니라 **「가장 큰 쪼갤 수 없는 조각」** 이다.
- **`max-content`** — 줄바꿈을 한 번도 안 했을 때의 크기.
- **`fit-content`** — `min(max-content, max(min-content, 쓸 수 있는 공간))`. 셋 중 유일하게 부모 크기가 섞인다.
- **축소 맞춤(shrink-to-fit)** — `fit-content` 공식의 옛 이름. `float`·`absolute`·`inline-block` 의 `auto` 가 이것이다.
- **줄바꿈 기회(soft wrap opportunity)** — 글을 쪼갤 수 있는 자리. 공백과 **하이픈**. `white-space: pre` 면 없다.
- **자동 최소 크기(automatic minimum size)** — flex·grid 항목의 `min-*: auto` 가 풀리는 값. 대개 `min-content`.
- **내용 기반 최소 크기(content-based minimum size)** — 비율로 정해지는 축에 걸리는 바닥. 8번에서 비율을 깨는 범인.
- **`aspect-ratio`** — 한 축이 정해지면 다른 축을 비율로 만든다. 두 축이 다 지정되면 **담기되 무시된다.**
- **퇴화한 비율(degenerate ratio)** — `0 / 1` 처럼 어느 한쪽이 0 인 비율. 담기지만 레이아웃에서 쓰이지 않는다.
- **진단 3창** — `cssRules`(담겼나) → `querySelectorAll`(잡혔나) → `getComputedStyle`(이겼나). 5번은 첫째 창에서, 8·9번은 셋을 다 통과하고 `getBoundingClientRect()` 에서 갈렸다.
