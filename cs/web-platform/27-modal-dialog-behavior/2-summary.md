# web-platform/27-modal-dialog-behavior — 모달의 상호작용 계약: 바깥 클릭·ESC 스택·포커스 가두기·스크롤 잠금 — 정리 (힌트)

## 해결하는 문제

모달은 "화면 위에 상자 하나 띄우기"로 끝나지 않는다. 상자를 띄운 순간 사용자는 네 가지를 기대한다.

```text
기대                                   이게 깨지면
① 상자 바깥을 누르면 닫힌다            → 열자마자 닫힘 / 상자 안 드롭다운을 눌렀는데 닫힘
② ESC를 누르면 맨 위 상자만 닫힌다      → ESC 한 번에 겹친 상자가 전부 사라짐
③ Tab은 상자 안에서만 돈다              → 포커스가 뒤 페이지로 빠져 보이지 않는 버튼이 눌림
④ 상자가 떠 있는 동안 배경은 안 움직인다 → 위 상자만 닫았는데 배경이 스크롤됨
```

쉬운 예: 은행 창구의 "번호표 화면"이 떠 있다. 손님이 화면 밖 아무 데나 누르면 화면이 닫혀야 한다. "취소"(ESC)를 누르면 맨 위 안내창 하나만 닫혀야 한다. 화면이 떠 있는 동안 뒤의 메뉴 버튼은 눌리면 안 된다.

똑같은 구조다: 웹의 모달은 "지금 이 상자가 화면의 주인"이라는 **상태**를 가진다. 네 기대는 모두 그 상태를 입력 장치(포인터·키보드·스크롤)마다 지키는 규칙이다.

실무 예: 결제 확인 모달 안에 카드사 선택 드롭다운이 있고, 그 위에 "약관 보기" 모달이 또 뜬다. 드롭다운은 부모 `overflow`에 잘리지 않으려고 portal로 `body`에 붙어 있다. 이 화면 하나에서 네 기대가 한꺼번에 시험받는다.

- 이 네 규칙을 WAI-ARIA APG "Dialog (Modal) Pattern"은 키보드 상호작용(Tab·Shift+Tab 순환, Escape로 닫기)과 포커스 이동(열 때 안으로, 닫을 때 연 요소로)으로 정리한다. 바깥 클릭과 스크롤 잠금은 APG의 키보드 표에 없는 실무 관행이다.
  - *모달*: 떠 있는 동안 그 아래 화면과의 상호작용을 막는 대화상자. APG는 모달 아래 창을 inert(조작 불가)로 본다.
  - *portal*: 컴포넌트(논리) 부모와 다른 DOM 위치(대개 `body` 끝)에 요소를 그리는 기법. [26-portals-and-two-trees](../26-portals-and-two-trees/2-summary.md)
    - 흔한 오해: "DOM이 body에 있으니 논리적으로도 바깥이다" — 논리 부모는 여전히 모달 안의 버튼이다.

## 동작·원리

네 규칙을 하나씩 본다. 각 규칙마다 **처음 그린 그림 → 실제 그림 → 코드** 순서다.

### 1. 바깥 클릭 — 판정(어느 트리에 묻나)과 시점(어느 이벤트로 듣나)

바깥 클릭에는 질문이 두 개 들어 있다.

```text
질문 A (판정): 이 클릭은 모달 안쪽인가?        → 관계 질문 → 논리 트리에 묻는다
질문 B (시점): 어느 이벤트·단계로 들어야 하나?  → 시간 질문 → pointerdown + 캡처
```

#### 1-1. 판정 — DOM `contains`는 portal 앞에서 틀린다

모달 안에서 드롭다운을 열면 드롭다운은 portal로 `body`에 붙는다.

```text
DOM 트리 (물리 위치)                    논리 트리 (관계)
body                                   page
├ #app … [모달 열기]                     └ modal
├ div[role=dialog]   ← 모달                └ dialog
│ └ [메뉴 열기]                                └ [메뉴 열기]
└ div (메뉴)         ← dialog 밖!                  └ 메뉴 (portal)
  └ [메뉴 항목]                                        └ [메뉴 항목]
```

- 물리: `dialog.contains(메뉴 항목)` → `false` → "바깥" → 닫힘.
- 논리: 메뉴 항목 → 메뉴 → [메뉴 열기] → dialog → "안쪽" → 유지.

```javascript
// 논리 부모(portal로 띄운 요소만 등록)를 우선 따라 올라간다
const logicalParent = new WeakMap(); // 요소 → 논리 부모 요소

function isLogicallyInside(target, container) {
  for (let n = target; n; n = logicalParent.get(n) ?? n.parentNode) {
    if (n === container) return true;
  }
  return false; // 루트까지 갔는데 못 만남 → 바깥
}
```

- 판정은 클릭된 요소에서 출발해 부모 포인터를 따라 올라간다. portal로 띄운 요소에서만 DOM 부모 대신 논리 부모로 건너간다.
  - *부모 포인터 상향 탐색*: 노드에서 부모 링크를 따라 루트 쪽으로 올라가며 목표를 찾는 탐색. 깊이 d면 O(d).

### 실험: 같은 메뉴 항목, 두 트리의 답

dialog를 `body`에 붙이고, 그 안의 [메뉴 열기] 버튼을 논리 부모로 하는 메뉴를 `body` 끝에 따로 붙였다. 위 `isLogicallyInside`로 판정했다.

(실험, Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04)

```text
[D2] DOM 경로(parentNode): item → DIV → BODY → HTML → #document
[D2] 논리 경로(논리 부모 우선): item → DIV → menuBtn → dialog → BODY → HTML → #document
[D2] dialog.contains(item) = false / isLogicallyInside(item, dialog) = true
```

