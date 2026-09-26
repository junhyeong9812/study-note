# html/syntax/20 — `lang`·`dir` 과 양방향 텍스트: `dir=auto`·`bdi`/`bdo` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [`lang` 속성](https://html.spec.whatwg.org/multipage/dom.html#the-lang-and-xml:lang-attributes)(「빈 문자열은 **주 언어를 모른다**는 뜻」)·[`dir` 속성](https://html.spec.whatwg.org/multipage/dom.html#the-dir-attribute)(auto 방향성 — 「첫 L·AL·R 글자」 · `bdi`·`script`·`style`·`textarea`·`dir` 을 가진 요소는 건너뛴다 · 입력 요소는 값을 본다)와 [렌더링 절 15.3.5 「Bidirectional text」](https://html.spec.whatwg.org/multipage/rendering.html#bidirectional-text)(`[dir]`·`bdi` 의 `unicode-bidi: isolate` · `bdo` 의 `isolate-override`), [Unicode Standard Annex #9 「Unicode Bidirectional Algorithm」](https://www.unicode.org/reports/tr9/)(Revision 52, Unicode 18.0.0 — P2·W6·W7·N1·I1·L2), [HTML-AAM](https://w3c.github.io/html-aam/)(편집본 — `bdi`·`bdo` → `generic` · `lang`·`dir` 은 **텍스트 속성**으로). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 블록마다 던진 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다(캡처 조립기). 하네스는 [17번 주제의 3-answer.md](../17-table-structure/3-answer.md) `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다** — 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — `api.webstatus.dev` 조회로 **`<bdi>` 는 Baseline widely**(newly 2020-01-15 → widely 2022-07-15), **`<bdo>`·`:lang()` 은 widely**(2018-01-29), **`:dir()` 은 widely**(newly 2023-12-07 → widely 2026-06-07), **Hyphenation(`hyphens`) 은 widely**(newly 2023-09-18 → widely 2026-03-18), **`direction`·`unicode-bidi`(Layout direction override) 는 widely**(2022-07-15).
> **선행** — [13번 주제](../13-phrasing-semantics/2-summary.md)(구절 시맨틱 — `bdi`·`bdo` 도 구절 요소다) · [14번 주제](../14-quotation-edits-and-time/2-summary.md)(`q` 의 따옴표 모양을 `lang` 이 고른 실측).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **본체는 창 ② 의 새 칸 — 「글자마다의 x 좌표」다.** 양방향 텍스트의 사고는 **글자 순서**에서 난다. 그런데 **DOM·`textContent`·`innerText` 는 전부 논리 순서(쓴 순서)** 라 **시각 순서가 어디에도 안 보인다.** 그래서 **`Range.getClientRects()` 로 글자 하나하나의 x 를 찍어 화면 순서를 복원**했다 — 창을 바꿔 물은 것이다(제5의 상태).
> ★★★ **RTL 글자는 원고에 한 글자도 싣지 않았다.** 양방향 제어·RTL 글자가 마크다운 렌더와 터미널을 뒤섞기 때문이다. 소스에서는 `String.fromCodePoint(0x05E9, …)` 와 문자 참조 `&#x5E9;` 로 만들고, 출력에는 **코드 포인트 16진 값(`U+05E9`)과 좌표만** 찍었다. 원고의 「히브리」·「아랍」은 **한글 이름표**다.

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
| **흔들린다(머신 사이)** | (1)·demo 의 **글자 x(px)** | 설치된 글꼴에 매인다. ★ 그래서 근거는 **절댓값이 아니라 「어느 글자가 왼쪽인가」(순서)** 다 |
| **흔들린다(머신 사이)** | (7) 의 **플랫폼 글꼴 이름** · `lang` 없는 칸의 글꼴 | 설치된 글꼴과 **시스템 로캘**에 매인다 |
| **흔들린다(머신·시점 사이)** | (7) 의 **하이픈 줄 수** | **하이픈 사전이 프로필에 있느냐**에 매인다 — 새 프로필은 비어 있다 |
| **안 흔들린다** | 화면 순서(왼쪽→오른쪽 글자 목록) · 「3 이 이름보다 오른쪽」 | 같은 판·같은 글꼴 계열이면 결정적이다 |
| **안 흔들린다** | `:dir()`·`[dir]`·`:lang()` 매칭 · 계산 `direction`·`unicode-bidi` | 〃 |
| **안 흔들린다** | 격자의 「**… = N / M**」 줄 | 스크립트가 센다 |

실측 — 이 배치(17\~20)의 캡처 **61블록을 세 번 돌려 61블록 전부 한 글자도 같았다**(흔들린 칸 0 · 고칠 것 0). 같은 머신이라 px·글꼴 칸도 안 움직였다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **② 프로브 — 글자 x 좌표**(`Range.getClientRects()`) | ★★★ **쓴다 — 본체** | 「화면에서 어느 글자가 왼쪽인가」((1)·(5)·demo) |
| **② 프로브 — 선택자·계산값** | ★ **쓴다** | 「`dir=auto` 가 무엇으로 정했나」((2)) · 「상속된 방향·언어에 선택자가 걸리나」((3)·(4)) |
| **② 프로브 — 줄 수·플랫폼 글꼴** | ★ **쓴다** | 「`lang` 이 하이픈과 글꼴을 바꾸나」((7)) |
| **⑦ 접근성 트리 — 내부 덤프** | 쓴다 | 「트리는 요소마다 어느 언어·방향을 적나」((6)) |
| **① `--dump-dom` · ⑦ CDP `ax` 모드** | **안 쓴다(쓸 수 있지만 뺐다)** | DOM 직렬화와 트리 이름에 **RTL 글자가 그대로 섞인다** — 원고 규칙 때문에 뺐다. **부적용이 아니라 「고르지 않은 창」** 이다 |
| **③ `innerText` 대 `textContent`** | **부적용** | 둘 다 **논리 순서**다 — 시각 순서를 못 본다(그래서 창 ② 로 바꿨다) |
| **④·⑤·⑥** | **부적용** | 문서 모드·요청·렌더 차단과 무관하다 — **잴 것이 없다** |

- ★★★ **제5의 상태 — 「글자 순서」를 좌표로 물었다.** 「화면에 무엇이 어떤 순서로 보이나」를 묻는 창은 원래 스크린샷(픽셀)이다. 픽셀로는 **글자를 식별할 수 없다.** 그래서 **같은 질문을 「글자마다의 x」로** 물었다. ★ **그 창이 못 보는 것** — 줄바꿈이 끼면 x 만으로는 순서가 안 선다(이 판의 문장은 전부 한 줄이다). 합자(글자 둘이 한 모양)도 x 가 겹친다.

## 한눈에 — 쉽게 말하면

**★ 오른쪽에서 왼쪽으로 쓰는 이름 하나가 옆의 숫자를 끌고 간다. `bdi` 는 그 이름에 울타리를 친다.**

**왼손잡이 손님이 끼어든 줄서기**에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 모두 **왼쪽에서 오른쪽으로** 서는 줄 | 한국어 문단 — 방향 **ltr** |
| **오른쪽에서 왼쪽으로** 서는 손님 무리 | 히브리·아랍 글자 — Bidi 클래스 **R·AL** |
| 방향 없이 **아무 쪽에나 붙는** 사람 | 공백·`:` 같은 **중립(neutral)** 글자 |
| 앞 손님을 **따라 서는** 사람 | 숫자 — **약한(weak)** 글자. **앞의 강한 글자가 R 이면 R 무리에 낀다** |
| 손님 무리에 **울타리** 치기 | **`<bdi>`**(격리 — isolate) · `dir` 을 가진 요소 |
| 무리를 **통째로 반대로** 세우기 | **`<bdo dir=rtl>`**(무시하고 뒤집기 — override) |
| 줄의 **첫 손님을 보고** 방향 정하기 | **`dir=auto`** — 첫 강한 글자 |

