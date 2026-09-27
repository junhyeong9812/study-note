# html/syntax/33 — `output`·`progress`·`meter`: 계산 결과 / 진행 / 범위 안의 측정값 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The output element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-output-element)(★ **「요소의 값 자체는 폼을 제출할 때 제출되지 않는다」** · `for` 는 **순서 없는 고유 토큰 집합** · value/defaultValue 의 **default value override**), [「The progress element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-progress-element)(★ **`value` 가 없으면 불확정** · 「그냥 계기(gauge)에 `progress` 는 틀린 요소」), [「The meter element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-meter-element)(★ 여섯 점의 계산 순서 · **구역(region) 규칙** · 「UA 는 … 세 구역과의 관계를 **보여야 한다(should)**」), [Rendering 「The meter element」](https://html.spec.whatwg.org/multipage/rendering.html#the-meter-element-2)(「**플랫폼 관례**에 맞는 모양」 · 「원시 모양(primitive appearance)을 **자세히 적어야 한다**」는 명세 쪽 할 일 표시), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/) 의 요소 대응표(`output` → **status** · `progress` → **progressbar**(확정이면 valuemax·valuemin·valuenow) · `meter` → **meter**). **명세 본문은 앞 배치가 2026-09-26 에 받아 둔 사본**(`form-elements` · `rendering` · HTML-AAM)으로 읽었다 — 이 배치는 네트워크를 쓰지 않았다.\
> ★★ **WAI-ARIA 사본은 없다** — `status` 역할이 **암묵 `aria-live=polite`·`aria-atomic=true`** 를 갖는다는 정의는 ARIA 쪽 문장이라 이 배치가 **열지 못했다.** 그래서 (1) 격자의 「라이브」 열은 **명세 열을 비워 두고 세지 않는다**(판정 보류).
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 하네스는 [29번 주제](../29-constraint-validation/3-answer.md)의 `html29b-form.py`·`html29b-cdp.py`·`html29b-rec.js` 를 `html33b-` 로 복사한 것이고, 이 묶음이 **실행기 하나**(`html33b-run.py`)를 더했다 — 전문과 29번 판과의 차이는 [정답 파일](3-answer.md)의 `## 실행 검증` 에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 명세 사본의 지원 표는 `output` 을 **Chrome 10+**, `progress`·`meter` 를 **Chrome 6+** 로 적는다(이 배치는 따로 조회하지 않았다).
> **선행** — [25번 주제](../25-label-association/2-summary.md)(★ **`output`·`progress`·`meter` 는 셋 다 labelable** — 라벨의 `for` 로 이름을 받는다 · ★ **`output` 에도 `for` 가 있는데 뜻이 다르다** — (3)).
> **경계** — **암묵 역할 일반**(`button` 이 무료로 주는 것)은 목록의 **41번 주제** · **제약 검증 API** 는 [29번](../29-constraint-validation/2-summary.md) · **라벨이 이름을 주는 규칙**은 [25번](../25-label-association/2-summary.md) — 여기는 **세 요소의 의미가 갈리는 자리와 `output` 의 라이브 성질**까지.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑦(접근성 트리) + 창 ⑤(서버 요청 로그)의 「역할 격자」다** — 역할 · 라이브 속성 · 제출에 실리나 · `labels` 를 한 표로 묻는다. `meter` 의 구역은 **새 창 하나**(UA 그림자 트리의 `pseudo` + 계산된 색)로 묻는다.

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
| **안 흔들린다** | 접근성 노드의 역할·속성 · 서버가 받은 필드 · `labels.length` · `form.elements` · 그림자 트리의 `pseudo` 이름과 계산된 색 · 「갈린 칸 N / M」 | 탭마다 페이지를 새로 연다 · 같은 판이면 결정적이다 — 캡처 세 판이 한 글자도 같았다([정답](3-answer.md)의 재대조) |
| **안 흔들린다** | `meter` 의 접근성 값 `0.6000000238418579` | 속성 `0.6` 이 **32비트 부동소수**를 거쳐 나온 값이다 — 판마다 같다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑦ 접근성 트리** | ★ **쓴다 — 본체** | **역할** · `live`/`atomic` 속성 · 접근성 **값** · 트리가 든 **글자**((1)·(3)) |
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | `name` 을 단 세 요소가 **제출에 실리나**((1)) |
| **② 노드 프로브** | 쓴다 | `labels` · `form.elements` · `value`/`defaultValue` · `htmlFor` 의 **타입**((1)·(3)) |
| **UA 그림자 트리**(CDP `DOM.getDocument` 의 `pierce` + `CSS.getComputedStyleForNode`) | ★ **새로 세운다** | `meter` 가 **어느 구역**으로 그려지나 — 값 막대의 `pseudo` 이름과 **계산된 색**((2)) |
| **① · ③ · ④ · ⑥** | **부적용** | 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「구역」을 색으로 물었다.** 명세는 `meter` 가 **어떻게 보여야 하는지** 정하지 않는다(「보여야 한다(should)」 · 「플랫폼 관례」). 그래서 「Chrome 이 구역을 구별하나」를 **스크린샷 대신 그림자 트리 안 값 막대의 이름과 계산된 색**으로 물었다. ★ 이 창이 못 보는 것 — **실제로 칠해진 픽셀.** 계산값은 「무엇이 선언됐나」다((2)).
- ★★ **제5의 상태 — 「라이브 영역이 알렸나」를 트리의 속성으로 물었다.** 스크린 리더의 **발화**는 이 판이 **못 잰다.** CDP 가 보여 주는 것은 **노드의 `live` 속성**과 **바뀐 글자**까지다. 값을 바꾼 뒤 받은 `Accessibility.*` 이벤트는 **0 건**이고, 같은 탭을 다시 읽으면 **`loadComplete` 1 건**이 온다 — **듣는 쪽은 살아 있었다**((3) — 규칙 34 의 「오게 만든 판」).
- ★ **18-A — 몇 군데 물었나.** (1) 은 **다섯 요소 × 여섯 열 = 30 칸**(명세 열로 셀 수 있는 칸 **22** — 「이름」·「AX 범위」 두 열은 세지 않는다) · (2) 는 **`meter` 열 개** · (3) 은 **바꾸기 한 번 뒤의 이벤트 이름 전부**를 찍는다.

