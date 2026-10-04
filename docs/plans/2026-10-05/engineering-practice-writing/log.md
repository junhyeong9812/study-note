# log — engineering-practice-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-04 13:30 | AIEFS 분석(rohitg00/ai-engineering-from-scratch, scratchpad 클론·Opus 워커): 보고서 docs/plans/2026-10-04/aie-analysis/report.md — 워커 Write 거부로 메인이 저장 · 권장: AI 영역 NEXT 등록·ANN leaf 후보(pgvector 없음)·흔한 오해 줄·규칙↔검사기 대조 | 사용자: §17 진행, pgvector 나중 |
| 2026-10-04 15:30~19:03 | 웹 플랫폼(다른 실행) 완료 대기 — 대기 루프 2h 한도로 종료 · 확인: d01a1d83·8a9d8693 로컬 커밋, push 대기 5시간 | 사용자: 여기서 병합+push |
| 2026-10-05 01:55 | 웹 플랫폼 미커밋 log 1줄 커밋(3b190e5e) → main ff + push(c79e2d8b..3b190e5e) | 완료 |
| 2026-10-05 02:00 | 인터뷰(보강 방식 20편 · 흔한 오해 줄 + 대조표 · 검증 앞과 같게 · 합의 auto) → 명세 작성 직후 승인 기록 · 브랜치 docs/engineering-practice-writing(main 3b190e5e) · codex 사용 가능(리셋 지남) | SPEC=1·MODE=auto |
| 2026-10-05 02:10 | 브리핑(api-design판 이식 + §17 실험 예시·이미지 빌드 규칙(기존 베이스만·자기 이미지만 rmi)·git 실험은 scratchpad 일회용 저장소·흔한 오해 줄) · 집필 발사(Opus 5병렬, 18편): 01·02·12·18 / 03·04·05 / 06·07·08 / 09·10·11·13 / 14·15·16·17 — 종합 19·20 후속 · 규칙↔검사기 대조표 워커 발사(읽기 전용) | 회수 대기 |
| 2026-10-05 | 규칙↔검사기 대조표 회수(읽기 전용, 새 leaf 387편 측정): README §3이 6절인데 검사기·노트는 7절(정본 드리프트)·형식 규칙 다수가 브리핑에만·검사기 범위 안 387 PASS·실제 위반 소수(장애 6개 8편·실험 절 위치 3편·태그 없는 펜스 3)·금지어 1,245회지만 표본상 조건 없는 단정은 소수·생성 문서 19개 드리프트 0·옛 컬렉션 깨진 링크 3 · 저장 rules-vs-checker.md(워커 Write 불가 → 메인 저장) · 수정은 하지 않음(NEXT 후보) | 보고 |
| 2026-10-05 | 집필 회수 1/5: 03·04·05(3 PASS, 각 9문항, [?] 3) — 실험(git 2.43 일회용 저장소): 03 객체 5개·블롭 공유·hash-object = sha1sum 재계산·Java 재계산·force push 유실(bare 원격 reflog 없음)·reflog 복구·lease/force-if-includes·충돌 --ours 오해결 조용한 소실 → remerge-diff로 탐지·checkout --ours vs -X ours, 04 통합 주기 시뮬레이션(명시) 1일 94~151 vs 20일 802~864 충돌 줄·의미 충돌(ort 충돌 0인데 javac 실패), 05 섞인 PR vs 나눈 PR(동작 변경 2줄)·range-diff creation factor 60 vs 100 · Cisco/SmartBear는 벤더 연구로 명시 · 사실 점검 브리핑 작성·1/5 발사 | 3 PASS |
| 2026-10-05 | 집필 회수 2/5: 01·02·12·18(4 PASS, [?] ~5 — McConnell 본문·SWEBOK 절 이름·Programming Perl 초판) — 실험: 01 회고 시뮬레이션(명시: 의식만 RITUAL ≈ 없음, 원인 겨냥 REAL은 반복 문제 20→4·원인이 매번 새로우면 손해), 02 추적 매트릭스 v1 커버 1/3 → v2 4/5·비기능 테스트 0·고아 테스트, 12 3점 추정 몬테카를로(가능성 최대 합 30일 지킬 확률 ~1%·공통 원인 P90 44→53), 18 perlglossary 두 판 원문 대조·자동화 손익분기(예시) · 원본 정정: Scrum 2017 표현·Conway 1968·'동시에' · 사실 점검 2/5 발사 | 4 PASS |
| 2026-10-05 | 집필 회수 3/5: 09·10·11·13(4 PASS, 각 8~9문항, [?] ~4) — 실험: 09 DORA 5지표 계산(시뮬레이션: honest 2.6회/주·실패율 22.2% vs 게이밍 재배포 17회로 7.6회/주·7.7%·재작업 0%)·rebase가 커미터 날짜 변경, 10 부채 이자 변경 줄(F2 이후 상환이 역전)·누락된 규칙 사본, 11 문서 신선도 검사 7건·런북 명령 실행 실패·검토일만 올리는 게이밍, 13 TCO·가중합(예시)·OpenSSF Scorecard 공개 API 재계산 일치 · DORA 2023 MTTR→실패 배포 복구·2024 재작업률·현 모델 복구 시간은 처리량 · SWE@G 10장 원문 확인(커리큘럼 [?] 해소) · 사실 점검 3/5 발사 | 4 PASS |
| 2026-10-05 | 집필 회수 4/5: 14~17(4 PASS, [?] ~6) — 실험: 14 PMD 7.7.0 기준선 줄 번호 키 새 위반 5 vs 지문 키 2, 15 SpotBugs+FindSecBugs 보안 3/9·OSV 질의 날짜별 결과·ASVS 5.0.0 345개(원본 '약 350' 정정), 16 로그 표준 준수율·trace_id 검색 누락·지표 이름 lint 4/7, 17 license-maven-plugin 전이 의존성 포함 8개 ALLOW/REVIEW/DENY·law.go.kr DRF 조문 diff · **원본 legal-standards·provisions.md(2026-08-24 수집)는 개인정보 보호법 2026-09-11 시행 개정 전 조문**(제34조② 유출 가능성 통지 신설·③→④·제30조의3·제64조② 등) → 새 leaf에 참고 줄, 원본 갱신은 NEXT · 원본 operational §6 깨진 링크 · 사실 점검 4/5 발사 | 4 PASS |
| 2026-10-05 | 사실 점검 회수 1/5: 03·04·05 — 중대 0, 중간 4(04 git-flow 범위 원문은 'explicitly versioned, or … multiple versions'(OR)·Branch by Abstraction 단계는 TBD 사이트 원문대로·충돌 덩어리 '많거나 같음' + 해석 표시, 05 Sadowski 기대 주제는 인터뷰 12건·수치는 로그 900만 변경), 경미 7(ref 파일 41바이트, 리뷰어 2명↑ 25% 미만, SWE@G '하루 안 첫 피드백', Bacchelli 'key aspect') · 재실행 9종 결정적 출력 동일 · codex 2차 리뷰 러너 준비(scratchpad/ep/codex/run1.sh) → 03·04·05 발사 | 3 PASS |
| 2026-10-05 | 사실 점검 회수 2/5: 01·02·12·18 — 중대 0, 중간 5(01 Royce 원문 PDF(archive)로 직접 확인·'waterfall' 단어 없음·Bell–Thayer 기원은 2차 출처, 02 arXiv 2403.17479 표 3은 29148:2011 기반 요구 냄새 목록(5.2.7 범주 아님) → [?], 12 McConnell 1.3 대화 요약 오류·공통요인 P90 증가는 평균 이동 + 퍼짐 증가로 분리, 18 예시 계산을 실제 사례처럼 쓴 것), 경미 ~6 · 원본 정정 줄(Scrum 2017 표현·Conway 1968·'동시에') 원본·원문 모두와 일치 · 재실행 4종 일치 · [?] +1 | 4 PASS |
| 2026-10-05 | 사실 점검 회수 3/5: 09·10·11·13 — 중대 0, 중간 1(09 merge --squash는 작성자 날짜까지 커밋 시각 — 재실험), 경미 ~4(11 SWE@G 'setting up' Borg 문서, 13 Scorecard Code-Review 판정 근거·OpenTofu 보도자료 문구·HashiCorp FAQ 'not retroactive' 출처) · 재실행 8종 결정적 출력 동일(sha256 일치) · Scorecard 스캔 날짜 명시 확인 · codex 2차 리뷰 01·02·12·18 발사(백그라운드) | 4 PASS |
| 2026-10-05 | 집필 회수 5/5: 06·07·08(3 PASS, [?] ~5) — 실험: 06 의미 충돌 병합(충돌 0·main RED)·파이프라인 DAG 순차 29분 vs 병렬 22분(예시)·수동 배포 누락 검증(시뮬레이션), 07 직접 위상정렬 = Maven reactor·make mtime 헛빌드/놓침·캐시 키 누락 오염·outputTimestamp 재현 jar 해시 일치·TZ/로캘 환경 의존·증분 빌드 한계, 08 이미지 474/286/160MB·레이어 순서 재빌드 11.7s vs 2.5s·.dockerignore 150MB→11.8kB·scratch 셸 없음·musl에 glibc 바이너리 실패·RUN rm 크기 불변 · Docker 레거시 빌더(buildx 없음) · 사고: SIGPIPE로 빌드 중단 뒤 docker run이 없는 이미지 pull 시도 → 'pull access denied' 실패(받은 것 없음) → --pull never · 자기 빌드 이미지 태그 7 + dangling 10(생성 시각·history로 자기 것 확인) rmi, prune 없음 · **집필 18편 완료** · 사실 점검 5/5 + 종합 19·20 발사 | 3 PASS |
| 2026-10-05 | codex(high) 2차 리뷰 회수 10편(한도 없음): 01 6·02 5·03 ~2·04 3·05 4·09 4·10 2·11 2·12 3·18 2건 · 13 진행 중 · 판정 브리핑(adjudicate-briefing.md)·프롬프트(scratchpad/ep/review/) 작성 · 판정 발사: 03·04·05 / 01·02·12·18 | 판정 대기 |
| 2026-10-05 | 판정 회수 03·04·05(codex 지적 16): 채택 15·부분 1·기각 0 — 03 저장소 구성(index·HEAD·config)·SHA-1 충돌 전제·merge-base 여럿(부분)·충돌 종류(modify/delete·rename 등)·git add 무인자 재실험·강제 push 기준은 fast-forward·force-if-includes '도달 가능'·-X ours 바이너리·log -m -S 재실험, 04 플래그 전환은 설정 방식에 달림(Hodgson)·git cherry 인자 방향 재실험·for-each-ref 주석, 05 Myers는 greedy(minimal 별도)·range-diff 비용·CODEOWNERS @org/team·presubmit 'can reject' | 3 PASS |
| 2026-10-05 | 판정 회수 01·02·12·18(codex 지적 16): 채택 15·부분 1·기각 0 — 01 나선형 모델 1986 SEN(1988은 IEEE Computer판)·위험 해소 수단 다양·백로그 'ordered list'·스프린트 중 변경은 목표 위태 여부·코드 주석·원인 단정 완화, 02 v1 '빨라야' 분류 오류 해설(부분)·추적 화살표·'테스트 연결 없는 요구'·비기능 확인 수단·고아 테스트 원인, 12 10.1절 제목·임계 경로 조건·재실행(44.1일 초과 독립 9.7~9.9% vs 공통 44.4~44.5%), 18 package는 test 포함(-DskipTests)·문서는 질문을 '줄인다' | 4 PASS |
| 2026-10-05 | 사실 점검 회수 4/5: 14~17 — 중대 0, 중간 3(15 SpotBugs 범주 SECURITY 3·BAD_PRACTICE 3·EXPERIMENTAL 2·MALICIOUS_CODE 1, 16 원본 straggler 링크 실제 대상 cs/systems/straggler·PRR은 SRE 인수 전제(출시 조건은 해석)), 경미 ~5(eng-practices 'absolute authority' 절 위치·Sonar 20줄 조건·ASVS 345 근거·해석 라벨 통일·FSF 교차 근거) · **법령 law.go.kr DRF 재확인 전부 일치**(법률 제21445호 2026-09-11 시행·제34조②④⑤·제30조의3·제64조의2②·시행령 제39조의2·3 72시간 등) · 재실행 8종 일치 · gnu.org 접속 불가 · codex 2차 리뷰 14~17 발사 | 4 PASS |
| 2026-10-05 | 판정 회수 09·10·11·13(codex 지적 11): 채택 5·부분 5·기각 1 — 09 gamed 재배포 17은 '첫 배포 뒤 기능 커밋마다'·A..B 빈 조건은 조상 관계(재실험)·재작업 판정 규칙 조건(부분)·블로그 날짜 09-23(KST 09-24)(부분), 10 log --name-only는 병합 커밋 파일 누락(재실험, 부분)·show --numstat 지적은 실측과 달라 기각, 11 CI 예시 두 잡으로 분리(allow_failure)·YAML 단순 검사 한계(부분), 13 HashiCorp BSL Additional Use Grant 원문대로(해석 표시)·Scorecard Contributors 소스 동작(GitHub ListContributors·5회 미만 제외)(부분)·Heroku 이전은 예시 | 4 PASS |
| 2026-10-05 | codex 2차 리뷰 회수 14~17: 14 3·15 4·16 6·17 6건 → 판정 발사 | 판정 대기 |
| 2026-10-05 | 판정 회수 14~17(codex 지적 19): 채택 13·부분 6·기각 0 — 14 pmd:check는 기존 위반도 막음(plugin.xml)·기준선 수동 축소·지문에 파일 경로, 15 ASVS L2 253은 출발 집합(부분)·SBOM 없이도 질의 가능(부분)·OSV last_affected/limit·next_page_token, 16 trace_id 전부 0 거부(W3C 3.2.2.3, 재실행)·무효 traceparent 무시·grep 출력 a_json 행 누락(재실행으로 교체)·카디널리티는 곱이 상한·히스토그램 단위(부분)·난수 SHOULD(부분), 17 5일 파기는 지침(법은 지체 없이, 부분)·배치 주기로 최대 24시간 지연→4일·72시간 통지 단서·제34조① 7호 누락·Apache §4 (b)·LGPL §6 재연결(부분) | 4 PASS |
| 2026-10-05 | 사실 점검 회수 5/5: 06·07·08 — 중대 0, 중간 ~5(06 surefire.skip 속성 없음(maven.test.skip·skipTests는 failsafe도)·SWE@G 23장 원문 범위, 07 SWEBOK 장 번호(8장 §6·6장 §3.2) PDF 목차 확인, 08 imagePullPolicy 기본값(태그 생략도 Always)·BuildKit CACHED는 관찰 아님), 경미 ~12 · [?] 6→1(Gradle·SOURCE_DATE_EPOCH 관례·de_DE 로캘 미설치·OCI·Knight) · 재실행 16종(결정적 일치, 시간만 범위) · 빌드 --pull=false·run --pull never, 자기 이미지 태그 8 + dangling 7(생성 시각·history로 확인) rmi·dangling 수 시작 전 26 그대로 · **사실 점검 18편 완료** · codex 2차 리뷰 06·07·08 발사 | 3 PASS |
| 2026-10-05 | codex 2차 리뷰 회수 06·07·08: 06 3·07 4·08 3건 → 판정 발사 · **일반 노트 18편 codex 2차 리뷰 완료** | 판정 대기 |
| 2026-10-05 | 집필 회수 종합 19·20(2 PASS, 각 10문항, [?] 0) — 19: leaf 시나리오 87개 전부 링크(verify19.py 링크 149·누락 0)·판정 수정 재추출 반영(03-2 -m -S·04-3 cherry·02-2), 20: Knight(SEC 34-70694를 Internet Archive 사본으로 — sec.gov 403·개인정보 미사용, 보도자료 $440M vs SEC $460M 병기) + Cloudflare 2019-07-02(상세 글 타임라인·27분·80%) · 실험: 재사용 플래그+1대 누락 시뮬레이션(636 → 26,558 → 되돌림 212,000)·백트래킹 정규식 n=2000 19.5s vs RE2J 수 ms·CI 정규식 시간 예산 검사 · 사실 점검 19·20 발사 | 2 PASS |
| 2026-10-05 | 판정 회수 06·07·08(codex 지적 10): 채택 5·부분 5·기각 0 — 06 YAML 빈틈(integration이 재빌드 — Only Build Your Binaries Once·Failsafe는 플러그인 설정 필요·deploy 작업 checkout 누락), 07 COPY 캐시는 메타데이터 체크섬(부분)·역의존 재빌드는 '후보'(Gradle ABI 회피, 부분)·useIncrementalCompilation true/false 재실험(2 vs 1 파일)·출처 증명(SLSA)(부분), 08 scratch는 최소 시작점(jlink 실험과 모순 해소)·gcompat(부분)·474MB 내역 docker history 실측(부분) · 이미지 빌드 없음·dangling 26 그대로 · **일반 18편 판정 완료** · 웹 교차 표본 발사 | 3 PASS |
| 2026-10-05 | 사실 점검 회수 19·20: 중대 0, 중간 3(20 RuleBudget 지연 원인은 CPU 제한(--cpus=1 94~101ms vs 2 58~61ms, 해석)·정규식 시간 범위 19~49초·45~91ms/28~49초), 경미 ~6(27분 시각은 계산 표시·SEC ¶41 인용, 19 02 출력 공백까지 원문대로·bisect 128+ 중단·SEC는 회사 대상 명령) · 19 링크 149(고유 87) 누락·오류 0·인용 ~150 대조 · SEC는 IA 사본만 · 참고: reliability/04 '45분 동안 4.6억'은 실현 손실(담당 밖 → NEXT) · codex 19·20 발사 | 2 PASS |
| 2026-10-05 | codex 2차 리뷰 회수 19·20: 각 4건 · **20편 codex 2차 리뷰 완료** → 판정 19·20 + 정합 패스 한 워커로 발사(scratchpad/ep/consistency-prompt.md) | 회수 대기 |
| 2026-10-05 | 웹 교차 표본 회수(01~18): 63건 — 일치 62·불일치 0·확인 불가 1(02:61 conforming이 인용한 2차 출처에 없음) · 관찰 3(06:352 seqNum=4·04:299 개정일·17:65 FSF는 apache.org로 대조) | web-cross-sample.md 저장 · 02·06은 정합 패스 회수 뒤 메인 반영 |
| 2026-10-05 | 판정 19·20 + 정합 패스 회수: codex 8건 채택 7·부분 1·기각 0(19-2 VersionDrift 전원 실패 시 exit 0 → 재현 후 수정, 20 SEC PDF 18쪽·Cloudflare 승인 "또는"·경과 시간) · 정합: Knight 06 표현 SEC ¶1·¶17로 교정, git cherry 04·19 동기화, 나머지 축 일치 · "미작성"→링크 18 · 19 재대조(링크 149·누락 0) · 상대 링크 631 깨짐 0 · 영역 밖 목록 4종(보고만) | 20 PASS |
| 2026-10-05 | 메인 반영: 02:61 conforming `[?]` 명시 · 06:352 InformIT seqNum=3·4 · check_new 20 PASS · 정리 확인(sn-ep 컨테이너 0·이미지 0·dangling 26·루트 새 파일 0) · 영역 표 재생성(초안 20, engineering-practice README만 변경) | 노트 커밋 e30d3726 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 03·04·05 | Opus 독립 | 0 | 4 | 7 | 3→3 | 웹 표본 9 · 실험 재실행 9 |
| 01·02·12·18 | Opus 독립 | 0 | 5 | ~6 | 5→6 | 웹 표본 12 · 실험 재실행 4 |
| 09·10·11·13 | Opus 독립 | 0 | 1 | ~4 | ~4→~4 | 웹 표본 12 · 실험 재실행 8 |
| 03·04·05 판정 | Opus(codex 지적 16) | 채택 15 | 부분 1 | 기각 0 | | 재실험 3 |
| 01·02·12·18 판정 | Opus(codex 지적 16) | 채택 15 | 부분 1 | 기각 0 | | 재실험 1 |
| 14~17 | Opus 독립 | 0 | 3 | ~5 | ~6→~6 | 웹 표본 12 · 실험 재실행 8 |
| 09·10·11·13 판정 | Opus(codex 지적 11) | 채택 5 | 부분 5 | 기각 1 | | 재실험 3 |
| 14~17 판정 | Opus(codex 지적 19) | 채택 13 | 부분 6 | 기각 0 | | 재실행 1 |
| 06·07·08 | Opus 독립 | 0 | ~5 | ~12 | 6→1 | 웹 표본 9 · 실험 재실행 16 |
| 06·07·08 판정 | Opus(codex 지적 10) | 채택 5 | 부분 5 | 기각 0 | | 재실험 1 |
| 19·20 | Opus 독립 | 0 | 3 | ~6 | 0→0 | 웹 표본 8 · 실험 재실행 3 |
| 19·20 판정 | Opus(codex 지적 8) | 채택 7 | 부분 1 | 기각 0 | | 재실험 1 · 정합 Knight 06·cherry 04 동기화 |
| 웹 교차 01~18 | Opus 독립 | 불일치 0 | 확인 불가 1 | 관찰 3 | | 63건 · V5 24+ 충족 |

