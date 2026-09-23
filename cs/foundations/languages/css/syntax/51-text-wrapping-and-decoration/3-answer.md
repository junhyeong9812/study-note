# css/syntax/51 — 텍스트 줄바꿈·서식·장식: `word-break`·`overflow-wrap`·`text-wrap`·`text-decoration` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 줄 수·줄 폭은 Google Chrome 151.0.7922.173 headless(Linux)에서 실제로 측정한 것**이다.\
> 줄은 `Range.selectNodeContents(el).getClientRects()` 로 세고, 눈으로 봐야 하는 것은 CDP 스크린샷으로 확인했다.\
> ⚠️ **줄 수는 글꼴에 달려 있다.** 재현되는 것은 3이냐 4냐가 아니라 **부등호**다 — 선행이 [50번](../50-fonts-and-webfonts/2-summary.md)인 이유다.\
> 규칙은 [CSS Text 4](https://drafts.csswg.org/css-text-4/) · [CSS Text Decoration 4](https://drafts.csswg.org/css-text-decor-4/) · [CSS Overflow 3](https://drafts.csswg.org/css-overflow-3/) 로 접지했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 이 셋은 각각 몇 줄이 되는가

**실행 결과** (Chrome 151 headless — 240px 상자, 줄 폭은 행 상자의 `width`)

```text
  (가) 기본                       줄 3개   28.17 | 314.31 | 40.50
  (나) word-break: break-all      줄 2개  237.55 | 154.39
  (다) overflow-wrap: break-word  줄 3개   28.17 | 237.39 | 122.09
```

**줄 수**

- **3 / 2 / 3.**

**어느 것이 뚫는가**

- **(가)** 뿐이다. 둘째 줄이 **314.31px** 로 240px 상자를 **74px** 넘겼다.
- (나)·(다)는 가장 넓은 줄이 각각 237.55px·237.39px 로 상자 안에 들어간다.

**`break-all` 과 `break-word` 의 줄 수가 다른 이유**

```text
  break-all   : 줄바꿈 '기회'를 글자마다 만든다(②단계)
                -> 첫 줄을 끝까지 채우는 것이 가능해진다 -> "The ThisIsAnExtrem"
  break-word  : 기회는 그대로 두고, '넘칠 때만' 그 낱말을 쪼갠다(④단계)
                -> "The" 다음 낱말이 한 줄에 안 들어가니 줄을 바꾸고, 그 낱말만 쪼갠다
```

- 둘은 **다른 단계에서 끼어든다.** 겉보기 증상(「안 뚫린다」)만 같다.

**첫 줄에 `The` 만 남는 쪽**

- **(다) `break-word`** 다. 첫 줄 폭이 28.17px 로 「The」 하나다.
- (나)는 237.55px — `The` 뒤에 긴 토큰의 앞부분이 같이 실렸다.

### 2. `min-content` 상자의 폭은 얼마가 되는가

**실행 결과** (Chrome 151 headless — `Hydroelectric plant`, `width: min-content`)

```text
  overflow-wrap: normal       폭 108.703125px   줄 2개 (106.70 · 40.83)
  overflow-wrap: break-word   폭 108.703125px   줄 2개 (106.70 · 40.83)
  overflow-wrap: anywhere     폭  14.03125px    줄 17개
  word-break:    break-all    폭  14.03125px    줄 17개
```

**두 상자의 폭은 같은가**

- **다르다.** 108.70px 대 14.03px.

**`break-word` 는 안 쓴 것과 같은가**

- **크기 계산에 한해서는 같다.** `normal` 과 폭도 줄 수도 한 글자도 안 달랐다.
- 다만 **폭이 밖에서 정해진 상자**에서는 다르다 — 1번이 그 경우다.

**`anywhere` 쪽 폭은 무엇으로 정해지나**

- **가장 넓은 글자 하나의 폭**이다. 「쪼갤 수 있다」가 `min-content` 계산에 반영되므로,
  더 줄여도 넘치지 않는 하한이 글자 하나가 된다.

**flex 아이템에 걸면**

- 그 아이템의 `min-content` 가 글자 하나 폭까지 내려가므로 **극단적으로 좁아질 수 있다.**
- 「넘침만 막고 싶다」면 `break-word` 가 맞다.
- 내재적 크기 자체는 [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)가 정본이다.

### 3. 한국어에서 셋은 어떻게 갈리는가

**실행 결과** (Chrome 151 headless — `줄바꿈기회는 브라우저가 스스로 정하는 것이다`)

```text
  상자 110px
    기본       줄 3개   108 | 108 |  93
    break-all  줄 3개   108 | 108 |  93      <- 기본과 한 글자도 안 다르다
    keep-all   줄 4개    88 |  74 |  93 | 44

  상자 190px
    기본       줄 2개   186 | 127
    break-all  줄 2개   186 | 127
    keep-all   줄 2개   166 | 141            <- 줄 수는 같고 끊는 자리가 다르다
```

**줄 수**

- 110px 에서 **3 / 3 / 4.**

**기본과 `break-all` 은 다른가**

- **똑같다.** 110·130·150·170·190·210px 여섯 폭에서 **전부** 같았다.
- 이유는 **한글에는 이미 글자마다 줄바꿈 기회가 있기 때문**이다(유니코드 줄바꿈 규칙의 CJK 처리).\
  `break-all` 이 더 찍을 점선이 없다.
- ★ 그래서 「한국어에 `break-all` 을 걸면 어절이 잘린다」는 말은 정확하지 않다 —\
  **안 걸어도 이미 잘린다.**

**`keep-all` 은 줄을 더 쓰는가**

- **더 쓴다.** 110px 에서 3줄 → **4줄**. 어절을 지키는 대가가 **세로 공간**이다.

**190px 로 넓히면**

- 줄 수가 **셋 다 2줄**로 같아지고, **끊는 위치만** 다르다(186/127 대 166/141).
- 즉 `keep-all` 의 비용은 **폭이 좁을수록** 커진다.

### 4. `hyphens` 세 값은 어떻게 갈리는가

**실행 결과** (Chrome 151 headless — 100px 상자, `extra&shy;ordi&shy;narily compli&shy;cated`)

```text
  hyphens: none      줄 2개   117 |  98      <- 117px 이 100px 상자를 뚫었다
  hyphens: manual    줄 4개    72 |   6 | 45 | 98
  hyphens: auto      줄 4개    72 |   6 | 45 | 98

  소프트 하이픈이 없는 텍스트("extraordinarily complicated")
  hyphens: auto                줄 2개   117 |  98
  hyphens: auto  lang="en-US"  줄 2개   117 |  98
  hyphens: auto  lang="de" (독일어 문장)  줄 2개   122 | 146
```

**앞의 셋**

- **2 / 4 / 4줄.** `none` 은 소프트 하이픈을 **무시**하고, `manual` 과 `auto` 는 쓴다.
- `manual` 이 기본값이므로, 아무것도 안 쓰면 소프트 하이픈은 동작한다.

**소프트 하이픈이 없는 넷째**

- **2줄.** `auto` 인데 **자동 하이프네이션이 전혀 일어나지 않았다.**

**`lang` 을 `de` 로 바꾸면**

- **안 달라졌다.** 독일어 긴 낱말도 끊기지 않고 그대로 넘쳤다.

**잰 것과 못 잰 것**

- **잰 것** — `none` / `manual` / `auto` 가 **소프트 하이픈을 쓰느냐**로 갈린다(2줄 대 4줄).
- ★ **못 잰 것** — 「`lang` 이 있어야 자동 하이프네이션이 먹는다」.\
  「안 돌려 봤다」가 아니다. **던졌는데 이 환경의 Chrome 에 하이프네이션 사전이 없어서**
  `lang` 을 무엇으로 바꿔도 결과가 안 움직였고, 그래서 **판정 자체가 성립하지 않았다.**
- 명세는 `hyphens: auto` 가 **콘텐츠 언어를 알 때만** 자동 하이프네이션을 하도록 규정한다 —\
  그 규칙은 **명세로 접지**하고 실측으로 적지 않는다.

### 5. `text-wrap: balance` 는 언제 아무 일도 안 하는가

**실행 결과** (Chrome 151 headless — 260px 상자, 낱말 수를 늘려 가며 `wrap` 과 줄 폭을 비교)

```text
  줄 수    1    2    3    4    5    6    7    8    9   10   11
  효과     -    O    O    O    O    O    X    X    X    X    X

  예) 4줄짜리
    wrap    : 255 | 251 | 236 |  93
    balance : 204 | 181 | 233 | 216
  예) 7줄짜리
    wrap    : 256 | 236 | 235 | 214 | 231 | 209 |  84
    balance : 256 | 236 | 235 | 214 | 231 | 209 |  84     <- 완전히 같다
```

**4줄짜리에서**

- 마지막 줄이 93px 로 혼자 짧던 것을 **넷을 고르게** 폈다(204·181·233·216).

**10줄짜리에서**

- **아무것도 안 한다.** `wrap` 과 줄 폭이 한 자리도 안 달랐다.

**경계**

- **6줄까지 적용되고 7줄부터 안 한다.**

**명세가 정한 숫자인가**

- **아니다.** 명세는 「UA 가 균형 맞추기를 **제한된 줄 수로 한정해도 된다**」고 허용할 뿐이다.\
  **6은 Chrome 151 의 구현값**이고, 다른 브라우저·다음 버전에서는 다를 수 있다.
- 그래서 `balance` 는 **제목·캡션용**이다. 본문에 걸면 대개 아무 일도 안 일어난다.

### 6. `text-overflow: ellipsis` 는 언제 찍히는가

**실행 결과** (Chrome 151 headless — 150px 상자, `한 줄에 안 들어가는 긴 문장이다`)

```text
                                     높이   scrollW/clientW   화면
  hidden + nowrap + ellipsis         26px   214 / 150        "한 줄에 안 들어가는…"
  hidden + ellipsis (nowrap 없음)     50px   150 / 150        두 줄로 접힌다, … 없음
  nowrap + ellipsis (hidden 없음)    26px   214 / 150        테두리 밖으로 삐져나간다
  hidden + nowrap (ellipsis 없음)    26px   214 / 150        글자 중간에서 뚝 잘린다
```

**`…` 이 찍히는 것**

- **첫째뿐**이다. 셋이 동시에 맞아야 한다.

**`white-space: normal` 인 상자**

- 그냥 **두 줄로 접힌다.** 넘치지 않으므로(`scrollWidth == clientWidth`) 잘릴 것도 없다.

**`overflow: visible` 인 상자**

- 한 줄인 채로 **테두리 밖으로 그대로 나간다.** 자르지 않으니 `…` 도 없다.

**두 줄짜리 말줄임**

- **이 속성으로는 못 한다.** `line-clamp`(구 `-webkit-line-clamp`) 영역이다.

> **`text-overflow` 는 자르지 않는다** — 자르는 것은 `overflow` 이고,
> 이 속성은 **잘린 자리에 표시를 넣을 뿐**이다. 그래서 `overflow` 없이는 할 일이 없다.

### 7. 이 자손은 밑줄을 끌 수 있는가

**실행 결과** (Chrome 151 headless)

```text
  .off (text-decoration: none)     textDecorationLine = "none"
                                   textDecorationColor = "rgb(0, 102, 204)"
  .ib  (display: inline-block)     textDecorationLine = "none"
  부모 (.dec)                      textDecoration = "underline 3px wavy rgb(204, 0, 0)"

  스크린샷의 밑줄 행에서 빨간 픽셀 수
    첫 줄 (.off)  91개   <- 줄 전체에 끊김 없이 그어져 있다
    둘 줄 (.ib)   42개   <- 앞뒤 두 토막뿐, 가운데가 비었다
```

**두 줄의 화면은 같은가**

- **다르다.** 첫 줄은 물결선이 관통하고, 둘째 줄은 자손 구간에서 **끊긴다.**

**두 자손의 계산값**

- **둘 다 `none`** 이다.

**계산값이 같은데 화면이 다른 이유**

- `text-decoration` 은 **상속이 아니라 전파**이기 때문이다.
- 자손의 계산값은 「**자손이 자기 선을 그리느냐**」를 말할 뿐이고,
  화면의 선은 **부모가 자기 행 상자 위에 그린 하나의 선**이다.
- 그 선은 자손 위를 지나가고, **자손은 그것을 지울 수 없다.**
- 끊기는 것은 자손이 **원자 인라인**이 됐을 때뿐이다. `inline-block`·`float`·`absolute`·표 셀 등.

```text
  상속이라면                          실제(전파)
  부모 값 -> 자식 바구니에 담긴다      부모가 '선 하나'를 긋는다
  자식이 자기 값을 쓰면 그만이다       자식의 값과 무관하게 그 선이 지나간다
```

**자손이 `line-through` 를 주면**

- **두 선이 겹쳐 보인다** — 부모의 밑줄(부모 색·모양)과 자손의 취소선(자손 색)이 둘 다 그려진다.
- 실측에서 부모 검은 밑줄 + 자손 파란 취소선이 함께 보였다.

### 8. 왜 `overflow: hidden` 으로는 안 되는가

**근본 원인**

- 그 토큰 안에 **줄바꿈 기회가 하나도 없기** 때문이다.\
  브라우저는 상자 끝에 닿으면 **직전 기회로 되돌아가** 자르는데, 되돌아갈 곳이 없다.

**`overflow: hidden` 이 바꾸는 것**

- 바뀌는 것 — **넘친 부분이 안 보인다**(그리고 스크롤 컨테이너가 생기며 BFC 도 생긴다).
- **안 바뀌는 것** — 줄 수도, 줄 폭도, 글자가 잘린다는 사실도 그대로다.\
  1번 실측의 314.31px 줄은 여전히 314.31px 이고 **뒷부분을 읽을 수 없다.**

**고치는 속성과 단계**

- `overflow-wrap: break-word`(또는 `anywhere`).
- 파이프라인의 **④단계**다 — ②에서 기회를 못 찾고 ③에서 넘치는 것이 확정된 **뒤에** 끼어든다.
- `word-break: break-all` 은 **②단계**에서 기회를 더하므로 결과가 다르다(1번).

### 9. `white-space` 와 `text-wrap` 은 어떤 관계인가

**실행 결과** (Chrome 151 headless — 계산값)

```text
  white-space: pre-wrap          ->  white-space-collapse: preserve      text-wrap-mode: wrap
  white-space: nowrap            ->  white-space-collapse: collapse      text-wrap-mode: nowrap
  white-space: break-spaces      ->  white-space-collapse: break-spaces  text-wrap-mode: wrap
  white-space-collapse: preserve ->  white-space 가 "pre-wrap" 으로 읽힌다
  text-wrap: balance             ->  text-wrap-mode: wrap   text-wrap-style: balance
```

**`pre-wrap` 을 쪼개면**

- `white-space-collapse: preserve` + `text-wrap-mode: wrap`.

**롱핸드만 썼을 때**

- `white-space` 가 **`"pre-wrap"` 으로 직렬화**된다. 진짜 단축이라는 증거다.

**`nowrap` 뒤에 `balance` 를 쓰면**

- **줄바꿈이 안 막힌다.** `text-wrap` 단축이 `text-wrap-mode` 칸을 `wrap` 으로 채운다.

**캐스케이드인가 단축인가**

- **단축**이다. 명시도 싸움이 아니라, **단축이 자기가 덮는 칸을 채우는** 규칙이다 —\
  [50번](../50-fonts-and-webfonts/2-summary.md)의 `font` 가 `font-weight` 를 되돌리는 것과 **정확히 같은 규칙**이다.
- `white-space` 와 `text-wrap` 은 **`text-wrap-mode` 라는 칸을 공유한다.** 둘 다 쓰면 뒤가 이긴다.

### 10. `word-wrap` 과 `overflow-wrap` 은 무엇이 다른가

**다른 것인가**

- **같은 속성**이다. `word-wrap` 이 옛 이름이고 `overflow-wrap` 이 표준 이름이다.\
  브라우저는 `word-wrap` 을 **별칭**으로 계속 받는다.

**`word-break: break-word` 라고 쓰면**

**실행 결과** (Chrome 151 headless — 240px 상자, 1번과 같은 문장)

```text
  word-break: break-word
    cssText                     "... word-break: break-word; ..."   <- 담겼다
    getComputedStyle word-break "break-word"
    getComputedStyle overflow-wrap "normal"                          <- 이쪽은 안 건드린다
    줄 3개   28.17 | 237.39 | 122.09
             ^^^^^^^^^^^^^^^^^^^^^^  overflow-wrap: break-word 와 한 자리도 안 다르다
```

- Chrome 은 **받는다.** 그리고 결과가 `overflow-wrap: break-word` 와 **정확히 같다.**
- 하지만 이것은 **명세에 없는 값**이고, 옛 코드를 살려 두려고 남긴 호환 동작이다. 새 코드에 쓸 값이 아니다.
- 표준에 없는 값이므로 **다른 엔진에서 조용히 버려질 수 있다**([07번](../07-syntax-and-error-recovery/2-summary.md)).

**이름이 비슷한데 속성이 다른 짝 셋**

```text
  word-break: break-all      <->  overflow-wrap: break-word
  white-space: nowrap        <->  text-wrap: nowrap
  line-break: anywhere       <->  overflow-wrap: anywhere
```

- 앞의 두 짝은 **각각 다른 단계**에서 일하고, 셋째 짝은 **CJK 금칙 강도** 대 **넘침 처리**다.
- 값 이름만 외우면 반드시 틀리는 자리다 — **속성 이름과 묶어서** 외운다.

### 11. 다른 주제와 잇기

**줄 수가 머신마다 다를 수 있는 이유**

- **글꼴이 다르면 글자 폭이 다르고, 폭이 다르면 줄 수가 다르다.**\
  [50번](../50-fonts-and-webfonts/2-summary.md)의 실측에서 같은 40px `Handgloves` 가
  글꼴에 따라 191px \~ 239px 로 갈렸다 — 25% 차이면 줄 하나가 바뀌고도 남는다.
- 그래서 이 문서의 숫자는 **이 환경의 값**이고, 재현되는 것은 **부등호**다.

**`font: 16px sans-serif` 한 줄이 줄 수에 영향을 주는가**

- **준다.** 글꼴·크기를 바꾸는 것은 물론이고, **`font-weight`·`font-stretch` 를 되돌리는 것**만으로도
  글자 폭이 달라져 줄 수가 바뀔 수 있다([50번](../50-fonts-and-webfonts/2-summary.md)의 실측 — `Ubuntu` 에서 400과 700의 폭이 129.77px 대 134.92px).
- 그래서 **글꼴이 먼저 정해져야 줄바꿈이 정해진다.**

**줄 높이를 다루지 않는 이유**

- **행 상자의 높이**는 [목록의 **19번 주제**](../19-inline-formatting-context/)가 정본이기 때문이다.\
  이 문서는 「줄이 **몇 개** 생기나」까지만 다루고, 「그 줄이 **얼마나 높은가**」는 넘긴다.
- 두 주제가 만나는 자리는 하나다 — **줄 수 × 줄 높이 = 상자 높이.**

**`anywhere` 가 `min-content` 를 바꾸는 것**

- [목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)(내재적 크기)와 이어진다. 거기가 `min-content`/`max-content` 의 정본이고,
  여기서는 **이 두 값이 그 계산에 참여하느냐**만 다룬다.

**전파와 상속의 차이를 한 문장으로**

- **상속은 값이 내려가는 것이고, 전파는 선이 지나가는 것이다.**\
  값은 자식이 덮을 수 있지만, 선은 자식이 지울 수 없다([03번](../03-inheritance-and-global-keywords/2-summary.md)).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `devicePixelRatio = 1`.\
**엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**줄 수를 세는 법** — 요소의 `offsetHeight` 를 `line-height` 로 나누지 않고, **행 상자를 직접 센다.**

```js
function LINES(sel){
  const e = document.querySelector(sel);
  const r = document.createRange();
  r.selectNodeContents(e);                 // 텍스트 전체를 감싼 Range
  return [...r.getClientRects()];          // 행 상자 하나당 사각형 하나
}
// 줄 수 = 길이, 줄 폭 = 각 사각형의 width
```

★ **한계 하나** — `text-overflow: ellipsis` 가 켜진 한 줄에서는 이 방법이 **2를 돌려준다**(말줄임 표시가 별도 사각형이 된다). 그 경우에만 **상자 높이**로 줄 수를 판정했다.

**하네스** — 문서 조각과 프로브 스크립트를 합쳐 한 문서로 만들고 결과를 `<pre>` 에 써 넣은 뒤 `--dump-dom` 에서 잘라 읽는다. 눈으로 봐야 하는 것(`…` 의 유무, 밑줄이 끊기나)은 `--remote-debugging-port` 로 CDP 에 붙어 `Page.captureScreenshot` 을 찍고 **픽셀을 세서** 판정했다.

```bash
google-chrome --headless --disable-gpu --no-sandbox --dump-dom /tmp/doc.html 2>/dev/null \
  | sed -n '/&lt;&lt;&lt;BEGIN&gt;&gt;&gt;/,/&lt;&lt;&lt;END&gt;&gt;&gt;/p' | sed '1d;$d'
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `word-break` 3값 × `overflow-wrap` 3값, 240px 상자 | 2 | 동작 방식 (2) · A1 |
| `min-content` × 4조합 | 1 | 동작 방식 (3) · A2 |
| 한국어 × 3값 × 상자 폭 6가지(110\~210px) | 2 | 동작 방식 (4) · A3 |
| `hyphens` 3값 × 소프트 하이픈 유무 × `lang` 3가지 | 2 | 동작 방식 (5) · A4 |
| `text-wrap` 3값 × 낱말 수 18가지(줄 수 1\~11) | 3 | 동작 방식 (6) · A5 |
| `white-space` 4형태의 두 롱핸드 계산값 | 1 | 동작 방식 (7) · A9 |
| `text-overflow` 4조합 + 스크린샷 | 2 | 동작 방식 (8) · A6 |
| `text-decoration` 전파 3형태 + 스크린샷 픽셀 판정 | 3 | 동작 방식 (9) · A7 |
| `text-decoration` 단축·`thickness`·`offset` 계산값 | 1 | 동작 방식 (10) |
| demo 4개(끊기 3형태 · `keep-all` · `ellipsis` · 전파) | 각 1 | 2-summary 의 demo |
| demo 의 「바꿔 볼 것」 단언 6개 | 각 1 | 2-summary 의 demo |

**구현에 달린 항목** — 버전·머신이 바뀌면 다시 찍을 자리다.

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| 모든 줄 폭·줄 수 | 표 참조 | **글꼴에 달렸다.** 재현되는 것은 부등호다 |
| `balance` 의 줄 수 상한 = **6** | 7줄부터 효과 없음 | **명세는 「제한해도 된다」까지만 말한다.** Chrome 구현값 |
| `text-wrap: pretty` 가 동작한 것 | 215/196/179/127 | **Baseline limited** — 다른 엔진은 무시할 수 있다 |
| `word-break: break-word` 를 Chrome 이 받는 것 | 계산값 `break-word`, 결과는 `overflow-wrap: break-word` 와 동일 | **표준에 없는 호환 값.** 다른 엔진은 버릴 수 있다 |
| `text-overflow: "→"`(문자열 값)을 **버린 것** | 계산값 `clip`, `cssText` 가 `""` | 명세(css-overflow-4)는 문자열을 허용하는데 **Chrome 151 은 안 받았다** |

**못 잰 것** — **`hyphens: auto` 의 `lang` 의존성.** 이 환경의 Chrome 에 하이프네이션 사전이 없어
`lang` 을 `en`·`en-US`·`de` 로 바꿔 가며 던져도 줄 폭이 한 자리도 안 움직였다.\
「안 돌려 봤다」가 아니라 **측정의 전제가 없어서 판정이 안 서는 제3의 상태**다.\
쪼개서 잰 조각 — `none`/`manual`/`auto` 가 **소프트 하이픈**을 쓰느냐는 갈렸다(2줄 대 4줄).

**안 돌려 본 것** — ① `line-break` 의 `strict`/`loose` 차이 ② `hanging-punctuation` ③ `line-clamp` 로 여러 줄 말줄임 ④ `text-decoration-skip-ink` 를 껐을 때의 차이. 넷 다 이 문서에서 결론으로 쓰지 않았다.

## 용어 풀이

- **줄바꿈 기회(break opportunity)** — 줄을 바꿔도 되는 지점. 띄어쓰기·하이픈 뒤·CJK 글자 사이.
- **행 상자(line box)** — 한 줄을 담는 상자. 이 문서의 「줄 수」는 이것의 개수다.
- **UAX #14** — 유니코드 줄바꿈 알고리즘. 기본 기회가 어디 있는지를 정한다.
- **`word-break`** — 기회를 더하거나 빼는 속성(②단계). `break-all` / `keep-all`.
- **`overflow-wrap`** — 넘칠 때만 낱말을 쪼개는 속성(④단계). `break-word` / `anywhere`. 옛 이름은 `word-wrap`.
- **`break-word` ↔ `anywhere`** — **내재적 크기 계산에 참여하느냐**가 유일한 차이.
- **어절** — 띄어쓰기로 나뉘는 한국어 덩어리. `keep-all` 이 지키는 단위.
- **내재적 크기** — 내용만으로 정해지는 폭. `min-content` 는 「더 줄이면 넘치기 시작하는 폭」.
- **소프트 하이픈(U+00AD)** — 보이지 않는 「여기서 끊어도 좋다」 표시.
- **`text-wrap: balance`** — 줄 길이를 고르게 만드는 값. Chrome 151 은 **6줄까지만** 적용한다.
- **`text-wrap: pretty`** — 마지막 줄이 짧아지지 않게 고르는 값. Baseline limited.
- **`white-space-collapse` / `text-wrap-mode`** — `white-space` 를 쪼갠 두 롱핸드. 뒤엣것은 `text-wrap` 과 공유한다.
- **`text-overflow`** — 잘린 자리에 표시를 넣는 속성. 자르는 것은 `overflow` 다.
- **전파(propagation)** — 부모가 그린 장식선이 자손 위를 지나가는 것. **상속이 아니다.**
- **원자 인라인(atomic inline)** — 통째로 한 글자처럼 취급되는 상자. 장식선이 관통하지 않는다.
- **`text-underline-offset`** — 밑줄을 글자에서 떼는 거리. `text-decoration` 단축에 안 들어간다.
