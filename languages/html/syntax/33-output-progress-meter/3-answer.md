# html/syntax/33 — `output`·`progress`·`meter`: 계산 결과 / 진행 / 범위 안의 측정값 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스(33\~36번 공용)는 이 파일의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 `output`·`progress`·`meter` 절 · 렌더링 절 · [HTML-AAM](https://w3c.github.io/html-aam/) 의 요소 대응표로 접지했다(앞 배치가 받아 둔 사본 — **WAI-ARIA 사본은 없다**).\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 역할 격자다** — 명세 열로 셀 수 있는 22 칸을 미리 선언하고 「명세 열과 갈린 칸」을 스크립트가 센다(A1).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 명세 열과 갈린 칸 0 / 22 — `output` 은 `status` · `live=polite atomic=true` · 제출 ✕ · `form.elements` 에는 있음 / 서버 필드는 `i` 하나

**출력**

명세 열 파일 —

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

**왜 그런가**

- **역할** — `textbox` · `status` · `progressbar` · `progressbar` · `meter`. HTML-AAM 의 대응표 그대로다.
- ★★★ **라이브 속성은 `output` 하나에만** — `polite · atomic=true`. `progress`·`meter` 는 「—」. (이 열의 명세 쪽은 WAI-ARIA 문장이라 **판정 보류** — 세지 않았다.)
- ★★★ **제출** — `name` 을 다섯에 다 달았는데 서버는 **`i=1`** 만 받았다. `output` — 「요소의 값 자체는 **제출되지 않는다**」. `progress`·`meter` — **폼 연관 요소가 아니다**(카테고리가 labelable 뿐 · `name` 속성이 명세에 없다).
- **`labels`** — 다섯 다 **1**(셋 다 labelable — [25번](../25-label-association/2-summary.md)). 그래서 **이름**도 다섯 다 라벨 글자다(「입력」·「결과」·「진행」·「대기」·「측정」).
- ★★ **`form.elements`** — `input`·`output` 만. **`output` 은 listed 인데 제출되지 않는다.**
- **접근성 값** — `progress` 확정 `30` · 불확정 **없음** · `meter` `0.6000000238418579` · `output` **없음**(글자는 자식 노드). **범위** — `progress` 는 둘 다 `0..100`, `meter` 는 `0..1`.

### 2. 명세 열과 갈린 칸 0 / 10 — `pseudo` 셋(최적 · 차선 · 더 나쁨) · 색 세 가지

**출력**

명세 열 파일 —

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

**왜 그런가**

- ★★★ **값 막대 요소가 구역마다 다른 `pseudo` 를 받는다** — `-webkit-meter-optimum-value` · `-webkit-meter-suboptimum-value` · `-webkit-meter-even-less-good-value`. 그림자 트리에는 그 밖에 `-webkit-meter-inner-element` · `-webkit-meter-bar` 가 있다.
- ★★★ **열 칸 전부 명세의 구역 규칙과 맞았다** — `optimum` 이 `low`\~`high` 사이면 그 사이가 최적 · 바깥은 차선(`g1`\~`g3`) · 위에 있으면 `high`\~최댓값이 최적 · 아래 토막이 더 나쁨(`h1`\~`h3`) · 아래에 있으면 거꾸로(`l1`\~`l3`) · 세 속성이 없으면 **범위 전체가 최적**(`n1`).
- ★★ **색은 세 가지** — 초록 `rgb(16, 124, 16)` · 노랑 `rgb(255, 185, 0)` · 주황 `rgb(216, 59, 1)`. **이 색은 명세에 없다**(A7).

### 3. `value` 만 바뀌고 `defaultValue` 는 `"3"` · `reset()` 이 `"3"` 으로 · `htmlFor` 는 `DOMTokenList`(`a`,`b`) · 트리의 글자는 둘 다 `"4"` 로 · 다른 것은 `live=polite` 하나 · 이벤트 0 건

**출력**

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

**왜 그런가**

- ★★★ **value setter** — 「**default value override 를 지금의 기본값으로 둔다**(null 이면 자손 글자 `"3"`) → 글자를 바꾼다」. 그래서 `defaultValue` 는 `"3"` 에 붙잡혀 있다.
- ★★★ **reset** — 「기본값으로 **글자를 바꾸고** override 를 null 로」. 마크업의 `"3"` 으로 돌아간다.
- ★★ **`htmlFor`** — `[SameObject, PutForwards=value, Reflect="for"] readonly attribute DOMTokenList htmlFor`. `label` 의 `htmlFor` 는 **문자열**이다(A8).
- ★★★ **트리** — 두 노드 다 글자가 `"4"` 로 바뀌었다. `output` 은 `status` · `live=polite`, `p` 는 `paragraph` · `live` 없음.
- ★★★ **이벤트 0 건** · 대조로 **같은 탭을 다시 읽은 뒤에는 `Accessibility.loadComplete` 1 건** — 듣는 쪽은 살아 있었다(A9).

### 4. 「폼 컨트롤의 이벤트 처리기에서 쉽게 가리키게 하려고」 — 바로 뒤가 「요소의 값 자체는 폼을 제출할 때 제출되지 않는다」

- 명세 원문 — 「The `output` element is associated with a form so that it can be easily referenced from the event handlers of form controls; **the element's value itself is not submitted when the form is submitted.**」
- 그래서 `form.elements.o` 처럼 **이름으로 가리킬 수는 있고**(listed) 서버에는 안 간다(A1).

