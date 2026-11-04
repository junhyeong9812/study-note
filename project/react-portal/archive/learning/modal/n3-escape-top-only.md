# N3-① ESC가 전부 닫는다 — "맨 위"를 아는 곳이 없다

> 데모: "문제 재현" → **N3 ESC 전체 닫힘 · Tab 탈출** 켜기 → Portal 모달 열기 → 모달 위에 또 열기 → ESC 한 번
> 증상: 두 모달이 전부 닫힌다. (토글을 끄면 위의 것만 닫힌다)
> Tab 탈출(N3-②)은 [n3-tab-trap.md](n3-tab-trap.md)

## 한 문장

**각 모달의 ESC 리스너가 "내가 맨 위 모달인가?"를 확인하지 않고 반응해서 전부 닫힌다.** 라이브러리는 리스너를 **하나만** 두고, 그 리스너가 **모달 스택의 맨 위 하나만** 닫는다.

## naive 구조: 모달마다 자기 리스너 (클로저)

```js
// demo/naive-modal.js:77-86 — createNaiveModal이 불릴 때마다 실행됨
  // N3 버그: 모달마다 자기 리스너가 ESC에 반응(맨 위 확인 없음) → ESC 한 번에 전부 닫힘. Tab 가두기도 없음.
  const onKey = (e) => {
    if (e.key === 'Escape') {
      if (bugs.escAllNoTrap || isTop()) modal.close('escape');   // N3 켜짐 → 맨 위인지 안 봄
    } else if (e.key === 'Tab' && !bugs.escAllNoTrap && isTop()) {
      trapTab(e, dialog.el);
    }
  };
  document.addEventListener('keydown', onKey, true);
```

모달을 두 번 열면 `createNaiveModal`이 두 번 실행되고, 그때마다 **새 `onKey`** 가 생겨 document에 붙는다. 각 `onKey`는 **자기가 만들어진 호출의 `modal`** 을 클로저로 기억한다. → [closures](../../frontend/closures.md)

```
createNaiveModal() 1번째  →  modal #1  ←── onKey#1 이 기억
createNaiveModal() 2번째  →  modal #2  ←── onKey#2 가 기억

document의 keydown 리스너: [onKey#1, onKey#2]   (등록 순서)
```

각 리스너는 **자기 모달만** 안다. 다른 모달이 위에 있는지는 모른다.

## 실제로 무슨 일이 일어나나 — 두 경로 (jsdom에서 확인)

같은 document에 달린 리스너들은 **동시에가 아니라 등록 순서대로 하나씩** 실행된다.

### A. 데모 구조: #2가 #1의 논리 자식 (#1 dialog 안에서 "또 열기")

```
로그:  #2 닫힘 reason=destroy
       #1 닫힘 reason=escape
```
```
ESC 1번
 ├ onKey#1 (먼저 등록) → "ESC네" → 모달 #1 close
 │    └ portal#1.destroy() → 논리 자식부터 정리 → 모달 #2도 destroy (reason: destroy)
 │                                              → #2의 리스너도 이때 해제
 └ onKey#2 → 이미 해제됐으므로 브라우저가 호출하지 않음
```
- **맨 위가 아닌 #1이 반응**해서 그 자식 #2까지 휩쓸었다.
- #2 로그가 먼저인 이유: destroy는 **자식부터** 정리한다.

### B. 형제 구조: #1, #2를 같은 카드에서 따로 엶

```
로그:  #1 닫힘 reason=escape
       #2 닫힘 reason=escape
```
연쇄가 없어도 **두 리스너가 각자** 자기 모달을 닫아서 전부 닫힌다.

### 원인은 하나

A든 B든 **"맨 위인지 확인 없음"**. 캡처·버블과는 무관하다(버블로 달아도 같다).

## 라이브러리 구조: 공유 리스너 1개 + 모달 스택

```js
// src/modal.js:7 — 모듈에 하나
const stack = [];

// src/modal.js:29
const top = () => stack[stack.length - 1];

// src/modal.js:78-87
function onKeyDown(e) {
  const modal = top();            // 맨 위 모달 하나만
  if (!modal) return;
  if (e.key === 'Escape') {
    e.preventDefault();
    modal.close('escape');        // 그것만 닫음
  } else if (e.key === 'Tab') {
    trapTab(e, modal);
  }
}

// src/modal.js:126-127 — createModal 안: 리스너는 첫 모달 때 한 번만 붙인다
  stack.push(modal);
  if (stack.length === 1) attachDocument();
```

```
stack: [#1, #2]   ESC → top() = #2 → #2만 닫음 → stack: [#1]
                  ESC → top() = #1 → #1 닫음   → stack: []  → 리스너 해제
```

## 비교

| | naive | 라이브러리 |
|---|---|---|
| 리스너 수 | 모달 수만큼 (모달마다 클로저) | 항상 1개 (모듈 공유) |
| 각 리스너가 아는 것 | 자기 모달 하나 | 공유 `stack` 전체 |
| ESC에 누가 반응하나 | 모든 모달이 각자 | 스택의 맨 위만 |
| "맨 위"를 아는 곳 | 없음 | `stack` (열린 순서 배열) |

"다른 모달에 도달하지 못하게" 하는 방법이 **stopPropagation으로 이벤트를 막는 것이 아니다.** 리스너를 하나만 두고 **그 리스너가 맨 위를 고르는** 구조로 만든 것이다.

## 레이어 스택과 모달 스택은 다르다

- `src/layers.js`의 스택: z-index용. **모든 portal**(메뉴 같은 비모달 포함)이 들어간다.
- `src/modal.js`의 `stack`: ESC·바깥 클릭·Tab용. **모달만** 들어간다.

메뉴가 열려 있을 때 ESC가 메뉴를 "맨 위 모달"로 착각하면 안 되므로 따로 둔다.

## 테스트

`test/modal.test.js` — "M2 ESC › 맨 위 모달 하나씩 닫힌다": 두 개를 열고 ESC 한 번에 1개 남는지, 두 번째에 0개인지.
