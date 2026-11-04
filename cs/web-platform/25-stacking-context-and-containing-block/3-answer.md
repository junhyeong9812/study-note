# web-platform/25-stacking-context-and-containing-block — 정답

## 정답

### 1. z-index는 층 단위로 비교된다

```text
 루트 쌓임 맥락 (html)
 ├ header  z:2  ─┐ 비교되는 것은 이 둘
 └ card    z:1  ─┘ → header가 위
    └ (card가 만든 쌓임 맥락)
       └ modal z:9999  ← card 층 안에서만 의미가 있음
```

- z-index는 같은 쌓임 맥락에 속한 형제끼리만 비교된다(MDN: "only have meaning within its parent's stacking context").
- 모달(9999)과 헤더(2)는 서로 비교되지 않는다. 모달이 속한 층의 대표인 카드(1)가 헤더(2)와 비교되어 진다. 카드 층 전체가 헤더 아래이므로 모달도 헤더 아래다.

### 2. 실험 A 예측

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(1) card{position:relative; z-index:1} 안의 child z-index:9999 → 점(50,40) 맨 위 = header
(2) card{position:relative; z-index:auto} 안의 child z-index:9999 → 맨 위 = child
(3) card{z-index:auto; opacity:0.99} 안의 child z-index:9999 → 맨 위 = header
(4) card{z-index:1} 유지, 같은 상자를 body 직속(z-index:9999)으로 옮김 → 맨 위 = portal
```

- (1) 카드 층에 갇혀 졌다.
- (2) `position: relative`만으로는 층이 생기지 않는다. 자식이 루트 층에서 9999 대 2로 이겼다.
- (3) `opacity < 1`이 층을 만들어 다시 졌다. 층을 만드는 것은 z-index만이 아니다.
- (4) body 직속이 되자 루트 층에서 비교되어 이겼다.

### 3. portal과 z-index의 순서

```text
처음 그림: portal = z-index를 크게 줘서 올리는 기능
실제:     ① z-index만으로는 부모 층을 못 벗어남(실험 A (1))
          ② DOM을 body 직속으로 옮겨 층·기준 상자·클리핑 체인을 벗어남(실험 A (4))
          ③ 옮긴 뒤 body 직속 레이어끼리 z-index로 순서를 정함(예: 열린 순서대로 1000 + i)
```

- portal은 z-index를 쓰는 기능이 아니라, **z-index만으로는 안 되는 문제**를 DOM 이동으로 푸는 기능이다.
- z-index는 옮긴 **다음** 단계에서, 같은 루트 층에 모인 레이어끼리의 순서에 쓴다. 이때 레이어 컨테이너에 `position` 값이 있어야 z-index가 적용된다(정답 4).

### 4. position 없는 z-index

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(1) A{position:static; z-index:100}, B{position:relative; z-index:auto} 겹친 점 맨 위 = B / getComputedStyle(A).zIndex = 100
(2) A{position:relative; z-index:100} → 맨 위 = A
(3) 부모 display:flex, A{position:static; z-index:100}(flex item) → 맨 위 = A
```

- 맨 위는 B다. A는 위치 지정 요소가 아니라 z-index가 그리기에 쓰이지 않는다. A는 Appendix E 4단계(위치 지정 없는 블록), B는 8단계(위치 지정, z-index auto)에 그려진다.
- `getComputedStyle(A).zIndex`는 `"100"`이다. 계산값이 보인다고 적용된 것은 아니다.
- 부모가 flex면 A는 flex 아이템이라 position 없이도 z-index가 적용되어 A가 위다.

### 5. 무엇이 잘리나

- 기본(`transform` 없음): absolute 자식은 잘리고 fixed 자식은 안 잘린다.
  - absolute의 기준 상자 = 가장 가까운 위치 지정 조상 = 카드. 체인이 카드를 거친다.
  - fixed의 기준 상자 = 뷰포트. 체인이 카드를 거치지 않는다.
- `transform: translateZ(0)`을 더하면 fixed의 기준 상자가 카드로 바뀌어 fixed 자식도 잘린다. 카드는 같은 속성 때문에 쌓임 맥락도 만든다.
- 근거: CSS 2.2 §11.1.1 — 클리핑은 "all of the element's content except any descendant elements … whose containing block is the viewport or an ancestor of the element"에 적용된다. MDN "Containing block" — fixed는 뷰포트 기준이지만, `transform` 등이 `none`이 아닌 조상이 있으면 그 조상의 패딩 상자가 기준이다.

### 6. 실험 C 예측

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(2) + card{filter:blur(0px)}
   overlay rect = 100,100 300x150 / 카드 밖 점(20,20) 맨 위 = HTML
