# web-api/08 — `getComputedStyle`: 스크립트에서 계산값을 읽는다는 것 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 여기서 다루는 것은 **「CSS 가 무엇을 계산하나」가 아니라 「스크립트가 그것을 어떻게 읽나**」다. **값이 어느 단계에서 픽셀이 되는지는 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)가 정본**이고 여기서 다시 쓰지 않는다.\
> **기준 소스** — [CSSOM](https://drafts.csswg.org/cssom/#dom-window-getcomputedstyle) 의 「`getComputedStyle()`」·「`CSSStyleDeclaration`」·「resolved values」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `getComputedStyle` 은 DOM Level 2 Style(2000) 부터 있었고 **Baseline 추적 대상이 아닐 만큼 오래됐다**(갈래 [`../README.md`](../README.md) 의 「확인하지 못한 것」).\
> **선행** — [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)(`el.style`)와 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)(값 처리 단계).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 있다** — 마지막 절에서 **읽기 비용을 재기 때문**이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 계산값 문자열 · `length` · `item(i)` 목록 · 예외 이름 · 객체 동일성 · `display:none` 과 트리 밖의 대답 | 전부 명세가 정한 절차의 결과다 |
| **안 흔들린다** | 시간 표의 **자릿수와 순위** | 세 판 모두 같았다 |
| **흔들린다** | `performance.now()` 의 **개별 수치**(중앙값·최소·최대 전부) | 판마다 달라진다 |
| **흔들린다** | `cs.font` 의 글꼴 이름 · flex 실측의 `307.19` | **이 머신의 글꼴 치수**에 달렸다 — 다른 기계에서는 다른 숫자다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- **수치를 인용할 때는 「몇 판을 어떻게 쟀나」를 같이 적는다** — 한 파일 안에서 **9판**을 돌려 **중앙값**을 쓰고 최소·최대를 함께 실었다.
- ★ **`performance.now()` 는 Chrome 에서 100마이크로초 단위로 뭉개진다**([04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) 실측). 표에서 **가장 작은 칸이 `0.10`** 이면 그것은 **분해능 한 칸**이다 — 「공짜」가 아니라 「**이 도구로는 못 잰다**」로 읽는다.
- **재대조에서 수치 칸만 정규화**한다. 위 표에 없는 것은 정규화하지 않는다.

## 한눈에 — 쉽게 말하면

**★ `el.style` 이 「장바구니에 내가 담은 것」이라면 `getComputedStyle` 은 「계산대가 뽑아 준 영수증」이다.**

계산대에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 내가 **직접 담은 것** | `el.style` — `style` 속성에 쓴 것뿐([07번 주제](../07-dataset-classlist-inline-style/2-summary.md)) |
| 계산대가 뽑은 **영수증** | `getComputedStyle(el)` — 시트·상속·UA 기본값을 전부 적용한 뒤의 값 |
| 영수증에는 **안 담은 품목까지 전부** | 476줄 — 내가 건드리지 않은 속성도 다 찍힌다 |
| 영수증의 금액은 **절대 금액** | `50%`·`3em` 이 아니라 `200px`·`60px` |
| 영수증은 **고쳐 쓸 수 없다** | 읽기 전용 — 쓰면 `NoModificationAllowedError` |
| **영수증을 뽑을 때마다 새 종이** | `getComputedStyle(el) !== getComputedStyle(el)` |
| 그런데 **그 종이의 숫자는 계속 갱신된다** | 라이브 — 잡아 둔 객체가 나중 변경을 따라온다 |
| ★ **영수증과 봉투 속이 다를 수 있다** | 계산값 ≠ 상자 — 창 ④ 가 그것만 본다 |

- **`el.style` 로 안 보이던 값이 여기서 보이는 이유는 「값이 온 곳」이 다르기 때문**이다. 인라인은 넷 중 하나일 뿐이다.
- ★ **이름이 거짓말이다.** 돌려받는 것은 **언제나 「계산값」이 아니다** — 속성에 따라 **사용값**일 때가 있다. 명세가 정한 이름은 **해석값(resolved value)** 이고, **그 구분의 정본은 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)** 다.
- ★ **읽기가 쓰기와 섞이면 비싸진다.** 그것만이 이 주제가 재는 수치다.

```text
   값이 오는 곳 넷                          두 창구가 보는 범위
   ┌──────────────────────┐
   │ UA 기본 시트         │ ─┐
   │ 작성자 스타일시트    │  │
   │ 부모에게서 상속      │  ├──> getComputedStyle(el)   전부 본다 (476줄)
   │ 인라인 style 속성    │ ─┤
   └──────────────────────┘  └──> el.style              이 한 줄만 본다 (0~n줄)
```

## 이 주제가 답하려는 질문

1. **`el.style` 로는 안 보이던 값이 왜 여기서는 보이나.** 그리고 **돌려받은 것이 내가 쓴 글자가 아닌** 이유는.
2. **상자가 없는 요소**(`display: none`·트리 밖)에 물으면 무엇이 오나. **둘이 같은가.**
3. **이 읽기는 얼마나 비싼가.** 그리고 **무엇이 비싸게 만드나** — 읽기 자체인가, 섞는 것인가.

## 이 갈래의 관측 창 — ★ 창 4 는 `getBoundingClientRect()`

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom             스크립트가 다 돈 뒤의 트리를 글자로
                               ★ 이 주제에서는 아무것도 못 본다 — 아래 (1)
  창 2  노드 단위 프로브        el.style 과 getComputedStyle 을 같은 줄에
  창 3  두 번 읽기              바꾸기 전 / 바꾼 뒤를 같은 객체로
  ★ 창 4 (이 주제 고유)  getBoundingClientRect() 를 계산값 옆에 나란히
        무엇을 답하나:  그 계산값이 '레이아웃을 거친 값' 인가
        이 한 창이 세 가지를 가른다
          - box-sizing 이 걸린 width 가 어느 상자를 말하나
          - transform 이 계산값에 안 섞이는 것
          - 계산값이 한 글자도 안 바뀌는데 결과만 갈리는 자리 (min-width: auto)
  ★ 창 5 (빌려 쓴다)  04번의 performance.now() 9판 중앙값 — 비용
                      ★ 분해능 100마이크로초. 0.10 은 '공짜' 가 아니라 '못 잰다' 이다
