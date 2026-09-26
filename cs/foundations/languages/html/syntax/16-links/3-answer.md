# html/syntax/16 — 링크: `href` 의 형태·`target`·`rel`(`noopener`/`noreferrer`/`nofollow`)·`download` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「Links」 절·[Referrer Policy](https://w3c.github.io/webappsec-referrer-policy/)·[HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)와 새 창 쪽 프로브다.** `rel` 이 바꾸는 것은 화면에 하나도 없다(A3·A4).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 전부 해석된 URL — 틀린 URL 만 글자 그대로, `href` 없는 `a` 만 링크가 아니다

**출력**

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

**왜 그런가**

- **`../b.html` → `http://127.0.0.1:18713/b.html`**, **`?q=1` → 문서 경로 + `?q=1`**, **`""` → 문서 URL 자신.** `a.href` 는 속성 글자가 아니라 **문서 URL 기준으로 해석한 결과**다.
- **`//127.0.0.1:18714/b.html` → `http:` 를 빌려 온다.** 대문자 스킴은 **소문자**, `x/../` 는 **접힌다.**
- ★ **`http://[틀림` → 글자 그대로**다. 명세 `href` getter — 「url 이 null 이면 `href` 속성 값을 돌려준다」. **`:link` 는 참**, 포커스도 되고 역할도 `link` 다 — 풀리지 않아도 링크다.
- ★★★ **`h15` 만 `:link` 거짓 · 포커스 안 됨 · `generic`.** `href` 가 있어야 링크다(HTML-AAM — 「`href` 없는 `a` → `generic`」).

### 2. `noopener`·`noreferrer`·`opener` 셋만 참 — 그대로인 칸 4 / 14

**출력**

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

```text
$ python3 html13b-link.py page d/html13b-16-href.html | sed -n '20,21p'
해석해도 글자가 그대로인 칸 = #h9 · #h12 · #h13 · #h14
그대로인 칸 = 4 / 14
(exit 0)
```

**왜 그런가**

- ★★★ **참은 셋뿐** — 명세가 「가능한 지원 토큰은 `noreferrer`·`noopener`·`opener`」라고 적은 그대로다. **`nofollow` 는 거짓** — 브라우저에게 **처리 모델이 없다.** `stylesheet` 는 `<a>` 의 토큰이 아니다.
- **그대로인 칸 4** — 이미 절대 URL 인 셋과 못 푼 하나. 나머지 열은 **글자가 바뀌었다.**

### 3. `null` · `Referer` 없음 · 출처만 · 0 칸

**출력**

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

**왜 그런가**

- ★★★ **`_blank · rel 없음` 의 `window.opener` 는 `null`** 이다. 명세 「요소의 noopener 구하기」 둘째 줄 — 「링크 타입에 **`opener` 가 없고** target 이 **`_blank`** 면 참」.
- ★★★ **`noreferrer` 는 서버 `Referer=(없음)`, `document.referrer` 빈 문자열.** 서버 로그가 「**처음부터 안 보냈다**」를 보인다.
- ★★ **다른 출처로는 `Referer=http://127.0.0.1:18713/`** — 경로 없이 **출처만.** Referrer Policy 의 기본 **`strict-origin-when-cross-origin`** 이 적용된 결과다.
- ★ **`nofollow` 는 0 칸** — 서버 `Referer`·`document.referrer`·`window.opener` 가 `rel 없음` 과 **한 글자도 같다.**
- **링크마다 서버 요청은 정확히 한 줄**이다.

### 4. 이름 target 은 열쇠를 준다 — 갈린 칸 = 12 / 27

**출력**

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

**왜 그런가**

- ★★ **`창이름1`(rel 없음) = 창 객체** — 이름 target 은 `_blank` 가 아니라 **기본 `noopener` 가 안 걸린다.**
- **`창이름2`(noopener) = `null`** — `noopener` 가 **일을 하는 자리가 여기**다.
- **`창이름3`(noreferrer) = `null`** — `noreferrer` 가 **`noopener` 를 함의**한다. `창이름1` 과 **3 / 3** 갈렸다.
- ★★ **`창이름4`(referrerpolicy=no-referrer) = 창 객체** — `Referer` 만 지우고 **열쇠는 준다.** `창이름3` 과 **1 / 3**(opener 칸) 갈렸다.
- ★★★ **갈린 칸 = 12 / 27** — 비교 아홉 쌍 × 세 칸. **0 인 쌍이 둘**(`_blank` 의 `noopener`·`nofollow`)이다 — 앞은 「**이미 기본**」, 뒤는 「**처리 모델이 없음**」으로 **0 의 이유가 다르다.**

