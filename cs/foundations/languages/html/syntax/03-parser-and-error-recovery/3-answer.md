# html/syntax/03 — 파서와 오류 복구: 태그 수프가 트리가 되는 과정·암묵 태그 삽입 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** `--dump-dom` 으로 읽은 것이다. 하네스는 맨 아래 `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「Parsing HTML documents」로 접지했다.\
> ★ **엔진은 Chrome 하나다.** 다만 **이 주제의 트리 모양은 명세가 알고리즘째 규정**하므로 관찰이면서 동시에 명세 보장이다 — 예외는 XML `parsererror` 의 문구·`style` 과 stderr 동작뿐이다(A7).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. 문단 하나가 요소 셋으로 쪼개진다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-p-div.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>p 안에 쓴 div</title>
<p>앞<div>안</div>뒤</p>
===== dom html01b-p-div.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>p 안에 쓴 div</title>
</head><body><p>앞</p><div>안</div>뒤<p></p>
</body></html>
(exit 0)
```

**트리**

```text
   body
     p                 <- 내가 연 p
       #text "앞"
     div               <- p 를 닫고 body 에 붙었다
       #text "안"
     #text "뒤"        <- ★ p 밖이다
     p                 <- ★ 짝 없는 </p> 가 만든 '빈 p'
       (자식 없음)
     #text "\n"
```

- `body` 의 직계 자식은 **다섯**이다 — `p` · `div` · 텍스트 `"뒤"` · **빈 `p`** · 줄바꿈 텍스트.

**`뒤` 는 어디에 있는가**

- **어느 요소 안도 아니다** — `body` 의 직계 텍스트 노드다.

**소스에 없는데 생긴 것**

- **빈 `<p></p>`** 하나. **짝 없는 `</p>` 가 만들었다.**
- 명세의 「in body」 규칙이 「`</p>` 를 만났는데 열린 `p` 가 없으면 **`<p>` 시작 태그를 넣은 것처럼 처리하고 바로 닫아라**」고 적어 뒀다.

**`p { color: red }` 를 주면**

- **「앞」만 빨개진다.** 「안」은 `div` 안이고 「뒤」는 `p` 밖이다.
- ★ 증상이 「일부 글자만 스타일이 다르다」라 **원인을 CSS 에서 찾게 된다.** 마크업이 원인이다.

### 2. 표는 `tbody` 를 끼워 넣는다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-implied.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>암묵으로 끼워 넣는 것</title>
<table><tr><td>셀</td></tr></table>
<select><option>가</option></select>
===== dom html01b-implied.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>암묵으로 끼워 넣는 것</title>
</head><body><table><tbody><tr><td>셀</td></tr></tbody></table>
<select><option>가</option></select>
</body></html>
(exit 0)
```

**`table` 의 직계 자식**

- **`tbody` 하나**다. 내가 쓴 `<tr>` 은 그 안에 있다.

**`select` 쪽**

- **삽입이 없다.** `select > option` 그대로다. **모든 부모가 끼워 넣는 게 아니라 표 계열이 특별**하다.

**`table > tr` 선택자**

- **0개**를 잡는다. 트리에는 `table > tbody > tr` 만 있다.
- 고치려면 `table tr`(자손) 또는 `table > tbody > tr`.

**02번 주제의 「생략 가능 태그」와 같은가**

- **아니다.**

```text
   생략 가능 태그 (02번)              암묵 삽입 (여기)
   +---------------------------+     +---------------------------+
   | 끝 태그를 안 써도 된다     |     | 시작 태그째 없는데         |
   | </li> · </p> · </td>       |     | 요소가 생긴다              |
   | -> 유효한 마크업           |     | -> 파서가 채운 것          |
   +---------------------------+     +---------------------------+
```

- 다만 **`<tbody>` 는 「시작 태그 생략도 허용」 목록에도 있다** — 그래서 이 경우는 **유효하면서 동시에 삽입**이다. 무효한 삽입의 예는 A3 이다.

