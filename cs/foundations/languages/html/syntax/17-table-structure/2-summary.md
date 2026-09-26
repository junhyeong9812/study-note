# html/syntax/17 — 표 구조: `table`/`thead`/`tbody`/`tfoot`/`caption`/`colgroup` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [HTML 4.01 §11.2.1](https://www.w3.org/TR/html401/struct/tables.html)(옛 `tfoot` 위치 규칙 — 대조용) · [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Tabular data」](https://html.spec.whatwg.org/multipage/tables.html) 절(요소마다의 콘텐츠 모델 · `HTMLTableElement` 의 `rows`·`insertRow()` 단계 · 4.9.12 「표 처리 모델」)과 [파싱 절의 「in table」 삽입 모드](https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-intable), [렌더링 절 15.3.8 Tables](https://html.spec.whatwg.org/multipage/rendering.html#tables-2), [HTML-AAM](https://w3c.github.io/html-aam/)(편집본 — `table`·`caption`·`tbody` 의 역할과 「table 요소의 접근 가능한 이름 계산」), [CSS 2.1 §17.3 Columns](https://www.w3.org/TR/CSS2/tables.html#columns)(열에 적용되는 속성 넷). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 블록마다 던진 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다(캡처 조립기). 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다** — 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — HTML 에는 언어 버전이 없다. `api.webstatus.dev` 조회로 **「Tables」(`table`) 는 Baseline widely**(newly 2015-07-29 → widely 2018-01-29), **`display: table` 도 widely** 다. 이 주제의 표면은 전부 오래된 것이다 — **바뀌는 것은 표면이 아니라 파서·트리가 그 표면으로 만드는 것**이다.
> **선행** — [03번 주제](../03-parser-and-error-recovery/2-summary.md)(파서 오류 복구 — 이 주제의 `tbody` 삽입과 foster parenting 은 **그쪽 (2)·(3) 의 결론 위에 선다**)와 [05번 주제](../05-content-categories-and-models/2-summary.md)(콘텐츠 모델).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **본체는 창 ① `--dump-dom` 이다** — 표는 **소스에 쓴 것과 DOM 에 생긴 것이 가장 크게 갈리는 요소**다. 파서가 `tbody` 를 끼우고, 못 둘 것을 표 앞으로 빼낸다. 그 두 일은 **소스를 읽어서는 절대 안 보이고** 창 ① 로만 보인다. 창 ② 는 「그래서 화면 순서가 어떻게 되나」를, 창 ⑦ 은 「트리가 무엇을 남기나」를 잇는다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |
| **흔들린다** | CDP 가 쓰는 **포트 번호와 프로필 경로** | 실행마다 다르다 — **출력에는 안 들어간다** |
| **흔들린다(머신 사이)** | (4)·(7)·demo 의 **px 값**(셀 폭·셀 x·행의 top) | 설치된 글꼴에 매인다. 그래서 근거는 **절댓값이 아니라 「어느 쪽이 위인가」·「바뀌었나 안 바뀌었나」** 로 읽는다 |
| **안 흔들린다** | `--dump-dom` 의 트리 모양 · 표 앞으로 나간 것의 목록 | 파서는 결정적이다 |
| **안 흔들린다** | 역할·이름·설명·`nameFrom` · 행의 순서 | 같은 판이면 결정적이다 |
| **안 흔들린다** | 격자의 「**… = N / M**」 줄 | 스크립트가 센다 — 사람이 세지 않는다 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

실측 — 이 배치(17\~20)의 캡처 **61블록을 세 번 돌려 61블록 전부 한 글자도 같았다**(흔들린 칸 0 · 고칠 것 0). 같은 머신이라 px 칸도 안 움직였다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **① `--dump-dom`** | ★★★ **쓴다 — 본체** | 「파서가 무엇을 끼우고 무엇을 빼냈나」((1)·(2)) |
| **② 프로브**(DOM API · `getBoundingClientRect` · `getComputedStyle` · 픽셀) | ★ **쓴다** | 「스크립트 API 가 무엇을 세나」((3)) · 「화면에서 어느 행이 위인가」((4)) · 「`col` 의 속성이 셀에 닿나」((7)) |
| **⑦ 접근성 트리**(CDP + `chrome://accessibility` 내부 덤프) | ★ **쓴다** | 「표의 이름은 어디서 오나」((5)) · 「행 묶음이 트리에 남나」((6)) · 「트리의 행 순서」((4)) |
| **③ `innerText` 대 `textContent`** | **부적용** | 표 구조 요소는 글자를 만들지 않는다 — **잴 것이 없다** |
| **④ `compatMode`** | **부적용** | 문서 모드를 안 바꾼다 — **잴 것이 없다** |
| **⑤ 서버 요청 로그** | **부적용** | 요청을 일으키는 요소가 없다 — **잴 것이 없다** |
| **⑥ `renderBlockingStatus`** | **부적용** | 렌더를 막는 자원이 없다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「행의 순서는?」을 창 ① 에 물으면 **소스 순서**가, 창 ② 에 물으면 **화면 순서**가, `table.rows` 에 물으면 **IDL 이 정한 순서**가 나온다((4)). 셋 다 틀린 답이 아니다 — **창마다 다른 것을 잰다.** ★ 그리고 명세의 「표 처리 모델」이 매기는 순서는 **어느 창에도 직접 안 나온다** — 페이지 스크립트로 옮겨 계산했다. **그 계산 열도 창을 바꿔 물은 것**이다.
- ★ **창 ⑦ 은 이 배치에서 둘로 늘었다.** CDP `Accessibility.getFullAXTree` 에 더해 **`chrome://accessibility` 의 「blink」 내부 덤프**를 같은 브라우저에서 받는다 — CDP 에는 없는 **`nameFrom`(이름의 출처)** 과 **표 좌표(`tableRowIndex`·`tableCell*`)** 가 거기 있다. 하네스는 [3-answer.md](3-answer.md) 에 있다.

## 한눈에 — 쉽게 말하면

**★ 표는 서식 양식이다. 칸이 빠지면 파서가 채워 넣고, 칸에 못 쓸 낙서는 양식 바깥 여백으로 옮겨 적는다.**

관공서 **서식 양식**에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 서식 양식 한 장 | **`<table>`** |
| 양식 맨 위의 **제목란** | **`<caption>`** — 창 ⑦ 에서 **표의 이름**이 된다((5)) |
| 머리글 줄 · 본문 칸 묶음 · 합계 줄 | **`<thead>` · `<tbody>` · `<tfoot>`** — 행 묶음(row group) |
| 양식에 **본문 칸 묶음이 인쇄돼 있지 않으면** 직원이 그어 넣는다 | 파서가 **`<tbody>` 를 끼워 넣는다**((1)) |
| 칸 밖에 쓴 **낙서**를 양식 **위 여백**으로 옮겨 적는다 | **foster parenting** — 표 **앞**으로 빼낸다((1)·(2)) |
| 합계 줄을 먼저 써도 **양식 맨 아래**에 찍힌다 | `tfoot` 은 소스 앞에 써도 **화면 맨 아래**다((4)) |
| **세로 줄 전체에 색 띠**를 칠하는 투명 필름 | **`<col>`** — 칠·테두리·폭·접기 **넷만** 칸에 닿는다((7)) |

- **파서는 표를 고친다.** 소스에 `tbody` 를 안 써도 DOM 에는 있다. `table > tr` 선택자가 **0개**를 잡는다((3)).
- **표 안에 못 두는 것은 버리지 않고 표 앞으로 뺀다.** 14가지를 넣어 보니 **7가지가 나갔다**((2)).
- **행의 순서는 창마다 다르다.** DOM · `rows` · 화면 · 명세 표 모델 · 트리가 **넷이나 DOM 과 갈렸다**((4)).

