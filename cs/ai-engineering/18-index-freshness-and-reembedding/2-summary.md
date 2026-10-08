# ai-engineering/18-index-freshness-and-reembedding — 벡터 인덱스 신선도: 변경·삭제 전파와 임베딩 모델 교체 — 정리 (힌트)

## 해결하는 문제

벡터 인덱스는 원천 문서에서 **파생된 데이터**다. 원천이 바뀌면 따라 바뀌어야 한다.

```text
  원천(규정 DB·위키)            파생(벡터 인덱스)
  문서 수정  ───── ? ─────→  옛 청크·옛 벡터가 남아 있으면 → 옛 규정으로 답한다
  문서 삭제  ───── ? ─────→  청크가 남아 있으면 → 지운 내용(개인정보 포함)이 답에 등장
  임베딩 모델 교체 ─ ? ─→  옛 벡터와 새 벡터가 섞이면 → 오류 없이 검색 품질만 무너진다
```

- *파생 데이터(derived data)*: 원천에서 계산해 만든 사본. 지우고 다시 만들 수 있다. 개념은 [data-engineering/01](../../data-engineering/01-system-of-record-and-derived-data/2-summary.md)이 단일 출처다.
- *신선도(freshness)*: 파생 데이터가 원천을 얼마나 늦게 따라오나. "원천 변경 시각 → 인덱스 반영 시각"의 차이로 잰다.
- *재임베딩(re-embedding)*: 같은 청크를 다른(새) 임베딩 모델로 다시 벡터화하는 일.

쉬운 예: 도서관 색인 카드.
- 책 내용이 바뀌었는데 카드는 옛 요약 그대로다. 카드를 보고 찾아간 사람은 옛 내용을 기대한다.
- 폐기한 책의 카드가 남아 있다. 카드만 보고 "그 책에 이렇게 적혀 있다"고 말한다.
- 색인 규칙(분류법)을 바꾸면서 카드 절반만 새 규칙으로 고쳤다. 새 규칙으로 찾는 사람에게 옛 카드는 보이지 않는다.

똑같은 구조다.\
검색 인덱스 동기화([database/48](../../database/48-search-index-sync-and-reindexing/2-summary.md))와 같은 문제에, **"벡터 공간 자체가 모델마다 다르다"**는 조건이 하나 더 붙는다.

실무 예:
- 환불 기한을 14일 → 7일로 고쳤는데 챗봇이 일주일 동안 "14일"이라고 답한다.
- 탈퇴 회원의 상담 기록을 원천에서 지웠는데 RAG 응답에 그 내용이 인용된다.
- 더 좋은 임베딩 모델로 바꾸는 배치를 밤새 돌리는 동안 검색 품질이 떨어진다.

## 동작·원리

### 1. 임베딩 모델이 바뀌면 공간이 바뀐다

```text
  같은 문장 "환불 기한은 7일"
   모델 A(옛) → a = [0.12, -0.40, …]     ← 공간 A의 점
   모델 B(새) → b = [-0.33, 0.05, …]     ← 공간 B의 점

   cos(a, b) ≈ 0    같은 뜻인데 서로 무관한 방향 (실험 1: 평균 0.002)

  질의를 B로 임베딩해 A 벡터와 비교 = 다른 지도의 좌표를 겹쳐 읽는 것
```

- 각 모델은 자기만의 좌표축을 학습한다. 차원 수가 같아도 축의 뜻이 다르다(해석 — 아래 실험의 모형은 이를 무작위 회전으로 흉내 낸다).
- 차원 수가 다르면 계산 자체가 실패한다. 같으면 계산은 되고 **값만 무의미하다.** 이쪽이 더 위험하다.
  - OpenAI "Embeddings" 가이드(2026-10-08 확인): 기본 길이가 text-embedding-3-small 1536, text-embedding-3-large 3072이고, `dimensions` 파라미터로 줄일 수 있다. 같은 제공자 안에서도 모델·설정마다 벡터가 다르다.

### 실험 1: 옛·새 벡터가 섞인 인덱스의 recall

