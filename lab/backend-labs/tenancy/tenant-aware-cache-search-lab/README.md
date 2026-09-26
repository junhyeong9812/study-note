# 13. Tenant-aware Cache & Search Lab

캐시와 검색 인덱스를 여러 테넌트가 공유할 때 발생하는
캐시 키 누수 / 인덱스 폭증 / 전체 샤드 조회 / 대형 테넌트 편중을 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 내용 | 출처 |
|------|------|------|
| Elastic 공식 블로그 | 샤드마다 문서가 없어도 고정 메모리 비용이 있어, 무료 테넌트가 많으면 테넌트별 인덱스가 불가능했음 | [Elastic Blog](https://www.elastic.co/blog/found-multi-tenancy) |
| 같은 글 | 공유 인덱스에서 작은 테넌트 하나를 조회해도 클러스터의 모든 샤드를 조회하는 문제 → tenant_id를 라우팅 키로 해결 | 위와 동일 |
| 인덱스 폭증 계산 | 테넌트 1만 × 문서 유형 10 × 언어 10이면 인덱스 100만 개 필요, 공유하면 100개 | [ePages Tech Blog](https://developer.epages.com/blog/tech-stories/multitenancy-and-elasticsearch) |
| 라우팅의 한계 | 라우팅은 hash % 샤드 수라서 다른 테넌트가 같은 샤드에 올 수 있어 tenant 필터가 반드시 필요 | [Elastic 포럼](https://discuss.elastic.co/t/custom-routing-above-shard-count/34028) |
| 권장 샤드 크기 | 10~50GB, 작은 테넌트를 각자 인덱스로 나누면 과소 샤드와 인덱스 폭증이 빨리 옴 | [BigData Boutique](https://bigdataboutique.com/blog/multi-tenancy-with-elasticsearch-and-opensearch-c1047b) |
| 하이브리드 시도 | 공유 인덱스에서 일정 크기를 넘은 테넌트만 전용 인덱스로 재색인하는 방식 논의 | [Elastic 포럼](https://discuss.elastic.co/t/multy-tenany-elasticsearch/347832) |

**채택 기준 (제안값)**: 테넌트 1,000개, 문서 1,000만 건(상위 1% 테넌트가 50%), 검색 500 QPS, 캐시 조회 5,000 RPS

## Questions

1. 캐시 키에 tenant_id가 빠지면 다른 테넌트의 응답이 캐시에서 나가는가?
2. 테넌트별 인덱스, 공유 인덱스, 공유 + 라우팅 중 무엇을 쓸까?
3. 공유 인덱스에서 작은 테넌트 검색이 왜 느려지는가?
4. 라우팅으로 같은 샤드에 모인 다른 테넌트 문서가 검색 결과에 섞이지 않는가?
5. 대형 테넌트 하나 때문에 특정 샤드만 커진다면?
6. 테넌트 삭제 시 캐시와 인덱스에서 데이터가 완전히 사라지는가?

## Architecture

```
Query API (tenant_id)
  ↓
Cache Layer ── key = {tenant_id}:{resource}:{id}
  ↓ miss
Search Strategy (비교)
 ├── A. 테넌트별 인덱스
 ├── B. 공유 인덱스 + tenant 필터
 ├── C. 공유 인덱스 + tenant 라우팅 + 필터
 └── D. 하이브리드 (대형 테넌트만 전용 인덱스)

Leak Test Suite ── 교차 테넌트 캐시 적중·검색 결과 검사
```

## Load Profile

| 항목 | 값 |
|------|---|
| 테넌트 | 1,000개 (상위 1%가 문서 50%) |
| 문서 | 1,000만 건 |
| 검색 | 500 QPS (소형 테넌트 요청 80%) |
| 캐시 조회 | 5,000 RPS |
| 색인 | 200 docs/s |
| 누수 주입 | 캐시 키 생성 로직 일부에서 tenant_id 누락 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | 캐시 키 누수 | | | | |
| 2 | 인덱스 전략 선택 | | | | |
| 3 | 소형 테넌트 검색 지연 | | | | |
| 4 | 라우팅 충돌 시 결과 혼입 | | | | |
| 5 | 대형 테넌트 샤드 편중 | | | | |
| 6 | 테넌트 삭제 완전성 | | | | |

## Load Test Results

| 전략 | 인덱스·샤드 수 | 소형 테넌트 p99 | 대형 테넌트 p99 | 클러스터 메모리 | 조회 샤드 수 |
|------|-------------|--------------|--------------|------------|----------|
| | | | | | |
| | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| 교차 테넌트 캐시 적중 | 0 | | |
| 교차 테넌트 검색 결과 | 0 | | |
| 테넌트 삭제 후 잔존 캐시·문서 | 0 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
