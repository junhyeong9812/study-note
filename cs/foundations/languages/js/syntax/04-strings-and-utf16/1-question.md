# js/syntax/04 — 문자열과 UTF-16: 「`length` 가 세는 것은 글자가 아니다」 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 「틀림」으로 표시한다.
>
> **환경** — node v18.19.1(기본 PATH · ICU 74.2 · 유니코드 15.1) · v20.19.6(nvm · ICU 77.1 · 유니코드 16.0) ·
> Google Chrome 151.0.7922.173 · x86-64 Linux.
>
> ★★ **이 주제의 인출 축은 셋**이다 —
> ① **네 가지 자가 어디서 갈리나** ② **페어 한가운데를 자르면 무엇이 남나** ③ **자소를 물을 수 있는 도구가 있나**.
> ★★★ **1번이 이 주제의 본체다** — 격자의 네 열을 채울 수 있어야 한다.
> ★★★ **7번은 두 판이 갈린다.** 이 배치 네 주제에서 **유일한 자리**다 — 양쪽을 다 적어야 답이다.
> ★★ **코드 유닛은 `\uXXXX` 로 펼쳐 적어라.** 이모지를 그대로 적으면 몇 칸인지 안 보인다.
>
> **선행** — [01](../01-value-types-and-typeof/2-summary.md) · [02](../02-coercion-and-loose-equality/2-summary.md)(`'10' < '9'`) ·
> [03](../03-numbers-and-bigint/2-summary.md)(큰 ID 를 문자열로).

## 이 파일을 푸는 법

- ★★ **예측형 여섯 문항(1·2·3·4·5·7)은 소스만 보고 출력을 적어 본 뒤** 답을 연다.
- ★★★ **1번은 열 줄 × 네 열을 채워야** 답이다. 못 채우면 이 주제를 다시 읽는다.
- ★★★ **4번은 「무엇이 일어나나」가 아니라 「나가는 길마다 무엇이 다른가」를 적어야** 답이다.
- ★ 각 문항 끝에서 스스로 물어라 — 「**이것은 명세인가 ICU 데이터인가**」.

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. 한 문자열을 네 번 재면 (예측) ★★★ 이 주제의 본체

```js
// js01b-04a-code-unit-grid.js
// 한 문자열을 네 가지 자로 재 본다 — 코드 유닛 · 코드 포인트 · 자소 · UTF-8 바이트.
// ★ 네 칸이 전부 다른 답을 내는 것이 이 주제의 전부다.
const CP = String.fromCodePoint;
const SAMPLES = [
  ["ascii A",      "A"],
  ["hangul GA",    "가"],
  ["NFC e-acute",  "\u00e9"],
  ["NFD e-acute",  "e\u0301"],
  ["jamo HAN",     "\u1112\u1161\u11ab"],
  ["thumbs up",    "👍"],
  ["thumbs+skin",  "👍" + CP(0x1f3fd)],
  ["family ZWJ",   "👨\u200d👩\u200d👧"],
  ["flag KR",      "🇰🇷"],
  ["rainbow flag", "🏳\ufe0f\u200d🌈"],
];

const seg = new Intl.Segmenter("ko", { granularity: "grapheme" });
const esc = (s) => Array.from({ length: s.length }, (_, i) =>
  "\\u" + s.charCodeAt(i).toString(16).padStart(4, "0")).join("");

console.log("[1] 네 가지 자 — 같은 문자열을 네 번 잰다");
console.log("name".padEnd(15) + "s.length".padStart(9) + "[...s]".padStart(8) +
            "grapheme".padStart(10) + "utf8".padStart(7));
console.log("-".repeat(15 + 9 + 8 + 10 + 7));
for (const [name, s] of SAMPLES)
  console.log(name.padEnd(15) +
    String(s.length).padStart(9) +
    String([...s].length).padStart(8) +
    String([...seg.segment(s)].length).padStart(10) +
    String(Buffer.byteLength(s, "utf8")).padStart(7));

console.log("");
console.log("[2] s.length 가 세고 있는 것 — 코드 유닛을 그대로 펼치면");
for (const [name, s] of SAMPLES) console.log("  " + name.padEnd(15) + esc(s));

console.log("");
console.log("[3] 눈으로 보는 글자 (터미널 폭은 또 다른 이야기다)");
for (const [name, s] of SAMPLES) console.log("  " + name.padEnd(15) + s);
```