- 모형: 문서 3,000개의 "의미"를 32차원 잠재 벡터로 두고(군집 60, seed 18), 모델 A·B를 서로 다른 무작위 직교 투영(32 → 64차원)으로 만들었다. 모델마다 차원당 잡음 0.03을 더했다. 질의 200개.
- 정답: 잠재 공간의 최근접 10개. recall@10 = 정답 중 검색 결과 top-10에 든 비율.
- 마이그레이션 진행률 f: 문서 중 f만 B 벡터로 바꾸고 나머지는 A 벡터로 둔 "섞인 인덱스".

(실험, 호스트 Python 3.12.3 표준 라이브러리, 2026-10-08)

```text
같은 문서의 A 벡터와 B 벡터 코사인 평균: 0.002  (같은 의미인데 공간이 달라 거의 직교)
이중 색인(전환 전 = A 전체 인덱스를 A 질의로): recall@10 0.81
B로 바꾼 비율 | 질의=B, 섞인 인덱스 | 질의=A, 섞인 인덱스 | 질의=B, version='B'만 | 상위10 중 옛(A) 벡터 수(질의=B)
        0.00 |               0.00 |               0.81 |                 0.00 |   10.0
        0.25 |               0.25 |               0.68 |                 0.25 |    0.8
        0.50 |               0.48 |               0.48 |                 0.48 |    0.2
        0.75 |               0.67 |               0.25 |                 0.67 |    0.0
        1.00 |               0.82 |               0.00 |                 0.82 |    0.0
```

- 관찰 1: 질의를 B로 바꾼 순간 아직 A인 문서는 거의 안 나온다. 진행률 25%에서 recall 0.25다. 오류는 하나도 없다.
- 관찰 2: 질의를 A로 두면 반대로 B로 바뀐 문서가 사라진다(25% → 0.68, 75% → 0.25).
- 관찰 3: 진행률 0%에서 질의만 B로 바꾸면 recall 0.00이다. 상위 10이 전부 다른 공간의 벡터라 사실상 무작위다(해석 — 코사인 ≈ 0 근처의 우연한 값으로 순위가 정해진다).
- 관찰 4: `version = 'B'` 필터를 걸어도 recall은 섞인 인덱스와 같다. 필터는 "섞임"을 드러낼 뿐 빠진 문서를 채우지 못한다. 해법은 **B 색인을 다 채운 뒤 한 번에 전환**(이중 색인)이다. 전환 전에는 A 전체(0.81), 전환 후에는 B 전체(0.82)를 쓴다.

### 2. 이중 색인 후 전환 (blue-green)

```text
  단계 0  운영: current_model = m1   질의 임베딩 = m1, 검색 WHERE model = 'm1'
  단계 1  백필: 전체 청크를 m2로 재임베딩 → (doc_id, chunk_no, 'm2') 행 추가
          이 동안 새 변경은 m1·m2 둘 다에 쓴다(이중 쓰기)
  단계 2  검증: m2 쪽 행 수 = m1 쪽 행 수, 평가셋 recall·정답률(19번)
  단계 3  전환: current_model = m2 — 질의 임베딩 모델과 검색 필터를 **같은 설정 하나로** 동시에
  단계 4  정리: 되돌릴 기간이 지나면 m1 행·인덱스 삭제
```

- 불변식: **질의를 임베딩한 모델 = 검색 대상 벡터를 만든 모델.** 두 값을 따로 설정하면 배포 순서에 따라 잠깐씩 어긋난다(해석).
- 검색 엔진의 별칭 원자 교체([database/48](../../database/48-search-index-sync-and-reindexing/2-summary.md) 5절)와 같은 모양이다. 벡터 쪽에서는 "포인터"가 모델 버전 설정이다.
- pgvector README FAQ: `vector`(차원 미지정) 열에 여러 차원을 저장할 수 있고, 인덱스는 같은 차원의 행에만 만들 수 있다 — 식 인덱스 `embedding::vector(3)`와 부분 인덱스 `WHERE (model_id = 123)`로 모델별 인덱스를 둔다.

### 실험 2: pgvector에서 차원 혼합·버전별 인덱스·재실행·삭제

스크립트 핵심(전체는 다섯 단계를 차례로 실행):

