# data-engineering/05-change-data-capture — 질문

## 질문

1. (왜) `updated_at > :last_seen` 폴링으로 파생 저장소를 맞추면 무엇을 놓치나? 로그 기반 CDC는 그중 무엇을 해결하나?
2. (그림) PostgreSQL 17에서 커밋 → WAL → 논리 디코딩 → 슬롯 → 커넥터 → 토픽 흐름을 그리고, 슬롯이 기억하는 두 위치(`restart_lsn`, `confirmed_flush_lsn`)의 뜻을 적어라.
3. (예측) `REPLICA IDENTITY DEFAULT`인 테이블에서 `UPDATE`, `DELETE`, 롤백한 `INSERT`, `ALTER TABLE ... ADD COLUMN`을 차례로 실행하고 `test_decoding` 슬롯에서 변경을 읽으면 각각 어떻게 나오나? `FULL`로 바꾸면 무엇이 달라지나?
4. (예측) 테이블에 1~5가 있다. (B1) 스냅샷 SELECT → INSERT 6 → 슬롯 생성 → INSERT 7, (B2) 슬롯 생성 → INSERT 6 → 스냅샷 SELECT → INSERT 7 순서로 하면 스냅샷과 스트림에 각각 무엇이 들어오나? 둘 다 피하는 방법은?
5. (경계) Debezium 증분 스냅샷은 스트리밍을 멈추지 않고 테이블을 다시 읽는다. 창 열기·닫기 신호와 버퍼가 무엇을 막나? 소비자가 초기 스냅샷 때와 다르게 각오해야 할 점은?
6. (예측) 연결된 소비자가 없는 논리 슬롯을 만든 뒤 WAL을 약 150 MB 만들고 `CHECKPOINT`를 하면 `pg_wal` 크기와 `wal_status`는? `max_slot_wal_keep_size=32MB`를 걸고 같은 일을 하면?
7. (연결) PostgreSQL 슬롯과 MySQL binlog 보존은 커넥터가 오래 멈췄을 때 서로 반대 방향으로 깨진다. 각각 어떻게 깨지고, 공통 복구 수단은 무엇인가?
8. (장애 진단) 웨어하우스의 회원 수가 원천보다 꾸준히 많고 차이가 매주 커진다. 파이프라인은 초록이다. CDC 쪽에서 의심할 원인 두 가지와 확인 방법은?
9. (장애 진단) 운영 PostgreSQL 디스크 경보가 울렸다. 어떤 쿼리로 무엇을 보고, 원인이 버려진 슬롯이면 어떻게 정리하고 재발을 막나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
