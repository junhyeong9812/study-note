# css/syntax/50 — 글꼴과 웹폰트: `font` 단축·`@font-face`·`font-display`·가변 폰트 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [CSS Fonts Module Level 4](https://drafts.csswg.org/css-fonts-4/) (`font` 단축·매칭 알고리즘·`@font-face` 기술자·`font-display`) · [CSS Fonts Module Level 5](https://drafts.csswg.org/css-fonts-5/) (`src` 의 `tech()`·`font-palette`) · [CSS Font Loading Module Level 3](https://drafts.csswg.org/css-font-loading/) (`document.fonts`·`FontFaceSet.check()`). 열어서 확인한 것만 적었다.
> **실행 검증** — **Google Chrome 151.0.7922.173** headless · Linux · `devicePixelRatio = 1`. 이 문서의 폭 수치는 전부 그 환경의 `getBoundingClientRect().width` 실측이다.\
> 웹폰트 실험에는 **직접 만든 740바이트짜리 최소 TTF** 를 `data:` URI 로 넣어 썼다(외부 URL 은 쓰지 않았다). `font-display` 다섯 값만 **응답을 일부러 늦추는 로컬 HTTP 서버**로 쟀다.\
> **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다 — 크로스 브라우저 차이는 Baseline 데이터로만 접지했다.
> **버전** — `font-family`·`@font-face`·`font-display`·`font-variation-settings` 는 전부 Baseline **widely**. `font-size-adjust` 만 **newly**(2024-07-25). 날짜는 `api.webstatus.dev` 조회 결과이고 아래 「구현 세부사항 대 언어 보장」에 다시 적었다.
> ⚠️ **글꼴은 환경이다.** 여기 적힌 폭 수치는 **이 머신에 설치된 글꼴에 달려 있다.** 다른 머신에서는 숫자가 달라진다 — 재현되는 것은 숫자가 아니라 **「같으냐 다르냐」라는 판정**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 값은 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**`font-family` 는 글꼴이 아니라 「글꼴을 찾아 달라는 쪽지」다.**

비유 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 통역사를 부르는 쪽지 | `font-family: Georgia, serif` — **이름 목록**이다 |
| 쪽지에 적힌 이름 순서 | 후보 순서. 앞에서부터 찾는다 |
| 사무실 명부 | 그 머신에 설치된 글꼴 + `@font-face` 로 등록한 이름 |
| 명부에 없으면 다음 이름 | 대체(fallback) |
| **글자 하나가 통역 한 건** | 대체는 **글자 단위**로 다시 일어난다 |
| 내가 데려온 통역사 | `@font-face` 로 파일을 딸려 보낸 웹폰트 |
| 통역사가 도착할 때까지 | `font-display` — 입 다물고 기다리나(FOIT), 임시로 말하나(FOUT) |
| 통역사 한 명이 억양을 조절 | 가변 폰트 — 한 파일이 굵기·너비를 연속으로 낸다 |

- 쪽지는 **요청**이고, 실제로 누가 왔는지는 쪽지에 안 적힌다.\
  그래서 `getComputedStyle(el).fontFamily` 를 읽으면 **내가 적은 목록이 그대로 돌아온다.**\
  없는 이름을 적어도 그대로 돌아온다 — **이것이 이 주제 최대의 함정**이다.
- 이름이 없으면 브라우저는 조용히 다음 후보로 내려간다. **에러도 경고도 없다.**
- 그래서 「글꼴이 안 먹는다」는 증상과 「글꼴이 잘 먹었다」는 정상이 **화면에서 구별되지 않는 경우**가 있다.

```text
       내가 쓴 것                    브라우저가 한 일                내가 읽을 수 있는 것

  font-family: Georgia,        Georgia 있나? -> 없다              getComputedStyle
               serif;          serif   있나? -> 있다(Noto Serif)    -> "Georgia, serif"
                                                                      ^^^^^^^
                                                                   쓴 그대로 돌아온다
```

실무에서 이게 터지는 자리는 **디자인 시안과 다른 글꼴로 배포되는 것**이다.\
개발자 머신에는 그 글꼴이 깔려 있고 서버에는 없다 — 화면은 멀쩡히 글자가 보이므로 아무도 못 잡는다.

> **대체(fallback)** — 목록의 앞 이름으로 못 그릴 때 다음 이름으로 내려가는 것.\
> 예: `Georgia, serif` 에서 Georgia 가 없으면 `serif` 로 내려간다. 내려간 사실은 어디에도 기록되지 않는다.

> **글리프(glyph)** — 글꼴 파일 안에 실제로 그려져 있는 글자 그림 하나.\
> 예: 「A」라는 문자에 대응하는 그림. 글꼴에 그 그림이 없으면 그 글자만 다른 글꼴에서 가져온다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. `font-family` 에 적은 목록 중 **실제로 어느 글꼴이 쓰였는지 어떻게 아는가.**
2. `font: 16px sans-serif` 한 줄이 **그 앞에 써 둔 무엇을 되돌리는가.**
3. 웹폰트가 늦게 도착하는 동안 **화면에 무엇이 보이고, 그것을 무엇으로 고르는가.**

## 환경 확인 — 이 머신에 무슨 글꼴이 있나

글꼴 주제는 **환경을 안 밝히면 본문 전체가 검증 불가**가 된다. 그래서 이 절이 본문 앞에 온다.

```bash
$ fc-list : family | sort -u | wc -l
312
```

실험에 쓴 이름만 추려 「있나 / 없나」를 갈랐다.

| 이름 | 이 머신에 | 확인 방법 |
|---|---|---|
| `DejaVu Sans` · `DejaVu Serif` · `DejaVu Sans Mono` | **있다** | `fc-list` 에 그 이름으로 등재 |
| `Liberation Sans` · `Liberation Serif` · `Nimbus Sans` · `Nimbus Roman` | **있다** | 〃 |
| `Noto Sans` · `Noto Serif` · `Noto Sans CJK KR` · `Noto Serif CJK KR` | **있다** | 〃 |
| `Ubuntu` · `Ubuntu Sans` (가변 폰트) | **있다** | `fc-list : family file variable` 이 `variable=True` |
| `나눔고딕`(`NanumGothic`) · `나눔명조` | **있다 — 다만 이름이 한글이다** | 아래 ★ |
| `Georgia` · `Verdana` · `Comic Sans MS` | **없다** | `fc-list : family` 에 없다 |
| `Arial` · `Helvetica` · `Times New Roman` | **파일은 없는데 쓰인다** | 아래 ★★ |

★ **`fc-match` 는 판정 도구가 아니다.** 없는 이름을 물어도 **항상 무언가를 돌려준다.**

```text
$ fc-match "Georgia"
NotoSerifCJK-Regular.ttc: "Noto Serif CJK JP" "Regular"

$ fc-match "Comic Sans MS"
NotoSansCJK-Regular.ttc: "Noto Sans CJK JP" "Regular"
```

두 줄 다 **「없다」는 뜻**이다. `fc-match` 는 「이 이름을 지금 쓰면 뭐가 나오나」를 답할 뿐,\
「그 이름이 설치돼 있나」는 답하지 않는다. 설치 여부는 `fc-list : family | grep` 로 본다.

★★ **없는데 쓰이는 이름이 있다 — fontconfig 의 이름 별칭.**

