# web-platform/25-stacking-context-and-containing-block — 쌓임 맥락과 containing block: z-index가 비교되는 범위, fixed의 기준 상자, overflow 클리핑과 뷰포트 스크롤 — 정리 (힌트)

## 해결하는 문제

화면 요소는 평면에 겹쳐 그려진다. 겹친 자리에서 누가 위에 오는지, 위치 값 `top: 0`이 무엇을 기준으로 하는지, 넘친 부분을 누가 자르는지가 정해져 있어야 같은 CSS가 같은 화면을 만든다.

```text
  ┌──────── header (z-index: 2) ────────┐
  │   ┌──── card (z-index: 1) ──────────┼──┐   겹친 자리 ▓ 에서
  └───┼──▓▓▓▓▓▓▓▓▓▓────────────────────┘  │   누가 위인가?
      │  ▓ 모달 (z-index: 9999) ▓          │   모달의 top:0 은 무엇의 top인가?
      │                                  │   카드 밖으로 넘친 모달을 누가 자르나?
      └──────────────────────────────────┘
```

이 세 질문에 CSS는 세 개의 서로 다른 장치로 답한다.

- **쌓임 맥락(stacking context)** — 누가 위인가. z-index는 이 맥락 **안에서만** 비교된다.
  - *쌓임 맥락*: z축 순서를 따로 정하는 묶음. 묶음 안을 다 정렬한 뒤, 묶음 전체가 부모 묶음 안에 한 덩어리로 끼워진다.
- **containing block** — 무엇을 기준으로 놓이나. `top/left`와 `%` 크기가 이 상자를 기준으로 계산된다.
  - *containing block(기준 상자)*: 요소의 위치·크기를 계산하는 기준 사각형. `position` 값마다 찾는 규칙이 다르다.
- **overflow 클리핑** — 누가 자르나. `overflow: hidden`은 자기 상자 밖의 내용을 자른다. 단, 기준 상자 체인이 자기를 거치는 자손만 자른다.
  - *클리핑*: 상자 경계 밖의 픽셀을 그리지 않는 것. 내용은 그대로 있고 보이지만 않는다.

쉬운 예: 회사 조직도로 줄 세우기다.

- 팀(쌓임 맥락) 안에서는 직급(z-index)으로 줄을 선다. 하지만 회사 전체 행사에서는 **팀 단위로** 줄을 선다.
- 2팀 막내는 1팀에서 아무리 높은 직급을 받아도(9999) 1팀이 2팀 뒤에 서면 2팀 누구보다도 뒤다.
- 앞으로 나가려면 직급을 올리는 게 아니라 **팀을 옮겨야** 한다.

똑같은 구조다.\
카드가 층을 만들면 카드 안 모달은 카드 층의 일원이 되고, 카드 층 전체가 헤더 아래면 모달도 헤더 아래다.

실무 예:

- 카드 안 모달에 `z-index: 9999`를 줬는데 sticky 헤더(`z-index: 2`) 아래에 깔린다(아래 실험 A).
- 애니메이션을 위해 카드에 `transform: translateZ(0)`을 넣자, 화면 전체를 덮던 `position: fixed` 오버레이가 카드 크기로 줄고 카드 밖이 잘린다(아래 실험 C).
- 모달을 띄웠는데 뒤 페이지가 휠로 스크롤된다. `body`에 `overflow: hidden`을 주면 멈추지만, `html`에도 overflow를 준 페이지에서는 안 멈춘다(아래 실험 D).

이 셋을 피하는 흔한 방법이 "모달을 `body` 직속으로 옮기는 portal"이다. 옮기면 카드의 층·기준 상자·클리핑 체인에서 한꺼번에 빠진다.

## 동작·원리

### 1. 쌓임 맥락 — z-index는 전역 숫자 경쟁이 아니다

처음 그리기 쉬운 그림과 실제 그림이 다르다.

```text
처음 그린 그림 (전역 경쟁)                실제 그림 (층 단위 비교)

 모든 요소가 한 줄로 z-index 경쟁          루트 쌓임 맥락 (html)
  modal  9999  ← 맨 위                     ├ header  z:2  ─┐ 이 둘끼리만 비교
  header    2                              └ card    z:1  ─┘ → header가 위
  card      1                                 └ (card가 만든 쌓임 맥락)
                                                 └ modal z:9999 ← card 층 "안에서만" 9999
 → modal이 이긴다 (✗)                       → card 층 전체가 header 아래 → modal도 아래 (✓)
```

- MDN "Stacking context": "the z-index values of its child stacking contexts only have meaning within its parent's stacking context."
  - 흔한 오해: "z-index를 충분히 크게 주면 무엇이든 덮는다." 부모가 층을 만들면 숫자는 그 층 안에서만 의미가 있다.
