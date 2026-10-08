# ai-engineering/16-vector-index-ann — 벡터 인덱스: 전수 탐색 vs HNSW·IVFFlat, recall과 지연의 절충 — 정리 (힌트)

## 해결하는 문제

RAG([15번](../15-rag-pipeline/2-summary.md))의 검색 단계는 "질의 벡터와 가장 가까운 문서 벡터 k개"를 찾는다. 인덱스가 없으면 모든 행과 거리를 계산한다.

```text
  전수(정확) 탐색:  질의 1건 = 행 N개 × 차원 d 곱셈        → 비용이 N에 비례
                    N = 5만, d = 128  →  질의당 중앙값 약 24~30ms (실험 1, 2코어)
  근사 인덱스(ANN): 일부 후보만 본다                         → 질의당 1ms 안팎, 대신 정답 일부를 놓친다
```

- *최근접 탐색(nearest neighbor search)*: 질의와 거리가 가장 가까운 벡터 k개를 찾는 일. 무차별 탐색의 비용 식은 [math/13](../../math/13-linear-algebra-essentials/2-summary.md) 5절이 단일 출처다.
- *ANN(approximate nearest neighbor)*: 정답 top-k를 "거의" 찾는 인덱스. 속도를 얻고 정확도를 조금 내준다.
- *recall@k*: 정확 top-k 중 근사 결과 top-k에 들어온 비율. `|근사 top-k ∩ 정확 top-k| / k`.
  - 흔한 오해: "인덱스는 결과를 바꾸지 않는다." B-tree 인덱스([database/08](../../database/08-btree-indexes/2-summary.md))는 결과가 같다. pgvector README는 근사 인덱스를 추가하면 "질의 결과가 달라진다"고 적는다.

쉬운 예: 도서관에서 "이 책과 비슷한 책"을 찾는다.
- 전수 탐색 = 서가를 처음부터 끝까지 다 본다. 정확하지만 느리다.
- IVFFlat = 책을 주제별 서가 50개로 나눠 두고, 가까운 서가 몇 개만 본다. 경계에 꽂힌 책은 놓친다.
- HNSW = "비슷한 책" 쪽지가 붙은 책을 따라 건너간다. 고속도로(위층)로 동네까지 가고, 골목(아래층)에서 주변을 훑는다.

똑같은 구조다.\
빠르게 찾는 대가로 **정답을 일부 놓치고(recall < 1), 그 정도는 파라미터로 조절한다.**

실무 예:
- 상품 설명 임베딩 500만 건을 매 질의 전수 탐색하면 지연 예산을 넘는다. HNSW를 붙이자 빨라졌지만 "어제와 다른 결과"가 문의로 들어온다.
- `WHERE tenant_id = ? ORDER BY embedding <=> ? LIMIT 10`이 10건이 아니라 2~4건을 돌려준다.

## 동작·원리

### 1. 세 가지 탐색 방식

```text
  (a) 전수 탐색                  (b) IVFFlat (lists = 5 예시)        (c) HNSW (층 3개 예시)
  모든 행과 거리 계산            구축: k-평균으로 중심 5개           층 2:  A ─────────── F
  → top-k 힙                     ┌────┬────┬────┬────┬────┐         층 1:  A ──── C ──── F ──── H
                                 │ c1 │ c2 │ c3 │ c4 │ c5 │         층 0:  A─B─C─D─E─F─G─H─I─J (전부)
                                 │목록│목록│목록│목록│목록│
                                 └────┴────┴────┴────┴────┘         질의: 맨 위층 진입점에서 출발,
                                 질의: 가까운 중심 probes개를 골라   가까운 이웃으로 탐욕 이동,
                                 그 목록만 전수 계산                 더 못 가면 한 층 내려간다.
                                                                     층 0에서 후보 ef_search개를 모은다
```

