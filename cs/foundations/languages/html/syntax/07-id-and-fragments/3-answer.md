# html/syntax/07 — `id` 와 조각 식별자: 문서 내 링크·`:target`·스크롤 앵커 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [URL Standard](https://url.spec.whatwg.org/) 로 접지했다 — **이 주제는 두 명세에 걸쳐 있다.**\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★ **`scrollY` 의 절댓값은 흔들리는 칸이다.** 근거로 쓰는 것은 「**0 인가 · 앞 값과 같은가**」뿐이다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 맞으면 스크롤과 `:target` 이 같이 오고, 없는 조각은 둘 다 없다

**출력** (Chrome 151 headless)

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

**왜 그런가**

| 조각 | `scrollY` | `:target` | 왜 |
|---|---|---|---|
| (없음) | 0 | `null` | 가리키는 부분이 없다 |
| `#s2` | 0 아님 | `section "둘째"` | `id` 가 맞았다 |
| `#한글` | 0 아님 | `section "한글 id"` | 한글 `id` 도 그대로 먹는다 |
| `#%ED%95%9C%EA%B8%80` | **앞 줄과 같다** | 〃 | **같은 조각이다** |
| `#옛앵커` | 0 아님 | **`a "name 으로만"`** | `<a name>` 이 아직 먹는다 |
| `#쌍둥이` | 0 아님 | `section "중복 첫째"` | **첫째**가 가리키는 부분이 된다 |
| `#없는조각` | **0** | `null` | 갈 곳이 없어 **맨 위에서 시작**한 것 |

- **`location.hash` 는 언제나 퍼센트 인코딩된 꼴로 답한다.** `#한글` 로 띄워도 `"#%ED%95%9C%EA%B8%80"` 이다 — 두 판의 `scrollY` 가 같은 것이 **같은 조각임의 증거**다.
- **`<a name>` 이 아직 먹는 이유** — 명세의 「가리키는 부분을 찾는」 절차가 `id` 다음에 **`name` 속성을 가진 `<a>`** 를 본다. ★ 다만 [06번 주제](../06-global-attributes/3-answer.md)에서 본 **전역 이름**은 `<a name>` 으로 **안 생겼다.** 두 규칙이 다르다.
- **중복 `id` 는 첫째다.** `getElementById('쌍둥이')` 도 `"중복 첫째"` 를 주고, `[id='쌍둥이']` 로는 **2개**가 잡힌다 — **중복을 막는 장치가 어디에도 없다.**
- ★ **마지막 줄의 `scrollY = 0` 을 「맨 위로 갔다」로 읽으면 안 된다.** 새로 띄운 판이라 원래 0 이었다. 「안 움직인다」와 「맨 위로 간다」를 가르려면 **이미 스크롤된 상태에서** 던져야 한다 — A2 가 그것이다.

### 2. `#top` 에서만 갈린다 — 그리고 없는 이름은 안 움직인다

**출력**

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

**왜 그런가**

- **두 판이 다른 곳은 세 번째 칸 하나다** — 한쪽은 `id="top"`, 다른 쪽은 `id="s3"`.
- **갈리는 줄은 세 번째다.** `#top` 으로 갔을 때 한쪽은 **그 칸으로**(1404), 다른 쪽은 **맨 위로**(0).
- **명세의 절차가 그대로 보인다.** ① `id` 가 맞는 요소 → ② `name` 이 맞는 `<a>` → ③ 조각이 **빈 문자열이거나 `top`**(대소문자 무시)이면 **문서의 맨 위** → ④ 그 밖이면 **가리키는 부분이 없다.**
- **빈 `#` 은 두 판 다 0 이다** — ③ 으로 바로 간다.
- ★★ **`#없는이름` 은 두 판 다 `2106` 그대로다.** ④ 이므로 **스크롤 위치를 바꾸지 않는다.** 「맨 위로 되돌아간다」가 아니다.
- **마지막 `:target` 은 두 판 다 `null` 이다.** ★ `#top` 으로 그 칸에 **갔는데도** `:target` 이 안 켜질 수 있다 — ③ 으로 간 경우가 그렇다. **스크롤과 `:target` 이 갈리는 자리**가 여기다.
- **`location.hash` 는 실패해도 남는다** — `"#없는이름"` 이다. **주소는 바뀌었는데 아무 데도 안 갔다.**

