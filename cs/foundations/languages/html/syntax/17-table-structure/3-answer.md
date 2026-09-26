# html/syntax/17 — 표 구조: `table`/`thead`/`tbody`/`tfoot`/`caption`/`colgroup` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였고 사람이 옮겨 적지 않았다. 하네스는 맨 아래 `## 실행 검증` 절에 있다(18\~20번이 같은 하네스를 쓴다).\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [HTML-AAM](https://w3c.github.io/html-aam/), [CSS 2.1 §17](https://www.w3.org/TR/CSS2/tables.html) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ① 이다** — 소스에 쓴 표와 DOM 에 생긴 표가 갈린다(A1·A2).
> ★★ **스크린리더가 표를 어떻게 읽는지는 못 본다**(A10).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 다섯 표 전부에 `tbody` 가 생기고, 비표 내용은 표 앞으로 나간다 — `caption` 은 제자리

**출력**

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

**왜 그런가**

- ★★★ **다섯 표 모두 `<table>` 바로 안에 `<tbody>` 가 있다** — 소스에는 하나도 없었다. 「in table」 삽입 모드가 `td`·`th`·`tr` 시작 태그를 만나면 **`tbody` 를 넣고 다시 처리**한다([03번 주제](../03-parser-and-error-recovery/3-answer.md)의 결론).
- ★★ **`#나` 의 `div`·「글자」와 `#다` 의 「꼬리」·`span` 은 각 표의 바로 앞 형제**다. 「그 밖의 모든 것」 줄이 foster parenting 을 켠다. **`tr` 안에 쓴 것도** 나간다.
- ★ **`#라` 의 `caption` 은 `tbody` 뒤에 남았다.** 콘텐츠 모델은 「맨 앞」이지만 파서는 순서를 강제하지 않는다.
- **`#마` 는 `tbody` 와 `tr` 이 둘 다 생겼다** — 「in table body」 모드가 `td` 를 만나 `tr` 을 넣는다.

### 2. 7 / 14 가 표 앞으로 — `hidden`·`script`·`style`·`template`·주석·공백은 남고, `form` 은 빈 채로 남는다

**출력**

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

**왜 그런가**

- ★★★ **표 앞으로 나간 칸은 7 / 14** — `div`·`span`·글자·`img`·`input type=text`·`form` 안의 `input`·`tr` 안의 `div`.
- ★★ **`input type=text` 는 나가고 `input type=hidden` 은 남았다.** 「in table」 모드가 `input` 을 **`type` 이 `hidden` 일 때만** 「파스 오류, 그 자리에 넣는다」로 따로 적는다.
- ★★★ **`form` 은 빈 채로 표 직속에 남고 `input` 은 표 앞으로 나갔다.** 그런데 **`input.form` 은 그 `form` 이다**(`true` · `elements.length = 1` · `childNodes.length = 0`). 명세가 `form` 을 「넣고 **form 요소 포인터**를 그것에 두고 **바로 꺼낸다**」로 적어서 — 뒤의 `input` 은 트리에서 떨어져도 포인터로 이어진다.
- **공백은 제자리**(「in table text」 모드 — 공백뿐이면 그대로 넣는다), **주석도 제자리**(주석 토큰 줄), **`script`·`style`·`template` 은 「in head」 규칙**으로 제자리다.

### 3. API 는 파서가 끼운 `tbody` 를 센다 — `table > tr` 은 0개, `div.innerHTML` 은 태그를 버린다

**출력**

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

**왜 그런가**

- ★★ **`tBodies.length = 1` · `rows.length = 2` · `children = tbody`** — API 는 DOM 을 읽을 뿐이고 DOM 에는 `tbody` 가 있다.
- ★★★ **`table > tr` 이 0, `table tr` 이 2** — 트리가 `table > tbody > tr` 이다.
- ★★ **`innerHTML` 은 요소를 문맥으로 한 조각 파싱이다.** `div` 문맥은 「in body」 라 `tr`·`td` 태그를 **무시**하고 글자 `"셀"` 만 남긴다. `template` 은 「in template」, `tbody` 는 「in table body」 라 `tr` 이 산다. **`table` 문맥은 또 `tbody` 를 끼운다.**
- ★ **`insertRow()` 는 파서가 아니라 DOM 명세 단계로 `tbody` 를 만든다** — 「`rows` 가 비었고 `tbody` 가 없으면 `tbody` 를 만들어 넣는다」. `thead` 만 있는 표도 `rows` 가 비었으므로 **새 `tbody`** 가 생겼다(`thead tbody`).

### 4. 네 창이 전부 DOM 과 갈린다 — 명세 표 모델은 나머지 셋과도 다르다

**출력**

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

**왜 그런가**

- **DOM** — 발 · 본문1 · 머리 · 본문2. 파서는 `thead`·`tfoot` 을 **옮기지 않는다.**
- ★★ **`table.rows`** — 머리 · 본문1 · 본문2 · 발. 명세 `rows` 게터가 「**`thead` 의 행 먼저, 그다음 `table`·`tbody` 의 행, 끝으로 `tfoot` 의 행**」으로 정렬하라고 적는다.
- ★★ **화면** — 머리 · 본문1 · 본문2 · 발. 렌더링 절의 `thead { display: table-header-group }`·`tfoot { display: table-footer-group }` 를 CSS 표 레이아웃이 위·아래에 놓는다.
- ★★★ **명세 표 모델** — 본문1 · 머리 · 본문2 · 발. 4.9.12.1 「표 만들기」는 자식을 **트리 순서로 훑되 `tfoot` 만 「미룬 tfoot 목록」에 넣어 끝에 처리**한다. `thead` 는 **제자리**다. **화면과 같지 않다.**
- ★★ **트리(`tableRowIndex`)** — 머리 · 본문1 · 본문2 · 발. **화면을 따랐고 명세 모델과 갈렸다** — 머리 칸 배정의 기준 좌표가 명세 모델이므로, 이런 표에서는 **명세가 정한 좌표와 Chrome 이 쓰는 좌표가 다르다.**
- **N = 4** 다.

