# html/syntax/32 — `button` 의 `type` 과 폼 소유권: `form` 속성·`formaction`/`formmethod` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The button element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-button-element)(★ `type` 의 **누락 기본값·무효 기본값 = Auto 상태** · 「Auto 상태이고 **`command`·`commandfor` 가 없고** 부모가 `select` 가 아니면 **제출 단추**」 · **활성화 동작** — 「폼 소유자가 있으면 … **Auto 상태면 돌아간다**」), [「Implicit submission」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#implicit-submission)(★ **기본 단추 = 그 폼이 소유한 트리 순서로 첫 제출 단추**), [「Association of controls and forms」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#association-of-controls-and-forms)(`form` 속성), [「Form submission algorithm」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-algorithm)(**제출자 요소의** method·action·no-validate), [`requestSubmit()`](https://html.spec.whatwg.org/multipage/forms.html#dom-form-requestsubmit)·[`submit()`](https://html.spec.whatwg.org/multipage/forms.html#dom-form-submit), [「Constructing the entry list」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-the-form-data-set)(「단추인데 **제출자가 아니면** 건너뛴다」). **명세 본문은 앞 배치가 2026-09-26 에 받아 둔 사본**으로 읽었다 — 이 배치는 네트워크를 쓰지 않았다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 클릭·Enter 는 **CDP 의 진짜 마우스·키**다. 하네스는 [29번 주제](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. ★ **`command`·`commandfor`** 는 뒤에 들어온 것이다(이 배치는 도입 시점을 조회하지 않았다) — 그 둘이 **「type 없는 단추 = 제출」 규칙의 예외**를 만든다((1)).
> **선행** — [21번 주제](../21-form-submission-model/2-summary.md) — ★★★ 이 편과 가장 많이 겹친다. **제출을 일으키는 것 열여섯 시도**((2) — 단추 없는 폼의 Enter · `type=button` · `type=zzz` · `disabled` 기본 단추) · **단추마다 덮기**((3) — `formaction`·`formmethod`·`formenctype`) · **어느 `form` 에 속하나**((4) — `input` 의 `form` 속성 · 없는 id · 중첩 `form`)를 이미 쟀다. **여기서는 그 측정을 다시 하지 않고**, 거기 없던 것 — **`commandfor` 단추 · Enter 가 고르는 기본 단추의 격자 · 단추(`button`) 쪽의 소유권 · 누른 단추의 `name`/`value` 와 `requestSubmit` 의 예외** — 만 잰다.
> **경계** — **`name`/`value` 는 누른 단추만 실린다**는 [24번](../24-input-types-choice-special/2-summary.md)의 (1) 이 클릭·`requestSubmit()` 으로 쟀다 — 여기는 **Enter 와 `requestSubmit(단추)`** 쪽을 더한다. **중첩 `form` 을 파서가 버리는 것**의 정본은 [05번](../05-content-categories-and-models/2-summary.md). **`dialog` 를 여는 동작**은 목록의 **47번 주제**.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다** — 「제출됐나」는 서버가 요청을 받았나로, 「누가 제출했나」는 **서버가 받은 `act` 값**으로 판정한다. 짝으로 **창 ②**(`submit` 이벤트의 `submitter` · `button.type` · `willValidate` · `button.form`)와 **창 ①**(`--dump-dom` — 중첩 `form`)을 쓴다.

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
| **안 흔들린다** | 요청 수·메서드·경로·필드 · `submitter` · `button.type`·`willValidate`·`button.form` · 「제출된 칸 N / M」 | 시도마다 페이지를 새로 연다 · 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 제출이 **갔나** · **어디로**(경로·메서드) · **누른 단추**(`act`)((1)\~(4)) |
| **② 노드 프로브**(`submit`·`submitter` · `.type` · `willValidate` · `.form`) | ★ **쓴다** | 그 단추가 **제출 단추인가** · **어느 폼**의 것인가 · 호출이 **예외**를 던지나((1)·(3)·(4)) |
| **① `--dump-dom`** | 쓴다 | 중첩 `form` 이 **트리에 남았나**((3)) |
| **⑦ 접근성 트리** | **부적용** | 단추의 역할은 `type` 과 무관하게 `button` 이다([24번](../24-input-types-choice-special/2-summary.md)) — **잴 것이 없다** |
| **③ · ④ · ⑥** | **부적용** | 무관하다 |

- ★★ **제5의 상태 — 「제출 단추인가」를 `willValidate` 로 물었다.** 명세의 「제출 단추」 여부는 **읽는 API 가 없다.** 대신 명세가 「**제출 단추가 아닌 `button` 은 제약 검증에서 빠진다**」고 적으므로 `willValidate` 가 곧 그 대답이다. ★ **바꾼 창이 못 보는 것** — 비활성이거나 `datalist` 안이어도 거짓이 된다. 그래서 (1) 의 표본은 **그런 것 없이** 두었다.
- ★★ **18-A — 몇 군데 물었나.** (2) 는 **칸 수 둘 × 단추 구성 일곱 = 14 폼**에서 Enter 를 눌렀다. 「안 갔다」가 결론인 칸이 있어 **14 칸을 미리 선언**하고 「제출된 칸 N / 14」를 스크립트가 센다. 거짓 「안 갔다」는 「뒤늦게 온 요청 = N」이 센다.

## 한눈에 — 쉽게 말하면

**★ 폼 안의 `<button>` 은 「초인종」이다. 아무 표시가 없으면 누르는 순간 택배가 나간다(제출). 「택배 아님」 스티커(`type="button"`)를 붙여야 그냥 종만 울린다.**

택배 창구 비유다([21번](../21-form-submission-model/2-summary.md)의 「택배 보내기」를 잇는다). 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **표시 없는 초인종** | `type` 없는 `button` — **Auto 상태 = 제출 단추** |
| **「택배 아님」 스티커** | **`type="button"`** — 누르면 **아무것도 안 한다**(`click` 만) |
| **다른 방 호출 버튼** | **`commandfor`** — `type` 이 없어도 **제출 단추가 아니다** · ★ 폼 안에서는 **`type="button"` 이 있어야 호출도 된다** |
| **현관 Enter 키** | **암묵 제출** — 그 폼이 소유한 **첫 제출 단추**를 대신 누른다 |
| **송장의 「보낸 사람」 칸** | **제출자(submitter)** — 그 단추의 `name`/`value`·`formaction`·`formmethod`·`formnovalidate` 만 쓰인다 |
| **다른 창구 소속 표** | **`form="id"`** — 트리 위치와 상관없이 **그 폼의 단추** |

