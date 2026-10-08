# ai-engineering/05-embeddings-and-similarity — 임베딩과 유사도: 모델이 정한 벡터 공간, 정규화, 차원 절단, 공간 혼합 — 정리 (힌트)

## 해결하는 문제

키워드 검색은 같은 뜻의 다른 말을 놓친다. "환불 받고 싶어요"로 찾을 때 "결제 취소 후 돈 돌려받기" 문서는 겹치는 단어가 없다.

두 문장을 모델에 **함께** 넣어 비슷한지 묻는 방법은 정확하지만 비싸다.
- Reimers·Gurevych(EMNLP 2019, Sentence-BERT 초록): 문장 1만 개에서 가장 비슷한 쌍을 BERT로 찾으면 약 5천만 번 추론(약 65시간)이 든다.
- 문장마다 **한 번씩만** 모델에 넣어 고정 길이 벡터를 만들고, 비교는 벡터 연산으로 하면 같은 일이 약 5초로 준다(같은 초록).
  - *임베딩(embedding)*: 텍스트를 고정 길이 실수 벡터로 바꾼 것. 뜻이 비슷한 텍스트가 가까운 점이 되도록 모델이 학습한다.
  - *바이-인코더(bi-encoder)*: 질의와 문서를 따로 벡터로 만든 뒤 비교하는 구조. 두 텍스트를 함께 넣는 쪽은 *크로스-인코더*([17-hybrid-search-and-reranking](../17-hybrid-search-and-reranking/2-summary.md)).

쉬운 예: 지도 좌표다.
- 가게마다 위도·경도를 한 번 적어 두면, "여기서 가까운 가게"는 좌표 거리 계산만으로 찾는다.
- 단, 좌표계가 같아야 한다. 한 가게는 WGS84로, 다른 가게는 다른 좌표계로 적으면 숫자 모양은 같아도 거리가 엉터리다.

똑같은 구조다.\
임베딩 모델이 좌표계다. 같은 모델로 만든 벡터끼리만 거리가 뜻을 갖는다. 질의·문서 인코더를 따로 두는 모델(DPR — 독립 BERT 두 개)도 있는데, 이때는 함께 학습한 그 한 쌍이 하나의 좌표계다(DPR §3.1).

실무 예: FAQ·상품 검색, 중복 문의 묶기, RAG의 문서 검색([15-rag-pipeline](../15-rag-pipeline/2-summary.md)), 의미 캐시([12](../12-prompt-and-semantic-caching/2-summary.md)).

## 동작·원리

### 1. 바이-인코더 흐름 — 문서는 미리, 질의는 요청 때

```text
  색인 (미리, 문서마다 1번)                    검색 (요청마다)
  문서 텍스트 ──> [임베딩 모델 M] ──> v_doc     질의 텍스트 ──> [같은 모델 M] ──> v_q
                                      │                                          │
                                      ▼                                          ▼
                          ┌──────── 벡터 저장소 ────────┐                  유사도 계산
                          │ doc_id │ model=M │ v_doc     │ <──────── top-k (전수 또는 ANN)
                          └────────────────────────────┘
```

- 비용이 갈린다. 문서 N개의 임베딩은 한 번 만들고 저장한다. 요청 때는 질의 하나만 모델에 넣고 나머지는 벡터 계산이다.
- 대가: 질의와 문서가 서로를 보지 못한 채 각자 압축된다. 세밀한 판단은 크로스-인코더 재순위가 보완한다([17](../17-hybrid-search-and-reranking/2-summary.md)).

### 2. 점과 각 — 유사도 세 가지

```text
        ▲ 축 2
        │      ● b (환불 방법)
        │    ╱
        │   ╱  θ 작음 → 비슷
        │  ╱ ─────● a (돈 돌려받기)
        │ ╱
        │╱──────────────────────● c (배송 조회)   θ 큼 → 다름
        └──────────────────────────────▶ 축 1
```

- 코사인·내적·L2의 정의와 "길이 1로 정규화하면 세 기준의 순위가 같다(`|u−w|² = 2 − 2cos θ`)"는 [math/13](../../math/13-linear-algebra-essentials/2-summary.md)이 단일 출처다. 여기서는 임베딩을 다룰 때 이 관계가 깨지는 세 경우만 본다.
  1. 정규화 안 된 벡터에 내적 → 노름 큰 벡터가 상위를 차지([math/13](../../math/13-linear-algebra-essentials/2-summary.md) 실험).
  2. 차원을 자른 뒤 재정규화 없이 내적을 코사인처럼 씀(아래 §4).
  3. 다른 모델의 벡터를 섞음(아래 §3).