- **숫자는 앞 무리를 따라간다.** 히브리 이름 뒤의 `: 3` 이 이름 무리에 끼어 **이름 왼쪽으로** 튄다((1)).
- **`bdi` 로 이름을 감싸면 이름만 제자리에서 뒤집히고 숫자는 제자리**다((1)).
- **`dir=auto` 는 첫 강한 글자만 본다** — 숫자·기호·공백은 건너뛴다((2)).

```text
  논리 순서(쓴 순서) 대 시각 순서(화면 순서) — (1) 의 실측

  쓴 순서      [R1][R2][R3][R4][:][␠][3][개]      ← DOM · textContent 가 보는 것
               U+05E9 U+05DC U+05D5 U+05DD : ␠ 3 개

  span        화면  3 ␠ : U+05DD U+05D5 U+05DC U+05E9 개     ← 3 이 맨 왼쪽으로 갔다
  bdi         화면  U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개     ← 이름만 뒤집히고 3 은 제자리

  R1~R4 = 히브리 글자 넷을 쓴 순서대로 부른 이름(U+05E9 · U+05DC · U+05D5 · U+05DD)
  — 원고에 RTL 글자를 싣지 않으려고 이름표로 바꿨다
```

> **Bidi 클래스(bidirectional character type)** — 유니코드가 글자마다 매긴 방향 성질. **L**(왼→오 강함) · **R/AL**(오→왼 강함) · **EN**(유럽 숫자 — 약함) · **ON·WS**(중립) 등.\
> 예: `3` 은 EN, `:` 은 CS(약함), 공백은 WS(중립), 히브리 글자는 R.

## 이 주제가 답하려는 질문

1. **RTL 이름 옆의 숫자는 왜 튀나** — 무엇으로 그것을 **보이게** 하나, `bdi` 는 무엇을 막나.
2. **`dir=auto` 는 무엇을 보고 방향을 정하나** — 그리고 상속된 방향·언어는 어느 선택자에 걸리나.
3. **`lang` 은 화면에서 무엇을 바꾸나** — 하이픈·글꼴. 트리는 언어를 어떻게 적나.

## 동작 방식

### (1) 창 ② 좌표 — RTL 이름 뒤의 숫자가 튀는 것, `bdi` 가 막는 것

**언제 쓰나** — 이 주제의 본체. 사용자 이름·상품명처럼 **어떤 문자로 들어올지 모르는 문자열**을 UI 문장에 끼울 때.

`「〈이름〉: 3개」` 라는 문장을 다섯 벌 — 이름을 `span`·`bdi`·`span dir=auto` 로 감싸고, 이름이 히브리·라틴일 때 — 만들었다. 페이지 스크립트가 **글자 하나마다 `Range` 를 만들어 `getClientRects()[0].left`** 를 받고, 그 x 로 정렬해 **화면 왼쪽→오른쪽 순서**를 복원했다.

```html
<!-- html17b-20-bdi.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>20 이름 뒤의 숫자</title>
<style>body { font-family: sans-serif; }</style>
</head>
<body>
<div id="판"></div>
<script>
// ★ RTL 글자는 소스에 직접 쓰지 않는다 — 코드 포인트로 만든다.
const 히 = String.fromCodePoint(0x05E9, 0x05DC, 0x05D5, 0x05DD);
const 경우 = [
  ["span 에 히브리 이름", `<span>${히}</span>: 3개`],
  ["bdi 에 히브리 이름", `<bdi>${히}</bdi>: 3개`],
  ["span dir=auto 에 히브리 이름", `<span dir="auto">${히}</span>: 3개`],
  ["span 에 라틴 이름", `<span>Kim</span>: 3개`],
  ["bdi 에 라틴 이름", `<bdi>Kim</bdi>: 3개`],
];
const 판 = document.getElementById("판");
for (const [k, html] of 경우) 판.insertAdjacentHTML("beforeend", `<p data-k="${k}">${html}</p>`);
const 표기 = ch => { const c = ch.codePointAt(0); return c >= 0x0590 && c <= 0x08FF ? "U+" + c.toString(16).toUpperCase().padStart(4, "0")
  : ch === " " ? "␠" : ch; };
function 글자들(p) {                      // 논리 순서(DOM 순서)로 글자마다 화면 x 를 잰다 — 창 ②
  const out = [], w = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
  for (let t = w.nextNode(); t; t = w.nextNode())
    for (let i = 0; i < t.data.length; i++) {
      const r = document.createRange(); r.setStart(t, i); r.setEnd(t, i + 1);
      out.push({ ch: t.data[i], x: r.getClientRects()[0].left });
    }
  return out;
}
window.__대상 = [];
window.__끝 = () => {
  const O = [];
  let 튄 = 0, 전체 = 0;
  const 요약 = [];
  for (const p of 판.querySelectorAll("p")) {
    const g = 글자들(p);
    const 시각 = [...g].sort((a, b) => a.x - b.x);
    const 이름끝 = Math.max(...g.slice(0, g.findIndex(o => o.ch === ":")).map(o => o.x));
    const 숫자 = g.find(o => o.ch === "3").x;
    const 오른쪽 = 숫자 > 이름끝;
    전체++; if (!오른쪽) 튄++;
    if (p.dataset.k.startsWith("span 에 히브리") || p.dataset.k.startsWith("bdi 에 히브리")) {
      O.push("(" + (O.length ? "나" : "가") + ") " + p.dataset.k + " — 논리 순서대로 글자와 x(px)");
      O.push("  " + g.map(o => 표기(o.ch) + "@" + o.x.toFixed(0)).join("  "));
      O.push("  화면 왼쪽→오른쪽 = " + 시각.map(o => 표기(o.ch)).join(" "));
    }
    요약.push("  " + p.dataset.k.padEnd(26) + "화면 왼쪽→오른쪽 = " + 시각.map(o => 표기(o.ch)).join(" ").padEnd(42)
      + "3 이 이름보다 오른쪽 = " + 오른쪽);
  }
  O.push("");
  O.push("(다) 다섯 경우 — 시각 순서와 숫자의 자리");
  O.push(...요약);
  O.push("");
  O.push("3 이 이름 왼쪽으로 간 칸 = " + 튄 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-20-bdi.html | sed -n '1,6p'
(가) span 에 히브리 이름 — 논리 순서대로 글자와 x(px)
  U+05E9@49  U+05DC@41  U+05D5@36  U+05DD@25  :@20  ␠@17  3@8  개@61
  화면 왼쪽→오른쪽 = 3 ␠ : U+05DD U+05D5 U+05DC U+05E9 개
(나) bdi 에 히브리 이름 — 논리 순서대로 글자와 x(px)
  U+05E9@32  U+05DC@24  U+05D5@19  U+05DD@8  :@44  ␠@48  3@52  개@61
  화면 왼쪽→오른쪽 = U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개
(exit 0)
```

```text
$ python3 html17b-cdp.py page html17b-20-bdi.html | sed -n '8,15p'
(다) 다섯 경우 — 시각 순서와 숫자의 자리
  span 에 히브리 이름             화면 왼쪽→오른쪽 = 3 ␠ : U+05DD U+05D5 U+05DC U+05E9 개       3 이 이름보다 오른쪽 = false
  bdi 에 히브리 이름              화면 왼쪽→오른쪽 = U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개       3 이 이름보다 오른쪽 = true
  span dir=auto 에 히브리 이름    화면 왼쪽→오른쪽 = U+05DD U+05D5 U+05DC U+05E9 : ␠ 3 개       3 이 이름보다 오른쪽 = true
  span 에 라틴 이름              화면 왼쪽→오른쪽 = K i m : ␠ 3 개                             3 이 이름보다 오른쪽 = true
  bdi 에 라틴 이름               화면 왼쪽→오른쪽 = K i m : ␠ 3 개                             3 이 이름보다 오른쪽 = true

3 이 이름 왼쪽으로 간 칸 = 1 / 5
(exit 0)
```

