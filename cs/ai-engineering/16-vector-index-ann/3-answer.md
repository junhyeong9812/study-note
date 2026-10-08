# ai-engineering/16-vector-index-ann — 정답

## 정답

### 1. 결과가 바뀌는 인덱스

- B-tree는 정확 인덱스다. 조건에 맞는 행을 빠짐없이 찾으므로 인덱스 유무와 관계없이 결과가 같다.
- HNSW·IVFFlat은 근사 최근접(ANN) 인덱스다. 후보 일부만 보고 top-k를 고르므로 정답 일부를 놓칠 수 있다.
  - pgvector README: 기본은 정확 탐색(완전 recall), 근사 인덱스를 추가하면 질의 결과가 달라진다.
- `recall@k = |근사 top-k ∩ 정확 top-k| / k`. 실험 1에서 HNSW 기본값(ef_search 40)의 recall@10은 0.923이었다(다시 구축하면 0.926·0.928). 10개 중 평균 0.7~0.8개가 다른 문서로 바뀐다.

### 2. 세 방식의 그림

```text
  전수:     모든 행 거리 계산 → top-k 힙 → k개
  IVFFlat:  [구축] k-평균 중심 lists개, 행은 가장 가까운 중심의 목록에
            [질의] 가까운 중심 probes개 → 그 목록들만 전수 계산 → k개
  HNSW:     [구축] 원소마다 최대 층을 지수 감소 확률로, 이웃 최대 m개(층 0은 2m),
                   이웃을 고를 때 후보 ef_construction개
            [질의] 맨 위층 진입점 → 탐욕 이동 → 한 층씩 내려감 → 층 0에서 후보 ef_search개 → 상위 k개
```

- `lists`는 서가 수, `probes`는 볼 서가 수다.
- `m`은 노드당 간선 수 상한(pgvector 0.8.7 소스 기준 층 0은 2m), `ef_construction`은 구축 때 후보 폭, `ef_search`는 질의 때 후보 폭이다(README).

### 3. ef_search를 올리면

(실험 1, PostgreSQL 17.11 + pgvector 0.8.7)

```text
  ef_search 10  → recall 0.763, p50 0.36ms
  ef_search 40  → recall 0.923, p50 0.94ms
  ef_search 400 → recall 0.983, p50 8.47ms
  ef_search 5, LIMIT 10 → 5행, recall 0.396
```

- recall과 지연이 함께 오른다. 전수 탐색(p50 약 24ms, recall 1.0)에 가까워지는 방향이다.
- `ef_search = 5`면 후보 목록이 5칸이라 `LIMIT 10`이어도 5행만 온다. README Troubleshooting: 결과는 `hnsw.ef_search` 크기로 제한된다.

### 4. 선택도 10% 필터

- 필터는 인덱스 탐색 **뒤에** 적용된다. 후보 40개 × 10% = 평균 4행(README의 예와 같다).
- 실험 2 실측: 평균 4.26행, recall 0.422(점검 재실행 4.21행, 0.415).
- `EXPLAIN ANALYZE` 한 질의: `rows=2`, `Filter: (cat = 3)`, `Rows Removed by Filter: 38` — 후보 40개 중 38개가 필터로 빠졌다.
- 채우는 방법
  1. 반복 인덱스 스캔(0.8.0+): `SET LOCAL hnsw.iterative_scan = strict_order | relaxed_order`. 실험에서 10행을 채웠고 recall 0.767(strict)·0.814(relaxed), 대신 p95가 6.20ms·4.94ms로 늘었다.
  2. `ef_search` 상향: 100이면 평균 9.02행.
  3. 값 종류가 적으면 부분 인덱스(`WHERE (cat = 3)`), 많으면 파티션. 선택도가 아주 낮으면 필터 열 B-tree + 정확 탐색.

### 5. probes = lists