- ★★★ 열 줄의 **네 열**(`length`·`[...s]`·자소·utf8 바이트)을 각각 채우면?
- ★★★ **네 열이 전부 다른 줄**이 있는가? 어느 것인가?
- ★★★ `[2]` 에서 가족 이모지의 **코드 유닛 열**을 적으면? 8칸이 무엇무엇인가?
- ★★ 조합형 한글은 몇 칸인가? **완성형과 어떻게 다른가**?
- ★★ 국기가 **자소 1 인데 코드 포인트 2** 인 이유는?
- ★ **DB 칼럼 크기**를 정할 때 필요한 열은 어느 것인가?

### 2. 서로게이트 페어를 해부하면 (예측) ★★★

```js
// js01b-04b-surrogate-pair.js
// 서로게이트 페어 해부 — 코드 포인트 하나가 코드 유닛 둘로 앉는 방식.
const e = "👍";
const hex = (n) => "U+" + n.toString(16).toUpperCase().padStart(4, "0");

console.log("[1] 한 글자인데 자리는 둘이다");
console.log("  s.length            :", e.length);
console.log("  charCodeAt(0)       :", e.charCodeAt(0), hex(e.charCodeAt(0)), "(high surrogate)");
console.log("  charCodeAt(1)       :", e.charCodeAt(1), hex(e.charCodeAt(1)), "(low surrogate)");
console.log("  codePointAt(0)      :", e.codePointAt(0), hex(e.codePointAt(0)));
console.log("  codePointAt(1)      :", e.codePointAt(1), hex(e.codePointAt(1)), "<- 뒤 조각만 따로 읽힌다");

console.log("");
console.log("[2] 둘을 합치는 산수 — 명세가 정한 식 그대로");
const hi = e.charCodeAt(0), lo = e.charCodeAt(1);
console.log("  (hi - 0xD800) * 0x400 + (lo - 0xDC00) + 0x10000");
console.log("  = (" + hi + " - 55296) * 1024 + (" + lo + " - 56320) + 65536");
console.log("  =", (hi - 0xd800) * 0x400 + (lo - 0xdc00) + 0x10000, "=", hex(e.codePointAt(0)));
console.log("  String.fromCharCode(hi, lo) === s :", String.fromCharCode(hi, lo) === e);
console.log("  String.fromCodePoint(0x1F44D) === s :", String.fromCodePoint(0x1f44d) === e);

console.log("");
console.log("[3] 서로게이트 구간은 '글자가 아닌' 자리다");
console.log("  0xD800 ~ 0xDFFF 는 코드 포인트 공간에서 비워 둔 2048칸");
console.log("  BMP 밖(0x10000 이상)의 글자는 그 두 칸을 빌려 두 유닛으로 앉는다");
console.log("  0xFFFF 까지인가 :", String.fromCharCode(0xffff).length, "| 0x10000 부터인가 :", String.fromCodePoint(0x10000).length);

console.log("");
console.log("[4] charCodeAt 과 codePointAt — 언제 갈리나");
const mixed = "a" + e + "가";
console.log("  s =", JSON.stringify(mixed), "| length =", mixed.length);
console.log("  i  charCodeAt   codePointAt  s[i] 를 escape 로");
for (let i = 0; i < mixed.length; i++)
  console.log("  " + String(i).padEnd(3) +
    String(mixed.charCodeAt(i)).padEnd(12) +
    String(mixed.codePointAt(i)).padEnd(13) +
    "\\u" + mixed.charCodeAt(i).toString(16).padStart(4, "0"));
console.log("  ★ codePointAt 은 '그 자리에서 시작하는 코드 포인트' 를 준다 —");
console.log("    high 자리에서는 합쳐 읽고, low 자리에서는 그 조각만 준다.");
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ `charCodeAt(0)` 과 `codePointAt(0)` 이 다른 이유는?
- ★★★ `codePointAt(1)` 이 `56397` 인 이유는? **무엇을 조심해야 하나**?
- ★★ 두 칸을 합치는 산수는 무엇인가? 결과가 맞는가?
- ★★ 한 칸에 앉는 경계는 어디인가? 실제로 던져 보면?
- ★★ `[4]` 의 표에서 **두 함수가 갈리는 자리는 몇 개**이고 어디인가?

### 3. 여섯 가지로 쪼개면 (예측) ★★★

```js
// js01b-04c-splitting.js
// 같은 문자열을 여섯 가지 방법으로 쪼갠다 — 어느 것이 무엇을 단위로 삼나.
const esc = (s) => Array.from({ length: s.length }, (_, i) =>
  "\\u" + s.charCodeAt(i).toString(16).padStart(4, "0")).join("");
