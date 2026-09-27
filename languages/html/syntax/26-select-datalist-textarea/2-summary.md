# html/syntax/26 — `select`/`option`/`optgroup`·`datalist`·`textarea` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The select element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-select-element)(★ **selectedness setting algorithm** · 표시 크기), [「The option element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-option-element)(값 = `value` 속성, 없으면 **HTML 인식 텍스트 내용**), [「The datalist element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-datalist-element)와 `list` 속성(「**제안**된 선택지」), [「The textarea element」](https://html.spec.whatwg.org/multipage/form-elements.html#the-textarea-element)(★ **원 값·API 값·값**의 세 가지 정규화 · 자식이 바뀔 때의 단계), [「Constructing the entry list」](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#constructing-the-form-data-set)·「이름·값 쌍 목록으로 바꾸기」(★ **줄바꿈을 CRLF 로**), [파싱 절의 `textarea` 시작 태그 줄](https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-inbody)·[직렬화 절](https://html.spec.whatwg.org/multipage/parsing.html#serialising-html-fragments), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/). **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다.**
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 제출은 **CDP 의 진짜 마우스**, 목록 밖 값은 **진짜 글자 입력**(`Input.insertText`)이다. 하네스는 [25번 주제](../25-label-association/3-answer.md)의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. ★ 명세의 `select` 절에는 **선택지를 CSS 로 꾸미는 새 모델**(`selectedcontent` 등 — 「Customizable `<select>`」)이 함께 들어 있다. 이 문서는 그 부분을 **재지 않았다** — 여기는 옛 모델의 **제출·값**까지다.
> **선행** — [24번 주제](../24-input-types-choice-special/2-summary.md)(서버가 받은 필드 목록으로 「안 실린다」를 증명하는 방식) · [04번 주제](../04-whitespace-and-character-references/2-summary.md)(`textarea` 첫 줄바꿈을 파서가 지우는 것 — (3) 절).
> **경계** — **`select` 를 스크립트로 다루는 표면**(`add()`·`remove()`·`selectedOptions` 의 살아 있는 목록)은 web-api 갈래의 몫이고, **`required` 인 `select` 의 빈 선택지**는 목록의 **29번 주제**(제약 검증)의 몫이다 — 여기는 **무엇이 실리나**와 **`textarea` 의 값이 어디서 오나**까지.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ⑤(서버 요청 로그)다.** 「`multiple` 에서 아무것도 안 고르면 **안 실린다**」·「목록 밖 값도 **실린다**」·「줄바꿈이 **CRLF 로** 간다」는 셋 다 **서버가 받은 바이트**로만 선다(`%0D%0A`). 짝으로 창 ②(`.value`·`selectedIndex`)와 창 ①(`--dump-dom`)이 **`textarea` 의 값이 속성이 아니라 자식 텍스트**임을 맡는다.

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
| **안 흔들린다** | 실린 필드와 그 순서 · 본문의 퍼센트 인코딩 · 「실린 칸 N / M」 | 같은 판이면 결정적이다 |
| **안 흔들린다** | `.value`·`selectedIndex`·`textContent`·`textLength` · 트리의 역할·이름 | 같은 판이면 결정적이다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑤ 서버 요청 로그** | ★ **쓴다 — 본체** | 어느 칸이 **실렸나 / 안 실렸나** · 같은 이름이 **몇 번** · 줄바꿈이 **무슨 바이트로**((1)) |
| **② 노드 프로브** | ★ **쓴다 — 본체의 짝** | `select` 의 `selectedIndex`·`selectedOptions`((1)) · `textarea` 의 `.value`·`textContent`·`defaultValue`((2)) |
| **① `--dump-dom`** | ★ **쓴다** | `textarea` 의 **직렬화** — `.value` 가 아니라 **자식 텍스트**가 나온다((2)) |
| **⑦ 접근성 트리** | 쓴다 | `optgroup` 의 **묶음과 이름** · `datalist` 가 트리에 있나((3)) |
| **③ `innerText` 대 `textContent`** | **부적용** | `textarea` 의 값은 렌더된 글자가 아니다 — ② 의 `textContent` 대 `.value` 가 그 자리를 맡았다 |
| **④ `compatMode`** · **⑥ `renderBlockingStatus`** | **부적용** | 무관하다 — 잴 것이 없다 |

- ★★★ **제4의 상태와 헷갈리지 마라 — 「안 실렸다」는 쟀고 비었다.** 페이지가 **칸 열넷의 필드 이름을 먼저 선언**하고(`__칸목록`), 하네스가 시도마다 **서버가 받은 필드 목록에서 찾았다**([24번](../24-input-types-choice-special/2-summary.md)과 같은 방식 — 규칙 18-A — **열네 곳을 물었다**).
- ★★ **제5의 상태 — 「CRLF 로 간다」를 화면이 아니라 서버가 받은 퍼센트 인코딩으로 물었다.** `.value` 는 **LF 로만** 답한다(API 값). 줄바꿈이 **보낼 때 바뀌는 것**은 본문의 **`%0D%0A`** 로만 보인다. ★ **바꾼 창이 못 보는 것** — `wrap="hard"` 가 넣는 줄바꿈(글꼴 폭에 달렸다)은 이 판이 던지지 않았다.

## 한눈에 — 쉽게 말하면

**★ 셋 다 「답을 적는 칸」인데 적는 방식이 다르다 — `select` 는 보기에 동그라미, `datalist` 는 보기가 딸린 빈칸, `textarea` 는 답안지 여백이다.**

