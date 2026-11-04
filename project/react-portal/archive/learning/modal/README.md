# 모달 실무 기능 — createModal 학습 노트

> 대상: `src/modal.js`, `test/modal.test.js` · 작성: 2026-11-03
> Portal로 모달을 만들면 **DOM 트리와 논리 트리가 갈라진다.** 그 때문에 생기는 문제 4가지와 각각의 해결.

## 구조

```
논리 트리                         DOM 트리
card                              body
 └ portal  (createPortal)          ├ #app … .card
    └ overlay   어두운 배경         └ .mini-portal          z-index 1000
       └ dialog role="dialog"         └ .mini-modal-overlay
          ├ h3, 버튼들                    └ .mini-modal (dialog)
          └ menu (비모달 portal) ──┐   ┌─ .mini-portal          z-index 1001  ← DOM은 dialog 밖!
             └ 메뉴 항목            └──┘     └ .menu → 메뉴 항목
```

모달 스택(`stack`)은 열린 순서대로 쌓이고, **맨 위 모달만** ESC·바깥 클릭·Tab 순환에 반응한다.

---

## 1. 바깥 클릭 — DOM이 아니라 논리 트리로 판정

### 문제
"바깥 클릭"을 DOM으로 판정하면 이렇게 된다.
```js
if (!dialog.el.contains(e.target)) close();   // ✗
```
모달 안에서 연 드롭다운 메뉴는 Portal이라 DOM상 body 직속 → `dialog.el.contains(메뉴)`는 **false** → 메뉴를 누르는 순간 모달이 닫힌다.

### 해결 (`src/modal.js` `onPointerDown`)
```js
const node = nodeOf(e.target);                                 // 클릭된 DOM → 노드
if (node && isLogicalDescendant(node, modal.dialog)) return;   // 논리 자손이면 안쪽
modal.close('outside');
```
메뉴는 `createPortal(메뉴 버튼)`으로 열었으므로 논리 체인이 `메뉴 항목 → menu → 메뉴 버튼 → … → dialog` → **안쪽**.

React 생태계의 모달 라이브러리들이 "portal 안 클릭"을 따로 처리하는 이유가 이것이다.

### 왜 click이 아니라 pointerdown인가
- 브라우저 순서: `pointerdown → mousedown → pointerup → mouseup → click`.
- 모달은 열기 버튼의 **click**에서 만들어진다. 이 시점에 그 클릭의 `pointerdown`은 이미 지나갔다.
- 만약 `click`을 들으면: 모달 생성 직후 **같은 click이 document까지 버블링**되어 "바깥 클릭"으로 판정 → 열자마자 닫힘.

### 왜 캡처 단계인가
```js
document.addEventListener('pointerdown', onPointerDown, true);   // 3번째 인자 true = 캡처
```
캡처는 window → target 방향으로 **먼저** 실행된다. 앱 코드가 버블 단계에서 `stopPropagation()`을 불러도 바깥 클릭 감지가 막히지 않는다. → [event-flow](../../frontend/event-flow.md)

---

## 2. ESC — 맨 위 모달만

```js
const top = () => stack[stack.length - 1];
...
if (e.key === 'Escape') { e.preventDefault(); top().close('escape'); }
```
- 모달 두 개가 겹쳐 있을 때 ESC 한 번에 둘 다 닫히면 안 된다.
- 레이어 스택(`layers.js`, z-index용)과 별개로 **모달 스택**을 둔다. 레이어에는 메뉴 같은 비모달 portal도 들어가기 때문.

---

## 3. 포커스 가두기 + 복귀

### 문제
Tab 순서는 **DOM 순서**를 따른다. 모달은 body 끝에 붙어 있어서, 모달 마지막 버튼에서 Tab을 누르면 브라우저 주소창 쪽이나 문서 처음(모달 뒤의 페이지)으로 빠져나간다. 키보드·스크린 리더 사용자는 모달 뒤의 화면을 조작하게 된다.

### 해결
| 시점 | 동작 | 코드 |
|---|---|---|
| 열 때 | 열기 전 포커스(`document.activeElement`)를 기억 | `previousFocus` |
| 연 직후 | dialog의 첫 포커스 요소로 이동(없으면 dialog 자체 — `tabIndex = -1`) | `queueMicrotask(...)` |
| Tab | 마지막 → 처음, Shift+Tab 처음 → 마지막. 밖에 있으면 안으로 | `trapTab` |
| 닫을 때 | 기억해 둔 요소로 복귀(문서에 남아 있으면) | 클린업의 `previousFocus.focus()` |

- **가장자리에서만 개입**: 중간 이동은 브라우저 기본 Tab 동작에 맡긴다.
- **왜 microtask인가**: `createModal`은 dialog만 만들고 돌려준다. 호출한 쪽이 **같은 동기 흐름에서** 버튼들을 붙인 뒤에 포커스를 옮겨야 첫 버튼을 찾을 수 있다. microtask는 현재 동기 코드가 끝난 직후에 실행된다.
- **알려진 한계**(`ponytail:` 주석): Tab 순환 범위는 dialog의 DOM 서브트리뿐 → 모달 안 드롭다운 메뉴의 버튼은 Tab 순환에 안 들어간다.
- `role="dialog"`, `aria-modal="true"`: 스크린 리더에 "모달 대화상자"임을 알린다. 기준: WAI-ARIA Authoring Practices의 Dialog(Modal) 패턴.