- **전수 탐색**: pgvector의 기본값이다. README: "By default, pgvector performs exact nearest neighbor search, which provides perfect recall."
- **IVFFlat**: README는 "벡터를 목록(lists)으로 나누고, 질의 벡터에 가장 가까운 목록 일부만 탐색한다"고 설명한다. 인덱스 생성 단계 이름에 `performing k-means`가 있다(README "Indexing Progress").
  - *lists*: 목록(군집) 개수. 시작점 권고 = 100만 행 이하 `rows / 1000`, 초과 `sqrt(rows)`(README).
  - *ivfflat.probes*: 질의 때 볼 목록 개수. 기본 1, 시작점 권고 `sqrt(lists)`. probes = lists면 정확 탐색이고 플래너는 인덱스를 쓰지 않는다(README).
- **HNSW**: README: "다층 그래프를 만든다. IVFFlat보다 속도-recall 절충이 좋고, 구축이 느리고 메모리를 더 쓴다. 학습 단계가 없어 빈 테이블에도 만들 수 있다."
  - Malkov–Yashunin(arXiv 1603.09320) 초록: 원소마다 최대 층을 **지수적으로 줄어드는 확률**로 무작위로 정한다. 위층부터 탐색해 로그 복잡도 스케일링을 얻는다. 구조가 스킵 리스트와 비슷하다.
  - *m*: 노드당 연결 최대 수(기본 16). README는 "층마다(per layer)"라고만 적지만, pgvector v0.8.7 소스(`src/hnsw.h` `HnswGetLayerM`)는 층 0만 `2 × m`(기본 32), 위층은 `m`이다.
  - *ef_construction*: 그래프를 만들 때 쓰는 동적 후보 목록 크기(기본 64). 크면 recall이 오르고 구축·삽입이 느려진다(README).
  - *hnsw.ef_search*: 질의 때 동적 후보 목록 크기(기본 40). 크면 recall이 오르고 느려진다(README).
  - 결과 수도 이 후보 목록 크기에 묶인다. README "Troubleshooting": 결과는 `hnsw.ef_search` 크기로 제한되고, 죽은 튜플이나 필터 조건 때문에 더 적을 수 있다.

### 실험 1: 같은 데이터, 세 방식의 recall@10과 지연

- 데이터(합성): 5만 행, 128차원, 군집 200개의 가우스 혼합을 길이 1로 정규화, 코사인 거리(`<=>`). 질의 200개는 같은 분포에서 뽑았고 표에는 없다. 필터용 `cat` 열은 0~9 균등(군집과 독립). Python 생성기 seed 16.
- 정답: 인덱스 없이 `ORDER BY embedding <=> q, id LIMIT 10`.
- 지연: PL/pgSQL 함수 안에서 질의마다 `clock_timestamp()` 차이를 쟀다(네트워크·클라이언트 제외, 질의 200개의 분위).

(실험, PostgreSQL 17.11 + pgvector 0.8.7(`SELECT extversion FROM pg_extension` 결과), Docker `pgvector/pgvector:pg17` `--cpus=2 --memory=1g`, 2026-10-08 — 각 줄은 `bench()` 한 번이 돌려준 행(psql 머리줄 생략)과 `\timing`·`pg_relation_size` 값을 모은 것)

```text
  방식 / 파라미터                      recall@10  반환 행  p50 ms  p95 ms   구축       인덱스 크기
  전수 탐색(Seq Scan, 새 세션 3회)     1.000      10      23.7~24.0  29.9~34.0  —         (힙 28MB)
  HNSW m=16 ef_construction=64                                              38.5s      40MB
    ef_search = 10                     0.763      10      0.36    0.67
    ef_search = 20                     0.857      10      0.53    0.84
    ef_search = 40 (기본)              0.923      10      0.94    1.53
    ef_search = 100                    0.947      10      2.02    2.82
    ef_search = 200                    0.965      10      3.54    5.10
    ef_search = 400                    0.983      10      8.47    9.85
    ef_search = 5 (LIMIT 10)           0.396       5      0.34    0.55
  HNSW m=8 ef_construction=32                                               13.1s      36MB
    ef_search = 40                     0.775      10      0.50    1.00
    ef_search = 100                    0.875      10      0.99    1.84
  IVFFlat lists=50 (= 5만/1000)                                             1.3s       26MB
    probes = 1 (기본)                  0.616      10      0.64    1.13
    probes = 3                         0.718      10      1.80    2.26
    probes = 7 (≈ sqrt(50))            0.794      10      4.66    5.32
    probes = 15                        0.898      10      9.81    11.81
    probes = 50 (= lists)              1.000      10      35.03   40.70
```

