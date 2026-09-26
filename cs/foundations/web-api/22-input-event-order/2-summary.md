# web-api/22 — 입력 이벤트의 순서: `keydown`→`beforeinput`→`input`→`change` 와 IME 조합 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 를 늘린 「한 번 타이핑의 시간선」이다** — 진짜 키 입력 한 번이 부르는 이벤트를 **한 줄씩, 그때의 `value` 와 함께** 적는다. 이벤트가 **값을 바꾸기 전인가 뒤인가**가 이 시간선에서만 보인다.\
> ★★★ **IME 조합은 CDP 의 흉내다 — 진짜 입력기가 아니다.** `Input.imeSetComposition`·`Input.insertText` 는 CDP 문서 스스로 **experimental** 이고 「IME 를 **흉내 낸다**(emulates)」고 적는다. 이 편이 조합에 대해 적는 것은 전부 **「CDP 가 조합을 흉내 냈을 때 Chrome 151 이 낸 이벤트」** 이고, **실제 한글·일본어 입력기가 같은 순서를 내는지는 못 쟀다**(아래 「도구가 못 보는 것」).\
> **기준 소스** — [W3C UI Events](https://w3c.github.io/uievents/) 의 「3.6.5 Key Events During Composition」·「3.6.6 Input Events During Composition」·「7.3.1 How to determine keyCode for keydown and keyup events」(비규범 절 — 입력기가 처리 중이면 **229**) · [W3C Input Events Level 2](https://w3c.github.io/input-events/) 의 `inputType` 표(`insertCompositionText` 는 **「beforeinput cancelable: No」**) · [HTML Living Standard — The input element](https://html.spec.whatwg.org/multipage/input.html) 의 「Common event behaviors」 절(「`change` 는 값이 **확정될 때**, 그게 말이 안 되면 **포커스를 잃을 때**」) · CDP 는 [devtools-protocol 의 `browser_protocol.json`](https://github.com/ChromeDevTools/devtools-protocol/blob/master/json/browser_protocol.json) 의 `Input` 도메인. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. **키는 CDP `Input.dispatchKeyEvent` 로 넣은 진짜 입력**(렌더러가 사용자 키처럼 처리한다), 붙여넣기는 같은 키에 **편집 명령 `copy`·`paste`** 를 실은 것, **조합은 CDP 의 흉내**다. 하네스는 [20번 주제](../20-listener-lifetime/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [16번 주제](../16-event-propagation-phases/2-summary.md)(순서 로그를 적는 법 · `input`·`keydown` 이 버블한다). ★ **[17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)의 (7)·(8)** 이 **키보드 Space/Enter 가 `click` 을 만드는 것**과 **Enter 의 암묵 제출**을 쟀다 — 여기의 `keydown` 이 그 앞단이다. 마크업 쪽(`<input>` 타입 지도)은 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **22번**이 정본이다(아직 폴더 없음).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 편에는 흔들리는 칸이 없었다** — 세는 것이 전부 **순서와 값**이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 다섯 시간선 · 12칸 격자 · 막기 네 칸 · Enter 처리기 네 칸 | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **못 잰다** | **실제 입력기**(IBus·Windows IME·macOS)의 조합 이벤트 순서 · 조합 중 `keydown` 의 `key`/`keyCode` | CDP 는 **입력기 아래 층을 건너뛰고** 조합을 흉내 낸다. **안 돌려 본 것이 아니라 이 도구로는 원리상 못 잰다** |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | 입력 값은 속성이 아니라 프로퍼티다 |
| 창 ② 노드 프로브 | ★ **쓴다** | 이벤트마다 **그때의 `value`**(시간선의 마지막 열) |
| 창 ③ 같은 것을 두 번 읽기 | ★ **쓴다** | `beforeinput` 과 `input` 에서 `value` 를 **두 번** 읽어 「바꾸기 전 / 뒤」를 가른다 |
| **창 ④ 디스패치 계수기 → 한 번 타이핑의 시간선** | ★★★ **본체** | 어느 이벤트가 어느 순서로 · `key`·`keyCode`·`isComposing`·`inputType`·`data` |
| **진짜 키 입력(CDP)** | ★ **쓴다 — 입력 쪽** | 글자 · Backspace · Enter · Ctrl+C/V |
| ★★ **CDP 의 조합 흉내** | ★ **쓴다 — 단 제5의 상태** | 실제 입력기 대신 **CDP 가 만든 조합**으로 물었다 |

- ★★★ **제5의 상태 — 「조합 중에 무엇이 오나」를 진짜 입력기가 아니라 CDP 의 흉내로 물었다.** ★ **바꾼 창이 못 보는 것** — ① CDP 의 조합 호출은 **키 이벤트를 하나도 만들지 않는다**((4) — 키 이벤트는 따로 넣어야 한다). ② 그래서 **조합 중 `keydown` 의 `key`·`keyCode` 는 이 편이 넣은 값이 그대로 보일 뿐**이다 — `"Process"`/`229` 를 **Chrome 이 만든 것인지 이 편이 넣은 것인지 가를 수 없다**((6)). ③ 실제 입력기가 조합을 **언제 확정하고 몇 번 갱신하는지**도 CDP 가 정한 것이다.

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **실제 한글·일본어 입력기의 이벤트 순서** | 이 머신의 headless Chrome 에 입력기가 붙어 있지 않다. CDP 는 **입력기를 건너뛰고** 조합 결과만 렌더러에 넣는다 |
| ★★ **조합 중 `keydown` 의 `key: "Process"` · `keyCode: 229`** | 그 값은 **입력기가 키를 가로챘을 때 플랫폼 층이** 붙인다(UI Events 7.3.1 의 모형). CDP 의 키 이벤트는 **그 층 아래로 곧장** 들어가므로 **넣은 값이 그대로** 보인다((6)의 ②·③) |
| **모바일 가상 키보드**의 `keydown`(흔히 `key: "Unidentified"`) | 가상 키보드가 없다 |
| **맞춤법 자동 고침·음성 입력의 `inputType`** | 던지지 않았다 |
| **입력에 걸리는 시간** | 순서만 봤다. **재지 않았다** |

## 한눈에 — 쉽게 말하면

**★ 키 하나를 누르는 일은 「손가락이 눌렀다(`keydown`) → 곧 글자를 넣겠다고 예고(`beforeinput`) → 넣었다(`input`) → 손가락을 뗐다(`keyup`)」의 네 박자다. 그리고 `change` 는 「이 칸의 값을 이제 확정한다」는 따로 오는 도장이다. 한글 조합 중에는 네 박자가 「아직 쓰는 중」 표시(`isComposing`)를 달고 여러 번 돈다.**

| 비유 | 실체 |
|---|---|
| 손가락이 눌렀다 | `keydown` — 값은 **아직 그대로** |
| (옛 방식의) 「글자 키였다」 신고 | `keypress` — **옛 이벤트**, 글자 키·Enter 에서만 |
| 「이제 넣겠다」는 예고 | `beforeinput` — 값은 **아직 그대로**, 여기서 막으면 안 들어간다 |
| 넣었다 | `input` — 값이 **바뀐 뒤** |
| 손가락을 뗐다 | `keyup` |
| 확정 도장 | `change` — Enter 로 확정하거나 **다른 곳으로 떠날 때** |
| 연필로 쓰는 중(지우고 고칠 수 있음) | IME 조합 — `compositionstart`/`update`/`end` · `isComposing: true` |

```text
   ★ 한 번 타이핑의 시간선 — 빈 <input> 에 a 를 누르고 바깥을 누른다 (이 판)

   시간 ───────────────────────────────────────────────────────────────────▶

   keydown   keypress   beforeinput   (textInput)   input     keyup      change   blur
   "a"       "a"        insertText    "a"           insertText "a"       (확정)   (떠남)
   value ""  ""         ""            ""            ▲ "a"      "a"       "a"      "a"
                                                    └ 여기서 값이 바뀐다
   ────────── 막으면 안 들어간다 ───────────┘        └── 이미 들어갔다 ──
```

## 이 주제가 답하려는 질문

1. **한 번의 타이핑에서 어떤 이벤트가 어떤 순서로 나나** — 그리고 **어느 이벤트에서 값이 이미 바뀌어 있나.**
2. **`change` 는 언제 나나** — `input` 과 무엇이 다른가.
3. **조합 중에 `input` 값을 믿으면 안 되는 이유** — 조합 중에는 무엇이 다르게 오고, 무엇을 막을 수 없나.

## 동작 방식

### (1) ★★★ 본체 — 글자 하나와 떠나기

**언제 쓰나** — 「`keydown` 에서 값을 읽었는데 방금 친 글자가 없다」·「`change` 가 왜 한 박자 늦지?」일 때.

**던진 것** — `<input>` 에 이벤트 열두 가지를 달고, 판마다 값을 정해 포커스를 준 뒤 **진짜 키**를 누르고 뗀다. 각 줄의 마지막 열은 **그 리스너 안에서 읽은 `value`** 다. 아래 (2)\~(4)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa20b-22-type.html -->
<!doctype html>
<meta charset="utf-8">
<title>22-type</title>
<style>input, button { font-size: 20px; width: 300px; display: block; margin: 20px; }</style>
<input id="칸">
<input id="원본" value="붙일글">
<button id="바깥">바깥</button>
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 칸 = $('칸');
const O = [];
let n = 0;
const 값 = v => v === undefined ? '-' : JSON.stringify(v);
const 형들 = ['keydown', 'keypress', 'beforeinput', 'textInput', 'input', 'keyup', 'change',
             'compositionstart', 'compositionupdate', 'compositionend', 'paste', 'blur'];
for (const 형 of 형들) 칸.addEventListener(형, e => {
  O.push('  ' + padw(String(++n), 4) + padw(e.type, 19) + padw(값(e.key), 12) + padw(값(e.keyCode), 8)
       + padw(값(e.isComposing), 8) + padw(값(e.inputType), 26) + padw(e.data === undefined ? '-' : 값(e.data), 10) + 값(칸.value));
});
window.__판 = (제목, 처음값) => {
  칸.value = 처음값; n = 0;
  칸.focus(); 칸.setSelectionRange(처음값.length, 처음값.length);
  O.push('');
  O.push(제목 + ' — 처음 값 ' + JSON.stringify(처음값));
  O.push('  ' + padw('#', 4) + padw('이벤트', 19) + padw('key', 12) + padw('keyCode', 8) + padw('isComp', 8)
       + padw('inputType', 26) + padw('data', 10) + '그때 value');
  return 1;
};
window.__원본고르기 = () => { $('원본').focus(); $('원본').select(); return 1; };
const 누르기 = (key, code, vk, text, 덧) => [
  ['rawkey', Object.assign({ type: 'keyDown', key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }, text ? { text } : {}, 덧 || {})],
  ['rawkey', Object.assign({ type: 'keyUp', key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }, 덧 ? { modifiers: 덧.modifiers } : {})]];
window.__단계 = [
  ['js', '__판("① 글자 a 하나 → 바깥을 누른다", "")'], ...누르기('a', 'KeyA', 65, 'a'), ['click', '#바깥'],
  ['js', '__판("② Backspace", "ab")'], ...누르기('Backspace', 'Backspace', 8, ''),
  ['js', '__판("③ 글자 c → Enter (폼 없음) → 다른 칸으로 옮긴다", "ab")'], ...누르기('c', 'KeyC', 67, 'c'), ...누르기('Enter', 'Enter', 13, '\r'),
  ['js', '__원본고르기()'], ...누르기('c', 'KeyC', 67, '', { modifiers: 2, commands: ['copy'] }),
  ['js', '__판("④ Ctrl+V 붙여넣기", "")'], ...누르기('v', 'KeyV', 86, '', { modifiers: 2, commands: ['paste'] }),
  ['js', '__판("⑤ CDP 조합 흉내 — ㅎ → 하 → 한 → 확정 → 바깥을 누른다", "")'],
  ['ime', 'ㅎ', 1, 1], ['ime', '하', 1, 1], ['ime', '한', 1, 1], ['insert', '한'], ['click', '#바깥'],
];
window.__끝 = () => O.slice(1).join('\n');
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-22-type.html | sed -n '1,10p'
① 글자 a 하나 → 바깥을 누른다 — 처음 값 ""
  #   이벤트             key         keyCode isComp  inputType                 data      그때 value
  1   keydown            "a"         65      false   -                         -         ""
  2   keypress           "a"         97      false   -                         -         ""
  3   beforeinput        -           -       false   "insertText"              "a"       ""
  4   textInput          -           -       -       -                         "a"       ""
  5   input              -           -       false   "insertText"              "a"       "a"
  6   keyup              "a"         65      false   -                         -         "a"
  7   change             -           -       -       -                         -         "a"
  8   blur               -           -       -       -                         -         "a"
(exit 0)
```

- ★★ **`keydown`·`keypress`·`beforeinput` 까지는 값이 `""`**, **`input` 에서 `"a"`** 다. **값을 바꾸는 것은 `beforeinput` 과 `input` 사이**다.
- **`beforeinput` 에 `inputType: "insertText"` · `data: "a"`** 가 실려 온다 — **무엇을 넣을지 넣기 전에** 안다.
- ★ **`change` 는 바깥을 눌러 떠날 때** 왔고, **`blur` 보다 먼저**다.
- `keypress` 는 **옛 이벤트**(UI Events 가 「Legacy KeyboardEvent events」로 따로 묶는다)다. `textInput` 은 **Chrome 이 내는 옛 비표준 이벤트**다 — 둘 다 **새 코드가 기댈 곳이 아니다.**

### (2) Backspace · Enter · 떠나기

```text
$ python3 wa20b-cdp.py page wa20b-22-type.html | sed -n '12,17p'
② Backspace — 처음 값 "ab"
  #   이벤트             key         keyCode isComp  inputType                 data      그때 value
  1   keydown            "Backspace" 8       false   -                         -         "ab"
  2   beforeinput        -           -       false   "deleteContentBackward"   null      "ab"
  3   input              -           -       false   "deleteContentBackward"   null      "a"
  4   keyup              "Backspace" 8       false   -                         -         "a"
(exit 0)
```

- **Backspace 는 `keypress` 가 없다** — 글자 키가 아니다. `inputType` 은 **`deleteContentBackward`**, `data` 는 **`null`**.

```text
   keypress 가 온 입력 / 안 온 입력 (이 판의 다섯 시간선)

   왔다      글자 a · 글자 c · Enter
   안 왔다   Backspace · Ctrl+V 붙여넣기 · CDP 조합 흉내

   ★ 「입력이 있었나」는 keypress 가 아니라 beforeinput/input 으로 묻는다
```

```text
$ python3 wa20b-cdp.py page wa20b-22-type.html | sed -n '19,32p'
③ 글자 c → Enter (폼 없음) → 다른 칸으로 옮긴다 — 처음 값 "ab"
  #   이벤트             key         keyCode isComp  inputType                 data      그때 value
  1   keydown            "c"         67      false   -                         -         "ab"
  2   keypress           "c"         99      false   -                         -         "ab"
  3   beforeinput        -           -       false   "insertText"              "c"       "ab"
  4   textInput          -           -       -       -                         "c"       "ab"
  5   input              -           -       false   "insertText"              "c"       "abc"
  6   keyup              "c"         67      false   -                         -         "abc"
  7   keydown            "Enter"     13      false   -                         -         "abc"
  8   keypress           "Enter"     13      false   -                         -         "abc"
  9   beforeinput        -           -       false   "insertLineBreak"         null      "abc"
  10  change             -           -       -       -                         -         "abc"
  11  keyup              "Enter"     13      false   -                         -         "abc"
  12  blur               -           -       -       -                         -         "abc"
(exit 0)
```

- ★★ **Enter 는 `beforeinput`(`insertLineBreak`)까지만 오고 `input` 이 없다** — 한 줄짜리 `<input>` 에는 줄바꿈이 **들어가지 않는다.**
- ★★ **`change` 가 Enter 에서 왔다**(10번째 줄) — 값이 `"abc"` 로 바뀐 뒤 Enter 가 **확정**으로 읽혔다. **그 뒤 떠날 때(12번째 줄 `blur`)는 `change` 가 또 오지 않았다** — 이미 확정됐다.
- HTML 은 「`change` 는 값이 **확정될 때**, 그런 동작이 없으면 **포커스를 잃을 때**」로만 적는다 — **Enter 가 확정이라는 것은 이 판의 관찰**이다.

```text
   change 는 「확정」 때 한 번

   ① a 를 치고 떠난다          input … → change(떠날 때) → blur
   ③ c 를 치고 Enter → 떠난다  input … → change(Enter 때) → … → blur (change 없음)

   ★ input 은 「바뀔 때마다」 · change 는 「확정될 때 한 번」
```

### (3) 붙여넣기

```text
$ python3 wa20b-cdp.py page wa20b-22-type.html | sed -n '34,41p'
④ Ctrl+V 붙여넣기 — 처음 값 ""
  #   이벤트             key         keyCode isComp  inputType                 data      그때 value
  1   keydown            "v"         86      false   -                         -         ""
  2   paste              -           -       -       -                         -         ""
  3   beforeinput        -           -       false   "insertFromPaste"         "붙일글"  ""
  4   textInput          -           -       -       -                         "붙일글"  ""
  5   input              -           -       false   "insertFromPaste"         "붙일글"  "붙일글"
  6   keyup              "v"         86      false   -                         -         "붙일글"
(exit 0)
```

- **`paste` 가 먼저**(클립보드 이벤트), 그다음 `beforeinput`(**`insertFromPaste`**, `data: "붙일글"`) → `input`.
- ★ **`keypress` 가 없다** — Ctrl+V 는 글자를 **치는** 것이 아니다. 키로 걸러 「입력」을 잡는 코드는 **붙여넣기를 놓친다.** `beforeinput`/`input` 의 `inputType` 이 입력의 **출처**를 말해 준다.

### (4) ★★★ CDP 로 흉내 낸 조합 — ㅎ → 하 → 한 → 확정

**언제 쓰나** — 「한글을 치는데 `input` 이 글자마다 여러 번 온다」·「검색창 자동완성이 자모 단위로 튄다」일 때.

**던진 것** — 같은 `<input>` 에 CDP 의 `imeSetComposition` 을 **ㅎ · 하 · 한** 세 번, 그다음 `insertText('한')` 으로 확정했다. ★★ **키 이벤트는 하나도 넣지 않았다** — 조합 호출이 무엇을 만드는지만 본다.

```text
$ python3 wa20b-cdp.py page wa20b-22-type.html | sed -n '43,61p'
⑤ CDP 조합 흉내 — ㅎ → 하 → 한 → 확정 → 바깥을 누른다 — 처음 값 ""
  #   이벤트             key         keyCode isComp  inputType                 data      그때 value
  1   compositionstart   -           -       -       -                         ""        ""
  2   compositionupdate  -           -       -       -                         "ㅎ"      ""
  3   beforeinput        -           -       true    "insertCompositionText"   "ㅎ"      ""
  4   input              -           -       true    "insertCompositionText"   "ㅎ"      "ㅎ"
  5   compositionupdate  -           -       -       -                         "하"      "ㅎ"
  6   beforeinput        -           -       true    "insertCompositionText"   "하"      "ㅎ"
  7   input              -           -       true    "insertCompositionText"   "하"      "하"
  8   compositionupdate  -           -       -       -                         "한"      "하"
  9   beforeinput        -           -       true    "insertCompositionText"   "한"      "하"
  10  input              -           -       true    "insertCompositionText"   "한"      "한"
  11  compositionupdate  -           -       -       -                         "한"      "한"
  12  beforeinput        -           -       true    "insertCompositionText"   "한"      "한"
  13  textInput          -           -       -       -                         "한"      "한"
  14  input              -           -       true    "insertCompositionText"   "한"      "한"
  15  compositionend     -           -       -       -                         "한"      "한"
  16  change             -           -       -       -                         -         "한"
  17  blur               -           -       -       -                         -         "한"
(exit 0)
```

- ★★★ **`keydown`/`keyup` 이 한 줄도 없다** — CDP 의 조합 호출은 **키 이벤트를 만들지 않는다.** 실제 입력기에서는 자모를 칠 때마다 키 이벤트가 온다(UI Events 3.6.5 가 그렇게 요구한다). **이 시간선은 「키 이벤트를 뺀 조합」이다.**
- ★★ **`input` 이 네 번 왔고, 그때마다 `value` 가 `"ㅎ"` → `"하"` → `"한"` → `"한"`** 이다. **조합 중의 `value` 는 확정 전의 중간 글자**다 — 이것을 서버에 보내거나 검색어로 쓰면 **「ㅎ」·「하」로 검색**하게 된다.
- **`isComposing` 이 `true`**, **`inputType` 이 `insertCompositionText`** — 조합 중인 입력임을 이 둘이 말한다.
- ★ **확정(`insertText`) 때도 `insertCompositionText` 가 한 번 더 오고 그다음 `compositionend`** 다.
- ★★ **이 판에서 CDP 흉내의 순서는 `compositionupdate` → `beforeinput` → `input`** 이다. UI Events 3.6.6 의 표는 **`beforeinput` → `compositionupdate` → `input`** 으로 적는다 — **흉내에서 본 순서가 명세 표와 다르다.** 실제 입력기에서 어느 쪽인지는 **못 쟀다.**
- **`change` 는 떠날 때 한 번** — `"한"` 으로.

```text
   ★ 조합 중의 input — 값이 중간 글자를 지나간다 (CDP 흉내 · 키 이벤트 없음)

   compositionstart
   compositionupdate "ㅎ" → beforeinput(isComposing) → input  value "ㅎ"   ← 믿으면 안 되는 값
   compositionupdate "하" → beforeinput(isComposing) → input  value "하"   ← 믿으면 안 되는 값
   compositionupdate "한" → beforeinput(isComposing) → input  value "한"   ← 아직 조합 중
   (확정) compositionupdate "한" → beforeinput → input  value "한"
   compositionend  "한"                                                      ← 여기서부터 믿는다

   고치는 법:  input 리스너에서  if (e.isComposing) return;   +   compositionend 에서 한 번 처리
```

```text
   명세 표(UI Events 3.6.6)와 이 판의 흉내 — 한 번 갱신의 순서

   명세 표        beforeinput → compositionupdate → (DOM 갱신) → input
   이 판(CDP)    compositionupdate → beforeinput → (DOM 갱신) → input

   ★ 실제 입력기에서는 못 쟀다 — 「Chrome 은 이렇다」로 일반화하지 않는다
```

### (5) ★★ 세 칸에서 같은 네 입력 — `<input>` · `<textarea>` · `contenteditable`

**언제 쓰나** — 편집기를 `contenteditable` 로 바꿨더니 Enter 처리가 달라졌을 때.

```html
<!-- wa20b-22-grid.html -->
<!doctype html>
<meta charset="utf-8">
<title>22-grid</title>
<style>input, textarea, div, button { font-size: 20px; width: 300px; display: block; margin: 12px; min-height: 30px; }</style>
<input id="한줄">
<textarea id="여러줄"></textarea>
<div id="편집" contenteditable></div>
<input id="원본" value="붙일글">
<script>
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 대상들 = ['한줄', '여러줄', '편집'];
const 읽기 = el => el.isContentEditable ? el.innerHTML : el.value;
let 판 = null;
for (const id of 대상들) {
  $(id).addEventListener('beforeinput', e => { if (판) 판.bi.push(e.inputType); });
  $(id).addEventListener('input', e => { if (판) 판.in.push(e.inputType); });
}
const 결과 = {};
window.__판 = (id, 입력) => {
  const el = $(id);
  if (el.isContentEditable) el.innerHTML = 'ab'; else el.value = 'ab';
  el.focus();
  const sel = getSelection();
  if (el.isContentEditable) { sel.removeAllRanges(); const r = document.createRange(); r.setStart(el.firstChild, 2); r.collapse(true); sel.addRange(r); }
  else el.setSelectionRange(2, 2);
  판 = { bi: [], in: [] };
  결과[id + '·' + 입력] = 판;
  return 1;
};
window.__적기 = (id, 입력) => { 결과[id + '·' + 입력].끝 = 읽기($(id)); 판 = null; return 1; };
window.__원본고르기 = () => { $('원본').focus(); $('원본').select(); return 1; };
const 키 = (key, code, vk, text, 덧) => [
  ['rawkey', Object.assign({ type: 'keyDown', key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }, text ? { text } : {}, 덧 || {})],
  ['rawkey', Object.assign({ type: 'keyUp', key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }, 덧 ? { modifiers: 덧.modifiers } : {})]];
const 입력들 = {
  '글자 c': 키('c', 'KeyC', 67, 'c'),
  'Backspace': 키('Backspace', 'Backspace', 8, ''),
  'Enter': 키('Enter', 'Enter', 13, '\r'),
  'Ctrl+V': 키('v', 'KeyV', 86, '', { modifiers: 2, commands: ['paste'] }),
};
const 단계 = [['js', '__원본고르기()'], ...키('c', 'KeyC', 67, '', { modifiers: 2, commands: ['copy'] })];
for (const [입력, 키들] of Object.entries(입력들))
  for (const id of 대상들)
    단계.push(['js', `__판(${JSON.stringify(id)}, ${JSON.stringify(입력)})`], ...키들, ['js', `__적기(${JSON.stringify(id)}, ${JSON.stringify(입력)})`]);
window.__단계 = 단계;
window.__끝 = () => {
  const O = [];
  O.push('처음 내용 "ab" · 캐럿은 끝 — 칸 = beforeinput 의 inputType / input 이 왔나 / 끝 내용');
  O.push((padw('입력', 12) + 대상들.map(id => padw(id === '한줄' ? '<input>' : id === '여러줄' ? '<textarea>' : 'contenteditable', 44)).join('')).trimEnd());
  let 갈림 = 0, 모두 = 0;
  for (const 입력 of Object.keys(입력들)) {
    const 칸 = id => { const r = 결과[id + '·' + 입력]; return (r.bi.join(',') || '-') + ' / ' + (r.in.length ? 'input 옴' : 'input 없음') + ' / ' + JSON.stringify(r.끝); };
    O.push((padw(입력, 12) + 대상들.map(id => padw(칸(id), 44)).join('')).trimEnd());
    const 기준 = r => r.bi.join(',') + '|' + r.in.length;
    for (const id of ['여러줄', '편집']) { 모두++; if (기준(결과[id + '·' + 입력]) !== 기준(결과['한줄·' + 입력])) 갈림++; }
  }
  O.push('');
  O.push('<input> 과 inputType 또는 input 유무가 갈린 칸 = ' + 갈림 + ' / ' + 모두);
  return O.join('\n');
};
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-22-grid.html
처음 내용 "ab" · 캐럿은 끝 — 칸 = beforeinput 의 inputType / input 이 왔나 / 끝 내용
입력        <input>                                     <textarea>                                  contenteditable
글자 c      insertText / input 옴 / "abc"               insertText / input 옴 / "abc"               insertText / input 옴 / "abc"
Backspace   deleteContentBackward / input 옴 / "a"      deleteContentBackward / input 옴 / "a"      deleteContentBackward / input 옴 / "a"
Enter       insertLineBreak / input 없음 / "ab"         insertLineBreak / input 옴 / "ab\n"         insertParagraph / input 옴 / "ab<div><br></div>"
Ctrl+V      insertFromPaste / input 옴 / "ab붙일글"     insertFromPaste / input 옴 / "ab붙일글"     insertFromPaste / input 옴 / "ab붙일글"

<input> 과 inputType 또는 input 유무가 갈린 칸 = 2 / 8
(exit 0)
```

- **글자 · Backspace · 붙여넣기는 세 칸이 같다.**
- ★★ **Enter 만 갈린다(2 / 8)** — `<input>` 은 `insertLineBreak` 인데 **`input` 이 없고**, `<textarea>` 는 같은 `insertLineBreak` 로 **`"\n"` 이 들어가고**, `contenteditable` 은 **`insertParagraph`** 로 **`<div><br></div>`** 가 생긴다.
- ★ Input Events 의 표도 **편집 호스트마다** `data`·`getTargetRanges()` 가 다르다고 적는다 — `contenteditable` 은 `data` 대신 **범위**로 말한다.

```text
   Enter 한 번 — 세 칸이 갈리는 자리 (이 판)

   <input>           beforeinput insertLineBreak  →  (input 없음)   "ab"         ← 줄바꿈이 안 들어간다
   <textarea>        beforeinput insertLineBreak  →  input          "ab\n"
   contenteditable   beforeinput insertParagraph  →  input          "ab<div><br></div>"
```

### (6) ★★ `beforeinput` 에서 막기 — 그리고 조합 중에는 못 막는다

**언제 쓰나** — 「숫자만 받는 칸」을 `beforeinput` 에서 거르려 할 때.

```html
<!-- wa20b-22-block.html -->
<!doctype html>
<meta charset="utf-8">
<title>22-block</title>
<style>input { font-size: 20px; width: 300px; display: block; margin: 20px; }</style>
<input id="칸">
<input id="원본" value="붙일글">
<script>
const $ = id => document.getElementById(id);
const 칸 = $('칸');
const O = [];
let 판 = null;
// 막는 자리를 판마다 바꾼다 — 'beforeinput' 또는 'keydown'
칸.addEventListener('beforeinput', e => {
  if (!판) return;
  판.bi.push(e.inputType + '(cancelable=' + e.cancelable + ')');
  if (판.막을곳 === 'beforeinput') { e.preventDefault(); 판.dp.push(e.defaultPrevented); }
});
칸.addEventListener('keydown', e => { if (판 && 판.막을곳 === 'keydown') e.preventDefault(); });
for (const 형 of ['keypress', 'input', 'compositionend'])
  칸.addEventListener(형, e => { if (판) 판.뒤.push(형); });
window.__판 = (제목, 막을곳) => {
  if (판) 판 = null;
  칸.value = ''; 칸.focus();
  판 = { 제목, 막을곳, bi: [], dp: [], 뒤: [] };
  return 1;
};
window.__적기 = () => {
  O.push(판.제목);
  O.push('  beforeinput = ' + (판.bi.join(' · ') || '없음'));
  if (판.막을곳 === 'beforeinput') O.push('  preventDefault 뒤 defaultPrevented = ' + 판.dp.join(' · '));
  O.push('  그 밖에 온 것 = ' + (판.뒤.join(' · ') || '없음'));
  O.push('  끝 value = ' + JSON.stringify(칸.value));
  O.push('');
  판 = null;
  return 1;
};
window.__원본고르기 = () => { $('원본').focus(); $('원본').select(); return 1; };
const 키 = (key, code, vk, text, 덧) => [
  ['rawkey', Object.assign({ type: 'keyDown', key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }, text ? { text } : {}, 덧 || {})],
  ['rawkey', Object.assign({ type: 'keyUp', key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk }, 덧 ? { modifiers: 덧.modifiers } : {})]];
window.__단계 = [
  ['js', '__원본고르기()'], ...키('c', 'KeyC', 67, '', { modifiers: 2, commands: ['copy'] }),
  ['js', '__판("① 글자 a — beforeinput 에서 preventDefault", "beforeinput")'], ...키('a', 'KeyA', 65, 'a'), ['js', '__적기()'],
  ['js', '__판("② Ctrl+V — beforeinput 에서 preventDefault", "beforeinput")'], ...키('v', 'KeyV', 86, '', { modifiers: 2, commands: ['paste'] }), ['js', '__적기()'],
  ['js', '__판("③ 글자 a — keydown 에서 preventDefault", "keydown")'], ...키('a', 'KeyA', 65, 'a'), ['js', '__적기()'],
  ['js', '__판("④ CDP 조합 흉내 ㅎ → 한 → 확정 — beforeinput 에서 preventDefault", "beforeinput")'],
  ['ime', 'ㅎ', 1, 1], ['ime', '한', 1, 1], ['insert', '한'], ['js', '__적기()'],
];
window.__끝 = () => O.join('\n').trimEnd();
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-22-block.html | sed -n '1,11p'
① 글자 a — beforeinput 에서 preventDefault
  beforeinput = insertText(cancelable=true)
  preventDefault 뒤 defaultPrevented = true
  그 밖에 온 것 = keypress
  끝 value = ""

② Ctrl+V — beforeinput 에서 preventDefault
  beforeinput = insertFromPaste(cancelable=true)
  preventDefault 뒤 defaultPrevented = true
  그 밖에 온 것 = 없음
  끝 value = ""
(exit 0)
```

- **글자 · 붙여넣기 — `cancelable: true`, 막으면 `defaultPrevented: true` 이고 값이 안 들어간다**(`input` 도 없다).
- ★ 글자 칸에서 **`keypress` 는 이미 와 있다** — `beforeinput` 은 `keypress` **뒤**다.

```text
$ python3 wa20b-cdp.py page wa20b-22-block.html | sed -n '13,16p'
③ 글자 a — keydown 에서 preventDefault
  beforeinput = 없음
  그 밖에 온 것 = 없음
  끝 value = ""
(exit 0)
```

- ★ **`keydown` 에서 막으면 그 뒤가 전부 사라진다** — `keypress`·`beforeinput`·`input` 이 없다. 막는 자리가 **앞일수록 넓게** 막는다.

```text
$ python3 wa20b-cdp.py page wa20b-22-block.html | sed -n '18,22p'
④ CDP 조합 흉내 ㅎ → 한 → 확정 — beforeinput 에서 preventDefault
  beforeinput = insertCompositionText(cancelable=false) · insertCompositionText(cancelable=false) · insertCompositionText(cancelable=false)
  preventDefault 뒤 defaultPrevented = false · false · false
  그 밖에 온 것 = input · input · input · compositionend
  끝 value = "한"
(exit 0)
```

- ★★★ **조합 중의 `beforeinput` 은 `cancelable: false`** 다. `preventDefault()` 를 불러도 **`defaultPrevented: false`**, **`input` 이 세 번 오고 값은 `"한"`** 이다. **막히지 않았다.**
- ★★ **명세가 그렇게 정한다** — Input Events Level 2 의 표에서 `insertCompositionText` 는 **「beforeinput cancelable: No」** 다. UI Events 3.6.6 도 「대부분의 입력기는 조합 중 갱신의 취소를 지원하지 않는다」고 적는다. **이 판(CDP 흉내)도 그랬다.**
- ★ 그래서 **「`beforeinput` 에서 막으면 된다」는 조합 중에는 거짓**이다 — 조합이 끝난 뒤(`compositionend`) 값을 **고쳐 쓰는** 쪽으로 가야 한다.

```text
   어디서 막으면 무엇이 사라지나

   막는 자리        cancelable        남는 것
   keydown          (키)              keydown 뿐 — 그 뒤 전부 사라진다
   beforeinput      true  (일반)      keydown · keypress · beforeinput — 값은 안 바뀐다
   beforeinput      false (조합 중)   ★ 전부 남는다 — 값이 바뀐다 (명세: 취소 불가)
```

### (7) ★★★ 조합 중의 Enter — 유명한 함정을 흉내로 던진다

**언제 쓰나** — 「한글로 치고 Enter 를 누르면 두 번 보내진다」·「마지막 글자가 빠진 채 보내진다」일 때.

**던진 것** — `keydown` 처리기 둘. **A 는 `e.key === 'Enter'` 만** 보고, **B 는 `e.isComposing || e.keyCode === 229` 를 먼저 거른다.** 폼의 `submit` 은 막고 센다. ★★ **②·③ 의 조합과 그 사이의 키는 전부 CDP 가 넣은 흉내**다.

```html
<!-- wa20b-22-enter.html -->
<!doctype html>
<meta charset="utf-8">
<title>22-enter</title>
<style>input { font-size: 20px; width: 300px; display: block; margin: 20px; }</style>
<form id="폼"><input id="칸" name="q"></form>
<script>
const $ = id => document.getElementById(id);
const 칸 = $('칸');
const O = [];
let 판 = null;
// 처리기 A — key 만 본다 · 처리기 B — isComposing 과 keyCode 229 를 먼저 거른다
칸.addEventListener('keydown', e => {
  if (!판) return;
  판.본키.push(JSON.stringify(e.key) + '/' + e.keyCode + '/isComposing=' + e.isComposing);
  if (e.key === 'Enter') 판.A.push(JSON.stringify(칸.value));
  if (!(e.isComposing || e.keyCode === 229) && e.key === 'Enter') 판.B.push(JSON.stringify(칸.value));
});
$('폼').addEventListener('submit', e => { e.preventDefault(); if (판) 판.제출++; });
window.__판 = 제목 => { 칸.value = ''; 칸.focus(); 판 = { 제목, 본키: [], A: [], B: [], 제출: 0 }; return 1; };
window.__적기 = () => {
  O.push(판.제목);
  O.push('  keydown 이 본 key/keyCode/isComposing = ' + (판.본키.join(' · ') || '없음'));
  O.push('  처리기 A 가 보낸 값 = ' + (판.A.join(' · ') || '없음'));
  O.push('  처리기 B 가 보낸 값 = ' + (판.B.join(' · ') || '없음'));
  O.push('  submit 이벤트 = ' + 판.제출 + '회 · 끝 value = ' + JSON.stringify(칸.value));
  O.push('');
  판 = null;
  return 1;
};
const 엔터 = [
  ['rawkey', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13, text: '\r' }],
  ['rawkey', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 }]];
