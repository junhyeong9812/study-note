# Event Object

> **한 줄**: 리스너가 호출될 때 브라우저는 **이벤트 정보를 담은 객체**를 첫 번째 인자로 넣어 준다. 그 안의 `target`이 "어디서 일어났나", `currentTarget`이 "지금 누구의 리스너가 실행 중인가"다.

## 이해의 흐름 — 헷갈렸던 지점에서 시작하기

> 전체 Q&A: [03-internals-qa Q21](../learning/pr1/03-internals-qa.md)

### "`native` 객체란? 그 `target`은 어떤 거야?"

추상화(React 등)에 가려져 있어서 몰랐던 것: **리스너에는 브라우저가 만든 순수 객체가 그대로 들어온다.**

```text
사용자 클릭
   │
   ▼
브라우저가 MouseEvent 객체를 만든다 ── { type:'click', target, currentTarget, clientX, … }
   │
   ▼  addEventListener로 등록한 함수를 "호출하면서 첫 인자로" 넣어 줌
function dispatch(native) { … }        ← native는 우리가 붙인 이름 (보통 e, event)
```

```text
<div class="mini-portal">   ← native.currentTarget  리스너가 달린 곳 (위임에서는 항상 컨테이너)
  <div class="overlay">
    <div class="modal">
      <button>닫기</button>   ← native.target        실제로 클릭된 가장 안쪽 요소
```

**"어디서 클릭됐나"는 `target`으로만 안다.** 그래서 `nodeOf(native.target)`로 시작 노드를 찾는다. 이름을 `native`로 지은 건 우리가 감싸서 새로 만드는 이벤트 객체(합성 이벤트)와 구분하려고.

## 브라우저가 실제로 하는 일

```js
el.addEventListener('click', (e) => { ... });
//                            ↑ 브라우저가 호출하면서 넣어 주는 객체
```

이벤트 종류마다 객체 타입이 다르다. 모두 `Event`를 상속한다.

| 이벤트 | 객체 타입 | 추가 정보 예 |
|---|---|---|
| `click`, `mousedown` | `MouseEvent` | `clientX/Y`, `button` |
| `pointerdown` | `PointerEvent` | `pointerType`(mouse/pen/touch) |
| `keydown` | `KeyboardEvent` | `key`, `code`, `ctrlKey` |
| `input` | `InputEvent` | `data`, `inputType` |
| `focusin` | `FocusEvent` | `relatedTarget` |

## 핵심 속성

| 속성 | 뜻 |
|---|---|
| `type` | 이벤트 이름 (`'click'`) |
| `target` | **이벤트가 실제로 일어난** 가장 안쪽 요소. 전파 내내 같다 |
| `currentTarget` | **지금 실행 중인 리스너가 달린** 요소. 전파하면서 바뀐다 |
| `eventPhase` | 1 캡처 / 2 타깃 / 3 버블 |
| `bubbles` | 버블링하는 이벤트인가 |
| `defaultPrevented` | 누가 `preventDefault()`를 불렀나 |
| `isTrusted` | 사용자 실제 입력이면 `true`, `dispatchEvent`로 만든 거면 `false` |
| `composedPath()` | 이 이벤트가 지나는 경로 배열 |

### target vs currentTarget

```html
<div id="box">            ← 리스너는 여기
  <button>
    <span>아이콘</span>   ← 여기를 클릭
  </button>
</div>
```
```js
box.addEventListener('click', (e) => {
  e.target;         // <span>  — 실제 클릭 지점
  e.currentTarget;  // #box    — 리스너가 달린 곳
});
```

- 위임 구조에서는 `currentTarget`이 항상 컨테이너다. **클릭 위치는 `target`으로만** 알 수 있다.
- `target`은 우리가 의도한 요소가 아니라 그 **안쪽**일 수 있다(아이콘 span 등). 그래서 위로 올라가며 찾는다: `e.target.closest('button')`.
- `currentTarget`은 리스너 실행이 끝나면 `null`이 된다. 나중에 쓰려면 미리 변수에 담아 둔다.

## 이벤트 직접 만들기

```js
el.dispatchEvent(new MouseEvent('click', { bubbles: true }));  // 테스트에서 클릭 흉내
```
- `bubbles: true`를 안 주면 버블링하지 않는다. 테스트에서 위임이 안 될 때 흔한 원인.

## 이 프로젝트에서

- `function dispatch(native)` (`src/events.js:11`) — `native`가 바로 이 객체. 우리가 만드는 합성 이벤트와 구분하려고 이름을 그렇게 붙였다.
- `nodeOf(native.target)` (`src/events.js:15`) — target에서 위로 올라가며 등록된 노드를 찾는다. `closest`와 같은 발상.
- 합성 이벤트 (`src/events.js:19-31`) — `target`/`currentTarget`을 DOM 요소가 아니라 **노드**로 바꿔 담는다.
- 테스트의 `new MouseEvent('click', { bubbles: true })` (`test/portal-logical.test.js`).

## 흔한 함정

- **target이 안쪽 요소라 비교 실패**: `if (e.target === button)`은 아이콘 클릭에서 false. `closest` 사용.
- **비동기에서 currentTarget 사용**: `setTimeout` 안에서는 이미 `null`.
- **React에서는 왜 몰랐나**: React 핸들러의 `e`는 네이티브가 아니라 React가 감싼 **합성 이벤트**다. 원본은 `e.nativeEvent`. → [event-delegation.md](event-delegation.md)