- 어느 기준을 쓸지는 **모델 문서가 정한다.** OpenAI 임베딩 가이드는 자사 임베딩이 길이 1로 정규화돼 있어 코사인을 내적으로 계산해도 되고 코사인과 L2의 순위가 같다고 적는다(2026-10-08 확인). 다른 모델은 그 모델 문서를 확인한다.

### 3. 공간은 모델의 것 — 차원이 같아도 섞으면 안 된다

```text
  모델 A의 공간                       모델 B의 공간 (A를 돌려 놓은 것과 같다고 해 보자)
    ▲                                  ▲
    │  ● 환불                           │            ● 배송
    │ ● 돈 돌려받기                     │
    │                ● 배송             │  ● 환불  ● 돈 돌려받기
    └──────────▶                       └──────────▶
  같은 뜻끼리 가깝다 (A 안에서)          같은 뜻끼리 가깝다 (B 안에서)

  섞으면: B로 만든 질의 "환불"  vs  A로 만든 문서 "돈 돌려받기"  → 좌표의 뜻이 달라 거리가 무의미
```

- 임베딩의 i번째 숫자가 무슨 뜻인지는 모델이 학습하며 정한다. 다른 모델(또는 같은 이름의 다른 버전)은 다른 좌표계일 수 있다.
- 차원이 같으면 저장소는 오류 없이 받아들이고 계산도 된다. **결과만 조용히 나빠진다.**
- 차원이 다르면 오히려 낫다. pgvector는 `expected 3 dimensions, not 2` 같은 오류로 막는다(아래 실험).

### 4. 차원 절단 — 앞쪽만 잘라 쓰는 모델

```text
  학습 방식에 따라 앞쪽 차원에 큰 정보가 먼저 담기는 임베딩 (Matryoshka Representation Learning)

  [ d1 d2 ... d256 | d257 ... d1024 | ... d3072 ]
    └── 256차원만 써도 쓸 만 ──┘
    └────────── 1024차원 ───────────┘
  잘라 낸 벡터의 길이는 1보다 작아진다 → 내적을 코사인처럼 쓰려면 다시 정규화
```

- Kusupati 외(2022, MRL 초록): 한 임베딩이 여러 크기에서 쓸 수 있도록 거친 정보부터 세밀한 정보 순으로 학습한다. ImageNet-1K 분류에서 같은 정확도에 임베딩 크기가 최대 14배 작다.
- OpenAI 임베딩 가이드(2026-10-08 확인)
  - text-embedding-3-small 기본 1536차원, text-embedding-3-large 기본 3072차원.
  - `dimensions` 파라미터로 줄여 받는 것을 권한다. 이미 받은 벡터를 직접 자르면 **다시 정규화하라**고 적고 예제 코드를 준다.
- 이 차이는 "코사인을 정직하게 계산하면" 없다. 코사인 식은 길이로 나누므로 자른 벡터에도 맞다. 문제는 **"길이가 1이니 내적 = 코사인"이라는 가정**으로 내적 연산자를 쓸 때다.

### 실험: 정규화·절단·공간 혼합이 최근접 순위를 바꾸는가

- 무엇: 64차원 단위 벡터 2,000개(주제 20개 × 100개, 주제 중심 + 가우스 잡음 0.12)와 주제별 질의 20개. "다른 모델"은 모델 A 벡터에 무작위 직교 회전을 곱한 것으로 흉내 냈다 — 뜻의 거리는 그대로이고 좌표만 다르다.
- 코드 핵심(`exp/05/emb.py`):

```python
docs_b = [rot(d) for d in docs]                          # 모델 B = A를 직교 회전 (차원 같음)
idx = [docs_b[i] if k < n_b else docs[i] for k, i in enumerate(order)]   # B 비율만큼 섞인 색인
qb = rot(q)                                              # 질의는 새 모델 B로
truth = set(... topk(qb, docs_b, dot))                   # 전부 B였을 때의 정답 top-10
got = topk(qb, idx, dot)                                 # 섞인 색인에서의 top-10
```

(실험, Python 3.12 `python:3.12-slim`, Docker `--network none --cpus=2`, 2026-10-08 — seed 2026·5, 2회 실행 출력 동일)

