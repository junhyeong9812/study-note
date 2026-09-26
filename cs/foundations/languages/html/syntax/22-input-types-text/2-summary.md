# html/syntax/22 — `<input>` 타입 지도 ① 텍스트 계열: `text`/`password`/`email`/`url`/`tel`/`search` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「The input element」](https://html.spec.whatwg.org/multipage/input.html) 절 — Text·Search·Telephone·URL·Email·Password 상태의 **값 정화(value sanitization) 알고리즘**과 **제약 검증** 줄, 「valid email address」 정의, 그리고 [HTML-AAM](https://w3c.github.io/html-aam/)(타입별 역할). **명세 본문은 2026-09-26 에 받아 해당 절을 직접 읽었다.**
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 하네스는 [21번 주제](../21-form-submission-model/3-answer.md)의 `## 실행 검증` 절에 있다(같은 하네스다).\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다.**
> **버전** — HTML 에는 언어 버전이 없다. 여섯 타입은 전부 오래된 표면이라 Baseline 조회 대상으로 따로 세지 않았다.
> **선행** — [21번 주제](../21-form-submission-model/2-summary.md)(무엇이 서버에 실리나).
> **경계** — **속성 대 프로퍼티**(`value` 속성과 `.value` 가 왜 갈리나)의 정본은 [web-api 06번](../../../../web-api/06-attribute-vs-property/2-summary.md)이다 — 여기는 **타입마다 `.value` 가 어떻게 정화되나**까지. **`:invalid`·`:user-invalid` 로 칠하는 것**은 [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md), **`pattern`·`minlength` 같은 검증 속성**은 목록의 **28번 주제**, **`autocomplete`·`inputmode`** 는 목록의 **30번 주제**다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **이 주제의 본체는 창 ②(노드 프로브 — `validity`·`checkValidity()`·`.value`)다.** 타입이 바꾸는 것은 **화면이 아니라 「무엇을 유효로 치나」와 「값을 어떻게 다듬나」** 다. ★ 근거는 **`validity.typeMismatch` 불리언**이지 `validationMessage` 문구가 아니다 — **명세는 문구를 정하지 않는다**((2)).

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
| ★ **흔들린다** | **`validationMessage` 문구** | 로케일·판마다 다르다 — ★ **근거로 쓰지 않는다**. 그래서 로케일을 `--lang=ko-KR` 로 **고정해** 찍고, 한 판은 `de-DE` 로 **일부러 바꿔** 문구만 갈리는 것을 보인다((2)) |
| **흔들린다** | CDP 포트·프로필 경로·서버 포트 | 출력에는 안 들어간다 |
| **안 흔들린다** | `validity.typeMismatch`·`checkValidity()`·`.value`·역할 | 같은 판이면 결정적이다 — 두 로케일에서도 같았다((2)) |
| **안 흔들린다** | 서버에 실린 필드 | 21번의 하네스 — 시도마다 페이지를 새로 연다 |
| **안 흔들린다** | 「N / M」 줄 | 스크립트가 센다 |

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **② 노드 프로브** | ★ **쓴다 — 본체** | `typeMismatch` 가 **켜지나** · `.value` 가 **속성 글자와 갈리나**((1)) |
| **⑦ 접근성 트리** | 쓴다 | 타입마다 **역할**이 무엇인가((1)) |
| **⑤ 서버 요청 로그** | 쓴다 | **정화된 값**이 그대로 실리나((3)) |
| **① `--dump-dom`** | 쓴다 | `password` 에 넣은 값이 **직렬화에 나오나**((4)) |
| **③ `innerText` 대 `textContent`** | **부적용** | 입력 칸의 값은 자식 글자가 아니다 — **잴 것이 없다** |
| **④ `compatMode`** | **부적용** | 문서 모드와 무관하다 |
| **⑥ `renderBlockingStatus`** | **부적용** | 입력은 렌더를 막지 않는다 |

- ★★ **제5의 상태 — 「타입이 무엇을 받나」를 제출이 아니라 `validity` 로 물었다.** 제출로 물으면 무효한 칸이 제출을 **막아 버려** 나머지 칸을 못 본다. 그래서 (1)은 `validity` 로 칸마다 따로 묻고, (3)은 **`novalidate` 폼**으로 무효한 칸까지 **전부 보내** 서버가 받은 값을 본다. ★ 바꾼 창이 못 보는 것 — `validity` 는 **사용자가 무엇을 입력할 수 있나**(키보드·입력 거부)를 말하지 않는다. 값은 전부 `value` 속성으로 넣었다.

## 한눈에 — 쉽게 말하면

**★ 여섯 타입은 전부 「한 줄 글자 칸」이다. 다른 것은 칸 옆에 붙은 「검사관」과 「손질 담당」 둘뿐이다.**