- DOM 경로에는 dialog가 없다. 논리 경로는 메뉴 `DIV`에서 [메뉴 열기]로 건너가 dialog를 만난다.

#### 1-2. 시점 — 여는 click이 닫기 리스너에 걸린다

흔한 첫 구현은 이렇다.

```javascript
openButton.addEventListener('click', () => {
  showModal();
  document.addEventListener('click', (e) => {          // 바깥 클릭 닫기
    if (!isLogicallyInside(e.target, dialog)) closeModal();
  });
});
```

증상: 모달이 열리지 않는다(정확히는 열리자마자 닫힌다).

처음 그린 그림과 실제는 이렇게 다르다.

```text
처음 그린 그림                                  실제
"닫히는 동작이 등록돼 있어야 닫히는 거 아냐?        닫기 리스너는 click 핸들러 "안에서"
 열 때는 아직 닫기 리스너가 없잖아"                등록됐다. 그 click은 아직 올라가는 중이다.

click ① 열기 ─────────── 끝                       click ① ── button ─ … ─ (핸들러: 열기 + 닫기 등록)
click ② (나중) 바깥 → 닫기                                  ─ … ─ body ─ document ◀ 방금 등록한 닫기 실행
                                                  click 하나가 열기·닫기에 둘 다 쓰였다
```

또 하나의 오해가 겹친다.

```text
처음 그린 그림                              실제
button → #card(위임 지점, 처리) ■ 멈춤      button → #card(처리) → … → body → document
                                           처리돼도 버블은 계속 올라간다
```

- 네이티브 버블링은 "누가 처리했다"고 멈추지 않는다. 멈추는 것은 리스너가 `stopPropagation()`을 불렀을 때뿐이다. [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md)
  - *버블 단계*: 이벤트가 대상에서 조상 쪽(`document`·`window`)으로 거꾸로 올라가며 리스너를 부르는 단계.
    - 흔한 오해: "위임 지점에서 핸들러가 실행되면 이벤트가 소비된다" — 소비라는 개념은 없다. 다음 조상으로 계속 간다.

왜 방금 붙인 리스너가 실행되나. DOM 표준의 디스패치는 **경로를 먼저 정하고**, 경로 위 노드에 들를 때마다 **그 순간의 리스너 목록을 복사해서** 부른다(WHATWG DOM §2.9 "Dispatching events", invoke 단계 "Let listeners be a clone of … event listener list").

```text
click 디스패치 (경로는 시작할 때 고정)
window ─▶ document ─▶ … ─▶ button                    ← 캡처 단계 (이미 지나감)
                           button ◀ 지금 여기: 핸들러 실행 중
                                    document에 리스너 추가 ★
window ◀─ document ◀─ … ◀─ button                    ← 버블 단계 (아직 안 감)
          ▲ 도착하는 순간 목록을 복사 → ★ 포함 → 실행

추가한 위치·단계별로 이번 이벤트에서 실행되나
┌────────────────────────────┬──────────┬──────────────────────────────┐
│ 어디에 추가했나             │ 실행?    │ 이유                          │
├────────────────────────────┼──────────┼──────────────────────────────┤
│ document, 버블             │ 실행     │ 아직 안 들른 노드             │
│ document, 캡처             │ 안 함    │ 캡처 단계는 이미 지나감        │
│ 지금 처리 중인 button 자신   │ 안 함    │ button 목록은 이미 복사됨      │
└────────────────────────────┴──────────┴──────────────────────────────┘
```

### 실험: 디스패치 도중에 붙인 리스너는 언제 실행되나

click 핸들러 안에서 리스너 세 개(document 버블·document 캡처·button 자신)를 붙이고 두 번 클릭했다.

```javascript
let n = 0;
btn.addEventListener('click', () => {
  const k = ++n;
  out.push(`button 핸들러(click ${k}): 리스너 3개 등록`);
  document.addEventListener('click', () => out.push(`  document 버블 리스너[등록 click ${k}] 실행`));
  document.addEventListener('click', () => out.push(`  document 캡처 리스너[등록 click ${k}] 실행`), true);
  btn.addEventListener('click', () => out.push(`  button 추가 리스너[등록 click ${k}] 실행`));
});
btn.click(); btn.click();
```

(실험, Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04)

```text
── click 1
button 핸들러(click 1): 리스너 3개 등록
  document 버블 리스너[등록 click 1] 실행
── click 2
  document 캡처 리스너[등록 click 1] 실행
button 핸들러(click 2): 리스너 3개 등록
  button 추가 리스너[등록 click 1] 실행
  document 버블 리스너[등록 click 1] 실행
  document 버블 리스너[등록 click 2] 실행
```

- click 1: 같은 click에서 실행된 것은 **document 버블** 하나다. 캡처와 button 자신에 붙인 것은 click 2부터 실행됐다.
- click 2의 마지막 줄: 이번 click 도중에 붙인 document 버블 리스너가 또 같은 click에 실행됐다. 이것이 "열자마자 닫힘"의 정확한 모양이다.

같은 구조를 위임 지점(`#card`)에서 열고, `stopPropagation` 유무만 바꿔 돌렸다.

(실험, Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04)

```text
[A3] stopPropagation=false: #card(위임 지점) 핸들러: 열기 / document 닫기 리스너 실행 → 닫힘 → 최종 open=false
[A3] stopPropagation=true: #card(위임 지점) 핸들러: 열기 → 최종 open=true
```

