# css/syntax/09 — 구조적 의사 클래스: `:nth-child()`·`:nth-of-type()` 과 `of S` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — [Selectors Level 4 §Child-indexed pseudo-classes](https://drafts.csswg.org/selectors-4/#child-index) 와 그 안의 [`:nth-child()`](https://drafts.csswg.org/selectors-4/#the-nth-child-pseudo) · [`:nth-of-type()`](https://drafts.csswg.org/selectors-4/#the-nth-of-type-pseudo) · [`An+B` 표기](https://drafts.csswg.org/css-syntax-3/#anb-microsyntax). 열어서 확인한 것만 적었다.
> **실행 검증** — 이 문서의 모든 매치 수는 **Google Chrome 151.0.7922.173** headless 에서 `document.querySelectorAll(...).length` 로 실제로 센 값이다. 규칙이 스타일시트에 담겼는지는 `cssRules` 로, 화면에 무엇이 보이는지는 `getComputedStyle` + 스크린샷으로 확인했다. `demo` 블록 **2개 전부**와 그 「바꿔 볼 것」도 돌려 확인했다.\
> **WebKit(Safari)은 이 머신에 없다** — Safari 관련 서술은 하지 않았다. **엔진은 Chrome 하나**다.
> **버전** — CSS 에 언어 버전은 없다. Baseline(2026-09-23 에 `api.webstatus.dev` 조회): `:nth-child()` **widely**(2015-07-29 → 2018-01-29) · **`:nth-child(… of S)` widely**(newly 2023-05-09 → widely 2025-11-09, Chrome 111 · Firefox 113 · Safari 9).
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 숫자는 실행으로 접지했다.

## 한눈에 — 쉽게 말하면

**세 가지 다른 줄서기다. 줄이 다르면 번호도 다르다.**

08번의 비유(그물 모양 / 그물의 힘)를 그대로 이어받고, 여기서는 **모양** 안에서 한 겹 더 쪼갠다.

| 비유 | 실체 | 세는 줄 |
|---|---|---|
| **반 전체 번호** | `:nth-child(n)` | 형제 **요소 전부**를 한 줄로 세운 번호 |
| **남학생 번호** | `:nth-of-type(n)` | **같은 태그끼리만** 다시 세운 번호 |
| **동아리 번호** | `:nth-child(n of S)` | **S 에 맞는 형제끼리만** 다시 세운 번호 |

- 셋 다 "몇 번째냐"를 묻지만 **줄이 다르다.** 같은 노드가 반 번호 3번, 남학생 번호 2번일 수 있다.
- ★ 그리고 **`.item:nth-of-type(2)` 는 「.item 중 둘째」가 아니다.**\
  "남학생 번호 2번인데 동아리원이기도 한 사람"이라는 뜻이다 — **줄서기와 거르기는 순서가 반대다.**
- 세는 대상을 내가 정하는 유일한 형태가 `of S` 다.

```text
   .box 의 자식들            반번호  p끼리번호  .item끼리번호
   ┌───────────────┐
   │ h2   "제목"   │          1        -          -
   │ p    p1       │          2        1          -
   │ p.item p2     │          3        2          1
   │ p    p3       │          4        3          -
   │ p.item p4     │          5        4          2
   │ p    p5       │          6        5          -
   │ p.item p6     │          7        6          3
   └───────────────┘

   p:nth-child(2n)     ->  반번호가 짝수인 p       ->  p1 p3 p5
   p:nth-of-type(2n)   ->  p끼리 번호가 짝수인 p   ->  p2 p4 p6
   :nth-child(2n of .item) -> .item끼리 짝수       ->  p4
```

**같은 트리에서 세 그물이 서로 다른 노드를 잡는다.** 이 표가 이 주제 전부다.

실무에서 이게 터지는 자리는 **줄무늬(zebra) 테이블**과 **카드 그리드**다.\
`:nth-child(odd)` 로 줄무늬를 넣어 놓고 행 하나를 `hidden` 으로 감추면, 감춰진 행도 번호를 그대로 차지해 **줄무늬가 두 줄 연달아 붙는다.** `of S` 가 그것을 고친다((4) 절).

> **의사 클래스(pseudo-class)** — 요소의 상태나 위치를 가리키는 `:` 로 시작하는 선택자.\
> 예: `:nth-child(2)` 는 "형제 중 둘째"라는 **위치**를 가리킨다.