### 5. `meter` — `progress` 쪽 「그냥 계기에 `progress` 는 틀린 요소(디스크 사용량을 예로 든다)」 · `meter` 쪽 「진행을 나타내는 데 쓰면 안 된다」

- 명세 `progress` 절 — 「The `progress` element is the wrong element to use for something that is just a gauge … **indicating disk space usage using `progress` would be inappropriate.**」
- 명세 `meter` 절 — 「The `meter` element **should not be used to indicate progress**」 · 「범위를 모르는 값(몸무게·키)에도 틀렸다」.
- 트리에서는 역할이 갈린다 — `progressbar` 대 `meter`(A1). **틀린 요소를 쓰면 보조 기술에는 틀린 뜻이 간다.**

### 6. 불확정 진행 막대 — 속성이 **없을 때만** · `value="0"` 은 확정 · 0 · 접근성 값 칸

- 명세 — 「`value` 속성이 **생략되면** 불확정 진행 막대다. 그렇지 않으면 확정이다」. `value="0"` 은 **값이 0 인 확정 막대**다.
- 명세 — `position` 은 불확정이면 **−1**, `value` getter 는 불확정이면 **0** 을 돌려준다(이 판은 IDL 로 찍지 않았다).
- 이 판의 트리 — **`p2` 의 접근성 값이 「—」**(없음), 범위는 `0..100` 그대로(A1).

### 7. 정하는 것 — 여섯 점과 **구역** · 정하지 않는 것 — **모양과 색** / 확인 — 그림자 트리의 `pseudo` 와 계산된 색 · 못 보는 것 — 칠해진 픽셀

- 명세 — 「UA requirements for regions of the gauge」가 **구역을 must** 로 정한다 · 「UA requirements for showing the gauge」는 「세 구역과의 관계를 **보여야 한다(should)**」 · 렌더링 절은 「**플랫폼 관례**에 맞게」.
- ★★ 이 판 — 스크린샷 대신 **값 막대 요소의 `pseudo` 이름(구역) + `background-color` 계산값(색)**(A2 — 새 창).
- ★ **계산값은 선언이다** — `appearance: auto` 가 테마로 그리면 **화면과 다를 수 있다.** 픽셀은 이 판이 안 찍었다.

### 8. `label[for]` — 이름을 줄 **칸 하나**(문자열) · `output[for]` — 계산에 들어간 **칸들**(`DOMTokenList`) · 이름은 `label` 이 준다

- `label` 의 `for` — 그 `id` 의 첫 labelable 요소가 **연결된 컨트롤**이 되어 **이름**을 받는다([25번](../25-label-association/2-summary.md)).
- `output` 의 `for` — 「계산 결과와 **계산에 들어간 값을 나타내는 요소들**의 관계」 · 순서 없는 고유 토큰 집합. **이름을 주지 않는다.**
- 이 판 — `output` 의 이름은 **`label for="o"` 의 글자 「결과」다**(A1 의 「이름」 열 · `labels` 1). `output for="i"` 는 이름에 아무것도 보태지 않았다.

### 9. 본 것 — 노드의 `live=polite · atomic=true` · 바뀐 글자 · 못 본 것 — 플랫폼 API 로 가는 알림 · 발화 / CDP 의 `Accessibility` 도메인은 라이브 알림을 이벤트로 내보내는 창이 아니다

- ★★★ **「0 건」을 「안 났다」로 읽으려면 그 창이 그것을 싣는 창이어야 한다** — 대조 판(다시 읽기 → `loadComplete` 1 건)은 **듣는 쪽이 살아 있음**만 보인다. **라이브 알림이 그 창에 실린다는 증거는 없다.** 그래서 「못 잰 것」이다(18-A · 규칙 34).
- 확인하려면 **실기기 보조 기술**(스크린 리더)이 필요하다.

### 10. 제출 안 됨 — 명세 · 노랑 — 구현 · `live=polite` — 구현의 관찰(명세 쪽은 WAI-ARIA 라 판정 보류) · 불확정의 범위 — 구현(명세가 막지 않는다)

- **명세** — `output` 값의 비제출 · 구역 규칙 · 역할 대응.
- **구현(Chrome)** — 구역의 **색** · `pseudo` 이름 · 접근성 값의 32비트 부동소수 · 불확정 `progress` 의 범위.
- **판정 보류** — `status` 의 암묵 `live`·`atomic`(WAI-ARIA 사본이 없다).

### 11. 정본 경계