시험지 비유다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **보기에 동그라미(하나만)** | `select` — 아무것도 안 치면 **첫 보기에 이미 동그라미가 쳐져 있다**(표시 크기 1 일 때) |
| **「해당하는 것을 모두 고르시오」** | `select multiple` — 고른 것마다 **같은 이름으로 한 번씩** 실린다 · ★ 하나도 안 고르면 **아예 없다** |
| **보기 번호 대신 보기 글자** | `value` 없는 `option` — **글자**(앞뒤·연속 공백을 정리한 것)가 실린다 |
| **보기 묶음 제목** | `optgroup label` — 묶음의 **이름**이 된다 · 실리지는 않는다 |
| **「예: 서울, 부산」이라고 써 둔 빈칸** | `datalist` — ★ **예시일 뿐**이다 · 목록에 없는 답도 실린다 |
| **답안지 여백에 쓴 글** | `textarea` — 값은 **자식 텍스트**다 · `value` **속성은 없는 것**과 같다 |
| **여백 첫 줄의 빈 줄** | `<textarea>` 바로 뒤의 줄바꿈 하나 — **파서가 지운다** |
| **채점실에 보낼 때 줄 끝 표시를 통일** | 제출 때 줄바꿈이 **CRLF(`\r\n`)** 로 바뀐다 |

- **`multiple` 은 `s=a&s=c` 처럼 같은 이름을 여러 번 싣는다**((1)).
- **`value=""` 인 선택지를 고르면 `s6=` 이 실린다** — 「안 실림」과 다르다((1)).
- ★★ **목록 밖 글자는 그대로 서버에 간다**((1)).
- ★★ **`textarea` 의 `value="…"` 는 무시된다** — 값은 태그 사이 글자다((2)).

```text
  세 칸이 값을 들고 있는 자리 — 제출에 실리는 것은 오른쪽 끝

  select       <option selected?> 들 ──(selectedness)──> 고른 option 의 값 ──> s=a   (multiple 이면 s=a&s=c)
                  └ 하나도 안 골랐고 표시 크기 1 ──> 첫 비활성 아닌 option 을 고른다
  input+list   사용자가 친 글자 ──────────────────────────────────────────────> d=아무 글자
                  └ datalist 는 옆에서 보기를 보여 줄 뿐
  textarea     자식 텍스트 ──(원 값)──> API 값(줄바꿈 LF) ──(제출)──> CRLF ──> t=첫%0D%0A둘
                  └ .value 로 한 번 쓰면(더러움 표시) 자식을 바꿔도 값이 안 따라온다
```

> **선택됨(selectedness)** — `option` 마다의 참/거짓 상태. `selected` **속성**은 그 초깃값이다.\
> 예: `<option selected>` 가 둘인 단일 `select` 는 **마지막 것만** 선택됨이 남는다.

> **API 값(API value)** — `textarea` 의 `.value` 가 돌려주는 값. 원 값의 줄바꿈을 **LF 로 통일**한 것이다.

## 이 주제가 답하려는 질문

1. **`select` 는 무엇을 싣나** — 아무것도 안 골랐을 때(단일·`multiple`·`size`) · 여럿 골랐을 때 · `value` 가 없을 때.
2. **`datalist` 는 입력을 제한하나** — 목록 밖 값, 그리고 `datalist` 안에 둔 칸.
3. **`textarea` 의 값은 어디서 오고 어떻게 바뀌어 나가나** — `value` 속성 · 자식 텍스트 · 첫 줄바꿈 · CRLF.

## 동작 방식

### (1) 창 ⑤ + 창 ② — 칸 열넷 × 두 인코딩

**언제 쓰나** — 서버가 「선택 안 함」을 **어떻게 받는지** 정할 때 · 자동완성 목록을 **검증으로 착각**하지 않으려고 할 때.

한 폼에 `select` 열 개 · 목록이 딸린 `input` · **`datalist` 안에 둔 `input`** · `textarea` 둘을 두고, 목록 밖 글자를 **진짜로 친 뒤** urlencoded 와 multipart 로 각각 보냈다.

```html
<!-- html25b-26-sent.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>26 무엇이 실리나</title>
<script src="html25b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post">
<select name="s1"><option value="a">가</option><option value="b">나</option></select>
<select name="s2"><option value="a" disabled>가</option><option value="b">나</option></select>
<select name="s3" multiple><option value="a">가</option><option value="b">나</option></select>
<select name="s4" multiple><option value="a" selected>가</option><option value="b">나</option><option value="c" selected>다</option></select>
<select name="s5"><option>  가   나  </option></select>
<select name="s6"><option value="" selected>고르세요</option><option value="b">나</option></select>
<select name="s7"><option value="a" selected>가</option><option value="b" selected>나</option></select>
<select name="s8" size="3"><option value="a">가</option><option value="b">나</option></select>
<select name="s9"><option value="a" disabled>가</option><option value="b" disabled>나</option></select>
<select name="s10"><option label="짧게">긴 글자</option></select>
<input name="d1" id="d1" list="목록">
<datalist id="목록"><option value="서울"></option><option value="부산"></option><input name="d2" value="목록 안의 칸"></datalist>
<textarea name="t1" value="속성 값">
첫 줄
둘째 줄</textarea>
<textarea name="t2" id="t2"></textarea>
<button id="보냄" name="b" value="보냄">보냄</button>
<button id="멀티" name="b" value="멀티" formenctype="multipart/form-data">멀티</button>
</form>
<script>
document.getElementById("t2").value = "첫\r둘\r\n셋\n넷";
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
window.__끝 = () => {
  const O = [칸("name", 5) + 칸("multiple·size", 15) + 칸(".value", 12) + 칸("selectedIndex", 14) + "selectedOptions"];
  for (const e of document.querySelectorAll("select")) {
    O.push(칸(e.name, 5) + 칸((e.multiple ? "multiple" : "—") + (e.hasAttribute("size") ? " size=" + e.size : ""), 15) + 칸(JSON.stringify(e.value), 12)
      + 칸(String(e.selectedIndex), 14) + JSON.stringify([...e.selectedOptions].map(o => o.value)));
  }
  O.push("");
  O.push("datalist 안의 input — willValidate=" + document.querySelector("[name=d2]").willValidate + " · form.elements 에 있나=" + [...document.getElementById("폼").elements].includes(document.querySelector("[name=d2]")));
  return O.join("\n");
};
window.__표 = "실린";
window.__칸목록 = [
  ["select · 고른 것 없음", "s1"], ["select · 첫 option 이 disabled", "s2"], ["select multiple · 고른 것 없음", "s3"],
  ["select multiple · 둘 고름", "s4"], ["select · value 없는 option", "s5"], ["select · value=\"\" 고름", "s6"],
  ["select · selected 둘", "s7"], ["select size=3 · 고른 것 없음", "s8"], ["select · option 전부 disabled", "s9"], ["option label=짧게 · 글자=긴 글자", "s10"],
  ["input list · 목록 밖 값", "d1"], ["datalist 안의 input", "d2"], ["textarea (자식 텍스트)", "t1"], ["textarea (스크립트 값)", "t2"],
];
window.__시도 = [
  { 이름: "목록 밖 값을 치고 보냄 클릭", 단계: [["type", "#d1", "목록에 없는 곳"], ["click", "#보냄"]] },
  { 이름: "목록 밖 값을 치고 멀티 클릭", 단계: [["type", "#d1", "목록에 없는 곳"], ["click", "#멀티"]] },
];
</script>
</body>
</html>
```

