# 02. 몰랐던 개념 사전

> 대화 중 처음 나오거나 헷갈렸던 개념. 이 프로젝트 코드의 어디서 쓰이는지 같이 적었다.

## DOM

### el (element)
- **element의 약자.** `document.createElement('div')`가 돌려주는 실제 DOM 요소(`HTMLElement`).
- 프런트엔드에서 관례적으로 쓰는 이름(Vue `$el` 등).
- 코드: `node.el` — 노드가 소유한 DOM 요소.

### createElement vs appendChild
- `document.createElement(tag)` — 요소를 **메모리에만** 만든다. 화면에 없고 부모도 없다(`el.parentNode === null`).
- `parent.appendChild(el)` — 이 순간 DOM 트리에 들어가 화면에 그려진다.
- `el.remove()` — DOM 트리에서 떼어낸다. 아무도 참조하지 않으면 GC가 회수.
- **만드는 것과 붙이는 곳이 별개** → 같은 요소를 카드 안에도, body에도 붙일 수 있다. Portal이 가능한 이유.
- 코드: `node.js:27` (`domParent.appendChild(el)`), `node.js:56` (`this.el.remove()`).

### DOM 트리 vs 논리 트리
- DOM 트리: 브라우저가 화면 배치에 쓰는 실제 요소 구조(`el.parentNode`).
- 논리 트리: 우리가 만든 컴포넌트 관계(`node.parent`). React에서는 Fiber 트리.
- 보통은 같고, Portal에서만 갈라진다.

### textContent vs innerHTML
- `textContent` — 문자열을 **글자 그대로** 넣는다. `'<b>hi</b>'`도 태그가 아니라 글자로 표시 → 안전.
- `innerHTML` — 문자열을 HTML로 해석한다.
- 코드: `node.js:64`.

## 이벤트

### 이벤트 버블링 (네이티브)
- 브라우저는 클릭된 요소에서 시작해 **DOM 부모 방향으로** 이벤트를 올려 보내며, 경로에 등록된 리스너를 호출한다.
- 브라우저는 **DOM만 안다.** 우리 논리 트리는 모른다.

### addEventListener — 리스너 vs 핸들러
- `el.addEventListener('click', fn)` — **브라우저에** "이 요소에서 click이 오면 fn을 불러 줘"라고 등록. 이게 **리스너**.
- 이 프로젝트에서 리스너는 `dispatch` 하나뿐이고 컨테이너에만 달린다(`events.js:45`).
- `on: { click: fn }`의 fn은 리스너가 아니라 노드 객체에 저장된 **핸들러**. dispatch가 꺼내서 실행한다.

### 이벤트 위임 (event delegation)
- 버튼마다 리스너를 달지 않고, **상위 컨테이너 하나**에 리스너를 달아 하위 이벤트를 대신 받아 나눠 주는 방식.
- React가 이렇게 동작한다. React 컴포넌트의 `onClick`도 실제 `<button>`에 달려 있지 않다.
- React 16까지는 `document`에, **17부터는 루트 컨테이너**(`createRoot`에 준 요소)에 단다. 한 페이지에 React 앱이 여러 개일 때 서로 간섭하는 문제 때문에 바뀌었다. portal 컨테이너에도 따로 단다.

### Event 객체 (native)
리스너가 호출될 때 브라우저가 첫 번째 인자로 넣어 주는 객체. 클릭이면 `MouseEvent`, 키 입력이면 `KeyboardEvent`.

| 속성 | 뜻 |
|---|---|
| `type` | 이벤트 종류 (`'click'`) |
| `target` | **이벤트가 실제로 일어난** 가장 안쪽 요소 |
| `currentTarget` | 지금 실행 중인 리스너가 **달린** 요소 |
| `clientX/Y` | 마우스 좌표 |
| `stopPropagation()` | 브라우저 버블링 중단 |
| `preventDefault()` | 기본 동작 취소 (링크 이동 등) |

- 위임에서는 `currentTarget`이 항상 컨테이너 → 클릭 위치는 `target`으로만 안다.

### 합성 이벤트 (SyntheticEvent)
- 핸들러에 네이티브 이벤트를 그대로 주지 않고 **감싸서 새로 만든 객체**. React의 용어.
- 이 프로젝트: `events.js:19-31`의 `event` 객체. `target`이 DOM 요소가 아니라 **노드**이고, `stopPropagation()`이 우리 루프도 멈춘다.