### 3. `getElementById` 는 글자를 그대로 보고 `#선택자` 는 CSS 문법을 거친다

**출력**

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

**왜 그런가**

- **`getElementById("")` 는 `null`** — 명세가 **빈 `id` 를 금지**한다. 트리에는 `id=""` 가 담겨 있지만 찾기의 대상이 아니다.
- **공백이 든 `id` 는 찾힌다.** 명세는 `id` 에 **공백을 금지**하는데 **파서는 안 고치고** `getElementById` 는 **문자열을 그대로 비교**하므로 찾힌다. ★ [05번 주제](../05-content-categories-and-models/3-answer.md)의 「무효인데 그대로」와 같은 집안이다.
- **앞뒤 공백은 안 깎인다.** `getElementById(" 앞뒤공백 ")` 은 찾고 `"앞뒤공백"` 은 `null` 이다.
- **`querySelector("#3a")` 는 `SyntaxError` 를 던진다.** CSS 식별자는 **숫자로 시작할 수 없다** — 선택자 파서가 거기서 멈춘다.
- **우회 둘** — `[id='3a']` 속성 선택자와 `#\33 a` 이스케이프. **둘 다 이 판에서 요소를 찾아냈다.**
- ★ **던지는 쪽이 오히려 낫다.** 조용히 `null` 을 주면 「왜 못 찾지」에서 막히는데, `SyntaxError` 는 **원인을 말해 준다.**

### 4. 명세가 정하고 아무도 강제하지 않는다

**왜 그런가**

- **정한 것은 명세다** — 「`id` 속성 값은 문서 안에서 **유일해야 하고**, **비어 있으면 안 되고**, **ASCII 공백을 포함하면 안 된다**」.
- **중복이어도 에러가 없다.** 파서는 담고, CSS 는 둘 다 잡고, `getElementById` 는 하나를 고른다. ★ 이 환경에 **마크업 검증기가 없어** 무효라는 판정 자체를 도구로 못 한다(A1 의 실험은 **트리와 동작**만 잰 것이다).
- **`getElementById` 는 트리 순서로 첫째를 준다.** DOM 명세가 정한다.
- **[06번 주제](../06-global-attributes/3-answer.md)에서는 다른 모양으로 드러났다** — `window.쌍둥이` 가 요소가 아니라 **`HTMLCollection`(length 2)** 이 된다. **같은 중복이 한쪽에서는 「첫째」, 다른 쪽에서는 「타입이 바뀜」으로 나타난다.**

### 5. 둘 다 일어나는 경우와 스크롤만 일어나는 경우가 있다

**왜 그런가**

- **조각 식별자가 하는 일 둘** — ① **가리키는 부분으로 스크롤**, ② 그 요소가 **`:target`** 이 된다.
- **같이 일어나는 경우** — 조각이 `id` 나 `<a name>` 과 맞았을 때(A1 의 다섯 줄).
- **스크롤만 일어나는 경우** — **빈 `#`** 과 **`id="top"` 이 없을 때의 `#top`**. 맨 위로 가는데 `:target` 은 `null` 이다(A2).
- **둘 다 안 일어나는 경우** — 없는 이름. 안 움직이고 `:target` 도 없다.
- **`:target` 은 많아야 하나다.** 「가리키는 부분」이 하나이기 때문이다.
- ★ **그래서 여러 칸을 동시에 켜는 UI 는 `:target` 으로 못 만든다.** 아코디언을 여럿 펼쳐 두는 형태가 그 예다.

### 6. 셋이 세 갈래로 다르다

**왜 그런가**

| 조각 | 어디로 | `:target` | `location.hash` |
|---|---|---|---|
| `#없는이름` | **안 움직인다** | `null` | `"#없는이름"` 으로 남는다 |
| `#`(빈 조각) | 맨 위로 | `null` | `"#"` |
| `#top` | `id="top"` 이 있으면 **그 칸으로** · 없으면 **맨 위로** | 앞쪽이면 그 요소 · 뒤쪽이면 `null` | `"#top"` |