**먼저 창 ② — `select` 마다의 선택 상태**

```text
$ python3 html25b-form.py page html25b-26-sent.html
name multiple·size  .value      selectedIndex selectedOptions
s1   —             "a"         0             ["a"]
s2   —             "b"         1             ["b"]
s3   multiple       ""          -1            []
s4   multiple       "a"         0             ["a","c"]
s5   —             "가 나"     0             ["가 나"]
s6   —             ""          0             [""]
s7   —             "b"         1             ["b"]
s8   — size=3      ""          -1            []
s9   —             ""          -1            []
s10  —             "긴 글자"   0             ["긴 글자"]

datalist 안의 input — willValidate=false · form.elements 에 있나=true
(exit 0)
```

**urlencoded 제출의 전문**

```text
$ python3 html25b-form.py 시도 html25b-26-sent.html | sed -n '1,6p'
[목록 밖 값을 치고 보냄 클릭]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「s1=a&s2=b&s4=a&s4=c&s5=%EA%B0%80+%EB%82%98&s6=&s7=b&s10=%EA%B8%B4+%EA%B8%80%EC%9E%90&d1=%EB%AA%A9%EB%A1%9D%EC%97%90+%EC%97%86%EB%8A%94+%EA%B3%B3&d2=%EB%AA%A9%EB%A1%9D+%EC%95%88%EC%9D%98+%EC%B9%B8&t1=%EC%B2%AB+%EC%A4%84%0D%0A%EB%91%98%EC%A7%B8+%EC%A4%84&t2=%EC%B2%AB%0D%0A%EB%91%98%0D%0A%EC%85%8B%0D%0A%EB%84%B7&b=%EB%B3%B4%EB%83%84」
          필드  s1=「a」 · s2=「b」 · s4=「a」 · s4=「c」 · s5=「가 나」 · s6=「」 · s7=「b」 · s10=「긴 글자」 · d1=「목록에 없는 곳」 · d2=「목록 안의 칸」 · t1=「첫 줄\r\n둘째 줄」 · t2=「첫\r\n둘\r\n셋\r\n넷」 · b=「보냄」
(exit 0)
```

**multipart 제출**

```text
$ python3 html25b-form.py 시도 html25b-26-sent.html | sed -n '7,12p'
[목록 밖 값을 치고 멀티 클릭]
  페이지  click(멀티 · detail=1) → submit(submitter=멀티)
  서버    A POST /r  Content-Type=multipart/form-data; boundary=(경계)
          질의  (없음)
          본문  (multipart — 부분 13개 · 경계로 갈라 필드만 적는다)
          필드  s1=「a」 · s2=「b」 · s4=「a」 · s4=「c」 · s5=「가 나」 · s6=「」 · s7=「b」 · s10=「긴 글자」 · d1=「목록에 없는 곳」 · d2=「목록 안의 칸」 · t1=「첫 줄\r\n둘째 줄」 · t2=「첫\r\n둘\r\n셋\r\n넷」 · b=「멀티」
(exit 0)
```

**실린 칸 격자**

