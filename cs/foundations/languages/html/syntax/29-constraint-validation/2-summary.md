# html/syntax/29 — 제약 검증: 유효성 상태·`novalidate`·`:valid`/`:user-invalid` 의 관계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Constraints」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constraints) 절 — 「statically validate the constraints」·「interactively validate the constraints」·**「Security」**(「서버는 클라이언트 쪽 검증에 기대면 안 된다」), [「A form control's value」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#a-form-control's-value)의 **user validity boolean**, [「Form submission algorithm」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#form-submission-algorithm)(★ **검증보다 앞에서** user validity 를 참으로 둔다), [「Focus — processing model」](https://html.spec.whatwg.org/multipage/interaction.html#focus-update-steps)의 **focus update steps**(포커스를 떠날 때 값이 달라졌으면 user validity 를 참으로), 그리고 [Selectors Level 4 §12.3.4](https://drafts.csswg.org/selectors-4/#user-pseudos)(`:user-invalid` 는 **`:invalid` 인 것만**). **명세 본문은 앞 배치가 받아 둔 사본**(HTML 은 2026-09-26, Selectors 4 는 2026-09-23)으로 읽었다 — 이 배치는 네트워크를 쓰지 않았다.\
> ★★ **HTML 이 `:user-valid`/`:user-invalid` 를 정의하는 절(「Pseudo-classes」)은 그 사본에 없다** — 그래서 이 문서의 명세층은 **user validity 가 서고 지는 문장들 + Selectors 4** 까지다. 그 절을 읽지 않은 채 「이탈」로 적지 않는다((1) 의 한 칸).
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 사용자 입력은 **CDP 의 진짜 키·마우스**(`Input.dispatchKeyEvent`·`Input.insertText`·`Input.dispatchMouseEvent`)이고, 스크립트 대입과 **가른다.** 하네스는 [25번 주제](../25-label-association/3-answer.md)의 판을 이어 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 실었다(30\~32번이 같은 하네스를 쓴다).\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. `:user-valid`/`:user-invalid` 의 Baseline 은 [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md)이 조회한 값(widely 2026-05-02)을 인용한다 — 이 배치는 다시 조회하지 않았다.
> **선행** — [28번 주제](../28-validation-attributes/2-summary.md)(속성이 **어느 깃발**을 켜나 — 이 편은 그 깃발을 **CSS·제출 쪽에서 읽는다**).
> **경계** — ★★★ **속성 × 타입 격자와 `validity` 깃발**은 [28번](../28-validation-attributes/2-summary.md)이 쟀다 — 다시 재지 않는다. **검증이 언제 도나**(`form.submit()` 은 건너뛴다)와 **`curl` 우회**는 [21번](../21-form-submission-model/2-summary.md)의 (2)·(5) 다. **`:invalid` 가 로드 직후부터 켜지고 `:user-invalid` 는 blur 뒤에 켜지는 것**은 [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md)의 (4)·(5) 가 **이메일 칸 하나**로 쟀다 — 여기는 그 열을 **칸 셋 × 시점 여섯**으로 늘리고 **제출 시도·`reset()`** 을 더한다. **스크립트로 읽고 덮어쓰는 표면**(`checkValidity`·`reportValidity`·`setCustomValidity`)의 정본은 web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **60번**이다 — 여기는 **그것이 제출·의사 클래스와 만나는 자리**만 (3) 에서 잰다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ②(노드 프로브)다 — `element.matches(':user-invalid')` 로 묻는 의사 클래스 격자.** 짝으로 **창 ⑤(서버 요청 로그)** 가 「검증을 건너면 서버가 무엇을 받나」를 한 쌍으로 보인다.

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
| **흔들린다** | CDP 포트·프로필 경로·서버 포트 | 출력에는 안 들어간다(로그는 서버 이름 `A` 만 적는다) |
| **흔들린다** | `validationMessage` 문구 · 검증 풍선 | 구현이다 — **근거로 쓰지 않는다**(이 편은 문구를 한 번도 찍지 않았다) |
| **안 흔들린다** | `matches()` 의 참·거짓 · `change`·`invalid`·`submit` 기록 · 서버가 받은 필드 · 「갈린 칸 N / M」 | 시도마다 페이지를 새로 연다 · 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **② 노드 프로브**(`matches()` · `validity` · `activeElement`) | ★ **쓴다 — 본체** | 의사 클래스 넷이 **시점마다** 맞나((1)) · 검증을 건너도 **깃발은 서 있나**((2)) · 스크립트 API 가 **포커스·`:user-invalid`** 를 움직이나((3)) |
| **② 의 짝 — `change`·`invalid`·`submit` 기록** | ★ **쓴다** | 「user validity 가 섰다」의 **명세상 방아쇠**(`change`)가 **났나**((1)) · 검증이 **돌았나**(`invalid`)((2)·(3)) |
| **⑤ 서버 요청 로그** | ★ **쓴다** | 검증을 건너는 네 길에서 **서버가 무효한 값을 받나**((2)) |
| **⑦ 접근성 트리** | **안 쟀다** | `:user-invalid` 가 트리의 `invalid` 상태와 같이 움직이나는 이 판이 묻지 않았다 — 「부적용」이 아니라 **안 돌려 본 것**이다 |
| **① · ③ · ④ · ⑥** | **부적용** | 파서·글자 렌더·문서 모드·렌더 차단과 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「검증이 돌았나」를 `invalid` 이벤트로 물었다**([21번](../21-form-submission-model/2-summary.md)과 같은 창). 검증 알고리즘은 밖에서 보이는 반환값이 없고, **실패하면 칸마다 `invalid`** 가 난다. ★ 이 창이 못 보는 것 — **돌았는데 통과한 경우**. 그래서 (2) 의 폼은 **일부러 무효**하게 만들었다.
- ★★ **18-A — 몇 군데 물었나.** (1) 은 **칸 셋 × 의사 클래스 넷 × 시점 여섯 = 72 곳**을 물었다. 「안 켜졌다」가 결론인 칸이 대부분이라 **그 72 곳을 미리 선언**하고 「로드 직후와 갈린 칸 N / 60」을 스크립트가 센다.

