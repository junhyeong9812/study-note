# backend-labs 인덱스

규칙: [README.md](README.md). 코드 repo: `/home/jun/project/lab/backend-labs-{commerce,tenancy}/<주제>/`
상태: `예정` → `구현중` → `측정` → `완료`. 선행 cs = 이 랩 전에 인출까지 끝낼 챕터.

## commerce — 정합성·동시성 (01~09)

| # | 주제 | 포트 | 선행 cs | 상태 |
|---|------|------|---------|------|
| 01 | [seat-reservation-lab](commerce/seat-reservation-lab/) | 8101 | [domain basic/02](../../cs/domain-modeling/basic/02-seat-reservation/) · [advanced/12](../../cs/domain-modeling/advanced/12-seat-hold/) · [ops 11 lock](../../cs/ops-patterns/11-distributed-lock/) · [ops 04 rate-limiter](../../cs/ops-patterns/04-rate-limiter/) | 예정 |
| 02 | [payment-consistency-lab](commerce/payment-consistency-lab/) | 8102 | [domain basic/10](../../cs/domain-modeling/basic/10-payment/) · [ops 06 idempotency](../../cs/ops-patterns/06-idempotency-store/) · [ops 07 outbox](../../cs/ops-patterns/07-outbox/) | 예정 |
| 03 | [order-saga-lab](commerce/order-saga-lab/) | 8103 | [domain basic/09](../../cs/domain-modeling/basic/09-order-state/) · [ops 08 saga](../../cs/ops-patterns/08-saga/) | 예정 |
| 04 | [ledger-lab](commerce/ledger-lab/) | 8104 | [domain basic/22](../../cs/domain-modeling/basic/22-settlement/) · [advanced/18](../../cs/domain-modeling/advanced/18-settlement-match/) · [advanced/16](../../cs/domain-modeling/advanced/16-audit-replay/) · [ops 16 event-sourcing](../../cs/ops-patterns/16-event-sourcing/) | 예정 |
| 05 | [auction-lab](commerce/auction-lab/) | 8105 | [ops 11 lock](../../cs/ops-patterns/11-distributed-lock/) | 예정 |
| 06 | [notification-lab](commerce/notification-lab/) | 8106 | [domain basic/07](../../cs/domain-modeling/basic/07-notification/) · [ops 01 retry](../../cs/ops-patterns/01-retry-backoff/) · [ops 05 backpressure](../../cs/ops-patterns/05-backpressure/) | 예정 |
| 07 | [cache-consistency-lab](commerce/cache-consistency-lab/) | 8107 | [ops 09 stampede](../../cs/ops-patterns/09-stampede/) | 예정 |
| 08 | [integration-concert-ticketing](commerce/integration-concert-ticketing/) | 8108 | 01·02·03·04·06·07 랩 (원본 Flow) | 예정 |
| 09 | [integration-auction-to-order](commerce/integration-auction-to-order/) | 8109 | 02·03·04·05·06·07 랩 (원본 Flow) | 예정 |

> **통합 랩(08·09)** — 지금은 다른 랩과 같은 단독 스캐폴드다. 01~07 API 서버를 다 완성한 뒤 각 서버를 이 프로젝트로 옮겨 와 **동시에 띄우는 구조**로 바꾼다(포트 8101~8107 동시 기동 전제). 그 전까지 08·09는 착수하지 않는다.

## tenancy — 멀티테넌시·인증/인가 (10~17)

근거자료: [00-sources-tenancy-auth.md](tenancy/00-sources-tenancy-auth.md). 대응 cs 챕터가 아직 거의 없다 — 착수 전 cs/ 신설 여부 판단.

| # | 주제 | 포트 | 선행 cs | 상태 |
|---|------|------|---------|------|
| 10 | [tenant-isolation-lab](tenancy/tenant-isolation-lab/) | 8210 | 없음 | 예정 |
| 11 | [noisy-neighbor-lab](tenancy/noisy-neighbor-lab/) | 8211 | [ops 03 bulkhead](../../cs/ops-patterns/03-bulkhead/) · [ops 04 rate-limiter](../../cs/ops-patterns/04-rate-limiter/) | 예정 |
| 12 | [tenant-provisioning-migration-lab](tenancy/tenant-provisioning-migration-lab/) | 8212 | 없음 | 예정 |
| 13 | [tenant-aware-cache-search-lab](tenancy/tenant-aware-cache-search-lab/) | 8213 | [ops 09 stampede](../../cs/ops-patterns/09-stampede/) | 예정 |
| 14 | [token-lifecycle-lab](tenancy/token-lifecycle-lab/) | 8214 | 없음 | 예정 |
| 15 | [authorization-model-lab](tenancy/authorization-model-lab/) | 8215 | [domain advanced/28](../../cs/domain-modeling/advanced/28-authorization/) | 예정 |
| 16 | [cross-tenant-authz-lab](tenancy/cross-tenant-authz-lab/) | 8216 | 없음 | 예정 |
| 17 | [sso-service-auth-lab](tenancy/sso-service-auth-lab/) | 8217 | 없음 | 예정 |
