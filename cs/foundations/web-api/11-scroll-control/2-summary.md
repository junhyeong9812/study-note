# web-api/11 — 스크롤 제어: `scrollTo`/`scrollBy`/`scrollIntoView`·스크롤 컨테이너 찾기·위치 복원 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 여기서 다루는 것은 「CSS 가 무엇을 스크롤 컨테이너로 만드나」가 아니라 「**스크립트가 그것을 어떻게 찾아 굴리나**」다. `overflow` 값별 판정과 스크롤바가 먹는 폭은 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)가 정본이고 여기서 다시 쓰지 않는다.\
> **기준 소스** — [CSSOM View Module](https://drafts.csswg.org/cssom-view/) 의 「Scrolling」·「`ScrollToOptions`」·「`scrollIntoView()`」·「`scrollingElement`」 절과 [HTML Living Standard — `history.scrollRestoration`](https://html.spec.whatwg.org/multipage/nav-history-apis.html#scroll-restoration-mode). 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 블록마다 명령이 배너로 실려 있고, 그 배너에는 **`--window-size=1000,800`** 이 들어 있다 — **스크롤 상한이 뷰포트 높이에 달려 있어 창 크기를 빼면 수치가 재현되지 않는다.**\
> ★ **못 잰 것이 하나 있다** — `behavior: 'smooth'` 의 **도착**이다. 「부른 직후에는 안 움직인다」까지는 관측했고 **애니메이션이 끝나는 순간은 이 도구로 못 봤다**((9)).\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. **이식성을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `scrollIntoView` 의 옵션 객체와 `scrollingElement` 는 CSSOM View 로 사후 명세화된 표면이고 **Baseline 추적 대상이 아닐 만큼 오래됐다**(갈래 [`../README.md`](../README.md) 의 「확인하지 못한 것」).\
> **선행** — [09번 주제](../09-element-geometry/2-summary.md)(`scrollTop` 을 **읽는** 쪽)와 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)(무엇이 스크롤 컨테이너인가).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 좌표를 재지만 **시간을 안 재기 때문**이다. 다만 **못 잰 칸**이 하나 있다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 모든 스크롤 오프셋 · 클램프 상한 · `scrollingElement` 가 누구인가 · `scrollIntoView` 옵션별 결과 · `overflow` 값별 판정 | 같은 창 크기·같은 판이면 결정적이다. **세 판을 돌려 한 글자도 같았다** |
| **흔들린다** | **창 크기를 바꾸면 상한과 좌표 전부** | 상한 = `scrollHeight − clientHeight` 이고 `clientHeight` 는 뷰포트에 달렸다. 그래서 배너에 `--window-size=1000,800` 을 박았다 |
| **흔들린다** | 스크롤바가 먹는 **15px** | **이 플랫폼의 스크롤바 설정**에 달렸다(정본: [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)) |
| **못 잰다** | `behavior: 'smooth'` 의 **도착 시각과 중간 값** | 프레임이 이 도구로 통제되지 않는다((9)). **안 돌려 본 것이 아니라 못 잰 것이다** |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

## 한눈에 — 쉽게 말하면

**★ 스크롤은 「요소를 옮기는 것」이 아니라 「상자 안에서 내용을 미는 것」이다. 그래서 먼저 물어야 할 것은 「어느 상자가 밀리나」다.**

두루마리에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 두루마리를 **감은 정도** | `el.scrollTop` — 내용을 얼마나 밀어 올렸나 |
| **얼마까지 감을 수 있나** | `scrollHeight − clientHeight` — 넘으면 **잘린다** |
| **절대 위치로 감기** | `scrollTo(x, y)` · `scrollTop = n` |
| **상대로 더 감기** | `scrollBy(dx, dy)` |
| **이 글자가 보이게 감아 줘** | `scrollIntoView()` — **얼마나 감을지는 브라우저가 정한다** |
| 두루마리가 **여러 겹** 겹쳐 있다 | 스크롤 컨테이너가 중첩된다 — `scrollIntoView` 는 **전부** 감는다 |
| **문서 전체도 두루마리다** | 마지막 한 겹이 `document.scrollingElement` 다 |
| 천천히 감아 달라고 하면 **나중에 끝난다** | `behavior: 'smooth'` 는 비동기다 |

- ★ **이 주제의 함정은 전부 「누가 굴러갔나」에 있다.** 내가 부른 요소가 굴러간다는 보장이 없다.
- ★ **읽는 쪽은 [09번 주제](../09-element-geometry/2-summary.md)다.** 여기는 **쓰는 쪽**이고, 쓰는 쪽에는 **조용히 무시되는 자리**가 여럿 있다.

```text
   한 번의 scrollIntoView() 가 건드리는 것

   문서(scrollingElement) ───────────┐
     └ #outer (overflow: auto) ──────┤  ★ 스크롤 컨테이너를 만날 때마다
         └ #mid (overflow: visible)  │     전부 굴린다
             └ #inner (overflow:auto)┤
                 └ #t (목표)         ┘

   #mid 는 스크롤 컨테이너가 아니라 건너뛴다
```

## 이 주제가 답하려는 질문

1. **문서를 굴리는 것은 누구인가** — `documentElement` 인가 `body` 인가. 그리고 **왜 둘인가.**
2. **`scrollIntoView` 는 무엇을 얼마나 움직이나** — 그리고 **누가 그 양을 정하나.**
3. **스크롤 컨테이너를 스크립트로 어떻게 찾나** — `overflow` 만 보면 되나.

## 이 갈래의 관측 창 — ★ 창 4 는 「조상 전수 스캔」

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom             스크립트가 다 돈 뒤의 트리를 글자로
                               ★ 부적용 — 스크롤 오프셋은 트리에 자국을 안 남긴다
  창 2  노드 단위 프로브        부르기 전 / 부른 뒤의 scrollTop 을 한 줄로
  창 3  두 번 읽기              대입하고 되읽는다 ([CSS 23번]의 판정법을 물려받는다)
  ★ 창 4 (이 주제 고유)  조상 전수 스캔 — 한 번 부르고 조상 '전부' 의 오프셋을 찍는다
        무엇을 답하나:  '누가 굴러갔나'
        왜 필요한가:    내가 부른 요소가 굴러간다는 보장이 없다.
                        한 요소만 보면 '안 굴렀다' 와 '바깥이 대신 굴렀다' 가 구분되지 않는다.
                        ★ 그리고 scrollIntoView 는 한 번에 여럿을 굴린다 — 하나만 봐서는 절반만 본다.
  ★ 못 재는 창  behavior: 'smooth' 의 진행과 도착
        프레임이 이 도구로 통제되지 않는다. (9) 에서 수치로 보인다
