# html/syntax/02 — 요소와 속성 문법: 빈 요소·태그 생략·불리언 속성·따옴표 규칙 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The HTML syntax」](https://html.spec.whatwg.org/multipage/syntax.html) 절 — 「Elements」·「Attributes」·「Optional tags」, 그리고 [「Tokenization」](https://html.spec.whatwg.org/multipage/parsing.html#tokenization). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 과 DOM 프로브로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 산출이 **조용히 실패**하고 WebKit 은 없다. 이 갈래는 **「이식성」을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 이 주제의 규칙은 **전부 HTML Living Standard 의 파싱 알고리즘**에 있고 20년 넘게 안정돼 있다.
> **선행** — [01번 주제](../01-document-skeleton/2-summary.md)(문서의 뼈대). 거기서 세운 **창 넷**을 그대로 쓴다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · 실행 시각 · 프로세스 id | 판이 오르면 바뀐다 |
| **흔들린다** | 스크린샷 픽셀의 안티에일리어싱 | GPU·글꼴 래스터라이저에 달렸다 |
| **안 흔들린다** | **`--dump-dom` 트리 전체** | 파싱 알고리즘이 명세에 있다 |
| **안 흔들린다** | **속성 이름·값·개수** · 불리언 속성의 IDL 값 | 〃 |
| **안 흔들린다** | `tagName`·`localName` 의 대소문자 | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

## 한눈에 — 쉽게 말하면

**★ HTML 의 태그와 속성은 「내가 쓴 글자」가 아니라 「토크나이저가 뽑아낸 것」이다. 그 사이에서 많은 것이 조용히 바뀐다.**

세관 신고서에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 내가 적은 신고서 | **HTML 소스의 태그** |
| 세관이 옮겨 적은 전산 기록 | **DOM 의 요소와 속성** |
| 칸 이름을 전부 소문자로 통일해 입력함 | **태그·속성 이름의 소문자화** |
| 「해당 없음」 칸에 무엇을 적든 **적혀 있으면 해당** | **불리언 속성** |
| 같은 칸을 두 번 적으면 **먼저 적은 것만** 입력 | **중복 속성은 첫 것이 이긴다** |
| 칸을 비워 두면 표준 서식대로 채워 넣음 | **태그 생략 → 파서가 요소를 연다** |

- **`<br />` 의 슬래시는 아무 일도 안 한다.** 빈 요소는 슬래시가 있든 없든 같고, **빈 요소가 아닌 것**에 붙이면 **그냥 무시**된다.
- **`disabled="false"` 는 참**이다. 불리언 속성은 **있느냐 없느냐**만 본다.
- **중복 속성은 첫 것이 이긴다.** 뒤엣것은 **트리에 담기지도 않는다.**

```text
  내가 쓴 것                                 트리에 담긴 것
  +--------------------------------+        +----------------------------+
  | <br />                         |        | <br>                       |
  | <div class="d"/>텍스트</div>   |  ==>   | <div class="d">텍스트</div> |
  | <P ID="a" CLASS="B">           |        | <p id="a" class="B">       |
  | <p title="첫" title="둘">       |        | <p title="첫">             |
  | <button disabled="false">      |        | .disabled === true         |
  +--------------------------------+        +----------------------------+
```

실무에서 이게 터지는 자리는 **템플릿이 속성을 만들어 낼 때**다.\
`<input {{disabled ? 'disabled' : 'disabled="false"'}}>` 같은 코드가 **양쪽 다 비활성**을 만든다.\
그리고 **속성을 조건부로 붙이는 코드가 두 번 붙였을 때** 뒤엣것이 조용히 버려진다.

> **빈 요소(void element)** — 자식을 가질 수 없어 **끝 태그가 없는** 요소.\
> 예: `br`·`img`·`input`·`meta`·`link`·`hr`·`source`. 목록이 명세에 고정돼 있다.

> **불리언 속성(boolean attribute)** — 값이 아니라 **존재 여부**로 참·거짓을 나타내는 속성.\
> 예: `disabled`·`checked`·`required`·`readonly`·`multiple`·`async`·`defer`.

