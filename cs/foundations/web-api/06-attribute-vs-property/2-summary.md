# web-api/06 — 속성(attribute) 대 성질(property): `getAttribute`/`setAttribute` 와 IDL 프로퍼티의 반영 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 언어 문법은 [`../../languages/`](../../languages/) 에 있고, 여기는 **브라우저가 건네주는 객체와 그 계약**이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Interface `Element`」·「Attr」 절과 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/common-dom-interfaces.html#reflecting-content-attributes-in-idl-attributes) 의 「Reflecting content attributes in IDL attributes」 절, 그리고 [`input` 요소](https://html.spec.whatwg.org/multipage/input.html#the-input-element)·[`a` 요소](https://html.spec.whatwg.org/multipage/text-level-semantics.html#the-a-element) 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.** 다만 **이 주제의 핵심은 구현 사정이 아니라 명세가 속성마다 못 박은 계약**이라 명세 문장을 근거로 드는 자리가 유난히 많다.\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `getAttribute`/`setAttribute` 는 DOM Level 1(1998) 부터 있었고 「반영」이라는 말과 규칙 표는 HTML5 가 정리한 것이다.\
> **선행** — [01번 주제](../01-document-and-node-tree/2-summary.md)(문서와 노드 트리). 그리고 **속성이 트리에 어떤 글자로 담기는지**는 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번**([요소와 속성 문법](../../languages/html/syntax/02-elements-and-attributes/2-summary.md))이 정본이다 — 소문자화·중복 버리기·따옴표 경계·불리언의 존재 판정은 거기서 이미 실측했다. **여기는 이미 담긴 그것을 두 API 표면으로 읽고 쓸 때 생기는 비대칭부터**다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 없다.** 수치를 재지 않기 때문이다 — 시간도, 크기도, 개수의 추정도 없다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | `getAttribute` 의 반환값 · 프로퍼티 값 · `null` 대 `""` · 직렬화 문자열 · 예외 이름 | 전부 명세가 절차로 정한 결과다 |
| **안 흔들린다** | 속성 개수 · 속성 이름의 순서 | 이 문서가 만든 순서 그대로다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 그래서 제출 전 재대조에서 **정규화할 칸이 하나도 없다.** 블록이 한 글자라도 달라지면 그것은 전부 「고칠 것」이다.
- **수치가 없다는 사실 자체가 이 주제의 성격**이다. 여기서 재는 것은 빠르기가 아니라 **계약**이다 — 「이 속성은 저 프로퍼티와 이어져 있는가」.

## 한눈에 — 쉽게 말하면

**★ 요소 하나에 칸이 두 벌 있다. 마크업에 적힌 「속성」과 객체에 달린 「성질」이고, 둘을 잇는 배선은 속성마다 제각각이다.**

관공서 창구에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 손으로 적어 낸 **원서** | 속성(content attribute) — 마크업에 있는 것. **언제나 글자열**이다 |
| 창구 직원의 **화면 칸** | 성질(IDL 프로퍼티) — `el.id`·`el.checked`. **타입이 있다** |
| 원서와 화면이 **한 선으로 이어진 칸** | 반영(reflect) — 한쪽을 고치면 다른 쪽이 따라온다 |
| 원서 이름과 화면 이름이 **다른 칸** | `class` ↔ `className` · `for` ↔ `htmlFor` |
| 손님이 말을 바꾸면 **화면만 바뀌는 칸** | `value`·`checked` — 원서는 「처음 적어 온 것」으로 남는다 |
| 화면이 원서 글자를 **풀어서 보여 주는 칸** | `href` — 원서는 `sub/page.html`, 화면은 절대 URL |
| **원서를 복사기에 넣으면** | 직렬화 — 화면에만 있던 것은 복사본에 안 온다 |

- **「반영」은 구현의 사정이 아니라 명세가 속성마다 못 박은 계약이다.** 그래서 외우는 것이 아니라 **네 꼴로 나누어 판정**한다.
- **원서에 없는 칸을 물으면 「원서에 그 줄이 없다」(`null`)** 이고, **화면에 없는 값을 물으면 「빈 칸」**(`""`·`false`·`-1`)이다. 둘은 다른 대답이다.
- ★ **성질에만 쓴 것은 문서를 다시 글자로 뽑을 때 사라진다.** 이 문서의 창 ④ 가 그것만 본다.

```text
   마크업에 있는 것                     객체에 달린 것
   +-------------------------+         +--------------------------+
   |  속성 (content attr)    |  <-----> |  성질 (IDL property)    |
   |  <input value="초기">   |  반영    |  el.value = "초기"       |
   |  언제나 글자열          |  (배선)  |  타입이 있다 (string,    |
   |  getAttribute 로 읽는다 |          |   boolean, number, ...)  |
   +-------------------------+         +--------------------------+
              |                                     |
              v                                     v
        직렬화에 남는다                     직렬화에 안 남는다
        (outerHTML · --dump-dom)            (복사하면 사라진다)
```

**배선이 네 꼴이다.** 이 그림 하나가 이 주제의 전부다.

```text
  ① 그대로 이어짐        속성 "b2" <---------> 성질 "b2"       (id · title · hidden)
  ② 이름만 다름          속성 class <--------> 성질 className  (for <-> htmlFor)
  ③ 한쪽으로만 흐름      속성 value ---초기값--> 성질 value
                                    <--X--                     (사용자·스크립트가 바꾼 뒤)
  ④ 지나가며 풀림        속성 "sub/p.html" --절대화--> 성질 "https://…/sub/p.html"
```

## 이 주제가 답하려는 질문

1. **`input.value` 를 바꿨는데 `value` 속성이 그대로인 것은 버그인가.** 아니라면 무엇이 그렇게 정했나.
2. **반영 규칙을 외워야 하나.** 아니라면 **무엇으로 판정**하나.
3. **성질에만 있는 상태는 어디까지 따라오나** — 복제·직렬화·폼 리셋에서 각각 어떻게 되나.

## 이 갈래의 관측 창 — ★ 창 4 는 「속성 칸 그 자체」

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom             스크립트가 다 돈 뒤의 트리를 글자로
  창 2  노드 단위 프로브        getAttribute / 프로퍼티 를 같은 줄에 나란히
  창 3  두 번 읽기              바꾸기 전 / 바꾼 뒤를 같은 프로브로
  ★ 창 4 (이 주제 고유)  속성 칸 그 자체 — 'el.attributes' · 'outerHTML' · 직렬화 왕복
        무엇을 답하나:  성질에 쓴 그것이 '속성 칸'에 남았는가
        이 한 창이 세 가지를 한꺼번에 가른다
          - 반영되는 성질인가, 내가 만든 그냥 프로퍼티(expando)인가
          - 이 상태가 innerHTML 복사에 따라오나
          - cloneNode 와 innerHTML 왕복이 왜 갈리나
