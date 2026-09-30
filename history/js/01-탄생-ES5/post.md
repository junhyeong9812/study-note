# JavaScript 탄생 ~ ES5 (1995 ~ 2009)

> 원본: `~/project/js-history/01-탄생-ES5.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-19).\
> 연도·인명·표준번호·코드·표는 원문 그대로다.\
> ASCII 도식 5개와 「한눈에」의 말·사전 비유(대응표 포함), 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 웹을 정적인 문서에서 동적인 애플리케이션으로 바꾼 언어의 첫 14년. 단 10일 만에 만들어진 프로토타입이 어떻게 표준이 되고, 한 번 좌초했다가, 다시 살아나 ES5라는 안정된 토대에 도달했는지를 다룬다. 핵심 질문은 늘 "언제·왜"다.

이 14년을 하나의 비유로 읽으면 **말과 사전**의 이야기다.\
본문 흐름에 쓰는 비유는 이 하나뿐이다.

| 비유 | 실체 |
|------|------|
| 급히 만들어 퍼진 새 말 | 10일 만에 설계돼 Navigator 2.0 베타에 실린 JavaScript |
| 옆 동네가 듣고 따라 만든 같은 말 | 역공학으로 만든 Microsoft의 JScript |
| 중립 기관이 펴낸 맞춤법 사전 | ECMA가 채택한 명세 ECMA-262(ECMAScript) |
| 사전을 통째로 새로 쓰자던 개정안의 무산 | ES4의 폐기 |
| 이미 쓰이던 표현을 사전이 뒤늦게 올린 판 | ES5 |

- **말이 먼저 나왔고, 사전은 뒤따라왔다.**\
  1995년 12월 Navigator 2.0 베타가 JavaScript를 탑재했고, 첫 표준은 1997년 6월에 채택된다.
- **사전이 생긴 뒤에도 동네마다 말버릇은 한동안 달랐다.**\
  1차 브라우저 전쟁기의 `document.layers`와 `document.all`이 그것이다.
- **사전을 한 번에 크게 뜯어고치려던 시도는 무산됐다.**\
  그 자리를 작게 고치는 판인 ES5가 대신 메웠다.

순서를 그림으로 보면 이렇다.

```text
구현이 먼저, 명세가 나중 — 원문이 적은 순서 그대로

1995.12        Navigator 2.0 베타가 JavaScript를 탑재           (구현 1)
1996.08        Microsoft JScript (IE 3.0) — 역공학 호환 구현    (구현 2)
                   |
                   |  "서로 다른 구현이 갈라지는 것을 막으려면
                   |   중립적인 명세가 필요했다"
                   v
1996(월 미상)  Netscape가 ECMA International에 언어를 제출
1997.06        ECMA 총회가 ECMA-262 1판(ES1)을 채택             (명세)
```

- 위 두 줄이 **구현**, 아래 두 줄이 **명세**다.
- 가운데 화살표 옆 따옴표는 원문 문장을 그대로 옮긴 것이다.
- 네 줄의 연도와 이름은 전부 원문에 있는 값이다.
- 원문은 제출 시점을 "1996년"으로만 적고 월을 밝히지 않는다 — 그래서 (**월 미상**)으로 표시했다.\
  바로 위 1996.08(JScript)과 어느 쪽이 먼저인지는 원문이 말하지 않는다.

## 시대적 배경

1990년대 중반의 웹은 정적인 HTML 문서의 모음이었다.\
링크를 누르면 새 페이지가 통째로 다시 로드됐고, 폼 입력값 하나를 검증하려 해도 서버까지 왕복해야 했다.

```text
1990년대 중반 — 폼 입력값 하나를 검증하려 해도

[브라우저]  "이 칸이 비었는지 봐 줘"  ----------->  [서버]
                                                      |
[브라우저]  <-----------------------------------------+
            답이 돌아온다 — 이 두 화살표가 "서버까지 왕복"이다