- `stopPropagation`을 부르는 버튼으로 열면 버그가 **가려진다**. 그래서 "어떤 버튼으로 열면 되고 어떤 버튼은 안 된다"는 재현이 들쭉날쭉한 버그가 된다.

#### 1-3. 해결 — 닫기를 다른 이벤트(`pointerdown`)에 건다

클릭 한 번은 이벤트 여러 개다. 마우스 기준 순서는 UI Events·Pointer Events 명세가 정한다 (절 번호 미확인) [?].

```text
시간 →   pointerdown ─ mousedown ─ (뗌) ─ pointerup ─ mouseup ─ click
                                                                 │
                                               여는 핸들러: 모달 열기 + 닫기 리스너 등록
                                                                 │
click으로 닫기:        ──────────────────────────────── 같은 click을 받음 → 닫힘 ✗
pointerdown으로 닫기:  ── 이번 pointerdown은 이미 끝남 ── 다음에 누를 때부터 감지 ✓
```

```javascript
function onPointerDown(e) {
  const top = stack[stack.length - 1];
  if (!top) return;
  if (isLogicallyInside(e.target, top.dialog)) return;
  top.close('outside');
}
// 모달이 1개 이상일 때만 붙인다. 세 번째 인자 true = 캡처
document.addEventListener('pointerdown', onPointerDown, true);
```

`pointerdown`과 캡처는 **서로 다른 문제**를 막는다.

| 선택 | 막는 문제 |
|---|---|
| `pointerdown`(click 대신) | 여는 click이 닫기 판정에도 쓰임 → 열자마자 닫힘 |
| 캡처(버블 대신) | 앱 코드의 `stopPropagation`에 바깥 감지가 막힘 |

- *캡처 단계*: `window`에서 대상 쪽으로 내려가며 리스너를 부르는 단계. 내려가는 길에서 먼저 받으므로 아래 요소의 `stopPropagation`에 막히지 않는다.
  - 흔한 오해: "click을 캡처로 들으면 열자마자 닫힘도 해결된다" — 이 경우는 맞다(document 캡처는 여는 핸들러보다 먼저 지나감, 위 실험 표). 다만 드래그 문제(아래)는 남는다.
- click을 피하는 이유 하나 더: 입력창 안에서 눌러 텍스트를 끌다 오버레이에서 떼면, click은 누른 요소와 뗀 요소의 공통 조상에서 난다고 알려져 있다 (UI Events 원문 미대조) [?]. 그러면 "바깥"으로 오판될 수 있다. `pointerdown`은 누른 지점 하나로만 판정한다.
- 알려진 위험(미검증): `pointerdown`에서 모달을 닫으면 그 뒤의 `click`이 모달이 사라진 자리 아래 요소에 떨어질 수 있다(click-through) [?]. 이 노트의 실험 환경(jsdom)은 실제 입력 시퀀스와 hit-test를 흉내 내지 않아 재지 못했다. 실브라우저에서 오버레이 아래 버튼을 두고 확인해야 한다.

### 실험: 닫기를 pointerdown 캡처에 걸었을 때의 순서

실제 브라우저 순서를 손으로 재현해 `pointerdown → mousedown → pointerup → mouseup → click`을 차례로 디스패치했다. 여는 click 핸들러가 document에 pointerdown 캡처 리스너를 붙인다.

(실험, Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04)

```text
  pointerdown 디스패치 끝 (open=false)
  mousedown 디스패치 끝 (open=false)
  pointerup 디스패치 끝 (open=false)
  mouseup 디스패치 끝 (open=false)
  button click: 열기 + pointerdown 캡처 리스너 등록
  click 디스패치 끝 (open=true)
  document 캡처 pointerdown 리스너: target=#BODY → 바깥 → 닫기
  (다음) body pointerdown 디스패치 끝 (open=false)
```

- 여는 click이 끝난 뒤에도 `open=true`다. 다음 pointerdown(바깥)에서야 닫혔다.
- 순서 자체는 손으로 디스패치한 것이다. 실브라우저가 이 순서로 내는지는 이 실험이 보이지 않는다(명세 근거는 위 [?]).

### 2. ESC — 맨 위 모달만 (모달 스택)

#### 2-1. 처음 그린 그림 vs 실제

각 모달이 열릴 때 자기 ESC 리스너를 document에 붙이는 구현을 생각한다.

```javascript
function openModal(parentModal) {
  const modal = createModalBox(parentModal);
  const onKey = (e) => { if (e.key === 'Escape') modal.close('escape'); }; // 맨 위 확인 없음
  document.addEventListener('keydown', onKey, true);
  return modal;
}
```

- `onKey`는 클로저다. 호출마다 새로 생기고, 그 호출의 `modal` 하나만 기억한다. [language/07](../../language/07-scope-closures-first-class-functions/2-summary.md)

```text
openModal() 1번째 → modal #1 ←── onKey#1 이 기억
openModal() 2번째 → modal #2 ←── onKey#2 가 기억

document의 keydown 리스너 목록: [onKey#1, onKey#2]   (등록 순서)
```

ESC 한 번에 둘 다 닫힌다. 왜인가?

```text
처음 그린 그림                          실제
(가) 캡처라서 둘이 "동시에" 받는다?      같은 노드의 리스너는 등록 순서대로 하나씩 실행된다.
(나) 부모가 닫히며 자식도 닫힌다?        구조에 따라 (가')·(나) 둘 다 일어난다.
                                       근본 원인은 하나 — "내가 맨 위인가" 확인이 없다.
```

두 구조로 나눠 보면 이렇다.

