# 특화·클라우드 네이티브 DB (2015 ~ 현재)

> 원본: `~/project/database-history/05-특화-현대-DB.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-18).\
> 연도·인명·논문명·표준번호·코드는 원문 그대로다.\
> 용어 블록의 「예:」, 「대가는 무엇인가」, 트레이드오프 표는 원문에 없는 보충 설명이다.\
> 원문이 절마다 반복해 쓴 소제목(「왜·언제 생겼나」·「주요 시스템」·「영향」)은 이 문서의 골격으로 대체했다.

## 한눈에 — 쉽게 말하면

**특화 DB = 공구함에 드라이버만 있던 시절이 끝나고, 망치·렌치·핀셋이 생긴 것.**

- 예전에는 무슨 데이터든 관계형 DB 하나에 다 넣었다.\
  못을 박을 때도 드라이버 손잡이로 두드리던 셈이다.
- 그런데 데이터의 모양이 달라졌다.\
  1초에 수십만 건 쏟아지는 센서 값, "친구의 친구의 친구"를 따라가는 관계망, 뜻으로 검색해야 하는 문장 — 모양이 다르면 필요한 공구도 다르다.
- 그래서 모양마다 전용 엔진이 생겼다.\
  시계열·그래프·검색·벡터가 각각 한 칸씩 차지했다.
- 동시에 반대 방향의 힘도 있다.\
  드라이버(PostgreSQL)에 망치 머리를 끼워 파는 사람들이 나타났다 — 확장(extension) 노선이다.

```text
[ 하나로 다 하던 시절 ]          [ 워크로드마다 다른 엔진 ]
+------------------+             시계열 → InfluxDB / TimescaleDB
|                  |             그래프 → Neo4j
|  관계형 DB 하나   |   -------> 검색   → Elasticsearch
|  (모든 워크로드)  |             벡터   → Qdrant / pgvector
|                  |             분석   → BigQuery / Snowflake / DuckDB
+------------------+
 "하나로 다 한다"                "모양에 맞는 것을 고른다" (폴리글랏 퍼시스턴스)
```

이 그림이 **똑같은 구조로** 이 시대의 정의다.\
데이터의 모양마다 저장 구조와 인덱스가 달라야 하므로, 엔진 자체가 갈라졌다.

> **폴리글랏 퍼시스턴스(polyglot persistence)** — 한 서비스 안에서 데이터 종류마다 다른 DB를 골라 쓰는 방식.\
> 예: 주문은 PostgreSQL, 로그 검색은 Elasticsearch, 추천 벡터는 Qdrant에 둔다.

> **워크로드(workload)** — 시스템에 실제로 들어오는 일의 성격(읽기·쓰기 비율, 질의 모양, 데이터 크기).\
> 예: "초당 10만 건 쓰기 + 시간 범위 평균 조회"가 시계열 워크로드다.

## 시대적 배경

*(이 편의 「시대 배경」에 해당한다)*

2010년대 초의 NoSQL 운동(MongoDB·Cassandra·HBase)은 "관계형 모델이 모든 워크로드에 맞지는 않는다"는 명제를 대중화했다.\
그러나 NoSQL은 주로 **확장성(scalability)** 문제, 즉 단일 노드를 넘어서는 수평 확장에 대한 응답이었다.

2015년 이후의 흐름은 결이 다르다.\
이제 질문은 "어떻게 더 크게 확장하나"가 아니라 "**이 특정한 데이터의 모양과 질의 패턴에 가장 잘 맞는 엔진은 무엇인가**"로 옮겨갔다.

```text
 2000년대 질문                   2015년 이후 질문
+-------------------------+      +-----------------------+
| "서버 한 대로 부족하다" |      | "이 데이터의 모양에   |
|  → 어떻게 나눠 담지?    |      |   맞는 엔진이 뭐지?"  |
|  → 샤딩·복제·CAP        |      |  → 시계열·그래프·벡터 |
+-------------------------+      +-----------------------+
 답: 규모(scale)                 답: 특화(specialization)
```

이 분화를 밀어붙인 동력은 세 가지다.

1. **데이터의 모양이 다양해졌다.**\
   IoT·모니터링이 폭증시킨 시계열, 소셜·추천·사기 탐지의 관계망(그래프), 전문(full-text) 검색, 그리고 2022년 말 LLM이 촉발한 임베딩 벡터.\
   각각은 행(row)과 조인(join)에 최적화된 B-tree 기반 RDBMS로는 비효율적이다.\
   시계열의 고빈도 삽입, 그래프의 다단계 순회(traversal), 벡터의 근사 최근접 이웃(ANN) 검색은 저장 구조와 인덱스 자체가 달라야 한다.

2. **클라우드가 하드웨어의 제약을 풀었다.**\
   온프레미스 DB는 스토리지와 컴퓨트가 같은 서버에 묶여 있어, 디스크가 부족하면 CPU까지 같이 사야 했다.\
   클라우드의 무한에 가까운 네트워크 스토리지(S3 등)는 이 둘을 **물리적으로 분리**(disaggregation)할 수 있게 했고, 이것이 Aurora·Snowflake·BigQuery로 이어지는 "클라우드 네이티브" 설계의 핵심 원리가 되었다.

3. **운영 부담을 0으로 만들려는 압력.**\
   서버리스(serverless) 모델은 "쓰지 않을 때는 비용도 0, 트래픽이 오면 자동 확장"을 약속하며, scale-to-zero·즉시 브랜칭 같은 개발자 경험(DX) 중심 기능으로 진화했다.

> **온프레미스(on-premise)** — 클라우드가 아니라 회사가 직접 산 서버에 올려 운영하는 방식.\
> 예: 사옥 지하 전산실의 랙에 DB 서버를 두고 쓰는 것.

> **스토리지 / 컴퓨트** — 데이터를 담아 두는 부분과, 질의를 계산하는 부분.\
> 예: 디스크 용량이 스토리지, 질의를 푸는 CPU·메모리가 컴퓨트다.

아래는 이 시대를 정의한 특화 DB 계열과 클라우드 네이티브 아키텍처를 차례로 다룬다.

---

## 무엇이 바뀌었나

### 1. 시계열 데이터베이스 (Time-Series DB)

**무엇** — 타임스탬프가 붙은 채 끝없이 쌓이기만 하는 데이터를 위한 전용 엔진.

**언제·왜 생겼나** — 2010년대 중반 클라우드 인프라 모니터링(메트릭·로그), DevOps의 관측성(observability), 그리고 IoT 센서가 폭발하면서 **타임스탬프로 인덱싱된 append-only 데이터**가 급증했다.

이 데이터는 세 가지 특성을 가진다.

- 초당 수십만 건의 지속적 고빈도 삽입.
- 과거 데이터는 거의 갱신되지 않음(immutable).
- "지난 1시간의 평균을 1분 단위로" 같은 시간 범위 집계 스캔이 지배적.

범용 RDBMS의 행 기반 저장과 B-tree는 이 패턴에 최적화돼 있지 않다.

```text
 [ 일반 테이블에 넣으면 ]            [ 시계열 엔진 ]
 한 덩어리 테이블                    시간 단위로 자동 분할(청크)