```

- **창 4 를 먼저 정한 것이 이 주제의 설계**다. 창 1\~3 은 **값이 무엇인지**를 보여 주지만 **그 값이 어느 쪽 칸에 사는지**는 안 보여 준다. 두 칸이 우연히 같은 값이면 셋 다 「정상」이라고 답한다.
- ★ **창 1 과 창 4 는 다르다.** 창 1 은 **끝난 뒤 한 번** 전체 문서를, 창 4 는 **조작 사이사이에 같은 자리를** 묻는다. 그리고 창 4 에는 창 1 에 없는 것이 하나 더 있다 — **왕복**(직렬화했다가 다시 파싱하면 무엇이 사라지나).

## 동작 방식

### (1) 「반영」은 명세가 속성마다 못 박은 계약이다

**언제 쓰나** — `el.무엇` 이 `getAttribute('무엇')` 과 같은 것이라고 **가정하기 직전**에.

HTML 명세에는 「Reflecting content attributes in IDL attributes」라는 절이 있다. 거기서 **「이 IDL 프로퍼티는 저 콘텐츠 속성을 반영한다」고 선언된 것만** 이어져 있고, **반영의 종류도 그 자리에서 정해진다** — 글자열인지, 불리언인지, 「URL 로 푼다」인지, 「알려진 값만 받는다」인지.

```text
  명세의 요소 정의                             그 결과
  ┌──────────────────────────────────┐
  │ a 요소:                          │
  │   href — reflect, URL 로 푼다     │ ─────> lk.href 가 절대 URL 을 준다
  │ label 요소:                      │
  │   htmlFor — 'for' 속성을 reflect  │ ─────> 이름이 다른 이유가 여기 있다
  │ input 요소:                      │
  │   defaultValue — 'value' reflect  │ ─────> value 속성은 defaultValue 쪽에 이어져 있고
  │   value — '값 모드'에 따른 별도    │        el.value 는 반영이 아니다
  └──────────────────────────────────┘
```

- **그래서 외울 것은 목록이 아니라 네 꼴이다.** 아래 (2)\~(5) 가 그 넷이고, (6) 이 「그 밖」이다.
- ★ **반영이 없는 속성도 많다.** `data-user-id` 를 아무리 써도 `el.dataUserId` 는 생기지 않는다 — 그쪽은 반영이 아니라 `dataset` 이라는 **별도 표면**이고, 그것이 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)다.

비용 — 판정은 명세를 한 번 읽는 값이고, 안 하면 **조용히 틀린 채 도는 코드**를 얻는다.

### (2) 꼴 ① — 그대로 반영된다

**언제 쓰나** — `id`·`title`·`hidden`·`lang` 처럼 **이름도 같고 뜻도 같은** 속성에서.

**던진 것** — 이 한 파일이 꼴 ①\~④ 와 「없는 속성」까지 전부 찍는다. 아래 (3)\~(5)·(어디서 틀리나 5)의 블록이 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa06b-06-four.html -->
<!doctype html>
<meta charset="utf-8">
<base href="https://example.org/a/b/">
<title>06-four</title>
<div id="a1" class="card big" title="쪽지"></div>
<label id="lb" for="f1">라벨</label>
<form id="fm"><input id="in" value="초기"><input id="ck" type="checkbox" checked></form>
<a id="lk" href="sub/page.html?q=1#n">링크</a>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const J = v => JSON.stringify(v);
const el = document.getElementById('a1');
const row = (label, ...cells) => O.push(padw(label, 28) + cells.map((c, i) => padw(c, i === cells.length - 1 ? 0 : 24)).join(''));

O.push('① 반영된다 — 이름도 같고 양쪽이 서로 따라간다 (id)');
row('', "getAttribute('id')", 'el.id');
row('처음', J(el.getAttribute('id')), J(el.id));
el.setAttribute('id', 'b2');
row("setAttribute('id','b2')", J(el.getAttribute('id')), J(el.id));
el.id = 'c3';
row("el.id = 'c3'", J(el.getAttribute('id')), J(el.id));
el.removeAttribute('id');
row("removeAttribute('id')", J(el.getAttribute('id')), J(el.id));
O.push('');

O.push('② 이름이 다르다 — class ↔ className · for ↔ htmlFor');
const lb = document.getElementById('lb');
row('', "getAttribute", '프로퍼티');
row("el.class 라는 프로퍼티", '(없다)', String(el.class));
row("class / className", J(el.getAttribute('class')), J(el.className));
el.className = 'x y';
row("className = 'x y' 뒤", J(el.getAttribute('class')), J(el.className));
row("label.for 라는 프로퍼티", '(없다)', String(lb.for));
row("for / htmlFor", J(lb.getAttribute('for')), J(lb.htmlFor));
O.push('');

O.push('③ 한쪽만 바뀐다 — input.value 는 「초기값」만 반영한다');
const inp = document.getElementById('in');
const r3 = (label) => row(label, J(inp.getAttribute('value')), J(inp.value), J(inp.defaultValue));
row('', "getAttr('value')", '.value', '.defaultValue');
r3('처음');
inp.setAttribute('value', 'A');
r3("setAttribute('value','A')");
inp.value = 'B';
r3("inp.value = 'B'");
inp.setAttribute('value', 'C');
r3("setAttribute('value','C')");
document.getElementById('fm').reset();
r3('form.reset()');
O.push('');

O.push('③ 같은 꼴의 불리언판 — checkbox 의 checked 와 defaultChecked');
const ck = document.getElementById('ck');
const r4 = (label) => row(label, J(ck.getAttribute('checked')), String(ck.checked), String(ck.defaultChecked));
row('', "getAttr('checked')", '.checked', '.defaultChecked');
r4('처음 (마크업에 checked)');
ck.click();
r4('ck.click() 사용자 조작');
ck.setAttribute('checked', 'checked');
r4("setAttribute('checked')");
ck.checked = true; ck.removeAttribute('checked');
r4("checked=true · 속성 제거");
O.push('');

O.push('④ URL 이 정규화된다 — getAttribute 는 원문, 프로퍼티는 절대 URL');
const lk = document.getElementById('lk');
O.push("문서의 base = " + J(document.baseURI));
row("getAttribute('href')", J(lk.getAttribute('href')));
row('lk.href', J(lk.href));
row('lk.protocol/host/pathname', J(lk.protocol) + ' ' + J(lk.host) + ' ' + J(lk.pathname));
row('lk.search / lk.hash', J(lk.search) + ' ' + J(lk.hash));
lk.href = '../up.html';
row("lk.href = '../up.html' 뒤", "속성 " + J(lk.getAttribute('href')) + "  프로퍼티 " + J(lk.href));
O.push('');

O.push('없는 속성을 물으면 — 「빈 값」이 프로퍼티 타입마다 다르다');
const b = document.createElement('div');
for (const [attr, prop, val] of [['id', 'id', b.id], ['class', 'className', b.className],
     ['title', 'title', b.title], ['tabindex', 'tabIndex', b.tabIndex],
     ['hidden', 'hidden', b.hidden], ['data-x', 'dataset.x', b.dataset.x]]) {
  row("getAttribute('" + attr + "')", J(b.getAttribute(attr)), 'el.' + prop + ' = ' + J(val));
}
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
① 반영된다 — 이름도 같고 양쪽이 서로 따라간다 (id)
                            getAttribute('id')      el.id
처음                        "a1"                    "a1"
setAttribute('id','b2')     "b2"                    "b2"
el.id = 'c3'                "c3"                    "c3"
removeAttribute('id')       null                    ""
(exit 0)
```