```

- **왜 창 ④ 가 필요한가** — CSS 갈래에서 `getComputedStyle` 은 **진단 3창의 셋째 창**(이겼나)이었다. 그런데 **이 주제에서는 그 창 자체가 주인공**이므로, **그 창을 검사할 창**이 따로 필요하다.
- ★ **CSS 갈래가 이미 경고했다** — **셋째 창은 거짓 안심을 준다.** 「값은 담겼는데 레이아웃이 안 쓴 것」·「계산값은 그대로인데 배치만 바뀐 것」이 그쪽 실측에 여럿 있고, 전부 **`getBoundingClientRect()` 로만** 잡혔다(정본: [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md)의 진단 3창과 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)의 네 단계).
- **창 ④ 는 [목록의 09번 주제](../09-element-geometry/)(요소 기하)를 미리 빌려 오는 것**이다. 여기서는 **판정 도구**로만 쓰고, 좌표계·`offset*`/`client*`/`scroll*` 의 규칙은 그쪽 몫이다.

## 동작 방식

### (1) 창 ① 은 이 주제에서 아무것도 못 본다

**언제 쓰나** — 이 주제를 시작할 때. **무엇이 안 보이는지부터 확인한다.**

```html
<!-- wa06b-08-tree.html -->
<!doctype html>
<meta charset="utf-8">
<title>08-tree</title>
<style>#p { color: rgb(0, 128, 0); font-size: 21px }</style>
<p id="p">시트가 칠한 글</p>
<script>
  // 계산값을 읽기만 한다 — 읽기는 트리를 바꾸지 않는다.
  window.읽은값 = getComputedStyle(document.getElementById('p')).color;
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-tree.html | sed -n '4,5p'
<style>#p { color: rgb(0, 128, 0); font-size: 21px }</style>
</head><body><p id="p">시트가 칠한 글</p>
(exit 0)
```

- **`<p id="p">` 에는 아무 속성도 없다.** 계산값을 읽어도 **트리에 자국이 안 남는다** — 읽기는 문서를 안 바꾼다.
- 시트가 칠한 초록도 `21px` 도 **트리에는 `<style>` 안의 규칙 글자로만** 있다. **「이 요소가 지금 무슨 색인가」는 창 ① 으로 영영 못 묻는다.**
- ★ **이 갈래의 주력 창이 통째로 부적용인 주제**다. 그래서 창 ②\~④ 가 본문 전부를 진다.

비용 — 없다. 다만 **이 사실을 안 적어 두면 「트리를 봤는데 없더라」가 근거로 쓰인다.**

### (2) `el.style` 이 못 보는 넷

**언제 쓰나** — 「지금 이 요소가 무슨 값인가」를 물을 때.

**던진 것** — 아래 (3)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa06b-08-two.html -->
<!doctype html>
<meta charset="utf-8">
<title>08-two</title>
<style>
  #sheet { font-size: 21px }
  #wins  { color: blue !important }
  #box   { --tone: 진하게 }
</style>
<div id="parent" style="color: rgb(0, 128, 0)"><span id="inherit">상속받는 것</span></div>
<div id="inline" style="color: red">인라인</div>
<div id="sheet">시트</div>
<div id="wins" style="color: red">시트의 important 가 이긴다</div>
<div id="ua">아무도 안 건드림</div>
<div id="box">커스텀 속성</div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push((padw(a, 34) + padw(b, 32) + (c === undefined ? '' : c)).replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const gcs = el => getComputedStyle(el);

O.push('값이 온 곳이 넷인데 el.style 은 그중 하나만 본다');
row('값이 어디서 왔나', 'el.style', 'getComputedStyle');
row('인라인 style 의 color', J($('inline').style.color), J(gcs($('inline')).color));
row('스타일시트의 font-size', J($('sheet').style.fontSize), J(gcs($('sheet')).fontSize));
row('부모에게서 상속된 color', J($('inherit').style.color), J(gcs($('inherit')).color));
row('아무도 안 준 display', J($('ua').style.display), J(gcs($('ua')).display));
row('시트의 !important 가 이긴 color', J($('wins').style.color), J(gcs($('wins')).color));
row('커스텀 속성 --tone', J($('box').style.getPropertyValue('--tone')),
    J(gcs($('box')).getPropertyValue('--tone')));
O.push('');

O.push('돌려받은 객체의 성질 — el.style 과 무엇이 다른가');
const cs = gcs($('inline'));
row('무슨 객체인가', cs.constructor.name, $('inline').style.constructor.name);
row('선언 개수 length', 'computed = ' + cs.length, 'inline = ' + $('inline').style.length);
row('cssText', J(cs.cssText), '(inline 은 ' + J($('inline').style.cssText) + ')');
row('getPropertyValue 와 카멜', J(cs.getPropertyValue('font-size')) + '  ' + J(cs.fontSize));
for (const [label, fn] of [["cs.color = 'lime'", () => { cs.color = 'lime'; }],
                           ["cs.setProperty('color','lime')", () => cs.setProperty('color', 'lime')],
                           ["cs.removeProperty('color')", () => cs.removeProperty('color')],
                           ["cs.cssText = 'color: lime'", () => { cs.cssText = 'color: lime'; }]]) {
  try { fn(); row(label, '예외 없음', '되읽기 ' + J(cs.color)); }
  catch (e) { row(label, '예외 ' + e.name, '되읽기 ' + J(cs.color)); }
}
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-two.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
값이 온 곳이 넷인데 el.style 은 그중 하나만 본다
값이 어디서 왔나                  el.style                        getComputedStyle
인라인 style 의 color             "red"                           "rgb(255, 0, 0)"
스타일시트의 font-size            ""                              "21px"
부모에게서 상속된 color           ""                              "rgb(0, 128, 0)"
아무도 안 준 display              ""                              "block"
시트의 !important 가 이긴 color   "red"                           "rgb(0, 0, 255)"
커스텀 속성 --tone                ""                              "진하게"
(exit 0)
```

- **인라인만 왼쪽에 보인다.** 시트도, 상속된 것도, 아무도 안 준 기본값도 `el.style` 에는 없다.
- ★ **다섯째 줄이 가장 중요하다** — 인라인에 `color: red` 를 썼는데 시트의 `!important` 가 이겨서 **계산값은 파랑**이다. **`el.style` 만 보면 「내가 빨강을 썼으니 빨강이겠지」로 오진**한다.
- **커스텀 속성도 상속돼 온다** — `--tone` 이 `getComputedStyle` 쪽에만 보인다. 다만 **커스텀 속성의 값 처리는 보통 속성과 다르다**(정본: [CSS 36번 주제](../../languages/css/syntax/36-custom-properties/2-summary.md)).
- **값의 모양도 다르다** — 인라인은 쓴 글자 `"red"`, 계산값은 **`"rgb(255, 0, 0)"`**. 계산값은 **정규화된 형식**으로 온다.

```text
   질문                               창구
   '내가 이 요소에 직접 뭘 썼나'      el.style           (07번)
   '지금 실제로 무슨 값인가'           getComputedStyle   (이 주제)
   '그래서 화면에 어떤 상자가 놓였나'  getBoundingClientRect  (창 ④ · 09번)
```

비용 — `el.style` 은 그냥 읽기다. `getComputedStyle` 은 **스타일을 다시 계산해야 할 수도** 있다(아래 (10)).

### (3) 돌려받은 객체 — 같은 타입인데 읽기 전용이다

**언제 쓰나** — 계산값을 「고쳐서 돌려주려」 할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-two.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,18p'
돌려받은 객체의 성질 — el.style 과 무엇이 다른가
무슨 객체인가                     CSSStyleDeclaration             CSSStyleDeclaration
선언 개수 length                  computed = 475                  inline = 1
cssText                           ""                              (inline 은 "color: red;")
getPropertyValue 와 카멜          "16px"  "16px"
cs.color = 'lime'                 예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
cs.setProperty('color','lime')    예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
cs.removeProperty('color')        예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
cs.cssText = 'color: lime'        예외 NoModificationAllowedError 되읽기 "rgb(255, 0, 0)"
(exit 0)
```

- **타입이 `el.style` 과 똑같이 `CSSStyleDeclaration`** 이다. 그런데 **쓰려고 하면 네 창구 모두 `NoModificationAllowedError`** 를 던진다.
- ★ **여기는 조용하지 않다.** [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 `el.style` 은 거의 전부 조용히 버렸는데, **읽기 전용 위반은 예외**다.
- **`length` 가 475**(다음 실험에서는 476 — **커스텀 속성이 하나 늘었기 때문**)이고 **`cssText` 는 빈 문자열**이다. 「전부 있는데 통째로는 못 뽑는다」는 모양이다.
- **고치고 싶으면 `el.style` 에 쓴다.** 계산값은 결과이지 입력이 아니다.

비용 — 없다. 다만 **`cssText` 가 비었다고 「값이 없다」로 읽으면 안 된다.**

### (4) 읽는 문법이 셋이다

**언제 쓰나** — 속성 이름을 코드에 적을 때.

**던진 것** — 아래 (5)·(6)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa06b-08-read.html -->
<!doctype html>
<meta charset="utf-8">
<title>08-read</title>
<style>
  #host { width: 400px; font-size: 20px }
  #kid  { width: 50%; padding: 3em 1em; margin: 4px 8px; --tone: 진하게;
          background: rgb(0, 128, 0) none repeat scroll 0% 0%; border: 2px dashed red }
</style>
<div id="host"><div id="kid">잰다</div></div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push((padw(a, 34) + padw(b, 30) + (c === undefined ? '' : c)).replace(/ +$/, ''));
const kid = document.getElementById('kid');
const cs = getComputedStyle(kid);

O.push('읽는 문법이 셋이다 — 같은 선언을 세 창구로 물었다');
row('무엇으로 물었나', '돌려받은 것', '판정');
row("cs.fontSize (카멜)", J(cs.fontSize));
row("cs.getPropertyValue('font-size')", J(cs.getPropertyValue('font-size')), '카멜과 같은가 ' + (cs.fontSize === cs.getPropertyValue('font-size')));
row("cs['font-size'] (케밥 대괄호)", J(cs['font-size']), '★ 이것도 된다');
row("cs.getPropertyValue('fontSize')", J(cs.getPropertyValue('fontSize')), '★ 카멜로 물으면 빈 문자열');
row("cs.fontsize (전부 소문자)", String(cs.fontsize), '프로퍼티가 없다');
row("cs.getPropertyValue('zzz')", J(cs.getPropertyValue('zzz')));
row("cs.getPropertyValue('--tone')", J(cs.getPropertyValue('--tone')), '커스텀 속성은 이 창구로만');
row("cs['--tone']", String(cs['--tone']), '★ 커스텀 속성은 대괄호로 안 읽힌다');
O.push('');

O.push('단축 속성을 물으면 — 목록에는 낱개로 담겨 있다');
row('무엇을 물었나', '돌려받은 것');
for (const p of ['margin', 'padding', 'border', 'borderTopWidth', 'background', 'font']) {
  row('cs.' + p, J(cs[p]));
}
row('인라인 쪽 kid.style.margin', J(kid.style.margin), '(시트에 쓴 것은 안 보인다)');
O.push('');

O.push('목록으로 읽으면 — el.style 과 크기가 다르다');
row('cs.length', String(cs.length), 'kid.style.length = ' + kid.style.length);
row('cs.item(0) · item(1) · item(2)', J(cs.item(0)) + ' ' + J(cs.item(1)) + ' ' + J(cs.item(2)));
row('목록에 단축 이름이 있나', String([...Array(cs.length).keys()].some(i => cs.item(i) === 'margin')),
    "'margin-top' 은 " + [...Array(cs.length).keys()].some(i => cs.item(i) === 'margin-top'));
row('목록에 --tone 이 있나', String([...Array(cs.length).keys()].some(i => cs.item(i) === '--tone')));
row('cs.cssText', J(cs.cssText), '(인라인은 ' + J(kid.style.cssText) + ')');
row('window.getComputedStyle 인가', String(window.getComputedStyle === getComputedStyle),
    'cs.parentRule = ' + String(cs.parentRule));
O.push('');

O.push('절대 단위로 바뀌어 나온다 — 어느 단계에서 바뀌는지는 CSS 04 가 정본이다');
row('시트에 쓴 선언', 'kid.style (인라인 창구)', 'getComputedStyle (해석값 창구)');
for (const [decl, prop] of [['width: 50%', 'width'], ['padding: 3em', 'paddingTop'],
     ['font-size (상속)', 'fontSize'], ['border: 2px dashed red', 'borderTopColor']]) {
  row(decl, J(kid.style[prop]), J(cs[prop]));
}
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-read.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,10p'
읽는 문법이 셋이다 — 같은 선언을 세 창구로 물었다
무엇으로 물었나                   돌려받은 것                   판정
cs.fontSize (카멜)                "20px"
cs.getPropertyValue('font-size')  "20px"                        카멜과 같은가 true
cs['font-size'] (케밥 대괄호)     "20px"                        ★ 이것도 된다
cs.getPropertyValue('fontSize')   ""                            ★ 카멜로 물으면 빈 문자열
cs.fontsize (전부 소문자)         undefined                     프로퍼티가 없다
cs.getPropertyValue('zzz')        ""
cs.getPropertyValue('--tone')     "진하게"                      커스텀 속성은 이 창구로만
cs['--tone']                      undefined                     ★ 커스텀 속성은 대괄호로 안 읽힌다
(exit 0)
```

