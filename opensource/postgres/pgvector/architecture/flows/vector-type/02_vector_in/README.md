# vector_in

상위: [확장 로드와 vector 타입](../README.md)

**`vector` 의 텍스트 입력 함수다.** `'[1,2,3]'` 을 앞에서부터 한 번 훑으며 `strtof` 로 원소를 읽어 스택의 `float x[16000]` 에 모으고, 끝에서 차원을 검사한 뒤 꼭 맞는 크기의 `Vector` 를 할당해 복사한다. NaN 과 무한대는 원소마다 거절한다.

## 위치

`src` / `vector.c` L177-L281 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L177-L281))

## 실제 코드

값의 모양은 헤더에 정의돼 있다. `dim` 이 `int16` 이라 차원 상한 16000 이 이 칸에 들어간다.

`src` / `vector.h` L11-L24 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.h#L11-L24))

```c
// vector.h L11-L24
#define VECTOR_MAX_DIM 16000

#define VECTOR_SIZE(_dim)		add_size(offsetof(Vector, x), mul_size(sizeof(float), _dim))
#define DatumGetVector(x)		((Vector *) PG_DETOAST_DATUM(x))
#define PG_GETARG_VECTOR_P(x)	DatumGetVector(PG_GETARG_DATUM(x))
#define PG_RETURN_VECTOR_P(x)	PG_RETURN_POINTER(x)

typedef struct Vector
{
	int32		vl_len_;		/* varlena header (do not touch directly!) */
	int16		dim;			/* number of dimensions */
	int16		unused;			/* reserved for future use, always zero */
	float		x[FLEXIBLE_ARRAY_MEMBER];
}			Vector;
```

```c
// vector.c L177-L281
Datum
vector_in(PG_FUNCTION_ARGS)
{
	char	   *lit = PG_GETARG_CSTRING(0);
	int32		typmod = PG_GETARG_INT32(2);
	float		x[VECTOR_MAX_DIM];
	int			dim = 0;
	char	   *pt = lit;
	Vector	   *result;

	while (vector_isspace(*pt))
		pt++;

	if (*pt != '[')
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_TEXT_REPRESENTATION),
				 errmsg("invalid input syntax for type vector: \"%s\"", lit),
				 errdetail("Vector contents must start with \"[\".")));

	pt++;

	while (vector_isspace(*pt))
		pt++;

	if (*pt == ']')
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("vector must have at least 1 dimension")));

	for (;;)
	{
		float		val;
		char	   *stringEnd;

		if (dim == VECTOR_MAX_DIM)
			ereport(ERROR,
					(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
					 errmsg("vector cannot have more than %d dimensions", VECTOR_MAX_DIM)));

		while (vector_isspace(*pt))
			pt++;

		/* Check for empty string like float4in */
		if (*pt == '\0')
			ereport(ERROR,
					(errcode(ERRCODE_INVALID_TEXT_REPRESENTATION),
					 errmsg("invalid input syntax for type vector: \"%s\"", lit)));

		errno = 0;

		/* Use strtof like float4in to avoid a double-rounding problem */
		/* Postgres sets LC_NUMERIC to C on startup */
		val = strtof(pt, &stringEnd);

		if (stringEnd == pt)
			ereport(ERROR,
					(errcode(ERRCODE_INVALID_TEXT_REPRESENTATION),
					 errmsg("invalid input syntax for type vector: \"%s\"", lit)));

		/* Check for range error like float4in */
		if (errno == ERANGE && isinf(val))
			ereport(ERROR,
					(errcode(ERRCODE_NUMERIC_VALUE_OUT_OF_RANGE),
					 errmsg("\"%s\" is out of range for type vector", pnstrdup(pt, stringEnd - pt))));

		CheckElement(val);
		x[dim++] = val;

		pt = stringEnd;

		while (vector_isspace(*pt))
			pt++;

		if (*pt == ',')
			pt++;
		else if (*pt == ']')
		{
			pt++;
			break;
		}
		else
			ereport(ERROR,
					(errcode(ERRCODE_INVALID_TEXT_REPRESENTATION),
					 errmsg("invalid input syntax for type vector: \"%s\"", lit)));
	}

	/* Only whitespace is allowed after the closing brace */
	while (vector_isspace(*pt))
		pt++;

	if (*pt != '\0')
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_TEXT_REPRESENTATION),
				 errmsg("invalid input syntax for type vector: \"%s\"", lit),
				 errdetail("Junk after closing right brace.")));

	CheckDim(dim);
	CheckExpectedDim(typmod, dim);

	result = InitVector(dim);
	for (int i = 0; i < dim; i++)
		result->x[i] = x[i];

	PG_RETURN_POINTER(result);
}
```

검사 함수 셋과 할당 함수다.