```

- 브라우저 안에는 페이지를 그 자리에서 바꿀 수단이 없었다.\
  그래서 아주 작은 판단 하나도 서버까지 갔다 와야 했다.
- 되돌아오는 화살표를 "서버까지 왕복"까지만 적은 이유가 있다.\
  원문은 폼 검증의 **응답이 무엇인지는 적지 않는다.**\
  "새 페이지가 통째로 다시 로드됐고"는 원문에서 **링크를 눌렀을 때**의 이야기다.
- 말풍선 문구는 원문의 "폼 입력값 하나를 검증하려 해도"를 그림용으로 풀어 쓴 것이다.

당시 브라우저 시장을 지배하던 Netscape는 브라우저 안에서 가볍게 돌릴 **접착제 언어(glue language)** 가 필요하다고 봤다.\
디자이너와 아마추어 프로그래머도 쓸 수 있을 만큼 쉬우면서, 페이지를 동적으로 만들 수 있는 스크립트 언어를 원했다.

> **접착제 언어(glue language)** — 이미 있는 부품들을 이어 붙여 돌아가게 만드는, 짧게 쓰는 스크립트 언어.\
> 예: 페이지의 폼과 버튼을 이어 붙여 "보내기 전에 빈칸인지 본다" 정도를 몇 줄로 적는 것.

이 시기는 동시에 두 개의 "자바"가 등장한 때이기도 하다.\
Sun의 Java(애플릿)가 브라우저의 무거운 실행 환경을 노렸다면, JavaScript는 HTML 곁에 붙는 가벼운 스크립트를 노렸다.\
이름 때문에 둘은 자주 혼동되지만, 태생도 설계 철학도 다른 별개의 언어다.

---

## 1995 — 탄생: Mocha → LiveScript → JavaScript

### 10일 만의 프로토타입

Brendan Eich는 1995년 4월 Netscape에 합류했다.\
그는 원래 브라우저에 Scheme(리스프 계열의 함수형 언어)을 넣으려고 왔지만, 경영진은 문법만큼은 당시 떠오르던 Java를 닮아야 한다고 못 박았다.\
Navigator 2.0 베타 출시 일정에 맞추기 위해, Eich는 **약 10일 만에** 언어의 첫 버전을 만들어냈다.

그 결과물은 여러 갈래의 혼혈이었다.\
이 "10일 설계"라는 제약이 이후 수십 년간 따라다닐 언어의 **장점과 결함을 동시에** 박아 넣었다.

```text
10일 설계 — 원문이 적은 세 갈래의 혼혈

Scheme 에서  ->  일급 함수(first-class function)와 클로저
Self   에서  ->  클래스 없는 프로토타입 기반 객체 모델
Java   에서  ->  if, for, while 같은 C 계열 중괄호 문법과 겉모습
                          |
                          v
                   JavaScript (1995)
