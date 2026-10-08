# vector

상위: [확장 로드와 vector 타입](../README.md)

**`vector` 에서 `vector` 로 가는 cast 함수이고, 하는 일은 typmod 검사 하나다.** 이미 만들어진 값이 `vector(3)` 같은 차원 고정 열이나 식으로 들어갈 때 PostgreSQL 이 길이 강제(length coercion) 함수로 이것을 부른다. 값은 건드리지 않고 그대로 돌려준다.

## 위치

`src` / `vector.c` L429-L438 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L429-L438))

## 실제 코드

자기 자신으로 가는 cast 로 등록된다. 함수 인자가 `(vector, integer, boolean)` 세 개인 것이 길이 강제 함수의 꼴이다.

`sql` / `vector.sql` L234-L235 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L234-L235))

```sql
-- vector.sql L234-L235
CREATE CAST (vector AS vector)
	WITH FUNCTION vector(vector, integer, boolean) AS IMPLICIT;
```

```c
// vector.c L424-L438
/*
 * Convert vector to vector
 * This is needed to check the type modifier
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(vector);
Datum
vector(PG_FUNCTION_ARGS)
{
	Vector	   *vec = PG_GETARG_VECTOR_P(0);
	int32		typmod = PG_GETARG_INT32(1);

	CheckExpectedDim(typmod, vec->dim);

	PG_RETURN_POINTER(vec);
}
```

`src` / `vector.c` L79-L89 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L79-L89))

```c
// vector.c L79-L89
/*
 * Ensure expected dimensions
 */
static inline void
CheckExpectedDim(int32 typmod, int dim)
{
	if (typmod != -1 && typmod != dim)
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("expected %d dimensions, not %d", typmod, dim)));
}
```

## 동작 흐름

```text
 vector(vec, typmod, explicit)                      L429
   L432  vec = PG_GETARG_VECTOR_P(0)       detoast 한 값
   L433  typmod = PG_GETARG_INT32(1)
   L435  CheckExpectedDim(typmod, vec->dim)
           typmod == -1          -> 검사 없음        L85
           typmod != vec->dim    -> "expected %d dimensions, not %d"
   L437  같은 포인터를 돌려준다 (복사 없음)
```

```text
 이 함수가 갈라 주는 두 경우

 INSERT INTO items (embedding) SELECT '[1,2]'::vector      embedding 은 vector(3) 열
   '[1,2]'::vector          vector_in, typmod -1 -> dim 2 값
   열 typmod 3 에 맞추기     vector(값, 3, false)
                              CheckExpectedDim(3, 2) -> ERROR expected 3 dimensions, not 2

 SELECT '[1,2,3]'::vector::vector(3)
   vector(값, 3, true)       CheckExpectedDim(3, 3) -> 통과, 같은 값
```

세 번째 인자(명시적 cast 여부)는 받지만 읽지 않는다. 문자열 길이처럼 잘라 맞추는 일이 없으므로 명시적이든 암묵적이든 결과가 같다.

## 결과가 쓰이는 곳

```text
 같은 Vector 포인터
      --> 차원이 맞는다는 보장을 얻은 채 힙 튜플에 저장된다
      --> 그 열의 HNSW/IVFFlat 인덱스는 typmod 를 dimensions 로 믿고 쓴다
          (값마다 다시 HnswCheckDim / IvfflatCheckDim 으로도 검사한다)
```

## 다루지 않는 것

PostgreSQL 이 길이 강제 함수를 언제 끼워 넣는지(`coerce_type_typmod`)는 서버 쪽 규칙이라 다루지 않았다. `halfvec(halfvec, integer, boolean)`, `sparsevec(sparsevec, integer, boolean)` 도 같은 일을 한다.