- 비교 대상은 **같은 쌓임 맥락에 속한 형제 층**이다. 모달(9999)과 헤더(2)는 서로 비교되지 않는다. 비교되는 것은 모달의 조상 층인 카드(1)와 헤더(2)다.

### 2. 쌓임 맥락을 만드는 속성

쌓임 맥락은 z-index만 만드는 게 아니다. 의도하지 않은 속성 하나로도 생긴다(MDN "Features creating stacking contexts" 발췌).

```text
  루트 요소 html
  position: absolute | relative  +  z-index ≠ auto
  position: fixed | sticky              (z-index가 auto여도)
  flex·grid 아이템                 +  z-index ≠ auto
  opacity < 1
  transform · scale · rotate · translate · filter · backdrop-filter
    · perspective · clip-path · mask  ≠ none
  mix-blend-mode ≠ normal,  isolation: isolate
  will-change 에 위 속성 중 하나
  contain: layout | paint (strict·content 포함)
  container-type: size | inline-size
  top layer에 올라간 요소(<dialog> showModal, popover, 전체 화면)
```

- `position: fixed | sticky`는 z-index가 auto여도 쌓임 맥락을 만든다(CSS Positioned Layout 3: "Fixed and sticky positioned boxes nonetheless form a stacking context").
- `transform: translateZ(0)`(GPU 가속 핵), `opacity: 0.99`(페이드 애니메이션 중간값)가 의도치 않은 층의 흔한 출처다.
  - 흔한 오해: "`position: relative`를 주면 층이 생긴다." `relative`만으로는 안 생긴다. z-index가 `auto`가 아닐 때 생긴다(아래 실험 A의 (2)).

### 3. 한 층 안의 그리기 순서 — CSS 2.2 Appendix E

```text
  한 쌓임 맥락 안 (아래 → 위)                    E.2 단계
  ┌────────────────────────────────────────┐
  │ ⑦ 양수 z-index 층 (작은 값부터, 같으면 트리 순서) │  9
  │ ⑥ 위치 지정 + z-index auto/0 (트리 순서)     │  8
  │ ⑤ 인라인 내용(텍스트·inline-block)          │  7
  │ ④ float                                │  5
  │ ③ 위치 지정 없는 블록 자손의 배경·테두리       │  4
  │ ② 음수 z-index 층 (가장 음수부터)            │  3
  │ ① 층을 만든 요소 자신의 배경·테두리           │  1~2
  └────────────────────────────────────────┘
```

- 같은 z-index 값이면 **트리 순서상 뒤의 것**이 위다(E.2 8·9단계 "in tree order").
- 위치 지정 요소(⑥)는 z-index가 auto여도 위치 지정 없는 블록(③)보다 위에 그려진다. 그래서 `position: static`인 요소에 z-index를 아무리 줘도, 겹친 `position: relative` 형제가 위로 온다(아래 실험 B).
- z-index는 위치 지정 상자에 적용된다(CSS Positioned Layout 3: "The z-index property applies to all positioned boxes"). 예외로 flex·grid 아이템은 `position: static`이어도 z-index가 적용된다(CSS Flexbox 1 §4.3·CSS Grid 1 §9.5 [?] — 절 번호는 기억, 동작은 실험 B (3)으로 확인).
  - *위치 지정 요소(positioned)*: `position`이 `static`이 아닌 요소.
  - 흔한 오해: "개발자 도구 Computed에 z-index: 100이 보이니 적용된 것이다." 계산값은 100으로 나오지만 그리기에서는 쓰이지 않는다(실험 B (1)).

### 실험 A: 자식 9999는 부모 층 밖 헤더 2를 못 이긴다

환경: 헤더 `position: relative; z-index: 2`(높이 60px), 그 아래 카드 `position: relative`를 `margin-top: -30px`로 헤더와 겹치게 둔다. 카드 안 자식 `position: absolute; z-index: 9999`. 겹친 점 (50, 40)에서 `document.elementFromPoint`가 돌려준 요소 id를 DOM에 쓰고 `--dump-dom`으로 꺼냈다. 3회 같은 출력.

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(1) card{position:relative; z-index:1} 안의 child z-index:9999 → 점(50,40) 맨 위 = header
(2) card{position:relative; z-index:auto} 안의 child z-index:9999 → 맨 위 = child
(3) card{z-index:auto; opacity:0.99} 안의 child z-index:9999 → 맨 위 = header
(4) card{z-index:1} 유지, 같은 상자를 body 직속(z-index:9999)으로 옮김 → 맨 위 = portal
```

- (1) 카드가 층을 만들자 9999가 헤더 2에 졌다.
- (2) 카드가 층을 만들지 않으면 자식이 루트 층에 직접 참여해 9999 대 2로 이겼다. 문제는 숫자가 아니라 **부모의 층**이다.
- (3) z-index 없이 `opacity: 0.99` 하나로 층이 다시 생겨 졌다.
- (4) DOM을 body로 옮기면 루트 층에서 비교되어 이겼다.

```text
"Portal은 z-index를 활용하는 기능 같은데?"