- **라벨이 이름을 주는 규칙** — [25번](../25-label-association/2-summary.md).
- **제약 검증 API**(`output` 에도 `willValidate` 등이 있다) — [29번](../29-constraint-validation/2-summary.md).
- **암묵 역할 일반** — 목록의 **41번 주제**.
- **`output` 이 서버에 안 가는 것** — **여기**(A1 · A4).

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800` · `--force-renderer-accessibility`. **엔진은 이것 하나다.**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

★ **하네스** — [29번](../29-constraint-validation/3-answer.md)의 `html29b-form.py`·`html29b-cdp.py`·`html29b-rec.js` 를 복사해 `html33b-` 로 이름을 바꿨다. **바꾼 것은 한 줄이다** — 접근성 노드의 **값**(`"값"`)을 함께 돌려주게 했다(A1 의 「AX 값」 열). 나머지 둘은 **이름 말고는 한 글자도 같다.**

```text
$ diff ../../html29b/src/html29b-cdp.py <(sed 's/html33b/html29b/g' html33b-cdp.py)
119c119
<     return {"역할": val(n, "role"), "이름": val(n, "name"), "설명": val(n, "description"), "이름출처": src,
---
>     return {"역할": val(n, "role"), "이름": val(n, "name"), "설명": val(n, "description"), "이름출처": src, "값": (n.get("value") or {}).get("value"),
(exit 1)
```

```text
$ diff ../../html29b/src/html29b-form.py <(sed 's/html33b/html29b/g' html33b-form.py) && diff ../../html29b/src/html29b-rec.js <(sed 's/html33b/html29b/g' html33b-rec.js) && echo '둘 다 같다'
둘 다 같다
(exit 0)
```

★ **더한 것 셋** — ① **실행기 `html33b-run.py`**(33\~36번 — 서버가 **어느 파일을 받았나**를 창 ⑤ 로 · 이미지를 **`/go` 까지 붙잡아** 「로드 전」을 잡는다 · 칸마다 **새 탭 · 캐시 끔 · 뷰포트/DPR 을 CDP `Emulation.setDeviceMetricsOverride` 로** · CDP 의 요청 **우선순위** · 콘솔 기록 · 그리고 이 편의 **UA 그림자 트리 창**(`속`)과 **라이브 창**(`라이브`)) · ② **시험 이미지 생성기 `html33b-make-images.py`**(34\~36번) · ③ **순서 세기 `html33b-tally.py`**(34번).\
★ **`/go`·끝 표지는 호스트 이름만 `localhost` 로 바꿔 부른다** — 붙잡힌 이미지가 `127.0.0.1` 의 연결(호스트당 여섯)을 다 차지해도 막히지 않게. 같은 서버다.

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌려(`capture.sh blocks` · `blocks-r1` · `blocks-r2`) `normalize-shaky.py` 로 첫 판과 견줬다 — 결과는 이 절 끝의 「재대조」 줄이다. 33\~36번의 블록이 전부 그 안에 있다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **역할 격자 22 칸** | 3 | 동작 방식 (1) · A1 |
| **`meter` 열 개** | 3 | 동작 방식 (2) · A2 |
| **`output` 바꾸기 · 되돌리기 · 이벤트** | 3 | 동작 방식 (3) · A3 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `meter` 구역의 색 | 초록 · 노랑 · 주황 | 명세는 모양을 정하지 않는다 |
| `meter` 의 접근성 값 | `0.6000000238418579` | 32비트 부동소수를 거친다 — 구현 |
| 불확정 `progress` 의 범위 | `0..100` 을 낸다 | HTML-AAM 은 확정일 때만 말한다 |

**안 돌려 본 것** — ① **`progress.position`·`value` IDL**(명세 문장만). ② **`meter` 의 `title` 단위**. ③ **`output` 의 제약 검증**(`willValidate`).

**못 잰 것** — ① **스크린 리더의 발화.** ② **`meter` 의 실제 픽셀.**

**부적용인 창** — **창 ① · ③ · ④ · ⑥**.

**재대조** — `capture.sh blocks-r1`·`blocks-r2` 를 첫 판(`blocks`)과 `normalize-shaky.py` 로 견준 결과가 **두 번 다 「블록 54개 · 동일 53 · 흔들린 칸 1 · ★고칠 것 0 · 한쪽에만 0」** 이다. 흔들린 한 블록은 **34번의 `34-prio-tally`**(20 판의 순서 세기)이고, 그것은 34번 머리말의 「흔들리는 칸」 표에 **미리 선언한** 칸이다. 기본 규칙 넷에 **그 블록 전용 규칙 넷**을 더했다 —\
`--rule '^ *[0-9]+ 판  [r0-9 ]+\n='`(순서 한 줄씩) · `--rule '가짓수 . [0-9]+=가짓수 = <n>'` · `--rule '마지막인 판 . [0-9]+=마지막인 판 = <n>'` · `--rule '먼저인 판 . [0-9]+=먼저인 판 = <n>'`.\
★ **규칙 패턴에 `=` 를 쓰지 마라** — 이 도구는 `--rule` 을 **첫 `=`** 에서 가른다. 처음 판에서 `가짓수 = [0-9]+=…` 로 적었다가 패턴이 `가짓수 ` 에서 잘려 **정규화가 조용히 빗나갔다**(규칙 32 의 같은 집안) — `.` 으로 바꿨다.\
★ **첫 재대조에서 「고칠 것」 둘이 더 나왔다** — `34-lazy-out`·`36-resize-out` 의 **함께 나간 두 요청의 순서**가 판마다 자리를 바꿨다. 한 블록에 흔들리는 칸을 섞지 않으려고(규칙 11) 페이지가 **표지 사이 묶음 안만 이름순으로** 찍게 고치고 세 판을 처음부터 다시 받았다 — 위 줄이 그 결과다.

**하네스 전문** — 34\~36번이 같은 파일을 쓴다. 29번 판에서 온 셋(`html33b-cdp.py`·`html33b-form.py`·`html33b-rec.js`)은 위 `diff` 가 차이의 전부다 — 전문은 [29번](../29-constraint-validation/3-answer.md)에 있다.

```python
# html33b-run.py
#!/usr/bin/env python3
"""33~36 — 창 ⑤(서버 요청 로그)를 「어느 후보 파일을 받았나」로 읽는 실행기. 29편 하네스(html33b-cdp.py)를 불러 쓴다.

사용: html33b-run.py 격자 <페이지> | 속 <페이지> | 라이브 <페이지>
  · 서버 하나(A)를 이 프로세스 안에 띄운다. 포트는 0 — 운영체제가 고른다(출력에는 안 적는다).
  · 경로 셋 —
      /i/<파일>   바로 준다
      /h/<파일>   ★ 붙잡아 둔다 — 페이지가 /go 를 부를 때까지 응답하지 않는다(「로드 전」 상태를 확실히 잡으려고)
      /m?<글자>   표지 — 페이지가 「지금 여기까지 왔다」를 로그 순서에 박는다(응답은 빈 204)
    로그는 받은 순서대로 「받음 i/…」·「받음 h/…」·「표지 …」·「풀어 줌」 줄만 적는다. 시각·포트는 안 적는다.
  · 격자 — 페이지의 window.__칸목록 = [{이름, 폭, 높이, dpr, 쪽?, 뒤단계?: [...]}, ...] 를 하나씩 돈다.
    칸마다 ★ 새 탭 → Network.setCacheDisabled(true) → Emulation.setDeviceMetricsOverride(폭 · 높이 · dpr) → 이동
    → DOMContentLoaded 를 기다림 → window.__전() (있으면 · 붙잡힌 이미지가 아직 안 온 상태)
    → fetch('/go') → load 를 기다림 → 뒤단계 → window.__뒤() (있으면) → fetch('/m?끝') → 탭을 닫는다.
    ★ /go 와 /m?끝 은 호스트 이름만 localhost 로 바꿔 부른다(붙잡힌 이미지가 연결을 다 차지해도 막히지 않게).
    뒤단계 꼴: ["js", 식] · ["크기", 폭, 높이, dpr](Emulation.setDeviceMetricsOverride 를 다시 건다)
    칸이 끝나면 결과 = {이름, 폭, 높이, dpr, 전, 뒤, 로그: [줄…], 요청: [{경로, 처음우선순위, 바뀐우선순위: […]}], 콘솔: [글자…]}
    를 모아, 페이지를 새로 열어 window.__종합(결과들) 이 돌려준 글자를 찍는다 — 표 짜기·칸 세기는 페이지가 한다.
    ★ 「뒤늦게 온 요청 = N」 — 칸의 「표지 끝」 뒤에 서버가 받은 줄 수(다음 칸을 열기 전에 센다).
  · 속 — window.__속대상 = [id…] 마다 그 요소의 UA 그림자 트리를 CDP DOM(pierce)으로 내려가
    pseudo 속성이 있는 노드와 그 계산된 background-color(CSS.getComputedStyleForNode)를 window.__속 에 넣고 window.__끝() 을 찍는다.
  · 라이브 — window.__대상 의 접근성 노드를 전(window.__AX전)·후(window.__AX뒤)로 받고,
    그 사이에 window.__바꾸기() 를 돌린 뒤 받은 CDP 이벤트 가운데 Accessibility.* 의 이름과 수를 window.__이벤트 로 넣어 window.__끝() 을 찍는다.
    ★ 대조 — 끝으로 같은 탭을 다시 읽어(Page.reload) 그때 받은 Accessibility.* 이벤트를 센다 — 듣는 쪽이 살아 있음을 보이는 판.
"""
import http.server, importlib.util, json, mimetypes, os, shutil, sys, threading, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cdp", os.path.join(HERE, "html33b-cdp.py"))
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)

LOG = []
LOCK = threading.Lock()
GATE = threading.Event()
mimetypes.add_type("image/webp", ".webp")


def 적기(s):
    with LOCK:
        LOG.append(s)


def take_log():
    with LOCK:
        out = LOG[:]
        LOG.clear()
    return out


def server():
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=HERE, **k)

        def 파일(self, rel):
            p = os.path.join(HERE, "i", os.path.basename(rel))
            if not os.path.isfile(p):
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            data = open(p, "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(p)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urllib.parse.urlsplit(self.path)
            q = ("?" + urllib.parse.unquote(u.query)) if u.query else ""
            if u.path.startswith("/i/"):
                적기("받음  i/" + u.path[3:] + q)
                return self.파일(u.path[3:])
            if u.path.startswith("/h/"):
                적기("받음  h/" + u.path[3:] + q)
                if not GATE.wait(30):
                    적기("시간 초과  h/" + u.path[3:] + q)
                return self.파일(u.path[3:])
            if u.path == "/go":
                적기("풀어 줌")
                GATE.set()
                return self.비움()
            if u.path == "/m":
                적기("표지  " + urllib.parse.unquote(u.query))
                return self.비움()
            return super().do_GET()

        def 비움(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

        def log_message(self, *a):
            pass

    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


def 옆(path):
    """/go 와 /m?끝 은 호스트 이름을 localhost 로 바꿔 부른다 — 붙잡힌 이미지가 127.0.0.1 의 연결(호스트당 여섯)을
    다 차지하고 있어도 막히지 않게(같은 서버 · 다른 연결 풀)."""
    return ("fetch(location.origin.replace('127.0.0.1', 'localhost') + " + json.dumps(path)
            + ", { mode: 'no-cors' }).then(() => 1)")


def 새탭(c, 폭=1000, 높이=800, dpr=1):
    tid = c.send("Target.createTarget", {"url": "about:blank"})["targetId"]
    sid = c.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
    for m in ("Page.enable", "Runtime.enable", "DOM.enable", "CSS.enable", "Accessibility.enable", "Log.enable", "Network.enable"):
        c.send(m, sid=sid)
    c.send("Network.setCacheDisabled", {"cacheDisabled": True}, sid)
    크기(c, sid, 폭, 높이, dpr)
    return tid, sid


def 크기(c, sid, 폭, 높이, dpr):
    c.send("Emulation.setDeviceMetricsOverride", {"width": 폭, "height": 높이, "deviceScaleFactor": dpr, "mobile": False}, sid)


def 닫기(c, tid):
    c.send("Target.closeTarget", {"targetId": tid})


def 이동(c, sid, url, 끝까지=True):
    c.send("Page.navigate", {"url": url}, sid)
    c.wait("Page.domContentEventFired", sid)
    if 끝까지:
        c.wait("Page.loadEventFired", sid)


def 이미지경로(url):
    u = urllib.parse.urlsplit(url)
    if u.path.startswith(("/i/", "/h/")):
        return u.path[1:] + (("?" + urllib.parse.unquote(u.query)) if u.query else "")
    return None


def 네트워크(c, sid):
    """이 탭이 보낸 이미지 요청 — 보낸 순서 · 처음 우선순위 · 바뀐 우선순위."""
    cdp.evaluate(c, sid, "1")          # 앞서 온 이벤트를 다 받아 둔다
    by, order = {}, []
    for e in c.events:
        if e.get("sessionId") != sid:
            continue
        m, p = e.get("method"), e.get("params", {})
        if m == "Network.requestWillBeSent":
            path = 이미지경로(p["request"]["url"])
            if path:
                by[p["requestId"]] = {"경로": path, "처음우선순위": p["request"].get("initialPriority"), "바뀐우선순위": []}
                order.append(p["requestId"])
        elif m == "Network.resourceChangedPriority" and p.get("requestId") in by:
            by[p["requestId"]]["바뀐우선순위"].append(p["newPriority"])
    logs = [e["params"]["entry"]["text"] + (f" (줄 {e['params']['entry']['lineNumber'] + 1})" if "lineNumber" in e["params"]["entry"] else "")
            for e in c.events if e.get("sessionId") == sid and e.get("method") == "Log.entryAdded"]
    return [by[r] for r in order], logs


def 단계(c, sid, st):
    if st[0] == "js":
        v = cdp.evaluate(c, sid, st[1])
        if isinstance(v, str) and v.startswith("«예외"):
            raise RuntimeError(st[1] + " -> " + v)
    elif st[0] == "크기":
        크기(c, sid, *st[1:4])
    else:
        raise RuntimeError("모르는 단계: " + st[0])


def 울타리(c, sid):
    """목록을 읽으려고 연 탭이 보낸 표지(load 등)가 다음 칸의 로그에 섞이지 않게 —
    같은 호스트로 표지 하나를 더 보내고, 그것이 로그에 올 때까지 받은 줄을 버린다."""
    cdp.evaluate(c, sid, "new Promise(r => setTimeout(r, 0)).then(() => fetch('/m?읽기끝')).then(() => 1)")
    while "표지  읽기끝" not in take_log():
        cdp.evaluate(c, sid, "new Promise(r => setTimeout(r, 0)).then(() => 1)")


def 격자(c, base, page):
    tid, sid = 새탭(c)
    이동(c, sid, base + page, 끝까지=False)
    cells = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__칸목록)"))
    cdp.evaluate(c, sid, 옆("/go"))
    c.wait("Page.loadEventFired", sid)
    울타리(c, sid)
    닫기(c, tid)
    res, late = [], 0
    for cell in cells:
        GATE.clear()
        c.events.clear()
        tid, sid = 새탭(c, cell["폭"], cell.get("높이", 800), cell["dpr"])
        이동(c, sid, base + cell.get("쪽", page), 끝까지=False)
        before = cdp.evaluate(c, sid, "window.__전 ? window.__전() : null")
        cdp.evaluate(c, sid, 옆("/go"))
        c.wait("Page.loadEventFired", sid)
        for st in cell.get("뒤단계", []):
            단계(c, sid, st)
        after = cdp.evaluate(c, sid, "window.__뒤 ? window.__뒤() : null")
        cdp.evaluate(c, sid, 옆("/m?끝"))
        reqs, logs = 네트워크(c, sid)
        닫기(c, tid)
        log = take_log()
        end = next(i for i, l in enumerate(log) if l == "표지  끝")
        late += len(log) - end - 1
        res.append({**cell, "전": before, "뒤": after, "로그": log[:end + 1], "요청": reqs, "콘솔": logs})
    GATE.set()
    tid, sid = 새탭(c)
    이동(c, sid, base + page)
    울타리(c, sid)
    print(cdp.evaluate(c, sid, "window.__종합(" + json.dumps(res, ensure_ascii=False) + ")"))
    닫기(c, tid)
    take_log()
    print(f"뒤늦게 온 요청 = {late}")


def 속(c, base, page):
    GATE.set()
    tid, sid = 새탭(c)
    이동(c, sid, base + page)
    ids = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__속대상)"))
    root = c.send("DOM.getDocument", {"depth": -1, "pierce": True}, sid)["root"]
    by = {}

    def attrs(n):
        a = n.get("attributes", [])
        return dict(zip(a[0::2], a[1::2]))

    def find(n):
        if attrs(n).get("id") in ids:
            by[attrs(n)["id"]] = n
        for k in ("children", "shadowRoots"):
            for ch in n.get(k, []):
                find(ch)
    find(root)
    out = {}
    for i in ids:
        got = []

        def walk(n, in_shadow):
            ps = attrs(n).get("pseudo")
            if in_shadow and ps:
                st = c.send("CSS.getComputedStyleForNode", {"nodeId": n["nodeId"]}, sid)["computedStyle"]
                bg = next(x["value"] for x in st if x["name"] == "background-color")
                got.append([ps, bg])
            for ch in n.get("children", []):
                walk(ch, in_shadow)
            for sr in n.get("shadowRoots", []):
                walk(sr, True)
        walk(by[i], False)
        out[i] = got
    cdp.evaluate(c, sid, "window.__속 = " + json.dumps(out, ensure_ascii=False))
    print(cdp.evaluate(c, sid, "window.__끝()"))
    닫기(c, tid)


