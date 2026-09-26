# js/syntax/04 — 문자열과 UTF-16: 「`length` 가 세는 것은 글자가 아니다」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력은 **node v20.19.6**(기본 판) · **node v18.19.1**(대조) · **Google Chrome 151.0.7922.173** · x86-64 Linux 에서 실제로 돌려 얻은 것이고,
> 블록은 **전부 캡처 파일에서 조립**했다.
> 소스는 `js01b-04a-code-unit-grid.js`\~`js01b-04h-browser.js` 와 `js01b-vdiff.sh` 다.
>
> ★★★ **7번은 두 판의 출력을 둘 다 싣는다** — 이 배치 네 주제에서 **판이 갈린 유일한 자리**다.
> ★★ **코드 유닛은 `\uXXXX` 로 펼쳐 찍었다** — 이모지를 그대로 찍으면 터미널 폭에 따라 칸이 어긋난다.
> ★★ **예외는 `e.constructor.name` 과 `e.message` 로만 찍었다.**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | Node 스택트레이스의 **절대 경로** — 한 줄도 싣지 않았다 | ★★★ **격자의 `length`·`[...s]`·바이트 수 전부** |
> | 예외 **문구**(판이 오르면 바뀐다) | ★★★ **`\uXXXX` 로 펼친 코드 유닛 열** |
> | ★★ **자소 수** — ICU 판에 달렸다(두 판에서는 안 갈렸다) | ★★ **예외의 종류** — `URIError`·`RangeError`·`TypeError` |
> | **터미널에서 이모지가 몇 칸인가** — 잴 방법이 표준에 없다 | ★★ `normalize` 결과 · **나가는 길마다의 답** · 종료 코드 |

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 한 문자열을 네 번 재면 — **열 줄에서 네 열이 흩어진다** ★★★ 본체

**출력**

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

**왜 그런가**

- ★★★ **네 열이 전부 다른 줄은 셋**이다 — **가족 이모지(`8 5 1 18`)** · **국기(`4 2 1 8`)** ·
  **살색 이모지(`4 2 1 8`)**. 그중 **가족 이모지가 가장 넓게 벌어진다.**
  ★ `A` 는 `1 1 1 1` 로 넷이 같다 — **ASCII 에서만 「몇 글자인가」가 한 가지 답**을 갖는다.
- ★★★ **가족 이모지의 8칸은 `\ud83d\udc68\u200d\ud83d\udc69\u200d\ud83d\udc67`** 이다.
  사람 셋이 각 **2칸**(서로게이트 페어), 그 사이 **ZWJ 둘**이 각 **1칸** — 합쳐 8 이다.
  ★ 코드 포인트로는 **5**(사람 3 + ZWJ 2), 자소로는 **1** 이다.
- ★★ **조합형 한글 `\u1112\u1161\u11ab` 은 3칸**이고 **완성형 `\ud55c` 은 1칸**이다.
  화면에 똑같이 보이는데 `length` 가 3 과 1 이다 — ★ **한글도 이 문제에서 자유롭지 않다.**
- ★★ **국기가 자소 1 인데 코드 포인트 2** 인 것은 **지역 표시 기호 두 개**(`\ud83c\uddf0` + `\ud83c\uddf7`)의 조합이기 때문이다.
  두 글자가 붙어 한 그림이 된다.
- ★ **DB 칼럼 크기에 필요한 것은 마지막 열(utf8 바이트)** 이다.
  `"가"` 는 `length` 1 인데 **3바이트**이고 가족 이모지는 `length` 8 인데 **18바이트**다.
  ★ `length` 로 칼럼을 잡으면 **넘친다.**

### 2. 서로게이트 페어를 해부하면 — **갈리는 자리는 high 하나뿐이다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`charCodeAt` 은 칸을, `codePointAt` 은 글자를 읽는다.**
  같은 0 번 자리에서 `55357`(`U+D83D`)과 `128077`(`U+1F44D`)이 나온다.
