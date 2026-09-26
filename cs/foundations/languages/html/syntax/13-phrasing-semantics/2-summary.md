# html/syntax/13 — 구절 시맨틱: `strong`/`em`/`b`/`i`/`mark`/`small`/`code`/`kbd`/`samp`/`abbr` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Text-level semantics」](https://html.spec.whatwg.org/multipage/text-level-semantics.html) 절(요소마다 「represents」 문장)과 [「Rendering — Phrasing content」](https://html.spec.whatwg.org/multipage/rendering.html#phrasing-content-3) 의 UA 스타일시트, 그리고 [HTML-AAM](https://w3c.github.io/html-aam/)(HTML Accessibility API Mappings — 요소가 **어느 역할에 대응하나**를 정한 명세). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 블록마다 던진 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다(캡처 조립기). 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다** — 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — HTML 에는 언어 버전이 없다. 열 요소 전부 **20년 넘게 안정된 표면**이다. ★ 다만 그 요소들이 **접근성 역할에 대응하게 된 것은 최근**이다 — `strong`·`emphasis`·`code`·`generic` 역할은 **WAI-ARIA 1.2 본문에는 있고 1.1 본문에는 없다**(두 판의 역할 앵커를 직접 대조했다). **`mark` 역할은 1.2 에도 없다** — HTML-AAM 편집본이 대응시키는 역할이다.
> **선행** — [05번 주제](../05-content-categories-and-models/2-summary.md)(구절 콘텐츠라는 카테고리)와 [11번 주제](../11-sectioning-and-landmarks/2-summary.md)(창 ⑦ — 접근성 트리를 여는 법).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 두 창의 대조다 — 창 ②(`getComputedStyle`)가 「같다」고 답하는 자리에서 창 ⑦(접근성 트리)이 「다르다」고 답한다.** 「보이는 것은 같고 의미만 다르다」를 **한 창으로는 증명할 수 없다** — 모양은 창 ② 로, 의미는 창 ⑦ 로만 보인다.

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
| **흔들린다** | CDP 가 쓰는 **포트 번호와 프로필 경로** | 실행마다 무작위로 고른다 — **출력에는 안 들어간다** |
| **흔들린다(머신 사이)** | demo 검증의 **상자 크기와 기본 글꼴 이름**(`"Noto Sans CJK KR"`) | 설치된 글꼴에 달렸다. 그래서 격자 블록은 **`body { font-family: sans-serif }` 로 글꼴 칸을 고정**했다 |
| **안 흔들린다** | 계산 스타일 네 칸(`font-weight`·`font-style`·`font-size`·`background-color`) | 같은 판이면 결정적이다 |
| **안 흔들린다** | 접근성 트리의 **역할 이름·접근 가능한 이름·설명** | 〃 |
| **안 흔들린다** | 격자의 「**갈린 칸 N / M**」 | 스크립트가 센다 — 사람이 세지 않는다 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다([03번 주제](../03-parser-and-error-recovery/2-summary.md)) |

실측 — 이 배치(13\~16)의 캡처 **55블록을 세 번 돌려 55블록 전부 한 글자도 같았다**(흔들린 칸 0 · 고칠 것 0).

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **② 프로브**(`getComputedStyle`) | ★ **쓴다 — 본체의 반쪽** | 「모양이 같은가」. 짝마다 **다섯 칸이 전부 같다**((1)) |
| **⑦ 접근성 트리**(CDP) | ★ **쓴다 — 본체의 나머지 반쪽** | 「의미가 같은가」. 짝마다 **역할 한 칸이 갈린다**((1)·(2)) |
| **① `--dump-dom`** | 쓴다 — 한 번 | 「트리에 의미가 남나」 — **태그 이름 말고는 아무것도 없다**((3)) |
| **③ `innerText` 대 `textContent`** | 쓴다 — 한 번 | 「의미가 글자에 남나」 — **둘 다 한 글자도 안 남긴다**((7)) |
| **④ `compatMode`** | **부적용** | 구절 요소는 문서 모드를 안 바꾼다 — **잴 것이 없다** |
| **⑤ 서버 요청 로그** | **부적용** | 요청을 일으키는 요소가 없다 — **잴 것이 없다** |
| **⑥ `renderBlockingStatus`** | **부적용** | 렌더를 막는 자원이 없다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「같은 질문을 다른 창으로 물었다」.** 「`b` 와 `strong` 은 같은가」를 창 ② 에 물으면 「**같다**」가 나온다. 틀린 답이 아니다 — **그 창이 볼 수 있는 것에 대해서는 맞는 답**이다. 같은 질문을 창 ⑦ 로 다시 물어야 「**역할이 다르다**」가 나온다. ★ 그리고 창 ⑦ 도 못 보는 것이 있다 — **스크린리더가 그 역할을 받아 무엇을 하는가**다(아래 「도구가 못 보는 것」).

## 한눈에 — 쉽게 말하면

**★ 굵은 글씨는 하나인데 거기 붙은 명찰이 다르다. 화면은 명찰을 안 보여 주고, 접근성 트리만 명찰을 읽는다.**

회사 게시판의 **빨간 형광펜**에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 형광펜의 **색과 굵기** | **계산 스타일** — 창 ② 가 읽는다 |
| 형광펜 옆에 붙은 **작은 명찰**(「긴급」·「그냥 눈에 띄게」) | **접근성 역할** — 창 ⑦ 만 읽는다 |
| 「**긴급**」 명찰이 붙은 굵은 글씨 | **`<strong>`** → 역할 `strong` |
| 명찰 **없이** 굵게만 칠한 글씨 | **`<b>`** → 역할 `generic`(뜻 없는 묶음) |
| 「**여기 힘주어 읽으시오**」 명찰의 기울인 글씨 | **`<em>`** → 역할 `emphasis` |
| 명찰 없이 기울이기만 한 글씨 | **`<i>`** → `generic` |
| 「**코드**」 명찰이 붙은 고정폭 글씨 | **`<code>`** → 역할 `code` |
| 명찰 없는 고정폭 글씨 둘 | **`<kbd>`**(누를 키)·**`<samp>`**(프로그램이 낸 출력) → 둘 다 `generic` |
| 게시판 **맨 아래의 깨알 글씨** | **`<small>`** — 명세의 뜻은 「부가 설명」인데 **명찰은 `generic`** 이다 |
| 줄임말 옆 **풀어 쓴 쪽지** | **`<abbr title="…">`** — 쪽지가 **이름**이 된다 |