### 5. 같은 출처는 내려받고, 다른 출처는 이동한다 — `javascript:` 는 요청 0줄

**출력**

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

**왜 그런가**

- ★★★ **같은 출처 — 내려받기, 파일 이름 `저장한-이름.txt`**(`download` 값).
- ★★★ **다른 출처 — 이 탭이 그 파일로 이동**했다. 서버 B 는 요청을 **한 줄 받았다** — 요청은 갔고 **처리 방식이 내려받기에서 이동으로 바뀐** 것이다.
- **`download` 없는 같은 출처 링크와 결과가 같다** — 다른 출처에서 `download` 는 **없는 것과 같다.**
- **`javascript:`** — `document.title` 이 바뀌었고 **`location.href` 그대로 · 서버 요청 0줄.** 스크립트만 돌았다.

### 6. opener 가 있으면 새 창이 원래 탭을 바꿀 수 있다

- ★ **`window.opener` 를 쥔 새 창은 `opener.location` 으로 원래 탭을 다른 페이지로 보낼 수 있다**(tabnabbing 이라 불리는 공격의 뼈대). ★ **이 문서는 그 공격을 던지지 않았다** — 쟀던 것은 **참조가 있나 없나**까지다.
- 명세 「요소의 noopener 구하기」 — ① **`noopener` 나 `noreferrer` 면 참** ② **`opener` 가 없고 target 이 `_blank` 면 참** ③ blob URL 의 출처 조건 ④ 아니면 거짓. **`_blank` 는 ② 줄**이다.
- **`rel="opener"` 는 ② 를 끄는 스위치**다 — 기본을 뒤집었으니 **정말 opener 가 필요한 곳**을 위한 길이 따로 있어야 했다(A3 의 `_blank · opener` = 창 객체).
- ★ **「예전에는 `_blank` 가 opener 를 줬다」는 경위는 이 판에서 확인할 수 없다**(옛 판이 없다) — 명세의 현재 알고리즘과 이 판의 동작만이 근거다.

### 7. 브라우저 쪽은 「잴 것이 없다」, 검색 엔진 쪽은 「못 잰 것」

- ★★ **「잴 것이 없다」(제4의 상태)** 다 — 근거 둘. ① **브라우저가 스스로 「처리하지 않는다」고 답했다**(`relList.supports('nofollow')` → `false`, A2). ② **행동도 0 / 3**(A3). 「재 봤더니 같았다」보다 강하다 — **같을 수밖에 없는 이유를 브라우저가 밝혔기** 때문이다.
- **「검색 엔진이 따라가지 않는다」는 「못 잰 것」(제3의 상태)** 이다. 동작은 **이 머신 밖**에 있고 잴 도구가 없다.
- **섞으면** 「브라우저가 `nofollow` 를 처리한다」(틀림)나 「`nofollow` 는 아무 효과가 없다」(잴 수 없는 단정) 중 하나가 된다. 이 문서는 **둘 다 적지 않는다.**

### 8. `_blank` 에서는 0 칸, 이름 target 에서는 1 칸 — `noreferrer` 는 `noopener` 를 함의한다

- **`_blank` 에서는 0 칸** — `_blank` 가 이미 `noopener` 라 opener 칸이 둘 다 `null` 이다(A4 의 표에서 두 줄이 같다). **이름 target 에서는 1 칸**(opener).
- 명세 — 「`noreferrer` 는 링크를 따라갈 때 **리퍼러 정보를 새지 않게** 하고, **같은 조건에서 `noopener` 동작도 함의한다**」.
- ★ **서버 로그가 더 강한 이유** — `document.referrer` 가 비어 있는 것만으로는 「**헤더는 보냈는데 새 문서에 안 넘긴 것**」과 「**처음부터 안 보낸 것**」이 구분되지 않는다. 서버 로그의 `Referer=(없음)` 은 **뒤쪽**임을 보인다.

### 9. `href` 가 없으면 링크의 세 가지를 다 잃는다

