# cs/development-standards/security-standards — 보안 기준 (OWASP Top 10 · NIST SSDF · OWASP ASVS) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 원고: 내가 직접 쓴다(작성 예정). 본문 절은 원고, 「전체 흐름」「핵심 문장」은 원고 압축, 맨 아래 「[Claude 추가]」 절만 원고에 없던 내용.
> 상위 묶음: [development-standards](../README.md)

## 전체 흐름

<!-- 원고 완성 후 압축 -->

## 본문 (원고 — 골격 후보, 쓰면서 바꿔도 됨)

세 문서는 층이 다르다 — 공부 순서도 이 순서가 자연스럽다.

```text
OWASP Top 10   "무엇이 가장 많이 뚫리는가"      — 위험 목록 (인식)
OWASP ASVS     "내 앱이 무엇을 만족해야 하는가"  — 검증 요구사항 (제품 기준)
NIST SSDF      "개발 과정을 어떻게 운영해야 하는가" — 프로세스 관행 (조직 기준)
```

### 1. OWASP Top 10 — 가장 흔한 위험 10가지와 각각의 근본 원인
<!-- 최신판(2025 RC 또는 2021) 기준으로 10항목 + "내 코드에서 어디가 해당되는가" -->
### 2. OWASP ASVS — 검증 수준(L1/L2/L3)과 챕터 구조
<!-- ASVS 5.0(2025) 기준. 인증·세션·접근제어·입력검증·암호·에러/로깅·데이터보호·통신·API 등 -->
### 3. NIST SSDF (SP 800-218) — 네 그룹의 관행
<!-- PO(Prepare the Organization) · PS(Protect the Software) · PW(Produce Well-Secured Software) · RV(Respond to Vulnerabilities) -->
### 4. 세 기준의 연결 — Top 10의 위험 하나를 ASVS 요구사항과 SSDF 관행으로 추적해 보기
### 5. 현장에서 만나는 상황 — 코드 리뷰·CI·의존성 관리에 어떻게 심는가

## 핵심 문장

-

## 관련 자료 (공부 레퍼런스)

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **OWASP ASVS** (Application Security Verification Standard): https://owasp.org/www-project-application-security-verification-standard/ — 원문 repo: https://github.com/OWASP/ASVS
- **NIST SP 800-218, SSDF v1.1** (Secure Software Development Framework): https://csrc.nist.gov/pubs/sp/800/218/final
- 보조: OWASP Cheat Sheet Series(각 항목 구현 지침): https://cheatsheetseries.owasp.org/ · CWE Top 25: https://cwe.mitre.org/top25/

---

## [Claude 추가] 더 알면 좋은 것

> 원고 완성 후 작성. 복습 대상은 본문, 이 절은 확장 읽을거리.