### 3. 표 안의 `div` 는 표 앞으로 밀려난다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-foster.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>표 밖으로 밀려나는 것</title>
<table><div>표 안에 쓴 div</div><tr><td>셀</td></tr></table>
===== dom html01b-foster.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>표 밖으로 밀려나는 것</title>
</head><body><div>표 안에 쓴 div</div><table><tbody><tr><td>셀</td></tr></tbody></table>
</body></html>
(exit 0)
```

**`div` 의 자리**

- **`table` 의 바로 앞 형제**다. `body > div, table` 순서다.

**내용은 남았는가**

- **남았다.** 「표 안에 쓴 div」라는 글자가 그대로 있다 — **버려진 게 아니라 옮겨졌다.**

**`table.previousElementSibling`**

- **그 `div`** 다.

**이름과 이유**

- **foster parenting**(위탁 양육)이다. 「표가 못 받아 주는 자식을 **바로 앞의 자리에 맡긴다**」는 뜻이다.
- ★ **버리는 것이 아니라 맡기는 것**이라는 게 이름의 요점이다. CSS 의 오류 복구가 **버리는** 것과 대비된다.

```text
   내가 쓴 것                      트리
   <table>                         body
     <div>…</div>   ----------->     div        <- 표 '앞'으로
     <tr><td>…</td></tr>             table
   </table>                            tbody
                                         tr
                                           td
```

### 4. `<i>` 를 하나 썼는데 둘이 된다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-adoption.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>잘못 겹친 서식 태그</title>
<p><b>굵게<i>둘 다</b>기울임만</i>맨몸</p>
<p><em>하나<strong>둘</em>셋</strong>넷</p>
===== dom html01b-adoption.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>잘못 겹친 서식 태그</title>
</head><body><p><b>굵게<i>둘 다</i></b><i>기울임만</i>맨몸</p>
<p><em>하나<strong>둘</strong></em><strong>셋</strong>넷</p>
</body></html>
(exit 0)
```

**첫 문단의 `i` 개수**

- **둘**이다. 하나는 `b` 안(`<i>둘 다</i>`), 하나는 `b` 밖(`<i>기울임만</i>`).

**「기울임만」이 있는 곳**

- **`p > i`** 안이다. `b` 안이 **아니다** — `</b>` 로 굵기가 끊겼으므로.

**화면으로 잡을 수 있는가**

- ★ **없다.** 화면 결과가 **내 의도와 거의 같다** — 「굵게」는 굵고, 「둘 다」는 굵고 기울고, 「기울임만」은 기울었다.
- 갈리는 것은 **요소 개수와 구조**뿐이다. **창 ① 로만 보인다.**

**알고리즘 이름**

- **adoption agency algorithm**. 명세에서 가장 긴 알고리즘 중 하나로, 번호 붙은 단계가 스무 개 가까이 된다.
- 두 번째 문단(`<em>`/`<strong>`)도 **같은 모양**이다 — **서식 요소 목록**에 든 태그는 전부 이 대우를 받는다.

