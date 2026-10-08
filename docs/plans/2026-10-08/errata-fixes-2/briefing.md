# 수정 워커 브리핑 — errata-fixes-2

저장소: `/home/jun/project/study-note` · 브랜치 `docs/errata-fixes-2`(이미 체크아웃됨 — 브랜치 전환·커밋·push 금지, 메인이 커밋한다).
명세: `docs/plans/2026-10-08/errata-fixes-2/requirement-spec.md` — 먼저 읽을 것. 원천 목록: `docs/plans/NEXT.md` N0-u~N0-z와 보안 항목(79행 근처).

## 목표
학습 노트·원고·커리큘럼에 남은 사실 오류를 **최소 문구**로 고친다. 각 오류는 이전 영역 작업에서 근거가 확인된 것이다 — 근거를 **다시 열어 대조한 뒤** 고친다.

## 규칙
1. 대상 줄과 그 앞뒤 절을 끝까지 읽고 고친다. 줄 번호는 이전 시점 기준이라 어긋날 수 있다 — 문구로 찾는다.
2. 근거는 직접 연다: 근거 leaf(실험 표·출처 줄), 1차 출처 URL(curl). 기억으로 판정 금지. 못 열면 고치지 않고 보고에 "미확인"으로.
3. 고치는 줄만 바꾼다. 헤딩·질문 수·구조·문체(옛 형식 노트·원고 포함) 유지. 필요하면 근거 leaf로 가는 상대 링크 한 줄("참고:")을 붙여도 된다 — 링크는 실재 확인.
4. 근거 leaf가 같은 사실을 이미 정확히 쓰고 있으면 그 표현과 수치를 맞춘다(새 수치를 만들지 않는다).
5. 새 형식 leaf(`1-question.md`·`2-summary.md`·`3-answer.md`·`metadata.md` 4파일)를 고쳤으면 `python3 docs/plans/2026-09-30/network-writing/check_new.py <leaf 폴더>` PASS 확인.
6. 고친 파일의 상대 링크가 모두 실재하는지 확인.
7. 금지: 생성 문서(영역 README·index) 수기 수정, check_new·생성기 수정, 저장소 루트 파일, git 쓰기 명령, 개인정보, 공격 코드. 실험이 필요하면 호스트 python3(표준 라이브러리) 또는 `docker run --rm --pull never --network none --cpus=2 -u $(id -u):$(id -g) -e HOME=/tmp --name sn-err2-<id> <있는 이미지>`만. 임시 파일은 `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/err2/<task>/`.
8. 다른 워커가 같은 시간에 다른 파일을 고친다 — 맡은 파일만 건드린다.

## 근거 찾는 곳
- 영역 작업 폴더: `docs/plans/2026-10-0{5,6,7,8}/*-writing/`(log.md·web-cross-sample.md), 판정 결과는 scratchpad `/tmp/claude-1000/-home-jun-project-study-note/16696510-853f-4d10-82ba-64d9eb37bcc8/scratchpad/{math,arch,de,net46,lang,da}/`.
- 근거 leaf: `cs/data-analysis/08`(신뢰구간·겹침 실험 E)·`14`(해시 할당 salt 실험), `cs/language/02`(정규식 백트래킹 JDK 21 실험)·`19`(의존성 해석·MVS), `cs/math/*`(Little 법칙·압축·epsilon 관련), `cs/data-engineering/05`(복제 슬롯)·`09`(스키마 호환성), `cs/network/46`(LB 알고리즘), `cs/architecture/*`(NAND·메모리 순서).

## 보고 형식 (최종 메시지)
표: `파일:줄 | 바꾸기 전(짧게) | 바꾼 뒤(짧게) | 근거(열어 본 파일:줄 또는 URL) | 상태(수정/미확인/불필요)` + 실행한 검증 명령과 결과 + 고친 파일 목록.
