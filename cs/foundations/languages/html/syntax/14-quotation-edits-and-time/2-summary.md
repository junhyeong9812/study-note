# html/syntax/14 — 인용·편집·시각: `blockquote`/`q`/`cite`·`ins`/`del`·`time` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The `q` element」](https://html.spec.whatwg.org/multipage/text-level-semantics.html#the-q-element)·[「The `cite` element」](https://html.spec.whatwg.org/multipage/text-level-semantics.html#the-cite-element)·[「The `time` element」](https://html.spec.whatwg.org/multipage/text-level-semantics.html#the-time-element)·[「Edits」](https://html.spec.whatwg.org/multipage/edits.html)·[「The `blockquote` element」](https://html.spec.whatwg.org/multipage/grouping-content.html#the-blockquote-element) 절, [렌더링 절](https://html.spec.whatwg.org/multipage/rendering.html)의 `q::before`/`q::after` 규칙, 그리고 [HTML-AAM](https://w3c.github.io/html-aam/). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 블록마다 던진 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다. 하네스는 [13번 주제의 3-answer.md](../13-phrasing-semantics/3-answer.md) `## 실행 검증` 절에 있다(이 배치가 공유한다).\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 이 주제의 요소들은 전부 오래된 표면이다. ★ 다만 **`quotes: auto`**(언어에 맞춰 따옴표를 고르는 CSS 값)는 CSS 쪽의 비교적 새 표면이고, **HTML 명세 렌더링 절에는 이제 언어별 따옴표 표가 없다**(렌더링 절 전문에서 `quotes` 를 찾아 확인했다 — `q::before { content: open-quote }` 두 줄만 있다).
> **선행** — [13번 주제](../13-phrasing-semantics/2-summary.md)(같은 구절 시맨틱 묶음 · 창 ② × 창 ⑦ 대조).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ③ 대 창 ⑦ 이다 — `q` 의 따옴표는 `innerText` 에 없고 접근성 트리에는 있다.** 그리고 **`time` 에서는 창 ② 가 본체다** — `dateTime` 이 **아무것도 해석하지 않고** 속성 글자를 돌려준다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |
| **흔들린다** | CDP 포트·프로필 경로 | 실행마다 무작위 — **출력에는 안 들어간다** |
| **안 흔들린다** | 따옴표 글자(`“ ‘ « 「 „`)와 그 순서 | 같은 판이면 결정적이다 |
| **안 흔들린다** | `.cite`·`.dateTime` 이 돌려주는 글자 | IDL 반영이 명세에 있다 |
| **안 흔들린다** | 격자의 「갈린 칸 N / M」 | 스크립트가 센다 |
| **안 흔들린다** | `.cite` 의 절대 URL | ★ **`<base href="https://example.org/doc/">` 로 기준을 고정**했다 — 없으면 스크래치패드의 `file://` 경로가 박힌다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **③ `innerText` 대 `textContent`** | ★ **쓴다 — `q` 의 본체** | 따옴표가 **글자로 남나** — 둘 다 **안 남는다**((1)) |
| **⑦ 접근성 트리** | ★ **쓴다 — `q` 의 본체** | 따옴표가 **보조 기술에 넘어가나** — **넘어간다**((2)) |
| **② 프로브**(IDL·계산 스타일) | ★ **쓴다 — `time`·`cite` 의 본체** | 속성이 **해석되나** — `dateTime` 은 **안 한다**, `.cite` 는 **URL 로 푼다**((3)·(5)) |
| **① `--dump-dom`** | 쓴다 — 한 번 | 따옴표가 **트리에 있나** — **없다**((1)) |
| **④ `compatMode`** | **부적용** | 문서 모드와 무관하다 — **잴 것이 없다** |
| **⑤ 서버 요청 로그** | **부적용** | ★ `cite` 속성은 URL 인데 **요청을 일으키지 않는다** — 요청을 만드는 속성이 없으니 **잴 것이 없다**([16번 주제](../16-links/2-summary.md)의 `href` 와 다르다) |
| **⑥ `renderBlockingStatus`** | **부적용** | 렌더를 막는 자원이 없다 |

- ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「따옴표가 있나」를 창 ①·③ 에 물으면 「**없다**」, 창 ⑦ 에 물으면 「**있다**」다. **셋 다 맞는 답**이다 — 따옴표는 **CSS 가 만든 생성 콘텐츠**라 트리에도 글자에도 없고, **렌더된 결과를 읽는 접근성 트리**에만 있다.
- ★★ **`time` 은 제4의 상태와 헷갈리기 쉽다.** 틀린 `datetime` 을 넣고 다섯 창을 다 물었더니 **한 칸도 안 갈렸다**((4)). 이것은 「**잴 것이 없다**」가 아니다 — 쟀고, **같았다.** 결론은 「**검증자가 없다**」이다. 셋을 갈라 둔다:

| 상태 | 뜻 | 이 주제의 자리 |
|---|---|---|
| **재 봤더니 같았다** | 창이 열렸고 물었고 답이 같았다 | 틀린 `datetime` 의 역할·이름·설명·속성·`display` — **0 / 65** |
| **잴 것이 없다**(제4의 상태) | 그 동작 자체가 없다 | `cite` 속성의 **요청**(창 ⑤) — 요청을 안 일으킨다 |
| **못 잰 것**(제3의 상태) | 동작은 있는데 도구가 없다 | HTML-AAM 이 적는 **`datetime` 의 플랫폼 속성**(`AXDateTimeValue` 등) — CDP 트리에 안 나온다 |

## 한눈에 — 쉽게 말하면

