# 요구사항 명세서 — domain-modeling-writing

> 작성일: 2026-10-03 · 작업 폴더: `docs/plans/2026-10-03/domain-modeling-writing/` · 브랜치: main(08c53572)에서 `docs/domain-modeling-writing`.
> 선행: network·os·database·distributed·reliability·software-design(모두 main 반영·push). 브리핑·실험 규칙·도구는 software-design판을 재사용한다.
> **동시 실행 금지**: 같은 작업 트리에서 다른 세션이 이 영역을 진행하지 않는다는 전제(10-01~02에 같은 세션의 두 실행이 병렬로 같은 영역을 진행해 중복·덮어쓰기가 생겼다). 착수·회수마다 `git log`·파일 mtime으로 다른 실행의 흔적을 확인한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 진행하자" → (10-03) 영역 선택 질문
- Q/A (2026-10-03): 영역 **도메인 모델링**(`cs/domain-modeling/`, 커리큘럼 §13) · 검증 **앞 영역(분산·신뢰성·설계)과 같게** — 실험 근거 우선(I7), Opus 사실 점검·실험 재실행, codex 2차 리뷰(한도 10-04 08:53까지 → 그 전이면 Opus 대체), 판정·정합·웹 표본

## 1. 목표·대상 (필수)

- `cs/domain-modeling/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **28편**(커리큘럼 §13 01~28)
  - 보강 3편(원본은 그대로, 링크로 이어받음): 01 `domain-modeling/domain-vs-application-logic` · 02 `domain-modeling/pojo` · 21 `systems/server-design/03-data-layer.md`(CQRS 절)
  - 연습 트랙 2편: 15 `domain-modeling/basic`(30편)·26 `domain-modeling/advanced`(30편) — 컬렉션은 그대로 두고, leaf는 **트랙 안내 노트**(무엇을 어떤 순서로 풀고 각 문제가 어느 전술·전략 개념을 연습하는지, 7절 골격)로 쓴다.
  - 종합 2편(27 dm-symptom-index·28 dm-incidents)은 마지막.
- 생성 문서 `cs/domain-modeling/curriculum.md`(기존 컬렉션과 이름이 겹치는 영역) 재생성: 28편 전부 `초안(Claude)`.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말·표식 없음, metadata 단계 `초안`.
- **I2 근거**: Evans 『DDD』(2부·4부)·『DDD Reference』 2015, Vernon 『IDDD』·"Effective Aggregate Design" 2011, Fowler PoEAA·martinfowler.com(AnemicDomainModel·CQRS·EventSourcing 등), Brandolini Event Storming, Khononov 『Learning DDD』, Fowler 『Analysis Patterns』(Quantity·Money·Accounting), java.time/IANA tz DB·RFC 9557, ISO 4217, JSR 354(Moneta), PostgreSQL 17 문서, 원논문·공식 문서. 책 원문을 못 열면 장 단위·`[?]`(목차·출판사 발췌로 확인한 범위만 단정).
- **I3 커리큘럼 일치**: §13 각 행의 요지·⚠·🔧·📚 전부, 선행 링크(software-design·database·distributed·api-design 등 실재 경로 확인).
- **I4 기존 보존**: 원본·basic·advanced 컬렉션·다른 영역 노트 수정 금지(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 컨테이너 `sn-dm-w<NN>-*`(`--cpus=2`, 포트 미개방 또는 127.0.0.1), 끝나면 `docker rm -fv <이름>`. **`docker * prune`·일괄 삭제 금지, 이미지 새로 받기 금지**(이미 있는 이미지만: eclipse-temurin:21-jdk, maven:3.9-eclipse-temurin-21, postgres:17, redis:7-alpine 등), 개인정보 금지, 저장소 루트 파일 금지(절대 경로).
- **I7 실험 근거 우선 — 도메인 해석**: 편마다 실행 가능한 핵심 주장 1개 이상을 실험으로 보인다(15·26·27·28 제외 가능) — 예: 빈약 모델 vs 풍부 모델에서 불변식 위반이 몇 경로로 새는가(테스트로 셈), 애그리거트 경계·동시 수정 시 낙관적 잠금 충돌(PG 17 재현), java.time DST 전이(존재하지 않는/겹치는 로컬 시각), BigDecimal·double 반올림·배분 오차(1원 분배), 이중 기입 원장의 차대 불일치 검출(SQL), 대사(reconciliation) 누락·중복 탐지, 상태 기계 불법 전이 차단, 유효 일자 규칙 조회. 출력은 실제 실행 결과만, 실험 코드·환경·출력·관찰을 노트에 싣는다.

## 3. 기준소스 (필수)

- curriculum.md §13, `cs/domain-modeling/curriculum.md`, I2 출처, §1 원본 노트와 basic·advanced 컬렉션

## 4. 금지영역 (필수)

- domain-modeling 새 leaf 밖 노트(basic·advanced·원본 포함 — 읽기만), 커리큘럼 본문(NEXT로)
- 생성 문서 수기 수정 · 이번 작업이 만들지 않은 컨테이너·볼륨·이미지

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 리뷰, 한도 시 Opus 적대 리뷰 → 판정 · V4 정합(software-design·database·distributed 선행 포함) · V5 웹 교차 20+, 링크 신규 깨짐 0, 생성 문서 재생성, 정리 확인

## 6. stakes (필수)

- **중간** — 새 학습 자료 28편, 사실 오류(책 인용·라이브러리 동작·시간대 규칙) 위험.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 도메인 실험은 JDK 21 단일 파일(temurin 일회용 컨테이너)과 PostgreSQL 17 일회용 컨테이너로 충분하다. 외부 라이브러리(Moneta 등)는 maven 이미지로 scratchpad에 받는다.
- **A2**: codex는 10-04 08:53까지 한도 — 집필·점검을 먼저 하고, 2차 리뷰 시점에 한도가 남아 있으면 Opus 대체.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(software-design판 이식 + 도메인 실험 예시·트랙 안내 노트 규칙) | 브리핑 |
| 02 | 집필(Opus 병렬 5, 워커당 5~6편), 종합 27·28 후속 | 28 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | 2차 리뷰 → 판정 → 정합 → 웹 | V3~V5 |
| 05 | 생성 문서·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-03)
- [x] auto
