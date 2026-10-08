# array_to_vector

상위: [확장 로드와 vector 타입](../README.md)

**`integer[]`, `real[]`, `double precision[]`, `numeric[]` 을 `vector` 로 바꾸는 cast 함수다.** 1차원이고 NULL 이 없는 배열만 받는다. 원소 타입마다 `float` 로 바꾸는 방법이 다르고, 바꾼 뒤에야 NaN·무한대를 검사한다. 네 cast 모두 `AS ASSIGNMENT` 라서 `INSERT` 의 대입 자리에서는 명시적 cast 없이도 불린다.

## 위치

`src` / `vector.c` L444-L512 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L444-L512))

## 실제 코드

`sql` / `vector.sql` L237-L250 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L237-L250))

```sql
-- vector.sql L237-L250
CREATE CAST (vector AS real[])
	WITH FUNCTION vector_to_float4(vector, integer, boolean) AS IMPLICIT;

CREATE CAST (integer[] AS vector)
	WITH FUNCTION array_to_vector(integer[], integer, boolean) AS ASSIGNMENT;

CREATE CAST (real[] AS vector)
	WITH FUNCTION array_to_vector(real[], integer, boolean) AS ASSIGNMENT;

CREATE CAST (double precision[] AS vector)
	WITH FUNCTION array_to_vector(double precision[], integer, boolean) AS ASSIGNMENT;

CREATE CAST (numeric[] AS vector)
	WITH FUNCTION array_to_vector(numeric[], integer, boolean) AS ASSIGNMENT;
```

```c
// vector.c L440-L512
/*
 * Convert array to vector
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(array_to_vector);
Datum
array_to_vector(PG_FUNCTION_ARGS)
{
	ArrayType  *array = PG_GETARG_ARRAYTYPE_P(0);
	int32		typmod = PG_GETARG_INT32(1);
	Vector	   *result;
	int16		typlen;
	bool		typbyval;
	char		typalign;
	Datum	   *elemsp;
	int			nelemsp;

	if (ARR_NDIM(array) > 1)
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("array must be 1-D")));

	if (ARR_HASNULL(array) && array_contains_nulls(array))
		ereport(ERROR,
				(errcode(ERRCODE_NULL_VALUE_NOT_ALLOWED),
				 errmsg("array must not contain nulls")));

	get_typlenbyvalalign(ARR_ELEMTYPE(array), &typlen, &typbyval, &typalign);
	deconstruct_array(array, ARR_ELEMTYPE(array), typlen, typbyval, typalign, &elemsp, NULL, &nelemsp);

	CheckDim(nelemsp);
	CheckExpectedDim(typmod, nelemsp);

	result = InitVector(nelemsp);

	if (ARR_ELEMTYPE(array) == INT4OID)
	{
		for (int i = 0; i < nelemsp; i++)
			result->x[i] = DatumGetInt32(elemsp[i]);
	}
	else if (ARR_ELEMTYPE(array) == FLOAT8OID)
	{
		for (int i = 0; i < nelemsp; i++)
			result->x[i] = DatumGetFloat8(elemsp[i]);
	}
	else if (ARR_ELEMTYPE(array) == FLOAT4OID)
	{
		for (int i = 0; i < nelemsp; i++)
			result->x[i] = DatumGetFloat4(elemsp[i]);
	}
	else if (ARR_ELEMTYPE(array) == NUMERICOID)
	{
		for (int i = 0; i < nelemsp; i++)
			result->x[i] = DatumGetFloat4(DirectFunctionCall1(numeric_float4, elemsp[i]));
	}
	else
	{
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("unsupported array type")));
	}

	/*
	 * Free allocation from deconstruct_array. Do not free individual elements
	 * when pass-by-reference since they point to original array.
	 */
	pfree(elemsp);

	/* Check elements */
	for (int i = 0; i < result->dim; i++)
		CheckElement(result->x[i]);

	PG_RETURN_POINTER(result);
}
```

## 동작 흐름

```text
 array_to_vector(array, typmod, explicit)           L444
   L456  ARR_NDIM > 1         -> "array must be 1-D"
   L461  NULL 원소가 있으면    -> "array must not contain nulls"
   L466  get_typlenbyvalalign + deconstruct_array -> elemsp[], nelemsp
   L469  CheckDim(nelemsp)
   L470  CheckExpectedDim(typmod, nelemsp)
   L472  InitVector(nelemsp)
   L474  원소 타입별로 float 에 넣는다
           INT4OID     DatumGetInt32       L477
           FLOAT8OID   DatumGetFloat8      L482
           FLOAT4OID   DatumGetFloat4      L487
           NUMERICOID  numeric_float4 호출  L492
           그 밖       "unsupported array type"
   L505  pfree(elemsp)          배열 껍데기만. 원소는 원래 배열을 가리킨다 (주석 L501-L504)
   L508  CheckElement 를 원소마다   NaN, inf 거절
```

```text
 원소 타입마다 float 로 가는 길

 '{1,2,3}'::int[]               int32 -> float      정수 그대로 (큰 수는 반올림)
 '{0.1,0.2}'::float8[]          double -> float     정밀도가 줄어든다
 '{1e39}'::float8[]             double -> float     inf 가 되어 L508 에서 거절
 '{1.5}'::numeric[]             numeric_float4 를 거친다
 '{1,NULL}'::int[]              L461 에서 거절
```

검사 순서가 `vector_in` 과 다르다. 텍스트 입력은 원소를 읽는 즉시 검사하지만(L242), 배열 입력은 `float` 로 다 옮긴 다음 한꺼번에 검사한다(L508). `double` 의 큰 값은 옮기는 순간에야 무한대가 되므로 옮긴 뒤에 보는 것이 맞다.

반대 방향 `vector` -> `real[]` 는 `vector_to_float4`(L518)가 맡고 `AS IMPLICIT` 로 등록된다.

## 결과가 쓰이는 곳

```text
 Vector *
      --> INSERT INTO items VALUES (ARRAY[1,2,3]) 의 대입 cast 결과로 힙에 저장된다
      --> 응용이 float 배열을 그대로 넘기는 드라이버 경로
```

## 다루지 않는 것

`deconstruct_array` 와 `numeric_float4` 의 내부, `halfvec`/`sparsevec` 쪽 배열 cast(`array_to_halfvec`, `array_to_sparsevec`)는 같은 틀이라 다루지 않았다.
