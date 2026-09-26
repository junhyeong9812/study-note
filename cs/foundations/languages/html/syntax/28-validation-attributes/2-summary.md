# html/syntax/28 — 검증 속성: `required`/`pattern`/`min`/`max`/`step`/`minlength`/`maxlength` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The input element」](https://html.spec.whatwg.org/multipage/input.html) — 상태마다의 **「지정하지 말아야 하고 적용되지 않는(do not apply) 속성」 목록**, [`pattern`](https://html.spec.whatwg.org/multipage/input.html#the-pattern-attribute)(★ **컴파일된 패턴** — `RegExpCreate(…, "v")` · `^(?:` … `)$`), [`min`·`max`](https://html.spec.whatwg.org/multipage/input.html#the-min-and-max-attributes)(★ **`min` 이 눈금의 기준도 정한다**), [`step`](https://html.spec.whatwg.org/multipage/input.html#the-step-attribute)(★ **step base** 알고리즘 · 허용 눈금), Range 상태의 「눈금에 안 맞으면 **반올림해야 한다**」, 그리고 [「Limiting user input length」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#limiting-user-input-length:-the-maxlength-attribute)·`minlength`(★ **「값이 마지막으로 사용자 편집으로 바뀌었고」**). **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다.**
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 사용자 편집은 **CDP 의 진짜 키 입력**(`Input.dispatchKeyEvent`·`Input.insertText`)이다. 로케일은 **`ko-KR`**(환경 변수 `LANGUAGE`). 하네스는 [25번 주제](../25-label-association/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. ★ **`pattern` 을 `v` 플래그로 컴파일하는 것은 명세의 현재 판**이다(`v` 는 ES2024 — [JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md)). 언제 `u` 에서 바뀌었는지는 이 문서가 확인하지 않았다.
> **선행** — [23번 주제](../23-input-types-number-date/2-summary.md)(`validity` 깃발 · `range` 의 값 고침) · [22번 주제](../22-input-types-text/2-summary.md)(`typeMismatch`).
> **경계** — ★★★ **검증이 언제 도나**(단추 클릭·Enter·`requestSubmit()` 은 돌고, **`form.submit()` 은 건너뛴다**)와 **`curl` 로 우회하면 서버가 무효한 값을 그대로 받는 것**은 [21번 주제](../21-form-submission-model/2-summary.md)가 이미 쟀다 — 여기서 다시 재지 않는다. **유효성 상태를 CSS 가 읽는 경로**(`:invalid`·`:user-invalid`)와 **`novalidate`** 는 목록의 **29번 주제**와 [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md), **스크립트로 읽고 덮어쓰는 표면**(`checkValidity`·`reportValidity`·`setCustomValidity`)은 web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **60번**이다 — 여기는 **속성이 어느 깃발을 켜나**까지.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ②(`validity` 불리언 깃발)다.** `validationMessage` 문구는 **구현**이라 근거로 쓰지 않는다([22번](../22-input-types-text/2-summary.md)). 「이 속성이 이 타입에서 **무시된다**」는 깃발이 **안 켜진 것**이라 침묵이 근거다 — 그래서 **칸 마흔둘을 미리 선언하고** 「무시된 칸 N / 42」를 스크립트가 센다.

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
| **흔들린다** | `validationMessage` 문구 · 콘솔 경고의 문구 | 구현이다 — **근거로 쓰지 않는다**(콘솔 경고는 「있다」만 쓴다) |
| **고정했다** | 로케일 = `ko-KR` | 날짜 칸의 ArrowUp 이 올린 조각(이 판은 **연도**)이 로케일의 조각 순서에 달렸을 수 있어 고정했다 — 다른 로케일은 안 돌려 봤다 |
| **안 흔들린다** | `validity` 깃발 · `.value` · 「무시된 칸 N / 42」·「갈린 칸」 | 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **② 노드 프로브**(`validity` 깃발 · `.value`) | ★ **쓴다 — 본체** | 속성이 그 타입에서 **깃발을 켜나** · 값을 **고치나**((1)\~(4)) |
| **② 의 짝 — 속성 없는 쌍둥이** | ★ **쓴다** | 「값이 고쳐졌다」가 **그 속성 때문인가**((1) — 제5의 상태) |
| **콘솔 기록**(CDP `Log.entryAdded`) | 쓴다 | 무효한 `pattern` 이 **조용히 버려지나**((3)) |
| **⑤ 서버 요청 로그** | **부적용** — 21번 인용 | 검증이 제출을 막는 것·`curl` 우회는 [21번](../21-form-submission-model/2-summary.md)의 (2)·(5) 가 쟀다 |
| **⑦ 접근성 트리** | **안 쟀다** | 검증 속성이 트리에 남기는 상태(`required`·무효 표시)는 이 판이 묻지 않았다 — 「부적용」이 아니라 **안 돌려 본 것**이다 |
| **① · ③ · ④ · ⑥** | **부적용** | 무관하다 |

- ★★★ **제5의 상태 — `range` 는 깃발로 못 묻는다.** `range` 는 범위·눈금에 안 맞는 값을 **고쳐 버려서**([23번](../23-input-types-number-date/2-summary.md)) 깃발이 **언제나 꺼져 있다.** 그래서 「속성이 먹었나」를 **값**으로 물었다 — 칸마다 **같은 타입·같은 값·같은 편집을 받되 그 속성만 없는 쌍둥이**를 두고, 둘의 `.value` 가 다르면 「속성이 값을 고쳤다」로 센다. ★ **바꾼 창이 못 보는 것** — 쌍둥이와 같게 고쳐지는 것(`range` 의 빈 값 → 50 처럼 **타입이 고치는 것**)은 속성의 몫으로 안 센다. 그래서 `required` 인 `range` 는 「·」다.
- ★★ **18-A — 몇 군데 물었나.** (1) 은 **속성 일곱 × 타입 여섯 = 42 곳**을 **두 판**(편집 없음 · 진짜 키로 편집한 뒤) 물었다. 「무시됐다」는 **그 42 곳 중 깃발도 값도 안 움직인 곳**이다.

## 한눈에 — 쉽게 말하면

**★ 검증 속성은 「서류 양식의 기재 요령」이다. 요령마다 붙는 칸이 정해져 있다 — 「숫자로 적으시오」 옆에 「글자 수 제한」을 붙여 봐야 아무도 안 센다.**

서류 창구 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **「반드시 기재」** | `required` → `valueMissing` — 거의 모든 칸 · ★ **`range` 에는 안 붙는다**(비울 수가 없다) |
| **「이 모양으로 적으시오」** | `pattern` → `patternMismatch` — **글자 칸**(`text`·`email` 등)에만 · `number`·`date` 는 **무시** |
| **「○ 이상 · ○ 이하」** | `min`/`max` → `rangeUnderflow`/`rangeOverflow` — **수·날짜 칸**에만 · `text` 는 **무시** |
| **「○ 단위로」** | `step` → `stepMismatch` — 수·날짜 칸 · ★ 눈금의 **출발점은 `min`**(없으면 `value` 속성) |
| **「○ 자 이상 · 이내」** | `minlength`/`maxlength` → `tooShort`/`tooLong` — 글자 칸 · ★ **손님이 직접 고쳐 쓴 뒤에만** 센다 |
| **슬라이더 칸** | `range` — 요령을 어기면 **직원이 알아서 고쳐 적는다**(깃발이 아니라 값) |
| **체크 칸** | `checkbox` — `required` 하나만 |

- **무시된 칸은 22 / 42** — 명세의 「적용되지 않는다」 목록과 **한 칸도 안 갈렸다**((1)).
- ★★★ **`min=1 step=2` 면 `4` 는 틀리고 `5` 는 맞다** — 눈금이 1·3·5·… 다((2)).
- ★★ **`pattern="a|bc"` 는 `abc` 를 거절한다** — 브라우저가 `^(?:a|bc)$` 로 감싼다((3)).
- ★★ **스크립트로 넣은 긴 값은 `maxlength` 를 넘어도 `tooLong` 이 안 켜진다**((4)).

```text
  속성 하나가 깃발을 켜기까지 — 세 관문 (위에서 막히면 깃발은 없다)

  속성 ──┬─ ① 이 타입에 적용되나?          (명세의 상태별 「do not apply」 목록)
         │        아니다 ──> 무시 (깃발 · 값 모두 그대로)            pattern × number · min × text
         ├─ ② 값 조건이 맞나?               (빈 값은 pattern·minlength 가 안 본다)
         ├─ ③ 편집 조건이 맞나?             (minlength·maxlength 만 — 「마지막 변경이 사용자 편집」)
         │        아니다 ──> 깃발 없음                              스크립트로 넣은 긴 값
         └─ 깃발 ──> 제출 때 검증이 돌면 막힌다   ← 언제 도나·우회는 21번 (form.submit()·curl)

  range 는 ② 에서 깃발 대신 값을 고친다 (must round)  ── 깃발은 언제나 꺼져 있다
```

> **`validity` 깃발** — `ValidityState` 의 불리언들. `valueMissing`·`patternMismatch`·`rangeUnderflow`·`rangeOverflow`·`stepMismatch`·`tooShort`·`tooLong` 이 이 주제의 일곱이다.\
> 예: `min=5` 인 `number` 에 `1` → `rangeUnderflow = true`.

## 이 주제가 답하려는 질문

1. **각 속성은 어느 타입에서만 의미가 있나** — 무시되면 무엇이 보이나(아무것도).
2. **`step` 의 눈금은 어디서 출발하나** — `min` · `value` 속성 · 기본값, 그리고 값이 **들어온 경로**가 결과를 바꾸나.
3. **`pattern`·`maxlength` 는 적힌 대로 동작하나** — 암묵 감싸기·`v` 플래그, 사용자 편집 조건.

## 동작 방식

### (1) 창 ② — 속성 일곱 × 타입 여섯

**언제 쓰나** — 「`number` 칸에 `pattern` 을 달았는데 아무 일도 없다」·「`text` 칸에 `min` 을 줬다」 같은 보고를 받았을 때. **에러도 경고도 없이 무시된다.**

칸마다 값은 **「그 속성이 먹는다면 깃발이 켜질」 값**으로 골라 **스크립트로** 넣었고, `minlength`·`maxlength` 두 줄만 둘째 판에서 **진짜 키로 편집**했다(글자 칸은 한 글자 더 치거나 End + Backspace, 날짜는 ArrowUp, 체크박스는 Space, 슬라이더는 ArrowRight). 각 칸에는 **속성만 없는 쌍둥이**가 같은 값·같은 편집을 받는다. 「명세」 열은 **따로 둔 파일**이다.

```html
<!-- html25b-28-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 속성과 타입</title>
<script src="html25b-28-spec.js"></script>
</head>
<body>
<div id="자리"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 타입 = ["text", "email", "number", "date", "checkbox", "range"];
// [속성, 속성값, 깃발, 타입별 스크립트 값]  — 값은 「그 속성이 먹는다면 깃발이 켜질」 값으로 골랐다
const 줄 = [
  ["required", "", "valueMissing", { text: "", email: "", number: "", date: "", checkbox: null, range: "" }],
  ["pattern", "x+", "patternMismatch", { text: "abc", email: "a@b.c", number: "5", date: "2026-01-01", checkbox: null, range: "50" }],
  ["min", "5|2026-01-02", "rangeUnderflow", { text: "1", email: "a@b.c", number: "1", date: "2026-01-01", checkbox: null, range: "1" }],
  ["max", "5|2026-01-01", "rangeOverflow", { text: "9", email: "a@b.c", number: "9", date: "2026-01-02", checkbox: null, range: "9" }],
  ["step", "2", "stepMismatch", { text: "3", email: "a@b.c", number: "3", date: "2026-01-02", checkbox: null, range: "3" }],
  ["minlength", "20", "tooShort", { text: "a", email: "a@b.c", number: "1", date: "2026-01-01", checkbox: null, range: "50" }],
  ["maxlength", "1", "tooLong", { text: "abc", email: "a@b.co", number: "123", date: "2026-01-01", checkbox: null, range: "50" }],
];
const 자리 = document.getElementById("자리");
for (const [속성, 속성값, , 값들] of 줄) {
  for (const t of 타입) {
    const i = document.createElement("input");
    i.type = t; i.id = 속성 + "-" + t;
    const [보통, 날짜] = 속성값.split("|");
    i.setAttribute(속성, t === "date" && 날짜 ? 날짜 : 보통);
    if (속성 === "step" && t === "date") i.min = "2026-01-01";   // 눈금의 기준을 못 박는다
    const 대조 = document.createElement("input");                 // 같은 타입 · 같은 값 · 같은 편집 — 속성만 없다
    대조.type = t; 대조.id = "대조-" + i.id;
    if (속성 === "step" && t === "date") 대조.min = "2026-01-01";
    자리.append(i, 대조);
    if (값들[t] !== null) { i.value = 값들[t]; 대조.value = 값들[t]; }   // 스크립트로 넣는다
  }
}
// 사용자 편집 — minlength·maxlength 줄만 (진짜 키 입력)
const 편집 = [];
for (const 속성 of ["minlength", "maxlength"]) {
  for (const 앞 of ["#", "#대조-"]) {
    const 샵 = t => 앞 + 속성 + "-" + t;
    if (속성 === "minlength") { 편집.push(["type", 샵("text"), "b"], ["type", 샵("email"), "d"], ["type", 샵("number"), "2"]); }
    else { for (const t of ["text", "email", "number"]) 편집.push(["key", 샵(t), "End", "End", 35], ["keyhere", "Backspace", "Backspace", 8]); }
    편집.push(["key", 샵("date"), "ArrowUp", "ArrowUp", 38], ["key", 샵("checkbox"), " ", "Space", 32, " "], ["key", 샵("range"), "ArrowRight", "ArrowRight", 39]);
  }
}
const 뒤 = "JSON.stringify(Object.fromEntries([...document.querySelectorAll('#자리 input')].map(i => [i.id, { v: i.value, c: i.checked, f: Object.fromEntries(['valueMissing','patternMismatch','rangeUnderflow','rangeOverflow','stepMismatch','tooShort','tooLong'].map(k => [k, i.validity[k]])) }])))";
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [
  { 이름: "편집 없음 (스크립트 값만)", 단계: [], 뒤 },
  { 이름: "minlength·maxlength 줄을 진짜 키로 편집한 뒤", 단계: 편집, 뒤 },
];
window.__종합 = 결과 => {
  const O = [];
  let 명세갈림 = 0;
  for (const r of 결과) {
    const S = JSON.parse(r.뒤);
    O.push("── " + r.이름);
    O.push((칸("속성 \\ 타입", 12) + 타입.map(t => 칸(t, 11)).join("")).trimEnd());
    let 무시 = 0, 전체 = 0;
    for (const [속성, , 깃발, 값들] of 줄) {
      let 행글 = 칸(속성, 12);
      for (const t of 타입) {
        const id = 속성 + "-" + t, s = S[id];
        const 켬 = s.f[깃발], 바뀜 = s.v !== S["대조-" + id].v;
        const 먹음 = 켬 || 바뀜;
        무시 += !먹음; 전체++;
        if (r === 결과[결과.length - 1] && 먹음 !== 명세[t].includes(속성)) 명세갈림++;
        행글 += 칸(켬 ? "깃발" : 바뀜 ? "값 " + s.v : "·", 11);
      }
      O.push(행글.trimEnd());
    }
    O.push("무시된 칸 = " + 무시 + " / " + 전체 + "  (「깃발」= 그 속성의 validity 깃발이 켜짐 · 「값 N」= 깃발 없이 값이 N 으로 고쳐짐(속성 없는 짝과 다름) · 「·」= 아무 일 없음)");
    O.push("");
  }
  const 편집뒤 = JSON.parse(결과[1].뒤);
  O.push("편집 뒤의 값 — " + ["minlength", "maxlength"].map(a => a + ": " + 타입.map(t => t + "=" + JSON.stringify(편집뒤[a + "-" + t].v) + (t === "checkbox" ? "(checked=" + 편집뒤[a + "-" + t].c + ")" : "")).join(" ")).join("\n              "));
  O.push("명세의 적용 목록과 갈린 칸(편집 뒤) = " + 명세갈림 + " / " + 줄.length * 타입.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```javascript
// html25b-28-spec.js
// 명세 열 — 타입마다 「적용되는」 속성 목록. 명세의 상태별 「must not be specified and do not apply」 목록에서 이 표의 일곱 속성을 뺀 나머지다.
const 명세 = {
  text: ["required", "pattern", "minlength", "maxlength"], email: ["required", "pattern", "minlength", "maxlength"],
  number: ["required", "min", "max", "step"], date: ["required", "min", "max", "step"],
  checkbox: ["required"], range: ["min", "max", "step"],
};
```

```text
$ python3 html25b-form.py --lang=ko-KR 시도 html25b-28-grid.html | sed -n '/^── /,$p'
── 편집 없음 (스크립트 값만)
속성 \ 타입 text       email      number     date       checkbox   range
required    깃발       깃발       깃발       깃발       깃발       ·
pattern     깃발       깃발       ·          ·          ·          ·
min         ·          ·          깃발       깃발       ·          값 5
max         ·          ·          깃발       깃발       ·          값 5
step        ·          ·          깃발       깃발       ·          값 4
minlength   ·          ·          ·          ·          ·          ·
maxlength   ·          ·          ·          ·          ·          ·
무시된 칸 = 26 / 42  (「깃발」= 그 속성의 validity 깃발이 켜짐 · 「값 N」= 깃발 없이 값이 N 으로 고쳐짐(속성 없는 짝과 다름) · 「·」= 아무 일 없음)

── minlength·maxlength 줄을 진짜 키로 편집한 뒤
속성 \ 타입 text       email      number     date       checkbox   range
required    깃발       깃발       깃발       깃발       깃발       ·
pattern     깃발       깃발       ·          ·          ·          ·
min         ·          ·          깃발       깃발       ·          값 5
max         ·          ·          깃발       깃발       ·          값 5
step        ·          ·          깃발       깃발       ·          값 4
minlength   깃발       깃발       ·          ·          ·          ·
maxlength   깃발       깃발       ·          ·          ·          ·
무시된 칸 = 22 / 42  (「깃발」= 그 속성의 validity 깃발이 켜짐 · 「값 N」= 깃발 없이 값이 N 으로 고쳐짐(속성 없는 짝과 다름) · 「·」= 아무 일 없음)

편집 뒤의 값 — minlength: text="ab" email="a@b.cd" number="12" date="2027-01-01" checkbox="on"(checked=true) range="51"
              maxlength: text="ab" email="a@b.c" number="12" date="2027-01-01" checkbox="on"(checked=true) range="51"
명세의 적용 목록과 갈린 칸(편집 뒤) = 0 / 42
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **무시된 칸은 편집 뒤 22 / 42 — 명세의 적용 목록과 갈린 칸은 0 / 42** 다. 타입마다 **먹은 속성**이 명세 목록 그대로다 — `text`·`email` 은 `required`·`pattern`·`minlength`·`maxlength` · `number`·`date` 는 `required`·`min`·`max`·`step` · `checkbox` 는 `required` 하나 · `range` 는 `min`·`max`·`step`.
- ★★★ **`pattern` 은 `number`·`date` 에서 무시되고, `min`/`max`/`step` 은 `text`·`email` 에서 무시된다** — 깃발도 값도 안 움직였다(「·」). 명세의 Number 상태 목록 — 「다음 속성은 **지정하지 말아야 하고 적용되지 않는다**: … `maxlength`, `minlength`, …, **`pattern`**, …」. 에러도 콘솔 경고도 없다 — **침묵이 결론**이다.
- ★★ **`range` 는 깃발 대신 값을 고쳤다** — `min=5` 에 `1` → **`5`**, `max=5` 에 `9` → **`5`**, `step=2` 에 `3` → **`4`**. 쌍둥이(속성 없음)는 `1`·`9`·`3` 을 그대로 들고 있어서 「속성이 먹었다」가 선다. 깃발은 **셋 다 꺼져 있다** — [23번](../23-input-types-number-date/2-summary.md)의 「`range` 는 무효가 될 수 없다」.
- ★★ **`required` 는 `range` 에서만 무시** — `range` 는 **빈 값이 없어서** 적용 목록에서 빠졌다(명세의 Range 상태 목록에 `required` 가 있다). **`checkbox` 의 `required` 는 먹는다** — 체크 안 된 칸이 `valueMissing`.
- ★★★ **`minlength`·`maxlength` 는 편집 없이는 `text`·`email` 에서도 조용하다** — 첫 판(편집 없음)은 두 줄이 **전부 「·」** 라 무시된 칸이 **26 / 42** 다. 진짜 키로 한 번 고친 뒤에야 `text`·`email` 네 칸이 **「깃발」** 이 됐다. 이것이 (4) 의 「사용자 편집 조건」이다.
- ★ **`number`·`date`·`checkbox`·`range` 는 편집해도 `minlength`·`maxlength` 가 안 먹는다** — 편집 뒤 값(`12`·`2027-01-01`·`on`·`51`)이 쌍둥이와 **같게** 바뀌었고 깃발도 없다.

```text
  명세의 적용 목록 = 이 판의 격자 (편집 뒤) — ● 먹음 · ○ 값을 고침 · · 무시

                text   email   number   date   checkbox   range
  required       ●       ●       ●        ●       ●         ·      ← range 는 빈 값이 없다
  pattern        ●       ●       ·        ·       ·         ·      ← 글자 칸만
  min            ·       ·       ●        ●       ·         ○      ← 수·날짜 칸만
  max            ·       ·       ●        ●       ·         ○
  step           ·       ·       ●        ●       ·         ○
  minlength      ●       ●       ·        ·       ·         ·      ← 글자 칸만 · 사용자 편집 뒤에만
  maxlength      ●       ●       ·        ·       ·         ·
                                                       무시된 칸 22 / 42 · 갈린 칸 0 / 42
```

### (2) 창 ② — `step` 의 눈금은 `min` 에서 출발한다

**언제 쓰나** — 「`min=1 step=2` 인데 4 가 왜 안 되나」 · 「값을 속성으로 줬더니 `stepMismatch` 가 안 켜진다」를 가를 때.

```html
<!-- html25b-28-step.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 눈금의 기준</title>
</head>
<body>
<input id="n1" type="number" min="1" step="2">
<input id="n2" type="number" min="1" step="2">
<input id="n3" type="number" min="1" step="2" value="4">
<input id="n4" type="number" step="2" value="3">
<input id="n5" type="number" step="2" value="3">
<input id="n6" type="number" step="2" value="3">
<input id="n7" type="number" step="2">
<input id="n8" type="number" min="1" step="2">
<input id="a2" type="number" step="0.5" value="1.3">
<input id="a2s" type="number" step="0.5">
<input id="t1" type="time" step="900" value="13:07">
<input id="t2" type="time" step="900">
<input id="t3" type="time" step="900" min="13:00" value="13:07">
<input id="d1" type="date" step="7" min="2026-09-07" value="2026-09-10">
<input id="d2" type="date" step="7" value="2026-09-10">
<input id="r1" type="range" min="1" step="2" value="4">
<input id="r2" type="range" min="1" step="2">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const $ = id => document.getElementById(id);
// 스크립트로 넣는 값 — [id, 값]
const 스크립트 = [["n1", "4"], ["n2", "5"], ["n5", "4"], ["n6", "5"], ["n7", "3"], ["a2s", "1.3"], ["t2", "13:07"], ["r2", "4"]];
for (const [id, v] of 스크립트) $(id).value = v;
const 모두 = [...document.querySelectorAll("input")];
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [{ 이름: "n8 에 진짜 키로 4 를 친다", 단계: [["type", "#n8", "4"]],
  뒤: "JSON.stringify(Object.fromEntries([...document.querySelectorAll('input')].map(i => [i.id, [i.value, i.validity.stepMismatch]])))" }];
window.__종합 = 결과 => {
  const S = JSON.parse(결과[0].뒤);
  const O = [칸("id", 4) + 칸("속성", 58) + 칸("값을 넣은 길", 17) + 칸(".value", 14) + "stepMismatch"];
  for (const i of 모두) {
    const 속성 = [...i.attributes].filter(a => a.name !== "id").map(a => a.name + "=" + JSON.stringify(a.value)).join(" ");
    const 스 = 스크립트.find(([id]) => id === i.id);
    const 길 = i.id === "n8" ? "진짜 키 \"4\"" : 스 ? "스크립트 " + JSON.stringify(스[1]) : "속성만";
    O.push(칸(i.id, 4) + 칸(속성, 58) + 칸(길, 17) + 칸(JSON.stringify(S[i.id][0]), 14) + S[i.id][1]);
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html25b-form.py --lang=ko-KR 시도 html25b-28-step.html | sed -n '/^id /,$p'
id  속성                                                      값을 넣은 길     .value        stepMismatch
n1  type="number" min="1" step="2"                            스크립트 "4"     "4"           true
n2  type="number" min="1" step="2"                            스크립트 "5"     "5"           false
n3  type="number" min="1" step="2" value="4"                  속성만           "4"           true
n4  type="number" step="2" value="3"                          속성만           "3"           false
n5  type="number" step="2" value="3"                          스크립트 "4"     "4"           true
n6  type="number" step="2" value="3"                          스크립트 "5"     "5"           false
n7  type="number" step="2"                                    스크립트 "3"     "3"           true
n8  type="number" min="1" step="2"                            진짜 키 "4"      "4"           true
a2  type="number" step="0.5" value="1.3"                      속성만           "1.3"         false
a2s type="number" step="0.5"                                  스크립트 "1.3"   "1.3"         true
t1  type="time" step="900" value="13:07"                      속성만           "13:07"       false
t2  type="time" step="900"                                    스크립트 "13:07" "13:07"       true
t3  type="time" step="900" min="13:00" value="13:07"          속성만           "13:07"       true
d1  type="date" step="7" min="2026-09-07" value="2026-09-10"  속성만           "2026-09-10"  true
d2  type="date" step="7" value="2026-09-10"                   속성만           "2026-09-10"  false
r1  type="range" min="1" step="2" value="4"                   속성만           "5"           false
r2  type="range" min="1" step="2"                             스크립트 "4"     "5"           false
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`min=1 step=2` 에 `4` 는 `stepMismatch`, `5` 는 통과** — `n1`·`n2`. 명세의 step base — 「**`min` 속성**이 있고 수로 바뀌면 그 값」. 허용 눈금은 **1, 3, 5, …** 이다(0, 2, 4 가 아니다). 명세 — 「값에서 step base 를 뺀 것이 허용 눈금의 **정수배가 아니면** step mismatch」.
- ★★★ **값이 들어온 경로는 결과를 바꾸지 않았다** — 같은 `min=1 step=2` 에 `4` 를 **스크립트로(`n1`)·속성으로(`n3`)·진짜 키로(`n8`)** 넣었더니 **셋 다 `true`** 다.
- ★★★ **`min` 이 없으면 `value` 속성이 눈금의 출발점이다** — `step=2 value="3"`(`n4`)은 `false`, 거기에 스크립트로 `4`(`n5`)는 **`true`**, `5`(`n6`)는 `false`. 명세의 step base 둘째 줄 — 「`min` 이 없고 **`value` 속성**이 있고 수로 바뀌면 **그 값**」. 눈금이 3·5·7 로 선다. **`value` 속성도 `min` 도 없으면**(`n7`) 기본 기준 0 — `3` 은 `true`.
- ★★★ **[23번](../23-input-types-number-date/2-summary.md)의 (4) 가 「Chrome 이 속성으로 준 값에는 `stepMismatch` 를 안 켠다 — 명세와 갈림」으로 적은 칸은 이 규칙으로 설명된다.** 23편의 `a2`(`step=0.5 value="1.3"`)는 **`value` 속성 자신이 눈금의 출발점**이라 `1.3` 이 눈금 위에 있다(`false`) · `a2s`(속성 없이 스크립트 `1.3`)는 출발점이 0 이라 `true`. 여기서 **같은 두 줄을 그대로 다시 쟀다**(`a2`·`a2s`). `time` 도 같다 — `t1`(`value="13:07"` 이 출발점) `false` · `t2`(스크립트, 출발점 0) `true` · **`min="13:00"` 을 주면**(`t3`) 속성 값인데도 `true`. `date` 도 같다 — 23편의 `a5` 는 **`min` 이 있어서** 켜진 것이고, **`min` 없이 `value` 속성만**(`d2`) 주면 `false` 다. **갈린 것은 들어온 경로가 아니라 step base 였다** — 이 판에서 명세와 어긋난 칸은 없다.
- ★★ **`range` 는 눈금에 맞게 고친다** — `min=1 step=2` 에 `4` 는 속성(`r1`)·스크립트(`r2`) 둘 다 **`5`** 가 됐다. 명세의 Range 상태 — 「step mismatch 를 겪으면 가장 가까운 허용 값으로 **반올림해야 한다(must)** · 둘이면 **양의 무한대 쪽**」(3 과 5 가 똑같이 가깝다 → 5). **`number` 는 반올림이 「해도 된다(may)」** 이고 이 판은 **안 했다**(`n1` 의 `.value` 는 `"4"` 그대로).

```text
  step base — 눈금의 출발점을 고르는 순서 (명세 「The step base」)

  min 속성이 있고 수로 읽히나 ──> 그것            n1 n2 n3 n8 (1) · t3 (13:00) · d1 (2026-09-07)
     └ 아니면 value 속성이 있고 수로 읽히나 ──> 그것   n4 n5 n6 (3) · a2 (1.3) · t1 (13:07) · d2 (2026-09-10)
        └ 아니면 타입의 기본 기준 ──> 그것 (week 만 따로 있다)
           └ 아니면 0                                n7 · a2s · t2

  min=1 step=2 의 눈금       1   3   5   7 …     ← 4 는 눈금 사이 = stepMismatch
  value="3" step=2 의 눈금   …   3   5   7 …     ← 속성 값 자신이 눈금 위 = 통과
```

### (3) 창 ② + 콘솔 — `pattern` 은 `^(?:…)$` 로 감싸고 `v` 플래그로 컴파일한다

**언제 쓰나** — `pattern` 에 **`|`(또는)** 을 쓸 때 · 문자 클래스에 **`-`** 를 그대로 넣을 때 · 대소문자를 안 가리려 할 때.

```html
<!-- html25b-28-pattern.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 pattern 의 감싸기</title>
</head>
<body>
<input id="p1" pattern="a|bc">
<input id="p2" pattern="a|bc">
<input id="p3" pattern="a|bc">
<input id="p4" pattern="[a-z-]+">
<input id="p5" pattern="[a-z\-]+">
<input id="p6" pattern="[\p{L}--[a-z]]+">
<input id="p7" pattern="[\p{L}--[a-z]]+">
<input id="p8" pattern="\p{L}+">
<input id="p9" pattern="abc">
<input id="p10" pattern="x+">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 값 = { p1: "a", p2: "bc", p3: "abc", p4: "1", p5: "1", p6: "ABC가", p7: "abc", p8: "가나", p9: "ABC", p10: "" };
for (const [id, v] of Object.entries(값)) document.getElementById(id).value = v;
const 던짐 = f => { try { return String(f()); } catch (e) { return e.constructor.name + " 「" + e.message + "」"; } };
window.__콘솔 = true;
window.__끝 = () => {
  const O = [칸("id", 5) + 칸("pattern", 20) + 칸(".value", 10) + "patternMismatch"];
  for (const i of document.querySelectorAll("input")) {
    O.push(칸(i.id, 5) + 칸(i.getAttribute("pattern"), 20) + 칸(JSON.stringify(i.value), 10) + i.validity.patternMismatch);
  }
  O.push("");
  O.push("같은 글자를 JS 로 — 감싸지 않으면");
  O.push("  /a|bc/v.test(\"abc\")        = " + 던짐(() => /a|bc/v.test("abc")));
  O.push("  /^a|bc$/v.test(\"abc\")      = " + 던짐(() => /^a|bc$/v.test("abc")));
  O.push("  /^(?:a|bc)$/v.test(\"abc\")  = " + 던짐(() => /^(?:a|bc)$/v.test("abc")));
  O.push("");
  O.push("[a-z-] 를 플래그별로 컴파일하면");
  for (const f of ["", "u", "v"]) O.push("  new RegExp(\"[a-z-]\", " + JSON.stringify(f) + ")  → " + 던짐(() => new RegExp("[a-z-]", f)));
  O.push("");
  O.push("콘솔 기록(Log.entryAdded) " + __LOG.length + "줄");
  for (const s of __LOG) O.push("  " + s);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html25b-form.py page html25b-28-pattern.html
id   pattern             .value    patternMismatch
p1   a|bc                "a"       false
p2   a|bc                "bc"      false
p3   a|bc                "abc"     true
p4   [a-z-]+             "1"       false
p5   [a-z\-]+            "1"       true
p6   [\p{L}--[a-z]]+     "ABC가"   false
p7   [\p{L}--[a-z]]+     "abc"     true
p8   \p{L}+              "가나"    false
p9   abc                 "ABC"     true
p10  x+                  ""        false

같은 글자를 JS 로 — 감싸지 않으면
  /a|bc/v.test("abc")        = true
  /^a|bc$/v.test("abc")      = true
  /^(?:a|bc)$/v.test("abc")  = false

[a-z-] 를 플래그별로 컴파일하면
  new RegExp("[a-z-]", "")  → /[a-z-]/
  new RegExp("[a-z-]", "u")  → /[a-z-]/u
  new RegExp("[a-z-]", "v")  → SyntaxError 「Invalid regular expression: /[a-z-]/v: Invalid character class」

콘솔 기록(Log.entryAdded) 1줄
  Pattern attribute value [a-z-]+ is not a valid regular expression: Uncaught SyntaxError: Invalid regular expression: /[a-z-]+/v: Invalid character class
(exit 0)
```

- ★★★ **`pattern="a|bc"` 는 `a`·`bc` 만 받고 `abc` 를 거절한다** — `p1`·`p2` `false` · `p3` `true`. 명세 — 「`^(?:` + 패턴 + `)$` 를 **`v` 플래그로** 만든다」. JS 로 같은 글자를 감싸지 않으면(`/a|bc/v`) `abc` 가 **통과**하고, **`^`·`$` 만 붙이면**(`/^a|bc$/v`) **또 통과**한다 — `^a` 또는 `bc$` 로 읽히기 때문이다. **`(?:…)` 까지 있어야** 명세의 결과(`false`)와 같다. 명세가 그 이유를 적는다 — 「패턴이 **감싼 뒤에야 유효해지는** 것이 아니라 **혼자서도 유효**하도록」.
- ★★★ **`v` 에서 무효한 패턴은 조용히 버려진다** — `[a-z-]+`(`p4`)는 `u` 로는 유효하지만 **`v` 로는 `SyntaxError`**(「Invalid character class」 — 문자 클래스 안의 맨 `-`)다. 그래서 컴파일된 패턴이 **없고**, 값 `1` 이 **`false`**(검사 안 함)다. `[a-z\-]+`(`p5`)로 이스케이프하면 `true`. 명세 — 「`RegExpCreate(pattern, "v")` 가 **실패하면** 컴파일된 패턴이 **없다**」 · 「UA 는 이 오류를 **개발자 콘솔에 남기기를 권한다**」. ★ 이 판은 **콘솔에 한 줄**을 남겼다(`Pattern attribute value [a-z-]+ is not a valid regular expression …`) — 화면·`validity`·예외로는 **아무것도 안 보인다.**
- ★★ **`v` 전용 문법이 먹는다** — `[\p{L}--[a-z]]+`(글자에서 소문자 로마자를 **뺀 집합**)가 `ABC가` 를 받고 `abc` 를 거절했다(`p6`·`p7`). 집합 빼기 `--` 는 **`v` 에만 있다**([JS 30번](../../../js/syntax/30-regexp-advanced/2-summary.md)의 (4) — 그 편의 「어디서 틀리나」 (8) 「`u` 패턴에 `v` 를 그냥 바꿔 단다」가 이 자리의 JS 쪽이다). `\p{L}+`(`p8`)도 된다.
- ★ **대소문자를 가린다** — `pattern="abc"` 에 `ABC`(`p9`)는 `true`. 플래그를 더할 방법이 없다 — 명세가 플래그를 **`"v"` 하나로 고정**했다. 대소문자를 안 가리려면 패턴에 둘 다 쓴다(`[aA]…`).
- ★ **빈 값은 안 본다** — `p10`(`""`)은 `false`. 명세 — 「값이 **빈 문자열이 아니고** …」. 비우지 못하게 하려면 `required` 를 **같이** 단다.

```text
  pattern="a|bc" 가 값 "abc" 를 만나기까지

  속성 글자  a|bc
     │ ① RegExpCreate("a|bc", "v")        ← 혼자서 유효한가 (실패하면 패턴 없음 = 검사 안 함 + 콘솔 한 줄)
     │ ② RegExpCreate("^(?:a|bc)$", "v")  ← 통째로 감싼다
     ▼
  "a" ●   "bc" ●   "abc" ✕ patternMismatch

  감싸지 않으면      /a|bc/v      "abc" ● (부분 일치)
  ^ $ 만 붙이면      /^a|bc$/v    "abc" ● (^a 또는 bc$)
  명세의 감싸기      /^(?:a|bc)$/v "abc" ✕
```

### (4) 창 ② — `maxlength` 는 「사용자가 마지막으로 고쳤을 때」만 센다

**언제 쓰나** — 서버에서 불러온 긴 값을 `maxlength` 칸에 채웠는데 **폼이 그냥 제출될 때** · 입력 제한과 검증을 **같은 것**으로 여길 때.

```html
<!-- html25b-28-length.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>28 길이 제한과 편집</title>
</head>
<body>
<input id="m1" maxlength="3">
<input id="m2" maxlength="3">
<input id="m3" minlength="5">
<input id="m4" minlength="5">
<input id="m5" maxlength="3">
<textarea id="m6" maxlength="3">abcdef</textarea>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const $ = id => document.getElementById(id);
$("m1").value = "abcdef";
$("m4").value = "ab";
$("m5").value = "abcdef";
const 설명 = {
  m1: "스크립트 \"abcdef\" → (둘째 시도) End + Backspace",
  m2: "(둘째 시도) 진짜로 \"abcdef\" 를 친다",
  m3: "(둘째 시도) 진짜로 \"ab\" 를 친다",
  m4: "스크립트 \"ab\"",
  m5: "스크립트 \"abcdef\" → (둘째 시도) End + Backspace → 스크립트 \"abcdef\"",
  m6: "자식 텍스트 \"abcdef\"",
};
window.__표 = "종합";
window.__뒤숨김 = true;
const 뒤 = "JSON.stringify(Object.fromEntries(['m1','m2','m3','m4','m5','m6'].map(id => { const e = document.getElementById(id); return [id, [e.value, e.validity.tooLong, e.validity.tooShort]]; })))";
window.__시도 = [
  { 이름: "편집 없음", 단계: [], 뒤 },
  { 이름: "진짜 키로 편집", 단계: [
    ["key", "#m1", "End", "End", 35], ["keyhere", "Backspace", "Backspace", 8],
    ["type", "#m2", "abcdef"], ["type", "#m3", "ab"],
    ["key", "#m5", "End", "End", 35], ["keyhere", "Backspace", "Backspace", 8], ["js", "document.getElementById('m5').value = 'abcdef'; 1"],
  ], 뒤 },
];
window.__종합 = 결과 => {
  const O = [];
  for (const r of 결과) {
    const S = JSON.parse(r.뒤);
    O.push("── " + r.이름);
    O.push(칸("id", 4) + 칸("속성", 14) + 칸(".value", 10) + 칸("tooLong", 9) + 칸("tooShort", 9) + "무엇을 했나");
    for (const id of Object.keys(S)) {
      const e = $(id), a = e.hasAttribute("maxlength") ? "maxlength=3" : "minlength=5";
      O.push(칸(id, 4) + 칸(a, 14) + 칸(JSON.stringify(S[id][0]), 10) + 칸(String(S[id][1]), 9) + 칸(String(S[id][2]), 9) + 설명[id]);
    }
    O.push("");
  }
  return O.join("\n").trimEnd();
};
</script>
</body>
</html>
```

```text
$ python3 html25b-form.py 시도 html25b-28-length.html | sed -n '/^── /,$p'
── 편집 없음
id  속성          .value    tooLong  tooShort 무엇을 했나
m1  maxlength=3   "abcdef"  false    false    스크립트 "abcdef" → (둘째 시도) End + Backspace
m2  maxlength=3   ""        false    false    (둘째 시도) 진짜로 "abcdef" 를 친다
m3  minlength=5   ""        false    false    (둘째 시도) 진짜로 "ab" 를 친다
m4  minlength=5   "ab"      false    false    스크립트 "ab"
m5  maxlength=3   "abcdef"  false    false    스크립트 "abcdef" → (둘째 시도) End + Backspace → 스크립트 "abcdef"
m6  maxlength=3   "abcdef"  false    false    자식 텍스트 "abcdef"

── 진짜 키로 편집
id  속성          .value    tooLong  tooShort 무엇을 했나
m1  maxlength=3   "abcde"   true     false    스크립트 "abcdef" → (둘째 시도) End + Backspace
m2  maxlength=3   "abc"     false    false    (둘째 시도) 진짜로 "abcdef" 를 친다
m3  minlength=5   "ab"      false    true     (둘째 시도) 진짜로 "ab" 를 친다
m4  minlength=5   "ab"      false    false    스크립트 "ab"
m5  maxlength=3   "abcdef"  false    false    스크립트 "abcdef" → (둘째 시도) End + Backspace → 스크립트 "abcdef"
m6  maxlength=3   "abcdef"  false    false    자식 텍스트 "abcdef"
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **스크립트로 넣은 `abcdef` 는 `maxlength=3` 을 넘어도 `tooLong` 이 `false`** — `m1` 첫 판. 값도 **잘리지 않았다**(`"abcdef"`). 명세 — 「`maxlength` 가 있고, **더러움 표시가 참**이고, **값이 마지막으로 사용자 편집으로 바뀌었고**(스크립트의 변경이 아니라), API 값의 길이가 최대보다 크면 too long」.
- ★★★ **진짜 키로 한 글자 지우면 켜진다** — `m1` 둘째 판은 `"abcde"`(여전히 5 > 3)에 **`tooLong = true`**. 사용자 편집 조건이 채워졌다.
- ★★ **사용자가 치는 글자는 `maxlength` 에서 막힌다** — `m2` 에 `abcdef` 를 치니 **`"abc"`** 만 들어갔고 `tooLong` 은 `false`. 명세 — 「UA 는 사용자가 값을 최대보다 길게 만들지 **못하게 해도 된다(may)**」. **입력 제한(막기)과 검증(깃발)은 다른 문장**이다.
- ★★ **마지막 변경이 스크립트면 다시 꺼진다** — `m5` 는 편집으로 켠 뒤 스크립트가 `abcdef` 를 다시 넣었더니 **`false`**.
- ★ **`minlength` 도 같다** — 진짜로 친 `ab`(`m3`)는 `tooShort = true`, 스크립트로 넣은 `ab`(`m4`)는 `false`. `textarea` 의 자식 텍스트(`m6`)도 편집 전이라 `false`([26번](../26-select-datalist-textarea/2-summary.md) — 더러움 표시가 거짓).

```text
  maxlength=3 인 칸의 값 "abcdef" — 어떻게 들어왔나가 깃발을 가른다

  스크립트 .value = "abcdef"      ──> tooLong false    (마지막 변경 = 스크립트)
     └ 진짜 Backspace → "abcde"    ──> tooLong true     (마지막 변경 = 사용자 편집)
         └ 스크립트 .value = …     ──> tooLong false    (다시 스크립트)
  진짜로 "abcdef" 를 친다         ──> "abc" 에서 막힘  (입력 제한 — 깃발이 켜질 일이 없다)

  ★ 서버에서 불러온 긴 값은 사용자가 손대기 전까지 검증을 통과한다
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 깃발 |
|---|---|---|
| 비우지 못하게 | `required` | `valueMissing` — `range` 제외 |
| 모양 강제 | `pattern="[0-9]{3}-[0-9]{4}"` | `patternMismatch` — **글자 칸만** · 빈 값은 안 본다 |
| 범위 | `min="1" max="10"` | `rangeUnderflow`·`rangeOverflow` — **수·날짜 칸만** |
| 눈금 | `step="2"` (+ `min` 이 출발점) | `stepMismatch` — `step="any"` 면 눈금 없음 |
| 글자 수 | `minlength="2" maxlength="10"` | `tooShort`·`tooLong` — **글자 칸만 · 사용자 편집 뒤** |

### 어디서 헷갈리나

- **`pattern` 은 통째로 일치해야 한다** — `^`·`$` 를 쓸 필요가 없다(써도 된다).
- **`pattern` 의 `|` 는 전체를 가른다** — 감싸기가 있어서 괜찮다.
- **`pattern` 의 문자 클래스 안 `-` 는 이스케이프한다** — `v` 규칙이다.
- **`step` 의 눈금은 0 이 아니라 `min` 에서 시작한다.**
- **`maxlength` 는 스크립트 값을 막지도 검사하지도 않는다.**

## 어디서 틀리나

### 1. `type="number"` 에 `pattern="\d{4}"` 로 네 자리를 강제한다

**무시된다**((1) — `pattern` × `number` 「·」). 네 자리 **글자**가 필요하면 `type="text"` + `inputmode="numeric"` + `pattern`([23번](../23-input-types-number-date/2-summary.md)의 「`number` 에 전화번호」).

### 2. `min=1 step=2` 에서 짝수가 된다고 여긴다

**홀수만 된다**((2) — `4` 는 `stepMismatch`). 짝수 눈금이 필요하면 `min` 을 짝수로 둔다.

### 3. 값을 `value` 속성으로 줬더니 `stepMismatch` 가 안 켜져서 「속성 값은 검증 안 한다」고 결론 낸다

**`value` 속성이 눈금의 출발점이 된 것**이다((2) — `n4` 대 `n3`). `min` 을 주면 속성 값도 검사된다. ★ [23번](../23-input-types-number-date/2-summary.md)의 해석이 이 함정에 빠졌다.

### 4. `pattern="[a-z-]+"` 가 소문자와 하이픈만 받을 거라 여긴다

**아무것도 검사하지 않는다**((3) — `p4` 가 `1` 을 통과시켰다). `v` 에서 무효한 패턴은 **버려지고 콘솔 한 줄**만 남는다. `[a-z\-]+` 로 쓴다.

### 5. `maxlength` 가 있으니 긴 값은 제출이 안 된다고 여긴다

**스크립트·서버가 채운 값은 통과한다**((4) — `m1`·`m5`). 그리고 [21번](../21-form-submission-model/2-summary.md)의 (5) — **`curl` 로 보낸 본문은 어떤 속성도 안 거친다.** 서버가 다시 잰다.

### 6. 클라이언트 검증 속성을 다 달았으니 서버 검증은 생략한다

**서버는 그 검증을 모른다** — [21번](../21-form-submission-model/2-summary.md)의 (5) 가 잰 대로 **`novalidate` 폼·`curl` 이 보낸 본문과 검증 폼이 보냈을 본문이 한 글자도 같다.** 거기에 이 주제의 결과가 더해진다 — **타입과 안 맞는 속성은 조용히 무시되고**((1)), **무효한 `pattern` 은 버려지고**((3)), **`maxlength` 는 스크립트 값을 안 센다**((4)). 브라우저 쪽 검증은 **사용자 편의**다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 상태마다 「지정하지 말아야 하고 **적용되지 않는** 속성」 목록 — 적용 안 되면 깃발이 없다 | (1) |
| **명세(HTML)** | step base = `min` → `value` 속성 → 타입 기본값 → 0 · 값 − base 가 눈금의 정수배가 아니면 step mismatch — **값이 들어온 경로를 묻지 않는다** | (2) |
| **명세(HTML)** | Range 는 눈금·범위 밖 값을 **반올림해야 한다(must)** · 둘이면 양의 무한대 쪽 · Number·날짜류는 **해도 된다(may)** | (2) |
| **명세(HTML)** | 컴파일된 패턴 = `RegExpCreate(p, "v")` 가 성공할 때만 `^(?:p)$` 를 `v` 로 · 실패하면 **패턴 없음**(콘솔 기록 권장) · 빈 값은 안 본다 | (3) |
| **명세(HTML)** | `tooLong`·`tooShort` = 더러움 표시 참 **+ 마지막 변경이 사용자 편집** · 사용자의 초과 입력은 **막아도 된다(may)** | (4) |
| **구현(Chrome)** | Number 의 반올림(may)을 **안 한다** · 사용자의 초과 입력을 **막는다** · 무효한 `pattern` 을 **콘솔에 남긴다** | (2)\~(4) |
| **이 판의 관찰** | **명세의 적용 목록과 갈린 칸 0 / 42** · step base 규칙이 **네 타입 모두** 명세대로 | (1)·(2) |
| ★ **앞 편의 정정** | [23번](../23-input-types-number-date/2-summary.md)의 「구현(Chrome) — 명세와 갈림: 속성으로 넣은 값에 `stepMismatch` 를 안 켠다」는 **step base 가 `value` 속성이 된 결과**다 — 갈림이 아니다 | (2) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **검증 실패 때 사용자가 보는 풍선 말** | 헤드리스에는 그 UI 가 없다 — 이 문서는 **깃발**까지만 쟀다(문구는 구현) |
| **스크린리더가 무효 상태를 알리나** | 보조 기술이 없다 · `aria-invalid` 와의 관계도 재지 않았다 |
| **모바일 입력기가 `pattern`·`maxlength` 를 보고 자판을 바꾸나** | 입력기가 없다 — [22번](../22-input-types-text/2-summary.md)과 같은 제3의 상태 |
| **IME 조합 중의 `maxlength`**(한글을 치다가 끊기는 자리) | 이 판은 `Input.insertText` 로 조합 없이 넣었다 — **안 돌려 본 것** |

## 언제 쓰고 언제 안 쓰나

- **속성은 타입에 맞춰 단다** — 글자 칸에는 `pattern`·`minlength`·`maxlength`, 수·날짜 칸에는 `min`·`max`·`step`. 반대로 달면 **아무 일도 없다.**
- **`step` 을 쓰면 `min` 을 함께 적는다** — 출발점을 명시해야 눈금이 읽힌다.
- **`pattern` 은 `v` 문법으로 쓰고 한 번 콘솔을 본다** — 버려진 패턴은 거기만 흔적이 있다.
- **`maxlength` 는 「입력을 막는 도구」로만 믿는다** — 서버·스크립트가 넣는 값의 길이는 **서버가 잰다.**
- **서버 검증은 언제나 따로** — 이 주제의 속성은 전부 **브라우저 안의 편의**다([21번](../21-form-submission-model/2-summary.md)의 (5)).

## 핵심 문장

1. **검증 속성은 타입마다 적용이 정해져 있다 — 안 맞는 타입에서는 에러도 경고도 없이 무시된다(이 판: 무시 22 / 42, 명세와 갈림 0).**
2. **`pattern` 은 글자 칸에만, `min`/`max`/`step` 은 수·날짜 칸에만, `checkbox` 는 `required` 만 먹는다.**
3. **`range` 는 깃발 대신 값을 고친다.**
4. **`step` 의 눈금은 `min` 에서 출발한다 — `min=1 step=2` 면 1·3·5 — `min` 이 없으면 `value` 속성이 출발점이다.**
5. **값이 속성·스크립트·키 입력 중 어디로 들어왔는지는 `stepMismatch` 를 바꾸지 않는다.**
6. **`pattern` 은 `^(?:…)$` 로 감싸 `v` 플래그로 컴파일된다 — `v` 에서 무효한 패턴은 조용히 버려진다.**
7. **`maxlength`·`minlength` 는 값이 마지막으로 사용자 편집으로 바뀌었을 때만 깃발을 켠다 — 스크립트로 넣은 긴 값은 통과한다.**

## 관련 자료

- [21번 주제](../21-form-submission-model/2-summary.md) — ★ **검증이 언제 도나**((2) — `form.submit()` 은 건너뛰고 `requestSubmit()` 은 `invalid` 로 멈춘다)와 **`curl` 우회**((5))의 정본.
- [22번 주제](../22-input-types-text/2-summary.md) — `typeMismatch` · **`validationMessage` 는 문구가 구현**.
- [23번 주제](../23-input-types-number-date/2-summary.md) — `range` 가 값을 고치는 것 · `stepMismatch` 가 처음 보인 자리(★ 그 편의 「명세와 갈림」 해석은 이 편 (2) 가 정정한다).
- [JS 30번 — 정규식 심화](../../../js/syntax/30-regexp-advanced/2-summary.md) — `u` 와 `v` 의 차이 · `v` 가 거절하는 글자의 정본. 여기는 그것이 **`pattern` 에서 어떻게 번지나**.
- [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) — `:invalid`·`:user-invalid` 가 이 깃발을 읽는 시점.
- 목록의 **29번 주제**(유효성 상태 · `novalidate` · CSS 와의 관계) · web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **60번**(`setCustomValidity`·`reportValidity`).

## 용어 풀이

- **`validity` 깃발** — `ValidityState` 의 불리언. 속성마다 하나씩 대응한다.
- **적용되지 않는다(do not apply)** — 명세가 상태마다 적어 둔 「이 타입에서는 의미 없는 속성」 목록.
- **step base** — 눈금의 출발점. `min` → `value` 속성 → 타입 기본값 → 0.
- **허용 눈금(allowed value step)** — `step` 을 수로 읽은 것(× 타입의 배율). `any` 면 없음.
- **컴파일된 패턴(compiled pattern regular expression)** — `pattern` 을 `^(?:…)$` 로 감싸 `v` 로 만든 정규식. 못 만들면 없음.
- **`v` 플래그(unicodeSets)** — ES2024 정규식 플래그. 집합 연산(`--`·`&&`)이 되고, 문자 클래스 안의 맨 `-`·`(` 등을 거절한다.
- **사용자 편집(user edit)** — 사용자가 직접 값을 바꾼 것. 스크립트의 `.value =` 는 아니다.
- **더러움 표시(dirty value flag)** — 값이 기본값에서 바뀌었다는 표시. `tooLong`·`tooShort` 의 조건 중 하나.

## 더 들어가면

- **왜 `maxlength` 는 사용자 편집만 보나** — 명세의 비규범 설명은 없다. 결과로 보면 **서버가 채운 옛 값**(규칙이 바뀌기 전에 저장된 긴 값)을 가진 폼이 **사용자가 손도 안 댔는데 제출이 막히는** 일을 피한다(해석이다).
- **왜 `pattern` 을 `v` 로 바꿨나** — `v` 는 `u` 보다 엄격한 문법이라 **옛 패턴 일부가 무효가 된다**((3) 의 `[a-z-]`). 명세는 그 대가를 알고도 집합 연산·글자열 속성을 얻는 쪽을 택한 것으로 보인다 — 변경의 경위는 이 문서가 확인하지 않았다.
- **`step="any"`** — 허용 눈금이 **없다**. `number` 에서 소수를 자유롭게 받으려면 이것을 준다(이 판은 던지지 않았다).
