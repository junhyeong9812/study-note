# WeakSet & WeakMap

> **한 줄**: 객체를 담되 **그 객체를 붙잡지 않는** 컬렉션. 담긴 객체가 다른 곳에서 더 이상 쓰이지 않으면, 컬렉션 안에 있어도 GC가 회수할 수 있다. "이 객체에 표시(또는 부가 정보)를 붙이되, 수명에는 관여하지 않겠다"는 용도.

## 이해의 흐름 — 헷갈렸던 지점에서 시작하기

> 전체 Q&A: [03-internals-qa Q22·Q23](../learning/pr1/03-internals-qa.md)

### ① "중복 방지(`handled`)는 클릭이 2번 들어오면 1번만 처리한다는 뜻?"

```text
처음 그린 그림                       실제
클릭 ×2 ─▶ handled ─▶ 1번만 처리      사용자 클릭 2번 = 이벤트 객체 2개 (E1 ≠ E2) → 둘 다 처리
                                    
                                    막는 것은 "클릭 1번(E1)이 리스너 두 곳에 도착"하는 경우뿐:
                                      .mini-root     ← dispatch ②  같은 E1 → handled.has ✓ → return
                                       └ .mini-portal ← dispatch ①  E1 처음 → 표시하고 처리
                                          └ button   ← 클릭 1번
```

연타를 한 번으로 줄이는 건 **디바운스/스로틀**이라는 별개 기법이다.

### ② "WeakSet은 데이터를 복사해서 넣는 거 아니야?"

```text
handled.add(native)      → native 객체를 가리키는 "약한 참조"를 넣음 (복사 아님)
handled.has(native)      → "같은 객체인가"로 판정 (내용 비교 아님)

const a = {x:1}, b = {x:1};   new WeakSet([a]).has(b)  → false
```

두 dispatch가 받는 게 **브라우저가 만든 같은 이벤트 객체 하나**라서 중복 판정이 된다. → [reference-vs-copy](reference-vs-copy.md)

## Set과 무엇이 다른가

```js
const set  = new Set();
const weak = new WeakSet();

let obj = { name: 'a' };
set.add(obj);
weak.add(obj);

obj = null;   // 내 변수에서는 놓았다
// set  : 여전히 obj를 붙잡고 있음 → 회수 불가 (메모리에 계속 남음)
// weak : 붙잡지 않음              → 다른 참조가 없으니 회수 가능
```

| | `Set` | `WeakSet` |
|---|---|---|
| 담을 수 있는 값 | 아무거나 (숫자·문자열·객체) | **객체만** (등록되지 않은 Symbol도 가능 — ES2023) |
| 담긴 값을 붙잡나 | **강한 참조** — 붙잡음 | **약한 참조** — 안 붙잡음 |
| 메서드 | `add` `has` `delete` `clear` | `add` `has` `delete` **만** |
| `size`, 순회(`for…of`, `forEach`) | 가능 | **불가** |
| 용도 | 값 목록 관리 | 객체에 "표시" 붙이기 |

## 강한 참조 vs 약한 참조

GC는 **루트(전역 변수, 실행 중인 함수의 변수)에서 강한 참조를 따라 도달할 수 있는 객체만** 살려 둔다. → [memory-and-cleanup](memory-and-cleanup.md)

```
루트 ──강한──▶ Set ──강한──▶ obj        obj에 도달 가능 → 살아 있음

루트 ──강한──▶ WeakSet ┄┄약한┄┄▶ obj     약한 참조는 "도달"로 치지 않음
                                         다른 강한 참조가 없으면 → 회수
```

약한 참조는 GC가 "살려 둘지" 판단할 때 **세지 않는** 참조다.

## 왜 size와 순회가 없나

**언제 회수될지 아무도 모르기 때문이다.** GC 실행 시점은 엔진이 정한다.

만약 `weak.size`가 있다면 같은 코드에서도 실행할 때마다 값이 달라질 수 있다(GC가 돌았느냐에 따라). 이런 비결정적인 동작을 막으려고, **"이 객체가 들어 있나?"(`has`)만 물을 수 있게** 설계되었다. 내가 객체를 들고 있어야 물어볼 수 있으니, 물어보는 시점에는 그 객체가 반드시 살아 있다.

