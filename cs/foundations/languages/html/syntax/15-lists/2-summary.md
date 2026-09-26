# html/syntax/15 — 목록: `ul`/`ol`(`start`·`reversed`·`value`)/`dl` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The `ol` element」](https://html.spec.whatwg.org/multipage/grouping-content.html#the-ol-element)·[「The `li` element」](https://html.spec.whatwg.org/multipage/grouping-content.html#the-li-element)(서수 값 알고리즘)·[「The `dl` element」](https://html.spec.whatwg.org/multipage/grouping-content.html#the-dl-element) 절, [렌더링 절 「Lists」](https://html.spec.whatwg.org/multipage/rendering.html#lists), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 하네스는 [13번 주제의 3-answer.md](../13-phrasing-semantics/3-answer.md) `## 실행 검증` 절에 있다(이 배치가 공유한다).\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.** ★ 특히 **「`list-style: none` 이 목록 역할을 지운다」는 WebKit(Safari)의 동작으로 알려져 있는데 WebKit 이 이 머신에 없다 — 「미실행」이다.**
> **버전** — HTML 에는 언어 버전이 없다. `ol`·`ul`·`li`·`dl` 은 오래된 표면이다. `reversed` 와 `dl` 안의 `div` 묶음도 **이 판에서 동작한다**(아래 실측) — 들어온 시기는 이 문서가 확인하지 않았다.
> **선행** — [05번 주제](../05-content-categories-and-models/2-summary.md)(`ul` 의 콘텐츠 모델 — 「`li` 와 스크립트 지원 요소만」).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑦ 대 창 ②·③ 이다 — 번호는 접근성 트리(`ListMarker`)에만 있고, DOM 프로퍼티(`li.value`·`ol.start`)와 `innerText` 에는 없다.** 거기에 `dl` 의 묶음은 **창 ①(파서)** 이 본다.

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
| **흔들린다** | CDP 포트·프로필 경로 | 실행마다 무작위 — **출력에는 안 들어간다** |
| **안 흔들린다** | 접근성 트리의 **표지 글자**(`"3. "`·`"IV. "`·`"• "`) | 같은 판이면 결정적이다 |
| **안 흔들린다** | `ol.start`·`li.value` 의 값 | IDL 반영이 명세에 있다 |
| **안 흔들린다** | `--dump-dom` 트리 | 파싱 알고리즘이 명세에 있다 |
| **안 흔들린다** | 「같은 칸 N / M」 | 스크립트가 센다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑦ 접근성 트리** | ★ **쓴다 — 본체** | 번호가 **실제로 무엇으로 찍혔나** — `ListMarker` 노드의 이름((1)) |
| **② 프로브**(IDL·`::marker` 계산값) | ★ **쓴다 — 본체의 짝** | DOM 이 번호를 **아나** — **모른다**((1)·(2)) |
| **③ `innerText`** | ★ **쓴다** | 번호가 **글자로 남나** — **안 남는다**((1)) |
| **① `--dump-dom`** | ★ **쓴다 — `dl`·`ul` 의 본체** | 파서가 **고치나** — **안 고친다**((3)) |
| **④ `compatMode`** | **부적용** | 문서 모드와 무관하다 — **잴 것이 없다** |
| **⑤ 서버 요청 로그** | **부적용** | 요청을 일으키는 요소가 없다 |
| **⑥ `renderBlockingStatus`** | **부적용** | 렌더를 막는 자원이 없다 |

- ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「셋째 항목의 번호는?」을 창 ② 에 물으면 `li.value` 가 **`0`** 을 준다. 틀린 답이 아니다 — **`value` 속성이 없다**는 정답이다. 같은 질문을 창 ⑦ 로 물어야 **`"3. "`** 이 나온다. ★ **그리고 둘이 우연히 같아지는 칸이 있다**((2) — 4 / 27). 그 칸만 보고 「DOM 이 번호를 안다」고 읽으면 틀린다.
- ★ **`::marker` 계산값은 창 ② 인데도 번호를 안 준다** — `content` 가 전부 `normal` 이다((1)). 번호는 **계산값 단계 뒤**(카운터를 세는 단계)에서 정해진다.

## 한눈에 — 쉽게 말하면

**★ 목록의 번호는 원고에 없다. 인쇄소가 찍을 때 세는 것이다.**

은행 번호표 기계에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 줄 선 **손님들** | **`<li>`** 들 |
| 번호표 기계의 **시작 번호 설정** | **`<ol start>`** |
| 기계를 **거꾸로 세게** 돌려 놓은 것 | **`<ol reversed>`** |
| 한 손님에게 **번호를 손으로 찍어 준 것** — 뒷사람은 그다음부터 받는다 | **`<li value>`** |
| **숫자 대신 알파벳·로마자** 표 | **`type="a"`·`type="I"`** |
| 번호표를 **손님 명단에 적어 두지 않는다** | 번호는 **`li.value` 에도 `innerText` 에도 없다** |
| 번호를 알려면 **기계가 뽑은 표**를 봐야 한다 | **접근성 트리의 `ListMarker`** |
| 「사과 — 빨갛다」 식의 **용어 사전** | **`<dl>`**(`dt` 용어 · `dd` 설명) |

