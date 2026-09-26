# web-api/01 — 문서와 노드 트리: `Node`·`Element`·`Text`·`Comment` 와 두 컬렉션 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 `--dump-dom` 으로 실제로 받은 것**이다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 로 접지했다.\
> **엔진은 Chrome 하나다** — Firefox 는 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. **이식성을 주장하지 않는다.**\
> **이 주제의 블록에는 흔들리는 칸이 없다** — 재는 수치가 없기 때문이다. 트리 문자열·노드 수·`nodeType`·API 반환값은 다시 돌려도 한 글자도 같아야 한다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 두 컬렉션의 길이 — 7 대 2

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
box.childNodes.length = 7
box.children.length   = 2

childNodes[0]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n  "
childNodes[1]  nodeType=1 ELEMENT_NODE  nodeName=P  nodeValue=null
childNodes[2]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n  "
childNodes[3]  nodeType=8 COMMENT_NODE  nodeName=#comment  nodeValue=" 주석 "
childNodes[4]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n  "
childNodes[5]  nodeType=1 ELEMENT_NODE  nodeName=P  nodeValue=null
childNodes[6]  nodeType=3 TEXT_NODE  nodeName=#text  nodeValue="\n"

children[0]    nodeName=P
children[1]    nodeName=P
(exit 0)
```

**두 수**

- `childNodes.length` = **7**, `children.length` = **2**.

**차이를 만든 것**

- **텍스트 노드 4개**(`nodeType 3`)와 **주석 노드 1개**(`nodeType 8`). 합쳐 5개가 `children` 에서 빠진다.

**`<p>` 둘 사이**

- **노드 하나**다. 줄바꿈과 들여쓰기가 **연속된 문자들**이라 파서가 한 텍스트 노드로 모아 넣는다 — 출력의 `childNodes[4]` 가 `"\n  "` 하나인 것이 근거다.

**한 줄로 붙여 쓰면**

- 공백 텍스트 노드가 아예 안 생겨 `childNodes.length` 는 **3**(요소 둘 + 주석 하나), `children.length` 는 그대로 **2** 가 된다.

```text
   <div id="box">           <div id="box"><p>첫 문단</p><!-- 주석 --><p>둘째 문단</p></div>
     <p>첫 문단</p>
     <!-- 주석 -->          childNodes 7 -> 3      children 2 -> 2
     <p>둘째 문단</p>
   </div>                   ★ 마크업의 '보기 좋음' 이 노드 수를 바꾼다
```

### 2. 첫째 자식을 집으면 — 글자 덩어리를 집는다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
box.firstChild          = #text "\n  "
box.firstElementChild   = <p id=p1>
box.lastChild           = #text "\n"
box.lastElementChild    = <p id=p2>
p1.nextSibling          = #text "\n  "
p1.nextElementSibling   = <p id=p2>
p1.parentNode           = <div id=box>
p1.parentElement        = <div id=box>

document.body.parentNode           = <html>
document.body.parentElement        = <html>
document.documentElement.parentNode    = #document
document.documentElement.parentElement = null

frag 안 span.parentNode    = #document-fragment
frag 안 span.parentElement = null
(exit 0)
```

**세 줄**

- `box.firstChild` = **`#text "\n  "`** — 들여쓰기 공백이다.
- `box.firstElementChild` = **`<p id=p1>`**.
- `box.childNodes[0].nodeValue` = **`"\n  "`**.

**`textContent` 가 빈 문자열처럼 보이는 이유**

- 빈 문자열이 아니라 **공백 문자열**이다. `JSON.stringify` 로 감싸야 `"\n  "` 이 보인다 — 그냥 찍으면 눈에 아무것도 안 보인다.

**나중에 터지는 이유**

- **마크업을 한 줄로 쓰면 이 사고가 안 난다.** 손으로 붙여 쓴 템플릿이 포매터·템플릿 엔진을 거치면서 줄바꿈이 들어가는 순간 처음 깨진다. 코드는 한 글자도 안 바뀌었는데 결과가 바뀐다.

**「자식이 없다」 판정**

- 요소 기준이면 `el.childElementCount === 0` 또는 `el.firstElementChild === null`.
- `firstChild === null` 은 **공백 하나만 있어도 거짓**이 된다.