## 한눈에 — 쉽게 말하면

**★ `output` 은 「계산기 화면」, `progress` 는 「다운로드 막대」, `meter` 는 「주유계」다. 계산기 화면은 결과를 보여 줄 뿐 서류에 적혀 나가지 않고, 다운로드 막대는 끝을 모르면 「진행 중」만 보이며, 주유계는 눈금 위에 「적정 구간」을 따로 칠한다.**

자동차 계기판 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **계산기 화면** | **`output`** — 계산 결과 · **제출에 안 실림**(`name` 이 있어도) · 암묵 역할 **`status`** |
| **화면이 바뀌면 조용히 알려 주는 안내 방송** | `status` 역할의 **`live=polite` · `atomic=true`**((1)·(3)) |
| **다운로드 막대** | **`progress`** — 일의 **진행** · 역할 **`progressbar`** |
| **끝을 모르는 「진행 중」 막대** | **`value` 없는 `progress`** — 불확정 · 접근성 값이 **없다** |
| **주유계** | **`meter`** — 알려진 범위 안의 **측정값** · 역할 **`meter`** |
| **주유계의 적정·주의·위험 구간** | `low`·`high`·`optimum` 이 나누는 **세 구역** — Chrome 은 **색 셋**으로 가른다((2)) |

- **다섯 요소 · 명세 열로 셀 수 있는 22 칸이 전부 맞았다**(0 / 22) — `output` 은 `status` · 서버 필드에 **`i` 하나만** 왔다((1)).
- ★★ **`meter` 열 개의 구역이 명세 규칙과 전부 맞았고, 색은 세 가지였다**((2)).
- ★★ **`output.value = '4'` 뒤에 `defaultValue` 는 `"3"` 그대로, `form.reset()` 이 `"3"` 으로 되돌렸다** · `htmlFor` 는 **`DOMTokenList`** 다((3)).

```text
  세 요소 — 「이 숫자는 무엇인가」로 가른다

    무엇을 보여 주나                 요소        역할          제출
    ─────────────────────────────    ─────────   ───────────   ────
    계산·사용자 동작의 결과          output      status        ✕ (name 이 있어도)
    일이 얼마나 끝났나(진행)         progress    progressbar   ✕ (form 과 무관)
    알려진 범위 안의 측정값          meter       meter         ✕ (form 과 무관)

    「디스크 사용량」은 진행이 아니다 → meter      (명세 — progress 는 틀린 요소)
    「업로드 42%」는 측정값이 아니다   → progress  (명세 — meter 를 진행에 쓰지 마라)
```

> **라이브 영역(live region)** — 내용이 바뀌면 보조 기술이 **포커스를 옮기지 않고** 바뀐 것을 알려 주는 영역.\
> 예: `status` 역할(`output` 의 암묵 역할)은 `polite` — 사용자가 하던 말을 끝낸 뒤에 알린다.

## 이 주제가 답하려는 질문

1. **세 요소는 접근성 트리·제출·라벨에서 어디가 같고 어디가 갈리나** — 명세가 무엇을 정하나.
2. **`meter` 의 `low`/`high`/`optimum` 은 무엇을 바꾸나** — 명세는 구역을 정하고, 모양은 누가 정하나.
3. **`output` 의 값을 스크립트로 바꾸면 무엇이 바뀌나** — DOM 쪽 값 두 개 · 접근성 트리 · 라이브 알림 중 이 판이 볼 수 있는 것.

## 동작 방식

### (1) 창 ⑦ + 창 ⑤ + 창 ② — 다섯 요소 × 여덟 열

**언제 쓰나** — 「계산 결과 칸의 값이 서버에 안 온다」·「진행 막대를 스크린 리더가 뭐라고 읽나」·「라벨을 `meter` 에 달아도 되나」를 가를 때.

한 폼 안에 대조용 `input` 과 세 요소(`progress` 는 두 벌)를 두고, **전부에 `name` 과 `label` 을 달았다.** 제출은 `requestSubmit()` 이다. 「명세 열」은 **따로 둔 파일**이다.

