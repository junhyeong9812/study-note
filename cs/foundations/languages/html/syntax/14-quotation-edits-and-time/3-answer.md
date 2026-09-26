# html/syntax/14 — 인용·편집·시각: `blockquote`/`q`/`cite`·`ins`/`del`·`time` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스(`html13b-cdp.py`·`capture.sh`)는 [13번 주제의 3-answer.md](../13-phrasing-semantics/3-answer.md) `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **따옴표는 창 ⑦ 에만 있고, `datetime` 은 어느 창에서도 검사되지 않는다**(A2·A4).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 따옴표는 `innerText` 에도 `textContent` 에도 트리에도 없다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html13b-14-q.html 2>/dev/null | grep '^<p id='
<p id="ko">ko: <q>바깥 <q>안쪽 <q>셋째</q></q></q></p>
<p id="en" lang="en">en: <q>outer <q>inner</q></q></p>
<p id="fr" lang="fr">fr: <q>dehors <q>dedans</q></q></p>
<p id="ja" lang="ja">ja: <q>外 <q>内</q></q></p>
<p id="de" lang="de">de: <q>außen <q>innen</q></q></p>
<p id="없음" lang="">lang="": <q>바깥 <q>안쪽</q></q></p>
(exit 0)
```

```text
$ python3 html13b-cdp.py page html13b-14-q.html | sed -n '1,13p'
창 ③ — 따옴표는 글자로 남나
  #ko   innerText   = "ko: 바깥 안쪽 셋째"
        textContent = "ko: 바깥 안쪽 셋째"
  #en   innerText   = "en: outer inner"
        textContent = "en: outer inner"
  #fr   innerText   = "fr: dehors dedans"
        textContent = "fr: dehors dedans"
  #ja   innerText   = "ja: 外 内"
        textContent = "ja: 外 内"
  #de   innerText   = "de: außen innen"
        textContent = "de: außen innen"
  #없음   innerText   = "lang=\"\": 바깥 안쪽"
        textContent = "lang=\"\": 바깥 안쪽"
(exit 0)
```

```text
$ python3 html13b-cdp.py page html13b-14-q.html | sed -n '15,24p'
창 ② — 따옴표를 누가 만드나
  getComputedStyle(q, '::before').content = open-quote
  getComputedStyle(q, '::after').content  = close-quote
  #ko   quotes = auto
  #en   quotes = auto
  #fr   quotes = auto
  #ja   quotes = auto
  #de   quotes = auto
  #없음   quotes = auto
  자식 노드 = #text, Q
(exit 0)
```

**왜 그런가**

- ★★★ **`innerText` 에 따옴표가 없다.** 렌더된 글자를 읽는 창인데도 **CSS 생성 콘텐츠는 글자로 안 친다.**
- **트리에도 없다** — 파서는 `<q>` 를 그대로 두고 따옴표 노드를 안 만든다. 자식 노드는 `#text, Q` 뿐이다.
- **`::before` 의 계산값은 `open-quote`** 다 — 「여는 따옴표를 찍어라」라는 **지시**이지 글자가 아니다. 글자를 고르는 것은 `quotes` 이고, 그 계산값은 여섯 줄 다 **`auto`** 다.

### 2. 트리에는 글자로 있다 — `lang` 이 모양을 고른다

**출력**

```text
$ python3 html13b-cdp.py ax html13b-14-q.html
RootWebArea    이름='14 q 의 따옴표'
  paragraph      이름=''
    StaticText     이름='ko: '
    StaticText     이름='“'
    StaticText     이름='바깥 '
    StaticText     이름='‘'
    StaticText     이름='안쪽 '
    StaticText     이름='‘'
    StaticText     이름='셋째'
    StaticText     이름='’'
    StaticText     이름='’'
    StaticText     이름='”'
  paragraph      이름=''
    StaticText     이름='en: '
    StaticText     이름='“'
    StaticText     이름='outer '
    StaticText     이름='‘'
    StaticText     이름='inner'
    StaticText     이름='’'
    StaticText     이름='”'
  paragraph      이름=''
    StaticText     이름='fr: '
    StaticText     이름='«'
    StaticText     이름='dehors '
    StaticText     이름='«'
    StaticText     이름='dedans'
    StaticText     이름='»'
    StaticText     이름='»'
  paragraph      이름=''
    StaticText     이름='ja: '
    StaticText     이름='「'
    StaticText     이름='外 '
    StaticText     이름='『'
    StaticText     이름='内'
    StaticText     이름='』'
    StaticText     이름='」'
  paragraph      이름=''
    StaticText     이름='de: '
    StaticText     이름='„'
    StaticText     이름='außen '
    StaticText     이름='‚'
    StaticText     이름='innen'
    StaticText     이름='‘'
    StaticText     이름='“'
  paragraph      이름=''
    StaticText     이름='lang="": '
    StaticText     이름='“'
    StaticText     이름='바깥 '
    StaticText     이름='‘'
    StaticText     이름='안쪽'
    StaticText     이름='’'
    StaticText     이름='”'
(exit 0)
```

