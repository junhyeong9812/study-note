# web-platform/04-dom-and-event-model — DOM 트리와 이벤트 모델: 전파(캡처·버블)와 위임 — 정리 (힌트)

## 해결하는 문제

화면 요소는 겹쳐 있다. 버튼은 카드 안에, 카드는 목록 안에 있다. 사용자가 버튼을 누르면 "누른 것"은 버튼이기도 하고 카드이기도 하고 목록이기도 하다.

```text
  <ul id=list>                 클릭 한 번 ─▶ 누가 알아야 하나?
    <li class=card>              - 버튼: "저장" 동작
      <button>저장</button>       - 카드: 선택 표시
    </li>                         - 목록: 분석 로깅, 바깥 클릭 닫기
  </ul>
```

- 요소마다 따로 알리면 두 가지가 깨진다.
  - 비용: 행 1,000개에 리스너 1,000개(아래 실험: `JSEventListeners` +1000).
  - 동적 요소: 나중에 추가된 행에는 리스너가 없다.
- DOM은 문서를 **트리**로 두고, 이벤트를 **트리 경로를 따라 전파**한다. 위에서 내려오며(캡처) 대상에 닿고 다시 올라가며(버블) 조상들이 같은 이벤트를 본다.
  - *DOM(Document Object Model)*: 문서를 노드 트리로 나타낸 것과 그것을 다루는 API. WHATWG DOM 표준이 정한다.
  - *이벤트 전파*: 이벤트 하나가 경로 위 여러 노드의 리스너를 차례로 부르는 것.
- 그래서 조상 하나가 자손 전체의 이벤트를 받는 **위임(delegation)** 이 가능해진다.

쉬운 예: 아파트 단지 택배다.
- 택배가 단지 정문 → 동 → 층 → 호실로 내려가고(캡처), 호실에 닿은 뒤 수령 확인이 거꾸로 올라간다(버블).
- 경비실(조상) 한 곳이 단지로 들어오는 택배를 한자리에서 기록할 수 있다. 새로 입주한 호실도 따로 등록할 필요가 없다.

똑같은 구조다.\
대신 중간 층이 "여기서 멈춰"(`stopPropagation`)라고 하면 경비실은 그 택배를 못 본다.

실무 예:
- 무한 스크롤 목록에서 행마다 리스너를 달면 새로 붙은 행이 클릭에 반응하지 않는다. 목록에 위임하면 반응한다(아래 실험).
- 모달 컴포넌트가 내부 클릭에 `stopPropagation`을 걸자, 문서 레벨의 분석 로깅·"바깥 클릭 닫기"가 깨졌다.
- SPA에서 화면을 오갈 때마다 `window`에 `resize` 리스너를 붙이고 떼지 않아, 떼어 낸 DOM이 메모리에 남았다(아래 실험: 300회 뒤 노드 +15,900).

## 동작·원리

### 1. DOM 트리 — 노드와 트리 순서

```text
  Document
   └─ html (Element)
       ├─ head
       └─ body
           ├─ div#box
           │   └─ button#btn
           │       └─ "btn" (Text)
           └─ div#list
  트리 순서 = 전위 깊이 우선 순회(preorder DFS): Document, html, head, body, div#box, button, "btn", div#list
```

- DOM 표준은 노드 트리와 **트리 순서**(전위 깊이 우선)를 정의한다. `querySelectorAll`의 결과 순서, `compareDocumentPosition`이 이 순서를 따른다. → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md), [web-api/01 문서와 노드 트리](../../../languages/web-api/01-document-and-node-tree/2-summary.md)
- 노드 종류: Document, Element, Text, Comment, DocumentFragment(그림자 루트 포함) 등. 이벤트를 받을 수 있는 것은 `EventTarget`을 구현한 객체다 — 노드뿐 아니라 `window`, `AbortSignal`, `XMLHttpRequest`도 그렇다.

### 2. 이벤트 디스패치 — 경로를 먼저 정하고, 거꾸로 한 번·바로 한 번