```text
  UAX #9 가 「span 에 히브리 이름」을 처리하는 길 — 문단 방향 ltr (수준 0)

  글자       R1 R2 R3 R4   :     ␠     3     개
  클래스     R R R R    CS    WS    EN    L
  W6         -          ON    -     -     -      <- 숫자 사이가 아닌 구분 기호 CS 는 중립 ON 이 된다
  W7         -          -     -     EN    -      <- 3 앞의 첫 강한 글자가 R 이라 EN 그대로 (L 이면 L 이 됐다)
  N1         -          R     R     -     -      <- R 과 EN 사이의 중립은 R 이 된다 (숫자는 R 처럼 친다)
  I1 (수준)  1 1 1 1    1     1     2     0      <- 짝수 수준에서 R 은 +1, EN 은 +2
  L2         [ 수준 1 이상 덩어리를 뒤집는다 ]                  개 는 수준 0 이라 제자리
  화면       3 ␠ : R4 R3 R2 R1 개

  bdi 로 감싸면 — 이름이 격리되어 바깥에서는 「중립 한 덩어리」로 보인다
  :·␠·3 의 앞 강한 글자가 문단 시작(ltr)이 되어 W7 이 3 을 L 로 바꾸고, 전부 수준 0 에 남는다.
```

- ★★★ **3 이 이름 왼쪽으로 간 칸은 5 중 1** — 「`span` 에 히브리 이름」 하나다. 화면 순서가 **`3 ␠ : (이름 거꾸로) 개`** 이고, **`3` 과 `개` 가 갈라졌다**(x 8 대 61). 「3개」가 「3 … 개」로 찢어진 것이다.
- ★★★ **`bdi` 로 감싸면 돌아온다** — 화면 순서 **`(이름 거꾸로) : ␠ 3 개`**. 이름 **안**은 여전히 오→왼으로 그려지지만(이름의 글자 순서는 원래 그렇다), **바깥 문장의 순서는 쓴 대로**다.
- ★★ **`span dir=auto` 도 막는다** — 명세 렌더링 절이 **`[dir]` 을 가진 요소에 `unicode-bidi: isolate`** 를 준다. `bdi` 와 같은 격리다. ★ **`dir` 이 없는 `span` 은 격리가 없다** — 그래서 사고가 났다.
- ★ **라틴 이름에서는 두 경우가 같다**(`K i m : ␠ 3 개`). **이름이 RTL 일 때만** 터지므로 **개발 중 테스트 데이터로는 안 보인다.**
- ★★ **글자 순서는 DOM 에 안 보인다.** 위 블록의 「논리 순서」 줄(DOM 순서)은 다섯 경우가 전부 `이름 : ␠ 3 개` 다. **창 ① 도 창 ③ 도 똑같이 논리 순서를 준다** — 좌표를 찍어야 갈린다.

> **격리(isolate)** — 안쪽 텍스트를 바깥 양방향 계산에서 **한 개의 중립 글자처럼** 다루는 것. `unicode-bidi: isolate`.\
> 예: `<bdi>` 는 기본으로 격리되고, `dir` 을 가진 요소도 렌더링 절이 격리를 준다.

### (2) 창 ② 선택자 — `dir=auto` 는 첫 강한 글자를 본다

**언제 쓰나** — 사용자 입력·댓글처럼 방향을 모르는 덩어리에 방향을 맡길 때.

`dir=auto` 인 요소 열다섯에 문자열을 넣고, **첫 강한 글자 규칙을 옮긴 스크립트 계산** · **`:dir(rtl)` 매칭** · **계산 `direction`** · **`[dir=rtl]` 매칭**을 나란히 찍었다.

```html
<!-- html17b-20-auto.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>20 dir=auto 는 무엇을 보나</title>
</head>
<body>
<div id="판"></div>
<script>
// ★ RTL 글자는 소스에 직접 쓰지 않는다 — 코드 포인트로 만든다.
const 히 = String.fromCodePoint(0x05E9, 0x05DC, 0x05D5, 0x05DD);   // 히브리 문자 넷
const 아 = String.fromCodePoint(0x0645, 0x0631, 0x062D, 0x0628, 0x0627);   // 아랍 문자 다섯
const 경우 = [
  ["abc", "abc"],
  ["히브리", 히],
  ["아랍", 아],
  ["123 + 히브리", "123 " + 히],
  ["!abc", "!abc"],
  ["abc + 히브리", "abc " + 히],
  ["히브리 + abc", 히 + " abc"],
  ["공백 + 히브리", "   " + 히],
  ["123 만", "123"],
  ["빈 문자열", ""],
];
const 판 = document.getElementById("판");
for (const [k, s] of 경우) {
  const p = document.createElement("p");
  p.dir = "auto"; p.dataset.k = k; p.textContent = s;
  판.append(p);
}
판.insertAdjacentHTML("beforeend",
  `<p dir="auto" data-k="bdi(히브리) + abc"><bdi>${히}</bdi> abc</p>` +
  `<p dir="auto" data-k="span dir=ltr(abc) + 히브리"><span dir="ltr">abc</span> ${히}</p>` +
  `<input dir="auto" data-k="input value=히브리" value="${히}">` +
  `<input dir="auto" data-k="input value=abc" value="abc">` +
  `<textarea dir="auto" data-k="textarea 히브리">${히}</textarea>`);
// 명세 「auto 방향성」의 첫 강한 글자 규칙을 옮긴 근사 — 글자의 Bidi 클래스를 코드 포인트 범위로 어림한다
const R범위 = [[0x0590, 0x08FF], [0xFB1D, 0xFDFF], [0xFE70, 0xFEFF]];
const 강함 = ch => { const c = ch.codePointAt(0);
  if (R범위.some(([a, b]) => c >= a && c <= b)) return "rtl";
  return /\p{L}/u.test(ch) ? "ltr" : null; };
function 첫강한(e) {
  if (e.localName === "input" || e.localName === "textarea") { for (const ch of e.value) { const d = 강함(ch); if (d) return d; } return "ltr"; }
  const 걷기 = n => {
    for (const c of n.childNodes) {
      if (c.nodeType === 3) { for (const ch of c.data) { const d = 강함(ch); if (d) return d; } }
      else if (c.nodeType === 1 && !["bdi", "script", "style", "textarea"].includes(c.localName) && !c.hasAttribute("dir")) { const d = 걷기(c); if (d) return d; }
    }
    return null;
  };
  return 걷기(e) || "ltr";
}
window.__대상 = [];
window.__끝 = () => {
  const O = ["dir=auto 인 요소마다 — 첫 강한 글자 규칙(스크립트 근사) · :dir(rtl) · 계산 direction · [dir=rtl]"];
  let 갈림 = 0, 전체 = 0, rtl수 = 0;
  for (const e of 판.querySelectorAll("[data-k]")) {
    const 규칙 = 첫강한(e), 선택 = e.matches(":dir(rtl)") ? "rtl" : "ltr", 계산 = getComputedStyle(e).direction;
    전체++; if (규칙 !== 선택 || 선택 !== 계산) 갈림++; if (선택 === "rtl") rtl수++;
    O.push("  " + e.dataset.k.padEnd(28) + "규칙 = " + 규칙 + "   :dir(rtl) = " + String(e.matches(":dir(rtl)")).padEnd(6)
      + "direction = " + 계산 + "   [dir=rtl] = " + e.matches("[dir=rtl]"));
  }
  const 입력 = 판.querySelector('[data-k="input value=abc"]');
  입력.value = 히;
  O.push("");
  O.push("  input value=abc 의 value 를 스크립트로 히브리로 바꾼 뒤   :dir(rtl) = " + 입력.matches(":dir(rtl)")
    + " · direction = " + getComputedStyle(입력).direction);
  O.push("");
  O.push("rtl 로 판정된 칸 = " + rtl수 + " / " + 전체);
  O.push("규칙·:dir()·direction 이 갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-20-auto.html
dir=auto 인 요소마다 — 첫 강한 글자 규칙(스크립트 근사) · :dir(rtl) · 계산 direction · [dir=rtl]
  abc                         규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  히브리                         규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  아랍                          규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  123 + 히브리                   규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  !abc                        규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  abc + 히브리                   규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  히브리 + abc                   규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  공백 + 히브리                    규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  123 만                       규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  빈 문자열                       규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  bdi(히브리) + abc              규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  span dir=ltr(abc) + 히브리     규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  input value=히브리             규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false
  input value=abc             규칙 = ltr   :dir(rtl) = false direction = ltr   [dir=rtl] = false
  textarea 히브리                규칙 = rtl   :dir(rtl) = true  direction = rtl   [dir=rtl] = false

  input value=abc 의 value 를 스크립트로 히브리로 바꾼 뒤   :dir(rtl) = true · direction = rtl

rtl 로 판정된 칸 = 8 / 15
규칙·:dir()·direction 이 갈린 칸 = 0 / 15
(exit 0)
```

