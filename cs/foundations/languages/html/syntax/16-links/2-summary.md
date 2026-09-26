# html/syntax/16 — 링크: `href` 의 형태·`target`·`rel`(`noopener`/`noreferrer`/`nofollow`)·`download` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Links」](https://html.spec.whatwg.org/multipage/links.html) 절 — 「Following hyperlinks」(★ **「요소의 noopener 구하기」 알고리즘**)·「Downloading resources」·「Link types」(`nofollow`·`noopener`·`noreferrer`·`opener`), 그리고 [Referrer Policy](https://w3c.github.io/webappsec-referrer-policy/)(기본 정책), [HTML-AAM](https://w3c.github.io/html-aam/). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 링크는 **CDP 의 실제 마우스 입력**으로 눌렀고(스크립트의 `a.click()` 이 아니다), 요청은 **같은 프로세스 안에 띄운 서버 둘**이 받아 적었다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.** 「`_blank` 가 기본으로 `noopener`」는 **명세 알고리즘**이고, **다른 엔진이 그것을 구현했는지는 미실행**이다.
> **버전** — HTML 에는 언어 버전이 없다. ★ 이 주제의 핵심인 **「`target="_blank"` 가 `rel="opener"` 없이는 `noopener` 로 동작한다」는 명세가 나중에 바꾼 규칙**이다 — 한때는 `_blank` 로 연 창이 `window.opener` 로 원래 창을 쥐었다. 바뀐 시점은 이 문서가 확인하지 않았다.
> **선행** — [07번 주제](../07-id-and-fragments/2-summary.md)(`#fragment` 가 무엇을 찾나).
> **경계** — **프로토콜은 [`history/web/02-HTTP-진화.md`](../../../../../../history/web/02-HTTP-진화.md) 의 몫이고, 여기는 마크업이 그 요청을 어떻게 만드느냐**다. ★ 다만 그 문서에는 **`Referer` 헤더·Referrer-Policy 절이 없다**(두 낱말로 grep 해 확인했다) — 이 주제가 싣는 `Referer` 는 **서버 로그로 본 관찰**과 **Referrer Policy 명세의 기본값 한 줄**까지다. `window.opener` 를 스크립트로 다루는 일은 웹 API 쪽인데, **웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))에 `window.open`·`opener` 주제는 없다**(확인).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다.** `rel` 이 바꾸는 것은 **화면이 아니라 요청과 새 창의 관계**라, 서버가 받은 `Referer` 헤더와 새 창 쪽에서 찍은 `window.opener` 로만 보인다. `href` 쪽은 **창 ②(`a.href` 가 해석한 값)** 가 본체다.

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
| **흔들린다** | CDP 포트·프로필 경로·내려받기 임시 폴더 | 실행마다 무작위 — **출력에는 안 들어간다** |
| **죽였다** | 서버 로그의 **시각·클라이언트 포트** | ★ 서버가 **「어느 서버 · 메서드 · 경로 · `Referer`」 네 칸만** 적게 짰다 |
| **고정했다** | 서버 포트 **18713(A)·18714(B)** | 소스에 박았다 — 포트가 달라 **다른 출처**다 |
| **고정했다** | favicon 요청 | 모든 페이지가 `<link rel="icon" href="data:,">` 를 달아 **요청 자체가 안 생긴다** |
| **안 흔들린다** | 링크마다의 요청 줄 수·`Referer`·`document.referrer`·`window.opener` | 링크를 **하나씩** 누르고 **새 문서의 `load` 이벤트**를 받은 뒤 다음으로 간다 — 순서가 섞일 틈이 없다 |
| **안 흔들린다** | `a.href`·`:link`·포커스·역할 | 같은 판이면 결정적이다 |
| **안 흔들린다** | 「갈린 칸 N / M」 | 스크립트가 센다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | `Referer` 가 **실렸나** · 요청이 **몇 번** 갔나 · `download` 가 **내려받았나 이동했나**((3)·(4)) |
| **새 창 쪽 프로브**(CDP 로 붙은 새 문서) | ★ **쓴다 — 본체의 짝** | `window.opener` 가 **`null` 인가** · `document.referrer`((3)) |
| **② 프로브**(`a.href`·`:link`·`relList`) | ★ **쓴다 — `href` 의 본체** | `href` 가 **무엇으로 풀렸나** · 브라우저가 **어느 `rel` 을 처리하나**((1)·(2)) |
| **⑦ 접근성 트리** | 쓴다 | 링크인가(`link` 대 `generic`) · `rel`·`download` 가 **트리에 흔적을 남기나**((1)·(5)) |
| **① `--dump-dom`** | **부적용** | 링크는 파서가 고칠 것이 없다 — 트리에 `href` 글자가 그대로 있을 뿐이다 |
| **③ `innerText` 대 `textContent`** | **부적용** | 링크의 글자는 여느 글자와 같다 — **잴 것이 없다** |
| **④ `compatMode`** | **부적용** | 문서 모드와 무관하다 |
| **⑥ `renderBlockingStatus`** | **부적용** | 링크는 렌더를 막지 않는다 |

- ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「`noreferrer` 가 무엇을 지우나」를 **새 창의 `document.referrer`** 로 물으면 「빈 문자열」, **서버 로그**로 물으면 「`Referer` 헤더가 **아예 없다**」다. 둘 다 같은 사실을 보이지만 ★ **서버 로그만이 「보냈는데 새 창이 감춘 것」과 「처음부터 안 보낸 것」을 가른다.** 이 판은 **안 보냈다.**
- ★★★ **`nofollow` 는 「잴 것이 없다」(제4의 상태)의 자리다.** 브라우저가 **처리하지 않는 토큰**이라고 **스스로 말했고**(`relList.supports('nofollow')` → `false`), 요청·새 창 세 칸에서 **「rel 없음」과 0 / 3 갈렸다.** ★ **그러나 「검색 엔진이 그것을 어떻게 쓰나」는 「못 잰 것」(제3의 상태)이다** — 동작은 이 머신 밖에 있다. 두 상태를 섞지 않는다.

## 한눈에 — 쉽게 말하면

**★ 링크를 누르는 것은 「새 문서에게 편지를 보내는 것」이다. `rel` 은 그 편지의 발신인 칸과, 새 문서가 「답장할 주소」를 쥐느냐를 정한다.**