처음 그린 그림                         실제 — 순서가 반대
portal = z-index를 크게 줘서           ① z-index만으로는 못 이김 (부모 층에 갇힘)   ← 실험 A (1)
         맨 위로 올리는 기능               card(z:1) 층 안의 모달(z:9999) < header(z:2)
                                       ② DOM을 body로 옮겨 층을 탈출              ← 실험 A (4)
                                       ③ 옮긴 뒤 body 최상위끼리 z-index로 순서 정리
```

### 실험 B: position 없는 요소의 z-index

환경: 블록 A(`z-index: 100`, position 없음) 다음에 블록 B(`position: relative; top: -50px`, z-index 없음)를 두어 겹치게 했다. 겹친 점 (100, 75)의 `elementFromPoint`와 `getComputedStyle(A).zIndex`. 3회 같은 출력.

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(1) A{position:static; z-index:100}, B{position:relative; z-index:auto} 겹친 점 맨 위 = B / getComputedStyle(A).zIndex = 100
(2) A{position:relative; z-index:100} → 맨 위 = A
(3) 부모 display:flex, A{position:static; z-index:100}(flex item) → 맨 위 = A
```

- (1) 계산값은 100인데 B 아래에 그려졌다. A는 ③단계(위치 지정 없는 블록), B는 ⑥단계(위치 지정, auto)에 그려진다.
- (2) `position: relative`를 주면 ⑦단계(양수 z-index 층)로 올라가 이겼다.
- (3) flex 아이템은 position 없이도 z-index가 적용됐다.

### 4. containing block — position마다 기준 상자가 다르다

```text
  position          기준 상자(containing block)                          근거: MDN "Containing block"
  ───────────────   ─────────────────────────────────────────────────
  static·relative   가장 가까운 블록 컨테이너(또는 서식 맥락을 만드는) 조상의 콘텐츠 상자
  ·sticky
  absolute          가장 가까운 위치 지정 조상(static이 아닌)의 패딩 상자. 없으면 초기 containing block
  fixed             뷰포트(연속 매체). 단 아래 속성을 가진 조상이 있으면 그 조상의 패딩 상자
```

- absolute·fixed의 기준을 **조상으로 끌어오는** 속성(MDN, CSS Positioned Layout 3 "fixed positioning containing block"):
  - `transform`·`perspective`·`filter`·`backdrop-filter`·`rotate`·`scale`·`translate` ≠ none
  - `contain: layout | paint | strict | content`
  - `will-change`에 위 속성(예: `transform`, `filter`)
  - `content-visibility: auto`
- *초기 containing block*: 루트 요소의 기준 상자. 연속 매체에서는 뷰포트 크기의 사각형이다.

```text
처음 그린 그림                            실제 그림 (조상에 transform이 있을 때)

 position: fixed = 항상 화면 기준          fixed의 기준 찾기: 조상을 거슬러 올라감
                                          overlay → card(transform 있음!) → 멈춤
 ┌──────── 뷰포트 ────────┐                ┌──────── 뷰포트 ────────┐
 │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│                │                      │
 │▒▒▒ overlay inset:0 ▒▒▒│                │   ┌── card ──┐        │
 │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│                │   │▒▒overlay▒│ ← inset:0 이 card 기준
 └──────────────────────┘                │   └──────────┘        │
                                          └──────────────────────┘
```

- 흔한 오해: "fixed니까 화면 기준이겠지." 조상 어딘가의 `transform` 하나로 기준이 바뀐다. 그 조상은 같은 속성 때문에 쌓임 맥락도 만든다 — `transform`은 층과 기준 상자를 **동시에** 바꾼다.
- 반대로 `opacity < 1`은 쌓임 맥락만 만들고 기준 상자는 바꾸지 않는다(아래 실험 C (3)). 두 효과는 별개다.

### 5. overflow 클리핑 — 기준 상자 체인이 지나가는 자손만 자른다

```text
  CSS 2.2 §11.1.1: 클리핑은 "all of the element's content except any descendant elements
   (and their respective content and descendants) whose containing block is the viewport
   or an ancestor of the element" 에 적용된다.

  .card { overflow: hidden; position: relative; }

    absolute 자식 → 기준 = card (위치 지정 조상)      → 체인이 card를 거침  → 잘림
    fixed 자식    → 기준 = 뷰포트 (card 밖)          → 체인이 card를 안 거침 → 안 잘림

  .card { overflow: hidden; position: relative; transform: translateZ(0); }

    fixed 자식    → 기준 = card (transform 때문)     → 잘림
```