```text
A. 중첩: #2가 #1 dialog 안에서 열림 (논리 자식)
ESC ─▶ onKey#1 (먼저 등록) "ESC네" → #1 close
          └ 논리 자식부터 정리 → #2 close(reason=destroy) → onKey#2 해제
     ─▶ onKey#2 → 이미 해제됨 → 호출 안 됨
결과: #2(destroy), #1(escape)  — 맨 위가 아닌 #1이 반응해 자식까지 휩쓸었다

B. 형제: #1, #2를 같은 화면에서 따로 엶
ESC ─▶ onKey#1 → #1 close(escape)
     ─▶ onKey#2 → #2 close(escape)
결과: 연쇄가 없어도 두 리스너가 각자 닫았다
```

- A에서 `onKey#2`가 호출되지 않는 것은 표준의 "removed" 표시 때문이다. 목록은 복사됐지만, 해제된 리스너는 inner invoke가 건너뛴다(WHATWG DOM §2.9).
- 캡처·버블과는 무관하다. 버블로 달아도 같은 결과가 난다.

#### 2-2. 해결 — 공유 리스너 하나 + 스택

```javascript
const stack = []; // 열린 순서. 맨 뒤가 맨 위

function onKeyDown(e) {
  const top = stack[stack.length - 1];
  if (!top) return;
  if (e.key === 'Escape') {
    e.preventDefault();
    top.close('escape');
  } else if (e.key === 'Tab') {
    trapTab(e, top.dialog);
  }
}

function pushModal(modal) {
  stack.push(modal);
  if (stack.length === 1) document.addEventListener('keydown', onKeyDown, true); // 0→1에 붙임
}
function removeModal(modal) {
  stack.splice(stack.indexOf(modal), 1);
  if (stack.length === 0) document.removeEventListener('keydown', onKeyDown, true); // 1→0에 뗌
}
```

```text
stack: [#1, #2]  ESC → top = #2 → #2만 닫음 → stack: [#1]
stack: [#1]      ESC → top = #1 → #1 닫음   → stack: []  → 리스너 해제
```

- "다른 모달에 이벤트가 닿지 않게 막는 것"(`stopPropagation`)이 해결이 아니다. 리스너를 하나로 줄이고, 그 리스너가 맨 위를 고르게 만든 것이 해결이다.
- 메뉴·툴팁 같은 비모달 portal은 이 스택에 넣지 않는다. ESC가 메뉴를 "맨 위 모달"로 착각하면 안 되기 때문이다. z-index용 레이어 순서와 모달 스택은 따로 둔다.
  - *스택(LIFO)*: 마지막에 넣은 것을 먼저 꺼내는 자료구조. 모달은 마지막에 연 것이 맨 위다. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md)

### 실험: ESC 한 번 — 구현 × 구조

모달별 리스너(`perModal`)와 공유 리스너+스택(`stack`) 두 구현을 중첩·형제 구조에서 돌렸다. 닫힐 때 자식을 먼저 `destroy`로 닫는다.

(실험, Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04)

```text
[D1 perModal, 중첩] 남은 모달 [] / #2 닫힘(destroy), #1 닫힘(escape)
[D1 perModal, 형제] 남은 모달 [] / #1 닫힘(escape), #2 닫힘(escape)
[D1 stack, 중첩] 남은 모달 [#1] / #2 닫힘(escape)
[D1 stack, 형제] 남은 모달 [#1] / #2 닫힘(escape)
```

- `perModal`은 두 구조 모두 0개가 됐다. 닫힌 이유(reason)가 경로를 드러낸다 — 중첩은 연쇄(destroy), 형제는 각자(escape).
- `stack`은 구조와 상관없이 맨 위 #2만 닫혔다.

### 3. 포커스 — 열 때 안으로, Tab은 가두고, 닫을 때 돌려준다

#### 3-1. 왜 Tab이 빠져나가나

```text
처음 그린 그림                         실제
"모달이 화면 맨 위에 있으니             Tab은 화면이 아니라 DOM 순서(포커스 탐색 순서)를 본다.
 Tab도 모달 안에서 돈다"               오버레이는 마우스만 막는다. 키보드 포커스는 못 막는다.

DOM 순서 (body 위 → 아래)
  [뒤쪽1] [열기]                    ← 어두운 배경 뒤 (보이지만 못 누름)
  [A] [mid] [B]                    ← body 끝의 모달
            │ Tab
            ▼
  다음 요소 없음 → 브라우저 UI(주소창 등) → 다시 문서 처음 [뒤쪽1] → Enter → 보이지 않는 버튼이 눌림
```

- Tab 순서 규칙(양수 `tabindex` 먼저, 나머지 DOM 순서)은 [11-accessibility-basics](../11-accessibility-basics/2-summary.md)의 "키보드 포커스 순서"에 있다. 이 노트는 그 순서를 모달 안에 가두는 방법만 다룬다.
- APG Dialog(Modal) 키보드 표: Tab은 마지막에서 첫 요소로, Shift+Tab은 첫 요소에서 마지막으로 옮긴다.

#### 3-2. 가장자리에서만 개입한다

학습자가 정리한 한 줄: "끝에서 Tab을 누르면 브라우저 UI로 빠지지 않게 first로 돌려준다." 맞다. 거기에 `preventDefault`가 왜 필요한지만 더하면 된다.

```javascript
const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function trapTab(e, dialog) {
  const items = [...dialog.querySelectorAll(FOCUSABLE)]; // DOM 순서
  if (items.length === 0) { e.preventDefault(); dialog.focus(); return; } // dialog에 tabindex=-1
  const first = items[0];
  const last = items[items.length - 1];
  const active = document.activeElement;
  const inside = dialog.contains(active);
  if (e.shiftKey) {
    if (!inside || active === first || active === dialog) { e.preventDefault(); last.focus(); }
  } else if (!inside || active === last) {
    e.preventDefault();
    first.focus();
  }
}
```

