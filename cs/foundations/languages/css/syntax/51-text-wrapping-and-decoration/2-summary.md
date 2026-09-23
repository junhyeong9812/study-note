# css/syntax/51 — 텍스트 줄바꿈·서식·장식: `word-break`·`overflow-wrap`·`text-wrap`·`text-decoration` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Text Module Level 4](https://drafts.csswg.org/css-text-4/) (`white-space` 분해·`word-break`·`overflow-wrap`·`text-wrap`·`hyphens`) · [CSS Text Decoration Level 4](https://drafts.csswg.org/css-text-decor-4/) (`text-decoration-*`·`text-underline-offset`) · [CSS Overflow Level 3](https://drafts.csswg.org/css-overflow-3/) (`text-overflow`). 열어서 확인한 것만 적었다.
> **실행 검증** — **Google Chrome 151.0.7922.173** headless · Linux. 이 문서의 **줄 수와 줄 폭은 전부 실측**이다 — `Range.selectNodeContents(el).getClientRects()` 로 행 상자를 세고, 눈으로 봐야 하는 것은 CDP 스크린샷으로 확인했다.\
> **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다 — 크로스 브라우저 차이는 Baseline 데이터로만 접지했다.
> **버전** — `word-break`·`overflow-wrap`·`white-space`·`text-overflow`·`text-decoration`·`hyphens` 는 Baseline **widely**. `text-wrap` 은 **newly**(2024-10-17), `text-wrap: balance` 는 **newly**(2024-05-13), `white-space-collapse` 는 **newly**(2024-03-19), **`text-wrap: pretty` 는 아직 Baseline 이 아니다(limited)**. `api.webstatus.dev` 조회 결과이고 아래 「구현 세부사항 대 언어 보장」에 다시 적었다.
> ⚠️ **줄 수는 글꼴에 달려 있다.** 같은 문장도 글꼴이 다르면 글자 폭이 달라 줄 수가 달라진다 — 선행 주제가 [50번](../50-fonts-and-webfonts/2-summary.md)인 이유다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**줄바꿈은 「자를 위치를 고르는 것」이 아니라 「이미 있는 틈에서 고르는 것」이다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 종이를 접을 수 있는 **점선** | 줄바꿈 기회(break opportunity) |
| 점선이 원래 찍혀 있는 자리 | 띄어쓰기 · 하이픈 뒤 · 한글/한자 글자 사이 |
| 점선을 **더 찍는** 가위 | `word-break: break-all` · `overflow-wrap: anywhere` |
| 점선이 **없으면 삐져나간다** | 긴 URL·긴 토큰이 상자를 뚫는 것 |
| 삐져나갈 때만 가위를 꺼낸다 | `overflow-wrap: break-word` |
| 점선 몇 개를 **지운다** | `word-break: keep-all`(한국어 어절 보호) |
| 점선 중 **어느 것을 고를지 다시 생각한다** | `text-wrap: balance` · `pretty` |
| 접고 남은 부분에 **「…」를 찍는다** | `text-overflow: ellipsis` |
| 완성된 줄 위에 **자를 대고 선을 긋는다** | `text-decoration` |

- 브라우저는 줄을 채우다 상자 끝에 닿으면 **직전 점선으로 되돌아가** 자른다.
- **점선이 하나도 없으면 되돌아갈 곳이 없어서 그냥 삐져나간다.** 에러도 경고도 없다.
- 그래서 「긴 URL 이 상자를 뚫는다」는 **점선 문제**이지 `overflow` 문제가 아니다.

```text
  상자 폭 240px
  +--------------------------------+
  |The ThisIsAnExtremelyLongUnbreak|ableToken ends.     <- 점선이 없어 뚫고 나간다
  +--------------------------------+
      ^   ^
      점선은 여기 둘뿐이다(띄어쓰기)

  가위를 주면
  +--------------------------------+
  |The ThisIsAnExtremelyLongUnbrea |
  |kableToken ends.                |                    <- 낱말 한가운데에 점선이 생겼다
  +--------------------------------+
```

실무에서 이게 터지는 자리는 **사용자가 넣은 URL·이메일·파일명**이다.\
한국어 문장은 띄어쓰기가 있어 대개 안 터지는데, 링크 하나가 섞이면 그 카드만 가로로 깨진다.

> **줄바꿈 기회(break opportunity)** — 그 자리에서 줄을 바꿔도 되는 지점.\
> 예: `hello world` 에는 공백 하나가 기회다. `hello-world` 는 하이픈 뒤도 기회다. `helloworld` 에는 기회가 없다.

> **행 상자(line box)** — 한 줄을 담는 상자. 이 문서에서 「줄 수」는 행 상자의 개수이고,\
> `Range.getClientRects().length` 로 센 값이다. 행 상자의 **높이**가 어떻게 정해지는지는 [목록의 **19번 주제**](../19-inline-formatting-context/)가 정본이다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `word-break` 와 `overflow-wrap` 은 **무엇이 다른가** — 같은 문장에서 줄 수가 어떻게 갈리는가.
2. 한국어에서 **어절이 잘리는 것을 어떻게 막고**, 그 대가로 무엇을 내는가.
3. `text-decoration` 은 왜 **자손이 끌 수 없는가** — 상속과 무엇이 다른가.

## 동작 방식

### (1) 줄을 만드는 순서 — 점선을 찾고, 없으면 뚫는다

**언제 쓰나** — 「왜 여기서 줄이 바뀌지」·「왜 안 바뀌지」를 진단할 때. 전부 이 순서 안에 있다.

```text
  ① 공백 처리          white-space-collapse 가 연속 공백·줄바꿈을 어떻게 할지 정한다
        ↓
  ② 줄바꿈 기회 찾기    유니코드 줄바꿈 규칙 + word-break · hyphens 가 기회를 더하고 뺀다
        ↓
  ③ 줄 채우기          상자 폭까지 채우고, 넘으면 직전 기회로 되돌아가 자른다
        ↓
  ④ 기회가 없으면?      overflow-wrap 이 여기서만 끼어든다 — 없으면 그냥 넘친다
        ↓
  ⑤ 줄 고르기 다시     text-wrap: balance / pretty 가 ③의 결과를 통째로 다시 고른다
        ↓
  ⑥ 넘친 것 처리       text-overflow 가 잘린 자리에 표시를 넣는다(한 줄일 때만)
```

