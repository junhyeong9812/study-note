# reliability/09-cancellation-propagation — 질문

## 질문

1. (왜) "타임아웃이 났다"와 "작업이 멈췄다"가 다른 이유는? 과부하 때 둘의 차이가 goodput을 0으로 만드는 과정을 설명하라.
2. (예측) 100ms 단계 20개를 하는 작업을 `CompletableFuture.supplyAsync(...).orTimeout(500ms)`로 부르고 500ms에 포기했다. 1.8초 뒤 작업은 몇 단계까지 했을까? `cf.cancel(true)`를 불러도 같은가? 이유는?
3. (예측) 같은 작업을 `ExecutorService.submit` + `get(500ms)` + `cancel(true)`로 멈추려 한다. 작업이 (a) sleep하는 경우 (b) `InterruptedException`을 잡고 무시하는 경우 (c) 확인 없는 CPU 루프 (d) 단계마다 `isInterrupted()`를 확인하는 CPU 루프라면 각각 포기 뒤 몇 단계를 더 하나?
4. (예측) Go `net/http` 서버에서 클라이언트가 500ms에 끊는다. 핸들러가 `r.Context()`를 받아 `time.Sleep`만 하는 경우와 `select`로 `ctx.Done()`을 보는 경우, 각각 어떻게 되나? 끊긴 뒤 `r.Context().Err()`는?
5. (경계) Resilience4j TimeLimiter의 `cancelRunningFuture`(기본값?)는 `Future` 경로와 `CompletionStage` 경로에서 각각 무엇을 하나? CompletableFuture 기반 TimeLimiter가 타임아웃 뒤 스레드를 새게 하는 이유를 두 단계로 설명하라.
6. (그림) 구조적 동시성 스코프에서 형제 작업 하나가 실패하면 나머지는 어떻게 되나? JDK 21과 JDK 25에서 API는 어떻게 다른가?
7. (경계) 플랫폼 스레드에서 `java.net.Socket` 읽기로 막힌 스레드를 인터럽트하면? 가상 스레드라면? (JEP 444)
8. (적용) 외부 PG 승인 호출이 있는 주문 처리에서 취소를 어떻게 설계하나? "커밋 지점" 앞과 뒤를 나눠 답하라.
9. (장애 진단) 종료(shutdown)할 때마다 특정 배치 작업이 기한을 넘겨 강제 종료된다. 코드에서 무엇을 찾나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
