# html/syntax/22 — `<input>` 타입 지도 ① 텍스트 계열: `text`/`password`/`email`/`url`/`tel`/`search` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스는 [21번 주제](../21-form-submission-model/3-answer.md)의 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「The input element」 절과 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ② 다** — 근거는 `typeMismatch` 깃발이고 문구가 아니다(A1·A2).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 무효는 5 / 18 — `email` 넷과 `url` 하나 · `tel` 은 0 / 3 · 손질된 칸 5 / 18

**출력**

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

**왜 그런가**

- ★★★ **무효 = `e2`(`a`) · `e4`(`한@b.kr`) · `e5`(`a@-b.kr`) · `e6`(`multiple` 없는 쉼표 목록) · `u2`(`x`)** — 넷이 `email`, 하나가 `url` 이다. **`e1`(`a@b`)은 유효**, **`u3`(`javascript:alert(1)`)도 유효**, **`tel` 셋은 전부 유효.**
- ★★ **손질된 칸 = `t1`·`n3`(줄바꿈 제거) · `e3`·`u4`(앞뒤 공백 제거) · `e7`(쉼표 뒤 공백 제거)**. `t2` 의 앞뒤 공백은 **그대로**다.
- **역할** — `search` 만 `searchbox`, 나머지는 `textbox`(`password` 포함).

### 2. 깃발은 같고 문구만 바뀐다 — `e5` 는 두 로케일 다 무엇이 틀렸는지 안 짚는다

**출력**

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

**왜 그런가**

- **무효인 칸은 1번과 같은 다섯**이다. 문구는 전부 독일어로 바뀌었다 — 명세의 getter 는 「**알맞게 현지화된 메시지**」를 돌려주라고만 한다.
- ★ **`e5` 는 「메일 주소를 입력하라」**(ko: 「이메일 주소를 입력하세요.」 · de: 「Gib eine E-Mail-Adresse ein.」) — 다른 칸은 틀린 글자를 짚는데 이 칸만 일반 문구다. **문구의 모양도 구현이다.**

### 3. 무효한 값까지 실리고, 실리는 것은 정화된 `.value` 다

**출력**

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

**왜 그런가**

- ★★★ **`t1=「줄바꿈」` · `t2=「 앞뒤 공백 」` · `e2=「a」` · `e3=「a@b.kr」` · `e7=「a@b.kr,c@d.kr」` · `u4=「http://한글.kr/경로」` · `n3=「1234」` · `p1=「비밀」`.**
- **`novalidate`** 라 무효한 `e2`·`e6`·`u2` 도 실렸다. 실린 글자는 **1번의 `.value` 열과 같다** — 속성 글자가 아니다.
- **`password` 도 맨글자**다 — 가림은 화면의 일이다.

### 4. 셋 다 `value` 속성 그대로 — `text` 와 `password` 가 직렬화에서 같다

**출력**

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

**왜 그런가**

- ★★★ **`#글`·`#비` 는 `value="속성값"`, `#빈` 은 속성 없음** — 스크립트가 `.value` 를 셋 다 「스크립트값」으로 바꿨는데 직렬화에는 **안 나왔다.** `<pre>` 에는 `.value = 스크립트값` 과 **`.defaultValue` = 속성 글자**가 찍혔다.
- ★★ **`text` 와 `password` 는 한 글자도 다르지 않다** — 직렬화가 적는 것은 **속성**이고, `.value` 는 속성을 반영하지 않는다([web-api 06번](../../../../web-api/06-attribute-vs-property/2-summary.md)). 「비밀번호라서 숨긴다」가 아니다.

### 5. `@` 뒤는 「라벨 + (점 + 라벨)*」 — 점이 0 번이어도 된다 · RFC 5322 의 「의도적 위반」

- 정규식 `…@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$` — **라벨 하나 뒤에 「점 + 라벨」이 `*`(0 번 이상)** 이다. 그래서 **`a@b` 는 유효**다(A1 의 `e1`). 라벨은 영숫자로 시작·끝나야 해서 `-b` 는 탈락하고(`e5`), `@` 앞은 ASCII 영숫자·기호만이라 `한` 은 탈락한다(`e4`).
- 명세는 이것을 **「RFC 5322 의 의도적 위반(willful violation)」** 이라 부르고, RFC 가 「**@ 앞은 너무 엄격하고, @ 뒤는 너무 모호하며, 주석·공백·따옴표 문자열을 대부분의 사용자에게 낯선 방식으로 허용할 만큼 너무 관대해서** 여기 쓰기에 실용적이지 않다」고 적는다.

### 6. 전화번호 형식이 너무 다양해서 — `pattern` 이나 `setCustomValidity()`

- 명세 — 「URL·Email 타입과 달리 Telephone 타입은 **특정 문법을 강제하지 않는다. 이것은 의도적이다.** 실제로 전화번호 칸은 **자유 양식**인 경향이 있다 — 유효한 전화번호가 매우 다양하기 때문이다」.
- 권하는 수단 — **`pattern` 속성**, 또는 **`setCustomValidity()`** 로 클라이언트 쪽 검증에 끼어드는 것(목록의 **28번 주제**가 `pattern` 의 정본이다).

### 7. 앞뒤 공백은 `email`·`url` · 줄바꿈만은 `text`·`search`·`tel`·`password` · `multiple` 은 조각마다

- 명세의 값 정화 줄 — `text`·`search`·`tel`·`password` 는 「**줄바꿈을 지운다**」, `url`·`email` 은 「줄바꿈을 지우고 **앞뒤 ASCII 공백을 지운다**」. A1 의 `t2`(그대로)와 `e3`·`u4`(지워짐)가 그 경계다.
- **`email multiple`** — 「**쉼표로 쪼개 조각마다** 앞뒤 공백을 지우고 쉼표 하나로 다시 잇는다」. `e7` 이 `"a@b.kr,c@d.kr"` 이 됐다.