```text
Tab 키 → document 캡처 keydown → 맨 위 모달의 trapTab
   지금 포커스가 마지막인가? (또는 모달 밖인가?)
     예     → preventDefault() + first.focus()
     아니오 → 아무것도 안 함 → 브라우저 기본 이동

Tab:       [A] ─▶ [mid] ─▶ [B] ─┐
            ▲  (가운데는 브라우저)  │
            └─────────────────────┘ first.focus()
```

| 부분 | 없으면 |
|---|---|
| `preventDefault()` | `first.focus()` 직후 브라우저가 원래 하던 "다음 요소로 이동"을 마저 해서 [mid]로 간다 (실브라우저 미측정) [?] |
| 가운데는 손대지 않음 | 가운데까지 직접 옮기면 `tabindex` 정렬·숨김 요소 규칙을 다시 만들어야 한다 |
| `!inside` | 포커스가 이미 모달 밖(마우스로 뒤를 눌렀다 등)이면 다음 Tab에서 안으로 되돌리지 못한다 |

#### 3-3. 같은 "안쪽인가"인데 왜 여기서는 DOM에 묻나

바깥 클릭(§1)에서는 DOM `contains`가 틀렸는데, `trapTab`은 `contains`와 `querySelectorAll`을 쓴다.

```text
질문                               성격        묻는 트리
이 클릭이 모달에 속하나 (§1)         관계         논리 트리 (portal 메뉴도 안쪽)
Tab이 다음에 어디로 가나 (§3)       위치·순서     DOM 트리 (브라우저가 DOM 순서로 움직이니까)
```

- 브라우저의 Tab 이동은 논리 트리를 모른다. 그래서 "Tab으로 닿는 요소와 처음·마지막"은 위치 질문이고 DOM에 묻는 것이 맞다.
- 대가: 모달 안에서 연 portal 메뉴의 항목은 DOM상 dialog 밖이라 순환 목록에 들어가지 않는다. 메뉴에 포커스가 있을 때 Tab을 누르면 `!inside`로 모달 첫 요소로 돌아간다. 실무에서는 메뉴가 열리면 포커스를 메뉴로 옮기고 메뉴가 자기 키보드를 처리하는 식으로 푸는 경우가 많다.

#### 3-4. 열 때·닫을 때

| 시점 | 할 일 | 안 하면 |
|---|---|---|
| 열기 직전 | `previous = document.activeElement` 기억 | 돌아갈 곳을 모른다 |
| 연 직후 | 첫 포커스 요소로(없으면 dialog 자체) | 첫 Tab이 "여는 버튼 다음"(뒤 페이지)부터 시작 |
| 닫을 때 | `previous`가 문서에 남아 있으면 `previous.focus()` | 포커스가 `body`로 떨어져 키보드 사용자가 위치를 잃음 |

- APG: 닫을 때 포커스는 연 요소로 돌아가고, 그 요소가 없으면 논리적 흐름에 맞는 다른 요소로 간다.
- 연 직후 포커스 이동은 마이크로태스크(`queueMicrotask`)로 미루는 구현이 있다. 모달을 만든 쪽이 같은 동기 흐름에서 버튼을 다 붙인 뒤에 첫 요소를 찾기 위해서다.
- `<dialog>`의 `showModal()`은 바깥을 inert로 만들어 Tab이 바깥으로 가지 않게 한다. 직접 만든 모달은 이것을 `trapTab`으로 흉내 내는 셈이다. [web-api/14](../../../languages/web-api/14-dialog-popover-scripting/2-summary.md)

### 실험: Tab 가장자리 — 가두기 없음 vs `trapTab`

jsdom은 Tab의 **기본 이동**을 흉내 내지 않는다. 그래서 이 실험은 "가장자리에서 개입했나(`defaultPrevented`, 옮긴 대상)"만 잰다.

(실험, Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04)

```text
[E trap=false]
  mid(가운데)에서 Tab: defaultPrevented=false, active=mid
  B(마지막)에서 Tab: defaultPrevented=false, active=B
  A(처음)에서 Shift+Tab: defaultPrevented=false, active=A
  뒤쪽1(밖)에서 Tab: defaultPrevented=false, active=behind1
  복귀 없이 dialog 제거 → active=body
  previous.focus() 후 → active=opener
[E trap=true]
  mid(가운데)에서 Tab: defaultPrevented=false, active=mid
  B(마지막)에서 Tab: defaultPrevented=true, active=A
  A(처음)에서 Shift+Tab: defaultPrevented=true, active=B
  뒤쪽1(밖)에서 Tab: defaultPrevented=true, active=A
  복귀 없이 dialog 제거 → active=body
  previous.focus() 후 → active=opener
```

- 가운데(mid)는 두 경우 모두 개입하지 않았다. 가장자리와 바깥에서만 `trapTab`이 개입했다.
- 포커스된 요소를 지우면 `activeElement`가 `body`로 떨어졌다. 복귀 코드가 있어야 opener로 간다.

### 4. 배경 스크롤 잠금 — 참조 카운트와 원래 값 복원

#### 4-1. 왜 `overflow: hidden`인가