```

- 화살표 셋과 그 라벨은 원문이 세 갈래로 나눠 적은 항목 그대로다.
- 원문은 이 셋의 합을 "여러 갈래의 혼혈"이라고 부른다.
- 원문이 의의를 따로 붙인 갈래는 Scheme 하나뿐이다 — 거기서 온 일급 함수와 클로저가 "JavaScript가 함수형 스타일을 품게 된 뿌리"다.\
  Self·Java 갈래에는 원문이 의의를 적지 않는다.

> **일급 함수(first-class function)** — 함수를 값처럼 변수에 담고 인자로 넘길 수 있다는 성질.\
> 예: `nums.map(function (n) { return n * 2; })`처럼 함수를 그대로 인자 자리에 넣는 것(아래 ES5 절의 코드다).

> **클로저(closure)** — 함수가 만들어진 자리의 바깥 변수를 나중에 불려도 계속 들여다보는 것.\
> 예: 바깥에서 만든 `count`를 안쪽 함수가 붙들고 있어, 그 함수를 한참 뒤에 불러도 같은 `count`를 본다.

> **프로토타입 기반 객체 모델** — 클래스라는 틀 없이, 이미 있는 객체를 원형으로 삼아 그 성질을 물려받는 방식.\
> 예: "말하기"를 가진 객체를 원형으로 삼으면, 새 객체는 그 기능을 자기 안에 다시 적지 않고도 말할 수 있다.

### 이름의 정치학

언어 이름은 짧은 시간에 세 번 바뀌었고, 그 변화 자체가 당시 Netscape의 사업적 상황을 보여준다.

- **Mocha** (1995년 5월) — Eich가 개발 중에 쓰던 내부 코드네임.
- **LiveScript** (1995년 9월) — Navigator 2.0 베타에 처음 실려 나갈 때의 이름.
- **JavaScript** (1995년 12월) — Sun Microsystems와의 마케팅 제휴 속에 공동 발표하며 최종 확정된 이름.

마지막 개명은 기술적 이유가 아니라 마케팅 때문이었다.\
당시 Java의 인기에 편승하려는 의도였다.\
1995년 12월 Navigator 2.0 베타가 JavaScript를 탑재하며 언어는 세상에 정식으로 나왔다.

**대가는 무엇인가** — 원문이 손실로 적은 문장은 이것이다.

> 이 결정이 "Java와 JavaScript는 같은 것"이라는 30년짜리 오해를 낳았다.

---

## 1996~1997 — 표준화의 시작과 첫 분열

### 마이크로소프트의 JScript

JavaScript가 성공하자 Microsoft가 곧장 따라왔다.\
1996년 8월 IE 3.0과 함께 **JScript**를 내놓았는데, 이는 라이선스를 받은 것이 아니라 JavaScript를 역공학(reverse-engineering)해 만든 호환 구현이었다(이름에 "Java"를 쓸 수 없어 "JScript"가 됐다).

> **역공학(reverse-engineering)** — 남이 만든 완성품의 동작을 밖에서 관찰해, 같은 동작을 하는 것을 따로 만들어 내는 일.\
> 예: 원문이 적은 대로 Microsoft는 라이선스 없이 JavaScript의 동작을 보고 JScript를 만들었다.

**대가는 무엇인가** — 원문이 손실로 적은 문장은 이것이다.

> 이로써 같은 언어의 미묘하게 다른 두 구현이 시장에 공존하게 됐다.

### ECMA 표준화 (ES1)

서로 다른 구현이 갈라지는 것을 막으려면 중립적인 명세가 필요했다.\
Netscape는 1996년 표준화 기구 **ECMA International**에 언어를 제출했고, 1997년 6월 ECMA 총회가 첫 번째 표준 **ECMA-262 1판**(ES1)을 채택했다.\
표준의 이름이 "JavaScript"가 아니라 **ECMAScript**가 된 것은, "JavaScript"라는 상표를 Sun(이후 Oracle)이 소유하고 있었기 때문이다.\
이때부터 "JavaScript"는 구현체의 이름, "ECMAScript"는 명세의 이름이라는 구분이 굳어졌다.

> **명세(specification) / 구현(implementation)** — 이렇게 동작해야 한다고 글로 적어 둔 것 / 그 글대로 실제로 돌아가게 만든 프로그램.\
> 예: 원문 그대로 — "JavaScript"는 구현체의 이름, "ECMAScript"는 명세의 이름이다.

> **왜 중요한가** — 표준이 생겼다는 건 어느 한 회사가 언어를 마음대로 바꿀 수 없게 됐다는 뜻이다. 이후 모든 브라우저는 "ECMAScript 몇 판을 따르는가"로 호환성을 이야기하게 된다.

---

## 1998~1999 — ES2, ES3 그리고 정규식

- **ES2** (1998년 6월) — ISO/IEC 16262 국제 표준과 정합을 맞추기 위한 판으로, 내용은 사실상 편집상의 수정에 그쳤다.
- **ES3** (1999년 12월) — 실질적인 두 번째 도약. 이후 거의 10년간 "사실상의 JavaScript"로 군림한 버전이다.

ES3가 추가한 것들은 오늘날에도 매일 쓰는 기본기다.

- **정규표현식(RegExp)** — 문자열 패턴 매칭의 표준화.
- **`try / catch / finally`** — 구조화된 예외 처리.
- **`do-while`**, `switch` 개선, 더 나은 문자열 처리와 숫자 포매팅.

> **정규표현식(RegExp)** — 문자열이 어떤 모양인지를 기호로 적어 두고 그 모양에 맞는지 맞춰 보는 도구.\
> 예: 아래 코드의 `/(\d{4})-(\d{2})-(\d{2})/`가 "숫자 4개-숫자 2개-숫자 2개" 모양을 뜻한다.

> **예외 처리(try / catch)** — 중간에 잘못되면 그 자리에서 멈추는 대신, 잘못됨을 한곳에 모아 받는 방식.\
> 예: 아래 코드에서 `throw new Error("형식 불일치")`가 나면 `catch (e)` 블록이 받는다.

```javascript
// ES3에서 비로소 표준이 된 예외 처리와 정규식
try {
  var re = /(\d{4})-(\d{2})-(\d{2})/;
  var m = "2009-12-03".match(re);
  if (!m) throw new Error("형식 불일치");
  console.log(m[1], m[2], m[3]); // 2009 12 03
} catch (e) {
  console.log("오류:", e.message);
}
```

ES3는 브라우저들이 공통으로 기댈 수 있는 안정적인 기준선을 제공했다.\
2000년대 내내 "크로스 브라우저 JavaScript"란 곧 ES3 호환을 의미했다.

---

## 1990s 후반 ~ 2000s 초 — 브라우저 전쟁과 DHTML의 혼돈

표준이 있었지만, 현실의 웹은 한동안 더 어지러웠다.\
이른바 **1차 브라우저 전쟁**(약 1995~2001)이 한창이었기 때문이다.

Netscape와 Microsoft는 표준 준수가 아니라 독자 기능 경쟁으로 맞붙었다.\
양쪽 다 **DHTML(Dynamic HTML)** — JavaScript로 HTML과 CSS를 실시간 조작해 페이지를 동적으로 만드는 기법 — 을 밀었지만, 그 수단이 서로 호환되지 않았다.

> **DHTML(Dynamic HTML)** — 원문의 정의 그대로, JavaScript로 HTML과 CSS를 실시간 조작해 페이지를 동적으로 만드는 기법.\
> 예: Netscape는 `document.layers`로, Microsoft는 `document.all`로 같은 일을 했다.

- Netscape는 `document.layers`와 비표준 `<layer>` 태그를, Microsoft는 `document.all`을 밀었다. 같은 일을 하는 코드가 브라우저마다 완전히 달랐다.
- Microsoft는 ActiveX, VBScript 같은 자사 전용 기술을 얹었다.

```text
같은 일을 하는 코드가 브라우저마다 완전히 달랐다

