# 확장 로드와 vector 타입

상위: [pgvector 아키텍처 지도](../../README.md)

`CREATE EXTENSION vector` 로 타입이 등록되고, 공유 라이브러리가 처음 올라올 때 `_PG_init` 이 거리 함수와 인덱스 옵션을 준비한 뒤, **문자열 `'[1,2,3]'` 하나가 `Vector` 구조체가 되어 디스크에 놓이고 다시 문자열로 나가기까지**의 흐름이다. pgvector 의 타입은 전부 PostgreSQL 의 varlena(가변 길이 값)다. 앞 4바이트 길이 헤더 뒤에 차원 수와 원소 배열이 붙는 단순한 모양이라, 입출력 함수가 하는 일은 대부분 "파싱하고 차원을 검사하는 것"이다. 차원 고정(`vector(3)`)은 typmod 로 표현되고, 그 검사는 입력 함수와 별도의 길이 강제 cast 두 군데에서 일어난다. 여기서 정한 typmod 가 나중에 인덱스 빌드의 차원 수가 된다.

기준 태그: v0.8.7 [`f37c13f68b`](https://github.com/pgvector/pgvector/tree/f37c13f68b57d2c3472b2214fbcff699d6d34876). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/` 아래다.

## 전체 그림

```text
 CREATE EXTENSION vector
   vector.control            module_pathname = '$libdir/vector'    L3
   sql/vector.sql
     CREATE TYPE vector (INPUT = vector_in, OUTPUT = vector_out,
       TYPMOD_IN = vector_typmod_in, RECEIVE = vector_recv,
       SEND = vector_send, STORAGE = external)                      L33-L40
     CREATE CAST (vector AS vector) WITH FUNCTION vector(...)       L234
 ------------------------------------------------------------------------
 라이브러리가 처음 올라올 때
 [01] _PG_init                               vector.c      L58
      +-- BitvecInit / HalfvecInit           CPU 에 맞는 거리 함수 포인터 선택
      +-- HnswInit / IvfflatInit             reloption, GUC 등록  --> [거리 연산자와 Index AM]
 ------------------------------------------------------------------------
 값 하나의 입출력 (모두 vector.c)
 텍스트 입력   '[1,2,3]'::vector(3)
 [02] vector_in                                            L177
      +-- 글자를 strtof 로 하나씩 읽어 스택 배열 x[16000] 에   L229
      +-- CheckDim / CheckExpectedDim(typmod, dim)          L273-L274
      +-- InitVector(dim) 에 복사                           L276
 [03] vector_typmod_in   vector(3) 의 "3" 을 typmod 로      L344
 [04] vector             vector(3) 열에 넣을 때 차원 강제     L429
 텍스트 출력
 [05] vector_out         float_to_shortest_decimal 로 최단 표기  L290
 이진 입출력 (COPY BINARY, 확장 쿼리 프로토콜)
 [06] vector_recv / vector_send                            L375 / L409
 배열에서
 [07] array_to_vector    int4[], float8[], float4[], numeric[] -> vector   L444
```

네 타입의 값 모양을 나란히 놓으면 다음과 같다. `vector` 와 `halfvec` 은 원소 크기만 다르고, `sparsevec` 은 0 이 아닌 원소의 위치와 값을 따로 둔다. `bit` 는 pgvector 가 만든 타입이 아니라 PostgreSQL 의 `bit` 다.

```text
 값 모양 (varlena, 앞 4바이트는 길이 헤더)

 vector    vector.h L18-L24
 +--------+-------+--------+-------+-------+-----+
 | vl_len | dim   | unused | x[0]  | x[1]  | ... |   x = float(4바이트) * dim
 | int32  | int16 | int16  | float | float |     |   VECTOR_SIZE(dim) = 8 + 4*dim
 +--------+-------+--------+-------+-------+-----+   VECTOR_MAX_DIM 16000

 halfvec   halfvec.h L67-L73
 +--------+-------+--------+-------+-------+-----+
 | vl_len | dim   | unused | x[0]  | x[1]  | ... |   x = half(2바이트) * dim
 +--------+-------+--------+-------+-------+-----+   HALFVEC_MAX_DIM 16000

 sparsevec sparsevec.h L22-L29
 +--------+-------+-------+--------+------------------+-----------------+
 | vl_len | dim   | nnz   | unused | indices[nnz]     | values[nnz]     |
 | int32  | int32 | int32 | int32  | int32, 0 부터    | float           |
 +--------+-------+-------+--------+------------------+-----------------+
   indices 는 항상 정렬. SPARSEVEC_MAX_DIM 10억, SPARSEVEC_MAX_NNZ 16000

 bit       PostgreSQL 의 VarBit (bit 길이 + 바이트 배열)
```

`'[1,2,3]'::vector(3)` 한 값이 지나는 크기를 소스 규칙대로 세면 다음과 같다.

```text
 '[1,2,3]'::vector(3)

 vector_typmod_in({"3"})  -> typmod 3
 vector_in('[1,2,3]', oid, 3)
   x = {1.0, 2.0, 3.0}, dim = 3
   CheckExpectedDim(3, 3) 통과
   InitVector(3)  VECTOR_SIZE(3) = offsetof(Vector, x) 8 + 4*3 = 20 바이트
 +----------+------+--------+-----+-----+-----+
 | 20       | 3    | 0      | 1.0 | 2.0 | 3.0 |
 +----------+------+--------+-----+-----+-----+
   0          4      6        8     12    16     (바이트 위치)

 vector_send 로 나가면  dim(2) + unused(2) + float4 * 3 = 16 바이트
 vector_out  으로 나가면 "[1,2,3]"
```

## 어디에서 쓰이는가

```text
 [거리 연산자와 Index AM]  <->, <=> 같은 연산자 함수가 모두 PG_GETARG_VECTOR_P 로
                            이 모양을 꺼내 a->dim, a->x 를 읽는다
 [HNSW 빌드] [IVFFlat]      인덱스 열의 atttypmod 를 차원 수로 쓴다
                            typmod 가 없으면(-1) "column does not have dimensions"
 상위 [행 쓰기와 WAL 기록]  INSERT 의 값은 vector_in 을 거친 Datum 으로 heap_insert 에 들어간다
```

상위 PostgreSQL 지도의 [행 쓰기와 WAL 기록](../../../../architecture/flows/heap-insert-wal/README.md)이 이 값이 힙 페이지에 놓이는 길이다.

## 단계

1. [_PG_init](01__PG_init/README.md)이 라이브러리 로드 때 SIMD 디스패치와 인덱스 옵션 등록을 한 번에 한다.
2. [vector_in](02_vector_in/README.md)이 `'[...]'` 문자열을 파싱해 `Vector` 를 만든다.
3. [vector_typmod_in](03_vector_typmod_in/README.md)이 `vector(n)` 의 n 을 검사해 typmod 로 돌려준다.
4. [vector](04_vector/README.md)가 이미 만들어진 값을 typmod 열에 넣을 때 차원을 강제한다.
5. [vector_out](05_vector_out/README.md)이 값을 최단 십진 표기 문자열로 바꾼다.
6. [vector_recv](06_vector_recv/README.md)와 `vector_send` 가 이진 형식으로 주고받는다.
7. [array_to_vector](07_array_to_vector/README.md)가 배열을 `vector` 로 바꾼다.

## 결과가 쓰이는 곳

```text
 Vector 값 (varlena)
      --> 힙 튜플의 열 값으로 저장된다 (STORAGE = external 이라 TOAST 될 때 압축 없이 밖으로 나간다)
      --> 함수가 받을 때는 DatumGetVector = PG_DETOAST_DATUM 으로 펼친다 (vector.h L14)
      --> HNSW 원소 튜플의 data 칸에 통째로 복사된다 (hnsw.h L382)
      --> IVFFlat 리스트 튜플의 center 칸에 중심점이 같은 모양으로 들어간다 (ivfflat.h L275)

 typmod (차원 수)
      --> 인덱스 빌드가 TupleDescAttr(index->rd_att, 0)->atttypmod 로 읽는다
          (hnswbuild.c L697, ivfbuild.c L352)
```

## 다루지 않는 것

`halfvec` 과 `sparsevec` 의 입출력 함수(`halfvec_in` halfvec.c L181, `sparsevec_in` sparsevec.c L204)는 같은 틀에 원소 형식만 다르므로 따로 문서를 두지 않았다. 덧셈·뺄셈·곱셈 연산자(`vector_add` 등), 비교 연산자와 B-tree 연산자 클래스 `vector_ops`(`vector_cmp`), 집계 `avg`/`sum`(`vector_accum`, `vector_avg`), `subvector`, `binary_quantize`, 타입 사이 cast(`halfvec_to_vector`, `sparsevec_to_vector`), 확장 업그레이드 스크립트(`sql/vector--*.sql`)는 요약만 하거나 다루지 않았다. 거리 함수는 [거리 연산자와 Index AM](../operators-index-am/README.md)에 있다.

## 하위 메서드

- [01 _PG_init](01__PG_init/README.md)
- [02 vector_in](02_vector_in/README.md)
- [03 vector_typmod_in](03_vector_typmod_in/README.md)
- [04 vector](04_vector/README.md)
- [05 vector_out](05_vector_out/README.md)
- [06 vector_recv](06_vector_recv/README.md)
- [07 array_to_vector](07_array_to_vector/README.md)