```text
  소스에 쓴 것과 DOM 에 생긴 것 — 창 ① 로만 보인다

  소스                                          DOM (--dump-dom)
  ----                                          ----------------
  <table>                                       <div>div</div>글자       <- 표 앞으로 나왔다
    <div>div</div>글자                          <table>
    <tr><td>셀</td></tr>                          <tbody>                <- 안 쓴 것이 생겼다
  </table>                                          <tr><td>셀</td></tr>
                                                  </tbody>
                                                </table>
```

실무에서 이게 터지는 자리는 **표를 스크립트로 다루는 코드**다.\
`table.firstElementChild` 가 `tr` 이 아니라 `tbody` 이고, 서버 템플릿이 표 안에 끼운 스피너 `<div>` 가 **표 위에** 뜬다. 둘 다 **소스를 읽어서는 안 보인다.**

> **행 묶음(row group)** — `thead`·`tbody`·`tfoot` 이 묶는 행의 덩어리. 표 처리 모델의 용어다.\
> 예: 소스에 `tbody` 가 없어도 파서가 끼운 `tbody` 하나가 모든 `tr` 을 묶는다.

> **foster parenting** — 표 안에 올 수 없는 내용을 **표 바로 앞으로 옮겨 붙이는** 파서 동작. [03번 주제](../03-parser-and-error-recovery/2-summary.md) (3) 이 정본이다.\
> 예: `<table><div>x</div><tr>…` 의 `div` 가 `<table>` 앞으로 나간다.

## 이 주제가 답하려는 질문

1. **파서는 표를 어떻게 고치나** — 무엇을 끼우고, 무엇을 빼내고, 무엇을 그대로 두나. 그것이 스크립트 API 에 어떻게 비치나.
2. **행의 순서를 누가 정하나** — `thead` 를 뒤에, `tfoot` 을 앞에 쓰면 DOM·화면·트리가 같은 답을 하나.
3. **표의 이름과 열의 스타일은 어디서 오나** — `caption` 이 이름이 되는 조건과, `col` 이 셀에 닿는 속성의 범위.

## 동작 방식

### (1) 창 ① — 파서가 끼운 `tbody` 와 표 앞으로 나간 것

**언제 쓰나** — 이 주제의 본체. 「내가 쓴 표」와 「브라우저가 가진 표」가 **다르다**는 것을 처음 보는 자리다.

표 다섯 개를 **틀리게 또는 모자라게** 썼다 — `tbody` 없이 · 표 안에 `div` 와 글자 · 행 안에 글자와 `span` · 행 **뒤에** `caption` · `tr` 없이 `td` 만.

```html
<!-- html17b-17-parse.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 파서가 고친 표</title>
</head>
<body>
<table id="가"><tr><td>셀</td></tr></table>
<table id="나"><div id="div">div</div>글자<tr><td>셀</td></tr></table>
<table id="다"><tr><td>셀</td>꼬리<span id="span">span</span></tr></table>
<table id="라"><tr><td>셀</td></tr><caption id="cap">늦은 caption</caption></table>
<table id="마"><td>td 만</td></table>
</body>
</html>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-17-parse.html 2>/dev/null
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>17 파서가 고친 표</title>
</head>
<body>
<table id="가"><tbody><tr><td>셀</td></tr></tbody></table>
<div id="div">div</div>글자<table id="나"><tbody><tr><td>셀</td></tr></tbody></table>
꼬리<span id="span">span</span><table id="다"><tbody><tr><td>셀</td></tr></tbody></table>
<table id="라"><tbody><tr><td>셀</td></tr></tbody><caption id="cap">늦은 caption</caption></table>
<table id="마"><tbody><tr><td>td 만</td></tr></tbody></table>


</body></html>
(exit 0)
```

```text
  다섯 표 — 파서가 한 일

  #가  <tr><td>                     -> tbody 를 끼웠다
  #나  <div>div</div>글자 <tr>…     -> div 와 글자가 표 앞으로 · tbody 를 끼웠다
  #다  <tr><td>셀</td>꼬리<span>    -> tr 안에 있던 글자와 span 도 표 앞으로
  #라  … </tr><caption>             -> caption 은 옮기지 않았다 — tbody 뒤에 남았다
  #마  <td> 만                      -> tbody 와 tr 을 둘 다 끼웠다

  끼우기(삽입)와 빼내기(이동)는 파서의 일이다. 고치지 않은 것(#라)도 있다.
```

- ★★★ **소스에 없는 `<tbody>` 가 다섯 표 전부에 있다.** 「in table」 삽입 모드가 `td`·`th`·`tr` 시작 태그를 만나면 **`tbody` 를 먼저 넣고** 다시 처리한다 — [03번 주제](../03-parser-and-error-recovery/2-summary.md) (2) 의 결론이 그대로다. `#마` 는 **`tr` 까지** 끼워졌다(「in table body」 모드가 `td` 를 만나 `tr` 을 넣는다).
- ★★ **`#나`·`#다` 의 `div`·글자·`span` 이 표 앞으로 나갔다.** 「in table」 모드의 「그 밖의 모든 것」 줄이 **foster parenting 을 켜고 「in body」 규칙으로 처리**하기 때문이다 — [03번 주제](../03-parser-and-error-recovery/2-summary.md) (3) 의 결론. ★ **`tr` 안에 쓴 것도 나간다**(`#다` 의 「꼬리」). 표의 칸은 `td`·`th` 뿐이다.
- ★ **`#라` 의 `caption` 은 제자리에 남았다** — `tbody` **뒤에**. 콘텐츠 모델은 「`caption` 이 맨 앞」인데 **파서는 그 순서를 강제하지 않는다.** [05번 주제](../05-content-categories-and-models/2-summary.md) (4) 의 「파서가 안 고치는 것」과 같은 부류다. 이 `caption` 이 이름이 되는지는 (5) 가 판다.

### (2) 창 ① 격자 — 표 안에 열네 가지를 넣으면 몇 가지가 나가나

**언제 쓰나** — 「표 안에 뭘 넣으면 밖으로 나가나」를 **하나씩 외우지 않고** 규칙으로 읽는 자리.

표마다 **하나씩** 넣고, 그것이 **표 바로 앞 형제**가 됐는지 **표의 직속 자식**으로 남았는지 페이지 스크립트가 셌다.

