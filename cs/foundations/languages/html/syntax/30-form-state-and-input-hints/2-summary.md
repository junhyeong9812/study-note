# html/syntax/30 — 폼 상태·입력 보조 속성: `disabled`/`readonly`/`autofocus`/`autocomplete`/`inputmode` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Enabling and disabling form controls」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#enabling-and-disabling-form-controls:-the-disabled-attribute)(★ **비활성이면 제약 검증에서 빠진다**), [「The readonly attribute」](https://html.spec.whatwg.org/multipage/input.html#the-readonly-attribute)(★ **「텍스트 컨트롤만 읽기 전용이 될 수 있다」** · 지정되면 제약 검증에서 빠진다), 상태마다의 **「지정하지 말아야 하고 적용되지 않는」 목록**(Checkbox·Range 등에 `readonly` 가 있다), [`required`](https://html.spec.whatwg.org/multipage/input.html#the-required-attribute)(★ **「요소가 mutable 이고」**), [「Constructing the entry list」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-the-form-data-set)(비활성은 건너뛴다), [「The autofocus attribute」](https://html.spec.whatwg.org/multipage/interaction.html#the-autofocus-attribute)(★ **autofocus 후보 목록** · **조각 대상이 있으면 비운다** · `dialog` 가 보일 때), [「Autofill processing model」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill-processing-model)(★ **IDL-exposed autofill value**), [「Input modalities: the inputmode attribute」](https://html.spec.whatwg.org/multipage/interaction.html#input-modalities:-the-inputmode-attribute)(★ **「가상 키보드를 … 보여야 한다(should)」** · IDL 은 알려진 값으로만). **명세 본문은 앞 배치가 2026-09-26 에 받아 둔 사본**으로 읽었다 — 이 배치는 네트워크를 쓰지 않았다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 포커스는 **CDP 의 진짜 Tab 키**, 편집은 **진짜 키**(`Input.dispatchKeyEvent`·`Input.insertText`)다. 하네스는 [29번 주제](../29-constraint-validation/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. ★ `inputmode` 는 명세의 브라우저 지원 표가 **Chrome 66+** 로 적는다(이 배치는 따로 조회하지 않았다).
> **선행** — [24번 주제](../24-input-types-choice-special/2-summary.md)(★ `disabled` 칸은 **안 실리고** `readonly` 칸은 **실린다** — (1) 격자의 `text` 줄) · [27번 주제](../27-fieldset-and-legend/2-summary.md)(★ **비활성 묶음 안의 `required` 빈 칸이 제출을 막지 않았다** — `fieldset[disabled]` 는 거기서 쟀다).
> **경계** — **포커스 순서·`tabindex`·`inert`** 는 목록의 **45번 주제**, **`dialog` 를 여는 동작과 포커스 트랩**은 목록의 **47번 주제**다 — 여기는 **`autofocus` 가 어느 칸을 고르나**까지. **`:disabled`·`:read-only` 로 칠하는 것**은 [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md). **제약 검증 상태 자체**는 [29번](../29-constraint-validation/2-summary.md).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤ + 창 ② + 진짜 Tab 의 「세 지점 격자」다** — 제출(서버가 받은 필드) · 포커스(Tab 이 닿은 곳) · 검증(`willValidate`). `autocomplete`·`inputmode` 는 **창 ② 의 IDL 값과 창 ⑦ 의 침묵**으로 묻는다.

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
| **안 흔들린다** | 서버가 받은 필드 · Tab 이 닿은 순서 · `willValidate` · IDL 값 · 접근성 노드의 속성 이름 · 「갈린 칸 N / M」 | 시도마다 페이지를 새로 연다 · 같은 판이면 결정적이다 |
| **안 흔들린다** | `document.hasFocus()` = `true` | headless 창이 포커스를 가진 판이다 — ★ `autofocus` 의 결과는 **이 줄이 참일 때만** 뜻이 있다((3)) |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 그 칸이 **제출에 실리나**((1)·(2)) |
| **② 노드 프로브**(`willValidate` · `activeElement` · IDL) | ★ **쓴다 — 본체** | **검증에 참가하나** · **포커스가 어디 있나** · `autocomplete`/`inputMode` 가 **무엇으로 읽히나**((1)\~(4)) |
| **진짜 키 입력**(Tab · Space · 화살표 · 글자) | ★ **쓴다** | **순차 포커스를 받나**((1)) · **사용자가 값을 바꿀 수 있나**((2)) |
| **⑦ 접근성 트리** | 쓴다 | `autocomplete`·`inputmode` 가 **트리에 무엇을 남기나**((4) — 18-A) |
| **① · ③ · ④ · ⑥** | **부적용** | 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「사용자가 못 고친다」를 값으로 물었다.** `readonly` 가 먹었는지는 깃발이 없다. 그래서 칸마다 **속성만 없는 짝**을 두고 **같은 진짜 키**를 준 뒤 **짝은 바뀌고 자기는 안 바뀐** 곳을 센다((2) — [28번](../28-validation-attributes/2-summary.md)의 쌍둥이와 같은 방식).
- ★★ **18-A — 몇 군데 물었나.** (1) 은 **속성 셋 × 대상 다섯 × 지점 셋 = 45 곳** · (4) 는 **24 칸 × 접근성 노드**를 물었다. 「트리에 흔적이 없다」가 (4) 의 결론이라 **물은 칸 수와 나온 속성 이름 전부**를 찍는다.

## 한눈에 — 쉽게 말하면

**★ `disabled` 는 「창구 폐쇄」, `readonly` 는 「열람만 가능」이다. 폐쇄된 창구는 서류를 받지도, 손님을 부르지도, 검사하지도 않는다. 열람 창구는 서류를 받고 손님도 부르지만 검사는 건너뛴다 — 그리고 「열람만」 팻말은 글자 칸에만 붙는다.**

관공서 창구 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **창구 폐쇄** | **`disabled`** — 제출에 **안 실림** · Tab 이 **건너뜀** · `willValidate` **거짓** |
| **열람만 가능** | **`readonly`** — 제출에 **실림** · Tab 이 **닿음** · `willValidate` **거짓** |
| **「열람만」 팻말이 안 붙는 창구** | `checkbox`·`radio`·`range`·`select` — 손님이 **그대로 고친다**((2)) |
| **번호표 자동 발급** | **`autofocus`** — 문서에서 **첫 후보** 하나 · 주소에 **조각이 있으면 발급 안 함** |
| **서류 양식의 칸 이름표** | **`autocomplete`** 토큰 — 규칙에 맞으면 **IDL 에 그대로**, 틀리면 **빈 문자열** |
| **「숫자 자판을 준비하세요」 메모** | **`inputmode`** — 자판을 띄우는 것은 **기기**다(이 판은 못 본다) |

