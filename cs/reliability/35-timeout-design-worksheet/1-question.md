# reliability/35-timeout-design-worksheet — 질문

## 질문

1. (그림) 게이트웨이 → 서비스 A → (B 재고, DB, 외부 PG) 경로의 예산표를 그려라. 사용자 SLO 3.0초에서 출발해, 표가 통과해야 할 검사 네 가지를 적어라.
2. (예측) Envoy route `timeout: 1s`, 재시도 없음. 결제 서비스가 승인에 1.5초 걸린다. 사용자는 무엇을 받고, 결제는 몇 번 승인되나?
3. (예측) 같은 서비스에 route `timeout: 3.5s`, `retry_on: "5xx"`, `num_retries: 2`, `per_try_timeout: 1s`를 걸면? 같은 설정에서 요청에 `Idempotency-Key`를 붙이고 서비스가 키로 중복을 막으면?
4. (경계) Envoy의 route `timeout`, `per_try_timeout`, route `idle_timeout`, cluster `connect_timeout`은 각각 무엇을 덮나? `x-envoy-expected-rq-timeout-ms`를 남은 예산으로 쓰면 안 되는 이유는?
5. (예측) Resilience4j에서 하류가 처음 두 번은 1.5초, 세 번째는 0.1초 걸린다. TimeLimiter 1초, Retry 최대 시도 3번(첫 호출 포함)일 때 `Retry(TimeLimiter(call))`와 `TimeLimiter(Retry(call))`의 결과와 걸린 시간은? 뒤쪽 순서에서 호출자가 실패를 받은 뒤 무슨 일이 일어나나?
6. (예측) 인터럽트에 반응하지 않는 하류(항상 1.5초)를 TimeLimiter 1초로 감싸고 서킷 브레이커를 바깥(`CB(TL(call))`)과 안쪽(`TL(CB(call))`)에 둘 때, 서킷 브레이커가 세는 실패·성공은 각각? 기본 설정에서 이 호출이 "느린 호출"로 세어지나?
7. (연결) Spring Boot에서 Resilience4j 애너테이션을 쓰면 기본 순서는 무엇인가? 그 순서가 5·6번의 문제를 피하는 이유는?
8. (장애 진단) "결제 실패라고 떠서 다시 했더니 두 번 결제됐다"는 문의가 들어왔다. 어떤 로그를 맞대어 보고, 예산표의 어느 검사가 깨졌는지 어떻게 확인하나? 재발 방지는?
9. (적용) 외부 PG 승인 단계의 칸(per-try·시도·멱등·모호할 때 경로)을 어떻게 채우나? 왜 게이트웨이에서 재시도하지 않나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
