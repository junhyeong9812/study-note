# web-api/04 — `textContent` 대 `innerHTML` 대 `innerText`: 파싱·비용·XSS — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 언어 문법은 [`../../languages/`](../../languages/) 에 있고, 여기는 **브라우저가 건네주는 객체와 그 계약**이다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「`textContent`」 절 · [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 「`innerHTML`」(DOM Parsing)·「`innerText`」·「fragment parsing algorithm」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 하네스는 [3-answer.md](3-answer.md) 의 `## 실행 검증` 절에 있다.\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **「이식성」을 주장하지 않는다.** 특히 **`innerText` 는 원래 IE 의 확장**이었다가 뒤늦게 표준화된 것이라 엔진 차이가 남아 있을 수 있는 자리인데, 여기서는 **한 엔진의 관찰**만 싣는다.\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `Trusted Types` 는 Baseline **newly**(2026-02-24), Sanitizer API 는 **limited** 다([`../README.md`](../README.md)) — 그래서 이 문서는 둘을 **대안으로 확정해 적지 않는다.**\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 명세로, 출력은 실행으로 접지했다.

**★ 이 주제에는 흔들리는 칸이 있다.** 네 주제 중 여기만 그렇다 — 시간을 재기 때문이다.

| 안 흔들리는 칸 (근거로 쓴다) | 흔들리는 칸 (근거로 쓰지 않는다) |
|---|---|
| 읽은 문자열 · 파싱 결과 트리 · 자식 수 · **실행 횟수**(`script=0`·`img=1`·`svg=1`) · 문자열 길이 | `performance.now()` 의 **개별 수치**(중앙값·최소·최대 전부) |
| **자릿수와 순위** — 「어느 쪽이 몇 자릿수 크냐」는 세 판 모두 같았다 | 같은 자릿수 안의 대소(예: `appendChild` 대 `DocumentFragment`) |

- **수치를 인용할 때는 「몇 판을 어떻게 쟀나」를 같이 적는다** — 한 파일 안에서 **9판**을 돌려 **중앙값**을 쓰고 최소·최대를 함께 실었다.
- **재대조에서 수치 칸은 정규화**한다(`normalize-shaky.py --rule '(중앙값|최소|최대) +[0-9]+\.[0-9]+=\1 <수치>'`). **위 표에 없는 것은 정규화하지 않는다.**
- ★ **`performance.now()` 는 Chrome 에서 100마이크로초 단위로 뭉개진다** — 그래서 아래 표에 `0.00`·`0.10` 만 나오는 칸이 있다. 「0 이다」가 아니라 「**이 도구의 분해능 아래다**」로 읽는다.

## 한눈에 — 쉽게 말하면

**★ 같은 요소를 세 창구로 읽을 수 있다. 셋은 다른 것을 주고, 다른 값을 치르고, 다른 위험을 진다.**

민원 창구에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **글자만 옮겨 적어 주는 창구** | `textContent` — 트리의 모든 글자. 안 보이는 것도 준다 |
| **서류를 원본 그대로 복사해 주는 창구** | `innerHTML` — 마크업 문자열. **쓸 때는 파서를 부른다** |
| **「지금 화면에 뭐라고 적혀 있나」를 읽어 주는 창구** | `innerText` — 렌더 결과. 안 보이는 것은 빼고 준다 |
| 복사 창구에 **남의 서류를 그냥 넣는 것** | `innerHTML` 에 신뢰할 수 없는 문자열 — **XSS** |
| 「지금 화면」을 물으려면 **화면을 먼저 그려야 한다** | `innerText` 읽기가 **레이아웃을 강제**한다 |

- **셋의 차이는 「무엇을 주나」에서 끝나지 않는다.** 비용과 위험까지 셋이 다르다.
- **`innerText` 만 화면에 의존한다.** 그래서 같은 트리인데 **CSS 를 바꾸면 답이 바뀐다.**
- **`innerHTML` 쓰기는 문자열을 트리로 바꾸는 파서 호출**이다. 그 파서가 마크업을 **고쳐서** 넣는다.

```text
   <div id="box">
     <p>보이는 문단</p>
     <p style="display:none">숨은 문단</p>
     <style>.z { color: red }</style>

   textContent  ->  "보이는 문단" + "숨은 문단" + ".z { color: red }"   전부 준다
   innerText    ->  "보이는 문단"                                       보이는 것만
   innerHTML    ->  "<p>보이는 문단</p><p style=…>숨은 문단</p><style>…" 마크업째
```

실무에서 이게 터지는 자리는 「**사용자가 쓴 글을 화면에 보여 주기**」다.\
`el.innerHTML = 댓글` 한 줄이면 **댓글에 들어 있던 마크업이 실행된다.**\
그리고 **「`<script>` 만 걸러내면 되겠지」가 틀렸다** — 아래에서 `<script>` 는 **안 돌고** `<img onerror>` 는 **도는 것**을 같이 던져서 본다.

> **XSS(교차 사이트 스크립팅)** — 남이 준 문자열이 **내 페이지의 코드로 실행**되는 것.\
> 예: 댓글에 `<img src=x onerror="...">` 를 적어 두면 그 페이지를 여는 모든 사람의 브라우저에서 그 코드가 돈다.

> **레이아웃(layout)** — 요소가 화면 어디에 얼마만큼 놓이는지를 계산하는 단계.\
> 예: `innerText` 를 읽으려면 「무엇이 보이나」를 알아야 하므로 이 계산을 **먼저 끝내야** 한다.

## 이 주제가 답하려는 질문

1. **셋이 각각 무엇을 읽고 무엇을 쓰나.** 그리고 **어디서 답이 갈리나.**
2. **`innerHTML` 에 문자열을 넣으면 정확히 무슨 일이 일어나나.** 파서가 무엇을 고치고 무엇을 실행하나.
3. **셋의 비용은 얼마나 다른가.** 그리고 그 차이를 **재지 않고 말해도 되나.**

## 이 갈래의 관측 창 — 네 번째 창은 「실행 흔적」이다

[01번 주제](../01-document-and-node-tree/2-summary.md)의 창 셋에 이 주제만의 창을 하나 더 세운다.