신청서 창구에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **아무 칸** | `text` — 검사관 없음, 손질은 **줄바꿈만 지움** |
| **「검색」이라고 적힌 아무 칸** | `search` — `text` 와 **모양만 다르다**(명세: 「주로 스타일의 차이」) · 역할은 `searchbox` |
| **가림막이 달린 칸** | `password` — 검사관 없음, 화면에서만 가린다 |
| **「메일 주소 모양인가」 검사관** | `email` — 명세의 **정규식 하나**로 본다 · 앞뒤 공백을 **손질**한다 |
| **「절대 URL 인가」 검사관** | `url` — **URL 파서**가 풀리면 통과 · 앞뒤 공백을 손질한다 |
| **「전화번호」라고 적힌 아무 칸** | `tel` — ★ **검사관이 없다**(명세가 일부러 뺐다) |
| **손님 폰의 자판 모양** | 모바일 가상 키보드 — ★ **이 판이 못 본다** |

- **`email` 은 `a@b` 를 통과시킨다** — 점 없는 도메인도 명세의 정규식에 맞는다((1)).
- **`tel` 은 아무 글자나 통과시킨다** — 「아무 글자!」도 유효다((1)).
- **`url` 은 `javascript:` 도 통과시킨다** — 절대 URL 이기만 하면 된다((1)).
- ★ **손질은 서버까지 간다** — 앞뒤 공백이 지워진 값이 실린다((3)).

```text
  한 칸의 값이 서버에 닿기까지 — 타입이 끼어드는 두 자리

  value 속성 / 사용자 입력
          │
          ▼  ① 값 정화(sanitization) — 타입마다 다르다
  .value  "a@b.kr"  (앞뒤 공백·줄바꿈이 지워짐)
          │
          ▼  ② 제약 검증 — typeMismatch 가 켜지나
  유효 ──> 제출에 실린다          무효 ──> 제출이 막힌다 (novalidate 면 그대로 실린다)

  ★ ① 은 언제나 돈다(제출과 무관) · ② 는 제출 때 막는 데 쓰인다
```

> **값 정화(value sanitization)** — 타입마다 명세가 정한 「값 다듬기」. `value` 속성을 넣을 때·타입이 바뀔 때·스크립트가 넣을 때 돈다.\
> 예: `email` 은 「줄바꿈을 지우고 **앞뒤 공백**을 지운다」 — `" a@b.kr "` → `"a@b.kr"`.

> **`typeMismatch`** — `validity` 객체의 불리언. 값이 **그 타입의 문법에 안 맞으면** 참이다. 명세는 `email`·`url` 에만 이 줄을 둔다.

## 이 주제가 답하려는 질문

1. **여섯 타입 중 무엇이 값을 검사하고 무엇이 안 하나** — `tel` 은 왜 안 하나.
2. **`email`·`url` 의 검사는 정확히 무엇을 통과시키나** — `a@b`, `javascript:`, 한글.
3. **타입은 값을 어떻게 다듬고, 그 다듬은 값이 서버에 그대로 가나** — 그리고 `password` 는 무엇을 숨기나.

## 동작 방식

### (1) 창 ② + 창 ⑦ — 열여덟 칸의 `typeMismatch`·`.value`·역할

**언제 쓰나** — 「이 칸에 이 값을 넣으면 브라우저가 막나」를 **제출 전에** 알고 싶을 때.

여섯 타입에 값 열여덟 개를 **`value` 속성으로** 넣었다. 폼은 `novalidate` 다((3) 에서 전부 보내려고).