그림 해설 (한 단계씩):

- **②와 ④가 다른 단계**라는 것이 이 주제의 뼈대다. `word-break` 는 ②에, `overflow-wrap` 은 ④에 산다.
- ⑤는 Chrome 에서 **줄 수가 적을 때만** 돈다 — (6)에서 실측한다.
- ⑥은 **잘라내기이지 줄바꿈이 아니다.** ③에서 이미 한 줄로 확정돼 있어야 한다.

### (2) ★★ `word-break` 와 `overflow-wrap` — 어디서든 끊나, 넘칠 때만 끊나

**언제 쓰나** — 긴 토큰이 상자를 뚫을 때. **둘 중 무엇을 쓸지가 이 주제의 과녁**이다.

```text
  word-break: break-all          overflow-wrap: break-word
  ─────────────────────          ─────────────────────────
  "점선을 전부 찍는다"            "점선이 없어서 넘칠 때만 찍는다"
  줄을 채우는 단계(②)에서         넘치는 것이 확정된 뒤(④)에
  낱말 중간이 줄 끝에 와도 OK     그 낱말 하나만 쪼갠다
```

**실측 — 같은 문장, 같은 240px 상자, 줄 수와 줄 폭**

```text
  텍스트: "The ThisIsAnExtremelyLongUnbreakableToken ends."

  (가) 아무것도 안 줌           줄 3개   폭  28.17 | 314.31 | 40.50
                                              ^^^^^^ 상자(240px)를 74px 뚫었다
  (나) word-break: break-all    줄 2개   폭 237.55 | 154.39
                                              ^^^^^^ "The" 가 첫 줄에 같이 실렸다
  (다) overflow-wrap: break-word 줄 3개  폭  28.17 | 237.39 | 122.09
                                              ^^^^^ "The" 는 혼자 남았다
```

그림으로 보면 **어디가 달라졌는지**가 분명하다.

```text
  (가) 기본                        (나) break-all                (다) break-word
  +------------------+            +------------------+          +------------------+
  |The               |            |The ThisIsAnExtrem|          |The               |
  |ThisIsAnExtremelyLongUnbreak..  |elyLongUnbreakable|          |ThisIsAnExtremely |
  |ends.             |            |Token ends.       |          |LongUnbreakableTok|
  +------------------+            +------------------+          |en ends.          |
   줄 3개 · 뚫린다                  줄 2개 · 꽉 찬다              +------------------+
                                                                  줄 3개 · 안 뚫린다
```

- **(나)는 「The」 뒤에서 줄을 안 바꿨다.** 낱말 경계를 지킬 의무가 없어졌으므로
  첫 줄을 **끝까지 채우는 쪽**을 골랐다. 그래서 줄이 하나 줄었다.
- **(다)는 「The」 뒤에서 줄을 바꿨다.** 점선은 여전히 띄어쓰기에만 있고,
  그 다음 낱말이 한 줄에 안 들어가니까 **그 낱말만** 쪼갰다.
- **줄 수가 결론이다** — 3 / 2 / 3. 겉보기 증상(「안 뚫린다」)은 (나)와 (다)가 같지만
  **줄 수와 줄 폭이 다르므로 레이아웃 결과가 다르다.**

비용 — `break-all` 은 **읽기를 해친다**(짧은 낱말도 잘린다). 긴 토큰만 문제라면 `break-word` 가 맞다.

```html demo
<div class="b">The ThisIsAnExtremelyLongUnbreakableToken ends.</div>
<div class="b all">The ThisIsAnExtremelyLongUnbreakableToken ends.</div>
<div class="b word">The ThisIsAnExtremelyLongUnbreakableToken ends.</div>
<style>
  .b    { width: 240px; font: 16px/24px sans-serif; border: 1px solid #999; margin: 6px 0; }
  .all  { word-break: break-all; }
  .word { overflow-wrap: break-word; }
</style>
```

> **보이는 것** — 첫 상자는 **글자가 테두리를 뚫고 오른쪽으로 삐져나가** 세 줄이 된다.\
> 둘째 상자(`break-all`)는 **두 줄**이고 첫 줄이 테두리에 꽉 차게 채워진다 — `The` 뒤에서 줄이 안 바뀐다.\
> 셋째 상자(`break-word`)는 **세 줄**인데 아무것도 안 뚫린다 — 첫 줄에 `The` 만 혼자 있다.\
> **바꿔 볼 것** — `overflow-wrap: break-word` → `anywhere` 로 바꾸면 **이 상자에서는 결과가 똑같다**(폭이 고정이라 차이가 안 난다. 차이가 나는 조건은 아래 (3)) · `word-break: break-all` 을 한국어 문장에 걸면 → 아무것도 안 달라진다(아래 (4))

*(Chrome 151 headless 실측 — 줄 수 3 / 2 / 3, 줄 폭은 위 표 그대로. 첫 상자의 둘째 줄이 314.31px 로 **240px 상자를 74px 넘겼다**.)*

### (3) `anywhere` 와 `break-word` — 내재적 크기에 들어가느냐

**언제 쓰나** — flex·grid 아이템이나 `width: min-content` 를 쓸 때. **폭이 내용으로 정해지는 상황**에서만 갈린다.

```text
  min-content 폭을 계산할 때

  overflow-wrap: break-word     "이 낱말은 안 쪼개진다고 치고 계산"  -> 가장 긴 낱말의 폭
  overflow-wrap: anywhere       "쪼갤 수 있다고 치고 계산"          -> 가장 넓은 글자 하나의 폭
  word-break: break-all         〃                                 -> 〃
```

**실측** — `<span style="width: min-content">Hydroelectric plant</span>`

```text
  overflow-wrap: normal       상자 폭 108.70px   줄 2개 (106.70 · 40.83)
  overflow-wrap: break-word   상자 폭 108.70px   줄 2개 (106.70 · 40.83)   <- normal 과 같다
  overflow-wrap: anywhere     상자 폭  14.03px   줄 17개                   <- 글자 하나 폭
  word-break: break-all       상자 폭  14.03px   줄 17개                   <- 같다
```

