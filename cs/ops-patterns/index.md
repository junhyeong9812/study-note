# ops-patterns 인덱스

원본: `/home/jun/project/myway/ops-patterns/` — 챕터 폴더명은 원본과 1:1 대응.
상태: `공부중` → `서머리` → `질문/정답` → `복습중`. 시작 안 한 챕터는 비워둔다.

| 챕터 | 상태 | 비고 |
|------|------|------|
| [01-retry-backoff](01-retry-backoff/) | | |
| [02-circuit-breaker](02-circuit-breaker/) | | |
| [03-bulkhead](03-bulkhead/) | | |
| [04-rate-limiter](04-rate-limiter/) | | |
| [05-backpressure](05-backpressure/) | | |
| [06-idempotency-store](06-idempotency-store/) | | |
| [07-outbox](07-outbox/) | | |
| [08-saga](08-saga/) | | |
| [09-stampede](09-stampede/) | | |
| [10-scheduler](10-scheduler/) | | |
| [11-distributed-lock](11-distributed-lock/) | | |
| [12-leader-election](12-leader-election/) | | |
| [13-snowflake](13-snowflake/) | | |
| [14-logical-clock](14-logical-clock/) | | |
| [15-crdt](15-crdt/) | | |
| [16-event-sourcing](16-event-sourcing/) | | |
| [17-timeseries](17-timeseries/) | | |
| [18-blockchain](18-blockchain/) | | |
| [19-graceful-shutdown](19-graceful-shutdown/) | | |

## 원본 챕터가 없는 주제

`myway/ops-patterns` 에 대응 챕터가 없어 번호를 받지 않은 주제들이다. 폴더명이 곧 주제다.

| 주제 | 출처 | 상태 | 비고 |
|------|------|------|------|
| [failure-modes](failure-modes/) | `jun-bank/docs/study/11-failure-modes/` 원고를 일반화 | 서머리 | 실패 유형 카탈로그 |
| [failure-at-scale](failure-at-scale/) | 〃 | 서머리 | 규모에서 드러나는 실패 |
| [deadline-propagation](deadline-propagation/) | 원고 없음 — 개념 정리(2026-09-18) | 질문/정답 | 클라이언트 타임아웃과 서버 데드라인. 위 19챕터가 데드라인과 만나 어긋나는 자리를 §8에 모았다 |