| 선언 | 이 머신에서 그려진 것 | 「Handgloves」 40px 폭 |
|---|---|---|
| `font-family: "Times New Roman"` | **Liberation Serif** | 191.078125px |
| `font-family: "Liberation Serif"` | Liberation Serif | **191.078125px (같다)** |
| `font-family: Arial` | Liberation Sans 계열 | 211.25px |
| `font-family: Georgia` | 아무것도 — **UA 기본 글꼴로 떨어졌다** | 220.40625px |
| `font-family: Zzzznope`(존재하지 않는 이름) | 〃 | **220.40625px (같다)** |

`Times New Roman` 은 **파일이 없는데도 「쓰였다」**. 리눅스의 fontconfig 가 그 이름을
치수 호환 글꼴로 **바꿔치기**하도록 설정돼 있기 때문이다.\
`Georgia` 는 그런 규칙이 없어서 **목록에서 건너뛰어졌다.**

> **치수 호환 대체(metric-compatible substitution)** — 이름은 다르지만 글자 폭이 같게 만들어진 글꼴로 바꿔치는 것.\
> 예: `Times New Roman` 자리에 Liberation Serif 를 넣으면 줄바꿈 위치가 안 바뀐다.

**그래서 「이 이름은 없으니 건너뛴다」는 단정은 OS 마다 다르다.** 재 봐야 안다.

## 동작 방식

### (1) 글꼴 고르기 — 목록은 글자마다 다시 읽힌다

**언제 쓰나** — 한글·라틴·이모지가 섞인 글을 다룰 때. 「한글만 다른 글꼴로 나온다」의 정체가 여기다.

```text
  font-family: BoxOnly, "DejaVu Serif";      (BoxOnly 는 A~Z 만 들어 있는 웹폰트)

  텍스트   A     B     C     ' '    a     b     c
           |     |     |      |     |     |     |
  1순위  BoxOnly에 있나?                  BoxOnly에 있나?
           O     O     O      X     X     X     X
           |     |     |      |     |     |     |
  2순위                    DejaVu Serif에 있나?
                              O     O     O     O
           v     v     v      v     v     v     v
         [■]   [■]   [■]     ' '    a     b     c
```

그림 해설 (한 단계씩):

- 대체는 **선언 단위가 아니라 글자 단위**다. 한 요소 안에서 두 글꼴이 섞인다.
- 실측 — `font: 40px BoxOnly, serif` 에서 `ABC` 는 **120px**(= 40px × 3, 전각 네모 세 개),\
  `abc` 는 **69.328125px**(= serif 의 실제 폭). 같은 요소, 같은 선언인데 폭이 따로 나온다.
- 그래서 한글 페이지에서 `font-family: Roboto, sans-serif` 를 쓰면\
  **라틴은 Roboto, 한글은 그 뒤 sans-serif** 가 된다 — 이게 정상 동작이지 버그가 아니다.

비용 — 글자마다 후보를 훑으므로 목록이 길수록 첫 배치가 느려진다.\
실무에서 목록을 5\~6개 넘게 쓰는 일은 거의 없고, 마지막은 **반드시 generic family** 로 닫는다.

> **generic family** — `serif`·`sans-serif`·`monospace`·`cursive`·`fantasy`·`system-ui` 처럼\
> 특정 파일이 아니라 **범주**를 가리키는 이름. 브라우저가 반드시 하나를 내놓는다.\
> 예: `sans-serif` 는 이 머신에서 `Noto Sans CJK KR` 로 풀렸다.

```html demo
<p class="mix"><span class="up">ABC</span><span class="lo">abc</span></p>
<style>
  @font-face { font-family: BoxOnly;
    src: url(data:font/ttf;base64,AAEAAAAKAIAAAwAgT1MvMmN1Yl4AAACsAAAAYGNtYXAAXQDOAAABDAAAAGBnbHlmA74H2gAAAWwAAAAkaGVhZGMGQ6IAAAGQAAAANmhoZWEHCgNVAAAByAAAACRobXR4B9AAZAAAAewAAAAIbG9jYQAAACQAAAH0AAAADG1heHAABAAGAAACAAAAACBuYW1lCQsgMQAAAiAAAACicG9zdP+fADMAAALEAAAAIAAEA+gBkAAFAAACigJYAAAASwKKAlgAAAFeADIBLAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAABURVNUAEAAQQBaAyD/OAAAAyAAyAAAAAEAAAAAAfQCvAAAACAAAAAAAAEAAwABAAAADAAEAFQAAAAEAAQAAQAAAFr//wAAAEH//wAAAAEABAAAAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABAAEAAQABADIAAAO2ArwAAwAAAQEBAQAyA4QAAPx8AAAAAAK8AAAAAAABAAAAAQAA4Vrz2V8PPPUACwPoAAAAAAAAAAAAAAAAAAAAAAAyAAADtgK8AAAACAACAAEAAAAAAAEAAAMg/zgAAAPoADIAMgO2AAEAAAAAAAAAAAAAAAAAAAACA+gAMgPoADIAAAAAAAAAAAAAACQAAQAAAAIABAABAAAAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAYATgADAAEECQABAA4AAAADAAEECQACAA4ADgADAAEECQADABYAHAADAAEECQAEAA4AMgADAAEECQAFAAYAQAADAAEECQAGAA4ARgBCAG8AeABUAGUAcwB0AFIAZQBnAHUAbABhAHIAQgBvAHgAVABlAHMAdAA7ADEALgAwAEIAbwB4AFQAZQBzAHQAMQAuADAAQgBvAHgAVABlAHMAdAAAAAMAAAAAAAD/nAAyAAAAAQAAAAAAAAAAAAAAAAAAAAA=) format("truetype"); }
  .mix { font: 40px BoxOnly, serif; }
</style>
```

> **보이는 것** — 대문자 `ABC` 는 **까만 네모 세 개**로, 소문자 `abc` 는 **평범한 세리프 글자**로 그려진다.\
> 안에 박은 글꼴에는 `A`\~`Z` 글리프만 들어 있어서, 같은 선언 안에서 **글자마다 다른 글꼴이 쓰인 것**이다.\
> **바꿔 볼 것** — `ABC` 를 `abc` 로 바꾸면 → 네모가 사라지고 전부 세리프로 그려진다 · `font: 40px BoxOnly, serif` 에서 `serif` 를 빼면 → 소문자는 UA 기본 글꼴로 내려간다

*(Chrome 151 headless 실측 — `.up` 폭 **120px**(= 40px × 3, 전각 네모), `.lo` 폭 **69.328125px**. 안에 박은 것은 이 문서를 쓰며 직접 만든 **740바이트짜리 TTF** 이고, 외부 URL 을 쓰지 않았다.)*

### (2) ★ 「정말 그 글꼴로 그려졌나」를 판정하는 법

**언제 쓰나** — 「디자인과 글꼴이 다르다」를 고칠 때. **먼저 세워야 하는 것이 이 판정 방법**이다.

세 창구를 순서대로 열어야 한다. 셋을 안 가르면 증상이 전부 같다.

```text
  ① document.styleSheets[0].cssRules      규칙이 담겼나
        |  @font-face 가 통째로 버려졌을 수 있다(format/tech 가 알 수 없는 값이면)
        v
  ② document.fonts                        그 이름의 face 가 등록·로드됐나
        |  status: unloaded / loading / loaded / error
        v
  ③ 폭 대조                                실제로 그 글꼴로 그려졌나
           <- 시스템 글꼴은 ①②에 아예 안 나온다. ③밖에 없다
```