- **`href` 없는 `<a>`** — `:link` 거짓 · **포커스 안 됨** · 역할 **`generic`**(A1 의 `h15`). 키보드로 닿지도 않고 보조 기술에게 링크로 안 보인다.
- **`href="#"`·`href="javascript:…"`** — **링크로는 남는다**(`link` 역할·포커스). ★ 그런데 **역할이 틀린다** — 보조 기술은 「링크」로 알리는데 누르면 **이동하지 않고 동작**을 한다. `href="#"` 는 A1 의 해석대로 **자기 문서의 빈 조각**으로 가고, `javascript:` 는 A5 처럼 **이동 없이 스크립트만** 돈다.
- **기준 — 「어디로 가나」면 `<a href>`, 「무엇을 하나」면 `<button>`.** 둘의 네이티브 차이(키보드·역할·폼)는 목록의 **41번 주제**가 정본이다.

### 10. 이동은 구현, 출처만은 명세의 기본 정책, 다른 엔진은 미실행

- ★★ **구현(Chrome)** 이다. 명세는 「교차 출처에서는 `download` 를 **`Content-Disposition: attachment` 와 함께 써야** 사용자가 **수상한 동작이라는 경고를 받지 않는다**」까지만 적는다 — **「경고」의 그림**이지 「무시하고 이동」이 아니다.
- **출처만 간 것 — 명세(Referrer Policy)의 기본 정책 `strict-origin-when-cross-origin`.** 링크에 `referrerpolicy` 가 없으면 이것이 쓰인다. 결과는 **이 판의 관찰**이다.
- ★★ **못 적는다.** 알고리즘은 명세에 있지만 **다른 엔진이 구현했는지는 미실행**이다. 적을 수 있는 것은 「**명세가 그렇게 정했고, Chrome 151 이 그대로 동작했다**」 둘이다.

### 11. 정본 경계

- **HTTP 헤더·요청 모델** — [`history/web/02-HTTP-진화.md`](../../../../../../history/web/02-HTTP-진화.md). ★ **`Referer`·Referrer-Policy 절은 없다**(grep 확인).
- **`#fragment`** — [07번 주제](../07-id-and-fragments/2-summary.md).
- **`rel` 토큰 전체 지도** — 목록의 **53번 주제**.
- **`window.opener` 의 스크립트 표면** — 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md)). ★ **지금 해당 주제가 없다.**

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.**\
★ **서버 둘은 하네스 프로세스 안의 스레드**다 — `127.0.0.1:18713`(A)·`127.0.0.1:18714`(B). 파일은 이 주제의 소스 폴더에서 내준다. **로그는 「서버 · `GET` · 경로 · `Referer`」 네 칸**만 적는다(시각·클라이언트 포트는 안 적는다).

**하네스** — [13번 주제](../13-phrasing-semantics/3-answer.md)의 `html13b-cdp.py`(CDP 연결·`ax_of`·`dump_tree`)를 **불러 쓰고**, 링크 전용 실행기를 새로 짰다.
★★ **이 실행기를 짜며 겪은 교착 둘** — 둘 다 「**타이밍에 기대지 않는다**」를 지키려다 드러났다.
① **새 창의 `Page.enable` 이 대답하지 않는다** — 자동 부착의 **디버거 대기**로 멈춘 창은 `runIfWaitingForDebugger` 전까지 명령에 답하지 않는다. 그래서 **응답을 기다리지 않고 보낸다**(`post`).
② **`rel=opener` 링크에서 `mouseReleased` 가 돌아오지 않는다** — 마우스 입력도 응답을 안 기다리고 보내게 고쳤다. ★ **관찰은 「opener 를 준 링크에서만 막혔다」까지**다(나머지 링크는 안 막혔다). 「opener 관계인 새 창이 **같은 렌더러**에 떠서, 디버거 대기로 멈춘 그 창이 원래 창의 입력 응답까지 막았다」는 **해석**이다 — 프로세스 배치를 직접 찍지 않았다.