+-----------------------------+      +---------------------------+
| 3년치 모든 행이 한 인덱스에 |      | 9/15   9/16   9/17   9/18 |
| B-tree 가 계속 커지고       |      | (하루치 = 청크 하나)      |
| 삽입마다 무작위 쓰기        |      | 최근 청크만 메모리에      |
+-----------------------------+      +---------------------------+
 → 삽입도 조회도 같이 무거워진다     → "어제 하루"는 청크 하나만 스캔
```

이 대비의 결론 — 시간이 축인 데이터는 시간으로 잘라 두는 것만으로 삽입과 조회가 동시에 싸진다.

> **append-only** — 기존 행을 고치지 않고 새 행을 뒤에 붙이기만 하는 쓰기 패턴.\
> 예: 온도 센서는 1초마다 새 값을 추가할 뿐, 어제 측정값을 고치지 않는다.

> **관측성(observability)** — 시스템 바깥에서 들어오는 신호(메트릭·로그·추적)만 보고 안에서 무슨 일이 벌어지는지 알아내는 능력.\
> 예: CPU 그래프와 에러 로그만으로 "어제 3시 장애는 캐시 미스 때문"이라고 짚어내는 것.

**주요 시스템**

- **InfluxDB** (2013, InfluxData/구 Errplane, Y Combinator) — 시계열에 특화한 커스텀 NoSQL 엔진.\
  데이터 모델은 measurement + **태그셋(tag set)** + 필드 + 타임스탬프 구조이며, 자체 질의 언어 InfluxQL(SQL 유사) 이후 함수형 언어 Flux를 도입했다.\
  TSM(Time-Structured Merge Tree)이라는 LSM 변형 스토리지로 고빈도 쓰기와 시간 압축을 처리한다.
- **TimescaleDB** (2017, Timescale/현 Tiger Data) — **PostgreSQL 확장**(extension)으로 구현된 시계열 DB.\
  시계열 테이블을 시간(과 공간) 기준으로 자동 분할하는 **하이퍼테이블(hypertable)** 추상으로, 사용자에게는 하나의 테이블처럼 보이지만 내부적으로 다수의 청크(chunk)로 파티셔닝된다.\
  PostgreSQL 위에 올라타 SQL·조인·트랜잭션·생태계를 그대로 쓴다는 점이 InfluxDB와의 핵심 대비다.

```sql
-- TimescaleDB: 일반 테이블을 하이퍼테이블로 전환하면 시간 기준 자동 분할
CREATE TABLE metrics (
    time        TIMESTAMPTZ NOT NULL,
    device_id   TEXT,
    cpu         DOUBLE PRECISION
);
SELECT create_hypertable('metrics', 'time');

-- 연속 집계(continuous aggregate): 1시간 버킷 평균을 미리 구체화
SELECT time_bucket('1 hour', time) AS bucket,
       device_id,
       avg(cpu)
FROM metrics
WHERE time > now() - INTERVAL '1 day'
GROUP BY bucket, device_id;
```

코드 읽는 법 — `create_hypertable` 한 줄이 평범한 테이블을 시간 기준 자동 분할 테이블로 바꾼다.\
아래 질의의 `time_bucket('1 hour', time)`은 값을 1시간 칸으로 묶는 함수이고, 그 결과를 미리 계산해 두는 것이 연속 집계다.

**어디에 자리 잡았나** — 시계열은 가장 빠르게 성장한 DB 카테고리 중 하나가 되었다.

**대가는 무엇인가 / 남긴 갈림길** — 설계 철학의 분기가 여기서 선명해졌다.\
InfluxDB의 "전용 엔진을 새로 짓는다" 대 TimescaleDB의 "검증된 PostgreSQL 위에 특화 계층을 얹는다"는, 이후 모든 특화 DB가 반복하게 되는 근본 선택지(green-field vs. extension)다.\
후자의 노선은 뒤의 pgvector에서 다시 등장한다.

---

### 2. 그래프 데이터베이스의 성숙 (Neo4j)

**무엇** — 관계(연결)를 조인이 아니라 포인터로 저장해, 여러 단계를 따라가는 질의를 싸게 만든 엔진.

**언제·왜 생겼나** — 관계(relationship) 자체가 1급 시민인 데이터에서는 "친구의 친구의 친구"처럼 여러 단계의 연결을 따라가는 질의가 핵심이다.\
소셜 네트워크, 추천, 사기 탐지, 지식 그래프, 네트워크 토폴로지가 그런 데이터다.\
RDBMS에서 이는 매 단계마다 비싼 조인(self-join)을 쌓는 일이라, 깊이가 깊어질수록 성능이 기하급수적으로 나빠진다.

```text
[ RDBMS 3단계 친구 찾기 ]            [ 그래프 DB 3단계 순회 ]
friend 테이블을 3번 self-join         Alice ─▶ Bob ─▶ Carol ─▶ Dave
                                       포인터를 세 번 따라간다
비용 ∝ 테이블 전체 크기                비용 ∝ 실제로 밟은 노드 수
(사용자 1000만 명이면 매 조인이 무겁다) (친구가 50명이면 50 근처)
```

이 대비의 결론 — 그래프 DB는 노드 간 연결을 물리적 포인터로 저장(index-free adjacency)해, 순회 비용을 그래프 크기가 아니라 **탐색하는 부분의 크기에 비례**하게 만든다.

> **index-free adjacency** — 이웃을 찾을 때 인덱스를 뒤지지 않고, 노드가 들고 있는 포인터를 바로 따라가는 저장 방식.\
> 예: 주소록에서 이름을 검색하는 대신, 명함 뒷면에 적힌 다음 사람 연락처로 바로 넘어가는 것.

> **순회(traversal)** — 그래프에서 연결선을 따라 노드에서 노드로 이동하며 답을 모으는 일.\
> 예: "Alice의 동료가 좋아한 제품"은 동료 관계 한 번, 좋아요 관계 한 번을 따라가는 2단계 순회다.

**주요 시스템**

- **Neo4j** (창업 2007, 스웨덴, Emil Eifrem 등) — 속성 그래프(property graph) 모델의 사실상 표준.\
  2011년 Neo4j 1.4와 함께 선언적 그래프 질의 언어 **Cypher**가 처음 공개되었다.\
  2015~현재 구간에서 Neo4j는 클러스터링(Causal Clustering)·분석 라이브러리(GDS, Graph Data Science)·클라우드 관리형 서비스(AuraDB)를 갖추며 **연구 프로토타입에서 엔터프라이즈 플랫폼으로 성숙**했다.\
  2024년 이후에는 LLM의 지식 그래프 기반 RAG(GraphRAG)와 결합하며 새로운 수요를 얻었다.

```cypher
// Cypher: ASCII-아트로 그래프 패턴을 직접 표현
// "Alice와 함께 일하는 사람들이 좋아하는 제품" — 2-hop 순회
MATCH (a:Person {name: 'Alice'})-[:WORKS_WITH]->(colleague:Person)
      -[:LIKES]->(p:Product)