> **구조적 의사 클래스(structural pseudo-class)** — 문서 트리의 **모양**만 보고 판정하는 의사 클래스.\
> 예: `:first-child`·`:nth-of-type(2)`·`:empty`. 사용자 입력과 무관하다([10번](../10-state-and-form-pseudo-classes/2-summary.md)의 상태 의사 클래스와 대비).

## 이 주제가 답하려는 질문

1. **`An+B` 를 어떻게 읽나** — `2n`·`2n+1`·`-n+3`·`n+3` 이 각각 무엇을 잡는지 손으로 펼칠 수 있는가.
2. `:nth-child` 와 `:nth-of-type` 이 **같은 트리에서 다른 노드를 잡는 자리**를 만들 수 있는가.
3. `of S` 가 `:nth-of-type` 과 **어떻게 다른가** — 그리고 `:nth-of-type` 에 클래스를 붙이면 왜 안 되는가.

## 예시 데이터 — 이 편이 쓰는 두 트리

**트리 T1 — 섞인 자식 7개** (`09-tree.html`). 08 의 판 A 와 달리 **첫 자식이 `h2`** 인 것이 핵심이다.

```text
div.box
 ├─ (1) h2#H        "제목"
 ├─ (2) p#p1
 ├─ (3) p#p2 .item
 ├─ (4) p#p3
 ├─ (5) p#p4 .item
 ├─ (6) p#p5
 └─ (7) p#p6 .item
```

**트리 T2 — 태그가 섞인 자식 5개** (`09-mix.html`). `of S` 와 `:nth-of-type` 을 가르려면 이게 필요하다.

```text
div.mix
 ├─ (1) p#A    .i
 ├─ (2) span#B .i
 ├─ (3) p#C    .i
 ├─ (4) span#D
 └─ (5) p#E    .i
```

## 동작 방식

### (1) `An+B` 를 펼치는 법 — n 에 0, 1, 2, … 를 넣는다

**언제 쓰나** — `:nth-child(...)` 괄호 안을 읽을 때마다.

```text
   An + B          n 에 0,1,2,3,... 을 차례로 넣어 나온 수가 "번호"다
   ^    ^          1 보다 작은 번호는 버린다
   |    +--- 시작 오프셋
   +-------- 걸음 폭

   2n    -> n=0:0(버림) 1:2  2:4  3:6  ...   ->  2,4,6,...      짝수
   2n+1  -> n=0:1  1:3  2:5  ...             ->  1,3,5,...      홀수
   3n+1  -> n=0:1  1:4  2:7  ...             ->  1,4,7,...
   -n+3  -> n=0:3  1:2  2:1  3:0(버림) ...   ->  3,2,1          "처음 셋"
   n+3   -> n=0:3  1:4  2:5  ...             ->  3,4,5,...      "셋째부터 끝까지"
   0n+2  -> 언제나 2                          ->  2             :nth-child(2) 와 같다
```

- **`odd` 는 `2n+1` 의 별칭, `even` 은 `2n` 의 별칭**이다.
- **`-n+B` 가 「처음 B 개」**, **`n+B` 가 「B 번째부터 끝까지」** — 이 두 관용구를 외우면 대부분 해결된다.
- **`A` 가 음수면 번호가 줄어들다 0 이하에서 멈춘다.** 그래서 유한 개다.

T1 에 던져 센 결과다(전부 `p` 로 한정해 h2 를 뺐다).

| 그물 | 잡힌 노드 | 개수 |
|---|---|---|
| `p:nth-child(2n)` | p1 p3 p5 | 3 |
| `p:nth-child(2n+1)` | p2 p4 p6 | 3 |
| `p:nth-child(odd)` | p2 p4 p6 | 3 |
| `p:nth-child(even)` | p1 p3 p5 | 3 |
| `p:nth-child(-n+3)` | p1 p2 | 2 |
| `p:nth-child(n+3)` | p2 p3 p4 p5 p6 | 5 |
| `p:nth-child(3n+1)` | p3 p6 | 2 |
| `p:nth-child(0n+2)` | p1 | 1 |
| `p:nth-child(n)` | p1 … p6 | 6 |
| `p:nth-child(0)` | — | 0 |
| `p:nth-child(-n+0)` | — | 0 |

★ **`odd` 인데 p1·p3·p5 가 아니다.** `h2` 가 1번을 차지했기 때문에 홀수 번호는 3·5·7 이고 그게 p2·p4·p6 이다.\
**「홀수 번째 문단」을 원했으면 `odd` 가 아니라 `:nth-of-type(odd)` 였다.**