- **「없음」과 갈린 칸 18 / 30** — `disabled` 가 **15 칸 전부**, `readonly` 가 **3 칸**(`text`·`checkbox`·`textarea` 의 검증)((1)).
- ★★★ **`readonly` 가 사용자 편집을 막은 칸은 4 / 8** — `range`·`checkbox`·`radio`·`select` 는 **그대로 바뀌었다**((2)).
- ★★★ **그런데 `readonly` 인 `checkbox`·`radio`·`range` 도 `willValidate` 가 거짓이다** — 편집은 못 막으면서 **검증에서는 빠졌다.** `readonly required` 인 체크박스는 **안 켠 채로 제출됐다**((2)).
- ★★ **주소에 `#조각` 이 붙으면 `autofocus` 가 아무 칸도 안 골랐다**((3)).

```text
  세 지점 — 한 칸이 폼에서 겪는 일 (이 판 · text 칸)

                      제출(서버)   Tab 포커스   검증(willValidate)
  (속성 없음)           실림          닿음          참
  disabled              ✕            ✕             ✕        ← 세 지점 전부 끊긴다
  readonly              실림          닿음          ✕        ← 검증만 끊긴다
                                                              (그래서 readonly required 빈 칸은 그냥 보내진다)
```

> **`willValidate`** — 「이 칸이 제출 때 검증되나」를 돌려주는 불리언. 명세의 **제약 검증 후보**(candidate for constraint validation)인가와 같다.\
> 예: `disabled` 인 칸은 `false` — 값이 아무리 틀려도 제출을 막지 않는다.

## 이 주제가 답하려는 질문

1. **`disabled` 와 `readonly` 는 제출·포커스·검증의 어디서 갈리나** — 대상 요소마다 같은가.
2. **`readonly` 는 어느 타입에서 무엇을 막나** — 막지 못하는 타입에서 검증은 어떻게 되나.
3. **`autofocus`·`autocomplete`·`inputmode` 는 무엇을 남기나** — 페이지 안에서 잴 수 있는 것과 없는 것.

## 동작 방식

### (1) 창 ⑤ + 창 ② + 진짜 Tab — 속성 셋 × 대상 다섯 × 지점 셋

**언제 쓰나** — 「수정 못 하게 막은 칸이 서버에 안 온다」·「읽기 전용 칸에 Tab 이 멈춘다」·「비워 둔 필수 칸인데 제출이 된다」를 가를 때.

폼 셋(속성 없음 · `disabled` · `readonly`)에 같은 다섯 대상을 두었다. **제출**은 그 폼의 `button` 을 제출자로 준 `requestSubmit(단추)` 이다(단추 자신도 대상이므로). **포커스**는 앞의 `시작` 단추에서 **진짜 Tab 을 열여덟 번** 눌러 닿은 곳을 모았다. 「명세 열」은 **따로 둔 파일**이다.