### 3. 쌍의 두 이름이 답하는 것 — 건너뛰나 마나

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '5,8p'
p1.nextSibling          = #text "\n  "
p1.nextElementSibling   = <p id=p2>
p1.parentNode           = <div id=box>
p1.parentElement        = <div id=box>
(exit 0)
```

**규칙 한 문장**

- **이름에 `Element` 가 들어가면 텍스트·주석을 건너뛴다.** 안 들어가면 나온 순서 그대로 준다.

**부모 쌍이 다른 이유**

- 부모는 **하나뿐이라 건너뛸 대상이 없다.** 그래서 부모 쌍의 규칙은 「건너뛴다」가 아니라 「**부모가 요소가 아니면 `null` 을 준다**」이다.

**쌍은 여섯**

```text
   firstChild        / firstElementChild
   lastChild         / lastElementChild
   nextSibling       / nextElementSibling
   previousSibling   / previousElementSibling
   childNodes        / children
   parentNode        / parentElement        <- 이 쌍만 규칙이 다르다
```

### 4. 나무 꼭대기에서 부모를 물으면 — 하나만 `null`

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,13p;15,16p'
document.body.parentNode           = <html>
document.body.parentElement        = <html>
document.documentElement.parentNode    = #document
document.documentElement.parentElement = null
frag 안 span.parentNode    = #document-fragment
frag 안 span.parentElement = null
(exit 0)
```

**갈리는 줄과 그 이유**

- 네 번째 줄만 `null` 이다. 그리고 그 이유는 **「부모가 없어서」가 아니다** — 부모는 `#document` 로 멀쩡히 있고, 그것이 **요소가 아닐** 뿐이다(`nodeType 9`).

**`parentNode` 루프의 문제**

```text
   <div> -> <body> -> <html> -> #document -> null
                                   ^^^^^^^^^
                                   요소가 아닌데 한 바퀴 더 돈다
   여기서 el.matches(...) 를 부르면 TypeError 가 난다
```

- `parentElement` 로 쓰면 `<html>` 에서 저절로 멈춘다. 조건에 맞는 조상을 찾는 것이면 **`closest()` 한 줄**이 낫다.

**조각 안의 노드**

- 같은 모양이다 — `parentNode` 는 **`#document-fragment`**, `parentElement` 는 **`null`**. 조각도 요소가 아니기 때문이다(`nodeType 11`).

### 5. `ownerDocument` 와 `isConnected` — 다른 질문이다

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
document                  nodeType= 9  nodeName=#document
document.doctype          nodeType=10  nodeName=html
document.documentElement  nodeType= 1  nodeName=HTML
p 안의 텍스트             nodeType= 3  nodeName=#text
새 주석                   nodeType= 8  nodeName=#comment
새 조각                   nodeType=11  nodeName=#document-fragment

el.ownerDocument === document      = true
alien.ownerDocument === document   = false
alien.ownerDocument === other      = true
붙인 뒤 alien.ownerDocument === document = true

el  instanceof Node/Element/HTMLElement = true/true/true
t   instanceof Node/CharacterData/Element = true/true/false
c   instanceof Node/CharacterData/Element = true/true/false
f   instanceof Node/Element = true/false
document instanceof Node/Element = true/false
(exit 0)
```

**갓 만든 노드**

- `el.ownerDocument === document` 는 **`true`**, `el.isConnected` 는 **`false`**.
- **만든 순간 이미 문서에 매인다.** 「매였다」와 「붙어 있다」는 다른 이야기다.

**다른 문서의 노드**

- 붙이기 **전** — `alien.ownerDocument === other` 가 `true`, `=== document` 는 `false`.
- 붙인 **뒤** — `alien.ownerDocument === document` 가 **`true`** 로 바뀐다.

**예외가 안 나는 이유**

- 명세가 삽입 절차 안에 **입양(adopt)** 단계를 넣어 뒀기 때문이다. 옛 DOM 에서 `WrongDocumentError` 를 던지던 자리다.

```text
   other 문서                      document
   +-----------+                   +-----------+
   |  <i>      |   appendChild     |  <body>   |
   +-----------+  ------------->   |    <i>    |   ownerDocument 가 함께 바뀐다
                                   +-----------+
