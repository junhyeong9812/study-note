# database/18-app-level-concurrency-patterns — 질문

## 질문

1. (왜) "확인하고 행동하기(check-then-act)"가 기본 격리 수준에서 깨지는 이유를 시간축으로 그려라. 이 틈을 막는 도구 네 가지는?
2. (예측) 재고 100, 8세션이 "`SELECT qty` → `qty > 0`이면 `UPDATE ... SET qty = qty - 1`"을 반복한다. 차감 자체는 원자적인데 왜 음수가 되나? 한 문장으로 고친 SQL과, 성공·품절을 판정하는 방법은?
3. (경계) PostgreSQL 17 READ COMMITTED에서 조건부 UPDATE(`WHERE qty > 0`)가 동시 요청에도 정확한 이유를 설명하라. 앞 트랜잭션이 롤백하면 어떻게 되나?
4. (연결) UNIQUE 제약이 있을 때 동시 check-then-insert에서 두 번째 INSERT는 어떤 과정을 거쳐 어떤 오류를 받나(PostgreSQL·MySQL·Spring)? 앱의 사전 `SELECT`는 그러면 왜 두나?
5. (그림) MySQL 8.4 REPEATABLE READ에서 두 세션이 없는 이메일을 `SELECT ... FOR UPDATE`로 확인한 뒤 INSERT한다. 어떤 락이 걸리고 왜 교착(1213)이 나는지 그려라. 올바른 해법은?
6. (경계) PostgreSQL `ON CONFLICT DO UPDATE`는 무엇을 보장하나? MySQL `ON DUPLICATE KEY UPDATE`의 영향 행 수 1·2·0은 각각 무슨 뜻이고, 어떤 테이블에서 쓰지 말라고 하나?
7. (장애 진단) 결제사 응답이 느려진 순간 주문 API 전체가 느려지고 커넥션 풀이 고갈됐다. `pg_stat_activity`에서 무엇이 보이고, 원인과 구조적 대처는?
8. (장애 진단) "INSERT 해 보고 23505면 기존 행을 SELECT"하는 코드가 MySQL에서는 되는데 PostgreSQL에서만 실패한다. 오류 메시지와 이유, 고치는 법은?
9. (설계) 다음 각각에 맞는 패턴을 고르고 이유를 대라: (a) 일별 조회수 누적 (b) 쿠폰 1인 1매 (c) 여러 규칙을 검사하는 계좌 출금 (d) 여러 워커가 나눠 가져가는 작업 큐.
10. (연결) 잠글 행이 아예 없는 경우(예: 회의실 예약이 겹치지 않게)에는 어떻게 동시성을 지키나? DDIA 7장의 해법을 대라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