Netscape 쪽                        Microsoft 쪽
+----------------------------+     +----------------------------+
| document.layers            |     | document.all               |
| 비표준 <layer> 태그        |     |                            |
+----------------------------+     +----------------------------+
              \                       /
               \                     /
                v                   v
      개발자는 브라우저를 판별해 분기하는 코드를 짠다
      "이 브라우저면 이 코드, 저 브라우저면 저 코드"

칸 밖 — ActiveX, VBScript (대응 없음 — 자사 전용 기술)
```

- 두 칸의 대립축은 원문의 대립축 그대로다 — **같은 일을 하는 수단이 브라우저마다 달랐다**는 것.
- 칸 안에 적힌 이름은 원문이 **같은 일을 하는 수단**으로 양쪽에 짝지어 든 것 그대로다.
- ActiveX·VBScript는 그 짝이 아니라서 칸 밖으로 뺐다.\
  원문은 이것을 "Microsoft는 ActiveX, VBScript 같은 자사 전용 기술을 얹었다"라는 **별도 항목**으로 적고, Netscape 쪽에 맞세우지 않는다.
- 아래로 모이는 두 화살표가 원문이 적은 결과, 즉 브라우저를 판별해 분기하는 코드다.

**대가는 무엇인가** — 원문이 그 결과로 적은 문장은 이것이다.

> 그 결과 개발자들은 브라우저를 판별해 분기하는 코드를 짜야 했고("이 브라우저면 이 코드, 저 브라우저면 저 코드"), JavaScript는 "장난감 언어", "호환성 지옥"이라는 평판을 얻었다.

1997년 10월 출시된 IE 4.0이 Navigator 4.0보다 빠르고 W3C 표준을 더 충실히 따르면서 전세가 기울었고, 결국 IE가 시장을 장악하며 전쟁은 끝났다.

---

## 2000s 중반 — ES4의 좌초: 과욕의 실패

ES3 이후 위원회는 언어를 **대대적으로** 키우려 했다.\
그것이 **ES4**(ECMAScript 4)다.\
첫 초안은 1999년으로 거슬러 올라가고, 한때 2008년 10월 완성을 목표로 삼았다.

ES4의 야심은 컸다.\
클래스, 인터페이스, 네임스페이스, **선택적 정적 타입(optional static typing)**, 제너레이터 등 — JavaScript를 사실상 Java/C#급의 대형 언어로 바꾸려 했다.

그러나 ES4는 **완성되지 못하고 폐기됐다.**\
기술적 문제가 아니라 정치적 충돌이 원인이었다.

- **Adobe·Mozilla·Opera·Google** 진영은 야심 찬 ES4를 지지했다(Adobe의 ActionScript가 ES4 기반이었다).
- **Microsoft·Yahoo** 진영은 너무 급진적이고 기존 웹과의 하위 호환을 깰 위험이 크다며 반대했다.

> **하위 호환(backward compatibility)** — 새 판을 내놓아도 예전에 쓰던 코드가 그대로 돌아가는 성질.\
> 예: 원문이 적은 반대 이유가 "기존 웹과의 하위 호환을 깰 위험이 크다"였다.

위원회는 합의에 이르지 못했다.\
2008년, 양 진영은 ES4를 버리고 더 작고 점진적인 개선에 집중하기로 타협한다.\
이 화해의 산물이 **"Harmony"** 프로젝트이며, 그 첫 결실이 바로 ES5다.

> **왜 중요한가** — ES4의 실패는 이후 표준화 철학을 바꿨다. "한 번에 거대한 도약"이 아니라 "작고 합의 가능한 단위로 점진 진화"라는 원칙이 자리 잡았고, 이는 훗날 매년 릴리스하는 TC39 프로세스(ES2015+)로 이어진다.

---

## 2005 — AJAX: JavaScript의 재평가

언어 명세와 별개로, JavaScript의 위상을 송두리째 바꾼 사건은 한 편의 글에서 시작됐다.\
2005년 2월 18일, UI 디자이너 **Jesse James Garrett**이 *"Ajax: A New Approach to Web Applications"*라는 글에서 **AJAX**(Asynchronous JavaScript + XML)라는 용어를 처음 공개적으로 제시했다.

핵심 기술 자체는 새롭지 않았다.\
`XMLHttpRequest`(XHR)는 Microsoft가 1999년 IE5에 ActiveX 컴포넌트로 넣었고, Mozilla가 2002년 구현했으며, Google은 2004년 Gmail과 Google Maps에서 이미 조용히 쓰고 있었다.\
AJAX의 본질은 **페이지를 새로 로드하지 않고도 서버와 비동기로 데이터를 주고받는 것**이다.

```text
페이지 전체 리로드                   AJAX
+------------------------------+     +------------------------------+
| 링크를 누르면 통째로 리로드  |     | XMLHttpRequest가 서버로 간다 |
| 폼 검증 하나도 서버까지 왕복 |     | 데이터만 비동기로 주고받는다 |
+------------------------------+     +------------------------------+
```

- 왼쪽 두 줄은 이 편 첫머리 「시대적 배경」의 두 문장을 따로 적은 것이고(원문은 이 둘을 한 결과로 묶지 않는다), 오른쪽은 이 절이 적은 AJAX의 본질이다.
- 두 칸의 대립축은 원문의 대립축 그대로다 — **페이지를 새로 로드하느냐, 새로 로드하지 않고 데이터만 주고받느냐**.\
  오른쪽 칸의 문구는 원문의 "페이지를 새로 로드하지 않고도 서버와 비동기로 데이터를 주고받는 것"에서 온 것이다.

> **비동기(asynchronous)** — 답이 올 때까지 멈춰 서 있지 않고 다른 일을 계속하다가, 답이 오면 그때 처리하는 방식.\
> 예: 아래 코드의 `xhr.open("GET", "/data.json", true)`에서 세 번째 인자 `true`에 원문이 `// true = 비동기`라는 주석을 달아 두었고, 응답이 오면 등록해 둔 함수가 불린다.