```html
<!-- html21b-22-types.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<link rel="icon" href="data:,">
<title>22 텍스트 계열 타입</title>
<script src="html21b-rec.js"></script>
</head>
<body>
<form id="폼" action="/r" method="post" novalidate>
<input id="t1" name="t1" type="text" value="줄&#10;바꿈">
<input id="t2" name="t2" type="text" value=" 앞뒤 공백 ">
<input id="s1" name="s1" type="search" value="검색어">
<input id="p1" name="p1" type="password" value="비밀">
<input id="e1" name="e1" type="email" value="a@b">
<input id="e2" name="e2" type="email" value="a">
<input id="e3" name="e3" type="email" value=" a@b.kr ">
<input id="e4" name="e4" type="email" value="한@b.kr">
<input id="e5" name="e5" type="email" value="a@-b.kr">
<input id="e6" name="e6" type="email" value="a@b.kr, c@d.kr">
<input id="e7" name="e7" type="email" value="a@b.kr, c@d.kr" multiple>
<input id="u1" name="u1" type="url" value="http://x">
<input id="u2" name="u2" type="url" value="x">
<input id="u3" name="u3" type="url" value="javascript:alert(1)">
<input id="u4" name="u4" type="url" value=" http://한글.kr/경로 ">
<input id="n1" name="n1" type="tel" value="아무 글자!">
<input id="n2" name="n2" type="tel" value="010-1234-5678">
<input id="n3" name="n3" type="tel" value="12&#10;34">
<button id="보냄">보냄</button>
</form>
<script>
const 칸 = (s, w) => s + " ".repeat(Math.max(w - [...s].reduce((n, c) => n + (c.codePointAt(0) > 0x1100 ? 2 : 1), 0), 1));
const J = v => JSON.stringify(v);
const 칸들 = [...document.querySelectorAll("#폼 input")];
window.__대상 = 칸들.map(i => [i.id, "#" + i.id]);
window.__시도 = [{ 이름: "novalidate 로 전부 보내기", 단계: [["click", "#보냄"]] }];
window.__끝 = () => {
  const O = [칸("id", 4) + 칸("type", 9) + 칸("value 속성", 22) + 칸(".value", 22) + 칸("typeMismatch", 13) + 칸("checkValidity()", 16) + "역할"];
  for (const i of 칸들) {
    O.push(칸(i.id, 4) + 칸(i.type, 9) + 칸(J(i.getAttribute("value")), 22) + 칸(J(i.value), 22)
      + 칸(String(i.validity.typeMismatch), 13) + 칸(String(i.checkValidity()), 16) + __AX[i.id].역할);
  }
  O.push("");
  O.push("validationMessage 전문 (비어 있지 않은 것만)");
  for (const i of 칸들) if (i.validationMessage) O.push("  " + i.id + "  " + i.validationMessage);
  O.push("");
  const 틀림 = 칸들.filter(i => i.validity.typeMismatch);
  O.push("typeMismatch 인 칸 = " + 틀림.map(i => i.id).join(" · ") + " → " + 틀림.length + " / " + 칸들.length);
  const tel = 칸들.filter(i => i.type === "tel");
  O.push("tel 에서 무효가 된 칸 = " + tel.filter(i => !i.checkValidity()).length + " / " + tel.length);
  const 바뀜 = 칸들.filter(i => i.value !== i.getAttribute("value"));
  O.push("value 속성과 .value 가 다른 칸 = " + 바뀜.map(i => i.id).join(" · ") + " → " + 바뀜.length + " / " + 칸들.length);
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html21b-form.py --lang=ko-KR page html21b-22-types.html
id  type     value 속성            .value                typeMismatch checkValidity() 역할
t1  text     "줄\n바꿈"            "줄바꿈"              false        true            textbox
t2  text     " 앞뒤 공백 "         " 앞뒤 공백 "         false        true            textbox
s1  search   "검색어"              "검색어"              false        true            searchbox
p1  password "비밀"                "비밀"                false        true            textbox
e1  email    "a@b"                 "a@b"                 false        true            textbox
e2  email    "a"                   "a"                   true         false           textbox
e3  email    " a@b.kr "            "a@b.kr"              false        true            textbox
e4  email    "한@b.kr"             "한@b.kr"             true         false           textbox
e5  email    "a@-b.kr"             "a@-b.kr"             true         false           textbox
e6  email    "a@b.kr, c@d.kr"      "a@b.kr, c@d.kr"      true         false           textbox
e7  email    "a@b.kr, c@d.kr"      "a@b.kr,c@d.kr"       false        true            textbox
u1  url      "http://x"            "http://x"            false        true            textbox
u2  url      "x"                   "x"                   true         false           textbox
u3  url      "javascript:alert(1)" "javascript:alert(1)" false        true            textbox
u4  url      " http://한글.kr/경로 " "http://한글.kr/경로" false        true            textbox
n1  tel      "아무 글자!"          "아무 글자!"          false        true            textbox
n2  tel      "010-1234-5678"       "010-1234-5678"       false        true            textbox
n3  tel      "12\n34"              "1234"                false        true            textbox

validationMessage 전문 (비어 있지 않은 것만)
  e2  이메일 주소에 '@'를 포함해 주세요. 'a'에 '@'가 없습니다.
  e4  '@' 앞 부분에 '한' 기호가 포함되면 안됩니다.
  e5  이메일 주소를 입력하세요.
  e6  '@' 다음 부분에 ',' 기호가 포함되면 안됩니다.
  u2  URL을 입력하세요.

typeMismatch 인 칸 = e2 · e4 · e5 · e6 · u2 → 5 / 18
tel 에서 무효가 된 칸 = 0 / 3
value 속성과 .value 가 다른 칸 = t1 · e3 · e7 · u4 · n3 → 5 / 18
(exit 0)
```

```text
  여섯 타입 × 「검사관이 있나 · 무엇을 손질하나」 (명세 값 정화 알고리즘 · 제약 검증 줄)

  타입       손질                              검사(typeMismatch)                 이 판   역할(CDP)
  text       줄바꿈을 지운다                   없다                               t1·t2   textbox
  search     줄바꿈을 지운다                   없다                               s1      searchbox
  password   줄바꿈을 지운다                   없다                               p1      textbox
  tel        줄바꿈을 지운다                   ★ 없다                             n1~n3   textbox
  url        줄바꿈 + 앞뒤 공백                「비었거나 유효한 절대 URL」이 아니면  u1~u4   textbox
  email      줄바꿈 + 앞뒤 공백                명세 정규식에 안 맞으면              e1~e6   textbox
  email      쉼표로 쪼개 조각마다 앞뒤 공백      조각마다 정규식                      e7      textbox
   multiple
```