**★ `q` 의 따옴표는 글자가 아니라 「인쇄소가 찍어 주는 장식」이다. `time` 의 `datetime` 은 「기계용 쪽지」인데, 그 쪽지를 검사하는 사람이 없다.**

책 편집부에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 원고에 「**여기부터 인용**」이라고만 표시해 두면 인쇄소가 **그 나라 따옴표**를 찍어 준다 | **`<q>`** — 따옴표는 **CSS 생성 콘텐츠**(`q::before { content: open-quote }`) |
| 원고 파일을 복사해 가면 **따옴표가 안 따라온다** | **`innerText`·`textContent`** 에 따옴표가 없다 |
| 낭독자는 **인쇄된 책**을 읽으므로 따옴표를 본다 | **접근성 트리**에 따옴표 글자가 있다 |
| 인용 옆에 적은 **「출처 파일 주소」 메모** | **`cite` 속성** — 화면에 안 나오고 **요청도 안 한다** |
| 참고 문헌 목록의 **책 제목** | **`<cite>` 요소** — 사람 이름이 아니라 **저작물 제목** |
| 교정지의 **빨간 줄**과 **끼워 넣은 글** | **`<del>`·`<ins>`** — 역할 `deletion`·`insertion` |
| 원고 귀퉁이의 **기계용 날짜 쪽지** | **`<time datetime>`** — 브라우저가 **읽지도 검사하지도 않는다** |

- **따옴표는 세 창 중 한 창에만 있다** — 창 ①(트리)·창 ③(글자)에는 없고 창 ⑦(접근성 트리)에만 있다((1)·(2)).
- **따옴표 모양은 `lang` 이 고른다** — `ko`·`en` 은 `“‘`, `fr` 은 `«`, `ja` 는 `「『`, `de` 는 `„‚`((2)).
- **`datetime` 은 틀려도 아무도 모른다** — 열네 형식을 넣어 **갈린 칸 0 / 65**((4)).

```text
  같은 <q> 가 네 창에서

  소스        <q>바깥 <q>안쪽</q></q>
                    |
  창 ①  트리      <q>바깥 <q>안쪽</q></q>          따옴표 없음
  창 ③  글자      "바깥 안쪽"                       따옴표 없음
  창 ②  CSS       ::before content = open-quote    '따옴표를 찍어라' 라는 지시만
  창 ⑦  접근성    “ 바깥 ‘ 안쪽 ’ ”                 ★ 여기에만 글자로 있다

  따옴표는 트리에서 생기지 않고, 렌더 단계에서 CSS 가 만든다.
```

실무에서 이게 터지는 자리는 **`<q>` 안에 따옴표를 손으로 또 쓰는 것**이다 — 화면에 **따옴표가 두 겹**이 된다.\
명세가 그것을 금한다 — 「인용 부호를 `q` 의 바로 앞·뒤·안에 쓰지 말라 — **UA 가 렌더링에 넣는다**」.\
그리고 반대 방향의 사고도 있다 — **`innerText` 로 복사한 인용문에는 따옴표가 없다.** 글자로 따옴표가 필요하면 `<q>` 가 아니라 **글자를 직접** 써야 한다.

> **생성 콘텐츠(generated content)** — CSS 의 `content` 로 **렌더 단계에서 만들어진 글자**. DOM 에는 노드가 없다.\
> 예: `q::before { content: open-quote }` 가 찍는 `“`.

> **IDL 반영(reflect)** — 요소의 속성(`datetime`)을 스크립트 프로퍼티(`.dateTime`)로 **그대로 비춰 주는 것.**\
> 예: `datetime="내일"` 이면 `.dateTime` 도 `"내일"` 이다 — **해석하지 않는다.**

## 이 주제가 답하려는 질문

1. **`q` 의 따옴표는 어디에 있나** — 트리인가, 글자인가, 렌더인가. 그 모양은 무엇이 고르나.
2. **`cite` 속성과 `cite` 요소는 각각 무엇을 하나** — 화면·트리·요청 어디에 흔적이 남나.
3. **`time datetime` 에 틀린 값을 넣으면 무엇이 달라지나** — 달라지는 것이 없다면 그 결론은 무엇인가.

## 동작 방식

### (1) 창 ① + 창 ③ — 따옴표는 트리에도 글자에도 없다

**언제 쓰나** — 「`q` 가 따옴표를 붙인다」가 **어디서** 일어나는지 묻는 자리.

`<q>` 를 세 겹(`ko`)·두 겹(`en`·`fr`·`ja`·`de`·`lang=""`)으로 겹쳤다.

```html
<!-- html13b-14-q.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>14 q 의 따옴표</title>
</head>
<body>
<p id="ko">ko: <q>바깥 <q>안쪽 <q>셋째</q></q></q></p>
<p id="en" lang="en">en: <q>outer <q>inner</q></q></p>
<p id="fr" lang="fr">fr: <q>dehors <q>dedans</q></q></p>
<p id="ja" lang="ja">ja: <q>外 <q>内</q></q></p>
<p id="de" lang="de">de: <q>außen <q>innen</q></q></p>
<p id="없음" lang="">lang="": <q>바깥 <q>안쪽</q></q></p>
<script>
window.__대상 = [];
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("창 ③ — 따옴표는 글자로 남나");
  for (const id of ["ko", "en", "fr", "ja", "de", "없음"]) {
    const p = document.getElementById(id);
    O.push("  #" + id.padEnd(4) + " innerText   = " + J(p.innerText));
    O.push("  " + " ".repeat(6) + "textContent = " + J(p.textContent));
  }
  O.push("");
  O.push("창 ② — 따옴표를 누가 만드나");
  const q = document.querySelector("#ko q");
  O.push("  getComputedStyle(q, '::before').content = " + getComputedStyle(q, "::before").content);
  O.push("  getComputedStyle(q, '::after').content  = " + getComputedStyle(q, "::after").content);
  for (const id of ["ko", "en", "fr", "ja", "de", "없음"])
    O.push("  #" + id.padEnd(4) + " quotes = " + getComputedStyle(document.querySelector("#" + id + " q")).quotes);
  O.push("  자식 노드 = " + [...q.childNodes].map(n => n.nodeName).join(", "));
  return O.join("\n");
};
</script>
</body>
</html>
```

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