- ★★★ **`codePointAt(1)` 이 `56397`** 인 것은 그 함수가 「**그 자리에서 시작하는 코드 포인트**」를 주기 때문이다.
  low 서로게이트 자리에서는 **앞으로 돌아가 합칠 수가 없으므로** 그 조각만 준다.
  ★ **조심할 것은 인덱스다** — 루프를 `i++` 로 돌면 **반쪽이 섞여 나온다.**
  코드 포인트로 돌려면 `for...of` 를 쓰거나 `i` 를 **2씩** 올려야 한다.
- ★★ **합치는 산수**는 `(hi - 0xD800) * 0x400 + (lo - 0xDC00) + 0x10000` 이고
  `(55357 - 55296) * 1024 + (56397 - 56320) + 65536 = 128077` 로 `codePointAt` 과 맞는다.
- ★★ **경계는 `0xFFFF` 와 `0x10000`** 이다. 던져 보면 앞엣것이 `length` 1, 뒤엣것이 2 다.
- ★★★ **`[4]` 의 표에서 두 함수가 갈리는 자리는 하나**(`i=1`, high 서로게이트)뿐이다.
  `i=0`(`a`)·`i=2`(low)·`i=3`(`가`)은 둘이 같다.
  ★ **갈리는 것은 high 자리뿐**이라는 것이 이 표의 결론이다.

### 3. 여섯 가지로 쪼개면 — **「안 깨진다」에 두 단계가 있다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`split('')` 만 페어를 깨뜨린다.** 나머지 다섯은 `\ud83d\udc4d` 를 한 조각으로 지킨다.
  ★ **이터레이션 프로토콜이 코드 포인트 단위**라는 것이 명세의 약속이고, `split(/(?:)/u)` 는 **`u` 플래그**가 그 단위를 켠다.
- ★★★ **NFD 형태(`e` + `U+0301`)에서는 여섯 중 다섯이 둘로 쪼개고 `Segmenter` 만 하나**로 본다.
  **가족 이모지에서는 `[...s]` 가 다섯 조각**을 내고 `Segmenter` 만 하나다.
  ★★ 그래서 **「안 깨진다」에 두 단계**가 있다 — **코드 포인트를 지키는 단계**와 **자소를 지키는 단계**.
  `[...s]` 를 쓰면 글자가 된다는 말은 **절반만 맞다.**
- ★★ **뒤집기**에서 차이가 눈에 보인다.
  `split("").reverse().join("")` 은 `\u0062\udc4d\ud83d\u0061` — **low 가 앞, high 가 뒤**로 와서 깨진 글자가 찍힌다.
  `[...t].reverse().join("")` 은 `\u0062\ud83d\udc4d\u0061` 로 멀쩡하다.
- ★★ **`t[1]`·`charAt(1)`·`at(1)` 이 전부 `\ud83d`**(반쪽)이고 **`[...t][1]` 만 `\ud83d\udc4d`**(글자)다.
  ★ 비용은 **`[...t]` 가 O(n)** 이라는 것이다 — 한 글자를 얻으려고 문자열 전체를 훑는다.
- ★ **`u` 를 빼면 `split(/(?:)/)` 는 코드 유닛 단위**가 되어 `split('')` 과 같아진다. **플래그 하나가 단위를 바꾼다.**

### 4. 페어 한가운데를 자르면 — **침묵한 뒤 길마다 다르게 군다** ★★★ 본체

**출력**

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

**왜 그런가**

- ★★★ **자르는 자리에서는 아무 일도 안 난다.** `slice`·`substring`·`substr` 넷이 전부
  **예외도 경고도 없이** 반쪽을 돌려준다.
- ★★★ **그 반쪽은 값으로서 완전히 정상**이다 — `length` 가 1, `typeof` 가 `"string"`,
  `half === half` 가 참, `half + "x"` 도 된다. **`charCodeAt` 까지 답한다.**
  ★ **「깨진 문자열」이라는 표시가 값 어디에도 없다.**
