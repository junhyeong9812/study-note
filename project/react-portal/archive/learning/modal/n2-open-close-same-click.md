# N2. 열자마자 닫힘 — 여는 click이 닫기 리스너에도 걸린다

> 데모: "문제 재현" → **N2 click으로 바깥 감지** 켜기 → Portal 모달 열기
> 증상: 모달이 나타나지 않는다. 로그에 `── Portal 모달 열기` 바로 다음 `portal#1 닫힘 (reason: outside)`

## 한 문장

**"바깥 클릭 시 닫기"를 여는 것과 같은 click 이벤트로 만들면, 여는 click이 document까지 올라가면서 방금 등록된 닫기 리스너에 걸려 바로 닫힌다.** 라이브러리는 닫기를 **pointerdown**에 걸어서, 여는 이벤트와 닫는 이벤트를 **서로 다른 이벤트**로 만든다.

N1이 "어느 트리에 묻느냐"의 문제였다면, N2는 **"이벤트가 언제 어디를 지나가느냐"(시간 순서)** 의 문제다.

## 전제 1: 클릭 한 번은 이벤트 여러 개

마우스를 한 번 누르고 떼면 브라우저는 이벤트를 **순서대로** 발생시킨다.

```
pointerdown → mousedown → (버튼 뗌) → pointerup → mouseup → click
```

모달은 여는 버튼의 **click** 핸들러에서 만들어진다(`on: { click }`).

## 전제 2: 버블링은 "처리됐다"고 멈추지 않는다

네이티브 버블링은 리스너가 이벤트를 처리했든 아니든 **document까지 계속 올라간다.** 멈추는 건 누군가 `stopPropagation()`을 불렀을 때뿐이다. 그래서 여는 버튼의 click은 `.mini-root`에서 dispatch가 실행된 **뒤에도** document까지 간다. 이건 정상 동작이다. → [event-flow](../../frontend/event-flow.md)

## 동작 흐름 — N2 켜짐 (naive)

```
사용자가 "Portal 모달 열기"를 누름
│
├─ pointerdown ─ button → … → document          모달 없음, 리스너 없음 → 아무 일 없음
├─ mousedown / pointerup / mouseup               (관계없음)
│
└─ click (target = 여는 버튼)
   │
   │  [버블링 — DOM 경로]
   ├─ button
   ├─ .actions
   ├─ .card
   ├─ .mini-root  ◀ dispatch 리스너
   │    └ 여는 버튼 핸들러 → openPortalModal → createNaiveModal
   │         ├ portal / overlay / dialog 생성 → 화면에 모달
   │         └ document.addEventListener('click', onOutside)   ★ 닫기 리스너 등록
   │                                                             (이 click은 아직 올라가는 중)
   ├─ #app, main, section …
   ├─ body, html
   └─ document  ◀ ★ 방금 등록한 닫기 리스너 실행
        └ onOutside(e)
             e.target = 여는 버튼 (카드 안 = 모달 밖)
             → 바깥 클릭으로 판정
             → modal.close('outside')   ✗ 열린 그 click에 의해 닫힘
```

**한 번의 click에 두 리스너가 반응했다.**

```
click 1번
 ├ .mini-root 에서: "열어라"       (여는 버튼 핸들러)
 └ document  에서: "바깥이네, 닫아라" (여는 도중에 생긴 닫기 리스너)
```

사용자가 "바깥을 누른 두 번째 click"이 있는 게 아니다. **여는 click 하나가 닫기 판정에도 쓰였다.** 닫기 리스너 입장에서 그 click은 "모달 밖(여는 버튼)을 누른 click"이다.

## 동작 흐름 — 라이브러리

```
사용자가 "Portal 모달 열기"를 누름
│
├─ pointerdown ─ button → … → document          모달 없음, 닫기 리스너 없음 → 아무 일 없음
│                                                 (이 이벤트는 여기서 끝났다)
├─ mousedown / pointerup / mouseup
│
└─ click (target = 여는 버튼)
   ├─ … → .mini-root  ◀ dispatch
   │    └ 여는 버튼 핸들러 → createModal
   │         └ document.addEventListener('pointerdown', onPointerDown, true)   ★ 닫기 리스너
   └─ … → document     닫기 리스너는 pointerdown용 → 이 click에는 반응 없음   ✓ 모달 유지

(나중에) 사용자가 바깥을 누름
└─ pointerdown ─ document 캡처에서 onPointerDown → 바깥 → 닫힘   ✓
```

## 시간축으로 보면

```
시간 →     pointerdown ── mousedown ── pointerup ── mouseup ── click
                                                                │
                                                      여는 핸들러 실행, 닫기 리스너 등록
                                                                │
naive:      'click' 리스너 ─────────────────────── 같은 click을 받음 → 닫힘 ✗
라이브러리:  'pointerdown' 리스너 ── 이번 pointerdown은 이미 지나감 → 다음 누를 때부터 감지 ✓
```

## 역할 분담

| 동작 | 이벤트 | 어디서 |
|---|---|---|
| 모달 **열기** | click | 여는 버튼 핸들러 (`demo/main.js`) |
| **바깥 클릭**으로 닫기 | **pointerdown** (캡처) | document 리스너 (`src/modal.js` `onPointerDown`) |
| "닫기" 버튼으로 닫기 | click | 닫기 버튼 핸들러 → `modal.close()` |
| ESC로 닫기 | keydown (캡처) | document 리스너 (`onKeyDown`) |