**①②는 웹폰트에만 쓸 수 있다.** 시스템 글꼴은 `document.fonts` 에 등장하지 않으므로
「Georgia 가 이 머신에 있나」는 ③으로만 답할 수 있다.

★ **`getComputedStyle` 은 이 판정에 쓸 수 없다.** 선언 목록을 그대로 돌려주기 때문이다.

```text
                   선언                          getComputedStyle(el).fontFamily
  Georgia 없음   font-family: Georgia          ->  "Georgia"          <- 그대로
  Georgia 없음   font-family: Georgia, serif   ->  "Georgia, serif"   <- 그대로
  없는 이름      font-family: Zzzznope         ->  "Zzzznope"         <- 그대로
```

★★ **`document.fonts.check()` 도 이 판정에 쓸 수 없다.** 이름만 보고는 늘 `true` 다.

```text
  document.fonts.check("40px Georgia")     -> true    (Georgia 는 이 머신에 없다)
  document.fonts.check("40px Zzzznope")    -> true    (그런 글꼴은 세상에 없다)
  document.fonts.check("40px BoxTest")     -> false   (@font-face 는 있는데 아직 안 받음)
```

`check()` 가 답하는 것은 「**이 지정에 걸리는 `@font-face` 가 전부 로드됐나**」다.\
걸리는 `@font-face` 가 없으면 시스템 대체로 어떻게든 그려지므로 **`true`**.\
**「설치돼 있나」를 묻는 함수가 아니다.**

#### 쓸 수 있는 판정 — 센티넬 대조

```text
  같은 텍스트를 두 번 그린다

    A:  font-family: <후보>, <센티넬>      B:  font-family: <센티넬>
              |                                        |
              +--------------- 폭 비교 ----------------+
                        |
         같다 -> 후보가 안 쓰였다        다르다 -> 후보가 쓰였다
```

**센티넬을 둘 이상 쓴다** — 후보의 치수가 우연히 한 센티넬과 같을 수 있다.

실측(40px `Handgloves`, 센티넬 `monospace`(200px) · `"DejaVu Sans"`(235.4375px)):

| 후보 | `후보, monospace` 폭 | 판정 |
|---|---|---|
| `"DejaVu Serif"` | 239.375 | **쓰였다** |
| `"Times New Roman"` | 191.078125 | **쓰였다**(별칭으로) |
| `Arial` · `Helvetica` | 211.25 | **쓰였다**(별칭으로) |
| `Ubuntu` | 210.375 | **쓰였다** |
| `나눔고딕` | 215.640625 | **쓰였다** |
| `Georgia` · `Verdana` · `"Comic Sans MS"` | **200 (센티넬과 같다)** | **안 쓰였다** |
| `"Nanum Gothic"`(로마자 이름) | **200** | **안 쓰였다** ★ |
| `Zzzznope` | **200** | 안 쓰였다 |

★ **`"Nanum Gothic"` 은 안 먹고 `나눔고딕` 은 먹었다.** 글꼴이 자기 이름을 한글로 등록해 두면
CSS 의 `font-family` 는 **그 이름**을 찾는다. `fc-match "Nanum Gothic"` 은 파일을 찾아 주지만
그것은 fontconfig 의 느슨한 매칭이고, CSS 의 글꼴 매칭은 그보다 엄격하다.

비용 — 이 판정은 **요소를 실제로 레이아웃해야** 나온다. 비교 대상 텍스트는 후보 글꼴 간에
폭 차이가 크게 나는 것(`Handgloves`·`mmmmmmmmlli`)을 쓴다.

```html demo
<p class="probe"><span class="a">Handgloves</span> &larr; Georgia, monospace</p>
<p class="probe"><span class="b">Handgloves</span> &larr; monospace</p>
<style>
  .probe { font: 14px sans-serif; margin: 4px 0; }
  .probe span { font-size: 40px; }
  .a { font-family: Georgia, monospace; }
  .b { font-family: monospace; }
</style>
```

> **보이는 것** — 두 줄의 `Handgloves` 가 **글자 모양도 폭도 완전히 같다.** Georgia 가 이 머신에 없어서 `.a` 가 `monospace` 로 내려갔다는 뜻이다.\
> Georgia 가 깔린 머신에서 열면 위쪽만 세리프 글꼴로 바뀌어 두 줄이 달라 보인다 — **그 차이가 곧 판정**이다.\
> **바꿔 볼 것** — `Georgia` → `"DejaVu Serif"`(이 머신에 있는 이름)로 바꾸면 두 줄의 폭이 달라진다 · 센티넬 `monospace` → `serif` 로 바꿔도 두 줄은 여전히 서로 같다(후보가 없으면 센티넬이 무엇이든 같다)

*(Chrome 151 headless 실측 — 두 `span` 의 `getBoundingClientRect().width` 가 **둘 다 200px** 로 같았다. `"DejaVu Serif", monospace` 로 바꾼 판은 239.375px 대 200px 로 갈렸다.)*

### (3) ★★ `font` 단축 — 한 줄이 열세 속성을 되돌린다

**언제 쓰나** — 「분명히 굵게 해 놨는데 안 굵다」를 진단할 때. **가장 많이 당하는 자리**다.

```text
  .a { font-style: italic;  font-weight: 700;  font-variant-caps: small-caps;
       line-height: 2;      font-size: 30px;   font-family: serif; }

  .b { font: 16px sans-serif; }          <- 크기와 글꼴만 적었다

  ------------------- 실측 계산값 -------------------
                    .a 만              .a + .b
  font-style        italic        ->   normal      되돌아감
  font-weight       700           ->   400         되돌아감
  font-variant-caps small-caps    ->   normal      되돌아감
  line-height       60px          ->   normal      되돌아감
  font-size         30px          ->   16px        내가 적었다
  font-family       serif         ->   sans-serif  내가 적었다
```

그림 해설 (한 단계씩):

- 단축은 **「안 적은 칸을 그냥 두는」 것이 아니라 「안 적은 칸을 초기값으로 쓰는」 것**이다.\
  이것은 `font` 만의 특성이 아니라 **모든 단축 속성의 규칙**이다(`background`·`border` 도 같다).
- 그런데 `font` 는 **자기가 직접 값을 받지 않는 속성까지** 되돌린다. 이게 유별난 점이다.

실측 — `font: 16px serif` 한 줄이 초기값으로 되돌린 속성 **전부**:

| 되돌아간 속성 | 앞에서 정해 둔 값 | `font` 뒤 |
|---|---|---|
| `font-style` | `italic` | `normal` |
| `font-weight` | `700` | `400` |
| `font-variant-caps` | `small-caps` | `normal` |
| `font-stretch` | `75%`(`condensed`) | `100%` |
| `line-height` | `60px` | `normal` |
| `font-feature-settings` | `"liga" 0` | `normal` |
| `font-variation-settings` | `"wght" 700` | `normal` |
| `font-optical-sizing` | `none` | `auto` |
| `font-variant-numeric` | `tabular-nums` | `normal` |
| `font-language-override` | `"TRK"` | `normal` |
| `font-size-adjust` | `0.5` | `none` |
| `font-kerning` | `none` | `auto` |

