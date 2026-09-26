# html/syntax/20 — `lang`·`dir` 과 양방향 텍스트: `dir=auto`·`bdi`/`bdo` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스(`html17b-cdp.py`·`capture.sh`)는 [17번 주제의 3-answer.md](../17-table-structure/3-answer.md) `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/dom.html#the-dir-attribute) 와 [UAX #9](https://www.unicode.org/reports/tr9/), [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ② 의 글자 x 좌표다**(A1·A7). ★★ **RTL 글자는 이 파일에 없다** — 출력은 코드 포인트 이름뿐이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `span` 이면 `3` 이 맨 왼쪽으로 가 `개` 와 갈라진다 — 1 / 5, `bdi` 로 감싸면 돌아온다

**출력**

```text
$ python3 html17b-cdp.py page html17b-20-bdi.html | sed -n '1,6p'
(가) span 에 히브리 이름 — 논리 순서대로 글자와 x(px)
  U+05E9@49  U+05DC@41  U+05D5@36  U+05DD@25  :@20  ␠@17  3@8  개@61
  화면 왼쪽→오른쪽 = 3 ␠ : U+05DD U+05D5 U+05DC U+05E9 개
(나) bdi 에 히브리 이름 — 논리 순서대로 글자와 x(px)
  U+05E9@32  U+05DC@24  U+05D5@19  U+05DD@8  :@44  ␠@48  3@52  개@61
  화면 왼쪽→오른쪽 = U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개
(exit 0)
```

```text
$ python3 html17b-cdp.py page html17b-20-bdi.html | sed -n '8,15p'
(다) 다섯 경우 — 시각 순서와 숫자의 자리
  span 에 히브리 이름             화면 왼쪽→오른쪽 = 3 ␠ : U+05DD U+05D5 U+05DC U+05E9 개       3 이 이름보다 오른쪽 = false
  bdi 에 히브리 이름              화면 왼쪽→오른쪽 = U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개       3 이 이름보다 오른쪽 = true
  span dir=auto 에 히브리 이름    화면 왼쪽→오른쪽 = U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개       3 이 이름보다 오른쪽 = true
  span 에 라틴 이름              화면 왼쪽→오른쪽 = K i m : ␠ 3 개                             3 이 이름보다 오른쪽 = true
  bdi 에 라틴 이름               화면 왼쪽→오른쪽 = K i m : ␠ 3 개                             3 이 이름보다 오른쪽 = true

3 이 이름 왼쪽으로 간 칸 = 1 / 5
(exit 0)
```

**왜 그런가**

- ★★★ **span — `3 ␠ : U+05DD U+05D5 U+05DC U+05E9 개`**, **bdi — `U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개`**. 이름 **안**은 두 경우 모두 오→왼으로 그려진다(쓴 순서의 첫 글자 U+05E9 가 이름의 오른쪽 끝). 갈린 것은 **이름 바깥의 `: 3`** 이다.
- ★★ **N = 1** — 「span 에 히브리 이름」만 `false`. `bdi`·`span dir=auto`·라틴 이름 둘은 `true`.
- ★★ **`3` 과 `개` 가 갈라졌다** — `3` 은 x 8, `개` 는 x 61. `3` 은 이름 무리(수준 1 이상)에 끼어 뒤집혔고 `개` 는 수준 0 에 남았다(A7).
- ★ **라틴 이름이면 `span` 도 멀쩡하다** — 이름이 RTL 일 때만 터진다.

### 2. rtl 8 / 15 · 갈림 0 / 15 — 명세 규칙과 Chrome 의 두 창이 전부 같다

**출력**

```text
$ python3 html17b-cdp.py page html17b-20-auto.html
dir=auto 인 요소마다 — 첫 강한 글자 규칙(스크립트 근사) · :dir(rtl) · 계산 direction · [dir=rtl]
  abc                         규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  히브리                         규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  아랍                          규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  123 + 히브리                   규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  !abc                        규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  abc + 히브리                   규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  히브리 + abc                   규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  공백 + 히브리                    규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  123 만                       규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  빈 문자열                       규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  bdi(히브리) + abc              규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  span dir=ltr(abc) + 히브리     규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  input value=히브리             규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  input value=abc             규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  textarea 히브리                규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false

  input value=abc 의 value 를 스크립트로 히브리로 바꾼 뒤   :dir(rtl) = true · direction = rtl

rtl 로 판정된 칸 = 8 / 15
규칙·:dir()·direction 이 갈린 칸 = 0 / 15
(exit 0)
```