- **번호는 DOM 에 없다.** `li.value` 는 `value` 속성이 없으면 **`0`**, `reversed` 목록의 `ol.start` 는 **`1`** 이다 — 화면의 번호와 다르다((1)).
- **`value` 는 뒷번호를 끌고 간다** — `1, 7, 8`. 거꾸로 목록이면 `3, 7, 6`((1)).
- **파서는 목록을 안 고친다** — `<ul>` 안의 `<div>`·글자·`<p>` 가 그대로 남는다((3)).

```text
  같은 셋째 항목을 세 창에 물으면

  <ol reversed>                         창 ②  li.value          0      (속성이 없다)
    <li>가</li>                          창 ②  ol.start          1      (reversed 인데도)
    <li>나</li>                          창 ③  innerText         "가\n나\n다"  (번호 없음)
    <li>다</li>   <- 이 항목             창 ⑦  ListMarker        "1. "  ★ 여기에만 번호가 있다
  </ol>

  번호는 원고(DOM)에 없고, 인쇄(렌더) 단계에서 센 결과로만 존재한다.
```

실무에서 이게 터지는 자리는 **「3번 항목을 지우면 번호가 알아서 당겨진다」를 믿고 본문에서 「위의 3번」이라고 적는 것**이다 — 번호는 당겨지지만 **본문 글자는 안 당겨진다.**\
그리고 더 조용한 자리는 **스크립트로 번호를 읽으려는 것**이다 — `li.value` 는 **`0`** 을 준다.

> **서수 값(ordinal value)** — 명세가 `li` 마다 계산하는 번호. **표지(marker)가 찍는 값**이 이것이다.\
> 예: `<ol start="5">` 의 첫 `li` 는 서수 값 5.

> **`::marker`** — 목록 항목 앞의 표지(번호·점)를 가리키는 의사 요소.\
> 예: `li::marker { color: red }` 로 번호만 빨갛게.

## 이 주제가 답하려는 질문

1. **목록의 번호는 어디에 있나** — DOM 인가, 글자인가, 렌더인가. `start`·`reversed`·`value` 가 그것을 어떻게 바꾸나.
2. **`ul` 안에 `li` 가 아닌 것을 넣거나 `dl` 을 `div` 로 묶으면 파서와 접근성 트리가 무엇을 하나.**
3. **`list-style: none` 이 목록의 역할을 지우나** — 이 판(Chrome)에서.

## 동작 방식

### (1) 창 ② × 창 ③ × 창 ⑦ — 열두 목록의 번호를 세 창에 묻는다

**언제 쓰나** — 이 주제의 본체. **「번호는 DOM 에 있다」라는 착각을 한 블록으로 깨뜨린다.**

`start`(5·0·-2·틀린 값)·`reversed`·`value`·`type` 을 한 목록씩 바꿔 가며 열두 목록을 놓고, 목록마다 **`ol.start` · 세 `li` 의 `value` · `::marker` 계산값 · 접근성 트리의 표지 · `innerText`** 를 한 줄에 찍었다.