```

- ★ **창 ③ 은 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)가 이미 쓴 판정법**이다 — `scrollTop = 200` 을 대입하고 되읽어 값이 남으면 스크롤 컨테이너. 여기서는 그것을 **조상 전체로 넓힌 것**이 창 ④ 다.

## 동작 방식

### (1) 문서를 굴리는 것은 누구인가

**언제 쓰나** — 페이지 전체를 굴릴 때. **`body` 와 `documentElement` 중 어느 쪽인지부터.**

**던진 것** — 아래 (10)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-11-doc.html -->
<!doctype html>
<meta charset="utf-8">
<title>11-doc</title>
<style>body { margin: 0 } #big { width: 3000px; height: 3000px }</style>
<div id="big">넓고 긴 내용</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [34, 12, 26, 14][i])).join('').replace(/ +$/, ''));
const 이름 = e => e === document.documentElement ? 'documentElement' : e === document.body ? 'body' : String(e);

O.push('문서를 굴리는 것은 누구인가 — 표준 모드');
O.push('  document.compatMode      = ' + document.compatMode);
O.push('  document.scrollingElement = ' + 이름(document.scrollingElement));
O.push('');
row('무엇을 했나', 'scrollY', 'documentElement.scrollTop', 'body.scrollTop');
const 찍기 = label => row(label, scrollY, document.documentElement.scrollTop, document.body.scrollTop);
찍기('초기');
scrollTo(0, 300);                       찍기('window.scrollTo(0, 300)');
document.documentElement.scrollTop = 100; 찍기('documentElement.scrollTop = 100');
document.body.scrollTop = 700;          찍기('body.scrollTop = 700');
O.push('');
O.push('★ 표준 모드에서 body.scrollTop 에 쓰는 것은 아무 일도 안 한다 — 예외도 없다.');
O.push('');

O.push('위치 복원 — history.scrollRestoration');
O.push('  기본값 = ' + history.scrollRestoration);
history.scrollRestoration = 'manual';
O.push("  'manual' 로 바꾼 뒤 = " + history.scrollRestoration);
let 예외 = '예외 없음';
try { history.scrollRestoration = 'zzz'; } catch (e) { 예외 = '예외 ' + e.name; }
O.push("  'zzz' 를 대입하면 = " + 예외 + ' · 되읽으면 ' + history.scrollRestoration + ' (열거값이라 조용히 무시된다)');
history.scrollRestoration = 'auto';
O.push("  'auto' 로 되돌린 뒤 = " + history.scrollRestoration);
O.push('  ★ 실제 복원이 일어나는 것은 뒤로 가기·새로 고침 때다 — 이 문서는 그 순간을 관측하지 못했다(못 잰 것).');

document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-doc.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,11p'
문서를 굴리는 것은 누구인가 — 표준 모드
  document.compatMode      = CSS1Compat
  document.scrollingElement = documentElement

무엇을 했나                       scrollY     documentElement.scrollTop body.scrollTop
초기                              0           0                         0
window.scrollTo(0, 300)           300         300                       0
documentElement.scrollTop = 100   100         100                       0
body.scrollTop = 700              100         100                       0

★ 표준 모드에서 body.scrollTop 에 쓰는 것은 아무 일도 안 한다 — 예외도 없다.
(exit 0)
```

- **표준 모드에서는 `documentElement`(`<html>`)가 문서를 굴린다.** `scrollTo` 로 굴리면 **`documentElement.scrollTop` 에 값이 들어가고 `body.scrollTop` 은 0** 이다.
- ★ **`body.scrollTop = 700` 은 아무 일도 안 한다** — 예외도 경고도 없고 되읽으면 0 이다. **「안 굴러갔다」는 되읽어야만 안다.**
- **`document.scrollingElement` 가 그 답을 직접 준다.** 모드를 따지지 말고 이것을 쓰면 된다.

**doctype 을 지우면 뒤집힌다.**

```html
<!-- wa09b-11-quirks.html -->
<meta charset="utf-8">
<title>11-quirks</title>
<style>body { margin: 0 } #big { width: 3000px; height: 3000px }</style>
<div id="big">doctype 을 뺀 같은 문서</div>
<script>
const O = [];
const 이름 = e => e === document.documentElement ? 'documentElement' : e === document.body ? 'body' : String(e);
O.push('doctype 을 지우면 — 호환 모드');
O.push('  document.compatMode       = ' + document.compatMode);
O.push('  document.scrollingElement = ' + 이름(document.scrollingElement));
scrollTo(0, 300);
O.push('  window.scrollTo(0, 300) 뒤   scrollY=' + scrollY
     + '  documentElement.scrollTop=' + document.documentElement.scrollTop
     + '  body.scrollTop=' + document.body.scrollTop);
document.documentElement.scrollTop = 100;
O.push('  documentElement.scrollTop=100 뒤  scrollY=' + scrollY + '  (아무 일도 안 일어난다)');
document.body.scrollTop = 700;
O.push('  body.scrollTop=700 뒤             scrollY=' + scrollY + '  (이쪽이 문서를 굴린다)');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-quirks.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}'
doctype 을 지우면 — 호환 모드
  document.compatMode       = BackCompat
  document.scrollingElement = body
  window.scrollTo(0, 300) 뒤   scrollY=300  documentElement.scrollTop=0  body.scrollTop=300
  documentElement.scrollTop=100 뒤  scrollY=300  (아무 일도 안 일어난다)
  body.scrollTop=700 뒤             scrollY=700  (이쪽이 문서를 굴린다)
(exit 0)
```

- **호환 모드에서는 `body` 가 굴린다.** `documentElement.scrollTop` 쪽이 조용히 무시된다 — **정확히 반대**다.
- ★ **그래서 옛 코드에 `document.body.scrollTop` 과 `document.documentElement.scrollTop` 을 `||` 로 이어 놓은 관용구**가 있는 것이다. 오늘은 **`document.scrollingElement` 하나**면 된다.
- **`window.scrollY` 는 두 모드에서 똑같이 동작한다** — 모드에 안 휘둘리는 유일한 읽기다.

비용 — 스크롤 오프셋을 읽는 것은 **레이아웃을 강제한다**([목록의 **10번 주제**](../10-layout-thrashing/) 실측에서 `window.scrollY` 도 방아쇠였다).

### (2) 같은 일을 시키는 표면이 넷이다

**언제 쓰나** — 굴릴 때. **인자 순서에서 제일 많이 틀린다.**

**던진 것** — 아래 (3)·(4)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-11-api.html -->
<!doctype html>
<meta charset="utf-8">
<title>11-api</title>
<style>
  body { margin: 0; font: 14px monospace }
  #sc { width: 300px; height: 200px; overflow: auto; border: 5px solid rgb(51, 51, 51) }
  #in { width: 900px; height: 800px }
  #tail { height: 2000px }
</style>
<div id="sc"><div id="in">스크롤 상자 안의 내용</div></div>
<div id="tail">문서 아래</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [40, 16, 16][i])).join('').replace(/ +$/, ''));
const sc = document.getElementById('sc');

O.push('같은 일을 시키는 네 가지 표면 — 대상은 #sc 하나');
row('무엇을 불렀나', 'sc.scrollTop', 'sc.scrollLeft');
sc.scrollTop = 0; sc.scrollLeft = 0;
row('(초기)', sc.scrollTop, sc.scrollLeft);
sc.scrollTop = 120;               row('sc.scrollTop = 120', sc.scrollTop, sc.scrollLeft);
sc.scrollTo(30, 60);              row('sc.scrollTo(30, 60)  ← x, y 순서', sc.scrollTop, sc.scrollLeft);
sc.scrollTo({ top: 200 });        row('sc.scrollTo({top: 200})', sc.scrollTop, sc.scrollLeft);
sc.scrollBy(10, 25);              row('sc.scrollBy(10, 25)', sc.scrollTop, sc.scrollLeft);
sc.scrollBy({ top: -25 });        row('sc.scrollBy({top: -25})', sc.scrollTop, sc.scrollLeft);
sc.scrollTo({ top: 300, left: 0 }); row('sc.scrollTo({top:300, left:0})', sc.scrollTop, sc.scrollLeft);
O.push('');
O.push('★ 두 인자 꼴은 (x, y) 이고 객체 꼴은 {left, top} 이다 — 순서가 뒤집혀 보인다.');
O.push('★ 객체 꼴에서 빠뜨린 축은 그대로 둔다(scrollTo 여도 그 축은 안 움직인다).');
O.push('');

O.push('범위 밖 값을 넣으면 — 잘린다, 예외가 아니다');
row('무엇을 넣었나', 'sc.scrollTop', '판정');
const 상한 = sc.scrollHeight - sc.clientHeight;
sc.scrollTop = -50;      row('-50', sc.scrollTop, '0 으로 잘림');
sc.scrollTop = 999999;   row('999999', sc.scrollTop, '상한 ' + 상한 + ' 으로 잘림');
O.push('  상한 = scrollHeight(' + sc.scrollHeight + ') - clientHeight(' + sc.clientHeight + ') = ' + 상한);
sc.scrollTop = 'abc';    row("'abc' (문자열)", sc.scrollTop, '0 으로 읽힌다');
sc.scrollTop = 100.4;    row('100.4 (소수)', sc.scrollTop, '되읽으면 정수다');
sc.scrollTop = 100.7;    row('100.7 (소수)', sc.scrollTop, '되읽으면 정수다');
O.push('  scrollTop 의 타입은 ' + typeof sc.scrollTop + ' 인데 이 판에서는 장치 픽셀로 맞춰져 돌아온다(dpr = ' + devicePixelRatio + ').');
O.push('');