**앞의 여섯은 `font` 단축이 값을 받을 수 있는 칸**이고(내가 적으면 그 값이 된다),\
**뒤의 여섯은 `font` 가 값을 받을 수도 없는데 되돌리기만 하는 칸**이다.\
`font-variation-settings` 가 여기 있다는 것이 가변 폰트에서 아프다 — (8)에서 다시 본다.

비용 — 리셋 CSS 나 컴포넌트 기본 스타일에 `font:` 가 한 줄 들어 있으면,
그 아래에서 정해 둔 글꼴 관련 설정이 **한꺼번에** 날아간다. 에러는 없다.

```html demo
<p class="a">Italic Bold Small-Caps</p>
<p class="a b">Italic Bold Small-Caps</p>
<style>
  .a { font-style: italic; font-weight: 700; font-variant-caps: small-caps;
       line-height: 2; font-size: 30px; font-family: serif; }
  .b { font: 16px sans-serif; }
</style>
```

> **보이는 것** — 윗줄은 30px 세리프에 **기울고 굵고 작은대문자**이며 줄 간격이 넓다. 아랫줄은 16px 산세리프에 **곧고 보통 굵기이고 작은대문자도 아니며** 줄 간격이 좁다.\
> `.b` 는 크기와 글꼴만 적었는데 기울임·굵기·작은대문자·줄높이가 **함께 사라졌다.**\
> **바꿔 볼 것** — `.b` 를 `font-size: 16px; font-family: sans-serif;` 두 줄로 바꾸면 → 크기·글꼴만 바뀌고 **기울임·굵기·작은대문자가 그대로 남는다**(줄 간격도 배수 `2` 가 살아 있어 32px 이 된다) · `.b` 를 `font: italic bold small-caps 16px/2 sans-serif` 로 바꾸면 → 네 가지가 다시 살아난다

*(Chrome 151 headless 실측 — 아랫줄 계산값: `font-style: normal` · `font-weight: 400` · `font-variant-caps: normal` · `line-height: normal` · `font-size: 16px` · `font-family: sans-serif`. 윗줄은 `italic` / `700` / `small-caps` / `60px` / `30px` / `serif`.)*

### (4) `font` 단축의 문법 — 두 칸은 필수이고 순서가 고정이다

**언제 쓰나** — `font:` 를 썼는데 **한 줄이 통째로 무시될** 때.

```text
  font:  [ style | variant | weight | stretch ]*   size   [ / line-height ]?   family
         \_________ 앞의 넷, 순서 자유, 생략 가능 ___/    \필수/  \____선택____/    \필수/
                                                          ^                        ^
                                         size 와 family 가 없으면 선언째 버려진다
```

실측 — `cssText` 로 **담겼나**를 본 것이다(07번의 「진단 3창」 첫 창).

| 쓴 것 | `cssRules` 의 `cssText` | 결과 |
|---|---|---|
| `font: 16px serif` | `"font: 16px serif;"` | 담겼다 |
| `font: italic small-caps bold condensed 16px/1.4 serif` | `"font: italic small-caps bold condensed 16px / 1.4 serif;"` | 담겼다 |
| `font: bold italic 16px serif` | `"font: italic bold 16px serif;"` | 담겼다 — **앞의 넷은 순서 자유** |
| `font: 150% serif` | `"font: 150% serif;"` | 담겼다(계산값 24px) |
| `font: italic 16px` | **`""`** | **버려졌다** — family 없음 |
| `font: 16px/1.4 serif bold` | **`""`** | **버려졌다** — family 뒤에 다른 값 |
| `font: sans-serif 16px` | **`""`** | **버려졌다** — 순서 뒤집힘 |

- 버려진 세 줄은 **아무 일도 일으키지 않는다.** 앞에서 정해 둔 값이 그대로 남는다 —\
  「단축이 되돌린다」는 (3)의 규칙조차 **안 일어난다.** 통째로 없는 줄이 되기 때문이다.
- 그래서 **「`font:` 를 썼는데 아무것도 안 바뀐다」와 「`font:` 를 썼더니 다 날아갔다」는 정반대 증상**이고,\
  앞엣것은 문법 오류, 뒤엣것은 정상 동작이다.
- `font: caption` 처럼 **시스템 글꼴 키워드**를 쓰면 한 낱말로 끝난다(`caption`·`icon`·`menu`·`message-box`·`small-caption`·`status-bar`).\
  실측 — 이 환경에서 `font: caption` 의 계산값은 `font-family: Arial` · `font-size: 16px` 였다.

> **단축**(shorthand) **속성** — 여러 롱핸드를 한 줄로 쓰는 속성.\
> 예: `font: 16px serif` 는 `font-size: 16px; font-family: serif;` 에 더해 **나머지 칸을 초기값으로** 쓴다.

### (5) `@font-face` — 이름을 새로 등록하는 것

**언제 쓰나** — 머신에 없는 글꼴을 쓰고 싶을 때.

```text
  @font-face {                     이것은 선택자도 아니고 규칙도 아니다.
    font-family: BoxOnly;          <- "BoxOnly" 라는 이름을 명부에 새로 만든다
    src: url(...) format("truetype");
  }                                ^ 그 이름으로 찾으면 이 파일을 쓰라는 등록

  .x { font-family: BoxOnly, serif; }
       ^^^^^^^^^^^^^^^^^^^^^^^^^^  <- 등록된 이름을 '요청'하는 쪽은 평소와 똑같다
```

- `@font-face` 는 **글꼴을 적용하지 않는다.** 이름을 만들 뿐이고, 쓰는 것은 `font-family` 다.
- 그래서 `@font-face` 만 써 놓고 어디서도 그 이름을 안 부르면 **파일을 내려받지도 않는다.**\
  실측 — 어떤 요소도 `BoxTest` 를 안 쓰는 문서에서 `document.fonts.check("40px BoxTest")` 가 **`false`** 였다(아직 `unloaded`).
- **같은 이름으로 여러 번 등록**할 수 있다. 굵기·기울임·문자 범위별로 나눠 등록하는 것이 정석이다.

```text
  @font-face { font-family: X; font-weight: 400; src: url(x-regular.woff2) ... }
  @font-face { font-family: X; font-weight: 700; src: url(x-bold.woff2) ... }
                        ^ 이름은 하나, 파일은 둘
  .t { font-family: X; font-weight: 700; }   ->  x-bold.woff2 가 쓰인다
```

### (6) `src` 목록 — 앞에서부터 「쓸 수 있는 것」을 고른다

**언제 쓰나** — 웹폰트가 안 먹을 때. `src` 한 줄이 어디서 끊겼는지를 본다.

```text
  src: local("DejaVu Serif"),              1) 머신에 있으면 그걸 쓴다(내려받지 않는다)
       url(a.woff2) format("woff2"),       2) 형식을 지원하면 받아 본다
       url(b.ttf)   format("truetype");    3) 앞이 실패하면 다음

  format() 은 '받아 보기 전에 거르는 힌트'다.
      지원하는 형식이면   -> 받아서 실제 내용으로 판단한다(형식이 틀려도 내용이 맞으면 쓴다)
      모르는 형식이면     -> 그 항목을 건너뛴다
      모든 항목이 걸러지면 -> @font-face 규칙 자체가 없던 것이 된다
```