### 5. `caption` 이 이름이 되고 `aria-label` 에 밀리면 설명이 된다 — `display: none` 은 이름을 지우고, 속성 없는 `tbody` 는 트리에서 빠진다

**출력**

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

**왜 그런가**

- ★★★ **`#캡션` 이름 = `"분기별 매출"` · `nameFrom = caption`.** HTML-AAM 「table 요소의 이름 계산」 — **`aria-label`/`aria-labelledby` → 첫 child `caption` → `title`.**
- ★★ **`#aria` 는 이름 = `"에어리아 이름"`, 설명 = `"분기별 매출"`** — `caption` 이 **설명으로 밀려났다.** `#둘다` 는 반대로 `title` 이 설명으로 갔다.
- **`#늦은`(tbody 뒤 `caption`)도 이름이 됐다** — 「첫 child `caption`」이지 「첫 자식」이 아니다.
- ★ **`#숨긴`(`display: none`) 은 이름 없음, `#클립`(1px + `clip-path`) 은 이름 있음.** 트리에서 빠진 `caption` 은 이름을 못 준다(HTML-AAM 의 주석). 화면에서만 숨긴 것은 트리에 남는다.
- ★★ **둘째 소스의 `rowgroup` 은 첫 표 2개 · 둘째 표 3개 · 셋째 표 0개**다. 속성 없는 `tbody` 가 **무시된 노드로 빠졌다** — HTML-AAM 은 `tbody` 를 `rowgroup` 에 대응시키므로 **명세 대응과 갈린 구현**이다. `id` 를 달면 나온다.

### 6. 셀에 닿은 속성은 4 / 8 — 배경·테두리·폭·`visibility`

**출력**

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

**왜 그런가**

- ★★★ **4 / 8** — `background-color`(픽셀) · `border`(폭·x·픽셀) · `width`(폭) · `visibility: collapse`(폭 0).
- ★★ **`background-color` 는 「칠해진 픽셀」 칸에서만** 보였다. 셀의 계산 `background` 는 투명 그대로다.
- ★ **`color` 를 준 `col` 자신의 계산값은 `rgb(255, 0, 0)`, 셀의 계산 `color` 는 `rgb(0, 0, 0)`** 그대로다.

### 7. `col` 은 셀의 조상이 아니다 — CSS 표 모델이 따로 불러 쓰는 넷만 닿는다

- **트리의 사실** — 셀은 `tr` 의 자식이고 `col` 은 `colgroup` 의 자식이다. **`col` 은 셀의 조상이 아니므로 상속이 안 된다.** `color`·`font-weight`·`text-align`·`padding` 이 거기 걸렸다.
- **CSS 2.1 §17.3** — 「열·열 묶음 요소에 적용되는 속성: `border`·`background`·`width`·`visibility`」. ★ `border` 에는 **「표의 `border-collapse` 가 `collapse` 일 때만」** 이 붙는다. `background` 에는 「셀과 행의 배경이 투명할 때만」이 붙는다.
- **계산 `background` 로 판정하면 `background-color` 칸을 「안 닿는다」로 틀린다.** 열 배경은 셀 **아래 층**에 칠해지므로 셀의 계산값이 아니다 — 픽셀 창이 필요했다.

### 8. 「명세 표 모델」 열은 스크립트가 계산한 것 — 제5의 상태

- **어느 창도 명세 표 모델의 좌표를 직접 보고하지 않는다.** 명세 알고리즘을 **페이지 스크립트로 옮겨 계산**했다 — **제5의 상태, 「같은 질문을 다른 창으로 물었다」** 다. ★ 그 창이 못 보는 것 — **옮긴 스크립트가 명세를 잘못 읽었을 가능성**은 스크립트 자신이 못 잡는다. 그래서 소스를 전부 실었다.
- **틀린 답들이 아니다.** 창 ① 은 **소스 순서**, 창 ② 는 **CSS 가 배치한 순서**, `rows` 는 **IDL 이 정렬한 순서**를 정확히 답했다. 「행의 순서」라는 질문에는 **「어느 창의」** 가 붙어야 답이 선다.
- **부적용** — 창 ③(`innerText`)·④(`compatMode`)·⑤(요청 로그)·⑥(`renderBlockingStatus`). 표 구조 요소는 글자·문서 모드·요청·렌더 차단 어느 것도 안 만든다 — **잴 것이 없다.**

### 9. 파서·DOM·렌더링은 명세, 트리의 좌표와 `tbody` 누락은 구현 — 둘 다 명세와 갈렸다