O.push('스크롤 컨테이너가 아닌 요소에 쓰면 — 조용히 0 이다');
const 안굴러 = document.getElementById('in');
안굴러.scrollTop = 100;
O.push('  #in.scrollTop = 100 을 쓰고 되읽으면 ' + 안굴러.scrollTop
     + '   (overflow=' + getComputedStyle(안굴러).overflowY + ' · scrollHeight ' + 안굴러.scrollHeight
     + ' · clientHeight ' + 안굴러.clientHeight + ')');
O.push('  예외도 경고도 없다. 「안 굴러갔다」는 되읽어야만 안다.');
O.push('');

O.push('창을 굴리는 표면');
scrollTo(0, 0);
scrollTo(0, 400);        O.push('  window.scrollTo(0, 400)      scrollY = ' + scrollY);
scrollBy(0, 50);         O.push('  window.scrollBy(0, 50)       scrollY = ' + scrollY);
scrollTo({ top: 10 });   O.push('  window.scrollTo({top: 10})   scrollY = ' + scrollY);
scrollTo(0, 999999);     O.push('  window.scrollTo(0, 999999)   scrollY = ' + scrollY
     + '   (문서 높이 ' + document.documentElement.scrollHeight + ' - 뷰포트 ' + document.documentElement.clientHeight + ')');
O.push('  window.scrollY 와 document.scrollingElement.scrollTop 이 같은가: '
     + (scrollY === document.scrollingElement.scrollTop));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-api.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
같은 일을 시키는 네 가지 표면 — 대상은 #sc 하나
무엇을 불렀나                           sc.scrollTop    sc.scrollLeft
(초기)                                  0               0
sc.scrollTop = 120                      120             0
sc.scrollTo(30, 60)  ← x, y 순서       60              30
sc.scrollTo({top: 200})                 200             30
sc.scrollBy(10, 25)                     225             40
sc.scrollBy({top: -25})                 200             40
sc.scrollTo({top:300, left:0})          300             0

★ 두 인자 꼴은 (x, y) 이고 객체 꼴은 {left, top} 이다 — 순서가 뒤집혀 보인다.
★ 객체 꼴에서 빠뜨린 축은 그대로 둔다(scrollTo 여도 그 축은 안 움직인다).
(exit 0)
```

- **`scrollTop = n` 은 한 축만**, **`scrollTo`/`scrollBy` 는 두 축을** 건드린다.
- ★ **두 인자 꼴은 `(x, y)` 이고 객체 꼴은 `{left, top}`** 이다. `scrollTo(30, 60)` 은 **가로 30 · 세로 60** 이다 — 위 표에서 `scrollTop` 이 60, `scrollLeft` 가 30 이 된 줄이 그것이다. **순서가 뒤집혀 보여서 여기서 틀린다.**
- ★ **객체 꼴에서 빠뜨린 축은 안 움직인다.** `scrollTo({top: 200})` 인데 `scrollLeft` 가 30 그대로다 — **이름이 `scrollTo` 여도 「절대 위치로 옮긴다」가 두 축 모두에 적용되지 않는다.**
- **`scrollBy` 는 현재 값에 더한다.** 음수를 주면 되감긴다.

```text
   인자 두 꼴의 축 순서가 다르다

   scrollTo(30, 60)         →  scrollLeft = 30 · scrollTop = 60     (x, y)
   scrollTo({top: 60})      →  scrollTop  = 60 · scrollLeft 그대로   (이름으로)
   scrollTo({left: 30})     →  scrollLeft = 30 · scrollTop  그대로

   ★ 두 인자 꼴에는 '그대로' 가 없다 — 둘 다 지정된다
```

### (3) 범위 밖 값을 넣으면 — 잘린다, 예외가 아니다

**언제 쓰나** — 계산한 값을 넣을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-api.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,26p'
범위 밖 값을 넣으면 — 잘린다, 예외가 아니다
무엇을 넣었나                           sc.scrollTop    판정
-50                                     0               0 으로 잘림
999999                                  615             상한 615 으로 잘림
  상한 = scrollHeight(800) - clientHeight(185) = 615
'abc' (문자열)                          0               0 으로 읽힌다
100.4 (소수)                            100             되읽으면 정수다
100.7 (소수)                            101             되읽으면 정수다
  scrollTop 의 타입은 number 인데 이 판에서는 장치 픽셀로 맞춰져 돌아온다(dpr = 1).

스크롤 컨테이너가 아닌 요소에 쓰면 — 조용히 0 이다
  #in.scrollTop = 100 을 쓰고 되읽으면 0   (overflow=visible · scrollHeight 800 · clientHeight 800)
  예외도 경고도 없다. 「안 굴러갔다」는 되읽어야만 안다.
(exit 0)
```

- **음수는 0 으로, 너무 큰 값은 상한으로 잘린다.** **예외가 없다.**
- **상한은 `scrollHeight − clientHeight`** 다. 이 상자에서는 `clientHeight` 가 **세로 200 에서 가로 스크롤바 15 를 뺀 185** 라 상한이 615 다.
- **문자열을 넣으면 `0`** 이다 — 숫자로 바꿀 수 없는 값은 0 으로 떨어진다. **오타가 「맨 위로 가기」가 된다.**
- **소수를 넣으면 되읽을 때 정수**다. 이 판은 `devicePixelRatio` 가 1 이라 **장치 픽셀에 맞춰진다** — **다른 배율에서는 소수가 남을 수 있다**(여기서 확인하지 않았다).
- ★ **스크롤 컨테이너가 아닌 요소에 쓰면 조용히 0** 이다. 예외도 경고도 없고, **되읽어야만 안 굴러간 것을 안다.**

```text
   쓰기의 네 가지 조용한 실패

   ① 범위 밖        →  잘린다        (예외 없음)
   ② 숫자가 아님    →  0             (예외 없음)
   ③ 컨테이너 아님  →  0             (예외 없음)
   ④ 모드 반대쪽    →  아무 일 없음   (예외 없음)

   ★ 전부 '되읽기' 로만 드러난다 — 이 주제의 창 ③ 이 그래서 필요하다
```

### (4) 창을 굴리는 표면

**언제 쓰나** — 페이지 전체를 굴릴 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-api.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '28,33p'
창을 굴리는 표면
  window.scrollTo(0, 400)      scrollY = 400
  window.scrollBy(0, 50)       scrollY = 450
  window.scrollTo({top: 10})   scrollY = 10
  window.scrollTo(0, 999999)   scrollY = 1497   (문서 높이 2210 - 뷰포트 713)
  window.scrollY 와 document.scrollingElement.scrollTop 이 같은가: true