- 네 줄이 전부 **양쪽이 같다.** `setAttribute` 로 써도 프로퍼티가 따라오고, 프로퍼티로 써도 속성이 따라온다.
- ★ **마지막 줄만 다르다.** `removeAttribute('id')` 뒤 속성은 `null` 인데 프로퍼티는 `""` 다. **없는 것을 두 창구에 물으면 대답이 다르다** — 아래 (6) 에서 다시 본다.

```text
   setAttribute('id','b2')            el.id = 'c3'
   ┌──────────┐                       ┌──────────┐
   │ 속성 "b2"│──반영──> 성질 "b2"    │성질 "c3" │──반영──> 속성 "c3"
   └──────────┘                       └──────────┘
        양방향이다 — 어느 쪽으로 써도 반대쪽이 따라온다
```

비용 — 없다. 이 꼴에서는 두 표면 중 아무거나 써도 된다.

### (3) 꼴 ② — 이름이 다르다

**언제 쓰나** — `class` 와 `for` 를 스크립트에서 다룰 때. **둘뿐**이라고 기억하면 된다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,14p'
② 이름이 다르다 — class ↔ className · for ↔ htmlFor
                            getAttribute            프로퍼티
el.class 라는 프로퍼티      (없다)                  undefined
class / className           "card big"              "card big"
className = 'x y' 뒤        "x y"                   "x y"
label.for 라는 프로퍼티     (없다)                  undefined
for / htmlFor               "f1"                    "f1"
(exit 0)
```

- **`el.class` 와 `label.for` 는 없다** — `undefined` 다. 예외가 아니라 **그냥 없는 프로퍼티**라 조용하다.
- 이름이 갈린 이유는 역사다. `class` 와 `for` 는 **초기 자바스크립트의 예약어**였고, 그래서 IDL 쪽 이름이 `className`·`htmlFor` 가 됐다.
- ★ **`className` 을 두고 오늘 실제로 쓰는 것은 `classList` 다.** 그쪽은 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)다.

```text
   마크업            성질 이름          왜
   class="card"  ->  el.className       'class' 가 예약어였다
   for="f1"      ->  label.htmlFor      'for' 가 예약어였다
   그 밖         ->  이름이 같다        (id · title · hidden · lang · dir …)
```

비용 — 없다. 다만 **오타가 조용하다** — `el.classname = 'x'` 는 에러 없이 **그냥 프로퍼티 하나를 만들고 끝난다**(아래 (6)).

### (4) 꼴 ③ — 한쪽만 바뀐다 (★ 이 주제의 중심)

**언제 쓰나** — 폼을 스크립트로 다룰 때. **사고가 여기 몰린다.**

`input.value` 는 **반영이 아니다.** 명세에서 `value` 속성을 반영하는 프로퍼티는 **`defaultValue`** 이고, `el.value` 는 「값 모드」라는 별도 상태다. 세 칸을 나란히 찍으면 한눈에 보인다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '16,22p'
③ 한쪽만 바뀐다 — input.value 는 「초기값」만 반영한다
                            getAttr('value')        .value                  .defaultValue
처음                        "초기"                  "초기"                  "초기"
setAttribute('value','A')   "A"                     "A"                     "A"
inp.value = 'B'             "A"                     "B"                     "A"
setAttribute('value','C')   "C"                     "B"                     "C"
form.reset()                "C"                     "C"                     "C"
(exit 0)
```

```text
   시각 ->

   처음            속성 "초기"   .value "초기"   .defaultValue "초기"
                        └───────────반영───────────┘   (셋이 같다)

   setAttribute('value','A')
                   속성 "A"      .value "A"      .defaultValue "A"
                        └───────────반영───────────┘   (아직 안 갈렸다)

   inp.value = 'B'         ★ 여기서 갈린다
                   속성 "A"      .value "B"      .defaultValue "A"
                        └─반영─┘  ×           (배선이 끊긴 것이 아니라
                                                 .value 가 별도 상태로 옮겨 앉는다)

   setAttribute('value','C')
                   속성 "C"      .value "B"      .defaultValue "C"
                                  ↑ 안 따라온다

   form.reset()    속성 "C"      .value "C"      .defaultValue "C"
                                  ↑ 리셋이 defaultValue 를 다시 부어 준다
```

- **`setAttribute('value', …)` 는 「초기값」을 고치는 것**이고, 사용자나 스크립트가 `.value` 를 한 번이라도 만진 뒤에는 **화면에 아무 영향이 없다.**
- ★ **되돌리는 길은 `form.reset()`** 이다. 그때 `.value` 가 `defaultValue` 로 되돌아간다 — 위 마지막 줄이 그 증거다.
- 「값 모드가 바뀌었다」를 명세는 **dirty value flag** 라고 부른다. 이름이 있다는 것 자체가 **구현 사정이 아니라 계약**이라는 뜻이다.

**같은 꼴의 불리언판이 `checked` 다.** 여기가 더 잘 틀린다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,29p'
③ 같은 꼴의 불리언판 — checkbox 의 checked 와 defaultChecked
                            getAttr('checked')      .checked                .defaultChecked
처음 (마크업에 checked)     ""                      true                    true
ck.click() 사용자 조작      ""                      false                   true
setAttribute('checked')     "checked"               false                   true
checked=true · 속성 제거    null                    true                    false
(exit 0)
```

- **마크업의 `checked` 속성 → `defaultChecked`** 이고, `el.checked` 는 별도 상태다.
- `ck.click()` **한 번**으로 `.checked` 가 `false` 가 되는데 **속성은 `""` 그대로**다. 창 1 로 보면 「체크돼 있다」로 보이고 실제 화면은 꺼져 있다.
- `setAttribute('checked','checked')` 를 해도 **`.checked` 는 안 켜진다**(세 번째 줄). 「체크 좀 켜 줘」를 속성으로 쓰면 아무 일도 안 난다.
- ★ **마지막 줄이 반대 방향의 증거**다 — `checked = true` 로 켜고 속성을 지우면 **`.checked` 는 `true` 인데 `defaultChecked` 가 `false`** 로 갈린다.

비용 — 이 꼴을 모르면 **폼 상태를 읽는 코드가 전부 조용히 틀린다.** 값은 성질로 읽고, 초기값은 속성으로 읽는다.

### (5) 꼴 ④ — 지나가며 풀린다 (URL)

**언제 쓰나** — 링크·이미지·폼의 주소를 스크립트로 읽을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '31,37p'
④ URL 이 정규화된다 — getAttribute 는 원문, 프로퍼티는 절대 URL
문서의 base = "https://example.org/a/b/"
getAttribute('href')        "sub/page.html?q=1#n"
lk.href                     "https://example.org/a/b/sub/page.html?q=1#n"
lk.protocol/host/pathname   "https:" "example.org" "/a/b/sub/page.html"
lk.search / lk.hash         "?q=1" "#n"
lk.href = '../up.html' 뒤   속성 "../up.html"  프로퍼티 "https://example.org/a/up.html"
(exit 0)
```