RETURN colleague.name, p.name
```

코드 읽는 법 — 괄호 `()`가 노드, 대괄호 화살표 `-[:LIKES]->`가 관계다.\
질의문의 생김새가 그리려는 그림과 그대로 닮았다는 것이 Cypher의 발상이다.

**왜 이게 나은가** — Cypher의 패턴 매칭 문법(`()-[]->()`)은 직관성으로 주목받아, 이후 **GQL**(Graph Query Language)이라는 ISO 국제 표준(2024년 제정)의 기반이 되었다.\
SQL 이후 ISO가 표준화한 최초의 새 질의 언어다.

**어디에 자리 잡았나** — 그래프 DB는 RDBMS를 대체하기보다, 관계 중심 워크로드를 위한 폴리글랏 퍼시스턴스의 한 축으로 자리 잡았다.

---

### 3. 검색 엔진 (Elasticsearch)

**무엇** — "단어 → 그 단어가 든 문서" 방향으로 색인을 뒤집어 두고, 관련도 순으로 결과를 주는 엔진.

**언제·왜 생겼나** — 전문 검색(full-text search)은 `LIKE '%...%'`로는 도저히 감당할 수 없는 별도의 문제 영역이다.\
형태소 분석, 관련도 점수(BM25/TF-IDF), 패싯, 오타 보정이 모두 여기에 속한다.\
색인을 역(inverted index)으로 구성해 "단어 → 문서" 매핑으로 검색하는 Apache Lucene이 이 영역의 엔진이었지만, Lucene은 라이브러리일 뿐 분산·운영을 제공하지 않았다.

```text
[ LIKE '%사과%' ]                  [ 역색인(inverted index) ]
문서를 처음부터 끝까지 다 읽는다     단어별로 문서 번호를 미리 모아 둔다
문서1 ... 문서2 ... 문서3 ...        "사과" → [1, 7, 12]
                                    "배"   → [3, 7]
비용 ∝ 전체 문서 크기                비용 ∝ 그 단어의 문서 목록 길이
관련도 순서 없음                     BM25 점수로 정렬 가능
```

이 대비의 결론 — 검색이 빠른 이유는 더 빨리 읽어서가 아니라, **읽는 방향을 미리 뒤집어 놨기** 때문이다.

> **역색인(inverted index)** — 문서에서 단어를 찾는 대신, 단어에서 문서를 찾도록 뒤집어 만든 색인.\
> 예: 책 뒤의 "찾아보기"가 바로 역색인이다 — 단어를 보면 몇 쪽인지 바로 안다.

> **BM25 / TF-IDF** — 검색어와 문서가 얼마나 잘 맞는지 점수를 매기는 방식.\
> 예: 흔한 단어("그리고")는 점수를 낮게, 드문 단어("역색인")는 높게 쳐서 순위를 정한다.

**주요 시스템**

- **Elasticsearch** (2010, Shay Banon) — Lucene을 분산·복제·샤딩으로 감싸고, 스키마 없는 JSON 문서와 RESTful API로 노출한 검색 엔진.\
  Logstash·Kibana와 묶인 **ELK 스택**은 로그 분석·관측성의 표준이 되었다.\
  텍스트 검색을 넘어 집계(aggregation) 분석 엔진으로도 널리 쓰였다.

#### 영향과 벡터로의 진화

**왜 이게 나은가 / 그다음** — Elasticsearch의 중요성은 **2022년 이후 벡터 검색을 흡수**했다는 데 있다.\
2022~2023년 Elasticsearch·OpenSearch·Redis·PostgreSQL 같은 기존 강자들이 차례로 벡터(임베딩) 검색을 추가하면서, "전통적 키워드 검색(BM25)"과 "의미 기반 벡터 검색"을 결합한 **하이브리드 검색**이 표준 패턴이 되었다.\
즉 검색 엔진 카테고리는 다음 절의 벡터 DB와 경계가 흐려지며 수렴하고 있다.

---

### 4. 벡터 데이터베이스 (2019 ~, 2023 RAG 붐)

> 이 시대 특화 DB의 가장 극적인 사건. 한 줄로 요약하면: **LLM이 모든 데이터를 고차원 벡터로 바꿔놓자, 그 벡터를 저장하고 "의미적으로 가까운 것"을 빠르게 찾는 전용 DB가 폭발적으로 필요해졌다.**

**무엇** — 문장·이미지를 숫자 목록으로 바꿔 놓고, "뜻이 가까운 것"을 거리로 찾아 주는 엔진.

**언제·왜 생겼나** — 딥러닝 임베딩 모델은 텍스트·이미지·오디오를 수백~수천 차원의 부동소수점 벡터로 변환한다.\
이 공간에서 **벡터 간 거리(코사인 유사도 등)가 의미적 유사도**에 대응한다.\
따라서 "이 질문과 의미가 가장 가까운 문서 10개"를 찾는 문제는 고차원 공간의 **최근접 이웃(nearest neighbor) 검색**이 된다.\
정확한 최근접 이웃은 차원의 저주로 사실상 풀 수 없어, **근사 최근접 이웃(ANN, Approximate Nearest Neighbor)** 알고리즘이 핵심 인덱스가 된다.\
특히 그래프 기반 **HNSW**(Hierarchical Navigable Small World)와 IVF, 그리고 더 최근의 DiskANN이 그것이다.

```text
키워드 검색과 벡터 검색은 찾는 기준이 다르다

질문: "환불 정책이 어떻게 되나요?"

  키워드(BM25)                     벡터(임베딩 거리)
  "환불"·"정책" 글자가 든 문서      뜻이 가까운 문서
  → "환불 정책 안내"  (찾음)        → "환불 정책 안내"    (찾음)
  → "반품 규정"      (못 찾음)      → "반품 규정"        (찾음)
                                      글자는 달라도 벡터가 가깝다
