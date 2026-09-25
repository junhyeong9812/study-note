# html/syntax/07 — `id` 와 조각 식별자: 문서 내 링크·`:target`·스크롤 앵커 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Navigating to a fragment」](https://html.spec.whatwg.org/multipage/browsing-the-web.html#scrolling-to-a-fragment)·[「The `id` attribute」](https://html.spec.whatwg.org/multipage/dom.html#the-id-attribute) 절과 [WHATWG URL Standard](https://url.spec.whatwg.org/#concept-url-fragment). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **「이식성」을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 지원 상태는 **Baseline** 으로 읽는다. 이 주제가 다루는 것은 전부 **20년 넘게 안정된 표면**이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★ **이 주제의 본체는 창 ② (프로브)다.** 다만 창 ② 만으로는 절반밖에 못 본다 — 조각 식별자가 하는 일의 절반이 **스크롤**이고 그것은 트리에도 IDL 반영에도 안 나타난다. 그래서 이 주제는 **`window.scrollY` 를 창 하나로 더 쓴다.** 창 넷의 정의는 [01번](../01-document-skeleton/2-summary.md) 의 「이 갈래의 창」 절에 있다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · 실행 시각 | 판이 오르면 바뀐다 |
| **흔들린다** | `scrollY` 의 **절댓값**(702·1404·2106) | 칸 높이·테두리·기본 여백에 달렸다 |
| **안 흔들린다** | `scrollY` 가 **0 인가 아닌가 · 앞 값과 같은가** | 이것이 이 주제의 근거다 |
| **안 흔들린다** | `:target` 이 무엇인가(요소 이름 / `null`) | 규칙이 명세에 있다 |
| **안 흔들린다** | `location.hash` 의 **퍼센트 인코딩 꼴** | URL 명세가 정한다 |
| **안 흔들린다** | `getElementById` 가 **몇 번째**를 주나 | DOM 명세가 정한다 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ `#` 뒤는 주소가 아니라 「도착한 뒤에 할 일」이다. 서버는 그 글자를 받아 본 적이 없다.**

건물 주소와 호실 번호에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 도로명 주소 — 우편물이 그걸 보고 온다 | **URL 의 `#` 앞부분**(서버가 받는다) |
| 봉투 구석의 「3층 302호」 메모 | **조각 식별자**(`#s2` — 서버에 안 간다) |
| 문에 붙인 문패 | **`id`** |
| 같은 문패가 둘 — 아무도 안 막는다 | **중복 `id`** |
| 엘리베이터가 그 층에 서는 것 | **스크롤** |
| 그 방에만 켜지는 불 | **`:target`** |
| 「1층 로비로」라는 특별 번호 | **`#top` 과 빈 `#`** |
| 없는 호실을 불렀을 때 | **안 움직인다**(되돌아가지도 않는다) |

- **`#` 뒤가 하는 일은 둘이다** — **스크롤**과 **`:target`**. 둘은 **같이 움직이지만 같은 것이 아니다.**
- **`id` 의 유일성은 강제되지 않는다.** 중복이어도 에러가 없고, `getElementById` 는 **첫째**를 준다.
- 없는 조각으로 가면 「아무 일도 안 일어난다」가 **아니다** — `:target` 이 **꺼진다.**

```text
  주소창의 글자                     어디로 가나
  https://예시/문서.html#s2
  +------------------------+  +--------+
  |    서버가 받는 부분      |  | 안 감  |
  +------------------------+  +--------+
                                   │
                                   ├──> ① 그 id 를 가진 요소로 스크롤한다
                                   └──> ② 그 요소가 `:target` 이 된다
```

```text
  조각이 가리키는 것이 없을 때 — 세 경우가 다 다르다

  #없는이름   ->  스크롤: 안 움직인다(있던 자리 그대로)   :target: null
  #           ->  스크롤: 맨 위로                        :target: null
  #top        ->  id 가 top 인 칸이 있으면 -> 그 칸으로
                  없으면                   -> 맨 위로     :target: null
```