회사 우편실에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 편지 봉투의 **보낸 곳 칸** | **`Referer` 헤더** — 서버가 받는다 |
| 받은 사람이 편지에서 읽는 **보낸 곳** | **`document.referrer`** — 새 문서가 읽는다 |
| 받은 사람이 **보낸 사람의 책상 열쇠**를 쥐는 것 | **`window.opener`** — 새 창이 원래 창을 쥔다 |
| 「**열쇠는 주지 마라**」 도장 | **`rel="noopener"`** |
| 「**보낸 곳도 지우고 열쇠도 주지 마라**」 도장 | **`rel="noreferrer"`** |
| 「**열쇠를 줘라**」 도장 | **`rel="opener"`** |
| **새 봉투(새 창)** 로 보내면 기본이 「열쇠 안 줌」 | **`target="_blank"`** 는 기본으로 `noopener` |
| 「**이 편지는 추천이 아니다**」라는, 우편실은 **안 읽는** 메모 | **`rel="nofollow"`** — 브라우저는 처리하지 않는다 |
| 「**뜯지 말고 보관함에 넣어라**」 | **`download`** — **같은 회사 안(같은 출처)** 에서만 들어준다 |

- **`noreferrer` 는 봉투의 보낸 곳을 지운다** — 서버 로그에 `Referer` 가 **없다**((3)).
- **`_blank` 는 이미 열쇠를 안 준다** — `rel` 없이도 `window.opener` 가 **`null`** 이다((3)).
- **다른 출처로는 보낸 곳이 줄어든다** — 경로 없이 **출처만** 간다((3)).
- **`download` 는 다른 출처에서 무시된다** — 내려받지 않고 **그 파일로 이동**한다((4)).

```text
  같은 링크 한 번 누르기가 남기는 세 흔적

  원래 창 (A: 127.0.0.1:18713)                 서버               새 창
  <a target=_blank href="/dest.html">  ──요청──>  A GET /dest.html
                                                 Referer=A/rel.html  ──>  document.referrer = A/rel.html
                                                                           window.opener   = null   ★ _blank 의 기본

  rel=noreferrer 이면                             Referer=(없음)       ──>  document.referrer = ""
                                                                           window.opener   = null
  rel=opener 이면                                 Referer=A/rel.html   ──>  window.opener   = 창 객체

  세 흔적 중 화면에 보이는 것은 하나도 없다.
```

실무에서 이게 터지는 자리는 **예전 코드의 `rel="noopener noreferrer"` 를 「보안에 좋다니까」 일괄로 붙이는 것**이다.\
`_blank` 라면 `noopener` 는 **이미 기본**이라 한 칸도 안 바꾸고(0 / 3), `noreferrer` 는 **분석 도구가 보는 유입 경로를 지운다**(2 / 3).\
그리고 반대 방향의 사고 — **`target` 에 이름을 준 링크**(`target="도움말"`)는 **`_blank` 가 아니라서 기본으로 열쇠를 준다**((3) 의 `창이름1`).

> **`Referer` 헤더** — 요청이 **어느 문서에서 왔나**를 서버에 알리는 HTTP 헤더. 철자가 `Referrer` 가 아니라 `Referer` 다(헤더 이름이 그렇게 굳었다).\
> 예: 이 판에서 같은 출처 링크는 `Referer=http://127.0.0.1:18713/html13b-16-rel.html`.

> **`window.opener`** — 새 창이 **자기를 연 창**을 가리키는 참조. `null` 이면 못 쥔다.\
> 예: `rel="opener"` 로 연 창에서만 「창 객체」였다.

## 이 주제가 답하려는 질문

1. **`href` 의 여러 형태가 각각 무엇으로 풀리나** — 상대·절대·프로토콜 상대·`#`·빈 문자열·`javascript:`·틀린 URL·`href` 없음.
2. **`noopener`·`noreferrer`·`nofollow`·`opener`·`referrerpolicy` 가 각각 무엇을 바꾸나** — 요청의 `Referer`, 새 문서의 `document.referrer`, 새 창의 `window.opener` 세 칸으로.
3. **`download` 는 언제 들어지고 언제 무시되나.**

## 동작 방식

### (1) 창 ② + 창 ⑦ — `href` 열다섯 형태가 무엇으로 풀리나

**언제 쓰나** — `href` 에 무엇을 적든 **브라우저가 최종적으로 무슨 URL 을 쓰는지** 확인하는 자리.

문서를 `http://127.0.0.1:18713/d/html13b-16-href.html` 에 두고(★ `../` 가 뜻을 가지도록 한 단계 아래 폴더), 열다섯 링크의 **속성 글자 · `a.href` · `:link` 일치 · 포커스 · 역할**을 한 줄씩 찍었다.

```html
<!-- html13b-16-href.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>16 href 의 형태</title>
</head>
<body>
<p><a id="h1" href="b.html">1</a> <a id="h2" href="./b.html">2</a> <a id="h3" href="../b.html">3</a>
<a id="h4" href="/b.html">4</a> <a id="h5" href="?q=1">5</a> <a id="h6" href="#끝">6</a>
<a id="h7" href="">7</a> <a id="h8" href="//127.0.0.1:18714/b.html">8</a>
<a id="h9" href="http://127.0.0.1:18714/b.html">9</a>
<a id="h10" href="HTTP://127.0.0.1:18714/x/../%7Euser/b.html">10</a>
<a id="h11" href="  b.html  ">11</a> <a id="h12" href="javascript:void(0)">12</a>
<a id="h13" href="mailto:a@example.com">13</a> <a id="h14" href="http://[틀림">14</a>
<a id="h15">15</a></p>
<script>
const 번호 = Array.from({ length: 15 }, (_, i) => "h" + (i + 1));
window.__대상 = 번호.map(id => [id, "#" + id]);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("문서 URL = " + location.href);
  O.push("");
  O.push(" #   " + "href 속성".padEnd(46) + "a.href".padEnd(58) + ":link  포커스  역할");
  for (const id of 번호) {
    const a = document.getElementById(id);
    a.focus();
    const 포커스 = document.activeElement === a ? "된다" : "안 됨";
    O.push((" " + id).padEnd(5) + (a.hasAttribute("href") ? J(a.getAttribute("href")) : "(속성 없음)").padEnd(46)
      + J(a.href).padEnd(58) + String(a.matches(":link")).padEnd(7) + 포커스.padEnd(7) + __AX[id].역할);
  }
  const 있음 = 번호.map(id => document.getElementById(id)).filter(a => a.hasAttribute("href"));
  const 그대로 = 있음.filter(a => a.href === a.getAttribute("href"));
  O.push("");
  O.push("해석해도 글자가 그대로인 칸 = " + 그대로.map(a => "#" + a.id).join(" · "));
  O.push("그대로인 칸 = " + 그대로.length + " / " + 있음.length);
  O.push("");
  O.push("rel 의 지원 토큰 — a.relList.supports()");
  const a = document.getElementById("h1");
  for (const t of ["noopener", "noreferrer", "opener", "nofollow", "stylesheet", "zzz"]) {
    let r;
    try { r = String(a.relList.supports(t)); } catch (e) { r = e.name + " 「" + e.message + "」"; }
    O.push("  " + t.padEnd(11) + r);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html13b-link.py page d/html13b-16-href.html | sed -n '1,18p'
문서 URL = http://127.0.0.1:18713/d/html13b-16-href.html

 #   href 속성                                       a.href                                                    :link  포커스  역할
 h1  "b.html"                                      "http://127.0.0.1:18713/d/b.html"                         true   된다     link
 h2  "./b.html"                                    "http://127.0.0.1:18713/d/b.html"                         true   된다     link
 h3  "../b.html"                                   "http://127.0.0.1:18713/b.html"                           true   된다     link
 h4  "/b.html"                                     "http://127.0.0.1:18713/b.html"                           true   된다     link
 h5  "?q=1"                                        "http://127.0.0.1:18713/d/html13b-16-href.html?q=1"       true   된다     link
 h6  "#끝"                                          "http://127.0.0.1:18713/d/html13b-16-href.html#%EB%81%9D" true   된다     link
 h7  ""                                            "http://127.0.0.1:18713/d/html13b-16-href.html"           true   된다     link
 h8  "//127.0.0.1:18714/b.html"                    "http://127.0.0.1:18714/b.html"                           true   된다     link
 h9  "http://127.0.0.1:18714/b.html"               "http://127.0.0.1:18714/b.html"                           true   된다     link
 h10 "HTTP://127.0.0.1:18714/x/../%7Euser/b.html"  "http://127.0.0.1:18714/%7Euser/b.html"                   true   된다     link
 h11 "  b.html  "                                  "http://127.0.0.1:18713/d/b.html"                         true   된다     link
 h12 "javascript:void(0)"                          "javascript:void(0)"                                      true   된다     link
 h13 "mailto:a@example.com"                        "mailto:a@example.com"                                    true   된다     link
 h14 "http://[틀림"                                  "http://[틀림"                                              true   된다     link
 h15 (속성 없음)                                       ""                                                        false  안 됨    generic
(exit 0)
```

