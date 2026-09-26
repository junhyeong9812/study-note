# web-api/08 — `getComputedStyle`: 스크립트에서 계산값을 읽는다는 것 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [CSSOM](https://drafts.csswg.org/cssom/#dom-window-getcomputedstyle) 의 「`getComputedStyle()`」·「resolved values」 절로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★ **「CSS 가 무엇을 계산하나」는 이 문서가 아니다** — [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)가 정본이다. 여기는 **스크립트가 그것을 어떻게 읽나**뿐이다.

**★ 이 주제에는 흔들리는 칸이 있다** — 마지막 두 답에서 **읽기 비용을 재기 때문**이다.

| 안 흔들리는 칸 | 흔들리는 칸 |
|---|---|
| 계산값 문자열 · `item(i)` 목록 · 예외 이름 · 객체 동일성 · `display:none` 과 트리 밖의 대답 | `performance.now()` 의 **모든 수치** |
| 시간 표의 **자릿수와 순위** — 세 판 모두 같았다 | 같은 자릿수 안의 대소 |
| — | **`length` 의 값**(475·476 — 판과 그 문서의 커스텀 속성 수에 달린다) |
| — | `cs.font` 의 글꼴 이름 · flex 실측의 `307.19` — **이 머신의 글꼴 치수** |

측정 조건 — **한 파일 안에서 9판**을 돌려 **중앙값**을 쓰고 최소·최대를 함께 실었다. 교차·묶음 조건은 행 **400**, 속성별 조건은 반복 **2000** 이다. **결론으로 쓰는 것은 자릿수와 순위뿐**이다.\
★ **`performance.now()` 의 분해능은 100마이크로초**다([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) 실측). 표에서 **가장 작은 칸이 `0.10`** 이면 그것은 **분해능 한 칸**이다 — 「공짜」가 아니라 「**이 도구로는 못 잰다**」로 읽는다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 값이 온 곳이 넷일 때 — `el.style` 은 그중 하나만 본다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-two.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
값이 온 곳이 넷인데 el.style 은 그중 하나만 본다
값이 어디서 왔나                  el.style                        getComputedStyle
인라인 style 의 color             "red"                           "rgb(255, 0, 0)"
스타일시트의 font-size            ""                              "21px"
부모에게서 상속된 color           ""                              "rgb(0, 128, 0)"
아무도 안 준 display              ""                              "block"
시트의 !important 가 이긴 color   "red"                           "rgb(0, 0, 255)"
커스텀 속성 --tone                ""                              "진하게"
(exit 0)
```

**왜 그런가**

- **인라인만 왼쪽 칸에 보인다.** 시트가 준 `font-size`, 부모에게서 상속된 `color`, 아무도 안 준 `display` 는 전부 `el.style` 에 없다.
- ★ **가장 위험한 줄은 다섯째**다 — 인라인에 `color: red` 를 썼는데 시트의 `!important` 가 이겨서 **계산값은 파랑**이다. **`el.style` 만 보면 「내가 빨강을 썼으니 빨강이겠지」로 확신하게 된다.** 값이 **있어서** 더 위험하다.
- **인라인에 `red` 라고 썼어도 계산값은 `"rgb(255, 0, 0)"`** 이다. 계산값은 **정규화된 형식**으로 온다 — 내가 쓴 글자가 아니다.
- **커스텀 속성 `--tone` 도 오른쪽 칸에만** 보인다. 상속돼 왔기 때문이다. 다만 **커스텀 속성의 값 처리는 보통 속성과 다르다**(정본: [CSS 36번 주제](../../languages/css/syntax/36-custom-properties/2-summary.md)).

### 2. 돌려받은 객체를 만져 보면 — 타입이 같은데 읽기 전용이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-two.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,18p'
돌려받은 객체의 성질 — el.style 과 무엇이 다른가
무슨 객체인가                     CSSStyleDeclaration             CSSStyleDeclaration
선언 개수 length                  computed = 475                  inline = 1
cssText                           ""                              (inline 은 "color: red;")
getPropertyValue 와 카멜          "16px"  "16px"
cs.color = 'lime'                 예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
cs.setProperty('color','lime')    예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
cs.removeProperty('color')        예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
cs.cssText = 'color: lime'        예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
(exit 0)
```

**왜 그런가**