- 모든 목록을 본다 = 전수 탐색과 같은 결과다. 실험에서 recall 1.000.
- README: 이 경우 플래너는 인덱스를 쓰지 않는다. 새로 만든 계획의 `EXPLAIN`이 `Seq Scan` + `Sort`였다.
- 지연(p50 35ms)은 전수 탐색(24ms)보다 짧아지지 않았다. 계획이 같은 `Seq Scan`이라 차이는 측정 잡음이다(점검 재실행 25.9ms vs 29.5ms). 정확도가 필요하면 인덱스 없이 전수 탐색을 쓰는 편이 단순하다.

### 6. 빈 테이블에 IVFFlat

- 신호: `NOTICE: ivfflat index created with little data` / `DETAIL: This will cause low recall.` / `HINT: Drop the index until the table has more data.` 오류가 아니라 알림 한 줄이다.
- 실험 3(probes 7): 적재 후 생성 0.794, 500행일 때 생성 0.562, 빈 테이블 생성 0.404(점검 재실행 0.431 — 구축마다 조금 다르다).
- 이유: IVFFlat은 생성 시점 데이터로 k-평균 중심을 정한다. 데이터가 없으면 중심이 실제 분포와 무관하다.
- HNSW는 학습 단계가 없어 빈 테이블에도 만들 수 있다(README). 행이 들어올 때마다 그래프에 끼워 넣는다.
- 대처: 적재 뒤 `REINDEX` 또는 재생성.

### 7. 인덱스를 안 쓰는 ORDER BY

- `EXPLAIN`에 `Seq Scan` → `Sort`가 보인다(인덱스 스캔 없음).
- README: 인덱스를 쓰려면 `ORDER BY`가 거리 연산자 결과의 **오름차순**이고 `LIMIT`이 있어야 한다. `1 - 거리`는 식이라 인덱스 순서와 맞지 않는다.
- 고침: `ORDER BY embedding <=> $1 LIMIT 10`으로 쓰고, 유사도가 필요하면 SELECT 목록에서 `1 - (embedding <=> $1)`을 계산한다.

### 8. 공유 인덱스와 테넌트

- README "Multitenancy": 근사 인덱스를 테넌트끼리 공유하면 한 테넌트의 벡터가 다른 테넌트의 recall과 속도에 영향을 준다.
- 모양은 4번 필터 문제와 같다. `tenant_id` 필터가 후보 목록 뒤에 적용되는데, 후보를 큰 테넌트의 벡터가 차지한다(해석).
- 격리: 테넌트별 리스트 파티션(`PARTITION BY LIST(customer_id)`) 또는 테이블 분리(README).

### 9. 닮은 자료구조

- `top-N heapsort` = 크기 k의 힙으로 상위 k만 남긴다([data-structure/07-heap](../../data-structure/07-heap/2-summary.md)).
- HNSW 층 배정 = 지수 감소 확률로 높이를 정하는 스킵 리스트([data-structure/12-skip-list](../../data-structure/12-skip-list/2-summary.md)). 논문 초록도 스킵 리스트와 비슷하다고 적는다.
- IVFFlat 목록 = "중심 → 벡터 목록". "용어 → 문서 목록"인 역색인과 같은 꼴이다([data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)).

### 10. 운영 recall 감시

- README "Monitoring": 근사 결과와 정확 결과를 비교해 recall을 감시한다.
- 절차
  1. 고정 표본 질의 세트를 둔다.
  2. 근사 top-k: 평소 설정으로 실행.
  3. 정확 top-k: 트랜잭션 안 `SET LOCAL enable_indexscan = off`로 실행.
  4. `|교집합| / k`를 지표로 보내고 추세를 본다.
- 주의
  - `SET LOCAL`로 그 트랜잭션에만 적용한다. 세션 `SET`은 커넥션 풀을 타고 다른 요청에 새어 나간다(해석).
  - 같은 세션에서 PL/pgSQL 함수가 이미 만든 계획은 설정을 바꿔도 재사용될 수 있다. 실험에서 `enable_indexscan = off` 뒤에도 recall이 0.926(근사)이었고, 새 세션에서야 1.000이 나왔다.
  - 정확 탐색은 질의당 수십 ms라 표본에만 돌린다.
