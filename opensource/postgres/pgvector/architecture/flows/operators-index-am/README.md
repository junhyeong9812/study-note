# 거리 연산자와 Index AM 연결

상위: [pgvector 아키텍처 지도](../../README.md)

`ORDER BY embedding <=> '[...]' LIMIT 5` 한 줄이 **어떻게 PostgreSQL 의 인덱스 접근 메서드(Index AM) 인터페이스를 거쳐 `hnsw` 나 `ivfflat` 인덱스에 닿는가**를 보는 흐름이다. pgvector 는 실행기나 플래너를 고치지 않는다. 대신 SQL 로 세 가지를 등록한다. 연산자(`<=>` 와 그 함수 `cosine_distance`), 접근 메서드(`CREATE ACCESS METHOD hnsw ... HANDLER hnswhandler`), 그리고 둘을 묶는 연산자 클래스(`vector_cosine_ops`: 이 연산자는 이 AM 에서 `ORDER BY` 용이고, 거리 계산에는 이 지원 함수를 써라)다. 핸들러가 돌려주는 `IndexAmRoutine` 은 "나는 순서 연산자로 정렬된 결과를 낼 수 있다(`amcanorderbyop`)"고 선언하고 빌드·삽입·스캔 함수 포인터를 채운다. 연산자 함수와 인덱스가 실제로 부르는 지원 함수가 서로 다를 수 있다는 점이 이 흐름의 요점이다. `<->` 연산자는 제곱근을 씌운 L2 거리를 돌려주지만 인덱스는 제곱근을 뺀 `vector_l2_squared_distance` 로 비교하고, `<=>` 는 코사인 거리지만 인덱스는 값을 먼저 정규화한 뒤 음의 내적으로 비교한다.

