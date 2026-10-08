# log

| 시각 | 사건 | 결과 |
|---|---|---|
| 10-08 13:21 | 명세 승인 · auto | 흐름 13 + 구조 6 + pgvector + 후속 3 |
| 10-08 13:22 | task01: reference/tools/arch-map/(check-code-blocks.py 일반화·README·writer/verifier-brief) 작성, pgvector 클론 v0.8.7 f37c13f 고정. 스모크: MySQL 완성본 대조 | 아래 |
| 10-08 13:22 | 스모크: MySQL 598 bad=0 재현, 가짜 줄 MISMATCH·exit 1 | 통과 → 커밋 |
| 10-08 13:23 | task01 커밋 8fc4c1cc. 흐름 1차 배치 작성 4 위임: connection-startup+query-pipeline, executor+heap-insert-wal, buffer-manager+mvcc-visibility, nbtree-insert+heavyweight-lock | 대기 |
| 10-08 13:36 | buffer-manager(12파일, 11편으로 재편)·mvcc-visibility(11파일) 수신 bad=0. 발견: 작성 워커가 하위 fork 를 띄움 → 동시 상한 초과 위험. 브리핑 두 편에 '하위 워커 금지' 규칙 추가, 실행 중 작성 3에 SendMessage 통지. 검증 위임 (동시 4: 작성 3 + 검증 1) | 대기 |
| 10-08 13:38 | nbtree-insert(13파일, 12편)·heavyweight-lock(12파일, 11편 — fork 작성, 규칙 공지 전) 수신 · 메인 check + 신설 함수 정의줄 확인 | 아래 |
| 10-08 13:39 | nbtree 49·lock 40 블록 bad=0, 신설 함수 정의줄(_bt_findsplitloc L129, JoinWaitQueue L1173·호출 L1112, FastPathTransferRelationLocks L2829) 확인. 검증 위임 (동시 4: 작성 2 + 검증 2) | 대기 |
| 10-08 13:43 | buffer-manager+mvcc 검증 packet (11건 수정 — io_method=sync 일 때 틀리던 문장, freelist 복귀 경로 추가, db-engine 인용 원문화; 반증 ~95 유지) · 메인 재대조 5개 일치 → 커밋 |
| 10-08 13:43 | buffer-manager(c094119a)·mvcc-visibility(6ffe4f85) 커밋. commit+vacuum 작성 위임 (동시 4: 작성 3 + 검증 1) — vacuum 의 db-engine 절은 실제 인용만, '다음 한계' 표현 금지 지시 | 대기 |
| 10-08 13:45 | connection-startup(10파일)·query-pipeline(11파일) 수신 bad=0 → 검증 위임 (동시 4: 작성 2 + 검증 2) | 대기 |
| 10-08 13:47 | nbtree+lock 검증 packet (7건 수정, 분할 예시·fast-path·충돌 행렬 수치 오류 0; 반증 ~115 유지) · 메인 재대조 3개 일치, 남은 의심 L2301->L2302(호출 줄) 메인 수정 → 커밋 |
| 10-08 13:47 | nbtree(fade7fe1)·lock(c12049ea) 커밋. checkpoint+wal-redo 작성 위임. executor(11파일, 10번 standard_ExecutorFinish 로 교체)·heap-insert-wal(11파일) 수신 → 검증 위임 (동시 4: 작성 2 + 검증 2) | 대기 |
| 10-08 13:53 | connection+query 검증 packet (6건 수정, 97/98~100/101 연결 한계 경로 소스로 확정 — 98~100 일반 역할은 postinit L941 예약 검사, 101 은 proc.c L455; 반증 ~95 유지) · 메인 재대조 5개 일치 → 커밋 |
| 10-08 13:53 | connection-startup(9b0e5730)·query-pipeline(f60f98f9) 커밋 — 검증 완료 6흐름. streaming-replication 작성 위임 (동시 4: 작성 3 + 검증 1) | 대기 |
| 10-08 13:57 | executor+heap-insert-wal 검증 packet (13건 수정 — 불가능한 RedoRecPtr 예시(세그먼트 첫머리) +0x28 로, commit_delay 서술 조건부, 손계산 전부 일치; 반증 ~95 유지) · 메인 재대조 5개 일치, 번역문 따옴표 인용을 원문 인용으로 메인 수정 → 커밋 |
| 10-08 13:57 | executor(f7d1a61a)·heap-insert-wal(c15dc7fa) 커밋 — 검증 완료 8흐름. 구조 1차(process-model·shared-memory·page-tuple-layout) 작성 위임 (동시 4: 작성 4) | 대기 |
| 10-08 14:07 | streaming-replication(13파일, 12편 시간순 재편) 수신 bad=0 — 검증은 다음 자리. 구조 2차 작성 우선 위임 | 대기 |
| 10-08 14:12 | checkpoint(10파일, 9편 — CheckPointBuffers 를 04 에 흡수)·wal-redo(11파일) 수신 bad=0 — 흐름 13편 작성 완료. pgvector 작성 위임 | 대기 |
| 10-08 14:12 | pgvector 작성 위임(목록 확정 + 흐름 4~5 + api-index + README 기준 커밋) — 마지막 작성분 (동시 4: 작성 4) | 대기 |
| 10-08 14:17 | commit(11파일, 시간순 재편)·vacuum(14파일, 13편) 수신 bad=0 — SyncRep L1557 < ProcArray L2389 순서 확인 → 검증 위임 (동시 4: 작성 3 + 검증 1) | 대기 |
| 10-08 14:20 | 구조 1차(process-model 699·shared-memory 1075·page-tuple-layout 728줄, 48블록 bad=0) 수신 — sizeof 는 scratchpad 밖 out-of-tree 컴파일로 측정, 소스 레포 status clean 확인. checkpoint+wal-redo 검증 위임 | 대기 |
| 10-08 14:24 | 구조 2차(disk-layout 944·wal-record-format 965·buffer-descriptor-snapshot 1071줄, 49블록 bad=0) 수신 — 구조 6편 작성 완료. 크기는 대체 구조체 gcc 계산 → 검증 때 struct1 의 out-of-tree 생성 헤더로 재측정 지시 | - |
| 10-08 14:24 | 구조 6편 검증 위임(실제 생성 헤더 pg-struct1/build/src/include 로 sizeof/offsetof 재측정 지시) (동시 4: 작성 1(pgvector) + 검증 3) | 대기 |
| 10-08 14:26 | commit+vacuum 검증 packet (14건 수정 — SyncRep 취소 불가 이유 정정, eager scan 꺼짐 원인, MultiXactCutoff 추가; 반증 ~85 유지) · 메인 재대조 5개 일치, 남은 의심 중 vacuum README L723 autovacuum 경로 조건 메인 추가 → 커밋 |
| 10-08 14:26 | commit(03c08d67)·vacuum(9e894e0b) 커밋 — 검증 완료 10흐름. streaming-replication 검증 위임 (동시 4: 작성 1 + 검증 3) | 대기 |
| 10-08 14:30 | checkpoint+wal-redo 검증 packet (5건 수정 — 불가능한 예시 3개: backup_label C1 0x60->0x80(RUNNING_XACTS 필수), pd_upper 7900->7904(MAXALIGN), FPI 레코드 LSN 충돌; 반증 ~115 유지, LSN·세그먼트 계산 전부 일치) · 메인 재대조 6개 일치 → 커밋 |
| 10-08 14:33 | streaming-replication 검증 packet (9건 수정 — 위치 부등호에 근거와 재시작 직후 예외, StartReplication 거절 조건 방향, restart_lsn 은 덮어씀; 반증 ~60 유지) · 메인 재대조 5개 일치 → 커밋 — 흐름 13편 검증 완료 |
| 10-08 14:33 | streaming-replication 커밋(24adc760). 메인: PG 지도 README 완성 갱신(흐름 13·함수 137·구조 6 링크, vacuum 행 db-engine 문구 정정 — 후속 ①), api-index 링크 안내, opensource/index.md mysql·postgres 행 '완성' (후속 ②), postgres/index.md | pgvector·구조 검증 대기 |
| 10-08 14:42 | 구조 6편 검증 packet — 실제 서버 빌드·initdb(scratchpad, 소스 밖)로 pg_shmem_allocations·pageinspect·pg_waldump·pg_control CRC 실측, 숫자 오류 0, 인용·서술 9곳 + 코드 헤더 경로 49줄 수정. 검증 워커의 'db-engine 링크 미실존' 의심은 메인 재확인으로 기각(69 링크 0 broken). 잔존 postgres 프로세스 없음 → 커밋 |
| 10-08 14:52 | pgvector 검증 packet (8건 수정 — HNSW 결과 순서 근사 서술 정정(strict/relaxed), IVFFlat 비용·GenericXLog flags 정밀화, SQL 예시 문법; 반증 ~150 유지, 손계산·기본값 전부 일치) · 메인 재대조 3개 일치, 남은 의심 2건 메인 처리(README 검증 상태 문구, 02 메모리 예시 전제) → 커밋 |
| 10-08 14:52 | 최종 점검: PG 550·pgvector 104 블록 bad=0, @@ 0, opensource md 1325 상대 링크 깨짐 0, 소스 레포 2개 clean, 잔존 postgres 프로세스 0(pgrep 첫 결과는 검사 셸 자신 — 오탐) | 완료 |
| 10-08 14:52 | 사이클 마감: NEXT N0-my 후속 ①②③ 해소 기록. CS 이슈 0건 | - |