사용자에게는 모두 "누르면 열리고 닫힌다"로 보이지만, 내부에서는 **바깥 클릭 감지만 다른 이벤트**에 걸려 있다. 여는 click과 닫는 pointerdown이 서로 다른 이벤트라서 한 번의 클릭이 둘 다에 쓰일 수 없다.

## 차이 나는 코드

### naive — `demo/naive-modal.js:63-75`

```js
  // N2 버그: click을 "버블"로 듣는다(흔한 naive 코드). 여는 click이 아직 document에 도착하기 전에
  //          이 리스너가 붙으므로, 같은 click이 document에 닿는 순간 "바깥"으로 판정 → 열자마자 닫힘.
  const outsideType = bugs.clickOutside ? 'click' : 'pointerdown';   // N2 켜짐 → 'click'
  const outsideCapture = !bugs.clickOutside;                         // N2 켜짐 → false (버블)
  const onOutside = (e) => {
    if (!isTop()) return;
    const inside = bugs.domContains
      ? dialog.el.contains(e.target)
      : isLogicalDescendant(nodeOf(e.target), dialog);
    if (!inside) modal.close('outside');
  };
  document.addEventListener(outsideType, onOutside, outsideCapture);
  // N2 켜짐이면 실제로는: document.addEventListener('click', onOutside, false)
```

### 라이브러리 — `src/modal.js:35-41, 89-92, 126-127`

```js
function onPointerDown(e) {
  const modal = top();
  if (!modal) return;
  const node = nodeOf(e.target);
  if (node && isLogicalDescendant(node, modal.dialog)) return;
  modal.close('outside');
}

function attachDocument() {
  document.addEventListener('pointerdown', onPointerDown, true);   // pointerdown + 캡처
  document.addEventListener('keydown', onKeyDown, true);
}

// createModal 안
  stack.push(modal);
  if (stack.length === 1) attachDocument();
```

### 여는 쪽은 둘 다 같다 — `demo/main.js:145-152`

```js
  text: 'Portal 모달 열기',
  on: {
    // stopPropagation을 일부러 안 부른다: 여는 click이 document까지 올라가도
    // 라이브러리(pointerdown 캡처)는 멀쩡하고, naive(click 버블)는 열자마자 닫힌다 — N2 재현
    click: () => {
      log('── Portal 모달 열기', 'sep');
      openPortalModal(card);    // ← 이 안에서 위의 addEventListener가 실행됨
    },
  },
```

### 비교

| | naive (N2) | 라이브러리 |
|---|---|---|
| 등록 | `addEventListener('click', onOutside, false)` | `addEventListener('pointerdown', onPointerDown, true)` |
| 듣는 이벤트 | 여는 이벤트와 **같은 종류**(click) | 여는 click보다 **먼저 끝난** pointerdown |
| 여는 click이 document에 도착하면 | 닫기 실행 → **닫힘** | 반응 없음 → **유지** |
| 단계 | 버블 — 앱이 `stopPropagation`하면 못 받음 | 캡처 — 앱보다 먼저 받음 |

## 왜 데모의 여는 버튼은 stopPropagation을 안 부르나

원래는 불렀다. 그러면 click이 document까지 **못 가서** N2 버그가 **우연히 가려진다.** 실제 앱에서는 이게 "어떤 버튼으로 열면 되고 어떤 버튼으로 열면 안 되는" 알 수 없는 버그가 된다(stopPropagation을 부르는 버튼만 정상). 일부러 빼서 드러나게 했고, 라이브러리는 이 상태에서도 정상이다. 이것이 pointerdown 설계의 근거다.

## 덧붙임: 캡처는 다른 이유다

라이브러리의 `true`(캡처)는 N2 해결과 **별개**다. 앱 코드가 버블 단계에서 `stopPropagation()`을 불러도 바깥 클릭 감지가 막히지 않게 하려는 것. 캡처는 window → target 방향으로 **먼저** 실행된다.

참고로 click을 **캡처**로 들었다면 "열자마자 닫힘"은 생기지 않는다. document의 캡처 단계는 여는 버튼 핸들러보다 **먼저** 지나가므로, 그 뒤에 단 캡처 리스너는 이번 click을 못 받는다. 그래도 pointerdown을 쓰는 이유:
- 판정이 **누르는 순간** 끝난다(반응이 빠르고, click까지 기다리지 않음).
- 안쪽에서 누르고 바깥에서 떼는 **드래그**(입력창 텍스트를 끌어 선택하다 오버레이에서 뗌)에서 click은 두 요소의 공통 조상에서 발생해 "바깥"으로 오판되기 쉽다. pointerdown은 누른 지점 하나로만 판정한다.

## 검증

- A1 스모크(이 작업 착수 시): click 핸들러 안에서 document에 추가한 **버블** click 리스너가 **같은 click**에 실행됨을 jsdom으로 확인.
- 데모 스모크: N2 단독으로 켜면 "열기 직후 모달 0개", 끄면 1개.