- **`tbody` 삽입·foster parenting** — 파싱 절 「in table」·「in table body」 삽입 모드. **`rows` 정렬·`insertRow()`** — `HTMLTableElement` 의 IDL 단계. **렌더 순서** — 렌더링 절의 `display` 값 + CSS 표 레이아웃.
- ★★ **트리의 행 순서는 구현**이고 **명세 표 모델과 갈렸다**(A4). **`tbody` 가 빠진 것도 구현**이고 **HTML-AAM 의 `rowgroup` 대응과 갈렸다**(A5).
- **표의 이름 우선순위는 HTML-AAM** 의 「table 요소의 이름 계산」 절이다. 이 판은 그대로 따랐다.

### 10. 스크린리더의 읽기도 플랫폼 API 의 값도 못 쓴다 — 둘 다 제3의 상태

- **못 쓴다.** NVDA·VoiceOver·Orca 가 없다. `caption` 이 **트리의 이름이 된다**까지가 관찰이다.
- **안 보여 준다.** CDP 트리와 내부 덤프는 Chrome 의 **내부 트리**다. HTML-AAM 이 적는 **IAccessible2·UIA·ATK·AX 의 표 값**은 그 아래 층이다. **존재하는 층인데 이 판에 잴 도구가 없으니 「못 잰 것」(제3의 상태)** 이다 — 「잴 것이 없다」가 아니다. ★ `chrome://accessibility` 에는 「linux」 형식을 고르는 칸이 있으나, 탐색 중 한 번 고른 판이 빈 트리를 돌려줬을 뿐 **캡처 블록으로 남기지 않았다** — 근거로 쓰지 않는다.

### 11. 정본 경계

- **`tbody` 삽입·foster parenting** — [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 **(2)·(3)**. 여기는 그 결론이 **표의 API·순서·트리에 어떻게 번지나**부터.
- **`innerHTML` 의 문맥 파싱** — 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **04번**([`textContent` 대 `innerHTML` 대 `innerText`](../../../../web-api/04-textcontent-innerhtml-innertext/2-summary.md)).
- **`display: table` 계열** — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))은 이것을 **「다루지 않는 것」으로 뺐고 표 마크업을 HTML 17·18 에 맡겼다.** 그래서 이 주제는 CSS 쪽 근거를 **CSS 2.1 §17 과 렌더링 절**로만 접지했다.
- **다음 편** — [18번 주제](../18-table-headers-and-scope/2-summary.md) 가 이 주제의 **표 처리 모델(칸 좌표)** 을 이어받아 **각 칸에 어느 머리 칸이 묶이나**를 판다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.**\
★★ **보조 기술 없음.** NVDA·VoiceOver·Orca 가 설치돼 있지 않다.

**CDP 하네스 — 13번 판을 복사해 넷을 더했다.** [13번 주제](../13-phrasing-semantics/3-answer.md)의 `html13b-cdp.py`(기다림 = `Page.loadEventFired` · `page` 모드)를 그대로 잇고 —
① **포트를 `--remote-debugging-port=0` 으로** — 13번 판은 19910\~19999 에서 무작위로 골랐다. 같은 기계의 다른 작업과 겹칠 수 있어 **Chrome 이 고른 포트를 프로필의 `DevToolsActivePort` 에서 읽는다.**
② **`int` 모드와 `window.__내부`** — 같은 브라우저에 `chrome://accessibility` 창을 하나 더 열어 **「blink」 내부 덤프**를 받는다. CDP 에 없는 `nameFrom`·`tableCell*`·`textDirection`·`language` 가 거기 있다. ★★ **실측 사고 둘을 막았다** — 새 창이 앞으로 오면 원래 페이지가 뒤로 밀려 **빈 트리(`-`)** 가 돌아온다(고치기 전 8판 중 6판) → `Target.activateTarget` 으로 원래 페이지를 앞으로 되돌린다. 고친 뒤 6판이 전부 덤프를 받았다. 그리고 첫 판은 **덤프가 빈 채로 영원히 기다렸다** → 기다림에 **횟수 상한과 「무엇을 못 기다렸나」를 적는 예외**를 달았다(조건 폴링은 `setTimeout` 20ms).
③ **`window.__픽셀`** — 좌표마다 1×1 스크린샷을 떠 RGB 를 읽는다((7) 의 열 배경).
④ **`window.__글꼴`·`--hyphen`** — 20번이 쓴다(플랫폼 글꼴 · 하이픈 사전).
★ 이 머신의 헤드리스 Chrome 은 **CDP 가 기본으로 열려 있지 않다** — 하네스가 직접 띄운다.