```html
<!-- html17b-17-foster.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 표 안에 넣은 것</title>
</head>
<body>
<hr id="시작">
<table data-k="div"><div>x</div><tr><td>셀</td></tr></table>
<table data-k="span"><span>x</span><tr><td>셀</td></tr></table>
<table data-k="글자">x<tr><td>셀</td></tr></table>
<table data-k="공백"> <tr><td>셀</td></tr></table>
<table data-k="img"><img alt="x"><tr><td>셀</td></tr></table>
<table data-k="input text"><input type="text"><tr><td>셀</td></tr></table>
<table data-k="input hidden"><input type="hidden"><tr><td>셀</td></tr></table>
<table data-k="script"><script></script><tr><td>셀</td></tr></table>
<table data-k="style"><style></style><tr><td>셀</td></tr></table>
<table data-k="template"><template>x</template><tr><td>셀</td></tr></table>
<table data-k="form"><form><input name="q"></form><tr><td>셀</td></tr></table>
<table data-k="주석"><!-- x --><tr><td>셀</td></tr></table>
<table data-k="tr 안 div"><tr><div>x</div><td>셀</td></tr></table>
<table data-k="td 안 div"><tr><td><div>x</div></td></tr></table>
<script>
window.__대상 = [];
const 이름 = n => n.nodeType === 1 ? "<" + n.localName + (n.type && n.localName === "input" ? " " + n.type : "") + ">"
  : n.nodeType === 3 ? (n.data.trim() ? "글자" : "공백") : n.nodeType === 8 ? "주석" : "?";
window.__끝 = () => {
  const O = ["표 안에 쓴 것이 어디로 갔나 — 표 바로 앞 형제 / 표의 직속 자식(tbody 말고) / td 안"];
  let 나감 = 0, 전체 = 0;
  for (const t of document.querySelectorAll("table[data-k]")) {
    const 앞 = [];
    for (let n = t.previousSibling; n && !(n.nodeType === 1 && (n.localName === "table" || n.id === "시작")); n = n.previousSibling)
      if (!(n.nodeType === 3 && n.data === "\n")) 앞.unshift(이름(n));
    const 안 = [...t.childNodes].filter(n => !(n.nodeType === 1 && n.localName === "tbody")).map(이름);
    const td안 = [...t.querySelector("td").childNodes].map(이름);
    전체++; if (앞.length) 나감++;
    O.push("  " + t.dataset.k.padEnd(13) + "표 앞 = " + (앞.join(" ") || "—").padEnd(16)
      + "표 직속 = " + (안.join(" ") || "—").padEnd(18) + "td 안 = " + td안.join(" "));
  }
  const f = document.querySelector('table[data-k="form"]');
  const 입력 = f.previousElementSibling, 폼 = f.querySelector("form");
  O.push("");
  O.push("form 칸 — 표 앞으로 나간 input 의 .form 이 표 안에 남은 form 인가 = " + (입력.form === 폼)
    + " · form.elements.length = " + 폼.elements.length + " · form.childNodes.length = " + 폼.childNodes.length);
  O.push("");
  O.push("표 앞으로 나간 칸 = " + 나감 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-17-foster.html
표 안에 쓴 것이 어디로 갔나 — 표 바로 앞 형제 / 표의 직속 자식(tbody 말고) / td 안
  div          표 앞 = <div>           표 직속 = —                 td 안 = 글자
  span         표 앞 = <span>          표 직속 = —                 td 안 = 글자
  글자           표 앞 = 글자              표 직속 = —                 td 안 = 글자
  공백           표 앞 = —               표 직속 = 공백                td 안 = 글자
  img          표 앞 = <img>           표 직속 = —                 td 안 = 글자
  input text   표 앞 = <input text>    표 직속 = —                 td 안 = 글자
  input hidden 표 앞 = —               표 직속 = <input hidden>    td 안 = 글자
  script       표 앞 = —               표 직속 = <script>          td 안 = 글자
  style        표 앞 = —               표 직속 = <style>           td 안 = 글자
  template     표 앞 = —               표 직속 = <template>        td 안 = 글자
  form         표 앞 = <input text>    표 직속 = <form>            td 안 = 글자
  주석           표 앞 = —               표 직속 = 주석                td 안 = 글자
  tr 안 div     표 앞 = <div>           표 직속 = —                 td 안 = 글자
  td 안 div     표 앞 = —               표 직속 = —                 td 안 = <div>

form 칸 — 표 앞으로 나간 input 의 .form 이 표 안에 남은 form 인가 = true · form.elements.length = 1 · form.childNodes.length = 0

표 앞으로 나간 칸 = 7 / 14
(exit 0)
```

```text
  「in table」 모드가 갈라 놓는 세 갈래

  표 앞으로 나간다 (foster)           표 안에 남는다                 td 안이면
  -----------------------           -------------------            -------------
  div · span · 글자 · img            공백                           아무거나 된다
  input type=text                    input type=hidden             (td 는 흐름 콘텐츠를 받는다)
  tr 안의 div                        script · style · template
  form 안의 input                    주석
                                     form (빈 채로)

  7 / 14 가 나갔다. 남은 것은 「in table」 모드가 이름을 불러 따로 처리하는 것들이다.
```

- ★★★ **14칸 중 7칸이 표 앞으로 나갔다.** 나간 것은 **「in table」 모드가 이름을 부르지 않는 것 전부**다 — `div`·`span`·글자·`img`·`input type=text`·`tr` 안의 `div`.
- ★★ **남은 것은 명세가 이름을 불러 따로 적은 것들이다.** `script`·`style`·`template` 은 「in head」 규칙으로 처리되고, 주석은 그대로 끼워지고, **공백 글자**는 「in table text」 모드에서 **공백뿐이면 제자리에** 들어간다.
- ★★ **`input type=hidden` 은 남고 `input type=text` 는 나갔다.** 같은 `input` 인데 **`type` 속성의 값**이 가른다 — 명세가 `hidden` 만 「파스 오류지만 그 자리에 넣는다」로 적고, 나머지 `type` 은 「그 밖의 모든 것」 줄로 보낸다.
- ★★★ **`form` 은 빈 채로 표 안에 남고, 그 안에 쓴 `input` 은 표 앞으로 나갔다.** 그런데 **`input.form` 은 그 빈 `form` 을 가리킨다**(`true` · `form.elements.length = 1` · `form.childNodes.length = 0`). 파서의 **form 요소 포인터**가 연결을 붙잡고 있어서다 — **트리에서는 떨어져 있는데 제출은 같이 된다.** 트리를 읽어서는 절대 안 보이는 연결이다.
- **`td` 안은 무엇이든 된다** — `td` 의 콘텐츠 모델이 흐름 콘텐츠라 `div` 가 그대로 남았다.

### (3) 창 ② — 스크립트 API 는 자동 `tbody` 를 센다

**언제 쓰나** — 소스에 `tbody` 를 안 쓴 표를 스크립트로 만질 때 · `innerHTML` 로 행을 넣을 때.

```html
<!-- html17b-17-api.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 스크립트 API 가 세는 것</title>
</head>
<body>
<table id="쓴표"><tr><td>가</td></tr><tr><td>나</td></tr></table>
<div id="상자"></div>
<template id="틀"></template>
<table id="빈표"></table>
<table id="넣을표"><tbody id="몸"></tbody></table>
<script>
window.__대상 = [];
const $ = id => document.getElementById(id);
const 자식 = n => [...n.childNodes].map(c => c.nodeType === 1 ? c.localName : c.nodeType === 3 ? JSON.stringify(c.data) : "?").join(" ");
window.__끝 = () => {
  const O = [];
  const t = $("쓴표");
  O.push("(가) 소스에 tbody 를 안 쓴 표");
  O.push("  table.tBodies.length           = " + t.tBodies.length);
  O.push("  table.rows.length              = " + t.rows.length);
  O.push("  table.children                 = " + 자식(t));
  O.push("  querySelectorAll('table > tr') = " + document.querySelectorAll("#쓴표 > tr").length);
  O.push("  querySelectorAll('table tr')   = " + document.querySelectorAll("#쓴표 tr").length);
  O.push("");
  const 조각 = "<tr><td>셀</td></tr>";
  O.push("(나) 같은 문자열 " + JSON.stringify(조각) + " 을 innerHTML 로 넣으면");
  $("상자").innerHTML = 조각;
  O.push("  div.innerHTML            -> div 의 자식      = " + 자식($("상자")));
  $("틀").innerHTML = 조각;
  O.push("  template.innerHTML       -> content 의 자식  = " + 자식($("틀").content));
  $("빈표").innerHTML = 조각;
  O.push("  table.innerHTML          -> table 의 자식    = " + 자식($("빈표")));
  $("몸").innerHTML = 조각;
  O.push("  tbody.innerHTML          -> tbody 의 자식    = " + 자식($("몸")));
  O.push("");
  O.push("(다) 스크립트 API 로 행을 만들면");
  const 새표 = document.createElement("table");
  새표.insertRow().insertCell().textContent = "셀";
  O.push("  빈 table.insertRow()     -> table 의 자식    = " + 자식(새표));
  const 둘째 = document.createElement("table");
  둘째.createTHead();
  둘째.insertRow();
  O.push("  thead 만 있는 table.insertRow() -> table 의 자식 = " + 자식(둘째));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-17-api.html | sed -n '1,6p'
(가) 소스에 tbody 를 안 쓴 표
  table.tBodies.length           = 1
  table.rows.length              = 2
  table.children                 = tbody
  querySelectorAll('table > tr') = 0
  querySelectorAll('table tr')   = 2
(exit 0)
```

