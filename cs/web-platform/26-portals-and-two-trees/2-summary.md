# web-platform/26-portals-and-two-trees — 두 트리: 컴포넌트(논리) 트리와 DOM 트리, Portal과 논리 버블링 — 정리 (힌트)

## 해결하는 문제

카드 안의 버튼이 모달을 연다. 모달은 카드의 상태·Context·클릭 처리를 그대로 써야 한다. 그런데 모달의 DOM이 카드 안에 있으면 카드의 CSS에 갇힌다.

```text
  카드 안에 모달 DOM을 두면                   모달 DOM만 body로 옮기면 (appendChild)
  ┌ .card  overflow:hidden; transform ┐      body
  │  ┌ .modal ───────────────┐        │       ├ #app ─ .card          ← 카드는 그대로
  │  │ 카드 상자에 잘림·갇힘  │        │       └ .modal                ← 화면은 OK
  └──┴───────────────────────┴────────┘
  CSS 문제 ✗ / 관계 OK                      CSS 문제 OK / 관계 ✗ (카드의 Context·onClick·수명과 끊김)
```

- 갇히는 이유(쌓임 맥락·containing block·overflow 클리핑)는 선행 주제 [25-stacking-context-and-containing-block](../25-stacking-context-and-containing-block/2-summary.md)이 다룬다.
- 둘 다 원한다: **DOM은 다른 곳에, 관계는 원래 자리에.** 이것이 Portal이다.
  - *Portal*: 콘텐츠의 DOM은 다른 컨테이너(보통 `body` 아래)에 붙이고, 프레임워크가 관리하는 부모-자식 관계는 원래 부모 아래에 유지하는 기능. React의 `createPortal(children, domNode)`가 대표 예다.
    - 흔한 오해: "Portal은 z-index를 쓰는 기능이다." — z-index만으로는 부모의 쌓임 맥락·`overflow`를 못 벗어난다. Portal은 DOM을 밖으로 빼서 피하고, z-index는 뺀 뒤 body 최상위에서 순서를 정할 때 쓴다.

쉬운 예: 파견 근무다.
- 자리(어느 건물·어느 층에 앉나)는 고객사다. 출입증·자리 배치·소방 동선은 고객사 건물 기준이다.
- 소속(누구에게 보고하나·월급·결재 라인)은 원 회사다. 원 회사 팀이 해체되면 파견도 같이 끝난다.

똑같은 구조다.\
자리 = DOM 트리, 소속 = 논리 트리다. "이 사람 몇 층에 있어?"는 건물에 묻고, "이 사람 누구 팀이야?"는 인사 시스템에 묻는다. 건물 출입 기록으로 소속을 판정하면 틀린다.

실무 예:
- 모달 안의 날짜 선택기·셀렉트 드롭다운·툴팁·자동완성 목록은 대개 Portal로 띄운다. 그런데 "바깥 클릭 시 닫기"를 DOM `contains`로 짜면 그 위젯을 누르는 순간 모달이 닫힌다.
- Portal 대신 별도 루트로 렌더한 "가짜 portal"은 겉보기엔 동작한다. Context를 읽거나 부모가 클릭을 받아야 하는 순간에야 깨진다(아래 실험).
- Portal로 띄운 모달 안의 키 입력이, 모달을 연 패널의 키 핸들러까지 올라가 가로채진다.

## 동작·원리

### 1. 트리가 두 개 — 노드 하나가 부모를 둘 가진다

```text
  논리 트리 (node.parent)                     DOM 트리 (el.parentNode)
  root                                        body
   └ card ◀── Context 'dark' 제공              ├ #app
      ├ inner-btn                              │  └ #root
      └ portal  ◀──── 같은 노드 ────▶          │     └ #card
         └ portal-btn                          │        └ #inner-btn
                                               └ #portal          ← portal 한 칸만 여기로
                                                  └ #portal-btn
```

- 프레임워크는 DOM과 별개로 컴포넌트의 트리를 들고 있다. 평소에는 두 트리의 모양이 같고, Portal은 둘을 일부러 가른다.
  - *DOM 트리*: 브라우저가 화면을 그리고 이벤트 경로를 계산하는 실제 요소 트리. `el.parentNode`로 올라간다. → [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md)
  - *논리 트리(컴포넌트 트리)*: 프레임워크가 상태·이벤트 핸들러·Context·수명을 관리하는 트리. React에서는 Fiber 트리다(부모 포인터 이름은 `return`). → [18-ui-rerender-and-memoization](../18-ui-rerender-and-memoization/2-summary.md)

아래는 두 트리를 동시에 들고 있는 최소 노드다. 논리 부모(`parent`)와 DOM 부모(`domParent`)를 따로 받는 것이 전부다.

```javascript
const elToNode = new WeakMap();                 // DOM 요소 → 논리 노드 (역방향 다리)

class Node {
  constructor(el, parent, domParent, handlers = {}) {
    this.el = el;                               // 이 노드가 소유한 DOM 요소
    this.parent = parent;                       // 논리 부모 (Node)
    this.handlers = handlers;                   // { click: fn } — 저장만 한다
    this.contexts = new Map();
    elToNode.set(el, this);
    domParent?.appendChild(el);                 // DOM 부모 (Element) — 여기서 갈라질 수 있다
  }
  inject(key, fallback) {                       // Context 조회: 논리 트리를 위로
    for (let n = this; n; n = n.parent) if (n.contexts.has(key)) return n.contexts.get(key);
    return fallback;
  }
}
```