- `break-word` 는 **「쪼갤 수 있다」를 크기 계산에 알리지 않는다.** 그래서 `min-content` 가 안 줄어든다.
- `anywhere` 는 알린다. 그래서 상자가 **글자 하나 폭까지** 쪼그라들 수 있다.
- **실무의 함정** — flex 아이템에 `overflow-wrap: anywhere` 를 걸면 그 아이템이 **극단적으로 좁아질 수** 있다.\
  「넘치는 것만 막고 싶다」면 `break-word` 가 맞다.
- 내재적 크기(`min-content`·`max-content`)가 무엇인지는 [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)가 정본이다. 여기서는 **이 두 값이 그 계산에 참여하느냐**만 다룬다.

> **내재적 크기(intrinsic size)** — 상자 폭을 밖에서 안 정해 줄 때 **내용만으로** 정해지는 크기.\
> 예: `min-content` 는 「더 줄이면 넘치기 시작하는 폭」이다. 보통은 가장 긴 낱말의 폭이다.

### (4) ★ `word-break: keep-all` — 한국어에서 어절을 지킨다

**언제 쓰나** — 한국어·중국어·일본어 본문에서. **한글은 기본값이 이미 「어디서든」이다.**

```text
  한글의 기본 줄바꿈 기회

  줄 바 꿈 기 회 는   브 라 우 저 가   스 스 로   정 하 는   것 이 다
   ^ ^ ^ ^ ^ ^   ^   ^ ^ ^ ^ ^ ^   ^   ^ ^ ^   ^  ^ ^ ^  ^  ^ ^ ^
   글자 사이마다 전부 기회다(유니코드 줄바꿈 규칙이 CJK 를 그렇게 다룬다)

  keep-all 을 주면

  줄바꿈기회는   브라우저가   스스로   정하는   것이다
              ^            ^        ^        ^
              띄어쓰기에만 기회가 남는다
```

**실측** — 같은 문장 `줄바꿈기회는 브라우저가 스스로 정하는 것이다`, 상자 폭을 바꿔 가며

| 상자 폭 | `normal` | `break-all` | `keep-all` |
|---|---|---|---|
| 110px | **3줄** (108·108·93) | **3줄** (108·108·93) | **4줄** (88·74·93·44) |
| 130px | 3줄 (122·127·63) | 3줄 (122·127·63) | 3줄 (88·122·93) |
| 150px | 3줄 (137·146·29) | 3줄 (137·146·29) | 3줄 (88·122·93) |
| 190px | 2줄 (186·127) | 2줄 (186·127) | 2줄 (166·141) |
| 210px | 2줄 (200·112) | 2줄 (200·112) | 2줄 (166·141) |

그림 해설 (한 줄씩):

- ★ **`normal` 과 `break-all` 이 여섯 폭에서 전부 똑같았다.**\
  한글은 이미 글자마다 기회가 있어서 **`break-all` 이 더 찍을 점선이 없다.**\
  「한국어에 `break-all` 을 걸면 어절이 잘린다」는 표현은 정확하지 않다 — **기본값이 이미 그렇다.**
- ★ **`keep-all` 은 줄을 하나 더 쓸 수 있다.** 110px 에서 3줄 → **4줄**.\
  어절을 지키는 값이므로 **높이가 늘어나는 것이 대가**다.
- 130px·150px 에서는 줄 수가 같은데 **줄 폭이 다르다** — 끊는 위치가 어절 경계로 옮겨졌다.

비용 — 세로 공간. 좁은 칸(테이블 셀·칩·버튼)에서는 `keep-all` 이 줄을 늘려 레이아웃을 밀 수 있다.\
그래서 **본문에는 `keep-all`, 좁은 칸에는 기본값**이 보통의 선택이다.

```html demo
<div class="k">줄바꿈기회는 브라우저가 스스로 정하는 것이다</div>
<div class="k keep">줄바꿈기회는 브라우저가 스스로 정하는 것이다</div>
<style>
  .k    { width: 110px; font: 16px/24px sans-serif; border: 1px solid #999; margin: 6px 0; }
  .keep { word-break: keep-all; }
</style>
```

> **보이는 것** — 위 상자는 **3줄**이고 `줄바꿈기회`·`브라우저` 같은 **어절이 줄 끝에서 잘려** 다음 줄로 이어진다.\
> 아래 상자(`keep-all`)는 **4줄**이고 **어절이 하나도 안 잘린다** — 대신 상자가 한 줄만큼 더 높다.\
> **바꿔 볼 것** — `.keep` 에 `word-break: break-all` 을 대신 넣으면 → **위 상자와 완전히 같아진다**(한글에는 더 찍을 점선이 없다) · 상자 폭 `110px` → `190px` 로 넓히면 → 두 상자가 둘 다 2줄이 되고 끊는 위치만 달라진다

*(Chrome 151 headless 실측 — 위 3줄(107.53 · 107.53 · 92.81), 아래 4줄(88.33 · 73.61 · 92.81 · 44.17). 190px 로 넓힌 판은 둘 다 2줄이고 폭이 186/127 대 166/141 이었다.)*

### (5) `hyphens` — 사전이 있어야 자동이 된다

**언제 쓰나** — 서양어 본문에서 오른쪽 여백을 줄이고 싶을 때.

```text
  hyphens: none      소프트 하이픈(U+00AD)이 있어도 무시한다
  hyphens: manual    소프트 하이픈이 있는 자리에서만 끊는다  <- 기본값
  hyphens: auto      사전을 보고 알아서 끊는다 + manual 의 자리도 쓴다
                     ^^^^ lang 속성으로 어느 언어 사전인지 알려 줘야 한다
```

**실측** — 100px 상자, `extra&shy;ordi&shy;narily compli&shy;cated`

| 값 | 소프트 하이픈 | 줄 수 | 줄 폭 |
|---|---|---|---|
| `none` | 있음 | 2 | 117 · 98 ← **117px 이 100px 상자를 뚫었다** |
| `manual` | 있음 | **4** | 72 · 6 · 45 · 98 |
| `auto` | 있음 | **4** | 72 · 6 · 45 · 98 |
| `auto` | **없음** | 2 | 117 · 98 ← **자동 하이프네이션이 안 일어났다** |
| `auto` + `lang="en-US"`, 하이픈 없음 | 없음 | 2 | 117 · 98 |
| `auto` + `lang="de"` (독일어 `Silbentrennung Donaudampfschiff`) | 없음 | 2 | 122 · 146 |