- ★★★ **`tel` 은 셋 다 유효다** — 「아무 글자!」도(`tel 에서 무효가 된 칸 = 0 / 3`). 명세가 이유까지 적는다 — 「URL·Email 과 달리 Telephone 타입은 **특정 문법을 강제하지 않는다. 이것은 의도적이다** — 실제로 전화번호 칸은 자유 양식인 경향이 있다. 유효한 전화번호가 너무 다양하기 때문이다. 형식을 강제해야 하는 시스템은 **`pattern` 속성이나 `setCustomValidity()`** 로 클라이언트 검증에 끼어들라」.
- ★★★ **`email` 의 `a@b` 는 유효**다(`typeMismatch=false`). 명세의 정의가 정규식으로 주어진다 —

```text
  /^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/

  @ 뒤  = 라벨 하나 + ( "." 라벨 )*     ← 「*」 — 점이 0 번이어도 된다 → a@b 통과
  라벨  = 영숫자로 시작·끝, 가운데만 "-"  ← a@-b.kr 탈락 (e5)
  @ 앞  = ASCII 영숫자와 기호만          ← 한@b.kr 탈락 (e4)
```

  명세는 이것을 「RFC 5322 에 대한 **의도적 위반**」이라 부른다 — RFC 는 「@ 앞은 너무 엄격하고, @ 뒤는 너무 모호하고, 주석·공백·따옴표 문자열은 너무 관대해서 여기 쓰기에 실용적이지 않다」.
- ★★ **`multiple` 이 없는 `email` 에 쉼표 목록(`e6`)은 무효**, `multiple` 이 있으면(`e7`) **유효**이고 `.value` 가 `"a@b.kr,c@d.kr"`(쉼표 뒤 공백이 **지워졌다**). 명세의 `multiple` 판 정화 — 「쉼표로 쪼개 **조각마다** 앞뒤 공백을 지우고, 쉼표 하나로 다시 잇는다」.
- ★★★ **`url` 은 `javascript:alert(1)` 을 통과시킨다** — 제약 줄이 「비었거나 **유효한 절대 URL**」 뿐이라 **스킴을 가리지 않는다.** `x`(상대 URL)만 탈락했다. ★ 그래서 **`type=url` 은 링크로 다시 쓸 값을 걸러 주지 않는다** — 서버가 스킴을 본다.
- ★★ **`value` 속성과 `.value` 가 다른 칸은 5 / 18** — `t1`(줄바꿈)·`n3`(줄바꿈)은 **줄바꿈이 지워졌고**, `e3`·`u4` 는 **앞뒤 공백**, `e7` 은 **쉼표 뒤 공백**이 지워졌다. ★ **`text` 의 앞뒤 공백(`t2`)은 그대로**다 — 공백 손질은 `email`·`url` 만 한다.
- **역할** — `search` 만 `searchbox`, 나머지 다섯은 `textbox` 다. ★ **`password` 는 HTML-AAM 이 「대응하는 역할 없음」**(계산된 역할 `html-input-password`)으로 적는데 **CDP 트리는 `textbox`** 로 찍었다 — 구현의 선택이다.

### (2) 창 ② — `validationMessage` 는 문구가 로케일마다 다르다 · 깃발은 같다

**언제 쓰나** — 검증 문구를 **테스트의 기대값**으로 쓰려 할 때(쓰면 안 된다).

(1) 과 **같은 파일**을 `--lang=de-DE` 로 띄운 판의 문구 절만 잘랐다(하네스는 환경 변수 `LANGUAGE` 로 로케일을 준다 — [23번](../23-input-types-number-date/2-summary.md)의 (1) 이 그 까닭을 싣는다).

```text
$ python3 html21b-form.py --lang=de-DE page html21b-22-types.html | sed -n '/^validationMessage/,/^$/p'
validationMessage 전문 (비어 있지 않은 것만)
  e2  Die E-Mail-Adresse muss ein @-Zeichen enthalten. In der Angabe "a" fehlt ein @-Zeichen.
  e4  Vor dem @-Zeichen darf das Zeichen "한" nicht verwendet werden.
  e5  Gib eine E-Mail-Adresse ein.
  e6  Nach dem @-Zeichen darf das Zeichen "," nicht verwendet werden.
  u2  Gib eine URL ein.

(exit 0)
```

- ★★★ **문구가 칸마다 다 다르고, 무효인 칸은 그대로 다섯**이다(`e2`·`e4`·`e5`·`e6`·`u2`). 명세의 `validationMessage` getter 는 「UA 가 사용자에게 보여 줄 **알맞게 현지화된 메시지**를 돌려준다」고만 하고 **글자를 정하지 않는다** — 로케일마다 다른 것이 명세대로다.
- ★ **`e5`(`a@-b.kr`) 는 두 로케일 다 「메일 주소를 입력하라」는 일반 문구**다 — 다른 칸처럼 **무엇이 틀렸는지** 짚지 않는다. 문구의 친절함도 구현의 몫이다.