- **`getAttribute('href')` 는 마크업에 적힌 글자 그대로**이고, **`lk.href` 는 문서의 base 로 푼 절대 URL** 이다. 둘 다 「맞는 값」인데 **쓰임이 다르다.**
- 명세가 이 속성을 「URL 로 푸는(resolve) 반영」으로 못 박았기 때문이고, 덤으로 `protocol`·`host`·`pathname`·`search`·`hash` 라는 **조각 프로퍼티**까지 같이 온다.
- ★ **쓰는 쪽은 반대다** — `lk.href = '../up.html'` 로 쓰면 **속성에는 쓴 글자 그대로** 담기고 프로퍼티만 절대 URL 을 답한다. **왕복이 안 맞는 유일한 꼴**이다.

```text
   마크업           속성 (원문)                프로퍼티 (푼 것)
   sub/page.html?q=1#n
        │
        ├── getAttribute('href') ──> "sub/page.html?q=1#n"
        └── lk.href ──────────────> "https://example.org/a/b/sub/page.html?q=1#n"
                                       └ base href 로 풀었다
   쓰는 쪽
   lk.href = '../up.html'
        ├── 속성 ─────────────────> "../up.html"      (쓴 그대로)
        └── 프로퍼티 ─────────────> "https://example.org/a/up.html"
```

- 같은 꼴이 `img.src`·`form.action`·`area.href` 에도 걸린다. **원문이 필요하면 `getAttribute`**, **실제로 갈 곳이 필요하면 프로퍼티**다.

비용 — 문자열을 자르는 대신 프로퍼티를 읽으면 **base 해석·인코딩이 공짜로 맞는다.** 그 규칙 전체는 목록의 **45번 주제**(`URL`·`URLSearchParams`)다.

### (6) 그 밖 — 반영이 없는 것 · 제한된 반영 · 모양이 바뀌는 것

**언제 쓰나** — 위 네 꼴 어디에도 안 들어가는 속성을 만났을 때.

**던진 것**

```html
<!-- wa06b-06-edge.html -->
<!doctype html>
<meta charset="utf-8">
<title>06-edge</title>
<div id="d" data-user-id="7"></div>
<input id="in" type="text">
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push(padw(a, 34) + padw(b, 24) + (c === undefined ? '' : c));
const d = document.getElementById('d'), inp = document.getElementById('in');

O.push('반영은 명세가 속성마다 못 박은 것이다 — 없는 자리도 있고 제한된 자리도 있다');
row('', 'getAttribute', '프로퍼티');
row("data-user-id (반영 없음)", J(d.getAttribute('data-user-id')), 'd.dataUserId = ' + String(d.dataUserId));
row("  같은 것을 dataset 으로", J(d.getAttribute('data-user-id')), 'd.dataset.userId = ' + J(d.dataset.userId));
d.foo = 1;
row("d.foo = 1 (그냥 프로퍼티)", J(d.getAttribute('foo')), 'd.foo = ' + String(d.foo));
d.setAttribute('bar', '2');
row("setAttribute('bar','2')", J(d.getAttribute('bar')), 'd.bar = ' + String(d.bar));
row('  이때 d.outerHTML', J(d.outerHTML));
O.push('');

O.push('제한된 반영 — 알려진 값만 받고 나머지는 기본값으로 떨어진다 (input.type)');
row('', "getAttribute('type')", '.type');
row('처음', J(inp.getAttribute('type')), J(inp.type));
inp.setAttribute('type', 'checkbox');
row("setAttribute('type','checkbox')", J(inp.getAttribute('type')), J(inp.type));
inp.setAttribute('type', 'bogus');
row("setAttribute('type','bogus')", J(inp.getAttribute('type')), J(inp.type));
inp.setAttribute('type', 'TEXT');
row("setAttribute('type','TEXT')", J(inp.getAttribute('type')), J(inp.type));
inp.setAttribute('maxlength', '-3');
row("setAttribute('maxlength','-3')", J(inp.getAttribute('maxlength')), '.maxLength = ' + inp.maxLength);
O.push('');

O.push('값의 모양이 바뀐다 — 속성은 언제나 문자열, 프로퍼티는 IDL 타입');
row('', 'getAttribute', '프로퍼티');
d.hidden = true;
row('d.hidden = true', J(d.getAttribute('hidden')), 'd.hidden = ' + d.hidden);
d.tabIndex = 3;
row('d.tabIndex = 3', J(d.getAttribute('tabindex')), 'd.tabIndex = ' + d.tabIndex + ' (' + typeof d.tabIndex + ')');
d.setAttribute('tabindex', ' 07 ');
row("setAttribute('tabindex',' 07 ')", J(d.getAttribute('tabindex')), 'd.tabIndex = ' + d.tabIndex);
d.setAttribute('CLASS', 'q');
row("setAttribute('CLASS','q')", J(d.getAttribute('class')), 'd.className = ' + J(d.className));
row("  대문자로 되물으면", J(d.getAttribute('CLASS')), 'd.attributes.length = ' + d.attributes.length);
row('  최종 d.outerHTML', J(d.outerHTML));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-edge.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
반영은 명세가 속성마다 못 박은 것이다 — 없는 자리도 있고 제한된 자리도 있다
                                  getAttribute            프로퍼티
data-user-id (반영 없음)          "7"                     d.dataUserId = undefined
  같은 것을 dataset 으로          "7"                     d.dataset.userId = "7"
d.foo = 1 (그냥 프로퍼티)         null                    d.foo = 1
setAttribute('bar','2')           "2"                     d.bar = undefined
  이때 d.outerHTML                "<div id=\"d\" data-user-id=\"7\" bar=\"2\"></div>"
(exit 0)
```

- **`data-user-id` 를 써도 `d.dataUserId` 는 안 생긴다.** 반영이 아니라 **`dataset` 이라는 별도 표면**으로만 온다([07번 주제](../07-dataset-classlist-inline-style/2-summary.md)).
- ★ **`d.foo = 1` 은 속성을 만들지 않는다.** 그냥 자바스크립트 프로퍼티(expando)다. **에러도 경고도 없다.**
- ★ **거꾸로 `setAttribute('bar','2')` 도 프로퍼티를 만들지 않는다.** `d.bar` 는 `undefined` 다. **배선이 없는 이름은 양쪽 다 조용하다.**

