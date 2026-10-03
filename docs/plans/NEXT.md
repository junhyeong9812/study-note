# NEXT — 다음 작업 전망 (프로젝트 롤링 단일 문서)

## 기준

- 마지막 갱신: 2026-10-03 testing-writing 완료(테스트 21편, 실험 근거) · 직전: domain-modeling-writing(28편, push 4cc9c096) · 작업 폴더: `docs/plans/2026-10-03/testing-writing/` · 브랜치: `docs/testing-writing`

## 다음 작업 후보 (우선순위순)

### N0-c. 커리큘럼 미작성 leaf 집필 — 우선순위: 높음 · 네트워크 51·OS 38·DB 57·분산 36·신뢰성 53·설계 56·도메인 모델링 28·테스트 21 완료(10-03), 남은 영역: 보안·데이터 분석·웹 플랫폼·API 설계·언어·데이터 공학·엔지니어링 실천·수학·아키텍처·자료구조·알고리즘 잔여

- **재사용 도구**: `docs/plans/2026-09-30/os-writing/`의 briefing(§3-1 교훈·§4 원고 이어받기·§5 로컬 재현)·factcheck·adjudicate 브리핑, network-writing의 check_new.py, 생성기(gen_area_readme.py — 새 leaf 폴더 우선 인식).
- **관측(두 영역 실측)**: 1차 Opus 점검 뒤에도 codex가 편당 7~12건(OS)·9~11건(네트워크)을 더 찾았고 판정 기각은 거의 0 → **2차 리뷰는 필수**. Opus 대체 리뷰는 편당 ~1.6건으로 codex보다 적게 찾는다 — codex 한도가 병목.
- **권장**: codex 한도를 먼저 확인하고, 한도가 부족하면 영역을 나눠 codex 몫을 배분(예: 하루 한 묶음). 워커 브리핑에 **작업 디렉토리 절대 경로·루트에 파일 금지**를 명시(OS에서 루트 유출 2회). 무거운 벤치 금지 문구를 수치로(스레드·CPU초 상한).
- **발생 가능한 문제**: man 페이지가 최신 커널보다 뒤처짐(두 영역 공통) — 기본값은 커널 문서·소스로. WebSearch 세션 한도(200) 소진 — curl·로컬 man으로 대체 가능.
- **착수 전 확인할 것**: 다음 영역, codex 한도, 원고 있는 leaf 처리 방식(OS는 새 leaf + 원고 링크).
- **DB 관측(10-01)**: codex 57편 전수가 가능했다(한도 1회, 리셋 대기). 2차 지적 314건 중 기각 3 — 1차 Opus 점검 뒤에도 편당 ~5.5건. 판정 때 원문을 열지 않고 판정한 근거가 묶음마다 1~3건 → 정합 패스에서 원문 대조로 회수. **명세 파일 생성은 게이트를 리셋한다** — 진행 중인 워커가 있으면 합의 직후 set-state, 또는 워커가 쉴 때 생성. **/tmp scratchpad는 재부팅에 사라진다** — 실험 코드·산출물 원본이 근거면 저장소 밖 영구 경로 검토.

- **분산 관측(10-01)**: 사용자 요청으로 **실험 근거 우선(I7)** 도입 — 편당 실험 1개+, 사실 점검이 재실행(V1b). 재실행으로 중대 2건(15 출력 +94/+100 재현 불가 → 실측 교체, 30 Kafka Streams 늦은 레코드 WARN 로그 존재)을 잡았다. 재부팅(/tmp 소실)으로 실험 원본이 사라짐 → 이후 영역은 실험 코드 핵심을 노트에 싣고 scratchpad에도 둔다. codex 22편 + 한도 뒤 Opus 대체 14편.

- **신뢰성 관측(10-02)**: codex 40편(편당 ~5건) + 한도 뒤 Opus 대체 13편(편당 ~1.6건) — 대체 리뷰가 덜 찾는 경향 재확인. **같은 세션의 두 실행이 병렬로 같은 영역을 진행**해 중복 워커·공용 헬퍼 덮어쓰기가 생겼고, 한쪽이 멈춘 뒤 인수 → 작업 폴더 log에 '소유 실행'을 적고 헬퍼는 실행별로 둔다. 외부 요청 UA에 사용자 이메일이 들어간 사고 1건 → 브리핑에 개인정보 금지 조항(유지).

### N0-e. 커리큘럼 본문 오기 4건 — 우선순위: 낮음(1행)