```text
  dir=auto 가 보는 것 — 명세 「auto 방향성」

  "123 + 히브리"   1 2 3 ␠ (히브리…)     숫자·공백은 약함·중립 → 건너뛴다 → 첫 강한 글자 R → rtl
  "!abc"          ! a b c               ! 는 중립 → 첫 강한 글자 L → ltr
  "abc + 히브리"   a …                   첫 강한 글자 L → ltr   (뒤의 히브리는 안 본다)
  "123 만"        강한 글자 없음         → 명세: 「없으면 ltr」
  <bdi>(히브리)</bdi> abc               bdi 안은 건너뛴다 → a → ltr
  <span dir=ltr>abc</span> (히브리)      dir 가진 요소 안은 건너뛴다 → R → rtl
  <input value>   값의 첫 강한 글자       값을 바꾸면 다시 판정한다
```

- ★★★ **규칙·`:dir()`·`direction` 이 갈린 칸 0 / 15** — 명세 규칙을 옮긴 계산과 Chrome 의 두 창이 **전부 같았다.** 「0」이 결론이다.
- ★★ **`rtl` 로 판정된 칸 8 / 15.** 숫자로 시작해도(`123 + 히브리`) 공백으로 시작해도 **첫 강한 글자**가 히브리면 rtl 이다.
- ★★ **`bdi` 안과 `dir` 을 가진 요소 안은 건너뛴다** — 명세 「contained text auto directionality」가 `bdi`·`script`·`style`·`textarea`·**`dir` 이 정의된 요소**를 건너뛰라고 적는다. 그래서 `<bdi>(히브리)</bdi> abc` 는 **ltr**, `<span dir=ltr>abc</span> (히브리)` 는 **rtl** 이다.
- ★ **`input`·`textarea` 는 값을 본다.** 스크립트로 값을 바꾼 뒤 다시 물었더니 `:dir(rtl)` 이 **`true` 로 바뀌었다** — 판정이 한 번으로 굳지 않는다.
- ★★ **`[dir=rtl]` 은 열다섯 전부 `false`** 다 — 속성 값이 `auto` 이기 때문이다. **판정된 방향을 선택자로 잡으려면 `:dir()`** 이다((3)).

### (3) 창 ② 선택자 — 상속된 방향은 `[dir=rtl]` 에 안 걸린다

**언제 쓰나** — `[dir="rtl"] .x { … }` 로 RTL 스타일을 쓰려 할 때.

```html
<!-- html17b-20-sel.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>20 상속된 방향과 언어</title>
<style>body { font-family: sans-serif; }</style>
</head>
<body>
<div dir="rtl" id="부모"><p id="자식">abc</p><p id="자식ltr" dir="ltr">abc</p></div>
<div lang="en-US" id="영부모"><p id="영자식">abc</p><p id="빈lang" lang="">abc</p></div>
<p lang="EN" id="대문자">abc</p>
<p><bdo dir="rtl" id="bdo">abc</bdo> · <span dir="rtl" id="spanrtl">abc</span> · <bdi id="bdi">abc</bdi> · <bdo id="bdo맨">abc</bdo></p>
<script>
window.__대상 = [];
const $ = id => document.getElementById(id);
function 시각(e) {
  const t = e.firstChild, g = [];
  for (let i = 0; i < t.data.length; i++) { const r = document.createRange(); r.setStart(t, i); r.setEnd(t, i + 1); g.push({ ch: t.data[i], x: r.getClientRects()[0].left }); }
  return g.sort((a, b) => a.x - b.x).map(o => o.ch).join(" ");
}
window.__끝 = () => {
  const O = ["(가) 방향 — 요소 × 선택자"];
  const 방향선택자 = [":dir(rtl)", "[dir=rtl]", "[dir=rtl] *", ":dir(ltr)"];
  let 갈림 = 0;
  for (const id of ["부모", "자식", "자식ltr"]) {
    const e = $(id);
    O.push("  #" + id.padEnd(8) + 방향선택자.map(s => s + " = " + String(e.matches(s)).padEnd(6)).join(" ") + "direction = " + getComputedStyle(e).direction);
    if (e.matches(":dir(rtl)") !== e.matches("[dir=rtl]")) 갈림++;
  }
  O.push("  :dir(rtl) 와 [dir=rtl] 가 갈린 요소 = " + 갈림 + " / 3");
  O.push("");
  O.push("(나) 언어 — 요소 × 선택자");
  const 언어선택자 = [":lang(en)", "[lang=en]", "[lang|=en]", ":lang(ko)"];
  for (const id of ["영부모", "영자식", "빈lang", "대문자"]) {
    const e = $(id);
    O.push("  #" + id.padEnd(8) + 언어선택자.map(s => s + " = " + String(e.matches(s)).padEnd(6)).join(" ") + "lang 속성 = " + JSON.stringify(e.getAttribute("lang")));
  }
  O.push("");
  O.push("(다) 글자 순서 — 화면 왼쪽→오른쪽(창 ②) · 계산 unicode-bidi · direction");
  for (const id of ["bdo", "spanrtl", "bdi", "bdo맨"]) {
    const e = $(id), s = getComputedStyle(e);
    const 꼴 = "<" + e.localName + (e.getAttribute("dir") ? " dir=" + e.getAttribute("dir") : "") + ">abc";
    O.push("  " + 꼴.padEnd(20) + "화면 = " + 시각(e) + "   unicode-bidi = " + s.unicodeBidi.padEnd(18) + "direction = " + s.direction);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-20-sel.html | sed -n '1,5p'
(가) 방향 — 요소 × 선택자
  #부모      :dir(rtl) = true   [dir=rtl] = true   [dir=rtl] * = false  :dir(ltr) = false direction = rtl
  #자식      :dir(rtl) = true   [dir=rtl] = false  [dir=rtl] * = true   :dir(ltr) = false direction = rtl
  #자식ltr   :dir(rtl) = false  [dir=rtl] = false  [dir=rtl] * = true   :dir(ltr) = true  direction = ltr
  :dir(rtl) 와 [dir=rtl] 가 갈린 요소 = 1 / 3
(exit 0)
```

