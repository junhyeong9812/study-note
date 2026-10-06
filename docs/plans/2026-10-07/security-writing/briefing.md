# 집필 브리핑 — 커리큘럼 leaf 새 노트 (보안, 2026-10-07)

> 명세: 같은 폴더 `requirement-spec.md`. 문서 규칙 정본: `cs/README.md` 「작성 규칙」.
> 형식 참고(내용 복사 금지): `cs/database/16-mvcc/`, `cs/algorithm/12-hash-functions/`, `cs/web-platform/` 아무 편

## 1. 입력

- **커리큘럼 행**: `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md` §8 보안 표에서 담당 slug를 찾는다. 요지·선행·⚠ 깨지면·🔧·📚 칸은 **모두 다뤄야 할 요구사항**이다. §8 머리 문단(원리 → 암호 기초 → 인증·인가 → 웹/앱 공격 → 공급망·운영, **TLS/PKI 본문은 network/29~32에만** — 여기선 링크)도 읽는다.
- **영역 표**: `cs/security/README.md`(생성 문서). 원본(보강 6편): `cs/foundations/security/{sha256-and-digest,hmac,jwks,oidc,identity-and-ids,audit-enforce-rollout}.md` — **읽기만**.
- **선행 링크**: 다른 영역 노트는 실제 경로로(`ls` 확인). 자료구조·알고리즘은 커리큘럼 번호 ≠ 폴더 번호(대응표 = `cs/data-structure/curriculum.md`·`cs/algorithm/curriculum.md` 노트 칸). math·language 등 아직 없는 영역은 그 영역 README + "미작성".
- **근거**: Saltzer–Schroeder 1975, Shostack 『Threat Modeling』, OWASP(Top 10 2021·2025, ASVS 4.0.3/5.0, Cheat Sheet Series), NIST SP(800-38D GCM·800-63B 인증·800-132·800-57 키 관리·800-90A·800-218), RFC(2104 HMAC, 4226 HOTP, 6238 TOTP, 6265·6265bis 쿠키, 6749·6750·7636·9700 OAuth, 7519·7517·7518 JWT/JWK, 7748, 8446, 8017, 9106 Argon2, 8032 Ed25519), W3C(CSP Level 3, WebAuthn), WHATWG Fetch(CORS), OpenID Connect Core, CWE·NVD·CISA KEV, 사고 원문(GAO·FTC·공식 사후 보고·CVE). 책 본문을 못 열면 장 단위·`[?]`.
- WebSearch·WebFetch·curl이나 **실험(§5)** 으로 **실제 확인**한 것만 사실로 쓴다.

## 2. 출력 — `cs/security/<NN-slug>/`의 4파일

- 제목 다음 줄부터 바로 본문(머리말·표식 없음). metadata.md:

```
# metadata

| 항목 | 값 |
|---|---|
| 단계 | 초안 |
| 초안 | 2026-10-07 (Claude) |
| 검수 | — |
| 학습 | — |
```

- 2-summary.md 골격(최상위 `## ` 7개, 이 순서):

```
# security/<NN-slug> — <한 줄 제목> — 정리 (힌트)

## 해결하는 문제
## 동작·원리
## 쓰이는 자료구조·알고리즘
## 적용 — 풀어나가는 법
## 장애 시나리오와 대처
## 핵심 문장
## 관련 주제·근거
```

- **동작·원리**: ASCII 그림 먼저(신뢰 경계·데이터 흐름, 블록 모드 그림, HMAC 이중 해시, 서명/검증 흐름, DH 교환, 세션·쿠키 흐름, OAuth 인가 코드+PKCE 시퀀스, CORS preflight 시퀀스, 인가 결정 흐름), 글은 그 해설.
- **쓰이는 자료구조·알고리즘**: 예) Merkle–Damgård·스펀지, HMAC, 모듈러 지수·타원곡선, 해시 체인(HOTP), 역할 그래프·관계 튜플(ReBAC), 토큰 버킷(남용 제한), 문맥 인코딩 상태 기계. 기존 cs 노트가 있으면 링크(`../../algorithm/12-hash-functions/2-summary.md` 등).
- **적용**: 코드는 Java 21 기본(JS·TS — 브라우저 쪽), 설정(Spring Security·HTTP 헤더·CSP), 진단(로그·헤더·`openssl` 출력 읽기). **취약 예 → 고친 예** 짝으로 보인다.
- **장애 시나리오와 대처**: 3~5개. 현상 → 보이는 형태(응답 코드·로그·브라우저 콘솔) → 원인 → 대처, ⚠ 칸 포함.
- **핵심 문장** 3~6, **관련 주제·근거**(선행·후속 링크, 1차 출처 URL·RFC 절, 실험 목록).
- 1-question / 3-answer: `cs/database/16-mvcc/`와 같은 틀. 질문 6~10(왜 / 예측 / 경계 / 연결 / 장애 진단), 정답 번호·개수 일치.