- 흔한 오해: "`overflow: hidden`이면 자식은 다 잘린다." 기준 상자가 그 요소 바깥(뷰포트 등)인 fixed 자손은 DOM상 자식이어도 안 잘린다. 그래서 `overflow: hidden`만 있는 카드에서는 fixed 모달이 멀쩡히 화면을 덮는다.
- CSS Overflow 3은 상자의 넘침(overflow)에 "all descendants whose containing block chain includes the box"를 포함한다고 정의한다. 클리핑 대상도 이 체인으로 갈린다.

### 실험 C: 조상 transform 하나로 fixed 오버레이가 카드에 갇힌다

환경: 카드 `position: relative; overflow: hidden`(뷰포트 좌표 100,100, 300×150) 안에 오버레이 `position: fixed; inset: 0`. 카드에 속성을 하나씩 넣었다 빼며 오버레이의 `getBoundingClientRect`와, 카드 밖 점 (20, 20)의 `elementFromPoint`를 기록. 3회 같은 출력.

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
viewport = 800x513, card rect = 100,100 300x150
(1) card{overflow:hidden; position:relative}, overlay{position:fixed; inset:0}
   overlay rect = 0,0 800x513 / 카드 밖 점(20,20) 맨 위 = overlay
(2) + card{transform:translateZ(0)}
   overlay rect = 100,100 300x150 / 카드 밖 점(20,20) 맨 위 = HTML
(2) + card{filter:blur(0px)}
   overlay rect = 100,100 300x150 / 카드 밖 점(20,20) 맨 위 = HTML
(2) + card{will-change:transform}
   overlay rect = 100,100 300x150 / 카드 밖 점(20,20) 맨 위 = HTML
(2) + card{contain:paint}
   overlay rect = 100,100 300x150 / 카드 밖 점(20,20) 맨 위 = HTML
(3) + card{opacity:0.99} (쌓임 맥락만 만듦)
   overlay rect = 0,0 800x513 / 카드 밖 점(20,20) 맨 위 = overlay
```

- (1) `overflow: hidden`만으로는 fixed 오버레이가 뷰포트 전체(800×513)를 덮었다. 카드 밖 점도 오버레이였다.
- (2) 네 속성 모두 오버레이 상자를 카드 크기(300×150)로 바꿨다. `inset: 0`이 카드 기준이 됐다. 카드 밖 점에는 오버레이가 없어 뒤의 `html`이 잡혔다.
- (2)의 `filter: blur(0px)`는 눈에 보이는 효과가 없는 값인데도 기준을 바꿨다. `none`이 아니면 된다.
- (3) `opacity`는 층만 만들고 기준 상자는 그대로였다.
- `elementFromPoint`는 히트 테스트 결과다. 눈으로 본 픽셀을 캡처한 것이 아니므로, 화면 픽셀 클리핑은 이 실험으로 직접 재지 않았다. 오버레이 상자 자체가 카드 크기로 줄었으므로 카드 밖에 그려질 것이 없다는 것까지가 측정 범위다.

### 6. 페이지 스크롤은 누구의 것인가 — body → 뷰포트 전파

```text
처음 그린 그림                           실제 그림

 body 가 길어서 body 가 스크롤된다        스크롤되는 것은 뷰포트(창)다
 ┌ body ─────────┐ ▲                    ┌ 뷰포트 ───────┐ ▲  ← 스크롤바의 주인
 │               │ █                    │ html          │ █
 │               │ │                    │  └ body       │ │
 └───────────────┘ ▼                    └───────────────┘ ▼
                                         html·body 내용이 뷰포트보다 길어서 넘친다
```

- CSS Overflow 3 §3.1.4·CSS 2.2 §11.1.1: 루트 요소(`html`)의 overflow를 뷰포트에 적용한다. 단 `html`의 overflow가 양 축 `visible`이고 `body`가 있으면, **`body`의 overflow를 대신 뷰포트에 적용**한다. 값을 넘긴 `body` 자신의 사용값은 `visible`이 된다.

```text
  html.overflow   body.overflow   뷰포트에 적용되는 값      body 자신
  ─────────────   ─────────────   ─────────────────────   ─────────────────────────
  visible         hidden          hidden  (body → 뷰포트)   visible (사용값)
  auto            hidden          auto    (html → 뷰포트)   hidden — body가 자기 스크롤 컨테이너
  hidden          visible         hidden  (html → 뷰포트)   visible