```text
  경로(path) 계산: 대상 → 부모 → … → Document → Window      (디스패치 시작 시 한 번)

  [캡처 패스] path를 거꾸로(바깥 → 안)                [버블 패스] path를 바로(안 → 바깥)
   Window      CAPTURING_PHASE(1) capture 리스너        button   AT_TARGET(2)  비-capture 리스너
   Document    CAPTURING_PHASE(1)                      div#box  BUBBLING_PHASE(3)  ← bubbles=false면 건너뜀
   html        CAPTURING_PHASE(1)                      body     BUBBLING_PHASE(3)
   body        CAPTURING_PHASE(1)                      html     BUBBLING_PHASE(3)
   div#box     CAPTURING_PHASE(1)                      Document BUBBLING_PHASE(3)
   button      AT_TARGET(2)  capture 리스너만           Window   BUBBLING_PHASE(3)
```

- DOM 표준 2.9 Dispatching events
  - 경로를 먼저 만든다(`get the parent`가 null을 돌려줄 때까지). 문서에 붙은 일반 노드의 클릭이면 Window까지 간다. 분리된 노드, `composed: false`인 섀도 트리 안 이벤트(섀도 루트에서 멈춤), `load` 이벤트(Document가 Window를 부모로 돌려주지 않음)는 더 짧다.
  - "For each item of event's path, in reverse order" — 캡처 패스. 대상이면 `AT_TARGET`, 아니면 `CAPTURING_PHASE`로 "capturing" 호출.
  - "For each item of event's path" — 버블 패스. 대상이면 `AT_TARGET`, 아니면 `bubbles`가 false일 때 건너뛰고 `BUBBLING_PHASE`로 "bubbling" 호출.
  - inner invoke: "capturing"이면 `capture`가 false인 리스너를, "bubbling"이면 `capture`가 true인 리스너를 건너뛴다.
- 결과: **대상에서도 capture 리스너가 비-capture 리스너보다 먼저** 불린다. 등록 순서와 무관하다(아래 실험에서 버블 리스너를 먼저 등록했는데도 캡처가 먼저였다).
- 리스너 목록은 경로 항목마다 invoke할 때 복제된다("Let listeners be a clone of … event listener list"). 그래서 이미 복제한 그 노드·그 단계의 목록에 **추가한** 리스너는 그 호출에서 안 불린다. 아직 invoke하지 않은 조상(버블 쪽)에 추가하면 같은 이벤트에서 불릴 수 있다. **제거한** 리스너는 `removed` 표시 때문에 안 불린다.
  - *`target` vs `currentTarget`*: `target`은 이벤트가 향한 노드, `currentTarget`은 지금 리스너가 달린 노드. → [web-api/16 전파 3단계](../../../languages/web-api/16-event-propagation-phases/2-summary.md)

### 실험: 실제 클릭의 전파 순서

환경: headless Chrome 151.0.7922.173, Playwright `playwright-core`(`page.click` → CDP 실제 마우스 입력), Node 20, 127.0.0.1 로컬 페이지. `window`·`document`·`body`·`div#box`·`button`에 버블 리스너를 **먼저**, 캡처 리스너를 **나중에** 등록. 괄호 안은 `eventPhase`.

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 3회 같은 출력)

```text
(a) 실제 클릭 전파 순서:
   window:캡처(1)
   document:캡처(1)
   body:캡처(1)
   div#box:캡처(1)
   button:캡처(2)
   button:버블(2)
   div#box:버블(3)
   body:버블(3)
   document:버블(3)
   window:버블(3)
```

- 표준 그림과 같다. `button`에서는 두 리스너 모두 `eventPhase` 2(AT_TARGET)였고, 캡처 리스너가 먼저 불렸다.

같은 버튼에 리스너 L1(안에서 `Promise.then`)·L2를 달고, 실제 클릭과 스크립트의 `b.click()`을 비교했다(`e04b-micro-between.js`).

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04)

```text
실제 클릭   : L1 → micro → L2
b.click()  : L1 → L2 → click() 반환 → micro
```

- 실제 입력: 리스너 콜백 하나가 끝나면 JS 스택이 비어 마이크로태스크 체크포인트가 돈다(HTML 표준 "clean up after running script"). 그래서 L1의 `then`이 L2보다 먼저다.
- 스크립트 디스패치: `click()`을 부른 스크립트가 스택에 남아 있어 체크포인트가 돌지 않는다. `then`은 호출한 스크립트가 끝난 뒤에 돈다. 같은 리스너 코드라도 이벤트가 어디서 왔는지에 따라 순서가 달라진다 — 테스트에서 `el.click()`으로 재현한 순서가 실제 사용자 입력과 다를 수 있다.

