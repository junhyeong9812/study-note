# 요구사항 명세서 — language-writing

> 작성일: 2026-10-07 · 작업 폴더: `docs/plans/2026-10-07/language-writing/` · 브랜치: `docs/language-writing`(docs/network-lb-writing 749279e4에서 이어 만듦 — push는 남은 커리큘럼을 다 마친 뒤 한 번).
> 선행: data-engineering-writing(17편)·network-lb-writing(1편), 둘 다 커밋·미push. 브리핑·도구는 data-engineering판을 이식.

## 0. 요구사항 원문 (인터뷰)

- 원문: "남은 커리큘럼도 전부 진행 계획에 넣어서 쭉 진행하도록 해보자"
- Q/A (2026-10-07): 순서 **네트워크 원고 1 → 언어 27 → 데이터 분석 28** · push **영역마다 커밋만, 마지막에 한 번 묻기** · 방식은 앞 영역과 같게(원고 보강, 영역 밖 미작성 링크 교정, 출처 URL 사전 제공), 합의 auto · 동시 서브에이전트 ≤5("병렬로 순차처리").

## 1. 목표·대상 (필수)

- `cs/language/NN-slug/{1-question,2-summary,3-answer,metadata}.md` **27편**(커리큘럼 §6 01~27).
  - 보강 10편(원고는 읽기만): 01·02·03·04 ← `cs/foundations/compiler-pipeline` · 04·06·07·09 ← `cs/foundations/variables-and-memory` · 15 ← `cs/foundations/process-thread` · 20 ← `languages/c-cpp-csharp.md` · 21 ← `languages/README.md`·`languages/c-cpp-csharp.md`·`languages/{go,java,kotlin,rust}/언어-특성/`(병합)
  - 종합 2편(26 pl-symptom-index·27 pl-incidents)은 마지막.
- 영역 표 `cs/language/README.md` 재생성.
- 정합 단계에서 다른 영역 노트가 language 01~27을 "미작성"으로 가리키는 곳을 **링크만** 교정.

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말 없음, metadata 단계 `초안`, `흔한 오해:` 한 줄(선택).
- **I2 근거**: JLS·JVMS SE21, Java API·`java` 도구 문서, OpenJDK 소스, JEP(444·483 등), HotSpot GC 튜닝 가이드, JSR-133 FAQ·Cookbook, JOL·Shipilëv, GraalVM·Spring Native 문서, Cox 2007·2018, semver, Python 문서·PEP 703, LLVM PGO·ThinLTO·GCC 문서, C 표준 초안 N1570, CISA 메모리 안전 로드맵, 사고 원문(Cloudflare 2017-02-23·2019-07-02, CVE-2014-0160, npm 2016-03), 원고. 교재(Dragon Book·TAPL·GC Handbook·SICP·Sipser·JCIP·POSA2) 본문을 못 열면 장 단위·`[?]` — **기억으로 쓴 절·장·연도 번호에는 반드시 `[?]`**.
- **I3 커리큘럼 일치**: 각 행의 요지·선행·⚠·🔧·📚 전부, 선행 링크 실재 확인. **언어 중립 원리**(문법 레퍼런스 아님).
- **I4 기존 보존**: 원고·다른 영역 노트 수정 금지(정합 단계 링크 교정만 예외 — 문장 의미 변경 금지).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-lang-w<NN>-*`(`--rm --pull never --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp`, `--network none`), 이미지는 있는 것만(eclipse-temurin:21-jdk·python:3.12-slim·node:22-*·golang:1.23-alpine), pull·빌드·rmi·prune 금지, `docker create`/`rm` 대신 `--rm`만. 호스트 gcc 13·clang 18·objdump·python3(표준 라이브러리). sudo·패키지 설치 금지(pip·npm install·go get 포함). ReDoS·UB·request smuggling은 **원리와 방어 관찰까지**(자기 로컬 코드, 공격 재현·무기화 금지, 외부 대상 금지). 개인정보 금지, 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상(종합 선택) — briefing §5 예시(PrintCompilation 계층 전이·워밍업, 백트래킹 시간 증가 vs 선형 엔진, 깊은 중첩 StackOverflowError, var/let 클로저, 제네릭 소거 javap, 참조 카운트 순환, G1 로그, 탈출 분석 on/off, 가상 스레드 처리량, GIL CPU 작업, 메가모픽 호출, UB null 검사 삭제·sanitizer, -O0/-O2·LTO/PGO 크기·속도 등). 측정값은 이 호스트(i7-13700HX, `--cpus=2`) 한정.
- **I8 동시성**: 동시 서브에이전트 ≤5.

## 3. 기준소스 (필수)

- curriculum.md §6, `cs/language/README.md`, I2 출처, §1 원고, 관련 기존 노트(architecture/09·10·14·18·21, os/*, security/24, data-structure/29·34, algorithm/*, languages/{java,rust,c}/syntax/*)

## 4. 금지영역 (필수)

- language 밖 노트(정합 단계 링크 교정 제외 — 읽기만), 원고, 커리큘럼 본문(NEXT로), `check_new.py`·생성기, 생성 문서 수기 수정, 이 작업이 만들지 않은 컨테이너·볼륨·네트워크·이미지, I6의 금지 행위

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 → 판정 · V4 정합(architecture·os·security·data-structure 겹치는 주제 + 영역 밖 링크) · V5 웹 교차 40+, 링크 신규 깨짐 0, 영역 표 재생성, 정리 확인(sn-lang 컨테이너 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 27편, 사실 오류(명세 규칙·런타임 기본값·GC 동작·사고 수치) 위험. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: JDK 21·CPython 3.12·node 22·Go 1.23·gcc/clang으로 새 패키지 없이 실험이 된다 — GraalVM Native Image·JOL·JMH·free-threaded Python은 없으므로 문서와 대체 측정(`PrintFieldLayout`·직접 시간 측정)으로 보이고 그 사실을 적는다.
- **A2**: WebSearch 한도 소진 — 브리핑에 1차 출처 URL을 미리 넣고 curl로 연다.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑 3종(data-engineering판 이식 + 언어 실험·출처) | 브리핑 |
| 02 | 집필(Opus 5워커: 01·02·03·04·22 / 05·06·07·08·17·18 / 09·10·11·12·13 / 14·15·23·24·25 / 16·19·20·21), 종합 26·27 후속 | 27 PASS |
| 03 | 사실 점검 + 실험 재실행(끝난 묶음부터, 동시 ≤5) | packet |
| 04 | codex 2차 → 판정 → 정합(영역 밖 링크 포함) → 웹 | V3~V5 |
| 05 | 영역 표·정리·커밋(push는 끝에)·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-07)
- [x] auto