def 글자아래(c, sid, sel):
    """그 노드 아래 StaticText 의 이름을 트리 순서로 이어 붙인다 — 접근성 트리가 들고 있는 글자."""
    root = c.send("DOM.getDocument", {"depth": 0}, sid)["root"]["nodeId"]
    nid = c.send("DOM.querySelector", {"nodeId": root, "selector": sel}, sid)["nodeId"]
    be = cdp.backend(c, sid, nid)
    nodes = c.send("Accessibility.getFullAXTree", {}, sid)["nodes"]
    by = {n["nodeId"]: n for n in nodes}
    top = next(n for n in nodes if n.get("backendDOMNodeId") == be)
    out = []

    def walk(n):
        if cdp.val(n, "role") == "StaticText":
            out.append(cdp.val(n, "name"))
        for ch in n.get("childIds", []):
            if ch in by:
                walk(by[ch])
    walk(top)
    return "".join(out)


def 이벤트이름(c, sid):
    names = {}
    for e in c.events:
        m = e.get("method", "")
        if e.get("sessionId") == sid and m.startswith("Accessibility."):
            names[m] = names.get(m, 0) + 1
    return names


def 라이브(c, base, page):
    GATE.set()
    tid, sid = 새탭(c)
    이동(c, sid, base + page)
    targets = json.loads(cdp.evaluate(c, sid, "JSON.stringify(window.__대상 || [])"))
    c.send("Accessibility.getFullAXTree", {}, sid)
    ax = {k: {**cdp.ax_of(c, sid, sel), "글자": 글자아래(c, sid, sel)} for k, sel in targets}
    c.events.clear()
    cdp.evaluate(c, sid, "window.__바꾸기()")
    cdp.evaluate(c, sid, 옆("/m?끝"))
    names = 이벤트이름(c, sid)
    ax2 = {k: {**cdp.ax_of(c, sid, sel), "글자": 글자아래(c, sid, sel)} for k, sel in targets}
    for k, v in (("__AX전", ax), ("__AX뒤", ax2), ("__이벤트", names)):
        cdp.evaluate(c, sid, "window." + k + " = " + json.dumps(v, ensure_ascii=False))
    print(cdp.evaluate(c, sid, "window.__끝()"))
    # ★ 대조 — 듣는 쪽이 살아 있나: 같은 탭을 다시 읽으면 Accessibility.* 이벤트가 오는가(규칙 34 — 「오게 만든 판」)
    c.events.clear()
    c.send("Page.reload", {}, sid)
    c.wait("Page.loadEventFired", sid)
    cdp.evaluate(c, sid, 옆("/m?끝"))
    again = 이벤트이름(c, sid)
    print("대조 — 같은 탭을 다시 읽은 뒤 받은 Accessibility.* 이벤트 = "
          + (" · ".join(f"{k} {v}" for k, v in again.items()) if again else "0 건"))
    닫기(c, tid)