- `parent`는 Node, `domParent`는 DOM 요소다. 타입부터 다르다.
- `domParent`는 "화면 전체를 그리는 큰 DOM"이 아니다. 이 노드의 `el`을 바로 아래에 붙일 요소 하나이고, 노드마다 다르다.

### 2. Portal = 한 칸에서만 갈라지는 것

```text
  만드는 함수                      parent(논리)    domParent(DOM)     결과
  createRoot(container)            없음            container          논리 트리의 시작
  createChild(parent)              parent          parent.el          두 트리 일치
  createPortal(parent, target)     parent          target(body 등)    두 트리 분리  ← 이게 Portal
  (가짜) createRoot(body)          없음            body               논리 트리가 새로 시작 ← 관계 끊김
```

```javascript
const div = () => document.createElement('div');
const listen = (container) => container.addEventListener('click', dispatch);   // dispatch는 3절

function createRoot(container) { const r = new Node(div(), null, container); listen(r.el); return r; }
function createChild(parent, handlers) { return new Node(div(), parent, parent.el, handlers); }
function createPortal(parent, target, handlers) {
  const p = new Node(div(), parent, target, handlers);   // 논리 부모는 parent, DOM 부모는 target
  listen(p.el);                                          // 왜 따로 다나 → 5절
  return p;
}
```

- portal 안의 내용은 다시 평범한 `createChild`다. 그래서 portal 컨테이너 아래에 차곡차곡 쌓인다. 위치가 바뀌는 것은 portal 한 칸뿐이다.
- 가짜 portal과 진짜 portal은 DOM 위치가 똑같다. 차이는 `parent`가 있느냐 하나다.

```text
  중첩 portal: portal#1 안에서 portal#2를 body로 연다
  DOM:   body ├ #portal1        ← #2는 #1의 DOM 형제 → 겹침 순서를 z-index로 정해야 한다
              └ #portal2
  논리:  card └ portal1 └ portal2   ← #2의 클릭은 #2 → #1 → card 로 올라가고, #1을 닫으면 #2도 정리
```

### 3. 이벤트는 두 단계 — 브라우저는 DOM으로 리스너만, dispatch가 논리로 핸들러

처음 떠올리기 쉬운 그림과 실제 그림이 다르다.

```text
  처음 그린 그림                                 실제 — 두 단계로 나뉜다
  브라우저 ─▶ DOM을 타며                          [단계 1] 브라우저 (DOM 경로만 안다)
            "이 버튼을 어떻게 처리할지" 탐색        클릭된 요소 → 부모 → … → document
            → 버튼의 onClick 실행                   경로 위에서 addEventListener된 "리스너"만 호출
                                                    ── 처리 방법(핸들러)을 찾지 않는다 ──
                                                              │
                                                              ▼ 그 리스너 = 컨테이너의 dispatch
                                                  [단계 2] dispatch (프레임워크 코드, 논리 트리)
                                                    target → 시작 노드 찾기 → n.parent 따라 핸들러 실행
```

- 브라우저는 컴포넌트 트리를 모른다. 이벤트 경로는 디스패치 시작 때 DOM 구조로 정해진다(WHATWG DOM "Dispatching events"). 그래서 DOM상 다른 곳에 있는 portal은 경로가 완전히 다르다.
- 프레임워크의 핸들러(`onClick`)는 DOM 요소에 달려 있지 않다. 노드 객체에 저장만 되어 있다.

**등록이 두 종류다.** 이 구분이 위임 전체를 푸는 열쇠다.

```text
                     무엇을             어디에                         언제
  브라우저 리스너     dispatch 함수       루트·portal 컨테이너 "요소"     루트 생성 때 1번, portal 열 때마다
   (addEventListener)
  프레임워크 핸들러   on의 함수          노드 "객체"의 handlers 필드     노드를 만들 때마다
   (저장만)

  <button> 자체에는 브라우저 리스너가 하나도 없다.
```

  - *이벤트 위임*: 요소마다 리스너를 달지 않고 조상 컨테이너 하나에 달아, 버블해 올라온 이벤트를 받아 나눠 주는 방식. 일반 원리는 [04 §4 위임](../04-dom-and-event-model/2-summary.md)에 있고, 여기서는 "나눠 주는 기준이 DOM이 아니라 논리 트리"인 점만 다룬다.
    - 흔한 오해: "`on: { click }`을 넘기면 그 버튼에 클릭 리스너가 등록된다." — 노드 객체에 함수가 저장될 뿐이다. 브라우저에 등록되는 것은 컨테이너의 `dispatch` 하나다.

```javascript
const seen = new WeakSet();                     // 이벤트 객체 단위 중복 방지 (5절)

function nodeOf(el) {                           // DOM → 논리로 건너가는 다리
  for (let cur = el; cur; cur = cur.parentNode) {
    const n = elToNode.get(cur);
    if (n) return n;                            // 처음 만나는 등록 요소의 노드
  }
  return null;
}

function dispatch(native) {                     // 브라우저 입장에서는 평범한 리스너 하나
  if (seen.has(native)) return;
  seen.add(native);
  for (let n = nodeOf(native.target); n; n = n.parent) {   // DOM 부모가 아니라 논리 부모
    n.handlers[native.type]?.(native);
  }
}
```