```sql
-- (1)(2) 차원 미지정 열에 m1(3차원)·m2(4차원) 섞기 → 거리 정렬, 이어서 m2 3차원 행 추가 후 3차원끼리 정렬
CREATE TABLE mixed(id int, model text, embedding vector);
INSERT INTO mixed VALUES (1,'m1','[1,0,0]'), (2,'m2','[0.6,0.8,0,0]');
SELECT id FROM mixed ORDER BY embedding <=> '[1,0,0]' LIMIT 5;
INSERT INTO mixed VALUES (3,'m2','[0,1,0]');
SELECT id, model, round((embedding <=> '[1,0,0]')::numeric,3) AS dist
FROM mixed WHERE vector_dims(embedding) = 3 ORDER BY embedding <=> '[1,0,0]';
-- (3) 모델별 식·부분 HNSW 인덱스 (청크 4만 개 × 모델 2개)
CREATE INDEX ON chunk_emb USING hnsw ((embedding::vector(4)) vector_cosine_ops) WHERE model = 'm2';
EXPLAIN (COSTS OFF) SELECT doc_id FROM chunk_emb WHERE model = 'm2' ORDER BY embedding::vector(4) <=> '[1,0,0,0]' LIMIT 10;
-- (4) 같은 배치(청크 400개)를 두 번: 키 없는 naive 테이블 vs 키 + ON CONFLICT … WHERE 해시가 다를 때만
-- (5) 원천 src에서 doc 42 삭제 → 외래 키 없는 emb_nofk vs ON DELETE CASCADE emb_fk, 고아 탐지
```

(실험, PostgreSQL 17.11 + pgvector 0.8.7, Docker `pgvector/pgvector:pg17` `--cpus=2 --memory=1g`, 2026-10-08 — psql 출력 그대로, CREATE·INSERT 줄 일부 생략)

```text
ERROR:  different vector dimensions 4 and 3
INSERT 0 1
 id | model | dist  
----+-------+-------
  1 | m1    | 0.000
  3 | m2    | 1.000
(2 rows)

                             QUERY PLAN                             
--------------------------------------------------------------------
 Limit
   ->  Index Scan using chunk_emb_embedding_idx on chunk_emb
         Order By: ((embedding)::vector(4) <=> '[1,0,0,0]'::vector)
(3 rows)

INSERT 0 400
INSERT 0 400
   t   | rows | distinct_chunks 
-------+------+-----------------
 naive |  800 |             400
(1 row)

INSERT 0 400
INSERT 0 0
   t   | rows 
-------+------
 keyed |  400
(1 row)

DELETE 1
 left_without_fk | left_with_cascade 
-----------------+-------------------
               4 |                 0
(1 row)

 orphan_chunks 
---------------
             4
(1 row)
```

- 관찰 1: 차원이 다르면 `ERROR: different vector dimensions 4 and 3`으로 크게 실패한다. 차원이 같으면 m1·m2가 한 결과에 섞여 나온다. 실험 1의 "조용한 붕괴"가 이쪽이다.
- 관찰 2: 키 없는 적재를 재실행하면 같은 청크가 2배가 된다. 검색 top-k가 같은 내용으로 채워진다(해석 — 중복 청크가 다른 근거를 밀어낸다).
- 관찰 3: 외래 키가 없으면 원천을 지워도 청크 4개가 남는다. 같은 DB라면 `ON DELETE CASCADE`로 0개가 된다. 다른 저장소라면 고아 청크 질의로 찾는다.

### 3. 변경·삭제를 전파하는 길

```text
  원천 DB ──(1) 같은 트랜잭션에 outbox 행──→ 색인 워커 ──→ 청킹·임베딩 ──→ 벡터 테이블 upsert/delete
          └─(2) CDC(커밋 로그 구독)────────┘
  주기 점검 ──(3) 고아·지연 탐지 질의 ──→ 경보·재처리
```

