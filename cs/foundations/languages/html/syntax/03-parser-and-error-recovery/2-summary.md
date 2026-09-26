# html/syntax/03 — 파서와 오류 복구: 태그 수프가 트리가 되는 과정·암묵 태그 삽입 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [「Parsing HTML documents」](https://html.spec.whatwg.org/multipage/parsing.html) — 「Tree construction」·「The rules for parsing tokens in HTML content」·[「adoption agency algorithm」](https://html.spec.whatwg.org/multipage/parsing.html#adoption-agency-algorithm). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에 실제로 띄워 `--dump-dom` 으로 읽은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** Firefox 155.0.1 은 이 환경에서 headless 산출이 **조용히 실패**하고 WebKit 은 없다. 이 갈래는 **「이식성」을 주장하지 않는다** — 다만 **이 주제만은 명세가 알고리즘째 규정**하므로, 아래 트리 모양은 **관찰이면서 동시에 명세 보장**이다(구현 정의 칸이 가장 작은 주제다).
> **버전** — HTML 에는 언어 버전이 없다. 파싱 알고리즘은 **HTML5 표준화(2008\~2014)에서 처음 글로 적혔고** 그 뒤 크게 바뀌지 않았다.
> **선행** — [02번 주제](../02-elements-and-attributes/2-summary.md). 거기는 **명세가 허용한 표기**까지, 여기는 **명세를 어겼을 때 파서가 만드는 트리**부터다.
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
===== google-chrome --version =====
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 · 실행 시각 · 프로세스 id | 판이 오르면 바뀐다 |
| **흔들린다** | 스크린샷 픽셀의 안티에일리어싱 | GPU·글꼴 래스터라이저에 달렸다 |
| **흔들린다** | XML `parsererror` 상자의 **인라인 `style` 값과 문구** | 명세 밖이다 — **구현이 정한다** |
| **안 흔들린다** | **`--dump-dom` 트리 전체** | ★ **파싱 알고리즘이 명세에 있다** |
| **안 흔들린다** | 삽입된 요소의 **이름과 자리** · 요소 개수 | 〃 |
| **안 흔들린다** | 블록의 `(exit N)` (**전부 0**) | 파서는 실패하지 않는다 |
| **안 흔들린다** | XML 쪽이 **에러를 낸다는 사실**(문구가 아니라) | XML 명세가 well-formedness 를 요구한다 |

## 한눈에 — 쉽게 말하면

**★ HTML 파서는 「읽기」가 아니라 「받아쓰기 + 교정」이다. 무엇을 던져도 반드시 트리 하나를 내놓는다.**

구술을 받아 적는 속기사에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 말을 받아 적는 속기사 | **HTML 파서** |
| 「지금 어디를 적는 중인가」(제목인가 본문인가) | **삽입 모드(insertion mode)** |
| 문장이 안 끝났는데 다음 문장이 시작되면 앞을 끊어 줌 | **암묵으로 닫기** |
| 표 양식에 빠진 칸을 채워 넣음 | **암묵으로 삽입**(`tbody`) |
| 표 칸에 못 넣을 낙서를 **표 바깥 여백**에 옮겨 적음 | **foster parenting** |
| 굵게 읽던 대목이 끊기면 **다시 굵게 시작** | **서식 태그 재생성**(adoption agency) |
| **절대 「못 알아듣겠다」고 멈추지 않음** | **파스 오류가 파싱을 멈추지 않는다** |

- **「오류 복구」는 「대충 한다」가 아니다.** 명세가 **어떤 잘못된 입력이 어떤 트리가 되는지까지** 규정한다.
- 그래서 **같은 태그 수프를 던지면 모든 브라우저가 같은 트리**를 만든다 — 그것이 HTML5 표준화가 한 일이다.
- **에러를 내는 파서는 옆에 있다** — 같은 마크업을 `.xhtml` 로 주면 XML 파서가 **문서 대신 에러 상자**를 만든다.

```text
  <p>앞<div>안</div>뒤</p>              소스는 한 줄인데
        |
        v
  p                                     트리는 이렇게 된다
  #text "앞"                              (p 가 div 앞에서 닫혔다)
  div
    #text "안"
  #text "뒤"                            <- p 밖이다
  p                                     <- 짝 없는 </p> 가 만든 '빈 p'
  (비어 있음)
```