```text
$ python3 html25b-form.py 시도 html25b-26-sent.html | sed -n '/^칸 /,$p'
칸                                (1)   (2)
select · 고른 것 없음             실림  실림
select · 첫 option 이 disabled    실림  실림
select multiple · 고른 것 없음    —    —
select multiple · 둘 고름         실림  실림
select · value 없는 option        실림  실림
select · value="" 고름            실림  실림
select · selected 둘              실림  실림
select size=3 · 고른 것 없음      —    —
select · option 전부 disabled     —    —
option label=짧게 · 글자=긴 글자  실림  실림
input list · 목록 밖 값           실림  실림
datalist 안의 input               실림  실림
textarea (자식 텍스트)            실림  실림
textarea (스크립트 값)            실림  실림
(1) 목록 밖 값을 치고 보냄 클릭 — 실린 칸 = 11 / 14
(2) 목록 밖 값을 치고 멀티 클릭 — 실린 칸 = 11 / 14
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **`multiple` 에서 아무것도 안 고르면(`s3`) 아예 없다** — 본문에 `s3=` 조차 없다. **단일 `select` 에서 안 고르면(`s1`) 첫 선택지 `a` 가 실린다.** 창 ② 가 이유를 보인다 — `s1` 의 `selectedIndex` 는 **0**, `s3` 는 **-1**. 명세의 selectedness setting algorithm — 「`multiple` 이 **없고** 표시 크기가 **1** 이고 선택된 것이 하나도 없으면, **비활성이 아닌 첫 선택지**를 선택됨으로 둔다」.
- ★★ **`size=3`(`s8`)이면 단일이어도 안 실린다** — 표시 크기가 1 이 아니라 그 규칙이 **안 돈다**(`selectedIndex` -1). **선택지가 전부 `disabled`(`s9`)** 여도 고를 것이 없어 안 실린다. **첫 선택지가 `disabled`(`s2`)면 둘째 `b`** 가 실렸다.
- ★★★ **`multiple` 에서 둘을 고르면 같은 이름이 두 번** — `s4=a&s4=c`(필드 `s4=「a」 · s4=「c」`). 창 ② 의 `.value` 는 **첫째 `"a"` 하나만** 답한다 — **`.value` 로 다중 선택을 읽으면 나머지를 잃는다**(`selectedOptions` 는 `["a","c"]`).
- ★★ **`value` 없는 선택지는 글자가 실린다 — 공백을 정리해서** — `  가   나  ` → **`가 나`**(`%EA%B0%80+%EB%82%98`). 명세 — 값은 「`value` 속성, **없으면 HTML 인식 텍스트 내용**」이고 그 텍스트는 끝에 「**ASCII 공백 벗기고 합치기**(strip and collapse)」를 거친다.
- ★ **`label` 속성은 값이 아니다** — `s10` 은 `label="짧게"` 인데 **`긴 글자`** 가 실렸다(`label` 은 **보이는 이름**만 바꾼다 — (3) 의 트리 이름이 `짧게`).
- ★ **`value=""` 를 고르면 빈 값으로 실린다** — `s6=`(필드 `s6=「」`). 「안 실림」(`s3`)과 **서버에서 다르게 보인다.** `selected` 가 둘인 단일 `select`(`s7`)는 **마지막 `b`** 만 남았다 — 명세 — 「둘 이상이면 **마지막 것을 뺀 나머지**를 거짓으로」.
- ★★★ **목록 밖 글자(`d1`)는 그대로 실렸다** — `d1=「목록에 없는 곳」`. `datalist` 는 **입력을 제한하지 않는다.** 명세의 `list` 속성 — 「사용자에게 **제안하는** 미리 정한 선택지」 · 「UA 는 그 제안을 **보여 주어야 한다**」. 거르는 문장은 없다.
- ★★★ **`datalist` 안의 `input`(`d2`)이 실렸다 — 명세와 갈린다.** 명세의 항목 목록 거름망 첫 줄 — 「필드에 **`datalist` 조상이 있으면** 건너뛴다」. 이 판의 Chrome 은 **urlencoded·multipart 둘 다에** `d2=「목록 안의 칸」` 을 실었다. 창 ② 의 `willValidate` 는 **`false`** — 「`datalist` 조상이 있으면 **제약 검증에서 제외**」라는 **다른 문장은 지켰다.** 한 요소에 걸린 두 명세 문장 중 **하나만** 구현된 것이다(아래 「구현 세부사항 대 언어 보장」).
- ★★★ **줄바꿈은 CRLF 로 갔다** — `t1`(자식 텍스트 `첫 줄⏎둘째 줄`)은 본문에 **`%0D%0A`**, `t2`(스크립트로 `첫\r둘\r\n셋\n넷` — CR 하나 · CRLF · LF 하나를 섞었다)는 **셋 다 `%0D%0A`** 가 됐다. 명세 — 「이름·값 쌍 목록으로 바꿀 때, **LF 가 뒤따르지 않는 CR** 과 **CR 이 앞서지 않는 LF** 를 전부 **CR LF** 로 바꾼다」. multipart 도 같다(필드 `t2=「첫\r\n둘\r\n셋\r\n넷」`).
- **실린 칸** — 두 인코딩 다 **11 / 14**(안 실린 셋 = `s3`·`s8`·`s9`).

```text
  select 가 「아무것도 안 골랐을 때」 — 실리나를 가르는 두 조건

                          multiple   표시 크기     selectedIndex   실리나
  s1  보통                  없음        1              0          ● 첫 option
  s2  첫 option disabled    없음        1              1          ● 둘째 option
  s8  size=3                없음        3             -1          ·
  s3  multiple              있음        4(명세)       -1          ·   (s3= 도 없다)
  s9  option 전부 disabled  없음        1             -1          ·   고를 것이 없다

  ★ 「첫 option 을 고른다」는 multiple 없음 AND 표시 크기 1 일 때만 돈다
```

```text
  datalist 에 걸린 두 명세 문장 — 이 판은 하나만 지켰다

  <datalist> <input name="d2"> </datalist>
        │
        ├─ 제약 검증 : 「datalist 조상이 있으면 barred」 ──> willValidate = false     ● 지켰다
        └─ 항목 목록 : 「datalist 조상이 있으면 건너뛴다」 ──> 서버에 d2 가 왔다      ★ 갈렸다
```

### (2) 창 ② + 창 ① — `textarea` 의 값은 자식 텍스트다

**언제 쓰나** — 서버 템플릿이 `<textarea value="{{…}}">` 로 값을 채우고 있을 때 · 스크립트로 값을 넣은 뒤 **자식을 바꿔** 초기화하려 할 때.

```html
<!-- html25b-26-textarea.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>26 textarea 의 값</title>
</head>
<body>
<form id="폼">
<textarea id="t1" value="속성 값">
첫 줄
둘째 줄</textarea>
<textarea id="t2">