```text
[1] 단위 벡터면 코사인·내적·L2 순위가 같다 (질의 20개, top-10)
  코사인=내적 순위 일치: 20/20, 코사인=L2 순위 일치: 20/20
  확인: |a-b|^2 = 0.808371, 2-2cos = 0.808371
[2] 정규화 안 된 벡터(노름 0.5~3배)에 내적 연산자를 쓰면
  코사인 top-10과 내적 top-10 겹침: 평균 2.7/10
  같은 주제 비율: 코사인 100%, 내적 100%
  내적 top-10의 평균 노름 2.76 (전체 평균 1.73)
[3] 앞 32차원만 잘라 쓸 때 (재정규화 여부)
  자른 벡터의 코사인 top-10 대비 겹침: 재정규화 없이 내적 6.8/10, 재정규화 후 내적 10.0/10
  자른 벡터 노름 범위: 0.46 ~ 0.89 (자르기 전 1.00)
[4] 두 '모델 공간' 혼합: 모델 B = 모델 A를 무작위 직교 회전 (차원 같음 → 오류 없음)
  B 비율 100%: recall@10 1.00, 1위 점수 평균 0.693
  B 비율  50%: recall@10 0.52, 1위 점수 평균 0.677
  B 비율   0%: recall@10 0.00, 1위 점수 평균 0.392
```

- 관찰 1([2]): 주제는 모두 맞았지만 주제 안의 순위가 노름 순으로 바뀌었다(겹침 2.7/10, 뽑힌 것의 평균 노름 2.76 > 전체 1.73). 원리는 [math/13](../../math/13-linear-algebra-essentials/2-summary.md)과 같다.
- 관찰 2([3]): 32차원으로 자르니 길이가 0.46~0.89로 제각각이 됐다. 재정규화 없이 내적을 쓰면 정직한 코사인 top-10과 6.8개만 겹친다. 재정규화하면 10개 모두 겹친다.
- 관찰 3([4]): 색인의 절반만 새 모델로 바꾼 상태에서 recall@10이 0.52다. 오류는 없다. **1위 점수 평균은 0.677로 정상(0.693)과 거의 같다** — 점수만 보는 모니터링으로는 못 잡는다.
  - *recall@10*: 정답 top-10 중 실제 반환된 top-10에 든 비율.
- 관찰 4([4] 0%): 전부 옛 모델 벡터면 recall 0이다. 1위 점수(0.392)는 낮아졌지만 결과는 여전히 10개가 나온다.
- 한계(해석): 실제 두 모델의 관계는 회전보다 훨씬 복잡하다. 회전은 "차원이 같아도 좌표가 다르면 무의미하다"를 가장 깨끗하게 보이는 모형이다.

### 실험: pgvector 연산자 — 음의 내적과 차원 검사

(실험, PostgreSQL 17.11 + pgvector 0.8.7 `pgvector/pgvector:pg17`, 2026-10-08)

```sql
CREATE TABLE doc (id text, emb vector(3));
-- (예시) a·b는 질의와 방향이 거의 같고 길이 1, c는 방향이 덜 맞지만 길이가 큼
INSERT INTO doc VALUES ('a', '[0.6,0.8,0]'), ('b', '[0.8,0.6,0]'), ('c', '[3,0,2]');
SELECT id, emb <#> '[0.7,0.7,0.1]' FROM doc ORDER BY emb <#> '[0.7,0.7,0.1]';
SELECT id, emb <=> '[0.7,0.7,0.1]' FROM doc ORDER BY emb <=> '[0.7,0.7,0.1]';
SELECT id, l2_normalize(emb) <#> l2_normalize('[0.7,0.7,0.1]'::vector) FROM doc ORDER BY 2;
INSERT INTO doc VALUES ('d', '[1,0]');
```

```text
-- 내적(<#>) 정렬: 음의 내적 오름차순
 c  | -2.300
 a  | -0.980
 b  | -0.980
-- 코사인 거리(<=>) 정렬
 a  |    0.015
 b  |    0.015
 c  |    0.359
-- 문서·질의를 l2_normalize 한 뒤 내적 정렬 = 코사인 정렬 (값 = -(1 - 코사인 거리))
 a  |      -0.985
 b  |      -0.985
 c  |      -0.641
-- 차원이 다른 벡터 삽입
ERROR:  expected 3 dimensions, not 2
```