Garrett이 한 일은 "이름을 붙인 것"이다.\
그런데 그 이름이 결정적이었다.\
Gmail처럼 페이지 리로드 없이 매끄럽게 동작하는 앱들이 이미 사람들을 놀라게 하던 차에, AJAX라는 단어가 흩어져 있던 기법들을 하나의 운동으로 묶어냈다.\
"장난감"으로 취급받던 JavaScript가 갑자기 **진지한 애플리케이션 플랫폼**으로 재조명됐고, 이른바 "Web 2.0"의 화려한 사용자 경험이 폭발적으로 늘었다.

```javascript
// AJAX의 심장 — 페이지 리로드 없이 서버와 통신
var xhr = new XMLHttpRequest();
xhr.open("GET", "/data.json", true); // true = 비동기
xhr.onreadystatechange = function () {
  if (xhr.readyState === 4 && xhr.status === 200) {
    var data = JSON.parse(xhr.responseText); // 단, 표준 JSON은 ES5에서야 들어온다
    render(data);
  }
};
xhr.send();
```

AJAX 열풍은 jQuery(2006), Prototype, Dojo 같은 라이브러리의 폭발로 이어졌다.\
브라우저 호환성의 고통을 라이브러리가 흡수해주면서, JavaScript 개발의 생산성이 비로소 실용 궤도에 올랐다.