```text
  href 한 글자가 풀리는 길

  문서 URL   http://127.0.0.1:18713/d/html13b-16-href.html
                                    ~~
  "b.html"           ->  http://127.0.0.1:18713/d/b.html          같은 폴더
  "../b.html"        ->  http://127.0.0.1:18713/b.html            한 단계 위
  "/b.html"          ->  http://127.0.0.1:18713/b.html            출처의 뿌리
  "?q=1"             ->  …/d/html13b-16-href.html?q=1            경로 유지, 질의만 교체
  "#끝"              ->  …/d/html13b-16-href.html#%EB%81%9D      ★ 글자가 퍼센트 인코딩
  ""                 ->  …/d/html13b-16-href.html                 ★ 자기 자신
  "//127.0.0.1:18714/b.html" -> http://127.0.0.1:18714/b.html    ★ 스킴만 빌려 온다
  "HTTP://…/x/../%7Euser/b.html" -> http://…/%7Euser/b.html     스킴 소문자 · 점 경로 접힘
  "  b.html  "       ->  …/d/b.html                               앞뒤 공백을 버린다
  "http://[틀림"      ->  "http://[틀림"                            ★ 못 풀면 글자 그대로
  (속성 없음)         ->  ""                                       ★ 링크가 아니다
```

- ★★★ **`a.href` 는 속성 글자가 아니라 해석한 URL 이다.** 상대 형태는 **문서 URL 기준**으로 풀리고, 스킴은 소문자가 되고, `x/../` 는 접히고, 앞뒤 공백은 버려진다.
- ★★ **빈 문자열 `href=""` 는 「자기 자신」** 이다 — 누르면 **같은 문서를 다시 연다.** 「아무 데도 안 가는 링크」가 아니다.
- ★★ **`#끝` 은 `#%EB%81%9D`** — 조각의 한글이 **퍼센트 인코딩**됐다. 조각이 무엇을 찾나는 [07번 주제](../07-id-and-fragments/2-summary.md)가 정본이다.
- ★ **프로토콜 상대 `//host/…` 는 문서의 스킴(`http:`)만 빌려 온다.**
- ★ **틀린 URL(`http://[틀림`)은 `a.href` 가 속성 글자를 그대로 준다** — 명세의 `href` getter — 「url 이 null 이고 `href` 속성이 없으면 빈 문자열, **url 이 null 이면 `href` 속성 값을 돌려준다**」 — 그대로다. **그래도 `:link` 는 참이고 포커스도 되고 역할도 `link`** 다 — 「틀린 링크」도 링크다.
- ★★★ **`href` 가 없는 `<a>`(`h15`)만 전부 다르다** — `:link` 거짓 · **포커스 안 됨** · 역할 **`generic`**. HTML-AAM 도 「`href` 없는 `a` → `generic`」이다. **`href` 가 있어야 링크다.**
- **`javascript:`·`mailto:` 는 그대로** — 이미 절대 URL 이라 풀 것이 없다. 역할은 둘 다 `link` 다.

같은 실행에서 서버가 받은 것은 **문서 한 줄뿐**이다 — favicon 요청이 없다(흔들리는 칸 표의 「고정했다」).

```text
$ python3 html13b-link.py page d/html13b-16-href.html | sed -n '30,$p'
서버 A GET /d/html13b-16-href.html  Referer=(없음)
(exit 0)
```

```text
$ python3 html13b-link.py page d/html13b-16-href.html | sed -n '20,21p'
해석해도 글자가 그대로인 칸 = #h9 · #h12 · #h13 · #h14
그대로인 칸 = 4 / 14
(exit 0)
```

- ★ **「해석해도 글자가 그대로」인 칸은 14 중 4다** — 이미 절대 URL 인 셋(`h9`·`h12`·`h13`)과 **못 푼 하나**(`h14`). 나머지 열은 **전부 바뀌었다** — `href` 를 **읽은 글자로 비교하면 안 되는** 이유다.

### (2) 창 ② — 브라우저가 스스로 말하는 「처리하는 `rel`」

**언제 쓰나** — `nofollow` 가 브라우저에서 무엇을 하는지 **재기 전에** 브라우저에게 묻는 자리.

(1) 과 같은 실행의 뒷부분이다.

```text
$ python3 html13b-link.py page d/html13b-16-href.html | sed -n '23,29p'
rel 의 지원 토큰 — a.relList.supports()
  noopener   true
  noreferrer true
  opener     true
  nofollow   false
  stylesheet false
  zzz        false
(exit 0)
```