```text
  <div dir="rtl" id="부모">
    <p id="자식">                     <- 방향은 물려받았다(direction = rtl) · 속성은 없다
    <p id="자식ltr" dir="ltr">        <- 다시 ltr

              :dir(rtl)   [dir=rtl]   [dir=rtl] *    :dir(ltr)
  #부모        O           O           -              -
  #자식        O           X  <-        O              -
  #자식ltr     X           X           O  <-!         O

  ★ [dir=rtl] 은 「속성이 붙은 요소」, :dir(rtl) 은 「그 방향인 요소」다.
  ★ [dir=rtl] * 는 안쪽에서 ltr 로 되돌린 요소까지 잡는다.
```

- ★★★ **`:dir(rtl)` 와 `[dir=rtl]` 이 갈린 요소 1 / 3** — `#자식`. **방향은 물려받았는데 속성은 없다.** `[dir=rtl]` 은 **속성 선택자**라 자기 속성만 본다.
- ★★ **`[dir=rtl] *`(자손 결합)은 `#자식ltr` 까지 잡는다** — 안쪽에서 `dir="ltr"` 로 되돌렸는데도. **옛날 RTL 스타일 패턴의 함정**이다 — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **32번**([논리 속성](../../../css/syntax/32-logical-properties-and-writing-mode/2-summary.md))이 「`[dir="rtl"] .x` 패턴은 논리 속성 한 줄로 대체된다」로 적은 그 패턴이다.
- **`:dir()` 은 판정된 방향을 본다** — `#자식ltr` 에서 `:dir(ltr)` 이 `true` 다.

### (4) 창 ② 선택자 — `:lang()` 은 물려받고 `[lang]` 은 안 물려받는다

```text
$ python3 html17b-cdp.py page html17b-20-sel.html | sed -n '7,11p'
(나) 언어 — 요소 × 선택자
  #영부모     :lang(en) = true   [lang=en] = false  [lang|=en] = true   :lang(ko) = false lang 속성 = "en-US"
  #영자식     :lang(en) = true   [lang=en] = false  [lang|=en] = false  :lang(ko) = false lang 속성 = null
  #빈lang   :lang(en) = false  [lang=en] = false  [lang|=en] = false  :lang(ko) = false lang 속성 = ""
  #대문자     :lang(en) = true   [lang=en] = true   [lang|=en] = true   :lang(ko) = false lang 속성 = "EN"
(exit 0)
```

- ★★ **`:lang(en)` 은 `#영자식`(속성 없음)에도 걸린다** — 언어는 **조상에게서 물려받고**, `:lang()` 은 그 **판정된 언어**를 본다. `en-US` 도 `en` 에 걸린다(하위 태그 매칭).
- ★★ **`[lang=en]`·`[lang|=en]` 은 속성만 본다** — `#영자식` 은 둘 다 `false`. `#영부모` 의 `"en-US"` 는 `[lang=en]` 에는 안 걸리고 `[lang|=en]`(「`en` 이거나 `en-` 으로 시작」)에는 걸린다.
- ★ **`[lang=en]` 이 `lang="EN"` 에 걸렸다**(`#대문자`). HTML 문서에서 `lang` 은 **값을 대소문자 무시로 비교하는 속성**이다 — Selectors 가 그 목록을 HTML 에 맡긴다.
- ★ **`lang=""` 은 `:lang(en)` 에 안 걸린다**(`#빈lang`) — 부모가 `en-US` 인데도. 명세의 「빈 문자열은 주 언어를 모른다」다. **(6) 에서 트리는 이것을 다르게 적었다.**

### (5) 창 ② 좌표 — `bdo dir=rtl` 만 라틴 글자를 뒤집는다

```text
$ python3 html17b-cdp.py page html17b-20-sel.html | sed -n '13,17p'
(다) 글자 순서 — 화면 왼쪽→오른쪽(창 ②) · 계산 unicode-bidi · direction
  <bdo dir=rtl>abc    화면 = c b a   unicode-bidi = isolate-override  direction = rtl
  <span dir=rtl>abc   화면 = a b c   unicode-bidi = isolate           direction = rtl
  <bdi>abc            화면 = a b c   unicode-bidi = isolate           direction = ltr
  <bdo>abc            화면 = a b c   unicode-bidi = isolate-override  direction = ltr
(exit 0)
```

```text
  같은 "abc" — 네 요소

  <bdo dir=rtl>   c b a    isolate-override · rtl   <- 글자의 방향 성질을 무시하고 rtl 로 강제
  <span dir=rtl>  a b c    isolate · rtl            <- 방향은 rtl 인데 L 글자는 L 로 선다
  <bdi>           a b c    isolate · ltr            <- 격리만 한다 (auto 판정 → ltr)
  <bdo>           a b c    isolate-override · ltr   <- dir 이 없으면 부모 방향(ltr)으로 강제 — 순서 그대로
```

- ★★★ **`<bdo dir=rtl>abc</bdo>` 만 `c b a`** 다. `unicode-bidi: isolate-override` 가 **글자의 Bidi 클래스를 무시하고** 전부 rtl 로 세운다.
- ★★ **`<span dir=rtl>abc</span>` 는 `a b c`** 다 — `direction: rtl` 이어도 **L 글자는 L 로** 선다. `dir=rtl` 이 바꾸는 것은 **글자 순서가 아니라 문단의 기본 방향**(정렬·중립 글자의 자리)이다.
- ★ **`dir` 없는 `<bdo>` 는 부모 방향으로 강제**한다 — 부모가 ltr 이라 순서 그대로다. 명세는 `bdo` 에 **`dir` 을 반드시 쓰라**고 적는다.

### (6) 창 ⑦ 내부 덤프 — 트리는 `lang=""` 을 부모 언어로 적었다

**언제 쓰나** — 「보조 기술은 이 문단을 어느 언어로 읽나」의 **입력**을 볼 때.

같은 파일을 내부 덤프로 찍었다. 요소마다 **`language`·`textDirection`** 이 적힌다(CDP 트리에는 없는 칸이다). `id` 에 RTL 글자가 없어 이 파일만 덤프를 실을 수 있다.

```text
$ python3 html17b-cdp.py int html17b-20-sel.html htmlTag,language,textDirection
rootWebArea             htmlTag=#document language=ko textDirection=ltr
      genericContainer #부모      htmlTag=div language=ko textDirection=rtl
        paragraph      #자식      htmlTag=p language=ko textDirection=rtl
        paragraph      #자식ltr   htmlTag=p language=ko textDirection=ltr
      genericContainer #영부모     htmlTag=div language=en-US textDirection=ltr
        paragraph      #영자식     htmlTag=p language=en-US textDirection=ltr
        paragraph      #빈lang   htmlTag=p language=en-US textDirection=ltr
      paragraph      #대문자     htmlTag=p language=EN textDirection=ltr
      paragraph               htmlTag=p language=ko textDirection=ltr
        genericContainer #bdo     htmlTag=bdo language=ko textDirection=rtl
        genericContainer #spanrtl htmlTag=span language=ko textDirection=rtl
        genericContainer #bdi     htmlTag=bdi language=ko textDirection=ltr
        genericContainer #bdo맨    htmlTag=bdo language=ko textDirection=ltr
(exit 0)
```

```text
  #빈lang  (lang="", 부모 lang="en-US")

  명세 (HTML)        「빈 문자열 = 주 언어를 모른다」
  :lang(en)          false          <- 명세대로 (4)
  트리 language      en-US          <- 부모 값을 물려 적었다

  같은 브라우저 안에서 CSS 와 접근성 트리가 lang="" 을 다르게 읽었다.
```

