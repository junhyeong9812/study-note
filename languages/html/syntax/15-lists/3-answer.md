# html/syntax/15 — 목록: `ul`/`ol`(`start`·`reversed`·`value`)/`dl` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스(`html13b-cdp.py`·`capture.sh`)는 [13번 주제의 3-answer.md](../13-phrasing-semantics/3-answer.md) `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다.** WebKit 은 **미실행**이다.
> ★★★ **번호는 창 ⑦ 에만 있다**(A1·A2).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `0 1 2` · `-2 -1 0` · `3 2 1` · `10 9 8`, 셋째는 `8` 과 `6`

**출력**

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

**왜 그런가**

- **`start` 가 첫 번호**다 — 0 도 음수도 된다.
- **`reversed` 는 항목 수(3)에서 시작해 내려간다.** `start="10"` 이 있으면 10 에서.
- ★★ **`value="7"` 은 그 항목을 7 로 만들고 뒤를 끌고 간다** — 올려 세면 `8`, 내려 세면 `6`.
- **`start="삼"` 은 정수가 아니라 없는 것처럼** — `1 2 3`.
- **`type="I" start="4"` 는 `IV`** 부터다.

### 2. `ol.start` 는 1, `li.value` 는 0 — 같은 칸 = 4 / 27, 전부 우연

**출력** — 1번과 같은 실행이다(위 블록의 `ol.start`·`li.value`·`::marker`·`innerText` 열). 끝부분이 아래다.

```text
$ python3 html13b-cdp.py page html13b-15-num.html | sed -n '15,17p'
DOM 이 번호를 아나 — li.value 가 표지의 번호와 같은 칸을 센다(숫자 표지인 ol 만)
  같은 칸 = s0/1 (0) · sneg/3 (0) · val/2 (7) · revval/2 (7)
같은 칸 = 4 / 27
(exit 0)
```

**왜 그런가**

- ★★ **`rev` 의 `ol.start` 는 `1`** — 첫 표지는 `3.` 인데도. IDL 이 `ReflectDefault=1` 이다(A5).
- **`base` 의 `li.value` 는 `0,0,0`** — `value` 속성이 없다.
- **`::marker` 계산값은 전부 `normal`**, **`innerText` 는 `"가\n나\n다"`** 다. 번호가 **어느 쪽에도 없다.**
- ★★★ **같은 칸 4 개는 전부 우연이다.** `s0/1`·`sneg/3` 은 번호가 **0** 이라 기본값 0 과 겹쳤고, `val/2`·`revval/2` 는 **`value="7"` 을 손으로 쓴 칸**이다. `li.value` 는 번호가 아니라 **속성의 거울**이다.

### 3. 파서는 목록을 안 고친다 — 생략한 끝 태그만 닫는다

**출력**

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

**왜 그런가**

- ★★★ **`<div>`·글자·`<p>` 가 `<ul>` 안에 그대로 있다.** 콘텐츠 모델을 어겼지만 **옮기지도 감싸지도 않는다.**
- ★ **`#생략` 은 닫혔다** — `dt`·`dd` 끝 태그는 명세가 **생략 가능**으로 정한 것이라 파서가 채운다. 이 파일에서 파서가 한 일은 **이것 하나**다.
- **`#거꾸로` 는 그대로** — 순서는 파서가 모른다.

### 4. `list` 는 남고 표지만 사라진다 — `div` 는 트리에서 빠진다

**출력**

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

**왜 그런가**

- ★★ **`#없앰` 에 `list` 가 남았다.** 사라진 것은 **`ListMarker` 노드**뿐이다(Chrome 151 의 관찰).
- ★★ **`#묶음` 의 `div` 는 트리에서 사라졌다** — `term`·`definition` 이 `DescriptionList` 바로 아래로 평평하게 붙었다.
- ★ **`dl` 은 `DescriptionList`** 로 찍혔다 — HTML-AAM 은 **`list`** 다. Chrome 의 **내부 이름**이다. `dt` → `term`, `dd` → `definition` 은 HTML-AAM 과 같다.
- **목록 밖의 `<li>` 도 `listitem` + 표지 `• `** — 구현의 관찰이다.
- ★ **`#섞임` 은 목록 안에 `generic`·`StaticText`·`paragraph` 가 `listitem` 과 섞여 들어갔다.**