> **토크나이저(tokenizer)** — 글자열을 태그·속성·텍스트 같은 **토큰**으로 자르는 파서의 앞단.\
> 예: `<a href=/a b=1>` 을 「시작 태그 `a`, 속성 `href=/a`, 속성 `b=1`」로 자른다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **끝 태그를 안 써도 되는 것은 무엇이고, 그 규칙은 어디서 오나.** 빈 요소와 「생략 가능 태그」는 같은 것인가.
2. **`/` 는 무엇을 하나.** `<br />`·`<div />`·`href=x/y` 의 슬래시가 각각 어떻게 되나.
3. **속성 값은 어디까지가 값인가.** 따옴표를 안 쓰면 경계를 무엇이 정하나.
4. **같은 속성을 두 번 쓰면 무엇이 남나.** 그리고 「값이 `false` 인 불리언 속성」은 왜 참인가.

★ 관찰 수단은 [01번 주제](../01-document-skeleton/2-summary.md)에서 세운 **창 ①**(`--dump-dom`)과 **창 ②**(`attributes`·`childNodes` 프로브)다. 이 주제는 **그 둘을 나란히 놓는 것**이 본체다 — 직렬화가 정규화해 버려서 `--dump-dom` 만으로는 못 보는 것이 있다(중복 속성이 **몇 개** 담겼나).

## 동작 방식

### (1) 빈 요소와 슬래시 — 슬래시는 아무 일도 안 한다

**언제 쓰나** — XML 습관으로 `/>` 를 쓸 때마다. **가장 널리 잘못 알려진 자리다.**

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

```text
  소스                              트리                      무슨 일이 일어났나
  <br>          ------------->      <br>                     그대로
  <br/>         ------------->      <br>                     '/' 가 무시됐다
  <br />        ------------->      <br>                     '/' 가 무시됐다
  <img … />     ------------->      <img …>                  '/' 가 무시됐다
  <div class="d"/>텍스트</div>  ->  <div class="d">텍스트</div>
                                       ^ div 는 안 닫혔다. </div> 가 닫은 것이다
  <span/>뒤</span>            ->    <span>뒤</span>
                                       ^ 같다
```

그림 해설 (한 단계씩):

- **빈 요소에 붙인 `/` 는 토크나이저가 그냥 버린다.** `<br>`·`<br/>`·`<br />` 는 **완전히 같은 토큰**이 된다.
- **빈 요소가 아닌 것에 붙여도 마찬가지**다. `<div />` 는 **`<div>` 하나를 연 것**이고, 뒤따르는 글자가 **그 안으로 들어간다.**
- 실측에서 `<div class="d"/>여기는 div 안인가?</div>` 가 **`<div class="d">여기는 div 안인가?</div>`** 가 됐다. 답은 「**예, div 안이다**」.
- ★ 그래서 **`<div />` 를 「빈 div」로 쓰면 그 뒤의 문서 절반이 div 안으로 들어간다.** XML 습관이 만드는 가장 비싼 사고다.

화면으로 보면 이렇다. 빨간 상자가 **닫히지 않아** 뒤따르는 파란 문단을 통째로 품는다.

```html demo
<div class="a"/>빈 div 를 만들려 했다
<p>이 문단은 어디에 있나?</p>
<style>
  .a { border: 2px solid #b91c1c; padding: 6px; }
  p  { border: 2px dashed #2563eb; padding: 6px; }
</style>
```

> **보이는 것** — 빨간 실선 상자 **안에** 파란 점선 상자가 들어가 있다. `<div … />` 로 닫았다고 생각한 상자가 안 닫혀서, 뒤에 쓴 문단이 그 안으로 들어간 것이다.\
> **바꿔 볼 것** — `<div class="a"/>` → `<div class="a"></div>`(두 상자가 나란히 선다) · `/` 를 지워 `<div class="a">`(결과가 같다 — 슬래시가 아무 일도 안 한다는 증거다)

*(Chrome 151 headless 실측 — 래퍼를 붙인 사본에서 `.a` 의 자식 요소가 `p, style, script`, `p.closest(".a") !== null` 이 `true`, `body` 의 직계 자식이 `div` 하나뿐이었다. 검증 블록은 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.)*

비용 — 없음(파서는 안 멈춘다). **그래서 비싸다.**