- ★★★ **`innerText` 에 따옴표가 없다.** [04번 주제](../04-whitespace-and-character-references/2-summary.md)의 창 ③ 은 「렌더된 글자」를 읽는 창인데도 **따옴표를 안 넣었다.** `innerText` 는 **CSS 생성 콘텐츠를 글자로 치지 않는다.**
- **`textContent` 에도 없다** — 이쪽은 원래 트리의 글자만 읽는다.
- **창 ①(트리)에도 없다** — 파서는 `<q>` 를 **그대로** 둔다. 따옴표 노드를 끼워 넣지 않는다.

### (2) 창 ② + 창 ⑦ — 따옴표를 만드는 것은 CSS, 읽어 가는 것은 접근성 트리

**언제 쓰나** — (1) 의 「없다」가 **정말 없는 것인지, 안 보이는 것인지** 가르는 자리.

(1) 과 같은 실행의 뒷부분이다.

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

같은 파일을 접근성 트리로 찍었다.

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

```text
  lang 이 고른 따옴표 (이 판의 관찰)

  lang      바깥       안쪽       셋째
  ko        “ ”        ‘ ’        ‘ ’     <- 세 겹째는 두 겹째 것을 되풀이한다
  en        “ ”        ‘ ’
  fr        « »        « »                <- 안쪽도 같은 모양
  ja        「 」       『 』
  de        „ “        ‚ ‘                <- 여는 쪽이 아래에 붙는다
  ""        “ ”        ‘ ’

  계산값은 여섯 줄 전부 quotes = auto 다. 글자를 고르는 것은 lang 이다.
```

- ★★★ **접근성 트리에는 따옴표가 글자(`StaticText`)로 있다.** 창 ①·③ 에 없던 것이 **렌더 결과를 읽는 창**에는 나온다 — 보조 기술은 따옴표를 **받는다.**
- ★★ **만드는 것은 CSS 다.** `::before` 의 계산값이 `open-quote`, `::after` 가 `close-quote` 이고, `q` 의 자식 노드는 `#text, Q` 뿐이다 — **따옴표 노드가 없다.**
- ★★ **모양은 `lang` 이 고른다.** 계산값은 전부 `quotes = auto` 로 같은데 **글자가 다섯 가지로 갈렸다.** `auto` 가 「요소의 언어에 맞춰라」이기 때문이다. ★ **어느 언어가 어느 글자인지는 이 판의 구현 표**다 — HTML 명세 렌더링 절에는 언어별 표가 없다(머리말).
- ★ **`ko` 의 세 겹째는 `‘’` 를 되풀이했다** — 표에 두 단계만 있으면 마지막 단계를 되풀이한다.
- ★ **`q` 자신은 이 트리에 노드로 안 나왔다** — 따옴표와 글자가 문단에 바로 붙었다. HTML-AAM 이 `q` → **`generic`** 이고, 이 판이 **`id` 없는 `generic` 을 무시된 노드로 빼기** 때문으로 보인다(이 배치에서 본 사례가 전부 그랬다 — 구현의 관찰이지 규칙이 아니다). `id` 를 단 `<q>` 는 (4) 의 트리에서 **`generic` 노드로 남는다.** 어느 쪽이든 **「인용」이라는 역할은 없다.**

> **`quotes: auto`** — 요소의 **언어**에 맞는 따옴표 쌍을 브라우저가 고르게 하는 CSS 값.\
> 예: `lang="fr"` 이면 `«` `»`.

### (3) 창 ② + 창 ⑦ — `cite` 속성은 URL 로 풀리고, 아무 데도 안 나온다

**언제 쓰나** — 인용에 출처를 달 때, **무엇이 그것을 쓰는지** 묻는 자리.

```html
<!-- html13b-14-cite.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>14 cite 속성과 cite 요소</title>
<base href="https://example.org/doc/">
</head>
<body>
<blockquote id="bq" cite="notes/talk.html#p3">
  <p>블록 인용의 본문</p>
</blockquote>
<p>짧은 인용 <q id="q" cite="https://example.com/a b">q 의 본문</q> 끝.</p>
<p><cite id="ci">어린 왕자</cite> 에서 인용했다.</p>
<p>값이 <del id="del" cite="log.html" datetime="2026-09-01">1만 원</del><ins id="ins" datetime="2026-09-26T09:00+09:00">2만 원</ins> 이 됐다.</p>
<script>
window.__대상 = [["bq", "#bq"], ["q", "#q"], ["ci", "#ci"], ["del", "#del"], ["ins", "#ins"]];
const $ = id => document.getElementById(id);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("cite 속성 — 속성값 · IDL 이 돌려주는 값 · 접근성 노드");
  for (const id of ["bq", "q", "del"]) {
    const el = $(id), a = __AX[id];
    O.push("  #" + id.padEnd(4) + "getAttribute = " + J(el.getAttribute("cite")));
    O.push("        .cite        = " + J(el.cite));
    O.push("        역할 = " + a.역할 + " · 이름 = " + J(a.이름) + " · 설명 = " + J(a.설명)
      + " · 속성 = " + J(Object.keys(a.속성)));
  }
  O.push("");
  O.push("cite 요소 · ins/del — 계산 스타일과 역할");
  for (const id of ["bq", "ci", "del", "ins"]) {
    const c = getComputedStyle($(id));
    O.push("  #" + id.padEnd(4) + "display = " + c.display.padEnd(7) + "font-style = " + c.fontStyle.padEnd(7)
      + "text-decoration = " + c.textDecorationLine.padEnd(13) + "margin-left = " + c.marginLeft.padEnd(5)
      + "역할 = " + __AX[id].역할);
  }
  O.push("");
  O.push("ins/del 의 datetime");
  for (const id of ["del", "ins"])
    O.push("  #" + id.padEnd(4) + ".dateTime = " + J($(id).dateTime));
  O.push("");
  O.push("창 ③ — 지운 글자도 글자인가");
  O.push("  innerText = " + J($("del").parentNode.innerText));
  return O.join("\n");
};
</script>
</body>
</html>
```

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

