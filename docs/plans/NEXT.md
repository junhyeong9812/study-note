# NEXT — 다음 작업 전망 (프로젝트 롤링 단일 문서)

## 기준

- 마지막 갱신: 2026-10-05 dsa-remaining-writing 완료(자료구조 8·알고리즘 13 — 커리큘럼 §2·§3 미작성 0) · 직전: engineering-practice-writing(20편, push 0310d6cb) · 작업 폴더: `docs/plans/2026-10-05/dsa-remaining-writing/` · 브랜치: `docs/dsa-remaining-writing`

## 다음 작업 후보 (우선순위순)

### N0-c. 커리큘럼 미작성 leaf 집필 — 우선순위: 높음 · 네트워크 51·OS 38·DB 57·분산 36·신뢰성 53·설계 56·도메인 모델링 28·테스트 21(10-03)·API 설계 23·웹 플랫폼 24(10-04)·엔지니어링 실천 20·자료구조·알고리즘 잔여 21(10-05) 완료, 남은 영역: 보안·데이터 분석·언어·데이터 공학·수학·아키텍처

- **재사용 도구**: `docs/plans/2026-09-30/os-writing/`의 briefing(§3-1 교훈·§4 원고 이어받기·§5 로컬 재현)·factcheck·adjudicate 브리핑, network-writing의 check_new.py, 생성기(gen_area_readme.py — 새 leaf 폴더 우선 인식).
- **관측(두 영역 실측)**: 1차 Opus 점검 뒤에도 codex가 편당 7~12건(OS)·9~11건(네트워크)을 더 찾았고 판정 기각은 거의 0 → **2차 리뷰는 필수**. Opus 대체 리뷰는 편당 ~1.6건으로 codex보다 적게 찾는다 — codex 한도가 병목.
- **권장**: codex 한도를 먼저 확인하고, 한도가 부족하면 영역을 나눠 codex 몫을 배분(예: 하루 한 묶음). 워커 브리핑에 **작업 디렉토리 절대 경로·루트에 파일 금지**를 명시(OS에서 루트 유출 2회). 무거운 벤치 금지 문구를 수치로(스레드·CPU초 상한).
- **발생 가능한 문제**: man 페이지가 최신 커널보다 뒤처짐(두 영역 공통) — 기본값은 커널 문서·소스로. WebSearch 세션 한도(200) 소진 — curl·로컬 man으로 대체 가능.
- **착수 전 확인할 것**: 다음 영역, codex 한도, 원고 있는 leaf 처리 방식(OS는 새 leaf + 원고 링크).
- **DB 관측(10-01)**: codex 57편 전수가 가능했다(한도 1회, 리셋 대기). 2차 지적 314건 중 기각 3 — 1차 Opus 점검 뒤에도 편당 ~5.5건. 판정 때 원문을 열지 않고 판정한 근거가 묶음마다 1~3건 → 정합 패스에서 원문 대조로 회수. **명세 파일 생성은 게이트를 리셋한다** — 진행 중인 워커가 있으면 합의 직후 set-state, 또는 워커가 쉴 때 생성. **/tmp scratchpad는 재부팅에 사라진다** — 실험 코드·산출물 원본이 근거면 저장소 밖 영구 경로 검토.

- **분산 관측(10-01)**: 사용자 요청으로 **실험 근거 우선(I7)** 도입 — 편당 실험 1개+, 사실 점검이 재실행(V1b). 재실행으로 중대 2건(15 출력 +94/+100 재현 불가 → 실측 교체, 30 Kafka Streams 늦은 레코드 WARN 로그 존재)을 잡았다. 재부팅(/tmp 소실)으로 실험 원본이 사라짐 → 이후 영역은 실험 코드 핵심을 노트에 싣고 scratchpad에도 둔다. codex 22편 + 한도 뒤 Opus 대체 14편.