실무에서 이게 터지는 자리는 **탭 UI 를 `#탭이름` 으로 만들 때**다.\
탭을 누를 때마다 **페이지가 위아래로 튀는데** 아무도 스크롤 코드를 쓴 적이 없다 — `#` 이 하는 일이다.\
그리고 없는 탭 이름을 주면 **불만 꺼지고 자리는 그대로**여서, 증상이 「아무 일도 안 일어난다」로 보인다.

> **조각 식별자(fragment identifier)** — URL 의 `#` 뒤 부분. **서버에 전송되지 않는다.**\
> 예: `/문서.html#s2` 에서 서버가 받는 것은 `/문서.html` 까지다.

> **`:target`** — 지금 조각 식별자가 가리키는 요소에 붙는 CSS 의사 클래스.\
> 예: `section:target { background: yellow }` 면 `#가` 로 간 칸만 노래진다.

## 이 주제가 답하려는 질문

1. **`#` 뒤 글자가 무엇을 찾고, 못 찾으면 무슨 일이 일어나나.**
2. **`id` 가 중복이면 무엇이 무엇을 주나.** 유일성은 누가 강제하나.
3. **스크롤과 `:target` 은 항상 같이 움직이나.**

## 동작 방식

### (1) 창 ②+`scrollY` — 조각이 찾는 것과 못 찾았을 때

**언제 쓰나** — 문서 내 링크를 만들 때, 그리고 「**왜 페이지가 튀지?**」 를 물을 때.

같은 문서를 조각만 바꿔 **일곱 번** 새로 띄웠다.

```text
===== for f in '' '#s2' '#한글' '#%ED%95%9C%EA%B8%80' '#옛앵커' '#쌍둥이' '#없는조각'; do echo "-- 조각 '$f'"; dom "file://$PWD/html05b-fragment.html$f" | probe; done =====
-- 조각 ''
location.hash   = ""
window.scrollY  = 0
:target         = null
getElementById('쌍둥이') = "중복 첫째"   [id=쌍둥이] 는 2개
-- 조각 '#s2'
location.hash   = "#s2"
window.scrollY  = 702
:target         = section / "둘째"
getElementById('쌍둥이') = "중복 첫째"   [id=쌍둥이] 는 2개
-- 조각 '#한글'
location.hash   = "#%ED%95%9C%EA%B8%80"
window.scrollY  = 1404
:target         = section / "한글 id"
getElementById('쌍둥이') = "중복 첫째"   [id=쌍둥이] 는 2개
-- 조각 '#%ED%95%9C%EA%B8%80'
location.hash   = "#%ED%95%9C%EA%B8%80"
window.scrollY  = 1404
:target         = section / "한글 id"
getElementById('쌍둥이') = "중복 첫째"   [id=쌍둥이] 는 2개
-- 조각 '#옛앵커'
location.hash   = "#%EC%98%9B%EC%95%B5%EC%BB%A4"
window.scrollY  = 2108
:target         = a / "name 으로만"
getElementById('쌍둥이') = "중복 첫째"   [id=쌍둥이] 는 2개
-- 조각 '#쌍둥이'
location.hash   = "#%EC%8C%8D%EB%91%A5%EC%9D%B4"
window.scrollY  = 2808
:target         = section / "중복 첫째"
getElementById('쌍둥이') = "중복 첫째"   [id=쌍둥이] 는 2개
-- 조각 '#없는조각'
location.hash   = "#%EC%97%86%EB%8A%94%EC%A1%B0%EA%B0%81"
window.scrollY  = 0
:target         = null
getElementById('쌍둥이') = "중복 첫째"   [id=쌍둥이] 는 2개
(exit 0)
```

