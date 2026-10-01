# database/32-replication-leader-follower — 질문

## 질문

1. (왜) 복제는 어떤 문제 두 가지를 풀고, 어떤 문제는 풀지 못하나? 팔로워를 늘려도 쓰기 용량이 그대로인 이유는?
2. (경계) PostgreSQL 물리 스트리밍 복제와 MySQL binlog(ROW) 복제는 "무엇을" 보내나? 각각의 장단점 하나씩과, ROW 형식이 문장 형식보다 복제에 안전한 이유는?
3. (예측) PostgreSQL 17에서 `synchronous_standby_names = 's1'`, `synchronous_commit`을 `remote_write`·`on`·`remote_apply`로 바꿔 가며 커밋한다. 각각 커밋 응답은 무엇을 기다린 뒤 오나? 어느 설정에서 "커밋 직후 s1에서 조회하면 반드시 보인다"가 성립하나?
4. (경계) MySQL 8.4 준동기 복제에서 `AFTER_SYNC`와 `AFTER_COMMIT`의 차이는? 응답이 10초 넘게 안 오면 어떻게 되고, 그때 유실 보장은 어떻게 바뀌나?
5. (장애 진단) 사용자가 "글을 쓰고 목록에 가면 내 글이 없다"고 한다. 무엇을 먼저 확인하고, PostgreSQL·MySQL 각각에서 어떤 지표를 보며, 코드로는 어떻게 고치나?
6. (연결) read-your-writes·monotonic reads·consistent prefix reads를 각각 한 줄 예로 설명하고, 각각을 지키는 방법을 하나씩 대라.
7. (예측) 비동기 복제에서 리더가 커밋 5까지 응답했고 팔로워는 3까지 받은 상태에서 리더가 죽었다. 팔로워를 승격한 뒤 무슨 일이 생기나? 옛 리더가 살아 돌아오면 PostgreSQL에서는 어떻게 다시 붙이나?
8. (장애 진단) 팔로워에서 돌던 30분짜리 리포트가 `ERROR: canceling statement due to conflict with recovery`로 실패한다. SQLSTATE는? 원인과 세 가지 대처, 각 대처의 대가는?
9. (장애 진단) 팔로워 한 대를 점검하려고 내렸더니 (a) 리더의 모든 커밋이 멈췄다 / (b) 며칠 뒤 리더 디스크가 가득 찼다. 각각 어떤 설정 때문이고 어떻게 예방하나?
10. (연결) GitHub 2012-09-11 사고에서 뒤처진 노드가 리더가 된 뒤 데이터 유실 말고 어떤 피해가 났나? 페일오버 설계에서 이 사고가 주는 교훈 두 가지는?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