const show = (parts) => "[" + parts.map(esc).join(" | ") + "]";

const seg = new Intl.Segmenter("ko", { granularity: "grapheme" });
const samples = [["thumbs up", "👍"], ["NFD e-acute", "e\u0301"], ["family ZWJ", "👨\u200d👩\u200d👧"]];

for (const [name, s] of samples) {
  console.log("[" + name + "]  s.length = " + s.length);
  console.log("  s.split('')      " + show(s.split("")));
  console.log("  [...s]           " + show([...s]));
  console.log("  Array.from(s)    " + show(Array.from(s)));
  console.log("  for...of         " + show((() => { const a = []; for (const c of s) a.push(c); return a; })()));
  console.log("  s.split(/(?:)/u) " + show(s.split(/(?:)/u)));
  console.log("  Segmenter        " + show([...seg.segment(s)].map((x) => x.segment)));
  console.log("");
}

console.log("[뒤집기 — 이 차이가 눈에 보이는 자리]");
const t = "a👍b";
console.log("  원본                 :", t, "|", esc(t));
console.log("  split('').reverse()  :", t.split("").reverse().join(""), "|", esc(t.split("").reverse().join("")));
console.log("  [...t].reverse()     :", [...t].reverse().join(""), "|", esc([...t].reverse().join("")));
console.log("");
console.log("[인덱스 접근 세 가지]");
console.log("  t[1]           :", esc(t[1]));
console.log("  t.charAt(1)    :", esc(t.charAt(1)));
console.log("  t.at(1)        :", esc(t.at(1)));
console.log("  [...t][1]      :", esc([...t][1]), " <- 이것만 '글자' 다");
```

- 세 문자열 × 여섯 방법의 출력을 각각 적으면?
- ★★★ **깨뜨리는 방법**은 어느 것인가? 나머지 다섯과 무엇이 다른가?
- ★★★ NFD 형태(`e` + `U+0301`)와 가족 이모지에서는 **몇 개가 하나로 보는가**? 그래서 「안 깨진다」에 몇 단계가 있는가?
- ★★ 뒤집기 두 가지의 결과를 코드 유닛으로 적으면?
- ★★ `t[1]`·`charAt(1)`·`at(1)`·`[...t][1]` 중 **글자를 주는 것**은? 그 비용은?
- ★ `split(/(?:)/u)` 에서 `u` 를 빼면 어떻게 되는가?

### 4. 페어 한가운데를 자르면 (예측) ★★★ 본체

```js
// js01b-04d-cut-through-pair.js
// 서로게이트 페어 한가운데를 자르면 JS 는 무엇을 하나 — 터지지도 고치지도 않는다.
const esc = (s) => Array.from({ length: s.length }, (_, i) =>
  "\\u" + s.charCodeAt(i).toString(16).padStart(4, "0")).join("");
const s = "ab👍cd";

console.log("[1] 자르는 자리는 그냥 받아들여진다");
console.log("  s          =", JSON.stringify(s), "| length =", s.length);
console.log("  s.slice(0,3)  ->", esc(s.slice(0, 3)), "| length", s.slice(0, 3).length);
console.log("  s.slice(3)    ->", esc(s.slice(3)), "| length", s.slice(3).length);
console.log("  s.substring(0,3) ->", esc(s.substring(0, 3)));
console.log("  s.substr(2,1)    ->", esc(s.substr(2, 1)));
console.log("  ★ 예외도 경고도 없다. 잘린 반쪽이 그대로 문자열 안에 남는다.");

