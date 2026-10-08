# HnswInitSupport

상위: [거리 연산자와 Index AM 연결](../README.md)

**인덱스의 연산자 클래스에서 거리 함수와 정규화 판정 함수를 꺼내 `HnswSupport` 에 담는 함수다.** 빌드·삽입·스캔이 모두 시작할 때 이것을 부르고, 이후 거리 계산은 전부 `support->procinfo` 를 거친다. 짝으로 쓰이는 `HnswGetTypeInfo` 는 3번 지원 함수로 타입별 정보(차원 상한, 차원 함수, 정규화 함수)를 받는데, `vector` 연산자 클래스에는 3번이 없어서 기본값이 쓰인다.

## 위치

`src` / `hnswutils.c` L153-L159 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L153-L159))

## 실제 코드

```c
// hnswutils.c L138-L159
/*
 * Get proc
 */
FmgrInfo *
HnswOptionalProcInfo(Relation index, uint16 procnum)
{
	if (!OidIsValid(index_getprocid(index, 1, procnum)))
		return NULL;

	return index_getprocinfo(index, 1, procnum);
}

/*
 * Init support functions
 */
void
HnswInitSupport(HnswSupport * support, Relation index)
{
	support->procinfo = index_getprocinfo(index, 1, HNSW_DISTANCE_PROC);
	support->collation = index->rd_indcollation[0];
	support->normprocinfo = HnswOptionalProcInfo(index, HNSW_NORM_PROC);
}
```

결과를 담는 구조체와 타입 정보 구조체다.

`src` / `hnsw.h` L291-L304 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.h#L291-L304))

```c
// hnsw.h L291-L304
typedef struct HnswTypeInfo
{
	int			maxDimensions;
	Datum		(*dimensions) (PG_FUNCTION_ARGS);
	Datum		(*normalize) (PG_FUNCTION_ARGS);
	void		(*checkValue) (Pointer v);
}			HnswTypeInfo;

typedef struct HnswSupport
{
	FmgrInfo   *procinfo;
	FmgrInfo   *normprocinfo;
	Oid			collation;
}			HnswSupport;
```

타입 정보는 3번 지원 함수가 있으면 그것을 부르고, 없으면 `vector` 기본값을 쓴다.

`src` / `hnswutils.c` L1395-L1458 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L1395-L1458))

```c
// hnswutils.c L1384-L1458
static void
SparsevecCheckValue(Pointer v)
{
	SparseVector *vec = (SparseVector *) v;

	if (vec->nnz > HNSW_MAX_NNZ)
		ereport(ERROR,
				(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
				 errmsg("sparsevec cannot have more than %d non-zero elements for hnsw index", HNSW_MAX_NNZ)));
}

/*
 * Get type info
 */
const		HnswTypeInfo *
HnswGetTypeInfo(Relation index)
{
	FmgrInfo   *procinfo = HnswOptionalProcInfo(index, HNSW_TYPE_INFO_PROC);

	if (procinfo == NULL)
	{
		static const HnswTypeInfo typeInfo = {
			.maxDimensions = HNSW_MAX_DIM,
			.dimensions = vector_dims,
			.normalize = l2_normalize,
			.checkValue = NULL
		};

		return (&typeInfo);
	}
	else
		return (const HnswTypeInfo *) DatumGetPointer(FunctionCall0Coll(procinfo, InvalidOid));
}

FUNCTION_PREFIX PG_FUNCTION_INFO_V1(hnsw_halfvec_support);
Datum
hnsw_halfvec_support(PG_FUNCTION_ARGS)
{
	static const HnswTypeInfo typeInfo = {
		.maxDimensions = HNSW_MAX_DIM * 2,
		.dimensions = halfvec_vector_dims,
		.normalize = halfvec_l2_normalize,
		.checkValue = NULL
	};

	PG_RETURN_POINTER(&typeInfo);
}

FUNCTION_PREFIX PG_FUNCTION_INFO_V1(hnsw_bit_support);
Datum
hnsw_bit_support(PG_FUNCTION_ARGS)
{
	static const HnswTypeInfo typeInfo = {
		.maxDimensions = HNSW_MAX_DIM * 32,
		.dimensions = bitlength,
		.normalize = NULL,
		.checkValue = NULL
	};

	PG_RETURN_POINTER(&typeInfo);
}

FUNCTION_PREFIX PG_FUNCTION_INFO_V1(hnsw_sparsevec_support);
Datum
hnsw_sparsevec_support(PG_FUNCTION_ARGS)
{
	static const HnswTypeInfo typeInfo = {
		.maxDimensions = SPARSEVEC_MAX_DIM,
		.dimensions = sparsevec_vector_dims,
		.normalize = sparsevec_l2_normalize,
		.checkValue = SparsevecCheckValue
	};

	PG_RETURN_POINTER(&typeInfo);
}
```

연산자 클래스가 번호를 채우는 모습이다.

