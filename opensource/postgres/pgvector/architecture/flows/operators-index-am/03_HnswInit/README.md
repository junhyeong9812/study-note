# HnswInit

상위: [거리 연산자와 Index AM 연결](../README.md)

**HNSW 의 인덱스 옵션 두 개와 설정 변수 네 개를 서버에 등록하는 함수다.** `_PG_init` 이 라이브러리 로드 때 한 번 부른다. 인덱스 옵션(`WITH (m = 16, ef_construction = 64)`)은 인덱스마다 카탈로그에 남고, 설정 변수(`SET hnsw.ef_search = 100`)는 세션마다 바꿀 수 있다. 같은 일을 IVFFlat 은 `IvfflatInit` 에서 한다.

## 위치

`src` / `hnsw.c` L81-L112 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.c#L81-L112))

## 실제 코드

```c
// hnsw.c L28-L40
static const struct config_enum_entry hnsw_iterative_scan_options[] = {
	{"off", HNSW_ITERATIVE_SCAN_OFF, false},
	{"relaxed_order", HNSW_ITERATIVE_SCAN_RELAXED, false},
	{"strict_order", HNSW_ITERATIVE_SCAN_STRICT, false},
	{NULL, 0, false}
};

int			hnsw_ef_search;
int			hnsw_iterative_scan;
int			hnsw_max_scan_tuples;
double		hnsw_scan_mem_multiplier;
int			hnsw_lock_tranche_id;
static relopt_kind hnsw_relopt_kind;
```

```c
// hnsw.c L78-L112
/*
 * Initialize index options and variables
 */
void
HnswInit(void)
{
	if (!process_shared_preload_libraries_in_progress)
		HnswInitLockTranche();

	hnsw_relopt_kind = add_reloption_kind();
	add_int_reloption(hnsw_relopt_kind, "m", "Max number of connections",
					  HNSW_DEFAULT_M, HNSW_MIN_M, HNSW_MAX_M, AccessExclusiveLock);
	add_int_reloption(hnsw_relopt_kind, "ef_construction", "Size of the dynamic candidate list for construction",
					  HNSW_DEFAULT_EF_CONSTRUCTION, HNSW_MIN_EF_CONSTRUCTION, HNSW_MAX_EF_CONSTRUCTION, AccessExclusiveLock);

	DefineCustomIntVariable("hnsw.ef_search", "Sets the size of the dynamic candidate list for search",
							"Valid range is 1..1000.", &hnsw_ef_search,
							HNSW_DEFAULT_EF_SEARCH, HNSW_MIN_EF_SEARCH, HNSW_MAX_EF_SEARCH, PGC_USERSET, 0, NULL, NULL, NULL);

	DefineCustomEnumVariable("hnsw.iterative_scan", "Sets the mode for iterative scans",
							 NULL, &hnsw_iterative_scan,
							 HNSW_ITERATIVE_SCAN_OFF, hnsw_iterative_scan_options, PGC_USERSET, 0, NULL, NULL, NULL);

	/* This is approximate and does not affect the initial scan */
	DefineCustomIntVariable("hnsw.max_scan_tuples", "Sets the max number of tuples to visit for iterative scans",
							NULL, &hnsw_max_scan_tuples,
							20000, 1, INT_MAX, PGC_USERSET, 0, NULL, NULL, NULL);

	/* Same range as hash_mem_multiplier */
	DefineCustomRealVariable("hnsw.scan_mem_multiplier", "Sets the multiple of work_mem to use for iterative scans",
							 NULL, &hnsw_scan_mem_multiplier,
							 1, 1, 1000, PGC_USERSET, 0, NULL, NULL, NULL);

	MarkGUCPrefixReserved("hnsw");
}
```

기본값과 범위는 헤더의 상수다.

`src` / `hnsw.h` L53-L62 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.h#L53-L62))

```c
// hnsw.h L53-L62
/* HNSW parameters */
#define HNSW_DEFAULT_M	16
#define HNSW_MIN_M	2
#define HNSW_MAX_M		100
#define HNSW_DEFAULT_EF_CONSTRUCTION	64
#define HNSW_MIN_EF_CONSTRUCTION	4
#define HNSW_MAX_EF_CONSTRUCTION		1000
#define HNSW_DEFAULT_EF_SEARCH	40
#define HNSW_MIN_EF_SEARCH		1
#define HNSW_MAX_EF_SEARCH		1000
```

`WITH (...)` 를 구조체로 바꾸는 `amoptions` 와, 그 구조체를 읽는 쪽이다.

`src` / `hnsw.c` L238-L250 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.c#L238-L250))

```c
// hnsw.c L238-L250
static bytea *
hnswoptions(Datum reloptions, bool validate)
{
	static const relopt_parse_elt tab[] = {
		{"m", RELOPT_TYPE_INT, offsetof(HnswOptions, m)},
		{"ef_construction", RELOPT_TYPE_INT, offsetof(HnswOptions, efConstruction)},
	};

	return (bytea *) build_reloptions(reloptions, validate,
									  hnsw_relopt_kind,
									  sizeof(HnswOptions),
									  tab, lengthof(tab));
}
```

`src` / `hnswutils.c` L113-L136 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswutils.c#L113-L136))