```text
처음 그린 그림                          실제
"모달이 덮었으니 배경은 안 움직인다"      모달을 띄워도 아래 페이지의 넘치는 내용은 그대로다.
                                        휠을 굴리면 뷰포트가 스크롤되고 배경이 움직인다.

body { overflow: hidden }
  → html의 overflow가 visible(기본)이면 body 값이 뷰포트로 전파된다 (CSS Overflow 3 §3.1.4)
  → 뷰포트 스크롤 불가. 내용은 지워지지 않고, 해제하면 보던 위치 그대로다
```

- 모달 자체는 `position: fixed`로 뷰포트 기준이라 잠금의 영향을 받지 않는다.

#### 4-2. 카운트 없이 잠그면

`body.style.overflow`는 **값이 하나뿐인 공유 자원**이다. 모달 여럿이 같은 자원 하나를 잠그고 푼다.

```text
처음 그린 그림 (스위치 하나)                실제로 원하는 것 (숫자 하나)
열 때 on, 닫을 때 off                       "잠금이 필요한 모달이 몇 개인가"
#1 열기  on   🔒                          #1 열기  0→1  실제 잠금 🔒 (원래 값 저장)
#2 열기  on   🔒                          #2 열기  1→2  아무것도 안 함 🔒
#2 닫기  off  🔓 ← #1이 열려 있는데 풀림    #2 닫기  2→1  아무것도 안 함 🔒
#1 닫기  off  🔓                          #1 닫기  1→0  원래 값 복원 🔓
```

- 각 모달은 "내가 잠갔으니 내가 푼다"고만 생각한다. ESC 문제(각 리스너가 자기 모달만 앎)와 같은 모양이다.
  - *참조 카운트*: 공유 자원을 쓰는 사용자 수를 세어, 0이 될 때만 해제하는 방식. 실제 동작은 0↔1 경계에서만 일어난다. [language/09](../../language/09-memory-management-models/2-summary.md)

```javascript
let lockCount = 0;
let savedOverflow = '';

function lockScroll() {
  if (lockCount++ === 0) {                        // 증가 전이 0 → 내가 첫 번째
    savedOverflow = document.body.style.overflow; // 첫 잠금 때만 원래 값 저장
    document.body.style.overflow = 'hidden';
  }
}
function unlockScroll() {
  if (--lockCount === 0) document.body.style.overflow = savedOverflow; // 감소 후 0 → 내가 마지막
}
```

| 식 | 순서 | 의미 |
|---|---|---|
| `lockCount++ === 0` | 비교(증가 전 값) → 증가 | 내가 첫 번째인가 |
| `--lockCount === 0` | 감소 → 비교 | 내가 마지막인가 |

#### 4-3. 왜 `savedOverflow`인가, 왜 첫 잠금 때만 저장하나

- 해제 때 `''`로 덮으면 페이지가 원래 갖던 인라인 값(예: `overflow: scroll`)이 지워진다.
- `savedOverflow`에는 문자열이 들어간다. 문자열은 원시값이라 **값 복사**다. 나중에 `body.style.overflow`가 `'hidden'`으로 바뀌어도 저장한 값은 그대로다. [language/06](../../language/06-values-references-passing/2-summary.md)
- 잠글 때마다 저장하면, 두 번째 모달은 이미 잠긴 `'hidden'`을 "원래 값"으로 저장한다. 마지막 해제가 `'hidden'`을 복원해 영원히 잠긴다.

### 실험: 세 가지 잠금 구현의 overflow 변화

원래 `body.style.overflow = 'scroll'`인 페이지에서 #1 열기 → #2 열기 → #2 닫기 → #1 닫기 순서로 돌렸다.

(실험, Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04)

```text
[C naive]
  단계       count  body.style.overflow
  시작       -      'scroll'
  #1 열기    -      'hidden'
  #2 열기    -      'hidden'
  #2 닫기    -      ''
  #1 닫기    -      ''
[C saveEveryTime]
  단계       count  body.style.overflow
  시작       0      'scroll'
  #1 열기    1      'hidden'
  #2 열기    2      'hidden'
  #2 닫기    1      'hidden'
  #1 닫기    0      'hidden'
[C refcount]
  단계       count  body.style.overflow
  시작       0      'scroll'
  #1 열기    1      'hidden'
  #2 열기    2      'hidden'
  #2 닫기    1      'hidden'
  #1 닫기    0      'scroll'
```

- `naive`: #2를 닫는 순간 `''` — #1이 열려 있는데 잠금이 풀렸다. 원래 값 `'scroll'`도 잃었다.
- `saveEveryTime`: 카운트는 맞지만 두 번째 저장이 `'hidden'`을 덮어써서 끝까지 잠겼다.
- `refcount`: 마지막 닫기에서만 풀리고 원래 값으로 돌아갔다.

#### 4-4. 정리 경로는 하나로

모달이 사라지는 경로는 `close()`만이 아니다. 논리 부모가 사라지면(화면 전환, 카드 삭제) 모달도 연쇄로 사라진다. `unlockScroll()`·스택 제거·포커스 복귀를 `close()` 안에만 두면 이 경로에서 빠진다. 카운트가 줄지 않아 스크롤이 계속 잠긴다.

```text
close() ──────┐
              ├─▶ cleanup() 한 곳: closed=true · 스택에서 제거 · (0이면) 리스너 해제 · unlockScroll · 포커스 복귀
부모 destroy ──┘   closed 플래그로 두 번 불려도 한 번만
```

## 쓰이는 자료구조·알고리즘