`sql` / `vector.sql` L427-L446 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L427-L446))

```sql
-- vector.sql L427-L446
CREATE OPERATOR CLASS vector_l2_ops
	FOR TYPE vector USING hnsw AS
	OPERATOR 1 <-> (vector, vector) FOR ORDER BY float_ops,
	FUNCTION 1 vector_l2_squared_distance(vector, vector);

CREATE OPERATOR CLASS vector_ip_ops
	FOR TYPE vector USING hnsw AS
	OPERATOR 1 <#> (vector, vector) FOR ORDER BY float_ops,
	FUNCTION 1 vector_negative_inner_product(vector, vector);

CREATE OPERATOR CLASS vector_cosine_ops
	FOR TYPE vector USING hnsw AS
	OPERATOR 1 <=> (vector, vector) FOR ORDER BY float_ops,
	FUNCTION 1 vector_negative_inner_product(vector, vector),
	FUNCTION 2 vector_norm(vector);

CREATE OPERATOR CLASS vector_l1_ops
	FOR TYPE vector USING hnsw AS
	OPERATOR 1 <+> (vector, vector) FOR ORDER BY float_ops,
	FUNCTION 1 l1_distance(vector, vector);
```

## 동작 흐름

```text
 HnswInitSupport(support, index)                     L153
   L156  procinfo     = index_getprocinfo(index, 1, 1)    FUNCTION 1, 반드시 있다
   L157  collation    = index->rd_indcollation[0]
   L158  normprocinfo = HnswOptionalProcInfo(index, 2)    FUNCTION 2
           L144  index_getprocid 가 무효면 NULL           없는 칸은 NULL

 HnswGetTypeInfo(index)                              L1398
   L1401 HnswOptionalProcInfo(index, 3)
   L1403 NULL 이면 정적 기본값
           maxDimensions 2000, vector_dims, l2_normalize, checkValue 없음
   L1415 있으면 그 함수를 불러 HnswTypeInfo 포인터를 받는다
```

```text
 연산자 클래스별로 채워지는 값 (HNSW)

 opclass                FUNCTION 1                     FUNCTION 2   타입 정보
 vector_l2_ops          vector_l2_squared_distance     -            기본 (2000)
 vector_ip_ops          vector_negative_inner_product  -            기본 (2000)
 vector_cosine_ops      vector_negative_inner_product  vector_norm  기본 (2000)
 vector_l1_ops          l1_distance                    -            기본 (2000)
 halfvec_l2/ip/l1_ops   halfvec_*_distance             -            hnsw_halfvec_support (4000)
 halfvec_cosine_ops     halfvec_negative_inner_product l2_norm      hnsw_halfvec_support (4000)
 sparsevec_l2/ip/l1_ops sparsevec_*_distance           -            hnsw_sparsevec_support
 sparsevec_cosine_ops   sparsevec_negative_inner_product l2_norm    hnsw_sparsevec_support
 bit_hamming_ops        hamming_distance               -            hnsw_bit_support (64000)
 bit_jaccard_ops        jaccard_distance               -            hnsw_bit_support (64000)

 FUNCTION 2 는 cosine 계열에만 있다 (vector.sql L441, L859, L1205)
 차원 상한: HNSW_MAX_DIM 2000, halfvec * 2, bit * 32, sparsevec 은 SPARSEVEC_MAX_DIM
```

`sparsevec` 만 `checkValue` 가 있다. 차원은 10억까지 받지만 0 이 아닌 원소가 1000 개(`HNSW_MAX_NNZ`)를 넘으면 인덱스에 넣지 않고 오류를 낸다(L1389). nnz 가 1000 이면 값 크기는 `SPARSEVEC_SIZE(1000)` = 16 + 4*1000 + 4*1000 = 8016 바이트이고, 원소 튜플은 MAXALIGN(72 + 8016) = 8088 바이트로 한 페이지에 둘 수 있는 상한 `HNSW_MAX_SIZE` 8156 바이트(hnsw.h L78) 안에 든다.

## 결과가 쓰이는 곳

```text
 HnswSupport
      --> HnswGetDistance 가 FunctionCall2Coll(procinfo, collation, a, b) (L532)
      --> normprocinfo 가 있으면 [06] HnswFormIndexValue 와 검색의 GetScanValue 가 정규화
 HnswTypeInfo
      --> InitBuildState 의 maxDimensions 검사 (hnswbuild.c L711)
      --> HnswCheckDim 이 dimensions 함수로 값의 차원을 잰다 (L1368)
      --> normalize 함수가 [06] 에서 쓰인다
```

## 다루지 않는 것

`index_getprocinfo` 의 캐시(relcache 의 `rd_supportinfo`)는 PostgreSQL 쪽이다. IVFFlat 은 같은 일을 `InitBuildState`(ivfbuild.c L375-L378)와 `ivfflatbeginscan`(ivfscan.c L291-L293)에서 직접 한다.