- **카멜 프로퍼티**(`cs.fontSize`)와 **`getPropertyValue('font-size')`** 가 같은 값을 준다. ★ **대괄호에 케밥을 넣어도 된다**(`cs['font-size']`) — 카멜과 케밥 **둘 다 프로퍼티로 정의**돼 있기 때문이다.
- ★ **`getPropertyValue` 에는 케밥만 넣는다.** `getPropertyValue('fontSize')` 는 **예외가 아니라 빈 문자열**이다 — 없는 속성을 물은 것과 **구분이 안 된다**(`getPropertyValue('zzz')` 도 `""`).
- ★ **커스텀 속성은 `getPropertyValue` 로만** 읽힌다. `cs['--tone']` 은 `undefined` 다 — **카멜 매핑은 명세가 아는 속성에만** 만들어진다.
- **전부 소문자로 쓴 `cs.fontsize` 는 `undefined`** 다. 그런 프로퍼티가 없다.

```text
   읽는 창구            대상                  못 찾으면
   cs.fontSize          알려진 속성(카멜)      undefined
   cs['font-size']      알려진 속성(케밥)      undefined
   getPropertyValue()   케밥 + 커스텀 속성     ""       ★ 오타와 구분이 안 된다
```

비용 — 없다. **오타를 잡고 싶으면 카멜 프로퍼티를 쓴다**(`undefined` 가 나온다). **커스텀 속성을 읽으려면 `getPropertyValue` 를 쓴다.**

### (5) 목록으로 읽으면 — `el.style` 과 크기가 다르다

**언제 쓰나** — 「무엇이 담겨 있나」를 세어 볼 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-read.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '22,28p'
목록으로 읽으면 — el.style 과 크기가 다르다
cs.length                         476                           kid.style.length = 0
cs.item(0) · item(1) · item(2)    "accent-color" "align-content" "align-items"
목록에 단축 이름이 있나           false                         'margin-top' 은 true
목록에 --tone 이 있나             true
cs.cssText                        ""                            (인라인은 "")
window.getComputedStyle 인가      true                          cs.parentRule = null
(exit 0)
```

- **`length` 가 476, `el.style` 은 0** 이다. **`el.style.length` 는 「내가 쓴 선언 수**」이고 **`getComputedStyle().length` 는 「속성 전부**」다 — **이름이 같고 뜻이 전혀 다르다.**
- **목록은 알파벳 순**이고(`accent-color`·`align-content`·`align-items`), **단축 이름은 목록에 없다** — `margin` 은 없고 `margin-top` 은 있다. **담겨 있는 것은 낱개뿐**이다([07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 「담기는 것은 낱개」와 같은 규칙).
- ★ **커스텀 속성은 목록에 있다.** 그래서 문서마다 `length` 가 다르다 — 이 실험에서 476, 커스텀 속성이 없는 앞 실험에서 475 였다. **`length` 를 상수로 외우지 마라.**
- **`cssText` 는 빈 문자열**이고 **`parentRule` 은 `null`** 이다. **`window.getComputedStyle` 과 전역의 `getComputedStyle` 은 같은 함수**다(전역이 `window` 다).

**단축 속성을 물으면 되접어 준다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-read.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,20p'
단축 속성을 물으면 — 목록에는 낱개로 담겨 있다
무엇을 물었나                     돌려받은 것
cs.margin                         "4px 8px"
cs.padding                        "60px 20px"
cs.border                         "2px dashed rgb(255, 0, 0)"
cs.borderTopWidth                 "2px"
cs.background                     "rgb(0, 128, 0) none repeat scroll 0% 0% / auto padding-box border-box"
cs.font                           "20px \"Noto Sans CJK KR\""
인라인 쪽 kid.style.margin        ""                            (시트에 쓴 것은 안 보인다)
(exit 0)
```

- 목록에는 낱개만 있는데 **`cs.margin` 을 물으면 `"4px 8px"`** 이 온다. **읽을 때 낱개를 모아 되접는 것**이다.
- **`cs.background` 는 아홉 낱개를 전부 펼친 긴 문자열**이다 — 되접기가 항상 짧아지는 것은 아니다.
- ★ **`cs.font` 의 글꼴 이름은 이 머신의 것**이다(`"Noto Sans CJK KR"`). **다른 기계에서는 다른 글자**가 나온다 — 위 「흔들리는 칸」 표에 그렇게 선언해 두었다.

비용 — 속성 하나를 읽는 것과 단축을 읽는 것의 비용 차이는 **재지 않았다.**

### (6) 값이 절대 단위로 바뀌어 나온다 — 단계 이야기는 CSS 04 가 정본이다