비용 — 없다. 다만 `An+B` 는 **형제 목록이 바뀌면 결과가 통째로 바뀐다** — 마크업에 스타일을 못박는 형태다.

### (2) `:nth-child` 와 `:nth-of-type` — 같은 트리, 다른 노드

**언제 쓰나** — "둘째 문단"을 고르고 싶을 때. 여기서 거의 항상 첫 번째로 틀린다.

```text
   p:nth-child(2)                      p:nth-of-type(2)
   "형제 전체 줄에서 2번인데 p 인 것"    "p 끼리 줄에서 2번인 것"

   div.box                             div.box
    ├─ 1 h2                             ├─   h2
    ├─ 2 p1   <=  p 이고 2번            ├─ 1 p1
    ├─ 3 p2                             ├─ 2 p2   <=
    ├─ 4 p3                             ├─ 3 p3
    ...                                 ...
      잡힌 것: p1                          잡힌 것: p2
```

```text
   실측 (Chrome 151 headless, T1)
   p:nth-child(1)    -> 0개      h2 가 1번이라 "1번이면서 p" 인 노드가 없다
   p:nth-child(2)    -> p1
   p:nth-child(3)    -> p2
   p:nth-of-type(1)  -> p1
   p:nth-of-type(2)  -> p2
   p:nth-of-type(3)  -> p3
   p:first-child     -> 0개      같은 이유
   p:first-of-type   -> p1
```

그림 해설 (한 단계씩):

- **`:nth-child` 는 태그를 안 본다.** 번호를 먼저 매기고, 그다음에 `p` 인지 거른다.
- **`:nth-of-type` 은 태그별로 줄을 새로 세운다.** `h2` 는 `h2` 줄, `p` 는 `p` 줄이다.
- 그래서 **`p:nth-child(1)` 은 0개**다 — "1번이 p 였으면"이라는 조건이지 "첫 p"가 아니다.
- 뒤에서 세는 짝도 똑같다 — `p:nth-last-child(1)` 은 p6, `p:nth-last-of-type(2)` 는 p5(실측).

```html demo
<div class="box">
  <h2>제목</h2><p>p1</p><p>p2</p><p>p3</p>
</div>
<style>
  .box p { padding: 4px 8px; margin: 3px; font: 16px system-ui; }
  .box p:nth-child(2)   { background: #fde68a; }
  .box p:nth-of-type(2) { outline: 2px solid #b91c1c; }
</style>
```

> **보이는 것** — **노란 배경은 p1 에, 빨간 2px 테두리는 p2 에** 걸린다. 서로 다른 줄이다. 조작은 없고 뜨자마자 그 상태다. `h2` 가 첫째 자식을 차지해 「자식 번호」가 한 칸 밀린 것이 원인 전부다.\
> **바꿔 볼 것** — `<h2>제목</h2>` 를 지우면 **노란 배경과 빨간 테두리가 둘 다 p2 한 줄에** 겹친다(밀림이 사라져 두 줄서기가 같아진다)

*(Chrome 151 headless 실측: 원본 p1 `background-color: rgb(253, 230, 138)` / `outline-style: none`, p2 `rgba(0, 0, 0, 0)` / `solid`. h2 를 지운 판은 p1 이 `rgba(0, 0, 0, 0)` / `none`, p2 가 `rgb(253, 230, 138)` / `solid`.)*

비용 — 없다. **`:nth-of-type` 쪽이 마크업 변화에 덜 취약하다** — 다른 태그가 끼어들어도 번호가 안 밀린다.

### (3) `of S` — 세는 대상을 내가 정한다

**언제 쓰나** — "이 클래스인 것들 중 n번째"가 필요할 때. 이것만이 그 뜻이다.

```text
   :nth-child(An+B of S)

   순서가 이렇다
     1) 형제 중 S 에 맞는 것만 골라   <- 여기서 줄이 새로 만들어진다
     2) 그 줄에 1,2,3,... 번호를 매기고
     3) An+B 에 맞는 번호를 고른다

   T1 에서 S = .item  이면 줄은  [p2, p4, p6]
     :nth-child(1 of .item)     -> p2
     :nth-child(2 of .item)     -> p4
     :nth-child(2n of .item)    -> p4
     :nth-child(2n+1 of .item)  -> p2, p6
     :nth-last-child(1 of .item)-> p6
```