---

## 4. 배경 스크롤 잠금 — 참조 카운트

```js
let lockCount = 0;
function lockScroll()   { if (lockCount++ === 0) { saved = body.style.overflow; body.style.overflow = 'hidden'; } }
function unlockScroll() { if (--lockCount === 0) body.style.overflow = saved; }
```
- 모달 두 개를 열고 위의 것을 닫았을 때 잠금이 풀리면 안 된다 → **마지막 하나가 닫힐 때만** 해제.
- 원래 값(`saved`)을 복원한다. `''`로 덮어쓰면 페이지가 원래 `overflow: scroll`이었을 때 깨진다(테스트가 이 경우를 확인).

---

## 5. 정리는 한 곳에서 (M5)

```js
portal.onCleanup(() => {
  closed = true;
  stack.splice(stack.indexOf(modal), 1);
  if (stack.length === 0) detachDocument();   // 모달 0개면 document 리스너도 0개
  unlockScroll();
  if (previousFocus?.isConnected) previousFocus.focus();
  onClose?.(reason);
});
```
- 모달이 닫히는 경로는 두 가지: `modal.close()` 직접 호출, **논리 부모의 destroy**(예: 카드가 사라짐).
- 해제를 `close()` 안에 쓰면 두 번째 경로에서 누락된다(스크롤이 영원히 잠기는 버그). 그래서 **portal 클린업 한 곳**에만 두고, `close()`는 `portal.destroy()`만 부른다.
- `closed` 플래그 → `close()`를 두 번 불러도 한 번만 정리.
- `onClose(reason)`: `'outside' | 'escape' | 'close' | 'destroy'`.
- 앞서 배운 "획득한 쪽이 해제도 예약한다" 원칙 그대로. → [memory-and-cleanup](../../frontend/memory-and-cleanup.md)

---

## 테스트가 결함을 잡는지 (변이 점검)

| 망가뜨린 것 | 결과 |
|---|---|
| 바깥 판정을 `dialog.el.contains(e.target)`로 | "dialog 안에서 연 portal은 안쪽" 테스트 실패 |
| 스크롤 잠금 참조 카운트 제거(닫을 때마다 복원) | "마지막 모달이 닫히면 복원" 테스트 실패 |

복구 후 전체 32개 통과(기존 17 + 모달 15).

## 직접 겪어 보기 — 문제 재현 토글

데모 카드 아래 **"문제 재현"** 체크박스를 켜면 Portal 모달이 일부러 틀린 `demo/naive-modal.js`로 열린다. **하나씩** 켜고, 끄면 라이브러리 버전으로 돌아온다(모달이 열려 있으면 토글이 바뀌지 않음).

| 토글 | 해 볼 것 | 겪는 증상 | 원인 (naive 코드) | 라이브러리의 해결 |
|---|---|---|---|---|
| N1 | 모달 → 메뉴 열기 → 메뉴 항목 | 모달이 닫힘 | `dialog.el.contains(e.target)` — 메뉴는 DOM상 body | 논리 자손 판정 (§1) → [자세히](n1-outside-click.md) |
| N2 | Portal 모달 열기 | 열자마자 닫힘 | `document`에 **click 버블** 리스너 → 여는 click이 이어서 document에 도착 | `pointerdown` 캡처 (§1) → [자세히](n2-open-close-same-click.md) |
| N3 | 또 열기 → ESC / Tab 연타 | 전부 닫힘 / 뒤 페이지로 탈출 | 모달마다 자기 ESC 리스너, 맨 위 확인 없음, Tab 가두기 없음 | 모달 스택 + `trapTab` (§2·3) → [ESC](n3-escape-top-only.md) · [Tab](n3-tab-trap.md) |
| N4 | 또 열기 → 위 모달 닫기 → 휠 | 배경이 스크롤됨 | 닫을 때 무조건 `overflow = ''` | 참조 카운트 (§4) → [자세히](n4-scroll-lock-refcount.md) |

N2에서 여는 버튼은 `stopPropagation()`을 부르지 않는다. 그래도 라이브러리 버전은 멀쩡하다 — `pointerdown`은 클릭보다 먼저 끝나 있기 때문.

## 데모에서 확인

1. **Portal 모달 열기** → 포커스가 "안쪽 버튼 클릭"으로 이동, 페이지 스크롤 잠김
2. **Tab**을 계속 누르기 → 모달 버튼 안에서만 돎
3. **ESC** → 닫히고 포커스가 "Portal 모달 열기" 버튼으로 돌아옴
4. 다시 열고 **메뉴 열기 → 메뉴 항목** → 모달 유지 (로그: "DOM상 dialog 밖이지만 논리 자손")
5. **모달 위에 또 열기** → ESC 한 번에 위의 것만 닫힘
6. **어두운 배경 클릭** → 닫힘 (reason: outside)