> **왜 무시되나** — HTML 토크나이저에는 「self-closing flag」가 있어 `/>`로 끝난 시작 태그에 표시를 남긴다.\
> 그런데 **트리 구축 단계가 그 표시를 빈 요소 말고는 쓰지 않는다** — 명세가 「acknowledge self-closing flag」를 안 하면 **파스 오류**로 규정하지만, **파스 오류는 트리를 바꾸지 않는다**([03번 주제](../03-parser-and-error-recovery/2-summary.md)).

### (2) 태그 생략 — 어디까지 허용되나

**언제 쓰나** — 목록·표·문단을 손으로 쓸 때.

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

```text
  소스                       트리                          누가 닫았나
  <p>첫 문단                 <p>첫 문단\n</p>              다음 <p> 가 닫았다
  <p>둘째 문단               <p>둘째 문단\n</p>            </body> 가 닫았다
  <li>가                     <li>가\n  </li>               다음 <li> 가 닫았다
  <td>a<td>b                 <td>a</td><td>b…</td>         다음 <td> 가 닫았다
  <dt>용어<dd>뜻             <dt>용어</dt><dd>뜻</dd>      다음 <dd> 가 닫았다
```

그림 해설 (한 단계씩):

- **끝 태그 생략은 명세의 「Optional tags」 절이 요소마다 조건과 함께 규정**한다 — 아무 데서나 되는 게 아니다.
- `</p>` 는 **다음에 오는 것이 문단을 못 품는 요소일 때** 생략할 수 있다. 실측에서 `<p>첫 문단` 다음의 `<p>` 가 앞 문단을 닫았다.
- `</li>`·`</td>`·`</dt>`·`</dd>` 도 같은 꼴 — **같은 계열의 다음 요소나 부모의 끝**이 닫아 준다.
- ★ **이것은** 「**파서가 고쳐 준 것**」이 아니라 「**명세가 허용한 것**」이다. [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 오류 복구와 **성질이 다르다** — 이쪽은 유효한 마크업이다.
- ★ **`<tbody>` 는 시작 태그까지 생략됐다.** 실측 트리에 `<tbody>` 가 있는데 소스에는 없다 — **삽입**이다. 그쪽은 03번 주제.

비용 — 없음. 다만 **어느 것이 생략 가능한지 외워야** 하므로 팀 규칙으로는 「다 쓴다」가 낫다.

### (3) 창 ② — 불리언 속성은 있느냐 없느냐만 본다

**언제 쓰나** — `disabled`·`checked`·`required` 를 템플릿으로 만들 때. **가장 자주 터지는 자리다.**

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

```text
  소스                          getAttribute()        .disabled
  disabled                      ""                    true
  disabled=""                   ""                    true
  disabled="false"              "false"               true      <- ★
  DISABLED="DISABLED"           "DISABLED"            true
  (없음)                        null                  false
```

그림 해설 (한 단계씩):

- **값은 아무 상관이 없다.** `"false"` 든 `"DISABLED"` 든 **속성이 붙어 있으면 참**이다.
- **거짓으로 만드는 유일한 방법은 속성을 아예 빼는 것**이다.
- `getAttribute` 가 돌려주는 값과 **IDL 속성**(`.disabled`)이 돌려주는 값은 **다른 것**이다 — 앞은 **글자열**, 뒤는 **불리언**.
- ★ **직렬화는 `disabled=""` 로 정규화**한다. 실측 트리에서 `disabled` 만 쓴 것이 `disabled=""` 로 나왔다 — **내가 쓴 형태와 트리의 형태가 다르다.**

비용 — 없음. 그러나 **템플릿 엔진이 `false` 를 글자로 찍는 순간 반대 뜻**이 된다.

### (4) 대소문자 — 무엇이 소문자가 되고 무엇이 안 되나

**언제 쓰나** — 옛 코드베이스를 읽을 때, `data-*` 를 읽을 때.

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

```text
  소스                       트리·DOM
  <P …>                      localName = "p"      tagName = "P"
                                ^ 소문자로 담기고     ^ HTML 문서에서는 대문자로 답한다
  CLASS="Box Big"            속성 이름 "class"    값 "Box Big"
                                ^ 소문자화            ^ 값은 안 건드린다
  DATA-Key="Val"             속성 이름 "data-key" dataset.key = "Val"
                                ^ 소문자화            ^ 그래서 dataset.Key 가 아니다
```

그림 해설 (한 단계씩):

- **태그 이름과 속성 이름은 소문자로 정규화**된다. **속성 값은 그대로**다.
- **`tagName` 은 대문자로 답한다.** HTML 네임스페이스의 요소는 `tagName` 이 대문자, `localName` 이 소문자다 — 둘이 다른 것이 **정상**이다.
- ★ **`data-*` 의 대소문자는 여기서 한 번 더 꼬인다.** `DATA-Key` 가 `data-key` 로 소문자화되므로 **`dataset.key`** 로 읽힌다. 소스에 대문자로 쓴 `Key` 는 흔적도 없다(전역 속성의 정본은 [**목록의 06번 주제**](../06-global-attributes/)).
- **선택자는 다르다** — CSS 의 속성 **값** 매칭은 기본이 대소문자 구분이다(`[class="box"]` 는 `"Box Big"` 을 못 잡는다). 그쪽은 CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **08번**이 정본이다.

비용 — 없음.

### (5) 창 ② — 중복 속성은 첫 것이 이기고, 뒤엣것은 담기지도 않는다

**언제 쓰나** — 속성을 조건부로 덧붙이는 템플릿에서.

앞 (4)의 프로브가 같이 찍은 것이 근거다.

```text
  소스                                      트리
  <p id="c2" title="첫" title="둘" TITLE="셋">
                        ^^^^^^^^^  ^^^^^^^^^^^
                        둘 다 버려진다

  -> 속성 개수 = 2        (id 와 title 뿐이다)
  -> title      = "첫"
  -> 직렬화하면 <p id="c2" title="첫">   ★ 버려진 흔적이 아예 없다
```

그림 해설 (한 단계씩):

- **첫 것이 이긴다.** 뒤엣것은 **덮어쓰지 않고 버려진다.**
- **`TITLE="셋"` 도 같은 속성**이다 — 이름이 소문자화된 뒤에 중복 판정을 하기 때문이다.
- ★ **창 ① 로는 못 본다.** 직렬화된 트리에는 **버려진 속성의 흔적이 없어** 「원래 하나만 썼나 보다」로 읽힌다. **`attributes.length` 를 세야**(창 ②) 「둘을 버렸다」가 보인다.
- 같은 규칙이 **[01번 주제](../01-document-skeleton/2-summary.md)의 두 번째 `<html>`** 에도 적용된다 — 속성이 합쳐지되 **이미 있는 것은 안 덮는다.**

비용 — 없음. **그래서 조용하다.**

### (6) 따옴표 없는 속성값 — 경계를 공백이 정한다

**언제 쓰나** — 손으로 빠르게 쓸 때, 템플릿이 따옴표를 빠뜨렸을 때.

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

```text
  소스                              결과
  href=/search?q=a&b title=hello    href="/search?q=a&b"   title="hello"
                                       ^ & 는 그대로 (04번 주제의 문자 참조 규칙)

  href=/a/b title=hello world       href="/a/b"  title="hello"  world=""
                                                              ^^^^^^^^ ★ 새 속성이 생겼다

  href=/a/b class=x/y               class="x/y"
                                       ^ 값 안의 '/' 는 값의 일부다
```

그림 해설 (한 단계씩):

- **따옴표가 없으면 값은 공백에서 끝난다.** `title=hello world` 의 `world` 는 **값이 아니라 새 불리언 속성**이 된다.
- 그 결과 `world=""` 라는 **내가 쓴 적 없는 속성**이 트리에 생긴다 — 불리언 속성 규칙(3)에 따라 **참으로 읽히는 속성**이다.
- **값 안의 `/` 는 값의 일부**다(`class="x/y"`). `/` 가 특별해지는 것은 **`>` 바로 앞**에서뿐이다 — 그마저 (1)에서 봤듯 무시된다.
- ★ **`&` 도 그대로 남았다.** 속성값의 문자 참조 규칙은 텍스트와 다르다 — 그쪽은 [04번 주제](../04-whitespace-and-character-references/2-summary.md)가 정본이다.

비용 — 없음. **따옴표를 쓰면 이 자리 전체가 사라진다.**

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 속성이 쓸 수 있는 네 꼴

```text
<input disabled>                 빈 속성       값은 "" 이 된다
<input value=abc>                따옴표 없음   공백·> 에서 끝난다
<input value='a b'>              홑따옴표
<input value="a b">              겹따옴표      ★ 기본으로 이것만 쓴다
```

### 금지 사례 — 속성에서 하면 안 되는 것

```text
<div />                          빈 요소가 아니면 '/' 가 무시되고 열린 채 남는다
<input disabled="false">         값과 무관하게 참이다
<a title=hello world>            world 라는 속성이 생긴다
<p id="a" id="b">                뒤엣것이 담기지도 않는다
<a href=a&copy=1>                텍스트와 속성값의 참조 규칙이 다르다 (04번 주제)
<input value=a"b>                따옴표 없는 값에 " ' ` = < > 를 넣으면 파스 오류
```

### 어디서 헷갈리나

- **「빈 요소」와 「끝 태그 생략」은 다른 것**이다. 앞은 **끝 태그가 없는 요소**(명세가 목록으로 고정), 뒤는 **있는데 안 써도 되는 것**.
- **`/>` 는 XML 문법이지 HTML 문법이 아니다.** HTML 에서는 **장식**이다(단, `<svg>`·`<math>` 안의 외래 요소에서는 실제로 닫는다 — 이 판에서 확인하지 않았다).
- **`tagName` 이 대문자인 것은 버그가 아니다.** `localName` 과 갈라 쓴다.
- **불리언 속성의 「값」을 읽지 마라.** `.disabled` 같은 **IDL 속성**으로 읽는다.
- **중복 속성은 `--dump-dom` 으로 안 보인다.** `attributes.length` 로 센다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `<div />` 로 빈 상자를 만들려 한다

실측에서 **`<div class="d"/>` 다음 글자가 div 안으로 들어갔다.** `/` 는 무시되고 div 는 열린 채 남는다.\
증상은 「레이아웃이 통째로 어긋난다」인데 원인은 **슬래시 하나**다. **창 ① 로 보면 즉시 드러난다.**

### 2. `disabled="false"` 로 끄려 한다

**참이다.** 실측에서 `.disabled` 가 `true` 였다.\
끄는 방법은 **속성을 안 붙이는 것** 하나뿐이다. 템플릿이라면 조건부로 **속성 전체**를 넣거나 뺀다.

### 3. 속성을 두 번 붙여 놓고 「뒤엣것이 이기겠지」 한다

**첫 것이 이긴다.** 실측에서 `title="첫" title="둘" TITLE="셋"` 의 **속성 개수가 2**였다.\
★ **`--dump-dom` 에는 흔적이 없다** — 그래서 이 사고는 **창 ② 없이는 진단이 안 된다.**

### 4. 따옴표를 빼고 공백이 든 값을 쓴다

실측에서 `title=hello world` 가 **`title="hello"` + `world=""`** 가 됐다.\
「값이 잘렸다」에서 그치지 않고 **없던 속성이 생긴다** — 그것이 불리언 속성이면 기능이 켜진다.

### 5. `dataset` 을 대문자로 읽으려 한다

실측에서 `DATA-Key="Val"` 이 `data-key` 가 되어 **`dataset.key`** 로 읽혔다.\
소스의 대문자는 **트리에 흔적이 없다.** 「분명히 `Key` 라고 썼는데」는 근거가 못 된다.

### 6. 「토크나이저가 자른 것」과 「내가 쓴 것」을 같게 본다

직렬화가 한 번 더 정규화한다 — `disabled` → `disabled=""`, `<br/>` → `<br>`, `&` → `&amp;`.\
★ **그래서 `--dump-dom` 출력은 「내가 쓴 소스」가 아니다.** 되쓰기 규칙은 [04번 주제](../04-whitespace-and-character-references/2-summary.md)가 정본이다.

## 구현 세부사항 대 언어 보장

★ **HTML 은 「명세가 오류 복구까지 정한」 드문 언어다.** 토크나이저의 상태 기계까지 명세 본문에 있어,\
이 표의 **거의 전부가 명세 보장**이고 **「구현 정의」 칸이 아주 작다.**

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `<br/>` 의 `/` 가 무시되는 것 | **명세**(토크나이저의 self-closing flag 를 트리 구축이 쓰지 않는다) |
| 빈 요소 목록이 고정인 것 | **명세**(「Void elements」) |
| `</p>`·`</li>`·`</td>` 생략이 허용되는 조건 | **명세**(「Optional tags」) |
| 불리언 속성이 값과 무관하게 참인 것 | **명세**(「Boolean attributes」) |
| 태그·속성 이름이 소문자화되는 것 | **명세**(토크나이저) |
| 속성 값의 대소문자가 보존되는 것 | **명세** |
| 중복 속성에서 **첫 것이 이기는 것** | **명세**(토크나이저의 「duplicate-attribute」 파스 오류 + 「drop」) |
| 따옴표 없는 값이 공백에서 끝나는 것 | **명세**(토크나이저) |
| `tagName` 이 대문자인 것 | **명세**(DOM Standard — HTML 네임스페이스 요소의 `tagName` 은 ASCII 대문자화) |
| **`disabled` 가 `disabled=""` 로 직렬화되는 것** | **명세**(HTML 직렬화 알고리즘) + 관찰 |
| **`--dump-dom` 의 출력 형식**(어디서 줄이 바뀌나) | **명세**(직렬화) + **도구**(Chrome 의 플래그) |
| SVG·MathML 안에서 `/>` 가 실제로 닫는 것 | **명세**(외래 콘텐츠). ★ **이 판에서 확인하지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 빈 요소를 쓴다 | `<br>`·`<img …>` | `<br />`(해롭진 않으나 뜻이 없다) |
| 빈 컨테이너가 필요하다 | `<div></div>` | `<div />` |
| 불리언 속성을 조건부로 준다 | 속성 **전체**를 넣거나 뺀다 | `disabled="{{false}}"` |
| 속성값에 공백·특수문자가 있다 | **겹따옴표** | 따옴표 생략 |
| 속성을 여러 곳에서 덧붙인다 | 합쳐서 **한 번만** 쓴다 | 두 번 쓰고 뒤엣것을 기대 |
| 끝 태그를 생략한다 | 「Optional tags」를 확인하고 | 감으로 생략 |
| 「이렇게 담겼겠지」를 확인한다 | 창 ① + **창 ②** | `--dump-dom` 만 |

판단 규칙 두 줄.

- **소스와 트리를 늘 갈라 본다.** 이 주제의 사고는 전부 **그 둘이 다른 자리**에서 난다.
- **직렬화가 감추는 것이 있다**(중복 속성). **센 것**(`attributes.length`)이 **읽은 것**보다 강하다.

## 핵심 문장

- **`<br />` 의 슬래시는 아무 일도 안 한다.** 빈 요소가 아닌 것에 붙이면 **요소가 열린 채 남아** 뒤 내용을 삼킨다.
- **불리언 속성은 값이 아니라 존재로 판단한다.** 실측에서 `disabled="false"` 가 `.disabled === true` 였다.
- **중복 속성은 첫 것이 이기고 뒤엣것은 담기지도 않는다** — 실측 `attributes.length = 2`. **`--dump-dom` 에는 흔적이 없다.**
- **따옴표 없는 값은 공백에서 끝난다** — `title=hello world` 가 **`world=""` 라는 없던 속성**을 만들었다.
- **태그·속성 이름은 소문자화되고 값은 보존된다.** `tagName` 이 대문자인 것은 DOM 의 규정이다.
- **끝 태그 생략은** 「**오류 복구**」가 아니라 「**명세가 허용한 것**」이다 — 03번 주제와 성질이 다르다.
- 이 주제의 규칙은 **거의 전부 명세 보장**이다. HTML 은 토크나이저 상태 기계까지 명세에 있는 드문 언어다.

## 관련 자료

- [`../README.md`](../README.md) — HTML 문법·API 주제 목록(이 주제는 02번)
- [01번 주제](../01-document-skeleton/2-summary.md) — **창 넷의 정본.** 뼈대 태그의 생략은 거기, 여기는 **그 밖의 모든 태그·속성 표기**
- [03번 주제](../03-parser-and-error-recovery/2-summary.md) — **오류 복구의 정본.**\
  여기는 「**명세가 허용하는 표기**」까지, 거기는 「**명세를 어겼을 때 파서가 하는 일**」부터
- [04번 주제](../04-whitespace-and-character-references/2-summary.md) — 속성값 안의 `&` 가 텍스트와 다르게 처리되는 이유
- [목록의 **06번 주제**](../06-global-attributes/)(전역 속성) — `data-*`·`hidden`·`contenteditable` 의 정본. 여기는 **표기 규칙**까지
- 목록의 **30번 주제**(`disabled`/`readonly`) — 불리언 속성이 **무엇을 바꾸는지**의 정본. 여기는 **왜 참이 되는지**까지
- [목록의 **05번 주제**](../05-content-categories-and-models/)(콘텐츠 모델) — 「어느 요소 안에 무엇을 넣을 수 있나」. `<p>` 안의 `<div>` 가 왜 문제인지는 거기와 03번
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **08번** — 속성 선택자가 값의 대소문자를 어떻게 보는지
- [`../../../../compiler-pipeline/`](../../../../compiler-pipeline/) — **토크나이저·파서 일반론의 정본.**\
  「토큰화가 무엇인가」는 거기, 여기는 「**HTML 토크나이저가 내 글자를 어떻게 바꾸나**」만

## 용어 풀이

- **빈 요소(void element)** — 자식을 못 갖고 끝 태그가 없는 요소. `br`·`img`·`input`·`meta`·`link`·`hr` 등. 목록이 명세에 고정돼 있다.
- **self-closing flag** — 토크나이저가 `/>`로 끝난 시작 태그에 남기는 표시. **트리 구축은 빈 요소 말고는 쓰지 않는다.**
- **생략 가능 태그(optional tag)** — 명세가 조건과 함께 생략을 허용한 태그. `</p>`·`</li>`·`<tbody>` 등.
- **불리언 속성(boolean attribute)** — 존재 여부로 참·거짓을 나타내는 속성. 값은 보지 않는다.
- **IDL 속성(IDL attribute)** — `el.disabled` 처럼 **DOM 객체의 프로퍼티**. 글자열인 **콘텐츠 속성**(`getAttribute`)과 다른 것이다.
- **콘텐츠 속성(content attribute)** — 마크업에 쓰인 속성 그 자체. `getAttribute`·`setAttribute` 가 다룬다.
- **토크나이저(tokenizer)** — 글자열을 토큰으로 자르는 파서의 앞단. 대소문자화·중복 속성 버리기가 여기서 일어난다.
- **파스 오류(parse error)** — 명세가 「오류」라고 이름 붙인 입력. ★ **트리를 바꾸지 않고 파싱을 멈추지도 않는다.**
- **직렬화(serialization)** — 트리를 다시 글자열로 되쓰는 것. `--dump-dom` 이 보여 주는 것이 이것이다.

## 더 들어가면

- **`/>` 가 실제로 닫는 자리가 딱 하나 있다** — `<svg>`·`<math>` 안의 **외래 콘텐츠**다. 거기서는 XML 규칙이 적용돼 `<circle />` 가 닫힌다. ★ **이 판에서 확인하지 않았다** — 인라인 SVG 는 목록의 39번 주제다.
- **「파스 오류」라는 이름이 오해를 부른다.** 명세는 `<div />`·중복 속성·따옴표 없는 값 안의 `"` 를 전부 **parse error** 로 규정하지만, 그 뜻은 「**유효하지 않다**」이지 「**파싱이 실패한다**」가 아니다. 실측에서 전부 `(exit 0)` 이었다([03번 주제](../03-parser-and-error-recovery/2-summary.md)).
- **중복 속성이 보안 표면이 된 적이 있다.** 서버 쪽 정제기(sanitizer)와 브라우저가 **다른 쪽 속성을 채택**하면 필터를 우회할 수 있다 — 「첫 것이 이긴다」를 두 구현이 똑같이 지켜야 안전하다. 이 갈래에서 실측으로 확인한 것은 **Chrome 이 첫 것을 쓴다**는 사실 하나다.
- **속성 순서는 트리에 보존된다.** 실측 프로브의 `[...el.attributes]` 가 소스 순서대로 나왔다. 다만 **의미는 없다** — CSS·선택자·접근성 어디도 속성 순서를 보지 않는다.
