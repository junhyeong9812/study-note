# html/syntax/01 — HTML 문서의 뼈대: `<!DOCTYPE html>`·`<html lang>`·`<head>`/`<body>` 의 필수 요소 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 「호환 모드에서 박스 모델이 안 바뀐다」 같은 관찰은 **이 엔진의 것**이고, 이 갈래는 이식성을 주장하지 않는다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 안 쓴 세 요소가 트리에 생긴다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-min.html =====
안녕===== dom html01b-min.html =====
<html><head></head><body>안녕</body></html>
(exit 0)
```

**노드 개수**

- **네 개**다 — `html` · `head` · `body` · 텍스트 노드 `"안녕"`.
- 내가 타자한 것은 **텍스트 하나**뿐이다. 나머지 셋은 파서가 삽입했다.

```text
   소스 (파일 전체)        파서가 만든 트리
   +-----------+          #document
   | 안녕      |            html          <- 삽입
   +-----------+              head        <- 삽입 (비어 있다)
                              body        <- 삽입
                                #text "안녕"
```

**`document.body` 는 존재하는가**

- **있다.** `html`·`head`·`body` 는 **시작·끝 태그가 모두 생략 가능**한 요소라(명세의 「Optional tags」) 파서가 삽입 모드에 따라 연다.
- 그래서 「`body` 가 없을까 봐」 방어하는 코드는 **파싱 단계에서는 쓸 자리가 없다.**

**「필수 요소」의 뜻**

- **트리에 있어야 한다는 뜻**이지 **내가 타자해야 한다는 뜻이 아니다.**
- 이 구분이 이 주제의 뼈대다 — A3·A5 가 그 반대쪽 절반이다.

### 2. 첫 줄이 모드를 가른다

**출력** (Chrome 151 headless — 같은 파일에서 첫 줄만 지운 두 판)

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

**갈리는 값 셋**

| | DOCTYPE 있음 | DOCTYPE 없음 |
|---|---|---|
| `document.compatMode` | `CSS1Compat` | `BackCompat` |
| `document.doctype` | `html` | `null` |
| `#u` 계산 `width` | `764px`(= `auto`) | **`200px`** |

**`#u` 의 계산된 `width`**

- 표준 모드 **`764px`** · 호환 모드 **`200px`**.
- `width: 200` 은 **단위가 없어 무효**다. 표준 모드는 그 선언을 버려 `auto` 가 되고(부모 폭 `764px`), 호환 모드는 **`200px` 로 봐준다**(Quirks Mode Standard 의 「unitless length」 quirk).
- `height` 도 같다 — `24px`(줄 높이) 대 `40px`.

**사라지는 노드**

- **DOCTYPE 노드 자체.** DOCTYPE 은 선언문이 아니라 **트리의 첫 자식 노드**다. 그래서 `document.doctype` 이 `null` 이 된다.

**박스 모델은 바뀌는가**

- ★ **이 판에서는 안 바뀌었다.**

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

- **두 모드 모두 `box-sizing` 이 `content-box`**, 계산 `width` 가 `200px`, 바깥 너비가 `260` 이다.
- 「호환 모드 = 옛 박스 모델」은 **널리 알려진 사고**지만 Chrome 151 에서는 재현되지 않는다. Quirks Mode Standard 도 박스 모델 quirk 를 규정하지 않는다.
- ★ **이 판에서 실제로 갈린 것은** 「**단위 없는 길이**」다. 근거로 쓸 것은 그쪽이다.

### 3. 제목은 없다 — 파서가 만들어 주지 않는다

**출력** (Chrome 151 headless)

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

**`document.title` 과 `querySelector("title")`**

- `document.title` = **빈 문자열**, `document.querySelector("title")` = **`null`**.
- `head` 의 자식 요소는 **`meta` 하나**뿐이다. `title` 요소는 **트리에 아예 없다.**

**파서가 알려 주는 것**

- **아무것도 없다.** 예외도 경고도 없고 `(exit 0)` 이다.

**A1 의 세 요소와 무엇이 다른가**