window.__단계 = [
  ['js', '__판("① 조합 없이 글자 a → Enter")'],
  ['rawkey', { type: 'keyDown', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, text: 'a' }],
  ['rawkey', { type: 'keyUp', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65 }], ...엔터, ['js', '__적기()'],
  ['js', '__판("② CDP 조합 흉내 한 — 조합 중에 Enter 의 keyDown(key=Enter · 13) → 확정 → keyUp")'],
  ['ime', 'ㅎ', 1, 1], ['ime', '한', 1, 1],
  ['rawkey', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 }],
  ['insert', '한'],
  ['rawkey', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, nativeVirtualKeyCode: 13 }],
  ['js', '__적기()'],
  ['js', '__판("③ CDP 조합 흉내 한 — 조합 중에 keyDown(key=Process · 229) 를 넣으면")'],
  ['ime', 'ㅎ', 1, 1],
  ['rawkey', { type: 'keyDown', key: 'Process', code: 'KeyS', windowsVirtualKeyCode: 229, nativeVirtualKeyCode: 229 }],
  ['ime', '한', 1, 1], ['insert', '한'],
  ['js', '__적기()'],
  ['js', '__판("④ 조합이 끝난 뒤 한 번 더 Enter")'], ['ime', '한', 1, 1], ['insert', '한'], ...엔터, ['js', '__적기()'],
];
window.__끝 = () => O.join('\n').trimEnd();
</script>
```

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '1,5p'
① 조합 없이 글자 a → Enter
  keydown 이 본 key/keyCode/isComposing = "a"/65/isComposing=false · "Enter"/13/isComposing=false
  처리기 A 가 보낸 값 = "a"
  처리기 B 가 보낸 값 = "a"
  submit 이벤트 = 1회 · 끝 value = "a"
(exit 0)
```

