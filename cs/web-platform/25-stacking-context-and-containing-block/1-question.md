# web-platform/25-stacking-context-and-containing-block — 질문

## 질문

1. (왜) "z-index를 충분히 크게 주면 무엇이든 덮는다"는 그림은 왜 틀렸나? 헤더(`z-index: 2`), 카드(`z-index: 1`), 카드 안 모달(`z-index: 9999`)로 실제 비교 단위를 트리로 그려라.
2. (예측) 실험 A에서 카드를 (1) `position: relative; z-index: 1` (2) `position: relative; z-index: auto` (3) `z-index: auto; opacity: 0.99` (4) z-index 1 유지 + 자식을 body 직속으로 옮김, 네 경우로 바꾸면 겹친 점의 맨 위는 각각 header·child(portal) 중 무엇일까?
3. (연결) "portal은 z-index를 활용하는 기능"이라는 설명을 바로잡아라. DOM 이동과 z-index는 각각 어느 단계에서 무슨 일을 하나?
4. (예측) `position: static`인 A에 `z-index: 100`, 뒤의 B에 `position: relative`(z-index 없음)를 주고 겹쳤다. 맨 위는? `getComputedStyle(A).zIndex`는 무엇을 돌려줄까? 부모를 `display: flex`로 바꾸면?
5. (경계) `overflow: hidden; position: relative`인 카드 안에 `position: absolute` 자식과 `position: fixed` 자식이 있다. 어느 쪽이 잘리나? 카드에 `transform: translateZ(0)`을 더하면 무엇이 바뀌나? 근거가 되는 명세 문장은?
6. (예측) 실험 C에서 카드에 `filter: blur(0px)`, `will-change: transform`, `contain: paint`, `opacity: 0.99`를 하나씩 넣으면 fixed 오버레이의 상자 크기는 각각 뷰포트(800×513)·카드(300×150) 중 무엇일까?
7. (경계) `document.body.style.overflow = 'hidden'`이 화면 전체 스크롤을 막는 이유는? `html { overflow: auto }`가 있는 페이지에서는 어떻게 되나? `hidden`일 때 `scrollTo(0, 500)`은 동작하나?
8. (장애 진단) 모달 위에 확인 모달을 띄우고 확인 모달만 닫았더니 배경이 스크롤되고, 모달을 다 닫은 뒤 페이지 원래 overflow(`'scroll'`)가 사라졌다. 원인과 고치는 코드를 대라.
9. (장애 진단) 카드 hover 애니메이션을 부드럽게 하려고 `overflow: hidden`인 카드에 `will-change: transform`을 넣은 뒤, 카드 안 버튼으로 연 전체 화면 모달이 카드 크기로 잘리고 헤더 아래에 깔린다. 두 증상 각각의 원인과, 한 번에 해결하는 방법은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