실측 네 가지:

| `src` | 결과(40px `ABCDE`, 폴백 `monospace` = 100px) |
|---|---|
| `local("DejaVu Serif")` | **쓰였다** — 239.375px 로 `"DejaVu Serif"` 직접 지정과 같다 |
| `url(<ttf 데이터>) format("woff2")` | **쓰였다(200px).** 형식을 틀리게 적었는데도 받아서 내용으로 판단했다 |
| `url(<ttf 데이터>) format("zzz-nope")` | **안 쓰였다(100px).** 그리고 `document.fonts` 에 face 가 **아예 없다** |
| `url(<ttf>) format("truetype") tech(zzz-nope)` | **안 쓰였다(100px).** `tech()` 도 같은 식으로 거른다 |
| `url(깨진 데이터) format("truetype"), url(<ttf>) format("truetype")` | **쓰였다(200px)** — 앞이 실패하면 다음으로 넘어간다 |

★ **`format("woff2")` 를 ttf 에 붙였는데도 쓰였다**는 것이 중요하다.\
`format()` 은 **「내가 지원하지 않는 형식이면 받지 말라」는 힌트**이지 내용 검증이 아니다.\
반대로 **모르는 낱말**을 적으면 그 항목이 통째로 걸러지고, 남는 항목이 없으면 `@font-face` 가 사라진다 —\
`document.fonts` 를 열어 봐야 알 수 있고 **콘솔에는 아무 말도 없다.**

> ★ `@supports font-format(woff2)` 로 **형식 지원 여부를 미리 물어보는** 방법은
> [목록의 **41번 주제**](../41-supports-feature-queries/)(`@supports` 기능 질의)가 정본이다. 여기서는 존재만 언급한다.

### (7) `unicode-range` — 한 이름을 문자 범위로 쪼갠다

**언제 쓰나** — 한글 웹폰트처럼 파일이 큰 경우. 쓰이는 범위만 내려받게 한다.

```text
  @font-face { font-family: X; src: url(box.ttf); unicode-range: U+0041-0043; }

  텍스트:   A   B   C   D   E   F   G   H   I   J
  범위 안:  O   O   O   X   X   X   X   X   X   X
  쓰이는 것 [■] [■] [■]  <---------- monospace ---------->

  실측 폭 = 3 x 40px  +  7 x 20px  =  120 + 140 = 260px   (측정값 260px)
```

- 범위 밖 글자는 **그 face 를 아예 안 본다.** 대체 사슬의 다음으로 넘어간다.
- 페이지에 그 범위의 글자가 **하나도 없으면 파일을 내려받지 않는다.** 이게 이 기술자의 값어치다.
- 실측 — `document.fonts` 에서 그 face 의 `unicodeRange` 가 `"U+41-43"` 으로 보였다.

### (8) ★★ `font-display` — FOIT 와 FOUT 중 무엇을 고를 것인가

**언제 쓰나** — 웹폰트를 쓰는 모든 페이지에서. 안 적으면 `auto` 가 되고, 그건 선택을 안 한 것이다.

폰트가 도착하기 전의 시간이 두 토막으로 나뉜다.

```text
  요청                                                                시간 ->
   |----- 차단 기간 -----|------------ 교체 기간 ------------|--- 실패 기간 ---
   |  글자를 안 그린다   |  폴백으로 그려 두고, 오면 바꾼다   |  와도 안 바꾼다
   |      (FOIT)        |              (FOUT)               |

   block     차단 3초   + 교체 무한
   swap      차단 0     + 교체 무한
   fallback  차단 0.1초 + 교체 3초       <- 늦으면 영영 폴백
   optional  차단 0.1초 + 교체 0          <- 거의 항상 폴백. 대신 레이아웃이 안 흔들린다
   auto      브라우저 재량
```

> **FOIT(Flash of Invisible Text)** — 폰트를 기다리는 동안 **글자를 아예 안 그리는** 것.\
> 예: 제목 자리가 빈 채로 있다가 툭 나타난다. 읽을 게 없으니 체감이 느리다.

> **FOUT(Flash of Unstyled Text)** — 폴백으로 **먼저 그려 놓고** 나중에 바꿔 끼우는 것.\
> 예: 고딕으로 읽히다가 갑자기 명조로 바뀌면서 줄바꿈 위치가 흔들린다.

**★ 잴 수 있었다.** `data:` URI 는 즉시 도착해서 못 재므로, **응답을 일부러 늦추는 로컬 HTTP 서버**를 세우고
다섯 값을 한 페이지에 나란히 띄운 뒤 CDP 로 시각별 폭과 스크린샷을 받았다.

**실측 ① — 폰트가 1.5초 뒤에 도착할 때** (폭: 폴백 200px → 웹폰트 400px)

```text
          t=0     0.9s    1.7s    2.6s    4.6s    7.0s
  auto     200     200     400     400     400     400
  block    200     200     400     400     400     400
  swap     200     200     400     400     400     400
  fallback 200     200     400     400     400     400
  optional 200     200     200     200     200     200   <- 영영 안 바꾼다
```

**실측 ② — 폰트가 4초 뒤에 도착할 때**

```text
          t=0     1.7s    3.3s    3.8s    4.6s    7.0s
  auto     200     200     200     200     400     400
  block    200     200     200     200     400     400
  swap     200     200     200     200     400     400
  fallback 200     200     200     200     200     200   <- 교체 기간 3초를 넘겨 포기
  optional 200     200     200     200     200     200
```

**실측 ③ — 「보이나 안 보이나」는 스크린샷으로 갈랐다** (폰트는 4초 뒤 도착, 어두운 픽셀 수로 판정)

```text
  시각      auto      block     swap      fallback  optional
  0.2s     안 보임    안 보임    보임       보임       보임
  0.8s     안 보임    안 보임    보임       보임       보임
  1.9s     안 보임    안 보임    보임       보임       보임
  2.0s      보임     안 보임    보임       보임       보임      <- auto 의 차단이 여기서 끝났다
  2.9s      보임     안 보임    보임       보임       보임
  3.2s      보임      보임      보임       보임       보임      <- block 의 차단 3초
```

그림 해설 (한 줄씩):

- `block` 의 차단 기간은 **3.0초**로 관찰됐다 — 명세가 권하는 값과 같다.
- `auto` 는 **약 2.0초**에 폴백을 보여 줬다. **명세는 `auto` 를 UA 재량으로 둔다** — 이 값은 관찰이지 보장이 아니다.\
  적어도 **`auto` 와 `block` 이 같지 않다**는 것은 이 환경에서 두 번 반복해 같게 나왔다.
- `swap`·`fallback`·`optional` 은 0.2초 시점에 이미 **폴백 글자가 보였다.**
- **`optional` 은 도착해도 안 바꾼다.** 그래서 「레이아웃이 절대 안 흔들린다」가 이 값의 값어치다.

비용 — 고르는 것은 **무엇을 포기하느냐**다.

| 값 | 포기하는 것 | 쓰는 자리 |
|---|---|---|
| `block` | 초반 가독성(빈 화면) | 아이콘 폰트처럼 **폴백이 의미가 없는** 것 |
| `swap` | 레이아웃 안정(글자가 바뀌며 밀림) | 본문 — 읽히는 것이 먼저다 |
| `fallback` | 느린 회선에서 웹폰트 자체 | 본문인데 브랜드 글꼴이 필수가 아닐 때 |
| `optional` | 웹폰트를 거의 늘 포기 | **CLS 를 0으로 두고 싶을 때** |

