# l2_distance

상위: [거리 연산자와 Index AM 연결](../README.md)

**`<->` 연산자의 함수, 유클리드(L2) 거리다.** 차원이 같은지 보고, 원소 차의 제곱을 `float` 로 더한 뒤 마지막에 `sqrt` 를 한 번 씌운다. 인덱스는 이 함수가 아니라 `sqrt` 를 뺀 `vector_l2_squared_distance` 를 쓴다. 제곱근은 단조 증가라 대소 비교 결과가 같고, 원소마다 한 번씩 부르는 거리 계산에서 제곱근 한 번을 아낀다(주석 L592-L593 "This saves a sqrt calculation").

## 위치

`src` / `vector.c` L580-L589 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L580-L589))

## 실제 코드

`sql` / `vector.sql` L254-L257 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L254-L257))

```sql
-- vector.sql L254-L257
CREATE OPERATOR <-> (
	LEFTARG = vector, RIGHTARG = vector, PROCEDURE = l2_distance,
	COMMUTATOR = '<->'
);
```

```c
// vector.c L560-L605
VECTOR_TARGET_CLONES static float
VectorL2SquaredDistance(int dim, float *ax, float *bx)
{
	float		distance = 0.0;

	/* Auto-vectorized */
	for (int i = 0; i < dim; i++)
	{
		float		diff = ax[i] - bx[i];

		distance += diff * diff;
	}

	return distance;
}

/*
 * Get the L2 distance between vectors
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(l2_distance);
Datum
l2_distance(PG_FUNCTION_ARGS)
{
	Vector	   *a = PG_GETARG_VECTOR_P(0);
	Vector	   *b = PG_GETARG_VECTOR_P(1);

	CheckDims(a, b);

	PG_RETURN_FLOAT8(sqrt((double) VectorL2SquaredDistance(a->dim, a->x, b->x)));
}

/*
 * Get the L2 squared distance between vectors
 * This saves a sqrt calculation
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(vector_l2_squared_distance);
Datum
vector_l2_squared_distance(PG_FUNCTION_ARGS)
{
	Vector	   *a = PG_GETARG_VECTOR_P(0);
	Vector	   *b = PG_GETARG_VECTOR_P(1);

	CheckDims(a, b);

	PG_RETURN_FLOAT8((double) VectorL2SquaredDistance(a->dim, a->x, b->x));
}
```

차원 검사다.

`src` / `vector.c` L67-L77 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L67-L77))

```c
// vector.c L67-L77
/*
 * Ensure same dimensions
 */
static inline void
CheckDims(Vector * a, Vector * b)
{
	if (a->dim != b->dim)
		ereport(ERROR,
				(errcode(ERRCODE_DATA_EXCEPTION),
				 errmsg("different vector dimensions %d and %d", a->dim, b->dim)));
}
```

## 동작 흐름

```text
 '[1,2,3]' <-> '[4,6,3]'

 l2_distance(a, b)                                   L580
   L583  a = PG_GETARG_VECTOR_P(0)          detoast
   L586  CheckDims(a, b)                    3 == 3
   L588  VectorL2SquaredDistance(3, a->x, b->x)      L561
           i=0  diff = 1 - 4 = -3   distance = 9
           i=1  diff = 2 - 6 = -4   distance = 25
           i=2  diff = 3 - 3 =  0   distance = 25
         sqrt(25.0) = 5.0
   -> 5

 vector_l2_squared_distance(a, b)                    L596
   -> 25      인덱스 안에서는 이 값으로 비교한다
```

```text
 같은 연산자, 두 가지 호출 경로

 SELECT a <-> b                                  -> l2_distance           5
 ORDER BY a <-> b (순차 스캔 + 정렬)              -> l2_distance           5
 ORDER BY a <-> b (hnsw/ivfflat 인덱스 스캔)
   인덱스 안 비교, 후보 정렬                       -> vector_l2_squared_distance  25
   결과 행의 a <-> b 표시값                        -> 실행기가 l2_distance 로 다시 계산
 거리 순서 5 < 6  <=>  25 < 36 이라 정렬이 같다
```

`VectorL2SquaredDistance` 는 `float` 로 더한다. 주석 "Auto-vectorized"(L565)는 이 단순 루프를 컴파일러가 SIMD 로 펼친다는 뜻이고, `VECTOR_TARGET_CLONES`(L42-L46)가 FMA 판을 따로 하나 더 만든다.

`CheckDims` 가 차원이 다르면 오류를 낸다. 그래서 차원이 섞인 열(typmod 없는 `vector`)에 `<->` 를 쓰면 행에 따라 오류가 날 수 있다.

## 결과가 쓰이는 곳

```text
 float8
      --> SQL 결과값, 순차 스캔의 정렬 키
 vector_l2_squared_distance 의 float8
      --> HNSW: HnswGetDistance (hnswutils.c L532) 를 통해 그래프 탐색의 모든 비교
      --> IVFFlat: GetScanLists 의 중심점 거리, GetScanItems 의 정렬 키 (ivfscan.c L74, L167)
 l2_distance (FUNCTION 3)
      --> IVFFlat k-means 의 거리 (vector.sql L410)
```

## 다루지 않는 것

`l1_distance`(`<+>`, L741)는 `fabsf` 합이라는 점만 다르다. `halfvec` 의 F16C 판과 `sparsevec` 의 병합식 계산(sparsevec.c L888)은 같은 의미를 다른 저장 형식에서 계산한다.
