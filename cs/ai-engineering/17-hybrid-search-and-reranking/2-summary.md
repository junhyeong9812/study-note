# ai-engineering/17-hybrid-search-and-reranking — 하이브리드 검색: BM25 + 벡터, RRF 합성, 재순위 — 정리 (힌트)

## 해결하는 문제

어휘 검색과 벡터 검색은 서로 다른 질의에서 실패한다.

```text
  질의 "E-1277 오류"           어휘(BM25): 코드 E-1277이 든 문서를 정확히 찾는다
                              밀집(벡터): "오류 코드에 관한 문서"는 찾지만 1277인지 1196인지 흐려진다

  질의 "페이 거절 방법"         어휘(BM25): 문서에는 "결제 실패"라고 적혀 있다 → 겹치는 단어가 없다
  (문서: "결제 실패 안내")     밀집(벡터): 뜻이 같다는 것을 안다 → 찾는다
```

- *어휘 검색(lexical search)*: 질의 단어가 문서에 그대로 나오는지로 점수를 매긴다. 대표가 BM25다. 식·파라미터는 [database/46](../../database/46-full-text-search-and-analyzers/2-summary.md) 6절이 단일 출처다.
- *밀집 검색(dense retrieval)*: 질의와 문서를 임베딩 벡터로 바꿔 코사인·내적으로 찾는다([15](../15-rag-pipeline/2-summary.md)·[16번](../16-vector-index-ann/2-summary.md)).
- *하이브리드 검색*: 둘을 함께 돌려 결과를 합친다.
- Anthropic "Contextual Retrieval"(2024-09-19): 임베딩은 의미 관계를 잘 잡지만 "Error code TS-999" 같은 **정확 일치**를 놓칠 수 있어 BM25를 함께 쓴다고 적는다.

쉬운 예: 도서관 사서 둘에게 같은 부탁을 한다.
- 한 사서는 색인 카드를 글자 그대로 찾는다. 책 번호는 정확하지만 "비슷한 뜻"은 모른다.
- 다른 사서는 내용을 이해하고 비슷한 책을 권한다. 번호는 자주 헷갈린다.
- 두 사람의 추천 목록을 하나로 합쳐야 한다. 한 사람은 100점 만점, 다른 사람은 1점 만점으로 매겼다.

똑같은 구조다.\
**척도가 다른 두 점수를 어떻게 합칠 것인가**, 그리고 합친 뒤 **누가 최종 순서를 정하나(재순위)**가 이 주제다.

실무 예:
- 고객센터 검색: "결제 오류 E-4021"처럼 코드와 자연어가 섞인 질의.
- 사내 문서 검색: 제품 번호·티켓 번호로 찾는 질의와 "배포 롤백 절차" 같은 질의가 섞인다.

## 동작·원리

### 1. 점수를 그대로 더하면 척도가 큰 쪽이 이긴다

```text
  같은 질의 하나의 점수 분포 (실험 1)
  BM25    최고 2.30   (범위가 질의·말뭉치마다 다르고 고정된 상한이 없다)
  코사인  범위 [-0.11, 0.74]

  BM25 + 코사인 → 순위를 사실상 BM25가 정한다
```

- BM25는 idf × 포화 tf의 합이라 질의 용어 수·말뭉치 통계에 따라 범위가 바뀐다([database/46](../../database/46-full-text-search-and-analyzers/2-summary.md)). 코사인은 −1~1이다.
- min-max 정규화(질의마다 0~1로 펴기)는 척도를 맞추지만, 한쪽 목록의 점수 분포가 납작하거나 이상값이 있으면 순위가 크게 흔들린다(해석).

### 2. RRF — 점수 대신 순위로 합친다

```text
  RRFscore(d) = Σ  1 / (k + r(d))       r(d) = 목록 안에서 d의 순위(1부터), 목록에 없으면 더하지 않음(*)
               목록

  k = 60일 때
   순위 1 → 1/61 = 0.0164      순위 2 → 0.0161      순위 10 → 0.0143      순위 50 → 0.0091

  문서     BM25 순위   밀집 순위   RRF
  A           1           —       0.0164              ← 한 목록에서만 1위
  B           9           2       0.0145 + 0.0161 = 0.0306   ← 두 목록 모두 상위권
```

