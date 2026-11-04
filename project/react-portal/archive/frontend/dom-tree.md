# DOM Tree

> **한 줄**: DOM은 HTML 문서를 브라우저가 **JS 객체의 트리**로 만든 것이다. 요소를 만드는 것(`createElement`)과 트리에 붙이는 것(`appendChild`)은 별개다.

## 이해의 흐름 — 헷갈렸던 지점에서 시작하기

> 코드를 읽으며 실제로 했던 질문과, 그걸 바로잡은 그림. 전체 Q&A: [03-internals-qa Q3·Q6·Q8](../learning/pr1/03-internals-qa.md)

### ① "`createElement`로 만든 요소도 어딘가에 등록되는 거 아니야?"

```text
처음 그린 그림                               실제
createElement('div')                        createElement('div')
   │                                           │
   ▼                                           ▼
 document 어딘가에 자동 등록?                  메모리에만 있는 고아 요소
                                              (parentNode = null, 화면에 없음)
                                               │
                                               │ appendChild ← 이 순간에만 트리에 들어감
                                               ▼
                                             body ─ … ─ <div>   화면에 그려짐
```

**만드는 것과 붙이는 것은 별개다.** 그래서 같은 방식으로 만든 요소를 카드 안에도, body에도 붙일 수 있다 — Portal이 가능한 이유.

### ② "`domParent`는 화면 전체를 그리는 큰 DOM이지?"

```text
처음 그린 그림                         실제 — 노드마다 "바로 위에 붙을 요소 하나"
  ┌──────── 큰 DOM ────────┐           #app            ← root의 domParent
  │ 모든 노드가 여기 붙음    │            └ .mini-root   ← card의 domParent (= root.el)
  └────────────────────────┘               └ .card    ← 버튼의 domParent (= card.el)
                                                └ button
                                       body           ← portal의 domParent (= target)
                                        └ .mini-portal
```

| 누가 만드나 | domParent | 결과 |
|---|---|---|
| `createRoot(container)` | `container` | 시작점 |
| `createNode(parent, …)` | `parent.el` | 논리 부모 = DOM 부모 |
| `createPortal(parent, target)` | `target` | **둘이 갈라짐 — Portal** |

한 칸씩 붙어서 결과적으로 큰 트리가 되는 것이지, 큰 DOM 하나에 전부 직접 붙는 구조가 아니다.

### ③ "`el`은 무슨 객체야?"

**element의 약자** — 노드(우리가 만든 논리 객체)가 소유한 **실제 DOM 요소**. 노드 → 요소는 `node.el`, 요소 → 노드는 registry(WeakMap).

## 브라우저가 실제로 하는 일

1. HTML을 파싱해서 요소마다 객체(`HTMLDivElement`, `HTMLButtonElement` …)를 만든다.
2. 그 객체들을 부모-자식으로 연결한 트리가 `document`다.
3. 트리가 바뀌면 브라우저가 스타일 계산 → 레이아웃 → 페인트를 다시 해서 화면에 반영한다.

```
document
└ html
  ├ head
  └ body
    ├ header
    └ div#app
      └ div.mini-root
```

각 요소 객체는 트리 탐색용 속성을 가진다.

| 속성 | 뜻 |
|---|---|
| `parentNode` | 부모 노드 (없으면 `null`) |
| `children` / `childNodes` | 자식 요소 / 자식 노드(텍스트 포함) |
| `contains(other)` | other가 자기 자손인지 |
| `ownerDocument` | 소속 문서 |

## 만드는 것 vs 붙이는 것

```js
const el = document.createElement('div');  // ① 메모리에만 존재 (detached)
el.parentNode;                              //    null
document.body.contains(el);                 //    false — 화면에 없음

document.body.appendChild(el);              // ② 트리에 들어감 → 화면에 그려짐
otherParent.appendChild(el);                // ③ 다시 붙이면 "이동" (복사 아님 — 한 요소는 부모 하나)

el.remove();                                // ④ 트리에서 떼어냄 (객체는 아직 메모리에 있을 수 있음)
```

- `createElement`는 공장일 뿐이다. 트리에 넣지 않는다.
- 요소는 **부모를 하나만** 가진다. 이미 붙은 요소를 다른 곳에 `appendChild`하면 옮겨진다.
- 떼어낸 요소도 누군가 참조하면 메모리에 남는다. → [memory-and-cleanup.md](memory-and-cleanup.md)

## 내용 넣기: textContent vs innerHTML

```js
el.textContent = '<b>hi</b>';   // 글자 그대로 표시: <b>hi</b>  — 안전
el.innerHTML   = '<b>hi</b>';   // HTML로 해석: 굵은 hi          — 사용자 입력이면 XSS 위험
```

## 이 프로젝트에서

- `src/node.js:62` `document.createElement(tag)` → 만들기
- `src/node.js:27` `domParent.appendChild(el)` → 붙이기. **어디에 붙이느냐**를 바꾼 게 Portal
- `src/node.js:56` `this.el.remove()` → 떼기
- `src/node.js:64` `textContent` 사용

## 흔한 함정

- **만들기만 하고 안 붙임**: 에러 없이 화면에 아무것도 안 나온다.
- **"복사"를 기대하고 appendChild**: 원래 자리에서 사라진다. 복사는 `el.cloneNode(true)`.
- **innerHTML에 사용자 입력**: 스크립트 주입(XSS). 텍스트는 `textContent`로.
- **React에서는 왜 몰랐나**: JSX가 `createElement`·`appendChild`를 대신 호출한다. React가 DOM 조작을 전부 맡기 때문에 직접 볼 일이 없다.
