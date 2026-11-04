# N4. 위 모달만 닫았는데 배경이 스크롤된다 — 참조 카운트

> 데모: "문제 재현" → **N4 스크롤 잠금 카운트 없음** 켜기 → Portal 모달 열기 → 모달 위에 또 열기 → **위 모달의 닫기** → 마우스 휠
> 증상: 아래 모달(#1)이 아직 열려 있는데 뒤의 페이지가 스크롤된다. (토글을 끄면 마지막 모달을 닫을 때까지 스크롤되지 않는다)
> 페이지 아래의 줄무늬 "스크롤 확인용 영역"은 이 증상을 보이려고 페이지를 길게 만든 것.

## 한 문장

**스크롤 잠금은 "모달이 하나라도 열려 있는 동안"이어야 하는데, naive는 모달 하나가 닫힐 때마다 무조건 풀어 버린다.** 라이브러리는 열린 모달 수를 세서(**참조 카운트**) **0이 될 때만** 푼다.

## 배경: 스크롤 잠금이 왜 필요한가

모달이 열려 있을 때 휠을 굴리면 모달 뒤의 페이지가 스크롤된다. 사용자는 모달을 보고 있는데 배경이 움직이고, 모달을 닫으면 엉뚱한 위치에 와 있다. 그래서 모달이 열려 있는 동안 `body`의 스크롤을 막는다.

```js
document.body.style.overflow = 'hidden';   // 잠금: 넘치는 내용을 숨김 → 스크롤 불가
document.body.style.overflow = saved;      // 해제: 원래 값으로
```

`overflow` 값과 body → 뷰포트 전파 규칙은 [overflow](../../frontend/overflow.md).

## 문제: 잠금은 하나인데 모달은 여러 개

`body.style.overflow`는 **값이 하나뿐인 공유 자원**이다. 모달이 여러 개 열리면 여러 모달이 **같은 자원 하나**를 잠그고 푼다.

### naive — 카운트 없음 (`demo/naive-modal.js:88-95, 102`)

```js
  // ── 스크롤 잠금 ──
  // N4 버그: 카운트 없이 열 때 잠그고 닫을 때 무조건 해제 → 위 모달만 닫아도 잠금이 풀림
  if (bugs.noRefcount) {
    document.body.style.overflow = 'hidden';          // 열 때: 잠금
  } else if (lockCount++ === 0) { ... }
  ...
  // 클린업(닫을 때)
    if (bugs.noRefcount) document.body.style.overflow = '';   // 닫을 때: 무조건 해제
```

```
#1 열기   overflow = 'hidden'   🔒
#2 열기   overflow = 'hidden'   🔒  (이미 잠겨 있음, 그대로)
#2 닫기   overflow = ''         🔓  ← #1이 아직 열려 있는데 풀림 ✗
#1 닫기   overflow = ''         🔓
```

각 모달은 **자기가 잠갔으니 자기가 푼다**고만 생각한다. 다른 모달이 아직 잠금을 필요로 하는지는 모른다. N3-①(각 리스너가 자기 모달만 안다)과 같은 모양의 문제다.

### 라이브러리 — 참조 카운트 (`src/modal.js:8-21`)

```js
// ── 배경 스크롤 잠금 (참조 카운트) ──
let lockCount = 0;
let savedOverflow = '';

function lockScroll() {
  if (lockCount++ === 0) {                          // 0 → 1: 첫 모달일 때만 실제로 잠금
    savedOverflow = document.body.style.overflow;   //        원래 값 기억
    document.body.style.overflow = 'hidden';
  }
}

function unlockScroll() {
  if (--lockCount === 0) document.body.style.overflow = savedOverflow;   // 1 → 0: 마지막일 때만 해제
}
```

```
#1 열기   lockCount 0→1   overflow = 'hidden'   🔒 (실제 잠금, 원래 값 기억)
#2 열기   lockCount 1→2   (아무것도 안 함)       🔒
#2 닫기   lockCount 2→1   (아무것도 안 함)       🔒  ← #1이 열려 있으니 유지 ✓
#1 닫기   lockCount 1→0   overflow = 원래 값      🔓 (실제 해제)
```

- **잠금·해제를 직접 하지 않고 "잠금이 필요하다/필요 없어졌다"를 신고만** 한다. 실제 잠금은 **0↔1 경계**에서만 일어난다.
- 모달이 몇 개든, 어떤 순서로 닫히든 **마지막 하나가 닫힐 때** 풀린다.

### `lockCount++ === 0`, `--lockCount === 0` 읽는 법

| 식 | 동작 | 의미 |
|---|---|---|
| `lockCount++ === 0` | **비교 먼저**(증가 전 값), 그다음 1 증가 | "증가 전에 0이었나?" = 내가 첫 번째인가 |
| `--lockCount === 0` | **1 감소 먼저**, 그다음 비교 | "감소 후 0이 됐나?" = 내가 마지막인가 |

`++`/`--`가 변수 **뒤**에 있으면 "쓰고 나서 변경", **앞**에 있으면 "변경하고 나서 씀".

## 원래 값을 복원하는 이유 (`savedOverflow`)

naive는 해제할 때 `''`(빈 값)으로 덮어쓴다. 페이지가 원래 `body { overflow: scroll }` 같은 인라인 값을 갖고 있었다면 모달을 한 번 열고 닫는 것만으로 **페이지 설정이 지워진다.** 라이브러리는 첫 잠금 직전의 값을 기억해 두었다가 마지막 해제 때 **그 값으로** 되돌린다.

테스트가 이 경우를 직접 확인한다 (`test/modal.test.js` M4):

```js
document.body.style.overflow = 'scroll';      // 원래 값
const { modal: first, a } = openWithButtons(mountRoot());
expect(document.body.style.overflow).toBe('hidden');

const { modal: second } = openWithButtons(a);
second.close();
expect(document.body.style.overflow).toBe('hidden'); // 아직 하나 남음

first.close();
expect(document.body.style.overflow).toBe('scroll'); // 원래 값 복원
```

변이 점검: 카운트를 빼고 닫을 때마다 복원하게 바꾸면 이 테스트가 실패한다.

## 정리 경로가 하나여야 하는 이유 (M5와 연결)

`unlockScroll()`은 `close()` 안이 아니라 **portal 클린업** 안에 있다 (`src/modal.js:131-138`).

```js
  portal.onCleanup(() => {
    closed = true;
    stack.splice(stack.indexOf(modal), 1);
    if (stack.length === 0) detachDocument();
    unlockScroll();                                  // ← 여기
    if (previousFocus?.isConnected) previousFocus.focus();
    onClose?.(reason);
  });
```

모달이 사라지는 경로는 `close()`만이 아니다. **논리 부모가 destroy되면**(예: 카드가 사라짐) 모달도 연쇄로 사라진다. `unlockScroll()`을 `close()` 안에 두면 이 경로에서 카운트가 줄지 않아 **스크롤이 영원히 잠긴다.** 그래서 획득(`lockScroll`) 바로 옆에서 해제를 클린업에 예약했다 — PR #1의 "획득한 쪽이 해제도 예약한다" 원칙. → [memory-and-cleanup](../../frontend/memory-and-cleanup.md)

`closed` 플래그 덕분에 `close()`를 두 번 불러도 클린업은 한 번만 실행된다 → 카운트가 두 번 줄어드는 일도 없다.

## 같은 패턴이 쓰이는 곳

**공유 자원 하나를 여러 사용자가 켜고 끌 때** 참조 카운트가 쓰인다.

| 예 | 공유 자원 |
|---|---|
| 모달 스크롤 잠금 | `body.style.overflow` |
| 이 프로젝트의 document 리스너 | `if (stack.length === 1) attachDocument()` / `if (stack.length === 0) detachDocument()` — 같은 0↔1 경계 원리 |
| 로딩 스피너 | 요청 여러 개 중 마지막이 끝날 때만 숨김 |
| 메모리 관리(참조 카운트 GC), 파일 핸들 | "아무도 안 쓸 때만 해제" |

## 알려진 한계

- `overflow: hidden`만으로는 **iOS Safari**에서 배경 스크롤이 완전히 막히지 않는 경우가 있다. 실무 라이브러리는 `position: fixed` + 스크롤 위치 저장·복원 등을 함께 쓴다.
- 스크롤바가 사라지면서 페이지 폭이 넓어져 내용이 옆으로 살짝 밀릴 수 있다(스크롤바 폭만큼). 실무에서는 `padding-right`로 보정하거나 `scrollbar-gutter: stable`을 쓴다.
- 이 프로젝트는 학습용이라 두 가지 모두 다루지 않았다.