```

- `overflow: hidden`은 사용자 스크롤(휠·터치·스크롤바)을 막지만, 코드의 `scrollTo`는 막지 않는다(CSS Overflow 3: "the content must still be scrollable programmatically"). 코드 스크롤까지 막는 값은 `clip`이다.
  - *스크롤 컨테이너*: 넘친 내용을 스크롤로 보여 줄 수 있는 상자. `hidden`·`auto`·`scroll`은 스크롤 컨테이너를 만들고 `clip`은 만들지 않는다.
  - 흔한 오해: "`hidden`으로 바꾸면 넘친 내용이 지워진다." 내용은 그대로 있고 사용자가 그쪽으로 못 갈 뿐이다. 원래 값으로 되돌리면 보던 위치에서 다시 스크롤된다.

### 실험 D: body overflow의 전파와 스크롤 잠금

환경: 높이 3000px 내용. 각 설정에서 뷰포트 세로 스크롤바 폭(`innerWidth - documentElement.clientWidth`), `scrollTo(0, 500)` 뒤 `scrollY`를 기록. 이어서 모달 2개를 열고 1개를 닫는 잠금 시나리오를 스위치 방식과 카운트 방식으로 비교했다(원래 값 `'scroll'`). 3회 같은 출력.

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(1) 기본
   html.overflow(computed)=visible body.overflow(computed)=visible 뷰포트 세로 스크롤바 폭=15px scrollTo(0,500) 뒤 scrollY=500 body.scrollTop=0
(2) body{overflow:hidden}
   html.overflow(computed)=visible body.overflow(computed)=hidden 뷰포트 세로 스크롤바 폭=0px scrollTo(0,500) 뒤 scrollY=500 body.scrollTop=0
(3) html{overflow:auto} + body{overflow:hidden}
   html.overflow(computed)=auto body.overflow(computed)=hidden 뷰포트 세로 스크롤바 폭=15px scrollTo(0,500) 뒤 scrollY=500 body.scrollTop=0
(4) html{overflow:hidden}
   html.overflow(computed)=hidden body.overflow(computed)=visible 뷰포트 세로 스크롤바 폭=0px scrollTo(0,500) 뒤 scrollY=500 body.scrollTop=0
(5) 스위치 방식: 원래 'scroll' → 모달 2개 열고 1개 닫음 → body.style.overflow=''
(6) 카운트+원래 값 방식: 원래 'scroll' → 2개 열고 1개 닫음 → 'hidden' → 나머지 닫음 → 'scroll'
```

- (2) `body`에 준 `hidden`이 뷰포트로 전파되어 뷰포트 스크롤바가 사라졌다(15px → 0px).
- (3) `html`이 `visible`이 아니면 전파되지 않는다. 뷰포트 스크롤바가 남았다 — 잠금 실패다. `body`는 자기 스크롤 컨테이너가 됐지만 높이가 내용만큼 늘어 넘침이 없으므로 아무것도 막지 않는다.
- (2)~(4) 모두 `scrollTo` 뒤 `scrollY=500`이다. `hidden`이어도 코드 스크롤은 된다.
- `getComputedStyle(body).overflow`는 (2)에서 `hidden`이다. 계산값을 보여 줄 뿐, 전파 뒤의 사용값(`visible`)은 보여 주지 않는다.
- (5) 스위치 방식은 모달이 하나 남았는데 잠금이 풀렸고, 원래 값 `'scroll'`도 잃었다. (6) 카운트 방식은 마지막 모달이 닫힐 때만 원래 값으로 돌렸다.
- 측정하지 못한 것: headless에서 실제 휠·터치 입력으로 사용자 스크롤이 막히는지는 이 실험에서 재지 않았다. 스크롤바 폭 0과 명세 문장을 근거로 한다.

## 쓰이는 자료구조·알고리즘

- **쌓임 맥락 트리 + 층 단위 재귀 그리기**: 쌓임 맥락은 DOM 트리 위에 얹힌 더 성긴 트리다. 그리기는 층마다 Appendix E 순서로 자식 층을 그리고, 자식 층 안으로 재귀한다 — 깊이 우선 순회. → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)

```text
  DOM 트리                      쌓임 맥락 트리 (층을 만든 요소만)
  html                          html (루트 층)
   ├ header (rel, z:2)           ├ header  [z:2]
   └ main                        └ card    [z:1]
      └ card (rel, z:1)              └ modal [z:9999]   ← card 층의 자식으로만 정렬됨
         └ div
            └ modal (abs, z:9999)
```

- **층 안의 안정 정렬**: 같은 층의 자식 층을 z-index로 정렬하고, 같은 값이면 트리 순서를 유지한다 — 키가 z-index인 안정 정렬과 같은 결과다. → [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md)
- **조상 방향 선형 탐색**: containing block은 부모 포인터를 따라 올라가며 조건(위치 지정·`transform` 등)에 맞는 첫 조상을 찾는다. 깊이 d에 O(d). `closest()`와 같은 모양이다. → [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md)
- **참조 카운트**: 스크롤 잠금을 여러 모달이 공유할 때, "몇 개가 잠금을 원하나"를 정수로 세고 0이 될 때만 푼다. 첫 획득 때만 원래 값을 저장한다.