## 리뷰 ledger

| 대상 | 작성 | 검증(별도 워커) | 수정 | 메인 재대조 |
|---|---|---|---|---|
| buffer-manager · mvcc-visibility | 워커(+fork 1, 규칙 공지 전) | 1차 | 11 | 5 |
| nbtree-insert · heavyweight-lock | 워커(+fork 1, 규칙 공지 전) | 1차 | 7 (+메인 1) | 3 |
| connection-startup · query-pipeline | 워커 | 1차 | 6 | 5 |
| executor · heap-insert-wal | 워커 | 1차 | 13 (+메인 1) | 5 |
| commit · vacuum | 워커 | 1차 | 14 (+메인 1) | 5 |
| checkpoint · wal-redo | 워커 | 1차 | 5 | 6 |
| streaming-replication | 워커 | 1차 | 9 | 5 |
| 구조 6편 | 워커 2 | 1차(실서버 빌드 실측) | 9 + 헤더 경로 49줄 | 블록·링크 재확인, 검증 워커 오판 1 기각 |
| pgvector 5흐름 | 워커 | 1차 | 8 (+메인 2) | 3 |

## 생략한 검증

없음. 전 묶음 작성≠검증 분리, 예시 숫자 손계산·실측.

## 완료 요약

- 브랜치 `docs/postgres-architecture-body` (main 24dba712 기준, push 전).
- PostgreSQL: 흐름 13편(함수 문서 137편)·구조 6편·지도·api-index 완성. pgvector(v0.8.7): 흐름 5편(함수 문서 42편)·지도·api-index.
- 후속 처리: ①PG vacuum 행 db-engine 문구 정정 ②opensource/index.md mysql·postgres 행 '완성' ③reference/tools/arch-map/(대조 스크립트 sql 확장·브리핑 2·절차 README).
- 진행 중 규칙 추가: 하위 워커 금지(작성 워커가 fork 를 띄워 동시 상한 초과 위험).
