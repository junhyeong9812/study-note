# html/syntax/19 — `figure`/`figcaption`·`address`·`hr`·`details` 밖의 잡다한 구조 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 의 [`figure`·`figcaption`](https://html.spec.whatwg.org/multipage/grouping-content.html#the-figure-element)(콘텐츠 모델 — 「`figcaption` 은 첫째 또는 마지막」)·[`hr`](https://html.spec.whatwg.org/multipage/grouping-content.html#the-hr-element)(「문단 수준의 주제 전환 — 또는 `select` 의 선택지 사이 구분선」)·[`address`](https://html.spec.whatwg.org/multipage/sections.html#the-address-element)(「가장 가까운 `article`·`body` 의 **연락처**」)와 [`select` 의 콘텐츠 모델](https://html.spec.whatwg.org/multipage/form-elements.html#the-select-element), [파싱 절의 `hr` 시작 태그 줄](https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-inbody), 그리고 [HTML-AAM](https://w3c.github.io/html-aam/)(편집본 — `figure`·`figcaption`·`address`·`hr` 의 역할과 「figure 요소의 이름 계산」). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 실제로 받은 것이다. 블록마다 던진 명령이 배너로 실려 있고 사람이 옮겨 적지 않았다(캡처 조립기). 하네스는 [17번 주제의 3-answer.md](../17-table-structure/3-answer.md) `## 실행 검증` 절에 있다.\
> ★ **엔진은 Chrome 하나다.** 이 갈래는 **이식성을 주장하지 않는다** — 「두 엔진에서 확인했다」고 적지 않는다.
> **버전** — `api.webstatus.dev` 조회로 **`<figure>`·`<figcaption>`·`<address>`·`<hr>` 는 전부 Baseline widely**(2018-01-29). ★ **`select` 안의 `hr`** 은 명세가 최근에 콘텐츠 모델로 받아들인 자리다 — 관련 항목 **「Customizable `<select>`」 는 Baseline limited** 다(그 기능 전체가 limited 이지 `hr` 한 가지를 따로 잰 것은 아니다).
> **선행** — [11번 주제](../11-sectioning-and-landmarks/2-summary.md)(구획 요소와 랜드마크 — 창 ⑦ 을 연 편. `address` 가 「가장 가까운 `article`·`body`」를 보는 것이 그쪽 구획 개념 위에 선다).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.
> ★★★ **본체는 창 ⑦ 이다** — 이 주제의 요소들은 **모양으로는 거의 아무것도 안 한다**(`address` 는 기울임 하나, `figure` 는 여백 하나). 무엇이 **이름**이 되고 무엇이 **역할**이 되는지는 창 ⑦ 로만 보인다. 창 ① 은 「파서가 위치 위반을 고치나」 한 가지를 확인한다.

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |
| **흔들린다** | CDP 가 쓰는 **포트 번호와 프로필 경로** | 실행마다 다르다 — **출력에는 안 들어간다** |
| **안 흔들린다** | 역할·이름·설명·`nameFrom` | 같은 판이면 결정적이다 |
| **안 흔들린다** | `--dump-dom` 의 자식 순서 | 파서는 결정적이다 |
| **안 흔들린다** | 블록의 `(exit N)` | 파서는 실패하지 않는다 |

★ 이 주제에는 **px 값이 없다** — 머신 사이에서 흔들릴 칸이 없다. 실측 — 이 배치(17\~20)의 캡처 **61블록을 세 번 돌려 61블록 전부 한 글자도 같았다.**

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| **⑦ 접근성 트리**(CDP + 내부 덤프) | ★★★ **쓴다 — 본체** | 「`figcaption` 이 `figure` 의 이름이 되나」((1)) · 「`address`·`hr` 의 역할」((3)·(4)) |
| **① `--dump-dom`** | ★ **쓴다** | 「파서가 가운데 `figcaption`·`select` 안의 `hr` 을 고치나」((2)·(4)) |
| **② 프로브**(`getComputedStyle` · DOM API) | 쓴다 — 조금 | `address` 의 기울임 · `select.options` |
| **③ `innerText` 대 `textContent`** | **부적용** | 이 요소들은 글자를 안 만든다 — **잴 것이 없다** |
| **④·⑤·⑥** | **부적용** | 문서 모드·요청·렌더 차단과 무관하다 — **잴 것이 없다** |

- ★★ **제5의 상태 — 「`address` 가 연락처인가」를 역할로 물었다.** 명세의 좁은 뜻(연락처)을 재는 창은 없다. 가장 가까운 창이 **역할**인데, 그 답은 **`group`** 이다((3)). 「역할로는 안 드러난다」가 결론이고, 그 좁은 뜻을 지키는 것은 **쓰는 사람의 규율**뿐이다.