★ **이 환경에서는 `hyphens: auto` 의 자동 하이프네이션이 전혀 일어나지 않았다.**\
`lang` 을 `en`·`en-US`·`de` 로 바꿔 가며 던졌는데 줄 폭이 한 글자도 안 바뀌었다 —\
이 headless Chrome 에 **하이프네이션 사전이 붙어 있지 않다**고 보는 것이 맞다.

★★ **그래서 「`lang` 속성이 있어야 먹는다」는 이 환경에서 「못 잰 것」이다.**\
「안 돌려 봤다」가 아니다 — **던졌는데 측정의 전제(사전)가 없어서 판정이 안 선다.**\
쪼개서 잰 조각은 이것이다 — **`manual`·`none` 은 사전 없이도 갈렸다**(4줄 대 2줄).\
즉 **소프트 하이픈을 쓰느냐 마느냐는 쟀고, 자동 사전이 `lang` 을 보느냐는 못 쟀다.**\
명세는 `hyphens: auto` 가 **콘텐츠 언어를 알 때만** 자동 하이프네이션을 하도록 규정한다 —
그 접지는 명세로만 하고 실측으로 적지 않는다.

> **소프트 하이픈(soft hyphen, U+00AD)** — 「여기서 끊어도 좋다」는 보이지 않는 표시.\
> 예: `extra&shy;ordinarily` 는 평소엔 `extraordinarily` 로 보이고, 줄 끝에 걸리면 `extra-` 로 끊긴다.

### (6) `text-wrap` — 줄을 고르고 나서 다시 고른다

**언제 쓰나** — 제목이 「한 낱말만 다음 줄로 넘어가는」 모양이 될 때.

```text
  text-wrap: wrap      왼쪽부터 탐욕적으로 채운다(기본)
  text-wrap: balance   줄 길이를 고르게 만든다      -> 제목·짧은 문단용
  text-wrap: pretty    마지막 줄이 너무 짧지 않게   -> 본문용
  text-wrap: nowrap    줄을 안 바꾼다
```

**실측 ① — 같은 문장, 260px 상자**

```text
  wrap    : 255 | 251 | 236 |  93        <- 마지막 줄이 혼자 짧다
  pretty  : 215 | 196 | 179 | 127        <- 마지막 줄을 늘렸다
  balance : 204 | 181 | 233 | 216        <- 넷을 고르게 폈다
```

```text
   wrap                      balance
  +--------------------+    +--------------------+
  |################### |    |###############     |
  |################### |    |#############       |
  |##################  |    |#################   |
  |######              |    |################    |
  +--------------------+    +--------------------+
   마지막 줄이 튄다           네 줄이 비슷하다
```

★ **실측 ② — `balance` 에는 줄 수 상한이 있다.** 낱말 수를 늘려 가며 「효과가 있나」를 셌다.

```text
  줄 수    1    2    3    4    5    6    7    8    9   10   11
  효과     -    O    O    O    O    O    X    X    X    X    X
                                        ^
                                   7줄부터 아무것도 안 한다
```

- **6줄까지만 `balance` 가 돌았다.** 7줄 이상에서는 `wrap` 과 **줄 폭이 완전히 같았다.**
- 명세는 「UA 가 균형 맞추기를 **제한된 줄 수로 한정해도 된다**」고 허용한다 —\
  **6이라는 숫자는 Chrome 151 의 구현값**이지 명세 수치가 아니다.
- 그래서 `balance` 는 **제목·인용·캡션용**이다. 본문에 걸면 대개 아무 일도 안 일어난다.

★ **`text-wrap: pretty` 는 아직 Baseline 이 아니다**(limited). Chrome 에서는 동작하지만
다른 엔진에서는 무시될 수 있고, 무시돼도 **에러가 없다**(기본 `wrap` 으로 그려진다).

비용 — 두 값 다 **줄을 한 번 더 고르는 계산**이다. Chrome 이 `balance` 에 줄 수 상한을 둔 이유가 그것이다.

### (7) `white-space` 는 이제 단축이다

**언제 쓰나** — `white-space: nowrap` 과 `text-wrap: balance` 를 같이 쓰려다 충돌할 때.

```text
  white-space  =  white-space-collapse  +  text-wrap-mode
                  (공백을 어떻게 다루나)     (줄을 바꾸나)

  normal      ->  collapse        +  wrap
  nowrap      ->  collapse        +  nowrap
  pre         ->  preserve        +  nowrap
  pre-wrap    ->  preserve        +  wrap
  pre-line    ->  preserve-breaks +  wrap
  break-spaces->  break-spaces    +  wrap
```

**실측** — 계산값을 직접 읽은 것이다.

```text
  white-space: pre-wrap            -> collapse=preserve      text-wrap-mode=wrap
  white-space: nowrap              -> collapse=collapse      text-wrap-mode=nowrap
  white-space: break-spaces        -> collapse=break-spaces  text-wrap-mode=wrap
  white-space-collapse: preserve   -> white-space 가 "pre-wrap" 으로 직렬화된다
```

- 마지막 줄이 핵심이다 — **롱핸드만 썼는데 단축이 그 값으로 읽힌다.** 진짜 단축이라는 증거다.
- `text-wrap` 도 단축이다 — `text-wrap: balance` 의 계산값은
  `text-wrap-mode: wrap` + `text-wrap-style: balance` 였다(실측).
- 그래서 **`text-wrap-mode` 는 `white-space` 와 `text-wrap` 둘 다에 걸쳐 있다.**\
  `white-space: nowrap` 뒤에 `text-wrap: balance` 를 쓰면 `nowrap` 이 `wrap` 으로 **되돌아간다** —
  단축이 자기 칸을 채우기 때문이다([50번](../50-fonts-and-webfonts/2-summary.md)의 `font` 단축과 같은 규칙).

### (8) `text-overflow: ellipsis` — 세 가지가 동시에 맞아야 한다

**언제 쓰나** — 제목·파일명을 한 줄로 자를 때.

```text
  ① overflow 가 visible 이 아니다      (보통 hidden)
        +
  ② 그 줄이 한 줄이다                  (white-space: nowrap 등)
        +
  ③ text-overflow: ellipsis
        =
     "…" 이 찍힌다
```

**실측** — 150px 상자, `한 줄에 안 들어가는 긴 문장이다`

