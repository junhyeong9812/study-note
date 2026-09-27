# css/syntax/04 — 값 처리 단계: 지정값·계산값·사용값·실제값 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 값은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `getComputedStyle`·`getBoundingClientRect`·`offsetWidth`·`clientWidth` 로 읽은 것이다.\
> 규칙은 [CSS Cascading and Inheritance Level 5](https://drafts.csswg.org/css-cascade-5/) 「Value Processing」과 [CSSOM](https://drafts.csswg.org/cssom/) 「resolved values」로 접지했다.\
> **엔진은 Chrome 하나이고 `devicePixelRatio` 는 1이다.** 실제값 단계의 수치는 그 자리에 「구현 세부」로 표시했다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `width: 50%` 하나를 네 단계로 관통시켜라

**출력** (Chrome 151 headless)

```text
#half  width = 200px          (렌더된 상태)
#wrap  width = 400px
```

**네 단계의 값**

```text
① 지정값 specified   50%       캐스케이드가 뽑은 그 선언의 값
② 계산값 computed    50%       단위·키워드만 절대화한다. % 는 아직 못 푼다
③ 사용값 used        200px     부모 content 폭 400px 을 알아야 나온다
④ 실제값 actual      200px     장치 격자에 맞춘 값 (여기서는 그대로)
```

**`%` 가 계산값에서 아직 `%` 인 이유**

- `%` 를 풀려면 **기준이 되는 길이**(부모 content 폭)를 알아야 하고, 그것은 레이아웃을 돌려야 나온다.
- 계산값은 **레이아웃 이전**의 판이라 기준이 없다. 그래서 `%` 는 그대로 남겨 두고 다음 단계로 넘긴다.
- 같은 이유로 `auto`·`min-content` 도 계산값에서는 키워드 그대로다.

**레이아웃이 끼어드는 자리**

- **②와 ③ 사이**다. 이 문서의 모든 함정이 이 경계에서 나온다.

**`getComputedStyle(half).width`**

- **`"200px"`** — ③ 사용값을 준다.
- 곧 이 호출은 **「계산값」이 아니라** 「**해석값**」을 준다. 이름이 거짓말이다.

> **해석값(resolved value)** — `getComputedStyle` 이 돌려주는 값. CSSOM 이 속성마다 계산값/사용값 중 무엇을 줄지 규정한다.\
> 예: `width` 는 사용값 쪽, `color` 는 계산값 쪽이다.

### 2. 같은 코드가 다른 값을 돌려준다

**출력** (Chrome 151 headless)

```text
getComputedStyle(a).width = 200px        보이는 요소
getComputedStyle(b).width = 50%          display:none 인 요소
```

**두 값**

- `a` = **`"200px"`**, `b` = **`"50%"`**.

**갈리는 조건 한 문장**

- **그 요소가 상자를 만드는가.** 상자가 없으면 ③ 사용값이 존재하지 않으므로 ② 계산값이 대신 나온다.

```text
상자가 있다                          상자가 없다 (display:none)
+---------------------------+       +---------------------------+
| ② 계산값 50%              |       | ② 계산값 50%              |
|      ↓ 레이아웃           |       |      ↓ 레이아웃이 없다     |
| ③ 사용값 200px            |       |   (③ 이 만들어지지 않는다)|
+---------------------------+       +---------------------------+
   해석값 = 200px                       해석값 = 50%
```

- 조상 하나가 `display: none` 이어도 같다. 자기 자신일 필요가 없다.
- `visibility: hidden` 은 **상자를 만든다** — 그때는 `200px` 이 나온다.

**`color`·`letter-spacing` 은**

- **안 갈린다.** 둘 다 해석값이 계산값으로 규정돼 있어 상자와 무관하다.
- 실측: `display: none` 인 요소에서도 `letter-spacing: 0.1em`(부모 글꼴 20px)이 `2px` 로 나왔다.

**`parseFloat` 코드에서의 버그**

```js
const w = parseFloat(getComputedStyle(el).width);   // "200px" → 200   (개발 중)
                                                    // "50%"   → 50    (탭이 닫혀 있을 때)
                                                    // "auto"  → NaN
```

- 세 경우 다 **예외가 안 난다.** `50` 이나 `NaN` 이 그대로 흘러가 훨씬 나중에 어긋난 레이아웃으로만 드러난다.
- 실제 픽셀이 필요하면 `getBoundingClientRect().width` 를 쓴다.

### 3. `getComputedStyle` 은 어느 단계를 보여 주는가

**정식 이름**

- **해석값(resolved value)** 이다. CSSOM 명세의 용어이고, 「계산값(computed value)」과는 다른 개념이다.

**두 무리 (실측으로 확인한 것)**

```text
사용값을 주는 무리                    계산값을 주는 무리
+---------------------------+        +---------------------------+
| width       50%  → 200px  |        | color   red   → rgb(255,0,0)|
| margin      auto → 150px  |        | letter-spacing 0.1em → 2px  |
| transform   50%  → 100(px)|        | border-width thin → 1px     |
| height, padding, top/left |        | font-size, line-height:normal|
+---------------------------+        +---------------------------+
```

**갈림의 기준 한 문장**

- **레이아웃을 돌려야 알 수 있는 값이면 사용값을, 아니면 계산값을 준다.**

**반복 호출이 비싼 경우**

- **사용값을 주는 속성을 읽을 때**다. 최신 레이아웃이 필요하므로 **동기적으로 레이아웃을 강제**할 수 있다.
- 읽기와 쓰기를 번갈아 하면 그 횟수만큼 레이아웃이 돈다. 읽을 것을 먼저 모아 읽고 쓸 것을 몰아 쓰면 한 번으로 준다.
- `color` 같은 계산값 속성만 읽는 것은 이 비용이 없다.

### 4. `em` 은 어디서 픽셀이 되는가

**출력** (Chrome 151 headless)

```text
#parent font-size / text-indent / line-height / letter-spacing = 20px / 40px / 30px / 2px
#child  font-size / text-indent / line-height / letter-spacing = 10px / 40px / 15px / 2px
```

**세 값의 예측**

- `text-indent` = **`40px`** · `letter-spacing` = **`2px`** · `line-height` = **`15px`**.

**하나만 다시 계산되는 것과 그 이유**

- **`line-height`** 다.
- `line-height: 1.5` 의 **계산값은 「숫자 1.5」 자체**다(명세가 그렇게 정했다). 숫자가 상속되어 자식이 **자기 `font-size`** 에 곱한다 — `10 × 1.5 = 15px`.
- 나머지 둘은 계산값이 **이미 절대 길이**(`40px`·`2px`)라 그 길이가 그대로 내려온다.

**「자식이 부모의 `em` 을 다시 계산하지 않는다」의 증명**

```text
만약 자식이 다시 계산한다면            실제 (실측)
+---------------------------+         +---------------------------+
| text-indent 2em × 10px    |         | text-indent = 40px        |
|              = 20px       |         | letter-spacing = 2px      |
| letter-spacing 0.1em×10px |         +---------------------------+
|              = 1px        |
+---------------------------+
      ↑ 이 값들은 나오지 않았다
```

- 자식 글꼴이 절반인데 값이 그대로라는 것이 곧 **글자(`2em`)가 아니라 계산값(`40px`)이 내려왔다**는 증거다.

**`line-height: 1.5em` 으로 바꾸면**

- 부모의 계산값이 `30px`(절대 길이)이 되고, 자식은 **`30px`** 을 그대로 받는다.
- 자식 글꼴이 `10px` 인데 줄높이가 `30px` 이 되어 줄 간격이 지나치게 벌어진다.
- **무단위로 쓰라는 관례가 여기서 나온다.**

### 5. 중첩된 `em` 은 어떻게 되는가

**출력** (Chrome 151 headless)

```text
html      font-size = 16px
1단계 li  font-size = 24px
2단계 li  font-size = 36px
3단계 li  font-size = 54px
```

**세 단계의 예측**

- **24px → 36px → 54px**. 매 단계 1.5배씩 곱해진다.

**`font-size` 는 곱해지고 `letter-spacing` 은 안 곱해지는 이유**

```text
font-size: 1.5em                     letter-spacing: 0.4em
  em 의 기준 = 부모의 font-size        em 의 기준 = 그 요소 자신의 font-size
      ↓                                    ↓
  자식이 자기 선언을 갖고 있으므로       자식에 선언이 없으면 계산값이
  매번 새로 계산된다 → 곱해진다          그대로 상속된다 → 안 곱해진다
```

- **`em` 의 기준이 두 가지**인 것이 핵심이다 — `font-size` 에 쓴 `em` 만 부모 기준이고, 나머지 속성의 `em` 은 그 요소 자신의 `font-size` 기준이다.
- 그리고 `letter-spacing` 은 자식에 **선언이 없어서** 계산 자체가 안 일어난다(03번의 상속 규칙).

**`1.5rem` 으로 바꾸면**

- **세 단계 모두 `24px`** 이 된다(실측). `rem` 은 루트 글꼴만 보므로 중첩과 무관하다.

**`em` 과 `rem` 의 대가**

| | 얻는 것 | 잃는 것 |
|---|---|---|
| `em` | 컴포넌트 글꼴을 바꾸면 여백이 같이 따라온다 | 중첩에서 곱해진다 |
| `rem` | 어디에 있든 값이 같아 예측하기 쉽다 | 컴포넌트 글꼴을 바꿔도 여백이 안 따라온다 |

### 6. 이 세 창구는 같은 것을 묻는가

**출력** (Chrome 151 headless — `width:200px; padding:15px; border:5px solid`)

```text
box-sizing: content-box   gCS.width=200px  clientWidth=230  offsetWidth=240  rect=240
box-sizing: border-box    gCS.width=200px  clientWidth=190  offsetWidth=200  rect=200
transform: scale(2) 인 width:100px 요소   gCS.width=100px   rect=200
```

**셋이 돌려주는 것 (`content-box`)**

- `getComputedStyle().width` = **`200px`** — 내가 쓴 `width` 가 가리키던 상자의 사용값.
- `getBoundingClientRect().width` = **`240`** — 테두리까지 포함한 실제 상자(200 + 패딩 30 + 테두리 10).
- `offsetWidth` = **`240`** — 같은 폭을 **정수로 반올림**한 값.

**`border-box` 로 바꾸면**

- `getComputedStyle().width` 는 **여전히 `200px`** 이지만 그 `200px` 의 **뜻이 바뀐다** — 이제 테두리까지 포함한 폭이다.
- `clientWidth` 가 `230 → 190` 으로 바뀐 것이 그 증거다(content 가 `200 → 160` 으로 줄었다).
- **★ 곧 해석값은 「`box-sizing` 이 가리키는 그 상자」의 사용값**이지, 언제나 content 폭이 아니다.

**`transform: scale(2)` 에서 두 배가 되는 것**

- **`getBoundingClientRect().width` 하나**다(`100px` → `200`).
- `getComputedStyle().width` 는 `100px` 그대로다 — 변환은 레이아웃 이후의 일이라 `width` 의 사용값을 안 바꾼다.

**`offsetWidth` 로 레이아웃 계산을 하면 안 되는 이유**

- **이미 정수로 반올림된 값**이기 때문이다. 실측에서 `100.594px` 짜리 상자의 `offsetWidth` 는 `101` 이었다.
- 이것을 다시 나누거나 누적하면 칸 수만큼 오차가 쌓인다. 소수가 필요하면 `getBoundingClientRect()` 를 쓴다.

### 7. 실제값이 보이는 자리

**출력** (Chrome 151 headless, `devicePixelRatio = 1`)

```text
#frac (렌더됨)      getComputedStyle=100.594px   rect=100.59375   offsetWidth=101
#frac (display:none) getComputedStyle=100.6px
.third (333px 의 33.333%)  getComputedStyle=110.984px  rect=110.984375
.third 셋의 합       110.984375 × 3 = 332.953125      (부모 333px 에 0.046875px 모자란다)
```

**렌더된 `#frac` 의 두 값**

- `getComputedStyle().width` = **`100.594px`**, `getBoundingClientRect().width` = **`100.59375`**.
- 둘은 **같은 값의 다른 표기**다 — 뒤엣것이 정확한 값이고 앞엣것은 소수 셋째 자리로 자른 것이다.

**`display: none` 으로 만들면**

- **`100.6px`** — 내가 쓴 값 그대로다.
- 상자가 없으면 ③ 사용값도 ④ 실제값도 만들어지지 않으므로 ② 계산값이 나온다. **격자를 안 탄다.**

**`.third` 셋의 합**

- **`332.953125px`** — 부모 `333px` 에 **`0.046875px` 모자란다.**
- `getComputedStyle` 이 보여 주는 `110.984px` 을 세 배 하면 `332.952px` 이라 **손으로 검산해도 안 맞는다.** 표시값이 잘린 값이기 때문이다.

**보장인가 구현 세부인가**

- **구현 세부**다. `100.59375 = 6438/64` 이고, 이것은 **Chrome 151 이 길이를 1/64px 고정소수점으로 저장**하기 때문에 나온 수치다.
- 명세는 「장치에 맞게 근사한다」까지만 정한다. **다른 엔진·다른 `devicePixelRatio` 에서는 다른 값이 나올 수 있다** — 이 문서는 한 엔진에서만 확인했다.
- 「소수 폭은 정확히 안 나눠진다」는 **성질**이고, 「0.046875px 이 남는다」는 **한 판의 결과**다. 결론은 앞엣것 위에만 세운다.

### 8. 세로 마진의 `%` 는 무엇의 비율인가

**출력** (Chrome 151 headless, 부모 `width: 400px` · 높이 `auto`)

```text
#box margin-top = 40px   margin-left = 40px
```

**두 값**

- **둘 다 `40px`** 이다. 부모 폭 `400px` 의 10%.

**폭을 기준으로 삼는 이유**

```text
만약 높이 기준이라면
  부모 높이 ← 자식들의 높이 합 ← 자식의 세로 마진 ← 부모 높이 ...
                                                        ↑ 순환
```

- 부모 높이가 `auto` 면 **높이가 자식에 의존하고 자식 마진이 다시 높이에 의존해 순환**한다.
- 그래서 명세가 **인라인 방향(가로쓰기에서는 폭)** 하나로 못박았다. 상하 패딩도 같다.

**어느 단계의 일인가**

- **③ 사용값** 단계다. `%` 는 ②에서 못 풀리고 레이아웃이 기준 길이를 알려 줘야 풀린다.

**`padding-top: 56.25%` 로 16:9 상자 만들기**

- 같은 규칙 덕분이다 — **상하 패딩의 `%` 가 폭 기준**이라 `높이 = 폭 × 0.5625` 가 된다(`9/16 = 0.5625`).
- 실측: 부모 `400px` 에서 `padding-top: 56.25%` 인 요소의 `padding-top` 이 `225px`, 상자 높이가 `225` 였다(`400 × 0.5625 = 225`).
- 오늘은 `aspect-ratio` 로 직접 쓸 수 있다([목록의 **31번 주제**](../31-intrinsic-sizing-and-aspect-ratio/)). 이 관행은 그 이전의 우회였다.

### 9. `transform` 을 숨겨진 요소에서 읽으면

**출력** (Chrome 151 headless)

```text
#a (display:none)       transform = none
#a width                            = 200px
#b (visibility:hidden)  transform = matrix(1, 0, 0, 1, 100, 0)
```

**`display: none` 일 때**

- **`"none"`** 이 나온다. 선언이 사라진 게 아니다.

**`visibility: hidden` 으로 바꾸면**

- **`matrix(1, 0, 0, 1, 100, 0)`** 이 나온다. `translateX(50%)` 의 `50%` 가 **상자 폭 200px 의 절반인 100px** 로 풀렸다.
- `visibility: hidden` 은 **상자를 만든다** — 자리를 차지하고 레이아웃을 돈다.

**사용값인가 계산값인가**

- **사용값**이다. 근거는 **`%` 가 풀려 있다**는 것이다 — `%` 를 풀려면 상자 치수를 알아야 하고, 그것은 레이아웃 이후다.
- 같은 이유로 상자가 없는 `display: none` 에서는 만들 수 없어 `none` 으로 떨어진다.

**어디서 깨지는가**

```js
el.style.display = 'none';
const t = getComputedStyle(el).transform;   // "none"  ← 여기서 잃는다
el.style.display = '';
el.style.transform = t;                     // 변환이 통째로 사라진다
```

- **예외도 경고도 없다.** 요소가 제자리로 튀는 것으로만 드러난다.
- 상자가 있는 상태에서 읽거나, 선언 값 자체가 필요하면 `el.style.transform`·`cssRules` 쪽을 읽는다.

### 10. 다른 주제와 잇기

**자식이 물려받는 판**

- **② 계산값**이다.
- ①이 아닌 이유 — 그러면 자식마다 `em` 을 다시 풀게 되어 부모 글꼴 변경이 자손 전체를 예측 불가능하게 흔든다.
- ③이 아닌 이유 — 사용값은 **그 요소의 상자에 딸린 값**이라 다른 상자에 의미가 없다.
- 그래서 [03번 주제](../03-inheritance-and-global-keywords/2-summary.md)의 `inherit` 도 정확히 「부모의 **계산값**」이다.

**`width: auto` 가 전환되지 않는 이유**

- 전환은 **계산값 사이를 보간**하는데, `auto` 의 계산값은 `auto` 라는 **키워드**다.
- `auto` 와 `200px` 사이에는 중간값이 정의되지 않는다 — 「절반쯤 auto」가 없다.
- 사용값 `300px` 과 `200px` 사이라면 보간할 수 있겠지만, **전환은 ③이 아니라 ②를 본다.** 정본은 [52번 주제](../52-transition/2-summary.md).

**`"30px"` 을 보고도 「계산값은 숫자 1.5」라고 말할 근거**

- **상속 결과**다. 자식(`font-size: 10px`)의 `line-height` 가 `15px` 이었다.
- `30px` 이 상속됐다면 자식도 `30px` 이어야 한다. `15px` 이 나왔다는 것은 **숫자가 내려와 다시 곱해졌다**는 뜻이다.
- 곧 **출력 하나만으로는 단계를 판정할 수 없다** — 상속을 한 칸 더 보아야 한다. 이 주제에서 가장 조심할 자리다.

**무효한 값이 걸러지는 곳**

- **네 단계 중 어디도 아니다.** `width: 10`(단위 없음)은 **파싱 단계에서 선언째 버려진다.**
- 실측: 그 규칙의 `style` 목록에 `width` 가 **아예 들어 있지 않았다**(`[height]` 만 남았다).
- 곧 ①지정값조차 만들어지지 않는다. 정본은 [07번 주제](../07-syntax-and-error-recovery/2-summary.md).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `devicePixelRatio = 1`. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다).

