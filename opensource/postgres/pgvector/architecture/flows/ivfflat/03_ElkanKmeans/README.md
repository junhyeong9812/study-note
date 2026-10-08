# ElkanKmeans

상위: [IVFFlat 빌드와 검색](../README.md)

**표본으로 `lists` 개의 중심점을 구하는 k-means 다.** 시작점은 k-means++ 로 고른다(`InitCenters`). 반복은 Elkan 의 가속 방식을 쓴다. 점과 중심점 사이 거리의 상한·하한과 중심점끼리의 거리를 들고 다니며, 삼각 부등식으로 "이 중심점이 더 가까울 리 없다"가 확인되는 계산은 건너뛴다. 최대 500 회 반복하고, 한 바퀴 동안 배정이 하나도 바뀌지 않으면 멈춘다. 이 방식이 삼각 부등식을 쓰기 때문에 거리 함수도 따로 받는다(L238-L242: L2 연산자 클래스는 제곱 아닌 L2, 내적·코사인은 각 거리).

## 위치

`src` / `ivfkmeans.c` L246-L485 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfkmeans.c#L246-L485))

## 실제 코드

입구 함수다. 표본이 하나도 없으면 무작위 중심점을 쓴다.

`src` / `ivfkmeans.c` L553-L570 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfkmeans.c#L553-L570))

```c
// ivfkmeans.c L549-L570
/*
 * Perform naive k-means centering
 * We use spherical k-means for inner product and cosine
 */
void
IvfflatKmeans(Relation index, VectorArray samples, VectorArray centers, const IvfflatTypeInfo * typeInfo, Size memoryUsed)
{
	MemoryContext kmeansCtx = AllocSetContextCreate(CurrentMemoryContext,
													"Ivfflat kmeans temporary context",
													ALLOCSET_DEFAULT_SIZES);
	MemoryContext oldCtx = MemoryContextSwitchTo(kmeansCtx);

	if (samples->length == 0)
		RandomCenters(index, centers, typeInfo);
	else
		ElkanKmeans(index, samples, centers, typeInfo, memoryUsed);

	CheckCenters(index, centers, typeInfo);

	MemoryContextSwitchTo(oldCtx);
	MemoryContextDelete(kmeansCtx);
}
```

k-means++ 시작점이다.

`src` / `ivfkmeans.c` L23-L91 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfkmeans.c#L23-L91))

```c
// ivfkmeans.c L18-L91
/*
 * Initialize with kmeans++
 *
 * https://theory.stanford.edu/~sergei/papers/kMeansPP-soda.pdf
 */
static void
InitCenters(Relation index, VectorArray samples, VectorArray centers, float *lowerBound)
{
	FmgrInfo   *procinfo;
	Oid			collation;
	float	   *weight = palloc_array_checked(float, samples->length);
	int			numCenters = centers->maxlen;
	int			numSamples = samples->length;

	procinfo = index_getprocinfo(index, 1, IVFFLAT_KMEANS_DISTANCE_PROC);
	collation = index->rd_indcollation[0];

	/* Choose an initial center uniformly at random */
	VectorArraySet(centers, 0, VectorArrayGet(samples, RandomInt() % samples->length));
	centers->length++;

	for (int i = 0; i < numSamples; i++)
		weight[i] = FLT_MAX;

	for (int i = 0; i < numCenters; i++)
	{
		int			j;
		double		sum;
		double		choice;

		CHECK_FOR_INTERRUPTS();

		sum = 0.0;

		for (j = 0; j < numSamples; j++)
		{
			Datum		vec = PointerGetDatum(VectorArrayGet(samples, j));
			double		distance;

			/* Only need to compute distance for new center */
			/* TODO Use triangle inequality to reduce distance calculations */
			distance = DatumGetFloat8(FunctionCall2Coll(procinfo, collation, vec, PointerGetDatum(VectorArrayGet(centers, i))));

			/* Set lower bound */
			lowerBound[(Size) j * numCenters + i] = distance;

			/* Use distance squared for weighted probability distribution */
			distance *= distance;

			if (distance < weight[j])
				weight[j] = distance;

			sum += weight[j];
		}

		/* Only compute lower bound on last iteration */
		if (i + 1 == numCenters)
			break;

		/* Choose new center using weighted probability distribution. */
		choice = sum * RandomDouble();
		for (j = 0; j < numSamples - 1; j++)
		{
			choice -= weight[j];
			if (choice <= 0)
				break;
		}

		VectorArraySet(centers, i + 1, VectorArrayGet(samples, j));
		centers->length++;
	}

	pfree(weight);
}
```