- (*) 원 논문은 각 순위를 문서 집합 전체의 순열로 둔다. 상위 N건만 넘기는 구현에서 "목록에 없으면 0"으로 처리하는 것은 그 관례다(실험 1의 "각 상위 50" 행).
- *RRF(reciprocal rank fusion)*: Cormack·Clarke·Büttcher(SIGIR 2009)의 식. 점수 척도를 버리고 순위만 쓰므로 척도 문제가 사라진다.
  - 원 논문: "k = 60 was fixed during a pilot investigation" — k = 60은 예비 조사에서 정해 고정한 값이다.
- 성질: 1/(k + r)은 순위에 따라 완만하게 줄어든다. 그래서 **두 목록에 모두 상위권으로 든 문서**가 한 목록에서만 1위인 문서를 이길 수 있다(위 표의 B > A).
  - 이 성질이 장점(합의)이자 약점(한쪽 전문 검색기의 확신을 버림)이다. 실험 1에서 둘 다 보인다.

### 3. 재순위 — 후보를 비싼 모델로 다시 매긴다

```text
  1단계(값싼 검색, 수백만 건 대상)      2단계(비싼 재순위, 후보 N건만)
  BM25 top-50 ─┐
               ├─ RRF → 후보 N건 ──→ 교차 인코더: (질의, 문서) 쌍마다 점수 ──→ 최종 top-k
  벡터 top-50 ─┘                       N이 작으면 후보 밖 정답은 영영 못 살린다
```

- *양방향 인코더(bi-encoder)*: 질의와 문서를 **따로** 벡터로 만든다. 문서 벡터를 미리 계산해 색인할 수 있어 빠르다([16번](../16-vector-index-ann/2-summary.md)의 벡터 검색).
- *교차 인코더(cross-encoder)*: 질의와 문서를 **함께** 한 입력으로 넣어 관련도 점수를 낸다. 쌍마다 모델을 돌려야 해 느리므로 후보에만 쓴다.
  - Nogueira–Cho 본문 "Method": 질의를 문장 A, 문단을 문장 B로 이어 BERT에 넣고(질의 최대 64토큰, 합쳐 512토큰), `[CLS]` 벡터로 관련 확률을 낸다. 문단마다 따로 계산해 그 확률로 순위를 매긴다. 같은 글은 BM25 같은 값싼 1단계 뒤의 2단계로 이 재순위를 둔다.
  - Nogueira–Cho(arXiv 1901.04085) 초록: BERT를 질의 기반 문단 재순위에 쓰는 단순한 재구현으로 MS MARCO 문단 검색 리더보드 1위, 이전 최고 대비 MRR@10 27%(상대) 향상.
- Anthropic "Contextual Retrieval": 맥락 임베딩 + 맥락 BM25에 재순위를 더하면 top-20 검색 실패율이 67% 줄었다고 보고한다(재순위 없이 49%).
- pgvector README "Hybrid Search": PostgreSQL 전문 검색과 함께 쓰고, RRF나 교차 인코더로 결과를 합치는 예제를 링크한다.

### 실험 1: 점수 합 vs 정규화 합 vs RRF, 질의 유형별

- 말뭉치(합성): 지원 문서 300편. 문서마다 개념 2개(결제·실패·환불 등 10개 중)를 동의어 3개 중 하나로 쓰고, 공통 단어 5개와 고유 오류 코드 `E-1000`~`E-1299` 하나를 넣었다. seed 17.
- 어휘 검색: [database/46](../../database/46-full-text-search-and-analyzers/2-summary.md)의 Lucene BM25 식(k1 = 1.2, b = 0.75)을 그대로 구현.
- 밀집 검색 **모형**: 실제 임베딩 모델이 아니다. 동의어를 같은 개념 벡터(64차원)로 묶고, 단어마다 고정 성분을 조금 섞었다. 오류 코드는 모두 "코드" 개념 하나로 묶여 개별 성분만 약하게 남는다 — "뜻은 알고 번호는 흐린" 검색기를 흉내 낸다.
- 질의 세 유형
  - 코드: `[E-1277, 오류, 문의]` — 정답 = 그 코드의 문서 1건(60개)
  - 바꿔 말함: 문서에 안 쓰인 동의어로 개념 쌍을 물음 — 정답 = 같은 개념 쌍 문서 전부(평균 6.6건, 40개)
  - 섞임: 코드 + 다른 동의어로 쓴 그 문서의 개념 — 정답 1건(60개)