- `<#>`는 **음의** 내적을 돌려준다. PostgreSQL 인덱스 스캔이 오름차순만 지원해서다(pgvector README). 점수로 보여 주려면 `* -1`.
- 정규화 안 된 c가 내적 1위, 코사인 3위다. `l2_normalize`(pgvector 0.7.0부터) 뒤에는 내적 순위 = 코사인 순위다.
- 차원이 다르면 시끄럽게 실패한다. 차원이 같은 다른 모델 벡터는 이 검사를 통과한다 — 막는 것은 앱이 둔 모델 열이다.

## 쓰이는 자료구조·알고리즘

- **내적·노름** — 유사도 계산의 전부다. 정의와 정규화 관계는 [math/13](../../math/13-linear-algebra-essentials/2-summary.md).
- **전수 최근접 = 크기 k 힙** — 모든 벡터와 점수를 계산하며 상위 k만 유지한다. N개에 O(N·d + N log k)([data-structure/07-heap](../../data-structure/07-heap/2-summary.md)).
- **근사 최근접(ANN)** — N이 커지면 HNSW·IVFFlat 같은 색인을 쓴다. 결과가 정확 탐색과 달라질 수 있다([16-vector-index-ann](../16-vector-index-ann/2-summary.md)).
- **차원 절단 = 앞쪽 슬라이스 + 재정규화** — Matryoshka식 학습을 한 모델에서만 의미가 있다. 아무 모델의 벡터나 앞쪽을 자르면 정보가 고르게 퍼져 있어 손실이 클 수 있다(MRL이 따로 학습하는 이유 — 해석).
- **직교 회전** — 거리를 보존하는 좌표 변환. 실험에서 "같은 뜻, 다른 좌표계"를 흉내 냈다.

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

| 증상 | 원리 | 확인 |
|---|---|---|
| 모델 교체 배포 뒤 일부 질의 결과만 엉뚱, 오류 없음 | 옛·새 모델 벡터가 한 색인에 섞였다 | `SELECT model, count(*) ... GROUP BY model`, 고정 질의셋 recall@10 |
| 어떤 질의든 같은 문서 몇 개가 상위 | 정규화 안 된 벡터에 내적 | 상위 결과의 노름 vs 전체 노름 분포 |
| 차원을 줄인 뒤 순위가 미묘하게 바뀜 | 잘라 낸 벡터를 재정규화하지 않고 내적 사용 | 저장된 벡터의 노름이 1인지 표본 검사 |
| `ORDER BY ... <#> ... DESC`가 가장 먼 것부터 반환 | `<#>`는 음의 내적 | 점수 부호 확인, 오름차순으로 |

### 2. 저장 — 벡터와 모델을 한 행에

pgvector README의 "다른 차원의 벡터를 한 열에" FAQ가 바로 이 모양(`model_id` + 표현식·부분 인덱스)을 예로 든다.

```sql
-- 문서 하나에 모델별 벡터를 따로 둔다 (교체 기간에는 두 행이 공존)
CREATE TABLE doc_embedding (
  doc_id     bigint  NOT NULL,
  model      text    NOT NULL,          -- 예: 'emb-v3@1024'  (모델 이름 + 차원 + 정규화 여부까지)
  embedding  vector  NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (doc_id, model)
);
-- 모델마다 부분 인덱스: 같은 차원끼리만 색인할 수 있다
CREATE INDEX ON doc_embedding USING hnsw ((embedding::vector(1024)) vector_cosine_ops)
  WHERE model = 'emb-v3@1024';

-- 질의는 같은 모델의 벡터만 본다
SELECT doc_id
FROM doc_embedding
WHERE model = 'emb-v3@1024'
ORDER BY embedding::vector(1024) <=> $1::vector(1024)
LIMIT 10;
```

- 교체는 "새 모델 벡터를 모두 채운 뒤 질의 쪽 모델 값을 한 번에 바꾼다". 절차는 [18-index-freshness-and-reembedding](../18-index-freshness-and-reembedding/2-summary.md).

### 3. 코드 — 모델이 다르면 계산 자체를 거부 (Java 21)

