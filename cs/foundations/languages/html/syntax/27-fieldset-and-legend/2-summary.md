# html/syntax/27 — `fieldset`/`legend` 와 그룹 비활성화 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The fieldset element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-fieldset-element)(★ `disabled` 가 **첫 `legend` 자식의 자손을 빼고** 퍼진다 · 「비활성 fieldset」의 정의), [「The legend element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-legend-element), [「Enabling and disabling form controls」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#enabling-and-disabling-form-controls:-the-disabled-attribute)(★ 「폼 컨트롤이 **disabled** 인 조건」 · 비활성 컨트롤은 사용자 상호작용 작업의 `click` 을 **디스패치하지 않는다**), [「Constructing the entry list」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-the-form-data-set), [`click()`](https://html.spec.whatwg.org/multipage/interaction.html#dom-click), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/) 의 「4.1.5 fieldset 의 이름 계산」·`fieldset`/`legend` 역할 줄. **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다.**
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 클릭은 **CDP 의 진짜 마우스**다. 하네스는 [25번 주제](../25-label-association/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. `fieldset[disabled]` 는 명세의 브라우저 지원 표에 「Chrome 20+」로 적힌 오래된 표면이다(이 문서는 그 시점을 재지 않았다).
> **선행** — [25번 주제](../25-label-association/2-summary.md)(칸 **하나**의 이름) · [24번 주제](../24-input-types-choice-special/2-summary.md)(`disabled` 는 안 실린다 · 라디오 그룹은 `name` 으로 묶인다).
> **경계** — **`disabled` 와 `readonly` 가 제출·포커스·검증에서 갈리는 세 지점**은 목록의 **30번 주제**다 — 여기는 **`fieldset` 이 그 `disabled` 를 어디까지 퍼뜨리나**와 **묶음의 이름**까지. 이름 출처 순서 전체는 목록의 **43번 주제**, `:disabled` 의사 클래스의 선택자 쪽 이야기는 [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md)이다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 한 표에 모은 네 창이다** — 칸마다 **창 ②**(`:disabled` 매치 · `focus()` 가 가나 · 진짜 클릭을 받나)와 **창 ⑤**(서버에 실리나)를 한 줄로 놓고 「**퍼진 칸 N / M**」을 스크립트가 센다. 묶음의 이름은 **창 ⑦** 이 맡는다.

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
| **고정했다** | 누른 자리 | 요소 한가운데 — 매번 새로 계산한다 |
| **안 흔들린다** | `:disabled` 매치 · 포커스 · 클릭을 받았나 · 실린 필드 · 「퍼진 칸 N / M」 | 같은 판이면 결정적이다 |
| **안 흔들린다** | 묶음의 역할·이름·`nameFrom` | 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **② 노드 프로브** | ★ **쓴다 — 본체** | `:disabled` 가 매치하나 · `focus()` 로 포커스가 가나 · 진짜 클릭이 요소에 `click` 을 주나((1)) |
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체의 한 열** | 퍼진 칸이 **안 실리나**((1)) |
| **⑦ 접근성 트리**(CDP + 내부 덤프) | ★ **쓴다** | `fieldset` 의 이름이 **`legend` 에서 오나** · 라디오 묶음의 역할((2)) |
| **① `--dump-dom`** | 쓴다(곁가지) | demo 검증 |
| **③ `innerText` 대 `textContent`** · **④ `compatMode`** · **⑥ `renderBlockingStatus`** | **부적용** | 무관하다 — 잴 것이 없다 |

- ★★ **제5의 상태 — 「포커스를 받을 수 있나」를 Tab 키가 아니라 `focus()` 로 물었다.** 칸마다 `focus()` 를 부르고 `document.activeElement` 가 그 칸인지 본다. ★ **바꾼 창이 못 보는 것** — **Tab 순서**(어느 칸 다음에 어느 칸이 오나)는 이 창이 답하지 않는다. 「포커스 가능한가」까지다.
- ★★ **18-A — 몇 군데 물었나.** 열네 칸 × 네 물음 중 **제출 칸이 성립하지 않는 셋**(제출 단추 — 제출자가 아니면 원래 안 실린다 · `a`·`span` — 폼 컨트롤이 아니다)의 「실림」을 **부적용**으로 빼서 **53 곳**을 물었다. 「퍼졌다」는 **그 53 곳 중 disabled 처럼 군 곳**이다.

## 한눈에 — 쉽게 말하면

**★ `fieldset[disabled]` 는 「공사 중 칸막이」다. 칸막이 안의 창구는 전부 닫는데, 칸막이에 붙은 첫 안내판(첫 `legend`)만은 열어 둔다.**

은행 창구 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **칸막이로 둘러친 창구들** | `fieldset` 과 그 안의 폼 컨트롤 |
| **칸막이 앞 안내판** | **첫 `legend` 자식** — 묶음의 **이름**이 된다 |
| **「공사 중」 팻말** | `disabled` — 안의 창구가 **전부** 닫힌다(칸마다 `disabled` 를 단 것처럼) |
| **안내판에 달린 창구** | 첫 `legend` 안의 칸 — ★ **닫히지 않는다** |
| **두 번째 안내판** | 둘째 `legend` — 그냥 칸막이 안의 물건이다 · 안의 칸은 **닫힌다** |
| **칸막이 안의 작은 칸막이** | 안쪽 `fieldset` — 바깥 팻말이 **그대로 내려온다** |
| **칸막이 안에 붙은 포스터·전단** | 링크·`tabindex` 요소 — 창구가 아니라서 **팻말과 무관** |
| **닫힌 창구의 서류** | 비활성 칸의 값 — **제출에 안 실린다** · 필수 칸이어도 **검사를 안 한다** |

- **팻말 하나로 칸 전부가 네 가지를 동시에 잃는다** — `:disabled` 매치 · 포커스 · 클릭 · 제출((1)).
- ★★ **첫 `legend` 안의 칸만 살아남는다** — 둘째 `legend`·안쪽 `fieldset` 의 `legend` 는 아니다((1)).
- ★ **`legend` 가 첫 자식이 아니어도 「첫 `legend` 자식」이면 된다**((1)·(2)).
- ★★ **`legend` 는 묶음의 이름이 된다** — 라디오 묶음에 「배송 방법」이라는 이름을 붙이는 형태가 이것이다((2)).

```text
  fieldset[disabled] 한 줄이 퍼지는 범위 — 명세 「A form control is disabled if …」

  <fieldset disabled>
    <legend> 첫 범례 <input lg1> </legend>          ← ● 살아남는다 (첫 legend 자식의 자손)
    <legend> 둘째 범례 <input lg2> </legend>        ← ✕ 닫힌다
    <input i1> <input rq required> <checkbox> <select> <textarea> <button>   ← ✕ 전부
    <fieldset>                                       ← 「비활성 fieldset」이 된다 (:disabled 매치)
      <legend> 안쪽 범례 <input lg3> </legend>      ← ✕ 닫힌다 (바깥의 첫 legend 가 아니다)
      <input i2>                                     ← ✕
    </fieldset>
    <a href> <span tabindex>                         ← ● 폼 컨트롤이 아니다
  </fieldset>
```

> **비활성 fieldset(disabled fieldset)** — `disabled` 속성이 있거나, **비활성 fieldset 의 자손이면서 그 첫 `legend` 자식 안에 있지 않은** `fieldset`. 안쪽 `fieldset` 이 속성 없이도 `:disabled` 에 매치하는 이유다.

> **첫 `legend` 자식** — `fieldset` 의 **자식**인 `legend` 중 트리 순서로 첫째. 손자(`div` 안의 `legend`)는 안 된다.

## 이 주제가 답하려는 질문

1. **`fieldset[disabled]` 는 무엇을 어디까지 끄나** — 어느 자손이 · 무엇(선택자·포커스·클릭·제출)을.
2. **무엇이 그 퍼짐에서 빠지나** — 첫 `legend` · 폼 컨트롤이 아닌 것.
3. **`legend` 는 어떻게 묶음의 이름이 되나** — 첫 자식이 아닐 때 · 둘일 때 · 자식이 아닐 때 · 라디오 묶음.

## 동작 방식

### (1) 창 ② + 창 ⑤ — 퍼짐 격자

**언제 쓰나** — 「결제 수단을 고르기 전에는 카드 칸 묶음을 끄고 싶다」처럼 **칸 여럿을 한 번에** 끌 때 · 끈 묶음 안에 **살려 둘 칸**이 있을 때.

한 폼에 비활성 `fieldset` 둘과 바깥 칸 하나를 두고, 칸마다 **진짜로 한 번씩 누른 뒤**(시도마다 새 페이지) 마지막에 **보냄**을 눌렀다. 표의 「명세」 열은 명세 문장으로 채운 **따로 둔 파일**이다.

```html
<!-- html25b-27-spread.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>27 비활성화가 퍼지는 곳</title>
<script src="html25b-rec.js"></script>
<script src="html25b-27-spec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post">
<fieldset id="바깥" disabled>
  <legend>첫 범례 <input name="lg1" id="lg1" value="첫 범례 안"></legend>
  <legend>둘째 범례 <input name="lg2" id="lg2" value="둘째 범례 안"></legend>
  <input name="i1" id="i1" value="입력">
  <input name="rq" id="rq" required>
  <input type="checkbox" name="c1" id="c1">
  <select name="s1" id="s1"><option>가</option></select>
  <textarea name="t1" id="t1">글</textarea>
  <button name="b1" id="b1" value="안쪽 단추">안쪽 단추</button>
  <fieldset id="안쪽">
    <legend>안쪽 범례 <input name="lg3" id="lg3" value="안쪽 범례 안"></legend>
    <input name="i2" id="i2" value="안쪽 입력">
  </fieldset>
  <a href="#x" id="a1">링크</a>
  <span tabindex="0" id="sp">tabindex 글자</span>
</fieldset>
<fieldset id="뒤범례" disabled>
  <div>앞 div</div>
  <legend>첫 자식 아닌 범례 <input name="lg4" id="lg4" value="첫 자식 아닌 범례 안"></legend>
</fieldset>
<input name="o1" id="o1" value="바깥 입력">
<button id="보냄" name="보냄" value="1">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// [표시, id, 제출 칸이 성립하나] — 명세 열은 html25b-27-spec.js 가 따로 든다
const 행 = [
  ["첫 legend 안의 input", "lg1", true],
  ["둘째 legend 안의 input", "lg2", true],
  ["input", "i1", true],
  ["required 인데 빈 input", "rq", true],
  ["checkbox", "c1", true],
  ["select", "s1", true],
  ["textarea", "t1", true],
  ["button (제출 단추)", "b1", false],
  ["안쪽 fieldset 의 legend 안 input", "lg3", true],
  ["안쪽 fieldset 의 input", "i2", true],
  ["a[href]", "a1", false],
  ["span[tabindex]", "sp", false],
  ["첫 자식이 아닌 첫 legend 안 input", "lg4", true],
  ["fieldset 밖 input", "o1", true],
];
window.__받음 = [];
document.getElementById("c1").checked = true;
for (const [, id] of 행) document.getElementById(id).addEventListener("click", e => { __받음.push(id); if (id === "a1" || id === "b1") e.preventDefault(); });
const 뒤 = id => "JSON.stringify({ 받음: __받음.includes('" + id + "'), 켜짐: document.getElementById('" + id + "').checked === true })";
window.__표 = "종합";
window.__시도 = [
  ...행.map(([이름, id]) => ({ 이름: "클릭 " + 이름, 단계: [["click", "#" + id]], 뒤: 뒤(id) })),
  { 이름: "보냄", 단계: [["click", "#보냄"]] },
];
window.__종합 = 결과 => {
  const 필드 = 결과[결과.length - 1].필드 || [];
  const O = [칸("칸", 34) + 칸(":disabled", 10) + 칸("focus()", 9) + 칸("클릭", 9) + 칸("실림", 9) + 칸("명세", 9) + "명세와"];
  let 퍼짐 = 0, 전체 = 0, 갈림 = 0;
  for (const [k, [이름, id, 제출]] of 행.entries()) {
    const 명세 = 명세상비활성[id];
    const e = document.getElementById(id);
    const 비활성 = e.matches(":disabled");
    e.focus(); const 포커스 = document.activeElement === e; e.blur();
    const r = JSON.parse(결과[k].뒤);
    const 클릭 = r.받음;
    const 실림 = 제출 ? 필드.includes(id) : null;
    const 막힘 = [비활성, !포커스, !클릭, 실림 === null ? null : !실림];
    const 셈 = 막힘.filter(x => x !== null);
    퍼짐 += 셈.filter(x => x).length; 전체 += 셈.length;
    const 같나 = 셈.every(x => x === 명세);
    if (!같나) 갈림++;
    O.push(칸(이름, 34) + 칸(비활성 ? "매치" : "—", 10) + 칸(포커스 ? "감" : "안 감", 9) + 칸(클릭 ? "받음" : "안 받음", 9)
      + 칸(실림 === null ? "(부적용)" : 실림 ? "실림" : "—", 9) + 칸(명세 ? "disabled" : "아님", 9) + (같나 ? "같다" : "★ 갈림"));
  }
  O.push("");
  O.push("fieldset 자신의 :disabled — 바깥=" + document.getElementById("바깥").matches(":disabled") + " · 안쪽=" + document.getElementById("안쪽").matches(":disabled") + " · 뒤범례=" + document.getElementById("뒤범례").matches(":disabled"));
  O.push("퍼진 칸 = " + 퍼짐 + " / " + 전체 + "  (disabled 처럼 군 칸 — :disabled 매치 · 포커스 안 감 · 클릭 안 받음 · 안 실림)");
  O.push("명세 열과 갈린 행 = " + 갈림 + " / " + 행.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```javascript
// html25b-27-spec.js
// 명세 열 — 「A form control is disabled if … a descendant of a fieldset element whose disabled attribute is
// specified, and the element is not a descendant of that fieldset element's first legend element child」로 채웠다.
// true = 명세상 disabled. a·span 은 폼 컨트롤이 아니라 false.
const 명세상비활성 = {
  lg1: false,
  lg2: true,
  i1: true,
  rq: true,
  c1: true,
  s1: true,
  t1: true,
  b1: true,
  lg3: true,
  i2: true,
  a1: false,
  sp: false,
  lg4: false,
  o1: false,
};
```

**보냄 — 서버가 받은 것**

```text
$ python3 html25b-form.py 시도 html25b-27-spread.html | sed -n '/^\[보냄\]$/,/^$/p'
[보냄]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「lg1=%EC%B2%AB+%EB%B2%94%EB%A1%80+%EC%95%88&lg4=%EC%B2%AB+%EC%9E%90%EC%8B%9D+%EC%95%84%EB%8B%8C+%EB%B2%94%EB%A1%80+%EC%95%88&o1=%EB%B0%94%EA%B9%A5+%EC%9E%85%EB%A0%A5&%EB%B3%B4%EB%83%84=1」
          필드  lg1=「첫 범례 안」 · lg4=「첫 자식 아닌 범례 안」 · o1=「바깥 입력」 · 보냄=「1」

(exit 0)
```

**격자**

```text
$ python3 html25b-form.py 시도 html25b-27-spread.html | sed -n '/^칸 /,$p'
칸                                :disabled focus()  클릭     실림     명세     명세와
첫 legend 안의 input              —        감       받음     실림     아님     같다
둘째 legend 안의 input            매치      안 감    안 받음  —       disabled 같다
input                             매치      안 감    안 받음  —       disabled 같다
required 인데 빈 input            매치      안 감    안 받음  —       disabled 같다
checkbox                          매치      안 감    안 받음  —       disabled 같다
select                            매치      안 감    안 받음  —       disabled 같다
textarea                          매치      안 감    안 받음  —       disabled 같다
button (제출 단추)                매치      안 감    안 받음  (부적용) disabled 같다
안쪽 fieldset 의 legend 안 input  매치      안 감    안 받음  —       disabled 같다
안쪽 fieldset 의 input            매치      안 감    안 받음  —       disabled 같다
a[href]                           —        감       받음     (부적용) 아님     같다
span[tabindex]                    —        감       받음     (부적용) 아님     같다
첫 자식이 아닌 첫 legend 안 input —        감       받음     실림     아님     같다
fieldset 밖 input                 —        감       받음     실림     아님     같다

fieldset 자신의 :disabled — 바깥=true · 안쪽=true · 뒤범례=true
퍼진 칸 = 35 / 53  (disabled 처럼 군 칸 — :disabled 매치 · 포커스 안 감 · 클릭 안 받음 · 안 실림)
명세 열과 갈린 행 = 0 / 14
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **퍼진 칸은 35 / 53** — 명세상 disabled 인 **열 줄은 물음 넷(부적용 빼고)이 전부 막혔고**, 아닌 **네 줄은 전부 살아 있다.** 반쯤 막힌 줄은 **하나도 없다** — `:disabled` · 포커스 · 클릭 · 제출은 **한 상태의 네 얼굴**이다. **명세 열과 갈린 행은 0 / 14.**
- ★★★ **첫 `legend` 안의 `lg1` 만 살았다** — `:disabled` 아님 · 포커스 감 · 클릭 받음 · **실림**(`lg1=「첫 범례 안」`). **둘째 `legend` 안의 `lg2` 는 닫혔다.** 명세 — 「`fieldset` 의 모든 폼 컨트롤 자손을 disabled 로 만든다 — **그 `fieldset` 의 첫 `legend` 자식의 자손은 빼고**」.
- ★★ **안쪽 `fieldset` 의 `legend` 안(`lg3`)도 닫혔다** — 그 `legend` 는 **안쪽** `fieldset` 의 첫 `legend` 이지 **바깥** 의 것이 아니다. 명세의 조건이 「**그** `fieldset` 의 첫 `legend` 자식」이다. 안쪽 `fieldset` 자신은 속성이 없는데 **`:disabled` 에 매치**했다(「fieldset 자신의 :disabled — 안쪽=true」) — 「비활성 fieldset」 정의의 둘째 줄이다.
- ★★ **첫 자식이 아닌 첫 `legend`(`lg4`)도 예외다** — `<div>` 뒤에 온 `legend` 인데 `lg4` 가 **살아서 실렸다.** 명세는 「첫 **자식**」이 아니라 「첫 **`legend` 자식**」을 말한다.
- ★★ **`a[href]`·`span[tabindex]` 는 아무것도 안 잃었다** — 포커스도 클릭도 된다. `disabled` 는 **폼 컨트롤**의 상태다. **링크를 끄려면 `fieldset` 으로는 안 된다.**
- ★★★ **`required` 인데 빈 `rq` 가 있는데도 제출됐다** — 서버가 요청을 받았다(「보냄」 블록). 비활성 칸은 **제약 검증에서 빠지기** 때문이다(명세의 「barred from constraint validation」 — [21번](../21-form-submission-model/2-summary.md)이 잰 「검증이 돌면 `invalid` 로 멈춘다」가 **여기서는 안 걸렸다**).
- ★ **진짜 클릭이 `click` 을 주지 않는다** — 명세 — 「disabled 인 폼 컨트롤은 **사용자 상호작용 작업 원천**에 들어온 `click` 이벤트가 그 요소에 **디스패치되지 않게** 해야 한다」. 스크립트의 `click()` 도 첫 줄이 「이 요소가 disabled 인 폼 컨트롤이면 **돌아간다**」다.
- **실린 칸** — 서버가 받은 필드는 **`lg1`·`lg4`·`o1`·`보냄`** 넷. 비활성 여덟 칸(`lg2`·`i1`·`rq`·`c1`·`s1`·`t1`·`lg3`·`i2`)은 **이름조차 없다**([24번](../24-input-types-choice-special/2-summary.md)의 「`disabled` 는 안 실린다」와 같은 거름망).

```text
  네 물음이 한 상태에서 나온다 — 줄마다 전부 막히거나 전부 산다

                               :disabled   focus()   클릭     실림
  lg2 · i1 · rq · c1 · s1 · t1    ✕          ✕        ✕        ✕     ← 열 줄 (b1 은 실림 부적용)
  lg3 · i2 · b1
  ───────────────────────────────────────────────────────────────
  lg1 (첫 legend)                 ●          ●        ●        ●
  lg4 (첫 자식 아닌 첫 legend)    ●          ●        ●        ●
  a[href] · span[tabindex]        ●          ●        ●      (부적용)
  o1 (fieldset 밖)                ●          ●        ●        ●

  ★ 반쯤 막힌 줄이 없다 — 퍼진 칸 35 / 53 은 「막힌 줄 × 물음 수」의 합이다
```

### (2) 창 ⑦ — `legend` 는 묶음의 이름이 된다

**언제 쓰나** — 라디오 그룹 「택배 / 방문」에 **질문 글**(「배송 방법」)을 붙일 때. 칸마다의 라벨(「택배」)만으로는 **무엇을 고르는지**가 안 전해진다.

```html
<!-- html25b-27-name.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>27 묶음의 이름</title>
</head>
<body>
<fieldset id="f1"><legend>배송 방법</legend><label><input type="radio" name="r1" id="r1"> 택배</label><label><input type="radio" name="r1"> 방문</label></fieldset>
<fieldset id="f2"><div>안내 글</div><legend>배송 방법</legend><label><input type="radio" name="r2"> 택배</label></fieldset>
<fieldset id="f3"><div><legend>배송 방법</legend></div><label><input type="radio" name="r3"> 택배</label></fieldset>
<fieldset id="f4"><legend>첫 범례</legend><legend>둘째 범례</legend><label><input type="radio" name="r4"> 택배</label></fieldset>
<fieldset id="f5" aria-label="에어리아 이름"><legend>배송 방법</legend><label><input type="radio" name="r5"> 택배</label></fieldset>
<fieldset id="f6" title="제목 이름"><label><input type="radio" name="r6"> 택배</label></fieldset>
<fieldset id="f7"><label><input type="radio" name="r7"> 택배</label></fieldset>
<div id="f8" role="radiogroup" aria-labelledby="h8"><span id="h8">배송 방법</span><label><input type="radio" name="r8"> 택배</label></div>
<div id="f9"><span>배송 방법</span><label><input type="radio" name="r9"> 택배</label></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 행 = [
  ["f1", "legend 가 첫 자식"], ["f2", "legend 앞에 div"], ["f3", "legend 가 div 안(자식 아님)"],
  ["f4", "legend 둘"], ["f5", "aria-label + legend"], ["f6", "title 만"], ["f7", "이름 없음"],
  ["f8", "div role=radiogroup + aria-labelledby"], ["f9", "그냥 div"],
];
window.__대상 = 행.map(([id]) => [id, "#" + id]);
window.__내부 = true;
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("무엇을", 38) + 칸("역할", 12) + 칸("이름", 18) + "nameFrom"];
  for (const [id, 무엇] of 행) {
    const a = __AX[id], n = __INT[id];
    O.push(칸(id, 4) + 칸(무엇, 38) + 칸(a.역할 || (a.무시 ? "(무시됨)" : "(없음)"), 12) + 칸(JSON.stringify(a.이름), 18) + ((n && n.속성.nameFrom) || "(없음)"));
  }
  const 이름있는묶음 = 행.filter(([id]) => __AX[id].이름 !== "").length;
  O.push("");
  O.push("이름이 있는 묶음 = " + 이름있는묶음 + " / " + 행.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html25b-form.py page html25b-27-name.html
id  무엇을                                역할        이름              nameFrom
f1  legend 가 첫 자식                     group       "배송 방법"       relatedElement
f2  legend 앞에 div                       group       "배송 방법"       relatedElement
f3  legend 가 div 안(자식 아님)           group       ""                (없음)
f4  legend 둘                             group       "첫 범례"         relatedElement
f5  aria-label + legend                   group       "에어리아 이름"   attribute
f6  title 만                              group       "제목 이름"       title
f7  이름 없음                             group       ""                (없음)
f8  div role=radiogroup + aria-labelledby radiogroup  "배송 방법"       relatedElement
f9  그냥 div                              generic     ""                (없음)

이름이 있는 묶음 = 6 / 9
(exit 0)
```

- ★★★ **첫 `legend` 자식이 `fieldset` 의 이름이다** — `f1` 은 역할 **`group`**, 이름 **`"배송 방법"`**, `nameFrom` = `relatedElement`. HTML-AAM 4.1.5 — 「`aria-*` 가 없으면 **`legend` 자식 중 첫째**의 서브트리를 쓴다」.
- ★★ **첫 자식이 아니어도 된다** — `f2`(`div` 뒤의 `legend`)도 `"배송 방법"`. **자식이 아니면 안 된다** — `f3`(`div` 안의 `legend`)은 `""`. **둘이면 첫째** — `f4` 는 `"첫 범례"`.
- ★ **`aria-label` 이 이기고, 없으면 `title`** — `f5` `"에어리아 이름"`(`attribute`) · `f6` `"제목 이름"`(`title`) · 아무것도 없으면 `f7` 처럼 `group` 인데 이름이 빈다.
- ★★ **`fieldset` 없이 같은 모양을 내려면 `role="radiogroup"` + `aria-labelledby`** — `f8` 은 `radiogroup` · `"배송 방법"`. **그냥 `div`(`f9`)는 `generic` 이고 이름이 없다** — 화면에서 「배송 방법」이 라디오 바로 위에 있어도 트리에서는 **묶음이 아니다.**
- **이름이 있는 묶음 = 6 / 9.**

```text
  「첫 legend 자식」 — 이름((2))과 비활성 예외((1))가 같은 것을 본다

  f1  fieldset ─┬─ legend "배송 방법"     ← 첫 legend 자식 ●  이름
                └─ label …
  f2  fieldset ─┬─ div
                ├─ legend "배송 방법"     ← 첫 자식은 아니지만 첫 legend 자식 ●   (1) 의 lg4 가 이 모양 — 예외 ●
                └─ label …
  f3  fieldset ─┬─ div ── legend          ← fieldset 의 자식이 아니다 ✕  이름 ""
                └─ label …
  f4  fieldset ─┬─ legend "첫 범례"       ← ●
                ├─ legend "둘째 범례"     ← ✕                                      (1) 의 lg2 가 닫힌 자리
                └─ label …
```

```text
  fieldset 의 이름 — HTML-AAM 4.1.5 (이 판의 f1 ~ f7)

  aria-labelledby / aria-label ──> 있으면 끝                        f5 "에어리아 이름"
  fieldset 의 자식 legend 중 첫째 ──> 그 서브트리                  f1 · f2(첫 자식 아님) · f4(첫째)
                                    (자식이 아니면 안 센다)          f3 ""
  title ──> 그 값                                                  f6 "제목 이름"
  없음 ──> ""                                                      f7 ""

  fieldset 이 아니면 — role=radiogroup + aria-labelledby 가 같은 모양   f8 radiogroup "배송 방법"
                       그냥 div 는 묶음이 아니다                         f9 generic ""
```

### demo — 칸막이 안에서 살아남는 칸

```html demo
<!-- html25b-27-demo.html -->
<fieldset disabled>
  <legend>범례 안 <input value="고칠 수 있다"></legend>
  <input value="못 고친다">
  <button type="button">못 누른다</button>
  <a href="#">링크는 그대로</a>
</fieldset>
<style>
  fieldset { display: grid; gap: 6px; max-width: 320px; }
</style>
```

> **보이는 것** — 칸막이 안의 입력·단추가 **흐리게** 그려지고 누를 수 없는데, **범례 안의 입력만 또렷하고 고칠 수 있다.** 링크는 평소처럼 누를 수 있다.\
> **바꿔 볼 것** — 범례 안의 입력을 `legend` 밖(칸막이 안)으로 옮겨 보라 — (1) 의 `lg1` 과 `i1` 이 갈리는 것이 그 한 자리다

*(Chrome 151 headless 실측, 창 폭 1000: 네 요소의 `:disabled` — 검증 파일은 아래)*

```html
<!-- html25b-27-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 27 검증</title>
<body>
<fieldset disabled>
  <legend>범례 안 <input value="고칠 수 있다"></legend>
  <input value="못 고친다">
  <button type="button">못 누른다</button>
  <a href="#">링크는 그대로</a>
</fieldset>
<style>
  fieldset { display: grid; gap: 6px; max-width: 320px; }
</style>
<script>
const O = [];
for (const e of document.querySelectorAll("fieldset input, fieldset button, fieldset a")) {
  O.push(e.tagName.toLowerCase().padEnd(7) + JSON.stringify(e.tagName === "INPUT" ? e.value : e.textContent) + " · :disabled=" + e.matches(":disabled"));
}
document.body.append(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ python3 html25b-form.py dom html25b-27-democheck.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
input  "고칠 수 있다" · :disabled=false
input  "못 고친다" · :disabled=true
button "못 누른다" · :disabled=true
a      "링크는 그대로" · :disabled=false
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 결과 |
|---|---|---|
| 칸 여럿을 한 번에 끄기 | `<fieldset disabled> … </fieldset>` | 안의 폼 컨트롤이 **전부** disabled |
| 끈 묶음 안에서 하나만 살리기 | 그 칸을 **첫 `legend`** 안에 | 살아남는다 |
| 라디오 묶음에 질문 글 | `<fieldset><legend>배송 방법</legend> 라디오들 </fieldset>` | 묶음 `group` · 이름 = `legend` |
| `fieldset` 없이 같은 것 | `<div role="radiogroup" aria-labelledby="h">` | 묶음 `radiogroup` · 이름 = 가리킨 글자 |

### 어디서 헷갈리나

- **`legend` 는 `fieldset` 의 자식이어야 한다** — `div` 로 한 번 감싸면 이름도 예외도 사라진다.
- **예외는 「첫 `legend`」 하나** — 둘째 `legend` 안의 칸은 닫힌다.
- **링크는 `disabled` 가 없다** — `fieldset` 이 못 끈다.
- **안쪽 `fieldset` 은 속성 없이도 `:disabled`** 다.

## 어디서 틀리나

### 1. 끈 묶음 안의 필수 칸이 제출을 막을 거라 여긴다

**안 막는다**((1) — `rq` 가 비었는데 서버가 요청을 받았다). 비활성 칸은 제약 검증에서 빠진다. **서버는 그 필드를 아예 못 받는다** — 「필수인데 비었다」가 아니라 「없다」로 처리해야 한다.

### 2. 묶음을 껐으니 안의 링크·단축 동작도 멈춘다고 여긴다

**`a[href]`·`tabindex` 요소는 그대로 동작한다**((1)). 끄려면 따로(`inert` 등 — 이 판은 재지 않았다).

### 3. 「이 묶음을 끄면 이 스위치도 꺼진다」가 싫어서 스위치를 `legend` 에 넣었는데, 둘째 `legend` 였다

**닫힌다**((1) 의 `lg2`). 예외는 **첫 `legend` 자식** 하나뿐이다.

### 4. 안쪽 `fieldset` 에 `legend` 를 두면 그 안의 칸은 바깥 `disabled` 를 피한다고 여긴다

**못 피한다**((1) 의 `lg3`). 안쪽 `fieldset` 자체가 비활성이 된다.

### 5. 라디오 위에 `<p>배송 방법</p>` 을 두면 묶음 이름이 된다고 여긴다

**안 된다**((2) 의 `f9` — `generic` · 이름 `""`). `fieldset` + `legend` 또는 `role="radiogroup"` + `aria-labelledby`.

### 6. 꾸미려고 `legend` 를 `div` 로 감싼다

**이름이 사라진다**((2) 의 `f3`). 예외도 사라진다(첫 `legend` **자식**이 아니므로).

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 폼 컨트롤이 disabled = 자기 `disabled` **또는** `disabled` 인 `fieldset` 의 자손이면서 **그 첫 `legend` 자식의 자손이 아닐 것** | (1) |
| **명세(HTML)** | 비활성 fieldset = `disabled` 속성 **또는** 비활성 fieldset 의 자손(그 첫 `legend` 밖) | (1) |
| **명세(HTML)** | 비활성 컨트롤은 사용자 상호작용 작업의 `click` 을 **디스패치하지 않는다** · `click()` 도 돌아간다 | (1) |
| **명세(HTML)** | 항목 목록 — disabled 인 필드는 **건너뛴다** · 비활성 컨트롤은 **제약 검증에서 제외** | (1) |
| **명세(HTML-AAM)** | `fieldset` → `group` · 이름 = `aria-*` → **첫 `legend` 자식** → `title` · `legend` 는 대응 역할 없음 | (2) |
| **구현(Chrome)** | 위 규칙 전부 · `focus()` 가 비활성 칸에 안 간다 | (1)·(2) |
| **이 판의 관찰** | **명세와 갈린 행 0 / 14** · 반쯤 막힌 줄 없음 | (1) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **스크린리더가 라디오 묶음에 들어갈 때 「배송 방법, 묶음」을 읽나** | 보조 기술이 없다 — 트리의 `group` 이름까지(**못 잰 것**). README 의 과녁(「라디오 그룹의 이름을 `legend` 로」)은 **그 입력까지** 증명한다 |
| **Tab 순서에서 비활성 칸을 건너뛰나** | 이 판은 `focus()` 로만 물었다(제5의 상태) — Tab 키 순회는 **안 돌려 본 것** |
| **비활성 칸이 흐리게 그려지는 모양** | 픽셀을 안 쟀다 — demo 로 사람이 본다 |
| **모바일 입력기에서 비활성 칸을 건너뛰는 「다음」 단추** | 입력기가 없다 |

## 언제 쓰고 언제 안 쓰나

- **칸 여럿을 조건부로 끌 때는 `fieldset[disabled]`** — 칸마다 `disabled` 를 다는 것보다 **한 줄**이다. 단 **끈 칸은 서버에 안 간다**는 것을 서버가 안다.
- **끈 묶음 안에 살려 둘 스위치는 첫 `legend` 안에** — 「이 묶음 사용」 체크박스가 전형이다.
- **라디오 묶음에는 `fieldset` + `legend`** — 질문 글이 묶음의 이름이 된다. 모양이 거슬리면 CSS 로 고치되 **`legend` 를 `div` 로 감싸지 않는다.**
- **보여만 주고 보낼 값이면 `disabled` 가 아니라 `readonly`**([24번](../24-input-types-choice-special/2-summary.md) · 목록의 **30번 주제**) — `fieldset` 은 `readonly` 를 퍼뜨리지 않는다(이 판은 재지 않았다 — 명세에 그런 문장이 없다).

## 핵심 문장

1. **`fieldset[disabled]` 는 안의 폼 컨트롤을 전부 disabled 로 만든다 — `:disabled` · 포커스 · 클릭 · 제출을 함께 잃는다.**
2. **예외는 첫 `legend` 자식 안의 칸 하나뿐이다 — 둘째 `legend`, 안쪽 `fieldset` 의 `legend` 는 아니다.**
3. **`legend` 가 첫 자식이 아니어도 「첫 `legend` 자식」이면 이름도 예외도 된다 — 자식이 아니면(감싸면) 둘 다 사라진다.**
4. **안쪽 `fieldset` 은 속성 없이도 비활성 fieldset 이 된다.**
5. **비활성 칸은 제약 검증에서 빠진다 — 끈 묶음 안의 필수 칸은 제출을 막지 않는다.**
6. **링크·`tabindex` 요소는 `fieldset` 이 못 끈다.**
7. **`legend` 는 `fieldset`(`group`)의 이름이 된다 — 라디오 묶음의 질문 글을 주는 형태다.**

## 관련 자료

- [24번 주제](../24-input-types-choice-special/2-summary.md) — `disabled` 칸이 안 실리는 거름망 · 라디오 그룹.
- [25번 주제](../25-label-association/2-summary.md) — 칸 **하나**의 이름(`label`). 여기는 칸 **묶음**의 이름.
- [21번 주제](../21-form-submission-model/2-summary.md) — 검증이 돌면 `invalid` 로 멈춘다. 여기는 **비활성 칸이 그 검증에서 빠지는 것**.
- [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) — `:disabled`·`:enabled` 의 선택자 쪽.
- 목록의 **30번 주제**(`disabled` 대 `readonly`) · **43번 주제**(이름 계산 순서 전체).

## 용어 풀이

- **비활성 fieldset** — `disabled` 가 있거나 비활성 fieldset 안(그 첫 `legend` 밖)에 있는 `fieldset`.
- **첫 `legend` 자식** — `fieldset` 의 자식 `legend` 중 첫째. 이름과 비활성 예외가 둘 다 이것을 본다.
- **폼 컨트롤이 disabled** — 자기 `disabled` 또는 비활성 `fieldset` 에서 내려온 상태. 네 얼굴(`:disabled`·포커스·클릭·제출)을 함께 잃는다.
- **제약 검증에서 제외(barred from constraint validation)** — 검증 대상에서 빠지는 것. 비활성 칸·`readonly`·`datalist` 안의 칸 등.
- **`group` 역할** — 관련 요소의 묶음. `fieldset`·`optgroup` 이 이것이다.
- **`radiogroup` 역할** — 라디오 묶음 전용 역할. `fieldset` 대신 `div` 에 붙인다.

## 더 들어가면

- **왜 첫 `legend` 를 예외로 두나** — 명세가 이유를 적지는 않는다. 쓰임새로 보면 **묶음을 다시 켜는 스위치**를 둘 자리가 필요하다 — 끈 묶음 안에 스위치가 있으면 **다시 켤 방법이 없다**(해석이다).
- **렌더된 `legend`** — 명세의 렌더링 절은 「`float` 도 절대 위치도 아닌 **첫 `legend` 자식**」을 테두리에 걸쳐 그린다. 이름·비활성 예외가 보는 「첫 `legend` 자식」과 **조건이 하나 더 많다** — 이 판은 떠 있는 `legend` 를 던지지 않았다.