## 한눈에 — 쉽게 말하면

**★ 제약 검증은 「현관의 체크리스트」다. 빈칸이 있으면 종이는 처음부터 빨갛게 표시돼 있지만(`:invalid`), 손님을 혼내는 것은 손님이 한 번 써 보고 돌아선 뒤다(`:user-invalid`). 그리고 그 종이는 택배 기사(서버)에게 같이 가지 않는다.**

현관 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **체크리스트의 빨간 표시** | **유효성 상태**(`validity` 깃발) — 칸의 값이 정한다 · **`:valid`/`:invalid`** 가 그대로 읽는다 |
| **「손님이 써 봤다」 도장** | **user validity**(요소마다 하나인 불리언) — **포커스를 떠날 때 값이 달라졌거나**, **제출을 시도했을 때** 찍힌다 · `reset` 이 지운다 |
| **손님에게 보이는 빨간 줄** | **`:user-invalid`** = 도장 **+** 빨간 표시 |
| **현관에서 멈춰 세움** | **대화형 검증**(제출 때) — `invalid` 이벤트를 쏘고 멈춘다 |
| **「체크 생략」 팻말** | **`novalidate`**(폼) · **`formnovalidate`**(단추) — 멈추지 않지만 **빨간 표시는 그대로** 있다 |
| **택배 기사** | **서버** — 체크리스트를 **못 본다** |

- **로드 직후와 갈린 칸 6 / 60** — 여섯 칸 전부가 `:user-*` 줄이었다. **`:valid`/`:invalid` 는 여섯 시점 내내 한 번도 안 움직였다**((1)).
- ★★★ **`:user-invalid` 가 켜진 시점은 「키 입력 → Tab」과 「제출 시도」 둘뿐** — 스크립트 대입·포커스 중 입력에서는 안 켜졌고, `reset()` 이 껐다((1)).
- ★★★ **서버가 무효한 값을 받은 시도 4 / 5** — 검증을 켠 폼의 **클릭** 하나만 막혔다((2)).
- ★★ **`novalidate` 폼도 제출을 시도하면 손대지 않은 칸에 `:user-invalid` 가 켜졌다** — 검증을 건너도 도장은 찍힌다((3)).

```text
  한 칸이 겪는 두 층 — 값이 정하는 층과 사용자가 정하는 층

  값 ─────────> validity 깃발 ─────> :valid / :invalid         (로드 직후부터 · 스크립트 대입에도)
                    │
  사용자 ──> user validity 도장 ─┐
   · 포커스를 떠날 때 값이 달라짐  ├─> :user-valid / :user-invalid   (도장 AND 깃발)
   · 제출 시도 (submit() 은 아님)  │
   · reset() 이 지운다            ┘

  제출 시도 ──> ① 도장을 전부 찍는다 ──> ② novalidate 가 아니면 검증 ──> 무효면 invalid 쏘고 멈춤
                                         ★ 서버는 ②를 모른다 (curl · fetch · 속성 지우기 · novalidate)
```

> **user validity** — `input`·`textarea`·`select` 마다 하나 있는 불리언. HTML 명세의 이름이다.\
> 예: 빈 `required` 칸을 두고 제출 단추를 누르면 **그 칸의 user validity 가 참**이 되고 `:user-invalid` 가 맞는다.

## 이 주제가 답하려는 질문

1. **`:invalid` 와 `:user-invalid` 는 정확히 언제 갈리나** — 무엇이 도장을 찍고 무엇이 지우나.
2. **`novalidate`·`formnovalidate` 는 무엇을 끄나** — 깃발인가, 검증 실행인가.
3. **클라이언트 검증을 건너는 길은 몇 개이고, 서버는 그것을 가를 수 있나.**

## 동작 방식

### (1) 창 ② — 칸 셋 × 의사 클래스 넷 × 시점 여섯

**언제 쓰나** — 「페이지가 뜨자마자 폼이 빨갛다」·「자동 채움 뒤에 빨간 줄이 안 나온다」·「비밀번호 칸을 그냥 지나쳤는데 빨갛다」를 가를 때.

세 칸은 **유효 여부를 시점 내내 바꾸지 않도록** 값을 골랐다 — 스크립트도 키 입력도 **같은 쪽의 값**을 넣는다(빈 칸은 `x` 를 쳤다가 지운다). 그래서 움직이는 것은 **도장뿐**이다. 시도마다 페이지를 새로 열었고, 칸 하나만 건드린다(`T5`·`T6` 은 제출 단추).

