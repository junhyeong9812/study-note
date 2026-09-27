# html/syntax/02 — 요소와 속성 문법: 빈 요소·태그 생략·불리언 속성·따옴표 규칙 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「The HTML syntax」·「Tokenization」으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 슬래시는 한 개도 바꾸지 않는다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-void-slash.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>빈 요소와 슬래시</title>
<p>줄1<br>줄2<br/>줄3<br />줄4</p>
<img src="a.gif" alt="그림"/>
<div class="d"/>여기는 div 안인가?</div>
<span/>뒤</span>
===== dom html01b-void-slash.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>빈 요소와 슬래시</title>
</head><body><p>줄1<br>줄2<br>줄3<br>줄4</p>
<img src="a.gif" alt="그림">
<div class="d">여기는 div 안인가?</div>
<span>뒤</span>
</body></html>
(exit 0)
```

**`br` 요소의 개수와 직렬화**

- **세 개**이고 **전부 `<br>`** 로 나온다. `<br>`·`<br/>`·`<br />` 가 **같은 토큰**이 된다.

**`<div class="d"/>` 뒤의 글자**

- **div 안**이다. 실측 트리가 `<div class="d">여기는 div 안인가?</div>` 였다.
- `/` 가 무시돼 div 가 **열린 채** 남고, 뒤에 쓴 `</div>` 가 닫았다.

**`<span/>뒤</span>` 의 `뒤`**

- **span 안**이다. 같은 이유다.

**`/` 가 실제로 바꾼 것**

- **0개.** 이 파일에서 슬래시는 **아무 일도 하지 않았다.**

```text
  self-closing flag 를 붙이는 것까지는 토크나이저가 한다
        |
        v
  트리 구축 단계가 그 표시를 '빈 요소가 아니면' 쓰지 않는다
        |
        v
  명세는 그것을 parse error 로 규정한다 — 그러나 트리는 안 바뀐다
```

### 2. 닫아 주는 것은 「다음에 오는 것」이다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-omit.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>태그 생략</title>
<p>첫 문단
<p>둘째 문단
<ul>
  <li>가
  <li>나
</ul>
<table>
  <tr><td>a<td>b
  <tr><td>c<td>d
</table>
<dl><dt>용어<dd>뜻<dt>용어2<dd>뜻2</dl>
===== dom html01b-omit.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>태그 생략</title>
</head><body><p>첫 문단
</p><p>둘째 문단
</p><ul>
  <li>가
  </li><li>나
</li></ul>
<table>
  <tbody><tr><td>a</td><td>b
  </td></tr><tr><td>c</td><td>d
</td></tr></tbody></table>
<dl><dt>용어</dt><dd>뜻</dd><dt>용어2</dt><dd>뜻2</dd></dl>
</body></html>
(exit 0)
```

**각각 무엇이 닫았나**

| 요소 | 닫은 것 |
|---|---|
| 첫 `p` | **다음 `<p>` 시작 태그** |
| 둘째 `p` | **문서의 끝**(`body` 가 닫히면서) |
| 첫 `li` | **다음 `<li>` 시작 태그** |
| 첫 `td` | **다음 `<td>` 시작 태그** |
| `dt` | **다음 `<dd>` 시작 태그** |

**소스에 없는데 트리에 생긴 것**

- **`<tbody>`** 다. `<table>` 바로 다음에 `<tr>` 이 오면 파서가 끼워 넣는다.
- ★ 이것은 **생략이 아니라 삽입**이다 — 성질이 다르다([03번 주제](../03-parser-and-error-recovery/2-summary.md)가 정본).

**유효한가, 고친 것인가**

- **유효하다.** 명세의 「Optional tags」 절이 **조건과 함께 허용**한 것이다.

**둘을 가르는 기준**

- **명세가 허용 목록에 넣어 뒀나**다. 허용된 생략은 **유효한 마크업**이고, 그 밖에 파서가 손댄 것은 **오류 복구**다.
- 이 주제는 앞엣것까지, [03번 주제](../03-parser-and-error-recovery/2-summary.md)가 뒤엣것부터.