### 5. 설계다 — IDL 은 `ReflectDefault=1`, 시작 값은 따로 센다

- 명세 시작 값 — 「`start` 가 있고 정수로 파싱되면 그 값. **없고 `reversed` 가 있으면 소유한 `li` 의 수.** 아니면 1」.
- `start` IDL 은 **`[CEReactions, Reflect, ReflectDefault=1] attribute long start`** 다. 속성을 비추되 **없으면 1**.
- ★ **그래서 불일치는 설계다.** IDL 은 **입력(속성)** 을 비추고, 시작 값은 **표지를 셀 때** 계산한다. 번호를 스크립트로 얻는 API 는 **명세에 없다.**

### 6. `value` 는 「세던 수」를 갈아 끼운다

- 명세 서수 값 알고리즘 — 「`numbering` 을 시작 값으로 두고, 항목마다 ① **`value` 가 있고 정수면 `numbering` 을 그 값으로 바꾼다** ② 그 항목의 서수 값은 `numbering` ③ `reversed` 면 1 빼고 아니면 1 더한다」.
- **거꾸로 목록에서 `value="7"` 뒤가 6** 인 이유 — ③ 에서 **1 을 뺀다.** 끌고 가는 방향이 목록의 방향이다.
- 명세 — 「`value` IDL 은 서수 값에 **직접 대응하지 않는다. 속성을 비출 뿐이다.** `1, 3, 4` 로 찍히는 목록에서 IDL 은 `0, 3, 0` 을 돌려준다」.

### 7. Chrome 은 남겼다 — Safari 는 미실행

- **남았다**(A4).
- **못 적는다.** 이 머신에 WebKit 이 없다 — **「못 잰 것」(제3의 상태)** 이다. 「지운다」는 **알려진 사례**로 들은 것이지 이 문서의 관찰이 아니다.
- **「Chrome 151 에서 이렇다」로 적고, 이식성은 Baseline·명세로만** 말한다 — 이 동작은 **명세가 정하지 않았다**(HTML-AAM 의 `ul`·`ol`·`li` 줄에 `list-style` 조건이 없다 — 세 줄을 읽었다).

### 8. 순서가 뜻인가 · 이름 — 값 묶음

- **아니다.** `ol` 은 「**순서를 바꾸면 뜻이 바뀐다**」, `ul` 은 「**바꿔도 안 바뀐다**」를 주장한다. 점과 숫자는 CSS 로 바꿀 수 있다.
- **`dl` 은 이름 — 값 묶음**(용어·설명, 키·값)이다. ★ **`div` 묶음은 안 넘어간다**(A4) — 트리에는 **순서**로만 남는다.

### 9. 알고리즘은 명세, 이름은 구현, 파서의 무반응은 관찰

- **서수 값 알고리즘 — 명세(HTML).**
- **`DescriptionList`·`ListMarker` — 구현(Chrome 의 내부 역할 이름).**
- **`<div>` 를 안 고친 것 — 이 판의 관찰**이다. 파서가 트리를 고치는 자리의 규칙은 [03번 주제](../03-parser-and-error-recovery/2-summary.md)가 정본이고, ★ **이 배치는 파서 명세의 해당 절을 열어 보지 않았다** — 그래서 「명세가 안 고치게 정했다」까지는 적지 않는다. 확인한 것은 **콘텐츠 모델이 「`li` 와 스크립트 지원 요소만」이라는 것**(명세)과 **이 판이 어겨진 트리를 그대로 두었다는 것**(관찰) 둘이다.

### 10. 정본 경계

