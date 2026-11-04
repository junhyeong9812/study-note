# web-platform/26-portals-and-two-trees — 정답

## 정답

### 1. appendChild만 하면 / Portal이 더 지키는 것

```text
                       DOM 위치(CSS)        논리 관계(Context·핸들러 버블·수명)
  카드 안에 그대로       ✗ 카드 CSS에 갇힘     ✓
  appendChild(body)     ✓                     ✗ 끊김
  Portal                ✓                     ✓ ← 논리 부모는 그대로 둔다
```

- `appendChild`만 하면 카드의 쌓임 맥락·`overflow`·`transform` 조상에서 벗어난다. 대신 카드의 Context·클릭 처리·수명과 끊긴다.
- Portal은 DOM 부모만 바꾸고 논리 부모(`parent`)는 그대로 둔다.
- z-index만으로는 부모 쌓임 맥락 밖으로 못 나간다. Portal은 DOM을 빼서 그 문제를 피하고, z-index는 뺀 뒤 body 최상위에서 순서를 정할 때 쓴다.

### 2. 두 단계 그림과 등록 두 종류

```text
  [단계 1] 브라우저: 클릭된 요소 → 부모 → … → document (DOM 경로)
           경로 위에서 addEventListener된 리스너만 호출 — 처리 방법을 찾지 않는다
                │  그 리스너 = 컨테이너의 dispatch
                ▼
  [단계 2] dispatch: nodeOf(target)로 시작 노드 → n = n.parent 따라 handlers[type] 실행
```

| | 무엇을 | 어디에 | 언제 |
|---|---|---|---|
| 브라우저 리스너 | `dispatch` | 루트·portal 컨테이너 요소 | 루트 생성 때 1번, portal 열 때마다 |
| 프레임워크 핸들러 | `on`의 함수 | 노드 객체의 `handlers` | 노드를 만들 때마다(저장만) |

- 버튼 요소 자체에는 브라우저 리스너가 없다.

### 3. 형제 DOM 안의 portal

(실험, Node 20.19.6 · jsdom 29.1.1 · vitest 4.1.12, 2026-11-04 — 3회 같은 출력)

```text
  [단계1] 브라우저 → dispatch 리스너 (currentTarget=#portal2)
  [단계2] 핸들러 portal2-btn
  [단계2] 핸들러 portal2
  [단계2] 핸들러 card
  [단계2] 핸들러 root
  [단계1] 브라우저 → dispatch 리스너 (currentTarget=#root)
          이미 처리한 이벤트 → return
```

- dispatch 리스너는 **두 번** 불린다. DOM 경로 `#portal2-btn → #portal2 → #sidebar → #root → …`에 컨테이너가 둘 다 있기 때문이다. 두 번째는 같은 이벤트 객체라 `seen`에서 걸러져 처리는 한 번이다.
- 핸들러 순서는 논리 경로 `portal2-btn → portal2 → card → root`다.
- `sidebar` 핸들러는 **불리지 않는다.** DOM 조상이지만 논리 조상이 아니다. React에서도 같았다(실험 `in-sibling`: sidebar `onClick` 없음, card `onClick` 호출).

### 4. 처리 뒤에도 계속되는 네이티브 버블링

- 불린다. 실험 (a): 핸들러 세 개 뒤에 `#app`·`document` 네이티브 리스너가 이어서 찍혔다.
- 브라우저에는 "처리됨" 개념이 없다. 전파를 멈추는 것은 `stopPropagation()`(·`stopImmediatePropagation()`) 호출뿐이다.
- 열기 핸들러가 `document`에 "바깥 클릭 닫기" 리스너를 단다고 하자. 같은 클릭의 버블 패스가 아직 `document`에 닿지 않았으므로 방금 단 리스너가 같은 이벤트로 불린다. 그래서 열자마자 닫힌다. 대처: 다음 틱에 등록, 열기·닫기 이벤트 분리(`pointerdown` vs `click`), 트리거를 안쪽으로 판정.

### 5. createPortal vs createRoot

(실험, Node 20.19.6 · jsdom 29.1.1 · vitest 4.1.12 · react 19.3.1, 2026-11-04 — 3회 같은 출력)

```text
== real 클릭   card.contains=false   DOM: #real → #target → body → html
  React onClick real (theme=dark)
  React onClick card (React 부모)
  네이티브 document 리스너
== fake 클릭   card.contains=false   DOM: #fake → div → #target → body → html
  React onClick fake (theme=light)
  네이티브 document 리스너
```

| | (가) `createPortal` | (나) `createRoot` |
|---|---|---|
| `useContext` | `dark` | `light`(기본값) |
| 카드 `onClick` | 호출됨 | 안 됨 |
| `card.contains(button)` | `false` | `false` |

- DOM 위치는 같다. 차이는 전부 React 트리에서 난다 — (나)는 새 루트라 부모 체인이 없다.
- (나)에서도 버튼 자기 `onClick`은 동작한다. prop으로 직접 넘긴 함수는 트리와 무관하다. 그래서 이 실수는 Context나 부모 클릭이 필요할 때 드러난다.

### 6. 네이티브 리스너와 React 핸들러의 순서, portal 안 stopPropagation