```python
# html17b-cdp.py
#!/usr/bin/env python3
"""CDP 로 헤드리스 Chrome 에 붙어 창 ⑦(접근성 트리)을 연다.

사용:
  html17b-cdp.py ax   <url|파일>   접근성 트리 전체를 트리 순서로 찍는다
  html17b-cdp.py page <url|파일>   페이지의 window.__대상 = [[열쇠, 선택자], ...] 마다
                              접근성 노드(역할·이름·설명·무시 여부)를 받아 window.__AX 로 넣고
                              window.__끝() 이 돌려준 문자열을 찍는다(표 짜기·칸 세기는 페이지가 한다)
                              ★ 페이지가 window.__픽셀 = () => [[열쇠, x, y], ...] 를 두면
                                그 좌표의 화면 픽셀 RGB 를 window.__PX 로 넣어 준다
                              ★ 페이지가 window.__글꼴 = [[열쇠, 선택자], ...] 를 두면
                                그 요소를 그린 플랫폼 글꼴 이름을 window.__FONT 로 넣어 준다
                              ★ 페이지가 window.__내부 = true 를 두면 내부 덤프(아래 int)를
                                htmlId 를 열쇠로 window.__INT 에 넣어 준다(무시된 노드는 속성 ignored 가 true)
  html17b-cdp.py page --hyphen <url|파일>
                              같은 일을 하되 새 프로필에 하이픈 사전(src/hyphen-data)을 먼저 넣는다
  html17b-cdp.py int  <url|파일> <속성,…>
                              chrome://accessibility 의 「blink」 내부 트리 덤프를 받아
                              노드마다 역할·htmlId·고른 속성만 트리 순서로 찍는다

★ 기다림은 시간 상수가 아니라 이벤트다 — Page.loadEventFired 를 받은 뒤에 묻는다.
  내부 덤프는 「단추가 생겼나」·「덤프 글이 찼나」라는 조건을 페이지 안에서 await 로 기다린다.
★ CDP 포트와 프로필 경로는 실행마다 다르다 — 출력에는 안 들어간다.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.path.join(HERE, f".prof-html17b-{os.getpid()}")
# ★ 포트는 0 — Chrome 이 빈 포트를 고르고 프로필의 DevToolsActivePort 에 적는다.
#   고정 범위에서 무작위로 고르면 같은 기계의 다른 작업과 겹칠 수 있다(뒤 브라우저가 앞에 붙는다).
FLAGS = ["--headless", "--disable-gpu", "--no-sandbox", "--window-size=1000,800",
         "--force-renderer-accessibility", "--remote-debugging-port=0",
         f"--user-data-dir={PROF}", "about:blank"]


class Cdp:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, suppress_origin=True)
        self.n = 0
        self.events = []

    def send(self, method, params=None, sid=None):
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError(method + " " + json.dumps(r["error"], ensure_ascii=False))
                return r.get("result", {})
            self.events.append(r)

    def post(self, method, params=None, sid=None):
        """응답을 안 기다리고 보낸다 — 디버거 대기 중인 새 창은 run 전까지 답을 안 한다."""
        self.n += 1
        msg = {"id": self.n, "method": method, "params": params or {}}
        if sid:
            msg["sessionId"] = sid
        self.ws.send(json.dumps(msg))

    def wait(self, method, sid=None, pred=lambda p: True):
        """이미 받아 둔 이벤트부터 뒤지고, 없으면 올 때까지 막고 기다린다."""
        while True:
            for i, e in enumerate(self.events):
                if e.get("method") == method and (sid is None or e.get("sessionId") == sid) \
                        and pred(e.get("params", {})):
                    return self.events.pop(i).get("params", {})
            self.events.append(json.loads(self.ws.recv()))


def start():
    shutil.rmtree(PROF, ignore_errors=True)
    # ★ --hyphen — 하이픈 사전(hyphen-data)을 새 프로필에 미리 넣는다. 새 프로필은 사전이 비어 있다
    #   (Chrome 이 구성 요소 갱신으로 나중에 내려받는다 — 그 시점은 이 하네스가 통제하지 못한다).
    if HYPHEN:
        os.makedirs(PROF, exist_ok=True)
        shutil.copytree(os.path.join(HERE, "hyphen-data"), os.path.join(PROF, "hyphen-data"))
    proc = subprocess.Popen(["google-chrome"] + FLAGS,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    port_file = os.path.join(PROF, "DevToolsActivePort")
    for _ in range(400):          # 브라우저가 CDP 를 열 때까지 — 순서만 기다린다(값에는 안 들어간다)
        try:
            port = open(port_file).read().split()[0]
            v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version"))
            return proc, Cdp(v["webSocketDebuggerUrl"])
        except Exception:
            time.sleep(0.05)
    raise RuntimeError("CDP 가 안 열렸다")


def open_page(c, url):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "DOM.enable", "Accessibility.enable"):
        c.send(m, sid=sid)
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.loadEventFired", sid)
    return sid


def evaluate(c, sid, expr):
    r = c.send("Runtime.evaluate", {"expression": expr, "awaitPromise": True,
                                    "returnByValue": True}, sid)
    if "exceptionDetails" in r:
        d = r["exceptionDetails"]
        return "«예외 " + (d.get("exception", {}).get("description") or d.get("text", "?")) + "»"
    return r.get("result", {}).get("value")


def val(node, key):
    return (node.get(key) or {}).get("value", "")


def ax_of(c, sid, selector):
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": selector}, sid)["nodeId"]
    if not nid:
        return {"없음": True}
    nodes = c.send("Accessibility.getPartialAXTree",
                   {"nodeId": nid, "fetchRelatives": True}, sid)["nodes"]
    n = next(x for x in nodes if x.get("backendDOMNodeId") and
             x["backendDOMNodeId"] == backend(c, sid, nid))
    kids = [x for x in nodes if x.get("parentId") == n["nodeId"]]
    props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])}
    return {"역할": val(n, "role"), "이름": val(n, "name"), "설명": val(n, "description"),
            "무시": bool(n.get("ignored")), "속성": props,
            "표지": [val(x, "name") for x in kids if val(x, "role") == "ListMarker"]}


def backend(c, sid, nid):
    return c.send("DOM.describeNode", {"nodeId": nid}, sid)["node"]["backendNodeId"]


def dump_tree(c, sid):
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    SKIP = {"InlineTextBox"}

    def walk(n, d):
        role = val(n, "role")
        ignored = n.get("ignored")
        if role not in SKIP and not ignored:
            name = val(n, "name")
            props = {p["name"]: p["value"].get("value") for p in n.get("properties", [])
                     if p["name"] == "level" or (p["name"] == "url" and role == "link")}
            extra = " ".join(f"{k}={v}" for k, v in props.items())
            print(f"{'  ' * d}{role:14} 이름={name!r} {extra}".rstrip())
            d += 1
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch], d)

    for n in nodes:
        if not n.get("parentId"):
            walk(n, 0)


INTERNAL_JS = r"""(async (title) => {
  const until = async (f, what, n = 500) => { for (let i = 0; i < n; i++) { const v = f(); if (v) return v;
    await new Promise(r => setTimeout(r, 20)); }
    throw new Error("내부 덤프 — " + what + " 을 못 기다렸다: pre=" + JSON.stringify([...document.querySelectorAll('#pages pre')].map(q => q.textContent.slice(0, 80)))); };
  const b = await until(() => [...document.querySelectorAll('#pages button')].find(x =>
    x.id.endsWith('showOrRefreshTree') && x.getAttribute('aria-label') === 'Show accessibility tree for ' + title), '단추');
  // ★ 줄이 처음 그려질 때는 모드가 전부 disabled 다 — 「Web: true」로 바뀐 뒤에 눌러야 덤프가 온다
  await until(() => document.querySelector('[aria-label="Web for ' + title + '"][aria-pressed="true"]'), '모드');
  const a = document.getElementById('filter-allow'); a.value = '*'; a.dispatchEvent(new Event('change'));
  // ★ 첫 요청이 빈 트리(「-」)로 돌아오는 판이 있다 — 덤프가 찰 때까지 새로고침 단추를 다시 누른다
  const api = document.getElementById('apiType').value;
  if (api !== 'blink') throw new Error('apiType = ' + api);
  let p = null;
  for (let k = 0; k < 40 && !p; k++) {
    const r = [...document.querySelectorAll('#pages button')].find(x => x.id === b.id) || b;
    r.click();
    try { p = await until(() => { const q = document.querySelector('#pages pre');
      return q && q.textContent.includes('id#=') ? q : null; }, '덤프', 25); } catch (e) { p = null; }
  }
  if (!p) throw new Error('내부 덤프 — 40 번 눌러도 빈 트리다');
  return p.textContent;
})"""


def internal(c, sid):
    """창 ⑦ 의 내부 덤프 — 같은 브라우저의 chrome://accessibility 에 두 번째 창을 열어 받는다."""
    title = evaluate(c, sid, "document.title")
    href = evaluate(c, sid, "location.href")
    sid2 = open_page(c, "chrome://accessibility")
    # ★ 새 창이 앞으로 오면 원래 페이지가 뒤로 밀려 빈 트리(「-」)가 돌아온다 — 원래 페이지를 다시 앞으로
    for t in c.send("Target.getTargets")["targetInfos"]:
        if t["type"] == "page" and t["url"] == href:
            c.send("Target.activateTarget", {"targetId": t["targetId"]})
    text = evaluate(c, sid2, INTERNAL_JS + "(" + json.dumps(title) + ")")
    out = []
    heads = list(re.finditer(r"(\+*)id#=(-?\d+) (\S+)", text or ""))
    if not heads:
        raise RuntimeError("내부 덤프를 못 받았다: " + str(text)[:300])
    for i, m in enumerate(heads):
        body = text[m.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        attrs = {}
        for k, v in re.findall(r"(\w[\w-]*)(?:=('[^']*'|\S+))?", body):
            attrs[k] = v.strip("'") if v else True
        out.append({"깊이": len(m.group(1)) // 2, "역할": m.group(3), "속성": attrs})
    return out


def pixels(c, sid, points):
    """창 ② 의 짝 — 화면에 실제로 칠해진 색. 좌표마다 1×1 스크린샷을 떠서 RGB 를 읽는다."""
    import base64, io
    from PIL import Image
    out = {}
    for key, x, y in points:
        png = c.send("Page.captureScreenshot", {"format": "png", "clip":
                     {"x": x, "y": y, "width": 1, "height": 1, "scale": 1}}, sid)["data"]
        px = Image.open(io.BytesIO(base64.b64decode(png))).convert("RGB").getpixel((0, 0))
        out[key] = "rgb(%d, %d, %d)" % px
    return out


HYPHEN = "--hyphen" in sys.argv
if HYPHEN:
    sys.argv.remove("--hyphen")


def fonts(c, sid, targets):
    """창 ② 의 짝 — 요소의 글자를 실제로 그린 플랫폼 글꼴(CSS.getPlatformFontsForNode)."""
    c.send("CSS.enable", sid=sid)
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    out = {}
    for key, sel in targets:
        nid = c.send("DOM.querySelector", {"nodeId": root, "selector": sel}, sid)["nodeId"]
        fs = c.send("CSS.getPlatformFontsForNode", {"nodeId": nid}, sid)["fonts"]
        out[key] = [f["familyName"] for f in fs]
    return out


def main():
    mode, url = sys.argv[1], sys.argv[2]
    if "://" not in url:
        url = "file://" + os.path.abspath(url)
    proc, c = start()
    try:
        sid = open_page(c, url)
        if mode == "ax":
            dump_tree(c, sid)
        elif mode == "page":
            targets = evaluate(c, sid, "JSON.stringify(window.__대상 || [])")
            ax = {k: ax_of(c, sid, s) for k, s in json.loads(targets)}
            evaluate(c, sid, "window.__AX = " + json.dumps(ax, ensure_ascii=False))
            pts = json.loads(evaluate(c, sid, "JSON.stringify(window.__픽셀 ? window.__픽셀() : [])"))
            if pts:
                evaluate(c, sid, "window.__PX = " + json.dumps(pixels(c, sid, pts), ensure_ascii=False))
            fts = json.loads(evaluate(c, sid, "JSON.stringify(window.__글꼴 || [])"))
            if fts:
                evaluate(c, sid, "window.__FONT = " + json.dumps(fonts(c, sid, fts), ensure_ascii=False))
            if evaluate(c, sid, "window.__내부 === true"):
                nodes = internal(c, sid)
                by = {}
                for n in nodes:          # 같은 htmlId 가 둘이면 무시되지 않은 노드를 고른다
                    hid = n["속성"].get("htmlId")
                    if hid and (hid not in by or "ignored" in by[hid]["속성"]):
                        by[hid] = n
                evaluate(c, sid, "window.__INT = " + json.dumps(by, ensure_ascii=False))
            print(evaluate(c, sid, "window.__끝()"))
        elif mode == "int":
            keys = sys.argv[3].split(",")
            for n in internal(c, sid):
                a = n["속성"]
                if "ignored" in a or n["역할"] in ("staticText", "inlineTextBox"):
                    continue
                extra = " ".join(f"{k}={a[k]}" for k in keys if k in a)
                hid = ("#" + a["htmlId"]) if "htmlId" in a else ""
                print(f"{'  ' * n['깊이']}{n['역할']:14} {hid:8} {extra}".rstrip())
        else:
            sys.exit("모드는 ax | page | int")
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(PROF, ignore_errors=True)


if __name__ == "__main__":
    main()
```