실무에서 이게 터지는 자리는 **문단 안에 블록을 넣을 때**다.\
`<p>` 안에 `<div>`·`<ul>`·`<table>` 을 넣는 템플릿은 **아무 에러 없이** 문단을 쪼갠다.\
CSS 가 `p` 에 준 스타일이 뒤쪽 글자에 안 먹고, 「**빈 상자가 하나 더**」 생긴다.

> **삽입 모드(insertion mode)** — 파서의 현재 상태. 같은 태그도 모드에 따라 다르게 처리된다.\
> 예: `<tr>` 은 「in table」 모드에서는 `tbody` 를 끼워 넣게 하고, 「in body」 모드에서는 그냥 무시된다.

> **파스 오류(parse error)** — 명세가 「무효」라고 이름 붙인 입력.\
> 예: `<p><div>`. ★ **트리를 바꾸지도 파싱을 멈추지도 않는다** — 이름표일 뿐이다.

> **foster parenting** — 표 안에 올 수 없는 내용을 **표 바로 앞으로 옮겨 붙이는** 파서 동작.\
> 예: `<table><div>x</div><tr>…` 의 `div` 가 `<table>` 앞으로 나간다.

## 이 주제가 답하려는 질문

원고가 없는 문법 주제라 「문제」 대신 이 네 질문을 둔다.

1. **잘못된 마크업은 어떤 트리가 되나.** 그리고 그것이 **왜 예측 가능한가.**
2. **파서가 손대는 방식은 몇 가지인가.** 닫기·삽입·이동·재생성 — 각각 언제 나오나.
3. **「오류 복구」의 뜻은 무엇인가.** 무엇이 「오류」이고, 복구란 정확히 무엇을 하는 것인가.
4. **에러를 내는 파서와 무엇이 다른가.** 같은 입력을 XML 로 주면?

★ 관찰 수단은 [01번 주제](../01-document-skeleton/2-summary.md)에서 세운 **창 ①**(`--dump-dom`)이 거의 전부다.\
**이 주제는 창 ① 하나가 본체**이고, 그래서 이 문서의 절마다 **트리 그림**이 먼저 온다.

## 동작 방식

파서가 손대는 방식은 **다섯 가지**다. 절 하나가 한 가지씩 맡는다.

```text
   ①  닫기          여기 올 수 없는 것이 오면 열린 것을 닫는다      (1)
   ②  삽입          빠진 요소를 끼워 넣는다                        (2)
   ③  이동          여기 둘 수 없는 것을 딴 데로 옮긴다            (3)
   ④  재생성        끊긴 서식을 다시 연다                          (4)
   ⑤  바꿔 읽기      닫는 태그를 여는 태그로 읽는다 / 텍스트로 본다  (5)(6)
```

### (1) 닫기 — `<p><div>` 가 문단을 쪼갠다

**언제 쓰나** — 문단 안에 블록을 넣는 모든 템플릿. **가장 자주 터지는 자리다.**

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

```text
   소스 한 줄                          트리
   <p>앞<div>안</div>뒤</p>
                                       body
   [1] <p>      -> p 를 연다              p
   [2] "앞"     -> p 안에 텍스트             #text "앞"
   [3] <div>    -> ★ p 를 닫는다          div
                   (p 는 div 를 품을 수      #text "안"
                    없다 — 콘텐츠 모델)    #text "뒤"       <- p 밖!
   [4] </div>   -> div 를 닫는다          p                <- ★ 빈 p
   [5] "뒤"     -> body 에 붙는다           (자식 없음)
   [6] </p>     -> 열린 p 가 없다
                   -> ★ 빈 <p> 를 만들어 닫는다
```

그림 해설 (한 단계씩):

- **`<div>` 시작 태그가 `<p>` 를 닫는다.** `p` 의 콘텐츠 모델이 구절(phrasing)만 받으므로, 블록이 오면 파서가 **먼저 닫는다**(콘텐츠 모델의 정본은 [목록의 **05번 주제**](../05-content-categories-and-models/)).
- **`뒤` 는 `p` 밖**이다. 소스만 읽으면 문단 안으로 보이는데 트리는 다르다.
- ★ **짝 없는 `</p>` 는 「빈 `<p>` 를 만들어 닫는」다.** 실측 트리 끝의 `<p></p>` 가 그것이다 — **내가 쓴 적 없는 요소**다.
- 그래서 `p:last-child` 같은 선택자가 **빈 문단을 잡고**, `p { margin }` 이 **한 벌 더** 생긴다.

화면으로 보면 이렇다.