- **모양은 짝끼리 똑같다.** `b`/`strong` · `i`/`em` · `code`/`kbd`/`samp` 다섯 짝의 계산 스타일 25칸이 **한 칸도 안 갈렸다**((1)).
- **명찰은 짝끼리 다르다.** 역할 5칸 중 **4칸이 갈렸다** — 안 갈린 하나는 `kbd`/`samp`(둘 다 명찰 없음)다.
- **명찰은 화면·트리·글자 어디에도 안 남는다.** 접근성 트리에만 있다((3)·(7)).

```text
  같은 굵은 글씨가 두 창에서 어떻게 보이나

                    창 ② 계산 스타일              창 ⑦ 접근성 트리
                    ----------------              ----------------
  <strong>가</strong>   font-weight 700      ->       strong
  <b>가</b>             font-weight 700      ->       generic
                        ~~~~~~~~~~~~~~~               ~~~~~~~
                        같다                           다르다

  「보이는 것은 같다」는 창 ② 의 답이고, 「의미가 다르다」는 창 ⑦ 의 답이다.
  한 창으로는 둘 다 말할 수 없다.
```

실무에서 이게 터지는 자리는 **디자인 시안의 「굵게」를 보고 태그를 고르는 것**이다.\
시안은 모양만 말하므로 `<b>` 든 `<strong>` 이든 **화면 검수는 통과한다.** 차이는 화면 밖에 있다.\
그리고 반대 방향의 사고도 있다 — **CSS 로 `<strong>` 의 굵기를 지우면 의미도 사라진 줄 안다.** 안 사라진다((5)).

> **접근성 역할(role)** — 브라우저가 보조 기술에게 「이 조각은 무엇이다」라고 넘기는 이름표.\
> 예: `<strong>` 의 역할은 `strong`, `<b>` 의 역할은 `generic`(뜻 없음).

> **`generic` 역할** — 「뜻이 없는 묶음」이라는 역할. `<span>`·`<div>` 가 받는 그것이다.\
> 예: 이 주제에서 `<b>`·`<i>`·`<kbd>`·`<samp>`·`<small>` 이 전부 `<span>` 과 **같은 역할**을 받았다.

## 이 주제가 답하려는 질문

1. **「보이는 것은 같다」와 「의미가 다르다」를 각각 무엇으로 재나.** 한 창으로 둘 다 되나.
2. **열 요소 중 어느 것이 역할을 받고 어느 것이 `generic` 인가.** 그 대응은 **누가 정하나**(명세인가 Chrome 인가).
3. **모양과 의미를 떼어 놓을 수 있나** — 스타일을 지우면 의미도 지워지나, 스타일을 입히면 의미가 생기나.

## 동작 방식

### (1) 창 ② × 창 ⑦ — 열 요소 격자, 갈린 칸을 스크립트가 센다

**언제 쓰나** — 이 주제의 본체. **이 한 블록이 「모양 = 의미」라는 착각을 깨뜨린다.**

열 요소와 비교용 `<span>` 을 한 문단에 두고, 요소마다 계산 스타일 다섯 칸을 창 ② 로, 역할을 창 ⑦ 로 읽었다. 그다음 **「똑같아 보이는 짝」 다섯**을 견주어 **갈린 칸을 스크립트가 직접 센다.**\
★ `body { font-family: sans-serif }` 는 **글꼴 칸을 머신에 안 매이게** 하려고 넣었다(없으면 이 머신의 기본 글꼴 이름이 찍힌다 — 흔들리는 칸).

```html
<!-- html13b-13-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>13 보이는 것 대 의미</title>
<style>body { font-family: sans-serif; }</style>
</head>
<body>
<p>
<strong id="strong">가</strong> <b id="b">가</b>
<em id="em">가</em> <i id="i">가</i>
<code id="code">가</code> <kbd id="kbd">가</kbd> <samp id="samp">가</samp>
<mark id="mark">가</mark> <small id="small">가</small>
<abbr id="abbr" title="월드 와이드 웹">WWW</abbr> <span id="span">가</span>
</p>
<script>
const 요소 = ["strong", "b", "em", "i", "code", "kbd", "samp", "mark", "small", "abbr", "span"];
window.__대상 = 요소.map(t => [t, "#" + t]);
const 열 = ["font-weight", "font-style", "font-family", "font-size", "background-color"];
const 칸 = (s, w) => String(s).padEnd(w);
window.__끝 = () => {
  const O = [];
  const 값 = {};
  for (const t of 요소) {
    const c = getComputedStyle(document.getElementById(t));
    값[t] = Object.fromEntries(열.map(k => [k, c.getPropertyValue(k)]));
    값[t]["역할"] = window.__AX[t].역할;
  }
  O.push("열 요소의 계산 스타일(창 ②)과 접근성 역할(창 ⑦)");
  O.push(칸("요소", 10) + 칸("weight", 8) + 칸("style", 8) + 칸("family", 12) + 칸("size", 11)
       + 칸("background", 18) + "역할");
  for (const t of 요소) {
    const v = 값[t];
    O.push(칸("<" + t + ">", 10) + 칸(v["font-weight"], 8) + 칸(v["font-style"], 8)
         + 칸(v["font-family"], 12) + 칸(v["font-size"], 11) + 칸(v["background-color"], 18) + v["역할"]);
  }
  O.push("");
  O.push("「똑같아 보이는 짝」끼리 견주면 — 어느 칸이 갈리나");
  const 짝 = [["strong", "b"], ["em", "i"], ["code", "kbd"], ["code", "samp"], ["kbd", "samp"]];
  const 모든열 = [...열, "역할"];
  let 스타일갈림 = 0, 스타일전체 = 0, 역할갈림 = 0, 역할전체 = 0;
  for (const [a, b] of 짝) {
    const 갈린 = 모든열.filter(k => 값[a][k] !== 값[b][k]);
    for (const k of 모든열) {
      const 다름 = 값[a][k] !== 값[b][k];
      if (k === "역할") { 역할전체++; if (다름) 역할갈림++; }
      else { 스타일전체++; if (다름) 스타일갈림++; }
    }
    O.push("  " + 칸(a + " 대 " + b, 16) + (갈린.length ? "갈린 열 = " + 갈린.join(", ") : "갈린 열 없음"));
  }
  O.push("");
  O.push("스타일 칸 갈림 = " + 스타일갈림 + " / " + 스타일전체 + " · 역할 칸 갈림 = " + 역할갈림 + " / " + 역할전체);
  O.push("갈린 칸 = " + (스타일갈림 + 역할갈림) + " / " + (스타일전체 + 역할전체));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html13b-cdp.py page html13b-13-grid.html
열 요소의 계산 스타일(창 ②)과 접근성 역할(창 ⑦)
요소        weight  style   family      size       background        역할
<strong>  700     normal  sans-serif  16px       rgba(0, 0, 0, 0)  strong
<b>       700     normal  sans-serif  16px       rgba(0, 0, 0, 0)  generic
<em>      400     italic  sans-serif  16px       rgba(0, 0, 0, 0)  emphasis
<i>       400     italic  sans-serif  16px       rgba(0, 0, 0, 0)  generic
<code>    400     normal  monospace   13px       rgba(0, 0, 0, 0)  code
<kbd>     400     normal  monospace   13px       rgba(0, 0, 0, 0)  generic
<samp>    400     normal  monospace   13px       rgba(0, 0, 0, 0)  generic
<mark>    400     normal  sans-serif  16px       rgb(255, 255, 0)  mark
<small>   400     normal  sans-serif  13.3333px  rgba(0, 0, 0, 0)  generic
<abbr>    400     normal  sans-serif  16px       rgba(0, 0, 0, 0)  Abbr
<span>    400     normal  sans-serif  16px       rgba(0, 0, 0, 0)  generic

「똑같아 보이는 짝」끼리 견주면 — 어느 칸이 갈리나
  strong 대 b      갈린 열 = 역할
  em 대 i          갈린 열 = 역할
  code 대 kbd      갈린 열 = 역할
  code 대 samp     갈린 열 = 역할
  kbd 대 samp      갈린 열 없음

스타일 칸 갈림 = 0 / 25 · 역할 칸 갈림 = 4 / 5
갈린 칸 = 4 / 30
(exit 0)
```