- ★★★ **`relList.supports()` 가 참인 것은 `noopener`·`noreferrer`·`opener` 셋뿐이다.** `nofollow` 는 **거짓**이다.
- ★★ 명세가 이 셋을 정확히 적어 둔다 — 「`rel` 의 지원 토큰은 **처리 모델에 영향을 주고** UA 가 지원하는 것들이다. **가능한 지원 토큰은 `noreferrer`·`noopener`·`opener`**」. 즉 **`supports()` 가 거짓이면 브라우저에게 그 토큰의 처리 모델이 없다.**
```text
  rel 토큰을 브라우저가 어떻게 대하나

  토큰          relList.supports   처리 모델   (3) 의 행동
  noopener      true               있다        이름 target 에서 opener 를 끊는다
  noreferrer    true               있다        Referer 를 지우고 opener 도 끊는다
  opener        true               있다        _blank 의 기본을 되돌린다
  nofollow      false              없다        0 / 3 — 아무것도 안 바뀐다
  stylesheet    false              (a 에는)    —
  zzz           false              없다        —

  supports() 가 참인 토큰 = 명세가 적은 「가능한 지원 토큰」 셋과 정확히 같다.
```

- ★ **`stylesheet` 도 거짓**이다 — `<a>` 에서는 뜻이 없다(`<link>` 의 토큰이다).
- ★★ **그래서 `nofollow` 는 「잴 것이 없다」** — 브라우저가 스스로 「**처리하지 않는다**」고 답했다. (3) 의 서버 로그가 그것을 **행동으로** 한 번 더 확인한다.

### (3) 창 ⑤ + 새 창 — `rel` 열세 조합을 하나씩 눌렀다

**언제 쓰나** — 이 주제의 본체. **「`rel` 이 무엇을 바꾸나」를 요청 한 줄과 새 창 한 줄로** 답한다.

원래 창(A)에서 링크를 **하나씩** 실제 마우스로 누르고, 서버가 받은 줄과 **새 문서 쪽에서 찍은** `window.opener`·`document.referrer` 를 적었다. 새 창은 CDP 자동 부착 + **디버거 대기**로 붙잡아 `load` 이벤트를 받은 뒤에 물었다.

```html
<!-- html13b-16-rel.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>16 rel 격자</title>
</head>
<body>
<p><a id="none" target="_blank" href="/html13b-16-dest.html?k=none">rel 없음</a></p>
<p><a id="noopener" target="_blank" rel="noopener" href="/html13b-16-dest.html?k=noopener">noopener</a></p>
<p><a id="noreferrer" target="_blank" rel="noreferrer" href="/html13b-16-dest.html?k=noreferrer">noreferrer</a></p>
<p><a id="nofollow" target="_blank" rel="nofollow" href="/html13b-16-dest.html?k=nofollow">nofollow</a></p>
<p><a id="opener" target="_blank" rel="opener" href="/html13b-16-dest.html?k=opener">opener</a></p>
<p><a id="policy" target="_blank" referrerpolicy="no-referrer" href="/html13b-16-dest.html?k=policy">referrerpolicy=no-referrer</a></p>
<p><a id="cross" target="_blank" href="http://127.0.0.1:18714/html13b-16-dest.html?k=cross">다른 출처 · rel 없음</a></p>
<p><a id="crossopener" target="_blank" rel="opener" href="http://127.0.0.1:18714/html13b-16-dest.html?k=crossopener">다른 출처 · rel=opener</a></p>
<p><a id="named" target="창이름1" href="/html13b-16-dest.html?k=named">target=창이름1 · rel 없음</a></p>
<p><a id="namednoopener" target="창이름2" rel="noopener" href="/html13b-16-dest.html?k=namednoopener">target=창이름2 · noopener</a></p>
<p><a id="namednoref" target="창이름3" rel="noreferrer" href="/html13b-16-dest.html?k=namednoref">target=창이름3 · noreferrer</a></p>
<p><a id="namedpolicy" target="창이름4" referrerpolicy="no-referrer" href="/html13b-16-dest.html?k=namedpolicy">target=창이름4 · referrerpolicy=no-referrer</a></p>
<p><a id="self" href="/html13b-16-dest.html?k=self">target 없음 (같은 탭)</a></p>
</body>
</html>
```

```html
<!-- html13b-16-dest.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>도착</title>
</head>
<body>
<p>도착한 쪽</p>
</body>
</html>
```

```text
$ python3 html13b-link.py rel | sed -n '1,39p'
[_blank · rel 없음]
  서버 A GET /html13b-16-dest.html?k=none  Referer=http://127.0.0.1:18713/html13b-16-rel.html
  새 문서  window.opener = null · document.referrer = http://127.0.0.1:18713/html13b-16-rel.html
[_blank · noopener]
  서버 A GET /html13b-16-dest.html?k=noopener  Referer=http://127.0.0.1:18713/html13b-16-rel.html
  새 문서  window.opener = null · document.referrer = http://127.0.0.1:18713/html13b-16-rel.html
[_blank · noreferrer]
  서버 A GET /html13b-16-dest.html?k=noreferrer  Referer=(없음)
  새 문서  window.opener = null · document.referrer = (빈 문자열)
[_blank · nofollow]
  서버 A GET /html13b-16-dest.html?k=nofollow  Referer=http://127.0.0.1:18713/html13b-16-rel.html
  새 문서  window.opener = null · document.referrer = http://127.0.0.1:18713/html13b-16-rel.html
[_blank · opener]
  서버 A GET /html13b-16-dest.html?k=opener  Referer=http://127.0.0.1:18713/html13b-16-rel.html
  새 문서  window.opener = 창 객체 · document.referrer = http://127.0.0.1:18713/html13b-16-rel.html
[_blank · referrerpolicy=no-referrer]
  서버 A GET /html13b-16-dest.html?k=policy  Referer=(없음)
  새 문서  window.opener = null · document.referrer = (빈 문자열)
[_blank · 다른 출처]
  서버 B GET /html13b-16-dest.html?k=cross  Referer=http://127.0.0.1:18713/
  새 문서  window.opener = null · document.referrer = http://127.0.0.1:18713/
[_blank · 다른 출처 · opener]
  서버 B GET /html13b-16-dest.html?k=crossopener  Referer=http://127.0.0.1:18713/
  새 문서  window.opener = 창 객체 · document.referrer = http://127.0.0.1:18713/
[target=창이름1 · rel 없음]
  서버 A GET /html13b-16-dest.html?k=named  Referer=http://127.0.0.1:18713/html13b-16-rel.html
  새 문서  window.opener = 창 객체 · document.referrer = http://127.0.0.1:18713/html13b-16-rel.html
[target=창이름2 · noopener]
  서버 A GET /html13b-16-dest.html?k=namednoopener  Referer=http://127.0.0.1:18713/html13b-16-rel.html
  새 문서  window.opener = null · document.referrer = http://127.0.0.1:18713/html13b-16-rel.html
[target=창이름3 · noreferrer]
  서버 A GET /html13b-16-dest.html?k=namednoref  Referer=(없음)
  새 문서  window.opener = null · document.referrer = (빈 문자열)
[target=창이름4 · referrerpolicy=no-referrer]
  서버 A GET /html13b-16-dest.html?k=namedpolicy  Referer=(없음)
  새 문서  window.opener = 창 객체 · document.referrer = (빈 문자열)
[같은 탭 · rel 없음]
  서버 A GET /html13b-16-dest.html?k=self  Referer=http://127.0.0.1:18713/html13b-16-rel.html
  새 문서  window.opener = null · document.referrer = http://127.0.0.1:18713/html13b-16-rel.html
(exit 0)
```

