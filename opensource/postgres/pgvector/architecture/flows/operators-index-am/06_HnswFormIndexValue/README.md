# HnswFormIndexValue

상위: [거리 연산자와 Index AM 연결](../README.md)

**힙에서 온 열 값을 인덱스에 넣을 모양으로 다듬는 함수다.** TOAST 를 한 번 풀고, 타입별 값 검사를 하고, 연산자 클래스에 정규화 함수(FUNCTION 2)가 있으면 크기가 0 인 벡터는 버리고 나머지는 단위 벡터로 바꾼다. 코사인 거리 인덱스가 실제로는 "정규화된 벡터의 음의 내적" 인덱스가 되는 자리가 여기다.

## 위치

`src` / `hnswutils.c` L411-L433 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L411-L433))

## 실제 코드

```c
// hnswutils.c L161-L177
/*
 * Normalize value
 */
Datum
HnswNormValue(const HnswTypeInfo * typeInfo, Oid collation, Datum value)
{
	return DirectFunctionCall1Coll(typeInfo->normalize, collation, value);
}

/*
 * Check if non-zero norm
 */
bool
HnswCheckNorm(HnswSupport * support, Datum value)
{
	return DatumGetFloat8(FunctionCall1Coll(support->normprocinfo, support->collation, value)) > 0;
}
```

```c
// hnswutils.c L408-L433
/*
 * Form index value
 */
bool
HnswFormIndexValue(Datum *out, Datum *values, bool *isnull, const HnswTypeInfo * typeInfo, HnswSupport * support)
{
	/* Detoast once for all calls */
	Datum		value = PointerGetDatum(PG_DETOAST_DATUM(values[0]));

	/* Check value */
	if (typeInfo->checkValue != NULL)
		typeInfo->checkValue(DatumGetPointer(value));

	/* Normalize if needed */
	if (support->normprocinfo != NULL)
	{
		if (!HnswCheckNorm(support, value))
			return false;

		value = HnswNormValue(typeInfo, support->collation, value);
	}

	*out = value;

	return true;
}
```

정규화는 타입 정보의 `normalize`, `vector` 에서는 `l2_normalize` 다.

`src` / `vector.c` L786-L819 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L786-L819))

```c
// vector.c L782-L819
/*
 * Normalize a vector with the L2 norm
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(l2_normalize);
Datum
l2_normalize(PG_FUNCTION_ARGS)
{
	Vector	   *a = PG_GETARG_VECTOR_P(0);
	float	   *ax = a->x;
	double		norm = 0;
	Vector	   *result;
	float	   *rx;

	result = InitVector(a->dim);
	rx = result->x;

	/* Auto-vectorized */
	for (int i = 0; i < a->dim; i++)
		norm += (double) ax[i] * (double) ax[i];

	norm = sqrt(norm);

	/* Return zero vector for zero norm */
	if (norm > 0)
	{
		for (int i = 0; i < a->dim; i++)
			rx[i] = ax[i] / norm;

		/* Check for overflow */
		for (int i = 0; i < a->dim; i++)
		{
			if (isinf(rx[i]))
				float_overflow_error();
		}
	}

	PG_RETURN_POINTER(result);
}
```

## 동작 흐름

```text
 HnswFormIndexValue(&out, values, isnull, typeInfo, support)    L411
   L415  value = PG_DETOAST_DATUM(values[0])     이후 거리 계산마다 풀지 않게 한 번
   L418  checkValue 가 있으면 (sparsevec 만) nnz <= 1000 검사
   L422  normprocinfo 가 있으면
           L424  HnswCheckNorm: vector_norm(value) > 0 ?
                   아니면 return false  -> 이 행은 인덱스에 들어가지 않는다
           L427  value = l2_normalize(value)
   L430  *out = value, return true
```

```text
 '[3,4]' 를 vector_cosine_ops 인덱스에 넣을 때

 vector_norm([3,4]) = sqrt(9 + 16) = 5 > 0          통과
 l2_normalize       = [3/5, 4/5] = [0.6, 0.8]        이 값이 원소 튜플에 저장된다

 '[0,0]' 이면 norm 0 -> false
   빌드: InsertTuple 이 false 를 그대로 돌려 indtuples 를 세지 않는다 (hnswbuild.c L500)
   삽입: HnswInsertTuple 이 return (hnswinsert.c L762)
   -> 이 행은 cosine 인덱스 스캔 결과에 나오지 않는다
```

```text
 정규화가 있을 때와 없을 때 인덱스 안의 거리

 vector_ip_ops      저장 a,          검색 q          거리 -(a . q)
 vector_cosine_ops  저장 a/|a|,      검색 q/|q|      거리 -(a/|a| . q/|q|) = cos 유사도의 음수
                                                     cosine_distance = 1 - cos 와 순서가 같다
 검색 값의 정규화는 GetScanValue (hnswscan.c L114-L115)
```

## 결과가 쓰이는 곳

```text
 out (정규화된 Datum)
      --> [HNSW 빌드] InsertTuple 이 원소에 복사 (hnswbuild.c L567)
      --> hnswinsert 의 HnswInsertTupleOnDisk 로 (hnswinsert.c L765)
 false
      --> 그 행은 인덱스에 없다. 힙에는 그대로 있다
```

## 다루지 않는 것

`halfvec_l2_normalize`, `sparsevec_l2_normalize` 는 같은 일을 원소 형식만 달리 한다. IVFFlat 은 같은 판정을 `AddTupleToSort`(ivfbuild.c L177-L183)에서 하고, k-means 표본은 FUNCTION 4 로 따로 판정한다(`AddSample` L72-L76).