```

**어느 것을 써야 하나**

- 「문서에 있나」는 **`isConnected`** 다. `ownerDocument` 는 갓 만든 노드에도 `document` 를 답하므로 **항상 그렇다고 대답한다.**

### 6. 번호표 여섯 개

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
document                  nodeType= 9  nodeName=#document
document.doctype          nodeType=10  nodeName=html
document.documentElement  nodeType= 1  nodeName=HTML
p 안의 텍스트             nodeType= 3  nodeName=#text
새 주석                   nodeType= 8  nodeName=#comment
새 조각                   nodeType=11  nodeName=#document-fragment
(exit 0)
```

**여섯의 뜻**

- `1` 요소 · `3` 텍스트 · `8` 주석 · `9` 문서 · `10` doctype · `11` 문서 조각.

**빈 번호**

- `2`(속성)·`4`(CDATA 구역)·`5`(엔티티 참조)·`6`(엔티티)·`12`(표기법)는 **DOM4 에서 제거**됐고 **번호만 예약된 채로 남았다.** 특히 **속성이 노드에서 빠진 것**이 가장 큰 변화다.

**`#` 으로 시작하는 이름**

- 요소가 **아닌** 노드들이다 — `#text`·`#comment`·`#document`·`#document-fragment`. 요소는 태그 이름이 오고, `doctype` 만 예외적으로 `html` 이라는 맨 이름이 온다.

**`nodeValue` 가 값을 갖는 노드**

- **`Text` 와 `Comment`** 뿐이다(둘 다 `CharacterData`). 요소는 `null` 이다 — 출력의 `nodeValue=null` 이 그것이다.

### 7. `--dump-dom` 이 보여 주는 것 — 소스가 아니라 나무다

**출력**

```html
<!-- ex01d.html -->
<!doctype html>
<meta charset="utf-8">
<title>01d</title>
<p id="hello">안녕</p>
<script>
const p = document.getElementById('hello');
p.textContent = '바뀐 글';
p.setAttribute('data-touched', 'yes');
p.after(document.createElement('hr'));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01d.html
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>01d</title>
</head><body><p id="hello" data-touched="yes">바뀐 글</p><hr>
<script>
const p = document.getElementById('hello');
p.textContent = '바뀐 글';
p.setAttribute('data-touched', 'yes');
p.after(document.createElement('hr'));
</script>
</body></html>
(exit 0)
```

**소스인가 나무인가**

- **나무다.** 소스에는 없는 것이 셋 들어 있다 — `<html>`/`<head>`/`<body>`, 바뀐 글자와 `data-touched` 속성, 새로 생긴 `<hr>`.

**안 쓴 태그가 있는 이유**

- **HTML 파서가 넣었다.** 그 규칙의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서·오류 복구)이다. 여기서는 **그 결과를 API 로 읽고 바꾸는 것**만 다룬다.

**`<hr>` 이 보이는 이유**

- `--dump-dom` 이 **스크립트가 다 돌고 난 뒤**의 나무를 직렬화하기 때문이다. 그래서 이 창은 **「내 API 호출이 무엇을 바꿨나」의 증거**가 된다.

**이 창이 못 보는 것**

- **한 시점의 스냅샷**이라 그 뒤에 타이머·네트워크로 바뀌는 것은 안 보인다.
- **노드의 정체를 못 보여 준다.** 직렬화된 문자열에서 공백 텍스트 노드는 그냥 줄바꿈처럼 보인다 — 그것이 노드인지 아닌지는 **창 2**(`childNodes.length`)로만 안다.
- **컬렉션이 살아 있는지도 못 본다** — 그것은 **창 3**(두 번 읽기)의 몫이다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).

### 8. 공백 텍스트 노드가 안 생기는 자리

**연속 공백이 노드 하나인 이유**

- 파서는 **문자들을 모아 두었다가** 다음 태그를 만날 때 **한 번에 텍스트 노드로 삽입**한다. 그래서 `"\n  "` 처럼 여러 문자가 **노드 하나**가 된다.

**한 줄로 붙여 쓰면**

- 태그와 태그 사이에 **문자가 하나도 없어서** 삽입할 텍스트 노드 자체가 생기지 않는다.

**지우는 표준 API**