## 3. 쓰는 방식 (합의된 기준)

1. 그림 먼저, 글은 그림 해설. 2. 용어는 처음 나오는 자리 바로 아래 `  - *용어*: 설명`, 헷갈리기 쉬운 것만 `    - 흔한 오해: …` 한 줄(근거 있는 것만). 3. 한 문장에 한 개념. 4. 코드: Java 21(기본)·JS·TS, 저수준은 C. 셸은 진단·실험 구동에만. 5. 수치·기본값·버전은 출처·실험으로 확인했을 때만, 못 하면 `[?]`, 예시 수치는 "(예시)".

## 3-1. 앞 영역에서 나온 주의

- `[?]`는 확인 못 한 것에만. "항상·모든·반드시·절대" 금지(예외가 있으면 조건). 노트 안 모순 금지(그림 vs 글, 요약 vs 정답, 실험 출력 vs 해석).
- **표준·판·버전 한정**: "RFC 6265bis 초안 기준", "Chrome 기본값(Lax-by-default)", "OWASP Top 10 2021의 A01", "NIST SP 800-63B-4". 브라우저 기본값·라이브러리 기본값은 판마다 다르다 — 확인한 판을 적는다. 표준 요구(MUST) vs 권고(SHOULD) vs 제품 기본값 vs 관례를 구분한다.
- **계층을 섞지 않는다**: 프로토콜 보장 vs 라이브러리 기본값 vs 애플리케이션 책임. TLS 세부는 network/29~32 링크.
- **사고·CVE 수치는 원문 그대로**(날짜·피해 규모·CVE 번호·CVSS), 해석은 "해석"이라고 표시. 2차 보도만 있으면 그렇게 밝힌다.

## 4. 기존 노트 이어받기 (보강 6편)

- 원본은 수정하지 않는다. 먼저 읽고, 설명된 것은 "기초는 원본 §N" 링크 + 한두 줄 요약. 빈 곳(⚠ 장애, 실험, 적용, 질문·정답)을 채운다. 원본에 틀린 내용이 있으면 새 leaf에 바르게 쓰고 `참고: 원본 §N의 "…"는 …(근거)` 한 줄.

## 5. 실험 근거 (명세 I7, 필수 — 단 §6 안전 특칙 안에서)

- 편마다 실행 가능한 핵심 주장 1개 이상(29·30 선택). **방어 관점**: 자기가 만든 작은 예제에서 "취약 설정이면 이렇게 보인다 → 고치면 이렇게 막힌다"를 보인다. 예:
  - 03: 같은 블록 반복 평문을 ECB vs GCM으로 암호화해 암호문 패턴 비교, GCM에 같은 nonce를 두 번 쓰면 두 암호문 XOR = 두 평문 XOR임을 확인(교육용 고정 키), 태그 변조 시 복호 실패 예외.
  - 04·05: 해시 3성질 설명 + `openssl dgst`·Java `MessageDigest` 출력, HMAC RFC 4231 테스트 벡터 재현, 문자열 비교 vs `MessageDigest.isEqual` 차이(측정은 노이즈가 크므로 범위·한계를 함께).
  - 06·07: Ed25519/ECDSA 서명·검증(`openssl`·Java), 메시지 1비트 변경 시 검증 실패, `openssl s_client`는 로컬 `openssl s_server`에만.
  - 08: bcrypt 72바이트 이후 무시 확인(라이브러리 버전 명시), 비용 인자별 해시 시간, Argon2 파라미터(가능한 라이브러리만 — 설치 불가면 문서 근거).
  - 09: `SecureRandom` vs `Random` 출력 예측 가능성(알려진 시드 재현), 시크릿 스캐너 개념(로컬 일회용 git 저장소에 가짜 키 문자열 — 실제 키 금지).
  - 10·17: TOTP를 RFC 6238 부록 B 테스트 벡터로 재현, 로그인 실패 메시지 차이로 계정 존재가 드러나는지(로컬 예제 앱).
  - 11·19·20·21: 로컬 127.0.0.1 서버 2개(다른 포트 = 다른 출처) + 호스트 headless Chrome으로 쿠키 SameSite·HttpOnly 동작, CSP가 인라인 스크립트를 막는 콘솔 메시지, CORS preflight와 "서버는 200인데 브라우저가 차단", CSRF 토큰 유무.
  - 12·13·14: JWT 검증기가 `alg:none`·알고리즘 혼동을 **거부하는지** 확인(자기 검증 코드·로컬 키), `kid` 캐시 미스 시나리오, PKCE `code_challenge` 계산을 RFC 7636 부록 B 벡터로.
  - 15·16: 로컬 예제 API에서 객체 수준 인가 누락(IDOR)과 고친 판, 순차 ID vs 랜덤 ID 추측 가능성 계산(생일 경계).
  - 18: 로컬 postgres:17 일회용 컨테이너에서 문자열 연결 쿼리 vs `PreparedStatement` 결과 차이.
  - 22·23: SSRF·역직렬화는 **허용 목록·안전 설정이 요청/객체를 거부하는 것**을 보인다(로컬 전용, 외부·메타데이터 주소로 실제 요청 금지 — 거부 로직만 테스트).
  - 24: C 예제에서 스택 카나리 abort, ASLR 주소 변화, AddressSanitizer 보고 — 완화책 관찰까지만.
  - 25·26·27·28: SBOM·의존성 목록 도구 출력(있는 도구만), 로그 redaction 전후, 토큰 버킷 남용 제한(로컬 부하는 작게).