```text
$ python3 html17b-cdp.py page html17b-17-api.html | sed -n '8,12p'
(나) 같은 문자열 "<tr><td>셀</td></tr>" 을 innerHTML 로 넣으면
  div.innerHTML            -> div 의 자식      = "셀"
  template.innerHTML       -> content 의 자식  = tr
  table.innerHTML          -> table 의 자식    = tbody
  tbody.innerHTML          -> tbody 의 자식    = tr
(exit 0)
```

```text
$ python3 html17b-cdp.py page html17b-17-api.html | sed -n '14,16p'
(다) 스크립트 API 로 행을 만들면
  빈 table.insertRow()     -> table 의 자식    = tbody
  thead 만 있는 table.insertRow() -> table 의 자식 = thead tbody
(exit 0)
```

```text
  같은 문자열 "<tr><td>셀</td></tr>" — 어디에 넣느냐로 갈린다

  넣은 곳            파서가 서 있는 삽입 모드        결과
  div.innerHTML      in body                        "셀"   <- tr·td 태그가 버려졌다
  template.innerHTML in template                    tr     <- 그대로 산다
  table.innerHTML    in table                       tbody  <- 또 끼웠다
  tbody.innerHTML    in table body                  tr     <- 그대로 산다

  ★ innerHTML 은 「그 요소를 문맥으로 한 조각 파싱」이다 — 문맥이 삽입 모드를 고른다.
```

- ★★ **`tBodies.length` 가 1, `rows.length` 가 2** 다 — 소스에 `tbody` 를 안 썼는데 **API 는 파서가 끼운 `tbody` 를 센다.** API 는 **DOM 을 읽을 뿐**이기 때문이다.
- ★★★ **`table > tr` 이 0개**, `table tr` 이 2개다. 트리에는 `table > tbody > tr` 만 있다 — [03번 주제](../03-parser-and-error-recovery/2-summary.md) 가 「실무를 무는 첫 자리」로 적은 그것이다.
- ★★ **`div.innerHTML = "<tr>…"` 은 태그가 버려지고 글자만 남는다.** 「in body」 모드는 `tr`·`td` 시작 태그를 **무시**한다 — [05번 주제](../05-content-categories-and-models/2-summary.md) (6) 의 「부모 없이 쓴 `td` 만 사라진다」와 같은 규칙이다. ★ **`template.innerHTML` 에서는 산다** — [10번 주제](../10-template-slot-shadow-dom/2-summary.md) (2) 가 「`<template>` 안도 삽입 모드를 받는다」로 캡처했다. 조각을 **어느 문맥에서 파싱하나**의 정본은 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **04번**([`textContent` 대 `innerHTML` 대 `innerText`](../../../../web-api/04-textcontent-innerhtml-innertext/2-summary.md))이다.
- ★ **`table.innerHTML` 도 `tbody` 를 또 끼운다.** 문맥이 `table` 이면 「in table」 모드로 시작하기 때문이다.
- ★ **`insertRow()` 도 `tbody` 를 만든다** — 명세 단계가 「`rows` 가 비었고 `tbody` 가 없으면 **`tbody` 를 만들어** 거기 넣는다」다. `thead` 만 있는 표에서도 `thead` 안이 아니라 **새 `tbody`** 에 들어갔다(`thead tbody`). ★ **이 경로는 파서가 아니라 DOM 명세의 단계**다 — 결과가 파서와 닮았을 뿐 이유가 다르다.

### (4) 창 ① × 창 ② × 창 ⑦ — 네 행의 순서를 다섯 창에 물으면

**언제 쓰나** — `thead` 를 `tbody` 뒤에, `tfoot` 을 맨 앞에 쓴 표(콘텐츠 모델 위반)를 만났을 때.

소스 순서가 **`tfoot` · `tbody` · `thead` · `tbody`** 인 표 하나를 다섯 창에 물었다. 「명세 표 모델」 열은 명세 4.9.12.1 「표 만들기」의 **행 순서 부분을 페이지 스크립트로 옮긴 계산**이다.

```html
<!-- html17b-17-order.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 행의 순서</title>
<style>body { font-family: sans-serif; } td { padding: 4px; }</style>
</head>
<body>
<table id="표">
<tfoot><tr id="발"><td>tfoot 의 행</td></tr></tfoot>
<tbody><tr id="본문1"><td>첫 tbody 의 행</td></tr></tbody>
<thead><tr id="머리"><td>thead 의 행</td></tr></thead>
<tbody><tr id="본문2"><td>둘째 tbody 의 행</td></tr></tbody>
</table>
<script>
window.__대상 = [];
window.__내부 = true;
const 표 = document.getElementById("표");
// 명세 「표 만들기(forming a table)」 알고리즘에서 행 순서를 정하는 부분만 옮긴 것
function 명세순서(t) {
  const 앞 = [], 미룬 = [];
  for (const g of t.children) {
    if (g.localName === "tfoot") 미룬.push(g);
    else if (["thead", "tbody"].includes(g.localName)) 앞.push(g);
    else if (g.localName === "tr") 앞.push({ children: [g] });
  }
  return [...앞, ...미룬].flatMap(g => [...g.children]).map(r => r.id);
}
window.__끝 = () => {
  const O = [];
  const DOM = [...표.querySelectorAll("tr")].map(r => r.id);
  const 창 = {
    "① DOM 트리 순서": DOM,
    "   table.rows": [...표.rows].map(r => r.id),
    "② 화면 위→아래": [...표.querySelectorAll("tr")].sort((a, b) =>
      a.getBoundingClientRect().top - b.getBoundingClientRect().top).map(r => r.id),
    "   명세 표 모델(스크립트)": 명세순서(표),
    "⑦ 트리 tableRowIndex": [...표.querySelectorAll("tr")].sort((a, b) =>
      __INT[a.id].속성.tableRowIndex - __INT[b.id].속성.tableRowIndex).map(r => r.id),
  };
  O.push("같은 네 행을 다섯 창에 물었다 — 위(앞)에서부터");
  let 갈림 = 0;
  for (const [k, v] of Object.entries(창)) {
    const 다름 = v.join() !== DOM.join();
    if (k !== "① DOM 트리 순서" && 다름) 갈림++;
    O.push("  " + k.padEnd(20) + v.join(" · ") + (k === "① DOM 트리 순서" ? "" : 다름 ? "   <- DOM 과 다름" : "   = DOM"));
  }
  O.push("");
  O.push("table.tHead = #" + 표.tHead.rows[0].id + " · table.tFoot = #" + 표.tFoot.rows[0].id + " · tBodies.length = " + 표.tBodies.length);
  O.push("DOM 순서와 갈린 창 = " + 갈림 + " / " + (Object.keys(창).length - 1));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-17-order.html
같은 네 행을 다섯 창에 물었다 — 위(앞)에서부터
  ① DOM 트리 순서         발 · 본문1 · 머리 · 본문2
     table.rows       머리 · 본문1 · 본문2 · 발   <- DOM 과 다름
  ② 화면 위→아래           머리 · 본문1 · 본문2 · 발   <- DOM 과 다름
     명세 표 모델(스크립트)    본문1 · 머리 · 본문2 · 발   <- DOM 과 다름
  ⑦ 트리 tableRowIndex  머리 · 본문1 · 본문2 · 발   <- DOM 과 다름

table.tHead = #머리 · table.tFoot = #발 · tBodies.length = 2
DOM 순서와 갈린 창 = 4 / 4
(exit 0)
```

