# 11. Noisy Neighbor Lab

한 테넌트의 트래픽 폭주가 다른 테넌트의 성능을 떨어뜨리는
노이지 네이버 문제를 쿼터 · 공정 스케줄링 · 셀 분리로 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 내용 | 출처 |
|------|------|------|
| Azure 아키텍처 센터 | 한 테넌트가 자원을 과도하게 쓰면 다른 테넌트 성능이 저하되며, 각자는 작아도 합산 사용량이 피크를 만들 수 있음 | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/noisy-neighbor) |
| 같은 문서 | 완화책으로 쿼터 강제(Throttling·Rate Limiting), 샤드·스탬프 확장, 예약 용량 판매 제시 | [Microsoft Learn](https://learn.microsoft.com/en-gb/azure/architecture/antipatterns/noisy-neighbor/noisy-neighbor) |
| Shopify Pods | shop_id를 샤딩 키로 완전히 독립된 DB 클러스터(pod)에 나눠 노이지 네이버 영향을 국소화 | [Shopify Engineering](https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale) |
| Shopify 체크아웃 스로틀 | 예외적 부하 시 일부 상점의 쓰기를 큐에 넣어 같은 샤드의 다른 상점을 보호 | [InfoQ](https://www.infoq.com/news/2017/10/shopify-commerce) |
| Shopify 샤드 재배치 | 자원 집약적 상점이 한 샤드에 몰리면 무중단으로 상점을 다른 샤드로 이전 | [Shopify Engineering](https://shopify.engineering/mysql-database-shard-balancing-terabyte-scale) |
| Okta 토큰 한도 | API 토큰 하나가 기본적으로 엔드포인트 한도의 50%만 쓰도록 제한해 하나가 전체를 독점하지 못하게 함 | [Okta 문서](https://developer.okta.com/docs/reference/rl-global-other-endpoints/) |

**채택 기준 (제안값)**: 테넌트 100개가 각 20 RPS(합계 2,000 RPS)로 사용하는 중 한 테넌트가 50배(1,000 RPS)로 폭주

## Questions

1. 한 테넌트가 50배로 폭주하면 나머지 99개 테넌트의 p99는 얼마나 나빠지는가?
2. 전역 한도와 테넌트별 한도 중 무엇이 공정한가?
3. 폭주 테넌트를 거절할까, 큐에 넣어 늦게 처리할까?
4. 요청 수는 같아도 비싼 쿼리를 보내는 테넌트는 어떻게 제한할까?
5. 유료 등급(Tier)에 따라 한도를 다르게 줄 수 있나?
6. 폭주가 반복되는 테넌트를 다른 셀(pod)로 옮긴다면?

## Architecture

```
Client (tenant_id)
  ↓
API Gateway
  ↓
Fairness Control (비교)
 ├── A. 전역 Rate Limit
 ├── B. 테넌트별 토큰 버킷 (Tier별 한도)
 ├── C. 테넌트별 가중 공정 큐 (Weighted Fair Queue)
 └── D. 셀 분리 (tenant → cell 라우팅)
        ↓
   Application → DB (테넌트별 커넥션 쿼터)

Tenant Metrics ── 테넌트별 RPS / 비용 / p99
```

## Load Profile

| 항목 | 값 |
|------|---|
| 테넌트 | 100개 (Free 70 / Pro 25 / Enterprise 5) |
| 평시 | 테넌트당 20 RPS, 합계 2,000 RPS |
| 폭주 | 1개 테넌트가 1,000 RPS로 10분간 |
| 비싼 쿼리 | 1개 테넌트가 평균의 20배 비용 쿼리를 10 RPS |
| 동시 폭주 | Pro 테넌트 10개가 동시에 5배 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | 폭주 시 타 테넌트 영향 | | | | |
| 2 | 전역 vs 테넌트별 한도 | | | | |
| 3 | 거절 vs 큐잉 | | | | |
| 4 | 비용 기반 제한 | | | | |
| 5 | Tier별 한도 | | | | |
| 6 | 셀 이동 | | | | |

## Load Test Results

| 방식 | 폭주 테넌트 처리량 | 폭주 테넌트 429 비율 | 정상 테넌트 p99 (평시 대비) | DB 커넥션 포화 |
|------|---------------|-----------------|------------------------|-------------|
| | | | | |
| | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| 정상 테넌트 p99 증가율 | 목표 이내 (예: +20%) | | |
| Enterprise 테넌트 한도 보장 | 100% | | |
| 셀 이동 중 유실·중복 요청 | 0 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