```text
   조각                          scrollY    :target
   +---------------------------+---------+------------------+
   | (없음)                     | 0       | null             |
   | #s2                       | 702     | section "둘째"    |
   | #한글                      | 1404    | section "한글 id" |
   | #%ED%95%9C%EA%B8%80        | 1404    | section "한글 id" |  <- 같다
   | #옛앵커  (a name=…)        | 2108    | a "name 으로만"  ★ |
   | #쌍둥이  (id 가 둘)         | 2808    | section "중복 첫째" |
   | #없는조각                   | 0   ★   | null             |
   +---------------------------+---------+------------------+
```

그림 해설 (한 단계씩):

- **조각이 맞으면 그 요소로 스크롤하고 그 요소가 `:target` 이 된다.** 둘이 한 번에 일어난다.
- **한글 `id` 도 그대로 먹는다.** 다만 `location.hash` 는 **퍼센트 인코딩된 꼴**(`%ED%95%9C%EA%B8%80`)로 답한다 — 내가 무엇을 쳤든 같다. ★ **주소창에 보이는 글자와 `location.hash` 가 답하는 글자가 다르다.**
- **`<a name="…">` 은 아직 먹는다.** `:target` 이 그 `<a>` 요소에 붙었다. ★ 다만 [06번 주제](../06-global-attributes/2-summary.md)에서 본 **전역 이름**은 `<a name>` 으로 안 생겼다 — **두 규칙이 다르다.**
- **`id` 가 중복이면 첫째로 간다.** `getElementById` 도 첫째를 준다.
- **없는 조각으로 새로 띄우면 `scrollY` 가 0 이다** — 갈 곳이 없어 **그냥 맨 위에서 시작**한 것이지 「맨 위로 갔다」가 아니다. 그 구분은 아래 (2) 가 가른다.

### (2) 창 ②+`scrollY` — `#top` 과 빈 `#` 의 특별 취급

**언제 쓰나** — 「맨 위로」 링크를 만들 때. 그리고 「**없는 조각과 빈 조각이 같겠지**」라고 생각할 때.

한 문서 안에서 조각을 **여섯 번 갈아 끼우며** 위치를 읽었다. 두 판은 **`id="top"` 인 칸이 있고 없고만 다르다.**

```text
===== 소스: html05b-top.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>#top 과 빈 조각과 없는 조각</title>
<style>
  body { margin: 0; }
  section { height: 700px; border-top: 2px solid #999; }
</style>
</head>
<body>
<section id="s1">첫째</section>
<section id="s2">둘째</section>
<section id="top">id 가 top 인 칸</section>
<section id="s4">넷째</section>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
  const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
  const o = [];
  const 간다 = (h, 설명) => { location.hash = h; o.push(pad("location.hash = " + JSON.stringify(h), 34)
      + "scrollY = " + pad(String(Math.round(window.scrollY)), 6) + 설명); };
  o.push(pad("처음", 34) + "scrollY = " + Math.round(window.scrollY));
  간다("#s4", "맞는 id 가 있다");
  간다("#top", "id 가 top 인 칸이 있다");
  간다("#s4", "");
  간다("#", "빈 조각");
  간다("#s4", "");
  간다("#없는이름", "맞는 것이 아무것도 없다");
  o.push("");
  o.push("마지막 :target = " + document.querySelector(":target")
         + "   location.hash = " + JSON.stringify(decodeURIComponent(location.hash)));
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
===== dom html05b-top.html | probe =====
처음                              scrollY = 0
location.hash = "#s4"             scrollY = 2106  맞는 id 가 있다
location.hash = "#top"            scrollY = 1404  id 가 top 인 칸이 있다
location.hash = "#s4"             scrollY = 2106  
location.hash = "#"               scrollY = 0     빈 조각
location.hash = "#s4"             scrollY = 2106  
location.hash = "#없는이름"       scrollY = 2106  맞는 것이 아무것도 없다

마지막 :target = null   location.hash = "#없는이름"
(exit 0)
```