- ★★★ **나가는 길마다 답이 다르다** — 이 절의 표가 그것이다.

  | 나가는 길 | 무엇을 하나 | 되돌아오나 |
  |---|---|---|
  | `JSON.stringify` | **이스케이프해서 보존**(`"\ud83d"`) | ★ **된다** — `JSON.parse(JSON.stringify(x)) === x` |
  | `encodeURIComponent` | ★ **`URIError: URI malformed`** | — 유일하게 **터지는** 길 |
  | UTF-8(`Buffer`·`TextEncoder`) | ★ **조용히 `U+FFFD`**(`ef bf bd`) | ★ **안 된다** |
  | UTF-16LE(`Buffer`) | **그대로 통과**(`3d d8`) | **된다** |
  | `normalize("NFC")` | **그대로 통과**(`\ud83d`) | — 건드리지 않는다 |

- ★★★ **되돌릴 수 없는 길은 UTF-8** 이다. `Buffer.from(half,"utf8").toString("utf8") === half` 가 **거짓**이다.
  ★★ **파일에 쓰거나 네트워크로 보내는 순간 원래 값이 사라진다** — 이 주제에서 가장 조용한 사고다.
  ★ `TextEncoder`(표준 API)도 같은 `ef bf bd` 를 낸다 — **Node 의 `Buffer` 에만 매인 결론이 아니다.**
- ★★★ **세 언어가 같은 상황에서 다른 답을 한다.**

  | 언어 | 문자열의 단위 | 경계 아닌 자리를 자르면 |
  |---|---|---|
  | **Rust** | UTF-8 **바이트** | ★ **런타임 패닉** — 프로그램이 죽는다 |
  | **Go** | UTF-8 **바이트** | ★ **침묵.** 깨진 바이트가 남고 `range` 로 돌면 **`U+FFFD` 가 바이트마다** 나온다 |
  | **JS** | UTF-16 **코드 유닛** | ★ **침묵.** **짝 없는 서로게이트가 값으로 남고** 나가는 길마다 답이 다르다 |

  ★★ **Rust·Go 의 동작은 형제 문서의 실측**이다 — 이 문서에서 직접 돌리지 않았다:
  [`rust/syntax/15-slices-ranges-and-utf8-boundaries`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/2-summary.md) ·
  [`go/syntax/10-strings-bytes-runes-and-utf8-iteration`](../../../go/syntax/10-strings-bytes-runes-and-utf8-iteration/2-summary.md).
  ★★★ **JS 가 가장 늦게 터진다.** Rust 는 자르는 자리에서, Go 는 읽는 자리에서, **JS 는 내보내는 자리에서** 드러난다.
- ★★ **잘 자르는 법은 둘** — `[...s].slice(0,3).join('')` 과 `Segmenter` 로 세 자소를 가져오는 것.
  이 예에서는 **둘이 같은 답**(`\u0061\u0062\ud83d\udc4d`)을 낸다.

### 5. 정규화 — **`===` 와 `localeCompare` 가 다른 층에 산다** ★★★

**출력**

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

**왜 그런가**

- ★★★ **`===` 는 코드 유닛 열을 그대로 견준다.** 그래서 `Set` 크기가 **2** 이고 `Map` 이 **못 찾는다**(`undefined`).
  **`localeCompare` 만 `0`** 을 돌려준다 — ★ **같은 두 값에 두 도구가 다른 답**을 한다.
  ★★ 비교를 `===` 로 하면서 정렬·검색을 `localeCompare` 로 하면 **둘이 어긋난다.**
- ★★★ **조합형 한글은 3칸, 완성형은 1칸**이고 `"한글".normalize("NFD").length` 는 **6** 이다.
  ★ **macOS 가 만든 파일 이름이 NFD 에 가깝다** — 그 경계에서 「같은 이름인데 못 찾는」 사고가 난다.
- ★★ **`NFKC` 가 길이를 바꾸는 줄**은 `\u00bd`(½ → `1⁄2`, 3)와 `\u2163`(Ⅳ → `IV`, 2)와 `\ufb01`(ﬁ → `fi`, 2)이다.
  ★ **「같은 글자를 모으는」 것이 아니라 「비슷한 글자로 갈아치우는」 것**이다.