**언제 쓰나** — 시트에 쓴 글자와 스크립트가 받는 글자를 견줄 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-read.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '30,35p'
절대 단위로 바뀌어 나온다 — 어느 단계에서 바뀌는지는 CSS 04 가 정본이다
시트에 쓴 선언                    kid.style (인라인 창구)       getComputedStyle (해석값 창구)
width: 50%                        ""                            "200px"
padding: 3em                      ""                            "60px"
font-size (상속)                  ""                            "20px"
border: 2px dashed red            ""                            "rgb(255, 0, 0)"
(exit 0)
```

- **왼쪽 칸이 이 주제가 읽을 곳**이다 — 시트로 준 것은 **`el.style` 에 하나도 안 보인다.**
- 오른쪽 칸은 **절대 단위로 바뀌어 나온다**(`50%` → `200px`, `3em` → `60px`, `red` → `rgb(255, 0, 0)`).
- ★ **어느 값이 어느 단계에서 픽셀이 되는지, `%` 가 무엇의 몇 %인지, `line-height: 1.5` 가 왜 함정인지는 전부 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)와 [CSS 33번 주제](../../languages/css/syntax/33-length-units/2-summary.md)가 정본이다.** 거기서 이미 실측했고 **여기서 다시 쓰지 않는다.**
- **여기서 가져갈 결론은 한 줄이다** — **돌려받는 것은 내가 쓴 글자가 아니다.** 그래서 **문자열 비교로 「내가 쓴 값이 들어갔나」를 판정하면 틀린다.**

비용 — 없다. **결론 한 줄과 링크가 이 절의 전부**다.

### (7) 상자가 없는 요소 — `display: none` 과 트리 밖은 다르다

**언제 쓰나** — 숨긴 요소나 아직 안 붙인 요소의 값을 읽을 때.

**던진 것** — 아래 (8)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa06b-08-none.html -->
<!doctype html>
<meta charset="utf-8">
<title>08-none</title>
<style>
  #host { width: 400px; font-size: 20px; color: rgb(0, 128, 0) }
  .probe { width: 50%; padding: 3em; transform: translateX(50%) }
  #gone { display: none }
  #deco::before { content: "표식"; color: rgb(0, 0, 255) }
  #deco::marker { color: rgb(255, 0, 255) }
</style>
<div id="host">
  <div id="shown" class="probe">보인다</div>
  <div id="gone" class="probe">안 보인다</div>
  <li id="deco">의사 요소가 붙은 것</li>
  <div id="pull">뗄 것</div>
</div>
<template id="tpl"><div class="probe">다른 문서에 있는 것</div></template>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push((padw(a, 28) + padw(b, 30) + (c === undefined ? '' : c)).replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const g = (el, p) => { try { return J(getComputedStyle(el)[p]); } catch (e) { return '예외 ' + e.name; } };

O.push('display:none 인 요소도 대답은 한다 — 대신 레이아웃이 필요한 칸만 원문으로 남는다');
row('프로퍼티', '보이는 요소', 'display:none 인 요소');
for (const p of ['color', 'fontSize', 'paddingTop', 'width', 'transform', 'display']) {
  row(p, g($('shown'), p), g($('gone'), p));
}
O.push('');

O.push('트리에 없는 요소에 물으면 — 여기가 이 갈래 고유의 자리다');
row('무엇에 물었나', 'color', 'width · display');
const 새것 = document.createElement('div'); 새것.className = 'probe';
row('createElement 만 한 것', g(새것, 'color'), g(새것, 'width') + ' · ' + g(새것, 'display'));
row('  getComputedStyle().length', String(getComputedStyle(새것).length), 'cssText = ' + J(getComputedStyle(새것).cssText));
const tplKid = $('tpl').content.querySelector('.probe');
row('template.content 안의 것', g(tplKid, 'color'), g(tplKid, 'width') + ' · ' + g(tplKid, 'display'));
row('  그 노드의 ownerDocument', String(tplKid.ownerDocument === document), 'isConnected = ' + tplKid.isConnected);
const pull = $('pull');
const 뗴기전 = g(pull, 'color');
pull.remove();
row('뗀 뒤 같은 노드', 뗴기전 + ' -> ' + g(pull, 'color'), g(pull, 'width') + ' · ' + g(pull, 'display'));
O.push('');

O.push('의사 요소 — 두 번째 인자로 묻는다');
const deco = $('deco');
const gp = (ps, p) => { try { return J(getComputedStyle(deco, ps)[p]); } catch (e) { return '예외 ' + e.name; } };
row('두 번째 인자', 'content', 'color');
for (const ps of ['::before', ':before', '::after', '::marker', '::first-line', '::zzz', 'before', '']) {
  row(J(ps), gp(ps, 'content'), gp(ps, 'color'));
}
row('(인자 없이 요소 자신)', g(deco, 'content'), g(deco, 'color'));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-none.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
display:none 인 요소도 대답은 한다 — 대신 레이아웃이 필요한 칸만 원문으로 남는다
프로퍼티                    보이는 요소                   display:none 인 요소
color                       "rgb(0, 128, 0)"              "rgb(0, 128, 0)"
fontSize                    "20px"                        "20px"
paddingTop                  "60px"                        "60px"
width                       "200px"                       "50%"
transform                   "matrix(1, 0, 0, 1, 160, 0)"  "none"
display                     "block"                       "none"
(exit 0)
```

- **`display: none` 인 요소도 대답은 한다.** `color`·`fontSize`·`paddingTop` 은 보이는 요소와 **같은 값**이다.
- ★ **레이아웃이 필요한 칸만 원문으로 남는다** — `width` 가 `"200px"` 이 아니라 **`"50%"`**, `transform` 이 **`"none"`** 이다. **상자가 없으면 사용값을 만들 수 없기 때문**이고, 그 규정의 정본은 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-none.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,16p'
트리에 없는 요소에 물으면 — 여기가 이 갈래 고유의 자리다
무엇에 물었나               color                         width · display
createElement 만 한 것      ""                            "" · ""
  getComputedStyle().length 0                             cssText = ""
template.content 안의 것    ""                            "" · ""
  그 노드의 ownerDocument   false                         isConnected = false
뗀 뒤 같은 노드             "rgb(0, 128, 0)" -> ""        "" · ""
(exit 0)
```

- ★ **트리 밖은 완전히 다르다** — `createElement` 만 한 요소, `template.content` 안의 요소, **트리에서 뗀 요소** 셋 다 **모든 값이 빈 문자열**이고 **`length` 가 0** 이다.
- **「뗀 뒤 같은 노드」 줄이 결정적**이다 — 붙어 있을 때 `"rgb(0, 128, 0)"` 을 주던 바로 그 노드가 떼자 `""` 를 준다. **노드가 바뀐 게 아니라 연결이 끊긴 것**이다.
- ★ **그래서 「`display:none` 이면 값이 안 나온다」는 틀렸다.** 둘은 다르다.

```text
   무엇                          getComputedStyle 의 대답
   보이는 요소                   전부 · width 는 사용값 (200px)
   display: none                 전부 · width 는 계산값 (50%) · transform 은 none
   트리 밖 (createElement·뗀 것) ★ 전부 빈 문자열 · length = 0
   다른 문서 (template.content)  ★ 전부 빈 문자열 · length = 0
```

비용 — 없다. 다만 **초기화 코드에서 아직 안 붙인 요소의 계산값을 읽으면 빈 문자열이 온다** — 그 값을 수치로 파싱하면 `NaN` 이 되어 뒤에서 터진다.

### (8) 의사 요소 — 두 번째 인자로 묻는다

**언제 쓰나** — `::before`/`::after` 가 실제로 무엇이 됐는지 확인할 때. **이것 말고 방법이 없다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-none.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '18,28p'
의사 요소 — 두 번째 인자로 묻는다
두 번째 인자                content                       color
"::before"                  "\"표식\""                    "rgb(0, 0, 255)"
":before"                   "\"표식\""                    "rgb(0, 0, 255)"
"::after"                   "none"                        "rgb(0, 128, 0)"
"::marker"                  "normal"                      "rgb(255, 0, 255)"
"::first-line"              "normal"                      "rgb(0, 128, 0)"
"::zzz"                     ""                            ""
"before"                    "\"표식\""                    "rgb(0, 0, 255)"
""                          "normal"                      "rgb(0, 128, 0)"
(인자 없이 요소 자신)       "normal"                      "rgb(0, 128, 0)"
(exit 0)
```

- **`'::before'` 와 `':before'` 가 같은 답**을 준다 — 옛 한 콜론 표기도 받는다.
- ★ **콜론이 아예 없어도 된다** — `'before'` 가 `'::before'` 와 **같은 답**을 줬다. 명세가 접두 콜론을 벗겨 내고 이름만 본다.
- **`'::after'` 는 `content` 가 `"none"`** 이다 — 규칙을 안 줬기 때문이다. ★ **`::before`/`::after` 에서 `content` 의 초깃값이 `normal` 이 아니라 `none` 으로 계산된다**(정본: [CSS 13번 주제](../../languages/css/syntax/13-pseudo-elements-and-generated-content/2-summary.md)).
- **모르는 의사 요소(`'::zzz'`)는 예외가 아니라 빈 문자열**을 준다. **오타가 조용하다.**
- **두 번째 인자를 빼거나 `''` 를 주면 요소 자신**을 읽는다 — `content` 가 `"normal"`, `color` 가 요소의 것이다. ★ **인자를 빼먹으면 다른 것을 읽는데 에러가 없다.**
- ★ **계산값이 나온다고 의사 요소가 존재하는 것은 아니다.** 그 함정의 정본도 [CSS 13번 주제](../../languages/css/syntax/13-pseudo-elements-and-generated-content/2-summary.md)다 — 거기서 **`content: none` 인데도 `width` 가 계산되는** 실측을 했다.

비용 — 없다. 다만 **오타 진단이 없으므로 이름을 상수로 두는 편이 낫다.**

### (9) 라이브인가 스냅숏인가 — 둘 다다

**언제 쓰나** — 계산값 객체를 변수에 담아 두고 쓸 때.

**던진 것**