def main():
    mode, page = sys.argv[1], sys.argv[2]
    a = server()
    base = f"http://127.0.0.1:{a.server_address[1]}/"
    proc, c = cdp.start()
    try:
        {"격자": 격자, "속": 속, "라이브": 라이브}[mode](c, base, page)
    finally:
        proc.terminate()
        proc.wait()
        shutil.rmtree(cdp.PROF, ignore_errors=True)
        GATE.set()
        a.shutdown()


if __name__ == "__main__":
    main()
```

```python
# html33b-make-images.py
#!/usr/bin/env python3
"""33~36 의 시험 이미지를 i/ 아래에 만든다 — PNG 는 표준 라이브러리(zlib · struct)로, WebP 는 Chrome 의 canvas 로.
  · 파일 이름은 크기만 적는다(a400 = 폭 400). 한 색으로 칠한 그림이다 — 내용은 묻지 않는다.
  · WebP 는 canvas.toDataURL('image/webp') 가 돌려준 바이트를 그대로 쓴다. 같은 판에서 image/avif 도 물어 본다.
"""
import base64, importlib.util, os, struct, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "i")
spec = importlib.util.spec_from_file_location("cdp", os.path.join(HERE, "html33b-cdp.py"))
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)


def png(name, w, h, rgb):
    row = b"\x00" + bytes(rgb) * w
    raw = zlib.compress(row * h, 9)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")
    open(os.path.join(OUT, name), "wb").write(data)