```text
  짝 다섯, 열 여섯 칸짜리 비교표를 한 장으로

                weight  style   family     size   background | 역할
  strong / b      =       =       =          =        =      |  X   strong  / generic
  em     / i      =       =       =          =        =      |  X   emphasis/ generic
  code   / kbd    =       =       =          =        =      |  X   code    / generic
  code   / samp   =       =       =          =        =      |  X   code    / generic
  kbd    / samp   =       =       =          =        =      |  =   generic / generic
                ---------------------------------------------+-----
                스타일 칸  0 / 25 갈림                        | 역할 칸 4 / 5 갈림

  ★ 갈린 네 칸이 전부 오른쪽 한 열에 몰렸다.
```

- ★★★ **갈린 칸은 30 중 4이고, 네 칸 전부 역할 열이다.** 스타일 25칸은 **한 칸도 안 갈렸다.** 「보이는 것은 같고 의미만 다르다」가 **숫자 하나로** 선다.
- ★★ **`<strong>` 은 정말로 `strong` 역할이다.** `<em>` 은 `emphasis`, `<code>` 는 `code`, `<mark>` 는 `mark` 다. **`<b>`·`<i>`·`<kbd>`·`<samp>`·`<small>` 은 `<span>` 과 같은 `generic`** 이다.
- ★ **`kbd`/`samp` 짝만 0 칸이다.** 모양도 역할도 같다 — 이 판에서 **둘을 가르는 창이 하나도 없다.** 뜻의 차이(누를 키 / 프로그램 출력)는 명세의 문장에만 있다.
- ★ **`<abbr>` 의 역할이 `Abbr` 로 찍혔다** — ARIA 에 없는 이름이다. (2) 가 그것을 따로 판다.
- **`code`·`kbd`·`samp` 는 `font-size` 가 `13px`** 이다 — 16px 문단 안인데도. (4) 에서 다시 본다.

> **UA 스타일시트(user agent stylesheet)** — 브라우저가 기본으로 까는 스타일. 명세 렌더링 절이 **「기대되는」 값**을 싣는다.\
> 예: 명세의 `b, strong { font-weight: bolder; }` 한 줄이 두 요소를 **같은 굵기**로 만든다.

### (2) 창 ⑦ — 같은 문단의 접근성 트리를 통째로

**언제 쓰나** — (1) 의 역할 열이 **표를 짜는 스크립트의 가공이 아니라 트리 그대로**라는 것을 확인하는 자리.

(1) 과 같은 파일이다. 스크립트 없이 **트리 전체를 트리 순서로** 찍었다.

```text
$ python3 html13b-cdp.py ax html13b-13-grid.html
RootWebArea    이름='13 보이는 것 대 의미'
  paragraph      이름=''
    strong         이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    emphasis       이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    code           이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    mark           이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
    StaticText     이름=' '
    Abbr           이름='월드 와이드 웹'
      StaticText     이름='WWW'
    StaticText     이름=' '
    generic        이름=''
      StaticText     이름='가'
(exit 0)
```

- ★★ **트리 그대로다.** `strong`·`emphasis`·`code`·`mark` 가 노드로 서 있고, 나머지는 `generic` 이다.
- ★ **`Abbr` 는 Chrome 의 내부 역할 이름**이다. HTML-AAM 은 `<abbr>` 에 「**대응하는 ARIA 역할 없음**」이라고 적고 계산 역할을 `html-abbr` 로 둔다. **Chrome 이 그 빈자리를 자기 이름으로 채운 것**이다 — 명세 보장이 아니라 구현이다.
- **`<abbr>` 의 이름이 `'월드 와이드 웹'`** 이다 — `title` 이 이름이 됐다((6)).
- **`StaticText ' '`** 는 요소 사이의 공백이다 — 트리에 글자 노드로 남는다.
- ★ **`generic` 노드가 트리에 남은 것은 요소마다 `id` 를 달았기 때문이다.** 이 판은 **`id` 없는 `generic` 을 무시된 노드로 빼고 글자만 부모에 붙였다**(이 배치에서 본 사례 전부 — 구현의 관찰이다) — [14번 주제](../14-quotation-edits-and-time/2-summary.md)의 (2)·(4) 가 `id` 없는 `<q>` 와 있는 `<q>` 로 그 차이를 캡처했다. **역할이 `generic` 이라는 사실은 어느 쪽이든 같다.**

```text
  역할을 누가 정하나 — 두 층

  명세 (HTML-AAM)                      구현 (Chrome 151 의 트리)
  ------------------                   -------------------------
  strong  -> strong role                strong
  em      -> emphasis role              emphasis
  code    -> code role                  code
  mark    -> mark role                  mark
  b, i, small, samp, span -> generic    generic
  kbd     -> 대응 역할 없음              generic      <- 빈자리를 generic 으로
  abbr    -> 대응 역할 없음              Abbr         <- 빈자리를 자기 이름으로

  ★ 왼쪽이 보장이고 오른쪽이 이 판의 관찰이다.
```

