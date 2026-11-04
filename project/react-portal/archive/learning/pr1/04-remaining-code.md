# 04. 남은 코드 — dispatch의 두 장치, layers, 테스트

> 01~03에서 안 본 부분. 줄 번호는 PR #1 기준.

---

## A. 중복 방지 `handled` (`src/events.js:9-13`)

```js
const handled = new WeakSet();

function dispatch(native) {
  if (handled.has(native)) return;   // 이미 처리한 이벤트면 무시
  handled.add(native);               // 처리했다고 표시
  ...
```

### 언제 같은 이벤트가 두 번 오나

**portal의 target이 루트 DOM 안에 있을 때.** 컨테이너 두 개가 같은 DOM 경로 위에 겹친다.

```js
createPortal(card, root.el);   // target = .mini-root (body가 아니라)
```
```
.mini-root        ← dispatch 리스너 ②
 ├ .card
 └ .mini-portal   ← dispatch 리스너 ①
    └ button      ← 클릭
```
브라우저는 버블 단계에서 경로의 리스너를 **전부** 부른다.
1. `.mini-portal`의 dispatch 호출 → `handled`에 없음 → 표시 후 처리 (card 핸들러 1회)
2. `.mini-root`의 dispatch 호출 → **같은 이벤트 객체** → `handled`에 있음 → 바로 return

`handled`가 없으면 2에서 논리 트리 루프가 한 번 더 돌아서 card 핸들러가 **두 번** 실행된다.

### 실제로 확인한 것 (변이 점검)

12행을 지우고 테스트를 돌리면:
```
× portal target이 루트 DOM 안이어도 핸들러는 한 번만 호출된다
× DOM 조상이지만 논리 조상이 아닌 컴포넌트의 핸들러는 호출되지 않는다
AssertionError: expected "vi.fn()" to be called 1 times, but got 2 times
```
두 번째 테스트도 portal을 다른 노드의 DOM 안에 넣기 때문에 같은 이유로 실패한다. 복구하면 17/17 통과.

### 오해 주의: "클릭 2번 → 1번 처리"가 아니다
사용자가 두 번 클릭하면 이벤트 객체가 두 개(E1, E2) 생기므로 **둘 다 처리된다.** 막는 건 **한 번의 클릭(같은 객체)이 리스너 두 곳에서 이중 처리되는 것**뿐이다. 연타 방지는 디바운스/스로틀이라는 별개 기법.

### 왜 WeakSet인가
- 이벤트 객체는 처리가 끝나면 필요 없다. 일반 Set이면 클릭할 때마다 쌓여서 영원히 남는다.
- WeakSet은 이벤트 객체가 쓰이지 않게 되면 같이 사라진다. → [memory-and-cleanup](../../frontend/memory-and-cleanup.md)

### 데모에서는 왜 안 보였나
데모의 portal은 전부 `target = body`라서 `.mini-root`와 경로가 겹치지 않는다. 이 장치는 **target을 앱 안으로 지정하는 경우**를 위한 것이다.

---

## B. 우리판 이벤트 객체 (합성 이벤트, `src/events.js:18-31`)

```js
let stopped = false;                 // 이 dispatch 한 번에만 쓰는 지역 변수
const event = {
  type: native.type,                 // 'click'
  nativeEvent: native,               // 원본 (필요하면 좌표 등 꺼내 쓰라고)
  target: start,                     // ← DOM 요소가 아니라 "노드"
  currentTarget: null,               // 루프에서 핸들러 실행 직전에 갱신
  stopPropagation() {
    stopped = true;                  // ① 우리 루프 중단
    native.stopPropagation();        // ② 브라우저 버블링도 중단
  },
  preventDefault() {
    native.preventDefault();         // 기본 동작 취소는 원본에 그대로 전달
  },
};
```

### 왜 네이티브 이벤트를 그대로 안 넘기나

| 네이티브 그대로 넘기면 | 감싸서 넘기면 |
|---|---|
| `e.target`이 DOM 요소 → 핸들러가 노드를 알려면 다시 찾아야 함 | `e.target`이 **노드** |
| `e.stopPropagation()`이 브라우저 버블링만 멈춤 → **우리 루프는 계속 돎** | `stopped = true`로 우리 루프도 멈춤 |
| `e.currentTarget`은 항상 컨테이너 | 지금 핸들러가 실행 중인 **노드** |

