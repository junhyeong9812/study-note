# html/syntax/19 — `figure`/`figcaption`·`address`·`hr`·`details` 밖의 잡다한 구조 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 출력은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려** 받은 것이다. 블록은 캡처 조립기로 붙였다. 하네스(`html17b-cdp.py`·`capture.sh`)는 [17번 주제의 3-answer.md](../17-table-structure/3-answer.md) `## 실행 검증` 절에 있다.\
> 규칙은 [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/) 와 [HTML-AAM](https://w3c.github.io/html-aam/) 으로 접지했다.\
> ★ **엔진은 Chrome 하나다** — 이 갈래는 이식성을 주장하지 않는다.
> ★★★ **본체는 창 ⑦ 이다.** `figcaption` 은 이름이 아니고(A1), `address` 의 뜻은 역할에 안 실린다(A3).

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `figcaption` 만 있는 `figure` 는 이름이 비었다 — 이름은 `aria-label`·`title`·`aria-labelledby` 에서만

**출력**

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

**왜 그런가**

- ★★★ **`#f1`·`#f2`·`#f3`·`#f6`·`#f8` — 이름·설명 둘 다 빈 문자열, `nameFrom` 없음.** `figcaption` 이 첫째든 마지막이든 가운데든, 둘이든 그렇다.
- **`#f4`(img alt 만)도 이름 없음** — `alt` 는 안쪽 `img` 의 이름이다(`image` · `"막대 그래프"`).
- **`#f5` = `"에어리아 이름"`(`attribute`) · `#f7` = `"제목 속성"`(`title`) · `#f10` = 캡션 글자(`relatedElement`)** — HTML-AAM 의 이름 출처 그대로다.
- ★ **`figure` 밖의 `figcaption` 은 `Figcaption`** — Chrome 의 자기 이름이다(HTML-AAM 은 `caption`). 감싼 `div` 는 `generic`.

### 2. 파서도 트리도 순서를 그대로 둔다

**출력**

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

**왜 그런가**

- ★★ **DOM — `img` · `figcaption` · `img`**, 트리 — `image` · `Figcaption` · `image`. 파싱 절에는 `figcaption` 의 위치를 바꾸는 규칙이 **없다** — 「in body」 모드의 보통 블록 요소로 처리된다.
- ★ **`#f6`·`#f9` 도 그대로다** — (A1 의 자식 순서 칸 · `figure` 밖 `figcaption` 의 역할 줄). [05번 주제](../05-content-categories-and-models/2-summary.md) (6) 의 「부모 없이 쓴 자식 일곱 중 `td` 만 사라진다」와 같다.

### 3. `address` 는 셋 다 `group` · `hr` 은 셋 다 `separator` — `select` 안의 `hr` 은 DOM 에 남는다

**출력**

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

**왜 그런가**

- ★★★ **`address` 셋 — `group`.** `body` 안(`#a1`)과 `article` 안(`#a2`)이 **같다.** `aria-label` 을 준 `#a3` 만 이름 `"연락처"` 가 붙었다. HTML-AAM 대응이 `address` → `group` 이다.
- ★★ **`hr` 셋 — CDP `separator`, 내부 `splitter`.** `role="separator"` 를 준 `div` 와 같다.
- ★★ **`select` 의 자식 = `option` · `hr` · `option`, `options.length = 2`** — `hr` 은 DOM 에 남되 **선택지로 세지 않는다.**
- **`font-style = italic` 셋** — 렌더링 절의 `address { font-style: italic }`. 모양으로 남는 것은 그것뿐이다.

### 4. HTML-AAM 은 `figure` 의 이름 출처를 `aria-*` 와 `title` 로만 적고, `figcaption` 은 「참여하지 않는다」고 적는다

- **이름 출처** — 「`aria-label`·`aria-labelledby` 가 있으면 이름 계산 알고리즘으로」 → 「아니면 `title`」 → 「둘 다 없으면 이름 없음」. **`figcaption` 에 대해서는** 「부모 `figure` 에 관한 추가 정보를 준다 — **저자가 명시적으로 가리키지 않는 한 이름·설명 계산에 참여하지 않는다**」.
- **`#f10`** — `aria-labelledby="캡10"` 으로 `figcaption` 을 가리켰다. `nameFrom = relatedElement` 는 「**다른 요소를 가리켜 받은 이름**」이라는 뜻이다. 명세가 말한 「명시적으로 가리킨」 경우다.
- **`#f4` 의 `alt` 글자는 안쪽 `image` 노드의 이름 칸**에 있다(A1 · 요약 (1) 의 트리). `figure` 노드의 이름 칸이 아니다.

### 5. ① 과 ③ 은 `address`, ② 와 ④ 는 아니다 — 트리는 판단을 못 도와준다

- **① 기사의 기자 이메일** — 그 `article` 의 연락처다 → `address`. **③ 회사 소개 페이지 맨 아래의 대표 전화** — 그 문서(`body`)의 연락처다 → `address`.
- **② 배송지** — 연락처가 아닌 주소다 → `<p>`. 명세가 「임의의 주소(예: 우편 주소)에 쓰면 안 된다 — 실제로 관련 연락처가 아닌 한」이라고 적는다. **④ 약력** — 「연락처 외의 정보를 담으면 안 된다」.
- ★★ **트리는 못 도와준다** — 넷을 전부 `<address>` 로 감싸도 역할은 `group` 이다(A3). 「연락처인가」를 역할로 물은 것은 **제5의 상태**(창을 바꿔 물었다)이고, 그 창의 답이 「**구별 없음**」이다. 그 뜻을 지키는 것은 **쓰는 사람의 규율**뿐이다.

### 6. 표의 `caption` 은 이름이 되고 `figcaption` 은 안 된다 — 역할은 `figcaption` 쪽만 Chrome 이름으로 찍혔다

- **이름** — HTML-AAM 「table 요소의 이름 계산」은 **`aria-*` 다음에 「첫 child `caption` 의 하위 트리」** 를 쓴다([17번 주제](../17-table-structure/2-summary.md) (5) — `nameFrom = caption`). 「figure 요소의 이름 계산」은 **`figcaption` 을 넣지 않는다**(A4). **같은 「캡션」인데 규칙이 다르다.**
- **역할** — HTML-AAM 은 둘 다 **`caption`** 역할에 대응시킨다. 내부 덤프에서는 표의 것이 **`caption`**([18번 주제](../18-table-headers-and-scope/2-summary.md) (4) 의 덤프 셋째 줄), `figcaption` 이 **`figcaption`**(요약 (1) 의 내부 덤프)이고, **CDP 는 `figcaption` 을 `Figcaption` 으로** 찍었다 — `caption` 이 아니다. ★ 표 `caption` 의 CDP 역할은 이 배치의 캡처 블록에 없다 — 대조는 내부 덤프끼리만 한다.

### 7. 불일치는 `Figcaption` 하나 — `select` 안 `hr` 은 명세가 허용한 두 길 중 하나

- ★★ **`figcaption` 의 역할 이름 `Figcaption`** — HTML-AAM 은 `caption`. [13번 주제](../13-phrasing-semantics/2-summary.md) 의 `Abbr` 와 같은 꼴(명세에 있는 역할 대신 Chrome 의 내부 이름)이다.
- **`select` 안의 `hr` 을 `separator` 로 둔 것은 불일치가 아니다** — HTML-AAM 의 `hr` 줄이 「`select` 의 자손이면 `none` 으로 노출**해도 된다**(MAY)」다. 해도 되는 것을 안 한 것이다.
- **DOM 에 남는 것** — 파싱 절 「in body」의 **`hr` 시작 태그 줄**(「`select` 가 범위 안에 있으면 암묵 끝 태그를 만들고 `hr` 을 넣는다」)과 `select` 의 **콘텐츠 모델**(「`option`·`optgroup`·`hr`·…」). 현재 파싱 절에는 **「in select」 삽입 모드 자체가 없다.**

### 8. 둘 다 못 쓴다

- **못 쓴다.** 보조 기술이 없다. 캡션은 트리에 **자식 글자**로 있다 — 언제 읽히는지는 그 뒤의 일이다.
- **못 봤다.** 엔진이 하나다. Baseline 은 「Customizable `<select>`」 전체가 **limited** 라는 것까지만 말한다.

### 9. 정본 경계

- **「파서가 안 고치는 것」·`figure` 밖 `figcaption`** — [05번 주제](../05-content-categories-and-models/2-summary.md)의 (4)·(6).
- **`details`/`summary`** — 목록의 **48번 주제**.
- **`alt` 판단** — 목록의 **44번 주제** · **이름 계산 전체** — 목록의 **43번 주제**.

## 실행 검증

**환경** — Google Chrome 151.0.7922.173 · Linux · headless · `--window-size=1000,800`. **엔진은 이것 하나다.**\
★★ **보조 기술 없음.** NVDA·VoiceOver·Orca 가 설치돼 있지 않다.

**하네스** — [17번 주제](../17-table-structure/3-answer.md)의 `html17b-cdp.py` 를 그대로 쓴다. 이 주제는 **`page` 모드 + `window.__내부`** 로 CDP 역할·이름과 내부 덤프의 `nameFrom` 을 한 실행에 받고, **`ax`·`int` 모드**로 트리 원본을 찍는다. ★ 탐침 요소에는 전부 `id` 를 달았다 — 이 판은 `id` 없는 `generic` 을 트리에서 빼기 때문이다([13번 주제](../13-phrasing-semantics/2-summary.md) (2)).

| 무엇을 | 몇 번 | 결과가 쓰인 곳 |
|---|---|---|
| **`figure` 열 개**(이름·설명·`nameFrom`·자식 순서) | 3 | 동작 방식 (1) · A1·A4 |
| **트리·내부 덤프·`--dump-dom`**(`figure`) | 3 | 동작 방식 (1)·(2) · A2 |
| **`address`·`hr`**(역할·`font-style`·`select`) | 3 | 동작 방식 (3)·(4) · A3 |

**구현에 달린 항목**

| 항목 | 이 판의 값 | 왜 다시 찍나 |
|---|---|---|
| `figcaption` 의 역할 이름 | **`Figcaption`** | HTML-AAM 은 `caption` — 구현 이름이다 |
| `figure` 의 이름 | `figcaption` 에서 **안 온다** | 편집본과 같다 — 명세가 다시 바뀌면 따라 바뀔 수 있다 |
| `select` 안 `hr` 의 역할 | **`separator`** | 명세가 `none` 도 허용한다 |
| 내부 덤프의 `hr` 역할 이름 | **`splitter`** | 내부 이름이다 |

**안 돌려 본 것** — ① **Firefox·Safari**(엔진이 없다). ② **`aria-describedby` 로 캡션을 설명에 잇기** — 목록의 **43번 주제**의 몫. ③ **`details`/`summary`** — 목록의 **48번 주제**.

**못 잰 것**(「안 돌려 본 것」과 다르다) — ① **스크린리더의 캡션·연락처 읽기**(A8). ② **플랫폼 API 층의 캡션 관계**(IA2 의 `LABEL_FOR` 류) — CDP·내부 덤프는 그 위 층이다.

**부적용인 창** — **창 ③·④·⑤·⑥.** 이 요소들은 글자·문서 모드·요청·렌더 차단 어느 것도 바꾸지 않는다 — **잴 것이 없다.**

## 용어 풀이

- **접근 가능한 이름** — 보조 기술이 부르는 이름. `figure` 는 `aria-*`·`title` 에서만 받는다.
- **`relatedElement`** — 다른 요소를 가리켜 받은 이름이라는 `nameFrom` 값.
- **`group`** — 뜻 없는 묶음 역할. `address` 가 받는다.
- **`separator`** — 구분선 역할. `hr` 이 받는다.
- **제5의 상태** — 같은 질문을 다른 창으로 물은 것. 이 주제에서는 「연락처인가」를 역할로 물었다.
