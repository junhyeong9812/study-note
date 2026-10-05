# 요구사항 명세서 — dsa-remaining-writing

> 작성일: 2026-10-05 · 작업 폴더: `docs/plans/2026-10-05/dsa-remaining-writing/` · 브랜치: main(cf3b4e73 — origin/main 0310d6cb + 로컬 log 커밋 1)에서 `docs/dsa-remaining-writing`.
> 선행: engineering-practice-writing(20편, push 0310d6cb). 브리핑·실험 규칙·도구는 engineering-practice판을 재사용한다.
> **동시 실행 금지**: 같은 작업 트리에서 다른 실행이 이 영역을 진행하지 않는다는 전제. 착수·회수마다 `git log`·`git branch`·파일 mtime으로 흔적을 확인하고, 있으면 멈추고 사용자에게 묻는다.

## 0. 요구사항 원문 (인터뷰)

- 원문: "다음 작업 진행하자"
- Q/A (2026-10-05): 영역 **자료구조·알고리즘 잔여 21편**(공부 우선순위 — 기본기 먼저) · 원고 있는 leaf **보강 방식**(§17과 같게) · 검증 **앞 영역과 같게, 합의 auto**

## 1. 목표·대상 (필수)

- 커리큘럼 §2·§3의 미작성·원고 있음 leaf **21편**. 폴더 = **커리큘럼 번호 `NN-slug`**(생성기가 `cs/<area>/NN-slug`로 찾는다 · 다른 영역 노트가 이미 `algorithm/33-lossless-…` 등으로 링크). 기존 myway 폴더(`data-structure/01~35`·`algorithm/01~30`)는 원래 번호 그대로라 **번호 접두가 겹치는 폴더가 생긴다**(예: `02-linked-list`와 `02-adt-and-cost-contracts`) — 커리큘럼 §2·§3 머리말의 설계(번호 = 학습 순서, 노트 링크 칸이 대응).
  - 자료구조 8: 01-data-structures-basics(보강, 원본 `cs/foundations/data-structures-basics`) · 02-adt-and-cost-contracts · 25-ring-buffer · 26-timer-structures · 29-concurrent-data-structures · 19-lsm-merge-model(보강, 원본 `cs/data-structure/lsm-merge-model`) · 43-ds-symptom-index · 44-ds-incidents
  - 알고리즘 13: 01-algorithm-basics(보강, 원본 `cs/foundations/algorithm-basics`) · 02-asymptotic-analysis · 03-recursion · 09-sorting-in-practice · 11-external-sort-and-k-way-merge · 12-hash-functions · 33-lossless-compression-lz77-huffman · 34-modern-codecs-lz4-zstd-brotli · 39-randomized-algorithms · 40-complexity-p-np · 41-computability-and-halting · 42-alg-symptom-index · 43-alg-incidents
  - 종합 4편(ds 43·44, alg 42·43)은 마지막.
- 생성 문서 `cs/data-structure/curriculum.md`·`cs/algorithm/curriculum.md` 재생성(두 영역은 컬렉션 README와 이름이 겹쳐 curriculum.md로 생성됨).

## 2. 경계·불변식 (필수)