- ★★★ **`K` 가 아닌데 글자가 바뀌는 줄은 `\u212b`(ANGSTROM SIGN)** 이다.
  **NFC 만 거쳐도 `\u00c5`** 가 된다 — 같은 글자의 다른 표현으로 취급되기 때문이다.
  ★★ **「표준 동치(NFC/NFD)는 글자를 안 바꾼다」는 틀린 직관**이고, 이 한 줄이 그것을 깬다.
  ★ 그 줄의 NFD 길이가 2 인 것도 같은 이유다.
- ★ **`normalize` 는 ZWJ 를 못 고친다** — 가족 이모지 길이가 그대로 8 이다. 정규화의 영역이 아니다.
  없는 형태를 주면 **`RangeError`** 이고 네 가지로 닫혀 있다.

### 6. 자소를 묻는 도구 ★★

**출력**

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

**왜 그런가**

- ★★★ **「있는가」를 던져서 확인했다** — `typeof Intl.Segmenter` 가 `function` 이고
  `resolvedOptions()` 가 `{"locale":"ko","granularity":"grapheme"}` 을 답한다.
  ★ **문서를 읽은 것이 아니라 물어본 것**이다. 문서는 「무엇이 옳은가」를, 실행은 「지금 무엇이 되는가」를 말한다.
- ★★★ **일곱 문자열 중 자소가 1 이 아닌 것은 국기 두 개짜리(`🇰🇷🇯🇵`) 하나**뿐이고 그것이 **2** 다.
  `length` 는 2\~8 로 흩어져 있는데 **자소는 전부 1** 이다 — ★ 이 열이 **「사람이 세는 글자」에 가장 가깝다.**
- ★★ **`granularity` 를 바꾸면 같은 문장이 자소 16 · 단어 9 · 문장 2 조각**으로 갈린다.
  ★ **단어 분할이 공백 분할과 다르다** — `["Hello", ",", " ", "세계", "!", " "]` 처럼
  **구두점과 공백이 각각 따로** 나온다. `split(" ")` 으로는 얻을 수 없는 분할이다.
- ★★★ **못 답하는 질문은** 「터미널에서 몇 칸인가」다.
  `"가나".padEnd(4)` 는 **코드 유닛을 세어** 4칸짜리 문자열을 만들지만 화면 폭은 그보다 넓다.
  ★★ **표준 JS 에 화면 폭을 재는 API 가 없어서 이 문서는 그 수치를 적지 않았다** —
  「안 돌려 본 것」이 아니라 「**측정 방법 자체가 표준 밖인 것**」이라 따로 적는다.
- ★★ **자소 수는 「ICU 데이터에 달린 것」 칸**이다.
  v18(ICU 74.2 · 유니코드 15.1)과 v20(ICU 77.1 · 유니코드 16.0)에서 **한 글자도 안 갈렸지만**
  ★ **그것은 관찰이지 보장이 아니다.** 새 이모지가 들어온 판에서는 달라질 수 있다.

### 7. 두 판이 갈린 자리 — **v18 에는 없고 v20 에는 있다** ★★★

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

**왜 그런가**

- ★★★ **`typeof String.prototype.isWellFormed` 가 v20 은 `function`, v18 은 `undefined`** 다.
  ★ **이 배치 네 주제에서 두 판이 갈린 유일한 자리**다. `isWellFormed`/`toWellFormed` 는 **ES2024** 이고
  v18 의 V8 은 10.2, v20 은 11.3 이다.
- ★★★ **v18 에서는 다섯 줄이 전부 `TypeError: … is not a function`** 으로 바뀐다.
  ★ **「미지원」을 단정하기 전에 던져 본 것**이고, 그 예외가 가장 강한 근거다.
- ★★ **`toWellFormed()` 는 짝 없는 서로게이트를 `U+FFFD` 로 바꾼다** — 4번 절의 **UTF-8 인코딩이 하는 일과 같다.**
  ★★ 차이는 「**내가 언제 하느냐**」다. 미리 부르면 **어디서 깨졌는지 알 수 있고**,
  안 부르면 **파일에 쓰는 순간 말없이** 바뀐다. 같은 손실을 **시끄럽게 만드는 장치**다.