```

이 대비의 결론 — 벡터 검색은 글자가 아니라 **뜻의 가까움**으로 찾기 때문에, 표현이 다른 문서도 걸린다.

> **임베딩(embedding)** — 문장·이미지를 그 뜻이 위치로 나타나도록 숫자 목록(벡터)으로 바꾼 것.\
> 예: "강아지"와 "개"의 벡터는 서로 가깝고, "환율"의 벡터는 멀리 떨어진다.

> **차원의 저주(curse of dimensionality)** — 차원이 수백·수천으로 커지면 모든 점이 고만고만하게 멀어져, 정확한 최근접 이웃 찾기가 전수 비교와 다름없어지는 현상.\
> 예: 1536차원에서 "정확히 가장 가까운 하나"를 보장하려면 사실상 전부 계산해 봐야 한다.

> **ANN(근사 최근접 이웃)** — 정확히 가장 가까운 것 대신, 거의 가까운 것을 훨씬 빠르게 찾는 방식.\
> 예: 10개를 찾을 때 9개만 정확해도 되니 100배 빠르게 답하는 쪽을 택하는 것.

**타임라인이 인과를 잘 보여준다.**

```text
2018~2019  태동      Weaviate(2019) · Milvus(2019) 전용 엔진 등장
   ↓                  용도: 추천 · 이미지 검색
2021       진입      Qdrant(2021, Rust) · Pinecone(2021, 관리형 SaaS)
   ↓
2021.4     확장 노선  pgvector — PostgreSQL 에 벡터 타입 + ANN 인덱스
   ↓
2022.11    ChatGPT 공개
   ↓
2022말~23  RAG 붐    질문을 임베딩 → 벡터 DB 검색 → 프롬프트에 주입
                      수요 폭증 · 2023 상반기는 과열의 정점
```

- **2018~2019 — 태동.** Weaviate(2019, 지식 그래프 결합형), Milvus(2019, Zilliz, 이후 LF AI 기부)가 전용 벡터 검색 엔진으로 등장.\
  추천·이미지 검색이 초기 용도였다.
- **2021 — 본격 진입.** Qdrant(2021, Rust 기반), Pinecone(2021, 완전 관리형 SaaS)가 합류.
- **2021 4월 — pgvector.** PostgreSQL에 벡터 타입과 ANN 인덱스(IVFFlat, 이후 HNSW)를 더하는 확장.\
  "기존 DB 위에 얹는다" 노선의 벡터판.
- **2022년 말 ~ 2023 — RAG 붐(폭발점).** ChatGPT(2022.11) 이후 **RAG(Retrieval-Augmented Generation)** 패턴이 LLM 애플리케이션의 표준 아키텍처로 자리 잡았다.\
  LLM의 환각(hallucination)과 지식 컷오프를 보완하기 위해, 질문을 임베딩해 벡터 DB에서 관련 문서를 검색하고 그 내용을 프롬프트에 주입하는 방식이다.\
  이 한 가지 패턴이 벡터 DB 수요를 폭증시켰고, 2023년 상반기는 벡터 DB를 둘러싼 마케팅·과열의 정점이었다.

> **RAG(Retrieval-Augmented Generation)** — 모델이 답하기 전에 관련 문서를 먼저 검색해 프롬프트에 붙여 주는 방식.\
> 예: 사내 규정을 모르는 모델에게 규정 문서 3쪽을 찾아 붙여 주고 답하게 한다.

> **환각(hallucination)** — 모델이 근거 없는 내용을 사실인 것처럼 지어내는 현상.\
> 예: 존재하지 않는 논문 제목과 저자를 자신 있게 답하는 것.

```python
# RAG의 검색 단계 — 질문을 임베딩해 의미적으로 가까운 청크를 가져온다 (개념 예시)
query_vec = embed("환불 정책이 어떻게 되나요?")   # → 1536차원 벡터
docs = vector_db.search(query_vec, top_k=5)        # ANN(HNSW) 근사 최근접 이웃
prompt = build_prompt(context=docs, question=...)  # 검색 결과를 프롬프트에 주입
answer = llm.generate(prompt)
```

코드 읽는 법 — 네 줄이 곧 RAG의 전부다.\
질문을 벡터로 바꾸고, 가까운 문서 5개를 찾고, 그것을 프롬프트에 넣고, 모델에 넘긴다.

```sql
-- pgvector: 일반 SQL 안에서 벡터 컬럼과 거리 연산자(<=>: 코사인 거리)
CREATE EXTENSION vector;
CREATE TABLE documents (id bigserial, content text, embedding vector(1536));
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- 질의 벡터와 가장 가까운 5개 (ORDER BY 거리 + LIMIT)
SELECT content
FROM documents
ORDER BY embedding <=> '[0.12, -0.04, ...]'
LIMIT 5;
```

코드 읽는 법 — 벡터 검색이 특별한 API가 아니라 그냥 `ORDER BY 거리 LIMIT 5`라는 점이 pgvector 노선의 핵심 주장이다.\
`<=>`가 코사인 거리 연산자이고, `USING hnsw`가 ANN 인덱스를 만든다.

#### 주요 시스템과 두 진영

벡터 DB 생태계는 **전용 엔진**과 **기존 DB 확장**의 두 진영으로 나뉘며, 2026년 현재 프로덕션을 양분한다.

| 진영 | 대표 | 특징 |
|------|------|------|
| 전용(green-field) | **Qdrant**(Rust), **Milvus**(분산·대규모), **Weaviate**(하이브리드·모듈), Pinecone(완전 관리형), LanceDB(임베디드) | 대규모·고처리량 ANN에 최적화. 분산·샤딩·필터링·양자화를 자체 설계 |
| 확장(bolt-on) | **pgvector**(PostgreSQL), MongoDB Atlas Vector Search, Elasticsearch/OpenSearch, Redis | 기존 운영 DB 안에서 벡터를 함께 다룸. 별도 인프라 없이 시작 가능, 중소·하이브리드 워크로드에 적합 |

#### 최신 동향 (2024 ~ 2026)

- **RAG가 표준 인프라로.** 2026년 기준 RAG는 AI 애플리케이션의 기본 구성요소가 되었고, 벡터 DB 수요를 이끄는 1순위 용도다.\
  시장 규모는 2025년 약 43억 달러로 추정되며 2030년 140억 달러로의 성장이 전망된다.
- **서버리스·에이전트 워크로드.** Pinecone은 서버리스 아키텍처를 **에이전트(agentic) 워크로드** 대규모화에 맞춰 재설계하고, 임베딩·리랭킹 모델을 파이프라인에 내장(Pinecone Inference)했다.\
  MongoDB Atlas는 벡터 검색을 트랜잭션 클러스터와 독립적으로 확장하는 Search Node를 도입했다.
- **pgvector의 부상.** "별도 벡터 DB를 두지 않고 이미 쓰는 PostgreSQL에서 끝낸다"는 단순함이 강력해, pgvector는 2026년 가장 널리 배포된 벡터 솔루션 중 하나가 되었다.\
  다만 초대규모 분산 처리량에서는 전용 엔진에 못 미친다는 트레이드오프가 명확하다.

**왜 이게 나은가 / 대가는 무엇인가** — 벡터 DB는 "특정 워크로드가 전용 DB 카테고리를 새로 만든다"는 이 시대의 패턴을 가장 압축적으로 재현했다.\
다만 그 촉발 요인이 데이터 규모가 아니라 **새로운 AI 알고리즘**이었다는 점이 새롭다.\
동시에 기존 DB들의 빠른 흡수(pgvector·Atlas·Elasticsearch)는, 벡터 검색이 영구히 독립 카테고리로 남을지 아니면 "모든 DB의 기능 하나"로 수렴할지를 둘러싼 논쟁을 열어놓았다.

---

### 5. 클라우드 네이티브 DB — 스토리지·컴퓨트 분리

**무엇** — 데이터를 담는 쪽과 계산하는 쪽을 물리적으로 떼어 놓고, 각각 따로 늘리는 구조.

**언제·왜 생겼나** — 온프레미스 시대의 DB는 스토리지·컴퓨트·로깅·복구가 한 서버 안에 단단히 결합돼 있었다.\
클라우드는 이 결합을 깰 기회를 줬다 — 네트워크로 무한히 붙는 스토리지(S3 등)와 별도로 탄력적으로 늘리는 컴퓨트.\
**스토리지-컴퓨트 분리**(disaggregation)가 이 시대 데이터 인프라의 핵심 설계 원리다.\
읽기 부하가 늘면 컴퓨트만, 데이터가 늘면 스토리지만 독립적으로 확장한다.

```text
[ 전통적 구조 ]                    [ 클라우드 네이티브 ]
 ┌──────────────┐                  컴퓨트(stateless)
 │  컴퓨트       │                  ┌────┐ ┌────┐ ┌────┐
 │  + 스토리지   │   ──분리──>      │ R/W│ │ RO │ │ RO │  ← 독립 확장
 │  (한 서버)    │                  └─┬──┘ └─┬──┘ └─┬──┘
 └──────────────┘                    └──────┼──────┘
  디스크 부족 →                        공유 스토리지 계층
  CPU까지 같이 증설                    (S3 / 분산 로그) ← 독립 확장
