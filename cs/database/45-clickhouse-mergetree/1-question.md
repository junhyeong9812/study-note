# database/45-clickhouse-mergetree — 질문

## 질문

1. (왜) 분석용 테이블을 PostgreSQL 힙 + B-tree 대신 MergeTree에 두면 읽기와 쓰기에서 각각 무엇이 좋아지나? 대가로 무엇을 잃나?
2. (예측) `PARTITION BY toYYYYMM(ts)` 테이블에 9월 행 3개와 10월 행 7개를 담은 INSERT 한 번을 보낸다. 파트가 몇 개 생기나? 이름은 대략 어떤 꼴이고 레벨은 얼마인가?
3. (계산) 26.8 기본값에서 한 파티션의 활성 파트가 2000개다. 다음 INSERT는 어떻게 되나? 3001개면? 이 임계는 테이블 단위인가 파티션 단위인가?
4. (경계) `ORDER BY (tenant_id, metric, ts)` 테이블에 `WHERE metric = 'cpu'`만 건다. 그래뉼을 건너뛸 수 있나? 답이 tenant_id의 카디널리티에 따라 어떻게 달라지나?
5. (연결) PostgreSQL BRIN과 ClickHouse 희소 기본 인덱스는 무엇이 같고 무엇이 다른가? 로컬 재현에서 BRIN이 여분으로 읽은 행은 몇 개였나?
6. (장애 진단) 배치로 1만 행씩 넣는데도 `Too many parts`가 난다. `PARTITION BY (tenant_id, toDate(ts))`다. 무엇을 조회해 원인을 확정하고, 어떻게 고치나?
7. (경계) async insert를 켰다. `wait_for_async_insert`를 1로 두는 것과 0으로 두는 것은 에러가 드러나는 곳과 유실 가능성에서 어떻게 다른가? 26.8에서 두 설정의 기본값은?
8. (장애 진단) `ReplacingMergeTree`에서 같은 주문 ID가 두 번 집계된다. 누군가 매일 `OPTIMIZE TABLE orders FINAL` 크론을 제안한다. 무엇이 문제이고 대신 무엇을 하나?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
