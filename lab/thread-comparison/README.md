# thread-comparison — 주기 작업 실행: Manual Thread+Sleep vs ScheduledExecutorService

- 원본: `/home/jun/project/thread-comparison` · 기간: 2026-01-17 (git 커밋 기준, 단일 세션) · 스택: Java 21 + Spring Boot 3.5.8, Gradle
- 상태: **완료** (단일 케이스 측정 — 3초/50ms 간격 1회)

## 무엇을 알고 싶었나 — 질문·가설

- 주기적 작업(모니터링·샘플링)을 돌릴 때 **`Thread` + `Thread.sleep()` 수동 루프**와 **`ScheduledExecutorService.scheduleAtFixedRate()`** 중 어느 쪽이 주기를 정확히 지키는가.
- 가설(원본 README 비교표 기준): Manual 방식은 "작업 시간만큼 밀림", Scheduled 방식은 "정확한 주기 유지 시도" — 이를 실측으로 확인.

부수 비교 항목(원본 README): 예외 처리(스레드 사망 vs 계속 실행), 종료 처리(interrupt+join vs cancel() 한 줄), 코드 복잡도, 리소스 관리(매번 새 스레드 vs 풀 재사용).

## 실험 환경과 방법

| 항목 | 값 |
|------|-----|
| 테스트 케이스 | 3초 동안 50ms 간격 샘플링 (`/api/quick-test` 상당) |
| 비교 대상 | `ManualThreadSampler` vs `ScheduledThreadSampler` |
| API | `GET /api/compare?interval=100&duration=5000` · `quick-test`(3초) · `detailed-test`(10초) |

측정 방식(src 코드 기준 — `service/ComparisonService.java`, `sampler/*.java`):

- 두 샘플러를 **순차 실행**(Manual → 500ms 안정화 대기 → Scheduled)하고, 각 실행에서 샘플 시각(`System.currentTimeMillis()`) 목록을 수집.
- 매 샘플마다 `OperatingSystemMXBean.getCpuLoad()`로 CPU도 샘플링하고, `simulateWork()`로 **1~5ms 랜덤 연산 부하를 의도적으로 삽입**(실제 작업 시뮬레이션 — Manual 방식의 드리프트를 유발하는 장치).
- 지표 산출: 연속 샘플 간 간격 목록에서 평균 간격·최소/최대·표준편차, 기대 샘플 수 대비 정확도(`실제/기대×100`).
- 승자 판정: `표준편차 + max(0, 100-정확도)` 점수가 낮은 쪽.
- Manual은 작업 후 고정 `sleep(intervalMs)` (작업 시간이 누적됨), Scheduled는 `scheduleAtFixedRate`가 다음 실행 시각을 고정.

핵심 코드 대비 (원본 README에서 — 두 방식의 차이가 드리프트의 원인):

```java
// Manual Thread + Sleep — 작업 후 sleep → 작업 시간만큼 주기가 밀림
new Thread(() -> {
    while (isRunning.get()) {
        timestamps.add(System.currentTimeMillis());
        doWork();                  // 작업 시간 발생
        Thread.sleep(intervalMs);  // 고정 sleep → 주기 = 작업시간 + interval
    }
}).start();

// ScheduledExecutorService — 다음 실행 시각이 고정
scheduler.scheduleAtFixedRate(() -> {
    timestamps.add(System.currentTimeMillis());
    doWork();  // 작업 시간이 발생해도 다음 실행 시각은 그대로
}, 0, intervalMs, TimeUnit.MILLISECONDS);
```

## 결과 — 단일 케이스 (3초, 50ms 간격)

| 항목 | Manual Thread | ScheduledExecutorService |
|------|---------------|--------------------------|
| 총 샘플 수 | 60 | 60 |
| 목표 대비 정확도 | 101.7% | 101.7% |
| 평균 간격 | 50.8ms | 50.0ms |
| 간격 드리프트 | +0.8ms | +0.0ms |
| 표준편차 | 0.56ms | **0.00ms** |

출처: `/home/jun/project/thread-comparison/README.md` ("실제 테스트 결과")

원본 판정: **ScheduledExecutorService 승**.

## 종합 결론

- **Scheduled는 표준편차 0.00ms** — 작업 시간이 있어도 다음 실행 시각이 고정되므로 간격이 완전히 일정.
- **Manual은 작업 시간(약 0.8ms)이 매 주기에 누적**되어 평균 간격이 50.8ms로 드리프트 발생.
- 원본 결론: 간격이 정확해야 하는 **모니터링·벤치마크 용도에는 `ScheduledExecutorService` 권장**.
- 코드 구조 관점(비교표): 예외 발생 시에도 스케줄링이 계속되고, 종료가 `cancel()` 한 줄이며, 스레드 풀을 재사용한다는 운영상 이점도 Scheduled 쪽.

## 한계·남은 질문

- **측정이 1케이스(3초/50ms) 1회뿐** — 간격·시간·작업 부하를 바꾼 반복 측정 없음. 반복 횟수·분산 검증은 문서에 없음.
- 작업 시간(1~5ms)이 간격(50ms)에 근접·초과하는 경우(scheduleAtFixedRate의 실행 밀림)는 다루지 않음.
- CPU 샘플 값(avgCpu·peakCpu)은 코드로는 수집하지만 README 결과표에는 없음 — 문서에 없음.
- `scheduleAtFixedRate` vs `scheduleWithFixedDelay` 비교는 하지 않음.

## 원본 문서 지도

| 파일 | 내용 |
|------|------|
| `README.md` | 비교 관점 표, 핵심 코드 대비, 실측 결과(유일한 수치), 해석 |
| `src/.../service/ComparisonService.java` | 순차 실행·승자 판정·요약 출력 로직 |
| `src/.../sampler/ManualThreadSampler.java` | 수동 루프 + 고정 sleep + simulateWork, 지표 계산 |
| `src/.../sampler/ScheduledThreadSampler.java` | scheduleAtFixedRate + 데몬 스레드 풀, 지표 계산 |
| `src/.../controller/ComparisonController.java` | `/api/compare`, `/api/quick-test`, `/api/detailed-test` |
