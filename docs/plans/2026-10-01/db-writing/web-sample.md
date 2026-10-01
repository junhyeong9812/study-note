# 웹 교차 표본 — 데이터베이스 (V5)

> 사실 점검 packet의 "원문으로 직접 확인한 외부 사실"에서 편마다 1~2개씩 뽑은 27건. 정합 패스 작업자가 URL을 다시 열어 인용이 원문에 있는지, 노트가 그 사실과 맞게 쓰는지 확인하고 결과 칸을 채운다.

| # | 노트 | 주장 | 출처 | 원문 인용 | 결과 |
|---|---|---|---|---|---|
| 1 | 12 | Seq Scan 비용식 | https://www.postgresql.org/docs/17/using-explain.html | "(disk pages read * seq_page_cost) + (rows scanned * cpu_tuple_cost)" || ✅ (공백 차이만) |
| 2 | 12 | 처음 다섯 번은 custom plan | https://www.postgresql.org/docs/17/sql-prepare.html | "the first five executions are done with custom plans" || ✅ |
| 3 | 13 | InnoDB 문장 롤백은 락을 놓지 않음 | https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html | "Locks are not released in a rollback of a single SQL statement." || ✅ (curl 차단 → WebFetch로 확인) |
| 4 | 14 | PG RR = 스냅숏 격리 | https://www.postgresql.org/docs/17/transaction-iso.html | "implemented using a technique known … as Snapshot Isolation" || ✅ |
| 5 | 15 | 교착 검사 대기 기본 1s | https://www.postgresql.org/docs/17/runtime-config-locks.html | "The default is one second (1s)" || ✅ (공백 차이만) |
| 6 | 16 | XID 300만 남으면 할당 거부 | https://www.postgresql.org/docs/17/routine-vacuuming.html | "refuse to assign new XIDs once there are fewer than three million transactions left" || ✅ — 16 거부 문구에 17판 한정 추가(14~16판 문구 병기) |
| 7 | 17 | Thomas Write Rule과 충돌 직렬성 | https://15445.courses.cs.cmu.edu/fall2023/notes/17-timestampordering.pdf | "conflict serializable if it does not use Thomas Write Rule" || ✅ |
| 8 | 18 | ON CONFLICT DO UPDATE 원자성 | https://www.postgresql.org/docs/17/sql-insert.html | "guarantees an atomic INSERT or UPDATE outcome" || ✅ |
| 9 | 19 | SSD 캐시 flush 무시 | https://www.postgresql.org/docs/17/wal-reliability.html | "many of these do not honor cache flush commands by default" || ✅ |
| 10 | 20 | archive_command 성공 시에만 0 | https://www.postgresql.org/docs/17/continuous-archiving.html | "return zero exit status if and only if it succeeds" || ✅ |
| 11 | 32 | 준동기 타임아웃 시 비동기 복귀 | https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html | "the source reverts to asynchronous replication" || ✅ (WebFetch) — 32 §동작·정답 3 "비동기로 되돌아간다" 일치 |
| 12 | 33 | 유니크 키는 분할 식 컬럼 포함 | https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html | "every unique key on the table must use every column in the table's partitioning expression" || ✅ (WebFetch) |
| 13 | 42 | 크래시 복구 시작점은 redo 레코드 | https://www.postgresql.org/docs/17/wal-configuration.html | "the point in the WAL (known as the redo record) from which it should start the REDO operation" || ✅ |
| 14 | 55 | Spanner commit wait 기대 대기 | https://static.googleusercontent.com/media/research.google.com/en//archive/spanner-osdi2012.pdf | "the expected wait is at least 2 ∗ ε" || ✅ — PDF 텍스트 추출에서 ε 글자만 빠짐, 문장 일치. 55 정답 4 "≥ 2ε" |
| 15 | 09 | 복합 인덱스 규칙 | https://www.postgresql.org/docs/17/indexes-multicolumn.html | "equality constraints on leading columns, plus any inequality constraints on the first column…" || ✅ |
| 16 | 11 | hash_mem_multiplier 기본 2.0 | https://www.postgresql.org/docs/17/runtime-config-resource.html | "The default value is 2.0" || ✅ |
| 17 | 39 | PG 해시 인덱스는 4바이트 해시만 | https://www.postgresql.org/docs/17/hash-index.html | "Each hash index tuple stores just the 4-byte hash value" || ✅ |
| 18 | 40 | 트라이그램 없는 패턴은 전체 인덱스 스캔 | https://www.postgresql.org/docs/17/pgtrgm.html | "a pattern with no extractable trigrams will degenerate to a full-index scan" || ✅ |
| 19 | 45 | parts_to_throw_insert 23.6 전 300 | https://raw.githubusercontent.com/ClickHouse/ClickHouse/26.8/src/Storages/MergeTree/MergeTreeSettings.cpp | "Prior to version 23.6 this setting was set to 300." || ✅ |
| 20 | 46 | GIN은 가중치 미저장 | https://www.postgresql.org/docs/17/textsearch-indexes.html | "GIN indexes store only the words (lexemes) of tsvector values, and not their weight labels." || ✅ |
| 21 | 48 | NOTIFY는 커밋 시에만 전달 | https://www.postgresql.org/docs/17/sql-notify.html | "the notify events are not delivered until and unless the transaction is committed" || ✅ |
| 22 | 49 | Pub/Sub at-most-once | https://redis.io/docs/latest/develop/pubsub/ | "Redis' Pub/Sub exhibits at-most-once message delivery semantics." || ✅ |
| 23 | 56 | MySQL 1205 SQLSTATE HY000 | https://dev.mysql.com/doc/mysql-errors/8.4/en/server-error-reference.html | "Error number: 1205; Symbol: ER_LOCK_WAIT_TIMEOUT; SQLSTATE: HY000" || ✅ (WebFetch) — 56은 서버 HY000 / Connector/J 40001 구분, 22 정답 5에 같은 구분 추가 |
| 24 | 56 | Spring 6.0+ 기본 번역기 | https://github.com/spring-projects/spring-framework/blob/6.2.x/spring-jdbc/src/main/java/org/springframework/jdbc/support/SQLExceptionSubclassTranslator.java | "This translator serves as the default JDBC exception translator as of 6.0." || ✅ — 14·15의 Spring 매핑을 이 기본 경로로 맞춤 |
| 25 | 57 | GitLab 약 300GB 삭제 | https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/ | "around 300 GB of data had already been removed" || ✅ — 20 유실 구간을 57과 같게(00:00 / 23:30 병기) 수정 |
| 26 | 57 | GitHub 954건 | https://github.blog/2018-10-30-oct21-post-incident-analysis/ | "one of our busiest clusters had 954 writes in the affected window" || ✅ |
| 27 | 54 | 실행기는 demand-pull | https://www.postgresql.org/docs/17/executor.html | "This is essentially a demand-pull pipeline mechanism." || ✅ |