### (3) 창 ① — 트리에는 태그 이름 말고 아무것도 없다

**언제 쓰나** — 「파서가 뭔가 해 주나」를 묻는 자리. **안 해 준다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html13b-13-grid.html 2>/dev/null | sed -n '/^<p>$/,/^<\/p>$/p'
<p>
<strong id="strong">가</strong> <b id="b">가</b>
<em id="em">가</em> <i id="i">가</i>
<code id="code">가</code> <kbd id="kbd">가</kbd> <samp id="samp">가</samp>
<mark id="mark">가</mark> <small id="small">가</small>
<abbr id="abbr" title="월드 와이드 웹">WWW</abbr> <span id="span">가</span>
</p>
(exit 0)
```

- **쓴 그대로다.** 파서는 구절 요소를 **고치지도 옮기지도 않는다.** 속성도 그대로다.
- ★ **그래서 창 ① 은 「의미」를 못 본다.** 보이는 것은 **내가 쓴 태그 이름**뿐이다 — 그것은 **입력**이지 브라우저가 무엇을 했는지가 아니다. [12번 주제](../12-heading-levels-and-outline/2-summary.md)의 「태그를 세는 것은 증명이 아니다」와 같은 이야기다.

### (4) 창 ② + 창 ⑦ — 겹쳐 쓰면 굵기·크기는 쌓이고 역할은 안 쌓인다

**언제 쓰나** — `<b>` 안에 `<b>`, `<kbd>` 안에 `<kbd>` 를 쓸 때.

```html
<!-- html13b-13-more.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>13 겹치기·지우기·이름</title>
<style>
body { font-family: sans-serif; }
#민strong { font-weight: 400; }
#굵span { font-weight: 700; }
</style>
</head>
<body>
<p id="겹">
<b id="b1">바깥 b<b id="b2">안 b<b id="b3">그 안 b</b></b></b>
<strong id="s1">바깥 strong<strong id="s2">안 strong</strong></strong>
<em id="e1">바깥 em<em id="e2">안 em</em></em>
<kbd id="k1"><kbd id="k2">Ctrl</kbd>+<kbd id="k3">C</kbd></kbd>
<small id="m1">바깥 small<small id="m2">안 small</small></small>
</p>
<p>
<strong id="민strong">굵기를 지운 strong</strong>
<span id="굵span">굵기를 입힌 span</span>
</p>
<p>
<abbr id="abbr" title="월드 와이드 웹">WWW</abbr>
<span id="span" title="월드 와이드 웹">WWW</span>
<abbr id="맨abbr">WWW</abbr>
</p>
<p id="글"><strong>꼭</strong> <em>지금</em> <mark>여기</mark> <kbd>Enter</kbd></p>
<script>
window.__대상 = [["b1", "#b1"], ["b2", "#b2"], ["b3", "#b3"], ["s1", "#s1"], ["s2", "#s2"], ["e1", "#e1"], ["e2", "#e2"],
  ["k1", "#k1"], ["k2", "#k2"], ["m1", "#m1"], ["m2", "#m2"],
  ["민strong", "#민strong"], ["굵span", "#굵span"],
  ["abbr", "#abbr"], ["span", "#span"], ["맨abbr", "#맨abbr"]];
const $ = id => document.getElementById(id);
const cs = id => getComputedStyle($(id));
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = [];
  O.push("(가) 겹쳐 쓰면 — bolder·smaller 는 「더」라서 쌓인다");
  for (const id of ["b1", "b2", "b3", "s1", "s2"])
    O.push("  " + ("#" + id).padEnd(6) + "font-weight = " + cs(id).fontWeight.padEnd(5) + "역할 = " + __AX[id].역할);
  for (const id of ["e1", "e2"])
    O.push("  " + ("#" + id).padEnd(6) + "font-style = " + cs(id).fontStyle.padEnd(8) + "역할 = " + __AX[id].역할
      + "   level 같은 속성 = " + J(__AX[id].속성));
  for (const id of ["k1", "k2", "m1", "m2"])
    O.push("  " + ("#" + id).padEnd(6) + "font-size = " + cs(id).fontSize.padEnd(10) + "역할 = " + __AX[id].역할);
  O.push("");
  O.push("(나) 모양과 의미를 엇갈리게 — 스타일을 지운 strong · 스타일을 입힌 span");
  for (const id of ["민strong", "굵span"])
    O.push("  " + ("#" + id).padEnd(10) + "font-weight = " + cs(id).fontWeight.padEnd(5) + "역할 = " + __AX[id].역할);
  O.push("");
  O.push("(다) title 은 무엇이 되나 — 이름인가 설명인가");
  for (const id of ["abbr", "span", "맨abbr"])
    O.push("  " + ("#" + id).padEnd(8) + "역할 = " + __AX[id].역할.padEnd(9) + "이름 = " + J(__AX[id].이름).padEnd(12)
      + "설명 = " + J(__AX[id].설명) + "   text-decoration = " + cs(id).textDecorationLine + " " + cs(id).textDecorationStyle);
  O.push("");
  O.push("(라) 창 ③ — 의미는 글자에 남나");
  O.push("  innerText   = " + J($("글").innerText));
  O.push("  textContent = " + J($("글").textContent));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html13b-cdp.py page html13b-13-more.html | sed -n '1,12p'
(가) 겹쳐 쓰면 — bolder·smaller 는 「더」라서 쌓인다
  #b1   font-weight = 700  역할 = generic
  #b2   font-weight = 900  역할 = generic
  #b3   font-weight = 900  역할 = generic
  #s1   font-weight = 700  역할 = strong
  #s2   font-weight = 900  역할 = strong
  #e1   font-style = italic  역할 = emphasis   level 같은 속성 = {}
  #e2   font-style = italic  역할 = emphasis   level 같은 속성 = {}
  #k1   font-size = 13px      역할 = generic
  #k2   font-size = 13px      역할 = generic
  #m1   font-size = 13.3333px 역할 = generic
  #m2   font-size = 11.1111px 역할 = generic
