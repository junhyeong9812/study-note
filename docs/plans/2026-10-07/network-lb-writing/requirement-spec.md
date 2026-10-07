# 요구사항 명세서 — network-lb-writing

> 작성일: 2026-10-07 · 작업 폴더: `docs/plans/2026-10-07/network-lb-writing/` · 브랜치: `docs/network-lb-writing`(docs/data-engineering-writing ea99abb5에서 이어 만듦 — push는 남은 커리큘럼을 다 마친 뒤 한 번).
> 선행: data-engineering-writing(17편, 커밋 ea99abb5, 미push). 브리핑·도구는 data-engineering판을 이식.

## 0. 요구사항 원문 (인터뷰)

- 원문: "남은 커리큘럼도 전부 진행 계획에 넣어서 쭉 진행하도록 해보자"
- Q/A (2026-10-07): 순서 **네트워크 원고 1 → 언어 27 → 데이터 분석 28** · push **영역마다 커밋만, 마지막에 한 번 묻기** · 방식은 앞 영역과 같게(원고 보강, 영역 밖 미작성 링크 교정, 출처 URL 사전 제공), 합의 auto · 동시 서브에이전트 ≤5.

## 1. 목표·대상 (필수)

- `cs/network/46-load-balancers-and-proxies/{1-question,2-summary,3-answer,metadata}.md` **1편**(커리큘럼 §7 46행) — 원고 `cs/systems/server-design/02-request-path.md` §3(로드밸런서)·§5 세션 절을 분할 이어받아 보강(원고는 읽기만).
- 영역 표 `cs/network/README.md` 재생성.
- 정합 단계에서 다른 영역 노트가 network/46을 "미작성"·원고 경로로만 가리키는 곳을 **링크만** 교정.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말 없음, metadata 단계 `초안`.
- **I2 근거**: Maglev(Eisenbud 외 NSDI 2016 PDF), RFC 7239, nginx·HAProxy·Envoy·Kubernetes·AWS ELB·Spring Boot Actuator 공식 문서, 원고. 기억으로 쓴 절·연도·버전에는 `[?]`.
- **I3 커리큘럼 일치**: 요지·선행(35·11)·⚠(깊은 헬스체크 연쇄, XFF 스푸핑, sticky 불균형)·🔧(라운드로빈·least-conn·일관 해싱/Maglev)·📚 전부.
- **I4 기존 보존**: 원고·다른 영역 노트 수정 금지(정합 단계 링크 교정만 예외).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-net46-*`(`--rm --pull never --cpus=2`, nginx·백엔드는 이 작업 전용 `--internal` 네트워크 — 끝나면 삭제), 이미지는 있는 것만(nginx:1.27-alpine·eclipse-temurin:21-jdk·python:3.12-slim), pull·빌드·rmi·prune 금지, `docker create`/`rm` 대신 `--rm`만. XFF 스푸핑은 로컬 자기 구성에서 신뢰 경계 유무 차이만(외부 대상·우회 기법 금지). 개인정보 금지, 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: nginx 분배(round-robin vs least_conn)·수동 헬스체크·재시도, 깊은 헬스체크 연쇄, XFF realip, 스티키 불균형, Maglev 테이블 disruption(Java 모형), 드레이닝 중 1개 이상.
- **I8 동시성**: 동시 서브에이전트 ≤5.

## 3. 기준소스 (필수)

- curriculum.md §7 46행, `cs/network/README.md`, 원고 `cs/systems/server-design/02-request-path.md`, I2 출처, 관련 기존 노트(network/11·15·19·21·35·36·38·47·49·52, reliability/14·50, api-design/19)

## 4. 금지영역 (필수)

- network/46 밖 노트(정합 단계 링크 교정 제외), 원고, 커리큘럼 본문, `check_new.py`·생성기, 생성 문서 수기 수정, 이 작업이 만들지 않은 컨테이너·볼륨·네트워크·이미지

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정 · V4 정합(원고·network 35·47·reliability/14 + 영역 밖 링크) · V5 웹 교차 6+(1편 분량), 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(sn-net46 컨테이너·네트워크 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 1편, 제품 기본값·알고리즘 사실 오류 위험. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: nginx:1.27-alpine + JDK 백엔드로 분배·헬스체크·realip·드레이닝을 로컬 내부 네트워크에서 재현할 수 있다(능동 헬스체크·slow_start는 nginx Plus 전용이라 문서로 대신).
- **A2**: WebSearch 한도 소진 — 브리핑의 URL을 curl로 연다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑 3종(data-engineering판 이식 + LB 실험·출처) | 브리핑 |
| 02 | 집필(Opus 1) | PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | codex 2차 → 판정+정합(영역 밖 링크) → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋(push는 끝에)·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-07)
- [x] auto