- **신뢰성 관측(10-02)**: codex 40편(편당 ~5건) + 한도 뒤 Opus 대체 13편(편당 ~1.6건) — 대체 리뷰가 덜 찾는 경향 재확인. **같은 세션의 두 실행이 병렬로 같은 영역을 진행**해 중복 워커·공용 헬퍼 덮어쓰기가 생겼고, 한쪽이 멈춘 뒤 인수 → 작업 폴더 log에 '소유 실행'을 적고 헬퍼는 실행별로 둔다. 외부 요청 UA에 사용자 이메일이 들어간 사고 1건 → 브리핑에 개인정보 금지 조항(유지).

- **웹 플랫폼 관측(10-04)**: 실험 근거를 **실제 브라우저**(호스트 headless Chrome 151 + scratchpad playwright-core, Node 20)로 — 브라우저 다운로드 없이 가능. 측정 해석 오류(화면 밖 버튼·HTTP/1.1 6연결·preload 우선순위·INP 폴백·TBT 구간)가 재실행·2차 리뷰에서 5건 잡힘 → **수치는 맞아도 해석이 틀리는 것**이 웹 실험의 주 실패모드. codex 24편 전수(한도 미도달) 편당 ~5.6건, 기각 1 — codex가 가용하면 영역 전체를 codex로. 워커 하나가 `pkill -f`로 다른 워커의 브라우저를 죽임 → 브리핑에 "자기 PID만 종료" 명시 유지.

### N0-o. 엔지니어링 실천 20편 사용자 검수 · 원본·영역 밖 후속 — 우선순위: 중간

- 검수: metadata `초안`. `[?]` 잔여: 02 29148 5.2.5 conforming(본문 유료) · 17 FSF 원 페이지 미열람(gnu.org 시간 초과).
- **원본 갱신(사용자 결정 필요 — 원본은 읽기 전용으로 둠)**: `cs/engineering/development-standards/legal-standards`·`provisions.md`가 2026-09-11 시행 개인정보 보호법 개정(법률 제21445호 — 제34조② 유출 가능성 통지, 시행령 72시간, 제64조의2② 10%) 전 상태 → 17 노트로 링크하거나 본문 갱신. 원본 operational-standards의 `../../straggler/` → `cs/systems/straggler`.
- 영역 밖 낡은 표기: engineering-practice를 "미작성"으로 가리키는 곳 — os/28:355, reliability/24:235·238, reliability/44:233, software-design/14:166·211, software-design/53:206·257(+3-answer 77), web-platform/20:292. os/31:245의 `36-profiling`·`20-performance-method-and-amdahl` 소속 오기.
- Knight 축약 "45분에 4.6억": reliability/04 2-summary 288·3-answer 55, ops-patterns/failure-modes 317 → SEC ¶1·¶17(45분 = 주문 송출, 4.6억 = 결국 실현된 손실; 보도자료 4.4억).
- 관측: codex 20/20 가용, 지적 80 중 기각 1 — codex가 있으면 전량 codex 유지. 이미지 빌드 실험은 legacy builder + `--pull=false`/`--pull never`로 새 pull 없이 가능(08 워커가 실수 pull 시도 1회 — 실패, 받은 것 없음).

### N0-p. 작성 규칙 ↔ 검사기 정비 — 우선순위: 중간 (근거 `docs/plans/2026-10-05/engineering-practice-writing/rules-vs-checker.md`)

- ① `cs/README.md` §3을 7절로 고치고 브리핑에만 있는 형식 규칙을 「작성 규칙」으로 올려 정본 단일화(문서) ② 위반 0인 기계 규칙(언어 태그·제목 형식·metadata 날짜·생성 문서 `--check`)을 check_new error로 ③ warning 후보 ④ 검사기를 작업 폴더에서 고정 위치로 옮기고 훅·CI 자동 실행 여부 결정. ②·④는 L1(spec부터).

### N0-r. 자료구조·알고리즘 잔여 21편 검수 · 영역 밖 후속 — 우선순위: 중간

