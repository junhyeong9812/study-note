# web-api/09 — 요소 기하: `getBoundingClientRect`·`offset*`/`client*`/`scroll*` 과 좌표계 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> **이 갈래는 언어가 아니라 플랫폼이다.** 여기서 다루는 것은 「CSS 가 상자를 어떻게 정하나」가 아니라 「**스크립트가 그 상자를 어떻게 읽나**」다. 상자 모델 자체는 [CSS 15번 주제](../../languages/css/syntax/15-box-model-and-box-sizing/2-summary.md)가, 스크롤 컨테이너는 [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)가, `transform` 은 [CSS 54번 주제](../../languages/css/syntax/54-transform-2d-and-origin/2-summary.md)가 정본이고 여기서 다시 쓰지 않는다.\
> **기준 소스** — [CSSOM View Module](https://drafts.csswg.org/cssom-view/) 의 「Extensions to the `Element` Interface」·「The `DOMRect` Interface」·「Extensions to the `Window` Interface」 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 블록마다 명령이 배너로 실려 있고, 그 배너에는 **`--window-size=1000,800`** 이 들어 있다 — **좌표를 싣는 주제라 창 크기를 빼면 아무 수치도 재현되지 않는다.**\
> **엔진은 Chrome 하나다** — Firefox 155.0.1 은 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. 그래서 이 문서는 **이식성을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `offsetWidth` 계열은 IE 시절의 사실상 표준이 CSSOM View 로 사후 명세화된 것이고, **Baseline 추적 대상이 아닐 만큼 오래됐다**(갈래 [`../README.md`](../README.md) 의 「확인하지 못한 것」).\
> **선행** — [08번 주제](../08-getcomputedstyle/2-summary.md)(계산값 읽기)와 [CSS 15번 주제](../../languages/css/syntax/15-box-model-and-box-sizing/2-summary.md)(박스 모델).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 수치를 재지만 **시간이 아니라 좌표**를 재기 때문이다. 같은 창 크기에서 좌표는 결정적이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 모든 좌표·치수 · `offsetParent` 가 누구인가 · 정수/소수 여부 · `getClientRects().length` · 객체 동일성 | 같은 창 크기·같은 판이면 레이아웃이 결정적이다. **세 판을 돌려 한 글자도 같았다** |
| **흔들린다** | **창 크기를 바꾸면 절대 좌표 전부** | 그래서 배너에 `--window-size=1000,800` 을 박았다. 기본 창(780×493)에서는 다른 수가 나온다 |
| **흔들린다** | 스크롤바가 먹는 **15px** · 인라인 조각의 폭(`97.28` 류) | **이 플랫폼의 스크롤바 설정과 글꼴 치수**에 달렸다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- ★ **「시간이 안 흔들린다」는 뜻이 아니다** — 이 주제는 **시간을 아예 재지 않는다.** 읽기 비용은 [08번 주제](../08-getcomputedstyle/2-summary.md)와 [목록의 **10번 주제**](../10-layout-thrashing/)가 잰다.
- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

## 한눈에 — 쉽게 말하면

**★ 세 묶음은 「서로 다른 자로 잰 값」이 아니라 「서로 다른 원점에서 잰 값」이다.**

지도에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **지금 내 창에서 몇 칸 아래인가** | `getBoundingClientRect()` — 원점이 **뷰포트 왼쪽 위** |
| **이 건물 안에서 몇 층인가** | `offsetTop`/`offsetLeft` — 원점이 **`offsetParent`** |
| **이 서랍을 얼마나 밀어 넣었나** | `scrollTop`/`scrollLeft` — 원점이 **자기 내용** |
| 건물이 어디인지는 **따로 물어야 안다** | `offsetParent` 가 누구인지 안 보면 `offsetTop` 은 뜻이 없다 |
| 창을 굴리면 **창 기준 값만** 바뀐다 | 스크롤은 `rect` 를 바꾸고 `offsetTop` 은 안 바꾼다 |
| 지도에는 **기울인 건물도 똑바로 그린 사각형**으로 들어간다 | `rotate` 를 줘도 `rect` 는 축 정렬 외접 상자다 |
| 치수는 **눈금이 다르다** | `offsetWidth` 는 정수, `rect.width` 는 소수 |

- **세 묶음을 한 요소에 동시에 대 보면** 무엇이 다른지가 한 줄에 드러난다 — 그것이 이 주제의 첫 실험이다.
- ★ **이름이 비슷해서 섞어 쓰게 된다.** `offsetWidth`·`clientWidth`·`scrollWidth` 는 **재는 칸이 다 다르고**, `offsetTop` 과 `rect.top` 은 **원점이 다르다.**
- ★ **읽는 값이 비싸다.** 이 주제의 모든 읽기가 [목록의 **10번 주제**](../10-layout-thrashing/)가 재는 「강제 동기 레이아웃」의 방아쇠다.

```text
   원점이 셋이다

   ┌─ 뷰포트(지금 보이는 창) ────────────────┐
   │  ↖ 여기가 rect 의 원점                   │
   │                                          │
   │    ┌─ offsetParent(가장 가까운 위치 잡힌 조상) ─┐
   │    │  ↖ 여기가 offsetTop 의 원점                │
   │    │                                            │
   │    │     ┌─ 요소 자신 ──────────┐               │
   │    │     │ ↖ 여기가 scrollTop 의 │               │
   │    │     │   원점(자기 내용)      │               │
   │    │     └────────────────────────┘               │
   │    └──────────────────────────────────────────────┘
   └──────────────────────────────────────────┘
```

## 이 주제가 답하려는 질문

1. **세 묶음의 기준점이 각각 무엇인가.** 스크롤하면 **어느 값이 변하고 어느 값이 안 변하나.**
2. **`offsetParent` 는 무엇이 되나.** 그리고 **`null` 이 되는 자리는 어디인가.**
3. **같은 상자를 재는데 왜 수가 다른가** — 테두리·스크롤바·`transform`·소수점.

## 이 갈래의 관측 창 — ★ 창 4 는 `elementFromPoint()`

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom             스크립트가 다 돈 뒤의 트리를 글자로
                               ★ 이 주제에서는 아무것도 못 본다 — 아래 (1)
  창 2  노드 단위 프로브        한 요소에 세 묶음을 동시에 대고 한 줄로 찍는다
  창 3  두 번 읽기              스크롤 전 / 스크롤 뒤를 같은 요소로
  ★ 창 4 (이 주제 고유)  document.elementFromPoint(x, y)
        무엇을 답하나:  '내가 읽은 그 좌표를 도로 넣으면 이 요소가 나오나'
        왜 필요한가:    앞의 세 창은 전부 '값을 읽기'만 한다.
                        읽은 수가 어느 원점의 것인지는 값만 봐서는 구분이 안 된다
                        — 스크롤이 0 이면 세 수가 우연히 같아지기 때문이다.
        이 창은 좌표를 '쓴다'. 틀린 원점의 좌표를 넣으면 엉뚱한 요소가 나온다.
  ★ 부적용인 창  시간 측정 — 이 주제는 비용을 재지 않는다 (10번 주제의 몫)
```

- ★ **왜 창 ④ 가 필요한가** — **스크롤이 0 일 때는 `rect.top` 과 `offsetTop` 누적값이 같은 수**다. 그 상태에서 코드를 쓰면 **틀린 채로 돌아간다.** 굴리는 순간 갈리는데, 그때는 이미 그 수를 여기저기 쓴 뒤다.
- **창 ④ 는 판정만 한다.** 좌표를 어떻게 옮기는지(스크롤 오프셋을 더하고 빼는 것)는 아래 (6)이다.

## 동작 방식

### (1) 창 ① 은 이 주제에서 아무것도 못 본다

**언제 쓰나** — 이 주제를 시작할 때. **무엇이 안 보이는지부터 확인한다.**

```html
<!-- wa09b-09-tree.html -->
<!doctype html>
<meta charset="utf-8">
<title>09-tree</title>
<style>#t { margin-left: 40px; width: 120px; height: 30px }</style>
<div id="t">좌표를 잰 상자</div>
<script>
  // 기하를 읽기만 한다 — 읽기는 트리를 바꾸지 않는다.
  const t = document.getElementById('t');
  window.읽은좌표 = [t.getBoundingClientRect().left, t.offsetLeft, t.scrollTop];
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-tree.html 2>/dev/null | sed -n '4,5p'
<style>#t { margin-left: 40px; width: 120px; height: 30px }</style>
</head><body><div id="t">좌표를 잰 상자</div>
(exit 0)
```

- **`<div id="t">` 에는 아무 속성도 없다.** 좌표를 읽어도 **트리에 자국이 안 남는다** — 읽기는 문서를 안 바꾼다.
- **「이 상자가 어디에 몇 픽셀로 놓였나」는 창 ① 로 영영 못 묻는다.** 트리에는 `margin-left: 40px` 이라는 **선언의 글자**만 있고, 그것이 실제로 몇 픽셀이 됐는지는 없다.
- ★ 이 갈래의 주력 창이 통째로 부적용인 주제다. [08번 주제](../08-getcomputedstyle/2-summary.md)와 같은 모양이고, 이유도 같다 — **창 ① 은 트리를 보고 이 주제는 레이아웃을 본다.**

비용 — 없다. 다만 **이 사실을 안 적어 두면 「트리를 봤는데 없더라」가 근거로 쓰인다.**

### (2) 세 묶음을 한 요소에 동시에 댄다

**언제 쓰나** — 「이 요소가 어디에 있나」를 물을 때. **어느 창구로 물을지부터 정해야 한다.**

**던진 것** — 아래 (3)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-09-three.html -->
<!doctype html>
<meta charset="utf-8">
<title>09-three</title>
<style>
  body { margin: 0 }
  #head { height: 500px; background: rgb(238, 238, 238) }
  #scroller { width: 300px; height: 200px; overflow: auto;
              border: 5px solid rgb(51, 51, 51); padding: 10px; margin-left: 20px }
  #inner { position: relative; width: 600px; height: 800px }
  #t { position: absolute; top: 250px; left: 120px; width: 100px; height: 60px; overflow: auto }
  #tin { width: 300px; height: 300px }
  #tail { height: 1500px }
</style>
<div id="head">문서 위쪽</div>
<div id="scroller"><div id="inner"><div id="t"><div id="tin">t 안의 내용</div></div></div></div>
<div id="tail">문서 아래쪽</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const F = n => n.toFixed(2);
const $ = id => document.getElementById(id);
const t = $('t'), sc = $('scroller');
const 표 = cols => (...c) => O.push(c.map((v, i) => padw(String(v), cols[i])).join('').replace(/ +$/, ''));
const row = 표([22, 12, 12, 12, 12, 12, 12]);
const row2 = 표([26, 14, 40]);

O.push('한 요소에 세 묶음을 동시에 대고 스크롤을 세 번 움직였다');
row('무엇을 했나', 'rect.top', 'rect.left', 'offsetTop', 'offsetLeft', 't.scrollTop', 'sc.scrollTop');
const 찍기 = label => {
  const r = t.getBoundingClientRect();
  row(label, F(r.top), F(r.left), t.offsetTop, t.offsetLeft, t.scrollTop, sc.scrollTop);
};
찍기('초기');
sc.scrollTop = 100;  찍기('sc.scrollTop = 100');
scrollTo(0, 200);    찍기('window 를 200 로');
t.scrollTop = 50;    찍기('t.scrollTop = 50');
O.push('');

O.push('그래서 세 묶음의 기준점이 다르다');
row2('무엇을 재나', '기준점', '스크롤에 따라 변하나');
row2('getBoundingClientRect()', '뷰포트', '변한다 — 조상 스크롤러·창 둘 다');
row2('offsetTop / offsetLeft', 'offsetParent', '안 변한다 — 배치가 바뀌어야 변한다');
row2('el.scrollTop', '자기 내용', '자기가 굴려질 때만 변한다');
O.push('');
O.push('offsetParent = ' + (t.offsetParent ? '#' + t.offsetParent.id : String(t.offsetParent))
     + '   ·   window.scrollY = ' + scrollY + '   ·   t.scrollTop 의 상한 = '
     + (t.scrollHeight - t.clientHeight) + ' (scrollHeight ' + t.scrollHeight + ' - clientHeight ' + t.clientHeight + ')');
O.push('rect.top + scrollY = ' + F(t.getBoundingClientRect().top + scrollY)
     + '   ← 창 스크롤만 되돌린 값이지 offsetTop 이 아니다 (offsetTop = ' + t.offsetTop + ')');

document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-three.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
한 요소에 세 묶음을 동시에 대고 스크롤을 세 번 움직였다
무엇을 했나           rect.top    rect.left   offsetTop   offsetLeft  t.scrollTop sc.scrollTop
초기                  765.00      155.00      250         120         0           0
sc.scrollTop = 100    665.00      155.00      250         120         0           100
window 를 200 로      465.00      155.00      250         120         0           100
t.scrollTop = 50      465.00      155.00      250         120         50          100
(exit 0)
```

- **스크롤을 세 번 움직였는데 움직인 칸이 매번 다르다.**
  - `sc.scrollTop = 100` — **`rect.top` 만** 100 줄었다(765 → 665). 조상 스크롤러가 굴러가면 화면에서의 위치가 바뀐다.
  - `window` 를 200 로 — **또 `rect.top` 만** 200 줄었다(665 → 465).
  - `t.scrollTop = 50` — **아무 칸도 안 바뀌었다.** 자기 **안쪽 내용**을 민 것이라 자기 상자는 그대로다.
- ★ **`offsetTop` 은 네 줄 내내 `250`** 이다. 스크롤은 배치를 안 바꾸기 때문이다.
- ★ **`t.scrollTop` 은 다른 둘과 성격이 아예 다르다.** 앞의 둘이 「나는 어디 있나」라면 이것은 「내 안을 얼마나 밀었나」다. **같은 묶음으로 외우면 반드시 틀린다.**

### (3) 그래서 기준점이 셋이다

**언제 쓰나** — 읽은 수를 다른 수와 더하거나 빼기 직전에.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-three.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,15p'
그래서 세 묶음의 기준점이 다르다
무엇을 재나               기준점        스크롤에 따라 변하나
getBoundingClientRect()   뷰포트        변한다 — 조상 스크롤러·창 둘 다
offsetTop / offsetLeft    offsetParent  안 변한다 — 배치가 바뀌어야 변한다
el.scrollTop              자기 내용     자기가 굴려질 때만 변한다

offsetParent = #inner   ·   window.scrollY = 200   ·   t.scrollTop 의 상한 = 255 (scrollHeight 300 - clientHeight 45)
rect.top + scrollY = 665.00   ← 창 스크롤만 되돌린 값이지 offsetTop 이 아니다 (offsetTop = 250)
(exit 0)
```

- **`offsetParent` 가 `#inner`** 다 — `#inner` 에 `position: relative` 가 걸려 있어서다((4)).
- **`t.scrollTop` 의 상한이 `255`** 다. `scrollHeight`(300) − `clientHeight`(45) 인데, **`clientHeight` 가 60 이 아니라 45 인 것**은 가로 스크롤바가 15px 을 먹었기 때문이다(정본: [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md)).
- ★ **마지막 줄이 함정의 정체**다. `rect.top + scrollY` 는 **창 스크롤만 되돌린 값**(665)이지 `offsetTop`(250)이 아니다. **가운데에 낀 조상 스크롤러 100 은 그 셈에 안 들어 있다.**

```text
   같은 요소, 다른 원점

   문서 맨 위 ─┬─ 500 ─ #scroller 시작
               │
               ├─ (sc 안을 100 굴렸다)
               │
   offsetParent(#inner) 시작 ─┬─ 250 ──> offsetTop = 250   (안 변한다)
                              │
   뷰포트 위 ────────────────┴─ 465 ──> rect.top = 465     (창·조상 둘 다 반영)
                                          rect.top + scrollY = 665
                                          ↑ 창 200 만 되돌린 값. 조상 100 은 그대로 빠져 있다
```

비용 — 이 읽기들이 전부 **레이아웃을 강제한다.** [목록의 **10번 주제**](../10-layout-thrashing/)가 그 값을 잰다.

### (4) `offsetParent` 가 무엇이 되나

**언제 쓰나** — `offsetTop` 을 쓰기 전에 **반드시** 한 번.

**던진 것** — 아래 (5)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-09-parent.html -->
<!doctype html>
<meta charset="utf-8">
<title>09-parent</title>
<style>
  body { margin: 0 }
  #a { margin-top: 60px; padding: 10px }
  #b { margin-top: 20px; padding: 5px }
  #c { width: 80px; height: 20px }
</style>
<div id="a"><div id="b"><div id="c">여기</div></div></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [30, 20, 14, 14][i])).join('').replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const a = $('a'), b = $('b'), c = $('c');
const 이름 = e => e === null ? 'null' : (e.id ? '#' + e.id : e.tagName);