```js
weak.has(obj);   // ✓ 객체를 들고 있으니 답이 확정적
weak.size;       // ✗ undefined — 없음
[...weak];       // ✗ TypeError — 순회 불가
```

## WeakSet의 대표 용도

### 1. "이미 처리했다" 표시 (이 프로젝트)

```js
// src/events.js:9-13
const handled = new WeakSet();

function dispatch(native) {
  if (handled.has(native)) return;   // 이 이벤트 객체, 이미 처리했나?
  handled.add(native);               // 처리했다고 표시
  ...
}
```

- 같은 이벤트 객체가 컨테이너 두 곳의 dispatch에 도착할 수 있다(portal target이 루트 안일 때). → [04-remaining-code §A](../learning/pr1/04-remaining-code.md)
- **Set으로 쓰면**: 클릭할 때마다 이벤트 객체가 쌓이고 절대 빠지지 않는다. 몇 시간 쓰면 수만 개.
- **WeakSet으로 쓰면**: 이벤트 처리가 끝나면 브라우저도 우리 코드도 그 객체를 안 쓴다 → 자동으로 회수. **지울 코드를 따로 안 써도 된다.**

### 2. 순환 참조 탐지 (재귀 순회)

```js
function deepClone(value, seen = new WeakSet()) {
  if (typeof value !== 'object' || value === null) return value;
  if (seen.has(value)) throw new Error('순환 참조');   // 이미 방문한 객체
  seen.add(value);
  ...
}
```
방문한 객체를 표시만 하면 되고, 함수가 끝나면 표시도 필요 없다.

### 3. 진짜 인스턴스인지 확인 (브랜딩)

```js
const instances = new WeakSet();
class Token {
  constructor() { instances.add(this); }
  static isToken(x) { return instances.has(x); }   // 생김새가 같은 가짜 객체는 false
}
```

## WeakMap: 표시 대신 "값"을 붙일 때

WeakSet이 "들어 있다/없다"만 기억한다면, WeakMap은 **객체 → 값**을 기억한다. 키가 약한 참조다.

```js
// src/registry.js
const elToNode = new WeakMap();
elToNode.set(el, node);    // DOM 요소에 "주인 노드" 정보를 붙임
elToNode.get(el);          // 꺼내기
```
- DOM 요소 객체 자체를 고치지 않고(`el.__node = node` 같은 속성 추가 없이) 정보를 붙인다.
- 요소가 DOM에서 빠지고 아무도 참조하지 않으면, 키와 값이 같이 회수된다.

| | WeakSet | WeakMap |
|---|---|---|
| 기억하는 것 | 객체가 들어 있나 | 객체 → 값 |
| 메서드 | `add` `has` `delete` | `set` `get` `has` `delete` |
| 이 프로젝트 | `handled` (처리한 이벤트) | `elToNode` (요소 → 노드) |

## 흔한 함정

- **원시값 넣기**: `weak.add('a')` → TypeError. 객체만 된다.
- **목록이 필요한데 WeakSet 사용**: "열린 모달 전부 닫기"처럼 **순회해야 하면 못 쓴다.** 그래서 `src/layers.js`의 레이어 스택은 일반 배열이다(대신 `removeLayer`로 직접 빼야 한다).
- **회수를 눈으로 확인하려 함**: 코드로는 관찰할 수 없다(그게 설계 의도). 개발자 도구 Memory 탭의 heap snapshot으로만 본다.
- **WeakSet에 넣었으니 정리 끝이라고 착각**: WeakSet은 **자기가** 붙잡지 않을 뿐이다. 다른 곳(배열, 리스너 클로저)이 붙잡고 있으면 여전히 남는다.

## 더 나아가면 (참고)

- `WeakRef`: 객체 하나를 약하게 참조. `.deref()`로 꺼내는데, 이미 회수됐으면 `undefined`.
- `FinalizationRegistry`: 객체가 회수된 **뒤에** 콜백을 받는다. 실행 시점이 보장되지 않아 정리 로직의 주 수단으로 쓰면 안 된다.
- 둘 다 일반 앱 코드에서는 거의 쓸 일이 없다. 캐시 같은 특수한 경우용.