- 검수: metadata `초안`. `[?]` 잔여: Sipser 정리·문제 번호(40·41), Sedgewick 1.3 성능 목표(ds 02), GNU sort 기본값(alg 11), Cassandra 전략 전환 재병합(ds 19), TCP 버퍼 원형 여부·512칸 휠 흔들림·큐 처리량 원인·안전한 메모리 회수(ds 25·26·29), Java String.hashCode 비랜덤화 이유(ds 44), SO의 .NET 엔진 여부(alg 43), Brotli 서버 모듈 기본 품질(alg 34).
- **영역 밖 낡은 "미작성" 표기 22곳**(이제 실재 — 링크로): network/16:210·17:169·20:175·21:171·25:162·38:251·39:146·305·43:130·301·44:290, reliability/05:177·07:163·40:208, database/22:207·41:158·277, domain-modeling/25:232, web-platform/14:47, engineering-practice/12:166·20:30·141·220·307·415, myway data-structure/01-dynamic-array:446·02-linked-list:833·04-queue-deque:996.
- 오류(원본·myway 읽기 전용 — 사용자 결정): `data-structure/03-stack` 529행 "수천 줄 반복"(HotSpot MaxJavaStackTraceDepth 기본 1024) · `foundations/data-structures-basics` §7(531~532행) 탈출 없는 Python 재귀 "스택 오버플로" → CPython은 RecursionError · 원본 foundations 2편의 코드 버그 9건(새 노트 "참고:" 줄에 목록).
- 관측: 폴더 번호 = 커리큘럼 번호 규칙으로 myway 폴더와 접두가 겹친다(02-linked-list / 02-adt-…) — 링크는 slug까지 써야 안전. codex 21/21 가용, 지적 94 기각 0. `java X.java` 소스 실행기는 스택 트레이스 끝을 실행기 프레임만큼 자른다(1019 vs 1024) — 실험 해석 주의.
- 메인 실수 1: 지시문을 따옴표 없는 heredoc으로 생성 → 백틱 확장(부작용 없음). 지시문은 Write 또는 `<<'EOF'`.

### N0-q. AI 엔지니어링 영역 후보 (AIEFS 분석) — 우선순위: 낮음~중간

- 근거 `docs/plans/2026-10-04/aie-analysis/report.md` §5b(26 leaf 안, 백엔드 우선 순서) · §6. 공부 우선순위상 reliability·api-design 검수 뒤에 열 것(링크 실재).
- **결정 대기**: ANN 벡터 인덱스 leaf — math/13 🔧이 가리키나 받을 leaf 없음. 로컬에 pgvector 이미지 없음 → 이미지 받기 허용 또는 Java 단일 파일 HNSW 실험(사용자가 "나중에 정하기"로 보류, 10-05).
- AIEFS는 "실습 참고" 링크로만(MIT), 근거는 1차 출처 직접 확인.

### N0-e. 커리큘럼 본문 오기 4건 — 우선순위: 낮음(1행)

- curriculum.md §7: 02행 "12로 이어짐" → 10(fragmentation-mtu-pmtud) · 44행 ⚠ "47의 사이드채널" → 43 · 08행 선행 `data-structure/13-radix-trie` → `20-radix-trie`. 고친 뒤 gen_area_readme.py 재실행.
- (10-01 분산) curriculum.md §10 33행 선행·데이터 구조 표 240행 `data-structure/41-rope` → 실제 노트 `28-rope`.
- (10-04 웹) curriculum.md §16 06행(1373) 🔧 "B-트리(IndexedDB 구현)" → Chromium 구현은 LevelDB(LSM)에서 SQLite 이행 중(06 노트 근거) — 표현을 "구현은 브라우저마다(Chromium LevelDB→SQLite)"로.
- (10-05 DSA) curriculum.md §3 284행 alg 03 ⚠ "중복 부분문제 → 지수 시간" → "중복 부분문제가 지수적으로 쌓이면 지수 시간"(T(n)=2T(n/2)+O(1)은 선형).
- (10-03 도메인) curriculum.md §13 28행 Horizon "1999~" → 판결 [1] "introduced … in 2000" · §13 선행 `algorithm/04-binary-search` → 실제 `06-binary-search`.

### N0-f. 네트워크 51편 사용자 검수 — 우선순위: 중간