- ★★ **`textDirection` 은 선택자·계산값과 같다** — `#자식` rtl · `#자식ltr` ltr · `#bdo`·`#spanrtl` rtl · `#bdi` ltr. HTML-AAM 은 `dir` 을 **「텍스트 속성(writing-mode)」** 으로 넘기라고 적는다.
- ★★★ **`#빈lang` 의 `language` 가 `en-US`** 다. 명세는 `lang=""` 을 **「주 언어를 모른다」** 로 적고, 같은 브라우저의 `:lang(en)` 은 **`false`** 를 줬다((4)). **트리만 부모 언어를 물려 적었다** — 명세 ↔ 구현 불일치이고, **한 브라우저 안의 불일치**다.
- ★ **`#대문자` 는 `language=EN`** — 쓴 그대로 적었다(정규화 없음).

### (7) 창 ② — `lang` 이 하이픈과 글꼴을 바꾼다 — 하이픈은 사전이 있을 때만

**언제 쓰나** — `hyphens: auto` 를 켤 때 · 한·중·일 문자가 섞인 문서에서 글꼴이 이상할 때.

폭 90px 상자에 `hyphens: auto` 를 주고, 낱말 둘 × `lang` 넷의 **줄 수**(`span.getClientRects().length`)를 셌다. 같은 한자 두 글자 × `lang` 다섯의 **실제로 그린 글꼴**(CDP `CSS.getPlatformFontsForNode`)도 받았다. ★ 이 파일만 `<html>` 에 `lang` 이 없다(「없음」 칸을 만들려고).

```html
<!-- html17b-20-lang.html -->
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>20 lang 이 바꾸는 것</title>
<style>
.좁은 { width: 90px; hyphens: auto; font-family: sans-serif; font-size: 16px; }
.한자 { font-family: sans-serif; font-size: 16px; }
</style>
</head>
<body>
<div id="판"></div>
<script>
const 낱말 = { "영어 낱말": "internationalization characteristically", "독일어 낱말": "Donaudampfschifffahrt" };
const 언어 = ["", "en", "de", "ko"];
const 판 = document.getElementById("판");
for (const [k, w] of Object.entries(낱말))
  for (const l of 언어)
    판.insertAdjacentHTML("beforeend", `<p class="좁은"${l ? ` lang="${l}"` : ""}><span data-k="${k}" data-l="${l}">${w}</span></p>`);
const 한자언어 = ["", "ja", "zh-CN", "zh-TW", "ko"];
for (const l of 한자언어)
  판.insertAdjacentHTML("beforeend", `<p class="한자"${l ? ` lang="${l}"` : ""}><span id="한-${l || "없음"}">直骨</span></p>`);
window.__대상 = [];
window.__글꼴 = 한자언어.map(l => ["한-" + (l || "없음"), "#한-" + (l || "없음")]);
window.__끝 = () => {
  const O = ["(가) hyphens: auto · 폭 90px — 낱말 × lang 의 줄 수(span.getClientRects().length)"];
  let 갈림 = 0, 전체 = 0;
  for (const k of Object.keys(낱말)) {
    const 줄 = l => 판.querySelector(`span[data-k="${k}"][data-l="${l}"]`).getClientRects().length;
    const 기준 = 줄("");
    O.push("  " + k.padEnd(8) + 언어.map(l => "lang=" + (l || "없음") + " " + 줄(l)).join("  ·  "));
    for (const l of 언어.slice(1)) { 전체++; if (줄(l) !== 기준) 갈림++; }
  }
  O.push("  lang 없음과 줄 수가 갈린 칸 = " + 갈림 + " / " + 전체);
  O.push("");
  O.push("(나) 같은 한자 두 글자 × lang — 실제로 그린 플랫폼 글꼴(CSS.getPlatformFontsForNode)");
  for (const l of 한자언어) O.push("  lang=" + (l || "없음").padEnd(6) + JSON.stringify(__FONT["한-" + (l || "없음")]));
  return O.join("\n");
};
</script>
</body>
</html>
```

**① 새 프로필 그대로** — 하네스는 실행마다 빈 프로필로 띄운다.

```text
$ python3 html17b-cdp.py page html17b-20-lang.html
(가) hyphens: auto · 폭 90px — 낱말 × lang 의 줄 수(span.getClientRects().length)
  영어 낱말   lang=없음 2  ·  lang=en 2  ·  lang=de 2  ·  lang=ko 2
  독일어 낱말  lang=없음 1  ·  lang=en 1  ·  lang=de 1  ·  lang=ko 1
  lang 없음과 줄 수가 갈린 칸 = 0 / 6

(나) 같은 한자 두 글자 × lang — 실제로 그린 플랫폼 글꼴(CSS.getPlatformFontsForNode)
  lang=없음    ["Noto Sans CJK KR"]
  lang=ja    ["Noto Sans CJK JP"]
  lang=zh-CN ["Noto Sans CJK SC"]
  lang=zh-TW ["Noto Sans CJK TC"]
  lang=ko    ["Noto Sans CJK KR"]
(exit 0)
```

**② 같은 파일, 새 프로필에 하이픈 사전을 넣고** — `--hyphen` 이 `hyphen-data`(이 머신의 Chrome 기본 프로필에 구성 요소 갱신으로 받아져 있던 사전을 스크래치패드에 복사한 것)를 프로필에 먼저 넣는다.

```text
$ ls hyphen-data
120.0.6050.0
(exit 0)
```

```text
$ python3 html17b-cdp.py page --hyphen html17b-20-lang.html
(가) hyphens: auto · 폭 90px — 낱말 × lang 의 줄 수(span.getClientRects().length)
  영어 낱말   lang=없음 2  ·  lang=en 8  ·  lang=de 6  ·  lang=ko 2
  독일어 낱말  lang=없음 1  ·  lang=en 1  ·  lang=de 5  ·  lang=ko 1
  lang 없음과 줄 수가 갈린 칸 = 3 / 6

(나) 같은 한자 두 글자 × lang — 실제로 그린 플랫폼 글꼴(CSS.getPlatformFontsForNode)
  lang=없음    ["Noto Sans CJK KR"]
  lang=ja    ["Noto Sans CJK JP"]
  lang=zh-CN ["Noto Sans CJK SC"]
  lang=zh-TW ["Noto Sans CJK TC"]
  lang=ko    ["Noto Sans CJK KR"]
(exit 0)
```

```text
  하이픈 — lang × 사전

                      lang 없음   en    de    ko
  사전 없음   영어      2         2     2     2      <- lang 이 뭐든 아무 일도 없다
              독일어    1         1     1     1
  사전 있음   영어      2         8     6     2      <- en·de 사전이 끊었다
              독일어    1         1     5     1      <- de 사전만 독일어 복합어를 끊었다

  ★ hyphens: auto = 「lang 이 가리키는 사전이 있을 때만」
```