- **I1 형식**: 7절 골격, Q/A 6~10, 제목 아래 머리말·표식 없음, metadata 단계 `초안`. 용어 풀이 `흔한 오해:` 한 줄(선택, 근거 있는 것만).
- **I2 근거**: CLRS 3판, Sedgewick 『Algorithms』 4판, Knuth TAOCP(정렬·탐색), Sipser 『Introduction to the Theory of Computation』, 원논문(Varghese–Lauck 1987 타이머 휠, Michael–Scott 1996 큐, Huffman 1952, Ziv–Lempel 1977, Aumasson–Bernstein SipHash 2012, Carter–Wegman 1979, Duda ANS, O'Neil LSM 1996), RFC 1951(DEFLATE)·8878(zstd)·7932(Brotli), LZ4 포맷 문서, OpenJDK 소스(TimSort·HashMap·ConcurrentHashMap·ArrayBlockingQueue·DelayQueue·ScheduledThreadPoolExecutor), Netty HashedWheelTimer, Linux kernel timer wheel 문서, 28C3 HashDoS(Klink–Wälde 2011)·oCERT-2011-003, Bloch 2006 블로그, Stack Overflow 2016-07-20 사후 보고, Cloudflare 2019-07-02 사후 보고, 원본 노트. 책 본문을 못 열면 장 단위·`[?]`.
- **I3 커리큘럼 일치**: 각 행의 요지·선행·⚠·🔧·📚 전부, 선행 링크 실재 확인(기존 myway 폴더는 실제 번호로 — 커리큘럼 번호와 다름).
- **I4 기존 보존**: 원본 노트·기존 myway 66편·다른 영역 노트 수정 금지(링크만).
- **I5 링크·트리**: 새로 깨는 링크 0, 리프에 md만.
- **I6 재현 안전**: 전용 일회용 `sn-dsa-w<NN>-*`(`--cpus=2`, `-u $(id -u):$(id -g) -e HOME=/tmp`), 이미지 **pull·빌드·rmi·prune 금지**(있는 것만 — eclipse-temurin:21-jdk, python:3.12-slim, node:22-*). 호스트 도구(gcc·python3·gzip·zstd·xz)는 사용 가능, 새 패키지 설치 금지. 개인정보 금지, 저장소 루트 파일 금지.
- **I7 실험 근거 우선**: 편마다 실행 가능한 핵심 주장 1개 이상을 실제 출력으로(종합 4편 선택) — 예: ArrayList vs LinkedList 같은 인터페이스 다른 비용, 링 버퍼 덮어쓰기·가득 참 판정, 타이머 힙 vs 휠 삽입/만료 비용, ABA 재현·lock-free vs 락 처리량, HashMap 충돌 키로 성능 절벽(트리화 전후), TimSort "Comparison method violates its general contract!", 외부 정렬 k-way 병합, 재귀 깊이 → StackOverflowError, 이진 탐색 `(lo+hi)/2` 오버플로, gzip/zstd/xz 비율·속도, 허프만 부호 길이, 정규식 백트래킹 시간 폭증, 퀵정렬 무작위 피벗. 출력은 실제 실행만.

## 3. 기준소스 (필수)

- curriculum.md §2·§3, 생성 문서 `cs/{data-structure,algorithm}/curriculum.md`, I2 출처, §1 원본 노트, 기존 myway 노트(링크 대상)

## 4. 금지영역 (필수)

- 대상 21편 밖 노트(원본·기존 myway·다른 영역 — 읽기만), 커리큘럼 본문(NEXT로), `check_new.py`·생성기
- 생성 문서 수기 수정 · 이번 작업이 만들지 않은 컨테이너·볼륨·이미지

## 5. 검증 방법 (필수)

- V1 check_new · V1b 사실 점검이 편당 실험 1개+ 재실행 · V2 Opus 사실 점검 · V3 codex(high) 2차 리뷰(한도 시 Opus 적대 리뷰) → 판정 · V4 정합(기존 myway 노트·network·database·reliability·security 링크 포함) · V5 웹 교차 24+, 링크 신규 깨짐 0, 생성 문서 재생성, 정리 확인(sn-dsa 컨테이너 0)

## 6. stakes (필수)

- **중간** — 새 학습 자료 21편, 사실 오류(복잡도·도구 동작·사고 수치·코덱 수치) 위험. 문서라 되돌리기 쉬움.

## 7. 자율성

- [x] auto

## 8. load-bearing 가정

- **A1**: 실험은 호스트 gcc·python3·압축 도구와 eclipse-temurin:21-jdk(Java 21)로 새 이미지·패키지 없이 된다. lz4·brotli CLI가 없으므로 34의 그 둘은 문서·RFC 근거(실측은 gzip·zstd·xz).
- **A2**: codex는 사용 가능(§17에서 20/20) — 한도에 닿으면 Opus 대체.

## 9. task 분해

| task | 목표 | acceptance |
|---|---|---|
| 01 | 브리핑(engineering-practice판 이식 + 자료구조·알고리즘 실험 예시·번호 규칙) | 브리핑 3종 |
| 02 | 집필(Opus 병렬 5, 워커당 3~4편), 종합 4편 후속 | 21 PASS |
| 03 | 사실 점검 + 실험 재실행 | packet |
| 04 | 2차 리뷰(codex) → 판정 → 정합 → 웹 | V3~V5 |
| 05 | 생성 문서·정리·커밋·(확인 후) push·log·NEXT·측정로그 | V5 |

## 승인 상태

- [x] 6칸
- [x] 합의: 사용자 답변(2026-10-05)
- [x] auto