```html demo
<p>앞<div>안</div>뒤</p>
<style>
  p   { border: 2px solid #2563eb; padding: 4px; margin: 4px 0; min-height: 1em; }
  div { border: 2px dashed #b91c1c; padding: 4px; }
</style>
```

> **보이는 것** — 파란 상자 안에 「앞」, 그 아래 빨간 점선 상자 안에 「안」, 그 아래 **테두리 없는 맨 글자로 「뒤」**, 그리고 맨 아래에 **글자가 없는 파란 빈 상자**가 하나 더 있다. 문단 하나를 썼는데 **문단 상자가 둘**이고, 「뒤」는 **어느 상자에도 안 들어가 있다.**\
> **바꿔 볼 것** — `<div>` → `<span>`(하나의 상자로 합쳐진다 — `span` 은 `p` 안에 올 수 있다) · `</p>` 를 지우기(빈 상자가 사라진다)

*(Chrome 151 headless 실측 — 래퍼를 붙인 사본에서 `p` 요소가 **2개**, 첫 `p` 의 `textContent` 가 `"앞"`·높이 `36`, 둘째 `p` 의 `textContent` 가 `""`·높이 `28`, `body` 의 직계 자식이 `p, div, p, style, script` 였다. 검증 블록은 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.)*

비용 — 없음(파서는 안 멈춘다). **그래서 비싸다.**

### (2) 삽입 — 표는 빠진 칸을 채워 넣는다

**언제 쓰나** — 표를 손으로 쓰거나 템플릿으로 만들 때.

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

```text
   소스                                     트리
   <table><tr><td>셀</td></tr></table>      table
                                              tbody      <- ★ 내가 안 쓴 것
                                                tr
                                                  td
                                                    #text "셀"

   <select><option>가</option></select>     select
                                              option     <- 여기는 삽입이 없다
```

그림 해설 (한 단계씩):

- **`<tbody>` 가 저절로 생긴다.** 「in table」 삽입 모드에서 `<tr>` 을 만나면 파서가 **`tbody` 를 먼저 열고** 그 안에 넣는다.
- ★ 이것은 [02번 주제](../02-elements-and-attributes/2-summary.md)의 **「생략 가능 태그」와 겉이 같고 속이 다르다** — 저쪽은 **끝** 태그를 안 써도 되는 것이고, 이쪽은 **시작 태그째 없는데 요소가 생기는 것**이다.
- 그래서 **`table > tr` 이라는 CSS 선택자가 아무것도 못 잡는다.** 트리에는 `table > tbody > tr` 만 있다. 이것이 이 규칙이 실무를 무는 첫 번째 자리다.
- `select > option` 은 **삽입이 없다** — 모든 부모가 자식을 끼워 넣는 게 아니라 **표 계열이 특별**하다.

비용 — 없음. **선택자와 `children[0]` 이 어긋나는 대가**가 있다.

### (3) 이동 — foster parenting: 표 밖으로 밀려난다

**언제 쓰나** — 표 안에 로딩 스피너·조건부 블록을 끼울 때. **가장 놀라운 자리다.**

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

```text
   소스                                          트리
   <table>                                       body
     <div>표 안에 쓴 div</div>   ------------->     div          <- ★ 표 '앞'으로
     <tr><td>셀</td></tr>                            #text "표 안에 쓴 div"
   </table>                                        table
                                                     tbody
                                                       tr
                                                         td
```

그림 해설 (한 단계씩):

- **`div` 가 `table` 앞으로 나갔다.** 표 안에는 표 요소만 올 수 있으므로 파서가 **바로 앞 형제 자리로 옮긴다**(foster parenting).
- ★ **「버려진 것」이 아니다.** 내용은 살아 있고 **자리만 바뀌었다** — 그래서 화면에는 보이는데 **DOM 구조가 내 코드와 다르다.**
- 프레임워크가 표를 만들다 이것을 맞으면 **행이 아니라 표 위에** 무언가가 뜬다. 증상이 「스피너가 표 위에 있다」라 원인을 마크업에서 찾기 어렵다.
- ★ **공백은 예외다** — [02번 주제](../02-elements-and-attributes/2-summary.md)의 `html01b-omit.html` 트리를 보면 `<table>` 과 `<tbody>` 사이에 **공백 텍스트 노드가 그대로 남아 있다.** 공백은 밀려나지 않는다(그쪽은 [04번 주제](../04-whitespace-and-character-references/2-summary.md)).

비용 — 없음. **구조가 조용히 바뀌는 대가**가 크다.

### (4) 재생성 — 잘못 겹친 서식 태그는 다시 열린다