(exit 0)
```

- **`window.scrollTo`/`scrollBy` 도 같은 규칙**이다 — 두 인자 꼴은 `(x, y)`, 객체 꼴은 이름으로.
- **창도 상한에서 잘린다** — 문서 높이에서 뷰포트 높이를 뺀 값이다. **뷰포트 높이가 창 크기에 달려 있으므로 이 수는 배너의 `--window-size` 에 묶여 있다.**
- **`window.scrollY` 와 `document.scrollingElement.scrollTop` 이 같은 값**이다. 둘은 같은 것을 두 창구로 본다.

### (5) ★ 창 ④ — 한 번 불렀는데 셋이 움직인다

**언제 쓰나** — `scrollIntoView` 를 부른 뒤 **화면이 예상과 다를 때.**

**던진 것** — 아래 (6)·(7)·(8)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-11-into.html -->
<!doctype html>
<meta charset="utf-8">
<title>11-into</title>
<style>
  body { margin: 0; font: 13px monospace }
  #head { height: 500px }
  #outer { height: 300px; overflow: auto; border: 2px solid rgb(51, 51, 51); margin-top: 40px }
  #mid { padding: 10px }
  #inner { height: 250px; overflow: auto; border: 2px solid rgb(136, 136, 136) }
  .fill { height: 600px }
  #t { height: 30px; background: rgb(204, 255, 204) }
  #tail { height: 2000px }
</style>
<div id="head">문서 위</div>
<div id="outer"><div id="mid"><div id="inner">
  <div class="fill">inner 채움 1</div><div id="t">목표</div><div class="fill">inner 채움 2</div>
</div><div class="fill">mid 채움</div></div></div>
<div id="tail">문서 아래</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [36, 10, 17, 17, 12][i])).join('').replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const t = $('t'), inner = $('inner'), outer = $('outer'), mid = $('mid');
const 되돌리기 = () => { scrollTo(0, 0); outer.scrollTop = 0; inner.scrollTop = 0; };

O.push('창 ④ — 무엇이 움직였는지 조상 전체를 훑는다');
row('무엇을 불렀나', 'scrollY', 'outer.scrollTop', 'inner.scrollTop', 't.rect.top');
const 찍기 = label => row(label, scrollY, outer.scrollTop, inner.scrollTop, t.getBoundingClientRect().top.toFixed(0));
찍기('(초기)');
t.scrollIntoView(); 찍기('t.scrollIntoView()');
O.push('  ★ 한 번 불렀는데 셋이 같이 움직였다 — 스크롤 컨테이너를 만날 때마다 굴린다.');
O.push('  ★ mid 는 스크롤 컨테이너가 아니라 안 움직였다: mid.scrollTop = ' + mid.scrollTop);
O.push('');

O.push('옵션이 정하는 것');
row('무엇을 불렀나', 'scrollY', 'outer.scrollTop', 'inner.scrollTop', 't.rect.top');
for (const opt of [true, false, { block: 'start' }, { block: 'center' }, { block: 'end' }, { block: 'nearest' }]) {
  되돌리기();
  t.scrollIntoView(opt);
  찍기('scrollIntoView(' + JSON.stringify(opt) + ')');
}
O.push('  ★ 인자 없음 = true = {block: "start"} · false = {block: "end"} 다.');
O.push('  ★ nearest 는 「이미 보이면 안 움직인다」 — 여기서는 아래에 있었으므로 end 와 같은 자리로 갔다.');
O.push('');

O.push('스크롤 컨테이너로 쳐 주는 overflow 는 무엇인가 — #inner 의 값만 바꿨다');
row('#inner 의 overflow', 'scrollY', 'outer.scrollTop', 'inner.scrollTop', '굴렀나');
for (const v of ['visible', 'hidden', 'clip', 'auto', 'scroll']) {
  되돌리기();
  inner.style.overflow = v;
  t.scrollIntoView();
  row('overflow: ' + v, scrollY, outer.scrollTop, inner.scrollTop, inner.scrollTop > 0 ? '굴렀다' : '안 굴렀다');
}
inner.style.overflow = 'auto';
O.push('  ★ hidden 도 스크롤 컨테이너다 — 스크롤바가 없을 뿐이다. clip 은 아니다.');
O.push('  ★ inner 가 안 굴러가면 그만큼을 바깥이 대신 굴린다(outer.scrollTop 이 커진다).');
O.push('');

O.push('그래서 스크롤 컨테이너를 스크립트로 찾으려면');
되돌리기();
const 굴릴수있나 = el => {
  const oy = getComputedStyle(el).overflowY;
  return (oy === 'auto' || oy === 'scroll' || oy === 'hidden') && el.scrollHeight > el.clientHeight;
};
let e = t.parentElement; const 사슬 = [];
while (e) { 사슬.push((e.id ? '#' + e.id : e.tagName) + '(' + getComputedStyle(e).overflowY + (굴릴수있나(e) ? ' ← 스크롤러' : '') + ')'); e = e.parentElement; }
O.push('  ' + 사슬.join('  <  '));
O.push('  ★ 사슬 끝의 HTML 은 overflowY 가 visible 인데 문서는 굴러간다(scrollY 를 ' + (scrollTo(0, 120), scrollY) + ' 로 만들 수 있다).');
O.push('    위 규칙만으로는 루트를 놓친다 — 마지막 한 칸은 document.scrollingElement 로 따로 잡아야 한다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
창 ④ — 무엇이 움직였는지 조상 전체를 훑는다
무엇을 불렀나                       scrollY   outer.scrollTop  inner.scrollTop  t.rect.top
(초기)                              0         0                0                1154
t.scrollIntoView()                  542       12               600              0
  ★ 한 번 불렀는데 셋이 같이 움직였다 — 스크롤 컨테이너를 만날 때마다 굴린다.
  ★ mid 는 스크롤 컨테이너가 아니라 안 움직였다: mid.scrollTop = 0
(exit 0)
```

- **한 번 불렀는데 `scrollY`·`outer`·`inner` 셋이 같이 움직였다.** `scrollIntoView` 는 **목표에서 위로 올라가며 스크롤 컨테이너를 만날 때마다 굴린다.**
- **`#mid` 는 안 움직였다** — 스크롤 컨테이너가 아니기 때문이다. **건너뛴다.**
- ★ **그래서 한 요소만 보면 절반만 본다.** 「`inner.scrollTop` 이 안 움직였네」로는 **안 굴러간 것인지 바깥이 대신 굴러간 것인지** 구분이 안 된다 — (7)이 그 차이를 보여 준다.

### (6) 옵션이 정하는 것

**언제 쓰나** — 목표를 화면 어디에 놓을지 정할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,17p'
옵션이 정하는 것
무엇을 불렀나                       scrollY   outer.scrollTop  inner.scrollTop  t.rect.top
scrollIntoView(true)                542       12               600              0
scrollIntoView(false)               91        0                380              683
scrollIntoView({"block":"start"})   542       12               600              0
scrollIntoView({"block":"center"})  323       0                490              341
scrollIntoView({"block":"end"})     91        0                380              683
scrollIntoView({"block":"nearest"}) 91        0                380              683
  ★ 인자 없음 = true = {block: "start"} · false = {block: "end"} 다.
  ★ nearest 는 「이미 보이면 안 움직인다」 — 여기서는 아래에 있었으므로 end 와 같은 자리로 갔다.
(exit 0)
```

- **인자 없음 = `true` = `{block: 'start'}`** 이고 **`false` = `{block: 'end'}`** 다. 불리언은 옛 형태이고 **옵션 객체가 같은 일을 더 넓게** 한다.
- **`center` 는 가운데**로 놓는다 — `rect.top` 이 뷰포트 한가운데 언저리다.
- ★ **`nearest` 는 「이미 보이면 안 움직인다」다.** 여기서는 목표가 아래에 있었으므로 **`end` 와 같은 자리**로 갔다 — **그래서 이 출력만 보면 둘을 구분할 수 없다.** 구분하려면 **이미 보이는 요소**로 다시 던져야 한다(아래 demo 가 그 자리다).
- **`inline` 축도 같은 규칙**이다(`start`/`center`/`end`/`nearest`). **이 문서는 세로 축만 던졌다** — 가로는 확인하지 않았다.

### (7) 어떤 `overflow` 가 굴러가나

**언제 쓰나** — 「왜 저 상자가 안 굴러가지」일 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '19,27p'
스크롤 컨테이너로 쳐 주는 overflow 는 무엇인가 — #inner 의 값만 바꿨다
#inner 의 overflow                  scrollY   outer.scrollTop  inner.scrollTop  굴렀나
overflow: visible                   542       612              0                안 굴렀다
overflow: hidden                    542       12               600              굴렀다
overflow: clip                      580       574              0                안 굴렀다
overflow: auto                      542       12               600              굴렀다
overflow: scroll                    542       12               600              굴렀다
  ★ hidden 도 스크롤 컨테이너다 — 스크롤바가 없을 뿐이다. clip 은 아니다.
  ★ inner 가 안 굴러가면 그만큼을 바깥이 대신 굴린다(outer.scrollTop 이 커진다).
(exit 0)
```

