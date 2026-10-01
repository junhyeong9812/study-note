# database/42-recovery-aries-checkpoints — 질문

## 질문

1. (왜) STEAL과 NO-FORCE는 각각 무엇이고, 각각이 복구에 어떤 단계를 필요하게 만드나? 둘 다 허용하는 이유는?
2. (경계) pageLSN·prevLSN·recLSN·flushedLSN은 각각 어디에 저장되고 무엇에 쓰이나? 페이지를 디스크에 쓰기 전에 반드시 성립해야 하는 부등식은?
3. (계산) 다음 로그에서 크래시가 났다. 분석 단계가 끝났을 때의 ATT·DPT, 재실행 시작 LSN, 취소할 트랜잭션과 쓰게 될 CLR(undoNextLSN 포함)을 적어라.
   `10 T1 BEGIN · 20 T1 UPDATE P1 · 30 T2 UPDATE P2 · 40 CKPT-BEGIN · 50 CKPT-END ATT={T1:20,T2:30} DPT={P1:20,P2:30} · 60 T1 UPDATE P3(prev 20) · 70 T2 COMMIT · 80 T1 UPDATE P1(prev 60)`
4. (왜) 재실행 단계는 결국 취소될 T1의 변경까지 왜 다시 적용하나? 재실행 중 어떤 레코드를 건너뛰나(세 조건)?
5. (예측) 3번의 취소 단계에서 CLR 100을 쓴 직후 서버가 다시 죽었다. 재시작하면 무엇을 다시 하고, 무엇을 하지 않나?
6. (연결) PostgreSQL 17에는 왜 ARIES식 취소 단계가 없나? `ROLLBACK`의 WAL에는 무엇이 남나? InnoDB는 어떻게 다른가?
7. (경계) 퍼지 체크포인트와 블로킹 체크포인트의 차이는? PostgreSQL의 `CHECKPOINT_ONLINE` 레코드가 자기보다 앞의 redo 위치를 가리키는 이유는?
8. (장애 진단) PostgreSQL이 재시작 후 20분째 `the database system is in recovery mode`로 접속을 거부한다. 원인 후보, 평소에 봤어야 할 지표, 설정 조정 방향과 그 대가를 말하라.
9. (장애 진단) 서버 로그에 `checkpoints are occurring too frequently (9 seconds apart)`가 반복된다. 무엇이 일어나고 있고 WAL 양은 왜 더 늘어나나? MySQL에서 대응되는 증상은?
10. (예측) MySQL 8.4에서 1시간 돌던 대량 `UPDATE` 도중 mysqld가 죽었다. 재시작 뒤 접속은 금방 되는데 그 테이블 갱신이 오래 막힌다. 왜 그런가, 얼마나 걸릴 수 있나, 무엇으로 예방하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