### (3) 창 ⑤ — 서버에는 정화된 값이 간다

**언제 쓰나** — 「사용자가 넣은 그대로」를 서버가 받는다고 믿을 때.

(1) 의 폼(`novalidate`)을 그대로 제출했다.

```text
$ python3 html21b-form.py 시도 html21b-22-types.html
[novalidate 로 전부 보내기]
  페이지  click(보냄 · detail=1) → submit(submitter=보냄)
  서버    A POST /r  Content-Type=application/x-www-form-urlencoded
          질의  (없음)
          본문  「t1=%EC%A4%84%EB%B0%94%EA%BF%88&t2=+%EC%95%9E%EB%92%A4+%EA%B3%B5%EB%B0%B1+&s1=%EA%B2%80%EC%83%89%EC%96%B4&p1=%EB%B9%84%EB%B0%80&e1=a%40b&e2=a&e3=a%40b.kr&e4=%ED%95%9C%40b.kr&e5=a%40-b.kr&e6=a%40b.kr%2C+c%40d.kr&e7=a%40b.kr%2Cc%40d.kr&u1=http%3A%2F%2Fx&u2=x&u3=javascript%3Aalert%281%29&u4=http%3A%2F%2F%ED%95%9C%EA%B8%80.kr%2F%EA%B2%BD%EB%A1%9C&n1=%EC%95%84%EB%AC%B4+%EA%B8%80%EC%9E%90%21&n2=010-1234-5678&n3=1234」
          필드  t1=「줄바꿈」 · t2=「 앞뒤 공백 」 · s1=「검색어」 · p1=「비밀」 · e1=「a@b」 · e2=「a」 · e3=「a@b.kr」 · e4=「한@b.kr」 · e5=「a@-b.kr」 · e6=「a@b.kr, c@d.kr」 · e7=「a@b.kr,c@d.kr」 · u1=「http://x」 · u2=「x」 · u3=「javascript:alert(1)」 · u4=「http://한글.kr/경로」 · n1=「아무 글자!」 · n2=「010-1234-5678」 · n3=「1234」
뒤늦게 온 요청 = 0
(exit 0)
```

- ★★★ **무효한 칸도 실렸다** — `e2=「a」` · `u2=「x」` · `e6=「a@b.kr, c@d.kr」`. `novalidate` 라 검증이 제출을 막지 않았다([21번](../21-form-submission-model/2-summary.md)의 (5)).
- ★★ **실린 값은 `.value` 다** — `t1=「줄바꿈」`(줄바꿈 없음) · `e3=「a@b.kr」`(앞뒤 공백 없음) · `e7=「a@b.kr,c@d.kr」`. 서버가 받은 것은 **속성 글자가 아니라 정화된 값**이다.
- **`password` 도 맨글자로 간다** — `p1=「비밀」`. 가림은 **화면의 일**이다. 전송을 지키는 것은 HTTPS 이지 타입이 아니다.

### (4) 창 ① — `password` 의 값은 직렬화에 안 나온다 · `text` 도 똑같다

**언제 쓰나** — 「비밀번호 칸의 값이 DOM 에 남는다/안 남는다」를 판단할 때.

`text`·`password` 둘에 `value="속성값"` 을 두고, 스크립트가 **셋 다** `.value = "스크립트값"` 으로 바꿨다.

```html
<!-- html21b-22-dump.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>22 속성과 프로퍼티</title>
</head>
<body>
<input id="글" type="text" value="속성값">
<input id="비" type="password" value="속성값">
<input id="빈" type="password">
<script>
for (const id of ["글", "비", "빈"]) document.getElementById(id).value = "스크립트값";
document.body.append(Object.assign(document.createElement("pre"), {
  textContent: ["글", "비", "빈"].map(id => id + " .value = " + document.getElementById(id).value
    + " · .defaultValue = " + JSON.stringify(document.getElementById(id).defaultValue)).join("\n")
}));
</script>
</body>
</html>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html21b-22-dump.html 2>/dev/null
<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="utf-8">
<title>22 속성과 프로퍼티</title>
</head>
<body>
<input id="글" type="text" value="속성값">
<input id="비" type="password" value="속성값">
<input id="빈" type="password">
<script>
for (const id of ["글", "비", "빈"]) document.getElementById(id).value = "스크립트값";
document.body.append(Object.assign(document.createElement("pre"), {
  textContent: ["글", "비", "빈"].map(id => id + " .value = " + document.getElementById(id).value
    + " · .defaultValue = " + JSON.stringify(document.getElementById(id).defaultValue)).join("\n")
}));
</script><pre>글 .value = 스크립트값 · .defaultValue = "속성값"
비 .value = 스크립트값 · .defaultValue = "속성값"
빈 .value = 스크립트값 · .defaultValue = ""</pre>


</body></html>
(exit 0)
```