- **없다.** `normalize()` 는 **인접한 텍스트 노드를 합칠** 뿐 지우지 않는다. 대처는 둘이다 — 빌드 단계에서 마크업의 공백을 줄이거나, 읽는 쪽에서 `children` 계열을 쓰는 것.

**화면과 노드는 다른 이야기**

- **다르다.** 화면에서 공백이 하나로 합쳐 보이는 것은 **CSS 의 `white-space` 처리**이고, 노드는 그대로 남아 있다. 공백이 화면에서 어떻게 축약되는지는 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **04번**(공백·텍스트·문자 참조)이 정본이다.

### 9. 무엇이 무엇을 상속하나

**출력**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,17p'
el  instanceof Node/Element/HTMLElement = true/true/true
t   instanceof Node/CharacterData/Element = true/true/false
c   instanceof Node/CharacterData/Element = true/true/false
f   instanceof Node/Element = true/false
document instanceof Node/Element = true/false
(exit 0)
```

**네 줄의 답과 계층**

- 텍스트 노드는 `Element` 가 **아니다** · 주석은 `CharacterData` **다** · 조각은 `Node` **다** · `document` 는 `Element` 가 **아니다**.

```text
                      Node
                        |
     +-------------+----+--------+----------------+
     |             |             |                |
  Element    CharacterData   Document    DocumentFragment
     |             |
  HTMLElement   +--+----+
                |       |
              Text   Comment
```

**텍스트 노드에 `children` 이 없는 이유**

- `children` 은 **`ParentNode`** 믹스인의 것이고, 그것을 갖는 것은 `Element`·`Document`·`DocumentFragment` 뿐이다. 텍스트 노드는 자식을 가질 수 없다.

**누가 무엇을 주나**

- `childNodes`·`firstChild`·`parentNode` = **`Node`**.
- `children`·`firstElementChild`·`append`·`prepend`·`querySelector` = **`ParentNode`**(그리고 `Element`).

**조각이 `children` 을 갖는 이유**

- **`DocumentFragment` 도 `ParentNode`** 이기 때문이다. 그래서 문서에 붙이기 전에도 요소를 같은 방식으로 다룰 수 있다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)).

### 10. 다른 주제와 잇기

**둘 다 라이브인 것이 출발점인 이유**

- `childNodes`(`NodeList`)와 `children`(`HTMLCollection`)이 **둘 다 라이브**라, 「`NodeList` 는 정적이고 `HTMLCollection` 은 라이브」라는 흔한 요약이 **틀렸음**이 여기서 이미 드러난다. 갈리는 것은 **타입이 아니라 그 타입을 만든 API** 다([02번 주제](../02-element-queries-and-live-collections/2-summary.md)).

**경계**

- 「**마크업에서 트리가 나오는 규칙**」은 HTML 갈래(03번·04번), 「**그 트리를 읽는 API 계약**」은 이 갈래다. 「**값과 타입의 의미**」는 JS 갈래다.

**대문자와 소문자**

- HTML 문서의 **HTML 요소**만 `nodeName` 이 ASCII 대문자다. SVG·MathML 요소와 XML 문서의 요소는 **원래 대소문자 그대로**다 — 그래서 문자열 비교로 태그를 가르는 코드는 SVG 를 만나면 조용히 어긋난다.

**명세가 타입별로 정했다는 말**

- 「라이브냐」는 **구현이 고른 최적화가 아니라 명세가 인터페이스마다 못 박은 계약**이다. `HTMLCollection` 은 정의부터 라이브이고, `NodeList` 는 **그것을 만든 쪽이 라이브인지 정적인지 정한다.** 그래서 「Chrome 은 이렇더라」가 아니라 「**이렇게 되어야 한다**」로 읽는다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다**(Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고, WebKit 은 없다). 따라서 **크로스 브라우저 이식성은 이 문서의 주장 범위 밖**이다.

**하네스** — 01\~04 네 주제가 공유한다. 실험 파일마다 결과를 문자열로 모아 **`<script type="text/plain">` 노드**에 넣고, `--dump-dom` 으로 받은 뒤 마커 사이만 잘라낸다.

```bash
# 블록 하나를 다시 던지는 법 — 소스 펜스를 그 이름의 .html 로 저장하고 같은 디렉토리에서
google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex01a.html \
  | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
