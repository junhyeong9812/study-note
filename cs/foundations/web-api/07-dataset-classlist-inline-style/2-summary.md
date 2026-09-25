# web-api/07 — `dataset`·`classList`·인라인 `style`: 스크립트가 만지는 세 표면 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 언어 문법은 [`../../languages/`](../../languages/) 에 있고, 여기는 **브라우저가 건네주는 객체와 그 계약**이다.\
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/dom.html#dom-dataset) 의 「`dataset`」 절과 [WHATWG DOM Standard](https://dom.spec.whatwg.org/#interface-domtokenlist) 의 「Interface `DOMTokenList`」 절, [CSSOM](https://drafts.csswg.org/cssom/#the-elementcssinlinestyle-interface) 의 「`ElementCSSInlineStyle`」·「`CSSStyleDeclaration`」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `classList` 와 `dataset` 은 HTML5 가 들여왔고 `el.style` 은 DOM Level 2 Style(2000) 부터 있었다.\
> **선행** — [06번 주제](../06-attribute-vs-property/2-summary.md)(속성 대 성질). 거기서 「**`data-*` 와 `class` 는 반영이 아니다**」까지 봤고, 여기는 **그럼 무엇이냐**부터다.\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 없다.** 수치를 재지 않기 때문이다 — 시간도, 크기도 없다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 속성 이름과 값 · `dataset` 키 목록과 순서 · `classList` 반환값과 `length` · `style.length` 와 `item(i)` 목록 · 예외 이름 · 직렬화 문자열 | 전부 명세가 절차로 정한 결과다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 단축 속성이 **몇 개의 낱개로 풀리나**(`background` → 10)는 **명세가 정한 낱개 목록**이라 흔들리지 않는다. 다만 **명세에 낱개가 더해지면 바뀐다** — 그래서 아래 (8) 에 「판을 적고 다시 찍어라」를 달아 두었다.
- 그래서 제출 전 재대조에서 **정규화할 칸이 하나도 없다.**

## 한눈에 — 쉽게 말하면

**★ 셋 다 속성 하나를 보는 「전용 리모컨」이다. 본체에 있는 것은 여전히 글자열 한 줄뿐이다.**

텔레비전에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 본체 뒤의 **단자와 라벨** | `class="a b"` · `style="color:red"` · `data-foo-bar="7"` — **글자열 한 줄** |
| **전용 리모컨 셋** | `classList` · `el.style` · `dataset` |
| 리모컨을 누르면 **라벨이 통째로 다시 쓰인다** | 정규화 — `class` 의 여분 공백이 그때 정리된다 |
| 리모컨에 **없는 버튼**을 누르면 | 아무 일도 안 난다 — **조용히 버려짐**(`style.color='bogus'`) |
| 리모컨이 **못 받는 값**을 넣으면 | **삑** — 예외(`classList.add('두 칸')`) |
| 리모컨 이름과 라벨 이름의 **표기가 다르다** | `data-foo-bar` ↔ `dataset.fooBar` |
| 한 버튼이 **여러 단자를 한꺼번에** 건드린다 | 단축 속성 — `style.background` 하나가 낱개 10개로 풀린다 |
| 리모컨은 **본체 라벨만** 본다 | `el.style` 은 스타일시트를 못 본다 — 그 창은 [08번 주제](../08-getcomputedstyle/2-summary.md) |

- **셋은 서로 다른 세 가지가 아니라 「속성 칸을 보는 세 창**」이다. 그래서 진단도 하나로 통한다 — **쓰고 나서 속성을 되읽어라.**
- **실패 방식이 셋이다** — 담겼다 / **조용히 버려졌다** / 예외. 가운데 것이 가장 나쁘고, 그것만 보는 창이 이 주제의 창 ④ 다.

```text
                  요소 하나
   ┌───────────────────────────────────────────────┐
   │  class="a b"        style="color:red"   data-foo-bar="7"   │
   └───────┬───────────────────┬────────────────────┬──────────┘
           │                   │                    │
      classList            el.style              dataset
   ["a","b"] 목록      선언 목록 (length=1)    {fooBar:"7"} 객체
   add/remove/          setProperty/           키 대입/ delete
   toggle/replace/      getPropertyValue/
   contains             cssText
```

## 이 주제가 답하려는 질문

1. **`data-foo-bar` 가 `dataset.fooBar` 가 되는 규칙은 정확히 무엇인가.** 그리고 **대문자를 섞어 쓰면** 어떻게 되나.
2. **`classList.toggle` 의 두 번째 인자는 무엇을 바꾸나.** 그리고 다섯 메서드 중 **무엇이 값을 돌려주나**.
3. **잘못 쓴 스타일 선언은 어디로 가나** — 예외인가, 조용히 사라지나. **무엇으로 가르나.**

## 이 갈래의 관측 창 — ★ 창 4 는 「담겼나」

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom             스크립트가 다 돈 뒤의 트리를 글자로
  창 2  노드 단위 프로브        getAttribute / 세 표면의 값을 같은 줄에
  창 3  두 번 읽기              쓰기 전 / 쓴 뒤를 같은 프로브로
  ★ 창 4 (이 주제 고유)  '담겼나' — 쓴 자리에서 곧바로 되읽어 세 갈래로 가른다
        담겼다           되읽은 값이 바뀌었다
        조용히 버려졌다  되읽은 값이 그대로다 · 예외도 없다   ★ 이것만 눈에 안 보인다
        예외             이름과 메시지가 나온다