## 적용 — 풀어나가는 법

1. **"z-index를 올려도 안 올라온다" → 숫자보다 층을 먼저 찾는다.**
   - 증상: 9999, 99999로 올려도 그대로다.
   - 원리: 그 요소의 조상 중 쌓임 맥락을 만든 첫 조상이 경쟁 단위다.
   - 확인: 아래 스니펫으로 조상의 층을 나열한다. Chrome DevTools의 Layers 패널, Elements의 Computed 패널도 쓸 수 있다.

```javascript
// 조상 중 쌓임 맥락을 만들 법한 요소를 나열한다(주요 속성만 — MDN 목록 전체는 아니다)
function stackingAncestors(el) {
  const out = [];
  for (let n = el.parentElement; n; n = n.parentElement) {
    const s = getComputedStyle(n);
    const parentDisplay = n.parentElement ? getComputedStyle(n.parentElement).display : '';
    const flexOrGridItem = /flex|grid/.test(parentDisplay);
    const why = [
      s.position !== 'static' && s.zIndex !== 'auto' && `position:${s.position}+z-index:${s.zIndex}`,
      (s.position === 'fixed' || s.position === 'sticky') && `position:${s.position}`,
      flexOrGridItem && s.zIndex !== 'auto' && `flex/grid item+z-index:${s.zIndex}`,
      s.opacity !== '1' && `opacity:${s.opacity}`,
      s.transform !== 'none' && 'transform',
      s.filter !== 'none' && 'filter',
      s.isolation === 'isolate' && 'isolation',
      /transform|opacity|filter/.test(s.willChange) && `will-change:${s.willChange}`,
      /paint|layout|strict|content/.test(s.contain) && `contain:${s.contain}`,
    ].filter(Boolean);
    if (why.length) out.push([n, why.join(', ')]);
  }
  return out; // 첫 항목이 el이 실제로 경쟁하는 층
}
```

2. **"fixed 모달이 카드 안에 갇혀 잘린다" → 기준 상자를 찾는다.**
   - 증상: 오버레이가 화면 전체가 아니라 어떤 상자 크기로 줄고 그 밖이 잘린다.
   - 원리: 조상의 `transform`·`filter`·`will-change`·`contain`이 fixed의 기준을 가져갔다.
   - 확인: `overlay.getBoundingClientRect()`가 뷰포트 크기인지 본다(실험 C). 아니라면 위 스니펫처럼 조상을 올라가며 `transform`·`filter`·`contain`·`willChange`를 본다.
3. **층·기준 상자·클리핑에서 한꺼번에 빠지기 — DOM을 body 직속으로 옮긴다.** 예: 모달·툴팁·드롭다운을 body로 옮기는 portal. 옮긴 뒤에는 body 직속 요소끼리 같은 층(루트)에서 비교되므로, 그 안에서만 z-index 규칙을 정한다.

```javascript
// body 직속 레이어들에 열린 순서대로 z-index 부여 — 나중에 연 것이 위(값은 예시)
const BASE_Z = 1000;
const stack = [];
const restack = () => stack.forEach((el, i) => { el.style.zIndex = String(BASE_Z + i); });
export function pushLayer(el) { stack.push(el); restack(); }
export function removeLayer(el) {
  const i = stack.indexOf(el);
  if (i !== -1) { stack.splice(i, 1); restack(); }
}
// 레이어 컨테이너는 position 값이 있어야 z-index가 적용된다(실험 B)
```

4. **z-index는 숫자 경쟁 대신 이름 붙은 단계로.** 예: `--z-header: 10; --z-dropdown: 100; --z-modal: 1000;`(예시). 새 층이 필요한 컴포넌트는 `isolation: isolate`로 자기 내부 z-index가 밖과 경쟁하지 않게 가둔다.
5. **배경 스크롤 잠금은 카운트 + 원래 값 복원으로.**

```javascript
let lockCount = 0;
let savedOverflow = '';
export function lockScroll() {
  if (lockCount++ === 0) {
    savedOverflow = document.body.style.overflow;  // 첫 잠금 때만 원래 값 저장
    document.body.style.overflow = 'hidden';       // html이 visible이면 뷰포트로 전파
  }
}
export function unlockScroll() {
  if (--lockCount === 0) document.body.style.overflow = savedOverflow;
}
```

   - `html`에 overflow를 준 페이지면 `document.documentElement`를 잠근다(실험 D (3)·(4)).
   - 스크롤바가 사라지면 폭(실험: 15px)만큼 레이아웃이 옆으로 밀린다. `scrollbar-gutter: stable`이나 잠글 때 `padding-right` 보정을 쓴다.
   - iOS Safari에서는 `overflow: hidden`만으로 터치 스크롤이 막히지 않는 경우가 보고된다 [?]. 라이브러리들은 `position: fixed` + 스크롤 위치 저장·복원을 함께 쓴다.