## 한눈에 — 쉽게 말하면

**★ 그림 옆 설명문은 그림에 「딸린」 글이지 그림의 「이름표」가 아니다. 이 판의 Chrome 도 그렇게 본다.**

**박물관 전시**에 비유한다. 대응은 문서 끝까지 이것 하나로 고정한다.

| 비유 | 실체 |
|---|---|
| **액자 하나**(그림 + 아래 설명판) | **`<figure>`** — 역할 `figure` |
| 액자 아래 **설명판** | **`<figcaption>`** — 명세상 「나머지 내용의 캡션」 |
| 액자 뒤에 붙인 **분류 번호표** | 접근 가능한 **이름** — 설명판이 **저절로 번호표가 되지는 않는다**((1)) |
| 설명판을 **번호표로 쓰겠다고 적어 두기** | `aria-labelledby` 로 `figcaption` 을 가리키기 |
| 전시실 입구의 **「문의: 학예사 ○○○」** | **`<address>`** — 그 전시실(가장 가까운 `article`·`body`)의 **연락처** |
| 관람객의 **집 주소** | `<address>` 가 **아니다** — 연락처가 아닌 주소는 `<p>` |
| 전시실 사이의 **칸막이** | **`<hr>`** — 역할 `separator` |

- **`figcaption` 은 `figure` 의 이름이 아니다.** 이름 칸은 비어 있다((1)). 이름이 필요하면 `aria-labelledby` 로 잇는다.
- **`address` 의 역할은 `group` 이다** — 「연락처」라는 뜻은 역할에 안 실린다((3)).
- **`hr` 은 `select` 안에서도 `hr` 로 남는다** — 파서가 받아들였다((4)).

```text
  figcaption 은 트리에서 어디에 있나

  figure          이름 = ''                 <- 이름 칸은 비었다
    image         이름 = '막대 그래프'       <- 이름은 img 의 alt 에서
    Figcaption    이름 = ''
      StaticText  '그림 1. 월별 방문자'      <- 캡션 글자는 자식으로만 있다

  캡션은 「그림의 자식」으로 읽히지 「그림의 이름」으로 붙지 않는다.
```

> **접근 가능한 이름(accessible name)** — 보조 기술이 그 조각을 부를 때 쓰는 이름. 트리 덤프의 `이름=` 칸이다.\
> 예: `<figure aria-label="…">` 는 이름이 있고, `figcaption` 만 있는 `figure` 는 이름이 비었다.

## 이 주제가 답하려는 질문

1. **`figcaption` 은 `figure` 에 어떻게 묶이나** — 이름인가, 설명인가, 그냥 자식인가. 이름이 필요하면 어떻게 주나.
2. **콘텐츠 모델 위반(가운데 `figcaption`·`figcaption` 둘·`figure` 밖 `figcaption`)을 누가 고치나** — 파서인가, 트리인가, 아무도 아닌가.
3. **`address` 의 좁은 뜻과 `hr` 의 역할은 어느 창에 드러나나.**

## 동작 방식

### (1) 창 ⑦ — `figcaption` 은 `figure` 의 이름이 되지 않는다

**언제 쓰나** — 이 주제의 본체. 「캡션을 달았으니 그림에 이름이 있다」를 확인하는 자리.

`figure` 열 개에 **캡션의 자리·개수·이름 출처**를 하나씩 바꿔 주고, CDP 의 역할·이름·설명과 내부 덤프의 `nameFrom`, DOM 의 자식 순서를 같이 찍었다.