- ★★★ **`type` 없는 「+」 단추를 누르니 손잡이가 수량을 올리고 곧바로 폼이 나갔다** — 서버가 `qty=2` 를 받았다((1)).
- ★★★ **폼 안의 `type` 없는 `commandfor` 단추는 아무것도 안 했다** — 제출도 대화상자 열기도 없다. `type="button"` 을 붙이자 열렸다((1)).
- ★★ **제출된 칸 10 / 14 · 명세 열과 갈린 칸 0 / 14** — **폼 앞에 있는 `form=` 단추가 Enter 의 기본 단추**가 됐다((2)).
- ★★ **Enter 는 기본 단추의 `formaction`·`formmethod`·`formnovalidate` 와 `name`/`value` 를 그대로 썼다**((4)).

```text
  폼 안의 <button> 을 눌렀을 때 — 명세의 활성화 동작 (위에서부터)

  비활성인가? ── 예 ──> 끝
     │
  폼 소유자가 있나? ── 예 ──┬─ 제출 단추(submit · 또는 Auto + command/commandfor 없음)? ──> 제출   ← 「+」 사고
     │                     ├─ reset?  ──> 초기화
     │                     └─ Auto 상태(= type 없음 · commandfor 있음)? ──> 끝  ★ 아무것도 안 한다
     │
  commandfor 대상이 있나? ──> 명령 실행 (show-modal 등)           ← 폼 안이면 type="button" 이어야 여기까지 온다
```

> **제출자(submitter)** — 제출을 일으킨 단추. `SubmitEvent.submitter` 로 읽힌다.\
> 예: 「저장」·「삭제」 두 단추가 `name="act"` 를 나눠 가지면 서버는 `act` 값으로 **무엇을 눌렀나**를 안다 — **누른 것만** 실리기 때문이다.

## 이 주제가 답하려는 질문

1. **폼 안 `<button>` 은 왜 제출하나** — 그 규칙의 예외는 무엇인가.
2. **Enter 는 어느 단추를 누르나** — 단추 구성과 칸 수에 따라.
3. **단추는 어느 폼의 것인가, 그리고 제출은 그 단추의 무엇을 쓰나** — `form` 속성 · `formaction` · `name`/`value` · `requestSubmit` 대 `submit`.

## 동작 방식

### (1) 창 ⑤ + 창 ② — `type` 없는 단추의 사고와 `commandfor` 의 예외

**언제 쓰나** — 「수량 +」·「미리보기」·「모달 열기」 단추를 폼 안에 두었는데 **페이지가 새로 고쳐진다**·**아무 일도 없다**를 가를 때.

폼 안에 단추 넷 — `type` 없는 「+」 · `type=button` 인 「+」(둘 다 같은 손잡이가 수량을 올린다) · `type` 없는 `commandfor` 단추 · `type=button` 인 `commandfor` 단추. 아래 표본 아홉은 **폼 밖**에 두고 `.type` 과 `willValidate`(= 제출 단추인가)를 읽는다 — 다섯째 시도는 그중 `b8` 을 누른다.

```html
<!-- html29b-32-accident.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 폼 안의 단추</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="주문" action="/r" method="post">
  <input id="수량" name="qty" value="1">
  <button id="더하기1">+</button>
  <button id="더하기2" type="button">+</button>
  <button id="열기" commandfor="창" command="show-modal">열기</button>
  <button id="열기2" type="button" commandfor="창" command="show-modal">열기</button>
</form>
<dialog id="창"><p>창</p></dialog>
<div id="표본">
  <button id="b1">type 없음</button>
  <button id="b2" type="submit">submit</button>
  <button id="b3" type="reset">reset</button>
  <button id="b4" type="button">button</button>
  <button id="b5" type="BUTTON">BUTTON</button>
  <button id="b6" type="zzz">zzz</button>
  <button id="b7" type="">빈 글자</button>
  <button id="b8" commandfor="창" command="show-modal">commandfor</button>
  <button id="b9" type="submit" commandfor="창" command="show-modal">submit + commandfor</button>
</div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
for (const id of ["더하기1", "더하기2"]) document.getElementById(id).addEventListener("click", () => {
  const q = document.getElementById("수량");
  q.value = String(Number(q.value) + 1);
  적기("손잡이가 올림 qty=" + q.value);
});
window.__표 = "종합";
const 뒤 = "JSON.stringify({ qty: document.getElementById('수량').value, 창: document.getElementById('창').open })";
window.__시도 = [
  { 이름: "type 없는 + 클릭", 단계: [["click", "#더하기1"]], 뒤 },
  { 이름: "type=button 인 + 클릭", 단계: [["click", "#더하기2"]], 뒤 },
  { 이름: "type 없는 commandfor 단추 클릭", 단계: [["click", "#열기"]], 뒤 },
  { 이름: "type=button 인 commandfor 단추 클릭", 단계: [["click", "#열기2"]], 뒤 },
  { 이름: "폼 밖 표본 b8 클릭", 단계: [["click", "#b8"]], 뒤 },
];
window.__종합 = 결과 => {
  const O = [];
  for (const r of 결과) {
    const S = r.뒤 ? JSON.parse(r.뒤) : null;
    O.push(칸(r.이름, 36) + "서버 " + r.요청.length + "번" + (r.필드 ? " " + r.서버.find(l => l.trim().startsWith("필드")).trim() : "")
      + " · 뒤 " + (S ? "qty=" + S.qty + " 창.open=" + S.창 : "(이동해서 없음)"));
  }
  O.push("");
  // 제출 단추인가 — 명세: 제출 단추가 아닌 button 은 제약 검증에서 빠진다 → willValidate 로 읽는다
  O.push(칸("id", 4) + 칸("속성", 56) + 칸(".type", 10) + "willValidate");
  for (const b of document.querySelectorAll("#표본 button")) {
    const 속성 = [...b.attributes].filter(a => a.name !== "id").map(a => a.name + "=" + JSON.stringify(a.value)).join(" ") || "(없음)";
    O.push(칸(b.id, 4) + 칸(속성, 56) + 칸(JSON.stringify(b.type), 10) + b.willValidate);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html29b-form.py 시도 html29b-32-accident.html | sed -n '1,/^$/p'
[type 없는 + 클릭]
  페이지  click(더하기1 · detail=1) → 손잡이가 올림 qty=2 → submit(submitter=더하기1)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「qty=2」
          필드  qty=「2」
[type=button 인 + 클릭]
  페이지  click(더하기2 · detail=1) → 손잡이가 올림 qty=2
  뒤      {"qty":"2","창":false}
  서버    (받은 요청 없음)
[type 없는 commandfor 단추 클릭]
  페이지  click(열기 · detail=1)
  뒤      {"qty":"1","창":false}
  서버    (받은 요청 없음)
[type=button 인 commandfor 단추 클릭]
  페이지  click(열기2 · detail=1)
  뒤      {"qty":"1","창":true}
  서버    (받은 요청 없음)
[폼 밖 표본 b8 클릭]
  페이지  click(b8 · detail=1)
  뒤      {"qty":"1","창":true}
  서버    (받은 요청 없음)

(exit 0)
```