```

```js
// 출력을 담는 관용구 — 왜 <pre> 가 아니라 <script type="text/plain"> 인가
// <pre> 에 넣으면 직렬화 때 < 와 & 가 &lt;·&amp; 로 이스케이프되어 원문이 상한다.
// script 요소의 자식은 HTML 직렬화가 '날것 그대로' 뱉으므로 마크업 문자열을 그대로 실을 수 있다.
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
```

★ **`--virtual-time-budget` 은 쓰지 않았다.** 이 갈래의 정본 규칙이고, 시간이 걸린 실험을 조용히 무효화하기 때문이다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `childNodes` 대 `children` 전수 덤프(`nodeType`·`nodeName`·`nodeValue`) | 2 | 동작 방식 (2) · A1 · A2 |
| 탐색 쌍 8줄 + 문서 꼭대기 4줄 + 조각 2줄 | 2 | 동작 방식 (3)·(4) · A3 · A4 |
| `nodeType` 여섯 종 + `instanceof` 다섯 줄 | 2 | 동작 방식 (1) · A6 · A9 |
| `ownerDocument` 세 줄 + 입양 뒤 한 줄 | 2 | 동작 방식 (5) · A5 |
| 소스 대 `--dump-dom` 대조(파서 삽입·API 변경) | 2 | 동작 방식 (0) · A7 |
| `demo01` 을 래퍼에 띄워 census 가 7줄인지 | 1 | 동작 방식 (2)의 demo |
| `demo01` 의 「바꿔 볼 것」(한 줄로 붙여 쓰기 · `children` 으로 바꾸기) | 1 | 같은 demo |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `--dump-dom` 의 직렬화 형태 | `hidden=""` · 속성 순서 = 소스 순서 | 직렬화는 명세가 정하지만 **줄바꿈 위치와 도구 동작은 Chrome 의 것** |
| `document.implementation.createHTMLDocument` 가 만든 문서의 세부 | 위 출력대로 | 명세가 뼈대를 정하지만 세부는 이 판의 관찰 |
| `--dump-dom` 이 **로드 완료 시점**을 잡는 것 | 스크립트 실행 뒤의 트리가 나온다 | 도구 동작이고 명세와 무관하다 |

**안 돌려 본 것** — ① Firefox·Safari 에서의 재현(엔진이 없다). **이 문서의 모든 관찰은 Blink 한 판의 것**이고, 그중 명세가 보장하는 항목은 「구현 세부사항 대 언어 보장」 표에 갈라 적었다. ② 개발자 도구 Elements 패널에서 공백 텍스트 노드가 어떻게 보이는지(headless 라 UI 가 없다).

## 용어 풀이

- **노드(node)** — DOM 나무의 점 하나. 요소·글자·주석·문서·조각이 전부 노드다.
- **`nodeType`** — 노드의 종류를 나타내는 정수 상수. `1`·`3`·`8`·`9`·`10`·`11` 여섯이 오늘 만나는 전부다.
- **`nodeName`** — 요소면 태그 이름(HTML 문서의 HTML 요소는 대문자), 아니면 `#` 으로 시작하는 고정 문자열.
- **`nodeValue`** — `Text`·`Comment` 만 값을 갖는다. 요소는 `null`.
- **`CharacterData`** — `Text` 와 `Comment` 의 공통 조상. 「글자를 담는 노드」라는 계층.
- **`ParentNode`** — `children`·`firstElementChild`·`append`·`prepend`·`querySelector` 를 주는 믹스인.
- **입양(adopt)** — 다른 문서의 노드를 이 문서 것으로 바꾸는 명세상의 단계. 삽입할 때 자동으로 일어난다.
- **`isConnected`** — 이 노드가 지금 문서 트리에 이어져 있나. `ownerDocument` 와 다른 질문이다.
- **`--dump-dom`** — Chrome 의 headless 스위치. **로드가 끝난 시점의 DOM 을 HTML 로 직렬화**해 표준 출력으로 뱉는다.
- **직렬화(serialization)** — 나무를 다시 HTML 문자열로 그리는 것. `innerHTML` 읽기도 같은 알고리즘을 쓴다.
