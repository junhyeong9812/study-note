# html/syntax/25 — `label` 연결과 폼 필드 이름: `for`/`id`·감싸기·클릭 위임 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The label element」](https://html.spec.whatwg.org/multipage/forms.html#the-label-element)(★ **연결된 컨트롤(labeled control)** 의 정의 · 활성화 동작), [「Categories — labelable elements」](https://html.spec.whatwg.org/multipage/forms.html#category-label), [「Interactive content」](https://html.spec.whatwg.org/multipage/dom.html#interactive-content), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/) 의 「4.1.1 텍스트 칸의 이름 계산」·「4.1.7 그 밖의 폼 요소의 이름 계산」·`label` 역할 줄. **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다.**
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 클릭은 전부 **CDP 의 진짜 마우스**로 눌렀다(스크립트의 `click()` 이 아니다). 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다(26\~28번이 같은 하네스를 쓴다 — [21번](../21-form-submission-model/3-answer.md)의 하네스를 이었다).\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. `label` 은 가장 오래된 폼 표면이라 Baseline 조회 대상으로 삼지 않았다.
> **선행** — [22번 주제](../22-input-types-text/2-summary.md)(입력 칸의 역할) · [24번 주제](../24-input-types-choice-special/2-summary.md)(체크박스의 `click` 이 상태를 뒤집는다).
> **경계** — **이벤트가 경로를 도는 순서**는 [web-api 16번](../../../../web-api/16-event-propagation-phases/2-summary.md), **`preventDefault` 가 기본 동작을 막는 것**과 체크박스가 **리스너 안에서 이미 뒤집혀 있는 것**은 [web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md)이 정본이다 — 여기는 **라벨이 두 번째 `click` 을 만드는 것**까지. **이름 출처가 여럿일 때 어느 것이 이기나**(순서 전체)는 목록의 **43번 주제**, **묶음(`fieldset`)의 이름**은 [27번 주제](../27-fieldset-and-legend/2-summary.md)다 — 여기는 **라벨이 이름이 되나**까지만.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑦(접근성 트리)과 창 ②(페이지가 받은 `click`)의 짝이다.** 라벨이 끊기면 **두 가지가 함께 사라진다** — 글자를 눌러도 칸이 안 켜지고(창 ②), 칸의 **접근 가능한 이름**이 빈다(창 ⑦). 둘을 한 표에 놓고 「끊긴 칸 N / M」을 스크립트가 센다.

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
| **고정했다** | 누른 자리 | 요소 **한가운데** — 좌표를 `getBoundingClientRect` 에서 매번 새로 계산한다 |
| **안 흔들린다** | `click` 기록의 줄 순서·`isTrusted`·`detail` · 체크 상태 | 같은 판이면 결정적이다 |
| **안 흔들린다** | 접근 가능한 이름 · `nameFrom` · `labels.length` · 「끊긴 칸 N / M」 | 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑦ 접근성 트리**(CDP + `chrome://accessibility` 내부 덤프) | ★ **쓴다 — 본체** | 칸의 **접근 가능한 이름**이 무엇인가 · 그 이름이 **어디서 왔나**(`nameFrom`)((1)·(4)) |
| **② 노드 프로브**(페이지가 받은 `click` · `labels` · `control`) | ★ **쓴다 — 본체의 짝** | 글자를 누르면 칸에 **`click` 이 몇 번** 가나 · **어느 순서로** · 칸이 **켜졌나**((1)\~(3)) |
| **① `--dump-dom`** | 쓴다(곁가지) | demo 검증 — `labels.length` |
| **⑤ 서버 요청 로그** | **부적용** | 라벨은 제출에 아무것도 싣지 않는다 — **잴 것이 없다**(시도 블록의 「서버 (받은 요청 없음)」은 그 확인이다) |
| **③ `innerText` 대 `textContent`** · **④ `compatMode`** · **⑥ `renderBlockingStatus`** | **부적용** | 무관하다 |

- ★★ **제5의 상태 — 「클릭이 칸에 갔나」를 화면이 아니라 칸이 받은 `click` 으로 물었다.** 글자를 눌렀을 때 체크 표시가 생기는지는 픽셀로도 볼 수 있지만, 그러면 **몇 번 갔나**(한 번 켜고 한 번 끄면 화면은 그대로다)를 못 가른다. 그래서 모든 `input` 에 `click` 리스너를 달아 **받은 횟수**를 세고, 체크 상태를 따로 읽었다. ★ **바꾼 창이 못 보는 것** — 칸이 `click` 을 받았는데 **사용자에게 보이는 반응**(포커스 테두리·체크 그림)이 어땠는지는 모른다.
- ★ **`nameFrom` 은 내부 덤프에만 있다** — CDP 트리는 이름의 **글자**를 주고, `chrome://accessibility` 의 「blink」 트리는 그 이름이 **라벨에서 왔는지(`relatedElement`)·속성에서 왔는지(`attribute`)** 를 준다([17번](../17-table-structure/2-summary.md)이 처음 쓴 창이다).
- ★★ **18-A — 몇 군데 물었나.** (1) 의 격자는 **아홉 칸 × 세 물음 = 27 곳**을 물었다. 「끊겼다」는 **그 27 곳 중 답이 빈 곳**이다.

## 한눈에 — 쉽게 말하면

**★ 라벨은 「이름표 + 초인종 줄」이다. 이름표를 칸에 제대로 달면 두 가지가 한꺼번에 생긴다 — 누구 칸인지 읽히고(이름), 이름표를 당기면 칸의 초인종이 울린다(클릭).**

사물함 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **사물함에 붙은 이름표** | `label` — 칸의 **접근 가능한 이름**이 된다 |
| **이름표에 적힌 사물함 번호** | `for="id"` — 번호로 **가리킨다** |
| **이름표 봉투 안에 사물함 열쇠를 넣음** | 감싸기 — `<label>글자 <input></label>` |
| **이름표를 당기면 사물함 벨이 울림** | 라벨을 누르면 칸에 **두 번째 `click`** 이 간다 |
| **없는 번호가 적힌 이름표** | `for` 가 없는 `id`·라벨이 못 되는 요소를 가리킴 — ★ **봉투 안에 열쇠가 있어도 무효**(번호가 이긴다) |
| **봉투 안에 열쇠가 둘** | 감싼 안에 칸 둘 — **첫째만** 연결된다 |
| **이름표 없이 옆에 써 둔 글씨** | 그냥 글자 — 읽혀도 **이름이 아니다** · 당길 줄도 없다 |
| **사물함 문에 직접 쓴 이름** | `aria-label` — 이름은 생기지만 **당길 줄은 없다** |

- **`for`/`id` 와 감싸기는 결과가 같다** — 이름도 클릭도((1)).
- ★★ **`for` 를 적으면 감싸기가 무시된다** — `for` 가 빗나가면 **안에 있는 칸도 연결이 안 된다**((1)).
- ★★ **라벨을 누르면 칸에 `click` 이 한 번 더 간다** — 그 `click` 은 다시 라벨을 **거쳐 올라온다**((2)).
- ★ **라벨 안의 링크·단추를 누르면 칸에 안 간다** — 명세가 「아무것도 하지 않는다」로 정했다((3)).