- **스크롤 위치를 안 바꾸는 것은 `#없는이름` 하나다.**
- **`#top` 의 답이 문서에 따라 갈리는 이유** — 절차가 **`id` 먼저, `top` 은 마지막**이기 때문이다. 내 문서에 `id="top"` 인 요소가 있으면 그쪽이 이긴다.
- **실패해도 주소는 바뀐다.** 그래서 「주소가 바뀌었으니 갔겠지」는 근거가 못 된다.

### 7. 조각으로는 먹고 전역 이름은 못 만든다

**왜 그런가**

- **하는 일** — 조각 식별자의 **가리키는 부분**이 된다(A1 에서 `:target` 이 그 `<a>` 에 붙었다).
- **못 하는 일** — **`window.이름` 을 만들지 못한다**([06번 주제](../06-global-attributes/3-answer.md)에서 `undefined` 였다). `getElementById` 로도 안 잡힌다 — `id` 가 아니기 때문이다.
- **갈리는 이유** — 두 규칙이 서로 다른 목록을 본다. **조각 찾기**는 `name` 을 가진 `<a>` 를 보고, **이름 있는 접근**은 `<form>`·`<img>`·`<embed>`·`<object>`·`<iframe>` 의 `name` 만 본다.
- **새로 쓰지 않는다.** 명세가 `<a name>` 을 **폐기**(obsolete)로 표시했다. 지금 동작하는 것은 **옛 문서 호환** 때문이다.

### 8. 동작하고, 주소는 인코딩되고, 문자열 비교는 깨진다

**왜 그런가**

- **동작한다.** `#한글` 로 띄우면 그 칸으로 간다.
- **`location.hash` 는 `"#%ED%95%9C%EA%B8%80"` 을 답한다.** URL 명세가 조각을 **퍼센트 인코딩된 꼴로 직렬화**하기 때문이다.
- **인코딩해서 넣은 것과 그냥 넣은 것이 같다.** A1 의 두 줄이 `scrollY`·`:target` 까지 한 글자도 같았다.
- **`location.hash === "#한글"` 은 항상 거짓이다.** `decodeURIComponent(location.hash)` 를 거쳐야 한다 — A2 의 마지막 줄이 그렇게 읽은 것이다.
- ★ **이것은 HTML 의 규칙이 아니라 URL 의 규칙이다.** 층을 갈라 적어야 「HTML 이 한글을 못 쓴다」는 틀린 말이 안 생긴다.

### 9. 근거가 다르다 — 문자열 대 CSS 식별자

**왜 그런가**

- **`getElementById`** — 트리의 `id` 값과 **주어진 문자열을 그대로 비교**한다. 공백·숫자·빈 문자열 상관없이 **글자만 같으면** 찾는다(빈 문자열은 예외로 `null`).
- **`querySelector("#…")`** — **CSS 선택자 문법**으로 먼저 파싱한다. 문법에 안 맞으면 **찾기 전에 던진다.**
- **갈리는 값** — `id="3a"`. `getElementById` 는 찾고 `querySelector("#3a")` 는 **`SyntaxError`**.
- **우회 둘** — `[id='3a']`(속성 선택자는 값이 문자열이라 문법 제약이 없다) · `#\33 a`(CSS 이스케이프 — `3` 의 코드 포인트를 16진으로 적고 공백으로 끝낸다).

### 10. 서버는 `?tab=2` 까지만 받는다

**왜 그런가**

- **요청에 실리는 것은 경로와 질의 문자열까지**이고 조각은 **브라우저 안에 남는다.** `GET /문서.html?tab=2` 가 나간다.
- **그래서 `#` 상태를 서버 렌더에 쓸 수 없다.** 서버는 그 값을 본 적이 없다.
- **`#` 만 바꾸면 문서를 다시 받지 않는다.** A2 가 그 증거다 — 조각을 **여섯 번 갈아 끼웠는데 문서는 한 번만 띄웠다.**
- ★ **이 답의 근거는 반반이다.** 「다시 안 받는다」는 **실행으로 봤고**(A2), 「서버에 안 간다」는 **URL·HTTP 명세를 읽어 적은 것**이다. 이 주제에서 네트워크 요청을 찍어 확인하지 않았다.

