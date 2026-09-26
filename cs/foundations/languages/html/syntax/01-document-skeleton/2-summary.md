# html/syntax/01 — HTML 문서의 뼈대: `<!DOCTYPE html>`·`<html lang>`·`<head>`/`<body>` 의 필수 요소 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The html element」](https://html.spec.whatwg.org/multipage/semantics.html#the-html-element)·[「Writing HTML documents」](https://html.spec.whatwg.org/multipage/syntax.html#writing)·[「Parsing HTML documents」](https://html.spec.whatwg.org/multipage/parsing.html) 절. 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** Firefox 155.0.1 이 설치돼 있으나 이 환경에서 headless 산출이 **조용히 실패**하고 WebKit 은 없다. 그러므로 이 갈래는 **「이식성」을 주장하지 않는다** — 「두 엔진에서 확인했다」·「모든 브라우저가 이렇게 한다」고 적지 않는다.
> **버전** — HTML 에는 언어 버전이 없다(「HTML5」는 더 이상 기준이 아니다). 지원 상태는 **Baseline** 으로 읽는다. 이 주제가 다루는 것은 전부 **20년 넘게 안정된 표면**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

이 갈래가 근거로 쓸 칸을 먼저 선언한다. 제출 전 재대조가 한 줄에 판정되도록 하기 위한 것이다.

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · 실행 시각 · 프로세스 id | 판이 오르면 바뀐다 |
| **흔들린다** | 스크린샷 픽셀의 안티에일리어싱 | GPU·글꼴 래스터라이저에 달렸다 |
| **안 흔들린다** | **`--dump-dom` 트리 전체** | 파싱 알고리즘이 명세에 있다 |
| **안 흔들린다** | 노드 수 · 속성 이름과 값 · 코드포인트 목록 | 〃 |
| **안 흔들린다** | `document.compatMode` · `document.doctype` | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다(03번 주제) |

실측 — 이 배치의 캡처 **68블록을 두 번 돌려 68블록 전부 한 글자도 같았다**(흔들린 칸 0 · 고칠 것 0).

## 한눈에 — 쉽게 말하면

**★ 내가 쓴 HTML 은 「문서」가 아니다. 브라우저에게 주는 「지시서」다. 문서는 파서가 만든다.**

이삿짐 센터에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 내가 적어 보낸 짐 목록 | **HTML 소스** |
| 짐을 실제로 넣은 집 | **DOM 트리** |
| 목록에 안 적었어도 알아서 세워 주는 방 | **암묵으로 삽입되는 `html`·`head`·`body`** |
| 「이 집은 새 규격이다」라고 적은 첫 줄 | **`<!DOCTYPE html>`** |
| 새 규격 딱지를 안 붙였을 때 적용되는 옛 규격 | **호환 모드(quirks mode)** |
| 집주인 나라를 적은 문패 | **`<html lang>`** |

- **DOCTYPE 은 「HTML 버전 선언」이 아니다.** 오늘 하는 일은 **딱 하나** — **표준 모드로 켜는 것**이다.
- **`html`·`head`·`body` 는 안 써도 트리에 생긴다.** 그래서 「필수 요소」의 뜻이 「**내가 써야 하는 것**」이 아니라 「**트리에 있어야 하는 것**」이다.
- **정말로 내가 써야 하는 것은 `<title>` 과 `<meta charset>` 둘뿐**이다. 이 둘은 **파서가 만들어 주지 않는다.**

```text
  내가 쓴 것 (파일 전체)            파서가 만든 트리
  +---------------------+          +-----------------------------+
  | 안녕                |   ==>    | html                        |
  +---------------------+          |   head        <- 저절로 생김 |
                                   |   body                      |
      태그가 하나도 없다            |     #text "안녕"            |
                                   +-----------------------------+
```

```text
  내가 쓴 것                         파서가 만든 트리
  +---------------------------+     +-----------------------------+
  | <!DOCTYPE html>           |     | DOCTYPE html   <- 모드 스위치 |
  | <meta charset="utf-8">    |     | html                        |
  | <p>본문</p>               |     |   head                      |
  +---------------------------+     |     meta charset=utf-8      |
                                    |   body                      |
      title 이 없다                 |     p                       |
                                    +-----------------------------+
                                      title 은 끝내 안 생긴다
```

실무에서 이게 터지는 자리는 **템플릿을 조각내어 붙일 때**다.\
헤더 조각에서 `</head>` 를 빠뜨렸는데 화면은 멀쩡해서 몇 달을 모른다 — **파서가 조용히 고쳐 놨기 때문**이다.\
그러다 `<head>` 에 넣은 `<link>` 가 어느 날 `<body>` 로 밀려나 있는 것을 보고서야 안다(아래 (4)).