```text
===== 소스: html05b-top-none.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>#top — 맞는 id 가 없을 때</title>
<style>
  body { margin: 0; }
  section { height: 700px; border-top: 2px solid #999; }
</style>
</head>
<body>
<section id="s1">첫째</section>
<section id="s2">둘째</section>
<section id="s3">셋째 — id 가 top 인 칸이 없다</section>
<section id="s4">넷째</section>
<script>
window.addEventListener("load", () => setTimeout(() => {
  const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
  const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
  const o = [];
  const 간다 = (h, 설명) => { location.hash = h; o.push(pad("location.hash = " + JSON.stringify(h), 34)
      + "scrollY = " + pad(String(Math.round(window.scrollY)), 6) + 설명); };
  o.push(pad("처음", 34) + "scrollY = " + Math.round(window.scrollY));
  간다("#s4", "맞는 id 가 있다");
  간다("#top", "id 가 top 인 칸이 없다");
  간다("#s4", "");
  간다("#", "빈 조각");
  간다("#s4", "");
  간다("#없는이름", "맞는 것이 아무것도 없다");
  o.push("");
  o.push("마지막 :target = " + document.querySelector(":target")
         + "   location.hash = " + JSON.stringify(decodeURIComponent(location.hash)));
  const q = document.createElement("pre");
  q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
  document.body.appendChild(q);
}, 0));
</script>
</body>
</html>
===== dom html05b-top-none.html | probe =====
처음                              scrollY = 0
location.hash = "#s4"             scrollY = 2106  맞는 id 가 있다
location.hash = "#top"            scrollY = 0     id 가 top 인 칸이 없다
location.hash = "#s4"             scrollY = 2106  
location.hash = "#"               scrollY = 0     빈 조각
location.hash = "#s4"             scrollY = 2106  
location.hash = "#없는이름"       scrollY = 2106  맞는 것이 아무것도 없다

마지막 :target = null   location.hash = "#없는이름"
(exit 0)
```

```text
                    id="top" 인 칸이 있는 판      id="top" 인 칸이 없는 판
   +----------------+---------------------------+---------------------------+
   | 처음            | scrollY 0                 | scrollY 0                 |
   | #s4 로          | 2106                      | 2106                      |
   | #top 으로       | 1404  (그 칸으로 간다)      | 0     (맨 위로 간다)  ★    |
   | #s4 로          | 2106                      | 2106                      |
   | # (빈 조각)     | 0     (맨 위로)            | 0     (맨 위로)            |
   | #s4 로          | 2106                      | 2106                      |
   | #없는이름       | 2106  (안 움직인다) ★       | 2106  (안 움직인다) ★      |
   +----------------+---------------------------+---------------------------+
   | 끝의 :target    | null                      | null                      |
```

그림 해설:

- **`#top` 은 두 단계로 찾는다.** ① `id="top"` 인 요소를 찾고 ② 없으면 **문서의 맨 위**를 가리킨다. 두 판의 세 번째 줄이 **1404 대 0** 으로 갈린 것이 그 증거다.
- **빈 `#` 은 항상 맨 위다.** 찾을 이름이 없으므로 ② 로 바로 간다.
- ★★ **없는 이름은 완전히 다르다 — 안 움직인다.** `#s4` 에서 `#없는이름` 으로 가도 `scrollY` 가 **2106 그대로**다. 「맨 위로 되돌아간다」가 아니다.
- **셋 다 `:target` 은 `null` 이다.** ★ **`#top` 으로 그 칸에 가더라도** 맞는 요소가 없으면 `:target` 은 안 켜진다 — **스크롤과 `:target` 이 갈리는 자리**가 여기다.
- **`location.hash` 는 실패해도 남는다.** 마지막 줄이 `"#없는이름"` 이다 — **주소는 바뀌었는데 아무 데도 안 갔다.**