```text
$ python3 html29b-form.py 시도 html29b-32-accident.html | sed -n '/^type 없는 + 클릭 /,$p'
type 없는 + 클릭                    서버 1번 필드  qty=「2」 · 뒤 (이동해서 없음)
type=button 인 + 클릭               서버 0번 · 뒤 qty=2 창.open=false
type 없는 commandfor 단추 클릭      서버 0번 · 뒤 qty=1 창.open=false
type=button 인 commandfor 단추 클릭 서버 0번 · 뒤 qty=1 창.open=true
폼 밖 표본 b8 클릭                  서버 0번 · 뒤 qty=1 창.open=true

id  속성                                                    .type     willValidate
b1  (없음)                                                  "submit"  true
b2  type="submit"                                           "submit"  true
b3  type="reset"                                            "reset"   false
b4  type="button"                                           "button"  false
b5  type="BUTTON"                                           "button"  false
b6  type="zzz"                                              "submit"  true
b7  type=""                                                 "submit"  true
b8  commandfor="창" command="show-modal"                    "button"  false
b9  type="submit" commandfor="창" command="show-modal"      "submit"  true
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`type` 없는 「+」는 손잡이를 돌리고 그대로 제출했다** — 기록이 `click → 손잡이가 올림 qty=2 → submit(submitter=더하기1)` 이고 서버가 **`qty=「2」`** 를 받았다. 페이지는 떠났다(「뒤」 줄이 없다). 명세 — `type` 의 **누락 기본값은 Auto 상태**이고, Auto 상태인데 `command`·`commandfor` 가 없고 부모가 `select` 가 아니면 **제출 단추**다. [21번](../21-form-submission-model/2-summary.md)의 「어디서 틀리나」 1 이 이 규칙을 적었고, 여기는 **손잡이까지 돈 뒤에 나간다**는 순서를 더한다 — 손잡이의 결과(`qty=2`)가 **그대로 서버로** 갔다.
- ★★ **`type=button` 인 「+」는 손잡이만 돌았다** — `qty=2` 가 페이지에 남고 서버는 0.
- ★★★ **폼 안의 `type` 없는 `commandfor` 단추는 아무것도 안 했다** — 제출도 없고 `창.open=false`. 명세의 활성화 동작 — 「폼 소유자가 있으면: 제출 단추면 제출 · reset 이면 초기화 · **Auto 상태면 돌아간다**」 — `commandfor` 를 보는 단계는 **그 뒤**에 있다. `commandfor` 가 있어 **제출 단추는 아니지만**(표본 `b8` 의 `willValidate=false`) **Auto 상태라서** 명령까지 못 간다. **`type="button"` 을 붙이니 열렸다**(`창.open=true`). **같은 `type` 없는 `commandfor` 단추라도 폼 밖**(표본 `b8`)이면 폼 소유자 갈래를 안 타서 **열렸다** — 사고는 **폼 안**에서만 난다.
- ★★ **`.type` 은 Auto 를 두 이름으로 돌려준다** — `type` 없음·`zzz`·빈 글자는 **`"submit"`**, `commandfor` 만 있는 `b8` 은 **`"button"`**. 둘 다 명세상 **Auto 상태**인데 IDL 이 **그 상태가 하는 일**(제출 단추인가)을 따라 이름을 고른 모양이다(관찰 — 명세의 `type` IDL 문장은 이 편이 사본에서 찾지 못했다). `BUTTON` 은 대소문자 무시로 **`"button"`**.
- ★ **`type="submit"` 을 적으면 `commandfor` 가 있어도 제출 단추다**(`b9` — `willValidate=true`). 명세 — 「**또는** `type` 이 Submit Button 상태면」.

```text
  type 과 commandfor 가 정하는 것 (표본 · 폼 안의 두 시도)

  type 속성         commandfor   제출 단추인가(willValidate)   .type      폼 안에서 누르면
  (없음)·zzz·""     없음          예                           "submit"   제출 ★ 사고
  (없음)            있음          아니다                       "button"   아무것도 안 한다 ★
  button            있음          아니다                       "button"   명령(대화상자 열기)
  submit            있음          예                           "submit"   제출
  button·BUTTON     없음          아니다                       "button"   click 만
  reset             없음          아니다                       "reset"    초기화