(2) + card{will-change:transform}
   overlay rect = 100,100 300x150 / 카드 밖 점(20,20) 맨 위 = HTML
(2) + card{contain:paint}
   overlay rect = 100,100 300x150 / 카드 밖 점(20,20) 맨 위 = HTML
(3) + card{opacity:0.99} (쌓임 맥락만 만듦)
   overlay rect = 0,0 800x513 / 카드 밖 점(20,20) 맨 위 = overlay
```

- `filter`·`will-change: transform`·`contain: paint`는 카드(300×150). 셋 다 fixed의 기준 상자를 조상으로 끌어오는 속성이다. `blur(0px)`처럼 눈에 띄는 효과가 없어도 `none`이 아니면 된다.
- `opacity: 0.99`는 뷰포트(800×513). 쌓임 맥락은 만들지만 기준 상자는 바꾸지 않는다.

### 7. body overflow → 뷰포트

- 페이지 스크롤은 `body`가 아니라 뷰포트의 것이다. CSS Overflow 3 §3.1.4: `html`의 overflow가 양 축 `visible`이고 `body`가 있으면, `body`의 overflow를 뷰포트에 적용한다. 그래서 `body`의 `hidden`이 뷰포트 스크롤을 막는다.
- `html { overflow: auto }`면 전파되지 않는다. 뷰포트에는 `html`의 `auto`가 적용되어 스크롤이 남는다. `body`는 자기 스크롤 컨테이너가 되지만 높이가 내용만큼 늘어 막는 것이 없다.
- `hidden`이어도 `scrollTo`는 동작한다("must still be scrollable programmatically"). 코드 스크롤까지 막는 값은 `clip`이다.

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(2) body{overflow:hidden}
   html.overflow(computed)=visible body.overflow(computed)=hidden 뷰포트 세로 스크롤바 폭=0px scrollTo(0,500) 뒤 scrollY=500 body.scrollTop=0
(3) html{overflow:auto} + body{overflow:hidden}
   html.overflow(computed)=auto body.overflow(computed)=hidden 뷰포트 세로 스크롤바 폭=15px scrollTo(0,500) 뒤 scrollY=500 body.scrollTop=0
```

- 실제 휠·터치 입력이 막히는지는 실험에서 재지 않았다. 스크롤바 폭과 명세가 근거다.

### 8. 잠금 스위치 → 참조 카운트

- 원인 1: 열 때 `'hidden'`, 닫을 때 `''`로 덮는 on/off 스위치라, 모달이 하나 남았는데 확인 모달이 닫히며 잠금을 풀었다.
- 원인 2: 닫을 때 `''`로 덮어 원래 값 `'scroll'`을 잃었다. 열 때마다 저장하면 둘째 모달은 이미 `'hidden'`인 값을 원래 값으로 저장한다.

(실험, Google Chrome 155.0.8059.79 headless=new, 창 800×600, 2026-11-04)

```text
(5) 스위치 방식: 원래 'scroll' → 모달 2개 열고 1개 닫음 → body.style.overflow=''
(6) 카운트+원래 값 방식: 원래 'scroll' → 2개 열고 1개 닫음 → 'hidden' → 나머지 닫음 → 'scroll'
```

```javascript
let lockCount = 0;
let savedOverflow = '';
function lockScroll() {
  if (lockCount++ === 0) {
    savedOverflow = document.body.style.overflow;  // 첫 잠금 때만 저장
    document.body.style.overflow = 'hidden';
  }
}
function unlockScroll() {
  if (--lockCount === 0) document.body.style.overflow = savedOverflow;  // 마지막 해제 때만 복원
}
```

### 9. will-change 하나로 생긴 두 증상

- 잘림: `will-change: transform`은 fixed 자손의 기준 상자를 카드로 바꾼다(실험 C (2)). 오버레이의 `inset: 0`이 카드 기준이 되고, 기준 상자 체인이 카드를 거치므로 카드의 `overflow: hidden`에 잘린다.
- 헤더 아래: 같은 속성이 카드에 쌓임 맥락을 만든다. 모달의 z-index는 카드 층 안에서만 비교되고, z-index가 auto인 카드 층은 루트 층에서 8단계(z-index auto/0)에 그려져 9단계의 헤더(`z-index: 2`) 아래다. 같은 구조를 `opacity: 0.99`로 측정한 것이 실험 A (3)이다 — `will-change`로 헤더와 겹치는 경우는 직접 측정하지 않았다.
- 한 번에 해결: 모달을 body 직속으로 옮긴다. 층(실험 A (4))과 기준 상자·클리핑 체인에서 동시에 빠진다. 옮길 수 없으면 `will-change`를 hover 대상 요소(모달의 조상이 아닌 요소)로 좁히거나, 애니메이션 중에만 건다.