- ★★★ **`--dump-dom` 의 `value` 는 셋 다 속성 그대로**다 — `text` 도 `password` 도 `value="속성값"`, 속성이 없던 `#빈` 은 **속성이 없다.** 그런데 `.value` 는 셋 다 「스크립트값」이다.
- ★★ **`password` 가 특별해서가 아니다** — `text` 도 똑같이 안 나온다. `.value` 는 **「값 모드」라는 별도 상태**이고 `value` 속성은 **`defaultValue` 쪽**에 이어져 있다([web-api 06번](../../../../web-api/06-attribute-vs-property/2-summary.md)의 결론 — 「`input.value` 는 반영이 아니다」). 직렬화는 **속성**을 적는다.
- ★ 거꾸로 — **서버가 렌더한 HTML 의 `value="…"` 속성은 그대로 보인다**(`#비` 의 `value="속성값"`). 비밀번호를 `value` 속성에 채워 보내면 **소스 보기에 드러난다.**

```text
  같은 칸의 두 값 — 어느 창에서 읽었나

                 value 속성(= defaultValue)   .value            --dump-dom 의 value
  #글 text       속성값                       스크립트값         속성값
  #비 password   속성값                       스크립트값         속성값
  #빈 password   (없음)                        스크립트값         (속성 없음)

  ★ 직렬화는 속성을 적는다 — 타입과 무관하다
```

### demo — `email` 과 `tel` 의 검사관

```html demo
<!-- html21b-22-demo.html -->
<input type="email" value="a@b">
<input type="email" value="a">
<input type="tel" value="아무 글자!">
<style>
  input { display: block; margin: 6px; }
  input:invalid { outline: 3px solid crimson; }
</style>
```

> **보이는 것** — 세 칸 중 **가운데(`a`)만 빨간 테두리**다. `a@b` 는 점이 없어도 통과하고, 「아무 글자!」를 넣은 `tel` 도 테두리가 없다.\
> **바꿔 볼 것** — 가운데 `value="a"` 를 `value="a@b"` 로 바꾸면 테두리가 사라진다 — (1) 의 `e1` 과 같은 값이다

*(Chrome 151 headless 실측, 창 폭 1000: 둘째 칸만 `:invalid` 가 참이고 `outline-style` 이 `solid`. 검증 파일은 아래)*

```html
<!-- html21b-22-democheck.html -->
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 22 검증</title>
<body>
<input type="email" value="a@b">
<input type="email" value="a">
<input type="tel" value="아무 글자!">
<style>
  input { display: block; margin: 6px; }
  input:invalid { outline: 3px solid crimson; }
</style>
<script>
const O = [];
for (const i of document.querySelectorAll("input")) {
  const c = getComputedStyle(i);
  O.push(i.type.padEnd(6) + JSON.stringify(i.value).padEnd(14) + ":invalid=" + String(i.matches(":invalid")).padEnd(6)
    + "outline-style=" + c.outlineStyle);
}
document.body.append(Object.assign(document.createElement("script"),
  { type: "text/plain", textContent: "\n--OUT\n" + O.join("\n") + "\nOUT--\n" }));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html21b-22-democheck.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
email "a@b"         :invalid=false outline-style=none
email "a"           :invalid=true  outline-style=solid
tel   "아무 글자!"      :invalid=false outline-style=none
(exit 0)
```

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 쓰려는 것 | 형태 | 이 판에서 |
|---|---|---|
| 이름·주소 같은 자유 글자 | `type="text"` | 검사 없음 · 줄바꿈만 지운다 |
| 검색어 | `type="search"` | `text` 와 같고 역할만 `searchbox` |
| 메일 주소 | `type="email"` | 명세 정규식 — **`a@b` 통과** |
| 메일 주소 여러 개 | `type="email" multiple` | 쉼표로 쪼개 조각마다 검사 |
| 웹 주소 | `type="url"` | 절대 URL 이면 통과 — **`javascript:` 도** |
| 전화번호 | `type="tel"` | ★ **검사 없음** — 형식이 필요하면 `pattern` |
| 비밀번호 | `type="password"` | 화면에서만 가린다 · 전송·직렬화는 `text` 와 같다 |

### 어디서 헷갈리나

- **`email` 의 검사는 「주소가 실제로 있나」가 아니다** — 모양만 본다. 점 없는 도메인도 된다.
- **`tel` 은 「전화번호 검사」가 아니다** — 모바일 자판을 고르라는 **힌트**에 가깝다(그 자판은 이 판이 못 봤다).
- **`url` 은 「안전한 링크」가 아니다** — 스킴을 안 본다.
- **공백 손질은 `email`·`url` 만** 한다 — `text` 의 앞뒤 공백은 서버까지 간다.

## 어디서 틀리나