```html
<!-- html13b-15-num.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>15 번호는 어디 있나</title>
</head>
<body>
<ol id="base"><li>가</li><li>나</li><li>다</li></ol>
<ol id="s5" start="5"><li>가</li><li>나</li><li>다</li></ol>
<ol id="s0" start="0"><li>가</li><li>나</li><li>다</li></ol>
<ol id="sneg" start="-2"><li>가</li><li>나</li><li>다</li></ol>
<ol id="rev" reversed><li>가</li><li>나</li><li>다</li></ol>
<ol id="rev10" reversed start="10"><li>가</li><li>나</li><li>다</li></ol>
<ol id="val"><li>가</li><li value="7">나</li><li>다</li></ol>
<ol id="revval" reversed><li>가</li><li value="7">나</li><li>다</li></ol>
<ol id="a" type="a"><li>가</li><li>나</li><li>다</li></ol>
<ol id="I" type="I" start="4"><li>가</li><li>나</li><li>다</li></ol>
<ol id="bad" start="삼"><li>가</li><li>나</li><li>다</li></ol>
<ul id="ul"><li>가</li><li>나</li><li>다</li></ul>
<script>
const 목록 = ["base", "s5", "s0", "sneg", "rev", "rev10", "val", "revval", "a", "I", "bad", "ul"];
window.__대상 = [];
for (const id of 목록) for (let i = 1; i <= 3; i++)
  window.__대상.push([id + "/" + i, "#" + id + " > li:nth-child(" + i + ")"]);
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("목록".padEnd(12) + "속성".padEnd(22) + "ol.start  li.value 셋   ::marker content  접근성 트리의 표지          innerText");
  for (const id of 목록) {
    const L = document.getElementById(id);
    const 속성 = [...L.attributes].filter(a => a.name !== "id").map(a => a.name + (a.value ? "=" + a.value : "")).join(" ") || "—";
    const 값 = [...L.children].map(li => li.value).join(",");
    const 마커 = getComputedStyle(L.children[0], "::marker").content;
    const 이름 = [1, 2, 3].map(i => __AX[id + "/" + i].표지.join("")).map(J).join(" ");
    O.push(id.padEnd(10) + 속성.padEnd(22) + String(L.start ?? "—").padEnd(10) + 값.padEnd(12)
      + 마커.padEnd(17) + 이름.padEnd(26) + J(L.innerText));
  }
  O.push("");
  O.push("DOM 이 번호를 아나 — li.value 가 표지의 번호와 같은 칸을 센다(숫자 표지인 ol 만)");
  let 같음 = 0, 전체 = 0;
  const 같은칸 = [];
  for (const id of 목록) {
    const L = document.getElementById(id);
    if (L.nodeName !== "OL") continue;
    [...L.children].forEach((li, i) => {
      const n = parseInt(__AX[id + "/" + (i + 1)].표지.join(""), 10);
      if (Number.isNaN(n)) return;
      전체++;
      if (li.value === n) { 같음++; 같은칸.push(id + "/" + (i + 1) + " (" + n + ")"); }
    });
  }
  O.push("  같은 칸 = " + 같은칸.join(" · "));
  O.push("같은 칸 = " + 같음 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html13b-cdp.py page html13b-15-num.html | sed -n '1,13p'
목록          속성                    ol.start  li.value 셋   ::marker content  접근성 트리의 표지          innerText
base      —                     1         0,0,0       normal           "1. " "2. " "3. "         "가\n나\n다"
s5        start=5               5         0,0,0       normal           "5. " "6. " "7. "         "가\n나\n다"
s0        start=0               0         0,0,0       normal           "0. " "1. " "2. "         "가\n나\n다"
sneg      start=-2              -2        0,0,0       normal           "-2. " "-1. " "0. "       "가\n나\n다"
rev       reversed              1         0,0,0       normal           "3. " "2. " "1. "         "가\n나\n다"
rev10     reversed start=10     10        0,0,0       normal           "10. " "9. " "8. "        "가\n나\n다"
val       —                     1         0,7,0       normal           "1. " "7. " "8. "         "가\n나\n다"
revval    reversed              1         0,7,0       normal           "3. " "7. " "6. "         "가\n나\n다"
a         type=a                1         0,0,0       normal           "a. " "b. " "c. "         "가\n나\n다"
I         type=I start=4        4         0,0,0       normal           "IV. " "V. " "VI. "       "가\n나\n다"
bad       start=삼               1         0,0,0       normal           "1. " "2. " "3. "         "가\n나\n다"
ul        —                     —         0,0,0       normal           "• " "• " "• "            "가\n나\n다"
(exit 0)
```

```text
  start · reversed · value 가 만든 번호 (접근성 트리의 표지)

  목록                       1번째   2번째   3번째
  (속성 없음)                  1       2       3
  start=5                     5       6       7
  start=0                     0       1       2
  start=-2                   -2      -1       0
  reversed                    3       2       1     <- 항목 수에서 시작
  reversed start=10          10       9       8
  value=7 을 둘째에            1       7       8     <- 뒷번호를 끌고 간다
  reversed + 둘째 value=7      3       7       6     <- 거꾸로도 끌고 간다
  type=a                      a       b       c
  type=I start=4             IV       V      VI
  start=삼 (정수가 아님)        1       2       3     <- 없는 것처럼
  ul                          •       •       •
```

- ★★★ **번호는 창 ⑦ 에만 있다.** `li.value` 는 `value` 속성이 없으면 **`0`**, `::marker` 의 계산값은 **전부 `normal`**, `innerText` 는 **번호 없이 글자만**이다.
- ★★ **`reversed` 목록의 `ol.start` 는 `1`** 인데 첫 표지는 `3.` 이다. 명세 IDL 이 **`[Reflect, ReflectDefault=1] start`** — 속성이 없으면 **무조건 1** 을 돌려준다. 명세의 「시작 값」 알고리즘(`reversed` 면 **항목 수**)은 IDL 이 아니라 **표지를 셀 때**만 돈다.
- ★★ **`value` 는 뒤를 끌고 간다.** 둘째에 `value="7"` 을 주면 셋째가 **8**, 거꾸로 목록이면 **6** 이다. 명세 서수 값 알고리즘이 「`value` 가 있으면 그 값으로 **세던 수를 갈아 끼우고** 거기서 계속 센다」이기 때문이다.
- **음수·0 도 된다** — `start="-2"` 가 `-2, -1, 0` 이다.
- **정수가 아닌 `start` 는 없는 것처럼** — `start="삼"` 이 `1, 2, 3` 이고 `ol.start` 도 `1` 이다.
- **`type="I"` 와 `start="4"` 는 같이 간다** — 넷째 로마 숫자 `IV` 부터.
- ★ **`ul` 의 `ol.start` 칸은 `—`** 이다 — `HTMLUListElement` 에는 `start` 프로퍼티 자체가 **없다**(`undefined`).

> **`ReflectDefault=1`** — 속성이 없을 때 IDL 이 돌려줄 기본값을 1 로 정한 명세 표기.\
> 예: `<ol reversed>` 의 `.start` 는 `1` — 화면의 첫 번호(3)와 다르다.