### 5. `</br>` 만 특별하다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-close-void.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>닫는 태그로 쓴 빈 요소</title>
<p>앞</br>뒤</p>
<p>앞</img>뒤</p>
<p>앞</hr>뒤</p>
===== dom html01b-close-void.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>닫는 태그로 쓴 빈 요소</title>
</head><body><p>앞<br>뒤</p>
<p>앞뒤</p>
<p>앞뒤</p>
</body></html>
(exit 0)
```

**세 문단의 트리**

| 소스 | 트리 |
|---|---|
| `앞</br>뒤` | `앞<br>뒤` — **`<br>` 요소가 생겼다** |
| `앞</img>뒤` | `앞뒤` — 사라졌다 |
| `앞</hr>뒤` | `앞뒤` — 사라졌다 |

**다른 대우를 받는 것과 이유**

- **`</br>`** 이다. 명세의 「in body」 규칙에 「**`</br>` 을 만나면 `<br>` 시작 태그로 처리하라**」고 명문으로 적혀 있다.
- **웹에 이미 `</br>` 로 줄바꿈하는 문서가 많았기 때문**이다 — 오류 복구가 **화석을 명세에 박아 넣은** 대표 사례다.

**「빈 요소의 닫는 태그는 무시된다」가 맞는가**

- **틀렸다.** `</br>` 은 요소를 **만들고**, `</img>`·`</hr>` 은 무시된다. **규칙이 태그마다 다르다.**

**`</p>` 는 어느 쪽인가**

- **`</br>` 쪽**이다 — 열린 `p` 가 없으면 **빈 `p` 를 만든다**(A1). `p` 는 빈 요소가 아닌데도 같은 「만들어 주는」 대우를 받는다.
- ★ 그러므로 외울 것은 규칙 하나가 아니라 「**태그마다 명세에 따로 적혀 있다**」는 사실이다.

### 6. 「오류」는 이름표이고 「복구」는 규정된 교정이다

**출력** (Chrome 151 headless)

```text
===== 소스: html01b-garbage.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>기호 범벅</title>
<<<>>><p><<<b>>>x</p><3 > 2
===== dom html01b-garbage.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>기호 범벅</title>
</head><body>&lt;&lt;&lt;&gt;&gt;&gt;<p>&lt;&lt;<b>&gt;&gt;x</b></p><b>&lt;3 &gt; 2
</b></body></html>
(exit 0)
```

```text
===== for f in html01b-p-div.html html01b-garbage.html html01b-xml-bad.xhtml; do echo "$f  마크업 관련 stderr 줄 수 = $(google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr --dump-dom $f 2>&1 >/dev/null | grep -cE 'mismatch|parse error|unexpected|Opening and ending|tag')"; done =====
html01b-p-div.html  마크업 관련 stderr 줄 수 = 0
html01b-garbage.html  마크업 관련 stderr 줄 수 = 0
html01b-xml-bad.xhtml  마크업 관련 stderr 줄 수 = 0
(exit 0)
```

**「오류」와 「복구」**

- **오류** = 명세가 「무효」라고 **이름 붙인 입력**(parse error). 유효성의 문제이지 실행의 문제가 아니다.
- **복구** = 그 입력에 대해 **명세가 정해 둔 트리를 만드는 것**. 「대충 넘어간다」가 아니라 「**정해진 대로 고친다**」이다.

**알려 주는 방법**

- **없다.** 실측에서 기호 범벅(`<<<>>><p><<<b>>>x</p><3 > 2`)도 트리가 나왔고, **마크업 관련 stderr 줄이 0개**였다.
- 개발자 도구 Console 에도 안 찍힌다(headless 라 UI 는 확인하지 못했다 — **미실행**).

**`(exit N)` 이 같은 이유**

- **전부 `0`** 이다. **HTML 에는 「파싱 실패」라는 상태가 없다.**

**종료 코드는 근거가 되는가**

- ★ **안 된다.** 「안 흔들리는 칸」이지만 **언제나 같은 값이라 정보가 없다.**
- 이 갈래에서 근거가 되는 것은 **트리 그 자체**다.

### 7. 명세 칸이 큰 주제

**갈라 보기**

| 명세 보장 | 구현 관찰 |
|---|---|
| `<div>` 가 `<p>` 를 닫는 것 | `parsererror` 요소의 **이름·문구·인라인 `style`** |
| 짝 없는 `</p>` 가 빈 `p` 를 만드는 것 | **stderr 에 아무것도 안 찍히는 것** |
| `tbody` 삽입 · foster parenting | `--dump-dom` 의 **줄바꿈 자리**(직렬화 + 도구) |
| adoption agency 의 결과 트리 | |
| `</br>` → `<br>` · `</img>` 무시 | |
| EOF 가 전부 닫는 것 · 파싱이 안 멈추는 것 | |

**다른 언어의 같은 표와 비교하면**

- ★ **정반대 모양**이다. 보통은 「구현 정의」 칸이 크고 명세 칸이 작은데, 이 주제는 **명세 칸이 압도적으로 크다.**
- **HTML 은 「명세가 오류 복구까지 정한」 드문 언어**이기 때문이다.

**역사적 이유**

- HTML 4 까지 명세는 **유효한 문서만** 규정했고 **무효한 문서의 처리는 브라우저 재량**이었다.
- 그래서 「이 브라우저에서만 되는 페이지」가 생겼다. HTML5 는 **무효한 입력의 처리까지 규정**해 그 분기를 없앴다.

**「브라우저마다 다르다」는 어디까지 참인가**

- **이 주제에서는 거의 거짓**이다 — 트리 모양은 명세가 정한다.
- **참인 자리는 위 표의 오른쪽 칸**뿐이다. ★ 다만 **이 판은 Chrome 하나로만 확인**했으므로 「모든 브라우저가 같다」는 **명세를 근거로 한 서술**이지 이 판의 관찰이 아니다.

### 8. XML 파서는 멈춘다

**출력** (Chrome 151 headless — 같은 마크업, 확장자만 다름)

```text
===== 소스: html01b-html-same.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>HTML 파서</title>
<p>앞<b>굵게</p></b>
===== dom html01b-html-same.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>HTML 파서</title>
</head><body><p>앞<b>굵게</b></p>
</body></html>
(exit 0)
```

```text
===== 소스: html01b-xml-bad.xhtml =====
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>XML 파서</title></head>
<body><p>앞<b>굵게</p></b></body>
</html>
===== dom html01b-xml-bad.xhtml =====
<html xmlns="http://www.w3.org/1999/xhtml"><parsererror style="display: block; white-space: pre; border: 2px solid #c77; padding: 0 1em 0 1em; margin: 1em; background-color: #fdd; color: black"><h3>This page contains the following errors:</h3><div style="font-family:monospace;font-size:12px">error on line 3 at column 20: Opening and ending tag mismatch: b line 3 and p
</div><h3>Below is a rendering of the page up to the first error.</h3></parsererror>
<head><title>XML 파서</title></head>
<body><p>앞<b></b></p></body></html>
(exit 0)
```

**`.xhtml` 로 주면**

- **문서 대신 에러가 나온다.** 루트 바로 안에 **`parsererror` 요소**가 끼워지고, 본문은 **첫 에러 직전까지만** 남는다(`<b></b>` 가 비어 있다).
- 같은 마크업을 `.html` 로 주면 **`<p>앞<b>굵게</b></p>`** — 조용히 닫아 준다.

**에러가 나타나는 곳**

- **트리**다. 콘솔이 아니다 — 실측에서 이 파일도 **마크업 관련 stderr 줄이 0개**였다(A6 블록의 셋째 줄).

**메시지를 근거로 쓸 수 있는가**

- ★ **부분적으로만.** 「**에러 요소가 끼워졌다**」는 사실은 근거가 되지만, **`parsererror` 라는 이름·문구·인라인 `style` 은 명세 밖**이라 흔들릴 수 있다. 머리말의 「흔들리는 칸」 표에 그렇게 선언해 뒀다.

**설명하는 사건**

- **XHTML 의 좌초**다. 「엄격하게 하자」는 시도가 **오타 하나로 페이지 전체를 못 보게** 만들었고, 웹은 관대한 쪽을 골랐다.
- 역사는 [`../../../../../../history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md)가 정본이다 — 여기는 그 선택의 **오늘의 실물**만 보였다.