- 관찰 1: HNSW는 `ef_search`를 올릴수록 recall이 오르고 지연도 오른다. 기본 40에서 recall 0.923, p50 0.94ms다. 전수 탐색보다 약 25배 빠르고 정답 10개 중 평균 0.8개를 놓친다.
- 관찰 2: `ef_search = 5`에 `LIMIT 10`이면 **행이 5개만 온다.** 후보 목록이 5칸이라서다(README Troubleshooting과 일치).
- 관찰 3: 이 데이터에서 같은 지연이면 HNSW가 IVFFlat보다 recall이 높다. p50 약 2ms에서 HNSW(ef 100) 0.947, IVFFlat(probes 3) 0.718이다. README의 "속도-recall 절충이 더 좋다"와 같은 방향이다.
- 관찰 4: 구축은 반대다. IVFFlat 1.3초, HNSW 38.5초(병렬 빌드 끔). m·ef_construction을 줄이면 구축이 13.1초로 줄고 recall도 떨어진다(ef 40에서 0.775).
- 관찰 5: HNSW를 같은 설정으로 다시 만들었더니 ef 40의 recall이 0.926이었다(첫 구축 0.923, 별도 컨테이너에서 처음부터 다시 만든 점검 재실행 0.928). 층 배정이 무작위라 그래프가 매번 조금 다르다(해석 — 초록의 "무작위로 정한다"와 맞는다). 같은 그래프에서 3회 반복한 recall은 셋 다 0.926이었다.
- 관찰 6: probes = lists(50)이면 recall 1.000이고 지연(p50 35ms)은 전수 탐색(24ms)보다 짧아지지 않았다. 새로 만든 계획의 `EXPLAIN`은 이 설정에서 `Seq Scan`을 골랐다(README "the planner won't use the index"와 일치). 계획이 전수 탐색과 같으므로 두 값의 차이는 측정 잡음으로 본다 — 점검 재실행에서는 probes 50이 p50 25.9ms, 전수 탐색이 29.5~30.2ms였다.
- 관찰 7(점검 재실행 — 같은 생성기·같은 `bench()`, 별도 컨테이너, 다른 작업이 함께 돌던 호스트, 2026-10-08)
  - 전수 p50 29.5~30.2ms. HNSW 구축 49.9초·40MB, ef_search 10/20/40/100/400 → recall 0.758/0.866/0.928/0.947/0.983, ef 5 → 5행.
  - IVFFlat lists 50: 구축 1.5초·26MB, probes 1/7/50 → recall 0.553/0.764/1.000. **IVFFlat도 다시 만들면 recall이 달라졌다**(probes 1에서 0.616 → 0.553).
  - 지연은 호스트 부하에 따라 수십 % 움직였다. recall은 구축마다 HNSW ±0.01, IVFFlat ±0.06 정도 흔들렸다. 표의 값은 한 번 구축한 결과다.

측정 함정(이 실험에서 실제로 겪음):
- 같은 세션에서 `SET enable_indexscan = off`를 한 뒤 같은 PL/pgSQL 함수를 다시 부르자 recall이 여전히 0.926이었다. 함수가 이미 만든 계획(인덱스 스캔)을 재사용했다(해석). 새 세션에서 돌리자 1.000, p50 약 24ms가 나왔다. 설정을 바꿔 비교할 때는 세션을 새로 열거나 계획 캐시를 비운다.

### 2. 실행 계획으로 보기 — `EXPLAIN (ANALYZE, BUFFERS)`