```html
<!-- html29b-30-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 세 지점</title>
<script src="html29b-rec.js"></script>
<script src="html29b-30-spec.js"></script>
</head>
<body>
<button type="button" id="시작">시작</button>
<div id="자리"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 속성 = ["없음", "disabled", "readonly"];
const 대상 = ["text", "checkbox", "select", "textarea", "button"];
const 만들기 = t => {
  if (t === "text") { const e = document.createElement("input"); e.value = "가"; return e; }
  if (t === "checkbox") { const e = document.createElement("input"); e.type = "checkbox"; e.checked = true; return e; }
  if (t === "select") { const e = document.createElement("select"); e.append(new Option("가", "가", true, true), new Option("나", "나")); return e; }
  if (t === "textarea") { const e = document.createElement("textarea"); e.textContent = "가"; return e; }
  const e = document.createElement("button"); e.type = "submit"; e.value = "가"; e.textContent = "단추"; return e;
};
속성.forEach((a, k) => {
  const f = document.createElement("form");
  f.id = "폼" + k; f.action = "/r"; f.method = "post";
  for (const t of 대상) {
    const e = 만들기(t);
    e.id = a + "-" + t; e.name = t;
    if (a !== "없음") e.setAttribute(a, "");
    f.append(e);
  }
  document.getElementById("자리").append(f);
});
const 탭 = [["js", "document.getElementById('시작').focus(); window.__간곳 = []; 1"]];
for (let i = 0; i < 18; i++) 탭.push(["keyhere", "Tab", "Tab", 9], ["js", "window.__간곳.push(document.activeElement.id || document.activeElement.tagName); 1"]);
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [
  ...속성.map((a, k) => ({ 이름: "폼" + k + "(" + a + ") · requestSubmit(그 폼의 button)",
    단계: [["js", "(() => { try { document.getElementById('폼" + k + "').requestSubmit(document.getElementById('" + a + "-button')); } catch (e) { 적기('예외 ' + e.name); } return 1; })()"]] })),
  { 이름: "Tab 열여덟 번", 단계: 탭, 뒤: "JSON.stringify({ 간곳: window.__간곳, 검증: Object.fromEntries([...document.querySelectorAll('#자리 [id]')].map(e => [e.id, e.willValidate])) })" },
];
window.__종합 = 결과 => {
  const 탭결과 = JSON.parse(결과[3].뒤);
  const 셈 = (a, t, 점) => {
    if (점 === "제출") { const r = 결과[속성.indexOf(a)]; return r.필드 ? r.필드.includes(t) : false; }
    if (점 === "포커스") return 탭결과.간곳.includes(a + "-" + t);
    return 탭결과.검증[a + "-" + t];
  };
  const 점들 = ["제출", "포커스", "검증"];
  const O = [(칸("속성 · 대상", 22) + 점들.map(p => 칸(p, 8)).join("")).trimEnd()];
  let 갈림 = 0, 전체 = 0, 명세갈림 = 0, 명세전체 = 0;
  for (const a of 속성) for (const t of 대상) {
    let 행 = 칸(a + " · " + t, 22);
    for (const p of 점들) {
      const v = 셈(a, t, p);
      if (a !== "없음") { 전체++; 갈림 += v !== 셈("없음", t, p); }
      명세전체++; 명세갈림 += v !== 명세[a][t][점들.indexOf(p)];
      행 += 칸(v ? "예" : "—", 8);
    }
    O.push(행.trimEnd());
  }
  O.push("(제출 = 서버가 받은 필드에 그 이름이 있나 · 포커스 = 진짜 Tab 열여덟 번 안에 닿았나 · 검증 = willValidate)");
  O.push("Tab 이 닿은 곳 = " + 탭결과.간곳.join(" → "));
  for (const k of [0, 1, 2]) O.push("폼" + k + " 의 기록 = " + (결과[k].기록.join(" → ") || "(없음)") + " · 서버 필드 = " + (결과[k].필드 ? (결과[k].필드.join(",") || "(빈 본문)") : "(요청 없음)"));
  O.push("「없음」과 갈린 칸 = " + 갈림 + " / " + 전체);
  O.push("명세 열과 갈린 칸 = " + 명세갈림 + " / " + 명세전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

```javascript
// html29b-30-spec.js
// 명세 열 — [제출에 실리나, 순차 포커스를 받나, willValidate]
// disabled: 항목 목록에서 건너뛴다 · 포커스 가능 영역이 아니다 · 제약 검증에서 빠진다(barred)
// readonly: input 의 텍스트·날짜·number 칸과 textarea 에만 적용된다 — 적용되면 barred · checkbox 에는 적용되지 않는다 · select·button 에는 그 속성이 없다
// button: 누른(제출자) 단추만 실린다 — 이 표의 제출은 그 폼의 button 을 제출자로 준 requestSubmit 이다
const 명세 = {
  없음:     { text: [true, true, true],   checkbox: [true, true, true],   select: [true, true, true],   textarea: [true, true, true],   button: [true, true, true] },
  disabled: { text: [false, false, false], checkbox: [false, false, false], select: [false, false, false], textarea: [false, false, false], button: [false, false, false] },
  readonly: { text: [true, true, false],  checkbox: [true, true, true],   select: [true, true, true],   textarea: [true, true, false],  button: [true, true, true] },
};
```

```text
$ python3 html29b-form.py 시도 html29b-30-grid.html | sed -n '/^속성 · 대상/,$p'
속성 · 대상           제출    포커스  검증
없음 · text           예      예      예
없음 · checkbox       예      예      예
없음 · select         예      예      예
없음 · textarea       예      예      예
없음 · button         예      예      예
disabled · text       —      —      —
disabled · checkbox   —      —      —
disabled · select     —      —      —
disabled · textarea   —      —      —
disabled · button     —      —      —
readonly · text       예      예      —
readonly · checkbox   예      예      —
readonly · select     예      예      예
readonly · textarea   예      예      —
readonly · button     예      예      예
(제출 = 서버가 받은 필드에 그 이름이 있나 · 포커스 = 진짜 Tab 열여덟 번 안에 닿았나 · 검증 = willValidate)
Tab 이 닿은 곳 = 없음-text → 없음-checkbox → 없음-select → 없음-textarea → 없음-button → readonly-text → readonly-checkbox → readonly-select → readonly-textarea → readonly-button → BODY → 시작 → 없음-text → 없음-checkbox → 없음-select → 없음-textarea → 없음-button → readonly-text
폼0 의 기록 = submit(submitter=없음-button) · 서버 필드 = text,checkbox,select,textarea,button
폼1 의 기록 = submit(submitter=disabled-button) · 서버 필드 = (빈 본문)
폼2 의 기록 = submit(submitter=readonly-button) · 서버 필드 = text,checkbox,select,textarea,button
「없음」과 갈린 칸 = 18 / 30
명세 열과 갈린 칸 = 1 / 45
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`disabled` 는 대상 다섯 × 지점 셋 = 15 칸이 전부 끊겼다** — 서버 필드가 **빈 본문**(`requestSubmit(disabled 단추)` 도 **제출은 됐다** — `submit(submitter=disabled-button)`), Tab 은 **폼1 을 통째로 건너뛰고**, `willValidate` 는 전부 거짓. 명세 — 항목 목록을 만들 때 「필드가 **disabled** 면 건너뛴다」 · 「disabled 면 **제약 검증에서 빠진다**」 · `readonly` 절의 비규범 설명 — 「disabled 개념을 쓰는 규범 문장이 **활성화 동작**, **포커스 가능 영역인지**, **항목 목록 만들기** 같은 곳에 있다」(포커스 쪽의 규범 문장 자체는 이 편이 따라가 읽지 않았다).
- ★★ **`requestSubmit(disabled 인 단추)` 가 제출했다** — 명세의 `requestSubmit` 은 「제출 단추가 아니면 `TypeError` · 소유자가 다르면 `NotFoundError`」만 본다. **비활성 여부는 검사하지 않는다.** 그 단추의 `name` 은 비활성이라 **안 실렸다.**
- ★★★ **`readonly` 는 제출·포커스가 「없음」과 같고, 검증만 끊겼다** — `text`·`textarea` 의 `willValidate` 가 거짓(명세 — 「`readonly` 가 **지정되면** 제약 검증에서 빠진다」). [24번](../24-input-types-choice-special/2-summary.md)의 「`disabled` 는 안 실리고 `readonly` 는 실린다」가 `text` 줄이다.
- ★★ **`select`·`button` 의 `readonly` 는 아무것도 안 바꿨다** — 두 요소에는 **그 속성이 없다**(명세의 콘텐츠 속성 목록).
- ★★★ **명세 열과 갈린 칸 1 / 45 — `readonly · checkbox` 의 검증.** 명세는 Checkbox 상태에 `readonly` 가 「**지정하지 말아야 하고 적용되지 않는다**」고 적는다([28번](../28-validation-attributes/2-summary.md)이 「적용되지 않는 속성은 깃발도 없다」로 쓴 그 목록). 그 읽기라면 검증은 「없음」과 같아야 한다. **Chrome 은 `false`** 다. ★ 그런데 `readonly` 절의 문장은 「`readonly` 속성이 **`input` 요소에 지정되면**」이다 — **타입을 묻지 않는다.** 두 문장이 부딪히는 자리이고, **Chrome 은 뒤 문장을 글자대로 읽은 쪽**이다. 이 편은 이것을 **이탈로 세지 않고 「명세 판별」로 남긴다**((2) 에서 더 잰다).

```text
  「없음」과 갈린 칸 18 / 30 이 어디서 났나

                text   checkbox   select   textarea   button
  disabled      ✕✕✕    ✕✕✕        ✕✕✕      ✕✕✕        ✕✕✕       ← 15 (제출 · 포커스 · 검증)
  readonly      ··✕    ··✕        ···      ··✕        ···       ←  3 (검증만)
                       ★ 명세 목록으로는 ··· 이어야 할 자리 (판별)
```

### (2) 진짜 키 + 창 ② — `readonly` 가 막는 것과 못 막는 것

**언제 쓰나** — 「읽기 전용으로 둔 체크박스를 사용자가 켰다」·「읽기 전용 필수 칸이 비었는데 제출된다」를 가를 때.

여덟 타입마다 **`readonly` 칸과 짝**을 두고 **같은 진짜 키**를 줬다(글자 칸은 End + 글자, 수·날짜는 ArrowUp, 슬라이더는 ArrowRight, 체크박스·라디오는 Space, `select` 는 ArrowDown). 뒤의 세 폼은 `required` 와 겹칠 때다.