- ★★ **`.cite` 는 속성 글자가 아니라 해석된 URL 이다.** `notes/talk.html#p3` 이 `<base>` 기준으로 **절대 URL** 이 됐고, 공백은 **`%20`** 으로 바뀌었다. 명세 IDL 이 `[ReflectURL] cite` 이기 때문이다 — **URL 로 반영**한다.
- ★★★ **그런데 접근성 노드에는 아무것도 없다.** 이름도 설명도 빈 문자열이고, CDP 가 넘긴 속성 목록도 **빈 `[]`** 이다. 화면에도 안 나온다.
- ★ **HTML-AAM 의 `cite` 속성 줄은 「ARIA: 대응 없음 · macOS AX: `AXURL`」이다**. 즉 **플랫폼 한 곳에는 넘어간다**는데, **CDP 트리에는 그 층이 안 보인다** — 「없다」가 아니라 「**못 잰 것**」이다.
- ★ **요청도 안 한다** — `cite` 는 URL 이지만 브라우저가 **가져오지 않는다**. 이 주제에서 창 ⑤ 가 부적용인 이유다.
- ★ **명세가 그 용도를 적어 둔다** — 「UA 가 이 인용 링크를 따라가게 해 줄 **수는** 있지만, 이것은 **주로 사적인 용도**(예: 인용 통계를 모으는 서버 스크립트)이지 **독자를 위한 것이 아니다**」. 보이지 않는 것이 설계다.

```text
  cite 속성이 가는 곳과 안 가는 곳

  cite="notes/talk.html#p3"
        |
        +--> .cite (IDL)          https://example.org/doc/notes/talk.html#p3   ★ URL 로 풀린다
        +--> 화면                  (안 나온다)
        +--> 요청                  (안 한다)
        +--> CDP 접근성 트리        (안 나온다 — 속성 [])
        +--> macOS AX 의 AXURL     HTML-AAM 이 적는 곳. 이 판에서 못 본다
```

### (4) 창 ② + 창 ⑦ — `cite` 요소·`ins`/`del`·`blockquote` 의 모양과 역할

(3) 과 같은 실행의 뒷부분이다.

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

같은 파일의 접근성 트리다.

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

- **`<q id="q">`** — 트리에 **`generic`** 노드로 남았다((2) 의 `id` 없는 `<q>` 는 안 남았다). 따옴표 두 글자는 그 안의 `StaticText` 다.
- **`<blockquote>`** — `display: block` · `margin-left: 40px` · 역할 **`blockquote`**.
- **`<cite>`** — `italic` 인데 역할은 **`generic`**. HTML-AAM 은 「대응 역할 없음」(계산 역할 `html-cite`)이다 — Chrome 은 `generic` 으로 채웠다.
- **`<del>`·`<ins>`** — 취소선·밑줄에 역할 **`deletion`·`insertion`**. ★ **`<del>` 의 글자도 `innerText` 에 그대로 들어간다**(`1만 원2만 원`) — 「지웠다」는 표시일 뿐 **글자를 빼지 않는다.**

```text
  교정 기록은 세 창에서 이렇게 보인다

  <del datetime="2026-09-01">1만 원</del><ins datetime="…">2만 원</ins>

  창 ② 모양         1만 원 (취소선)   2만 원 (밑줄)
  창 ⑦ 역할         deletion          insertion
  창 ③ innerText    "1만 원2만 원"    <- 지운 글자도 그대로 흐른다
  창 ② .dateTime    "2026-09-01"      <- 속성 글자 그대로

  ★ 「지웠다」는 표시다. 글자를 빼고 싶으면 마크업에서 빼야 한다.
```
- **`.dateTime` 은 속성 글자 그대로**다 — (5) 가 그것을 전수로 판다.
- ★★ **`<cite>` 는 「저작물 제목」이다.** 명세 — 「**사람 이름은 저작물 제목이 아니다** — 그러므로 이 요소로 사람 이름을 표시하면 안 된다」. 역할이 `generic` 이라 **어느 창도 그 규칙을 잡지 않는다.**

### (5) 창 ② × 창 ⑦ — `time` 의 열네 형식, 갈린 칸을 스크립트가 센다

**언제 쓰나** — 이 주제의 둘째 본체. **「틀리면 뭔가 달라지겠지」를 반증하는 자리.**

명세가 드는 유효 형식 여덟(날짜·달·연도 없는 날짜·시각·전역 날짜와 시각·주·연도·기간)과 **틀린 것 넷**(없는 날·슬래시·낱말·빈 문자열), **`datetime` 없는 것 둘**을 넣었다. 그리고 역할·이름·설명·속성·`display` 다섯 칸을 **첫 줄(`2026-09-26`)과 견주어** 갈린 칸을 셌다.