- 대조군 — 조합 없이 `a` → Enter. **A·B 둘 다 보내고, `submit` 1회**(Enter 의 암묵 제출 — [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md)의 (8)).

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '7,11p'
② CDP 조합 흉내 한 — 조합 중에 Enter 의 keyDown(key=Enter · 13) → 확정 → keyUp
  keydown 이 본 key/keyCode/isComposing = "Enter"/13/isComposing=true
  처리기 A 가 보낸 값 = "한"
  처리기 B 가 보낸 값 = 없음
  submit 이벤트 = 0회 · 끝 value = "한"
(exit 0)
```

- ★★★ **조합 중에 넣은 Enter 의 `keydown` 에 Chrome 이 `isComposing: true` 를 달았다** — 넣은 것은 `key`/`keyCode` 뿐이고 `isComposing` 은 **Chrome 이 조합 상태를 보고 정한 값**이다. **이 칸이 흉내 안에서도 진짜로 잰 것**이다.
- ★★ **A 는 보냈다**(`"한"`) — `key` 가 `"Enter"` 이기 때문이다. **B 는 안 보냈다.** 조합을 확정하려고 누른 Enter 를 **A 는 「보내기」로 읽는다** — 그 뒤 확정된 글자가 또 들어오면 **두 번 보내기·빠진 글자**의 모양이 된다.
- **`submit` 은 0회** — 이 흉내에서는 Enter 에 `text` 를 안 실어 `keypress` 가 없었다. 실제 입력기에서 **폼이 제출되는지는 못 쟀다.**

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '13,17p'
③ CDP 조합 흉내 한 — 조합 중에 keyDown(key=Process · 229) 를 넣으면
  keydown 이 본 key/keyCode/isComposing = "Process"/229/isComposing=true
  처리기 A 가 보낸 값 = 없음
  처리기 B 가 보낸 값 = 없음
  submit 이벤트 = 0회 · 끝 value = "한"
(exit 0)
```

