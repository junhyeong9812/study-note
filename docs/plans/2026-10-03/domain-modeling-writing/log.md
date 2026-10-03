# log — domain-modeling-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-03 09:30 | 상태 확인: reliability(c228d690)·software-design(e9e50f1f) 모두 다른 실행이 완료·push(origin/main 1d0d8b13) · 미커밋 로그 2줄 커밋(08c53572) | |
| 2026-10-03 | 인터뷰 2건(영역 도메인 모델링 · 검증 앞 영역과 같게) → 명세 합의, auto · 브랜치 docs/domain-modeling-writing(main 08c53572) | SPEC=1·MODE=auto |
| 2026-10-03 | 브리핑(software-design판 이식 — 도메인 실험 예시·트랙 안내 노트 규칙·도커 안전 규칙 강화: prune·pull·rmi 금지) · 이미지 확인(temurin 21·maven·postgres 17·redis 7 있음) | |
| 2026-10-03 | 집필 발사(Opus 6병렬, 26편): 01·02·03·06·07 / 04·05·08·10 / 09·11·21·22 / 12·13·14·23 / 16~20 / 24·25·15·26 — 종합 27·28 후속 · 프롬프트 scratchpad/dm/writer-prompt.md(다른 실행 흔적 확인 지시 포함) | 회수 대기 |
| 2026-10-03 | 집필 회수 1/6: 09·11·21·22(4 PASS, 각 10문항, [?] 3) — 실험: 09 Spring 6.2.11 @EventListener 롤백 주문에도 메일 10회(유령 5)·AFTER_COMMIT 5회·AFTER_COMMIT DB 쓰기가 전파 없이도 저장됨(pgjdbc setAutoCommit 커밋 가설, [?])·REQUIRED 리스너 기동 실패 메시지, 11 if 블랙리스트 불법 전이 19/56 vs 전이 표 0·동시 취소/출고 RC 200/200 둘 다 성공 vs 조건부 UPDATE·RR 40001, 21 seq 체크포인트 투영 누락 18~25 → advisory lock 0·RYW 토큰 대기·재구축 EXCEPT 30행, 22 참조만 기록 시 재계산 불일치 40/100 vs 스냅숏 0·해시 체인 변조 탐지·세션 TimeZone 변경만으로 검증 100/100 실패 · 21 원본 CDC "유실 없음" 조건 정정 | 전용 컨테이너 정리 |
| 2026-10-03 | 집필 회수 2/6: 12·13·14·23(4 PASS, [?] 3) — 실험: 12 단위 값 객체(lbf·s+N·s)·double 누적 오차·건별 vs 총액 반올림 13원·NY 하루 23/25시간, 13 tzdb 규칙 변경(2026e 매니토바 모형)으로 미래 예약 1시간 어긋남·plusMonths 연쇄 28일 고착·생일 UTC 자정 저장·DST 벽시계 스케줄러 0/2/1회·RFC 9557 파싱, 14 1원 배분(largest remainder vs Fowler)·줄 vs 합계 세액 4309/10000 불일치·할인·세금 순서 33,000 갈림·통화 자릿수·BigDecimal equals/HashSet/TreeSet·JS 2^53, 23 PG EXCLUDE 겹침 거절·덮어쓰기 재계산 599건 불일치 vs 판 스탬프 0·배포 시각=발효 가정 36건 · 커리큘럼 이진 탐색 경로 04→실제 06 | 정리 확인 · 사실 점검 주의: tzdb 2025a·2026e 항목 원문 대조 |
| 2026-10-03 | 집필 회수 3/6: 16~20(5 PASS, [?] 약 7 — Khononov·Vernon·Evans 14장 원문 쪽 미확인) — 실험: 16 공유 Customer 한 줄 변경이 컴파일 오류 없이 영업 규칙 깨뜨림 vs 컨텍스트별 모델(반대 변경 비용도), 17 시간대 자체 구현 고정 UTC-5 238/365일 오류, 18 관계 맵 파급 BFS·getOrDefault 조용한 0 vs 계약 테스트 FAIL, 19 ACL 없음 4/4 조용한 실패·3파일 vs ACL 1파일 1줄, 20 보드 데이터 문법 검사 · DDD Reference 2015 PDF 원문 대조 | 정리 확인 · 정합 대기열: 16·17·20의 03·07 "미작성" 링크 |
| 2026-10-03 | 집필 회수 4/6: 24·25·15·26(4 PASS, 각 10문항, [?] 4) — 실험: 24 PG 17.11 지연 제약 트리거로 불균형 전표 커밋 거절·멱등 재전송 0행·UPDATE/DELETE 거절·역분개·동시 이체(잠금 없음 −3000, FOR UPDATE+RC 3000, FOR UPDATE+RR −3000)·TRUNCATE 행 트리거 우회·지연 트리거 인덱스 유무 19s vs 0.3s·트리거 search_path 함정, 25 분류 대사 사고 7종 탐지·EXCEPT는 중복 놓침/EXCEPT ALL·KST vs UTC 경계 가짜 차이 376 · 15·26 컬렉션 60편 읽고 트랙 안내 · 기존 basic/01 측정 문장 모순("넷 다 절반 넘었다" vs 444/1000)을 새 노트에 참고로 짚음(원본 미수정) | 정리 확인 · 링크 해소 스크립트 scratchpad/dm/24/resolve_links.py(정합 때 재실행) |
| 2026-10-03 | 집필 회수 5/6: 04·05·08·10(4 PASS, [?] 2) — 실험: 04 Hibernate 6.6.29+H2 equals 없는 값 객체 HashSet 2 vs record 1·생성 ID equals 저장 후 contains=false·가변 @Embeddable 공유 시 두 행 변경, 05 PG 17.11 거대 애그리거트 충돌 1976~2242 vs 작은 0·경계 밖 불변식 합 24/10·mappedBy 자식만 수정 시 루트 version 불변 vs FORCE_INCREMENT, 08 비대 서비스 우회 경로 2/3 vs 0/3·if vs 정책 diff(if가 더 작음 — 반대 측면 실음), 10 리포지토리 SQL에 옛 규칙 남아 불일치 10 vs 명세 객체 0·생성 vs 재구성 경로 · jar는 로컬 ~/.m2와 다른 워커 scratchpad에서 복사(네트워크 미사용) | 정리 확인 |
| 2026-10-03 | 집필 회수 6/6: 01·02·03·06·07(5 PASS, [?] 5) — 실험: 01 규칙 분산 위반 경로 2/3 vs 엔티티 0/3·규칙 변경 3파일 vs 1, 02 Hibernate 6.6 세션 밖 LazyInitializationException·프록시 필드 null vs getter·더티 체킹·무인자 생성자 없음 예외, 03 "주문 완료" 다의어 집계 5 vs 2·delay 5ms vs Duration·용어집 검사, 06 퍼징 빈약(setter) 위반 9974/10000 vs 풍부 0·BFS 도달 상태, 07 TS 3파일 vs DM 1파일·PG 트랜잭션 경계 재시도 A=800/B=200 vs 900/100 · 원본 보정 2줄(01)·1줄(02) · **집필 26/26 완료** | 정리 확인 |
| 2026-10-03 | 26 PASS 확인 · 사실 점검 브리핑(factcheck-briefing.md — 설계판 이식, tzdb·ISO 4217 원문 재확인·도커 안전) · 사실 점검 6묶음 + 종합 27·28 집필 발사(Opus) | 회수 대기 |
| 2026-10-03 | 사실 점검 회수 1/6: 12·13·14·23 — 중대 0, 중간 4(13 Skeet 필드 뜻·JDK 패치 번호별 tzdb(21.0.12=2026b에 파라과이 반영)·정답 6 실험 라벨, 23 btree_gist F.7→F.8), 경미 약 9(12 Analysis Patterns 3장 목차 확인 [?]−2, 13 매니토바 tzdb 모델 11-01·ZonedDateTime 조정 시 이전 오프셋 유지·postgres:17 OS tzdata 2026c 실측 추가, 23 Effectivity 2004-03-07) · 14 수정 0 · 재실행 10건 전부 일치(결정적 출력 동일) · tzdb 2025a·2026e·ISO 4217(2026-09-17 공표) 원문 일치 · 노트 밖 참고: languages/java/syntax/51 "17·21=2024a"는 패치 번호 한정 필요 | 4 PASS · 정리 확인 |
| 2026-10-03 | 사실 점검 회수 2/6: 16~20 — 중대 0, 중간 5(16 설계 B 성공은 공개 언어 정의에 달림 — 변형 재실행 `== SUSPENDED`면 B도 failures=1, 17 Khononov 속성 표 출처 과장 → [?], 18 DDD Crew 라이선스 CC BY-SA→CC BY 4.0·Reference `*` 각주 확인, 19 ACL 예외 경로의 반대 측면(PG 승인 건 대사 필요)), 경미 약 10 · 재실행 5건 전부 바이트 동일(19 첫 회 하네스 경합 — 노트 무관) · 03·07 "미작성" 링크 실재로 · [?] −1+2 | 5 PASS · 정리 확인 |
| 2026-10-03 | 사실 점검 회수 3/6: 04·05·08·10 — 중대 0, 중간 4(05 충돌 범위 1976~2242 → 1938~2313(12측정)·"3회 같은 결과" 틀림(재시도 수 실행마다 다름)·Evans 크기 수치 주장 Reference 2015로 한정, 08 Fowler 인용의 저자 주장과 해석 분리), 경미 4(04 ISO 4217 출처, 05 Spring 예외 변환 소스 확인 [?] 해소, 08 07 링크, 10 2ⁿ−1) · 재실행 6종 일치(05 A는 범위 확장) | 4 PASS · 정리 확인 |
| 2026-10-03 | 사실 점검 회수 4/6: 01·02·03·06·07 — 중대 0, 중간 4(02 "final이면 연관 즉시 읽음" 근거 없음 → 점검 실험(Hibernate 6.6.29 final 엔티티 LAZY는 실제 클래스·initialized=true)으로 근거 부여, 03 "배송 전 6건 중 3건" 틀림 → 수정, 07 실험 B 정체불명 출력 줄 → 재실행 출력으로 교체·HttpSecurity catch-all은 HTTP만), 경미 약 7 · 재실행 9종 일치(02 시간 범위 확대) · 원본 정정 줄 3개 원문 대조 일치 · 참고: 2-summary mtime 12:10:12 일괄 — 24 집필자의 resolve_links.py(양방향 링크 해소)로 추정 | 5 PASS · 정리 확인 |
| 2026-10-03 | 사실 점검 회수 5/6: 09·11·21·22 — **중대 1**(09 AFTER_COMMIT 쓰기 저장 원인 [?] 해소: Spring 6.2.11 doCleanupAfterCompletion이 autoCommit 복원 → pgjdbc setAutoCommit(true)가 commit, 연결 초기 autoCommit=false면 반대 결과 audit_a 0 — 반례 실험 추가, Hikari 반납 시 롤백 조건), 중간 5(09 장애 3 조건 설명, 11 PAID--REFUND 뜻 오기·미측정 빈도 단정 삭제, 21 시퀀스 빈칸 누락 범위 18~25 → 14~25), 경미 약 10(BEFORE_COMMIT 제외, 이벤트 식별자 Reference 문구, Harel 원문, enhanced switch 망라 검사 등) · 재실행 10종 일치(22 해시까지 동일) · [?] 09 −1·21 −1 | 4 PASS · 정리 확인 |
| 2026-10-03 | 사실 점검 회수 6/6: 24·25·15·26 — 중대 0, 중간 7(24 수수료 다중 분개 부호가 노트 규칙과 반대, 25 EXPLAIN 주장 틀림 — 실제 Sort+GroupAggregate(재실행)·KST/UTC 376 중 375 가짜+1 실제 누락, 15 basic/12 예시 오인·낡은 미작성 링크, 26 자료구조 표 21 오분류·06 링크), 경미 약 7 · 재실행 12종(25 EXPLAIN 1건 불일치 → 수정, 24 시간 범위 확대) · 15·26 트랙 안내 60행 전부 컬렉션 원문 대조 일치 · [?] 24 3→1 | 4 PASS · 정리 확인 · **사실 점검 26/26 완료** |
| 2026-10-03 12:25 | 2차 리뷰: codex 한도(리셋 10-04 08:53) → 명세 A2·V3대로 Opus 적대 리뷰 6묶음 발사(26편, 지적만 기록·수정 없음, scratchpad/dm/opusrev/out-NN.md) | 회수 대기 |
| 2026-10-03 | Opus 적대 리뷰 회수 6/6(26편, 지적 30건): 01·03·06·15·16·18·22·23 0건 · 02 3(프록시 필드는 초기화 뒤에도 null — 재현, JPA 접근자 요구 아님, in-line dirty tracking) · 04 2(Set.of 테스트 무의미, record equals 순서 비명시) · 05 2(버전 미증가 원인은 mappedBy 아님, OptimisticEntityLockException은 Hibernate 네이티브) · 07 2(Spring Data 쿼리 메서드 기본 트랜잭션 없음, AspectJ 모드 예외) · 08 1 · 09 1(REQUIRED 거부는 @EnableTransactionManagement 경로 한정·6.1.3) · 10 1(기본 UPDATE 전체 컬럼) · 11 1(실행 횟수 모순) · 12 5(ZoneRules lastRules 경로·하루 길이 예외(Lord_Howe·Apia·Santiago)·RFC 9557 오프셋 필수 등) · 13 3(진단 SQL 오탐 — Java/PG 중복 시각 해석 차) · 14 1(반올림 기본값 반례) · 17 1 · 19 1 · 20 1(보라=원인) · 21 2(EXCEPT는 HashSetOp·CQRS 확장 해석 출처) · 24 1 · 25 1 · 26 2 → 판정 6묶음 발사 | 회수 대기 |
| 2026-10-03 | 종합 27·28 회수(2 PASS, [?] 0) — 27: 장애 시나리오 121개 전수 색인·⚠ 10개 대응·반올림 모드 7종 실행으로 초안 오류("어떤 모드로든 9,999" → UP·CEILING은 10002) 발견·쿼리 네 모양 PG 실행, 28: MCO(MIB 보고서)·Post Office Horizon(Bates No 6 판결문 문단 인용)·Azure 2012 윤일·tzdb 규칙 변경(2022f·2023a~c) 1차 출처만, 모형 실험(연도+1 API별 결과·lbf·s 4.4482·파우치 중복) · Zune은 1차 출처 없어 제외 · 커리큘럼 28행 Horizon "1999~" vs 판결 "2000" → NEXT · 정합 대기열: 03·12·25·26의 27·28 미작성 링크 | **사고(경미)**: 저장소 루트에 0바이트 파일 Append·Seq(12:27:55, 리뷰어 셸 리다이렉트 추정) — 비어 있고 미추적 확인 후 삭제 |
| 2026-10-03 | 판정 회수 24·25·15·26(Opus 리뷰 지적 6건): 채택 4·부분 2·기각 0 — 24 two/multi-legged는 모델 구분(Fowler 원문), 25 재결제는 새 order_id라 DUPLICATE 아님(노트 안 모순 해소)·Stripe 보고서 자동 지급 조건, 26 표 17·20 오분류·04 측정 조합 9 | 4 PASS |
| 2026-10-03 | 판정 회수 09·11·21·22(Opus 리뷰 지적 4건): 채택 4·기각 0 — 09 REQUIRED 리스너 거부는 @EnableTransactionManagement 경로 한정·NOT_SUPPORTED 6.1.3+(소스·이슈 확인), 11 실행 횟수 모순, 21 EXCEPT 실측 HashSetOp Except(NOT EXISTS는 Hash Anti Join)·CQRS의 CQS 확장 해석을 Fowler 주장과 분리 | 4 PASS · 일회용 PG 정리 |
| 2026-10-03 | 판정 회수 16~20(Opus 리뷰 지적 3건): 채택 2·부분 1·기각 0 — 17 고정 오프셋 "수십 일" → 238일(실험 출력과 정합), 19 Evans ACL = 퍼사드·어댑터·번역기 조합(SO 인용으로 확인, 그림·쪽은 [?] 유지 — 리뷰어 근거 URL엔 문장 없었음), 20 보라는 원인 표시·이벤트는 모두 주황(2013 원문) | 5 PASS |
| 2026-10-03 | 판정 회수 01·02·03·06·07(Opus 리뷰 지적 5건): 채택 5·기각 0 — 02 프록시 필드 id는 초기화 뒤에도 null(판정자 재실행 출력 추가)·isInitialized는 해결책 아님·JPA는 필드 접근이면 접근자 불요·in-line dirty tracking 예외, 07 Spring Data 선언 쿼리 메서드는 기본 트랜잭션 없음·self-invocation 미적용은 프록시 모드 한정(AspectJ 예외) | 5 PASS |
| 2026-10-03 | 판정 회수 12·13·14·23(Opus 리뷰 지적 9건): 채택 8·부분 1·기각 0 — 판정자 재실행: ZoneRules 마지막 저장 전이 New_York·Winnipeg 2008(이후는 lastRules 선형 비교)·Lord_Howe 24h30m/23h30m·Apia 2011-12-30 없음·Santiago 자정 공백·XAU fraction −1·longValue 절사·MathContext(1) HALF_UP·PG 중복 시각 표준시 해석·numeric(19,4) 조용한 반올림 → 12·13·14 본문 조건·예외 반영, 12 RFC 9557 오프셋 필수(부분) · 미열람 2(RFC 9557·PG B.2 원문 — 재현으로 대체) | 4 PASS · 일회용 PG 정리 |
| 2026-10-03 | 판정 회수 04·05·08·10(Opus 리뷰 지적 6건): 채택 5·부분 1·기각 0 — 판정자 실험: Set.of 같은 값 둘 → IllegalArgumentException(테스트 그린 위장 수정)·소유 단방향 @OneToMany 자식 필드만 수정 시 루트 version 불변(원인은 mappedBy 아님)·기본 UPDATE 전체 컬럼 vs @DynamicUpdate, javap로 OptimisticEntityLockException은 Hibernate 네이티브·JPA 부트스트랩은 OptimisticLockException으로 감쌈, 08 Vernon 네 사유 "these and others"(부분) · 미열람 2(Record.equals javadoc·Hibernate Dynamic updates 절) → 정합 패스에서 원문 대조 · **2차 리뷰 판정 26편 완료**(지적 33 → 채택 28·부분 5·기각 0) | 4 PASS |
| 2026-10-03 | 사실 점검+2차 리뷰 회수 27·28 — **중대 2**(27 "1원 원인 넷, 모드는 무관" → 흔한 원인 셋(배분·반올림 위치·서로 다른 모드), 자릿수·스케일은 별도 증상 — 14 현행 본문·PG 재실행 근거, 1-question 2 문구도; 27 주문 4 해석이 25와 모순 → DUPLICATE_EXTERNAL 형태), 중간 4(27 05-3 원인·25-1 처리, 28 Azure "first time" 오독·판결 문단 [963]→[964]), 경미 약 6(30분 DST, EXCEPT 집합 연산, Horizon TC 정의·회의 문서 연도·해석 표시, MCO 라벨) · 27 행 121개를 01~26 현행 장애 절과 전수 대조 · 재실행 4종 일치 | 2 PASS · 정리 확인 |
| 2026-10-03 | 정합 패스 발사(Opus): 낡은 미작성 링크 · 판정 미열람 원문 5건(Record.equals·Dynamic updates·RFC 9557 §4.1·PG B.2·Evans 14장) · 공통 사실 교차 대조 7군 · 웹 교차 표본 20+ 신설 · 28 PASS·링크 0 | 회수 대기 |
| 2026-10-03 | 정합 패스 회수: 낡은 미작성 링크 6 → 실링크 · 미열람 원문 5건 대조(Record.equals·Dynamic updates·RFC 9557 일치, PG B.2는 "전이 직후 오프셋"으로 13 정밀화, Evans 14장 "One way" 문구) · 교차 정합 3(10↔05 원인, 04 프록시 equals 보강, 27↔25 분류 이름 대응) · 웹 표본 35행/26편 ✅33 ✗2(DDD Crew 라이선스 README CC BY vs LICENCE CC BY-SA → 17·18·20 병기) · 28 PASS · 링크 1070 깨짐 0 | |
| 2026-10-03 | 마감: 생성 문서 cs/domain-modeling/curriculum.md 재생성(초안 28, 다른 영역 변화 없음) · 컨테이너 sn-dm-* 0 · 저장소 루트 잔여 파일 0 · 완료 요약·NEXT·측정로그 · 아카이브: CS 이슈 0건(발견 사실은 노트 본문에 반영, 루트 빈 파일·동시 실행은 도구 사정) | 커밋 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 12·13·14·23 | Opus 독립 | 0 | 4 | ~9 | 3→1 | 웹 표본 12 · 재실행 10 |
| 16~20 | Opus 독립 | 0 | 5 | ~10 | 7→8 | 웹 표본 15 · 재실행 5(+변형 1) |
| 04·05·08·10 | Opus 독립 | 0 | 4 | 4 | 3→3 | 웹 표본 12 · 재실행 6 |
| 01·02·03·06·07 | Opus 독립 | 0 | 4 | ~7 | 5→5 | 웹 표본 15 · 재실행 9(+추가 1) |
| 09·11·21·22 | Opus 독립 | 1 | 5 | ~10 | 3→1 | 웹 표본 12 · 재실행 10(+반례 1) |
| 24·25·15·26 | Opus 독립 | 0 | 7 | ~7 | 4→2 | 웹 표본 8 · 재실행 12 |
| 24·25·15·26 판정 | Opus(적대 리뷰 지적 6) | 채택 4 | 부분 2 | 기각 0 | | |
| 09·11·21·22 판정 | Opus(적대 리뷰 지적 4) | 채택 4 | 부분 0 | 기각 0 | | 재실행 1 |
| 16~20 판정 | Opus(적대 리뷰 지적 3) | 채택 2 | 부분 1 | 기각 0 | | |
| 01·02·03·06·07 판정 | Opus(적대 리뷰 지적 5) | 채택 5 | 부분 0 | 기각 0 | | 재실행 1 |
| 12·13·14·23 판정 | Opus(적대 리뷰 지적 9) | 채택 8 | 부분 1 | 기각 0 | | 재실행 3종 |
| 04·05·08·10 판정 | Opus(적대 리뷰 지적 6) | 채택 5 | 부분 1 | 기각 0 | | 실험 3 |
| 27·28 | Opus 독립(점검+리뷰) | 2 | 4 | ~6 | 0→0 | 웹 표본 7 · 재실행 4 |