> **CLS(Cumulative Layout Shift)** — 페이지가 뜨는 동안 요소가 얼마나 밀렸는지를 합산한 지표.\
> 예: 글꼴이 바뀌며 본문이 한 줄 늘어나면 그 아래 전부가 밀리고, 그만큼 점수가 나빠진다.

### (9) 가변 폰트 — 한 파일이 굵기를 연속으로 낸다

**언제 쓰나** — 굵기를 여러 단계 쓰는 디자인에서. 파일 수와 용량이 줄어든다.

```text
  정적 폰트                              가변 폰트
  +----------------------------+        +----------------------------+
  | X-Thin.woff2   100         |        | X.woff2                    |
  | X-Light.woff2  300         |        |   wght 축: 100 ---- 900    |
  | X-Regular      400         |        |   wdth 축:  75 ---- 100    |
  | X-Medium       500         |        |                            |
  | X-Bold         700         |        | 450 · 437 같은 중간값도     |
  +----------------------------+        | 그 자리에서 만들어 낸다     |
   그 사이 값은 없다 -> 가장 가까운 것    +----------------------------+
```

> **축(axis)** — 가변 폰트가 연속으로 바꿀 수 있는 성질 하나. 네 글자 태그로 부른다.\
> 예: `wght`(굵기) · `wdth`(너비) · `slnt`(기울기) · `opsz`(광학 크기).

★ **`font-weight: 450` 이 되나 — 던져서 확인했다. 답이 「경우에 따라 다르다」였다.**

**실측 ① — 웹폰트로 불러온 가변 폰트**(같은 파일을 `@font-face` + `data:` URI 로)

```text
  font-weight   400      437      450      500
  40px "Weight" 폭
                129.77   130.59   130.84   132.00     <- 450 이 400 과 500 사이에 있다

  font-variation-settings: "wght" 450   ->  130.84    <- font-weight: 450 과 같은 값
  font-variation-settings: "wght" 800   ->  136.61
```

**실측 ② — 똑같은 파일을 시스템 글꼴(`font-family: Ubuntu`)로 쓴 경우**

```text
  font-weight   100      300      400      450      500      700
                125.61   128.38   129.77   129.77   132.00   134.92
                                           ^^^^^^ 400 과 똑같다 (450 이 스냅됐다)

  font-variation-settings: "wght" 450  ->  129.77   <- 아무 효과 없음
  font-variation-settings: "wght" 900  ->  129.77   <- 아무 효과 없음
  font-stretch: 75%                    ->  104.09   <- wdth 축은 먹었다
```

**같은 파일인데 결과가 다르다.** 이 머신의 fontconfig 는 가변 폰트를
`Thin`·`Light`·`Regular`·`Medium`… 같은 **이름 붙은 인스턴스** 여러 개로 노출하고,
Chrome 은 시스템 글꼴을 그중에서 고르기 때문에 **연속 축이 끊긴다.**

> **이름 붙은 인스턴스(named instance)** — 가변 폰트가 「이 좌표를 Regular 라 부른다」고 미리 정해 둔 지점.\
> 예: `Ubuntu` 한 파일이 fontconfig 에는 `style=Thin`·`style=Light`·`style=Medium` … 으로 여러 줄 나온다.

★ 그래서 **「가변 폰트는 `font-weight` 가 연속이다」는 웹폰트로 불러올 때의 이야기**다.\
시스템에 깔린 가변 폰트에 기대면 안 된다 — 이것은 **OS·fontconfig 의 구현 세부사항**이다.

★ **`font-variation-settings` 보다 상위 속성을 써라.**

| 축 | 상위 속성 |
|---|---|
| `wght` | `font-weight` |
| `wdth` | `font-stretch` |
| `slnt` · `ital` | `font-style: oblique <각도>` · `italic` |
| `opsz` | `font-optical-sizing` |

이유는 셋이다 — ① `font-variation-settings` 는 **상속될 때 통째로 덮인다**(축 하나만 바꿔도 나머지 축이 초기화된다) ·
② `font` 단축이 **되돌려 버린다**((3)의 표) · ③ 상위 속성은 그 글꼴에 축이 없을 때 **합성으로라도 흉내**를 낸다.
`font-feature-settings` 대 `font-variant-*` 도 **똑같은 이유로 똑같은 권고**다.

## 문법 — 형태와 어디서 헷갈리나

CSS 는 문법 표면이 단순하므로 이 절은 「형태」가 아니라 「**어디서 헷갈리나**」로 읽는다.

### 이름에 따옴표를 언제 붙이나

```css
font-family: "Times New Roman", Times, serif;   /* 공백이 있으면 따옴표가 안전하다 */
font-family: Times New Roman, serif;            /* 문법상 유효하다 — 식별자 나열 */
font-family: "serif";                           /* ★ 틀렸다 — 따옴표를 쓰면 generic 이 아니라 */
                                                /*    "serif" 라는 이름의 글꼴을 찾는다 */
font-family: 나눔고딕, sans-serif;               /* 한글 이름도 식별자로 쓸 수 있다 */
```

- **generic family 에는 절대 따옴표를 붙이지 않는다.** 붙이는 순간 평범한 이름이 된다.
- 숫자로 시작하거나 예약어와 겹치는 이름은 따옴표가 필요하다.

### `@font-face` 기술자와 같은 이름의 속성은 다른 물건이다

```css
@font-face {
  font-family: X;          /* 기술자 — "이 파일을 X 라 부른다" */
  font-weight: 100 900;    /* 기술자 — "이 파일이 덮는 굵기 범위" (범위를 쓸 수 있다) */
  font-display: swap;      /* 기술자 — 속성으로는 존재하지 않는다 */
  src: url(...) format("woff2");
}
.t { font-weight: 450; }   /* 속성 — "이 요소를 450 으로 그려라" (범위를 못 쓴다) */
```

실측 — `@font-face { font-weight: 100 900 }` 로 등록한 face 를 `font-weight: 250` 으로 쓰면 그 face 가 선택됐다.

### 금지 사례 — 버려지는 줄

```css
font: sans-serif 16px;          /* 순서 뒤집힘 — 선언째 버려진다 */
font: italic 16px;              /* family 없음 — 버려진다 */
font: 16px/1.4 serif bold;      /* family 뒤에 다른 값 — 버려진다 */
font-display: swap;             /* @font-face 밖에서는 아무 의미 없다 */
font-family: "sans-serif";      /* 문법은 맞지만 generic 이 아니게 된다 */
```

## 어디서 틀리나

### 1. ★ `getComputedStyle` 로 「글꼴이 먹었나」를 확인한다

**가장 흔한 사고다.** 선언 목록이 그대로 돌아오므로 **언제나 「먹은 것처럼」 보인다.**\
`--dump-dom` 으로 확인하는 자동화 스크립트도 같은 함정에 빠진다.\
고치는 법은 (2)의 센티넬 대조다.

### 2. ★ 없는 글꼴을 쓴 실험을 성공으로 적는다