os.makedirs(OUT, exist_ok=True)
for name, w, h, rgb in [
    ("p300x150.png", 300, 150, (37, 99, 235)),
    ("a400.png", 400, 200, (220, 38, 38)), ("a800.png", 800, 400, (22, 163, 74)), ("a1600.png", 1600, 800, (147, 51, 234)),
    ("d200.png", 200, 100, (234, 88, 12)), ("d400.png", 400, 200, (8, 145, 178)),
    ("c400x400.png", 400, 400, (202, 138, 4)), ("c800x400.png", 800, 400, (71, 85, 105)),
    ("g200.png", 200, 100, (190, 24, 93)), ("f200.png", 200, 100, (101, 163, 13)),
]:
    png(name, w, h, rgb)

proc, c = cdp.start()
try:
    sid = cdp.open_page(c, "about:blank")
    for t, name in (("image/webp", "f200.webp"), ("image/avif", None)):
        url = cdp.evaluate(c, sid, "(() => { const k = document.createElement('canvas'); k.width = 200; k.height = 100;"
                           " const g = k.getContext('2d'); g.fillStyle = 'rgb(101 163 13)'; g.fillRect(0, 0, 200, 100);"
                           " return k.toDataURL(" + repr(t) + "); })()")
        got = url.split(";", 1)[0][5:]
        print(f"canvas.toDataURL({t!r}) 가 돌려준 형식 = {got}")
        if name and got == t:
            open(os.path.join(OUT, name), "wb").write(base64.b64decode(url.split(",", 1)[1]))
