# database/06-pages-and-tuple-layout — 질문

## 질문

1. (왜) DB는 왜 행을 파일에 그냥 이어 쓰지 않고 고정 크기 페이지 + 슬롯 배열로 담나? 슬롯 배열이 없으면 무엇이 곤란한가?
2. (그림) PostgreSQL 8KB 힙 페이지에 행 3개를 넣은 직후를 그려라. 헤더·슬롯·빈 공간·행의 위치와 `pd_lower`·`pd_upper`가 어디를 가리키는지 표시하라. 슬롯이 3개면 `pd_lower`는 몇인가?
3. (예측) PostgreSQL에서 `UPDATE t SET name = 'bobby' WHERE id = 2`를 실행하면 페이지 안에서 무엇이 바뀌나? 옛 튜플의 `t_xmax`·`t_ctid`, 새 튜플의 슬롯 번호를 예측하라. 같은 UPDATE가 MySQL InnoDB에서는 어떻게 저장되나?
4. (경계) HOT 갱신은 언제 가능하고 언제 불가능한가? `fillfactor`를 낮추면 왜 도움이 되나?
5. (예측) `(a bool, b bigint, c bool, d bigint)`와 `(b bigint, d bigint, a bool, c bool)`는 같은 값을 담는다. PostgreSQL에서 행 길이는 각각 몇 바이트쯤이고, 왜 다른가?
6. (경계) PostgreSQL `text` 칼럼에 10,000바이트짜리 `'aaaa…'`와 9,600바이트짜리 무작위 16진 문자열을 넣었다. 각각 행 안에 남나, TOAST 테이블로 가나? 판단 기준은?
7. (연결) InnoDB는 한 페이지에 안 들어가는 행을 어떻게 처리하나? `CHAR(255) latin1` 칼럼 40개짜리 테이블을 만들면 무슨 일이 생기고, 왜 `TEXT`로 바꾸면 되나?
8. (장애 진단) 1만 행 테이블을 잔액 칼럼만 5번 전체 UPDATE했더니 파일이 약 6배가 됐다. 원인과, `VACUUM`을 돌린 뒤 파일 크기가 어떻게 되는지, 크기를 되돌리는 방법과 그 대가를 설명하라.
9. (장애 진단) 칼럼 하나(`char(500)`)를 추가한 배포 뒤, 행 수는 같은데 `sum(v)` 풀 스캔 리포트가 느려졌다. `EXPLAIN (ANALYZE, BUFFERS)`에서 무엇이 달라져 있을 것이고, 어떻게 고치나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