- ★★★ **링크마다 요청은 정확히 한 줄이다** — 서버 로그가 그것을 보증한다.
```text
  명세 「요소의 noopener 구하기」 — 위에서부터 먼저 걸리는 줄이 답이다

  ① rel 에 noopener 나 noreferrer 가 있나?             예 -> noopener 참
  ② rel 에 opener 가 없고 target 이 _blank 인가?       예 -> noopener 참   ★ _blank 의 기본
  ③ blob URL 인데 출처가 같은 사이트가 아닌가?          예 -> noopener 참
  ④ 그 밖                                              -> noopener 거짓 (opener 를 준다)

  target="창이름1"  (rel 없음)   ①X ②X(_blank 아님) ③X  -> ④  opener 를 준다
  target="_blank" rel="opener"  ①X ②X(opener 있음) ③X  -> ④  opener 를 준다
```

- ★★★ **`_blank · rel 없음` 의 `window.opener` 는 `null` 이다.** `rel="noopener"` 를 안 썼는데도. 명세의 「요소의 noopener 구하기」 알고리즘 둘째 줄 — 「**링크 타입에 `opener` 가 없고 target 이 `_blank` 면 참을 돌려준다**」 — 을 이 판이 그대로 따랐다.
- ★★ **그래서 `_blank · noopener` 는 `rel 없음` 과 한 칸도 안 갈린다**(아래 표 0 / 3). **`noopener` 가 일을 하는 자리는 `_blank` 가 아닌 이름 target 이다** — `창이름1`(rel 없음)은 「**창 객체**」, `창이름2`(noopener)는 **`null`**.
- ★★★ **`noreferrer` 는 요청에서 `Referer` 를 지웠다** — 서버 로그에 `Referer=(없음)`. 새 문서의 `document.referrer` 도 빈 문자열이다. 그리고 **`noopener` 까지 함께** — 이름 target(`창이름3`)에서도 `null` 이다. 명세 — 「`noreferrer` 는 … **`noopener` 의 동작도 함의한다**」.
- ★★ **`referrerpolicy="no-referrer"` 는 `Referer` 만 지운다** — 이름 target(`창이름4`)에서 **`window.opener` 가 「창 객체」로 남았다.** `noreferrer` 와 **한 칸이 갈린다**(아래 표 1 / 3).
- ★★ **`rel="opener"` 가 `_blank` 의 기본을 되돌린다** — `window.opener` 가 「창 객체」다. **다른 출처로 가도**(`crossopener`) 쥔다.
- ★★ **다른 출처(B)로는 `Referer` 가 출처만 간다** — `http://127.0.0.1:18713/`, 경로가 없다. Referrer Policy 명세의 **기본 정책이 `strict-origin-when-cross-origin`** 이고, 링크에 `referrerpolicy` 를 안 쓰면 그 기본이 쓰인다. ★ **정책 이름은 명세, 그 결과가 이 판에서 이렇게 보인 것은 관찰**이다.
- ★ **`nofollow` 는 세 칸 다 `rel 없음` 과 같다** — (2) 의 「처리 모델이 없다」가 **행동으로도** 확인됐다.

```text
$ python3 html13b-link.py rel | sed -n '41,$p'
링크                                          서버가 받은 Referer                                document.referrer                             window.opener
_blank · rel 없음                             http://127.0.0.1:18713/html13b-16-rel.html    http://127.0.0.1:18713/html13b-16-rel.html    null
_blank · noopener                           http://127.0.0.1:18713/html13b-16-rel.html    http://127.0.0.1:18713/html13b-16-rel.html    null
_blank · noreferrer                         (없음)                                          (빈 문자열)                                       null
_blank · nofollow                           http://127.0.0.1:18713/html13b-16-rel.html    http://127.0.0.1:18713/html13b-16-rel.html    null
_blank · opener                             http://127.0.0.1:18713/html13b-16-rel.html    http://127.0.0.1:18713/html13b-16-rel.html    창 객체
_blank · referrerpolicy=no-referrer         (없음)                                          (빈 문자열)                                       null
_blank · 다른 출처                              http://127.0.0.1:18713/                       http://127.0.0.1:18713/                       null
_blank · 다른 출처 · opener                     http://127.0.0.1:18713/                       http://127.0.0.1:18713/                       창 객체
target=창이름1 · rel 없음                        http://127.0.0.1:18713/html13b-16-rel.html    http://127.0.0.1:18713/html13b-16-rel.html    창 객체
target=창이름2 · noopener                      http://127.0.0.1:18713/html13b-16-rel.html    http://127.0.0.1:18713/html13b-16-rel.html    null
target=창이름3 · noreferrer                    (없음)                                          (빈 문자열)                                       null
target=창이름4 · referrerpolicy=no-referrer    (없음)                                          (빈 문자열)                                       창 객체
같은 탭 · rel 없음                               http://127.0.0.1:18713/html13b-16-rel.html    http://127.0.0.1:18713/html13b-16-rel.html    null

「_blank · rel 없음」과 갈린 칸 — _blank · nofollow                           0 / 3
「_blank · rel 없음」과 갈린 칸 — _blank · noopener                           0 / 3
「_blank · rel 없음」과 갈린 칸 — _blank · noreferrer                         2 / 3
「_blank · rel 없음」과 갈린 칸 — _blank · opener                             1 / 3
「_blank · rel 없음」과 갈린 칸 — _blank · referrerpolicy=no-referrer         2 / 3
「target=창이름1 · rel 없음」과 갈린 칸 — target=창이름2 · noopener                      1 / 3
「target=창이름1 · rel 없음」과 갈린 칸 — target=창이름3 · noreferrer                    3 / 3
「target=창이름1 · rel 없음」과 갈린 칸 — target=창이름4 · referrerpolicy=no-referrer    2 / 3
「target=창이름3 · noreferrer」과 갈린 칸 — target=창이름4 · referrerpolicy=no-referrer    1 / 3
갈린 칸 = 12 / 27
(exit 0)
```