```html
<!-- html17b-19-figure.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>19 그림과 캡션</title>
</head>
<body>
<figure id="f1"><img id="i1" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption>그림 1. 월별 방문자</figcaption></figure>
<figure id="f2"><figcaption>그림 2. 월별 방문자</figcaption><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"></figure>
<figure id="f3"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="앞 그림"><figcaption>그림 3. 가운데 캡션</figcaption><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="뒤 그림"></figure>
<figure id="f4"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"></figure>
<figure id="f5" aria-label="에어리아 이름"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption>그림 5. 캡션</figcaption></figure>
<figure id="f6"><figcaption>첫 캡션</figcaption><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption>둘째 캡션</figcaption></figure>
<figure id="f7" title="제목 속성"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"></figure>
<figure id="f8"><pre>코드 조각</pre><figcaption>예 8. 코드</figcaption></figure>
<figure id="f10" aria-labelledby="캡10"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="막대 그래프"><figcaption id="캡10">그림 10. 이어 붙인 캡션</figcaption></figure>
<div id="f9"><figcaption id="밖캡션">figure 밖의 figcaption</figcaption></div>
<script>
const 설명 = { f1: "img + 끝 figcaption", f2: "첫 figcaption + img", f3: "가운데 figcaption", f4: "img alt 만",
  f5: "aria-label + figcaption", f6: "figcaption 둘", f7: "title + img", f8: "pre + figcaption", f10: "aria-labelledby=캡션 id", f9: "figure 밖 figcaption" };
const 키 = Object.keys(설명);
window.__대상 = [...키.map(k => [k, "#" + k]), ["i1", "#i1"], ["밖캡션", "#밖캡션"]];
window.__내부 = true;
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = ["figure 마다 — CDP 역할·이름·설명 · 이름의 출처(내부 덤프 nameFrom) · 자식 순서(DOM)"];
  for (const k of 키) {
    const a = __AX[k], n = __INT[k];
    const 자식 = [...document.getElementById(k).children].map(e => e.localName).join(" ");
    O.push("  " + 설명[k].padEnd(24) + "역할 = " + a.역할.padEnd(8) + "이름 = " + J(a.이름).padEnd(20) + "설명 = " + J(a.설명).padEnd(14)
      + "nameFrom = " + ((n && n.속성.nameFrom) || "—").padEnd(15) + "자식 = " + 자식);
  }
  O.push("");
  O.push("  f1 안의 img  역할 = " + __AX.i1.역할 + " · 이름 = " + J(__AX.i1.이름));
  O.push("  figure 밖 figcaption  역할 = " + __AX["밖캡션"].역할 + " · 이름 = " + J(__AX["밖캡션"].이름));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-19-figure.html
figure 마다 — CDP 역할·이름·설명 · 이름의 출처(내부 덤프 nameFrom) · 자식 순서(DOM)
  img + 끝 figcaption      역할 = figure  이름 = ""                  설명 = ""            nameFrom = —              자식 = img figcaption
  첫 figcaption + img      역할 = figure  이름 = ""                  설명 = ""            nameFrom = —              자식 = figcaption img
  가운데 figcaption          역할 = figure  이름 = ""                  설명 = ""            nameFrom = —              자식 = img figcaption img
  img alt 만               역할 = figure  이름 = ""                  설명 = ""            nameFrom = —              자식 = img
  aria-label + figcaption 역할 = figure  이름 = "에어리아 이름"           설명 = ""            nameFrom = attribute      자식 = img figcaption
  figcaption 둘            역할 = figure  이름 = ""                  설명 = ""            nameFrom = —              자식 = figcaption img figcaption
  title + img             역할 = figure  이름 = "제목 속성"             설명 = ""            nameFrom = title          자식 = img
  pre + figcaption        역할 = figure  이름 = ""                  설명 = ""            nameFrom = —              자식 = pre figcaption
  aria-labelledby=캡션 id   역할 = figure  이름 = "그림 10. 이어 붙인 캡션"   설명 = ""            nameFrom = relatedElement 자식 = img figcaption
  figure 밖 figcaption     역할 = generic 이름 = ""                  설명 = ""            nameFrom = —              자식 = figcaption

  f1 안의 img  역할 = image · 이름 = "막대 그래프"
  figure 밖 figcaption  역할 = Figcaption · 이름 = ""
(exit 0)
```

```text
  figure 의 이름 — HTML-AAM 「figure 요소의 이름 계산」

  aria-label / aria-labelledby   ->  이름      (#f5 · #f10)
  title                          ->  이름      (#f7)
  그 밖                          ->  이름 없음 (figcaption 이 있어도 · img alt 가 있어도)

  ★ 명세 문장: 「figcaption 은 이름·설명 계산에 참여하지 않는다 — 저자가 명시적으로 가리키지 않는 한」
```

