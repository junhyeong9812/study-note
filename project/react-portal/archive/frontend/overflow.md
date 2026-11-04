# Overflow

> **한 줄**: `overflow`는 **내용이 상자보다 클 때 어떻게 할지**(보이기·잘라 숨기기·스크롤)를 정한다. `body`에 `overflow: hidden`을 주면 페이지(뷰포트) 스크롤이 막힌다 — 모달이 떠 있는 동안 배경 스크롤을 막는 가장 간단한 방법.

## 이해의 흐름 — 내가 정리한 것

> 전체 노트: [N4 스크롤 잠금](../learning/modal/n4-scroll-lock-refcount.md)

**내가 정리한 것**: "모달을 띄워도 아래 넘치는 부분은 그대로 있으니, 히든 처리를 하지 않으면 스크롤이 된다. 그래서 히든으로 스크롤을 막는다. 풀 때는 객체 속성만 바꾸는 게 아니라 카운트로 우리가 연 모달이 완전히 닫혔는지 감시해서 히든의 정합성을 맞춘다."

```text
① 왜 hidden                     ② 왜 카운트                       ③ 왜 savedOverflow
모달 ▣ 떠 있음                   naive: 스위치 하나 (on/off)        첫 잠금 직전 원래 값 기억
아래 페이지 내용 그대로            2개 열고 1개 닫음 → off ✗          'scroll' ─ 저장
→ 휠 굴리면 배경 스크롤           라이브러리: 숫자 (몇 개가 원하나)     'hidden' ─ 잠금
→ overflow:hidden으로 막음        2개 열고 1개 닫음 → 1 → 유지 ✓      마지막 해제 → 'scroll' 복원
                                 0이 될 때만 해제                    (두 번째 모달 때 또 저장하면
                                                                    'hidden'을 원래 값으로 착각)
```

보정 한 가지: 풀 때 넣는 값은 `''`이 아니라 **원래 값**(`savedOverflow`)이다 — 그래야 페이지 설정도 정합성이 맞는다.

## 값

| 값 | 넘치는 내용 | 스크롤 |
|---|---|---|
| `visible` (기본값) | 상자 밖으로 그냥 보임 | — |
| `auto` | 필요할 때만 스크롤바 | 가능 |
| `scroll` | 항상 스크롤바 | 가능 |
| **`hidden`** | **잘라서 숨김** | **사용자 스크롤 불가** (코드의 `scrollTo`는 가능) |
| `clip` | 잘라서 숨김 | 코드 스크롤도 불가, 스크롤 컨테이너가 아님 |

`overflow-x`, `overflow-y`로 축마다 따로 줄 수 있다. `overflow`는 둘을 한 번에 정하는 축약형.

## 페이지 스크롤은 누구의 overflow인가

페이지가 스크롤되는 건 **문서 내용이 화면(뷰포트)보다 길기 때문**이다. 그 스크롤은 `body`가 아니라 **뷰포트**의 것이다.

브라우저의 특별 규칙: **`html`의 overflow가 기본값(`visible`)이면, `body`에 준 overflow가 뷰포트로 전파된다.** 그래서 `body.style.overflow = 'hidden'` 한 줄로 화면 전체 스크롤이 멈춘다.

```
평소                                  body { overflow: hidden }
┌─────────────┐ ▲                    ┌─────────────┐
│ 보이는 화면   │ █ 스크롤바            │ 보이는 화면   │   스크롤바 없음
│             │ │                    │             │   휠·터치로 못 내려감
└─────────────┘ ▼                    └─────────────┘
  아래 내용 (휠로 내려 볼 수 있음)        아래 내용 (그대로 있지만 볼 수 없음)
```

- 내용이 **지워지는 게 아니다.** 사용자가 그쪽으로 스크롤할 수 없을 뿐.
- 다시 원래 값으로 돌리면 보던 위치 그대로 스크롤할 수 있다.

## overflow와 다른 개념의 관계

| 개념 | overflow와의 관계 |
|---|---|
| **클리핑** | `hidden`·`auto`·`scroll`·`clip`은 자손을 자기 영역 밖으로 그리지 못하게 자른다. 단, 자손의 **containing block 체인**이 그 요소를 거칠 때만. `position: fixed` 자손은 보통 안 잘린다(조상에 `transform`이 있으면 잘림) → [containing-block](containing-block.md) |
| **stacking context** | overflow만으로는 stacking context를 만들지 않는다. 데모 카드는 `position + z-index`·`transform`이 만든 것 → [stacking-context](stacking-context.md) |
| **Portal** | 부모의 `overflow: hidden`에 갇히는 걸 피하려고 DOM을 body로 옮긴다 |

## 이 프로젝트에서

### 1. 데모 카드의 함정 — 클리핑

```css
/* demo/style.css */
.card { position: relative; z-index: 1; overflow: hidden; transform: translateZ(0); }
```
일반 자식 모달이 카드 안에 갇혀 잘린다. Portal로 body에 붙이면 이 overflow에서 벗어난다.

### 2. 모달의 스크롤 잠금 — 뷰포트 스크롤 막기

```js
// src/modal.js:12-21
function lockScroll() {
  if (lockCount++ === 0) {
    savedOverflow = document.body.style.overflow;   // 원래 값 기억 (문자열 = 값 복사)
    document.body.style.overflow = 'hidden';        // 뷰포트 스크롤 막기
  }
}

function unlockScroll() {
  if (--lockCount === 0) document.body.style.overflow = savedOverflow;   // 마지막 모달일 때만 원래 값으로
}
```

- **왜 hidden**: 모달을 띄워도 아래 페이지의 넘치는 내용은 그대로 있어서, 막지 않으면 배경이 스크롤된다.
- **왜 카운트**: 잠금 상태가 "열린 모달이 하나라도 있다"와 항상 일치(정합성)하도록 — 마지막 모달이 닫힐 때만 푼다. → [N4](../learning/modal/n4-scroll-lock-refcount.md)
- **왜 원래 값 복원**: `''`로 덮으면 페이지의 원래 overflow 설정이 지워진다. 첫 잠금 때 한 번만 저장해야 한다(두 번째 때는 이미 `'hidden'`이라 진짜 원래 값을 잃는다).
- 모달 자체는 `position: fixed`라 뷰포트 기준으로 떠 있어 영향이 없다. 모달 **안**에 긴 내용이 있으면 모달 요소에 `overflow: auto`를 준다.

## 흔한 함정

- **`html`에도 overflow를 줬다**: 전파 규칙이 바뀌어 `body`의 hidden이 뷰포트에 안 먹을 수 있다. 이 경우 `document.documentElement.style.overflow`를 잠근다.
- **스크롤바가 사라지며 레이아웃이 밀림**: 스크롤바 폭만큼 페이지가 넓어져 내용이 옆으로 이동. `scrollbar-gutter: stable`이나 잠글 때 `padding-right` 보정.
- **iOS Safari**: `overflow: hidden`만으로 터치 스크롤이 완전히 막히지 않는 경우가 있다. 실무 라이브러리는 `position: fixed` + 스크롤 위치 저장·복원 등을 함께 쓴다.
- **원래 값 없이 `''`로 해제**: 페이지 설정 소실.
- **여러 곳이 각자 잠금/해제**: 모달·드로어·토스트가 각자 on/off하면 하나만 닫혀도 풀린다 → 참조 카운트로 한 곳에서 관리.