### (3) 창 ② — `id` 값의 경계

**언제 쓰나** — `id` 를 기계가 생성할 때(숫자로 시작하거나 공백이 섞인다).

```text
===== 소스: html05b-id-edge.html =====
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>id 값의 경계</title>
</head>
<body>
<p id="">빈 id</p>
<p id="a b">공백이 든 id</p>
<p id="3a">숫자로 시작하는 id</p>
<p id=" 앞뒤공백 ">앞뒤에 공백이 있는 id</p>
<script>
const w = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const pad = (s, n) => s + " ".repeat(Math.max(0, n - w(s)));
const o = [];
const 본다 = (설명, f) => { try { o.push(pad(설명, 32) + "-> " + f()); } catch (e) { o.push(pad(설명, 32) + "-> " + e.name); } };
const 글자 = e => e === null ? "null" : JSON.stringify(e.textContent);
본다('getElementById("")',          () => 글자(document.getElementById("")));
본다('getElementById("a b")',       () => 글자(document.getElementById("a b")));
본다('getElementById("3a")',        () => 글자(document.getElementById("3a")));
본다('getElementById(" 앞뒤공백 ")', () => 글자(document.getElementById(" 앞뒤공백 ")));
본다('getElementById("앞뒤공백")',   () => 글자(document.getElementById("앞뒤공백")));
본다('querySelector("#3a")',        () => 글자(document.querySelector("#3a")));
본다('querySelector("[id=\'3a\']")', () => 글자(document.querySelector("[id='3a']")));
본다('querySelector("#\\\\33 a")',   () => 글자(document.querySelector("#\\33 a")));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
</body>
</html>
===== dom html05b-id-edge.html | probe =====
getElementById("")              -> null
getElementById("a b")           -> "공백이 든 id"
getElementById("3a")            -> "숫자로 시작하는 id"
getElementById(" 앞뒤공백 ")    -> "앞뒤에 공백이 있는 id"
getElementById("앞뒤공백")      -> null
querySelector("#3a")            -> SyntaxError
querySelector("[id='3a']")      -> "숫자로 시작하는 id"
querySelector("#\\33 a")        -> "숫자로 시작하는 id"
(exit 0)
```

```text
   id 값           getElementById        querySelector
   +--------------+--------------------+---------------------------+
   | ""           | null          ★    | (빈 선택자는 못 쓴다)       |
   | "a b"        | 찾는다  ★          | #a\ b 로 이스케이프해야     |
   | "3a"         | 찾는다             | "#3a" -> SyntaxError  ★   |
   | " 앞뒤공백 "  | 정확히 같아야 찾는다 | [id=' 앞뒤공백 '] 로       |
   +--------------+--------------------+---------------------------+
```

그림 해설:

- **`id=""` 는 어떤 요소도 못 찾는다.** 명세가 **빈 `id` 를 금지**하고, `getElementById("")` 는 `null` 이다.
- **공백이 든 `id` 도 파서는 담는다.** 명세는 공백을 금지하지만 **파서가 안 고친다** — [05번 주제](../05-content-categories-and-models/2-summary.md)의 「무효인데 그대로」와 같은 집안이다.
- **앞뒤 공백은 안 깎인다.** `getElementById(" 앞뒤공백 ")` 은 찾고 `getElementById("앞뒤공백")` 은 `null` 이다.
- ★★ **`getElementById` 와 `querySelector` 가 갈린다.** 앞엣것은 **문자열을 그대로 비교**하고, 뒤엣것은 **CSS 선택자 문법**을 거친다. `#3a` 는 CSS 에서 유효한 식별자가 아니라 **`SyntaxError` 를 던진다.**
- **우회는 둘이다** — `[id='3a']` 속성 선택자, 또는 `#\33 a` 로 이스케이프. 둘 다 이 판에서 찾아냈다.

### (4) 창 ② — 조각은 서버에 가지 않는다