- ★★★ **`figcaption` 이 있는 `figure` 넷(`#f1`·`#f2`·`#f3`·`#f8`)의 이름이 전부 빈 문자열**이다. 설명도 비었다. `nameFrom` 도 없다.
- ★★ **이것은 명세 그대로다.** HTML-AAM 편집본의 「figure 요소의 이름 계산」은 「**`figcaption` 은 부모 `figure` 에 대한 추가 정보를 준다 — 저자가 명시적으로 가리키지 않는 한 이름·설명 계산에 참여하지 않는다**」로 시작하고, 이름 출처를 **`aria-label`·`aria-labelledby` → `title`** 둘로만 적는다. 이 판이 그대로 따랐다(`#f5`·`#f7`).
- ★★ **`aria-labelledby` 로 `figcaption` 을 가리키면 이름이 된다**(`#f10` — `nameFrom = relatedElement`). 「명시적으로 가리킨」 경우다.
- ★ **`img alt` 는 `figure` 의 이름이 아니다**(`#f4`) — 이름은 **안쪽 `image` 노드**에 있다(`'막대 그래프'`). 그림 전체의 이름과 그림 안 이미지의 이름은 다른 칸이다.
```text
$ python3 html17b-cdp.py int html17b-19-figure.html nameFrom,htmlTag | sed -n '1,8p'
rootWebArea             nameFrom=relatedElement htmlTag=#document
      figure         #f1      htmlTag=figure
        image          #i1      nameFrom=attribute htmlTag=img
        figcaption              htmlTag=figcaption
      figure         #f2      htmlTag=figure
        figcaption              htmlTag=figcaption
        image                   nameFrom=attribute htmlTag=img
      figure         #f3      htmlTag=figure
(exit 0)
```

- ★ **`figcaption` 의 역할 이름이 `Figcaption`** 이다(CDP — 위 블록의 끝줄. 내부 덤프는 소문자 `figcaption`) — HTML-AAM 은 `figcaption` 을 **`caption` 역할**에 대응시킨다. `caption` 이 아니라 **Chrome 의 자기 이름**이 찍혔다 — [13번 주제](../13-phrasing-semantics/2-summary.md) 의 `Abbr` 와 같은 꼴의 **명세 ↔ 구현 불일치**다.

> **`nameFrom`** — 내부 덤프가 적는 「이름이 어디서 왔나」. `attribute`(aria-label) · `title` · `relatedElement`(aria-labelledby) 등.\
> 예: `#f10` 은 `relatedElement` — 다른 요소(`figcaption`)를 가리켜 이름을 받았다.

### (2) 창 ① + 창 ⑦ — 위치를 어긴 `figcaption` 은 파서도 트리도 안 고친다

**언제 쓰나** — `figcaption` 을 두 이미지 사이에 넣었을 때 · 둘을 넣었을 때 · `figure` 밖에 썼을 때.

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-19-figure.html 2>/dev/null | grep -n 'id="f3"'
9:<figure id="f3"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="앞 그림"><figcaption>그림 3. 가운데 캡션</figcaption><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="뒤 그림"></figure>
(exit 0)
```

```text
$ python3 html17b-cdp.py ax html17b-19-figure.html | sed -n '1,16p'
RootWebArea    이름='19 그림과 캡션'
  figure         이름=''
    image          이름='막대 그래프'
    Figcaption     이름=''
      StaticText     이름='그림 1. 월별 방문자'
  figure         이름=''
    Figcaption     이름=''
      StaticText     이름='그림 2. 월별 방문자'
    image          이름='막대 그래프'
  figure         이름=''
    image          이름='앞 그림'
    Figcaption     이름=''
      StaticText     이름='그림 3. 가운데 캡션'
    image          이름='뒤 그림'
  figure         이름=''
    image          이름='막대 그래프'
(exit 0)
```

```text
  콘텐츠 모델 — 「figcaption 은 첫째 또는 마지막, 하나」

  #f3   img figcaption img        위반   파서: 그대로   트리: 그대로 (가운데 Figcaption)
  #f6   figcaption img figcaption 위반   파서: 그대로   (1) 의 자식 순서
  #f9   div > figcaption          위반   파서: 그대로   트리: Figcaption, 부모는 generic

  위반을 고치는 층이 없다 — 검사기(validator)만 잡는다.
```

- ★★ **가운데 `figcaption` 이 DOM 에서 그대로 가운데다**(`#f3` — `img` · `figcaption` · `img`). 파서는 `figcaption` 의 **위치를 고치지 않는다** — [05번 주제](../05-content-categories-and-models/2-summary.md) (4) 의 「파서가 안 고치는 것」과 같은 부류다.
- ★ **트리도 그대로 옮겼다** — `image` · `Figcaption` · `image` 순서다. 캡션이 **어느 그림에 딸린 것인지** 트리는 말하지 않는다.
- ★ **`figcaption` 둘도, `figure` 밖의 `figcaption` 도 그대로다.** 밖의 것도 역할은 `Figcaption` 이다 — [05번 주제](../05-content-categories-and-models/2-summary.md) (6) 가 「부모 없이 쓴 `figcaption` 은 사라지지 않는다」로 먼저 캡처했다.

### (3) 창 ⑦ + 창 ② — `address` 의 역할은 `group` 이다

**언제 쓰나** — 「주소니까 `<address>`」로 태그를 고르려 할 때.