```text
  rel 이 바꾸는 칸 (서버 Referer · document.referrer · window.opener)

                        Referer    referrer   opener
  _blank (rel 없음)      전체 URL   전체 URL   null      <- 기준
  _blank noopener        =          =          =         0 / 3   이미 기본이다
  _blank nofollow        =          =          =         0 / 3   브라우저가 안 읽는다
  _blank noreferrer      없음       ""         =         2 / 3
  _blank no-referrer 정책  없음      ""         =         2 / 3
  _blank opener          =          =          창 객체   1 / 3

  target=이름 (rel 없음)  전체 URL   전체 URL   창 객체   <- 기준 (이름 target 은 열쇠를 준다)
  이름 noopener          =          =          null      1 / 3
  이름 noreferrer        없음       ""         null      3 / 3   ★ 셋 다
  이름 no-referrer 정책   없음       ""         창 객체   2 / 3   ★ 열쇠는 그대로

                                                  갈린 칸 = 12 / 27
```

> **출처(origin)** — 스킴 + 호스트 + 포트. 포트만 달라도 **다른 출처**다.\
> 예: `127.0.0.1:18713` 과 `127.0.0.1:18714`.

> **보조 브라우징 맥락(auxiliary browsing context)** — 다른 창이 열어서 **여는 쪽과 관계가 이어진** 창. `rel="opener"` 가 그것을 만든다.

### (4) 창 ⑤ — `download` 는 다른 출처에서 무시된다

**언제 쓰나** — 「내려받기 버튼」을 링크로 만들 때.

같은 파일(`html13b-16-file.txt`)을 **같은 출처(A)** 와 **다른 출처(B)** 에 두고 `download="저장한-이름.txt"` 를 달았다. 비교로 **`download` 없는** 같은 출처 링크와 **`javascript:` URL** 을 하나 더 두었다. 내려받기는 CDP 의 `Browser.downloadWillBegin` 이벤트로, 이동은 `Page.frameNavigated` 로 받았다 — **둘 중 먼저 오는 쪽**을 결과로 적는다.

```html
<!-- html13b-16-dl.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>16 download</title>
</head>
<body>
<p><a id="same" href="/html13b-16-file.txt?k=same" download="저장한-이름.txt">같은 출처 · download 있음</a></p>
<p><a id="cross" href="http://127.0.0.1:18714/html13b-16-file.txt?k=cross" download="저장한-이름.txt">다른 출처 · download 있음</a></p>
<p><a id="plain" href="/html13b-16-file.txt?k=plain">같은 출처 · download 없음</a></p>
<p><a id="js" href="javascript:document.title='javascript: 가 돌았다'">javascript: URL</a></p>
</body>
</html>
```

```text
$ python3 html13b-link.py download
[같은 출처 · download 있음]
  서버 A GET /html13b-16-file.txt?k=same  Referer=http://127.0.0.1:18713/html13b-16-dl.html
  결과  내려받기 · suggestedFilename = 저장한-이름.txt · 저장된 파일 = ['저장한-이름.txt']
[다른 출처 · download 있음]
  서버 B GET /html13b-16-file.txt?k=cross  Referer=http://127.0.0.1:18713/
  결과  이 탭이 이동했다 · http://127.0.0.1:18714/html13b-16-file.txt?k=cross · 본문 = "받아 갈 글자 파일\n"
[같은 출처 · download 없음]
  서버 A GET /html13b-16-file.txt?k=plain  Referer=http://127.0.0.1:18713/html13b-16-dl.html
  결과  이 탭이 이동했다 · http://127.0.0.1:18713/html13b-16-file.txt?k=plain · 본문 = "받아 갈 글자 파일\n"
[javascript: URL]
  document.title = javascript: 가 돌았다
  location.href  = http://127.0.0.1:18713/html13b-16-dl.html
  서버 요청 = 0줄
(exit 0)
```

- ★★★ **같은 출처의 `download` 는 들어졌다** — 내려받기가 시작됐고 **파일 이름이 `download` 값**(`저장한-이름.txt`)이다. 서버 요청은 한 줄이다.
- ★★★ **다른 출처의 `download` 는 무시됐다** — 내려받지 않고 **이 탭이 그 파일로 이동**해 글자를 보여 줬다. 서버 B 가 요청을 받은 것도 한 줄이다 — **요청은 갔는데 처리 방식이 바뀐** 것이다.
- ★★ **명세는 「무시하라」고 하지 않는다.** 명세 — 「교차 출처에서는 `download` 속성을 **`Content-Disposition: attachment` 헤더와 함께 써야** 사용자가 **수상한 동작이라는 경고를 받지 않는다**」. 즉 명세의 그림은 「**경고**」이고, **「무시하고 이동」은 Chrome 의 선택**이다(구현).
- **`download` 없는 같은 출처 링크는 이동한다** — 다른 출처 `download` 와 **결과가 같다.** 그래서 **다른 출처에서 `download` 는 없는 것과 같다.**
- ★ **`javascript:` URL 은 스크립트를 돌렸고**(`document.title` 이 바뀌었다) **이동도 요청도 없었다** — 서버 요청 **0줄**, `location.href` 그대로.

```text
  download 가 가는 두 길

  같은 출처   A 문서 ── <a download> ──> A 파일    내려받기 ★ 이름 = download 값
  다른 출처   A 문서 ── <a download> ──> B 파일    이동    ★ download 를 무시 (Chrome)
                                                           명세는 「Content-Disposition 없이는 경고」까지만 말한다
```

### (5) 창 ⑦ — `rel`·`download` 는 접근성 트리에 흔적이 없다

```text
$ python3 html13b-link.py ax html13b-16-dl.html
RootWebArea    이름='16 download'
  paragraph      이름=''
    link           이름='같은 출처 · download 있음' url=http://127.0.0.1:18713/html13b-16-file.txt?k=same
      StaticText     이름='같은 출처 · download 있음'
  paragraph      이름=''
    link           이름='다른 출처 · download 있음' url=http://127.0.0.1:18714/html13b-16-file.txt?k=cross
      StaticText     이름='다른 출처 · download 있음'
  paragraph      이름=''
    link           이름='같은 출처 · download 없음' url=http://127.0.0.1:18713/html13b-16-file.txt?k=plain
      StaticText     이름='같은 출처 · download 없음'
  paragraph      이름=''
    link           이름='javascript: URL' url=javascript:document.title='javascript: %EA%B0%80 %EB%8F%8C%EC%95%98%EB%8B%A4'
      StaticText     이름='javascript: URL'
(exit 0)
```