(exit 0)
```

```text
  bolder 는 「700」이 아니라 「한 단계 더」다

  <b>              700   <- 부모 400 에서 한 단계
    <b>            900   <- 700 에서 한 단계
      <b>          900   <- 900 이 끝이라 더 못 간다

  <small>          13.3333px   <- 16 의 한 단계 아래
    <small>        11.1111px   <- 13.33 의 한 단계 아래 (또 줄었다)

  <kbd>            13px
    <kbd>          13px        <- 안 줄었다. 고정폭 글꼴의 기본 크기라서

  <em>             italic   emphasis
    <em>           italic   emphasis   <- 명세는 「강세가 한 단계 더」라는데 어느 칸도 안 바뀐다
```

- ★★ **`<b>` 의 굵기는 「700」이 아니라 「`bolder`」다.** 명세 UA 스타일시트가 `font-weight: bolder` 를 준다. 그래서 **겹치면 900 이 되고, 900 에서 멈춘다.** `<strong>` 도 똑같다(700 → 900).
- ★ **`<small>` 은 겹칠수록 계속 준다**(16 → 13.33 → 11.11). `smaller` 도 「한 단계 아래」이기 때문이다.
- ★ **`<kbd>` 안의 `<kbd>` 는 안 준다**(13 → 13). 고정폭 글꼴은 **기본 크기가 13px** 이라 16px 문단 안에서도 13px 로 시작하고, 그 안에서는 **같은 13px** 이다. ★ 이 「13px」은 **Chrome 의 고정폭 기본 크기 설정**에서 나온 값이다 — 명세는 `font-family: monospace` 만 준다.
- **역할은 겹쳐도 그대로다.** 바깥 `<strong>` 도 안쪽 `<strong>` 도 `strong`, 바깥 `<em>` 도 안쪽 `<em>` 도 `emphasis` 다. `level` 같은 속성도 **안 붙는다**(`{}`).
- ★★ **그런데 명세는 겹침에 뜻을 준다.** 「중요도는 조상 `strong` 의 **수**로 정해진다 — `strong` 하나마다 중요도가 올라간다」, `em` 도 「강세의 정도는 조상 `em` 의 **수**」다. **그 수는 역할의 속성으로는 안 넘어간다** — 트리의 **모양**(겹친 노드)으로만 남는다. 기울기는 겹쳐도 `italic` 그대로라 **화면에서도 안 보인다.**
- ★ 명세의 `<kbd>` 중첩은 「**바깥은 입력 한 덩어리, 안쪽은 실제 키 하나**」를 뜻한다(`<kbd><kbd>Ctrl</kbd>+<kbd>C</kbd></kbd>`). 그 뜻도 **어느 창에도 안 나타난다** — 역할은 `generic` 셋이다.

### (5) 창 ② × 창 ⑦ — 모양과 의미를 엇갈리게 놓으면

**언제 쓰나** — 「CSS 로 굵게 했으니 강조다」·「굵기를 지웠으니 강조가 아니다」 둘 다를 반증하는 자리.

(4) 와 같은 파일의 둘째 문단이다 — `<strong>` 의 굵기를 CSS 로 **지우고**, `<span>` 에 굵기를 **입혔다.**

```text
$ python3 html13b-cdp.py page html13b-13-more.html | sed -n '14,16p'
(나) 모양과 의미를 엇갈리게 — 스타일을 지운 strong · 스타일을 입힌 span
  #민strong  font-weight = 400  역할 = strong
  #굵span    font-weight = 700  역할 = generic
(exit 0)
```

```text
  모양과 의미는 서로를 안 끌고 간다

                         모양 (창 ②)        의미 (창 ⑦)
  <strong> 굵기 지움      400  (안 굵다)      strong    <- 의미가 남는다
  <span>   굵기 입힘      700  (굵다)         generic   <- 의미가 안 생긴다

  ★ 역할은 태그가 정한다. CSS 는 역할에 손이 안 닿는다.
```

- ★★★ **굵기를 지운 `<strong>` 은 여전히 `strong` 이다.** 모양이 사라져도 의미가 남는다.
- ★★★ **굵기를 입힌 `<span>` 은 여전히 `generic` 이다.** 모양이 생겨도 의미가 안 생긴다.
- ★ 그래서 「디자인이 굵게를 원하지 않는데 강조는 필요하다」면 **`<strong>` + CSS** 가 답이고, 「굵게만 필요하다」면 **CSS 만** 이 답이다. `<b>` 는 그 중간 — 「**주목시키되 중요하다는 뜻은 없다**」는 명세의 좁은 자리를 위한 것이다.

### (6) 창 ⑦ — `title` 은 `<abbr>` 에서는 이름, `<span>` 에서는 설명

**언제 쓰나** — 줄임말에 풀이를 달 때.

```text
$ python3 html13b-cdp.py page html13b-13-more.html | sed -n '18,21p'
(다) title 은 무엇이 되나 — 이름인가 설명인가
  #abbr   역할 = Abbr     이름 = "월드 와이드 웹"  설명 = ""   text-decoration = underline dotted
  #span   역할 = generic  이름 = ""          설명 = "월드 와이드 웹"   text-decoration = none solid
  #맨abbr  역할 = Abbr     이름 = ""          설명 = ""   text-decoration = none solid
(exit 0)
```

- ★★ **같은 `title` 이 `<abbr>` 에서는 「이름」, `<span>` 에서는 「설명」이 됐다.** HTML-AAM 의 `title` 속성 줄은 「이름 **또는** 설명 **또는** 대응 없음 — 이름 계산 절이 정한다」이고, `<abbr>`·`<dfn>` 의 `title` 줄은 「**플랫폼 API 에서 이름에 연결한다**」다. 이 판이 그대로 따랐다.
- ★ **`<span>` 이 이름을 못 받는 이유** — `generic` 역할은 **이름을 가질 수 없는 역할**이라 이름 대신 설명으로 갔다. 이름 계산 규칙 전체는 목록의 **43번 주제**가 정본이다.
- ★ **`title` 이 없는 `<abbr>` 는 점선 밑줄도 없다**(`text-decoration = none`). UA 스타일시트의 규칙이 `abbr[title]` 이라 **속성이 있어야 걸린다.**

```text
  같은 title 이 요소에 따라 다른 칸으로 간다

  <abbr title="월드 와이드 웹">WWW</abbr>
        역할 Abbr   ->  이름 = '월드 와이드 웹'   설명 = ''          밑줄 dotted
  <span title="월드 와이드 웹">WWW</span>
        역할 generic ->  이름 = ''               설명 = '월드 와이드 웹'  밑줄 없음
  <abbr>WWW</abbr>
        역할 Abbr   ->  이름 = ''               설명 = ''          밑줄 없음

  generic 은 이름을 못 가진다 -> 이름 칸이 막혀 설명 칸으로 밀려났다.