### 3. 멈추기 — `stopPropagation` · `stopImmediatePropagation` · `preventDefault`

```text
  stopPropagation()          "stop propagation flag" 설정 → 다음 invoke부터 안 감(지금 호출의 남은 리스너는 계속)
  stopImmediatePropagation() 위 + "stop immediate propagation flag" → 지금 호출의 남은 리스너도 안 부름
  preventDefault()           "canceled flag" 설정 → 전파와 무관, 기본 동작(링크 이동·체크·스크롤)만 취소
                             단, cancelable=false거나 passive 리스너 안이면 무시
```

- DOM 표준: `stopPropagation()`은 "this's stop propagation flag를 설정"한다. invoke는 그 플래그가 서 있으면 다음 경로 항목에서 바로 돌아온다. 대상 노드는 캡처 쪽·버블 쪽 두 번 invoke되므로, 대상의 capture 리스너에서 멈추면 같은 대상의 비-capture 리스너도 불리지 않는다.
- 전파 중단은 **위임의 적**이다. 자손에서 멈추면 그 위의 위임 리스너가 이벤트를 못 본다. → [web-api/17 stopPropagation vs preventDefault](../../../languages/web-api/17-stoppropagation-vs-preventdefault/2-summary.md)
- *passive 리스너*: `preventDefault()`를 부르지 않겠다고 약속한 리스너. 브라우저는 스크롤을 리스너 실행과 병렬로 시작할 수 있다. DOM 표준의 "default passive value"는 `touchstart`·`touchmove`·`wheel`·`mousewheel` 리스너를 `window`·`document`·`html`·`body`에 달 때 기본값을 true로 둔다. → [web-api/19 passive와 스크롤](../../../languages/web-api/19-passive-and-scroll/2-summary.md)

### 4. 위임 — 조상 하나 + `closest()`

```text
  ul#list ◀── 리스너 1개: e.target.closest('.item') 로 실제 항목을 되찾음
   ├ li.item  (리스너 없음)
   ├ li.item  (리스너 없음)
   └ li.item  ← 나중에 추가돼도 조상 리스너가 받음
```

- 버블 단계 위임은 버블링하는 이벤트(`click`, `input`, `keydown`, `focusin` 등)에만 된다. 버블하지 않는 이벤트도 조상의 캡처 리스너로는 받을 수 있다. `focus`·`blur`·`mouseenter`·`load`(요소)는 버블하지 않는다 — 각각 `focusin`/`focusout`, `mouseover`를 쓰거나 캡처 리스너로 받는다. → [web-api/18 이벤트 위임](../../../languages/web-api/18-event-delegation/2-summary.md)
- `e.target`은 항목 안의 아이콘·텍스트일 수 있다. 그래서 `closest()`로 항목까지 올라가고, 그 항목이 위임 조상 안에 있는지 확인한다.

### 실험: 위임 vs 개별 리스너, 그리고 `stopPropagation`

환경: 위와 같음. 버튼 1,000개를 만들며 (가) 버튼마다 리스너 (나) `#list`에 위임 리스너 하나. CDP `Performance.getMetrics`의 `JSEventListeners` 차이(GC 후). 이어서 ① 기존 항목 클릭 ② 생성 뒤 추가한 항목 클릭 ③ 자기 자신에 `stopPropagation` 리스너를 단 항목 클릭 — 각각 카운터가 올랐는지.

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 3회 같은 출력)

```text
(b) 개별 리스너: 항목 1000개 만들 때 JSEventListeners +1000, 처리 여부 [기존 항목, 나중 추가 항목, 자기에 stopPropagation 단 항목] = [O, X, O]
(b) 위임: 항목 1000개 만들 때 JSEventListeners +1, 처리 여부 [기존 항목, 나중 추가 항목, 자기에 stopPropagation 단 항목] = [O, O, X]
```

- 리스너 수: 1000 대 1.
- 나중에 추가한 항목: 개별 방식은 놓치고, 위임은 받는다.
- `stopPropagation`: 같은 노드의 다른 리스너(개별 방식의 카운터)는 그대로 불렸다. 조상의 위임 리스너는 못 받았다. 위임 쪽 약점이다.

### 5. 리스너 수명과 누수

```text
  window ──(강한 참조)──▶ 리스너 함수 ──(클로저)──▶ el (떼어 낸 div + 자손 52개)
     │                                         └─ GC가 못 거둠 = detached DOM 누수
     └─ AbortController.abort() 또는 removeEventListener 로 고리를 끊어야 회수 가능
```

