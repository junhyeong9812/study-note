# html/syntax/23 — `<input>` 타입 지도 ② 숫자·날짜: `number`/`range`/`date`/`time`/`datetime-local`/`month`/`week` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The input element」](https://html.spec.whatwg.org/multipage/input.html) 절 — Date·Month·Week·Time·Local Date and Time·Number·Range 상태의 **값 정화 알고리즘**·「문자열을 수로 바꾸는 알고리즘」·`valueAsNumber`/`valueAsDate`, 「Implementation notes regarding localization of form controls」(비규범), 제약 검증의 step mismatch 줄, 그리고 [HTML-AAM](https://w3c.github.io/html-aam/). **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다.**
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 하네스는 [21번 주제](../21-form-submission-model/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — Baseline(목록 README 의 2026-09-21 조회): **날짜·시간 `<input>` 타입 widely**(newly 2021-10-05 → widely 2024-04-05). `number`·`range` 는 따로 조회하지 않았다.
> **선행** — [22번 주제](../22-input-types-text/2-summary.md)(값 정화 · `validity` 깃발).
> **경계** — **`min`/`max`/`step` 이 눈금을 만드는 규칙**의 정본은 목록의 **28번 주제**다 — 여기는 그 깃발과 문구가 **어떻게 보이나**까지만. **`time` 요소의 `datetime`** 은 [14번 주제](../14-quotation-edits-and-time/2-summary.md)의 몫이다 — 여기는 그것과 **`input type=date` 가 어떻게 다른가**만 대비한다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다** — 「값은 로케일 무관 형식」은 **서버가 받은 글자**로만 증명된다. 짝으로 **창 ⑦(접근성 트리의 글자)** 이 「화면에는 로케일 형식으로 보인다」를 맡는다.

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
| ★ **일부러 바꿨다** | **로케일**(`ko-KR` / `de-DE`) | (1) 은 **같은 파일을 두 로케일로** 띄워 견준다 — 화면 글자·`Accept-Language` 가 갈리는 것이 결론이다 |
| **고정했다** | 나머지 블록의 로케일 = `ko-KR` | `validationMessage`·화면 글자가 로케일을 탄다 |
| **흔들린다** | `validationMessage` 문구 | 근거로 쓰지 않는다([22번](../22-input-types-text/2-summary.md)) |
| **흔들린다** | CDP 포트·프로필 경로·서버 포트 | 출력에는 안 들어간다 |
| **안 흔들린다** | 서버에 실린 값 · `.value` · `valueAsNumber` · `validity` 깃발 | 같은 판이면 결정적이다 |
| **안 흔들린다** | `valueAsDate` 의 `toISOString()` | UTC 로 찍어 **기계의 시간대에 안 탄다** |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 두 로케일에서 **실린 값이 같나** · 입력한 글자가 **무슨 값으로** 실렸나((1)·(3)) |
| **⑦ 접근성 트리의 글자** | ★ **쓴다 — 본체의 짝** | 화면에 **어떤 형식으로** 보이나((1)) |
| **② 노드 프로브** | 쓴다 | `.value`·`valueAsNumber`·`valueAsDate`·`validity` 깃발((2)\~(4)) |
| **① `--dump-dom`** | 쓴다(곁가지) | 로케일이 **정말 바뀌었나**(`navigator.language`)((1)) · demo 검증 |
| **③ `innerText` 대 `textContent`** | **부적용** | 입력의 값은 자식 글자가 아니다 |
| **④ `compatMode`** · **⑥ `renderBlockingStatus`** | **부적용** | 무관하다 — 잴 것이 없다 |

- ★★★ **제5의 상태 — 「화면에 무엇이 보이나」를 픽셀이 아니라 접근성 트리의 글자로 물었다.** 날짜 칸의 화면 글자는 **UA 의 그림자 트리** 안에 있어 DOM 프로브로는 안 닿는다(`.value` 는 로케일 무관 형식을 돌려준다). CDP 트리는 그 칸의 **`spinbutton` 들과 사이 글자(`StaticText`)** 를 준다 — 하네스가 그것을 트리 순서로 이어 붙였다. ★ **바꾼 창이 못 보는 것** — **글꼴·자리 배치·색**, 그리고 트리에 안 들어가는 **그림 요소**(달력 아이콘 등). 「이 글자들이 이 순서로 칸에 있다」까지다.

## 한눈에 — 쉽게 말하면

**★ 날짜·숫자 칸은 「통역사가 붙은 칸」이다. 사람에게는 그 사람 말(로케일)로 보여 주고, 서버에는 언제나 같은 공용어(ISO 꼴·점 소수)로 넘긴다.**

국제 회의장 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **참석자에게 들리는 말** | 화면 표시 — `2026. 09. 26.` / `26.09.2026` |
| **회의록에 적히는 공용어** | `.value`·제출 값 — `2026-09-26` |
| **통역사** | UA 의 입력 칸 — 표시·입력 해석을 로케일로 한다 |
| **참석자가 한 말을 통역사가 잘못 알아듣는 것** | ★ **입력 해석**은 로케일을 탄다 — `1,5` 가 `15` 도 `1.5` 도 된다 |
| **공용어로 못 옮기는 말** | 무효한 입력 — `.value` 가 **빈 문자열**, `badInput` 참 |
| **숫자 칸의 위아래 단추** | `number` 의 스핀 단추 — **수로 다룬다**(앞의 0 이 사라진다) |

- **서버에 가는 날짜는 두 로케일에서 한 글자도 같다**((1)).
- ★ **그런데 사람이 친 숫자 `1,5` 는 로케일마다 다른 값이 된다**((1) 의 `k1`).
- **`number` 에 `010-1234` 를 치면 값이 빈 문자열이 된다** · `0101234` 는 글자로는 남지만 **위 화살표 한 번에 `101235`** 가 된다((3)).

```text
  날짜 칸 하나 — 표시와 값의 두 길

                     ko-KR                      de-DE
  화면 (창 ⑦)        2026. 09. 26.              26.09.2026        ← 로케일이 정한다 (명세: 비규범 권고)
  .value (창 ②)      2026-09-26                 2026-09-26        ← 명세의 「유효한 날짜 문자열」
  서버 (창 ⑤)        d=2026-09-26               d=2026-09-26      ← 같다

  ★ 명세 — 「날짜·시간·숫자 칸이 사용자에게 보여 주는 형식은 폼 제출에 쓰이는 형식과 독립이다」
```

> **로케일(locale)** — 언어 + 지역의 표기 관례. 날짜 순서·소수점 기호·12/24시간제가 여기서 갈린다.\
> 예: `ko-KR` 은 `1,234.5`, `de-DE` 는 `1.234,5`.

> **`valueAsNumber` / `valueAsDate`** — `.value` 를 **수 / `Date`** 로 읽는 프로퍼티. 타입마다 「문자열을 수로 바꾸는 알고리즘」이 다르다.\
> 예: `month` 의 `valueAsNumber` 는 **1970년 1월부터 센 달 수**(`2026-09` → `680`).

## 이 주제가 답하려는 질문

1. **「값은 로케일 무관 형식」은 정확히 무엇이 무관하다는 뜻인가** — 표시·입력 해석·제출 값 중 어느 것이.
2. **`number` 에 전화번호를 넣으면 무엇이 깨지나** — 값 · 수 · 스핀 단추.
3. **값을 수·날짜로 읽는 API(`valueAsNumber`·`valueAsDate`)와 `min`/`max`/`step` 깃발은 어떻게 보이나** — 그리고 `range` 는 왜 빈 값이 없나.

## 동작 방식

### (1) 창 ⑤ + 창 ⑦ — 같은 파일을 두 로케일로

**언제 쓰나** — 서버가 날짜를 **어떤 형식으로 파싱해야 하나**, 사용자 로케일마다 분기해야 하나를 정할 때.

**먼저 — 로케일을 어떻게 바꾸나.** 브리핑의 계획은 `--lang=ko-KR` 대 `--lang=de-DE` 였는데, **리눅스의 Chrome 은 그 플래그를 듣지 않았다** — `navigator.language` 가 기계의 로케일(`ko-KR`)에 머문다. **환경 변수 `LANGUAGE`** 가 바꾼다.

```html
<!-- html21b-23-lang.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>23 로케일 확인</title>
<body>
<input id="e" type="email" value="a">
<script>
document.body.append(Object.assign(document.createElement("script"), { type: "text/plain",
  textContent: "\n--OUT\nnavigator.language = " + navigator.language
    + "\nvalidationMessage = " + document.getElementById("e").validationMessage
    + "\n(1234.5).toLocaleString() = " + (1234.5).toLocaleString() + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --lang=de-DE --dump-dom html21b-23-lang.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
navigator.language = ko-KR
validationMessage = 이메일 주소에 '@'를 포함해 주세요. 'a'에 '@'가 없습니다.
(1234.5).toLocaleString() = 1,234.5
(exit 0)
```

```text
$ LANGUAGE=de_DE google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html21b-23-lang.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
navigator.language = de-DE
validationMessage = Die E-Mail-Adresse muss ein @-Zeichen enthalten. In der Angabe "a" fehlt ein @-Zeichen.
(1234.5).toLocaleString() = 1.234,5
(exit 0)
```

- ★★ **`--lang=de-DE` 는 아무것도 안 바꿨다** — 세 줄 다 한국어·한국 관례다. **`LANGUAGE=de_DE`** 는 셋 다 바꿨다. 그래서 하네스의 `--lang=xx-YY` 는 **이름만 플래그이고 실제로는 `LANGUAGE` 를 넘긴다**(하네스 주석에 적었다).

이제 본 실험 — 일곱 타입에 값을 넣고, 두 `number` 칸(`k1`·`k2`)에는 **진짜로 글자를 쳐서**(`Input.insertText`) `1,5` 와 `1.5` 를 넣었다. 로케일마다 **새 브라우저**를 띄워 **화면 글자(창 ⑦) → 제출(창 ⑤)** 순으로 받았다.

```html
<!-- html21b-23-locale.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 두 로케일</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post" novalidate>
<input id="d" name="d" type="date" value="2026-09-26" aria-label="날짜">
<input id="t" name="t" type="time" value="13:05" aria-label="시각">
<input id="dt" name="dt" type="datetime-local" value="2026-09-26T13:05" aria-label="날짜와 시각">
<input id="m" name="m" type="month" value="2026-09" aria-label="달">
<input id="w" name="w" type="week" value="2026-W39" aria-label="주">
<input id="n" name="n" type="number" value="1234.5" step="any" aria-label="수">
<input id="r" name="r" type="range" aria-label="범위">
<input id="k1" name="k1" type="number" step="any" aria-label="입력한 수 1">
<input id="k2" name="k2" type="number" step="any" aria-label="입력한 수 2">
<button id="보냄">보냄</button>
</form>
<script>
window.__준비 = [["type", "#k1", "1,5"], ["type", "#k2", "1.5"]];
window.__칸 = ["d", "t", "dt", "m", "w", "n", "r", "k1", "k2"];
window.__보냄 = "#보냄";
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 로케일 html21b-23-locale.html ko-KR de-DE
[ko-KR]  navigator.language = ko-KR · 요청 1번
  Accept-Language  ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7
  본문  「d=2026-09-26&t=13%3A05&dt=2026-09-26T13%3A05&m=2026-09&w=2026-W39&n=1234.5&r=50&k1=15&k2=1.5」
[de-DE]  navigator.language = de-DE · 요청 1번
  Accept-Language  de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7
  본문  「d=2026-09-26&t=13%3A05&dt=2026-09-26T13%3A05&m=2026-09&w=2026-W39&n=1234.5&r=50&k1=1.5&k2=1.5」

칸   화면(ko-KR)               화면(de-DE)               서버(ko-KR)         서버(de-DE)
d    "2026. 09. 26."           "26.09.2026"              "2026-09-26"        "2026-09-26"
t    "오후 01:05"              "13:05"                   "13:05"             "13:05"
dt   "2026. 09. 26. 오후 01:05" "26.09.2026, 13:05"       "2026-09-26T13:05"  "2026-09-26T13:05"
m    "2026년 9월"              "September 2026"          "2026-09"           "2026-09"
w    "2026, 39번째 주"         "Woche 39, 2026"          "2026-W39"          "2026-W39"
n    "1234.5"                  "1234,5"                  "1234.5"            "1234.5"
r    ""                        ""                        "50"                "50"
k1   "15"                      "1,5"                     "15"                "1.5"
k2   "1.5"                     "1.5"                     "1.5"               "1.5"
화면 글자가 갈린 칸 = 7 / 9
서버 값이 갈린 칸 = 1 / 9
(exit 0)
```

- ★★★ **서버 값이 갈린 칸은 1 / 9**, **화면 글자가 갈린 칸은 7 / 9** 다. 날짜·시각·달·주·수 여섯 칸의 서버 값이 **두 로케일에서 한 글자도 같다** — `2026-09-26` · `13:05` · `2026-09-26T13:05` · `2026-09` · `2026-W39` · `1234.5`.
- ★★★ **화면은 로케일대로다** — 날짜가 `2026. 09. 26.` 대 `26.09.2026`(순서가 뒤집혔다), 시각이 `오후 01:05` 대 `13:05`(12 / 24시간제), 달이 `2026년 9월` 대 `September 2026`, 수가 `1234.5` 대 `1234,5`(소수점 기호). 명세의 비규범 절 — 「날짜·시간·숫자 칸에서 사용자에게 보여 주는 형식은 **폼 제출에 쓰이는 형식과 독립**이다. 브라우저는 **입력 요소의 언어나 사용자의 선호 로케일**의 관례를 따르라고 권한다」. ★ 이 페이지는 `lang="ko"` 인데 de-DE 판은 독일식으로 보였다 — **이 판은 페이지 언어가 아니라 사용자 로케일을 따랐다**(관찰).
- ★★★ **갈린 한 칸은 사람이 친 `k1`** 이다 — 같은 키 `1,5` 가 **ko-KR 에서 `15`, de-DE 에서 `1.5`** 가 됐다. ko-KR 의 쉼표는 **천 단위 구분**이라 버려졌고, de-DE 의 쉼표는 **소수점**이다. 화면에도 ko 는 `15`, de 는 `1,5` 로 남았다. **「값은 로케일 무관 형식」은 제출 값의 형식 이야기이지 입력 해석 이야기가 아니다.** `.`으로 친 `k2` 는 두 로케일 다 `1.5` 였다.
- **`range` 의 화면 글자는 비어 있다** — 트리에 `StaticText` 가 없다(손잡이만 있다). 서버 값은 둘 다 `50` 이다((4)).
날짜 칸 하나가 트리에서 어떻게 생겼나 — 하네스가 이어 붙인 「화면 글자」의 재료다(ko-KR).

```text
$ python3 html21b-form.py --lang=ko-KR ax html21b-23-locale.html | sed -n '1,17p'
RootWebArea    이름='23 두 로케일'
  form           이름=''
    Date           이름='날짜'
      generic        이름=''
        generic        이름=''
          spinbutton     이름='연도 연도'
            StaticText     이름='2026'
          StaticText     이름='. '
          spinbutton     이름='월 월'
            StaticText     이름='09'
          StaticText     이름='. '
          spinbutton     이름='일 일'
            StaticText     이름='26'
          StaticText     이름='.'
      button         이름='날짜 선택도구 표시'
    InputTime      이름='시각'
      generic        이름=''
(exit 0)
```

- ★ **날짜 칸은 `Date` 역할 아래 `spinbutton` 셋과 사이 글자(`. `)로 풀려 있다** — 하네스의 「화면 글자」는 이 `StaticText` 들을 순서대로 이은 것이고, **「날짜 선택도구 표시」 단추**는 뺐다. HTML-AAM 은 `input type=date` 를 「**대응하는 역할 없음**」(계산된 역할 `html-input-date`)으로 적는다 — `Date` 는 Chrome 의 이름이다.
- ★ **`Accept-Language` 도 로케일을 따라 바뀌었다** — `ko-KR,ko;q=0.9,…` 대 `de-DE,de;q=0.9,…`. **서버가 로케일을 알고 싶으면 이 헤더**를 본다 — 폼 값에는 안 들어 있다.

```text
  같은 제출에서 로케일이 닿는 곳과 안 닿는 곳

                          ko-KR               de-DE               로케일을 타나
  화면 글자 (⑦)          2026. 09. 26.       26.09.2026          ★ 탄다 (7 / 9)
  사람이 친 "1,5" 의 값   15                  1.5                 ★ 탄다 — 입력 해석
  .value · 제출 값 (⑤)    2026-09-26 …        2026-09-26 …        안 탄다 (8 / 9 같음)
  Accept-Language          ko-KR,…             de-DE,…             ★ 탄다 — 헤더
```

### (2) 창 ② — `.value` · `valueAsNumber` · `valueAsDate`

**언제 쓰나** — 입력 값을 **수나 `Date` 로** 받아 계산할 때, 그리고 틀린 값이 **무엇으로 정화되나**를 알 때.

```html
<!-- html21b-23-values.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 값과 valueAs</title>
</head>
<body>
<input id="d1" type="date" value="2026-09-26">
<input id="d2" type="date" value="2026-02-30">
<input id="d3" type="date" value="26.09.2026">
<input id="t1" type="time" value="13:05:30.5">
<input id="dt1" type="datetime-local" value="2026-09-26 13:05">
<input id="m1" type="month" value="2026-09">
<input id="w1" type="week" value="2026-W53">
<input id="w2" type="week" value="2026-W39">
<input id="n1" type="number" value="010-1234-5678">
<input id="n2" type="number" value="01012345678">
<input id="n3" type="number" value="1e3">
<input id="n4" type="number" value=" 12 ">
<time id="시각" datetime="2026-02-30">2월 30일</time>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const J = v => JSON.stringify(v);
const 시도 = f => { try { return String(f()); } catch (e) { return e.name + " 「" + e.message + "」"; } };
window.__끝 = () => {
  const O = [칸("id", 5) + 칸("value 속성", 18) + 칸(".value", 22) + 칸("valueAsNumber", 16) + "valueAsDate"];
  for (const i of document.querySelectorAll("input")) {
    O.push(칸(i.id, 5) + 칸(J(i.getAttribute("value")), 18) + 칸(J(i.value), 22) + 칸(String(i.valueAsNumber), 16)
      + 시도(() => i.valueAsDate === null ? "null" : i.valueAsDate.toISOString()));
  }
  const 비움 = [...document.querySelectorAll("input")].filter(i => i.getAttribute("value") && i.value === "");
  O.push("속성 값이 있는데 .value 가 빈 문자열이 된 칸 = " + 비움.map(i => i.id).join(" · ") + " → " + 비움.length + " / " + document.querySelectorAll("input").length);
  O.push("");
  const n1 = document.getElementById("n1");
  O.push("n1 에 스크립트로 넣기");
  O.push("  n1.value = \"010-1234\" 뒤 .value = " + (n1.value = "010-1234", J(n1.value)));
  O.push("  n1.valueAsNumber = 101234 뒤 .value = " + (n1.valueAsNumber = 101234, J(n1.value)));
  O.push("  n1.valueAsDate = new Date(0) → " + 시도(() => { n1.valueAsDate = new Date(0); return "예외 없음"; }));
  O.push("");
  const t = document.getElementById("시각");
  O.push("time 요소 datetime=\"2026-02-30\" → .dateTime = " + J(t.dateTime));
  O.push("date 입력 value=\"2026-02-30\" → .value = " + J(document.getElementById("d2").value));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py --lang=ko-KR page html21b-23-values.html
id   value 속성        .value                valueAsNumber   valueAsDate
d1   "2026-09-26"      "2026-09-26"          1790380800000   2026-09-26T00:00:00.000Z
d2   "2026-02-30"      ""                    NaN             null
d3   "26.09.2026"      ""                    NaN             null
t1   "13:05:30.5"      "13:05:30.5"          47130500        1970-01-01T13:05:30.500Z
dt1  "2026-09-26 13:05" "2026-09-26T13:05"    1790427900000   null
m1   "2026-09"         "2026-09"             680             2026-09-01T00:00:00.000Z
w1   "2026-W53"        "2026-W53"            1798416000000   2026-12-28T00:00:00.000Z
w2   "2026-W39"        "2026-W39"            1789948800000   2026-09-21T00:00:00.000Z
n1   "010-1234-5678"   ""                    NaN             null
n2   "01012345678"     "01012345678"         1012345678      null
n3   "1e3"             "1e3"                 1000            null
n4   " 12 "            ""                    NaN             null
속성 값이 있는데 .value 가 빈 문자열이 된 칸 = d2 · d3 · n1 · n4 → 4 / 12

n1 에 스크립트로 넣기
  n1.value = "010-1234" 뒤 .value = ""
  n1.valueAsNumber = 101234 뒤 .value = "101234"
  n1.valueAsDate = new Date(0) → InvalidStateError 「Failed to set the 'valueAsDate' property on 'HTMLInputElement': This input element does not support Date values.」

time 요소 datetime="2026-02-30" → .dateTime = "2026-02-30"
date 입력 value="2026-02-30" → .value = ""
(exit 0)
```

- ★★★ **없는 날짜 `2026-02-30` 은 `.value` 가 빈 문자열**이다 — 정화 알고리즘 「값이 **유효한 날짜 문자열이 아니면** 빈 문자열로 둔다」. 로케일 꼴 `26.09.2026` 도 빈 문자열이다. ★ **대비** — 같은 `2026-02-30` 을 **`time` 요소의 `datetime`** 에 두면 `.dateTime` 이 **그대로** `"2026-02-30"` 이다. [14번](../14-quotation-edits-and-time/2-summary.md)의 결론 「**검증자가 없다**」 — `time` 요소는 해석하지 않는 반영이고, **`input type=date` 는 정화가 있다.**
- ★★ **`datetime-local` 은 공백을 `T` 로 고친다** — `"2026-09-26 13:05"` → `"2026-09-26T13:05"`. 정화가 「유효한 로컬 날짜·시각 문자열이면 **정규화된** 꼴로」 바꾼다.
- ★★ **`valueAsNumber` 는 타입마다 단위가 다르다** — `date`·`week`·`datetime-local` 은 **1970-01-01 UTC 부터의 밀리초**, `time` 은 **자정부터의 밀리초**(`47130500` = 13:05:30.5), **`month` 는 1970년 1월부터의 달 수**(`680`).
- **`valueAsDate`** — `date`·`month`·`week`·`time` 은 **UTC 자정 기준 `Date`**(`week` 는 그 주의 **월요일**, `2026-W53` → `2026-12-28`). **`datetime-local` 과 `number` 는 `null`** — 명세가 두 타입에 이 속성을 **「적용하지 않는다」** 로 두었다.
- ★★★ **`number` 의 전화번호** — `"010-1234-5678"` 은 **빈 문자열**(유효한 부동소수 수가 아니다). `"01012345678"` 은 **글자로는 앞의 0 이 남는다**, 그러나 **`valueAsNumber` 는 `1012345678`** 이다. `"1e3"` 은 유효한 수라 그대로 남고, **`" 12 "`(앞뒤 공백)은 빈 문자열**이다 — `number` 는 공백을 **손질하지 않고 버린다.**
- ★ **`number` 에 `valueAsDate` 를 넣으면 `InvalidStateError`** — 명세 — 「적용되지 않는 상태에서 설정하면 **`InvalidStateError` DOMException** 을 던진다」.

### (3) 창 ② + 창 ⑤ — `number` 에 전화번호를 쳐 넣으면

**언제 쓰나** — 「숫자만 받으니 `type=number` 로 하자」는 결정을 반증할 때.

(2) 가 **속성**으로 넣었다면 여기는 **진짜로 친다**(`Input.insertText`). `tel` 두 칸을 짝으로 두었다.

```html
<!-- html21b-23-phone.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 number 에 전화번호</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post" novalidate>
<input id="n1" name="n1" type="number" aria-label="number 1">
<input id="n2" name="n2" type="number" aria-label="number 2">
<input id="t1" name="t1" type="tel" aria-label="tel 1">
<input id="t2" name="t2" type="tel" aria-label="tel 2">
<button id="보냄">보냄</button>
</form>
<script>
const 칸들 = ["n1", "n2", "t1", "t2"];
const 입력 = [["type", "#n1", "010-1234"], ["type", "#n2", "0101234"], ["type", "#t1", "010-1234"], ["type", "#t2", "0101234"]];
window.__읽기 = () => 칸들.map(id => {
  const e = document.getElementById(id);
  return id + " .value=" + JSON.stringify(e.value) + " badInput=" + e.validity.badInput + " valueAsNumber=" + e.valueAsNumber;
}).join(" · ");
window.__시도 = [
  { 이름: "입력만 하고 읽기", 단계: 입력, 뒤: "__읽기()" },
  { 이름: "입력하고 보내기", 단계: [...입력, ["click", "#보냄"]] },
  { 이름: "n2·t2 에서 위쪽 화살표 한 번", 단계: [...입력, ["key", "#n2", "ArrowUp", "ArrowUp", 38], ["key", "#t2", "ArrowUp", "ArrowUp", 38]], 뒤: "__읽기()" },
];
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py 시도 html21b-23-phone.html
[입력만 하고 읽기]
  페이지  (기록 없음)
  뒤      n1 .value="" badInput=true valueAsNumber=NaN · n2 .value="0101234" badInput=false valueAsNumber=101234 · t1 .value="010-1234" badInput=false valueAsNumber=NaN · t2 .value="0101234" badInput=false valueAsNumber=NaN
  서버    (받은 요청 없음)
[입력하고 보내기]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「n1=&n2=0101234&t1=010-1234&t2=0101234」
          필드  n1=「」 · n2=「0101234」 · t1=「010-1234」 · t2=「0101234」
[n2·t2 에서 위쪽 화살표 한 번]
  페이지  (기록 없음)
  뒤      n1 .value="" badInput=true valueAsNumber=NaN · n2 .value="101235" badInput=false valueAsNumber=101235 · t1 .value="010-1234" badInput=false valueAsNumber=NaN · t2 .value="0101234" badInput=false valueAsNumber=NaN
  서버    (받은 요청 없음)
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`010-1234` 를 친 `number` 는 `.value` 가 빈 문자열이고 `badInput` 이 참**이다 — 칸에는 글자가 **보이는데**(사용자는 쳤다) 값은 **없다.** 서버에는 **`n1=「」`** 가 갔다. `tel` 은 `010-1234` 그대로다.
- ★★★ **`0101234` 는 값이 `"0101234"` 로 남지만, 위쪽 화살표 한 번에 `"101235"`** 가 된다 — **앞의 0 이 사라졌다.** 스핀 단추는 값을 **수로** 더한다. `tel` 칸의 화살표는 **아무것도 안 바꿨다.**
- ★★ 명세가 이 경우를 직접 든다 — 「`type=number` 는 **숫자로만 이루어졌지만 엄밀히 말해 수가 아닌** 입력에 알맞지 않다. 예컨대 **신용카드 번호나 미국 우편번호**. … 스핀 박스(위아래 화살표)가 말이 되는가로 판단하라. … 알맞지 않으면 **`type=text`(필요하면 `inputmode`·`pattern` 과 함께)** 가 아마 맞다」. 전화번호도 **위아래 화살표로 고를 값이 아니다.**

```text
  "010-1234" 와 "0101234" 가 number 칸에서 겪는 일

  친 글자      .value        badInput   valueAsNumber   서버        위 화살표 뒤
  010-1234     ""            true       NaN             n1=「」      (없음)
  0101234      "0101234"     false      101234          n2=「0101234」  "101235"  ★ 0 이 사라짐
  (tel) 둘     그대로         false      NaN             그대로       그대로
```

### (4) 창 ② — `range` 는 빈 값이 없다 · `min`/`max`/`step` 의 깃발

**언제 쓰나** — 슬라이더의 초깃값을 안 줬을 때 서버가 무엇을 받나, 범위 밖 값이 **막히나 고쳐지나**를 알 때.

```html
<!-- html21b-23-range.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>23 범위와 눈금</title>
</head>
<body>
<input id="r1" type="range">
<input id="r2" type="range" min="0" max="10">
<input id="r3" type="range" min="0" max="5" step="2">
<input id="r4" type="range" value="">
<input id="r5" type="range" value="abc">
<input id="r6" type="range" value="200">
<input id="r7" type="range" min="10" max="0">
<input id="a1" type="number" min="0" max="10" value="11">
<input id="a2" type="number" step="0.5" value="1.3">
<input id="a2s" type="number" step="0.5">
<input id="a3" type="number" value="1.5">
<input id="a4" type="date" min="2026-01-01" value="2025-12-31">
<input id="a5" type="date" step="7" min="2026-09-07" value="2026-09-10">
<input id="a6" type="time" step="900" value="13:07">
<input id="a6s" type="time" step="900">
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const J = v => JSON.stringify(v);
document.getElementById("a2s").value = "1.3";      // 스크립트로 넣은 값
document.getElementById("a6s").value = "13:07";
const 깃발 = ["rangeUnderflow", "rangeOverflow", "stepMismatch", "badInput", "valueMissing"];
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("속성", 52) + 칸(".value", 14) + "켜진 validity 깃발"];
  for (const i of document.querySelectorAll("input")) {
    const 속성 = [...i.attributes].filter(a => a.name !== "id").map(a => a.name + "=" + J(a.value)).join(" ");
    const 켜짐 = 깃발.filter(k => i.validity[k]);
    O.push(칸(i.id, 4) + 칸(속성, 52) + 칸(J(i.value), 14) + (켜짐.join(" · ") || "(없음)"));
  }
  O.push("");
  O.push("validationMessage 전문 (비어 있지 않은 것만)");
  for (const i of document.querySelectorAll("input")) if (i.validationMessage) O.push("  " + i.id + "  " + i.validationMessage);
  O.push("");
  O.push("a2 와 a2s · a6 와 a6s 는 값이 같다 — 차이는 속성으로 넣었나 스크립트로 넣었나");
  for (const [x, y] of [["a2", "a2s"], ["a6", "a6s"]]) {
    const X = document.getElementById(x), Y = document.getElementById(y);
    O.push("  " + x + " stepMismatch = " + X.validity.stepMismatch + " · " + y + " stepMismatch = " + Y.validity.stepMismatch);
  }
  const 범위 = [...document.querySelectorAll("input[type=range]")];
  O.push("");
  O.push("range 에서 .value 가 빈 문자열인 칸 = " + 범위.filter(i => i.value === "").length + " / " + 범위.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py --lang=ko-KR page html21b-23-range.html
id  속성                                                .value        켜진 validity 깃발
r1  type="range"                                        "50"          (없음)
r2  type="range" min="0" max="10"                       "5"           (없음)
r3  type="range" min="0" max="5" step="2"               "2"           (없음)
r4  type="range" value=""                               "50"          (없음)
r5  type="range" value="abc"                            "50"          (없음)
r6  type="range" value="200"                            "100"         (없음)
r7  type="range" min="10" max="0"                       "10"          (없음)
a1  type="number" min="0" max="10" value="11"           "11"          rangeOverflow
a2  type="number" step="0.5" value="1.3"                "1.3"         (없음)
a2s type="number" step="0.5"                            "1.3"         stepMismatch
a3  type="number" value="1.5"                           "1.5"         (없음)
a4  type="date" min="2026-01-01" value="2025-12-31"     "2025-12-31"  rangeUnderflow
a5  type="date" step="7" min="2026-09-07" value="2026-09-10" "2026-09-10"  stepMismatch
a6  type="time" step="900" value="13:07"                "13:07"       (없음)
a6s type="time" step="900"                              "13:07"       stepMismatch

validationMessage 전문 (비어 있지 않은 것만)
  a1  값은 10 이하여야 합니다.
  a2s  유효한 값을 입력해 주세요. 가장 근접한 유효 값 2개는 1 및 1.5입니다.
  a4  값은 2026. 01. 01. 이후여야 합니다.
  a5  유효한 값을 입력해 주세요. 가장 근접한 유효 값 2개는 2026. 09. 07. 및 2026. 09. 14.입니다.
  a6s  유효한 값을 입력해 주세요. 가장 근접한 유효 값 2개는 오후 1:00 및 오후 1:15입니다.

a2 와 a2s · a6 와 a6s 는 값이 같다 — 차이는 속성으로 넣었나 스크립트로 넣었나
  a2 stepMismatch = false · a2s stepMismatch = true
  a6 stepMismatch = false · a6s stepMismatch = true

range 에서 .value 가 빈 문자열인 칸 = 0 / 7
(exit 0)
```

- ★★★ **`range` 일곱 칸 중 `.value` 가 빈 문자열인 칸은 0 / 7** 이다. 값을 안 주면 **`50`**, `min=0 max=10` 이면 **`5`** — 명세의 기본값 「**최솟값 + (최댓값 − 최솟값)의 절반**」. `value=""`·`"abc"` 도 `50`, **`200` 은 `100`**(최댓값으로 **고쳐졌다**), `max < min` 이면 **최솟값 `10`**.
- ★★ **`range` 는 고치고, `number` 는 깃발만 켠다** — `number` 의 `11`(`max=10`)은 값이 **그대로 `11`** 이고 `rangeOverflow` 가 켜졌다. `range` 의 넘침은 명세가 「UA 는 값을 최댓값으로 **바꿔야 한다**」로 적는다. 그래서 **`range` 는 무효가 될 수 없다** — 모든 칸의 깃발이 `(없음)` 이다.
- ★ **`step` 이 중간값을 비껴가면 가까운 눈금으로** — `min=0 max=5 step=2` 의 기본값 2.5 는 **`2`** 가 됐다(명세: 「가장 가까운 눈금, 둘이면 양의 무한대 쪽」 — 2 와 4 중 2.5 에 가까운 것은 2).
- ★★★ **같은 값이 속성으로 넣으면 `stepMismatch` 가 꺼지고, 스크립트로 넣으면 켜진다** — `a2`(`value="1.3"`)는 `(없음)`, `a2s`(스크립트 `.value = "1.3"`)는 `stepMismatch`. `time` 도 같다(`a6`/`a6s`). ★ 명세의 step mismatch 줄 — 「허용 눈금이 있고, 값을 수로 바꾼 것이 눈금의 정수배가 아니면 **step mismatch 를 겪는다**」 — 에는 **값이 어떻게 들어왔나를 묻는 조건이 없다.** 이 판은 **갈렸다**(아래 「구현 세부사항 대 언어 보장」). 그런데 **`date` 는 속성으로 넣어도 켜졌다**(`a5`) — 한 구현 안에서도 타입마다 다르다.
- **문구**(ko-KR) — `rangeOverflow` 「값은 10 이하여야 합니다.」, `stepMismatch` 「가장 근접한 유효 값 2개는 1 및 1.5입니다.」. 날짜·시각 문구 안의 값은 **로케일 형식**(`2026. 01. 01.`·`오후 1:00`)이다 — 문구는 사람에게 보여 줄 것이라 그렇다. **근거는 깃발이다.**

```text
  범위 밖 값 — range 와 number 가 다르게 군다

             value 속성   .value    깃발             명세
  range       200         "100"     (없음)           넘치면 최댓값으로 「바꿔야 한다」
  number      11 (max 10) "11"      rangeOverflow    깃발만 — 제출 때 막힌다
  range       (없음)       "50"      (없음)           기본값 = min + (max − min) / 2
```

### demo — 값을 안 준 슬라이더

```html demo
<!-- html21b-23-demo.html -->
<input type="range">
<input type="range" min="0" max="10">
<input type="range" value="200">
<style>
  input { display: block; width: 240px; margin: 8px; }
</style>
```

> **보이는 것** — 세 슬라이더 중 **위의 둘은 손잡이가 한가운데**, 셋째(`value="200"`)는 **오른쪽 끝**이다. 값을 안 줬는데 가운데에서 시작한다.\
> **바꿔 볼 것** — 둘째의 `max="10"` 을 `max="20"` 으로 바꿔도 손잡이는 **가운데**다(값이 `10` 이 된다 — (4) 의 「최솟값 + 절반」)

*(Chrome 151 headless 실측, 창 폭 1000: `.value` 가 `50` · `5` · `100`, (value − min)/(max − min) 이 50% · 50% · 100%. ★ 손잡이의 픽셀 위치를 잰 것이 아니라 **값에서 계산한 비율**이다. 검증 파일은 아래)*

```html
<!-- html21b-23-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 23 검증</title>
<body>
<input type="range">
<input type="range" min="0" max="10">
<input type="range" value="200">
<style>
  input { display: block; width: 240px; margin: 8px; }
</style>
<script>
const O = [];
for (const i of document.querySelectorAll("input")) {
  O.push("min=" + i.min.padEnd(3) + " max=" + i.max.padEnd(3) + " value 속성=" + JSON.stringify(i.getAttribute("value")).padEnd(6)
    + " .value=" + JSON.stringify(i.value) + " · (value−min)/(max−min) = " + ((i.valueAsNumber - (i.min === "" ? 0 : +i.min)) / ((i.max === "" ? 100 : +i.max) - (i.min === "" ? 0 : +i.min)) * 100) + "%");
}
document.body.append(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html21b-23-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
min=    max=    value 속성=null   .value="50" · (value−min)/(max−min) = 50%
min=0   max=10  value 속성=null   .value="5" · (value−min)/(max−min) = 50%
min=    max=    value 속성="200"  .value="100" · (value−min)/(max−min) = 100%
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | `.value`·제출 값의 꼴 |
|---|---|---|
| 날짜 | `type="date"` | `2026-09-26` |
| 시각 | `type="time"` | `13:05` (초·소수 초 가능 `13:05:30.5`) |
| 날짜와 시각(시간대 없음) | `type="datetime-local"` | `2026-09-26T13:05` — 공백은 `T` 로 정규화 |
| 달 | `type="month"` | `2026-09` |
| 주 | `type="week"` | `2026-W39` |
| 수 | `type="number"` | `1234.5` · `1e3` — 소수점은 **언제나 `.`** |
| 대충의 수(슬라이더) | `type="range"` | 빈 값 없음 — 기본은 **가운데** |
| 수가 아닌 숫자열(전화·카드·우편번호) | ★ `type="text"`/`"tel"` + `inputmode`·`pattern` | 글자 그대로 |

### 어디서 헷갈리나

- **표시 형식과 값 형식은 따로다** — 화면이 `26.09.2026` 이어도 서버는 `2026-09-26` 을 받는다.
- **입력 해석은 로케일을 탄다** — `1,5` 는 ko-KR 에서 `15` 다.
- **`number` 는 「숫자로 된 글자」가 아니라 「수」다** — 앞의 0·하이픈·공백이 살아남지 못한다.
- **`range` 는 무효가 안 된다** — 값이 고쳐지므로 서버는 **언제나 어떤 수**를 받는다.

## 어디서 틀리나

### 1. 서버가 사용자 로케일마다 날짜 파서를 바꾼다

**필요 없다** — 제출 값은 두 로케일에서 **같았다**((1) — 서버 값 갈린 칸은 사람이 친 `k1` 하나). 로케일이 필요하면 **`Accept-Language` 헤더**를 본다.

### 2. 「값은 로케일 무관」이니 숫자 입력도 로케일과 무관하다고 여긴다

**입력 해석은 로케일을 탄다** — `1,5` 가 ko-KR 에서 `15`, de-DE 에서 `1.5`((1) 의 `k1`). **같은 키가 열 배 다른 값**이 됐다.

### 3. 전화번호·우편번호를 `type="number"` 로 받는다

**하이픈이 들어가면 값이 사라지고**(`n1=「」`), **0 으로 시작하면 화살표 한 번에 0 이 사라진다**(`101235`)((3)). 명세도 「알맞지 않다」고 적는다. `tel` 또는 `text` + `inputmode="numeric"` 을 쓴다.

### 4. `max` 를 넘는 값은 브라우저가 알아서 고쳐 준다고 여긴다

**`range` 만 고친다** — `number`·`date` 는 **깃발만** 켠다((4)). `novalidate` 폼이면 그 값이 **그대로 간다**([21번](../21-form-submission-model/2-summary.md)의 (5)).

### 5. `valueAsNumber` 를 모든 타입에서 같은 단위로 읽는다

**`month` 는 달 수**(`680`), **`time` 은 자정부터의 밀리초**다((2)). `date` 만 보고 짠 코드가 `month` 에서 1970년 1월 1일 근처 값을 만든다.

### 6. 틀린 날짜 문자열도 `input type=date` 가 그대로 들고 있으리라 여긴다

**빈 문자열이 된다**((2) 의 `d2`·`d3`). 그대로 들고 있는 것은 **`time` 요소의 `datetime`** 쪽이다([14번](../14-quotation-edits-and-time/2-summary.md)).

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 각 타입의 `.value` 꼴(유효한 날짜·시각·달·주 문자열 · 유효한 부동소수 수) — 어긋나면 **빈 문자열로 정화** | (2) |
| **명세(HTML · 비규범)** | 사용자에게 보여 주는 형식은 **제출 형식과 독립** · 입력 요소의 언어나 사용자 로케일을 따르라고 **권한다** | (1) |
| **명세(HTML)** | `valueAsNumber` 의 단위(타입별 「문자열을 수로」) · `valueAsDate` 는 `datetime-local`·`number` 에 **적용 안 됨** → 읽으면 `null`, 쓰면 `InvalidStateError` | (2) |
| **명세(HTML)** | `range` 의 기본값 = 최솟값 + 절반 · 넘치면 최댓값으로 **바꿔야 한다** · 눈금은 가까운 쪽 | (4) |
| **명세(HTML)** | step mismatch 는 **값이 들어온 경로를 묻지 않는다** | (4) |
| **명세(HTML)** | `type=number` 는 수가 아닌 숫자열(카드 번호·우편번호)에 **알맞지 않다** | (3) |
| ★ **구현(Chrome) — 명세와 갈림** | `number`·`time` 은 **속성으로 넣은 값에 `stepMismatch` 를 안 켠다**(스크립트로 넣으면 켠다) · `date` 는 속성으로도 켠다 | (4) |
| **구현(Chrome)** | 화면 형식을 **페이지 `lang` 이 아니라 사용자 로케일**로 골랐다 · ko-KR 의 `,` 를 **천 단위 구분**으로 읽어 버렸다 | (1) |
| **구현(Chrome · 리눅스)** | `--lang` 플래그를 **안 듣고** `LANGUAGE` 환경 변수를 듣는다 | (1) |
| **이 판의 관찰** | 두 로케일의 제출 값이 같았다 | (1) — 다른 엔진은 **미실행** |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **날짜 선택 창(달력)·시각 선택 창** | 트리에는 「선택도구 표시」 **단추**까지만 있다 — 창은 **페이지 밖 UI** 이고 헤드리스에서 열지 않았다. 「못 잰 것」 |
| **화면 글자의 모양**(글꼴·자리·색) | 창 ⑦ 은 **글자와 순서**까지다(제5의 상태의 한계) |
| **모바일의 날짜 휠·숫자 자판** | 입력기가 없다 — [22번](../22-input-types-text/2-summary.md)과 같은 제3의 상태 |
| **스크린리더가 날짜 칸을 어떻게 읽나** | 보조 기술이 없다. 트리의 `spinbutton` 과 그 이름까지다((1) 의 트리 블록) |
| **다른 로케일(아랍 숫자·태국력 등)** | 두 로케일만 던졌다 — 안 돌려 본 것 |

## 언제 쓰고 언제 안 쓰나

- **날짜·시각은 전용 타입** — 서버는 ISO 꼴 하나만 파싱하면 된다. 로케일 표시는 브라우저가 한다.
- **시간대가 필요하면 `datetime-local` 만으로는 부족하다** — 이름 그대로 **시간대 없는** 값이다. 시간대는 따로 받는다.
- **스핀 단추가 말이 되는 수만 `number`** — 수량·나이. 전화·카드·우편번호·계좌번호는 **`text`/`tel` + `inputmode`**.
- **대충의 값이면 `range`** — 서버는 **언제나 범위 안의 수**를 받는다. 정확한 값이 필요하면 `number` 를 곁에 둔다.
- **사람이 친 소수는 로케일을 탄다** — 소수가 중요한 칸이면 **확인 표시**(`output` 등)를 곁에 둔다.

## 핵심 문장

1. **날짜·숫자 칸의 제출 값은 로케일 무관 형식이다 — 두 로케일에서 서버 값이 같았고 화면 글자는 7 / 9 칸이 달랐다.**
2. **그러나 입력 해석은 로케일을 탄다 — 같은 `1,5` 가 ko-KR 에서 `15`, de-DE 에서 `1.5` 가 됐다.**
3. **`number` 에 `010-1234` 를 치면 값이 빈 문자열이고, `0101234` 는 화살표 한 번에 `101235` 가 된다.**
4. **틀린 날짜는 빈 문자열로 정화된다 — `time` 요소의 `datetime` 은 그대로 둔다.**
5. **`valueAsNumber` 의 단위는 타입마다 다르다 — `month` 는 달 수, `time` 은 자정부터의 밀리초.**
6. **`range` 는 빈 값이 없다 — 기본은 가운데, 넘치면 끝으로 고친다.**
7. **Chrome 은 속성으로 넣은 `number`·`time` 값에 `stepMismatch` 를 켜지 않았다 — 명세에는 그런 조건이 없다.**

## 관련 자료

- [22번 주제](../22-input-types-text/2-summary.md) — **값 정화와 `validity` 깃발**의 첫 편. 여기는 그것의 숫자·날짜 판.
- [14번 주제 — 인용·편집·시각](../14-quotation-edits-and-time/2-summary.md) — **`time` 요소의 `datetime` 에는 검증자가 없다**의 정본. 여기는 **`input type=date` 는 정화가 있다**는 대비까지.
- [21번 주제](../21-form-submission-model/2-summary.md) — 서버 요청 로그 하네스와 `novalidate`.
- [24번 주제](../24-input-types-choice-special/2-summary.md) — 선택·특수 타입.
- 목록의 **28번 주제**(`min`/`max`/`step` 의 눈금 규칙) · **30번 주제**(`inputmode`) · **33번 주제**(`output`).

## 용어 풀이

- **로케일** — 언어 + 지역 관례. 날짜 순서·소수점·시간제를 정한다.
- **`Accept-Language`** — 브라우저가 선호 언어를 서버에 알리는 요청 헤더.
- **유효한 날짜 문자열(valid date string)** — `YYYY-MM-DD`. 없는 날(2월 30일)은 유효하지 않다.
- **유효한 부동소수 수(valid floating-point number)** — `-`? 숫자 · 소수부 · 지수부. 공백·하이픈은 안 된다.
- **`badInput`** — 칸에 보이는 글자를 **값으로 바꿀 수 없을 때** 참인 깃발.
- **`valueAsNumber` / `valueAsDate`** — 값을 수 / `Date` 로 읽는 프로퍼티. 타입마다 단위가 다르다.
- **스핀 박스(spinbox)** — `number` 의 위아래 단추·화살표. 값을 **수로** 더하고 뺀다.
- **step mismatch** — 값이 눈금(`step`)에 안 맞는 것.
- **제5의 상태** — 같은 질문을 다른 창으로 물은 것. 여기서는 화면 표시를 **접근성 트리의 글자**로 물었다.

## 더 들어가면

- **왜 표시와 값을 갈랐나** — 명세의 비규범 절이 이유를 짧게 댄다 — **페이지의 로케일을 쓰면 페이지가 제공한 데이터와 표시가 일관된다.** 그러나 **제출 형식은 하나**여야 서버가 로케일마다 분기하지 않는다. 이 판은 **사용자 로케일**을 따랐다.
- **`week` 의 주 번호** — `2026-W53` 이 유효했다. 명세 — 「주 연도는 **1월 1일이 목요일인 해**(또는 1월 1일이 수요일인 윤년)면 **53주**, 나머지는 52주」 · 「주 연도 y 의 첫 주는 그레고리력 y 년의 **첫 목요일이 든 주**」 · 「오늘날의 쓰임에서 ISO 8601 의 주와 같다」. 이 판은 2026 년이 53주 해임을 **값이 정화되지 않은 것**으로 보였다(빈 문자열이 되지 않았다).
- **`datetime-local` 에 `valueAsDate` 가 없는 이유** — 시간대가 없는 값을 `Date`(시점)로 바꾸려면 **시간대를 골라야** 한다. 명세는 그 선택을 하지 않고 속성 자체를 **적용하지 않았다** — 이 문장은 해석이다.
