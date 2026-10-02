# log — db-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-01 | 인터뷰 4건: 범위 57편 전부(원고 6·초안 3도 새 leaf) · Docker 임시 DB 허용 · 2차 리뷰 codex high, 한도 시 리셋 대기(Opus 대체 없음) → 명세 합의, auto | SPEC=1·MODE=auto, 브랜치 docs/db-writing(main d43fa61a) |
| 2026-10-01 | 컨테이너 기동: sn-dbw-pg(postgres:17 → 17.11, 127.0.0.1:55432), sn-dbw-my(mysql:8.4 → 8.4.10, 127.0.0.1:53306). 스모크: PG 인덱스 스캔 EXPLAIN ANALYZE·기본 read committed, MySQL EXPLAIN FORMAT=TREE·기본 REPEATABLE-READ. psql `-c` 여러 문장은 한 트랜잭션이라 CREATE DATABASE 실패 → 브리핑에 주의 기록 | A1 확인 |
| 2026-10-01 | briefing.md(OS 브리핑 + DB 특칙: 제품·버전 한정, 원고 9편 이어받기 목록, 컨테이너 사용 규칙·전용 DB·부하 상한·절대 경로·루트 금지) | — |
| 2026-10-01 | Opus 집필 워커 11개 발사(공통 지시 scratchpad/db/writer-prompt.md, 워커별 전용 DB w<번호>): 01~05·36 · 06~08·37·38 · 09·11·39·40·53 · 12~14·41·54 · 15~19 · 20·32·33·42·55 · 21~25 · 26~30 · 31·34·35·43·44 · 45~49 · 10·50~52 = 55편. 종합 56·57은 후속 | 회수 대기 |
| 2026-10-01 07:14 | **세션 중단**: 집필 워커 11개가 결과 없이 멈춤(15번 2-summary 1파일만 생성). 컨테이너·게이트(SPEC=1·auto)는 유지, 워커 DB w* 잔존 | 재발사: 공통 지시에 재시작 안내(DB DROP IF EXISTS 후 재생성, 부분 파일 재사용/덮어쓰기) 추가, 같은 11묶음 |
| 2026-10-01 | 회수 1/11: 10·50·51·52(Opus, w10) — check 4 PASS, [?] 0, ⚠ 4/4, 로컬 재현 다수(collation 4종 정렬 차이·ICU ci UNIQUE·NFC/NFD·ai_ci 커서 누락, EXCLUDE 겹침 제약·바이템포럴 AS OF, JSON 표현식·GIN 인덱스, 버전 조건 UPDATE·락 테이블), w10 DROP 확인 | PoEAA·SQL:2011 원문은 카탈로그·논문 경유로 명시 |
| 2026-10-01 | 회수 2/11: 06·07·08·37·38(Opus, w06) — check 5 PASS, [?] 2, ⚠ 5/5, 로컬 재현(pageinspect·bloat·HOT·TOAST·패딩, 링 버퍼 32버퍼·InnoDB young 승격, bigint vs uuid 밀도·WAL FPI, zlib 칼럼 압축, LSM 모형), w06 DROP 확인. 38은 lsm-tree 초안 이어받기(틀린 곳 없음) | — |
| 2026-10-01 | 회수 3~11/11: 45~49(ClickHouse 소스 기본값·PG FTS/pg_trgm·MySQL ngram, async 문서 vs 소스 불일치 기록) · 26~30(락 큐·2038·UUIDv7·부분 유니크·커밋 전 삭제 경합) · 09·11·39·40·53(skip scan·Memoize·hash 버킷·BRIN·래치 경합) · 01~05·36(NOT IN NULL·팬아웃·RANGE 프레임·JSON 검증) · 21~25(Hikari·57014·N+1·자기 호출·PoEAA) · 15~19(40P01·1213·xmin·OCC·group commit) · 12~14·41·54(통계 노후·격리 매트릭스·스필) · 31·34·35·43·44(RLS·keyset·CP949·롤업 멱등) · 20·32·33·42·55(pg_waldump·FPI·XA in-doubt·consistent hash) — 전부 로컬 재현 포함, 워커 DB DROP 확인 | 부하 상한 초과 보고 1(53 pgbench 2.45M·2.75M행, 5초씩, 즉시 DROP). 관찰: sn-dbw-pg에서 백엔드 SIGKILL→실제 크래시 복구(479MiB WAL 2.71s) — 원인 미상(동시 워커 부하 추정), 42 로그 예시로 사용 |
| 2026-10-01 07:39 | **게이트 사고(메인 절차 실수)**: 머리말 정리 작업 명세(docs/plans/2026-10-01/header-cleanup/requirement-spec.md)를 만들어 task-mode-guard가 세션 게이트를 SPEC=0·UNSET으로 리셋 → 진행 중 DB 워커 5개(w12·w15·w20·w21·w31)의 저장소 쓰기가 차단됨. 워커는 우회 없이 scratchpad에 스테이징 | 사용자 합의 후 set-state로 재개 → 스테이징 반영(12·13·14·41·54 / 31·34·35·43·44 / 20·32·33·42·55 / 19 정답 / w21 finish 스크립트 9건 OK) → **55 PASS / 0 FAIL**. 교훈: 병행 작업 중 새 작업 폴더 생성은 게이트를 리셋 — 워커 실행 중에는 새 spec 생성을 미루거나 먼저 사용자 합의 후 즉시 set-state |
| 2026-10-01 07:5x | 종합 56·57 집필 발사 ∥ DB factcheck-briefing(OS 것 DB용: 제품·버전 혼동·SQLSTATE·예외 매핑) + 사실 점검 11개 발사 → **세션 중단(2회째)**: 13개 모두 미완료 상태로 멈춤. 56·57 파일 없음, 55편 PASS 유지, 컨테이너에 fc* 점검 DB 잔존 | 08:13 재개: 워커 13개를 SendMessage로 이어서 진행(전사 보존 — 부분 편집은 현재 파일 재확인 후 계속) |
| 2026-10-01 | 사실 점검 회수 1/11: 26~30 — 중대 0, 중간 1(26 expand/contract 백필 단계 살아 있는 코드 v1 포함 오류), 경미 4(원고 참고 줄 '비휘발 기본값', RFC 9562 문구, NSDI 인용 절), 27·29 무수정, [?] 1 유지, 로컬 재현(MDL 1205·DATETIME 오프셋·uuidv7 부재), check 5 PASS | — |
| 2026-10-01 | 사실 점검 회수 2/11: 10·50·51·52 — 중간 2(10 WEIGHT_STRING 'é' 출력 잘림·ai_ci/as_cs 정렬 행 합침 — 로컬 재현으로 교정), 경미 2(amcheck 문구, Hibernate 3.3.8/3.3.11 귀속), 50·52 무수정, check 4 PASS | — |
| 2026-10-01 | 사실 점검 회수 3/11: 31·34·35·43·44 — 중간 3(31 AWS negative cache 뜻 뒤집힘, 34 Stripe 4단계 순서, 44 VACUUM FULL은 디스크를 테이블 크기만큼 더 씀), 경미 약 8(Spring Data Redis 4.0 deprecated, pg_repack, MySQL euckr 범위, 원고 절 이름, PG md.c 디스크 풀 문구), [?] 4→0, check 5 PASS | — |
| 2026-10-01 | 사실 점검 회수 4/11: 06·07·08·37·38 — 중간 3(06 InnoDB 768바이트 이상 고정 길이도 off-page, 07 README 인용 왜곡(링 dirty 처리), 08 Q6 질문·정답 불일치 — PG 로컬 재현), 경미 약 12(clock sweep 핀 버퍼 건너뜀·링에서 usage 0→1만, 강의 제목, 형제 번호 라벨 16→15·14→10·18→24, RLE 그림 모순, 고전 Leveled), [?] 2 유지, check 5 PASS | — |
| 2026-10-01 | 사실 점검 회수 5/11: 01~05·36 — 중간 2(02 NOT VALID/VALIDATE 락 수준 명시 — 요약·정답), 경미 약 5(Codd 성질 5개, PG 문서 가짜 인용 교체 04, Run Condition 동작 소스 확인), [?] 8→1(2NF 정의만 남음), 로컬 재현 다수(CREATE MATERIALIZED VIEW·PROPERTY GRAPH 구문 오류, jsonb_set WAL ~422KB 등), check 6 PASS | — |
| 2026-10-01 | 사실 점검 회수 6/11: 21~25 — 중간 7(21 PG 비슈퍼유저는 97개 넘으면 'reserved for SUPERUSER' 53300이 먼저·Hikari validationTimeout < connectionTimeout 코드 수정, 22 락 큐 규칙 1·JPA 타임아웃 경로 소스 확인, 24 JpaTransactionManager도 NESTED(세이브포인트)·병렬 스트림 일부만 트랜잭션 참여, 25 Repository 의존 방향 반대), 경미 약 6, [?] 1→0, check 5 PASS | 24 병렬 스트림 정정은 JDK 소스 미열람(일반 지식) — 2차 리뷰 대상 |
| 2026-10-01 | 사실 점검 회수 7/11: 20·32·33·42·55 — 중간 4(20 GitLab "한 번도 성공 없음"→"오류로 끝나고 S3 비어 있음", 32 ROW 안전 예시 NOW()→UUID()/RAND()/SYSDATE()(NOW는 SBR 안전), 32 AFTER_SYNC 무손실은 준동기 유지 중에만, 42 in recovery mode와 Consistent recovery DETAIL은 다른 메시지), 경미 약 8 · 55 수정 0 · 로컬 재현(PG 해시 분포·MySQL 1526) 일치 | 5 PASS · fc20 DROP |
| 2026-10-01 | 사실 점검 회수 8/11: 15~19 — 중간 2(15 innodb_table_locks 조건 문장 뒤집힘, 19 synchronous_commit=on은 동기 대기 서버 flush까지), 경미 9 · 재현 없음(문서·소스 대조) | 5 PASS |
| 2026-10-01 | 사실 점검 회수 9/11: 45~49 — **중대 1**(45 Too many parts 문구·임계 ≥·최대 파티션 기준 — 26.8 소스), 중간 3(45 async insert 쿼리 수 조건은 dedup 시만, 46 stopword는 재시작 불요, 46 BM25 샤드 로컬 통계), 경미 9 · 재현(BRIN·trgm·ngram) 일치 | 5 PASS · fc45 DROP |
| 2026-10-01 | 사실 점검 회수 10/11: 09·11·39·40·53 — 중간 4(09 HOT 요약 인덱스 예외 2곳, 09 INVALID UNIQUE 유일성 강제, 11 병합 조인 등호만), 경미 약 7 · 39 수정 0 · 재현(MySQL HASH→BTREE Note 3502, skip scan) 일치 | 5 PASS · fc09 DROP |
| 2026-10-01 | 사실 점검 회수 11/11: 12~14·41·54 — 중간 6(12 pgJDBC prepareThreshold, 13 HikariCP 반납 시 복원(소스), 14 P2/P3 광의·A 엄격형 병기, 41 TempTable mmap 기본 OFF, 54 fetch count 조건), 경미 약 5 · DDIA 1판 문구는 중국어 번역·2판 영어로 확인(1판 영어 원문 미열람) · 재현(PG 25P02·MySQL 3819) 일치 | 5 PASS · fc12 DROP |
| 2026-10-01 | 종합 56·57 집필 회수(Opus, 2 PASS, w56 DROP) — 56: 55편 장애 절 역색인 + Spring 6.x 기본 번역 경로(서브클래스→SQLSTATE, 40001→CannotAcquireLock, Connector/J 1205→40001 — 소스 판독만) · 57: GitLab·Sentry·GitHub 원문 대조. 교차 지적 7건 → 정합 패스 대기열: ①08↔28 UUIDv4 크기 비율 ②14·16 40001→CannotSerialize는 error-code 경로 한정 ③낡은 "미작성" 16·18·19·20 ④19↔32 WAL 디스크 풀 PANIC 문구 [?] 불일치 ⑤11 §4 깨진 링크 languages/sql/syntax/25-join-fan-out ⑥20 유실 구간 17:20~00:00 vs 23:30 | 사실 점검 56·57 발사(Opus) |
| 2026-10-01 08:30 | codex 2차 리뷰(high, 3병렬) 01~55 시작 — 러너 scratchpad/db/codex/run1.sh·runall.sh(한도 감지 시 즉시 중단, 56·57은 사실 점검 후) | 진행 중 |
| 2026-10-01 | 사실 점검 56·57 회수 — 중간 7(56 wraparound 문구는 PG17만 새 문구·14~16 옛 문구, 57 거부 상태 일반 모드 TRUNCATE 실패 조건, GitHub 옛 주 서버 인과·복구 시간 원인(전송+압축해제·로드) 교정 등), 경미 약 10 · Spring 6.2.x 기본 번역 경로·Connector/J 1205→40001 소스 재확인 일치 · 재현 55P03 두 문구·1205(HY000) · 정합 대기열 추가: ⑦14·15·16 40001→CannotSerialize는 xml 경로 한정(기본 경로 CannotAcquireLock) ⑧16 wraparound 문구에 PG17 한정 | 2 PASS · fc56 DROP |
| 2026-10-01 | codex 01~20 완료(한도 미도달) → 판정 브리핑 adjudicate-briefing.md(OS판 이식) · 판정 4묶음 발사(01~05·06~10·11~15·16~20, Opus) | 회수 대기 |
| 2026-10-01 | 판정 회수 01~05(codex 25건): 채택 20·부분 5·기각 0 — 01 π 예시 DISTINCT 모순·ctid 삭제 IS NOT DISTINCT FROM, 02 ON DUPLICATE KEY는 UPDATE·CHECK NOT ENFORCED, 03 반복 열은 1NF 위반 아님, 04 null-rejected 한정·array_agg는 NULL 포함·sum/count 대안 삭제, 05 순환 UPDATE 뒤 0행·MySQL 재귀 CTE 항상 구체화·절 번호 7.8.3 · 재현(PG fa01) | 5 PASS · fa01 DROP |
| 2026-10-01 | 판정 회수 11~15(codex 28건): 채택 22·부분 6·기각 0 — 11 MySQL 해시 조인 비등호(no condition)·인덱스 없을 때만 해시·findById 영속성 컨텍스트, 12 GIN은 Bitmap만·n_distinct 음수·GEQO 조건, 13 balance=balance-100은 갱신 손실 아님·flush_log_at_timeout·sync_binlog는 binlog 지속성, 14 SSI 취소 조건·WITH CONSISTENT SNAPSHOT, 15 fast-path 락·암묵적 레코드 락·유니크 단건은 레코드 락·PG 교착은 세이브포인트 단위 · 재현 없음 | 5 PASS |
| 2026-10-01 | 판정 회수 06~10(codex 32건): 채택 16·부분 16·기각 0 — 06 파티션 테이블 .ibd 다수(재현)·첫·끝 슬롯 예외, 07 usage_count는 첫 핀만·링 상한 1/8·unlogged 제외, 08 1/16 규칙은 클러스터드 한정·BRIN 예외, 09 UNIQUE면 (a)+(a,b) 통합 불가·파티션 부모 CONCURRENTLY 불가, 10 utf8mb4_bin은 PAD SPACE(재현) → 0900_bin 권장 · stop rule 2(09 부분 인덱스·10 UTS#10) · 재현 fa06 | 5 PASS · fa06 DROP |
| 2026-10-01 | 판정 회수 16~20(codex 29건): 채택 20·부분 8·기각 1(16 #4 — 질문이 커밋·중단을 전제로 줌) — 16 Spring 6 기본 경로 40001→CannotAcquireLock(정합 대기열 ⑦의 16 해소)·backend_xid도 감시(재현)·VACUUM FULL 슈퍼유저 조건, 17 Thomas Write Rule 조건·SET 문법, 18 JDBC/JPA 중복 키 예외 구분, 19 동기 커밋 한정·sync_binlog는 flush_log=1과 함께, 20 증분 백업 비관계 파일 통째·recovery target 이른 시점 불가·FATAL 문구·Azure 스냅숏 미사용 · 재현 fa16 | 5 PASS · fa16 DROP |
| 2026-10-01 | 판정 회수 21·22·23·25·26(codex 24건): 채택 19·부분 4·기각 1(23 OSIV 커넥션 보유 — HibernateJpaVendorAdapter DELAYED_ACQUISITION_AND_HOLD로 노트가 맞음) — 21 Boot 2.0+ Hikari·evict 시 close·keepaliveTime/maxLifetime 분리·connectionTimeout 0=MAX_VALUE, 22 취소 요청은 시도·transaction_timeout prepared 예외, 23 네이티브 쿼리 AUTO flush API별·read-only dirty check 제외, 25 Active Record 테스트 조건, 26 INSTANT 행 버전은 ALTER 문장당(재현) · fa21 | 5 PASS · fa21 DROP |
| 2026-10-01 | 판정 회수 27~31(codex 17건): 채택 14·부분 3·기각 0 — 27 PG epoch 2000-01-01·소수 초 상한, 28 UUIDv7 밀리초 단위 시간순·identity는 유일성 비보장, 29 하드 삭제 배치가 복구 회원까지 지움(재현 DELETE 2→1, 조건 추가)·보관 테이블 FK 모순 해소, 30 round(double,int) 에러(재현)·TTL은 항목 수명 상한, 31 SimpleKeyGenerator null·배열 조건·옛 키는 TTL 있을 때만 소멸 · fa27 | 5 PASS · fa27 DROP |
| 2026-10-01 | 판정 회수 35~37·39(codex 21건): 채택 14·부분 7·기각 0 — 35 CSV 파서 3결함(빈 인용 필드 EOF·길이 상한 off-by-one·비인용 필드 따옴표, Node 재실행 검증)·LOAD DATA IGNORE/LOCAL 의미·엄격 UTF-8 성공≠UTF-8 증거, 36 키 없는 CHECK는 NULL 통과(재현)·jsonb 값 제약·그래프 SQL 열 이름, 37 shared hit≠디스크·ClickHouse 26.3 async_insert 기본 on, 39 해시 크기 "작을 수 있다"·NDB · stop rule 2 · fa35 | 4 PASS · fa35 DROP |
| 2026-10-01 | 판정 회수 24·32~34(codex 28건): 채택 20·부분 8·기각 0 — 24 반환값 롤백(Try·Future)·rollback-only·Reactive 컨텍스트·바깥 세션 타임아웃 모순, 32 물리 복제 바이트 동일 아님(hint bit·UNLOGGED)·ROW에서도 DDL 문장·lag 그림 재작성·40P01, 33 HASH 짧은 범위 가지치기(재현)·pg_stat_statements 정규화·스냅숏 시작 위치, 34 keyset 누락 단서·MySQL 청크 트랜잭션·<=>/IS DISTINCT FROM NULL(재현)·gh-ost critical-load 옵션 · fa24 | 4 PASS · fa24 DROP |
| 2026-10-01 | (참고) header-cleanup 워크트리 커밋 d6f95526 — DB 노트 변환은 그 병합 뒤 | |
| 2026-10-01 | 머리말 정리 main 병합(f3ae23b5 push) → db-writing에 main 병합(0409182d; 브랜치에 있던 사용자 커밋 d8b9653b history 폴더화 이름 변경과 자동 합쳐짐) · DB 57편 새 형식 변환: 머리말 171파일 삭제, 본문용 9줄(원고 연결·버전 기준)은 2-summary 「관련 주제·근거」 첫머리로, metadata.md 57(초안 2026-10-01) | 57 PASS |
| 2026-10-01 | 판정 회수 45~49(codex 34건): 채택 26·부분 7·기각 1(49 package-private @Transactional — Spring 6.0+ 적용됨, 노트가 맞음) — 45 Compact 파트·ORDER BY 확장 가능·OPTIMIZE FINAL은 파티션별·asynchronous_insert_log, 46 trgm 접두 질의 인덱스 사용(재현)·ngram 구 검색 근사·Nori 미등록어, 47 LIKE generic plan Seq Scan(재현)·이스케이프, 48 outbox seq≠커밋 순서 모순 해소·_reindex conflicts proceed·삭제 external 버전, 49 L1 TTL은 L2 맞을 때만 상한·NOLOOP · 미열람 3(ES Delete version_type·BRIN 연산자 목록·Redis hash tags — 일반 지식으로 판정) · fa45 | 5 PASS · fa45 DROP · 정합 패스 때 미열람 3건 원문 대조 |
| 2026-10-01 | 판정 회수 38·40~44(codex 32건): 채택 23·부분 9·기각 0 — 38 RocksDB Bloom 기본 꺼짐·dynamic level base·flush는 스냅숏 버전 보존·tombstone 조기 제거, 40 BRIN 연산자 클래스·SPATIAL SRID, 41 Top-N 힙은 최대 힙·LIMIT도 LACKMEM이면 스필·Using temporary≠디스크, 42 prevLSN=BEGIN·PREPARE/XA PREPARED 예외·XID 없는 ROLLBACK은 ABORT 레코드 없음·WAL 없으면 체크포인트 건너뜀, 43 SET LOCAL 뒤 세션 값 복원(모순 해소)·ON CONFLICT USING 실패는 에러, 44 정합성 쿼리 지표별·누락 버킷 탐지(재현) · fa38 | 6 PASS · fa38 DROP |
| 2026-10-01 | codex 2차 리뷰 57편 완료(재개분 한도 미도달) · 판정 2묶음 발사(50~53, 54~57) | 회수 대기 |
| 2026-10-01 | 판정 회수 50~53(codex 21건): 채택 15·부분 6·기각 0 — 50 이력 트리거가 동시 트랜잭션에서 range 하한>상한 오류(재현)·PG18 WITHOUT OVERLAPS 빈 범위 거부, 51 값 컬렉션 삭제 의미는 매핑 의존·JSON CHECK 가능(재현), 52 소유자 확인과 버전 검사 둘 다 필요·벌크 UPDATE는 @Version 우회·RFC 9110 412는 MAY, 53 InnoDB 분할 중 X 래치 경로 검색 대기·배치 삽입은 튜플별 래치·WALWrite vs WalSync 구분 · 미열람 1(MySQL btr0cur.cc) · fa50 | 4 PASS · fa50 DROP |
| 2026-10-01 | 판정 회수 54~57(codex 23건): 채택 12·부분 11·기각 0 — 54 Parallel Append·Workers Launched 0의 fetch count 원인·pgJDBC 커서 조건(42.7.8), 55 CockroachDB Parallel Commits·TiDB 1PC·TSO 기본 구성·Function<Connection> 컴파일 실패(javac 21) → TxWork, 56 MDL 대기도 1205(재현)·Spring 57014는 6.2.9부터 QueryTimeout·pg_stat_statements는 누적(스냅숏 차이), 57 GitLab은 스테이징 LVM 스냅숏으로 복구·XID 쿼리 TOAST/matview 포함 · fa54 | 4 PASS · fa54 DROP · **DB codex 판정 57편 전부 완료** |
| 2026-10-01 | 정합 패스 발사(Opus): 대기열 8항목(08↔28 UUID 비율, 14·15 Spring 기본 경로, 16 wraparound 판 한정, 19↔32 PANIC 문구, 11 깨진 링크, 20 유실 구간, 낡은 미작성 링크, 판정 미열람 4건 원문 대조) + 공통 사실 일관성 + 웹 교차 표본 27건(web-sample.md) | 회수 대기 |
| 2026-10-01 12:20 | codex 재개분 38·40~49 완료(11편, 한도 미도달) → 판정 2묶음 발사(38·40~44, 45~49) | 회수 대기 |
| 2026-10-01 12:05 | **재부팅**(사고 아님·외부 요인): /tmp 소실 — scratchpad 전체(codex out-01~39 산출물·러너, 판정 산출물) · 컨테이너 전부 정지 → 재기동·스모크(PG·MySQL 1) · 판정 반영분은 노트에 있어 손실 없음 · codex 러너 재작성, 남은 38·40~57 재개(12:07) | 진행 |
| 2026-10-01 09:25 | codex 1차 실행 종료: 01~37·39 완료(38편), 38·40~41에서 **사용 한도**(리셋 11:57) → 남은 38·40~57(20편)은 11:59 자동 재개 러너(runrest.sh) 대기 · 판정 2묶음 발사(24·32~34, 35~37·39) | 명세대로 리셋 대기(Opus 대체 없음) |
| 2026-10-01 | 정합 패스 회수: 대기열 8항목 처리(08↔28 UUID 비율 측정 대상 명시, 14·15 Spring 6.x 기본 경로 정렬 + 15 재시도 주석의 55P03·3572 오분류 발견·수정, 16 wraparound 판 한정, 19↔32 PANIC 문구 xlog.c 근거로 통일, 11 링크는 실재(수정 없음), 20 유실 구간, 낡은 미작성 링크 약 35개 실링크, 미열람 4건 원문 대조 ✓) · 공통 사실 정정 2(22 1205 SQLSTATE 드라이버 층, 13 flush_log 0 vs 2 유실 조건) · 웹 표본 27/27 · 57 PASS · 링크 988 깨짐 0 | 영역 README 재생성(초안 57) · 컨테이너 sn-dbw-pg·my와 익명 볼륨 삭제(남은 작업 DB 0 확인) |
| 2026-10-01 | 마감: 완료 요약·생략한 검증·NEXT(N0-c 갱신·N0-h 추가)·측정로그 1행 · 아카이브: CS 이슈 0건(발견 사실은 노트 본문 반영, 게이트 리셋·재부팅은 도구·환경 사정) | 커밋 |
| 2026-10-02 | main ff → 69df46fb push(사용자 확인 — 폴더화 커밋 d8b9653b·5c741169 포함) | 완료 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 26~30 | Opus 독립 | 0 | 1 | 4 | 1→1 | 웹 표본 15 |
| 10·50~52 | Opus 독립 | 0 | 2 | 2 | 0→0 | 웹 표본 12 |
| 31·34·35·43·44 | Opus 독립 | 0 | 3 | ~8 | 4→0 | 웹 표본 15 |
| 06~08·37·38 | Opus 독립 | 0 | 3 | ~12 | 2→2 | 웹 표본 15 |
| 01~05·36 | Opus 독립 | 0 | 2 | ~5 | 8→1 | 웹 표본 18 |
| 21~25 | Opus 독립 | 0 | 7 | ~6 | 1→0 | 웹 표본 15 |
| 20·32·33·42·55 | Opus 독립 | 0 | 4 | ~8 | 3→3 | 웹 표본 15 |
| 15~19 | Opus 독립 | 0 | 2 | 9 | 5→4 | 웹 표본 15 |
| 45~49 | Opus 독립 | 1 | 3 | 9 | 10→9 | 웹 표본 15 |
| 09·11·39·40·53 | Opus 독립 | 0 | 4 | ~7 | 6→5 | 웹 표본 15 |
| 12~14·41·54 | Opus 독립 | 0 | 6 | ~5 | 5→1 | 웹 표본 15 |
| 56·57 | Opus 독립 | 0 | 7 | ~10 | 5→3 | 웹 표본 6 |
| 01~05 판정 | Opus(codex 지적 25) | 채택 20 | 부분 5 | 기각 0 | | |
| 11~15 판정 | Opus(codex 지적 28) | 채택 22 | 부분 6 | 기각 0 | | |
| 06~10 판정 | Opus(codex 지적 32) | 채택 16 | 부분 16 | 기각 0 | | |
| 16~20 판정 | Opus(codex 지적 29) | 채택 20 | 부분 8 | 기각 1 | | |
| 21~26(24 제외) 판정 | Opus(codex 지적 24) | 채택 19 | 부분 4 | 기각 1 | | |
| 27~31 판정 | Opus(codex 지적 17) | 채택 14 | 부분 3 | 기각 0 | | |
| 35~37·39 판정 | Opus(codex 지적 21) | 채택 14 | 부분 7 | 기각 0 | | |
| 24·32~34 판정 | Opus(codex 지적 28) | 채택 20 | 부분 8 | 기각 0 | | |
| 45~49 판정 | Opus(codex 지적 34) | 채택 26 | 부분 7 | 기각 1 | | |
| 38·40~44 판정 | Opus(codex 지적 32) | 채택 23 | 부분 9 | 기각 0 | | |
| 50~53 판정 | Opus(codex 지적 21) | 채택 15 | 부분 6 | 기각 0 | | |
| 54~57 판정 | Opus(codex 지적 23) | 채택 12 | 부분 11 | 기각 0 | | |

## 생략한 검증

- 재부팅(12:05)으로 codex 01~39 원문 산출물 소실 — 판정 결과는 노트에 반영된 뒤라 내용 손실 없음, 원문 재대조는 불가.
- 분산 영역(동시 진행) 노트로의 링크는 그 노트가 아직 미추적이라 "미작성" 유지 — distributed 커밋 때 재링크.

## 완료 요약

- **산출**: `cs/database/` 57편 × 4파일(1-question·2-summary·3-answer·metadata) — 미작성 48 + 원고 보강 6 + 기존 초안 보강 3, 종합 56(증상 역색인)·57(사고 3건). 영역 README: 미작성 0·초안 57. 머리말 정리(header-cleanup) 병합 뒤 새 형식으로 변환.
- **파이프라인**: Opus 집필 ×11(+종합 1) → Opus 사실 점검 ×12 → codex high 2차 리뷰 57편 전수(한도 1회 → 리셋 대기, Opus 대체 없음) → Opus 판정 ×12 → 정합 패스 → 웹 교차 27.
- **수치**: 1차 점검 중대 1(45 Too many parts)·중간 약 51 · 2차 지적 314건 → 채택 221·부분 90·기각 3 · 정합 정정 약 45(링크 35 포함) · 웹 27/27 · check 57 PASS · 링크 988 깨짐 0.
- **대표 정정**: 10 `utf8mb4_bin`은 PAD SPACE(재현) → `utf8mb4_0900_bin` · 29 하드 삭제 배치가 복구 회원까지 삭제(재현 DELETE 2→1) · 30 TTL은 항목 수명 상한일 뿐 · 34 백필·검증 SQL이 NULL 행 누락(`<=>`/`IS DISTINCT FROM`) · 50 이력 트리거 동시 트랜잭션 range 오류(재현) · 55 `Function<Connection,T>` 컴파일 실패(javac 21) · 56 Spring 57014→QueryTimeout은 6.2.9부터.
- **사고**: 게이트 리셋으로 워커 5개 쓰기 차단(명세 생성 시점 교훈) · 재부팅으로 /tmp 소실(외부 요인).