- ★★ **조합 중에 `key: "Process"` · `keyCode: 229` 를 넣으면 페이지는 그 값을 그대로 본다** — 그리고 `isComposing: true`. **A·B 둘 다 안 보낸다.**
- ★★★ **「조합 중 `keydown` 의 `key` 가 `"Process"`, `keyCode` 가 229」는 이 편이 넣은 값이다** — Chrome 이 **바꿔 적은 것이 아니다.** ②에서 `Enter`/`13` 을 넣었을 때 **그대로 `Enter`/`13` 이 보인 것**이 그 증거다. 229 는 UI Events 7.3.1 의 모형대로 **입력기가 키를 처리 중일 때 플랫폼 층이 붙이는 값**이고, CDP 는 **그 층 아래로** 넣는다. **실제 입력기에서 어떤 값이 오는지는 못 쟀다.**

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '19,23p'
④ 조합이 끝난 뒤 한 번 더 Enter
  keydown 이 본 key/keyCode/isComposing = "Enter"/13/isComposing=false
  처리기 A 가 보낸 값 = "한"
  처리기 B 가 보낸 값 = "한"
  submit 이벤트 = 1회 · 끝 value = "한"
(exit 0)
```

- 조합이 **끝난 뒤** Enter 는 `isComposing: false` — A·B 둘 다 보내고 `submit` 1회.

```text
   ★ 조합 중 Enter 의 함정 — 가드 하나

   처리기 A:  if (e.key === 'Enter') 보내기();                         ← 조합 확정용 Enter 에도 반응
   처리기 B:  if (e.isComposing || e.keyCode === 229) return;          ← 조합 중이면 거른다
              if (e.key === 'Enter') 보내기();

   이 판(CDP 흉내)에서 쟀다: 조합 중 keydown 의 isComposing = true (Chrome 이 붙였다)
   이 판에서 못 쟀다:       실제 입력기의 key("Process"?) · keyCode(229?) — 넣은 값이 그대로 보일 뿐

   ★ keyCode === 229 도 같이 보는 이유: 조합을 「여는」 첫 keydown 은 isComposing 이 false 다(UI Events 3.6.5 표)
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   키            keydown(e.key · e.code · e.isComposing · e.keyCode)   keyup     (옛) keypress
   예고          beforeinput(e.inputType · e.data · e.getTargetRanges())   막을 수 있다(조합 중 제외)
   결과          input(e.inputType · e.data · e.isComposing)               값이 바뀐 뒤
   확정          change                                                    Enter · 떠날 때
   조합          compositionstart · compositionupdate(e.data) · compositionend(e.data)
   클립보드      paste · copy · cut

   조합 가드
     el.addEventListener('input', e => { if (e.isComposing) return; 처리(el.value); });
     el.addEventListener('compositionend', () => 처리(el.value));