- ★★★ **사전이 없으면 `lang` 이 무엇이든 줄 수가 같다**(갈린 칸 0 / 6). **사전을 넣자 3 / 6 이 갈렸다** — 영어 낱말이 `en` 에서 8줄, `de` 에서 6줄, 독일어 복합어가 **`de` 에서만** 5줄.
- ★★ **`lang` 없음·`ko` 는 사전이 있어도 안 끊는다** — `hyphens: auto` 는 **콘텐츠 언어의 사전**을 쓴다. 언어를 모르거나 사전이 없는 언어면 끊지 않는다.
- ★★ **이것이 CSS 갈래의 「못 잰 것」을 푼다.** CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **51번**([줄바꿈](../../../css/syntax/51-text-wrapping-and-decoration/2-summary.md)) (5) 는 「이 headless Chrome 에 사전이 없어 `lang` 이 먹는지 못 쟀다」로 적었다. **원인이 사전 부재였다**는 것을 이 판이 **사전을 넣은 판과 뺀 판의 대조**로 보였다(그 문서는 고치지 않았다 — 이 문서의 몫이 아니다).
- ★★ **같은 한자가 `lang` 마다 다른 글꼴로 그려졌다** — `ja` → `Noto Sans CJK JP`, `zh-CN` → `SC`, `zh-TW` → `TC`, `ko`·없음 → `KR`. 한·중·일은 **같은 코드 포인트의 글자 모양이 지역마다 다르다** — `lang` 이 그 모양을 고른다. ★ **글꼴 이름은 이 머신의 설치 글꼴에 매이고**, `lang` 없는 칸은 **시스템 로캘**을 따른 것으로 보인다(머신 사이에서 흔들리는 칸).
- ★ **`lang` 이 음성 합성을 바꾸는지는 못 쟀다** — 이 머신에 음성 합성기·스크린리더가 없다. 트리에 `language` 가 적힌다((6))까지가 관찰이다.

### demo — 이름 뒤의 숫자

```html demo
<!-- html17b-20-demo.html -->
<p><span>&#x5E9;&#x5DC;&#x5D5;&#x5DD;</span>: 3개</p>
<p><bdi>&#x5E9;&#x5DC;&#x5D5;&#x5DD;</bdi>: 3개</p>
```

> **보이는 것** — 첫 줄은 **`3` 이 맨 왼쪽**, 그 오른쪽에 `:`, 히브리 이름, 그리고 **`개` 만 이름 오른쪽**에 떨어져 있다. 둘째 줄은 **이름 · `:` · `3개`** 로 쓴 순서대로 선다. 두 줄의 마크업은 이름을 감싼 요소(`span` / `bdi`) 하나만 다르다.\
> **바꿔 볼 것** — 첫 줄의 `<span>` 에 `dir="auto"` 를 주면 둘째 줄처럼 돌아온다((1) 의 「span dir=auto」 실측)

*(Chrome 151 headless 실측, 창 폭 1000: 첫 줄 이름 상자 x 25\~61 · `3` 의 x 8 — `3` 이 이름 왼쪽 / 둘째 줄 이름 상자 x 8\~44 · `3` 의 x 52 — 이름 오른쪽. 검증 파일은 [3-answer.md](3-answer.md) 의 `## 실행 검증`, 출력은 아래)*

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-20-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
창 폭 = 1000
<span>  이름 상자 x = 25~61 · 3 의 x = 8 · 3 이 이름보다 오른쪽 = false
<bdi>  이름 상자 x = 8~44 · 3 의 x = 52 · 3 이 이름보다 오른쪽 = true
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰는 꼴 | 명세가 하는 일 | 이 판의 계산값 |
|---|---|---|
| `lang="ko"`·`"en-US"` | 요소와 자손의 **언어**. 없으면 부모에게서 물려받는다 | `:lang()` 이 물려받은 값을 본다 |
| `lang=""` | 「**주 언어를 모른다**」 | `:lang(en)` 에 안 걸림 · 트리는 부모 언어 |
| `dir="ltr"`/`"rtl"` | 방향 지정 + **격리** | `unicode-bidi: isolate` |
| `dir="auto"` | **첫 강한 글자**로 방향 판정 + 격리 | `isolate`(입력·`textarea`·`pre` 는 `plaintext`) |
| `<bdi>` | 격리 + **`dir` 이 없으면 auto** | `isolate` · 판정된 방향 |
| `<bdo dir="rtl">` | 글자 성질 **무시하고** 강제 | `isolate-override` |

### 어디서 헷갈리나

- **`dir=rtl` 은 글자를 뒤집지 않는다.** 라틴 글자는 L 로 선다((5)). 뒤집는 것은 `bdo` 다.
- **`bdi` 는 방향을 정하는 요소가 아니라 울타리다.** 안쪽 방향은 `dir` 이 없으면 **auto** 로 판정된다 — 바깥에 새지 않게 하는 것이 본업이다.
- **`[dir=rtl]` 은 판정된 방향이 아니다.** 속성이 붙은 요소만 잡는다((3)).
- **`lang` 은 번역을 하지 않는다.** 글자는 그대로이고, **고르는 것**(글꼴·하이픈 사전·따옴표·음성)을 바꾼다.

## 어디서 틀리나

### 1. 사용자 이름을 `span` 으로 끼운다

**이름이 RTL 이면 옆 숫자가 튄다**((1) — 5 중 1). 라틴 이름으로 테스트하면 **안 보인다.**\
★ 처방은 **`<bdi>`** — 또는 감싼 요소에 `dir="auto"`. 둘 다 격리다.

```text
  <li><span>{{name}}</span>: {{count}}개</li>       <- 이름이 RTL 이면 count 가 이름 왼쪽으로
  <li><bdi>{{name}}</bdi>: {{count}}개</li>         <- 이름만 격리된다
```

### 2. `[dir="rtl"] .x` 로 RTL 스타일을 쓴다

**상속된 요소를 못 잡고, 되돌린 요소를 잘못 잡는다**((3)). `:dir(rtl)` 또는 **논리 속성**(CSS 32번)이다.

### 3. `hyphens: auto` 를 켰는데 `lang` 을 안 준다

**안 끊는다**((7) — `lang` 없음 2줄). ★ 그리고 **`lang` 을 줘도 브라우저에 그 언어의 사전이 없으면 안 끊는다** — 이 판의 새 프로필이 그랬다. 「켰는데 안 된다」의 원인이 둘이다.

### 4. `lang=""` 으로 「언어 지정 해제」를 한다

**CSS 는 모르는 언어로, 트리는 부모 언어로** 읽었다((4)·(6)). 한 브라우저 안에서 갈린다.\
★ 부모와 다른 언어면 **그 언어 태그를 쓴다.** 정말로 모르는 언어인 경우에만 `""` 이다.

### 5. `bdo` 를 격리 용도로 쓴다

**글자를 뒤집는다**((5) — `c b a`). 격리는 `bdi` 다.

### 6. 한·중·일이 섞인 문서에서 `lang` 을 안 준다

**한자가 시스템 로캘의 모양으로 그려진다**((7) — `lang` 없음 → `KR`). 일본어 문단의 한자가 한국식 모양으로 나온다.

## 구현 세부사항 대 언어 보장