- 이중 쓰기·outbox·CDC의 차이와 순서 보장은 [database/48](../../database/48-search-index-sync-and-reindexing/2-summary.md)과 [data-engineering/05-change-data-capture](../../data-engineering/05-change-data-capture/2-summary.md)가 단일 출처다.
- 벡터 쪽에서 더해지는 것
  - 임베딩 호출은 느리고 비싸고 실패한다([11번](../11-llm-api-client-contract/2-summary.md)). 워커는 재시도하므로 **멱등**이어야 한다.
  - 문서 하나가 청크 여러 개가 된다. 수정 때 청크 경계가 바뀌면 옛 `chunk_no`가 남는다 → 문서 단위로 "그 문서의 청크 전부 교체"를 한 트랜잭션에서 한다(해석 — 파티션 덮어쓰기와 같은 방식, [data-engineering/08](../../data-engineering/08-idempotent-pipelines-and-backfill/2-summary.md)).
  - 내용이 안 바뀐 청크는 다시 임베딩하지 않는다. **같은 모델의 행이 이미 있고** 청크 원문 해시가 같으면 건너뛴다(비용 절감). 모델을 바꿀 때는 원문이 같아도 새 모델 벡터가 없으므로 건너뛰지 않는다 — 키에 `model`이 든 이유다.
- Lewis 외(NeurIPS 2020) 초록은 세계 지식의 갱신을 열린 문제로 꼽는다. 같은 논문 본문 "Index hot-swapping" 단락은 2016년 12월 위키백과 인덱스와 2018년 12월 인덱스를 바꿔 끼워, 세계 지도자 82명 질문에서 시점이 맞는 인덱스면 70%·68%, 어긋난 인덱스면 12%·4%를 맞혔다고 보고한다. 재학습 없이 인덱스만 바꿔 지식을 바꾼 것이다 — 그래서 인덱스 신선도가 곧 답의 신선도다(해석).

## 쓰이는 자료구조·알고리즘

