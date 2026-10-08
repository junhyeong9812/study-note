# ai-engineering/18-index-freshness-and-reembedding — 정답

## 정답

### 1. 파생 데이터

- 벡터 인덱스는 원천 문서를 청킹·임베딩해 계산한 사본이다. 원천만 있으면 지우고 다시 만들 수 있다([data-engineering/01](../../data-engineering/01-system-of-record-and-derived-data/2-summary.md)).
- 수정이 전파되지 않으면: 옛 청크가 검색돼 옛 규정으로 답한다.
- 삭제가 전파되지 않으면: 지운 내용(개인정보 포함)이 인용된다. 출처 ID가 원천에 없는 문서를 가리킨다.
- RAG에서는 인덱스가 곧 비파라미터 지식이라, 인덱스 신선도가 답의 신선도다(해석).

### 2. 다른 모델, 다른 공간

(실험 1, Python 3.12.3)

```text
같은 문서의 A 벡터와 B 벡터 코사인 평균: 0.002
진행률 0.25, 질의 = B → recall@10 0.25 (상위 10 중 옛 A 벡터 평균 0.8개)
```

- 코사인은 거의 0이다. 같은 뜻이어도 공간이 달라 서로 무관한 방향이다.
- 질의가 B 공간에 있으니 A로 남은 75%는 거의 검색되지 않는다. recall이 진행률을 따라간다(25%·50%·75% → 0.25·0.48·0.67, 다 바꾸면 0.82).

### 3. 차원이 다를 때 vs 같을 때

- 다르면: `ERROR: different vector dimensions 4 and 3`. 질의가 실패한다. 크게 실패해 빨리 드러난다.
- 같으면: 오류 없이 거리가 계산된다. 실험 2에서 m1 행과 m2 행이 한 결과에 섞여 나왔다. 값만 무의미하다.
- 같은 쪽이 더 위험하다. 로그·오류율에 아무 신호가 없고 검색 품질만 떨어진다.

### 4. 버전 필터는 recall을 못 살린다

- 실험 1에서 `version = 'B'만` 열은 섞인 인덱스 열과 같은 값이다(진행률 25%·50%·75%에서 둘 다 0.25·0.48·0.67).
- 필터는 다른 공간의 벡터를 빼 줄 뿐, 아직 B로 안 바뀐 문서를 채우지 못한다.
- 지키는 방법: B 색인을 전부 채울 때까지 질의는 A 전체 인덱스로(recall 0.81), 다 채운 뒤 한 번에 B로 전환(0.82).

### 5. 이중 색인 후 전환

```text
  0 운영 m1  →  1 m2 전체 백필 + 새 변경은 m1·m2 이중 쓰기  →  2 m2 검증(행 수·평가셋)
    →  3 전환: current_model = m2 (질의 임베딩 모델 + 검색 필터 동시)  →  4 m1 삭제
```

- 동시에 바꿀 두 값: 질의를 임베딩하는 모델, 검색 대상 벡터의 모델(필터·인덱스).
- 따로 바꾸면 그 사이에 질의 = m2, 대상 = m1인 구간이 생긴다. 실험 1의 "진행률 0%에서 질의만 B" = recall 0.00이 그 상태다.
- 두 값을 같은 설정 하나에서 읽게 하면 전환이 한 번의 값 변경이 된다. [database/48](../../database/48-search-index-sync-and-reindexing/2-summary.md)의 별칭 원자 교체와 같은 모양이다.
- 단, 한 요청 안에서 설정을 두 번 읽으면(임베딩 전·검색 전) 그 사이 전환으로 질의 = m1, 대상 = m2가 될 수 있다. 요청 시작에 모델 버전을 한 번 읽어 고정하고 임베딩·검색에 같이 넘긴다(해석).

### 6. 재실행 중복

- 원인: 키 없는 INSERT. 실험 2에서 청크 400개 배치를 두 번 돌리자 800행(서로 다른 청크는 400)이 됐다.
- 방법 1: `(doc_id, chunk_no, model)` 기본 키 + `ON CONFLICT … DO UPDATE … WHERE 해시가 다를 때만`. 두 번째 실행은 `INSERT 0 0`, 400행 유지.
- 방법 2: 문서 단위로 그 문서·모델의 청크를 DELETE한 뒤 INSERT를 한 트랜잭션으로. 몇 번을 돌려도 마지막 상태가 같다.

### 7. 줄어든 청크

- 청크 0~2만 upsert되고 옛 청크 3·4가 남는다. 옛 내용이 계속 검색된다.
- 고침: 문서 단위 통째 교체(DELETE + INSERT 한 트랜잭션 — 적용 3의 워커). 파티션 덮어쓰기([data-engineering/08](../../data-engineering/08-idempotent-pipelines-and-backfill/2-summary.md))와 같은 방식이다.
- 같은 모델의 행이 이미 있고 내용 해시가 같은 청크는 임베딩 호출을 건너뛰어 비용을 줄인다. 모델 교체 때는 해시가 같아도 새 벡터가 필요하다.

### 8. 삭제 전파

- 같은 DB: 청크 테이블에 원천 외래 키 + `ON DELETE CASCADE`. 실험 2에서 남은 청크 4 → 0.
- 다른 저장소: outbox·CDC로 삭제 이벤트를 전파하고, 주기적으로 고아를 찾는다(`NOT EXISTS (원천)` — 실험 2에서 4건 탐지).
- 출처 검증 단계([15번](../15-rag-pipeline/2-summary.md))에서 인용 문서가 원천에 있는지 한 번 더 확인한다.
- 벡터 행 삭제로 끝나지 않는 이유: 백업·로그·분석 사본·평가셋 등 다른 복제본이 있다([data-engineering/12](../../data-engineering/12-data-retention-and-erasure/2-summary.md)). 물리 제거는 VACUUM 뒤이고, pgvector README는 HNSW VACUUM이 오래 걸릴 수 있다고 적는다.

### 9. 신선도 지표

- 잴 것: 원천 `updated_at`과 인덱스 `indexed_at`의 차이(반영 안 된 문서 수·최대 지연), 고아 청크 수, 모델별 청크 수(교체 진행률·혼재 여부).
- 진단 질의
  1. `docs LEFT JOIN (doc_id별 min(indexed_at))` → `indexed_at IS NULL OR indexed_at < updated_at`인 문서 수와 `max(now() - updated_at)`. `max`로 모으면 새 청크가 남은 옛 청크를 가려 7번의 문서를 놓친다(적용 2 점검 실험).
  2. `chunk_emb e WHERE NOT EXISTS (SELECT 1 FROM docs d WHERE d.doc_id = e.doc_id)`.
  3. `SELECT model, count(*) FROM chunk_emb GROUP BY model`.
- 지연은 목표를 정해(예시: 15분) 넘으면 경보한다. 이벤트 유실에 대비해 주기적 전수 대조를 둔다.