```text
  같은 네 행, 다섯 개의 순서

  창                         1         2          3          4
  ① DOM                      발        본문1      머리       본문2     <- 쓴 그대로
     table.rows (IDL)        머리      본문1      본문2      발        <- thead 먼저, tfoot 끝
  ② 화면 위→아래             머리      본문1      본문2      발        <- CSS 표 레이아웃
     명세 표 모델(계산)       본문1     머리       본문2      발        <- tfoot 만 끝으로
  ⑦ 트리 tableRowIndex       머리      본문1      본문2      발        <- 화면과 같다

  ★ DOM 과 같은 창은 하나도 없다. 그리고 명세 표 모델은 나머지 셋과도 다르다.
```

- ★★★ **DOM 순서와 갈린 창이 4 / 4** 다. 파서는 `thead`·`tfoot` 을 **옮기지 않는다** — DOM 은 쓴 그대로다.
- ★★ **`table.rows` 는 `thead` 행을 먼저, `tfoot` 행을 끝에** 둔다 — 명세의 `rows` 게터가 **그 순서로 정렬하라**고 적는다. **API 가 DOM 순서를 따르지 않는 드문 자리**다.
- ★★ **화면에서는 `thead` 가 맨 위, `tfoot` 이 맨 아래**다. 렌더링 절이 `thead { display: table-header-group }`·`tfoot { display: table-footer-group }` 를 주고, CSS 표 레이아웃이 그 값을 **소스 위치와 무관하게** 위·아래에 놓는다.
- ★★★ **명세의 「표 처리 모델」은 `tfoot` 만 끝으로 미루고 `thead` 는 제자리에 둔다**(본문1 · 머리 · 본문2 · 발). 그 모델이 매기는 좌표는 **머리 칸을 배정하는 기준**이다([18번 주제](../18-table-headers-and-scope/2-summary.md)). ★ **그런데 Chrome 의 트리(`tableRowIndex`)는 화면 순서를 따랐다** — 명세 모델과 **머리·본문1 의 자리가 뒤바뀌었다.** 콘텐츠 모델 위반인 표에서 **명세 모델과 구현의 좌표가 갈린 것**이다.

### (5) 창 ⑦ — `caption` 은 표의 이름이 된다

**언제 쓰나** — 표에 제목을 붙일 때 · `caption` 과 `aria-label`·`title` 이 같이 있을 때.

아홉 표에 이름 출처를 하나씩 바꿔 주고, CDP 의 이름·설명과 **내부 덤프의 `nameFrom`**(이름이 어디서 왔나)을 같이 찍었다.

```html
<!-- html17b-17-name.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 표의 이름</title>
</head>
<body>
<table id="캡션"><caption>분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="없음"><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="title" title="제목 속성"><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="둘다" title="제목 속성"><caption>분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="aria" aria-label="에어리아 이름"><caption>분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="늦은"><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr><caption>분기별 매출</caption></table>
<table id="숨긴"><caption style="display: none">분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="클립"><caption style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%)">분기별 매출</caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<table id="h2"><caption><h2>분기별 매출</h2></caption><tr><th>분기</th><th>매출</th></tr><tr><td>1</td><td>10</td></tr></table>
<script>
const 표 = ["캡션", "없음", "title", "둘다", "aria", "늦은", "숨긴", "클립", "h2"];
window.__대상 = 표.map(k => [k, "#" + k]);
window.__내부 = true;
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = ["표마다 창 ⑦ 이 준 역할·이름·설명과 이름의 출처(nameFrom — 내부 덤프)"];
  for (const k of 표) {
    const a = __AX[k], i = __INT[k].속성;
    O.push("  #" + k.padEnd(6) + "역할 = " + a.역할.padEnd(7) + "이름 = " + J(a.이름).padEnd(12)
      + "설명 = " + J(a.설명).padEnd(10) + "nameFrom = " + (i.nameFrom || "—"));
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-17-name.html
표마다 창 ⑦ 이 준 역할·이름·설명과 이름의 출처(nameFrom — 내부 덤프)
  #캡션    역할 = table  이름 = "분기별 매출"    설명 = ""        nameFrom = caption
  #없음    역할 = table  이름 = ""          설명 = ""        nameFrom = —
  #title 역할 = table  이름 = "제목 속성"     설명 = ""        nameFrom = title
  #둘다    역할 = table  이름 = "분기별 매출"    설명 = "제목 속성"   nameFrom = caption
  #aria  역할 = table  이름 = "에어리아 이름"   설명 = "분기별 매출"  nameFrom = attribute
  #늦은    역할 = table  이름 = "분기별 매출"    설명 = ""        nameFrom = caption
  #숨긴    역할 = table  이름 = ""          설명 = ""        nameFrom = —
  #클립    역할 = table  이름 = "분기별 매출"    설명 = ""        nameFrom = caption
  #h2    역할 = table  이름 = "분기별 매출"    설명 = ""        nameFrom = caption
(exit 0)
```

```text
  이름 출처의 우선순위 — HTML-AAM 「table 요소의 이름 계산」 그대로

  aria-label / aria-labelledby    ->  이름      (caption 은 설명으로 밀려난다)
  첫 child caption                ->  이름      (title 은 설명으로 밀려난다)
  title                           ->  이름
  아무것도 없음                    ->  이름 없음

  #늦은(tbody 뒤의 caption)  이름 = "분기별 매출"   <- 위치가 틀려도 child 면 된다
  #숨긴(display: none)       이름 없음             <- 트리에서 빠진 caption 은 이름을 못 준다
  #클립(1px 로 잘라 숨김)     이름 = "분기별 매출"   <- 화면에서만 숨긴 caption 은 이름을 준다
```

- ★★★ **`caption` 이 표의 이름이 됐다**(`nameFrom = caption`). HTML-AAM 의 「table 요소의 이름 계산」이 **「`aria-label`·`aria-labelledby` → 첫 child `caption` 의 하위 트리 → `title`」** 순서다. 이 판이 그대로 따랐다.
- ★★ **`aria-label` 이 있으면 `caption` 은 이름에서 밀려나 설명이 된다.** `title` 도 `caption` 이 있으면 설명이 된다(`#둘다`). **같은 글자가 칸만 옮긴다** — [13번 주제](../13-phrasing-semantics/2-summary.md) (6) 의 `title` 과 같은 꼴이다.
- ★ **`tbody` 뒤에 남은 `caption` 도 이름이 됐다**(`#늦은`) — 규칙이 「첫 **child** `caption`」이지 「첫 자식」이 아니기 때문이다. (1) 의 `#라` 처럼 **파서가 순서를 안 고쳐도** 이름은 선다.
- ★ **`display: none` 인 `caption` 은 이름을 못 준다**(`#숨긴`). HTML-AAM 이 따로 적는다 — 「`caption` 이 접근성 트리에서 숨겨지면 표에 이름을 주지 않는다」. ★ **화면에서만 숨긴 `caption` 은 이름을 준다**(`#클립` — 1px 상자 + `clip-path: inset(50%)`). 숨기는 **방법**이 트리에 남느냐를 가른다.
- **`caption` 안에 `<h2>` 를 넣어도 이름은 글자 그대로다**(`#h2`).

### (6) 창 ⑦ — 파서가 끼운 `tbody` 는 트리에서 빠진다

**언제 쓰나** — 트리 덤프에서 `rowgroup` 이 **있다 없다 하는** 이유를 찾을 때.

```html
<!-- html17b-17-ax.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 행 묶음은 트리에 남나</title>
</head>
<body>
<table><thead><tr><th>머리</th></tr></thead><tbody><tr><td>본문</td></tr></tbody><tfoot><tr><td>발</td></tr></tfoot></table>
<table><thead id="h"><tr><th>머리</th></tr></thead><tbody id="b"><tr><td>본문</td></tr></tbody><tfoot id="f"><tr><td>발</td></tr></tfoot></table>
<table><tr><th>머리</th></tr><tr><td>본문</td></tr></table>
</body>
</html>
```