★ **`of S` 와 `:nth-of-type` 이 갈리는 자리는 태그가 섞인 트리다.** T2 로 확인했다.

```text
   div.mix       .i 줄      p 줄      span 줄
    ├─ p#A  .i      1         1         -
    ├─ span#B .i    2         -         1
    ├─ p#C  .i      3         2         -
    ├─ span#D       -         -         2
    └─ p#E  .i      4         3         -

   :nth-child(2 of .i)   ->  span#B      (.i 줄의 2번)
   .i:nth-of-type(2)     ->  p#C         (p 줄의 2번이면서 .i)
                             ^^^^ 같은 "2번째"인데 다른 노드다
```

```text
   실측 (Chrome 151 headless, T2)
   :nth-child(1 of .i)  -> A        :nth-of-type(2)   -> C, D   (p 줄 2번 + span 줄 2번)
   :nth-child(2 of .i)  -> B        .i:nth-of-type(2) -> C
   :nth-child(3 of .i)  -> C        p:nth-of-type(2)  -> C
                                    span:nth-of-type(2) -> D
   p:nth-child(2 of .i) -> 0개      ".i 줄 2번이면서 p" — 2번은 span 이다
```

그림 해설 (한 단계씩):

- `of S` 는 「**거르고 나서 센다**」, `:nth-of-type` 은 「**태그로 나누고 나서 센다**」다.
- 그래서 `of .i` 의 2번은 `span#B` 이고, `.i:nth-of-type(2)` 는 `p#C` 다. **같은 트리에서 다른 답이다.**
- `p:nth-child(2 of .i)` 가 **0개**인 것이 순서를 증명한다 — 먼저 `.i` 줄에서 2번을 뽑고(`span#B`), **그다음** `p` 인지 보니 아니라서 탈락이다.
- `of` 는 **선택자 목록**을 받는다 — `:nth-child(1 of p, span)` 은 A, `:nth-child(2 of p, span)` 은 B 를 잡았다(실측).

비용 — 없다. 단 **`:nth-of-type` 에는 `of S` 가 없다.** 던져 보면 문법 오류다.

```text
  document.querySelectorAll('p:nth-of-type(2n of .item)')
    -> SyntaxError: 'p:nth-of-type(2n of .item)' is not a valid selector.

  스타일시트에 넣으면 조용히 사라진다 — cssRules 로 확인했다
    p:nth-of-type(2n of .item) { color: red }    <- 담기지 않았다
    p:nth-child(2n of .item)   { color: blue }   <- 담겼다
```

- `of S` 를 받는 것은 **`:nth-child()` 와 `:nth-last-child()` 둘뿐**이다.
- ★ **`of` 안의 목록은 관대하지 않다**(non-forgiving). `p:nth-child(2n of :unknownzz)` 를 넣었더니 **규칙이 통째로 사라졌다**(같은 `cssRules` 출력). `:is()` 와 다른 점이고, [11번 주제](../11-is-where-not/2-summary.md)가 그 대비를 정본으로 다룬다.

### (4) 그래서 무엇이 달라지나 — 줄무늬가 깨지는 자리

**언제 쓰나** — 목록·표에 줄무늬를 넣는데 **행이 숨겨지거나 필터링될 때.**

```text
   행 6개 중 2행·5행이 hidden 이다

   li:nth-child(2n+1)                  li:nth-child(2n+1 of :not([hidden]))
   +---------------------+             +---------------------+
   | 1행   ■ 색칠        |             | 1행   ■ 색칠        |
   | 2행   (숨김)  ■     |             | 2행   (숨김)        |
   | 3행   ■ 색칠        |  <- 연달아! | 3행                 |
   | 4행                 |             | 4행   ■ 색칠        |
   | 5행   (숨김)  ■     |             | 5행   (숨김)        |
   | 6행                 |             | 6행                 |
   +---------------------+             +---------------------+
   보이는 줄: 색 색 무 무  (깨졌다)      보이는 줄: 색 무 색 무  (맞다)
```

```html demo
<ul class="rows">
  <li>1행</li><li hidden>2행</li><li>3행</li><li>4행</li><li hidden>5행</li><li>6행</li>
</ul>
<style>
  .rows { list-style: none; padding: 0; margin: 0; font: 16px system-ui; }
  .rows li { padding: 5px 10px; }
  .rows li:nth-child(2n+1 of :not([hidden])) { background: #dbeafe; }
</style>
```