### 9. 화면으로 잡히는 것과 안 잡히는 것

**갈라 보기**

| | 화면으로 잡히나 |
|---|---|
| `<p><div>` 가 문단을 쪼개는 것 | **잡힌다** — 상자가 둘이 되고 「뒤」가 밖으로 나온다 |
| `tbody` 삽입 | 안 잡힌다(화면은 똑같다) — **선택자가 안 먹을 때** 드러난다 |
| foster parenting | **잡힌다** — 내용이 표 위에 뜬다 |
| adoption agency | ★ **안 잡힌다** — 화면 결과가 의도와 거의 같다 |
| `</br>` → `<br>` | **잡힌다** — 줄이 바뀐다 |

**「화면이 맞으니 구조도 맞겠지」가 틀리는 사례**

- **adoption agency** 가 정확히 그것이다. 실측에서 `<i>` 가 둘이 됐는데 **화면은 내 의도대로** 보였다.

**창과 그 한계**

- **창 ①**(`--dump-dom`)이 이 주제의 전부에 가깝다.
- 부족한 자리 — **「요소가 몇 개인가」를 셀 때**는 눈으로 세는 것보다 **창 ②**(`querySelectorAll().length`)가 확실하고, 「**내가 쓴 것이 무효인가**」는 어느 창으로도 안 나온다(validator 가 없다 — [01번 주제](../01-document-skeleton/3-answer.md) A8).

**외우기와 던지기**

- **던지기가 빠르다.** 콘텐츠 모델은 요소마다 다르고 예외가 많아, 「이거 넣어도 되나」는 **한 줄짜리 파일을 만들어 창 ① 로 보는 것**이 가장 싸다.

### 10. 버리는 파서와 고치는 파서

**한 문장**

- **CSS 는 모르는 것을 버리고, HTML 은 모르는 것을 고쳐서 쌓는다.** 둘 다 아무 말도 안 한다.

**서버 파서와 브라우저 파서가 다르면**

- 정제기가 **자기 트리**로 「안전하다」고 판단했는데 브라우저가 **다른 트리**를 만들면, 걸러 낸 것이 되살아난다.
- 예: 정제기가 `<table><div onclick=…>` 을 표 안의 무해한 노드로 보고 넘겼는데, 브라우저는 **표 앞으로 밀어내** 활성 영역에 놓는 식.
- ★ **이 판에서 정제기는 돌려 보지 않았다** — 재현하지 못한 시나리오다.

**02번 주제의 같은 집안**

- **중복 속성**이다. 「첫 것이 이긴다」를 두 구현이 **똑같이** 지켜야 필터가 성립한다.