### (2) 창 ② — DOM 이 번호를 「아는 것처럼 보이는」 칸

**언제 쓰나** — (1) 을 **표로만 읽으면 넘어지는 자리.**

(1) 과 같은 실행의 끝이다. `li.value` 가 표지의 번호와 **글자로 같은 칸**을 셌다.

```text
$ python3 html13b-cdp.py page html13b-15-num.html | sed -n '15,17p'
DOM 이 번호를 아나 — li.value 가 표지의 번호와 같은 칸을 센다(숫자 표지인 ol 만)
  같은 칸 = s0/1 (0) · sneg/3 (0) · val/2 (7) · revval/2 (7)
같은 칸 = 4 / 27
(exit 0)
```

- ★★★ **같은 칸은 27 중 4다.** 그런데 넷 다 **우연**이다.
  - **`s0/1`·`sneg/3`** — 번호가 **0** 이라 `value` 없는 `li.value` 의 기본값 **0** 과 겹쳤다.
  - **`val/2`·`revval/2`** — **`value="7"` 을 손으로 쓴 칸**이라 속성을 비춘 값이 7 이다.
- ★ **즉 `li.value` 는 「번호」가 아니라 「`value` 속성」이다.** 명세도 그렇게 적는다 — 「`value` IDL 은 서수 값에 직접 대응하지 않는다. **속성을 비출 뿐**이다. `1, 3, 4` 로 찍히는 목록에서 IDL 은 `0, 3, 0` 을 돌려준다」.
```text
  li.value 가 번호와 「같아 보이는」 네 칸 — 전부 다른 이유로 같다

  칸         표지    li.value   왜 같은가
  s0/1        0        0        번호가 마침 0 이고, value 없는 li.value 의 기본값도 0
  sneg/3      0        0        〃
  val/2       7        7        value="7" 을 손으로 썼다 — 속성을 비춘 것
  revval/2    7        7        〃

  나머지 23칸    li.value = 0 인데 표지는 1·2·3·5·10 …      <- 이쪽이 참모습
```

- ★★ **이 칸들이 「DOM 이 번호를 안다」는 거짓 근거가 된다.** 한두 칸만 찍어 확인하면 **우연히 맞는 칸**을 고를 수 있다 — 전수 격자를 돌린 이유다.

### (3) 창 ① — 파서는 목록을 안 고친다

**언제 쓰나** — `<ul>` 에 `<li>` 가 아닌 것을 넣었을 때, `<dl>` 을 `div` 로 묶었을 때, `dt`/`dd` 를 안 닫았을 때.

```html
<!-- html13b-15-tree.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>15 목록의 트리</title>
</head>
<body>
<ul id="섞임"><div>li 가 아닌 div</div>그냥 글자<li>진짜 li</li><p>p 도 넣었다</p></ul>
<ul id="없앰" style="list-style: none"><li>표지를 지운 목록</li><li>둘째</li></ul>
<li id="홀로">목록 밖의 li</li>
<dl id="묶음">
  <div><dt>사과</dt><dd>빨갛다</dd></div>
  <div><dt>포도</dt><dt>머루</dt><dd>보랏빛이다</dd><dd>송이로 달린다</dd></div>
</dl>
<dl id="생략"><dt>생략한 dt<dd>생략한 dd<dt>다음 dt<dd>다음 dd</dl>
<dl id="거꾸로"><dd>dt 없이 dd 먼저</dd><dt>뒤늦은 dt</dt></dl>
</body>
</html>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html13b-15-tree.html 2>/dev/null
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>15 목록의 트리</title>
</head>
<body>
<ul id="섞임"><div>li 가 아닌 div</div>그냥 글자<li>진짜 li</li><p>p 도 넣었다</p></ul>
<ul id="없앰" style="list-style: none"><li>표지를 지운 목록</li><li>둘째</li></ul>
<li id="홀로">목록 밖의 li</li>
<dl id="묶음">
  <div><dt>사과</dt><dd>빨갛다</dd></div>
  <div><dt>포도</dt><dt>머루</dt><dd>보랏빛이다</dd><dd>송이로 달린다</dd></div>
</dl>
<dl id="생략"><dt>생략한 dt</dt><dd>생략한 dd</dd><dt>다음 dt</dt><dd>다음 dd</dd></dl>
<dl id="거꾸로"><dd>dt 없이 dd 먼저</dd><dt>뒤늦은 dt</dt></dl>


</body></html>
(exit 0)
```

```text
  파서가 한 일과 안 한 일

  <ul><div>…</div>그냥 글자<li>…</li><p>…</p></ul>    그대로       ★ 안 고친다
  <li> (목록 밖)                                      그대로       ★ 안 고친다
  <dl><div><dt>…<dd>…</div>…</dl>                    그대로       (유효한 묶음)
  <dl><dt>생략<dd>생략<dt>다음<dd>다음</dl>             닫아 준다    ★ 이것만 고친다
  <dl><dd>먼저</dd><dt>뒤늦게</dt></dl>                그대로       ★ 순서도 안 고친다
```