```text
   생략하면 생기는 것                  생략하면 안 생기는 것
   +-------------------------+        +---------------------------+
   | html   head   body      |        | title                     |
   |   삽입 모드가 연다       |        | meta charset              |
   +-------------------------+        +---------------------------+
     "태그를 생략해도 되는" 요소         "내가 안 쓰면 없는" 요소
```

- `html`·`head`·`body` 는 **태그가 생략 가능한 요소**라 파서가 연다.
- `title` 은 **생략 가능 목록에 없다.** 파서가 만들 근거가 없으므로 안 만든다.

**「파서가 안 고쳤다」 = 「유효하다」인가**

- **아니다.** 파서는 **유효성을 판정하지 않는다** — 트리를 만들 뿐이다.
- `title` 누락은 **명세 위반이지만 파서가 아무 반응도 하지 않는 자리**다. 이 환경에 validator 가 없으므로(A8) **이 위반은 도구로 잡히지 않는다.**

### 4. `head` 는 글자 하나에 닫힌다

**출력** (Chrome 151 headless)

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

**`head` 의 자식 요소 목록**

- **`meta charset` 과 `title` 둘뿐**이다.

**`meta name="author"` 와 `link rel="canonical"` 이 가는 곳**

- **둘 다 `body`** 다. 내가 쓴 `</head>` 보다 **앞**에 있는데도 그렇다.

```text
   소스                                   트리
   <head>                                 head
     <meta charset>                         meta charset
     <title>t</title>                       title
     여기는 head 안에 쓴 글자다     ----+   (head 가 여기서 닫힌다)
     <meta name="author">              |  body
     <link rel="canonical">            +--> #text "여기는 head 안에…"
   </head>                                  meta name=author
   <body><p>본문</p></body>                 link rel=canonical
                                            p
```

**그렇게 되는 이유**

- 파서는 「**지금 `head` 안**」이라는 삽입 모드에 있다가 **공백이 아닌 문자**를 만나면 **`head` 를 닫고 `body` 로 옮긴다**(명세의 「in head」 삽입 모드).
- 그 뒤로는 이미 `body` 안이므로 `<meta>`·`<link>` 가 전부 `body` 에 붙는다. 내가 쓴 `</head>` 는 **이미 닫힌 것을 또 닫으라는 말**이라 무시된다.
- ★ **공백은 다르다** — 공백 문자는 `head` 를 닫지 않고 텍스트 노드로 붙는다([04번 주제](../04-whitespace-and-character-references/2-summary.md)).

**같은 사고를 내는 다른 입력**

- **닫는 따옴표를 빠뜨린 속성값**의 나머지가 텍스트로 흘러나올 때.
- **템플릿 엔진이 남긴 BOM 아닌 문자**·번역 도구가 끼워 넣은 글자·주석으로 감싸지 않은 설명 한 줄.

### 5. 「필수 요소」와 「필수 태그」

**한 문장**

- **요소는 트리에 있어야 하는 것이고, 태그는 내가 타자하는 글자다.** 둘의 필수 여부가 따로 논다.

**`body` 요소와 `<body>` 태그**

- **요소가 필수**이고 **태그는 선택**이다. 생략하면 파서가 만든다(A1).

**파서가 만들어 주는 것 / 안 만들어 주는 것**