> **보이는 것** — 화면에 보이는 줄은 1행·3행·4행·6행 넷이고, 그중 **1행과 4행에만 연한 파란 배경**이 깔린다. 곧 보이는 순서로 「색·무·색·무」가 되어 줄무늬가 맞는다. 조작은 없고 뜨자마자 그 상태다.\
> **바꿔 볼 것** — `of :not([hidden])` 을 떼어 `:nth-child(2n+1)` 로 만들면 **1행과 3행이 연달아 색칠되고 4행·6행은 둘 다 무색**이 된다(색칠이 가야 할 5행이 숨겨져 있어서 화면에서 사라진다)

*(Chrome 151 headless 실측 — 여섯 `li` 의 `background-color` 를 순서대로 읽었다. 원본: 1행 `rgb(219, 234, 254)` · 2행(숨김) 투명 · 3행 투명 · 4행 `rgb(219, 234, 254)` · 5행(숨김) 투명 · 6행 투명. `of` 를 뗀 판: 1행 `rgb(219, 234, 254)` · 2행(숨김) 투명 · 3행 `rgb(219, 234, 254)` · 4행 투명 · 5행(숨김) `rgb(219, 234, 254)` · 6행 투명.)*

★ **`of` 를 뗀 판에서 5행이 색칠돼 있다는 것이 사고의 정체다.** 화면에는 안 보이니 **눈으로는 「두 줄이 연달아 색칠됐네」까지만 보이고 왜 그런지는 안 보인다.** `getComputedStyle` 로 숨은 행까지 읽어야 원인이 드러난다.

비용 — `of S` 는 명시도에 **S 의 명시도를 통째로 더한다**(`:nth-child(1 of .c1)` 은 `(0,2,1)`). 정본은 [02번](../02-specificity/2-summary.md) 「손으로 세어 보기」 표다.

### (5) 나머지 구조 선택자 — 셋씩 짝지어 외운다

**언제 쓰나** — 첫·끝·유일을 고를 때.

```text
   자식 줄 기준            같은 태그 줄 기준
   :first-child            :first-of-type
   :last-child             :last-of-type
   :only-child             :only-of-type
   :nth-child(An+B)        :nth-of-type(An+B)
   :nth-last-child(An+B)   :nth-last-of-type(An+B)
      + of S 가능                of S 불가
```

- `:only-child` 는 **형제가 아무도 없는 것**, `:only-of-type` 은 **같은 태그 형제가 없는 것**이다.\
  실측에서 `<ul><li>a</li></ul>` 의 `li` 는 둘 다 맞았다.
- **`:empty` 는 자식이 하나도 없는 요소**다. 실측: `<p></p>` 와 `<p><!--c--></p>` 는 맞고, **`<p> </p>`(공백 하나)는 안 맞는다** — 공백도 텍스트 노드다. 주석은 안 센다.
- **`:root`** 는 문서의 뿌리다. HTML 에서는 언제나 `html` 하나(실측 1개). `html` 과 같은 요소를 고르지만 **의사 클래스라 B 자리**라서 더 세다([02번](../02-specificity/2-summary.md) 이 정본).\
  *(Chrome 151 headless 실측: `:root { color: rgb(1,1,1) }` 뒤에 `html { color: rgb(2,2,2) }` 를 써도 `html` 의 계산색은 `rgb(1, 1, 1)` 이었다 — 나중에 쓴 쪽이 졌다.)*

★ **`:nth-child` 는 요소만 센다.** 텍스트·주석 노드는 번호를 안 받는다.

```text
   <div class="b1">텍스트만 있는 형제<p id="q1">q1</p><!--주석--><p id="q2">q2</p></div>
   childNodes: [텍스트, P, 주석, P]

   .b1 :nth-child(1)  ->  q1      텍스트가 앞에 있는데도 q1 이 1번
   .b1 :nth-child(2)  ->  q2      주석이 끼어 있는데도 q2 가 2번
   #q1:first-child    ->  q1      맞는다
```

비용 — 없다.

## 문법 — 어디서 헷갈리나

### 형태

```css
li:nth-child(3)            /* 자식 줄 3번 */
li:nth-child(2n+1)         /* 자식 줄 홀수 */
li:nth-child(odd)          /* 위와 같은 뜻 */
li:nth-child(2n of .on)    /* .on 줄 짝수 */
li:nth-last-child(1 of .on)/* .on 줄의 마지막 */
li:nth-of-type(2n)         /* li 줄 짝수 — of 는 못 붙인다 */
```