(실험 1과 같은 환경, 질의 1개 — InitPlan·Planning 줄 생략)

```text
  HNSW (ef_search 40)
   Limit (actual time=0.918..0.942 rows=10 loops=1)
     ->  Index Scan using items_hnsw on items (actual time=0.916..0.936 rows=10 loops=1)
           Order By: (embedding <=> (InitPlan 1).col1)
           Buffers: shared hit=700
   Execution Time: 0.981 ms

  전수 탐색 (enable_indexscan = off)
   Limit (actual time=35.646..35.653 rows=10 loops=1)
     ->  Sort (actual time=35.644..35.646 rows=10 loops=1)
           Sort Key: ((items.embedding <=> (InitPlan 1).col1))
           Sort Method: top-N heapsort  Memory: 25kB
           ->  Seq Scan on items (actual time=0.067..23.079 rows=50000 loops=1)
                 Buffers: shared hit=3602
   Execution Time: 35.692 ms
```

- 전수 탐색은 5만 행을 다 읽고(3602 버퍼) **top-N 힙 정렬**로 10개만 남긴다.
- HNSW는 700 버퍼만 만진다. 그래프에서 질의 근처만 걸었다는 뜻이다.
- README: 인덱스를 쓰려면 `ORDER BY`가 거리 연산자 결과의 **오름차순**이고 `LIMIT`이 있어야 한다. `ORDER BY 1 - (embedding <=> q) DESC`는 인덱스를 쓰지 않는다.

### 3. 필터는 인덱스 탐색 **뒤에** 적용된다

```text
  SELECT id FROM items WHERE cat = 3 ORDER BY embedding <=> q LIMIT 10;

  HNSW 탐색 → 후보 ef_search = 40개 ──→ WHERE cat = 3 (선택도 10%) ──→ 평균 4개만 남음
                                                                          LIMIT 10인데 4건
```

- README "Filtering": "근사 인덱스에서는 필터가 인덱스 스캔 **후에** 적용된다. 조건이 행의 10%에 맞으면, HNSW와 기본 `hnsw.ef_search` 40에서 평균 4행만 맞는다."
- 0.8.0부터 *반복 인덱스 스캔(iterative index scan)*이 있다. 결과가 모자라면 인덱스를 더 훑는다. `hnsw.max_scan_tuples`(기본 20,000)나 `ivfflat.max_probes`에서 멈춘다(README).
  - `strict_order`: 결과를 거리 순서 그대로 지킨다.
  - `relaxed_order`: 순서가 조금 어긋날 수 있지만 recall이 더 좋다(README).

### 실험 2: 선택도 10% 필터와 결과 수 부족

(실험 1과 같은 환경·데이터, 질의 200개, `WHERE cat = 3`. 정답 = 필터를 건 정확 top-10. 각 줄 = `bench(3)` 한 번의 출력 행)

```text
  방식                                       recall@10  반환 행(평균)  p50 ms  p95 ms
  전수 탐색 + 필터 (인덱스 없음)             1.000      10.00          12.03   13.23
  HNSW ef_search 40                          0.422       4.26          1.01    1.59
  HNSW ef_search 100                         0.778       9.02          1.89    2.59
  HNSW ef_search 40 + iterative strict       0.767      10.00          2.80    6.20
  HNSW ef_search 40 + iterative relaxed      0.814      10.00          2.69    4.94
  IVFFlat lists 50, probes 7                 0.699      10.00          4.86    5.40
```

`EXPLAIN (ANALYZE, BUFFERS, COSTS OFF)` 한 질의(HNSW, ef_search 40 — InitPlan·Buffers 줄 생략):

```text
   Limit (actual time=0.854..0.905 rows=2 loops=1)
     ->  Index Scan using items_hnsw on items (actual time=0.852..0.901 rows=2 loops=1)
           Order By: (embedding <=> (InitPlan 1).col1)
           Filter: (cat = 3)
           Rows Removed by Filter: 38
```