```html
<!-- html17b-19-misc.html -->
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>19 address 와 hr</title>
</head>
<body>
<address id="a1">홍길동 · <a href="mailto:hong@example.com">hong@example.com</a></address>
<article id="글"><h2>기사</h2><p>본문</p><address id="a2">글쓴이 연락처 · <a href="tel:+82-2-000-0000">02-000-0000</a></address></article>
<address id="a3" aria-label="연락처">서울시 어딘가 1</address>
<p id="p1">앞</p>
<hr id="h1">
<p>뒤</p>
<select id="고르기"><option>가</option><hr id="h2"><option>나</option></select>
<div id="d1" role="separator"></div>
<script>
window.__대상 = [["a1", "#a1"], ["a2", "#a2"], ["a3", "#a3"], ["h1", "#h1"], ["h2", "#h2"], ["d1", "#d1"], ["글", "#글"]];
window.__내부 = true;
const J = v => JSON.stringify(v);
window.__끝 = () => {
  const O = ["요소마다 — CDP 역할·이름 · 무시 여부 · 내부 덤프 역할 · 부모(DOM)"];
  for (const [k] of window.__대상) {
    const a = __AX[k], n = __INT[k], e = document.getElementById(k);
    O.push("  #" + k.padEnd(4) + ("<" + e.localName + (e.getAttribute("role") ? " role=" + e.getAttribute("role") : "") + ">").padEnd(22)
      + "CDP 역할 = " + (a.무시 ? "(무시)" : a.역할).padEnd(11) + "이름 = " + J(a.이름).padEnd(8)
      + "내부 = " + (n ? (n.속성.ignored ? "(무시)" : n.역할) : "(덤프에 없음)").padEnd(18) + "부모 = <" + e.parentElement.localName + ">");
  }
  O.push("");
  O.push("  address 셋의 계산 font-style = " + ["a1", "a2", "a3"].map(k => getComputedStyle(document.getElementById(k)).fontStyle).join(" · "));
  O.push("  select.options.length = " + document.getElementById("고르기").options.length
    + " · select 의 자식 = " + [...document.getElementById("고르기").children].map(e => e.localName).join(" "));
  return O.join("\n");
};
</script>
</body>
</html>
```

```text
$ python3 html17b-cdp.py page html17b-19-misc.html
요소마다 — CDP 역할·이름 · 무시 여부 · 내부 덤프 역할 · 부모(DOM)
  #a1  <address>             CDP 역할 = group      이름 = ""      내부 = group             부모 = <body>
  #a2  <address>             CDP 역할 = group      이름 = ""      내부 = group             부모 = <article>
  #a3  <address>             CDP 역할 = group      이름 = "연락처"   내부 = group             부모 = <body>
  #h1  <hr>                  CDP 역할 = separator  이름 = ""      내부 = splitter          부모 = <body>
  #h2  <hr>                  CDP 역할 = separator  이름 = ""      내부 = splitter          부모 = <select>
  #d1  <div role=separator>  CDP 역할 = separator  이름 = ""      내부 = splitter          부모 = <body>
  #글   <article>             CDP 역할 = article    이름 = ""      내부 = article           부모 = <body>

  address 셋의 계산 font-style = italic · italic · italic
  select.options.length = 2 · select 의 자식 = option hr option
(exit 0)
```

```text
$ google-chrome --headless --disable-gpu --no-sandbox --window-size=1000,800 --dump-dom html17b-19-misc.html 2>/dev/null | grep -n '<select'
13:<select id="고르기"><option>가</option><hr id="h2"><option>나</option></select>
(exit 0)
```

```text
  address 가 뜻하는 것과 트리가 받는 것

  명세의 뜻      「가장 가까운 article 또는 body 의 연락처」
                  - body 안이면 문서 전체의 연락처
                  - article 안이면 그 글의 연락처
                  - 연락처가 아닌 주소(우편 주소 일반)에는 쓰지 않는다 -> <p>

  트리의 역할    group        (#a1 · #a2 · #a3 셋 다)
  화면           font-style: italic   (셋 다)

  「연락처」도 「어느 article 의 연락처인가」도 역할에는 안 실린다.
```

