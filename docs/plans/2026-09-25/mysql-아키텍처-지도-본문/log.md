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
