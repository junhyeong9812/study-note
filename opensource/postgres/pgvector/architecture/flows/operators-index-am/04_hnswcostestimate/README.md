# hnswcostestimate

상위: [거리 연산자와 Index AM 연결](../README.md)

**플래너가 HNSW 인덱스 스캔의 비용을 물을 때 답하는 함수다.** `ORDER BY` 가 없는 경로면 비용을 무한대로 돌려 아예 고르지 못하게 한다. 있으면 PostgreSQL 의 `genericcostestimate` 로 전체 비용을 얻은 뒤, "첫 행을 내기까지 인덱스의 몇 분의 일을 읽는가"를 HNSW 식으로 추정해 시작 비용(startup cost)만 그 비율로 줄인다. `LIMIT` 이 붙은 근사 최근접 질의에서 인덱스가 순차 스캔보다 싸 보이게 하는 장치다.

## 위치

`src` / `hnsw.c` L134-L233 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.c#L134-L233))

## 실제 코드

```c
// hnsw.c L131-L233
/*
 * Estimate the cost of an index scan
 */
static void
hnswcostestimate(PlannerInfo *root, IndexPath *path, double loop_count,
				 Cost *indexStartupCost, Cost *indexTotalCost,
				 Selectivity *indexSelectivity, double *indexCorrelation,
				 double *indexPages)
{
	GenericCosts costs;
	int			m;
	double		ratio;
	double		startupPages;
	double		spc_seq_page_cost;
	Relation	index;

	/* Never use index without order */
	if (path->indexorderbys == NIL)
	{
		*indexStartupCost = get_float8_infinity();
		*indexTotalCost = get_float8_infinity();
		*indexSelectivity = 0;
		*indexCorrelation = 0;
		*indexPages = 0;
#if PG_VERSION_NUM >= 180000
		/* See "On disable_cost" thread on pgsql-hackers */
		path->path.disabled_nodes = 2;
#endif
		return;
	}

	MemSet(&costs, 0, sizeof(costs));

	genericcostestimate(root, path, loop_count, &costs);

	index = index_open(path->indexinfo->indexoid, NoLock);
	HnswGetMetaPageInfo(index, &m, NULL, NULL);
	index_close(index, NoLock);

	/*
	 * HNSW cost estimation follows a formula that accounts for the total
	 * number of tuples indexed combined with the parameters that most
	 * influence the duration of the index scan, namely: m - the number of
	 * tuples that are scanned in each step of the HNSW graph traversal
	 * ef_search - which influences the total number of steps taken at layer 0
	 *
	 * The source of the vector data can impact how many steps it takes to
	 * converge on the set of vectors to return to the executor. Currently, we
	 * use a hardcoded scaling factor (HNSWScanScalingFactor) to help
	 * influence that, but this could later become a configurable parameter
	 * based on the cost estimations.
	 *
	 * The tuple estimator formula is below:
	 *
	 * numIndexTuples = entryLevel * m + layer0TuplesMax * layer0Selectivity
	 *
	 * "entryLevel * m" represents the floor of tuples we need to scan to get
	 * to layer 0 (L0).
	 *
	 * "layer0TuplesMax" is the estimated total number of tuples we'd scan at
	 * L0 if we weren't discarding already visited tuples as part of the scan.
	 *
	 * "layer0Selectivity" estimates the percentage of tuples that are scanned
	 * at L0, accounting for previously visited tuples, multiplied by the
	 * "scalingFactor" (currently hardcoded).
	 */
	if (path->indexinfo->tuples > 0)
	{
		double		scalingFactor = 0.55;
		int			entryLevel = (int) (log(path->indexinfo->tuples) * HnswGetMl(m));
		int			layer0TuplesMax = HnswGetLayerM(m, 0) * hnsw_ef_search;
		double		layer0Selectivity = scalingFactor * log(path->indexinfo->tuples) / (log(m) * (1 + log(hnsw_ef_search)));

		ratio = (entryLevel * m + layer0TuplesMax * layer0Selectivity) / path->indexinfo->tuples;

		if (ratio > 1)
			ratio = 1;
	}
	else
		ratio = 1;

	get_tablespace_page_costs(path->indexinfo->reltablespace, NULL, &spc_seq_page_cost);

	/* Startup cost is cost before returning the first row */
	costs.indexStartupCost = costs.indexTotalCost * ratio;

	/* Adjust cost if needed since TOAST not included in seq scan cost */
	startupPages = costs.numIndexPages * ratio;
	if (startupPages > path->indexinfo->rel->pages && ratio < 0.5)
	{
		/* Change all page cost from random to sequential */
		costs.indexStartupCost -= startupPages * (costs.spc_random_page_cost - spc_seq_page_cost);

		/* Remove cost of extra pages */
		costs.indexStartupCost -= (startupPages - path->indexinfo->rel->pages) * spc_seq_page_cost;
	}

	*indexStartupCost = costs.indexStartupCost;
	*indexTotalCost = costs.indexTotalCost;
	*indexSelectivity = costs.indexSelectivity;
	*indexCorrelation = costs.indexCorrelation;
	*indexPages = costs.numIndexPages;
}
```