```html
<!-- html29b-29-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>29 의사 클래스와 시점</title>
<script src="html29b-rec.js"></script>
<script src="html29b-29-spec.js"></script>
</head>
<body>
<form id="f" action="/r" method="post">
  <input id="r" name="r" required>
  <input id="e" name="e" type="email" value="ab">
  <input id="ok" name="ok" required value="가">
  <button id="보냄">보냄</button>
</form>
<script>
addEventListener("change", e => 적기("change(" + e.target.id + ")"), true);
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 상태 = { r: "빈 required", e: "type=email 값 ab", ok: "required 값 가" };
const 의사 = [":valid", ":invalid", ":user-valid", ":user-invalid"];
// 칸의 유효 여부는 시점마다 그대로 둔다 — 스크립트·키 입력 모두 같은 쪽의 값을 넣는다
const 대입 = { r: "", e: "cd", ok: "나" };
const 키 = {
  r: id => [["type", "#" + id, "x"], ["keyhere", "Backspace", "Backspace", 8]],
  e: id => [["key", "#" + id, "End", "End", 35], ["type", "#" + id, "d"]],
  ok: id => [["key", "#" + id, "End", "End", 35], ["type", "#" + id, "다"]],
};
const 시점 = [
  ["T1", "로드 직후", id => []],
  ["T2", "스크립트 대입 뒤", id => [["js", "document.getElementById('" + id + "').value = " + JSON.stringify(대입[id]) + "; 1"]]],
  ["T3", "진짜 키 입력 뒤(포커스 중)", id => 키[id](id)],
  ["T4", "진짜 키 입력 → Tab", id => [...키[id](id), ["keyhere", "Tab", "Tab", 9]]],
  ["T5", "제출 단추 클릭 뒤", id => [["click", "#보냄"]]],
  ["T6", "제출 단추 클릭 → reset()", id => [["click", "#보냄"], ["js", "document.getElementById('f').reset(); 1"]]],
];
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [];
for (const [t, , 단계] of 시점) for (const id of Object.keys(상태)) {
  const e = "document.getElementById('" + id + "')";
  window.__시도.push({ 이름: t + " " + id, 단계: 단계(id),
    뒤: "JSON.stringify({ v: " + e + ".value, m: " + JSON.stringify(의사) + ".map(p => " + e + ".matches(p)) })" });
}
window.__종합 = 결과 => {
  const S = Object.fromEntries(결과.map(r => [r.이름, JSON.parse(r.뒤)]));
  const O = [(칸("칸 · 의사 클래스", 30) + 시점.map(([t]) => 칸(t, 5)).join("")).trimEnd()];
  let 갈림 = 0, 전체 = 0, 명세갈림 = 0, 명세전체 = 0;
  for (const id of Object.keys(상태)) {
    의사.forEach((p, k) => {
      let 행 = 칸(id + " " + p, 30);
      for (const [t] of 시점) {
        const 맞음 = S[t + " " + id].m[k];
        if (t !== "T1") { 전체++; 갈림 += 맞음 !== S["T1 " + id].m[k]; }
        명세전체++; 명세갈림 += 맞음 !== 명세맞음(id, t, p);
        행 += 칸(맞음 ? "예" : "·", 5);
      }
      O.push(행.trimEnd());
    });
  }
  O.push("");
  const 기록 = Object.fromEntries(결과.map(r => [r.이름, r.기록]));
  for (const [t, 설명] of 시점) O.push(t + " = " + 설명 + " · 값 " + Object.keys(상태).map(id => id + "=" + JSON.stringify(S[t + " " + id].v)).join(" ")
    + " · change 이벤트 " + Object.keys(상태).map(id => id + "=" + 기록[t + " " + id].filter(x => x.startsWith("change")).length).join(" "));
  O.push("로드 직후(T1)와 갈린 칸 = " + 갈림 + " / " + 전체);
  O.push("명세 열과 갈린 칸 = " + 명세갈림 + " / " + 명세전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

「명세 열」은 **따로 둔 파일**이다 — user validity 가 서는 문장 둘과 Selectors 4 의 「`:invalid` 인 것만」을 칸마다 적용한 것이다.

```javascript
// html29b-29-spec.js
// 명세 열 — HTML 의 user validity 가 참이 되는 자리 × Selectors 4 의 「:user-invalid 는 :invalid 인 것만 · :user-valid 는 :valid 인 것만」
// user validity 가 참이 되는 자리: ① 포커스를 떠날 때 값이 포커스 받을 때와 달라졌으면(focus update steps) ② 제출 시도(submit() 가 아닌 길)
// 거짓이 되는 자리: reset. 스크립트 대입과 포커스 중의 입력은 어느 쪽도 아니다.
const 명세유효 = { r: false, e: false, ok: true };
const 명세사용자 = (id, t) => t === "T5" || (t === "T4" && id !== "r");   // r 은 x 를 쳤다 지워 포커스 받을 때와 값이 같다
const 명세맞음 = (id, t, p) => {
  const v = 명세유효[id], u = 명세사용자(id, t);
  return { ":valid": v, ":invalid": !v, ":user-valid": u && v, ":user-invalid": u && !v }[p];
};
```

```text
$ python3 html29b-form.py 시도 html29b-29-grid.html | sed -n '/^칸 /,$p'
칸 · 의사 클래스              T1   T2   T3   T4   T5   T6
r :valid                      ·    ·    ·    ·    ·    ·
r :invalid                    예   예   예   예   예   예
r :user-valid                 ·    ·    ·    ·    ·    ·
r :user-invalid               ·    ·    ·    예   예   ·
e :valid                      ·    ·    ·    ·    ·    ·
e :invalid                    예   예   예   예   예   예
e :user-valid                 ·    ·    ·    ·    ·    ·
e :user-invalid               ·    ·    ·    예   예   ·
ok :valid                     예   예   예   예   예   예
ok :invalid                   ·    ·    ·    ·    ·    ·
ok :user-valid                ·    ·    ·    예   예   ·
ok :user-invalid              ·    ·    ·    ·    ·    ·