```html
<!-- html29b-30-readonly.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 readonly 가 닿는 곳</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<div id="자리"></div>
<form id="가" action="/r" method="post"><input name="t" readonly required><button id="가보냄">보냄</button></form>
<form id="나" action="/r" method="post"><input name="c" type="checkbox" readonly required><button id="나보냄">보냄</button></form>
<form id="다" action="/r" method="post"><input name="t" required><button id="다보냄">보냄</button></form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// [이름, 만들기, 진짜 키 편집, 값 읽기]
const 줄 = [
  ["text", () => Object.assign(document.createElement("input"), { value: "가" }), s => [["key", s, "End", "End", 35], ["type", s, "x"]], e => e.value],
  ["number", () => Object.assign(document.createElement("input"), { type: "number", value: "1" }), s => [["key", s, "ArrowUp", "ArrowUp", 38]], e => e.value],
  ["date", () => Object.assign(document.createElement("input"), { type: "date", value: "2026-01-01" }), s => [["key", s, "ArrowUp", "ArrowUp", 38]], e => e.value],
  ["range", () => Object.assign(document.createElement("input"), { type: "range", value: "50" }), s => [["key", s, "ArrowRight", "ArrowRight", 39]], e => e.value],
  ["checkbox", () => Object.assign(document.createElement("input"), { type: "checkbox" }), s => [["key", s, " ", "Space", 32, " "]], e => String(e.checked)],
  ["radio", () => Object.assign(document.createElement("input"), { type: "radio" }), s => [["key", s, " ", "Space", 32, " "]], e => String(e.checked)],
  ["select", () => { const e = document.createElement("select"); e.append(new Option("가", "가"), new Option("나", "나")); return e; }, s => [["key", s, "ArrowDown", "ArrowDown", 40]], e => e.value],
  ["textarea", () => Object.assign(document.createElement("textarea"), { value: "가" }), s => [["key", s, "End", "End", 35], ["type", s, "x"]], e => e.value],
];
const 자리 = document.getElementById("자리");
for (const [t, 만들기] of 줄) for (const 앞 of ["ro", "tw"]) {
  const e = 만들기(); e.id = 앞 + "-" + t; e.name = 앞 + t;
  if (앞 === "ro") e.setAttribute("readonly", "");
  자리.append(e);
}
const 편집 = 줄.flatMap(([t, , 키]) => [...키("#ro-" + t), ...키("#tw-" + t)]);
const 읽기 = "JSON.stringify(Object.fromEntries([...document.querySelectorAll('#자리 [id]')].map(e => [e.id, [e.type === 'checkbox' || e.type === 'radio' ? String(e.checked) : e.value, e.willValidate, e.matches(':read-only')]])))";
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [
  { 이름: "편집 전", 단계: [], 뒤: 읽기 },
  { 이름: "진짜 키로 편집", 단계: 편집, 뒤: 읽기 },
  { 이름: "가(text readonly required 빈 칸) · 보냄", 단계: [["js", "(() => { const i = document.getElementById('가').t; 적기('valueMissing=' + i.validity.valueMissing + ' · willValidate=' + i.willValidate + ' · :invalid=' + i.matches(':invalid')); return 1; })()"], ["click", "#가보냄"]] },
  { 이름: "나(checkbox readonly required 안 켬) · 보냄", 단계: [["js", "(() => { const i = document.getElementById('나').c; 적기('valueMissing=' + i.validity.valueMissing + ' · willValidate=' + i.willValidate + ' · :invalid=' + i.matches(':invalid')); return 1; })()"], ["click", "#나보냄"]] },
  { 이름: "다(text required 빈 칸 · readonly 없음) · 보냄", 단계: [["js", "(() => { const i = document.getElementById('다').t; 적기('valueMissing=' + i.validity.valueMissing + ' · willValidate=' + i.willValidate + ' · :invalid=' + i.matches(':invalid')); return 1; })()"], ["click", "#다보냄"]] },
];
window.__종합 = 결과 => {
  const A = JSON.parse(결과[0].뒤), B = JSON.parse(결과[1].뒤);
  const O = [칸("type", 10) + 칸("readonly 칸: 전 → 뒤", 30) + 칸("짝(속성 없음): 전 → 뒤", 30) + 칸("willValidate", 14) + ":read-only"];
  let 막음 = 0;
  for (const [t] of 줄) {
    const r = "ro-" + t, w = "tw-" + t;
    const 막았나 = A[r][0] === B[r][0] && A[w][0] !== B[w][0];
    막음 += 막았나;
    O.push(칸(t, 10) + 칸(JSON.stringify(A[r][0]) + " → " + JSON.stringify(B[r][0]), 30) + 칸(JSON.stringify(A[w][0]) + " → " + JSON.stringify(B[w][0]), 30)
      + 칸(A[r][1] + " / " + A[w][1], 14) + A[r][2] + " / " + A[w][2]);
  }
  O.push("(willValidate · :read-only 는 「readonly 칸 / 짝」)");
  O.push("readonly 가 사용자 편집을 막은 칸 = " + 막음 + " / " + 줄.length);
  O.push("");
  for (const r of 결과.slice(2)) O.push(r.이름 + "\n  페이지  " + r.기록.join(" → ") + "\n  서버    " + (r.요청.length ? r.서버.find(l => l.trim().startsWith("필드")).trim() : "(받은 요청 없음)"));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html29b-form.py 시도 html29b-30-readonly.html | sed -n '/^type /,$p'
type      readonly 칸: 전 → 뒤         짝(속성 없음): 전 → 뒤       willValidate  :read-only
text      "가" → "가"                  "가" → "가x"                 false / true  true / false
number    "1" → "1"                    "1" → "2"                    false / true  true / false
date      "2026-01-01" → "2026-01-01"  "2026-01-01" → "2027-01-01"  false / true  true / false
range     "50" → "51"                  "50" → "51"                  false / true  true / true
checkbox  "false" → "true"             "false" → "true"             false / true  true / true
radio     "false" → "true"             "false" → "true"             false / true  true / true
select    "가" → "나"                  "가" → "나"                  true / true   true / true
textarea  "가" → "가"                  "가" → "가x"                 false / true  true / false
(willValidate · :read-only 는 「readonly 칸 / 짝」)
readonly 가 사용자 편집을 막은 칸 = 4 / 8

가(text readonly required 빈 칸) · 보냄
  페이지  valueMissing=false · willValidate=false · :invalid=false → click(가보냄 · detail=1) → submit(submitter=가보냄)
  서버    필드  t=「」
나(checkbox readonly required 안 켬) · 보냄
  페이지  valueMissing=true · willValidate=false · :invalid=false → click(나보냄 · detail=1) → submit(submitter=나보냄)
  서버    필드  (없음)
다(text required 빈 칸 · readonly 없음) · 보냄
  페이지  valueMissing=true · willValidate=true · :invalid=true → click(다보냄 · detail=1) → invalid(t)
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`readonly` 가 사용자 편집을 막은 칸은 4 / 8** — `text`·`number`·`date`·`textarea`. **`range`·`checkbox`·`radio`·`select`** 는 짝과 **똑같이 바뀌었다**(`50 → 51` · `false → true` · `가 → 나`). 명세 — 「**텍스트 컨트롤만** 읽기 전용이 될 수 있다. 체크박스·단추 같은 다른 컨트롤에는 읽기 전용과 비활성의 쓸모 있는 구별이 없어서 `readonly` 가 **적용되지 않는다**」 · 「`readonly` 는 (예: Date 상태에서는 되지만 **Checkbox 상태에서는 아니다**) mutable 을 막을 수 있다」.
- ★★★ **그런데 `willValidate` 는 `select` 만 참이다** — `range`·`checkbox`·`radio` 의 `readonly` 칸도 **`false`**. **편집은 못 막으면서 검증에서는 뺐다.** (1) 의 판별이 체크박스 하나가 아니라 「**`readonly` 가 적용되지 않는 `input` 타입 전부**」였다.
- ★★★ **`readonly required` 인 체크박스는 안 켠 채로 제출됐다** — `valueMissing=true` 인데 `willValidate=false` 라 **검증이 돌지 않았고** 서버 필드는 `(없음)`. 사용자는 그 칸을 **Space 로 켤 수 있으니**(위 표) 「필수 동의 체크박스를 `readonly` 로 두면 **필수가 사라진다**」.
- ★★ **`readonly required` 인 빈 글자 칸은 `valueMissing` 부터 거짓이다** — 명세의 `required` 제약 — 「요소가 required 이고 … **요소가 mutable 이고** 값이 빈 문자열이면 missing」. 읽기 전용이면 mutable 이 아니다. 짝(`readonly` 없음)은 `valueMissing=true` 로 `invalid(t)` 를 내고 멈췄다. ★ **체크박스의 `required` 제약에는 「mutable」 조건이 없다** — 그래서 거기는 `valueMissing=true` 가 섰다.
- ★ **`:read-only` 는 「사용자가 못 고친다」의 판정이 아니다** — `range`·`checkbox`·`radio`·`select` 는 **짝도** `:read-only` 다(글자를 편집하는 칸이 아니라서). `readonly` 가 먹었는지를 CSS 로 가를 수 없다.

```text
  readonly 가 닿는 곳 — 타입마다 두 질문 (이 판)

                  사용자 편집을 막나    검증에서 빼나(willValidate=false)
  text · number · date · textarea    막는다              뺀다          ← 명세대로 (텍스트 컨트롤)
  range · checkbox · radio           ✕ 못 막는다          ★ 뺀다        ← 「적용되지 않는다」와 부딪힘
  select                             ✕ (속성이 없다)       빼지 않는다   ← 명세대로