- **타입은 `el.style` 과 똑같이 `CSSStyleDeclaration`** 이다. **`length` 는 475 대 1**, **`cssText` 는 빈 문자열**(인라인 쪽은 `"color: red;"`)이다.
- **네 창구 모두 `NoModificationAllowedError`** 를 던지고 **되읽은 값이 안 바뀐다.** 프로퍼티 대입·`setProperty`·`removeProperty`·`cssText` 대입 전부다.
- ★ **[07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 `el.style` 과 정반대**다. 그쪽은 무효한 값을 **조용히 버렸고**(예외 0줄), 여기는 **읽기 전용 위반을 예외로** 알린다. **이 주제에서 예외가 나는 유일한 자리**다.
- **`cssText` 가 비었다고 「값이 없다」로 읽으면 틀리는 이유** — `length` 가 475 다. 값은 전부 있는데 **통째로 직렬화해 주지 않을 뿐**이다. 명세가 계산값의 `cssText` 를 빈 문자열로 정했다.

### 3. 읽는 문법 셋 — 하나만 오타를 잡아 준다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-read.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,10p'
읽는 문법이 셋이다 — 같은 선언을 세 창구로 물었다
무엇으로 물었나                   돌려받은 것                   판정
cs.fontSize (카멜)                "20px"
cs.getPropertyValue('font-size')  "20px"                        카멜과 같은가 true
cs['font-size'] (케밥 대괄호)     "20px"                        ★ 이것도 된다
cs.getPropertyValue('fontSize')   ""                            ★ 카멜로 물으면 빈 문자열
cs.fontsize (전부 소문자)         undefined                     프로퍼티가 없다
cs.getPropertyValue('zzz')        ""
cs.getPropertyValue('--tone')     "진하게"                      커스텀 속성은 이 창구로만
cs['--tone']                      undefined                     ★ 커스텀 속성은 대괄호로 안 읽힌다
(exit 0)
```

**왜 그런가**

| 창구 | 결과 | 못 찾으면 |
|---|---|---|
| `cs.fontSize`(카멜) | `"20px"` | `undefined` |
| `cs['font-size']`(케밥 대괄호) | `"20px"` | `undefined` |
| `cs.getPropertyValue('font-size')` | `"20px"` | **`""`** |
| `cs.getPropertyValue('fontSize')` | **`""`** | — |
| `cs.fontsize` | `undefined` | — |
| `cs.getPropertyValue('--tone')` | `"진하게"` | — |
| `cs['--tone']` | `undefined` | — |

- ★ **대괄호에 케밥을 넣어도 된다.** 카멜과 케밥이 **둘 다 프로퍼티로 정의**돼 있다.
- **오타를 잡아 주는 창구는 프로퍼티 접근**이다 — `undefined` 가 나온다. **`getPropertyValue` 는 조용하다** — `'fontSize'`(카멜)도, `'zzz'`(없는 속성)도 **똑같이 빈 문자열**이라 **구분이 안 된다.**
- **커스텀 속성은 `getPropertyValue` 로만** 읽힌다. **카멜 매핑은 명세가 아는 속성에만** 만들어지기 때문이다 — `--tone` 같은 이름은 아무도 미리 모른다.
- **목록에 단축 이름은 없다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-read.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '22,28p'
목록으로 읽으면 — el.style 과 크기가 다르다
cs.length                         476                           kid.style.length = 0
cs.item(0) · item(1) · item(2)    "accent-color" "align-content" "align-items"
목록에 단축 이름이 있나           false                         'margin-top' 은 true
목록에 --tone 이 있나             true
cs.cssText                        ""                            (인라인은 "")
window.getComputedStyle 인가      true                          cs.parentRule = null
(exit 0)
```

- `'margin'` 은 **없고** `'margin-top'` 은 **있다.** **담겨 있는 것은 낱개뿐**이고, `cs.margin` 을 물으면 **읽을 때 되접어** 준다(A8 은 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 같은 규칙과 짝이다).
- ★ **커스텀 속성은 목록에 있다.** 그래서 **문서마다 `length` 가 다르다** — 이 실험 476, 커스텀 속성이 없는 A2 의 실험 475. **상수로 외우지 마라.**

### 4. 상자가 없는 요소에 물으면 — `display: none` 은 대답하고 트리 밖은 침묵한다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-none.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
display:none 인 요소도 대답은 한다 — 대신 레이아웃이 필요한 칸만 원문으로 남는다
프로퍼티                    보이는 요소                   display:none 인 요소
color                       "rgb(0, 128, 0)"              "rgb(0, 128, 0)"
fontSize                    "20px"                        "20px"
paddingTop                  "60px"                        "60px"
width                       "200px"                       "50%"
transform                   "matrix(1, 0, 0, 1, 160, 0)"  "none"
display                     "block"                       "none"
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-none.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,16p'
트리에 없는 요소에 물으면 — 여기가 이 갈래 고유의 자리다
무엇에 물었나               color                         width · display
createElement 만 한 것      ""                            "" · ""
  getComputedStyle().length 0                             cssText = ""
template.content 안의 것    ""                            "" · ""
  그 노드의 ownerDocument   false                         isConnected = false
뗀 뒤 같은 노드             "rgb(0, 128, 0)" -> ""        "" · ""
(exit 0)
```

**왜 그런가**

```text
   무엇                           width          length   판정
   보이는 요소                    "200px"        전부     사용값이 나온다
   display: none                  "50%"          전부     ★ 계산값으로 떨어진다
                                  transform 은 "none"
   createElement 만 한 것         ""             0        ★ 통째로 침묵
   template.content 안의 것       ""             0        ★ 통째로 침묵
   붙어 있다가 뗀 것              "" (전에는 값) 0        ★ 통째로 침묵
```

- **`display: none` 과 「트리 밖」은 같지 않다.** 앞은 **`color`·`fontSize`·`paddingTop` 을 보이는 요소와 똑같이** 답하고, **레이아웃이 필요한 칸만** 원문으로 남는다(`width` 가 `"50%"`, `transform` 이 `"none"`). 뒤는 **모든 값이 빈 문자열이고 `length` 가 0** 이다.
- **한 문장으로** — **`display: none` 은 「스타일은 있는데 상자가 없는 것」이고, 트리 밖은 「스타일 자체가 없는 것**」이다. 명세가 「요소가 렌더 트리와 연결돼 있지 않으면 계산 스타일이 없다」고 정했다.
- **「뗀 뒤 같은 노드」 줄이 결정적**이다 — 붙어 있을 때 `"rgb(0, 128, 0)"` 을 주던 **바로 그 노드**가 떼자 `""` 를 준다. 노드가 바뀐 것이 아니라 **연결이 끊긴 것**이다.
- `display: none` 쪽 규정의 정본은 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)(②와 ③ 사이에 레이아웃이 있다)이고, **「트리 밖은 침묵한다」가 이 갈래 고유의 몫**이다.

### 5. 의사 요소를 물으면 — 콜론이 없어도 된다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-none.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '18,28p'
의사 요소 — 두 번째 인자로 묻는다
두 번째 인자                content                       color
"::before"                  "\"표식\""                    "rgb(0, 0, 255)"
":before"                   "\"표식\""                    "rgb(0, 0, 255)"
"::after"                   "none"                        "rgb(0, 128, 0)"
"::marker"                  "normal"                      "rgb(255, 0, 255)"
"::first-line"              "normal"                      "rgb(0, 128, 0)"
"::zzz"                     ""                            ""
"before"                    "\"표식\""                    "rgb(0, 0, 255)"
""                          "normal"                      "rgb(0, 128, 0)"
(인자 없이 요소 자신)       "normal"                      "rgb(0, 128, 0)"
(exit 0)
```

**왜 그런가**

- **`'::before'` 와 `':before'` 가 같은 답**을 준다 — 옛 한 콜론 표기도 받는다.
- ★ **콜론이 아예 없어도 같은 답**이다(`'before'`). 명세가 앞의 콜론을 벗겨 내고 **이름만** 본다.
- **`'::after'` 의 `content` 는 `"none"`** 이다 — 규칙을 안 줬기 때문이고, **`::before`/`::after` 에서 `content` 의 초깃값이 `normal` 이 아니라 `none` 으로 계산**된다(정본: [CSS 13번 주제](../../languages/css/syntax/13-pseudo-elements-and-generated-content/2-summary.md)).
- **모르는 이름(`'::zzz'`)은 예외가 아니라 빈 문자열**이다. **오타가 조용하다.**
- **마지막 둘(`''` 와 인자 없음)은 요소 자신**을 읽는다 — `content` 가 `"normal"`, `color` 가 요소의 것이다. ★ **인자를 빼먹으면 다른 것을 읽는데 아무 말도 없다.**
- `::marker` 가 `"rgb(255, 0, 255)"` 를 답한 것이 **두 번째 인자가 제대로 동작했다는 대조군**이다.

### 6. 라이브인가 스냅숏인가 — 객체는 새것, 값은 라이브

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-live.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
라이브인가 스냅숏인가 — 02번의 물음을 CSSOM 에 겹친다
같은 요소로 두 번 부르면      cs1 === cs2 가 false
el.style 은                   a.style === a.style 가 true
잡아 둘 때 cs1.color · width  "rgb(0, 128, 0)"          "100px"
a.style.color 를 바꾼 뒤      "rgb(255, 0, 0)"          잡아 둔 객체가 바뀌었다
class 를 갈아 폭을 바꾼 뒤    "300px"                   (시트 쪽 변경도 따라온다)
새로 부른 것과 같은가         "300px"                   true
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-live.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,14p'
잡아 둔 객체는 요소를 따라다닌다 — 요소가 트리를 떠나도
떼기 전 cs1.color · width     "rgb(255, 0, 0)"          "300px"
a.remove() 뒤 같은 cs1        ""                        ""
  cs1.length                  0                         a.isConnected = false
다시 붙인 뒤 같은 cs1         "rgb(255, 0, 0)"          "300px"
  cs1 === 처음 잡은 그 객체   false                     (부른 자리마다 새 객체다)
(exit 0)
```

**왜 그런가**

- **`cs1 === cs2` 가 `false`** 다 — 부를 때마다 **새 객체**다. **`a.style === a.style` 은 `true`** 다 — 이쪽은 같은 객체다. **둘이 반대**다.
- **라이브인 것은 값**이다. 잡아 둔 `cs1` 이 **인라인 변경**(`a.style.color`)도, **시트 쪽 변경**(`class` 를 갈아 폭이 바뀐 것)도 따라왔다.
- **떼면 빈 문자열이 오고 `length` 가 0** 이 된다(A4 의 「트리 밖」과 같다). **다시 붙이면 값이 돌아온다** — 객체가 죽은 것이 아니라 **요소를 계속 따라다니고 있었다**는 뜻이다.
- **값을 붙들어 두려면 문자열로 복사한다** — `const w = cs.width;`. 객체를 들고 있는 것으로는 **아무것도 고정되지 않는다.**

```text
                    el.style                 getComputedStyle(el)
   객체 동일성      === 가 true              === 가 false (매번 새것)
   보는 범위        내가 쓴 것만             전부
   쓸 수 있나       쓸 수 있다               읽기 전용 (예외)
   값               라이브                   라이브
   요소를 떼면      그대로                   ★ 전부 빈 문자열 · length 0
```

### 7. 계산값과 실제 상자 — `cs.width` 가 넷 다 같은데 상자는 넷 다 다르다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-used.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
창 ④ — 계산값 옆에 실제 상자를 나란히 둔다
무엇을                        cs.width            rect.width    무엇이 갈랐나
#cb  box-sizing 기본          "200px"             230.00        테두리·여백이 밖으로
#bb  border-box               "200px"             200.00        테두리·여백이 안으로
#sc  transform: scale(2)      "200px"             460.00        transform 이 안 섞인다
#gone  display: none          "200px"             0.00          ★ 상자가 아예 없다
(exit 0)
```

**왜 그런가**

- **`cs.width` 는 넷 다 `"200px"`** 이고 **상자는 230 / 200 / 460 / 0** 이다.
- **`box-sizing`** — `getComputedStyle().width` 는 **콘텐츠 상자**를 답한다. 그래서 테두리·안쪽 여백이 밖으로 나가면 상자가 230 이 되고, 안으로 들어가면 200 으로 같아진다. **계산값만 보면 둘이 구분이 안 된다.**
- ★ **`transform` 은 계산값에 안 섞인다.** `scale(2)` 인데 `cs.width` 는 `"200px"` 이고 상자는 **460**(= (200+20+10) × 2)이다. `transform` 은 **별도 속성으로** 계산값에 있고 `width` 에는 반영되지 않는다.
- ★ **`display: none` 이면 상자가 0** 이다. 계산값은 `"200px"` 이라고 **또박또박 답하는데** 화면에는 아무것도 없다.
- **그래서 「보이나」를 계산값으로 판정하면 틀린다** — `width` 가 픽셀로 나와도 상자가 없을 수 있고, 조상이 숨어 있으면 자기 `display` 는 `"block"` 이다. 판정은 **상자 크기**(창 ④)나 `checkVisibility()` 로 한다.

### 8. 계산값이 그대로인데 결과만 갈리는 자리 — ★ 이 주제의 결정적 실측

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-used.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,12p'
계산값이 한 글자도 안 바뀌는데 결과만 갈린다 — flex 항목의 min-width: auto
                              cs.minWidth         cs.overflow   rect.width  (#long / #rest)
처음                          "auto"              "visible"     307.19 / 35.09
style.overflow = 'hidden'     "auto"              "hidden"      100.00 / 100.00
style.minWidth = '0'          "0px"               "visible"     100.00 / 100.00
(exit 0)
```

**왜 그런가**

```text
   단계                        cs.minWidth   cs.overflow   상자 (#long / #rest)
   처음                        "auto"        "visible"     307.19 / 35.09
   style.overflow = 'hidden'   "auto"        "hidden"      100.00 / 100.00   ★ 계산값 그대로
   style.minWidth = '0'        "0px"         "visible"     100.00 / 100.00
```

- flex 항목의 **`min-width: auto`** 는 「내용보다 작아지지 마라」를 뜻한다. 그래서 **긴 라틴 낱말**(줄바꿈이 안 되는 것)이 든 항목이 307.19 를 차지하고 옆 항목이 35.09 로 밀렸다.
- ★ **`overflow: hidden` 을 주면 그 규칙이 꺼진다** — 상자가 **100 / 100** 으로 균등해진다. 그런데 **`cs.minWidth` 는 여전히 `"auto"`** 다. **계산값이 바뀌지 않는 단계가 둘째 단계**다.
- **왜 한쪽만 흔적이 남나** — `min-width: 0` 은 **그 속성의 값을 직접 바꾸는 것**이라 계산값이 `"0px"` 이 된다. `overflow: hidden` 은 **`min-width` 를 건드리지 않고** 「`auto` 가 무슨 뜻인지」를 바꾼다. **계산값은 「무엇이 선언됐나」를 말하지 「무엇이 일어나나」를 말하지 않는다.**
- ★ **그래서 이 주제의 창 ④ 를 `getBoundingClientRect` 로 정했다.** CSS 갈래가 같은 모양을 여러 번 만나고 전부 그 창으로 잡았다(정본: [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)의 진단 3창 주변 논의).
- 마지막 블록은 **창 ④ 가 새 정보를 안 주는 자리**다 — 트리 밖에서는 두 창이 함께 침묵한다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-used.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,17p'
트리 밖 · 다른 문서 — 계산값 창구가 아예 침묵한다
무엇에 물었나                 cs.width            cs.length     rect.width
createElement 만 한 것        ""                  0             0.00
붙어 있다가 뗀 것             "200px" -> ""       0             0.00
(exit 0)
```

- ★ **`307.19` 와 `35.09` 는 이 머신의 글꼴 치수에 달린 값**이다. **결론으로 쓰는 것은 「셋째 자리 수 대 100」이라는 관계**이지 숫자가 아니다.

### 9. 얼마나 비싼가 — 비싼 것은 섞는 것이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
읽기와 쓰기를 섞으면 — 400행 · 9판의 중앙값

쓰기·읽기 교차 (한 행마다 번갈아)       중앙값    57.00 ms   최소    53.20   최대    97.80
쓰기 다 하고 읽기 다 하기               중앙값     3.00 ms   최소     0.70   최대     5.10
읽기만 (쓰기 없음)                      중앙값     1.10 ms   최소     0.60   최대     1.60
쓰기만 (읽기 없음)                      중앙값     0.10 ms   최소     0.10   최대     0.20
(exit 0)
```

**왜 그런가**

```text
   순위 (이 판의 중앙값)
   쓰기·읽기 교차        57.00 ms   ★ 혼자 한 자릿수 위다
   쓰기 묶음 + 읽기 묶음  3.00 ms
   읽기만                 1.10 ms
   쓰기만                 0.10 ms    (분해능 한 칸 — 못 잰다)
```

- **비싼 것은 읽기도 쓰기도 아니라 「섞는 것**」이다. 위 두 줄은 **쓰기 횟수도 읽기 횟수도 같고 순서만 다른데** 자릿수가 하나 넘게 갈린다.
- 원리는 이렇다 — 쓰기가 레이아웃을 **더럽히고**, 그 뒤의 읽기가 **그 자리에서 다시 계산하게(강제 동기 레이아웃)** 만든다. 묶어 놓으면 더러움이 한 번만 풀린다.
- **신호 대 잡음** — 교차 조건과 묶음 조건은 **한 자릿수 이상** 차이라 신호가 압도적이다. **이 비교만 결론으로 쓴다.** 아래 「쓰기만」 줄(`0.10`\~`0.20`)은 **분해능 한두 칸**이라 그 절댓값으로 순위를 주장하지 않는다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,15p'
무엇을 읽느냐가 가른다 — 쓰기 뒤에 2000번 읽는다

쓰고 cs.color 읽기 (계산값)             중앙값     7.80 ms   최소     6.90   최대     9.50
쓰고 cs.width 읽기 (사용값)             중앙값   242.50 ms   최소   198.20   최대   250.60
쓰고 getComputedStyle 만 부르기         중앙값     0.70 ms   최소     0.70   최대     1.00
쓰기 없이 cs.width 만 읽기              중앙값     2.50 ms   최소     2.20   최대     2.80

sink = true   (읽은 값을 버리지 않았다는 확인)
(exit 0)
```

- **`getComputedStyle(el)` 을 부르기만 하면 0.70ms** — **객체를 만드는 것은 거의 공짜**다.
- **거기서 `color` 를 읽으면 7.80ms**, **`width` 를 읽으면 242.50ms** — **30배 가까이**다. **`color` 는 레이아웃이 필요 없고 `width` 는 필요하다.**
- **쓰기 없이 `width` 만 2000번 읽으면 2.50ms** — 레이아웃이 안 더러우면 다시 계산할 것이 없다.
- ★ **위 표의 가장 작은 칸은 「쓰기만」 줄의 `0.10`** 이고 그것은 **분해능 한 칸**이다 — 「공짜」가 아니라 「**이 도구로는 못 잰다**」로 읽는다. `performance.now()` 의 분해능이 **100마이크로초**다.
- 고치는 법(읽기 묶음과 쓰기 묶음으로 가르기)은 [목록의 **10번 주제**](../10-layout-thrashing/)가 정본이다.

### 10. 왜 창 ④ 가 필요한가 — 주인공을 검사할 창이 따로 있어야 한다

**출력** — 창 ① 이 이 주제에서 무엇을 보여 주는지부터.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-tree.html | sed -n '4,5p'
<style>#p { color: rgb(0, 128, 0); font-size: 21px }</style>
</head><body><p id="p">시트가 칠한 글</p>
(exit 0)
```

**왜 그런가**

- CSS 갈래의 진단 3창에서 `getComputedStyle` 은 **셋째 창**이고 「**이겼나**」를 묻는다 — `cssRules`(담겼나) → `querySelectorAll`(잡혔나) → `getComputedStyle`(이겼나). 정본은 [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)다.
- **이 주제에서는 그 셋째 창 자체가 주인공**이다. 주인공을 주인공으로 검사할 수는 없으므로 **그 창을 검사할 창**이 필요하다 — 그것이 `getBoundingClientRect()` 다.
- **창 ① 은 아무것도 안 보여 준다** — 위 트리의 `<p id="p">` 에는 **아무 속성도 없다.** 계산값을 읽어도 트리에 자국이 안 남고, 시트가 칠한 초록은 `<style>` 안의 **규칙 글자로만** 있다. **「이 요소가 지금 무슨 색인가」는 창 ① 으로 영영 못 묻는다.**
- **한 실측으로 뒷받침** — A8 의 둘째 단계다. **`cs.minWidth` 가 `"auto"` 로 한 글자도 안 바뀌었는데 상자가 307.19 에서 100 으로 바뀌었다.** 계산값은 「`min-width` 가 `auto` 로 선언됐다」를 말할 뿐이고, 「그 `auto` 가 지금 무슨 뜻인지」는 말하지 않는다.

### 11. 다른 주제와 잇기

**왜 그런가**

- **[07번 주제](../07-dataset-classlist-inline-style/2-summary.md)가 넘긴 질문** — **「`el.style` 에 없는 값은 지금 무엇이고, 그것을 어떻게 읽나.」** 07 은 `el.style.length` 가 **0** 인 채 화면이 초록인 것을 보여 주고 멈췄다.
- **[CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)와의 경계선** — **저쪽은 「어느 단계의 값이 나오나」, 이쪽은 「그 값을 어느 창구로 어떤 모양으로 받나」.** 지정값·계산값·사용값·실제값의 구분과 `%`·`em` 의 절대화 시점, `display:none` 의 되돌림은 전부 저쪽이 정본이고 **여기서 다시 쓰지 않았다.** 여기 고유의 것은 **객체의 성질**(읽기 전용·매번 새것·라이브), **읽는 문법 셋**, **트리 밖의 침묵**, **창 ④**, **비용**이다.
- **[목록의 10번 주제](../10-layout-thrashing/)가 미리 드러난 절** — 동작 방식 **(11)**(= A9)이다. 「쓰기·읽기 교차 57.00ms 대 묶음 3.00ms」가 그 주제의 전부를 한 줄로 보여 준다. 다만 **고치는 법은 그쪽이 정본**이다.
- **[04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)에서 물려받은 한계** — **`performance.now()` 의 분해능이 100마이크로초**라는 것. 그래서 이 문서는 **분해능 한 칸인 `0.10` 을 「공짜」로 읽지 않고 「못 잰다」로** 적었고, **그 줄로는 순위를 주장하지 않았다.**

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

**측정 조건** — 도구는 **`performance.now()`** 하나(벤치마크 하네스가 아니다) · 머신은 이 Linux 한 대 · **판 수 9** · **중앙값**을 쓰고 최소·최대를 함께 실었다 · 교차·묶음 조건은 행 **400**, 속성별 조건은 반복 **2000**.\
**재현되는 것은 자릿수와 순위**다. 절댓값은 재현되지 않는다.\
**신호 대 잡음** — 교차 대 묶음은 **한 자릿수 이상** 차이라 신호가 압도적이고, `cs.color` 대 `cs.width` 는 **30배 가까이**다. **그 둘만 결론으로 쓴다.** 「쓰기만」 줄(`0.10`\~`0.20`)은 **분해능 한두 칸이라 그 절댓값으로 순위를 주장하지 않는다.**

**하네스** — 01\~07 과 같은 것을 쓴다. 블록은 `capture.sh` 가 전부 파일로 받았고 사람이 옮겨 적지 않았다.

```bash
# 블록 하나를 다시 던지는 법
google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-used.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 이 주제의 창 ④ — 계산값 옆에 실제 상자를 나란히 둔다
J(getComputedStyle(el).width) + '   ' + el.getBoundingClientRect().width.toFixed(2)
// 창 ⑤ (04번에서 빌림) — 9판 중앙값. 분해능 100마이크로초
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
// 한글 칸 정렬은 JS 안에서 2폭 padw 로 한다. padEnd 는 UTF-16 단위라 어긋난다.
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
```

★ **`--virtual-time-budget` 은 쓰지 않았다**(이 갈래의 정본 규칙).\
★ **`--dump-dom` 은 `load` + `setTimeout(…, 0)` 까지만 기다린다.** 이 주제의 실험은 전부 **파싱 직후 동기**로 끝나므로 그 한계에 안 걸린다.\
★ **출력은 `<pre>` 가 아니라 `<script type="text/plain">` 에 담아 마커로 잘랐다.**

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 값이 온 곳 6종 × 두 창구 | 2 | 동작 방식 (2) · A1 |
| 객체의 타입·`length`·`cssText` · 쓰기 4종의 예외 | 2 | 동작 방식 (3) · A2 |
| 읽는 문법 8종 | 3 | 동작 방식 (4) · A3 |
| 단축 되접기 6종 · 목록과 `length` · `window` 동일성 | 3 | 동작 방식 (5) · A3 |
| 두 창구의 절대화 대조 4줄 | 2 | 동작 방식 (6) |
| `display:none` 6속성 × 두 요소 | 3 | 동작 방식 (7) · A4 |
| 트리 밖 3종(`createElement`·`template`·뗀 것) | 3 | 동작 방식 (7) · A4 |
| 의사 요소 8종 × 2속성 | 3 | 동작 방식 (8) · A5 |
| 라이브·객체 동일성·떼고 붙이기 | 3 | 동작 방식 (9) · A6 |
| 창 ④ — 계산값 대 상자 4종 | 3 | 동작 방식 (10) · A7 |
| 창 ④ — flex `min-width: auto` 3단계 | 3 | 동작 방식 (10) · A8 · A10 |
| **읽기·쓰기 4조건 × 9판** 중앙값·최소·최대 | 3 | 동작 방식 (11) · A9 |
| **속성별 4조건 × 9판** 중앙값·최소·최대 | 3 | 동작 방식 (11) · A9 |
| 창 ① 계산값을 읽은 문서의 트리 | 2 | 동작 방식 (1) · A10 |
| `demo` 블록을 래퍼에 띄워 초기 상태 + 버튼 확인 | 1 | 동작 방식 (11)의 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| **모든 시간 수치** | 위 표 | 판마다 흔들린다. **자릿수와 순위만 결론으로 쓴다** |
| `performance.now()` 의 분해능 | 100마이크로초 | Blink 의 정책이고 명세가 정한 값이 아니다 |
| **`length` 의 값** | 475 · 476 | **Chrome 151 이 지원하는 속성 수 + 그 문서의 커스텀 속성 수.** 상수로 쓰지 마라 |
| `item(i)` 목록의 내용 | `accent-color`·`align-content`·… | 순서는 명세가 정하지만 **어느 속성이 있나**는 구현이다 |
| `cs.font` 의 글꼴 이름 | `"Noto Sans CJK KR"` | **이 머신의 글꼴 설정**이다 |
| flex 실측의 `307.19`·`35.09` | 위 출력 | **글꼴 치수**에 달렸다. 결론은 「셋째 자리 수 대 100」이라는 관계뿐 |
| `cs.background` 가 펼쳐지는 긴 문자열 | 위 출력 | CSSOM 직렬화 + 구현 |
| 계산값의 정규화 형식(`matrix(…)`·`rgb(…)`) | 위 출력 | 명세 + 구현 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). ② **`el.computedStyleMap()`**(Typed OM) — 표면만 적었고 던져 보지 않았다. ③ **`el.checkVisibility()`** — 「보이나」 판정에 쓸 수 있다고 적었지만 **안 던졌다.** ④ **그림자 경계 안의 요소**에 대한 계산값([목록의 **12번 주제**](../12-shadow-dom/)의 몫). ⑤ **`::first-line`·`::selection` 처럼 「진짜 상자가 없는」 의사 요소의 계산값이 얼마나 믿을 만한지** — `::first-line` 에 규칙을 안 준 채 읽어 기본값만 확인했다. **「의사 요소 전부가 그렇다」로 일반화하지 않는다.** ⑥ **`getComputedStyle` 과 `MutationObserver`·`ResizeObserver` 의 상호작용**(목록의 **36·37번 주제**). ⑦ **`cs.color` 가 왜 싼지의 내부 근거** — Blink 소스를 읽지 않았다. **관찰만 적었고 「레이아웃이 필요 없어서」는 명세의 단계 구분으로부터의 추론**이다.

## 용어 풀이

- **해석값(resolved value)** — `getComputedStyle` 이 돌려주는 것에 명세가 붙인 이름. **속성에 따라 계산값일 때와 사용값일 때가 있다**(정본: [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)).
- **계산값(computed value)** — `em`·`thin`·`red` 가 절대화된 판. **상속되는 것이 이것**이다.
- **사용값(used value)** — `%`·`auto` 가 레이아웃으로 풀린 판. **상자가 있어야 존재한다.**
- **`CSSStyleDeclaration`** — `el.style` 과 `getComputedStyle` 이 공유하는 타입.
- **`NoModificationAllowedError`** — 읽기 전용 객체에 쓰려 할 때의 예외 이름.
- **라이브(live)** — 잡아 둔 객체가 나중 변경을 따라오는 것.
- **의사 요소** — `::before`·`::after`·`::marker`. **두 번째 인자**로 읽는다.
- **낱개 속성(longhand)** — 목록에 담기는 것은 낱개뿐이다.
- **정규화된 형식** — `red` → `rgb(255, 0, 0)`, `translateX(50%)` → `matrix(…)`.
- **강제 동기 레이아웃(forced synchronous layout)** — 쓰기로 더러워진 레이아웃을 읽기가 그 자리에서 다시 계산하게 만드는 것.
- **`min-width: auto`** — flex 항목에서 「내용보다 작아지지 마라」를 뜻하는 초깃값. `overflow` 가 `visible` 이 아니면 그 규칙이 꺼진다.
- **분해능(resolution)** — 측정 도구가 구분할 수 있는 최소 간격. 여기서는 100마이크로초.
- **중앙값(median)** — 여러 판을 크기순으로 늘어놓았을 때 가운데 값.
