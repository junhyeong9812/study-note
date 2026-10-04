# web-platform/04-dom-and-event-model — 정답

## 정답

### 1. 전파가 가능하게 하는 것

- 조상이 자손의 이벤트를 받을 수 있다 = **위임**.
- 행 1,000개 목록: 리스너를 행마다 1,000개 다는 대신 목록에 1개만 단다(실험: `JSEventListeners` +1000 대 +1). 나중에 추가된 행도 목록 안에서 버블하므로 따로 등록할 필요가 없다.
- 공통 처리(분석 로깅, 바깥 클릭 닫기)를 문서 레벨 리스너 하나로 할 수 있다.

### 2. 전파 그림

```text
 캡처 패스(경로 역순)                          버블 패스(경로 정순)
  window    1 CAPTURING                         button   2 AT_TARGET (비-capture 리스너)
  document  1                                   div#box  3 BUBBLING
  html      1                                   body     3
  body      1                                   html     3
  div#box   1                                   document 3
  button    2 AT_TARGET (capture 리스너)         window   3
```

- `bubbles`가 false인 이벤트는 버블 패스에서 대상 외 노드를 건너뛴다.

### 3. 대상에서의 순서

(실험, headless Chrome 151, 2026-10-04 — 3회 같은 출력)

```text
   div#box:캡처(1)
   button:캡처(2)
   button:버블(2)
   div#box:버블(3)
```

- 캡처 리스너가 먼저다. 등록 순서(버블 먼저)와 무관하다.
- DOM 표준 2.9: 캡처 패스(경로 역순)에서 대상은 `AT_TARGET`으로 "capturing" 호출 → inner invoke가 `capture`가 false인 리스너를 건너뜀 → 대상의 capture 리스너만 불린다. 버블 패스에서 "bubbling" 호출 → capture 리스너를 건너뜀 → 비-capture 리스너가 불린다.

### 4. 개별 vs 위임

(실험, headless Chrome 151, 2026-10-04 — 3회 같은 출력)

```text
(b) 개별 리스너: 항목 1000개 만들 때 JSEventListeners +1000, 처리 여부 [기존 항목, 나중 추가 항목, 자기에 stopPropagation 단 항목] = [O, X, O]
(b) 위임: 항목 1000개 만들 때 JSEventListeners +1, 처리 여부 [기존 항목, 나중 추가 항목, 자기에 stopPropagation 단 항목] = [O, O, X]
```

- 개별: +1000, ① O ② X(리스너가 없음) ③ O(`stopPropagation`은 같은 노드의 다른 리스너를 막지 않음).
- 위임: +1, ① O ② O ③ X(전파가 끊겨 조상까지 안 감).

### 5. 세 메서드

| 메서드 | 멈추는 것 |
|---|---|
| `stopPropagation()` | 다음 invoke부터의 전파(현재 호출의 남은 리스너는 계속. 대상의 capture 리스너에서 멈추면 같은 대상의 비-capture 리스너도 안 불림) |
| `stopImmediatePropagation()` | 위 + 현재 호출의 남은 리스너 |
| `preventDefault()` | 기본 동작(링크 이동·체크·스크롤 등). 전파는 그대로 |

- passive 리스너 안의 `preventDefault()`: DOM 표준의 "set the canceled flag"는 `cancelable`이 true이고 **in passive listener flag가 꺼져 있을 때만** 취소한다. 그래서 무시된다.

### 6. `focus` 위임

- `focus`는 `bubbles`가 false라 버블 패스에서 조상을 건너뛴다. 컨테이너의 버블 리스너는 불리지 않는다.
- 대안: ① 버블하는 `focusin`/`focusout` 사용 ② 컨테이너에 `{ capture: true }`로 달아 캡처 패스에서 받기(캡처 패스는 `bubbles`와 무관하게 돈다).

### 7. 리스너 사이의 마이크로태스크

(실험, headless Chrome 151, 2026-10-04)

```text
실제 클릭   : L1 → micro → L2
b.click()  : L1 → L2 → click() 반환 → micro
```

- 실제 클릭: 리스너 콜백이 끝나면 JS 실행 스택이 비어 "clean up after running script"가 마이크로태스크 체크포인트를 돈다.
- `b.click()`: 호출한 스크립트가 스택에 남아 있어 리스너 사이에 체크포인트가 없다. `then`은 바깥 스크립트가 끝난 뒤.
- 교훈: `el.click()`·`dispatchEvent`로 쓴 테스트는 실제 입력과 마이크로태스크 순서가 다를 수 있다.

### 8. 화면 전환 누수

(실험, headless Chrome 151, 2026-10-04 — 3회 같은 출력)

```text
(c) 해제 안 함: ... → Nodes +15900 / JSEventListeners +300
(c) AbortController 해제: ... → Nodes +0 / JSEventListeners +0
```

- 예측: 300 × 53 = 15,900노드, 리스너 300개가 GC 뒤에도 남는다. `window`의 리스너 목록 → 클로저 → 떼어 낸 `div`로 참조가 이어져 회수되지 않는다.
- 확인: Memory 패널 힙 스냅샷의 "Detached" 노드, 전환 N회 전후 CDP `Performance.getMetrics`의 `Nodes`·`JSEventListeners`(GC 뒤) 비교.
- 고치기: 화면마다 `AbortController`를 두고 `{ signal }`로 등록, 언마운트에서 `abort()`(실험: +0). `removeEventListener`를 쓸 때는 같은 함수 참조·같은 `capture` 값을 넘긴다.

### 9. 드롭다운이 위임을 깸

- 원인: 드롭다운 내부 클릭 핸들러가 `e.stopPropagation()`을 불러, 문서 레벨 위임 리스너(분석·바깥 클릭 닫기)까지 전파가 안 간다.
- `stopPropagation` 없이: 문서 리스너에서 판정한다.

```ts
document.addEventListener('click', (e) => {
  if (!e.composedPath().includes(dropdown)) dropdown.close();   // 바깥 클릭일 때만 닫기
});
```

- 내부에서 "이미 처리됨"을 알리고 싶으면 `preventDefault()` + 상위에서 `e.defaultPrevented` 확인처럼 전파를 끊지 않는 신호를 쓴다. 단, `preventDefault()`는 그 이벤트의 기본 동작(링크 이동·체크박스 토글 등)도 취소하므로, 기본 동작이 필요한 요소에서는 쓰지 않는다.
