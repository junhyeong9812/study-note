# Reference vs Copy (참조 vs 복사)

> **한 줄**: JS에서 **원시값은 값 자체**가, **객체는 객체를 가리키는 참조**가 전달된다. 객체 내용은 저절로 복사되지 않는다. 복사는 `...`이나 `structuredClone()`처럼 **직접 요청할 때만** 일어나고, `...`은 겉껍데기만 새로 만드는 **얕은 복사**다.

## 이해의 흐름 — 헷갈렸던 지점에서 시작하기

> 전체 Q&A: [03-internals-qa Q22](../learning/pr1/03-internals-qa.md), [overflow — savedOverflow](overflow.md)

### ① "클로저·WeakSet은 포인터가 아니라 모든 데이터를 그대로 복사해서 넣는 거 아니야?"

```text
처음 그린 그림                       실제
close = () => portal.destroy()      close ──▶ portal 변수 ──▶ 노드 객체 (메모리에 하나뿐)
  portal의 복사본을 들고 있음?                 닫기 버튼도 ────────┘
                                    
만약 복사였다면: 복사본을 destroy → 화면의 진짜 모달은 안 닫힘
실제로 닫힌다 = 참조라는 증거
```

복사는 `{ ...on }`, `[...children]`처럼 **직접 요청할 때만**, 그것도 겉만(얕은 복사).

### ② 반대로 — 원시값은 값이 복사된다 (`savedOverflow`)

```text
savedOverflow = body.style.overflow   'scroll' 문자열 "값"이 복사됨 (독립된 사본)
body.style.overflow = 'hidden'        body만 바뀜
savedOverflow                         여전히 'scroll'  ← 그래서 나중에 복원할 수 있다
```

| 담긴 것 | 변수에 들어 있는 것 | 이 프로젝트 |
|---|---|---|
| 객체 (노드·이벤트·요소) | 객체를 가리키는 참조 | 클로저의 `portal`, `handled.has(native)` |
| 원시값 (문자열·숫자) | 값 자체 | `savedOverflow` |

## 원시값 vs 객체

| 종류 | 예 | 변수에 들어 있는 것 |
|---|---|---|
| 원시값 | `number` `string` `boolean` `null` `undefined` `symbol` `bigint` | **값 자체** |
| 객체 | `{}` `[]` 함수, `Map`, `Set`, DOM 요소, 이벤트 객체 … | 객체를 **가리키는 참조** |

```js
let a = 1;
let b = a;        // 값 1을 복사
b = 2;
a;                // 1  — 영향 없음

const x = { n: 1 };
const y = x;      // 참조를 복사 (객체는 하나)
y.n = 2;
x.n;              // 2  — 같은 객체를 보고 있으니까
```

```
x ──┐
    ├──▶ { n: 2 }     메모리에 객체는 하나
y ──┘
```

C의 포인터처럼 "가리킨다"는 점은 같지만, 주소를 직접 보거나 계산할 수는 없다.

## 함수에 넘길 때도 같다

```js
function rename(obj) { obj.name = 'B'; }   // 넘겨받은 참조로 원본 객체를 수정
const user = { name: 'A' };
rename(user);
user.name;   // 'B'

function replace(obj) { obj = { name: 'C' }; }   // 지역 변수 obj가 "다른 객체를 가리키게" 바꿨을 뿐
replace(user);
user.name;   // 'B'  — 원본 변수 user는 그대로
```

- **객체를 고치면(mutate)** 원본이 바뀐다.
- **변수에 다른 걸 대입하면(reassign)** 그 변수만 바뀐다.

이 둘을 구분하는 게 핵심이다. (JS는 "참조로 전달"이 아니라 "참조값을 값으로 전달"한다 — call by sharing.)

## 비교도 참조로 한다

```js
{ n: 1 } === { n: 1 };   // false — 내용이 같아도 다른 객체
const o = { n: 1 };
o === o;                 // true  — 같은 객체
```

Set·WeakSet·Map의 `has`도 **같은 객체인가**로 판정한다. → [weak-collections](weak-collections.md)

## 복사하기

### 얕은 복사 — 겉만 새로