**하네스** — 03\~07 다섯 주제가 공유한 것이다. 문서 조각과 프로브 스크립트를 합쳐 한 문서로 만들고, 결과를 `<pre>` 에 써 넣은 뒤 `--dump-dom` 에서 잘라 읽는다.

```bash
# harness.sh body.html probes.js   —  probes.js 안에서 P(라벨, 값) / CS(선택자, 속성) 을 쓴다
{ echo '<!doctype html><meta charset="utf-8"><title>probe</title>'
  cat "$1"
  echo '<script>'
  echo 'const __o=[];function P(k,v){__o.push(k+" = "+v)}'
  echo 'function CS(s,p){return getComputedStyle(document.querySelector(s)).getPropertyValue(p)}'
  cat "$2"
  echo 'const __p=document.createElement("pre");'
  echo '__p.textContent="<<<BEGIN>>>\n"+__o.join("\n")+"\n<<<END>>>";'
  echo 'document.body.appendChild(__p);</script>'
} > /tmp/doc.html
google-chrome --headless --disable-gpu --no-sandbox --dump-dom /tmp/doc.html 2>/dev/null \
  | sed -n '/&lt;&lt;&lt;BEGIN&gt;&gt;&gt;/,/&lt;&lt;&lt;END&gt;&gt;&gt;/p' | sed '1d;$d'
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `width: 50%`·`auto`·`100.6px` × (렌더됨 / `display:none`) | 2 | 동작 방식 (1)(3)(4) · A1 · A2 · A7 |
| `margin: auto`·`margin: 10%`·`height: 50%` 사용값 | 1 | 동작 방식 (3) · A8 |
| `em` 4속성 × 부모·자식 | 1 | 동작 방식 (2) · A4 |
| `line-height` 4형태(`1.5`·`normal`·`1.5em`·`display:none`) | 1 | 동작 방식 (3) · A4 · A10 |
| `transform` × (렌더됨 / `display:none` / `visibility:hidden`) | 2 | 동작 방식 (3) · A9 |
| `border-width` `thin/medium/thick` · `0.3px/0.6px/1px` | 2 | 동작 방식 (3)(4) |
| `box-sizing` 두 모드 × 4창구 | 1 | 문법 절 · A6 |
| `transform: scale(2)` × 3창구 | 1 | A6 |
| `33.333%` 셋의 합 · `padding-top: 56.25%` | 2 | 동작 방식 (4) · A7 · A8 |
| demo 2개(`em` 중첩 목록 · `letter-spacing` 상속) — 값 + 스크린샷 | 각 1 | 2-summary 의 demo |
| demo 의 「바꿔 볼 것」 단언 2개(`1.5rem` 셋 다 24px · 자식에서 재선언 시 4px) | 각 1 | 2-summary 의 demo |

**구현에 달린 항목** — 버전·머신이 바뀌면 다시 찍을 자리다.

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `100.6px` → `100.59375` | 1/64px 격자 | Chrome 의 고정소수점 구현 |
| `33.333%` of 333px → `110.984375` | 〃 | 〃 |
| `0.3px` 테두리가 `1px` 로 보이는 것 | `display:none` 에서도 `1px` | 명세상 실제값 단계의 반올림을 Chrome 이 더 앞에서 한다 |
| `offsetWidth` = `101` | 정수 반올림 | CSSOM View 규정 + 위 격자값 |
| `line-height: 1.5` 해석값 `"30px"` | 직렬화 형식 | 계산값이 숫자라는 것은 명세, `"30px"` 표기는 관찰 |

**안 돌려 본 것** — `devicePixelRatio` 가 2 이상인 화면에서 `0.5px` 테두리가 어떻게 그려지는지는 확인하지 못했다. 이 환경은 `devicePixelRatio = 1` 이고 headless 에서 비율을 바꿔 다시 재는 실험을 하지 않았다.

## 용어 풀이

- **지정값(specified value)** — 캐스케이드·상속·초기값을 거쳐 배정된 값.
- **계산값(computed value)** — 상대 단위·키워드를 절대화한 값. **상속되는 단위**다.
- **사용값(used value)** — 레이아웃을 돌려 `%`·`auto` 를 푼 값.
- **실제값(actual value)** — 장치 격자·반올림을 적용한 최종값.
- **해석값(resolved value)** — `getComputedStyle` 이 돌려주는 값. 속성마다 계산값/사용값으로 규정돼 있다.
- **레이아웃(layout·reflow)** — 상자의 위치·치수를 정하는 단계. ②와 ③의 경계.
- **`em`** — 그 요소의 `font-size` 계산값 기준. 단 `font-size` 자신에 쓰면 부모 기준이라 중첩에서 곱해진다.
- **`rem`** — 루트 요소의 `font-size` 계산값 기준.
- **`devicePixelRatio`** — CSS 픽셀 하나가 장치 픽셀 몇 개인가.
- **`clientWidth`** — content + padding. 테두리·스크롤바 제외. 정수.
- **`offsetWidth`** — content + padding + border. 정수 반올림. 변환 미적용.
- **`getBoundingClientRect()`** — 변환까지 적용된 실제 상자. 소수.
- **1/64px 격자** *(Chrome 구현 세부)* — 엔진이 길이를 저장하는 고정소수점 단위.
- **layout thrashing** — 읽기와 쓰기를 번갈아 해서 레이아웃이 반복해 도는 것.
