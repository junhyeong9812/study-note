# 17. SSO & Service Auth Lab

테넌트별 외부 IdP 연동(SSO)과 서비스 간 인증에서 발생하는
로그인 폭주 / IdP 장애 / 무차별 대입 / 서비스 인증서 교체 문제를 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 내용 | 출처 |
|------|------|------|
| Okta 사용자별 한도 | 동일 사용자 인증 요청과 토큰 발급·갱신을 각각 초당 4회로 제한 (무차별 대입 방지) | [Okta 문서](https://developer.okta.com/docs/reference/rl2-limits) |
| Okta 인증 사용자 한도 | Identity Engine에 사용자당 5초 20회 제한, 초과 시 해당 사용자에게만 429 | 위와 동일 |
| Okta 클라이언트 한도 | 브라우저 기반 비인증 엔드포인트는 클라이언트 ID·IP·기기 조합으로 분당 60회 기본 제한 | [Okta 문서](https://developer.okta.com/docs/reference/rl2-client-based/) |
| Okta 앱별 한도 | OAuth 앱·토큰 하나는 기본적으로 조직 한도의 50%까지만 사용 | 위와 동일 |
| Okta 동시 요청 한도 | Enterprise 조직 기준 동시 트랜잭션 75개 | [Okta 문서](https://developer.okta.com/docs/reference/rl-additional-limits) |
| Okta 카운터 주기 | 대부분 분당 N회, 60초마다 초기화되지만 시계 정각과 맞춰지지 않음 | [Okta 문서](https://developer.okta.com/docs/reference/rate-limits/) |
| 서비스 간 인증 표준 | mTLS 클라이언트 인증과 인증서 바인딩 토큰(RFC 8705), 경량 키 바인딩 DPoP(RFC 9449) | [IETF Draft](https://www.ietf.org/ietf-ftp/internet-drafts/draft-chen-oauth-roadmap-01.html) |

**채택 기준 (제안값)**: 테넌트 100개 × 사용자 1,000명이 월요일 오전 10분 안에 로그인(약 170 logins/s), 서비스 간 호출 5,000 RPS

## Questions

1. 이메일 도메인으로 테넌트의 IdP를 찾는 과정(Home Realm Discovery)이 병목이 되는가?
2. 한 테넌트의 IdP가 죽으면 다른 테넌트 로그인은 영향이 없는가?
3. 처음 로그인한 SSO 사용자를 즉시 계정 생성(JIT 프로비저닝)할 때 중복 계정이 생기지 않는가?
4. 같은 이메일로 비밀번호 계정과 SSO 계정이 따로 있으면 어떻게 연결할까?
5. 무차별 대입 공격을 사용자 단위, IP 단위, 테넌트 단위 중 어디서 막을까?
6. 서비스 간 인증은 mTLS와 클라이언트 자격 증명 토큰 중 무엇이 나은가?
7. 서비스 인증서를 교체하는 순간 호출이 실패하지 않는가?

## Architecture

```
User
  ↓
Login API
  ↓
Home Realm Discovery ── email domain → tenant → IdP 설정
  ↓
Mock IdP (테넌트별, OIDC / SAML) ←── 지연 / 장애 주입
  ↓ callback
Account Linker / JIT Provisioner
  ↓
Session / Token 발급 (→ 14 Lab)

Brute-force Guard ── 사용자별 · IP별 · 테넌트별 한도

Service A ──(mTLS 또는 Client Credentials)──→ Service B
Cert Manager ── 인증서 자동 교체 (신·구 병행 기간)
```

## Load Profile

| 항목 | 값 |
|------|---|
| 테넌트 / 사용자 | 100개 / 테넌트당 1,000명 |
| 로그인 폭주 | 10분간 100,000건 (약 170 logins/s) |
| IdP 지연 | p50 200ms / p99 2s |
| IdP 장애 | 테넌트 1개의 IdP 5분 중단 |
| 무차별 대입 | 공격 IP 50개에서 사용자 1만 명 대상 1,000 req/s |
| 서비스 간 호출 | 5,000 RPS |
| 인증서 교체 | 부하 중 1회 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | IdP 탐색 병목 | | | | |
| 2 | 테넌트 IdP 장애 격리 | | | | |
| 3 | JIT 중복 계정 | | | | |
| 4 | 계정 연결 | | | | |
| 5 | 무차별 대입 방어 단위 | | | | |
| 6 | mTLS vs Client Credentials | | | | |
| 7 | 인증서 교체 | | | | |

## Load Test Results

| 시나리오 | 로그인 처리량 | 로그인 p99 | 타 테넌트 영향 | 공격 차단율 | 정상 사용자 오차단 |
|---------|-----------|----------|------------|---------|--------------|
| | | | | | |
| | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| JIT로 생긴 중복 계정 | 0 | | |
| 장애 IdP 외 테넌트의 로그인 실패율 | 평시와 동일 | | |
| 인증서 교체 중 서비스 호출 실패 | 0 | | |
| 무차별 대입으로 성공한 로그인 | 0 | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