O.push('offsetParent 가 무엇이 되나 — 중간 요소 #b 의 position 만 바꿨다');
row('무엇을 바꿨나', 'c.offsetParent', 'c.offsetTop', 'c.offsetLeft');
for (const pos of ['static', 'relative', 'absolute', 'fixed', 'sticky']) {
  b.style.position = pos;
  if (pos === 'sticky' || pos === 'absolute' || pos === 'fixed') b.style.top = '0';
  row('#b 를 position: ' + pos, 이름(c.offsetParent), c.offsetTop, c.offsetLeft);
}
b.style.position = 'static'; b.style.top = '';
O.push('');

O.push('자기 자신과 조상의 사정으로 null 이 되는 자리');
row('무엇을 했나', 'c.offsetParent', 'c.offsetTop', 'c.offsetWidth');
c.style.position = 'fixed';
row('#c 자신을 position: fixed', 이름(c.offsetParent), c.offsetTop, c.offsetWidth);
c.style.position = '';
a.style.display = 'none';
row('조상 #a 를 display: none', 이름(c.offsetParent), c.offsetTop, c.offsetWidth);
a.style.display = '';
const 뗀것 = document.createElement('div');
row('트리에 안 붙인 요소', 이름(뗀것.offsetParent), 뗀것.offsetTop, 뗀것.offsetWidth);
row('document.body', 이름(document.body.offsetParent), document.body.offsetTop, document.body.offsetWidth);
row('document.documentElement', 이름(document.documentElement.offsetParent),
    document.documentElement.offsetTop, document.documentElement.offsetWidth);