const half = s.slice(0, 3).slice(2);
console.log("");
console.log("[2] 그 반쪽은 '값' 으로는 아무 문제가 없다");
console.log("  half              =", esc(half));
console.log("  half.length       =", half.length);
console.log("  typeof half       =", typeof half);
console.log("  half === half     =", half === half);
console.log("  half.charCodeAt(0)=", half.charCodeAt(0));
console.log("  half + 'x'        =", esc(half + "x"));
console.log("  half 을 그대로 찍으면:", half);

console.log("");
console.log("[3] 밖으로 내보낼 때에야 드러난다 — 경로마다 대답이 다르다");
const probes = [
  ["JSON.stringify(half)",       () => JSON.stringify(half)],
  ["encodeURIComponent(half)",   () => encodeURIComponent(half)],
  ["Buffer.from(half,'utf8')",   () => [...Buffer.from(half, "utf8")].map((b) => b.toString(16)).join(" ")],
  ["Buffer utf8 roundtrip ===",   () => Buffer.from(half, "utf8").toString("utf8") === half],
  ["Buffer.from(half,'utf16le')", () => [...Buffer.from(half, "utf16le")].map((b) => b.toString(16)).join(" ")],
  ["Buffer utf16le roundtrip ===",() => Buffer.from(half, "utf16le").toString("utf16le") === half],
  ["new TextEncoder().encode",    () => [...new TextEncoder().encode(half)].map((b) => b.toString(16)).join(" ")],
  ["half.normalize('NFC')",       () => esc(half.normalize("NFC"))],
  ["JSON.parse(JSON.stringify) ===",() => JSON.parse(JSON.stringify(half)) === half],
];
for (const [label, f] of probes) {
  let r;
  try { r = String(f()); } catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(30) + " -> " + r);
}

console.log("");
console.log("[4] 잘 잘라내는 법");
console.log("  [...s].slice(0,3).join('') ->", esc([...s].slice(0, 3).join("")));
const seg = new Intl.Segmenter("ko", { granularity: "grapheme" });
console.log("  Segmenter 로 3자소         ->", esc([...seg.segment(s)].slice(0, 3).map((x) => x.segment).join("")));
```

- 네 묶음의 출력을 각각 적으면?
- ★★★ 자르는 자리에서 **무슨 일이 나는가**? 예외는? 경고는?
- ★★★ 그 반쪽은 **값으로서 정상인가**? 무엇으로 확인했는가?
- ★★★ `[3]` 의 아홉 줄에서 **나가는 길마다 답이 어떻게 다른가**? 표로 적으면?
- ★★★ **되돌릴 수 없는 길**은 어느 것인가? 되돌아가는 길은?
- ★★ **Rust · Go · JS 가 같은 상황에서 각각 무엇을 하는가**?
- ★ 잘 자르는 법 두 가지는?

### 5. 정규화 (예측) ★★★

```js
// js01b-04e-normalize.js
// 눈에 같은 두 문자열이 === 로 다른 자리 — 그리고 K 가 붙은 두 형태가 글자를 갈아치우는 것.
const esc = (s) => Array.from({ length: s.length }, (_, i) =>
  "\\u" + s.charCodeAt(i).toString(16).padStart(4, "0")).join("");
const nfc = "\u00e9", nfd = "e\u0301";

console.log("[1] === 는 정규화를 전혀 보지 않는다");
console.log("  두 문자열       :", nfc, nfd, " <- 화면에는 같아 보인다");
console.log("  esc             :", esc(nfc), "|", esc(nfd));
console.log("  length          :", nfc.length, nfd.length);
console.log("  nfc === nfd     :", nfc === nfd);
console.log("  nfc == nfd      :", nfc == nfd);
console.log("  Object.is       :", Object.is(nfc, nfd));
console.log("  [nfc].includes  :", [nfc].includes(nfd));
console.log("  new Set 크기     :", new Set([nfc, nfd]).size);
console.log("  Map 조회         :", new Map([[nfc, "found"]]).get(nfd));
console.log("  localeCompare   :", nfc.localeCompare(nfd), " <- 0 이면 로캘 기준으로는 같다고 본다");