> **DOM 트리(Document Object Model tree)** — 브라우저가 소스를 읽어 메모리에 세운 문서의 실제 모양.\
> 예: `<p>안녕` 한 줄이 `html > body > p > #text` 라는 네 노드가 된 것.

> **표준 모드(standards mode)** — 오늘의 규칙대로 CSS 를 해석하는 모드. `document.compatMode` 가 `CSS1Compat`.\
> 예: `width: 200`(단위 없음)을 무효로 버린다.

> **호환 모드(quirks mode)** — 1990년대 브라우저 흉내를 내는 모드. `document.compatMode` 가 `BackCompat`.\
> 예: `width: 200` 을 `200px` 로 봐준다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 세 질문을 둔다.

1. **DOCTYPE 이 오늘 하는 일은 정확히 무엇인가.** 있고 없고에 따라 **무엇이 관찰 가능하게** 달라지나.
2. **`html`·`head`·`body` 를 안 쓰면 트리는 어떻게 되나.** 그러면 「필수」라는 말은 무슨 뜻인가.
3. **`<head>` 에 넣을 수 있는 것과 없는 것은 무엇이 가르나.** 안 되는 것을 넣으면 어디로 가나.

## 이 갈래의 창 — 무엇으로 관찰하나

CSS 갈래에는 「진단 3창」이 있다(`cssRules` → `querySelectorAll` → `getComputedStyle`).\
CSS 는 **에러 없이 조용히 버리는** 언어라 「버려졌나」를 값으로 물어야 했기 때문이다.

HTML 은 정반대다 — **버리지 않고 고쳐서 쌓는다.** 그래서 물어야 할 것이 다르다:\
「버려졌나」가 아니라 「**내가 쓴 것과 브라우저가 만든 것이 어디서 갈라졌나**」다.\
★ **이 갈래의 창 넷을 여기서 세우고 02·03·04 가 그대로 쓴다.**

```text
  창 ①  --dump-dom                       파서가 만든 트리
          소스가 아니라 '결과'를 글자로 보여 준다. 이 갈래의 첫 번째 창이다
          -> 03번 주제는 이 창 하나가 본체다

  창 ②  프로브 (childNodes · nodeName · attributes)     노드 단위
          직렬화가 안 보여 주는 것을 센다
          -> 공백 텍스트 노드(04)·중복 속성이 몇 개 담겼나(02)

  창 ③  innerText  대  textContent        렌더  대  트리
          같은 글자가 어디서 갈리나. '소스가 맞다'와 '렌더된 것이 맞다'를 가른다
          -> 04번 주제의 본체

  창 ④  document.compatMode · document.doctype        모드 스위치
          무엇이 규칙 자체를 바꾸나
          -> 이 주제(01)의 본체
```

★ **없는 것도 적는다 — 이 환경에 `validator` 는 없다.**\
W3C Nu Validator 같은 검증기가 설치돼 있지 않고 네트워크로 부르지도 않았다.\
그래서 이 갈래는 「**이 마크업이 유효한가**」를 도구로 판정하지 않는다.\
대신 「**파서가 무엇을 고쳤나**」로 대신한다 — 고쳤다는 것이 곧 내가 틀렸다는 뜻이기 때문이다.\
★ 다만 **둘은 같지 않다.** 파서가 안 고친 것 중에도 무효한 것이 있다(`<title>` 누락이 정확히 그것이다 — 아래 (3)).

## 동작 방식

### (1) 창 ④ — DOCTYPE 이 오늘 하는 일은 딱 하나다

**언제 쓰나** — 모든 문서의 첫 줄. **이것부터 세워야 나머지 주제가 읽힌다.**

같은 파일에서 **첫 줄만 지운** 두 판을 던졌다.

```text
===== 소스: html01b-mode-on.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>모드 스위치</title>
<style>#u { width: 200; height: 40; }</style>
</head>
<body>
<div id="u">단위 없는 길이</div>
<script>
const o = [];
const u = document.getElementById("u");
o.push("document.compatMode      = " + document.compatMode);
o.push("document.doctype         = " + (document.doctype ? document.doctype.name : "null"));
o.push("documentElement.lang     = " + JSON.stringify(document.documentElement.lang));
o.push("#u 계산 width            = " + getComputedStyle(u).width);
o.push("#u 계산 height           = " + getComputedStyle(u).height);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html01b-mode-on.html | probe =====
document.compatMode      = CSS1Compat
document.doctype         = html
documentElement.lang     = "ko"
#u 계산 width            = 764px
#u 계산 height           = 24px
(exit 0)
```