---

## 2009 — ES5: 안정된 토대

ES3로부터 **약 10년 만인** 2009년 12월, **ECMAScript 5**(ES5)가 발표됐다.\
ES4의 거대한 야심을 접고, 기존 코드를 깨지 않으면서 언어를 다듬는 데 집중한 "현실적인" 판이다.\
화려한 새 문법보다는, 그동안 라이브러리들이 임시변통으로 메우던 구멍들을 표준으로 끌어올린 것이 핵심이다.

비유로 돌아오면 이 대목이 **이미 쓰이던 표현을 사전이 뒤늦게 올린 판**이다.

### Strict Mode (엄격 모드)

`"use strict";` 한 줄로 켜는, 더 엄격한 파싱·오류 처리 모드다.\
새 문법을 도입하지 않으면서, 조용히 넘어가던 실수를 에러로 드러낸다.\
선언 없는 전역 변수 생성 금지, 안전하지 않은 `this` 바인딩 제거 등 — JavaScript의 "느슨함"이 낳던 버그를 개발 단계에서 잡아준다.

> **엄격 모드(strict mode)** — `"use strict";` 한 줄로 켜는, 더 엄격한 파싱·오류 처리 모드(원문의 정의 그대로).\
> 예: 아래 코드에서 선언 없이 `undeclared = 10`을 쓰면 `ReferenceError`가 난다 — 비엄격 모드라면 전역 변수가 조용히 생겼을 자리다.

```javascript
"use strict";
function f() {
  undeclared = 10; // ReferenceError — 비엄격 모드라면 전역 변수가 조용히 생겼을 것
}
```

### 네이티브 JSON

그동안 JSON 파싱은 위험한 `eval()`이나 외부 라이브러리에 의존했다.\
ES5는 이를 언어에 내장했다.

- `JSON.parse(text)` — JSON 문자열을 객체로.
- `JSON.stringify(obj)` — 객체를 JSON 문자열로.

> **JSON** — 데이터를 주고받을 때 쓰는 문자 형식. 그 글자를 프로그램이 쓸 수 있는 객체로 되돌리는 일이 "파싱"이다.\
> 예: `JSON.parse(text)`가 그 문자열을 객체로, `JSON.stringify(obj)`가 객체를 다시 문자열로 바꾼다.

AJAX 시대에 데이터 교환의 사실상 표준이 XML에서 JSON으로 넘어가던 흐름과 정확히 맞물린 변화다.

### Array 반복 메서드

함수형 스타일의 배열 처리가 표준이 됐다.\
이전까지는 `for` 루프로 일일이 돌리거나 라이브러리에 기대야 했다.

