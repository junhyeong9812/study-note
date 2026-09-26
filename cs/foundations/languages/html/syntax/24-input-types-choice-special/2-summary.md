# html/syntax/24 — `<input>` 타입 지도 ③ 선택·특수: `checkbox`/`radio`/`file`/`color`/`hidden`/`submit`/`image` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Constructing the entry list」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-the-form-data-set)(무엇을 **건너뛰나**), [「The input element」](https://html.spec.whatwg.org/multipage/input.html) 의 Checkbox·Radio Button(★ **라디오 단추 그룹** 정의)·File Upload·Color(「색 칸의 색 갱신」)·Hidden(`_charset_`)·Image Button 상태, [「The form element」](https://html.spec.whatwg.org/multipage/forms.html#the-form-element)(`elements`), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/). **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다.**
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 단추·그림 단추·라디오는 **CDP 의 진짜 마우스**로 눌렀다. 하네스는 [21번 주제](../21-form-submission-model/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. ★ **`color` 칸이 CSS 색 이름(`red`)을 받는 것은 명세의 현재 판**이다(「CSS 색을 파싱한다」 — `alpha`·`colorspace` 속성과 함께 들어온 규칙). 언제 바뀌었는지는 이 문서가 확인하지 않았다.
> **선행** — [22번 주제](../22-input-types-text/2-summary.md) · [21번 주제](../21-form-submission-model/2-summary.md)(무엇이 서버에 실리나).
> **경계** — **`disabled` 와 `readonly` 가 포커스·검증에서 갈리는 것**은 목록의 **30번 주제**, **파일 업로드의 `accept`·`multiple`** 은 목록의 **31번 주제**, **`fieldset` 으로 라디오 그룹에 이름을 주는 것**은 목록의 **27번 주제**다 — 여기는 **제출에 실리나**까지. 체크박스의 `click` 이 **먼저 뒤집히고 막으면 되돌아가는 것**은 [web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md)이 정본이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다.** 「체크 안 된 체크박스는 **안 실린다**」는 **없는 것**을 증명하는 일이라 서버가 받은 필드 목록으로만 선다. 스크립트는 **실리는 칸 목록을 따로 들고** 칸마다 「실림 / —」을 세어 마지막 줄로 찍는다.

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
| **흔들린다** | CDP 포트·프로필 경로·서버 포트 | 출력에는 안 들어간다 |
| **죽였다** | `multipart` 경계 문자열 | 하네스가 경계로 갈라 필드만 적는다 |
| **고정했다** | 그림 단추를 누른 자리 | 요소의 왼쪽 위에서 **(7, 5)** — 좌표를 `getBoundingClientRect` 에서 매번 새로 계산한다 |
| **안 흔들린다** | 시도마다 실린 필드 · 「실린 칸 N / M」 | 같은 판이면 결정적이다 |
| **안 흔들린다** | 라디오의 `checked` 상태 · 역할 | 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 어느 칸이 **실렸나 / 안 실렸나** · 무슨 값으로((1)·(2)·(4)) |
| **② 노드 프로브** | 쓴다 | `.value`·`.checked` · 라디오 **누가 켜졌나** · `form.elements` 에 **있나**((1)·(3)) |
| **⑦ 접근성 트리** | 쓴다 | 타입마다 **역할**((1)) |
| **① `--dump-dom`** | 쓴다(곁가지) | demo 검증 — `checked` **속성**과 `.checked` |
| **③ `innerText` 대 `textContent`** | **부적용** | 입력의 값은 자식 글자가 아니다 |
| **④ `compatMode`** · **⑥ `renderBlockingStatus`** | **부적용** | 무관하다 — 잴 것이 없다 |

- ★★★ **제4의 상태와 헷갈리지 마라 — 「안 실렸다」는 쟀고 비었다.** 이 주제의 「—」 칸은 **안 물어본 것이 아니다.** 스크립트가 **칸 스무 개의 필드 이름을 먼저 선언**하고, 시도마다 **서버가 받은 필드 목록에서 찾았다.** 없으면 「—」다(규칙 18-A — 「몇 군데 물었고 몇 군데가 답했나」를 문서가 스스로 선언한다 — **20 곳을 물었다**).

## 한눈에 — 쉽게 말하면

**★ 제출은 「장바구니 결제」다. 계산대는 담긴 것만 찍는다 — 선반에 있었다는 것은 영수증에 안 나온다.**

마트 계산대 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **담은 물건** | 체크된 체크박스 · 골라진 라디오 — **실린다** |
| **선반에 둔 물건** | 체크 안 된 체크박스 · 아무것도 안 고른 라디오 그룹 — ★ **아예 안 실린다**(`c2=` 도 없다) |
| **이름표 없는 물건** | `name` 없는 칸 — 안 실린다 |
| **「판매 금지」 딱지** | `disabled` — 안 실린다 |
| **「만지지 마세요」 딱지** | `readonly` — ★ **실린다**(가져가는 것은 된다) |
| **점원이 몰래 넣는 쿠폰** | `hidden` — 보이지 않는데 실린다 |
| **누른 계산대 번호** | 제출 단추 — **누른 것 하나만** 실린다 |
| **사진을 찍은 자리** | 그림 단추 — **누른 좌표**가 `이름.x`·`이름.y` 로 실린다 |
| **한 번에 하나만 담는 칸** | 라디오 그룹 — **같은 폼 · 같은 이름**이 한 칸이다 |

- **체크 안 된 체크박스는 `이름=` 으로도 안 간다** — 필드 자체가 없다((1)).
- **`value` 없는 체크박스·라디오는 `on`** 으로 간다((1)).
- **두 제출 단추 중 누른 것만** 간다 · **그림 단추는 `img.x=7 · img.y=5`**((1)).
- **라디오는 이름이 같아도 폼이 다르면 따로** 논다((3)).

```text
  「항목 목록 만들기」 — 명세가 칸마다 거치는 거름망 (위에서 먼저 걸리면 건너뛴다)

  칸 ─┬─ datalist 안인가 · disabled 인가                  예 → 건너뜀   x1
      ├─ 단추인데 제출자가 아닌가                          예 → 건너뜀   b0 · (안 누른) s
      ├─ 체크박스·라디오인데 체크 안 됐나                  예 → 건너뜀   c2 · r2
      ├─ 그림 단추인가 ─ 제출자면 이름.x · 이름.y 두 항목 / 아니면 건너뜀
      ├─ name 이 없거나 빈 문자열인가                      예 → 건너뜀   (name 없음)
      └─ 그 밖 ─ 체크박스·라디오: value 없으면 "on"
                 파일: 고른 것 없으면 「이름 빈 파일」 하나
                 hidden name=_charset_: 인코딩 이름
                 나머지: .value

  ★ readonly 는 이 목록에 없다 → 실린다
```

> **항목 목록(entry list)** — 제출할 `이름·값` 쌍의 목록. 폼 제출과 `FormData` 가 같은 알고리즘으로 만든다.\
> 예: `c1=예 · c3=on · r1=나 · …` — 서버 로그의 「필드」 줄이 그것이다.

## 이 주제가 답하려는 질문

1. **어느 칸이 제출에 실리고 어느 칸이 아예 빠지나** — 체크박스·라디오·파일·`hidden`·`color`·`disabled`·`readonly`·단추.
2. **제출 단추와 그림 단추는 무엇을 싣나** — 둘 중 누른 것, 좌표.
3. **라디오는 무엇으로 한 그룹이 되나** — 이름, 폼, 트리.

## 동작 방식

### (1) 창 ⑤ — 칸 스무 개 × 네 가지 제출

**언제 쓰나** — 서버가 「이 필드가 없으면?」을 처리해야 하는지 정할 때. **체크박스가 안 오는 것은 버그가 아니다.**

한 폼에 스무 가지 칸을 두고 **네 가지로** 제출했다 — `보냄 1` · `보냄 2` · 그림 단추의 (7, 5) · 제출자 없는 `requestSubmit()`.

```html
<!-- html21b-24-sent.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>24 무엇이 실리나</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post">
<input type="checkbox" name="c1" value="예" checked>
<input type="checkbox" name="c2" value="예">
<input type="checkbox" name="c3" checked>
<input type="radio" name="r1" value="가">
<input type="radio" name="r1" value="나" checked>
<input type="radio" name="r2" value="가">
<input type="radio" name="r2" value="나">
<input type="radio" name="r3" checked>
<input type="file" name="f1">
<input type="hidden" name="h1" value="숨김">
<input type="hidden" name="_charset_" value="아무 값">
<input type="color" name="k1">
<input type="color" name="k2" value="red">
<input type="color" name="k3" value="#ABCDEF">
<input type="color" name="k4" value="아님">
<input type="text" name="x1" value="비활성" disabled>
<input type="text" name="x2" value="읽기 전용" readonly>
<input type="text" value="이름 없음">
<button type="button" name="b0" value="보통 단추">보통 단추</button>
<button id="보냄1" name="s" value="1">보냄 1</button>
<button id="보냄2" name="s" value="2">보냄 2</button>
<input type="image" id="그림" name="img" alt="그림 단추" width="40" height="20" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=">
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 요소들 = [...document.getElementById("폼").elements];
const 컨트롤 = [...document.querySelectorAll("#폼 input, #폼 button")];
컨트롤.forEach((e, k) => e.dataset.k = k);
window.__대상 = 컨트롤.map((e, k) => [k, "[data-k='" + k + "']"]);
window.__끝 = () => {
  const O = [칸("태그·type", 16) + 칸("name", 11) + 칸(".value", 16) + 칸(".checked", 9) + "역할"];
  for (const [k, e] of 컨트롤.entries()) {
    const 역할 = __AX[k].역할 || (__AX[k].무시 ? "(무시됨)" : "(없음)");
    O.push(칸(e.tagName.toLowerCase() + "·" + e.type, 16) + 칸(e.name || "(없음)", 11) + 칸(JSON.stringify(e.value), 16)
      + 칸(e.type === "checkbox" || e.type === "radio" ? String(e.checked) : "—", 9) + 역할);
  }
  O.push("");
  O.push("form.elements 의 개수 = " + 요소들.length + " · 폼 안의 input·button 개수 = " + 컨트롤.length);
  O.push("form.elements 에 없는 것 = " + 컨트롤.filter(e => !요소들.includes(e)).map(e => e.tagName.toLowerCase() + "·" + e.type).join(" · "));
  return O.join("\n");
};
window.__표 = "실린";
window.__칸목록 = [
  ["checkbox 체크됨 (value=예)", "c1"], ["checkbox 체크 안 됨", "c2"], ["checkbox 체크됨 (value 없음)", "c3"],
  ["radio 그룹 r1 (나 체크)", "r1"], ["radio 그룹 r2 (아무것도 안 고름)", "r2"], ["radio r3 (value 없음)", "r3"],
  ["file (고른 파일 없음)", "f1"], ["hidden", "h1"], ["hidden name=_charset_", "_charset_"],
  ["color (값 없음)", "k1"], ["color value=red", "k2"], ["color value=#ABCDEF", "k3"], ["color value=아님", "k4"],
  ["text disabled", "x1"], ["text readonly", "x2"], ["text (name 없음)", ""], ["button type=button", "b0"],
  ["제출 단추 s", "s"], ["image 단추의 img.x", "img.x"], ["image 단추의 img.y", "img.y"],
];
window.__시도 = [
  { 이름: "보냄 1 클릭", 단계: [["click", "#보냄1"]] },
  { 이름: "보냄 2 클릭", 단계: [["click", "#보냄2"]] },
  { 이름: "그림 단추 (7, 5) 클릭", 단계: [["clickat", "#그림", 7, 5]] },
  { 이름: "requestSubmit() · 제출자 없음", 단계: [["js", "document.getElementById('폼').requestSubmit(); 1"]] },
];
</script>
</body>
</html>
```

**먼저 창 ② + 창 ⑦ — 칸마다의 값과 역할**

```text
$ python3 html21b-form.py page html21b-24-sent.html
태그·type       name       .value          .checked 역할
input·checkbox  c1         "예"            true     checkbox
input·checkbox  c2         "예"            false    checkbox
input·checkbox  c3         "on"            true     checkbox
input·radio     r1         "가"            false    radio
input·radio     r1         "나"            true     radio
input·radio     r2         "가"            false    radio
input·radio     r2         "나"            false    radio
input·radio     r3         "on"            true     radio
input·file      f1         ""              —       button
input·hidden    h1         "숨김"          —       none
input·hidden    _charset_  "아무 값"       —       none
input·color     k1         "#000000"       —       ColorWell
input·color     k2         "#ff0000"       —       ColorWell
input·color     k3         "#abcdef"       —       ColorWell
input·color     k4         "#000000"       —       ColorWell
input·text      x1         "비활성"        —       textbox
input·text      x2         "읽기 전용"     —       textbox
input·text      (없음)     "이름 없음"     —       textbox
button·button   b0         "보통 단추"     —       button
button·submit   s          "1"             —       button
button·submit   s          "2"             —       button
input·image     img        ""              —       button

form.elements 의 개수 = 21 · 폼 안의 input·button 개수 = 22
form.elements 에 없는 것 = input·image
(exit 0)
```

**제출 넷 — 첫 제출의 전문과 나머지 셋**

```text
$ python3 html21b-form.py 시도 html21b-24-sent.html | sed -n '1,6p'
[보냄 1 클릭]
  페이지  click(보냄1 · detail=1) → submit(submitter=보냄1)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9&s=1」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」 · s=「1」
(exit 0)
```

```text
$ python3 html21b-form.py 시도 html21b-24-sent.html | sed -n '7,24p'
[보냄 2 클릭]
  페이지  click(보냄2 · detail=1) → submit(submitter=보냄2)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9&s=2」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」 · s=「2」
[그림 단추 (7, 5) 클릭]
  페이지  click(그림 · detail=1) → submit(submitter=그림)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9&img.x=7&img.y=5」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」 · img.x=「7」 · img.y=「5」
[requestSubmit() · 제출자 없음]
  페이지  submit(submitter=null)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「c1=%EC%98%88&c3=on&r1=%EB%82%98&r3=on&f1=&h1=%EC%88%A8%EA%B9%80&_charset_=UTF-8&k1=%23000000&k2=%23ff0000&k3=%23abcdef&k4=%23000000&x2=%EC%9D%BD%EA%B8%B0+%EC%A0%84%EC%9A%A9」
          필드  c1=「예」 · c3=「on」 · r1=「나」 · r3=「on」 · f1=「」 · h1=「숨김」 · _charset_=「UTF-8」 · k1=「#000000」 · k2=「#ff0000」 · k3=「#abcdef」 · k4=「#000000」 · x2=「읽기 전용」
(exit 0)
```

**실린 칸 격자**

```text
$ python3 html21b-form.py 시도 html21b-24-sent.html | sed -n '26,$p'
칸                                (1)   (2)   (3)   (4)
checkbox 체크됨 (value=예)        실림  실림  실림  실림
checkbox 체크 안 됨               —    —    —    —
checkbox 체크됨 (value 없음)      실림  실림  실림  실림
radio 그룹 r1 (나 체크)           실림  실림  실림  실림
radio 그룹 r2 (아무것도 안 고름)  —    —    —    —
radio r3 (value 없음)             실림  실림  실림  실림
file (고른 파일 없음)             실림  실림  실림  실림
hidden                            실림  실림  실림  실림
hidden name=_charset_             실림  실림  실림  실림
color (값 없음)                   실림  실림  실림  실림
color value=red                   실림  실림  실림  실림
color value=#ABCDEF               실림  실림  실림  실림
color value=아님                  실림  실림  실림  실림
text disabled                     —    —    —    —
text readonly                     실림  실림  실림  실림
text (name 없음)                  —    —    —    —
button type=button                —    —    —    —
제출 단추 s                       실림  실림  —    —
image 단추의 img.x                —    —    실림  —
image 단추의 img.y                —    —    실림  —
(1) 보냄 1 클릭 — 실린 칸 = 13 / 20
(2) 보냄 2 클릭 — 실린 칸 = 13 / 20
(3) 그림 단추 (7, 5) 클릭 — 실린 칸 = 14 / 20
(4) requestSubmit() · 제출자 없음 — 실린 칸 = 12 / 20
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **체크 안 된 체크박스(`c2`)와 아무것도 안 고른 라디오 그룹(`r2`)은 네 제출 전부 「—」** 다. 본문에 **`c2=` 조차 없다** — `c1=%EC%98%88&c3=on&r1=…` 에서 `c2` 가 통째로 빠졌다. 명세의 거름망 — 「체크박스·라디오인데 **체크 상태가 거짓**이면 **건너뛴다**」.
- ★★ **`value` 없는 체크박스(`c3`)·라디오(`r3`)는 `on`** — 명세 — 「`value` 속성이 있으면 그 값, **없으면 문자열 `"on"`**」. 창 ② 의 `.value` 도 `"on"` 이다.
- ★★★ **제출 단추 `s` 는 누른 것만 실렸다** — `보냄 1` 은 `s=1`, `보냄 2` 는 `s=2`. **그림 단추나 `requestSubmit()` 에서는 `s` 가 없다.** 명세 — 「단추인데 **제출자가 아니면** 건너뛴다」. 그래서 **같은 `name` 의 단추 둘로 「무엇을 눌렀나」를 서버에 알릴 수 있다.**
- ★★★ **그림 단추는 `img.x=7 · img.y=5`** — 누른 자리가 요소 왼쪽 위에서 (7, 5) 였고 **그대로** 실렸다. `img` 자체(값)는 없다. 명세 — 「이름 뒤에 `.` 을 붙여 **`x`·`y` 두 항목**을 만든다」.
- ★★ **`disabled`(`x1`)는 안 실리고 `readonly`(`x2`)는 실렸다** — 둘 다 사용자가 못 고치는데 **제출은 갈린다.** 거름망에 `disabled` 는 있고 `readonly` 는 **없다.** 포커스·검증에서의 차이는 목록의 **30번 주제**다.
- **`name` 없는 칸**(「이름 없음」)은 **언제나 「—」** — 이름이 없으면 항목이 안 생긴다. **`type=button`** 도 언제나 「—」(제출자가 될 수 없다).
- ★★ **`hidden` 둘** — `h1=숨김` 은 그대로, **`name="_charset_"` 는 `value="아무 값"` 을 무시하고 `UTF-8`** 이 실렸다. 명세 — 「`hidden` 이고 이름이 `_charset_` 면 **인코딩 이름**을 넣는다」.
- ★★ **`color` 넷** — 값 없음 **`#000000`**, `red` → **`#ff0000`**, `#ABCDEF` → **`#abcdef`**(소문자), `아님` → **`#000000`**. 명세의 「색 칸의 색 갱신」 — 값을 **CSS 색으로 파싱**하고, **실패하면 불투명 검정**, 그 색을 직렬화한다. ★ **`color` 는 빈 값이 없다** — 명세 — 「이 상태에서는 **언제나 색이 골라져 있고** 사용자가 값을 빈 문자열로 둘 방법이 없다」.
- ★★ **고른 파일이 없는 `file`(`f1`)도 실렸다** — urlencoded 본문에서는 **`f1=`**(빈 값)이다. multipart 에서 무엇으로 오는지는 (4).
- **실린 칸** — `보냄 1`·`보냄 2` 는 **13 / 20**, 그림 단추는 **14 / 20**(`s` 대신 `img.x`·`img.y`), `requestSubmit()` 은 **12 / 20**(단추 항목 없음).
- **역할(창 ⑦)** — 체크박스 `checkbox` · 라디오 `radio` · **파일 `button`** · **`hidden` 은 `none`**(트리에서 빠진다) · **색 `ColorWell`** · 제출·그림 단추 `button`. HTML-AAM 은 **`file`·`color` 를 「대응하는 역할 없음」**, `hidden` 을 「대응 없음(Not mapped)」으로 적는다 — `button`·`ColorWell` 은 Chrome 의 이름이다.
- ★★ **`form.elements` 에 그림 단추가 없다** — 21개 대 폼 안의 `input`·`button` 22개, 빠진 것은 `input·image` 하나. 명세의 `elements` 설명 — 「폼의 컨트롤들(**역사적 이유로 그림 단추는 뺀다**)」.

```text
  네 제출에서 실린 칸 — 칸이 갈리는 곳은 「단추」 줄뿐이다

                           보냄 1   보냄 2   그림(7,5)   requestSubmit()
  체크박스·라디오·파일·      같다     같다     같다        같다          ← 12 칸
  hidden·color·readonly
  s                         s=1      s=2      —           —
  img.x · img.y             —        —        7 · 5       —
                           13/20    13/20    14/20       12/20
  언제나 —                 c2 · r2 · x1(disabled) · name 없음 · type=button   ← 5 칸
```

### (2) 창 ⑤ — multipart 에서 빈 파일 칸

**언제 쓰나** — 파일 칸을 **선택 사항**으로 둔 업로드 폼의 서버 쪽 처리를 정할 때.

```html
<!-- html21b-24-file.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>24 빈 파일 칸</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="멀티" action="/r" method="post" enctype="multipart/form-data">
<input type="file" name="f1">
<input type="checkbox" name="c1" value="예" checked>
<input type="checkbox" name="c2" value="예">
<button id="보냄" name="s" value="멀티">보냄</button>
</form>
<script>
window.__시도 = [{ 이름: "multipart · 파일 안 고름", 단계: [["click", "#보냄"]] }];
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 시도 html21b-24-file.html
[multipart · 파일 안 고름]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 3개 · 경계로 갈라 필드만 적는다)
          필드  f1=「」 (filename=「」 · 부분 Content-Type: application/octet-stream) · c1=「예」 · s=「멀티」
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★ **고른 파일이 없어도 부분이 하나 온다** — `f1=「」 (filename=「」 · 부분 Content-Type: application/octet-stream)`. 명세 — 「고른 파일이 없으면 **이름이 빈 `File`**, 형식 `application/octet-stream`, 본문 빈 것을 넣는다」. ★ 그래서 서버는 **「파일 필드가 있다」로 「파일을 올렸다」를 판단하면 틀린다** — 파일 이름이 빈지 본다.
- 체크 안 된 `c2` 는 multipart 에서도 **없다** — 부분이 **3개**(`f1`·`c1`·`s`)다.

### (3) 창 ② — 라디오는 「같은 폼 + 같은 이름」으로 묶인다

**언제 쓰나** — 한 페이지에 **폼이 여럿**이고 라디오 이름이 겹칠 때, 또는 `form` 속성으로 라디오를 **폼 밖에** 둘 때.

```html
<!-- html21b-24-radio.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>24 라디오 묶음</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="갑"><input type="radio" id="갑1" name="r" value="갑1" checked><input type="radio" id="갑2" name="r" value="갑2"></form>
<form id="을"><input type="radio" id="을1" name="r" value="을1" checked><input type="radio" id="을2" name="r" value="을2"></form>
<input type="radio" id="밖1" name="r" value="밖1" checked><input type="radio" id="밖2" name="r" value="밖2">
<input type="radio" id="밖갑" name="r" value="밖갑" form="갑">
<input type="radio" id="대1" name="R" value="대1" checked>
<div><input type="radio" id="두1" name="d" value="두1" checked><input type="radio" id="두2" name="d" value="두2" checked></div>
<script>
const 목록 = () => [...document.querySelectorAll("input[type=radio]")];
const 찍기 = () => 목록().filter(i => i.checked).map(i => i.id).join(" · ");
window.__시도 = [
  { 이름: "처음 상태", 단계: [], 뒤: "찍기()" },
  { 이름: "을2 클릭", 단계: [["click", "#을2"]], 뒤: "찍기()" },
  { 이름: "밖갑 클릭", 단계: [["click", "#밖갑"]], 뒤: "찍기()" },
  { 이름: "밖2 클릭", 단계: [["click", "#밖2"]], 뒤: "찍기()" },
];
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 시도 html21b-24-radio.html
[처음 상태]
  페이지  (기록 없음)
  뒤      갑1 · 을1 · 밖1 · 대1 · 두2
  서버    (받은 요청 없음)
[을2 클릭]
  페이지  click(을2 · detail=1)
  뒤      갑1 · 을2 · 밖1 · 대1 · 두2
  서버    (받은 요청 없음)
[밖갑 클릭]
  페이지  click(밖갑 · detail=1)
  뒤      을1 · 밖1 · 밖갑 · 대1 · 두2
  서버    (받은 요청 없음)
[밖2 클릭]
  페이지  click(밖2 · detail=1)
  뒤      갑1 · 을1 · 밖2 · 대1 · 두2
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **처음 상태에 `checked` 가 넷**(`갑1`·`을1`·`밖1`·`대1`) — 넷 다 `name="r"`(대는 `R`)인데 **동시에 켜져 있다.** 셋이 **서로 다른 그룹**이기 때문이다 — 폼 `갑`, 폼 `을`, **폼 없음.** 명세의 그룹 정의 — 「**같은 폼 소유자이거나 둘 다 폼 소유자가 없고** · **같은 트리**에 있고 · 이름이 비지 않고 **같다**」.
- ★★★ **`을2` 를 누르면 `을1` 만 꺼진다** — `갑1`·`밖1` 은 그대로다. **이름이 같아도 폼이 다르면 따로다.**
- ★★★ **`밖갑`(트리에서는 폼 밖, `form="갑"`)을 누르면 `갑1` 이 꺼진다** — 그룹은 **트리 위치가 아니라 폼 소유자**로 정해진다. [21번](../21-form-submission-model/2-summary.md)의 (4) 에서 본 「`form` 속성이 트리를 이긴다」가 라디오 그룹에도 그대로다([17번](../17-table-structure/2-summary.md)의 `input.form` 과 같은 축).
- ★ **`밖2` 를 누르면 `밖1` 만 꺼진다** — 폼 없는 라디오끼리 한 그룹이다. `밖갑` 은 이 그룹이 **아니었다**(갑 쪽이다).
- **`대1`(`name="R"`)은 끝까지 켜져 있다** — 이름 비교가 **대소문자를 가린다**(「값이 **같다**」).
- **`두1`·`두2` 둘 다 `checked` 속성인데 켜진 것은 `두2`** — 명세의 「어떤 일이 일어난 뒤 그 요소의 체크 상태가 참이면 **같은 그룹의 나머지를 거짓으로**」가 파서가 차례로 넣을 때 돈 결과로 읽힌다(뒤의 것이 앞의 것을 껐다 — 순서는 해석이다).

```text
  name="r" 인 라디오 여섯이 만드는 그룹 — 폼 소유자가 가른다

  그룹 갑   : 갑1 · 갑2 · 밖갑(form="갑")    ← 트리에서 밖이어도 갑
  그룹 을   : 을1 · 을2
  그룹 (없음): 밖1 · 밖2
  그룹 R    : 대1                            ← 이름이 다르다 (대소문자)
```

### demo — 같은 이름에 `checked` 둘

```html demo
<!-- html21b-24-demo.html -->
<label><input type="radio" name="맛" value="단맛" checked> 단맛</label>
<label><input type="radio" name="맛" value="짠맛" checked> 짠맛</label>
<label><input type="radio" name="향" value="민트" checked> 민트</label>
<label><input type="checkbox" name="얼음"> 얼음</label>
<style>
  label { display: block; margin: 4px; }
</style>
```

> **보이는 것** — 「단맛」·「짠맛」 **둘 다 `checked` 를 적었는데 짠맛만 찍혀 있다.** 「민트」는 이름(`향`)이 달라 따로 찍혀 있고, 「얼음」 체크박스는 비어 있다.\
> **바꿔 볼 것** — 「짠맛」의 `name="맛"` 을 다른 이름으로 바꾸고 단맛이 찍히는지 보라 — (3) 의 `대1` 이 「이름이 다르면 다른 그룹」의 근거다

*(Chrome 151 headless 실측, 창 폭 1000: `단맛` 의 `.checked` 가 `false`, `짠맛`·`민트` 가 `true` — `checked` 속성은 셋 다 있다. 검증 파일은 아래)*

```html
<!-- html21b-24-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 24 검증</title>
<body>
<label><input type="radio" name="맛" value="단맛" checked> 단맛</label>
<label><input type="radio" name="맛" value="짠맛" checked> 짠맛</label>
<label><input type="radio" name="향" value="민트" checked> 민트</label>
<label><input type="checkbox" name="얼음"> 얼음</label>
<style>
  label { display: block; margin: 4px; }
</style>
<script>
const O = [];
for (const i of document.querySelectorAll("input")) {
  O.push(i.type.padEnd(9) + "name=" + i.name + " value=" + i.value + " · checked 속성=" + i.hasAttribute("checked") + " · .checked=" + i.checked);
}
document.body.append(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html21b-24-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
radio    name=맛 value=단맛 · checked 속성=true · .checked=false
radio    name=맛 value=짠맛 · checked 속성=true · .checked=true
radio    name=향 value=민트 · checked 속성=true · .checked=true
checkbox name=얼음 value=on · checked 속성=false · .checked=false
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 제출에서 |
|---|---|---|
| 켬/끔 하나 | `<input type="checkbox" name="n" value="예">` | 켜졌을 때만 `n=예` — 꺼지면 **아예 없음** |
| 여럿 중 하나 | `<input type="radio" name="n" value="…">` × N (같은 폼) | 고른 하나만 — 아무것도 안 고르면 **없음** |
| 사용자가 못 고치지만 보낼 값 | `readonly` | **실린다** |
| 사용자가 못 고치고 보내지도 않을 값 | `disabled` | **안 실린다** |
| 화면에 없는 값 | `type="hidden"` | 실린다 · `name="_charset_"` 는 인코딩 이름 |
| 어느 단추로 보냈나 | `<button name="act" value="저장">` + `value="미리보기"` | 누른 것 하나만 |
| 누른 좌표 | `<input type="image" name="img" alt="…">` | `img.x`·`img.y` |
| 색 | `type="color"` | 언제나 `#rrggbb` — 빈 값 없음 |
| 파일(선택 사항) | `type="file"` + multipart | 안 골라도 **이름 빈 부분 하나** |

### 어디서 헷갈리나

- **「체크 안 됨」은 `false` 가 아니라 「필드 없음」이다.**
- **`value` 를 안 적은 체크박스·라디오는 `on`** 이다 — 무엇을 골랐는지 서버가 모른다.
- **`readonly` 와 `disabled` 는 제출에서 정반대다.**
- **라디오 그룹은 이름 + 폼 소유자**다 — 이름만으로 묶이지 않는다.

## 어디서 틀리나

### 1. 체크박스를 끄면 서버가 `agree=false` 나 `agree=` 를 받는다고 여긴다

**아무것도 안 받는다**((1) 의 `c2` — 네 제출 전부 「—」). 서버는 **필드가 없으면 꺼짐**으로 읽어야 한다. ★ 흔한 우회는 같은 이름의 `hidden` 을 **앞에** 두는 것이다 — 그 동작(같은 이름이 둘일 때 서버가 무엇을 고르나)은 **서버 프레임워크의 몫**이라 이 판이 재지 않았다.

### 2. 보내지 않을 값을 `readonly` 로 둔다

**실린다**((1) 의 `x2`). 보내지 않으려면 `disabled`.

### 3. 수정 못 하게 `disabled` 로 뒀는데 서버가 그 값을 기다린다

**안 실린다**((1) 의 `x1`). 보여 주기만 하고 보내려면 `readonly`, 아니면 `hidden` 을 곁에 둔다.

### 4. 두 폼의 라디오에 같은 이름을 줘도 한 그룹일 거라 여긴다

**따로 논다**((3) — `갑1`·`을1`·`밖1` 이 동시에 켜져 있었다). 반대로 **폼 밖의 라디오에 `form` 을 주면** 그 폼의 그룹에 **들어간다**(`밖갑`).

### 5. 파일 필드가 왔으니 파일이 올라왔다고 판단한다

**안 골라도 부분이 온다**((2) — `filename=「」`). 파일 이름·크기를 본다.

### 6. `form.elements` 로 전부 돌면 그림 단추도 잡힌다고 여긴다

**빠진다**((1) — 21 대 22). 명세가 「역사적 이유로」 뺐다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 항목 목록의 거름망 — `datalist` 안 · `disabled` · 제출자 아닌 단추 · 체크 안 된 체크박스·라디오 · `name` 없음 → **건너뜀** | (1) |
| **명세(HTML)** | 체크박스·라디오의 값 = `value` 속성, 없으면 **`on`** | (1) |
| **명세(HTML)** | 그림 단추 = 제출자일 때만 **`이름.x`·`이름.y`** | (1) |
| **명세(HTML)** | `hidden` + `_charset_` = **인코딩 이름** | (1) |
| **명세(HTML)** | 고른 파일 없음 = **이름 빈 `File` · `application/octet-stream`** | (2) |
| **명세(HTML)** | 색 칸 = CSS 색 파싱 · 실패하면 **불투명 검정** · 빈 값이 없다 | (1) |
| **명세(HTML)** | 라디오 그룹 = **같은 폼 소유자(또는 둘 다 없음) · 같은 트리 · 같은 이름** | (3) |
| **명세(HTML)** | `form.elements` 는 **그림 단추를 뺀다**(역사적 이유) | (1) |
| **명세(HTML-AAM)** | checkbox · radio · submit·image → `button` · **file·color → 대응 역할 없음** · hidden → 대응 없음 | (1) |
| **구현(Chrome)** | `file` 을 `button`, `color` 를 `ColorWell` 로 트리에 둔다 | (1) |
| **이 판의 관찰** | 위 명세 줄이 **전부 그대로 동작했다** — 이 주제에서는 **명세와 갈린 칸이 없었다** | (1)\~(3) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **파일 선택 창·색 선택 창** | 페이지 밖 UI 다 — 헤드리스에서 열지 않았다. 「못 잰 것」 |
| **실제 파일을 고른 업로드** | 이 배치는 **빈 파일 칸**만 던졌다 — 목록의 **31번 주제**의 몫이다(안 돌려 본 것) |
| **같은 이름이 둘일 때 서버가 무엇을 고르나**(`hidden` 우회) | 서버 프레임워크의 동작이다 — 이 문서의 서버는 **받은 것을 전부 적을** 뿐이다 |
| **스크린리더가 라디오 그룹을 「3개 중 2번째」로 읽나** | 보조 기술이 없다. 그룹의 이름은 목록의 **27번 주제**(`fieldset`·`legend`)가 다룬다 |
| **키보드 화살표로 라디오 그룹 안을 도는 것** | 이 배치는 마우스만 눌렀다 — 안 돌려 본 것 |

## 언제 쓰고 언제 안 쓰나

- **켬/끔은 체크박스** — 서버는 「없음 = 꺼짐」으로 읽는다. **`value` 를 꼭 적는다.**
- **여럿 중 하나는 라디오** — 한 그룹은 **한 폼 안의 같은 이름.** 기본 선택이 없으면 **아무것도 안 갈 수 있다**는 것을 서버가 안다.
- **어떤 동작인지 알려야 하면 같은 `name` 의 제출 단추 둘** — 누른 것만 간다.
- **보여만 주고 보낼 값은 `readonly`, 보내지 않을 값은 `disabled`.**
- **그림 단추는 좌표가 필요할 때만** — 그냥 그림이 있는 단추면 `<button><img alt="…"></button>` 이 낫다(이 판은 그 비교를 던지지 않았다).
- **`hidden` 은 사용자가 바꿀 수 없다는 뜻이 아니다** — 개발자 도구와 `curl` 로 무엇이든 보낼 수 있다([21번](../21-form-submission-model/2-summary.md)의 (5)).

## 핵심 문장

1. **체크 안 된 체크박스와 아무것도 안 고른 라디오 그룹은 아예 안 실린다 — `이름=` 도 없다.**
2. **`value` 가 없는 체크박스·라디오는 `on` 으로 실린다.**
3. **제출 단추는 누른 것 하나만 실린다 — 그림 단추는 `이름.x`·`이름.y` 좌표로 실린다.**
4. **`disabled` 는 안 실리고 `readonly` 는 실린다.**
5. **라디오 그룹은 이름 + 폼 소유자로 묶인다 — 같은 이름이어도 폼이 다르면 따로, `form` 속성이면 그 폼으로 간다.**
6. **`color` 는 빈 값이 없다 — 틀린 값은 `#000000`, `red` 는 `#ff0000`.**
7. **고른 파일이 없어도 파일 칸은 이름 빈 부분으로 실린다.**

## 관련 자료

- [21번 주제 — 제출 모델](../21-form-submission-model/2-summary.md) — 서버 요청 로그 하네스 · **`form` 속성이 트리를 이긴다**.
- [17번 주제 — 표 구조](../17-table-structure/2-summary.md) — **트리 위치와 `input.form` 이 갈리는** 첫 사례.
- [web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md) — 체크박스·라디오가 **리스너 안에서 이미 뒤집혀 있고 막으면 되돌아가는 것**의 정본.
- [22번](../22-input-types-text/2-summary.md) · [23번 주제](../23-input-types-number-date/2-summary.md) — 타입 지도의 앞 두 쪽.
- 목록의 **26번 주제**(`select` 의 다중 선택이 어떻게 실리나) · **27번 주제**(`fieldset`·`legend` 로 그룹에 이름) · **30번 주제**(`disabled`·`readonly` 의 세 지점) · **31번 주제**(파일 업로드).

## 용어 풀이

- **항목 목록(entry list)** — 제출할 `이름·값` 쌍. 거름망을 통과한 칸만 든다.
- **체크 상태(checkedness)** — `.checked` 가 읽는 상태. `checked` **속성**은 초기값이다.
- **라디오 단추 그룹(radio button group)** — 같은 폼 소유자(또는 둘 다 없음) · 같은 트리 · 같은 비지 않은 이름인 라디오들.
- **제출자(submitter)** — 누른 단추. 단추 항목은 제출자 것만 든다.
- **선택된 좌표(selected coordinate)** — 그림 단추를 누른 자리. 요소 왼쪽 위 기준.
- **`_charset_`** — 이 이름의 `hidden` 은 값 대신 **문서 인코딩 이름**을 보낸다.
- **불투명 검정** — 색 칸이 색을 못 읽었을 때의 값 `#000000`.

## 더 들어가면

- **왜 체크 안 된 칸을 안 보내나** — 명세가 이유를 적지 않는다. 결과만 보면, 폼 인코딩에는 **「거짓」을 적는 칸이 없다** — 체크박스는 `value` 라는 **글자 하나**를 보내거나 **안 보내거나** 둘 중 하나다. 이 문단은 해석이다.
- **`elements` 가 그림 단추를 빼는 「역사적 이유」** — 명세는 그 이유를 풀어 쓰지 않는다. 이 배치는 확인하지 않았다.
- **`_charset_` 의 쓸모** — 서버가 **본문의 인코딩을 모를 때** 폼이 스스로 알려 주는 옛 수단이다. 이 페이지는 UTF-8 이라 `UTF-8` 이 실렸다 — 다른 인코딩 문서는 던지지 않았다.