- RRF는 각 검색기의 상위 50(BM25는 점수 > 0인 문서만)을 합쳤다.

(실험, 호스트 Python 3.12.3 표준 라이브러리, 3회 실행 출력 동일, 2026-10-08)

```text
(각 칸 = recall@10 / MRR)
문서 300, 섞인 질의 60, 코드 질의 60, 바꿔 말한 질의 40, 평균 정답 수(바꿔 말한) 6.6
예: 질의 ['E-1277', '오류', '문의'] → BM25 최고 2.30, 코사인 최고 0.74, 코사인 범위 [-0.11, 0.74]
BM25                 | 코드 1.00 / 1.00 | 바꿔 말함 0.15 / 0.50 | 섞임 1.00 / 0.75
밀집(코사인)              | 코드 0.17 / 0.11 | 바꿔 말함 0.99 / 1.00 | 섞임 1.00 / 0.77
점수 합 BM25+cos        | 코드 1.00 / 0.96 | 바꿔 말함 0.30 / 0.65 | 섞임 1.00 / 0.76
min-max 정규화 합        | 코드 0.85 / 0.76 | 바꿔 말함 0.37 / 0.76 | 섞임 1.00 / 0.79
RRF k=60 (각 상위 50)   | 코드 0.33 / 0.27 | 바꿔 말함 0.40 / 0.69 | 섞임 1.00 / 0.87
RRF k=60 (전체 순위)     | 코드 0.35 / 0.27 | 바꿔 말함 0.40 / 0.69 | 섞임 1.00 / 0.87
점수 합: 상위 10 중 BM25 상위 10과 겹침 평균 8.1개, 밀집 상위 10과 겹침 평균 2.7개
RRF k=60 (각 상위 50): 상위 10 중 BM25 상위 10과 겹침 평균 5.2개, 밀집 상위 10과 겹침 평균 4.7개
```

- *MRR(mean reciprocal rank)*: 질의마다 첫 정답 순위의 역수(1위 = 1, 2위 = 0.5)를 평균한 값.
- 관찰 1(밀집만 쓰면): 코드 질의 recall@10이 0.17이다. 정확 일치 질의를 놓친다. 반대로 BM25는 바꿔 말한 질의에서 0.15다.
- 관찰 2(점수를 그대로 더하면): 상위 10 중 평균 8.1개가 BM25 상위 10과 같다. 바꿔 말한 질의는 0.30으로, 밀집 단독(0.99)의 장점이 거의 사라졌다. 척도가 큰 BM25가 순위를 독점한다.
- 관찰 3(RRF): 두 신호가 모두 맞는 **섞인 질의에서 MRR 0.87로 가장 높다.** 상위 10이 두 목록에서 고르게 온다(5.2개·4.7개).
- 관찰 4(RRF의 약점): 코드 질의에서 0.33이다. BM25는 60개 모두 정답을 1위에 놓았는데, 융합 뒤 정답 순위 중앙값은 23위였다(추가 진단 출력, 아래).
- 이 모형의 두 검색기는 각자 한 유형에만 강하도록 일부러 극단적으로 만들었다. 실제 검색기는 두 신호가 부분적으로 겹친다. 숫자보다 **경향**을 본다.

(같은 환경, RRF 코드 질의 진단)

```text
코드 질의 60개: 정답의 BM25 순위 = 1 (전부), 밀집 상위 50 안에 든 경우 20/60, 그때 밀집 순위 중앙값 9.0
RRF 융합 뒤 정답 순위 중앙값 23.0, 최대 27
예: ['E-1277', '오류', '문의'] 정답 277
  doc 196: BM25 순위 9, 밀집 순위 2, RRF 0.0306, 단어 ['안내', '화면', '오류', '문의', 'E-1196', '다시', '할인권', '확인']
  doc 105: BM25 순위 21, 밀집 순위 1, RRF 0.0287, 단어 ['요청', '오류', '다시', '경우', '웹', '방법', 'E-1105', '느림']
  doc 134: BM25 순위 8, 밀집 순위 17, RRF 0.0277, 단어 ['E-1134', '오류', '문의', '처리', '다시', '안내', '아이디', '요청']
  doc 277: BM25 순위 1, 밀집 순위 -, RRF 0.0164, 단어 ['늦음', '확인', 'E-1277', '다시', '아이디', '웹', '아이디', '늦음', '앱', '경우']
```