```

- ★ **이 창은 CSS 갈래에서 왔다.** 거기서는 `cssRules`(담겼나) → `querySelectorAll`(잡혔나) → `getComputedStyle`(이겼나) 셋으로 갈랐다(정본: [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)). **CSS 는 에러가 없는 언어**라 무효한 선언이 조용히 버려지는데, **`el.style` 은 그 CSS 문법을 그대로 쓰는 표면**이라 같은 성질을 물려받는다.
- **창 1\~3 으로는 「조용히 버려짐」을 못 가른다.** 값이 안 바뀐 것과 원래 그 값이었던 것이 같아 보이기 때문이다. **쓰기 직전의 값을 잡아 두고 대조**해야 갈린다 — 그것이 창 ④ 가 하는 일이다.
- **세 표면의 실패 방식이 서로 다르다**는 것이 이 주제의 결론 하나다. `dataset` 과 `classList` 는 **예외를 던지는 자리**가 있고 `el.style` 은 **거의 전부 조용하다.**

## 동작 방식

### (1) 셋 다 속성 칸을 보는 창이다 — 창 ① 로 먼저 확인한다

**언제 쓰나** — 세 표면 중 무엇을 쓸지 고르기 전에. **셋이 같은 곳을 본다**는 것부터 확인한다.

```html
<!-- wa06b-07-tree.html -->
<!doctype html>
<meta charset="utf-8">
<title>07-tree</title>
<div id="t" class="a b" data-keep="지킨다" style="color: red"></div>
<script>
  const t = document.getElementById('t');
  t.dataset.newKey = '새로 쓴 것';
  t.classList.add('c');
  t.classList.toggle('a');
  t.style.fontWeight = 'bold';
  t.style.color = 'bogus';
  t.style.background = 'blue';
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-tree.html | sed -n '4p'
</head><body><div id="t" class="b c" data-keep="지킨다" style="color: red; font-weight: bold; background: blue;" data-new-key="새로 쓴 것"></div>
(exit 0)
```

- `dataset.newKey = …` 가 **`data-new-key="새로 쓴 것"` 속성을 만들었다.** 그리고 **속성 목록의 맨 뒤에 붙었다** — 나중에 설정된 순서다.
- `classList.add('c')` 와 `classList.toggle('a')` 를 거쳐 **`class="b c"`** 가 됐다.
- `style.fontWeight`·`style.background` 는 **`style` 속성 문자열에 이어 붙었고**, ★ **`style.color = 'bogus'` 는 흔적이 없다** — 원래 있던 `color: red` 가 그대로다.
- **창 ① 만 보면 마지막 것이 「안 썼다」인지 「쓰려다 버려졌다」인지 모른다.** 그래서 창 ④ 가 필요하다.

비용 — 없다. 다만 **세 표면을 쓰면 속성 문자열이 통째로 다시 쓰인다**는 것은 알고 있어야 한다(아래 (5)의 정규화).

### (2) `dataset` — 읽는 쪽: 케밥에서 카멜로

**언제 쓰나** — 마크업에 심어 둔 값을 스크립트로 꺼낼 때.

**던진 것** — 아래 (3)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa06b-07-dataset.html -->
<!doctype html>
<meta charset="utf-8">
<title>07-dataset</title>
<div id="m" data-foo-bar="케밥" data-fooBar="소스에 대문자" data-x="짧은 것" data-="이름이 빈 것" data-1-2="숫자"></div>
<div id="w"></div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push(padw(a, 26) + padw(b, 30) + (c === undefined ? '' : c));
const m = document.getElementById('m'), w = document.getElementById('w');

O.push('마크업 -> 속성 -> dataset  (읽는 쪽)');
row('소스에 쓴 것', '트리의 속성 이름', 'dataset 키');
for (const a of m.attributes) if (a.name !== 'id') row('', J(a.name), J(a.value));
row('', 'Object.keys(dataset)', J(Object.keys(m.dataset)));
row('', 'dataset.fooBar', J(m.dataset.fooBar));
row('', 'dataset.foobar', J(m.dataset.foobar));
row('', "dataset['1-2'] · ['12']", J(m.dataset['1-2']) + ' / ' + J(m.dataset['12']));
row('', 'dataset 객체 동일성', String(m.dataset === m.dataset));
O.push('');

O.push('dataset -> 속성  (쓰는 쪽) — 창 ④ 「담겼나」 왕복');
row('dataset 에 쓴 이름', '생긴 속성 이름 · 또는 예외', '되읽기');
const 써보기 = (key, val) => {
  const before = new Set([...w.attributes].map(a => a.name));
  let 결과;
  try { w.dataset[key] = val; 결과 = null; }
  catch (e) { 결과 = e.name; }
  if (결과) { row('dataset[' + J(key) + ']', '예외 ' + 결과, '속성이 안 생긴다'); return; }
  const 새것 = [...w.attributes].map(a => a.name).filter(n => !before.has(n));
  row('dataset[' + J(key) + ']', J(새것.join(',') || '(이미 있던 것)'), J(w.dataset[key]));
};
써보기('foo', 'a');
써보기('fooBar', 'b');
써보기('fooBAR', 'c');
써보기('a1B2', 'd');
써보기('foo-bar', 'e');
써보기('foo-Bar', 'f');
써보기('', 'g');
O.push('');

O.push('지우기와 최종 상태');
row('w.outerHTML', J(w.outerHTML));
delete w.dataset.foo;
row("delete w.dataset.foo 뒤", J(w.getAttribute('data-foo')), 'w.outerHTML 길이 = ' + w.outerHTML.length);
w.setAttribute('data-Late-Add', 'h');
row("setAttr('data-Late-Add')", J([...w.attributes].map(a => a.name).filter(n => n.includes('late'))),
    'dataset.lateAdd = ' + J(w.dataset.lateAdd));
row('', 'dataset.LateAdd / lateadd', J(w.dataset.LateAdd) + ' / ' + J(w.dataset.lateadd));
row('최종 Object.keys(dataset)', J(Object.keys(w.dataset)));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-dataset.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
마크업 -> 속성 -> dataset  (읽는 쪽)
소스에 쓴 것              트리의 속성 이름              dataset 키
                          "data-foo-bar"                "케밥"
                          "data-foobar"                 "소스에 대문자"
                          "data-x"                      "짧은 것"
                          "data-"                       "이름이 빈 것"
                          "data-1-2"                    "숫자"
                          Object.keys(dataset)          ["fooBar","foobar","x","","1-2"]
                          dataset.fooBar                "케밥"
                          dataset.foobar                "소스에 대문자"
                          dataset['1-2'] · ['12']       "숫자" / undefined
                          dataset 객체 동일성           true
(exit 0)
```

**규칙은 이렇다.**

```text
   속성 이름                  dataset 키
   data-foo-bar    ──────>    fooBar      'data-' 를 떼고, '-소문자' 를 대문자로
   data-x          ──────>    x
   data-           ──────>    ''          (빈 이름도 된다)
   data-1-2        ──────>    '1-2'       ★ '-숫자' 는 안 바꾼다. 점 표기로는 못 읽는다
   data-fooBar     ──────>    foobar      ★ 마크업의 대문자는 파서가 이미 소문자로 만들었다
       (소스에 대문자를 써도 트리에는 data-foobar 로 담긴다)
```

- **`-` 다음이 ASCII 소문자일 때만** 그 소문자를 대문자로 바꾸고 `-` 를 지운다. `data-1-2` 는 **`-` 다음이 숫자**라 그대로 남아 `dataset['1-2']` 로만 읽힌다.
- ★ **마크업에 `data-fooBar` 라고 써도 소용없다.** HTML 파서가 속성 이름을 **소문자로 맞추므로** 트리에는 `data-foobar` 가 담기고 키도 `foobar` 다(그 규칙의 정본은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번**).
- **`el.dataset` 은 부를 때마다 같은 객체**다(`m.dataset === m.dataset` 이 `true`). 그러나 **값은 라이브**다 — 속성을 나중에 바꿔도 따라온다((3) 마지막 줄).

비용 — `getAttribute('data-foo-bar')` 와 같은 일이다. 이름을 손으로 안 써도 되는 것이 값어치다.

### (3) `dataset` — 쓰는 쪽: 카멜에서 케밥으로, 그리고 ★ 대문자가 들어가면

**언제 쓰나** — 스크립트가 만든 값을 마크업에 심을 때. **여기가 이 표면의 함정**이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-dataset.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,22p'
dataset -> 속성  (쓰는 쪽) — 창 ④ 「담겼나」 왕복
dataset 에 쓴 이름        생긴 속성 이름 · 또는 예외    되읽기
dataset["foo"]            "data-foo"                    "a"
dataset["fooBar"]         "data-foo-bar"                "b"
dataset["fooBAR"]         "data-foo-b-a-r"              "c"
dataset["a1B2"]           "data-a1-b2"                  "d"
dataset["foo-bar"]        예외 SyntaxError              속성이 안 생긴다
dataset["foo-Bar"]        "data-foo--bar"               "f"
dataset[""]               "data-"                       "g"
(exit 0)
```

```text
   dataset 키          만들어지는 속성 이름
   foo        ──────>  data-foo
   fooBar     ──────>  data-foo-bar       대문자 하나 = '-소문자' 하나
   fooBAR     ──────>  data-foo-b-a-r     ★ 대문자마다 각각 '-' 가 붙는다
   a1B2       ──────>  data-a1-b2
   foo-Bar    ──────>  data-foo--bar      ★ '-' 는 그대로 두고 'B' 가 '-b' 를 더한다
   ''         ──────>  data-
   foo-bar    ──────>  ✗ SyntaxError      ★ '-' 다음이 소문자면 던진다