```
- ★★ **「보조 기술이 `WWW` 를 「월드 와이드 웹」으로 읽는다」는 이 판에서 못 본다.** 트리에 이름이 있다는 것까지가 관찰이다.

### (7) 창 ③ — 의미는 글자에 한 글자도 안 남는다

**언제 쓰나** — 「복사해 붙이면 강조가 따라가나」·「검색 색인이 강조를 보나」 같은 물음의 **바닥**.

```text
$ python3 html13b-cdp.py page html13b-13-more.html | sed -n '23,25p'
(라) 창 ③ — 의미는 글자에 남나
  innerText   = "꼭 지금 여기 Enter"
  textContent = "꼭 지금 여기 Enter"
(exit 0)
```

```text
  의미가 사는 곳과 안 사는 곳

  <p><strong>꼭</strong> <em>지금</em> <mark>여기</mark> <kbd>Enter</kbd></p>

  창 ①  트리          태그 이름이 있다   (내가 쓴 것 그대로)
  창 ③  innerText     "꼭 지금 여기 Enter"   의미 없음
  창 ③  textContent   "꼭 지금 여기 Enter"   의미 없음
  창 ②  계산 스타일    굵기·기울기·노랑      모양만
  창 ⑦  접근성 트리    strong·emphasis·mark  ★ 의미는 여기에만

  복사·검색 색인·글자 수 세기는 창 ③ 의 세계다 — 거기서는 의미가 이미 사라져 있다.
```

- **`innerText` 도 `textContent` 도 태그를 벗긴 글자뿐이다.** `<strong>`·`<em>`·`<mark>`·`<kbd>` 가 남긴 흔적이 **없다.**
- ★ 창 ③ 은 [04번 주제](../04-whitespace-and-character-references/2-summary.md)에서 **렌더와 트리가 갈리는 자리**를 잡는 창이었다. 여기서는 **안 갈린다** — 구절 요소는 공백도 줄바꿈도 안 바꾸기 때문이다. 「재 봤더니 같았다」이지 「잴 것이 없다」가 아니다.
- ★ **「그래서 검색 엔진이 `<strong>` 을 무시한다/중시한다」는 여기서 한 글자도 나오지 않는다** — 이 머신에서 잴 수 없는 물음이다(아래 「도구가 못 보는 것」).

### demo — 짝끼리 픽셀로 구별되지 않는다

```html demo
<!-- html13b-13-demo.html -->
<p><b>굵은 글씨</b> · <strong>굵은 글씨</strong></p>
<p><i>기울인 글씨</i> · <em>기울인 글씨</em></p>
<p><kbd>Ctrl+C</kbd> · <samp>Ctrl+C</samp> · <code>Ctrl+C</code></p>
```

> **보이는 것** — 세 줄 모두 **가운뎃점 양쪽이 똑같이 생겼다.** 첫 줄의 두 「굵은 글씨」, 둘째 줄의 두 「기울인 글씨」, 셋째 줄의 세 `Ctrl+C` 가 **굵기·기울기·글꼴·크기·상자 크기까지** 같다. 어느 쪽이 `<strong>` 이고 어느 쪽이 `<b>` 인지 **화면으로는 알 방법이 없다.**\
> **바꿔 볼 것** — `<strong>` 에 `style="font-weight: normal"` 을 주면 첫 줄 오른쪽만 얇아진다 — 그래도 역할은 `strong` 으로 남는다((5) 의 실측)

*(Chrome 151 headless 실측, 창 폭 1000: `b`·`strong` 상자 63.38 × 24.00 · `i`·`em` 78.09 × 24.00 · `kbd`·`samp`·`code` 39.00 × 19.00 — 짝끼리 소수 둘째 자리까지 같다. 검증 파일은 [3-answer.md](3-answer.md) 의 `## 실행 검증`, 출력은 아래)*

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html13b-13-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
창 폭 = 1000
<b>      상자 = 63.38 x 24.00   font = 700 normal 16px "Noto Sans CJK KR"
<strong> 상자 = 63.38 x 24.00   font = 700 normal 16px "Noto Sans CJK KR"
<i>      상자 = 78.09 x 24.00   font = 400 italic 16px "Noto Sans CJK KR"
<em>     상자 = 78.09 x 24.00   font = 400 italic 16px "Noto Sans CJK KR"
<kbd>    상자 = 39.00 x 19.00   font = 400 normal 13px monospace
<samp>   상자 = 39.00 x 19.00   font = 400 normal 13px monospace
<code>   상자 = 39.00 x 19.00   font = 400 normal 13px monospace
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다. 쓰는 꼴은 (1)·(4) 의 소스가 전부 실제로 던진 형태이므로 여기서는 **고르는 기준**만 표로 둔다.

| 쓰려는 뜻 | 요소 | 이 판의 역할 | 명세 한 줄 |
|---|---|---|---|
| **중요·심각·급함** | `<strong>` | `strong` | 「strong importance, seriousness, or urgency」 |
| **말할 때 힘주는 자리**(뜻이 바뀌는 강세) | `<em>` | `emphasis` | 「stress emphasis」 |
| 중요하진 않은데 **눈에 띄게**(제품명·핵심어) | `<b>` | `generic` | 「attention … without conveying any extra importance」 |
| **다른 목소리·분위기**(학명·외래어·생각) | `<i>` | `generic` | 「alternate voice or mood」 |
| **지금 이 맥락에서 관련 있어 표시**(검색어 강조) | `<mark>` | `mark` | 「marked or highlighted for reference purposes」 |
| **부가 설명·깨알 글씨**(면책·저작권) | `<small>` | `generic` | 「side comments such as small print」 |
| **컴퓨터 코드** | `<code>` | `code` | 「a fragment of computer code」 |
| **사용자가 넣는 입력**(누를 키) | `<kbd>` | `generic` | 「user input」 |
| **프로그램이 낸 출력** | `<samp>` | `generic` | 「sample or quoted output」 |
| **줄임말** | `<abbr title="…">` | `Abbr`(Chrome 내부) | 「abbreviation or acronym」 |

### 어디서 헷갈리나