- 정답 277은 BM25 1위지만 밀집 상위 50에 없어 RRF 0.0164(=1/61)만 받았다. "오류·문의"가 든 다른 문서들은 두 목록 모두 상위권이라 0.03 안팎을 받았다. 2절 표의 A < B가 그대로 일어났다.
- recall@10 0.33 ≈ 밀집 상위 50에 정답이 든 비율(20/60)이다. 두 목록에 모두 들어야 상위로 올라온다.

### 실험 2: 재순위 후보 수

- 재순위 **모형**: 정답을 알고 잡음(표준편차 0.3)을 섞은 채점기. 교차 인코더의 품질을 흉내 내는 것이 아니라 "후보에 없는 정답은 재순위가 살릴 수 없다"만 보인다. RRF 상위 N건을 다시 매겨 상위 3건을 본다. 바꿔 말한 질의 40개, seed 170.

(실험 1과 같은 환경)

```text
재순위 후보 수 | 바꿔 말한 질의 hit@3(정답 1건 이상) | 후보 안 정답 비율 | 후보 hit@N
            3 |  0.78 |  0.18 |  0.78
            5 |  0.82 |  0.26 |  0.82
           10 |  0.88 |  0.40 |  0.88
           20 |  0.93 |  0.49 |  0.93
           50 |  1.00 |  1.00 |  1.00
```

- *후보 안 정답 비율*: 질의마다 (후보 N건에 든 정답 수 ÷ 정답 수)의 평균 = 1단계 recall@N.
- *후보 hit@N*: 후보 N건에 정답이 하나라도 든 질의의 비율. 마지막 열은 사실 점검 때 같은 스크립트에 이 열만 더해 다시 돌린 값이다(앞 세 열은 그대로 재현됐다).

- 관찰: 후보 3건(=재순위 없이 RRF 상위 3과 같은 집합)이면 0.78, 후보 50건이면 1.00이다. 재순위 뒤 hit@3의 상한은 **후보 hit@N**이다 — 이 모형은 정답을 알고 매기므로 매 행에서 상한에 닿았다.
  - 후보 안 정답 비율(recall@N)은 재순위 뒤 recall@3의 상한이지 hit@3의 상한이 아니다. 후보 3건에서 0.18 < 0.78인 것은 모순이 아니다(정답이 평균 6.6건이라 하나만 들어도 hit이다).
- 대가: 채점할 (질의, 문서) 쌍의 수 = 후보 수다. 계산량은 후보 수에 비례한다(해석 — 쌍마다 한 번 계산). 모델 호출 횟수와 지연은 배치·병렬 설정에 따라 다르다 — Sentence Transformers `CrossEncoder.predict`는 쌍 목록을 받아 `batch_size`(기본 32)씩 묶어 계산한다.

## 쓰이는 자료구조·알고리즘

- **역색인 + BM25** — 어휘 검색. [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md), 식은 [database/46](../../database/46-full-text-search-and-analyzers/2-summary.md).
- **벡터 최근접(ANN)** — 밀집 검색. [16-vector-index-ann](../16-vector-index-ann/2-summary.md)
- **RRF = 다중 목록 병합** — 목록마다 순위 → `1/(k + r)` 누적(해시맵) → 정렬. 여러 정렬 목록을 합친다는 점에서 [algorithm/11-external-sort-and-k-way-merge](../../algorithm/11-external-sort-and-k-way-merge/2-summary.md)와 닮았지만, 키가 아니라 누적 점수로 다시 정렬한다.
- **상위 k 힙** — 각 단계의 top-k. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md)
- **2단계 검색(캐스케이드)** — 싼 단계로 후보를 줄이고 비싼 단계로 정밀하게. [13번](../13-model-routing-and-fallback/2-summary.md) 라우팅의 캐스케이드와 같은 꼴이다.

## 적용 — 풀어나가는 법

### 1. 증상 → 원리 → 확인