```

### (3) 창 ② — `autofocus` 는 어느 칸을 고르나

**언제 쓰나** — 「`autofocus` 를 둘 달았다」·「대화상자 안의 칸에 달았다」·「`#` 링크로 들어오면 포커스가 안 간다」를 가를 때.

```html
<!-- html29b-30-autofocus.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 autofocus</title>
</head>
<body>
<input id="a0">
<dialog id="창1"><input id="d0"><input id="d1" autofocus></dialog>
<dialog id="창2"><p>글</p><input id="e0"><input id="e1"></dialog>
<input id="a1" autofocus>
<input id="a2" autofocus>
<p id="p1">아래</p>
<script>
const 곳 = () => document.activeElement.id || document.activeElement.tagName;
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
window.__끝 = async () => {
  await 두틀();
  const O = ["주소의 조각 = " + JSON.stringify(location.hash) + " · document.hasFocus() = " + document.hasFocus()];
  O.push("로드 뒤 포커스 = " + 곳());
  const 창1 = document.getElementById("창1"), 창2 = document.getElementById("창2");
  창1.showModal(); O.push("창1.showModal() 뒤 = " + 곳()); 창1.close();
  창1.show();      O.push("창1.show() 뒤 = " + 곳()); 창1.close();
  창2.showModal(); O.push("창2.showModal() 뒤 (autofocus 없음) = " + 곳()); 창2.close();
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html29b-form.py page html29b-30-autofocus.html
주소의 조각 = "" · document.hasFocus() = true
로드 뒤 포커스 = a1
창1.showModal() 뒤 = d1
창1.show() 뒤 = d1
창2.showModal() 뒤 (autofocus 없음) = e0
(exit 0)
```

같은 페이지를 **주소에 `#p1` 을 붙여** 열었다.

```text
$ python3 html29b-form.py page 'html29b-30-autofocus.html#p1'
주소의 조각 = "#p1" · document.hasFocus() = true
로드 뒤 포커스 = BODY
창1.showModal() 뒤 = d1
창1.show() 뒤 = d1
창2.showModal() 뒤 (autofocus 없음) = e0
(exit 0)
```

- ★★★ **둘이면 첫째다** — `a1`·`a2` 둘 다 `autofocus` 인데 포커스는 **`a1`**. 명세 — 삽입될 때 **autofocus 후보 목록**에 쌓고, 한 번 비울 때 **목록의 앞에서부터** 포커스 가능한 첫 칸을 고른다. ★ 명세는 「같은 **autofocus 범위 뿌리**에 `autofocus` 둘을 두면 안 된다」고 **작성자에게** 금지한다 — 어겨도 에러는 없다.
- ★★★ **닫힌 `dialog` 안의 `d1` 은 건너뛰었다** — 트리 순서로 `a1` 보다 앞인데 로드 뒤 포커스가 `a1` 이다. 닫힌 대화상자의 칸은 **포커스 가능 영역이 아니라서** 목록에서 떨어진다. 대신 **`showModal()`·`show()` 가 그 `d1` 을 골랐다.** 명세 — 「`autofocus` 가 대화상자·팝오버 **안에** 있으면 그것이 **보일 때** 포커스된다」.
- ★★ **`autofocus` 없는 대화상자는 첫 칸으로 간다** — `창2.showModal()` 뒤 **`e0`**(글 문단은 포커스를 못 받는다).
- ★★★ **주소에 `#p1` 을 붙이니 로드 뒤 포커스가 `BODY`** 다 — 명세의 「autofocus 후보 비우기」 — 「최상위 문서에 **조각 대상(target element)** 이 있으면 **후보를 전부 비우고** 끝낸다」. 링크로 페이지 **중간**에 들어온 사용자를 칸으로 끌고 가지 않으려는 규칙이다. 대화상자 쪽은 영향이 없다(`d1`·`e0` 그대로).

### (4) 창 ② + 창 ⑦ — `autocomplete` 토큰 열일곱 · `inputmode` 일곱

**언제 쓰나** — 「`autocomplete="e-mail"` 이 먹나」·「토큰 순서를 바꿔도 되나」·「`inputmode` 가 접근성 트리에 남나」를 가를 때.