```

- **변환은 「대문자를 `-소문자` 로 바꾼다」 한 줄**이다. 그래서 **연속된 대문자마다 각각 `-` 가 붙어** `fooBAR` 가 `data-foo-b-a-r` 이 된다 — **읽기 규칙의 역이 아니다.**
- ★ **`foo-bar` 만 예외로 던진다.** 명세가 「키에 `-` 다음이 ASCII 소문자면 `SyntaxError`」라고 못 박았다. **왕복이 깨지는 것을 막으려는 것**이다 — 그대로 두면 `data-foo-bar` 가 되어 **`fooBar` 와 같은 속성을 두 키가 가리키게** 된다.
- **`foo-Bar` 는 안 던진다.** `-` 다음이 대문자라 그 규칙에 안 걸리고, 결과는 `data-foo--bar` 라는 **`-` 가 둘인 이상한 이름**이다. 던지지 않는 쪽이 더 나쁘다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-dataset.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,29p'
지우기와 최종 상태
w.outerHTML               "<div id=\"w\" data-foo=\"a\" data-foo-bar=\"b\" data-foo-b-a-r=\"c\" data-a1-b2=\"d\" data-foo--bar=\"f\" data-=\"g\"></div>"
delete w.dataset.foo 뒤   null                          w.outerHTML 길이 = 97
setAttr('data-Late-Add')  ["data-late-add"]             dataset.lateAdd = "h"
                          dataset.LateAdd / lateadd     undefined / undefined
최종 Object.keys(dataset) ["fooBar","fooBAR","a1B2","foo-Bar","","lateAdd"]
(exit 0)
```

- **`delete el.dataset.foo` 가 속성을 지운다**(`getAttribute('data-foo')` 가 `null`).
- ★ **나중에 `setAttribute('data-Late-Add', …)` 로 대문자를 써도** 트리에는 `data-late-add` 로 담기고(DOM 이 이름을 소문자로 맞춘다) 키는 **`lateAdd`** 다. `dataset.LateAdd`·`dataset.lateadd` 는 **둘 다 `undefined`** 다.
- 마지막 줄의 키 목록이 이 절의 요약이다 — **`fooBAR`·`a1B2`·`foo-Bar` 가 그대로 키로 돌아왔다.** 왕복이 되는 것은 **`-` 를 안 쓰고 대문자가 연속되지 않는 이름**뿐이다.

비용 — 없다. 다만 **이름을 정할 때 케밥 쪽에서 시작하라** — `data-user-id` → `userId` 는 안전하고, `userID` → `data-user-i-d` 는 아니다.

### (4) `classList` — 다섯 메서드와 ★ `toggle` 의 두 번째 인자

**언제 쓰나** — 상태를 클래스로 표현할 때. **이 주제에서 가장 자주 쓰는 표면**이다.

**던진 것** — 아래 (5)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa06b-07-classlist.html -->
<!doctype html>
<meta charset="utf-8">
<title>07-classlist</title>
<div id="c" class="a b"></div>
<div id="s" class="  두   칸   띄움  "></div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push((padw(a, 30) + padw(b, 28) + (c === undefined ? '' : c)).replace(/ +$/, ''));
const c = document.getElementById('c'), cl = c.classList;

O.push('연산마다 class 속성이 어떻게 되나 — 왼쪽을 부르고 오른쪽을 되읽었다');
row('연산', "getAttribute('class')", '반환값 · length');
row('처음', J(c.getAttribute('class')), 'length = ' + cl.length);
const 해보기 = (label, fn) => { const r = fn(); row(label, J(c.getAttribute('class')),
  (r === undefined ? '(undefined)' : String(r)) + '   length = ' + cl.length); };
해보기("add('c')", () => cl.add('c'));
해보기("add('a') 이미 있는 것", () => cl.add('a'));
해보기("add('d','e') 여러 개", () => cl.add('d', 'e'));
해보기("remove('zz') 없는 것", () => cl.remove('zz'));
해보기("remove('d','e')", () => cl.remove('d', 'e'));
해보기("toggle('a')", () => cl.toggle('a'));
해보기("toggle('a') 다시", () => cl.toggle('a'));
해보기("toggle('a', true)", () => cl.toggle('a', true));
해보기("toggle('a', true) 다시", () => cl.toggle('a', true));
해보기("toggle('a', false)", () => cl.toggle('a', false));
해보기("replace('b','q')", () => cl.replace('b', 'q'));
해보기("replace('nope','r')", () => cl.replace('nope', 'r'));
해보기("contains('q')", () => cl.contains('q'));
O.push('');

O.push('예외와 경계 — 창 ④ 「담겼나」 세 갈래로 가른다');
row('연산', '결과', "되읽은 getAttribute('class')");
const 던져보기 = (label, fn) => {
  const 전 = c.getAttribute('class');
  try { const r = fn(); row(label, '담김   반환 ' + String(r), J(c.getAttribute('class'))); }
  catch (e) { row(label, '예외 ' + e.name, J(c.getAttribute('class')) + (c.getAttribute('class') === 전 ? '  (안 바뀜)' : '')); }
};
던져보기("add('두 칸')", () => cl.add('두 칸'));
던져보기("add('')", () => cl.add(''));
던져보기("cl.value = 'x  y'", () => { cl.value = 'x  y'; return cl.length; });
던져보기("className = '가 나 가'", () => { c.className = '가 나 가'; return cl.length; });
던져보기("cl.supports('가')", () => cl.supports('가'));
O.push('');