O.push('');
O.push('★ offsetTop 은 「문서 위에서부터」가 아니라 「offsetParent 위에서부터」다 —');
O.push('  위 표의 첫 줄과 둘째 줄이 같은 요소의 같은 위치인데 ' + (() => {
  b.style.position = 'static'; const s = c.offsetTop;
  b.style.position = 'relative'; const r = c.offsetTop;
  b.style.position = 'static';
  return s + ' 와 ' + r + ' 로 갈린다';
})() + '.');

document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-parent.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
offsetParent 가 무엇이 되나 — 중간 요소 #b 의 position 만 바꿨다
무엇을 바꿨나                 c.offsetParent      c.offsetTop   c.offsetLeft
#b 를 position: static        BODY                95            15
#b 를 position: relative      #b                  5             5
#b 를 position: absolute      #b                  5             5
#b 를 position: fixed         #b                  5             5
#b 를 position: sticky        #b                  5             5
(exit 0)
```

- **중간 요소 `#b` 의 `position` 만 바꿨는데 `#c` 의 좌표가 95 에서 5 로 바뀐다.** 값이 바뀐 게 아니라 **기준이 바뀐 것**이다.
- **`static` 이면 건너뛴다** — `#b` 를 지나 **`BODY`** 까지 올라갔다. `static` 아닌 조상이 하나도 없으면 `body` 다.
- ★ **`relative`·`absolute`·`fixed`·`sticky` 는 넷 다 똑같이 `offsetParent` 가 된다.** 「위치가 잡혔나」 하나만 본다.
- ★ **그래서 `offsetTop` 은 「문서 위에서부터」가 아니다.** CSS 를 한 줄 고치면 조용히 기준이 바뀐다 — **에러도 경고도 없다.**

### (5) `offsetParent` 가 `null` 이 되는 자리

**언제 쓰나** — `offsetParent` 를 타고 올라가는 반복문을 쓸 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-parent.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,18p'
자기 자신과 조상의 사정으로 null 이 되는 자리
무엇을 했나                   c.offsetParent      c.offsetTop   c.offsetWidth
#c 자신을 position: fixed     null                95            80
조상 #a 를 display: none      null                0             0
트리에 안 붙인 요소           null                0             0
document.body                 null                0             1000
document.documentElement      null                0             1000

★ offsetTop 은 「문서 위에서부터」가 아니라 「offsetParent 위에서부터」다 —
  위 표의 첫 줄과 둘째 줄이 같은 요소의 같은 위치인데 95 와 5 로 갈린다.