★ 세 층으로 갈라 적는다 — **명세(WHATWG HTML · UAX #9 · HTML-AAM)가 보장하는 것 / Chrome 151 이 구현한 것 / 이 판에서 관찰한 것.**

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(UAX #9)** | 시각 순서 — W6·W7·N1·I1·L2 가 숫자를 R 무리에 넣는다 · 격리 글자는 중립 | (1) — ★ **좌표는 그 결과의 관찰**이다 |
| **명세(HTML)** | `dir=auto` 의 첫 강한 글자 규칙 · 건너뛰는 요소 · 입력 요소는 값 | (2) |
| **명세(HTML 렌더링)** | `[dir]`·`bdi` → `isolate` · `bdo` → `isolate-override` · `[dir]:dir(rtl)` → `direction: rtl` | (1)·(5) |
| **명세(HTML)** | `lang=""` = 모르는 언어 · 언어는 물려받는다 | (4) |
| **명세(Selectors · HTML)** | `:dir()`·`:lang()` 은 판정값 · `[dir]`·`[lang]` 은 속성 · `lang` 값은 대소문자 무시 | (3)·(4) |
| **구현(Chrome)** | 트리 `language` 가 `lang=""` 을 **부모 값으로** 적은 것 | (6) — ★ 명세와 갈렸다 |
| **구현(Chrome)** | 하이픈 사전을 **구성 요소 갱신으로 나중에** 받는 것 — 새 프로필은 비어 있다 | (7) |
| **이 판의 관찰** | 글자 x · 플랫폼 글꼴 이름 · `lang` 없음의 글꼴 | (1)·(7)·demo — 글꼴·로캘에 매인다 |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **`lang` 이 음성 합성의 발음을 바꾸는지** | 이 머신에 **음성 합성기·스크린리더가 없다.** 트리에 `language` 가 적힌다((6))까지가 관찰이다 — **「못 잰 것」(제3의 상태)** |
| **스크린리더가 RTL 이름을 어떤 순서로 읽는지** | 같은 이유. 소리는 **논리 순서**를 따를 것이라는 추측은 **이 문서가 적지 않는다** |
| **여러 줄에 걸친 양방향 텍스트의 순서** | x 좌표만으로는 **줄이 바뀌면 순서가 안 선다** — 이 판의 문장은 전부 한 줄이다 |
| **다른 엔진의 양방향 처리·하이픈 사전** | 엔진이 하나뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **`<html lang>` 은 항상** — 글꼴·하이픈·따옴표([14번 주제](../14-quotation-edits-and-time/2-summary.md) (2))가 전부 거기서 시작한다.
- **다른 언어의 조각에는 그 조각에 `lang`** — 한 문단 안의 일본어 인용 등.
- **방향을 모르는 문자열(사용자 입력·이름·상품명)은 `<bdi>`** — 또는 감싼 요소에 `dir="auto"`.
- **RTL 문서는 `<html dir="rtl">`** — CSS `direction` 이 아니라 마크업이다(CSS 32번이 같은 권고를 적는다).
- **`bdo` 는 글자 순서를 정말로 강제해야 할 때만** — 격리가 목적이면 `bdi`.
- **RTL 스타일은 `:dir()` 과 논리 속성으로** — `[dir=rtl]` 은 속성 선택자다.

## 핵심 문장

1. **RTL 이름 뒤의 `: 3` 은 UAX #9 가 이름 무리에 넣어 이름 왼쪽으로 보낸다 — 좌표로 찍으니 5 중 1 이 튀었고, `bdi` 로 감싸면 돌아왔다.**
2. **글자 순서는 DOM·`textContent`·`innerText` 어디에도 없다 — 글자마다 x 를 찍어야 보인다.**
3. **`dir=auto` 는 첫 강한 글자를 보고, `bdi` 안과 `dir` 가진 요소 안은 건너뛴다 — 명세 계산과 `:dir()`·`direction` 이 15 중 0 칸 갈렸다.**
4. **상속된 방향은 `:dir(rtl)` 에 걸리고 `[dir=rtl]` 에는 안 걸린다 — `[dir=rtl] *` 는 되돌린 요소까지 잡는다.**
5. **`bdo dir=rtl` 만 라틴 글자를 뒤집는다 — `dir=rtl` 은 방향만 바꾸고 L 글자는 L 로 선다.**
6. **`hyphens: auto` 는 `lang` 과 그 언어의 사전이 둘 다 있을 때만 끊는다 — 사전을 넣은 판과 뺀 판이 3 / 6 대 0 / 6 이었다.**
7. **`lang` 이 같은 한자의 글꼴을 JP·SC·TC·KR 로 바꿨다.**
8. **`lang=""` 을 CSS 는 모르는 언어로, 트리는 부모 언어로 읽었다 — 한 브라우저 안의 명세 ↔ 구현 불일치다.**

## 관련 자료

- [14번 주제 — 인용·편집·시각](../14-quotation-edits-and-time/2-summary.md) — `q` 의 따옴표 모양을 **`lang` 이 고른 실측**(ko·en `“‘` · fr `«` · ja `「『` · de `„‚`)이 (2) 에 있다. 여기의 글꼴·하이픈과 같은 「`lang` 이 고르는 것」이다.
- [04번 주제 — 공백·문자 참조](../04-whitespace-and-character-references/2-summary.md) — 이 문서가 RTL 글자를 원고에 안 싣고 **`&#x5E9;` 로 만든** 문자 참조의 정본((4)).
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **32번**([논리 속성과 글쓰기 방향](../../../css/syntax/32-logical-properties-and-writing-mode/2-summary.md)) — **CSS `direction` 이 축을 어떻게 뒤집나**와 `[dir="rtl"] .x` 패턴의 대체는 그쪽이 정본이다. 여기는 **HTML `dir` 이 그 값을 어떻게 정하나**(auto 판정·격리)까지.
- CSS 갈래 목록의 **51번**([텍스트 줄바꿈](../../../css/syntax/51-text-wrapping-and-decoration/2-summary.md)) — `hyphens` 속성의 정본. 그쪽 (5) 가 「사전이 없어 못 쟀다」로 남긴 것을 여기 (7) 이 **사전을 넣어** 쟀다.
- [`foundations/data-representation/`](../../../../data-representation/) — README 가 이 주제의 기존 주제로 드는 곳. ★ **실제로 열어 보니 유니코드의 코드 포인트·코드 유닛(§3.2)까지이고, 양방향 알고리즘은 없다.** 그래서 이 문서는 UAX #9 를 **원리까지 풀지 않고** 명세 링크와 규칙 이름(W6·W7·N1·I1·L2)으로만 접지했다.
- [13번 주제 — 구절 시맨틱](../13-phrasing-semantics/2-summary.md) — `bdi`·`bdo` 도 구절 요소다. 둘의 역할은 HTML-AAM 에서 `generic` 이다.

## 용어 풀이

- **논리 순서 / 시각 순서** — 쓴(저장된) 순서 / 화면에 보이는 순서. DOM 은 논리 순서다.
- **Bidi 클래스** — 글자의 방향 성질. L·R·AL(강함) · EN·AN·CS(약함) · WS·ON(중립).
- **첫 강한 글자** — 문자열에서 처음 나오는 L·R·AL 글자. `dir=auto` 와 UAX #9 의 P2 가 이것으로 방향을 정한다.
- **격리(isolate)** — 안쪽을 바깥 계산에서 중립 한 글자처럼 다루는 것. `bdi`·`[dir]`.
- **재정의(override)** — 글자 성질을 무시하고 방향을 강제하는 것. `bdo`.
- **`:dir()`** — 판정된 방향을 보는 의사 클래스. **`[dir]`** 은 속성 선택자다.
- **`:lang()`** — 물려받은 언어까지 보는 의사 클래스. 하위 태그(`en-US`)도 `en` 에 걸린다.
- **하이픈 사전(hyphenation dictionary)** — 낱말을 어디서 끊을 수 있는지 담은 언어별 자료. Chrome 은 구성 요소로 따로 받는다.

## 더 들어가면

- **UAX #9 의 전체 단계** — 문단 방향(P), 명시적 수준(X), 약한 글자(W1\~W7), 중립(N0\~N2), 암묵 수준(I1·I2), 재배열(L1\~L4). 이 문서는 사고 하나를 설명하는 네 규칙만 불렀다.
- **`dir=auto` 와 `unicode-bidi: plaintext`** — 렌더링 절은 `textarea`·`pre`·일부 `input` 의 `dir=auto` 에 `isolate` 대신 **`plaintext`** 를 준다 — 문단마다 방향을 따로 판정한다. 이 판에서 따로 재지 않았다.
- **`dirname` 속성** — 폼 제출 때 입력칸의 판정된 방향을 같이 보내는 속성(Baseline widely). 목록의 **21번 주제**(폼 제출) 쪽이다.