```text
  브라우저 ──호출──▶ dispatch(native)                  ← "교환원": 브라우저와 논리 트리 사이
                       │
                       ├ nodeOf(native.target)        어느 노드에서 일어났나 (DOM을 탄다 — 출발점 찾을 때만)
                       └ for (n = start; n; n = n.parent)
                           n.handlers[native.type]    저장해 둔 함수를 꺼내 실행 (논리 트리를 탄다)
```

- `nodeOf`가 DOM을 타는 이유: `target`이 등록하지 않은 안쪽 요소(아이콘 `span`, 텍스트 노드)일 수 있다. 그래서 위로 올라가 처음 만나는 등록 요소에서 논리로 건너간다.
- `'click'` 문자열 하나가 세 곳을 잇는다 — 브라우저에 등록한 타입 목록, `handlers`의 key, 받은 `native.type`. 등록 목록에 없는 타입(예: 목록에 `mouseover`가 없는데 핸들러 key가 `mouseover`)은 dispatch가 불리지 않아 핸들러가 실행되지 않는다.

### 4. 네이티브 버블링은 "처리됐다"고 멈추지 않는다

```text
  처음 그린 그림                          실제
  button → card → #root ■                 button → card → #root → #app → body → document
                    (dispatch가 처리,                       ▲
                     여기서 멈춤)                    dispatch 실행 — 그래도 브라우저는 계속 올린다
```

- 리스너가 이벤트를 "처리했다"는 개념은 브라우저에 없다. 전파를 멈추는 것은 `stopPropagation()` 호출뿐이다(DOM 표준의 stop propagation flag).
- 그래서 dispatch가 핸들러를 다 돌린 뒤에도 `#app`·`document`에 단 네이티브 리스너가 이어서 불린다(아래 실험 (a)).
- 결과 하나: 모달을 "여는" 클릭이 그대로 `document`의 "바깥 클릭 닫기" 리스너까지 올라가, 열자마자 닫힐 수 있다(장애 5).

### 5. portal 컨테이너에도 리스너가 필요한 이유 — 그리고 두 번 받는 경우

```text
  portal이 루트 DOM 밖(body 직속)                    portal이 루트 DOM 안(형제 sidebar의 DOM 안)
  DOM 경로: btn → #portal → body → document          DOM 경로: btn → #portal2 → #sidebar → #root → #app → …
  #root의 dispatch: 경로에 없음 → 못 받음 ✗          #portal2의 dispatch ① 처리
  → portal 컨테이너에 dispatch를 따로 단다            #root의 dispatch    ② 같은 이벤트 객체 → seen → return
```

- 단계 1에서만 portal은 "루트 밖"이다. 단계 2에서는 card·root가 논리 조상이므로 그 핸들러는 정상 실행된다.
- 컨테이너가 겹치면(portal 대상이 루트 안) 같은 네이티브 이벤트 객체가 dispatch 리스너 두 곳에 도착한다. `WeakSet`에 이벤트 객체를 표시해 한 번만 처리한다.
    - 흔한 오해: "중복 방지 = 사용자가 두 번 클릭하면 한 번만 처리." — 클릭마다 브라우저가 새 이벤트 객체를 만든다(E1 ≠ E2). 막는 것은 클릭 한 번의 같은 객체가 리스너 두 곳에 오는 경우뿐이다. 연타를 하나로 묶는 것은 디바운스·스로틀(타이머)이다.
- DOM 조상인 `sidebar`의 핸들러는 불리지 않는다. 핸들러를 고르는 기준이 논리 트리이기 때문이다(아래 실험 (c)).

### 실험: 두 단계 처리 순서 — 일반 자식 · portal · 형제 DOM 안 portal · 가짜 portal

환경: 위 1~3절의 코드 그대로(`Node`·`nodeOf`·`dispatch`·`createRoot`·`createChild`·`createPortal`)를 jsdom에서 실행. `#app`·`document`에 네이티브 클릭 리스너를 따로 달아 단계 1을 기록하고, 각 노드의 `click` 핸들러가 단계 2를 기록한다. `card`가 `theme = 'dark'`를 제공한다. `el.dispatchEvent(new MouseEvent('click', { bubbles: true }))`로 클릭.

```text
  root ─┬ card (theme=dark) ─┬ inner-btn            (일반 자식)
        │                    ├ portal  → DOM: body   └ portal-btn
        │                    └ portal2 → DOM: #sidebar 안   └ portal2-btn
        └ sidebar
  fake-root (body에 만든 별도 루트) └ fake-btn
```

(실험, Node 20.19.6 · jsdom 29.1.1 · vitest 4.1.12, 2026-11-04 — 3회 같은 출력)