(exit 0)
```

- **자기 자신이 `fixed`** 면 `null` 이다. 그런데 **`offsetTop` 은 95 로 값이 나온다** — 「기준이 없는데 값은 있다」는 모양이다. 이때의 95 는 **초기 포함 블록 기준**이다.
- **조상이 `display: none`** 이면 `null` 이고 **치수도 전부 0** 이다.
- **트리에 안 붙인 요소**도 `null`·0 이다([08번 주제](../08-getcomputedstyle/2-summary.md)의 「트리 밖은 침묵한다」와 같은 자리).
- ★ **`body` 와 `documentElement` 도 `null`** 이다. 그래서 **`while (e.offsetParent)` 로 올라가는 반복문은 `body` 에서 자연히 멈춘다** — 이것이 (6)의 누적 셈이 성립하는 근거다.

```text
   offsetParent 판정 — 위로 올라가며 처음 만나는 것

   자기가 fixed 인가 ──── 그렇다 ──> null
        │ 아니다
        v
   조상이 display:none 인가 ─ 그렇다 ──> null
        │ 아니다
        v
   위로 올라가며 position 이 static 이 아닌 조상 ──> 그것
        │ 끝까지 없다
        v
   body  (body 자신과 html 은 null)
```

비용 — `offsetParent` 를 읽는 것도 **레이아웃을 강제한다**([목록의 **10번 주제**](../10-layout-thrashing/)에서 실측).

### (6) 창 ④ — 읽은 좌표를 도로 넣어 본다

**언제 쓰나** — 좌표를 더하거나 빼서 다른 API 에 넘기기 직전에.

```html
<!-- wa09b-09-point.html -->
<!doctype html>
<meta charset="utf-8">
<title>09-point</title>
<style>
  body { margin: 0; font: 14px monospace }
  #head { height: 300px; background: rgb(238, 238, 238) }
  #rel { position: relative; margin-left: 40px; width: 400px }
  #t { width: 80px; height: 40px; margin-top: 20px; margin-left: 30px; background: rgb(204, 255, 204) }
  #tail { height: 2000px; background: rgb(250, 250, 250) }
</style>
<div id="head">문서 위</div>
<div id="rel"><div id="t">T</div></div>
<div id="tail">문서 아래</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [16, 10, 12, 14, 22, 22][i])).join('').replace(/ +$/, ''));
const F = n => n.toFixed(2);
const t = document.getElementById('t');
const 이름 = e => e === null ? 'null' : (e.id ? '#' + e.id : e.tagName);
// offsetTop / offsetLeft 를 조상까지 누적하면 '문서 기준' 좌표가 된다.
const 누적 = (el, 축) => { let v = 0, e = el; while (e.offsetParent) { v += 축 === 'y' ? e.offsetTop : e.offsetLeft; e = e.offsetParent; } return v; };

O.push('창 ④ — 좌표를 읽지 말고 그 좌표로 되물어 본다');
row('스크롤 상태', 'scrollY', 'rect.top', 'offset 누적', 'rect 중심으로 물으면', 'offset 좌표로 물으면');
const 찍기 = label => {
  const r = t.getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const oy = 누적(t, 'y') + 20, ox = 누적(t, 'x') + 40;
  row(label, scrollY, F(r.top), 누적(t, 'y'),
      이름(document.elementFromPoint(cx, cy)), 이름(document.elementFromPoint(ox, oy)));
};
찍기('스크롤 전');
scrollTo(0, 250);
찍기('scrollY = 250');
O.push('');
O.push('두 좌표가 스크롤 전에는 같은 요소를 가리키고, 250 을 굴리자 갈린다.');
O.push('elementFromPoint 가 받는 것은 뷰포트 좌표이기 때문이다 — offset 누적값은 문서 좌표다.');
O.push('되돌리려면 빼 준다: elementFromPoint(누적x - scrollX, 누적y - scrollY) = '
     + 이름(document.elementFromPoint(누적(t, 'x') + 40 - scrollX, 누적(t, 'y') + 20 - scrollY)));
O.push('');
O.push('뷰포트 밖을 물으면 — 스크롤해서 화면에서 사라진 자리');
scrollTo(0, 0);
O.push('  scrollY = 0 일 때 t 의 rect.top = ' + F(t.getBoundingClientRect().top)
     + ' → 뷰포트 높이 ' + document.documentElement.clientHeight + ' 안인가: '
     + (t.getBoundingClientRect().top < document.documentElement.clientHeight));
scrollTo(0, 1200);
const r2 = t.getBoundingClientRect();
O.push('  scrollY = 1200 일 때 rect.top = ' + F(r2.top) + ' (음수다) · elementFromPoint(그 점) = '
     + 이름(document.elementFromPoint(r2.left + 5, r2.top + 5)));
O.push('  그런데 offset 누적값은 ' + 누적(t, 'y') + ' 으로 한 글자도 안 변했다.');

document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-point.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,8p'
창 ④ — 좌표를 읽지 말고 그 좌표로 되물어 본다
스크롤 상태     scrollY   rect.top    offset 누적   rect 중심으로 물으면  offset 좌표로 물으면
스크롤 전       0         320.00      320           #t                    #t
scrollY = 250   250       70.00       320           #t                    #tail

두 좌표가 스크롤 전에는 같은 요소를 가리키고, 250 을 굴리자 갈린다.
elementFromPoint 가 받는 것은 뷰포트 좌표이기 때문이다 — offset 누적값은 문서 좌표다.
되돌리려면 빼 준다: elementFromPoint(누적x - scrollX, 누적y - scrollY) = #t
(exit 0)
```

- **스크롤 전에는 두 좌표가 똑같이 `#t` 를 가리킨다.** 여기서 멈추면 **틀린 코드가 통과한다.**
- **250 을 굴리자 갈린다** — `rect` 중심은 여전히 `#t` 인데 **offset 누적 좌표는 `#tail`**(문서 아래쪽 채움)을 가리킨다.
- ★ **`elementFromPoint` 가 받는 것은 뷰포트 좌표**다. offset 누적값은 **문서 좌표**라서, 굴린 만큼 어긋난다. **빼 주면 다시 맞는다**(`누적 − scrollX/scrollY`).
- ★ **이것이 이 주제의 창 ④ 인 이유** — 값을 읽기만 하면 두 수가 같은지 다른지밖에 못 본다. **넣어 보면 「무엇을 가리키는 수인가」가 드러난다.**

**뷰포트 밖으로 나가면.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-point.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '10,13p'
뷰포트 밖을 물으면 — 스크롤해서 화면에서 사라진 자리
  scrollY = 0 일 때 t 의 rect.top = 320.00 → 뷰포트 높이 713 안인가: true
  scrollY = 1200 일 때 rect.top = -880.00 (음수다) · elementFromPoint(그 점) = null
  그런데 offset 누적값은 320 으로 한 글자도 안 변했다.
(exit 0)
```

- **뷰포트 밖으로 나간 요소의 `rect.top` 은 음수**다(−880). **`elementFromPoint` 는 그 점에서 `null`** 을 돌려준다 — 화면 밖은 히트 테스트 대상이 아니다.
- **같은 순간에 offset 누적값은 320 그대로**다. **「화면에서 사라졌나」를 `offsetTop` 으로는 영영 못 묻는다.**

```text
   좌표를 옮기는 두 방향 (CSSOM View 가 정한 것은 '뷰포트 기준'이다)

   문서 좌표  =  rect.top  +  window.scrollY        ← 창 스크롤만 되돌린다
   뷰포트 좌표 =  문서 좌표  −  window.scrollY

   ★ 조상 스크롤러가 끼어 있으면 이 한 줄로는 안 된다 — (3)의 마지막 줄