자동 완성 **제안 UI** 와 **가상 키보드**는 headless 데스크톱에서 **볼 수 없다**(「못 잰 것」). 그래서 페이지 안에서 잴 수 있는 둘 — **IDL 값**과 **접근성 노드의 속성** — 만 물었다. 「명세 열」은 따로 둔 파일이다.

```html
<!-- html29b-30-hints.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>30 autocomplete 와 inputmode</title>
<script src="html29b-30-hints-spec.js"></script>
</head>
<body>
<form id="f1">
  <input id="c1" autocomplete="email">
  <input id="c2" autocomplete="EMAIL">
  <input id="c3" autocomplete="shipping email">
  <input id="c4" autocomplete="Shipping email">
  <input id="c5" autocomplete="section-A billing tel">
  <input id="c6" autocomplete="home email">
  <input id="c7" autocomplete="home name">
  <input id="c8" autocomplete="email shipping">
  <input id="c9" autocomplete="e-mail">
  <input id="c10" autocomplete="off">
  <input id="c11" autocomplete="shipping off">
  <input id="c12" type="password" autocomplete="current-password webauthn">
  <input id="c13" autocomplete="">
  <input id="c14">
  <textarea id="c15" autocomplete="street-address"></textarea>
  <select id="c16" autocomplete="country"><option>가</option></select>
</form>
<form id="f2" autocomplete="off"><input id="c17"></form>
<div id="m">
  <input id="m1" inputmode="numeric">
  <input id="m2" inputmode="NUMERIC">
  <input id="m3" inputmode="decimal">
  <input id="m4" inputmode="none">
  <input id="m5" inputmode="zzz">
  <input id="m6">
  <input id="m7" type="number">
</div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 모두 = [...document.querySelectorAll("[id^=c], [id^=m]")].filter(e => /^[cm]\d+$/.test(e.id));
window.__대상 = 모두.map(e => [e.id, "#" + e.id]);
window.__끝 = () => {
  const O = [칸("id", 5) + 칸("속성 글자", 34) + 칸("IDL 값", 30) + 칸("명세 열", 30) + "접근성 노드의 속성"];
  let 갈림 = 0, 전체 = 0;
  const 트리이름 = new Set();
  for (const e of 모두) {
    const 자동 = e.id.startsWith("c");
    const 글자 = 자동 ? (e.hasAttribute("autocomplete") ? JSON.stringify(e.getAttribute("autocomplete")) : "(속성 없음)" + (e.form && e.form.id === "f2" ? " · form off" : ""))
                    : (e.hasAttribute("inputmode") ? "inputmode=" + JSON.stringify(e.getAttribute("inputmode")) : "(속성 없음)" + (e.type === "number" ? " · type=number" : ""));
    const 값 = 자동 ? e.autocomplete : e.inputMode;
    const 기대 = 명세값[e.id];
    전체++; 갈림 += 값 !== 기대;
    const 속성 = Object.entries(__AX[e.id].속성).map(([k, v]) => k + "=" + v);
    속성.forEach(x => 트리이름.add(x.split("=")[0]));
    O.push(칸(e.id, 5) + 칸(글자, 34) + 칸(JSON.stringify(값), 30) + 칸(JSON.stringify(기대), 30) + (속성.join(" ") || "(없음)"));
  }
  O.push("명세 열과 갈린 칸 = " + 갈림 + " / " + 전체);
  O.push("접근성 노드에 나온 속성 이름 = " + [...트리이름].sort().join(" · "));
  return O.join("\n");
};
</script>
</body>
</html>
```

```javascript
// html29b-30-hints-spec.js
// 명세 열 — autocomplete 는 「IDL-exposed autofill value」(Autofill 처리 모델), inputMode 는 「알려진 값으로만 제한된 반영」
// 처리 모델: 마지막 토큰이 필드 이름 → IDL 값은 그 토큰 그대로 · 앞의 home/work 등은 Contact 필드 앞에서만 · shipping/billing 은 목록의 글자(소문자)
//            · section-* 는 소문자로 · 규칙에 안 맞으면 default = 빈 문자열 · off/on 은 토큰이 하나일 때만
const 명세값 = {
  c1: "email", c2: "EMAIL", c3: "shipping email", c4: "shipping email", c5: "section-a billing tel",
  c6: "home email", c7: "", c8: "", c9: "", c10: "off", c11: "", c12: "current-password webauthn",
  c13: "", c14: "", c15: "street-address", c16: "country", c17: "",
  m1: "numeric", m2: "numeric", m3: "decimal", m4: "none", m5: "", m6: "", m7: "",
};
```

```text
$ python3 html29b-form.py page html29b-30-hints.html
id   속성 글자                         IDL 값                        명세 열                       접근성 노드의 속성
c1   "email"                           "email"                       "email"                       invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c2   "EMAIL"                           "email"                       "EMAIL"                       invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c3   "shipping email"                  "shipping email"              "shipping email"              invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c4   "Shipping email"                  "shipping email"              "shipping email"              invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c5   "section-A billing tel"           "section-a billing tel"       "section-a billing tel"       invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c6   "home email"                      "home email"                  "home email"                  invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c7   "home name"                       ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c8   "email shipping"                  ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c9   "e-mail"                          ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c10  "off"                             "off"                         "off"                         invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c11  "shipping off"                    ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c12  "current-password webauthn"       "current-password webauthn"   "current-password webauthn"   invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c13  ""                                ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c14  (속성 없음)                       ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
c15  "street-address"                  "street-address"              "street-address"              invalid=false focusable=true editable=plaintext settable=true multiline=true readonly=false required=false
c16  "country"                         "country"                     "country"                     invalid=false focusable=true hasPopup=menu expanded=false
c17  (속성 없음) · form off            ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m1   inputmode="numeric"               "numeric"                     "numeric"                     invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m2   inputmode="NUMERIC"               "numeric"                     "numeric"                     invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m3   inputmode="decimal"               "decimal"                     "decimal"                     invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m4   inputmode="none"                  "none"                        "none"                        invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m5   inputmode="zzz"                   ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m6   (속성 없음)                       ""                            ""                            invalid=false focusable=true editable=plaintext settable=true multiline=false readonly=false required=false
m7   (속성 없음) · type=number         ""                            ""                            invalid=false focusable=true editable=plaintext settable=true required=false valuemin=0 valuemax=0 valuetext=
명세 열과 갈린 칸 = 1 / 24
접근성 노드에 나온 속성 이름 = editable · expanded · focusable · hasPopup · invalid · multiline · readonly · required · settable · valuemax · valuemin · valuetext
(exit 0)
```