- **`<b>` 는 「굵은 `<strong>`」이 아니다.** 뜻이 **없다고 명세가 적어 둔** 요소다 — 그래서 역할이 `generic` 이다.
- **`<small>` 은 「작은 글씨」가 아니다.** 뜻은 「부가 설명」이고, 크기는 그 결과일 뿐이다. ★ **그 뜻은 역할로 드러나지 않는다**(`generic`).
- **`<mark>` 는 「노란 배경」이 아니다.** 「이 맥락에서 관련 있음」이다 — 검색 결과에서 **검색어를 표시**하는 것이 전형이다.
- **`<em>` 과 `<strong>` 은 강도의 차이가 아니다.** `<em>` 은 **문장의 뜻을 바꾸는 강세**, `<strong>` 은 **내용의 중요도**다.
- **`<kbd>`·`<samp>` 는 이 판에서 가를 창이 없다**((1) 의 0칸). 뜻의 차이는 **쓰는 사람의 규율**이다.

## 어디서 틀리나

### 1. 시안의 「굵게」를 보고 `<b>` 와 `<strong>` 을 섞어 쓴다

**화면 검수는 통과한다** — (1) 에서 스타일 25칸이 한 칸도 안 갈렸다.\
★ 차이는 **역할 한 칸**에만 있다. 「중요하다」가 뜻이면 `<strong>`, 아니면 CSS 다.

```text
  태그를 고르는 순서 — 모양이 아니라 뜻에서 시작한다

  이 글자가 「중요하다」는 뜻인가? ── 예 ──> <strong>   (굵기가 싫으면 CSS 로 지운다)
          │
          아니오
          │
  읽을 때 힘을 줘야 뜻이 바뀌나? ─── 예 ──> <em>
          │
          아니오
          │
  그냥 눈에 띄게만 하고 싶다 ─────────────> CSS  (명세가 드는 좁은 자리면 <b>)
```

### 2. CSS 로 `<strong>` 의 굵기를 지우면 강조도 사라진 줄 안다

**안 사라진다.** (5) 에서 `font-weight: 400` 인 `<strong>` 이 **`strong` 역할 그대로**였다.\
★ 반대로 `<span style="font-weight: 700">` 은 **아무 의미도 안 얻는다.**

### 3. `<small>` 로 글자를 줄인다

크기는 CSS 의 일이다. ★ 그리고 `<small>` 을 겹치면 **계속 준다**((4) — 16 → 13.33 → 11.11).\
「부가 설명」이 아닌데 `<small>` 을 쓰면 **명세의 뜻을 어긴다** — 다만 **어느 창도 그것을 잡지 않는다**(역할이 `generic` 이라).

### 4. `<b>` 를 겹쳐 쓰고 「700 이겠지」 한다

**900 이다**((4)). `bolder` 는 「한 단계 더」라 부모에 따라 값이 달라진다.

### 5. `<abbr>` 에 `title` 을 빼고 쓴다

**점선 밑줄도 이름도 없다**((6)). 풀이를 줄 곳이 없어진다.\
★ 그리고 `title` 을 `<span>` 에 옮겨 달면 **이름이 아니라 설명**이 된다 — 같은 속성이 요소에 따라 다른 칸에 들어간다.

### 6. 「검색 엔진이 `<strong>` 을 좋아한다」를 근거로 태그를 고른다

**이 머신에서 잴 수 없는 주장이다.** 이 문서는 한 줄도 그것을 말하지 않는다.\
★ 잴 수 있는 것은 **브라우저가 보조 기술에 무엇을 넘기나**까지다 — 그 선택 기준이면 충분하다.

## 구현 세부사항 대 언어 보장

★ 세 층으로 갈라 적는다 — **명세(WHATWG HTML · HTML-AAM)가 보장하는 것 / Chrome 151 이 구현한 것 / 이 판에서 관찰한 것.**

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 요소마다의 **뜻**(「represents」 문장) | 문법 절의 표 |
| **명세(HTML 렌더링 절)** | `b, strong { font-weight: bolder }` · `cite, dfn, em, i, var { font-style: italic }` · `code, kbd, samp { font-family: monospace }` · `small { font-size: smaller }` · `mark { background: yellow; color: black }` · `abbr[title] { text-decoration: dotted underline }` | (1)·(4)·(6) — ★ 렌더링 절은 「기대되는(expected)」 값이라 **구현이 따르는 권고**다 |
| **명세(HTML-AAM)** | `strong`→`strong` · `em`→`emphasis` · `code`→`code` · `mark`→`mark` · `b`/`i`/`small`/`samp`/`span`→`generic` · `kbd`/`abbr`→**대응 역할 없음** | (1)·(2) |
| **명세(HTML-AAM)** | `<abbr>`·`<dfn>` 의 `title` 은 **이름**에 연결된다 | (6) |
| **명세(HTML)** | 겹친 `<strong>`·`<em>` 의 **수**가 중요도·강세의 정도다 | (4) — ★ 그 수를 넘기는 **역할 속성은 없다**(이 판의 관찰) |
| **구현(Chrome)** | 「대응 역할 없음」을 **`kbd` 는 `generic` 으로, `abbr` 는 `Abbr` 로** 채운 것 | (2) — 판마다 다를 수 있다 |
| **구현(Chrome)** | 고정폭 글꼴의 **기본 크기 13px** | (1)·(4) — 브라우저 설정값이다 |
| **구현(Chrome)** | `generic` 에 준 `title` 을 **설명**으로 넘기는 것 | (6) — 이름 계산 규칙의 적용 결과 |
| **이 판의 관찰** | 짝끼리 **상자 크기까지 같다**는 것 | demo — 글꼴이 바뀌면 절댓값은 바뀐다 |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **스크린리더가 `strong` 을 힘주어 읽는지** | 이 판에 **NVDA·VoiceOver·Orca 가 없다.** 접근성 트리는 보조 기술의 **입력**이지 출력이 아니다. ★ 게다가 역할을 받고도 **아무 일도 안 하는** 보조 기술이 있을 수 있다 — 그것도 못 본다 |
| **`<abbr>` 의 이름이 실제로 소리 나는지** | 같은 이유 |
| ★★ **검색 엔진이 `<strong>`·`<b>` 를 다르게 다루는지** | 이 머신에 검색 엔진이 없다 — **「못 잰 것」(제3의 상태)** 이다. 「SEO 에 좋다」는 이 문서에 없다 |
| **플랫폼 접근성 API 의 값**(MSAA·UIA·ATK·AX) | CDP 는 Chrome 의 **내부 트리**를 보여 준다. HTML-AAM 이 적는 플랫폼별 대응(예: `kbd` 의 「텍스트 속성 `font-family:monospace`」)은 **그 아래 층**이라 못 본다 |
| **다른 엔진의 역할 대응** | 엔진이 하나뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **중요하다는 뜻이 있으면 `<strong>`** — 굵기가 싫으면 CSS 로 지운다. 의미는 남는다.
- **뜻 없이 눈에 띄게만이면 CSS** — 제품명·핵심어처럼 명세가 드는 자리라면 `<b>` 도 된다.
- **읽을 때 힘을 주면 뜻이 바뀌는 자리에 `<em>`** — 「나는 **그** 책을 샀다」의 강세.
- **학명·외래어·생각 속 말에 `<i>`** — 기울임이 목적이 아니라 **다른 목소리**가 뜻이다.
- **코드는 `<code>`, 누를 키는 `<kbd>`, 프로그램 출력은 `<samp>`** — 셋 중 역할이 붙는 것은 `<code>` 뿐이다.
- **`<small>` 은 면책·저작권 같은 부가 설명에만** — 글씨를 줄이려고 쓰지 않는다.
- **`<abbr>` 에는 `title` 을 단다** — 없으면 점선도 이름도 없다.