**왜 그런가**

- ★★★ **접근성 트리에는 따옴표가 `StaticText` 로 있다.** A1 의 세 창에 없던 것이 **렌더 결과를 읽는 창**에는 나온다.
- **`ko` `“ ”`·`‘ ’` / `fr` `« »`·`« »` / `ja` `「 」`·`『 』` / `de` `„ “`·`‚ ‘`.** `en`·`lang=""` 은 `ko` 와 같다.
- **`ko` 의 세 겹째는 `‘ ’` 의 되풀이**다 — 쌍이 두 단계뿐이면 마지막 단계를 계속 쓴다.
- ★★ **고르는 것은 `lang` 이다.** `quotes: auto` 가 「요소의 언어에 맞춰라」이고, **어느 언어에 어느 글자인지는 이 판(구현)의 표**다. HTML 명세 렌더링 절에는 그 표가 없다.
- ★ **`<q>` 노드는 이 트리에 안 보인다** — `id` 가 없는 `generic` 이라 무시된 노드로 빠졌다(A3 의 `id` 달린 `<q>` 는 남는다).

### 3. `.cite` 는 URL 로 풀리지만, 속성은 접근성 노드에 안 나온다

**출력**

```text
$ python3 html13b-cdp.py page html13b-14-cite.html | sed -n '1,10p'
cite 속성 — 속성값 · IDL 이 돌려주는 값 · 접근성 노드
  #bq  getAttribute = "notes/talk.html#p3"
        .cite        = "https://example.org/doc/notes/talk.html#p3"
        역할 = blockquote · 이름 = "" · 설명 = "" · 속성 = []
  #q   getAttribute = "https://example.com/a b"
        .cite        = "https://example.com/a%20b"
        역할 = generic · 이름 = "" · 설명 = "" · 속성 = []
  #del getAttribute = "log.html"
        .cite        = "https://example.org/doc/log.html"
        역할 = deletion · 이름 = "" · 설명 = "" · 속성 = []
(exit 0)
```

```text
$ python3 html13b-cdp.py page html13b-14-cite.html | sed -n '12,23p'
cite 요소 · ins/del — 계산 스타일과 역할
  #bq  display = block  font-style = normal text-decoration = none         margin-left = 40px 역할 = blockquote
  #ci  display = inline font-style = italic text-decoration = none         margin-left = 0px  역할 = generic
  #del display = inline font-style = normal text-decoration = line-through margin-left = 0px  역할 = deletion
  #ins display = inline font-style = normal text-decoration = underline    margin-left = 0px  역할 = insertion

ins/del 의 datetime
  #del .dateTime = "2026-09-01"
  #ins .dateTime = "2026-09-26T09:00+09:00"

창 ③ — 지운 글자도 글자인가
  innerText = "값이 1만 원2만 원 이 됐다."
(exit 0)
```

```text
$ python3 html13b-cdp.py ax html13b-14-cite.html
RootWebArea    이름='14 cite 속성과 cite 요소'
  blockquote     이름=''
    paragraph      이름=''
      StaticText     이름='블록 인용의 본문'
  paragraph      이름=''
    StaticText     이름='짧은 인용 '
    generic        이름=''
      StaticText     이름='“'
      StaticText     이름='q 의 본문'
      StaticText     이름='”'
    StaticText     이름=' 끝.'
  paragraph      이름=''
    generic        이름=''
      StaticText     이름='어린 왕자'
    StaticText     이름=' 에서 인용했다.'
  paragraph      이름=''
    StaticText     이름='값이 '
    deletion       이름=''
      StaticText     이름='1만 원'
    insertion      이름=''
      StaticText     이름='2만 원'
    StaticText     이름=' 이 됐다.'
(exit 0)
```

