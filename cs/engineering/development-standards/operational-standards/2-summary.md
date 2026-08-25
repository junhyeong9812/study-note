# cs/development-standards/operational-standards — 운영 기준 (ISO/IEC 20000-1 · Google SRE) — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 원고: 내가 직접 쓴다(작성 예정). 본문 절은 원고, 「전체 흐름」「핵심 문장」은 원고 압축, 맨 아래 「[Claude 추가]」 절만 원고에 없던 내용.
> 상위 묶음: [development-standards](../README.md)

## 전체 흐름

<!-- 원고 완성 후 압축 -->

## 본문 (원고 — 골격 후보, 쓰면서 바꿔도 됨)

두 기준은 같은 대상(서비스 운영)을 다른 높이에서 본다.

```text
ISO/IEC 20000-1   "서비스 관리 체계(SMS)가 갖춰야 할 요구사항"   — 조직·프로세스 (무엇을 갖출 것)
Google SRE        "그 요구를 엔지니어링으로 어떻게 달성하는가"   — 실천·측정 (어떻게 할 것)
```

### 1. ISO/IEC 20000-1 — SMS의 구조와 요구사항 조항
<!-- 2018판: 4 조직 상황 · 5 리더십 · 6 기획 · 7 지원 · 8 운영(서비스 포트폴리오·관계·공급·수요·설계/이행·해결/이행·보증) · 9 성과평가 · 10 개선 -->
### 2. 운영 프로세스 — 사고(Incident)·문제(Problem)·변경(Change)·릴리즈·용량·가용성·연속성
### 3. Google SRE — SLI/SLO/SLA와 에러 버짓, toil, 온콜·포스트모템
### 4. 두 기준의 연결 — 20000-1의 "가용성 관리"를 SRE의 SLO·에러 버짓으로 구현하기
### 5. 현장에서 만나는 상황 — 장애 대응 runbook·배포/롤백·관측성(로그·메트릭·트레이스)
### 6. 선행 주제 연결 — [straggler](../../straggler/)의 tail latency가 SLO 설계에 주는 의미

## 핵심 문장

-

## 관련 자료 (공부 레퍼런스)

- **ISO/IEC 20000-1:2018** — Service management system requirements: https://www.iso.org/standard/70636.html (유료 표준 — 조항 구조는 무료 개요로)
- **Google SRE 도서(무료 공개)**: https://sre.google/books/
  - Site Reliability Engineering (2016) — SLO·에러 버짓·toil·온콜·포스트모템
  - The Site Reliability Workbook (2018) — SLO 구현 실습
- Google SRE 자료 허브: https://sre.google/resources/
- 보조: ITIL 4(20000-1과 짝이 되는 실천 프레임워크 — 용어 대조용)

---

## [Claude 추가] 더 알면 좋은 것

> 원고 완성 후 작성. 복습 대상은 본문, 이 절은 확장 읽을거리.