**제한된 반영** — 속성에는 무엇이든 담기지만 프로퍼티는 「아는 값」만 답한다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-edge.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,15p'
제한된 반영 — 알려진 값만 받고 나머지는 기본값으로 떨어진다 (input.type)
                                  getAttribute('type')    .type
처음                              "text"                  "text"
setAttribute('type','checkbox')   "checkbox"              "checkbox"
setAttribute('type','bogus')      "bogus"                 "text"
setAttribute('type','TEXT')       "TEXT"                  "text"
setAttribute('maxlength','-3')    "-3"                    .maxLength = -1
(exit 0)
```

- `setAttribute('type','bogus')` 뒤 **속성은 `"bogus"` 인데 프로퍼티는 `"text"`** 다. 명세가 이것을 「**limited to only known values**」라고 부르고 **기본값으로 떨어뜨리라**고 정했다.
- `'TEXT'` 도 마찬가지다 — **속성 값은 대소문자를 보존**하고, 프로퍼티만 ASCII 대소문자 무시로 맞춰 본 뒤 `"text"` 를 답한다.
- `maxlength` 에 `-3` 을 주면 **`.maxLength` 가 `-1`**(「제한 없음」의 기본값)이다. **음수는 유효하지 않으므로 반영 규칙이 기본값을 쓴다.**

**모양이 바뀌는 것** — 속성은 언제나 글자열이고 프로퍼티는 IDL 타입이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-edge.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,24p'
값의 모양이 바뀐다 — 속성은 언제나 문자열, 프로퍼티는 IDL 타입
                                  getAttribute            프로퍼티
d.hidden = true                   ""                      d.hidden = true
d.tabIndex = 3                    "3"                     d.tabIndex = 3 (number)
setAttribute('tabindex',' 07 ')   " 07 "                  d.tabIndex = 7
setAttribute('CLASS','q')         "q"                     d.className = "q"
  대문자로 되물으면               "q"                     d.attributes.length = 6
  최종 d.outerHTML                "<div id=\"d\" data-user-id=\"7\" bar=\"2\" hidden=\"\" tabindex=\" 07 \" class=\"q\"></div>"
(exit 0)
```

- `d.hidden = true` → **속성은 `""`**(빈 문자열)다. 불리언 반영은 「있으면 참」이라 값이 필요 없다.
- `d.tabIndex = 3` → 속성 `"3"`, 프로퍼티 `3`(number). **`setAttribute('tabindex',' 07 ')` 처럼 공백과 앞자리 0 이 있어도 프로퍼티는 `7` 로 파싱**한다 — 속성 쪽에는 `" 07 "` 이 그대로 남는다.
- ★ **`setAttribute('CLASS', 'q')` 가 `class` 를 고친다.** HTML 문서에서 속성 이름은 소문자로 맞춰지기 때문이다(그 규칙의 정본은 HTML 갈래 **02번**). `getAttribute('CLASS')` 도 같은 것을 답한다.

비용 — 이 절이 없으면 「반영은 늘 대칭이다」를 기본값으로 갖게 되고, `type`·`maxlength` 처럼 **속성과 프로퍼티가 영구히 어긋난 채 도는 자리**를 못 찾는다.

### (7) ★ 창 ④ — 성질에만 있는 것은 글자로 안 나온다

**언제 쓰나** — DOM 을 복사·저장·전송할 때. **여기가 이 주제의 실무 사고 지점**이다.

먼저 창 ① 로 본다. 스크립트가 **성질로만** `value`·`checked`·`className`·`title` 을 바꾸고 프로퍼티 하나를 더 만든 문서다.

```html
<!-- wa06b-06-tree.html -->
<!doctype html>
<meta charset="utf-8">
<title>06-tree</title>
<form id="fm"><input id="in" value="초기"><input id="ck" type="checkbox"></form>
<div id="d" class="처음"></div>
<script>
  in_ = document.getElementById('in');
  in_.value = '성질로만 바꾼 것';
  document.getElementById('ck').checked = true;
  const d = document.getElementById('d');
  d.className = '성질로 바꾼 class';
  d.title = '성질로 준 title';
  d.zzzNotReflected = '성질에만 있는 칸';
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-tree.html | sed -n '4,5p'
</head><body><form id="fm"><input id="in" value="초기"><input id="ck" type="checkbox"></form>
<div id="d" class="성질로 바꾼 class" title="성질로 준 title"></div>
(exit 0)
```

- `className`·`title` 은 **속성 칸에 남았고**, `value` 는 **`"초기"` 그대로**이며, `checked` 는 **아예 없고**, `zzzNotReflected` 는 **흔적도 없다.**
- ★ **창 ① 만 보면 이 문서는 「입력칸이 비어 있고 체크가 꺼진」 문서로 읽힌다.** 실제 화면은 정반대다.

이제 창 ④ 로 같은 자리를 조작 사이사이에 묻는다.

**던진 것**

```html
<!-- wa06b-06-serialize.html -->
<!doctype html>
<meta charset="utf-8">
<title>06-serialize</title>
<form id="fm"><input id="in" name="n" value="초기"><input id="ck" type="checkbox" checked></form>
<div id="copy"></div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const fm = document.getElementById('fm');
const inp = document.getElementById('in'), ck = document.getElementById('ck');
const 보기 = () => J(fm.innerHTML);
O.push('창 ④ — 바꾼 뒤 문서 자신에게 「속성에 남았나」를 다시 묻는다');
O.push('처음                fm.innerHTML = ' + 보기());
O.push('                    속성 개수 = ' + inp.attributes.length + '   .value = ' + J(inp.value));
inp.value = '사용자가 친 것';
ck.click();
O.push("inp.value 대입 · ck.click() 뒤");
O.push('                    fm.innerHTML = ' + 보기());
O.push('                    속성 개수 = ' + inp.attributes.length + '   .value = ' + J(inp.value) +
       '   ck.checked = ' + ck.checked);
O.push('                    ★ 직렬화가 한 글자도 안 바뀌었다');
inp.id = 'z9';
O.push("inp.id = 'z9' 뒤     fm.innerHTML = " + 보기());
O.push('');

O.push('그래서 「복사」 세 경로의 결과가 갈린다 — 던져 보기 전에는 모른다');
const copy = document.getElementById('copy');
copy.innerHTML = fm.innerHTML;
O.push('innerHTML 왕복      복사본 input.value = ' + J(copy.querySelector('input').value) +
       '   checkbox.checked = ' + copy.querySelectorAll('input')[1].checked);
const c2 = fm.cloneNode(true);
O.push('cloneNode(true)     복사본 input.value = ' + J(c2.querySelector('input').value) +
       '   checkbox.checked = ' + c2.querySelectorAll('input')[1].checked);
const c3 = document.importNode(fm, true);
O.push('importNode(fm,true) 복사본 input.value = ' + J(c3.querySelector('input').value) +
       '   checkbox.checked = ' + c3.querySelectorAll('input')[1].checked);
O.push('원본                원본   input.value = ' + J(inp.value) + '   checkbox.checked = ' + ck.checked);
O.push('원본의 defaultValue / defaultChecked = ' + J(inp.defaultValue) + ' / ' + ck.defaultChecked);
O.push('★ 직렬화를 거친 경로만 사용자 상태를 잃는다. 노드 복제는 HTML 명세가 값을 함께 옮기라고 정한다');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-serialize.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
창 ④ — 바꾼 뒤 문서 자신에게 「속성에 남았나」를 다시 묻는다
처음                fm.innerHTML = "<input id=\"in\" name=\"n\" value=\"초기\"><input id=\"ck\" type=\"checkbox\" checked=\"\">"
                    속성 개수 = 3   .value = "초기"
inp.value 대입 · ck.click() 뒤
                    fm.innerHTML = "<input id=\"in\" name=\"n\" value=\"초기\"><input id=\"ck\" type=\"checkbox\" checked=\"\">"
                    속성 개수 = 3   .value = "사용자가 친 것"   ck.checked = false
                    ★ 직렬화가 한 글자도 안 바뀌었다
inp.id = 'z9' 뒤     fm.innerHTML = "<input id=\"z9\" name=\"n\" value=\"초기\"><input id=\"ck\" type=\"checkbox\" checked=\"\">"
(exit 0)
```