## 장애 시나리오와 대처

### 1. 자식 z-index 9999가 부모 층 밖 헤더(z-index 2)를 못 이김 (⚠ 커리큘럼)

- **현상**: 카드·패널 안에서 연 모달·드롭다운이 sticky 헤더 아래에 깔린다.
- **보이는 형태**: z-index를 9999, 99999로 올려도 그대로다. 헤더와 겹친 부분만 가려진다(실험 A (1): 맨 위 = header).
- **원인**: 조상(카드)이 `position + z-index`·`opacity`·`transform` 등으로 쌓임 맥락을 만들었다. 자식의 z-index는 카드 층 안에서만 비교되고, 카드(1)가 헤더(2)에 진다.
- **대처**: 요소를 body 직속으로 옮겨 루트 층에서 비교한다(실험 A (4)). 옮길 수 없으면 카드의 z-index를 헤더보다 높이거나, 층을 만드는 속성이 꼭 필요한지 본다(실험 A (2)).

### 2. 조상 transform 하나로 fixed 모달이 카드 안에 갇혀 잘림 (⚠ 커리큘럼)

- **현상**: 애니메이션·GPU 가속을 위해 조상에 `transform`(또는 `filter`·`will-change: transform`·`contain: paint`)을 넣은 뒤, 화면을 덮던 모달이 카드 크기로 줄고 카드 밖이 잘린다.
- **보이는 형태**: 오버레이의 `getBoundingClientRect()`가 뷰포트가 아니라 카드 크기다(실험 C (2): 300×150). 카드 밖 클릭이 오버레이에 안 닿는다.
- **원인**: 그 속성이 fixed 자손의 containing block을 조상으로 바꿨다. 이제 기준 상자 체인이 `overflow: hidden` 카드를 거치므로 잘린다.
- **대처**: 모달을 body로 옮긴다. 효과용 `transform`을 모달 조상이 아닌 형제·자식 요소로 옮긴다. `translateZ(0)` 같은 가속 핵은 필요한 요소에만 둔다.

### 3. position 없는 요소의 z-index가 무시됨 (⚠ 커리큘럼)

- **현상**: z-index를 준 요소가 z-index 없는 다른 요소 아래에 깔린다.
- **보이는 형태**: DevTools Computed에는 `z-index: 100`이 보인다(실험 B (1): 계산값 100, 맨 위 = B).
- **원인**: `position: static`이고 flex·grid 아이템도 아니라 z-index가 그리기에 쓰이지 않는다. 겹친 쪽이 위치 지정 요소면 ⑥단계로 그려져 위로 온다.
- **대처**: `position: relative`를 함께 준다(실험 B (2)). 부모가 flex·grid이면 그대로 적용된다(실험 B (3)).

### 4. 배경 스크롤 잠금이 안 걸림 — html overflow

- **현상**: 모달을 띄웠는데 뒤 페이지가 휠로 스크롤된다.
- **보이는 형태**: `body.style.overflow`는 `'hidden'`인데 뷰포트 스크롤바가 남아 있다(실험 D (3): 15px).
- **원인**: 전역 CSS가 `html`에 `overflow`(예: `auto`, `overflow-x: hidden`)를 줬다. `html`이 `visible`이 아니면 `body`의 값은 뷰포트로 전파되지 않는다.
- **대처**: `html`(`document.documentElement`)의 overflow를 잠근다(실험 D (4)). 잠금 대상을 한 함수에 모아 페이지 구조가 바뀌어도 한 곳만 고친다.

### 5. 모달 하나만 닫았는데 배경 스크롤이 풀림 · 원래 overflow 소실

- **현상**: 모달 위에 확인 모달을 띄우고 확인 모달만 닫으면, 아래 모달이 떠 있는데 배경이 스크롤된다. 모달을 다 닫은 뒤 페이지의 원래 스크롤 설정이 바뀌어 있다.
- **보이는 형태**: 실험 D (5): 2개 열고 1개 닫음 → `body.style.overflow = ''`, 원래 `'scroll'`을 잃음.
- **원인**: 열 때 `'hidden'`, 닫을 때 `''`로 덮는 on/off 스위치. 둘째 모달이 열 때 값을 다시 저장하면 이미 `'hidden'`인 값을 원래 값으로 착각한다.
- **대처**: 참조 카운트로 0이 될 때만 풀고, 첫 잠금 때만 원래 값을 저장해 그 값으로 돌린다(실험 D (6)).

## 핵심 문장