## 생략한 검증

- codex 2차 리뷰 없음 — 한도(리셋 10-04 08:53)로 명세 A2·V3대로 Opus 적대 리뷰 26편 + 27·28은 사실 점검자가 리뷰 겸함. 앞 영역 관측상 대체 리뷰는 codex보다 덜 찾는다 → 선택 후속: 한도 해제 뒤 codex로 표본 재리뷰(NEXT).
- 책 원문 미열람(Evans DDD 본문 일부·Vernon IDDD·Khononov·Analysis Patterns 본문) — 목차·발췌·저자 공개 PDF로 확인한 범위만 단정, 나머지 `[?]`.

## 완료 요약

- **산출**: `cs/domain-modeling/` 28편 × 4파일(1-question·2-summary·3-answer·metadata) — 신규 23 + 보강 3(01·02·21, 원본 수정 없음) + 연습 트랙 안내 2(15·26, basic·advanced 60편 대조) · 종합 27(장애 시나리오 121개 역색인)·28(MCO·Horizon·Azure 2012·tzdb 규칙 변경). 생성 문서 curriculum.md: 미작성 0·초안 28.
- **파이프라인**: Opus 집필 ×7 → Opus 사실 점검·실험 재실행 ×7 → 2차 리뷰 Opus 적대 ×6(codex 한도) → Opus 판정 ×6 → 정합 패스 → 웹 교차 35.
- **수치**: 1차 점검 중대 3(09 AFTER_COMMIT 저장 원인 소스로 확정 + 반례 실험, 27 1원 원인 재정의, 27 주문 해석 모순)·중간 약 33 · 2차 지적 33 → 채택 28·부분 5·기각 0 · 정합 정정 약 12 · 웹 33/35(✗2 라이선스 병기로 수정) · check 28 PASS · 링크 1070 깨짐 0.
- **실험 근거(사용자 요청)**: 편마다 실행 결과를 근거로 실음 — 예) 빈약 모델 퍼징 위반 9974/10000 vs 풍부 0, 거대 애그리거트 충돌 1938~2313 vs 0, 1원 배분·반올림 모드 7종, DST 벽시계 스케줄러 0/2회, 원장 동시 이체 −3000(잠금 없음)·EXCEPT vs EXCEPT ALL, Spring AFTER_COMMIT 쓰기가 autoCommit 복원으로 커밋되는 경로(반례 0행).
- **대표 정정**: 05 루트 version 불변 원인 `mappedBy` → 자식 필드는 버전 검사 밖(소유 단방향도 동일, 실험 C-3) · 10 기본 UPDATE 전체 컬럼(@DynamicUpdate) · 02 프록시 필드는 초기화 뒤에도 null · 12·13 하루 길이 예외(Lord_Howe·Apia·Santiago)·ZoneRules lastRules 경로 · 25 EXPLAIN 실측(Sort+GroupAggregate) · 21 EXCEPT = HashSetOp.
- **사고**: 저장소 루트 0바이트 파일 2개(리뷰어 셸 리다이렉트 추정, 삭제) — 그 밖 없음(동시 실행 없음 확인).