- 세 번 찍은 `fm.innerHTML` 중 **앞의 둘이 한 글자도 같다.** `.value` 대입과 `click()` 은 직렬화를 전혀 건드리지 않았다.
- **속성 개수도 3 그대로**다. 성질을 만져도 속성 칸에는 아무 일도 안 난다.
- 세 번째 줄에서 `inp.id = 'z9'` 로 **반영되는 성질**을 만지자 그제야 직렬화가 바뀐다. **창 ④ 가 꼴 ①과 꼴 ③을 한 줄로 가른다.**

**그래서 「복사」 세 경로의 결과가 갈린다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-serialize.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,16p'
그래서 「복사」 세 경로의 결과가 갈린다 — 던져 보기 전에는 모른다
innerHTML 왕복      복사본 input.value = "초기"   checkbox.checked = true
cloneNode(true)     복사본 input.value = "사용자가 친 것"   checkbox.checked = false
importNode(fm,true) 복사본 input.value = "사용자가 친 것"   checkbox.checked = false
원본                원본   input.value = "사용자가 친 것"   checkbox.checked = false
원본의 defaultValue / defaultChecked = "초기" / true
★ 직렬화를 거친 경로만 사용자 상태를 잃는다. 노드 복제는 HTML 명세가 값을 함께 옮기라고 정한다
(exit 0)
```

```text
             원본                        복사본
             .value "사용자가 친 것"
             속성   value="초기"

   innerHTML 왕복   ─글자로 뽑고 다시 파싱─>  .value "초기"     ★ 사용자 상태가 사라진다
   cloneNode(true)  ─노드를 그대로 복제─────>  .value "사용자가 친 것"
   importNode(…)    ─복제 + 입양──────────>  .value "사용자가 친 것"
```

- ★ **직렬화를 거친 경로만 상태를 잃는다.** 글자에는 속성만 있기 때문이다.
- **노드 복제는 잃지 않는다** — HTML 명세가 `input` 의 복제 절차에서 **값과 체크 상태를 함께 옮기라고 따로 정해 두었다.** 구현의 친절이 아니라 계약이다.
- 이것이 [05번 주제](../05-documentfragment-and-template/2-summary.md)의 `cloneNode`·`importNode` 와 [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md)의 `innerHTML` 이 **여기서 만나는 자리**다.

비용 — 「DOM 을 저장했다가 복원한다」를 `innerHTML` 로 하면 **사용자가 친 것이 전부 날아간다.** 에러는 없다.

```html demo
<div id="d6box">
  <input id="d6in" value="초기값">
  <button id="d6a">.value 로 바꾸기</button>
  <button id="d6b">setAttribute 로 바꾸기</button>
</div>
<div id="d6out"></div>
<style>
  #d6box { border: 2px dashed #94a3b8; padding: 8px; }
  #d6out { font-family: monospace; background: #0f172a; color: #e2e8f0; padding: 8px; margin-top: 6px; }
</style>
<script>
  const 보이기 = () => document.getElementById('d6out').textContent =
    document.getElementById('d6in').outerHTML + '\n.value = ' + document.getElementById('d6in').value;
  document.getElementById('d6a').onclick = () => { d6in.value = '스크립트가 넣은 것'; 보이기(); };
  document.getElementById('d6b').onclick = () => { d6in.setAttribute('value', '속성에 쓴 것'); 보이기(); };
  보이기();
</script>
```

> **보이는 것** — 점선 상자 안에 「초기값」이 든 입력칸과 버튼 둘이 있고, 아래 검은 칸에 **그 입력칸의 `outerHTML` 과 `.value` 가 나란히** 찍힌다. 처음에는 둘 다 「초기값」이다.\
> **`.value` 로 바꾸기**를 누르면 입력칸의 글자와 아래의 `.value` 는 「스크립트가 넣은 것」으로 바뀌는데 **`outerHTML` 의 `value="초기값"` 은 한 글자도 안 바뀐다.**\
> 이어서 **`setAttribute` 로 바꾸기**를 누르면 반대가 된다 — **`outerHTML` 만 `value="속성에 쓴 것"` 으로 바뀌고 입력칸에 보이는 글자는 그대로**다.\
> **바꿔 볼 것** — 두 버튼의 **순서를 바꿔** 눌러 보라(아직 `.value` 를 안 만졌을 때는 `setAttribute` 가 화면까지 바꾼다 — 위 (4)의 「아직 안 갈렸다」 줄이다) · 입력칸에 **직접 타이핑한 뒤** `setAttribute` 를 눌러 보라(사용자 조작도 같은 플래그를 세운다).

*(Chrome 151 headless 실측: 버튼을 순서대로 눌러 `outerHTML` 이 `<input id="d6in" value="초기값">` → **그대로** → `<input id="d6in" value="속성에 쓴 것">` 으로, `.value` 가 `초기값` → `스크립트가 넣은 것` → **그대로** 로 갈리는 것을 확인했다)*

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
el.getAttribute('name')        // 글자열 또는 null
el.setAttribute('name', 'v')   // 값은 글자열로 변환된다
el.removeAttribute('name')
el.hasAttribute('name')        // 불리언
el.toggleAttribute('name')     // 있으면 빼고 없으면 넣는다
el.getAttributeNames()         // 이름 배열
el.attributes                  // NamedNodeMap — 라이브다

el.id  el.title  el.hidden     // 꼴 ① 이름이 같은 반영
el.className  label.htmlFor    // 꼴 ② 이름이 다른 반영
input.value  input.checked     // 꼴 ③ 반영이 아니다 (별도 상태)
input.defaultValue             //      이쪽이 value 속성의 반영이다
input.defaultChecked           //      이쪽이 checked 속성의 반영이다
a.href  img.src                // 꼴 ④ URL 로 푸는 반영
el.dataset                     // 반영이 아니라 별도 표면 (07번 주제)
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// 1. 체크박스를 켜려고 속성을 쓴다 — 아무 일도 안 난다
ck.setAttribute('checked', 'checked');    // .checked 는 그대로
ck.checked = true;                        // 이것이 맞다

// 2. 체크 해제하려고 속성 값을 false 로 준다 — 켜진다
ck.setAttribute('checked', 'false');      // 불리언 속성은 '있느냐'만 본다

// 3. 사용자가 친 값을 속성으로 읽는다 — 초기값이 나온다
const v = inp.getAttribute('value');      // 언제나 초기값
const v2 = inp.value;                     // 이것이 맞다

// 4. 오타 난 성질에 쓴다 — 조용히 프로퍼티 하나가 생긴다
el.classname = 'card';                    // 예외 없음, 아무 일도 안 난다

// 5. 링크의 원문이 필요한데 프로퍼티를 읽는다 — 절대 URL 이 온다
if (a.href === 'sub/page.html') { }       // 영영 거짓
if (a.getAttribute('href') === 'sub/page.html') { }   // 이것이 맞다

// 6. 없는 속성을 빈 문자열과 비교한다
if (el.getAttribute('title') === '') { }  // null 이라 거짓
if (!el.hasAttribute('title')) { }        // 이것이 맞다
```

