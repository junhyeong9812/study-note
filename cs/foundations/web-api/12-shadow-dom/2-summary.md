# web-api/12 — Shadow DOM: `attachShadow`·캡슐화 경계·슬롯 할당·`::part` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★ **마크업 갈래와의 경계** — HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **10번** 이 `template`·`slot`·선언적 Shadow DOM 을 **마크업으로** 다룬다. 거기가 「파서가 무엇을 만드나」의 정본이고, **여기는 「그것을 스크립트로 만들고 들여다보는 API」** 다. 그 편이 이미 보인 것(`<template>` 이 왜 안 사나 · `shadowrootmode` 의 세 값 · `getHTML` 의 `serializableShadowRoots`)은 **다시 쓰지 않고 인용만** 한다.\
> **기준 소스** — [WHATWG DOM Standard](https://dom.spec.whatwg.org/) 의 「Interface `ShadowRoot`」·「`attachShadow`」·「Signal slots」·「Dispatching events」(재타기팅) 절과 [CSS Scoping Module Level 1](https://drafts.csswg.org/css-scoping/) 의 `:host`·`:host-context`·`::part`·`exportparts` 절. 열어서 확인한 것만 적었다.\
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 `--dump-dom` 으로 실제로 받은 것이다. 블록마다 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다.\
> **엔진은 Chrome 하나다** — Firefox 는 이 환경에서 headless 산출이 조용히 실패하고 WebKit 은 없다. **이식성을 주장하지 않는다.**\
> **버전** — 웹 플랫폼 API 에는 언어 버전이 없다. `attachShadow` 는 오래된 표면이고, **`slotAssignment: 'manual'`·`serializable`·`getHTML()` 은 새 표면**이다(아래 「구현 세부사항 대 언어 보장」).\
> **선행** — [01번 주제](../01-document-and-node-tree/2-summary.md)(노드 트리)와 [05번 주제](../05-documentfragment-and-template/2-summary.md)(`DocumentFragment` 와 `<template>`).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

**★ 이 주제에는 흔들리는 칸이 거의 없다** — 시간도 좌표도 거의 안 재기 때문이다.

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 모든 조회 결과 · `mode` · `assignedNodes` 의 내용과 순서 · 계산값 색 · `composedPath()` 의 길이와 내용 · 예외 이름과 메시지 | 같은 판이면 결정적이다. **두 판을 돌려 95블록이 한 글자도 같았다** |
| **흔들린다** | `getBoundingClientRect().width` 의 **소수점**(`97.28` · `112.02`) | 글꼴과 창 크기에 달렸다. 이 문서는 **0 인가 아닌가만** 근거로 쓴다 |
| **흔들린다** | Chrome 판 번호와 예외 **메시지 문구** | 판이 오르면 바뀐다. **예외의 「이름」은 명세가 정하고 「문구」는 구현이 정한다** |
| **부적용** | `--dump-dom` 트리로 그림자 속을 보는 것 | 「재 봤더니 같았다」가 아니라 **잴 것이 없다** — (1)이 그 실측이다 |
| **못 잰다** | 스크린리더가 슬롯된 내용을 **어떤 순서로 읽는지** | 접근성 트리를 떠 봐도 **보조 기술의 출력은 아니다**(아래 「도구가 못 보는 것」) |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

## 한눈에 — 쉽게 말하면

**★ 그림자는 「숨기는 것」이 아니라 「이름을 따로 쓰는 방」이다. 그래서 막히는 것은 이름으로 찾는 길뿐이고, 손에 쥔 참조는 그대로 통한다.**

호텔 객실에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| 객실 안에 **따로 붙인 방 번호표** | 그림자 안의 `id`·class — 로비의 안내판에는 안 올라간다 |
| **로비 안내판으로는 객실 안을 못 찾는다** | `document.querySelector` 가 경계를 안 넘는다 |
| **객실에서 로비 간판도 못 읽는다** | 그림자 안 선택자도 바깥을 안 본다 — 막힘이 양방향이다 |
| 그런데 **열쇠를 쥐고 있으면 들어간다** | `attachShadow` 의 반환값·`shadowRoot`·`getRootNode().host` |
| `open` 은 **프런트에 열쇠 사본을 맡긴 것** | `host.shadowRoot` 가 루트를 준다 |
| `closed` 는 **사본을 안 맡긴 것** | `host.shadowRoot` 가 `null` — 내 열쇠는 그대로 쓸 수 있다 |
| 객실 **난방은 복도에서 흘러든다** | 상속되는 CSS 속성은 경계를 넘어온다 |
| 객실 **벽지는 복도 것이 안 온다** | 상속 안 되는 속성(`border` 등)은 안 온다 |
| 문에 낸 **작은 창구 하나** | `::part` — 호스트가 허락한 이름만 바깥에서 꾸민다 |
| 로비 짐을 **객실에서 보이게 놓아 주는 선반** | `<slot>` — 짐은 로비에 그대로 있고 자리만 빌려 준다 |
| 누가 **문을 두드렸다고만 전한다** | 이벤트 재타기팅 — 바깥에서는 `target` 이 호스트다 |

```text
   한 문서 안에 나무가 둘 있다

   document
     └ BODY
        └ #host          <- 라이트 DOM (바깥에서 보이는 나무)
             └ #라이트     이 아이는 바깥 규칙·바깥 선택자를 그대로 받는다

   #host.shadowRoot      <- 그림자 DOM (따로 사는 나무)
     ├ <p id="안문단">      바깥에서 이름으로는 못 찾는다
     └ <slot>              #라이트 가 여기에 '비친다' (옮겨지지 않는다)

   두 나무는 parentNode 로 이어져 있지 않다 — root.parentNode 는 null 이다
```

## 이 주제가 답하려는 질문

1. **경계가 정확히 무엇을 막나** — 선택자인가, 참조인가, 스타일인가, 이벤트인가. **막는 것과 안 막는 것을 전수로 가른다.**
2. **`closed` 가 무엇을 더 막나** — 「보안 장치」라는 말이 어디까지 참인가.
3. **슬롯에 배정된 자식은 어느 나무에 사나** — 옮겨지는 것인가 비치는 것인가.

## 이 갈래의 관측 창 — ★ 본체는 창 ④ 다

**★ 이 주제의 본체는 창 ④(「참조를 들고 경계를 넘어가 묻기」)다.** 창 ① 은 이 주제에서 **부적용**이다 — 그림자 속을 한 글자도 안 보여 준다(그것이 (1)의 결론이다).

[01번 주제](../01-document-and-node-tree/2-summary.md)가 세운 창 셋에 이 주제의 창을 하나 더 얹는다.

```text
  창 1  --dump-dom            스크립트가 다 돈 뒤의 트리를 글자로
        ★ 부적용 — outerHTML 은 그림자를 직렬화하지 않는다. '없다' 가 아니라 '안 보인다'
  창 2  노드 단위 프로브        shadowRoot.innerHTML · assignedNodes() · getRootNode()
  창 3  같은 것을 두 번 읽기    바깥에서 한 번 / 경계 안에서 한 번 — 답이 갈리면 그것이 경계다
  ★ 창 4 (이 주제의 본체)  참조를 들고 경계를 넘어가 묻기
        무엇을 답하나:  '무엇이 막히나' 가 아니라 '무엇이 안 막히나'
        무엇을 요구하나: 허락 — 열쇠(attachShadow 의 반환값 또는 open 의 shadowRoot)
        왜 필요한가:    바깥에서만 물으면 'null' 이 두 가지를 뜻한다 —
                        '없다' 와 '경계 밖이라 안 보인다'. 이 둘은 창 ④ 로만 갈린다
  ★ 부적용인 창  --dump-dom 트리 · outerHTML · getHTML() 의 기본값
        재 봤더니 같았던 것이 아니라 '잴 것이 없다' — 직렬화 대상이 아니다
```

- ★ **창 ④ 가 요구하는 것은 「허락」이다.** `open` 이면 프런트(호스트)가 열쇠를 내주고, `closed` 면 **내가 만들 때 받아 둔 열쇠**만 통한다. 남이 만든 `closed` 그림자는 페이지 스크립트가 다시 잡을 방법이 없다(HTML 갈래의 **10번** 이 그 실측이다).
- ★ **제5의 상태를 조심하라** — 「세 창이 전부 정상인데 기준만 다른 것」. `::part` 규칙은 `cssRules` 에 **담기고**, 선택자 문법도 **맞고**, 계산값도 **나온다.** 그런데 `part` 이름이 틀리면 아무것도 안 잡는다((9)).

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| **스크린리더가 슬롯된 내용을 어떤 순서로 읽는지** | 접근성 트리는 보조 기술의 **입력**이지 출력이 아니다. 「트리에 이렇게 있다」와 「이렇게 읽힌다」는 다른 문장이다 |
| 남이 만든 `closed` 그림자의 속 | 원리상 못 본다. **그것이 이 API 의 목적**이다 |
| 실제 칠해진 픽셀 | 이 문서는 `getComputedStyle` 과 `getBoundingClientRect` 까지만 본다 |
| 다른 엔진의 동작 | 엔진이 하나뿐이다 |
| 그림자가 만드는 **비용** | 재지 않았다. 이 문서는 성능을 한 줄도 주장하지 않는다 |

## 동작 방식

### (1) 창 ① 은 그림자를 한 글자도 못 본다

**언제 쓰나** — 「그림자가 생겼나」를 확인하려 할 때. **여기서 처음 넘어진다.**

**던진 것** — 아래 (2)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-12-tree.html -->
<!doctype html>
<meta charset="utf-8">
<title>12-tree</title>
<div id="열림"></div>
<div id="닫힘"></div>
<div id="선언"><template shadowrootmode="open"><b>선언적</b></template><span>라이트 자식</span></div>
<div id="직렬화"></div>
<script>
const O = [];
const J = v => JSON.stringify(v);
const $ = id => document.getElementById(id);
$('열림').attachShadow({ mode: 'open' }).innerHTML = '<b>스크립트로 만든 것</b>';
$('닫힘').attachShadow({ mode: 'closed' }).innerHTML = '<b>닫힌 것</b>';
const 직 = $('직렬화').attachShadow({ mode: 'open', serializable: true });
직.innerHTML = '<b>직렬화를 허락한 것</b>';

O.push('창 ① 이 못 보는 것을 창 ④ 로 꺼내 온다');
O.push('  #열림.shadowRoot.innerHTML                    = ' + J($('열림').shadowRoot.innerHTML));
O.push('  #닫힘.shadowRoot                              = ' + $('닫힘').shadowRoot);
O.push('  #선언.shadowRoot.innerHTML                    = ' + J($('선언').shadowRoot.innerHTML));
O.push('  #선언.querySelector("template")               = ' + $('선언').querySelector('template'));
O.push('  #선언.childNodes                              = ' + [...$('선언').childNodes].map(n => n.nodeName).join(' '));
O.push('');
O.push('getHTML() 로 경계를 넘겨 직렬화하면');
O.push('  #열림.getHTML()                                = ' + J($('열림').getHTML()));
O.push('  #열림.getHTML({serializableShadowRoots: true}) = ' + J($('열림').getHTML({ serializableShadowRoots: true })));
O.push('  #열림.getHTML({shadowRoots: [열림의 root]})    = ' + J($('열림').getHTML({ shadowRoots: [$('열림').shadowRoot] })));
O.push('  #직렬화.getHTML({serializableShadowRoots:true}) = ' + J($('직렬화').getHTML({ serializableShadowRoots: true })));
O.push('  root.serializable — 열림 ' + $('열림').shadowRoot.serializable
     + ' · 직렬화 ' + 직.serializable + ' · 선언 ' + $('선언').shadowRoot.serializable);
O.push('  ★ 기본값이 false 라 「직렬화해도 되는가」를 따로 허락해야 나온다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-tree.html 2>/dev/null | sed -n '4,8p'
</head><body><div id="열림"></div>
<div id="닫힘"></div>
<div id="선언"><span>라이트 자식</span></div>
<div id="직렬화"></div>
<script>
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-tree.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,6p'
창 ① 이 못 보는 것을 창 ④ 로 꺼내 온다
  #열림.shadowRoot.innerHTML                    = "<b>스크립트로 만든 것</b>"
  #닫힘.shadowRoot                              = null
  #선언.shadowRoot.innerHTML                    = "<b>선언적</b>"
  #선언.querySelector("template")               = null
  #선언.childNodes                              = SPAN
(exit 0)
```

- **덤프의 `<body>` 줄에는 네 상자가 전부 비어 보인다.** `#열림`·`#닫힘`·`#직렬화` 는 빈 `<div>` 고, `#선언` 에는 라이트 자식인 `<span>` 만 남았다.
- ★ **`#선언` 의 `<template>` 이 통째로 사라졌다.** 파서가 그것을 먹어 섀도 루트로 바꿔 놓았기 때문이다 — **정본은 HTML 갈래의 10번** 이고 여기서는 API 쪽 확인만 한다(`querySelector('template')` 이 `null`).
- ★★ **「트리를 봤는데 없더라」는 근거가 안 된다.** `--dump-dom` 은 `outerHTML` 이고 **`outerHTML` 은 섀도 트리를 직렬화하지 않는다.** 이것은 「안 돌려 봤다」도 「못 쟀다」도 아니라 **「그 창이 부적용」** 인 경우다.
- **창 ② 로 물으면 곧바로 답이 나온다** — `shadowRoot.innerHTML` 이 안을 그대로 준다.
- **`#닫힘.shadowRoot` 만 `null`** 이다. 나머지 셋은 루트를 준다.

```text
   같은 '없다' 가 두 가지를 뜻한다

   document.querySelector('#안문단')  -> null    경계 밖이라 안 보인다
   host.shadowRoot                   -> null    (closed 일 때) 안 내준다
   host.shadowRoot                   -> null    (그림자가 아예 없을 때)

   ★ 세 번째만 진짜 '없다' 다. 앞 둘은 '안 보인다' 다 — 창 ④ 로만 갈린다
```

```text
   같은 상자를 두 창으로 물으면 답이 갈린다

   창 ①  --dump-dom          <div id="열림"></div>        <- 비어 보인다
   창 ②  shadowRoot.innerHTML "<b>스크립트로 만든 것</b>"   <- 들어 있다

   ★ 창 ① 의 '없다' 는 '직렬화 대상이 아니다' 라는 뜻이다
```

비용 — 창 ② 는 **문자열을 새로 만든다**(직렬화). 루프 안에서 부르지 마라([목록의 **10번 주제**](../10-layout-thrashing/)와 같은 이유다).

### (2) 창 ④ — 그림자를 글자로 다시 꺼내려면 허락이 필요하다

**언제 쓰나** — 서버 렌더·스냅숏·테스트에서 **그림자까지 포함한 HTML** 이 필요할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-tree.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '8,14p'
getHTML() 로 경계를 넘겨 직렬화하면
  #열림.getHTML()                                = ""
  #열림.getHTML({serializableShadowRoots: true}) = ""
  #열림.getHTML({shadowRoots: [열림의 root]})    = "<template shadowrootmode=\"open\"><b>스크립트로 만든 것</b></template>"
  #직렬화.getHTML({serializableShadowRoots:true}) = "<template shadowrootmode=\"open\" shadowrootserializable=\"\"><b>직렬화를 허락한 것</b></template>"
  root.serializable — 열림 false · 직렬화 true · 선언 false
  ★ 기본값이 false 라 「직렬화해도 되는가」를 따로 허락해야 나온다.
(exit 0)
```

- **`getHTML()` 의 기본값은 빈 문자열**이다. `#열림` 에 그림자가 분명히 있는데도 **아무것도 안 나온다.**
- ★ **`{serializableShadowRoots: true}` 만으로도 안 나온다.** 그 옵션은 「**직렬화해도 된다고 표시된** 루트를 포함하라」는 뜻이지 「전부 포함하라」가 아니다. 표시는 `attachShadow({serializable: true})` 또는 마크업의 `shadowrootserializable` 로 한다.
- ★★ **넷째 줄이 비는 이유가 그것이다** — `#열림` 의 `root.serializable` 이 `false` 다. `#직렬화` 만 `true` 이고 그 줄에서만 내용이 나왔다.
- ★ **허락을 건너뛰는 길이 하나 있다** — `{shadowRoots: [내가 들고 있는 root]}`. **참조를 이미 쥐고 있는 쪽에는 막을 것이 없기 때문**이다. 이것이 창 ④ 의 성격을 그대로 보여 준다.
- **꺼낸 문자열의 모양이 `<template shadowrootmode="open">…</template>`** 이다. 즉 **직렬화의 결과가 곧 선언적 Shadow DOM 의 마크업**이다 — 뱉은 것을 그대로 다시 파싱하면 같은 그림자가 선다.

```text
   getHTML() 이 그림자를 포함하는 조건

   getHTML()                                  -> ""            허락도 참조도 없다
   getHTML({serializableShadowRoots: true})   -> ""            허락이 없다
   getHTML({shadowRoots: [root]})             -> <template …>  참조가 있다
   serializable: true 로 만든 루트 + 위 옵션  -> <template …>  허락이 있다

   ★ 기본값이 '안 나옴' 이다. 캡슐화가 목적이므로 내보내기가 opt-in 이다
```

### (3) ★ 본체 — `open` 과 `closed` 가 실제로 갈리는 칸은 몇 개인가

**언제 쓰나** — 「`closed` 로 만들면 안전한가」를 판단할 때.

**던진 것** — 두 호스트의 속을 **한 글자도 같게** 두고 `mode` 만 바꿨다. 아래 (4)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-12-mode.html -->
<!doctype html>
<meta charset="utf-8">
<title>12-mode</title>
<style>
  body { color: rgb(0, 100, 0) }
  p { color: rgb(200, 0, 0) }
  #열림::part(핵심) { color: rgb(255, 0, 255) }
  #닫힘::part(핵심) { color: rgb(255, 0, 255) }
</style>
<div id="열림"></div>
<div id="닫힘"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null || n === undefined ? String(n) : (n.id ? '#' + n.id : (n.nodeName || String(n)));

// 두 호스트를 한 글자도 같은 내용으로 만든다 — 다른 것은 mode 뿐이다.
const 속만들기 = host => {
  const r = host.attachShadow({ mode: host.id === '열림' ? 'open' : 'closed' });
  r.innerHTML = '<p id="속" part="핵심">안쪽 문단</p><p id="민">part 없는 문단</p>'
              + '<i id="글씨">상속만 받는 것</i><button id="단추">안쪽 단추</button>';
  return r;
};
const ro = 속만들기($('열림')), rc = 속만들기($('닫힘'));
const 격자 = [];
const 칸 = (질문, a, b) => 격자.push([질문, a, b, a === b ? '같다' : '갈린다']);

칸('host.shadowRoot',
   $('열림').shadowRoot ? 'ShadowRoot 를 준다' : 'null',
   $('닫힘').shadowRoot ? 'ShadowRoot 를 준다' : 'null');
칸('root.mode (참조로)', ro.mode, rc.mode);
칸('root.host (참조로)', ro.host === $('열림') ? '호스트를 준다' : '?', rc.host === $('닫힘') ? '호스트를 준다' : '?');
칸('root.querySelector("p") (참조로)',
   ro.querySelector('p') ? '찾는다' : '못 찾는다', rc.querySelector('p') ? '찾는다' : '못 찾는다');
칸('document.querySelector("#속")',
   document.querySelector('#속') ? '찾는다' : '못 찾는다', document.querySelector('#속') ? '찾는다' : '못 찾는다');
칸('안쪽요소.getRootNode().host (참조로)',
   ro.getElementById('속').getRootNode().host === $('열림') ? '호스트를 준다' : '?',
   rc.getElementById('속').getRootNode().host === $('닫힘') ? '호스트를 준다' : '?');
const cs = el => getComputedStyle(el);
칸('바깥 시트의 p 규칙이 닿나 (#민)',
   cs(ro.getElementById('민')).color === 'rgb(200, 0, 0)' ? '닿는다' : '안 닿는다',
   cs(rc.getElementById('민')).color === 'rgb(200, 0, 0)' ? '닿는다' : '안 닿는다');
칸('body 의 color 가 상속되나 (#글씨)',
   cs(ro.getElementById('글씨')).color, cs(rc.getElementById('글씨')).color);
칸('::part(핵심) 이 닿나',
   cs(ro.getElementById('속')).color === 'rgb(255, 0, 255)' ? '닿는다' : '안 닿는다',
   cs(rc.getElementById('속')).color === 'rgb(255, 0, 255)' ? '닿는다' : '안 닿는다');
ro.getElementById('단추').focus();
const ao = document.activeElement === $('열림') ? '호스트를 준다' : 이름(document.activeElement);
const aro = ro.activeElement === ro.getElementById('단추') ? '안쪽 단추를 준다' : String(ro.activeElement);
rc.getElementById('단추').focus();
const ac2 = document.activeElement === $('닫힘') ? '호스트를 준다' : 이름(document.activeElement);
const arc = rc.activeElement === rc.getElementById('단추') ? '안쪽 단추를 준다' : String(rc.activeElement);
칸('focus 뒤 document.activeElement', ao, ac2);
칸('focus 뒤 root.activeElement (참조로)', aro, arc);
const 받기 = (root, host) => {
  let 본것 = {};
  const h = e => { 본것 = { t: e.target === host ? '호스트로 바뀐다' : 이름(e.target), p: e.composedPath().length }; };
  document.addEventListener('시험', h);
  root.getElementById('단추').dispatchEvent(new CustomEvent('시험', { bubbles: true, composed: true }));
  document.removeEventListener('시험', h);
  return 본것;
};
const eo = 받기(ro, $('열림')), ec = 받기(rc, $('닫힘'));
칸('문서 리스너가 본 e.target', eo.t, ec.t);
칸('문서 리스너가 본 composedPath 길이', eo.p + ' 칸', ec.p + ' 칸');
const 점 = host => {
  const r = host.getBoundingClientRect();
  const el = document.elementFromPoint(r.left + 4, r.top + 4);
  return el === host ? '호스트를 준다' : 이름(el);
};
칸('elementFromPoint 가 무엇을 주나', 점($('열림')), 점($('닫힘')));
칸('host.getHTML({shadowRoots:[root]})',
   $('열림').getHTML({ shadowRoots: [ro] }).includes('안쪽 문단') ? '보인다' : '안 보인다',
   $('닫힘').getHTML({ shadowRoots: [rc] }).includes('안쪽 문단') ? '보인다' : '안 보인다');
칸('root.serializable', String(ro.serializable), String(rc.serializable));

O.push('open 과 closed 가 실제로 갈리는 칸은 몇 개인가');
O.push(padw('무엇을 물었나', 42) + padw('open', 22) + padw('closed', 22) + '판정');
격자.forEach(r => O.push(padw(r[0], 42) + padw(r[1], 22) + padw(r[2], 22) + r[3]));
O.push('');
O.push('갈린 칸 = ' + 격자.filter(r => r[3] === '갈린다').length + ' / ' + 격자.length);
O.push('');
O.push('★ closed 가 막는 것은 「host 에서 root 로 가는 길」과 「composedPath 가 안을 보여 주는 것」 둘뿐이다.');
O.push('  attachShadow 의 반환값을 들고 있으면 안을 고쳐 쓸 수 있다: '
     + rc.getElementById('속').textContent + ' -> '
     + (rc.getElementById('속').textContent = '닫힌 쪽(고쳐 씀)'));
O.push('');
O.push('attachShadow 가 거절하는 자리 — 이 주제에서 조용하지 않은 유일한 곳');
const 잡기 = fn => { try { fn(); return '예외 없음'; } catch (e) { return e.name + ' 「' + e.message + '」'; } };
O.push('  이미 붙은 호스트에 또  = ' + 잡기(() => $('열림').attachShadow({ mode: 'open' })));
O.push('  mode 를 안 주면        = ' + 잡기(() => document.createElement('div').attachShadow({})));
O.push('  인자를 아예 안 주면    = ' + 잡기(() => document.createElement('div').attachShadow()));
O.push('  mode 가 모르는 값이면  = ' + 잡기(() => document.createElement('div').attachShadow({ mode: 'zzz' })));
O.push('');
O.push('호스트가 될 수 있는 요소는 정해져 있다');
const 된다 = [], 안된다 = [];
for (const t of ['div', 'span', 'p', 'h1', 'section', 'my-el', 'input', 'br', 'table', 'button', 'img']) {
  try { document.createElement(t).attachShadow({ mode: 'open' }); 된다.push('<' + t + '>'); }
  catch (e) { 안된다.push('<' + t + '> ' + e.name); }
}
O.push('  되는 것   = ' + 된다.join(' · '));
O.push('  안 되는 것 = ' + 안된다.join(' · '));
O.push('  <img> 가 거절될 때의 말 = ' + 잡기(() => document.createElement('img').attachShadow({ mode: 'open' })));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-mode.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,23p'
open 과 closed 가 실제로 갈리는 칸은 몇 개인가
무엇을 물었나                             open                  closed                판정
host.shadowRoot                           ShadowRoot 를 준다    null                  갈린다
root.mode (참조로)                        open                  closed                갈린다
root.host (참조로)                        호스트를 준다         호스트를 준다         같다
root.querySelector("p") (참조로)          찾는다                찾는다                같다
document.querySelector("#속")             못 찾는다             못 찾는다             같다
안쪽요소.getRootNode().host (참조로)      호스트를 준다         호스트를 준다         같다
바깥 시트의 p 규칙이 닿나 (#민)           안 닿는다             안 닿는다             같다
body 의 color 가 상속되나 (#글씨)         rgb(0, 100, 0)        rgb(0, 100, 0)        같다
::part(핵심) 이 닿나                      닿는다                닿는다                같다
focus 뒤 document.activeElement           호스트를 준다         호스트를 준다         같다
focus 뒤 root.activeElement (참조로)      안쪽 단추를 준다      안쪽 단추를 준다      같다
문서 리스너가 본 e.target                 호스트로 바뀐다       호스트로 바뀐다       같다
문서 리스너가 본 composedPath 길이        7 칸                  5 칸                  갈린다
elementFromPoint 가 무엇을 주나           호스트를 준다         호스트를 준다         같다
host.getHTML({shadowRoots:[root]})        보인다                보인다                같다
root.serializable                         false                 false                 같다

갈린 칸 = 3 / 16

★ closed 가 막는 것은 「host 에서 root 로 가는 길」과 「composedPath 가 안을 보여 주는 것」 둘뿐이다.
  attachShadow 의 반환값을 들고 있으면 안을 고쳐 쓸 수 있다: 안쪽 문단 -> 닫힌 쪽(고쳐 씀)
(exit 0)
```

- ★★★ **갈린 칸은 16 중 3이다.** 그중 하나(`root.mode`)는 **모드 그 자체**이므로 실질적으로 갈리는 것은 **둘뿐**이다.
  - **`host.shadowRoot`** — `open` 은 루트를 주고 `closed` 는 `null` 을 준다.
  - **`composedPath()` 의 길이** — `open` 은 7칸, `closed` 는 5칸. **그림자 안의 두 칸이 빠진다.**
- ★ **나머지 열셋은 전부 같다.** 조회가 막히는 것도, 상속이 넘어오는 것도, `::part` 가 닿는 것도, `document.activeElement` 가 호스트로 바뀌는 것도, `e.target` 이 호스트가 되는 것도 **모드와 무관**하다.
- ★★ **그래서 `closed` 는 보안 장치가 아니다.** 근거 둘 —
  1. **`attachShadow` 의 반환값을 들고 있으면 안을 마음대로 고쳐 쓸 수 있다.** 출력 마지막 줄이 그것을 실제로 고쳐 쓴 결과다.
  2. **안쪽 요소를 한 번이라도 잡으면 `getRootNode().host` 로 바깥으로 나올 수 있다.** 막힌 것은 **바깥에서 안으로 들어가는 한 방향의 한 길**뿐이다.
- **`closed` 가 진짜로 주는 것은 「실수로 남의 속을 만지지 않게 하는 규율」** 이다. 적대적인 스크립트를 막는 경계가 아니다.

```text
   closed 가 잠그는 문과 안 잠그는 문

   [ 바깥 -> 안 ]  host.shadowRoot          잠긴다     null 을 준다
   [ 바깥 -> 안 ]  composedPath()           잠긴다     안쪽 칸이 빠진다
   [ 손 -> 안 ]   attachShadow 의 반환값     안 잠긴다  내가 만들 때 받았다
   [ 안 -> 바깥 ] getRootNode().host        안 잠긴다  안에서는 늘 나갈 수 있다

   ★ 잠긴 문 둘은 전부 '바깥에서 이름으로 찾는' 문이다
```

```text
   경계가 막는 것과 안 막는 것 — 전수 격자

   막힌다                          안 막힌다
   ----------------------------    ---------------------------------
   document.querySelector          상속되는 CSS 속성 (color · font-size)
   document.getElementById         ::part 로 허락한 것
   안쪽에서 쓰는 바깥 선택자        참조 (getRootNode().host · attachShadow 반환값)
   closest() · matches()           document.activeElement (호스트로 바뀌어 나온다)
   host.shadowRoot (closed 만)     composedPath() (open 에서만 전부)
   composedPath() 의 안쪽 칸 (closed)  elementFromPoint (호스트로 바뀌어 나온다)

   ★ open 과 closed 가 갈리는 것은 왼쪽 칸의 아래 둘뿐이다
```

### (4) `attachShadow` 가 거절하는 자리 — 이 주제에서 조용하지 않은 유일한 곳

**언제 쓰나** — 아무 요소에나 붙이려 할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-mode.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '25,34p'
attachShadow 가 거절하는 자리 — 이 주제에서 조용하지 않은 유일한 곳
  이미 붙은 호스트에 또  = NotSupportedError 「Failed to execute 'attachShadow' on 'Element': Shadow root cannot be created on a host which already hosts a shadow tree.」
  mode 를 안 주면        = TypeError 「Failed to execute 'attachShadow' on 'Element': Failed to read the 'mode' property from 'ShadowRootInit': Required member is undefined.」
  인자를 아예 안 주면    = TypeError 「Failed to execute 'attachShadow' on 'Element': 1 argument required, but only 0 present.」
  mode 가 모르는 값이면  = TypeError 「Failed to execute 'attachShadow' on 'Element': Failed to read the 'mode' property from 'ShadowRootInit': The provided value 'zzz' is not a valid enum value of type ShadowRootMode.」

호스트가 될 수 있는 요소는 정해져 있다
  되는 것   = <div> · <span> · <p> · <h1> · <section> · <my-el>
  안 되는 것 = <input> NotSupportedError · <br> NotSupportedError · <table> NotSupportedError · <button> NotSupportedError · <img> NotSupportedError
  <img> 가 거절될 때의 말 = NotSupportedError 「Failed to execute 'attachShadow' on 'Element': This element does not support attachShadow」
(exit 0)
```

- **앞의 넷은 전부 예외**다. 이름이 둘로 갈린다 — **이미 붙어 있으면 `NotSupportedError`**, **인자가 틀리면 `TypeError`.**
- ★ **호스트가 될 수 있는 요소는 정해져 있다.** `div`·`span`·`p`·`h1`·`section` 과 **하이픈이 든 이름**(`my-el`)은 되고, `input`·`br`·`table`·`button`·`img` 는 `NotSupportedError` 로 막힌다.
- ★★ **이 주제에서 예외가 나는 곳은 여기뿐이다.** 조회 실패도, 슬롯 오타도, `part` 이름 오타도 전부 조용하다. **그 대비가 이 편의 뼈대**다 — 「예외가 없다」는 「잘 됐다」가 아니다.
- **`button` 이 안 되는 것이 의외다** — 「단추를 컴포넌트로 만들자」가 곧바로 막힌다. 그래서 커스텀 요소([목록의 **13번 주제**](../13-custom-element-lifecycle/))를 쓰고 그 안에 단추를 넣는다.

```text
   attachShadow 를 받아 주는 요소

   되는 것    div  span  p  h1  section  article  aside  blockquote  main  나-하이픈
   안 되는 것 input  br  table  button  img  … -> NotSupportedError 로 막힌다

   ★ '아무 요소에나 붙는다' 가 아니다. 그리고 이 거절만은 소리를 낸다
```

### (5) 선택자는 경계에서 멈춘다 — 양쪽으로

**언제 쓰나** — 「왜 `querySelector` 가 못 찾지」일 때.

**던진 것** — 같은 `class` 와 같은 `id` 를 안팎에 하나씩 두고 서로 찾게 했다. 아래 (6)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-12-border.html -->
<!doctype html>
<meta charset="utf-8">
<title>12-border</title>
<div id="host"><span id="라이트" class="표적">라이트 자식</span></div>
<p id="바깥문단" class="표적">바깥 문단</p>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [46, 22, 24][i])).join('').replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const host = $('host');
const root = host.attachShadow({ mode: 'open' });
root.innerHTML = '<p id="안문단" class="표적">그림자 안 문단</p><slot></slot>';
const 안 = root.querySelector('#안문단');
const 이름 = v => v === null ? 'null' : (v.id ? '#' + v.id : v.tagName);

O.push('경계는 양쪽으로 막는다 — 같은 class 와 같은 id 를 안팎에 두고 서로 찾게 했다');
row('무엇으로 찾았나', '찾았나', '무엇이 나왔나');
row('document.querySelector("#안문단")', String(document.querySelector('#안문단') !== null), 이름(document.querySelector('#안문단')));
row('document.getElementById("안문단")', String(document.getElementById('안문단') !== null), 이름(document.getElementById('안문단')));
row('document.querySelectorAll(".표적").length', String(document.querySelectorAll('.표적').length), '안쪽 것은 안 세어졌다');
row('document.querySelectorAll("p").length', String(document.querySelectorAll('p').length), '바깥 문단 하나뿐');
row('root.querySelector("#안문단")', String(root.querySelector('#안문단') !== null), 이름(root.querySelector('#안문단')));
row('root.getElementById("안문단")', String(root.getElementById('안문단') !== null), 이름(root.getElementById('안문단')));
row('root.querySelector("#바깥문단")', String(root.querySelector('#바깥문단') !== null), 이름(root.querySelector('#바깥문단')));
row('안.closest("body")', String(안.closest('body') !== null), 이름(안.closest('body')));
row('안.closest("#host")', String(안.closest('#host') !== null), 이름(안.closest('#host')));
row('안.matches("body p")', String(안.matches('body p')), '선택자는 경계를 안 넘는다');
O.push('');

O.push('그런데 참조는 자유롭게 오간다 — 경계를 건너는 길이 따로 나 있다');
row('무엇을 물었나', '무엇이 나왔나', '');
row('안.getRootNode().constructor.name', 안.getRootNode().constructor.name, '');
row('안.getRootNode().host', 이름(안.getRootNode().host), '이 길로 바깥에 나간다');
row('안.getRootNode({composed: true})', 안.getRootNode({ composed: true }).constructor.name, '문서까지 올라간다');
row('안.ownerDocument', 안.ownerDocument.constructor.name, '소유 문서는 하나다');
row('안.isConnected', String(안.isConnected), '그림자 안도 연결돼 있다');
row('root.parentNode', String(root.parentNode), 'root 는 host 의 자식이 아니다');
row('root.nodeType', String(root.nodeType) + ' (DocumentFragment)', '05번 주제와 같은 번호다');
row('root instanceof DocumentFragment', String(root instanceof DocumentFragment), '');
row('host.childNodes.length', String(host.childNodes.length), '라이트 자식만 센다');
row('host.firstElementChild', 이름(host.firstElementChild), '');
O.push('');
O.push('★ 안에서 바깥을 못 보는 것은 「선택자가 경계를 안 넘는다」는 뜻이지 참조가 없다는 뜻이 아니다.');
O.push('  getRootNode().host 하나면 바깥으로 나가고, 거기서부터는 평범한 문서다: '
     + 이름(안.getRootNode().host.parentElement) + ' -> ' + 이름(document.querySelector('#바깥문단')));
O.push('');
O.push('그래서 그림자마다 같은 id 를 써도 된다');
for (let i = 0; i < 3; i++) {
  const h = document.createElement('div');
  document.body.appendChild(h);
  h.attachShadow({ mode: 'open' }).innerHTML = '<b id="안문단">' + i + '번째 그림자의 #안문단</b>';
}
O.push('  같은 id 를 가진 그림자를 셋 더 만든 뒤 document.querySelectorAll("#안문단").length = '
     + document.querySelectorAll('#안문단').length);
O.push('  document.getElementById("안문단") = ' + document.getElementById('안문단'));
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-border.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
경계는 양쪽으로 막는다 — 같은 class 와 같은 id 를 안팎에 두고 서로 찾게 했다
무엇으로 찾았나                               찾았나                무엇이 나왔나
document.querySelector("#안문단")             false                 null
document.getElementById("안문단")             false                 null
document.querySelectorAll(".표적").length     2                     안쪽 것은 안 세어졌다
document.querySelectorAll("p").length         1                     바깥 문단 하나뿐
root.querySelector("#안문단")                 true                  #안문단
root.getElementById("안문단")                 true                  #안문단
root.querySelector("#바깥문단")               false                 null
안.closest("body")                            false                 null
안.closest("#host")                           false                 null
안.matches("body p")                          false                 선택자는 경계를 안 넘는다
(exit 0)
```

- **바깥에서 안을 못 찾는다** — `querySelector`·`getElementById` 둘 다 `null`. `.표적` 은 **안팎에 셋인데 2만 세어졌다.**
- ★ **안에서 바깥도 못 찾는다** — `root.querySelector('#바깥문단')` 이 `null` 이고, `closest('body')` 조차 `null` 이다. **막힘이 양방향이다.**
- ★ **`closest('#host')` 가 `null` 인 이유** — `closest` 는 **조상을 따라 올라가며 선택자를 맞춰 보는데**, 그림자 안 요소의 조상 사슬은 `ShadowRoot` 에서 **끝난다.** 호스트는 그 사슬 위에 없다.
- ★★ **여기서 「그림자마다 같은 `id` 를 써도 되는 이유」가 나온다** — `id` 의 유일성은 **그 나무 안에서만** 요구된다. (6)의 마지막 블록이 그 실측이다.

### (6) 참조는 자유롭게 오간다 — 「막힌다」는 선택자 이야기다

**언제 쓰나** — 컴포넌트 안에서 바깥 문서를 건드려야 할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-border.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,28p'
그런데 참조는 자유롭게 오간다 — 경계를 건너는 길이 따로 나 있다
무엇을 물었나                                 무엇이 나왔나
안.getRootNode().constructor.name             ShadowRoot
안.getRootNode().host                         #host                 이 길로 바깥에 나간다
안.getRootNode({composed: true})              HTMLDocument          문서까지 올라간다
안.ownerDocument                              HTMLDocument          소유 문서는 하나다
안.isConnected                                true                  그림자 안도 연결돼 있다
root.parentNode                               null                  root 는 host 의 자식이 아니다
root.nodeType                                 11 (DocumentFragment) 05번 주제와 같은 번호다
root instanceof DocumentFragment              true
host.childNodes.length                        1                     라이트 자식만 센다
host.firstElementChild                        #라이트

★ 안에서 바깥을 못 보는 것은 「선택자가 경계를 안 넘는다」는 뜻이지 참조가 없다는 뜻이 아니다.
  getRootNode().host 하나면 바깥으로 나가고, 거기서부터는 평범한 문서다: BODY -> #바깥문단
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-border.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '30,32p'
그래서 그림자마다 같은 id 를 써도 된다
  같은 id 를 가진 그림자를 셋 더 만든 뒤 document.querySelectorAll("#안문단").length = 0
  document.getElementById("안문단") = null
(exit 0)
```

- **트리는 둘인데 문서는 하나다** — `ownerDocument` 가 같은 `HTMLDocument` 이고 `isConnected` 도 `true` 다. **그림자 안도 「연결된」 상태**다.
- ★ **`root.parentNode` 가 `null`** 이다. 섀도 루트는 호스트의 **자식이 아니라 별도의 뿌리**다. `host.childNodes.length` 가 라이트 자식만 센 것이 그 짝이다.
- ★ **`root` 는 `DocumentFragment` 다**(`nodeType === 11`). [05번 주제](../05-documentfragment-and-template/2-summary.md)의 그 조각과 **같은 종류**이고, 다른 점은 **호스트를 갖고 화면에 그려진다**는 것뿐이다.
- ★★ **「막힌다」는 전부 선택자 이야기다.** `getRootNode().host` 한 줄이면 바깥으로 나가고, 거기서부터는 평범한 문서다.
- **같은 `id` 를 가진 그림자를 셋 더 만들어도 `document.querySelectorAll('#안문단').length` 가 0** 이다. **유일성이 나무마다 따로** 요구되는 것이 이렇게 드러난다.

```text
   getRootNode() 두 꼴의 차이

   안.getRootNode()                  -> ShadowRoot      가장 가까운 뿌리에서 멈춘다
   안.getRootNode({composed: true})  -> HTMLDocument    경계를 뚫고 문서까지
   안.ownerDocument                  -> HTMLDocument    처음부터 문서다

   ★ ownerDocument 는 '어느 문서가 만들었나' 이고
     getRootNode() 는 '지금 어느 나무에 매달려 있나' 다
```

### (7) 스타일 — 선택자는 막히는데 상속은 넘어온다

**언제 쓰나** — 「왜 내 CSS 가 컴포넌트 안에 안 먹지」일 때. **그리고 그 반대일 때.**

**던진 것** — 아래 (8)·(9)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-12-style.html -->
<!doctype html>
<meta charset="utf-8">
<title>12-style</title>
<style>
  body { color: rgb(0, 100, 0); font-size: 21px }
  p { color: rgb(200, 0, 0) }
  .테두리 { border: 3px solid rgb(0, 0, 255) }
  #host::part(핵심) { color: rgb(255, 0, 255) }
  #host::part(없는이름) { color: rgb(1, 2, 3) }
  #겉::part(속것) { color: rgb(255, 128, 0) }
</style>
<div class="테마"><div id="host"><b id="라이트" class="테두리">라이트 자식</b></div></div>
<p id="바깥문단" class="테두리">바깥 문단</p>
<div id="겉"></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [34, 20, 14, 14][i])).join('').replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const root = $('host').attachShadow({ mode: 'open' });
root.innerHTML = '<p id="민" class="테두리">규칙 없는 문단</p>'
               + '<p id="파트" part="핵심">part 를 단 문단</p>'
               + '<i id="상속">글자만 있는 것</i><slot></slot>';