```c
// hnswutils.c L113-L136
int
HnswGetM(Relation index)
{
	HnswOptions *opts = (HnswOptions *) index->rd_options;

	if (opts)
		return opts->m;

	return HNSW_DEFAULT_M;
}

/*
 * Get the size of the dynamic candidate list in the index
 */
int
HnswGetEfConstruction(Relation index)
{
	HnswOptions *opts = (HnswOptions *) index->rd_options;

	if (opts)
		return opts->efConstruction;

	return HNSW_DEFAULT_EF_CONSTRUCTION;
}
```

IVFFlat 쪽 등록이다.

`src` / `ivfflat.c` L38-L59 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfflat.c#L38-L59))

```c
// ivfflat.c L38-L59
void
IvfflatInit(void)
{
	ivfflat_relopt_kind = add_reloption_kind();
	add_int_reloption(ivfflat_relopt_kind, "lists", "Number of inverted lists",
					  IVFFLAT_DEFAULT_LISTS, IVFFLAT_MIN_LISTS, IVFFLAT_MAX_LISTS, AccessExclusiveLock);

	DefineCustomIntVariable("ivfflat.probes", "Sets the number of probes",
							"Valid range is 1..lists.", &ivfflat_probes,
							IVFFLAT_DEFAULT_PROBES, IVFFLAT_MIN_LISTS, IVFFLAT_MAX_LISTS, PGC_USERSET, 0, NULL, NULL, NULL);

	DefineCustomEnumVariable("ivfflat.iterative_scan", "Sets the mode for iterative scans",
							 NULL, &ivfflat_iterative_scan,
							 IVFFLAT_ITERATIVE_SCAN_OFF, ivfflat_iterative_scan_options, PGC_USERSET, 0, NULL, NULL, NULL);

	/* If this is less than probes, probes is used */
	DefineCustomIntVariable("ivfflat.max_probes", "Sets the max number of probes for iterative scans",
							NULL, &ivfflat_max_probes,
							IVFFLAT_MAX_LISTS, IVFFLAT_MIN_LISTS, IVFFLAT_MAX_LISTS, PGC_USERSET, 0, NULL, NULL, NULL);

	MarkGUCPrefixReserved("ivfflat");
}
```

## 동작 흐름

```text
 HnswInit                                            L81
   L84   shared_preload_libraries 로 올라오는 중이 아니면 HnswInitLockTranche
           병렬 빌드의 LWLock tranche id 를 공유 메모리에 하나 받아 둔다 (L51-L76)
   L87   hnsw_relopt_kind = add_reloption_kind()
   L88   m                 기본 16,  2..100     AccessExclusiveLock
   L90   ef_construction   기본 64,  4..1000
   L93   hnsw.ef_search          기본 40,   1..1000     PGC_USERSET
   L97   hnsw.iterative_scan     기본 off   off | relaxed_order | strict_order
   L102  hnsw.max_scan_tuples    기본 20000, 1..INT_MAX
   L107  hnsw.scan_mem_multiplier 기본 1,  1..1000
   L111  MarkGUCPrefixReserved("hnsw")   hnsw.xxx 오타를 경고
```

```text
 등록한 이름이 읽히는 자리

 이름                       읽는 곳
 m                         HnswGetM (hnswutils.c L113) -> 빌드 InitBuildState, 메타 페이지에 기록
 ef_construction           HnswGetEfConstruction (L127) -> 빌드, 그리고 삽입마다 (hnswinsert.c L701)
 hnsw.ef_search            GetScanItems 의 0층 탐색 폭 (hnswscan.c L60), 비용 추정 (hnsw.c L201)
 hnsw.iterative_scan       hnswgettuple 의 결과 고갈 처리 (hnswscan.c L256)
 hnsw.max_scan_tuples      반복 스캔 중단 조건 (hnswscan.c L264)
 hnsw.scan_mem_multiplier  hnswbeginscan 의 maxMemory = work_mem * 배수 (hnswscan.c L160)
 lists                     IvfflatGetLists (ivfutils.c L58)
 ivfflat.probes            ivfflatbeginscan (ivfscan.c L262), 비용 추정 (ivfflat.c L123)
 ivfflat.iterative_scan    ivfflatbeginscan 의 maxProbes (ivfscan.c L271)
 ivfflat.max_probes        같은 자리 (L272)
```

`m` 은 인덱스를 만든 뒤에는 바꿔도 소용이 없다. 빌드할 때 메타 페이지에 적히고(hnswbuild.c L106), 삽입과 검색은 메타 페이지의 값을 읽는다(`HnswGetMetaPageInfo`). 반면 `ef_construction` 은 메타 페이지에도 적히지만 삽입은 옵션에서 다시 읽는다(hnswinsert.c L701).

## 결과가 쓰이는 곳

```text
 hnsw_relopt_kind       --> hnswoptions 가 build_reloptions 로 HnswOptions 를 만든다
 HnswOptions (rd_options)  --> HnswGetM, HnswGetEfConstruction
 GUC 전역 변수          --> [HNSW 검색] 과 [IVFFlat 빌드와 검색] 이 스캔마다 읽는다
```

## 다루지 않는 것

`HnswInitLockTranche` 의 공유 메모리 처리(PostgreSQL 19 전후 분기), `MarkGUCPrefixReserved` 가 없는 14 이하의 대체(`EmitWarningsOnPlaceholders`, L24-L26)는 요약만 했다.