```html
<!-- wa06b-08-live.html -->
<!doctype html>
<meta charset="utf-8">
<title>08-live</title>
<style>#a { color: rgb(0, 128, 0) } .narrow { width: 100px } .wide { width: 300px }</style>
<div id="a" class="narrow">잡아 둘 것</div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c) => O.push((padw(a, 30) + padw(b, 26) + (c === undefined ? '' : c)).replace(/ +$/, ''));
const a = document.getElementById('a');
const cs1 = getComputedStyle(a), cs2 = getComputedStyle(a);

O.push('라이브인가 스냅숏인가 — 02번의 물음을 CSSOM 에 겹친다');
row('같은 요소로 두 번 부르면', 'cs1 === cs2 가 ' + (cs1 === cs2));
row('el.style 은', 'a.style === a.style 가 ' + (a.style === a.style));
row('잡아 둘 때 cs1.color · width', J(cs1.color), J(cs1.width));
a.style.color = 'rgb(255, 0, 0)';
row("a.style.color 를 바꾼 뒤", J(cs1.color), '잡아 둔 객체가 바뀌었다');
a.classList.replace('narrow', 'wide');
row('class 를 갈아 폭을 바꾼 뒤', J(cs1.width), '(시트 쪽 변경도 따라온다)');
row('새로 부른 것과 같은가', J(getComputedStyle(a).width), String(getComputedStyle(a).width === cs1.width));
O.push('');

O.push('잡아 둔 객체는 요소를 따라다닌다 — 요소가 트리를 떠나도');
row('떼기 전 cs1.color · width', J(cs1.color), J(cs1.width));
a.remove();
row('a.remove() 뒤 같은 cs1', J(cs1.color), J(cs1.width));
row('  cs1.length', String(cs1.length), 'a.isConnected = ' + a.isConnected);
document.body.appendChild(a);
row('다시 붙인 뒤 같은 cs1', J(cs1.color), J(cs1.width));
row('  cs1 === 처음 잡은 그 객체', String(cs1 === cs2), '(부른 자리마다 새 객체다)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-live.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
라이브인가 스냅숏인가 — 02번의 물음을 CSSOM 에 겹친다
같은 요소로 두 번 부르면      cs1 === cs2 가 false
el.style 은                   a.style === a.style 가 true
잡아 둘 때 cs1.color · width  "rgb(0, 128, 0)"          "100px"
a.style.color 를 바꾼 뒤      "rgb(255, 0, 0)"          잡아 둔 객체가 바뀌었다
class 를 갈아 폭을 바꾼 뒤    "300px"                   (시트 쪽 변경도 따라온다)
새로 부른 것과 같은가         "300px"                   true
(exit 0)
```

- ★ **객체는 부를 때마다 새것**이다(`cs1 === cs2` 가 `false`). **`el.style` 은 반대**다(`a.style === a.style` 이 `true`).
- ★ **그런데 값은 라이브**다 — 잡아 둔 `cs1` 이 **인라인 변경도, `class` 를 갈아 시트 쪽이 바뀐 것도** 따라온다. **스냅숏이 아니다.**
- 「새 객체인데 라이브」가 모순처럼 보이지만 아니다 — **객체는 「이 요소의 계산값을 보는 창**」이고, 창을 새로 내도 보이는 것은 같다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-live.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,14p'
잡아 둔 객체는 요소를 따라다닌다 — 요소가 트리를 떠나도
떼기 전 cs1.color · width     "rgb(255, 0, 0)"          "300px"
a.remove() 뒤 같은 cs1        ""                        ""
  cs1.length                  0                         a.isConnected = false
다시 붙인 뒤 같은 cs1         "rgb(255, 0, 0)"          "300px"
  cs1 === 처음 잡은 그 객체   false                     (부른 자리마다 새 객체다)
(exit 0)
```

- **요소를 떼면 같은 `cs1` 이 빈 문자열을 주고 `length` 가 0 이 된다.** (7)에서 본 「트리 밖」과 같다.
- ★ **다시 붙이면 값이 돌아온다.** 객체가 죽은 것이 아니라 **요소를 계속 따라다니고 있었다.**
- **값을 붙들어 두려면 문자열로 복사한다** — `const w = cs.width;` 처럼.

```text
   el.style                       getComputedStyle(el)
   같은 객체 (=== 가 true)        부를 때마다 새 객체 (=== 가 false)
   내가 쓴 것만                   전부
   쓸 수 있다                     읽기 전용 (NoModificationAllowedError)
   ───────────────── 둘 다 라이브다 ─────────────────
```

비용 — **객체를 잡아 두어도 읽기 비용이 안 줄어든다.** 비싼 것은 객체를 만드는 것이 아니라 **값을 읽는 것**이다(아래 (10)).

### (10) ★ 창 ④ — 계산값 옆에 실제 상자를 나란히 둔다

**언제 쓰나** — 계산값을 읽고 「그럼 화면도 그렇겠지」로 넘어가기 직전에.

**던진 것** — 이 절의 블록 셋이 같은 실행에서 나왔다.

```html
<!-- wa06b-08-used.html -->
<!doctype html>
<meta charset="utf-8">
<title>08-used</title>
<style>
  #host { width: 400px; font-size: 20px }
  .box  { width: 200px; height: 40px; padding: 10px; border: 5px solid black }
  #cb   { box-sizing: content-box }
  #bb   { box-sizing: border-box }
  #sc   { transform: scale(2) }
  #gone { display: none }
  #bar  { display: flex; width: 200px }
  #bar > div { flex: 1 1 0 }
  #long { background: rgb(230, 230, 230) }
</style>
<div id="host">
  <div id="cb" class="box">content-box</div>
  <div id="bb" class="box">border-box</div>
  <div id="sc" class="box">scale(2)</div>
  <div id="gone" class="box">display:none</div>
  <div id="bar"><div id="long">Supercalifragilisticexpialidocious</div><div id="rest">rest</div></div>