- **스택(LIFO)** — 모달 스택. ESC·바깥 클릭·Tab 가두기는 맨 위(`stack[stack.length - 1]`)에만 반응한다. 닫힘은 중간 모달일 수도 있어(부모 destroy) `splice`로 제거한다. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md)
- **참조 카운트** — 스크롤 잠금(`lockCount`)과 document 리스너 부착(`stack.length` 0↔1)에 같은 원리를 쓴다. [language/09](../../language/09-memory-management-models/2-summary.md)
- **부모 포인터 상향 탐색** — 논리 트리에서 "안쪽인가"를 판정한다. O(깊이). [26-portals-and-two-trees](../26-portals-and-two-trees/2-summary.md)
- **순환 목록(가장자리 처리)** — Tab 순환. 목록 전체가 아니라 양 끝만 이어 붙인다.
- **스냅샷 순회** — 디스패치는 노드마다 리스너 목록을 복사해 돈다. 순회 중 추가는 그 노드에서 무시되고, 해제는 `removed` 표시로 반영된다(WHATWG DOM §2.9).

## 적용 — 풀어나가는 법

쉬운 예부터: "버튼 → 모달 하나, 닫기 버튼 하나"는 네 규칙이 거의 드러나지 않는다. 겹친 모달, 모달 안 드롭다운, 위임으로 연 버튼, 키보드 사용자가 붙는 순간 드러난다.

같은 구조를 실무 순서로 다시 본다: 증상 → 원리 → 확인.

| 증상 | 의심할 원리 | 확인 방법 |
|---|---|---|
| 모달이 안 열린다(열린 직후 닫힘) | 닫기를 여는 것과 같은 click 버블로 들음 | 닫기 콜백에 reason 로그 → 여는 click 직후 `outside`가 찍히나. 여는 버튼에 `stopPropagation`을 넣으면 사라지나(가려짐 확인) |
| 모달 안 드롭다운을 누르면 닫힌다 | DOM `contains` 판정 + portal | `dialog.contains(e.target)`가 `false`인지 콘솔로 확인 |
| ESC 한 번에 전부 닫힌다 | 모달별 리스너, 맨 위 확인 없음 | `getEventListeners(document).keydown` 개수(Chrome DevTools 콘솔 전용) [?] · 닫힘 reason이 escape/destroy 중 무엇인가 |
| Tab으로 뒤 페이지에 들어간다 | 가두기 없음 또는 `preventDefault` 누락 | 마우스를 치우고 Tab 연타 → `document.activeElement` 관찰 |
| 위 모달만 닫았는데 배경이 스크롤된다 | 카운트 없는 잠금 | 열기·닫기마다 `body.style.overflow` 로그 |
| 모달을 다 닫았는데 스크롤이 안 된다 | 잠글 때마다 저장 / 부모 destroy 경로에서 해제 누락 | 카운트 값이 0이 되는지, 원래 값이 무엇으로 저장됐는지 |

조립 순서(한 모달 시스템):

```text
open(modal)
  previous = activeElement
  stack.push(modal);  if (stack.length === 1) document에 pointerdown·keydown 캡처 리스너
  lockScroll()
  queueMicrotask(첫 포커스 요소.focus())
  cleanup 예약 ─────────────────────────────┐
                                           │
close(reason) / 부모 destroy ───────────────▶ cleanup()
  closed? → 끝                               stack 제거; (0이면) 리스너 해제
                                             unlockScroll(); previous.focus(); onClose(reason)
```

- 네이티브 `<dialog>`의 `showModal()`을 쓸 수 있으면 inert·ESC(`cancel` 이벤트)·최상위 레이어를 브라우저가 준다. 바깥 클릭·스크롤 잠금은 그때도 직접 정한다 (`showModal() [?]`의 스크롤 처리 미측정).

## 장애 시나리오와 대처

### 1. 열자마자 닫힘

- 현상: 버튼을 눌러도 모달이 보이지 않는다. 일부 버튼에서만 재현된다.
- 보이는 형태: 닫힘 로그 `reason: outside`가 여는 로그 바로 뒤에 찍힌다. 에러는 없다.
- 원인: 닫기 리스너를 여는 click 핸들러 안에서 document에 click 버블로 붙였다. 디스패치는 document에 도착할 때 목록을 복사하므로 방금 붙인 리스너가 같은 click에 실행된다. `stopPropagation`을 부르는 버튼만 우연히 정상이다.
- 대처: 바깥 감지를 `pointerdown` 캡처로 옮긴다. 여는 쪽의 `stopPropagation`에 기대지 않는다.

### 2. ESC 한 번에 중첩 모달이 전부 닫힘

- 현상: 약관 모달에서 ESC를 눌렀더니 결제 모달까지 사라진다.
- 보이는 형태: 닫힘 reason이 `escape` 둘(형제 구조) 또는 `destroy`+`escape`(중첩 구조).
- 원인: 모달마다 자기 keydown 리스너를 붙였고, 아무도 맨 위인지 확인하지 않는다. 리스너는 등록 순서대로 하나씩 실행된다.
- 대처: 모듈에 공유 리스너 하나 + 모달 스택. 리스너는 스택 맨 위만 닫는다. 비모달 portal은 스택에 넣지 않는다.

### 3. Tab이 모달 뒤로 빠져 보이지 않는 버튼이 눌림

- 현상: 키보드 사용자가 모달에서 Tab을 몇 번 누른 뒤 Enter → 배경의 "삭제" 버튼이 실행된다.
- 보이는 형태: 포커스 표시가 화면에서 사라진다(오버레이 뒤). 접근성 검사기는 이를 잡지 못할 수 있다 — 직접 키보드로 눌러 봐야 드러난다.
- 원인: Tab은 DOM 순서를 따르고, 오버레이는 마우스만 막는다.
- 대처: 가장자리 `trapTab`(+`preventDefault`), 연 직후 포커스 이동, 닫을 때 복귀. 가능하면 `showModal()`이나 배경 `inert`.