```

비용 — `elementFromPoint` 는 **레이아웃에 히트 테스트까지** 얹는다. [목록의 **10번 주제**](../10-layout-thrashing/) 실측에서 **이 주제의 읽기 가운데 가장 비쌌다.**

### (7) 세 계열이 각각 어느 칸을 재나

**언제 쓰나** — 치수를 읽을 때. **이름이 비슷해서 여기서 제일 많이 틀린다.**

**던진 것** — 아래 (8)·(9)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa09b-09-box.html -->
<!doctype html>
<meta charset="utf-8">
<title>09-box</title>
<style>
  body { margin: 0; font: 14px monospace }
  .box { width: 200px; height: 60px; padding: 10px; border: 5px solid rgb(51, 51, 51); margin: 8px }
  #sc { overflow: auto }
  #sc > div { width: 400px; height: 300px }
  #tr { transform: scale(2); transform-origin: 0 0 }
  #rot { transform: rotate(45deg) }
  #frac { width: 100.6px; height: 40.4px; padding: 3.3px; border: 2.2px solid rgb(0, 0, 0);
          margin-top: 8.6px }
  #gone { display: none }
  #wrap { width: 240px }
</style>
<div id="wrap">
  <div id="plain" class="box">plain</div>
  <div id="sc" class="box"><div>넘치는 내용</div></div>
  <div id="tr" class="box">scale(2)</div>
  <div id="rot" class="box">rotate(45deg)</div>
  <div id="frac">소수</div>
  <div id="gone" class="box">display:none</div>
  <span id="inl">줄을 넘기는 인라인 텍스트가 여기에 길게 이어진다 그래서 여러 줄이 된다 정말로 여러 줄이 된다</span>
</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const 표 = cols => (...c) => O.push(c.map((v, i) => padw(String(v), cols[i])).join('').replace(/ +$/, ''));
const row = 표([24, 11, 11, 11, 11, 13, 13]);
const F = n => n.toFixed(2);
const $ = id => document.getElementById(id);

O.push('세 묶음이 각각 어느 칸을 재나 — 같은 .box 에 테두리 5 · 패딩 10 · 내용 200x60');
row('무엇을', 'offsetW', 'clientW', 'scrollW', 'offsetH', 'rect.width', 'rect.height');
for (const id of ['plain', 'sc', 'tr', 'rot', 'frac', 'gone']) {
  const e = $(id), r = e.getBoundingClientRect();
  row('#' + id, e.offsetWidth, e.clientWidth, e.scrollWidth, e.offsetHeight, F(r.width), F(r.height));
}
const 뗀것 = document.createElement('div'); 뗀것.className = 'box';
const dr = 뗀것.getBoundingClientRect();
row('트리 밖', 뗀것.offsetWidth, 뗀것.clientWidth, 뗀것.scrollWidth, 뗀것.offsetHeight, F(dr.width), F(dr.height));
O.push('');

O.push('정수인가 소수인가 — #frac 은 width 100.6 · padding 3.3 · border 2.2');
const f = $('frac'), fr = f.getBoundingClientRect();
O.push('  offsetWidth = ' + f.offsetWidth + '   (Number.isInteger = ' + Number.isInteger(f.offsetWidth) + ')');
O.push('  rect.width  = ' + fr.width + '   (같은 상자를 잰 값이다)');
O.push('  offsetTop   = ' + f.offsetTop + '   rect.top = ' + fr.top);
O.push('');

O.push('transform 은 어느 쪽에 섞이나');
const tr = $('tr'), rot = $('rot');
O.push('  #tr  scale(2)      offsetWidth = ' + tr.offsetWidth + '   rect.width = ' + F(tr.getBoundingClientRect().width));
O.push('  #rot rotate(45deg) offsetWidth = ' + rot.offsetWidth + '   rect.width = ' + F(rot.getBoundingClientRect().width)
     + '   rect.left = ' + F(rot.getBoundingClientRect().left) + ' (축 정렬 외접 상자다)');
O.push('');

O.push('상자 하나가 아닌 것 — 줄을 넘긴 인라인');
const inl = $('inl');
O.push('  getClientRects().length = ' + inl.getClientRects().length
     + '   getBoundingClientRect().height = ' + F(inl.getBoundingClientRect().height)
     + '   (첫 조각 높이 = ' + F(inl.getClientRects()[0].height) + ')');
O.push('  .box 하나는 getClientRects().length = ' + $('plain').getClientRects().length);
O.push('');

O.push('돌려받는 객체');
const r1 = $('plain').getBoundingClientRect();
O.push('  타입 = ' + Object.prototype.toString.call(r1) + '   두 번 부르면 === ? '
     + ($('plain').getBoundingClientRect() === $('plain').getBoundingClientRect()));
O.push('  JSON.stringify = ' + JSON.stringify(r1));
$('plain').style.marginLeft = '100px';
O.push('  마진을 바꾼 뒤 붙들고 있던 옛 객체의 left = ' + F(r1.left)
     + '   새로 부른 것의 left = ' + F($('plain').getBoundingClientRect().left) + '  ← 스냅숏이다');

document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
세 묶음이 각각 어느 칸을 재나 — 같은 .box 에 테두리 5 · 패딩 10 · 내용 200x60
무엇을                  offsetW    clientW    scrollW    offsetH    rect.width   rect.height
#plain                  230        220        220        90         230.00       90.00
#sc                     230        205        420        90         230.00       90.00
#tr                     230        220        220        90         460.00       180.00
#rot                    230        220        220        90         226.27       226.27
#frac                   111        107        107        51         111.19       50.98
#gone                   0          0          0          0          0.00         0.00
트리 밖                 0          0          0          0          0.00         0.00
(exit 0)
```

- **`.box` 는 내용 200×60 · 패딩 10 · 테두리 5** 다. 그래서 `offsetWidth` 가 **230**(200 + 20 + 10), `clientWidth` 가 **220**(200 + 20), `rect.width` 가 **230.00** 이다.
- ★ **`offsetWidth` 와 `rect.width` 는 같은 칸(테두리 상자)을 잰다.** 다른 것은 **눈금**((8))과 **`transform` 을 반영하나**((9))뿐이다.
- **`#sc` 만 `clientWidth` 가 205** 다 — **스크롤바가 15px 을 먹었다.** `scrollWidth` 는 **420**(내용 400 + 패딩 20)이다.
- **`#gone`(`display: none`)과 트리 밖은 전부 0** 이다. [08번 주제](../08-getcomputedstyle/2-summary.md)에서는 `display: none` 이 **계산값을 대답했는데**, 기하는 **둘 다 0 으로 같다.** 기하는 상자가 있어야 존재한다.

```text
   한 상자에서 세 이름이 재는 칸

   +==========================================+  offsetWidth   230  (테두리 포함)
   |  테두리 5                                 |  rect.width  230.00  (같은 칸, 소수)
   |  +------------------------------------+  |
   |  |  패딩 10                            |  |  clientWidth   220  (테두리 뺀 안쪽, 스크롤바도 뺀다)
   |  |   +----------------------------+   |  |
   |  |   |  내용 200                   |   |  |  scrollWidth   220  (넘치면 넘친 만큼)
   |  |   +----------------------------+   |  |
   |  +------------------------------------+  |
   +==========================================+
      마진은 어느 이름에도 안 들어 있다 (CSS 15번)
```