```c
// ivfkmeans.c L238-L485
/*
 * Use Elkan for performance. This requires distance function to satisfy triangle inequality.
 *
 * We use L2 distance for L2 (not L2 squared like index scan)
 * and angular distance for inner product and cosine distance
 *
 * https://www.aaai.org/Papers/ICML/2003/ICML03-022.pdf
 */
static void
ElkanKmeans(Relation index, VectorArray samples, VectorArray centers, const IvfflatTypeInfo * typeInfo, Size memoryUsed)
{
	FmgrInfo   *procinfo;
	FmgrInfo   *normprocinfo;
	Oid			collation;
	int			dimensions = centers->dim;
	int			numCenters = centers->maxlen;
	int			numSamples = samples->length;
	VectorArray newCenters;
	float	   *agg;
	int		   *centerCounts;
	int		   *closestCenters;
	float	   *lowerBound;
	float	   *upperBound;
	float	   *s;
	float	   *halfcdist;
	float	   *newcdist;

	/* Calculate allocation sizes */
	Size		newCentersSize = VECTOR_ARRAY_SIZE(numCenters, centers->itemsize);
	Size		aggSize = mul_size(sizeof(float), mul_size(numCenters, dimensions));
	Size		centerCountsSize = mul_size(sizeof(int), numCenters);
	Size		closestCentersSize = mul_size(sizeof(int), numSamples);
	Size		lowerBoundSize = mul_size(sizeof(float), mul_size(numSamples, numCenters));
	Size		upperBoundSize = mul_size(sizeof(float), numSamples);
	Size		sSize = mul_size(sizeof(float), numCenters);
	Size		halfcdistSize = mul_size(sizeof(float), mul_size(numCenters, numCenters));
	Size		newcdistSize = mul_size(sizeof(float), numCenters);

	/* Calculate total size */
	Size		totalSize = memoryUsed;

	totalSize = add_size(totalSize, newCentersSize);
	totalSize = add_size(totalSize, aggSize);
	totalSize = add_size(totalSize, centerCountsSize);
	totalSize = add_size(totalSize, closestCentersSize);
	totalSize = add_size(totalSize, lowerBoundSize);
	totalSize = add_size(totalSize, upperBoundSize);
	totalSize = add_size(totalSize, sSize);
	totalSize = add_size(totalSize, halfcdistSize);
	totalSize = add_size(totalSize, newcdistSize);

	/* Check memory requirements */
	IvfflatCheckMemoryUsage(totalSize);

	/* Ensure indexing does not overflow */
	if (numCenters > INT_MAX / numCenters)
		elog(ERROR, "Indexing overflow detected. Please report a bug.");

	/* Set support functions */
	procinfo = index_getprocinfo(index, 1, IVFFLAT_KMEANS_DISTANCE_PROC);
	normprocinfo = IvfflatOptionalProcInfo(index, IVFFLAT_KMEANS_NORM_PROC);
	collation = index->rd_indcollation[0];

	/* Allocate space */
	/* Use float instead of double to save memory */
	agg = palloc(aggSize);
	centerCounts = palloc(centerCountsSize);
	closestCenters = palloc(closestCentersSize);
	lowerBound = palloc_extended(lowerBoundSize, MCXT_ALLOC_HUGE);
	upperBound = palloc(upperBoundSize);
	s = palloc(sSize);
	halfcdist = palloc_extended(halfcdistSize, MCXT_ALLOC_HUGE);
	newcdist = palloc(newcdistSize);

	/* Initialize new centers */
	newCenters = VectorArrayInit(numCenters, dimensions, centers->itemsize);
	newCenters->length = numCenters;

#ifdef IVFFLAT_MEMORY
	ShowMemoryUsage(MemoryContextGetParent(CurrentMemoryContext), totalSize);
#endif

	/* Pick initial centers */
	InitCenters(index, samples, centers, lowerBound);

	/* Assign each x to its closest initial center c(x) = argmin d(x,c) */
	for (int j = 0; j < numSamples; j++)
	{
		float		minDistance = FLT_MAX;
		int			closestCenter = 0;

		/* Find closest center */
		for (int k = 0; k < numCenters; k++)
		{
			/* TODO Use Lemma 1 in k-means++ initialization */
			float		distance = lowerBound[(Size) j * numCenters + k];

			if (distance < minDistance)
			{
				minDistance = distance;
				closestCenter = k;
			}
		}

		upperBound[j] = minDistance;
		closestCenters[j] = closestCenter;
	}

	/* Give 500 iterations to converge */
	for (int iteration = 0; iteration < 500; iteration++)
	{
		int			changes = 0;
		bool		rjreset;

		/* Can take a while, so ensure we can interrupt */
		CHECK_FOR_INTERRUPTS();

		/* Step 1: For all centers, compute distance */
		for (int j = 0; j < numCenters; j++)
		{
			Datum		vec = PointerGetDatum(VectorArrayGet(centers, j));

			for (int k = j + 1; k < numCenters; k++)
			{
				float		distance = 0.5 * DatumGetFloat8(FunctionCall2Coll(procinfo, collation, vec, PointerGetDatum(VectorArrayGet(centers, k))));

				halfcdist[(Size) j * numCenters + k] = distance;
				halfcdist[(Size) k * numCenters + j] = distance;
			}
		}

		/* For all centers c, compute s(c) */
		for (int j = 0; j < numCenters; j++)
		{
			float		minDistance = FLT_MAX;

			for (int k = 0; k < numCenters; k++)
			{
				float		distance;

				if (j == k)
					continue;

				distance = halfcdist[(Size) j * numCenters + k];
				if (distance < minDistance)
					minDistance = distance;
			}

			s[j] = minDistance;
		}

		rjreset = iteration != 0;

		for (int j = 0; j < numSamples; j++)
		{
			bool		rj;

			/* Step 2: Identify all points x such that u(x) <= s(c(x)) */
			if (upperBound[j] <= s[closestCenters[j]])
				continue;

			rj = rjreset;

			for (int k = 0; k < numCenters; k++)
			{
				Datum		vec;
				float		dxcx;

				/* Step 3: For all remaining points x and centers c */
				if (k == closestCenters[j])
					continue;

				if (upperBound[j] <= lowerBound[(Size) j * numCenters + k])
					continue;

				if (upperBound[j] <= halfcdist[(Size) closestCenters[j] * numCenters + k])
					continue;

				vec = PointerGetDatum(VectorArrayGet(samples, j));

				/* Step 3a */
				if (rj)
				{
					dxcx = DatumGetFloat8(FunctionCall2Coll(procinfo, collation, vec, PointerGetDatum(VectorArrayGet(centers, closestCenters[j]))));

					/* d(x,c(x)) computed, which is a form of d(x,c) */
					lowerBound[(Size) j * numCenters + closestCenters[j]] = dxcx;
					upperBound[j] = dxcx;

					rj = false;
				}
				else
					dxcx = upperBound[j];

				/* Step 3b */
				if (dxcx > lowerBound[(Size) j * numCenters + k] || dxcx > halfcdist[(Size) closestCenters[j] * numCenters + k])
				{
					float		dxc = DatumGetFloat8(FunctionCall2Coll(procinfo, collation, vec, PointerGetDatum(VectorArrayGet(centers, k))));

					/* d(x,c) calculated */
					lowerBound[(Size) j * numCenters + k] = dxc;

					if (dxc < dxcx)
					{
						closestCenters[j] = k;

						/* c(x) changed */
						upperBound[j] = dxc;

						changes++;
					}
				}
			}
		}

		/* Step 4: For each center c, let m(c) be mean of all points assigned */
		ComputeNewCenters(samples, agg, newCenters, centerCounts, closestCenters, normprocinfo, collation, typeInfo);

		/* Step 5 */
		for (int j = 0; j < numCenters; j++)
			newcdist[j] = DatumGetFloat8(FunctionCall2Coll(procinfo, collation, PointerGetDatum(VectorArrayGet(centers, j)), PointerGetDatum(VectorArrayGet(newCenters, j))));

		for (int j = 0; j < numSamples; j++)
		{
			for (int k = 0; k < numCenters; k++)
			{
				float		distance = lowerBound[(Size) j * numCenters + k] - newcdist[k];

				if (distance < 0)
					distance = 0;

				lowerBound[(Size) j * numCenters + k] = distance;
			}
		}

		/* Step 6 */
		/* We reset r(x) before Step 3 in the next iteration */
		for (int j = 0; j < numSamples; j++)
			upperBound[j] += newcdist[closestCenters[j]];

		/* Step 7 */
		for (int j = 0; j < numCenters; j++)
			VectorArraySet(centers, j, VectorArrayGet(newCenters, j));

		if (changes == 0 && iteration != 0)
			break;
	}
}
```