- ★★ **없는 판에서 같은 일을 하는 법 셋** —
  ① 짝 없는 서로게이트를 찾는 정규식(블록의 `broken` 함수 — **두 판에서 똑같이** `true`/`false` 를 냈다)
  ② `JSON.stringify` 가 `"\ud83d"` 로 이스케이프하는 것을 보는 것
  ③ **`Buffer`/`TextEncoder` 왕복이 깨지는지** 보는 것(`false`).
- ★ **두 출력을 가르는 유일한 근거 줄은 첫 줄**이다 — `node`·`v8`·`icu`·`unicode` 판이 거기 찍힌다.
  ★ 그 줄이 없으면 두 블록이 **왜 다른지** 문서에서 알 수가 없다.

### 8. 브라우저 — **같은 V8 인데 판이 다르다** ★★

**출력**

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

**왜 그런가**

- ★★★ **Chrome 151 에는 `isWellFormed` 가 있다**(`typeof` 가 `function`).
  Node 18 에는 없다 — ★ **엔진은 같은 V8 인데 판이 달라서** 기능 유무가 갈린다.
- ★★ **「같은 V8 이면 같다」가 틀린 이유**가 그것이다. **엔진 이름이 아니라 판을 물어야** 한다.
  ★ 그래서 이 문서의 모든 블록 첫 줄에 **판을 찍어** 두었다.
- ★★ **자소 수·코드 유닛 수·바이트 수는 Node 와 한 글자도 안 갈렸다** —
  `family.length` 8, `[...family].length` 5, 자소 1.
- ★ **`encodeURIComponent` 가 브라우저에서도 `URIError`** 이고 `TextEncoder` 도 `ef bf bd` 다.
  **호스트가 달라도 문자열 규칙은 같다** — 달라진 것은 **판에 달린 기능 유무**뿐이다.

### 9. 보장인가 데이터인가 ★★★

| 층 | 이 주제에서 여기 들어가는 것 |
|---|---|
| **명세 보장** | 문자열이 **UTF-16 코드 유닛의 열**인 것 · `length` 가 그 수인 것 · **BMP 밖은 두 칸** · 합치는 산수 · **인덱스와 `split('')` 은 칸 단위, 이터레이션은 코드 포인트 단위** · `codePointAt` 이 low 자리에서 조각만 주는 것 · **페어를 가르는 자르기가 안 터지는 것** · `JSON.stringify` 의 이스케이프(ES2019) · **`encodeURIComponent` 의 `URIError`** · `===` 가 정규화를 안 보는 것 · **`NFKC` 가 길이를 바꾸고 `NFC` 도 `U+212B` 를 바꾸는 것** · `isWellFormed`/`toWellFormed` 의 동작(ES2024) |
| **엔진(V8) · 판** | **v18 에 `isWellFormed` 가 없는 것** · Chrome 151 에 있는 것 · 나머지 여섯 스크립트가 두 판에서 같았던 것 |
| **ICU 데이터에 달린 것** | **`Intl.Segmenter` 의 자소 수** · `supportedLocalesOf` 의 목록 · `localeCompare` 가 `0` 인 것 |
| **이 판의 관찰** | 예외 **문구** · UA 문자열 |

- ★★★ **ICU 칸을 따로 세운 이유**는 그 답이 **명세가 아니라 데이터**에서 오기 때문이다.
  명세는 「자소 단위로 쪼갠다」까지 말하고 **「무엇이 한 자소인가」는 유니코드 데이터**가 정한다 —
  ★ **판이 오르면 답이 달라질 수 있는 유일한 칸**이다.
- ★★ **`Buffer` 로 얻은 결론이 Node 에만 매인 것이 아니다** — 같은 `ef bf bd` 를
  **표준 `TextEncoder`** 로도, **브라우저에서도** 확인했다.
  ★ 「한 도구에서 본 것을 성질로 일반화하지 마라」의 반대 방향 — **두 도구로 겹쳐 확인**한 것이다.
- ★★ **「두 판에서 자소 수가 같았다」는 「이 문서의 격자를 어느 판에서 읽어도 된다」의 근거**가 되고,
  **「자소 분할이 판에 무관하다」의 근거는 못 된다.**