- 오래 사는 대상(`window`·`document`·전역 이벤트 버스)에 단 리스너는, 그 클로저가 붙든 노드를 같이 살린다. 노드를 DOM에서 떼어도 회수되지 않는다.
- 해제 방법: `removeEventListener`(같은 함수 참조·같은 `capture` 값 필요), `{ once: true }`, `{ signal }` + `AbortController.abort()`. → [web-api/20 리스너 수명](../../../languages/web-api/20-listener-lifetime/2-summary.md)

### 실험: mount·unmount 반복과 누수

환경: 위와 같음. "컴포넌트" 하나 = `div` + 자손 52개(총 53노드)를 붙이고 `window`에 `resize` 리스너(클로저가 `div`를 참조)를 단 뒤 `div`를 뗀다. 100회씩 3번, 매번 `HeapProfiler.collectGarbage` 2회 후 `Nodes`·`JSEventListeners` 차이.

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 3회 같은 출력)

```text
(c) 해제 안 함: mount·unmount 100·200·300회 후(GC 뒤) → Nodes +5300 / JSEventListeners +100 → Nodes +10600 / JSEventListeners +200 → Nodes +15900 / JSEventListeners +300
(c) AbortController 해제: mount·unmount 100·200·300회 후(GC 뒤) → Nodes +0 / JSEventListeners +0 → Nodes +0 / JSEventListeners +0 → Nodes +0 / JSEventListeners +0
```

- 해제하지 않으면 회당 53노드·리스너 1개가 GC 뒤에도 남아 선형으로 쌓였다. `signal`로 해제하면 0이었다.

## 쓰이는 자료구조·알고리즘

- **트리 + 전위 깊이 우선 순회**: 트리 순서, 선택자 결과 순서, `TreeWalker`. → [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)
- **이벤트 경로 = 조상 체인을 담은 리스트**: 부모 포인터를 따라 올라가며 한 번 만들고, 거꾸로(캡처)·바로(버블) 두 번 순회한다. 디스패치 중 트리가 바뀌어도 경로는 그대로다.
- **노드별 리스너 리스트**: (type, callback, capture)가 같으면 중복 추가하지 않는 순서 있는 목록. 노드마다 invoke할 때 복제(스냅샷)해 그 순회 중 변경을 막는다 — 반복 중 컬렉션 수정 문제의 표준 해법.
- **`closest()` = 조상 방향 선형 탐색**: 깊이 d에 대해 O(d)마다 선택자 매칭.
- **도달성 기반 GC**: 리스너 목록에서 클로저로, 클로저에서 노드로 이어진 참조가 남으면 회수되지 않는다.

## 적용 — 풀어나가는 법

1. **목록·표·동적 영역은 위임으로.** 조상 하나에 리스너, `closest()`로 항목 찾기, `data-*`로 동작 구분.

```ts
const list = document.querySelector<HTMLUListElement>('#list')!;
list.addEventListener('click', (e) => {
  const item = (e.target as Element).closest<HTMLElement>('[data-id]');
  if (!item || !list.contains(item)) return;          // list 밖 항목 거르기(list 안에 중첩된 다른 위임 영역은 따로 판정해야 한다)
  const action = (e.target as Element).closest<HTMLElement>('[data-action]')?.dataset.action;
  if (action === 'delete') remove(item.dataset.id!);
  else select(item.dataset.id!);
});
```

2. **`stopPropagation` 대신 판정으로.** "바깥 클릭 닫기"는 내부 클릭을 막지 말고 문서 리스너에서 `e.composedPath().includes(modal)`로 가린다. 꼭 막아야 하면 이유를 주석으로 남기고, 위임 리스너가 위에 있는지 확인한다.
3. **리스너 수명을 소유자에 묶는다.** 컴포넌트마다 `AbortController` 하나, 언마운트에서 `abort()`.

```ts
class Widget {
  #ac = new AbortController();
  mount(el: HTMLElement) {
    window.addEventListener('resize', () => this.layout(el), { signal: this.#ac.signal });
    document.addEventListener('keydown', e => this.onKey(e), { signal: this.#ac.signal });
  }
  unmount() { this.#ac.abort(); }                     // 한 번에 전부 해제
  layout(el: HTMLElement) {} onKey(e: KeyboardEvent) {}
}
```