## 동작 흐름

```text
 IvfflatKmeans(index, samples, centers, typeInfo, memoryUsed)    L553
   L561  표본 0 개 -> RandomCenters (난수 좌표, 필요하면 정규화)
         아니면 ElkanKmeans
   L566  CheckCenters   중심점 수, NaN/inf, 코사인이면 노름 0 이 없는지

 ElkanKmeans                                          L246
   L266  할당 크기 계산 -> L290 IvfflatCheckMemoryUsage
           lowerBound  numSamples * numCenters 개의 float  가장 크다
           halfcdist   numCenters * numCenters 개
   L321  InitCenters (k-means++)                       L23
           첫 중심 = 무작위 표본 하나
           중심을 하나 고를 때마다 모든 표본과 거리 -> lowerBound 에 기록
           weight[j] = 지금까지 중심 중 가장 가까운 것까지 거리의 제곱
           다음 중심 = weight 비례 확률로 고른 표본
   L324  표본마다 가장 가까운 시작 중심 -> closestCenters, upperBound
   L347  최대 500 회
     Step 1  L356  중심점 쌍마다 halfcdist = 거리 / 2,  s(c) = 가장 가까운 다른 중심까지 반
     Step 2  L396  upperBound[j] <= s[c(j)] 인 표본은 건너뜀    확실히 지금 중심이 가장 가깝다
     Step 3  L401  남은 표본 j, 중심 k 마다
               u <= lowerBound[j][k] 또는 u <= halfcdist[c(j)][k] 면 건너뜀
               3a  필요하면 d(x, c(x)) 를 다시 계산해 u 를 정확히
               3b  여전히 의심스러우면 d(x, k) 계산 -> 더 가까우면 c(x) = k, changes++
     Step 4  L454  ComputeNewCenters: 배정된 표본의 평균 (빈 중심은 난수), 필요하면 정규화
     Step 5  L457  중심이 움직인 거리 newcdist, lowerBound -= newcdist (0 아래로는 0)
     Step 6  L475  upperBound += newcdist[c(j)]
     Step 7  L479  중심점 교체
             L482  changes == 0 이고 첫 바퀴가 아니면 끝
```