**왜 그런가**

- ★★★ **갈린 칸 0 / 15** — 첫 강한 글자 규칙(스크립트 근사), `:dir(rtl)`, 계산 `direction` 이 **열다섯 칸 모두 같다.**
- ★★ **rtl 8 / 15** — 히브리·아랍·`123 + 히브리`·`히브리 + abc`·`공백 + 히브리`·`span dir=ltr(abc) + 히브리`·`input value=히브리`·`textarea 히브리`. 숫자·공백·기호는 **건너뛰고** 첫 **L·R·AL** 글자를 본다.
- ★★ **`bdi(히브리) + abc` → ltr**, **`span dir=ltr(abc) + 히브리` → rtl** — 명세가 `bdi` 와 `dir` 가진 요소의 **안을 건너뛰라고** 적는다. 앞의 것은 `a` 를, 뒤의 것은 히브리 글자를 첫 강한 글자로 만난다.
- ★ **`[dir=rtl]` 은 전부 `false`** — 속성 값이 `auto` 다.
- ★ **값을 바꾸면 `:dir(rtl)` 이 `true` 로** — 입력 요소의 auto 방향성은 **값**을 본다.

### 3. 갈린 요소 1 / 3 — `#자식` 은 방향을 물려받았지만 속성이 없다

**출력**

```text
$ python3 html17b-cdp.py page html17b-20-sel.html | sed -n '1,5p'
(가) 방향 — 요소 × 선택자
  #부모      :dir(rtl) = true   [dir=rtl] = true   [dir=rtl] * = false  :dir(ltr) = false direction = rtl
  #자식      :dir(rtl) = true   [dir=rtl] = false  [dir=rtl] * = true   :dir(ltr) = false direction = rtl
  #자식ltr   :dir(rtl) = false  [dir=rtl] = false  [dir=rtl] * = true   :dir(ltr) = true  direction = ltr
  :dir(rtl) 와 [dir=rtl] 가 갈린 요소 = 1 / 3
(exit 0)
```

**왜 그런가**

- ★★★ **`#자식` — `:dir(rtl)` `true`, `[dir=rtl]` `false`.** `:dir()` 은 **판정된 방향**, `[dir=rtl]` 은 **자기 속성**을 본다. 방향은 부모에게서 물려받는다.
- ★★ **`[dir=rtl] *` 는 `#자식ltr` 에도 `true`** — 안쪽에서 `dir="ltr"` 로 되돌렸는데도 자손 결합은 **조상의 속성**만 본다. `#자식ltr` 의 `:dir(ltr)` 은 `true` 다.
- **N = 1.**

### 4. `:lang()` 은 물려받고 `[lang]` 은 안 물려받는다 — `bdo dir=rtl` 만 `c b a`

**출력**

```text
$ python3 html17b-cdp.py page html17b-20-sel.html | sed -n '7,11p'
(나) 언어 — 요소 × 선택자
  #영부모     :lang(en) = true   [lang=en] = false  [lang|=en] = true   :lang(ko) = false lang 속성 = "en-US"
  #영자식     :lang(en) = true   [lang=en] = false  [lang|=en] = false  :lang(ko) = false lang 속성 = null
  #빈lang   :lang(en) = false  [lang=en] = false  [lang|=en] = false  :lang(ko) = false lang 속성 = ""
  #대문자     :lang(en) = true   [lang=en] = true   [lang|=en] = true   :lang(ko) = false lang 속성 = "EN"
(exit 0)
```

```text
$ python3 html17b-cdp.py page html17b-20-sel.html | sed -n '13,17p'
(다) 글자 순서 — 화면 왼쪽→오른쪽(창 ②) · 계산 unicode-bidi · direction
  <bdo dir=rtl>abc    화면 = c b a   unicode-bidi = isolate-override  direction = rtl
  <span dir=rtl>abc   화면 = a b c   unicode-bidi = isolate           direction = rtl
  <bdi>abc            화면 = a b c   unicode-bidi = isolate           direction = ltr
  <bdo>abc            화면 = a b c   unicode-bidi = isolate-override  direction = ltr
(exit 0)
```

**왜 그런가**