### (8) 정수인가 소수인가

**언제 쓰나** — 두 수를 빼서 간격을 구할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '11,18p'
정수인가 소수인가 — #frac 은 width 100.6 · padding 3.3 · border 2.2
  offsetWidth = 111   (Number.isInteger = true)
  rect.width  = 111.1875   (같은 상자를 잰 값이다)
  offsetTop   = 401   rect.top = 400.59375

transform 은 어느 쪽에 섞이나
  #tr  scale(2)      offsetWidth = 230   rect.width = 460.00
  #rot rotate(45deg) offsetWidth = 230   rect.width = 226.27   rect.left = 9.86 (축 정렬 외접 상자다)
(exit 0)
```

- **`offsetWidth` 는 `111`, `rect.width` 는 `111.1875`** 다. **같은 상자인데 눈금이 다르다** — `offset*` 계열은 **정수로 반올림**해서 준다.
- **`offsetTop` 은 `401`, `rect.top` 은 `400.59375`** 다. **반올림 방향이 다를 수 있으니** 두 계열을 섞어 빼면 **1px 이 조용히 생기거나 사라진다.**
- ★ **간격·정렬처럼 뺄셈이 들어가는 계산은 `rect` 로만** 한다. 섞지 않는다.

### (9) `transform` 은 한쪽에만 섞인다

**언제 쓰나** — 애니메이션이 걸린 요소의 치수를 읽을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa09b-09-box.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '20,27p'
상자 하나가 아닌 것 — 줄을 넘긴 인라인
  getClientRects().length = 3   getBoundingClientRect().height = 60.00   (첫 조각 높이 = 20.00)
  .box 하나는 getClientRects().length = 1

돌려받는 객체
  타입 = [object DOMRect]   두 번 부르면 === ? false
  JSON.stringify = {"x":8,"y":8,"width":230,"height":90,"top":8,"right":238,"bottom":98,"left":8}
  마진을 바꾼 뒤 붙들고 있던 옛 객체의 left = 8.00   새로 부른 것의 left = 100.00  ← 스냅숏이다
(exit 0)
```

- **`scale(2)` 인데 `offsetWidth` 는 `230` 그대로**이고 **`rect.width` 는 `460.00`** 이다. **`transform` 은 레이아웃을 안 바꾸므로**([CSS 54번 주제](../../languages/css/syntax/54-transform-2d-and-origin/2-summary.md)) `offset*` 에 안 나타난다.
- **`rotate(45deg)` 는 `rect.width` 가 `226.27`** 이다 — 기울어진 상자의 **축 정렬 외접 상자**를 준다. **기울인 상자의 변 길이가 아니다.**
- **줄을 넘긴 인라인 요소**는 **상자가 하나가 아니다** — `getClientRects().length` 가 **3** 이고, `getBoundingClientRect()` 는 그 셋을 **전부 감싸는 하나**를 준다(높이 60 = 20 × 3).
- **돌려받는 `DOMRect` 는 스냅숏**이다 — 붙들고 있던 옛 객체는 마진을 바꿔도 `8.00` 그대로고, 새로 부른 것만 `100.00` 이다. ★ [08번 주제](../08-getcomputedstyle/2-summary.md)의 계산값 객체가 **라이브였던 것과 정반대**다.

```text
   두 계열이 갈리는 자리 한 장

                       offsetWidth    rect.width
   보통 상자                230          230.00     같다
   scale(2)                 230          460.00     ★ rect 에만 섞인다
   rotate(45deg)            230          226.27     ★ 외접 상자를 준다
   소수 폭                  111          111.1875   ★ 눈금이 다르다
   display: none              0            0.00     둘 다 없다
```

비용 — `getClientRects()` 도 `getBoundingClientRect()` 와 같은 값의 레이아웃 강제다([목록의 **10번 주제**](../10-layout-thrashing/) 실측).

### (10) 읽어서 무엇을 하나 — 화면 안에 있나

**언제 쓰나** — 「보이나」를 판정할 때. **이 주제의 값을 실제로 쓰는 자리다.**

```html demo
<div id="d9box">이 상자를 재 본다</div>
<button id="d9btn">아래로 400px 굴리기</button>
<div id="d9out"></div>
<div id="d9pad"></div>
<style>
  #d9box { width: 160px; height: 40px; background: #a7f3d0; border: 4px solid #065f46; }
  #d9out { font-family: monospace; white-space: pre; background: #0f172a; color: #e2e8f0; padding: 8px; margin-top: 6px; }
  #d9pad { height: 1200px; }
</style>
<script>
  const b = document.getElementById('d9box');
  const 보이기 = () => {
    const r = b.getBoundingClientRect();
    document.getElementById('d9out').textContent =
      'rect.top      = ' + r.top.toFixed(2) + '   (뷰포트 기준 — 굴리면 변한다)\n' +
      'offsetTop     = ' + b.offsetTop + '   (offsetParent 기준 — 안 변한다)\n' +
      'offsetParent  = ' + (b.offsetParent ? b.offsetParent.tagName : 'null') + '\n' +
      'offsetWidth   = ' + b.offsetWidth + '   rect.width = ' + r.width.toFixed(4) + '\n' +
      'window.scrollY= ' + Math.round(window.scrollY);
  };
  document.getElementById('d9btn').onclick = () => { window.scrollBy(0, 400); 보이기(); };
  addEventListener('scroll', 보이기);
  보이기();
</script>
```

> **보이는 것** — 검은 칸 첫 줄의 `rect.top` 은 상자가 지금 창의 위에서 몇 px 아래인지를 소수까지 보여 주고, 둘째 줄의 `offsetTop` 은 정수다.\
> 버튼을 누르면 페이지가 400px 내려가면서 **첫 줄만 400 줄어든다** — `offsetTop` 도 `offsetParent` 도 `offsetWidth` 도 **한 글자도 안 변한다**.\
> 넷째 줄은 같은 상자를 잰 두 수가 **`168` 과 `168.0000`** 으로 눈금만 다른 것을 나란히 보여 준다.\
> **바꿔 볼 것** — `#d9box` 에 `transform: scale(2)` 를 주면 **`rect.width` 만 두 배가 된다**(`offsetWidth` 는 그대로) · `#d9box` 의 부모에 `position: relative` 를 주면 **`offsetParent` 와 `offsetTop` 이 같이 바뀐다** · 상자에 `display: none` 을 주면 **다섯 줄이 전부 0 과 `null` 이 된다**

*(Chrome 151 headless 실측 — `--window-size=1000,800`: 초기 `rect.top` 8.00 · `offsetTop` 8 · `offsetParent` BODY · `offsetWidth` 168 · `rect.width` 168.0000, 버튼 한 번 뒤 `rect.top` −392.00 · `offsetTop` 8 그대로 · `scrollY` 400)*

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
// 뷰포트 기준 — 소수, transform 반영, 스냅숏
const r = el.getBoundingClientRect();
r.top  r.left  r.right  r.bottom  r.width  r.height  r.x  r.y
el.getClientRects()                  // 줄을 넘긴 인라인은 조각이 여럿이다