앞에 빈 줄</textarea>
<textarea id="t3">원래</textarea>
<textarea id="t4">원래</textarea>
<textarea id="t5"></textarea>
</form>
<script>
const J = v => JSON.stringify(v);
const t = id => document.getElementById(id);
const O = [];
const 찍기 = (무엇) => {
  O.push("── " + 무엇);
  for (const id of ["t1", "t2", "t3", "t4", "t5"]) {
    const e = t(id);
    O.push("  " + id + "  .value=" + J(e.value) + "  textContent=" + J(e.textContent) + "  defaultValue=" + J(e.defaultValue)
      + "  getAttribute('value')=" + J(e.getAttribute("value")) + "  textLength=" + e.textLength);
  }
};
찍기("파싱 직후");
t("t3").textContent = "바뀐 자식";          // 스크립트가 값을 건드린 적 없는 칸의 자식을 바꾼다
t("t4").value = "스크립트 값";              // 값을 먼저 넣고
t("t4").textContent = "바뀐 자식";          // 그다음 자식을 바꾼다
t("t5").value = "첫\r둘\r\n셋\n넷";
찍기("스크립트가 t3 자식 · t4 값→자식 · t5 값을 바꾼 뒤");
t("폼").reset();
찍기("form.reset() 뒤");
t("t4").value = "스크립트 값";
document.body.append(Object.assign(document.createElement("script"), { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
window.__끝 = () => O.join("\n");
</script>
</body>
</html>
```

**창 ② — 세 시점의 `.value`·`textContent`·`defaultValue`**

```text
$ python3 html25b-form.py page html25b-26-textarea.html
── 파싱 직후
  t1  .value="첫 줄\n둘째 줄"  textContent="첫 줄\n둘째 줄"  defaultValue="첫 줄\n둘째 줄"  getAttribute('value')="속성 값"  textLength=8
  t2  .value="\n앞에 빈 줄"  textContent="\n앞에 빈 줄"  defaultValue="\n앞에 빈 줄"  getAttribute('value')=null  textLength=7
  t3  .value="원래"  textContent="원래"  defaultValue="원래"  getAttribute('value')=null  textLength=2
  t4  .value="원래"  textContent="원래"  defaultValue="원래"  getAttribute('value')=null  textLength=2
  t5  .value=""  textContent=""  defaultValue=""  getAttribute('value')=null  textLength=0
── 스크립트가 t3 자식 · t4 값→자식 · t5 값을 바꾼 뒤
  t1  .value="첫 줄\n둘째 줄"  textContent="첫 줄\n둘째 줄"  defaultValue="첫 줄\n둘째 줄"  getAttribute('value')="속성 값"  textLength=8
  t2  .value="\n앞에 빈 줄"  textContent="\n앞에 빈 줄"  defaultValue="\n앞에 빈 줄"  getAttribute('value')=null  textLength=7
  t3  .value="바뀐 자식"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=5
  t4  .value="스크립트 값"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=6
  t5  .value="첫\n둘\n셋\n넷"  textContent=""  defaultValue=""  getAttribute('value')=null  textLength=7
── form.reset() 뒤
  t1  .value="첫 줄\n둘째 줄"  textContent="첫 줄\n둘째 줄"  defaultValue="첫 줄\n둘째 줄"  getAttribute('value')="속성 값"  textLength=8
  t2  .value="\n앞에 빈 줄"  textContent="\n앞에 빈 줄"  defaultValue="\n앞에 빈 줄"  getAttribute('value')=null  textLength=7
  t3  .value="바뀐 자식"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=5
  t4  .value="바뀐 자식"  textContent="바뀐 자식"  defaultValue="바뀐 자식"  getAttribute('value')=null  textLength=5
  t5  .value=""  textContent=""  defaultValue=""  getAttribute('value')=null  textLength=0
(exit 0)
```

**창 ① — 스크립트가 끝난 뒤의 직렬화**

```text
$ python3 html25b-form.py dom html25b-26-textarea.html | sed -n '/<form/,/<\/form>/p'
<form id="폼">
<textarea id="t1" value="속성 값">첫 줄
둘째 줄</textarea>
<textarea id="t2">
앞에 빈 줄</textarea>
<textarea id="t3">바뀐 자식</textarea>
<textarea id="t4">바뀐 자식</textarea>
<textarea id="t5"></textarea>
</form>
(exit 0)
```

- ★★★ **`value="속성 값"` 은 아무 데도 안 나온다** — `t1` 의 `.value` 는 **`"첫 줄\n둘째 줄"`**(자식 텍스트)이고 `getAttribute('value')` 만 `"속성 값"` 이다. `textarea` 에는 **`value` 라는 콘텐츠 속성이 없다** — 그냥 모르는 속성이다. 명세 — 「그 컨트롤의 **내용**이 컨트롤의 기본값이다」.
- ★★ **`<textarea>` 바로 뒤의 줄바꿈 하나는 파서가 지운다** — `t1` 은 소스에서 `<textarea …>⏎첫 줄` 인데 값이 `첫 줄` 로 시작한다. `t2`(줄바꿈 둘)는 **`"\n앞에 빈 줄"`** — 하나만 지웠다. 명세의 파싱 줄 — 「`textarea` 시작 태그 다음 토큰이 **LF 하나**면 무시한다(작성 편의)」. `<pre>` 와 같은 규칙이다([04번](../04-whitespace-and-character-references/2-summary.md)의 (3)).
- ★★ **직렬화는 그 줄바꿈을 되살리지 않는다** — 창 ① 의 `t2` 는 `<textarea id="t2">⏎앞에 빈 줄` 로 **줄바꿈이 하나**다. 이것을 다시 파싱하면 **그 하나가 또 지워진다.** 명세의 직렬화 절 — 「역사적 이유로 이 알고리즘은 `pre`·`textarea`·`listing` 의 **첫 LF 를 왕복시키지 않는다**」. **`innerHTML` 로 옮겨 담으면 빈 첫 줄이 하나씩 줄어든다.**
- ★★★ **자식을 바꾸면 값이 따라온다 — 스크립트가 값을 쓴 적이 없을 때만** — `t3`(자식만 바꿈)은 `.value` 가 **`"바뀐 자식"`** 으로 따라왔다. `t4`(값을 먼저 쓰고 자식을 바꿈)는 **`"스크립트 값"`** 에 머물렀다. 명세 — 「자식이 바뀌면, **더러움 표시(dirty value flag)가 거짓일 때** 원 값을 자식 텍스트로 둔다」 · 「`.value` 를 쓰면 더러움 표시를 **참**으로」.
- ★★ **`form.reset()` 은 자식 텍스트로 되돌린다** — `t4` 가 `"바뀐 자식"` 이 됐다(더러움 표시도 거짓으로).
- ★★ **`.value` 로 넣은 CR 은 LF 가 된다** — `t5` 는 `"첫\r둘\r\n셋\n넷"` 을 넣었는데 `.value` 가 **`"첫\n둘\n셋\n넷"`**, `textLength` 는 **7**. 명세 — 「API 값 = 원 값의 **줄바꿈을 정규화**한 것」. 보낼 때는 그것이 다시 **CRLF** 가 된다((1) 의 `t2`).
- ★ **창 ① 은 `.value` 를 모른다** — 마지막에 `t4.value` 를 다시 `"스크립트 값"` 으로 썼지만 직렬화는 **`바뀐 자식`**(자식 텍스트)이다. **`--dump-dom`·`innerHTML` 로 사용자가 친 글을 읽을 수 없다**([22번](../22-input-types-text/2-summary.md)의 `password` 와 같은 축).

```text
  textarea 의 값 셋 — 명세가 「역사적 이유로」 세 번 정규화한다

  소스 <textarea>⏎첫 줄⏎둘째 줄</textarea>
         │  파서: 첫 LF 하나를 버린다
         ▼
  자식 텍스트 "첫 줄\n둘째 줄" ──(더러움 표시가 거짓이면 따라간다)──> 원 값(raw value)
                                                                    │ 줄바꿈 정규화 → LF
                                                                    ▼
                                                           API 값 = .value · textLength · maxlength 가 본다
                                                                    │ 제출: LF → CR LF (wrap=hard 면 줄 삽입)
                                                                    ▼
                                                           서버  t1=첫+줄%0D%0A둘째+줄
  ★ .value = … 를 쓰는 순간 더러움 표시 = 참 → 그 뒤로 자식을 바꿔도 원 값은 그대로 (reset 이 되돌린다)
```

### (3) 창 ⑦ — `optgroup` 은 묶음이 되고 `datalist` 는 트리에 없다

**언제 쓰나** — 선택지가 많아 묶을 때 보조 기술에 **묶음 이름**이 전달되나 볼 때.

```html
<!-- html25b-26-ax.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>26 트리</title>
</head>
<body>
<label>하나 <select><optgroup label="과일"><option>사과</option><option selected>배</option></optgroup><optgroup label="채소" disabled><option>무</option></optgroup></select></label>
<label>여럿 <select multiple><optgroup label="과일"><option selected>사과</option><option>배</option></optgroup><option>기타</option></select></label>
<label>줄임 <select><option label="짧게">긴 글자</option></select></label>
<label>도시 <input list="목록"></label><datalist id="목록"><option value="서울"></option><option value="부산"></option></datalist>
<label>메모 <textarea></textarea></label>
</body>
</html>
```

```text
$ python3 html25b-form.py ax html25b-26-ax.html
RootWebArea    이름='26 트리'
  generic        이름=''
    LabelText      이름=''
      StaticText     이름='하나 '
      combobox       이름='하나 '
        MenuListPopup  이름=''
          group          이름='과일'
            option         이름='사과' selected=False
            option         이름='배' selected=True
          group          이름='채소'
            option         이름='무' disabled=True
    LabelText      이름=''
      StaticText     이름='여럿 '
      listbox        이름='여럿 ' multiselectable=True
        group          이름='과일'
          option         이름='사과' selected=True
          option         이름='배' selected=False
        option         이름='기타' selected=False
    LabelText      이름=''
      StaticText     이름='줄임 '
      combobox       이름='줄임 '
        MenuListPopup  이름=''
          option         이름='짧게' selected=True
    LabelText      이름=''
      StaticText     이름='도시 '
      combobox       이름='도시 '
        generic        이름=''
    LabelText      이름=''
      StaticText     이름='메모 '
      textbox        이름='메모 ' multiline=True
        generic        이름=''
(exit 0)
```

- ★★ **`optgroup` 은 `group` 이고 이름은 `label` 속성**이다 — `과일`·`채소`. HTML-AAM — `optgroup` → **`group` 역할**. 단일 `select` 는 `combobox` → `MenuListPopup` → `group` → `option`, `multiple` 은 **`listbox`**(`multiselectable=True`) → `group` → `option`.
- ★ **`disabled` 인 `optgroup` 은 안의 선택지를 `disabled=True` 로 만든다** — `무`. 묶음 자신에는 표시가 없다.
- ★ **`option` 의 트리 이름은 `label` 속성이 이긴다** — `줄임` 의 선택지 이름은 **`짧게`** 인데 (1) 에서 실린 값은 **`긴 글자`** 였다. **보이는 것과 보내는 것이 다르다.**
- ★★ **`datalist` 는 트리에 없다** — `도시` 칸은 **`combobox`** 로 찍히고, 목록 선택지는 트리에 안 나온다(이 판은 선택 창을 열지 않았다 — 열린 뒤의 트리는 안 돌려 본 것이다). HTML-AAM 은 `datalist` 를 `listbox` 로, 목록이 딸린 텍스트 칸을 `combobox` 로 적는다.
- **`textarea` 는 `textbox`(`multiline=True`)**, 이름은 라벨 글자다([25번](../25-label-association/2-summary.md)).

```text
  같은 optgroup 이 두 select 에서 — 트리의 층

  select (단일)                 select multiple
  combobox "하나"               listbox "여럿"  multiselectable
   └ MenuListPopup               ├ group "과일"
      ├ group "과일"             │   ├ option "사과" selected
      │   ├ option "사과"        │   └ option "배"
      │   └ option "배" selected └ option "기타"
      └ group "채소"
          └ option "무" disabled   ← optgroup 의 disabled 가 option 으로 내려왔다
```

### demo — 첫 줄바꿈과 무시되는 `value`

```html demo
<!-- html25b-26-demo.html -->
<textarea rows="3">
첫 줄바꿈은 사라진다</textarea>
<textarea rows="3">

둘이면 하나만 사라진다</textarea>
<textarea rows="3" value="이 속성은 안 보인다">자식 글자가 값이다</textarea>
```

> **보이는 것** — 세 칸 중 **첫 칸은 첫 줄부터 글자**가 있고, **둘째 칸은 한 줄 비우고** 글자가 있다. 셋째 칸에는 `value` 속성의 글이 아니라 **태그 사이 글자**가 보인다.\
> **바꿔 볼 것** — 둘째 칸의 빈 줄을 하나 지우고 다시 보라 — (2) 의 「LF 하나만 지운다」가 그 한 줄이다

*(Chrome 151 headless 실측, 창 폭 1000: 세 칸의 `.value` — 검증 파일은 아래)*

```html
<!-- html25b-26-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 26 검증</title>
<body>
<textarea rows="3">
첫 줄바꿈은 사라진다</textarea>
<textarea rows="3">

둘이면 하나만 사라진다</textarea>
<textarea rows="3" value="이 속성은 안 보인다">자식 글자가 값이다</textarea>
<script>
const O = [];
for (const [k, t] of [...document.querySelectorAll("textarea")].entries()) O.push("textarea " + (k + 1) + " · .value=" + JSON.stringify(t.value));
document.body.append(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ python3 html25b-form.py dom html25b-26-democheck.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
textarea 1 · .value="첫 줄바꿈은 사라진다"
textarea 2 · .value="\n둘이면 하나만 사라진다"
textarea 3 · .value="자식 글자가 값이다"
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 제출에서 |
|---|---|---|
| 하나 고르기 | `<select name="s"><option value="a">…` | 안 골라도 **첫 선택지** |
| 「선택 안 함」을 서버에 알리기 | 첫 선택지를 `<option value="">고르세요</option>` | `s=` (빈 값) |
| 여럿 고르기 | `<select name="s" multiple>` | `s=a&s=c` · 안 고르면 **없음** |
| 선택지 묶기 | `<optgroup label="과일">` | 묶음은 안 실린다 |
| 자유 입력 + 보기 | `<input list="id">` + `<datalist id="id"><option value="…"></datalist>` | **친 글자 그대로** |
| 여러 줄 글 | `<textarea name="t">초깃값</textarea>` | 줄바꿈 **CRLF** |

### 어디서 헷갈리나

- **단일 `select` 는 「안 고름」이 없다** — 표시 크기 1 이면 첫 선택지가 이미 골라져 있다.
- **`multiple` 의 `.value` 는 첫째 하나다** — 전부는 `selectedOptions`.
- **`datalist` 는 검증이 아니다** — 제한이 필요하면 `select` 나 서버 검증.
- **`textarea` 에는 `value` 속성이 없다** — 초깃값은 태그 사이에.

## 어디서 틀리나

### 1. 서버가 「선택 안 함」을 `s` 가 없는 것으로 판단한다(단일 `select`)

**단일 `select` 는 언제나 무언가를 싣는다**((1) 의 `s1` — 안 골랐는데 `s1=a`). 「선택 안 함」을 알고 싶으면 **`value=""` 인 첫 선택지**를 두고 빈 값을 본다(`s6=`).

### 2. 서버가 `multiple` 의 이름을 한 값으로 읽는다

**같은 이름이 여러 번 온다**((1) 의 `s4=a&s4=c`). 서버 프레임워크가 같은 이름을 **어떻게 합치는지**는 이 판이 재지 않았다 — 목록으로 받는 API 를 쓴다.

### 3. `datalist` 로 보기를 줬으니 그 밖의 값은 안 온다고 여긴다

**온다**((1) 의 `d1=「목록에 없는 곳」`). 명세가 처음부터 「제안」으로 정했다. [21번](../21-form-submission-model/2-summary.md)의 `curl` 우회를 생각하면 **`select` 로 바꿔도 서버 검증은 여전히 필요하다.**

### 4. `datalist` 안에 둔 칸은 안 보내질 거라 여긴다

**이 판의 Chrome 은 보냈다**((1) 의 `d2` — 명세와 갈린 자리). 옛 브라우저용 대체 입력을 `datalist` 안에 넣는 패턴이 있다면 **서버가 그 필드를 받는다.**

### 5. `<textarea value="…">` 로 초깃값을 채운다

**무시된다**((2) 의 `t1`). 태그 사이에 넣는다 — **첫 줄바꿈이 사라지는 것**까지 감안해서.

### 6. 스크립트로 값을 넣은 뒤 `textContent` 를 바꿔 되돌리려 한다

**안 된다**((2) 의 `t4` — `.value` 가 그대로). `.value` 를 다시 쓰거나 `form.reset()` 을 쓴다.

### 7. 서버가 받은 글의 줄바꿈을 LF 로 가정하고 글자 수를 센다

**CRLF 로 온다**((1) 의 `%0D%0A`). 브라우저의 `textLength`·`maxlength` 는 **LF 하나를 한 글자**로 센다((2) 의 `t5` — 7) — **서버에서 세면 줄마다 하나씩 더 많다.**

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | selectedness setting algorithm — `multiple` 없음 **그리고** 표시 크기 1 이면 비활성 아닌 첫 선택지 · 둘 이상 선택이면 **마지막만** | (1) |
| **명세(HTML)** | 표시 크기 = `size`, 없으면 `multiple` 이면 4 · 아니면 1 | (1) |
| **명세(HTML)** | `option` 의 값 = `value` 속성, 없으면 HTML 인식 텍스트 내용(**공백 벗기고 합치기**) · `label` 은 보이는 이름 | (1)·(3) |
| **명세(HTML)** | `list` = 「제안」 — 거르는 문장이 없다 | (1) |
| **명세(HTML)** | 항목 목록 — **`datalist` 조상이 있으면 건너뛴다** · 제약 검증 — `datalist` 조상이 있으면 **제외** | (1) |
| **명세(HTML)** | 이름·값 쌍 목록 — 외톨이 CR·LF 를 **CR LF** 로 | (1) |
| **명세(HTML)** | `textarea` — 원 값·API 값(LF)·값(제출 · `wrap`) · 자식 변경은 **더러움 표시가 거짓일 때만** 원 값에 반영 · `reset` 은 자식 텍스트로 | (2) |
| **명세(HTML 파싱)** | `textarea` 시작 태그 뒤 **LF 하나 무시** · 직렬화는 그 LF 를 **왕복시키지 않는다** | (2) |
| **명세(HTML-AAM)** | `optgroup` → `group` · `textarea` → `textbox`(multiline) · `datalist` → `listbox` · `option` → `option`(selected) | (3) |
| ★ **구현(Chrome) — 명세와 갈림** | **`datalist` 안의 칸을 항목 목록에 넣는다**(urlencoded·multipart 둘 다) — 제약 검증 제외(`willValidate=false`)는 지킨다 | (1) |
| **구현(Chrome)** | 단일 `select` 를 `combobox` → `MenuListPopup` 으로 · 닫힌 `datalist` 는 트리에 없다 | (3) |
| **이 판의 관찰** | 위 명세 줄들이 (갈림 한 줄 말고) **그대로 동작했다** | (1)\~(3) — 다른 엔진은 **미실행** |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **`select`·`datalist` 의 선택 창** | 페이지 밖 UI 다 — 헤드리스에서 열지 않았다. 「못 잰 것」 |
| **모바일의 선택 휠·자동완성 줄** | 입력기가 없다 — [22번](../22-input-types-text/2-summary.md)과 같은 제3의 상태 |
| **스크린리더가 묶음 이름을 읽나**(「과일 묶음, 사과」) | 보조 기술이 없다 — 트리의 `group` 이름까지 |
| **`wrap="hard"` 가 넣는 줄바꿈** | 글꼴 폭에 달린 구현 정의 — 이 판은 던지지 않았다(안 돌려 본 것) |
| **서버 프레임워크가 같은 이름 여러 개를 합치는 법** | 이 문서의 서버는 받은 것을 전부 적을 뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **값이 정해져 있으면 `select`** — 「선택 안 함」이 필요하면 `value=""` 첫 선택지(필수로 만들기는 목록의 **29번 주제**).
- **보기 + 자유 입력이면 `datalist`** — 보기 밖 값이 온다는 것을 **서버가 안다.**
- **`datalist` 안에 제출할 칸을 두지 않는다** — 이 판에서는 실렸고 명세는 안 싣는다. 엔진마다 갈릴 자리다.
- **여러 줄은 `textarea`** — 초깃값은 태그 사이, 서버는 **CRLF** 를 받는다.
- **다중 선택을 스크립트로 읽을 때는 `selectedOptions`** — `.value` 는 첫째뿐이다.

## 핵심 문장

1. **단일 `select` 는 안 골라도 첫 비활성 아닌 선택지가 실린다 — `multiple` 이나 `size` 가 있으면 안 실린다.**
2. **`multiple` 은 고른 것마다 같은 이름으로 한 번씩 싣는다 — 하나도 안 고르면 이름조차 없다.**
3. **`value` 없는 `option` 은 공백을 정리한 글자가 실린다 — `label` 은 보이는 이름일 뿐이다.**
4. **`datalist` 는 제안이다 — 목록 밖 값도 그대로 실린다.**
5. **이 판의 Chrome 은 `datalist` 안의 칸까지 실었다 — 명세는 건너뛰라고 한다.**
6. **`textarea` 의 값은 자식 텍스트다 — `value` 속성은 없는 것과 같고, 첫 줄바꿈 하나는 파서가 지운다.**
7. **`.value` 를 한 번 쓰면 자식을 바꿔도 값이 안 따라온다 — `reset()` 이 되돌린다.**
8. **줄바꿈은 `.value` 에서 LF, 제출에서 CRLF 다.**

## 관련 자료

- [24번 주제](../24-input-types-choice-special/2-summary.md) — 「실린 칸」 격자 방식의 정본 · 체크박스·라디오가 무엇을 싣나.
- [21번 주제](../21-form-submission-model/2-summary.md) — 제출 모델 · **`curl` 우회**(클라이언트가 무엇을 막든 서버는 다른 값을 받을 수 있다).
- [04번 주제](../04-whitespace-and-character-references/2-summary.md) — `pre`·`textarea` 의 **첫 줄바꿈**을 파서가 지우는 것의 정본. 여기는 그것이 **값과 직렬화**에 어떻게 번지나.
- [25번 주제](../25-label-association/2-summary.md) — `select`·`textarea` 의 이름은 라벨에서.
- [28번 주제](../28-validation-attributes/2-summary.md) — `textarea` 의 `maxlength` 가 **LF 를 한 글자**로 세는 것과 사용자 편집 조건.
- 목록의 **29번 주제**(필수 `select` 의 빈 선택지) · **30번 주제**(`disabled`·`readonly`).

## 용어 풀이

- **선택됨(selectedness)** — `option` 의 참/거짓 상태. `selected` 속성은 초깃값.
- **selectedness setting algorithm** — 선택이 없거나 둘 이상일 때 명세가 고쳐 두는 규칙.
- **표시 크기(display size)** — `size` 속성, 없으면 `multiple` 이면 4, 아니면 1.
- **HTML 인식 텍스트 내용** — `option` 의 글자를 모아 **앞뒤 공백을 벗기고 연속 공백을 하나로** 만든 것.
- **제안 원천(suggestions source element)** — `list` 가 가리키는 `datalist`. 보기를 보여 줄 뿐이다.
- **원 값 · API 값 · 값** — `textarea` 의 세 정규화. 원 값은 그대로, API 값은 LF, 값은 제출용(CRLF · `wrap`).
- **더러움 표시(dirty value flag)** — 사용자가 고치거나 스크립트가 `.value` 를 쓰면 참. 참이면 자식 변경이 값에 안 번진다.
- **CRLF** — 줄 끝을 `\r\n`(`%0D%0A`) 두 글자로 적는 것.

## 더 들어가면

- **왜 제출 때 CRLF 인가** — 명세는 이유를 적지 않는다. `application/x-www-form-urlencoded`·`multipart/form-data` 가 **인터넷 텍스트 형식의 줄 끝 관습(CRLF)** 위에서 자란 형식이라는 연혁과 맞물린다고 읽을 수 있다(해석이다 — 연혁은 이 문서가 확인하지 않았다).
- **`textarea` 의 세 정규화가 「역사적 이유」인 것** — 명세의 문장 그대로다 — 「역사적 이유로 이 요소의 값은 **세 가지 목적에 맞게 세 가지로** 정규화된다」. `maxlength` 가 **LF 하나를 한 글자**로 세는 것(API 값)과 서버가 받는 것(값)이 다른 이유가 여기 있다.
- **Customizable `<select>`** — 명세의 현재 판 `select` 절에는 `selectedcontent` 요소가 들어 있다(선택된 선택지를 단추 안에 복제하는 모델). 이 문서는 그 모델의 제출·트리를 **재지 않았다.**