### 8. 「비었거나 유효한 절대 URL」 — `javascript:` 는 유효하다 · 서버가 스킴을 거른다

- 제약 줄 — 「값이 **빈 문자열도 아니고 유효한 절대 URL 도 아니면** typeMismatch」. 스킴에 대한 조건이 없으므로 **`javascript:alert(1)` 은 유효**다(A1 의 `u3`). 상대 URL `x` 만 탈락했다.
- 받은 값을 링크로 쓰는 서버는 **허용할 스킴(`http:`·`https:`)을 스스로 거른다.** 브라우저의 `url` 타입은 그 일을 하지 않는다.

### 9. `password` 는 HTML-AAM 「대응 역할 없음」, CDP 는 `textbox` · 문구는 UA 가 정한다

- **HTML-AAM** — `input type=password` 는 「**대응하는 역할 없음**」(계산된 역할 `html-input-password`). **이 판의 CDP 트리는 `textbox`**(A1). 트리에 역할 이름을 무엇으로 찍나는 구현의 선택이다.
- **`validationMessage`** — 명세의 getter 는 제약을 어긴 칸이면 「UA 가 사용자에게 보여 줄 **알맞게 현지화된 메시지**」를 돌려주라고 한다. **글자는 UA 가 정한다**(A2 — 로케일마다 다르다).

### 10. 자판은 입력기가 띄운다 — 이 환경에 없다(제3의 상태) · 자동완성은 저장된 값과 브라우저 UI 가 없다

- 모바일 자판은 **운영체제의 입력기**가 띄우고, 페이지는 타입을 **힌트로 넘길 뿐**이다. 헤드리스 **데스크톱** Chrome 에는 띄울 입력기가 없어 **측정 대상 자체가 안 생긴다.** 자판은 실기기에 **존재하는 층**이므로 「잴 것이 없다」(제4)가 아니라 **「못 잰 것」(제3의 상태)** 이다.
- 자동완성·비밀번호 관리자 — 새 프로필에 **저장된 값이 없고**, 제안 목록은 **페이지 밖 브라우저 UI** 에 뜬다. 헤드리스에는 그 UI 가 없다 — 역시 제3의 상태다.

### 11. 정본 경계

- **`value` 속성 대 `.value`** — [web-api 06번](../../../../web-api/06-attribute-vs-property/2-summary.md). 여기는 그 결과가 `password` 직렬화에서 어떻게 보이나(A4).
- **`:invalid`·`:user-invalid`** — [CSS 10번](../../../css/syntax/10-state-and-form-pseudo-classes/2-summary.md). **`pattern`·`minlength`** — 목록의 **28번 주제**. **`autocomplete`·`inputmode`** — 목록의 **30번 주제**.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.** 하네스는 [21번](../21-form-submission-model/3-answer.md)의 `html21b-form.py`·`html21b-cdp.py` 그대로다.\
★ **로케일** — `page` 블록은 `--lang=ko-KR`(하네스가 환경 변수 `LANGUAGE=ko_KR` 로 바꿔 넘긴다)로 **고정**했다. 그 까닭(리눅스의 Chrome 이 `--lang` 플래그를 안 듣는다)은 [23번](../23-input-types-number-date/3-answer.md)의 `## 실행 검증` 에 있다.

**흔들림 확인** — 이 배치의 캡처를 **세 번** 돌렸다. 이 주제의 블록은 **세 판이 한 글자도 같았다**(재대조 결과는 [21번](../21-form-submission-model/3-answer.md)의 표와 같은 판).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **열여덟 칸 × `typeMismatch`·`checkValidity()`·`.value`·역할** | 3 | 동작 방식 (1) · A1 |
| **같은 파일의 `de-DE` 문구** | 3 | 동작 방식 (2) · A2 |
| **`novalidate` 제출 — 서버 필드** | 3 | 동작 방식 (3) · A3 |
| **`text`·`password` 의 `--dump-dom`** | 3 | 동작 방식 (4) · A4 |
| **demo 검증** | 3 | demo 절 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `password` 의 CDP 역할 | `textbox` | HTML-AAM 은 대응 역할 없음 |
| `validationMessage` 문구 | ko·de 두 벌 | 판마다 바뀔 수 있다 — 근거로 안 쓴다 |

**안 돌려 본 것** — ① **키 입력으로 줄바꿈·공백을 넣는 것**(값은 전부 속성으로 넣었다). ② **IDN 도메인의 퓨니코드 변환**. ③ **`pattern`·`minlength` 가 붙은 판** — 28번의 몫이다.

**못 잰 것** — ① **모바일 가상 키보드**. ② **자동완성·비밀번호 관리자**. ③ **스크린리더의 `password` 읽기.**

**부적용인 창** — **창 ③ · ④ · ⑥.** 입력의 값은 자식 글자도, 문서 모드도, 렌더 차단도 아니다 — **잴 것이 없다.**

## 용어 풀이

- **값 정화** — 타입마다 정한 값 다듬기(줄바꿈 · 앞뒤 공백 · 쉼표 조각).
- **`typeMismatch`** — `email`·`url` 의 문법에 안 맞으면 참.
- **valid email address** — 명세의 정규식. `@` 뒤에 점이 없어도 된다.
- **절대 URL** — 스킴이 있는 URL. `javascript:` 도 해당한다.
- **제3의 상태(못 잰 것)** — 층은 있는데 이 환경에 잴 도구·대상이 없는 것(모바일 자판).
