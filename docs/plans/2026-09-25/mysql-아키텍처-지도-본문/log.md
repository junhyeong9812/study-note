# log

| 시각 | 사건 | 결과 |
|---|---|---|
| 21:39 | 명세 승인 · auto | 흐름 13 + 구조 6 |
| 21:54 | 파일럿 connection-thread 수신 (9파일 1791줄) · 메인 check_blocks | 25블록 중 1 모호(동명 파일) → 스크립트를 GitHub 링크 경로로 해소하게 수정 후 0 bad. 형식 확정, 구조 slug 확정 |
| 21:55 | 워커 9 병렬 위임 (general-purpose): 검증 1(connection-thread), 작성 6(흐름 2개씩 — command-dispatch+commit-2pc, row-insert+btree-insert, mtr-redo+flush-checkpoint, buffer-pool-fetch+crash-recovery, mvcc-read+purge, record-lock+online-ddl), 구조 2(3편씩) | 대기 |
| 22:05 | 세션 중단 후 재개: 디스크 확인(작성 8건 산출물 0, 파일럿만 존재) → 워커 9 SendMessage 로 재개 | 대기 |
| 22:08 | connection-thread 검증 packet 수신 (8건 수정, 반증 ~30 유지) · 메인 표본 대조 | 수정 1번(L1378->L1377)은 검증 워커 오류 — sed 로 L1378 이 my_net_set_read_timeout 확인, 원복. 07 pkt_nr 모호 표현은 net_new_transaction(mysql_com.h L1091) 근거로 메인이 명확화 |
| 22:08 | 사용자 지시 "워커 최대 4개씩 순차" → 작성 워커 4개 중지(mvcc+purge, lock+ddl, 구조 2), 4개 유지 | 중지분은 앞 배치 끝난 뒤 재개 |
| 22:29 | mtr-redo(11파일, 29블록)·flush-checkpoint(11파일, 43블록) 수신 · 메인 check_blocks | 둘 다 bad=0 |
| 22:30 | 검증 워커 위임: mtr-redo + flush-checkpoint (동시 4: 작성 3 + 검증 1) | 대기 |
| 22:31 | buffer-pool-fetch(11파일)·crash-recovery(13파일, 함수 12개로 재편 — 지도 갱신 필요) 수신 · 메인 check_blocks | 확인 중 |
| 22:31 | buffer-pool 29·crash-recovery 46 블록 bad=0. 메인 반증: 'restart_dictionary -> innobase_dict_recover' 는 중간 DDSE_dict_recover(bootstrapper.cc L943/L84/L91 handlerton) 누락 → 검증 워커에 교정 지시. 구조 워커 중지 흔적: structure/ 빈 폴더 3개 | 검증 위임 (동시 4: 작성 2 + 검증 2) |
| 22:35 | command-dispatch(10파일)·commit-2pc(11파일) 수신 · 메인 check_blocks | 확인 |
| 22:35 | command-dispatch 49·commit-2pc 58 블록 bad=0 → 검증 위임 (동시 4: 작성 1(row+btree) + 검증 3) | 대기 |
| 22:35 | row-insert(12파일, 11_row_ins_sec_index_entry 추가)·btree-insert(10파일) 수신 · 메인 check_blocks | 확인 |
| 22:36 | row-insert 35·btree-insert 37 bad=0. 빈 자리 → 중지했던 mvcc-read+purge 작성 워커 재개 (동시 4: 검증 3 + 작성 1). row+btree 검증은 다음 자리 | 대기 |
| 22:40 | mtr-redo·flush-checkpoint 검증 packet (17건 수정, 반증 49 유지, 크기 관계 soft·adaptive·aggressive 추가) · 메인 재대조 | 수정값 4개 sed 1줄 확인 일치. 남은 2건 메인 처리: 03 L1791->L1792, 07 시간축 m_event(L2581)가 fsync(L2599)보다 먼저 — batch_completed L643-647·wait_for_pending_batch L527 확인 후 그림·문단 수정 |
| 22:40 | mtr-redo(525c6ba)·flush-checkpoint(713ebb4) 커밋. row-insert+btree-insert 검증 위임 (동시 4: 검증 3 + 작성 1(mvcc+purge)) | 대기 |
| 10-08 12:19 | 재개(10-08): 원 워크트리 소멸, 원 브랜치는 09-28 다른 세션이 main 병합(1133083a — 미검증 6흐름 + record-lock 3파일 포함). main 에서 docs/mysql-architecture-finish 분기, 워크트리 재생성. 남은 일: 6흐름 재검증, record-lock 완성, online-ddl·mvcc-read·purge, 구조 6, 지도 갱신. 동시 워커 ≤4 | 진행 |
| 10-08 12:20 | 임시 폴더 소실 → check_blocks·작성/검증 브리핑 재작성(추가 규칙 통합). 기존 10흐름 재대조 bad=0. 1차 배치 4: 검증 3(buffer+crash, dispatch+2pc, row+btree), 작성 1(mvcc-read+purge) | 대기 |
| 10-08 12:29 | buffer-pool+crash-recovery 검증 packet (13건 수정, 반증 74 유지) · 메인 재대조 | n_iterations>1(L1408, 시작 0 L1314)·!is_dirty(L477)·hton dict_recover(L5429)·레코드별 old_lsn(L3051-3052/3081/3123) 확인 일치 → 커밋 |
| 10-08 12:29 | buffer-pool-fetch(3fc2a36d)·crash-recovery(02999d42) 커밋. record-lock 완성+online-ddl 작성 위임 (동시 4: 검증 2 + 작성 2) | 대기 |
| 10-08 12:30 | command-dispatch+commit-2pc 검증 packet (10건 수정, 반증 ~75 유지, 크래시 조합은 조건부 서술로) · 메인 재대조 8개 일치 → 커밋 |
| 10-08 12:30 | command-dispatch(5ae82c6a)·commit-2pc(124334cc) 커밋. 구조 편 1차(tablespace-page·record-format·redo-log-files) 작성 위임 (동시 4: 검증 1 + 작성 3) | 대기 |
| 10-08 12:32 | row-insert+btree-insert 검증 packet (13건 수정, 반증 ~95 유지, 분할 예시를 page_get_middle_rec 실계산으로) · 메인 재대조 8개 일치 → 커밋 |
| 10-08 12:33 | row-insert(59616d1a)·btree-insert(70698830) 커밋 — 기존 10흐름 검증 완료. 구조 편 2차(undo-segments·memory-structures·threads) 작성 위임 (동시 4: 작성 4) | 대기 |
| 10-08 12:43 | record-lock(12파일, 46블록)·online-ddl(10파일, 42블록) 수신, bad=0. 발견: main(1133083a) 의 record-lock 01·02 에 미치환 @@ 자리표시자 — 이 브랜치에서 치환됨(전체 grep 0). 검증 위임 (동시 4: 작성 3 + 검증 1) | 대기 |
| 10-08 12:44 | 구조 1차(tablespace-page 768·record-format 614·redo-log-files 757줄, 38블록 bad=0) 수신. 메인 상수 대조: FIL_PAGE_DATA 38·REC_N_NEW_EXTRA_BYTES 5·블록 512·파일 헤더 2048 일치. 검증 위임 (동시 4: 작성 2 + 검증 2) | 대기 |
| 10-08 12:48 | 메인: 지도 README 완성 갱신(흐름 13·함수 129·구조 6, 전 링크, online-ddl 행 추가, purge 행 db-engine 문구 정정 — 지도 단계의 '다음 한계로 예고' 서술은 메인 오류, 실제 근거 10-01 과제 3 답·10-03 KDoc), api-index 링크·후보 문구, mysql/index.md 골격 문구 | PG 지도 vacuum 행 같은 오류 — 범위 밖, 보고 |
| 10-08 12:49 | 구조 1차 검증 packet (그림 수치 전부 일치, 산문 4곳 수정) · 메인 재대조: inode 식 L228·LOG_START_LSN 16*512·mlog 67~76 일치 → 커밋 |
| 10-08 12:50 | record-lock+online-ddl 검증 packet (10건 수정, 호환 행렬 16칸·시나리오 3개 손계산 일치, LOCK 절별 MDL 차이 추가) · 메인 재대조 5개 일치 → 커밋 |
| 10-08 12:53 | 구조 2차 검증 packet (8건 수정: history_len n_added_logs, buf_pool_get 64페이지 정렬 확정, LSN 주석 뒤바뀜 확정, page_hash 래치 16, 시작 3곳 맥락, timeout_event set=L5961 — 메인 브리핑의 'L416 유일' 은 메인 오류) · 메인 재대조 6개 일치 → 커밋 |
| 10-08 12:55 | mvcc-read+purge 검증 packet (13건 수정: RU view 수명, 08 체인 예시 불가능 시나리오, suspend 조건 반대 서술 등, 반증 ~60 유지) · 메인 재대조 6개 일치 → 커밋 |
| 10-08 12:56 | 최종 점검: opensource/mysql 코드 블록 598 bad=0, md 153 상대 링크 깨짐 0, @@ 0, mysql-server status clean. 금지 기호 22건은 지도·api-index·index 의 가운뎃점·〃 — ES 지도도 쓰는 레포 관례(15파일/1파일)라 유지 | 완료 |
| 10-08 12:56 | 사이클 마감: NEXT.md N0-my 추가(PG vacuum 문구·opensource/index mysql 행·도구 재사용). CS 이슈 0건(아카이브 없음) | - |