- ★★★ **`<ul>` 안의 `<div>`·맨 글자·`<p>` 가 그대로 남는다.** 콘텐츠 모델(「`li` 와 스크립트 지원 요소만」)을 어겼는데 **파서는 옮기지도 감싸지도 않는다.** [03번 주제](../03-parser-and-error-recovery/2-summary.md)의 `<p><div>` 처럼 **트리를 바꾸는 오류 복구가 이 판의 목록에서는 한 번도 일어나지 않았다**(관찰 — 파서 명세의 해당 절은 이 배치가 열어 보지 않았다).
- **목록 밖의 `<li>` 도 그대로**다.
- ★ **파서가 한 일은 딱 하나 — 생략한 `</dt>`·`</dd>` 를 닫아 준 것.** 명세가 두 끝 태그를 **생략 가능**으로 정해 두었기 때문이다(「`dt` 끝 태그는 바로 뒤에 `dt`·`dd` 가 오면 생략할 수 있다」).
- **`dd` 가 `dt` 보다 먼저 와도 그대로**다. 순서는 파서가 모른다.

### (4) 창 ⑦ — 같은 파일의 접근성 트리

(3) 과 같은 파일이다.

```text
$ python3 html13b-cdp.py ax html13b-15-tree.html
RootWebArea    이름='15 목록의 트리'
  list           이름=''
    generic        이름=''
      StaticText     이름='li 가 아닌 div'
    StaticText     이름='그냥 글자'
    listitem       이름='' level=1
      ListMarker     이름='• '
      StaticText     이름='진짜 li'
    paragraph      이름=''
      StaticText     이름='p 도 넣었다'
  list           이름=''
    listitem       이름='' level=1
      StaticText     이름='표지를 지운 목록'
    listitem       이름='' level=1
      StaticText     이름='둘째'
  listitem       이름='' level=1
    ListMarker     이름='• '
    StaticText     이름='목록 밖의 li'
  DescriptionList 이름=''
    term           이름='사과'
      StaticText     이름='사과'
    definition     이름=''
      StaticText     이름='빨갛다'
    term           이름='포도'
      StaticText     이름='포도'
    term           이름='머루'
      StaticText     이름='머루'
    definition     이름=''
      StaticText     이름='보랏빛이다'
    definition     이름=''
      StaticText     이름='송이로 달린다'
  DescriptionList 이름=''
    term           이름='생략한 dt'
      StaticText     이름='생략한 dt'
    definition     이름=''
      StaticText     이름='생략한 dd'
    term           이름='다음 dt'
      StaticText     이름='다음 dt'
    definition     이름=''
      StaticText     이름='다음 dd'
  DescriptionList 이름=''
    definition     이름=''
      StaticText     이름='dt 없이 dd 먼저'
    term           이름='뒤늦은 dt'
      StaticText     이름='뒤늦은 dt'
(exit 0)
```

- ★★ **`<ul>` 안의 `<div>`·글자·`<p>` 가 목록 안에 그대로 들어갔다.** `list` 의 자식으로 `generic`·`StaticText`·`paragraph` 가 `listitem` 과 나란히 있다 — **보조 기술이 「목록 항목 몇 개」를 세면 어긋날 수 있다.**
- ★★ **`list-style: none` 목록도 `list` 역할이 남았다.** 사라진 것은 **`ListMarker` 노드뿐**이다. ★ 「표지를 지우면 목록 역할도 지워진다」는 **WebKit 의 동작으로 알려진 것**이고 이 판에서는 **재현되지 않았다** — WebKit 은 **미실행**이다.
- **목록 밖의 `<li>` 도 `listitem` + 표지 `• `** 이다 — Chrome 이 **부모가 목록이 아니어도** 항목으로 만들었다(구현의 관찰).
- ★★ **`<dl>` 은 `DescriptionList` 로 찍혔다.** HTML-AAM 은 `dl` → **`list` 역할**(편집 주: ARIA 이슈 해결에 따라 바뀔 수 있음)이다 — **Chrome 은 내부 이름 `DescriptionList` 를 쓴다.** `dt` → `term`, `dd` → `definition` 은 HTML-AAM 과 같다.
- ★★ **`dl` 안의 `div` 는 트리에서 사라졌다.** `term`·`definition` 이 `DescriptionList` 바로 아래로 **평평하게** 붙는다 — **묶음은 보조 기술에 안 넘어간다.** `div` 는 **마크업과 스타일링을 위한 묶음**이다.
- **순서가 거꾸로인 `<dl>` 도 거꾸로 들어간다**(`definition` 먼저). 트리는 **쓴 순서**다.

```text
  <dl> 의 묶음은 두 트리에서 다르게 보인다

  DOM (창 ①)                            접근성 트리 (창 ⑦)
  dl                                     DescriptionList
    div                                    term        사과
      dt 사과                              definition  빨갛다
      dd 빨갛다                             term        포도
    div                                    term        머루
      dt 포도                              definition  보랏빛이다
      dt 머루                              definition  송이로 달린다
      dd 보랏빛이다
      dd 송이로 달린다                    ★ div 가 사라지고 평평해진다

  「포도·머루 가 한 묶음」이라는 정보는 접근성 트리의 모양에 없다 — 순서로만 남는다.
```