T1 = 로드 직후 · 값 r="" e="ab" ok="가" · change 이벤트 r=0 e=0 ok=0
T2 = 스크립트 대입 뒤 · 값 r="" e="cd" ok="나" · change 이벤트 r=0 e=0 ok=0
T3 = 진짜 키 입력 뒤(포커스 중) · 값 r="" e="abd" ok="가다" · change 이벤트 r=0 e=0 ok=0
T4 = 진짜 키 입력 → Tab · 값 r="" e="abd" ok="가다" · change 이벤트 r=0 e=1 ok=1
T5 = 제출 단추 클릭 뒤 · 값 r="" e="ab" ok="가" · change 이벤트 r=0 e=0 ok=0
T6 = 제출 단추 클릭 → reset() · 값 r="" e="ab" ok="가" · change 이벤트 r=0 e=0 ok=0
로드 직후(T1)와 갈린 칸 = 6 / 60
명세 열과 갈린 칸 = 1 / 72
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`:valid`/`:invalid` 는 여섯 시점 내내 같다** — 빈 `required` 칸(`r`)과 `ab` 인 이메일 칸(`e`)은 **로드 직후부터 `:invalid`** 다. 깃발은 **값이** 정하고, 명세의 `:invalid` 는 그 깃발을 읽을 뿐이다. [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md)의 (4) 가 본 「처음부터 빨간 폼」이 이것이다.
- ★★★ **`:user-*` 는 `T4`(키 입력 → Tab)와 `T5`(제출 단추 클릭)에서만 켜졌다** — 로드와 갈린 칸 **6 / 60** 이 전부 이 두 열의 `:user-*` 줄이다. `T2`(스크립트 대입)와 `T3`(포커스 중 입력)에서는 **안 켜졌다.** 명세의 **focus update steps** — 「포커스를 잃는 요소가 … 사용자가 포커스 중에 값을 바꿨고 **(처음 포커스 받을 때와 달라졌으면)** user validity 를 참으로 두고 `change` 를 쏜다」.
- ★★★ **제출 시도(`T5`)는 손대지 않은 칸 셋 모두에 도장을 찍었다** — `r`·`e` 는 `:user-invalid`, `ok` 는 **`:user-valid`**. 명세의 제출 알고리즘 — 「`submit()` 으로 부른 것이 아니면 **폼이 소유한 제출 가능 요소마다 user validity 를 참으로** 둔다」. 이 단계가 **검증보다 앞**이다((3) 의 `novalidate` 가 그 결과다).
- ★★ **`reset()` 이 도장을 지웠다**(`T6`) — 명세의 `input` 초기화 알고리즘 — 「user validity · 더러움 표시 … 를 **거짓으로** 되돌린다」.
- ★★★ **명세 열과 갈린 칸 1 / 72 — `r :user-invalid` 의 `T4`.** 빈 칸에 `x` 를 쳤다가 지우고 Tab 으로 떠났다. 값은 **처음 포커스 받을 때와 같은 `""`** 이고, **`change` 이벤트도 0 번**이다(`T4` 줄의 `r=0`). 그런데 Chrome 은 `:user-invalid` 를 켰다. 위 문장(「달라졌으면」)대로면 도장이 안 찍힌다. ★ **다만 이것을 이탈로 세지 않는다** — Selectors 4 는 「그 밖의 시점에도 **맞아도 된다(may)**」고 하고 「더 정확한 규칙은 호스트 언어가 정한다」고 넘기는데, **HTML 의 그 정의 절을 이 배치가 읽지 못했다.** 「**Chrome 의 방아쇠는 `change` 가 아니다**」까지가 이 판의 관찰이다.

```text
  같은 빈 required 칸 — 도장이 찍히는 길과 안 찍히는 길 (이 판)

  스크립트 .value = ""            도장 없음      :invalid
  포커스 → x → Backspace (머묾)     도장 없음      :invalid
  포커스 → x → Backspace → Tab     도장 ●        :invalid :user-invalid    ← change 0 번인데 켜졌다
  포커스만 → Tab                   도장 없음      :invalid                  ← (3) 의 한 줄
  제출 단추 클릭                   도장 ●        :invalid :user-invalid
  제출 뒤 reset()                  도장 지움      :invalid
```

### (2) 창 ⑤ — 검증을 건너는 다섯 시도

**언제 쓰나** — 「`required` 와 `type=email` 을 달았으니 서버는 검사 안 해도 된다」를 반증할 때.

두 폼은 **같은 무효 값**(「아무 글자」인 이메일 · `min=0` 에 `-5`)을 든다. `가` 는 검증을 켠 폼, `나` 는 `novalidate` 폼이다. 시도마다 **제출 직전에 깃발을 한 줄** 적는다.

```html
<!-- html29b-29-submit.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>29 검증을 건너는 길</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="가" action="/r" method="post">
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="가보냄">보냄</button>
  <button id="가건넘" formnovalidate>formnovalidate 단추</button>
</form>
<form id="나" action="/r" method="post" novalidate>
  <input type="email" name="addr" value="아무 글자" required>
  <input type="number" name="age" value="-5" min="0">
  <button id="나보냄">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 깃발 = id => "(() => { const f = document.getElementById('" + id + "'); 적기('깃발 addr.typeMismatch=' + f.addr.validity.typeMismatch + ' · age.rangeUnderflow=' + f.age.validity.rangeUnderflow + ' · form:invalid=' + f.matches(':invalid')); return 1; })()";
window.__표 = "종합";
window.__시도 = [
  { 이름: "가 · 보냄 클릭", 단계: [["js", 깃발("가")], ["click", "#가보냄"]] },
  { 이름: "가 · formnovalidate 단추 클릭", 단계: [["js", 깃발("가")], ["click", "#가건넘"]] },
  { 이름: "나(novalidate) · 보냄 클릭", 단계: [["js", 깃발("나")], ["click", "#나보냄"]] },
  { 이름: "가 · 속성을 지운 뒤 보냄 클릭", 단계: [["js", "(() => { const f = document.getElementById('가'); f.addr.removeAttribute('required'); f.addr.type = 'text'; f.age.removeAttribute('min'); return 1; })()"], ["js", 깃발("가")], ["click", "#가보냄"]] },
  { 이름: "가 · fetch(URLSearchParams(FormData(가)))", 단계: [["js", 깃발("가")], ["js", "fetch('/r', { method: 'POST', body: new URLSearchParams(new FormData(document.getElementById('가'))) }).then(r => { 적기('fetch 응답 ' + r.status); return 1; })"]] },
];
window.__종합 = 결과 => {
  const O = [칸("시도", 42) + 칸("submit", 8) + 칸("invalid", 9) + 칸("서버 요청", 10) + "서버가 받은 addr · age"];
  let 받음 = 0;
  for (const r of 결과) {
    const 필드 = r.서버.find(l => l.trim().startsWith("필드"));
    받음 += r.요청.length > 0;
    O.push(칸(r.이름, 42) + 칸(r.기록.some(x => x.startsWith("submit")) ? "났다" : "—", 8)
      + 칸(String(r.기록.filter(x => x.startsWith("invalid")).length) + "번", 9) + 칸(r.요청.length + "번", 10)
      + (필드 ? 필드.trim().replace(/^필드\s+/, "") : "(없음)"));
  }
  O.push("서버가 무효한 값을 받은 시도 = " + 받음 + " / " + 결과.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html29b-form.py 시도 html29b-29-submit.html | sed -n '1,/^$/p'
[가 · 보냄 클릭]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → click(가보냄 · detail=1) → invalid(addr) → invalid(age)
  서버    (받은 요청 없음)
[가 · formnovalidate 단추 클릭]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → click(가건넘 · detail=1) → submit(submitter=가건넘)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
[나(novalidate) · 보냄 클릭]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → click(나보냄 · detail=1) → submit(submitter=나보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
[가 · 속성을 지운 뒤 보냄 클릭]
  페이지  깃발 addr.typeMismatch=false · age.rangeUnderflow=false · form:invalid=false → click(가보냄 · detail=1) → submit(submitter=가보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」
[가 · fetch(URLSearchParams(FormData(가)))]
  페이지  깃발 addr.typeMismatch=true · age.rangeUnderflow=true · form:invalid=true → fetch 응답 200
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded;charset=UTF-8
          질의  (없음)
          본문  「addr=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90&age=-5」
          필드  addr=「아무 글자」 · age=「-5」

(exit 0)
```