**언제 쓰나** — 리치 텍스트 에디터·마크다운 변환기가 만든 HTML 을 읽을 때.

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

```text
   소스                                    트리
   <p><b>굵게<i>둘 다</b>기울임만</i>맨몸</p>

   [1] <b>      b 를 연다                  p
   [2] "굵게"                                b
   [3] <i>      i 를 연다 (b 안)               #text "굵게"
   [4] "둘 다"                                 i
   [5] </b>     ★ b 를 닫아야 하는데              #text "둘 다"
                i 가 아직 열려 있다          i              <- ★ 재생성된 i
   [6] 그래서 i 를 b 안에서 닫고,              #text "기울임만"
       b 밖에 i 를 '다시 연다'              #text "맨몸"
   [7] "기울임만"  -> 새 i 안
   [8] </i>     새 i 를 닫는다
   [9] "맨몸"   -> p 안, 서식 없음
```

그림 해설 (한 단계씩):

- **`<i>` 가 두 개가 된다.** 하나는 `b` 안, 하나는 `b` 밖 — **내가 쓴 `<i>` 는 하나**다.
- 이 동작에 명세가 붙인 이름이 **adoption agency algorithm**(입양 기관 알고리즘)이다. 「끊긴 서식 요소를 다시 만들어 준다」는 뜻이다.
- **화면 결과는 내 의도와 거의 같다** — 「굵게」는 굵고, 「둘 다」는 굵고 기울고, 「기울임만」은 기울었다. **그래서 안 들킨다.**
- ★ **그러나 요소 개수가 다르다.** `querySelectorAll("i").length` 가 **2**다. JS 로 서식 요소를 세거나 순회하는 코드가 여기서 어긋난다.
- 두 번째 줄(`<em>`/`<strong>`)도 **같은 모양**이다 — 서식 요소 목록에 든 태그는 전부 이 대우를 받는다.

비용 — 없음. **구조가 부풀어 오르는 대가**가 있다.

### (5) 바꿔 읽기 — `</br>` 는 `<br>` 이 된다

**언제 쓰나** — 옛 코드·잘못된 템플릿을 읽을 때.

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

```text
   소스              트리                    왜
   앞</br>뒤         앞<br>뒤                ★ 명세가 </br> 을 <br> 로 처리하라고 못 박았다
   앞</img>뒤        앞뒤                    무시된다 (빈 요소의 닫는 태그는 의미가 없다)
   앞</hr>뒤         앞뒤                    무시된다
```

그림 해설 (한 단계씩):

- **`</br>` 만 특별하다.** 명세가 「in body」 규칙에 **`</br>` 을 만나면 `<br>` 시작 태그로 취급하라**고 적어 뒀다.
- **웹에 이미 `</br>` 로 줄바꿈하는 문서가 많았기 때문**이다. 오류 복구가 **웹 호환성을 위해 화석을 명세에 박아 넣은** 대표 사례다.
- `</img>`·`</hr>` 은 **그냥 사라진다.** 같은 빈 요소인데 대우가 다르다 — **규칙이 태그마다 다르다**는 증거다.
- ★ 그래서 **「빈 요소의 닫는 태그는 무시된다」는 일반화가 틀렸다.** `</p>` 도 빈 `<p>` 를 만들고(1), `</br>` 은 `<br>` 이 된다.

비용 — 없음.

### (6) 파서는 절대 에러를 내지 않는다 — 기호 범벅을 던져 보면

**언제 쓰나** — 「이런 걸 넣으면 터지지 않나」를 물을 때.

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
   소스                       트리에 남은 것
   <<<>>>                     #text "<<<>>>"          <- 전부 텍스트
   <p>                        p
   <<<b>>>x</p>               #text "<<"  b  #text ">>x"
                                           ^ 이 b 는 진짜 요소로 읽혔다
   <3 > 2                     b (재생성)  #text "<3 > 2"