### dispatch
- "배분하다, 발송하다." 이 프로젝트에서는 `events.js:11`의 함수 이름.
- 받은 이벤트를 알맞은 핸들러들에게 나눠 보낸다.

## JS 문법·자료구조

### 구조 분해 매개변수
```js
constructor({ el, parent = null, domParent = null, on = {} })
```
- 객체 **하나**를 받아 그 안의 속성을 **이름으로** 꺼낸다. 순서 무관.
- `= null`, `= {}`는 안 넘겼을 때의 기본값.

### 전개 복사 `{ ...on }`
- 객체를 얕게 복사. 바깥에서 원본 `on`을 고쳐도 노드의 `handlers`는 영향받지 않는다.
- `[...this.children]` — Set을 배열로 복사. 도는 도중 원본에서 지워져도 순회가 꼬이지 않게.

### `!= null`
- `null`과 `undefined`만 걸러낸다. `if (text)`로 쓰면 `0`이나 `''`도 걸러져 버린다.

### 콜백 / 클린업 콜백
- 콜백: 나중에 호출되도록 넘겨 두는 함수.
- 클린업 콜백: 정리 용도의 콜백. `onCleanup(fn)`으로 저장, `destroy()`에서 실행.
- React `useEffect`가 return하는 함수와 같은 발상.

### 스택 vs 큐
- 큐(FIFO): 먼저 넣은 것이 먼저 나온다.
- 스택(LIFO): 나중에 넣은 것이 먼저 나온다.
- 클린업은 **스택** — 나중에 설치한 것을 먼저 걷어내는 게 안전. `node.js:53`의 `.reverse()`.
- `splice(0)` — 배열을 비우면서 꺼낸다 → 두 번 실행 방지.

### 재귀 / 깊이 우선
- 함수가 자기 자신을 호출. `destroy()`가 자식의 `destroy()`를 부른다.
- 깊이 우선이라 맨 아래 자손의 정리가 먼저 끝나고, 자기 자신은 맨 마지막.

### WeakMap / WeakSet
- 키를 **약하게** 참조한다 → 다른 곳에서 안 쓰이면 GC가 회수할 수 있다.
- 일반 Map이면 표가 요소를 붙잡아서, DOM에서 지운 요소도 메모리에 남는다.
- 코드: `registry.js`의 `elToNode`(WeakMap), `events.js:9`의 `handled`(WeakSet).

### 소멸자가 없다
- JS 객체는 사라질 때 자동으로 불리는 함수가 없다. GC는 메모리만 회수한다.
- 그래서 리스너 해제·레이어 제거는 `destroy()`로 **명시적으로** 해야 한다.

### 획득한 쪽이 해제도 예약 (RAII 발상)
- 자원을 얻는 코드 바로 옆에서 해제를 예약한다 → 잊을 일이 없다.
- C++ RAII, React `useEffect` cleanup과 같은 원리.
- 코드: `portal.js` — `pushLayer(el)` + `onCleanup(() => removeLayer(el))`, `onCleanup(listen(el))`.

## CSS

### stacking context
- z-index가 비교되는 **범위**. 부모가 stacking context를 만들면, 자식의 z-index는 그 부모 안에서만 비교된다.
- 그래서 `z-index: 1` 카드 안의 `z-index: 9999` 모달은 `z-index: 2` 헤더 아래에 깔린다.
- `position + z-index`, `transform`, `filter`, `opacity < 1` 등이 만든다.

### z-index는 positioned 요소에만 적용
- `position: static`(기본값)에는 z-index가 안 먹는다. 그래서 portal 컨테이너에 `position: relative`를 준다(`portal.js`).

### fixed와 containing block (데모 만들다 발견)
- `position: fixed` 요소는 보통 **뷰포트** 기준이라 조상의 `overflow: hidden`에 **잘리지 않는다.**
- 조상에 `transform`(또는 filter·contain 등)이 있으면 그 조상이 **containing block**(위치 계산 기준)이 되어 그 안에 갇히고 잘린다.
- 데모 카드에 `transform: translateZ(0)`을 넣은 이유 (`demo/style.css`).