| 조건 | 상자 높이 | 화면 |
|---|---|---|
| `overflow:hidden` + `nowrap` + `ellipsis` | 26px(한 줄) | **`한 줄에 안 들어가는…`** ← 찍혔다 |
| `overflow:hidden` + `ellipsis` (nowrap 없음) | 50px(두 줄) | 그냥 두 줄로 접힌다 |
| `nowrap` + `ellipsis` (overflow 없음) | 26px(한 줄) | **테두리 밖으로 그대로 삐져나간다** |
| `overflow:hidden` + `nowrap` (ellipsis 없음) | 26px(한 줄) | **글자 중간에서 뚝 잘린다** |

- 셋 중 **하나만 빠져도 조용히 다른 결과**가 나온다. 콘솔에는 아무 말도 없다.
- 「두 줄 이상에서 말줄임」은 이 속성으로 못 한다 — `-webkit-line-clamp`(`line-clamp`) 영역이다.

```html demo
<div class="el">한 줄에 안 들어가는 긴 문장이다</div>
<div class="el wrap">한 줄에 안 들어가는 긴 문장이다</div>
<div class="el vis">한 줄에 안 들어가는 긴 문장이다</div>
<style>
  .el   { width: 150px; font: 16px/24px sans-serif; border: 1px solid #999; margin: 6px 0;
          overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
  .wrap { white-space: normal; }
  .vis  { overflow: visible; }
</style>
```

> **보이는 것** — 첫 상자만 **한 줄로 잘리고 끝에 `…` 이 찍힌다.**\
> 둘째 상자(`white-space: normal`)는 **두 줄로 접히고 `…` 이 안 찍힌다** — 한 줄이 아니면 안 먹는다.\
> 셋째 상자(`overflow: visible`)는 **한 줄인데 글자가 테두리 밖으로 삐져나가고** `…` 도 없다.\
> **바꿔 볼 것** — 첫 상자의 `text-overflow: ellipsis` 를 빼면 → `…` 없이 **글자 중간에서 뚝 잘린다** · `white-space: nowrap` 만 빼면 → 두 줄로 접히면서 `…` 이 사라진다

*(Chrome 151 headless 실측 — 상자 높이 26px / 50px / 26px. 첫째·셋째는 `scrollWidth 214px` 대 `clientWidth 150px` 로 넘쳤고, 둘째는 둘 다 150px 이라 넘치지 않았다. `…` 의 유무는 스크린샷으로 확인했다.)*

### (9) ★ `text-decoration` — 상속이 아니라 「그려서 관통한다」

**언제 쓰나** — 링크 안의 `<span>` 에서 밑줄을 못 끄겠을 때.

```text
  상속이라면                         실제(전파, propagation)
  ┌─────────────┐                   ┌─────────────┐
  │ 부모: 밑줄   │                   │ 부모: 밑줄   │  <- 부모가 '하나의 선'을 그린다
  │  └ 자손: 상속 │                   │  └ 자손      │     그 선이 자손 위를 지나간다
  │     값을 덮으면 꺼진다 │           │     자손은 그 선을 지울 수 없다 │
  └─────────────┘                   └─────────────┘
```

**실측** — 부모에 `text-decoration: underline wavy #c00 3px`, 자손에 `text-decoration: none`

```text
  자손의 getComputedStyle(...).textDecorationLine   ->  "none"
  자손의 getComputedStyle(...).textDecorationColor  ->  "rgb(0, 102, 204)"   (자기 color)

  그런데 스크린샷에서는
    out [child off] out
    ~~~~~~~~~~~~~~~~~~~     <- 빨간 물결선이 자손 구간까지 '끊김 없이' 지나간다
```

그림 해설 (한 단계씩):

- 자손의 **계산값은 정말 `none`** 이다. 자손은 자기 선을 안 그린다.
- 하지만 **부모가 그린 선은 자손 위를 그대로 지나간다.** 자손이 끌 수 있는 것이 아니다.
- 선의 **색·모양·두께도 부모 것**이다. 자손의 `color` 가 파랑이어도 선은 빨간 물결이다.
- 자손이 `text-decoration-line: line-through` 를 주면 **두 선이 겹쳐 그려진다**(부모 밑줄 + 자기 취소선).

★ **끄는 방법은 하나뿐 — 자손을 「원자 인라인」으로 만드는 것.**

```text
  out [inline-block] out
  ___            _____     <- 밑줄이 inline-block 앞뒤에서 끊긴다
```

실측에서 `display: inline-block` 을 준 자손은 **부모 밑줄이 그 구간에서 끊겼다.**\
`float`·`position: absolute`·표 셀 등도 같은 효과다. 다만 **인라인 흐름이 바뀌므로 대가가 크다.**

- 이것이 [03번](../03-inheritance-and-global-keywords/2-summary.md)의 상속과 **명확히 다른 자리**다.\
  상속은 「부모의 계산값을 자식 바구니에 넣는 것」이고, 자식이 자기 값을 쓰면 그만이다.\
  `text-decoration` 은 **부모가 자기 행 상자 위에 선을 하나 긋는 것**이라 자식의 값과 무관하다.
- ★ **`text-decoration-color` 는 진짜 상속 속성이 아니고, `text-decoration` 전체가 비상속이다.**\
  「자손에게 내려간 것처럼 보이는」 것은 전파이지 상속이 아니다.

> **전파(propagation)** — 부모가 그린 장식선이 자손 텍스트 위를 지나가는 것.\
> 예: `<a>` 의 밑줄이 그 안의 `<span>` 글자 밑에도 그어진다. `<span>` 이 끌 수 없다.

> **원자 인라인(atomic inline)** — 안을 들여다보지 않고 통째로 한 글자처럼 취급하는 인라인 상자.\
> 예: `inline-block`·`<img>`·`<input>`. 장식선이 이 상자를 관통하지 않는다.

```html demo
<p class="dec">바깥 <span class="off">자손이 껐다</span> 바깥</p>
<p class="dec">바깥 <span class="ib">원자 인라인</span> 바깥</p>
<style>
  .dec { font: 20px/30px sans-serif; text-decoration: underline wavy #c00 3px;
         text-underline-offset: 6px; }
  .off { text-decoration: none; color: #06c; }
  .ib  { display: inline-block; color: #06c; }
</style>
```

