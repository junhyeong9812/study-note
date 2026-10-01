# database/03-normalization — 질문

## 질문

1. (왜) `orders_flat(order_id, customer_id, customer_email, amount)`에서 생기는 갱신·삽입·삭제 이상을 하나씩 예로 들어라. 원인이 되는 함수 종속은 무엇인가?
2. (계산) R = (A, B, C, G, H, I), F = {A→B, A→C, CG→H, CG→I, B→H}. (AG)+를 단계별로 구하라. AG는 슈퍼키인가, 후보 키인가? 판정 근거는?
3. (경계) 2NF·3NF·BCNF를 각각 한 줄로 정의하고, 각 단계를 어기는 테이블 예를 하나씩 들어라.
4. (설계) `orders_flat`을 BCNF로 분해하라. 그 분해가 손실 없는 이유를 조건식으로 설명하라. 잘못 분해하면 무엇이 생기나?
5. (경계) `dept_advisor(s_ID, i_ID, dept_name)`, F = {i_ID → dept_name, (s_ID, dept_name) → i_ID}. 이 테이블은 BCNF인가, 3NF인가? BCNF로 쪼개면 무엇을 잃나?
6. (연결) 반정규화를 할 때 Silberschatz가 드는 두 선택지와 각각의 비용은? 주문 상세에 `unit_price`를 두는 것은 반정규화인가?
7. (장애 진단) 운영 DB에서 "한 고객의 이메일이 주문마다 다르다"는 제보가 왔다. 전체 규모를 파악하는 쿼리, 원인, 근본 대처를 써라.
8. (장애 진단) 목록 API 하나가 테이블 12개를 조인하고 응답 시간이 들쭉날쭉하다. PostgreSQL에서 어떤 설정과 계획 신호를 확인하나? 설계 쪽 대처는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