```text
$ python3 html29b-form.py 시도 html29b-29-submit.html | sed -n '/^시도 /,$p'
시도                                      submit  invalid  서버 요청 서버가 받은 addr · age
가 · 보냄 클릭                            —      2번      0번       (없음)
가 · formnovalidate 단추 클릭             났다    0번      1번       addr=「아무 글자」 · age=「-5」
나(novalidate) · 보냄 클릭                났다    0번      1번       addr=「아무 글자」 · age=「-5」
가 · 속성을 지운 뒤 보냄 클릭             났다    0번      1번       addr=「아무 글자」 · age=「-5」
가 · fetch(URLSearchParams(FormData(가))) —      0번      1번       addr=「아무 글자」 · age=「-5」
서버가 무효한 값을 받은 시도 = 4 / 5
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **서버가 무효한 값을 받은 시도 4 / 5** — 검증을 켠 폼(`가`)의 **보냄 클릭**만 `invalid` 둘을 내고 멈췄다. 나머지 넷의 본문은 **한 글자도 같다**(`addr=%EC%95%84…&age=-5`). [21번](../21-form-submission-model/2-summary.md)의 (5) 가 `curl` 로 본 것과도 같다.
- ★★★ **`novalidate`·`formnovalidate` 는 깃발을 끄지 않는다** — 두 시도 모두 제출 직전 줄이 **`typeMismatch=true · rangeUnderflow=true · form:invalid=true`** 다. 명세의 제출 알고리즘 — 「**제출자 요소의 no-validate 상태**가 거짓이면 대화형으로 검증한다」. 끄는 것은 **검증을 돌리는 단계 하나**이고, **유효성 상태는 그대로다.** ★ `form:invalid` — 폼 요소도 `:invalid` 를 갖는다(자손 중 무효가 있으면).
- ★★★ **속성을 지우면 깃발 자체가 사라진다** — 페이지 안에서 `required`·`min` 을 지우고 `type` 을 `text` 로 바꾸니 **세 깃발이 전부 `false`** 가 되고 **클릭 제출이 통과**했다. 개발자 도구를 연 사용자는 **이것을 손으로 한다.**
- ★★ **`fetch` 는 검증을 부르지 않는다** — `submit` 도 `invalid` 도 없이 **요청 하나**가 갔다. 본문은 같고 **`Content-Type` 에 `;charset=UTF-8` 이 붙은 것만** 다르다(그 차이의 정본은 [web-api 30번](../../../../web-api/30-request-body-and-content-type/2-summary.md)).
- ★ 명세의 「Security」 절이 이 결과를 문장으로 적는다 — 「**서버는 클라이언트 쪽 검증에 기대면 안 된다.** 적대적인 사용자가 **일부러** 건너뛸 수 있고, 오래된 UA 나 **자동화 도구**가 **의도치 않게** 건너뛴다. 제약 검증 기능은 **사용자 경험**을 위한 것이지 **보안 장치가 아니다**」.

```text
  같은 무효 값 — 서버가 받은 것 (창 ⑤)

  검증 켠 폼 · 단추 클릭           invalid × 2 → 멈춤         서버 0
  검증 켠 폼 · formnovalidate 단추  깃발 그대로 → 제출         서버 1  addr=아무 글자 · age=-5
  novalidate 폼 · 단추 클릭         깃발 그대로 → 제출         서버 1  (같은 본문)
  속성을 지운 뒤 클릭               깃발 사라짐 → 제출         서버 1  (같은 본문)
  fetch                             검증 없음                  서버 1  (같은 본문 · charset 만 붙음)
  curl (21번 (5))                   브라우저 없음              서버 1  (같은 본문)
                                    ★ 서버 쪽에서 여섯 줄을 가를 칸이 없다
```

### (3) 창 ② — 스크립트로 묻는 검증이 제출·의사 클래스와 만나는 자리

**언제 쓰나** — 「`reportValidity()` 를 불렀는데 빨간 줄이 안 뜬다」·「`setCustomValidity` 를 한 번 부른 칸이 계속 제출을 막는다」를 가를 때. ★ **이 API 들 자체의 정본은 web-api 갈래 60번**이다.

```html
<!-- html29b-29-api.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>29 스크립트로 묻는 검증</title>
<script src="html29b-rec.js"></script>
</head>
<body>
<form id="다" action="/r" method="post">
  <input id="c1" name="c1" value="가">
  <input id="c2" name="c2" required>
  <input id="c3" name="c3" type="email" value="ab">
  <button id="다보냄">보냄</button>