> **보이는 것** — 첫 줄은 **빨간 물결 밑줄이 파란 글자 구간까지 끊김 없이** 지나간다. 자손이 `text-decoration: none` 을 줬는데도 선이 그대로 있다.\
> 둘째 줄은 **파란 글자 구간에서 밑줄이 끊긴다** — 앞뒤 `바깥` 아래에만 물결선이 있고 가운데는 비어 있다.\
> 두 줄의 유일한 차이는 자손이 `inline-block` 이냐 아니냐다.\
> **바꿔 볼 것** — `.off` 에 `color: #06c` 만 남기고 `text-decoration: none` 을 빼도 → **첫 줄은 그대로다**(자손의 선언과 무관하다) · `.ib` 의 `display: inline-block` 을 빼면 → 둘째 줄도 첫 줄처럼 선이 관통한다

*(Chrome 151 headless 실측 — 두 자손의 계산값이 **둘 다 `text-decoration-line: none`** 인데 화면은 다르다. 스크린샷의 밑줄 행에서 빨간 픽셀을 세면 첫 줄은 **91개**(한 줄 전체), 둘째 줄은 **42개**(양끝 두 토막)였다.)*

### (10) `text-decoration` 의 네 칸과 위치 조정

**언제 쓰나** — 밑줄을 글자에서 떼거나 두께를 바꿀 때.

```text
  text-decoration: <line> || <style> || <color> || <thickness>
                    ^^^^^^   ^^^^^^^   ^^^^^^^    ^^^^^^^^^^^
                    underline  solid    red       3px
                    overline   double   currentColor
                    line-through wavy              auto / from-font
                    none       dotted
                               dashed

  따로 노는 두 속성(단축에 안 들어간다)
    text-underline-offset   밑줄을 글자에서 얼마나 떼나
    text-underline-position 밑줄을 어느 기준선에 놓나 (under / left / right)
    text-decoration-skip-ink 내려긋는 획(g·y·p)을 피해 끊나
```

**실측** — `text-decoration: underline wavy #c00 3px; text-underline-offset: 6px`

```text
  getComputedStyle(...).textDecoration          -> "underline 3px wavy rgb(204, 0, 0)"
  getComputedStyle(...).textDecorationThickness -> "3px"
  getComputedStyle(...).textUnderlineOffset     -> "6px"
```

- 직렬화 순서(`line thickness style color`)가 **내가 쓴 순서와 다르다.** 단축의 값 순서는 자유다.
- `text-underline-offset` 은 **단축에 안 들어간다** — `text-decoration:` 을 다시 써도 안 되돌아간다.
- `thickness: from-font` 는 글꼴이 권하는 두께를 쓴다 — **[50번](../50-fonts-and-webfonts/2-summary.md)과 이어지는 자리**다.

## 문법 — 형태와 어디서 헷갈리나

CSS 는 문법 표면이 단순하므로 이 절은 「형태」가 아니라 「**어디서 헷갈리나**」로 읽는다.

### 이름이 헷갈리는 짝

| 헷갈리는 짝 | 가르는 한 문장 |
|---|---|
| `word-break` ↔ `overflow-wrap` | 전자는 **기회를 더한다**, 후자는 **넘칠 때만 쪼갠다** |
| `overflow-wrap` ↔ `word-wrap` | **같은 속성**이다. `word-wrap` 은 옛 이름(별칭)이다 |
| `break-word`(overflow-wrap) ↔ `break-all`(word-break) | 값 이름이 비슷하지만 **다른 속성의 값**이다 |
| `overflow-wrap: break-word` ↔ `anywhere` | **내재적 크기 계산에 참여하느냐**가 유일한 차이다 |
| `white-space: nowrap` ↔ `text-wrap: nowrap` | 같은 롱핸드(`text-wrap-mode`)를 건드린다. **나중에 쓴 단축이 이긴다** |
| `text-overflow` ↔ `overflow` | 앞은 **표시만**, 뒤는 **자르기**. 앞은 뒤 없이는 안 먹는다 |
| `line-break` ↔ `word-break` | 앞은 CJK 의 **금칙 처리 강도**(`strict`/`loose`), 뒤는 **기회 자체** |

### 금지 사례 — 안 먹는 줄

```css
p { text-overflow: ellipsis; }                  /* overflow·한 줄이 없으면 아무 일도 안 난다 */
a span { text-decoration: none; }               /* 부모가 그린 선은 안 꺼진다 */
p { word-break: break-word; }                   /* 비표준 값 — Chrome 은 받지만 명세에 없다 */
h1 { text-wrap: balance; }                      /* 7줄 넘으면 Chrome 에서 아무 일도 안 난다 */
div { white-space: nowrap; text-wrap: balance; } /* nowrap 이 wrap 으로 되돌아간다 */
p { hyphens: auto; }                            /* lang 이 없으면(그리고 사전이 없으면) 안 먹는다 */
```

## 어디서 틀리나

### 1. ★ `overflow: hidden` 으로 「넘침」을 막으려 한다

긴 토큰이 상자를 뚫는 것은 **줄바꿈 기회가 없어서**다.\
`overflow: hidden` 은 **보이지만 않게** 할 뿐이고 글자는 여전히 잘린다.\
고치는 법은 `overflow-wrap: break-word` 로 **기회를 만드는 것**.

### 2. ★ `word-break: break-all` 을 본문에 건다

「URL 만 문제」인데 **모든 낱말이 잘린다.** (2)의 실측에서 `The` 가 첫 줄에 붙어 버린 것이 그 증상이다.\
긴 토큰만 대상이면 `overflow-wrap: break-word` 가 맞다.

### 3. ★ 「한국어에 `break-all` 을 걸면 어절이 잘린다」고 생각한다

(4)의 실측 — **한글은 기본값이 이미 글자마다 끊는다.** `break-all` 은 아무것도 안 바꿨다(여섯 폭 전부).\
어절을 지키려면 `keep-all` 을 **명시적으로 켜야** 한다. 안 켠 상태가 「어디서든 끊김」이다.

### 4. `keep-all` 을 좁은 칸에 건다

어절이 상자보다 길면 **그 어절이 통째로 넘친다.** 줄 수도 늘어난다(110px 에서 3 → 4줄).\
좁은 칸에서는 `keep-all` + `overflow-wrap: break-word` 를 **같이** 쓰는 것이 보통의 해법이다.

### 5. flex 아이템에 `overflow-wrap: anywhere` 를 건다