// offsetParent 기준 — 정수, transform 안 섞임
el.offsetParent  el.offsetTop  el.offsetLeft  el.offsetWidth  el.offsetHeight

// 자기 안쪽 — 패딩 상자와 스크롤
el.clientTop  el.clientLeft  el.clientWidth  el.clientHeight   // 테두리·스크롤바 제외
el.scrollTop  el.scrollLeft  el.scrollWidth  el.scrollHeight   // 안쪽 내용

// 창 쪽
window.scrollX  window.scrollY
document.documentElement.clientWidth   // 뷰포트 폭 (스크롤바 제외)
document.elementFromPoint(x, y)        // ★ 뷰포트 좌표를 받는다
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// 1. offsetTop 을 문서 좌표로 쓴다 — offsetParent 가 바뀌면 조용히 틀린다
const y = el.offsetTop;                        // 기준이 무엇인지 모르는 수
let y2 = 0, e = el;                            // 이것이 문서 좌표다
while (e.offsetParent) { y2 += e.offsetTop; e = e.offsetParent; }

// 2. rect 와 offset 을 섞어 뺀다 — 반올림이 다르다
const 간격 = b.offsetTop - a.getBoundingClientRect().top;   // 1px 이 생기거나 사라진다
const 간격2 = b.getBoundingClientRect().top - a.getBoundingClientRect().top;

// 3. elementFromPoint 에 문서 좌표를 넣는다 — 굴리면 엉뚱한 요소가 나온다
document.elementFromPoint(문서x, 문서y);
document.elementFromPoint(문서x - scrollX, 문서y - scrollY);

// 4. transform 이 걸린 요소의 크기를 offsetWidth 로 읽는다 — 변환 전 크기다
el.offsetWidth;                                 // scale(2) 여도 그대로
el.getBoundingClientRect().width;               // 이것이 화면에 그려진 폭

// 5. 「보이나」를 offsetWidth 로 판정한다 — display:none 만 잡힌다
if (el.offsetWidth > 0) { }                     // 뷰포트 밖도 opacity:0 도 못 잡는다
if (el.checkVisibility()) { }                   // 목록의 35번 주제(IntersectionObserver)가 정본