## 리뷰 ledger

| 대상 | 작성 | 검증(별도 워커) | 수정 수 | 메인 재대조 |
|---|---|---|---|---|
| connection-thread | 파일럿 | 1차 | 8 (+메인이 검증 오류 1 원복) | 표본 + 07 명확화 |
| mtr-redo · flush-checkpoint | 워커 | 1차 | 17 | 4 + 남은 2건 메인 처리 |
| buffer-pool-fetch · crash-recovery | 워커 | 재검증(10-08) | 13 | 4 + old_lsn 루프 확인 |
| command-dispatch · commit-2pc | 워커 | 재검증 | 10 | 8 |
| row-insert · btree-insert | 워커 | 재검증 | 13 | 8 |
| record-lock · online-ddl | 워커 | 1차 | 10 | 5 |
| mvcc-read · purge | 워커 | 1차 | 13 | 6 |
| 구조 6편 | 워커 2 | 1차 2 | 4 + 8 | 3 + 6 |

## 생략한 검증

없음. stakes 낮음 + 날조 방지를 위해 전 흐름에 작성≠검증 분리 적용.

## 완료 요약

- 브랜치 `docs/mysql-architecture-finish` (main 0c49c2e0 기준). 흐름 13편(함수 문서 129편)·구조 6편·지도·api-index 완성.
- 메인 오류 2건 기록: 지도 purge 행 "다음 한계로 예고"(고침), 검증 브리핑의 "timeout_event set L416 유일"(검증 워커가 L5961 로 바로잡음).
- 미완: push·병합(사용자 확인 대기), PG 지도 같은 문구 정정(NEXT N0-my).