```html
<!-- html13b-14-time.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>14 time 의 datetime</title>
</head>
<body>
<ul>
<li><time id="t1" datetime="2026-09-26">오늘</time> 날짜
<li><time id="t2" datetime="2026-09">이번 달</time> 달
<li><time id="t3" datetime="09-26">매년 이날</time> 연도 없는 날짜
<li><time id="t4" datetime="14:30">오후 두 시 반</time> 시각
<li><time id="t5" datetime="2026-09-26T14:30+09:00">오늘 오후</time> 전역 날짜·시각
<li><time id="t6" datetime="2026-W39">39주</time> 주
<li><time id="t7" datetime="2026">올해</time> 연도
<li><time id="t8" datetime="PT2H">두 시간</time> 기간
<li><time id="t9" datetime="2026-02-30">없는 날</time> 틀림 — 2월 30일
<li><time id="t10" datetime="26/09/2026">슬래시</time> 틀림 — 형식
<li><time id="t11" datetime="내일">내일</time> 틀림 — 낱말
<li><time id="t12" datetime="">빈 값</time> 틀림 — 빈 문자열
<li><time id="t13">2026-09-26</time> datetime 없음 — 내용이 값
<li><time id="t14">어제</time> datetime 없음 — 내용도 틀림
</ul>
<script>
const 번호 = Array.from({ length: 14 }, (_, i) => "t" + (i + 1));
window.__대상 = 번호.map(id => [id, "#" + id]);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push(" #   " + "getAttribute".padEnd(26) + ".dateTime".padEnd(26) + "역할  이름  설명  속성  display  innerText");
  const 틀린것 = new Set(["t9", "t10", "t11", "t12", "t14"]);
  const 서명 = {};
  for (const id of 번호) {
    const el = document.getElementById(id), a = __AX[id];
    const 줄 = [a.역할, J(a.이름), J(a.설명), J(Object.keys(a.속성)), getComputedStyle(el).display];
    서명[id] = 줄.join("|");
    O.push((" " + id).padEnd(5) + J(el.getAttribute("datetime")).padEnd(26) + J(el.dateTime).padEnd(26)
      + 줄.join("  ") + "  " + J(el.innerText));
  }
  O.push("");
  O.push("유효한 것과 틀린 것이 갈리는 칸 — 역할·이름·설명·속성·display 다섯 칸을 t1 과 견준다");
  let 갈림 = 0, 전체 = 0;
  for (const id of 번호) {
    if (id === "t1") continue;
    const a = 서명.t1.split("|"), b = 서명[id].split("|");
    a.forEach((v, i) => { 전체++; if (v !== b[i]) 갈림++; });
  }
  O.push("갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

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

```text
  datetime 을 받아서 브라우저가 하는 일

  datetime="2026-02-30"  (없는 날)
        |
        +--> .dateTime        "2026-02-30"     그대로 돌려준다 — 파싱 안 함
        +--> 역할             time             유효한 것과 같다
        +--> 이름·설명         ""               〃
        +--> CDP 속성          []               〃
        +--> display          inline           〃
        +--> 콘솔              0줄              경고 없음
        +--> 화면              "없는 날"         내용 글자만 보인다

  ★ 검증자가 없다. 명세는 형식을 정하지만, 그 형식을 검사하는 것은 브라우저가 아니다.
```

- ★★★ **갈린 칸 = 0 / 65.** 유효한 것 여덟, 틀린 것 넷, `datetime` 없는 것 둘이 **다섯 칸에서 한 칸도 안 갈렸다.** 콘솔도 **0줄**이다.
- ★★★ **`.dateTime` 은 파싱하지 않는다.** `"2026-02-30"`·`"내일"`·`"26/09/2026"` 을 **글자 그대로** 돌려준다. 명세 IDL 이 `[Reflect] DOMString dateTime` — **글자를 비출 뿐**이다.
- ★★ **`datetime` 이 없으면 `.dateTime` 은 `""`** 이다(`t13`·`t14`). 명세는 이때 「**datetime 값은 내용 글자**」라고 정하는데(`t13` 의 `2026-09-26`), **IDL 은 속성만 비추므로 그 값을 안 준다.** 「명세가 말하는 값」과 「스크립트가 받는 값」이 **다른 두 개**다.
- ★ **역할은 `time`** 이다 — HTML-AAM 도 `time` → `time role` 이다. 그러나 **값은 트리에 안 실렸다**(속성 `[]`). HTML-AAM 은 `datetime` 을 **플랫폼 속성**(IA2 `datetime:` · macOS `AXDateTimeValue`)으로 넘기라고 적는데, 그 층은 **CDP 로 못 본다** — 「못 잰 것」.
- ★★ **결론은 「검증자가 없다」이다.** 형식은 명세에 있지만 **어긋났을 때 알려 주는 쪽이 브라우저에 없다.** 형식을 지키게 하는 것은 **검증기**(W3C Nu Validator 류)인데 **이 환경에 없다**([01번 주제](../01-document-skeleton/2-summary.md)의 「이 갈래의 창」 절) — 그래서 **어느 형식이 유효한가**는 이 문서에서 **명세를 읽은 것**이지 실행 결과가 아니다.

```text
  「datetime 값」과 .dateTime 은 다른 두 개다

  <time>2026-09-26</time>                  (datetime 속성 없음)

  명세의 datetime 값     "2026-09-26"   <- 속성이 없으면 내용 글자
  .dateTime (IDL)        ""             <- [Reflect] — 속성만 비춘다
  역할                    time
  CDP 속성                []

  <time datetime="내일">내일</time>
  명세의 datetime 값     "내일"          <- 형식에 안 맞는다 (명세상 무효)
  .dateTime              "내일"          <- 그래도 그대로 돌려준다
