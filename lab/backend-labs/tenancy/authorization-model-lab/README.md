# 15. Authorization Model Lab

권한 모델(RBAC · ABAC · ReBAC)에 따라 달라지는
권한 체크 지연 / 목록 필터링 비용 / 권한 변경 반영 지연을 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 내용 | 출처 |
|------|------|------|
| Google Zanzibar 논문 | 수조 개 ACL, 초당 수백만 건 권한 요청 처리, 3년간 p95 10ms 미만·가용성 99.999% 초과 | [USENIX ATC '19](https://www.usenix.org/conference/atc19/presentation/pang) |
| 같은 논문 초록 | 사용자 행동의 인과 순서를 지켜 ACL·객체 변경 중에도 외부 일관성을 제공 | [Google Research](https://research.google/pubs/pub48190/) |
| Zanzibar 발표 자료 | p95 10ms 미만, p99.9 100ms 미만 | [ATC '19 슬라이드](https://www.usenix.net/sites/default/files/conference/protected-files/atc19_slides_pang.pdf) |
| 같은 자료 | 피크 기준 Check 420만 QPS, Read 820만, Expand 76만, Write 2.5만 (읽기 중심) | 위와 동일 |
| 같은 자료 | 관계 튜플 2조 개 이상, 클라이언트 쿼리 초당 1,000만 건 이상 | 위와 동일 |
| 검색 결과 권한 | 검색 결과 하나에 수십~수백 번의 권한 체크가 필요해 저지연이 중요 | [Packt 요약](https://hub.packtpub.com/google-researchers-present-zanzibar-a-global-authorization-system-it-scales-trillions-of-access-control-lists-and-millions-of-authorization-requests-per-second/amp/) |
| 가용성 원칙 | 권한 시스템이 응답하지 않으면 클라이언트는 "거부"로 간주해야 함 | [ATC '19 발표 요약](https://videohighlight.com/v/mstZT431AeQ) |

> Zanzibar 수치는 목표가 아니라 **읽기:쓰기 비율(약 170:1)과 지연 목표(p95 10ms)를 가져오는 참고점**으로 쓴다.

**채택 기준 (제안값)**: 사용자 10만, 리소스 100만, 관계 1,000만 건, 권한 체크 5,000 QPS, 권한 변경 30/s

## Questions

1. RBAC, ABAC, ReBAC 중 우리 도메인(팀 · 폴더 · 문서 공유)에 맞는 것은?
2. 목록 조회에서 결과 100건마다 권한을 체크하면 얼마나 느려지는가?
3. 권한 체크 결과를 캐시하면, 권한을 뺏은 직후에도 접근이 허용되는가?
4. 그룹이 5단계로 중첩되면 체크 비용은 얼마나 늘어나는가?
5. 권한 서버가 죽으면 거부(fail-closed)할까, 허용(fail-open)할까?
6. 권한 변경과 문서 변경의 순서가 뒤바뀌면? (권한 뺏은 뒤 올린 문서가 보이는 문제)

## Architecture

```
Resource API
  ↓
Policy Enforcement Point
  ↓
AuthZ Service (비교)
 ├── A. RBAC   : user → role → permission
 ├── B. ABAC   : 정책 엔진 (속성 평가)
 └── C. ReBAC  : 관계 튜플 (object#relation@user) 그래프 탐색
        ↓
   Decision Cache (TTL / 버전 토큰)
        ↓
   Relation Store

List Filtering (비교)
 ├── 조회 후 필터 (post-filter)
 └── 권한 인덱스로 사전 필터 (pre-filter)
```

## Load Profile

| 항목 | 값 |
|------|---|
| 사용자 / 그룹 / 리소스 | 100,000 / 5,000 / 1,000,000 |
| 관계 튜플 | 10,000,000 |
| 그룹 중첩 깊이 | 1 / 3 / 5 (변수) |
| 단건 권한 체크 | 5,000 QPS |
| 목록 조회 | 200 QPS, 페이지당 후보 100건 |
| 권한 변경 | 30/s (체크 대비 약 170:1) |
| 권한 서버 장애 | 1분 중단 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | 권한 모델 선택 | | | | |
| 2 | 목록 조회 권한 필터 | | | | |
| 3 | 결정 캐시와 권한 회수 | | | | |
| 4 | 그룹 중첩 비용 | | | | |
| 5 | fail-closed vs fail-open | | | | |
| 6 | 권한·문서 변경 순서 | | | | |

## Load Test Results

| 모델 | 중첩 깊이 | 캐시 | 체크 p95 | 체크 p99.9 | 목록 조회 p99 | 회수 반영 지연 |
|------|---------|-----|---------|----------|------------|------------|
| | | | | | | |
| | | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| 권한 회수 후 허용된 요청 (허용 지연 이후) | 0 | | |
| 권한 없는 리소스가 목록에 노출 | 0 | | |
| 권한 서버 장애 중 허용된 요청 (fail-closed 시) | 0 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