### 11. 정본 경계

**왜 그런가**

| 무엇 | 정본 | 여기는 |
|---|---|---|
| `:target` 을 **선택자로서** 다루는 것 | CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **10번** | 다른 상태 의사 클래스와 나란히 놓는 것은 그쪽. 여기는 **조각이 그것을 켜고 끄는 것**까지 |
| `getElementById`·`querySelector`·`scrollIntoView` | web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **02번**·**11번** | API 는 그쪽. 여기서는 **찾는 근거가 갈리는 것**만 봤다 |
| 전역 속성으로서의 `id` | [06번 주제](../06-global-attributes/3-answer.md) | 그쪽은 **속성**, 여기는 **URL 과 스크롤** |
| `href`·`target`·`rel` | [목록의 **16번 주제**](../16-links/) | 그쪽은 **바깥으로**, 여기는 **문서 안** |

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · 기본 창 폭 **780**. **엔진은 이것 하나다.** **주소창이 없어** 「주소창에 보이는 글자」는 `location.hash` 로 대신 읽었다.

**하네스** — 05\~08 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe` 가 그 함수들이다.

```bash
# html05b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
serve() { python3 html05b-server.py >"$1" 2>&1 & echo $!; }
```

- ★ **조각을 바꿔 가며 띄우는 판은 `file://` 절대 경로로 던졌다** — 상대 경로에 `#` 을 붙이면 조각이 아니라 파일 이름의 일부가 된다.
- ★ **프로브를 `load` 뒤 `setTimeout(…, 0)` 에서 찍는다.** 조각 스크롤은 문서 로드가 끝난 뒤에 일어나므로 파싱 중에 읽으면 `scrollY` 가 0 으로 보인다. ★★ **`--dump-dom` 은 `load` 와 `setTimeout(…, 0)` 까지는 기다린다**([08번 주제](../08-script-loading/3-answer.md)에서 그 한계를 잰다).
- ★ **`--virtual-time-budget` 은 쓰지 않는다**(정본 규칙).

**demo 블록 검증** — 문서의 `demo` 블록에 래퍼와 측정 프로브를 붙인 사본을 따로 띄워 `보이는 것` 과 `바꿔 볼 것` 을 **한 블록에서 네 단계로 이어** 확인했다.

```text
===== 소스: html05b-demo07a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 07 검증</title>
<body>
<nav><a href="#가">가로</a> · <a href="#나">나로</a> · <a href="#없다">없는 곳으로</a></nav>
<section id="가">가 칸</section>
<section id="나">나 칸</section>
<style>
  section { padding: 8px; border: 2px solid #94a3b8; margin: 4px 0; }
  section:target { background: #fde68a; border-color: #b45309; }
</style>
<script>
const o = [];
const 폭 = s => [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 칸 = (s, n) => s + " ".repeat(Math.max(0, n - 폭(s)));
const 바탕 = id => getComputedStyle(document.getElementById(id)).backgroundColor;
const 줄 = 설명 => o.push(칸(설명, 22) + "가 = " + 칸(바탕("가"), 20) + " 나 = " + 칸(바탕("나"), 20)
  + " :target = " + ((document.querySelector(":target") || {}).id || "null"));
줄("처음");
document.querySelector('a[href="#가"]').click(); 줄("#가 링크를 누름");
document.querySelector('a[href="#나"]').click(); 줄("#나 링크를 누름");
document.querySelector('a[href="#없다"]').click(); 줄("#없다 링크를 누름");
o.push("마지막 location.hash = " + JSON.stringify(decodeURIComponent(location.hash)));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html05b-demo07a.html | probe =====
처음                  가 = rgba(0, 0, 0, 0)     나 = rgba(0, 0, 0, 0)     :target = null
#가 링크를 누름       가 = rgb(253, 230, 138)   나 = rgba(0, 0, 0, 0)     :target = 가
#나 링크를 누름       가 = rgba(0, 0, 0, 0)     나 = rgb(253, 230, 138)   :target = 나
#없다 링크를 누름     가 = rgba(0, 0, 0, 0)     나 = rgba(0, 0, 0, 0)     :target = null
마지막 location.hash = "#없다"
(exit 0)
```