</div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (a, b, c, d) => O.push((padw(a, 30) + padw(b, 20) + padw(c === undefined ? '' : c, 14)
                                   + (d === undefined ? '' : d)).replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const F = n => Number.isFinite(n) ? n.toFixed(2) : String(n);

O.push('창 ④ — 계산값 옆에 실제 상자를 나란히 둔다');
row('무엇을', 'cs.width', 'rect.width', '무엇이 갈랐나');
row('#cb  box-sizing 기본', J(getComputedStyle($('cb')).width), F($('cb').getBoundingClientRect().width), '테두리·여백이 밖으로');
row('#bb  border-box', J(getComputedStyle($('bb')).width), F($('bb').getBoundingClientRect().width), '테두리·여백이 안으로');
row('#sc  transform: scale(2)', J(getComputedStyle($('sc')).width), F($('sc').getBoundingClientRect().width), 'transform 이 안 섞인다');
row('#gone  display: none', J(getComputedStyle($('gone')).width), F($('gone').getBoundingClientRect().width), '★ 상자가 아예 없다');
O.push('');

O.push('계산값이 한 글자도 안 바뀌는데 결과만 갈린다 — flex 항목의 min-width: auto');
const long = $('long'), rest = $('rest');
row('', 'cs.minWidth', 'cs.overflow', 'rect.width  (#long / #rest)');
const 찍기 = label => row(label, J(getComputedStyle(long).minWidth), J(getComputedStyle(long).overflow),
    F(long.getBoundingClientRect().width) + ' / ' + F(rest.getBoundingClientRect().width));
찍기('처음');
long.style.overflow = 'hidden';
찍기("style.overflow = 'hidden'");
long.style.overflow = '';
long.style.minWidth = '0';
찍기("style.minWidth = '0'");
O.push('');

O.push('트리 밖 · 다른 문서 — 계산값 창구가 아예 침묵한다');
row('무엇에 물었나', 'cs.width', 'cs.length', 'rect.width');
const 뗀것 = document.createElement('div'); 뗀것.className = 'box';
row('createElement 만 한 것', J(getComputedStyle(뗀것).width), String(getComputedStyle(뗀것).length),
    F(뗀것.getBoundingClientRect().width));
const cb = $('cb');
const 전 = J(getComputedStyle(cb).width);
cb.remove();
row('붙어 있다가 뗀 것', 전 + ' -> ' + J(getComputedStyle(cb).width), String(getComputedStyle(cb).length),
    F(cb.getBoundingClientRect().width));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-used.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
창 ④ — 계산값 옆에 실제 상자를 나란히 둔다
무엇을                        cs.width            rect.width    무엇이 갈랐나
#cb  box-sizing 기본          "200px"             230.00        테두리·여백이 밖으로
#bb  border-box               "200px"             200.00        테두리·여백이 안으로
#sc  transform: scale(2)      "200px"             460.00        transform 이 안 섞인다
#gone  display: none          "200px"             0.00          ★ 상자가 아예 없다
(exit 0)
```

- **세 줄 전부 `cs.width` 가 `"200px"` 로 같은데 실제 상자는 230 / 200 / 460** 이다.
- **`box-sizing`** — `cs.width` 는 **콘텐츠 상자**를 답한다. 테두리·안쪽 여백이 밖으로 나가면 상자가 커지고(230), 안으로 들어가면 같아진다(200).
- ★ **`transform` 은 계산값에 안 섞인다.** `scale(2)` 인데 `cs.width` 는 `"200px"` 이고 상자는 460 이다(200 + 테두리·여백 30 을 두 배).
- ★ **`display: none` 이면 상자가 아예 없다**(0). 계산값은 `"200px"` 이라고 답하는데 화면에는 아무것도 없다.

**그리고 계산값이 한 글자도 안 바뀌는데 결과만 갈리는 자리가 있다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-used.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,12p'
계산값이 한 글자도 안 바뀌는데 결과만 갈린다 — flex 항목의 min-width: auto
                              cs.minWidth         cs.overflow   rect.width  (#long / #rest)
처음                          "auto"              "visible"     307.19 / 35.09
style.overflow = 'hidden'     "auto"              "hidden"      100.00 / 100.00
style.minWidth = '0'          "0px"               "visible"     100.00 / 100.00
(exit 0)
```

- flex 항목의 **`min-width: auto`** 는 「내용보다 작아지지 마라」를 뜻한다. 그래서 긴 낱말이 든 항목이 **307.19px** 을 차지하고 옆 항목이 35.09 로 밀렸다.
- ★ **`overflow: hidden` 을 주면 그 규칙이 꺼진다** — 상자가 **100 / 100** 으로 균등해진다. 그런데 **`cs.minWidth` 는 여전히 `"auto"`** 다. **계산값은 한 글자도 안 바뀌었다.**
- **`min-width: 0` 을 직접 주면** 계산값이 `"0px"` 로 바뀌고 상자도 100 이 된다. **같은 결과에 이르는 두 길인데 한쪽만 계산값에 흔적이 있다.**
- ★ 이것이 CSS 갈래가 말한 「**계산값은 무엇이 선언됐나를 말하지 무엇이 일어나나를 말하지 않는다**」의 실물이다. **창 ④ 없이는 못 잡는다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-used.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,17p'
트리 밖 · 다른 문서 — 계산값 창구가 아예 침묵한다
무엇에 물었나                 cs.width            cs.length     rect.width
createElement 만 한 것        ""                  0             0.00
붙어 있다가 뗀 것             "200px" -> ""       0             0.00
(exit 0)
```

- 트리 밖에서는 **두 창이 함께 침묵한다** — 계산값도 빈 문자열, 상자도 0. **여기서는 창 ④ 가 새 정보를 주지 않는다.**

비용 — `getBoundingClientRect()` 는 **레이아웃을 강제한다.** 진단에는 쓰되 **루프 안에서는 쓰지 마라**(아래).

### (11) ★ 비용 — 읽기가 쓰기와 섞이면 자릿수가 바뀐다

**언제 쓰나** — 계산값을 루프에서 읽을 때.

**던진 것** — 수치를 싣는 실험이므로 마크업을 그대로 남긴다.

```html
<!-- wa06b-08-cost.html -->
<!doctype html>
<meta charset="utf-8">
<title>08-cost</title>
<style>.row { width: 50%; padding: 2px }</style>
<div id="host"></div>
<script>
const N = 9, ROWS = 400, ITER = 2000;
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
const host = document.getElementById('host');
const rows = [];
for (let i = 0; i < ROWS; i++) {
  const d = document.createElement('div'); d.className = 'row'; d.textContent = i;
  host.appendChild(d); rows.push(d);
}
let sink = 0;
const bench = (label, fn) => {
  const t = [];
  for (let r = 0; r < N; r++) { const s = performance.now(); fn(r); t.push(performance.now() - s); }
  O.push(padw(label, 40) + '중앙값 ' + med(t).toFixed(2).padStart(8) + ' ms' +
         '   최소 ' + Math.min(...t).toFixed(2).padStart(8) + '   최대 ' + Math.max(...t).toFixed(2).padStart(8));
};

O.push('읽기와 쓰기를 섞으면 — ' + ROWS + '행 · ' + N + '판의 중앙값');
O.push('');
bench('쓰기·읽기 교차 (한 행마다 번갈아)', r => {
  for (const d of rows) { d.style.paddingLeft = (r % 2) + 'px'; sink += getComputedStyle(d).width.length; } });
bench('쓰기 다 하고 읽기 다 하기', r => {
  for (const d of rows) d.style.paddingLeft = (r % 2) + 'px';
  for (const d of rows) sink += getComputedStyle(d).width.length; });
bench('읽기만 (쓰기 없음)', () => {
  for (const d of rows) sink += getComputedStyle(d).width.length; });
bench('쓰기만 (읽기 없음)', r => {
  for (const d of rows) d.style.paddingLeft = (r % 2) + 'px'; });
O.push('');

O.push('무엇을 읽느냐가 가른다 — 쓰기 뒤에 ' + ITER + '번 읽는다');
O.push('');
const one = rows[0];
bench('쓰고 cs.color 읽기 (계산값)', r => {
  for (let i = 0; i < ITER; i++) { one.style.marginLeft = (i % 2) + 'px'; sink += getComputedStyle(one).color.length; } });
bench('쓰고 cs.width 읽기 (사용값)', r => {
  for (let i = 0; i < ITER; i++) { one.style.marginLeft = (i % 2) + 'px'; sink += getComputedStyle(one).width.length; } });
bench('쓰고 getComputedStyle 만 부르기', r => {
  for (let i = 0; i < ITER; i++) { one.style.marginLeft = (i % 2) + 'px'; sink += getComputedStyle(one) ? 1 : 0; } });
bench('쓰기 없이 cs.width 만 읽기', () => {
  for (let i = 0; i < ITER; i++) sink += getComputedStyle(one).width.length; });
O.push('');
O.push('sink = ' + (sink > 0) + '   (읽은 값을 버리지 않았다는 확인)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
읽기와 쓰기를 섞으면 — 400행 · 9판의 중앙값

쓰기·읽기 교차 (한 행마다 번갈아)       중앙값    57.00 ms   최소    53.20   최대    97.80
쓰기 다 하고 읽기 다 하기               중앙값     3.00 ms   최소     0.70   최대     5.10
읽기만 (쓰기 없음)                      중앙값     1.10 ms   최소     0.60   최대     1.60
쓰기만 (읽기 없음)                      중앙값     0.10 ms   최소     0.10   최대     0.20
(exit 0)
```

- **읽기만 하면 1.10ms, 쓰기만 하면 0.10ms 인데 둘을 한 행마다 번갈아 하면 57.00ms** 다. **자릿수가 하나 넘게 바뀐다.**
- **같은 횟수의 쓰기와 읽기를 「전부 쓰고 나서 전부 읽기」로 묶으면 3.00ms** 다. **쓰기·읽기 횟수는 같은데 순서만 바꿨다.**
- ★ **비싼 것은 읽기도 쓰기도 아니라 「섞는 것**」이다. 쓰기가 레이아웃을 더럽히고, 읽기가 그것을 **동기적으로 다시 계산하게** 만든다.
- **신호 대 잡음** — 교차 조건과 묶음 조건이 **한 자릿수 이상** 차이라 신호가 압도적이다. **이 비교만 결론으로 쓴다.**

**무엇을 읽느냐도 가른다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom wa06b-08-cost.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,15p'
무엇을 읽느냐가 가른다 — 쓰기 뒤에 2000번 읽는다

쓰고 cs.color 읽기 (계산값)             중앙값     7.80 ms   최소     6.90   최대     9.50
쓰고 cs.width 읽기 (사용값)             중앙값   242.50 ms   최소   198.20   최대   250.60
쓰고 getComputedStyle 만 부르기         중앙값     0.70 ms   최소     0.70   최대     1.00
쓰기 없이 cs.width 만 읽기              중앙값     2.50 ms   최소     2.20   최대     2.80

sink = true   (읽은 값을 버리지 않았다는 확인)
(exit 0)
```

- **`getComputedStyle(el)` 을 부르기만 하면 0.70ms** — 객체를 만드는 것은 거의 공짜다.
- **거기서 `color` 를 읽으면 7.80ms**, **`width` 를 읽으면 242.50ms** 다. **30배 가까이**다.
- ★ **`color` 는 레이아웃이 필요 없고 `width` 는 필요하다.** 「계산값을 읽는다」가 한 가지 일이 아니라는 뜻이다 — **어느 속성이 레이아웃을 거치는지가 비용을 정한다**(그 구분의 정본은 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)의 ②/③ 경계다).
- **쓰기 없이 `width` 만 2000번 읽으면 2.50ms** — 레이아웃이 안 더러우면 다시 계산할 것이 없다.
- ★ **`performance.now()` 의 분해능은 100마이크로초**다. 「쓰기만」 줄의 `0.10`\~`0.20` 은 **분해능 한두 칸**이라 「공짜」가 아니라 「**이 도구로는 못 잰다**」로 읽는다. **그 줄로는 순위를 주장하지 않는다.**
- **이 절이 [목록의 10번 주제](../10-layout-thrashing/)(레이아웃 스래싱)의 씨앗**이다. 고치는 법(읽기 묶음과 쓰기 묶음으로 가르기)은 그쪽이 정본이다.

비용 — 이 절 자체가 비용이다. **9판·중앙값·최소·최대**를 실었고 **자릿수와 순위만 결론으로** 쓴다.

```html demo
<p id="d8p">스타일시트가 칠한 글</p>
<button id="d8b">인라인으로 한 줄 쓰기</button>
<div id="d8out"></div>
<style>
  #d8p { color: rgb(0, 128, 0); font-size: 21px; }
  #d8out { font-family: monospace; background: #0f172a; color: #e2e8f0; padding: 8px; margin-top: 6px; white-space: pre; }
</style>
<script>
  const p = document.getElementById('d8p');
  const 보이기 = () => document.getElementById('d8out').textContent =
    'p.style.color            = ' + JSON.stringify(p.style.color) +
    '\ngetComputedStyle().color = ' + JSON.stringify(getComputedStyle(p).color) +
    '\np.style.length = ' + p.style.length + '   getComputedStyle().length = ' + getComputedStyle(p).length;
  document.getElementById('d8b').onclick = () => { p.style.color = 'rgb(220, 38, 38)'; 보이기(); };
  보이기();
</script>
```

> **보이는 것** — 글씨는 초록인데 검은 칸의 첫 줄 **`p.style.color` 는 빈 문자열**이고 둘째 줄 `getComputedStyle().color` 만 `"rgb(0, 128, 0)"` 이다. 셋째 줄은 **`p.style.length = 0`** 과 세 자리 수인 `getComputedStyle().length` 를 나란히 보여 준다.\
> 버튼을 누르면 글씨가 빨개지고 **두 줄이 같아진다** — 그제야 `p.style.color` 에 값이 생기고 `p.style.length` 가 **1** 이 된다. 오른쪽 `length` 는 **한 글자도 안 바뀐다.**\
> **바꿔 볼 것** — `p.style.color` 를 `p.style.colour`(영국식 철자)로 바꿔 보라(**아무 일도 안 일어나고 에러도 없다** — [07번 주제](../07-dataset-classlist-inline-style/2-summary.md)의 「조용히 버려짐」이다) · `getComputedStyle(p).color = 'blue'` 를 콘솔에서 던져 보라(`NoModificationAllowedError`) · `getComputedStyle(p, '::first-line').color` 를 읽어 보라(두 번째 인자가 있다).

*(Chrome 151 headless 실측: 초기 상태에서 `p.style.color` `""` · `getComputedStyle().color` `"rgb(0, 128, 0)"` · `p.style.length` 0 · `getComputedStyle().length` 475, 버튼 뒤 `p.style.color` `"rgb(220, 38, 38)"` · 계산값 동일 · `p.style.length` 1 · 계산값 `length` 475 그대로)*

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
getComputedStyle(el)                 // window.getComputedStyle 과 같다
getComputedStyle(el, '::before')     // 두 번째 인자는 의사 요소
getComputedStyle(el, null)           // 요소 자신 (인자를 뺀 것과 같다)

const cs = getComputedStyle(el);
cs.fontSize                          // 카멜
cs['font-size']                      // 케밥도 된다
cs.getPropertyValue('font-size')     // 케밥만
cs.getPropertyValue('--tone')        // 커스텀 속성은 이쪽으로만
cs.getPropertyPriority('color')      // 계산값에서는 언제나 ''
cs.length   cs.item(0)               // 속성 전부 (알파벳 순 · 낱개만)
cs.cssText                           // 빈 문자열
cs.parentRule                        // null
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// 1. 계산값에 쓰려고 한다 — 예외
getComputedStyle(el).color = 'red';       // NoModificationAllowedError
el.style.color = 'red';                   // 이것이 맞다

// 2. getPropertyValue 에 카멜을 넣는다 — 조용히 빈 문자열
cs.getPropertyValue('fontSize');          // "" (오타와 구분이 안 된다)
cs.getPropertyValue('font-size');         // 이것이 맞다

// 3. 커스텀 속성을 대괄호로 읽는다 — undefined
cs['--tone'];                              // undefined
cs.getPropertyValue('--tone');             // 이것이 맞다

// 4. 내가 쓴 글자와 비교한다 — 정규화돼서 온다
if (cs.color === 'red') { }                // 영영 거짓 ("rgb(255, 0, 0)" 이다)
if (cs.width === '50%') { }                // 렌더된 요소에서는 거짓 ("200px")

// 5. 아직 안 붙인 요소에서 읽는다 — 빈 문자열
const d = document.createElement('div');
parseFloat(getComputedStyle(d).width);     // NaN

// 6. 의사 요소 인자를 빼먹는다 — 요소 자신을 읽는다
getComputedStyle(el).content;              // "normal" (요소의 것)
getComputedStyle(el, '::before').content;  // 이것이 맞다

// 7. 루프에서 쓰기와 읽기를 번갈아 한다 — 자릿수가 바뀐다
for (const d of rows) { d.style.paddingLeft = '1px'; sink += getComputedStyle(d).width; }
```

### 어디서 헷갈리나

- **이름이 거짓말이다** — 돌려받는 것이 언제나 「계산값」이 아니다. 명세 용어는 **해석값(resolved value)** 이고 속성마다 **계산값일 때와 사용값일 때**가 있다(정본: [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)).
- **`length` 의 뜻이 `el.style` 과 정반대**다 — 이쪽은 「전부」, 저쪽은 「내가 쓴 것」.
- **객체는 새것인데 값은 라이브**다. 둘을 한 문장으로 붙여 외운다.
- **`display: none` 과 「트리 밖」은 다르다.** 앞은 대답하고 뒤는 침묵한다.

## 어디서 틀리나

### 1. `el.style` 을 찍어 보고 「스타일이 없다」고 오진한다

시트로 칠한 요소의 `el.style.length` 는 **0** 이다. 「지금 무슨 값인가」는 이 주제의 창구로 물어야 한다.

### 2. 계산값 문자열을 내가 쓴 글자와 비교한다

`"red"` 로 썼어도 `"rgb(255, 0, 0)"` 이 온다. 색·길이·`transform` 이 전부 **정규화된 형식**으로 온다. 실측에서 `translateX(50%)` 가 **`matrix(1, 0, 0, 1, 160, 0)`** 이었다.

### 3. 아직 안 붙인 요소의 계산값을 읽는다

`createElement` 만 한 요소·`template.content` 안의 요소·뗀 요소 모두 **모든 값이 빈 문자열**이고 `length` 가 0 이다. `parseFloat` 하면 `NaN` 이다.

### 4. `display: none` 도 같은 줄 알고 넘어간다

숨긴 요소는 **대답한다.** 다만 `width` 가 `"50%"`, `transform` 이 `"none"` 처럼 **레이아웃이 필요한 칸만 원문으로 남는다.** 그 값을 픽셀로 알고 계산하면 틀린다.

### 5. 계산값이 같으면 화면도 같다고 믿는다

실측에서 **`min-width` 계산값이 `"auto"` 로 한 글자도 안 바뀌는데 상자가 307.19 에서 100 으로 바뀌었다.** 창 ④(`getBoundingClientRect`)로만 잡힌다.

### 6. 루프에서 읽기와 쓰기를 번갈아 한다

실측에서 **57.00ms 대 3.00ms** — 같은 횟수인데 순서만 다르다. 고치는 법은 [목록의 **10번 주제**](../10-layout-thrashing/)가 정본이다.

### 7. 의사 요소 이름을 틀리게 쓰고도 모른다

`'::zzz'` 는 **예외가 아니라 빈 문자열**이다. 두 번째 인자를 아예 빼면 **요소 자신을 읽는데** 그것도 조용하다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `getComputedStyle` 이 시트·상속·UA 기본값을 전부 반영한 값을 주는 것 | **명세**(CSSOM — resolved value) |
| 돌려받은 객체가 **읽기 전용**이고 쓰면 `NoModificationAllowedError` 인 것 | **명세**(CSSOM) |
| 부를 때마다 **새 객체**인데 값은 **라이브**인 것 | **명세**(CSSOM — live object) |
| **트리 밖 요소에 빈 문자열을 주는 것** | **명세**(CSSOM — 요소가 렌더 트리에 없으면 계산 스타일이 없다) |
| `display: none` 에서 **해석값이 계산값으로 떨어지는 것** | **명세**(CSSOM) — 실측 근거는 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md) |
| 두 번째 인자로 의사 요소를 읽는 것 · 한 콜론도 받는 것 | **명세**(CSSOM) |
| 커스텀 속성이 `getPropertyValue` 로만 읽히는 것 | **명세**(CSSOM — 카멜 매핑은 알려진 속성에만) |
| 목록이 **낱개만** 담고 단축은 읽을 때 되접히는 것 | **명세**(CSSOM 직렬화) |
| **`length` 의 값**(475 · 476) | **구현** — Chrome 151 이 지원하는 속성 수 + 그 문서의 커스텀 속성 수. **상수로 쓰지 마라** |
| 목록이 알파벳 순인 것 | **명세**(CSSOM 이 순서를 정한다) **+ 구현**(어느 속성이 있나) |
| `cs.font` 의 글꼴 이름 | **이 머신의 글꼴 설정** |
| **모든 시간 수치** | **구현 + 머신 + 그 판의 부하.** 자릿수와 순위만 결론으로 쓴다 |
| `performance.now()` 의 분해능 100마이크로초 | **구현**(Blink 의 정책) |
| `min-width: auto` 가 `overflow` 에 따라 꺼지는 것 | **명세**(CSS Flexbox) — 여기서는 **창 ④ 의 예**로만 썼다 |

- ★ **「비싸다」는 것만은 명세가 보장하지 않는다.** 명세는 **무엇을 돌려주라**고 정하지 **얼마나 걸리는지**는 말하지 않는다. 이 문서의 시간 표는 **이 판·이 머신의 관찰**이다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 「지금 무슨 값인가」 | `getComputedStyle` | `el.style` |
| 「내가 이 요소에 뭘 썼나」 | `el.style`([07번 주제](../07-dataset-classlist-inline-style/2-summary.md)) | `getComputedStyle` |
| 값을 바꾼다 | `el.style` · 클래스 토글 | 계산값에 대입(예외다) |
| 커스텀 속성을 읽는다 | `cs.getPropertyValue('--x')` | `cs['--x']` |
| 의사 요소의 `content` 확인 | `getComputedStyle(el, '::before')` | 요소 자신 읽기 |
| 「화면에 어떤 상자가 놓였나」 | `getBoundingClientRect`([목록의 **09번 주제**](../09-element-geometry/)) | 계산값의 `width` |
| 요소가 보이는지 판정 | 상자 크기·`checkVisibility()` | `display` 계산값 하나 |
| 루프에서 여러 요소의 값을 읽는다 | 읽기를 **한 묶음으로** 모은다 | 쓰기와 번갈아([목록의 **10번 주제**](../10-layout-thrashing/)) |
| 테마 값을 읽는다 | 루트에서 커스텀 속성 한 번 읽고 **캐시** | 매 프레임 다시 읽기 |
| 아직 안 붙인 요소 | 붙이고 읽는다 | 그냥 읽기(빈 문자열이 온다) |

## 핵심 문장

1. **`el.style` 은 내가 쓴 것만, `getComputedStyle` 은 값이 온 곳 넷을 전부 본다** — 인라인·시트·상속·UA 기본값.
2. **돌려받는 것은 내가 쓴 글자가 아니다** — 정규화되고 절대 단위로 바뀐 **해석값**이다. **어느 단계의 값인지는 [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md)가 정본**이다.
3. **객체는 부를 때마다 새것인데 값은 라이브다.** 그리고 **읽기 전용**이다 — 쓰면 예외가 난다.
4. **`display: none` 은 대답하고, 트리 밖은 침묵한다.** 둘을 같은 것으로 읽지 마라.
5. **계산값이 같아도 화면은 다를 수 있다** — 창 ④(`getBoundingClientRect`)를 나란히 둬야 보인다.
6. **비싼 것은 읽기가 아니라 쓰기와 섞는 것이다.** 실측에서 같은 횟수인데 **57.00ms 대 3.00ms** 였다.
7. **무엇을 읽느냐도 가른다** — `color` 7.80ms 대 `width` 242.50ms. **레이아웃을 거치는 속성이 비싸다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 08번)
- [07번 주제](../07-dataset-classlist-inline-style/2-summary.md) — `el.style`. 「내가 쓴 것」 쪽 창구가 거기다. 이 주제는 **그것이 못 보는 것**부터
- [06번 주제](../06-attribute-vs-property/2-summary.md) — 속성과 성질. `style` 속성이 `el.style` 로 반영되는 자리
- [04번 주제](../04-textcontent-innerhtml-innertext/2-summary.md) — `performance.now()` 의 **분해능 100마이크로초** 실측. 이 주제가 그 한계를 물려받는다
- [목록의 **09번 주제**](../09-element-geometry/)(요소 기하) — 창 ④ 로 빌려 쓴 `getBoundingClientRect` 의 **정본**. 좌표계와 `offset*`/`client*`/`scroll*` 는 그쪽
- [목록의 **10번 주제**](../10-layout-thrashing/)(레이아웃 스래싱) — 이 주제의 (11)이 그 씨앗이다. **고치는 법**은 그쪽이 정본
- 목록의 **38번 주제**(`requestAnimationFrame` 과 프레임 예산) — 읽기·쓰기를 **언제** 묶나
- [CSS 04번 주제](../../languages/css/syntax/04-value-processing-stages/2-summary.md) — ★ **이 주제의 정본 이웃.** 지정값·계산값·사용값·실제값과 **`getComputedStyle` 이 어느 것을 주나**가 거기다. **여기서 다시 쓰지 않는다**
- [CSS 03번 주제](../../languages/css/syntax/03-inheritance-and-global-keywords/2-summary.md) — **상속되는 것은 계산값이다.** 이 주제가 「상속된 값도 나온다」로만 쓰는 것의 근거
- [CSS 33번 주제](../../languages/css/syntax/33-length-units/2-summary.md) — `em`·`%` 가 **무엇의 몇 %인가**. 절대화의 기준은 그쪽
- [CSS 13번 주제](../../languages/css/syntax/13-pseudo-elements-and-generated-content/2-summary.md) — 의사 요소. **`content` 가 `none` 으로 계산되는 것**과 「계산값이 나와도 존재하는 게 아니다」가 거기다
- [CSS 36번 주제](../../languages/css/syntax/36-custom-properties/2-summary.md) — 커스텀 속성의 값 처리. 여기는 **`getPropertyValue` 라는 창구**까지만
- [CSS 07번 주제](../../languages/css/syntax/07-syntax-and-error-recovery/2-summary.md) — **진단 3창의 정본.** 이 주제의 주인공이 그 셋째 창(이겼나)이다

## 용어 풀이

- **해석값(resolved value)** — `getComputedStyle` 이 돌려주는 것에 명세가 붙인 이름. **속성에 따라 계산값일 때와 사용값일 때가 있다.**
- **계산값(computed value)** — `em`·`thin`·`red` 같은 것이 절대화된 판. **상속되는 것이 이것**이다.
- **사용값(used value)** — `%`·`auto` 가 레이아웃으로 풀린 판. **상자가 있어야 존재한다.**
- **`CSSStyleDeclaration`** — `el.style` 과 `getComputedStyle` 이 공유하는 타입. **뒤엣것은 읽기 전용**이다.
- **읽기 전용 위반** — `NoModificationAllowedError`. **이 주제에서 유일하게 예외가 나는 자리**다.
- **라이브(live)** — 잡아 둔 객체가 나중 변경을 따라오는 것. 계산값 객체가 그렇다.
- **의사 요소(pseudo-element)** — `::before`·`::after`·`::marker` 처럼 마크업에 없는데 그려지는 상자.
- **낱개 속성(longhand)** — 목록에 담기는 것은 낱개뿐이다(`margin-top`).
- **정규화된 형식(serialization)** — 계산값이 오는 형식. `red` → `rgb(255, 0, 0)`, `translateX(50%)` → `matrix(…)`.
- **레이아웃 강제(forced synchronous layout)** — 쓰기로 더러워진 레이아웃을 읽기가 그 자리에서 다시 계산하게 만드는 것. **이 주제가 재는 비용의 원인**이다.
- **분해능(resolution)** — 측정 도구가 구분할 수 있는 최소 간격. 여기서는 100마이크로초.
- **중앙값(median)** — 여러 판을 크기순으로 늘어놓았을 때 가운데 값.

## 더 들어가면

- **`el.computedStyleMap()`**(Typed OM)은 계산값을 **문자열이 아니라 타입 붙은 객체**로 준다 — `el.computedStyleMap().get('width').value` 가 숫자 `200` 이다. 문자열을 `parseFloat` 하는 자리를 없앨 수 있지만 **Chromium 계열에만** 있어 이 목록에서는 다루지 않는다.
- **`el.checkVisibility()`** 는 「보이나」를 한 번에 판정한다 — `display: none` 인 조상, `visibility`, `content-visibility`, 빈 상자까지 본다. **계산값 하나로 판정하려던 자리**를 대신한다. (**이 문서는 던져 보지 않았다** — 표면만 적는다.)
- **`getComputedStyle` 의 두 번째 인자는 의사 요소만** 받는다. **의사 클래스(`:hover`)는 못 준다** — 상태를 시뮬레이션해 읽는 방법은 표준에 없고 개발자 도구의 기능이다.
- **스타일 재계산과 레이아웃은 다른 단계**다. (11)에서 `color` 읽기가 7.80ms, `width` 읽기가 242.50ms 로 갈린 것이 그 경계다 — 앞은 스타일 재계산까지, 뒤는 레이아웃까지 간다. 그 파이프라인 전체는 [목록의 **10번 주제**](../10-layout-thrashing/)와 [CSS 56번 주제](../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md)가 정본이다.
- **그림자 경계 안의 요소**도 `getComputedStyle` 로 읽을 수 있다 — 요소 참조만 있으면 된다. 다만 **`closed` 그림자는 참조를 얻을 길이 없다.** 그 경계는 [목록의 **12번 주제**](../12-shadow-dom/)다.
