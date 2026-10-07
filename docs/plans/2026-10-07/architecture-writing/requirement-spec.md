# 요구사항 명세서 — architecture-writing

> 작성일: 2026-10-07 · 작업 폴더: `docs/plans/2026-10-07/architecture-writing/` · 브랜치: main(origin f5c89c5a + 로컬 log 커밋 1)에서 `docs/architecture-writing`.
> 선행: math-writing(17편, push f5c89c5a). 브리핑·도구는 math판을 재사용한다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "우선 다음 작업 진행해야겠네"
- Q/A (2026-10-07): 영역 **컴퓨터 구조 22편**(미작성 12 + 원고 10) · 진행 **앞 영역과 같게(원고 보강, 영역 밖 미작성 링크 교정, 검색 한도 대비 출처 URL 사전 제공), 합의 auto**

## 1. 목표·대상 (필수)

- `cs/architecture/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **22편**(커리큘럼 §4 01~23 중 17 제외 — 17 nand-flash-ftl은 이미 `cs/systems/nand-flash` 초안(Claude)으로 연결돼 있어 이번 범위 밖).
  - 보강 10편(원고는 읽기만): 01·03·04·06 ← `cs/foundations/data-representation` · 07·08·09 ← `cs/foundations/hardware-basics` · 10 ← `cs/systems/call-stack`(+`foundations/memory-management`) · 11 ← `cs/foundations/memory-management` · 16 ← `cs/systems/storage-media-workload`
  - 종합 2편(22 symptom-index·23 incidents)은 마지막.
- 영역 표 `cs/architecture/README.md` 재생성.
- 정합 단계에서 다른 영역 노트가 architecture 01~23을 "미작성"으로 가리키는 곳을 **링크만** 교정.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말 없음, metadata 단계 `초안`, `흔한 오해:` 한 줄(선택).
- **I2 근거**: CS:APP 3판(2·3·4·5·6·12장 — 출판사·저자 사이트 목차로 절 확인), OSTEP 36·37·44(PDF), P&H(장 번호는 열 수 있는 목차로만, 아니면 `[?]`), IEEE 754-2019(표준 본문 유료 → Goldberg 1991·문서), Unicode 표준·UAX #15·#29, RFC 3629, Intel·Arm 매뉴얼 공개분, JLS·JVM 명세, Java·Python 문서, Linux 커널 문서·man 페이지, Drepper 2007 "What Every Programmer Should Know About Memory", JSR-133·JMM FAQ, Dean "Latency Numbers", Kocher 외 2019·Lipp 외 2018, 사고 원문(GAO/IMTEC-92-26, Ariane 501 Inquiry Board 보고서, Intel FDIV 백서, 2038 관련 커널 문서). 책 본문을 못 열면 장 단위·`[?]` — **기억으로 쓴 절·정리 번호에는 반드시 `[?]`**(math 영역 교훈).
- **I3 커리큘럼 일치**: 각 행의 요지·선행·⚠·🔧·📚 전부, 선행 링크 실재 확인.
- **I4 기존 보존**: 원고·다른 영역 노트 수정 금지(정합 단계의 링크 교정만 예외 — 문장 의미 변경 금지).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-arch-w<NN>-*`(`--rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp`, `--network none`), 이미지는 있는 것만, pull·빌드·rmi·prune 금지. 호스트 gcc·objdump·file·iconv·python3(표준 라이브러리)·lscpu·numactl 가능, **sudo·커널 설정 변경 금지**(perf는 `perf_event_paranoid=4`라 사용 불가 — 시간 측정으로 대신), 패키지 설치 금지. 19(Spectre/Meltdown)는 **원리·완화책 관찰까지만**(`/sys/devices/system/cpu/vulnerabilities/*` 읽기, 문서) — 부채널 공격 재현 코드 금지. 개인정보 금지, 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상(종합 선택) — 예: signed/unsigned 비교(C), Java int 오버플로·`Math.addExact`·좁히기 캐스트, `0.1+0.2`·NaN 정렬·BigDecimal, UTF-8 바이트·서로게이트 절단·NFC/NFD·MySQL utf8 대신 문자열 길이 비교, 그래핌 vs 코드포인트 길이·터키어 i, 엔디안 덤프·구조체 패딩(`offsetof`), 가산기 시뮬레이션, `file`·`objdump`로 아키텍처·명령어 인코딩, 재귀 깊이·스택 프레임(`objdump -d`), 행/열 순회·연결 리스트 추적, 캐시 stride 충돌·false sharing(패딩 유무), 지연 자릿수(메모리 vs syscall vs 로컬 소켓), volatile 없는 플래그 대기·DCL, 분기 예측(정렬 vs 비정렬 합), 인터럽트 카운트(`/proc/interrupts` 읽기), 순차 vs 랜덤 I/O(작게, 임시 파일), NUMA 토폴로지(`lscpu`·`numactl -H` 읽기), SIMD 자동 벡터화(`-O3` vs `-O0`). 측정값은 이 호스트(i7-13700HX 하이브리드 P/E 코어, `--cpus=2`) 한정으로 적는다.

## 3. 기준소스 (필수)

- curriculum.md §4, `cs/architecture/README.md`, I2 출처, §1 원고, 관련 기존 노트(math/11·15, os/*, security/24, network/*, database/* 저장·I/O, data-structure/25, algorithm/42·43)

## 4. 금지영역 (필수)

- architecture 밖 노트(정합 단계 링크 교정 제외 — 읽기만), 커리큘럼 본문(NEXT로), `check_new.py`·생성기, 생성 문서 수기 수정, 이 작업이 만들지 않은 컨테이너·이미지, I6의 금지 행위

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정 · V4 정합(math·os·security·network·database 겹치는 주제 + 영역 밖 링크) · V5 웹 교차 24+, 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(sn-arch 컨테이너 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 22편, 사실 오류(표준 수치·하드웨어 동작·사고 수치) 위험. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 실험은 호스트 gcc·objdump와 eclipse-temurin:21-jdk·python 표준 라이브러리로 새 패키지 없이 된다. 하드웨어 카운터(perf)는 쓸 수 없어 시간 측정·비율로 보인다.
- **A2**: WebSearch 한도가 소진돼 있을 수 있다 — 브리핑에 주요 1차 출처 URL을 미리 넣고 curl/WebFetch로 연다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑 3종(math판 이식 + 구조 실험 예시·출처 URL 목록) | 브리핑 |
| 02 | 집필(Opus 병렬 5, 워커당 4편), 종합 22·23 후속 | 22 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | codex 2차 → 판정 → 정합(영역 밖 링크 포함) → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-07)
- [x] auto