```javascript
var nums = [1, 2, 3, 4];
var doubled = nums.map(function (n) { return n * 2; });      // [2,4,6,8]
var evens   = nums.filter(function (n) { return n % 2 === 0; }); // [2,4]
var sum     = nums.reduce(function (a, b) { return a + b; }, 0); // 10
nums.forEach(function (n) { console.log(n); });
```

표준화된 메서드: `forEach`, `map`, `filter`, `reduce`, `reduceRight`, `every`, `some`, `indexOf`, `lastIndexOf`, 그리고 타입 판별용 `Array.isArray`.

### Getter / Setter 와 객체 메타프로그래밍

속성을 읽고 쓸 때의 동작을 함수로 정의하는 접근자 속성(get/set), 그리고 객체의 동작을 세밀하게 제어하는 메서드들이 들어왔다.

> **접근자 속성(get / set)** — 속성을 읽고 쓸 때의 동작을 함수로 정의한 것(원문의 정의 그대로).\
> 예: 아래 코드에서 `temp.fahrenheit = 212`라고 쓰면 `set` 함수가 돌아 `_c`가 100이 된다.

> **객체 메타프로그래밍** — 값이 아니라 객체의 동작 자체를 코드로 다루는 것.\
> 예: 아래 코드의 `Object.defineProperty(o, "id", { value: 42, writable: false })`는 그 속성을 고쳐 쓸 수 있는지까지 지정한다.

```javascript
var temp = {
  _c: 0,
  get fahrenheit() { return this._c * 9 / 5 + 32; },
  set fahrenheit(f) { this._c = (f - 32) * 5 / 9; }
};
temp.fahrenheit = 212;
console.log(temp._c); // 100

// 객체 제어 메서드
var o = Object.create(null);            // 프로토타입 없는 깨끗한 객체
Object.defineProperty(o, "id", {        // 속성 속성(writable/enumerable…) 직접 제어
  value: 42, writable: false
});
console.log(Object.keys(temp));         // 열거 가능한 키 배열
```

추가된 `Object.create`, `Object.defineProperty`, `Object.keys`, `Object.freeze` 등은 라이브러리 저자들이 견고한 추상화를 만들 수 있는 도구가 됐다.

> **ES5의 의의** — ES5는 새 패러다임을 들고 오지 않았다. 대신 ES3 이후 현장이 라이브러리로 메우던 공백(JSON, 배열 함수, 엄격 모드)을 언어 자체로 흡수해 **모두가 공유하는 견고한 바닥**을 깔았다. 이 안정된 토대 위에서, 6년 뒤 진짜 큰 도약인 ES2015(ES6)가 가능해진다.

---

## 14년의 궤적 요약

*(이 편에는 「남긴 것」에 해당하는 별도 절이 없다 — 원문의 결론은 바로 위 「ES5의 의의」와 아래 표다. 표는 원문 그대로 옮긴 것이다.)*

| 시점 | 사건 | 핵심 의미 |
|------|------|-----------|
| 1995.05~12 | Mocha → LiveScript → JavaScript | Eich가 10일 만에 설계, Java 마케팅에 편승해 개명 |
| 1996.08 | Microsoft JScript (IE3) | 역공학 구현 — 분열의 시작 |
| 1997.06 | ES1 (ECMA-262 1판) | 명세=ECMAScript, 구현=JavaScript 분리 |
| 1999.12 | ES3 | 정규식·예외처리 — 10년간의 사실상 표준 |
| ~2001 | 1차 브라우저 전쟁 / DHTML | 비표준 경쟁, 호환성 지옥 |
| ~2008 | ES4 폐기 | 과욕+정치 충돌 → "점진 진화"로 노선 전환 |
| 2005.02 | AJAX 명명 | JavaScript의 재평가, Web 2.0 |
| 2009.12 | ES5 | strict mode·JSON·배열 메서드·get/set — 안정된 토대 |

---

## 용어 풀이