**왜 그런가**

- ★★ **`.cite` 는 `getAttribute` 와 다르다.** `<base>` 기준으로 **절대 URL** 이 되고 공백이 `%20` 이 된다 — 명세 IDL 이 **`ReflectURL`** 이다.
- ★★★ **접근성 노드에는 흔적이 없다** — 이름·설명 빈 문자열, 속성 `[]`. HTML-AAM 은 `cite` 속성을 「**ARIA 대응 없음**」(macOS `AXURL` 에만)으로 적는다. 그 플랫폼 층은 CDP 로 **못 본다**(못 잰 것).
- **`<cite>` 요소는 `italic` · 역할 `generic`** 이다. HTML-AAM 은 「대응 역할 없음」.
- **`1만 원` 이 `innerText` 에 있다** — `<del>` 은 **취소선과 `deletion` 역할**을 줄 뿐 글자를 빼지 않는다.
- **`<blockquote>` 는 `margin-left: 40px` · 역할 `blockquote`**, `<ins>` 는 밑줄 · **`insertion`** 이다.

### 4. 틀린 것도 그대로 — 갈린 칸 = 0 / 65, 콘솔 0줄

**출력**

```text
$ python3 html13b-cdp.py page html13b-14-time.html
 #   getAttribute              .dateTime                 역할  이름  설명  속성  display  innerText
 t1  "2026-09-26"              "2026-09-26"              time  ""  ""  []  inline  "오늘"
 t2  "2026-09"                 "2026-09"                 time  ""  ""  []  inline  "이번 달"
 t3  "09-26"                   "09-26"                   time  ""  ""  []  inline  "매년 이날"
 t4  "14:30"                   "14:30"                   time  ""  ""  []  inline  "오후 두 시 반"
 t5  "2026-09-26T14:30+09:00"  "2026-09-26T14:30+09:00"  time  ""  ""  []  inline  "오늘 오후"
 t6  "2026-W39"                "2026-W39"                time  ""  ""  []  inline  "39주"
 t7  "2026"                    "2026"                    time  ""  ""  []  inline  "올해"
 t8  "PT2H"                    "PT2H"                    time  ""  ""  []  inline  "두 시간"
 t9  "2026-02-30"              "2026-02-30"              time  ""  ""  []  inline  "없는 날"
 t10 "26/09/2026"              "26/09/2026"              time  ""  ""  []  inline  "슬래시"
 t11 "내일"                      "내일"                      time  ""  ""  []  inline  "내일"
 t12 ""                        ""                        time  ""  ""  []  inline  "빈 값"
 t13 null                      ""                        time  ""  ""  []  inline  "2026-09-26"
 t14 null                      ""                        time  ""  ""  []  inline  "어제"

유효한 것과 틀린 것이 갈리는 칸 — 역할·이름·설명·속성·display 다섯 칸을 t1 과 견준다
갈린 칸 = 0 / 65
(exit 0)
```

```text
$ echo "콘솔 줄 수 = $(google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --enable-logging=stderr --dump-dom html13b-14-time.html 2>&1 >/dev/null | grep -c ':CONSOLE:')"
콘솔 줄 수 = 0
(exit 0)
```

**왜 그런가**

- ★★★ **`.dateTime` 은 파싱하지 않는다.** `"2026-02-30"`·`"내일"` 을 글자 그대로 돌려준다. 명세 IDL 이 `[Reflect] DOMString dateTime` 이다.
- ★★ **`t13` 의 `.dateTime` 은 `""`** — 속성이 없기 때문이다. 명세의 「datetime 값」은 이때 **내용 글자**(`2026-09-26`)지만 **IDL 은 속성만 비춘다**(A7).
- ★★★ **갈린 칸은 0 / 65** — 역할(`time`)·이름·설명·속성·`display` 다섯 칸이 **열네 줄 전부 같다.** **콘솔도 0줄**이다.
- ★ **결론 — 「검증자가 없다」.** 브라우저는 `datetime` 을 **읽지도 검사하지도 않는다.**