- ★★ **`#영자식` — `:lang(en)` `true`, `[lang=en]`·`[lang|=en]` `false`.** 언어는 물려받고 `:lang()` 은 그것을 본다. 속성 선택자는 자기 속성만 본다.
- ★ **`#영부모`(`en-US`) — `[lang=en]` `false`, `[lang|=en]` `true`.** `|=` 은 「`en` 이거나 `en-` 으로 시작」이다.
- ★ **`#대문자`(`EN`) — `[lang=en]` `true`.** HTML 명세가 `lang` 을 **값을 대소문자 무시로 비교하는 속성 목록**에 넣었다.
- ★★ **`#빈lang` — 셋 다 `false`.** `lang=""` 은 「주 언어를 모른다」라 부모의 `en-US` 를 물려받지 않는다.
- ★★★ **`<bdo dir=rtl>abc` 만 `c b a`**(`isolate-override`). `<span dir=rtl>abc` 는 `a b c`(`isolate`) — **`dir=rtl` 은 L 글자를 뒤집지 않는다.** `<bdi>` 는 `isolate`·ltr, `dir` 없는 `<bdo>` 는 `isolate-override`·ltr(부모 방향)이라 순서 그대로다.

### 5. 사전이 없으면 0 / 6, 사전을 넣으면 3 / 6 — 글꼴은 JP·SC·TC·KR

**출력**

```text
$ python3 html17b-cdp.py page html17b-20-lang.html
(가) hyphens: auto · 폭 90px — 낱말 × lang 의 줄 수(span.getClientRects().length)
  영어 낱말   lang=없음 2  ·  lang=en 2  ·  lang=de 2  ·  lang=ko 2
  독일어 낱말  lang=없음 1  ·  lang=en 1  ·  lang=de 1  ·  lang=ko 1
  lang 없음과 줄 수가 갈린 칸 = 0 / 6

(나) 같은 한자 두 글자 × lang — 실제로 그린 플랫폼 글꼴(CSS.getPlatformFontsForNode)
  lang=없음    ["Noto Sans CJK KR"]
  lang=ja    ["Noto Sans CJK JP"]
  lang=zh-CN ["Noto Sans CJK SC"]
  lang=zh-TW ["Noto Sans CJK TC"]
  lang=ko    ["Noto Sans CJK KR"]
(exit 0)
```

```text
$ ls hyphen-data
120.0.6050.0
(exit 0)
```

```text
$ python3 html17b-cdp.py page --hyphen html17b-20-lang.html
(가) hyphens: auto · 폭 90px — 낱말 × lang 의 줄 수(span.getClientRects().length)
  영어 낱말   lang=없음 2  ·  lang=en 8  ·  lang=de 6  ·  lang=ko 2
  독일어 낱말  lang=없음 1  ·  lang=en 1  ·  lang=de 5  ·  lang=ko 1
  lang 없음과 줄 수가 갈린 칸 = 3 / 6

(나) 같은 한자 두 글자 × lang — 실제로 그린 플랫폼 글꼴(CSS.getPlatformFontsForNode)
  lang=없음    ["Noto Sans CJK KR"]
  lang=ja    ["Noto Sans CJK JP"]
  lang=zh-CN ["Noto Sans CJK SC"]
  lang=zh-TW ["Noto Sans CJK TC"]
  lang=ko    ["Noto Sans CJK KR"]
(exit 0)
```

**왜 그런가**

- ★★★ **새 프로필 — 전부 영어 2줄·독일어 1줄, 갈린 칸 0 / 6.** `hyphens: auto` 가 켜져 있어도 **사전이 없으면 안 끊는다.**
- ★★★ **사전을 넣은 프로필 — 영어 낱말이 `en` 8줄·`de` 6줄, 독일어 복합어가 `de` 5줄, 갈린 칸 3 / 6.** `lang` 없음·`ko` 는 사전이 있어도 2줄·1줄이다 — **그 언어의 사전**을 쓰기 때문이다.
- ★★ **한자 글꼴 — `ja` JP · `zh-CN` SC · `zh-TW` TC · `ko`·없음 KR.** `lang` 이 같은 코드 포인트의 **지역별 모양**을 골랐다. `lang` 없음이 KR 인 것은 이 머신의 로캘을 따른 것으로 보인다(흔들리는 칸).
- ★ 사전 판은 `120.0.6050.0` — 이 머신의 Chrome 기본 프로필이 구성 요소 갱신으로 받아 둔 것을 스크래치패드에 복사했다.