```text
  증상                                원리                          확인
  "E-4021"로 찾으면 엉뚱한 오류 문서   밀집은 정확 일치를 흐린다      밀집 단독 vs BM25 단독 결과 비교
  하이브리드인데 벡터를 붙인 효과가    점수 합 = 척도 큰 쪽 독점      합성 결과 상위 10과 각 단독 상위 10의 겹침 수
  거의 없다
  RRF 도입 뒤 코드 검색이 나빠졌다     한 목록에만 든 1위는 1/(k+1)   정답의 목록별 순위와 융합 순위
  재순위를 붙였는데 recall이 그대로    후보 밖 정답은 못 살린다       후보 N건 안 정답 비율
```

- 진단 질의마다 `각 검색기의 상위 순위·점수 → 융합 점수 → 재순위 점수`를 함께 기록한다. 어느 단계에서 정답이 떨어졌는지 바로 보인다.

### 2. RRF 합성 (Java 21)

```java
import java.util.*;

public final class Rrf {
    // rankings: 검색기마다 문서 ID를 순위 순서대로(1위가 index 0)
    static List<String> fuse(List<List<String>> rankings, int k, int topN) {
        Map<String, Double> score = new HashMap<>();
        for (List<String> ranking : rankings) {
            for (int i = 0; i < ranking.size(); i++) {
                score.merge(ranking.get(i), 1.0 / (k + i + 1), Double::sum);   // 순위는 1부터
            }
        }
        return score.entrySet().stream()
                .sorted(Map.Entry.<String, Double>comparingByValue().reversed()
                        .thenComparing(Map.Entry.comparingByKey()))            // 동점은 ID로 고정
                .limit(topN)
                .map(Map.Entry::getKey)
                .toList();
    }
}
```

- 동점 처리를 고정해야 재실행 때 순서가 흔들리지 않는다.
- 검색기마다 상위 몇 건을 넘길지(실험은 50)가 RRF 결과를 바꾼다. 재순위 후보 수보다 크게 잡는다.

### 실험 3: 2절 표를 `Rrf.fuse`로 재현

- 입력: BM25 목록 `[A, x2, …, x8, B]`(A 1위, B 9위), 밀집 목록 `[y1, B, y3]`(B 2위), k = 60, 상위 3.

(실험, OpenJDK 21.0.12 temurin, Docker `--network none --cpus=2`, `java Rrf.java`, 2026-10-08)

```text
[B, A, y1]
```

- B(0.0306)가 A(0.0164)를 이겼다. A와 y1은 둘 다 한 목록 1위라 점수가 같고, 동점 규칙(ID 순)으로 A가 앞선다.

### 3. PostgreSQL 17 + pgvector에서 두 목록 만들기

```sql
-- 어휘 목록: 전문 검색 (ts_rank_cd는 BM25가 아니다 — database/46)
SELECT id, row_number() OVER (ORDER BY ts_rank_cd(tsv, q) DESC) AS r
FROM docs, to_tsquery('simple', replace(plainto_tsquery('simple', $1)::text, ' & ', ' | ')) q
WHERE tsv @@ q                          -- 단어를 OR로: 하나라도 맞으면 후보
ORDER BY r LIMIT 50;

-- 밀집 목록: 벡터 최근접
SELECT id, row_number() OVER (ORDER BY embedding <=> $2) AS r
FROM docs
ORDER BY embedding <=> $2 LIMIT 50;
```

- `plainto_tsquery`는 남은 단어 사이에 `&`(AND)를 넣는다(PostgreSQL 17 문서 12.3.2). 그대로 쓰면 질의 단어가 **모두** 든 문서만 후보가 된다. 실험 1의 정답 277에는 "오류·문의"가 없어 AND면 어휘 목록에서 빠진다. 위 질의는 `&`를 `|`(OR)로 바꿔 BM25처럼 "하나라도 맞으면 후보"로 만든다.
- 확인: 실험 1 진단의 문서 4건(196·105·134·277) 단어로 `docs`를 만들고 `'E-1277 오류 문의'`로 조회했다. 첫 줄은 `plainto_tsquery` 결과, `-- AND` 아래는 원래 질의(0행), `-- OR` 아래는 위 질의(`id | ts_rank_cd | r`)다.

(실험, PostgreSQL 17.11, Docker `pgvector/pgvector:pg17` — 전문 검색만, vector 확장 미사용, `psql -At`, 2026-10-08)