```text
  창 1  --dump-dom            결과 트리를 글자로
  창 2  길이 · 자식 수         무엇이 몇 개인가
  창 3  두 번 읽기             라이브냐 정적이냐 (02번)
  ★ 창 4 (이 주제 고유)  전역 카운터로 '실행 흔적' 을 남긴다
        무엇을 답하나:  '트리에 들어갔나' 가 아니라 '실제로 돌았나'
        왜 필요한가:    <script> 는 트리에 '있는데 안 돈다'.
                        트리만 보면 둘이 구분이 안 된다

  ★ 창 5 (비용)  performance.now() 로 9판을 재고 중앙값을 쓴다
        무엇을 답하나:  '느리다' 가 아니라 '몇 자릿수 느리다'
```

- **창 4 가 이 주제의 핵심**이다. 「`<script>` 가 들어갔나」와 「`<script>` 가 돌았나」는 **다른 질문**이고, 답이 **서로 반대**다.
- **창 5 를 안 쓰면 비용 이야기를 쓸 수 없다.** 이 저장소의 규칙이 그렇다 — **재지 않은 성능 주장은 금지**다.

## 동작 방식

### (0) 셋을 나란히 읽는다

**언제 쓰나** — 무엇을 골라야 할지 정할 때. **이 출력 하나가 이 주제의 절반이다.**

```html
<!-- ex04a.html -->
<!doctype html>
<meta charset="utf-8">
<title>04a</title>
<div id="box">
  <p>보이는 문단</p>
  <p style="display: none">숨은 문단</p>
  <span hidden>hidden 속성</span>
  <style>.z { color: red }</style>
  <script type="application/json">{"설정": 1}</script>
  <p>줄<br>바꿈<span style="text-transform: uppercase">abc</span></p>
</div>
<script>
const O = [];
const box = document.getElementById('box');
O.push('textContent = ' + JSON.stringify(box.textContent));
O.push('');
O.push('innerText   = ' + JSON.stringify(box.innerText));
O.push('');
O.push('innerHTML   = ' + JSON.stringify(box.innerHTML));
O.push('');
const p2 = box.querySelectorAll('p')[1];
O.push('display:none 인 p 의 textContent = ' + JSON.stringify(p2.textContent));
O.push('display:none 인 p 의 innerText   = ' + JSON.stringify(p2.innerText));
O.push('display:none 인 p 의 innerHTML   = ' + JSON.stringify(p2.innerHTML));
O.push('');
O.push('innerText 를 문서에서 떼어낸 복제본에서 읽으면 = ' + JSON.stringify(box.cloneNode(true).innerText));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,5p'
textContent = "\n  보이는 문단\n  숨은 문단\n  hidden 속성\n  .z { color: red }\n  {\"설정\": 1}\n  줄바꿈abc\n"

innerText   = "보이는 문단\n\n줄\n바꿈ABC"

innerHTML   = "\n  <p>보이는 문단</p>\n  <p style=\"display: none\">숨은 문단</p>\n  <span hidden=\"\">hidden 속성</span>\n  <style>.z { color: red }</style>\n  <script type=\"application/json\">{\"설정\": 1}</script>\n  <p>줄<br>바꿈<span style=\"text-transform: uppercase\">abc</span></p>\n"
(exit 0)
```

```text
   같은 <div id="box"> 를 셋으로 읽었다

   textContent   보이는 문단 · 숨은 문단 · hidden 속성 · <style> 내용 · <script> 내용
                 + 소스의 줄바꿈·들여쓰기까지 전부
                 ★ 안 보이는 것도 전부 준다.  트리에 글자가 있으면 준다

   innerText     보이는 문단 · 줄\n바꿈 · ABC
                 ★ display:none · hidden · <style> · <script> 가 전부 빠졌다
                 ★ <br> 이 "\n" 이 되고, text-transform: uppercase 가 적용돼 ABC 다

   innerHTML     마크업 그대로.  hidden 이 hidden="" 로 직렬화돼 있다
```

그림 해설 (한 단계씩):

- **`textContent` 는 트리를 훑는다.** 화면을 안 보므로 `<style>`·`<script>` 안의 글자도 그대로 준다 — 이것이 **「안전하지만 놀라운」** 성질이다.
- **`innerText` 는 화면을 본다.** 그래서 `display: none`·`hidden` 이 빠지고, `<br>` 이 줄바꿈이 되고, **`text-transform` 까지 적용된 글자**를 준다(`abc` 가 `ABC` 로 나왔다).
- **`innerHTML` 은 트리를 다시 직렬화한다.** 내가 쓴 소스가 아니라 **트리에서 되뽑은 마크업**이다 — 그래서 `hidden` 이 `hidden=""` 로 정규화돼 있다.

비용 — 아래 (5)에서 잰다. **여기서는 주장하지 않는다.**

### (1) ★ `innerText` 는 렌더에 의존한다 — 그런데 안 보이면 물러선다

**언제 쓰나** — 「화면에 보이는 글자」가 필요할 때. **그리고 그 답이 이상할 때.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04a.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,11p'
display:none 인 p 의 textContent = "숨은 문단"
display:none 인 p 의 innerText   = "숨은 문단"
display:none 인 p 의 innerHTML   = "숨은 문단"

innerText 를 문서에서 떼어낸 복제본에서 읽으면 = "\n  보이는 문단\n  숨은 문단\n  hidden 속성\n  .z { color: red }\n  {\"설정\": 1}\n  줄바꿈abc\n"
(exit 0)
```

```text
   같은 <p style="display:none"> 를 두 자리에서 물었다

   (가) 부모 <div> 에 대고 innerText 를 읽으면
        -> 그 <p> 의 글자가 '빠진다'.   안 보이니까

   (나) 그 <p> 자신에 대고 innerText 를 읽으면
        -> "숨은 문단" 이 '나온다'       ★ textContent 와 같은 답

   왜 — 명세가 그렇게 정했다.  '이 요소가 렌더되고 있지 않으면
        innerText 는 textContent 와 같은 값을 준다'

   (다) 문서에서 떼어낸 복제본에서 읽으면
        -> 들여쓰기 공백까지 전부.  즉 textContent 그대로
