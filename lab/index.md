# lab 인덱스

실험 프로젝트 목록. 상태: `완료` / `부분` / `설계만(미실행)`.

| 프로젝트 | 주제 | 한 줄 결론 | 상태 |
|---|---|---|---|
| [cache-split-lab](cache-split-lab/) | 캐시 분할·복제 시 히트율 손실 | s=0의 정답(키 해시)이 s=1.5의 오답이 된다 — 균등 분포에선 라운드로빈이 6.4배 느리고, 쏠린 분포에선 키 해시가 핫 노드 쏠림으로 먼저 무너진다(용량 −15%) | 완료 |
| [cache-lab](cache-lab/) | Caffeine/Redis/2계층 캐시 비교 | 어떤 캐시든 No Cache 대비 90%+ 개선(p95 53ms→2\~5ms), 단 쓰기 30% 혼합 15배 저하·워밍업 30초 — 환경이 구현체 선택을 정한다 | 완료 |
| [sync-async-lab](sync-async-lab/) | 12개 서버 동기/비동기 실측 | 저부하(200 VU)는 모델 차이를 숨기고 1000 VU에서 3배+ 격차(Go/WebFlux 3.1k vs MVC 954 req/s) — 실 DB에선 커넥션 풀이 상한 결정 | 완료 |
| [proto-bench](proto-bench/) | HTTP vs gRPC 역전 포인트 | "gRPC가 항상 빠르다"는 오해 — 역전은 페이로드 100\~200KB·동시성 100\~200 VU·복잡도 \~150필드, 축을 넘으면 HTTP가 이긴다 | 완료 |
| [distributed-log-pipeline](distributed-log-pipeline/) | Kafka→Spark→HDFS vs PostgreSQL | 1.2억건 실측 — 정렬 조회는 PostgreSQL 37배, 집계는 Compaction(30,803→100파일, 27.4배 개선) 후 HDFS+Spark 2.4배. Small File Problem이 제1병목 | 완료 |
| [sorting-and-graph](sorting-and-graph/) | 정렬·그래프 자원 제한 실측 | 100,000개에서 Quick 7.6ms vs Bubble 14,033ms(1,846배) — 그래프 4종은 모두 O(V+E)라 선택 기준은 속도가 아니라 성질 | 완료 |
| [thread-comparison](thread-comparison/) | sleep 루프 vs ScheduledExecutor | ScheduledExecutorService 표준편차 0.00ms vs Manual +0.8ms 누적 드리프트 — 주기 작업엔 Scheduled | 완료(1케이스) |
| [redis-atomicity-lab](redis-atomicity-lab/) | Redis 원자성(Lua/WATCH/Redisson) | 설계·인프라·시나리오 4종 완성, **실험 미실행 — 모든 수치는 예상값** | 설계만 |
| [backend-labs](backend-labs/) | 정합성·동시성(01~09) · 멀티테넌시·인증(10~17) API 구현 실험 17종 | — | 예정 |
