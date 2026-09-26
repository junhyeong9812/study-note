# 14. Token Lifecycle Lab

인증 토큰의 발급 · 검증 · 갱신 · 폐기 과정에서 발생하는
로그아웃 후 토큰 재사용 / 갱신 경합 / 리프레시 토큰 탈취 / 서명 키 교체를 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 내용 | 출처 |
|------|------|------|
| RFC 9700 (OAuth 2.0 보안 BCP) | 2025년 1월 발행, 기존 RFC 6749·6750·6819의 위협 모델과 보안 권고를 갱신 | [RFC 9700](https://ftp.nic.ad.jp/rfc/rfc9700.pdf) |
| 같은 문서 목차 | 리프레시 토큰 보호, 탈취된 액세스 토큰 오용 방지(발신자 제한·대상 제한) 항목 포함 | 위와 동일 |
| RFC 9700 요약 | 토큰 재사용 방지, 액세스 토큰 권한 최소화 권고 | [WorkOS 요약](https://workos.com/blog/oauth-best-practices) |
| 발신자 제한 토큰 | mTLS 인증서 바인딩(RFC 8705), DPoP 키 바인딩(RFC 9449)으로 탈취 토큰 사용을 막음 | [IETF Draft](https://www.ietf.org/ietf-ftp/internet-drafts/draft-chen-oauth-roadmap-01.html) |
| 리프레시 토큰 순환 | 재사용 감지 시 토큰 계열 전체를 폐기하는 방식이 일반적 | [Gravitee 정리](https://gravitee.io/corpus/gen-1403/oauth/oauth-refresh-token-rotation-and-replay-detection-strategies.html) |
| 순환 방식 논의 | 서버 클러스터형 클라이언트에서는 순환이 오히려 운영 부담이 될 수 있다는 IETF 메일링 논의 | [IETF OAuth WG](https://mailarchive.ietf.org/arch/msg/oauth/M8pK9Z4VYKW5jNtMwqNPi_Ram9g/) |
| Okta 사용자별 한도 | 동일 사용자의 토큰 발급·갱신 요청을 초당 4회로 제한 | [Okta 문서](https://developer.okta.com/docs/reference/rl2-limits) |

**채택 기준 (제안값)**: 활성 세션 100만, 액세스 토큰 TTL 15분 → 갱신 약 1,100 req/s, API 토큰 검증 5,000 RPS

## Questions

1. 로그아웃한 사용자의 JWT가 만료 전까지 계속 쓰인다면?
2. 세션 조회(Stateful)와 JWT(Stateless) 중 무엇이 5,000 RPS에서 유리한가?
3. 브라우저 탭 두 개가 같은 리프레시 토큰으로 동시에 갱신하면?
4. 이미 사용된 리프레시 토큰이 다시 들어오면(탈취 의심) 무엇을 폐기할까?
5. 서명 키를 교체할 때 기존 토큰을 가진 사용자는 튕기지 않는가?
6. 액세스 토큰 TTL을 줄이면 보안은 좋아지지만 갱신 부하는 얼마나 늘어나는가?

## Architecture

```
Client
  ↓ login
Auth Server
 ├── Access Token (JWT, TTL 변수)
 └── Refresh Token (순환, 계열 ID 추적)
        ↓
Resource API
  ↓
Token Validation (비교)
 ├── A. JWT 서명 검증만
 ├── B. JWT + 폐기 목록(Redis denylist)
 └── C. 세션 저장소 조회

Key Manager ── JWKS (kid 기반 신·구 키 병행)
Refresh Service ── 재사용 감지 → 계열 전체 폐기
```

## Load Profile

| 항목 | 값 |
|------|---|
| 활성 세션 | 1,000,000 |
| 액세스 토큰 TTL | 5 / 15 / 60분 (변수) |
| 갱신 요청 | TTL 15분 기준 약 1,100 req/s |
| API 토큰 검증 | 5,000 RPS |
| 로그아웃·폐기 | 50 req/s |
| 동시 갱신 경합 | 세션의 5%가 같은 리프레시 토큰으로 100ms 내 2회 갱신 |
| 탈취 시뮬레이션 | 리프레시 토큰 0.1%를 다른 기기에서 재사용 |
| 키 교체 | 부하 중 서명 키 1회 교체 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | 로그아웃 후 토큰 재사용 | | | | |
| 2 | Stateless vs Stateful | | | | |
| 3 | 동시 갱신 경합 | | | | |
| 4 | 재사용 감지 시 폐기 범위 | | | | |
| 5 | 서명 키 교체 | | | | |
| 6 | TTL과 갱신 부하 | | | | |

## Load Test Results

| 검증 방식 | TTL | 검증 p99 | 갱신 RPS | 폐기 반영 지연 | 오탐 로그아웃 |
|----------|-----|---------|---------|------------|-----------|
| | | | | | |
| | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| 폐기 후 수락된 요청 | 0 (허용 지연 이후) | | |
| 재사용된 리프레시 토큰으로 발급된 새 토큰 | 0 | | |
| 정상 동시 갱신인데 강제 로그아웃된 세션 | 목표 이하 | | |
| 키 교체 중 서명 검증 실패 | 0 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