- **`auto`·`scroll`·`hidden` 은 굴러가고 `visible`·`clip` 은 안 굴러간다.**
- ★ **`hidden` 이 스크롤 컨테이너라는 것**이 핵심이다 — **스크롤바가 없을 뿐 굴릴 수 있다.** `clip` 은 아니다. **이 구분의 정본은 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)이고,** 여기서는 **`scrollIntoView` 가 그 판정을 그대로 따른다**는 것만 확인했다.
- ★ **안 굴러가는 값일 때 바깥이 대신 굴러간다** — `outer.scrollTop` 이 크게 뛴다. **총 이동량은 비슷한데 누가 움직였는지가 다르다.** 창 ④ 없이는 못 본다.
- **`clip` 줄만 `scrollY` 가 다르다** — `clip` 은 스크롤 컨테이너가 아니어서 바깥이 더 멀리 굴러야 했다.

### (8) 스크롤 컨테이너를 스크립트로 찾으려면

**언제 쓰나** — 「이 요소를 담고 있는 스크롤러가 누구인가」를 코드로 구할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-into.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '29,32p'
그래서 스크롤 컨테이너를 스크립트로 찾으려면
  #inner(auto ← 스크롤러)  <  #mid(visible)  <  #outer(auto ← 스크롤러)  <  BODY(visible)  <  HTML(visible)
  ★ 사슬 끝의 HTML 은 overflowY 가 visible 인데 문서는 굴러간다(scrollY 를 120 로 만들 수 있다).
    위 규칙만으로는 루트를 놓친다 — 마지막 한 칸은 document.scrollingElement 로 따로 잡아야 한다.
(exit 0)
```

- **규칙은 두 조건의 곱**이다 — **`overflow` 가 `auto`·`scroll`·`hidden` 중 하나이고**, **내용이 실제로 넘칠 때**(`scrollHeight > clientHeight`). 둘 중 하나만으로는 안 된다.
- ★ **그 규칙만으로는 루트를 놓친다.** `<html>` 의 `overflowY` 는 **`visible`** 인데 **문서는 굴러간다.** 뷰포트 스크롤은 `overflow` 로 만들어진 것이 아니기 때문이다.
- **그래서 사슬의 마지막 한 칸은 `document.scrollingElement` 로 따로 잡는다.**

```js
// 스크롤 컨테이너 찾기 — 두 조건 + 루트 예외
function 스크롤러찾기(el) {
  for (let e = el.parentElement; e; e = e.parentElement) {
    const oy = getComputedStyle(e).overflowY;
    if ((oy === 'auto' || oy === 'scroll' || oy === 'hidden') && e.scrollHeight > e.clientHeight) return e;
  }
  return document.scrollingElement;   // ★ 루트는 overflow 로 안 잡힌다
}
```

비용 — 이 함수는 **조상마다 `getComputedStyle` 과 `scrollHeight` 를 읽는다.** [목록의 **10번 주제**](../10-layout-thrashing/)의 방아쇠를 **조상 수만큼** 당긴다 — **루프 안에서 부르지 마라.**

### (9) `behavior: 'smooth'` — 비동기인 것까지만 관측했다

**언제 쓰나** — 부드럽게 굴리고 **그 뒤에 무언가를 할 때.**

```html
<!-- wa09b-11-smooth.html -->
<!doctype html>
<meta charset="utf-8">
<title>11-smooth</title>
<style>
  body { margin: 0; font: 14px monospace }
  #sc { width: 300px; height: 200px; overflow: auto; border: 5px solid rgb(51, 51, 51) }
  #in { height: 2000px }
  #tail { height: 4000px }
  #css { scroll-behavior: smooth; width: 300px; height: 200px; overflow: auto; border: 5px solid rgb(136, 136, 136) }
  #css > div { height: 2000px }
</style>
<div id="sc"><div id="in">내용</div></div>
<div id="css"><div>scroll-behavior: smooth 를 CSS 로 준 상자</div></div>
<div id="tail">문서 아래</div>
<script>
const O = [];
const sc = document.getElementById('sc'), css = document.getElementById('css');

O.push('behavior 가 무엇을 바꾸나 — 부른 직후 같은 tick 에서 되읽는다');
sc.scrollTop = 0;
sc.scrollTo({ top: 500, behavior: 'auto' });
O.push("  scrollTo({top: 500, behavior: 'auto'})   직후 sc.scrollTop = " + sc.scrollTop);
sc.scrollTop = 0;
sc.scrollTo({ top: 500 });
O.push('  scrollTo({top: 500})  (기본값)          직후 sc.scrollTop = ' + sc.scrollTop);
sc.scrollTop = 0;
sc.scrollTo({ top: 500, behavior: 'smooth' });
O.push("  scrollTo({top: 500, behavior: 'smooth'}) 직후 sc.scrollTop = " + sc.scrollTop + '   ★ 안 움직였다');
O.push('');
O.push('CSS 로 scroll-behavior: smooth 를 준 상자는 scrollTop 대입도 비동기가 되나');
css.scrollTop = 0;
css.scrollTop = 500;
O.push('  css.scrollTop = 500 직후 되읽으면 ' + css.scrollTop + '   (getComputedStyle = '
     + getComputedStyle(css).scrollBehavior + ')');
css.scrollTop = 0;
css.scrollTo({ top: 500 });
O.push('  css.scrollTo({top: 500}) 직후 되읽으면 ' + css.scrollTop + '   ← 기본값이 CSS 를 따라간다');
css.scrollTo({ top: 500, behavior: 'instant' });
O.push("  css.scrollTo({top: 500, behavior: 'instant'}) 직후 " + css.scrollTop + '   ← CSS 를 눌러 덮는다');
O.push('');