```

그림 해설 — 왼쪽은 디스크 한 칸이 모자라도 서버를 통째로 사야 한다.\
오른쪽은 읽기가 늘면 읽기 전용 컴퓨트(RO)만 붙이고, 데이터가 늘면 스토리지만 늘린다.

**주요 시스템**

- **Amazon DynamoDB** (2012) — Amazon의 관리형 NoSQL 키-값/문서 스토어.\
  2007년 사내 Dynamo 논문의 계보를 잇되, **운영 부담 없는 완전 관리형·무제한 확장·한 자릿수 ms 지연**을 표방했다.\
  클라우드 시대 NoSQL의 대표.
- **Amazon Aurora** (발표 2014, 출시 2015) — MySQL/PostgreSQL 호환 관계형 DB이면서, 내부적으로 **로그(redo log)를 스토리지 계층으로 밀어내는** 재설계가 핵심이다.\
  "로그가 곧 데이터베이스(the log is the database)"라는 원리로, 컴퓨트는 질의·트랜잭션·버퍼캐시만 담당하고 로깅·스토리지·복구는 3개 가용영역에 걸쳐 쿼럼 쓰기로 복제되는 분산 스토리지 서비스가 맡는다.\
  클라우드 네이티브 관계형 DB의 교과서적 사례.
- **Google BigQuery** (공개 2010, GA 2011~2012) — Google의 내부 분석 엔진 **Dremel**(2010 논문)을 외부화한 서버리스 데이터 웨어하우스.\
  사용자가 클러스터를 관리하지 않고 SQL만 던지면, 컬럼형 저장(Colossus/Capacitor)과 분산 실행이 알아서 페타바이트를 스캔한다.\
  "서버리스 분석"의 원형.
- **Snowflake** (창업 2012, 스텔스 공개 2014, GA 2015) — Oracle 출신 Benoit Dageville·Thierry Cruanes와 Vectorwise 공동창업자 Marcin Zukowski가 세운 클라우드 데이터 웨어하우스.\
  **스토리지·컴퓨트의 완전 분리**를 단일 설계 결정으로 삼아, 공유 스토리지 위에 서로 독립적인 다수의 **가상 웨어하우스**(컴퓨트 클러스터)를 띄운다.\
  한 팀의 무거운 분석이 다른 팀에 영향을 주지 않고, 컴퓨트를 끄면 비용도 멈춘다.\
  2020년 당시 최대 규모의 소프트웨어 IPO를 기록하며 이 아키텍처의 상업적 정당성을 증명했다.

> **쿼럼(quorum) 쓰기** — 복제본 전부가 아니라 미리 정해 둔 수(흔히 과반)만 확인해 주면 쓰기를 성공으로 치는 방식.\
> 예: Aurora는 복제본 6개 중 4개가 받았다고 답하면 커밋으로 인정한다.

> **데이터 웨어하우스(data warehouse)** — 분석용으로 모아 둔 대용량 데이터 저장소.\
> 예: 여러 서비스의 거래 기록을 한곳에 모아 두고 "분기별 매출 추이"를 뽑는 곳.

**왜 이게 나은가** — Aurora·BigQuery·Snowflake가 공유하는 스토리지-컴퓨트 분리는 이제 **데이터 인프라의 기본값**이다.\
이 원리는 뒤의 서버리스 DB(컴퓨트를 0까지 끄기)와 레이크하우스(공유 스토리지에 여러 엔진을 붙이기)로 직접 이어진다.\
데이터 웨어하우스는 "비싼 고정 클러스터"에서 "쓴 만큼 내는 탄력 자원"으로 의미가 바뀌었다.

---

### 6. 서버리스 데이터베이스 (Neon, PlanetScale)

**무엇** — 안 쓸 때는 컴퓨트를 0으로 꺼 두고, 요청이 오면 되살리는 DB.

**언제·왜 생겼나** — 스토리지-컴퓨트 분리를 **극한까지** 밀면 "트래픽이 없을 때 컴퓨트를 완전히 0으로(scale-to-zero), 요청이 오면 수백 ms 안에 되살린다"는 진정한 서버리스가 된다.\
동시에 클라우드 개발 문화는 코드처럼 다룰 수 있는 DB를 요구했다 — Git 브랜치처럼 즉시 만들고 버리는 데이터베이스.\
이는 규모가 아니라 **개발자 경험**(DX)이 주도한 진화다.

```text
[ 기존: 테스트용 DB 만들기 ]        [ 브랜칭 ]
1. 새 인스턴스 띄운다                git 브랜치처럼 한 번에
2. 50GB 덤프를 복원한다              50GB DB 브랜치가 1초 안에
3. 수십 분 대기 · 스토리지 2배       추가 스토리지 ≈ 0
4. 다 쓰면 지우는 걸 잊는다          (쓰기 전까지 페이지를 공유)
```

이 대비의 결론 — 복사를 실제로 하지 않고 "쓸 때만 복사"하기 때문에 브랜치가 사실상 공짜다.

> **Copy-on-Write(쓸 때 복사)** — 복제본을 만들 때 실제 데이터를 복사하지 않고 원본을 같이 보다가, 고치는 순간에만 그 부분을 복사하는 기법.\
> 예: 문서 사본을 만들어도 실제로는 같은 종이를 보다가, 한 쪽을 고칠 때 그 쪽만 복사한다.

> **scale-to-zero** — 요청이 없으면 컴퓨트를 완전히 꺼서 비용을 0으로 만드는 것.\
> 예: 밤새 아무도 안 쓰는 개발용 DB는 꺼져 있다가 아침 첫 요청에 깨어난다.

**주요 시스템**

- **Neon** (서버리스 PostgreSQL) — PostgreSQL의 스토리지 계층을 분리해 재구현했다.\
  상태 없는(stateless) 컴퓨트 노드 + Pageserver(스토리지 백엔드)·Safekeeper(WAL 중복 서비스)로 구성되며, 자동 스케일링·scale-to-zero와 함께 **Copy-on-Write 브랜칭**을 제공한다.\
  50GB DB의 브랜치가 1초 안에, 거의 0의 추가 스토리지로 만들어진다(쓰기 전까지 페이지를 공유).\
  2025년 5월 Databricks가 약 10억 달러에 인수해 Lakebase의 기반이 되었다.
- **PlanetScale** (서버리스 MySQL/Postgres) — YouTube가 MySQL을 인터넷 규모로 샤딩하려고 만든 **Vitess** 위에 구축.\
  수평 샤딩·커넥션 풀링·무중단 스키마 변경을 더했다.\
  브랜칭 모델은 Neon과 달라 — MySQL 브랜치는 스키마 중심 환경이고, 데이터 포함 브랜치는 백업 복원을 요한다.\
  2025년 9월에는 Vitess 팀이 PostgreSQL용으로 별도 설계한 Neki 기반 Postgres 제품을 추가했다.

**왜 이게 나은가** — 서버리스 DB는 "데이터베이스를 코드처럼" 다루는 워크플로를 대중화했다.\
브랜치마다 격리된 DB, PR마다 미리보기 환경이 그것이다.\
Neon의 Databricks 인수와 Lakebase 출시는, 서버리스 OLTP가 레이크하우스 분석 플랫폼과 통합되는 차세대 수렴 지점을 시사한다.

---

### 7. HTAP — 트랜잭션과 분석의 통합

**무엇** — 거래 처리와 분석을 한 시스템에서 동시에 하려는 시도.

**언제·왜 생겼나** — 전통적으로 OLTP(트랜잭션, 행 저장)와 OLAP(분석, 컬럼 저장)는 서로 다른 시스템이었고, ETL 파이프라인이 둘 사이에서 데이터를 밤마다 옮겼다.\
이 지연 때문에 "실시간 비즈니스 결정"이 불가능했다.\
**HTAP**(Hybrid Transactional/Analytical Processing)는 이 벽을 허물어 같은 데이터에 대해 트랜잭션과 분석을 한 시스템에서 처리하려는 시도다.\
용어 자체는 **Gartner가 2014년** 보고서에서 만들었다(처음엔 인메모리 전제, 2018년에 인메모리 제약을 풀어 일반화).

**주요 시스템**

- **SingleStore**(구 MemSQL) — 인메모리 행 저장 + 디스크 컬럼 저장을 결합.
- **TiDB** — OLTP용 행 저장 **TiKV**와 ClickHouse 기반 컬럼 엔진 **TiFlash**를 두고, Raft 합의로 행→컬럼 복제를 동기화해 같은 데이터를 두 형태로 동시에 보유한다.

#### 영향과 한계

**대가는 무엇인가** — HTAP는 ETL 제거와 실시간 분석이라는 매력적 약속에도, "하나의 시스템이 정반대 워크로드를 모두 잘하기는 어렵다"는 근본 긴장 때문에 기대만큼 보편화되지는 못했다.

```text
HTAP 가 제기한 문제         2025년 무렵 업계의 답
"트랜잭션과 분석을          ├─ zero-ETL  : 시스템은 분리하되 복제를 자동화
 가깝게 두자"               └─ 레이크하우스: 공유 스토리지 + 여러 엔진을 붙임
                            문제의식은 살아남고, 해법은 단일 시스템이 아닌 쪽으로 분기