핵심은 두 번째 줄이다. 우리 루프(`for (n = start; n && !stopped; n = n.parent)`)는 브라우저가 아니라 우리가 돌리는 것이라서, 브라우저의 stopPropagation으로는 못 멈춘다. 그래서 `stopped` 플래그가 필요하다.

### stopped가 지역 변수인 이유
`dispatch`가 불릴 때마다 새로 생긴다 → 이번 클릭에서 멈춘 것이 다음 클릭에 영향을 주지 않는다. `stopPropagation` 메서드가 이 변수를 바꿀 수 있는 건 **클로저** 덕분이다(같은 함수 안에서 만들어진 메서드라서 바깥 변수에 접근 가능). → [closures](../../frontend/closures.md)

### currentTarget 갱신 (`events.js:37`)
```js
event.currentTarget = n;   // 핸들러 실행 직전에
handler(event);
```
같은 event 객체를 여러 핸들러가 차례로 받는다. 각자 "지금 내가 누구인지"를 `currentTarget`으로 알 수 있다.

### 데모에서 쓰는 곳
```js
card.handlers.click = (e) => {
  if (e.target === card) return;   // 카드 자체(빈 곳)를 클릭한 건 무시
  log('card 핸들러 (논리 부모)');
};
```
`e.target`이 노드라서 `=== card`처럼 **노드끼리 바로 비교**할 수 있다.

---

## C. 레이어 스택 (`src/layers.js`)

```js
export const BASE_Z = 1000;
const stack = [];                         // 열린 portal 컨테이너들 (열린 순서)

function restack() {                      // 배열 순서대로 z-index 다시 매기기
  stack.forEach((el, i) => {
    el.style.zIndex = String(BASE_Z + i); // 1000, 1001, 1002 …
  });
}

export function pushLayer(el) {           // 열 때 (portal.js)
  stack.push(el);                         // 맨 뒤 = 맨 위
  restack();
}

export function removeLayer(el) {         // 닫을 때 (portal 클린업)
  const i = stack.indexOf(el);
  if (i === -1) return;                   // 없으면 아무것도 안 함 (두 번 불려도 안전)
  stack.splice(i, 1);                     // 빼고
  restack();                              // 남은 것들 번호 다시
}

export function getLayers() {
  return [...stack];                      // 복사본을 줌 → 바깥에서 원본 배열을 못 건드림
}
```

### 동작 예
```
열기 A        stack [A]          A=1000
열기 B        stack [A, B]       A=1000 B=1001
열기 C        stack [A, B, C]    A=1000 B=1001 C=1002
B 닫기        stack [A, C]       A=1000 C=1001   ← restack으로 C가 내려옴 (순서는 유지)
열기 D        stack [A, C, D]    D=1002          ← 항상 맨 위
```

### 설계 포인트
- **배열 위치 = 쌓인 순서.** z-index 값을 따로 기억하지 않고 매번 위치로 다시 계산 → 값이 꼬일 일이 없다.
- **모듈 변수**: `stack`은 `export`하지 않는다. 바깥에서는 `pushLayer`/`removeLayer`로만 바꿀 수 있다(캡슐화). 읽기용 `getLayers`도 복사본을 준다.
- **페이지 전체에 하나**: 모듈은 한 번만 로드되므로 모든 portal이 같은 스택을 공유한다 → 전역 레이어 순서.
- **일반 배열이라 el을 붙잡는다**: 그래서 클린업의 `removeLayer`가 빠지면 닫은 모달이 메모리에 남는다.
- **BASE_Z = 1000**: 앱의 일반 요소(헤더 z-index 2 등)보다 확실히 위에 있도록 띄운 시작값.

### 설계상 한계 (알고 쓰기)
- 열린 순서만 본다. "이미 열린 모달을 클릭하면 맨 위로" 같은 재정렬은 없다.
- 모든 portal이 body 직속이라는 전제에서만 숫자 비교가 공정하다. target을 다른 stacking context 안으로 주면 그 안에서만 비교된다.

---

## D. 테스트 코드 읽는 법 (`test/`)

### 도구 (Vitest)
| 코드 | 뜻 |
|---|---|
| `describe('이름', () => {...})` | 테스트 묶음 |
| `test('이름', () => {...})` | 테스트 하나 |
| `expect(값).toBe(기대)` | 같은가 (`===`) |
| `expect(값).toEqual(기대)` | 내용이 같은가 (배열·객체) |
| `vi.fn()` | **가짜 함수(스파이)**. 몇 번, 무슨 인자로 불렸는지 기록 |
| `expect(spy).toHaveBeenCalledTimes(n)` | n번 불렸나 |
| `expect(spy).not.toHaveBeenCalled()` | 안 불렸나 |
| `afterEach(fn)` | 각 테스트가 끝날 때마다 실행 |