console.log("");
console.log("[2] normalize 를 거치면 같아진다");
console.log("  nfd.normalize('NFC') === nfc :", nfd.normalize("NFC") === nfc);
console.log("  nfc.normalize('NFD') === nfd :", nfc.normalize("NFD") === nfd);
console.log("  normalize() 기본값은 NFC 인가 :", nfd.normalize() === nfc);

console.log("");
console.log("[3] 한글은 이 문제가 더 크다 — 조합형과 완성형");
const jamo = "\u1112\u1161\u11ab";
console.log("  조합형 '한'  :", jamo, "| length", jamo.length, "|", esc(jamo));
console.log("  완성형 '한'  :", "한", "| length", "한".length, "|", esc("한"));
console.log("  === 인가     :", jamo === "한");
console.log("  NFC 뒤       :", jamo.normalize("NFC") === "한", "| length", jamo.normalize("NFC").length);
console.log("  '한글'.normalize('NFD').length :", "한글".normalize("NFD").length);

console.log("");
console.log("[4] K 가 붙으면 '같은 글자로 모으는' 게 아니라 '다른 글자로 바꾼다'");
console.log("code unit".padEnd(12) + "NFC len".padStart(8) + "NFD len".padStart(9) +
            "NFKC len".padStart(10) + "   원본 -> NFKC");
console.log("-".repeat(12 + 8 + 9 + 10 + 18));
for (const s of ["\u00bd", "\u2163", "\ufb01", "\u2460", "\u3273", "\u00b2", "\u212b"])
  console.log(esc(s).padEnd(12) +
              String(s.normalize("NFC").length).padStart(8) +
              String(s.normalize("NFD").length).padStart(9) +
              String(s.normalize("NFKC").length).padStart(10) +
              "   " + JSON.stringify(s) + " -> " + JSON.stringify(s.normalize("NFKC")));

console.log("  ★ 마지막 줄은 K 가 아닌데도 글자가 바뀐다 — NFC 가 이미 바꾼다:");
console.log("     \u212b -> NFC -> " + esc("\u212b".normalize("NFC")) + "  (ANGSTROM SIGN 이 A WITH RING 으로)");

console.log("");
console.log("[5] normalize 가 못 고치는 것");
console.log("  family.normalize('NFC').length :", ("👨\u200d👩\u200d👧").normalize("NFC").length, "<- ZWJ 는 그대로다");
let e;
try { "a".normalize("NFX"); } catch (err) { e = err.constructor.name + ": " + err.message; }
console.log("  'a'.normalize('NFX') :", e);
```

- 다섯 묶음의 출력을 각각 적으면?
- ★★★ `===` 와 `localeCompare` 가 **다른 답**을 내는 이유는?
- ★★★ 한글 조합형과 완성형은 각각 몇 칸인가? `"한글".normalize("NFD").length` 는?
- ★★ `NFKC` 가 **길이를 바꾸는** 줄은 어느 것인가?
- ★★★ **`K` 가 아닌데도 글자가 바뀌는 줄**이 하나 있다 — 무엇인가? 그것이 어떤 직관을 깨는가?
- ★ `normalize` 가 **못 고치는 것**은 무엇인가? 없는 형태를 주면?

### 6. 자소를 묻는 도구 (경계) ★★

- `Intl.Segmenter` 가 **있는지 어떻게 확인했는가**? 문서를 읽었는가?
- ★★★ 일곱 문자열 중 **자소가 1 이 아닌 것**은 몇 개인가?
- ★★ `granularity` 를 바꾸면 같은 문장이 **몇 조각**으로 갈리는가?
- ★★ 단어 분할이 **공백 분할과 다른** 자리는?
- ★★★ 이 도구로도 **못 답하는 질문**이 하나 남는다 — 무엇인가? 왜 이 문서는 그 수치를 안 적었는가?
- ★★ 자소 수는 **어느 층**에 속하는가? 두 판에서 같았다면 보장인가?

### 7. `isWellFormed` 를 두 판에 던지면 (예측) ★★★

```js
// js01b-04g-well-formed.js
// ES2024 의 well-formed 문자열 메서드 — 이 배치에서 두 판이 갈린 유일한 자리다.
const esc = (s) => Array.from({ length: s.length }, (_, i) =>
  "\\u" + s.charCodeAt(i).toString(16).padStart(4, "0")).join("");