| | 예 |
|---|---|
| 만들어 준다 | `html` · `head` · `body` · `tbody`([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |
| 안 만들어 준다 | `title` · `meta charset` |

**생략하면 누가 손해인가**

- **기계는 손해가 없다** — 같은 트리가 나온다.
- **사람이 손해**다. 구조가 안 보이고, 조각을 합칠 때 경계를 못 잡는다(A10).

### 6. DOCTYPE 은 선언문이 아니라 노드다

**`document.doctype` 이 `null` 일 수 있다는 뜻**

- DOCTYPE 이 **트리에 실제로 존재하는 노드**라는 뜻이다. 없으면 그 자리가 비고, 그 사실이 `null` 로 읽힌다.
- 실측에서 첫 줄만 지웠더니 `doctype = null` 이었다(A2).

**`<!DOCTYPE html>` 의 `html`**

- **루트 요소의 이름**이다. 버전 번호가 아니다.

**오늘 하는 일 한 가지**

- **표준 모드로 켜는 것.** 그 밖에 하는 일이 없다 — 유효성 검사도, 버전 선택도 하지 않는다.

**`compatMode` 로 구분되지 않는 짝**

- **표준 모드와 「거의 표준 모드」(`limited-quirks`)** 다. 둘 다 `CSS1Compat` 을 돌려준다.
- 그 세 번째 모드는 이 판에서 재현하지 않았다 — **안 돌려 본 것**이다.

### 7. 1,252바이트째의 선언도 먹었다

**출력** (Chrome 151 headless — 같은 바이트열, `<meta charset>` 위치만 다름)

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

**명세의 1024바이트가 무엇의 한계인가**

- **프리스캔**의 한계다 — 본격 파싱 전에 **앞부분만 훑어** 인코딩 선언을 찾는 단계에서 1024바이트까지만 본다.
- 「1024바이트를 넘으면 선언이 무효」라는 뜻이 **아니다.**

**이 판에서 먹었는가**

- **먹었다.** 16바이트째에 둔 것도 **1,252바이트째에 둔 것도** `characterSet` 이 `EUC-KR` 이었다.
- 코드포인트가 `U+FFFD U+C493 U+FFFD` 로 깨진 것은 **파일이 UTF-8 인데 EUC-KR 이라 선언해서**다 — 선언이 적용됐다는 증거로 일부러 어긋나게 만들었다.

**브라우저가 더 한 일**

- 프리스캔을 넘긴 선언은 「**인코딩 바꾸기**」 알고리즘이 **파서를 처음부터 다시 돌려** 반영한다. 결과는 같고 **비용이 다르다.**
- ★ 그 재파싱 비용은 **이 판에서 재지 않았다.** 재지 않은 성능 주장은 하지 않는다.

**선언을 빼면**

- ★ **이 환경에서는 잴 수 없었다.** `file://` 로 띄우면 Chrome 151 이 **인코딩을 자동 감지**해 선언 없이도 맞혔다(EUC-KR 바이트도, UTF-8 바이트도).
- 그래서 「**못 잰 것**」이다 — 「안 돌려 본 것」과 다르다. **근거로 쓸 수 없다.**
- 쪼개서 잰 조각 — **선언을 어긋나게 주면 깨진다**는 것까지는 보였다. 곧 **선언이 추측을 이긴다.**
- 서버가 `Content-Type` 헤더로 인코딩을 주면 그쪽이 또 다르다. 그 갈래는 목록의 **50번 주제**가 정본이다.

### 8. validator 가 없다 — 그러면 무엇으로 보나

**무엇으로 대신하는가**

- 「**파서가 무엇을 고쳤나**」로 대신한다. 고쳤다는 것이 곧 내가 명세와 다르게 썼다는 뜻이기 때문이다.
- 이 환경에 W3C Nu Validator 류가 없고 네트워크로 부르지도 않았다. **없으면 없다고 적는다.**

**알려 주는 것 / 못 알려 주는 것**

| | |
|---|---|
| 알려 준다 | 파서가 **고친** 위반 — `<p><div>`·닫지 않은 태그·`head` 를 닫아 버린 글자 |
| 못 알려 준다 | 파서가 **안 고친** 위반 — `title` 누락·`alt` 누락·틀린 `rel` 값 |

**한계를 보여 주는 사례**

- **`title` 누락**(A3)이 정확히 그것이다. 트리에 흔적이 없고 에러도 없어 **창 ① 로는 잡히지 않는다.**

**이 갈래의 창 넷**

```text
  창 ①  --dump-dom                        파서가 만든 트리
  창 ②  프로브(childNodes·nodeName·attributes)   노드 단위로 센다
  창 ③  innerText 대 textContent           렌더 대 트리
  창 ④  document.compatMode · document.doctype   모드 스위치
```

- CSS 의 「진단 3창」이 「**버려졌나**」를 묻는다면, 이 넷은 「**어디서 갈라졌나**」를 묻는다.

### 9. `lang` 이 넘겨주는 것과 이 판이 못 보는 것

**영향을 주는 곳 셋**

- **DOM** — `documentElement.lang` 이 `"ko"`(A2 블록에서 확인).
- **CSS** — `:lang(ko)` 선택자가 잡는다.
- **글꼴·줄바꿈·하이픈** — 같은 한자를 중국어·일본어·한국어 자형 중 무엇으로 그릴지가 갈린다.

**확인할 수 없는 것**

- **음성 합성**(스크린리더가 어느 언어로 읽나)이다. 이 환경에 NVDA·VoiceOver 가 없다.
- Chrome 의 접근성 트리 덤프까지는 쓸 수 있지만 「**실제로 어떻게 읽히는지**」는 못 본다.

**조각마다 안 써도 되는 이유**

- `lang` 은 **상속**된다. `<html lang="ko">` 하나면 문서 전체가 한국어이고, **다른 언어 조각에만** 덧쓴다.

**「확인 못 했다」를 적는 법**

- 본문의 그 자리에 「**미실행**」을 적고, `## 실행 검증` 절의 「**안 돌려 본 것**」에 이유와 함께 남긴다.
- **「못 쟀다」와 「안 돌려 봤다」는 다르므로 갈라 적는다** — A7 의 charset 은 앞엣것, 스크린리더는 뒤엣것이다.

### 10. 버리는 언어와 고치는 언어

**모르는 것을 만나면**

- **CSS** — **버린다.** 선언 하나·규칙 하나·at-rule 하나 단위로 조용히 사라진다.
- **HTML** — **고쳐서 쌓는다.** 태그를 닫아 주고 요소를 끼워 넣어 **반드시 트리를 만든다.**

**결과가 정반대인 이유**

- **CSS 는 없어도 페이지가 성립하고, HTML 은 없으면 페이지가 없다.** 그래서 한쪽은 모르면 버리고 한쪽은 모르면 지어낸다.

**HTML 명세가 다른 점**

- ★ **오류 복구까지 명세에 적혀 있다.** 파싱 알고리즘이 삽입 모드·토큰 처리까지 문장으로 규정돼 있어, **「잘못된 마크업이 어떤 트리가 되는가」가 명세 보장**이다.
- 그래서 이 갈래의 「**구현 세부사항 대 언어 보장**」 표에서 **「구현 정의」 칸이 생각보다 작다** — 트리 모양은 거의 다 명세 쪽이고, 구현 쪽에 남는 것은 **로그·자동 감지·직렬화 세부** 정도다.

**위험해지는 자리**

- **조각 경계가 요소 경계와 어긋날 때.** 파서가 고친 결과가 사람의 의도와 달라지는데 **에러가 없으니 안 들킨다.**
- 극단은 03번 주제의 **foster parenting** — 표 안에 쓴 요소가 **표 앞으로 밀려난다.**

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다). **마크업 검증기는 없다.**

**하네스** — 01\~04 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe`·`nojs` 가 이 셋이다.

```bash
# html01b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
```

- `probe` 의 마지막 `sed` 가 있는 이유 — **프로브 출력은 `<pre>` 의 텍스트라 직렬화가 `&`·`<`·`>` 를 되쓴다.** 그것을 되돌린 것이고, **배너에 적혀 있으므로 그대로 다시 던질 수 있다.**
- ★ **`--virtual-time-budget` 은 쓰지 않는다**(정본 규칙). 이 주제의 실험은 전부 파싱 시점에 끝나므로 필요도 없다.
- ★ **캡처는 파이프를 태우지 않는다** — 출력을 전부 받은 뒤 필터를 걸어야 `(exit N)` 이 참이 된다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 글자 두 개짜리 문서의 트리 | 2 | 동작 방식 (2) · A1 |
| DOCTYPE 유무 — `compatMode`·`doctype`·`lang`·단위 없는 길이 | 2 | 동작 방식 (1) · A2 |
| **호환 모드의 박스 모델**(`width`+`padding`+`border`) | 2 | 동작 방식 (1) · A2 — **재현 안 됨** |
| `title` 없는 문서의 트리와 `document.title` | 2 | 동작 방식 (3) · A3 |
| `head` 안의 텍스트가 뒤 요소를 끌고 내려가는 것 | 2 | 동작 방식 (4) · A4 |
| `<meta charset>` 바이트 위치(16 대 1,252) | 2 | 동작 방식 (5) · A7 |
| 선언 없이 UTF-8·EUC-KR 바이트를 던져 본 것 | 4 | A7 — **자동 감지로 못 잼** |
| 뼈대 한 벌의 트리 | 2 | 동작 방식 (7) |
| 캡처 전체 재대조(`capture.sh` 두 판 `diff`) | 2 | 머리말 「흔들리는 칸」 표 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 호환 모드의 박스 모델 | **안 바뀜**(양쪽 `260`) | Quirks Mode Standard 밖이다 — 엔진마다 다를 수 있다 |
| 1024바이트 넘은 `charset` | **먹음**(재파싱) | 「언제 재파싱하나」가 구현 재량이다 |
| 선언 없을 때의 인코딩 | **자동 감지로 맞힘** | `file://` 스킴 + Chrome 의 감지기. 서버 문서에서는 기대하면 안 된다 |
| `--dump-dom` 의 줄바꿈 자리 | 소스의 텍스트 노드를 그대로 | 직렬화 알고리즘 + 도구 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). 이 갈래는 이식성을 주장하지 않는다. ② **스크린리더가 `lang` 을 어떻게 읽나**(NVDA·VoiceOver 없음) — A9 에 「미실행」으로 표기했다. ③ **「거의 표준 모드」**(`limited-quirks`) — 옛 `PUBLIC` DOCTYPE 을 재현하지 않았다. ④ **재파싱 비용** — 재지 않았으므로 성능 주장을 하지 않는다.