- z-index는 같은 쌓임 맥락 안에서만 비교된다. 부모가 층을 만들면 자식 9999도 부모 층 밖의 2를 못 이긴다(실험 A).
- 쌓임 맥락은 `position + z-index`만이 아니라 `opacity < 1`·`transform`·`filter`·`will-change`·`contain`·fixed·sticky 등으로도 생기고, 층 안은 Appendix E 순서와 트리 순서로 그려진다.
- z-index는 위치 지정 상자(그리고 flex·grid 아이템)에만 적용된다. 계산값이 보여도 그리기에 안 쓰일 수 있다(실험 B).
- `position: fixed`의 기준은 보통 뷰포트지만, 조상의 `transform`·`filter`·`will-change`·`contain`이 그 조상으로 바꾼다. 그러면 그 조상의 `overflow: hidden`에 잘린다(실험 C).
- 페이지 스크롤은 뷰포트의 것이고, `html`이 `visible`일 때만 `body`의 overflow가 뷰포트로 전파된다(실험 D).
- 층·기준 상자·클리핑을 한꺼번에 벗어나는 방법은 DOM을 body 직속으로 옮기는 것이고, z-index는 옮긴 다음에 순서를 정하는 데 쓴다.

## 관련 주제·근거

- 선행
  - [02-rendering-pipeline](../02-rendering-pipeline/2-summary.md) — 레이아웃·페인트·합성. 쌓임 맥락은 페인트 순서를, containing block은 레이아웃 기준을 정한다. `transform`·`will-change`는 합성 레이어와도 엮인다.
- 후속
  - [26-portals-and-two-trees](../26-portals-and-two-trees/2-summary.md) — 쌓임 맥락·containing block에서 벗어나려고 DOM을 옮길 때, 논리 관계(이벤트·Context·수명)는 어떻게 유지하나
  - [27-modal-dialog-behavior](../27-modal-dialog-behavior/2-summary.md) — 옮긴 모달의 상호작용 계약(바깥 클릭·ESC·Tab·스크롤 잠금 참조 카운트)
- 연결
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md) — DOM을 body로 옮기면 이벤트 버블 경로도 바뀐다
  - [21-component-and-state-patterns](../21-component-and-state-patterns/2-summary.md)
  - [23-web-symptom-index](../23-web-symptom-index/2-summary.md) — 증상에서 원인 계층으로
  - 자료구조: [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md), [algorithm/09-sorting-in-practice](../../algorithm/09-sorting-in-practice/2-summary.md)
- 문서
  - CSS 2.2 Appendix E "Elaborate description of Stacking Contexts" <https://www.w3.org/TR/CSS22/zindex.html> — E.2 그리기 순서(음수 z-index → 위치 지정 없는 블록 → float → 인라인 → z-index auto/0 → 양수 z-index, 같은 값은 tree order)
  - CSS 2.2 §11.1.1 overflow <https://www.w3.org/TR/CSS22/visufx.html> — 클리핑 예외(기준 상자가 뷰포트·조상인 자손), 루트·body overflow의 뷰포트 적용
  - CSS Positioned Layout Level 3 <https://drafts.csswg.org/css-position-3/> — fixed positioning containing block(layout viewport, `transform` 등), "Fixed and sticky positioned boxes nonetheless form a stacking context", "The z-index property applies to all positioned boxes"
  - CSS Overflow Level 3 <https://drafts.csswg.org/css-overflow-3/> — §3.1.4 viewport propagation, `hidden`은 코드 스크롤 허용·`clip`은 금지, 넘침 = "descendants whose containing block chain includes the box"
  - MDN "Stacking context" <https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_positioned_layout/Stacking_context> — 쌓임 맥락을 만드는 속성 목록
  - MDN "Containing block" <https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_display/Containing_block> — position별 기준 상자, absolute·fixed의 기준을 바꾸는 조상 속성
- 실험 목록(Google Chrome 155.0.8059.79, `--headless=new --disable-gpu --window-size=800,600 --dump-dom`, 페이지 안 스크립트가 측정값을 DOM에 기록, 각 3회 같은 출력, 2026-11-04)
  - A: 부모 층 유무(`z-index:1` / `auto` / `opacity:0.99`)와 body 이동에 따른 겹친 점의 `elementFromPoint`
  - B: `position: static`·`relative`·flex 아이템의 z-index 적용 여부, `getComputedStyle().zIndex`
  - C: `overflow: hidden` 카드 안 fixed 오버레이의 `getBoundingClientRect`·카드 밖 `elementFromPoint` — `transform`·`filter`·`will-change`·`contain`·`opacity` 각각
  - D: `html`·`body` overflow 조합별 뷰포트 스크롤바 폭·`scrollTo` 결과, 스위치 vs 카운트 잠금