```

2025년 무렵 업계의 무게추는 오히려 **zero-ETL**과 **레이크하우스** 쪽으로 일부 이동했다.

> **레이크하우스(lakehouse)** — 값싼 공유 스토리지(데이터 레이크) 위에 데이터 웨어하우스급 관리 기능을 얹은 구조.\
> 예: S3에 쌓인 Parquet 파일에 여러 분석 엔진이 각자 붙어 SQL을 돌린다.

---

### 8. DuckDB — 임베디드 분석 데이터베이스

**무엇** — 서버 없이 내 프로그램 안에서 돌아가는 분석 엔진.

**언제·왜 생겼나** — "SQLite가 트랜잭션(OLTP)에서 한 일을 분석(OLAP)에서 한다"가 DuckDB의 한 줄 정체성이다.\
2018~2019년 네덜란드 CWI 연구소의 Mark Raasveldt·Hannes Mühleisen가 만들었고, 2019년 SIGMOD 데모 논문으로 발표됐다.\
동기는 명확했다.\
데이터 과학자가 분석 질의를 돌리려면 Spark 클러스터나 데이터 웨어하우스를 띄워야 했는데, 노트북에서 수 GB를 다루는 데는 과했다.\
반대로 SQLite는 가볍지만 행 기반이라 분석 스캔이 느렸다.\
**프로세스 안에 임베드되는(in-process) 분석 OLAP 엔진**이라는 빈자리가 있었다.

```text
              OLTP(거래)              OLAP(분석)
 서버형    PostgreSQL · MySQL     Snowflake · BigQuery
 임베디드  SQLite                 ← 여기가 비어 있었다 → DuckDB