- curriculum.md §7: 02행 "12로 이어짐" → 10(fragmentation-mtu-pmtud) · 44행 ⚠ "47의 사이드채널" → 43 · 08행 선행 `data-structure/13-radix-trie` → `20-radix-trie`. 고친 뒤 gen_area_readme.py 재실행.
- (10-01 분산) curriculum.md §10 33행 선행·데이터 구조 표 240행 `data-structure/41-rope` → 실제 노트 `28-rope`.
- (10-03 도메인) curriculum.md §13 28행 Horizon "1999~" → 판결 [1] "introduced … in 2000" · §13 선행 `algorithm/04-binary-search` → 실제 `06-binary-search`.

### N0-f. 네트워크 51편 사용자 검수 — 우선순위: 중간

- 배포 사이트에서 읽기 → 확정 시 3파일 상단 `✅ 검수 완료(YYYY-MM-DD)`. `[?]` 잔여(편당 0~5)는 검수 때 판단. 08 blackhole `ip route get` EINVAL·23 SYN-ACK 한도 소진 뒤 결과는 실행 미검증(userns 불가).

### N0-i. 분산 36편 사용자 검수 + 영역 밖 후속 — 우선순위: 중간

- 새 형식(metadata 단계 `초안`). `[?]` 잔여: 05 Fidge 1988·04 STEPT 실제 데몬·27 랙 배치·23 경험칙 2.
- 영역 밖 후속: `cs/database/57-db-incidents/2-summary.md` 212·348행 "distributed 36(미작성)" → `../../distributed/36-distributed-incidents/2-summary.md` · `cs/distributed/03` 285행의 reliability 07·08 링크는 reliability 작업 후 재점검.

### N0-j. 운영·신뢰성 53편 사용자 검수 + codex 재리뷰(선택) — 우선순위: 중간

- 새 형식(metadata 단계 `초안`). codex 한도(10-04 20:53) 뒤 Opus 대체 13편(14·19·20·31·34·38·40·42·48·49·50·52·53)을 codex로 재리뷰하면 대체 리뷰 누락률을 잴 수 있다.
- 원문 미열람 3건: 38 Georges 외 2007, 53 CrowdStrike CEO 7-25 게시물(TechTarget 인용), Knight SEC 34-70694(sec.gov curl 차단). 남은 미작성 링크 48(폴더 없는 영역) — 해당 영역 집필 때 링크.

### N0-l. 테스트 21편 사용자 검수 + codex 재리뷰(선택) · 영역 밖 낡은 링크 — 우선순위: 중간

- 2차 리뷰가 전부 Opus 대체(codex 한도 10-04 08:53) — 한도 해제 후 표본 codex 재리뷰로 누락률 측정 가능. 남은 `[?]` 9(Khorikov·GOOS·TDDbE·WELC 본문 미열람).
- 영역 밖 후속(관측): 다른 영역 노트의 "testing … 미작성" 표기 20곳이 이제 실재 노트를 가리킴 — software-design 12·13·25·26·50·51·52, os/15, reliability/53(227·367행), domain-modeling 13·advanced/27, data-analysis/README(목록: scratchpad/ts/cons/out-of-area-stale-testing-refs.txt — /tmp라 재부팅 시 소실, 필요하면 `grep -rn "testing.*미작성" cs/`로 재추출).
- 도구 관측: jqwik 1.10 User Guide에 Anti-AI Usage Clause — AI 에이전트 작업에서는 실행하지 않는다(fast-check 등으로). Pact는 기본 사용 통계 전송 — `pact_do_not_track=true`. 기존 이미지에 C 컴파일러 없음.

### N0-k. 소프트웨어 설계 56편 사용자 검수 + codex 재리뷰(선택) — 우선순위: 중간

- 2차 리뷰가 전부 Opus 대체(codex 한도) — 한도 해제 후 표본(예: 10편)을 codex로 재리뷰하면 누락률을 잴 수 있다.
- 영역 밖 후속: curriculum 56행 "GAO-14-694 [?]"는 원문 확인됨 → `[?]` 제거 후 gen_area_readme.py 재실행. 남은 미작성 링크 40(language·testing·domain-modeling·api-design 미작성 leaf) — 해당 영역 집필 때 링크.

### N0-i. 도메인 모델링 28편 — codex 표본 재리뷰(선택) · 노트 밖 정정 2건 — 우선순위: 낮음~중간