- **내용 해시 키 + 멱등 upsert** — `(doc_id, chunk_no, model)` 기본 키, `content_hash`로 변경 판정, `ON CONFLICT … WHERE 해시가 다를 때만`. [reliability/13-idempotency](../../reliability/13-idempotency/2-summary.md), [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **포인터 원자 교체(blue-green)** — 새 버전을 옆에 다 만든 뒤 "현재 모델" 설정만 바꾼다. [database/48](../../database/48-search-index-sync-and-reindexing/2-summary.md) 5절
- **변경 데이터 캡처·outbox** — 커밋 순서대로 변경을 흘린다. [data-engineering/05](../../data-engineering/05-change-data-capture/2-summary.md)
- **반조인(anti-join)으로 고아 찾기** — `NOT EXISTS (원천)`. 실험 2의 `orphan_chunks`.
- **식 인덱스 + 부분 인덱스** — 모델 버전별 HNSW(pgvector FAQ). 인덱스 원리는 [16번](../16-vector-index-ann/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

```text
  증상                                   원리                               확인 질의·지표
  고친 규정 대신 옛 규정으로 답한다       변경이 인덱스에 늦게/안 반영         원천 updated_at vs 인덱스 indexed_at 차이
  지운 문서가 인용된다                   삭제가 전파되지 않음                고아 청크 수(NOT EXISTS)
  모델 교체 배치 중 검색 품질 하락        옛·새 공간 혼합                     model별 행 수, 질의 모델 = 검색 필터 모델?
  같은 내용 청크가 top-k를 채운다         재실행 중복                         (doc_id, chunk_no, model)별 count > 1
```

### 2. 진단 질의 (PostgreSQL 17)

```sql
-- 신선도 지연: 원천이 바뀐 뒤 아직 반영 안 된 문서와 최대 지연
-- min: 청크 하나라도 수정 전에 색인됐으면 그 문서는 아직 낡았다 (max면 새 청크가 옛 청크를 가린다)
SELECT count(*) AS stale_docs, max(now() - d.updated_at) AS max_lag
FROM docs d
LEFT JOIN (SELECT doc_id, min(indexed_at) AS indexed_at
           FROM chunk_emb WHERE model = current_setting('app.current_model')
           GROUP BY doc_id) e USING (doc_id)
WHERE e.indexed_at IS NULL OR e.indexed_at < d.updated_at;

-- 고아 청크: 원천에서 사라진 문서의 청크
SELECT count(*) FROM chunk_emb e
WHERE NOT EXISTS (SELECT 1 FROM docs d WHERE d.doc_id = e.doc_id);

-- 모델 교체 진행률: 모델별 청크 수
SELECT model, count(*) FROM chunk_emb GROUP BY model;
```

- 문서별 `max(indexed_at)`을 쓰면 장애 4처럼 청크 0~2만 새로 색인되고 옛 청크 3·4가 남은 문서를 "최신"으로 판정한다. 점검 실험(PostgreSQL 17.11, Docker `pgvector/pgvector:pg17`, 2026-10-08)에서 그런 문서 1과 미반영 문서 2를 두자 `max`는 문서 2만, `min`은 1·2를 냈다.
  - 이 질의는 워커가 문서를 다시 볼 때마다 그 문서의 모든 청크 `indexed_at`을 갱신한다고 가정한다(적용 3의 통째 교체). 내용이 같아 임베딩을 건너뛴 문서도 확인 시각은 갱신해야 오탐이 없다.
  - 남은 옛 청크는 청크 번호 집합(원천에서 다시 자른 결과 vs 인덱스)을 주기적으로 대조해 직접 찾을 수도 있다.
- `app.current_model`은 예시 설정 이름이다. 운영에서는 질의 임베딩 코드가 읽는 설정과 같은 출처를 쓴다.
- 신선도 지연은 지표로 내보내고 목표(예: 15분 — 예시)를 넘으면 경보한다([database/48](../../database/48-search-index-sync-and-reindexing/2-summary.md) 6절).

### 3. 문서 단위 재색인 워커 (Java 21, JDBC)

```java
// 문서 하나의 청크를 현재 모델로 통째 교체한다. 재시도해도 결과가 같다(멱등).
void reindexDocument(Connection con, long docId, String model, List<Chunk> chunks,
                     Embedder embedder) throws SQLException {
    // 임베딩 호출은 트랜잭션 밖에서 먼저 한다 — 느린 외부 호출 동안 락을 잡지 않는다
    List<float[]> vectors = embedder.embed(model, chunks.stream().map(Chunk::text).toList());
    con.setAutoCommit(false);
    try (var del = con.prepareStatement(
             "DELETE FROM chunk_emb WHERE doc_id = ? AND model = ?");
         var ins = con.prepareStatement(
             "INSERT INTO chunk_emb(doc_id, chunk_no, model, content_hash, embedding, indexed_at) "
           + "VALUES (?, ?, ?, ?, ?::vector, now())")) {
        del.setLong(1, docId); del.setString(2, model); del.executeUpdate();   // 경계가 바뀐 옛 청크까지 제거
        for (int i = 0; i < chunks.size(); i++) {
            ins.setLong(1, docId); ins.setInt(2, i); ins.setString(3, model);
            ins.setString(4, chunks.get(i).sha256());
            ins.setString(5, Arrays.toString(vectors.get(i)));                // "[0.1, 0.2, …]" 형식
            ins.addBatch();
        }
        ins.executeBatch();
        con.commit();
    } catch (SQLException e) {
        con.rollback();
        throw e;
    }
}
```

- 원천에서 문서가 사라졌으면 같은 경로에서 `DELETE`만 하고 끝낸다(삭제 이벤트도 같은 워커로).
- 그 문서·**그 모델**의 행이 이미 있고 내용 해시가 모두 같으면 임베딩 호출 자체를 건너뛰는 분기를 앞에 둔다(새 모델로 재임베딩할 때는 건너뛰지 않는다).
- `Embedder`·`Chunk`는 예시 인터페이스다. 이 코드는 실행하지 않았다(실험 2의 SQL로 같은 키·삭제 동작을 확인).

### 4. 삭제 요청(개인정보)

- 벡터 행 삭제는 질의에서 즉시 안 보이게 하지만, 물리적 제거·백업·로그·평가셋 사본은 따로다. 전파 지도와 보존 기한은 [data-engineering/12](../../data-engineering/12-data-retention-and-erasure/2-summary.md)가 단일 출처다.
- pgvector README: HNSW 인덱스의 VACUUM은 오래 걸릴 수 있어 먼저 `REINDEX INDEX CONCURRENTLY`를 하면 빨라진다("Vacuuming"). 죽은 튜플은 결과 수를 줄일 수 있다(Troubleshooting). 대량 삭제 뒤에는 인덱스 재구성·VACUUM을 계획한다.
- 임베딩 벡터에서 원문을 복원할 수 있는지는 이 노트에서 다루지 않는다. 벡터도 원문과 같은 등급의 데이터로 지운다(해석 — 보수적 선택).

## 장애 시나리오와 대처

### 1. 원천에서 지운 문서가 답변에 등장한다 (⚠ 커리큘럼)

- 현상: 탈퇴 회원의 상담 내용이 RAG 응답에 인용된다.
- 보이는 형태: 응답의 출처 ID가 원천에 없는 문서를 가리킨다. 오류 없음.
- 원인: 삭제가 벡터 테이블로 전파되지 않았다. 외래 키 없는 파생 테이블에는 원천 삭제 뒤에도 청크가 남는다(실험 2: 4개).
- 대처: 같은 DB면 `ON DELETE CASCADE`, 아니면 outbox·CDC로 삭제 이벤트 전파 + 주기적 고아 탐지(`NOT EXISTS`). 출처 검증 단계([15번](../15-rag-pipeline/2-summary.md))에서 원천 존재를 한 번 더 확인한다.

### 2. 임베딩 모델을 문서별로 점진 교체 → 품질 붕괴, 오류는 없음 (⚠ 커리큘럼)

- 현상: 재임베딩 배치가 도는 며칠 동안 검색 결과가 이상하다.
- 보이는 형태: 진행률 25%일 때 recall@10 0.25(질의 = 새 모델), 질의 = 옛 모델이면 0.68(실험 1). 로그에 오류가 없다.
- 원인: 옛·새 벡터는 다른 공간이다(같은 문서의 A·B 코사인 평균 0.002). 차원이 같으면 계산은 되고 값만 무의미하다.
- 대처: 이중 색인 후 한 번에 전환(2절). 모델 버전 열과 버전별 부분 인덱스를 두고, 질의 임베딩 모델과 검색 필터를 같은 설정 하나에서 읽는다. 그 값은 요청 시작에 한 번 읽어 그 요청의 임베딩과 검색에 함께 넘긴다.

### 3. 재임베딩 배치 재실행 → 같은 청크 중복 (⚠ 커리큘럼)

- 현상: 같은 문장이 top-k를 여러 칸 차지해 다른 근거가 밀려난다.
- 보이는 형태: 청크 400개 배치를 두 번 돌리자 800행(실험 2).
- 원인: 키 없는 INSERT. 중간 실패 후 처음부터 다시 돌렸다.
- 대처: `(doc_id, chunk_no, model)` 키 + `ON CONFLICT`(두 번째 실행 0행), 또는 문서 단위 DELETE + INSERT 한 트랜잭션(적용 3). 중복 탐지 질의를 정기 점검에 넣는다.

### 4. 문서를 고쳤는데 옛 내용으로 답한다

- 현상: 규정 변경 후에도 며칠간 옛 숫자를 답한다.
- 보이는 형태: 원천 `updated_at`이 인덱스 `indexed_at`보다 늦은 문서가 쌓인다. 또는 청크 수가 줄었는데 옛 마지막 청크가 남아 있다.
- 원인: 변경 이벤트 유실·워커 적체, 또는 청크 단위 upsert만 해서 경계가 바뀐 옛 청크가 남았다.
- 대처: 신선도 지연 지표와 경보(적용 2), 문서 단위 통째 교체(적용 3), 이벤트 유실에 대비한 주기적 전수 대조.

### 5. 차원이 다른 모델로 바꾸자 검색이 전부 실패한다

- 현상: 배포 직후 검색 API가 500을 낸다.
- 보이는 형태: `ERROR: different vector dimensions 4 and 3`(실험 2). 또는 `vector(1536)` 열에 3072차원 삽입 오류.
- 원인: 새 모델 벡터를 옛 열·옛 인덱스에 섞었다.
- 대처: 이것은 "크게 실패하는" 쪽이라 오히려 빨리 드러난다. 새 차원은 새 열(또는 차원 미지정 열 + 모델별 식·부분 인덱스)에 두고 2절 절차로 전환한다.
- 함께 확인: pgvector는 `vector` 인덱스를 2,000차원까지만 지원한다(README, v0.8.7 기준). 3072차원 같은 새 모델은 `halfvec`(4,000차원까지) 인덱스나 `dimensions` 축소를 검토한다.

## 핵심 문장

- 벡터 인덱스는 원천에서 파생된 데이터다. 변경·삭제가 전파되지 않으면 옛 내용·지운 내용으로 답한다.
- 임베딩 모델이 바뀌면 공간이 바뀐다. 옛·새 벡터를 섞으면 차원이 같을 때는 오류 없이 품질만 무너진다.
- 모델 교체는 새 색인을 다 채운 뒤 질의 모델과 검색 대상을 한 번에 전환한다.
- 재임베딩 워커는 `(문서, 청크, 모델)` 키와 문서 단위 교체로 멱등하게 만든다.
- 신선도 지연·고아 청크·모델별 행 수를 지표로 둔다.

## 관련 주제·근거

- 선행
  - [15-rag-pipeline](../15-rag-pipeline/2-summary.md) — 오프라인 색인 단계
  - [data-engineering/01-system-of-record-and-derived-data](../../data-engineering/01-system-of-record-and-derived-data/2-summary.md) — 원천과 파생
- 후속·연결
  - [database/48-search-index-sync-and-reindexing](../../database/48-search-index-sync-and-reindexing/2-summary.md) — 이중 쓰기·outbox·CDC, 별칭 교체, 지연 감지
  - [data-engineering/05-change-data-capture](../../data-engineering/05-change-data-capture/2-summary.md) · [data-engineering/08-idempotent-pipelines-and-backfill](../../data-engineering/08-idempotent-pipelines-and-backfill/2-summary.md) · [data-engineering/12-data-retention-and-erasure](../../data-engineering/12-data-retention-and-erasure/2-summary.md)
  - [16-vector-index-ann](../16-vector-index-ann/2-summary.md) — 버전별 부분 인덱스, 죽은 튜플과 결과 수
  - [17-hybrid-search-and-reranking](../17-hybrid-search-and-reranking/2-summary.md) — 어휘 색인도 같이 최신으로
- 문서·논문
  - pgvector README(2026-10-08 확인) — FAQ "Can I store vectors with different dimensions in the same column?"(식·부분 인덱스), 인덱스 차원 한도(vector 2,000·halfvec 4,000), "Vacuuming"(REINDEX 먼저), Troubleshooting(죽은 튜플) <https://github.com/pgvector/pgvector>
  - OpenAI "Embeddings" 가이드(2026-10-08 확인) — text-embedding-3-small 1536·large 3072 기본 길이, `dimensions` 파라미터 <https://developers.openai.com/api/docs/guides/embeddings>
  - Lewis 외, "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", arXiv 2005.11401 (NeurIPS 2020) — 초록: 비파라미터 메모리, 지식 갱신이 열린 문제. 본문 "Index hot-swapping": 2016·2018 인덱스 교체, 70%·68% vs 12%·4% <https://arxiv.org/abs/2005.11401>
  - Kleppmann, 『Designing Data-Intensive Applications』 1판 11·12장 — 파생 데이터 재구축 [?]
- 실험 목록
  - 1. 잠재 32차원 문서 3,000·질의 200(seed 18), 모델 A·B = 서로 다른 무작위 직교 투영(64차원) — 진행률별 섞인 인덱스 recall@10(질의 A·B), 버전 필터, 이중 색인(호스트 Python 3.12.3 표준 라이브러리)
  - 2. PostgreSQL 17.11 + pgvector 0.8.7(Docker `pgvector/pgvector:pg17`) — 차원 혼합 오류, 같은 차원 혼합, 모델별 식·부분 HNSW 인덱스의 `EXPLAIN`, 키 없는 재실행 vs `ON CONFLICT`, 외래 키 유무별 삭제 전파와 고아 탐지
  - 3. 적용 2 신선도 질의의 `max(indexed_at)` vs `min(indexed_at)` — 옛 청크가 남은 문서 1·미반영 문서 2(PostgreSQL 17.11, Docker `pgvector/pgvector:pg17`)