1번의 결과다. 화면에 글자가 보이니 맞아 보이고, 스크린샷을 찍어도 정상으로 보인다.\
**「대체 글꼴로 그려진 화면」과 「의도한 글꼴로 그려진 화면」은 둘 다 멀쩡해 보인다.**

### 3. ★★ `font` 단축이 뒤에 와서 앞의 설정을 지운다

```css
.btn      { font-weight: 700; }
.btn.dark { font: 16px system-ui; }   /* 굵기가 400 으로 돌아간다 */
```

캐스케이드에서 **뒤가 이기는 것이 아니라 단축이 칸을 채우는 것**이다.\
`.btn.dark` 가 더 셀 필요도 없다 — `font` 는 `font-weight` 칸에 초기값을 직접 써 넣는다.\
진단은 「`font-weight` 를 누가 이겼나」가 아니라 「**`font:` 를 쓴 규칙이 어디 있나**」로 찾아야 한다.

### 4. `font-family` 목록의 마지막을 generic 으로 안 닫는다

```css
font-family: "Pretendard", "Apple SD Gothic Neo";   /* 둘 다 없으면 UA 기본 글꼴 */
```

- 실측 — 후보가 전부 없으면 **UA 기본 글꼴**로 떨어졌다(이 환경에서는 `Noto Sans CJK KR`, 폭 220.40625px).
- 그것은 `serif`(227.96875px) 도 `sans-serif` 와 우연히 같은 값일 뿐 **내가 고른 값이 아니다.**

### 5. 한글 페이지에서 라틴 글꼴만 지정한다

`font-family: Inter` 만 쓰면 **한글은 전부 대체 사슬 끝으로 내려간다.**\
(1)의 글자 단위 대체가 정상 동작하는 것이지 버그가 아니다.\
고치는 법은 한글 글꼴을 목록에 **명시적으로** 넣는 것.

### 6. `@font-face` 를 써 놓고 `font-family` 로 안 부른다

이름만 만들어 놓은 상태다. 파일도 안 받는다. `document.fonts` 에서 `unloaded` 로 보인다.

### 7. `src` 의 `format()` 에 오타를 낸다

`format("wofff2")` 하나로 **`@font-face` 규칙 전체가 사라진다.** 콘솔에 아무 말도 없다.\
`document.fonts.size` 가 기대보다 작으면 이것을 의심한다.

### 8. `font-display` 를 안 적는다

`auto` 가 되고, 실측에서 `auto` 는 **약 2초 동안 글자를 안 그렸다.**\
본문 글꼴이라면 거의 언제나 `swap` 이나 `optional` 중 하나를 골라야 한다.

### 9. `font-variation-settings` 로만 굵기를 준다

`font` 단축 한 줄에 되돌아가고, 상속 시 다른 축까지 같이 날아간다.\
`font-weight` 를 쓰고, 축이 특이할 때만(`GRAD`·`XOPQ` 같은 사설 축) `font-variation-settings` 를 쓴다.

### 10. 시스템에 깔린 가변 폰트에 연속 굵기를 기대한다

(9)의 실측 — 이 머신에서 `font-family: Ubuntu; font-weight: 450` 은 400 과 **완전히 같은 폭**이었다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `font-family` 가 **이름 목록**이고 앞에서부터 고른다는 것 | **명세**(css-fonts-4 「Font Matching Algorithm」) |
| 대체가 **글자 단위**로 일어난다는 것 | **명세**(같은 절의 system font fallback) |
| `getComputedStyle` 이 **선언 목록**을 돌려준다는 것 | **명세**(`font-family` 의 계산값은 지정값과 같다) |
| `document.fonts.check()` 가 **로드 여부**를 답한다는 것 | **명세**(css-font-loading-3) |
| `font` 단축이 롱핸드를 **초기값으로 되돌린다**는 것 | **명세**(단축의 일반 규칙 + css-fonts-4 가 되돌릴 속성 목록을 명시) |
| `font` 가 `font-size` 와 `font-family` 를 **요구**하고 순서가 고정인 것 | **명세**(`font` 의 문법 정의) |
| `src` 목록을 앞에서부터 고르고 `format()`/`tech()` 로 거르는 것 | **명세**(css-fonts-4 「src」) |
| `unicode-range` 가 문자 범위로 face 를 고르는 것 | **명세** |
| `font-display` 의 **차단/교체/실패 기간이라는 구조** | **명세**(css-fonts-4 「font-display」) |
| `block` 의 차단 기간이 **3초**라는 것 | **명세가 권하는 값**(3초 이하) + 이 환경의 관찰이 3.0초 |
| `fallback` 의 교체 기간이 **3초**라는 것 | 〃 — 실측 ②가 4초 도착에서 포기했다 |
| **`auto` 가 약 2.0초**에 폴백을 보여 준 것 | **관찰.** 명세는 `auto` 를 UA 재량으로 둔다 |
| **`auto` 와 `block` 이 다르다**는 것 | **관찰**(Chrome 151, 두 번 반복해 같음). 다른 브라우저는 모른다 |
| 가변 폰트에서 `font-weight` 가 **연속값**이 되는 것 | **명세**(css-fonts-4 가 가변 폰트 축 연결을 규정) |
| **시스템 가변 폰트에서 450 이 400 으로 스냅된 것** | **이 환경의 구현 세부.** fontconfig 가 이름 붙은 인스턴스로 노출한 결과 |
| `Times New Roman` 이 **Liberation Serif** 로 그려진 것 | **이 리눅스 설정의 fontconfig 규칙.** 명세도 CSS 도 아니다 |
| `"Nanum Gothic"` 은 안 먹고 `나눔고딕` 은 먹은 것 | **관찰.** 글꼴이 자기 이름을 무엇으로 등록했나에 달렸다 |
| 이 문서의 **모든 px 수치** | **이 머신의 값.** 설치 글꼴이 다르면 전부 달라진다 |
| `format("woff2")` 를 ttf 에 붙여도 쓰인 것 | **관찰**(Chrome 151). 명세는 `format()` 을 **힌트**로 규정한다 |

**★ 이 주제에서 명세와 환경이 갈리는 자리는 「어떤 이름이 무엇으로 풀리나」 하나다.**\
규칙(고르는 순서·단축의 리셋·기간 구조)은 명세로 예측할 수 있지만,
**결과(어느 파일이 쓰였나·폭이 몇 px 인가)는 반드시 그 머신에서 재 봐야 한다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 이렇게 |
|---|---|
| 본문 글꼴을 브랜드 글꼴로 | `@font-face` + `font-display: swap` + `unicode-range` 로 쪼개기 |
| 레이아웃이 절대 안 흔들려야 | `font-display: optional` — 웹폰트를 포기할 각오를 하는 값이다 |
| 아이콘 폰트 | `font-display: block` — 폴백 글자가 의미 없는 유일한 경우 |
| 굵기를 3단계 이상 쓴다 | 가변 폰트 하나 + `font-weight` |
| 시스템 글꼴로 충분하다 | `font-family: system-ui, sans-serif` — 내려받지 않는 것이 가장 빠르다 |
| 글꼴을 한 줄로 몰아 쓰고 싶다 | `font:` 단축. 단 **그 줄이 무엇을 되돌리는지 알고** 쓴다 |
| 한 속성만 바꾸고 싶다 | **롱핸드를 쓴다.** `font:` 를 쓰면 안 적은 칸이 다 날아간다 |
| 축을 하나만 미세 조정 | `font-weight`·`font-stretch` 먼저. 사설 축일 때만 `font-variation-settings` |