O.push('잡아 둔 classList 는 라이브인가 · 공백은 어떻게 되나');
row('c.classList === c.classList', String(c.classList === cl));
c.setAttribute('class', 'z1 z2 z3');
row('setAttribute 로 갈아 끼운 뒤', '잡아 둔 cl.length = ' + cl.length, J([...cl]));
const s = document.getElementById('s');
row('소스의 class 속성', J(s.getAttribute('class')));
row('classList 로 보면', 'length = ' + s.classList.length, J([...s.classList]));
row('classList.value', J(s.classList.value), '(속성 원문 그대로다)');
s.classList.add('끝');
row("add('끝') 뒤 속성", J(s.getAttribute('class')), '(그때 정규화된다)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-classlist.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,16p'
연산마다 class 속성이 어떻게 되나 — 왼쪽을 부르고 오른쪽을 되읽었다
연산                          getAttribute('class')       반환값 · length
처음                          "a b"                       length = 2
add('c')                      "a b c"                     (undefined)   length = 3
add('a') 이미 있는 것         "a b c"                     (undefined)   length = 3
add('d','e') 여러 개          "a b c d e"                 (undefined)   length = 5
remove('zz') 없는 것          "a b c d e"                 (undefined)   length = 5
remove('d','e')               "a b c"                     (undefined)   length = 3
toggle('a')                   "b c"                       false   length = 2
toggle('a') 다시              "b c a"                     true   length = 3
toggle('a', true)             "b c a"                     true   length = 3
toggle('a', true) 다시        "b c a"                     true   length = 3
toggle('a', false)            "b c"                       false   length = 2
replace('b','q')              "q c"                       true   length = 2
replace('nope','r')           "q c"                       false   length = 2
contains('q')                 "q c"                       true   length = 2
(exit 0)
```

- **`add`·`remove` 는 `undefined` 를 돌려준다.** 여러 개를 한 번에 받고(`add('d','e')`), **이미 있는 것을 더하거나 없는 것을 빼도 조용하다** — 에러가 아니라 「할 일 없음」이다.
- **`toggle`·`replace`·`contains` 는 값을 돌려준다** — `toggle` 은 **그 뒤의 유무**(불리언), `replace` 는 **바꿨는가**, `contains` 는 **있는가**.
- ★ **`toggle(name, force)` 의 두 번째 인자는 「뒤집기」를 「강제」로 바꾼다.**

```text
   toggle('a')           있으면 빼고 없으면 넣는다      -> 반환은 '그 뒤에 있나'
   toggle('a', true)     언제나 넣는다   (= add)        -> 언제나 true
   toggle('a', false)    언제나 뺀다     (= remove)     -> 언제나 false
```

- 실측에서 **`toggle('a', true)` 를 두 번 불러도 결과가 안 바뀌었다**(멱등). `toggle('a')` 는 두 번 부르면 원상복구된다.
- **왜 있나** — 조건을 코드로 갈라 쓰지 않기 위해서다. `el.classList.toggle('on', 조건)` 한 줄이 `if (조건) add else remove` 를 대신한다.
- **`replace('nope','r')` 는 `false` 를 돌려주고 아무 일도 안 한다.** 없는 것을 바꾸라고 해도 새로 넣지 않는다.

비용 — 메서드 하나가 **`class` 속성 문자열을 통째로 다시 쓴다.** 낱개로 쪼개져 저장되는 것이 아니다.

### (5) `classList` — 예외·공백·정규화

**언제 쓰나** — 클래스 이름이 사용자 입력이나 외부 데이터에서 올 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-classlist.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '18,24p'
예외와 경계 — 창 ④ 「담겼나」 세 갈래로 가른다
연산                          결과                        되읽은 getAttribute('class')
add('두 칸')                  예외 InvalidCharacterError  "q c"  (안 바뀜)
add('')                       예외 SyntaxError            "q c"  (안 바뀜)
cl.value = 'x  y'             담김   반환 2               "x  y"
className = '가 나 가'        담김   반환 2               "가 나 가"
cl.supports('가')             예외 TypeError              "가 나 가"  (안 바뀜)
(exit 0)
```

- **공백이 든 토큰은 `InvalidCharacterError`**, **빈 토큰은 `SyntaxError`** 다. **둘 다 속성이 안 바뀐다** — 되읽은 값이 그대로다(「안 바뀜」).
- ★ **`classList.value` 나 `className` 으로 쓰면 그 검사를 통째로 건너뛴다.** `cl.value = 'x  y'` 는 예외 없이 **공백 둘짜리 문자열을 그대로** 속성에 넣는다. **메서드만 검사하고 문자열 대입은 검사하지 않는다.**
- `classList.supports` 는 `DOMTokenList` 에 있지만 **`classList` 에서는 `TypeError`** 다. 그 메서드는 **`rel` 처럼 「지원 토큰 목록」이 정의된 속성에서만** 쓸 수 있고 `class` 에는 그런 목록이 없다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-classlist.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '26,32p'
잡아 둔 classList 는 라이브인가 · 공백은 어떻게 되나
c.classList === c.classList   true
setAttribute 로 갈아 끼운 뒤  잡아 둔 cl.length = 3       ["z1","z2","z3"]
소스의 class 속성             "  두   칸   띄움  "
classList 로 보면             length = 3                  ["두","칸","띄움"]
classList.value               "  두   칸   띄움  "        (속성 원문 그대로다)
add('끝') 뒤 속성             "두 칸 띄움 끝"             (그때 정규화된다)
(exit 0)
```

- **`classList` 는 라이브다** — 잡아 둔 `cl` 이 `setAttribute` 로 갈아 끼운 값을 따라온다. 그리고 **같은 객체**다(`c.classList === c.classList` 가 `true`).
- ★ **원문은 그대로 있다가 한 번 건드리면 정규화된다.** `class="  두   칸   띄움  "` 는 `classList.value` 로 읽으면 **원문 그대로**인데, `add('끝')` 한 번에 속성이 **`"두 칸 띄움 끝"`** 으로 정리된다.
- 그래서 **「속성 문자열이 안 바뀌었다」를 근거로 「아무 일도 안 났다」고 읽으면 안 된다** — 반대로 **아무 일도 안 시켰는데 문자열이 바뀌는 자리**가 여기다.

비용 — 정규화는 한 번뿐이고 싸다. 다만 **CSS 나 서버가 그 문자열을 원문으로 대조하고 있으면 깨진다.**

### (6) 인라인 `style` — `style` 속성 문자열과 같은 것이다

**언제 쓰나** — 계산한 값을 요소에 직접 줄 때.

**던진 것** — 아래 (7)\~(9)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa06b-07-style.html -->
<!doctype html>
<meta charset="utf-8">
<title>07-style</title>
<style>#sheet { color: rgb(0, 128, 0); font-size: 21px }</style>
<div id="s" style="color: red; padding-left: 4px">인라인</div>
<div id="sheet">스타일시트가 칠한 것</div>
<div id="n">style 속성이 없다</div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push((padw(a, 40) + padw(b, 34) + (c === undefined ? '' : c)).replace(/ +$/, ''));
const s = document.getElementById('s'), n = document.getElementById('n');

O.push('인라인 style 은 style 속성 문자열과 같은 것이다');
row('getAttribute("style")', J(s.getAttribute('style')));
row('s.style.cssText', J(s.style.cssText));
row('둘이 한 글자도 같은가', String(s.getAttribute('style') === s.style.cssText), '(끝의 세미콜론 하나 차이다)');
row('s.style.color · paddingLeft', J(s.style.color) + '  ' + J(s.style.paddingLeft));
row("getPropertyValue('padding-left')", J(s.style.getPropertyValue('padding-left')));
row('s.style.length · item(0)', s.style.length + '  ' + J(s.style.item(0)));
row('s.style === s.style', String(s.style === s.style));
row('style 속성이 없는 요소', J(n.getAttribute('style')), 'n.style.cssText = ' + J(n.style.cssText));
n.style.color = 'teal';
row('거기에 한 줄 쓰면', J(n.getAttribute('style')), '속성 === cssText 가 ' + (n.getAttribute('style') === n.style.cssText));
s.style.color = 'navy';
row("s.style.color = 'navy' 뒤", J(s.getAttribute('style')), '속성 === cssText 가 ' + (s.getAttribute('style') === s.style.cssText));
O.push('');

O.push('창 ④ — 쓴 자리에서 되읽어 담김 · 조용히 버려짐 · 예외로 가른다');
row('쓴 것', '되읽기', '판정');
const 써보기 = (label, fn, read) => {
  const 전 = read();
  try { fn(); const 후 = read();
    row(label, J(후), 후 === 전 ? '안 바뀜 — 조용히 버려졌다' : (후 === '' ? '지워졌다' : '담겼다')); }
  catch (e) { row(label, '예외 ' + e.name, e.message.slice(0, 40)); }
};
const t = document.createElement('div');
써보기("style.color = 'blue'", () => t.style.color = 'blue', () => t.style.color);
써보기("style.color = 'bogus'", () => t.style.color = 'bogus', () => t.style.color);
써보기("style.color = ''", () => t.style.color = '', () => t.style.color);
써보기("style.width = '10'", () => t.style.width = '10', () => t.style.width);
써보기("style.width = '10px'", () => t.style.width = '10px', () => t.style.width);
써보기("style.colour = 'red' (오타)", () => t.style.colour = 'red', () => t.style.getPropertyValue('colour'));
써보기("setProperty('color','lime','important')", () => t.style.setProperty('color', 'lime', 'important'),
       () => t.style.color + ' !' + t.style.getPropertyPriority('color'));
써보기("setProperty('--x','7')", () => t.style.setProperty('--x', '7'), () => t.style.getPropertyValue('--x'));
써보기("style['--x'] = '9' (대괄호)", () => t.style['--x'] = '9', () => t.style.getPropertyValue('--x'));
써보기("cssText = 'color:green;bogus:1;width:z'", () => t.style.cssText = 'color:green;bogus:1;width:z',
       () => t.style.cssText);
row('그 뒤 t.getAttribute("style")', J(t.getAttribute('style')));
O.push('');

O.push('한 줄 썼는데 목록에는 몇 줄이 담기나 — 단축 속성은 낱개로 풀린다');
const u = document.createElement('div');
const 재기 = (label, fn) => { fn(); O.push(padw(label, 40) + padw('length = ' + u.style.length, 18) +
  J([...Array(u.style.length).keys()].map(i => u.style.item(i)).join(' '))); };
재기("style.color = 'red'", () => u.style.color = 'red');
재기("style.margin = '1px 2px'", () => u.style.margin = '1px 2px');
재기("style.marginTop = '9px' (한 낱개만)", () => u.style.marginTop = '9px');
재기("style.margin = '' (단축으로 지우기)", () => u.style.margin = '');
재기("style.background = 'blue'", () => u.style.background = 'blue');
row('그 뒤 getAttribute("style")', J(u.getAttribute('style')));
row('u.style.background 되읽기', J(u.style.background), 'u.style.margin = ' + J(u.style.margin));
O.push('');

O.push('el.style 은 스타일시트 규칙을 못 본다 — 그 창은 08번 주제다');
const sh = document.getElementById('sheet');
row('sheet 의 style 속성', J(sh.getAttribute('style')));
row('sh.style.color · fontSize', J(sh.style.color) + '  ' + J(sh.style.fontSize));
row('sh.style.length', String(sh.style.length), '(스타일시트가 칠했는데 0 이다)');
row('getComputedStyle 로 물으면', J(getComputedStyle(sh).color) + '  ' + J(getComputedStyle(sh).fontSize));
row('인라인이 있는 s 는', 'style.color = ' + J(s.style.color), 'computed = ' + J(getComputedStyle(s).color));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,11p'
인라인 style 은 style 속성 문자열과 같은 것이다
getAttribute("style")                   "color: red; padding-left: 4px"
s.style.cssText                         "color: red; padding-left: 4px;"
둘이 한 글자도 같은가                   false                             (끝의 세미콜론 하나 차이다)
s.style.color · paddingLeft             "red"  "4px"
getPropertyValue('padding-left')        "4px"
s.style.length · item(0)                2  "color"
s.style === s.style                     true
style 속성이 없는 요소                  null                              n.style.cssText = ""
거기에 한 줄 쓰면                       "color: teal;"                    속성 === cssText 가 true
s.style.color = 'navy' 뒤               "color: navy; padding-left: 4px;" 속성 === cssText 가 true
(exit 0)
```

- **`el.style.cssText` 와 `getAttribute('style')` 은 같은 것**이다 — 정확히는 **끝의 세미콜론 하나만 다르다**(원문에 없으면 `cssText` 가 붙여 준다). 한 줄이라도 쓰고 나면 **둘이 한 글자까지 같아진다**(마지막 두 줄).
- **`style` 속성이 없는 요소에서도 `el.style` 은 있다** — `cssText` 가 `""` 인 빈 선언 목록이다. **`null` 이 아니다.**
- **`el.style` 은 같은 객체**다(`s.style === s.style` 이 `true`). [08번 주제](../08-getcomputedstyle/2-summary.md)의 `getComputedStyle` 과 **여기가 갈린다.**
- 읽는 창구가 셋이다 — **카멜 프로퍼티**(`style.paddingLeft`), **`getPropertyValue('padding-left')`**, **`item(i)`/`length`**.

비용 — 인라인 스타일은 **캐스케이드에서 매우 강하다.** 시트로 되돌릴 수 없고 `!important` 로만 이긴다. 그 규칙의 정본은 [CSS 01번 주제](../../languages/css/syntax/01-cascade-and-priority/2-summary.md)다.

### (7) ★ 창 ④ — 쓴 자리에서 되읽어 세 갈래로 가른다

**언제 쓰나** — `el.style` 에 값을 쓸 때마다. **이 표면은 거의 전부 조용하다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,25p'
창 ④ — 쓴 자리에서 되읽어 담김 · 조용히 버려짐 · 예외로 가른다
쓴 것                                   되읽기                            판정
style.color = 'blue'                    "blue"                            담겼다
style.color = 'bogus'                   "blue"                            안 바뀜 — 조용히 버려졌다
style.color = ''                        ""                                지워졌다
style.width = '10'                      ""                                안 바뀜 — 조용히 버려졌다
style.width = '10px'                    "10px"                            담겼다
style.colour = 'red' (오타)             ""                                안 바뀜 — 조용히 버려졌다
setProperty('color','lime','important') "lime !important"                 담겼다
setProperty('--x','7')                  "7"                               담겼다
style['--x'] = '9' (대괄호)             "7"                               안 바뀜 — 조용히 버려졌다
cssText = 'color:green;bogus:1;width:z' "color: green;"                   담겼다
그 뒤 t.getAttribute("style")           "color: green;"
(exit 0)
```

```text
   style.color = 'blue'      되읽으니 "blue"   ->  담겼다
   style.color = 'bogus'     되읽으니 "blue"   ->  ★ 조용히 버려졌다 (예외 없음)
   style.color = ''          되읽으니 ""       ->  지워졌다
   style.width = '10'        되읽으니 ""       ->  ★ 조용히 버려졌다 (단위가 없다)
   style.colour = 'red'      되읽으니 ""       ->  ★ 조용히 버려졌다 (철자가 다르다)
   style['--x'] = '9'        되읽으니 "7"      ->  ★ 조용히 버려졌다 (커스텀은 대괄호로 못 쓴다)
```

- **네 줄이 「조용히 버려졌다**」다. **예외도 경고도 없고 콘솔도 조용하다.** 되읽어 대조하지 않으면 영영 안 보인다.
- **`style.colour = 'red'`**(영국식 철자)는 **그냥 자바스크립트 프로퍼티 하나를 만들고 끝난다** — [06번 주제](../06-attribute-vs-property/2-summary.md)의 expando 와 같은 사고다.
- **커스텀 속성은 `setProperty`/`getPropertyValue` 로만** 다룬다. `style['--x'] = '9'` 는 **대괄호 표기라도 안 된다** — 실측에서 앞서 `setProperty('--x','7')` 로 넣은 `"7"` 이 그대로였다.
- **`setProperty(name, value, 'important')`** 로 우선순위를 줄 수 있고 `getPropertyPriority` 로 되읽는다.
- **`cssText` 대입은 여러 선언을 한 번에 던지는데, 유효한 것만 남는다** — `'color:green;bogus:1;width:z'` 를 주면 **`color: green;` 만** 남는다. **셋 중 둘이 조용히 사라졌다.**

비용 — 창 ④ 없이 쓰면 **틀린 값을 쓴 코드가 「아무 일도 안 하는 코드」로 조용히 산다.** CSS 갈래가 말한 「에러가 없는 언어」의 성질이 그대로 여기 있다.

### (8) 한 줄 썼는데 목록에는 여러 줄 — 단축 속성은 낱개로 풀린다

**언제 쓰나** — `style.margin`·`style.background` 처럼 단축 속성을 쓸 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '27,34p'
한 줄 썼는데 목록에는 몇 줄이 담기나 — 단축 속성은 낱개로 풀린다
style.color = 'red'                     length = 1        "color"
style.margin = '1px 2px'                length = 5        "color margin-top margin-right margin-bottom margin-left"
style.marginTop = '9px' (한 낱개만)     length = 5        "color margin-top margin-right margin-bottom margin-left"
style.margin = '' (단축으로 지우기)     length = 1        "color"
style.background = 'blue'               length = 10       "color background-image background-position-x background-position-y background-size background-repeat background-attachment background-origin background-clip background-color"
그 뒤 getAttribute("style")             "color: red; background: blue;"
u.style.background 되읽기               "blue"                            u.style.margin = ""
(exit 0)
```

- **`style.margin = '1px 2px'` 한 줄이 `length` 를 1 에서 5 로 올린다** — `margin-top`·`margin-right`·`margin-bottom`·`margin-left` **네 낱개**로 풀려 담긴다.
- **`style.background = 'blue'` 는 낱개 9개**를 더한다(`length` 1 → 10).
- ★ **그런데 되읽으면 다시 단축으로 보인다** — `getAttribute('style')` 이 `"color: red; background: blue;"` 다. **담기는 것은 낱개, 직렬화는 단축**이다. 낱개가 전부 갖춰지고 서로 모순되지 않을 때 CSSOM 이 단축으로 되접는다.
- **단축으로 지우면 낱개가 전부 빠진다** — `style.margin = ''` 뒤 `length` 가 5 에서 1 로 돌아왔다.
- ★ **낱개 개수는 명세가 정한 목록이다.** 명세에 낱개가 더해지면 이 수가 바뀐다 — **판을 적고 다시 찍을 자리**다(이 문서는 Chrome 151).

비용 — 낱개 하나만 고치려고 단축을 쓰면 **나머지 낱개가 초기값으로 리셋된다.** 실측에서 `style.background='blue'` 가 `background-image` 이하 아홉 낱개를 전부 다시 썼다.

### (9) `el.style` 로는 스타일시트가 안 보인다 — 그 창은 08번이다

**언제 쓰나** — 「지금 이 요소의 색이 뭐지」를 물을 때. **여기서 표면이 갈린다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-07-style.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '36,41p'
el.style 은 스타일시트 규칙을 못 본다 — 그 창은 08번 주제다
sheet 의 style 속성                     null
sh.style.color · fontSize               ""  ""
sh.style.length                         0                                 (스타일시트가 칠했는데 0 이다)
getComputedStyle 로 물으면              "rgb(0, 128, 0)"  "21px"
인라인이 있는 s 는                      style.color = "navy"              computed = "rgb(0, 0, 128)"
(exit 0)
```

- **스타일시트가 칠한 요소의 `el.style` 은 빈 목록**이다 — `length` 가 **0** 이고 `getAttribute('style')` 이 `null` 이다. **화면은 초록인데** 그렇다.
- 같은 요소를 `getComputedStyle` 로 물으면 **`"rgb(0, 128, 0)"`·`"21px"`** 가 나온다.
- ★ **`el.style` 이 답하는 것은 「내가 이 요소에 직접 쓴 것」뿐**이다. 시트도, 상속도, UA 기본값도 안 본다.
- 인라인이 있는 요소에서도 **값의 모양이 다르다** — `el.style.color` 는 쓴 글자 `"navy"` 그대로이고 `getComputedStyle` 은 **절대화한 `"rgb(0, 0, 128)"`** 이다.

```text
   질문                            대답하는 창구
   '내가 이 요소에 직접 뭘 썼나'   el.style        (이 주제)
   '지금 실제로 무슨 값인가'        getComputedStyle (08번 주제)
```

비용 — 이 경계를 모르면 「스타일이 안 먹었다」를 진단할 때 **`el.style` 을 찍어 보고 「값이 없다」고 오진**한다.

```html demo
<div id="d7chip">알림</div>
<button id="d7t">toggle('on')</button>
<button id="d7y">toggle('on', true)</button>
<button id="d7n">toggle('on', false)</button>
<div id="d7out"></div>
<style>
  #d7chip { display: inline-block; padding: 4px 12px; border-radius: 6px; background: #e2e8f0; color: #0f172a; }
  #d7chip.on { background: #2563eb; color: #fff; }
  #d7out { font-family: monospace; background: #0f172a; color: #e2e8f0; padding: 8px; margin-top: 6px; }
</style>
<script>
  const chip = document.getElementById('d7chip');
  const 보이기 = r => document.getElementById('d7out').textContent =
    'class 속성 = ' + JSON.stringify(chip.getAttribute('class')) + '   반환값 = ' + r;
  d7t.onclick = () => 보이기(chip.classList.toggle('on'));
  d7y.onclick = () => 보이기(chip.classList.toggle('on', true));
  d7n.onclick = () => 보이기(chip.classList.toggle('on', false));
  보이기('(아직 안 눌렀다)');
</script>
```

> **보이는 것** — 처음에는 회색 알약이고 아래 검은 칸에 **`class 속성 = null`** 이 찍힌다. **`class` 속성이 아예 없다.**\
> **`toggle('on')`** 을 누르면 알약이 파래지고 속성이 `"on"`, 반환값이 `true` 가 된다. **한 번 더** 누르면 회색으로 돌아가고 **속성이 `null` 이 아니라 빈 문자열 `""`** 이 된다 — 한 번 건드린 자리에는 빈 속성이 남는다.\
> **`toggle('on', true)`** 는 **몇 번을 눌러도 파란 채로** 있고 반환값이 언제나 `true` 다. **`toggle('on', false)`** 는 반대로 언제나 회색·`false` 다.\
> **바꿔 볼 것** — `toggle('on', true)` 를 `add('on')` 으로 바꿔 보라(반환값이 `undefined` 로 바뀐다) · `chip.classList.toggle('두 칸')` 을 콘솔에서 던져 보라(`InvalidCharacterError`) · `chip.className = 'on on'` 으로 넣어 보라(메서드가 아니라 문자열 대입이라 **검사 없이 그대로 담긴다**).

*(Chrome 151 headless 실측: 버튼을 `toggle` → `toggle` → `toggle(true)` → `toggle(true)` → `toggle(false)` 순으로 눌러 `class` 속성이 `null` → `"on"` → `""` → `"on"` → `"on"` → `""` 로, 계산된 배경색이 `rgb(226, 232, 240)` ↔ `rgb(37, 99, 235)` 로 갈리는 것을 확인했다)*

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
// dataset — DOMStringMap
el.dataset.fooBar            // data-foo-bar 를 읽는다
el.dataset['1-2']            // '-숫자' 는 바뀌지 않아 대괄호로만
el.dataset.newKey = 'v';     // data-new-key 를 만든다
delete el.dataset.newKey;    // 속성을 지운다
Object.keys(el.dataset)      // 키 전수

// classList — DOMTokenList (라이브)
el.classList.add('a', 'b')        // undefined
el.classList.remove('a', 'b')     // undefined
el.classList.toggle('a')          // 그 뒤에 있나 (불리언)
el.classList.toggle('a', force)   // force 가 참이면 add, 거짓이면 remove
el.classList.replace('a', 'b')    // 바꿨나 (불리언)
el.classList.contains('a')        // 있나 (불리언)
el.classList.value                // 속성 원문 그대로 · 대입도 된다(검사 없음)
el.classList.length  [...el.classList]

// 인라인 style — CSSStyleDeclaration
el.style.paddingLeft = '4px'      // 카멜
el.style.setProperty('padding-left', '4px')
el.style.setProperty('--x', '7')  // 커스텀 속성은 이 창구로만
el.style.getPropertyValue('--x')
el.style.getPropertyPriority('color')   // '' 또는 'important'
el.style.removeProperty('color')
el.style.cssText = 'color:red'    // 통째로 갈아 끼운다
el.style.length  el.style.item(0)
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// 1. 커스텀 속성을 프로퍼티로 쓴다 — 조용히 버려진다
el.style['--x'] = '9';                  // 아무 일도 안 난다
el.style.setProperty('--x', '9');       // 이것이 맞다

// 2. 단위를 안 붙인다 — 조용히 버려진다
el.style.width = 10;                    // 아무 일도 안 난다
el.style.width = '10px';                // 이것이 맞다

// 3. 공백이 든 클래스를 메서드로 넣는다 — 예외
el.classList.add('두 칸');               // InvalidCharacterError
el.classList.add('두', '칸');            // 이것이 맞다

// 4. dataset 키에 '-' 를 쓴다 — 예외이거나 이상한 이름
el.dataset['foo-bar'] = 'v';            // SyntaxError
el.dataset['foo-Bar'] = 'v';            // data-foo--bar 가 생긴다 (안 던진다)
el.dataset.fooBar = 'v';                // 이것이 맞다

// 5. 대문자를 연달아 쓴다 — '-' 가 글자마다 붙는다
el.dataset.userID = '7';                // data-user-i-d
el.dataset.userId = '7';                // data-user-id

// 6. el.style 로 지금 색을 읽는다 — 시트로 칠한 것은 안 보인다
if (el.style.color === 'red') { }       // 인라인에만 있을 때만 참
if (getComputedStyle(el).color === 'rgb(255, 0, 0)') { }   // 08번 주제
```

### 어디서 헷갈리나

- **`classList.value` 와 `className` 은 같은 것**이다. 둘 다 속성 원문이고 **둘 다 검사를 안 한다.**
- **`dataset` 의 키 이름과 속성 이름은 서로의 역이 아니다.** 읽기는 `-소문자`→대문자, 쓰기는 대문자→`-소문자`. **연속 대문자에서 왕복이 깨진다.**
- **`el.style.length` 는 「내가 쓴 선언 수**」이고 [08번 주제](../08-getcomputedstyle/2-summary.md)의 `getComputedStyle().length` 는 「**속성 전부**」다. 이름이 같고 뜻이 전혀 다르다.

## 어디서 틀리나

### 1. 스타일 값이 조용히 버려진 것을 모른다

`style.width = 10`(단위 없음)·`style.color = 'bogus'`·철자가 다른 프로퍼티는 **예외도 경고도 없다.** 되읽어 대조하는 창 ④ 말고는 진단이 없다.

### 2. `dataset` 키에 대문자를 연달아 쓴다

`userID` 는 `data-user-i-d` 가 된다. 마크업이나 CSS 가 `data-user-id` 를 기대하고 있으면 **맞물리지 않는데 에러가 없다.**

### 3. 마크업에 `data-fooBar` 라고 쓴다

파서가 `data-foobar` 로 소문자화하므로 `dataset.fooBar` 는 **`undefined`** 다. 실측에서 그 값은 **`dataset.foobar` 로만** 읽혔다.

### 4. `classList.value`·`className` 으로 검사를 우회한다

메서드는 공백·빈 토큰을 막지만 **문자열 대입은 안 막는다.** 실측에서 `cl.value = 'x  y'` 가 예외 없이 담겼다.

### 5. 단축 속성으로 낱개 하나만 고치려 한다

`style.background = 'blue'` 는 **낱개 9개를 전부 다시 쓴다.** `background-image` 로 심어 둔 것이 사라진다. 낱개 하나만 고치려면 낱개 이름을 쓴다.

### 6. `el.style` 을 찍어 보고 「스타일이 없다」고 오진한다

시트로 칠한 요소의 `el.style.length` 는 **0** 이다. 「지금 무슨 값인가」는 [08번 주제](../08-getcomputedstyle/2-summary.md)의 창구로 물어야 한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `data-foo-bar` ↔ `fooBar` 변환 규칙과 **`-` 다음 소문자에 `SyntaxError`** | **명세**(HTML `dataset` 절) |
| `-` 다음이 숫자면 안 바뀌는 것(`data-1-2` → `'1-2'`) | **명세**(같은 절 — ASCII 소문자만 대상) |
| `classList` 다섯 메서드의 반환값과 `toggle` 의 두 번째 인자 | **명세**(DOM `DOMTokenList`) |
| 공백 토큰 `InvalidCharacterError` · 빈 토큰 `SyntaxError` | **명세**(DOM — validate steps) |
| `classList` 가 라이브이고 같은 객체인 것 | **명세**(DOM) |
| 한 번 건드리면 `class` 속성이 정규화되는 것 | **명세**(DOM — 토큰 목록을 다시 직렬화한다) |
| `el.style` 이 `style` 속성과 같은 것이고 `cssText` 로 왕복하는 것 | **명세**(CSSOM) |
| **무효한 선언이 조용히 버려지는 것** | **명세**(CSS — 파싱 실패는 에러가 아니라 무시다) |
| 커스텀 속성이 `setProperty` 로만 되는 것 | **명세**(CSSOM — 카멜 매핑은 알려진 속성에만 만들어진다) |
| **단축 속성이 풀리는 낱개의 개수**(`background` → 10) | **명세**(CSS 가 낱개 목록을 정한다) **+ 판**(낱개가 추가되면 바뀐다) |
| 직렬화가 단축으로 되접히는 것 | **명세**(CSSOM 직렬화) **+ 구현**(되접는 조건의 세부) |
| `cssText` 끝의 세미콜론 | **명세**(CSSOM 직렬화 형식) |
| `classList.supports` 가 `TypeError` 인 것 | **명세**(지원 토큰 목록이 정의된 속성에서만) |

- ★ **「조용히 버려진다」는 구현의 게으름이 아니라 CSS 의 설계**다. CSS 는 모르는 선언을 **무시하도록** 정해져 있고(전방 호환), `el.style` 은 그 문법을 쓰는 표면이라 같은 성질을 갖는다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 상태를 클래스로 표현 | `classList.toggle(name, 조건)` | `className` 문자열 붙이기 |
| 클래스 이름이 외부에서 온다 | `classList.add`(검사가 있다) | `classList.value`·`className` 대입 |
| 마크업에 값을 심고 스크립트가 읽는다 | `data-*` + `dataset` | `el.myThing`(expando) |
| 객체·큰 데이터를 요소에 붙인다 | `WeakMap` | `dataset`(글자열만 된다 · 직렬화 비용) |
| 계산한 수치를 요소에 준다 | `el.style.setProperty` · 커스텀 속성 | 클래스 수십 개 만들기 |
| 커스텀 속성을 쓴다 | `setProperty('--x', …)` | `style['--x'] = …` |
| 낱개 하나만 고친다 | 낱개 이름(`backgroundImage`) | 단축(`background`) |
| 「지금 무슨 값인가」 | `getComputedStyle`([08번 주제](../08-getcomputedstyle/2-summary.md)) | `el.style` |
| 스타일을 껐다 켰다 한다 | 클래스 토글 | 인라인 `style` 대입(캐스케이드에서 되돌리기 어렵다) |

## 핵심 문장

1. **셋은 속성 하나를 보는 전용 창이다.** 본체에 있는 것은 글자열 한 줄뿐이다.
2. **`dataset` 의 변환은 왕복이 아니다** — 읽기는 `-소문자`→대문자, 쓰기는 대문자→`-소문자`. **연속 대문자에서 깨진다**(`fooBAR` → `data-foo-b-a-r`).
3. **`dataset` 은 `-` 다음이 소문자인 키에만 던진다.** `foo-Bar` 는 안 던지고 `data-foo--bar` 를 만든다 — **안 던지는 쪽이 더 나쁘다.**
4. **`toggle` 의 두 번째 인자는 「뒤집기」를 「강제」로 바꾼다** — 참이면 `add`, 거짓이면 `remove`. 멱등이 된다.
5. **`el.style` 은 `style` 속성 문자열 그 자체**다(`cssText`). 시트도 상속도 안 보인다.
6. **잘못 쓴 스타일 선언은 조용히 버려진다.** 예외도 경고도 없고, **되읽어 대조하는 창 ④** 말고는 진단이 없다.
7. **단축 속성은 낱개로 담기고 단축으로 직렬화된다.** 한 줄이 목록 열 줄이 될 수 있다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 07번)
- [06번 주제](../06-attribute-vs-property/2-summary.md) — 「**`data-*` 와 `class` 는 반영이 아니다**」의 정본. 이 주제는 **그럼 무엇이냐**부터다
- [08번 주제](../08-getcomputedstyle/2-summary.md) — 「**지금 무슨 값인가**」의 창구. `el.style` 이 못 보는 것을 전부 그쪽이 본다
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md) — **라이브**라는 성질. `classList` 가 그 성질을 갖는다
- 목록의 **12번 주제**(Shadow DOM) — 그림자 경계 안의 `class` 는 바깥 시트가 못 본다. 표면은 같고 **범위**가 다르다
- 목록의 **54번 주제**(Web Animations) — 인라인 `style` 보다 **더 강한** 자리에서 값을 쓰는 방법
- [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md) — **「에러가 없는 언어」와 진단 3창의 정본.** 이 주제의 창 ④ 가 거기서 왔다
- [CSS 01번 주제](../../languages/css/syntax/01-cascade-and-priority/2-summary.md) — 인라인 `style` 이 캐스케이드에서 **어디에 서나**
- [CSS 36번 주제](../../languages/css/syntax/36-custom-properties/2-summary.md) — 커스텀 속성의 **값 처리**. 여기는 **`setProperty` 라는 표면**까지만
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **02번**([요소와 속성 문법](../../languages/html/syntax/02-elements-and-attributes/2-summary.md)) — **속성 이름이 소문자로 맞춰지는 것**의 정본. `data-fooBar` 가 왜 안 되는지의 근거
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **06번**(전역 속성) — `data-*` 의 **마크업 쪽** 정본. 여기는 **`dataset` 이라는 API 표면**만