- 노트에 싣는 것: 실험 코드 핵심, 환경(제품·버전), **실제 출력**, 관찰과 해석. 출력 블록 앞에 `(실험, OpenJDK 21 temurin, 2026-10-07)` 식으로. 비결정 값은 여러 번 돌린 범위.
- 실험으로 보일 수 없는 주장은 1차 출처로 대신하고 그 사실을 적는다. packet에 실험 목록(주장·코드 경로·명령·환경·출력 요지).

## 6. 실행 환경과 안전 규칙 (보안 영역 특칙 포함)

- **안전 특칙(명세 I6)**: 대상은 **자기가 만든 로컬 예제뿐**. 외부 호스트·실제 서비스·제3자 시스템으로의 공격성 요청·스캔 금지(문서 열람용 curl은 허용). 무기화된 익스플로잇, 셸코드, 악성코드, 탐지·방어 우회 기법, 실제 자격 증명 수집 코드는 쓰지 않는다. 공격은 원리 수준 설명 + 방어 쪽 실험으로 다룬다. 실제 키·토큰·비밀번호를 만들거나 노트에 싣지 않는다(예시는 테스트 벡터·명백한 가짜 값).
- **컨테이너**: 자기 전용 일회용 `sn-sec-w<NN>-*`, `--rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp`, 가능하면 `--network none`, 둘 이상 연결이 필요하면 자기 내부 네트워크(`docker network create --internal sn-sec-w<NN>-net`, 끝나면 삭제). 이미지는 있는 것만(`eclipse-temurin:21-jdk`, `python:3.12-slim`, `node:22-alpine`·`node:22-bookworm-slim`, `postgres:17`, `nginx:alpine`) — pull·빌드·rmi·prune 금지. 끝나면 `docker ps -a --filter name=sn-sec-w<NN>` 비었는지 확인.
- **Java**: 호스트 java는 8. `docker run … eclipse-temurin:21-jdk java X.java`. JDK(`javax.crypto`·`java.security`)로 되는 것은 JDK만. 라이브러리(jjwt·nimbus-jose-jwt·spring-security-crypto 등)가 필요하면 `maven:3.9-eclipse-temurin-21` + 소규모 pom + 공용 로컬 저장소(`-v <scratchpad>/ts/m2:/m2 -Dmaven.repo.local=/m2`), 의존성을 받은 뒤 실행은 `--network none`. python은 `python:3.12-slim` 표준 라이브러리만. pip·apt·npm 전역 설치 금지.
- **브라우저**: 호스트 `/usr/bin/google-chrome` headless + scratchpad 안 `playwright-core`(`npm install --prefer-offline`, 브라우저 다운로드 금지 — 웹 플랫폼 작업 방식). 로컬 서버는 127.0.0.1의 임의 포트, 끝나면 종료. 브라우저·서버 프로세스는 자기 PID만 종료(`pkill -f` 금지).
- **호스트 도구**: `openssl`(로컬 파일·로컬 `s_server`만), python3, gcc. 
- **부하 상한**: 실행 수십 초 이내, `--cpus=2` 이하.
- **파일 위치**: `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/sec/<담당 첫 번호>/`에만. 저장소 루트·노트 폴더 금지.
- **개인정보 금지**: 요청·파일·노트 어디에도 사용자 식별 정보 금지.
- **금지**: 이 작업이 만들지 않은 컨테이너·볼륨·이미지(`sn-*` 다른 접두·`payment-*`·`jun-bank-*` 등).

## 7. 하지 말 것

- 담당 폴더 밖 수정 금지, git 조회만, 리프에 md만, 하위 에이전트·fork 금지.

## 8. 자기 검증

- `python3 docs/plans/2026-09-30/network-writing/check_new.py <담당 폴더들>` → 전부 PASS. 노트 안 모순·실험 출력 vs 본문 수치 대조.

## 9. 반환 packet (한국어)

- 폴더·check 결과 · 편별 근거 · 실험 목록(주장·코드 경로·명령·환경·출력 요지) · 정리 확인 · `[?]` 목록 · ⚠ 커버 · 원본 오류(보강 편) · 미완료