```text
== (a) 일반 자식 inner-btn 클릭
  DOM 경로  : #inner-btn → #card → #root → #app → body → html → document
  논리 경로 : inner-btn → card → root
  [단계1] 브라우저 → dispatch 리스너 (currentTarget=#root)
  [단계2] 핸들러 inner-btn
  [단계2] 핸들러 card
  [단계2] 핸들러 root
  [단계1] 브라우저 → 네이티브 리스너 #app
  [단계1] 브라우저 → 네이티브 리스너 document
== (b) portal(→body) 안 portal-btn 클릭
  DOM 경로  : #portal-btn → #portal → body → html → document
  논리 경로 : portal-btn → portal → card → root
  [단계1] 브라우저 → dispatch 리스너 (currentTarget=#portal)
  [단계2] 핸들러 portal-btn
  [단계2] 핸들러 portal
  [단계2] 핸들러 card
  [단계2] 핸들러 root
  [단계1] 브라우저 → 네이티브 리스너 document
== (c) portal(→sidebar DOM 안) 안 portal2-btn 클릭
  DOM 경로  : #portal2-btn → #portal2 → #sidebar → #root → #app → body → html → document
  논리 경로 : portal2-btn → portal2 → card → root
  [단계1] 브라우저 → dispatch 리스너 (currentTarget=#portal2)
  [단계2] 핸들러 portal2-btn
  [단계2] 핸들러 portal2
  [단계2] 핸들러 card
  [단계2] 핸들러 root
  [단계1] 브라우저 → dispatch 리스너 (currentTarget=#root)
          이미 처리한 이벤트 → return
  [단계1] 브라우저 → 네이티브 리스너 #app
  [단계1] 브라우저 → 네이티브 리스너 document
== (d) 가짜 portal(별도 루트) 안 fake-btn 클릭
  DOM 경로  : #fake-btn → #fake-root → body → html → document
  논리 경로 : fake-btn → fake-root
  [단계1] 브라우저 → dispatch 리스너 (currentTarget=#fake-root)
  [단계2] 핸들러 fake-btn
  [단계1] 브라우저 → 네이티브 리스너 document
== Context: inject("theme", "light")
  portal-btn  → dark
  portal2-btn → dark
  fake-btn    → light
== "card 안쪽인가?" — DOM contains vs 논리 조상
  inner-btn   card.el.contains=true  논리 조상=true
  portal-btn  card.el.contains=false 논리 조상=true
  portal2-btn card.el.contains=false 논리 조상=true
  fake-btn    card.el.contains=false 논리 조상=false
== 트리 순서(querySelectorAll 순서 = 기본 Tab 순서의 바탕)
  inner-btn, portal2-btn, portal-btn, fake-btn
```

- (a) 단계 2의 핸들러 세 개가 단계 1의 `#app`·`document` 리스너보다 먼저다. 핸들러는 `#root`의 dispatch 안에서 돌고, `#root`가 `#app`보다 DOM상 안쪽이기 때문이다. dispatch가 다 처리한 뒤에도 네이티브 버블링은 계속됐다(4절).
- (b) DOM 경로에 `#card`·`#root`·`#app`이 없다. 그래서 `#app` 네이티브 리스너는 안 불렸다. 그런데 card·root 핸들러는 불렸다. 단계 1과 단계 2의 답이 다르다.
- (c) DOM 경로에는 `#sidebar`가 있는데 `sidebar` 핸들러는 안 불렸다. 논리 경로에 sidebar가 없기 때문이다. dispatch 리스너는 두 번 불렸고 처리는 한 번이었다(5절).
- (d) DOM 위치는 (b)와 같은 body 아래다. 그런데 card 핸들러에 닿지 않았고 Context는 기본값 `light`였다. 끊긴 것은 DOM이 아니라 논리 트리다.
- 마지막 두 블록은 7절의 근거다. `contains`는 DOM 질문의 답, 논리 조상은 관계 질문의 답이다. 트리 순서에서 `portal2-btn`이 `portal-btn`보다 앞인 것도 DOM 위치(sidebar 안 vs body 끝) 때문이다.

### 6. Context와 수명도 논리 트리를 탄다

```text
  inject('theme') — 논리 트리를 위로만               destroy(card) — 논리 자식을 먼저, 재귀로
  portal-btn → portal → card ✓ 'dark'                card.destroy()
  (DOM 부모 body는 보지 않는다)                        ├ inner-btn.destroy()
                                                       └ portal.destroy()      ← DOM은 body에 있어도 같이 정리
  fake-btn → fake-root → (끝) → fallback 'light'          └ portal-btn.destroy()
                                                       → 자기 정리(리스너 해제 등) → el.remove()
                                                     가짜 portal: card를 없애도 fake-root는 남는다
```

- Context는 "가장 가까운 논리 조상의 제공값"이다. DOM 조상이 무엇이든 상관없다.
- 수명: 부모가 사라지면 논리 자식도 사라진다. portal의 DOM이 body에 있어도 부모와 함께 정리된다.
- 정리 순서: 자식 목록은 추가 순서로 돌지만 재귀(깊이 우선)라서 결과적으로 맨 아래부터 끝난다(후위 순회). 자식 정리 → 자기 정리 순서라서 각 노드는 자기 정리만 책임진다.
- React의 가짜 portal은 별도 루트를 언마운트할 시점을 직접 관리해야 한다. 부모 루트의 커밋 도중(effect cleanup 안)에 다른 루트를 동기로 `unmount`하면 React가 경고하므로, 흔히 다음 틱으로 미룬다. 진짜 portal은 같은 트리라서 부모와 함께 정리된다.

### 7. 질문의 성격이 트리를 고른다 — 위치 vs 관계

```text
  처음 그린 그림: "DOM이 클릭을 돌 때 portal에 물어서 생긴 문제"
  실제: 이벤트가 어디로 가느냐는 같았다. document 리스너는 어느 쪽이든 같은 e.target을 받는다.
        다른 것은 받은 "다음의 판정 한 줄"이다.

  질문: "이 메뉴 항목이 모달 안쪽인가?"      ← 관계에 대한 질문
  엘리먼트에게 물음  dialog.el.contains(t)        노드에게 물음  n = n.parent 루프
    .modal 아래 DOM 자식을 뒤짐                     메뉴 항목 → menu(portal) → 메뉴 열기 버튼
    메뉴는 body 쪽 다른 portal에 있음                 → dialog ✓ 만남
    → 없음 → "바깥" ✗ → 모달이 닫힘                → "안쪽" ✓
```