- ★ **판이 갈린 자리는 하나**다 — 일곱 스크립트 중 `js01b-04g-well-formed.js` 뿐이다.

### 10. 경계와 형제들 ★★★

| 주제 | 정본 |
|---|---|
| 코드 포인트와 UTF-8/16 의 **비트 배치** | [`cs/foundations/data-representation/`](../../../../data-representation/) |
| `String` 메서드와 템플릿 리터럴 | [목록의 **28번 주제**](../28-string-methods-and-template-literals/) |
| 정규식의 `u`/`v` 플래그 | 목록의 [**29**](../29-regexp-basics/)·[**30**](../30-regexp-advanced/)번 주제 |
| `[...s]` 가 코드 포인트 단위인 것의 **프로토콜** | [목록의 **19번 주제**](../19-iterable-protocol-and-for-of/) |
| well-formed `JSON.stringify` | [목록의 **31번 주제**](../31-json/) |
| `Intl` 전반 | 목록의 **50번 주제** |

- ★★★ **파이썬은 코드 포인트를 센다.** `len("👍")` 이 **1** 이다 — JS 의 `length` 가 2 인 것과 정확히 대비된다.
  다만 **결합 문자·ZWJ 에서는 파이썬도 똑같이 걸린다**(가족 이모지가 5).
  ★ 형제 문서: [`python/syntax/06-strings-bytes-unicode`](../../../python/syntax/06-strings-bytes-unicode/2-summary.md).
- ★★★ **러스트는 UTF-8 바이트를 세고**, **경계가 아닌 자리를 자르면 런타임 패닉**이다.
  ★ 형제 문서: [`rust/syntax/15-slices-ranges-and-utf8-boundaries`](../../../rust/syntax/15-slices-ranges-and-utf8-boundaries/2-summary.md).
- ★★ **자바도 UTF-16 이라 같은 집안**이다. `length()`·`charAt`·`codePointAt` 의 구조가 그대로 대응한다.
  ★ 형제 문서: [`java/syntax/35-string`](../../../java/syntax/35-string/2-summary.md).
- ★★ **Go 는 UTF-8 바이트를 세고 침묵한다** — 잘린 바이트가 남고 `range` 로 돌면 **`U+FFFD` 가 바이트마다** 나온다.
  ★ **JS 와 Go 가 둘 다 침묵하지만 남는 것이 다르다** — Go 는 **깨진 바이트**, JS 는 **짝 없는 코드 유닛**이다.
  ★ 형제 문서: [`go/syntax/10-strings-bytes-runes-and-utf8-iteration`](../../../go/syntax/10-strings-bytes-runes-and-utf8-iteration/2-summary.md).
- ★ **이 주제가 끝까지 책임지는 것 셋** — ① 네 가지 자가 어디서 갈리나
  ② 페어를 가르면 무엇이 남고 나가는 길마다 어떻게 되나 ③ 자소를 물을 수 있는 도구와 그 한계.

## 실행 검증

| 소스 | 무엇을 고정하나 | 몇 번 · 어디서 |
|---|---|---|
| `js01b-04a-code-unit-grid.js` | **네 가지 자의 격자 10줄** · 코드 유닛을 펼친 열 | node20 1벌 + node18 대조 1벌 |
| `js01b-04b-surrogate-pair.js` | `charCodeAt` 과 `codePointAt` 이 **high 자리에서만** 갈리는 것 · 합치는 산수 | node20 1벌 + node18 대조 1벌 |
| `js01b-04c-splitting.js` | **여섯 방법 × 세 문자열** · 「안 깨진다」의 두 단계 · 뒤집기 | node20 1벌 + node18 대조 1벌 |
| `js01b-04d-cut-through-pair.js` | **자를 때 침묵하는 것** · **나가는 길 다섯의 서로 다른 답** · 되돌아오는 길 | node20 1벌 + node18 대조 1벌 |
| `js01b-04e-normalize.js` | `===` 대 `localeCompare` · 한글 조합형 · **`NFC` 가 `U+212B` 를 바꾸는 것** | node20 1벌 + node18 대조 1벌 |
| `js01b-04f-segmenter.js` | `Intl.Segmenter` 가 **있다는 것** · 자소 열 · granularity 셋 | node20 1벌 + node18 대조 1벌 |
| `js01b-04g-well-formed.js` | ★★★ **두 판이 갈린 유일한 자리** — v20 과 v18 양쪽 | node20 1벌 · **node18 1벌(양쪽 다 실음)** |
| `js01b-04h-browser.js` | Chrome 151 에는 **있다**는 것 · 나머지 수치가 같은 것 | Chrome 151 1벌 |
| `js01b-vdiff.sh` | 일곱 중 **여섯이 두 판에서 한 글자도 같다**는 것 | 1벌 |

