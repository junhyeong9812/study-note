# database/26-schema-migration — 질문

## 질문

1. (왜) 스키마 변경을 "한 번의 ALTER"로 하면 안 되는 이유 세 가지(DB 안·앱 쪽·데이터)는 무엇인가?
2. (예측) PostgreSQL에서 세션 A가 `BEGIN; SELECT count(*) FROM t;` 후 커밋하지 않고 있다. 세션 B가 `ALTER TABLE t ADD COLUMN c int;`를 실행하고, 이어서 세션 C가 `SELECT * FROM t LIMIT 1;`을 실행한다. B와 C는 각각 어떻게 되나? `ALTER`가 수 ms짜리 작업인데도 왜 그런가?
3. (경계) PostgreSQL 17에서 다음 중 테이블을 재작성하는 것은? (a) `ADD COLUMN e int NOT NULL DEFAULT 0` (b) `ADD COLUMN f timestamptz DEFAULT clock_timestamp()` (c) `ALTER COLUMN c TYPE bigint`(int에서) (d) `ALTER COLUMN name TYPE varchar(100)`(varchar(50)에서). 재작성 여부를 스테이징에서 어떻게 확인하나?
4. (설계) 큰 테이블의 `email` 컬럼에 NOT NULL을 걸고 싶다. 기존 NULL 행이 있다. PostgreSQL 17에서 긴 락 없이 끝내는 순서를 써라.
5. (연결) `name` → `full_name` rename을 expand/contract로 할 때, 각 단계에서 어떤 코드 버전이 살아 있고 어느 단계부터 롤백이 불가능한가? 규칙을 한 문장으로.
6. (예측) `BEGIN; INSERT ...; ALTER TABLE r ADD COLUMN x int; ROLLBACK;`을 PostgreSQL 17과 MySQL 8.4에서 각각 실행하면 결과는? 이것이 마이그레이션 도구 사용에 주는 함의는?
7. (장애 진단) MySQL 8.4에서 `ALTER TABLE ... ALGORITHM=INSTANT` 배포 직후 API가 멈췄다. `SHOW PROCESSLIST`에 `Waiting for table metadata lock`이 수십 줄이다. 원인, 즉시 조치, 재발 방지는? INSTANT인데 왜 막혔나?
8. (장애 진단) 백필을 시작하자 복제본 기반 화면에서 "방금 저장한 게 안 보인다"는 문의가 온다. 어떤 지표를 보고, 원인은 무엇이며, 백필을 어떻게 바꾸나?
9. (장애 진단) `CREATE UNIQUE INDEX CONCURRENTLY`가 실패했다. 테이블에 무엇이 남고, 그것이 왜 문제이며, 어떻게 정리하나?
10. (경계) MySQL에서 `SET SESSION lock_wait_timeout = 1`로 `ALTER`를 실행해 `ERROR 1205`를 받았다. 이 1205는 `innodb_lock_wait_timeout`의 1205와 무엇이 다른가? 두 변수의 8.4 기본값은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