- **네 링크가 전부 `link` 에 이름 = 글자, `url` = 해석한 URL** 이다. `download` 가 있든 없든, 같은 출처든 다른 출처든 **같은 모양**이다.
- ★ HTML-AAM 도 `download`·`rel` 을 「**대응 없음**」(모든 플랫폼 칸이 「Not mapped」)으로 적는다. **보조 기술은 「이 링크는 내려받기다」를 트리에서 알 수 없다** — 알리고 싶으면 **글자로** 적는다.
- ★ `javascript:` 링크의 `url` 도 해석된 글자다 — 한글이 **퍼센트 인코딩**돼 있다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다. 쓰는 꼴은 (1)·(3)·(4) 의 소스가 전부 실제로 던진 형태다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 새 창으로 열기 | `target="_blank"` | ★ **`window.opener` 가 `null`** — `noopener` 를 안 써도 |
| 새 창이 원래 창을 쥐게 | `target="_blank" rel="opener"` | `window.opener` = 창 객체 |
| 유입 경로를 안 남기기 | `rel="noreferrer"` | `Referer` 없음 + **`noopener` 까지** |
| 유입 경로만 안 남기기(열쇠는 그대로) | `referrerpolicy="no-referrer"` | `Referer` 없음 · 이름 target 에서 **opener 남음** |
| 검색 엔진에 「추천 아님」 | `rel="nofollow"` | ★ **브라우저 동작 0칸** — 검색 엔진 쪽은 **못 잰다** |
| 내려받게 | `download="이름"` | **같은 출처에서만** — 다른 출처는 이동 |
| 링크가 아닌 `<a>` | `href` 없음 | `generic` · 포커스 안 됨 · `:link` 아님 |

### 어디서 헷갈리나

- **`noopener` 는 「보안 옵션」이 아니라 「열쇠를 주지 마라」다.** `_blank` 에서는 **이미 기본**이다. 효과가 있는 것은 **이름 target** 이다.
- **`noreferrer` ⊃ `noopener`.** `noreferrer` 하나면 둘 다 된다. 반대로 **`referrerpolicy="no-referrer"` 는 `noopener` 를 안 준다.**
- **`href=""` 는 빈 링크가 아니다** — 자기 자신으로 간다.
- **`href` 없는 `<a>` 는 링크가 아니다** — 「버튼처럼 쓰는 `<a>`」의 뿌리가 여기다. 링크와 버튼이 갈리는 기준은 **「어디로 가나(`href`)」 대 「무엇을 하나(동작)」** — 동작이면 `<button>` 이다. 그 네이티브 차이는 목록의 **41번 주제**가 정본이다.
- **`download` 는 파일 이름 제안**이다 — 다른 출처면 **이름도 내려받기도 없다.**

## 어디서 틀리나

### 1. `_blank` 마다 `rel="noopener"` 를 붙여야 안전하다고 믿는다

**이 판에서는 붙여도 한 칸도 안 바뀐다**((3) — 0 / 3). `_blank` 가 이미 `noopener` 다.\
★ 붙여서 해가 되지는 않는다. 다만 **효과를 기대하는 자리가 틀렸다** — 이름 target 에 붙여야 일을 한다.

### 2. `target="창이름"` 도 `_blank` 처럼 안전한 줄 안다

**아니다.** 이름 target 은 **`window.opener` 를 준다**((3) 의 `창이름1`). 기본 `noopener` 는 **`_blank` 에만** 걸린다.

```text
  target 값에 따라 기본이 갈린다 (rel 없이)

  target="_blank"      window.opener = null      <- 명세 ② 줄
  target="창이름1"      window.opener = 창 객체   <- ② 줄에 안 걸린다
  target 없음 (같은 탭) window.opener = null      <- 새 창이 아니다
```

### 3. `referrerpolicy="no-referrer"` 로 `noreferrer` 를 대신한다

**`Referer` 만 같다.** 이름 target 에서 **opener 가 남는다**((3) 의 `창이름4` — `noreferrer` 와 1 / 3).

### 4. `nofollow` 가 브라우저에서 무언가를 바꾼다고 여긴다

**바꾸지 않는다.** `relList.supports('nofollow')` 가 **거짓**이고((2)) 행동도 0 / 3 이다((3)).\
★ 「검색 엔진이 따라가지 않는다」는 **이 머신에서 잴 수 없는 주장**이라 이 문서는 하지 않는다.

### 5. 다른 도메인의 파일에 `download` 를 달면 내려받아질 줄 안다

**이동한다**((4)). Chrome 이 **무시**한다. 내려받게 하려면 **서버가 `Content-Disposition: attachment`** 를 보내야 한다(명세의 문장) — 그 경로는 이 문서가 **던지지 않았다.**

### 6. `href` 를 속성 글자로 비교한다

`a.href` 는 **해석한 URL** 이라 14 중 10이 글자가 바뀐다((1)). `getAttribute('href')` 와 `a.href` 를 **섞어 비교하면** 같은 링크가 달라 보인다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 「요소의 noopener 구하기」 — `noopener`/`noreferrer` 면 참, **`opener` 가 없고 target 이 `_blank` 면 참** | (3) |
| **명세(HTML)** | `noreferrer` 는 `Referer` 를 안 보내고 **`noopener` 를 함의** | (3) |
| **명세(HTML)** | `rel` 의 지원 토큰은 **`noreferrer`·`noopener`·`opener` 뿐** | (2) |
| **명세(HTML)** | `nofollow` — 「원저자가 **보증하지 않는** 링크」라는 **주석** | (2)·(3) — 처리 모델이 없다 |
| **명세(HTML)** | 교차 출처 `download` 는 **`Content-Disposition` 과 함께 써야 경고가 안 난다** | (4) |
| **명세(Referrer Policy)** | 기본 정책 **`strict-origin-when-cross-origin`** | (3) 의 다른 출처 줄 |
| **명세(HTML-AAM)** | `a[href]` → `link` · `href` 없는 `a` → `generic` · `rel`·`download` → **대응 없음** | (1)·(5) |
| **명세(URL)** | 상대 URL 해석·점 경로 접기·퍼센트 인코딩 | (1) — ★ URL 명세 본문은 이 배치가 열어 보지 않았다 |
| **구현(Chrome)** | 교차 출처 `download` 를 **무시하고 이동** | (4) |
| **구현(Chrome)** | `javascript:` URL 이 **요청 없이** 스크립트를 돌린 것 | (4) |
| **이 판의 관찰** | 위 명세 줄들이 **그대로 동작했다**는 것 | (3) — 다른 엔진은 **미실행** |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **검색 엔진이 `nofollow` 를 따르는지** | 이 머신에 검색 엔진이 없다 — 「**못 잰 것**」. 브라우저 쪽은 「잴 것이 없다」로 끝났다 |
| **`window.opener` 로 원래 창을 바꾸는 공격**(tabnabbing) | 이 문서는 **참조가 있나 없나**까지 쟀다. 그 참조로 **무엇을 할 수 있나**는 스크립트 표면이라 던지지 않았다 |
| **`Content-Disposition` 을 보낸 교차 출처 `download`** | 서버가 그 헤더를 보내게 짜지 않았다 — **안 돌려 본 것** |
| **스크린리더가 「새 창에서 열림」·「내려받기」를 알리는지** | 보조 기술이 없다. 트리에는 흔적이 없었다((5)) |
| **다른 엔진의 `_blank` 기본 `noopener`** | 엔진이 하나뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **새 창은 `target="_blank"` 하나로 충분하다** — 열쇠는 기본으로 안 준다.
- **이름 target 을 쓸 때는 `rel="noopener"` 를 붙인다** — 거기서는 기본이 「준다」다.
- **유입 경로를 숨겨야 하면 `rel="noreferrer"`** — 열쇠까지 같이 안 준다. 유입 분석이 필요하면 붙이지 않는다.
- **`rel="opener"` 는 새 창이 원래 창과 정말 대화해야 할 때만.**
- **`nofollow` 는 검색 엔진용 메모**다 — 브라우저 동작을 기대하지 않는다.
- **내려받기는 같은 출처 파일에 `download`**, 다른 출처면 **서버의 `Content-Disposition`**.
- **동작이면 `<button>`, 이동이면 `<a href>`** — `href` 없는 `<a>` 는 링크가 아니다.