### demo — 번호는 화면에만 있다

```html demo
<!-- html13b-15-demo.html -->
<ol reversed><li>셋째로 좋은 것</li><li>둘째로 좋은 것</li><li>가장 좋은 것</li></ol>
<ol><li>첫째</li><li value="10">열째로 건너뛴다</li><li>그다음</li></ol>
<ol type="I" start="4"><li>넷째 장</li><li>다섯째 장</li></ol>
```

> **보이는 것** — 첫 목록은 **3, 2, 1** 로 거꾸로 센다. 둘째 목록은 **1, 10, 11** — 둘째 항목에서 10 으로 뛰고 셋째가 11 로 따라간다. 셋째 목록은 **IV, V** 로마 숫자다. 마크업에는 **숫자가 한 글자도 없다.**\
> **바꿔 볼 것** — 둘째 목록의 `<ol>` 에 `reversed` 를 붙인다(그러면 `3, 10, 9` — `value` 가 거꾸로 목록에서도 뒤를 끌고 간다)

*(Chrome 151 headless 실측 — 접근성 트리의 `ListMarker` 이름으로 읽었다. 픽셀은 읽지 않았다. 「바꿔 볼 것」의 `3, 10, 9` 는 바꾼 판을 따로 던져 확인했다 — 아래 둘째 블록)*

```text
$ python3 html13b-cdp.py ax html13b-15-demo.html
RootWebArea    이름=''
  list           이름=''
    listitem       이름='' level=1
      ListMarker     이름='3. '
      StaticText     이름='셋째로 좋은 것'
    listitem       이름='' level=1
      ListMarker     이름='2. '
      StaticText     이름='둘째로 좋은 것'
    listitem       이름='' level=1
      ListMarker     이름='1. '
      StaticText     이름='가장 좋은 것'
  list           이름=''
    listitem       이름='' level=1
      ListMarker     이름='1. '
      StaticText     이름='첫째'
    listitem       이름='' level=1
      ListMarker     이름='10. '
      StaticText     이름='열째로 건너뛴다'
    listitem       이름='' level=1
      ListMarker     이름='11. '
      StaticText     이름='그다음'
  list           이름=''
    listitem       이름='' level=1
      ListMarker     이름='IV. '
      StaticText     이름='넷째 장'
    listitem       이름='' level=1
      ListMarker     이름='V. '
      StaticText     이름='다섯째 장'
(exit 0)
```

「바꿔 볼 것」을 바꾼 판(둘째 목록에 `reversed`)이다 — 소스는 [3-answer.md](3-answer.md) 의 `## 실행 검증`.

```text
$ python3 html13b-cdp.py ax html13b-15-democheck.html
RootWebArea    이름=''
  list           이름=''
    listitem       이름='' level=1
      ListMarker     이름='3. '
      StaticText     이름='첫째'
    listitem       이름='' level=1
      ListMarker     이름='10. '
      StaticText     이름='열째로 건너뛴다'
    listitem       이름='' level=1
      ListMarker     이름='9. '
      StaticText     이름='그다음'
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다. 쓰는 꼴은 (1)·(3) 의 소스가 전부 실제로 던진 형태다.

| 목록 | 주장하는 것 | 이 판의 역할 |
|---|---|---|
| `<ul>` | **순서가 중요하지 않다** — 바꿔도 뜻이 안 바뀐다 | `list` / 항목 `listitem` |
| `<ol>` | **순서가 뜻이다** — 바꾸면 뜻이 바뀐다 | `list` / 항목 `listitem` |
| `<dl>` | **이름 — 값 묶음**(용어와 설명, 키와 값) | `DescriptionList`(HTML-AAM 은 `list`) / `term`·`definition` |

| 속성 | 붙는 곳 | 하는 일 | DOM 에서 읽으면 |
|---|---|---|---|
| `start="N"` | `ol` | 첫 번호를 N 으로(음수·0 가능) | `ol.start` = N (없으면 **1**) |
| `reversed` | `ol` | 거꾸로 센다 — 기본 시작은 **항목 수** | ★ `ol.start` 는 **1** 그대로 |
| `value="N"` | `li`(부모가 `ol`) | 이 항목을 N 으로, **뒤는 거기서 이어서** | `li.value` = N (없으면 **0**) |
| `type` = `1`·`a`·`A`·`i`·`I` | `ol`·`li` | 표지 종류 — 명세 렌더링 절의 **표현 힌트** | `ol.type` 글자 그대로 |

### 어디서 헷갈리나

- **`ul` 과 `ol` 의 차이는 「점 대 숫자」가 아니다.** **순서가 뜻인가**다. 점을 숫자로 바꾸는 것은 CSS 다.
- **`reversed` 는 번호만 거꾸로 센다** — 항목의 순서를 뒤집지 않는다.
- **`li.value` 는 번호가 아니다** — `value` 속성이다. 번호를 스크립트로 읽을 방법은 **DOM 에 없다.**
- **`dl` 의 `div` 는 스타일용 묶음**이다 — 접근성 트리에서는 사라진다.

## 어디서 틀리나

### 1. 스크립트로 번호를 읽으려고 `li.value` 를 쓴다

**`0` 이다**((1)). 번호는 DOM 에 없다.\
★ 그리고 **우연히 맞는 칸**이 있다((2) — 번호가 0 이거나 `value` 를 손으로 쓴 칸). 그 칸으로 확인하면 **「된다」로 오해한다.**

### 2. `reversed` 목록의 `ol.start` 로 첫 번호를 구한다

**`1` 이다**((1)) — `ReflectDefault=1`. 첫 번호는 **항목 수**인데 IDL 은 그것을 안 센다.

### 3. `value` 하나를 고치면 그 항목만 바뀔 줄 안다

**뒤가 전부 따라간다**((1) — `1, 7, 8` · `3, 7, 6`).

```text
  value 는 「세던 수」를 갈아 끼운다 (명세 서수 값 알고리즘)

  올려 세는 목록          numbering   표지         거꾸로 목록          numbering   표지
  li            시작  ->     1         1.          li           시작  ->    3          3.
  li value=7    갈아 끼움 ->  7         7.          li value=7   갈아 끼움 ->  7          7.
  li            +1    ->     8         8.          li           -1    ->    6          6.