- ★★★ **`address` 셋의 역할이 전부 `group`** 이다 — `body` 안이든 `article` 안이든. HTML-AAM 의 대응(`address` → `group`)과 같다. ★ **`group` 은 「묶음」이라는 뜻뿐**이다 — **「연락처」라는 명세의 좁은 뜻은 역할에 안 드러난다.** 어느 `article` 에 딸린 연락처인지도 안 드러난다.
- ★★ **그래서 「`address` 는 주소가 아니라 연락처」라는 규칙은 어느 창도 지켜 주지 않는다.** 우편 주소를 `<address>` 로 감싸도 트리는 똑같이 `group` 이다. 명세 문장이 유일한 근거다 — 「임의의 주소(예: 우편 주소)를 나타내는 데 쓰면 안 된다 — 그것이 실제로 연락처가 아닌 한」.
- **`aria-label` 을 주면 이름이 붙는다**(`#a3` — `"연락처"`). 역할은 여전히 `group`.
- **모양은 기울임 하나다**(`font-style = italic`) — 렌더링 절의 `address { font-style: italic }`.

> **`group` 역할** — 「관련된 것들의 묶음」. 랜드마크도 아니고 특별한 뜻도 없다.\
> 예: `address`·`details`·`hgroup` 이 HTML-AAM 에서 이 역할을 받는다.

### (4) 창 ⑦ + 창 ① — `hr` 은 `separator`, `select` 안에서도

**언제 쓰나** — 주제 전환 구분선을 넣을 때 · 선택지 목록을 나눌 때.

(3) 과 같은 파일이다. `body` 의 `hr`, `select` 안의 `hr`, `role="separator"` 를 준 `div` 를 나란히 찍었다.

```text
  hr 세 자리

  <hr>                 CDP separator · 내부 splitter
  <select><hr>         CDP separator · 내부 splitter    DOM: select > option hr option
  <div role=separator> CDP separator · 내부 splitter

  ★ 명세: hr = 「문단 수준의 주제 전환」 또는 「select 의 선택지 사이 구분선」
     파서: select 가 열려 있어도 hr 을 넣는다 · 콘텐츠 모델도 hr 을 받는다
     HTML-AAM: separator — select 안이면 none 으로 노출해도 된다(MAY)
```

- ★★ **`hr` 의 역할은 `separator`** 다 — HTML-AAM 대응 그대로. 내부 덤프의 이름은 **`splitter`** 로 찍혔다(Chrome 내부 이름 — CDP 는 `separator` 로 바꿔 보여 준다).
- ★★ **`select` 안의 `hr` 이 DOM 에 남았다**(`select > option hr option`) — 파싱 절의 `hr` 시작 태그 줄이 「`select` 가 열려 있으면 암묵 끝 태그를 만들고 **`hr` 을 넣는다**」로 적고, `select` 의 콘텐츠 모델도 `hr` 을 받는다. `select.options.length` 는 2 — `hr` 은 **선택지가 아니다.**
- ★ **`select` 안의 `hr` 도 `separator`** 다. HTML-AAM 은 「`select` 의 자손이면 `none` 으로 노출**해도 된다**(MAY)」고 적는다 — **`separator` 로 둔 것도 명세 안이다.** 불일치가 아니라 **구현이 고른 한쪽**이다.

### `details`/`summary` — 경계만

`details`·`summary` 는 이 주제 이름의 「밖」이다. **스크립트 없이 여닫는 표면**이라 목록의 **48번 주제**(`details`/`summary` 와 `popover` 속성)가 정본이다. 여기서는 재지 않았다.

## 문법 — 형태와 규칙

HTML 은 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

| 요소 | 명세의 뜻 | 콘텐츠 모델·자리 | 이 판의 역할 |
|---|---|---|---|
| `<figure>` | 본문에서 참조되는 **독립 단위**(그림·코드·인용) | `figcaption` **첫째 또는 마지막, 하나** + 흐름 콘텐츠 | `figure` · 이름은 `aria-*`·`title` 에서만 |
| `<figcaption>` | 부모 `figure` 의 **나머지 내용의 캡션** | `figure` 의 첫째·마지막 자식 | `Figcaption`(Chrome 이름 — AAM 은 `caption`) |
| `<address>` | 가장 가까운 `article`·`body` 의 **연락처** | 흐름 콘텐츠(제목·구획·`header`·`footer`·`address` 자손 없이) | `group` |
| `<hr>` | 문단 수준의 **주제 전환** · `select` 의 구분선 | 흐름 콘텐츠 · `select` 안 | `separator` |

### 어디서 헷갈리나

- **`figure` 는 「그림」 전용이 아니다.** 코드 조각·인용·표도 된다(`#f8` 의 `pre`). 「본문에서 떼어도 뜻이 서는 단위」면 된다.
- **`figcaption` 은 `alt` 를 대신하지 않는다.** 이미지의 이름은 **`img` 의 `alt`** 에서 온다(`#f1` 의 `image` 노드). `figcaption` 은 그림 전체에 딸린 글이다.
- **`address` 는 「글쓴이 정보」도 아니다.** 연락처가 아닌 약력은 `address` 가 아니다 — 명세가 「연락처 외의 정보를 담으면 안 된다」고 적는다.