const cs = el => getComputedStyle(el);

O.push('바깥 시트의 규칙이 그림자 안으로 새나 — 같은 선택자가 안팎에 걸린다');
row('무엇을', 'color', 'border 폭', 'font-size');
row('바깥 #바깥문단 (p · .테두리)', cs($('바깥문단')).color, cs($('바깥문단')).borderTopWidth, cs($('바깥문단')).fontSize);
row('그림자 안 #민 (p · .테두리)', cs(root.getElementById('민')).color, cs(root.getElementById('민')).borderTopWidth, cs(root.getElementById('민')).fontSize);
row('그림자 안 #상속 (선택자 없음)', cs(root.getElementById('상속')).color, cs(root.getElementById('상속')).borderTopWidth, cs(root.getElementById('상속')).fontSize);
row('슬롯에 배정된 #라이트', cs($('라이트')).color, cs($('라이트')).borderTopWidth, cs($('라이트')).fontSize);
O.push('');
O.push('★ 선택자는 경계에서 멈추는데 상속은 넘어온다 — 둘은 다른 길이다.');
O.push('  넘어온 것: color · font-size (상속되는 속성)   막힌 것: border (상속 안 되는 속성)');
O.push('');

O.push('안쪽 시트를 넣으면 — 그 시트는 안에서만 산다');
root.innerHTML = '<style>p { color: rgb(0, 0, 255) } .테두리 { border: 1px dashed rgb(0, 0, 0) }'
               + ' :host { display: block; outline: 2px solid rgb(0, 200, 200) }'
               + ' :host(.켜짐) { background: rgb(250, 250, 200) }'
               + ' :host-context(.테마) { padding-left: 7px }</style>' + root.innerHTML;
