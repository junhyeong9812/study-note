# database/16-mvcc — 질문

## 질문

1. (왜) MVCC가 없으면 긴 보고서 쿼리와 이체가 어떻게 서로를 막나? MVCC는 무엇을 막지 않게 하고, 무엇은 여전히 막나?
2. (그림) PostgreSQL 17과 MySQL 8.4 InnoDB는 옛 버전을 각각 어디에 두나? 한 행을 한 번 UPDATE한 뒤의 모습을 두 엔진에 대해 그려라(PostgreSQL은 xmin·xmax·t_ctid, InnoDB는 DB_TRX_ID·DB_ROLL_PTR).
3. (계산) PostgreSQL 스냅샷이 `100:105:101,103`이다. XID 99, 101, 102, 104, 105가 만든 버전은 각각 보이나? (102는 커밋, 104는 중단됐다고 하자.)
4. (예측) REPEATABLE READ의 T1이 `bal=200`을 읽은 뒤, T2가 같은 행에 +50을 커밋했다. 이어서 T1이 `UPDATE ... SET bal = bal + 1`을 하면 PostgreSQL 17과 MySQL 8.4에서 각각 어떻게 되나? MySQL 쪽에서 lost update가 생기는 코드 모양은?
5. (경계) 일반 `VACUUM`과 `VACUUM FULL`은 무엇이 다른가? 일반 `VACUUM`을 돌렸는데 테이블 파일 크기가 그대로인 것은 정상인가?
6. (장애 진단) `VACUUM VERBOSE`가 `10000 are dead but not yet removable`을 출력한다. 무엇이 cutoff를 붙잡고 있을 수 있나? 확인 쿼리와 재발 방지책을 대라.
7. (연결) HOT 갱신이 되려면 어떤 두 조건이 필요한가? HOT가 인덱스 bloat와 vacuum 부담을 줄이는 이유는?
8. (장애 진단) PostgreSQL이 `database is not accepting commands that assign new transaction IDs to avoid wraparound data loss`를 낸다. 왜 이런 제한이 있나(XID 크기와 비교 방식)? 문서가 권하는 복구 순서와 하지 말아야 할 것은?
9. (장애 진단) MySQL에서 `History list length`가 계속 오른다. 무엇을 뜻하며, 어떤 작업이 흔한 원인이고, 어떻게 확인·해소하나?
10. (연결) MVCC의 "옛 버전을 볼 수 있는 스냅샷이 하나라도 있으면 못 지운다"는 규칙이, 앱 코드의 트랜잭션 범위 설계에 주는 교훈은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
