# database/14-isolation-levels-and-anomalies — 질문

## 질문

1. (그림) 갱신 손실(P4)과 write skew(A5B)를 각각 `r1[x] … w2[x] …` 표기로 쓰고, 두 세션 시간축으로 그려라. 둘을 가르는 결정적 차이는 무엇인가?
2. (왜) SQL 표준은 격리 수준을 "무엇을 금지하나"로 정의한다. 이 정의 방식 때문에 생기는 일 두 가지(제품 차이, Berenson 외의 비판)를 말하라. 모든 수준에서 금지해야 한다고 Berenson 외가 말한 현상은?
3. (예측) 재고 10에서 두 세션이 각각 `SELECT qty` → 애플리케이션에서 `qty - 1` 계산 → `UPDATE … SET qty = 9`를 겹쳐 실행한다. PostgreSQL 17 RC, PostgreSQL 17 RR, MySQL 8.4 RR, MySQL 8.4 SERIALIZABLE에서 각각 어떻게 되나?
4. (예측) 당직 2명 테이블에서 두 세션이 각각 `count(*)`로 2명을 확인하고 자기 행을 off로 바꾼다. PostgreSQL 17의 RR과 SERIALIZABLE에서 결과와 오류 메시지는? MySQL 8.4 SERIALIZABLE에서는 어떤 오류로 드러나며, 왜 그 오류인가?
5. (경계) "PostgreSQL REPEATABLE READ = 스냅샷 격리"와 "락 기반 REPEATABLE READ"는 서로 무엇을 막고 무엇을 허용하나? Berenson 외가 둘을 "비교 불가"라고 한 근거는?
6. (연결) PostgreSQL SSI는 매번 의존 그래프 전체의 사이클을 찾지 않는다. 대신 무엇을 찾나? 그 방식의 대가(부작용)는? `SIReadLock`은 다른 트랜잭션을 막나?
7. (장애 진단) MySQL 8.4 기본 격리 수준 트랜잭션에서 `SELECT count(*) … WHERE id >= 2`는 1인데, 이어서 같은 조건의 `UPDATE`가 2행을 바꿨다. 무엇이 일어났고 어떻게 고치나?
8. (설계) "두 계좌 잔액 합 ≥ 0"을 지키는 출금 로직이 동시 요청에 깨진다. 격리 수준을 올리지 않고 고치는 방법 두 가지와, SERIALIZABLE로 고칠 때 반드시 함께 해야 하는 것은?
9. (장애 진단) 정합성 문제 때문에 PostgreSQL 전체를 SERIALIZABLE로 올렸더니 `could not serialize access due to read/write dependencies among transactions`가 폭증했다. SQLSTATE는? 원인 후보와 줄이는 방법은?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