### 5. 명세가 금하고, `lang` 이 바뀌어도 안 따라간다

- 명세 — 「인용 부호를 `q` 요소의 **바로 앞·뒤·안에 써서는 안 된다**(must not). **UA 가 렌더링에 넣는다**」.
- **손으로 쓴 따옴표는 글자라 `lang` 이 바뀌어도 그대로**다. 그리고 `<q>` 가 **따옴표를 또 붙여** 두 겹이 된다.
- **글자 따옴표를 직접 써야 하는 자리** — 따옴표가 **글자로 남아야** 할 때(A1 — 복사·`innerText`·메일 본문). 그때는 `<q>` 를 쓰지 않는다.

### 6. 0 / 65 는 「재 봤더니 같았다」, 요청은 「잴 것이 없다」, 플랫폼 속성은 「못 잰 것」

- **틀린 `datetime` 의 0 / 65 — 「재 봤더니 같았다」.** 창이 열렸고 물었고 답이 같았다. ★ 그 결과가 말하는 결론이 「**검증자가 없다**」다.
- **`cite` 의 요청 — 「잴 것이 없다」(제4의 상태).** `cite` 는 요청을 **일으키지 않는** 속성이라 창 ⑤ 로 잴 동작 자체가 없다.
- **`datetime` 의 플랫폼 속성 — 「못 잰 것」(제3의 상태).** HTML-AAM 은 IA2 `datetime:` · macOS `AXDateTimeValue` 로 넘기라고 적는다. **동작은 있을 수 있는데** CDP 트리에는 그 층이 없다.
- ★ **「어느 형식이 유효한가」는 실행으로 못 말한다.** 브라우저가 검사하지 않고, 이 환경에 **검증기가 없다.** 요약 (5) 의 형식 표는 **명세를 읽은 것**이다.

### 7. 다르다 — 「datetime 값」은 명세의 개념, `.dateTime` 은 속성의 거울

- 명세 — 「`time` 요소의 datetime 값은 **`datetime` 속성이 있으면 그 값, 없으면 요소의 자식 글자**다」.
- **`.dateTime` 은 그때 `""`** 이다. IDL 이 **`Reflect`** — **속성을 비출 뿐** 명세의 「datetime 값」 알고리즘을 돌리지 않는다.
- ★ **`.cite` 는 `ReflectURL`**(URL 로 푼다), **`.dateTime` 은 `Reflect`**(글자 그대로). 같은 「반영」이어도 **규칙이 다르다** — 규칙의 일반론은 웹 API 갈래의 **06번**이다.

### 8. 규칙은 명세, 따옴표 표는 구현, `<cite>` 의 `generic` 은 구현

- **`q::before { content: open-quote }` — 명세(HTML 렌더링 절)** 의 기대값이다.
- **`fr` → `«` — 구현**이다. `quotes: auto` 가 「언어에 맞게」까지를 말하고, 글자 표는 이 판의 것이다. **HTML 명세 렌더링 절에는 언어별 표가 없다**(렌더링 절 전문에서 `quotes` 를 찾아 확인했다).
- **`<cite>` 의 `generic` — 구현.** HTML-AAM 은 「대응 역할 없음」(계산 역할 `html-cite`)이라 적고, Chrome 이 `generic` 으로 채웠다.

### 9. 정본 경계

- **생성 콘텐츠의 상자** — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **13번**([의사 요소와 생성 콘텐츠](../../../css/syntax/13-pseudo-elements-and-generated-content/2-summary.md)).
- **반영의 일반 규칙** — 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **06번**([속성 대 성질](../../../../web-api/06-attribute-vs-property/2-summary.md)).
- **날짜를 실제로 파싱하는 자리** — 목록의 **23번 주제**(`<input>` 숫자·날짜).
- **`lang` 의 영향 전체** — [목록의 **20번 주제**](../20-lang-dir-and-bidi/)(`lang`·`dir`).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 보조 기술·검증기 없음.

