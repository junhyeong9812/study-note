# _PG_init

상위: [확장 로드와 vector 타입](../README.md)

**공유 라이브러리 `vector` 가 백엔드에 올라올 때 한 번 불리는 초기화 함수다.** 네 줄이 전부이고, 앞 둘은 CPU 기능을 보고 `bit` 와 `halfvec` 거리 함수 포인터를 고르며, 뒤 둘은 HNSW 와 IVFFlat 의 인덱스 옵션(reloption)과 설정 변수(GUC)를 등록한다.

## 위치

`src` / `vector.c` L58-L65 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/vector.c#L58-L65))

## 실제 코드

```c
// vector.c L48-L65
#if PG_VERSION_NUM >= 180000
PG_MODULE_MAGIC_EXT(.name = "vector", .version = "0.8.7");
#else
PG_MODULE_MAGIC;
#endif

/*
 * Initialize index options and variables
 */
PGDLLEXPORT void _PG_init(void);
void
_PG_init(void)
{
	BitvecInit();
	HalfvecInit();
	HnswInit();
	IvfflatInit();
}
```

`HalfvecInit` 은 기본 구현을 먼저 꽂아 두고, x86-64 에서 AVX, F16C, FMA 가 모두 있으면 F16C 구현으로 바꾼다.

`src` / `halfutils.c` L278-L300 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/halfutils.c#L278-L300))

```c
// halfutils.c L278-L300
void
HalfvecInit(void)
{
	/*
	 * Could skip pointer when single function, but no difference in
	 * performance
	 */
	HalfvecL2SquaredDistance = HalfvecL2SquaredDistanceDefault;
	HalfvecInnerProduct = HalfvecInnerProductDefault;
	HalfvecCosineSimilarity = HalfvecCosineSimilarityDefault;
	HalfvecL1Distance = HalfvecL1DistanceDefault;

#ifdef HALFVEC_DISPATCH
	if (SupportsCpuFeature(CPU_FEATURE_AVX | CPU_FEATURE_F16C | CPU_FEATURE_FMA))
	{
		HalfvecL2SquaredDistance = HalfvecL2SquaredDistanceF16c;
		HalfvecInnerProduct = HalfvecInnerProductF16c;
		HalfvecCosineSimilarity = HalfvecCosineSimilarityF16c;
		/* Does not require FMA, but keep logic simple */
		HalfvecL1Distance = HalfvecL1DistanceF16c;
	}
#endif
}
```

`BitvecInit` 은 같은 방식으로 AVX-512 POPCNT 가 있으면 해밍·자카드 거리 함수를 바꾼다.

`src` / `bitutils.c` L207-L224 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/bitutils.c#L207-L224))

```c
// bitutils.c L207-L224
void
BitvecInit(void)
{
	/*
	 * Could skip pointer when single function, but no difference in
	 * performance
	 */
	BitHammingDistance = BitHammingDistanceDefault;
	BitJaccardDistance = BitJaccardDistanceDefault;

#ifdef BIT_DISPATCH
	if (SupportsAvx512Popcount())
	{
		BitHammingDistance = BitHammingDistanceAvx512Popcount;
		BitJaccardDistance = BitJaccardDistanceAvx512Popcount;
	}
#endif
}
```

## 동작 흐름

```text
 _PG_init                                          vector.c L58
   L61  BitvecInit
          BitHammingDistance  = ...Default           bitutils.c L214
          BitJaccardDistance  = ...Default           L215
          BIT_DISPATCH 이고 SupportsAvx512Popcount   L218
            -> ...Avx512Popcount 로 교체             L220-L221
   L62  HalfvecInit
          L2, 내적, 코사인, L1 네 포인터 = ...Default   halfutils.c L285-L288
          HALFVEC_DISPATCH 이고 AVX|F16C|FMA          L291
            -> ...F16c 로 교체                        L293-L297
   L63  HnswInit      --> [거리 연산자와 Index AM] 03
          m, ef_construction reloption
          hnsw.ef_search, hnsw.iterative_scan, hnsw.max_scan_tuples,
          hnsw.scan_mem_multiplier GUC
   L64  IvfflatInit
          lists reloption
          ivfflat.probes, ivfflat.iterative_scan, ivfflat.max_probes GUC
```

`vector` 타입의 거리 함수에는 이런 함수 포인터 교체가 없다. 대신 컴파일 시점의 `target_clones` 속성으로 같은 일을 맡긴다.

```text
 SIMD 를 고르는 두 가지 방식

 vector    VECTOR_TARGET_CLONES  vector.c L42-L46
             USE_TARGET_CLONES 이고 __FMA__ 가 아니면
             __attribute__((target_clones("default", "fma")))
             -> 컴파일러가 두 벌을 만들고 로더가 고른다
             VectorL2SquaredDistance 등 static 함수에 붙는다 (L560)

 halfvec   함수 포인터 4개를 _PG_init 에서 채운다
 bit       함수 포인터 2개를 _PG_init 에서 채운다
             (bitutils.h 의 extern 선언, 실행 중 CPUID 로 판단)
```

`PG_MODULE_MAGIC` 은 이 라이브러리가 어느 PostgreSQL 판으로 빌드됐는지를 서버가 확인하는 표지다. 18 이상에서는 이름과 판(`"vector"`, `"0.8.7"`)을 함께 싣는다(L49).

## 결과가 쓰이는 곳

```text
 BitHammingDistance, BitJaccardDistance
      --> hamming_distance, jaccard_distance (bitvec.c L54, L69) -> <~>, <%> 연산자
 HalfvecL2SquaredDistance 등
      --> halfvec 의 <->, <#>, <=>, <+> 연산자 함수
 hnsw_relopt_kind, ivfflat_relopt_kind
      --> hnswoptions / ivfflatoptions 가 WITH (m = ..., lists = ...) 를 파싱할 때
 hnsw_ef_search, ivfflat_probes 등 전역 변수
      --> 검색 흐름이 매 스캔에서 읽는다 ([HNSW 검색], [IVFFlat 빌드와 검색])
```

## 다루지 않는 것

`SupportsCpuFeature` 와 `SupportsAvx512Popcount` 의 CPUID 판별 세부, F16C·AVX-512 구현 본문, 라이브러리를 `shared_preload_libraries` 로 미리 올렸을 때의 차이(`HnswInit` 의 `process_shared_preload_libraries_in_progress` 분기, hnsw.c L84)는 요약만 했다. `HnswInit` 본문은 [거리 연산자와 Index AM 의 HnswInit](../../operators-index-am/03_HnswInit/README.md)에 있다.