```

| 넣은 값 | 명세의 형식 이름 | 이 판의 반응 |
|---|---|---|
| `2026-09-26` | valid date string | 없음 |
| `2026-09` | valid month string | 없음 |
| `09-26` | valid yearless date string | 없음 |
| `14:30` | valid time string | 없음 |
| `2026-09-26T14:30+09:00` | valid global date and time string | 없음 |
| `2026-W39` | valid week string | 없음 |
| `2026` | 「네 자리 이상 숫자」(연도) | 없음 |
| `PT2H` | valid duration string | 없음 |
| `2026-02-30` · `26/09/2026` · `내일` · `""` | **어느 형식에도 안 맞는다** | ★ **역시 없음** |

### demo — `lang` 이 따옴표를 바꾼다

```html demo
<!-- html13b-14-demo.html -->
<p lang="ko"><q>바깥 <q>안쪽</q></q></p>
<p lang="fr"><q>dehors <q>dedans</q></q></p>
<p lang="ja"><q>外 <q>内</q></q></p>
<p lang="de"><q>außen <q>innen</q></q></p>
```

> **보이는 것** — 네 줄의 인용이 **각기 다른 따옴표**로 감싸인다. 한국어 줄은 `“바깥 ‘안쪽’”`, 프랑스어 줄은 `«dehors «dedans»»`, 일본어 줄은 `「外 『内』」`, 독일어 줄은 `„außen ‚innen‘“`. 마크업에는 따옴표가 **한 글자도 없다.**\
> **바꿔 볼 것** — 넷째 줄의 `lang="de"` → `lang="fr"`(그 줄의 따옴표가 `«` 로 바뀐다)

*(Chrome 151 headless 실측 — 접근성 트리의 `StaticText` 로 읽었다. 글자를 픽셀로 읽지 않았으므로 이 줄은 **어느 글자가 넘어가나**의 근거이지 **어떻게 그려지나**의 근거가 아니다)*

```text
$ python3 html13b-cdp.py ax html13b-14-demo.html
RootWebArea    이름=''
  paragraph      이름=''
    StaticText     이름='“'
    StaticText     이름='바깥 '
    StaticText     이름='‘'
    StaticText     이름='안쪽'
    StaticText     이름='’'
    StaticText     이름='”'
  paragraph      이름=''
    StaticText     이름='«'
    StaticText     이름='dehors '
    StaticText     이름='«'
    StaticText     이름='dedans'
    StaticText     이름='»'
    StaticText     이름='»'
  paragraph      이름=''
    StaticText     이름='「'
    StaticText     이름='外 '
    StaticText     이름='『'
    StaticText     이름='内'
    StaticText     이름='』'
    StaticText     이름='」'
  paragraph      이름=''
    StaticText     이름='„'
    StaticText     이름='außen '
    StaticText     이름='‚'
    StaticText     이름='innen'
    StaticText     이름='‘'
    StaticText     이름='“'
(exit 0)
```

- ★ 「바꿔 볼 것」의 단언(`fr` 이면 `«`)은 (2) 의 `fr` 줄이 같은 판에서 던진 것이다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다. 쓰는 꼴은 (1)·(3)·(5) 의 소스가 전부 실제로 던진 형태다.

| 쓰려는 것 | 형태 | 주의 |
|---|---|---|
| 문단 크기의 인용 | `<blockquote cite="URL">…</blockquote>` | `cite` 는 **안 보이고 요청도 안 한다** |
| 문장 안의 짧은 인용 | `<q cite="URL">…</q>` | ★ **따옴표를 손으로 쓰지 않는다** — UA 가 넣는다 |
| 저작물 제목 | `<cite>어린 왕자</cite>` | ★ **사람 이름에 쓰지 않는다** |
| 지운 것 / 넣은 것 | `<del datetime="…" cite="URL">` · `<ins …>` | `del` 의 글자도 **글자로 남는다** |
| 기계가 읽을 시각 | `<time datetime="2026-09-26">오늘</time>` | ★ **틀려도 아무도 안 알려 준다** |
| 내용이 이미 기계 형식 | `<time>2026-09-26</time>` | 명세의 값은 내용이지만 **`.dateTime` 은 `""`** |

### 어디서 헷갈리나

- **`cite` 속성과 `cite` 요소는 다른 것이다.** 속성은 **출처 URL**(안 보인다), 요소는 **저작물 제목**(기울여 보인다).
- **`<q>` 의 따옴표는 글자가 아니다.** 복사·`innerText`·`textContent` 에서 **사라진다.**
- **`<del>` 은 글자를 지우지 않는다.** 취소선을 긋고 `deletion` 역할을 줄 뿐, **글자는 그대로** 흐른다.
- **`<time>` 은 형식을 검사하지 않는다.** `datetime` 은 **기계가 읽을 수 있게 적어 두는 약속**이지, 브라우저가 지켜 주는 것이 아니다.

## 어디서 틀리나

### 1. `<q>` 안에 따옴표를 또 쓴다

**두 겹이 된다.** 명세가 금한다 — 「인용 부호를 `q` 의 앞·뒤·안에 쓰지 말라」.\
★ 그리고 `lang` 이 다른 문서로 옮겨 가면 **손으로 쓴 따옴표만 안 바뀐다.**

던져서 확인했다 — 손으로 쓴 `"` 를 `<q>` 안에 넣고 `ko`·`fr` 두 줄로.