- ★★★ **규칙에 맞는 토큰은 IDL 에 그대로, 틀리면 빈 문자열** — `e-mail`(`c9`)·`email shipping`(`c8`, 순서가 틀림)·`home name`(`c7`, `home` 은 연락처 필드 앞에만)·`shipping off`(`c11`, `off` 는 혼자여야)이 전부 **`""`**. 명세의 처리 모델이 **마지막 토큰부터 거꾸로** 읽고, 한 단계라도 어긋나면 「default」로 뛰어 **IDL 값을 빈 문자열로** 둔다. ★ 에러도 콘솔 경고도 없다 — **IDL 값을 읽어야만 보인다.**
- ★★ **`section-A` 는 소문자로, `Shipping` 도 소문자로** — `c5` 는 `"section-a billing tel"`, `c4` 는 `"shipping email"`. 명세가 그 두 조각을 「소문자로 바꾼다」·「**목록의 글자**를 넣는다」로 적는다.
- ★★★ **명세 열과 갈린 칸 1 / 24 — `c2`(`"EMAIL"`).** Chrome 은 **`"email"`** 로 돌려줬다. 명세의 처리 모델은 필드 이름을 **대소문자 무시로 비교**만 하고, IDL 값은 「**IDL value 를 field 와 같은 값으로 둔다**」 — 소문자로 바꾸는 단계가 **필드 토큰에는 없다**(`section-*` 에만 있다). 알고리즘을 끝까지 읽은 판정이다 → **이탈 1**(값의 대소문자뿐 — 자동 완성이 먹는지와는 무관하다).
- ★★ **폼의 `autocomplete="off"` 는 칸의 IDL 을 `"off"` 로 만들지 않는다** — `c17` 은 **`""`**. 명세 — 속성이 없으면 default 로 가 **IDL 값은 빈 문자열** · 폼이 off 면 내부의 **autofill field name** 만 `"off"` 가 된다. **IDL 로는 폼의 off 가 안 보인다.**
- ★★ **`inputMode` 는 알려진 값만** — `NUMERIC` → `"numeric"` · `zzz` → `""`. 명세 — 「알려진 값으로만 제한된 반영」. **`type=number` 는 `inputMode` 를 채우지 않는다**(`m7` `""`) — 타입에 맞는 자판을 고르는 것은 「UA 가 정해야 한다(should)」는 **기기 쪽** 일이다.
- ★★★ **접근성 노드에 `autocomplete`·`inputmode` 의 흔적은 없다** — 24 칸에서 나온 속성 이름은 `editable · expanded · focusable · hasPopup · invalid · multiline · readonly · required · settable · valuemax · valuemin · valuetext` 뿐이고, 토큰이 달라도 **칸마다 같은 줄**이다. **18-A — 24 곳을 물었고 0 곳이 답했다.** ★ **「트리에 없다」는 「보조 기술이 못 쓴다」가 아니다** — 보조 기술이 DOM 속성을 따로 읽을 수 있고, 이 판은 그것을 **못 본다.**

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 보여 주되 보내지 않기 | `disabled` | 제출 ✕ · 포커스 ✕ · 검증 ✕ |
| 보내되 못 고치게 | `readonly` | **글자·수·날짜 칸과 `textarea` 만** 막는다 |
| 들어오자마자 입력 | `autofocus` | 문서에 **하나** · `dialog` 안이면 열릴 때 |
| 자동 완성 힌트 | `autocomplete="[section-*] [shipping\|billing] [home\|work\|…] 필드"` | 순서가 틀리면 **조용히 `""`** |
| 가상 키보드 힌트 | `inputmode="numeric"` | 데스크톱에서는 **볼 것이 없다** |

### 어디서 헷갈리나

- **`readonly` 체크박스는 사용자가 켤 수 있다** — 그러면서 검증에서는 빠진다(이 판).
- **`readonly required` 는 둘 다 먹지 않는 짝이다** — 글자 칸은 missing 이 안 서고, 체크박스는 missing 이 서도 검증이 안 돈다.
- **`autocomplete` 토큰은 순서가 있다** — 필드 이름이 **맨 끝**.
- **`:read-only` 로 `readonly` 가 먹었는지 모른다** — 체크박스는 짝도 `:read-only`.

## 어디서 틀리나

### 1. 서버에 보내야 하는 값을 `disabled` 로 잠근다

**안 실린다**((1) — 폼1 의 서버 필드가 빈 본문 · [24번](../24-input-types-choice-special/2-summary.md)의 `x1`). 보내야 하면 `readonly` 또는 곁에 `hidden`.

### 2. 「동의」 체크박스를 바꾸지 못하게 `readonly` 로 둔다

**사용자가 Space 로 켠다**((2) — `checkbox false → true`). 바꾸지 못하게 하려면 `disabled`(그러면 안 실린다) 또는 스크립트로 막는다.

### 3. `readonly required` 체크박스로 「필수 동의」를 강제한다

**안 켠 채로 제출된다**((2) — 「나」 폼 · 서버 필드 `(없음)`). `readonly` 를 빼라.

### 4. 서버가 채운 값을 `readonly required` 로 두고 비었으면 제출이 막힐 거라 여긴다

**막히지 않는다**((2) — 「가」 폼 · `t=「」` 가 갔다). 빈 값 검사는 서버가 한다([29번](../29-constraint-validation/2-summary.md)).

### 5. `autofocus` 가 링크로 들어온 사용자에게도 먹을 거라 여긴다

**`#조각` 이 있으면 안 먹는다**((3) — `BODY`). 그것이 명세가 의도한 동작이다.

### 6. `autocomplete="e-mail"`·토큰 순서를 틀려도 「대충 알아듣겠지」

**IDL 이 `""` 가 된다**((4) — `c8`·`c9`). 에러가 없으니 **`element.autocomplete` 를 한 번 읽어 확인**한다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | disabled — 항목 목록에서 **건너뛴다** · **제약 검증에서 빠진다** · (비규범 설명) 「disabled 개념을 쓰는 규범 문장이 … **포커스 가능 영역인지** … 에 있다」 | (1) |
| **명세(HTML)** | readonly — **텍스트 컨트롤에만 적용** · 적용되면 not mutable · 「`input` 에 **지정되면** 검증에서 빠진다」 · Checkbox·Radio·Range 등의 「적용되지 않는」 목록에 있다 | (1)·(2) |
| **명세(HTML)** | `required` 의 missing — 글자 칸은 **mutable 조건**이 있고 체크박스는 없다 | (2) |
| **명세(HTML)** | `requestSubmit(단추)` — 제출 단추인지·소유자인지만 검사 · **비활성은 묻지 않는다** | (1) |
| **명세(HTML)** | autofocus 후보 — 앞에서부터 첫 포커스 가능 칸 · **조각 대상이 있으면 비운다** · `dialog` 가 보일 때 그 안의 `autofocus` | (3) |
| **명세(HTML)** | autofill 처리 모델 — 틀리면 IDL 값 `""` · `section-*` 소문자 · 필드 토큰은 **그대로** · `inputMode` 는 알려진 값으로만 | (4) |
| **구현(Chrome)** | **`readonly` 가 적용되지 않는 `input` 타입도 검증에서 뺀다**(`range`·`checkbox`·`radio`) — 두 문장 중 「지정되면」 쪽을 읽었다 · 필드 토큰을 **소문자로** 돌려준다 | (1)·(2)·(4) |
| **이 판의 관찰** | 「없음」과 갈린 칸 18 / 30 · 명세 열과 갈린 칸 **1 / 45**(판별) · **1 / 24**(이탈) · 편집을 막은 칸 4 / 8 · 트리에 힌트 흔적 0 / 24 | (1)\~(4) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **`inputmode` 가 띄우는 가상 키보드** | 데스크톱 headless 에 **가상 키보드가 없다** — 「모바일에서 숫자 자판이 뜬다」는 명세의 **should 문장**까지이고 이 판은 **못 쟀다** |
| ★★ **자동 완성 제안 UI · 비밀번호 관리자** | 페이지 밖의 브라우저 UI 이고 새 프로필에 저장된 값이 없다([22번](../22-input-types-text/2-summary.md)과 같은 제3의 상태) |
| **보조 기술이 `autocomplete` 를 읽나** | 트리에는 없지만(18-A) 보조 기술이 DOM 을 따로 읽는지는 **못 본다** |
| **포커스 링이 보이나** | 픽셀을 안 찍었다 — `:focus-visible` 은 [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) |

