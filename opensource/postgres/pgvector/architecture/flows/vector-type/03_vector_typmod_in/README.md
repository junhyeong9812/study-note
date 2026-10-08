# vector_typmod_in

상위: [확장 로드와 vector 타입](../README.md)

**`vector(3)` 처럼 타입 이름 뒤 괄호에 적은 값을 정수 typmod 하나로 바꾸는 함수다.** 인자가 정확히 하나이고 1 이상 16000 이하인지만 본다. 돌려준 값은 열 정의의 `atttypmod` 에 저장되고, 그 열에 들어오는 값의 차원 검사와 인덱스 빌드의 차원 수로 다시 쓰인다.

## 위치

`src` / `vector.c` L344-L369 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L344-L369))

## 실제 코드

타입 등록문에서 이 함수가 `TYPMOD_IN` 으로 꽂힌다.

`sql` / `vector.sql` L33-L40 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L33-L40))

```sql
-- vector.sql L33-L40
CREATE TYPE vector (
	INPUT     = vector_in,
	OUTPUT    = vector_out,
	TYPMOD_IN = vector_typmod_in,
	RECEIVE   = vector_recv,
	SEND      = vector_send,
	STORAGE   = external
);
```

```c
// vector.c L344-L369
Datum
vector_typmod_in(PG_FUNCTION_ARGS)
{
	ArrayType  *ta = PG_GETARG_ARRAYTYPE_P(0);
	int32	   *tl;
	int			n;

	tl = ArrayGetIntegerTypmods(ta, &n);

	if (n != 1)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("invalid type modifier")));

	if (*tl < 1)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("dimensions for type vector must be at least 1")));

	if (*tl > VECTOR_MAX_DIM)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("dimensions for type vector cannot exceed %d", VECTOR_MAX_DIM)));

	PG_RETURN_INT32(*tl);
}
```

## 동작 흐름

```text
 CREATE TABLE items (embedding vector(3))
   파서가 타입 수식어 "3" 을 cstring[] 로 모아 TYPMOD_IN 함수를 부른다

 vector_typmod_in({"3"})                            L344
   L351  ArrayGetIntegerTypmods -> tl = {3}, n = 1
   L353  n != 1   -> "invalid type modifier"         vector(3,4) 는 여기서
   L358  *tl < 1  -> "must be at least 1"            vector(0)
   L363  *tl > 16000 -> "cannot exceed 16000"        vector(16001)
   L368  return 3
   --> pg_attribute.atttypmod = 3
```

typmod 는 정의에서 한 번 정해지고, 이후 값이 그 열을 지날 때 두 곳에서 검사에 쓰인다.

```text
 typmod 3 이 다시 읽히는 자리

 값 입력       vector_in(cstring, oid, typmod)     세 번째 인자   L181
                 CheckExpectedDim(typmod, dim)                     L274
 값 강제       vector(vector, typmod, bool)         두 번째 인자   L433  --> [04]
                 CheckExpectedDim(typmod, vec->dim)                L435
 이진 입력     vector_recv(internal, oid, typmod)                  L379, L388
 배열 cast     array_to_vector(array, typmod, bool)                L448, L470
 인덱스 빌드   TupleDescAttr(index->rd_att, 0)->atttypmod
                 hnswbuild.c L697, ivfbuild.c L352
                 -1 (typmod 없는 열) 이면 "column does not have dimensions"
```

`vector` 처럼 typmod 없이 정의한 열은 `atttypmod = -1` 이다. `CheckExpectedDim` 은 -1 이면 아무것도 보지 않으므로(L85) 값마다 차원이 달라도 저장은 된다. 대신 HNSW 와 IVFFlat 인덱스는 만들 수 없다.

## 결과가 쓰이는 곳

```text
 typmod (int32)
      --> pg_attribute.atttypmod 로 카탈로그에 남는다
      --> [04] vector cast, [02] vector_in, [06] vector_recv, [07] array_to_vector 의 검사 기준
      --> [HNSW 빌드] InitBuildState, [IVFFlat 빌드와 검색] InitBuildState 의 dimensions
```

## 다루지 않는 것

`ArrayGetIntegerTypmods`(PostgreSQL 의 공용 함수)의 내부는 다루지 않는다. `CREATE TYPE` 에는 `TYPMOD_OUT` 이 없어서 typmod 를 글자로 바꾸는 쪽은 PostgreSQL 기본 동작에 맡긴다. `halfvec_typmod_in`, `sparsevec_typmod_in` 은 같은 틀이다.