(3)의 실측 — `min-content` 가 **글자 하나 폭(14.03px)** 까지 내려간다.\
아이템이 예상보다 훨씬 좁아진다. 넘침만 막고 싶으면 `break-word`.

### 6. `text-overflow: ellipsis` 만 쓴다

세 조건 중 하나라도 빠지면 조용히 다른 결과가 나온다((8)의 표).\
특히 **`white-space: nowrap` 을 빼먹는 것**이 가장 흔하다.

### 7. ★ 링크 안의 `<span>` 에서 밑줄을 끄려 한다

`text-decoration: none` 을 줘도 **부모가 그린 선은 안 꺼진다**((9)).\
고치려면 `<a>` 쪽에서 끄거나, 그 `<span>` 을 `inline-block` 으로 만든다(대가가 크다).

### 8. `white-space: nowrap` 뒤에 `text-wrap` 단축을 쓴다

`text-wrap: balance` 가 `text-wrap-mode` 칸을 `wrap` 으로 채워 **`nowrap` 이 풀린다.**\
줄바꿈을 막으면서 균형을 잡을 수는 없다(애초에 한 줄이면 균형도 없다).

### 9. `text-wrap: balance` 를 본문에 건다

(6)의 실측 — **7줄부터 아무 일도 안 한다.** 효과가 없는데 있다고 믿는 상태가 된다.

### 10. `hyphens: auto` 만 쓰고 `lang` 을 안 단다

명세가 **콘텐츠 언어를 알아야** 자동 하이프네이션을 하도록 규정한다.\
★ 다만 이 환경에서는 `lang` 을 달아도 안 일어났다 — **사전이 없으면 `lang` 이 있어도 안 된다**((5)).

### 11. `word-wrap` 과 `overflow-wrap` 을 둘 다 쓴다

