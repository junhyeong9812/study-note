# 01. 내가 정리한 전체 구조

> 대화하면서 내 말로 정리한 것을 다듬은 버전. 틀렸다가 고친 부분은 ⚠️로 표시.

## 한 문장

**Portal = DOM은 다른 곳(body)에 붙이되, 논리적인 부모-자식 관계는 원래 자리 그대로 유지하는 것.**

z-index를 쓰는 기능이 아니다. 부모의 stacking context·overflow에 갇히는 문제를 **DOM을 밖으로 빼서** 피하고, 빼낸 뒤에 body 최상위에서 z-index로 순서를 정한다.

## 트리가 두 개다

```
논리 트리 (node.parent)              DOM 트리 (el.parentNode)
root                                 body
 └ card                               ├ #app
    └ portal  ←──── 같은 노드 ────→   │  └ .mini-root
       └ overlay → modal → 버튼        │     └ .card
                                      └ .mini-portal   ← portal만 여기로
                                         └ .overlay → .modal → 버튼
```

| 따르는 트리 | 동작 |
|---|---|
| DOM 트리 | 화면 위치, CSS(stacking context·overflow), **브라우저의** 이벤트 버블링 |
| 논리 트리 | **우리** 핸들러 실행 순서, Context(`inject`), 정리(`destroy`) |

## Node 객체 = 두 트리를 동시에 들고 있는 것

- `Node` 하나가 DOM 요소 `el` 하나를 소유한다.
- 생성자(`src/node.js:8-28`)가 하는 일
  1. `on`으로 받은 핸들러를 `this.handlers`에 **복사해서 저장** (`{ ...on }`)
  2. 핸들러의 key(`click` 등)가 `EVENT_TYPES`에 있는지 검사, 없으면 경고
  3. `register(el, this)` — el → 노드 역방향 연결 등록
  4. `parent.children.add(this)` — **논리 트리**에 연결
  5. `domParent.appendChild(el)` — **DOM 트리**에 연결
- `parent`는 **Node**, `domParent`는 **DOM 요소** — 타입부터 다르다.

### domParent는 "화면 전체 큰 DOM"이 아니다 ⚠️

노드마다 **바로 위에 붙을 요소 하나**다.

