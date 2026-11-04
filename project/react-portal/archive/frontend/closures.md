# Closures (클로저)

> **한 줄**: 함수는 **자기가 만들어진 곳의 변수들을 기억한다.** 그 함수를 다른 곳으로 넘기거나 나중에 호출해도, 만들어질 때 보이던 변수에 계속 접근(읽기·쓰기)할 수 있다. 이 "함수 + 기억한 변수 환경" 묶음이 클로저다.

## 이해의 흐름 — N3에서 다시 만난 클로저

> 전체 노트: [N3-① ESC](../learning/modal/n3-escape-top-only.md)

N3(ESC가 전부 닫음)를 이해하는 열쇠가 클로저였다.

```text
createNaiveModal() 1번째 호출 ─┬─ modal #1 (지역 변수)
                              └─ onKey#1 ──기억──▶ modal #1     함수는 끝났지만 onKey#1은
                                                                document에 등록돼 살아 있음
createNaiveModal() 2번째 호출 ─┬─ modal #2
                              └─ onKey#2 ──기억──▶ modal #2

document keydown 리스너: [onKey#1, onKey#2]
ESC ─▶ onKey#1: "내 모달 닫자"   onKey#2: "내 모달 닫자"   ← 각자 자기 것만 앎 → 전부 닫힘
```

- 호출할 때마다 **새 환경**이 생기고, 그 안에서 만든 함수는 **그 환경의 변수**를 기억한다.
- 데모의 닫기 버튼이 정확히 "자기 모달"을 닫는 것도 같은 원리다.
- 라이브러리는 이 구조를 피했다: 리스너를 **모듈에 하나만** 두고, 특정 모달이 아니라 **공유 `stack`** 을 보고 "지금 맨 위가 누구냐"를 매번 묻는다.

## 가장 작은 예

```js
function makeCounter() {
  let count = 0;                 // makeCounter 안의 지역 변수
  return () => {                 // 이 화살표 함수가 count를 "기억"
    count += 1;
    return count;
  };
}

const next = makeCounter();      // makeCounter는 여기서 실행이 끝났다
next();  // 1                    // 그런데 count가 살아 있다
next();  // 2
```

보통 지역 변수는 함수가 끝나면 사라진다. 그런데 안쪽 함수가 `count`를 참조하고 있고, 그 안쪽 함수가 바깥(`next`)으로 나갔기 때문에 `count`도 같이 살아남는다.

## 실제로 무슨 일이 일어나나

함수를 **호출할 때마다** 그 호출만의 변수 공간(렉시컬 환경)이 새로 생긴다. 그 안에서 만들어진 함수는 그 공간을 가리키는 연결을 갖는다.

```
makeCounter() 호출 #1  →  환경 A { count: 0 }  ←── next  (A를 가리킴)
makeCounter() 호출 #2  →  환경 B { count: 0 }  ←── next2 (B를 가리킴)

next()  → A.count 증가 → 1, 2, 3 …
next2() → B.count 증가 → 1, 2 …      ← 서로 독립
```

- 변수를 찾을 때는 **자기 환경 → 만들어진 곳의 환경 → 그 바깥 …** 순으로 올라간다(스코프 체인). 이 순서는 **코드를 어디에 썼느냐**로 정해지고, 어디서 호출하느냐와는 상관없다(렉시컬 스코프).
- **값을 복사하는 게 아니라 변수 자체를 공유**한다. 그래서 읽기만이 아니라 **바꾸기**도 된다.

## 이 프로젝트의 클로저들

### 1. stopPropagation이 `stopped`를 바꾼다 (`src/events.js:18-27`)

```js
function dispatch(native) {
  let stopped = false;                // dispatch 호출마다 새로 생김
  const event = {
    stopPropagation() {
      stopped = true;                 // ← 바깥 변수 stopped를 "바꿈"
      native.stopPropagation();       // ← 바깥 변수 native도 기억
    },
  };
  for (let n = start; n && !stopped; n = n.parent) {   // 같은 stopped를 읽음
    ...handler(event);                // 핸들러가 event.stopPropagation()을 부르면
  }                                   // 이 루프가 멈춘다
}
```
- 핸들러는 `stopped`라는 변수를 모른다. `event.stopPropagation()`만 부른다. 그 메서드가 클로저로 `stopped`를 쥐고 있어서 루프 조건이 바뀐다.
- 클릭할 때마다 dispatch가 새로 호출되므로 `stopped`도 매번 새로 생긴다 → 이전 클릭이 다음 클릭에 영향 없음.