## 핵심 문장

1. **`b`/`strong` 은 계산 스타일 다섯 칸이 전부 같고 역할 한 칸만 다르다 — 모양은 창 ② 로, 의미는 창 ⑦ 로만 보인다.**
2. **다섯 짝을 견주면 갈린 칸은 30 중 4이고, 넷 다 역할 열이다.**
3. **`<b>`·`<i>`·`<kbd>`·`<samp>`·`<small>` 은 `<span>` 과 같은 `generic` 이다.**
4. **굵기를 지운 `<strong>` 은 여전히 `strong` 이고, 굵기를 입힌 `<span>` 은 여전히 `generic` 이다.**
5. **`b` 의 굵기는 `bolder` 라서 겹치면 900 이 된다.**
6. **같은 `title` 이 `<abbr>` 에서는 이름, `<span>` 에서는 설명이 된다.**
7. **역할 대응은 HTML-AAM 이 정하고, Chrome 의 트리는 그 구현이다 — `Abbr` 는 구현이 채운 이름이다.**
8. **스크린리더가 그 역할로 무엇을 하는지는 이 판에서 못 본다.**

## 관련 자료

- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — **구절 콘텐츠라는 카테고리**가 정본이다. 여기는 **그 안의 요소들이 무엇을 뜻하고 무엇으로 대응되나**부터.
- [11번 주제 — 구획 요소와 랜드마크](../11-sectioning-and-landmarks/2-summary.md) — **창 ⑦ 을 연 편**이다. 하네스의 뿌리가 그쪽이다.
- [12번 주제 — 제목 레벨과 문서 개요](../12-heading-levels-and-outline/2-summary.md) — 「글꼴 크기는 레벨의 증거가 아니다」가 여기의 「굵기는 의미의 증거가 아니다」와 같은 꼴이다.
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **01번**([캐스케이드와 우선순위](../../../css/syntax/01-cascade-and-priority/2-summary.md)) — **UA 스타일시트가 캐스케이드의 어디에 있나**는 그쪽이 정본이다. 여기는 **UA 스타일시트가 두 요소에 같은 값을 준다**는 결과까지.
- CSS 갈래 [목록의 **04번**](../04-whitespace-and-character-references/)([값 처리 단계](../../../css/syntax/04-value-processing-stages/2-summary.md)) — `bolder`·`smaller` 같은 **상대값이 계산값이 되는 과정**은 그쪽.
- 웹 API 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **08번**([`getComputedStyle`](../../../../web-api/08-getcomputedstyle/2-summary.md)) — **창 ② 의 도구 자체**는 그쪽이 정본이다.
- [14번 주제](../14-quotation-edits-and-time/2-summary.md)(인용·편집·시각) — 같은 구절 시맨틱 묶음의 다음 편. `cite`·`q`·`ins`/`del`·`time`.
- 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나) · 목록의 **43번 주제**(접근 가능한 이름 계산) — `role` 로 역할을 덮어쓰는 일과 `title` 이 이름/설명 중 어디로 가나의 **전체 규칙**은 그쪽이 정본이다.

## 용어 풀이

- **구절 콘텐츠(phrasing content)** — 문단 안 글자 흐름에 들어가는 요소들. 이 주제의 열 요소가 전부 여기 든다.
- **접근성 역할(role)** — 보조 기술에게 넘기는 「이 조각은 무엇이다」라는 이름표.
- **`generic`** — 뜻 없는 묶음의 역할. `<span>`·`<div>` 와 같다. **이름을 가질 수 없다.**
- **HTML-AAM** — HTML 요소·속성이 **어느 ARIA 역할과 어느 플랫폼 API 에 대응하나**를 정한 W3C 명세.
- **UA 스타일시트** — 브라우저가 기본으로 까는 스타일시트. 명세 렌더링 절이 그 「기대값」을 싣는다.
- **`bolder` / `smaller`** — 부모 값에서 **한 단계** 굵게/작게. 그래서 겹치면 쌓인다.
- **접근 가능한 이름(accessible name)** — 보조 기술이 그 조각을 부를 때 쓰는 이름. `<abbr title>` 이 그것이 된다.
- **접근 가능한 설명(accessible description)** — 이름 뒤에 덧붙는 설명. `<span title>` 이 그것이 된다.
- **CDP(Chrome DevTools Protocol)** — 브라우저에 원격으로 붙어 내부 상태를 묻는 프로토콜. 창 ⑦ 의 열쇠다.

## 더 들어가면

- **왜 `<b>`·`<i>` 가 폐기되지 않았나** — 한때 「표현 태그」로 몰려 퇴출될 뻔했지만, 명세는 둘에게 **좁은 뜻**(주목·다른 목소리)을 새로 주어 살렸다. 그 좁은 뜻이 **역할로는 `generic`** 이라는 것이 이 주제의 실측이다. 연혁은 `history/web/03` 의 몫이다.
- **왜 `kbd` 는 역할이 없나** — 「누를 키」라는 뜻을 담을 ARIA 역할이 없다. HTML-AAM 은 대신 **플랫폼 API 의 텍스트 속성**(`font-family: monospace`)으로 넘기라고 적는다 — 즉 **「모양」으로 넘긴다.** 이 판의 CDP 트리에는 그 층이 안 보인다.
- **`strong` 역할이 생기기 전** — 역할 대응이 없던 시절에는 `<strong>` 도 트리에서 `<b>` 와 **구분되지 않았을 수 있다.** 이 판에서는 확인할 수 없는 연혁이다(옛 Chrome 판이 없다).
