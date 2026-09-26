# 16. Cross-tenant AuthZ Lab

다른 사용자·다른 테넌트의 객체 ID를 넣었을 때 발생하는
객체 수준 권한 누락(BOLA/IDOR) / 기능 수준 권한 누락 / 속성 수준 노출을 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 내용 | 출처 |
|------|------|------|
| OWASP API Security Top 10 2023 | 1위는 Broken Object Level Authorization(BOLA): 객체 식별자를 다루는 엔드포인트가 넓은 공격 표면이 됨 | [OWASP](https://owasp.org/projects/api-security-project) |
| 2023 목록 구성 | API3 객체 속성 수준 권한, API5 기능 수준 권한, API4 무제한 자원 소비 포함 | [Palo Alto Networks](https://www.paloaltonetworks.com/blog/cloud-security/demystifying-api-security) |
| BOLA 예시 | 자신의 ID를 다른 ID로 바꿔 다른 사람의 데이터에 접근 | 위와 동일 |
| 2019 → 2023 변화 | 접근 제어가 인증보다 앞 순위로 올라옴. 로그인은 대체로 맞지만 접근 체크에서 실수가 쌓인다는 해석 | [SecureLayer7](https://securelayer7.net/learn/api-security/owasp-api-top-10) |
| 대기업 사례 | 대규모 보안팀을 가진 기업들도 BOLA 공격을 겪음 | [Indusface](https://www.indusface.com/learning/owasp-api-top-10-broken-object-level-authorization/) |
| 속성 수준 예시 | 자기 역할을 user에서 admin으로 바꾸는 식의 필드 조작 | [Radware](https://www.radware.com/cyberpedia/application-security/owasp-api-security-top-10) |

**채택 기준 (제안값)**: 테넌트 3개 × 역할 3종(일반·테넌트 관리자·플랫폼 관리자)으로 모든 엔드포인트에 교차 요청 매트릭스 실행, 공격 계정당 100 req/s ID 열거

## Questions

1. 다른 테넌트의 주문 ID를 넣으면 조회·수정·삭제가 되는가?
2. 순차 ID(1, 2, 3)와 UUID 중 무엇이 열거 공격에 강한가? 그것만으로 충분한가?
3. 없는 리소스와 권한 없는 리소스에 404와 403 중 무엇을 줄까? (존재 여부 노출)
4. 일반 사용자가 관리자 API 경로를 직접 호출하면?
5. 요청 본문에 role, tenant_id 필드를 넣어 보내면 반영되는가?
6. 테넌트 관리자와 플랫폼 관리자의 경계는 어디서 강제하나?
7. 새 엔드포인트가 추가될 때 권한 체크 누락을 어떻게 자동으로 잡을까?

## Architecture

```
Client
  ↓
API Layer
  ↓
Authorization Guard (비교)
 ├── A. 컨트롤러마다 수동 체크
 ├── B. 공통 필터 / AOP (리소스 소유자 · 테넌트 검증)
 └── C. 리포지토리 계층에서 tenant 강제 + 권한 서비스 (→ 15 Lab)

Request DTO Allowlist ── 변경 가능한 필드만 바인딩

Attack Matrix Runner
 ├── 모든 엔드포인트 × 모든 역할 × 타 테넌트/타 사용자 ID
 └── CI에서 매 빌드 실행
```

## Load Profile

| 항목 | 값 |
|------|---|
| 테넌트 | 3개 |
| 역할 | 일반 사용자 / 테넌트 관리자 / 플랫폼 관리자 |
| 엔드포인트 | 전체 (목표 커버리지 100%) |
| 교차 요청 매트릭스 | 엔드포인트 × 역할 × (자기 / 타 사용자 / 타 테넌트) |
| ID 열거 공격 | 계정당 100 req/s, 순차 ID vs UUID |
| 속성 조작 | role, tenant_id, owner_id 필드 주입 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | 타 테넌트 객체 접근 | | | | |
| 2 | 순차 ID vs UUID | | | | |
| 3 | 404 vs 403 | | | | |
| 4 | 관리자 API 직접 호출 | | | | |
| 5 | 속성 조작 | | | | |
| 6 | 관리자 계층 경계 | | | | |
| 7 | 권한 누락 자동 탐지 | | | | |

## Attack Matrix Results

| 엔드포인트 | 역할 | 자기 리소스 | 타 사용자 | 타 테넌트 | 기대 결과 | 통과 |
|----------|-----|----------|--------|---------|---------|-----|
| | | | | | | |
| | | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| 교차 요청 매트릭스 커버리지 | 100% | | |
| 허용되면 안 되는데 허용된 요청 | 0 | | |
| 반영되면 안 되는 필드가 반영된 요청 | 0 | | |
| 열거 공격 탐지 후 차단까지 걸린 요청 수 | 목표 이하 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
