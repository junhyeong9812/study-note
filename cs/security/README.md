# 보안 — `cs/security/` 커리큘럼

> **생성 문서** — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §8에서 `docs/plans/2026-09-28/cs-restructure/gen_area_readme.py`로 만든다. 직접 고치지 말고 커리큘럼을 고친 뒤 재실행한다.
> 번호 = 권장 학습 순서. 상태: `미작성` · `원고 있음` · `초안(Claude)` · `검수 완료`. ⚠ 깨지면·🔧·📚 세부는 커리큘럼 본문에 있다.
> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 30 · 검수 완료 0

> 원리 → 암호 기초 → 인증·인가 → 웹/앱 공격 → 공급망·운영. **TLS/PKI 본문은 network/29~32에만** 둔다(단일 출처) — 여기선 암호 부품과 신뢰 모델까지.
> 뼈대: OSTEP 53~57(Security 파트), K&R 8장, OWASP Top 10 2021, Aumasson 『Serious Cryptography』 [?], RFC.

## 8.1 원리

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 01 | `security-principles` | CIA·최소 권한·심층 방어·fail-safe 기본값·완전한 중재 | 필수 | 초안(Claude) | [01-security-principles](01-security-principles/) |
| 02 | `threat-modeling` | 자산·공격 표면·신뢰 경계·STRIDE | 권장 | 초안(Claude) | [02-threat-modeling](02-threat-modeling/) |

## 8.2 암호 기초

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 03 | `symmetric-encryption-and-aead` | 블록 암호·운용 모드·AEAD(AES-GCM·ChaCha20-Poly1305) | 필수 | 초안(Claude) | [03-symmetric-encryption-and-aead](03-symmetric-encryption-and-aead/) |
| 04 | `hash-functions-and-digests` | 암호 해시의 3성질·SHA-2·길이 확장 | 필수 | 초안(Claude) | [04-hash-functions-and-digests](04-hash-functions-and-digests/) · [../foundations/security/sha256-and-digest.md](../foundations/security/sha256-and-digest.md) |
| 05 | `mac-and-hmac` | 무결성+출처 인증, HMAC | 필수 | 초안(Claude) | [05-mac-and-hmac](05-mac-and-hmac/) · [../foundations/security/hmac.md](../foundations/security/hmac.md) |
| 06 | `public-key-and-signatures` | RSA·ECC·전자서명(ECDSA·Ed25519) | 필수 | 초안(Claude) | [06-public-key-and-signatures](06-public-key-and-signatures/) |
| 07 | `key-exchange-forward-secrecy` | DH·ECDHE·전방 비밀성 | 권장 | 초안(Claude) | [07-key-exchange-forward-secrecy](07-key-exchange-forward-secrecy/) |
| 08 | `password-storage-and-kdf` | salt·느린 KDF(bcrypt·scrypt·Argon2)·pepper | 필수 | 초안(Claude) | [08-password-storage-and-kdf](08-password-storage-and-kdf/) |
| 09 | `randomness-and-key-management` | CSPRNG·키 수명·회전·KMS·시크릿 관리 | 필수 | 초안(Claude) | [09-randomness-and-key-management](09-randomness-and-key-management/) |

## 8.3 인증·인가

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 10 | `authentication-basics` | 지식/소유/생체, MFA·TOTP·WebAuthn | 필수 | 초안(Claude) | [10-authentication-basics](10-authentication-basics/) |
| 11 | `sessions-and-cookie-security` | 세션 ID·고정·쿠키 속성(HttpOnly·Secure·SameSite) | 필수 | 초안(Claude) | [11-sessions-and-cookie-security](11-sessions-and-cookie-security/) |
| 12 | `tokens-and-jwt` | 자기 포함 토큰·서명·만료·폐기 | 필수 | 초안(Claude) | [12-tokens-and-jwt](12-tokens-and-jwt/) |
| 13 | `jwks-and-key-rotation` | 공개키 배포·`kid`·캐시·회전 | 권장 | 초안(Claude) | [13-jwks-and-key-rotation](13-jwks-and-key-rotation/) · [../foundations/security/jwks.md](../foundations/security/jwks.md) |
| 14 | `oauth2-and-oidc` | 위임 인가·인가 코드+PKCE·ID 토큰 | 필수 | 초안(Claude) | [14-oauth2-and-oidc](14-oauth2-and-oidc/) · [../foundations/security/oidc.md](../foundations/security/oidc.md) |
| 15 | `access-control-models` | ACL·RBAC·ABAC·ReBAC, 객체 수준 인가 | 필수 | 초안(Claude) | [15-access-control-models](15-access-control-models/) |
| 16 | `identifiers-and-enumeration` | 순차 ID vs 랜덤·불투명 식별자 | 권장 | 초안(Claude) | [16-identifiers-and-enumeration](16-identifiers-and-enumeration/) · [../foundations/security/identity-and-ids.md](../foundations/security/identity-and-ids.md) |
| 17 | `refresh-token-rotation-and-revocation` | access·refresh 수명 설계, refresh 회전과 재사용 탐지, 동시 갱신 경합, 전체 로그아웃·강제 만료, 브라우저 저장 위치와 BFF | 필수 | 초안(Claude) | [17-refresh-token-rotation-and-revocation](17-refresh-token-rotation-and-revocation/) |