const lone = "👍".slice(0, 1);

console.log("node", process.version, "| v8", process.versions.v8,
            "| icu", process.versions.icu, "| unicode", process.versions.unicode);
console.log("");
console.log("  typeof String.prototype.isWellFormed :", typeof String.prototype.isWellFormed);
console.log("  typeof String.prototype.toWellFormed :", typeof String.prototype.toWellFormed);

const probes = [
  ["pair.isWellFormed()",  () => "👍".isWellFormed()],
  ["lone.isWellFormed()",  () => lone.isWellFormed()],
  ["ascii.isWellFormed()", () => "a".isWellFormed()],
  ["lone.toWellFormed()",  () => esc(lone.toWellFormed())],
  ["pair.toWellFormed()",  () => esc("👍".toWellFormed())],
];
console.log("");
for (const [label, f] of probes) {
  let r;
  try { r = String(f()); } catch (e) { r = e.constructor.name + ": " + e.message; }
  console.log("  " + label.padEnd(24) + " -> " + r);
}

console.log("");
console.log("  ★ 이 메서드가 없는 판에서 같은 일을 손으로 하려면:");
const broken = (s) => /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/.test(s);
console.log("    직접 짠 검사 — lone 이 깨졌나 :", broken(lone));
console.log("    직접 짠 검사 — pair 가 깨졌나 :", broken("👍"));
console.log("    JSON.stringify 로도 드러난다  :", JSON.stringify(lone));
console.log("    Buffer 왕복으로도 드러난다     :", Buffer.from(lone, "utf8").toString("utf8") === lone);
```

- ★★★ **v20 과 v18 의 출력을 각각** 적으면?
- ★★★ v18 에서 다섯 줄이 **무엇으로 바뀌는가**?
- ★★ `toWellFormed()` 는 무엇을 하는가? 4번 절의 **어느 동작과 같은가**? 차이는?
- ★★ 이 메서드가 없는 판에서 **같은 일을 하는 법** 셋을 대면?
- ★ 두 출력을 가르는 **유일한 근거 줄**은 어느 것인가?

### 8. 브라우저 (경계) ★★

- ★★★ Chrome 151 에 `isWellFormed` 가 **있는가**? 그 사실이 「Node 18 에 없다」와 어떻게 맞물리는가?
- ★★ 「같은 V8 이면 같다」는 어디가 틀렸는가?
- ★★ 자소 수·코드 유닛 수·바이트 수가 Node 와 **갈렸는가**?
- ★ `encodeURIComponent` 와 `TextEncoder` 는 브라우저에서 어떻게 나오는가?

### 9. 보장인가 데이터인가 (연결) ★★★ 이 갈래의 축

- ★★★ 이 주제에서 **명세 보장** 칸에 들어가는 것 다섯을 대면?
- ★★★ **ICU 데이터에 달린 것**은 무엇인가? 왜 그 칸을 따로 세웠는가?
- ★★ `Buffer` 로 얻은 결론이 **Node 에만 매인 것**인가? 무엇으로 확인했는가?
- ★★ 「두 판에서 자소 수가 같았다」는 무엇의 근거가 되고 무엇의 근거가 못 되는가?
- ★ 이 주제에서 **판이 갈린 자리**는 몇 개인가?

### 10. 경계와 형제들 (연결) ★★★

- **문자 인코딩의 원리** · **`String` 메서드** · **정규식의 `u` 플래그** · **`JSON`** 은 각각 어디가 정본인가?
- ★★★ **파이썬**은 무엇을 세는가? 같은 이모지에서 `len` 이 얼마인가?
- ★★★ **러스트**는 무엇을 세고, 경계가 아닌 자리를 자르면 무엇을 하는가?
- ★★ **자바**는 어느 집안인가? 무엇이 같은가?
- ★★ **Go** 는 같은 상황에서 무엇을 하는가? JS 와 어떻게 다른가?
- ★ 이 주제가 **끝까지 책임지는 것** 세 가지를 대면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