### 3. 다섯 버튼 중 넷이 비활성이다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-boolean.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>불리언 속성</title>
<button id="b1" disabled>속성 이름만</button>
<button id="b2" disabled="">빈 문자열</button>
<button id="b3" disabled="false">false 라고 씀</button>
<button id="b4" DISABLED="DISABLED">대문자</button>
<button id="b5">속성이 없다</button>
<script>
const o = [];
for (const id of ["b1","b2","b3","b4","b5"]) {
  const e = document.getElementById(id);
  o.push(id + "  getAttribute('disabled') = " + JSON.stringify(e.getAttribute("disabled"))
            + "   .disabled = " + e.disabled);
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-boolean.html | nojs =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>불리언 속성</title>
</head><body><button id="b1" disabled="">속성 이름만</button>
<button id="b2" disabled="">빈 문자열</button>
<button id="b3" disabled="false">false 라고 씀</button>
<button id="b4" disabled="DISABLED">대문자</button>
<button id="b5">속성이 없다</button>
(exit 0)
```

```text
===== 소스: html01b-boolean.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>불리언 속성</title>
<button id="b1" disabled>속성 이름만</button>
<button id="b2" disabled="">빈 문자열</button>
<button id="b3" disabled="false">false 라고 씀</button>
<button id="b4" DISABLED="DISABLED">대문자</button>
<button id="b5">속성이 없다</button>
<script>
const o = [];
for (const id of ["b1","b2","b3","b4","b5"]) {
  const e = document.getElementById(id);
  o.push(id + "  getAttribute('disabled') = " + JSON.stringify(e.getAttribute("disabled"))
            + "   .disabled = " + e.disabled);
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-boolean.html | probe =====
b1  getAttribute('disabled') = ""   .disabled = true
b2  getAttribute('disabled') = ""   .disabled = true
b3  getAttribute('disabled') = "false"   .disabled = true
b4  getAttribute('disabled') = "DISABLED"   .disabled = true
b5  getAttribute('disabled') = null   .disabled = false
(exit 0)
```

**`.disabled` 예측**

| | `getAttribute("disabled")` | `.disabled` |
|---|---|---|
| `disabled` | `""` | **`true`** |
| `disabled=""` | `""` | **`true`** |
| `disabled="false"` | `"false"` | **`true`** ★ |
| `DISABLED="DISABLED"` | `"DISABLED"` | **`true`** |
| (없음) | `null` | `false` |

**직렬화**

- 첫 버튼이 **`disabled=""`** 로 나온다. 값 없는 속성은 **빈 문자열**로 되쓰인다.
- `DISABLED="DISABLED"` 는 **`disabled="DISABLED"`** — 이름만 소문자화되고 **값은 그대로**다.

**비활성을 끄는 방법**

- **속성을 아예 안 붙이는 것 하나뿐**이다.
- 템플릿이라면 `disabled="{{x}}"` 가 아니라 **속성 전체를 조건부로** 넣는다.

### 4. 이름은 소문자가 되고 값은 그대로, 중복은 첫 것만

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-case-dup.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>대소문자와 중복 속성</title>
<P ID="c1" CLASS="Box Big" DATA-Key="Val">대문자로 쓴 태그</P>
<p id="c2" title="첫" title="둘" TITLE="셋">중복 속성</p>
<script>
const o = [];
const c1 = document.getElementById("c1");
o.push("c1 tagName   = " + c1.tagName + "      localName = " + c1.localName);
o.push("c1 속성 이름 = " + [...c1.attributes].map(a => a.name).join(", "));
o.push("c1 class 값  = " + JSON.stringify(c1.getAttribute("class")));
o.push("c1 dataset.key = " + JSON.stringify(c1.dataset.key));
const c2 = document.getElementById("c2");
o.push("c2 속성 개수 = " + c2.attributes.length
       + "   title = " + JSON.stringify(c2.getAttribute("title")));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-case-dup.html | nojs =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>대소문자와 중복 속성</title>
</head><body><p id="c1" class="Box Big" data-key="Val">대문자로 쓴 태그</p>
<p id="c2" title="첫">중복 속성</p>
(exit 0)
```

```text
===== 소스: html01b-case-dup.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>대소문자와 중복 속성</title>
<P ID="c1" CLASS="Box Big" DATA-Key="Val">대문자로 쓴 태그</P>
<p id="c2" title="첫" title="둘" TITLE="셋">중복 속성</p>
<script>
const o = [];
const c1 = document.getElementById("c1");
o.push("c1 tagName   = " + c1.tagName + "      localName = " + c1.localName);
o.push("c1 속성 이름 = " + [...c1.attributes].map(a => a.name).join(", "));
o.push("c1 class 값  = " + JSON.stringify(c1.getAttribute("class")));
o.push("c1 dataset.key = " + JSON.stringify(c1.dataset.key));
const c2 = document.getElementById("c2");
o.push("c2 속성 개수 = " + c2.attributes.length
       + "   title = " + JSON.stringify(c2.getAttribute("title")));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-case-dup.html | probe =====
c1 tagName   = P      localName = p
c1 속성 이름 = id, class, data-key
c1 class 값  = "Box Big"
c1 dataset.key = "Val"
c2 속성 개수 = 2   title = "첫"
(exit 0)
```

**대소문자가 바뀌는 것**

| | 바뀌나 |
|---|---|
| `tagName` | **대문자로 답한다**(`P`) — HTML 네임스페이스의 규정 |
| `localName` | **소문자**(`p`) |
| 속성 이름 | **소문자화**(`CLASS` → `class`, `DATA-Key` → `data-key`) |
| 속성 값 | **안 바뀐다**(`"Box Big"` 그대로) |

**`dataset` 으로는**

- **`dataset.key`** 다. `DATA-Key` 가 `data-key` 로 소문자화된 뒤 `dataset` 규칙이 적용되므로 `dataset.Key` 가 아니다.

**`c2` 의 속성 개수와 `title`**

- **2개**(`id`·`title`)이고 `title` 은 **`"첫"`** 이다.
- `title="둘"` 과 `TITLE="셋"` 은 **덮어쓰지 않고 버려졌다.** `TITLE` 도 소문자화 뒤 중복 판정을 받는다.

**`--dump-dom` 만으로 알 수 있는가**

- **아니다.** 직렬화된 트리는 `<p id="c2" title="첫">` 이라 **버려진 흔적이 없다.**
- **창 ②**(`attributes.length`)가 있어야 「둘을 버렸다」가 보인다.

```text
   창 ①  --dump-dom        <p id="c2" title="첫">      "원래 하나만 썼나 보다"
   창 ②  attributes.length  = 2                        "셋 중 둘을 버렸다"
                                                        ^ 이쪽만 사고를 잡는다
```

### 5. 따옴표를 빼면 없던 속성이 생긴다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-unquoted.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>따옴표 없는 속성값</title>
<a id="u1" href=/search?q=a&b title=hello>1</a>
<a id="u2" href=/a/b title=hello world>2</a>
<a id="u3" href=/a/b class=x/y>3</a>
<script>
const o = [];
for (const id of ["u1","u2","u3"]) {
  const e = document.getElementById(id);
  o.push(id + " 속성 = " + [...e.attributes].map(a => a.name + "=" + JSON.stringify(a.value)).join("  "));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-unquoted.html | nojs =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>따옴표 없는 속성값</title>
</head><body><a id="u1" href="/search?q=a&amp;b" title="hello">1</a>
<a id="u2" href="/a/b" title="hello" world="">2</a>
<a id="u3" href="/a/b" class="x/y">3</a>
(exit 0)
```

```text
===== 소스: html01b-unquoted.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>따옴표 없는 속성값</title>
<a id="u1" href=/search?q=a&b title=hello>1</a>
<a id="u2" href=/a/b title=hello world>2</a>
<a id="u3" href=/a/b class=x/y>3</a>
<script>
const o = [];
for (const id of ["u1","u2","u3"]) {
  const e = document.getElementById(id);
  o.push(id + " 속성 = " + [...e.attributes].map(a => a.name + "=" + JSON.stringify(a.value)).join("  "));
}
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-unquoted.html | probe =====
u1 속성 = id="u1"  href="/search?q=a&b"  title="hello"
u2 속성 = id="u2"  href="/a/b"  title="hello"  world=""
u3 속성 = id="u3"  href="/a/b"  class="x/y"
(exit 0)
```

**세 링크의 속성 목록**

| | 속성 |
|---|---|
| `u1` | `id="u1"` · `href="/search?q=a&b"` · `title="hello"` |
| `u2` | `id="u2"` · `href="/a/b"` · `title="hello"` · **`world=""`** |
| `u3` | `id="u3"` · `href="/a/b"` · `class="x/y"` |

**없던 속성이 생기는가**

- **생긴다.** `title=hello world` 의 `world` 가 **값이 아니라 새 속성**이 되고, 그 값은 **빈 문자열**이다.
- 값이 빈 문자열이므로 **불리언 속성 규칙상** 「**있다**」로 읽힌다 — 우연히 `disabled` 같은 이름이 오면 기능이 켜진다.

**`class=x/y` 의 `/`**

- **값의 일부**다(`class="x/y"`). `/` 가 특별해지는 것은 **`>` 바로 앞**에서뿐이고, 그마저 A1 처럼 무시된다.

**따옴표 없는 값에 넣으면 안 되는 글자**

- **`"` · `'` · `` ` `` · `=` · `<` · `>`** 와 **공백**. 앞의 여섯은 명세가 **파스 오류**로 규정하고, 공백은 값을 끝낸다.

### 6. 「빈 요소」와 「생략 가능 태그」

**정의 차이**

- **빈 요소는 끝 태그가 「없는」 요소**이고, **생략 가능 태그는 끝 태그가 「있는데 안 써도 되는」 것**이다.

**`br` 과 `li`**

- `br` = **빈 요소**. `li` = **끝 태그 생략 가능한 보통 요소**.

**빈 요소 목록**

- **명세가 고정 목록으로 정한다** — `area`·`base`·`br`·`col`·`embed`·`hr`·`img`·`input`·`link`·`meta`·`source`·`track`·`wbr`.
- **내가 늘릴 수 없다.** 커스텀 요소에 `/>` 를 써도 빈 요소가 되지 않는다.

**빈 상자를 만드는 것**

- **`<div></div>`** 다. `<div />` 는 **열린 상자**다(A1).

### 7. 값이 아니라 존재를 본다

**명세의 어느 규정인가**

- 「**Boolean attributes**」 절이다 — 「속성이 있으면 참, 없으면 거짓이고 **값은 무시된다**」고 못 박는다. 허용되는 값도 **빈 문자열과 속성 이름 자체**뿐이다.

**콘텐츠 속성과 IDL 속성**

- **콘텐츠 속성**(`getAttribute("disabled")`) — **글자열**. `""`·`"false"`·`"DISABLED"`·`null`.
- **IDL 속성**(`el.disabled`) — **불리언**. 위 넷 중 `null` 만 `false`.
- 둘을 같은 것으로 읽는 것이 이 주제의 첫 번째 사고다.

**템플릿에서 안전한 형태**

- 속성 **전체**를 조건부로 넣는다(`{{#if x}}disabled{{/if}}`).
- JS 라면 `el.disabled = x` 또는 `el.toggleAttribute("disabled", x)`.

**`aria-*` 는 같은가**

- **아니다.** `aria-*` 는 **값을 보는** 속성이다 — `aria-disabled="false"` 는 **거짓**이다.
- ★ 「불리언 속성처럼 생겼는데 값을 보는 것」이 바로 옆에 있다. 접근성 쪽 정본은 목록의 **42번·46번 주제**다.

### 8. 버려진 속성은 흔적이 없다

**`--dump-dom` 에 안 남는 이유**

- 버려진 속성은 **트리에 들어가지도 않았기 때문**이다. 직렬화는 트리를 되쓰는 것이므로 **없는 것은 못 쓴다.**

**어느 창을 쓰나**

- **창 ②** — `el.attributes.length` 를 센다. 실측에서 셋을 쓴 요소의 속성이 **2개**였다.

**보안 표면이 되는 경우**

- 서버 쪽 정제기(sanitizer)와 브라우저가 **다른 쪽 속성을 채택**하면 필터를 우회할 수 있다.
- 예: 정제기가 뒤엣것을 보고 `href="#"` 를 통과시켰는데 브라우저는 앞엣것 `href="javascript:…"` 를 쓰는 식.
- ★ **이 판에서 확인한 것은 「Chrome 이 첫 것을 쓴다」 하나**다. 정제기 쪽은 돌려 보지 않았다.

**01번 주제의 같은 규칙**

- **두 번째 `<html>` 시작 태그.** 새 요소를 안 만들고 속성만 합치되 **이미 있는 속성은 안 덮는다.**

### 9. 「파스 오류」는 「파싱 실패」가 아니다

**파싱이 안 멈추는 이유**

- HTML 파서는 **반드시 트리를 내놓도록 명세가 규정**한다. 「parse error」는 **「이 입력은 유효하지 않다」는 이름표**이지 중단 신호가 아니다.
- 명세는 오류마다 **무슨 트리를 만들지까지** 적어 둔다 — 그래서 **틀린 마크업도 결과가 하나로 정해진다.**

**셋의 관계**

```text
   무효한 마크업        명세를 어긴 것.            validator 가 잡는다 (이 환경엔 없다)
        |
        +-- 파스 오류    명세가 이름 붙인 무효.     파서는 '그래도' 트리를 만든다
        |
        +-- 파싱 실패    HTML 에는 없다.           XML 파서에만 있다 (03번 주제)
```

**`(exit N)` 이 전부 같은 이유**

- **전부 `0`** 이다. 파서가 실패하지 않으므로 Chrome 도 실패하지 않는다.
- 그래서 이 갈래에서 **종료 코드는 근거가 못 된다** — 「안 흔들리는 칸」이지만 **정보가 없는 칸**이다.

**무효를 잡아 주는 것**

- **마크업 검증기**다. ★ **이 환경에는 없다**([01번 주제](../01-document-skeleton/3-answer.md) A8) — 그래서 이 갈래는 「파서가 무엇을 고쳤나」로 대신한다.

### 10. 소스와 트리가 달라진 다섯 자리

**다섯**

1. `<br/>` → `<br>` (슬래시가 사라짐)
2. `<div />` → **열린 div** (슬래시가 무시되고 뒤 내용을 품음)
3. `<P CLASS=…>` → `<p class=…>` (이름이 소문자화)
4. `disabled` → `disabled=""` (빈 값으로 되쓰기)
5. `title="첫" title="둘"` → `title="첫"` (**중복이 버려짐**)

**보이는 것 / 안 보이는 것**

| 창 ① 로 보인다 | 창 ② 가 있어야 보인다 |
|---|---|
| 1 · 2 · 3 · 4 | **5**(속성 개수) |

- ★ **하나 더** — `title=hello world` 가 만든 `world=""` 는 **창 ① 로도 보인다**(새 속성이 트리에 있으므로).

**「소스가 맞다」와 「렌더된 것이 맞다」**

- 이 주제의 예로는 **`<div />`** 가 가장 선명하다. **소스는 내 의도대로 적혀 있고**(빈 div 를 쓰려 했다), **트리와 화면은 전혀 다르다**(뒤 문단을 품었다).
- 그래서 **소스를 아무리 읽어도 안 잡힌다** — 창 ① 이나 화면으로 봐야 한다. demo 블록이 그 자리다.

**03번 주제와의 경계**

- 여기는 「**명세가 허용하는 표기**」까지 — 빈 요소·생략 가능 태그·속성 문법.
- 거기는 「**명세를 어겼을 때 파서가 만드는 트리**」부터 — 암묵 삽입·서식 태그 재생성·foster parenting.
- 실무에서는 **같은 파일 안에 섞여** 있으므로 「이것은 허용된 생략인가, 파서가 고친 것인가」를 늘 갈라 물어야 한다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **마크업 검증기는 없다.**

**하네스** — 01\~04 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe`·`nojs` 가 이 셋이다.

```bash
# html01b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
```

**demo 블록 검증** — 문서의 `demo` 블록에 래퍼(`<!doctype>`·`<body>`)와 측정 프로브를 붙인 사본을 따로 띄워 `보이는 것` 을 확인했다.

```text
===== 소스: html01b-demo02a.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 02a 검증</title>
<body>
<div class="a"/>빈 div 를 만들려 했다
<p>이 문단은 어디에 있나?</p>
<style>
  .a { border: 2px solid #b91c1c; padding: 6px; }
  p  { border: 2px dashed #2563eb; padding: 6px; }
</style>
<script>
const o = [];
const a = document.querySelector(".a");
o.push(".a 자식 요소     = " + [...a.children].map(e => e.localName).join(", "));
o.push("p 가 .a 안인가   = " + (document.querySelector("p").closest(".a") !== null));
o.push("body 직계 자식   = " + [...document.body.children].map(e => e.localName).join(", "));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-demo02a.html | probe =====
.a 자식 요소     = p, style, script
p 가 .a 안인가   = true
body 직계 자식   = div
(exit 0)
```

- `.a` 의 자식 요소가 **`p, style, script`** — 뒤따르는 문단이 실제로 div 안이다.
- `body` 의 직계 자식이 **`div` 하나뿐**이다.
- ★ **`바꿔 볼 것` 에 적은 단언도 검증 대상**이다. 두 변형을 따로 던졌다.

```text
===== 소스: html01b-demo02b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 02a 의 '바꿔 볼 것' 검증</title>
<body>
<div class="v1"></div>닫아 준 판
<p class="p1">문단 1</p>
<div class="v2">슬래시를 지운 판
<p class="p2">문단 2</p>
<style>
  div { border: 2px solid #b91c1c; padding: 6px; }
  p   { border: 2px dashed #2563eb; padding: 6px; }
</style>
<script>
const o = [];
o.push(".v1 자식 요소  = [" + [...document.querySelector(".v1").children].map(e => e.localName).join(", ") + "]");
o.push("p1 이 .v1 안인가 = " + (document.querySelector(".p1").closest(".v1") !== null));
o.push(".v2 자식 요소  = [" + [...document.querySelector(".v2").children].map(e => e.localName).join(", ") + "]");
o.push("p2 가 .v2 안인가 = " + (document.querySelector(".p2").closest(".v2") !== null));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-demo02b.html | probe =====
.v1 자식 요소  = []
p1 이 .v1 안인가 = false
.v2 자식 요소  = [p, style, script]
p2 가 .v2 안인가 = true
(exit 0)
```

- `<div class="a"></div>` 로 닫은 판(`.v1`)은 **자식 요소가 `[]`** 이고 뒤 문단이 밖에 있다 — 두 상자가 나란히 선다.
- `/` 만 지운 판(`.v2`)은 **`<div />` 판과 결과가 같다**(`[p, style, script]`) — 슬래시가 아무 일도 안 한다는 증거다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 빈 요소·비빈 요소의 `/` 다섯 경우 | 2 | 동작 방식 (1) · A1 |
| 태그 생략 다섯 경우(`p`·`li`·`td`·`dt`·`dd`) + `tbody` 삽입 | 2 | 동작 방식 (2) · A2 |
| 불리언 속성 다섯 경우의 콘텐츠·IDL 값 | 2 | 동작 방식 (3) · A3 |
| 대소문자 정규화(`tagName`·`localName`·이름·값·`dataset`) | 2 | 동작 방식 (4) · A4 |
| **중복 속성 셋의 `attributes.length`** | 2 | 동작 방식 (5) · A4 · A8 |
| 따옴표 없는 값 세 경우 | 2 | 동작 방식 (6) · A5 |
| **demo 블록**(`<div />` 가 문단을 삼키는 것) | 2 | 동작 방식 (1) |
| demo 의 `바꿔 볼 것` 두 단언 | 1 | 동작 방식 (1) |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `disabled` 의 직렬화 형태 | `disabled=""` | 직렬화 알고리즘 + 구현 |
| `--dump-dom` 의 줄바꿈 자리 | 소스의 텍스트 노드를 그대로 | 직렬화 + 도구 |
| 중복 속성에서 **첫 것을 쓰는 것** | `title="첫"` | 명세대로지만 **정제기 쪽은 안 돌려 봤다** |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). ② **SVG·MathML 안에서 `/>` 가 실제로 닫는 것** — 외래 콘텐츠는 이 배치 밖이라 던지지 않았다. 목록의 **39번 주제**에서 확인할 자리다. ③ **서버 쪽 정제기와의 중복 속성 불일치** — 정제기가 없어 재현하지 못했다. A8 에 그렇게 표기했다. ④ **커스텀 요소에 `/>` 를 붙였을 때** — 던지지 않았다.

## 용어 풀이

- **빈 요소(void element)** — 끝 태그가 없는 요소. 명세가 **고정 목록**으로 정한다. 내가 늘릴 수 없다.
- **self-closing flag** — `/>`로 끝난 시작 태그에 토크나이저가 남기는 표시. **트리 구축은 빈 요소 말고는 쓰지 않는다.**
- **생략 가능 태그(optional tag)** — 명세가 조건과 함께 생략을 허용한 태그. **유효한 마크업**이다.
- **불리언 속성(boolean attribute)** — 존재 여부로 참·거짓을 나타내는 속성. **값을 보지 않는다.**
- **콘텐츠 속성(content attribute)** — 마크업에 적힌 속성. `getAttribute` 가 **글자열**로 돌려준다.
- **IDL 속성(IDL attribute)** — DOM 객체의 프로퍼티(`el.disabled`). **타입이 있다.**
- **토크나이저(tokenizer)** — 글자열을 토큰으로 자르는 파서의 앞단. 소문자화·중복 버리기가 여기서 일어난다.
- **파스 오류(parse error)** — 명세가 무효라고 이름 붙인 입력. **트리를 바꾸지도, 파싱을 멈추지도 않는다.**
- **직렬화(serialization)** — 트리를 다시 글자열로 되쓰는 것. `--dump-dom` 이 보여 주는 것.
- **정제기(sanitizer)** — 신뢰할 수 없는 HTML 에서 위험한 것을 걸러 내는 서버·클라이언트 쪽 도구.