```text
===== 소스: html01b-mode-off.html =====
<html lang="ko">
<head>
<meta charset="utf-8">
<title>모드 스위치 — DOCTYPE 없음</title>
<style>#u { width: 200; height: 40; }</style>
</head>
<body>
<div id="u">단위 없는 길이</div>
<script>
const o = [];
const u = document.getElementById("u");
o.push("document.compatMode      = " + document.compatMode);
o.push("document.doctype         = " + (document.doctype ? document.doctype.name : "null"));
o.push("documentElement.lang     = " + JSON.stringify(document.documentElement.lang));
o.push("#u 계산 width            = " + getComputedStyle(u).width);
o.push("#u 계산 height           = " + getComputedStyle(u).height);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html01b-mode-off.html | probe =====
document.compatMode      = BackCompat
document.doctype         = null
documentElement.lang     = "ko"
#u 계산 width            = 200px
#u 계산 height           = 40px
(exit 0)
```

```text
   DOCTYPE 있음                          DOCTYPE 없음
   +------------------------------+      +------------------------------+
   | compatMode = CSS1Compat      |      | compatMode = BackCompat      |
   | doctype    = html            |      | doctype    = null            |
   | width: 200  -> 무효 -> auto   |      | width: 200  -> 200px 로 봐줌  |
   +------------------------------+      +------------------------------+
     단위 없는 길이를 버린다                 단위 없는 길이를 받아 준다
```

그림 해설 (한 단계씩):

- **`document.doctype` 이 `null` 이 된다.** DOCTYPE 은 **트리에 남는 노드**다 — 없으면 그 노드가 없다.
- **`document.compatMode` 가 `BackCompat` 이 된다.** 이것이 스위치의 이름이다.
- **관찰 가능한 결과는 CSS 쪽에서 난다.** 실측에서 `width: 200`(단위 없음)이 표준 모드에서는 `auto`(그래서 `764px`)로, 호환 모드에서는 **`200px`** 로 계산됐다.
- ★ **「호환 모드면 옛 박스 모델(`border-box`)이 된다」는 이 판에서 재현되지 않았다.** 아래가 그 실측이다.

```text
===== 소스: html01b-box-on.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>호환 모드의 박스 모델</title>
<style>#b { width: 200px; padding: 20px; border: 10px solid; }</style>
</head>
<body>
<div id="b">상자</div>
<script>
const o = [];
const b = document.getElementById("b");
o.push("compatMode        = " + document.compatMode);
o.push("계산 width        = " + getComputedStyle(b).width);
o.push("계산 box-sizing   = " + getComputedStyle(b).boxSizing);
o.push("바깥 너비(rect)   = " + b.getBoundingClientRect().width);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html01b-box-on.html | probe =====
compatMode        = CSS1Compat
계산 width        = 200px
계산 box-sizing   = content-box
바깥 너비(rect)   = 260
(exit 0)
```

```text
===== 소스: html01b-box-off.html =====
<html lang="ko">
<head>
<meta charset="utf-8">
<title>호환 모드의 박스 모델 — DOCTYPE 없음</title>
<style>#b { width: 200px; padding: 20px; border: 10px solid; }</style>
</head>
<body>
<div id="b">상자</div>
<script>
const o = [];
const b = document.getElementById("b");
o.push("compatMode        = " + document.compatMode);
o.push("계산 width        = " + getComputedStyle(b).width);
o.push("계산 box-sizing   = " + getComputedStyle(b).boxSizing);
o.push("바깥 너비(rect)   = " + b.getBoundingClientRect().width);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html01b-box-off.html | probe =====
compatMode        = BackCompat
계산 width        = 200px
계산 box-sizing   = content-box
바깥 너비(rect)   = 260
(exit 0)
```

- **두 모드 모두 `box-sizing` 이 `content-box` 이고 바깥 너비가 `260`** 이다. 널리 알려진 사고지만 **Chrome 151 에서는 사실이 아니다** — 이 갈래에서 실측으로 뒤집힌 첫 번째 전제다.

비용 — 없음. **첫 줄 15글자**로 얻는 것이라 안 쓸 이유가 없다.

### (2) 창 ① — `html`·`head`·`body` 는 안 써도 생긴다

**언제 쓰나** — 「이 태그를 꼭 써야 하나」를 물을 때마다.

파일 전체가 **글자 두 개**뿐인 문서를 던졌다.

```text
===== 소스: html01b-min.html =====
안녕===== dom html01b-min.html =====
<html><head></head><body>안녕</body></html>
(exit 0)
```

```text
   소스 (파일 전체)        파서가 만든 트리
   +-----------+          #document
   | 안녕      |            html            <- 삽입됨
   +-----------+              head          <- 삽입됨 (비어 있다)
                              body          <- 삽입됨
                                #text "안녕"
```

그림 해설 (한 단계씩):

