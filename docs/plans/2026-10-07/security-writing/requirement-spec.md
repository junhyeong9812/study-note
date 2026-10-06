# 요구사항 명세서 — security-writing

> 작성일: 2026-10-07 · 작업 폴더: `docs/plans/2026-10-07/security-writing/` · 브랜치: main(b65834ab — origin/main 8121ff99 + 로컬 log 커밋 1)에서 `docs/security-writing`.
> 선행: errata-fixes(push 8121ff99). 브리핑·도구는 dsa-remaining판을 재사용한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 진행하고 커리큘럼 작성 얼마나 남았어?"
- Q/A (2026-10-07): 영역 **보안 30편**(미작성 24 + 원고 6) · 진행 방식 **앞 영역과 같게(원고 보강), 합의 auto**
- 남은 양(2026-10-07): 보안 30 · 데이터 분석 28 · 언어 27 · 아키텍처 22 · 수학 17 · 데이터 공학 17 · 네트워크 원고 1 = **142편**(작성 완료 502편)

## 1. 목표·대상 (필수)

- `cs/security/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **30편**(커리큘럼 §8 01~30).
  - 보강 6편(원본 `cs/foundations/security/*`는 읽기만): 04 ← sha256-and-digest · 05 ← hmac · 13 ← jwks · 14 ← oidc · 16 ← identity-and-ids · 26 ← audit-enforce-rollout
  - 종합 2편(29 symptom-index·30 incidents)은 마지막.
- 영역 표 `cs/security/README.md` 재생성(30편 `초안(Claude)`).

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말 없음, metadata 단계 `초안`, `흔한 오해:` 한 줄(선택).
- **I2 근거**: Saltzer–Schroeder 1975, Shostack 『Threat Modeling』, OWASP(Top 10 2021·2025, ASVS, Cheat Sheet), NIST(SP 800-38D·800-63B·800-132·800-57·SP 800-218), RFC(2104·4226·6238·6265·6749·6750·7519·7517·7636·7748·8446·9106·9700 등), W3C(CSP·Fetch·WebAuthn), WHATWG Fetch, 각 CVE·사고 보고서(NVD, GAO, 공식 사후 보고), 원본 노트. TLS/PKI 본문은 network/29~32에만 둔다(링크).
- **I3 커리큘럼 일치**: 각 행의 요지·선행·⚠·🔧·📚 전부, 선행 링크 실재 확인.
- **I4 기존 보존**: 원본·다른 영역 노트 수정 금지(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 안전(보안 영역 특칙)**: 실험은 **방어 관점의 작은 재현만** — 자기 일회용 로컬 컨테이너(`sn-sec-w<NN>-*`, `--network none` 또는 내부 전용 네트워크, `--cpus=2`, `-u`)에서, 자기가 만든 취약 예제 코드와 그 **수정판의 차이**를 보인다. 외부 호스트·실제 서비스·제3자 시스템을 대상으로 하는 요청·스캔·공격 금지. 실제 무기화된 익스플로잇·셸코드·악성코드·우회 기법·실제 자격 증명 수집 코드 금지. 메모리 안전(24)은 완화책 관찰(ASLR·카나리·NX 동작, AddressSanitizer 보고)까지만. 사고·CVE는 공개 보고서 수준으로 서술. 이미지 pull·빌드 금지(있는 것만), 개인정보 금지, 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상(종합 선택) — 예: ECB 패턴 노출 vs GCM, GCM nonce 재사용 시 XOR 관계, 길이 확장(H(key‖msg)) vs HMAC, 비상수 시간 비교 측정, bcrypt 72바이트 절단, TOTP 계산 = RFC 6238 테스트 벡터, 쿠키 속성·SameSite 동작(로컬 브라우저), JWT `alg` 혼동을 거부하는 검증기, 파라미터 바인딩 vs 문자열 연결(로컬 DB), CSP가 인라인 스크립트를 막는 것(헤드리스 브라우저), CORS preflight, 로그 redaction.

## 3. 기준소스 (필수)

- curriculum.md §8, `cs/security/README.md`, I2 출처, 원본 `cs/foundations/security/*`, network/29~32(TLS 단일 출처)

## 4. 금지영역 (필수)

- security 밖 노트(읽기만), 커리큘럼 본문(NEXT로), `check_new.py`·생성기, 생성 문서 수기 수정, 이 작업이 만들지 않은 컨테이너·볼륨·이미지, I6의 금지 행위

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정 · V4 정합(network/29~32·api-design·web-platform·reliability·engineering-practice/15 포함) · V5 웹 교차 24+, 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(sn-sec 컨테이너 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 30편, 사실 오류(RFC·NIST 수치·CVE·사고 수치) 위험. 문서라 되돌리기 쉬움. I6 안전 경계는 stakes와 무관하게 유지.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 실험은 eclipse-temurin:21-jdk·python:3.12-slim·node:22·postgres:17·호스트 headless Chrome(웹 플랫폼 작업에서 확인)·호스트 openssl로 새 이미지 없이 된다.
- **A2**: codex 사용 가능 — 한도 시 Opus 대체.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(dsa판 이식 + 보안 안전 특칙 I6·실험 예시) | 브리핑 3종 |
| 02 | 집필(Opus 병렬 6, 워커당 4~5편), 종합 29·30 후속 | 30 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | codex 2차 → 판정 → 정합 → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-07)
- [x] auto