```

그림 해설 (한 단계씩):

- **`<` 뒤에 글자가 안 오면 태그가 아니다.** `<<<>>>` 가 통째로 텍스트가 됐다.
- **`<<<b>` 안의 `b` 는 진짜 요소**가 됐다 — 앞의 `<<` 는 텍스트, `<b` 부터가 태그다.
- **`<3 > 2` 도 텍스트**다. `<` 뒤가 숫자라 태그 이름이 못 된다.
- ★ **종료 코드는 `0`, stderr 에 마크업 관련 줄은 0개**다. 아래 (7)이 그 실측이다.

```text
===== for f in html01b-p-div.html html01b-garbage.html html01b-xml-bad.xhtml; do echo "$f  마크업 관련 stderr 줄 수 = $(google-chrome --headless --disable-gpu --no-sandbox --enable-logging=stderr --dump-dom $f 2>&1 >/dev/null | grep -cE 'mismatch|parse error|unexpected|Opening and ending|tag')"; done =====
html01b-p-div.html  마크업 관련 stderr 줄 수 = 0
html01b-garbage.html  마크업 관련 stderr 줄 수 = 0
html01b-xml-bad.xhtml  마크업 관련 stderr 줄 수 = 0
(exit 0)
```

- ★ **이것이 「오류 복구」의 뜻**이다 — **오류를 알려 주지 않고 트리를 만든다.**
- CSS 는 **조용히 버리고**(CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **07번**), HTML 은 **조용히 고친다.** 둘 다 아무 말이 없다.

### (7) 끝까지 안 닫은 문서 — EOF 가 전부 닫는다

```text
===== 소스: html01b-eof.html =====
<!DOCTYPE html>
<meta charset="utf-8">
<title>끝까지 안 닫은 문서</title>
<div><section><ul><li>하나
===== dom html01b-eof.html =====
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>끝까지 안 닫은 문서</title>
</head><body><div><section><ul><li>하나
</li></ul></section></div></body></html>
(exit 0)
```

```text
   소스                          트리
   <div><section><ul><li>하나    div
   (여기서 파일 끝)                section
                                     ul
                                       li
                                         #text "하나\n"
                                       </li> </ul> </section> </div>  <- EOF 가 닫았다
```

- **중첩이 아무리 깊어도 EOF 가 전부 닫는다.** 「닫는 태그를 빠뜨려서 트리가 안 만들어진다」는 일은 **없다.**
- ★ 다만 **어디까지 열려 있었느냐가 결과를 바꾼다** — 파일 끝 직전에 쓴 내용이 전부 그 안으로 들어간다.

### (8) 에러를 내는 파서는 옆에 있다 — 같은 마크업을 XML 로

**언제 쓰나** — 「왜 HTML 은 이렇게 관대한가」를 물을 때. **이 절이 대비의 본체다.**

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

```text
   같은 마크업 <p>앞<b>굵게</p></b>

   .html 로 주면 (HTML 파서)          .xhtml 로 주면 (XML 파서)
   +----------------------------+     +--------------------------------+
   | p                          |     | parsererror       <- 에러가     |
   |   #text "앞"               |     |   h3 "This page contains …"    |
   |   b                        |     |   div "error on line 3 at      |
   |     #text "굵게"           |     |        column 20: Opening and  |
   +----------------------------+     |        ending tag mismatch…"  |
     b 를 p 안에서 닫아 주고 끝        +--------------------------------+
     아무 말도 안 한다                  본문은 '첫 에러까지만' 남는다
```

그림 해설 (한 단계씩):

- **XML 파서는 멈춘다.** 트리에 `parsererror` 요소를 **문서 첫머리에 끼워 넣고**, 본문은 **에러 직전까지만** 남긴다(`<b></b>` 가 비어 있다).
- **HTML 파서는 고친다.** `<b>굵게</b>` 로 닫아 주고 끝이다.
- ★ **둘 다 stderr 에는 아무것도 안 찍는다**(위 (6) 블록의 세 번째 줄). XML 쪽의 「에러」도 **콘솔이 아니라 트리에 있다.**
- ★ **`parsererror` 의 문구와 인라인 `style` 은 명세 밖**이다 — 「흔들리는 칸」 표에 그렇게 선언해 뒀다. **근거로 쓸 것은 「에러 요소가 끼워졌다」는 사실**이지 그 문구가 아니다.
- 이것이 **XHTML 이 좌초한 이유**의 실물이다 — 문서 하나의 오타가 **페이지 전체를 못 보게** 만든다. 역사는 [`../../../../../../history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md)가 정본이다.

비용 — XML 쪽은 **전부 아니면 전무**, HTML 쪽은 **언제나 무언가**. 웹이 뒤쪽을 골랐다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 파서가 손대는 다섯 가지

```text
닫기        <p><div>          여기 못 오는 것이 오면 열린 것을 닫는다
삽입        <table><tr>       빠진 요소를 끼워 넣는다 (tbody)
이동        <table><div>      못 두는 것을 표 앞으로 옮긴다 (foster parenting)
재생성      <b><i></b>        끊긴 서식 요소를 다시 연다 (adoption agency)
바꿔 읽기   </br>             닫는 태그를 여는 태그로 읽는다
```

