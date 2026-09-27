# web-api/22 — 입력 이벤트의 순서: `keydown`→`beforeinput`→`input`→`change` 와 IME 조합 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.\
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 받은 것**이다 — 키는 **CDP 로 넣은 진짜 입력**, 조합은 **CDP 의 흉내**(`Input.imeSetComposition`·`Input.insertText` — CDP 가 experimental 로 표시)다. 명령은 블록마다 배너로 실려 있다.\
> 규칙은 [W3C UI Events](https://w3c.github.io/uievents/) 3.6.5 · 3.6.6 · 7.3.1 · [W3C Input Events Level 2](https://w3c.github.io/input-events/) 의 `inputType` 표 · [HTML — The input element](https://html.spec.whatwg.org/multipage/input.html) 의 Common event behaviors 로 접지했다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> ★★★ **실제 입력기(한글·일본어 IME)의 이벤트 순서는 못 쟀다.**

| 안 흔들리는 칸 | 흔들리는 칸 · 못 잰 칸 |
|---|---|
| 다섯 시간선 · 12칸 격자 · 막기 네 칸 · Enter 처리기 네 칸 | ★★ **못 잰 것** — 실제 입력기의 순서 · 조합 중 `keydown` 의 `key`/`keyCode` |
| 캡처를 세 판 돌려 **한 글자도 같았다** | Chrome 판 번호 |

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 여덟 줄 — 값은 `input` 에서 바뀌고, `change` 가 `blur` 보다 먼저

**출력**

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

**왜 그런가**

- **`keydown` → `keypress` → `beforeinput` → `textInput` → `input` → `keyup` → `change` → `blur`.**
- ★ **`"a"` 를 처음 보는 것은 `input`** 이다. `beforeinput` 까지는 **넣기 전**이라 `""` — 대신 `data: "a"` 로 **무엇을 넣을지**는 안다.
- **`change` 가 `blur` 보다 먼저**다 — 떠나면서 먼저 확정하고 그다음 포커스를 잃었다.

### 2. `keypress` 는 Enter 에만 · Enter 는 `input` 없이 `change` 를 낸다

**출력**

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

**왜 그런가**

- **`keypress`** — ② Backspace **없음** · ③ c 와 Enter **있음** · ④ Ctrl+V **없음**. `keypress` 는 **글자를 치는 키와 Enter** 에서만 오는 옛 이벤트다.
- ★ **③ Enter 는 `beforeinput`(`insertLineBreak`)만 있고 `input` 이 없다** — 한 줄 칸에는 줄바꿈이 안 들어간다. **`change` 는 Enter 에서**(10번째 줄) 왔고, **떠날 때(`blur`)는 또 오지 않았다.**
- **④ `paste` → `beforeinput`(`insertFromPaste`, `data: "붙일글"`) → `textInput` → `input`.**

### 3. 키 이벤트 없이 `input` 네 번 — 값이 중간 글자를 지나간다

**출력**

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

**왜 그런가**

- ★★ **키 이벤트는 한 줄도 없다** — CDP 의 조합 호출은 **키 이벤트를 만들지 않는다.** 실제 입력기라면 UI Events 3.6.5 대로 조합 중에도 `keydown`/`keyup` 이 와야 한다.
- **`input` 네 번 · `value` 는 `"ㅎ"` → `"하"` → `"한"` → `"한"`.** 넷 다 `isComposing: true` · `insertCompositionText`.
- ★ **이 판(흉내)의 순서는 `compositionupdate` → `beforeinput` → `input`** 이다. UI Events 3.6.6 의 표는 **`beforeinput` → `compositionupdate` → `input`** — **명세 표와 다르다.** 실제 입력기에서 어느 쪽인지는 **못 쟀다.**

### 4. Enter 만 갈린다 — 2 / 8

**출력**

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

**왜 그런가**

- 글자 · Backspace · 붙여넣기는 세 칸이 같다.
- **Enter** — `<input>` 은 `insertLineBreak` 인데 **`input` 없음**, `<textarea>` 는 같은 `insertLineBreak` 로 **`"\n"`**, `contenteditable` 은 **`insertParagraph`** 로 `<div><br></div>`.

### 5. 조합 중에는 못 막는다

**출력**

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

```text
$ python3 wa20b-cdp.py page wa20b-22-block.html | sed -n '13,16p'
③ 글자 a — keydown 에서 preventDefault
  beforeinput = 없음
  그 밖에 온 것 = 없음
  끝 value = ""
(exit 0)
```

```text
$ python3 wa20b-cdp.py page wa20b-22-block.html | sed -n '18,22p'
④ CDP 조합 흉내 ㅎ → 한 → 확정 — beforeinput 에서 preventDefault
  beforeinput = insertCompositionText(cancelable=false) · insertCompositionText(cancelable=false) · insertCompositionText(cancelable=false)
  preventDefault 뒤 defaultPrevented = false · false · false
  그 밖에 온 것 = input · input · input · compositionend
  끝 value = "한"
(exit 0)
```

**왜 그런가**

- **① 글자 · ② 붙여넣기** — `cancelable: true` · `defaultPrevented: true` · 값 `""`. ①에는 `keypress` 가 **이미 와 있다**(`beforeinput` 이 그 뒤다).
- **③ `keydown` 에서 막기** — 그 뒤가 **전부** 없다. 값 `""`.
- ★★★ **④ 조합 흉내 — `cancelable: false` 가 세 번, `defaultPrevented: false`, `input` 세 번, 값 `"한"`.** **막히지 않았다.** Input Events Level 2 의 표가 `insertCompositionText` 를 **「beforeinput cancelable: No」** 로 정한다.

### 6. A 는 조합 중 Enter 에 반응하고 B 는 거른다

**출력**

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '1,5p'
① 조합 없이 글자 a → Enter
  keydown 이 본 key/keyCode/isComposing = "a"/65/isComposing=false · "Enter"/13/isComposing=false
  처리기 A 가 보낸 값 = "a"
  처리기 B 가 보낸 값 = "a"
  submit 이벤트 = 1회 · 끝 value = "a"
(exit 0)
```

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '7,11p'
② CDP 조합 흉내 한 — 조합 중에 Enter 의 keyDown(key=Enter · 13) → 확정 → keyUp
  keydown 이 본 key/keyCode/isComposing = "Enter"/13/isComposing=true
  처리기 A 가 보낸 값 = "한"
  처리기 B 가 보낸 값 = 없음
  submit 이벤트 = 0회 · 끝 value = "한"
(exit 0)
```

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '13,17p'
③ CDP 조합 흉내 한 — 조합 중에 keyDown(key=Process · 229) 를 넣으면
  keydown 이 본 key/keyCode/isComposing = "Process"/229/isComposing=true
  처리기 A 가 보낸 값 = 없음
  처리기 B 가 보낸 값 = 없음
  submit 이벤트 = 0회 · 끝 value = "한"
(exit 0)
```

```text
$ python3 wa20b-cdp.py page wa20b-22-enter.html | sed -n '19,23p'
④ 조합이 끝난 뒤 한 번 더 Enter
  keydown 이 본 key/keyCode/isComposing = "Enter"/13/isComposing=false
  처리기 A 가 보낸 값 = "한"
  처리기 B 가 보낸 값 = "한"
  submit 이벤트 = 1회 · 끝 value = "한"
(exit 0)
```

**왜 그런가**

- **① 조합 없음** — `"Enter"/13/false`, A·B 둘 다 `"a"`, `submit` 1회.
- ★★ **② 조합 중 Enter** — `"Enter"/13/isComposing=true`. **A 만 `"한"` 을 보냈다.** `submit` 0회(흉내의 Enter 에 글자를 안 실어 `keypress` 가 없었다).
- ★★★ **②의 `isComposing: true` 는 Chrome 이 정한 값**이다 — 이 편은 `key`/`keyCode` 만 넣었다. **③의 `"Process"`/229 는 이 편이 넣은 값**이다 — ②에서 `Enter`/13 을 넣었더니 **그대로 `Enter`/13 이 보였으므로**, Chrome 이 키 값을 조합 상태에 맞춰 **바꿔 적지 않는다**는 것까지가 이 판의 사실이다.
- **④ 조합이 끝난 뒤** — `isComposing=false`, A·B 둘 다 보내고 `submit` 1회.

### 7. 중간 글자로 요청이 간다

- **`ㅎ`·`하`·`한` 으로 세 번**(확정까지 네 번) 요청이 간다(문항 3).
- 가드 —

```text
   el.addEventListener('input', e => { if (e.isComposing) return; 검색(el.value); });
   el.addEventListener('compositionend', () => 검색(el.value));
```

### 8. `input` 은 바뀔 때마다, `change` 는 확정 때 한 번

- **`input` 은 값이 바뀔 때마다**, **`change` 는 값이 확정될 때 한 번**이다.
- **HTML 이 정한 것** — 「확정될 때, 확정 동작이 없으면 **포커스를 잃을 때**」. **이 판의 관찰** — 떠날 때(문항 1)와 **Enter 에서도**(문항 2의 ③). Enter 가 확정이라는 것은 **HTML 이 적지 않은, Chrome 의 동작**이다.

### 9. 흉내는 키를 안 만들고, 넣은 키를 그대로 보인다

- **키 이벤트**가 없다(문항 3). UI Events 3.6.5 의 표는 조합을 여는 `keydown`, 조합 중의 `keyup`(`isComposing: true`), 조합을 닫는 `keydown` 을 요구한다. 순서도 3.6.6 의 표와 다르다.
- ★★ **적을 수 있는 것** — 조합 중에 **넣은** 키에 Chrome 이 **`isComposing: true` 를 붙인다**(②). **적을 수 없는 것** — **실제 입력기에서 `key`·`keyCode` 가 무엇으로 오나.** ②(`Enter`/13 → 그대로)와 ③(`Process`/229 → 그대로)을 나란히 두면, **보인 값이 곧 넣은 값**이라 **229 가 Chrome 의 것인지 가를 수 없다.** UI Events 7.3.1(비규범 절)은 229 를 「입력기가 키를 처리 중일 때」의 값으로 모형화한다 — **입력기와 플랫폼 층의 일**이고, CDP 는 그 층 아래로 넣는다.
- **재려면** — 창이 있는 Chrome 에 **OS 입력기**(IBus·Windows IME 등)를 붙여 **사람이 쳐야** 한다.

### 10. `keypress` 는 명세의 옛 이벤트, `textInput` 은 Chrome 의 것

- **`keypress`** — UI Events 가 **「Legacy KeyboardEvent events」** 로 따로 묶는 옛 이벤트. **`textInput`** — **Chrome 의 비표준 옛 이벤트**(이 판에서 `input` 바로 앞에 왔다).
- `keypress` 로 잡으면 **Backspace · 붙여넣기 · 조합**을 놓친다(문항 2·3).

### 11. 다른 주제와 잇기

- **17번 주제의 암묵 제출** — 문항 6의 **①과 ④** 에서 `submit` 1회로 보였다. **②** 에서는 안 보였다 — 흉내의 Enter 에 글자(`text`)를 안 실었더니 `keypress` 도 `submit` 도 없었다 — 둘의 인과는 이 편이 가르지 않았다. **실제 입력기에서 조합 확정 Enter 가 제출하는지는 못 쟀다.**
- **HTML 22번** — 텍스트 계열 `<input>` 타입마다 달라지는 것(모바일 키보드·기본 검증·자동완성)은 **마크업 쪽**, 여기는 **그 칸에서 나는 이벤트의 순서**다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 크로스 브라우저 이식성은 이 문서의 주장 범위 밖이다.

★ **키** — `Input.dispatchKeyEvent` 로 `keyDown`(글자면 `text` 를 싣는다)과 `keyUp` 을 따로 보냈다. **Ctrl+C/V** 는 `modifiers: 2` 에 **편집 명령 `copy`·`paste`** 를 실었다(headless 의 클립보드로 실제로 붙었다).\
★★ **조합** — `Input.imeSetComposition`(ㅎ·하·한)과 `Input.insertText`(확정). **CDP 가 experimental 로 표시하고 「흉내」라고 적는 명령**이다. 실제 입력기는 **안 붙였다 — 이 환경에서 못 붙인다.**\
★ **하네스** — [20번 주제](../20-listener-lifetime/2-summary.md)의 (1)에 전문이 있다.

```sh
# wa20b-22-rerun.sh
# 이 편의 블록을 다시 던지는 법 — 스크래치패드의 src 에서
# 키는 CDP Input.dispatchKeyEvent(진짜 입력) · 조합은 Input.imeSetComposition/insertText(CDP 의 흉내)
python3 wa20b-cdp.py page wa20b-22-type.html
python3 wa20b-cdp.py page wa20b-22-grid.html
python3 wa20b-cdp.py page wa20b-22-block.html
python3 wa20b-cdp.py page wa20b-22-enter.html
```

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| 시간선 다섯 판(글자·Backspace·Enter·붙여넣기·조합) | 캡처 3판 | 동작 방식 (1)\~(4) · A1\~A3 |
| 세 칸 × 네 입력 | 캡처 3판 | 동작 방식 (5) · A4 |
| 막기 네 칸 · Enter 처리기 네 칸 | 캡처 3판 | 동작 방식 (6)·(7) · A5 · A6 |

**구현에 달린 항목**

| 항목 | 값 | 왜 다시 찍나 |
|---|---|---|
| `change` 가 Enter 에서 오는 것 | 옴 | HTML 이 적지 않은 동작이다 |
| 흉내에서 `compositionupdate` 와 `beforeinput` 의 선후 | `compositionupdate` 먼저 | 명세 표와 다르다 |
| `textInput` | 옴 | Chrome 의 비표준 이벤트다 |

**안 돌려 본 것 · 못 잰 것** — ① Firefox·Safari(엔진이 없다). ② ★★ **실제 입력기**(못 잰다 — 도구가 입력기 아래로 넣는다). ③ 모바일 가상 키보드. ④ 실행 취소·맞춤법 고침의 `inputType`.