```

### 4. `<ul>` 에 `<div>` 를 끼우면 파서가 고쳐 줄 줄 안다

**안 고친다**((3)). 그리고 접근성 트리에서 **목록 안에 `listitem` 이 아닌 것이 섞인다**((4)).

### 5. `list-style: none` 이 목록 역할을 지운다고 단정한다

**이 판(Chrome)에서는 안 지웠다**((4)). 알려진 사례는 **WebKit** 이고 **이 머신에서 못 돌렸다.** 한 엔진에서 본 것을 「브라우저가 그렇다」로 적지 않는다.

```text
  list-style: none 이 지운 것과 안 지운 것 (Chrome 151)

  <ul>                         list  ·  listitem  ·  ListMarker "• "
  <ul style="list-style:none"> list  ·  listitem  ·  (없음)            <- 표지만 사라졌다

  WebKit 은 역할까지 지운다고 알려져 있다  ->  이 머신에 없다 — 미실행
```

### 6. `dl` 을 `div` 로 묶으면 묶음이 보조 기술에 전해질 줄 안다

**`div` 는 트리에서 사라진다**((4)). 묶음은 **순서**로만 남는다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 서수 값 알고리즘 — `start`·`reversed`·`value` 로 번호를 센다 | (1) |
| **명세(HTML)** | `ol` 의 시작 값 — `start` 가 정수면 그것, 아니면 `reversed` 면 **항목 수**, 아니면 1 | (1) — `start="삼"` 이 1 |
| **명세(HTML IDL)** | `[Reflect, ReflectDefault=1] start` · `[Reflect] value` · `[Reflect] reversed` | (1)·(2) — ★ **번호를 IDL 로 못 읽는 것이 명세 설계**다 |
| **명세(HTML)** | `ul`·`ol` 의 콘텐츠 모델 「`li` 와 스크립트 지원 요소 0개 이상」 · `dl` 의 「`dt`/`dd` 묶음, 또는 그 묶음을 감싼 `div`」 | (3) — **어겨도 이 판의 파서는 안 고쳤다**(관찰) |
| **명세(HTML)** | `dt`·`dd` 끝 태그 생략 규칙 | (3) — 파서가 닫아 준 유일한 자리 |
| **명세(HTML-AAM)** | `ul`·`ol`·`dl` → `list` · `li` → `listitem` · `dt` → `term` · `dd` → `definition` | (4) |
| **구현(Chrome)** | `dl` 을 **`DescriptionList`** 로 부르는 것 · `ListMarker` 노드 | (1)·(4) |
| **구현(Chrome)** | `list-style: none` 에도 **`list` 를 남기는 것** | (4) — ★ WebKit 은 다르다고 알려져 있다(**미실행**) |
| **구현(Chrome)** | 목록 밖 `li` 에도 `listitem` + 표지 | (4) |
| **구현(Chrome)** | `dl` 안 `div` 를 트리에서 빼는 것 | (4) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **스크린리더가 「목록, 항목 3개」라고 알리는지** | 보조 기술이 없다. 트리의 `list`·`listitem` 까지가 관찰이다 |
| ★★ **WebKit 의 `list-style: none` 동작** | 엔진이 없다 — **미실행** |
| **`ListMarker` 가 화면에 어떻게 그려지나** | 이 문서는 표지를 **트리의 글자**로 읽었다. 픽셀은 안 읽었다 |
| **`aria-setsize`·`aria-posinset` 이 넘어가는 값** | HTML-AAM 은 `li` 에 그것을 붙이라 적는다. 탐색 판 한 번에서 CDP 가 넘긴 `listitem` 의 속성은 **`level` 하나뿐**이었다 — 그 값이 플랫폼 층에서 붙는지는 **못 잰 것**이다(캡처하지 않은 탐색이라 본문 근거로는 안 쓴다) |

## 언제 쓰고 언제 안 쓰나

- **순서가 뜻이면 `ol`, 아니면 `ul`** — 모양은 CSS 로 바꾼다.
- **첫 번호를 바꿔야 하면 `start`**, 거꾸로 세야 하면 `reversed` — 숫자를 글자로 박지 않는다.
- **번호를 건너뛰어야 하면 `value`** — 뒤가 따라간다는 것을 알고 쓴다.
- **스크립트가 번호를 알아야 하면 직접 센다** — DOM 은 안 준다.
- **용어·설명, 키·값이면 `dl`** — 스타일을 위해 `div` 로 묶어도 된다(묶음은 트리에서 사라진다).
- **목록에는 `li` 만 넣는다** — 파서도 보조 기술도 안 고쳐 준다.

## 핵심 문장

1. **목록의 번호는 접근성 트리의 `ListMarker` 에만 있다 — `li.value`·`ol.start`·`::marker` 계산값·`innerText` 에는 없다.**
2. **`li.value` 는 번호가 아니라 `value` 속성이다 — 없으면 0 이고, 번호와 같은 칸은 27 중 4 인데 전부 우연이다.**
3. **`reversed` 목록의 `ol.start` 는 1 이다 — `ReflectDefault=1`.**
4. **`value` 는 뒷번호를 끌고 간다 — 거꾸로 목록에서도.**
5. **파서는 `ul` 안의 `div`·글자·`p` 를 안 고친다 — 생략한 `dt`/`dd` 끝 태그만 닫아 준다.**
6. **`dl` 안의 `div` 묶음은 접근성 트리에서 사라진다.**
7. **Chrome 151 은 `list-style: none` 목록에도 `list` 역할을 남긴다 — WebKit 은 미실행.**

## 관련 자료

- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — **`ul` 이 무엇을 담을 수 있나**의 정본이다. 여기는 **어겼을 때 파서와 트리가 무엇을 하나**까지.
- [03번 주제 — 파서와 오류 복구](../03-parser-and-error-recovery/2-summary.md) — **파서가 트리를 고치는 자리**는 그쪽. 여기는 **목록에는 그 복구가 없다**는 결과.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **13번**([의사 요소와 생성 콘텐츠](../../../css/syntax/13-pseudo-elements-and-generated-content/2-summary.md)) — **`::marker`·`counter()`·`list-item` 카운터**로 번호를 **만드는** 법은 그쪽이 정본이다. 여기는 **HTML 속성이 그 카운터를 어떻게 움직이나**까지.
- 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **06번**([속성 대 성질](../../../../web-api/06-attribute-vs-property/2-summary.md)) — `ReflectDefault` 같은 **반영 규칙의 일반론**.
- [13번 주제](../13-phrasing-semantics/2-summary.md) · [14번 주제](../14-quotation-edits-and-time/2-summary.md) — 같은 시맨틱 묶음. 창 ② × 창 ⑦ 대조의 형식.
- 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나) — WebKit 사례에 흔히 붙는 처방(`role="list"` 를 손으로 다는 것)의 **옳고 그름**은 그쪽이 정본이다.

## 용어 풀이

- **서수 값(ordinal value)** — 명세가 `li` 마다 계산하는 번호. 표지가 찍는 값.
- **시작 값(starting value)** — `ol` 의 첫 서수 값. `start` → (없으면) `reversed` 면 항목 수 → 1.
- **표지(marker)** — 항목 앞의 번호·점. 접근성 트리에서는 **`ListMarker`** 노드다.
- **`ReflectDefault=1`** — 속성이 없을 때 IDL 이 1 을 돌려주게 하는 명세 표기.
- **`DescriptionList`** — Chrome 이 `dl` 에 쓰는 내부 역할 이름. HTML-AAM 은 `list`.
- **`term` / `definition`** — `dt` / `dd` 의 역할.
- **콘텐츠 모델** — 요소가 무엇을 자식으로 가질 수 있나. 어겨도 **파서가 늘 고쳐 주지는 않는다.**

## 더 들어가면

- **왜 번호를 DOM 에 안 두나** — 번호는 **렌더의 결과**다. CSS 로 `list-style: none` 을 주면 없어지고, `counter-reset` 으로 바꿀 수도 있다. DOM 에 박으면 **스타일이 바꾼 번호와 DOM 의 번호가 어긋난다.** 그래서 DOM 은 **입력(`start`·`value`)만** 들고, 번호는 렌더가 센다.
- **WebKit 의 `list-style: none`** — 「표지를 지우면 목록 역할이 사라진다」는 **이 배치의 브리핑이 알려진 사례로 준 것**이다. 이 머신에 WebKit 이 없어 **그 동작도 그 이유도 확인하지 못했다.** 확인한 것은 **Chrome 151 이 역할을 남긴다**는 반대쪽 한 엔진뿐이다 — 어느 쪽도 명세가 정한 것이 아니다.
- **`dl` 에 `div` 가 허용된 까닭** — 스타일링(한 묶음에 배경·테두리) 때문이다. 접근성 트리에서 사라지는 것은 **그 목적과 맞다** — 묶음은 **보이게 하려는 것**이지 **뜻을 더하려는 것**이 아니다.