- **`html`·`head`·`body` 세 개의 시작·끝 태그는 전부 생략 가능**하다(명세의 「Optional tags」).
- 생략하면 파서가 **삽입 모드**에 따라 자동으로 연다 — 버리는 게 아니라 **채운다.**
- 그래서 **`document.body` 는 언제나 있다.** 「`body` 가 없어서 스크립트가 터진다」는 일은 **파싱 단계에서는 일어나지 않는다.**
- ★ **「필수 요소」의 뜻이 여기서 갈린다** — 명세가 「필수」라고 하는 것은 **트리에 있어야 한다**는 뜻이지 **내가 타자해야 한다**는 뜻이 아니다.

비용 — 없음. 다만 **생략하면 사람이 구조를 못 본다.** 도구는 괜찮고 사람이 손해다.

### (3) 정말로 내가 써야 하는 것 — `<title>` 은 파서가 만들어 주지 않는다

**언제 쓰나** — 「그럼 아무것도 안 써도 되나」에 답할 때. **(2)의 반대쪽 절반이다.**

```text
===== 소스: html01b-no-title.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<p>제목 요소가 없는 문서</p>
<script>
const o = [];
o.push("document.title           = " + JSON.stringify(document.title));
o.push("head 의 자식 요소         = " + [...document.head.children].map(e => e.localName).join(", "));
o.push("querySelector('title')   = " + document.querySelector("title"));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-no-title.html | nojs =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
</head><body><p>제목 요소가 없는 문서</p>
(exit 0)
```

```text
===== 소스: html01b-no-title.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<p>제목 요소가 없는 문서</p>
<script>
const o = [];
o.push("document.title           = " + JSON.stringify(document.title));
o.push("head 의 자식 요소         = " + [...document.head.children].map(e => e.localName).join(", "));
o.push("querySelector('title')   = " + document.querySelector("title"));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-no-title.html | probe =====
document.title           = ""
head 의 자식 요소         = meta
querySelector('title')   = null
(exit 0)
```

```text
   생략하면 생기는 것                  생략하면 안 생기는 것
   +-------------------------+        +---------------------------+
   | <html>  <head>  <body>  |        | <title>                   |
   |   파서가 삽입한다        |        |   파서가 만들지 않는다     |
   +-------------------------+        +---------------------------+
     document.body 는 항상 있다         querySelector('title') = null
                                       document.title = ""  (빈 문자열)
```

그림 해설 (한 단계씩):

- **`title` 요소가 트리에 아예 없다.** `document.querySelector("title")` 이 **`null`**, `document.title` 은 **빈 문자열**이다.
- **에러는 없다.** 화면도 멀쩡하다 — 탭 이름이 URL 로 대신 나올 뿐이다.
- ★ **그래서 이것이 「파서가 안 고친 무효」다.** 명세는 `head` 에 `title` 이 **정확히 하나** 있어야 한다고 못 박지만(문서에 상위 `title` 을 물려받는 iframe 등 예외 빼고), **파서는 그 위반에 아무 반응도 하지 않는다.**
- **`<meta charset>` 도 같은 성질**이다 — 파서가 만들어 주지 않는다. 다만 이쪽은 **없어도 브라우저가 추측**하므로(아래 (5)) 증상이 더 늦게 드러난다.

비용 — `title` 없음은 **접근성·검색·탭·북마크·공유**가 한꺼번에 상한다. 한 줄로 막을 수 있는 것 중 가장 비싼 축이다.

### (4) `<head>` 에 텍스트를 쓰면 — 거기서 `head` 가 닫힌다

**언제 쓰나** — 템플릿 조각을 `<head>` 에 붙일 때. **가장 자주 터지는 자리다.**

```text
===== 소스: html01b-head-text.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>head 안의 텍스트</title>
여기는 head 안에 쓴 글자다
<meta name="author" content="나">
<link rel="canonical" href="/a">
</head>
<body>
<p>본문</p>
</body>
</html>
===== dom html01b-head-text.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>head 안의 텍스트</title>
</head><body>여기는 head 안에 쓴 글자다
<meta name="author" content="나">
<link rel="canonical" href="/a">


<p>본문</p>


</body></html>
(exit 0)
```

```text
   소스                                   트리
   <head>                                 head
     <meta charset>                         meta charset
     <title>t</title>                       title
     여기는 head 안에 쓴 글자다     ----+   (여기서 head 가 닫힌다)
     <meta name="author">              |  body
     <link rel="canonical">            +--> #text "여기는 head 안에…"
   </head>                                  meta name=author
   <body>                                   link rel=canonical
     <p>본문</p>                            p
```

그림 해설 (한 단계씩):