**`innerHTML` 은**

- **같은 알고리즘을 거친다**(fragment parsing — 문맥 요소에 맞춰 삽입 모드를 정해 놓고 돌린다).
- 다만 **그 API 표면은 web-api 갈래가 정본**이다. 이 갈래는 **파서가 만든 트리의 모양**까지다.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless. **엔진은 이것 하나다.** **마크업 검증기는 없다.**

**하네스** — 01\~04 네 주제가 공유한다. 블록의 배너에 적힌 `dom`·`probe`·`nojs` 가 이 셋이다.

```bash
# html01b-harness.sh
dom()   { google-chrome --headless --disable-gpu --no-sandbox --dump-dom "$1" 2>/dev/null; }
probe() { sed -n '/^###P###$/,/^###E###$/p' | sed '1d;$d' \
          | sed 's/&lt;/</g; s/&gt;/>/g; s/&amp;/\&/g'; }
nojs()  { sed '/^<script>$/,$d'; }
```

- ★ **이 주제의 블록에는 프로브 스크립트를 안 넣었다.** `<script>` 가 트리에 섞이면 **관찰 대상인 트리 자체가 바뀌기** 때문이다 — 전부 **순수 마크업 + 날것의 `--dump-dom`** 이다.
- ★ **`--virtual-time-budget` 은 쓰지 않는다**(정본 규칙).
- **stderr 를 세는 블록**은 `grep -c` 를 마지막 명령으로 두지 않았다 — 0건일 때 종료 코드가 1이 되어 **「0건」이 실패로 기록**되기 때문이다. `echo "… = $(… | grep -c …)"` 로 감쌌다.

**demo 블록 검증** — 문서의 `demo` 블록에 래퍼와 측정 프로브를 붙인 사본을 따로 띄워 `보이는 것` 을 확인했다.

```text
===== 소스: html01b-demo03b.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 03b 검증</title>
<body>
<p>앞<div>안</div>뒤</p>
<style>
  p { border: 2px solid #2563eb; padding: 4px; margin: 4px 0; min-height: 1em; }
  div { border: 2px dashed #b91c1c; padding: 4px; }
</style>
<script>
const o = [];
const ps = document.querySelectorAll("p");
o.push("p 요소 개수 = " + ps.length);
ps.forEach((p, i) => o.push("p[" + i + "] textContent = " + JSON.stringify(p.textContent)
  + "   높이 = " + p.getBoundingClientRect().height));
o.push("body 직계 자식 = " + [...document.body.children].map(e => e.localName).join(", "));
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-demo03b.html | probe =====
p 요소 개수 = 2
p[0] textContent = "앞"   높이 = 36
p[1] textContent = ""   높이 = 28
body 직계 자식 = p, div, p, style, script
(exit 0)
```

- `p` 요소가 **2개**, 첫 것의 `textContent` 가 `"앞"`(높이 36), 둘째가 `""`(높이 28) — **빈 상자가 실제로 그려진다.**
- `body` 의 직계 자식이 `p, div, p, style, script` — 트리가 [2-summary.md](2-summary.md) 의 그림과 같다.

`바꿔 볼 것` 에 적은 두 단언도 따로 던졌다.

```text
===== 소스: html01b-demo03c.html (demo 블록 + 래퍼 + 측정 프로브) =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>demo 03 의 '바꿔 볼 것' 검증</title>
<body>
<p class="v1">앞<span>안</span>뒤</p>
<hr>
<p class="v2">앞<div>안</div>뒤
<style>
  p   { border: 2px solid #2563eb; padding: 4px; margin: 4px 0; min-height: 1em; }
  div { border: 2px dashed #b91c1c; padding: 4px; }
</style>
<script>
const o = [];
o.push("v1(div 를 span 으로) p 개수 = " + document.querySelectorAll("p.v1").length
       + "   textContent = " + JSON.stringify(document.querySelector("p.v1").textContent));
o.push("v2(</p> 를 지움)     p 개수 = " + document.querySelectorAll("p").length
       + "   그중 빈 p = " + [...document.querySelectorAll("p")].filter(p => p.textContent === "").length);
const q = document.createElement("pre");
q.textContent = "\n###P###\n" + o.join("\n") + "\n###E###\n";
document.body.appendChild(q);
</script>
===== dom html01b-demo03c.html | probe =====
v1(div 를 span 으로) p 개수 = 1   textContent = "앞안뒤"
v2(</p> 를 지움)     p 개수 = 2   그중 빈 p = 0
(exit 0)
```