```python
# html13b-link.py
#!/usr/bin/env python3
"""16 링크 — 창 ⑤(서버 요청 로그)를 본체로, 창 ⑦·새 창 쪽 프로브를 곁들인다.

사용: html13b-link.py rel | download | page <경로> | ax <경로>
  · 서버 둘을 이 프로세스 안에 띄운다 — 127.0.0.1:18713(A) 와 127.0.0.1:18714(B). 포트가 달라 **다른 출처**다.
  · 서버 로그는 「어느 서버 · 경로 · Referer 헤더」만 적는다. 시각·포트 추첨·클라이언트 포트는 안 적는다.
  · 링크는 CDP 의 실제 마우스 입력으로 누른다(스크립트의 a.click() 이 아니다).
  · 기다림은 전부 이벤트다 — 새 창은 자동 부착 + 디버거 대기로 붙잡은 뒤 loadEventFired 를 받는다.
"""
import http.server, importlib.util, json, os, shutil, sys, threading

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp", os.path.join(HERE, "html13b-cdp.py"))
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)

LOG = []
LOCK = threading.Lock()


def server(label, port):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def do_GET(self):
            with LOCK:
                LOG.append(f"{label} GET {self.path}  Referer={self.headers.get('Referer', '(없음)')}")
            return super().do_GET()

        def log_message(self, *a):
            pass

    H.extensions_map = {**H.extensions_map, ".txt": "text/plain; charset=utf-8"}
    s = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def take_log():
    with LOCK:
        out = LOG[:]
        LOG.clear()
    return out


def click(c, sid, selector):
    box = cdp.evaluate(c, sid, f"""(() => {{ const r = document.querySelector({json.dumps(selector)})
        .getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }})()""")
    # ★ 응답을 안 기다린다 — rel=opener 의 새 창은 같은 렌더러에서 디버거 대기로 멈춰 있어
    #   mouseReleased 의 응답이 그 창이 풀릴 때까지 안 온다(기다리면 교착이다)
    for t in ("mousePressed", "mouseReleased"):
        c.post("Input.dispatchMouseEvent", {"type": t, "x": box[0], "y": box[1], "button": "left",
               "clickCount": 1, "buttons": 1 if t == "mousePressed" else 0}, sid)


def goto(c, sid, url):
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)


def popup(c):
    """자동 부착된 새 창을 붙잡아 load 까지 기다린 뒤 세션을 돌려준다."""
    ev = c.wait("Target.attachedToTarget", pred=lambda p: p["targetInfo"]["type"] == "page"
                and p.get("waitingForDebugger"))
    s = ev["sessionId"]
    c.post("Page.enable", sid=s)
    c.post("Runtime.enable", sid=s)
    c.post("Runtime.runIfWaitingForDebugger", sid=s)
    c.wait("Page.loadEventFired", s)
    return s, ev["targetInfo"]["targetId"]


def rel(c, sid):
    rows = [("none", "_blank · rel 없음"), ("noopener", "_blank · noopener"),
            ("noreferrer", "_blank · noreferrer"), ("nofollow", "_blank · nofollow"),
            ("opener", "_blank · opener"), ("policy", "_blank · referrerpolicy=no-referrer"),
            ("cross", "_blank · 다른 출처"), ("crossopener", "_blank · 다른 출처 · opener"),
            ("named", "target=창이름1 · rel 없음"), ("namednoopener", "target=창이름2 · noopener"),
            ("namednoref", "target=창이름3 · noreferrer"),
            ("namedpolicy", "target=창이름4 · referrerpolicy=no-referrer"),
            ("self", "같은 탭 · rel 없음")]
    probe = "JSON.stringify([window.opener === null ? 'null' : '창 객체', document.referrer || '(빈 문자열)'])"
    table = []
    for key, label in rows:
        goto(c, sid, "http://127.0.0.1:18713/html13b-16-rel.html")
        take_log()
        c.events.clear()
        click(c, sid, "#" + key)
        if key == "self":
            c.wait("Page.loadEventFired", sid)
            opener, ref = json.loads(cdp.evaluate(c, sid, probe))
        else:
            s, tid = popup(c)
            opener, ref = json.loads(cdp.evaluate(c, s, probe))
            c.send("Target.closeTarget", {"targetId": tid})
        log = take_log()
        print(f"[{label}]")
        for line in log:
            print("  서버 " + line)
        print(f"  새 문서  window.opener = {opener} · document.referrer = {ref}")
        header = log[0].split("Referer=")[1] if log else "(요청 없음)"
        table.append((label, header, ref, opener))
    print()
    print(f"{'링크':44}{'서버가 받은 Referer':46}{'document.referrer':46}window.opener")
    for label, h, r, o in table:
        print(f"{label:44}{h:46}{r:46}{o}")
    print()
    row = {t[0]: t for t in table}
    pairs = [("_blank · nofollow", "_blank · rel 없음"), ("_blank · noopener", "_blank · rel 없음"),
             ("_blank · noreferrer", "_blank · rel 없음"), ("_blank · opener", "_blank · rel 없음"),
             ("_blank · referrerpolicy=no-referrer", "_blank · rel 없음"),
             ("target=창이름2 · noopener", "target=창이름1 · rel 없음"),
             ("target=창이름3 · noreferrer", "target=창이름1 · rel 없음"),
             ("target=창이름4 · referrerpolicy=no-referrer", "target=창이름1 · rel 없음"),
             ("target=창이름4 · referrerpolicy=no-referrer", "target=창이름3 · noreferrer")]
    total = hit = 0
    for a, b in pairs:
        d = sum(1 for i in (1, 2, 3) if row[a][i] != row[b][i])
        total += 3
        hit += d
        print(f"「{b}」과 갈린 칸 — {a:44}{d} / 3")
    print(f"갈린 칸 = {hit} / {total}")


def download(c, sid, root):
    dl = os.path.join(root, ".dl")
    shutil.rmtree(dl, ignore_errors=True)
    os.makedirs(dl)
    c.send("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": dl, "eventsEnabled": True})
    for key, label in (("same", "같은 출처 · download 있음"), ("cross", "다른 출처 · download 있음"),
                       ("plain", "같은 출처 · download 없음")):
        goto(c, sid, "http://127.0.0.1:18713/html13b-16-dl.html")
        take_log()
        c.events.clear()
        click(c, sid, "#" + key)
        # 둘 중 먼저 오는 쪽을 받는다 — 내려받기가 시작되거나, 이 탭이 그 URL 로 새 문서를 싣는다
        def 맞음(e):
            m = e.get("method")
            if m == "Browser.downloadWillBegin":
                return True
            return m == "Page.frameNavigated" and ("k=" + key) in e["params"]["frame"]["url"]
        while True:
            hit = [e for e in c.events if 맞음(e)]
            if hit:
                break
            c.events.append(json.loads(c.ws.recv()))
        if hit[0]["method"] == "Page.frameNavigated":
            c.wait("Page.loadEventFired", sid)
        print(f"[{label}]")
        if hit[0]["method"] == "Browser.downloadWillBegin":
            name = hit[0]["params"]["suggestedFilename"]
            c.wait("Browser.downloadProgress", pred=lambda p: p["state"] == "completed")
            for line in take_log():
                print("  서버 " + line)
            print(f"  결과  내려받기 · suggestedFilename = {name} · 저장된 파일 = {sorted(os.listdir(dl))}")
            for f in os.listdir(dl):
                os.remove(os.path.join(dl, f))
        else:
            for line in take_log():
                print("  서버 " + line)
            where = cdp.evaluate(c, sid, "location.href + ' · 본문 = ' + JSON.stringify(document.body.innerText)")
            print(f"  결과  이 탭이 이동했다 · {where}")
    shutil.rmtree(dl, ignore_errors=True)
    goto(c, sid, "http://127.0.0.1:18713/html13b-16-dl.html")
    take_log()
    cdp.evaluate(c, sid, """window.__기다림 = new Promise(r => new MutationObserver(() => r(document.title))
        .observe(document.querySelector('title'), { childList: true })); '준비'""")
    click(c, sid, "#js")
    print("[javascript: URL]")
    print("  document.title = " + cdp.evaluate(c, sid, "window.__기다림"))
    print("  location.href  = " + cdp.evaluate(c, sid, "location.href"))
    log = take_log()
    print("  서버 요청 = " + (str(len(log)) + "줄" if log else "0줄"))


def main():
    mode = sys.argv[1]
    a, b = server("A", 18713), server("B", 18714)
    proc, c = cdp.start()
    try:
        tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m in ("Page.enable", "Runtime.enable"):
            c.send(m, sid=sid)
        c.send("Target.setAutoAttach", {"autoAttach": True, "waitForDebuggerOnStart": True, "flatten": True})
        if mode == "page":
            for m in ("DOM.enable", "Accessibility.enable"):
                c.send(m, sid=sid)
            goto(c, sid, "http://127.0.0.1:18713/" + sys.argv[2])
            targets = cdp.evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
            ax = {k: cdp.ax_of(c, sid, sel) for k, sel in json.loads(targets)}
            cdp.evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
            print(cdp.evaluate(c, sid, "window.__끝()"))
            for line in take_log():
                print("서버 " + line)
        elif mode == "ax":
            c.send("Accessibility.enable", sid=sid)
            goto(c, sid, "http://127.0.0.1:18713/" + sys.argv[2])
            cdp.dump_tree(c, sid)
        elif mode == "rel":
            rel(c, sid)
        elif mode == "download":
            download(c, sid, HERE)
        else:
            sys.exit("모드는 rel | download | page | ax")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(cdp.PROF, ignore_errors=True)
        a.shutdown(); b.shutdown()


if __name__ == "__main__":
    main()
```

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다. `rel` 블록 둘(열세 조합 × 서버 로그·새 창)도 **세 판 모두 한 글자도 같았다.** favicon 요청은 모든 페이지의 `<link rel="icon" href="data:,">` 로 **생기지 않았다** — 서버가 **거르지 않았는데** 로그에 없다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`href` 열다섯 형태 × `a.href`·`:link`·포커스·역할** | 3 | 동작 방식 (1) · A1 |
| **`relList.supports()` 여섯 토큰** | 3 | 동작 방식 (2) · A2 |
| **`rel` 열세 조합 × 서버 `Referer`·`document.referrer`·`window.opener`** + 갈린 칸 집계 | 3 | 동작 방식 (3) · A3 · A4 |
| **`download` 셋 + `javascript:`** | 3 | 동작 방식 (4) · A5 |
| **`download` 페이지의 접근성 트리** | 3 | 동작 방식 (5) |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 교차 출처 `download` | **무시하고 이동** | 명세는 「경고」까지만 — 구현의 선택이다 |
| `_blank` 기본 `noopener` | 동작한다 | 명세 알고리즘이지만 **다른 엔진은 미실행** |
| 다른 출처 `Referer` 가 출처만 | 그렇다 | 기본 정책이 바뀌면 바뀐다 |
| `rel=opener` 링크에서만 입력 응답이 막힌 것 | 막혔다(원인은 해석) | 프로세스 배치는 구현이다 |
| 틀린 URL 의 `:link` 참 | 참 | 관찰이다 |