```html
<!-- html33b-33-grid.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>33 세 요소</title>
<script src="html33b-rec.js"></script>
<script src="html33b-33-spec.js"></script>
</head>
<body>
<form id="f" action="/r" method="post">
  <label for="i">입력</label> <input id="i" name="i" value="1">
  <label for="o">결과</label> <output id="o" name="o" for="i">3</output>
  <label for="p1">진행</label> <progress id="p1" name="p1" value="30" max="100">30%</progress>
  <label for="p2">대기</label> <progress id="p2" name="p2" max="100"></progress>
  <label for="m1">측정</label> <meter id="m1" name="m1" value="0.6" low="0.3" high="0.7" optimum="0.9">60%</meter>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const 줄 = [["i", "input"], ["o", "output"], ["p1", "progress · value 있음"], ["p2", "progress · value 없음"], ["m1", "meter · low/high/optimum"]];
window.__대상 = 줄.map(([k]) => [k, "#" + k]);
window.__표 = "종합";
window.__뒤숨김 = true;
window.__시도 = [{ 이름: "requestSubmit()", 단계: [["js", "document.getElementById('f').requestSubmit(); 1"]] }];
window.__종합 = 결과 => {
  const 필드 = 결과[0].필드 || [];
  const f = document.getElementById("f");
  const 값 = k => {
    const a = __AX[k], e = document.getElementById(k);
    return {
      역할: a.역할,
      이름: JSON.stringify(a.이름),
      라이브: a.속성.live ? a.속성.live + " · atomic=" + a.속성.atomic : "—",
      제출: 필드.includes(e.getAttribute("name")) ? "실림" : "—",
      labels: String(e.labels.length),
      elements: [...f.elements].includes(e) ? "있음" : "—",
      AX값: a.값 === undefined || a.값 === null ? "—" : String(a.값),
      범위: a.속성.valuemin === undefined ? "—" : a.속성.valuemin + ".." + a.속성.valuemax,
    };
  };
  const 열 = ["역할", "라이브", "제출", "labels", "elements", "AX값"];
  const O = [칸("요소", 28) + 칸("역할", 13) + 칸("이름", 8) + 칸("라이브", 22) + 칸("제출", 6) + 칸("labels", 8) + 칸("elements", 10) + 칸("AX 값", 20) + "AX 범위"];
  let 갈림 = 0, 전체 = 0;
  for (const [k, 이름] of 줄) {
    const v = 값(k);
    O.push(칸(k + " " + 이름, 28) + 칸(v.역할, 13) + 칸(v.이름, 8) + 칸(v.라이브, 22) + 칸(v.제출, 6) + 칸(v.labels, 8) + 칸(v.elements, 10) + 칸(v.AX값, 20) + v.범위);
    for (const c of 열) if (명세[k][c] !== null) { 전체++; if (명세[k][c] !== v[c]) { 갈림++; O.push("  ↳ 명세 열과 갈림 — " + c + " : 명세 " + JSON.stringify(명세[k][c]) + " · 이 판 " + JSON.stringify(v[c])); } }
  }
  O.push("(라이브 = 접근성 노드의 live · atomic 속성 · 제출 = 서버가 받은 필드에 그 name 이 있나 · elements = form.elements 에 있나 · AX 범위 = valuemin..valuemax)");
  O.push("서버가 받은 필드 = " + (필드.join(",") || "(없음)"));
  O.push("명세 열과 갈린 칸 = " + 갈림 + " / " + 전체);
  return O.join("\n");
};
</script>
</body>
</html>
```

```javascript
// html33b-33-spec.js
// 명세 열 — 역할은 HTML-AAM 의 요소 대응표, 나머지는 HTML 의 요소 절 · null = 이 배치의 사본으로 판정할 수 없는 칸(세지 않는다)
// output: 「status role」 · 값은 「폼을 제출할 때 제출되지 않는다」 · listed · labelable
// progress: 「progressbar role, 확정이면 aria-valuemax = 최대값 · aria-valuenow = 현재값」 · form-associated 가 아니다(name 속성이 없다) · labelable
// meter: 「meter role」 · form-associated 가 아니다 · labelable
// live · atomic: WAI-ARIA 의 status 역할이 정한다 — 이 배치는 ARIA 사본이 없어 null
const 명세 = {
  i:  { 역할: "textbox",     라이브: null, 제출: "실림", labels: "1", elements: "있음", AX값: null },
  o:  { 역할: "status",      라이브: null, 제출: "—",   labels: "1", elements: "있음", AX값: null },
  p1: { 역할: "progressbar", 라이브: null, 제출: "—",   labels: "1", elements: "—",   AX값: "30" },
  p2: { 역할: "progressbar", 라이브: null, 제출: "—",   labels: "1", elements: "—",   AX값: "—" },
  m1: { 역할: "meter",       라이브: null, 제출: "—",   labels: "1", elements: "—",   AX값: null },
};
```