```html
<!-- html13b-14-double.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>14 따옴표를 손으로 또 쓰면</title>
</head>
<body>
<p id="ko">ko: <q>"안녕"</q></p>
<p id="fr" lang="fr">fr: <q>"안녕"</q></p>
<script>
window.__대상 = [];
window.__끝 = () => ["ko", "fr"].map(id =>
  "#" + id + "  innerText = " + JSON.stringify(document.getElementById(id).innerText)).join("\n");
</script>
</body>
</html>
```

```text
$ python3 html13b-cdp.py page html13b-14-double.html
#ko  innerText = "ko: \"안녕\""
#fr  innerText = "fr: \"안녕\""
(exit 0)
```

```text
$ python3 html13b-cdp.py ax html13b-14-double.html
RootWebArea    이름='14 따옴표를 손으로 또 쓰면'
  paragraph      이름=''
    StaticText     이름='ko: '
    StaticText     이름='“'
    StaticText     이름='"안녕"'
    StaticText     이름='”'
  paragraph      이름=''
    StaticText     이름='fr: '
    StaticText     이름='«'
    StaticText     이름='"안녕"'
    StaticText     이름='»'
(exit 0)
```

```text
  <q>"안녕"</q>  을 쓰면 (위 두 블록을 읽은 것)

  접근성 트리  ko   “ "안녕" ”     <- UA 의 따옴표 + 손으로 쓴 따옴표, 두 겹
               fr   « "안녕" »     <- 바깥만 lang 을 따른다. 손으로 쓴 것은 글자라 그대로
  innerText    ko   ko: "안녕"     <- 남는 것은 손으로 쓴 것뿐
               fr   fr: "안녕"

  ★ 명세는 「따옴표를 q 의 앞·뒤·안에 쓰지 말라 — UA 가 넣는다」고 적는다.
```

### 2. `innerText` 로 인용문을 가져가서 따옴표를 기대한다

**없다**((1)). 따옴표는 **CSS 생성 콘텐츠**라 `innerText` 가 글자로 치지 않는다.\
★ 반대로 **접근성 트리에는 있다**((2)) — 「보조 기술은 받는데 복사는 못 받는다」.

### 3. `cite` 속성이 링크가 될 줄 안다

**화면에도 안 나오고, 요청도 안 하고, CDP 접근성 트리에도 없다**((3)). 출처를 **보여 주고** 싶으면 `<a href>` 를 따로 쓴다.

### 4. `<cite>` 로 발언자 이름을 감싼다

명세가 **명시적으로 금한다**((4)). 그런데 역할이 `generic` 이라 **어느 도구도 안 잡는다.**

### 5. `datetime` 에 사람이 읽는 형식을 넣는다

`26/09/2026`·`내일` 도 **아무 일 없이 통과한다**((5) — 갈린 칸 0 / 65).\
★ 「브라우저가 받아 줬으니 맞겠지」가 이 주제의 가장 흔한 착각이다 — **받아 주는 게 아니라 안 보는 것**이다.

### 6. `<time>2026-09-26</time>` 의 `.dateTime` 이 날짜를 줄 줄 안다

**`""`** 다((5) 의 `t13`). 명세의 「datetime 값」은 내용 글자지만 **IDL 은 속성만 비춘다.**

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML 렌더링 절)** | `q::before { content: open-quote }` · `q::after { content: close-quote }` | (2) |
| **명세(CSS)** | `quotes: auto` 가 **언어에 맞는** 따옴표를 고른다 | (2) — ★ **어느 언어가 어느 글자인지는 구현의 표**다 |
| **명세(HTML)** | `q` 안팎에 따옴표를 **쓰지 말라** · `cite` 요소에 **사람 이름을 쓰지 말라** | (1)·(4) — **강제하는 도구는 없다** |
| **명세(HTML IDL)** | `.cite` 는 **`ReflectURL`** · `.dateTime` 은 **`Reflect`**(글자 그대로) | (3)·(5) |
| **명세(HTML)** | `datetime` 값이 **맞아야 하는 형식** 아홉 가지 | (5) 의 표 — ★ **실행으로는 확인 못 한다**(검증자가 없다) |
| **명세(HTML-AAM)** | `blockquote`→`blockquote` · `del`→`deletion` · `ins`→`insertion` · `time`→`time` · `q`→`generic` · `cite`→대응 없음 | (2)·(4)·(5) |
| **명세(HTML-AAM)** | `cite` 속성 → **ARIA 대응 없음**(macOS `AXURL`) · `time`·`ins`/`del` 의 `datetime` → **플랫폼 속성** | (3)·(5) — CDP 로는 못 본다 |
| **구현(Chrome)** | `lang` 별 따옴표 글자 표 | (2) |
| **이 판의 관찰** | `innerText` 가 생성 콘텐츠를 **안 넣는** 것 | (1) — `innerText` 알고리즘의 명세 문장은 이 배치에서 열어 보지 않았다 |
| **구현(Chrome)** | `cite` 요소를 `generic` 으로 채운 것 | (4) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **스크린리더가 따옴표를 읽는지·인용을 알려 주는지** | 보조 기술이 없다. 트리에 `“` 가 있다는 것까지가 관찰이다 |
| ★★ **`datetime` 이 유효한지** | 이 환경에 **검증기가 없다.** 형식 표는 명세를 읽은 것이다 |
| **플랫폼 API 의 `datetime`·`AXURL`** | CDP 트리는 그 아래 층을 안 보여 준다 — 「못 잰 것」 |
| **검색 엔진·달력 앱이 `time` 을 읽는지** | 이 머신에서 잴 수 없다. 이 문서는 그 주장을 안 한다 |
| **다른 엔진의 따옴표 표** | 엔진이 하나뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **문장 안 인용은 `<q>`, 문단 인용은 `<blockquote>`** — 따옴표는 **쓰지 않는다.**
- **글자로 따옴표가 꼭 남아야 하면**(복사·메일 본문) `<q>` 대신 **따옴표 글자**를 직접 쓴다.
- **출처를 보여 줄 거면 `<a href>`** — `cite` 속성은 **기계용 메모**다.
- **`<cite>` 는 책·논문·영화 제목에만** — 사람 이름에는 안 쓴다.
- **`<time datetime>` 은 명세 형식을 사람이 지킨다** — 브라우저가 안 지켜 준다. 가능하면 **서버가 만든 값**을 넣는다.
- **`<del>`·`<ins>` 는 「고친 기록」을 남기고 싶을 때** — 지운 글자는 **여전히 글자**다.