`vitest.config.js`의 `environment: 'jsdom'` → Node에서 가짜 브라우저(jsdom)를 띄워 `document`, `MouseEvent`를 쓸 수 있게 한다.

### 공통 준비와 뒷정리 (`test/portal-logical.test.js:5-18`)
```js
let root;
afterEach(() => {
  root?.destroy();              // ① 만든 트리 정리
  document.body.innerHTML = ''; // ② DOM 비우기
});

function mountRoot() { ... root = createRoot(app); return root; }

const click = (el) => el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
```
- **왜 `root.destroy()`가 필요한가**: 레이어 스택은 모듈 변수라 **테스트 간에 공유**된다. destroy로 portal을 닫지 않으면 이전 테스트의 portal이 스택에 남아서 다음 테스트의 z-index 기대값이 틀어진다. `body.innerHTML = ''`만으로는 스택이 안 비워진다.
- **`bubbles: true`**: 안 주면 이벤트가 버블링하지 않아서 컨테이너의 dispatch까지 못 간다 → 모든 이벤트 테스트가 실패한다. → [event-object](../../frontend/event-object.md#이벤트-직접-만들기)

### 테스트 = 불변식 증명
각 테스트는 "이게 깨지면 Portal이 아니다"라는 조건 하나를 확인한다.

| 불변식 | 대표 테스트 | 무엇으로 증명하나 |
|---|---|---|
| I1 DOM 이동 | `portal-dom.test.js` "DOM 부모는 target" | `portal.el.parentNode === body`, `card.el.contains(modal.el) === false` |
| I2 논리 버블링 | "DOM이 아닌 논리 부모 체인" | 핸들러가 기록한 순서 `['button','portal','card','root']` |
| I2 (날카로운 판) | "DOM 조상이지만 논리 조상이 아닌…" | portal을 **형제의 DOM 안에** 넣고, 형제 스파이가 **안 불림** |
| I3 stopPropagation | "호출한 지점 위의…" | 위쪽 스파이들이 `not.toHaveBeenCalled()` |
| I4 생명주기 | "논리 부모를 destroy하면…" | DOM 없음, 레이어 없음, **DOM을 억지로 다시 붙여도** 핸들러 안 불림 |
| I5 Context | "portal 경계를 넘어…" | `inject` 결과가 가장 가까운 논리 조상 값 |
| I6 레이어 | "나중에 연 portal의 z-index가 더 크다" | z-index 숫자 비교, 닫은 뒤 재정렬 |

### "DOM 조상이지만 논리 조상이 아닌" 테스트가 핵심인 이유
```js
const sibling = createNode(r, 'div', { on: { click: vi.fn() } });
const card    = createNode(r, 'div', { on: { click: vi.fn() } });
const portal  = createPortal(card, sibling.el);   // portal을 "형제" DOM 안으로
click(createNode(portal, 'button').el);

expect(card.handlers.click).toHaveBeenCalledTimes(1);   // 논리 부모 → 불림
expect(sibling.handlers.click).not.toHaveBeenCalled();  // DOM 부모 → 안 불림
```
- target이 body면 body는 노드가 아니라서, "DOM을 따랐는지 논리를 따랐는지" 구분이 안 된다.
- 형제 노드의 DOM 안에 넣으면 **DOM 조상(sibling) ≠ 논리 조상(card)** 상황이 만들어진다. 이 테스트만이 버블링이 DOM을 따르는지 논리를 따르는지 **판별**한다.

### 테스트가 진짜 결함을 잡는지 확인한 방법 (변이 점검)
테스트가 통과하는 것만으로는 부족하다. **일부러 코드를 망가뜨렸을 때 실패하는지** 봐야 테스트가 의미 있다.

| 망가뜨린 것 | 결과 |
|---|---|
| `n = n.parent` → `n = nodeOf(n.el.parentNode)` (DOM 기준 버블링) | I2 테스트 4개 실패 |
| `if (handled.has(native)) return;` 삭제 | 2개 실패 ("1번이어야 하는데 2번") |

둘 다 복구 후 17/17 통과.
