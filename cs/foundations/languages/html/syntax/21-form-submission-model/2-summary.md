# html/syntax/21 — `<form>` 의 제출 모델: `action`/`method`/`enctype`·제출을 일으키는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Form submission」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-2) 절 — 「Implicit submission」·「Form submission algorithm」·「Constructing the entry list」·「Plain text form data」, 그리고 [「Form submission attributes」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-attributes)(`method`·`formmethod`·`enctype` 의 기본값), [「The button element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-button-element)(`type` 의 기본 상태), [HTML-AAM](https://w3c.github.io/html-aam/)(`form` 의 역할). **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다** — 아래 인용은 전부 그 판의 문장이다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 제출은 **CDP 의 실제 마우스·키 입력**으로 일으켰고(스크립트의 `click()` 이 아니다), 요청은 **하네스 프로세스 안에 띄운 서버**가 받아 적었다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다(22\~24번이 같은 하네스를 쓴다).\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 폼 제출은 가장 오래된 표면이라 Baseline 조회 대상이 아니다. 다만 ★ **`requestSubmit()`·`SubmitEvent.submitter` 는 뒤에 들어온 것**이다(명세의 브라우저 지원 표 — SubmitEvent Chrome 81+). 이 문서는 **그 시점을 따로 재지 않았다.**
> **선행** — [05번 주제](../05-content-categories-and-models/2-summary.md)(`form` 안의 `form` 을 파서가 버린다) · [17번 주제](../17-table-structure/2-summary.md)(표 안의 `form` 이 빈 채로 남는다).
> **경계** — **HTTP 메서드·헤더의 연혁은 [`history/web/02-HTTP-진화.md`](../../../../../../history/web/02-HTTP-진화.md) 의 몫이고, 여기는 마크업이 그 요청을 어떻게 만드느냐**다. ★ 그 문서에 **폼과 닿는 자리는 두 줄뿐**이다 — HTTP/1.0 절의 「`GET`에 더해 `HEAD`, `POST`가 들어와 폼 전송 … 이 가능해졌다」와 `Content-Type` 의 뜻. **`application/x-www-form-urlencoded`·`multipart/form-data`·질의 문자열·`Referer` 는 한 줄도 없다**(네 낱말로 `grep` 해 확인했다). 그래서 이 주제가 싣는 **본문 형식은 전부 서버 로그로 본 관찰 + HTML 명세의 인코딩 절**까지다. **`FormData`·`fetch` 로 같은 본문을 스크립트로 만드는 일**은 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **30번**이다(폴더는 아직 없다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다.** 폼이 **무엇을 보내는지는 서버가 받은 요청으로만 안다** — 화면에도 DOM 에도 흔적이 없다. 짝으로 **창 ②(페이지가 받은 `click`·`submit`·`invalid` 이벤트)** 가 「제출이 **어디까지** 갔나」를 말한다.

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
| **흔들린다** | CDP 포트·프로필 경로·**서버 포트** | 실행마다 운영체제가 고른다 — ★ **출력에는 안 들어간다**(로그는 서버 이름 `A` 만 적는다) |
| **죽였다** | `multipart/form-data` 의 **경계(boundary) 문자열** | 실행마다 바뀐다 — 하네스가 **경계로 본문을 갈라 필드 목록만** 적고 경계 자리에는 `(경계)` 라고 쓴다 |
| **죽였다** | 서버 로그의 **시각·클라이언트 포트** | 적지 않게 짰다 |
| **고정했다** | favicon 요청 | 모든 페이지가 `<link rel="icon" href="data:,">` 를 달아 요청이 안 생긴다 |
| **안 흔들린다** | 시도마다의 **요청 줄 수·메서드·경로·`Content-Type`·질의·본문·필드** | 시도마다 페이지를 **새로 열고**, 제출 여부를 **이벤트로** 가른다(아래 「제출이 났나를 어떻게 가르나」) |
| **안 흔들린다** | 페이지 쪽 기록(`click`·`submit`·`invalid`) | 같은 판이면 결정적이다 |
| **안 흔들린다** | 「갈린 칸 N / M」·「서버가 받은 시도 N / M」 | 스크립트가 센다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 요청이 **몇 번** 갔나 · **메서드·경로** · **질의에 실렸나 본문에 실렸나** · **`Content-Type`** · 필드((1)\~(5)) |
| **② 노드 프로브**(페이지가 받은 이벤트 · `input.form`) | ★ **쓴다 — 본체의 짝** | `submit` 이벤트가 **났나** · 검증이 돌아 `invalid` 가 **났나** · 제출 단추에 `click` 이 **났나** · 입력이 **어느 `form` 에 속하나**((2)·(4)) |
| **⑦ 접근성 트리** | 쓴다(곁가지) | `form` 이 트리에서 **무엇으로 찍히나**((6)) |
| **① `--dump-dom`** | **부적용** | 이 주제에서 파서가 고치는 자리(`form` 안의 `form`·표 안의 `form`)는 [05번](../05-content-categories-and-models/2-summary.md)·[17번](../17-table-structure/2-summary.md)이 이미 찍었다 — 여기는 **그 결과가 제출에 어떻게 번지나**를 창 ②·⑤로 본다 |
| **③ `innerText` 대 `textContent`** | **부적용** | 제출은 글자 렌더와 무관하다 — **잴 것이 없다** |
| **④ `compatMode`** | **부적용** | 문서 모드와 무관하다 |
| **⑥ `renderBlockingStatus`** | **부적용** | 폼은 렌더를 막지 않는다 |

- ★★ **제5의 상태 — 「검증이 돌았나」를 `invalid` 이벤트로 물었다.** 명세의 「제약을 대화형으로 검증한다」는 **밖에서 보이는 반환값이 없다.** 대신 검증이 **실패하면** 칸마다 `invalid` 이벤트가 난다. ★ **바꾼 창이 못 보는 것** — **검증이 돌았는데 통과한 경우**는 `invalid` 가 안 나므로 이 창에 안 보인다. 그래서 (2)는 **무효한 폼(`가빈`·`나빈`)을 따로 두어** 「돌았다면 반드시 `invalid` 가 난다」 쪽에서 물었다.
- ★★ **제출이 났나를 어떻게 가르나 — 시간 상수 없이.** 명세는 폼 제출의 이동을 **「DOM 조작 작업 원천」에 작업으로 넣어 뒤로 미룬다**(「plan to navigate」 — *Queue an element task on the DOM manipulation task source*). 하네스는 동작 뒤에 **같은 작업 원천의 작업 하나**(`details` 의 `toggle`)를 더 넣고, 그것이 돌 때 **`beforeunload` 가 이미 났나**를 본다. 났으면 새 문서의 `load` 를 기다리고, 안 났으면 「안 갔다」로 적는다. ★ **이 판별의 전제**(Chrome 이 폼 제출 작업을 그 작업 원천에 넣는다)는 **관찰**이다. 그래서 **거짓 「안 갔다」를 따로 센다** — 시도마다 다음 페이지를 열 때 **그 사이에 뒤늦게 온 요청**이 있었나를 세어 마지막 줄 `뒤늦게 온 요청 = N` 으로 찍는다. 이 배치의 모든 `시도` 블록이 **0** 이었다.

## 한눈에 — 쉽게 말하면

**★ 폼 제출은 「택배 보내기」다. `action` 은 받는 주소, `method` 는 「봉투 겉면에 적나(GET) 상자 안에 넣나(POST)」, `enctype` 은 「상자 안을 어떻게 싸나」다.**

택배 창구에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **받는 주소** | **`action`** — 없으면 **지금 문서의 주소** |
| **송장(겉면)에 내용물을 다 적어 보냄** | **GET** — 필드가 **URL 의 질의 문자열**로 간다 |
| **상자 안에 넣어 보냄** | **POST** — 필드가 **요청 본문**으로 간다 |
| **상자 안을 싸는 방식** | **`enctype`** — 퍼센트 인코딩 / 부분마다 칸막이(multipart) / 맨글자(text/plain) |
| **상자에 붙이는 「내용물 종류」 딱지** | **`Content-Type` 헤더** |
| **창구 직원이 송장 검사** | **제약 검증** — 틀리면 **보내지 않는다** |
| **「검사 없이 뒷문으로」** | **`form.submit()`** — 검증도 `submit` 이벤트도 건너뛴다 |
| **창구를 아예 안 거치고 트럭에 직접 싣기** | **`curl`** — 브라우저도 검증도 없다 |

- **GET 은 `enctype` 을 안 본다** — 송장에 적는 법은 하나뿐이다((1)).
- **텍스트 칸에서 Enter 는 「기본 단추를 누른 것」이다** — 단추가 없으면 **칸이 하나일 때만** 보낸다((2)).
- **`form.submit()` 은 창구를 건너뛴다** — 무효한 값도 서버에 간다((2)).
- ★ **서버는 창구를 거쳤는지 모른다** — `curl` 로 보낸 본문과 브라우저가 보낸 본문이 **한 글자도 같다**((5)).

```text
  한 번의 제출이 지나는 길 (명세 「form submission algorithm」 요약)

  트리거                 검증        submit 이벤트      항목 목록       인코딩            이동
  ─────────────────     ─────────   ──────────────    ─────────────   ───────────────   ─────────────
  단추 클릭 / Enter  ──> 돈다 ──X──> 난다(막을 수 있다) ──> 만든다 ──> method·enctype ──> 작업으로 미룸
  requestSubmit()    ──> 돈다      난다                    │           GET  → 질의
  form.submit()      ─────────────────────────────────────>┘           POST → 본문 (enctype 셋)
                         ★ submit() 은 두 칸을 통째로 건너뛴다
```

> **질의 문자열(query string)** — URL 의 `?` 뒤. `?q=1&s=2` 처럼 **이름=값** 을 `&` 로 잇는다.\
> 예: `GET /r?q=%ED%95%9C+%EA%B8%80` — 「한 글」이 퍼센트 인코딩됐다(공백은 `+`).

> **퍼센트 인코딩** — URL 에 못 쓰는 바이트를 `%` + 두 자리 16진수로 적는 것. 한글 한 글자는 UTF-8 세 바이트라 `%XX` 셋이 된다.\
> 예: 「한」 = `%ED%95%9C`.

## 이 주제가 답하려는 질문

1. **`method` × `enctype` 이 필드를 어디에(질의 / 본문) 어떤 모양으로 싣나** — 그리고 `Content-Type` 은 무엇이 되나.
2. **무엇이 제출을 일으키고, 각각이 검증·`submit` 이벤트를 거치나** — 단추 클릭·Enter(암묵 제출)·`submit()`·`requestSubmit()`.
3. **단추마다 설정을 덮는 것**(`formaction`·`formmethod`·`formenctype`)과 **폼 밖의 입력을 묶는 것**(`form` 속성)은 무엇을 바꾸나.

## 동작 방식

**페이지 쪽 기록기** — 모든 제출 페이지가 이 스크립트를 싣는다. `click`·`invalid`·`submit` 을 **캡처 단계에서** 받아 같은 탭의 `sessionStorage` 에 적는다(같은 출처로 이동해도 남는다). `beforeunload` 는 위의 「제출이 났나」 판별에 쓴다.

```javascript
// html21b-rec.js
// 페이지 쪽 기록 — 같은 탭의 sessionStorage 에 적는다(같은 출처로 이동해도 남는다)
const 적기 = s => {
  const a = JSON.parse(sessionStorage.getItem("기록") || "[]");
  a.push(s);
  sessionStorage.setItem("기록", JSON.stringify(a));
};
addEventListener("click", e => {
  const t = e.target.closest("button, input");
  if (t) 적기("click(" + (t.id || t.name) + " · detail=" + e.detail + ")");
}, true);
addEventListener("invalid", e => 적기("invalid(" + e.target.name + ")"), true);
addEventListener("beforeunload", () => sessionStorage.setItem("떠남", "1"));
addEventListener("submit", e => 적기("submit(submitter=" + (e.submitter ? e.submitter.id || e.submitter.name : "null") + ")"), true);
```

### (1) 창 ⑤ — `method` × `enctype` 여섯 칸과 두 갈래

**언제 쓰나** — 서버 쪽 코드가 **필드를 어디서 읽어야 하는지**(질의냐 본문이냐, 무슨 파서냐) 정할 때.

같은 두 필드 — `q` = 「한 글」(한글 + 공백), `s` = 「a&b=c+d」(구분 기호 셋) — 를 여덟 폼에 넣고 **진짜 마우스로** 단추를 눌렀다.

```html
<!-- html21b-21-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 무엇이 서버에 실리나</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="g1" action="/r" method="get"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b1">보냄</button></form>
<form id="g2" action="/r" method="get" enctype="multipart/form-data"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b2">보냄</button></form>
<form id="g3" action="/r" method="get" enctype="text/plain"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b3">보냄</button></form>
<form id="p1" action="/r" method="post"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b4">보냄</button></form>
<form id="p2" action="/r" method="post" enctype="multipart/form-data"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b5">보냄</button></form>
<form id="p3" action="/r" method="post" enctype="text/plain"><input name="q" value="한 글"><input name="s" value="a&amp;b=c+d"><button id="b6">보냄</button></form>
<form id="x1" action="/r" method="put"><input name="q" value="한 글"><button id="b7">보냄</button></form>
<form id="x2" method="post"><input name="q" value="한 글"><button id="b8">보냄</button></form>
<script>
window.__표 = "싣기";
window.__시도 = [
  { 이름: "GET · urlencoded(기본)", 단계: [["click", "#b1"]] },
  { 이름: "GET · multipart/form-data", 단계: [["click", "#b2"]] },
  { 이름: "GET · text/plain", 단계: [["click", "#b3"]] },
  { 이름: "POST · urlencoded(기본)", 단계: [["click", "#b4"]] },
  { 이름: "POST · multipart/form-data", 단계: [["click", "#b5"]] },
  { 이름: "POST · text/plain", 단계: [["click", "#b6"]] },
  { 이름: "method=put", 단계: [["click", "#b7"]] },
  { 이름: "action 없음 · POST", 단계: [["click", "#b8"]] },
];
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 시도 html21b-21-grid.html | sed -n '1,18p'
[GET · urlencoded(기본)]
  페이지  click(b1 · detail=1) → submit(submitter=b1)
  서버    A GET /r
          질의  q=%ED%95%9C+%EA%B8%80&s=a%26b%3Dc%2Bd
          본문  (없음)
          필드  q=「한 글」 · s=「a&b=c+d」
[GET · multipart/form-data]
  페이지  click(b2 · detail=1) → submit(submitter=b2)
  서버    A GET /r
          질의  q=%ED%95%9C+%EA%B8%80&s=a%26b%3Dc%2Bd
          본문  (없음)
          필드  q=「한 글」 · s=「a&b=c+d」
[GET · text/plain]
  페이지  click(b3 · detail=1) → submit(submitter=b3)
  서버    A GET /r
          질의  q=%ED%95%9C+%EA%B8%80&s=a%26b%3Dc%2Bd
          본문  (없음)
          필드  q=「한 글」 · s=「a&b=c+d」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-grid.html | sed -n '19,36p'
[POST · urlencoded(기본)]
  페이지  click(b4 · detail=1) → submit(submitter=b4)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80&s=a%26b%3Dc%2Bd」
          필드  q=「한 글」 · s=「a&b=c+d」
[POST · multipart/form-data]
  페이지  click(b5 · detail=1) → submit(submitter=b5)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 2개 · 경계로 갈라 필드만 적는다)
          필드  q=「한 글」 · s=「a&b=c+d」
[POST · text/plain]
  페이지  click(b6 · detail=1) → submit(submitter=b6)
  서버    A POST /r  Content-Type=text/plain
          질의  (없음)
          본문  「q=한 글\r\ns=a&b=c+d\r\n」
          필드  q=「한 글」 · s=「a&b=c+d」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-grid.html | sed -n '37,48p'
[method=put]
  페이지  click(b7 · detail=1) → submit(submitter=b7)
  서버    A GET /r
          질의  q=%ED%95%9C+%EA%B8%80
          본문  (없음)
          필드  q=「한 글」
[action 없음 · POST]
  페이지  click(b8 · detail=1) → submit(submitter=b8)
  서버    A POST /html21b-21-grid.html  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-grid.html | sed -n '50,$p'
시도                          메서드  질의  본문          Content-Type                        「GET · urlencoded(기본)」과 갈린 칸
GET · urlencoded(기본)        GET     있음  없음          (없음)                              (기준)
GET · multipart/form-data     GET     있음  없음          (없음)                              0 / 4
GET · text/plain              GET     있음  없음          (없음)                              0 / 4
POST · urlencoded(기본)       POST    없음  퍼센트 인코딩 application/x-www-form-urlencoded   4 / 4
POST · multipart/form-data    POST    없음  multipart     multipart/form-data                 4 / 4
POST · text/plain             POST    없음  글자 그대로   text/plain                          4 / 4
method=put                    GET     있음  없음          (없음)                              0 / 4
action 없음 · POST            POST    없음  퍼센트 인코딩 application/x-www-form-urlencoded   4 / 4
본문에 실린 시도 = 4 / 8
갈린 칸 = 16 / 28
뒤늦게 온 요청 = 0
(exit 0)
```

```text
  「무엇이 서버에 실리나」 — 여섯 칸 격자 (q=「한 글」 · s=「a&b=c+d」)

                   GET                                POST
                   ───────────────────────────        ──────────────────────────────────────────
  urlencoded       질의  q=%ED%95%9C+%EA%B8%80&…       본문  q=%ED%95%9C+%EA%B8%80&s=a%26b%3Dc%2Bd
  (기본)                                               Content-Type: application/x-www-form-urlencoded
  multipart        질의  ← urlencoded 와 같다 ★         본문  부분 2개 (경계로 칸막이 · 값은 맨글자)
                                                       Content-Type: multipart/form-data; boundary=…
  text/plain       질의  ← urlencoded 와 같다 ★         본문  q=한 글\r\ns=a&b=c+d\r\n   ★ 인코딩 없음
                                                       Content-Type: text/plain

  ★ GET 열은 enctype 을 안 본다 — 명세의 「Mutate action URL」은 언제나 urlencoded 직렬화기다
```

- ★★★ **GET 은 필드를 질의 문자열에, POST 는 본문에 싣는다** — 서버 로그의 「질의」·「본문」 칸이 정확히 뒤바뀐다(격자 표 — GET 셋은 **질의 있음·본문 없음**, POST 셋은 **질의 없음·본문 있음**).
- ★★★ **GET 은 `enctype` 을 무시한다** — `multipart/form-data`·`text/plain` 을 줘도 질의가 **urlencoded 와 한 글자도 같다**(격자 0 / 4 · 0 / 4). 명세의 표가 `http` + GET 을 **「Mutate action URL」** 로 보내고, 그 단계는 「**application/x-www-form-urlencoded 직렬화기**를 돌린다」고만 적는다 — `enctype` 을 읽는 줄이 없다.
- ★★ **urlencoded 는 구분 기호까지 인코딩한다** — `&`→`%26`, `=`→`%3D`, `+`→`%2B`, 공백→`+`. 그래서 서버는 `a&b=c+d` 를 **한 필드로** 되살린다(필드 줄의 `s=「a&b=c+d」`).
- ★★★ **`text/plain` 은 아무것도 인코딩하지 않는다** — 본문이 `q=한 글\r\ns=a&b=c+d\r\n` 이다. 명세의 「text/plain 인코딩 알고리즘」이 **이름 + `=` + 값 + CRLF** 를 이어 붙이기만 하고, 스스로 「**사람이 읽으라고 만든 형식이고 컴퓨터가 믿고 해석할 수 없다**(값 안의 줄바꿈과 끝의 줄바꿈을 못 가른다)」고 적는다.
- ★ **`multipart/form-data` 는 부분 2개**로 왔고, 값은 인코딩 없이 들어 있다(하네스가 경계로 갈라 필드만 적었다). 파일을 보낼 수 있는 **유일한** 형식이다 — [24번](../24-input-types-choice-special/2-summary.md)의 빈 파일 칸과 목록의 **31번 주제**(파일 업로드)가 잇는다.
- ★★ **`method="put"` 은 GET 이 됐다** — `method` 의 「누락 기본값·무효 기본값은 둘 다 GET」이다. **HTML 폼은 GET·POST(·`dialog`) 밖의 메서드를 못 보낸다.**
- **`action` 이 없으면 지금 문서로 보낸다** — `POST /html21b-21-grid.html`. 명세 — 「`action` 이 빈 문자열이면 폼 문서의 URL 로 한다」.

### (2) 창 ⑤ + 창 ② — 제출을 일으키는 것 열여섯 시도

**언제 쓰나** — 「Enter 로 제출되는 폼」·「왜 이 단추가 제출하지?」·「스크립트로 보냈더니 검증이 안 돈다」를 가를 때.

일곱 폼이 **단추 · 칸 수 · 무효 여부**만 다르다. `가빈`·`나빈` 은 `required` 칸이 **비어 있는** 무효 폼이다. Enter 는 **칸에 포커스를 두고 CDP 로 진짜 키**를 눌렀다([web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md)이 쓴 방법 — 합성 이벤트가 아니다).

```html
<!-- html21b-21-trigger.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 제출을 일으키는 것</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="가" action="/r"><input name="q" value="1"><button id="가단추">보냄</button></form>
<form id="가빈" action="/r"><input name="q" required><button id="가빈단추">보냄</button></form>
<form id="나" action="/r"><input name="q" value="1"></form>
<form id="나빈" action="/r"><input name="q" required></form>
<form id="다" action="/r"><input name="q" value="1"><input name="r" value="2"></form>
<form id="라" action="/r"><input name="q" value="1"><input type="checkbox" name="c" checked></form>
<form id="마" action="/r"><input name="q" value="1"><button id="마단추" disabled>보냄</button></form>
<form id="바" action="/r"><input name="q" value="1"><button id="바단추" type="button">누름</button></form>
<form id="사" action="/r"><input name="q" value="1"><button id="사단추" type="zzz">누름</button></form>
<script>
window.__표 = "제출";
const 폼 = id => "document.getElementById('" + id + "')";
window.__시도 = [
  { 이름: "가 · 제출 단추 클릭", 단계: [["click", "#가단추"]] },
  { 이름: "가 · 칸에서 Enter", 단계: [["enter", "#가 [name=q]"]] },
  { 이름: "가 · form.submit()", 단계: [["js", 폼("가") + ".submit(); 1"]] },
  { 이름: "가 · form.requestSubmit()", 단계: [["js", 폼("가") + ".requestSubmit(); 1"]] },
  { 이름: "가빈 · 제출 단추 클릭", 단계: [["click", "#가빈단추"]] },
  { 이름: "가빈 · 칸에서 Enter", 단계: [["enter", "#가빈 [name=q]"]] },
  { 이름: "가빈 · form.submit()", 단계: [["js", 폼("가빈") + ".submit(); 1"]] },
  { 이름: "가빈 · form.requestSubmit()", 단계: [["js", 폼("가빈") + ".requestSubmit(); 1"]] },
  { 이름: "나 · 단추 없음 · 칸 하나 · Enter", 단계: [["enter", "#나 [name=q]"]] },
  { 이름: "나빈 · 단추 없음 · 칸 하나 · Enter", 단계: [["enter", "#나빈 [name=q]"]] },
  { 이름: "다 · 단추 없음 · 칸 둘 · Enter", 단계: [["enter", "#다 [name=q]"]] },
  { 이름: "라 · 단추 없음 · 칸+체크박스 · Enter", 단계: [["enter", "#라 [name=q]"]] },
  { 이름: "마 · disabled 단추 · Enter", 단계: [["enter", "#마 [name=q]"]] },
  { 이름: "바 · type=button 클릭", 단계: [["click", "#바단추"]] },
  { 이름: "바 · type=button · Enter", 단계: [["enter", "#바 [name=q]"]] },
  { 이름: "사 · type=zzz 클릭", 단계: [["click", "#사단추"]] },
];
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '1,24p'
[가 · 제출 단추 클릭]
  페이지  click(가단추 · detail=1) → submit(submitter=가단추)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[가 · 칸에서 Enter]
  페이지  click(가단추 · detail=0) → submit(submitter=가단추)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[가 · form.submit()]
  페이지  (기록 없음)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[가 · form.requestSubmit()]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
(exit 0)
```

- ★★★ **칸에서 Enter 는 제출 단추에 `click` 을 낸다 — `detail=0`** 이다(마우스 클릭은 `detail=1`). 그 뒤에 `submit` 이 났고 `submitter` 가 **그 단추**다. [web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md)의 (8) — 「입력칸에서 Enter 를 누르면 제출 단추에 `click` 이 난다 · 그 `click` 을 막으면 `submit` 도 안 난다」 — 과 같은 관찰이다. 명세 — 「기본 단추에 활성화 동작이 있고 비활성이 아니면, 암묵 제출은 **그 기본 단추에 `click` 이벤트를 쏴야 한다**」.
- ★★★ **`form.submit()` 은 페이지 기록이 비어 있다** — `click` 도 `submit` 도 없는데 **서버는 받았다.**
- **`requestSubmit()` 은 `submit` 이 났고 `submitter=null`** 이다 — 인자로 단추를 안 줬기 때문이다.

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '25,39p'
[가빈 · 제출 단추 클릭]
  페이지  click(가빈단추 · detail=1) → invalid(q)
  서버    (받은 요청 없음)
[가빈 · 칸에서 Enter]
  페이지  click(가빈단추 · detail=0) → invalid(q)
  서버    (받은 요청 없음)
[가빈 · form.submit()]
  페이지  (기록 없음)
  서버    A GET /r
          질의  q=
          본문  (없음)
          필드  q=「」
[가빈 · form.requestSubmit()]
  페이지  invalid(q)
  서버    (받은 요청 없음)
(exit 0)
```

- ★★★ **무효한 폼에서 `submit()` 만 서버에 닿았다** — `q=「」`, `required` 인데 빈 값이다. 나머지 셋(클릭·Enter·`requestSubmit()`)은 **`invalid(q)` 가 나고 멈췄다.** `submit` 이벤트도 안 났다 — 검증이 **`submit` 이벤트보다 앞**이다.
- 명세의 제출 알고리즘이 정확히 이렇게 갈라 적는다 — 「**`submit()` 메서드에서 온 것이 아니면**: … 대화형으로 제약을 검증하고, 결과가 부정이면 **돌아간다** … `submit` 이벤트를 쏜다」. **`submit()` 에서 온 제출은 이 덩어리 전체를 건너뛴다.**

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '40,75p'
[나 · 단추 없음 · 칸 하나 · Enter]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[나빈 · 단추 없음 · 칸 하나 · Enter]
  페이지  invalid(q)
  서버    (받은 요청 없음)
[다 · 단추 없음 · 칸 둘 · Enter]
  페이지  (기록 없음)
  서버    (받은 요청 없음)
[라 · 단추 없음 · 칸+체크박스 · Enter]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1&c=on
          본문  (없음)
          필드  q=「1」 · c=「on」
[마 · disabled 단추 · Enter]
  페이지  (기록 없음)
  서버    (받은 요청 없음)
[바 · type=button 클릭]
  페이지  click(바단추 · detail=1)
  서버    (받은 요청 없음)
[바 · type=button · Enter]
  페이지  submit(submitter=null)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
[사 · type=zzz 클릭]
  페이지  click(사단추 · detail=1) → submit(submitter=사단추)
  서버    A GET /r
          질의  q=1
          본문  (없음)
          필드  q=「1」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-trigger.html | sed -n '77,$p'
시도                                    submit  invalid  서버가 받은 요청  「가 · 제출 단추 클릭」과 갈린 칸
가 · 제출 단추 클릭                     났다    —       1번               (기준)
가 · 칸에서 Enter                       났다    —       1번               0 / 3
가 · form.submit()                      —      —       1번               1 / 3
가 · form.requestSubmit()               났다    —       1번               0 / 3
가빈 · 제출 단추 클릭                   —      났다     0번               3 / 3
가빈 · 칸에서 Enter                     —      났다     0번               3 / 3
가빈 · form.submit()                    —      —       1번               1 / 3
가빈 · form.requestSubmit()             —      났다     0번               3 / 3
나 · 단추 없음 · 칸 하나 · Enter        났다    —       1번               0 / 3
나빈 · 단추 없음 · 칸 하나 · Enter      —      났다     0번               3 / 3
다 · 단추 없음 · 칸 둘 · Enter          —      —       0번               2 / 3
라 · 단추 없음 · 칸+체크박스 · Enter    났다    —       1번               0 / 3
마 · disabled 단추 · Enter              —      —       0번               2 / 3
바 · type=button 클릭                   —      —       0번               2 / 3
바 · type=button · Enter                났다    —       1번               0 / 3
사 · type=zzz 클릭                      났다    —       1번               0 / 3
서버가 받은 시도 = 9 / 16
갈린 칸 = 20 / 45
뒤늦게 온 요청 = 0
(exit 0)
```

```text
  Enter 한 번이 폼에 따라 갈리는 길 (명세 「Implicit submission」)

  칸에서 Enter
     │
     ├─ 제출 단추가 있다 ──> 기본 단추(트리 순서로 첫 제출 단추)
     │                        ├─ 비활성 아님 ──> 그 단추에 click (detail=0) ──> 제출    가 · 가빈
     │                        └─ disabled     ──> 아무 일도 없다                        마
     │
     └─ 제출 단추가 없다 ──> 「암묵 제출을 막는 칸」이 몇 개인가
                              ├─ 1 개  ──> 폼 자체로 제출 (click 없음 · submitter=null)  나 · 나빈 · 라 · 바
                              └─ 2 개↑ ──> 아무 일도 없다                                  다

  막는 칸 = input 의 text·search·tel·url·email·password·date·month·week·time·datetime-local·number
  ★ 체크박스는 막는 칸이 아니다 (라) · type=button 은 제출 단추가 아니다 (바)
```

- ★★★ **서버가 받은 시도는 9 / 16**, 기준(「가 · 제출 단추 클릭」)과 **갈린 칸은 20 / 45** 다.
- ★★★ **단추 없는 폼의 Enter 는 칸 수로 갈린다** — 칸 하나(`나`)는 **보냈고**, 칸 둘(`다`)은 **아무 기록도 요청도 없다.** 명세 — 「폼에 **암묵 제출을 막는 칸이 둘 이상**이면 돌아간다」.
- ★★ **체크박스는 「막는 칸」에 안 든다** — `라`(텍스트 하나 + 체크박스)는 Enter 로 **보냈고** `c=on` 까지 실렸다. 명세의 목록이 `input` 의 **텍스트류·날짜류·`number`** 만 든다.
- ★★ **`disabled` 인 기본 단추는 Enter 를 삼킨다** — `마` 는 기록도 요청도 없다. 기본 단추가 **있으니** 「단추 없음」 갈래로도 안 간다.
- ★★★ **`type="button"` 은 제출하지 않지만, 그 폼의 Enter 는 제출한다** — `바` 의 클릭은 `click` 만 남았고, Enter 는 **`submit(submitter=null)`** 로 보냈다. `type=button` 은 **제출 단추가 아니라서** 폼이 「단추 없는 폼」으로 취급된다.
- ★★ **`type="zzz"` 는 제출 단추다** — 무효한 `type` 값은 **Auto 상태**(누락 기본값·무효 기본값)이고, Auto 상태의 `button` 은 (`command`·`commandfor` 가 없고 부모가 `select` 가 아니면) **제출 단추**다. ★ **폼 안의 평범한 `<button>` 이 제출하는 사고의 뿌리가 이 규칙이다** — 목록의 **32번 주제**가 정본이다.

### (3) 창 ⑤ — 단추마다 덮기: `formaction`·`formmethod`·`formenctype`

**언제 쓰나** — 한 폼에 「저장」·「미리보기」처럼 **보낼 곳이 다른 단추**를 둘 때.

```html
<!-- html21b-21-override.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 단추마다 덮기</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="겟폼" action="/r" method="get">
  <input name="q" value="한 글">
  <button id="기본">폼의 설정</button>
  <button id="덮음" formaction="/r2" formmethod="post">formaction · formmethod</button>
  <input type="submit" id="입력덮음" formaction="/r3" formmethod="post" value="input 쪽">
  <button id="글자" formmethod="post" formenctype="text/plain">formmethod · formenctype</button>
</form>
<form id="포스트폼" action="/r" method="post" enctype="text/plain">
  <input name="q" value="한 글">
  <button id="글자2">폼의 설정</button>
  <button id="빈덮음" formmethod="">formmethod=""</button>
</form>
<script>
const 폼 = id => "document.getElementById('" + id + "')";
window.__시도 = [
  { 이름: "겟폼 · 폼의 설정", 단계: [["click", "#기본"]] },
  { 이름: "겟폼 · button formaction·formmethod", 단계: [["click", "#덮음"]] },
  { 이름: "겟폼 · input formaction·formmethod", 단계: [["click", "#입력덮음"]] },
  { 이름: "겟폼 · formmethod=post formenctype=text/plain", 단계: [["click", "#글자"]] },
  { 이름: "겟폼 · requestSubmit(#덮음)", 단계: [["js", 폼("겟폼") + ".requestSubmit(" + 폼("덮음") + "); 1"]] },
  { 이름: "포스트폼 · 폼의 설정", 단계: [["click", "#글자2"]] },
  { 이름: "포스트폼 · formmethod=\"\"", 단계: [["click", "#빈덮음"]] },
];
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 시도 html21b-21-override.html | sed -n '1,30p'
[겟폼 · 폼의 설정]
  페이지  click(기본 · detail=1) → submit(submitter=기본)
  서버    A GET /r
          질의  q=%ED%95%9C+%EA%B8%80
          본문  (없음)
          필드  q=「한 글」
[겟폼 · button formaction·formmethod]
  페이지  click(덮음 · detail=1) → submit(submitter=덮음)
  서버    A POST /r2  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
[겟폼 · input formaction·formmethod]
  페이지  click(입력덮음 · detail=1) → submit(submitter=입력덮음)
  서버    A POST /r3  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
[겟폼 · formmethod=post formenctype=text/plain]
  페이지  click(글자 · detail=1) → submit(submitter=글자)
  서버    A POST /r  Content-Type=text/plain
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「%ED%95%9C+%EA%B8%80」
[겟폼 · requestSubmit(#덮음)]
  페이지  submit(submitter=덮음)
  서버    A POST /r2  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「q=%ED%95%9C+%EA%B8%80」
          필드  q=「한 글」
(exit 0)
```

- ★★★ **`formaction`·`formmethod` 가 그 단추로 보낼 때만 폼의 설정을 덮는다** — `#기본` 은 `GET /r`, `#덮음` 은 `POST /r2`. `input type=submit` 도 같다(`POST /r3`). 명세 — 「요소가 제출 단추이고 `formmethod` 가 있으면 **요소의 method 는 그 속성의 상태**, 아니면 폼 소유자의 `method`」.
- ★ **`requestSubmit(단추)` 도 그 단추의 덮기를 쓴다** — `POST /r2`, `submitter=덮음`.
- ★★★ **그런데 `formenctype="text/plain"` 의 본문이 퍼센트 인코딩돼 있다** — `「q=%ED%95%9C+%EA%B8%80」`, 끝의 CRLF 도 없다. **`Content-Type` 은 `text/plain` 이다.** (1)에서 **폼 자체가 `method=post enctype=text/plain`** 일 때는 `「q=한 글\r\n…」` 이었다. 명세는 제출 알고리즘에서 「**제출자 요소의** method」·「**제출자 요소의** enctype」을 쓰고, `text/plain` 칸은 「text/plain 인코딩 알고리즘」을 돌리라고 한다 — **이 판의 본문은 그것과 갈린다**(아래 「구현 세부사항 대 언어 보장」).

```text
$ python3 html21b-form.py 시도 html21b-21-override.html | sed -n '31,$p'
[포스트폼 · 폼의 설정]
  페이지  click(글자2 · detail=1) → submit(submitter=글자2)
  서버    A POST /r  Content-Type=text/plain
          질의  (없음)
          본문  「q=한 글\r\n」
          필드  q=「한 글」
[포스트폼 · formmethod=""]
  페이지  click(빈덮음 · detail=1) → submit(submitter=빈덮음)
  서버    A GET /r
          질의  q=%C3%AD%E2%80%A2%C5%93%20%C3%AA%C2%B8%E2%82%AC
          본문  (없음)
          필드  q=「í•œ ê¸€」
뒤늦게 온 요청 = 0
(exit 0)
```

- **폼 자체가 `method=post enctype=text/plain` 이면 본문은 맨글자**다 — (1)과 같다.
- ★★ **`formmethod=""` 는 GET 이 됐다** — `formmethod` 는 「누락 기본값이 없고 **무효 기본값이 GET**」이다. 빈 문자열은 무효 값이다.
- ★★★ **그 GET 의 질의가 깨졌다** — `q=%C3%AD%E2%80%A2%C5%93%20%C3%AA%C2%B8%E2%82%AC`, 서버가 디코딩하면 `「í•œ ê¸€」` 이다. 「한」의 UTF-8 세 바이트(`ED 95 9C`)를 **한 바이트씩 서양 글자로 읽은 뒤 다시 UTF-8 로 인코딩한** 모양이고, 공백도 `+` 가 아니라 `%20` 이다. 명세대로면 GET 은 언제나 urlencoded 직렬화기라 `q=%ED%95%9C+%EA%B8%80` 이어야 한다((1) 의 GET 세 줄). ★ **「한 바이트씩 서양 글자로 읽었다」는 바이트 모양에서 읽은 해석**이다 — Chrome 소스를 확인하지 않았다.

```text
  단추가 method 를 덮을 때 — 이 판에서 본문 모양이 무엇을 따랐나

  폼의 method/enctype        단추의 덮기                     실제 메서드   본문·질의 모양          명세대로면
  ────────────────────────  ─────────────────────────────  ───────────  ─────────────────────  ─────────────────────
  post · text/plain          (없음)                          POST         q=한 글\r\n             같다
  get                        formmethod=post formenctype=    POST         q=%ED%95%9C+%EA%B8%80   q=한 글\r\n
                             text/plain                                   ★ urlencoded 모양
  post · text/plain          formmethod=""                   GET          q=%C3%AD%E2%80%A2…      q=%ED%95%9C+%EA%B8%80
                                                                          ★ 깨진 글자
  ★ 둘 다 「단추가 method 를 바꾼」 자리에서만 났다. 폼이 스스로 정한 조합(1)은 여섯 칸 다 명세와 같았다.
```

### (4) 창 ② + 창 ⑤ — 어느 `form` 에 속하나

**언제 쓰나** — 레이아웃 때문에 입력을 폼 **밖**에 둬야 할 때, 또는 표·중첩 때문에 **트리와 소속이 어긋날** 때.

```html
<!-- html21b-21-owner.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 어느 form 에 속하나</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="갑" action="/r"><input id="i1" name="안" value="1"><button id="갑단추">보냄</button></form>
<input id="i2" name="form속성" value="2" form="갑">
<input id="i3" name="그냥밖" value="3">
<form id="을" action="/r2"><input id="i4" name="을안인데갑" value="4" form="갑"></form>
<input id="i5" name="없는폼" value="5" form="없음">
<table><form id="병" action="/r3"><tr><td><input id="i6" name="표안" value="6"><input type="submit" id="병단추" value="보냄"></td></tr></form></table>
<form id="겉" action="/r4"><form id="속" action="/r5"><input id="i7" name="중첩" value="7"><button id="속단추">보냄</button></form></form>
<script>
window.__시도 = [
  { 이름: "갑의 단추", 단계: [["click", "#갑단추"]] },
  { 이름: "표 안의 form 병의 단추", 단계: [["click", "#병단추"]] },
  { 이름: "form 안의 form 의 단추", 단계: [["click", "#속단추"]] },
];
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__끝 = () => {
  const O = [칸("id", 8) + 칸("name", 14) + 칸("부모", 10) + "input.form"];
  for (const i of document.querySelectorAll("input")) {
    const 부모 = i.parentElement.tagName.toLowerCase() + (i.parentElement.id ? "#" + i.parentElement.id : "");
    O.push(칸(i.id, 8) + 칸(i.name || "(없음)", 14) + 칸(부모, 10) + (i.form ? "form#" + i.form.id : "null"));
  }
  O.push("");
  O.push("form 개수 = " + document.forms.length + " · id = " + [...document.forms].map(f => f.id).join(" · "));
  O.push("form#병 의 자식 수 = " + document.getElementById("병").childNodes.length
    + " · form#병.elements.length = " + document.getElementById("병").elements.length);
  O.push("form#갑.elements = " + [...document.getElementById("갑").elements].map(e => e.id).join(" · "));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py page html21b-21-owner.html
id      name          부모      input.form
i1      안            form#갑   form#갑
i2      form속성      body      form#갑
i3      그냥밖        body      null
i4      을안인데갑    form#을   form#갑
i5      없는폼        body      null
i6      표안          td        form#병
병단추  (없음)        td        form#병
i7      중첩          form#겉   form#겉

form 개수 = 4 · id = 갑 · 을 · 병 · 겉
form#병 의 자식 수 = 0 · form#병.elements.length = 2
form#갑.elements = i1 · 갑단추 · i2 · i4
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-21-owner.html
[갑의 단추]
  페이지  click(갑단추 · detail=1) → submit(submitter=갑단추)
  서버    A GET /r
          질의  %EC%95%88=1&form%EC%86%8D%EC%84%B1=2&%EC%9D%84%EC%95%88%EC%9D%B8%EB%8D%B0%EA%B0%91=4
          본문  (없음)
          필드  안=「1」 · form속성=「2」 · 을안인데갑=「4」
[표 안의 form 병의 단추]
  페이지  click(병단추 · detail=1) → submit(submitter=병단추)
  서버    A GET /r3
          질의  %ED%91%9C%EC%95%88=6
          본문  (없음)
          필드  표안=「6」
[form 안의 form 의 단추]
  페이지  click(속단추 · detail=1) → submit(submitter=속단추)
  서버    A GET /r4
          질의  %EC%A4%91%EC%B2%A9=7
          본문  (없음)
          필드  중첩=「7」
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`form` 속성이 트리 위치를 이긴다** — `i2`(`body` 에 있음)도, `i4`(**다른 폼 `을` 의 자식**)도 `input.form` 이 `form#갑` 이고, 갑을 제출하면 **셋이 다 실렸다**(`안`·`form속성`·`을안인데갑`). 명세의 「폼 소유자 재설정」 — `form` 속성이 있으면 **그 id 의 폼**이 소유자다.
- ★★ **없는 id 를 가리키면 소유자가 없다** — `i5` 는 `null` 이다. **가장 가까운 조상 폼으로 되돌아가지도 않는다**(애초에 조상이 없지만, 명세는 `form` 속성이 있으면 조상을 보지 않는다).
- ★★★ **표 안의 `form#병` 은 자식이 0 인데 `elements.length = 2`** 이고, 그 단추가 `GET /r3` 로 **`표안=6` 을 보냈다.** [17번](../17-table-structure/2-summary.md)의 (2) — 「`form` 은 빈 채로 남고 `input` 은 밖으로 나갔지만 `input.form` 은 그 `form` 을 가리킨다」 — 가 **제출에서도 그대로**다. (여기의 `input` 은 `td` 안이라 밖으로 나가지 않았다 — 소유는 **파서의 「form 요소 포인터」** 로 이어졌다.)
- ★★★ **`form` 안의 `form` 은 없던 일이 됐다** — 폼 개수가 **4**(`속` 이 없다)이고, `속` 의 단추가 **겉의 `action`(`/r4`)** 으로 보냈다. [05번](../05-content-categories-and-models/2-summary.md)의 결론 — 「안쪽 `<form>` 시작 태그가 **통째로 무시**된다」 — 이 제출 주소까지 바꾼다.

```text
  트리 위치와 폼 소유가 갈리는 세 자리

  소스                                          트리                         소유(input.form)   제출되는 곳
  <input form="갑"> (body 에)                   body 의 자식                 갑                  갑의 action
  <form id=을><input form="갑"></form>          을의 자식                    갑 ★               갑의 action
  <table><form id=병><tr><td><input>            form#병 은 빈 채 · input 은 td  병 ★ (포인터)       /r3
  <form id=겉><form id=속 action=/r5><input>    속 은 사라짐 · input 은 겉 안    겉                  /r4 ★
```

### (5) 창 ⑤ — 클라이언트 검증은 서버에 없다

**언제 쓰나** — 「`type=email` 에 `required` 를 달았으니 서버는 검사 안 해도 된다」는 말을 반증할 때.

```html
<!-- html21b-21-guard.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 클라이언트 검증</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="막음" action="/r" method="post">
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="막음단추">보냄</button>
</form>
<form id="안막음" action="/r" method="post" novalidate>
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="안막음단추">보냄</button>
</form>
<script>
window.__시도 = [
  { 이름: "검증 있음", 단계: [["click", "#막음단추"]] },
  { 이름: "novalidate", 단계: [["click", "#안막음단추"]] },
];
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 시도 html21b-21-guard.html
[검증 있음]
  페이지  click(막음단추 · detail=1) → invalid(addr) → invalid(age)
  서버    (받은 요청 없음)
[novalidate]
  페이지  click(안막음단추 · detail=1) → submit(submitter=안막음단추)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
뒤늦게 온 요청 = 0
(exit 0)
```

```text
$ python3 html21b-form.py curl
보낸 명령  curl -s -o /dev/null -w '%{http_code}' --data 'addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5' http://127.0.0.1:<A>/r
  응답 코드 200 · curl exit 0
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
(exit 0)
```

- **검증이 있는 폼은 `invalid` 둘을 내고 멈췄다** — 서버 요청 **0**.
- ★★★ **`curl` 로 같은 본문을 보내니 서버가 그대로 받았다** — 「아무 글자」인 `addr` 와 `-5` 인 `age`. **`novalidate` 폼이 보낸 본문과 한 글자도 같다**(두 블록의 「본문」 줄). 서버 쪽에서 보면 **브라우저가 검증했는지, 검증을 꺼 두었는지, 브라우저를 아예 안 거쳤는지를 가를 칸이 없다.**
- ★ 그래서 **클라이언트 검증은 사용자 편의**이지 **서버의 방어가 아니다.** 명세도 제약 검증 절의 「보안」 항목에서 같은 말을 한다 — 「서버는 클라이언트 쪽 검증에 **기대면 안 된다**」(목록의 **29번 주제**가 정본이다).

### (6) 창 ⑦ — `form` 은 트리에서 무엇으로 찍히나

```html
<!-- html21b-21-ax.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>21 폼의 역할</title>
</head>
<body>
<form action="/r"><input name="q" aria-label="이름 없는 폼의 칸"></form>
<form action="/r" name="폼이름"><input name="q" aria-label="name 속성만 있는 폼의 칸"></form>
<form action="/r" aria-label="검색 조건"><input name="q" aria-label="aria-label 폼의 칸"></form>
<form action="/r" title="툴팁 제목"><input name="q" aria-label="title 폼의 칸"></form>
</body>
</html>
```

```text
$ python3 html21b-form.py ax html21b-21-ax.html
RootWebArea    이름='21 폼의 역할'
  form           이름=''
    textbox        이름='이름 없는 폼의 칸'
      generic        이름=''
  form           이름=''
    textbox        이름='name 속성만 있는 폼의 칸'
      generic        이름=''
  form           이름='검색 조건'
    textbox        이름='aria-label 폼의 칸'
      generic        이름=''
  form           이름='툴팁 제목'
    textbox        이름='title 폼의 칸'
      generic        이름=''
(exit 0)
```

- **이름이 없는 폼도 CDP 트리의 역할은 `form`** 이다. `name` 속성은 **접근 가능한 이름이 되지 않았다**(`이름=''`). `aria-label`·`title` 은 이름이 됐다.
- ★★ **HTML-AAM 은 「`form` 에 접근 가능한 이름이 없으면 랜드마크로 노출하지 마라」고 적는다.** CDP 트리는 **역할 이름까지**만 준다 — 이름 없는 폼이 **플랫폼 접근성 API 에서 랜드마크로 안 나가는지**는 그 아래 층이라 **이 판이 못 쟀다**(제3의 상태). 랜드마크 일반은 [11번](../11-sectioning-and-landmarks/2-summary.md)이 정본이다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다. 쓰는 꼴은 (1)\~(6) 의 소스가 전부 실제로 던진 형태다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 검색처럼 **주소로 공유할** 요청 | `<form action="/r">` (method 생략 = GET) | 필드가 **질의**로 간다 |
| 서버 상태를 **바꾸는** 요청 | `method="post"` | 필드가 **본문**으로 · `application/x-www-form-urlencoded` |
| 파일을 보내는 폼 | `method="post" enctype="multipart/form-data"` | 부분마다 칸막이 · **GET 에서는 무시** |
| 사람이 읽을 본문 | `enctype="text/plain"` | 인코딩 없음 — **기계가 되읽기 어렵다**(명세의 경고) |
| 단추마다 다른 곳으로 | `<button formaction formmethod formenctype>` | 그 단추로 보낼 때만 덮는다 — ★ `formenctype=text/plain` 은 (3) 을 보라 |
| 폼 밖의 입력을 묶기 | `<input form="폼id">` | 트리 위치보다 **이긴다** |
| 제출하지 않는 단추 | `<button type="button">` | 클릭은 제출 안 함 — ★ **그 폼의 Enter 는 제출한다** |
| 스크립트로 제출 | `form.requestSubmit(단추?)` | 검증 · `submit` 이벤트를 **거친다** |
| 스크립트로 제출(옛 방식) | `form.submit()` | 검증 · `submit` 이벤트를 **건너뛴다** |

### 어디서 헷갈리나

- **`enctype` 은 POST 에서만 뜻이 있다.** GET 폼에 `multipart/form-data` 를 줘도 파일은 **안 간다**(질의가 urlencoded 와 같다).
- **`method` 는 셋뿐이다** — `get`·`post`·`dialog`. `put`·`delete` 는 **GET 이 된다.**
- **`button` 의 기본 `type` 은 제출이다** — 무효한 값도 제출이다.
- **Enter 제출은 「단추가 있나」와 「칸이 몇 개인가」 두 축이다.**
- **`submit()` 과 `requestSubmit()` 은 이름만 비슷하다** — 앞엣것은 검증·이벤트를 건너뛴다.

## 어디서 틀리나

### 1. 폼 안의 「취소」 단추가 폼을 보낸다

`<button>취소</button>` 는 **`type` 이 없으니 제출 단추**다((2) 의 `사` — 무효한 `type` 도 제출). **`type="button"`** 을 적는다. ★ 그래도 **그 폼의 Enter 는 막히지 않는다**((2) 의 `바`) — Enter 를 막고 싶으면 `submit` 이벤트에서 막는다.

### 2. 칸이 하나뿐인 검색 폼에 단추를 빼면 Enter 가 안 먹을 줄 안다

**먹는다**((2) 의 `나`). 칸이 **둘 이상**이면 안 먹는다(`다`). 로그인 폼(아이디 + 비밀번호)에서 단추를 빼면 **Enter 로 로그인이 안 된다.**

### 3. `form.submit()` 으로 보내면서 `submit` 리스너의 검사가 돌 줄 안다

**안 돈다**((2) 의 `가빈 · form.submit()`) — 리스너도 제약 검증도 건너뛰고 **빈 `required` 값을 보냈다.** 스크립트로 보낼 때는 **`requestSubmit()`** 을 쓴다.

```text
  같은 무효 폼(가빈)에 세 가지 호출

  단추 클릭          invalid(q)  →  멈춤              서버 0
  requestSubmit()    invalid(q)  →  멈춤              서버 0
  submit()           (기록 없음)  →  그대로 보냄        서버 1  q=「」 ★
```

### 4. GET 폼에 `enctype="multipart/form-data"` 를 주고 파일을 기다린다

**GET 은 `enctype` 을 안 본다**((1) 의 격자 0 / 4). 파일 업로드는 **POST + multipart** 둘 다 있어야 한다.

### 5. 클라이언트 검증이 있으니 서버 검증을 뺀다

**서버는 브라우저를 거쳤는지 모른다**((5) — `curl` 과 `novalidate` 의 본문이 한 글자도 같다).

### 6. 단추에 `formenctype="text/plain"` 을 달고 폼의 `text/plain` 과 같을 거라 여긴다

**이 판에서는 다르다**((3)) — 폼이 GET 이고 단추가 POST 로 덮으면 본문이 **urlencoded 모양**으로 왔다. `text/plain` 을 쓸 일이 있으면 **폼 자체에** `method="post" enctype="text/plain"` 을 적는다(그 조합은 명세대로였다).

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | GET 은 「Mutate action URL」 — **언제나 urlencoded 직렬화기**, POST 는 「Submit as entity body」 — `enctype` 셋으로 갈린다 | (1) |
| **명세(HTML)** | `method` 의 누락·무효 기본값 = GET · `formmethod` 의 무효 기본값 = GET | (1)·(3) |
| **명세(HTML)** | `action` 이 빈 문자열이면 **폼 문서의 URL** | (1) |
| **명세(HTML)** | text/plain 인코딩 = `이름=값` + CRLF — **사람이 읽는 형식이고 모호하다** | (1) |
| **명세(HTML)** | 암묵 제출 — 기본 단추가 있고 비활성이 아니면 **그 단추에 `click`** · 단추가 없으면 **막는 칸이 둘 이상일 때 돌아간다** | (2) |
| **명세(HTML)** | `submit()` 에서 온 제출은 **검증과 `submit` 이벤트를 건너뛴다** | (2) |
| **명세(HTML)** | `button` 의 `type` 누락·무효 = **Auto** — 조건이 맞으면 제출 단추 | (2) |
| **명세(HTML)** | 제출 알고리즘은 **제출자 요소의** method·enctype 을 쓴다 | (3) |
| **명세(HTML)** | 이동은 **DOM 조작 작업 원천의 작업**으로 미룬다 | 하네스의 판별 근거 |
| **명세(HTML-AAM)** | 이름 없는 `form` 은 랜드마크로 노출하지 않는다 | (6) — 플랫폼 층은 못 쟀다 |
| ★ **구현(Chrome) — 명세와 갈림** | 폼이 GET 이고 단추가 POST·`text/plain` 으로 덮으면 **본문이 urlencoded 모양** | (3) |
| ★ **구현(Chrome) — 명세와 갈림** | 폼이 POST·`text/plain` 이고 단추가 `formmethod=""`(→GET)이면 **질의의 한글이 깨지고 공백이 `%20`** | (3) |
| **구현(Chrome)** | 폼 제출 작업이 **`beforeunload` 를 그 작업 안에서** 낸다(판별의 전제) | 흔들림 없음 — 16시도 |
| **이 판의 관찰** | 위 명세 줄들이 **그대로 동작했다**는 것 | 다른 엔진은 **미실행** |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **이름 없는 `form` 이 플랫폼 API 에서 랜드마크로 나가는지** | CDP 트리는 역할 이름까지다 — 「**못 잰 것**」 |
| **검증 실패 때 사용자가 보는 풍선 말** | 헤드리스에는 그 UI 가 없다 — 이 문서는 `invalid` **이벤트가 났나**까지만 쟀다 |
| **HTTPS·다른 출처로의 제출**(`Referer`·쿠키·CORS) | 서버가 같은 출처 HTTP 하나다 — **안 돌려 본 것** |
| **`method="dialog"`** | 목록의 **47번 주제**(`dialog`)의 몫이다 — 여기서 던지지 않았다 |
| **`accept-charset`·`target`·`rel` 이 제출에 주는 영향** | 이 주제는 `action`·`method`·`enctype` 셋만 쟀다 |
| **다른 엔진의 (3) 두 줄** | 엔진이 하나뿐이다 — Chrome 버그인지 판단할 비교 대상이 없다 |

## 언제 쓰고 언제 안 쓰나

- **읽기(검색·필터)는 GET** — 결과 주소를 복사·북마크할 수 있다. **쓰기(가입·결제)는 POST** — 새로고침·주소창에 값이 남지 않는다.
- **파일이 있으면 POST + `multipart/form-data`**, 없으면 기본(urlencoded).
- **`text/plain` 은 쓰지 않는다** — 명세 스스로 「기계가 믿고 해석할 수 없다」고 적는다.
- **폼 안의 비제출 단추는 전부 `type="button"`**, Enter 를 막아야 하면 **`submit` 이벤트**에서.
- **스크립트로 보낼 때는 `requestSubmit()`** — `submit()` 은 검증을 건너뛴다.
- **서버는 늘 다시 검증한다.**

## 핵심 문장

1. **GET 은 필드를 질의 문자열에, POST 는 본문에 싣는다 — 서버 로그의 두 칸이 정확히 뒤바뀐다.**
2. **GET 은 `enctype` 을 무시한다 — 질의는 언제나 urlencoded 다.**
3. **`text/plain` 은 인코딩을 안 한다 — `이름=값` 과 CRLF 뿐이다.**
4. **텍스트 칸의 Enter 는 기본 단추에 `click`(`detail=0`)을 낸다 — 단추가 없으면 막는 칸이 하나일 때만 보낸다.**
5. **`form.submit()` 은 검증도 `submit` 이벤트도 건너뛴다 — 빈 `required` 칸이 서버에 갔다.**
6. **`button` 의 `type` 이 없거나 틀리면 제출 단추다 — `type="button"` 이어도 그 폼의 Enter 는 제출한다.**
7. **`form` 속성은 트리 위치를 이긴다 — 다른 폼의 자식이어도 가리킨 폼으로 간다.**
8. **서버는 브라우저를 거쳤는지 모른다 — `curl` 과 폼의 본문이 한 글자도 같다.**

## 관련 자료

- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — **`form` 안의 `form` 을 파서가 버린다**의 정본. 여기는 그 결과가 **제출 주소를 바꾼다**까지((4)).
- [17번 주제 — 표 구조](../17-table-structure/2-summary.md) — **표 안의 `form` 이 빈 채로 남는다**의 정본. 여기는 그래도 **제출은 된다**까지((4)).
- [web-api 17번 — `stopPropagation` 대 `preventDefault`](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md) — **Enter → 제출 단추 `click` → `submit`** 사슬과 **그 `click` 을 막으면 제출도 막힌다**의 정본. 여기는 **폼 모양에 따라 Enter 가 무엇을 하나**까지.
- 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **30번**(`FormData`·`URLSearchParams`) — 폼과 **같은 본문을 스크립트로** 만드는 자리.
- [`history/web/02-HTTP-진화.md`](../../../../../../history/web/02-HTTP-진화.md) — **HTTP/1.0 에서 `POST` 가 들어와 폼 전송이 가능해진** 연혁. ★ 그 문서에 **본문 형식(urlencoded·multipart)·질의 문자열 절은 없다.**
- 목록의 **22·23·24번 주제** — 각 **입력 타입이 무엇을 싣나.** [22번](../22-input-types-text/2-summary.md) · [23번](../23-input-types-number-date/2-summary.md) · [24번](../24-input-types-choice-special/2-summary.md).
- 목록의 **29번 주제**(제약 검증) — **검증 상태와 `novalidate`** 의 정본. 여기는 **검증이 제출을 막나**까지.
- 목록의 **31번 주제**(파일 업로드) · **32번 주제**(`button` 의 `type` 과 폼 소유권) — `multipart` 의 파일 쪽과 `form`·`formaction` 의 정본.

## 용어 풀이

- **질의 문자열(query string)** — URL 의 `?` 뒤. GET 제출이 필드를 싣는 자리.
- **요청 본문(request body)** — 헤더 뒤에 오는 바이트. POST 제출이 필드를 싣는 자리.
- **`application/x-www-form-urlencoded`** — `이름=값` 을 `&` 로 잇고 특수 문자를 퍼센트 인코딩하는 형식. 폼의 기본.
- **`multipart/form-data`** — 경계 문자열로 부분을 나누고 부분마다 머리말을 다는 형식. 파일을 실을 수 있다.
- **`text/plain`**(폼 인코딩) — `이름=값` + CRLF. 인코딩이 없다.
- **경계(boundary)** — multipart 의 칸막이 문자열. 실행마다 바뀐다.
- **제출자(submitter)** — 제출을 일으킨 단추. `SubmitEvent.submitter` 로 보인다. 폼 자체가 보내면 `null`.
- **기본 단추(default button)** — 트리 순서로 그 폼의 **첫 제출 단추**. 암묵 제출이 이것에 `click` 을 낸다.
- **암묵 제출(implicit submission)** — 텍스트 칸에서 Enter 로 제출되는 것.
- **암묵 제출을 막는 칸(field that blocks implicit submission)** — 텍스트류·날짜류·`number` 인 `input`. 단추 없는 폼에 이것이 **둘 이상**이면 Enter 가 아무것도 안 한다.
- **폼 소유자(form owner)** — 입력이 속한 폼. `form` 속성이 있으면 그 id, 없으면 가장 가까운 조상 폼(파서의 포인터 포함).
- **`beforeunload`** — 문서를 떠나기 직전에 나는 이벤트. 하네스가 「이동이 시작됐나」를 가르는 데 썼다.

## 더 들어가면

- **왜 GET 에 `enctype` 이 없나** — GET 에는 본문이 없고 URL 은 글자 줄이라, 싣는 방법이 urlencoded 하나뿐이다. 명세가 `data:` 스킴의 POST·`mailto:` 스킴까지 표로 나눠 두는 것을 보면(**`mailto:` + POST 는 「Mail as body」**), 「메서드 × 스킴」이 먼저 갈리고 `enctype` 은 **본문이 있는 칸 안에서만** 쓰인다.
- **왜 `text/plain` 이 남아 있나** — 명세가 「사람이 읽으라고 만든 형식」이라고 적고, `mailto:` 로 메일 본문을 채우는 옛 용도가 있다(「Mail as body」 칸이 `text/plain` 을 따로 다룬다). 이 배치는 `mailto:` 제출을 던지지 않았다.
- **이동을 작업으로 미루는 이유** — 명세는 폼마다 「계획된 이동(planned navigation)」을 하나만 두고, 새 제출이 오면 **앞의 작업을 지우고** 새로 넣는다. 한 번의 조작에서 제출이 여러 번 일어나도 **마지막 하나만** 간다는 뜻이다. 이 배치는 그 경합을 던지지 않았다.
