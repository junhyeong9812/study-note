# css/syntax/09 — 구조적 의사 클래스: `:nth-child()`·`:nth-of-type()` 과 `of S` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 **모든 개수와 노드 이름은 Google Chrome 151.0.7922.173 headless 에서 실제로 돌려 받은 것**이다.\
> 매치는 `document.querySelectorAll(sel).length` 와 잡힌 노드 `id`, 규칙 생존은 `document.styleSheets[*].cssRules`, 화면 결과는 `getComputedStyle` + 스크린샷으로 읽었다.\
> 규칙은 [Selectors Level 4 §Child-indexed pseudo-classes](https://drafts.csswg.org/selectors-4/#child-index) 로, 지원 상태는 `api.webstatus.dev` 조회(2026-09-23)로 접지했다. **엔진은 Chrome 하나다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

두 트리의 번호를 먼저 붙여 둔다. **이 표를 손에 들고 답하면 전부 풀린다.**

```text
   T1                    반번호   p끼리   .item끼리
   h2#H                    1        -        -
   p#p1                    2        1        -
   p#p2 .item              3        2        1
   p#p3                    4        3        -
   p#p4 .item              5        4        2
   p#p5                    6        5        -
   p#p6 .item              7        6        3

   T2                    반번호   p끼리   span끼리   .i끼리
   p#A    .i               1        1        -         1
   span#B .i               2        -        1         2
   p#C    .i               3        2        -         3
   span#D                  4        -        2         -
   p#E    .i               5        3        -         4
```

### 1. `An+B` 를 펼칠 수 있는가

**실행 결과** (Chrome 151 headless, T1)

```text
  p:nth-child(2n)    ->  3개   p1, p3, p5
  p:nth-child(2n+1)  ->  3개   p2, p4, p6
  p:nth-child(-n+3)  ->  2개   p1, p2
  p:nth-child(n+3)   ->  5개   p2, p3, p4, p5, p6
  p:nth-child(3n+1)  ->  2개   p3, p6
  p:nth-child(0)     ->  0개
  p:nth-child(0n+2)  ->  1개   p1
  p:nth-child(n)     ->  6개   p1 ~ p6
```

**다섯이 각각 어느 노드를 잡는가**

- 위 출력 그대로다. 펼치는 과정은 이렇다.

```text
   2n    -> 2,4,6      반번호 2,4,6 = p1,p3,p5
   2n+1  -> 1,3,5,7    반번호 1 은 h2 라 탈락 -> p2,p4,p6
   -n+3  -> 3,2,1      반번호 1 은 h2 라 탈락 -> p1,p2
   n+3   -> 3,4,5,6,7  -> p2,p3,p4,p5,p6
   3n+1  -> 1,4,7      반번호 1 은 h2 라 탈락 -> p3,p6
```

**`-n+3` 과 `n+3` 을 뭐라고 읽는가**

- **`-n+B` = 「처음 B 개」**, **`n+B` = 「B 번째부터 끝까지」**.

**`:nth-child(0)` 은 문법 오류인가 0개인가**

- **0개다.** 문법은 유효하고, 번호가 1부터라 아무것도 안 맞을 뿐이다. `-n+0` 도 0개였다.

**`odd`·`even` 은 무엇의 별칭인가**

- `odd` = **`2n+1`**, `even` = **`2n`**.

### 2. `odd` 가 p1·p3·p5 가 아닌 이유

**실행 결과**

```text
  p:nth-child(odd)   ->  3개   p2, p4, p6
  p:nth-child(even)  ->  3개   p1, p3, p5
  p:nth-of-type(odd) ->  3개   p1, p3, p5
```

**`p:nth-child(odd)` 는 어느 셋인가**

- **p2 · p4 · p6.**

**왜 어긋나는가**

- `h2` 가 **반번호 1번**을 차지했기 때문이다. 홀수 번호는 1·3·5·7 이고 그중 1번은 `h2` 라 탈락, 남은 3·5·7 이 p2·p4·p6 이다.

**「홀수 번째 문단」을 원했다면**

- **`p:nth-of-type(odd)`** 다. 실측에서 p1·p3·p5 를 잡았다.

**어긋남을 만든 노드**

- **`h2#H`** 하나다. 그 태그 하나가 이후 모든 반번호를 한 칸 밀었다.

### 3. `:nth-child` 와 `:nth-of-type` 이 갈리는 자리

**실행 결과**

```text
  p:nth-child(1)    ->  0개
  p:nth-child(2)    ->  1개   p1
  p:nth-of-type(1)  ->  1개   p1
  p:nth-of-type(2)  ->  1개   p2
  p:first-child     ->  0개
  p:first-of-type   ->  1개   p1
  p:last-child           ->  1개   p6
  p:nth-last-child(2)    ->  1개   p5
  p:nth-last-of-type(2)  ->  1개   p5
```

**여섯이 각각 무엇을 잡는가**

- 위 출력 그대로다. **`p:nth-child(1)` 과 `p:first-child` 는 0개다.**

**`p:nth-child(1)` 이 0개인 이유**

- **"반번호가 1번이면서 `p` 인 노드"를 찾는 것**인데 1번은 `h2` 다.\
  「첫 `p`」가 아니라 「**1번 자리가 `p` 였다면**」이라는 조건이다.

**마크업 변화에 덜 취약한 쪽**

- **`:nth-of-type`** 이다. 다른 태그가 앞에 끼어들어도 `p` 끼리의 번호는 안 밀린다.
- `:nth-child` 는 형제 목록이 조금만 바뀌어도 통째로 어긋난다.

**뒤에서 세는 짝**

- `p:nth-last-child(1)` → **p6**(마지막 자식이면서 `p`) · `p:nth-last-of-type(2)` → **p5**(뒤에서 둘째 `p`).
- 이 트리에서는 뒤쪽에 `h2` 가 없어서 둘의 답이 같다 — **앞쪽에 낀 태그가 원인이었다**는 것을 거꾸로 보여 준다.

### 4. "첫 `.item`" 을 고르는 선택자

**실행 결과**

```text
  .item:nth-of-type(1)     ->  0개
  .item:nth-of-type(2)     ->  1개   p2
  .item:nth-child(3)       ->  1개   p2
  :nth-child(1 of .item)   ->  1개   p2
  p.item:nth-of-type(2)    ->  1개   p2
```

**넷이 각각 무엇을 잡는가**

- 위 출력 그대로다.

**`.item:nth-of-type(1)` 이 0개인 이유**

```text
   1) :nth-of-type(1) 이 먼저 "p 끼리 줄의 1번" 을 고른다  ->  p1
   2) 그다음 .item 인지 본다                              ->  p1 에는 없다
   -> 0개

   ★ "거르고 나서 센다" 가 아니라 "세고 나서 거른다" 이다.
```

**`.item:nth-of-type(2)` 가 `p2` 를 맞히는 것이 왜 위험한가**

- **우연이기 때문이다.** `p2` 가 `p` 줄의 2번이면서 `.item` 이기도 한 것뿐이다.
- 「되는 줄 알고」 넘어가면, 트리에 `p` 하나가 끼어드는 순간 **조용히 다른 노드를 고르게 된다.**
- `.item:nth-child(3)` 도 마찬가지 우연이다.

**「첫 `.item`」의 뜻을 정확히 갖는 것**

- **`:nth-child(1 of .item)`** 하나뿐이다.

### 5. `of S` 는 무엇을 세는가

**실행 결과**

```text
  :nth-child(2n of .item)      ->  1개   p4
  :nth-child(2n+1 of .item)    ->  2개   p2, p6
  :nth-last-child(1 of .item)  ->  1개   p6
  :nth-child(1 of .item)       ->  1개   p2
  :nth-child(2 of .item)       ->  1개   p4
  :nth-child(1 of p, span)     ->  1개   A    (T2)
  :nth-child(2 of p, span)     ->  1개   B    (T2)
```

**셋이 각각 무엇을 잡는가**

- `2n of .item` → **p4**(`.item` 줄의 2번) · `2n+1 of .item` → **p2, p6**(1번·3번) · `:nth-last-child(1 of .item)` → **p6**.

**적용 순서 세 단계**

```text
   1) 형제 중 S 에 맞는 것만 고른다   ->  [p2, p4, p6]
   2) 그 줄에 1,2,3 번호를 매긴다
   3) An+B 에 맞는 번호를 고른다
```

**`of` 뒤에 여러 개를 쓸 수 있는가**

- **쓸 수 있다.** `of` 는 **선택자 목록**을 받는다. 실측에서 `:nth-child(1 of p, span)` 이 A, `(2 of p, span)` 이 B 를 잡았다.

**`of S` 를 붙일 수 있는 것**

- **`:nth-child()` 와 `:nth-last-child()` 둘뿐**이다.

### 6. 숨긴 행이 번호를 차지하는가

**실행 결과** (여섯 `li` 의 `background-color` 를 순서대로)

```text
  li:nth-child(2n+1)
    1행 rgb(219,234,254) | 2행(숨김) 투명 | 3행 rgb(219,234,254)
    4행 투명             | 5행(숨김) rgb(219,234,254) | 6행 투명

  li:nth-child(2n+1 of :not([hidden]))
    1행 rgb(219,234,254) | 2행(숨김) 투명 | 3행 투명
    4행 rgb(219,234,254) | 5행(숨김) 투명 | 6행 투명

  참고: tr:nth-child(odd) -> r1, r3, r5   /   tr:not([hidden]) -> r1, r3, r4, r6
```

**`li:nth-child(2n+1)` 은 어느 것을 잡는가**

- **1행 · 3행 · 5행.** 그중 **5행은 숨겨져 있다.**

**보이는 줄만 보면 줄무늬가 어떻게 되는가**

```text
   화면에 보이는 것:  1행(색) 3행(색) 4행(무) 6행(무)
                      ^^^^^^^^^^^^^^ 색이 두 줄 연달아 붙는다
```

- 색칠이 가야 할 5행이 **화면에서 사라지면서** 줄무늬가 깨진다.

**`of :not([hidden])` 은 어느 것을 잡는가**

- **1행 · 4행.** 보이는 넷(1·3·4·6) 중 1번째와 3번째다.
- 화면에서는 **색 · 무 · 색 · 무**로 맞는다.

**스크린샷만으로 원인까지 진단할 수 있는가**

- **없다.** 화면에는 「두 줄이 붙었다」는 증상만 보이고, **원인인 5행의 색은 숨어 있어 안 보인다.**
- `getComputedStyle` 로 **숨은 행까지 읽어야** 「색칠이 거기로 갔구나」가 드러난다.

### 7. `of S` 와 `:nth-of-type` 이 갈리는 자리

**실행 결과** (T2)

```text
  :nth-child(2 of .i)   ->  1개   B   (span)
  .i:nth-of-type(2)     ->  1개   C   (p)
  p:nth-child(2 of .i)  ->  0개
  :nth-of-type(2)       ->  2개   C, D
  p:nth-of-type(2)      ->  1개   C
  span:nth-of-type(2)   ->  1개   D
```

**셋이 각각 무엇을 잡는가**

- `:nth-child(2 of .i)` → **span#B** · `.i:nth-of-type(2)` → **p#C** · `p:nth-child(2 of .i)` → **0개**.

**앞의 둘이 다른 노드를 잡는 이유**

```text
   of .i        ->  줄을 .i 로 만든다     [A, B, C, E]   2번 = B (span)
   :nth-of-type ->  줄을 태그로 나눈다    p:[A, C, E] / span:[B, D]
                    거기서 2번을 고른 뒤 .i 인지 본다  ->  C
```

- 「**거르고 나서 센다**」 대 「**태그로 나누고 나서 센다**」의 차이다.

**`p:nth-child(2 of .i)` 가 0개인 것이 증명하는 것**

- **순서**다. 먼저 `.i` 줄에서 2번을 뽑고(`span#B`) **그다음** `p` 인지 보니 아니라서 탈락이다.
- `of S` 가 "나중에 거르는" 것이 아니라 **먼저 줄을 만드는** 것임을 보여 준다.

**`:nth-of-type(2)` 는 몇 개인가**

- **2개** — `p#C`(p 줄 2번)와 `span#D`(span 줄 2번). **태그마다 줄이 따로 있으니 2번도 여럿이다.**

### 8. `:nth-of-type` 에 `of` 를 붙이면

**실행 결과**

```text
  스타일시트에 네 규칙을 넣고 cssRules 를 읽었다
    p:nth-of-type(2n of .item)   { color: red }    <- 담기지 않았다
    p:nth-child(2n of .item)     { color: blue }   <- 담겼다
    p:nth-child(2n of :unknownzz){ color: green }  <- 담기지 않았다
    p:nth-child(2n of .a, .b)    { color: teal }   <- 담겼다
  남은 규칙: ['p:nth-child(2n of .item)', 'p:nth-child(2n of .a, .b)']

  document.querySelectorAll('p:nth-of-type(2n of .item)')
    -> SyntaxError: 'p:nth-of-type(2n of .item)' is not a valid selector.
```

**두 규칙은 `cssRules` 에 담기는가**

- **둘 다 안 담긴다.** `:nth-of-type(… of …)` 도, `of :unknownzz` 도 사라졌다.

**`querySelectorAll` 은 무엇을 돌려주는가**

- **`SyntaxError` 예외**를 던진다. JS 에서는 시끄럽고 CSS 에서는 조용하다.

**"관대하다"는 무슨 뜻이고 `of` 는 그런가**

- **모르는 선택자가 섞여도 그것만 버리고 나머지를 살리는** 성질이다.
- **`of` 는 관대하지 않다.** `of :unknownzz` 하나에 규칙이 통째로 사라졌다.

**정본은 어느 주제인가**

- [11번 주제](../11-is-where-not/2-summary.md)다. 거기서 `:is()`·`:where()`(관대함)와 `:not()`·`:has()`·`of S`(관대하지 않음)를 같은 실험에서 대조했다.

### 9. `:empty` 는 무엇을 잡는가

**실행 결과**

```text
  <p id="e1"></p>  <p id="e2"> </p>  <p id="e3"><!--c--></p>  <p id="e4">x</p>

  p:empty  ->  2개   e1, e3
```

**넷 중 무엇을 잡는가**

- **e1 과 e3.**

**주석과 공백은 각각 세는가**

- **주석은 안 센다**(e3 가 잡혔다). **공백은 센다**(e2 가 안 잡혔다 — 공백 하나도 텍스트 노드다).

**들여쓰기하면 무슨 일이 생기는가**

- 소스를 여러 줄로 쓰면 태그 사이에 **줄바꿈+들여쓰기 텍스트 노드**가 생겨 **`:empty` 가 아니게 된다.**
- HTML 을 압축(minify)하느냐에 따라 스타일이 달라지는 자리다.

**"내용이 없어 보이는 것"으로 읽으면 어디서 틀리는가**

- `<p> </p>` 에서 틀린다 — 화면에는 아무것도 안 보이는데 `:empty` 가 아니다.
- 반대로 `<p><!--c--></p>` 는 주석만 있어도 `:empty` 다.

### 10. `:nth-child` 가 세는 것은 무엇인가

**실행 결과**

```text
  <div class="b1">텍스트만 있는 형제<p id="q1">q1</p><!--주석--><p id="q2">q2</p></div>
  childNodes: [텍스트, P, 주석, P]

  .b1 :nth-child(1)  ->  1개   q1
  .b1 :nth-child(2)  ->  1개   q2
  #q1:first-child    ->  1개   q1
```

**`.b1 :nth-child(1)` 은 무엇을 잡는가**

- **q1.**

**앞에 텍스트 노드가 있는데 왜 q1 이 1번인가**

- **`:nth-child` 는 「요소 형제」만 센다.** 텍스트·주석 노드는 번호를 안 받는다.
- 실제 자식 노드는 넷인데 번호를 받은 것은 `P` 둘뿐이다.

**`#q1:first-child` 는 맞는가**

- **맞는다.** 같은 이유다.

**구현 사정인가 명세 보장인가**

- **명세 보장이다.** Selectors 4 가 "element siblings" 를 센다고 정한다. 브라우저를 바꿔도 안 달라진다.

### 11. 명시도는 어떻게 되는가

**`p:nth-child(1)` 의 `(A, B, C)`**

- **`(0, 1, 1)`** — 의사 클래스 1(B) + 타입 1(C).

**`p:nth-child(1 of .c1)` 은**

- **`(0, 2, 1)`** — 위에 더해 **`of` 의 `.c1` 명시도가 통째로** 더해진다.
- `of .c1.c2` 였다면 `(0, 3, 1)` 이다.

**정본은 어느 주제인가**

- **[02번 주제](../02-specificity/2-summary.md)** 다. 위 두 값은 거기 「손으로 세어 보기」 16행 표에서 **두 판 대조로 실측된** 것이다.

**`:root` 가 `html` 보다 센 이유**

- **`:root` 는 의사 클래스라 B 자리**, `html` 은 타입 선택자라 C 자리다. `(0,1,0) > (0,0,1)`.
- *(Chrome 151 headless 실측: `:root { color: rgb(1,1,1) }` **뒤에** `html { color: rgb(2,2,2) }` 를 써도 계산색은 `rgb(1, 1, 1)` 이었다 — 나중에 쓴 쪽이 졌다.)*

### 12. 다른 주제와 잇기

**"n 번째 자식을 가진 부모"를 고르려면**

- **`:has()`** 다 — `div:has(> p:nth-child(3))` 꼴. 구조적 의사 클래스만으로는 **위로 못 간다**([08번](../08-basic-selectors-and-combinators/2-summary.md) (3)).
- 정본은 [목록의 **12번 주제**](../12-has-relational-selector/).

**번호로 거는 스타일이 마크업 변경에 약한 이유**

- 번호는 **형제 목록 전체에서 파생된 값**이라, 태그 하나가 끼어들거나 빠지면 **모든 번호가 밀린다.**
- 이 문서의 `h2` 하나가 그 실물이다 — 그것 때문에 `odd` 의 답이 뒤집혔다.

**「줄무늬가 두 줄 붙었다」의 원인은 어디서 찾나**

- **숨겨진 형제**다. `hidden`·`display: none` 인 형제도 **번호를 그대로 차지한다.**
- 화면이 아니라 **`getComputedStyle` 로 숨은 행까지 읽어야** 보인다.

**flex 의 `order` 로 그림 순서를 바꾸면 번호도 바뀌는가**

- **안 바뀐다.**
- *(Chrome 151 headless 실측: `display: flex` 안의 셋째 아이템에 `order: -1` 을 줘 화면 맨 왼쪽(x 좌표 8, 가장 작다)으로 보냈는데 `:nth-child(1)`·`:first-child` 는 여전히 **첫째 아이템**을 잡았다.)*
- 선택자는 **문서 트리 순서**를 보지 화면 순서를 보지 않는다.

## 용어 풀이

- **구조적 의사 클래스** — 문서 트리의 모양만 보고 판정하는 `:` 선택자.
- **`An+B`** — `:nth-*()` 괄호 안의 표기. `A` 걸음 폭 · `B` 시작 오프셋. n 에 0,1,2,… 를 넣고 1 이상만 쓴다.
- **`odd` / `even`** — `2n+1` · `2n` 의 별칭.
- **반번호(child index)** — 형제 **요소** 전체를 한 줄로 센 번호. 텍스트·주석은 안 센다.
- **타입 줄(type index)** — 같은 태그 형제끼리 다시 센 번호.
- **`of S`** — S 에 맞는 형제만 골라 **새 줄을 만드는** 필터. `:nth-child()`·`:nth-last-child()` 전용.
- **관대하지 않다(non-forgiving)** — 목록에 모르는 선택자가 하나라도 있으면 전체가 무효.
- **`:empty`** — 자식 노드가 하나도 없는 요소. 공백 텍스트가 있으면 아니고, 주석만 있으면 맞다.
- **`:root`** — 문서의 뿌리 요소. HTML 에서는 `html`. 의사 클래스라 B 자리.
- **`:only-child` / `:only-of-type`** — 형제가 아예 없는 것 / 같은 태그 형제가 없는 것.
- **`cssRules`** — 스타일시트에 실제로 담긴 규칙 목록. 규칙이 버려졌는지 확인하는 관측 창.

## 실행 검증

**환경** — Google Chrome **151.0.7922.173** (`--headless --no-sandbox --disable-gpu`). Firefox 155.0.1 은 이 환경에서 **headless 스크린샷이 산출되지 않아 쓰지 않았다.** WebKit(Safari)은 없다. **이 문서의 모든 값은 Blink 단일 엔진의 관찰이다.**

| 무엇을 | 어떻게 | 몇 번 | 결과가 실린 곳 |
|---|---|---|---|
| `An+B` 11종 (T1) | `querySelectorAll().length` + 노드 id | 11개 1회씩 | 정답 1 · 2 |
| `:nth-child` ↔ `:nth-of-type` (T1) | 같은 방법 | 9개 | 정답 3 |
| 흔한 오해 5종 (T1) | 같은 방법 | 5개 | 정답 4 |
| `of S` (T1·T2) | 같은 방법 | 9개 | 정답 5 · 7 |
| 숨긴 행 줄무늬 | `getComputedStyle().backgroundColor` 를 **숨은 행까지** 6개 전부 | 원본 1 + `of` 제거판 1 | 정답 6 · 2-summary (4) |
| `:nth-of-type(… of …)` · `of :unknownzz` | 스타일시트 4규칙 주입 후 `cssRules` + `querySelectorAll` 예외 | 1회 | 정답 8 |
| `:empty` · 요소만 세는 것 · `:root` | `querySelectorAll().length` | 8개 | 정답 9 · 10 |
| `:root` 대 `html` 승부 | `getComputedStyle` 두 판 | 2회 | 정답 11 |
| flex `order` 대 `:nth-child` | `getBoundingClientRect().left` + `querySelectorAll` | 1회 | 정답 12 |
| `An+B` 공백 규칙 | `querySelectorAll()` 예외 유무 | 5개 | 2-summary 「헷갈리는 자리」 |
| `demo` 블록 2개 | 래퍼를 씌운 사본 + `getComputedStyle` + 스크린샷 | 원본 2 + 변형 2 | 2-summary (2)(4) |

**구현 의존 항목**

| 항목 | 왜 | 다시 찍을 것 |
|---|---|---|
| `of S` 가 동작하는 것 | Baseline widely 이지만 **Chrome 111 부터**다. 더 낮은 버전에서는 규칙이 사라진다 | 정답 5 · 7 전부 |
| `cssRules` 의 `selectorText` 문자열 | **직렬화 동작** — 엔진·버전마다 표기가 다를 수 있다 | 정답 8 |
| `An+B` 전개 · 요소만 세는 것 · 숨긴 형제가 번호를 차지하는 것 | **명세 보장** — 버전이 올라도 안 바뀐다 | 다시 찍을 필요 없음 |

**안 돌려 본 것** — `:nth-of-type` 의 네임스페이스 판정(XML 문서 필요), grid 의 `grid-auto-flow` 와 선택자 번호의 관계, `:has()` 안에서의 `:nth-child` 동작. 셋 다 이 문서에서 **결론으로 쓰지 않았고 「미실행」으로 표기했다.**