```text
$ python3 html17b-cdp.py ax html17b-17-ax.html
RootWebArea    이름='17 행 묶음은 트리에 남나'
  table          이름=''
    rowgroup       이름=''
      row            이름=''
        columnheader   이름='머리'
          StaticText     이름='머리'
    row            이름=''
      cell           이름='본문'
        StaticText     이름='본문'
    rowgroup       이름=''
      row            이름=''
        cell           이름='발'
          StaticText     이름='발'
  table          이름=''
    rowgroup       이름=''
      row            이름=''
        columnheader   이름='머리'
          StaticText     이름='머리'
    rowgroup       이름=''
      row            이름=''
        cell           이름='본문'
          StaticText     이름='본문'
    rowgroup       이름=''
      row            이름=''
        cell           이름='발'
          StaticText     이름='발'
  table          이름=''
    row            이름=''
      columnheader   이름='머리'
        StaticText     이름='머리'
    row            이름=''
      cell           이름='본문'
        StaticText     이름='본문'
(exit 0)
```

- ★★ **첫 표의 `tbody` 는 트리에 `rowgroup` 으로 안 나왔다** — `thead`·`tfoot` 은 나왔다. **둘째 표처럼 `id` 를 달면 `tbody` 도 나온다.** 셋째 표(파서가 끼운 `tbody`)는 `table > row` 로 바로 이어졌다.
- ★★★ **HTML-AAM 은 `tbody` 를 `rowgroup` 역할에 대응시킨다.** 이 판은 **속성 없는 `tbody` 를 무시된 노드로 빼고 행만 표에 붙였다** — 명세 대응과 구현이 갈린 자리다. [13번 주제](../13-phrasing-semantics/2-summary.md) (2) 가 적은 「`id` 없는 `generic` 을 뺀다」와 **같은 꼴의 구현 관찰**이다(이 배치에서 본 사례 전부).
- ★ **행과 칸은 어느 쪽이든 그대로다** — 빠진 것은 **묶음 노드 하나**다. 보조 기술이 「본문 묶음」을 따로 알리는지는 이 판에서 못 본다(아래 「도구가 못 보는 것」).

### (7) 창 ② — `col` 에 속성을 하나씩 주면 셀에 닿는 것은 넷이다

**언제 쓰나** — 「열 전체에 색을 칠하려면 `col` 에 주면 된다」를 쓰기 전에.

가운데 `col` 에 속성을 **하나씩** 주고, 가운데 셀을 **속성 없는 표의 같은 셀**과 견줬다. 잰 것은 셀의 폭·x · 계산 스타일 다섯 칸 · **셀 왼쪽 위 (x+2, y+2) 의 화면 픽셀**이다.

```html
<!-- html17b-17-col.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>17 col 에 준 속성</title>
<style>
body { font-family: sans-serif; margin: 8px; }
table { border-collapse: collapse; margin-bottom: 4px; }
td { padding: 8px; }
.background-color { background-color: gold; }
.border { border: 6px solid rgb(0, 0, 255); }
.width { width: 200px; }
.visibility { visibility: collapse; }
.color { color: rgb(255, 0, 0); }
.font-weight { font-weight: 700; }
.text-align { text-align: right; }
.padding { padding: 20px; }
</style>
</head>
<body>
<script>
const 속성 = ["없음", "background-color", "border", "width", "visibility", "color", "font-weight", "text-align", "padding"];
for (const p of 속성)
  document.body.insertAdjacentHTML("beforeend",
    `<table><colgroup><col><col class="${p}"><col></colgroup><tr><td>가</td><td id="셀-${p}">가나</td><td>다</td></tr></table>`);
window.__대상 = [];
const 셀 = p => document.getElementById("셀-" + p);
window.__픽셀 = () => 속성.map(p => { const r = 셀(p).getBoundingClientRect(); return [p, r.left + 2, r.top + 2]; });
const 잰것 = p => {
  const e = 셀(p), r = e.getBoundingClientRect(), s = getComputedStyle(e);
  return { "셀 폭": r.width.toFixed(1), "셀 x": r.left.toFixed(1), "계산 color": s.color, "계산 background": s.backgroundColor,
    "계산 weight": s.fontWeight, "계산 align": s.textAlign, "계산 padding": s.paddingLeft, "칠해진 픽셀": __PX[p] };
};
window.__끝 = () => {
  const O = ["가운데 col 에 속성 하나씩 — 가운데 셀에서 무엇이 바뀌었나(속성 없는 표와 견준다)"];
  const 기준 = 잰것("없음");
  O.push("  기준(속성 없음)      " + Object.entries(기준).map(([k, v]) => k + "=" + v).join(" · "));
  let 닿음 = 0;
  for (const p of 속성.slice(1)) {
    const v = 잰것(p);
    const col값 = getComputedStyle(document.querySelector("col." + p)).getPropertyValue(p === "border" ? "border-top-width" : p);
    const 바뀐 = Object.keys(v).filter(k => v[k] !== 기준[k]);
    if (바뀐.length) 닿음++;
    O.push("  " + p.padEnd(18) + " col 자신의 계산값 = " + col값.padEnd(20) + "셀에서 바뀐 것 = "
      + (바뀐.length ? 바뀐.map(k => k + " " + 기준[k] + "->" + v[k]).join(" · ") : "없음"));
  }
  O.push("");
  O.push("셀에 닿은 속성 = " + 닿음 + " / " + (속성.length - 1));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-17-col.html
가운데 col 에 속성 하나씩 — 가운데 셀에서 무엇이 바뀌었나(속성 없는 표와 견준다)
  기준(속성 없음)      셀 폭=45.5 · 셀 x=38.7 · 계산 color=rgb(0, 0, 0) · 계산 background=rgba(0, 0, 0, 0) · 계산 weight=400 · 계산 align=start · 계산 padding=8px · 칠해진 픽셀=rgb(255, 255, 255)
  background-color   col 자신의 계산값 = rgb(255, 215, 0)    셀에서 바뀐 것 = 칠해진 픽셀 rgb(255, 255, 255)->rgb(255, 215, 0)
  border             col 자신의 계산값 = 6px                 셀에서 바뀐 것 = 셀 폭 45.5->51.5 · 셀 x 38.7->41.7 · 칠해진 픽셀 rgb(255, 255, 255)->rgb(0, 0, 255)
  width              col 자신의 계산값 = 200px               셀에서 바뀐 것 = 셀 폭 45.5->200.0
  visibility         col 자신의 계산값 = collapse            셀에서 바뀐 것 = 셀 폭 45.5->0.0
  color              col 자신의 계산값 = rgb(255, 0, 0)      셀에서 바뀐 것 = 없음
  font-weight        col 자신의 계산값 = 700                 셀에서 바뀐 것 = 없음
  text-align         col 자신의 계산값 = right               셀에서 바뀐 것 = 없음
  padding            col 자신의 계산값 = 20px                셀에서 바뀐 것 = 없음

셀에 닿은 속성 = 4 / 8
(exit 0)
```

```text
  col 은 셀의 조상이 아니다 — 트리에서 셀은 tr 의 자식이다

  table
  ├─ colgroup ─ col  col.X  col          <- 여기에 속성을 줬다
  └─ tbody ─ tr ─ td  td  td             <- 셀은 이쪽 가지에 있다

  상속으로 내려가는 것 (color · font-weight · text-align · padding)  -> 안 닿는다
  CSS 표 모델이 따로 불러 쓰는 것 (background · border · width · visibility)  -> 닿는다
```