- **접착제 언어(glue language)** — 이미 있는 부품들을 이어 붙여 돌아가게 만드는, 짧게 쓰는 스크립트 언어.
- **일급 함수(first-class function)** — 함수를 값처럼 변수에 담고 인자로 넘길 수 있다는 성질. Scheme에서 온 갈래다.
- **클로저(closure)** — 함수가 만들어진 자리의 바깥 변수를 나중에도 계속 들여다보는 것.
- **프로토타입 기반 객체 모델** — 클래스 틀 없이 이미 있는 객체를 원형으로 삼는 객체 방식. Self에서 온 갈래다.
- **역공학(reverse-engineering)** — 완성품의 동작을 밖에서 보고 같은 동작을 하는 것을 따로 만드는 일. JScript가 그렇게 만들어졌다.
- **명세(specification) / 구현(implementation)** — 글로 적어 둔 규정 / 그 규정대로 돌아가는 프로그램. ECMAScript가 명세, JavaScript가 구현체의 이름이다.
- **ECMA-262 / ECMAScript** — 1997년 6월 ECMA 총회가 채택한 표준 문서와 그 표준의 이름.
- **정규표현식(RegExp)** — 문자열의 모양을 기호로 적어 맞춰 보는 도구. ES3에서 표준화됐다.
- **예외 처리(try / catch / finally)** — 잘못됨을 한곳에 모아 받는 구조. ES3에서 표준화됐다.
- **DHTML(Dynamic HTML)** — JavaScript로 HTML과 CSS를 실시간 조작해 페이지를 동적으로 만드는 기법.
- **하위 호환(backward compatibility)** — 새 판을 내도 예전 코드가 그대로 도는 성질. ES4 반대의 이유였다.
- **선택적 정적 타입(optional static typing)** — ES4가 넣으려 했던 기능 중 하나.
- **Harmony** — ES4를 접고 작고 점진적인 개선에 집중하기로 한 2008년 타협이 낳은 프로젝트. 첫 결실이 ES5다.
- **AJAX(Asynchronous JavaScript + XML)** — 페이지를 새로 로드하지 않고 서버와 비동기로 데이터를 주고받는 것.
- **비동기(asynchronous)** — 답을 기다리며 멈추지 않고 다른 일을 계속하는 방식.
- **`XMLHttpRequest`(XHR)** — AJAX의 심장. 1999년 IE5에 ActiveX 컴포넌트로 처음 들어갔다.
- **엄격 모드(strict mode)** — `"use strict";` 한 줄로 켜는 더 엄격한 파싱·오류 처리 모드.
- **JSON** — 데이터 교환용 문자 형식. ES5에서 `JSON.parse`·`JSON.stringify`가 언어에 내장됐다.
- **접근자 속성(get / set)** — 속성을 읽고 쓸 때의 동작을 함수로 정의한 것.
- **객체 메타프로그래밍** — 값이 아니라 객체의 동작 자체를 코드로 다루는 것. `Object.defineProperty` 등.

---

## 참고 출처

- [Brendan Eich - Wikipedia](https://en.wikipedia.org/wiki/Brendan_Eich)
- [1995: The Birth of JavaScript - Cybercultural](https://cybercultural.com/p/1995-the-birth-of-javascript/)
- [ECMAScript version history - Wikipedia](https://en.wikipedia.org/wiki/ECMAScript_version_history)
- [ECMAScript - Wikipedia](https://en.wikipedia.org/wiki/ECMAScript)
- [The browser wars and the birth of JavaScript - Red Hat Developer](https://developers.redhat.com/blog/2019/07/23/the-browser-wars-and-the-birth-of-javascript)
- [Browser wars - Wikipedia](https://en.wikipedia.org/wiki/Browser_wars)
- [Ajax (programming) - Wikipedia](https://en.wikipedia.org/wiki/Ajax_(programming))
- [What Does AJAX Even Stand For? - The History of the Web](https://thehistoryoftheweb.com/what-does-ajax-even-stand-for/)
- [John Resig - ECMAScript 5 Strict Mode, JSON, and More](https://johnresig.com/blog/ecmascript-5-strict-mode-json-and-more/)
- [JavaScript ES5 (JS 2009) - GeeksforGeeks](https://www.geeksforgeeks.org/javascript/javascript-es5-js-2009/)
