# web-platform/02-rendering-pipeline — 질문

## 질문

1. (왜) 브라우저는 왜 렌더링을 파싱·스타일·레이아웃·페인트·합성 단계로 나누나? "바뀐 것이 닿는 단계부터만 다시 돈다"를 `width`·`color`·`transform` 세 속성으로 설명하라.
2. (그림) 동기 `<script>`와 `<link rel=stylesheet>`가 HTML 파싱과 첫 렌더링을 각각 어떻게 막는지 시간축 그림으로 그려라.
3. (경계) 강제 동기 레이아웃은 언제 생기나? `el.style.width = …` 한 줄과 `el.offsetWidth` 한 줄 중 무엇이 레이아웃을 "부르는" 쪽인가?
4. (예측) 막대 300개에 대해 "읽고 바로 쓰기"를 교차하는 함수와 "다 읽고 다 쓰기" 함수를 headless Chrome 151에서 돌리면 `LayoutCount` 증가는 각각 얼마일까? CPU 4× 스로틀에서 시간은 어떻게 변할까?
5. (예측) 같은 1초 이동을 `left`(rAF), `transform`(rAF), `transform` CSS 애니메이션으로 하면 트레이스의 Layout 이벤트 수는 대략 어떻게 나올까? `transform`(rAF)에서 스타일 계산 횟수가 줄지 않는 이유는?
6. (예측·계산) 200×20px `div` 100개 중 10개, 100개에 `will-change: transform`을 걸면 합성 레이어 수는? 픽셀당 4바이트로 어림하면 100개가 더하는 래스터 메모리는?
7. (연결) Blink는 `.list li.item a` 같은 선택자를 어떻게 빠르게 맞추나? RuleSet 버킷·오른쪽→왼쪽 검사·Bloom 필터를 연결해 설명하라.
8. (장애 진단) 아코디언을 펼칠 때 화면이 굳고 Performance 패널에 "Forced reflow" 경고가 반복된다. 무엇을 확인하고 어떻게 고치나?
9. (장애 진단) 성능을 올리겠다며 카드 목록 전체에 `will-change: transform`을 걸었더니 모바일에서 오히려 나빠졌다. 왜인가, 어떻게 확인하고 고치나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