(실험, 같은 환경, 2026-11-04 — 3회 같은 출력)

```text
== inner 클릭   card.contains=true   DOM: #inner → #card → #app → body → html
  네이티브 #card 리스너
  React onClick inner (theme=dark)
  React onClick card (React 부모)
  네이티브 document 리스너
== real-stop 클릭   card.contains=false   DOM: #real-stop → #target → body → html
  React onClick real-stop (theme=dark)
```

- 네이티브 `#card` 리스너가 먼저다. React 핸들러는 루트 컨테이너(`#app`) 리스너 안에서 실행되고(React 17+), `#card`는 `#app`보다 DOM상 안쪽이라 단계 1에서 먼저 지나간다.
- `real-stop`: 카드 `onClick`은 안 불렸다(논리 버블 중단). 네이티브 `document` 리스너도 안 불렸다 — React가 원본 이벤트 전파도 멈췄다(이 구성에서 관찰). portal 경계의 `stopPropagation`은 `document` 레벨 로깅까지 막을 수 있다.

### 7. 위치 vs 관계

| 질문 | 성격 | 트리 |
|---|---|---|
| 바깥 클릭이면 닫기 | 관계(이 모달에 속하나) | 논리 |
| Tab 다음 포커스 대상 | 위치·순서(트리 순서) | DOM |
| 부모 `overflow`에 잘리나 | 위치 | DOM |
| `useContext` 값 | 관계 | 논리 |
| 부모 언마운트 시 같이 정리 | 관계(수명) | 논리 |
| `.card .btn` 선택자 적용 | 위치(DOM 조상) | DOM |

- 같은 "안쪽"이라도 "이 모달에 속하나"는 논리, "Tab이 모달 DOM 안에서 도나"는 DOM이다. 실험의 트리 순서 `inner-btn, portal2-btn, portal-btn, fake-btn`에서 portal 버튼의 위치는 논리 위치가 아니라 DOM 위치(sidebar 안·body 끝)를 따랐다.

### 8. 날짜 선택기를 누르면 모달이 닫힘

- 원인: "이 클릭이 모달 안쪽인가"는 관계 질문인데 엘리먼트(`dialog.contains`)에게 물었다. 엘리먼트는 DOM만 안다. 날짜 선택기는 Portal이라 DOM상 body 끝(모달 밖)이므로 "바깥"이 된다. 실험: `portal-btn`은 `card.el.contains=false`, 논리 조상 `true`.
- 최소 두 트리 코드:

```javascript
const node = nodeOf(e.target);                         // DOM → 논리로 건너가기
const inside = node && isLogicalDescendant(node, dialog);   // n = n.parent로 dialog를 찾는다
if (!inside) close('outside');
```

- React: 모달 루트의 React `onPointerDown`에서 "안쪽" 표시를 남기고 `document` 리스너가 그 표시를 본다. portal 위젯의 이벤트도 React 트리로 모달 루트까지 버블하므로 안쪽으로 잡힌다. React 핸들러가 `document` 리스너보다 먼저 도는 순서(6번 실험)에 기대므로 테스트로 고정한다. 위젯이 별도 루트라면 그 DOM 컨테이너를 안쪽 영역으로 따로 등록한다.
- 회귀 테스트: "모달 안에서 연 portal 위젯 클릭 → 모달 유지". 판정을 `contains`로 되돌리면 실패해야 한다.

### 9. portal 모달의 키가 패널 onKeyDown으로

- 프레임워크 이벤트는 논리 트리로 버블한다. 모달을 렌더한 패널이 논리 조상이므로, DOM상 body 끝이어도 키 이벤트가 패널 `onKeyDown`에 닿는다(5번·3번 실험의 클릭과 같은 구조).
- `stopPropagation`(portal 경계): 그 지점 위로의 논리 버블을 끊는다. 하지만 조상 관계는 남아 있고, 경계를 빠뜨린 새 위젯·다른 이벤트 타입에서 다시 샌다. 네이티브 전파도 멈춰 `document` 리스너가 못 받을 수 있다(6번).
- 구조적 해소: 열림 상태를 상위(앱 루트 레이어·모듈 소유)로 올려 모달을 루트 근처에서 렌더한다. 그러면 패널이 논리 조상 경로에서 빠져 버블할 경로 자체가 없어진다. `stopPropagation`은 백스톱으로만 둔다. 실제 사례는 [issue/…/tree-position-semantics](../../../issue/typescript/react/tree-position-semantics/2-summary.md).

### 10. nodeOf와 WeakSet

- `target`은 등록하지 않은 안쪽 요소(아이콘 `span`·텍스트)일 수 있다. 브라우저가 주는 정보는 DOM 요소뿐이므로, DOM을 위로 타서 처음 만나는 등록 요소의 노드로 건너간다. 건너간 뒤의 질문(누가 핸들러를 받나)은 관계 질문이라 논리 트리만 탄다.
- `WeakSet`은 연타를 줄이지 않는다. 클릭마다 새 이벤트 객체(E1 ≠ E2)라 두 번 다 처리된다. 막는 것은 클릭 한 번의 같은 객체가 겹친 컨테이너의 dispatch 두 곳에 도착하는 경우(3번)뿐이다. 연타 묶기는 디바운스·스로틀이다.
