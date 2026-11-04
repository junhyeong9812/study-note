# web-platform/26-portals-and-two-trees — 질문

## 질문

1. (왜) 카드 안에서 연 모달의 DOM을 `appendChild`로 body에 옮기기만 하면 무엇이 풀리고 무엇이 깨지나? Portal은 그중 무엇을 더 지키나? "Portal은 z-index 기능이다"는 왜 틀렸나?
2. (그림) "브라우저가 DOM 트리를 따라 올라가며 이 버튼을 어떻게 처리할지 찾는다"는 그림을 두 단계 그림으로 고쳐 그려라. 브라우저 리스너와 프레임워크 핸들러는 각각 무엇을, 어디에, 언제 등록하나?
3. (예측) 논리 트리 `root ─ card ─ portal2 ─ portal2-btn`, `root ─ sidebar`이고, portal2의 DOM은 sidebar의 DOM 안에 붙였다. 루트와 portal2 컨테이너에 위임 dispatch가 있다. `portal2-btn` 클릭 시 dispatch 리스너는 몇 번 불리고, 핸들러는 어떤 순서로 실행되며, `sidebar` 핸들러는 불리나?
4. (경계) 루트 컨테이너의 dispatch가 버튼·카드·루트 핸들러를 모두 실행했다. 그 뒤 `#app`·`document`의 네이티브 리스너는 불리나? 멈추게 하는 것은 무엇뿐인가? 이 성질이 "열자마자 닫히는 메뉴"를 어떻게 만드나?
5. (예측) Provider가 `dark`를 주는 카드(`onClick` 있음) 아래에서 같은 콘텐츠를 (가) `createPortal` (나) `useEffect` 안의 `createRoot(el).render`로 같은 `#target`에 렌더했다. 각각 `useContext` 값, 안쪽 버튼 클릭 시 카드 `onClick` 호출 여부, `card.contains(button)` 값은?
6. (예측) React 실험에서 일반 자식 버튼을 클릭하면 네이티브 `#card` 리스너와 React `onClick`(버튼·카드) 중 무엇이 먼저 찍히나? portal 안 버튼이 자기 `onClick`에서 `e.stopPropagation()`을 부르면 카드 `onClick`과 네이티브 `document` 리스너는?
7. (경계) 다음을 위치 질문/관계 질문으로 나누고 어느 트리에 물어야 하는지 답하라: 바깥 클릭이면 닫기 · Tab 다음 포커스 대상 · 부모 `overflow`에 잘리나 · `useContext` 값 · 부모 언마운트 시 같이 정리되나 · `.card .btn` 선택자 적용.
8. (장애 진단) 모달 안의 날짜 선택기(Portal로 body에 렌더)에서 날짜를 누르면 모달이 닫히고 선택이 적용되지 않는다. 바깥 클릭 판정은 `dialog.contains(e.target)`이다. 원인과, 최소 두 트리 코드에서의 고친 판정, React에서의 대안을 대라.
9. (장애 진단) Portal 모달 안의 입력란에서 Ctrl+←를 누르자 모달을 연 패널의 `onKeyDown`이 이 키를 가로챘다. 왜인가? `stopPropagation`만 추가하는 것과 구조적 해소는 각각 무엇을 보장하나?
10. (연결) 위임 dispatch는 왜 출발 노드를 찾을 때만 DOM을 타고(`nodeOf`), 그 뒤로는 논리 트리만 타나? 이벤트 객체 단위 중복 방지(`WeakSet`)는 사용자가 두 번 연타한 클릭을 한 번으로 줄이나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