### 어디서 헷갈리나

- **「속성」이라는 말이 두 가지를 가리킨다.** 한국어로는 마크업의 attribute 도 「속성」, 객체의 property 도 「속성」이다. 이 문서는 뒤엣것을 「**성질**」로 적어 갈랐다. 명세 용어로는 **content attribute** 와 **IDL attribute** 다.
- **`value` 라는 이름이 세 군데 있다** — `value` 속성 · `.value` 성질 · `.defaultValue` 성질. **속성과 이어진 것은 세 번째**다.
- **`el.attributes` 는 라이브다.** 순회하면서 지우면 [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 라이브 컬렉션 사고가 그대로 난다.

## 어디서 틀리나

### 1. `input.value` 를 속성으로 읽는다

사용자가 무엇을 쳤는지 알고 싶은데 `getAttribute('value')` 를 읽어 **언제나 초기값**을 받는다. `--dump-dom` 으로 확인해도 초기값이 나오므로 **증거가 오진을 확인해 준다.**

### 2. 체크박스를 속성으로 켜고 끈다

`setAttribute('checked', …)` 는 `defaultChecked` 만 바꾼다. 실측에서 `setAttribute('checked','checked')` 뒤에도 `.checked` 가 **`false`** 였다. 반대로 `removeAttribute('checked')` 도 켜진 체크를 못 끈다.

### 3. `innerHTML` 로 DOM 을 복사·저장한다

폼 상태·스크롤·미디어 재생 위치처럼 **성질에만 있는 것**이 전부 사라진다. 실측에서 `innerHTML` 왕복만 `"초기"` 를 돌려줬고 `cloneNode`·`importNode` 는 사용자 값을 지켰다.

### 4. 성질 이름의 오타가 조용히 지나간다

`el.classname`·`el.tabindex`(소문자 i)·`el.readonly` 는 **에러 없이 그냥 프로퍼티를 만든다.** 창 ④ 로 `outerHTML` 을 찍어 **속성이 안 생겼다**를 확인하는 것이 유일한 진단이다.

### 5. `null` 과 `""` 를 같게 본다

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-06-four.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '39,45p'
없는 속성을 물으면 — 「빈 값」이 프로퍼티 타입마다 다르다
getAttribute('id')          null                    el.id = ""
getAttribute('class')       null                    el.className = ""
getAttribute('title')       null                    el.title = ""
getAttribute('tabindex')    null                    el.tabIndex = -1
getAttribute('hidden')      null                    el.hidden = false
getAttribute('data-x')      null                    el.dataset.x = undefined
(exit 0)
```

없는 속성에 대해 **`getAttribute` 는 `null`** 인데 프로퍼티는 타입마다 **`""`·`false`·`-1`·`undefined`** 로 제각각이다. `if (el.getAttribute('x'))` 와 `if (el.x)` 는 **다른 것을 묻는 문장**이다.

### 6. 반영이 「늘 대칭」이라고 믿는다

`type`·`maxlength` 처럼 **속성에 담긴 글자와 프로퍼티가 영영 어긋나는** 자리가 있다. 실측에서 속성 `"bogus"` 옆에 프로퍼티 `"text"` 가 나란히 있었다. **명세가 「알려진 값만」이라고 정했기 때문**이지 브라우저가 고친 것이 아니다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 어떤 IDL 프로퍼티가 어떤 속성을 반영하는가 | **명세**(HTML — 요소마다 정의에 적혀 있다) |
| 반영의 종류(글자열·불리언·URL 로 풀기·알려진 값만·정수) | **명세**(HTML 「Reflecting content attributes」 절) |
| `value`·`checked` 가 반영이 아니고 `defaultValue`·`defaultChecked` 가 반영인 것 | **명세**(HTML `input` 절 — dirty value flag / dirty checkedness flag) |
| `form.reset()` 이 `.value` 를 `defaultValue` 로 되돌리는 것 | **명세**(HTML 폼 리셋 알고리즘) |
| `cloneNode` 가 입력 값·체크 상태를 함께 옮기는 것 | **명세**(HTML `input` 의 cloning steps) |
| 없는 속성에 `getAttribute` 가 `null` 을 주는 것 | **명세**(DOM) |
| HTML 문서에서 속성 이름이 소문자로 맞춰지는 것 | **명세**(DOM `setAttribute`) — 실측 근거는 HTML 갈래 **02번** |
| `--dump-dom` 의 직렬화 형태(속성 순서·따옴표·`checked=""`) | **명세**(HTML 직렬화) **+ 구현**(줄바꿈 위치) |
| `.maxLength` 가 음수 입력에서 `-1` 인 것 | **명세**(기본값이 `-1` 인 제한된 정수 반영) |

- ★ **이 주제는 표가 구현 쪽으로 거의 안 기운다.** 반영은 **계약**이고, 그래서 다른 엔진에서도 같아야 한다 — 다만 **이 문서는 Chrome 하나로만 확인했으므로 「같았다」는 말은 하지 않는다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 사용자가 친 값을 읽는다 | `inp.value` | `getAttribute('value')` |
| 초기값을 읽거나 고친다 | `inp.defaultValue` · `setAttribute('value', …)` | `inp.value` |
| 체크를 켜고 끈다 | `ck.checked = …` | `setAttribute('checked', …)` |
| 링크가 실제로 갈 곳 | `a.href` | `getAttribute('href')` |
| 마크업에 적힌 원문 | `a.getAttribute('href')` | `a.href` |
| 불리언 속성의 유무 판정 | `el.hasAttribute` · 반영 성질 | 속성 **값** 비교 |
| `data-*` | [`el.dataset`](../07-dataset-classlist-inline-style/2-summary.md) | `getAttribute('data-…')` 도 되지만 이름을 손으로 쓴다 |
| `class` 조작 | [`el.classList`](../07-dataset-classlist-inline-style/2-summary.md) | `el.className` 문자열 붙이기 |
| 표준에 없는 내 정보 | `data-*` 또는 `WeakMap` | `el.myThing = …`(expando — 직렬화에 안 남고 충돌 위험) |
| DOM 을 복사해 상태까지 지킨다 | `cloneNode(true)` | `innerHTML` 왕복 |

## 핵심 문장

1. **요소에는 칸이 두 벌 있다** — 마크업의 **속성**(언제나 글자열)과 객체의 **성질**(타입이 있다).
2. **둘을 잇는 배선은 「반영」이고, 그것은 명세가 속성마다 못 박은 계약이다.** 구현 사정이 아니다.
3. **배선은 네 꼴이다** — 그대로 · 이름만 다름 · 한쪽으로만 · 지나가며 풀림. 그리고 **배선이 아예 없는 이름**이 넷보다 많다.
4. **`value`·`checked` 는 반영이 아니다.** 속성을 반영하는 것은 `defaultValue`·`defaultChecked` 이고, `form.reset()` 이 둘을 다시 잇는다.
5. **성질에만 있는 상태는 글자로 안 나온다** — `innerHTML` 왕복은 잃고 `cloneNode` 는 지킨다.
6. **없는 것을 물으면 두 창구의 대답이 다르다** — 속성은 `null`, 성질은 타입마다 `""`·`false`·`-1`.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 06번)
- [01번 주제](../01-document-and-node-tree/2-summary.md) — 노드와 요소. **`Attr` 도 노드라는 것**과 `el.attributes` 가 거기에 있다
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md) — **`el.attributes` 는 라이브 컬렉션**이다. 순회 중 삭제 사고는 그쪽이 정본
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) — `innerHTML` 이 **무엇을 글자로 뽑나**. 여기는 **그 글자에 무엇이 안 실리나**부터
- [05번 주제](../05-documentfragment-and-template/2-summary.md) — `cloneNode`·`importNode`. 여기는 **그 복제가 폼 상태를 가져오는가**만 얹는다
- [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)(`dataset`·`classList`·인라인 `style`) — **`data-*` 와 `class` 를 실제로 다루는 표면.** 이 주제는 「반영이 아니다」까지만 말하고 넘긴다
- 목록의 **45번 주제**(`URL`·`URLSearchParams`) — 꼴 ④ 가 푸는 **URL 규칙 자체**는 그쪽
- 목록의 **60번 주제**(제약 검증 API) — `value` 위에 얹히는 검증 상태
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번**([요소와 속성 문법](../../languages/html/syntax/02-elements-and-attributes/2-summary.md)) — **속성이 트리에 어떤 글자로 담기나의 정본.** 소문자화·중복 속성 버리기·불리언의 존재 판정·따옴표 경계는 전부 거기다. 여기는 **담긴 뒤**부터
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **06번**(전역 속성) — `data-*` 의 **마크업 쪽** 정본. 여기는 **`dataset` 이라는 API 표면**만
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **30번**(폼 상태·입력 보조 속성) — `disabled`·`readonly` 가 **무엇을 바꾸나**는 그쪽

## 용어 풀이

- **콘텐츠 속성(content attribute)** — 마크업에 쓰인 속성 그 자체. `getAttribute`·`setAttribute` 가 다룬다. **값은 언제나 글자열**이다.
- **IDL 속성(IDL attribute) · 성질** — `el.checked` 처럼 DOM 객체에 달린 프로퍼티. **타입이 있다.** 이 문서는 한국어 혼동을 피해 「**성질**」로 적었다.
- **반영(reflect)** — 명세가 「이 IDL 프로퍼티는 저 콘텐츠 속성과 이어진다」고 못 박은 것. **양방향이 기본**이고 종류가 여럿이다.
- **URL 로 푸는 반영** — 읽을 때 문서의 base 로 절대 URL 을 만들어 주는 반영. `a.href`·`img.src`.
- **알려진 값만 받는 반영(limited to only known values)** — 모르는 값이면 기본값을 답하는 반영. `input.type`.
- **dirty value flag** — 사용자나 스크립트가 `.value` 를 한 번이라도 바꿨음을 표시하는 명세의 플래그. 이것이 서면 `value` 속성 변경이 `.value` 에 안 온다.
- **dirty checkedness flag** — 위의 체크 상태판.
- **`defaultValue` · `defaultChecked`** — `value`·`checked` **속성을 반영하는** 성질. 「초기값」이다.
- **expando** — 표준에 없는데 스크립트가 객체에 그냥 붙인 프로퍼티. 속성을 만들지 않고 직렬화에도 안 남는다.
- **직렬화(serialize)** — 노드 트리를 HTML 글자열로 뽑는 것. `outerHTML`·`--dump-dom`.
- **`NamedNodeMap`** — `el.attributes` 의 타입. 이름으로 찾는 **라이브** 컬렉션이다.
- **불리언 속성(boolean attribute)** — 있으면 참, 없으면 거짓인 속성. **값은 무관**하다(정본: HTML 갈래 **02번**).

## 더 들어가면

- **`Attr` 도 노드다.** `el.attributes[0]` 은 `Attr` 노드이고 `nodeType` 이 2 다. 예전에는 자식 노드를 가질 수 있었지만 오늘 명세에서는 **값이 글자열 하나**로 단순해졌다. `getAttributeNode`·`setAttributeNode` 는 아직 있지만 쓸 일이 거의 없다.
- **이름공간이 붙은 속성**(`getAttributeNS`)은 SVG·MathML 이 섞인 문서에서만 필요하다. HTML 요소의 속성은 이름공간이 없다.
- **`toggleAttribute(name, force)`** 는 [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 `classList.toggle` 과 **같은 모양의 두 번째 인자**를 갖는다. 불리언 속성을 켜고 끌 때 `setAttribute`/`removeAttribute` 를 갈라 쓰는 것보다 짧다.
- **커스텀 요소**는 반영을 **직접 구현**한다 — `observedAttributes` + `attributeChangedCallback` 으로 속성 쪽을, getter/setter 로 성질 쪽을 짜고 **두 방향이 무한히 되부르지 않게** 막아야 한다. 그 설계가 목록의 **13번 주제**다.
- **`el.attributes` 의 순서**는 「설정된 순서」다. 실측에서 나중에 `setAttribute` 한 것이 **뒤에 붙었다**(위 (6)의 `outerHTML`). 명세가 순서를 보장하지만 **의미 있는 정보로 쓰지는 마라** — 마크업 작성 순서와 스크립트 조작이 섞인다.
