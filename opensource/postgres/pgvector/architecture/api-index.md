# API 역인덱스

상위: [pgvector 아키텍처 지도](README.md)

"이 연산자·인덱스 옵션·설정 변수·타입을 쓰면 어느 흐름들을 지나는가"를 뒤에서부터 찾는 표다. 흐름 문서가 함수에서 출발한다면 이 표는 **SQL 에 적는 이름에서 출발한다.**

기준 태그: `v0.8.7` [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876). 줄 번호는 `sql/vector.sql` 이면 그 파일, 아니면 `src/` 아래 파일 기준이다.

## 범위를 먼저 밝힌다

```text
 이 표는 흐름 다섯 편이 실제로 덮는 길만 적었다
 덮지 않는 이름도 맨 아래에 따로 적었다 - 없는 것을 있는 척하지 않으려고

 흐름 이름 줄임
   타입      확장 로드와 vector 타입
   연산자AM  거리 연산자와 Index AM 연결
   HNSW빌드  HNSW 빌드
   HNSW검색  HNSW 검색
   IVFFlat   IVFFlat 빌드와 검색
```

표의 흐름 이름은 [지도의 흐름 표](README.md#흐름-다섯-편)에서 각 흐름 문서로 이어진다.

## 모든 질의가 공유하는 앞단

```text
 SELECT ... ORDER BY embedding <op> $1 LIMIT k
   |
   v
 플래너   연산자 <op> 가 열의 인덱스 연산자 클래스에 FOR ORDER BY 로 있는가
          amcanorderbyop = true (hnsw.c L334, ivfflat.c L251)
          amcostestimate = hnswcostestimate / ivfflatcostestimate     --> 연산자AM 04
   v
 실행기   ambeginscan -> amrescan -> amgettuple 반복                  --> HNSW검색 / IVFFlat 07
          WHERE 만 있고 ORDER BY 가 없으면 비용이 무한대라 이 인덱스를 쓰지 않는다
          (hnsw.c L148, ivfflat.c L100)
```

## 연산자

| 연산자 | 타입과 등록 줄 | SQL 함수 | 인덱스 연산자 클래스 | 지나는 흐름 |
|---|---|---|---|---|
| `<->` | vector L254, halfvec L714, sparsevec L1110 | `l2_distance` | `*_l2_ops` (hnsw 셋 다, ivfflat 은 vector·halfvec) | 연산자AM 07 -> HNSW검색 / IVFFlat |
| `<#>` | vector L259, halfvec L719, sparsevec L1115 | `vector_negative_inner_product` | `*_ip_ops` (hnsw 셋 다, ivfflat 은 vector·halfvec) | 연산자AM 08 -> HNSW검색 / IVFFlat |
| `<=>` | vector L264, halfvec L724, sparsevec L1120 | `cosine_distance` | `*_cosine_ops` (hnsw 셋 다, ivfflat 은 vector·halfvec) | 연산자AM 06, 08 (정규화) -> HNSW검색 / IVFFlat |
| `<+>` | vector L269, halfvec L729, sparsevec L1125 | `l1_distance` | `*_l1_ops` (hnsw 만) | 연산자AM 07 -> HNSW검색 |
| `<~>` | bit L882 | `hamming_distance` | `bit_hamming_ops` (hnsw, ivfflat) | 타입 01 (디스패치) -> HNSW검색 / IVFFlat |
| `<%>` | bit L887 | `jaccard_distance` | `bit_jaccard_ops` (hnsw 만) | 타입 01 (디스패치) -> HNSW검색 |

```text
 연산자와 인덱스 안의 거리가 다른 경우

 <->   인덱스는 vector_l2_squared_distance (제곱근 없음)          vector.sql L430
 <=>   인덱스는 값을 l2_normalize 한 뒤 vector_negative_inner_product   L440-L441
 순서는 같으므로 인덱스가 낸 순서가 곧 ORDER BY 순서다 (재확인 없음, hnswscan.c L329)
```

## 인덱스 옵션 (`CREATE INDEX ... WITH (...)`)

| 옵션 | AM | 기본 | 범위 | 등록 | 지나는 흐름 |
|---|---|---|---|---|---|
| `m` | hnsw | 16 | 2..100 | hnsw.c L88 | 연산자AM 03 -> HNSW빌드 02 (`ml`, `maxLevel`), 메타 페이지에 기록 -> HNSW검색 05 |
| `ef_construction` | hnsw | 64 | 4..1000, `>= 2 * m` | hnsw.c L90 | 연산자AM 03 -> HNSW빌드 02, 07 |
| `lists` | ivfflat | 100 | 1..32768 | ivfflat.c L42 | 연산자AM 03 -> IVFFlat 02 (표본 수), 03, 04 -> 검색 07 (probes 상한) |

## 설정 변수 (GUC)

모두 `PGC_USERSET` 이라 세션에서 `SET` 으로 바꿀 수 있다. 등록은 `HnswInit`(hnsw.c L81)과 `IvfflatInit`(ivfflat.c L38)이 한다.

| 이름 | 기본 | 범위 | 등록 | 읽는 곳 | 지나는 흐름 |
|---|---|---|---|---|---|
| `hnsw.ef_search` | 40 | 1..1000 | hnsw.c L93 | hnswscan.c L60, L73 / hnsw.c L201 | HNSW검색 05, 09 / 연산자AM 04 |
| `hnsw.iterative_scan` | off | off, relaxed_order, strict_order | hnsw.c L97 | hnswscan.c L60, L256, L318 | HNSW검색 03, 09 |
| `hnsw.max_scan_tuples` | 20000 | 1..INT_MAX | hnsw.c L102 | hnswscan.c L264 | HNSW검색 03 |
| `hnsw.scan_mem_multiplier` | 1 | 1..1000 | hnsw.c L107 | hnswscan.c L160 | HNSW검색 01 |
| `ivfflat.probes` | 1 | 1..32768 | ivfflat.c L45 | ivfscan.c L262 / ivfflat.c L123 | IVFFlat 07, 09 / 연산자AM 04 |
| `ivfflat.iterative_scan` | off | off, relaxed_order | ivfflat.c L49 | ivfscan.c L271 | IVFFlat 07 |
| `ivfflat.max_probes` | 32768 | 1..32768 | ivfflat.c L54 | ivfscan.c L272 | IVFFlat 07 |

서버 설정 중 이 흐름들이 읽는 것은 둘이다.

```text
 maintenance_work_mem   HNSW 빌드의 그래프 메모리 상한 (hnswbuild.c L727, 병렬은 L964)
                        IVFFlat 빌드의 표본·k-means 메모리 검사 (ivfutils.c L129), 정렬 메모리
 work_mem               HNSW 반복 스캔의 메모리 상한 (hnswscan.c L160)
                        IVFFlat 검색의 정렬 메모리 (ivfscan.c L249)
```

## 타입

| 타입 | 값 모양 | 차원 상한 (값 / hnsw / ivfflat) | 지나는 흐름 |
|---|---|---|---|
| `vector` | `int16 dim` + `float4[]` (vector.h L18) | 16000 / 2000 / 2000 | 타입 02-07 -> 연산자AM -> 모든 인덱스 흐름 |
| `halfvec` | `int16 dim` + `half[]` (halfvec.h L67) | 16000 / 4000 / 4000 | 타입 (같은 틀) -> 연산자AM 05 (`hnsw_halfvec_support`) |
| `sparsevec` | `dim`, `nnz`, 인덱스 배열, 값 배열 (sparsevec.h L22) | 10억 / 10억 (nnz <= 1000) / 인덱스 없음 | 타입 (같은 틀) -> 연산자AM 05 (`hnsw_sparsevec_support`) -> HNSW |
| `bit` | PostgreSQL `VarBit` | - / 64000 / 64000 | 연산자AM 05 (`hnsw_bit_support`), IVFFlat (`ivfflat_bit_support`) |

```text
 차원 상한이 어디서 오는가

 값      VECTOR_MAX_DIM 16000 (vector.h L11), HALFVEC_MAX_DIM 16000, SPARSEVEC_MAX_DIM 10억
 hnsw    HNSW_MAX_DIM 2000 (hnsw.h L33), halfvec * 2, bit * 32       (hnswutils.c L1406-L1451)
 ivfflat IVFFLAT_MAX_DIM 2000 (ivfflat.h L37), halfvec * 2, bit * 32 (ivfutils.c L416-L451)
 열에 typmod 가 없으면 (vector, 차원 미지정) 두 인덱스 모두 만들 수 없다
   "column does not have dimensions"  (hnswbuild.c L706, ivfbuild.c L361)
```

## SQL 문

| SQL | 첫 진입 | 지나는 흐름 |
|---|---|---|
| `CREATE EXTENSION vector` | `sql/vector.sql`, 라이브러리 로드 시 `_PG_init` | 타입 01 |
| `'[1,2,3]'::vector(3)` | `vector_typmod_in`, `vector_in` | 타입 02, 03 |
| `INSERT ... VALUES (ARRAY[...])` | `array_to_vector` | 타입 07 |
| `CREATE INDEX ... USING hnsw (col vector_l2_ops)` | `hnswbuild` | 연산자AM 01, 05, 06 -> HNSW빌드 |
| `CREATE INDEX ... USING ivfflat (col) WITH (lists = 100)` | `ivfflatbuild` (`vector_l2_ops` 가 ivfflat 의 DEFAULT) | 연산자AM 02 -> IVFFlat 01-06 |
| `SELECT ... ORDER BY col <-> $1 LIMIT k` (hnsw) | `hnswbeginscan`, `hnswgettuple` | 연산자AM 04 -> HNSW검색 |
| `SELECT ... ORDER BY col <-> $1 LIMIT k` (ivfflat) | `ivfflatbeginscan`, `ivfflatgettuple` | 연산자AM 04 -> IVFFlat 07-09 |

hnsw 에는 DEFAULT 연산자 클래스가 없다(vector.sql L427-L446 모두 `FOR TYPE vector USING hnsw` 에 `DEFAULT` 가 없다). 그래서 hnsw 인덱스를 만들 때는 연산자 클래스를 적는다.

## 덮지 않는 것

```text
 INSERT 후 인덱스 갱신   hnswinsert (hnswinsert.c L771) / ivfflatinsert (ivfinsert.c L189)
                        빌드의 디스크 단계와 같은 알고리즘이라 요약만 했다
 VACUUM                 hnswbulkdelete, hnswvacuumcleanup / ivfflatbulkdelete, ivfflatvacuumcleanup
 B-tree 연산자 클래스    vector_ops, halfvec_ops, sparsevec_ops (=, <, > 비교와 vector_cmp)
 산술·기타 함수          +, -, *, ||, l2_norm, vector_norm, l2_normalize 의 SQL 사용,
                        subvector, binary_quantize, avg, sum
 타입 사이 cast          vector, halfvec, sparsevec 사이 양방향, vector -> real[]
 halfvec, sparsevec 의 입출력 함수 본문
 SIMD 구현 본문          F16C (halfutils.c), AVX-512 POPCNT (bitutils.c)
```
