# 10. Tenant Isolation Lab

여러 고객사(테넌트)가 하나의 시스템을 공유할 때 발생하는
데이터 누수 / 격리 모델별 비용 / 커넥션 풀 컨텍스트 오염을 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 내용 | 출처 |
|------|------|------|
| AWS 멀티테넌트 가이드 | Silo는 테넌트별 DB 인스턴스, Bridge는 테넌트별 스키마, Pool은 DB의 행 수준 보안으로 격리 | [AWS Guidance](https://docs.aws.amazon.com/solutions/multi-tenant-architectures-on-aws/) |
| 같은 가이드 | Silo는 격리가 가장 강하지만 비용·복잡도 최대, Pool은 반대 | 위와 동일 |
| AWS 격리 백서 | Silo는 노이지 네이버 우려가 없고 테넌트별 비용 추적이 쉬움 | [AWS Whitepaper](https://docs.aws.amazon.com/pdfs/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.pdf) |
| RLS 벤치마크 A | 100만 행, (tenant_id, created_at) 복합 인덱스에서 수동 WHERE 대비 처리량 차이 2% 미만 | [DEV 사례](https://dev.to/sameer_hassan/multi-tenant-database-architecture-row-level-security-rls-postgresql-isolation-24oe) |
| RLS 벤치마크 B | 단건 조회는 +0.1ms 수준, GROUP BY는 약 2.4배, ILIKE 검색은 약 6배 느려짐 | [DEV 사례](https://dev.to/__8fa66572/postgresql-rls-in-go-architecting-secure-multi-tenancy-4ifm) |
| RLS 주의점 | 정책 작성 방식에 따라 인덱스 스캔이 순차 스캔으로 바뀌어 p99가 급증할 수 있음 | [DEV 사례](https://dev.to/software_mvp-factory/postgresql-row-level-security-without-the-performance-tax-436g) |

> RLS 벤치마크는 개인 블로그 수치라 그대로 믿지 않고, 이 Lab에서 **재현해 검증할 가설**로 사용한다.

**채택 기준 (제안값)**: 테넌트 1,000개, 전체 1,000만 행, 상위 1% 테넌트가 데이터의 50% 보유(편중 분포), 조회 2,000 QPS

## Questions

1. 개발자가 `WHERE tenant_id`를 빠뜨리면 다른 테넌트 데이터가 보이는가?
2. Pool(RLS) · Bridge(스키마) · Silo(DB) 중 무엇을 선택할까?
3. RLS의 오버헤드는 쿼리 유형(단건, 집계, 검색)마다 얼마나 다른가?
4. 커넥션 풀에서 이전 요청의 테넌트 컨텍스트가 남아 있다면?
5. 배치·관리자 작업은 격리를 어떻게 우회(bypass)할까?
6. 테넌트 하나를 삭제하거나 데이터를 내보내야 한다면?

## Architecture

```
Client (JWT: tenant_id claim)
  ↓
Tenant Context Filter ── 요청마다 tenant_id 설정
  ↓
Repository
  ↓
Isolation Strategy (비교)
 ├── A. Pool   : 공유 테이블 + tenant_id + RLS
 ├── B. Bridge : 테넌트별 스키마 (search_path)
 └── C. Silo   : 테넌트별 DB (라우팅 테이블)

Isolation Test Suite ── 모든 API에 타 테넌트 ID 주입 → 0건이어야 통과
```

## Load Profile

| 항목 | 값 |
|------|---|
| 테넌트 수 | 1,000개 |
| 데이터 | 총 1,000만 행, 상위 1% 테넌트가 50% 보유 |
| 조회 | 2,000 QPS (단건 70% / 집계 20% / 검색 10%) |
| 쓰기 | 200 TPS |
| 커넥션 풀 | 트랜잭션 모드 풀러 사용, 컨텍스트 초기화 누락 주입 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | WHERE 누락 시 누수 | | | | |
| 2 | 격리 모델 선택 | | | | |
| 3 | 쿼리 유형별 RLS 비용 | | | | |
| 4 | 커넥션 풀 컨텍스트 오염 | | | | |
| 5 | 관리자·배치 우회 | | | | |
| 6 | 테넌트 삭제·내보내기 | | | | |

## Load Test Results

| 격리 모델 | 쿼리 유형 | QPS | p50 | p99 | 테넌트당 비용 |
|----------|---------|-----|-----|-----|-----------|
| | | | | | |
| | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| 교차 테넌트 조회 결과 | 0건 | | |
| 컨텍스트 미설정 요청의 조회 결과 | 0건 (거부) | | |
| 테넌트 삭제 후 잔존 데이터 | 0건 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