**언제 쓰나** — 「`#tab=2` 를 서버가 읽게 하자」는 말이 나올 때.

★ **이 한 줄은 이 주제에서 실행으로 확인한 것이 아니다** — [URL 명세](https://url.spec.whatwg.org/#concept-url-fragment)와 HTTP 의 규칙을 읽어 적은 것이다.\
요청 줄에 실리는 것은 **경로와 질의 문자열까지**이고 조각은 **브라우저 안에 남는다.**

```text
   주소창                           네트워크로 나가는 것
   /문서.html?tab=2#s2     ==>     GET /문서.html?tab=2
   +-----------------+             +--------------------+
   | ?tab=2  서버 몫  |             | 여기까지만          |
   | #s2     브라우저 |             |                    |
   +-----------------+             +--------------------+
```

- **그래서 `#` 상태는 서버 렌더에 못 쓴다.** 서버는 그 값을 본 적이 없다.
- **그래서 `#` 을 바꾸는 것은 페이지를 다시 받지 않는다.** (2) 에서 조각을 여섯 번 갈아 끼웠는데 **문서는 한 번만 띄웠다.**

### (5) demo — `:target` 은 켜지고 꺼진다

```html demo
<nav><a href="#가">가로</a> · <a href="#나">나로</a> · <a href="#없다">없는 곳으로</a></nav>
<section id="가">가 칸</section>
<section id="나">나 칸</section>
<style>
  section { padding: 8px; border: 2px solid #94a3b8; margin: 4px 0; }
  section:target { background: #fde68a; border-color: #b45309; }
</style>
```

> **보이는 것** — 「가로」를 누르면 **가 칸만** 노랗게 켜지고 테두리가 진해진다. 「나로」를 누르면 **가 칸이 꺼지고 나 칸이 켜진다** — 한 번에 하나만 켜진다.\
> **바꿔 볼 것** — 「없는 곳으로」를 누르면 → **둘 다 꺼진다**(`:target` 이 `null` 이 된다). 주소의 `#없다` 는 그대로 남는데 **켜진 칸은 없다** · 링크를 누르지 않고 처음 상태로 두면 → 처음부터 **둘 다 꺼져 있다**.
>
> *(Chrome 151 headless 실측, 창 폭 780: 켜진 칸의 배경이 `rgb(253, 230, 138)` · 꺼진 칸은 `rgba(0, 0, 0, 0)` · 「없는 곳」 뒤 `location.hash` 는 `"#없다"`)*

★ 「보이는 것」과 「바꿔 볼 것」의 단언을 **한 블록에서 네 단계로 이어 던져** 확인했다 — [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 문서 내 링크

```html
<a href="#s2">둘째 칸으로</a>
<a href="#">맨 위로</a>
<a href="#top">맨 위로 (id 가 top 인 칸이 없을 때만)</a>
<section id="s2">둘째</section>
```

### 금지 사례 — 명세가 막는데 파서는 안 막는 것

```html
<p id="">빈 id</p>
<p id="a b">공백이 든 id</p>
<p id="쌍둥이">첫째</p>
<p id="쌍둥이">둘째</p>
```

### 어디서 헷갈리나

- **`href="#"` 과 `href="#top"` 은 같지 않다.** 뒤엣것은 `id="top"` 인 요소를 **먼저 찾는다.**
- **`#없는이름` 은 「맨 위로」가 아니다.** 안 움직인다.
- **`getElementById` 와 `#선택자` 는 다른 문법을 쓴다.** 숫자로 시작하는 `id` 에서 갈린다.

## 어디서 틀리나

### 1. `id` 가 유일하다고 믿고 코드를 짠다

**아무도 안 막는다.** 중복이어도 에러가 없고 `getElementById` 는 **첫째**를 준다.\
★ [06번 주제](../06-global-attributes/2-summary.md)에서 본 대로 **`window.쌍둥이` 는 요소가 아니라 `HTMLCollection` 이 된다** — 같은 중복이 **두 API 에서 다른 모양으로** 드러난다.

### 2. 「없는 조각 = 맨 위로」라고 외운다

**안 움직인다.** 맨 위로 가는 것은 **빈 `#`** 과 **`id="top"` 이 없을 때의 `#top`** 뿐이다.

### 3. 탭 UI 를 `#` 으로 만들고 스크롤이 튄다고 한다

`#` 이 하는 일이 **스크롤과 `:target` 둘**이라서 그렇다.\
★ 스크롤만 끄는 방법은 이 주제 밖이다 — 마크업으로는 못 끈다.

### 4. `location.hash` 로 문자열을 비교한다

**퍼센트 인코딩된 꼴이 온다.** 한글 `id` 는 `#%ED%95%9C%EA%B8%80` 이다.\
★ `decodeURIComponent` 를 거치지 않고 `=== "#한글"` 로 비교하면 **항상 거짓**이다.

### 5. 숫자로 시작하는 `id` 를 `#선택자` 로 찾는다

**`SyntaxError` 를 던진다.** `getElementById` 는 찾는데 `querySelector("#3a")` 는 던진다.\
★ **에러가 나는 쪽이 오히려 낫다** — 조용히 못 찾는 것보다 원인이 보인다.

### 6. `#` 값을 서버가 읽을 수 있다고 본다

**서버는 그 글자를 받은 적이 없다.** 조각은 브라우저 안에만 있다.

## 구현 세부사항 대 언어 보장

★ **HTML 은 명세가 오류 복구까지 정한 언어**라 「구현 정의」 칸이 작다. 세 층으로 갈라 적는다.

| 층 | 무엇을 보장하나 | 이 주제에서 |
|---|---|---|
| **명세(URL)** | 조각이 서버에 안 간다 · 퍼센트 인코딩 꼴 | `location.hash` 의 인코딩 |
| **명세(HTML)** | 「가리키는 부분」을 찾는 절차 — `id` → `name` → `top` → 맨 위 | `#top` 의 두 단계 · `<a name>` 이 아직 먹는 것 |
| **명세(HTML)** | `id` 는 **비어 있으면 안 되고 공백을 포함하면 안 된다** | `id=""`·`id="a b"` 가 **무효**인 근거 |
| **명세(DOM)** | `getElementById` 는 **트리 순서로 첫째** | 중복 `id` 에서 첫째가 오는 것 |
| **명세(CSS Selectors)** | `:target` 의 정의 · 식별자 문법 | `#3a` 가 `SyntaxError` 인 근거 |
| **구현(Blink)** | 명세 구현 | 이 판의 출력이 명세와 어긋난 자리를 **찾지 못했다** |
| **이 판의 관찰** | Chrome 151 이 실제로 뱉은 것 | `scrollY` 값들 · `:target` 이 `null` 이 되는 자리 |

**도구가 못 보는 것**

- **부드러운 스크롤·스크롤 앵커링.** 이 판은 **최종 위치**만 읽었다. 가는 도중에 무슨 일이 일어나는지는 안 봤다.
- **뒤로 가기·앞으로 가기.** 조각 이동이 방문 기록에 쌓이는 것은 이 배치에서 **안 던졌다.**
- **주소창.** headless 에는 주소창이 없다 — 「주소창에 보이는 글자」는 `location.hash` 로 대신 읽은 것이다.
- **다른 엔진.** Chrome 하나뿐이라 이식성을 주장할 수 없다.

## 언제 쓰고 언제 안 쓰나

- **`id` 는 문서에 하나만** — 강제되지 않으므로 **내가 지켜야 한다.**
- **`id` 는 글자로 시작하게** — 숫자로 시작하면 `#선택자` 가 못 쓴다.
- **문서 내 링크는 `<a href="#…">` 로** — 스크롤 코드를 쓰지 않는다. 브라우저가 하는 일이다.
- **`:target` 은 「지금 어디를 가리키나」에만** — 탭의 **상태 저장**으로 쓰면 없는 이름에서 **전부 꺼진 상태**가 생긴다.
- **`<a name>` 은 새로 쓰지 않는다** — 아직 먹지만 `id` 가 하는 일을 다 못 한다([06번 주제](../06-global-attributes/2-summary.md)).

## 핵심 문장

1. **`#` 뒤는 서버에 가지 않는다. 브라우저가 도착한 뒤에 하는 일이다.**
2. **`#` 이 하는 일은 스크롤과 `:target` 둘이고, `#top` 에서 그 둘이 갈린다.**
3. **없는 조각은 「맨 위로」가 아니라 「안 움직임」이다 — 그리고 `:target` 은 꺼진다.**
4. **`id` 의 유일성은 강제되지 않는다. `getElementById` 는 첫째를 주고, 전역 이름은 `HTMLCollection` 이 된다.**
5. **`getElementById` 는 문자열을 그대로 보고 `#선택자` 는 CSS 문법을 거친다 — 숫자로 시작하는 `id` 에서 갈린다.**

## 관련 자료

- [06번 주제 — 전역 속성](../06-global-attributes/2-summary.md) — **전역 속성으로서의 `id` 는 그쪽이다.** 여기는 **URL 과 스크롤**부터.
- [05번 주제 — 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — 「무효인데 파서가 안 고친다」의 정본. `id="a b"` 가 같은 집안이다.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **10번** — **`:target` 을 선택자로서 다루는 것은 그쪽이 정본이다**(다른 상태 의사 클래스와 나란히). 여기는 **조각 식별자가 그것을 켜고 끄는 것**까지.
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **02번**·**11번** — `getElementById` 계열과 스크롤 제어 API 는 그쪽이 정본이다.
- 목록의 **16번 주제**(링크) — `href` 의 형태·`target`·`rel`. **바깥으로 가는 링크**가 그쪽이고, 여기는 **문서 안**이다.

## 용어 풀이

- **조각 식별자(fragment identifier)** — URL 의 `#` 뒤 부분. 서버에 전송되지 않는다.
- **가리키는 부분(indicated part)** — 조각 식별자가 지목한 문서의 자리. 명세의 용어다.
- **`:target`** — 가리키는 부분인 요소에 붙는 CSS 의사 클래스. 한 문서에 **많아야 하나**다.
- **`id`** — 문서 안에서 유일해야 하는 이름. **비어 있으면 안 되고 공백을 포함하면 안 된다.**
- **`<a name>`** — 옛 방식의 앵커. 조각 식별자로는 아직 먹지만 새로 쓰지 않는다.
- **퍼센트 인코딩(percent-encoding)** — URL 에서 ASCII 밖 글자를 `%XX` 로 적는 방식.
- **스크롤 앵커** — 조각 식별자가 스크롤을 일으키는 것. 브라우저가 하는 일이고 스크립트가 아니다.

## 더 들어가면

- **왜 `#top` 만 특별한가** — 아주 오래된 문서들이 `<a href="#top">` 를 「맨 위로」로 써 왔기 때문이다. 명세는 그 관용을 **찾는 절차의 마지막 단계**로 못 박았다. [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 「절대 멈추지 않는다」와 같은 집안의 결정이다.
- **왜 없는 조각에서 안 움직이나** — 「가리키는 부분이 없으면 **스크롤 위치를 바꾸지 않는다**」가 명세의 처리다. 「맨 위로」로 처리했다면 링크 하나 잘못 눌러 읽던 자리를 잃게 된다.
- **`:target` 이 하나뿐인 이유** — 「가리키는 부분」이 하나이기 때문이다. 그래서 여러 칸을 동시에 켜는 UI 는 `:target` 으로 못 만든다.