| 만드는 함수 | domParent | 결과 |
|---|---|---|
| `createRoot(container)` | `container` (#app) | 시작점 |
| `createNode(parent, …)` | `parent.el` | 논리 부모 = DOM 부모 |
| `createPortal(parent, target)` | `target` (body) | **둘이 갈라짐 — 이게 Portal** |

portal 안의 내용은 다시 평범한 `createNode`라서 `.mini-portal` 안에 차곡차곡 쌓인다. 위치가 바뀌는 건 portal 한 칸뿐.

### 중첩 portal

"모달 위에 또 열기" = `createPortal(portal#1, body)`.
- DOM: #2도 **body 직속**, #1의 **형제** → 그래서 z-index(1000, 1001)로 순서를 정해야 한다.
- 논리: #2의 부모는 #1 → 클릭은 `#2 → #1 → card → root`, #1을 닫으면 #2도 같이 정리.

## 정리(destroy)와 클린업

- `destroy()`(`src/node.js:49`)는 **자식부터 재귀**로 정리 → 내 클린업 실행 → registry 해제 → 부모에서 빠짐 → DOM에서 제거.
  - ⚠️ "역순으로 자식 제거"가 아니라, 자식은 추가된 순서대로 돌지만 **재귀(깊이 우선)** 라서 결과적으로 맨 아래부터 끝난다.
- 자식이 각자 자기 클린업을 끝내므로, 부모 차례에는 **자기 클린업만 남는다.** → 각 노드는 자기 뒷정리만 책임지면 된다.
- 클린업 = **나중에 실행할 함수(콜백)를 배열에 저장**해 뒀다가 destroy 때 실행.
  - ⚠️ 큐(FIFO)가 아니라 **스택(LIFO)** — `.reverse()`로 마지막에 등록한 것부터.
- JS에는 소멸자가 없다 → 객체가 사라진다고 클린업이 저절로 돌지 않는다. `destroy()`를 **명시적으로** 불러야 한다.
- **획득한 쪽이 해제도 예약한다**: `pushLayer(el)` 바로 옆에 `onCleanup(() => removeLayer(el))`. Node는 레이어가 뭔지 몰라도 된다.

## inject (Context)

- ⚠️ DOM을 타는 게 아니라 **논리 트리(`n.parent`)를, 위로만** 탄다. 처음 찾은 provide 값을 돌려준다.
- DOM을 탔다면 portal 안에서는 body로 올라가서 card의 값을 못 찾는다.

## 이벤트 — 가장 오래 헤맨 부분

### 등록이 두 종류다

| | 무엇을 | 어디에 | 코드 | 언제 |
|---|---|---|---|---|
| **브라우저 리스너** | `dispatch` 함수 | `.mini-root`, `.mini-portal` **요소** | `listen()` → `events.js:45` | root 생성 시 1번, portal **열 때마다** 1번 |
| **우리 핸들러** | `on: { click: fn }`의 fn | **노드 객체**의 `handlers` | `node.js:12` | 모든 노드 생성 시 |

- `createNode`의 `on`은 브라우저 등록이 아니라 **노드에 메모해 두기**다.
- 버튼에는 브라우저 리스너가 **하나도 없다.** (개발자 도구 Event Listeners 패널로 확인 가능)
- portal의 리스너 등록은 `main.js`에 안 보이고 `createPortal` 안(`portal.js:19`)에 숨어 있다.
- ⚠️ portal은 페이지 로드 시 없다. **열기 버튼을 누를 때마다** 새로 생기고, 그때마다 `listen`이 불린다.

### 클릭 한 번의 흐름 = 두 단계

```
[단계 1] 브라우저 — DOM 트리를 따라 위로
  클릭된 요소 → 부모 → 부모 … 경로에 addEventListener된 리스너를 호출
  우리 구조에서 그 리스너 = 컨테이너의 dispatch 하나뿐
  (브라우저는 우리 논리 트리를 모른다. 핸들러를 "찾지" 않는다 ⚠️)

[단계 2] dispatch — 논리 트리를 따라 위로
  ① nodeOf(native.target)    클릭된 DOM 요소 → 시작 노드
  ② n = start; n = n.parent   논리 부모로 올라가며
  ③ n.handlers[native.type]   'click' key로 저장된 함수가 있으면 실행
```

- `'click'` 문자열 하나가 세 곳을 잇는다: `EVENT_TYPES`(등록 목록) ↔ `on: { click }`(key) ↔ `native.type`(꺼낼 때).
- portal은 #app 밖이라 단계 1의 경로에 `.mini-root`가 없다 → **portal에도 `listen`이 따로 필요**하다. 이게 없으면 단계 2가 시작조차 안 된다.
- ⚠️ "app이 portal 이벤트를 못 받는다"는 **단계 1(브라우저 리스너)에서만** 맞다. 단계 2에서 card·root 핸들러는 정상 실행된다. 데모에서 `[네이티브] #app` 로그가 안 찍히는 건 #app에 **직접** 단 브라우저 리스너라서다.

### dispatch란

우리가 `events.js:11`에 만든 함수. 브라우저에게는 평범한 리스너 하나로 보이고, 안에서는 논리 트리를 따라 핸들러를 배분한다 → **브라우저와 논리 트리 사이의 교환원**. 이 방식이 **이벤트 위임**이고, React도 같다(React 17+는 루트 컨테이너 + portal 컨테이너에 리스너).

### native와 target

- `native` = 브라우저가 리스너를 부를 때 넣어 주는 **진짜 이벤트 객체**(`MouseEvent` 등). 이름은 우리가 지은 것.
- `native.target` = **실제로 클릭된 가장 안쪽 DOM 요소**.
- `native.currentTarget` = 지금 리스너가 달린 요소(위임에서는 항상 컨테이너).
- 그래서 "어디서 클릭됐나"는 `target`으로만 알 수 있고, `nodeOf(native.target)`로 시작 노드를 찾는다.