### 6. `textDirection` 은 선택자와 같고, `#빈lang` 의 `language` 는 `en-US` 다

**출력**

```text
$ python3 html17b-cdp.py int html17b-20-sel.html htmlTag,language,textDirection
rootWebArea             htmlTag=#document language=ko textDirection=ltr
      genericContainer #부모      htmlTag=div language=ko textDirection=rtl
        paragraph      #자식      htmlTag=p language=ko textDirection=rtl
        paragraph      #자식ltr   htmlTag=p language=ko textDirection=ltr
      genericContainer #영부모     htmlTag=div language=en-US textDirection=ltr
        paragraph      #영자식     htmlTag=p language=en-US textDirection=ltr
        paragraph      #빈lang   htmlTag=p language=en-US textDirection=ltr
      paragraph      #대문자     htmlTag=p language=EN textDirection=ltr
      paragraph               htmlTag=p language=ko textDirection=ltr
        genericContainer #bdo     htmlTag=bdo language=ko textDirection=rtl
        genericContainer #spanrtl htmlTag=span language=ko textDirection=rtl
        genericContainer #bdi     htmlTag=bdi language=ko textDirection=ltr
        genericContainer #bdo맨    htmlTag=bdo language=ko textDirection=ltr
(exit 0)
```

**왜 그런가**

- ★★ **`textDirection`** — `#부모`·`#자식` rtl · `#자식ltr` ltr · `#bdo`·`#spanrtl` rtl · `#bdi`·`#bdo맨` ltr. (3)·(4) 의 `:dir()`·`direction` 과 **같다.**
- ★★★ **`#빈lang` 의 `language = en-US`** — 부모 값을 물려 적었다. 명세는 `lang=""` 을 「주 언어를 모른다」로 적고, 같은 브라우저의 `:lang(en)` 은 `false` 를 줬다(A4). **트리만 다르게 읽었다.**
- ★ **`#대문자` 는 `language = EN`** — 쓴 그대로다.

### 7. W6·W7·N1 이 `: 3` 을 이름 쪽(R)으로 붙이고, I1·L2 가 그 덩어리를 뒤집는다 — 좌표로만 보인다

- **따라가기** — 글자 클래스 `R R R R · CS · WS · EN · L`.
  - **W6** — 숫자 사이가 아닌 `:`(CS)는 중립 **ON** 이 된다.
  - **W7** — `3`(EN) 앞의 첫 강한 글자는 **R**(이름) — L 이 아니므로 EN 그대로다.
  - **N1** — `R … (ON WS) … EN` 사이의 중립은 **R** 이 된다(숫자는 R 처럼 친다).
  - **I1** — 문단 수준 0(짝수)에서 R 은 **1**, EN 은 **2**. `개`(L)는 **0**.
  - **L2** — 수준 1 이상 덩어리 `이름 : ␠ 3` 을 뒤집는다 → 화면 `3 ␠ : (이름 거꾸로)`, 그 오른쪽에 `개`.
  - ★ **`3` 은 수준 2** 다.
- **`bdi` 로 감싸면** — 격리된 이름은 바깥 계산에서 **중립 한 글자**(격리 시작·끝 표시)로 보인다. `3` 의 W7 은 이름을 건너 **문단 시작(sos, ltr)** 까지 가서 **L** 을 만나 `3` 이 **L** 이 된다. `: ␠` 는 L 사이 중립이라 L. 전부 수준 0 — **쓴 순서 그대로** 선다.
- ★★★ **DOM·`textContent`·`innerText` 는 저장된(논리) 순서를 돌려준다** — 양방향 알고리즘은 **그리는 단계**에서 돈다. 그래서 **글자마다 `Range.getClientRects()` 의 x 를 찍어** 화면 순서를 복원했다 — **제5의 상태**(같은 질문을 다른 창으로 물었다)다.

### 8. 순서는 UAX #9 의 보장, px 는 관찰 — 불일치는 `lang=""` 하나이고 그것이 브라우저 안에서 갈렸다