**구현 의존 항목** — 다음은 **이 환경(node 20.19.6 / 18.19.1 · Chrome 151 · ICU 74.2 / 77.1)에서만** 그렇다.

- ★★★ **`Intl.Segmenter` 의 자소 수** — **ICU 데이터**에 달렸다. 두 판에서 안 갈렸지만 **보장이 아니다.**
- ★★ **`isWellFormed` 의 유무** — **판**에 달렸다. ES2024 를 구현한 판부터 있다.
- ★★ **예외 메시지 문구** — `URI malformed` · `The normalization form should be one of NFC, NFD, NFKC, NFKD.` ·
  `… is not a function`. **종류는 명세, 문구는 V8 의 것**이다.
- ★ **`supportedLocalesOf` 의 목록** · **`localeCompare` 가 `0` 인 것** — 로캘 데이터에 달렸다.
- ★ **UA 문자열** `Chrome/151.0.0.0`.

**문자열이 UTF-16 코드 유닛의 열인 것 · `length` 가 세는 것 · 서로게이트 페어와 그 산수 · 쪼개는 여섯 방법의 단위 · 페어를 가르는 자르기가 안 터지는 것 · 나가는 길 다섯의 서로 다른 답 · 정규화 네 형태와 `NFC` 가 `U+212B` 를 바꾸는 것은 구현 의존이 아니다.**
어느 엔진에서도 같아야 한다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — **Rust·Go 를 이 문서에서 직접 돌린 것**(형제 문서의 실측을 인용했다) ·
  정규식 `u`/`v` 플래그 전반 · `Intl.Segmenter` 의 **로캘별 단어 분할**(태국어·일본어) ·
  `String.raw` 와 템플릿 리터럴 · `TextDecoder` 의 `fatal` 옵션 ·
  **ICU 판이 더 낮거나 높은 Node** · 다른 엔진(SpiderMonkey·JavaScriptCore) ·
  `String.prototype.at` 의 음수 인덱스와 페어의 상호작용.
- ★★ **못 잰 것** — **「터미널·브라우저에서 이 글자가 몇 칸을 먹나」.**
  `padEnd` 는 코드 유닛을 세고 `Segmenter` 는 자소를 세는데, **화면 폭은 둘 중 어느 것도 아니다.**
  표준 JS 에 그것을 묻는 API 가 없고, 터미널로 재면 **터미널·폰트에 따라 답이 달라져** 그 조건의 답이 나온다.
  ★★★ 그래서 본문은 **「표준에 그 API 가 없다」까지만 적고 수치를 한 개도 적지 않았다** —
  「안 돌려 본 것」이 아니라 「**측정 방법 자체가 전제를 요구해 잴 수 없는 것**」이라 따로 적는다.

**판이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **`Intl.Segmenter` 의 자소 격자** — ICU·유니코드 판이 오르면 **새 이모지에서 달라질 수 있다.**
- ★★★ **7번의 두 블록** — v18 쪽이 언젠가 지원하는 판으로 바뀌면 그 대비가 사라진다.
  ★ 그때는 **「갈렸던 자리」였다는 사실을 지우지 말고 판과 함께 남긴다.**
- ★★ **예외 메시지 문구** — 네 블록에 들어 있다.
- ★ **`Intl.Segmenter` 의 `supportedLocalesOf`** — 빌드에 들어간 로캘에 달렸다.
- **코드 유닛 격자와 서로게이트 산수는 다시 돌릴 필요가 없다** — UTF-16 과 명세가 정해 놓았다.