finally:
    proc.terminate()
    proc.wait()
    import shutil
    shutil.rmtree(cdp.PROF, ignore_errors=True)
```

```python
# html33b-tally.py
#!/usr/bin/env python3
"""html33b-tally.py <판 수> — 34편 우선순위 페이지(html33b-34-prio.html?log — 서버 로그만 찍는 판)를 N 판 돌려, 서버가 붙잡힌 이미지를 받은 순서의 가짓수를 센다.
  · 순서 한 줄 = 그 판에서 서버가 받은 k= 꼬리표를 받은 순서대로 이은 것.
  · 표는 가짓수(많은 순 · 같으면 글자 순)와 판 수 · 끝에 「r3(fetchpriority=low)이 마지막인 판」과 「r2 가 r1 보다 먼저인 판」을 센다.
  ★ 실행기의 출력을 전부 받은 뒤 이 스크립트 안에서 걸러 낸다(파이프를 태우지 않는다).
"""
import collections, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
n = int(sys.argv[1])
seen = collections.Counter()
low_last = high_first = 0
for _ in range(n):
    r = subprocess.run([sys.executable, os.path.join(HERE, "html33b-run.py"), "격자", "html33b-34-prio.html?log"],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode:
        sys.exit("실행기 exit " + str(r.returncode))
    order = re.findall(r"받음  h/p300x150\.png\?k=(r\d)", r.stdout)
    seen[" ".join(order)] += 1
    low_last += bool(order) and order[-1] == "r3"
    high_first += order.index("r2") < order.index("r1")
for k, v in sorted(seen.items(), key=lambda x: (-x[1], x[0])):
    print(f"{v:3d} 판  {k}")
print(f"판 = {n} · 순서의 가짓수 = {len(seen)}")
print(f"r3(fetchpriority=low)이 마지막인 판 = {low_last} / {n}")
print(f"r2(fetchpriority=high)가 r1(속성 없음)보다 먼저인 판 = {high_first} / {n}")
```

```bash
# capture.sh
#!/usr/bin/env bash
# html33b 묶음(HTML 33~36 — output·progress·meter / img / srcset·sizes / picture) — 문서에 실을 블록을 전부 파일로 받는다.
#   사용: ./capture.sh [출력디렉토리]    (기본 blocks)
# ★ 29편 하네스(capture.sh)를 이었다 — 출력 디렉토리 절대경로 정규화(규칙 25) · set -o pipefail ·
#   자르는 명령은 배너에 적되 실행에는 파이프를 물리지 않는다 · grep -c 를 마지막 명령으로 두지 않는다 · 표준 출력만 싣는다(규칙 18).
# ★ 이 묶음이 더한 것 — 실행기 html33b-run.py(창 ⑤ 를 「어느 후보 파일을 받았나」로) · 시험 이미지 생성기 · 순서 세기(html33b-tally.py).
# ★ 시험 이미지는 캡처가 매번 새로 만든다(src/i/) — 저장소에는 들어가지 않는다.
set -o pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="${1:-blocks}"
case $OUT_DIR in /*) ;; *) OUT_DIR="$HERE/$OUT_DIR" ;; esac
SRC="$HERE/src"
RAW="$OUT_DIR/.raw"
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR" "$RAW"
cd "$SRC" || exit 1

run() {  # run <열쇠> <명령문자열> — 한 번만 돌려 표준 출력과 종료 코드를 받아 둔다
  local key="$1" cmd="$2"
  if [ ! -f "$RAW/$key.rc" ]; then
    eval "$cmd" > "$RAW/$key.out" 2>/dev/null
    printf '%s' "$?" > "$RAW/$key.rc"
  fi
}

out_block() {  # out_block <블록이름> <열쇠> <명령> [필터]
  local name="$1" key="$2" cmd="$3" pipe="$4" rc
  run "$key" "$cmd"
  rc="$(cat "$RAW/$key.rc")"
  {
    printf '```text\n'
    if [ -n "$pipe" ]; then
      printf '$ %s | %s\n' "$cmd" "$pipe"
      eval "cat '$RAW/$key.out' | $pipe"
    else
      printf '$ %s\n' "$cmd"
      cat "$RAW/$key.out"
    fi
    printf '(exit %s)\n' "$rc"
    printf '```\n'
  } > "$OUT_DIR/$name.txt"
}

key() { local s="$*"; s="${s//[ \/#\'?]/_}"; printf '%s' "$s"; }
run33() { local name="$1"; shift; out_block "$name" "run-$(key "$@")" "python3 html33b-run.py $*"; }
form33() { local name="$1"; shift; local args="" pipe=""
  while [ $# -gt 0 ]; do if [ "$1" = "--" ]; then pipe="$2"; break; fi; args="$args $1"; shift; done
  args="${args# }"; out_block "$name" "form-$(key "$args")" "python3 html33b-form.py $args" "$pipe"; }

src_html() { { printf '<!-- %s -->\n' "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_js()   { { printf '// %s\n'        "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_py()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }
src_sh()   { { printf '# %s\n'         "$(basename "$2")"; cat "$2"; } > "$OUT_DIR/$1.txt"; }

out_block ver ver "google-chrome --version"
out_block cmdv cmdv "command -v cwebp avifenc"
out_block make make "python3 html33b-make-images.py"
out_block files files "stat -c '%s %n' i/*"
out_block webphead webphead "od -A d -c -N 16 i/f200.webp"
out_block harness-diff harness-diff "diff ../../html29b/src/html29b-cdp.py <(sed 's/html33b/html29b/g' html33b-cdp.py)"
out_block harness-diff2 harness-diff2 "diff ../../html29b/src/html29b-form.py <(sed 's/html33b/html29b/g' html33b-form.py) && diff ../../html29b/src/html29b-rec.js <(sed 's/html33b/html29b/g' html33b-rec.js) && echo '둘 다 같다'"

# ------------------------------------------------------------ 33 output · progress · meter
src_html 33-grid-src   html33b-33-grid.html
src_js   33-spec-src   html33b-33-spec.js
form33   33-grid-out   시도 html33b-33-grid.html
src_html 33-meter-src  html33b-33-meter.html
src_js   33-meter-spec html33b-33-meter-spec.js
run33    33-meter-out  속 html33b-33-meter.html
src_html 33-live-src   html33b-33-live.html
run33    33-live-out   라이브 html33b-33-live.html

# ------------------------------------------------------------ 34 img
src_html 34-shift-src  html33b-34-shift.html
run33    34-shift-out  격자 html33b-34-shift.html
src_html 34-lazy-src   html33b-34-lazy.html
run33    34-lazy-out   격자 html33b-34-lazy.html
src_html 34-alt-src    html33b-34-alt.html
src_js   34-alt-spec   html33b-34-alt-spec.js
form33   34-alt-out    page html33b-34-alt.html
src_html 34-prio-src   html33b-34-prio.html
run33    34-prio-out   격자 html33b-34-prio.html
out_block 34-prio-tally tally "python3 html33b-tally.py 20"

# ------------------------------------------------------------ 35 srcset · sizes
src_html 35-grid-src   html33b-35-grid.html
src_js   35-rule-src   html33b-35-rule.js
run33    35-grid-out   격자 html33b-35-grid.html
src_html 35-sizes-src  html33b-35-sizes.html
run33    35-sizes-out  격자 html33b-35-sizes.html
src_html 35-x-src      html33b-35-x.html
run33    35-x-out      격자 html33b-35-x.html
src_html 35-drop-src   html33b-35-drop.html
run33    35-drop-out   격자 html33b-35-drop.html
src_html 35-resize-src html33b-35-resize.html
run33    35-resize-out 격자 html33b-35-resize.html
src_html 35-auto-src   html33b-35-auto.html
run33    35-auto-out   격자 html33b-35-auto.html

# ------------------------------------------------------------ 36 picture
src_html 36-art-src    html33b-36-art.html
run33    36-art-out    격자 html33b-36-art.html
src_html 36-resize-src html33b-36-resize.html
run33    36-resize-out 격자 html33b-36-resize.html
src_html 36-type-src   html33b-36-type.html
run33    36-type-out   격자 html33b-36-type.html
src_html 36-dims-src   html33b-36-dims.html
run33    36-dims-out   격자 html33b-36-dims.html
src_html 36-ax-src     html33b-36-ax.html
form33   36-ax-out     page html33b-36-ax.html
form33   36-ax-tree    ax html33b-36-ax.html

# ------------------------------------------------------------ 하네스 (33-answer 실행 검증)
src_py   run-py        html33b-run.py
src_py   make-py       html33b-make-images.py
src_py   tally-py      html33b-tally.py
src_js   rec-js        html33b-rec.js
src_sh   capture-sh    ../capture.sh
```

## 용어 풀이

- **역할 격자** — 요소 × (역할 · 라이브 · 제출 · 라벨 …) 표.
- **default value override** — `output` 이 붙잡아 두는 기본값.
- **구역** — `meter` 의 최적 · 차선 · 더 나쁨.
- **UA 그림자 트리 창** — CDP `DOM.getDocument(pierce)` 로 브라우저가 만든 속 트리를 내려가 `pseudo` 와 계산값을 읽는 창.