- **공백이 아닌 글자 하나**가 `head` 안에 오면 파서는 **그 자리에서 `head` 를 닫고 `body` 를 연다**(명세의 「in head」 삽입 모드).
- **그 뒤에 쓴 `<meta>`·`<link>` 가 전부 `body` 로 따라 내려간다.** 내가 `</head>` 를 제대로 썼는데도 그렇다.
- ★ **`<link rel="canonical">` 이 `body` 에 있으면 무시된다.** 증상은 「SEO 가 안 먹는다」인데 원인은 **저 위에 찍힌 글자 하나**다.
- 같은 일이 **주석 아닌 한글 한 글자**·**닫는 따옴표를 빠뜨린 속성값의 나머지**·**템플릿 엔진이 남긴 개행 아닌 문자**에서 난다.

비용 — 없음(파서는 안 멈춘다). **그래서 비싸다** — 아무도 안 알려 준다.

### (5) `<meta charset>` 의 위치 — 명세의 1024바이트와 이 판의 관찰

**언제 쓰나** — 글자가 깨질 때. **이 주제는 목록의 50번 주제가 정본이고 여기서는 「뼈대의 어디에 두나」까지만 쓴다.**

같은 바이트열을 두 파일에 넣고 **`<meta charset>` 의 바이트 위치만** 바꿨다.

```text
===== grep -abo '<meta charset' html01b-charset-early.html html01b-charset-late.html =====
html01b-charset-early.html:16:<meta charset
html01b-charset-late.html:1252:<meta charset
(exit 0)
```

```text
===== for f in html01b-charset-early.html html01b-charset-late.html; do echo "-- $f"; dom "$f" | probe; done =====
-- html01b-charset-early.html
document.characterSet = EUC-KR
p code points         = U+FFFD U+C493 U+FFFD
-- html01b-charset-late.html
document.characterSet = EUC-KR
p code points         = U+FFFD U+C493 U+FFFD
(exit 0)
```

그림 해설 (한 단계씩):

- **선언은 둘 다 먹었다.** 16바이트째에 둔 것도, **1,252바이트째에 둔 것도** `characterSet` 이 `EUC-KR` 이 됐다.
- ★ **그러므로 「1024바이트를 넘기면 무시된다」는 이 판에서 관찰되지 않았다.** 명세의 1024바이트는 **프리스캔**(본격 파싱 전에 인코딩만 훑어보는 단계)의 한계이고, 그 뒤에 나온 선언은 「**인코딩 바꾸기**」 알고리즘이 **파서를 처음부터 다시 돌려서** 처리한다. 결과는 같고 **비용이 다르다.**
- 코드포인트가 `U+FFFD U+C493 U+FFFD` 로 나온 것은 **파일이 UTF-8 인데 EUC-KR 이라고 선언해서** 생긴 깨짐이다 — 선언이 실제로 적용됐다는 증거로 일부러 어긋나게 만든 것이다.
- ★ **이 판에서 「선언이 없을 때」는 잴 수 없었다** — `file://` 로 띄우면 Chrome 151 이 인코딩을 **자동 감지해** 선언 없이도 맞혔다. 「**못 잰 것**」이지 「안 돌려 본 것」이 아니다(아래 「어디서 틀리나」 5).

비용 — **맨 앞에 두는 것이 공짜**다. 늦게 두면 재파싱이 일어날 수 있다(이 판에서 재파싱 자체를 계측하지는 않았다 — 재지 않은 성능 주장은 하지 않는다).

### (6) `lang` — 트리에 남는 값과 그것이 넘겨지는 곳

**언제 쓰나** — 문서를 열 때마다. 한 번 쓰고 끝이다.

앞의 (1) 블록이 `documentElement.lang = "ko"` 를 같이 찍었다. 그것이 관찰의 전부다.

```text
   <html lang="ko">
        |
        +--> DOM        documentElement.lang === "ko"
        +--> CSS        :lang(ko) 선택자가 잡는다
        +--> 글꼴·하이픈  한중일 한자 자형이 갈린다
        +--> 음성 합성    스크린리더가 읽을 언어를 고른다   <- 이 판에서 확인 불가
```

그림 해설 (한 단계씩):

- `lang` 은 **상속된다.** `<html lang="ko">` 하나면 문서 전체가 한국어다. 다른 언어 조각에만 덧쓴다.
- ★ **음성 합성 쪽은 이 환경에서 확인할 수 없다** — 스크린리더(NVDA·VoiceOver)가 없다. 명세·ARIA 문서로만 접지하고 **「미실행」으로 표기**한다.
- 양방향 텍스트(`dir`)와 `lang` 의 깊은 이야기는 [**목록의 20번 주제**](../20-lang-dir-and-bidi/)가 정본이다.

비용 — 없음.

### (7) 뼈대 한 벌 — 이 모든 것을 합치면