**안 돌려 본 것** — ① **서버가 `Content-Disposition: attachment` 를 보내는 교차 출처 `download`** — 명세가 말하는 「경고 없는 길」인데 이 서버는 그 헤더를 안 보낸다. ② **`window.opener.location` 을 바꾸는 공격** — 스크립트 표면이다. ③ **HTTPS → HTTP 의 `Referer`** — 이 배치의 서버는 둘 다 HTTP 다. ④ **`<area>`·`<form>` 의 `rel`** — 명세의 같은 알고리즘이 쓰이지만 이 주제는 `<a>` 만 봤다. ⑤ **`ping` 속성(하이퍼링크 감사)** — 이 주제 밖이다.

**못 잰 것** — ① **검색 엔진의 `nofollow` 처리** — 이 머신에 없다. ② **스크린리더가 「새 창」·「내려받기」를 알리는지** — 보조 기술이 없다. ③ **다른 엔진의 동작 전부.**

**부적용인 창** — **창 ①(`--dump-dom`) · 창 ③(`innerText` 대 `textContent`) · 창 ④(`compatMode`) · 창 ⑥(`renderBlockingStatus`).** 링크는 파서가 고칠 것도, 렌더된 글자가 트리와 갈릴 것도, 문서 모드도, 렌더 차단도 없다 — **잴 것이 없다.**

## 용어 풀이

- **`Referer` 헤더 / `document.referrer`** — 서버가 받는 「어디서 왔나」 / 새 문서가 읽는 「어디서 왔나」.
- **`window.opener`** — 새 창이 자기를 연 창을 쥔 참조.
- **요소의 noopener 구하기(get an element's noopener)** — 링크를 따라갈 때 **새 창에 opener 를 줄지** 정하는 명세 알고리즘. `_blank` 면 기본이 참이다.
- **지원 토큰(supported tokens)** — `relList.supports()` 가 참인 토큰. 처리 모델이 있는 것만.
- **`strict-origin-when-cross-origin`** — Referrer Policy 의 기본 정책. 다른 출처에는 출처만 보낸다.
- **자동 부착 + 디버거 대기** — 새 창을 뜨는 순간 붙잡아 멈춰 두는 CDP 방법. 시간 상수 없이 새 창을 읽는 수단이다.
- **제4의 상태(잴 것이 없다) · 제3의 상태(못 잰 것)** — `nofollow` 의 브라우저 쪽 / 검색 엔진 쪽.