### 금지 사례 — 파서가 조용히 고치는 것들

```text
<p><div>…</div></p>            문단이 둘로 쪼개지고 빈 p 가 하나 더 생긴다
<table><tr>…                   tbody 가 끼워진다 — table > tr 선택자가 안 잡는다
<table><div>…</div><tr>        div 가 표 '앞'으로 밀려난다
<b>1<i>2</b>3</i>              i 가 둘이 된다
</br>                          <br> 이 된다 (</img>·</hr> 는 사라진다)
```

### 어디서 헷갈리나

- **「파스 오류」는 「파싱 실패」가 아니다.** 실측에서 전부 `(exit 0)` 이고 stderr 도 0줄이었다.
- **「생략 가능 태그」와 「암묵 삽입」은 다르다.** 앞은 **유효**([02번 주제](../02-elements-and-attributes/2-summary.md)), 뒤는 **파서가 채운 것**.
- **「밀려났다」와 「버려졌다」는 다르다.** foster parenting 은 **내용을 살린다.**
- **「화면이 맞으니 트리도 맞겠지」가 틀린다.** adoption agency 는 **화면은 맞고 구조만 다르다.**
- **빈 요소의 닫는 태그 규칙은 태그마다 다르다** — `</br>` 만 특별하다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 여섯 다 **에러 없이 조용히 어긋난다.**

### 1. `<p>` 안에 블록을 넣는다

실측에서 `<p>앞<div>안</div>뒤</p>` 가 **`p` 두 개 + `div` 하나 + `p` 밖의 텍스트**가 됐다.\
`p { color }` 를 주면 **「뒤」에만 안 먹는다.** 증상이 「일부 글자만 스타일이 다르다」라 원인을 CSS 에서 찾게 된다.

### 2. `table > tr` 선택자를 쓴다

실측 트리에 **`tbody` 가 끼어** 있어 `table > tr` 이 **아무것도 못 잡는다.**\
`table tr`(자손)이나 `table > tbody > tr` 로 써야 한다. **소스에는 `tbody` 가 없으므로 소스를 읽어서는 절대 안 보인다.**

### 3. 표 안에 조건부 블록을 끼운다

실측에서 `<table>` 안의 `div` 가 **표 앞으로 밀려났다.**\
「스피너가 표 위에 뜬다」·「`table.firstElementChild` 가 예상과 다르다」의 원인이 이것이다.

### 4. 서식 요소를 세거나 순회한다

실측에서 `<i>` 를 **하나 썼는데 트리에 둘**이 됐다.\
**화면은 멀쩡하다** — 그래서 눈으로는 절대 안 잡힌다. `querySelectorAll` 로 세야 보인다.

### 5. 「이 마크업은 터질 것」이라 기대한다

실측에서 `<<<>>><p><<<b>>>x</p><3 > 2` 가 **트리를 만들었고 `(exit 0)`, stderr 마크업 줄 0개**였다.\
**HTML 에는 「파싱 실패」가 없다.** 터지길 기대하는 코드는 영영 안 터진다.

### 6. 「명세에 없으니 브라우저 마음대로겠지」로 읽는다

★ **정반대다.** 이 주제의 트리 모양은 **거의 전부 명세 보장**이다 — 파싱 알고리즘이 명세 본문에 있다.\
그래서 이 주제의 「구현 정의」 칸은 **`parsererror` 의 문구와 `--dump-dom` 의 줄바꿈 자리 정도**로 아주 작다.

## 구현 세부사항 대 언어 보장