`src` / `vector.c` L79-L140 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L79-L140))

```c
// vector.c L79-L140
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

/*
 * Ensure valid dimensions
 */
static inline void
CheckDim(int dim)
{
	if (dim < 1)
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("vector must have at least 1 dimension")));

	if (dim > VECTOR_MAX_DIM)
		ereport(ERROR,
				(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
				 errmsg("vector cannot have more than %d dimensions", VECTOR_MAX_DIM)));
}

/*
 * Ensure finite element
 */
static inline void
CheckElement(float value)
{
	if (isnan(value))
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("NaN not allowed in vector")));

	if (isinf(value))
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("infinite value not allowed in vector")));
}

/*
 * Allocate and initialize a new vector
 */
Vector *
InitVector(int dim)
{
	Vector	   *result;
	Size		size;

	size = VECTOR_SIZE(dim);
	result = (Vector *) palloc0(size);
	SET_VARSIZE(result, size);
	result->dim = dim;

	return result;
}
```

## 동작 흐름

```text
 vector_in(lit, oid, typmod)                         L177
   L182  float x[VECTOR_MAX_DIM]     스택에 16000 * 4 = 64000 바이트
   L187  앞 공백 건너뛰기
   L190  '[' 가 아니면 "Vector contents must start with "[""
   L201  바로 ']' 면 "vector must have at least 1 dimension"

   L206  for (;;)                     원소 하나씩
     L211  dim == 16000 이면 "cannot have more than 16000 dimensions"
     L220  문자열 끝이면 형식 오류
     L229  val = strtof(pt, &stringEnd)
     L231  하나도 못 읽었으면 형식 오류
     L237  ERANGE 이고 inf 면 "out of range"
     L242  CheckElement(val)          NaN, inf 거절 (L111-L123)
     L243  x[dim++] = val
     L250  ','  -> 다음 원소
     L252  ']'  -> 루프 끝
           그 밖 -> 형식 오류

   L264  닫는 괄호 뒤에는 공백만 허용 ("Junk after closing right brace")
   L273  CheckDim(dim)                1 <= dim <= 16000
   L274  CheckExpectedDim(typmod, dim)  typmod 가 -1 이 아니면 같아야
   L276  InitVector(dim)              palloc0(8 + 4*dim), SET_VARSIZE, dim
   L277  x[] 를 result->x[] 로 복사
```

```text
 '[1, 2.5 ,3]' 을 읽는 순서 (pt 가 남은 문자열을 가리킨다)

 pt              line        action
 [1, 2.5 ,3]     L190 L196   '[' 확인, pt++
 1, 2.5 ,3]      L229 L243   strtof -> 1.0, x[0]
 , 2.5 ,3]       L250        ',' -> pt++
  2.5 ,3]        L216 L229   공백 건너뛰고 strtof -> 2.5, x[1]
  ,3]            L247 L250   공백 건너뛰고 ',' -> pt++
 3]              L229        strtof -> 3.0, x[2]
 ]               L252-L255   ']' -> pt++, break
 ""              L264-L267   뒤 공백 검사 통과
 dim = 3. typmod 가 3 이거나 -1 이면 통과
```

```text
 거절되는 입력과 걸리는 줄

 input            error                                       line
 '1,2,3'          Vector contents must start with "["         L190
 '[]'             vector must have at least 1 dimension       L201
 '[1,,2]'         invalid input syntax                        L231
 '[1,NaN]'        NaN not allowed in vector                   L242 -> L114
 '[1,1e39]'       "1e39" is out of range for type vector      L237
 '[1,2] x'        Junk after closing right brace              L267
 '[1,2]'::vector(3)  expected 3 dimensions, not 2            L274 -> L85
```

16000 차원 검사가 루프 안(L211)에도 있는 까닭은 `x` 가 고정 크기 스택 배열이기 때문이다. 원소를 하나 더 쓰기 전에 막지 않으면 배열 밖에 쓴다.

## 결과가 쓰이는 곳

```text
 Vector * (palloc 한 varlena)
      --> INSERT 의 열 값이 되어 힙에 저장된다
      --> 리터럴이면 쿼리 상수가 되어 ORDER BY v <-> '[...]' 의 검색 값이 된다
          (인덱스 스캔의 orderByData->sk_argument, [HNSW 검색] 04)
```

## 다루지 않는 것

`strtof` 의 로캘 처리(주석 L228: PostgreSQL 이 시작할 때 `LC_NUMERIC` 을 C 로 둔다), PostgreSQL 17 이상에서 `scanner_isspace` 를 쓰는 공백 판정(L142-L157), 소프트 오류 보고(`escontext`)를 쓰지 않는다는 점은 요약만 했다. `halfvec_in` 과 `sparsevec_in` 은 같은 틀이다.