- **엘리먼트에게 물으면 DOM만 안다.** `el.contains`·`el.closest`·`el.parentNode`는 DOM 관계만 따라간다. 관계를 알려면 노드(논리 트리)에게 물어야 한다.

```text
              질문이 "위치"에 관한 것인가, "관계"에 관한 것인가?
                    │                                     │
                  위치                                   관계
   화면 어디 그려지나 · CSS 상속·선택자 ·        누구의 자식인가 · 이벤트를 어느 핸들러가 받나 ·
   쌓임·잘림 · Tab 순서 · 네이티브 이벤트 경로    Context는 어디서 오나 · 언마운트 때 같이 정리되나 ·
                    │                           "이 위젯의 안쪽인가"
                DOM 트리                                논리 트리
```

- 같은 "안쪽인가"라도 무엇의 안쪽인지에 따라 묻는 트리가 다르다.
  - "모달에 속하는 클릭인가(닫을까 말까)" → 관계 → 논리 트리.
  - "Tab을 누르면 다음에 어디로 가나" → 위치·순서 → DOM 트리. 브라우저의 순차 포커스 이동 기본 순서는 tabindex가 같은 요소끼리 문서의 트리 순서를 따른다(HTML 표준 "sequential focus navigation"). 그래서 body 끝의 portal 모달은 Tab 순서상 맨 뒤다 — 모달의 포커스 가두기가 필요한 이유다.
  - "CSS가 걸리나" → 위치 → DOM 트리. portal 안 요소에는 DOM 부모의 상속 글꼴·하위 선택자(`.card .btn`)가 적용되지 않는다.

### 8. React에서: `createPortal` vs `createRoot`(가짜 portal)

```text
  진짜 — createPortal(children, target)            가짜 — createRoot(el).render(children)
  React 트리 (하나)                                React 트리 A           React 트리 B (새 루트)
  Provider(dark)                                   Provider(dark)         Content  ← 부모 없음
   └ div#card (onClick)                             └ div#card (onClick)
      └ (portal) └ Content  ← 부모 체인 유지            └ FakePortal (null 렌더)
  DOM: Content는 #target 아래                      DOM: Content는 #target 아래 — 같음
```

- react.dev `createPortal` 문서: portal은 DOM 노드의 물리적 위치만 바꾸고, 그 밖의 면에서는 렌더한 컴포넌트의 자식처럼 동작한다(부모의 Context 접근, React 트리를 따른 이벤트 버블).
- React 17부터 React의 네이티브 리스너는 `document`가 아니라 루트 컨테이너(`createRoot`에 넘긴 요소)에 단다(React 17 릴리스 노트). portal 컨테이너가 루트 밖이면 그 컨테이너에도 리스너가 필요하다 — 2·5절의 `listen(p.el)`과 같은 구조다.
  - *합성 이벤트(SyntheticEvent)*: React가 네이티브 이벤트를 감싸 만든 객체. React 트리를 따라 핸들러에 전달되고, 원본은 `e.nativeEvent`다.

| 개념 | 위 최소 코드 | React |
|---|---|---|
| 논리 부모 | `node.parent` | Fiber `return` |
| DOM과 논리 분리 | `new Node(el, parent, target)` | `createPortal(children, container)` |
| Context 조회 | `inject` — `n.parent`로 위로 | `useContext` — Fiber 조상의 Provider |
| 위임 리스너 | 루트·portal 컨테이너의 `dispatch` | 루트(·portal) 컨테이너의 React 리스너 |
| 논리 버블링 | `for (n…; n = n.parent)` | 합성 이벤트를 Fiber 트리로 전파 |
| "가짜 portal" 실수 | DOM만 `appendChild` / 별도 루트 | 별도 `createRoot` |

### 실험: React `createPortal` vs `createRoot`

환경: `Theme` Context(기본값 `light`)의 Provider가 `dark`를 주고, 그 안의 `div#card`에 `onClick`. 카드 아래에 버튼 다섯 개 — `inner`(일반 자식), `real`(`createPortal` → `#target`), `in-sibling`(`createPortal` → 카드의 React 형제 `div#sidebar`의 DOM 안, sidebar에도 `onClick`), `real-stop`(`createPortal`, 자기 `onClick`에서 `e.stopPropagation()`), `fake`(`useEffect` 안에서 `createRoot(el).render`). `#card`와 `document`에 네이티브 리스너. `act()` 안에서 `dispatchEvent(new MouseEvent('click', { bubbles: true }))`.

(실험, Node 20.19.6 · jsdom 29.1.1 · vitest 4.1.12 · react 19.3.1, 2026-11-04 — 3회 같은 출력)

```text
== inner 클릭   card.contains=true   DOM: #inner → #card → #app → body → html
  네이티브 #card 리스너
  React onClick inner (theme=dark)
  React onClick card (React 부모)
  네이티브 document 리스너
== real 클릭   card.contains=false   DOM: #real → #target → body → html
  React onClick real (theme=dark)
  React onClick card (React 부모)
  네이티브 document 리스너
== in-sibling 클릭   card.contains=false   DOM: #in-sibling → #sidebar → #app → body → html
  React onClick in-sibling (theme=dark)
  React onClick card (React 부모)
  네이티브 document 리스너
== real-stop 클릭   card.contains=false   DOM: #real-stop → #target → body → html
  React onClick real-stop (theme=dark)
== fake 클릭   card.contains=false   DOM: #fake → div → #target → body → html
  React onClick fake (theme=light)
  네이티브 document 리스너
```