IVFFlat 쪽은 같은 틀에 비율만 `probes / lists` 다.

`src` / `ivfflat.c` L122-L125 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfflat.c#L122-L125))

```c
// ivfflat.c L122-L125
	/* Get the ratio of lists that we need to visit */
	ratio = ((double) ivfflat_probes) / lists;
	if (ratio > 1.0)
		ratio = 1.0;
```

## 동작 흐름

```text
 hnswcostestimate(root, path, ...)                   L134
   L148  path->indexorderbys == NIL
           startup = total = 무한대, 18 이상은 disabled_nodes = 2   L157
           -> 순서 없는 스캔(WHERE 만 있는 경우)에는 쓰이지 않는다
   L164  genericcostestimate(...)              PostgreSQL 공용 추정
   L167  HnswGetMetaPageInfo -> m             메타 페이지의 m (옵션이 아니다)
   L197  tuples > 0 이면
           entryLevel       = (int)(ln(tuples) * ml)       ml = 1/ln(m)
           layer0TuplesMax  = 2m * ef_search
           layer0Selectivity = 0.55 * ln(tuples) / (ln(m) * (1 + ln(ef_search)))
           ratio = (entryLevel * m + layer0TuplesMax * layer0Selectivity) / tuples
           ratio 는 최대 1
   L215  indexStartupCost = indexTotalCost * ratio
   L218  startupPages 가 힙 페이지보다 많고 ratio < 0.5 면
           랜덤 페이지 비용을 순차 비용으로 바꾸고 넘친 페이지 비용을 뺀다
           (주석 L217: 순차 스캔 비용에는 TOAST 가 들어가지 않으므로)
   L228  다섯 출력값을 채운다
```

식의 항이 무엇을 세는지 소스 주석(L170-L196)을 그림으로 옮기면 다음과 같다.

```text
 entryLevel * m              위층을 내려오며 층마다 이웃 m 개를 본다
                              층 수는 ln(N) / ln(m) 로 어림 (원소 N 개일 때 가장 높은 층의 어림값)
 layer0TuplesMax             0층에서 ef_search 번 확장하고, 확장마다 이웃 2m 개
 layer0Selectivity           그중 이미 본 것을 빼고 실제로 새로 읽는 비율
                              0.55 는 주석이 말하는 하드코딩 배율 (HNSWScanScalingFactor)
```

기본값 `m = 16`, `ef_search = 40` 에서 표 크기마다 계산하면 다음과 같다.

```text
 tuples       entryLevel  layer0Max  selectivity  읽는 튜플   ratio
 10,000       3           1280       0.3897       546.8       0.0547
 1,000,000    4           1280       0.5845       812.1       0.000812
 10,000,000   5           1280       0.6819       952.8       0.0000953

 entryLevel = (int)(ln(tuples) / ln(16)),  layer0Max = 2 * 16 * 40
 읽는 튜플 = entryLevel * 16 + 1280 * selectivity
 시작 비용 = genericcostestimate 의 total * ratio
```

```text
 IVFFlat 은 (ivfflat.c L123)
   ratio = probes / lists      기본 1 / 100 = 0.01, 최대 1
   전체 비용에서 먼저 페이지의 절반(sequentialRatio 0.5)을 순차 읽기로 바꾸고 (L130)
   시작 비용 = total * ratio
```

HNSW 는 총비용은 줄이지 않고 시작 비용만 줄인다(IVFFlat 은 위처럼 총비용도 L130 에서 조금 줄인다). 플래너는 `LIMIT k` 가 있으면 시작 비용과 총비용 사이를 k 의 비율로 보간하므로, 작은 `LIMIT` 일수록 이 비율이 효과를 낸다. 이 보간은 PostgreSQL 쪽 규칙이다.

## 결과가 쓰이는 곳

```text
 indexStartupCost, indexTotalCost, indexSelectivity, indexPages
      --> 플래너가 이 인덱스 경로와 순차 스캔 + 정렬 경로를 비교한다
      --> 고르면 실행기가 [HNSW 검색] 의 hnswbeginscan 부터 부른다
```

## 다루지 않는 것

`genericcostestimate` 와 `get_tablespace_page_costs` 의 내부, 플래너가 `LIMIT` 으로 비용을 보간하는 방식은 PostgreSQL 쪽이라 다루지 않았다. 반복 스캔(`hnsw.iterative_scan`)은 비용 추정에 반영되지 않는다(이 함수가 그 변수를 읽지 않는다).