```

이 표가 DuckDB의 자리다 — 가벼운데 분석에 강한 칸이 비어 있었다.

#### 핵심 설계

- **In-process.** 별도 서버 없이 애플리케이션 프로세스 안에서 라이브러리로 실행 — 프로세스 간 통신 오버헤드가 0이다.\
  Python `pip install duckdb` 한 줄로 시작한다.
- **컬럼형 + 벡터화 실행.** 행 단위가 아니라 값의 묶음(벡터)을 한 번에 처리하는 벡터화 엔진으로, 같은 in-process여도 SQLite 대비 분석 질의가 압도적으로 빠르다.
- Parquet·CSV·Arrow를 복사 없이 직접 질의하고, Pandas/Polars 데이터프레임과 매끄럽게 오간다.

> **벡터화 실행(vectorized execution)** — 한 행씩 처리하지 않고 값 수천 개를 한 묶음으로 처리해 CPU를 놀리지 않는 실행 방식.\
> 예: 합계를 구할 때 1건씩 더하지 않고 1024건을 한 번에 더한다.

> **in-process(임베디드)** — 별도 서버 프로세스 없이 내 애플리케이션 안에서 라이브러리로 도는 것.\
> 예: SQLite처럼 `import` 한 줄로 쓰고, 네트워크 연결이 아예 없다.

```python
import duckdb
# 서버 없이, Parquet 파일을 곧장 SQL로 — 메모리에 통째로 올리지 않음
duckdb.sql("""
    SELECT region, sum(amount)
    FROM 's3://bucket/sales/*.parquet'
    GROUP BY region
""").show()
```

코드 읽는 법 — 데이터베이스에 적재하는 단계가 없다.\
파일 경로를 테이블 자리에 그대로 쓰는 것이 이 엔진의 사용 감각이다.

**왜 이게 나은가** — DuckDB는 "분석 = 무거운 분산 클러스터"라는 가정을 깨고, **로컬·임베디드 분석**이라는 카테고리를 사실상 새로 열었다.\
노트북 데이터 분석, 데이터 파이프라인의 변환 단계, 심지어 브라우저(WASM) 안에서까지 돌며, MotherDuck 같은 "DuckDB + 클라우드" 하이브리드로 확장됐다.\
시계열의 TimescaleDB, 벡터의 pgvector와 함께 — "거대 인프라 없이, 이미 있는 자리에서 특화 워크로드를 끝낸다"는 이 시대의 또 다른 핵심 정서를 대표한다.

---

## 왜 그렇게 갔나 — 남은 선택지와 트레이드오프

이 시대의 모든 카테고리에서 같은 갈림길이 반복된다.

```text
               새 워크로드가 나타났다
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
 전용 엔진을 새로 짓는다          검증된 엔진 위에 얹는다
 (green-field)                   (extension / bolt-on)

 시계열 : InfluxDB               시계열 : TimescaleDB (PostgreSQL 확장)
 벡터   : Qdrant · Milvus        벡터   : pgvector · Atlas · Elasticsearch
 분석   : Snowflake · BigQuery

 얻는 것                         얻는 것
  - 그 워크로드에 최적            - 기존 SQL·조인·트랜잭션·생태계 그대로
  - 초대규모 분산 처리량          - 별도 인프라 없이 오늘 시작 가능
 잃는 것                         잃는 것
  - 운영할 시스템이 하나 더 는다   - 초대규모에서는 전용 엔진에 못 미침
  - 생태계를 처음부터 쌓아야 함    - 호스트 엔진의 한계를 물려받음

 제3의 축 : in-process
 (엔진은 새로 짓되, 띄울 인프라를 두지 않는다)
 분석   : DuckDB — 이미 돌고 있는 프로세스 안에서 끝낸다
```

읽는 법 — 어느 쪽이 옳다가 아니라, **내 데이터가 전용 엔진이 필요할 만큼 큰가**가 판단 기준이다.\
pgvector가 2026년 가장 널리 배포된 벡터 솔루션 중 하나가 된 이유는, "별도 벡터 DB를 두지 않고 이미 쓰는 PostgreSQL에서 끝낸다"는 단순함이 강력했기 때문이다.\
다만 초대규모 분산 처리량에서는 전용 엔진에 못 미친다는 트레이드오프가 명확하다.

셋째 축의 DuckDB는 엔진 자체는 새로 지었지만, TimescaleDB·pgvector와 "거대 인프라 없이 이미 있는 자리에서 특화 워크로드를 끝낸다"는 정서를 공유한다.

HTAP는 ETL 제거와 실시간 분석이라는 매력적 약속에도 기대만큼 보편화되지는 못했다.\
"한 시스템이 정반대 워크로드를 모두 잘하기는 어렵다"는 근본 긴장 때문에, 해법이 zero-ETL과 레이크하우스로 분기했다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다)*

2015년 이후의 데이터베이스 역사는 **분화와 수렴의 동시 진행**으로 요약된다.

- **분화(specialization).** 데이터의 모양마다 — 시계열·그래프·검색·벡터 — 전용 엔진이 생겨났다.\
  단일 RDBMS가 모든 것을 처리하던 시대는 끝났고, "워크로드에 맞는 도구를 고른다"는 폴리글랏 퍼시스턴스가 상식이 되었다.\
  벡터 DB는 이 패턴의 가장 최근이자 가장 격렬한 사례이며, 그 촉발 요인이 데이터 규모가 아니라 **LLM이라는 알고리즘**이었다는 점에서 새로운 유형의 동력을 보여줬다.

- **수렴(convergence).** 동시에 정반대 힘도 작동한다.\
  클라우드의 스토리지-컴퓨트 분리는 모든 클라우드 DB의 공통 골격이 되었고(Aurora·Snowflake·BigQuery·Neon), 기존 DB들은 특화 기능을 빠르게 흡수했다.\
  PostgreSQL은 확장(TimescaleDB·pgvector)으로 시계열과 벡터를 삼켰고, Elasticsearch·MongoDB는 벡터 검색을 내장했다.\
  "전용 DB를 새로 지을 것인가, 검증된 엔진 위에 얹을 것인가"라는 긴장이 카테고리마다 반복된다.

- **운영의 소멸.** 서버리스와 완전 관리형의 흐름은 DBA의 수작업 튜닝·확장·백업을 점점 인프라 안으로 흡수했다.\
  개발자에게 데이터베이스는 "관리하는 서버"에서 "API처럼 호출하는 자원"으로 추상화되었다.

```text
분화 ────────┐
             ├──> 2026년 현재의 최전선
수렴 ────────┤     · LLM/RAG 가 벡터를 일상화
             │     · 레이크하우스가 분석과 트랜잭션을 공유 스토리지 위에서 재통합