**캡처 조립기** — 이 배치(17\~20)가 공유한다. 블록마다 **한 번만 돌려 받아 둔 뒤** 자르는 필터를 건다(파이프를 크롬에 물리지 않는다 — 규칙 19-A). ★ **20번 파일에는 `ax`·`--dump-dom` 을 쓰지 않는다** — 트리 이름과 DOM 직렬화에 RTL 글자가 그대로 섞이기 때문이다.

```bash
# capture.sh
#!/usr/bin/env bash
# html17b 묶음(HTML 17~20) — 문서에 실을 블록을 전부 파일로 받는다.
#   사용: ./capture.sh [출력디렉토리]    (기본 blocks)
# ★ 출력 디렉토리를 첫머리에서 절대경로로 정규화한다(규칙 25).
# ★ set -o pipefail — 없으면 파이프 뒤 명령의 종료 코드가 기록된다.
# ★ 자르는 명령은 배너에 적되 실행에는 파이프를 물리지 않는다 — 전부 받아 둔 뒤 필터를 건다.
# ★ grep -c 를 블록의 마지막 명령으로 두지 않는다(0건이면 exit 1).
# ★ 표준 출력만 싣는다 — 표준 오류는 버린다(규칙 18).
# ★ RTL 글자가 출력에 섞이는 모드(ax·dump-dom)는 20번 파일에 쓰지 않는다 — 출력은 코드 포인트 16진 값뿐이다.
set -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${1:-blocks}"
case $OUT_DIR in /*) ;; *) OUT_DIR="$HERE/$OUT_DIR" ;; esac
SRC="$HERE/src"
RAW="$OUT_DIR/.raw"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR" "$RAW"
cd "$SRC" || exit 1

CH="google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800"
MARK="sed -n '/^--OUT\$/,/^OUT--\$/{//!p}'"

run() {  # run <열쇠> <명령문자열> — 한 번만 돌려 표준 출력과 종료 코드를 받아 둔다
  local key="$1" cmd="$2"
  if [ ! -f "$RAW/$key.rc" ]; then
    eval "$cmd" > "$RAW/$key.out" 2>/dev/null
    printf '%s' "$?" > "$RAW/$key.rc"
  fi
}

# 출력 블록 — 코드펜스째 뱉는다. 배너 = 실제로 던진 명령 + (있으면) 자르는 필터.
out_block() {  # out_block <블록이름> <열쇠> <배너명령> <명령> [필터]
  local name="$1" key="$2" banner="$3" cmd="$4" pipe="$5" rc
  run "$key" "$cmd"
  rc="$(cat "$RAW/$key.rc")"
  {
    printf '```text\n'
    if [ -n "$pipe" ]; then
      printf '$ %s | %s\n' "$banner" "$pipe"
      eval "cat '$RAW/$key.out' | $pipe"
    else
      printf '$ %s\n' "$banner"
      cat "$RAW/$key.out"
    fi
    printf '(exit %s)\n' "$rc"
    printf '```\n'
  } > "$OUT_DIR/$name.txt"
}

