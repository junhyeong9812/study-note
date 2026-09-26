# html/syntax/20 — `lang`·`dir` 과 양방향 텍스트: `dir=auto`·`bdi`/`bdo` — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
> ★★★ 이 주제의 본체는 **창 ② 의 글자 x 좌표**다. 글자 순서를 답할 때는 「**쓴 순서**」와 「**화면 순서(왼쪽→오른쪽)**」를 따로 적어라.
> ★ **명세·구현·관찰을 갈라라** — 시각 순서는 UAX #9 가, `dir`·`lang` 의 뜻은 WHATWG HTML 이, 좌표·트리는 Chrome 이 만든다.
> ★★ **RTL 글자는 이 파일에 한 글자도 없다.** 소스는 `String.fromCodePoint(0x05E9, …)` 로 글자를 만들고, 출력은 `U+05E9` 같은 **코드 포인트 이름**으로만 찍는다. 「히브리」·「아랍」은 한글 이름표다.
> ★ 소스 펜스 첫 줄의 `<!-- 파일이름 -->` 은 **어느 파일을 던진 것인지 표시**이지 파일 내용이 아니다. 펜스의 소스는 전부 실제로 던진 파일이다.
> ★ 이 문서의 모든 근거는 **Chrome 151 단일 엔진**의 관찰이다. 이식성은 주장 범위 밖이다.
> 선행 — [13번 주제](../13-phrasing-semantics/1-question.md)(구절 시맨틱) · [14번 주제](../14-quotation-edits-and-time/1-question.md)(`lang` 이 고른 따옴표).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 이름 뒤의 숫자 — 다섯 벌의 화면 순서 (예측)

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

- 「span 에 히브리 이름」과 「bdi 에 히브리 이름」의 **화면 왼쪽→오른쪽** 글자 순서를 코드 포인트 이름으로 적어라.
- 다섯 경우 각각 「3 이 이름보다 오른쪽」은 `true` 인가 `false` 인가?
- 마지막 줄 「**3 이 이름 왼쪽으로 간 칸 = N / 5**」의 N 은?
- 「span 에 히브리 이름」에서 `3` 과 `개` 는 화면에서 붙어 있는가?

### 2. `dir=auto` 열다섯 (예측)

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

- 열다섯 요소 각각의 `:dir(rtl)` 과 `[dir=rtl]` 은?
- 「**rtl 로 판정된 칸 = N / 15**」·「**규칙·:dir()·direction 이 갈린 칸 = N / 15**」의 N 은?
- `bdi(히브리) + abc` 와 `span dir=ltr(abc) + 히브리` 는 각각 어느 방향인가?
- `input value=abc` 의 값을 스크립트로 히브리로 바꾸면 `:dir(rtl)` 은?

### 3. 물려받은 방향과 선택자 (예측)

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

- `#부모`·`#자식`·`#자식ltr` 각각의 `:dir(rtl)` · `[dir=rtl]` · `[dir=rtl] *` · `:dir(ltr)` 은?
- 「**:dir(rtl) 와 [dir=rtl] 가 갈린 요소 = N / 3**」의 N 은?

### 4. 물려받은 언어와 글자 순서 (예측)

- 3번 소스 그대로다. `#영부모`·`#영자식`·`#빈lang`·`#대문자` 각각의 `:lang(en)` · `[lang=en]` · `[lang|=en]` 은?
- `<bdo dir=rtl>abc` · `<span dir=rtl>abc` · `<bdi>abc` · `<bdo>abc` 의 화면 순서와 계산 `unicode-bidi` 는?

### 5. `lang` 과 하이픈·글꼴 (예측)

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

- 새 프로필(하이픈 사전 없음)에서 낱말 둘 × `lang` 넷의 줄 수는? 「**lang 없음과 줄 수가 갈린 칸 = N / 6**」의 N 은?
- 사전을 넣은 프로필(`--hyphen`)에서는?
- 같은 한자 두 글자를 `lang` 없음·`ja`·`zh-CN`·`zh-TW`·`ko` 로 그리면 플랫폼 글꼴 이름은?

### 6. 트리가 적는 언어와 방향 (예측)

- 3번 소스를 내부 덤프(`int` 모드)로 찍는다. 요소마다 `language` 와 `textDirection` 은?
- `#빈lang` 의 `language` 는 무엇으로 찍히는가?

### 7. 숫자의 자리를 정하는 규칙 (왜)

- 1번의 「span 에 히브리 이름」을 UAX #9 의 규칙 이름(W6·W7·N1·I1·L2)으로 한 줄씩 따라가라. `3` 은 어느 수준(level)을 받는가?
- `bdi` 로 감싸면 W7 에서 무엇이 달라지는가? 격리된 이름은 바깥 계산에서 무엇으로 보이나?
- 이 글자 순서가 DOM·`textContent`·`innerText` 에 안 보이는 이유는? 그래서 무엇으로 물었나 — 제 몇의 상태인가?

### 8. 명세·구현·관찰 가르기 (경계)

- 1번의 화면 순서는 명세의 보장인가 관찰인가? x 값(px)과 「어느 쪽이 왼쪽인가」는 각각 무엇인가?
- 이 주제에서 **명세 ↔ Chrome 불일치**는 어디인가? 한 브라우저 **안에서** 갈린 것은?
- 5번의 하이픈 결과는 명세·구현·환경 중 무엇에 매이나?

### 9. 이 판이 못 보는 것 (경계)

- 「`lang` 이 음성 합성의 발음을 바꾼다」를 이 문서가 실측으로 쓸 수 있는가? 그것은 제 몇의 상태인가?
- 글자 x 로 시각 순서를 복원하는 창이 **못 보는 경우**는?

### 10. 정본 경계 긋기 (연결)

- `lang` 이 따옴표 모양을 고른 실측은 어느 주제의 몇 절인가?
- CSS `direction` 이 축을 뒤집는 것과 `hyphens` 속성의 정본은 CSS 갈래의 몇 번인가? 그중 하나가 남긴 「못 잰 것」을 이 주제가 어떻게 이었나?
- README 가 이 주제의 기존 주제로 드는 `foundations/data-representation/` 에는 **양방향 알고리즘**이 있는가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