- `inner`: 네이티브 `#card` 리스너가 React `onClick`보다 먼저 불렸다. React 핸들러는 루트 컨테이너 `#app`의 리스너 안에서 돌고, `#card`는 `#app`보다 DOM상 안쪽이기 때문이다 — 단계 1 → 단계 2 구조가 React에서도 같다.
- `real`: DOM은 카드 밖인데 Context `dark`, 카드 `onClick` 호출. `real`의 DOM 경로에는 `#card`가 없어서 네이티브 `#card` 리스너는 안 불렸다.
- `in-sibling`: DOM 조상인 `#sidebar`의 `onClick`은 안 불리고, React 부모인 card의 `onClick`이 불렸다(위 미니 실험 (c)와 같은 결과).
- `real-stop`: React `e.stopPropagation()`이 카드 `onClick`을 막았고 네이티브 `document` 리스너도 안 불렸다. React가 원본 이벤트의 전파도 함께 멈춘 결과다(이 구성에서 관찰).
- `fake`: DOM 위치는 `real`과 같은 `#target` 아래인데 Context는 기본값 `light`, 카드 `onClick`은 없다. 자기 `onClick`은 동작한다 — 핸들러는 prop으로 직접 넘긴 함수라 트리와 무관하기 때문이다. 트리를 따라 찾는 것(Context·버블링·언마운트 연쇄)만 끊긴다. 그래서 이 실수는 겉보기엔 "대충 동작"한다.

## 쓰이는 자료구조·알고리즘

- **두 트리 노드 매핑 = `WeakMap` 역참조**(DOM 요소 → 논리 노드): 해시 맵 조회 O(1)(평균). 키가 약한 참조라 요소가 사라지면 항목도 GC 대상이 된다. → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [algorithm/12-hash-functions](../../algorithm/12-hash-functions/2-summary.md)
- **`nodeOf` = DOM 방향 부모 포인터 상향 탐색**: 처음 만나는 등록 요소까지 O(DOM 깊이). "출발점 찾기"에만 쓴다.
- **논리 부모 포인터 상향 탐색**: dispatch 루프·`inject`·"논리 조상인가" 판정이 모두 `n = n.parent` 같은 모양이다. 깊이 d에 O(d). 조상 판정은 LCA를 구하지 않고 한쪽에서 위로 올라가며 상대를 찾는 단순형이다.
- **수명 = 자식 집합 + 재귀 후위 순회**: 자식을 먼저 정리하고 자기를 정리한다. 순회 중 자식이 부모 목록에서 자기를 지우므로 복사본(`[...children]`)을 돈다. → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **이벤트 객체 단위 중복 표시 = `WeakSet`**: 같은 객체인지(참조 동일성)로 판정한다.
- **트리 순서 = 전위 깊이 우선 순회**: `querySelectorAll` 순서·기본 Tab 순서의 바탕. 논리 트리가 아니라 DOM 트리 위에서 정의된다. → [04 §1](../04-dom-and-event-model/2-summary.md)

## 적용 — 풀어나가는 법

1. **질문을 먼저 분류한다.** 코드가 무엇을 묻는지 한 문장으로 쓰고, 위치인지 관계인지 고른다(7절 그림). 판정 함수가 엘리먼트 API(`contains`·`closest`)인데 질문이 관계라면 의심한다.

2. **"바깥 클릭" 판정은 관계 질문이다 — 논리 트리에 묻는다.** 쉬운 예(최소 코드):

```javascript
function isLogicalDescendant(node, ancestor) {
  for (let n = node; n; n = n.parent) if (n === ancestor) return true;
  return false;
}
document.addEventListener('pointerdown', (e) => {
  const node = nodeOf(e.target);                      // 1) DOM → 논리로 건너가기
  if (node && isLogicalDescendant(node, dialog)) return;   // 2) 논리 트리에서 관계 확인
  closeDialog('outside');                             // nodeOf가 null(어떤 노드에도 속하지 않음)이면 바깥
});
```

   같은 구조의 React 실무 예: React에는 엘리먼트 → Fiber 역참조를 공개 API로 쓰기 어렵다. 대신 "이벤트가 React 트리로 버블한다"는 성질을 판정에 쓴다. 모달 루트에서 React 핸들러로 "안쪽" 표시를 남기고, `document` 리스너가 그 표시를 본다.

```jsx
function Modal({ onClose, children }) {
  const insideRef = useRef(false);
  useEffect(() => {
    const onDocDown = () => {
      if (!insideRef.current) onClose('outside');
      insideRef.current = false;                      // 다음 입력을 위해 초기화
    };
    document.addEventListener('pointerdown', onDocDown);
    return () => document.removeEventListener('pointerdown', onDocDown);
  }, [onClose]);
  // 모달 안의 portal 위젯(날짜 선택기 등) 클릭도 React 트리로 여기까지 버블한다
  return createPortal(
    <div onPointerDown={() => { insideRef.current = true; }}>{children}</div>,
    document.body,
  );
}
```

   - 이 방식은 React 핸들러가 `document` 네이티브 리스너보다 먼저 돈다는 순서에 기댄다. React 17+에서는 리스너가 루트(·portal) 컨테이너에 있어 성립한다(실험: React `onClick` → 네이티브 `document` 순). 순서는 테스트로 고정해 둔다.
   - 모달 안 위젯이 별도 루트로 렌더된다면(가짜 portal) React 트리로 버블하지 않으므로 이 표시도 남지 않는다. 그 위젯의 DOM 컨테이너를 "안쪽 영역"으로 따로 등록해야 한다.