4. **스크롤 관련 리스너는 passive로.** `preventDefault()`가 필요 없으면 `{ passive: true }`. 필요하면 범위를 좁힌 요소에만 non-passive로 단다.
5. **진단 도구.**
   - DevTools Elements → Event Listeners 패널, 콘솔 `getEventListeners(el)`(DevTools 전용).
   - Memory 패널 힙 스냅샷에서 "Detached" 필터로 떼어 낸 DOM 찾기.
   - 자동화: CDP `Performance.getMetrics`의 `JSEventListeners`·`Nodes`를 GC 뒤 비교(위 실험).

## 장애 시나리오와 대처

### 1. 리스너 누수 → 메모리 증가 (⚠ 커리큘럼)

- **현상**: SPA를 오래 쓰면 점점 느려지고 탭이 재로드된다.
- **보이는 형태**: 화면 전환을 반복할수록 `JSEventListeners`·`Nodes`가 GC 뒤에도 선형 증가(실험: 300회 → 리스너 +300, 노드 +15,900). 힙 스냅샷의 Detached `HTMLDivElement`.
- **원인**: `window`·`document`·전역 버스에 단 리스너를 언마운트 때 떼지 않음. `removeEventListener`에 다른 함수 참조(매번 새 화살표 함수)나 다른 `capture` 값을 넘겨 실제로는 안 떨어짐.
- **대처**: `AbortController` signal로 수명 묶기(실험: +0), 프레임워크의 정리 훅(예: React `useEffect` cleanup)에서 해제, 누수 회귀 테스트(전환 N회 후 `Nodes` 비교).

### 2. `stopPropagation` 남용 → 위임 핸들러 무력화 (⚠ 커리큘럼)

- **현상**: 특정 컴포넌트 안에서의 클릭만 분석 로그가 빠지거나, 드롭다운 "바깥 클릭 닫기"가 안 된다.
- **보이는 형태**: 문서·목록 레벨 위임 리스너가 그 영역의 이벤트만 못 받는다(실험: 위임 쪽 ③ X).
- **원인**: 하위 컴포넌트가 자기 처리 뒤 `e.stopPropagation()`을 호출.
- **대처**: 전파는 두고 판정으로 거른다(`composedPath()`, `defaultPrevented` 확인). 정말 막아야 하는 리스너는 캡처 단계의 상위 리스너가 먼저 처리하게 설계한다.

### 3. 동적으로 추가한 항목이 클릭에 반응하지 않음

- **현상**: 무한 스크롤·필터 후 새로 그린 행이 반응하지 않는다.
- **보이는 형태**: 처음 렌더한 행만 동작(실험: 개별 방식 ② X).
- **원인**: 리스너를 최초 렌더 시점의 요소에만 달았다. `innerHTML`로 다시 그리면 이전 요소와 리스너가 함께 사라진다.
- **대처**: 안정적인 조상에 위임한다.

### 4. 버블하지 않는 이벤트를 위임하려다 실패

- **현상**: 폼 컨테이너에 `focus`·`blur` 리스너를 달았는데 입력란 포커스를 못 잡는다.
- **보이는 형태**: 리스너가 한 번도 불리지 않는다.
- **원인**: `focus`·`blur`는 `bubbles`가 false다. 버블 패스에서 조상은 건너뛴다(표준: "If event's bubbles attribute is false, then continue").
- **대처**: `focusin`·`focusout`을 쓰거나 `{ capture: true }`로 캡처 단계에서 받는다.

### 5. 스크롤 리스너가 스크롤을 막음

- **현상**: 모바일에서 스크롤 시작이 늦고 버벅인다.
- **보이는 형태**: DevTools 콘솔의 위반(Violation) 메시지 "Added non-passive event listener to a scroll-blocking 'touchstart' event. Consider marking event handler as 'passive' to make the page more responsive. See https://www.chromestatus.com/feature/5745543795965952"(Chromium `third_party/blink/renderer/core/dom/events/event_target.cc` — 스크롤 차단 이벤트에 `passive`를 명시하지 않고 문서 최상위 노드가 아닌 곳에 달 때 보고), 스크롤 시작 지연.
- **원인**: 문서 수준이 아닌 요소에 단 `touchstart`·`wheel` 리스너는 기본 passive가 아니다. 브라우저는 그 리스너가 `preventDefault()`를 부를지 기다려야 한다.
- **대처**: `{ passive: true }`를 명시한다. 막아야 하는 영역(지도·캔버스)에만 non-passive.