- **`ul` 의 콘텐츠 모델** — [05번 주제](../05-content-categories-and-models/2-summary.md).
- **`::marker`·`counter()`** — CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **13번**([의사 요소와 생성 콘텐츠](../../../css/syntax/13-pseudo-elements-and-generated-content/2-summary.md)).
- **`role="list"` 처방의 옳고 그름** — 목록의 **42번 주제**(ARIA 를 언제 쓰지 말아야 하나).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** WebKit·보조 기술 없음.

**하네스** — [13번 주제](../13-phrasing-semantics/3-answer.md)의 `html13b-cdp.py`·`capture.sh`. ★ 이 주제를 위해 **`page` 모드가 요소의 자식 중 `ListMarker` 노드의 이름을 `표지` 로 넘기게** 했다 — `li` 자신의 이름은 빈 문자열이라 **표지는 자식 노드에서만** 읽힌다.

**demo 블록** — [2-summary.md](2-summary.md) 의 demo 는 요약 본문에 트리를 실었다. **「바꿔 볼 것」(둘째 목록에 `reversed`)을 바꾼 판으로 따로 던졌다.**

```html
<!-- html13b-15-democheck.html -->
<ol reversed><li>첫째</li><li value="10">열째로 건너뛴다</li><li>그다음</li></ol>
```

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

- **`3, 10, 9`** — 거꾸로 목록의 시작 값은 항목 수 3, 둘째가 `value` 로 10, 셋째는 **1 을 빼서 9** 다. 단언과 같다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **열두 목록 × 다섯 창**(`ol.start`·`li.value`·`::marker`·표지·`innerText`) + 같은 칸 집계 | 3 | 동작 방식 (1)·(2) · A1 · A2 |
| **`ul`·`dl` 의 `--dump-dom`** | 3 | 동작 방식 (3) · A3 |
| **같은 파일의 접근성 트리** | 3 | 동작 방식 (4) · A4 |
| **demo 와 「바꿔 볼 것」** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `list-style: none` 목록의 역할 | **`list` 가 남는다** | 엔진마다 다르다고 알려져 있다 — WebKit 미실행 |
| `dl` 의 역할 이름 | `DescriptionList` | HTML-AAM 은 `list` — 내부 이름이다 |
| `dl` 안 `div` 를 트리에서 빼는 것 | 뺀다 | 구현의 가지치기 |
| 목록 밖 `li` 의 역할 | `listitem` + 표지 | 명세가 정하지 않은 자리 |
| `listitem` 의 CDP 속성 | `level` 하나(탐색 판) | 캡처하지 않았다 — 본문 근거로 안 쓴다 |

**안 돌려 본 것** — ① **WebKit·Firefox**(엔진이 없다). ② **CSS `counter-reset`·`counter-set` 으로 번호를 바꾼 경우** — CSS 갈래 13번의 표면이다. ③ **중첩 목록의 `level`** — 이 주제의 격자는 한 단계만 썼다. ④ **`<menu>`** — 목록 역할을 받는 셋째 요소인데 이 주제의 범위 밖이다.

**못 잰 것** — ① **스크린리더가 「목록, 항목 N개」를 알리는지.** ② **WebKit 의 `list-style: none` 동작.** ③ **플랫폼 층의 `aria-setsize`·`aria-posinset`.**

**부적용인 창** — **창 ④(`compatMode`) · 창 ⑤(요청 로그) · 창 ⑥(`renderBlockingStatus`).** 목록은 문서 모드·요청·렌더 차단을 바꾸지 않는다 — **잴 것이 없다.**

## 용어 풀이

- **서수 값(ordinal value)** — `li` 마다 명세가 계산하는 번호. 표지가 찍는 값.
- **시작 값(starting value)** — `ol` 의 첫 서수 값.
- **`ListMarker`** — Chrome 접근성 트리의 표지 노드. 이름이 곧 번호 글자다.
- **`ReflectDefault=1`** — 속성이 없을 때 IDL 이 1 을 돌려주는 표기.
- **`DescriptionList`** — Chrome 의 `dl` 내부 역할 이름.
- **제3의 상태(못 잰 것)** — 동작은 있는데 이 머신에 잴 도구가 없는 것. 이 주제의 WebKit 이 그렇다.
