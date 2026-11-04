# 05 — 배경 스크롤 잠금: 스위치가 아니라 숫자로

- 커밋: [`8623f68`](https://github.com/junhyeong9812/react-portal/commit/8623f68) (createModal) · [`f6386cb`](https://github.com/junhyeong9812/react-portal/commit/f6386cb) (재현 토글 N4 + 스크롤 확인용 영역) · [PR #2](https://github.com/junhyeong9812/react-portal/pull/2)
- 학습 노트: [archive/learning/modal/n4-scroll-lock-refcount.md](../archive/learning/modal/n4-scroll-lock-refcount.md) · [archive/frontend/overflow.md](../archive/frontend/overflow.md)

---

## 1. 무엇이 문제였나

모달을 띄워도 아래 페이지의 넘치는 내용은 그대로 있어서, 막지 않으면 휠을 굴릴 때 배경이 스크롤된다.\
`body.style.overflow = 'hidden'`으로 막는다(`html`이 기본값이면 body의 overflow가 뷰포트로 전파된다).

그런데 `body.style.overflow`는 **값이 하나뿐인 공유 자원**이고, 모달은 여러 개 열린다.\
각 모달이 "내가 잠갔으니 내가 푼다"로 처리하면, 위 모달만 닫아도 아래 모달이 열린 채로 잠금이 풀린다.

---

## 2. 무엇을 고민했나

| 후보 | 방법 | 2개 열고 위의 것만 닫으면 |
|---|---|---|
| A. 스위치(on/off) | 열 때 `'hidden'`, 닫을 때 `''` | `''` → 배경 스크롤됨 ✗ · 원래 페이지 설정도 지워짐 |
| B. 참조 카운트 | 몇 개가 잠금을 원하는지 세고, **0↔1 경계**에서만 실제로 잠그고 품 | 카운트 1 → 유지 ✓ · 마지막에 원래 값 복원 |

→ **B.** 모달은 잠금을 직접 하지 않고 "필요하다 / 필요 없어졌다"를 **신고만** 한다.

해제를 어디에 둘지도 정해야 했다. 모달이 사라지는 경로는 `close()`만이 아니다 — **논리 부모가 destroy되면** 연쇄로 사라진다.\
`close()` 안에 두면 그 경로에서 카운트가 줄지 않아 스크롤이 영원히 잠긴다 → **portal 클린업 한 곳**에 둔다.

---

## 3. 그래서 이렇게

```text
             lockCount   조건                      실행                overflow
#1 열기      0 → 1       0 === 0 ✓ (첫 번째)       원래값 기억 + 잠금   'hidden' 🔒
#2 열기      1 → 2       1 === 0 ✗                (아무것도 안 함)     'hidden' 🔒
#2 닫기      2 → 1       1 === 0 ✗                (아무것도 안 함)     'hidden' 🔒 ✓
#1 닫기      1 → 0       0 === 0 ✓ (마지막)        원래값 복원          원래값   🔓
```

- `lockCount++ === 0`: 증가 **전** 값으로 비교 → "내가 첫 번째인가".
- `--lockCount === 0`: 감소 **후** 비교 → "내가 마지막인가".
- `savedOverflow`는 **첫 잠금 때 한 번만** 저장한다. 두 번째 때 또 저장하면 그 값은 이미 `'hidden'`이라 진짜 원래 값을 잃는다.
- 문자열은 원시값이라 **값이 복사**된다 → body를 `'hidden'`으로 바꿔도 `savedOverflow`는 원래 값 그대로.

---

## 4. 코드 — 실제 커밋에서

`src/modal.js` (`8623f68`)

```js
// ── 배경 스크롤 잠금 (참조 카운트) ──
let lockCount = 0;
let savedOverflow = '';

function lockScroll() {
  if (lockCount++ === 0) {
    savedOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  }
}

function unlockScroll() {
  if (--lockCount === 0) document.body.style.overflow = savedOverflow;
}
```

```js
  stack.push(modal);
  if (stack.length === 1) attachDocument();
  lockScroll();

  // 획득한 자원의 해제를 portal 클린업에 예약 → close()든 논리 부모 destroy든 같은 경로로 해제(M5)
  portal.onCleanup(() => {
    closed = true;
    stack.splice(stack.indexOf(modal), 1);
    if (stack.length === 0) detachDocument();
    unlockScroll();
    if (previousFocus?.isConnected) previousFocus.focus();
    onClose?.(reason);
  });
```

`demo/naive-modal.js` (`f6386cb`) — N4 버그.

열 때 (`createNaiveModal` 본문, 88~95행):

```js
  // ── 스크롤 잠금 ──
  // N4 버그: 카운트 없이 열 때 잠그고 닫을 때 무조건 해제 → 위 모달만 닫아도 잠금이 풀림
  if (bugs.noRefcount) {
    document.body.style.overflow = 'hidden';
  } else if (lockCount++ === 0) {
    savedOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
  }
```

닫을 때 (portal 클린업, 101~103행):

```js
    stack.splice(stack.indexOf(modal), 1);
    if (bugs.noRefcount) document.body.style.overflow = '';
    else if (--lockCount === 0) document.body.style.overflow = savedOverflow;
```

N4를 켜면 `if` 쪽(스위치), 끄면 `else` 쪽(라이브러리와 같은 카운트)이 실행된다.

---

## 5. 구현 중 마주친 문제

**데모 페이지가 짧아서 증상이 안 보였다.** 스크롤할 내용이 없으면 잠금이 풀려도 티가 나지 않는다 → 재현 토글을 만들며 150vh "스크롤 확인용 영역"을 추가했다.

**테스트는 원래 값 복원까지 본다.** `overflow = 'scroll'`로 시작해 → 2개 열고 1개 닫으면 `'hidden'` 유지 → 마지막에 `'scroll'` 복원. 카운트를 빼면 실패한다(변이 확인).

**같은 패턴이 이미 있었다.** document 리스너를 `stack.length === 1`에서 붙이고 `=== 0`에서 떼는 것도 0↔1 경계 원리다.

**알려진 한계.** iOS Safari에서 `overflow: hidden`만으로는 터치 스크롤이 완전히 막히지 않는 경우가 있고, 스크롤바가 사라지며 폭이 밀릴 수 있다(`scrollbar-gutter: stable`). 학습 범위 밖으로 두었다.

---

## 6. 결론

- 테스트 M4(카운트·원래 값 복원)·M5(논리 부모 destroy 시 스택·잠금·document 리스너 전부 해제)로 고정.
- 내가 정리한 한 줄: "히든으로 스크롤을 막고, 풀 때는 카운트로 우리가 연 모달이 완전히 닫혔는지 감시해서 히든의 정합성을 맞춘다."
- 개념 노트: [cs/web-platform/27-modal-dialog-behavior](../../../cs/web-platform/27-modal-dialog-behavior/) · [cs/web-platform/25-stacking-context-and-containing-block](../../../cs/web-platform/25-stacking-context-and-containing-block/)
