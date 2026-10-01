# log — header-cleanup

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-01 | 인터뷰 9건(범위 저장소 전체 · H1 아래 인용문 머리말 전부 · 상태는 폴더별 metadata.md(단계+날짜, 학습 노트 폴더 전부) · 생성 문서 머리말 유지 · 별도 브랜치로 DB와 병행) → 명세 합의, auto | **사고**: 명세 파일 생성이 세션 게이트를 리셋해 진행 중 DB 워커 5개의 쓰기가 막힘(스테이징으로 복구 — db-writing log 참조) |
| 2026-10-01 | worktree `scratchpad/hc`(브랜치 docs/header-cleanup, main d43fa61a). 기준값: 생성기 상태 합계 TOTAL 미작성 383·원고 64·초안 197·검수 0 (재생성 diff 0) | hc_base_status.txt |
| 2026-10-01 | `scratchpad/hc_strip.py` dry-run: 변경 3,850파일·머리말 27,281줄, 제외(no-header 1,255 · 생성 문서 19 · 첫 줄 H1 아님 97 — 그중 H1 아래 머리말 놓친 파일 0 확인), metadata 1,223(초안 413·원고 810) | 제목 위 인용문 1파일(reference/writing/evidence-10-git-conventions.md) 수동 제거 |
| 2026-10-01 | 적용: 3,851파일 수정 · **추가 0줄 / 삭제 31,149줄**(numstat) · metadata.md 1,223 생성 | I1 충족(삭제만) |
| 2026-10-01 | 생성기 `status()`를 metadata.md 단계로(없으면 예전 표식 규칙) → 재생성 상태 합계 **기준값과 완전 동일**(I2) · check_new.py: 초안 표기 검사 → metadata.md 단계·제목 아래 머리말 금지 → network·os 89 PASS · cs/README 작성 규칙 §2·§4 갱신 | heredoc 이스케이프로 생성기 1회 깨짐 → git checkout으로 복원 후 Edit로 재적용 |
| 2026-10-01 | 표본 diff(폴더별 2개) 육안 확인 · linkcheck main 213 → 210(머리말 안 링크 3개 소멸, 신규 0) | 듀얼 리뷰 발사: Opus(표본·metadata·엣지) ∥ codex(스크립트·도구 diff) |
| 2026-10-01 | codex 리뷰(high, 7건) 회수 → 실데이터 대조: ①빈 줄로 나뉜 인용 묶음 18파일 전부 머리말(원본 설명·복습 안내·측정 조건)로 확인 — 사용자 지시 범위, 유지 ②CRLF 0파일 ③검수 단계 폴더 0 — 합계 동일 확인됨 ④기존 metadata 0 ⑤머리말만 있는 파일 0(빈 줄 축약은 공백만) → 도구 보강 3: 생성기는 metadata 단계 칸 오류 시 SystemExit(조용한 폴백 금지), check_new는 단계 행 정확히 1개·같은 파서, front matter 건너뛴 첫 H1 기준 | 89 PASS · 상태 합계 동일 재확인 · Opus 리뷰는 재개 대기 |
| 2026-10-01 | Opus 리뷰 회수(H2·M5·L5 — 원문 scratchpad/hc_opus_review.md): H1 Claude 작성 언어 노트 618+1이 원고로 · H2 인용문 아닌 표식 줄 218 · M1 본문이 기대는 머리말(흔들리는 칸 표·기준 소스·실행 환경·펜스 규칙·csc()·측정 조건) · M2 portfolio 탐색 51·선행 링크 · M3 출처(opensource 기준 커밋·history 원본·reference 고지·workflow 정본) · M4 초안 날짜 13 · M5 check_new 회귀 · L1~L5 | 사용자 판단 3건 질문 |
| 2026-10-01 | 사용자 결정: H1 → 초안(날짜=머리말, 없으면 첫 커밋일) · M1 → 본문 끝 「## 실행 환경」 절로 옮김(복습 안내·표식·요약은 삭제 유지) · M2·M3 → 탐색 줄은 본문 끝, 출처는 「## 출처」 절로 복원 | 복원 작업자 발사(Opus, 브리핑 scratchpad/hc_restore_brief.md — H1·H2·M1~M4) |
| 2026-10-01 | 메인 직접: M5 check_new — H1 미발견 시 다른 검사 건너뛰던 회귀 제거(첫 비어 있지 않은 줄이 H1이어야 함, 제목 아래 인용문·표식 줄 금지) · L5 생성기 metadata 없는 노트 폴더 stderr 경고 · L3 템플릿 머리말의 파일별 작성 방식 → templates/README.md 절로, README·cs/README 참조 갱신 · L1 판정 규칙은 코드(1·3파일) 기준, 검수 폴더 0이라 영향 없음 · L4 DB 노트는 병합 후 hc_strip으로 변환 예정 · L2 practice/programmers 빈 폴더 47은 원고 유지(보고) | |
| 2026-10-01 | 복원 작업자 회수(Opus, scratchpad/hc_restore.py, 적용 전 백업 hc_before_restore.tgz): H1 원고→초안 619(날짜 git 이름변경 추적 618·머리말 1) → 단계 초안 1032·원고 191 · M4 날짜 13 · H2 표식 218파일 223줄 · 「## 실행 환경」 2,162파일(KEEP 줄 약 15.8k) · 참조 고쳐 쓰기 262(위 기준 소스 53·머리말 208·기타) · 탐색 88파일 · 「## 출처」 277파일 · 단언 4종 통과 | 메인 확인: 89 PASS · 생성기 TOTAL 미작성 383·원고 63·초안 198(deadline-propagation 1건 이동, 의도) · 깨진 링크 210→212(gate1-auth-pattern 원래 깨진 링크 2개 복원 — main 213에 있던 것) · 도구 수정(check_new·생성기·templates) 유지 확인 |
| 2026-10-01 | 애매 판정 12건 수용(cs 이관 노트 원고 출처는 「## 출처」로 — cs/README §5는 "새로 쓰는 노트" 한정이라 충돌 없음) | post-fix 재점검 발사(Opus, 읽기 전용) |
| 2026-10-01 | post-fix 재점검 회수(Opus, 표본 약 47 + 스크립트 전수 3,250): **fix first** — HIGH ts 48폴더 원고 잔존(H1 아래가 아닌 두 번째 인용문의 Claude 작성 표식이 본문에 남음)·csharp 36/c 4/go 1 판단 필요 · HIGH 「머리말」→「실행 환경」 오지시 ≥39(머리말이 본문 맨 위 판·흔들리는 칸 표를 뜻한 경우) · MED ts 1-question 선행 줄 21 누락·opensource 기준 2건 누락·복습 안내 오복원(python·csharp·go 1-question)·「## 출처」 중복 9 · 구조 검사 전부 정상·89 PASS | 복원 작업자 재개해 수정 지시(csharp·c·go는 원고 입력 없음 + 같은 커밋 형제에 Claude 작성 표식이면 초안, 근거 보고) |
| 2026-10-01 | 2차 수정 회수(hc_fix2.py, 백업 hc_before_fix2.tgz): ts 48 표식 삭제·초안(날짜 git 추적) · 「실행 환경」 지시 319건 개별 판정 → 교정 129·삭제 48·유지 141(머리말 원뜻 2건 복원) · 섹션 방향어 313 교정 · ts 선행 줄 29 복원 · opensource 기준 2 복원 · 복습 안내 15줄 삭제 · 「## 출처」 중복 9→0 · 89 PASS · 생성기 TOTAL 동일 · 단언 통과 | 잔여: csharp 36·c 4·go 1은 규칙(같은 커밋 형제 표식) 불충족 → 사용자 질문 |
| 2026-10-01 | 사용자 결정: 41편 Claude 작성 → 초안(날짜=첫 커밋일, hc_1b.json) 메인이 적용 · 남은 원고 = cs 이관 원고 19·practice/programmers 47·project/db-engine 36(실제 원고) · rust 29·35·47·55 펜스 규약 섞인 줄 복원·kotlin04 방향어는 작업자에 추가 지시 | |
| 2026-10-01 | 3차 소수정(rust 펜스 규약 4줄·kotlin04 방향어) · 41편 초안 적용 · 최종: 89 PASS · 생성기 TOTAL 동일 · 워크트리 커밋 d6f95526(5,080파일) | main 병합·push는 사용자 확인 대기 |

## 리뷰 ledger

## 생략한 검증

## 완료 요약