★★ **HTML 은 「명세가 오류 복구까지 정한」 드문 언어다.** 이 주제가 그 사실의 본체다.\
아래 표에서 **명세 칸이 압도적으로 크고 구현 칸이 거의 비어 있다** — 다른 언어의 같은 표와 정반대 모양이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `<div>` 가 `<p>` 를 닫는 것 | **명세**(「in body」 — `<p>` 를 닫는 태그 목록이 적혀 있다) |
| 짝 없는 `</p>` 가 **빈 `p` 를 만드는 것** | **명세**(「in body」의 `</p>` 규칙) |
| `<tr>` 앞에 **`tbody` 가 삽입되는 것** | **명세**(「in table」) |
| 표 안의 비표 요소가 **표 앞으로 옮겨지는 것** | **명세**(foster parenting 절) |
| 잘못 겹친 서식 태그가 **재생성되는 것** | **명세**(adoption agency algorithm — 단계까지 번호로 적혀 있다) |
| **`</br>` 이 `<br>` 이 되는 것** | **명세**(「in body」에 명문으로 있다) |
| `</img>`·`</hr>` 이 무시되는 것 | **명세**(「any other end tag」 규칙) |
| EOF 가 열린 요소를 전부 닫는 것 | **명세** |
| **파스 오류가 파싱을 멈추지 않는 것** | **명세**(파서는 반드시 문서를 내놓는다) |
| XML 파서가 well-formedness 위반에 **멈추는 것** | **명세**(XML 1.0 — fatal error) |
| **`parsererror` 요소의 이름·문구·인라인 `style`** | ★ **구현**(Blink). XML 명세는 「에러 처리를 계속하지 말라」까지만 말한다 |
| **stderr 에 아무것도 안 찍히는 것** | **관찰**(Chrome 151). 명세는 로그를 규정하지 않는다 |
| `--dump-dom` 의 줄바꿈 자리 | **명세**(직렬화) + **도구**(Chrome 플래그) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 문단 안에 무언가를 넣는다 | `span`·`a`·`strong` 같은 구절 요소 | `div`·`ul`·`table` |
| 표를 선택자로 잡는다 | `table tr` · `table > tbody > tr` | `table > tr` |
| 표 안에 조건부 UI 를 넣는다 | `<td>` 안에 넣거나 표 밖에 | `<table>` 바로 안 |
| 서식 요소를 세는 코드를 쓴다 | 트리를 창 ① 로 먼저 확인 | 소스를 세기 |
| 「틀린 마크업」을 잡고 싶다 | 린터·빌드 검사·창 ① | 브라우저(아무 말도 안 한다) |
| 엄격한 파싱이 필요하다 | XML 도구 체인(`.xhtml`) | HTML 파서에 기대하기 |

판단 규칙 두 줄.

- **「이 요소 안에 이것을 넣어도 되나」가 의심되면 던져 본다.** 콘텐츠 모델을 외우는 것보다 창 ① 이 빠르다.
- **트리가 내 코드와 다를 수 있다는 것을 기본값으로 둔다.** 화면이 맞아도 구조는 다를 수 있다((4)가 그렇다).

## 핵심 문장

- **HTML 파서는 절대 에러로 멈추지 않는다** — 실측에서 기호 범벅도 `(exit 0)`, stderr 마크업 줄 **0개**였다.
- 「**오류 복구**」는 「**대충**」이 아니라 「**명세가 정한 대로**」다. 그래서 **같은 수프는 어디서나 같은 트리**가 된다.
- **`<p><div>x</div></p>` 는 `p` 를 닫고, 텍스트를 밖으로 내보내고, 마지막에 「빈 `p`」를 하나 만든다.**
- **`<table><tr>` 은 `tbody` 를 끼워 넣는다** — `table > tr` 선택자가 안 잡히는 이유다.
- **표 안의 비표 요소는 표 「앞」으로 밀려난다**(foster parenting) — 버려지는 게 아니라 **자리만 바뀐다.**
- **잘못 겹친 `<b><i></b>` 는 `<i>` 를 하나 더 만든다** — **화면은 맞고 구조만 다르다.**
- **`</br>` 은 `<br>` 이 된다.** 웹 호환성을 위해 **화석을 명세에 박아 넣은** 자리다.
- **같은 마크업을 `.xhtml` 로 주면 XML 파서가 `parsererror` 를 트리에 끼워 넣고 본문을 잘라 버린다** — 오류 복구의 반대편이다.

## 관련 자료

- [`../README.md`](../README.md) — HTML 문법·API 주제 목록(이 주제는 03번)
- [01번 주제](../01-document-skeleton/2-summary.md) — **창 넷의 정본.** `html`·`head`·`body` 삽입은 거기, 여기는 **그 밖의 모든 교정**
- [02번 주제](../02-elements-and-attributes/2-summary.md) — **명세가 허용한 표기의 정본.**\
  「끝 태그를 안 써도 되는 것」은 거기(**유효**), 「안 썼는데 파서가 고친 것」은 여기(**무효**)
- [04번 주제](../04-whitespace-and-character-references/2-summary.md) — 표 안의 **공백**은 왜 밀려나지 않는지
- [목록의 **05번 주제**](../05-content-categories-and-models/)(콘텐츠 카테고리와 콘텐츠 모델) — **「무엇이 무엇 안에 올 수 있나」의 정본.**\
  여기는 「**어긴 결과**」까지, 거기는 「**규칙 자체**」