```java
record Embedding(String model, int dim, float[] v) {
    Embedding {
        if (v.length != dim) throw new IllegalArgumentException("dim mismatch: " + v.length + " != " + dim);
    }
}

static float[] truncateAndNormalize(float[] v, int dim) {
    float[] out = Arrays.copyOf(v, dim);                 // 앞쪽 dim개만
    double s = 0;
    for (float x : out) s += (double) x * x;
    double n = Math.sqrt(s);
    if (n == 0) throw new IllegalArgumentException("zero vector");
    for (int i = 0; i < dim; i++) out[i] = (float) (out[i] / n);
    return out;
}

static double dot(Embedding a, Embedding b) {
    if (!a.model().equals(b.model()) || a.dim() != b.dim())
        throw new IllegalStateException("different embedding spaces: " + a.model() + "/" + a.dim()
                + " vs " + b.model() + "/" + b.dim());
    double s = 0;
    for (int i = 0; i < a.dim(); i++) s += (double) a.v()[i] * b.v()[i];
    return s;
}
```

(실험, OpenJDK 21.0.12 `eclipse-temurin:21-jdk`, 2026-10-08 — `java EmbeddingGuard.java`)

```text
자르기만: [0.5, 0.5] 노름=0.707
자른 뒤 정규화: [0.70710677, 0.70710677] 노름=1.000
거부: different embedding spaces: emb-v3/2 vs emb-v2/2
```

## 장애 시나리오와 대처

### 1. 임베딩 모델 교체 중 옛/새 벡터 혼합 → 오류 없이 품질 붕괴 (⚠)

- **현상**: 새 임베딩 모델을 배포한 뒤 검색·RAG 답의 질이 떨어졌다. 일부 문서는 아무 질의에도 안 나온다.
- **보이는 형태**: 오류·예외 없음. 1위 점수 평균은 거의 그대로(실험 0.693 → 0.677). 고정 질의셋의 recall@10이 떨어진다(실험 1.00 → 0.52).
- **원인**: 질의는 새 모델로, 문서 일부는 옛 모델로 만들어졌다. 차원이 같아 저장소가 막지 않았다.
- **대처**: 벡터 행에 모델(이름·버전·차원)을 저장하고 질의를 같은 모델로 거른다. 새 모델 벡터를 다 채운 뒤 한 번에 전환한다. 고정 질의셋 recall을 배포 게이트로 둔다([19-llm-evaluation](../19-llm-evaluation/2-summary.md)).

### 2. 정규화 안 된 벡터에 내적 연산자 → 노름 큰 벡터가 상위 독점 (⚠)

- **현상**: 질의가 달라도 같은 몇 문서가 상위에 온다.
- **보이는 형태**: 상위 결과의 노름이 평균보다 크다(실험 2.76 vs 1.73).
- **원인**: 내적 = 노름 × 노름 × 코사인. 모델이 정규화된 벡터를 낸다는 가정이 틀렸거나, 중간 가공(평균·합산)으로 길이가 변했다.
- **대처**: 저장 전에 정규화(`l2_normalize` 또는 앱 코드)하거나 코사인 거리(`<=>`)를 쓴다. 저장 벡터의 노름 분포를 표본 검사한다. 원리는 [math/13](../../math/13-linear-algebra-essentials/2-summary.md) 장애 1.

### 3. 차원을 자른 뒤 재정규화 누락 → 순위 왜곡 (⚠)

- **현상**: 저장 비용을 줄이려 3072차원을 1024차원으로 잘라 넣은 뒤 순위가 조금씩 바뀌었다.
- **보이는 형태**: 잘린 벡터의 노름이 1이 아니다(실험 0.46~0.89). 정직한 코사인과의 top-10 겹침이 낮다(실험 6.8/10).
- **원인**: 내적을 코사인 대용으로 쓰는데, 자르면서 길이 1 가정이 깨졌다.
- **대처**: 가능하면 제공자의 차원 파라미터(OpenAI `dimensions`)로 처음부터 줄여 받는다. 직접 자르면 다시 정규화한다(OpenAI 가이드). 차원 절단은 Matryoshka식으로 학습한 모델에서만 쓴다.

### 4. `<#>` 부호를 잊고 내림차순 정렬

- **현상**: 가장 안 비슷한 문서가 먼저 나온다.
- **보이는 형태**: `ORDER BY embedding <#> $1 DESC`. 점수가 음수로 찍힌다.
- **원인**: pgvector `<#>`는 음의 내적이다. 오름차순이 "가장 비슷한 순"이다.
- **대처**: 오름차순으로 정렬하고, 화면 점수는 `* -1`로 바꾼다. 정규화된 벡터라면 코사인 거리 `<=>`가 덜 헷갈린다(유사도 = `1 - 거리`).