## 어디서 틀리나

### 1. `figcaption` 을 달았으니 그림에 이름이 있다고 여긴다

**이름 칸은 비었다**((1) — 넷 다 `""`). 명세(HTML-AAM)도 그렇게 적는다.\
그림을 **이름으로 불러야 하는** 자리(그림 목록·랜드마크 탐색)라면 `aria-labelledby` 로 캡션을 잇는다.

```text
  <figure>                                  <figure aria-labelledby="캡">
    <img alt="막대 그래프">                    <img alt="막대 그래프">
    <figcaption>그림 1. …</figcaption>         <figcaption id="캡">그림 1. …</figcaption>
  </figure>                                 </figure>

  figure 이름 = ''                          figure 이름 = '그림 1. …'   (nameFrom relatedElement)
```

### 2. 캡션을 이미지 사이에 둔다

**파서도 트리도 안 고친다**((2)). 캡션이 어느 그림의 것인지 **트리에는 순서 말고 단서가 없다.**

### 3. 우편 주소를 `<address>` 로 감싼다

**트리는 `group` 을 준다 — 어느 창도 막지 않는다**((3)). 명세 위반은 **쓰는 사람만** 안다.\
연락처가 아닌 주소는 `<p>` 다.

```text
  <address> 를 쓸지 가르는 두 질문 — 명세 문장에서

  이 글자가 「이 글(article) 또는 이 문서(body)에 대해 누구에게 연락하나」인가?
          │
          ├── 예 ──> <address>   (이메일·전화·담당자·그 연락처의 주소)
          │
          └── 아니오 ─> 그냥 주소·약력·회사 소개 ──> <p> 등
```

### 4. `select` 선택지를 나누려고 비활성 `option` 을 쓴다

이제는 **`hr` 을 넣을 수 있다**((4) — DOM 에 남고 `separator` 역할이며 `options` 에 안 센다). ★ 다만 이 자리는 **Customizable `<select>` 와 같이 들어온 변화**라 Baseline 은 limited 다 — **다른 엔진의 파서가 받아들이는지는 이 판에서 못 봤다.**

## 구현 세부사항 대 언어 보장

★ 세 층으로 갈라 적는다 — **명세(WHATWG HTML · HTML-AAM)가 보장하는 것 / Chrome 151 이 구현한 것 / 이 판에서 관찰한 것.**

| 층 | 무엇을 | 이 주제에서 |
|---|---|---|
| **명세(HTML)** | `figcaption` 자리(첫째·마지막) · `address` = 연락처 · `hr` = 주제 전환·`select` 구분선 | 문법 절 |
| **명세(HTML 파싱)** | `figcaption` 위치를 **안 고친다**(특별 규칙 없음) · `select` 안의 `hr` 을 **넣는다** | (2)·(4) |
| **명세(HTML-AAM)** | `figure` 이름 = `aria-*` → `title` · **`figcaption` 은 이름 계산에 참여 안 함** · `figcaption` → `caption` · `address` → `group` · `hr` → `separator`(`select` 안이면 `none` 도 됨) | (1)·(3)·(4) |
| **구현(Chrome)** | `figcaption` 의 역할 이름 **`Figcaption`** | (1) — ★ 명세(`caption`)와 갈렸다 |
| **구현(Chrome)** | `select` 안의 `hr` 을 `separator` 로 둔 것 | (4) — 명세가 허용한 두 길 중 하나 |
| **구현(Chrome)** | 내부 덤프의 `splitter` | (4) — 내부 이름 |

**도구가 못 보는 것**

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **스크린리더가 `figure` 에 들어가며 캡션을 읽는지** | 이 판에 **NVDA·VoiceOver·Orca 가 없다.** 캡션은 트리에 **자식 글자**로 있다 — 그것을 언제 읽는지는 보조 기술의 일이다 |
| ★★ **`address` 를 「연락처」로 알려 주는 보조 기술이 있는지** | 역할이 `group` 뿐이라 트리에 단서가 없다 — 그 뒤는 못 본다 |
| **플랫폼 API 층**(`figcaption` 의 `IA2_RELATION_LABEL_FOR` 류 관계) | CDP·내부 덤프는 그 위 층이다 |
| **다른 엔진의 `select` 안 `hr` 파싱** | 엔진이 하나뿐이다 |

## 언제 쓰고 언제 안 쓰나

