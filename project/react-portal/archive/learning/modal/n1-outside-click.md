# N1. 바깥 클릭 판정 — DOM에 물으면 틀린다

> 데모: "문제 재현" → **N1 바깥 판정 DOM contains** 켜기 → Portal 모달 열기 → 메뉴 열기 → 메뉴 항목
> 증상: 모달 안의 메뉴를 눌렀는데 모달이 닫힌다 (로그 `reason: outside`)

## 한 문장

**"이 버튼이 모달 안쪽인가?"는 논리 관계를 묻는 질문이다. N1은 그 답을 물리(DOM) 위치로 내서 틀렸다.** Portal로 내보낸 메뉴는 물리적으로 모달 밖(body)에 있으니 "바깥"이라는 틀린 답이 나온다.

## 메뉴는 어디에 있나

메뉴는 `createPortal(메뉴 열기 버튼)`으로 연다 (`demo/main.js:124`). Portal이니 DOM은 body로 간다.

```
DOM 트리 (물리)                            논리 트리 (관계)
body                                      card
├ .mini-portal  (모달)                     └ portal
│ └ .mini-modal-overlay                       └ overlay
│   └ .mini-modal  ← dialog.el                   └ dialog
│     └ … 메뉴 열기 버튼                              └ … 메뉴 열기 버튼
└ .mini-portal  (메뉴)   ← dialog 밖                      └ menu (portal)
  └ .menu                                                  └ box
    └ 메뉴 항목                                               └ 메뉴 항목
```

- 물리: 메뉴 항목은 `.mini-modal`의 DOM 자손이 **아니다**.
- 논리: 메뉴 항목은 dialog의 자손**이다**.

## 이벤트를 받는 곳은 같다

두 버전 모두 **document에 단 리스너 하나**가 `pointerdown`을 받고, 받는 정보도 `e.target`(= 메뉴 항목 `<button>`)으로 같다. 차이는 받은 **다음의 판정 한 줄**이다.

## 차이가 나는 코드

### naive — `demo/naive-modal.js:67-74`

```js
  const onOutside = (e) => {
    if (!isTop()) return;
    // N1 버그: DOM contains → dialog 안에서 연 메뉴(portal, DOM은 body)가 "바깥"이 됨
    const inside = bugs.domContains
      ? dialog.el.contains(e.target)                       // ← N1 켜짐: 물리 트리에 묻기
      : isLogicalDescendant(nodeOf(e.target), dialog);     // ← N1 꺼짐: 논리 트리에 묻기
    if (!inside) modal.close('outside');
  };
```

### 라이브러리 — `src/modal.js:24-27, 35-41`

```js
function isLogicalDescendant(node, ancestor) {
  for (let n = node; n; n = n.parent) if (n === ancestor) return true;
  return false;
}

function onPointerDown(e) {
  const modal = top();
  if (!modal) return;
  const node = nodeOf(e.target);
  // DOM의 contains가 아니라 논리 트리로 판정 → dialog 안에서 연 portal(DOM은 body)도 "안쪽"
  if (node && isLogicalDescendant(node, modal.dialog)) return;
  modal.close('outside');
}
```

### 나란히 놓으면

| | 물리 트리에 묻기 (N1 버그) | 논리 트리에 묻기 (라이브러리) |
|---|---|---|
| 코드 | `dialog.el.contains(e.target)` | `isLogicalDescendant(nodeOf(e.target), dialog)` |
| 무엇을 따라가나 | `.mini-modal` 아래 **DOM 자식들** | 클릭된 노드에서 **`n.parent`** 를 따라 위로 |
| 메뉴 항목에 대한 답 | 없음 → **바깥** ✗ | 메뉴 항목 → box → menu → 메뉴 열기 버튼 → row → **dialog** → **안쪽** ✓ |
| 결과 | 모달 닫힘 (메뉴도 논리 자식이라 같이 사라짐) | 모달 유지, click에서 메뉴 항목 핸들러 실행 |

## 논리 판정의 두 단계

```js
// 1) 물리 → 논리로 건너가기: src/registry.js:14-20
export function nodeOf(el) {
  for (let cur = el; cur; cur = cur.parentNode) {   // DOM을 타고 올라가며
    const node = elToNode.get(cur);                  // 처음 만나는 등록 노드
    if (node) return node;
  }
  return null;
}

// 2) 논리 트리에서 관계 확인: src/modal.js:24-27
for (let n = node; n; n = n.parent) if (n === ancestor) return true;
```

- `nodeOf`는 "어느 노드에서 출발할지" 정할 때만 DOM을 탄다. PR #1의 dispatch와 같은 구조.
- 출발 노드가 정해지면 그다음은 **논리 트리만** 탄다. `inject`, dispatch 루프와 같은 `n = n.parent` 모양.
- dialog를 만나면 그 자리에서 "안쪽"으로 끝난다. 루트까지 가도 못 만나면 "바깥".
- `nodeOf`가 `null`이면(어떤 노드에도 속하지 않는 곳, 예: body 빈 곳) 바깥.

## 왜 실무에서 자주 만나나

모달 안의 날짜 선택기, 셀렉트 드롭다운, 툴팁, 자동완성 목록은 대부분 **Portal로 구현**된다(부모의 `overflow`·stacking context에 잘리지 않으려고). 그래서 "바깥 클릭 시 닫기"를 `contains`로 짜면 그런 위젯을 누르는 순간 모달이 닫힌다.

React 생태계에서도 같은 문제가 있다. DOM 기준 바깥 클릭 훅은 portal 안 클릭을 바깥으로 보기 때문에, 라이브러리들이 portal 영역을 따로 등록·예외 처리하는 기능을 둔다.

## 일반 원칙

| 질문의 성격 | 묻는 트리 | 예 |
|---|---|---|
| **위치** | DOM | 화면 어디 그려지나, CSS가 어떻게 걸리나, 잘리나 |
| **관계** | 논리 | 누구의 자식인가, 이벤트를 누가 받나, Context는 어디서 오나, **안쪽인가** |

Portal을 쓰는 순간 두 트리가 갈라지므로, 질문마다 어느 트리에 물을지 골라야 한다. → [component-tree-vs-dom](../../frontend/component-tree-vs-dom.md)

## 테스트

`test/modal.test.js` — "dialog 안에서 연 portal은 DOM상 dialog 밖이지만 논리 자손이라 "안쪽"이다":

```js
expect(modal.dialog.el.contains(item.el)).toBe(false); // DOM 기준이면 "바깥"
pointerdown(item.el);
expect(getOpenModals()).toHaveLength(1);               // 논리 기준이라 닫히지 않음
```

라이브러리의 판정을 `dialog.el.contains(e.target)`로 바꾸면 이 테스트가 실패한다(변이 점검으로 확인).