row('무엇을', 'color', 'border 폭', '');
row('그림자 안 #민', cs(root.getElementById('민')).color, cs(root.getElementById('민')).borderTopWidth, '');
row('바깥 #바깥문단', cs($('바깥문단')).color, cs($('바깥문단')).borderTopWidth, '');
O.push('  ★ 안쪽 시트의 p 규칙이 바깥 문단을 건드리지 않았다. 양방향이다.');
O.push('');

O.push(':host 계열 — 안쪽 시트가 바깥의 호스트를 꾸미는 유일한 길');
row('무엇을', '값', '', '');
row(':host { display: block }', cs($('host')).display, '', '');
row(':host { outline: 2px }', cs($('host')).outlineWidth, '', '');
row(':host-context(.테마) padding', cs($('host')).paddingLeft, '조상의 class 를 본다', '');
row(':host(.켜짐) · class 주기 전', cs($('host')).backgroundColor, '', '');
$('host').classList.add('켜짐');
row(':host(.켜짐) · class 준 뒤', cs($('host')).backgroundColor, '', '');
O.push('  명시도로는 :host (0,1,0) 가 이길 자리에 바깥의 약한 선택자를 붙여 본다');
const 셀 = document.createElement('style');
셀.textContent = 'div#host { }  div { display: inline-block }';
document.head.appendChild(셀);
O.push('  바깥 시트에 div { display: inline-block } (0,0,1) 을 더하면 → ' + cs($('host')).display);
O.push('  ★ 명시도가 낮은 바깥 규칙이 이겼다 — 「어느 트리의 시트인가」가 명시도보다 먼저다.');
O.push('');

