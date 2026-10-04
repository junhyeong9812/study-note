# web-platform/03-event-loop — 질문

## 질문

1. (왜) 메인 스레드가 하나인 렌더러에 이벤트 루프 규칙이 없으면 무엇이 깨지나? "태스크 하나를 끝까지 실행"이라는 규칙이 지켜 주는 것과 대가는?
2. (그림) HTML 표준 처리 모델의 한 바퀴(태스크 선택 → 마이크로태스크 체크포인트 → 렌더링 업데이트)를 그리고, rAF 콜백이 스타일·레이아웃에 대해 어디서 도는지 표시하라.
3. (경계) "Task queues are sets, not queues"와 "The microtask queue is not a task queue"는 각각 무슨 뜻인가? 표준이 태스크 큐 사이의 순서를 정하지 않는다는 것은 무엇을 허용하나?
4. (예측) 아래 코드의 로그 순서는? 이 중 표준이 보장하는 부분과 headless Chrome 151에서 관찰됐을 뿐인 부분을 나눠라.
   `setTimeout(t1+그 안의 then)`, `setTimeout(t2)`, `MessageChannel` 메시지, `requestAnimationFrame(rAF+그 안의 then)`, `Promise.then(micro-1+그 안의 queueMicrotask)`, `queueMicrotask(micro-2)`, 동기 로그.
5. (예측) 300ms 동기 루프를 시작하고 50ms 뒤 버튼을 실제로 클릭하면, 클릭 핸들러는 `event.timeStamp`보다 대략 몇 ms 늦게 시작할까? Event Timing의 `duration`이 8의 배수로 나오는 이유는?
6. (예측) 500ms 동안 `Promise.then`으로 스스로를 다시 거는 루프와 `setTimeout(0)`으로 다시 거는 루프에서, 그동안 rAF는 각각 몇 번 돌까? 루프 전에 걸어 둔 `setTimeout(0)`은 언제 실행될까?
7. (연결) INP의 세 단계는 무엇이고, 각각 이벤트 루프의 어느 부분과 대응하나? 임계값은?
8. (장애 진단) 스피너를 켜고 `await Promise.resolve()` 뒤 무거운 작업을 시작했는데 스피너가 보이지 않는다. 왜이고 어떻게 고치나?
9. (장애 진단) 백그라운드 탭에서 돌아오니 rAF로 돌리던 폴링 로직이 멈춰 있었다. 표준 근거와 대처는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