```text
$ python3 html33b-form.py 시도 html33b-33-grid.html
[requestSubmit()]
  페이지  submit(submitter=null)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「i=1」
          필드  i=「1」

요소                        역할         이름    라이브                제출  labels  elements  AX 값               AX 범위
i input                     textbox      "입력"  —                    실림  1       있음      1                   —
o output                    status       "결과"  polite · atomic=true  —    1       있음      —                  —
p1 progress · value 있음    progressbar  "진행"  —                    —    1       —        30                  0..100
p2 progress · value 없음    progressbar  "대기"  —                    —    1       —        —                  0..100
m1 meter · low/high/optimum meter        "측정"  —                    —    1       —        0.6000000238418579  0..1
(라이브 = 접근성 노드의 live · atomic 속성 · 제출 = 서버가 받은 필드에 그 name 이 있나 · elements = form.elements 에 있나 · AX 범위 = valuemin..valuemax)
서버가 받은 필드 = i
명세 열과 갈린 칸 = 0 / 22
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **명세 열과 갈린 칸 0 / 22** — 역할은 HTML-AAM 의 대응표 그대로(`status` · `progressbar` · `meter`), `labels` 는 **다섯 다 1**, `form.elements` 에는 **`input` 과 `output` 만** 있다.
- ★★★ **`output` 은 `name="o"` 가 있는데 서버에 안 왔다** — 서버가 받은 필드는 **`i` 하나**. 명세 — 「`output` 이 폼과 연결되는 것은 **폼 컨트롤의 이벤트 처리기에서 쉽게 가리키려는** 것이다. **요소의 값 자체는 제출되지 않는다.**」 ★ `form.elements` 에는 **있다**(명세 카테고리 — listed) — **목록에는 오르는데 제출되지 않는** 유일한 쪽이다.
- ★★ **`progress`·`meter` 에 단 `name` 은 아무것도 아니다** — 두 요소는 **폼 연관 요소가 아니라**(카테고리가 「labelable」 뿐) `form.elements` 에도 없고 제출에도 없다. 명세의 콘텐츠 속성 목록에 `name` 이 **없다.**
- ★★★ **라이브 속성은 `output` 에만 있다** — `live=polite · atomic=true`. `progress`·`meter` 는 **값이 바뀌어도 라이브 영역이 아니다.** ★ 이 열의 **명세 쪽은 판정 보류**다(WAI-ARIA 사본 없음 — 머리말).
- ★★ **접근성 값** — 확정 `progress` 는 **`30`**, 불확정 `progress` 는 **없음**(HTML-AAM — 「**확정이면** valuenow 를 현재 값으로」), `meter` 는 **`0.6000000238418579`**(32비트 부동소수를 거친 값 — 「흔들리는 칸」 표). `output` 에는 **접근성 값이 없다** — 그 글자는 **값이 아니라 자식 글자**다((3)).

```text
  같은 「숫자 하나」가 트리에서 갖는 모양 (이 판)

  output   status       live=polite atomic=true    값 ✕  글자 "3" (자식 StaticText)
  progress progressbar  범위 0..100                값 30  (value="30" max="100")
  progress progressbar  범위 0..100                값 ✕   ← value 가 없으면 「몇 %」가 없다
  meter    meter        범위 0..1                  값 0.6000000238418579