```

그림 해설 (한 단계씩):

- `innerText` 는 「안 보이는 것을 뺀다」가 아니라 「**보이는 것을 읽는다**」다. 읽을 화면 자체가 없으면 **읽을 수가 없어서** `textContent` 로 물러선다.
- 그래서 **같은 노드가 어디서 읽히느냐에 따라 답이 다르다.** 부모를 통해 읽으면 빠지고, 자기 자신으로 읽으면 나온다.
- **문서 밖 노드에서는 언제나 `textContent` 와 같다** — `cloneNode(true)` 로 만든 사본에서 읽으면 들여쓰기 공백까지 전부 나온다. `innerText` 로 텍스트를 뽑아 비교하는 코드가 **트리 밖에서 조용히 다른 답**을 내는 자리다.
- **이것이 `innerText` 가 비싼 이유**이기도 하다 — 「보이나」를 알려면 **레이아웃이 최신이어야** 한다.

비용 — (5)에서 잰다.

### (2) ★ `innerHTML` 쓰기는 파서를 부른다 — 파서가 마크업을 고친다

**언제 쓰나** — 문자열로 트리를 만들 때. **그리고 「내가 넣은 것과 다른 게 들어갔다」를 만날 때.**

```html
<!-- ex04b.html -->
<!doctype html>
<meta charset="utf-8">
<title>04b</title>
<div id="host"></div>
<table id="tbl"></table>
<script>
const O = [];
const host = document.getElementById('host');
const put = (label, target, html) => {
  target.innerHTML = html;
  O.push('넣은 것   ' + html);
  O.push('읽은 것   ' + target.innerHTML);
  O.push('자식 수   ' + target.children.length + '   ' + label);
  O.push('');
};
put('p 는 div 를 품지 못한다', host, '<p>가<div>나</div>');
put('겹친 태그를 파서가 다시 연다', host, '<b><i>가</b>나</i>');
put('div 안에서는 td 가 버려진다', host, '<td>셀</td>');
put('table 안에서는 tbody 가 끼워진다', document.getElementById('tbl'), '<tr><td>셀');
put('닫지 않아도 닫아 준다', host, '<ul><li>하나<li>둘');
put('문자 참조는 풀린다', host, '&amp;lt; &lt; &#65;');
const before = host.innerHTML;
host.innerHTML = before;
O.push('한 번 더 넣었다 뺀 것이 같은가 = ' + (host.innerHTML === before));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04b.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
넣은 것   <p>가<div>나</div>
읽은 것   <p>가</p><div>나</div>
자식 수   2   p 는 div 를 품지 못한다

넣은 것   <b><i>가</b>나</i>
읽은 것   <b><i>가</i></b><i>나</i>
자식 수   2   겹친 태그를 파서가 다시 연다

넣은 것   <td>셀</td>
읽은 것   셀
자식 수   0   div 안에서는 td 가 버려진다

넣은 것   <tr><td>셀
읽은 것   <tbody><tr><td>셀</td></tr></tbody>
자식 수   1   table 안에서는 tbody 가 끼워진다

넣은 것   <ul><li>하나<li>둘
읽은 것   <ul><li>하나</li><li>둘</li></ul>
자식 수   1   닫지 않아도 닫아 준다

넣은 것   &amp;lt; &lt; &#65;
읽은 것   &amp;lt; &lt; A
자식 수   0   문자 참조는 풀린다

한 번 더 넣었다 뺀 것이 같은가 = true
(exit 0)
```

```text
   넣은 것                       읽은 것
   <p>가<div>나</div>       ->   <p>가</p><div>나</div>      p 가 닫히고 div 가 형제가 됐다
   <b><i>가</b>나</i>       ->   <b><i>가</i></b><i>나</i>   i 가 다시 열렸다
   <td>셀</td>  (div 안)    ->   셀                          td 가 통째로 버려졌다
   <tr><td>셀   (table 안)  ->   <tbody><tr><td>셀</td></tr></tbody>   tbody 가 끼워졌다
   <ul><li>하나<li>둘       ->   <ul><li>하나</li><li>둘</li></ul>     알아서 닫았다
   &amp;lt; &lt; &#65;      ->   &amp;lt; &lt; A             문자 참조가 한 번 풀렸다
```

그림 해설 (한 단계씩):

- **`innerHTML` 쓰기는 「문자열을 저장」하는 것이 아니라 「파싱해서 트리를 만드는」 것**이다. 그래서 **읽어 보면 다른 문자열**이 나온다.
- **어떤 것은 고쳐지고 어떤 것은 버려진다** — `<td>` 는 `<div>` 안에서 사라졌고, 같은 것이 `<table>` 안에서는 `<tbody>` 까지 생겨 살았다. **문맥이 결과를 바꾼다.**
- ★ **이 규칙의 정본은 여기가 아니다.** 「태그 수프가 어떤 트리가 되나」는 HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서·오류 복구)이 정본이다. **여기는 「그 파서를 `innerHTML` 이 부른다」는 사실과 그 결과가 API 삽입과 다르다는 것**까지만 다룬다.
- **[03번 주제](../03-node-creation-insertion-removal/2-summary.md)의 실측과 나란히 놓으면** 경계가 선명하다 — `p.appendChild(div)` 는 `<p><div></div></p>` 를 만드는데, 같은 모양을 `innerHTML` 로 넣으면 파서가 쪼갠다.
- **한 번 넣었다 뺀 것은 안정적이다** — 출력의 마지막 줄에서 `true` 가 나왔다. 파서가 고친 결과를 다시 넣으면 더는 안 바뀐다.

비용 — (5)에서 잰다. **파싱이 있다는 것이 비용의 근거이고, 그 크기는 재야 안다.**

### (3) ★★ XSS — `<script>` 는 안 돌고 `<img onerror>` 는 돈다

**언제 쓰나** — 신뢰할 수 없는 문자열을 화면에 넣을 때. **이 주제에서 가장 비싼 오해가 여기 있다.**

```html
<!-- ex04c.html -->
<!doctype html>
<meta charset="utf-8">
<title>04c</title>
<div id="viaHTML"></div>
<div id="viaText"></div>
<script>
window.run = {script: 0, img: 0, svg: 0, text: 0};
const payload =
  '<script>window.run.script++;<' + '/script>' +
  '<img src="data:image/gif;base64,zzz" onerror="window.run.img++">' +
  '<svg onload="window.run.svg++"></svg>';