3. **portal 안 이벤트가 부모 핸들러까지 올라가는 것은 의도된 동작이다.** 원하지 않으면:
   - 백스톱: portal 경계(콘텐츠 루트)에서 `stopPropagation()`. 단 네이티브 전파도 멈춰 `document` 리스너(분석 로깅 등)까지 못 받을 수 있다(실험 `real-stop`).
   - 구조적 해소: 모달을 그 부모 아래에서 렌더하지 않는다. 열림 상태를 상위(앱 루트의 레이어 컴포넌트·스토어)로 올려 루트 근처에서 렌더하면, 논리 조상 경로에서 그 패널이 빠진다. 실제 사례 → [issue/…/tree-position-semantics](../../../issue/typescript/react/tree-position-semantics/2-summary.md)

4. **가짜 portal 점검.** 증상(Context 기본값, 부모 `onClick` 없음, 부모 언마운트 뒤에도 남음) → 원리(논리 트리가 새로 시작) → 확인:
   - 코드: portal 자리에서 `createRoot`·`render`·`ReactDOM.render`·`appendChild`를 검색한다.
   - 테스트: portal 안에서 `useContext` 값이 Provider 값인지, 안쪽 클릭이 부모 `onClick`에 닿는지를 단언한다. 진짜 portal로 바꿨을 때 결과가 바뀌는지(변이 점검)로 테스트가 둘을 구분하는지 확인한다.

5. **직접 위임을 만들 때.** 루트 밖에 붙는 portal 컨테이너마다 리스너를 달고, 컨테이너가 겹칠 수 있으면 이벤트 객체 단위로 중복을 막는다(5절). 위임하는 이벤트 타입 목록과 핸들러 key가 어긋나면 경고를 낸다 — 조용히 안 불리는 것이 가장 찾기 어렵다.

## 장애 시나리오와 대처

### 1. 가짜 portal — Context가 기본값, 부모 `onClick` 미도달 (⚠ 커리큘럼)

- **현상**: 모달·툴팁 안에서 테마·로케일·권한이 기본값으로 보인다. 카드의 클릭 로깅이 모달 안 클릭만 빠진다. 카드를 닫아도 모달이 남는다.
- **보이는 형태**: 실험 `fake` — `theme=light`(Provider는 `dark`), 카드 `onClick` 없음. 자기 `onClick`은 동작해서 처음에는 안 보인다. Provider 밖 호출을 throw하게 만든 훅이라면 "Provider 없음" 에러로 드러난다.
- **원인**: Portal 대신 `createRoot(el).render(...)`로 별도 루트에 그렸다. DOM 위치는 같지만 논리 트리가 새로 시작돼 부모 체인이 없다.
- **대처**: `createPortal`로 바꾼다. 꼭 별도 루트가 필요하면(다른 앱·다른 문서) 필요한 Context를 그 루트에 다시 Provider로 감싸고, 수명을 명시적으로 묶는다(부모 정리 때 `unmount`, 커밋 중 동기 unmount 경고 회피).

### 2. portal 안 이벤트가 프레임워크 부모 핸들러까지 버블 (⚠ 커리큘럼)

- **현상**: 모달 안 버튼 클릭이 뒤의 카드 선택까지 바꾼다. 모달 입력란의 키가 모달을 연 패널의 단축키로 처리된다.
- **보이는 형태**: 실험 `real`·`in-sibling` — DOM은 카드 밖인데 카드 `onClick` 호출. DOM 조상(`sidebar`)이 아닌 React 부모가 받는다.
- **원인**: 프레임워크 이벤트는 논리 트리로 버블한다. 모달을 렌더한 컴포넌트가 논리 조상이다.
- **대처**: 의도된 동작임을 먼저 받아들인다. 막아야 하면 열림 상태를 상위로 올려 렌더 위치를 바꾸는 구조적 해소가 우선이고, portal 경계의 `stopPropagation`은 백스톱으로 둔다. 테스트에 대조군(모달 밖 키는 조상이 받는다)을 함께 둬, "아무것도 전파되지 않아서 통과"를 막는다.

### 3. DOM `contains`로 "안쪽" 판정 → portal 위젯 클릭을 바깥으로 오인 (⚠ 커리큘럼)

- **현상**: 모달 안의 날짜 선택기·드롭다운 항목을 누르면 모달이 닫힌다. 선택이 적용되지 않는다.
- **보이는 형태**: 바깥 클릭 핸들러의 닫힘 사유가 `outside`. 실험 — `portal-btn`·`portal2-btn`은 `card.el.contains=false`인데 논리 조상은 `true`.
- **원인**: "이 위젯의 안쪽인가"라는 관계 질문을 엘리먼트(DOM)에게 물었다. portal 위젯의 DOM은 body 끝에 있다. `closest('[data-keep-open]')`도 DOM을 타므로 같은 문제다.
- **대처**: 논리 트리로 판정한다(적용 2). 판정 기준을 DOM으로 바꾸면 실패하는 테스트("모달 안에서 연 portal 위젯 클릭 → 모달 유지")를 둔다.

### 4. 직접 만든 위임에서 portal 핸들러가 안 불리거나 두 번 불림