```text
'e' & '-1277' & '오류' & '문의'
-- AND
-- OR
196 | 0.300 | 1
134 | 0.300 | 2
105 | 0.200 | 3
277 | 0.200 | 4
```

  - `simple` 설정의 기본 파서는 `E-1277`을 `e`와 `-1277` 두 토큰으로 쪼갰다. 식별자를 통째로 맞추려면 별도 열·정확 일치 경로를 둔다(적용 4).
  - OR로 바꿔도 277은 4위였다. `ts_rank_cd`에 idf가 없어 드문 코드 토큰을 우대하지 않는다(아래 줄).
- 두 결과를 애플리케이션에서 `Rrf.fuse`로 합친다. pgvector README는 같은 방식의 Python 예제(`hybrid_search/rrf.py`)를 링크한다.
- PostgreSQL `ts_rank`·`ts_rank_cd`는 idf를 쓰지 않는다([database/46](../../database/46-full-text-search-and-analyzers/2-summary.md)). BM25가 필요하면 검색 엔진(Lucene 계열)을 쓰거나, 순위만 쓰는 RRF로 차이를 줄인다(해석).

### 4. 정확 일치 질의 보호

- 실험 1의 RRF 약점처럼, 질의가 식별자 꼴(`E-\d{4}`, 주문 번호 등)이면 어휘 결과 1위를 고정하거나 어휘 검색만 쓰는 경로를 둔다(해석 — 이 실험에서 BM25 단독이 코드 질의 1.00).
- 목록별 가중치를 둔 RRF(`w / (k + r)`)도 쓰이지만, 가중치는 평가셋으로 정한다([19번](../19-llm-evaluation/2-summary.md)).

## 장애 시나리오와 대처

### 1. BM25 점수와 코사인을 그대로 더했다 (⚠ 커리큘럼)

- 현상: 하이브리드로 바꿨는데 바꿔 말한 질의가 여전히 안 잡힌다.
- 보이는 형태: 합성 결과 상위 10의 8.1개가 BM25 상위 10과 같다. 바꿔 말한 질의 recall 0.30(밀집 단독 0.99, 실험 1).
- 원인: BM25는 범위가 질의마다 다르고 고정된 상한이 없으며(예: 최고 2.30), 코사인은 −1~1이다.
- 대처: 순위로 합친다(RRF). 점수로 합치려면 정규화 방식을 평가셋으로 검증한다.

### 2. 밀집 검색만 써서 코드·제품 번호 질의를 놓친다 (⚠ 커리큘럼)

- 현상: "E-4021"을 검색했는데 다른 오류 코드 문서가 나온다.
- 보이는 형태: 코드 질의 recall@10 0.17(실험 1의 밀집 모형).
- 원인: 임베딩은 의미를 담고 식별자의 글자 차이를 흐린다. Anthropic "Contextual Retrieval"도 같은 이유로 BM25를 결합한다.
- 대처: 어휘 검색을 함께 쓴다. 식별자 꼴 질의는 정확 일치 경로를 둔다(적용 4).

### 3. RRF 뒤 정확 일치 문서가 밀려났다

- 현상: 하이브리드 도입 후 코드 검색 품질이 BM25 단독보다 나빠졌다.
- 보이는 형태: 코드 질의 recall@10 1.00(BM25) → 0.33(RRF), 정답의 융합 순위 중앙값 23위(실험 1 진단).
- 원인: RRF는 한 목록에만 든 문서에 최대 1/(k+1)만 준다. 두 목록 모두 중간 순위인 문서가 이긴다.
- 대처: 질의 유형 판별·식별자 우선 경로, 목록별 가중치, 평가셋에서 질의 유형별로 따로 잰다.

### 4. 재순위 후보 수가 너무 작다 (⚠ 커리큘럼)

- 현상: 교차 인코더를 붙였는데 정답 문서가 끝내 안 나온다.
- 보이는 형태: 후보 3건이면 hit@3 0.78, 50건이면 1.00(실험 2). 후보 3건에 정답이 하나라도 든 질의가 78%뿐이다(후보 hit@N 0.78).
- 원인: 재순위는 받은 후보 안에서만 순서를 바꾼다.
- 대처: 1단계 후보를 넉넉히(실험은 50) 넘기고, 재순위 지연 예산으로 상한을 정한다. 1단계 후보의 hit@N(재순위 뒤 hit@k의 상한)과 recall@N(재순위 뒤 recall@k의 상한)을 별도 지표로 둔다.

## 핵심 문장

