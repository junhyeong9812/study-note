# cosine_distance

상위: [거리 연산자와 Index AM 연결](../README.md)

**`<=>` 연산자의 함수, 코사인 거리 `1 - cos(a, b)` 다.** 내적과 두 노름 제곱을 한 루프에서 함께 더하고, 부동소수 오차로 유사도가 [-1, 1] 밖으로 나가면 잘라 낸다. 같은 파일의 내적 계열 함수 셋(`inner_product`, `<#>` 의 `vector_negative_inner_product`, k-means 용 `vector_spherical_distance`)을 함께 본다. 인덱스는 코사인 거리를 직접 쓰지 않고 정규화 + 음의 내적으로 대신한다.

## 위치

`src` / `vector.c` L672-L696 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L672-L696))

## 실제 코드

`sql` / `vector.sql` L259-L267 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L259-L267))

```sql
-- vector.sql L259-L267
CREATE OPERATOR <#> (
	LEFTARG = vector, RIGHTARG = vector, PROCEDURE = vector_negative_inner_product,
	COMMUTATOR = '<#>'
);

CREATE OPERATOR <=> (
	LEFTARG = vector, RIGHTARG = vector, PROCEDURE = cosine_distance,
	COMMUTATOR = '<=>'
);
```

```c
// vector.c L607-L722
VECTOR_TARGET_CLONES static float
VectorInnerProduct(int dim, float *ax, float *bx)
{
	float		distance = 0.0;

	/* Auto-vectorized */
	for (int i = 0; i < dim; i++)
		distance += ax[i] * bx[i];

	return distance;
}

/*
 * Get the inner product of two vectors
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(inner_product);
Datum
inner_product(PG_FUNCTION_ARGS)
{
	Vector	   *a = PG_GETARG_VECTOR_P(0);
	Vector	   *b = PG_GETARG_VECTOR_P(1);

	CheckDims(a, b);

	PG_RETURN_FLOAT8((double) VectorInnerProduct(a->dim, a->x, b->x));
}

/*
 * Get the negative inner product of two vectors
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(vector_negative_inner_product);
Datum
vector_negative_inner_product(PG_FUNCTION_ARGS)
{
	Vector	   *a = PG_GETARG_VECTOR_P(0);
	Vector	   *b = PG_GETARG_VECTOR_P(1);

	CheckDims(a, b);

	PG_RETURN_FLOAT8((double) -VectorInnerProduct(a->dim, a->x, b->x));
}

VECTOR_TARGET_CLONES static double
VectorCosineSimilarity(int dim, float *ax, float *bx)
{
	float		similarity = 0.0;
	float		norma = 0.0;
	float		normb = 0.0;

	/* Auto-vectorized */
	for (int i = 0; i < dim; i++)
	{
		similarity += ax[i] * bx[i];
		norma += ax[i] * ax[i];
		normb += bx[i] * bx[i];
	}

	/* Use sqrt(a * b) over sqrt(a) * sqrt(b) */
	return (double) similarity / sqrt((double) norma * (double) normb);
}

/*
 * Get the cosine distance between two vectors
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(cosine_distance);
Datum
cosine_distance(PG_FUNCTION_ARGS)
{
	Vector	   *a = PG_GETARG_VECTOR_P(0);
	Vector	   *b = PG_GETARG_VECTOR_P(1);
	double		similarity;

	CheckDims(a, b);

	similarity = VectorCosineSimilarity(a->dim, a->x, b->x);

#ifdef _MSC_VER
	/* /fp:fast may not propagate NaN */
	if (isnan(similarity))
		PG_RETURN_FLOAT8(NAN);
#endif

	/* Keep in range */
	if (similarity > 1)
		similarity = 1.0;
	else if (similarity < -1)
		similarity = -1.0;

	PG_RETURN_FLOAT8(1.0 - similarity);
}

/*
 * Get the distance for spherical k-means
 * Currently uses angular distance since needs to satisfy triangle inequality
 * Assumes inputs are unit vectors (skips norm)
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(vector_spherical_distance);
Datum
vector_spherical_distance(PG_FUNCTION_ARGS)
{
	Vector	   *a = PG_GETARG_VECTOR_P(0);
	Vector	   *b = PG_GETARG_VECTOR_P(1);
	double		distance;

	CheckDims(a, b);

	distance = (double) VectorInnerProduct(a->dim, a->x, b->x);

	/* Prevent NaN with acos with loss of precision */
	if (distance > 1)
		distance = 1;
	else if (distance < -1)
		distance = -1;

	PG_RETURN_FLOAT8(acos(distance) / M_PI);
}
```

## 동작 흐름

```text
 '[1,0]' <=> '[1,1]'

 cosine_distance(a, b)                               L672
   L679  CheckDims
   L681  VectorCosineSimilarity(2, a->x, b->x)       L650
           similarity = 1*1 + 0*1 = 1
           norma = 1,  normb = 2
           return 1 / sqrt(1 * 2) = 0.7071           sqrt(a*b) 한 번 (주석 L664)
   L690  1 보다 크면 1, -1 보다 작으면 -1 로 자른다
   L695  return 1 - 0.7071 = 0.2929
```

```text
 내적 계열 네 함수

 함수                            연산자  계산                     쓰임
 inner_product                  -       a . b                    SQL 함수
 vector_negative_inner_product  <#>     -(a . b)                 연산자, HNSW/IVFFlat FUNCTION 1
 cosine_distance                <=>     1 - a.b / (|a||b|)       연산자
 vector_spherical_distance      -       acos(a . b) / pi         IVFFlat FUNCTION 3 (k-means)

 <#> 가 음수를 돌려주는 까닭: ORDER BY 는 작은 값부터 오고, 내적은 클수록 가깝다
```

```text
 인덱스 안에서 <=> 가 바뀌는 모습 (vector_cosine_ops)

 SQL           a <=> q  = 1 - a.q / (|a||q|)
 인덱스 저장    a' = a/|a|           (HnswFormIndexValue, FUNCTION 2 가 있으므로)
 인덱스 검색    q' = q/|q|           (GetScanValue)
 인덱스 비교    -(a' . q')  = -cos(a, q)   = (a <=> q) - 1
 상수 1 만큼 밀린 값이라 순서가 같다
```

`vector_spherical_distance` 는 입력이 이미 단위 벡터라고 가정하고(주석 L701) 노름을 계산하지 않는다. `acos` 의 정의역을 벗어나지 않도록 내적을 [-1, 1] 로 자르고(L716-L719), `pi` 로 나눠 [0, 1] 범위의 각 거리로 만든다. 주석(L700)은 k-means 가 삼각 부등식을 만족하는 거리를 필요로 해서 각 거리를 쓴다고 적는다.

## 결과가 쓰이는 곳

```text
 cosine_distance        --> SQL 결과값, 인덱스를 쓰지 않는 정렬
 vector_negative_inner_product
                        --> HNSW 그래프 탐색, IVFFlat 리스트 선택과 정렬
 vector_spherical_distance
                        --> ElkanKmeans, InitCenters (IVFFLAT_KMEANS_DISTANCE_PROC)
```

## 다루지 않는 것

MSVC `/fp:fast` 에서 NaN 이 전파되지 않을 수 있어 따로 검사하는 분기(L683-L687), `halfvec`·`sparsevec` 판, `bit` 의 `jaccard_distance` 는 다루지 않았다.