### 1. `type="tel"` 을 주면 숫자만 들어온다고 믿는다

**아무 글자나 유효다**((1) — `tel 에서 무효가 된 칸 = 0 / 3`). 서버는 「아무 글자!」를 받았다((3)).

### 2. `type="email"` 이 보안 검사를 해 준다고 믿는다

**모양 검사이고, 서버에는 무엇이든 닿는다** — [21번](../21-form-submission-model/2-summary.md)의 (5) 에서 `curl` 이 「아무 글자」를 그대로 보냈다. 게다가 **`a@b` 를 통과시킨다.**

### 3. `type="url"` 로 받은 값을 그대로 링크에 쓴다

**`javascript:alert(1)` 이 유효**다((1) 의 `u3`). 링크로 쓸 값은 서버가 스킴을 걸러야 한다.

### 4. `validationMessage` 문구로 테스트를 짠다

**로케일이 바뀌면 깨진다**((2)). 기대값은 **`validity.typeMismatch` 같은 깃발**로 둔다.

### 5. `password` 칸의 값이 HTML 소스에 드러날까 걱정하거나, 안 드러난다고 안심한다

**사용자가 넣은 값(`.value`)은 직렬화에 안 나오지만, `value` 속성은 나온다**((4)). 그리고 그건 `text` 도 같다 — 타입이 준 성질이 아니다.

### 6. 서버가 사용자의 원래 글자를 받는다고 여긴다

**정화된 값을 받는다**((3)) — `email`·`url` 의 앞뒤 공백, 모든 타입의 줄바꿈이 **브라우저에서 이미 지워졌다.**

## 구현 세부사항 대 언어 보장

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | 타입별 값 정화 — text·search·tel·password 는 **줄바꿈**, email·url 은 **줄바꿈 + 앞뒤 공백**, email multiple 은 **조각마다** | (1)·(3) |
| **명세(HTML)** | `email` 의 typeMismatch = 「valid email address」 정규식 · `url` = 「유효한 절대 URL」 | (1) |
| **명세(HTML)** | `tel` 은 **일부러** 문법을 강제하지 않는다 | (1) |
| **명세(HTML)** | Text 와 Search 의 차이는 **주로 스타일** | (1) |
| **명세(HTML)** | `validationMessage` 의 **글자는 정하지 않는다** | (2) |
| **명세(HTML-AAM)** | text·email·tel·url → `textbox` · search → `searchbox` · password → **대응 역할 없음** | (1) |
| **구현(Chrome)** | `password` 를 CDP 트리에서 **`textbox`** 로 둔다 | (1) |
| **구현(Chrome)** | `validationMessage` 의 문구 전부 · `e5` 의 일반 문구 — 명세는 「알맞게 현지화된 메시지」까지만 | (2) |
| **이 판의 관찰** | 두 로케일에서 **깃발이 같았다** | (1)·(2) |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **모바일 가상 키보드**(`tel` → 숫자 자판 · `email` → `@` 자판) | 헤드리스 **데스크톱** Chrome 에는 가상 키보드가 없다. 자판을 고르는 것은 **운영체제의 입력기**이고 페이지는 타입을 **힌트로 넘길 뿐**이다 — 자판이 떠야 잴 수 있는데 **띄울 입력기가 이 환경에 없다**(모바일 에뮬레이션은 이 배치가 던지지 않았다). 그래서 「**못 잰 것**」(제3의 상태)이다 — 자판은 페이지 밖에 **존재하는 층**이라 「잴 것이 없다」(제4의 상태)가 아니다 |
| ★★ **자동완성·비밀번호 관리자** | 채워 넣을 **저장된 값**이 새 프로필에 없고, 제안 목록은 **브라우저 UI**(페이지 밖)에 뜬다. 헤드리스에는 그 UI 가 없다 — 「못 잰 것」. `autocomplete` 토큰의 뜻은 목록의 **30번 주제**가 다룬다 |
| **스크린리더가 `password` 를 어떻게 읽나**(가린 글자·「보안 텍스트」 알림) | 보조 기술이 없다. CDP 트리는 `textbox` 까지다 |
| **사용자가 칸에 줄바꿈을 칠 수 있나** | 명세는 「UA 는 사용자가 LF·CR 을 넣게 **두면 안 된다**」고 한다. 이 판은 **값을 속성으로만** 넣었다 — 키 입력은 **안 돌려 본 것** |
| **IDN 도메인**(`a@한글.kr`)의 표시 변환 | 명세는 UA 가 퓨니코드를 표시용으로 바꿔도 된다고 한다 — 이 판은 **안 돌려 본 것** |

## 언제 쓰고 언제 안 쓰나