document.getElementById('viaHTML').innerHTML = payload;
document.getElementById('viaText').textContent = payload;
window.addEventListener('load', () => setTimeout(() => {
  const O = [];
  O.push('넣은 문자열 = ' + payload);
  O.push('');
  O.push('innerHTML 로 넣었을 때 실행 횟수  script=' + run.script + '  img(onerror)=' + run.img + '  svg(onload)=' + run.svg);
  O.push('textContent 로 넣었을 때 실행 횟수 = ' + run.text + '  (아무 핸들러도 등록되지 않는다)');
  O.push('');
  O.push('viaHTML.children.length = ' + document.getElementById('viaHTML').children.length +
         '   태그 = ' + [...document.getElementById('viaHTML').children].map(e => e.tagName).join(','));
  O.push('viaText.children.length = ' + document.getElementById('viaText').children.length);
  O.push('viaText.innerHTML = ' + document.getElementById('viaText').innerHTML);
  O.push('');
  const s = document.getElementById('viaHTML').querySelector('script');
  O.push('innerHTML 이 만든 script 노드는 트리에 있는가 = ' + (s !== null) + '   내용 = ' + JSON.stringify(s && s.textContent));
  O.push('');
  document.getElementById('viaText').appendChild(s);
  O.push('그 script 노드를 다른 부모로 옮겨 붙인 뒤 script 실행 횟수 = ' + run.script);
  const fresh = document.createElement('script');
  fresh.textContent = 'window.run.script += 10;';
  document.body.appendChild(fresh);
  O.push('createElement 로 만든 script 를 붙이면        script 실행 횟수 = ' + run.script);
  document.body.appendChild(Object.assign(document.createElement('script'),
    {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
}, 0));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '3,5p'
innerHTML 로 넣었을 때 실행 횟수  script=0  img(onerror)=1  svg(onload)=1
textContent 로 넣었을 때 실행 횟수 = 0  (아무 핸들러도 등록되지 않는다)

(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '6,10p'
viaHTML.children.length = 3   태그 = SCRIPT,IMG,svg
viaText.children.length = 0
viaText.innerHTML = &lt;script&gt;window.run.script++;&lt;/script&gt;&lt;img src="data:image/gif;base64,zzz" onerror="window.run.img++"&gt;&lt;svg onload="window.run.svg++"&gt;&lt;/svg&gt;

innerHTML 이 만든 script 노드는 트리에 있는가 = true   내용 = "window.run.script++;"
(exit 0)
```

```text
   한 문자열에 셋을 담아 던졌다

   <script>…</script>                 -> 실행 0회   ★ 안 돈다
   <img src=… onerror="…">            -> 실행 1회   ★ 돈다
   <svg onload="…">                   -> 실행 1회   ★ 돈다

   그런데 트리를 보면
   viaHTML.children = [SCRIPT, IMG, svg]      <- script 노드가 '있다'
   그 노드의 내용도 그대로 있다                 <- 그런데 '안 돌았다'

   ★ '트리에 있나' 와 '돌았나' 는 다른 질문이다.  창 4 가 없으면 못 가른다
```

그림 해설 (한 단계씩):

- **`<script>` 가 안 도는 것은 방어가 아니라 우연에 가깝다.** 명세가 「fragment parsing 으로 만들어진 script 는 실행 금지」로 정해 둔 것이고, **다른 실행 경로는 하나도 안 막는다.**
- **`onerror`·`onload` 같은 이벤트 핸들러 속성은 그대로 살아난다.** 실측에서 둘 다 **1회** 돌았다.
- **그래서 「`<script>` 만 걸러내면 된다」는 틀렸다.** 걸러야 할 것은 태그 하나가 아니라 **핸들러 속성 전부 · `javascript:` URL · `<iframe srcdoc>` · `<style>` 등 면적 전체**다. 직접 만든 필터로는 **못 막는다**고 보는 쪽이 안전하다.
- **`textContent` 쪽은 실행이 0 이고 자식 요소도 0** 이다. 같은 문자열이 **글자로만** 들어갔고, 읽어 보면 `&lt;script&gt;` 처럼 **이스케이프된 채로** 보인다.
- ★ **`nodeName` 이 `SCRIPT`·`IMG` 는 대문자인데 `svg` 는 소문자**다 — HTML 요소와 SVG 요소의 차이다([01번 주제](../01-document-and-node-tree/2-summary.md)).

**그 `<script>` 노드를 다른 곳으로 옮기면 살아날까** — 던져서 확인했다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04c.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '12,13p'
그 script 노드를 다른 부모로 옮겨 붙인 뒤 script 실행 횟수 = 0
createElement 로 만든 script 를 붙이면        script 실행 횟수 = 10
(exit 0)
```

```text
   innerHTML 이 만든 script 를 다른 부모로 appendChild      -> 여전히 0회
   createElement('script') 로 만든 것을 appendChild         -> 돈다 (+10)

   ★ '안 돈다' 는 그 노드에 찍힌 플래그이고, 자리를 옮긴다고 지워지지 않는다
   ★ 그런데 '스크립트를 만들어 붙이면 도는' 경로는 멀쩡히 열려 있다
```

- **`innerHTML` 로 만든 `<script>` 는 옮겨도 안 돈다.** 명세가 그 노드를 **「이미 시작된 것」으로 표시**해 두기 때문이고, 실측에서 옮긴 뒤에도 실행 횟수가 **0** 이었다.
- **그런데 `createElement('script')` 로 만들어 붙이면 돈다**(카운터가 10 늘었다). 그러니 「스크립트는 못 돈다」가 아니라 「**이 경로 하나만 막혀 있다**」가 맞다.

비용 — 없음. 이 절의 값은 비용이 아니라 「**오해를 실측으로 깨는 것**」이다.

```html demo
<div class="box">innerHTML &nbsp;&nbsp;-> <span id="h"></span></div>
<div class="box">textContent -> <span id="t"></span></div>
<script>
  const 받은문자열 = '<b style="color:#dc2626">굵은 빨강</b>';
  document.getElementById('h').innerHTML = 받은문자열;
  document.getElementById('t').textContent = 받은문자열;
</script>
<style>.box { border: 1px solid #cbd5e1; padding: 6px; margin: 4px 0; font: 14px/1.5 monospace; }</style>
```

> **보이는 것** — 위 칸에는 빨갛고 굵은 「굵은 빨강」 네 글자만 보이고, 아래 칸에는 `<b style="color:#dc2626">굵은 빨강</b>` 이라는 문자열이 **태그째 검은 고정폭 글자**로 보인다. 같은 문자열을 넣었는데 위쪽만 마크업으로 해석됐다.\
> *(Chrome 151 headless 실측: 위 칸 안쪽 `b` 의 계산값이 `color: rgb(220, 38, 38)` · `font-weight: 700`, 아래 칸은 `rgb(0, 0, 0)` · `400` 이고 그 `textContent` 가 태그 문자열 전체다.)*\
> **바꿔 볼 것** — 넣는 문자열을 `<img src=x onerror="alert(1)">` 로 바꾸면 위 칸에서만 핸들러가 돈다(위 (3)의 실측과 같은 일이다) · `innerHTML` 쪽을 `textContent` 로 바꾸면 두 칸이 똑같아진다.

### (4) 쓰기 — 셋이 만드는 트리가 다르다

**언제 쓰나** — 글자를 넣을 때. **읽기만큼 쓰기도 셋이 갈린다.**

```html
<!-- ex04e.html -->
<!doctype html>
<meta charset="utf-8">
<title>04e</title>
<div id="a"></div><div id="b"></div><div id="c"></div>
<script>
const O = [];
const s = '한 줄\n다음 줄 <b>굵게</b>';
O.push('넣는 문자열 = ' + JSON.stringify(s));
O.push('');
const a = document.getElementById('a'), b = document.getElementById('b'), c = document.getElementById('c');
a.textContent = s;
b.innerText = s;
c.innerHTML = s;
O.push('textContent 로 쓰면 innerHTML = ' + JSON.stringify(a.innerHTML));
O.push('innerText 로 쓰면   innerHTML = ' + JSON.stringify(b.innerHTML));
O.push('innerHTML 로 쓰면   innerHTML = ' + JSON.stringify(c.innerHTML));
O.push('');
O.push('각각의 children.length = ' + [a.children.length, b.children.length, c.children.length].join(' / '));
O.push('각각의 childNodes.length = ' + [a.childNodes.length, b.childNodes.length, c.childNodes.length].join(' / '));
O.push('');
const kept = c.firstChild;
c.textContent = '';
O.push("textContent = '' 뒤 c.childNodes.length = " + c.childNodes.length);
O.push('떼어진 노드는 살아 있다: kept.nodeValue = ' + JSON.stringify(kept.nodeValue) + '  isConnected = ' + kept.isConnected);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '3,5p'
textContent 로 쓰면 innerHTML = "한 줄\n다음 줄 &lt;b&gt;굵게&lt;/b&gt;"
innerText 로 쓰면   innerHTML = "한 줄<br>다음 줄 &lt;b&gt;굵게&lt;/b&gt;"
innerHTML 로 쓰면   innerHTML = "한 줄\n다음 줄 <b>굵게</b>"
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04e.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '7,8p'
각각의 children.length = 0 / 1 / 1
각각의 childNodes.length = 1 / 3 / 2
(exit 0)
```

```text
   같은 문자열  "한 줄\n다음 줄 <b>굵게</b>"  을 셋으로 썼다

   textContent =  ->  텍스트 노드 하나.        \n 은 \n 그대로, <b> 는 글자로
   innerText   =  ->  \n 이 <br> 이 된다!      요소가 생긴다
   innerHTML   =  ->  <b> 가 요소가 된다.      \n 은 \n 그대로

   childNodes   1 / 3 / 2
   children     0 / 1 / 1
```

그림 해설 (한 단계씩):

- **`textContent` 쓰기만 요소를 하나도 안 만든다.** 자식이 **텍스트 노드 하나**다 — 이것이 「절대 실행되지 않는다」의 구조적 이유다.
- ★ **`innerText` 쓰기는 줄바꿈을 `<br>` 로 바꾼다.** 읽을 때 `<br>` 을 `\n` 으로 준 것의 **역방향**이다. 「보이는 대로」라는 계약이 쓰기에도 적용된다.
- **`textContent = ''` 는 자식을 전부 뗀다.** 뗀 노드는 **살아 있다** — 출력의 마지막 줄에서 `isConnected` 가 `false` 인 채 값이 남아 있다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)).
- 자식을 비우는 것이라면 **`replaceChildren()`** 이 더 분명하다([03번 주제](../03-node-creation-insertion-removal/2-summary.md)).

비용 — (5)에서 잰다.

### (5) 비용 — 재고 나서 말한다

**언제 쓰나** — 「`innerHTML` 이 느리다」 같은 말을 하기 전에.

```html
<!-- ex04d.html -->
<!doctype html>
<meta charset="utf-8">
<title>04d</title>
<div id="host"></div>
<script>
const N = 9, COUNT = 2000;
const host = document.getElementById('host');
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const med = a => a.slice().sort((x, y) => x - y)[(a.length - 1) >> 1];
const bench = (label, fn) => {
  const t = [];
  for (let r = 0; r < N; r++) {
    host.textContent = '';
    const s = performance.now();
    fn();
    t.push(performance.now() - s);
  }
  O.push(padw(label, 34) + '중앙값 ' + med(t).toFixed(2).padStart(8) + ' ms' +
         '   최소 ' + Math.min(...t).toFixed(2).padStart(8) + '   최대 ' + Math.max(...t).toFixed(2).padStart(8));
};
O.push('쓰기 — ' + COUNT + '개 항목 만들기 · ' + N + '판의 중앙값');
O.push('');
bench('innerHTML += 를 항목마다', () => { for (let i = 0; i < COUNT; i++) host.innerHTML += '<span>' + i + '</span>'; });
bench('문자열을 모아 innerHTML 한 번', () => { let s = ''; for (let i = 0; i < COUNT; i++) s += '<span>' + i + '</span>'; host.innerHTML = s; });
bench('appendChild 를 항목마다', () => { for (let i = 0; i < COUNT; i++) host.appendChild(Object.assign(document.createElement('span'), {textContent: i})); });
bench('DocumentFragment 에 모아 한 번', () => { const f = document.createDocumentFragment(); for (let i = 0; i < COUNT; i++) f.appendChild(Object.assign(document.createElement('span'), {textContent: i})); host.appendChild(f); });
bench('textContent 한 번(태그 없음)', () => { let s = ''; for (let i = 0; i < COUNT; i++) s += i; host.textContent = s; });
O.push('');
O.push('읽기 — 위와 같은 ' + COUNT + '개 트리에서 · 읽기 전마다 스타일을 건드려 레이아웃을 더럽힌다');
O.push('');
{ const f = document.createDocumentFragment();
  for (let i = 0; i < COUNT; i++) f.appendChild(Object.assign(document.createElement('span'), {textContent: i}));
  host.textContent = ''; host.appendChild(f); }
const read = (label, fn) => {
  const t = [], v = [];
  for (let r = 0; r < N; r++) {
    host.style.paddingLeft = (r % 2) + 'px';
    const s = performance.now();
    v.push(fn().length);
    t.push(performance.now() - s);
  }
  O.push(padw(label, 34) + '중앙값 ' + med(t).toFixed(2).padStart(8) + ' ms' +
         '   최소 ' + Math.min(...t).toFixed(2).padStart(8) + '   최대 ' + Math.max(...t).toFixed(2).padStart(8) +
         '   길이 ' + v[0]);
};
read('textContent 읽기', () => host.textContent);
read('innerHTML 읽기', () => host.innerHTML);
read('innerText 읽기', () => host.innerText);
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04d.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
쓰기 — 2000개 항목 만들기 · 9판의 중앙값

innerHTML += 를 항목마다          중앙값  1558.70 ms   최소  1065.30   최대  2777.40
문자열을 모아 innerHTML 한 번     중앙값     1.20 ms   최소     1.00   최대     2.00
appendChild 를 항목마다           중앙값     2.20 ms   최소     1.70   최대     3.40
DocumentFragment 에 모아 한 번    중앙값     2.50 ms   최소     1.60   최대     5.90
textContent 한 번(태그 없음)      중앙값     0.10 ms   최소     0.00   최대     0.30
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --dump-dom ex04d.html | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,13p'
읽기 — 위와 같은 2000개 트리에서 · 읽기 전마다 스타일을 건드려 레이아웃을 더럽힌다

textContent 읽기                  중앙값     0.00 ms   최소     0.00   최대     0.30   길이 6890
innerHTML 읽기                    중앙값     0.20 ms   최소     0.10   최대     0.30   길이 32890
innerText 읽기                    중앙값     4.10 ms   최소     3.30   최대    70.10   길이 6890
(exit 0)
```

```text
   쓰기 — 2000개 항목 · 9판의 중앙값 (수치는 흔들린다. 자릿수만 읽어라)

   innerHTML += 를 항목마다      ~1,000 ms 대       ★ 세 자릿수 크다
   문자열을 모아 innerHTML 한 번  ~1 ms 대
   appendChild 를 항목마다        ~1 ms 대
   DocumentFragment 에 모아       ~1 ms 대          ★ 뒤 셋은 같은 자릿수다
   textContent 한 번(태그 없음)   분해능 아래

   읽기 — 같은 2000개 트리 · 읽기 전마다 스타일을 건드린다

   textContent   분해능 아래
   innerHTML     ~0.2 ms
   innerText     ~3\~5 ms       ★ 한두 자릿수 크다 (레이아웃을 돌린다)
```

그림 해설 (한 단계씩):

- ★ **`innerHTML +=` 만 자릿수가 다르다.** `+=` 는 **읽기 + 문자열 합치기 + 쓰기**라서, 항목마다 **트리 전체를 직렬화하고 다시 파싱**한다. 항목 수의 제곱으로 자란다.
- ★ **`DocumentFragment` 가 `appendChild` 반복보다 빠르지 않았다.** 세 판 모두 같은 자릿수였고 순위가 판마다 뒤집혔다 — **「조각에 모아 한 번에 넣으면 빠르다」는 이 측정에서 재현되지 않았다.** 트리에 이미 붙은 부모에 붙이는 이 실험 조건에서는 **레이아웃이 중간에 안 돌기 때문**으로 보이지만, 그 원인까지는 이 문서가 확인하지 않았다. 일괄 삽입의 정본은 목록의 **05번 주제**다.
- ★ **`innerText` 읽기만 한두 자릿수 크다.** 읽기 전에 스타일을 건드려 레이아웃을 더럽혔기 때문이고, **그것이 이 프로퍼티의 계약**이다 — 「보이는 것」을 답하려면 화면을 먼저 계산해야 한다. 이것이 목록의 **10번 주제**(레이아웃 스래싱)의 씨앗이다.
- `textContent` 읽기가 `0.00` 으로 나온 것은 「공짜」가 아니라 「**이 도구로는 못 잰다**」는 뜻이다. `performance.now()` 가 100마이크로초로 뭉개진다.

비용 — 이 절 자체가 비용이다. **9판·중앙값·최소·최대**를 함께 실었고, **자릿수만 결론으로 쓴다.**

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
el.textContent          // 읽기: 트리의 모든 글자 · 쓰기: 텍스트 노드 하나
el.innerText            // 읽기: 렌더된 글자 · 쓰기: 줄바꿈이 <br> 이 된다
el.innerHTML            // 읽기: 자식들의 마크업 · 쓰기: 파싱해서 자식을 갈아 끼운다
el.outerHTML            // 자기 자신까지 포함한 마크업
el.insertAdjacentHTML('beforeend', s)   // 기존 자식을 안 버리고 파싱해 넣는다
el.replaceChildren()    // 파싱 없이 자식을 비운다
node.nodeValue          // Text·Comment 의 글자 (01번)
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
el.innerHTML = 사용자입력;                 // XSS
el.innerHTML = '<script>…</script>';      // 안 돌아서 '안전해 보인다' — 착각의 씨앗
for (…) el.innerHTML += '<li>…</li>';     // 세 자릿수 느리다 (실측)
el.innerHTML = '';                        // 파서를 부른다. replaceChildren() 이 낫다
const t = el.innerText;                   // 루프 안이면 레이아웃을 강제한다
el.innerText === el.textContent           // 트리 밖에서는 늘 true — 비교가 무의미해진다
```

- **`insertAdjacentHTML` 도 같은 파서를 쓴다.** `innerHTML` 보다 안전한 것이 아니다 — **XSS 면적이 같다.**
- **`outerHTML` 에 쓰면 자기 자신이 교체된다.** 그 뒤 변수는 **문서에서 떨어진 옛 노드**를 가리킨다.

### 어디서 헷갈리나

- **`innerText` 와 `textContent` 는 트리 밖에서 같은 값**이다. 테스트에서 둘을 바꿔 써도 통과하다가, 화면에 붙이는 순간 갈린다.
- **`innerHTML` 로 읽은 것을 그대로 다시 쓰면 같은 트리가 되지만**, 그것은 **이미 한 번 파서를 통과한 문자열**이라 그렇다. 사람이 쓴 문자열은 고쳐진다.
- **`textContent` 가 `<style>` 내용을 준다.** 「화면 글자만」을 기대하면 놀란다.
- **`innerHTML` 이 읽기에도 비용이 있다** — 트리를 문자열로 다시 만드는 직렬화다.

## 어디서 틀리나

이 주제의 값어치는 전부 여기 있다. 일곱 중 여섯이 **에러 없이 조용히 어긋난다.**

### 1. `<script>` 를 걸러내면 안전하다고 믿는다

실측에서 `<script>` 는 **0회** 돌았고 `<img onerror>` 와 `<svg onload>` 는 **각각 1회** 돌았다.\
**`<script>` 가 안 도는 것이 오히려 함정**이다 — 직접 만든 필터가 「걸렀다」고 착각하게 만든다.

### 2. `innerHTML` 로 읽은 것과 내가 넣은 것이 같을 거라 여긴다

실측에서 `<p>가<div>나</div>` 가 **`<p>가</p><div>나</div>`** 로 나왔다.\
문자열을 저장한 것이 아니라 **파싱해서 트리로 만든 것**이라 그렇다.

### 3. `innerText` 를 「글자 읽기」로 쓴다

**렌더 결과**다. `display: none` 이 걸린 부분이 빠지고, `text-transform` 이 적용된 글자가 나온다.\
그리고 **문서 밖에서는 `textContent` 와 같아진다** — 테스트가 통과하고 실제에서 깨지는 전형적인 자리다.

### 4. 루프 안에서 `innerHTML +=` 를 쓴다

실측에서 **세 자릿수** 느렸다(2000항목 기준 1,000ms 대 1ms 대). 항목마다 **직렬화 + 파싱**이 한 번씩 일어난다.

### 5. `DocumentFragment` 를 쓰면 무조건 빠르다고 여긴다

이 실험에서는 **`appendChild` 반복과 같은 자릿수**였고 순위가 판마다 뒤집혔다.\
**빠르다고 적힌 것을 옮겨 적지 말고 자기 조건에서 재라** — 그것이 이 저장소의 규칙이다.

### 6. `innerHTML = ''` 로 비운다

파서를 부르는 경로이고, 의도가 「비우기」라면 **`replaceChildren()`** 이 더 분명하다.

### 7. `innerText` 를 읽고 바로 스타일을 쓴다

읽기가 **레이아웃을 강제**하므로 읽기·쓰기를 교차시키면 프레임마다 레이아웃이 다시 돈다. 그 사고의 정본은 목록의 **10번 주제**다.

## 구현 세부사항 대 언어 보장

여기서 「언어 보장」은 **명세(WHATWG DOM·HTML)가 정한 것**이고, 「구현」은 **Blink 가 하는 것**이다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `textContent` 가 **하위 트리의 모든 `Text` 를 이어 붙인** 것 | **명세**(DOM §4.4 `textContent`) |
| `textContent` 가 `<style>`·`<script>` 안의 글자도 주는 것 | **명세**(그 안도 `Text` 노드다) |
| `innerHTML` 쓰기가 **fragment parsing** 을 쓰는 것 | **명세**(HTML — DOM Parsing) |
| **그렇게 만들어진 `<script>` 가 실행되지 않는 것** | **명세**(HTML — fragment parsing 으로 만든 script 는 실행 금지) |
| **`onerror`·`onload` 속성은 그대로 동작하는 것** | **명세.** 막는 규정이 없다 — 이것이 XSS 면적의 본체다 |
| `innerText` 가 **렌더 결과**를 주는 것 | **명세**(HTML — `innerText` getter) |
| 렌더되지 않는 요소에서 `innerText` 가 **`textContent` 와 같아지는 것** | **명세**(같은 절 — not being rendered 면 textContent) |
| `innerText` 쓰기가 줄바꿈을 **`<br>`** 로 바꾸는 것 | **명세**(`innerText` setter) |
| 파서가 `<p>` 안의 `<div>` 를 쪼개고 `<tbody>` 를 끼우는 것 | **명세**(HTML 파싱 알고리즘). **정본은 HTML 갈래다** |
| `text-transform` 이 `innerText` 에 반영되는 것 | **명세**가 렌더 결과를 말하므로 따라오는 결과. 세부는 **관찰** |
| **`performance.now()` 가 100마이크로초로 뭉개지는 것** | **구현**(Blink 의 타이머 분해능 정책). 명세가 정한 값이 아니다 |
| **모든 시간 수치** | **이 판의 관찰.** 자릿수만 결론으로 쓴다 |
| `DocumentFragment` 가 이 실험에서 안 빨랐던 것 | **이 조건에서의 관찰.** 일반 규칙으로 읽지 않는다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 사용자가 준 글자를 보여 준다 | `textContent` | `innerHTML`(XSS) |
| 마크업이 꼭 필요하다 | 서버·라이브러리에서 **정화한** HTML | 직접 만든 태그 필터 |
| 화면에 보이는 글자를 뽑는다 | `innerText` | `textContent`(안 보이는 것이 섞인다) |
| 텍스트를 비교·검색한다 | `textContent` | `innerText`(화면에 따라 답이 바뀐다) |
| 목록을 만든다 | 문자열을 모아 `innerHTML` 한 번 · 노드 조립 | 루프 안에서 `innerHTML +=` |
| 자식을 비운다 | `replaceChildren()` | `innerHTML = ''` |
| 루프 안에서 글자를 읽는다 | `textContent` | `innerText`(레이아웃을 돌린다) |

판단 규칙 두 줄.

- **「이 문자열이 마크업이어야 하나」를 먼저 묻는다.** 아니면 `textContent` 다. 그 한 줄이 XSS 면적을 0 으로 만든다.
- **마크업이어야 한다면 「누가 만든 문자열인가」를 묻는다.** 내가 만든 것이 아니면 **직접 거르지 말고** 정화를 전담하는 도구에 맡긴다.

## 핵심 문장

- **셋은 다른 것을 준다** — `textContent` 는 트리의 모든 글자(`<style>` 내용까지), `innerText` 는 **화면에 보이는 글자**, `innerHTML` 은 **트리에서 되뽑은 마크업**이다.
- **`innerText` 는 렌더에 의존한다.** 같은 노드라도 **부모를 통해 읽으면 빠지고 자기 자신으로 읽으면 나온다** — 명세가 「렌더되지 않으면 `textContent` 와 같다」고 정해 뒀기 때문이다. **문서 밖에서는 언제나 `textContent` 와 같다.**
- **`innerHTML` 쓰기는 파서 호출**이다. 실측에서 `<p>가<div>나</div>` 가 `<p>가</p><div>나</div>` 로 **고쳐져** 들어갔다. 그 규칙의 정본은 HTML 갈래(03번)이고, 여기는 **그 파서를 부른다는 사실**까지다.
- ★ **`<script>` 는 안 돌고 `<img onerror>`·`<svg onload>` 는 돈다**(실측 0회 대 1회 대 1회). **`<script>` 노드는 트리에 멀쩡히 들어 있다** — 「들어갔나」와 「돌았나」는 다른 질문이다.
- **그래서 「script 만 막으면 된다」는 틀렸다.** 막아야 하는 것은 **핸들러 속성 전부와 URL 스킴까지**이고, 직접 만든 필터로는 못 막는다고 보는 쪽이 안전하다.
- **`textContent` 는 절대 실행되지 않는다.** 쓰기가 **텍스트 노드 하나**만 만들기 때문이다 — 구조가 보장한다.
- **비용은 쟀다** — 2000항목 9판 중앙값에서 `innerHTML +=` 만 **세 자릿수** 컸고, 읽기에서는 `innerText` 만 **한두 자릿수** 컸다. **`DocumentFragment` 는 이 조건에서 안 빨랐다.**
- **`performance.now()` 는 100마이크로초로 뭉개진다** — `0.00` 은 「공짜」가 아니라 「못 잰다」다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 04번)
- [01번 주제](../01-document-and-node-tree/2-summary.md) — `Text` 노드와 직렬화의 정본. `textContent` 가 무엇을 이어 붙이는지가 그쪽 개념 위에 선다
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md) — `innerHTML` 로 영역을 통째로 갈았을 때 **잡아 둔 컬렉션이 어떻게 되는지**의 실측이 그쪽에 있다
- [03번 주제](../03-node-creation-insertion-removal/2-summary.md) — **노드 단위 조작의 정본.** 여기는 문자열 단위다. 「`p.appendChild(div)` 는 되는데 같은 모양을 `innerHTML` 로 넣으면 쪼개진다」는 대비가 두 주제의 경계다
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **03번**(파서와 오류 복구) — ★ **「어떤 마크업이 어떤 트리가 되나」의 정본.**\
  그쪽은 **파서 알고리즘과 암묵 태그 삽입**까지, 여기는 **`innerHTML` 이 그 파서를 부른다는 것과 그 결과가 API 삽입과 다르다는 것**부터다. 위 (2)의 실측은 **그 사실을 보이기 위한 최소 예제**이고, 규칙 설명은 그쪽에 맡긴다
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **04번**(공백·텍스트·문자 참조) — `&amp;lt;` 가 한 번만 풀리는 것과 공백 축약의 정본
- [`../../security/`](../../security/) — **XSS 의 위협 모델과 방어 설계의 정본.** 여기는 **`innerHTML` 이라는 브라우저 표면 하나**에서 무엇이 실행되는지를 실측으로 보이는 데까지
- 목록의 **58번 주제**(CSP) — 스크립트 실행을 **브라우저가 차단**하는 층. 여기의 필터 이야기와 층이 다르다
- 목록의 **10번 주제**(레이아웃 스래싱) — `innerText` 읽기가 왜 비싼지의 정본
- 목록의 **05번 주제**(`DocumentFragment` 와 `<template>`) — 일괄 삽입의 정본. 위 (5)에서 **조각이 안 빨랐던 것**의 조건을 그쪽에서 더 다룬다

## 용어 풀이

- **`textContent`** — 하위 트리의 모든 `Text` 노드를 이어 붙인 문자열. 쓰면 **텍스트 노드 하나**가 된다.
- **`innerText`** — **렌더된** 텍스트. 안 보이는 것은 빠지고 `text-transform` 이 적용된다. 렌더되지 않으면 `textContent` 와 같다.
- **`innerHTML`** — 자식들을 직렬화한 마크업 문자열. 쓰면 **파싱**해서 자식을 갈아 끼운다.
- **fragment parsing** — 문자열을 어떤 요소의 자식으로 파싱하는 절차. **문맥 요소에 따라 결과가 달라진다.**
- **XSS(교차 사이트 스크립팅)** — 남이 준 문자열이 내 페이지의 코드로 실행되는 것.
- **이벤트 핸들러 속성** — `onerror`·`onload` 처럼 마크업에 쓴 핸들러. **`innerHTML` 로 들어가면 그대로 동작한다.**
- **직렬화(serialization)** — 트리를 다시 HTML 문자열로 만드는 것. `innerHTML` 읽기가 이것이다.
- **레이아웃 강제(forced layout)** — 최신 결과가 필요해서 그 자리에서 레이아웃을 돌리는 것. `innerText` 읽기가 유발한다.
- **분해능(resolution)** — 측정 도구가 구분할 수 있는 최소 간격. Chrome 의 `performance.now()` 는 100마이크로초다.
- **중앙값(median)** — 여러 판을 크기순으로 늘어놓았을 때 가운데 값. 평균보다 튀는 판에 덜 흔들린다.

## 더 들어가면

- **`innerText` 는 원래 IE 의 확장**이었다. 다른 엔진이 따라 구현하면서 동작이 제각각이었고, 2016년 무렵에야 「렌더된 텍스트」로 명세가 쓰였다. **표준이 구현을 뒤따라간 전형**이고, 그래서 엔진 차이가 남아 있을 수 있는 자리다 — 이 문서는 **한 엔진만** 봤다.
- **`Trusted Types`** 는 `innerHTML` 같은 **위험한 싱크에 문자열을 그냥 못 넣게** 만드는 브라우저 기능이다. Baseline **newly**(2026-02-24)라 **저변에 도달하기 전**이고, 그래서 이 문서는 대안으로 확정해 적지 않았다([`../README.md`](../README.md)).
- **Sanitizer API** 는 브라우저가 정화를 맡아 주는 방향인데 Baseline **limited** 다. 오늘 쓰는 것은 대개 라이브러리이고, **직접 만든 필터는 이 문서의 실측이 보여 준 이유로 권하지 않는다.**
- **`innerHTML` 읽기도 싸지 않다.** 실측에서 `textContent` 읽기보다 컸다 — 트리를 문자열로 다시 만드는 직렬화이기 때문이다. 다만 `innerText` 와는 **자릿수가 달랐다.**
- **「안 돈다」가 노드에 찍힌 플래그라는 것**은 위 (3)의 마지막 실측이 보여 준다 — 옮겨도 안 돌았다. 반면 `createElement('script')` 로 만든 것은 붙이자마자 돌았다. **막힌 것은 「파싱으로 만들어졌다」는 출처 하나**이고, 스크립트를 만들어 붙이는 정상 경로는 그대로다.