O.push('::part — 호스트가 허락한 구멍');
row('무엇을', 'color', 'part 속성', '');
row('그림자 안 #파트 (part="핵심")', cs(root.getElementById('파트')).color, root.getElementById('파트').getAttribute('part'), '');
row('그림자 안 #민 (part 없음)', cs(root.getElementById('민')).color, String(root.getElementById('민').getAttribute('part')), '');
O.push('  #host::part(없는이름) 은 아무것도 안 잡는다 — 예외도 경고도 없다.');
O.push('  바깥 문서 시트의 규칙 = ' + [...document.styleSheets[0].cssRules].map(r => r.selectorText).join(' · '));
O.push('  ★ 규칙은 담겼는데 아무것도 안 잡는 상태다 — 08번 주제의 「담겼는데 졌나」와 다른 제4의 상태다.');
O.push('');
O.push('두 겹 안쪽에 닿으려면 — exportparts');
const 겉root = $('겉').attachShadow({ mode: 'open' });
겉root.innerHTML = '<div id="속host" exportparts="핵심: 속것"></div>';
const 속host = 겉root.getElementById('속host');
const 속root = 속host.attachShadow({ mode: 'open' });
속root.innerHTML = '<p id="깊은" part="핵심">두 겹 안</p>';
O.push('  exportparts="핵심: 속것" 이 있을 때  #깊은.color = ' + cs(속root.getElementById('깊은')).color);
속host.removeAttribute('exportparts');
O.push('  exportparts 를 떼면                  #깊은.color = ' + cs(속root.getElementById('깊은')).color);
O.push('  ★ part 는 한 겹만 뚫는다. 두 겹을 뚫으려면 가운데 호스트가 다시 내보내야 한다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,9p'
바깥 시트의 규칙이 그림자 안으로 새나 — 같은 선택자가 안팎에 걸린다
무엇을                            color               border 폭     font-size
바깥 #바깥문단 (p · .테두리)      rgb(200, 0, 0)      3px           21px
그림자 안 #민 (p · .테두리)       rgb(0, 100, 0)      0px           21px
그림자 안 #상속 (선택자 없음)     rgb(0, 100, 0)      0px           21px
슬롯에 배정된 #라이트             rgb(0, 100, 0)      3px           21px

★ 선택자는 경계에서 멈추는데 상속은 넘어온다 — 둘은 다른 길이다.
  넘어온 것: color · font-size (상속되는 속성)   막힌 것: border (상속 안 되는 속성)
(exit 0)
```

- **`p` 규칙(빨강)도 `.테두리` 규칙(파란 3px)도 그림자 안에 안 닿았다.** `#민` 은 바깥 문단과 선택자가 같은데 색이 다르다.
- ★★ **그런데 `color` 와 `font-size` 는 넘어왔다.** `body` 에 준 `rgb(0, 100, 0)` 과 `21px` 이 **그림자 안에서도 계산값으로 나온다.**
- ★ **둘은 같은 길이 아니다.** 막힌 것은 **선택자 매칭**이고, 넘어온 것은 **상속**이다. 상속은 선택자를 거치지 않고 **부모의 계산값에서 곧바로** 온다 — 그래서 경계가 막을 것이 없다.
- ★ **그 증거가 `border` 다.** `border` 는 **상속되지 않는 속성**이라 안 넘어왔다(`0px`). 「넘어오는 것은 상속되는 속성뿐」이 정확한 문장이다.
- ★★ **슬롯에 배정된 `#라이트` 는 바깥 규칙을 전부 받았다**(테두리 3px). **배정은 이동이 아니기 때문**이다 — 그 요소는 여전히 라이트 DOM 에 있고, 스타일 계산도 라이트 DOM 기준으로 한다((11)).

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '11,15p'
안쪽 시트를 넣으면 — 그 시트는 안에서만 산다
무엇을                            color               border 폭
그림자 안 #민                     rgb(0, 0, 255)      1px
바깥 #바깥문단                    rgb(200, 0, 0)      3px
  ★ 안쪽 시트의 p 규칙이 바깥 문단을 건드리지 않았다. 양방향이다.
(exit 0)
```

- **안쪽 시트의 `p` 규칙이 바깥 문단을 건드리지 않았다.** 스타일도 **양방향**으로 막힌다.
- **안쪽 시트는 안쪽에서 이겼다** — `#민` 이 파란색 1px 로 바뀌었다.

```text
   스타일이 경계를 만나면

   바깥 시트  p { color: red }        --| 경계 |--X   선택자는 못 넘는다
   바깥 시트  body { color: green }   --| 경계 |-->   상속은 넘어온다 (부모의 계산값)
   바깥 시트  .테두리 { border }      --| 경계 |--X   상속 안 되는 속성이라 아예 안 온다
   안쪽 시트  p { color: blue }       X--| 경계 |--   밖으로도 못 나간다
   슬롯 자식  (라이트 DOM 에 있다)     경계 바깥이므로 바깥 규칙을 그대로 받는다
```

### (8) `:host` 계열 — 안쪽 시트가 바깥의 호스트를 꾸미는 유일한 길

**언제 쓰나** — 컴포넌트가 **자기 바깥 모양**(블록인가 인라인인가 등)을 정해야 할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,26p'
:host 계열 — 안쪽 시트가 바깥의 호스트를 꾸미는 유일한 길
무엇을                            값
:host { display: block }          block
:host { outline: 2px }            2px
:host-context(.테마) padding      7px                 조상의 class 를 본다
:host(.켜짐) · class 주기 전      rgba(0, 0, 0, 0)
:host(.켜짐) · class 준 뒤        rgb(250, 250, 200)
  명시도로는 :host (0,1,0) 가 이길 자리에 바깥의 약한 선택자를 붙여 본다
  바깥 시트에 div { display: inline-block } (0,0,1) 을 더하면 → inline-block
  ★ 명시도가 낮은 바깥 규칙이 이겼다 — 「어느 트리의 시트인가」가 명시도보다 먼저다.
(exit 0)
```

- **`:host` 는 호스트 요소를 잡는다** — `display: block` 과 `outline: 2px` 이 둘 다 먹었다.
- **`:host(.켜짐)` 은 호스트가 그 조건을 만족할 때만** 잡는다. class 를 주기 전에는 배경이 투명이었고 준 뒤에 바뀌었다.
- **`:host-context(.테마)` 는 조상을 본다** — 호스트의 **조상 어딘가**에 `.테마` 가 있으면 잡는다. 컴포넌트가 「어두운 테마 안에 놓였는지」를 아는 길이다.
- ★★ **`:host` 는 바깥 규칙에 진다 — 명시도가 아니라 「어느 트리의 시트인가」가 먼저다.** 명시도 `(0,1,0)` 인 `:host` 가 명시도 `(0,0,1)` 인 바깥의 `div` 규칙에게 졌다. **컴포넌트가 정한 기본값을 쓰는 쪽이 덮어쓸 수 있게 하려는 설계**다.
- ★ **`:host-context` 는 Chrome 에서는 되지만 표준화가 흔들린 표면**이다. 이 문서는 **Chrome 151 에서 이렇게 된다**까지만 말한다.

```text
   :host 세 꼴이 각각 무엇을 보나

   :host                     -> 호스트 자신
   :host(.켜짐)              -> 호스트가 그 선택자에 맞을 때만
   :host-context(.테마)      -> 호스트의 '조상' 에 .테마 가 있을 때

   ★ 셋 다 안쪽 시트에만 쓸 수 있다. 바깥에서는 그냥 #host 로 쓰면 된다
```

### (9) `::part` 와 `exportparts` — 호스트가 낸 창구

**언제 쓰나** — 컴포넌트를 쓰는 쪽이 **안쪽 일부만** 꾸며야 할 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '28,34p'
::part — 호스트가 허락한 구멍
무엇을                            color               part 속성
그림자 안 #파트 (part="핵심")     rgb(255, 0, 255)    핵심
그림자 안 #민 (part 없음)         rgb(0, 0, 255)      null
  #host::part(없는이름) 은 아무것도 안 잡는다 — 예외도 경고도 없다.
  바깥 문서 시트의 규칙 = body · p · .테두리 · #host::part(핵심) · #host::part(없는이름) · #겉::part(속것)
  ★ 규칙은 담겼는데 아무것도 안 잡는 상태다 — 08번 주제의 「담겼는데 졌나」와 다른 제4의 상태다.
(exit 0)
```

- **`#host::part(핵심)` 이 경계를 뚫고 안쪽 문단을 자홍색으로 칠했다.** `part` 속성이 없는 `#민` 은 안 잡혔다.
- ★★ **`part` 이름이 틀리면 예외도 경고도 없다.** `#host::part(없는이름)` 규칙은 **`cssRules` 에 멀쩡히 담겨 있고**(출력의 규칙 목록에 보인다) **문법도 맞는데** 아무것도 안 잡는다.
- ★ **이것이 「제4의 상태」다** — [08번 주제](../08-getcomputedstyle/2-summary.md)의 「담겼는데 졌나」와 다르다. 진 것이 아니라 **애초에 맞은 요소가 없다.** 진단은 **`cssRules` 가 아니라 `root.querySelectorAll('[part]')` 로 이름을 세는 것**이다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-style.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '36,39p'
두 겹 안쪽에 닿으려면 — exportparts
  exportparts="핵심: 속것" 이 있을 때  #깊은.color = rgb(255, 128, 0)
  exportparts 를 떼면                  #깊은.color = rgb(0, 100, 0)
  ★ part 는 한 겹만 뚫는다. 두 겹을 뚫으려면 가운데 호스트가 다시 내보내야 한다.
(exit 0)
```

- ★ **`part` 는 한 겹만 뚫는다.** 두 겹 안쪽 요소는 가운데 호스트가 **`exportparts` 로 다시 내보내야** 닿는다. 속성을 떼자 곧바로 상속색으로 돌아갔다.
- **`exportparts="핵심: 속것"` 은 「안쪽의 `핵심` 을 바깥에는 `속것` 이라는 이름으로 내보낸다」** 는 뜻이다. 이름을 바꿔 줄 수 있어 **안쪽 이름이 공개 계약이 되지 않는다.**

```text
   part 가 뚫는 겹수

   바깥 시트  #겉::part(속것)
                 |
                 v
   #겉 의 그림자   <div id="속host" exportparts="핵심: 속것">   <- 여기서 이름을 갈아 내보낸다
                      |
                      v
   #속host 의 그림자  <p part="핵심">                            <- 여기에 닿는다

   ★ exportparts 를 떼면 두 겹째에서 끊긴다 — 조용히
```

### (10) 슬롯 할당 — 무엇이 어느 칸에 배정됐나

**언제 쓰나** — 「내가 넣은 자식이 화면에 안 보일 때」.

**던진 것** — 아래 (11)\~(13)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-12-slot.html -->
<!doctype html>
<meta charset="utf-8">
<title>12-slot</title>
<div id="host">
  <span slot="머리" id="머리자식">머리에 넣을 것</span>
  <b id="익명">이름표 없는 것</b>
  <span slot="없는칸" id="미아">아무 데도 없는 칸을 가리킨다</span>
</div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const row = (...c) => O.push(c.map((v, i) => padw(String(v), [42, 38, 26][i])).join('').replace(/ +$/, ''));
const $ = id => document.getElementById(id);
const host = $('host');
const root = host.attachShadow({ mode: 'open' });
root.innerHTML = '<slot name="머리"></slot><slot><i id="기본값">슬롯의 기본 내용</i></slot>';
const 머리슬롯 = root.querySelector('slot[name="머리"]');
const 기본슬롯 = root.querySelector('slot:not([name])');
const 이름 = n => n === null || n === undefined ? String(n)
  : (n.nodeType === 3 ? '#text' : (n.id ? '#' + n.id : n.nodeName));

O.push('슬롯이 무엇을 받았나');
row('무엇을 물었나', '무엇이 나왔나', '');
row('머리슬롯.assignedNodes()', 머리슬롯.assignedNodes().map(이름).join(' '), '');
row('머리슬롯.assignedElements()', 머리슬롯.assignedElements().map(이름).join(' '), '');
row('기본슬롯.assignedNodes()', 기본슬롯.assignedNodes().map(이름).join(' '), '★ 줄바꿈 공백도 배정된다');
row('기본슬롯.assignedElements()', 기본슬롯.assignedElements().map(이름).join(' '), '요소만 센다');
row('기본슬롯.assignedNodes({flatten:true})', 기본슬롯.assignedNodes({ flatten: true }).map(이름).join(' '), '');
O.push('');

O.push('자식 쪽에서 물으면');
row('무엇을 물었나', '무엇이 나왔나', '');
row('#머리자식.assignedSlot.name', JSON.stringify($('머리자식').assignedSlot.name), '');
row('#익명.assignedSlot.name', JSON.stringify($('익명').assignedSlot.name), '이름 없는 슬롯은 빈 이름');
row('#미아.assignedSlot', String($('미아').assignedSlot), '★ 맞는 칸이 없으면 null');
O.push('  #머리자식.getBoundingClientRect().width = ' + $('머리자식').getBoundingClientRect().width.toFixed(2)
     + '   #미아 = ' + $('미아').getBoundingClientRect().width.toFixed(2) + '  <- 배정 못 받으면 안 그려진다');
O.push('  ★ 예외도 경고도 없다. slot="없는칸" 오타는 「조용히 사라짐」으로만 드러난다.');
O.push('');

O.push('배정은 옮기는 것이 아니다 — 트리는 그대로다');
row('무엇을 물었나', '무엇이 나왔나', '');
row('#익명.parentElement', 이름($('익명').parentElement), '여전히 host 의 자식이다');
row('#익명.getRootNode()', $('익명').getRootNode().constructor.name, '문서 쪽에 남아 있다');
row('#익명.assignedSlot.getRootNode()', $('익명').assignedSlot.getRootNode().constructor.name, '슬롯은 그림자 쪽이다');
row('host.children.length', String(host.children.length), '라이트 자식 셋');
row('root.children.length', String(root.children.length), '슬롯 둘뿐이다');
row('host.innerHTML 에 슬롯이 보이나', String(host.innerHTML.includes('<slot')), '안 보인다');
O.push('');

O.push('기본 내용(fallback)은 언제 보이나 — 여기서 공백 텍스트가 발목을 잡는다');
const 기본값 = root.getElementById('기본값');
O.push('  배정된 요소가 있을 때  #기본값 의 rect.width = ' + 기본값.getBoundingClientRect().width.toFixed(2));
$('익명').remove();
O.push('  #익명 을 뗀 뒤        배정 노드 = ' + 기본슬롯.assignedNodes().map(이름).join(' ')
     + ' · #기본값 의 rect.width = ' + 기본값.getBoundingClientRect().width.toFixed(2));
O.push('  ★ 요소를 다 뗐는데도 기본 내용이 안 나온다 — 줄바꿈 공백 텍스트가 아직 배정돼 있기 때문이다.');
const 깔끔 = document.createElement('div');
document.body.appendChild(깔끔);
const r3 = 깔끔.attachShadow({ mode: 'open' });
r3.innerHTML = '<slot><i id="기본값2">슬롯의 기본 내용</i></slot>';
const 슬롯3 = r3.querySelector('slot'), 기본값2 = r3.getElementById('기본값2');
O.push('  공백 없이 만든 host 에서  배정 노드 = ' + JSON.stringify(슬롯3.assignedNodes().map(이름))
     + ' · #기본값2 의 rect.width = ' + 기본값2.getBoundingClientRect().width.toFixed(2) + '  <- 이제 나온다');
O.push('  ★ 진단은 assignedNodes() 다 — rect 만 보면 「왜 기본값이 안 나오지」에서 막힌다.');
O.push('');

O.push('수동 할당 — slotAssignment: "manual"');
const 손 = document.createElement('div');
손.innerHTML = '<span slot="머리" id="손가">slot 이름을 달아 둔 것</span><b id="손나">이름 없는 것</b>';
document.body.appendChild(손);
const r4 = 손.attachShadow({ mode: 'open', slotAssignment: 'manual' });
r4.innerHTML = '<slot name="머리" id="머리칸"></slot><slot id="아무칸"></slot>';
const 머리칸 = r4.getElementById('머리칸'), 아무칸 = r4.getElementById('아무칸');
row('root.slotAssignment', r4.slotAssignment, '');
row('머리칸.assignedNodes() (자동 배정되나)', JSON.stringify(머리칸.assignedNodes().map(이름)), '★ slot 속성을 안 본다');
row('#손가.assignedSlot', String(손.querySelector('#손가').assignedSlot), '');
아무칸.assign(손.querySelector('#손가'), 손.querySelector('#손나'));
row('아무칸.assign(#손가, #손나) 뒤', JSON.stringify(아무칸.assignedNodes().map(이름)), '순서도 내가 정한다');
머리칸.assign(손.querySelector('#손가'));
row('머리칸.assign(#손가) 뒤 · 머리칸', JSON.stringify(머리칸.assignedNodes().map(이름)), '');
row('머리칸.assign(#손가) 뒤 · 아무칸', JSON.stringify(아무칸.assignedNodes().map(이름)), '한 노드는 한 칸에만');
const 자동 = document.createElement('div');
자동.innerHTML = '<span slot="없는칸" id="자동미아">자동 모드의 미아</span>';
document.body.appendChild(자동);
const r5 = 자동.attachShadow({ mode: 'open' });
r5.innerHTML = '<slot id="자동칸"></slot>';
let 예외 = '예외 없음';
try { r5.getElementById('자동칸').assign(자동.querySelector('#자동미아')); }
catch (e) { 예외 = e.name + ' 「' + e.message + '」'; }
O.push('  자동(named) 모드 슬롯에 assign() 을 부르면 = ' + 예외
     + ' · assignedNodes = ' + JSON.stringify(r5.getElementById('자동칸').assignedNodes().map(이름)));
O.push('  ★ 예외가 아니라 「아무 일도 안 일어남」이다. 모드를 잘못 고르면 조용히 빈 칸이 된다.');
O.push('');

O.push('flatten 이 무엇을 펴나 — 슬롯이 슬롯에 배정될 때');
const 겹 = document.createElement('div');
겹.innerHTML = '<b id="진짜">진짜 내용</b>';
document.body.appendChild(겹);
const r6 = 겹.attachShadow({ mode: 'open' });
r6.innerHTML = '<div id="중간"></div>';
const 중간 = r6.getElementById('중간');
const r7 = 중간.attachShadow({ mode: 'open' });
r7.innerHTML = '<slot id="속칸"><i id="속기본">속 기본값</i></slot>';
중간.appendChild(document.createElement('slot'));
row('속칸.assignedNodes()', JSON.stringify(r7.getElementById('속칸').assignedNodes().map(이름)), '바깥 <slot> 자체');
row('속칸.assignedNodes({flatten:true})', JSON.stringify(r7.getElementById('속칸').assignedNodes({ flatten: true }).map(이름)), '끝까지 따라간다');
중간.querySelector('slot').remove();
row('배정이 비었을 때 assignedNodes()', JSON.stringify(r7.getElementById('속칸').assignedNodes().map(이름)), '빈 배열');
row('그때 {flatten:true} 는', JSON.stringify(r7.getElementById('속칸').assignedNodes({ flatten: true }).map(이름)), '★ 기본 내용을 준다');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,7p'
슬롯이 무엇을 받았나
무엇을 물었나                             무엇이 나왔나
머리슬롯.assignedNodes()                  #머리자식
머리슬롯.assignedElements()               #머리자식
기본슬롯.assignedNodes()                  #text #text #익명 #text #text         ★ 줄바꿈 공백도 배정된다
기본슬롯.assignedElements()               #익명                                 요소만 센다
기본슬롯.assignedNodes({flatten:true})    #text #text #익명 #text #text
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '9,15p'
자식 쪽에서 물으면
무엇을 물었나                             무엇이 나왔나
#머리자식.assignedSlot.name               "머리"
#익명.assignedSlot.name                   ""                                    이름 없는 슬롯은 빈 이름
#미아.assignedSlot                        null                                  ★ 맞는 칸이 없으면 null
  #머리자식.getBoundingClientRect().width = 97.28   #미아 = 0.00  <- 배정 못 받으면 안 그려진다
  ★ 예외도 경고도 없다. slot="없는칸" 오타는 「조용히 사라짐」으로만 드러난다.
(exit 0)
```

- **`assignedNodes()` 와 `assignedElements()` 의 길이가 다르다** — 앞엣것은 **텍스트 노드까지** 세고 뒤엣것은 **요소만** 센다. 기본 슬롯이 받은 다섯 중 넷이 **마크업의 줄바꿈 공백**이다([01번 주제](../01-document-and-node-tree/2-summary.md)의 그 공백 텍스트 노드다).
- **`slot="머리"` 를 단 자식은 이름 있는 칸으로, 이름표 없는 자식은 이름 없는 칸으로** 간다.
- ★★ **`slot="없는칸"` 오타는 예외도 경고도 없다.** `assignedSlot` 이 `null` 이 되고 **`getBoundingClientRect().width` 가 0** 이 된다 — 즉 **화면에서 조용히 사라진다.**
- ★ **진단은 `assignedSlot` 이다.** 「안 보인다」를 CSS 문제로 오해하기 쉬운 자리다.

```text
   슬롯 배정 — 무엇이 어디로 가나

   라이트 DOM                          그림자 DOM
   <span slot="머리">  ────────────>  <slot name="머리">
   <b>   (이름표 없음) ────────────>  <slot>            (이름 없는 칸)
   <span slot="없는칸"> ──X            (맞는 칸이 없다)  -> assignedSlot 이 null

   ★ 맞는 칸이 없으면 '기본 칸으로 떨어지지' 않는다. 그냥 안 그려진다
```

### (11) 배정은 이동이 아니라 투영이다

**언제 쓰나** — 「내 자식이 어느 나무에 있나」를 따질 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '17,24p'
배정은 옮기는 것이 아니다 — 트리는 그대로다
무엇을 물었나                             무엇이 나왔나
#익명.parentElement                       #host                                 여전히 host 의 자식이다
#익명.getRootNode()                       HTMLDocument                          문서 쪽에 남아 있다
#익명.assignedSlot.getRootNode()          ShadowRoot                            슬롯은 그림자 쪽이다
host.children.length                      3                                     라이트 자식 셋
root.children.length                      2                                     슬롯 둘뿐이다
host.innerHTML 에 슬롯이 보이나           false                                 안 보인다
(exit 0)
```

- **`#익명.parentElement` 가 여전히 `#host` 이고 `getRootNode()` 가 `HTMLDocument` 다.** 배정돼도 **라이트 DOM 에 그대로 남아 있다.**
- ★ **`assignedSlot` 쪽은 `ShadowRoot` 에 산다** — 두 나무에 한 발씩 걸친 관계가 여기서 보인다.
- **`host.children.length` 는 3, `root.children.length` 는 2** 다. 두 목록이 섞이지 않는다.
- **`host.innerHTML` 에는 `<slot>` 이 안 보인다** — 직렬화도 나무를 섞지 않는다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '26,31p'
기본 내용(fallback)은 언제 보이나 — 여기서 공백 텍스트가 발목을 잡는다
  배정된 요소가 있을 때  #기본값 의 rect.width = 0.00
  #익명 을 뗀 뒤        배정 노드 = #text #text #text #text · #기본값 의 rect.width = 0.00
  ★ 요소를 다 뗐는데도 기본 내용이 안 나온다 — 줄바꿈 공백 텍스트가 아직 배정돼 있기 때문이다.
  공백 없이 만든 host 에서  배정 노드 = [] · #기본값2 의 rect.width = 112.02  <- 이제 나온다
  ★ 진단은 assignedNodes() 다 — rect 만 보면 「왜 기본값이 안 나오지」에서 막힌다.
(exit 0)
```

- ★★ **요소를 전부 뗐는데도 기본 내용이 안 나왔다.** 원인은 **줄바꿈 공백 텍스트 노드가 아직 배정돼 있기 때문**이다. 기본 내용은 **배정이 완전히 비었을 때만** 나온다.
- ★ **진단은 `assignedNodes()` 다.** `rect.width` 만 보면 「왜 기본값이 안 나오지」에서 막힌다 — **세 창이 다 정상인데 기준만 다른** 자리다.
- **공백 없이 만든 호스트에서는 곧바로 나왔다**(`rect.width` 가 0 에서 112.02 로).
- ★ **정본은 HTML 갈래의 10번** 이다. 거기는 마크업 쪽에서 같은 현상을 본다.

```text
   기본 내용(fallback)이 나오는 조건

   assignedNodes() = ["#text","#text","#익명","#text","#text"]  -> 안 나온다
   요소만 떼면     = ["#text","#text","#text","#text"]          -> 여전히 안 나온다
   공백까지 없으면 = []                                          -> 그제야 나온다

   ★ '요소가 없으면' 이 아니라 '노드가 하나도 없으면' 이다
```

### (12) 수동 할당 — `slotAssignment: 'manual'`

**언제 쓰나** — 자식에 `slot` 속성을 달 수 없을 때(남의 마크업을 감쌀 때).

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '33,41p'
수동 할당 — slotAssignment: "manual"
root.slotAssignment                       manual
머리칸.assignedNodes() (자동 배정되나)    []                                    ★ slot 속성을 안 본다
#손가.assignedSlot                        null
아무칸.assign(#손가, #손나) 뒤            ["#손가","#손나"]                     순서도 내가 정한다
머리칸.assign(#손가) 뒤 · 머리칸          ["#손가"]
머리칸.assign(#손가) 뒤 · 아무칸          ["#손나"]                             한 노드는 한 칸에만
  자동(named) 모드 슬롯에 assign() 을 부르면 = 예외 없음 · assignedNodes = []
  ★ 예외가 아니라 「아무 일도 안 일어남」이다. 모드를 잘못 고르면 조용히 빈 칸이 된다.
(exit 0)
```

- **`manual` 모드에서는 `slot` 속성을 아예 안 본다.** `slot="머리"` 를 달아 둔 자식도 `assignedSlot` 이 `null` 이다.
- **`slot.assign(...)` 으로 내가 직접 넣는다.** 인자 순서가 그대로 배정 순서다 — **마크업 순서와 다르게 놓을 수 있다.**
- **한 노드는 한 칸에만** 있을 수 있다. 다른 칸에 `assign` 하면 앞의 칸에서 빠진다.
- ★★ **자동(`named`) 모드 슬롯에 `assign()` 을 부르면 예외가 아니라 「아무 일도 안 일어남」** 이다. **모드를 잘못 고르면 조용히 빈 칸이 된다** — 이 주제의 조용한 실패가 여기서 또 나온다.

### (13) `flatten` 이 무엇을 펴나

**언제 쓰나** — 컴포넌트를 컴포넌트 안에 넣었을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-slot.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '43,47p'
flatten 이 무엇을 펴나 — 슬롯이 슬롯에 배정될 때
속칸.assignedNodes()                      ["SLOT"]                              바깥 <slot> 자체
속칸.assignedNodes({flatten:true})        ["#진짜"]                             끝까지 따라간다
배정이 비었을 때 assignedNodes()          []                                    빈 배열
그때 {flatten:true} 는                    ["#속기본"]                           ★ 기본 내용을 준다
(exit 0)
```

- **슬롯에 슬롯이 배정될 수 있다.** 그때 `assignedNodes()` 는 **바로 위 칸에 꽂힌 `<slot>` 자신**을 준다.
- ★ **`{flatten: true}` 는 그 사슬을 끝까지 따라가 진짜 내용을 준다.** 겹친 컴포넌트에서 「결국 무엇이 그려지나」를 묻는 것이 이쪽이다.
- ★★ **배정이 비었을 때도 `flatten` 이 다르게 답한다** — 빈 배열 대신 **기본 내용**을 준다. (11)의 「기본 내용이 언제 나오나」를 **한 줄로 묻는 방법**이 이것이다.

```text
   assignedNodes 두 꼴

   슬롯이 겹쳤을 때   기본값 -> ["SLOT"]      바로 위 칸에 꽂힌 것
                     flatten -> ["#진짜"]    끝까지 따라간 결과
   배정이 비었을 때   기본값 -> []            아무것도 안 꽂혔다
                     flatten -> ["#속기본"]  그러면 기본 내용이 그려진다

   ★ 'DOM 이 무엇을 받았나' 와 '화면에 무엇이 그려지나' 를 가르는 옵션이다
```

### (14) 이벤트 재타기팅 — 한 번의 클릭을 일곱 자리에서 본다

**언제 쓰나** — 위임 리스너가 **그림자 안 요소를 못 알아볼 때**.

**던진 것** — 아래 (15)의 블록도 같은 실행에서 잘라 낸 것이다.

```html
<!-- wa12b-12-event.html -->
<!doctype html>
<meta charset="utf-8">
<title>12-event</title>
<div id="host"><span id="슬롯자식">슬롯에 들어갈 자식</span></div>
<script>
const O = [];
const W = s => [...s].reduce((a, ch) => a + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const padw = (s, n) => s + ' '.repeat(Math.max(0, n - W(s)));
const $ = id => document.getElementById(id);
const 이름 = n => n === null || n === undefined ? String(n)
  : n === window ? 'Window'
  : n.nodeType === 11 ? '#shadow-root'
  : n.nodeType === 9 ? '#document'
  : (n.id ? '#' + n.id : n.nodeName);
const root = $('host').attachShadow({ mode: 'open' });
root.innerHTML = '<div id="껍데기"><button id="단추">안쪽 단추</button></div><slot></slot>';
const 단추 = root.getElementById('단추');

O.push('한 번의 click 을 일곱 자리에서 본다 — e.target 과 composedPath()');
O.push(padw('리스너를 어디에 달았나', 26) + padw('e.target', 14) + padw('e.currentTarget', 16) + 'composedPath()');
const 자리 = [['안쪽 단추', 단추], ['그림자 안 #껍데기', root.getElementById('껍데기')],
             ['ShadowRoot', root], ['호스트 #host', $('host')],
             ['document.body', document.body], ['document', document], ['window', window]];
const 행 = [];
for (const [라벨, t] of 자리) {
  t.addEventListener('시험', e => 행.push([라벨, 이름(e.target), 이름(e.currentTarget), e.composedPath().map(이름).join(' ')]));
}
단추.dispatchEvent(new CustomEvent('시험', { bubbles: true, composed: true }));
행.forEach(r => O.push(padw(r[0], 26) + padw(r[1], 14) + padw(r[2], 16) + r[3]));
O.push('');
O.push('★ composedPath() 는 어디서 보든 한 글자도 같다 — 경계 안팎이 같은 배열을 받는다.');
O.push('★ e.target 만 「보는 자리가 경계 밖이면 호스트로」 바뀐다.');
O.push('');

O.push('composed 를 끄면 경계에서 멈춘다');
const 받은곳 = [];
for (const [라벨, t] of 자리) {
  t.addEventListener('안넘', e => 받은곳.push(라벨));
}
단추.dispatchEvent(new CustomEvent('안넘', { bubbles: true, composed: false }));
O.push('  composed:false · bubbles:true  → 받은 자리 = ' + 받은곳.join(' · '));
const 받은곳2 = [];
for (const [라벨, t] of 자리) t.addEventListener('안떠', e => 받은곳2.push(라벨));
단추.dispatchEvent(new CustomEvent('안떠', { bubbles: false, composed: true }));
O.push('  composed:true  · bubbles:false → 받은 자리 = ' + 받은곳2.join(' · '));
O.push('  ★ 두 스위치가 서로 다른 것을 막는다 — bubbles 는 위로 가는 것을, composed 는 경계를 넘는 것을.');
O.push('');

O.push('생성자로 만든 이벤트의 composed 기본값 — 전부 false 다');
const 표 = [];
for (const [형, 만들기] of [['click', () => new MouseEvent('click', { bubbles: true })],
                           ['focus', () => new FocusEvent('focus')],
                           ['input', () => new InputEvent('input', { bubbles: true })],
                           ['keydown', () => new KeyboardEvent('keydown', { bubbles: true })],
                           ['CustomEvent(기본)', () => new CustomEvent('x')],
                           ['Event(기본)', () => new Event('x')]]) {
  표.push(형 + '=' + 만들기().composed);
}
O.push('  ' + 표.join(' · '));
let 실제 = '(안 불림)';
$('host').addEventListener('click', e => { 실제 = 'target=' + 이름(e.target) + ' · composed=' + e.composed + ' · composedPath()[0]=' + 이름(e.composedPath()[0]); });
단추.click();
O.push('  ★ 생성자는 기본이 false 다. 브라우저가 스스로 보내는 것과 다르다.');
O.push('  안쪽 단추.click() (HTMLElement.click) 을 호스트에서 보면 — ' + 실제);
O.push('');

O.push('슬롯에 배정된 자식에서 나는 이벤트는 재타기팅되나');
let 슬롯본것 = '(안 불림)';
document.addEventListener('시험2', e => { 슬롯본것 = 'target=' + 이름(e.target) + ' · composedPath()=' + e.composedPath().map(이름).join(' '); });
$('슬롯자식').dispatchEvent(new CustomEvent('시험2', { bubbles: true, composed: true }));
O.push('  ' + 슬롯본것);
O.push('  ★ 슬롯 자식은 라이트 DOM 에 있으므로 재타기팅되지 않는다. 경로에 <slot> 이 끼어 있을 뿐이다.');
document.body.appendChild(Object.assign(document.createElement('script'),
  {type: 'text/plain', textContent: '\n--OUT\n' + O.join('\n') + '\nOUT--\n'}));
</script>
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-event.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '1,12p'
한 번의 click 을 일곱 자리에서 본다 — e.target 과 composedPath()
리스너를 어디에 달았나    e.target      e.currentTarget composedPath()
안쪽 단추                 #단추         #단추           #단추 #껍데기 #shadow-root #host BODY HTML #document Window
그림자 안 #껍데기         #단추         #껍데기         #단추 #껍데기 #shadow-root #host BODY HTML #document Window
ShadowRoot                #단추         #shadow-root    #단추 #껍데기 #shadow-root #host BODY HTML #document Window
호스트 #host              #host         #host           #단추 #껍데기 #shadow-root #host BODY HTML #document Window
document.body             #host         BODY            #단추 #껍데기 #shadow-root #host BODY HTML #document Window
document                  #host         #document       #단추 #껍데기 #shadow-root #host BODY HTML #document Window
window                    #host         Window          #단추 #껍데기 #shadow-root #host BODY HTML #document Window

★ composedPath() 는 어디서 보든 한 글자도 같다 — 경계 안팎이 같은 배열을 받는다.
★ e.target 만 「보는 자리가 경계 밖이면 호스트로」 바뀐다.
(exit 0)
```

- ★★★ **`e.target` 은 「보는 자리」에 따라 바뀐다.** 그림자 안(단추·`#껍데기`·`ShadowRoot`)에서는 `#단추` 이고, **호스트부터 바깥에서는 전부 `#host`** 다. 이것이 **재타기팅(retargeting)** 이다.
- ★★ **`composedPath()` 는 어디서 보든 한 글자도 같다.** 일곱 줄이 **완전히 동일**하다 — 경계 안팎이 같은 배열을 받는다(`open` 일 때).
- ★ **그래서 위임 리스너에서 진짜 출처를 알려면 `e.composedPath()[0]` 을 쓴다.** `e.target` 은 「어느 컴포넌트가」까지만 알려 준다.
- **`e.currentTarget` 은 재타기팅과 무관하다** — 리스너를 단 자리 그대로다.

```text
   한 번의 클릭, 두 가지 답

   리스너 자리            e.target      composedPath()[0]
   ------------------     ----------    -----------------
   그림자 안 #껍데기      #단추         #단추
   ShadowRoot             #단추         #단추
   ---- 경계 ----
   호스트 #host           #host  <-바뀜  #단추
   document               #host  <-바뀜  #단추
   window                 #host  <-바뀜  #단추

   ★ target 은 '보는 자리에서 볼 수 있는 가장 가까운 조상' 으로 바뀐다
```

### (15) `composed` 와 `bubbles` 는 서로 다른 것을 막는다

**언제 쓰나** — 컴포넌트가 **자기 이벤트를 바깥에 알릴 때.**

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-event.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '14,17p'
composed 를 끄면 경계에서 멈춘다
  composed:false · bubbles:true  → 받은 자리 = 안쪽 단추 · 그림자 안 #껍데기 · ShadowRoot
  composed:true  · bubbles:false → 받은 자리 = 안쪽 단추 · 호스트 #host
  ★ 두 스위치가 서로 다른 것을 막는다 — bubbles 는 위로 가는 것을, composed 는 경계를 넘는 것을.
(exit 0)
```

- **`composed: false` 는 경계에서 멈춘다** — 그림자 안 셋까지만 받고 호스트부터는 못 받는다.
- **`bubbles: false` 는 위로 안 간다** — 그런데 **호스트는 받는다.** 그 자리에서 이벤트의 타깃이 **호스트로 바뀌어** 있어 「타깃 단계」가 한 번 더 성립하기 때문이다.
- ★ **두 스위치가 서로 다른 것을 막는다.** `bubbles` 는 **위로 가는 것**을, `composed` 는 **경계를 넘는 것**을 막는다. 컴포넌트가 바깥에 알릴 이벤트는 **둘 다 켜야** 한다.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-event.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '19,22p'
생성자로 만든 이벤트의 composed 기본값 — 전부 false 다
  click=false · focus=false · input=false · keydown=false · CustomEvent(기본)=false · Event(기본)=false
  ★ 생성자는 기본이 false 다. 브라우저가 스스로 보내는 것과 다르다.
  안쪽 단추.click() (HTMLElement.click) 을 호스트에서 보면 — target=#host · composed=true · composedPath()[0]=#단추
(exit 0)
```

- ★ **생성자로 만든 이벤트는 전부 `composed: false` 가 기본**이다. `new MouseEvent('click')` 조차 그렇다 — **브라우저가 스스로 보내는 클릭과 다르다.**
- **`HTMLElement.click()` 이 만드는 것은 `composed: true`** 다. 그래서 호스트에서 잡히고 `target` 이 호스트로 바뀌어 보였다.
- ★★ **테스트에서 이 차이에 넘어진다** — 합성 이벤트로 짠 테스트가 실제 클릭에서는 다르게 돈다.

```text
   합성 이벤트와 진짜 이벤트가 갈리는 자리

   new MouseEvent('click')          composed = false   경계에서 멈춘다
   el.click()                       composed = true    경계를 넘는다
   사용자가 진짜로 누른 클릭         composed = true    (이 문서는 실입력을 안 던졌다)

   ★ 테스트가 초록인데 실제로는 안 도는 자리가 여기다
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom wa12b-12-event.html 2>/dev/null | sed -n '/^--OUT$/,/^OUT--$/{//!p}' | sed -n '24,26p'
슬롯에 배정된 자식에서 나는 이벤트는 재타기팅되나
  target=#슬롯자식 · composedPath()=#슬롯자식 SLOT #shadow-root #host BODY HTML #document Window
  ★ 슬롯 자식은 라이트 DOM 에 있으므로 재타기팅되지 않는다. 경로에 <slot> 이 끼어 있을 뿐이다.
(exit 0)
```

- **슬롯에 배정된 자식에서 난 이벤트는 재타기팅되지 않는다.** 그 요소가 **라이트 DOM 에 있기 때문**이다.
- **경로에 `<slot>` 이 끼어 있다** — `#슬롯자식 SLOT #shadow-root #host …`. 배정이 **경로에는 반영되고 소유에는 반영되지 않는** 것이 여기서 한 줄로 보인다.
- ★ **이벤트 전파의 정본은 목록의 16번 주제**(전파 3단계)와 목록의 **21번 주제**(`CustomEvent`·`composed`)다. 여기서는 **경계가 무엇을 하는가**까지만 본다.

```text
   두 스위치 격자

                    bubbles: true        bubbles: false
   composed: true   안팎 전부            안쪽 타깃 + 호스트
   composed: false  그림자 안까지만      안쪽 타깃만

   ★ 컴포넌트가 바깥에 알릴 이벤트는 { bubbles: true, composed: true }
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```js
// wa12b-12-form.js
// 만든다
const root = host.attachShadow({ mode: 'open' });          // 또는 'closed'
host.attachShadow({ mode: 'open', serializable: true });    // 직렬화 허락
host.attachShadow({ mode: 'open', slotAssignment: 'manual' });
host.attachShadow({ mode: 'open', delegatesFocus: true });  // 이 문서는 안 던졌다

// 들여다본다
host.shadowRoot            // open 이면 루트, closed 면 null
root.mode  root.host  root.serializable  root.slotAssignment
root.querySelector(...)  root.getElementById(...)  root.activeElement  root.styleSheets

// 경계를 건넌다
el.getRootNode()                    // 가장 가까운 뿌리
el.getRootNode({ composed: true })  // 문서까지
el.ownerDocument                    // 처음부터 문서

// 글자로 꺼낸다
host.getHTML({ serializableShadowRoots: true })   // 허락받은 루트만
host.getHTML({ shadowRoots: [root] })             // 내가 들고 있는 루트

// 슬롯
slot.assignedNodes()  slot.assignedElements()  slot.assignedNodes({ flatten: true })
el.assignedSlot
slot.assign(a, b)                   // slotAssignment: 'manual' 일 때만 뜻이 있다

// 이벤트
e.composedPath()   e.composed
new CustomEvent('x', { bubbles: true, composed: true })
```

```css
/* wa12b-12-form.css */
/* 안쪽 시트에서만 */
:host { }  :host(.켜짐) { }  :host-context(.테마) { }
::slotted(span) { }          /* 배정된 자식 — 이 문서는 던지지 않았다 */

/* 바깥 시트에서 */
#host::part(핵심) { }
```

```html
<!-- wa12b-12-form.html -->
<!-- 마크업 쪽은 HTML 갈래의 10번이 정본이다 -->
<div id="호스트"><template shadowrootmode="open" shadowrootserializable></template></div>
<div id="속" part="핵심"></div>
<div id="가운데" exportparts="핵심: 속것"></div>
```

### 금지 사례 — 형태는 맞는데 뜻이 틀리는 자리

```js
// wa12b-12-bad.js
// 1. 바깥에서 그림자 안을 선택자로 찾는다 — 영영 null 이다
document.querySelector('#안문단');
host.shadowRoot.querySelector('#안문단');       // 이것이 맞다

// 2. closed 를 보안으로 쓴다 — 반환값 한 줄에 뚫린다
const 몰래 = host.attachShadow({ mode: 'closed' });
몰래.innerHTML = '무엇이든';                     // 들고 있으면 그대로 쓴다

// 3. 덤프에 안 보이니 안 생긴 줄 안다
// --dump-dom 은 outerHTML 이고 그림자를 직렬화하지 않는다

// 4. getHTML() 이 그림자를 줄 거라 믿는다
host.getHTML();                                  // ""
host.getHTML({ shadowRoots: [root] });           // 이것이 맞다

// 5. 위임 리스너에서 e.target 으로 안쪽 요소를 찾는다
document.addEventListener('click', e => e.target);            // 호스트다
document.addEventListener('click', e => e.composedPath()[0]); // 이것이 맞다

// 6. 컴포넌트의 CustomEvent 를 composed 없이 보낸다
el.dispatchEvent(new CustomEvent('done', { bubbles: true }));                   // 경계에서 멈춘다
el.dispatchEvent(new CustomEvent('done', { bubbles: true, composed: true }));   // 이것이 맞다

// 7. slot 이름 오타를 화면으로 찾는다
// assignedSlot 이 null 인지부터 본다

// 8. 요소를 다 떼면 기본 내용이 나올 거라 믿는다
slot.assignedNodes().length === 0;               // 공백 텍스트까지 없어야 한다

// 9. part 이름 오타를 cssRules 로 찾는다
// 규칙은 담겨 있다. root.querySelectorAll('[part]') 로 이름을 센다
```

### 어디서 헷갈리나

- **`shadowRoot` 와 `attachShadow` 의 반환값** — 같은 객체인데 **전자는 `closed` 에서 `null`** 이다.
- **`assignedNodes` 와 `assignedElements`** — 텍스트 노드 때문에 길이가 다르다.
- **`getRootNode()` 와 `ownerDocument`** — 앞엣것은 「지금 어느 나무에」, 뒤엣것은 「누가 만들었나」.
- **`::part` 와 `::slotted`** — 앞엣것은 **바깥 시트**에서 안을 꾸미고, 뒤엣것은 **안쪽 시트**에서 들어온 자식을 꾸민다. 방향이 반대다.
- **`composed` 와 `bubbles`** — 이름이 닮은 스위치인데 막는 것이 다르다.

## 어디서 틀리나

### 1. 「덤프에 없으니 안 생겼다」로 읽는다

`--dump-dom` 은 `outerHTML` 이고 **그림자를 직렬화하지 않는다.** (1)에서 네 상자가 전부 비어 보였지만 셋에 그림자가 있었다. **창을 바꿔 물어야 한다.**

### 2. `closed` 를 보안 장치로 쓴다

(3)에서 **갈린 칸이 16 중 3**이었고, 그중 실질은 둘이다. 반환값을 들고 있으면 안을 고쳐 쓸 수 있고 `getRootNode().host` 로 나올 수도 있다.

### 3. 위임 리스너에서 `e.target` 으로 안쪽 요소를 찾는다

(14)에서 **바깥 네 자리가 전부 `#host`** 였다. `e.composedPath()[0]` 이 답이다. 이벤트 위임이 그림자에서 깨지는 이유가 이것이다(목록의 **18번 주제**).

### 4. 컴포넌트의 이벤트에 `composed` 를 안 준다

(15)에서 `composed: false` 는 **그림자 안 셋까지만** 갔다. 그리고 **생성자의 기본값이 `false`** 다.

### 5. `slot` 이름 오타를 화면으로 찾는다

(10)에서 `#미아` 는 **예외도 경고도 없이 `rect.width` 가 0** 이었다. `assignedSlot` 이 `null` 인지부터 본다.

### 6. 기본 내용이 안 나오는데 CSS 를 뒤진다

(11)에서 원인은 **줄바꿈 공백 텍스트 노드**였다. `assignedNodes()` 를 찍으면 한 줄에 드러난다.

### 7. `part` 이름 오타를 `cssRules` 로 찾는다

(9)에서 `#host::part(없는이름)` 규칙은 **담겨 있었다.** 담긴 것과 잡는 것은 다르다.

### 8. `manual` 모드를 켜 놓고 `slot` 속성을 단다

(12)에서 **아무 일도 안 일어났다.** 그리고 자동 모드에서 `assign()` 을 불러도 조용하다 — **양쪽이 다 조용하다.**

### 9. 상속되는 속성과 아닌 속성을 안 가린다

(7)에서 `color`·`font-size` 는 넘어오고 `border` 는 안 넘어왔다. 「바깥 CSS 가 안 먹는다」는 **절반만 맞는 말**이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `open`/`closed` 가 `host.shadowRoot` 하나만 가르는 것 | **명세**(DOM — `shadowRoot` getter 가 `mode` 를 본다) |
| `closed` 에서 `composedPath()` 가 안쪽 칸을 빼는 것 | **명세**(DOM — 경로를 자르는 규칙) |
| 선택자가 경계를 **양방향으로** 못 넘는 것 | **명세**(DOM — 조회는 그 노드의 나무 안에서만) |
| **상속되는 속성만** 넘어오는 것 | **명세**(CSS Scoping — 상속은 flat tree 를 따른다) |
| 슬롯 배정이 **이동이 아닌** 것 | **명세**(DOM — assign 은 flat tree 만 바꾼다) |
| `assignedNodes` 가 **텍스트 노드를 포함**하는 것 | **명세**(DOM) |
| 기본 내용이 **배정이 완전히 빌 때만** 나오는 것 | **명세**(DOM — flat tree 구성) |
| `::part` 가 **한 겹만** 뚫고 `exportparts` 가 필요한 것 | **명세**(CSS Scoping) |
| `:host` 가 **바깥 규칙에 지는** 것 | **명세**(CSS Scoping — cascade 의 tree order) |
| `getHTML()` 의 기본값이 **「안 나옴」** 인 것 | **명세**(HTML — `serializable` 이 opt-in) |
| `attachShadow` 가 특정 요소만 받는 것 | **명세**(DOM — 허용 목록) |
| **예외의 「이름」**(`NotSupportedError`·`TypeError`) | **명세** |
| ★ **예외의 「문구」** | **구현.** 판이 오르면 바뀐다 — 외울 것은 이름이지 문구가 아니다 |
| ★ **`:host-context()`** | **구현.** Chrome 은 지원하고 표준화가 흔들린 표면이다. 여기서는 **Chrome 151 의 관찰**로만 적는다 |
| ★ `getBoundingClientRect` 의 **소수점** | **구현 + 글꼴 + 창 크기** |
| ★ **`slotAssignment: 'manual'`·`serializable`·`getHTML()`** | **명세에는 있고 새 표면**이다. 지원 상태는 갈래 [`../README.md`](../README.md) 의 Baseline 표를 본다 — **이 문서는 다른 엔진에서 던지지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 스타일을 격리한다 | Shadow DOM | class 접두사 규칙(사람이 지켜야 한다) |
| 남이 안을 못 건드리게 한다 | `closed` + 반환값을 클로저에 가둔다 | `closed` 만 믿기(보안이 아니다) |
| 디버깅에서 안을 본다 | `open` | `closed` 로 만들어 놓고 나중에 후회하기 |
| 안쪽 일부만 꾸미게 연다 | `::part` + `exportparts` | 안쪽 class 이름을 문서에 적기(계약이 된다) |
| 컴포넌트가 바깥 테마를 탄다 | 상속되는 속성 · CSS 커스텀 속성 · `:host-context` | 바깥에서 안쪽 선택자 쓰기 |
| 자식을 받는다 | `<slot>` + `assignedSlot` 으로 진단 | `slot` 이름을 눈으로 맞추기 |
| 남의 마크업을 감싼다 | `slotAssignment: 'manual'` + `slot.assign()` | 자식에 `slot` 속성 붙이기 |
| 바깥에 알린다 | `{ bubbles: true, composed: true }` | 기본값에 맡기기 |
| 위임 리스너에서 출처를 찾는다 | `e.composedPath()[0]` | `e.target` |
| 그림자까지 직렬화한다 | `serializable: true` + `getHTML({serializableShadowRoots: true})` | `outerHTML` |
| 마크업만으로 그림자를 만든다 | HTML 갈래의 **10번** 의 선언적 Shadow DOM | 스크립트가 돌기를 기다리기 |

## 핵심 문장

1. **경계가 막는 것은 「이름으로 찾는 길」이고, 참조는 그대로 통한다.**
2. **`open` 과 `closed` 가 실제로 갈리는 칸은 16 중 3이고 실질은 둘이다** — `host.shadowRoot` 와 `composedPath()`. **보안 장치가 아니다.**
3. **선택자는 양방향으로 막히는데 상속은 넘어온다** — 넘어오는 것은 **상속되는 속성뿐**이다.
4. **`::part` 는 한 겹만 뚫는다.** 이름이 틀리면 규칙이 담긴 채 아무것도 안 잡는다.
5. **슬롯 배정은 이동이 아니라 투영이다** — 자식은 라이트 DOM 에 남고 바깥 규칙을 그대로 받는다.
6. **기본 내용은 배정이 완전히 빌 때만 나온다** — 줄바꿈 공백 하나가 막는다.
7. **`e.target` 은 보는 자리에 따라 바뀌고 `composedPath()` 는 안 바뀐다.**
8. **이 주제에서 소리를 내는 것은 `attachShadow` 의 거절뿐이다.** 나머지는 전부 조용하다.
9. **창 ① 은 이 주제에서 부적용이다** — 못 잰 것이 아니라 **잴 것이 없다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 12번)
- HTML 갈래 목록([`html/syntax/README.md`](../../languages/html/syntax/README.md))의 **10번** — ★ **이 주제의 짝.** 그쪽은 **마크업으로**(`<template>` 이 왜 안 사나 · `shadowrootmode` · 슬롯 투영 · 선언적 Shadow DOM 이 덤프에서 어떻게 보이나), 여기는 **만들고 들여다보는 API 로**. **거기 있는 것을 다시 쓰지 않는다**
- [01번 주제](../01-document-and-node-tree/2-summary.md) — 나무를 보는 창 셋. **줄바꿈 공백 텍스트 노드**의 정본
- [05번 주제](../05-documentfragment-and-template/2-summary.md) — `ShadowRoot` 는 **호스트를 가진 `DocumentFragment`** 다. 조각 자체의 성질은 거기가 정본
- [02번 주제](../02-element-queries-and-live-collections/2-summary.md) — 조회가 **어느 범위에서** 도는가. 여기는 그 범위가 **나무 단위로 끊긴다**는 이야기
- [08번 주제](../08-getcomputedstyle/2-summary.md) — 계산값을 읽는 법. 「담겼는데 졌나」의 정본이고, 여기의 `::part` 오타는 **그것과 다른 상태**다
- [10번 주제](../10-layout-thrashing/2-summary.md) — 이 주제는 **명세 쪽**이고 그 주제는 **구현 쪽**이다. 견주어 읽으면 두 갈래의 성격이 갈린다
- [목록의 **13번 주제**](../13-custom-element-lifecycle/)(커스텀 요소 수명주기) — 그림자를 **언제** 붙이나. `button` 에 못 붙이는 것의 실무 해법
- 목록의 **16번 주제**(전파 3단계) · 목록의 **18번 주제**(이벤트 위임) — 재타기팅이 **위임을 어떻게 깨뜨리나**
- 목록의 **21번 주제**(`CustomEvent`·`composed`) — ★ **재타기팅과 `composed` 의 정본은 그쪽**이다. 여기서는 경계가 하는 일까지만
- CSS 갈래 목록([`css/syntax/README.md`](../../languages/css/syntax/README.md))의 **08번** — 선택자와 명시도. `:host` 가 **명시도로 지는 것이 아닌** 이유의 배경

## 용어 풀이

- **섀도 호스트(shadow host)** — 그림자를 매단 요소. `root.host` 가 가리키는 것.
- **섀도 루트(shadow root)** — 그림자 나무의 뿌리. **호스트를 가진 `DocumentFragment`** 이고 `parentNode` 가 `null` 이다.
- **라이트 DOM(light DOM)** — 호스트의 평범한 자식들. 바깥 문서에 그대로 사는 쪽.
- **평탄 트리(flat tree)** — 슬롯 배정을 반영해 **화면에 그려지는 순서로 편** 나무. 상속과 그리기가 이것을 따른다.
- **재타기팅(retargeting)** — 이벤트를 **보는 자리에서 볼 수 있는 가장 가까운 조상**으로 `target` 을 바꾸는 것.
- **`composed`** — 이벤트가 **그림자 경계를 넘을지**. `bubbles` 와 다른 스위치다.
- **`composedPath()`** — 이벤트가 지나갈 전체 경로. **경계 안팎이 같은 배열을 받는다**(`open` 일 때).
- **`::part`** — 호스트가 `part` 속성으로 **이름을 내준** 안쪽 요소를 바깥 시트가 잡는 의사 요소.
- **`exportparts`** — 안쪽 `part` 이름을 **한 겹 더 바깥으로** 내보내는 속성. 이름을 갈아 줄 수 있다.
- **`:host` / `:host-context`** — 안쪽 시트가 **호스트 자신** / **호스트의 조상 조건**을 보고 잡는 선택자.
- **수동 할당(manual slot assignment)** — `slot` 속성 대신 `slot.assign()` 으로 직접 넣는 모드.
- **`flatten`** — `assignedNodes` 옵션. 슬롯 사슬을 끝까지 따라가 **실제로 그려지는 것**을 준다.
- **부적용인 창** — 「재 봤더니 같았다」가 아니라 **잴 것이 없는** 창. 이 주제에서는 `--dump-dom` 트리가 그렇다.

## 더 들어가면

- **`::slotted(선택자)`** 는 안쪽 시트가 **배정돼 들어온 자식**을 꾸미는 길이다. **한 겹만** 잡고 자손은 못 잡는다. **이 문서는 던지지 않았다.**
- **`delegatesFocus: true`** 는 호스트가 포커스를 받으면 안쪽 첫 요소로 넘긴다. **던지지 않았다** — 포커스 이야기는 [목록의 **14번 주제**](../14-dialog-popover-scripting/)의 몫이다.
- **`slotchange` 이벤트**는 배정이 바뀔 때 난다. **관측하지 못했다**(이벤트 갈래의 몫이다).
- **CSS 커스텀 속성(`--x`)은 상속되므로 경계를 넘는다.** 컴포넌트에 테마를 넣는 실무의 정답이 그것인데 **이 문서는 던지지 않았다**(정본은 CSS 갈래).
- **`adoptedStyleSheets`** 로 여러 그림자가 시트 하나를 공유할 수 있다. **던지지 않았다.**
- **`ElementInternals`·폼 참여**(`formAssociated`)는 그림자 안 입력을 바깥 폼에 잇는다. **던지지 않았다.**
- **접근성** — 슬롯된 내용이 접근성 트리에서 어디에 놓이는지는 CDP 로 뜰 수 있지만, **스크린리더가 그것을 어떻게 읽는지는 여전히 못 본다.** 트리는 보조 기술의 **입력**이다.