기준 태그: v0.8.7 [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/` 아래다.

## 전체 그림

```text
 등록 (sql/vector.sql)
   CREATE OPERATOR <=> (PROCEDURE = cosine_distance)               L264
   CREATE ACCESS METHOD hnsw TYPE INDEX HANDLER hnswhandler          L364
   CREATE OPERATOR CLASS vector_cosine_ops FOR TYPE vector USING hnsw
     OPERATOR 1 <=> FOR ORDER BY float_ops
     FUNCTION 1 vector_negative_inner_product    거리 (HNSW_DISTANCE_PROC)
     FUNCTION 2 vector_norm                      정규화 판정 (HNSW_NORM_PROC)  L437-L441
 ------------------------------------------------------------------------------
 PostgreSQL 이 AM 을 열 때
 [01] hnswhandler                         hnsw.c       L267
      +-- amcanorderbyop = true, amsupport = 3, amcanmulticol = false
      +-- ambuild, aminsert, ambeginscan, amgettuple ... 함수 포인터
 [02] ivfflathandler                      ivfflat.c    L184
      +-- 같은 모양, amsupport = 5 (k-means 용 지원 함수 둘 + 타입 정보)
 [03] HnswInit                            hnsw.c       L81    (_PG_init 이 부른다)
      +-- reloption m, ef_construction / GUC hnsw.*
 ------------------------------------------------------------------------------
 플래너
 [04] hnswcostestimate                    hnsw.c       L134
      +-- ORDER BY 가 없으면 비용 무한대      L148
      +-- 레벨 수 * m + ef_search * 2m * 선택도 로 읽을 튜플 비율 추정
 ------------------------------------------------------------------------------
 빌드, 삽입, 스캔이 공통으로 쓰는 준비
 [05] HnswInitSupport                     hnswutils.c  L153
      +-- index_getprocinfo(FUNCTION 1)  거리 함수
      +-- HnswOptionalProcInfo(FUNCTION 2)  있으면 정규화
      +-- (짝) HnswGetTypeInfo(FUNCTION 3)  없으면 vector 기본값
 [06] HnswFormIndexValue                  hnswutils.c  L411
      +-- norm 이 0 이면 인덱스에 넣지 않음, 아니면 l2_normalize
 ------------------------------------------------------------------------------
 거리 함수 (모두 vector.c)
 [07] l2_distance / vector_l2_squared_distance       L580 / L596    <->
 [08] cosine_distance / vector_negative_inner_product L672 / L638   <=>, <#>
```

연산자 하나가 SQL 함수로 불릴 때와 인덱스 안에서 쓰일 때 실제 계산이 어떻게 갈리는지 정리하면 다음과 같다.

```text
 연산자   SQL 에서 불리는 함수            HNSW 가 쓰는 FUNCTION 1         HNSW FUNCTION 2
 <->      l2_distance                    vector_l2_squared_distance      -
 <#>      vector_negative_inner_product  vector_negative_inner_product   -
 <=>      cosine_distance                vector_negative_inner_product   vector_norm
 <+>      l1_distance                    l1_distance                     -
 <~>      hamming_distance (bit)         hamming_distance                -
 <%>      jaccard_distance (bit)         jaccard_distance                -

 FUNCTION 2 가 있으면 넣는 값과 찾는 값을 모두 l2_normalize 로 단위 벡터로 만든다
 단위 벡터 a, b 에서 cosine_distance = 1 - a.b 이므로 -a.b 와 순서가 같다
```

## 어디에서 쓰이는가

```text
 [HNSW 빌드]       ambuild = hnswbuild,  [05] [06] 으로 지원 함수와 값 정규화
 [HNSW 검색]       ambeginscan / amrescan / amgettuple = hnswbeginscan / hnswrescan / hnswgettuple
 [IVFFlat 빌드와 검색]  ivfflathandler 의 같은 자리
 상위 [nbtree 삽입과 분할]  index_insert 가 rd_indam->aminsert 를 부르는 자리에
                          B-tree 는 btinsert, pgvector 는 hnswinsert / ivfflatinsert 가 꽂힌다
```

상위 PostgreSQL 지도의 [index_insert](../../../../architecture/flows/nbtree-insert/02_index_insert/README.md)가 AM 함수 포인터로 넘기는 바로 그 자리다. B-tree 는 `amcanorder`(값 순서로 정렬)이고, pgvector 의 두 AM 은 `amcanorder = false`, `amcanorderbyop = true`(연산자 결과 순서로 정렬)라는 점이 다르다.

## 단계

1. [hnswhandler](01_hnswhandler/README.md)가 HNSW 의 `IndexAmRoutine` 을 채워 돌려준다.
2. [ivfflathandler](02_ivfflathandler/README.md)가 IVFFlat 의 `IndexAmRoutine` 을 같은 모양으로 돌려준다.
3. [HnswInit](03_HnswInit/README.md)이 `m`, `ef_construction` 인덱스 옵션과 `hnsw.*` 설정 변수를 등록한다.
4. [hnswcostestimate](04_hnswcostestimate/README.md)가 플래너에 인덱스 스캔 비용을 알려 준다.
5. [HnswInitSupport](05_HnswInitSupport/README.md)가 연산자 클래스에서 거리·정규화·타입 정보 함수를 꺼낸다.
6. [HnswFormIndexValue](06_HnswFormIndexValue/README.md)가 인덱스에 넣을 값을 검사하고 필요하면 정규화한다.
7. [l2_distance](07_l2_distance/README.md)와 `vector_l2_squared_distance` 가 L2 거리를 계산한다.
8. [cosine_distance](08_cosine_distance/README.md)와 내적 계열 함수가 코사인·내적 거리를 계산한다.

## 결과가 쓰이는 곳

```text
 IndexAmRoutine (함수 포인터 표)
      --> relcache 가 인덱스마다 rd_indam 으로 들고 있다
      --> 플래너: amcanorderbyop 로 ORDER BY <연산자> 를 인덱스 경로로 인정, amcostestimate 로 비용
      --> 실행기: ambeginscan -> amrescan -> amgettuple 반복 -> amendscan
 HnswSupport (procinfo, normprocinfo, collation)
      --> 빌드, 삽입, 스캔이 거리를 잴 때마다 FunctionCall2Coll(procinfo, ...)
```

## 다루지 않는 것

연산자 클래스 검증 함수(`hnswvalidate` 는 늘 `true`, hnsw.c L255), 빌드 단계 이름(`hnswbuildphasename`), VACUUM 쪽 함수 포인터(`ambulkdelete = hnswbulkdelete`, `amvacuumcleanup`), PostgreSQL 19 이상에서 정적 구조체로 바뀐 핸들러 분기, 플래너가 `amcanorderbyop` 를 보고 경로를 만드는 서버 쪽 코드는 다루지 않았다. `halfvec`, `sparsevec`, `bit` 의 거리 함수는 같은 틀이다.

## 하위 메서드

- [01 hnswhandler](01_hnswhandler/README.md)
- [02 ivfflathandler](02_ivfflathandler/README.md)
- [03 HnswInit](03_HnswInit/README.md)
- [04 hnswcostestimate](04_hnswcostestimate/README.md)
- [05 HnswInitSupport](05_HnswInitSupport/README.md)
- [06 HnswFormIndexValue](06_HnswFormIndexValue/README.md)
- [07 l2_distance](07_l2_distance/README.md)
- [08 cosine_distance](08_cosine_distance/README.md)