- ★★ **화면 순서** — UAX #9 가 정하는 결과다. 이 판은 그것을 **좌표로 관찰**했다. **x 값(px)은 글꼴에 매이는 관찰**이고, **「어느 글자가 왼쪽인가」는 알고리즘이 보장하는 순서의 관찰**이다 — 근거는 뒤쪽이다.
- ★★★ **명세 ↔ Chrome 불일치 — `lang=""` 을 트리가 부모 언어(`en-US`)로 적은 것**(A6). 같은 브라우저의 CSS(`:lang`)는 명세대로 「모르는 언어」로 읽었다 — **한 브라우저 안에서 갈렸다.** `dir=auto`·`:dir()`·`bdo`/`bdi` 는 명세와 갈린 칸이 없었다.
- ★★ **하이픈은 환경에 매인다** — 명세(CSS Text)는 「콘텐츠 언어를 알 때 사전으로」라고만 하고, **사전을 가지고 있나는 구현·설치 상태**다. 같은 판·같은 파일이 프로필에 따라 0 / 6 과 3 / 6 으로 갈렸다.

### 9. 음성은 「못 잰 것」 — 좌표 창은 여러 줄·합자를 못 본다

- **못 쓴다.** 이 머신에 음성 합성기·스크린리더가 없다. **존재하는 동작인데 잴 도구가 없다 — 제3의 상태.** 트리에 `language` 가 적히는 것(A6)까지가 관찰이다.
- **못 보는 경우** — ① **줄바꿈이 낀 문장** — 줄마다 x 가 다시 시작해 x 만으로는 순서가 안 선다. ② **합자·결합 글자** — 두 글자가 한 모양이면 x 가 겹친다. 이 판의 문장은 전부 **한 줄**이고 합자가 없는 글자만 썼다.

### 10. 정본 경계

- **`lang` 이 고른 따옴표** — [14번 주제](../14-quotation-edits-and-time/2-summary.md)의 **(2)**.
- **CSS `direction` 과 축** — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **32번**. **`hyphens`** — 같은 목록의 **51번**. ★ 51번 (5) 가 「사전이 없어 `lang` 이 먹는지 못 쟀다」로 남긴 것을, 이 주제가 **사전을 넣은 판과 뺀 판을 대조**해 「원인은 사전 부재, `lang` 은 먹는다」로 이었다(51번 문서는 고치지 않았다).
- **`foundations/data-representation/`** — README 하나에 **유니코드 코드 포인트·코드 유닛(§3.2)** 까지 있고 **양방향 알고리즘은 없다.** 그래서 이 주제는 UAX #9 를 명세 링크와 규칙 이름으로만 접지했다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.**\
★★ **보조 기술·음성 합성기 없음.**

**하네스** — [17번 주제](../17-table-structure/3-answer.md)의 `html17b-cdp.py` 를 그대로 쓴다. 이 주제가 더 쓴 것 — ① **`window.__글꼴`** — CDP `CSS.getPlatformFontsForNode` 로 요소를 **실제로 그린 글꼴**을 받는다. ② **`--hyphen`** — 새 프로필에 **하이픈 사전(`hyphen-data`)을 먼저 넣고** 띄운다. 새 프로필의 사전 칸은 비어 있고, Chrome 이 **구성 요소 갱신으로 나중에** 받는다 — 그 시점은 하네스가 통제하지 못하므로 **넣은 판과 안 넣은 판을 따로** 찍었다.\
★★ **RTL 글자를 원고에 들이지 않는 장치** — 소스는 `String.fromCodePoint` 와 `&#x5E9;` 로 글자를 만들고, 페이지 스크립트는 글자를 찍을 때 **U+0590\~U+08FF 를 `U+XXXX` 로 바꾸거나**((1)) **한글 이름표만** 찍는다((2)). **`ax` 모드와 `--dump-dom` 은 이 주제에 쓰지 않았다** — 트리 이름과 DOM 직렬화에 글자가 그대로 나오기 때문이다(내부 덤프는 `id`·`language`·`textDirection` 만 고른 `int` 모드라 안전하다). 제출 전 **RTL 글자(U+0590\~U+08FF)·양방향 제어(U+200E/F · U+202A\~202E · U+2066\~2069) 0개**를 전수 스캔으로 확인했다.

**demo 블록** — [2-summary.md](2-summary.md) 의 `demo` 를 **같은 마크업 + 측정 프로브**로 던졌다. 출력은 `3` 과 이름 상자의 x 만 찍는다.