## 핵심 문장

1. **`q` 의 따옴표는 CSS 생성 콘텐츠다 — 트리(창 ①)에도 글자(창 ③)에도 없고 접근성 트리(창 ⑦)에만 있다.**
2. **따옴표 모양은 `quotes: auto` 아래에서 `lang` 이 고른다 — `ko`·`en` 은 `“‘`, `fr` 은 `«`, `ja` 는 `「『`, `de` 는 `„‚`.**
3. **`.cite` 는 URL 로 풀리지만, `cite` 속성은 화면·요청·CDP 트리 어디에도 안 나온다.**
4. **`<cite>` 는 저작물 제목이고 사람 이름에 쓰면 안 된다 — 역할이 `generic` 이라 아무도 안 잡는다.**
5. **`<del>` 의 글자도 `innerText` 에 그대로 흐른다.**
6. **`time` 에 틀린 `datetime` 을 넣어도 갈린 칸은 0 / 65 다 — `.dateTime` 은 파싱 없이 글자를 돌려준다.**
7. **그 결론은 「잴 것이 없다」가 아니라 「검증자가 없다」다.**

## 관련 자료

- [13번 주제 — 구절 시맨틱](../13-phrasing-semantics/2-summary.md) — 같은 묶음의 앞 편이고 **창 ② × 창 ⑦ 대조의 형식**이 그쪽에서 섰다.
- [04번 주제 — 공백·텍스트·문자 참조](../04-whitespace-and-character-references/2-summary.md) — **창 ③ 의 정의**가 그쪽이다. 여기는 **생성 콘텐츠가 창 ③ 을 빠져나간다**는 결과까지.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **13번**([의사 요소와 생성 콘텐츠](../../../css/syntax/13-pseudo-elements-and-generated-content/2-summary.md)) — **`::before`·`content`·`quotes` 가 상자를 만드는 방식**은 그쪽이 정본이다. 여기는 **`q` 가 그것을 쓴다**까지.
- 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **06번**([속성 대 성질](../../../../web-api/06-attribute-vs-property/2-summary.md)) — **반영(reflect)의 일반 규칙**은 그쪽이 정본이다. 여기는 `cite`(URL 반영)와 `dateTime`(글자 반영) 두 사례.
- [목록의 **20번 주제**](../20-lang-dir-and-bidi/)(`lang`·`dir`) — **`lang` 이 글꼴·음성·하이픈에 미치는 영향 전체**는 그쪽. 여기는 따옴표 하나.
- 목록의 **23번 주제**(`<input>` 숫자·날짜) — **날짜 형식을 브라우저가 실제로 파싱하는 자리**(`input type=date`)는 그쪽이다. `time` 과 대비된다.
- [01번 주제 — 문서의 뼈대](../01-document-skeleton/2-summary.md) — 「이 환경에 validator 가 없다」의 선언.

## 용어 풀이

- **생성 콘텐츠(generated content)** — CSS `content` 로 렌더 단계에서 만든 글자. DOM 노드가 없다.
- **`open-quote` / `close-quote`** — 「여는/닫는 따옴표를 찍어라」라는 `content` 값. 어느 글자인지는 `quotes` 가 정한다.
- **`quotes: auto`** — 요소의 언어에 맞는 따옴표를 고르게 하는 값.
- **`cite` 속성** — `blockquote`·`q`·`ins`·`del` 의 **출처 URL.** 안 보이고 요청도 안 한다.
- **`cite` 요소** — **저작물 제목.** 사람 이름이 아니다.
- **`ReflectURL`** — 속성을 **URL 로 풀어서** 스크립트에 비추는 IDL 규칙.
- **datetime 값(datetime value)** — `datetime` 속성, 없으면 **내용 글자.** `.dateTime` IDL 과 **같지 않다.**
- **검증자(validator)** — 마크업이 명세 형식에 맞는지 검사하는 도구. **브라우저는 이 일을 안 한다.**

## 더 들어가면

- **왜 따옴표를 CSS 로 만들게 했나** — 인용 부호는 **언어마다 다르다.** 마크업에 글자로 박으면 번역·재사용 때마다 고쳐야 한다. 「여기가 인용이다」만 적고 **모양은 언어가 고르게** 한 것이 `<q>` 의 설계다. 대가가 (1) 의 「복사하면 사라진다」다.
- **왜 브라우저가 `datetime` 을 검사하지 않나** — `time` 은 **보이는 동작이 없는** 요소다. 검사해서 거절할 동작(제출·계산)이 없으니 **검사할 이유도 자리도 없다.** `input type=date` 는 반대다 — 값을 **제출**하므로 파싱한다(목록의 **23번 주제**).
- **`blockquote` 의 출처 표시** — 명세 — 「인용의 출처 표기는 **`blockquote` 요소 밖에 두어야 한다**(must)」. 뒤따르는 문단이 명세의 예이고, `figure`·`figcaption` 으로 묶는 구조는 [목록의 **19번 주제**](../19-figure-address-hr/)가 다룬다.