```text
===== 소스: html01b-skeleton.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>문서의 뼈대</title>
</head>
<body>
<p>본문</p>
</body>
</html>
===== dom html01b-skeleton.html =====
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>문서의 뼈대</title>
</head>
<body>
<p>본문</p>


</body></html>
(exit 0)
```

```text
   <!DOCTYPE html>          <- 표준 모드 스위치 (창 ④)
   <html lang="ko">         <- 언어. 상속된다
   <head>
     <meta charset="utf-8"> <- 맨 앞. 파서가 만들어 주지 않는다
     <title>…</title>       <- 필수. 파서가 만들어 주지 않는다
   </head>
   <body> … </body>
   </html>
```

- 이 일곱 줄에서 **파서가 못 만들어 주는 것은 `meta charset` 과 `title` 둘뿐**이다.
- 나머지 다섯 줄은 **사람이 읽으려고** 쓴다. 기계는 없어도 같은 트리를 만든다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — DOCTYPE 이 쓸 수 있는 꼴

```text
<!DOCTYPE html>        오늘 쓰는 유일한 형태. 대소문자를 안 가린다
<!doctype html>        같다
<!DOCTYPE HTML>        같다
(없음)                  호환 모드

<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" …>   옛 꼴. 쓰지 않는다
```

### 금지 사례 — 뼈대에서 하면 안 되는 것

```text
DOCTYPE 앞에 무언가를 둔다        주석·BOM 아닌 글자 하나면 호환 모드로 떨어진다
<head> 안에 텍스트를 둔다          거기서 head 가 닫힌다 (동작 방식 (4))
<title> 을 뺀다                   파서가 만들어 주지 않는다 (동작 방식 (3))
<meta charset> 을 <body> 에 둔다   이미 늦었거나 재파싱을 부른다
<html> 을 여러 번 연다             두 번째부터는 속성만 첫 html 에 합쳐진다
```

### 어디서 헷갈리나

- **DOCTYPE 은 「버전」이 아니다.** `<!DOCTYPE html>` 에서 `html` 은 **루트 요소 이름**이지 버전 번호가 아니다.
- **「필수 요소」와 「필수 태그」는 다르다.** `body` 요소는 필수이고 `<body>` 태그는 선택이다.
- **`<head>` 의 끝은 내가 정하는 게 아니다.** 파서가 「`head` 에 못 들어가는 것」을 보는 순간 닫는다.
- **`document.head`·`document.body` 는 언제나 있다** — 「없을까 봐」 방어 코드를 쓸 자리가 아니다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. 「태그를 안 썼으니 없겠지」로 읽는다

실측에서 파일 전체가 `안녕` 두 글자인데 트리에는 **`html`·`head`·`body` 가 전부 있었다.**\
그래서 **「소스를 읽어서 트리를 맞히는 것」이 안 된다** — 창 ① 로 봐야 한다.

### 2. DOCTYPE 을 「옛날 버전 선언」으로 기억한다

오늘 하는 일은 **표준 모드 전환 하나**다. 실측에서 갈린 것은 `compatMode`·`doctype`, 그리고 **CSS 해석**(`width: 200`)이었다.\
★ **그런데 「호환 모드면 박스 모델이 바뀐다」는 이 판에서 재현되지 않았다**(두 모드 모두 바깥 너비 `260`).\
고전 사례를 사실로 외우고 있으면 **여기서 틀린 근거를 댄다.**

### 3. `<head>` 조각에 글자를 흘린다

실측에서 `head` 안의 한 줄 텍스트가 **그 뒤의 `<meta>`·`<link>` 를 통째로 `body` 로 끌고 내려갔다.**\
증상은 「`canonical` 이 안 먹는다」인데 원인은 **마크업 저 위**다. `document.head.children` 을 찍어 보면 한 번에 드러난다.

### 4. `<title>` 을 「그냥 안 쓴 것」으로 넘긴다

**파서가 안 만들어 준다.** 실측에서 `querySelector("title")` 이 `null` 이었고 **아무 경고도 없었다.**\
「파서가 안 고쳤으니 유효한가 보다」는 **틀린 추론**이다 — 파서는 유효성을 판정하지 않는다.

### 5. `<meta charset>` 을 빼고 「잘 나오는데?」 한다

★ **이 판에서는 선언 없이도 잘 나왔다** — `file://` 에서 Chrome 151 이 **자동 감지**를 했다.\
그래서 이 환경은 **「선언을 뺐을 때 깨지는 것」을 재현할 수 없다.** 「안 돌려 봤다」가 아니라 「**못 쟀다**」이다.\
쪼개서 잰 조각은 이것이다 — **선언을 어긋나게 주면**(UTF-8 파일에 `euc-kr`) 코드포인트가 `U+FFFD` 로 깨졌다. **선언이 추측을 이긴다**는 것까지는 이 판에서 보였다.

