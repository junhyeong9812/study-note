# js/syntax/04 — 문자열과 UTF-16: 「`length` 가 세는 것은 글자가 아니다」 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **이 본문은 원고가 아니라 Claude 작성이다**(문법·API 갈래는 원고 없이 공식 문서로 접지한다).
>
> **기준 소스** — 열어서 확인한 것만.
> - [ECMA-262 최신 초안](https://tc39.es/ecma262/) — String 타입(UTF-16 코드 유닛의 열)·`codePointAt`·`normalize`·well-formed 메서드
> - [ECMA-262 판별 아카이브](https://262.ecma-international.org/) — `isWellFormed`/`toWellFormed` 가 들어온 판(ES2024)을 가릴 때
> - [ECMA-402 (Intl)](https://tc39.es/ecma402/) — `Intl.Segmenter`
> - [MDN — `String.prototype.length`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/length) · [MDN — `Intl.Segmenter`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/Segmenter)
>
> ★★★ **명세 조항 번호는 인용하지 않는다.** 규칙 진술은 위 문서로, **값·예외 타입과 메시지는 전부 실행으로** 접지했다.
>
> **실행 검증** — 이 문서의 모든 출력은 **실제로 돌려 받은 것**이고, 블록은 **전부 캡처 파일에서 조립**했다.
> 배너의 `node20` 은 `~/.nvm/versions/node/v20.19.6/bin/node`, `node18` 은 기본 PATH 의 `node`(v18.19.1)다.
> **어느 판에서 나왔는지는 아래 첫 블록**에 있다.

```sh
// js01b-versions.sh
#!/usr/bin/env bash
# 이 문서의 모든 출력이 어느 판에서 나왔는지 — 첫 블록에 싣는다.
set -u -o pipefail
N18=node
N20="$HOME/.nvm/versions/node/v20.19.6/bin/node"
for n in "$N18" "$N20"; do
  "$n" -e 'const v = process.versions;
    console.log("node " + v.node + "  v8 " + v.v8 + "  icu " + v.icu + "  unicode " + v.unicode +
                "  Intl.Segmenter " + typeof Intl.Segmenter +
                "  isWellFormed " + typeof String.prototype.isWellFormed);'
done
google-chrome --version 2>/dev/null
```

```text
===== ./js01b-versions.sh (exit=0) =====
node 18.19.1  v8 10.2.154.26-node.28  icu 74.2  unicode 15.1  Intl.Segmenter function  isWellFormed undefined
node 20.19.6  v8 11.3.244.8-node.33  icu 77.1  unicode 16.0  Intl.Segmenter function  isWellFormed function
Google Chrome 151.0.7922.173 
```

> ★★★ **이 배치 네 주제에서 두 판이 갈린 자리는 여기 하나뿐이다** — `isWellFormed`/`toWellFormed`(ES2024)가
> **v18 에는 없고 v20 에 있다.** 그래서 이 주제만 **양쪽 출력을 둘 다** 싣는다(7번 절).
> ★★ **코드 유닛을 볼 때는 `\uXXXX` 로 펼쳐 찍는다** — 이모지를 그대로 찍으면 **터미널 폭에 따라 칸이 어긋나고**
> 무엇이 몇 유닛인지 안 보인다. 이 문서의 격자가 전부 ASCII 인 이유다.
> ★★ **던지는 형태를 하나로 고정했다** — 예외는 `try`/`catch` 로 받아 **`e.constructor.name` 과 `e.message` 만** 찍는다.
>
> **버전** — `String` 은 초판부터 UTF-16 이다. `codePointAt`·`normalize`·`for...of` 의 코드 포인트 순회는 **ES2015**,
> `Intl.Segmenter` 는 **ES2022(ECMA-402)**, **`isWellFormed`/`toWellFormed` 는 ES2024** 다.
> `JSON.stringify` 가 짝 없는 서로게이트를 이스케이프하는 것(well-formed JSON.stringify)은 **ES2019** 다.
>
> **★ 흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **코드 유닛 격자의 모든 칸** — `length`·`[...s]`·바이트 수 |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **`\uXXXX` 로 펼친 코드 유닛 열** |
> | ★★ **`Intl.Segmenter` 의 자소 수** — ICU 판에 달렸다 | ★★ **예외의 종류** — `URIError`·`RangeError` |
> | **터미널에서 이모지가 몇 칸인가** — 잴 방법이 표준에 없다 | ★★ `normalize` 의 결과 · 종료 코드 |
>
> ★★ **자소 수만 「흔들릴 수 있는 칸」으로 선언한다** — ICU 74.2(v18)와 77.1(v20)은 유니코드 판이 다른데
> **이 문서의 일곱 문자열에서는 한 글자도 안 갈렸다.** 그래도 **보장이 아니므로** 흔들리는 쪽에 둔다.
>
> **선행** — [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md)(`"string"` 이 원시 값인 것) ·
> [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md)(**`'10' < '9'` 가 참인 이유**) ·
> [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md)(큰 ID 를 문자열로 주고받는 이유)
>
> ★★ **경계 — 문자 인코딩의 원리는 여기가 아니다.** [`cs/foundations/data-representation/`](../../../../data-representation/)가
> 「코드 포인트와 UTF-8/16 의 비트 배치」의 정본이다.
> **여기는 「JS 의 문자열이 UTF-16 코드 유닛의 열이라는 것이 코드에서 무엇을 만드나」부터다.**

## 한눈에 — 쉽게 말하면

**JS 의 문자열은 「글자의 줄」이 아니라 「16비트 칸의 줄」이다.**

16비트 칸 하나에 글자 하나가 들어가면 좋은데, 유니코드에는 **한 칸에 안 들어가는 글자**가 있다.
그런 글자는 **두 칸을 이어서** 앉는다. 그런데 `length` 는 **칸을 센다.**

```text
   문자열 "a👍"  — 눈에는 글자 두 개

   칸:   [ 0x0061 ] [ 0xD83D ] [ 0xDC4D ]
           'a'       <--- 👍 하나 --->
   length = 3        ★ 글자는 둘인데 3 이다

   네 가지 자가 서로 다른 답을 낸다:

     s.length          칸(코드 유닛)  -> 3
     [...s].length     글자 번호      -> 2
     Segmenter         사람이 보는 칸 -> 2
     utf8 바이트        저장·전송 크기 -> 5

   ★ "몇 글자인가" 는 질문이 아니다. 어느 자로 재는지를 먼저 정해야 한다.
```

**비유 대응표** — 이 문서는 끝까지 이 대응을 지킨다.

| 비유 | 실체 | 확인하는 법 |
|---|---|---|
| 16비트짜리 칸 | UTF-16 코드 유닛 | `s.length` 가 세는 것 |
| 두 칸을 이어 앉은 글자 | 서로게이트 페어 | `charCodeAt` 이 `0xD800`\~`0xDFFF` 를 준다 |
| 글자마다 붙은 만국 번호 | 코드 포인트 | `codePointAt` · `[...s]` 가 세는 것 |
| 사람이 보는 한 칸 | 자소 클러스터 | `Intl.Segmenter` 가 세는 것 |
| 봉투에 담아 부칠 때의 무게 | UTF-8 바이트 수 | `Buffer.byteLength` · `TextEncoder` |
| 짝을 잃은 반쪽 | 짝 없는 서로게이트 | ★ 예외 없이 문자열 안에 남는다 |
| 같은 글자를 쓰는 두 방법 | 정규화 형태(NFC/NFD) | 눈에 같은데 `===` 가 거짓 |

**똑같은 구조다** — 실무에서 이게 물리는 자리도 하나로 굳어 있다.
「**닉네임 10자 제한**」이 이모지 다섯 개에서 걸리고,
**미리보기 자르기**가 이모지 한가운데를 잘라 **깨진 글자**를 만든다.
둘 다 **예외가 안 나고** 값만 이상해진다 — 이 주제의 값이 전부 거기 있다.

> **코드 유닛(code unit)** — 인코딩이 쓰는 고정 크기 조각. UTF-16 에서는 **16비트** 하나다.
> 예: `"👍".length` 가 `2` 인 것은 코드 유닛이 둘이라는 뜻이다.

> **코드 포인트(code point)** — 유니코드가 글자마다 매긴 번호 하나.
> 예: `"👍".codePointAt(0)` 이 `128077`. 이 번호 하나가 UTF-16 에서는 **두 칸**을 먹는다.

> **자소 클러스터(grapheme cluster)** — 사람이 「한 글자」로 보는 단위.
> 예: 가족 이모지는 코드 포인트가 다섯인데 자소는 하나다.

## 이 주제가 답하려는 질문

1. **`length` 가 세는 것이 무엇인가** — 그리고 다른 세 가지 자와 어디서 갈리는가.
2. **서로게이트 페어 한가운데를 자르면 JS 는 무엇을 하는가** — 터지는가 고치는가 침묵하는가.
3. **「사람이 보는 한 글자」를 물을 수 있는 표준 도구가 있는가** — 있다. 언제부터인가.

## 동작 방식

> 이 절이 본문이다. 그림을 먼저 두고 그 그림을 문장으로 읽는다.

### (1) ★★★ 네 가지 자 — 같은 문자열을 네 번 잰다

**언제 쓰나** — 글자 수 제한·자르기·저장 크기 계산. 전부 이 오해 위에서 틀린다.

```text
   한 문자열, 네 가지 답

   문자열        코드 유닛(length)   코드 포인트([...s])   자소(Segmenter)   utf8 바이트
   ----------------------------------------------------------------------------------
   "A"                  1                   1                  1                1
   "가"                  1                   1                  1                3
   e + U+0301           2                   2                  1                3
   U+00E9               1                   1                  1                2
   "👍"                 2                   1                  1                4
   가족 이모지           8                   5                  1               18
   국기 "KR"            4                   2                  1                8

   ★ 같은 "한 글자" 가 1 · 2 · 4 · 8 칸을 먹는다.
   ★ 네 열이 서로 다른 질문의 답이다. 어느 열이 필요한지를 먼저 정한다.
```

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

```text
===== node20 js01b-04a-code-unit-grid.js (exit=0) =====
[1] 네 가지 자 — 같은 문자열을 네 번 잰다
name            s.length  [...s]  grapheme   utf8
-------------------------------------------------
ascii A                1       1         1      1
hangul GA              1       1         1      3
NFC e-acute            1       1         1      2
NFD e-acute            2       2         1      3
jamo HAN               3       3         1      9
thumbs up              2       1         1      4
thumbs+skin            4       2         1      8
family ZWJ             8       5         1     18
flag KR                4       2         1      8
rainbow flag           6       4         1     14

[2] s.length 가 세고 있는 것 — 코드 유닛을 그대로 펼치면
  ascii A        \u0041
  hangul GA      \uac00
  NFC e-acute    \u00e9
  NFD e-acute    \u0065\u0301
  jamo HAN       \u1112\u1161\u11ab
  thumbs up      \ud83d\udc4d
  thumbs+skin    \ud83d\udc4d\ud83c\udffd
  family ZWJ     \ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc67
  flag KR        \ud83c\uddf0\ud83c\uddf7
  rainbow flag   \ud83c\udff3\ufe0f\u200d\ud83c\udf08

[3] 눈으로 보는 글자 (터미널 폭은 또 다른 이야기다)
  ascii A        A
  hangul GA      가
  NFC e-acute    é
  NFD e-acute    é
  jamo HAN       한
  thumbs up      👍
  thumbs+skin    👍🏽
  family ZWJ     👨‍👩‍👧
  flag KR        🇰🇷
  rainbow flag   🏳️‍🌈
```

그림 해설 (한 단계씩).

- ★★★ **`[1]` 의 네 열이 열 줄에서 전부 다른 조합**을 만든다.
  `A` 는 `1 1 1 1` 로 네 열이 같고, **가족 이모지는 `8 5 1 18`** 로 넷이 전부 다르다.
  ★ **「몇 글자인가」는 질문이 아니다** — 어느 자로 재는지를 먼저 정해야 한다.
- ★★★ **`[2]` 가 `length` 가 세는 것을 눈으로 보여 준다.** 코드 유닛을 `\uXXXX` 로 펼치면
  `\ud83d\udc4d` 처럼 **두 칸이 나란히** 있는 것이 보인다 — `length` 가 2 인 이유가 그림에 있다.
- ★★★ **가족 이모지는 `\ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc67`** 이다.
  사람 셋(각 2칸)과 **ZWJ 둘**(각 1칸)이 합쳐 8칸이다. **코드 포인트로는 5** 다.
- ★★ **같은 `é` 가 1칸일 수도 2칸일 수도 있다** — `\u00e9` 와 `\u0065\u0301` 이 화면에 똑같이 보인다(5번 절).
- ★★ **조합형 한글 `\u1112\u1161\u11ab` 은 3칸**인데 자소로는 1 이고 NFC 를 거치면 `\ud55c` 한 칸이 된다.
  ★ **한글도 이 문제에서 자유롭지 않다.**
- ★★ **국기는 자소가 1 인데 코드 포인트가 2** 다 — 지역 표시 기호 두 개의 조합이다.
- ★ **UTF-8 바이트 수는 또 다른 축**이다. `"가"` 는 코드 유닛 1·바이트 3, `"👍"` 는 코드 유닛 2·바이트 4 다.
  **DB 칼럼 크기를 정할 때 필요한 것은 이 열**이지 `length` 가 아니다.

**비용** — `length` 가 O(1) 이고 인덱싱도 O(1) 이다. 저장 구조가 단순하다.
대신 **그 숫자가 사람이 세는 글자 수와 다르고**, 다른 게 언제인지는 **문자열마다** 다르다.

### (2) 서로게이트 페어 — 코드 포인트 하나가 칸 둘에 앉는 방식

**언제 쓰나** — 이모지·고대 문자·일부 한자를 다루는 자리.

```text
   유니코드 코드 포인트 공간

   0x0000 ........ 0xD7FF | 0xD800 ~ 0xDFFF | 0xE000 ....... 0xFFFF | 0x10000 ....... 0x10FFFF
        BMP — 한 칸에 앉는다    서로게이트 구간      BMP 나머지            BMP 밖 — 두 칸에 앉는다
                                    ^
                                    |  "글자" 가 아니다. 두 칸으로 쪼갤 때
                                       쓰려고 비워 둔 2048 칸이다.

   U+1F44D (👍) 를 두 칸으로 나누는 산수:
      hi = 0xD800 + ((cp - 0x10000) >> 10)      = 0xD83D
      lo = 0xDC00 + ((cp - 0x10000) & 0x3FF)    = 0xDC4D
```

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

```text
===== node20 js01b-04b-surrogate-pair.js (exit=0) =====
[1] 한 글자인데 자리는 둘이다
  s.length            : 2
  charCodeAt(0)       : 55357 U+D83D (high surrogate)
  charCodeAt(1)       : 56397 U+DC4D (low surrogate)
  codePointAt(0)      : 128077 U+1F44D
  codePointAt(1)      : 56397 U+DC4D <- 뒤 조각만 따로 읽힌다

[2] 둘을 합치는 산수 — 명세가 정한 식 그대로
  (hi - 0xD800) * 0x400 + (lo - 0xDC00) + 0x10000
  = (55357 - 55296) * 1024 + (56397 - 56320) + 65536
  = 128077 = U+1F44D
  String.fromCharCode(hi, lo) === s : true
  String.fromCodePoint(0x1F44D) === s : true

[3] 서로게이트 구간은 '글자가 아닌' 자리다
  0xD800 ~ 0xDFFF 는 코드 포인트 공간에서 비워 둔 2048칸
  BMP 밖(0x10000 이상)의 글자는 그 두 칸을 빌려 두 유닛으로 앉는다
  0xFFFF 까지인가 : 1 | 0x10000 부터인가 : 2

[4] charCodeAt 과 codePointAt — 언제 갈리나
  s = "a👍가" | length = 4
  i  charCodeAt   codePointAt  s[i] 를 escape 로
  0  97          97           \u0061
  1  55357       128077       \ud83d
  2  56397       56397        \udc4d
  3  44032       44032        \uac00
  ★ codePointAt 은 '그 자리에서 시작하는 코드 포인트' 를 준다 —
    high 자리에서는 합쳐 읽고, low 자리에서는 그 조각만 준다.
```

그림 해설.

- ★★★ **`charCodeAt` 은 칸을 읽고 `codePointAt` 은 글자를 읽는다.**
  같은 0 번 자리에서 앞엣것은 `55357`(`U+D83D`), 뒤엣것은 `128077`(`U+1F44D`)을 준다.
- ★★★ **`codePointAt(1)` 은 `56397`** 이다 — **뒤 조각만 따로** 나온다.
  `codePointAt` 은 「**그 자리에서 시작하는 코드 포인트**」를 주므로, **low 자리에서는 합쳐 읽을 수가 없다.**
  ★ 그래서 **인덱스를 잘못 짚으면 조용히 반쪽이 나온다.**
- ★★ **합치는 산수가 명세에 그대로 있고** 그 결과가 `128077` 로 맞는다. `String.fromCharCode(hi, lo)` 도 같은 문자열을 만든다.
- ★★ **`0xFFFF` 까지는 1칸, `0x10000` 부터 2칸**이다 — 경계를 실제로 던져 확인했다.
- ★★★ **`[4]` 의 네 줄짜리 표가 이 절의 요약**이다. `"a👍가"` 에서
  `i=1` 에서만 두 함수가 갈리고 나머지 세 자리는 같다 — **갈리는 자리는 high 서로게이트뿐**이다.

**비용** — BMP 안의 글자(한글·한자·라틴 전부)가 **한 칸에 들어가서** 인덱싱이 빠르다.
대신 **BMP 밖의 글자에서 모든 인덱스 계산이 어긋난다** — 그리고 이모지가 전부 거기 있다.

### (3) 쪼개는 여섯 가지 방법 — 무엇을 단위로 삼나

**언제 쓰나** — 문자열을 글자 단위로 돌거나 뒤집을 때.

```text
   같은 "👍" 를 여섯 가지로 쪼개면

   split('')          [\ud83d | \udc4d]     ★ 깨진다 — 코드 유닛 단위
   [...s]             [\ud83d\udc4d]        코드 포인트 단위
   Array.from(s)      [\ud83d\udc4d]        같다
   for...of           [\ud83d\udc4d]        같다
   split(/(?:)/u)     [\ud83d\udc4d]        u 플래그가 있으면 같다
   Segmenter          [\ud83d\udc4d]        자소 단위

   ★ 그런데 "e + U+0301" 에서는 앞의 다섯이 둘로 쪼개고 Segmenter 만 하나로 본다.
     즉 "안 깨지는 것" 에도 두 단계가 있다.
```

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

```text
===== node20 js01b-04c-splitting.js (exit=0) =====
[thumbs up]  s.length = 2
  s.split('')      [\ud83d | \udc4d]
  [...s]           [\ud83d\udc4d]
  Array.from(s)    [\ud83d\udc4d]
  for...of         [\ud83d\udc4d]
  s.split(/(?:)/u) [\ud83d\udc4d]
  Segmenter        [\ud83d\udc4d]

[NFD e-acute]  s.length = 2
  s.split('')      [\u0065 | \u0301]
  [...s]           [\u0065 | \u0301]
  Array.from(s)    [\u0065 | \u0301]
  for...of         [\u0065 | \u0301]
  s.split(/(?:)/u) [\u0065 | \u0301]
  Segmenter        [\u0065\u0301]

[family ZWJ]  s.length = 8
  s.split('')      [\ud83d | \udc68 | \u200d | \ud83d | \udc69 | \u200d | \ud83d | \udc67]
  [...s]           [\ud83d\udc68 | \u200d | \ud83d\udc69 | \u200d | \ud83d\udc67]
  Array.from(s)    [\ud83d\udc68 | \u200d | \ud83d\udc69 | \u200d | \ud83d\udc67]
  for...of         [\ud83d\udc68 | \u200d | \ud83d\udc69 | \u200d | \ud83d\udc67]
  s.split(/(?:)/u) [\ud83d\udc68 | \u200d | \ud83d\udc69 | \u200d | \ud83d\udc67]
  Segmenter        [\ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc67]

[뒤집기 — 이 차이가 눈에 보이는 자리]
  원본                 : a👍b | \u0061\ud83d\udc4d\u0062
  split('').reverse()  : b��a | \u0062\udc4d\ud83d\u0061
  [...t].reverse()     : b👍a | \u0062\ud83d\udc4d\u0061

[인덱스 접근 세 가지]
  t[1]           : \ud83d
  t.charAt(1)    : \ud83d
  t.at(1)        : \ud83d
  [...t][1]      : \ud83d\udc4d  <- 이것만 '글자' 다
```

그림 해설.

- ★★★ **`split('')` 만 서로게이트 페어를 깨뜨린다.** 나머지 다섯은 코드 포인트를 지킨다.
  ★ **이터레이션 프로토콜(`[...s]`·`for...of`·`Array.from`)이 코드 포인트 단위**라는 것이 명세의 약속이다(19번 주제).
- ★★★ **「안 깨진다」에 두 단계가 있다.**
  NFD 형태(`e` + `U+0301`)에서는 **다섯 방법이 전부 둘로 쪼개고 `Segmenter` 만 하나로 본다.**
  가족 이모지에서는 **`[...s]` 가 다섯 조각**을 내고 `Segmenter` 만 하나다.
  ★ **`[...s]` 를 쓰면 「글자」가 된다는 말은 절반만 맞다.**
- ★★★ **뒤집기에서 그 차이가 눈에 보인다.** `"a👍b".split("").reverse().join("")` 은
  `\u0062\udc4d\ud83d\u0061` — **low 가 앞, high 가 뒤로 와서** 화면에 깨진 글자가 찍힌다.
  `[...t].reverse()` 는 멀쩡하다.
- ★★ **인덱스 접근 셋(`t[1]`·`charAt(1)`·`at(1)`)이 전부 반쪽**을 준다.
  **`[...t][1]` 만 글자**다 — 다만 그것은 **매번 전체를 훑으므로 O(n)** 이다.
- ★ `split(/(?:)/u)` 는 **`u` 플래그**가 있어야 코드 포인트 단위가 된다. 플래그 하나가 단위를 바꾼다.

**비용** — 이터레이션 프로토콜을 쓰면 코드 포인트가 지켜지고 문법도 짧다.
대신 **O(n) 이고**, 자소까지는 안 간다 — 거기서부터는 `Intl.Segmenter` 다.

### (4) ★★★ 페어 한가운데를 자르면 — JS 는 터지지도 고치지도 않는다

**언제 쓰나** — 미리보기 자르기·길이 제한·버퍼 경계에서 잘린 문자열을 받을 때.

```text
   같은 상황에서 세 언어가 다른 답을 한다

   Rust   s[0..3] 가 문자 경계가 아니면   -> ★ 패닉 (프로그램이 죽는다)
   Go     문자열 슬라이스는 바이트 단위     -> ★ 침묵. 깨진 바이트가 남고
                                              range 로 돌면 U+FFFD 가 나온다
   JS     s.slice(0, 3) 이 페어를 가르면   -> ★ 침묵. "짝 없는 서로게이트" 가
                                              문자열 안에 값으로 남는다

   ★ JS 가 가장 늦게 터진다 — 자를 때가 아니라 "밖으로 내보낼 때" 다.
     그리고 내보내는 길마다 답이 다르다.
```

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

```text
===== node20 js01b-04d-cut-through-pair.js (exit=0) =====
[1] 자르는 자리는 그냥 받아들여진다
  s          = "ab👍cd" | length = 6
  s.slice(0,3)  -> \u0061\u0062\ud83d | length 3
  s.slice(3)    -> \udc4d\u0063\u0064 | length 3
  s.substring(0,3) -> \u0061\u0062\ud83d
  s.substr(2,1)    -> \ud83d
  ★ 예외도 경고도 없다. 잘린 반쪽이 그대로 문자열 안에 남는다.

[2] 그 반쪽은 '값' 으로는 아무 문제가 없다
  half              = \ud83d
  half.length       = 1
  typeof half       = string
  half === half     = true
  half.charCodeAt(0)= 55357
  half + 'x'        = \ud83d\u0078
  half 을 그대로 찍으면: �

[3] 밖으로 내보낼 때에야 드러난다 — 경로마다 대답이 다르다
  JSON.stringify(half)           -> "\ud83d"
  encodeURIComponent(half)       -> URIError: URI malformed
  Buffer.from(half,'utf8')       -> ef bf bd
  Buffer utf8 roundtrip ===      -> false
  Buffer.from(half,'utf16le')    -> 3d d8
  Buffer utf16le roundtrip ===   -> true
  new TextEncoder().encode       -> ef bf bd
  half.normalize('NFC')          -> \ud83d
  JSON.parse(JSON.stringify) === -> true

[4] 잘 잘라내는 법
  [...s].slice(0,3).join('') -> \u0061\u0062\ud83d\udc4d
  Segmenter 로 3자소         -> \u0061\u0062\ud83d\udc4d
```

그림 해설.

- ★★★ **자르는 자리에서는 아무 일도 안 난다.** `slice`·`substring`·`substr` 넷이 전부 **예외도 경고도 없이**
  반쪽을 돌려준다. `length` 도 `1` 이고 `typeof` 도 `"string"` 이다.
  ★ **값으로서는 완전히 정상**이다 — `===` 로 자기 자신과 같고 이어붙이기도 된다.
- ★★★ **터지는 것은 「밖으로 내보낼 때」이고 길마다 답이 다르다** — 이 절의 표가 그것이다.

  | 나가는 길 | 짝 없는 서로게이트에 무엇을 하나 |
  |---|---|
  | `JSON.stringify` | **이스케이프해서 보존**한다(`"\ud83d"`) — ES2019 의 well-formed JSON.stringify |
  | `encodeURIComponent` | ★ **`URIError: URI malformed`** — 유일하게 터지는 길 |
  | UTF-8 인코딩(`Buffer`·`TextEncoder`) | ★ **조용히 `U+FFFD` 로 바꾼다**(`ef bf bd`) — **왕복이 깨진다** |
  | UTF-16LE 인코딩 | **그대로 통과**하고 **왕복이 된다**(`3d d8`) |
  | `normalize("NFC")` | **그대로 통과**한다 |

- ★★★ **UTF-8 로 나가는 순간 되돌릴 수 없다.** `Buffer.from(half, "utf8").toString("utf8") === half` 가 **거짓**이다.
  ★★ **이것이 이 주제에서 가장 조용한 사고**다 — 파일에 쓰고 나면 원래 값을 복구할 방법이 없다.
- ★★ **`JSON` 왕복은 살아난다** — `JSON.parse(JSON.stringify(half)) === half` 가 참이다.
  ★ ES2019 전에는 `JSON.stringify` 가 **깨진 UTF-8 로 나가** 왕복이 안 됐다. **판이 고친 자리**다.
- ★★ **잘 자르는 법은 코드 포인트나 자소 단위로 세는 것**이다 —
  `[...s].slice(0,3).join('')` 이 `\u0061\u0062\ud83d\udc4d` 로 **이모지를 통째로** 가져온다.

**비용** — 자르기가 O(1) 이고 어떤 인덱스에도 안 터진다.
대신 **깨진 값이 문자열 안에 살아서 돌아다니고**, 그 사고가 **저 멀리 출력 자리에서** 드러난다.

### (5) 정규화 — 눈에 같은데 `===` 가 다르다고 한다

**언제 쓰나** — 사용자 입력·파일 이름·검색어를 **비교하거나 저장하기 직전**.

```text
        NFD (풀어 쓴 것)              NFC (합쳐 쓴 것)
          e + U+0301                     U+00E9
          [2 칸]                         [1 칸]
             \                            /
              \      normalize           /
               +------------------------+
                      같아진다

   ★ normalize 를 안 거치면 === · includes · Set · Map 키가 전부 둘을 다른 것으로 본다.
   ★ 그런데 localeCompare 는 0 을 돌려준다 — 규칙이 다른 층이다.
```

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

```text
===== node20 js01b-04e-normalize.js (exit=0) =====
[1] === 는 정규화를 전혀 보지 않는다
  두 문자열       : é é  <- 화면에는 같아 보인다
  esc             : \u00e9 | \u0065\u0301
  length          : 1 2
  nfc === nfd     : false
  nfc == nfd      : false
  Object.is       : false
  [nfc].includes  : false
  new Set 크기     : 2
  Map 조회         : undefined
  localeCompare   : 0  <- 0 이면 로캘 기준으로는 같다고 본다

[2] normalize 를 거치면 같아진다
  nfd.normalize('NFC') === nfc : true
  nfc.normalize('NFD') === nfd : true
  normalize() 기본값은 NFC 인가 : true

[3] 한글은 이 문제가 더 크다 — 조합형과 완성형
  조합형 '한'  : 한 | length 3 | \u1112\u1161\u11ab
  완성형 '한'  : 한 | length 1 | \ud55c
  === 인가     : false
  NFC 뒤       : true | length 1
  '한글'.normalize('NFD').length : 6

[4] K 가 붙으면 '같은 글자로 모으는' 게 아니라 '다른 글자로 바꾼다'
code unit    NFC len  NFD len  NFKC len   원본 -> NFKC
---------------------------------------------------------
\u00bd             1        1         3   "½" -> "1⁄2"
\u2163             1        1         2   "Ⅳ" -> "IV"
\ufb01             1        1         2   "ﬁ" -> "fi"
\u2460             1        1         1   "①" -> "1"
\u3273             1        1         1   "㉳" -> "바"
\u00b2             1        1         1   "²" -> "2"
\u212b             1        2         1   "Å" -> "Å"
  ★ 마지막 줄은 K 가 아닌데도 글자가 바뀐다 — NFC 가 이미 바꾼다:
     Å -> NFC -> \u00c5  (ANGSTROM SIGN 이 A WITH RING 으로)

[5] normalize 가 못 고치는 것
  family.normalize('NFC').length : 8 <- ZWJ 는 그대로다
  'a'.normalize('NFX') : RangeError: The normalization form should be one of NFC, NFD, NFKC, NFKD.
```

그림 해설.

- ★★★ **`===` 는 정규화를 전혀 보지 않는다.** 코드 유닛 열을 그대로 견준다.
  그래서 **`Set` 크기가 2 이고 `Map` 이 못 찾는다.**
- ★★★ **`localeCompare` 만 `0` 을 준다.** 같은 두 값에 **`===` 는 거짓, `localeCompare` 는 0** 이다 —
  ★ **어느 층에서 묻느냐에 따라 답이 갈린다.** 비교를 `===` 로 하면서 정렬을 `localeCompare` 로 하면 **둘이 어긋난다.**
- ★★★ **한글이 이 문제에 더 크게 걸린다.** 조합형 `\u1112\u1161\u11ab` 은 **3칸**이고 완성형 `\ud55c` 은 **1칸**인데
  화면에 똑같이 보인다. `"한글".normalize("NFD").length` 가 **6** 이다.
  ★ **macOS 가 만든 파일 이름이 NFD 에 가깝다** — 그 경계에서 사고가 난다.
- ★★ **`NFKC` 는 「모으는」 것이 아니라 「갈아치우는」 것**이다.
  `U+00BD`(½)가 `1⁄2` 세 글자가 되고 `U+2163`(Ⅳ)가 `IV` 두 글자가 된다 — **길이가 늘어난다.**
  검색 색인에는 쓸 만하지만 **원본 보존에는 쓰면 안 된다.**
- ★★★ **`K` 가 아닌데도 글자가 바뀌는 자리가 있다** — `U+212B`(ANGSTROM SIGN)는
  **NFC 만 거쳐도 `U+00C5`** 가 된다. ★ 「표준 동치는 글자를 안 바꾼다」는 **틀린 직관**이다.
- ★ **`normalize` 는 ZWJ 를 못 고친다.** 가족 이모지의 길이가 그대로 8 이다 — 정규화의 영역이 아니다.
- ★ 없는 형태를 주면 `RangeError` 다 — 네 가지로 닫혀 있다.

**비용** — 한 줄로 두 표현을 한 형태로 모을 수 있다.
대신 **O(n) 이고 새 문자열을 만들며**, 어느 형태를 정본으로 삼을지 **팀이 정해 놓아야** 한다.

### (6) `Intl.Segmenter` — 「사람이 보는 한 칸」을 묻는 표준 도구

**언제 쓰나** — 닉네임 길이 제한·미리보기 자르기·커서 이동.

```js
// js01b-04f-segmenter.js
// Intl.Segmenter — '사람이 세는 한 칸' 을 물을 수 있는 유일한 표준 도구.
const esc = (s) => Array.from({ length: s.length }, (_, i) =>
  "\\u" + s.charCodeAt(i).toString(16).padStart(4, "0")).join("");

console.log("[1] 있는가부터 던져서 확인한다");
console.log("  typeof Intl.Segmenter :", typeof Intl.Segmenter);
console.log("  supportedLocalesOf    :", JSON.stringify(Intl.Segmenter.supportedLocalesOf(["ko", "en", "zz"])));
const seg = new Intl.Segmenter("ko", { granularity: "grapheme" });
console.log("  resolvedOptions       :", JSON.stringify(seg.resolvedOptions()));

console.log("");
console.log("[2] 자소 단위로 쪼갠 결과");
const SAMPLES = [
  ["family ZWJ",   "👨\u200d👩\u200d👧"],
  ["flag KR+JP",   "🇰🇷🇯🇵"],
  ["NFD e-acute",  "e\u0301"],
  ["jamo HAN",     "\u1112\u1161\u11ab"],
  ["thumbs+skin",  "👍\ud83c\udffd"],
  ["rainbow flag", "🏳\ufe0f\u200d🌈"],
  ["GA + acute",    "가\u0301"],
];
console.log("name".padEnd(15) + "length".padStart(8) + "[...s]".padStart(8) + "grapheme".padStart(10));
console.log("-".repeat(15 + 8 + 8 + 10));
for (const [n, s] of SAMPLES)
  console.log(n.padEnd(15) + String(s.length).padStart(8) +
    String([...s].length).padStart(8) + String([...seg.segment(s)].length).padStart(10));

console.log("");
console.log("[3] 자소 하나하나를 꺼내 보면");
for (const [n, s] of SAMPLES.slice(0, 2)) {
  console.log("  " + n);
  for (const piece of seg.segment(s))
    console.log("    index " + String(piece.index).padEnd(3) + esc(piece.segment));
}

console.log("");
console.log("[4] granularity 를 바꾸면 다른 질문이 된다");
const text = "Hello, 세계! 반갑다 👋";
for (const g of ["grapheme", "word", "sentence"]) {
  const parts = [...new Intl.Segmenter("ko", { granularity: g }).segment(text)].map((x) => x.segment);
  console.log("  " + g.padEnd(10) + parts.length + "조각  " + JSON.stringify(parts.slice(0, 6)) + (parts.length > 6 ? " ..." : ""));
}

console.log("");
console.log("[5] 그래도 Segmenter 가 답하지 못하는 질문 — 터미널 폭");
console.log("  '가나'.length       :", "가나".length, " <- 코드 유닛");
console.log("  자소 수             :", [...seg.segment("가나")].length);
console.log("  '가나'.padEnd(4)    :", JSON.stringify("가나".padEnd(4)), "| length", "가나".padEnd(4).length);
console.log("  ★ 표준 JS 에는 '화면에서 몇 칸인가' 를 묻는 API 가 없다.");
console.log("    padEnd 는 코드 유닛을 세므로 한글·이모지 표를 정렬하는 데 쓸 수 없다.");
console.log("    이 문서는 화면 폭을 재지 않았다 — 잴 방법이 표준에 없기 때문이다.");
```

```text
===== node20 js01b-04f-segmenter.js (exit=0) =====
[1] 있는가부터 던져서 확인한다
  typeof Intl.Segmenter : function
  supportedLocalesOf    : ["ko","en"]
  resolvedOptions       : {"locale":"ko","granularity":"grapheme"}

[2] 자소 단위로 쪼갠 결과
name             length  [...s]  grapheme
-----------------------------------------
family ZWJ            8       5         1
flag KR+JP            8       4         2
NFD e-acute           2       2         1
jamo HAN              3       3         1
thumbs+skin           4       2         1
rainbow flag          6       4         1
GA + acute            2       2         1

[3] 자소 하나하나를 꺼내 보면
  family ZWJ
    index 0  \ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc67
  flag KR+JP
    index 0  \ud83c\uddf0\ud83c\uddf7
    index 4  \ud83c\uddef\ud83c\uddf5

[4] granularity 를 바꾸면 다른 질문이 된다
  grapheme  16조각  ["H","e","l","l","o",","] ...
  word      9조각  ["Hello",","," ","세계","!"," "] ...
  sentence  2조각  ["Hello, 세계! ","반갑다 👋"]

[5] 그래도 Segmenter 가 답하지 못하는 질문 — 터미널 폭
  '가나'.length       : 2  <- 코드 유닛
  자소 수             : 2
  '가나'.padEnd(4)    : "가나  " | length 4
  ★ 표준 JS 에는 '화면에서 몇 칸인가' 를 묻는 API 가 없다.
    padEnd 는 코드 유닛을 세므로 한글·이모지 표를 정렬하는 데 쓸 수 없다.
    이 문서는 화면 폭을 재지 않았다 — 잴 방법이 표준에 없기 때문이다.
```

그림 해설.

- ★★★ **「있는가」부터 던져서 확인했다.** `typeof Intl.Segmenter` 가 `function` 이고
  `resolvedOptions` 가 `{"locale":"ko","granularity":"grapheme"}` 을 준다 — **문서를 읽은 게 아니라 물어본 것**이다.
- ★★★ **일곱 문자열 중 자소가 1 이 아닌 것은 국기 두 개짜리 하나뿐**이다.
  `length` 가 2\~8 로 흩어져 있는데 **자소는 전부 1** 이다 — ★ **이 열이 「사람이 세는 글자」에 가장 가깝다.**
- ★★ **`supportedLocalesOf(["ko","en","zz"])` 가 `["ko","en"]`** 을 준다 — 없는 로캘은 **조용히 빠진다.**
- ★★ **`granularity` 를 바꾸면 다른 질문**이 된다. 같은 문장이 자소 16 · 단어 9 · 문장 2 조각으로 갈린다.
  ★ **단어 분할이 공백 분할과 다르다** — `"Hello"`·`","`·`" "`·`"세계"` 처럼 **구두점과 공백이 따로** 나온다.
- ★★★ **그래도 못 답하는 질문이 하나 남는다 —** 「터미널에서 몇 칸인가」.
  `"가나".padEnd(4)` 는 **코드 유닛을 세어** 4 를 만들지만 화면에서는 더 넓다.
  ★★ **표준 JS 에 그것을 재는 API 가 없어서 이 문서는 그 수치를 재지 않았다** — 「안 돌려 본 것」이 아니라 「**잴 방법이 없는 것**」이다.
- ★★ **자소 수는 ICU 판에 달렸다.** 이 문서의 일곱 문자열에서는 v18(ICU 74.2 · 유니코드 15.1)과
  v20(ICU 77.1 · 유니코드 16.0)이 **한 글자도 안 갈렸지만**, 그것은 관찰이지 보장이 아니다.

**비용** — 표준만으로 자소를 셀 수 있고 로캘까지 고려된다.
대신 **ICU 데이터에 기대므로 판마다 답이 달라질 수 있고**, `length` 보다 훨씬 비싸다.

### (7) ★★★ 두 판이 갈린 자리 — `isWellFormed`/`toWellFormed`(ES2024)

**언제 쓰나** — 짝 없는 서로게이트를 **밖으로 내보내기 전에** 막고 싶을 때.

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

**node 20.19.6 — 있다**

```text
===== node20 js01b-04g-well-formed.js (exit=0) =====
node v20.19.6 | v8 11.3.244.8-node.33 | icu 77.1 | unicode 16.0

  typeof String.prototype.isWellFormed : function
  typeof String.prototype.toWellFormed : function

  pair.isWellFormed()      -> true
  lone.isWellFormed()      -> false
  ascii.isWellFormed()     -> true
  lone.toWellFormed()      -> \ufffd
  pair.toWellFormed()      -> \ud83d\udc4d

  ★ 이 메서드가 없는 판에서 같은 일을 손으로 하려면:
    직접 짠 검사 — lone 이 깨졌나 : true
    직접 짠 검사 — pair 가 깨졌나 : false
    JSON.stringify 로도 드러난다  : "\ud83d"
    Buffer 왕복으로도 드러난다     : false
```

**node 18.19.1 — 없다**

```text
===== node18 js01b-04g-well-formed.js (exit=0) =====
node v18.19.1 | v8 10.2.154.26-node.28 | icu 74.2 | unicode 15.1

  typeof String.prototype.isWellFormed : undefined
  typeof String.prototype.toWellFormed : undefined

  pair.isWellFormed()      -> TypeError: "👍".isWellFormed is not a function
  lone.isWellFormed()      -> TypeError: lone.isWellFormed is not a function
  ascii.isWellFormed()     -> TypeError: "a".isWellFormed is not a function
  lone.toWellFormed()      -> TypeError: lone.toWellFormed is not a function
  pair.toWellFormed()      -> TypeError: "👍".toWellFormed is not a function

  ★ 이 메서드가 없는 판에서 같은 일을 손으로 하려면:
    직접 짠 검사 — lone 이 깨졌나 : true
    직접 짠 검사 — pair 가 깨졌나 : false
    JSON.stringify 로도 드러난다  : "\ud83d"
    Buffer 왕복으로도 드러난다     : false
```

그림 해설.

- ★★★ **이 배치 네 주제에서 두 판이 갈린 유일한 자리**다. v20 은 `function`, v18 은 `undefined` 다.
  ★ **v18 에서는 다섯 줄이 전부 `TypeError: … is not a function`** 으로 바뀐다.
  「이 판에 없다」를 **문서에서 읽은 게 아니라 던져서 확인**했다.
- ★★★ **`toWellFormed()` 는 짝 없는 서로게이트를 `U+FFFD` 로 바꾼다** — 4번 절의 UTF-8 인코딩이 하는 일과 같다.
  **차이는** 「내가 언제 하느냐」다. 미리 하면 **어디서 깨졌는지 알 수 있고**, 안 하면 파일에 쓰는 순간 조용히 바뀐다.
- ★★ **없는 판에서도 같은 일을 할 수 있다** — 짝 없는 서로게이트를 찾는 정규식이나
  `JSON.stringify` / `Buffer` 왕복으로 드러난다. 블록의 마지막 네 줄이 **두 판에서 똑같이** 나온다.
- ★ **v8 과 ICU 판도 같이 찍어** 두었다 — 이 줄이 **두 출력을 가르는 유일한 근거**다.

### (8) 브라우저에서 — 같은 V8 인데 판이 다르다

**언제 쓰나** — 「Node 18 에 없으니 브라우저에도 없겠지」를 물을 때.

```text
<!doctype html><meta charset="utf-8"><title>UTF-16 in the browser</title>
<p>이 페이지는 값을 찍기만 한다.</p>
<pre id="out"></pre>
<script src="js01b-04h-browser.js"></script>
```

```js
// js01b-04h-browser.js
const esc = (s) => Array.from({ length: s.length }, (_, i) =>
  "\\u" + s.charCodeAt(i).toString(16).padStart(4, "0")).join("");
const lone = "\ud83d\udc4d".slice(0, 1);
const seg = new Intl.Segmenter("ko", { granularity: "grapheme" });
const family = "\ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc67";
const rows = [
  ["엔진",                        navigator.userAgent.replace(/^.*(Chrome\/[\d.]+).*$/, "$1")],
  ["family.length",               family.length],
  ["[...family].length",          [...family].length],
  ["family 자소 수",               [...seg.segment(family)].length],
  ["typeof ''.isWellFormed",      typeof "".isWellFormed],
  ["lone.isWellFormed()",         lone.isWellFormed()],
  ["esc(lone.toWellFormed())",    esc(lone.toWellFormed())],
  ["esc(lone)",                   esc(lone)],
  ["JSON.stringify(lone)",        JSON.stringify(lone)],
  ["encodeURIComponent(lone)",    (() => { try { return encodeURIComponent(lone); } catch (e) { return e.constructor.name + ": " + e.message; } })()],
  ["new TextEncoder().encode(lone)", [...new TextEncoder().encode(lone)].map((b) => b.toString(16)).join(" ")],
];
document.getElementById("out").textContent =
  rows.map(([k, v]) => k.padEnd(34) + " : " + String(v)).join("\n");
```

```text
===== google-chrome --headless --disable-gpu --no-sandbox --dump-dom js01b-04h-browser.html 2>/dev/null | sed -n '/^<pre id="out">/,/<\/pre>/p' (exit=0) =====
<pre id="out">엔진                                 : Chrome/151.0.0.0
family.length                      : 8
[...family].length                 : 5
family 자소 수                        : 1
typeof ''.isWellFormed             : function
lone.isWellFormed()                : false
esc(lone.toWellFormed())           : \ufffd
esc(lone)                          : \ud83d
JSON.stringify(lone)               : "\ud83d"
encodeURIComponent(lone)           : URIError: URI malformed
new TextEncoder().encode(lone)     : ef bf bd</pre>
```

그림 해설.

- ★★★ **Chrome 151 에는 `isWellFormed` 가 있다.** Node 18 에는 없다 —
  ★ **엔진은 같은 V8 이지만 판이 달라서** 기능 유무가 갈린다.
  「V8 이면 다 된다」는 틀리고 「**어느 V8 판인가**」를 물어야 한다.
- ★★ **자소 수·코드 유닛 수·바이트 수가 Node 와 한 글자도 안 달랐다.**
- ★★ **`encodeURIComponent` 가 브라우저에서도 `URIError`** 다. `TextEncoder` 도 `ef bf bd` 로 같다 —
  **호스트가 달라도 문자열 규칙은 같다.**
- ★ 이 페이지는 **값을 찍기만 하고 아무것도 바꾸지 않는다.** 호스트 페이지는 네 줄이고 검사는 옆의 `.js` 가 한다.

## 문법 — 형태와 규칙

**형태 — 이것이 전부다.** 출력이 없는 파일이라 `--check` 로 문법만 확인했다(「진단 0줄」도 블록으로 싣는다).

```js
// js01b-04x-forms.js
// 형태만 모아 둔 파일 — 출력은 없다. `node --check` 로 문법만 확인한다.
const s = "ab";

s.length;                     // ★ UTF-16 코드 유닛의 수. 글자 수가 아니다
s[0];                         // 코드 유닛 하나
s.charAt(0);                  // 같다
s.at(-1);                     // 뒤에서 세는 것만 다르다 (ES2022)
s.charCodeAt(0);              // 그 자리의 코드 유닛 (0 ~ 65535)
s.codePointAt(0);             // ★ 그 자리에서 시작하는 코드 포인트 (합쳐 읽는다)

[...s];                       // ★ 코드 포인트 단위로 쪼갠다
Array.from(s);                // 같다
s.split("");                  // ★ 코드 유닛 단위 — 서로게이트 페어가 깨진다

String.fromCharCode(0x41);    // 코드 유닛으로 만든다
String.fromCodePoint(0x1f44d); // 코드 포인트로 만든다 — 페어가 필요하면 알아서 둘이 된다

s.normalize("NFC");           // 합쳐 쓴 형태로. 기본값도 NFC
s.normalize("NFKC");          // ★ 호환 동치 — 글자가 바뀐다

new Intl.Segmenter("ko", { granularity: "grapheme" }).segment(s);  // 자소 단위

// ES2024 — Node 18 에는 없다
// s.isWellFormed();          // 짝 없는 서로게이트가 있나
// s.toWellFormed();          // 그것을 U+FFFD 로 바꾼 새 문자열
```

```text
===== node20 --check js01b-04x-forms.js (exit=0) =====

```

규칙은 아홉이다.

1. **문자열은 UTF-16 코드 유닛의 열**이다. `length` 가 세는 것은 **칸**이지 글자가 아니다.
2. **BMP 밖의 코드 포인트는 두 칸에 앉는다**(서로게이트 페어). 이모지가 전부 거기 있다.
3. **인덱스 접근(`[i]`·`charAt`·`at`)과 `split('')` 은 칸 단위**다 — 페어를 깨뜨린다.
4. **이터레이션(`[...s]`·`for...of`·`Array.from`)은 코드 포인트 단위**다 — 페어를 지킨다.
5. **`charCodeAt` 은 칸을, `codePointAt` 은 그 자리에서 시작하는 코드 포인트를** 준다.
6. **페어를 가르는 자르기는 예외를 안 던진다.** 짝 없는 서로게이트가 값으로 남는다.
7. **밖으로 나갈 때 길마다 답이 다르다** — `JSON` 은 보존, `encodeURIComponent` 는 `URIError`, **UTF-8 은 조용히 `U+FFFD`**.
8. **`===` 는 정규화를 안 본다.** 눈에 같은 두 문자열이 다를 수 있다. `normalize` 는 네 형태다.
9. **자소는 `Intl.Segmenter`** 로만 셀 수 있고, **터미널 폭을 재는 표준 API 는 없다.**

## 어디서 틀리나

### (1) ★★★ `length` 로 글자 수를 제한한다

「닉네임 10자」가 **이모지 다섯 개**에서 걸린다. 가족 이모지 하나가 **8** 이다.
`[...s].length` 나 `Intl.Segmenter` 를 쓴다 — **어느 쪽이 맞는지는 「글자」의 정의에 달렸다.**

### (2) ★★★ `slice` 로 미리보기를 자른다

페어 한가운데를 자르면 **예외 없이** 반쪽이 남는다.
그 값이 **UTF-8 로 나가는 순간 `U+FFFD` 가 되고 되돌릴 수 없다.**
`[...s].slice(0, n).join('')` 이나 `Segmenter` 를 쓴다.

### (3) ★★ `split('').reverse().join('')` 로 뒤집는다

이모지가 **깨진다.** `[...s].reverse().join('')` 이 코드 포인트는 지키지만
**NFD 결합 문자와 ZWJ 는 여전히 어긋난다** — 자소 단위로 뒤집으려면 `Segmenter` 가 필요하다.

### (4) ★★ `[...s]` 를 쓰면 「글자」가 된다고 믿는다

**절반만 맞다.** NFD 형태(`e` + `U+0301`)는 둘로, 가족 이모지는 다섯으로 쪼개진다.
**코드 포인트와 자소는 다른 단위**다.

### (5) ★★ `charCodeAt` 으로 이모지를 읽는다

`0xD83D` 같은 **반쪽 번호**가 나온다. `codePointAt` 을 쓴다 —
다만 **low 자리에서 부르면 그것도 반쪽**을 준다.

### (6) ★★★ 정규화를 안 하고 비교·저장한다

macOS 가 만든 파일 이름은 NFD 에 가깝고 웹·리눅스는 NFC 다.
**`Set` 이 중복을 못 걸러내고 `Map` 이 못 찾는다.** 경계마다 한 형태로 모은다.

### (7) ★★ `NFKC` 를 「정규화」로 뭉뚱그린다

**글자가 바뀐다.** `Ⅳ` 가 `IV` 두 글자가 된다. 원본 보존에는 쓰면 안 된다.
★ 반대로 **`NFC` 도 글자를 바꾸는 자리가 있다**(`U+212B` → `U+00C5`).

### (8) ★★ `padEnd` 로 표를 정렬한다

**코드 유닛을 센다.** 한글·이모지가 섞이면 화면에서 어긋난다.
표준 JS 에는 화면 폭을 재는 API 가 없다.

### (9) ★ UTF-8 바이트 수를 `length` 로 계산한다

`"가"` 는 `length` 가 1 이고 UTF-8 로는 3바이트다.
DB 칼럼 크기에 필요한 것은 `Buffer.byteLength` 나 `TextEncoder().encode().length` 다.

### (10) ★★ 「Node 18 에 없으니 브라우저에도 없겠지」로 넘긴다

**Chrome 151 에는 `isWellFormed` 가 있다.** 같은 V8 이라도 **판이 다르다.**
기능 유무는 **던져서 확인**한다.

## 구현 세부사항 대 언어 보장

세 층으로 가른다. ★★ **이 주제는 「명세 보장」이 두껍고 「데이터에 달린 것」이 하나 얇게 있다** — 자소 분할이 그것이다.

| 층 | 무엇인가 | 어떻게 확인했나 |
|---|---|---|
| **명세(ECMA-262 / 402) 보장** | 어느 엔진에서도 같아야 하는 것 | 기준 소스 + 실행으로 재확인 |
| **엔진(V8) · 판** | 판마다 갈리는 것 | 두 판 대조 + Chrome 151 |
| **ICU 데이터에 달린 것** | 유니코드 판이 바뀌면 달라질 수 있는 것 | 「관찰」로 명기 |

### 명세 보장

| 사실 | 어떻게 확인했나 |
|---|---|
| 문자열은 **UTF-16 코드 유닛의 열**이고 `length` 가 그 수다 | 격자의 첫 열 |
| **BMP 밖은 두 칸**에 앉고 그 산수가 정해져 있다 | 합치는 식을 계산해 `codePointAt` 과 대조 |
| **인덱스·`split('')` 은 칸 단위, 이터레이션은 코드 포인트 단위** | 여섯 방법을 같은 문자열에 던짐 |
| `codePointAt` 이 **low 자리에서는 그 조각만** 준다 | 네 줄짜리 표 |
| **페어를 가르는 자르기가 예외를 안 던진다** | `slice`·`substring`·`substr` 넷 |
| **`JSON.stringify` 가 짝 없는 서로게이트를 이스케이프**한다(ES2019) | 왕복이 참 |
| **`encodeURIComponent` 는 `URIError`** | 실행 |
| **`===` 는 정규화를 안 본다** · `normalize` 는 네 형태 | `Set`·`Map` 으로 확인 |
| **`NFKC` 가 길이를 바꾼다** · **`NFC` 도 `U+212B` 를 바꾼다** | 일곱 줄 표 |
| `normalize` 에 없는 형태를 주면 **`RangeError`** | 실행 |
| **`isWellFormed`/`toWellFormed` 의 동작**(ES2024) | v20 에서 실행 |

### 엔진(V8) · 판

| 사실 | 어떻게 확인했나 |
|---|---|
| **v18 에는 `isWellFormed` 가 없고 v20 에는 있다** | 두 판의 출력을 둘 다 실음 |
| **Chrome 151 에는 있다** — 같은 V8 인데 판이 다르다 | 브라우저 블록 |
| 나머지 여섯 스크립트는 **두 판에서 한 글자도 같았다** | `js01b-vdiff.sh 04` |
| UTF-8 인코딩이 짝 없는 서로게이트를 `U+FFFD` 로 바꾸는 것 | ★ `Buffer` 는 Node 의 API 이지만 **`TextEncoder` 도 같은 답**을 냈다 |

### ICU 데이터에 달린 것

| 관찰 | 어디가 흔들리나 |
|---|---|
| **`Intl.Segmenter` 의 자소 수** | ICU 판·유니코드 판에 달렸다. v18 은 74.2/15.1, v20 은 77.1/16.0 인데 **이 일곱 문자열에서는 안 갈렸다** |
| `supportedLocalesOf` 가 돌려주는 목록 | 빌드에 들어간 로캘 데이터에 달렸다 |
| `localeCompare` 가 `0` 을 주는 것 | 로캘 비교 규칙과 ICU 판에 달렸다 |
| 예외 **문구** | 종류는 명세, 문구는 V8 의 것이다 |

### 그래서 이렇게 적으면 틀린다

- ✗ 「`length` 는 글자 수다」
  ○ **UTF-16 코드 유닛의 수**다. 가족 이모지 한 칸이 8 이다.
- ✗ 「`[...s]` 를 쓰면 글자 단위가 된다」
  ○ **코드 포인트 단위**다. NFD 형태(`e` + `U+0301`)는 둘, 가족 이모지는 다섯으로 쪼개진다.
- ✗ 「이모지를 자르면 에러가 난다」
  ○ **아무 일도 안 난다.** 반쪽이 값으로 남고, **출력 자리에서** 드러난다.
- ✗ 「깨진 문자열은 UTF-8 로 쓰면 그대로 남는다」
  ○ **`U+FFFD` 로 바뀌고 되돌릴 수 없다.** UTF-16LE 로는 왕복한다.
- ✗ 「정규화는 글자를 안 바꾼다」
  ○ `NFKC` 는 확실히 바꾸고, **`NFC` 도 `U+212B` 같은 자리에서 바꾼다.**
- ✗ 「`Intl.Segmenter` 의 답은 보장이다」
  ○ **ICU 데이터에 달렸다.** 두 판에서 같았다는 것은 관찰이다.
- ✗ 「한글은 이 문제와 상관없다」
  ○ **조합형 한글은 3칸**이고 `"한글".normalize("NFD").length` 가 6 이다.
- ✗ 「Node 18 에 없으면 그 판의 V8 에는 다 없다」
  ○ **Chrome 151 에는 있다.** 같은 엔진이라도 판을 물어야 한다.

**판정 기준 한 줄**: 어떤 코드가 **`length` 나 정수 인덱스로 문자열을 자르고 있으면** 그 자리는 이모지를 넣어 봐야 하는 자리다.

## 언제 쓰고 언제 안 쓰나

| 쓰는 것 | 상황 |
|---|---|
| `s.length` | **저장 칸 수**가 필요할 때(버퍼 크기·UTF-16 기준 제한) |
| `[...s].length` · `for...of` | **코드 포인트** 단위로 돌 때 |
| `Intl.Segmenter` | **사람이 세는 글자**가 필요할 때 — 닉네임 제한·자르기 |
| `codePointAt` | 글자의 **번호**가 필요할 때 |
| `String.fromCodePoint` | 번호로 글자를 만들 때. `fromCharCode` 는 칸 단위라 페어를 직접 넣어야 한다 |
| `normalize("NFC")` | 사용자 입력·파일 이름을 **저장·비교하기 직전** |
| `isWellFormed` / `toWellFormed` | 밖으로 내보내기 전 **깨진 값을 막을 때**(ES2024 — Node 18 에는 없다) |
| `Buffer.byteLength` · `TextEncoder` | **UTF-8 바이트 수**가 필요할 때(DB 칼럼·전송량) |

**안 쓰는 자리**는 넷이다.
**`length` 로 「몇 글자」를 세지 마라** — 그 질문에는 세 가지 답이 있다.
**정수 인덱스로 문자열을 자르지 마라** — 페어 한가운데가 조용히 갈린다.
**`split('')` 으로 글자를 쪼개지 마라** — 이모지가 깨진다.
**`NFKC` 로 원본을 저장하지 마라** — 글자가 바뀐다.

## 핵심 문장

- **`length` 는 UTF-16 코드 유닛을 센다.** 글자도 아니고 바이트도 아니고 화면의 칸도 아니다 — **넷이 다 다르다.**
- **BMP 밖의 글자는 두 칸에 앉는다.** 이모지가 전부 거기 있어서 이 문제가 실무에서 매일 나온다.
- **인덱스와 `split('')` 은 칸 단위, 이터레이션은 코드 포인트 단위** — 그리고 **자소는 `Segmenter`** 다.
- **페어를 가르는 자르기는 안 터진다.** Rust 는 패닉하고 Go 는 침묵하는데, **JS 는 침묵한 뒤 출력 자리에서 길마다 다르게** 군다.
- **UTF-8 로 나가면 `U+FFFD` 가 되어 되돌릴 수 없고, `JSON` 은 이스케이프해 보존하며, `encodeURIComponent` 만 터진다.**
- **`===` 는 정규화를 안 본다.** 눈에 같은 두 문자열이 다르고, `localeCompare` 는 또 다른 답을 한다.
- **`isWellFormed` 는 이 배치에서 두 판이 갈린 유일한 자리**다 — 기능 유무는 **던져서** 확인한다.

## 관련 자료

- 목록: [js/syntax 주제 목록](../README.md) — 이 주제는 **04번**
- 선행: [01 — 값의 종류와 `typeof`](../01-value-types-and-typeof/2-summary.md) — 문자열이 **원시 값**이고 점을 찍으면 래퍼가 생기는 것.
- 선행: [02 — 강제 변환과 `==` 대 `===`](../02-coercion-and-loose-equality/2-summary.md) — **`'10' < '9'` 가 참**인 이유.
  **경계**: 그쪽은 「문자열이 다른 타입과 섞일 때」까지, 여기는 「**그 문자열 안이 어떻게 생겼나**」부터다.
- 선행: [03 — 숫자와 `BigInt`](../03-numbers-and-bigint/2-summary.md) — 큰 ID 를 **문자열로 주고받는** 이유.
- 이어지는 곳: [목록의 **28번 주제**](../28-string-methods-and-template-literals/) 「`String` 메서드와 템플릿 리터럴」 — 이 코드 유닛 열 위에서 도는 메서드들.
- 이어지는 곳: 목록의 [**29**](../29-regexp-basics/)·[**30**](../30-regexp-advanced/)번 주제 「정규식」 — **`u`/`v` 플래그**가 코드 포인트 단위를 켜는 자리.
- 이어지는 곳: [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) 「이터러블 프로토콜과 `for...of`」 — **`[...s]` 가 코드 포인트 단위인 것의 정본**.
- 이어지는 곳: 목록의 **50번 주제** 「`Intl` 국제화 포맷」 — `Intl.Segmenter` 를 포함한 ECMA-402 전반.
- 이어지는 곳: [목록의 **31번 주제**](../31-json/) 「`JSON`」 — well-formed `JSON.stringify` 의 정본.
- 기존 노트: [`cs/foundations/data-representation/`](../../../../data-representation/) — 코드 포인트와 UTF-8/16 의 **비트 배치**.
  **경계**: 그쪽은 「바이트가 어떻게 생겼나」까지, 여기는 「**JS 가 그것을 어떤 타입으로 다루나**」부터다.
- ★★ 형제 비교 — [`python/syntax/06-strings-bytes-unicode`](../../../python/syntax/06-strings-bytes-unicode/2-summary.md):
  **파이썬은 코드 포인트를 센다.** `"👍"` 의 `len` 이 **1** 이다. JS 의 `length` 가 2 인 것과 정확히 대비된다.
- ★★ 형제 비교 — [`rust/syntax/15-slices-ranges-and-utf8-boundaries`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/2-summary.md):
  **러스트는 UTF-8 바이트를 센다.** 그리고 **경계가 아닌 자리를 자르면 패닉한다** — JS 가 침묵하는 바로 그 자리다.
- ★ 형제 비교 — [`java/syntax/35-string`](../../../java/syntax/35-string/2-summary.md):
  **자바도 UTF-16** 이다. `length()`·`charAt`·`codePointAt` 의 구조가 **같은 집안**이다.
- 연혁은 여기가 아니다: [`history/js/`](../../../../../../history/js/) — 왜 UTF-16 이 골라졌나.

## 용어 풀이

- **코드 유닛(code unit)**: 인코딩이 쓰는 고정 크기 조각. UTF-16 은 16비트, UTF-8 은 8비트다. **`length` 가 세는 것**이 이것이다.
- **코드 포인트(code point)**: 유니코드가 글자마다 매긴 번호. 범위는 `0`\~`0x10FFFF` 다.
- **BMP (Basic Multilingual Plane)**: `0x0000`\~`0xFFFF` 구간. 한글·한자·라틴이 전부 여기 있고 **한 칸에 앉는다.**
- **서로게이트 페어(surrogate pair)**: BMP 밖 코드 포인트를 **두 칸으로 쪼개 담는** 방식. high 가 `0xD800`\~`0xDBFF`, low 가 `0xDC00`\~`0xDFFF` 다.
- **짝 없는 서로게이트(lone surrogate)**: 짝을 잃은 반쪽. **글자가 아니지만** JS 문자열 안에는 값으로 들어간다.
- **well-formed 문자열**: 짝 없는 서로게이트가 없는 문자열. `isWellFormed()` 가 묻는 것이 이것이다(ES2024).
- **자소 클러스터(grapheme cluster)**: 사람이 한 글자로 보는 단위. `Intl.Segmenter` 가 센다.
- **ZWJ (ZERO WIDTH JOINER, `U+200D`)**: 이모지 여럿을 한 그림으로 묶는 보이지 않는 글자. 가족 이모지가 8칸인 이유다.
- **결합 문자(combining character)**: 앞 글자에 덧붙어 한 글자처럼 보이게 하는 글자(`U+0301` 등).
- **정규화(normalization)**: 같은 글자를 나타내는 여러 표현을 한 형태로 모으는 것.
  NFC(합침)·NFD(풂)는 **표준 동치**, NFKC·NFKD 는 **호환 동치**라 글자가 바뀐다.
- **`U+FFFD` (REPLACEMENT CHARACTER)**: 인코딩이 처리 못 한 자리를 대신하는 글자. 화면에 마름모 물음표로 보인다.
- **ICU**: 유니코드 데이터와 로캘 규칙을 담은 라이브러리. `Intl` 이 이것에 기댄다 — **판이 다르면 답이 달라질 수 있다.**

## 더 들어가면

- **`String.raw` 와 템플릿 리터럴**은 이 문자열 위에 얹힌 **문법**이고 28번 주제다.
  이 문서는 `\uXXXX` 이스케이프를 **출력에 찍기 위해** 썼을 뿐 문법으로는 다루지 않았다.
- **정규식의 `u` 플래그**가 패턴을 코드 포인트 단위로 바꾼다. `v` 플래그(ES2024)는 거기에 집합 연산을 더한다 — 29·30번 주제다.
  이 문서에서는 `split(/(?:)/u)` 한 줄만 던졌다.
- **`Intl.Segmenter` 의 `word` 분할이 공백 분할과 다르다**는 것은 던져서 봤지만,
  로캘별 규칙(태국어·일본어처럼 공백이 없는 언어)은 **이 문서에서 던지지 않았다.**
- **`String.prototype.at` 은 코드 유닛 단위**다(ES2022). 「뒤에서 세기」만 편해질 뿐 단위는 그대로다.
- **터미널 폭(East Asian Width)** 을 재는 표준 API 가 없다. 이 문서는 **그 수치를 재지 않았다** —
  「안 돌려 본 것」이 아니라 「**표준으로는 잴 방법이 없는 것**」이라 따로 적는다.
- **`Buffer` 는 Node 의 API** 다. 같은 답을 **표준 `TextEncoder`** 로도 확인해 두었으므로
  이 문서의 UTF-8 관련 결론은 Node 에만 매인 것이 아니다.
