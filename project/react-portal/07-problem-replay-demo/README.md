# 07 — 문제 재현 토글: 해결된 코드에서 문제를 다시 "겪게" 만들기

- 커밋: [`f6386cb`](https://github.com/junhyeong9812/react-portal-lab/commit/f6386cb) · [PR #2](https://github.com/junhyeong9812/react-portal-lab/pull/2)
- 학습 노트: [archive/learning/modal/README.md](../archive/learning/modal/README.md) 「직접 겪어 보기」

---

## 1. 무엇이 문제였나

모달 기능을 다 만든 뒤 코드를 같이 읽으려 하니, 데모는 **이미 해결된 버전**이라 문제가 화면에 나타나지 않았다.\
"왜 이렇게 만들었나"를 설명으로만 들으면 와닿지 않는다 — 문제를 직접 겪어 봐야 해결책의 이유가 보인다.

---

## 2. 무엇을 고민했나

| 후보 | 요지 | 대가 |
|---|---|---|
| A. 라이브러리에 옵션 추가 | `createModal({ outsideCheck: 'dom' })` 등 | 학습용 분기가 라이브러리 API를 오염 |
| B. 데모 전용 naive 모달 + 토글 | `demo/naive-modal.js`에 일부러 틀린 구현, 체크박스로 하나씩 켬 | 라이브러리와 비슷한 코드가 데모에 한 벌 더 생김 |
| C. 문제별 별도 페이지 | 문제 상황만 모은 페이지 | 올바른 버전과 탭을 오가며 비교해야 함 |
| D. 읽기만 | 코드 변경 없음 | 문제를 겪을 수 없음 |

→ **B.** `src/`는 건드리지 않고, 체크가 없으면 라이브러리 `createModal`, 하나라도 있으면 naive로 연다.

---

## 3. 그래서 이렇게

```text
[문제 재현] ☐ N1 바깥 판정 DOM contains    → 메뉴 항목을 누르면 모달이 닫힘
           ☐ N2 click으로 바깥 감지          → 여는 즉시 닫힘
           ☐ N3 ESC 전체 닫힘 · Tab 탈출     → 중첩에서 ESC 한 번에 전부 / Tab이 뒤 페이지로
           ☐ N4 스크롤 잠금 카운트 없음       → 위 모달만 닫아도 배경 스크롤

openPortalModal: anyBug() ? createNaiveModal : createModal
```

- 각 토글은 **자기 증상만** 재현한다(나머지는 정답 동작). 모달이 열려 있으면 토글이 바뀌지 않는다(잠금 카운트가 섞이므로).
- 여는 버튼의 `stopPropagation`을 뺐다 → N2가 드러나고, 라이브러리는 그 상태에서도 정상.
- 스크롤 확인용 150vh 영역 추가 → N4가 보인다.

---

## 4. 코드 — 실제 커밋에서

`demo/naive-modal.js` (`f6386cb`)

```js
export const bugs = {
  domContains: false, // N1 바깥 판정을 DOM contains로
  clickOutside: false, // N2 바깥 감지를 pointerdown(캡처) 대신 click(버블)으로
  escAllNoTrap: false, // N3 모달 스택 없이 각자 ESC 처리 + Tab 가두기 없음
  noRefcount: false, // N4 스크롤 잠금 참조 카운트 없음
};
```

`demo/main.js` (`f6386cb`)

```js
  const naive = anyBug();
  const make = naive ? createNaiveModal : createModal;
```

---

## 5. 구현 중 마주친 문제

**재현 검증.** jsdom 스모크로 토글을 하나씩 켰을 때 증상만 바뀌는지 확인했다.

| 상태 | 열기 직후 | 메뉴 항목 후 | Tab 가둠 | 위 닫은 뒤 overflow | ESC 1회 후 |
|---|---|---|---|---|---|
| N0 전부 끔 | 1 | 1 | true | "hidden" | 1 |
| N1 | 1 | **0** | true | "hidden" | 1 |
| N2 | **0** | — | — | — | — |
| N3 | 1 | 1 | **false** | "hidden" | **0** |
| N4 | 1 | 1 | true | **""** | 1 |

출처: react-portal `docs/plans/2026-11-04/naive-modal-demo/log.md`

**이 데모 덕분에 생긴 학습 문서.** N1~N4를 하나씩 겪으며 질문한 내용을 [archive/learning/modal/](../archive/learning/modal/README.md)의 n1~n4 노트로 남겼고, 캡처·overflow 개념 문서가 따라 나왔다.

---

## 6. 결론

- "해결된 코드에서 문제를 다시 겪게 만드는 토글"은 설계 이유를 설명하는 가장 빠른 방법이었다. 라이브러리 오염 없이 데모 계층에만 두었다.
- 실브라우저에서만 볼 수 있는 click-through는 여전히 미검증으로 남아 있다([03](../03-outside-click/README.md)).