### 헷갈리는 자리

- **`An+B` 안에는 공백을 마음대로 못 넣는다.** 부호 둘레에는 넣어도 되지만 **수와 `n` 사이에는 못 넣는다**(`2n` 이 한 토큰이다).\
  *(Chrome 151 headless 실측: `:nth-child( 2n + 1 )`·`(+2n+1)`·`(2n+ 1)` 은 정상 매치, `(2 n+1)`·`(- n+3)` 은 `SyntaxError`.)*
- **`of` 앞뒤에는 공백이 필요하다** — `2n of .item`.
- **`:nth-child(0)` 은 유효하지만 아무것도 안 잡는다**(번호는 1부터다). 문법 오류가 아니라 0개다.
- **`:nth-of-type` 에 클래스를 붙여도 세는 줄은 안 바뀐다** — `p.item:nth-of-type(2)` 는 여전히 `p` 줄의 2번이다.
- **뿌리 요소도 번호를 받는다.** `html:nth-child(1)` 은 실측에서 1개였다 — 형제가 없으면 자기가 1번이다.

## 어디서 틀리나

### 1. `.item:nth-of-type(n)` 을 "n 번째 .item" 으로 읽는다 ★ 가장 흔하다

```text
   T1 에서 .item 은 p2, p4, p6 셋이다. "첫 .item" 을 고르고 싶다.

   .item:nth-of-type(1)   ->  0개   <-- 하나도 안 잡힌다
   .item:nth-of-type(2)   ->  p2    <-- 우연히 맞는 것처럼 보인다
   .item:nth-child(3)     ->  p2    <-- 이것도 우연이다
   :nth-child(1 of .item) ->  p2    <-- 이것만 "첫 .item" 이라는 뜻이다
```

**`.item:nth-of-type(1)` 이 0개인 이유**: `p` 줄의 1번은 `p1` 이고 `p1` 에는 `.item` 이 없다.\
★ **`:nth-of-type(2)` 가 `p2` 를 맞히는 바람에 「되는 줄 알고」 넘어가는 것**이 이 함정의 본체다.\
트리가 조금만 바뀌면 조용히 다른 것을 고르게 된다.

### 2. `odd`/`even` 이 화면의 홀·짝수 줄이라고 생각한다

`odd` 는 **자식 줄의 홀수 번호**다. 앞에 제목 태그가 하나 있으면 실제로 색칠되는 것은 짝수 번째 문단이다(위 (1) 실측).\
**「보이는 줄의 홀수」를 원했다면 `of :not([hidden])` 이 필요하다**((4) 절).

### 3. 숨긴 행이 번호를 안 차지한다고 생각한다

```text
   hidden / display:none 인 형제도 :nth-child 번호를 그대로 차지한다.
   (4) 실측에서 숨긴 5행이 색칠을 "가져가 버렸고", 화면에는 그 색이 안 보인다.
```

★ **화면으로는 절대 안 잡히는 사고다.** 줄무늬가 두 줄 붙은 것만 보이고 원인은 숨은 행에 있다.

### 4. `of S` 를 `:nth-of-type` 의 확장으로 본다

```text
   p:nth-of-type(2n of .item)   ->  SyntaxError, 규칙이 cssRules 에서 사라진다
```

`of S` 는 **`:nth-child()`·`:nth-last-child()` 전용**이다. 둘은 애초에 다른 줄을 센다.

### 5. `of` 안에 아무 선택자나 넣어도 된다고 생각한다

```text
   p:nth-child(2n of :unknownzz) { }   ->  규칙이 통째로 사라진다 (cssRules 로 확인)
```

`of` 목록은 **관대하지 않다**(non-forgiving). `:is()` 처럼 "모르는 것 하나만 버리기"가 안 된다([11번](../11-is-where-not/2-summary.md)).

### 6. `:empty` 가 "내용이 없어 보이는 것"이라고 생각한다

```text
   <p></p>            :empty  O
   <p><!--c--></p>    :empty  O     주석은 안 센다
   <p> </p>           :empty  X     공백 하나도 텍스트 노드다
```

**소스에 줄바꿈과 들여쓰기를 넣으면 대부분의 「빈」 요소가 `:empty` 가 아니게 된다.**