- **메일은 `email`, 웹 주소는 `url`** — 모양 검사와 (모바일에서는) 알맞은 자판을 거저 얻는다. **서버 검사는 따로.**
- **전화번호는 `tel` + 필요하면 `pattern`** — `number` 는 쓰지 않는다([23번](../23-input-types-number-date/2-summary.md)).
- **검색 칸은 `search`** — 역할이 `searchbox` 가 된다.
- **비밀번호는 `password` + HTTPS** — 타입은 **화면만** 가린다. `value` 속성에 채워 보내지 않는다.
- **공백이 뜻을 갖는 값(예: 앞뒤 공백을 지키는 코드 조각)** 은 `text` — `email`·`url` 은 공백을 지운다.

## 핵심 문장

1. **여섯 타입 중 값을 검사하는 것은 `email`·`url` 둘뿐이다 — `tel` 은 명세가 일부러 뺐다.**
2. **`email` 은 명세의 정규식 하나로 본다 — `a@b` 는 유효, `한@b.kr`·`a@-b.kr` 은 무효다.**
3. **`url` 은 절대 URL 이면 통과한다 — `javascript:` 도.**
4. **타입마다 값을 정화한다 — 줄바꿈은 모두가, 앞뒤 공백은 `email`·`url` 만 지운다. 서버는 정화된 값을 받는다.**
5. **`validationMessage` 는 문구가 구현이다 — 근거는 `typeMismatch` 깃발로 둔다.**
6. **`password` 의 입력값이 직렬화에 안 나오는 것은 `text` 도 같다 — `.value` 는 속성이 아니다.**
7. **모바일 키보드·자동완성은 헤드리스 데스크톱에서 못 잰다 — 페이지 밖의 UI 다.**

## 관련 자료

- [21번 주제 — 폼의 제출 모델](../21-form-submission-model/2-summary.md) — **무엇이 서버에 실리나**와 `curl` 우회의 정본. 여기는 **타입마다 무엇이 실리나**.
- [web-api 06번 — 속성 대 프로퍼티](../../../../web-api/06-attribute-vs-property/2-summary.md) — **`value` 속성과 `.value`** 의 정본. 여기는 그 결과가 **`password` 에서 어떻게 보이나**((4)).
- [CSS 10번 — 상태·폼 의사 클래스](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md) — **`:invalid` 와 `:user-invalid` 의 시점 차이**. 이 주제의 demo 는 `:invalid` 하나만 쓴다.
- [23번 주제](../23-input-types-number-date/2-summary.md) — 숫자·날짜 타입 · **`number` 에 전화번호를 넣으면**.
- [24번 주제](../24-input-types-choice-special/2-summary.md) — 선택·특수 타입.
- 목록의 **28번 주제**(`pattern`·`minlength` 등 검증 속성) · **29번 주제**(제약 검증 상태) · **30번 주제**(`autocomplete`·`inputmode`).

## 용어 풀이

- **값 정화(value sanitization)** — 타입마다 명세가 정한 값 다듬기. 속성·스크립트로 넣을 때 돈다.
- **`typeMismatch`** — 값이 타입의 문법(`email`·`url`)에 안 맞으면 참인 깃발.
- **`checkValidity()`** — 제약을 전부 보고 유효하면 `true`. 무효면 `invalid` 이벤트를 낸다.
- **`validationMessage`** — UA 가 사용자에게 보여 줄 문구. 글자는 구현이다.
- **valid email address** — 명세가 ABNF 와 정규식으로 정한 메일 주소 모양. RFC 5322 를 **일부러** 따르지 않는다.
- **절대 URL(absolute URL)** — 스킴이 있어 기준 URL 없이 풀리는 URL. `x` 는 아니고 `javascript:alert(1)` 은 그렇다.
- **`defaultValue`** — `value` **속성**을 반영하는 프로퍼티. `.value` 와 다르다.
- **가상 키보드·입력기** — 모바일 운영체제가 띄우는 자판. 페이지는 타입·`inputmode` 로 힌트만 준다.

## 더 들어가면

- **왜 `email` 을 RFC 대로 하지 않았나** — 명세의 문장 그대로 「RFC 5322 는 @ 앞에서 너무 엄격하고, @ 뒤에서 너무 모호하며, 주석·공백·따옴표 문자열을 대부분의 사용자에게 낯선 방식으로 허용할 만큼 너무 관대하다」. 그래서 **실제로 쓰이는 모양**만 받는 정규식 하나를 명세에 박았다 — 브라우저마다 다르게 굴 여지를 없앤 것이다(이 판은 Chrome 하나라 「같다」를 확인하지 못했다).
- **왜 `tel` 에 검사가 없나** — 명세의 문장이 곧 답이다 — 전화번호 형식이 나라마다 너무 달라 **어떤 문법을 넣어도 누군가의 진짜 번호를 막는다.** 대신 `pattern` 으로 **자기 시스템의 형식**을 적으라고 한다.
- **`search` 의 `searchbox` 역할** — 보조 기술이 「검색 칸」이라고 알릴 수 있는 재료다. 검색 **영역** 전체는 `<search>` 랜드마크([11번](../11-sectioning-and-landmarks/2-summary.md))의 몫이다.