- `<div>` → `<span>` 으로 바꾸면 **`p` 가 하나**이고 `textContent` 가 `"앞안뒤"` — 한 상자로 합쳐진다.
- `</p>` 를 지우면 **빈 `p` 가 0개** — 빈 상자가 사라진다.

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| `<p><div>x</div></p>` 의 트리 | 2 | 동작 방식 (1) · A1 |
| `<table><tr>` 의 `tbody` 삽입 + `select` 대조 | 2 | 동작 방식 (2) · A2 |
| 표 안 `div` 의 foster parenting | 2 | 동작 방식 (3) · A3 |
| 잘못 겹친 서식 태그 두 벌(`b`/`i`, `em`/`strong`) | 2 | 동작 방식 (4) · A4 |
| `</br>`·`</img>`·`</hr>` 세 경우 | 2 | 동작 방식 (5) · A5 |
| 기호 범벅(`<<<>>>`·`<<<b>`·`<3 > 2`) | 2 | 동작 방식 (6) · A6 |
| **stderr 마크업 줄 수 세 파일** | 2 | 동작 방식 (6) · A6 · A8 |
| 끝까지 안 닫은 문서(EOF) | 2 | 동작 방식 (7) |
| **같은 마크업의 `.html` 대 `.xhtml`** | 2 | 동작 방식 (8) · A8 |
| **demo 블록**과 그 `바꿔 볼 것` 두 단언 | 2 | 동작 방식 (1) |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `parsererror` 의 이름·문구·인라인 `style` | `"error on line 3 at column 20: Opening and ending tag mismatch: b line 3 and p"` | **명세 밖이다** — 근거로 쓸 것은 「에러 요소가 끼워졌다」는 사실뿐 |
| stderr 마크업 줄 수 | **0** | 명세는 로그를 규정하지 않는다 |
| `--dump-dom` 의 줄바꿈 자리 | 소스의 텍스트 노드를 그대로 | 직렬화 + 도구 |

**안 돌려 본 것** — ① **Firefox·Safari 재현**(엔진이 없다). 「모든 브라우저가 같은 트리를 만든다」는 **명세를 근거로 한 서술**이고 이 판의 관찰이 아니다. ② **개발자 도구 Console 의 실제 표시**(headless 라 UI 가 없다) — 「Console 에도 안 찍힌다」는 **미실행**이다. ③ **서버 쪽 정제기와의 트리 불일치**(A10) — 정제기가 없다. ④ **`innerHTML` 의 fragment parsing** — web-api 갈래 표면이라 던지지 않았다. ⑤ **`<template>` 안의 파싱**([목록의 **10번 주제**](../10-template-slot-shadow-dom/)) · **SVG·MathML 의 외래 콘텐츠 규칙**.

## 용어 풀이

- **태그 수프(tag soup)** — 문법을 안 지킨 HTML. 브라우저가 어떻게든 읽어 내던 시절의 이름이다.
- **삽입 모드(insertion mode)** — 파서의 현재 상태. 「initial」·「in head」·「in body」·「in table」 등.
- **트리 구축(tree construction)** — 토큰을 받아 DOM 트리를 쌓는 뒷단. 오류 복구가 여기서 일어난다.
- **파스 오류(parse error)** — 명세가 무효라고 이름 붙인 입력. **트리도 안 바꾸고 파싱도 안 멈춘다.**
- **암묵 삽입(implied element)** — 소스에 없는 요소를 파서가 끼워 넣는 것. `html`·`head`·`body`·`tbody`.
- **foster parenting** — 표가 못 받는 자식을 **표 바로 앞**에 맡기는 동작. **버리지 않는다.**
- **adoption agency algorithm** — 잘못 겹친 서식 요소를 **다시 열어** 트리를 바로잡는 알고리즘.
- **서식 요소(formatting element)** — `a`·`b`·`i`·`em`·`strong`·`code` 등. 명세가 목록으로 정해 재생성 대상으로 삼는다.
- **well-formed** — XML 이 요구하는 최소 조건. 어기면 **치명적 오류**이고 파싱이 멈춘다.
- **`parsererror`** — Blink 가 XML 파싱 실패를 문서에 끼워 넣는 요소. ★ **구현이 정한 것**이다.
- **fragment parsing** — `innerHTML` 처럼 조각을 파싱할 때 **문맥 요소에 맞춰** 삽입 모드를 정해 놓고 돌리는 것.