- 어휘 검색은 정확 일치에, 밀집 검색은 바꿔 말한 질의에 강하다. 하이브리드는 둘의 실패를 서로 메운다.
- BM25 점수와 코사인은 척도가 달라 그대로 더하면 큰 쪽이 순위를 독점한다.
- RRF는 순위의 역수 `1/(k + r)`(원 논문 k = 60)를 더한다. 척도 문제는 없지만 두 목록에 모두 든 문서를 우대한다.
- 재순위는 후보 안에서만 순서를 바꾼다. 1단계 후보 N건의 hit@N·recall@N이 최종 hit@k·recall@k의 상한이다.
- 하이브리드의 효과는 질의 유형마다 다르다. 평가셋을 유형별로 나눠 잰다.

## 관련 주제·근거

- 선행
  - [15-rag-pipeline](../15-rag-pipeline/2-summary.md) — 근거 있는 답은 검색이 근거를 찾아와야 나온다
  - [16-vector-index-ann](../16-vector-index-ann/2-summary.md) — 밀집 목록을 만드는 인덱스
  - [database/46-full-text-search-and-analyzers](../../database/46-full-text-search-and-analyzers/2-summary.md) — BM25 식·분석기, PostgreSQL `ts_rank`는 BM25가 아님
- 후속·연결
  - [18-index-freshness-and-reembedding](../18-index-freshness-and-reembedding/2-summary.md) — 어휘·벡터 색인을 함께 최신으로
  - [19-llm-evaluation](../19-llm-evaluation/2-summary.md) — 질의 유형별 평가셋, 가중치 결정
  - [data-structure/32-inverted-index](../../data-structure/32-inverted-index/2-summary.md)
- 논문·문서
  - Cormack, Clarke, Büttcher, "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods", SIGIR '09 — `RRFscore(d) = Σ 1/(k + r(d))`, k = 60 <https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf>
  - Robertson, Zaragoza, "The Probabilistic Relevance Framework: BM25 and Beyond", Foundations and Trends in IR 3(4) 333–389 (2009) <https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf>
  - Nogueira, Cho, "Passage Re-ranking with BERT", arXiv 1901.04085 (2019) — 초록·"Method" 절(2026-10-08 확인) <https://arxiv.org/abs/1901.04085>
  - Reimers, Gurevych, "Sentence-BERT", arXiv 1908.10084 (EMNLP 2019) — 문장 임베딩(양방향 인코더) <https://arxiv.org/abs/1908.10084>
  - Anthropic, "Contextual Retrieval" (2024-09-19, 2026-10-08 확인) — 정확 일치를 놓치는 임베딩 + BM25, 재순위 결합 시 실패율 67% 감소 <https://www.anthropic.com/engineering/contextual-retrieval>
  - PostgreSQL 17 문서 12.3.2 "Parsing Queries" — `plainto_tsquery`는 남은 단어 사이에 `&`(AND)를 넣는다(2026-10-08 확인) <https://www.postgresql.org/docs/17/textsearch-controls.html>
  - Sentence Transformers `CrossEncoder.predict(inputs, …, batch_size=32, …)` API(2026-10-08 확인) <https://sbert.net/docs/package_reference/cross_encoder/model.html>
  - pgvector README "Hybrid Search"(2026-10-08 확인) — 전문 검색과 함께, RRF·교차 인코더 예제 링크 <https://github.com/pgvector/pgvector>
- 실험 목록(1·2는 호스트 Python 3.12.3 표준 라이브러리, 2026-10-08)
  - 1. 합성 지원 문서 300편(seed 17), BM25(Lucene 식) + 개념 밀집 모형(64차원) — 점수 합·min-max 합·RRF(k = 60)의 질의 유형별 recall@10·MRR, 상위 10 겹침, RRF 코드 질의 진단
  - 2. 재순위 모형(정답 + 잡음, seed 170) — 후보 수 3~50별 hit@3·후보 안 정답 비율(recall@N)·후보 hit@N
  - 3. Java 21 `Rrf.fuse`로 2절 표(A·B) 재현(OpenJDK 21.0.12 temurin, Docker `--network none`)
  - 4. 적용 3의 어휘 목록 SQL — `plainto_tsquery` AND vs `&`→`|` OR, 문서 4건(PostgreSQL 17.11, Docker `pgvector/pgvector:pg17`)