let 진행 = [];
const 재기 = tag => 진행.push(tag + ' ' + sc.scrollTop);
sc.scrollTop = 0;
sc.scrollTo({ top: 500, behavior: 'smooth' });
재기('부른 직후');
const t0 = performance.now();
while (performance.now() - t0 < 200) { /* 동기 루프로 200ms 를 태운다 */ }
재기('동기 루프 200ms 뒤');
setTimeout(() => {
  재기('setTimeout 0 뒤');
  setTimeout(() => {
    재기('setTimeout 0 을 한 겹 더');
    O.push('smooth 가 어디까지 갔나 — ' + 진행.join('  ·  '));
    O.push('  ★ 동기 루프로는 못 따라간다(스크립트가 도는 동안 애니메이션이 진행하지 않는다).');
    O.push('  ★ --dump-dom 은 load + setTimeout(…, 0) 두 겹까지만 기다린다 — 세 겹을 걸면 출력이 통째로 사라진다.');
    O.push('  ★ 그래서 「도착한 순간」은 이 도구로 못 잰다. 관측한 것은 「부른 직후에는 안 움직인다」까지다.');
    document.body.appendChild(Object.assign(document.createElement('script'),
      {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
  }, 0);
}, 0);
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-smooth.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
behavior 가 무엇을 바꾸나 — 부른 직후 같은 tick 에서 되읽는다
  scrollTo({top: 500, behavior: 'auto'})   직후 sc.scrollTop = 500
  scrollTo({top: 500})  (기본값)          직후 sc.scrollTop = 500
  scrollTo({top: 500, behavior: 'smooth'}) 직후 sc.scrollTop = 0   ★ 안 움직였다

CSS 로 scroll-behavior: smooth 를 준 상자는 scrollTop 대입도 비동기가 되나
  css.scrollTop = 500 직후 되읽으면 0   (getComputedStyle = smooth)
  css.scrollTo({top: 500}) 직후 되읽으면 0   ← 기본값이 CSS 를 따라간다
  css.scrollTo({top: 500, behavior: 'instant'}) 직후 500   ← CSS 를 눌러 덮는다
(exit 0)
```

- **`auto`(기본)는 동기다** — 부른 직후 되읽으면 **이미 도착**해 있다.
- **`smooth` 는 비동기다** — 부른 직후 되읽으면 **아직 0** 이다. **한 tick 안에서는 아무 일도 일어나지 않는다.**
- ★ **CSS 의 `scroll-behavior: smooth` 가 `scrollTop` 대입까지 비동기로 만든다.** 프로퍼티에 쓰는 코드에는 아무 표시가 없는데 **CSS 한 줄이 그 코드의 동기성을 바꾼다.**
- **`behavior: 'instant'` 는 그 CSS 를 눌러 덮는다** — 스크립트 쪽에서 강제로 동기로 되돌리는 유일한 길이다.

**도착은 못 잤다.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-smooth.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '11,14p'
smooth 가 어디까지 갔나 — 부른 직후 0  ·  동기 루프 200ms 뒤 0  ·  setTimeout 0 뒤 0  ·  setTimeout 0 을 한 겹 더 0
  ★ 동기 루프로는 못 따라간다(스크립트가 도는 동안 애니메이션이 진행하지 않는다).
  ★ --dump-dom 은 load + setTimeout(…, 0) 두 겹까지만 기다린다 — 세 겹을 걸면 출력이 통째로 사라진다.
  ★ 그래서 「도착한 순간」은 이 도구로 못 잰다. 관측한 것은 「부른 직후에는 안 움직인다」까지다.
(exit 0)
```

- **동기 루프로 200ms 를 태워도 값이 0 그대로**다 — 스크립트가 도는 동안 **애니메이션이 진행하지 않는다**(같은 스레드다).
- **`--dump-dom` 은 `load` 뒤의 `setTimeout(…, 0)` 을 두 겹까지만 기다린다** — 세 겹을 걸면 **출력이 통째로 사라진다**(직접 확인했다). 그래서 **도착 시각도 중간 값도 못 봤다.**
- ★ **이것은 「안 돌려 본 것」이 아니라 「못 잰 것」이다.** 「smooth 가 몇 ms 걸린다」를 이 문서는 **주장하지 않는다.** 재려면 CDP 로 프레임을 몰아야 한다.
- **그래도 실무 결론은 관측한 것만으로 선다** — **`smooth` 뒤에 좌표를 읽으면 옛 값이다.** 도착을 기다리려면 `scrollend` 이벤트([목록의 **16번 주제**](../16-event-propagation-phases/) 이후의 이벤트 갈래)를 써야 한다. **이 문서는 그 이벤트도 못 관측했다.**

### (10) 위치 복원 — `history.scrollRestoration`

**언제 쓰나** — 뒤로 가기에서 위치가 튈 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-11-doc.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '13,18p'
위치 복원 — history.scrollRestoration
  기본값 = auto
  'manual' 로 바꾼 뒤 = manual
  'zzz' 를 대입하면 = 예외 없음 · 되읽으면 manual (열거값이라 조용히 무시된다)
  'auto' 로 되돌린 뒤 = auto
  ★ 실제 복원이 일어나는 것은 뒤로 가기·새로 고침 때다 — 이 문서는 그 순간을 관측하지 못했다(못 잰 것).
(exit 0)
```

- **기본값은 `'auto'`** 다 — 브라우저가 알아서 복원한다.
- **`'manual'` 로 바꾸면 브라우저가 복원을 안 한다** — 내가 직접 복원해야 한다.
- ★ **잘못된 값을 넣어도 예외가 없다.** `'zzz'` 를 대입하면 **조용히 무시**되고 옛 값이 남는다 — **열거된 값만 받는 속성**이라서다. [06번 주제](../06-attribute-vs-property/2-summary.md)의 「조용히 버려짐」과 같은 모양이다.
- ★ **실제 복원이 일어나는 순간은 못 봤다** — 뒤로 가기·새로 고침이 필요한데 `--dump-dom` 은 한 번 여는 것뿐이다. **「이 값이 무엇인가」까지만 관측했다.**
- **복원이 튀는 진짜 원인은 경합**이다 — 브라우저가 복원한 뒤에 이미지가 로드되어 **문서 높이가 늘면** 그 위치가 엉뚱해진다. **`manual` 로 끄고, 내용이 자리 잡은 뒤에 직접 복원하는 것**이 처방이다. (**이 문서는 그 경합을 재현하지 못했다.**)

### (11) 그래서 어떻게 쓰나

**언제 쓰나** — 목록에서 항목 하나를 보여 줄 때.

```html demo
<div id="d11box">
  <div class="d11it">1</div><div class="d11it">2</div><div class="d11it">3</div>
  <div class="d11it" id="d11t">4 — 목표</div><div class="d11it">5</div><div class="d11it">6</div>
</div>
<button id="d11a">scrollTo(0, 100)</button>
<button id="d11b">scrollBy(0, 40)</button>
<button id="d11c">목표를 start 로</button>
<button id="d11d">목표를 nearest 로</button>
<div id="d11out"></div>
<style>
  #d11box { height: 120px; overflow: auto; border: 3px solid #334155; width: 220px; }
  .d11it { height: 60px; border-bottom: 1px solid #cbd5e1; font: 14px monospace; }
  #d11t { background: #a7f3d0; }
  #d11out { font-family: monospace; white-space: pre; background: #0f172a; color: #e2e8f0; padding: 8px; margin-top: 6px; }
</style>
<script>
  const 상자 = document.getElementById('d11box'), 목표 = document.getElementById('d11t');
  const 보이기 = 무엇 => document.getElementById('d11out').textContent =
    '방금 한 것    = ' + 무엇 +
    '\n상자.scrollTop = ' + 상자.scrollTop + '   (상한 ' + (상자.scrollHeight - 상자.clientHeight) + ')' +
    '\n목표.rect.top  = ' + 목표.getBoundingClientRect().top.toFixed(2) +
    '\n창.scrollY     = ' + Math.round(window.scrollY) + '   ← 창은 안 움직인다';
  document.getElementById('d11a').onclick = () => { 상자.scrollTo(0, 100); 보이기('scrollTo(0, 100)'); };
  document.getElementById('d11b').onclick = () => { 상자.scrollBy(0, 40); 보이기('scrollBy(0, 40)'); };
  document.getElementById('d11c').onclick = () => { 목표.scrollIntoView({ block: 'start' }); 보이기("scrollIntoView({block:'start'})"); };
  document.getElementById('d11d').onclick = () => { 목표.scrollIntoView({ block: 'nearest' }); 보이기("scrollIntoView({block:'nearest'})"); };
  보이기('(아직 아무것도)');
</script>
```

> **보이는 것** — 220px 짜리 상자 안에서 여섯 줄이 굴러간다. 첫 버튼은 **한 번에 100 으로 점프**하고, 둘째 버튼은 **누를 때마다 40 씩 더** 내려간다(괄호 안의 상한에서 멈춘다).\
> 셋째 버튼은 초록 줄(목표)을 **상자 맨 위에** 붙인다. 넷째 버튼은 **목표가 이미 보이면 아무것도 안 하고**, 안 보일 때만 **최소한으로** 움직인다 — 셋째를 누른 뒤 넷째를 누르면 **숫자가 하나도 안 변한다.**\
> 넷째 줄의 `창.scrollY` 는 **네 버튼 어느 것에도 안 변한다** — 목표가 상자 안에서 이미 보이게 되므로 바깥까지 굴릴 일이 없다.\
> **바꿔 볼 것** — `#d11box` 의 `overflow` 를 `hidden` 으로 바꾸면 **스크롤바가 사라지는데 버튼은 그대로 동작한다**(`hidden` 도 스크롤 컨테이너다) · `clip` 으로 바꾸면 **세 버튼이 전부 0 에서 안 움직인다** · `#d11box` 에 `scroll-behavior: smooth` 를 주면 **숫자가 옛 값으로 찍힌다**(비동기가 된다)

*(Chrome 151 headless 실측 — `--window-size=1000,800`: 상한 246 · `scrollTo(0, 100)` 뒤 100 · 거기서 `scrollBy(0, 40)` 뒤 140 · `block: 'start'` 뒤 183 · 이어서 `block: 'nearest'` 를 눌러도 183 그대로 · `목표.rect.top` 은 194 → 94 → 54 → 11 → 11 · `창.scrollY` 는 네 번 다 0. `overflow: clip` 으로 바꾼 사본에서는 네 버튼을 다 누른 뒤에도 `scrollTop` 이 0 이고 `rect.top` 이 194 그대로였다.)*

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
// 요소를 굴린다
el.scrollTop = 120;   el.scrollLeft = 30;         // 한 축씩 · 잘린다
el.scrollTo(30, 60);                              // (x, y)
el.scrollTo({ top: 60, left: 30, behavior: 'smooth' });
el.scrollBy(0, 40);   el.scrollBy({ top: -40 });  // 상대

// 창을 굴린다
window.scrollTo(0, 400);  window.scrollBy(0, 50);
window.scrollX  window.scrollY
document.scrollingElement                         // ★ 모드를 안 따져도 된다

// 요소가 보이게 굴린다 (조상 스크롤러를 전부 굴린다)
el.scrollIntoView();                              // = true = {block: 'start'}
el.scrollIntoView(false);                         // = {block: 'end'}
el.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'smooth' });

// 위치 복원
history.scrollRestoration;                        // 'auto' | 'manual'
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// 1. body 와 documentElement 를 직접 고른다 — 모드에 따라 한쪽이 죽는다
document.body.scrollTop = 0;                       // 표준 모드에서는 무시된다
document.scrollingElement.scrollTop = 0;           // 이것이 맞다

// 2. 두 인자 꼴의 순서를 세로부터 쓴다
el.scrollTo(100, 0);                               // 가로로 100 간다
el.scrollTo({ top: 100 });                         // 이것이 세로다

// 3. scrollTo 가 두 축을 다 옮길 거라 믿는다
el.scrollTo({ top: 0 });                           // scrollLeft 는 그대로다
el.scrollTo({ top: 0, left: 0 });                  // 둘 다 되돌리려면 이렇게

// 4. smooth 를 부르고 바로 읽는다 — 옛 값이다
el.scrollTo({ top: 500, behavior: 'smooth' });
console.log(el.scrollTop);                         // 0 이다

// 5. 범위 밖 값을 예외로 잡으려 한다 — 예외가 없다
try { el.scrollTop = 99999; } catch (e) { }        // 조용히 상한으로 잘린다
el.scrollTop === el.scrollHeight - el.clientHeight; // 끝까지 갔는지는 이렇게 본다

// 6. overflow 만 보고 스크롤러를 찾는다 — 루트를 놓친다
getComputedStyle(e).overflowY !== 'visible';        // <html> 은 visible 인데 굴러간다
document.scrollingElement;                          // 사슬의 마지막 칸

// 7. scrollIntoView 가 이 요소만 굴릴 거라 믿는다
el.scrollIntoView();                                // 조상 스크롤러를 전부 굴린다
```

### 어디서 헷갈리나

- **`scrollTo` 와 `scrollTop`** — 이름이 닮았는데 **인자 축이 다르다.**
- **`hidden` 과 `clip`** — 화면이 같은데 **하나만 굴러간다**(정본: [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)).
- **`nearest` 와 `end`** — 요소가 아래에 있으면 **결과가 같다.** 위에 있을 때 갈린다.
- **`scrollRestoration` 과 스크롤 복원 코드** — 앞엣것은 **브라우저의 복원을 끄는 스위치**이지 복원 기능이 아니다.

## 어디서 틀리나

### 1. `document.body.scrollTop` 에 쓴다

표준 모드에서는 **아무 일도 안 일어나고 예외도 없다.** 실측에서 700 을 넣고 되읽으니 0 이었다. **`document.scrollingElement` 를 쓴다.**

### 2. 두 인자 꼴의 축을 거꾸로 쓴다

`scrollTo(100, 0)` 은 **가로로 100** 간다. 세로로 가려면 `scrollTo(0, 100)` 이나 `scrollTo({top: 100})` 이다.

### 3. `smooth` 를 부르고 바로 읽는다

실측에서 **부른 직후 `scrollTop` 이 0** 이었다. 그리고 **CSS 의 `scroll-behavior` 가 `scrollTop` 대입까지 비동기로 만든다** — 스크립트만 봐서는 안 보인다.

### 4. 안 굴러간 것을 모른 채 지나간다

**컨테이너가 아니거나 · 숫자가 아니거나 · 모드가 반대면 전부 조용히 0** 이다. **되읽기 한 줄**이 유일한 진단이다.

### 5. `scrollIntoView` 가 바깥까지 굴리는 것을 잊는다

모달 안의 요소에 부르면 **뒤의 페이지까지 굴러간다.** 실측에서 한 번 불렀더니 **셋이 같이** 움직였다.

### 6. `overflow` 만 보고 스크롤러를 찾는다

`<html>` 은 `overflowY` 가 **`visible`** 인데 문서는 굴러간다. **루트를 따로 잡아야 한다.**

### 7. 위치 복원을 켜 둔 채 내용을 나중에 채운다

브라우저가 복원한 뒤에 내용이 늘면 **그 위치가 엉뚱해진다.** `manual` 로 끄고 직접 복원한다. (**이 문서는 그 경합을 재현하지 못했다** — 처방만 적는다.)

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 표준 모드는 `documentElement`, 호환 모드는 `body` 가 문서를 굴리는 것 | **명세**(CSSOM View — `scrollingElement` 가 그 규칙을 정의한다) |
| 범위 밖 값이 **잘리는** 것(예외가 아님) | **명세**(CSSOM View — 스크롤 위치를 범위 안으로 clamp) |
| 두 인자 꼴이 `(x, y)`, 객체 꼴이 `{left, top}` 인 것 | **명세**(CSSOM View — `ScrollToOptions`) |
| 객체 꼴에서 **빠뜨린 축이 안 움직이는** 것 | **명세**(지정되지 않은 축은 현재 값) |
| `scrollIntoView` 가 **조상 스크롤러를 전부** 굴리는 것 | **명세**(CSSOM View — scroll an element into view) |
| 불리언 인자가 `{block: 'start'}`/`{block: 'end'}` 와 같은 것 | **명세**(CSSOM View) |
| `behavior: 'smooth'` 가 **비동기**인 것 | **명세**(CSSOM View — smooth 는 시간에 걸쳐 진행한다) |
| CSS `scroll-behavior` 가 **기본 behavior 를 정하는** 것 | **명세**(CSSOM View + CSS Overflow) |
| `scrollRestoration` 이 **열거값**이고 잘못된 값이 무시되는 것 | **명세**(HTML — enumerated attribute) |
| `hidden` 이 스크롤 컨테이너이고 `clip` 이 아닌 것 | **명세**(CSS Overflow) — 실측 근거는 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md) |
| **`scrollIntoView` 가 고르는 정확한 스크롤 양** | ★ **구현.** 명세는 「보이게 하라」와 정렬 옵션만 정하고 **얼마나 굴릴지는 구현이 정한다** — `nearest` 가 특히 그렇다 |
| **소수를 넣으면 정수로 돌아오는 것** | **구현 + 장치 픽셀 비.** 이 판은 `devicePixelRatio` 가 1 이다 |
| 스크롤바가 먹는 **15px** 과 그래서 달라지는 **상한** | **구현 + 플랫폼 설정** |
| **`smooth` 의 지속 시간과 곡선** | ★ **구현.** 명세는 시간을 정하지 않는다. **이 문서는 재지도 못했다** |
| **모든 절대 좌표와 상한** | **구현 + 창 크기.** 배너의 `--window-size` 가 전제다 |

- ★ **`nearest` 처럼 「알아서 해 주는」 옵션일수록 구현 쪽**이다. **정확한 위치를 보장받아야 하면 직접 계산해서 `scrollTo` 로 넣는다.**

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 페이지 맨 위로 | `window.scrollTo(0, 0)` · `document.scrollingElement` | `document.body.scrollTop = 0` |
| 정확한 위치로 | `scrollTo({top: n})` | `scrollIntoView`(양을 구현이 정한다) |
| 「보이게만 해 줘」 | `scrollIntoView({block: 'nearest'})` | 좌표를 손으로 계산 |
| 상대 이동 | `scrollBy` | 읽고 더해서 `scrollTo`(그 사이 값이 변한다) |
| 끝까지 갔는지 판정 | `scrollTop >= scrollHeight - clientHeight - 1` | `scrollTop === scrollHeight`(영영 거짓이다) |
| 부드럽게 굴린다 | `behavior: 'smooth'` + 뒤 작업은 **이벤트로** | 부른 다음 줄에서 좌표 읽기 |
| CSS 의 smooth 를 이번만 끈다 | `behavior: 'instant'` | 클래스 토글로 CSS 를 껐다 켜기 |
| 스크롤러 찾기 | `overflow` 두 조건 + `document.scrollingElement` | `overflow !== 'visible'` 하나 |
| 위치 복원 | `scrollRestoration = 'manual'` + 내용이 자리 잡은 뒤 복원 | 기본값에 맡기고 내용은 나중에 채우기 |
| 스크롤 위치를 자주 읽는다 | [목록의 **35번 주제**](../35-intersection-observer/)(IntersectionObserver) | 매 프레임 `scrollY` 읽기([목록의 **10번 주제**](../10-layout-thrashing/)) |

## 핵심 문장

1. **먼저 물을 것은 「누가 굴러가나」다** — 내가 부른 요소가 굴러간다는 보장이 없다.
2. **문서를 굴리는 것은 모드에 따라 갈린다** — 표준 모드는 `documentElement`, 호환 모드는 `body`. **`document.scrollingElement` 가 그 답을 준다.**
3. **쓰기는 조용히 실패한다** — 범위 밖·숫자 아님·컨테이너 아님·모드 반대, 넷 다 예외가 없다. **되읽기만이 진단이다.**
4. **두 인자 꼴은 `(x, y)`, 객체 꼴은 `{left, top}`** 이고 **빠뜨린 축은 안 움직인다.**
5. **`scrollIntoView` 는 조상 스크롤러를 전부 굴린다** — 모달 안에서 부르면 뒤 페이지까지 움직인다.
6. **`hidden` 은 굴러가고 `clip` 은 안 굴러간다** — 화면은 같다.
7. **스크롤러 찾기 규칙은 루트에서 예외가 난다** — `<html>` 의 `overflow` 는 `visible` 이다.
8. **`smooth` 는 비동기다** — 그리고 **CSS 한 줄이 `scrollTop` 대입까지 비동기로 만든다.** 도착은 이 문서가 **못 쟀다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 11번)
- [09번 주제](../09-element-geometry/2-summary.md) — ★ **`scrollTop`·`scrollHeight`·`clientHeight` 를 읽는 쪽이 그쪽**이다. 여기는 **쓰는 쪽**
- [10번 주제](../10-layout-thrashing/2-summary.md) — 스크롤 오프셋을 읽는 것도 **레이아웃을 강제한다.** 스크롤 핸들러가 그 주제의 대표 사고 자리다
- [06번 주제](../06-attribute-vs-property/2-summary.md) — `scrollRestoration` 처럼 **열거값이 조용히 무시되는** 모양의 정본
- [목록의 **35번 주제**](../35-intersection-observer/)(IntersectionObserver) — 「보이나」를 **스크롤 위치를 읽지 않고** 묻는 법
- 목록의 **38번 주제**(`requestAnimationFrame`) — 스크롤에 맞춰 무언가를 움직일 때
- 목록의 **46번 주제**(History API) — `scrollRestoration` 의 이웃. **뒤로 가기에서 무엇이 복원되나**
- [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md) — ★ **이 주제의 정본 이웃.** 무엇이 스크롤 컨테이너가 되나, `hidden` 과 `clip` 의 차이, 스크롤바가 먹는 폭이 전부 거기다. **여기서 다시 쓰지 않는다**
- [CSS 21번 주제](../../languages/css/syntax/21-position-and-containing-block/2-summary.md) — `sticky` 가 **스크롤 컨테이너 안에서만 산다**는 것
- [CSS 58번 주제](../../languages/css/syntax/58-scroll-driven-animations/2-summary.md) — 스크롤을 **애니메이션의 시간축**으로 쓰는 법. 스크립트 없이 하는 쪽

## 용어 풀이

- **스크롤 컨테이너(scroll container)** — 내용이 넘칠 때 굴릴 수 있는 상자. `overflow` 가 `auto`·`scroll`·`hidden` 일 때 생긴다(`clip` 은 아니다).
- **스크롤포트(scrollport)** — 그 상자에서 실제로 보이는 칸. `clientWidth`/`clientHeight` 가 재는 칸이다.
- **`scrollingElement`** — 문서를 굴리는 요소. 표준 모드는 `<html>`, 호환 모드는 `<body>`.
- **호환 모드(quirks mode)** — `<!doctype html>` 이 없을 때 들어가는 옛 동작 모드. `document.compatMode` 가 `BackCompat` 이다.
- **클램프(clamp)** — 범위 밖 값을 **범위 안으로 잘라 넣는 것.** 이 주제의 쓰기가 전부 그렇다.
- **`ScrollToOptions`** — `{left, top, behavior}` 꼴의 인자 객체.
- **`block`/`inline`** — `scrollIntoView` 의 두 축. 글 흐름 기준이라 가로쓰기에서는 `block` 이 세로다(정본: [CSS 32번 주제](../../languages/css/syntax/32-logical-properties-and-writing-mode/2-summary.md)).
- **`scrollRestoration`** — 뒤로 가기에서 **브라우저가 위치를 복원할지**를 정하는 스위치. `'auto'` 또는 `'manual'`.
- **조용한 실패(silent failure)** — 예외도 경고도 없이 아무 일도 안 일어나는 것. 이 주제의 쓰기에 네 가지가 있다.

## 더 들어가면

- **`scrollend` 이벤트**는 「굴리기가 끝났다」를 알려 준다 — `smooth` 의 도착을 기다리는 정답이다. **이 문서는 관측하지 못했다**(프레임을 못 몬다). 이벤트 자체는 이 갈래의 이벤트 묶음 몫이다.
- **`scroll` 이벤트는 프레임마다 온다** — 그 안에서 `getBoundingClientRect()` 를 읽으면 [목록의 **10번 주제**](../10-layout-thrashing/)가 곧바로 시작된다. **이 문서는 그 이벤트도 관측하지 못했다.**
- **`scroll-snap`** 은 CSS 로 「멈출 자리」를 정한다. 스크립트로 굴려도 스냅이 걸린다 — 정본은 CSS 갈래이고 **여기서 던져 보지 않았다.**
- **`overscroll-behavior`** 는 끝까지 간 스크롤이 **바깥으로 전달되는 것**을 막는다((5)에서 본 「바깥이 대신 굴러가는」 일의 CSS 쪽 스위치다). **던져 보지 않았다.**
- **`Element.scrollIntoViewIfNeeded()`** 는 `{block: 'nearest'}` 의 옛 비표준 판이다. **Chromium 한정**이라 이 목록에서는 다루지 않는다.
- **가로 축**(`scrollLeft`·`inline`)은 이 문서가 **세로만큼 던지지 않았다.** 쓰기 방향이 오른쪽에서 왼쪽인 문서에서는 **`scrollLeft` 가 음수가 되는 판**이 있는데 **확인하지 않았다.**