- [목록의 **17번 주제**](../17-table-structure/)(표 구조) — `tbody` 삽입이 표 설계에 미치는 영향의 정본
- [`../../../../compiler-pipeline/`](../../../../compiler-pipeline/) — **렉서·파서·AST 일반론의 정본.**\
  「파싱이 무엇인가」는 거기, 여기는 「**에러로 멈추지 않는 파서**」라는 HTML 고유 설계와 삽입 모드
- [`../../../../../../history/web/03-HTML-CSS-진화.md`](../../../../../../history/web/03-HTML-CSS-진화.md) — **XHTML 의 엄격함이 좌초한 이유의 정본.**\
  여기는 그 선택의 **오늘의 결과**만 — (8)의 `parsererror` 가 그 실물이다
- CSS 갈래 목록([`css/syntax/README.md`](../../../css/syntax/README.md))의 **07번** — **버리는 언어의 정본.**\
  CSS 는 조용히 **버리고** HTML 은 조용히 **고친다** — 둘 다 에러를 안 던지는데 방향이 반대다

## 용어 풀이

- **태그 수프(tag soup)** — 문법을 안 지킨 HTML. 브라우저가 어떻게든 읽어 내던 시절의 이름이다.
- **삽입 모드(insertion mode)** — 파서의 현재 상태. 「initial」·「in head」·「in body」·「in table」 등.
- **트리 구축(tree construction)** — 토큰을 받아 DOM 트리를 쌓는 파서의 뒷단. 오류 복구가 여기서 일어난다.
- **파스 오류(parse error)** — 명세가 무효라고 이름 붙인 입력. **트리를 바꾸지도 파싱을 멈추지도 않는다.**
- **암묵 삽입(implied element)** — 소스에 없는 요소를 파서가 끼워 넣는 것. `html`·`head`·`body`·`tbody`.
- **foster parenting** — 표 안에 못 오는 내용을 **표 바로 앞**으로 옮기는 동작. **버리지 않는다.**
- **adoption agency algorithm** — 잘못 겹친 서식 요소를 **다시 열어** 트리를 바로잡는 알고리즘.
- **서식 요소(formatting element)** — `a`·`b`·`i`·`em`·`strong`·`code` 등. 명세가 목록으로 정해 두고 재생성 대상으로 삼는다.
- **well-formed** — XML 이 요구하는 최소 조건(태그 짝이 맞고 하나의 루트가 있을 것). 어기면 **치명적 오류**다.
- **`parsererror`** — Blink 가 XML 파싱 실패를 문서에 끼워 넣는 요소. ★ **명세가 아니라 구현이 정한 것**이다.

## 더 들어가면

- **오류 복구가 명세에 들어간 것 자체가 사건**이었다. HTML 4 까지 명세는 「유효한 문서」만 규정했고, **무효한 문서의 처리는 브라우저마다 달랐다.** 그래서 「IE 에서만 되는 페이지」가 생겼다. HTML5 는 **무효한 입력의 처리까지 규정**해 그 분기를 없앴다 — 이 주제의 트리가 **명세 보장**인 이유다.
- **adoption agency 는 명세에서 가장 악명 높은 알고리즘**이다. 번호 붙은 단계가 스무 개 가까이 되고, 그 자체로 한 절을 차지한다. 이름은 「부모를 잃은 노드에게 새 부모를 찾아 준다」는 농담에서 왔다.
- **`</br>` 같은 화석이 명세에 몇 개 더 있다.** `<isindex>`(지금은 제거됨)·`<nobr>`·문서 끝의 `</body>` 뒤 텍스트 처리 등. 전부 **「웹에 이미 있는 문서를 깨지 않으려고」** 들어간 것이다.
- **서버 쪽 파서와 브라우저 파서가 다르면 보안 문제가 된다.** 정제기가 「이 마크업은 안전」이라 판단한 트리와 브라우저가 만드는 트리가 다르면 필터를 우회할 수 있다 — [02번 주제](../02-elements-and-attributes/2-summary.md)의 중복 속성과 **같은 집안**이다. ★ 이 판에서는 정제기를 돌려 보지 않았다.
- **DOM 조작 API 는 web-api 갈래가 정본**이다. `innerHTML` 에 넣은 조각도 **같은 파싱 알고리즘**(fragment parsing)을 거치지만, 그 API 표면은 이 갈래 밖이다.