## 생략한 검증

- 없음(빚 0). 참고 한계: 정합 패스는 지시 축 표적 grep 대조(20편 전문 교차 읽기 아님) · 19 `quotes.py` MISS 53행은 휴리스틱 잡음으로 표본 확인 · 17:65 FSF 판정은 gnu.org 시간 초과로 apache.org 서술로 대조 · 29148 본문 유료로 5.2.5 중 1개 `[?]`.

## 완료 요약

- 산출: `cs/engineering-practice/01~20` 20편(보강 6: 01·14·15·16·17·18 — 원본은 링크로 이어받고 수정 없음, 종합 2: 19·20) + 영역 표 재생성. 부속: 규칙↔검사기 대조표(`rules-vs-checker.md`, 보고만), AIEFS 분석(`docs/plans/2026-10-04/aie-analysis/report.md`).
- 검증: V1 20 PASS · V1b/V2 Opus 사실 점검(중대 0·중간 21, 실험 재실행 전 묶음) · V3 codex(high) 20/20, 지적 80 → 채택 60·부분 19·기각 1 · V4 정합(모순 2 교정·링크 18·깨짐 0) · V5 웹 63건(불일치 0·확인 불가 1 반영).
- 핵심 diff (실파일에서 복사):
  - `cs/engineering-practice/README.md` before `> 현황: 미작성 14 · 원고 있음 1 · 초안(Claude) 5 · 검수 완료 0` → after `> 현황: 미작성 0 · 원고 있음 0 · 초안(Claude) 20 · 검수 완료 0`
  - `02-requirements-engineering/2-summary.md:61` before `절 번호는 표준 견본의 목차로, 목록은 2차 출처로 확인했다(표준 본문은 유료).` → after `절 번호는 표준 견본의 목차로 확인했다. 5.2.5 목록 중 8개는 2차 출처로 확인했고, 준수(conforming)는 그 출처에 이름이 없어 `[?]`다(표준 본문은 유료라 열지 못함).`
- 발견(영역 밖, 보고만 → NEXT): 개인정보 보호법 2026-09-11 개정으로 원본 legal-standards·provisions.md 낡음 · 원본 operational-standards `../../straggler/` 깨짐 · Knight "45분에 4.6억" 축약(reliability/04·ops-patterns/failure-modes) · 다른 영역의 engineering-practice "미작성" 표기 6노트 · os/31의 잘못된 소속 표기.
- CS 이슈 아카이브: 0건(이번 log에 CS 개념 사고·이슈 카드 대상 없음 — 문서 작업).