### 4. 위 모달만 닫았는데 배경 스크롤이 풀림

- 현상: 두 번째 모달을 닫자 첫 모달 뒤의 페이지가 휠에 움직인다.
- 보이는 형태: `body.style.overflow`가 `''`로 바뀌어 있다.
- 원인: 잠금이 스위치(on/off) 하나다. 각 모달이 자기가 풀 때 다른 모달의 필요를 모른다.
- 대처: 참조 카운트. 첫 잠금 때만 원래 값 저장, 0이 될 때만 복원.

### 5. 모달을 다 닫았는데 스크롤이 영원히 잠김

- 현상: 화면 전환으로 모달이 사라진 뒤, 또는 모달 두 개를 연 뒤 페이지가 스크롤되지 않는다.
- 보이는 형태: 모달이 0개인데 `body.style.overflow === 'hidden'`.
- 원인: (가) 잠글 때마다 원래 값을 저장해 `'hidden'`을 원래 값으로 착각. (나) 해제를 `close()` 안에만 둬서 부모 destroy 경로에서 카운트가 줄지 않음.
- 대처: 첫 잠금 때만 저장. 해제를 정리 함수 한 곳에 예약하고 `closed` 플래그로 중복 실행을 막는다.

### 6. 모달 안 드롭다운을 누르면 모달이 닫힘

- 현상: 날짜 선택기·셀렉트 항목을 고르는 순간 모달이 닫힌다.
- 보이는 형태: 닫힘 reason `outside`, 대상은 portal 메뉴 안 요소.
- 원인: 바깥 판정을 DOM `contains`로 했다. portal 메뉴는 DOM상 dialog 밖이다.
- 대처: 논리 부모를 따라 올라가는 판정. 위치 질문(Tab 순서)은 DOM, 관계 질문(안쪽인가)은 논리 트리.

## 핵심 문장

- 바깥 클릭은 "어느 트리에 묻나"(관계 → 논리 트리)와 "어느 이벤트로 듣나"(여는 click과 다른 `pointerdown`)를 따로 풀어야 한다.
- 디스패치 도중 아직 들르지 않은 조상에 붙인 버블 리스너는 같은 이벤트에서 실행된다 — 그래서 click 버블 닫기는 여는 click에 걸린다.
- ESC 문제의 원인은 캡처도 연쇄도 아니고 "맨 위 확인 없음"이다. 공유 리스너 하나가 스택 맨 위만 닫는다.
- Tab은 화면이 아니라 DOM 순서를 따른다. 가장자리에서만 `preventDefault`로 반대쪽 끝에 넘기고, 열 때 들이고 닫을 때 돌려준다.
- 스크롤 잠금은 공유 자원이다. 참조 카운트로 0↔1 경계에서만 잠그고 풀며, 원래 값은 첫 잠금 때 한 번만 저장한다.

## 관련 주제·근거

- 선행: [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md)(캡처·버블·stopPropagation) · [11-accessibility-basics](../11-accessibility-basics/2-summary.md)(Tab 순서·포커스 표시) · [26-portals-and-two-trees](../26-portals-and-two-trees/2-summary.md)(논리 트리·portal)
- 함께 보기: [web-api/14 dialog·popover](../../../languages/web-api/14-dialog-popover-scripting/2-summary.md)(`showModal()`·inert) · [language/07 클로저](../../language/07-scope-closures-first-class-functions/2-summary.md) · [language/06 값과 참조](../../language/06-values-references-passing/2-summary.md) · [data-structure/03-stack](../../data-structure/03-stack/2-summary.md)
- 근거
  - WAI-ARIA APG "Dialog (Modal) Pattern" — 키보드 상호작용(Tab·Shift+Tab 순환, Escape), 열 때·닫을 때 포커스. https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/ (2026-11-04 확인)
  - WHATWG DOM 표준 §2.9 "Dispatching events" — invoke 단계의 리스너 목록 복사("This avoids event listeners added after this point from being run"), removed 표시. https://dom.spec.whatwg.org/#concept-event-listener-inner-invoke (2026-11-04 확인)
  - W3C UI Events · Pointer Events — `pointerdown → mousedown → pointerup → mouseup → click` 순서, 드래그 시 click 대상 (절 번호·원문 미대조) [?]
  - CSS Overflow Level 3 §3.1.4 viewport propagation — body overflow의 뷰포트 전파. https://drafts.csswg.org/css-overflow-3/ (본문 해설·실험: [25-stacking-context-and-containing-block](../25-stacking-context-and-containing-block/2-summary.md))
- 실험 목록 (전부 Node 20.19.6 · vitest 4.1.12 · jsdom 29.1.1, 2026-11-04, 임시 테스트로 돌린 뒤 삭제)
  - 디스패치 도중 붙인 리스너 3종(document 버블·캡처·대상 자신)의 실행 여부, 위임 지점 `stopPropagation`이 버그를 가리는지
  - 손으로 재현한 `pointerdown → … → click` 순서에서 pointerdown 캡처 닫기
  - ESC 한 번: 모달별 리스너 vs 공유 리스너+스택 × 중첩·형제
  - Tab 가장자리: 가두기 없음 vs `trapTab`, 포커스 복귀 유무(jsdom은 Tab 기본 이동을 흉내 내지 않음)
  - 스크롤 잠금: naive · 매번 저장 · 참조 카운트의 overflow 변화
  - 측정하지 못한 것: 실브라우저 이벤트 순서, pointerdown 닫기의 click-through, `preventDefault` 없는 `first.focus()`의 실제 이동