- 2차 리뷰를 codex 한도로 Opus 적대 리뷰로 대체했다(10-03). 한도 해제(10-04 08:53) 뒤 codex로 표본 5~8편 재리뷰하면 대체 리뷰의 누락률을 잴 수 있다.
- 노트 밖: `languages/java/syntax/51-java-time-types` 「tzdb 판이 갈렸다」의 "17·21 = 2024a"는 패치 번호(17.0.13·21.0.5) 한정 필요(21.0.12 = 2026b) · DDD Crew 저장소 README(CC BY 4.0)와 LICENCE(CC BY-SA 4.0)가 다름 — 다른 영역 노트에 같은 표기가 있으면 병기.
- **관측(10-03)**: Opus 적대 리뷰 편당 ~1.3건(앞 영역 codex ~5건)이지만 이번엔 사실 점검이 편당 ~1.3 중간을 이미 잡았다. 재실행·실측으로 판정한 지적 비율이 높았다(12·13·05·10 등) — 실험 근거 우선 규칙이 리뷰 판정 품질을 올림.

### N0-h. DB 57편 사용자 검수 — 우선순위: 중간

- 새 형식(metadata.md 단계 `초안`). 검수하면 단계 `검수`와 날짜.

### N0-g. OS 38편 사용자 검수 + codex 재리뷰(선택) — 우선순위: 중간

- 배포 사이트에서 읽기 → 확정 시 3파일 상단 `✅ 검수 완료(날짜)`. 남은 [?] 18.
- codex 한도 해제 후 10~38 중 표본을 codex로 재리뷰하면 대체 리뷰의 누락률을 잴 수 있다.

### N0-d. myway 150편 사용자 검수 — 우선순위: 중간

- 배포 사이트에서 읽기 → 확정 시 1-question·3-answer 상단 `✅ 검수 완료(YYYY-MM-DD)`, 원래 본문 정정 줄 84곳 확인.

### N1. seat-reservation-lab 첫 API — 우선순위: 중간 · 17개 랩 중 선행 cs가 가장 명확한 첫 주제

- **왜 다음인가**: 스캐폴드·기록 경로·append-only 규칙이 준비됨. 선행 cs = domain basic/02 · advanced/12 · ops 11 · ops 04.
- **발생 가능한 문제**: 관측 신호 — 기본 `java`가 1.8(JAVA_HOME 미지정 시 기동 실패) · 중단된 bootRun이 고아 프로세스로 포트를 점유(auction-lab 8105 실측).
- **권장 대처**: 착수 시 JAVA_HOME 21 고정, 기동 전 `ss -ltnp`로 포트 점유 확인.
- **착수 전 확인할 것**: 8/20 우선순위(기본기 → 도메인 → api/ops)와 포트폴리오 트랙 병행 비율 — 사용자 결정.

### NA. (issue 카드) 정확성 재점검 확대 — 우선순위: 중간

- **왜 다음인가**: codex 재점검은 표본 8장만 했다. 교정 전 48건 → 후 6건이었으니, 나머지 146장에도 예제 코드 엣지 결함이 남아 있을 수 있다(관측: 재점검 6건 모두 "고친 코드"의 오류 처리 누락).
- **권장 대처**: 복습하면서 걸리는 카드부터 `## 정정` append. 또는 폴더 단위로 codex 인라인 재점검(카드 8장당 1회).

### NB. (issue 카드) 검색엔진 카드군 도메인 추정 여지 — 우선순위: 낮음

- **왜 다음인가**: 이름·수치는 가공했지만 카드 조합으로 원 도메인 구조를 추정할 여지가 남았다(리뷰 잔여 리스크).
- **권장 대처**: 해당 폴더 README·카드의 도메인 특유 예시를 다른 도메인 예로 교체할지 판단.

### N2. mysql 아키텍처 지도 미완 링크 — 우선순위: 낮음

- **관측**: 09-25 WIP 병합으로 깨진 링크 32 — record-lock 03~11 단계·structure/(memory-structures·redo-log-files·tablespace-page·threads·undo-segments·record-format)·mvcc-read·purge 미작성, `flows/structure/…` 경로 오기 일부.
- **권장 대처**: 지도 작성 재개 시 미작성 문서부터, 경로 오기는 `../../structure/`로 교정.

## 보류·이월


- 통합 랩 08·09 — 01~07 API 서버 완성 후 동시 기동 구조로 전환(사용자 결정). 재개 조건: 01~07 완료.

- 아카이브 보류(보안 — 패치·배포 미확인) 약 20건 — 재개 조건: 원 프로젝트에서 수정 배포가 확인되면 다음 사이클 마감 때 카드화(목록은 비공개 로컬 원장).

## 완료 이력

- 완료 → `docs/plans/2026-09-26/backend-labs-scaffold/`
- 완료 → `docs/plans/2026-09-24/cs-issue-archive/`