- **본문에서 「그림 3 을 보라」처럼 떼어 참조하는 단위에 `figure`** — 그림·코드·표·인용 전부 된다.
- **캡션은 `figcaption` 으로, 첫째나 마지막에 하나** — 가운데 두면 아무도 안 고친다.
- **그림을 이름으로 불러야 하면 `aria-labelledby` 로 캡션을 잇는다** — 저절로는 이름이 안 된다.
- **이미지의 이름은 `alt` 로** — 캡션과 `alt` 는 다른 칸이다(`alt` 판단은 목록의 **44번 주제**).
- **`address` 는 그 글·그 문서의 연락처에만** — 우편 주소 일반은 `<p>`.
- **`hr` 은 주제가 바뀌는 자리에만** — 단순한 선은 CSS `border` 다. `select` 구분선으로도 쓸 수 있다(Baseline limited).

## 핵심 문장

1. **`figcaption` 은 `figure` 의 이름이 되지 않는다 — 이 판도 그렇고 HTML-AAM 편집본도 「명시적으로 가리키지 않는 한 참여하지 않는다」고 적는다.**
2. **`figure` 의 이름은 `aria-label`·`aria-labelledby`·`title` 에서만 온다 — `aria-labelledby` 로 캡션을 가리키면 그것이 이름이 된다.**
3. **위치를 어긴 `figcaption` 은 파서도 트리도 고치지 않는다.**
4. **`address` 의 역할은 `group` 이다 — 「연락처」라는 좁은 뜻은 어느 창에도 안 드러난다.**
5. **`hr` 은 `separator` 이고, `select` 안에서도 DOM 에 남아 `separator` 가 된다.**
6. **`figcaption` 의 역할 이름 `Figcaption` 은 Chrome 이 붙인 것이다 — HTML-AAM 은 `caption` 에 대응시킨다.**

## 관련 자료

- [11번 주제 — 구획 요소와 랜드마크](../11-sectioning-and-landmarks/2-summary.md) — `address` 가 보는 **「가장 가까운 `article`·`body`」** 라는 구획 개념과 창 ⑦ 의 뿌리가 그쪽이다.
- [05번 주제 — 콘텐츠 카테고리와 콘텐츠 모델](../05-content-categories-and-models/2-summary.md) — 「파서가 안 고치는 것」((4))과 `figure` 밖 `figcaption` 이 사라지지 않는 것((6))의 정본.
- [13번 주제 — 구절 시맨틱](../13-phrasing-semantics/2-summary.md) — `Abbr` 처럼 **Chrome 이 자기 이름으로 채운 역할**의 첫 사례. 여기의 `Figcaption` 이 같은 꼴이다.
- [17번 주제 — 표 구조](../17-table-structure/2-summary.md) — `caption` 은 **표의 이름이 된다.** 같은 「캡션」인데 `figcaption` 은 이름이 안 된다 — 두 요소의 이름 계산 규칙이 다르다.
- 목록의 **43번 주제**(접근 가능한 이름 계산) · **44번 주제**(`alt` 판단) — 이름 계산 전체와 이미지 `alt` 의 정본.
- 목록의 **48번 주제**(`details`/`summary` 와 `popover`) — 이 주제가 뺀 `details` 의 정본.

## 용어 풀이

- **캡션(caption)** — 무엇에 딸린 설명문. 표의 `caption` 은 이름이 되고, `figure` 의 `figcaption` 은 이름이 안 된다.
- **접근 가능한 이름** — 보조 기술이 그 조각을 부를 때 쓰는 이름.
- **`relatedElement`** — 다른 요소를 가리켜(`aria-labelledby`) 받은 이름이라는 `nameFrom` 값.
- **`group` 역할** — 뜻 없는 「관련된 것들의 묶음」.
- **`separator` 역할** — 구획을 나누는 선. Chrome 내부 이름은 `splitter`.
- **Customizable `<select>`** — `select` 안에 `hr`·`div`·`button` 등을 받아들이는 최근 변화. Baseline limited.

## 더 들어가면

- **HTML-AAM 의 판마다 이 규칙이 같았나** — 이 문서는 **편집본 하나만 열었다.** 옛 판의 문장은 확인하지 않았으므로, 편집본의 현재 문장과 이 판의 트리가 **같다**는 것까지만 적는다.
- **`figure` 와 `aria-describedby`** — 캡션을 이름이 아니라 **설명**으로 잇고 싶으면 `aria-describedby` 다. 이 판에서 재지 않았다.
- **`search`·`hgroup`** — 「잡다한 구조」의 이웃들. `search` 는 [11번 주제](../11-sectioning-and-landmarks/2-summary.md)가 랜드마크로 다뤘고, `hgroup` 은 [12번 주제](../12-heading-levels-and-outline/2-summary.md)의 제목 개요 쪽이다.