- **처음에는 둘 다 꺼져 있다** — 배경이 `rgba(0, 0, 0, 0)` 이고 `:target` 은 `null`.
- **`#가` 를 누르면 가 칸만 켜진다**(`rgb(253, 230, 138)`), **`#나` 를 누르면 가가 꺼지고 나가 켜진다.** 한 번에 하나뿐이다.
- **`#없다` 를 누르면 둘 다 꺼진다.** `location.hash` 는 `"#없다"` 로 남는데 `:target` 은 `null` 이다.
- ★ 색 값은 선언한 `#fde68a` 를 `rgb()` 로 되쓴 것이라 **안 흔들리는 칸**이다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **조각 일곱 가지** — 한글·인코딩·옛 앵커·중복·없는 것 | 2 | 동작 방식 (1) · A1 · A7 · A8 |
| **`#top`·빈 `#`·없는 이름** — 두 판 여섯 줄씩 | 2 | 동작 방식 (2) · A2 · A5 · A6 |
| `id` 값 경계 여덟 가지 | 2 | 동작 방식 (3) · A3 · A9 |
| **demo 블록**과 그 `바꿔 볼 것` | 2 | 동작 방식 (5) |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `scrollY` 의 절댓값 | `702` · `1404` · `2106` · `2108` · `2808` | 칸 높이·테두리·기본 여백에 달렸다 — **0 인가 · 같은가**만 근거로 쓴다 |
| `:target` 의 배경색 되쓰기 꼴 | `rgb(253, 230, 138)` | 직렬화 형식 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). ② **뒤로 가기·앞으로 가기** — 조각 이동이 방문 기록에 쌓이는 것을 안 던졌다. ③ **`scroll-behavior: smooth` 와 스크롤 앵커링** — 최종 위치만 읽었고 가는 도중은 안 봤다. ④ **네트워크 요청 자체** — 「조각이 서버에 안 간다」는 **명세를 읽어 적은 것**이다(A10).

**못 잰 것**(「안 돌려 본 것」과 다르다) — **주소창에 보이는 글자.** headless 에 주소창이 없어 **측정 수단이 없다.** 쪼개서 잰 조각은 `location.hash` 가 답하는 값뿐이고, 「사람 눈에 한글로 보이나」는 **잴 수 없다.**

**부적용인 창** — **창 ①(`--dump-dom` 트리)과 창 ④(`compatMode`).** 조각 식별자는 트리를 한 글자도 바꾸지 않고 문서 모드와도 무관해 **잴 것이 없다**(「재 봤더니 같았다」가 아니다). ★ 그 대신 이 주제는 **`window.scrollY` 를 창 하나로 더 썼다.**

## 용어 풀이

- **조각 식별자(fragment identifier)** — URL 의 `#` 뒤 부분. 서버에 전송되지 않는다.
- **가리키는 부분(indicated part)** — 조각 식별자가 지목한 문서의 자리. 명세의 용어다.
- **`:target`** — 가리키는 부분인 요소에 붙는 CSS 의사 클래스. 많아야 하나다.
- **`id`** — 문서 안에서 유일해야 하는 이름. 비어 있으면 안 되고 ASCII 공백을 포함하면 안 된다.
- **`<a name>`** — 옛 방식의 앵커. **폐기**됐지만 조각 찾기에서는 아직 먹는다.
- **이름 있는 접근(named access on Window)** — `id` 와 **일부 요소의** `name` 이 `window` 의 이름이 되는 규칙. `<a>` 는 그 목록에 없다.
- **퍼센트 인코딩(percent-encoding)** — URL 에서 ASCII 밖 글자를 `%XX` 로 적는 방식.
- **CSS 이스케이프** — 선택자에서 문법에 안 맞는 글자를 `\` 로 적는 것. `#\33 a` 가 `id="3a"` 를 가리킨다.