```

### (2) 창 ⑤ — Enter 한 번 × 칸 수 둘 × 단추 구성 일곱

**언제 쓰나** — 「검색창에서 Enter 가 안 먹는다」·「Enter 를 치니 엉뚱한 단추로 제출됐다」를 가를 때.

열네 폼이 **칸 수(1·2)** 와 **단추 구성**만 다르다. 단추는 전부 `name="act"` 를 나눠 가지므로 **서버가 받은 `act`** 가 누른 단추다. `G` 는 **폼보다 앞(폼 밖)** 에 `form=` 으로 이 폼을 가리키는 단추를 둔다. Enter 는 첫 칸에 포커스를 두고 **진짜 키**로 눌렀다. 「명세 열」은 따로 둔 파일이다.

```html
<!-- html29b-32-implicit.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 Enter 와 단추 구성</title>
<script src="html29b-rec.js"></script>
<script src="html29b-32-spec.js"></script>
</head>
<body>
<div id="자리"></div>
<script>
addEventListener("submit", e => 적기("누른 " + (e.submitter ? e.submitter.value : "null")), true);
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// 단추 구성 — [표시, 폼 앞(폼 밖)에 둘 것, 폼 안에 둘 것]
const 구성 = {
  A: ["단추 없음", "", ""],
  B: ["제출 단추", "", '<button name="act" value="go">보냄</button>'],
  C: ["type=button 만", "", '<button type="button" name="act" value="btn">단추</button>'],
  D: ["type=button 다음 제출 단추", "", '<button type="button" name="act" value="btn">단추</button><button name="act" value="go">보냄</button>'],
  E: ["type=reset 다음 제출 단추", "", '<button type="reset" name="act" value="rst">지움</button><button name="act" value="go">보냄</button>'],
  F: ["disabled 제출 단추 다음 제출 단추", "", '<button name="act" value="dis" disabled>보냄</button><button name="act" value="go">보냄</button>'],
  G: ["폼 앞의 form= 제출 단추 다음 안의 제출 단추", "OUT", '<button name="act" value="in">보냄</button>'],
};
const 자리 = document.getElementById("자리");
const 목록 = [];
for (const n of [1, 2]) for (const [k, [표시, 앞, 안]] of Object.entries(구성)) {
  const id = "f" + n + k;
  const 칸들 = '<input name="a" value="1">' + (n === 2 ? '<input name="b" value="2">' : "");
  자리.insertAdjacentHTML("beforeend", (앞 ? '<button form="' + id + '" name="act" value="out">밖</button>' : "")
    + '<form id="' + id + '" action="/r">' + 칸들 + 안 + "</form>");
  목록.push([id, n, k, 표시]);
}
window.__표 = "종합";
window.__시도 = 목록.map(([id, n, k, 표시]) => ({ 이름: id, 단계: [["enter", "#" + id + " input[name=a]"]] }));
window.__종합 = 결과 => {
  const O = [칸("폼", 5) + 칸("칸 수", 6) + 칸("단추 구성", 44) + 칸("제출", 6) + 칸("submitter", 11) + "서버가 받은 필드"];
  let 제출 = 0, 명세갈림 = 0;
  결과.forEach((r, i) => {
    const [id, n, k, 표시] = 목록[i];
    const s = r.기록.find(x => x.startsWith("누른 ")) || "";
    const 됨 = r.요청.length > 0;
    제출 += 됨; 명세갈림 += 됨 !== 명세제출[n + k];
    O.push(칸(id, 5) + 칸(String(n), 6) + 칸(표시, 44) + 칸(됨 ? "예" : "—", 6) + 칸(s ? s.slice(3) : "—", 11)
      + (됨 ? r.서버.find(l => l.trim().startsWith("필드")).trim().replace(/^필드\s+/, "") : "(요청 없음)"));
  });
  O.push("제출된 칸 = " + 제출 + " / " + 결과.length);
  O.push("명세 열과 갈린 칸 = " + 명세갈림 + " / " + 결과.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```javascript
// html29b-32-spec.js
// 명세 열 — 「Implicit submission」: 기본 단추 = 그 폼이 소유한 첫 제출 단추(트리 순서)
// 기본 단추가 있고 비활성이 아니면 그 단추에 click · 비활성이면 아무것도 안 한다 · 제출 단추가 없으면 막는 칸이 둘 이상일 때 돌아가고 아니면 폼 자체로 제출
// type=button·type=reset 은 제출 단추가 아니다 · 폼 밖이라도 form= 으로 소유된 단추는 트리 순서에 든다
const 명세제출 = {
  "1A": true,  "1B": true, "1C": true,  "1D": true, "1E": true, "1F": false, "1G": true,
  "2A": false, "2B": true, "2C": false, "2D": true, "2E": true, "2F": false, "2G": true,
};
```

```text
$ python3 html29b-form.py 시도 html29b-32-implicit.html | sed -n '/^폼 /,$p'
폼   칸 수 단추 구성                                   제출  submitter  서버가 받은 필드
f1A  1     단추 없음                                   예    null       a=「1」
f1B  1     제출 단추                                   예    go         a=「1」 · act=「go」
f1C  1     type=button 만                              예    null       a=「1」
f1D  1     type=button 다음 제출 단추                  예    go         a=「1」 · act=「go」
f1E  1     type=reset 다음 제출 단추                   예    go         a=「1」 · act=「go」
f1F  1     disabled 제출 단추 다음 제출 단추           —    —         (요청 없음)
f1G  1     폼 앞의 form= 제출 단추 다음 안의 제출 단추 예    out        act=「out」 · a=「1」
f2A  2     단추 없음                                   —    —         (요청 없음)
f2B  2     제출 단추                                   예    go         a=「1」 · b=「2」 · act=「go」
f2C  2     type=button 만                              —    —         (요청 없음)
f2D  2     type=button 다음 제출 단추                  예    go         a=「1」 · b=「2」 · act=「go」
f2E  2     type=reset 다음 제출 단추                   예    go         a=「1」 · b=「2」 · act=「go」
f2F  2     disabled 제출 단추 다음 제출 단추           —    —         (요청 없음)
f2G  2     폼 앞의 form= 제출 단추 다음 안의 제출 단추 예    out        act=「out」 · a=「1」 · b=「2」
제출된 칸 = 10 / 14
명세 열과 갈린 칸 = 0 / 14
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **제출된 칸 10 / 14 · 명세 열과 갈린 칸 0 / 14.** 안 간 넷은 **칸 둘 + 단추 없음**(`f2A`) · **칸 둘 + `type=button` 만**(`f2C`) · **`disabled` 가 첫 제출 단추**(`f1F`·`f2F`).
- ★★★ **기본 단추는 「트리 순서로 첫 제출 단추」다** — `type=button`(`D`)·`type=reset`(`E`)이 앞에 있어도 **건너뛰고** 뒤의 제출 단추가 눌렸다(`act=go`). 둘 다 **제출 단추가 아니기** 때문이다. 명세 — 「폼의 **기본 단추**는 그 폼이 소유한 **트리 순서로 첫 제출 단추**」.
- ★★★ **첫 제출 단추가 `disabled` 면 뒤에 멀쩡한 제출 단추가 있어도 안 간다**(`F`) — 명세 — 「기본 단추가 활성화 동작이 있고 **비활성이 아니면** click 을 쏜다」. 기본 단추는 **이미 정해졌고**(비활성인 첫째), 그것이 비활성이라 끝난다. 「단추 없음」 갈래로도 안 간다 — **제출 단추가 있으니까.** [21번](../21-form-submission-model/2-summary.md)의 `마` 가 단추 하나로 본 것을 **뒤에 둘째가 있어도** 같다로 넓혔다.
- ★★★ **폼 앞의 `form=` 단추가 기본 단추다**(`G`) — **폼 밖**에 있지만 소유자가 이 폼이고 트리 순서로 **안의 단추보다 앞**이다. 서버가 받은 필드도 **`act=「out」` 이 맨 앞**이다(항목 목록이 **트리 순서**다).
- ★★ **단추 없는 폼은 칸 수로 갈린다**(`A`·`C`) — 칸 하나면 **폼 자체로** 제출(`submitter=null` · `act` 없음), 둘이면 아무 일도 없다. 21번의 `나`·`다`·`바` 와 같은 결과다(**그 셋은 다시 잰 칸**이다 — 격자를 채우려고 넣었다).
- ★★ **Enter 로 눌린 단추의 `name`/`value` 가 실렸다** — `act=go`·`act=out`. Enter 는 **기본 단추에 click 을 쏘는 것**이므로 그 단추가 **제출자**다.

```text
  Enter 가 고르는 단추 — 기본 단추 = 이 폼이 소유한 트리 순서의 첫 「제출 단추」

  [밖 form=f](G)  ─┐
  <form id=f>      │ 트리 순서
    [type=button] ─┼─ 제출 단추 아님 → 건너뜀
    [type=reset]  ─┼─ 제출 단추 아님 → 건너뜀
    [disabled]    ─┼─ 제출 단추 ● ← 여기서 멈춤 → 비활성이라 아무것도 안 함  (F)
    [보냄]        ─┘  제출 단추 (F 에서는 둘째라 기본 단추가 못 된다)
  </form>
  제출 단추가 하나도 없으면 → 막는 칸이 1 개면 폼 자체로 · 2 개↑면 아무것도 (A · C)
```

### (3) 창 ⑤ + 창 ② + 창 ① — 단추는 어느 폼의 것인가

**언제 쓰나** — 레이아웃 때문에 「보냄」 단추를 폼 **밖**(머리글·바닥글)에 둘 때.

[21번](../21-form-submission-model/2-summary.md)의 (4) 는 **`input`** 에 `form` 을 줬다. 여기는 **`button`** 에 준다 — 단추는 **어느 폼을 제출하나**까지 정한다.

```html
<!-- html29b-32-owner.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 단추의 폼 소유자</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="갑" action="/r"><input name="a" value="1"><button id="안단추" name="act" value="in">안</button></form>
<button id="밖단추" form="갑" name="act" value="out">밖</button>
<button id="없는폼단추" form="없음" name="act" value="none">없는 id</button>
<form id="을" action="/r2"><input name="b" value="2"><button id="을안갑" form="갑" name="act" value="inB">을 안</button></form>
<form id="겉" action="/r4"><input name="c" value="3"><form id="속" action="/r5"><button id="속단추" name="act" value="nest">속</button></form></form>
<button id="속가리킴" form="속" name="act" value="toNest">속을 가리킴</button>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 단추 = ["안단추", "밖단추", "없는폼단추", "을안갑", "속단추", "속가리킴"];
window.__표 = "종합";
window.__시도 = 단추.map(id => ({ 이름: id + " 클릭", 단계: [["click", "#" + id]] }));
window.__종합 = 결과 => {
  const O = [칸("단추", 12) + 칸("부모", 10) + 칸("form 속성", 10) + 칸("button.form", 13) + 칸("요청", 10) + "서버가 받은 필드"];
  결과.forEach((r, i) => {
    const b = document.getElementById(단추[i]);
    const 부모 = b.parentElement.tagName.toLowerCase() + (b.parentElement.id ? "#" + b.parentElement.id : "");
    O.push(칸(b.id, 12) + 칸(부모, 10) + 칸(b.getAttribute("form") || "(없음)", 10) + 칸(b.form ? "form#" + b.form.id : "null", 13)
      + 칸(r.요청.length ? r.요청.map(q => q.메서드 + " " + q.경로).join(",") : "없음", 10)
      + (r.요청.length ? r.서버.find(l => l.trim().startsWith("필드")).trim().replace(/^필드\s+/, "") : "—"));
  });
  O.push("form 개수 = " + document.forms.length + " · id = " + [...document.forms].map(f => f.id).join(" · "));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html29b-form.py 시도 html29b-32-owner.html | sed -n '/^단추 /,$p'
단추        부모      form 속성 button.form  요청      서버가 받은 필드
안단추      form#갑   (없음)    form#갑      GET /r    a=「1」 · act=「in」
밖단추      body      갑        form#갑      GET /r    a=「1」 · act=「out」
없는폼단추  body      없음      null         없음      —
을안갑      form#을   갑        form#갑      GET /r    a=「1」 · act=「inB」
속단추      form#겉   (없음)    form#겉      GET /r4   c=「3」 · act=「nest」
속가리킴    body      속        null         없음      —
form 개수 = 3 · id = 갑 · 을 · 겉
뒤늦게 온 요청 = 0
(exit 0)
```

같은 페이지의 `--dump-dom` 에서 중첩 부분만 —

```text
$ python3 html29b-form.py dom html29b-32-owner.html | sed -n '/<form id="겉"/,/속가리킴/p'
<form id="겉" action="/r4"><input name="c" value="3"><button id="속단추" name="act" value="nest">속</button></form>
<button id="속가리킴" form="속" name="act" value="toNest">속을 가리킴</button>
(exit 0)
```

- ★★★ **폼 밖 단추의 `form="갑"` 은 갑을 제출한다** — `밖단추` 는 `body` 에 있는데 **`GET /r`** 로 `a=「1」 · act=「out」`. 명세의 폼 소유자 — 「`form` 속성이 있으면 **그 id 의 `form`** 이 소유자」.
- ★★★ **다른 폼 안에 있어도 `form` 속성이 이긴다** — `을안갑` 은 `form#을` 의 자식인데 **갑을 제출**했다(`GET /r` · 을의 `b` 는 **안 실렸다**). 을은 **제출되지 않았다.**
- ★★ **없는 id 를 가리킨 단추는 아무것도 안 한다** — `없는폼단추` 의 `button.form` 은 **`null`** 이고 요청이 없다. 명세의 활성화 동작 — 「**폼 소유자가 있으면** …」 갈래를 못 타고, `commandfor` 도 없으니 끝난다. **가장 가까운 조상으로 되돌아가지 않는다**(조상 폼이 없는 자리지만, `form` 속성이 있으면 명세는 조상을 보지 않는다 — 21번의 `i5`).
- ★★★ **중첩 `form` 은 파서가 버렸다** — `--dump-dom` 에 `<form id="속">` 이 **없고** `속단추` 는 **겉 안**에 있다. `속단추` 는 **겉의 `action`(`/r4`)** 으로 `c=3 · act=nest` 를 보냈다. 그래서 **`form="속"` 을 가리킨 단추**(`속가리킴`)는 **소유자가 없다**(`null` · 요청 없음) — 소스에는 `id="속"` 이 있는데 **트리에는 없다.** [05번](../05-content-categories-and-models/2-summary.md)의 「안쪽 `<form>` 시작 태그는 통째로 무시된다」가 **`form` 속성의 대상**까지 없앤다.
- **폼 개수 = 3**(`갑 · 을 · 겉`).

```text
  단추의 폼 소유자 — 트리 위치 대 form 속성 (이 판)

  단추            트리에서 어디         form 속성    소유자      눌렀을 때
  안단추          갑 안                 —           갑          갑 제출 (act=in)
  밖단추          body                  갑          갑 ★        갑 제출 (act=out)
  을안갑          을 안                 갑          갑 ★        갑 제출 · 을은 아무 일 없음
  없는폼단추      body                  없음         null        아무것도 안 함
  속단추          겉 안 (속은 버려짐)    —           겉          겉 제출 (/r4)
  속가리킴        body                  속           null ★      아무것도 안 함 (속이 트리에 없다)
```

### (4) 창 ⑤ + 창 ② — 누가 제출했나: Enter · `requestSubmit` · `submit()`

**언제 쓰나** — 「Enter 로 보냈더니 `formaction` 쪽으로 갔다」·「스크립트로 보냈더니 누른 단추 값이 없다」·「`requestSubmit` 이 예외를 던진다」를 가를 때.

한 폼에 **빈 `required` 칸**을 넣었다 — 검증이 도는 길은 **`invalid` 로 멈추고**, 첫 단추(`formnovalidate`)로 가는 길은 통과한다. 첫 단추는 `formaction="/r2" formmethod="post"` 이고, 둘째는 폼의 설정(`GET /r`)을 쓴다.

```html
<!-- html29b-32-submitter.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>32 누가 제출했나</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r">
  <input id="q" name="q" value="1">
  <input id="빈" name="빈" required>
  <button id="첫" name="act" value="a" formaction="/r2" formmethod="post" formnovalidate>첫 단추</button>
  <button id="둘" name="act" value="b">둘째 단추</button>
  <button id="보통" type="button" name="act" value="c" formaction="/r3">type=button</button>
</form>
<form id="남" action="/r9"><button id="남단추">남의 단추</button></form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 폼 = "document.getElementById('폼')", $ = id => "document.getElementById('" + id + "')";
const 불러 = 식 => ["js", "(() => { try { " + 식 + "; 적기('반환됨'); } catch (e) { 적기('예외 ' + e.name); } return 1; })()"];
window.__표 = "종합";
window.__시도 = [
  { 이름: "첫 단추 클릭", 단계: [["click", "#첫"]] },
  { 이름: "둘째 단추 클릭", 단계: [["click", "#둘"]] },
  { 이름: "q 에서 Enter", 단계: [["enter", "#q"]] },
  { 이름: "requestSubmit()", 단계: [불러(폼 + ".requestSubmit()")] },
  { 이름: "requestSubmit(둘째)", 단계: [불러(폼 + ".requestSubmit(" + $("둘") + ")")] },
  { 이름: "requestSubmit(첫)", 단계: [불러(폼 + ".requestSubmit(" + $("첫") + ")")] },
  { 이름: "submit()", 단계: [불러(폼 + ".submit()")] },
  { 이름: "type=button 단추 클릭", 단계: [["click", "#보통"]] },
  { 이름: "requestSubmit(type=button 단추)", 단계: [불러(폼 + ".requestSubmit(" + $("보통") + ")")] },
  { 이름: "requestSubmit(남의 폼 단추)", 단계: [불러(폼 + ".requestSubmit(" + $("남단추") + ")")] },
];
window.__종합 = 결과 => {
  const O = [칸("시도", 34) + 칸("submit", 8) + 칸("invalid", 9) + 칸("요청", 11) + 칸("서버가 받은 필드", 30) + "호출"];
  for (const r of 결과) {
    const 필드 = r.요청.length ? r.서버.find(l => l.trim().startsWith("필드")).trim().replace(/^필드\s+/, "") : "—";
    const 호출 = r.기록.find(x => x === "반환됨" || x.startsWith("예외")) || "—";
    O.push(칸(r.이름, 34) + 칸(r.기록.some(x => x.startsWith("submit(")) ? "났다" : "—", 8) + 칸(r.기록.some(x => x.startsWith("invalid")) ? "났다" : "—", 9)
      + 칸(r.요청.length ? r.요청.map(q => q.메서드 + " " + q.경로).join(",") : "없음", 11) + 칸(필드, 30) + 호출);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html29b-form.py 시도 html29b-32-submitter.html | sed -n '/^시도 /,$p'
시도                              submit  invalid  요청       서버가 받은 필드              호출
첫 단추 클릭                      났다    —       POST /r2   q=「1」 · 빈=「」 · act=「a」 —
둘째 단추 클릭                    —      났다     없음       —                            —
q 에서 Enter                      났다    —       POST /r2   q=「1」 · 빈=「」 · act=「a」 —
requestSubmit()                   —      났다     없음       —                            반환됨
requestSubmit(둘째)               —      났다     없음       —                            반환됨
requestSubmit(첫)                 났다    —       POST /r2   q=「1」 · 빈=「」 · act=「a」 반환됨
submit()                          —      —       GET /r     q=「1」 · 빈=「」             반환됨
type=button 단추 클릭             —      —       없음       —                            —
requestSubmit(type=button 단추)   —      —       없음       —                            예외 TypeError
requestSubmit(남의 폼 단추)       —      —       없음       —                            예외 NotFoundError
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **Enter 는 첫 단추의 설정을 전부 썼다** — `q 에서 Enter` 가 **`POST /r2`** 로 `act=「a」` 를 보냈고, **빈 `required` 가 있는데도 `invalid` 가 없다**(`formnovalidate`). 첫 단추를 **클릭한 것과 한 글자도 같다.** Enter 는 기본 단추에 **click 을 쏘고**, 제출 알고리즘은 **제출자 요소의** method·action·no-validate 를 읽는다.
- ★★★ **둘째 단추 클릭은 `invalid` 로 멈췄다** — 둘째는 `formnovalidate` 가 **없으니** 폼의 검증이 돈다. **같은 폼인데 누른 단추에 따라 검증이 갈린다**([29번](../29-constraint-validation/2-summary.md)의 `formnovalidate`).
- ★★★ **`requestSubmit()` 은 제출자가 폼 자신이다** — `formaction`·`formnovalidate` 가 **안 쓰여** 검증이 돌고 멈췄다. **`requestSubmit(첫)`** 은 첫 단추의 덮기를 **전부** 써서 `POST /r2 · act=a`. 명세 — 「submitter 가 null 이면 **submitter 를 이 폼으로**」.
- ★★★ **`submit()` 은 검증·`submit` 이벤트 없이 폼의 설정으로 갔다** — `GET /r` · `act` **없음** · 빈 칸 그대로(`빈=「」`). [21번](../21-form-submission-model/2-summary.md)의 「어디서 틀리나」 3 과 같다. 명세 — 「`submit()` 은 **submitted from submit() method** 를 참으로 제출」 → 검증·이벤트 단계를 건너뛴다.
- ★★ **`requestSubmit` 의 두 예외** — `type=button` 단추를 주면 **`TypeError`**(제출 단추가 아니다), 남의 폼 단추를 주면 **`NotFoundError`**(소유자가 이 폼이 아니다). 명세의 두 줄 그대로다.
- ★ **`type=button` 단추의 `formaction` 은 쓰일 데가 없다** — 클릭해도 요청이 없다. `formaction` 은 **제출 단추의 속성**이다.

```text
  같은 폼 — 제출을 일으킨 것에 따라 쓰이는 설정 (이 판)

  무엇이 일으켰나       제출자       검증    method·경로   act
  첫 단추 클릭          첫           건넘    POST /r2      a     ← formaction·formmethod·formnovalidate
  q 에서 Enter          첫 (기본)     건넘    POST /r2      a     ← 위와 한 글자도 같다
  requestSubmit(첫)     첫           건넘    POST /r2      a
  둘째 단추 클릭        둘째         돈다 → invalid 로 멈춤
  requestSubmit()       폼 자신      돈다 → invalid 로 멈춤
  submit()              (없음)       없음    GET /r        —     ← 이벤트도 없다
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 폼 안의 「그냥 단추」 | `<button type="button">` | `click` 만 — **손잡이가 도는 단추는 전부 이것** |
| 폼 안의 대화상자 여는 단추 | `<button type="button" commandfor="창" command="show-modal">` | `type` 이 없으면 **아무것도 안 한다** |
| 폼 밖의 제출 단추 | `<button form="폼id">` | 그 폼을 제출 · **트리 순서로 앞이면 Enter 의 기본 단추** |
| 단추마다 다른 곳으로 | `<button formaction="/x" formmethod="post">` | 그 단추가 **제출자일 때만**(Enter 로 눌려도) |
| 무엇을 눌렀나 알리기 | `<button name="act" value="save">` | **누른 단추만** 실린다 |
| 스크립트로 제출 | `form.requestSubmit(단추)` | 검증·`submit` 이벤트·단추의 덮기 **전부** |

### 어디서 헷갈리나

- **`type` 없는 `button` 은 `type="submit"` 과 같다** — 단 `commandfor` 가 있으면 제출 단추가 아니다.
- **Enter 는 「첫 제출 단추」를 누른다** — 첫 **단추**가 아니다.
- **`form` 속성은 조상 폼을 이긴다** — 그리고 없는 id 면 **소유자가 없다.**
- **`requestSubmit()` 은 단추를 안 주면 단추의 설정을 하나도 안 쓴다.**

## 어디서 틀리나

### 1. 폼 안의 「+」·「미리보기」 단추에 `type` 을 안 적는다

**손잡이가 돌고 곧바로 제출된다**((1) — 서버 `qty=2`). 폼 안의 단추는 **전부 `type` 을 적는다.**

### 2. 폼 안의 모달 여는 단추를 `commandfor` 만으로 만든다

**아무것도 안 한다**((1) — `창.open=false`). **`type="button"`** 을 같이 적는다.

### 3. 「취소」를 앞에, 「저장」을 뒤에 두면 Enter 가 「취소」를 누를까 걱정해 `type=button` 을 뺀다

**반대다** — `type=button` 이면 Enter 가 **건너뛰고** 「저장」을 누른다((2) — `D`). 빼면 「취소」가 **첫 제출 단추**가 된다.

### 4. 첫 제출 단추를 `disabled` 로 두고 Enter 는 둘째로 갈 거라 여긴다

**아무 데도 안 간다**((2) — `F`).

### 5. 머리글의 `form=` 단추를 두었더니 Enter 가 그 단추로 간다

**트리 순서로 앞이라 기본 단추다**((2) — `G`). 그 단추에 `formaction` 이 있으면 Enter 도 그쪽으로 간다((4)).

### 6. 스크립트로 보낼 때 `form.submit()` 을 쓴다

**검증·`submit` 이벤트·단추 값이 다 빠진다**((4) — `GET /r` · `act` 없음). **`requestSubmit(단추)`** 를 쓴다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | `type` 누락·무효 기본값 = **Auto** · Auto + `command`/`commandfor` 없음 + 부모가 `select` 아님 = **제출 단추** · 또는 Submit Button 상태 | (1) |
| **명세(HTML)** | 활성화 동작 — 폼 소유자가 있으면 제출 / reset / **Auto 면 돌아간다** → 그 뒤에야 `commandfor` | (1) |
| **명세(HTML)** | 제출 단추가 아닌 `button` 은 제약 검증에서 빠진다 | (1) — `willValidate` |
| **명세(HTML)** | 기본 단추 = 소유한 **트리 순서 첫 제출 단추** · 비활성이 아니면 click · 제출 단추가 없으면 막는 칸 수로 | (2) |
| **명세(HTML)** | `form` 속성의 id 가 소유자 · 없으면 소유자 없음 | (3) |
| **명세(HTML)** | 제출은 **제출자 요소의** method·action·no-validate · 항목 목록은 **제출자인 단추만** | (2)·(4) |
| **명세(HTML)** | `requestSubmit` — 제출 단추 아니면 `TypeError` · 소유자 다르면 `NotFoundError` · 없으면 폼 자신 · `submit()` 은 검증·이벤트를 건너뛴다 | (4) |
| **구현(Chrome)** | `.type` 이 Auto 를 `"submit"`/`"button"` 두 이름으로 돌려준다 | (1) |
| **이 판의 관찰** | 제출된 칸 **10 / 14** · 명세 열과 갈린 칸 **0 / 14** | (2) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| **모바일 가상 키보드의 「이동」·「완료」 키가 암묵 제출을 일으키나** | 가상 키보드가 없다 — 명세도 「플랫폼에 따라 Enter 가」 정도로만 적는다 |
| **`button.type` IDL 의 명세 문장** | 받아 둔 사본에서 그 줄을 찾지 못했다 — (1) 의 두 이름은 **관찰**로만 적었다 |

## 언제 쓰고 언제 안 쓰나

- **폼 안의 모든 `button` 에 `type` 을 적는다** — 제출은 `submit`, 나머지는 `button`. 기본값에 기대지 않는다.
- **`commandfor` 단추는 폼 안이면 `type="button"` 과 함께.**
- **`form` 속성** — 레이아웃상 폼 밖에 둬야 할 때만. **트리 순서가 Enter 를 바꾼다**는 것을 기억한다.
- **「무엇을 눌렀나」는 `name`/`value`** — 스크립트로 보낼 때는 **`requestSubmit(그 단추)`**.

## 핵심 문장

1. **`type` 없는 `button` 은 Auto 상태이고, `commandfor` 가 없으면 제출 단추다 — 폼 안의 손잡이 단추가 폼을 보내는 사고의 뿌리다.**
2. **폼 안의 `type` 없는 `commandfor` 단추는 제출도 명령도 안 한다 — 활성화 동작이 Auto 상태에서 먼저 돌아가기 때문이다.**
3. **Enter 는 그 폼이 소유한 트리 순서의 첫 「제출 단추」를 누른다 — `type=button`·`reset` 은 건너뛰고, 그 단추가 비활성이면 아무것도 안 한다(이 판: 10 / 14 · 명세와 0 갈림).**
4. **`form` 속성은 트리 위치를 이긴다 — 폼 밖·다른 폼 안의 단추도 그 폼을 제출하고, 트리 순서로 앞이면 Enter 의 기본 단추가 된다.**
5. **제출은 제출자 단추의 `formaction`·`formmethod`·`formnovalidate`·`name`/`value` 를 쓴다 — Enter 로 눌려도 같고, `requestSubmit()`(단추 없이)·`submit()` 은 그 어느 것도 안 쓴다.**

## 관련 자료

- [21번 주제](../21-form-submission-model/2-summary.md) — ★ **제출을 일으키는 것**((2))·**단추마다 덮기**((3))·**`input` 의 폼 소유권**((4))의 정본. 이 편은 그 위에 `commandfor` · Enter 격자 · 단추의 소유권 · 제출자의 설정을 더했다.
- [24번 주제](../24-input-types-choice-special/2-summary.md) — **누른 단추만 실린다**(클릭·그림 단추·`requestSubmit()`).
- [05번 주제](../05-content-categories-and-models/2-summary.md) — 중첩 `form` 을 파서가 버린다.
- [29번 주제](../29-constraint-validation/2-summary.md) — `formnovalidate`·`novalidate` 가 끄는 것.
- 목록의 **47번 주제**(`dialog` — 여는 동작과 모달).

## 용어 풀이

- **Auto 상태** — `button` 의 `type` 이 없거나 무효할 때의 상태. `commandfor` 가 없으면 제출 단추다.
- **제출 단추(submit button)** — 누르면 폼을 제출하는 단추. `willValidate` 가 참인 `button`.
- **활성화 동작(activation behavior)** — 누르면 일어나는 일. `button` 은 비활성 → 폼 소유자 → `commandfor` 순서로 본다.
- **기본 단추(default button)** — 그 폼이 소유한 트리 순서의 첫 제출 단추. Enter 가 누른다.
- **폼 소유자(form owner)** — 컨트롤이 속한 폼. `form` 속성이 있으면 그 id.
- **제출자(submitter)** — 제출을 일으킨 단추(또는 폼 자신).
- **`commandfor`/`command`** — 단추가 다른 요소(대화상자·팝오버)에게 명령을 보내게 하는 속성.

## 더 들어가면

- **왜 Auto 상태가 폼 안에서 먼저 돌아가나** — `commandfor` 를 새로 넣으면서 **옛 페이지의 `type` 없는 단추**가 갑자기 명령을 보내지 않게 하려는 순서로 읽힌다 — 폼 안에서는 옛 동작(제출)이냐 아무것도 아니냐만 남는다(해석이다 — 명세의 비규범 설명은 이 사본에서 찾지 못했다).
- **`formtarget`** — 제출 결과를 열 창. 이 판은 던지지 않았다.
- **그림 단추(`type=image`)의 좌표** — [24번](../24-input-types-choice-special/2-summary.md)의 `img.x`·`img.y`.