## 구현 세부사항 대 언어 보장

| 것 | 성격 | 근거 |
|---|---|---|
| `An+B` 를 펼치는 규칙 | **명세 보장** | css-syntax-3 §anb-microsyntax |
| `:nth-child` 가 요소만 센다 | **명세 보장** | Selectors 4 §child-index — "element siblings" |
| 숨긴 요소도 번호를 차지한다 | **명세 보장** | 선택자 매칭은 **박스 생성 이전**이다. `display` 를 보지 않는다 |
| `of S` 가 `:nth-child` 계열 전용 | **명세 보장** | `:nth-of-type` 문법에 `of` 가 없다 |
| `of` 목록이 non-forgiving | **명세 보장** | `<complex-selector-list>` 이지 forgiving 이 아니다 |
| `of S` 가 Chrome 111 부터인 것 | **구현 현황** | Baseline widely(2023-05-09 → 2025-11-09) |
| `:has()` 안에서의 동작 | **여기서 미실행** | [목록의 **12번 주제**](../12-has-relational-selector/) |

★ **「숨겨도 번호를 차지한다」가 구현 사정이 아니라 명세 보장**이라는 점이 중요하다. 브라우저를 바꿔도 안 달라진다.

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 줄무늬 테이블(행이 고정) | `:nth-child(odd)` | — |
| 줄무늬 테이블(행이 숨겨진다) | `:nth-child(2n+1 of :not([hidden]))` | `:nth-child(odd)` |
| "n 번째 카드" | `:nth-child(n of .card)` | `.card:nth-of-type(n)` |
| 제목 뒤 첫 문단 | `h2 + p` (08번의 조합자) | `p:nth-child(2)` |
| 목록의 처음 셋 | `:nth-child(-n+3)` | `:nth-child(1), :nth-child(2), :nth-child(3)` |
| 넷째부터 접기 | `:nth-child(n+4)` | JS 로 클래스 붙이기 |
| 마지막 항목 구분선 제거 | `:last-child` | `:nth-child(N)` 하드코딩 |
| "자식을 가진 부모" | `:has()` ([목록의 **12번 주제**](../12-has-relational-selector/)) | 구조 선택자로 시도 |

판단 규칙 두 줄.

- **「몇 번째」를 쓰기 전에 「어느 줄에서 몇 번째」를 먼저 말해 보라.** 말이 안 나오면 아직 선택자를 못 고른 것이다.
- **번호로 거는 스타일은 마크업 변경에 가장 약하다.** 태그 하나가 끼어드는 것만으로 조용히 어긋난다.

## 핵심 문장

- `:nth-child`·`:nth-of-type`·`of S` 는 **세는 줄이 다르다** — 형제 전체 / 같은 태그끼리 / S 에 맞는 것끼리.
- `An+B` 는 **n 에 0, 1, 2, … 를 넣어 나온 수 중 1 이상**이다. `-n+3` 은 처음 셋, `n+3` 은 셋째부터 끝까지.
- **`p:nth-child(1)` 은 「첫 p」가 아니다.** 앞에 다른 태그가 하나 있으면 0개가 된다.
- **`.item:nth-of-type(1)` 은 「첫 .item」이 아니다.** 실측에서 0개였다. 그 뜻을 가진 것은 `:nth-child(1 of .item)` 뿐이다.
- `of S` 와 `:nth-of-type` 은 **태그가 섞인 트리에서 다른 노드를 잡는다** — `of .i` 의 2번은 `span`, `.i:nth-of-type(2)` 는 `p` 였다.
- **`of S` 는 `:nth-child()`·`:nth-last-child()` 에만 붙는다.** `:nth-of-type` 에 붙이면 `SyntaxError` 이고 규칙이 `cssRules` 에서 사라진다.
- **숨긴 형제도 번호를 차지한다** — 그래서 필터링되는 목록의 줄무늬는 `of :not([hidden])` 이 필요하다. 화면으로는 원인이 안 보인다.

## 관련 자료