```html
<!-- html17b-20-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 20 검증</title>
<body>
<p><span>&#x5E9;&#x5DC;&#x5D5;&#x5DD;</span>: 3개</p>
<p><bdi>&#x5E9;&#x5DC;&#x5D5;&#x5DD;</bdi>: 3개</p>
<script>
const O = ["창 폭 = " + window.innerWidth];
for (const p of document.querySelectorAll("p")) {
  const 감싼 = p.firstElementChild, r = document.createRange();
  const t = p.lastChild; r.setStart(t, t.data.indexOf("3")); r.setEnd(t, t.data.indexOf("3") + 1);
  const 숫자x = r.getClientRects()[0].left, 이름 = 감싼.getBoundingClientRect();
  O.push("<" + 감싼.localName + ">  이름 상자 x = " + 이름.left.toFixed(0) + "~" + 이름.right.toFixed(0) + " · 3 의 x = " + 숫자x.toFixed(0)
    + " · 3 이 이름보다 오른쪽 = " + (숫자x > 이름.right - 1));
}
document.body.appendChild(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-20-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
창 폭 = 1000
<span>  이름 상자 x = 25~61 · 3 의 x = 8 · 3 이 이름보다 오른쪽 = false
<bdi>  이름 상자 x = 8~44 · 3 의 x = 52 · 3 이 이름보다 오른쪽 = true
(exit 0)
```

- **첫 줄(`span`)은 `3` 이 이름 상자 왼쪽(8 < 25), 둘째 줄(`bdi`)은 오른쪽(52 > 44).** 「바꿔 볼 것」(`span dir=auto`)은 (1) 의 셋째 경우가 같은 문장으로 던진 것이다.
- ★ px 는 머신 사이에서 흔들린다. 근거는 **어느 쪽인가**다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`bdi` 좌표 격자**(다섯 벌) | 3 | 동작 방식 (1) · A1·A7 |
| **`dir=auto` 격자**(열다섯) | 3 | 동작 방식 (2) · A2 |
| **선택자·글자 순서·내부 덤프** | 3 | 동작 방식 (3)\~(6) · A3·A4·A6 |
| **하이픈·글꼴**(사전 없음 / 있음) | 3 / 3 | 동작 방식 (7) · A5 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 트리의 `lang=""` | **부모 언어**(`en-US`) | 명세·CSS 와 갈린다 — 고쳐질 수 있다 |
| 하이픈 사전 | 새 프로필 **없음** · 넣으면 `en`·`de` 동작 | 구성 요소 갱신에 매인다 |
| 한자 글꼴 | JP·SC·TC·KR | 설치 글꼴·로캘에 매인다 |
| 글자 x | 문서의 px | 글꼴에 매인다 — 순서만 근거 |

**안 돌려 본 것** — ① **Firefox·Safari 의 양방향·하이픈**(엔진이 없다). ② **여러 줄 양방향 문장** — 좌표 창이 못 본다(A9). ③ **`dirname` 속성·`unicode-bidi: plaintext`** — 요약 「더 들어가면」.

**못 잰 것**(「안 돌려 본 것」과 다르다) — ① **`lang` 에 따른 음성 합성**(A9). ② **스크린리더가 RTL 이름을 읽는 순서**.

**부적용인 창** — **창 ③**(`innerText`·`textContent` 는 둘 다 논리 순서 — 그래서 창 ② 좌표로 바꿨다) · **창 ④·⑤·⑥**(잴 것이 없다). ★ **창 ① 과 CDP `ax` 모드는 부적용이 아니라 원고 규칙 때문에 고르지 않은 창**이다.

## 용어 풀이

- **논리 순서 / 시각 순서** — 저장된 순서 / 화면 순서.
- **Bidi 클래스** — 글자의 방향 성질(L·R·AL·EN·CS·WS·ON …).
- **수준(embedding level)** — UAX #9 가 글자마다 매기는 숫자. 홀수는 오→왼. L2 가 높은 수준부터 뒤집는다.
- **격리 / 재정의** — `bdi`·`[dir]` 의 `isolate` / `bdo` 의 `isolate-override`.
- **하이픈 사전** — 언어별 끊는 자리 자료. 없으면 `hyphens: auto` 가 아무것도 안 한다.
- **제5의 상태** — 같은 질문을 다른 창으로 물은 것. 이 주제는 글자 순서를 좌표로 물었다.
