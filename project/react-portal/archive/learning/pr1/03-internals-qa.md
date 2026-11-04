# 03. 내부 동작 Q&A

> 코드 읽으며 실제로 했던 질문을 순서대로. "처음 생각"은 질문할 때의 이해, "정답"은 확인된 동작.

---

## Q1. Portal은 z-index를 활용하는 기능인가?

- **정답**: 아니다. z-index만으로는 못 푸는 문제(부모의 stacking context, overflow)를 **DOM을 body로 옮겨서** 피하는 기능이다. z-index는 옮긴 **다음에** body 최상위에서 순서를 정하는 데 쓴다.

## Q2. 순수 JS로 만들까, React 위에 만들까?

- **정답**: 순수 JS로 DOM만 body에 붙이면 Portal의 절반(DOM 이동)만 재현된다. 나머지 절반인 **논리 관계 유지**(이벤트 버블링·Context·생명주기)를 보려면 **미니 논리 트리**를 같이 만들어야 한다. React 위에 만들면 그 핵심을 React가 대신 해 버려서 원리가 안 보인다.

## Q3. `el`은 무엇의 약자인가?

- **정답**: element. 노드가 소유한 실제 DOM 요소. → [02 › el](02-concepts.md#el-element)

## Q4. 생성자는 무엇을 하나? (`src/node.js:8-28`)

- **처음 생각**: 핸들러는 `on` 빈 객체로 만들어지고, for문으로 타입을 검사하고, register로 등록하고, 부모의 자식으로 추가하고, domParent에 el을 붙인다. `on`은 맨 마지막 요소로 받는다.
- **정답**: 전부 맞고 한 가지만 보정. `on`은 "마지막 요소"가 아니라 **구조 분해로 이름으로 꺼내는 옵션**이다. `EVENT_TYPES`는 생성 시 받는 게 아니라 `events.js`에서 import한 고정 목록.

## Q5. cleanup은 어디에 쓰이나?

- **정답**: 노드가 destroy될 때 해야 할 뒷정리를 **미리 예약해 두는 함수 목록**. 사용처는 두 곳.
  - `root.js:10` — 루트 리스너 해제
  - `portal.js` — 레이어 제거(`removeLayer`), portal 리스너 해제
- 등록 역순(스택)으로 실행된다.

## Q6. `createElement`로 만든 요소도 어딘가에 등록되나?

- **정답**: 아니다. 메모리에만 존재하고 문서 트리에는 없다. `appendChild`해야 화면에 들어간다. 그래서 생성자 마지막 줄 `domParent.appendChild(el)`이 필요하다. → [02 › createElement vs appendChild](02-concepts.md#createelement-vs-appendchild)

## Q7. className, text는 엘리먼트에 주입하는 건가?

- **정답**: 맞다. 단 그 옵션은 `Node` 생성자가 아니라 **`createNode`**(`node.js:61-66`)에 있다.
  - `createNode`: 엘리먼트를 만들고 꾸미는 편의 함수 (tag, className, text)
  - `Node` 생성자: 이미 만든 el을 두 트리에 연결하는 것만 담당

## Q8. domParent는 화면 전체를 그리는 큰 DOM인가?

- **처음 생각**: 전체 JS 화면을 그리는 큰 DOM.
- **정답**: 아니다. **이 노드의 el을 바로 아래에 붙일 요소 하나**이고, 노드마다 다르다. root는 `#app`, 일반 노드는 `parent.el`, portal은 `body`. 한 칸씩 붙어서 결과적으로 큰 트리가 된다.

## Q9. destroy·cleanup·inject의 동작, 그리고 portal 안 모달의 부모는?

- **처음 생각**:
  - destroy는 역순으로 하나씩, 맨 아래 자식부터 제거
  - 클린업은 큐 형태로 하나씩 꺼내 실행
  - inject는 상위 돔이나 하위 돔을 타고 간다
  - 모달의 DOM 부모는 `.mini-portal`, 논리 부모는 app 안의 컴포넌트
- **정답**:
  - destroy — 자식은 **추가 순서대로** 돌지만 **재귀**라서 결과적으로 맨 아래부터 끝난다.
  - 클린업 — 큐가 아니라 **스택**(`.reverse()`).
  - inject — DOM이 아니라 **논리 트리**를, **위로만**.
  - 모달 — DOM 부모는 맞다(`.mini-portal` 안). 논리 부모는 직접적으로는 `overlay`이고, 거슬러 올라가면 `portal → card → root`. card는 **조상**이지 직접 부모가 아니다.

## Q10. portal 안에서 portal을 또 열면, 2번째의 실제(DOM) 부모도 body인가?

- **정답**: 그렇다. `createPortal(portal#1, document.body)`이므로 #2도 **body 직속**, #1의 **형제**다. 논리 부모만 #1. 그래서 둘의 순서를 z-index(1000, 1001)로 정한다.

## Q11. 자식 destroy 후 자기 클린업을 도는 순서에 이유가 있나? 객체가 삭제되면 클린업이 자동으로 돌지 않나?

- **처음 생각**: 삭제되면서 자동으로 돌 텐데… → 아, 자식을 먼저 삭제하면 결국 자기 자신에 대한 클린업만 남는구나. 그리고 레이어 삭제를 portal 생성 시 넣어 둠으로써 역할 전달을 생성이 담당한다.
- **정답**:
  - JS에는 소멸자가 없다. 자동으로 돌지 않고 `destroy()`를 **명시적으로** 불러야 한다(데모에선 닫기 버튼).
  - 순서 이유는 스스로 도달한 결론 그대로 — 각 노드는 자기 클린업만 책임진다.
  - "생성이 해제를 담당" = **획득한 쪽이 해제도 예약한다**(RAII 발상).
  - `[...this.children]` 복사본을 도는 이유: 자식 destroy가 부모의 `children`에서 자기를 지우므로.

## Q12. `listen(el)`의 역할은?

- **정답**: 컨테이너에 `dispatch`를 브라우저 리스너로 달고, **떼는 함수를 돌려준다.** 그 해제 함수가 곧바로 클린업에 들어간다(`portal.onCleanup(listen(el))`).

## Q13. app 밖의 DOM이라서, mini-portal에서 일어난 이벤트를 app이 받아 실행할 수 없다는 말인가?

- **정답**: **단계를 나누면** 반은 맞다.
  - 단계 1(브라우저, DOM 경로): 맞다. `.mini-root`는 경로에 없어서 그 리스너는 이 클릭을 모른다. → 그래서 portal에 `listen`이 따로 필요.
  - 단계 2(dispatch, 논리 경로): 아니다. card·root 핸들러는 정상 실행된다.
  - 증거: 데모에서 card·root 로그는 찍히고, `#app`에 직접 단 `[네이티브]` 로그만 안 찍힌다.

## Q14. "이벤트가 정의된 걸 DOM 트리를 따라 찾는다"가 대전제 1인가?

- **처음 생각**: 브라우저가 DOM 트리를 따라 버튼 클릭 시 어떻게 처리할지 이벤트를 찾는다.
- **정답**: "어떻게 처리할지 찾는" 건 단계 2의 일이다. 우리 핸들러는 **DOM에 달려 있지 않다**(노드 객체에 저장). 정확한 대전제는:
  1. 브라우저는 클릭된 요소부터 DOM을 따라 올라가며 **`addEventListener`된 리스너를 호출할 뿐**이다. 그 경로의 리스너는 컨테이너의 `dispatch` 하나뿐.
  2. `dispatch`가 `nodeOf(target)`으로 시작 노드를 찾고, 논리 부모를 따라 `handlers.click`을 실행한다.

## Q15. React는 최상위 DOM에 리스너를 등록한다는데, dispatch는 뭔가?

- **정답**: `events.js:11`에 우리가 직접 만든 함수이자, **브라우저에 등록되는 그 리스너 자체**. 하는 일:
  1. 중복 방지 (`handled`)
  2. `nodeOf(native.target)`로 시작 노드 찾기
  3. 우리판 이벤트 객체(합성 이벤트) 만들기
  4. `n = n.parent`로 올라가며 핸들러 실행
- React의 "최상위"는 `document`가 아니라 **`createRoot`에 준 루트 컨테이너**(17+).

## Q16. "Portal 모달 열기"와 "닫기"를 누르면 이벤트가 어떻게 전달되나?

**열기** (버튼은 `#app` 안):
```
브라우저: button → .actions → .card → .mini-root(dispatch!) 
dispatch: nodeOf → 열기 버튼 노드 → handlers.click 실행 (main.js:99)
  stopPropagation → 루프·브라우저 버블링 중단 (#app 로그 안 찍힘)
  openPortalModal(card)
    createPortal → .mini-portal을 body에 붙임, z=1000, listen(el)로 dispatch 부착
    buildModal + 버튼 3개 createNode (핸들러는 노드에 저장)
```

**닫기** (버튼은 `.mini-portal` 안):
```
브라우저: button → .actions → .modal → .overlay → .mini-portal(dispatch!)
          (#app·.mini-root는 경로에 없음)
dispatch: nodeOf → 닫기 버튼 노드 → handlers.click 실행 (main.js:85)
  stopPropagation → portal.destroy()
    [1] 자식 재귀 destroy (overlay → modal → h3, meta, row → 버튼들)
    [2] 자기 클린업 역순: 리스너 해제 → removeLayer
    [3] unregister  [4] card.children에서 빠짐  [5] el.remove() → 화면에서 사라짐
```

- 공통 흐름: **DOM을 따라 올라가다 처음 만나는 dispatch → 클릭된 노드 찾기 → 논리 부모 방향으로 핸들러 실행.** 다른 건 "어느 컨테이너의 dispatch냐"뿐.

## Q17. root에 dispatch가 있다는 건 어디서 아나? `createNode(... on: { click })`에서 등록되는 건가?

- **정답**: `addEventListener`를 검색하면 dispatch를 다는 곳은 `events.js:45`(listen 안) **하나뿐**이고, listen을 부르는 곳은 `root.js:10`, `portal.js:19` **두 곳뿐**.
  - root: `main.js:20`의 `createRoot(app)`에서 페이지 시작 시 등록.
  - `createNode`의 `on`은 브라우저 등록이 아니라 `node.js:12`에서 **노드 객체에 저장만** 한다.

## Q18. root와 portal은 main에 의해 1번 생성되나?

- **정답**: root는 맞다(로드 시 1번). **portal은 로드 시 0개**. `createPortal`은 `openPortalModal` 안에만 있고, 열기 버튼·"또 열기"를 누를 때마다 새로 생긴다.

| 시점 | dispatch 리스너 |
|---|---|
| 로드 직후 | `.mini-root` |
| Portal 모달 열기 후 | + #1 |
| 모달 위에 또 열기 후 | + #2 |
| #1 닫기 후 | `.mini-root`만 |

## Q19. 포탈을 열 때 mini-portal에 리스너를 등록하는 코드는 main.js 어디에 있나?

- **정답**: main.js에는 **안 보인다.** `createPortal` 안(`portal.js:19`의 `portal.onCleanup(listen(el))`)에 숨어 있다. 쓰는 쪽은 `createPortal`만 부르면 된다.
- 주의: `createPortal(…, { on: { click } })`의 `on`은 리스너 등록이 아니라 **portal 노드의 핸들러 저장**이다(로그의 `portal#1 핸들러`).

## Q20. EVENT_TYPES를 가져와 붙이고, 동작은 on 안에 key로 매핑, dispatch가 클릭 이벤트를 받았으니 그 key의 핸들러를 실행하는 것인가?

- **정답**: 정확하다. `'click'` 문자열 하나가 세 곳을 잇는다.
```js
EVENT_TYPES = ['click', …]           // ① 브라우저에 등록할 목록 (events.js:5)
on: { click: fn }                    // ② key로 동작 매핑 → node.handlers (node.js:12)
n.handlers[native.type]              // ③ 받은 타입 이름으로 꺼내 실행 (events.js:35)
```
- ①과 ②의 이름이 안 맞으면(예: `mouseover`) dispatch가 불리지 않아 영영 실행 안 됨 → 생성자 경고가 이걸 잡는다.

## Q21. native 객체란? 그 target은?

- **정답**: `native` = 브라우저가 리스너에 넣어 주는 **진짜 이벤트 객체**(이름은 우리 합성 이벤트와 구분하려고 붙인 것). `native.target` = **실제로 클릭된 가장 안쪽 DOM 요소**, `native.currentTarget` = 리스너가 달린 컨테이너. → [02 › Event 객체](02-concepts.md#event-객체-native)
- `nodeOf`가 DOM을 타고 올라가는 이유: target이 우리가 등록 안 한 안쪽 요소(아이콘 span 등)일 수 있어서 → 처음 만나는 등록 요소의 노드를 시작점으로.
  - nodeOf: DOM을 타서 **시작 노드 하나**를 찾음
  - dispatch 루프: 그 시작 노드부터 **논리 트리**를 탐
- 확인법: dispatch 첫 줄에 `console.log(native.type, native.target, native.currentTarget)` → 콘솔 확인 후 삭제.

## Q22. 클로저·WeakSet은 객체를 포인터로 가져오는 게 아니라 데이터를 그대로 복사해서 넣는 것 아닌가?

- **정답**: 아니다. 둘 다 **참조**를 들고 있다.
  - 클로저는 값을 찍어 두는 게 아니라 **변수 자체**를 가리킨다 → `stopPropagation()`이 바꾼 `stopped`를 루프가 본다.
  - 객체는 변수에 넣거나 넘길 때 **참조값**이 전달된다 → 닫기 버튼의 클로저가 **진짜 그 portal 노드**를 destroy한다.
  - WeakSet `has`는 **같은 객체인가**로 판정한다.
- 복사는 `{ ...on }`, `[...children]`처럼 **명시적으로** 할 때만이고, 그것도 얕은 복사다. → [reference-vs-copy](../../frontend/reference-vs-copy.md)

## Q23. 중복 방지(`handled`)는 native에 클릭이 2번 들어오면 1번만 처리한다는 뜻인가?

- **처음 생각**: 클릭이 두 번 들어오면 한 번만 처리.
- **정답**: 아니다. **사용자가 두 번 클릭하면 두 번 다 처리된다.** 클릭마다 브라우저가 새 이벤트 객체를 만들기 때문(E1 ≠ E2).
  - 막는 것은 **클릭 한 번의 같은 이벤트 객체가 dispatch 리스너 두 곳에 도착하는 경우**(portal target이 루트 안 → `.mini-portal`과 `.mini-root`가 같은 경로).
```
클릭 1번 → E1 → dispatch ①(.mini-portal): 표시 후 처리
              → dispatch ②(.mini-root)  : 같은 E1 → return
```
- "짧은 시간 연타를 한 번으로"는 별개 기법인 **디바운스/스로틀**(타이머 기반).