```

★ **불확정 `progress` 도 범위(`0..100`)는 낸다** — 값만 없다. HTML-AAM 의 문장은 「**확정이면** valuemax·valuemin·valuenow 를 둔다」이고, 불확정일 때 범위를 **빼라고는 하지 않는다** — 그래서 이 칸은 명세 열에 넣지 않았다.

### (2) UA 그림자 트리 — `meter` 열 개의 값 막대

**언제 쓰나** — 「`optimum` 을 줬는데 색이 안 바뀐다」·「높을수록 좋은 값과 낮을수록 좋은 값을 어떻게 가르나」를 볼 때.

`min=0 max=1 low=0.3 high=0.7` 에 `optimum` 을 **가운데(0.5) · 위(0.9) · 아래(0.1)** 로 두고 값을 **0.2 · 0.5 · 0.8** 로 바꿨다. 마지막 하나는 세 속성이 **없다.** 「명세 열」은 명세 절의 구역 규칙을 **그대로 옮긴** 함수다.

```html
<!-- html33b-33-meter.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>33 meter 의 구역</title>
<script src="html33b-33-meter-spec.js"></script>
</head>
<body>
<div id="자리"></div>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
// [id, value, optimum] — 전부 min=0 max=1 low=0.3 high=0.7 · 마지막 줄만 low/high/optimum 없음
const 줄 = [
  ["g1", 0.2, 0.5], ["g2", 0.5, 0.5], ["g3", 0.8, 0.5],
  ["h1", 0.2, 0.9], ["h2", 0.5, 0.9], ["h3", 0.8, 0.9],
  ["l1", 0.2, 0.1], ["l2", 0.5, 0.1], ["l3", 0.8, 0.1],
  ["n1", 0.5, null],
];
const 자리 = document.getElementById("자리");
for (const [k, v, o] of 줄) {
  const m = document.createElement("meter");
  m.id = k; m.setAttribute("value", v);
  if (o !== null) { m.setAttribute("low", "0.3"); m.setAttribute("high", "0.7"); m.setAttribute("optimum", o); }
  자리.append(m);
}
window.__속대상 = 줄.map(([k]) => k);
window.__끝 = () => {
  const O = [칸("meter", 30) + 칸("값 막대의 pseudo", 36) + 칸("background-color", 22) + "명세 열(구역)"];
  let 갈림 = 0;
  const 이름 = { "-webkit-meter-optimum-value": "최적", "-webkit-meter-suboptimum-value": "차선", "-webkit-meter-even-less-good-value": "더 나쁨" };
  const 색 = new Set();
  for (const [k, v, o] of 줄) {
    const 값막대 = __속[k].find(([p]) => p.endsWith("-value"));
    const 구역 = 이름[값막대[0]] || "(모름)";
    const 기대 = 명세구역(v, o);
    갈림 += 구역 !== 기대;
    색.add(값막대[1]);
    O.push(칸(k + " value=" + v + " · optimum=" + (o === null ? "(없음)" : o), 30) + 칸(값막대[0], 36) + 칸(값막대[1], 22) + 기대);
  }
  O.push("그림자 트리의 pseudo 전부(g1) = " + __속.g1.map(([p]) => p).join(" · "));
  O.push("값 막대 색의 가짓수 = " + 색.size);
  O.push("명세 열과 갈린 칸 = " + 갈림 + " / " + 줄.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```javascript
// html33b-33-meter-spec.js
// 명세 열 — HTML 의 meter 절 「UA requirements for regions of the gauge」를 그대로 옮겼다(min 0 · max 1)
// low 가 없으면 최소값, high 가 없으면 최대값, optimum 이 없으면 최소·최대의 가운데
// 최적점이 low~high 사이면 그 사이가 최적 구역, 바깥 둘은 차선
// 최적점이 low 보다 작으면 최소~low 가 최적, low~high 가 차선, 나머지가 더 나쁨 (high 보다 크면 거꾸로)
function 명세구역(value, optimum) {
  const low = optimum === null ? 0 : 0.3, high = optimum === null ? 1 : 0.7;
  const opt = optimum === null ? 0.5 : optimum;
  if (opt >= low && opt <= high) return value >= low && value <= high ? "최적" : "차선";
  const 가까운 = opt < low ? value <= low : value >= high;
  if (가까운) return "최적";
  return value >= low && value <= high ? "차선" : "더 나쁨";
}
```

```text
$ python3 html33b-run.py 속 html33b-33-meter.html
meter                         값 막대의 pseudo                    background-color      명세 열(구역)
g1 value=0.2 · optimum=0.5    -webkit-meter-suboptimum-value      rgb(255, 185, 0)      차선
g2 value=0.5 · optimum=0.5    -webkit-meter-optimum-value         rgb(16, 124, 16)      최적
g3 value=0.8 · optimum=0.5    -webkit-meter-suboptimum-value      rgb(255, 185, 0)      차선
h1 value=0.2 · optimum=0.9    -webkit-meter-even-less-good-value  rgb(216, 59, 1)       더 나쁨
h2 value=0.5 · optimum=0.9    -webkit-meter-suboptimum-value      rgb(255, 185, 0)      차선
h3 value=0.8 · optimum=0.9    -webkit-meter-optimum-value         rgb(16, 124, 16)      최적
l1 value=0.2 · optimum=0.1    -webkit-meter-optimum-value         rgb(16, 124, 16)      최적
l2 value=0.5 · optimum=0.1    -webkit-meter-suboptimum-value      rgb(255, 185, 0)      차선
l3 value=0.8 · optimum=0.1    -webkit-meter-even-less-good-value  rgb(216, 59, 1)       더 나쁨
n1 value=0.5 · optimum=(없음) -webkit-meter-optimum-value         rgb(16, 124, 16)      최적
그림자 트리의 pseudo 전부(g1) = -webkit-meter-inner-element · -webkit-meter-bar · -webkit-meter-suboptimum-value
값 막대 색의 가짓수 = 3
명세 열과 갈린 칸 = 0 / 10
(exit 0)
```

- ★★★ **명세 열과 갈린 칸 0 / 10** — Chrome 은 값 막대 요소의 `pseudo` 를 **세 이름**(`-webkit-meter-optimum-value` · `-suboptimum-value` · `-even-less-good-value`)으로 바꿔 끼우고, 그것이 명세의 **최적 · 차선 · 더 나쁨**과 칸마다 맞았다.
- ★★★ **`optimum` 하나가 같은 값의 뜻을 뒤집는다** — 값 `0.8` 은 `optimum=0.9` 이면 **최적**, `0.1` 이면 **더 나쁨**, `0.5` 이면 **차선**이다. 명세 — 「최적점이 `high` 보다 크면 **`high`\~최댓값이 최적 구역**, `low`\~`high` 가 차선, 나머지가 더 나쁨」(낮으면 거꾸로 · 사이면 `low`\~`high` 가 최적이고 **바깥 둘은 차선**).
- ★★ **세 속성이 없으면 전부 최적이다**(`n1`) — `low` 는 최솟값, `high` 는 최댓값, `optimum` 은 가운데가 되어 **범위 전체가 최적 구역**이 된다.
- ★★★ **색은 세 가지**(`rgb(16, 124, 16)` · `rgb(255, 185, 0)` · `rgb(216, 59, 1)`) — ★ **이것은 명세가 아니다.** 명세는 「UA 는 값과 **세 구역의 관계를 보여야 한다(should)**」 · 렌더링 절은 「**플랫폼 관례**에 맞는 모양」이라고만 적고, 원시 모양은 「**자세히 적어야 한다**」는 **명세 쪽 할 일 표시**로 남아 있다. **초록·노랑·주황은 Chrome 의 선택**이다.
- ★ **이 창이 못 보는 것** — 값 막대가 **실제로 그 색으로 칠해졌나**(픽셀). 계산된 `background-color` 는 「그 요소에 무엇이 선언됐나」이고, `appearance: auto` 가 테마로 그리는 판이면 **계산값과 화면이 다를 수 있다**(CSS 갈래의 「계산값 ≠ 사용값」). 이 판은 **스크린샷을 찍지 않았다.**

```text
  optimum 이 정하는 「좋은 쪽」 (min 0 · low 0.3 · high 0.7 · max 1)

  0 ────── 0.3 ────────────── 0.7 ────── 1
  │  아래   │       가운데        │   위    │
  optimum 0.5 (가운데) :  차선  │       최적        │  차선
  optimum 0.9 (위)     : 더나쁨 │       차선        │  최적
  optimum 0.1 (아래)   :  최적  │       차선        │ 더나쁨
  (세 속성 없음)       :  ──────────── 전부 최적 ──────────────
```

### (3) 창 ② + 창 ⑦ — `output` 의 값을 바꾸고 되돌리기

**언제 쓰나** — 「계산 결과를 스크립트로 넣었는데 `reset` 하니 이상한 값으로 돌아간다」·「스크린 리더가 결과를 읽어 주나」를 가를 때.

`a + b = output` 계산기를 두고, **값을 `'4'` 로 바꾸고**(`output.value`) → 두 틀을 기다리고 → **`form.reset()`** 했다. 대조로 **보통 문단**(`p`)의 글자도 같이 바꿨다. 창 ⑦ 은 **바꾸기 전과 뒤**에 트리를 받고, 그 사이에 온 CDP `Accessibility.*` 이벤트를 **전부 센다.**

```html
<!-- html33b-33-live.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>33 output 의 값 바꾸기</title>
</head>
<body>
<form id="f">
  <input id="a" type="number" value="2"> + <input id="b" type="number" value="1"> =
  <output id="o" for="a b">3</output>
</form>
<p id="보통">3</p>
<script>
const 두틀 = () => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
const o = document.getElementById("o"), f = document.getElementById("f");
const 줄 = [];
const 찍기 = 때 => 줄.push(때 + " — value=" + JSON.stringify(o.value) + " · defaultValue=" + JSON.stringify(o.defaultValue) + " · textContent=" + JSON.stringify(o.textContent));
window.__대상 = [["o", "#o"], ["보통", "#보통"]];
window.__바꾸기 = async () => {
  찍기("처음");
  o.value = "4";
  document.getElementById("보통").textContent = "4";
  await 두틀();
  찍기("o.value = '4' 뒤");
  return 1;
};
window.__끝 = () => {
  const 글자 = x => x.역할 + " · 글자=" + JSON.stringify(x.글자) + " · live=" + (x.속성.live || "—");
  const O = ["[창 ②]", ...줄.map(s => "  " + s)];
  f.reset();
  찍기("form.reset() 뒤");
  O.push("  " + 줄[줄.length - 1]);
  O.push("  htmlFor = " + Object.prototype.toString.call(o.htmlFor) + " · " + JSON.stringify([...o.htmlFor]) + " · 길이 " + o.htmlFor.length);
  O.push("[창 ⑦ 전] output = " + 글자(__AX전.o) + "  |  p = " + 글자(__AX전.보통));
  O.push("[창 ⑦ 뒤] output = " + 글자(__AX뒤.o) + "  |  p = " + 글자(__AX뒤.보통));
  const 이름 = Object.keys(__이벤트);
  O.push("바꾼 뒤 받은 Accessibility.* 이벤트 = " + (이름.length ? 이름.map(k => k + " " + __이벤트[k]).join(" · ") : "0 건"));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html33b-run.py 라이브 html33b-33-live.html
[창 ②]
  처음 — value="3" · defaultValue="3" · textContent="3"
  o.value = '4' 뒤 — value="4" · defaultValue="3" · textContent="4"
  form.reset() 뒤 — value="3" · defaultValue="3" · textContent="3"
  htmlFor = [object DOMTokenList] · ["a","b"] · 길이 2
[창 ⑦ 전] output = status · 글자="3" · live=polite  |  p = paragraph · 글자="3" · live=—
[창 ⑦ 뒤] output = status · 글자="4" · live=polite  |  p = paragraph · 글자="4" · live=—
바꾼 뒤 받은 Accessibility.* 이벤트 = 0 건
대조 — 같은 탭을 다시 읽은 뒤 받은 Accessibility.* 이벤트 = Accessibility.loadComplete 1
(exit 0)
```

- ★★★ **`value` 를 바꿔도 `defaultValue` 는 `"3"`** 이고, **`form.reset()` 이 `"3"` 으로 되돌렸다.** 명세 — `value` 의 setter 는 「**default value override 를 지금의 기본값으로 둔 뒤**(처음 한 번 — `"3"` 이 붙잡힌다) 글자를 바꾼다」 · reset 은 「**기본값으로 글자를 바꾸고 override 를 비운다**」. 스크립트가 처음 넣은 값이 아니라 **마크업에 있던 글자**가 기본값이다.
- ★★ **`htmlFor` 는 `DOMTokenList`** 다(`["a","b"]` · 길이 2). **`label` 의 `htmlFor` 는 문자열**이다([25번](../25-label-association/2-summary.md)) — `label[for]` 는 **이름을 줄 칸 하나**를 가리키고, `output[for]` 는 **계산에 들어간 칸들**을 가리킨다. 명세 — 「공백으로 가른 **순서 없는 고유 토큰 집합**, 각각이 같은 트리의 ID」.
- ★★★ **트리의 글자는 `"3"` → `"4"` 로 바뀌었다** — `output` 도 보통 `p` 도 똑같이. 갈린 것은 **`output` 노드에만 `live=polite` 가 있다**는 것 하나다.
- ★★★ **바꾼 뒤 받은 `Accessibility.*` 이벤트는 0 건**이다 — 그리고 **같은 탭을 다시 읽으면 `loadComplete` 1 건**이 왔다(듣는 쪽이 살아 있다는 대조). ★ **이 0 은 「라이브 알림이 안 났다」가 아니다** — CDP 의 `Accessibility` 도메인은 **라이브 영역 알림을 이벤트로 내보내는 창이 아니다.** 플랫폼 접근성 API 로 가는 알림과 스크린 리더의 발화는 **이 판이 못 잰 것**이다.

```text
  「결과가 바뀌었다」가 어디까지 보이나 (이 판)

  output.value = '4'
     │
     ├─ 창 ②  textContent "4" · defaultValue "3"      ← 보인다
     ├─ 창 ⑦  status 노드 · live=polite · 글자 "4"     ← 보인다 (p 도 글자는 바뀐다)
     ├─ CDP Accessibility.* 이벤트        0 건          ← 이 창에는 알림이 안 실린다
     └─ 스크린 리더가 「4」라고 말하나     ?            ← 못 잰 것
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 계산 결과 | `<output for="a b" name="o">3</output>` | `status` · **제출 ✕** · `form.elements` 에는 있다 |
| 확정 진행 | `<progress value="30" max="100">30%</progress>` | `progressbar` · 값 30 |
| 불확정 진행 | `<progress max="100"></progress>` | `progressbar` · **값 없음** |
| 측정값 | `<meter value="0.6" low="0.3" high="0.7" optimum="0.9">` | `meter` · 구역이 색으로 갈린다 |

### 어디서 헷갈리나

- **`output` 의 `for` 는 라벨의 `for` 가 아니다** — 이름을 주지 않는다. 이름은 **`label for="o"`** 가 준다((1) — `labels` 1).
- **`progress`·`meter` 에는 `name` 도 `form` 도 없다** — 폼 연관 요소가 아니다.
- **`meter` 의 기본 범위는 0\~1** 이다 — `max` 를 안 쓰고 `value="12"` 를 주면 **꽉 찬 계기**가 된다(명세의 「BAD!」 예).
- **`progress` 에 `value="0"` 을 두면 불확정이 아니다** — 불확정은 **속성이 없을 때만**이다.

## 어디서 틀리나

### 1. 계산 결과를 `output` 에 두고 서버가 받을 거라 여긴다

**안 간다**((1) — 서버 필드 `i` 하나). 보내야 하면 **`input type=hidden`** 에 같은 값을 넣는다.

### 2. 디스크 사용량·점수를 `progress` 로 그린다

명세가 「**그냥 계기에 `progress` 는 틀린 요소**」라고 직접 적는다. 트리에서도 **`progressbar`** 로 읽힌다((1)) — 「일이 진행 중」이라는 뜻이 된다. `meter` 를 쓴다.

### 3. 업로드 진행률을 `meter` 로 그린다

거꾸로다 — 명세 — 「`meter` 를 **진행을 나타내는 데 쓰면 안 된다**」.

### 4. `optimum` 을 빼먹고 「높을수록 나쁨」을 기대한다

세 속성이 없으면 **범위 전체가 최적**이다((2) — `n1`). 「높을수록 나쁨」이면 **`optimum` 을 `low` 아래**에 둔다.

### 5. `output.value` 로 넣은 값을 reset 의 기준값이라 여긴다

**마크업 글자로 돌아간다**((3) — `"3"`). 기본값을 바꾸려면 **`defaultValue`** 에 넣는다.

### 6. 「`output` 을 쓰면 스크린 리더가 결과를 읽어 준다」를 확인했다고 여긴다

이 판이 본 것은 **`live=polite` 속성**까지다((3)). 발화는 **실기기 스크린 리더**로 확인한다.

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | `output` 의 값은 **제출되지 않는다** · listed · labelable · `for` 는 토큰 집합 · value/defaultValue/reset 의 override 규칙 | (1)·(3) |
| **명세(HTML)** | `progress` — `value` 가 없으면 **불확정** · 계기에 쓰면 **틀린 요소** · `progress`·`meter` 는 폼 연관이 아니다 | (1) |
| **명세(HTML)** | `meter` — 여섯 점의 계산 · **구역 규칙** · 보여 주기는 **should** · 모양은 「플랫폼 관례」 | (2) |
| **명세(HTML-AAM)** | `output` → status · `progress` → progressbar(확정이면 valuenow) · `meter` → meter | (1) |
| **명세(WAI-ARIA)** | `status` 의 암묵 `live`·`atomic` — **이 배치는 사본이 없다(판정 보류)** | (1) |
| **구현(Chrome)** | 구역을 **`pseudo` 셋 · 색 셋**으로 그린다 · `meter` 의 접근성 값을 **32비트 부동소수**로 낸다 · 불확정 `progress` 에도 범위를 낸다 | (1)·(2) |
| **이 판의 관찰** | 명세 열과 갈린 칸 **0 / 22 · 0 / 10** · 바꾼 뒤 `Accessibility.*` 이벤트 0 건(대조: 다시 읽기 1 건) | (1)\~(3) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **스크린 리더가 `output` 의 새 값을 말하나** | 플랫폼 접근성 API 로 가는 알림은 CDP `Accessibility` 도메인에 안 실린다 — **실기기 보조 기술**이 필요하다 |
| ★★ **`meter` 가 실제로 그 색으로 칠해졌나** | 스크린샷을 안 찍었다 — 계산값은 **선언**이다((2)) |
| **불확정 `progress` 의 움직이는 모양** | 애니메이션은 이 판의 창에 안 잡힌다 |

## 언제 쓰고 언제 안 쓰나

- **`output`** — **페이지 안에서 계산한 결과**(합계·환산). 서버에 보낼 값이면 `hidden` 과 **짝으로.**
- **`progress`** — **끝이 있는 일의 진행**. 끝을 모르면 `value` 를 **빼서** 불확정으로.
- **`meter`** — **범위가 알려진 측정값**(용량·점수·배터리). 범위를 모르는 값(몸무게·키)에는 쓰지 않는다(명세).
- **셋 다 라벨을 단다** — labelable 이다. 이름이 없으면 트리에서 **무엇의 진행·측정인지** 모른다((1) — 다섯 다 라벨 글자가 이름이 됐다).

## 핵심 문장

1. **`output` 은 계산 결과, `progress` 는 일의 진행, `meter` 는 알려진 범위 안의 측정값이다 — 명세가 서로를 대신 쓰지 말라고 직접 적는다.**
2. **`output` 은 `form.elements` 에는 오르지만 값은 제출되지 않는다 — `progress`·`meter` 는 아예 폼 연관 요소가 아니다.**
3. **`output` 의 암묵 역할은 `status` 이고, Chrome 의 트리에서 `live=polite · atomic=true` 를 갖는 것은 셋 중 `output` 뿐이다.**
4. **`meter` 의 `optimum` 이 「어느 쪽이 좋은가」를 정하고, 명세의 구역 규칙이 값마다 최적·차선·더 나쁨을 가른다 — 그것을 무슨 색으로 그리느냐는 브라우저의 선택이다.**
5. **`output` 의 기본값은 스크립트가 처음 넣은 값이 아니라 마크업의 글자다 — reset 은 그리로 돌아간다.**

## 관련 자료

- [25번 주제](../25-label-association/2-summary.md) — labelable 목록 · 라벨이 이름을 주는 규칙 · `label` 의 `htmlFor` 는 문자열.
- [29번 주제](../29-constraint-validation/2-summary.md) — 이 배치의 하네스(`html29b-*`)와 제약 검증 API.
- [30번 주제](../30-form-state-and-input-hints/2-summary.md) — 「접근성 트리에 흔적이 없다」를 **물은 칸 수와 함께** 찍는 방식(18-A)의 앞선 판.
- 목록의 **41번 주제** — 암묵 역할 일반(`button` 이 무료로 주는 것).

## 용어 풀이

- **labelable** — `label` 과 이을 수 있는 요소. `output`·`progress`·`meter` 가 여기 든다.
- **listed** — `form.elements` 에 오르는 요소. `output` 은 들고 `progress`·`meter` 는 안 든다.
- **불확정 진행 막대(indeterminate)** — 얼마나 남았는지 모르는 진행. `value` 속성이 없을 때.
- **구역(region)** — `meter` 의 범위를 `low`·`high` 로 나눈 세 토막 중 최적·차선·더 나쁨.
- **default value override** — `output` 이 붙잡아 두는 기본값. `value` 를 처음 바꿀 때 지금 글자로 잡힌다.
- **`status` 역할** — 보조 정보를 알리는 라이브 영역 역할. `output` 의 암묵 역할.
- **UA 그림자 트리** — 브라우저가 요소 안에 몰래 만든 트리. `meter` 의 막대가 여기 산다.

## 더 들어가면

- **`meter` 의 `title` 로 단위 주기** — 명세는 단위를 적는 속성이 없다며 **`title` 에 자유 글자로** 적으라 한다(「centimeters」 예). 이 판은 던지지 않았다.
- **`progress` 의 `position`** — 확정이면 `값 ÷ 최댓값`, 불확정이면 **−1**(명세). 이 판은 IDL 로 찍지 않았다.
- **`div role=status` 와의 비교** — 같은 역할을 ARIA 로 다는 판이다. 이 판은 **캡처하지 않았다** — `output` 의 이점을 「역할 + 폼 연결 + labelable 이 한 요소에」로 적는 것은 명세 문장에서 읽은 것이다.