같은 속성의 옛 이름과 새 이름이라 **나중 것이 이긴다.** 둘 다 쓰면 캐스케이드만 헷갈려진다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 줄바꿈이 **기회 위에서만** 일어난다는 것 | **명세**(css-text-4 가 UAX #14 를 참조) |
| `word-break` 가 **기회를 더하고**, `overflow-wrap` 이 **넘칠 때만** 끼어드는 것 | **명세**(두 속성의 정의) |
| `anywhere` 는 내재적 크기에 참여하고 `break-word` 는 안 하는 것 | **명세**(`overflow-wrap` 정의가 명시) |
| **한글에 글자마다 기회가 있다**는 것 | **명세**(UAX #14 의 CJK 처리) |
| `keep-all` 이 **어절 경계만 남긴다**는 것 | **명세** |
| **`normal` 과 `break-all` 이 한글에서 같았다**는 것 | **관찰**(6가지 폭에서 전부 같음). 명세로부터 따라 나오지만 실측으로 확인했다 |
| `white-space` 가 **두 롱핸드의 단축**이라는 것 | **명세**(css-text-4). Baseline newly(2024-03-19) |
| `text-wrap` 이 `text-wrap-mode` + `text-wrap-style` 단축인 것 | **명세.** Baseline newly(2024-10-17) |
| `balance` 가 **6줄까지만** 도는 것 | **Chrome 151 의 구현값.** 명세는 「제한해도 된다」까지만 말한다 |
| `pretty` 가 마지막 줄을 늘린 것 | **관찰.** `pretty` 는 **Baseline limited** — 다른 엔진은 무시할 수 있다 |
| `text-overflow: ellipsis` 의 **세 조건** | **명세**(css-overflow-3 + `text-overflow` 정의) |
| `text-decoration` 이 **상속이 아니라 전파**라는 것 | **명세**(css-text-decor-4 「Text Decoration Propagation」) |
| **원자 인라인에서 선이 끊기는 것** | **명세**(같은 절) |
| **자동 하이프네이션이 안 일어난 것** | **이 환경의 사실.** 사전이 없다. 명세·다른 환경의 이야기가 아니다 |
| 이 문서의 **모든 px 폭** | **이 환경의 값.** 글꼴이 다르면 전부 달라진다([50번](../50-fonts-and-webfonts/2-summary.md)) |
| 이 문서의 **줄 수** | 폭에서 따라 나오므로 **역시 환경값**이다. 재현되는 것은 **대소 관계**다 |

**★ 이 주제에서 재현되는 것은 숫자가 아니라 부등호다.**\
「`keep-all` 이 줄을 더 쓴다」·「`break-all` 이 줄을 덜 쓴다」·「`anywhere` 가 `min-content` 를 줄인다」는
글꼴이 바뀌어도 성립하지만, **3줄이냐 4줄이냐는 이 글꼴·이 폭에서의 값**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 이렇게 |
|---|---|
| 사용자가 넣은 URL·이메일이 상자를 뚫는다 | `overflow-wrap: break-word` — 그 토큰만 쪼갠다 |
| 좁은 칸(칩·배지)에서 무조건 안 뚫려야 | `overflow-wrap: anywhere` — 단 폭이 더 좁아질 각오 |
| 코드·해시처럼 원래 잘라도 되는 것 | `word-break: break-all` |
| 한국어 본문 | `word-break: keep-all` + `overflow-wrap: break-word` |
| 한국어 **좁은 칸** | 기본값(끊기게 둔다). `keep-all` 은 줄을 늘린다 |
| 제목이 한 낱말만 넘어간다 | `text-wrap: balance` — 6줄 이하에서만 |
| 본문 마지막 줄이 너무 짧다 | `text-wrap: pretty` — Baseline 이 아니므로 **없어도 되게** 쓴다 |
| 한 줄 말줄임 | `overflow: hidden` + `white-space: nowrap` + `text-overflow: ellipsis` **셋 다** |
| 여러 줄 말줄임 | `text-overflow` 로는 안 된다 — `line-clamp` 쪽 |
| 링크 밑줄을 부분적으로 끄고 싶다 | **끌 수 없다.** 구조를 바꾸거나 `<a>` 쪽에서 끈다 |
| 밑줄이 글자에 붙어 답답하다 | `text-underline-offset` — 단축에 안 들어가니 따로 쓴다 |

## 핵심 문장

- 줄바꿈은 **기회 위에서만** 일어난다. 「긴 URL 이 상자를 뚫는다」는 기회가 없다는 뜻이지 `overflow` 문제가 아니다.
- **`word-break` 는 기회를 더하고, `overflow-wrap` 은 넘칠 때만 끼어든다.** 실측에서 같은 문장이 **3줄 / 2줄 / 3줄**로 갈렸다.
- **`break-word` 와 `anywhere` 의 유일한 차이는 내재적 크기 계산에 참여하느냐**다 — `min-content` 가 108.70px 대 14.03px 로 갈렸다.
- **한글은 기본값이 이미 「어디서든」이다.** `break-all` 은 아무것도 안 바꿨고, 어절을 지키려면 **`keep-all` 을 켜야** 한다 — 대가는 줄 하나(110px 에서 3 → 4줄).
- **`text-wrap: balance` 는 6줄까지만 돈다**(Chrome 151). 본문에 걸면 대개 아무 일도 안 일어난다.
- **`white-space` 와 `text-wrap` 은 같은 롱핸드(`text-wrap-mode`)를 공유하는 두 단축**이다 — 뒤에 쓴 쪽이 앞을 되돌린다.
- **`text-overflow: ellipsis` 는 세 조건이 동시에 맞아야** 한다. 하나만 빠져도 조용히 다른 결과가 난다.
- **`text-decoration` 은 상속이 아니라 전파**다 — 자손의 계산값은 `none` 인데 부모가 그린 선은 그대로 관통한다. 끊는 것은 **원자 인라인뿐**이다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 51번)
- [`../50-fonts-and-webfonts/2-summary.md`](../50-fonts-and-webfonts/2-summary.md) — **이 주제의 앞 칸이자 선행.**\
  **어느 글꼴로 그리나가 정해져야 어디서 줄이 바뀌나가 정해진다.** 글자 폭·`font` 단축·대체 사슬은 거기, **줄 수**는 여기다.
- [`../03-inheritance-and-global-keywords/2-summary.md`](../03-inheritance-and-global-keywords/2-summary.md) — **상속의 정본.**\
  「무엇이 상속되나」는 거기, 여기는 「**`text-decoration` 은 상속이 아니다**」라는 대비 하나만 쓴다.
- [`../07-syntax-and-error-recovery/2-summary.md`](../07-syntax-and-error-recovery/2-summary.md) — **오류 복구의 정본.**\
  `word-break: break-word` 같은 비표준 값이 조용히 버려지거나 조용히 받아들여지는 이유가 거기다.
- [목록의 **19번 주제**](../19-inline-formatting-context/)(인라인 서식 문맥·행 상자·`line-height`·`vertical-align`) — **행 상자의 정본.**\
  이 문서는 **줄이 몇 개 생기나**까지만 다루고, **그 줄이 얼마나 높은가**는 전부 그쪽이다.
- [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)(내재적 크기 — `min-content`/`max-content`) — **내재적 크기의 정본.**\
  여기서는 `anywhere` 와 `break-word` 가 **그 계산에 참여하느냐**만 다룬다.
- [목록의 **23번 주제**](../23-overflow-and-scroll-containers/)(오버플로·스크롤 컨테이너) — `overflow` 가 무엇을 만드는지. `text-overflow` 는 그 위에 얹히는 표시다.
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **줄바꿈 기회(break opportunity)** — 줄을 바꿔도 되는 지점. 띄어쓰기·하이픈 뒤·CJK 글자 사이.
- **행 상자(line box)** — 한 줄을 담는 상자. 이 문서의 「줄 수」는 이것의 개수다.
- **UAX #14** — 유니코드의 줄바꿈 알고리즘 표준. 기본 기회가 어디 있는지를 정한다.
- **`word-break`** — 기회를 **더하거나 빼는** 속성. `break-all` / `keep-all`.
- **`overflow-wrap`(구 `word-wrap`)** — **넘칠 때만** 낱말을 쪼개는 속성. `break-word` / `anywhere`.
- **`break-word` ↔ `anywhere`** — 내재적 크기 계산 참여 여부가 유일한 차이.
- **어절** — 띄어쓰기로 구분되는 한국어의 덩어리. `keep-all` 이 지키는 단위.
- **내재적 크기** — 내용만으로 정해지는 폭. `min-content` 는 「더 줄이면 넘치기 시작하는 폭」.
- **소프트 하이픈(U+00AD)** — 보이지 않는 「여기서 끊어도 좋다」 표시. `hyphens: manual` 이 쓰는 것.
- **`text-wrap: balance`** — 줄 길이를 고르게 만드는 값. Chrome 151 은 **6줄까지만** 적용한다.
- **`text-wrap: pretty`** — 마지막 줄이 너무 짧아지지 않게 고르는 값. Baseline **limited**.
- **`white-space-collapse` / `text-wrap-mode`** — `white-space` 를 쪼갠 두 롱핸드.
- **`text-overflow`** — 잘린 자리에 표시를 넣는 속성. **자르기는 `overflow` 가 한다.**
- **전파(propagation)** — 부모가 그린 장식선이 자손 위를 지나가는 것. 상속이 아니다.
- **원자 인라인(atomic inline)** — 통째로 한 글자처럼 취급되는 인라인 상자. 장식선이 관통하지 않는다.
- **`text-underline-offset`** — 밑줄을 글자에서 떼는 거리. `text-decoration` 단축에 안 들어간다.

## 더 들어가면

- **`line-break`** — CJK 의 금칙 처리 강도(`auto`/`loose`/`normal`/`strict`/`anywhere`). 「줄 첫머리에 올 수 없는 글자」를 얼마나 엄하게 다룰지 정한다. Baseline widely(2020-07-28 → 2023-01-28). 이 문서에서는 실행하지 않았다.
- **`hanging-punctuation`** — 따옴표를 줄 밖으로 내보내 왼쪽 정렬을 가지런히 만든다.
- **`text-spacing-trim`** — CJK 괄호·문장부호의 좌우 여백을 다듬는 신규 속성.
- **`text-decoration-skip-ink`** — 내려긋는 획(`g`·`y`·`p`)에서 밑줄을 끊는다. 기본값이 `auto` 라 이미 켜져 있다.
- **`line-clamp`(구 `-webkit-line-clamp`)** — 여러 줄 말줄임. `text-overflow` 로 못 하는 것을 한다.
- **`text-emphasis`** — 한중일 강조점. Baseline widely(2022-03-03 → 2024-09-03).