**하네스** — [13번 주제](../13-phrasing-semantics/3-answer.md)의 `html13b-cdp.py`(`ax`·`page` 두 모드)와 `capture.sh` 를 그대로 쓴다. 이 주제는 **`page` 모드로 창 ②·③·⑦ 을 한 실행에** 묻고, **`ax` 모드로 트리 전체**를 찍는다.

**본문에 안 실린 실험 파일** — 없다. 요약 (1)\~(5) 가 소스를 전부 싣고 있다.\
★ 요약 (2) 의 「`id` 없는 `<q>` 는 트리에서 빠진다」는 **캡처 블록 둘**(`id` 없는 `<q>` 의 A2 · `id` 있는 `<q>` 의 A3)의 대조다. 탐색 중 **`cite` 속성 유무·`id` 유무를 따로 가른 판**을 한 번 찍었는데 `id` 만 갈랐다 — 캡처로 싣지 않았으므로 **본문 근거로는 두 블록만** 쓴다.

**demo 블록** — [2-summary.md](2-summary.md) 의 demo 파일을 **그대로** 접근성 트리로 찍었다(요약의 demo 절 아래 블록). 「바꿔 볼 것」의 `fr` 단언은 A2 의 `fr` 줄이다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`q` 여섯 줄**(창 ①·②·③) | 3 | 동작 방식 (1)·(2) · A1 |
| **같은 파일의 접근성 트리** | 3 | 동작 방식 (2) · A2 |
| **`cite`·`ins`/`del`·`blockquote`**(창 ②·③·⑦) | 3 | 동작 방식 (3)·(4) · A3 |
| **`time` 열네 형식 + 갈린 칸 집계 + 콘솔** | 3 | 동작 방식 (5) · A4 |
| **demo 의 접근성 트리** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `lang` 별 따옴표 글자 | `ko`·`en` `“‘` · `fr` `«` · `ja` `「『` · `de` `„‚` | 구현의 표다 |
| `innerText` 가 생성 콘텐츠를 뺀다 | 뺀다 | 관찰이다 |
| `id` 없는 `generic` 을 트리에서 빼는 것 | 뺀다 | 구현의 트리 가지치기다 |
| `<cite>` 의 역할 | `generic` | HTML-AAM 은 「대응 없음」 |
| 틀린 `datetime` 에 **경고가 없는 것** | 콘솔 0줄 | 판이 오르며 경고가 생길 수 있다 |

**안 돌려 본 것** — ① **Firefox·Safari 의 따옴표 표**(엔진이 없다). ② **CSS 로 `quotes` 를 직접 준 경우** — CSS 갈래 13번의 표면이다. ③ **`<blockquote>` 안의 `<footer>`·`<figcaption>` 출처 구조** — [목록의 **19번**](../19-figure-address-hr/)이다.

**못 잰 것** — ① **스크린리더가 따옴표를 읽는지·인용을 알려 주는지.** ② **`datetime` 이 유효한지** — 검증기가 없다. ③ **플랫폼 API 의 `datetime`·`AXURL`** — CDP 트리 밖이다. ④ **달력 앱·검색 엔진이 `time` 을 쓰는지.**

**부적용인 창** — **창 ④(`compatMode`) · 창 ⑤(요청 로그) · 창 ⑥(`renderBlockingStatus`).** ★ 창 ⑤ 는 `cite` 가 URL 인데도 부적용이다 — **요청을 안 일으키는 속성**이라 잴 동작이 없다.

## 용어 풀이

- **생성 콘텐츠** — CSS `content` 로 렌더 단계에서 만든 글자. DOM 노드가 없다.
- **`quotes: auto`** — 요소의 언어에 맞는 따옴표를 고르게 하는 값.
- **`ReflectURL` / `Reflect`** — 속성을 URL 로 풀어서 / 글자 그대로 스크립트에 비추는 IDL 규칙.
- **datetime 값** — `datetime` 속성, 없으면 내용 글자. `.dateTime` 과 같지 않다.
- **검증자(validator)** — 마크업이 명세 형식에 맞는지 검사하는 도구. 브라우저는 이 일을 안 한다.
- **제3의 상태(못 잰 것) · 제4의 상태(잴 것이 없다)** — 동작은 있는데 도구가 없는 것 / 동작 자체가 없는 것.
