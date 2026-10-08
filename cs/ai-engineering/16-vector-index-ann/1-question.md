# ai-engineering/16-vector-index-ann — 질문

## 질문

1. (왜) pgvector 테이블에 HNSW 인덱스를 추가했더니 같은 질의의 상위 10건이 달라졌다. B-tree 인덱스를 추가할 때는 왜 이런 일이 없고, 벡터 인덱스에서는 왜 생기나? recall@k를 식으로 정의하라.
2. (그림) 전수 탐색·IVFFlat·HNSW가 질의 하나를 처리하는 방식을 각각 그려라. IVFFlat의 `lists`·`probes`, HNSW의 `m`·`ef_construction`·`ef_search`는 그림의 어디에 해당하나?
3. (예측) 5만×128차원 데이터에서 HNSW(m 16, ef_construction 64)의 `hnsw.ef_search`를 10 → 40 → 400으로 올리면 recall@10과 p50 지연은 어느 방향으로 움직이나? `ef_search = 5`에 `LIMIT 10`이면 몇 행이 오나? (실험 1로 확인)
4. (계산) `WHERE cat = 3`(행의 10%)을 건 `ORDER BY embedding <=> q LIMIT 10`을 HNSW 기본 설정으로 돌리면 평균 몇 행이 기대되나? 실험 2의 실측값과 `EXPLAIN ANALYZE`의 어느 줄이 이를 보여 주나? 행 수를 채우는 방법 세 가지는?
5. (경계) IVFFlat에서 `ivfflat.probes`를 `lists`와 같게 하면 무엇이 되나? 이때 플래너는 어떤 계획을 고르나?
6. (장애 진단) 마이그레이션이 빈 테이블에 IVFFlat 인덱스를 만들고 그 뒤에 데이터를 적재했다. 어떤 신호가 남고, recall은 얼마나 떨어졌나(실험 3)? 왜 HNSW에는 이 문제가 없나?
7. (장애 진단) 인덱스가 있는데 `ORDER BY 1 - (embedding <=> $1) DESC LIMIT 10` 질의가 수십 ms 걸린다. `EXPLAIN`에 무엇이 보이고, 어떻게 고치나?
8. (장애 진단) 여러 테넌트가 HNSW 인덱스 하나를 공유한다. 큰 테넌트가 대량 적재한 뒤 작은 테넌트의 결과가 짧아지고 느려졌다. 원인과 README가 권하는 격리 방법은?
9. (연결) 전수 탐색 계획의 `Sort Method: top-N heapsort`, HNSW의 층 배정, IVFFlat의 "목록"은 각각 어떤 자료구조와 닮았나?
10. (적용) 운영 중 recall이 떨어지는지 어떻게 알 수 있나? 표본 질의로 재는 절차와 그때 주의할 점(설정 범위·계획 캐시)을 말하라.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 |
|------|------|-----------|