**못 잰 것**(③의 「안 돌려 본 것」과 다르다) — **`<meta charset>` 을 아예 뺐을 때의 깨짐.** 측정 방법 자체가 「**브라우저가 추측하지 못할 것**」을 전제하는데 Chrome 151 이 `file://` 에서 자동 감지를 해 버린다. 쪼개서 잰 조각은 **「어긋난 선언을 주면 깨진다」** 하나다.

## 용어 풀이

- **DOM 트리(Document Object Model tree)** — 파서가 세운 문서의 실제 모양. 소스와 다를 수 있다.
- **DOCTYPE** — 문서 첫 줄의 선언. **트리의 노드**이고, 오늘의 역할은 모드 전환 하나다.
- **표준 모드(standards mode)** — `document.compatMode === "CSS1Compat"`. 오늘의 규칙으로 해석한다.
- **호환 모드(quirks mode)** — `document.compatMode === "BackCompat"`. [Quirks Mode Standard](https://quirks.spec.whatwg.org/) 가 규정한 옛 동작을 켠다.
- **거의 표준 모드(limited-quirks mode)** — 셋째 모드. `compatMode` 로는 표준 모드와 구분되지 않는다.
- **삽입 모드(insertion mode)** — 파서의 상태. 「지금 `head` 안인가 `body` 안인가」로 같은 태그를 달리 처리한다.
- **생략 가능 태그(optional tag)** — 안 써도 파서가 그 요소를 만드는 태그.
- **프리스캔(prescan)** — 파싱 전에 앞 **1024바이트**만 훑어 인코딩 선언을 찾는 단계.
- **인코딩 바꾸기(change the encoding)** — 프리스캔을 넘긴 선언을 만났을 때 **파서를 다시 돌리는** 알고리즘.
- **foster parenting** — 표 안에 올 수 없는 요소를 **표 앞으로 옮기는** 파서 동작([03번 주제](../03-parser-and-error-recovery/2-summary.md)).
- **`--dump-dom`** — 파서가 만든 트리를 직렬화해 표준 출력으로 내놓는 Chrome 플래그. 이 갈래의 **창 ①**.
