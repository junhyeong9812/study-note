# Event Flow (캡처 · 타깃 · 버블)

> **한 줄**: 클릭 같은 이벤트가 생기면 브라우저는 그 이벤트를 **DOM 경로**를 따라 흘려 보내며, 경로에 등록된 리스너를 차례로 호출한다. 브라우저는 DOM만 알고, 프레임워크의 컴포넌트 트리는 모른다.

## 이해의 흐름 — 헷갈렸던 지점에서 시작하기

> 코드를 읽으며 실제로 했던 질문과, 그걸 바로잡은 그림. 전체 Q&A: [03-internals-qa Q13·Q14·Q16](../learning/pr1/03-internals-qa.md), [N2](../learning/modal/n2-open-close-same-click.md)

### ① "브라우저가 DOM 트리를 따라 올라가며, 버튼 클릭 시 **어떻게 처리할지** 찾는다?"

```text
처음 그린 그림                              실제 — 두 단계로 나뉜다
브라우저 ─▶ DOM을 타며                      [단계 1] 브라우저 (DOM 경로만 안다)
          "이 버튼의 처리 방법" 탐색          클릭된 요소 → 부모 → … → document
                                             경로에 addEventListener된 "리스너"만 호출
                                             ── 처리 방법(핸들러)을 찾지 않는다 ──
                                                        │
                                                        ▼ 리스너 = 컨테이너의 dispatch
                                           [단계 2] dispatch (우리 코드, 논리 트리)
                                             target → 노드 찾기 → n.parent 따라 핸들러 실행
```

브라우저는 **잡기만** 하고, **처리할 핸들러를 찾아 실행하는 건 단계 2**다. → [event-delegation](event-delegation.md)

### ② "portal은 app 밖이라, mini-portal에서 일어난 이벤트를 app이 받을 수 없다?"

```text
                         단계 1 (브라우저 리스너)     단계 2 (컴포넌트 핸들러)
portal 안 버튼 클릭        #app은 경로에 없음 → ✗       card·root는 논리 조상 → ✓
```

**단계 1에서만 맞다.** 그래서 portal 컨테이너에도 `listen`을 따로 달아 단계 1에서 잡을 지점을 만든다. 잡고 나면 단계 2에서 card·root 핸들러는 정상 실행된다.

### ③ "미니루트에서 처리됐으면 거기서 멈춰야 하는 거 아니야?"

```text
처음 그린 그림                     실제
button → .card → .mini-root ■     button → .card → .mini-root → #app → … → body → document
                   (처리됨, 멈춤)                    (dispatch 실행, 그래도 계속 올라감)
```

**네이티브 버블링은 "처리됐다"고 멈추지 않는다.** 멈추는 건 `stopPropagation()`을 불렀을 때뿐이다. 이 성질 때문에 N2(여는 click이 document의 닫기 리스너까지 올라감)가 생긴다.

## 브라우저가 실제로 하는 일

클릭이 일어나면:

1. 가장 안쪽의 클릭된 요소를 **target**으로 정한다.
2. `window`에서 target까지의 **경로**를 계산한다.
3. 그 경로를 세 단계로 흘린다.

```
              window
                │  ① 캡처 단계 (위 → 아래)   addEventListener(..., { capture: true })
              document
                │
              body
                │
           div.mini-portal
                │
             button  ← ② 타깃 단계
                │
           div.mini-portal
                │  ③ 버블 단계 (아래 → 위)   addEventListener(...) 기본값
              body
                │
              document
                │
              window
```

- 캡처 단계의 실행 순서·stopPropagation 실험: [event-capture.md](event-capture.md)
- 기본 `addEventListener(type, fn)`은 **버블 단계**에서 호출된다. 우리가 흔히 말하는 "버블링"이 이것.
- 각 단계에서 브라우저는 **그 요소에 등록된 리스너만** 호출한다. 리스너가 없는 요소는 그냥 지나친다.
- 경로는 이벤트가 시작될 때 **DOM 구조로** 정해진다. 그래서 DOM상 다른 곳에 있는 요소(portal)는 경로가 완전히 다르다.

## 리스너 등록과 해제

```js
function onClick(e) { /* ... */ }

el.addEventListener('click', onClick);                    // 버블 단계
el.addEventListener('click', onClick, { capture: true }); // 캡처 단계
el.addEventListener('scroll', onScroll, { passive: true });// preventDefault 안 함을 약속 → 스크롤 성능
el.addEventListener('click', onClick, { once: true });    // 한 번 실행 후 자동 해제

el.removeEventListener('click', onClick);                 // 등록할 때와 "같은 함수 참조"여야 해제됨
```

## 전파 멈추기

| 메서드 | 효과 |
|---|---|
| `e.stopPropagation()` | 경로의 **다음 요소**로 안 넘어감 (같은 요소의 다른 리스너는 실행됨) |
| `e.stopImmediatePropagation()` | 같은 요소의 나머지 리스너까지 중단 |
| `e.preventDefault()` | 전파와 무관. **기본 동작**(링크 이동, 폼 제출, 체크박스 토글 등)만 취소 |

## 버블링하지 않는 이벤트도 있다

- `focus` / `blur`는 버블링하지 않는다 → 위임하려면 `focusin` / `focusout` 사용.
- `mouseenter` / `mouseleave`도 버블링하지 않는다 → `mouseover` / `mouseout`은 버블링한다.
- 확인: `e.bubbles` 속성.

## 이 프로젝트에서

- portal 안 버튼 클릭의 경로: `button → … → .mini-portal → body → document → window`. **`#app`, `.mini-root`가 없다.**
- 그래서 `.mini-root`에 단 리스너는 portal 클릭을 못 받고, `.mini-portal`에 따로 `listen`해야 한다 (`src/portal.js:19`).
- 데모의 `[네이티브] #app` 로그(`demo/main.js:17`)가 portal 클릭에서 안 찍히는 이유도 같다.
- `e.stopPropagation()`은 우리 합성 이벤트에서도 네이티브 쪽을 함께 멈춘다 (`src/events.js:24-27`).

## 흔한 함정

- **익명 함수로 등록 후 해제 시도**: `removeEventListener('click', () => …)`는 다른 함수라 해제되지 않는다.
- **stopPropagation으로 기본 동작을 막으려 함**: 기본 동작은 `preventDefault`.
- **focus 위임이 안 됨**: 버블링하지 않는 이벤트라서. `focusin` 사용.
- **React에서는 왜 몰랐나**: React의 `onClick`은 이 흐름 위에 React가 따로 만든 흐름이다. 캡처는 `onClickCapture`로 노출된다. → [event-delegation.md](event-delegation.md)