운영의 소멸 ─┘     · 서버리스가 그 모든 것의 운영 비용을 0에 수렴시키려 한다
```

이 세 흐름이 만나는 지점이 2026년 현재의 최전선이다.

## 용어 풀이

- **폴리글랏 퍼시스턴스** — 데이터 종류마다 다른 DB를 골라 쓰는 방식.
- **워크로드** — 시스템에 들어오는 일의 성격(읽기·쓰기 비율, 질의 모양, 크기).
- **append-only** — 기존 행을 고치지 않고 뒤에 붙이기만 하는 쓰기 패턴.
- **관측성(observability)** — 바깥 신호만으로 시스템 내부 상태를 알아내는 능력.
- **하이퍼테이블 / 청크** — TimescaleDB가 시계열 테이블을 시간 기준으로 자동 분할한 추상과 그 조각.
- **index-free adjacency** — 인덱스 대신 포인터로 이웃을 바로 찾는 그래프 저장 방식.
- **순회(traversal)** — 그래프에서 연결을 따라 이동하며 답을 모으는 일.
- **역색인(inverted index)** — "단어 → 문서" 방향으로 뒤집어 만든 색인.
- **BM25 / TF-IDF** — 검색어와 문서의 관련도를 점수로 매기는 방식.
- **임베딩(embedding)** — 뜻이 위치로 나타나도록 데이터를 벡터로 바꾼 것.
- **차원의 저주** — 차원이 커지면 정확한 최근접 이웃 찾기가 사실상 전수 비교가 되는 현상.
- **ANN(근사 최근접 이웃)** — 정확성을 조금 양보하고 훨씬 빠르게 가까운 것을 찾는 방식. HNSW·IVF·DiskANN이 대표 알고리즘.
- **RAG** — 답하기 전에 관련 문서를 검색해 프롬프트에 붙이는 패턴.
- **환각(hallucination)** — 모델이 근거 없는 내용을 사실처럼 지어내는 현상.
- **하이브리드 검색** — 키워드(BM25)와 벡터 검색을 결합한 검색 방식.
- **스토리지-컴퓨트 분리(disaggregation)** — 저장과 계산을 떼어 각각 따로 확장하는 설계.
- **쿼럼(quorum) 쓰기** — 과반 복제본의 확인만으로 쓰기를 성공 처리하는 방식.
- **데이터 웨어하우스 / 레이크하우스** — 분석용 대용량 저장소, 그리고 값싼 공유 스토리지 위에 그 기능을 얹은 구조.
- **scale-to-zero** — 요청이 없으면 컴퓨트를 완전히 꺼서 비용을 0으로 만드는 것.
- **Copy-on-Write 브랜칭** — 쓸 때만 복사해서 DB 브랜치를 사실상 공짜로 만드는 기법.
- **HTAP / zero-ETL** — 트랜잭션과 분석을 한 시스템에서 처리하려는 시도, 그리고 시스템은 나누되 복제를 자동화하는 대안.
- **in-process(임베디드)** — 별도 서버 없이 애플리케이션 프로세스 안에서 도는 것.
- **벡터화 실행** — 값을 묶음 단위로 한 번에 처리하는 실행 방식.
- **green-field vs. extension** — 전용 엔진을 새로 짓는 노선과 검증된 엔진 위에 얹는 노선.

## 참고 출처

**시계열**
- [InfluxDB (Wikipedia)](https://en.wikipedia.org/wiki/InfluxDB)
- [TimescaleDB vs. InfluxDB: purpose built differently for time-series data (Timescale)](https://medium.com/timescale/timescaledb-vs-influxdb-purpose-built-differently-for-time-series-data-36489299877)
- [Comparing InfluxDB, TimescaleDB, and QuestDB (QuestDB)](https://questdb.com/blog/comparing-influxdb-timescaledb-questdb-time-series-databases/)

**그래프**
- [Neo4j (Wikipedia)](https://en.wikipedia.org/wiki/Neo4j)
- [Cypher Overview (Neo4j Docs)](https://neo4j.com/docs/cypher-manual/current/introduction/cypher-overview/)
- [Database startup Neo4j embraces AI to supercharge growth (TechCrunch, 2024-11)](https://techcrunch.com/2024/11/19/database-startup-neo4j-embraces-ai-to-supercharge-growth/)

**검색·벡터**
- [Vector databases (1): What makes each one different? (The Data Quarry)](https://thedataquarry.com/blog/vector-db-1/)
- [Best Vector Databases in 2026 (MarkTechPost, 2026-05)](https://www.marktechpost.com/2026/05/10/best-vector-databases-in-2026-pricing-scale-limits-and-architecture-tradeoffs-across-nine-leading-systems/)
- [Best Vector Databases 2026 (DataCamp)](https://www.datacamp.com/blog/the-top-5-vector-databases)
- [We Tried and Tested 10 Best Vector Databases for RAG Pipelines (ZenML)](https://www.zenml.io/blog/vector-databases-for-rag)
- [MongoDB Atlas Vector Search vs Pinecone (MongoEngine)](https://mongoengine.org/mongodb-atlas-vector-search-vs-pinecone/)
- [Pinecone Introduces Dedicated Read Nodes (InfoQ, 2025-12)](https://www.infoq.com/news/2025/12/pinecone-drn-vector-workloads/)

**클라우드 네이티브**
- [Amazon Aurora: Design Considerations for High Throughput Cloud-Native Relational Databases (Amazon Science / SIGMOD 2017)](https://www.amazon.science/publications/amazon-aurora-design-considerations-for-high-throughput-cloud-native-relational-databases)
- [A decade of database innovation: The Amazon Aurora story (Amazon Science)](https://www.amazon.science/blog/a-decade-of-database-innovation-the-amazon-aurora-story)
- [Amazon Aurora and Amazon DynamoDB (AWS)](https://aws.amazon.com/compare/aurora-and-dynamodb/)
- [Snowflake Inc. (Wikipedia)](https://en.wikipedia.org/wiki/Snowflake_Inc.)
- [The Elastic Data Warehouse: The Origin Story of Snowflake (Stacksync)](https://www.stacksync.com/blog/the-elastic-data-warehouse-the-origin-story-of-snowflake)

**서버리스**
- [Neon: Serverless Postgres (GitHub)](https://github.com/neondatabase/neon)
- [On Neon database: The architecture behind serverless Postgres (Thomas Gauvin)](https://thomasgauvin.com/writing/on-neon-database-the-architecture-behind-serverless-postgres/)
- [PlanetScale vs. Neon (Bytebase)](https://www.bytebase.com/blog/planetscale-vs-neon/)

**HTAP**
- [Hybrid transactional/analytical processing (Wikipedia)](https://en.wikipedia.org/wiki/Hybrid_transactional/analytical_processing)
- [HTAP: the Rise and Fall of Unified Database Systems? (InfoQ, 2025-06)](https://www.infoq.com/news/2025/06/htap-databases/)
- [HTAP Databases: A Survey (arXiv)](https://arxiv.org/html/2404.15670v1)

**DuckDB**
- [DuckDB (Wikipedia)](https://en.wikipedia.org/wiki/DuckDB)
- [In-Process Analytical Data Management with DuckDB (InfoQ)](https://www.infoq.com/articles/analytical-data-management-duckdb/)
- [Database of Databases — DuckDB (dbdb.io)](https://dbdb.io/db/duckdb)