## 핵심 문장

- **`font-family` 는 요청이고, 무엇이 응답했는지는 어디에도 기록되지 않는다.** `getComputedStyle` 도 `document.fonts.check()` 도 답하지 않는다.
- 그래서 **「그 글꼴로 그려졌나」는 폭을 재서 센티넬과 대조**하는 수밖에 없고, 센티넬은 둘 이상 쓴다.
- **대체는 글자 단위**다 — 한 선언 안에서 라틴과 한글이 다른 글꼴로 그려지는 것이 정상이다.
- **`font:` 한 줄은 열두 개가 넘는 속성을 초기값으로 되돌린다.** 그중 절반은 `font` 가 값을 받지도 못하는 칸이다.
- `font` 는 **`font-size` 와 `font-family` 가 필수**이고 순서가 고정이다. 어기면 **선언째 사라져서 아무 일도 안 일어난다.**
- **`font-display` 는 FOIT 와 FOUT 중 무엇을 감수할지 고르는 스위치**다. 안 적으면 `auto` 가 되고, 실측에서 `auto` 는 2초간 글자를 감췄다.
- **`optional` 은 「거의 항상 폴백」과 「레이아웃 무진동」을 맞바꾸는 값**이다 — 실측에서 1.5초 도착에도 끝내 안 바꿨다.
- 가변 폰트의 연속 굵기는 **웹폰트로 불러올 때의 이야기**다. 시스템에 깔린 같은 파일은 이 환경에서 400 으로 스냅됐다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 50번)
- [`../51-text-wrapping-and-decoration/2-summary.md`](../51-text-wrapping-and-decoration/2-summary.md) — **이 주제의 다음 칸.**\
  **어느 글꼴로 그리나(50) 가 정해져야 어디서 줄이 바뀌나(51) 가 정해진다.** 그쪽은 **줄 수**가 결론이다.
- [`../03-inheritance-and-global-keywords/2-summary.md`](../03-inheritance-and-global-keywords/2-summary.md) — **상속의 정본.**\
  글꼴 속성은 **상속되는 속성의 대표**다. 「무엇이 상속되나 · `inherit`/`initial`/`revert`/`unset`」은 거기, 여기는 「그래서 글꼴 목록을 어디에 한 번 쓰나」까지.
- [`../04-value-processing-stages/2-summary.md`](../04-value-processing-stages/2-summary.md) — **값 처리 단계의 정본.**\
  `em` 이 언제 px 이 되는지는 거기다. **`font-size` 가 그 사슬의 뿌리**이고, 여기는 「`font` 단축이 그 뿌리를 어떻게 건드리나」까지.
- [`../07-syntax-and-error-recovery/2-summary.md`](../07-syntax-and-error-recovery/2-summary.md) — **오류 복구의 정본.**\
  「무효한 선언이 조용히 버려진다」는 거기, 여기는 「`font:` 와 `src` 에서 그 일이 어떤 모양으로 나타나나」까지.
- [목록의 **19번 주제**](../19-inline-formatting-context/)(인라인 서식 문맥·행 상자·`line-height`) — **`line-height` 의 정본.**\
  여기서는 `font` 단축이 `line-height` 를 **되돌린다**는 것까지만 다루고, 그 값이 행 상자를 어떻게 만드는지는 그쪽이다.
- [목록의 **41번 주제**](../41-supports-feature-queries/)(`@supports` 기능 질의) — `@supports font-format()`·`font-tech()` 로 **형식 지원을 미리 묻는** 방법.
- [목록의 **33번 주제**](../33-length-units/)(길이 단위) — `em`·`ch`·`ex` 가 글꼴에 달려 있다는 것.
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **글리프(glyph)** — 글꼴 파일 안에 그려져 있는 글자 그림 하나. 문자(character)와 1:1이 아니다.
- **대체(fallback)** — 앞 후보로 못 그릴 때 다음 후보로 내려가는 것. **글자 단위**로 일어난다.
- **generic family** — `serif`·`sans-serif`·`monospace`·`cursive`·`fantasy`·`system-ui`. 따옴표를 붙이면 안 된다.
- **치수 호환 대체** — 이름 대신 글자 폭이 같은 다른 글꼴을 쓰는 OS 설정. `Times New Roman` → Liberation Serif.
- **센티넬 대조** — 후보와 함께 쓴 센티넬의 폭이 같은지로 「후보가 쓰였나」를 판정하는 방법.
- **`@font-face`** — 이름을 새로 등록하는 at-rule. 적용이 아니라 **등록**이다.
- **기술자(descriptor)** — `@font-face` 안에서만 쓰는 항목(`src`·`unicode-range`·`font-display`). 같은 이름의 속성과 다른 물건이다.
- **`format()` / `tech()`** — `src` 항목을 받기 전에 거르는 힌트. 모르는 낱말이면 그 항목이 사라진다.
- **`local()`** — 머신에 설치된 글꼴을 `@font-face` 의 소스로 쓰는 것. 내려받지 않는다.
- **`unicode-range`** — 그 face 가 담당할 문자 범위. 범위 밖 글자는 이 face 를 보지 않는다.
- **FOIT** — 폰트를 기다리며 글자를 안 그리는 것. 차단 기간의 증상.
- **FOUT** — 폴백으로 먼저 그리고 나중에 바꿔 끼우는 것. 교체 기간의 증상.
- **차단/교체/실패 기간** — `font-display` 가 나누는 세 구간. 값마다 앞 둘의 길이가 다르다.
- **가변 폰트(variable font)** — 한 파일이 축을 따라 연속으로 모양을 바꾸는 글꼴.
- **축(axis)** — `wght`·`wdth`·`slnt`·`opsz` 같은 네 글자 태그.
- **이름 붙은 인스턴스** — 가변 폰트가 미리 이름을 붙여 둔 축 좌표(`Regular`·`Medium`).
- **합성(synthesis)** — 굵은 글꼴이 없을 때 브라우저가 글자를 두껍게 그려 흉내 내는 것. `font-synthesis` 로 끈다.

## 더 들어가면

- **`size-adjust`·`ascent-override`·`descent-override`·`line-gap-override`** — `@font-face` 기술자로 **폴백 글꼴의 치수를 웹폰트에 맞춰 보정**한다. FOUT 때 레이아웃이 튀는 것을 줄이는 정석이고, `optional` 을 안 쓰고도 CLS 를 줄이는 길이다. 이 문서에서는 실행하지 않았다.
- **`font-synthesis`** — 굵은/기울인 face 가 없을 때 브라우저가 흉내 내는 것을 끄는 속성(`font-synthesis: none`). Baseline widely(2022-01-06 → 2024-07-06).
- **`font-palette`** — 컬러 폰트의 색 조합을 고른다. Baseline widely(2022-11-15 → 2025-05-15).
- **`@font-feature-values`** — `font-variant-alternates` 에서 쓸 이름을 글꼴별로 정의한다.
- **Local Font Access API** — 설치된 글꼴을 JS 로 나열하는 API. 권한이 필요하고 Baseline 이 아니다. 이 문서의 「환경 확인」을 브라우저 안에서 하는 방법이 될 수 있다.