// 6. rect 를 붙들어 두고 나중에 읽는다 — 스냅숏이라 안 따라온다
const r = el.getBoundingClientRect();
el.style.marginLeft = '100px';
r.left;                                         // 옛 값이다
```

### 어디서 헷갈리나

- **`offsetWidth` 와 `clientWidth`** — 앞은 **테두리 포함**, 뒤는 **테두리·스크롤바 제외**.
- **`scrollTop` 과 `offsetTop`** — 이름이 닮았지만 **하나는 내 안쪽, 하나는 내 위치**다.
- **`scrollWidth` 와 `clientWidth`** — 넘치는 내용이 없으면 **둘이 같다.** 같다고 해서 같은 뜻이 아니다.
- **`rect.top` 과 `rect.y`** — 이 주제에서는 같다. `width`/`height` 가 음수일 수 있는 `DOMRect` 일반에서는 갈린다.

## 어디서 틀리나

### 1. `offsetTop` 을 문서 좌표로 쓴다

실측에서 **같은 요소가 `95` 와 `5`** 로 갈렸다. 중간 조상에 `position: relative` 한 줄이 생기면 끝이다. **CSS 를 고쳤는데 JS 가 틀린다.**

### 2. 스크롤이 0 인 채로 확인하고 넘어간다

창 ④ 실측에서 **스크롤 전에는 두 좌표가 같은 요소를 가리켰다.** 굴려 보지 않으면 틀린 코드가 통과한다.

### 3. `rect` 와 `offset` 을 섞어서 뺀다

실측에서 **`offsetTop` 401 · `rect.top` 400.59375** 였다. 두 계열을 섞으면 **1px 이 조용히 생긴다.**

### 4. `transform` 이 걸린 요소를 `offsetWidth` 로 잰다

실측에서 **`scale(2)` 인데 `offsetWidth` 는 230 그대로**였다. 화면의 폭은 460 이다.

### 5. `rotate` 된 요소의 `rect.width` 를 「폭」으로 읽는다

**축 정렬 외접 상자**다. 실측에서 100×100 정사각형이 45도 돌자 `226.27`(테두리 포함) 이 나왔다.

### 6. `display: none` 인 요소의 치수를 읽고 계산한다

**전부 0 이다.** [08번 주제](../08-getcomputedstyle/2-summary.md)의 계산값은 `"200px"` 이라고 대답했는데 기하는 0 이다 — **두 창구의 답이 다르다.**

### 7. 루프 안에서 읽는다

이 주제의 모든 읽기가 **강제 동기 레이아웃**을 부른다. 고치는 법은 [목록의 **10번 주제**](../10-layout-thrashing/)가 정본이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `getBoundingClientRect()` 가 **뷰포트 기준**인 것 | **명세**(CSSOM View) |
| `rect` 가 **`transform` 을 반영**하고 축 정렬 외접 상자인 것 | **명세**(CSSOM View — transformed border box) |
| `offsetParent` 의 판정 절차(`static` 건너뛰기 · `fixed` 는 `null` · `body`/`html` 은 `null`) | **명세**(CSSOM View) |
| `offset*` 이 **정수로 반올림**되는 것 | **명세**(CSSOM View 가 `long` 으로 정의한다) |
| `clientWidth` 가 **패딩 상자에서 스크롤바를 뺀** 것 | **명세**(CSSOM View) |
| `display: none` 과 트리 밖에서 **전부 0** 인 것 | **명세**(CSSOM View — 상자가 없으면 0) |
| `elementFromPoint` 가 **뷰포트 좌표**를 받고 밖이면 `null` 인 것 | **명세**(CSSOM View) |
| `DOMRect` 가 **스냅숏**인 것 | **명세**(반환값은 새 객체다) |
| **스크롤바가 먹는 15px** | **구현 + 플랫폼 설정.** 겹침 스크롤바인 환경에서는 0 이다 |
| **모든 절대 좌표** | **구현 + 창 크기.** 그래서 배너에 `--window-size` 를 박았다 |
| 인라인 조각의 폭(`97.28` 류) | **이 머신의 글꼴 치수** |
| 소수의 자릿수(`111.1875` = 1/16 단위) | **구현.** Blink 가 레이아웃 단위를 1/64px 로 쓰고 그것이 반올림돼 나온다 — **명세는 소수라는 것까지만 정한다** |

- ★ **「소수점이 1/16 단위로 떨어진다」는 관찰이지 보장이 아니다.** 명세는 `double` 이라고만 한다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 「지금 화면 어디에 있나」 | `getBoundingClientRect()` | `offsetTop` |
| 두 요소의 간격 | `rect` 끼리 빼기 | `rect` 와 `offset` 섞기 |
| 변환이 걸린 요소의 실제 크기 | `rect.width` | `offsetWidth` |
| 변환을 뺀 레이아웃 크기 | `offsetWidth` | `rect.width` |
| 스크롤 여유가 얼마나 남았나 | `scrollHeight - clientHeight` | `offsetHeight` |
| 안쪽에 쓸 수 있는 폭 | `clientWidth` | `offsetWidth`(테두리·스크롤바가 낀다) |
| 「이 점에 무엇이 있나」 | `elementFromPoint`(뷰포트 좌표) | offset 누적 좌표 |
| 「화면에 보이나」 | 목록의 **35번 주제**(IntersectionObserver) | `offsetWidth > 0` |
| 값을 나중에 다시 쓸 때 | 그때 다시 읽는다 | `rect` 를 붙들어 두기 |
| 여러 요소를 잰다 | 읽기를 **한 묶음으로** 모은다 | 쓰기와 번갈아([목록의 **10번 주제**](../10-layout-thrashing/)) |

## 핵심 문장

1. **세 묶음은 자가 아니라 원점이 다르다** — `rect` 는 뷰포트, `offset*` 은 `offsetParent`, `scrollTop` 은 자기 내용.
2. **스크롤은 `rect` 만 움직인다.** `offsetTop` 은 배치가 바뀌어야 움직인다.
3. **`offsetTop` 은 기준을 모르면 뜻이 없다** — 실측에서 `position` 한 줄에 `95` 와 `5` 로 갈렸다.
4. **`offsetWidth` 는 정수, `rect.width` 는 소수다.** 섞어 빼면 1px 이 생긴다.
5. **`transform` 은 `rect` 에만 섞인다.** 그리고 회전하면 **외접 상자**가 온다.
6. **`display: none` 과 트리 밖은 전부 0 이다** — 계산값 창구와 답이 다르다.
7. **읽은 좌표는 도로 넣어 봐야 안다** — 스크롤이 0 이면 틀린 좌표도 맞아 보인다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 09번)
- [08번 주제](../08-getcomputedstyle/2-summary.md) — `getComputedStyle`. **그쪽은 「무엇이 선언됐나」, 여기는 「그래서 어떤 상자가 놓였나」**. 08 의 창 ④ 가 이 주제를 미리 빌려 갔다
- [10번 주제](../10-layout-thrashing/2-summary.md) — 이 주제의 읽기가 **얼마나 비싼가**. 고치는 법은 그쪽이 정본
- [11번 주제](../11-scroll-control/2-summary.md) — `scrollTop` 을 **읽는 것**까지가 여기, **굴리는 것**은 그쪽
- [01번 주제](../01-document-and-node-tree/2-summary.md) — 관측 3창의 정본
- 목록의 **35번 주제**(IntersectionObserver) — 「보이나」를 **폴링 없이** 묻는 법. 이 주제의 좌표 계산을 대신한다
- 목록의 **36번 주제**(ResizeObserver) — 치수가 **언제 바뀌었나**를 묻는 법
- [CSS 15번 주제](../../languages/css/syntax/15-box-model-and-box-sizing/2-summary.md) — ★ **이 주제의 정본 이웃.** 네 겹 상자와 `box-sizing`, `rect.width` 가 재는 칸의 정의가 거기다. **여기서 다시 쓰지 않는다**
- [CSS 21번 주제](../../languages/css/syntax/21-position-and-containing-block/2-summary.md) — `position` 과 포함 블록. **`offsetParent` 와 포함 블록은 닮았지만 다르다**(그쪽은 `%` 와 `top` 의 기준, 여기는 `offsetTop` 의 기준)
- [CSS 23번 주제](../../languages/css/syntax/23-overflow-and-scroll-containers/2-summary.md) — 스크롤 컨테이너와 **스크롤바가 먹는 15px**. `clientWidth` 가 줄어드는 근거가 거기다
- [CSS 54번 주제](../../languages/css/syntax/54-transform-2d-and-origin/2-summary.md) — `transform` 이 **레이아웃을 안 바꾼다**는 것. 이 주제의 (9)가 그 사실의 API 쪽 그림자다
- [CSS 56번 주제](../../languages/css/syntax/56-rendering-pipeline-and-will-change/2-summary.md) — 렌더링 파이프라인. 「읽기가 무엇을 되돌리나」의 배경
- [`../../../../history/web/04-브라우저-엔진.md`](../../../../history/web/04-브라우저-엔진.md) — 레이아웃 엔진의 계보. 「언제·왜」는 그쪽

## 용어 풀이

- **뷰포트(viewport)** — 지금 문서를 내다보는 창. `rect` 의 원점이고, 굴리면 문서 위를 미끄러진다.
- **`offsetParent`** — `offsetTop`/`offsetLeft` 의 기준이 되는 조상. **`position` 이 `static` 이 아닌 가장 가까운 조상**이고 없으면 `body` 다.
- **테두리 상자(border box)** — 내용 + 패딩 + 테두리. `offsetWidth` 와 `rect.width` 가 재는 칸.
- **패딩 상자(padding box)** — 내용 + 패딩. `clientWidth` 가 재는 칸(스크롤바는 뺀다).
- **`DOMRect`** — `getBoundingClientRect()` 가 돌려주는 객체. **스냅숏**이고 매번 새것이다.
- **축 정렬 외접 상자(axis-aligned bounding box)** — 기울어진 도형을 **가로·세로에 나란한 사각형 하나**로 감싼 것. `rotate` 된 요소의 `rect` 가 이것이다.
- **히트 테스트(hit testing)** — 어떤 점 위에 어느 요소가 있는지 찾는 일. `elementFromPoint` 가 하는 것.
- **강제 동기 레이아웃(forced synchronous layout)** — 쓰기로 더러워진 레이아웃을 읽기가 그 자리에서 다시 계산하게 만드는 것. 이 주제의 모든 읽기가 방아쇠다([목록의 **10번 주제**](../10-layout-thrashing/)).
- **초기 포함 블록(initial containing block)** — 문서의 맨 바깥 기준 상자. `fixed` 요소의 좌표가 이것을 기준으로 잰 값이다.

## 더 들어가면

- **`DOMRectReadOnly` 와 `DOMRect`** — `getBoundingClientRect()` 가 돌려주는 것은 쓸 수 있는 `DOMRect` 지만, **고쳐 봐야 요소는 안 움직인다**(스냅숏이라서). 이 문서는 **고쳐 보지 않았다** — 표면만 적는다.
- **`el.getBoundingClientRect()` 대 `el.getBoxQuads()`** — 뒤엣것은 **변환을 거치지 않은 네 꼭짓점**을 준다. 회전한 요소의 진짜 모서리를 알 수 있지만 **Chromium 한정**이라 이 목록에서는 다루지 않는다(**던져 보지 않았다**).
- **`scrollTop` 이 소수를 받나** — [목록의 **11번 주제**](../11-scroll-control/)에서 실측했다. 이 주제에서는 **읽는 쪽만** 다뤘다.
- **`visualViewport`** — 모바일에서 키보드가 올라오거나 핀치 줌을 하면 **레이아웃 뷰포트와 시각 뷰포트가 갈린다.** `rect` 는 레이아웃 뷰포트 기준이다. **이 판에서는 둘이 같아 갈라 볼 수 없었다**(못 잰 것).
- **`offsetWidth` 가 IE 에서 왔다는 것** — CSSOM View 는 이미 퍼진 구현을 사후에 적어 놓은 명세다. 그래서 **`offset*` 만 정수**인 것 같은 어긋남이 남아 있다. 경위는 [`../../../../history/web/04-브라우저-엔진.md`](../../../../history/web/04-브라우저-엔진.md) 의 몫이다.