## 용어 풀이

- **`DOMStringMap`** — `el.dataset` 의 타입. 키가 **글자열만** 담기는 맵처럼 생긴 객체다.
- **`DOMTokenList`** — `el.classList` 의 타입. **공백으로 갈린 토큰 목록**을 다루는 라이브 객체. `rel`·`sandbox` 등에도 쓰인다.
- **`CSSStyleDeclaration`** — `el.style` 의 타입. **선언 목록**이다. [08번 주제](../08-getcomputedstyle/2-summary.md)의 `getComputedStyle` 도 같은 타입을 돌려주는데 **읽기 전용**이다.
- **케밥 표기(kebab-case)** — `data-foo-bar` 처럼 `-` 로 잇는 표기. HTML·CSS 쪽 관례다.
- **카멜 표기(camelCase)** — `fooBar` 처럼 대문자로 잇는 표기. 자바스크립트 쪽 관례다.
- **토큰(token)** — 공백으로 갈린 한 낱말. 클래스 이름 하나가 토큰 하나다.
- **정규화(normalize)** — 토큰 목록을 다시 직렬화하면서 여분 공백이 정리되는 것.
- **단축 속성(shorthand)** — `margin`·`background` 처럼 여러 낱개를 한 번에 정하는 속성.
- **낱개 속성(longhand)** — `margin-top`·`background-color` 처럼 하나만 정하는 속성. **실제로 담기는 것은 이쪽**이다.
- **커스텀 속성(custom property)** — `--x` 로 시작하는 사용자 정의 속성. **`setProperty` 로만** 쓴다.
- **조용히 버려짐** — 값이 무효해서 담기지 않았는데 예외도 경고도 없는 것. **이 주제의 주된 실패 방식**이다.
- **expando** — 표준에 없는데 스크립트가 객체에 그냥 붙인 프로퍼티(정본: [06번 주제](../06-attribute-vs-property/2-summary.md)).