### 2. listen이 돌려주는 해제 함수 (`src/events.js:44-49`)

```js
export function listen(container) {
  for (const type of EVENT_TYPES) container.addEventListener(type, dispatch);
  return () => {
    for (const type of EVENT_TYPES) container.removeEventListener(type, dispatch);
    //                               ↑ listen이 끝난 뒤에도 "어느 컨테이너였는지" 기억
  };
}
```
- `portal.onCleanup(listen(el))` — 해제 함수는 한참 뒤 destroy 때 불린다. 그때도 자기가 어느 `container`에 붙였는지 안다.
- root용, portal#1용, portal#2용 해제 함수가 각각 **자기 container**를 기억한다(호출마다 환경이 따로 생기므로).

### 3. 클린업 예약 (`src/portal.js`)

```js
portal.onCleanup(() => removeLayer(el));   // 이 화살표 함수가 el을 기억
```
- `createPortal`은 즉시 끝나지만, 나중에 destroy가 이 함수를 부를 때 **이 portal의 el**을 정확히 뺀다.

### 4. 데모 핸들러가 "자기 portal"을 안다 (`demo/main.js:64-92`)

```js
function openPortalModal(parent) {
  const portal = createPortal(parent, document.body, {
    on: { click: () => log(`portal#${portal.depth} 핸들러`) },   // 이 호출의 portal
  });
  ...
  createNode(m.row, 'button', {
    text: '닫기',
    on: { click: (e) => { ...; portal.destroy(); } },            // 이 호출의 portal
  });
}
```
- `openPortalModal`을 두 번 부르면 환경이 두 개 생긴다. #1의 닫기 버튼은 #1의 `portal`을, #2의 닫기 버튼은 #2의 `portal`을 기억한다. 그래서 "어느 모달을 닫을지"를 따로 넘기지 않아도 된다.
- 참고: 첫 번째 핸들러는 `portal`이 할당되기 **전에** 만들어지지만 문제없다. 실행되는 시점(클릭할 때)에 변수를 읽기 때문이다. 클로저는 값이 아니라 **변수**를 기억한다.

## React에서는 어디서 쓰이나 (몰랐지만 매일 쓰던 것)

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  const onClick = () => setCount(count + 1);    // 이번 렌더의 count를 기억하는 클로저
  useEffect(() => {
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);             // id를 기억하는 클로저 (클린업)
  }, []);
  return <button onClick={onClick}>{count}</button>;
}
```
- 컴포넌트 함수는 **렌더할 때마다 다시 호출**된다 → 매 렌더마다 새 환경, 새 `count`, 새 `onClick`.
- 이벤트 핸들러, `useEffect`, 클린업 함수가 전부 클로저다.

## 흔한 함정

### 오래된 값 (stale closure)
```jsx
useEffect(() => {
  const id = setInterval(() => console.log(count), 1000);   // 첫 렌더의 count만 기억
  return () => clearInterval(id);
}, []);                                                     // 다시 안 만들어짐 → 계속 0 출력
```
클로저는 **만들어진 그 환경**을 기억한다. 이후 렌더에서 생긴 새 `count`는 모른다. 해결: 의존성 배열에 `count` 추가, 또는 `setCount(c => c + 1)`처럼 함수형 업데이트.

### 반복문의 `var`
```js
for (var i = 0; i < 3; i++) setTimeout(() => console.log(i));   // 3 3 3
for (let i = 0; i < 3; i++) setTimeout(() => console.log(i));   // 0 1 2
```
`var`는 반복 전체에 변수 하나 → 세 함수가 같은 `i`를 공유. `let`은 **반복마다** 새 변수.

### 메모리를 붙잡는다
```js
function mount(bigData) {
  window.addEventListener('resize', () => render(bigData));   // bigData를 기억
}
```
리스너가 살아 있는 한 `bigData`도 회수되지 않는다. 해제하지 않으면 누수. → [memory-and-cleanup](memory-and-cleanup.md)

### 해제 시 "같은 함수"가 아님
```js
el.addEventListener('click', () => go());
el.removeEventListener('click', () => go());   // 새로 만든 다른 함수 → 해제 안 됨
```
화살표 함수를 쓸 때마다 **새 함수 객체**(새 클로저)가 생긴다. 해제하려면 같은 참조를 보관하거나, 이 프로젝트의 `listen`처럼 해제 함수를 등록 시점에 만들어 둔다.