```text
  라벨 하나가 칸에 주는 것 — 연결이 끊기면 둘이 함께 사라진다

   <label for="c1">동의</label>  <input type="checkbox" id="c1">
         │                                 ▲
         ├── ① 이름 ─────────────────────────┤  접근 가능한 이름 = "동의"      (창 ⑦)
         │                                 │
         └── ② 클릭 위임 ── 글자를 누르면 ──┘  칸에 click 한 번 더 → 켜짐      (창 ②)

   연결 = for 가 가리킨 labelable 요소  /  for 가 없으면 안에 든 첫 labelable 요소
```

> **연결된 컨트롤(labeled control)** — 명세가 라벨마다 정하는 「이 라벨이 가리키는 칸」 하나. `label.control` 이 그것을 돌려준다.\
> 예: `<label for="c1">` 이고 `id="c1"` 인 체크박스가 있으면 그 체크박스.

> **라벨이 될 수 있는 요소(labelable element)** — `button` · `hidden` 이 아닌 `input` · `meter` · `output` · `progress` · `select` · `textarea` · 폼 연관 사용자 정의 요소. **`div` 는 아니다.**

## 이 주제가 답하려는 질문

1. **라벨은 어떻게 칸에 연결되나** — `for`/`id` 와 감싸기가 겹치거나 빗나가면 무엇이 이기나.
2. **연결이 끊기면 무엇이 사라지나** — 글자 클릭, 접근 가능한 이름, `input.labels`.
3. **라벨을 누르면 칸에 무슨 일이 몇 번 일어나나** — 두 번째 `click` 과 그 함정, 그리고 **위임이 멈추는 자리**.

## 동작 방식

### (1) 창 ⑦ + 창 ② — 연결 방식 아홉 칸 × 세 물음

**언제 쓰나** — 「글자를 눌러도 체크가 안 된다」·「스크린리더가 이름 없는 체크박스라고 읽는다」는 보고를 받았을 때. **둘은 같은 원인일 때가 많다.**

체크박스 아홉 개에 연결 방식만 바꿔 붙이고, 칸마다 **글자를 진짜로 눌렀다.** 페이지를 시도마다 새로 연다.

```html
<!-- html25b-25-link.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>25 라벨 연결</title>
</head>
<body>
<p><label id="L1" for="c1">동의 1</label> <input type="checkbox" id="c1"></p>
<p><label id="L2"><span id="T2">동의 2</span> <input type="checkbox" id="c2"></label></p>
<p><label id="L3" for="c3"><span id="T3">동의 3</span> <input type="checkbox" id="c3"></label></p>
<p><label id="L4" for="없는아이디"><span id="T4">동의 4</span> <input type="checkbox" id="c4"></label></p>
<p><div id="D5">상자</div><label id="L5" for="D5"><span id="T5">동의 5</span> <input type="checkbox" id="c5"></label></p>
<p><label id="L6"><span id="T6">동의 6</span> <input type="checkbox" id="c6a"> <input type="checkbox" id="c6b"></label></p>
<p><span id="T7">동의 7</span> <input type="checkbox" id="c7"></p>
<p><span id="T8">동의 8</span> <input type="checkbox" id="c8" aria-label="동의 8"></p>
<script>
const 행 = [
  ["for/id", "#L1", "c1"], ["감싸기", "#T2", "c2"], ["감싸기 + for 같은 칸", "#T3", "c3"],
  ["감싸기 + for 가 없는 id", "#T4", "c4"], ["감싸기 + for 가 div", "#T5", "c5"],
  ["감싼 안의 첫째 input", "#T6", "c6a"], ["감싼 안의 둘째 input", "#T6", "c6b"],
  ["라벨 없음 (옆 글자)", "#T7", "c7"], ["aria-label 만", "#T8", "c8"],
];
window.__기록 = [];
for (const i of document.querySelectorAll("input")) {
  i.addEventListener("click", e => __기록.push(i.id + (e.isTrusted ? "" : "(합성)")));
}
const 뒤 = id => "(() => { const i = document.getElementById('" + id + "'); return JSON.stringify({ 클릭: __기록.filter(x => x.startsWith('" + id + "')).length, 켜짐: i.checked, 포커스: document.activeElement.id || document.activeElement.tagName }); })()";
window.__표 = "종합";
window.__시도 = 행.map(([이름, 누를곳, id]) => ({ 이름, 단계: [["click", 누를곳]], 뒤: 뒤(id) }));
window.__대상 = 행.map(([, , id]) => [id, "#" + id]);
window.__내부 = true;
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__종합 = 결과 => {
  const O = [칸("연결 방식", 26) + 칸("글자 클릭 → input", 22) + 칸("접근 가능한 이름", 18) + 칸("nameFrom", 16) + 칸("labels", 7) + "label.control"];
  let 끊김 = 0, 전체 = 0;
  for (const [k, [이름, , id]] of 행.entries()) {
    const r = JSON.parse(결과[k].뒤);
    const i = document.getElementById(id);
    const 라벨 = document.querySelector("label:has(#" + id + "), label[for='" + id + "']");
    const 컨트롤 = [...document.querySelectorAll("label")].filter(l => l.control === i).map(l => l.id).join(",") || "—";
    const 이름값 = __AX[id].이름;
    const 출처 = (__INT[id] && __INT[id].속성.nameFrom) || "(없음)";
    const 칸들 = [r.클릭 > 0 && r.켜짐, 이름값 !== "", i.labels.length > 0];
    끊김 += 칸들.filter(x => !x).length; 전체 += 3;
    O.push(칸(이름, 26) + 칸("click " + r.클릭 + "번 · " + (r.켜짐 ? "켜짐" : "그대로"), 22) + 칸(JSON.stringify(이름값), 18)
      + 칸(출처, 16) + 칸(String(i.labels.length), 7) + 컨트롤);
  }
  O.push("");
  O.push("끊긴 칸 = " + 끊김 + " / " + 전체 + "  (칸 셋 — 글자 클릭이 켰나 · 이름이 있나 · labels 가 1 이상인가)");
  return O.join("\n");
};
</script>
</body>
</html>
```

**시도마다 — 칸이 받은 `click` · 체크 · 포커스**

```text
$ python3 html25b-form.py 시도 html25b-25-link.html | sed -n '1,/^$/p'
[for/id]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c1"}
  서버    (받은 요청 없음)
[감싸기]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c2"}
  서버    (받은 요청 없음)
[감싸기 + for 같은 칸]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c3"}
  서버    (받은 요청 없음)
[감싸기 + for 가 없는 id]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)
[감싸기 + for 가 div]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)
[감싼 안의 첫째 input]
  페이지  (기록 없음)
  뒤      {"클릭":1,"켜짐":true,"포커스":"c6a"}
  서버    (받은 요청 없음)
[감싼 안의 둘째 input]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"c6a"}
  서버    (받은 요청 없음)
[라벨 없음 (옆 글자)]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)
[aria-label 만]
  페이지  (기록 없음)
  뒤      {"클릭":0,"켜짐":false,"포커스":"BODY"}
  서버    (받은 요청 없음)

(exit 0)
```