- ★★★ **셀에 닿은 속성이 8 중 4** 다 — `background-color`·`border`·`width`·`visibility`. CSS 2.1 §17.3 이 「열·열 묶음 요소에 적용되는 속성」으로 드는 **바로 그 넷**이다.
- ★★ **`background-color` 는 픽셀로만 보였다.** 셀의 **계산 `background` 는 끝까지 투명**이다 — 열의 배경은 **셀 아래 층에 칠해질 뿐** 셀의 값이 아니다. 창 ② 의 계산값만 봤으면 「안 닿는다」로 틀린다.
- ★★ **`color`·`font-weight`·`text-align`·`padding` 은 `col` 자신의 계산값은 바뀌는데 셀은 그대로다.** 셀은 `col` 의 **자식이 아니라** `tr` 의 자식이라 상속이 안 된다 — CSS 2.1 이 「셀은 행의 자손이지 열의 자손이 아니다」라고 먼저 적는다.
- ★ **`border` 는 `border-collapse: collapse` 인 표에서만** 열에 먹는다(명세 조건). 이 격자는 그 조건을 켜고 쟀다 — 셀 폭이 6px 늘고 픽셀이 파랑이 됐다.
- **`visibility: collapse` 는 셀 폭을 0 으로** 만들었다 — 열이 통째로 접힌다.

### demo — 소스 순서와 화면 순서

```html demo
<!-- html17b-17-demo.html -->
<table border="1">
  <tfoot><tr><td>tfoot — 소스의 맨 앞</td></tr></tfoot>
  <tbody><tr><td>tbody — 소스의 가운데</td></tr></tbody>
  <thead><tr><td>thead — 소스의 맨 뒤</td></tr></thead>
</table>
```

> **보이는 것** — 표의 **맨 위 줄이 「thead — 소스의 맨 뒤」**, 가운데가 tbody, **맨 아래가 「tfoot — 소스의 맨 앞」** 이다. 소스에서는 순서가 정반대다.\
> **바꿔 볼 것** — `<thead>` 를 `<tbody>` 로 바꾸면 그 줄이 **가운데**로 내려온다 — 두 `tbody` 는 소스 순서대로 서고, `tfoot` 은 여전히 맨 아래다(실측: 행의 top 이 11 · 41 · 71 로 「tbody · thead 글자의 줄 · tfoot」. [3-answer.md](3-answer.md) 의 `## 실행 검증`)

*(Chrome 151 headless 실측, 창 폭 1000: 행의 top 이 thead 11 · tbody 41 · tfoot 71. 검증 파일은 [3-answer.md](3-answer.md) 의 `## 실행 검증`, 출력은 아래)*

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-17-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
창 폭 = 1000
DOM 순서      = tfoot · tbody · thead
화면 위→아래  = thead@11 · tbody@41 · tfoot@71
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다. 쓰는 꼴은 위 소스가 전부 실제로 던진 형태이므로 여기서는 **콘텐츠 모델과 파서가 하는 일**을 한 표에 둔다.

| 요소 | 명세 콘텐츠 모델의 자리 | 파서가 하는 일(이 판의 관찰) |
|---|---|---|
| `<caption>` | 표의 **첫 자식**(선택) | 뒤에 써도 **안 옮긴다** — 그래도 이름은 된다((1)·(5)) |
| `<colgroup>`/`<col>` | `caption` 뒤, 행 묶음 앞 | 스타일 넷만 셀에 닿는다((7)) |
| `<thead>` | `colgroup` 뒤, 본문 앞(선택) | 뒤에 써도 **안 옮긴다** — 화면에서는 맨 위((4)) |
| `<tbody>` | 0개 이상 — **또는 `tr` 을 바로** | `tr` 을 바로 쓰면 **끼워 넣는다**((1)) |
| `<tfoot>` | 맨 끝(선택) | 앞에 써도 **안 옮긴다** — 화면에서는 맨 아래((4)) |
| 그 밖의 요소·글자 | 올 수 없다 | **표 앞으로 뺀다**(foster) — 이름을 부른 예외 여럿((2)) |

### 어디서 헷갈리나

- **「`tbody` 는 생략해도 된다」는 「없어도 된다」가 아니다.** 콘텐츠 모델이 `tr` 을 바로 받는 것은 **파서가 `tbody` 를 끼워 주기 때문**이다. DOM 에는 **반드시** 있다.
- **「`tfoot` 은 끝에 쓴다」는 옛 규칙과 새 규칙이 있다.** HTML 4.01 은 「`TFOOT` 은 `TBODY` **앞**에 와야 한다 — 행을 다 받기 전에 발을 그릴 수 있도록」이라고 적었다. 지금 콘텐츠 모델은 **맨 끝**이다 — 어느 쪽으로 써도 화면은 맨 아래다((4)).
- **`caption` 은 `<table>` 앞에 쓰는 제목이 아니다.** 표의 **첫 자식**이다. 표 밖의 `<h2>` 는 표의 이름이 되지 않는다(`aria-labelledby` 로 잇지 않는 한).

## 어디서 틀리나

### 1. `table > tr` 로 행을 잡는다

**0개를 잡는다**((3)). 파서가 `tbody` 를 끼웠기 때문이다.\
`table tr` · `table > tbody > tr` · 스크립트면 `table.rows` 를 쓴다.

### 2. 서버 템플릿이 표 안에 조건부 UI 를 끼운다

```text
  <table>
    {% if loading %}<div class="spinner"></div>{% endif %}     <- 표 앞으로 나간다
    <tr>…</tr>
  </table>

  화면: 스피너가 표 「위」에 뜬다 · table.firstElementChild 는 tbody 다
  처방: td 안에 넣거나 표 밖에 둔다
```

(2) 의 격자에서 `div` 가 **표 앞 형제**가 됐다. 에러도 경고도 없다.

### 3. 표 안의 `form` 이 동작하니 구조도 맞는 줄 안다

**`form` 은 빈 채로 남고 `input` 은 표 앞으로 나갔다**((2)). 제출은 **form 요소 포인터 덕에** 우연히 된다.\
★ 그런데 **그 `form` 의 자식은 0개다**(`childNodes.length = 0`) — 트리에서 `form` 안을 뒤지는 코드는 `input` 을 못 찾는다. 폼은 **표 밖을 감싸거나 셀 안에** 둔다.

### 4. `div.innerHTML = "<tr>…"` 로 행을 만든다

**`tr`·`td` 태그가 버려지고 글자만 남는다**((3)). 문맥이 `div` 라 「in body」 모드로 파싱되기 때문이다.\
행 조각은 **`template`·`tbody` 에 넣거나 `insertRow()`** 를 쓴다.

### 5. `col` 로 열 글자색·정렬을 준다

**안 먹는다**((7) — `color`·`text-align` 은 셀에서 「없음」). 먹는 것은 넷뿐이다.\
열 글자색은 `td:nth-child(2)` 처럼 **셀을 직접 잡아야** 한다.

### 6. 계산값이 투명이니 열 배경이 안 칠해진 줄 안다

**칠해졌다**((7) — 픽셀이 `rgb(255, 215, 0)`). 셀의 계산 `background` 는 끝까지 투명이다.\
★ **계산값은 「셀이 무엇을 선언했나」를 말하지 「화면에 무엇이 칠해졌나」를 말하지 않는다.**

## 구현 세부사항 대 언어 보장

