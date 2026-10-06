# log — security-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-07 | 인터뷰(보안 30편 · 원고 보강 · 앞과 같게, 합의 auto) → 명세 작성 직후 승인 기록 · 브랜치 docs/security-writing(main b65834ab) · 남은 양 보고: 142편(보안 30·데이터 분석 28·언어 27·아키텍처 22·수학 17·데이터 공학 17·네트워크 원고 1) | SPEC=1·MODE=auto |
| 2026-10-07 | 브리핑 3종(dsa판 구조 + 보안 안전 특칙: 자기 로컬 예제만·외부 대상 금지·무기화 코드 금지·취약 예 → 고친 예 짝) · 집필 발사(Opus 6병렬, 28편): 01(01·02·03·04·05) / 06(06·07·08·09) / 10(10·11·12·13·14) / 15(15·16·17) / 18(18·19·20·21·22) / 23(23·24·25·26·27·28) — 종합 29·30 후속 | 회수 대기 |
| 2026-10-07 | 집필 회수 1/6: 15·16·17(3 PASS, 각 10문항, [?] 3) — 실험(로컬 JVM, 가짜 사용자·토큰): IDOR v1 200 → 소유 조건 v2 404·기능 수준 403·ReBAC 경로, 순차 ID 열거 10000/10000 vs 64비트 0·32비트 생일 충돌·v7 시각 복원, refresh 회전 재사용 탐지·탭 경합 오판·유예/single-flight·valid_after · 원본 정정 1(git SHA-1) · 커리큘럼 후보: 17 📚 IETF 초안 → RFC 10017(BCP 212) 주장 — 점검에서 확인 · 사실 점검 발사 | 3 PASS |
| 2026-10-07 | 집필 회수 2/6: 06·07·08·09(4 PASS, [?] ~10) — 실험: Ed25519/ECDSA/RSA-PSS 1비트 변경 시 verify=false·Ed25519 결정적 서명·알고리즘 혼동 InvalidKeyException, X25519 RFC 7748 벡터·정적 RSA 키 유출 시 premaster 복구 vs ECDHE·로컬 openssl s_server Server Temp Key 유무, bcrypt 72바이트 절단(pyca 3.2.2·BC 1.81.1)·cost별 시간·scrypt/Argon2id RFC 벡터·pepper 선해시, Random 시드 재현·SHA1PRNG 사전 setSeed 결정적·봉투 암호화 KEK 회전, git 이력 가짜 키 탐지 · 사실 점검 발사 | 4 PASS |
| 2026-10-07 | 집필 회수 3/6: 18·19·20·21·22(5 PASS, 각 9문항, [?] 0) — 실험(전부 로컬): postgres:17 내부 전용 네트워크 문자열 연결 rows=3 vs 바인딩 0·서버 로그 $1·ORDER BY 바인딩 오해·LIKE 이스케이프, sh -c vs 인자 배열·--, LDAP 필터 이스케이프, headless Chrome 151 + 127.0.0.1 서버: XSS 인코딩·Trusted Types·CSP nonce vs Report-Only, SameSite별 쿠키 첨부·CSRF 토큰+Origin 403, CORS 서버200·JS reject·credentials+*·preflight 405·Origin 반사 vs 허용목록, SSRF 가드(고정 해석기, 실제 요청 없음)·리다이렉트 기본값 · 사실 점검 발사 | 5 PASS |
| 2026-10-07 | 집필 회수 4/6: 01·02·03·04·05(5 PASS, [?] 2) — 실험: fail-open 200 vs fail-closed 503·만료 없는 판정 캐시, 경계에서 신뢰 헤더 제거 403 vs 통과 200, ECB 반복 블록 vs GCM·GCM nonce 재사용 C1⊕C2=P1⊕P2·태그 변조 예외·CBC IV 조작 vs GCM 거부·AAD, SHA 값 FIPS 일치·눈사태·잘린 해시 생일 충돌, HMAC RFC 4231 일치·비교 시간·웹훅 재직렬화 401 · 원본 정정 4(약 900경·thousands·비밀번호는 KDF·mTLS) · 길이 확장 위조 데모는 노트에 넣지 않음(원리+출처만), scratchpad 파일도 메인이 삭제 · 사실 점검 발사 | 5 PASS |
| 2026-10-07 | 사실 점검 회수 15·16·17: 중대 0·중간 3(OWASP 2021 A01 94%는 시험 범위·발생률 3.81%·Optus 휴면 엔드포인트 iTnews 근거 + IP 분산·회수 지연 = min(캐시 TTL, access 수명)) · 경미 ~9 · RFC 10017(BCP 212, 2026-08) 실재·인용 절 일치 · SAS TokenSettings 기본값 확인 · 실험 재실행 9 · [?] 6→4 · 웹 표본 9 → codex 2차 발사 | 3 PASS |
| 2026-10-07 | codex(high) 2차 회수 15·16·17(3·7·6) → 판정 발사 | 회수 대기 |
| 2026-10-07 | 집필 회수 5/6: 10·11·12·13·14(5 PASS, 각 9문항, [?] 3) — 실험: TOTP RFC 6238 부록 B 18값 일치·계정 열거(메시지·시간 차) vs 고친 판, 세션 고정 200 vs 재발급 401, headless Chrome HttpOnly·Lax·기본값 2분 예외(0초 첨부/130초 미첨부)·http 루프백 Secure, JWT 검증기 none·HS/RS 혼동·exp·aud 취약 ACCEPT vs 고친 REJECT·JDK21 r=s=0 거부, JWKS 회전·무작위 kid 쿨다운·503 fail-closed·사전 게시(가상 시계), PKCE RFC 7636 벡터·redirect_uri 접두 비교·가로챈 코드 S256 400·state · 원본 정정 1(jwks kid 필수) · 사실 점검 발사 | 5 PASS |
| 2026-10-07 | 사실 점검 회수 06·07·08·09: **중대 1**(Spring Security 7.1.1 BCrypt — 새 해시만 72바이트 초과 거부, checkpw는 잘라서 비교(소스 컴파일 재실험: hashpw(73) IAE / checkpw(73,h72)=true) → 앱이 로그인 입력도 바이트 검사 · CVE-2025-22228 수정판 전체·CNA 점수 명시) · 중간 3(Ed25519 강도는 SP 800-57 표 경계 → RFC 7748 §7 서술·PBKDF2 비례 데이터가 JIT로 틀림 → Python 재측정·DSA-1571 원문에 없는 인용) · 경미 ~6 · 실험 재실행 11 · [?] 12→10 · 웹 표본 12 → codex 2차 발사 | 4 PASS |
| 2026-10-07 | 판정 회수 15·16·17(codex 지적 16): 채택 13·부분 3·기각 0 — NIST RBAC 객체별 권한 가능·Zanzibar 집합 연산·@PostAuthorize 트랜잭션 예외·시퀀스 번호 차이는 추정치(gap)·생일 충돌은 확률(약 69%)·v7/ULID 같은 ms 순서·v7 카운터 비트·Spring refresh 만료는 회전마다 재설정·Web Locks는 순서만·데모 유예 단순화 명시·BFF 쿠키 토큰 조건·__Host-Http- 표현·탭 경합 그림 실험 출력과 맞춤 | 3 PASS |
| 2026-10-07 | 사실 점검 회수 18~22: **중대 1**(20 실험 해석 — 저장 목록의 (Lax)는 Playwright가 빈 값을 채운 것, CDP 원값은 미지정 · 2분 경계 재실험 0초 첨부/126초 미첨부) · 중간 ~8(Trusted Types 지원 범위 MDN BCD·Spring CSP nonce 고정 문자열·Spring CSRF 제외 메서드 TRACE 포함·csrf.spa()는 7.0·Fetch preflight 캐시 키·IMDSv2 홉 1 vs 계정 기본 IMDSv2면 2·Lax+POST 임시 완화) · 경미 ~10(형제 노트 링크화 포함) · 실험 재실행 8 · [?] 0→0 · 영역 밖: network/07:300 security 22 미작성 · 웹 표본 15 → codex 2차 발사 | 5 PASS |
| 2026-10-07 | codex(high) 2차 회수 06~09 → 판정 발사 | 회수 대기 |
| 2026-10-07 | 집필 회수 6/6: 23~28(6 PASS, Q/A 8, [?] 2) — 실험(로컬·자작·방어): 역직렬화 필터 허용목록 REJECTED·XXE 기본 파서 vs disallow-doctype·log4j 2.14.1 lookup(무해 가짜 값, JNDI 없음) vs noLookups/2.24.3, 스택 카나리·ASLR·GNU_STACK·ASan 보고(관찰만), npm 락파일 무결성 EINTEGRITY·CycloneDX SBOM, audit→enforce 판정·로그 주입 이스케이프, PII 거부목록 vs 허용목록·마스킹·해시 가명 열거·crypto-shredding, 토큰 버킷 429·수신 타임아웃 · **28편 집필 완료** → 사실 점검 23~28 + 종합 29·30 집필 발사 | 6 PASS |
| 2026-10-07 | codex(high) 2차 회수 18~22 → 판정 발사 | 회수 대기 |
| 2026-10-07 | 사실 점검 회수 01~05: **중대 1**(04 — 현재 shattered.io 도메인은 연구팀 사이트가 아님(다른 주체 운영), 집필자가 그 문구('thousands') 인용 → 2017 보관본·Google 블로그 원문 '100,000배'로 정정, 도메인 변경 주의 줄) · 중간 ~6(SP 800-38D 'almost as important'·05 정답 깨진 문자열·isEqual 차이는 노이즈(재실행 −6~+8%)·SHAttered 수치 원문·Git 2.13.0 sha1dc) · 실험 재실행 7 · [?] 3→2 · 정합 메모: 다른 노트의 shattered.io 인용도 점검 필요 · 웹 표본 15 → codex 2차 발사 | 5 PASS |
| 2026-10-07 | 판정 회수 06~09(codex 지적 16): 채택 14·부분 2·기각 0 — CertificateVerify 범위·SP 800-57 f = 기준점 위수 비트(결론 유지)·DER 길이 가변·RFC 6979 같은 해시면 같은 k·r 중복 = k 또는 n−k 신호·CDH ≠ 이산 로그·PSK 재개 서명 생략·Temp Key 없음 ≠ 정적 RSA 확정·다운그레이드 표시 한계·psk_ke vs 일회용 티켓·DelegatingPasswordEncoder 접두어 없는 해시 예외·재해시 기본 bcrypt → argon2 지정·KDF는 막지 않고 비싸게·salt/nonce는 유일성·KEK 유출 시 DEK 재암호화 | 4 PASS |
| 2026-10-07 | codex(high) 2차 회수 01~05 → 판정 발사 | 회수 대기 |
| 2026-10-07 | 사실 점검 회수 10~14: 중대 0·중간 ~6(WebAuthn 서명 카운터 조건 L3 §6.1.1·세션 고정 실험은 헤더 단순화 명시·CVE-2015-9235는 HS/RS 혼동(none 아님)·RFC 7519 §7.2 범위 vs claim 검사 근거 분리·requireProofKey 판별 기본값(main/7.0 true, 6.5 false)·OidcIdTokenValidator iss 오류 문구) · 경미 ~6 · 실험 재실행 8 결정값 일치 · [?] 3→1 · 웹 표본 15 → codex 2차 발사 | 5 PASS |
| 2026-10-07 | 판정 회수 18~22(codex 지적 23): 채택 20·부분 3·기각 0 — PG 계획은 보통 Bind 시점·pgjdbc simple 모드·JPA 네이티브 쿼리 named 파라미터 비이식·DOM XSS 서버 전송 여부·setAttribute/Trusted Types/textContent 조건·JSTL escapeXml·사이트 = (scheme, 등록 도메인)·permitAll ≠ CSRF 제외·SSO form_post는 state·교차 출처 fetch 기본 credentials same-origin(실험 로그 cookie=no)·CORS preflight 차단·출처 3-튜플 예외·SSRF 정의·HttpURLConnection 스킴 다른 리다이렉트 미추종(재실험) | 5 PASS |
| 2026-10-07 | codex(high) 2차 회수 10~14 → 판정 발사 | 회수 대기 |
| 2026-10-07 | 판정 회수 01~05(codex 지적 17): 표 기준 채택 9·부분 8·기각 0(워커 머리 요약은 '부분 7·기각 1' — 03 #5를 AAD 부분 기각·사용량 한계 채택으로 나눈 차이, 표를 정본으로) — 공개 설계 비밀 = 키·비밀번호·판정 캐시 환경 조건·식별자 허용 목록·뷰 소유자 권한·IMDSv2 홉(AMI v2.0이면 2)·CBC IV 뒤집기·GCM H 도출 조건과 E_K(J₀)·96비트 J₀·SIV 사용량 한계·충돌 저항 정의·2차 역상 긴 메시지·MD 출력 절단·NIST SHA-1 퇴출 범위·위조 CA 백데이팅·서명은 부인 방지 판단을 '뒷받침' | 5 PASS |
| 2026-10-07 | 사실 점검 회수 23~28: **중대 2**(25 xz — '릴리스 tarball에만'·'유지보수자 사칭' → 원문 'upstream repository and tarballs have been backdoored', 주입 스크립트 일부만 tarball 전용 · 28 slowloris 출력 라벨 오류(실제는 클라이언트 EOF) → 라벨 고친 재실행 출력으로 교체) · 중간 ~14(OWASP XXE/A08 원문에 없는 인용·SolarWinds 18,000 배포/약 100 피해·GAO 날짜(2017-03-10)·npm 캐시가 있으면 변조 감지 안 됨(재실측)·npm 해시 표기 섞임·SBOM 효과 단정 해석 표시·mod_reqtimeout 의미·SYN 큐·K&R 출처 삭제·장난감 over-read 해석 한계) · 실험 재실행 12 · [?] +3 −1 · 웹 표본 18 → codex 2차 발사 | 6 PASS |
| 2026-10-07 | 판정 회수 10~14(codex 지적 24): 채택 21·부분 3·기각 0 — 패스키 = discoverable credential·푸시 번호 최소 6자리(SHALL)·TOTP 두 칸 확률 2/10^6·SSO 콜백 인가 요청 저장소 조건·SameSite 표 범위·JWT = JWS/JWE Compact·JwtTypeValidator 빈 typ 허용·차단 목록 TTL = exp+시계 여유·allowEmptyExpiryClaim·JWKS 그림 게시 시점·옛 키 제거 하한 = 최대 수명+여유·긴급 회전 캐시·이중 확인 코드·kid 401 원인·공개 클라이언트 client_id·aud SHOULD·토큰 없음엔 오류 코드 생략·MAC ID 토큰 키 = client_secret·auth_time/amr 조건부·ID 토큰 alg=none 예외 | 5 PASS |
| 2026-10-07 | codex(high) 2차 회수 23~28 → 판정 발사 | 회수 대기 |
| 2026-10-07 | 집필 회수 종합 29·30(2 PASS, 각 10문항, [?] 1) — 29: 8증상 절 + 에러 없는 증상, Triage.java(WWW-Authenticate로 401/403 사유 구분·PDP 장애 fail-open 200 vs 503) · 30: 5사건 1차 출처(NVD·GAO-18-559 IA 사본·DOJ 공소장·OCC·CSRB·oss-security·CISA), JarInventory(가짜 jar로 중첩 log4j-core 판 탐지)·Echo(길이 대조) · 다른 leaf 지적 5(정합 패스로) · **30편 집필 완료** · 사실 점검 발사 | 2 PASS |
| 2026-10-07 | 판정 회수 23~28(codex 지적 32 — 워커 머리 요약 '33·채택 31'은 오기, 표가 정본): 채택 30·부분 2·기각 0 — readObject 필드 복원 순서·maxrefs 정의·스트림 필터가 JVM 필터 대체·JAXP 기본 한도·XInclude 별도·Log4j 영향 범위(2.12.2/2.3.1 제외)·trustURLCodebase 기본 false·-no-pie 범위·NX vs W^X·카나리 함수 종료 시 검사·ASan 객체 내부 미탐·락파일 link 무해시·재현 빌드 입력 조건·Sigstore 순서·Rekor는 감시자 필요·셰이딩·automerge 모순·addKeyValue 무이스케이프·해시 체인 끝 삭제·HMAC 가명 일방향·FPE ≠ 볼트·고가치 토큰·3.4.1 vs 3.5.1·crypto-shredding 사본 조건·limit_conn 헤더 후 집계·트리화 조건·버킷 버스트 | 6 PASS |
| 2026-10-07 | 사실 점검 회수 29·30: **중대 1**(kid 캐시 회복 시각 공식 산술 오류 '회전 + TTL'(100+600≠600) → '회전 전 마지막 페치 + TTL' — 13 장애 1에서 옮겨 온 오류, 13은 정합 패스에서 수정) · 중간 2(Spring 6.5.5 JWKS 페치 실패 → AuthenticationServiceException 재던짐 → 500 경로를 소스+Servlet 명세로 판정, [?] 해소·JarInventory 재귀 설명) · 경미 4 · 실험 재실행 3 일치 · 사건 원문 대조 일치 · 웹 표본 6 → codex 2차 발사 | 2 PASS |
| 2026-10-07 | codex(high) 2차 회수 29·30(6·3) · **30편 codex 2차 완료** → 판정(29·30) + 정합 패스(30편: 13 회복 시각 공식·JWKS 장애 500·44832 출처별·IMDSv2 서술 통일·영역 안 링크·영역 밖 '미작성' 49줄 후보 링크만 교정) 한 워커 발사 | 회수 대기 |
| 2026-10-07 | 웹 교차 표본 회수(01~28): 97행 — 일치 95(관찰 8)·불일치 2(경미: 23 Log4Shell 제외 판 목록에 2.12.3·2.12.4·2.3.2 누락 · 27 SP 800-122 영향 수준 기준에 조직 피해·접근/사용 누락)·확인 불가 0 · 대체 출처 3(sec.gov 403·uber 406·w3.org TR 403 → Wayback/편집자 초안) · web-cross-sample.md 저장 · 불일치 2건은 정합 패스 회수 뒤 메인이 반영 | V5 충족 |
| 2026-10-07 | 판정 + 정합 회수: 29·30 codex 지적 9 채택 8·부분 1·기각 0(RFC 6750 error SHOULD·kid 키 선택 조건·교차 출처 ≠ 교차 사이트·CORS preflight·Basic은 자동 전송·Origin 반사 조건·Equifax 10개월 기준·재현 빌드 정의(25도)·blackbox 인증서 측정 대상) · 정합: 13 회복 시각 공식 수정(cs 전체 '회전+TTL' 0건)·13 JWKS 장애 500 조건·44832 출처별(23)·IMDSv2 서술 통일(02·22)·29 은퇴 대기 하한 13과 맞춤·21 핵심 문장 조건 · 영역 안 링크 61 · 영역 밖 '미작성' 48줄/32파일 링크 교정(api-design/04:354는 대상 불특정이라 표기만 삭제) · 남은 영역 밖: 원본 sha256-and-digest의 shattered.io 인용 3곳·평문 언급 7곳 | 30 PASS |
| 2026-10-07 | 메인 반영: 웹 불일치 2 — 23 Log4Shell 제외 판 '보안 수정판 2.12.2+·2.3.1+'(4곳+정답)·266행 NVD 문장 2.12.3 포함 · 27 SP 800-122 기준 문장 원문대로 · check 30 PASS · 링크 1,374 깨짐 0 · 정리 확인(sn-sec 컨테이너 0·네트워크 0·dangling 26·루트 새 파일 0) · 영역 표 재생성(초안 30, security README만 변경) | 커밋 준비 |
| 2026-10-07 | 커밋: f743425e(보안 30편+영역 표) · 4e2f4c49(영역 밖 링크 48줄) | 완료 |
| 2026-10-07 | 사용자 확인 "main 병합 + push" → 로컬 main ff는 됐으나 **push 거부(non-fast-forward)** — origin/main이 1bf8a642로 앞서 있음(10-06 issue 카드 커밋 6개, 다른 작업). 통합 방식 사용자 확인 대기 | push 미완 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 15·16·17 | Opus 독립 | 0 | 3 | ~9 | 6→4 | 웹 표본 9 · 실험 재실행 9 |
| 06·07·08·09 | Opus 독립 | 1 | 3 | ~6 | 12→10 | 웹 표본 12 · 실험 재실행 11 |
| 15·16·17 판정 | Opus(codex 지적 16) | 채택 13 | 부분 3 | 기각 0 | | 재실험 0 |
| 18~22 | Opus 독립 | 1 | ~8 | ~10 | 0→0 | 웹 표본 15 · 실험 재실행 8 |
| 01~05 | Opus 독립 | 1 | ~6 | ~5 | 3→2 | 웹 표본 15 · 실험 재실행 7 |
| 06~09 판정 | Opus(codex 지적 16) | 채택 14 | 부분 2 | 기각 0 | | 재실험 0 |
| 10~14 | Opus 독립 | 0 | ~6 | ~6 | 3→1 | 웹 표본 15 · 실험 재실행 8 |
| 18~22 판정 | Opus(codex 지적 23) | 채택 20 | 부분 3 | 기각 0 | | 재실험 1 |
| 01~05 판정 | Opus(codex 지적 17) | 채택 9 | 부분 8 | 기각 0 | | 재실험 0 |
| 23~28 | Opus 독립 | 2 | ~14 | ~15 | 2→4 | 웹 표본 18 · 실험 재실행 12 |
| 10~14 판정 | Opus(codex 지적 24) | 채택 21 | 부분 3 | 기각 0 | | 재실험 0 |
| 23~28 판정 | Opus(codex 지적 32) | 채택 30 | 부분 2 | 기각 0 | | 재실험 0 |
| 29·30 | Opus 독립 | 1 | 2 | 4 | 1→0 | 웹 표본 6 · 실험 재실행 3 |
| 웹 교차 01~28 | Opus 독립 | 불일치 2 | 확인 불가 0 | 관찰 8 | | 97행 |
| 29·30 판정 + 정합 | Opus(codex 지적 9) | 채택 8 | 부분 1 | 기각 0 | | 정합 모순 3 교정 |

## 생략한 검증

- 없음(빚 0). 참고 한계: 책 본문(Shostack·OSTEP 일부·CS:APP·K&R)은 장 단위·`[?]` · PCI DSS v4.0 원문 PDF 403 → PCI FAQ로 대체 · sec.gov/uber.com/w3.org TR은 Wayback·편집자 초안으로 대조 · Spring JWKS 장애 500 경로는 소스+명세 판정(앱 실행 없음) · 동기화 패스키 signCount·가명정보 가이드라인 판은 `[?]`.

## 완료 요약

- 산출: `cs/security/01~30` 30편(보강 6: 04·05·13·14·16·26 — 원본은 읽기만, 원본 오류는 "참고:" 줄) + 영역 표 재생성 + 영역 밖 '미작성' 48줄 링크 교정(32파일).
- 안전: 실험은 전부 자기 로컬 예제(취약판 → 고친 판), 외부 대상 요청 0, 무기화 코드 0. 길이 확장 위조 데모는 노트에서 빼고 scratchpad 파일도 삭제. 24는 완화책 관찰까지만.
- 검증: V1 30 PASS · V1b/V2 Opus 사실 점검(중대 6·중간 ~42, 실험 재실행 전 묶음) · V3 codex(high) 30/30, 지적 137 → 채택 115·부분 22·기각 0 · V4 정합(모순 3+알려진 4 교정, 영역 안 링크 61) · V5 웹 97행(불일치 2 반영) + 사실 점검 웹 표본 ~90 · 링크 1,374 깨짐 0.
- 중대 사례(재발 방지 관측): 실험 출력 해석(Playwright가 SameSite 빈 값을 Lax로 채움·slowloris 라벨)·도메인 주인 바뀐 출처(shattered.io)·Spring BCrypt checkpw 절단·xz 'tarball에만'·산술 오류 전파(13 → 29).
- 핵심 diff(실파일에서 복사): `cs/security/README.md` before `> 현황: 미작성 24 · 원고 있음 6 · 초안(Claude) 0 · 검수 완료 0` → after `> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 30 · 검수 완료 0`
- CS 이슈 아카이브: 0건(문서 작업).