- 배포 사이트에서 읽기 → 확정 시 3파일 상단 `✅ 검수 완료(YYYY-MM-DD)`. `[?]` 잔여(편당 0~5)는 검수 때 판단. 08 blackhole `ip route get` EINVAL·23 SYN-ACK 한도 소진 뒤 결과는 실행 미검증(userns 불가).

### N0-i. 분산 36편 사용자 검수 + 영역 밖 후속 — 우선순위: 중간

- 새 형식(metadata 단계 `초안`). `[?]` 잔여: 05 Fidge 1988·04 STEPT 실제 데몬·27 랙 배치·23 경험칙 2.
- 영역 밖 후속: `cs/database/57-db-incidents/2-summary.md` 212·348행 "distributed 36(미작성)" → `../../distributed/36-distributed-incidents/2-summary.md` · `cs/distributed/03` 285행의 reliability 07·08 링크는 reliability 작업 후 재점검.

### N0-j. 운영·신뢰성 53편 사용자 검수 + codex 재리뷰(선택) — 우선순위: 중간

- 새 형식(metadata 단계 `초안`). codex 한도(10-04 20:53) 뒤 Opus 대체 13편(14·19·20·31·34·38·40·42·48·49·50·52·53)을 codex로 재리뷰하면 대체 리뷰 누락률을 잴 수 있다.
- 원문 미열람 3건: 38 Georges 외 2007, 53 CrowdStrike CEO 7-25 게시물(TechTarget 인용), Knight SEC 34-70694(sec.gov curl 차단). 남은 미작성 링크 48(폴더 없는 영역) — 해당 영역 집필 때 링크.

### N0-n. 웹 플랫폼 24편 사용자 검수 · 영역 밖 낡은 링크 — 우선순위: 중간

- 새 형식(metadata 단계 `초안`). `[?]` 잔여 22(편당 0~3 — 23 저엔트로피 해석, 24 도메인 매각 당사자 성명·ICO 108,000 동일 집합·PCI 6.4.3 원문 등).
- 측정 수치는 Chrome 151.0.7922.173·로컬 헤드리스·지정 스로틀 조건 값 — 브라우저 메이저가 바뀌면 08·13·14·15·16·19의 실험을 재실행해 범위만 갱신(코드는 scratchpad/wp/NN — /tmp라 재부팅 시 소실, 핵심 코드는 노트에 실림).
- 영역 밖 "web-platform 미작성" 6줄 → 실경로로: network/49:387·415, network/33:352, network/34:333, database/47:312, testing/18:247.
- 노트 안 남은 "미작성" 20곳은 폴더 없는 영역(security 11·17·19·21·24·25, language 19, data-analysis 04·05, engineering-practice 06, algorithm 33·34) — 해당 영역 집필 때 링크.

### N0-m. API 설계 23편 사용자 검수 + codex 재리뷰(선택) · 영역 밖 낡은 링크 — 우선순위: 중간

- 2차 리뷰가 전부 Opus 대체 — codex 표본 재리뷰로 누락률 측정 가능. `[?]` 잔여: 29(8)·07(1)·05(2).
- 영역 밖 후속(관측): 다른 영역 노트 20줄이 이제 실재하는 api-design 01~21을 "미작성"으로 가리킴 — network/36·51, distributed/19, reliability/11·13·35, database/10·17·28·31·52, software-design/16·17·43, domain-modeling/18·basic/07, testing/13. 사례 22·23·26·27의 "노트 미작성" 4줄(사례는 이번에 읽기만). `grep -rn "api-design.*미작성" cs/`로 재추출.
- database/31:60 "FAIL_ON_UNKNOWN_PROPERTIES 기본 true"는 Jackson 2.x 한정 필요(3.0 기본 false).
- 사례 22~27은 옛 형식(질문 A./B. 절)이라 check_new 불통과 · 제목 줄이 옛 번호(01~06) — 통일 골격 이관 여부는 사용자 결정. 커리큘럼 29행 "Optus 무인증 API 열거 [?]"는 원문 근거 약함(노트는 "인가 없는 API로 대량 조회").

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