★ 세 층으로 갈라 적는다 — **명세(WHATWG HTML · HTML-AAM · CSS 2.1)가 보장하는 것 / Chrome 151 이 구현한 것 / 이 판에서 관찰한 것.**

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML 파싱)** | `tr`·`td` 앞에 **`tbody` 삽입** · 비표 내용의 **foster parenting** · `input type=hidden`·`form`·`script`·`style`·`template`·주석의 예외 | (1)·(2) |
| **명세(HTML DOM)** | `rows` 의 **thead → 본문 → tfoot 정렬** · `insertRow()` 의 **`tbody` 생성** | (3)·(4) |
| **명세(HTML 표 처리 모델)** | 행 좌표 — **`tfoot` 만 끝으로** | (4) — 스크립트로 옮긴 계산 |
| **명세(HTML 렌더링 · CSS)** | `thead`/`tfoot` 의 `display` 값 → 화면 위·아래 · 열에 닿는 속성 넷 | (4)·(7) |
| **명세(HTML-AAM)** | 표의 이름 = `aria-*` → 첫 child `caption` → `title` · `tbody` → `rowgroup` | (5)·(6) |
| **구현(Chrome)** | 트리의 행 좌표가 **화면 순서**를 따른 것 | (4) — ★ 명세 모델과 갈렸다 |
| **구현(Chrome)** | 속성 없는 **`tbody` 를 트리에서 뺀 것** | (6) — ★ 명세 대응과 갈렸다 |
| **이 판의 관찰** | 셀 폭·top 의 px | (4)·(7)·demo — 글꼴이 바뀌면 절댓값은 바뀐다 |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **스크린리더가 `caption` 을 표 제목으로 읽는지** · 「3행 2열」처럼 표를 어떻게 읽는지 | 이 판에 **NVDA·VoiceOver·Orca 가 없다.** 트리는 보조 기술의 **입력**이지 출력이 아니다 |
| **`tbody` 가 빠진 트리가 보조 기술의 탐색을 바꾸는지** | 같은 이유 — 빠졌다는 것까지가 관찰이다 |
| **플랫폼 접근성 API 의 표 값**(IAccessibleTable·UIA Table·ATK·AX) | CDP 와 내부 덤프는 Chrome 의 **내부 트리**까지다 — 그 아래 층은 이 판에서 못 본다 |
| **다른 엔진의 행 좌표·`tbody` 처리** | 엔진이 하나뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **표는 2차원 자료에만** — 행과 열이 **둘 다 뜻을 가질 때**. 레이아웃 배치는 CSS grid 의 일이다(레이아웃 표를 트리가 어떻게 가르는지는 [18번 주제](../18-table-headers-and-scope/2-summary.md) (7)).
- **`tbody` 는 써 둔다** — 안 써도 생기지만, **써 두면 소스와 DOM 이 같아진다.** 스크립트·선택자가 덜 놀란다.
- **`thead`·`tfoot` 은 콘텐츠 모델 순서대로** — 뒤바꿔도 화면은 같지만 **명세 표 모델과 트리의 좌표가 갈린다**((4)).
- **`caption` 은 표의 첫 자식으로** — 이름이 된다. 숨기고 싶으면 `display: none` 이 아니라 **시각적으로만 숨기는 CSS** 를 쓴다 — (5) 의 `#클립`(1px 상자 + `clip-path`)은 **이름을 그대로 줬고** `#숨긴`(`display: none`)은 이름까지 지웠다.
- **열 스타일은 `col` 로 넷만** — 배경·테두리·폭·접기. 나머지는 셀 선택자다.
- **표 안에는 표 요소만** — 스피너·폼·안내 문구는 셀 안이나 표 밖이다.

## 핵심 문장

1. **파서는 `tr`·`td` 앞에 `tbody` 를 끼운다 — 그래서 `table > tr` 은 0개를 잡고 `tBodies.length` 는 1 이다.**
2. **표 안에 못 두는 것은 표 앞으로 나간다 — 14가지 중 7가지가 나갔고, 남은 것은 명세가 이름을 불러 예외로 적은 것들이다.**
3. **표 안의 `form` 은 빈 채로 남고 `input` 은 나가지만 `input.form` 은 그 `form` 을 가리킨다.**
4. **행의 순서는 창마다 다르다 — DOM 은 소스 순서, `rows`·화면·트리는 thead 먼저, 명세 표 모델은 tfoot 만 끝으로.**
5. **`caption` 이 표의 이름이 되고, `aria-label` 이 있으면 설명으로 밀려난다.**
6. **`col` 에서 셀에 닿는 속성은 배경·테두리·폭·`visibility` 넷뿐이고, 배경은 픽셀로만 보인다.**
7. **속성 없는 `tbody` 는 이 판의 트리에서 빠진다 — HTML-AAM 의 `rowgroup` 대응과 갈린 구현이다.**

## 관련 자료

- [03번 주제 — 파서와 오류 복구](../03-parser-and-error-recovery/2-summary.md) — **`tbody` 삽입((2))과 foster parenting((3))의 정본**이다. 여기는 그 결론을 **표의 설계·API·트리**로 끌고 온 것이다.
- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — 콘텐츠 모델과 「파서가 안 고치는 것」((4))·「부모 없이 쓴 `td` 」((6))의 정본.
- [10번 주제 — `template`·`slot`](../10-template-slot-shadow-dom/2-summary.md) — `<template>` 안도 삽입 모드를 받는 것((2))의 정본.
- 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **04번**([`innerHTML` 이 문맥에 따라 파싱하는 것](../../../../web-api/04-textcontent-innerhtml-innertext/2-summary.md))·**05번**([`<template>` 복제](../../../../web-api/05-documentfragment-and-template/2-summary.md)) — **`innerHTML`·`insertRow()` 같은 스크립트 표면**은 그쪽이 정본이다. 여기는 **그 표면이 파서가 만든 표를 어떻게 비추나**까지.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md)) — **`display: table` 계열과 표 레이아웃 알고리즘은 그 목록이 「다루지 않는 것」으로 뺐다**(표 **마크업**은 여기 17·18 에 맡긴다고 적었다). `border-collapse` 는 **46번**([테두리](../../../css/syntax/46-borders-radius-outline-shadow/2-summary.md))이 「표 모델은 이 주제 밖」이라며 한 줄만 다룬다. 그래서 (4)·(7) 의 CSS 쪽 근거는 **CSS 2.1 §17 과 렌더링 절**로만 접지했다.
- [18번 주제 — 표 머리 연결](../18-table-headers-and-scope/2-summary.md) — 이 주제의 **표 처리 모델**이 매기는 좌표로 **머리 칸을 배정하는** 다음 편.

## 용어 풀이

- **행 묶음(row group)** — `thead`·`tbody`·`tfoot`. 표 처리 모델이 행을 묶는 단위.
- **삽입 모드(insertion mode)** — 파서가 「지금 어느 문맥에 있나」를 기억하는 상태. 「in table」·「in table body」·「in body」 등.
- **foster parenting** — 표 안에 못 두는 내용을 표 **앞**으로 옮겨 붙이는 파서 동작.
- **form 요소 포인터(form element pointer)** — 파서가 「지금 열린 form」을 기억하는 칸. 트리 밖에서 `input` 을 `form` 에 잇는다.
- **표 처리 모델(table model)** — 명세가 칸마다 (x, y, 폭, 높이) 좌표를 매기는 알고리즘. 머리 칸 배정의 바탕이다.
- **`nameFrom`** — Chrome 내부 덤프가 적는 「이름이 어디서 왔나」. `caption`·`attribute`·`title`·`contents` 등.
- **내부 덤프** — `chrome://accessibility` 의 「blink」 트리. CDP 트리보다 속성이 많다.
- **열(column) 요소** — `col`·`colgroup`. 셀의 조상이 아니라 **별도 가지**다.

## 더 들어가면

- **왜 `tbody` 를 끼우나** — 표 처리 모델이 **행 묶음 단위로 좌표를 매기기** 때문이다. `tr` 이 표의 직속 자식이어도 모델은 돌지만, 파서가 DOM 을 **항상 같은 모양**(`table > tbody > tr`)으로 맞춰 두면 CSS 표 레이아웃과 스크립트가 한 경우만 다루면 된다. 연혁은 `history/web/03` 의 몫이다.
- **foster parenting 의 이름** — 「수양 부모」. 표가 못 기르는 자식을 **표의 부모가 대신 맡는다** — 명세의 「알맞은 삽입 자리」 단계가 「마지막 표의 부모 안, 그 표 바로 앞」이다. 이 판의 표는 전부 `body` 의 자식이라 `body` 가 맡았다.
- **`summary` 속성** — 옛 HTML 의 표 요약 속성은 **비준수**다. 명세는 「레이아웃 표로 분류하지 않았으면 그 값을 알려 줘도 된다(may)」고만 적는다. 이 판에서 재지 않았다.