</form>
<form id="라" action="/r" method="post" novalidate>
  <input id="d1" name="d1" required>
  <button id="라보냄">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
document.getElementById("라").addEventListener("submit", e => e.preventDefault());
const $ = "document.getElementById";
const 적어 = 식 => ["js", "(() => { 적기(" + 식 + "); return 1; })()"];
const 사용자 = "'user-invalid=' + (['c1','c2','c3','d1'].filter(id => document.getElementById(id).matches(':user-invalid')).join(',') || '(없음)') + ' · 포커스=' + (document.activeElement.id || document.activeElement.tagName)";
window.__표 = "종합";
window.__시도 = [
  { 이름: "다.checkValidity()", 단계: [적어("'반환 ' + " + $ + "('다').checkValidity()"), 적어(사용자)] },
  { 이름: "다.reportValidity()", 단계: [적어("'반환 ' + " + $ + "('다').reportValidity()"), 적어(사용자)] },
  { 이름: "라(novalidate · submit 을 막음) · 보냄 클릭", 단계: [["click", "#라보냄"], 적어(사용자)] },
  { 이름: "c2 에 포커스만 주고 Tab", 단계: [["js", $ + "('c2').focus(); 1"], ["keyhere", "Tab", "Tab", 9], 적어(사용자)] },
  { 이름: "c2·c3 을 채우고 c1.setCustomValidity('이유') · 보냄", 단계: [
    ["js", $ + "('c2').value = '나'; " + $ + "('c3').value = 'a@b.c'; " + $ + "('c1').setCustomValidity('이유'); 1"],
    적어("'c1.customError=' + " + $ + "('c1').validity.customError + ' · c1:invalid=' + " + $ + "('c1').matches(':invalid')"), ["click", "#다보냄"]] },
  { 이름: "같은 뒤 c1 을 진짜 키로 고치고 보냄", 단계: [
    ["js", $ + "('c2').value = '나'; " + $ + "('c3').value = 'a@b.c'; " + $ + "('c1').setCustomValidity('이유'); 1"],
    ["type", "#c1", "다"], 적어("'c1.value=' + " + $ + "('c1').value + ' · c1.customError=' + " + $ + "('c1').validity.customError"), ["click", "#다보냄"]] },
  { 이름: "같은 뒤 setCustomValidity('') · 보냄", 단계: [
    ["js", $ + "('c2').value = '나'; " + $ + "('c3').value = 'a@b.c'; " + $ + "('c1').setCustomValidity('이유'); " + $ + "('c1').setCustomValidity(''); 1"],
    적어("'c1.customError=' + " + $ + "('c1').validity.customError"), ["click", "#다보냄"]] },
];
window.__종합 = 결과 => {
  const O = [];
  for (const r of 결과) {
    O.push(r.이름);
    O.push("  페이지  " + r.기록.join(" → "));
    O.push("  서버    " + (r.요청.length ? r.요청.map(q => q.메서드 + " " + q.경로).join(", ") + " · " + r.서버.find(l => l.trim().startsWith("필드")).trim() : "(받은 요청 없음)"));
  }
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html29b-form.py 시도 html29b-29-api.html | sed -n '/^다.checkValidity/,$p'
다.checkValidity()
  페이지  invalid(c2) → invalid(c3) → 반환 false → user-invalid=(없음) · 포커스=BODY
  서버    (받은 요청 없음)
다.reportValidity()
  페이지  invalid(c2) → invalid(c3) → 반환 false → user-invalid=(없음) · 포커스=c2
  서버    (받은 요청 없음)
라(novalidate · submit 을 막음) · 보냄 클릭
  페이지  click(라보냄 · detail=1) → submit(submitter=라보냄) → user-invalid=d1 · 포커스=라보냄
  서버    (받은 요청 없음)
c2 에 포커스만 주고 Tab
  페이지  user-invalid=(없음) · 포커스=c3
  서버    (받은 요청 없음)
c2·c3 을 채우고 c1.setCustomValidity('이유') · 보냄
  페이지  c1.customError=true · c1:invalid=true → click(다보냄 · detail=1) → invalid(c1)
  서버    (받은 요청 없음)
같은 뒤 c1 을 진짜 키로 고치고 보냄
  페이지  c1.value=다가 · c1.customError=true → click(다보냄 · detail=1) → invalid(c1)
  서버    (받은 요청 없음)
같은 뒤 setCustomValidity('') · 보냄
  페이지  c1.customError=false → click(다보냄 · detail=1) → submit(submitter=다보냄)
  서버    POST /r · 필드  c1=「가」 · c2=「나」 · c3=「a@b.c」
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★ **`checkValidity()` 와 `reportValidity()` 는 둘 다 `invalid` 를 두 번 쏘고 `false` 를 돌려준다** — 갈린 것은 **포커스**다. `reportValidity()` 는 **첫 무효 칸(`c2`)으로 포커스를 옮겼고**, `checkValidity()` 는 `BODY` 그대로다. 명세 — `reportValidity` 는 「문제를 사용자에게 **알린다** … **포커스를 옮겨도 된다(may)**」, `checkValidity` 는 **이벤트만** 쏜다.
- ★★★ **둘 다 `:user-invalid` 를 켜지 않았다** — `user-invalid=(없음)`. 명세에서 도장을 찍는 문장은 **포커스 이동과 제출 시도**뿐이고, `reportValidity` 는 거기에 없다. **스크립트로 검증을 「보여 줘도」 CSS 는 모른다.**
- ★★★ **`novalidate` 폼의 제출 시도는 도장을 찍었다** — `submit` 을 막아 페이지에 머물게 하니 **손대지 않은 빈 `d1`** 이 `:user-invalid` 였다. (1) 의 문장 — 도장 찍기가 **no-validate 검사보다 앞**이다.
- ★ **포커스만 주고 Tab 으로 떠나면 도장이 없다** — 값을 안 바꿨기 때문이다. 「비밀번호 칸을 그냥 지나쳤다고 빨갛게 되지는 않는다」가 이 줄이다.
- ★★★ **`setCustomValidity('이유')` 는 값이 바뀌어도 풀리지 않는다** — 진짜 키로 `c1` 을 `다가` 로 고친 뒤에도 **`customError=true`** 이고 제출이 `invalid(c1)` 로 막혔다. **`setCustomValidity('')`** 를 부른 뒤에야 제출이 갔다. 명세 — 「사용자 정의 유효성 오류 메시지를 **그 값으로 둔다**」 · 빈 문자열이 아니면 custom error 다. **값이 바뀐다고 스스로 지워지는 문장은 없다.**

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 무엇을 끄나 · 켜나 |
|---|---|---|
| 폼 전체 검증을 건너기 | `<form novalidate>` | **검증 실행만** — 깃발·`:invalid` 는 그대로 |
| 이 단추로만 건너기 | `<button formnovalidate>` | 그 단추가 **제출자일 때만**(「임시 저장」 단추) |
| 손댄 뒤에만 오류 표시 | `input:user-invalid { … }` | 도장 **+** 무효 |
| 처음부터 오류 표시 | `input:invalid { … }` | 로드 직후부터 켜진다 |
| 스크립트 오류 걸기 · 풀기 | `el.setCustomValidity("이유")` · `el.setCustomValidity("")` | **빈 문자열로만** 풀린다 |

### 어디서 헷갈리나

- **`novalidate` 는 「검증을 끈다」가 아니라 「검증 단계를 건너뛴다」다** — 깃발은 선다.
- **`:user-invalid` 는 「blur 하면」이 아니라 「도장이 찍히면」이다** — 제출 시도도 찍는다.
- **`reportValidity()` 는 도장을 찍지 않는다** — CSS 쪽 표시는 따로다.
- **폼 요소도 `:invalid` 다** — 자손에 무효가 하나라도 있으면.

## 어디서 틀리나

### 1. 오류 표시를 `:invalid` 로 칠한다

**페이지가 뜨자마자 빨갛다**((1) — `T1` 에서 `r`·`e` 가 `:invalid`). `:user-invalid` 로 칠한다. [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md)의 「어디서 틀리나」 2 와 같은 자리다.

### 2. 「임시 저장」 단추를 위해 폼에 `novalidate` 를 단다

**「제출」 단추의 검증까지 꺼진다**((2) — `나` 는 어느 단추로 보내도 검증 없음). **그 단추에만 `formnovalidate`** 를 단다(`가건넘`).

### 3. `novalidate` 폼이니 `:user-invalid` 는 안 켜질 거라 여긴다

**켜진다**((3) — `d1`). 스크립트로 직접 검증하는 폼이면 **CSS 의 `:user-invalid` 규칙과 스크립트의 표시가 겹친다.**

### 4. `reportValidity()` 를 불렀으니 빨간 줄이 뜰 거라 여긴다

**안 뜬다**((3) — `user-invalid=(없음)`). 포커스와 풍선은 오지만 **도장은 안 찍힌다.**

### 5. `setCustomValidity` 를 입력 이벤트에서 한 번만 부른다

**값을 고쳐도 계속 막힌다**((3) — `c1.customError=true`). **값이 맞으면 `setCustomValidity('')`** 를 부르는 가지를 반드시 둔다.

### 6. 클라이언트 검증을 달았으니 서버 검증을 생략한다

**서버가 받은 본문으로는 다섯 길을 못 가른다**((2) — 4 / 5 · [21번](../21-form-submission-model/2-summary.md)의 `curl`). 명세의 「Security」 절 그대로다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | `input`·`textarea`·`select` 마다 **user validity** 불리언 · 처음은 거짓 | (1) |
| **명세(HTML)** | focus update steps — 포커스를 잃을 때 **처음과 값이 달라졌으면** user validity 를 참으로 + `change` | (1) |
| **명세(HTML)** | 제출 알고리즘 — `submit()` 이 아니면 **소유한 제출 가능 요소 전부**의 user validity 를 참으로 → **그다음에** no-validate 가 아니면 대화형 검증 | (1)·(3) |
| **명세(HTML)** | `reset` 이 user validity 를 거짓으로 | (1) |
| **명세(HTML)** | 「Security」 — 서버는 클라이언트 검증에 **기대면 안 된다** | (2) |
| **명세(HTML)** | `checkValidity` = 무효면 `invalid` · `reportValidity` = 그 위에 **알리기**(포커스는 may) · custom error = 메시지가 **빈 문자열이 아님** | (3) |
| **명세(Selectors 4)** | `:user-invalid` 는 **`:invalid` 인 것만** · 제출 시도 뒤에는 **맞아야 한다(must)** · 그 밖의 시점은 **맞아도 된다(may)** · 정확한 규칙은 호스트 언어 | (1) |
| **구현(Chrome)** | `reportValidity()` 가 **첫 무효 칸으로 포커스** · **값이 원래대로 돌아온 편집에도 도장**(`change` 0 번) | (1)·(3) |
| **이 판의 관찰** | 명세 열과 갈린 칸 **1 / 72** — 그 한 칸은 **HTML 의 의사 클래스 정의 절을 못 읽어** 이탈로 세지 않는다 | (1) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **검증 풍선** | 헤드리스에는 그 UI 가 없다 — `invalid` 이벤트와 포커스까지만 쟀다 |
| **HTML 의 `:user-valid`/`:user-invalid` 정의 문장** | 이 배치가 가진 명세 사본에 그 절(「Pseudo-classes」)이 없다 — **명세층이 비어 있는 자리**다 |
| **스크린리더가 `:user-invalid` 를 알리나** | 보조 기술이 없고 · 창 ⑦ 도 이 편은 안 쟀다 |
| **다른 엔진의 도장 시점** | 엔진이 하나다 — Selectors 4 가 `may` 로 열어 둔 자리라 **엔진마다 달라도 적합하다** |

## 언제 쓰고 언제 안 쓰나

- **오류 표시는 `:user-invalid`** — `:invalid` 는 「이 칸은 지금 무효다」를 **스크립트나 개발 중 점검**에 쓴다.
- **「검증 없이 보내는 단추」는 `formnovalidate`** — 폼 전체 `novalidate` 는 **검증을 전부 스크립트로 할 때만.**
- **`setCustomValidity` 는 「걸고 풀기」 한 쌍으로** — `input` 이벤트마다 **맞으면 `''`** 를 부른다.
- **서버는 언제나 다시 잰다** — 브라우저 검증은 **사용자가 빨리 고치게 돕는 것**이다.

## 핵심 문장

1. **`:valid`/`:invalid` 는 값이 정하고 로드 직후부터 맞는다 — `:user-*` 는 거기에 「사용자가 손댔다」 도장이 하나 더 있어야 맞는다.**
2. **도장은 포커스를 떠날 때(값이 달라졌으면)와 제출 시도 때 찍히고, `reset` 이 지운다 — 스크립트 대입·`reportValidity()` 는 찍지 않는다.**
3. **제출 시도는 검증보다 먼저 도장을 찍는다 — 그래서 `novalidate` 폼도 `:user-invalid` 가 켜진다.**
4. **`novalidate`·`formnovalidate` 는 검증 단계를 건너뛸 뿐 깃발을 끄지 않는다.**
5. **검증을 건너는 길(`formnovalidate`·`novalidate`·속성 지우기·`fetch`·`curl`)에서 서버가 받는 본문은 같다 — 서버는 가를 수 없다.**
6. **`setCustomValidity` 의 오류는 빈 문자열로 부를 때까지 남는다.**

## 관련 자료

- [28번 주제](../28-validation-attributes/2-summary.md) — ★ **속성이 어느 깃발을 켜나**의 정본(속성 × 타입 격자 · `maxlength` 는 사용자 편집일 때만). 여기는 그 깃발을 **CSS·제출에서 읽는** 쪽이다.
- [21번 주제](../21-form-submission-model/2-summary.md) — **검증이 언제 도나**((2) — `form.submit()` 은 건너뛴다)와 **`curl` 우회**((5))의 정본.
- [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) — `:invalid`·`:user-invalid` 의 **CSS 쪽 정본**(명시도·다른 상태 의사 클래스와의 관계). 그쪽은 이메일 칸 하나의 시점 넷, 여기는 **칸 셋 × 시점 여섯 + 제출·reset**.
- [web-api 30번](../../../../web-api/30-request-body-and-content-type/2-summary.md) — `fetch` 로 **같은 본문**을 만드는 쪽의 정본((2) 의 `charset` 차이).
- web-api 갈래 목록([`web-api/README.md`](../../../../web-api/README.md))의 **60번** — `checkValidity`·`reportValidity`·`setCustomValidity`·`ValidityState` 의 정본(폴더는 아직 없다). 여기는 **그 API 가 제출·의사 클래스와 만나는 자리**까지.
- [`security/`](../../../../security/README.md) — 이 저장소의 보안 묶음은 **해시·서명·토큰 프리미티브**라 **입력 검증을 다루는 편이 없다**(README 확인). 「서버가 다시 잰다」의 서버 쪽 설계는 이 목록 밖이다.
- [30번 주제](../30-form-state-and-input-hints/2-summary.md)(`disabled`·`readonly` 가 검증에서 빠지는 것) · [32번 주제](../32-button-type-and-form-owner/2-summary.md)(`formnovalidate` 를 단 단추가 **Enter 의 기본 단추**일 때).

## 용어 풀이

- **유효성 상태** — `validity` 의 깃발들. 값이 정한다.
- **user validity** — 요소마다 하나인 「사용자가 손댔다」 불리언. 포커스 이동(값이 달라졌을 때)·제출 시도가 참으로, `reset` 이 거짓으로.
- **정적 검증(statically validate)** — 무효한 칸마다 `invalid` 를 쏘고 목록을 돌려준다. `checkValidity` 가 이것.
- **대화형 검증(interactively validate)** — 정적 검증 + 사용자에게 알리기. 제출과 `reportValidity` 가 이것.
- **no-validate 상태** — 제출자 단추의 `formnovalidate`, 없으면 폼의 `novalidate`.
- **custom error** — `setCustomValidity` 로 건 메시지가 빈 문자열이 아닌 상태. `validity.customError`.
- **focus update steps** — 포커스가 옮겨 갈 때 도는 명세 알고리즘. 떠나는 칸의 `change` 와 도장이 여기서 난다.

## 더 들어가면

- **왜 제출 시도가 검증보다 먼저 도장을 찍나** — Selectors 4 가 「제출을 시도한 뒤에는 **반드시** 맞아야 한다」고 요구하므로, 검증이 멈추기 전에 도장이 있어야 멈춘 화면에 빨간 줄이 선다. `novalidate` 까지 찍히는 것은 **그 순서의 부수 효과**로 읽힌다(해석이다 — 명세의 비규범 설명은 이 사본에서 찾지 못했다).
- **`:user-invalid` 이전의 관례** — blur 때 `.touched` 클래스를 붙이던 패턴([CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md)의 「더 들어가면」).
- **`select` 의 도장** — 명세는 `select` 의 선택이 바뀌면 도장을 찍는 문장을 따로 둔다. 이 판은 `select` 를 던지지 않았다.