## 더 들어가면

- **`DOMTokenList` 는 `class` 전용이 아니다.** `link.relList`·`iframe.sandbox`·`a.relList`·`output.htmlFor` 가 같은 타입이고, **그쪽에서는 `supports()` 가 동작한다** — 지원 토큰 목록이 정의돼 있기 때문이다. `class` 에서만 `TypeError` 인 이유가 그것이다. (**이 문서는 `relList` 를 던져 보지 않았다** — 명세 구조만 적는다.)
- **`dataset` 에 객체를 담지 마라.** 값은 글자열로 변환되므로 `JSON.stringify` 를 거치게 되고, **DOM 속성에 큰 문자열이 박혀** 직렬화·복제·`MutationObserver` 비용이 전부 는다. 요소와 객체를 잇는 것은 **`WeakMap`** 이다.
- **`el.attributeStyleMap`**(Typed OM)은 `el.style` 의 타입이 붙은 판이다 — `el.attributeStyleMap.set('width', CSS.px(10))` 처럼 **숫자와 단위를 객체로** 다룬다. Chromium 계열에만 있어 이 목록에서는 다루지 않는다.
- **`classList` 는 라이브다** — 인덱스로 순회하며 `remove` 하면 [02번 주제](../02-element-queries-and-live-collections/2-summary.md)의 라이브 컬렉션 사고와 **같은 모양**이 된다. `[...el.classList]` 로 떠 놓고 돌리는 것이 안전하다. (**이 문서는 그 순회 사고를 `classList` 로 다시 던져 보지 않았다** — 라이브라는 것만 위 (5)에서 실측했다.)
- **인라인 `style` 과 CSP** — CSP 명세는 `style-src` 의 검사 대상을 **마크업의 `style` 속성과 `<style>` 요소**로 두고, `el.style` 같은 **CSSOM 쓰기는 검사 대상에 넣지 않는다.** **이 문서는 CSP 를 건 문서를 던져 보지 않았다** — 명세를 읽은 것이다. 실측이 필요한 경계이고, 그 자리는 목록의 **58번 주제**다.