## 언제 쓰고 언제 안 쓰나

- **`disabled`** — 「지금은 쓸 수 없고 **보내지도 않는다**」. 서버가 그 값을 기다리면 쓰지 않는다.
- **`readonly`** — **글자·수·날짜 칸과 `textarea`** 에만. 체크박스·라디오·`select` 를 못 바꾸게 하려고 쓰지 않는다.
- **`readonly` 와 `required` 를 같이 쓰지 않는다** — 어느 타입에서도 필수 검사가 돌지 않았다.
- **`autofocus`** — 페이지의 **주목적이 입력**일 때(검색·로그인) **하나만**. 긴 문서 중간의 폼에는 달지 않는다.
- **`autocomplete`** — 필드 이름을 **맨 끝**에, 쓰고 나서 **IDL 값을 한 번 읽는다.**
- **`inputmode`** — 타입이 `text` 여야 하는 숫자(카드 번호·인증 번호)에. `type=number` 로 바꾸지 않는다([23번](../23-input-types-number-date/2-summary.md)의 「`number` 에 전화번호」).

## 핵심 문장

1. **`disabled` 는 제출·포커스·검증 세 지점을 전부 끊고, `readonly` 는 검증만 끊는다.**
2. **`readonly` 는 텍스트 컨트롤(글자·수·날짜 칸과 `textarea`)에서만 편집을 막는다 — `checkbox`·`radio`·`range`·`select` 는 사용자가 그대로 바꾼다.**
3. **Chrome 은 편집을 못 막는 `readonly` 칸도 검증에서 뺀다 — 그래서 `readonly required` 체크박스는 안 켠 채로 제출된다(명세 두 문장이 부딪히는 자리).**
4. **`autofocus` 는 문서의 첫 후보 하나를 고르고, 주소에 조각이 있으면 아무것도 고르지 않는다 — 대화상자 안의 것은 열릴 때 쓰인다.**
5. **`autocomplete` 토큰이 규칙에 어긋나면 에러 없이 IDL 값이 빈 문자열이 된다.**
6. **`inputmode` 는 기기에 주는 힌트다 — 데스크톱 headless 에서는 IDL 값 말고 잴 것이 없고, 접근성 트리에도 흔적이 없다.**

## 관련 자료

- [24번 주제](../24-input-types-choice-special/2-summary.md) — `disabled` 는 안 실리고 `readonly` 는 실린다((1) 격자)의 첫 측정.
- [27번 주제](../27-fieldset-and-legend/2-summary.md) — `fieldset[disabled]` 가 자손 전부를 비활성으로 퍼뜨리고, **그 안의 `required` 빈 칸이 제출을 막지 않았다.**
- [29번 주제](../29-constraint-validation/2-summary.md) — 제약 검증 상태 · `willValidate` 가 거짓이면 **깃발이 서도 검증이 안 돈다**의 쪽.
- [28번 주제](../28-validation-attributes/2-summary.md) — 「적용되지 않는 속성」 목록을 격자로 쟀다(`readonly` 는 그 격자 밖).
- [22번 주제](../22-input-types-text/2-summary.md) — 자동 완성 UI 가 「못 잰 것」인 이유 · 타입마다의 가상 키보드.
- [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) — `:disabled`·`:read-only` 로 칠하기 · 비활성·읽기 전용 칸이 `:valid`/`:invalid` 둘 다 아닌 것.
- 목록의 **45번 주제**(`tabindex`·`inert` — 포커스 순서의 정본) · 목록의 **47번 주제**(`dialog` 의 모달·포커스 트랩).

## 용어 풀이

- **`willValidate`** — 제약 검증 후보인가. 거짓이면 제출 때 검증하지 않는다.
- **제약 검증에서 빠진다(barred from constraint validation)** — 후보에서 제외. `disabled`·`readonly`(적용될 때)·`hidden` 타입 등.
- **mutable** — 사용자가 값을 바꿀 수 있는 상태. `disabled`·(텍스트 컨트롤의) `readonly` 가 빼앗는다.
- **autofocus 후보 목록** — 문서가 모아 두는 `autofocus` 요소들. 한 번 비우면 끝난다.
- **조각 대상(target element)** — 주소의 `#조각` 이 가리키는 요소. [07번](../07-id-and-fragments/2-summary.md).
- **IDL-exposed autofill value** — `element.autocomplete` 가 돌려주는 값. 처리 모델이 정한다.
- **가상 키보드** — 터치 기기가 띄우는 화면 자판. `inputmode` 는 그 종류의 힌트다.

## 더 들어가면

- **왜 체크박스에는 `readonly` 가 없나** — 명세의 비규범 설명 — 「체크박스·단추 같은 컨트롤에는 **읽기 전용과 비활성 사이에 쓸모 있는 구별이 없다**」. 보내되 못 바꾸게 하려면 `disabled` + `hidden` 을 쓰는 것이 명세가 가정한 길로 읽힌다(해석이다).
- **`autocomplete` 와 접근성** — 목록([`README.md`](../README.md))은 이 주제를 「`autocomplete` 토큰이 왜 접근성 항목인지」로 적었다. 이 판은 그 근거가 되는 **WCAG 원문을 열지 않았다** — 여기서는 「토큰이 틀리면 조용히 빈 값」까지만 쟀다.
- **`enterkeyhint`** — 가상 키보드의 Enter 키 모양 힌트. 명세의 바로 다음 절이다. 이 판은 던지지 않았다.