```

### 어디서 헷갈리나

- **`keydown` 에서 `value` 를 읽으면 방금 친 글자가 없다** — 값은 `input` 에서 바뀐다((1)).
- **`input` 은 「확정」이 아니다** — 조합 중에는 중간 글자로도 온다((4)).
- **`keypress` 는 옛 이벤트**다 — Backspace·붙여넣기에는 없다((2)·(3)).

## 어디서 틀리나

### 1. `keydown` 에서 `el.value` 로 방금 친 글자를 읽는다

**아직 안 들어갔다**((1)). `input` 에서 읽거나, 넣을 글자는 `beforeinput` 의 `data` 로 본다.

### 2. `input` 마다 검색 요청을 보낸다 — 한글에서

**조합 중의 중간 글자(`ㅎ`·`하`)로 요청이 간다**((4)). `isComposing` 이면 건너뛰고 `compositionend` 에서 보낸다.

### 3. 채팅 입력에서 `keydown` 의 `e.key === 'Enter'` 만 보고 보낸다

**조합을 확정하려는 Enter 에도 반응한다**((7)). `e.isComposing || e.keyCode === 229` 를 먼저 거른다.

### 4. `beforeinput` 에서 막아 입력을 거른다 — 한글·일본어에서도

**조합 중에는 `cancelable: false` 라 못 막는다**((6) — 명세). 조합이 끝난 뒤 값을 고친다.

### 5. `keypress` 로 「입력이 있었나」를 잡는다

**붙여넣기·Backspace·조합에는 `keypress` 가 없다**((2)·(3)·(4)). `beforeinput`/`input` 을 쓴다.

### 6. `change` 를 「바뀔 때마다」로 쓴다

**확정될 때 한 번**이다((2)). 실시간 반응은 `input`.

### 7. `<input>` 에서 짠 Enter 처리를 `contenteditable` 에 그대로 쓴다

**`inputType` 이 `insertParagraph` 로 바뀌고 DOM 이 달라진다**((5)).

### 8. CDP·자동화 도구로 한글 입력을 테스트하고 「실제로도 이렇다」고 믿는다

**흉내는 키 이벤트를 안 만들고, 넣은 키 값을 그대로 보여 준다**((4)·(7)). 실제 입력기는 **사람이 쳐 보는** 수밖에 없다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `keydown` → `beforeinput` → `input` → `keyup` 순서 · `beforeinput` 에서 값이 아직 그대로인 것 | **명세**(UI Events · Input Events) · 이 판도 그랬다((1)) |
| 조합 중 `beforeinput` 이 **취소 불가**인 것 | ★ **명세**(Input Events Level 2 의 `inputType` 표 — `insertCompositionText` 는 cancelable No) · 이 판(CDP 흉내)도 `false` 였다((6)) |
| 조합 중 키 이벤트에 **`isComposing: true`** | **명세**(UI Events 3.6.5 — MUST) · 이 판은 **흉내 안에서** 그 값을 붙였다((7)) |
| 조합 중 `keydown` 의 `keyCode` 가 **229** | ★ **UI Events 7.3.1(비규범 절)의 모형** — **플랫폼 층의 일**이다. ★★ **이 편은 못 쟀다**(넣은 값이 그대로 보인다) |
| `compositionupdate` 와 `beforeinput` 의 **선후** | ★ **명세 표와 이 판의 흉내가 다르다**((4)) — 실제 입력기는 **못 쟀다** |
| `change` 가 **떠날 때** 오는 것 | **명세**(HTML — 확정이 없으면 포커스를 잃을 때) |
| `change` 가 **Enter 에서도** 오는 것 | ★ **이 판의 관찰** — HTML 은 「확정될 때」로만 적는다 |
| `textInput` 이벤트 | ★ **구현.** Chrome 의 옛 비표준 이벤트다 |
| `keypress` | ★ UI Events 가 **옛(Legacy) 이벤트**로 묶는다 |
| CDP 의 조합 흉내가 **키 이벤트를 안 만드는** 것 | ★ **도구의 성질**(CDP — experimental · 「emulates」) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 값이 바뀔 때마다 반응 | `input` + **`isComposing` 가드** | `keydown`·`keypress` 에서 `value` 읽기 |
| 확정된 값으로 한 번 | `change` | `input` 으로 흉내 |
| 넣기 **전에** 거르기(영문·숫자) | `beforeinput` + `preventDefault()` | 조합 중에도 된다고 믿기 |
| 한글·일본어 칸 | `compositionend` 에서 처리 | 조합 중 `input` 값으로 요청 |
| 단축키(Enter 로 보내기) | `keydown` + `e.isComposing \|\| e.keyCode === 229` 가드 | `e.key === 'Enter'` 만 |
| 입력의 출처(붙여넣기 등) 가르기 | `e.inputType` | 키 코드로 추측 |

## 핵심 문장

1. **값은 `beforeinput` 과 `input` 사이에서 바뀐다** — `keydown` 에서는 방금 친 글자가 없다.
2. **`change` 는 확정 때 한 번**이다 — 떠날 때, 이 판에서는 Enter 에서도.
3. **조합 중의 `input` 은 중간 글자를 지나간다** — `isComposing` 으로 거르고 `compositionend` 에서 처리한다.
4. **조합 중 `beforeinput` 은 명세상 취소할 수 없다** — 막기가 아니라 고쳐 쓰기로 간다.
5. **조합 중 Enter 는 `isComposing: true` 로 온다** — `e.key` 만 보는 처리기가 거기서 오작동한다.
6. **이 편의 조합은 CDP 의 흉내다** — 키 이벤트가 없고 넣은 키 값이 그대로 보인다. **실제 입력기는 못 쟀다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 22번)
- [17번 주제](../17-stoppropagation-vs-preventdefault/2-summary.md) — 키보드 Space/Enter 가 `click` 을 만드는 것 · Enter 의 암묵 제출. **여기의 `keydown` 뒤에 그쪽이 선다**
- [16번 주제](../16-event-propagation-phases/2-summary.md) — 순서 로그를 읽는 법
- [19번 주제](../19-passive-and-scroll/2-summary.md) — 진짜 입력과 합성 입력이 갈린 칸들(같은 하네스)
- [20번 주제](../20-listener-lifetime/2-summary.md) — 하네스 전문(키·조합 단계)
- [23번 주제](../23-pointer-events/2-summary.md) — 같은 「입력」 묶음의 포인터 쪽
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **22번** — `<input>` 텍스트 계열 타입 지도(마크업 쪽 정본 · 아직 폴더 없음)

## 용어 풀이

- **`beforeinput`** — 값이 바뀌기 **직전**의 이벤트. `inputType`·`data` 로 무엇을 넣을지 알린다. 대부분 막을 수 있다.
- **`inputType`** — 입력의 종류(`insertText`·`deleteContentBackward`·`insertFromPaste`·`insertCompositionText` …).
- **`change`** — 값이 **확정**됐을 때 한 번.
- **IME(입력기)** — 자모·가나를 모아 글자를 만드는 프로그램. 한글·일본어·중국어 입력에 쓴다.
- **조합(composition)** — 입력기가 글자를 만드는 중인 상태. 그동안의 글자는 바뀔 수 있다.
- **`isComposing`** — 이 키·입력 이벤트가 조합 중에 났나.
- **`keyCode` 229** — 입력기가 키를 처리 중일 때 옛 모형이 붙이는 값. 이 편은 **실제 값을 못 쟀다.**
- **CDP 의 조합 흉내** — `Input.imeSetComposition`·`Input.insertText`. 입력기 없이 조합 결과를 렌더러에 넣는다. 키 이벤트는 안 만든다.
- **한 번 타이핑의 시간선** — 이벤트를 한 줄씩, 그때의 `value` 와 함께 적은 것. 이 편의 본체.

## 더 들어가면

- **`getTargetRanges()`** 로 `contenteditable` 의 편집 범위를 읽는 것은 던지지 않았다.
- **`Input.dispatchKeyEvent` 의 `commands`** 는 붙여넣기에만 썼다 — 실행 취소(`historyUndo`) 등은 던지지 않았다.
- **실제 입력기**로 재려면 창이 있는 Chrome 과 OS 입력기가 필요하다 — 이 하네스 밖이다.