```js
const copy  = { ...obj };          // 객체
const copy2 = Object.assign({}, obj);
const arr2  = [...arr];            // 배열
const arr3  = arr.slice();
const arr4  = Array.from(set);     // Set → 배열
```

```js
const a = { list: [1, 2], name: 'x' };
const b = { ...a };

b.name = 'y';        // a.name은 그대로 'x'   — 겉 속성은 복사됨
b.list.push(3);      // a.list도 [1, 2, 3]    — 안쪽 배열은 같은 걸 공유!
```

```
a ──▶ { name: 'x', list: ─┐ }
                          ├──▶ [1, 2, 3]    안쪽은 하나
b ──▶ { name: 'y', list: ─┘ }
```

### 깊은 복사 — 안쪽까지 전부

```js
const deep = structuredClone(obj);    // 표준. 중첩 객체·배열·Map·Set·Date 등 복사
```
- **복사 못 하는 것**: 함수, DOM 요소, 클래스 인스턴스의 메서드(프로토타입) → 에러 또는 소실.
- `JSON.parse(JSON.stringify(obj))`는 옛 방식. `undefined`·함수 소실, `Date`가 문자열이 됨, 순환 참조에서 에러.

## const는 "고정"이 아니다

```js
const obj = { n: 1 };
obj.n = 2;        // ✓ 가능 — 객체 내용은 바꿀 수 있다
obj = {};         // ✗ TypeError — 변수가 가리키는 대상을 바꿀 수 없을 뿐
```
내용까지 막으려면 `Object.freeze(obj)` (이것도 얕다 — 안쪽 객체는 못 막음).

## 클로저도 복사가 아니다

클로저는 만들어질 때 값을 찍어 두는 게 아니라 **변수 자체를** 가리킨다. → [closures](closures.md)

```js
let stopped = false;
const stop = () => { stopped = true; };
stop();
stopped;   // true — 같은 변수
```

## 이 프로젝트에서

**참조 (복사 안 함)** — 같은 객체를 여러 곳이 공유해야 동작한다.
- 클로저의 `portal` (`demo/main.js`) — 닫기 버튼이 **진짜 그 노드**를 destroy. 복사였다면 화면의 모달은 안 닫힌다.
- `stopped` (`src/events.js`) — `stopPropagation()`이 바꾼 값을 루프가 본다.
- `handled.has(native)` — 두 dispatch가 받는 **같은 이벤트 객체**라서 중복 판정이 된다.
- `node.parent`, `node.el` — 트리 연결 전부 참조.

**복사 (명시적)** — 원본과 분리해야 할 때만.
- `this.handlers = { ...on }` (`src/node.js:12`) — 바깥에서 `on` 객체를 고쳐도 노드 핸들러는 그대로. 안의 함수들은 같은 함수(얕은 복사).
- `[...this.children]` (`src/node.js:52`) — destroy 중 원본 Set에서 자식이 빠져도 순회가 안 꼬이게. 원소는 같은 노드들.
- `return [...stack]` (`src/layers.js`) — 바깥에서 받은 배열을 고쳐도 내부 스택은 안전.

## React에서는 왜 중요한가

```jsx
// ✗ 같은 객체를 고침 → 참조가 같아서 React가 "안 바뀌었다"고 판단 → 리렌더 안 됨
user.name = 'B';
setUser(user);

// ✓ 새 객체를 만듦 → 참조가 달라짐 → 바뀐 걸 감지
setUser({ ...user, name: 'B' });
```
React는 변경 감지를 내용 비교가 아니라 **참조 비교(`Object.is`)**로 한다. 그래서 "불변성(immutability)" — 고치지 말고 새로 만들라 — 이 규칙이 된다. `useEffect` 의존성 배열, `React.memo`도 같은 원리.

## 흔한 함정

- **복사한 줄 알고 원본 수정**: `const b = a; b.x = 1;` — 복사가 아니라 같은 객체.
- **얕은 복사의 안쪽 공유**: `{ ...state }`로 복사 후 `copy.items.push()` → 원본 items도 바뀜.
- **객체 비교로 같음 판정**: `{ a: 1 } === { a: 1 }`은 false. 내용 비교가 필요하면 직접 비교.
- **DOM 요소를 structuredClone**: 에러. DOM 복제는 `el.cloneNode(true)`.