### 6. `<html>` 을 템플릿마다 열어 둔다

두 번째 `<html>` 시작 태그는 **새 요소를 만들지 않는다** — 속성만 첫 `html` 요소에 **합쳐진다**(이미 있는 속성은 안 덮는다. 중복 속성 규칙은 [02번 주제](../02-elements-and-attributes/2-summary.md)와 같은 「첫 것이 이긴다」이다).

## 구현 세부사항 대 언어 보장

★ **HTML 은 「명세가 오류 복구까지 정한」 드문 언어다.** 파서 알고리즘 자체가 명세 본문에 있다.\
그래서 이 표에서 **「구현 정의」 칸이 다른 언어보다 훨씬 작다** — 트리 모양은 거의 전부 **명세 보장**이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `html`·`head`·`body` 가 생략돼도 트리에 생기는 것 | **명세**(「Optional tags」 + 파싱 알고리즘의 삽입 모드) |
| DOCTYPE 유무가 `document.compatMode` 를 가르는 것 | **명세**(파싱 알고리즘의 「initial」 삽입 모드) |
| `head` 안의 비공백 텍스트가 `head` 를 닫는 것 | **명세**(「in head」 삽입 모드) |
| `title` 을 파서가 만들지 않는 것 | **명세**(파서는 유효성을 판정하지 않는다) |
| 두 번째 `<html>` 의 속성이 합쳐지는 것 | **명세**(「in body」 삽입 모드) |
| **호환 모드가 단위 없는 길이를 받아 주는 것** | **명세**(CSS 의 [Quirks Mode Standard](https://quirks.spec.whatwg.org/)) |
| **호환 모드에서 박스 모델이 안 바뀐 것** | **관찰**(Chrome 151). Quirks Mode Standard 는 박스 모델 quirk 를 규정하지 않는다 |
| **1,252바이트째의 `<meta charset>` 이 먹은 것** | **관찰 + 명세**. 명세는 프리스캔을 1024바이트로 제한하되 「인코딩 바꾸기」로 재파싱을 허용한다. **언제 재파싱하느냐는 구현에 달렸다** |
| **선언이 없을 때 인코딩을 맞힌 것** | **관찰**(Chrome 151 의 자동 감지 + `file://` 스킴). 명세 보장이 아니다 — **서버가 주는 문서에서는 기대하면 안 된다** |
| `--dump-dom` 의 출력 형식(어디서 줄이 바뀌나) | **명세**(HTML 직렬화 알고리즘) + **도구**(Chrome 의 플래그) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 새 문서를 연다 | `<!DOCTYPE html>` 첫 줄 · `<html lang>` · `charset` · `title` | 옛 `PUBLIC` DOCTYPE |
| 템플릿을 조각낸다 | 조각 경계를 요소 경계와 맞춘다 | `<head>` 조각 끝에 글자 흘리기 |
| 「이 태그 꼭 써야 하나」를 묻는다 | `--dump-dom` 으로 트리를 본다 | 소스를 읽어서 추측 |
| 옛 레이아웃을 그대로 살려야 한다 | 호환 모드가 필요한지 **재어 보고** 결정 | DOCTYPE 을 그냥 빼기 |
| 인코딩이 깨진다 | `charset` 을 **문서 맨 앞**으로 | 서버가 알아서 하겠지 |

판단 규칙 두 줄.

- **「내가 안 쓰면 파서가 만들어 주나」를 먼저 묻는다.** 만들어 주면 생략해도 되고, 아니면 반드시 쓴다.
- **뼈대는 의심이 들 때마다 창 ① 로 확인한다.** 소스를 읽는 것으로는 절대 확신할 수 없다.

## 핵심 문장

- **HTML 소스는 문서가 아니라 지시서**다. 문서는 파서가 만든다 — 그래서 **소스와 트리를 갈라 봐야** 한다.
- **`<!DOCTYPE html>` 이 오늘 하는 일은 표준 모드 전환 하나**다. 실측에서 갈린 것은 `compatMode`·`doctype`, 그리고 **단위 없는 CSS 길이**였다.
- **`html`·`head`·`body` 는 안 써도 트리에 생긴다** — 실측에서 파일 전체가 두 글자인데 셋 다 있었다.
- **`<title>` 과 `<meta charset>` 은 파서가 만들어 주지 않는다** — 이 둘이 「정말로 내가 써야 하는 것」이다.
- **`<head>` 안의 글자 하나가 `head` 를 닫는다** — 그 뒤의 `<meta>`·`<link>` 가 전부 `body` 로 내려간다.
- **파서는 유효성을 판정하지 않는다.** 「파서가 안 고쳤다」는 「유효하다」가 아니다.
- 이 환경에 **validator 는 없다.** 관찰 수단은 「**파서가 무엇을 고쳤나**」뿐이고, **엔진은 Chrome 하나**라 이식성을 주장하지 않는다.

## 관련 자료

- [`../README.md`](../README.md) — HTML 문법·API 주제 목록(이 주제는 01번)
- [02번 주제](../02-elements-and-attributes/2-summary.md) — 요소와 속성 문법. **뼈대를 이루는 태그의 표기 규칙**이 거기다
- [03번 주제](../03-parser-and-error-recovery/2-summary.md) — **파서가 트리를 고치는 알고리즘의 정본.**\
  여기는 「뼈대가 저절로 생긴다」는 **결과**까지, 거기는 「**어떤 규칙으로** 생기나」
- [04번 주제](../04-whitespace-and-character-references/2-summary.md) — `head` 안의 **공백**은 왜 `head` 를 안 닫는지
- [`../../../../../../history/web/01-웹-탄생-HTML.md`](../../../../../../history/web/01-웹-탄생-HTML.md) — **버전 없는 시작의 정본.**\
  「왜 HTML 에 버전이 사라졌나」는 거기, 여기는 「**그래서 DOCTYPE 이 오늘 무엇을 하나**」부터
- [`../../../../../../history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — 호환 모드가 생긴 경위(브라우저 전쟁기의 빚)
- 목록의 **50번 주제**(`meta` 계열) — **`charset`·`viewport` 의 정본.** 여기는 「뼈대의 어디에 두나」까지
- [목록의 **20번 주제**](../20-lang-dir-and-bidi/)(`lang`·`dir`) — `lang` 이 실제로 무엇을 바꾸는지의 정본
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **07번** — **에러 없이 버리는 언어**의 짝.\
  CSS 는 버리고 HTML 은 고친다. **둘 다 에러를 안 던지지만 방향이 반대다**

## 용어 풀이

- **DOM 트리(Document Object Model tree)** — 파서가 소스를 읽어 세운 문서의 실제 모양. 소스와 다를 수 있다.
- **DOCTYPE** — 문서 첫 줄의 `<!DOCTYPE html>`. 트리에 **노드로 남고**, 오늘의 역할은 모드 전환 하나다.
- **표준 모드(standards mode)** — 오늘의 규칙대로 해석하는 모드. `document.compatMode === "CSS1Compat"`.
- **호환 모드(quirks mode)** — 옛 브라우저 흉내 모드. `document.compatMode === "BackCompat"`.
- **삽입 모드(insertion mode)** — 파서의 상태 이름. 「지금 `head` 안인가 `body` 안인가」에 따라 같은 태그를 다르게 처리한다.
- **생략 가능 태그(optional tag)** — 안 써도 파서가 그 요소를 만드는 태그. `html`·`head`·`body`·`tbody` 등.
- **프리스캔(prescan)** — 본격 파싱 전에 앞부분만 훑어 인코딩 선언을 찾는 단계. 명세는 **1024바이트**로 제한한다.
- **`document.compatMode`** — 모드 스위치를 읽는 창. 이 갈래의 **창 ④**.
- **`--dump-dom`** — Chrome 에게 「파서가 만든 트리를 글자로 내놔라」고 시키는 플래그. 이 갈래의 **창 ①**.

## 더 들어가면

- **DOCTYPE 이 「버전 선언」이었던 시절의 잔재**가 `<!DOCTYPE html PUBLIC …>` 이다. 브라우저는 그 문자열로 **모드를 세 갈래**(표준·거의 표준·호환)로 갈랐다. 「거의 표준 모드」(`limited-quirks`)는 `document.compatMode` 로는 표준 모드와 **구분되지 않는다** — 둘 다 `CSS1Compat` 이다. 이 판에서 그 세 번째 모드는 재현하지 않았다.
- **`--dump-dom` 이 보여 주는 것은 「직렬화된 트리」이지 트리 자체가 아니다.** 직렬화는 되쓰기를 한 번 더 한다 — 그래서 소스에 없던 `&amp;` 가 생기거나, 내가 쓴 `<br/>` 이 `<br>` 이 되어 나온다([02번 주제](../02-elements-and-attributes/2-summary.md)·[04번 주제](../04-whitespace-and-character-references/2-summary.md)).
- **「뼈대가 저절로 생긴다」와 「그래서 안 써도 된다」는 다른 말**이다. 프레임워크가 조각을 합칠 때 **조각 경계가 요소 경계와 어긋나면** 파서가 고친 결과가 사람의 의도와 달라진다. 03번 주제의 foster parenting 이 그 극단이다.
- **DOM 조작 API 는 web-api 갈래가 정본**이다. 여기는 **파서가 만든 트리의 모양**까지다 — `createElement`·`appendChild` 로 트리를 바꾸는 이야기는 이 갈래 밖이다.