dom()  { out_block "$1" "dom-$2" "$CH --dump-dom $2 2>/dev/null" "$CH --dump-dom $2" "$3"; }
cdp()  { out_block "$1" "cdp-$2-$3" "python3 html17b-cdp.py $2 $3" "python3 html17b-cdp.py $2 $3" "$4"; }
cint() { out_block "$1" "int-$2-$3" "python3 html17b-cdp.py int $2 $3" "python3 html17b-cdp.py int $2 $3" "$4"; }

# 소스 삽입용 블록 — 원고의 펜스 안에 들어가므로 펜스로 감싸지 않는다.
# 배너는 여기서만 찍는다(basename — 규칙 28). 원고에 손으로 쓰면 이중 배너가 된다.
src_html() { { printf '<!-- %s -->\n' "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_js()   { { printf '// %s\n'        "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_py()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_sh()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }

out_block ver ver "google-chrome --version" "google-chrome --version"

# ------------------------------------------------------------ 17 표 구조
src_html 17-parse-src    html17b-17-parse.html
dom      17-parse-dom    html17b-17-parse.html
src_html 17-foster-src   html17b-17-foster.html
cdp      17-foster-out   page html17b-17-foster.html
src_html 17-api-src      html17b-17-api.html
cdp      17-api-a        page html17b-17-api.html "sed -n '1,6p'"
cdp      17-api-b        page html17b-17-api.html "sed -n '8,12p'"
cdp      17-api-c        page html17b-17-api.html "sed -n '14,16p'"
src_html 17-order-src    html17b-17-order.html
cdp      17-order-out    page html17b-17-order.html
src_html 17-name-src     html17b-17-name.html
cdp      17-name-out     page html17b-17-name.html
src_html 17-col-src      html17b-17-col.html
cdp      17-col-out      page html17b-17-col.html
src_html 17-ax-src       html17b-17-ax.html
cdp      17-ax-out       ax   html17b-17-ax.html
src_html 17-demo-src     html17b-17-demo.html
src_html 17-democheck-src html17b-17-democheck.html
dom      17-democheck-out html17b-17-democheck.html "$MARK"
src_html 17-democheck2-src html17b-17-democheck2.html
dom      17-democheck2-out html17b-17-democheck2.html "$MARK"

# ------------------------------------------------------------ 18 표 머리 연결
src_js   18-model-src    html17b-18-model.js
src_html 18-scope-src    html17b-18-scope.html
cdp      18-scope-out    page html17b-18-scope.html
src_html 18-grid-src     html17b-18-grid.html
cdp      18-grid-a       page html17b-18-grid.html "sed -n '1,27p'"
cdp      18-grid-b       page html17b-18-grid.html "sed -n '29,45p'"
cdp      18-grid-c       page html17b-18-grid.html "sed -n '47,64p'"
cdp      18-grid-d       page html17b-18-grid.html "sed -n '66,69p'"
cdp      18-grid-e       page html17b-18-grid.html "sed -n '71,76p'"
cint     18-grid-int     html17b-18-grid.html tableCellColumnIndex,tableCellRowIndex,tableCellColumnSpan,tableCellRowSpan "sed -n '1,35p'"
src_html 18-layout-src   html17b-18-layout.html
cdp      18-layout-out   page html17b-18-layout.html

# ------------------------------------------------------------ 19 figure·address·hr
src_html 19-figure-src   html17b-19-figure.html
cdp      19-figure-out   page html17b-19-figure.html
cdp      19-figure-ax    ax   html17b-19-figure.html "sed -n '1,16p'"
cint     19-figure-int   html17b-19-figure.html nameFrom,htmlTag "sed -n '1,8p'"
dom      19-figure-dom   html17b-19-figure.html "grep -n 'id=\"f3\"'"
src_html 19-misc-src     html17b-19-misc.html
cdp      19-misc-out     page html17b-19-misc.html
dom      19-misc-dom     html17b-19-misc.html "grep -n '<select'"

# ------------------------------------------------------------ 20 lang·dir·양방향
src_html 20-auto-src     html17b-20-auto.html
cdp      20-auto-out     page html17b-20-auto.html
src_html 20-bdi-src      html17b-20-bdi.html
cdp      20-bdi-a        page html17b-20-bdi.html "sed -n '1,6p'"
cdp      20-bdi-b        page html17b-20-bdi.html "sed -n '8,15p'"
src_html 20-sel-src      html17b-20-sel.html
cdp      20-sel-a        page html17b-20-sel.html "sed -n '1,5p'"
cdp      20-sel-b        page html17b-20-sel.html "sed -n '7,11p'"
cdp      20-sel-c        page html17b-20-sel.html "sed -n '13,17p'"
cint     20-sel-int      html17b-20-sel.html htmlTag,language,textDirection
src_html 20-lang-src     html17b-20-lang.html
cdp      20-lang-plain   page html17b-20-lang.html
out_block 20-lang-hyphen cdp-hyphen-20-lang "python3 html17b-cdp.py page --hyphen html17b-20-lang.html" \
  "python3 html17b-cdp.py page --hyphen html17b-20-lang.html"
out_block 20-hyphen-ver  ls-hyphen "ls hyphen-data" "ls hyphen-data"
src_html 20-demo-src     html17b-20-demo.html
src_html 20-democheck-src html17b-20-democheck.html
dom      20-democheck-out html17b-20-democheck.html "$MARK"

# ------------------------------------------------------------ 하네스 (3-answer 실행 검증)
src_py   cdp-py          html17b-cdp.py
src_sh   capture-sh      ../capture.sh
```

**demo 블록** — [2-summary.md](2-summary.md) 의 `demo` 를 **같은 마크업 + 측정 프로브**로 던졌다.

```html
<!-- html17b-17-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 17 검증</title>
<body>
<table border="1">
  <tfoot><tr><td>tfoot — 소스의 맨 앞</td></tr></tfoot>
  <tbody><tr><td>tbody — 소스의 가운데</td></tr></tbody>
  <thead><tr><td>thead — 소스의 맨 뒤</td></tr></thead>
</table>
<script>
const O = ["창 폭 = " + window.innerWidth];
const 행 = [...document.querySelectorAll("tr")].map(r => ({ 글: r.textContent.trim(), top: r.getBoundingClientRect().top }));
O.push("DOM 순서      = " + 행.map(r => r.글.split(" ")[0]).join(" · "));
O.push("화면 위→아래  = " + [...행].sort((a, b) => a.top - b.top).map(r => r.글.split(" ")[0] + "@" + r.top.toFixed(0)).join(" · "));
document.body.appendChild(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-17-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
창 폭 = 1000
DOM 순서      = tfoot · tbody · thead
화면 위→아래  = thead@11 · tbody@41 · tfoot@71
(exit 0)
```

**「바꿔 볼 것」도 던졌다** — `thead` 를 `tbody` 로 바꾼 사본이다(글자는 그대로라 줄의 이름표는 「thead」로 찍힌다).

```html
<!-- html17b-17-democheck2.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 17 검증 — 바꿔 볼 것</title>
<body>
<table border="1">
  <tfoot><tr><td>tfoot — 소스의 맨 앞</td></tr></tfoot>
  <tbody><tr><td>tbody — 소스의 가운데</td></tr></tbody>
  <tbody><tr><td>thead — 소스의 맨 뒤</td></tr></tbody>
</table>
<script>
const O = ["창 폭 = " + window.innerWidth];
const 행 = [...document.querySelectorAll("tr")].map(r => ({ 글: r.textContent.trim(), top: r.getBoundingClientRect().top }));
O.push("DOM 순서      = " + 행.map(r => r.글.split(" ")[0]).join(" · "));
O.push("화면 위→아래  = " + [...행].sort((a, b) => a.top - b.top).map(r => r.글.split(" ")[0] + "@" + r.top.toFixed(0)).join(" · "));
document.body.appendChild(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-17-democheck2.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
창 폭 = 1000
DOM 순서      = tfoot · tbody · thead
화면 위→아래  = tbody@11 · thead@41 · tfoot@71
(exit 0)
```

- **바꾸기 전** — thead 줄이 맨 위(11), tfoot 줄이 맨 아래(71). **바꾼 뒤** — 그 줄이 **가운데(41)** 로 내려왔고 tfoot 은 여전히 맨 아래다.
- ★ 이 블록의 **top 값은 머신 사이에서 흔들린다**(설치된 글꼴). 근거는 **순서**다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **다섯 표의 `--dump-dom`** | 3 | 동작 방식 (1) · A1 |
| **foster 격자**(14칸) | 3 | 동작 방식 (2) · A2 |
| **스크립트 API**(`tBodies`·`innerHTML`·`insertRow`) | 3 | 동작 방식 (3) · A3 |
| **행 순서 다섯 창** | 3 | 동작 방식 (4) · A4 |
| **표의 이름**(아홉 표) · **행 묶음 트리** | 3 | 동작 방식 (5)·(6) · A5 |
| **`col` 격자**(여덟 속성 + 픽셀) | 3 | 동작 방식 (7) · A6 |
| **demo 검증 · 「바꿔 볼 것」** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| 트리의 행 좌표 | **화면 순서**(thead 먼저) | 명세 표 모델(thead 제자리)과 갈린다 |
| 속성 없는 `tbody` | **트리에서 빠진다** | HTML-AAM 의 `rowgroup` 대응과 갈린다 |
| `nameFrom` 이름 | `caption`·`attribute`·`title` | 내부 덤프의 형식이다 — 판마다 이름이 바뀔 수 있다 |
| `chrome://accessibility` 의 화면 구조 | 단추 `aria-label` = 「Show accessibility tree for 〈제목〉」 | 하네스가 그 글자로 단추를 찾는다 — 판이 오르면 다시 확인 |

**안 돌려 본 것** — ① **Firefox·Safari 의 파서와 트리**(엔진이 없다). ② **`summary` 속성** — 비준수 속성이라 뺐다. ③ **`caption` 에 `aria-labelledby` 로 표 밖 제목을 잇는 것** — 목록의 **43번 주제**(이름 계산)의 몫이다.

**못 잰 것**(「안 돌려 본 것」과 다르다) — ① **스크린리더의 표 읽기 전부**(A10). ② **플랫폼 접근성 API 층** — CDP·내부 덤프는 그 위의 내부 트리까지다.

**부적용인 창** — **창 ③ · ④ · ⑤ · ⑥.** 표 구조 요소는 글자·문서 모드·요청·렌더 차단 어느 것도 바꾸지 않는다 — **잴 것이 없다.**

## 용어 풀이

- **삽입 모드** — 파서가 지금 어느 문맥에 있는지 기억하는 상태. 「in table」에서는 `tr` 앞에 `tbody` 를 넣는다.
- **foster parenting** — 표 안에 못 두는 것을 표 **앞**으로 옮겨 붙이는 파서 동작.
- **form 요소 포인터** — 파서가 기억하는 「지금 열린 form」. 트리 밖에서 `input` 과 `form` 을 잇는다.
- **표 처리 모델** — 칸마다 좌표를 매기는 명세 알고리즘. 18번의 머리 칸 배정이 그 위에 선다.
- **`nameFrom`** — 내부 덤프가 적는 이름의 출처.
- **제5의 상태** — 같은 질문을 **다른 창으로 물어** 답을 얻은 것. 이 주제에서는 명세 표 모델을 스크립트로 계산했다.