**격자 — 세 물음과 「끊긴 칸」**

```text
$ python3 html25b-form.py 시도 html25b-25-link.html | sed -n '/^연결 방식/,$p'
연결 방식                 글자 클릭 → input    접근 가능한 이름  nameFrom        labels label.control
for/id                    click 1번 · 켜짐      "동의 1"          relatedElement  1      L1
감싸기                    click 1번 · 켜짐      "동의 2"          relatedElement  1      L2
감싸기 + for 같은 칸      click 1번 · 켜짐      "동의 3"          relatedElement  1      L3
감싸기 + for 가 없는 id   click 0번 · 그대로    ""                (없음)          0      —
감싸기 + for 가 div       click 0번 · 그대로    ""                (없음)          0      —
감싼 안의 첫째 input      click 1번 · 켜짐      "동의 6"          relatedElement  1      L6
감싼 안의 둘째 input      click 0번 · 그대로    ""                (없음)          0      —
라벨 없음 (옆 글자)       click 0번 · 그대로    ""                (없음)          0      —
aria-label 만             click 0번 · 그대로    "동의 8"          attribute       0      —

끊긴 칸 = 14 / 27  (칸 셋 — 글자 클릭이 켰나 · 이름이 있나 · labels 가 1 이상인가)
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **끊긴 칸은 14 / 27** 이다. 세 물음(글자 클릭이 칸을 켰나 · 이름이 있나 · `labels` 가 1 이상인가)이 **연결된 네 줄(`for`/`id` · 감싸기 · 둘 다 · 감싼 안의 첫째)은 셋 다 살아 있고**, 연결이 없는 네 줄은 **셋 다 비었다.** `aria-label` 줄만 **이름은 있고 나머지 둘이 비었다.**
- ★★ **`for`/`id` · 감싸기 · 둘 다 — 세 줄이 한 글자도 같다** — `click 1번 · 켜짐`, 이름 = 라벨 글자, `nameFrom` = **`relatedElement`**(다른 요소에서 온 이름), `labels` = 1.
- ★★★ **`for` 가 빗나가면 안에 든 칸도 연결이 안 된다** — 「감싸기 + `for` 가 없는 `id`」와 「감싸기 + `for` 가 `div`」는 체크박스를 **안에 품고 있는데** `click 0번` · 이름 `""` · `labels` 0 이다. 명세의 두 문장이 순서대로 걸린다 — 「`for` 가 **지정됐고** 그 `id` 의 첫 요소가 라벨이 될 수 있는 요소면 그것이 연결된 컨트롤」 · 「`for` 가 **지정되지 않았으면** 안에 든 첫 라벨이 될 수 있는 요소」. **`for` 가 있는 순간 둘째 문장은 읽히지 않는다.** 그리고 첫째 문장의 조건이 안 맞으면 명세는 「그 밖에는 연결된 컨트롤이 **없다**」로 끝난다.
- ★★ **감싼 안에 칸이 둘이면 첫째만** — `c6a` 는 연결되고 `c6b` 는 `labels` 0 · 이름 `""`. 글자를 누르면 `c6a` 가 켜지고 **포커스도 `c6a`** 로 갔다(시도 블록의 「감싼 안의 둘째 input」 줄 — `c6b` 는 0번인데 포커스가 `c6a`).
- **옆에 둔 글자(라벨 없음)는 이름이 아니다** — 화면에서는 `동의 7` 이 칸 바로 옆에 있어도 트리의 이름은 `""` 이다. 글자를 눌러도 아무것도 안 켜지고 포커스는 `BODY` 에 남는다.
- ★ **`aria-label` 은 이름만 준다** — 이름 `"동의 8"` · `nameFrom` = **`attribute`**. 그러나 **`labels` 는 0 이고 글자를 눌러도 안 켜진다.** 「보조 기술에는 이름이 있다」와 「마우스 사용자의 클릭 면이 넓다」는 **다른 일**이다.
- ★ **연결된 칸은 라벨을 눌러도 포커스가 칸으로 간다** — `for`/`id` 줄의 포커스가 `c1` 이다(글자를 눌렀는데 체크박스가 포커스를 받았다).

```text
  연결된 컨트롤을 정하는 두 문장 — for 가 있으면 둘째 문장은 읽지 않는다

  label 에 for 가 있나?
     │
     ├─ 있다 ──> id 가 같은 첫 요소가 labelable 인가?
     │             ├─ 그렇다 ──> 그것이 연결된 컨트롤          for/id · 감싸기+for 같은 칸
     │             └─ 아니다 ──> ★ 연결된 컨트롤 없음           for 가 없는 id · for 가 div
     │                           (안에 체크박스가 있어도!)
     │
     └─ 없다 ──> 안에 labelable 요소가 있나?
                   ├─ 있다 ──> 트리 순서로 첫째               감싸기 · 감싼 안의 첫째
                   └─ 없다 ──> 연결된 컨트롤 없음
```

```text
  아홉 칸 — 세 물음이 함께 산다, 함께 죽는다

                        클릭 → 켜짐   이름            labels
  for/id                    ●         "동의 1"          1
  감싸기                    ●         "동의 2"          1
  감싸기 + for 같은 칸      ●         "동의 3"          1
  감싼 안의 첫째            ●         "동의 6"          1
  ─────────────────────────────────────────────────────────
  감싸기 + for 없는 id      ·         ""                0       ← 안에 품고도 끊겼다
  감싸기 + for 가 div       ·         ""                0       ←
  감싼 안의 둘째            ·         ""                0
  라벨 없음                 ·         ""                0
  aria-label 만             ·         "동의 8"          0       ← 이름만 산다
```

### (2) 창 ② — 라벨을 누르면 칸에 두 번째 `click`

**언제 쓰나** — 라벨과 칸을 **같은 조상의 `click` 리스너 하나**로 처리할 때. 한 번 누른 것이 **두 번** 불린다.

`window` 에는 **캡처 단계로**, 라벨과 칸에는 **버블 단계로** `click` 리스너를 달고, 받은 순서를 한 줄씩 적었다([web-api 16번](../../../../web-api/16-event-propagation-phases/2-summary.md)의 호출 순서 로그와 같은 방식이다).

```html
<!-- html25b-25-click.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>25 클릭 위임</title>
</head>
<body>
<p><label id="감쌈"><span id="감쌈글자">알림 받기</span> <input type="checkbox" id="감쌈칸"></label></p>
<p><label id="가리킴" for="가리킴칸">알림 받기</label> <input type="checkbox" id="가리킴칸"></p>
<p><label id="부름"><span id="부름글자">알림 받기</span> <input type="checkbox" id="부름칸"></label></p>
<p><label id="거름"><span id="거름글자">알림 받기</span> <input type="checkbox" id="거름칸"></label></p>
<p><label id="막음"><span id="막음글자">알림 받기</span> <input type="checkbox" id="막음칸"></label></p>
<p><label id="안쪽">
  <span id="안쪽글자">알림</span>
  <input type="checkbox" id="안쪽칸">
  <a id="안쪽링크" href="#없음">약관</a>
  <a id="안쪽앵커">href 없는 a</a>
  <button type="button" id="안쪽단추">도움말</button>