- [`../README.md`](../README.md) — CSS 문법·API 주제 목록(이 주제는 09번) · Baseline 표
- [`../08-basic-selectors-and-combinators/2-summary.md`](../08-basic-selectors-and-combinators/2-summary.md) — **선행.** 타입·클래스·조합자·속성 선택자. **거기는 「이름·관계로 고르기」까지, 여기는 「위치로 고르기」부터**
- [`../02-specificity/2-summary.md`](../02-specificity/2-summary.md) — **명시도의 정본.** `:nth-child(1 of .c1)` 이 `(0,2,1)` 인 계산은 거기 「손으로 세어 보기」 표에 있다. 여기서는 매칭만 다룬다
- [`../11-is-where-not/2-summary.md`](../11-is-where-not/2-summary.md) — `of` 목록이 관대하지 않은 것과 `:is()` 가 관대한 것의 대비
- [`../10-state-and-form-pseudo-classes/2-summary.md`](../10-state-and-form-pseudo-classes/2-summary.md) — 트리 모양이 아니라 **사용자 입력**으로 켜지는 의사 클래스
- [목록의 **12번 주제**](../12-has-relational-selector/)(`:has()`) — "n 번째 자식을 가진 부모"처럼 방향을 뒤집는 것
- [목록의 **13번 주제**](../13-pseudo-elements-and-generated-content/)(의사 요소·생성 콘텐츠) — `::marker`·`counter()` 로 **번호를 찍는** 쪽. 여기는 번호로 **고르는** 쪽
- [`reference/render-rules.md`](../../../../../../reference/render-rules.md) — 이 문서의 `demo` 블록 규칙

## 용어 풀이

- **구조적 의사 클래스** — 문서 트리의 모양만 보고 판정하는 `:` 선택자. 사용자 입력과 무관하다.
- **`An+B`** — `:nth-*()` 괄호 안의 표기. `A` 는 걸음 폭, `B` 는 시작 오프셋. n 에 0,1,2,… 를 넣는다.
- **`odd` / `even`** — 각각 `2n+1` · `2n` 의 별칭.
- **자식 줄(child index)** — 형제 **요소** 전체를 한 줄로 세운 번호. 텍스트·주석은 안 센다.
- **타입 줄(type index)** — 같은 태그 형제끼리만 다시 센 번호. `:nth-of-type` 이 쓴다.
- **`of S`** — `:nth-child(An+B of S)` 의 필터. **S 에 맞는 형제만 골라 새 줄을 만든다.** `:nth-child()`·`:nth-last-child()` 전용.
- **관대하지 않다(non-forgiving)** — 목록에 모르는 선택자가 하나라도 있으면 **전체가 무효**가 되는 성질. `of S` 가 그렇다.
- **`:empty`** — 자식 노드가 **하나도** 없는 요소. 공백 텍스트가 있으면 아니고, 주석만 있으면 맞다.
- **`:root`** — 문서의 뿌리 요소. HTML 에서는 `html`. 명시도는 `(0,1,0)`.
- **`:only-child` / `:only-of-type`** — 각각 형제가 아예 없는 것 / 같은 태그 형제가 없는 것.

## 더 들어가면

- **`of S` 가 없던 시절의 우회**는 "숨길 때 DOM 에서 아예 빼기"였다. 그래서 가상 스크롤·필터 UI 가 요소를 지웠다 넣었다 했다. `of S` 는 그 비용을 CSS 쪽으로 옮긴 것이다.
- **`of S` 의 `S` 는 조상 조건도 받는다** — 다만 판정 대상은 언제나 **그 형제 자신**이다.\
  *(Chrome 151 headless 실측: `.box` 안의 `.i` 셋에서 `:nth-child(2 of .box .i)` 와 `:nth-child(2 of .i)` 가 **같은 둘째 노드**를 잡았고, 없는 조상을 쓴 `:nth-child(2 of .nope .i)` 는 0개였다.)*
- **`:nth-of-type` 은 네임스페이스까지 본다**(같은 로컬 이름이어도 네임스페이스가 다르면 다른 타입). HTML 문서만 다루면 만날 일이 없다. *(이 머신에서 미실행.)*
- 트리 순서가 아니라 **화면에 그려진 순서**로 세고 싶다면 CSS 에는 방법이 없다. `order`(flex)는 **그림 순서만 바꾸고 선택자 번호는 안 바꾼다.**\
  *(Chrome 151 headless 실측: `display: flex` 안의 셋째 아이템에 `order: -1` 을 줘 **화면에서 맨 왼쪽**으로 보냈는데(x 좌표 8 로 가장 작다), `:nth-child(1)`·`:first-child` 는 여전히 **첫째 아이템**을 잡았다.)* grid 쪽(`grid-auto-flow`)은 미실행이다(목록의 **26번 주제**·**28번 주제**).