- 관찰 1: 평균 4.26행(점검 재실행 4.21행). README의 "평균 4행"이 그대로 재현됐다. 위 질의는 후보 40개 중 38개가 필터로 빠져 2행만 남았다.
- 관찰 2: 반복 스캔을 켜면 10행을 채운다. 대가로 p95가 1.59ms → 6.20ms(strict)로 늘었다.
- 관찰 3: IVFFlat은 probes 7이면 목록 7개(약 7,000행)를 다 훑으므로 10% 필터 뒤에도 10행이 남았다. 결과 수 부족은 "후보를 몇 개 보느냐"의 문제다(해석).
- 관찰 4: 인덱스 없는 전수 탐색이 필터 때 더 빨랐다(24ms → 12ms). 필터로 거리 계산 대상이 줄어서다(해석). README도 선택도가 낮은 조건에는 필터 열 인덱스로 정확 탐색을 하라고 권한다.

### 4. IVFFlat은 "데이터가 있을 때" 만든다

```text
  빈 테이블에 CREATE INDEX ... ivfflat (lists = 50)
     → k-평균이 학습할 데이터가 없음 → 중심이 실제 분포와 무관
     → 나중에 넣은 5만 행이 몇 개 목록에 몰리거나 엉뚱한 목록에 배정
     → probes를 그대로 둬도 recall 하락
```

- README: 좋은 recall의 세 열쇠 중 첫째가 "테이블에 데이터가 좀 있을 **때** 인덱스를 만든다"이다. HNSW는 학습 단계가 없어 이 제약이 없다.

### 실험 3: IVFFlat을 만드는 시점

(실험 1과 같은 환경·데이터, lists 50. 위 세 줄은 psql 출력 그대로, 표는 `bench()` 출력 행을 모은 것)

```text
  NOTICE:  ivfflat index created with little data
  DETAIL:  This will cause low recall.
  HINT:  Drop the index until the table has more data.

  생성 시점                         probes 7 recall@10   probes 15 recall@10
  5만 행 적재 후 생성               0.794                0.898
  500행일 때 생성 → 나머지 적재     0.562                —
  빈 테이블에서 생성 → 전부 적재    0.404                0.629
```

- 관찰: 경고는 `NOTICE` 한 줄이다. 오류가 아니라서 마이그레이션 스크립트 로그에 묻히기 쉽다. recall은 거의 반으로 떨어졌다.
- 점검 재실행(빈 테이블에서 생성 → 전부 적재): 같은 NOTICE, probes 7 recall 0.431, probes 15 0.652. 값은 구축마다 조금 다르고 "반 가까이 떨어진다"는 경향은 같다.

## 쓰이는 자료구조·알고리즘