## 8.4 웹·애플리케이션 공격

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 18 | `injection` | SQL·명령·LDAP 인젝션, 파라미터 바인딩 | 필수 | 초안(Claude) | [18-injection](18-injection/) |
| 19 | `xss-and-csp` | 반사·저장·DOM XSS, 문맥별 인코딩, CSP | 필수 | 초안(Claude) | [19-xss-and-csp](19-xss-and-csp/) |
| 20 | `csrf-and-samesite` | 교차 사이트 요청 위조, 토큰·SameSite·Origin 검사 | 필수 | 초안(Claude) | [20-csrf-and-samesite](20-csrf-and-samesite/) |
| 21 | `same-origin-and-cors` | 출처 모델·SOP·CORS·preflight | 필수 | 초안(Claude) | [21-same-origin-and-cors](21-same-origin-and-cors/) |
| 22 | `ssrf` | 서버가 대신 요청하게 만들기 | 필수 | 초안(Claude) | [22-ssrf](22-ssrf/) |
| 23 | `deserialization-and-parser-attacks` | 안전하지 않은 역직렬화·XXE·문자열 lookup 기능 | 권장 | 초안(Claude) | [23-deserialization-and-parser-attacks](23-deserialization-and-parser-attacks/) |
| 24 | `memory-safety-exploits` | 버퍼 오버플로·UAF·ROP·완화책(ASLR·NX·카나리) | 권장 | 초안(Claude) | [24-memory-safety-exploits](24-memory-safety-exploits/) |

## 8.5 공급망·운영

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 25 | `supply-chain-security` | 의존성 위험·SBOM·서명·재현 빌드, 의존성 업데이트 운영(Renovate·EOL 런타임) 절 | 권장 | 초안(Claude) | [25-supply-chain-security](25-supply-chain-security/) |
| 26 | `security-logging-and-audit` | 보안 로그·감사 추적·단계적 강제(audit→enforce) | 권장 | 초안(Claude) | [26-security-logging-and-audit](26-security-logging-and-audit/) · [../foundations/security/audit-enforce-rollout.md](../foundations/security/audit-enforce-rollout.md) |
| 27 | `pii-classification-masking-retention` | 데이터 분류, 마스킹·토큰화·가명화, 로그·트레이스·에러 리포트 유출 차단(redaction), 보관 기한과 파기(백업 포함), 운영 데이터를 테스트에 복제 금지 | 필수 | 초안(Claude) | [27-pii-classification-masking-retention](27-pii-classification-masking-retention/) |
| 28 | `dos-and-abuse` | 볼륨·프로토콜·애플리케이션 계층 DoS, 봇·남용 | 권장 | 초안(Claude) | [28-dos-and-abuse](28-dos-and-abuse/) |

## 8.6 영역 마감

| # | 주제 | 요지 | 등급 | 상태 | 노트 |
|---|---|---|---|---|---|
| 29 | `security-symptom-index` | 역색인: 401 vs 403, CORS 에러, `invalid signature`, `kid not found`, CSRF 403, TLS alert, 로그인 폭주, 메타데이터 접근 로그 | 필수 | 초안(Claude) | [29-security-symptom-index](29-security-symptom-index/) |
| 30 | `security-incidents` | 실사건: Heartbleed(2014) · Equifax Struts 미패치(2017) · Capital One SSRF(2019) · Log4Shell(2021) · xz 백도어(2024) | 권장 | 초안(Claude) | [30-security-incidents](30-security-incidents/) |