```text
 Step 2, 3 이 계산을 건너뛰는 근거 (삼각 부등식)

          c(x)
         /    \
     u  /      \  d(c(x), k)
       /        \
      x -------- k
         d(x,k)

 d(x,k) >= d(c(x),k) - d(x,c(x)) >= d(c(x),k) - u
 u <= d(c(x),k) / 2  이면  d(x,k) >= d(c(x),k) - u >= u >= d(x,c(x))
 -> k 가 c(x) 보다 가까울 수 없다. halfcdist 가 d(c(x),k)/2 를 미리 들고 있다
 그래서 거리 함수가 삼각 부등식을 만족해야 한다 (L2 제곱과 내적은 만족하지 않는다)
```

```text
 메모리 (lists = 100, vector(768), numSamples = 10,000)

 ComputeCenters 까지    표본 30,800,032 + 중심 308,032
 newCenters             308,032
 agg                    100 * 768 * 4 = 307,200
 lowerBound             10,000 * 100 * 4 = 4,000,000
 halfcdist              100 * 100 * 4 = 40,000
 그 밖 (counts, bounds, s, newcdist)    약 81,200
 합계 35,844,496 바이트 (약 34.2MB)  < 64MB 이면 통과
```

## 결과가 쓰이는 곳

```text
 centers (lists 개, 정규화 opclass 면 단위 벡터)
      --> [04] CreateListPages 의 리스트 튜플 center
      --> [05] AddTupleToSort 의 배정 기준 (이때는 FUNCTION 1 거리로 잰다)
```

## 다루지 않는 것

빈 중심점을 난수로 채우는 처리(주석 L224 "TODO Handle empty centers properly"), `float` 합의 오버플로 처리(L215-L216), 병렬 빌드에서 일꾼에게 중심점을 공유 메모리로 넘기는 부분은 다루지 않았다.