## 핵심 문장

- 임베딩은 텍스트를 고정 길이 벡터로 바꿔, 비싼 쌍 비교를 싼 벡터 계산으로 바꾼다. 문서는 미리 한 번, 질의는 요청 때 한 번 모델에 넣는다.
- 벡터 공간은 그것을 만든 모델의 것이다. 차원이 같아도 다른 모델의 벡터를 섞으면 오류 없이 검색 품질만 무너진다.
- 문서 벡터의 길이가 모두 같을 때(길이 1로 정규화가 대표적) 내적·코사인·L2가 같은 순위를 낸다. 길이가 제각각이면 순위가 갈릴 수 있다. 정규화 여부는 모델 문서와 표본 검사로 확인한다.
- 차원을 잘라 쓰면 길이가 1에서 벗어난다. 내적을 코사인처럼 쓰려면 다시 정규화한다.
- 벡터 행에 모델·버전·차원을 함께 저장하고, 질의는 같은 모델의 벡터만 비교한다.

## 관련 주제·근거

- 선행
  - [04-tokenization-and-token-cost](../04-tokenization-and-token-cost/2-summary.md) — 임베딩 모델의 입력도 토큰이다
  - [math/13-linear-algebra-essentials](../../math/13-linear-algebra-essentials/2-summary.md) — 내적·노름·코사인 정의, 정규화와 순위(단일 출처)
- 후속·연결
  - [12-prompt-and-semantic-caching](../12-prompt-and-semantic-caching/2-summary.md) — 임베딩 유사도로 캐시 적중
  - [15-rag-pipeline](../15-rag-pipeline/2-summary.md) · [16-vector-index-ann](../16-vector-index-ann/2-summary.md) · [17-hybrid-search-and-reranking](../17-hybrid-search-and-reranking/2-summary.md) · [18-index-freshness-and-reembedding](../18-index-freshness-and-reembedding/2-summary.md)
  - [data-structure/07-heap](../../data-structure/07-heap/2-summary.md) — 전수 탐색의 상위 k
- 논문
  - Reimers·Gurevych, "Sentence-BERT", EMNLP 2019 — 1만 문장 최다 유사 쌍: BERT 약 65시간 → SBERT 약 5초, 코사인으로 비교하는 문장 임베딩 <https://arxiv.org/abs/1908.10084>
  - Karpukhin 외, "Dense Passage Retrieval", EMNLP 2020 §3.1 — 문서 인코더 E_P·질의 인코더 E_Q를 독립 BERT 두 개로 두고 함께 학습 <https://arxiv.org/abs/2004.04906>
  - Kusupati 외, "Matryoshka Representation Learning"(arXiv 2022, 게재처 [?]) — 거친 것부터 세밀한 것 순으로 담는 표현, 같은 정확도에 최대 14배 작은 임베딩(ImageNet-1K) <https://arxiv.org/abs/2205.13147>
- 교재: Jurafsky·Martin, 『Speech and Language Processing』 3판 초안(2026-08-19판) 5장 Embeddings <https://web.stanford.edu/~jurafsky/slp3/>
- 문서 (2026-10-08 확인)
  - OpenAI "Embeddings" 가이드 — 기본 차원 1536·3072, `dimensions` 파라미터, 직접 자르면 재정규화, FAQ "OpenAI embeddings are normalized to length 1" <https://developers.openai.com/api/docs/guides/embeddings>
  - pgvector README(0.8.7) — `<->`·`<#>`(음의 내적)·`<=>`·`<+>`, 정규화된 벡터면 내적 권장, `l2_normalize`(0.7.0), 다른 차원 저장 FAQ(`model_id` + 표현식·부분 인덱스) <https://github.com/pgvector/pgvector>
- 실험 목록
  - 정규화·절단·공간 혼합(직교 회전) 최근접 모형 — Python 3.12 `python:3.12-slim`, seed 2026·5, 2회 실행 동일
  - pgvector 연산자 부호·정규화·차원 검사 — PostgreSQL 17.11 + pgvector 0.8.7 `pgvector/pgvector:pg17`(컨테이너 `sn-ai-w04-pg`, 종료 확인)
  - 절단 + 재정규화·모델 불일치 거부 — OpenJDK 21.0.12 `eclipse-temurin:21-jdk`