</label></p>
<p><label id="앞단추"><span id="앞단추글자">알림</span> <button type="button" id="앞단추단추">도움말</button> <input type="checkbox" id="앞단추칸"></label></p>
<script>
window.__기록 = [];
const 적 = s => __기록.push(s);
const 이름 = n => n === window ? "window" : n.id || n.nodeName;
for (const 곳 of [window, ...document.querySelectorAll("label, input")]) {
  곳.addEventListener("click", e => 적("click @" + 이름(e.currentTarget) + " target=" + 이름(e.target)
    + " isTrusted=" + e.isTrusted + " detail=" + e.detail + (e.target.type === "checkbox" ? " checked=" + e.target.checked : "")), 곳 === window);
}
for (const i of document.querySelectorAll("input")) i.addEventListener("change", () => 적("change @" + i.id + " checked=" + i.checked));
// 부름 — 라벨 리스너가 스스로 input.click() 을 부른다
document.getElementById("부름").addEventListener("click", () => document.getElementById("부름칸").click());
// 거름 — 라벨 자신을 향한 click 만 넘긴다
document.getElementById("거름").addEventListener("click", e => { if (e.target !== document.getElementById("거름칸")) { e.preventDefault(); document.getElementById("거름칸").click(); } });
// 막음 — 라벨의 click 을 막는다
document.getElementById("막음").addEventListener("click", e => { if (e.target.id === "막음글자") e.preventDefault(); });
const 뒤 = ids => "__기록.join('\\n          ') + '\\n          → ' + " + JSON.stringify(ids) + ".map(id => id + '.checked=' + document.getElementById(id).checked).join(' · ')";
window.__시도 = [
  { 이름: "감싼 라벨의 글자", 단계: [["click", "#감쌈글자"]], 뒤: 뒤(["감쌈칸"]) },
  { 이름: "for 로 가리킨 라벨", 단계: [["click", "#가리킴"]], 뒤: 뒤(["가리킴칸"]) },
  { 이름: "감싼 라벨의 체크박스 자체", 단계: [["click", "#감쌈칸"]], 뒤: 뒤(["감쌈칸"]) },
  { 이름: "라벨 리스너가 input.click() 을 부름", 단계: [["click", "#부름글자"]], 뒤: 뒤(["부름칸"]) },
  { 이름: "라벨 리스너가 걸러서 부름", 단계: [["click", "#거름글자"]], 뒤: 뒤(["거름칸"]) },
  { 이름: "라벨 click 에서 preventDefault", 단계: [["click", "#막음글자"]], 뒤: 뒤(["막음칸"]) },
  { 이름: "라벨 안의 span", 단계: [["click", "#안쪽글자"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "라벨 안의 a[href]", 단계: [["click", "#안쪽링크"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "라벨 안의 href 없는 a", 단계: [["click", "#안쪽앵커"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "라벨 안의 button", 단계: [["click", "#안쪽단추"]], 뒤: 뒤(["안쪽칸"]) },
  { 이름: "button 이 체크박스 앞에 있는 라벨의 글자", 단계: [["click", "#앞단추글자"]], 뒤: 뒤(["앞단추칸"]) },
];
</script>
</body>
</html>
```

```text
$ python3 html25b-form.py 시도 html25b-25-click.html | sed -n '1,27p'
[감싼 라벨의 글자]
  페이지  (기록 없음)
  뒤      click @window target=감쌈글자 isTrusted=true detail=1
          click @감쌈 target=감쌈글자 isTrusted=true detail=1
          click @window target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈칸 target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈 target=감쌈칸 isTrusted=true detail=1 checked=true
          change @감쌈칸 checked=true
          → 감쌈칸.checked=true
  서버    (받은 요청 없음)
[for 로 가리킨 라벨]
  페이지  (기록 없음)
  뒤      click @window target=가리킴 isTrusted=true detail=1
          click @가리킴 target=가리킴 isTrusted=true detail=1
          click @window target=가리킴칸 isTrusted=true detail=1 checked=true
          click @가리킴칸 target=가리킴칸 isTrusted=true detail=1 checked=true
          change @가리킴칸 checked=true
          → 가리킴칸.checked=true
  서버    (받은 요청 없음)
[감싼 라벨의 체크박스 자체]
  페이지  (기록 없음)
  뒤      click @window target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈칸 target=감쌈칸 isTrusted=true detail=1 checked=true
          click @감쌈 target=감쌈칸 isTrusted=true detail=1 checked=true
          change @감쌈칸 checked=true
          → 감쌈칸.checked=true
  서버    (받은 요청 없음)
(exit 0)
```

- ★★★ **감싼 라벨의 글자를 한 번 누르면 `click` 이 두 번 돈다** — 첫째는 **라벨의 글자**(`target=감쌈글자`)가 받은 진짜 클릭, 둘째는 **라벨이 칸에 보낸 `click`**(`target=감쌈칸`). ★ 둘째 `click` 은 칸에서 **버블해 올라와 라벨의 리스너를 한 번 더 부른다**(`click @감쌈 target=감쌈칸`). 라벨의 리스너 입장에서는 **한 번 눌렀는데 두 번 불렸다.**
- ★★ **둘째 `click` 도 `isTrusted=true` · `detail=1`** 이다 — 이 판의 Chrome 은 라벨이 보낸 `click` 을 **사용자가 만든 것으로 표시했다.** 그래서 `isTrusted` 로 두 `click` 을 가를 수 없다. 가를 수 있는 것은 **`target`** 이다.
- ★ **`for` 로 가리킨 라벨은 칸이 라벨 밖에 있다** — 둘째 `click` 은 칸에서 `window` 까지만 가고 **라벨은 안 거친다**(줄이 넷). 같은 「두 번째 `click`」인데 **라벨의 리스너가 두 번 불리는지는 구조가 정한다.**
- **칸 자체를 누르면 `click` 은 한 번** — 칸이 받고 라벨로 버블한다. 라벨의 활성화 동작은 **돌지 않는다** — 명세 — 「대화형 콘텐츠 자손을 향한 이벤트에 대한 라벨의 활성화 동작은 **아무것도 하지 않는 것**이어야 한다」(체크박스도 대화형 콘텐츠다).
- ★ **명세는 「두 번째 `click`」을 요구하지 않는다** — 명세는 라벨의 활성화 동작이 「**플랫폼의 라벨 동작과 맞아야 한다**」고만 하고, 예시로 「`click` 을 칸에 보낼 **수 있다**」 · 「다른 플랫폼에서는 **포커스만 주거나 아무것도 안 할 수도 있다**」를 든다. **두 번째 `click` 은 이 판의 관찰**이다.

```text
  감싼 라벨의 글자를 한 번 누르면 — 이벤트 둘, 라벨 리스너는 두 번

  진짜 클릭 ──> click #1  target = 글자(span)
                 window(캡처) → label ──┐
                                        │ 디스패치가 끝난 뒤 라벨의 활성화 동작
                                        ▼
               click #2  target = 체크박스        ← 체크가 뒤집힌 채 리스너에 들어온다
                 window(캡처) → 체크박스 → label   ← ★ 라벨을 한 번 더 지난다
                                        │
                                        ▼
               change  (체크박스)

  for 로 가리킨 라벨이면 click #2 는 체크박스 → (라벨 없음) — 라벨이 조상이 아니라서
```

### (3) 창 ② — 두 번 토글되는 함정 · 위임이 멈추는 자리

**언제 쓰나** — 「라벨을 눌러도 체크가 안 바뀐다」는데 리스너가 **`input.click()` 을 스스로 부르고** 있을 때 · 라벨 안에 **링크·단추**를 둘 때.

```text
$ python3 html25b-form.py 시도 html25b-25-click.html | sed -n '28,57p'
[라벨 리스너가 input.click() 을 부름]
  페이지  (기록 없음)
  뒤      click @window target=부름글자 isTrusted=true detail=1
          click @부름 target=부름글자 isTrusted=true detail=1
          click @window target=부름칸 isTrusted=false detail=0 checked=true
          click @부름칸 target=부름칸 isTrusted=false detail=0 checked=true
          click @부름 target=부름칸 isTrusted=false detail=0 checked=true
          change @부름칸 checked=true
          click @window target=부름칸 isTrusted=true detail=1 checked=false
          click @부름칸 target=부름칸 isTrusted=true detail=1 checked=false
          click @부름 target=부름칸 isTrusted=true detail=1 checked=false
          change @부름칸 checked=false
          → 부름칸.checked=false
  서버    (받은 요청 없음)
[라벨 리스너가 걸러서 부름]
  페이지  (기록 없음)
  뒤      click @window target=거름글자 isTrusted=true detail=1
          click @거름 target=거름글자 isTrusted=true detail=1
          click @window target=거름칸 isTrusted=false detail=0 checked=true
          click @거름칸 target=거름칸 isTrusted=false detail=0 checked=true
          click @거름 target=거름칸 isTrusted=false detail=0 checked=true
          change @거름칸 checked=true
          → 거름칸.checked=true
  서버    (받은 요청 없음)
[라벨 click 에서 preventDefault]
  페이지  (기록 없음)
  뒤      click @window target=막음글자 isTrusted=true detail=1
          click @막음 target=막음글자 isTrusted=true detail=1
          → 막음칸.checked=false
  서버    (받은 요청 없음)
(exit 0)
```

- ★★★ **라벨 리스너가 `input.click()` 을 부르면 체크가 두 번 뒤집혀 제자리다** — `부름칸.checked=false`. 순서 — ① 진짜 클릭이 라벨에 온다 → ② 리스너가 `input.click()` 을 불러 **켠다**(`isTrusted=false`, `change … true`) → ③ 그 `click` 이 라벨로 버블해 **리스너가 또 불리지만** 이번 `input.click()` 은 **아무 일도 안 한다**(명세의 `click()` — 「그 요소의 **click in progress flag** 가 켜져 있으면 돌아간다」) → ④ 진짜 클릭의 디스패치가 끝나고 **라벨의 활성화 동작이 한 번 더 `click` 을 보내 끈다**(`isTrusted=true`, `change … false`). **`change` 가 두 번 났는데 결과는 그대로다.**
- ★★ **고치는 법은 라벨 자신의 `click` 을 막는 것이다** — 「걸러서 부름」은 `target` 이 칸이 아닐 때 `preventDefault()` 를 부르고 나서 `input.click()` 을 부른다. **토글은 한 번**(`change … true`)이고 결과가 **`true`** 다. 라벨의 활성화 동작은 **라벨 쪽 `click` 의 기본 동작**이라 `preventDefault()` 로 막힌다([web-api 17번](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md)의 「기본 동작은 디스패치가 **끝난 뒤** 돈다 — 그래서 막을 수 있다」와 같은 축이다).
- ★ **그냥 `preventDefault()` 만 부르면 칸에 아무것도 안 간다** — 「막음」은 둘째 `click` 이 **아예 없다**(줄이 둘).

```text
$ python3 html25b-form.py 시도 html25b-25-click.html | sed -n '58,$p'
[라벨 안의 span]
  페이지  (기록 없음)
  뒤      click @window target=안쪽글자 isTrusted=true detail=1
          click @안쪽 target=안쪽글자 isTrusted=true detail=1
          click @window target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽칸 target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽 target=안쪽칸 isTrusted=true detail=1 checked=true
          change @안쪽칸 checked=true
          → 안쪽칸.checked=true
  서버    (받은 요청 없음)
[라벨 안의 a[href]]
  페이지  (기록 없음)
  뒤      click @window target=안쪽링크 isTrusted=true detail=1
          click @안쪽 target=안쪽링크 isTrusted=true detail=1
          → 안쪽칸.checked=false
  서버    (받은 요청 없음)
[라벨 안의 href 없는 a]
  페이지  (기록 없음)
  뒤      click @window target=안쪽앵커 isTrusted=true detail=1
          click @안쪽 target=안쪽앵커 isTrusted=true detail=1
          click @window target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽칸 target=안쪽칸 isTrusted=true detail=1 checked=true
          click @안쪽 target=안쪽칸 isTrusted=true detail=1 checked=true
          change @안쪽칸 checked=true
          → 안쪽칸.checked=true
  서버    (받은 요청 없음)
[라벨 안의 button]
  페이지  (기록 없음)
  뒤      click @window target=안쪽단추 isTrusted=true detail=1
          click @안쪽 target=안쪽단추 isTrusted=true detail=1
          → 안쪽칸.checked=false
  서버    (받은 요청 없음)
[button 이 체크박스 앞에 있는 라벨의 글자]
  페이지  (기록 없음)
  뒤      click @window target=앞단추글자 isTrusted=true detail=1
          click @앞단추 target=앞단추글자 isTrusted=true detail=1
          click @window target=앞단추단추 isTrusted=true detail=1
          click @앞단추 target=앞단추단추 isTrusted=true detail=1
          → 앞단추칸.checked=false
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **라벨 안의 `a[href]`·`button` 을 누르면 체크박스에 안 간다** — 줄이 둘뿐이고 `안쪽칸.checked=false`. **`span` 을 누르면 간다**(줄 여섯, `true`). 명세 — 「라벨의 **대화형 콘텐츠 자손**(과 그 자손)을 향한 이벤트에 대해 라벨의 활성화 동작은 **아무것도 하지 않는다**」.
- ★★ **`href` 없는 `a` 는 대화형 콘텐츠가 아니다** — 그래서 **위임이 된다**(`true`). 명세의 대화형 콘텐츠 목록은 `a` 를 「**`href` 속성이 있으면**」으로만 넣는다.
- ★★★ **단추가 체크박스보다 앞에 있으면 라벨은 단추에 연결된다** — 「button 이 체크박스 앞에 있는 라벨의 글자」를 누르자 둘째 `click` 이 **`앞단추단추`** 로 갔고 체크박스는 `false` 다. `button` 도 **라벨이 될 수 있는 요소**라서 「안에 든 **첫** labelable 요소」가 단추가 된 것이다. ★ 명세의 라벨 콘텐츠 모델 — 「연결된 컨트롤이 아닌 labelable 자손을 **두지 마라**」 — 이 이 사고를 막으려는 규칙이다(파서는 고치지 않는다).

```text
  라벨 안에서 누른 자리에 따라 — 위임이 되나

  <label> <span>알림</span> <input checkbox> <a href> <a> <button> </label>
            │                   │              │       │     │
            ▼                   ▼              ▼       ▼     ▼
           위임 ●            (칸 자체)        ·      위임 ●   ·
                              한 번만                         ← 대화형 콘텐츠: 아무것도 안 한다
  대화형 콘텐츠 = a[href] · button · input(hidden 아님) · select · textarea · label · details …
  ★ href 없는 a 는 목록에 없다 → 위임된다
```

### (4) 창 ⑦ — 라벨의 이름은 어떻게 만들어지나

**언제 쓰나** — 라벨에 칸 말고 **다른 것도 넣을 때**(값·단위·선택지), 라벨을 **둘** 붙일 때, `aria-*` 와 라벨을 **같이** 쓸 때.

```html
<!-- html25b-25-name.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>25 이름의 출처</title>
</head>
<body>
<p><label>수량 <input id="n1" value="3"></label></p>
<p><label for="n2">앞</label> <input id="n2"> <label for="n2">뒤</label></p>
<p><label for="n3">라벨</label> <input id="n3" aria-label="에어리아"></p>
<p><span id="s4">가리킨 글자</span> <label for="n4">라벨</label> <input id="n4" aria-labelledby="s4"></p>
<p><input id="n5" title="제목"></p>
<p><input id="n6" placeholder="자리표시"></p>
<p><label for="n7">라벨</label> <input id="n7" title="제목"></p>
<p><label><input type="checkbox" id="n8"> 매일 <select id="s8"><option>3</option><option selected>5</option></select> 번</label></p>
<p><label for="n9" hidden>숨은 라벨</label> <input id="n9"></p>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 행 = [
  ["n1", "감싼 라벨 + 자기 value=3"], ["n2", "for 로 가리킨 라벨 둘"], ["n3", "라벨 + aria-label"],
  ["n4", "라벨 + aria-labelledby"], ["n5", "title 만"], ["n6", "placeholder 만"],
  ["n7", "라벨 + title"], ["n8", "감싼 라벨 안에 select"], ["n9", "hidden 라벨"],
];
window.__대상 = 행.map(([id]) => [id, "#" + id]);
window.__내부 = true;
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("무엇을", 26) + 칸("이름", 16) + 칸("설명", 8) + 칸("nameFrom", 16) + 칸("CDP 이름 출처", 26) + "labels"];
  for (const [id, 무엇] of 행) {
    const a = __AX[id], n = __INT[id];
    O.push(칸(id, 4) + 칸(무엇, 26) + 칸(JSON.stringify(a.이름), 16) + 칸(JSON.stringify(a.설명), 8)
      + 칸((n && n.속성.nameFrom) || "(없음)", 16) + 칸(a.이름출처 || "(없음)", 26) + document.getElementById(id).labels.length);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html25b-form.py page html25b-25-name.html
id  무엇을                    이름            설명    nameFrom        CDP 이름 출처             labels
n1  감싼 라벨 + 자기 value=3  "수량 "         ""      relatedElement  relatedElement:labelwrapped 1
n2  for 로 가리킨 라벨 둘     "앞 뒤"         ""      relatedElement  relatedElement:labelfor   2
n3  라벨 + aria-label         "에어리아"      ""      attribute       attribute:aria-label      1
n4  라벨 + aria-labelledby    "가리킨 글자"   ""      relatedElement  relatedElement:aria-labelledby 1
n5  title 만                  "제목"          ""      title           attribute:title           0
n6  placeholder 만            "자리표시"      ""      placeholder     placeholder:placeholder   0
n7  라벨 + title              "라벨"          "제목"  relatedElement  relatedElement:labelfor   1
n8  감싼 라벨 안에 select     " 매일 5 번"    ""      relatedElement  relatedElement:labelwrapped 1
n9  hidden 라벨               ""              ""      (없음)          (없음)                    1
(exit 0)
```

- ★★ **감싼 라벨 안의 자기 값은 이름에서 빠진다** — `n1` 의 이름은 `"수량 "` 이고 자기 값 `3` 이 없다. HTML-AAM 4.1.1 — 「컨트롤이 라벨에 **감싸여 있으면** 그 컨트롤의 값을 이름에서 **뺀다**」.
- ★ **라벨이 둘이면 이어 붙인다** — `n2` 는 `"앞 뒤"` · `labels` 2. HTML-AAM — 「라벨이 여럿이면 **DOM 순서로 공백을 끼워** 잇는다」.
- ★★ **`aria-label`·`aria-labelledby` 는 라벨을 이긴다** — `n3`·`n4` 의 `nameFrom` 이 `attribute`·`relatedElement`(가리킨 글자)이고 라벨 글자는 이름에 없다. **`labels` 는 여전히 1** 이다 — 클릭 위임은 남고 이름만 바뀐다.
- **라벨이 없으면 `title` → `placeholder` 순** — `n5`·`n6`. `n7` 처럼 라벨이 있으면 `title` 은 **설명**으로 내려간다.
- ★ **감싼 라벨 안의 다른 칸은 그 값으로 이름에 들어간다** — `n8` 체크박스의 이름이 `" 매일 5 번"`(고른 선택지 `5`). ★ 이름의 **앞뒤 공백**(`"수량 "`·`" 매일 5 번"`)은 **이 판의 Chrome 이 준 글자 그대로**다 — 스크린리더가 공백을 어떻게 다루는지는 이 판이 못 본다.
- ★★ **`hidden` 라벨은 이름을 못 준다** — `n9` 는 `labels` 가 **1** 인데 이름이 `""` 다. 연결은 됐는데 이름 계산이 숨은 라벨을 건너뛴 것으로 읽힌다(해석이다). HTML-AAM 의 이 절에는 숨김에 관한 문장이 없다 — **이 판의 관찰**로 적는다(이름 출처 순서 전체의 정본은 목록의 **43번 주제**).

```text
  칸 하나의 이름 — 위에서 먼저 나오는 것이 이긴다 (HTML-AAM 4.1.1 · 이 판의 n3~n7)

  aria-labelledby ─┐
  aria-label ──────┴─> 있으면 여기서 끝          n3 "에어리아" · n4 "가리킨 글자"
  연결된 label(들) ───> 라벨 글자(둘이면 이어서) n1 · n2 · n7 · n8   (★ 감싼 칸 자신의 값은 뺀다)
  title ──────────────> n5 "제목"
  placeholder ────────> n6 "자리표시"
  없음 ───────────────> ""
```

### demo — 누를 수 있는 글자와 없는 글자

```html demo
<!-- html25b-25-demo.html -->
<p><label for="d1">for 로 이은 라벨</label> <input type="checkbox" id="d1"></p>
<p><label>감싼 라벨 <input type="checkbox"></label></p>
<p><label for="없음">for 가 빗나간 라벨 <input type="checkbox"></label></p>
<p><span>라벨 아닌 글자</span> <input type="checkbox"></p>
<style>
  label, span { padding: 4px 8px; background: #eef; }
</style>
```

> **보이는 것** — 네 줄 모두 파란 바탕의 글자 옆에 체크박스가 있다. **위의 두 글자를 누르면 체크가 켜지고, 아래 두 글자는 눌러도 아무 일이 없다.** 셋째 줄은 체크박스를 라벨이 **품고 있는데도** 그렇다.\
> **바꿔 볼 것** — 셋째 줄의 `for="없음"` 을 지우고 다시 눌러 보라 — (1) 의 「감싸기 + for 가 없는 id」 줄과 「감싸기」 줄이 갈리는 것이 그 한 속성이다

*(Chrome 151 headless 실측, 창 폭 1000: 체크박스 1·2 는 `labels.length=1`, 3·4 는 `0` — 검증 파일은 아래)*

```html
<!-- html25b-25-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 25 검증</title>
<body>
<p><label for="d1">for 로 이은 라벨</label> <input type="checkbox" id="d1"></p>
<p><label>감싼 라벨 <input type="checkbox"></label></p>
<p><label for="없음">for 가 빗나간 라벨 <input type="checkbox"></label></p>
<p><span>라벨 아닌 글자</span> <input type="checkbox"></p>
<style>
  label, span { padding: 4px 8px; background: #eef; }
</style>
<script>
const O = [];
for (const [k, i] of [...document.querySelectorAll("input")].entries()) {
  O.push("체크박스 " + (k + 1) + " · labels.length=" + i.labels.length + " · 라벨 글자=" + JSON.stringify(i.labels.length ? i.labels[0].textContent.trim() : ""));
}
document.body.append(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ python3 html25b-form.py dom html25b-25-democheck.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
체크박스 1 · labels.length=1 · 라벨 글자="for 로 이은 라벨"
체크박스 2 · labels.length=1 · 라벨 글자="감싼 라벨"
체크박스 3 · labels.length=0 · 라벨 글자=""
체크박스 4 · labels.length=0 · 라벨 글자=""
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 결과 |
|---|---|---|
| 칸과 라벨을 떨어뜨려 둔다 | `<label for="x">이름</label> … <input id="x">` | 이름 + 클릭 위임 |
| 칸을 라벨 안에 둔다 | `<label>이름 <input></label>` | 같다 |
| 둘 다 | `<label for="x">이름 <input id="x"></label>` | 같다 — `for` 가 같은 칸을 가리키면 |
| 라벨 둘 | `<label for="x">앞</label> <input id="x"> <label for="x">뒤</label>` | 이름 `"앞 뒤"` · `labels` 2 |
| 이름만(클릭 면 없이) | `aria-label="…"` · `aria-labelledby="id"` | 라벨보다 **이긴다** · 클릭 위임은 없다 |

### 어디서 헷갈리나

- **`for` 가 있으면 안에 든 칸은 무시된다** — 빗나간 `for` 는 감싸기까지 망친다.
- **`for` 는 `id` 를 가리킨다** — `name` 이 아니다.
- **라벨이 될 수 있는 요소만 연결된다** — `div`·`span`·`fieldset` 은 안 된다.
- **감싼 라벨 안에는 칸을 하나만** — 단추도 labelable 이라 **첫째를 가져간다.**

## 어디서 틀리나

### 1. 라벨로 감쌌으니 `for` 는 아무렇게나 적어도 된다고 여긴다

**`for` 가 빗나가면 안에 든 칸도 끊긴다**((1) — 「감싸기 + for 가 없는 id」 `click 0번` · 이름 `""`). 복사해 붙이다 `id` 만 바뀐 폼에서 흔하다.

### 2. 옆에 글자를 두면 이름이 된다고 여긴다

**안 된다**((1) — 「라벨 없음」 이름 `""`). 화면에서 가까운 것은 트리에서 아무 관계가 아니다.

### 3. `aria-label` 을 달았으니 라벨은 필요 없다고 여긴다

**이름은 생기지만 클릭 면이 사라진다**((1) — `aria-label` 줄 `click 0번` · `labels` 0). 작은 체크박스를 누르기 어려운 사용자에게는 **라벨 글자 전체가 누를 곳**이다.

### 4. 라벨 리스너에서 `input.click()` 을 불러 「라벨을 누르면 켜지게」 만든다

**두 번 토글되어 제자리다**((3) — `부름칸.checked=false`, `change` 두 번). 라벨은 **이미** 칸에 `click` 을 보낸다. 굳이 부르려면 라벨 쪽 `click` 을 `preventDefault()` 로 막는다(「걸러서 부름」).

### 5. 조상의 `click` 리스너 하나가 한 번 누름에 한 번 불린다고 여긴다

**감싼 라벨이면 두 번**((2) — 글자 `target` 하나, 칸 `target` 하나). `isTrusted` 로는 못 가른다(둘 다 `true`) — **`target` 으로 가른다.**

### 6. 라벨 안에 「약관 보기」 링크를 넣고 누르면 동의가 체크된다고 여긴다

**안 된다**((3) — `a[href]` 줄 `false`). 반대로 **`href` 없는 `a`** 는 체크된다 — 링크처럼 보이게 만든 가짜 링크가 동의를 켜 버린다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 연결된 컨트롤 = `for` 가 있으면 **그 `id` 의 첫 요소가 labelable 일 때만** · `for` 가 없으면 **안의 첫 labelable 자손** · 그 밖에는 **없다** | (1) |
| **명세(HTML)** | labelable = `button` · `hidden` 아닌 `input` · `meter` · `output` · `progress` · `select` · `textarea` · 폼 연관 사용자 정의 요소 | (1)·(3) |
| **명세(HTML)** | 라벨의 활성화 동작은 **플랫폼의 라벨 동작과 맞아야 한다** — 칸에 `click` 을 보낼 수도, 포커스만 줄 수도, 아무것도 안 할 수도 있다 | (2) |
| **명세(HTML)** | 대화형 콘텐츠 자손을 향한 이벤트에는 활성화 동작이 **아무것도 하지 않는다** · `a` 는 `href` 가 있을 때만 대화형 콘텐츠 | (3) |
| **명세(HTML)** | `click()` 은 **click in progress flag** 가 켜져 있으면 돌아간다(재진입 방지) | (3) |
| **명세(HTML-AAM)** | 텍스트 칸 = `aria-*` → 연결된 라벨(여럿이면 DOM 순서로 이음 · 감싸였으면 **자기 값 제외**) → `title` → `placeholder` · 그 밖의 폼 요소 = `aria-*` → 라벨 → `title` | (4) |
| **명세(HTML-AAM)** | `label` 은 **대응하는 역할 없음** | CDP 트리는 `LabelText` — [26번](../26-select-datalist-textarea/2-summary.md)의 (3) 트리 블록 |
| **구현(Chrome)** | 라벨이 칸에 **`click` 을 보낸다** · 그 `click` 이 **`isTrusted=true` · `detail=1`** · 연결된 칸에 **포커스**를 준다 | (1)·(2) |
| **구현(Chrome)** | `hidden` 라벨은 이름을 안 준다(`labels` 는 1) · 이름의 앞뒤 공백을 남긴다 | (4) |
| **이 판의 관찰** | 위 명세 줄이 **전부 그대로 동작했다** — 이 주제에서 **명세와 갈린 칸은 없었다** | (1)\~(4) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **스크린리더가 칸을 뭐라고 읽나** | 트리는 보조 기술의 **입력**이다 — 「동의 1, 체크 상자, 선택 안 됨」처럼 읽히는지는 보조 기술이 없어 **못 잰 것** |
| **모바일에서 라벨을 두드렸을 때** | 터치 입력기가 없다 — 이 판은 마우스만 눌렀다. 명세가 「플랫폼마다 다를 수 있다」고 한 자리라 **다른 플랫폼은 다를 수 있다** |
| **음성 입력(「동의 1 누르기」)** | 음성 제어 소프트웨어가 이름으로 칸을 찾는 동작 — 못 잰 것 |
| **플랫폼 접근성 API 의 라벨 관계**(`LABELLED_BY` 등) | CDP 와 내부 덤프는 Chrome 의 내부 트리까지다 |

## 언제 쓰고 언제 안 쓰나

- **칸마다 라벨을 단다** — `for`/`id` 와 감싸기 중 **하나로.** 둘 다 쓰면 `for` 가 **같은 칸**을 가리키는지 확인한다.
- **감싸기는 칸이 하나일 때만** — 설명 링크·도움말 단추는 **라벨 밖에** 둔다.
- **`aria-label` 은 라벨을 둘 자리가 없을 때만**(아이콘 단추 등) — 클릭 면이 필요한 체크박스·라디오에는 라벨.
- **라벨 리스너에서 칸을 다시 누르지 않는다** — 라벨이 이미 누른다.
- **`id` 를 바꾸는 리팩터링 뒤에는 `labels.length` 를 확인한다** — (1) 의 셋째 물음이 가장 싸게 끊김을 잡는다.

## 핵심 문장

1. **라벨은 `for`/`id` 로 가리키거나 칸을 감싸서 연결한다 — 둘의 결과는 같다(이름 + 클릭 위임).**
2. **`for` 가 있으면 안에 든 칸은 무시된다 — `for` 가 빗나가면 감싸기도 끊긴다.**
3. **연결이 끊기면 글자 클릭 · 접근 가능한 이름 · `input.labels` 가 함께 사라진다.**
4. **이 판의 Chrome 은 라벨을 누르면 칸에 두 번째 `click`(`isTrusted=true`)을 보낸다 — 감싼 라벨이면 그 `click` 이 라벨을 다시 지난다.**
5. **라벨 리스너가 `input.click()` 을 부르면 두 번 토글되어 제자리다 — 라벨 쪽 `click` 을 `preventDefault()` 로 막아야 한다.**
6. **라벨 안의 `a[href]`·`button` 을 누르면 위임이 안 된다 — `href` 없는 `a` 는 된다.**
7. **`aria-label` 은 이름만 주고 클릭 면은 안 준다.**

## 관련 자료

- [web-api 16번 — 이벤트 전파 단계](../../../../web-api/16-event-propagation-phases/2-summary.md) — 호출 순서 로그의 정본. 여기는 **라벨이 만든 둘째 이벤트가 그 경로를 어떻게 도나**.
- [web-api 17번 — `stopPropagation` 대 `preventDefault`](../../../../web-api/17-stoppropagation-vs-preventdefault/2-summary.md) — **기본 동작은 디스패치 뒤에 돈다** · 체크박스가 리스너 안에서 이미 뒤집혀 있다. 여기는 라벨의 활성화 동작이 **바로 그 기본 동작**이라는 것.
- [17번 주제](../17-table-structure/2-summary.md) · [19번 주제](../19-figure-address-hr/2-summary.md) — 창 ⑦ 의 **내부 덤프(`nameFrom`)** 를 쓴 앞 편. 19편은 `figcaption` 이 **이름이 안 된다**를, 여기는 `label` 이 **이름이 된다**를 같은 창으로 본다.
- [24번 주제](../24-input-types-choice-special/2-summary.md) — 체크박스·라디오가 무엇을 싣나.
- [27번 주제](../27-fieldset-and-legend/2-summary.md) — 칸 **묶음**의 이름(`legend`). 목록의 **43번 주제**(이름 계산 순서 전체) · **42번 주제**(ARIA 를 언제 쓰지 말아야 하나).

## 용어 풀이

- **연결된 컨트롤(labeled control)** — 라벨이 가리키는 칸 하나. `label.control`.
- **labelable 요소** — 라벨과 이을 수 있는 요소. `button`·`input`(hidden 아님)·`meter`·`output`·`progress`·`select`·`textarea`.
- **`input.labels`** — 그 칸에 연결된 라벨들의 목록. 끊기면 길이가 0.
- **활성화 동작(activation behavior)** — 요소를 「누르면」 일어나는 기본 동작. 라벨의 것은 칸에 `click` 을 보내는 것(이 판).
- **대화형 콘텐츠(interactive content)** — 사용자 조작을 위한 요소. `a[href]`·`button`·`input`·`select`·`textarea`·`label` 등.
- **click in progress flag** — `click()` 이 도는 동안 켜지는 표시. 켜져 있으면 같은 요소의 `click()` 이 아무것도 안 한다.
- **`nameFrom`** — Chrome 내부 덤프가 적는 「이름이 어디서 왔나」. `relatedElement`(다른 요소) · `attribute` · `title` · `placeholder` 등.
- **`isTrusted`** — 사용자 동작(또는 UA)이 만든 이벤트면 `true`, 스크립트가 만든 것이면 `false`.

## 더 들어가면

- **왜 명세는 라벨의 동작을 플랫폼에 맡기나** — 운영체제마다 「이름표를 누르면」의 관습이 달라서다. 명세의 예시 문장 그대로 「어떤 플랫폼에서는 칸에 `click` 을 보내고, 다른 플랫폼에서는 **포커스만 주거나 아무것도 안 할 수도** 있다」. 그래서 **두 번째 `click` 에 기대는 코드는 이식성이 없다**는 것이 명세에서 곧장 나오는 결론이다 — 이 판은 Chrome 하나라 다른 플랫폼을 재지 못했다.
- **`for` 가 이기는 이유** — 명세가 이유를 적지는 않는다. 결과만 보면 `for` 는 **명시적**이고 감싸기는 **구조에서 추론**하는 것이라, 둘이 다를 때 명시적인 쪽을 믿는 셈이다(해석이다).
- **Shadow DOM 을 건너는 라벨** — 명세의 조건은 「**같은 트리**의 labelable 요소」다. 그림자 트리 안의 칸을 바깥 라벨의 `for` 로는 못 가리킨다 — 이 배치는 던지지 않았다(그림자 트리는 [10번 주제](../10-template-slot-shadow-dom/2-summary.md)가 다룬다).