- **현상**: portal 안 버튼이 반응하지 않는다. 또는 portal을 루트 안 요소에 붙였더니 핸들러가 두 번씩 돈다.
- **보이는 형태**: 루트 밖 portal의 클릭에서 dispatch 로그가 없다. 루트 안 portal에서는 같은 클릭에 dispatch가 두 번(실험 (c): 두 번 도착).
- **원인**: 단계 1의 경로는 DOM 구조로 정해진다. 루트 밖 portal은 루트 리스너 경로에 없고, 루트 안 portal은 두 컨테이너의 경로에 모두 있다.
- **대처**: portal 컨테이너에 리스너를 달고, 이벤트 객체 단위 표시(`WeakSet`)로 한 번만 처리한다.

### 5. 여는 클릭이 `document`의 닫기 리스너까지 올라가 열자마자 닫힘

- **현상**: 메뉴 버튼을 누르면 메뉴가 깜빡이고 사라진다.
- **보이는 형태**: 열기 핸들러 → 같은 클릭으로 `document` "바깥 클릭" 리스너 → 닫기 순서의 로그.
- **원인**: 열기 핸들러가 실행되는 동안 `document`에 닫기 리스너가 등록된다. 같은 클릭의 네이티브 버블링은 "처리됐다"고 멈추지 않으므로, 버블 패스가 아직 `document`에 닿지 않았다면 방금 단 리스너까지 불린다(04 §2: 아직 invoke하지 않은 조상에 추가한 리스너는 같은 이벤트에서 불릴 수 있다).
- **대처**: 닫기 리스너를 다음 틱에 등록하거나, 열기와 닫기를 다른 이벤트(`pointerdown` vs `click`)로 나누거나, 판정에서 트리거 자신을 안쪽으로 친다.

## 핵심 문장

- 프레임워크는 DOM과 별개로 논리 트리를 들고 있고, Portal은 DOM 부모만 바꾸고 논리 부모는 그대로 둔다.
- 이벤트는 두 단계다: 브라우저는 DOM 경로로 등록된 리스너만 부르고, 그 리스너(dispatch)가 논리 트리를 따라 핸들러를 실행한다.
- 네이티브 버블링은 리스너가 처리했다고 멈추지 않는다 — 멈추는 것은 `stopPropagation()`뿐이다.
- Context·이벤트 핸들러·수명은 논리 트리를, 화면 위치·CSS·Tab 순서·네이티브 이벤트 경로는 DOM 트리를 따른다(실험: DOM 위치가 같은 진짜·가짜 portal의 Context가 `dark`·`light`로 갈렸다).
- 엘리먼트에게 물으면 DOM만 안다 — 위치 질문은 DOM에, 관계 질문은 노드(논리 트리)에 묻는다.

## 관련 주제·근거

- 선행
  - [25-stacking-context-and-containing-block](../25-stacking-context-and-containing-block/2-summary.md) — Portal이 피하려는 CSS 문제(쌓임 맥락·containing block·`overflow`)
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md) — 캡처·버블·위임·`stopPropagation`의 일반 원리(이 노트는 그 위에 논리 트리 단계를 얹는다)
  - [18-ui-rerender-and-memoization](../18-ui-rerender-and-memoization/2-summary.md) — 선언형 UI의 컴포넌트 트리와 재렌더
- 후속·연결
  - [27-modal-dialog-behavior](../27-modal-dialog-behavior/2-summary.md) — portal로 띄운 모달의 바깥 클릭을 논리 트리로 판정하기, 여는 클릭과 닫는 이벤트 분리, ESC 스택·Tab 가두기·스크롤 잠금
  - [11-accessibility-basics](../11-accessibility-basics/2-summary.md) — 포커스 순서와 모달 포커스 관리
  - [21-component-and-state-patterns](../21-component-and-state-patterns/2-summary.md) — 상태를 어디에 두나(열림 상태 승격)
  - 실전 사례: [issue/typescript/react/tree-position-semantics](../../../issue/typescript/react/tree-position-semantics/2-summary.md) — 조건부 래퍼 리마운트·Provider 밖 가지·portal 키 버블·중첩 portal 바깥 클릭
  - 자료구조: [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md), [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- 문서
  - react.dev "createPortal" <https://react.dev/reference/react-dom/createPortal> — portal은 DOM 노드의 물리적 위치만 바꾸고, Context 접근·이벤트 버블은 React 트리를 따른다
  - React 17 릴리스 노트(이벤트 위임 위치 변경: `document` → 루트 컨테이너) <https://legacy.reactjs.org/blog/2020/10/20/react-v17.html> — URL·날짜는 기억으로 적음 [?]
  - WHATWG DOM 표준 "Dispatching events" <https://dom.spec.whatwg.org/#dispatching-events> — 경로는 디스패치 시작 때 부모를 따라 계산, stop propagation flag
  - WHATWG HTML 표준 "sequential focus navigation" <https://html.spec.whatwg.org/multipage/interaction.html#sequential-focus-navigation> — 기본 Tab 순서의 바탕
- 실험 목록(Node 20.19.6 · jsdom 29.1.1 · vitest 4.1.12 · react 19.3.1, 2026-11-04, 각 3회 같은 출력)
  - 미니 두 트리(1~3절 코드): 일반 자식·portal(body)·portal(형제 DOM 안)·가짜 portal 클릭의 단계 1·2 순서, `inject` 결과, `contains` vs 논리 조상, 트리 순서
  - React `createPortal` vs `createRoot`: `useContext` 값, 카드 `onClick` 도달, 형제 DOM 안 portal, portal 안 `stopPropagation`, 네이티브 `#card`·`document` 리스너와의 순서