## 핵심 문장

1. **`a.href` 는 속성 글자가 아니라 해석한 URL 이다 — 열넷 중 열이 글자가 바뀐다.**
2. **`href` 없는 `<a>` 는 `:link` 도 포커스도 `link` 역할도 없다.**
3. **`target="_blank"` 는 `rel="opener"` 없이는 `noopener` 로 동작한다 — `window.opener` 가 `null` 이다.**
4. **`noopener` 가 일을 하는 자리는 이름 target 이다.**
5. **`noreferrer` 는 `Referer` 를 지우고 `noopener` 까지 준다 — `referrerpolicy="no-referrer"` 는 `Referer` 만 지운다.**
6. **다른 출처로는 `Referer` 가 출처만 간다 — 기본 정책 `strict-origin-when-cross-origin`.**
7. **`nofollow` 는 브라우저가 처리하지 않는 토큰이다 — `relList.supports` 가 거짓이고 행동도 0 / 3 이다.**
8. **다른 출처의 `download` 는 Chrome 이 무시하고 이동한다 — 명세는 「경고」까지만 말한다.**

## 관련 자료

- [07번 주제 — `id` 와 조각 식별자](../07-id-and-fragments/2-summary.md) — **`#fragment` 가 무엇을 찾나**의 정본이다. 여기는 **`href="#…"` 가 무엇으로 풀리나**까지.
- [`history/web/02-HTTP-진화.md`](../../../../../../history/web/02-HTTP-진화.md) — **HTTP 헤더·요청 모델의 진화**는 그쪽이다. ★ 그 문서에 **`Referer`·Referrer-Policy 절은 없다** — 이 주제의 `Referer` 는 서버 로그 관찰과 Referrer Policy 명세의 기본값 한 줄까지.
- 목록의 **38번 주제**(`iframe` 과 `referrerpolicy`) — **`referrerpolicy` 속성이 붙는 다른 자리**다.
- 목록의 **41번 주제**(네이티브 시맨틱이 주는 것) — **링크와 버튼이 무료로 주는 것의 차이**는 그쪽이 정본이다.
- 목록의 **51번 주제**(`http-equiv` 와 `referrer`) — **문서 전체의 Referrer 정책**을 메타로 주는 자리.
- 목록의 **53번 주제**(`link rel` 관계 지도) — **`rel` 토큰 전체 지도**는 그쪽. 여기는 `<a>` 에서 **처리 모델이 있는 셋 + `nofollow`** 까지.
- 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md)) — `window.open()`·`window.opener` 를 **스크립트로** 다루는 표면. ★ **지금 그 목록에 해당 주제가 없다.**

## 용어 풀이

- **`Referer` 헤더** — 요청이 어느 문서에서 왔나를 알리는 HTTP 헤더.
- **`document.referrer`** — 새 문서가 읽는 「나를 부른 문서」의 URL.
- **`window.opener`** — 새 창이 자기를 연 창을 쥔 참조. `null` 이면 못 쥔다.
- **`noopener` / `noreferrer` / `opener`** — 열쇠를 주지 마라 / 보낸 곳도 지우고 열쇠도 주지 마라 / 열쇠를 줘라.
- **`nofollow`** — 「보증하지 않는 링크」라는 주석. **브라우저의 처리 모델이 없다.**
- **지원 토큰(supported tokens)** — `relList.supports()` 가 참을 돌려주는 토큰. **UA 가 처리 모델을 구현한 것**만 든다.
- **출처(origin)** — 스킴 + 호스트 + 포트.
- **`strict-origin-when-cross-origin`** — 같은 출처에는 전체 URL, 다른 출처에는 **출처만**, 「신뢰할 수 있는 URL(HTTPS 류)에서 그렇지 않은 URL 로」 가는 요청에는 **안 보내는** 기본 Referrer 정책(Referrer Policy §3.7).
- **CDP 자동 부착(auto-attach) + 디버거 대기** — 새 창이 뜨는 순간 붙잡아 **스크립트가 돌기 전에** 멈춰 두는 방법. 이 주제가 새 창 쪽을 **시간 상수 없이** 읽은 수단이다.

## 더 들어가면

- **왜 `_blank` 의 기본이 바뀌었나** — ★ 이 단락은 **널리 알려진 경위를 옮긴 것이고 이 배치가 원문을 확인하지 않았다.** 새 창이 `window.opener.location` 을 바꿔 **원래 탭을 가짜 로그인 화면으로 갈아 끼우는** 공격(tabnabbing)이 알려졌고, `rel="noopener"` 를 **모두가 붙이게 하는 것**보다 **기본을 뒤집는 쪽**이 확실했다. 그 대가로 **정말 opener 가 필요한 곳**을 위해 `rel="opener"` 가 생겼다. ★ 이 문서는 공격 자체는 던지지 않았다.
- **`noreferrer` 가 왜 `noopener` 를 함의하나** — opener 가 있으면 새 창이 **`opener.location` 으로 원래 창의 URL 을 읽을 수 있어** 「보낸 곳을 숨긴다」가 무너진다(같은 출처일 때). 그래서 둘을 묶었다 — 명세가 「함의한다」고 적은 까닭으로 읽힌다(이 문장은 해석이다).
- **`Referer` 의 철자** — HTTP 초기 명세의 오타가 굳은 것으로 널리 알려져 있다(이 배치가 원문을 확인하지 않았다). 연혁은 HTTP 쪽 이야기지만 `history/web/02` 에는 아직 없다.