- **상위 k 힙** — 전수 탐색의 `Sort Method: top-N heapsort`(실험 2절). [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **계층 근접 그래프(HNSW)** — 층을 지수 감소 확률로 정하고 위층부터 탐욕 탐색(Malkov–Yashunin 초록). 층 배정 방식이 [data-structure/12-skip-list](../../data-structure/12-skip-list/2-summary.md)와 닮았다. 탐색 중 후보 목록은 거리 순 우선순위 큐로 관리한다(논문 알고리즘의 구현 세부는 본문 미열람 [?]).
- **k-평균 군집 + 목록(IVFFlat)** — 중심마다 벡터 목록을 둔다. "용어 → 문서 목록"의 역색인과 같은 꼴이라 이름이 *inverted file*이다(이름의 유래는 기억 [?]). [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- **B-tree(필터 열)** — 선택도가 낮은 필터는 필터 열 인덱스로 후보를 줄인 뒤 정확 탐색(README "Filtering"). [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md)
- **무차별 내적·코사인** — 비용 식과 정규화는 [math/13](../../math/13-linear-algebra-essentials/2-summary.md). 고차원에서 KD 트리가 무너지는 이유는 [data-structure/25-spatial-index](../../data-structure/25-spatial-index/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 고르는 순서

```text
  데이터 규모·지연 예산 확인
    │
    ├─ 전수 탐색이 지연 예산 안에 든다 ──────────────→ 인덱스 없이 정확 탐색(recall 1.0, 결과 안정)
    │     (필터가 행 대부분을 거르면 필터 열 B-tree)
    │
    ├─ 넘는다, 데이터가 계속 들어온다·구축 시간 여유 ──→ HNSW (m·ef_construction 기본값부터)
    │
    └─ 넘는다, 한 번에 적재·구축이 빨라야 한다 ────→ IVFFlat (적재 후 생성, lists = rows/1000)
```

- 기본값부터 시작하고 recall을 **측정한 뒤** 바꾼다. README: "use the defaults unless seeing low recall".

### 2. recall을 운영에서 재기

README "Monitoring": "근사 검색 결과를 정확 검색 결과와 비교해 recall을 감시하라."

```sql
-- 표본 질의 하나의 근사 top-10
BEGIN;
SET LOCAL hnsw.ef_search = 40;
SELECT array_agg(id) AS approx
FROM (SELECT id FROM items ORDER BY embedding <=> $1 LIMIT 10) s;
COMMIT;

-- 같은 질의의 정확 top-10 (이 트랜잭션에서만 인덱스 스캔을 끈다)
BEGIN;
SET LOCAL enable_indexscan = off;
SELECT array_agg(id) AS exact
FROM (SELECT id FROM items ORDER BY embedding <=> $1 LIMIT 10) s;
COMMIT;
```

```java
// 표본 질의마다 recall@k를 계산해 지표로 보낸다(정확 탐색은 비싸므로 표본만)
static double recallAtK(List<Long> approx, List<Long> exact) {
    Set<Long> truth = new HashSet<>(exact);
    long hit = approx.stream().filter(truth::contains).count();
    return (double) hit / exact.size();
}
```

- 정확 탐색은 질의당 수십 ms라(실험 1) 전 질의가 아니라 표본에만 돌린다.
- 데이터 분포가 바뀌면 recall도 바뀐다. 고정 질의 세트로 주기적으로 잰다.

### 3. 필터가 있는 질의

증상: `LIMIT 10`인데 10건이 안 온다. → 원리: 필터가 후보 목록 **뒤에** 적용된다(3절). → 확인과 대처:

```sql
-- 1) 확인: 반환 행 수와 Rows Removed by Filter
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM items WHERE cat = 3 ORDER BY embedding <=> $1 LIMIT 10;

-- 2) 반복 스캔(0.8.0+) — 한 질의에만
BEGIN;
SET LOCAL hnsw.iterative_scan = relaxed_order;
SELECT id FROM items WHERE cat = 3 ORDER BY embedding <=> $1 LIMIT 10;
COMMIT;

-- 3) 값 종류가 적으면 부분 인덱스, 많으면 파티션(README "Filtering")
CREATE INDEX ON items USING hnsw (embedding vector_cosine_ops) WHERE (cat = 3);
```

- 거리 순서가 꼭 맞아야 하면 `strict_order`를 쓰거나, README처럼 `relaxed_order` 결과를 `MATERIALIZED` CTE에 담아 다시 정렬한다(PostgreSQL 17+에서는 `ORDER BY distance + 0`).

### 4. 파라미터를 질의 단위로

- `SET LOCAL hnsw.ef_search = 100`처럼 트랜잭션 안에서만 바꾼다(README). 커넥션 풀에서 세션 단위 `SET`은 다음 요청에 새어 나간다(해석 — 풀은 세션을 재사용한다).
- 자바 쪽에서는 같은 트랜잭션 안에서 `SET LOCAL`과 검색 질의를 연달아 실행한다.

## 장애 시나리오와 대처

### 1. 인덱스를 만들었더니 검색 결과가 바뀌었다 (⚠ 커리큘럼)

- 현상: 배포 전후로 같은 질의의 상위 10건이 다르다. 스냅샷 테스트가 깨진다.
- 보이는 형태: 오류 없음. "이 문서가 왜 안 나오죠" 문의.
- 원인: 정확 탐색(recall 1.0)이 근사 탐색으로 바뀌었다. 기본 ef_search 40에서 recall 0.923이었다(실험 1).
- 대처: 근사임을 계약에 적는다. 표본 recall을 지표로 두고(적용 2), 테스트는 "정확 top-10 중 몇 개 이상"처럼 recall 기준으로 쓴다.

### 2. 필터를 걸었더니 LIMIT보다 적게 온다 (⚠ 커리큘럼)

- 현상: `WHERE tenant_id = ? … LIMIT 10`이 2~4건을 돌려준다.
- 보이는 형태: 화면의 추천 목록이 비거나 짧다. `EXPLAIN ANALYZE`의 `Rows Removed by Filter`가 크다.
- 원인: 필터가 후보 ef_search개 뒤에 적용된다. 선택도 10%에서 평균 4.26행(실험 2).
- 대처: 반복 스캔(`hnsw.iterative_scan`)·ef_search 상향·부분 인덱스·파티션. 선택도가 아주 낮으면 필터 열 인덱스 + 정확 탐색.

### 3. IVFFlat recall이 처음부터 낮다 (⚠ 커리큘럼)

- 현상: probes를 올려도 기대만큼 recall이 안 나온다.
- 보이는 형태: 생성 로그에 `NOTICE: ivfflat index created with little data` 한 줄.
- 원인: 데이터 적재 전에 인덱스를 만들어 k-평균 중심이 실제 분포와 무관하다. 빈 테이블 생성 시 probes 7 recall 0.404(적재 후 생성 0.794, 실험 3).
- 대처: 적재 후 `REINDEX`(또는 DROP 후 재생성). 마이그레이션에서 인덱스 생성을 초기 적재 뒤로 옮긴다. 데이터가 크게 늘거나 분포가 바뀐 뒤에도 재생성을 검토한다(해석 — 중심은 생성 때 정해진다).

### 4. 테넌트 하나가 다른 테넌트의 검색을 망친다 (⚠ 커리큘럼)

- 현상: 큰 테넌트가 데이터를 대량 적재한 뒤 작은 테넌트의 검색 결과가 줄고 느려진다.
- 보이는 형태: 테넌트 필터 질의의 반환 행 수 감소(장애 2와 같은 꼴), 지연 증가.
- 원인: README "Multitenancy": 근사 인덱스를 테넌트끼리 공유하면 한 테넌트의 벡터가 다른 테넌트의 recall(과 속도)에 영향을 준다. 후보 목록을 다른 테넌트 벡터가 차지한다(해석 — 실험 2의 필터 효과와 같은 원리).
- 대처: 리스트 파티션(테넌트별) 또는 테이블 분리(README).

### 5. 인덱스가 안 쓰이거나 만들어지지 않는다

- 현상 A: 인덱스가 있는데 지연이 전수 탐색 수준이다. 보이는 형태: `EXPLAIN`에 `Seq Scan` + `Sort`. 원인: `ORDER BY 1 - (embedding <=> q) DESC`처럼 거리 연산자 오름차순이 아니거나 `LIMIT`이 없다(README). 대처: `ORDER BY embedding <=> q LIMIT k`로 고친다.
- 현상 B: Docker 컨테이너에서 HNSW 생성이 실패한다. 보이는 형태(이 실험): `ERROR: could not resize shared memory segment "/PostgreSQL.…" to 265326048 bytes: No space left on device`. 원인: 병렬 빌드가 공유 메모리를 쓰는데 컨테이너의 `/dev/shm`이 64MB였다(`df -h /dev/shm`로 확인). 대처: 컨테이너 공유 메모리를 늘리거나(`--shm-size`), `maintenance_work_mem`을 줄이거나, 병렬 빌드를 끈다(`max_parallel_maintenance_workers = 0` — 이 실험의 선택, 대신 느려진다).

## 핵심 문장

- 전수 탐색은 recall 1.0이고 비용이 N에 비례한다. 근사 인덱스는 빠른 대신 결과가 바뀐다.
- HNSW는 `ef_search`, IVFFlat은 `probes`가 recall과 지연을 함께 움직이는 손잡이다. 기본값부터 시작해 recall을 재고 바꾼다.
- 필터는 인덱스 탐색 뒤에 적용된다. 선택도 10% + ef_search 40이면 평균 4행이다. 반복 스캔·부분 인덱스·파티션으로 푼다.
- IVFFlat은 k-평균으로 목록을 만들므로 데이터를 넣은 뒤 만든다. HNSW는 학습 단계가 없다.
- recall은 표본 질의로 근사 결과와 정확 결과를 비교해 운영 지표로 둔다.

## 관련 주제·근거

- 선행
  - [15-rag-pipeline](../15-rag-pipeline/2-summary.md) — 검색 단계가 이 인덱스를 쓴다
  - [database/08-btree-indexes](../../database/08-btree-indexes/2-summary.md) — 결과가 바뀌지 않는 정확 인덱스와 대비
  - [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md) — 내적·코사인·무차별 최근접 비용
- 후속·연결
  - [17-hybrid-search-and-reranking](../17-hybrid-search-and-reranking/2-summary.md) — 벡터 검색 결과를 어휘 검색과 합치기
  - [18-index-freshness-and-reembedding](../18-index-freshness-and-reembedding/2-summary.md) — 임베딩 모델 교체와 버전별 부분 인덱스
  - [data-structure/12-skip-list](../../data-structure/12-skip-list/2-summary.md) · [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) · [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- 문서·논문
  - pgvector README(설치 안내 v0.8.7 기준, 2026-10-08 확인) <https://github.com/pgvector/pgvector> — "Indexing"(기본 정확 탐색, 근사 인덱스 후 결과 변화) · "HNSW"(m 16·ef_construction 64·ef_search 40, 구축·메모리 절충, 학습 단계 없음) · "IVFFlat"(lists·probes 권고, probes = lists면 정확) · "Filtering"(필터는 스캔 후, 10% → 평균 4행) · "Iterative Index Scans"(0.8.0+, max_scan_tuples 20,000) · "Multitenancy" · "Monitoring" · "Troubleshooting"(ORDER BY·LIMIT 조건, 결과 수 제한, little data)
  - pgvector v0.8.7 소스 `src/hnsw.h` 126~127행 — `/* 2 * M connections for ground layer */`, `HnswGetLayerM(m, layer) (layer == 0 ? (m) * 2 : (m))`(2026-10-08 확인) <https://github.com/pgvector/pgvector/blob/v0.8.7/src/hnsw.h>
  - Malkov, Yashunin, "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs", arXiv 1603.09320 (2016-03-30) — 초록 확인. 학술지판(IEEE TPAMI 2020) 미열람 [?] <https://arxiv.org/abs/1603.09320>
  - Douze 외, "The Faiss library", arXiv 2401.08281 (2024) — 벡터 검색의 색인·압축·절충 공간(초록) <https://arxiv.org/abs/2401.08281>
- 실험 목록(모두 PostgreSQL 17.11 + pgvector 0.8.7, Docker `pgvector/pgvector:pg17` `--cpus=2 --memory=1g`, `/dev/shm` 64MB, `maintenance_work_mem` 256MB, `max_parallel_maintenance_workers` 0, 2026-10-08)
  - 1. 합성 5만×128차원(군집 200, seed 16), 질의 200 — 전수(3회) vs HNSW(m16/efc64, ef_search 5~400; m8/efc32; 재구축 후 3회) vs IVFFlat(lists 50, probes 1~50)의 recall@10·p50·p95·구축 시간·크기. 사실 점검 때 별도 컨테이너에서 같은 생성기로 한 번 더 구축·측정(관찰 7)
  - 2. 선택도 10% 필터 — 반환 행 수, 반복 스캔 strict·relaxed, `EXPLAIN (ANALYZE, BUFFERS)`
  - 3. IVFFlat 생성 시점(빈 테이블·500행·적재 후)별 recall