## 핵심 문장

- DOM은 문서를 노드 트리로 두고, 트리 순서는 전위 깊이 우선 순회다.
- 디스패치는 경로를 먼저 정한 뒤, 거꾸로 한 번(캡처)·바로 한 번(버블) 돈다. 대상에서도 캡처 리스너가 먼저다(실험).
- 위임은 버블링 덕분에 조상 리스너 하나로 동적 자손까지 받는다(실험: 리스너 1000 대 1, 나중 추가 항목 O).
- `stopPropagation`은 다음 노드로의 전파를 끊어 위의 위임 리스너를 무력화한다. 기본 동작 취소는 `preventDefault`이고 둘은 별개다.
- 오래 사는 대상에 단 리스너는 클로저가 붙든 DOM을 살린다. `AbortController`로 수명을 묶으면 GC 뒤 증가가 0이었다(실험).

## 관련 주제·근거

- 선행
  - [03-event-loop](../03-event-loop/2-summary.md) — 사용자 입력 이벤트는 태스크로 디스패치되고, 리스너 콜백이 끝나 스크립트 스택이 빌 때마다 마이크로태스크 체크포인트가 돈다(스크립트의 `dispatchEvent` 호출 안에서는 스택이 비지 않아 돌지 않는다)
- 후속·연결
  - [02-rendering-pipeline](../02-rendering-pipeline/2-summary.md) — DOM 변경이 스타일·레이아웃을 더럽히는 경로
  - [01-browser-architecture](../01-browser-architecture/2-summary.md) — 입력이 브라우저 프로세스에서 렌더러로 라우팅되는 경로
  - [11 `accessibility-basics`](../11-accessibility-basics/2-summary.md)(div 버튼·키보드 이벤트), [17 `list-virtualization`](../17-list-virtualization/2-summary.md), [18 `ui-rerender-and-memoization`](../18-ui-rerender-and-memoization/2-summary.md)
  - 문법: [web-api/01](../../../languages/web-api/01-document-and-node-tree/2-summary.md), [web-api/02 라이브 컬렉션](../../../languages/web-api/02-element-queries-and-live-collections/2-summary.md), [web-api/15 리스너 등록](../../../languages/web-api/15-listener-registration/2-summary.md), [web-api/16](../../../languages/web-api/16-event-propagation-phases/2-summary.md), [web-api/17](../../../languages/web-api/17-stoppropagation-vs-preventdefault/2-summary.md), [web-api/18](../../../languages/web-api/18-event-delegation/2-summary.md), [web-api/19](../../../languages/web-api/19-passive-and-scroll/2-summary.md), [web-api/20](../../../languages/web-api/20-listener-lifetime/2-summary.md), [web-api/21 사용자 정의 이벤트](../../../languages/web-api/21-custom-events/2-summary.md)
  - 자료구조: [algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md), [data-structure/08-graph](../../data-structure/08-graph/2-summary.md)
- 문서
  - WHATWG DOM 표준 <https://dom.spec.whatwg.org/> — 2.7 Interface EventTarget(event listener: type·callback·capture·passive·once·signal·removed, default passive value), 2.2 Interface Event(eventPhase 상수, stopPropagation·stopImmediatePropagation 단계), 2.9 Dispatching events(경로 역순 capturing·정순 bubbling, bubbles=false 건너뜀, inner invoke의 capture 필터, 리스너 목록 복제), 1.1 Trees("tree order is preorder, depth-first traversal"), 4.2 Node tree(노드 종류)
- 실험 목록(headless Chrome 151.0.7922.173, Playwright `playwright-core`, Node 20, 127.0.0.1 로컬 페이지, 스로틀 없음, 2026-10-04)
  - `e04-events.js` (a) 실제 클릭 전파 순서·eventPhase (b) 개별 vs 위임 리스너 1,000개의 `JSEventListeners`, 기존·추가·`stopPropagation` 항목 처리 여부 (c) mount·unmount 100·200·300회 후 GC 뒤 `Nodes`·`JSEventListeners`(해제 안 함 vs AbortController) — 3회 같은 출력
  - `e04b-micro-between.js`: 리스너 두 개 사이의 마이크로태스크 — 실제 클릭 vs `el.click()`
