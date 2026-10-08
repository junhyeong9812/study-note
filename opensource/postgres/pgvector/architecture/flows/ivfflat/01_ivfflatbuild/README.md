# ivfflatbuild

상위: [IVFFlat 빌드와 검색](../README.md)

**IVFFlat 의 `ambuild` 이다.** `BuildIndex` 가 다섯 단계를 순서대로 부른다. 상태 준비, 중심점 계산, 메타 페이지, 리스트 페이지, 항목 페이지다. HNSW 와 달리 페이지를 만들 때마다 GenericXLog 로 WAL 을 남기므로, 빌드가 끝난 뒤 따로 전체 페이지를 기록하지 않는다(init fork 만 예외).

## 위치

`src` / `ivfbuild.c` L1069-L1086 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L1069-L1086))

## 실제 코드

```c
// ivfbuild.c L1043-L1098
/*
 * Build the index
 */
static void
BuildIndex(Relation heap, Relation index, IndexInfo *indexInfo,
		   IvfflatBuildState * buildstate, ForkNumber forkNum)
{
	InitBuildState(buildstate, heap, index, indexInfo);

	ComputeCenters(buildstate);

	/* Create pages */
	CreateMetaPage(index, buildstate->dimensions, buildstate->lists, forkNum);
	CreateListPages(index, buildstate->centers, buildstate->lists, forkNum, &buildstate->listInfo);
	CreateEntryPages(buildstate, forkNum);

	/* Write WAL for initialization fork since GenericXLog functions do not */
	if (forkNum == INIT_FORKNUM)
		log_newpage_range(index, forkNum, 0, RelationGetNumberOfBlocksInFork(index, forkNum), true);

	FreeBuildState(buildstate);
}

/*
 * Build the index for a logged table
 */
IndexBuildResult *
ivfflatbuild(Relation heap, Relation index, IndexInfo *indexInfo)
{
	IndexBuildResult *result;
	IvfflatBuildState buildstate;

#ifdef IVFFLAT_BENCH
	SeedRandom(42);
#endif

	BuildIndex(heap, index, indexInfo, &buildstate, MAIN_FORKNUM);

	result = palloc_object(IndexBuildResult);
	result->heap_tuples = buildstate.reltuples;
	result->index_tuples = buildstate.indtuples;

	return result;
}

/*
 * Build the index for an unlogged table
 */
void
ivfflatbuildempty(Relation index)
{
	IndexInfo  *indexInfo = BuildIndexInfo(index);
	IvfflatBuildState buildstate;

	BuildIndex(NULL, index, indexInfo, &buildstate, INIT_FORKNUM);
}
```

상태 준비에서 리스트 수, 차원, 지원 함수, 정렬에 쓸 3열짜리 튜플 모양을 정한다.

`src` / `ivfbuild.c` L342-L418 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L342-L418))

```c
// ivfbuild.c L339-L418
/*
 * Initialize the build state
 */
static void
InitBuildState(IvfflatBuildState * buildstate, Relation heap, Relation index, IndexInfo *indexInfo)
{
	buildstate->heap = heap;
	buildstate->index = index;
	buildstate->indexInfo = indexInfo;
	buildstate->typeInfo = IvfflatGetTypeInfo(index);
	buildstate->tupdesc = RelationGetDescr(index);

	buildstate->lists = IvfflatGetLists(index);
	buildstate->dimensions = TupleDescAttr(index->rd_att, 0)->atttypmod;

	/* Disallow varbit since require fixed dimensions */
	if (TupleDescAttr(index->rd_att, 0)->atttypid == VARBITOID)
		ereport(ERROR,
				(errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
				 errmsg("type not supported for ivfflat index")));

	/* Require column to have dimensions to be indexed */
	if (buildstate->dimensions < 0)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("column does not have dimensions")));

	if (buildstate->dimensions > buildstate->typeInfo->maxDimensions)
		ereport(ERROR,
				(errcode(ERRCODE_PROGRAM_LIMIT_EXCEEDED),
				 errmsg("column cannot have more than %d dimensions for ivfflat index", buildstate->typeInfo->maxDimensions)));

	buildstate->reltuples = 0;
	buildstate->indtuples = 0;

	/* Get support functions */
	buildstate->procinfo = index_getprocinfo(index, 1, IVFFLAT_DISTANCE_PROC);
	buildstate->normprocinfo = IvfflatOptionalProcInfo(index, IVFFLAT_NORM_PROC);
	buildstate->kmeansnormprocinfo = IvfflatOptionalProcInfo(index, IVFFLAT_KMEANS_NORM_PROC);
	buildstate->collation = index->rd_indcollation[0];

	/* Require more than one dimension for spherical k-means */
	if (buildstate->kmeansnormprocinfo != NULL && buildstate->dimensions == 1)
		ereport(ERROR,
				(errcode(ERRCODE_INVALID_PARAMETER_VALUE),
				 errmsg("dimensions must be greater than one for this opclass")));

	/* Create tuple description for sorting */
	buildstate->sortdesc = CreateTemplateTupleDesc(3);
	TupleDescInitEntry(buildstate->sortdesc, (AttrNumber) 1, "list", INT4OID, -1, 0);
	TupleDescInitEntry(buildstate->sortdesc, (AttrNumber) 2, "tid", TIDOID, -1, 0);
	TupleDescInitEntry(buildstate->sortdesc, (AttrNumber) 3, "vector", TupleDescAttr(buildstate->tupdesc, 0)->atttypid, -1, 0);
#if PG_VERSION_NUM >= 190000
	TupleDescFinalize(buildstate->sortdesc);
#endif

	buildstate->slot = MakeSingleTupleTableSlot(buildstate->sortdesc, &TTSOpsVirtual);

	buildstate->memoryUsed = 0;
	buildstate->itemsize = buildstate->typeInfo->itemSize(buildstate->dimensions);

	buildstate->memoryUsed = add_size(buildstate->memoryUsed, VECTOR_ARRAY_SIZE(buildstate->lists, buildstate->itemsize));
	IvfflatCheckMemoryUsage(buildstate->memoryUsed);
	buildstate->centers = VectorArrayInit(buildstate->lists, buildstate->dimensions, buildstate->itemsize);

	/* TODO Move allocation to page creation */
	buildstate->listInfo = palloc_array_checked(ListInfo, buildstate->lists);

	buildstate->tmpCtx = AllocSetContextCreate(CurrentMemoryContext,
											   "Ivfflat build temporary context",
											   ALLOCSET_DEFAULT_SIZES);

#ifdef IVFFLAT_KMEANS_DEBUG
	buildstate->inertia = 0;
	buildstate->listSums = palloc0_array_checked(double, buildstate->lists);
	buildstate->listCounts = palloc0_array_checked(int, buildstate->lists);
#endif

	buildstate->ivfleader = NULL;
}
```

메타 페이지와, 모든 빌드 페이지 쓰기에 쓰는 GenericXLog 도우미다.

`src` / `ivfbuild.c` L491-L512 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfbuild.c#L491-L512))

```c
// ivfbuild.c L488-L512
/*
 * Create the metapage
 */
static void
CreateMetaPage(Relation index, int dimensions, int lists, ForkNumber forkNum)
{
	Buffer		buf;
	Page		page;
	GenericXLogState *state;
	IvfflatMetaPage metap;

	buf = IvfflatNewBuffer(index, forkNum);
	IvfflatInitRegisterPage(index, &buf, &page, &state);

	/* Set metapage data */
	metap = IvfflatPageGetMeta(page);
	metap->magicNumber = IVFFLAT_MAGIC_NUMBER;
	metap->version = IVFFLAT_VERSION;
	metap->dimensions = dimensions;
	metap->lists = lists;
	((PageHeader) page)->pd_lower =
		((char *) metap + sizeof(IvfflatMetaPageData)) - (char *) page;

	IvfflatCommitBuffer(buf, state);
}
```

`src` / `ivfutils.c` L162-L178 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfutils.c#L162-L178))

```c
// ivfutils.c L159-L178
/*
 * Init and register page
 */
void
IvfflatInitRegisterPage(Relation index, Buffer *buf, Page *page, GenericXLogState **state)
{
	*state = GenericXLogStart(index);
	*page = GenericXLogRegisterBuffer(*state, *buf, GENERIC_XLOG_FULL_IMAGE);
	IvfflatInitPage(*buf, *page);
}

/*
 * Commit buffer
 */
void
IvfflatCommitBuffer(Buffer buf, GenericXLogState *state)
{
	GenericXLogFinish(state);
	UnlockReleaseBuffer(buf);
}
```

## 동작 흐름

```text
 ivfflatbuild(heap, index, indexInfo)                L1069
   L1079 BuildIndex(heap, index, indexInfo, &buildstate, MAIN_FORKNUM)
           L1050 InitBuildState                       L342
                   lists = IvfflatGetLists          옵션 없으면 100
                   dimensions = atttypmod           -1 이면 "column does not have dimensions"
                   maxDimensions 넘으면 오류        vector 2000
                   procinfo (FUNCTION 1), normprocinfo (2), kmeansnormprocinfo (4)
                   kmeans 정규화가 있는데 차원이 1 이면 오류   L381
                   sortdesc = (list int4, tid, vector)          L387-L390
                   centers = VectorArray(lists 칸), 메모리 검사 L400-L402
           L1052 [02] ComputeCenters
           L1055 CreateMetaPage                     블록 0
           L1056 [04] CreateListPages               블록 1 ..
           L1057 CreateEntryPages                   [05] -> 정렬 -> [06]
           L1060 INIT_FORKNUM 이면 log_newpage_range   (주석 L1059)
           L1063 FreeBuildState
   L1082 heap_tuples = reltuples, index_tuples = indtuples
```

```text
 페이지 하나를 쓰는 GenericXLog 순서 (ivfutils.c)

 IvfflatNewBuffer             ReadBufferExtended(P_NEW) + LockBuffer(EXCLUSIVE)   L139
 IvfflatInitRegisterPage      state = GenericXLogStart(index)                     L165
                              page  = GenericXLogRegisterBuffer(.., FULL_IMAGE)   L166
                              IvfflatInitPage(page)                               L167
   ... PageAddItem 들 (page 는 GenericXLog 가 준 사본) ...
 IvfflatCommitBuffer          GenericXLogFinish(state)   사본을 버퍼에 반영 + WAL  L176
                              UnlockReleaseBuffer                                 L177
```

`GENERIC_XLOG_FULL_IMAGE` 는 차분이 아니라 페이지 전체를 WAL 에 싣는 등록 방식이다(PostgreSQL `generic_xlog` 쪽 규칙). 빌드가 새로 만드는 페이지는 모두 이 방식으로 등록되고, 이미 있는 리스트 튜플을 고치는 `IvfflatUpdateList` 는 플래그 0(차분)으로 등록한다(ivfutils.c L253). HNSW 빌드가 `building = true` 로 WAL 을 미뤘다가 `log_newpage_range` 로 한꺼번에 쓰는 것과 대조된다.

## 결과가 쓰이는 곳

```text
 블록 0 메타 (magic, version, dimensions, lists)
      --> IvfflatGetMetaPageInfo: 비용 추정, beginscan, insert
 IndexBuildResult
      --> index_build 의 통계 갱신
```

## 다루지 않는 것

`IVFFLAT_BENCH` 빌드의 `SeedRandom(42)`, `IVFFLAT_KMEANS_DEBUG` 의 지표 계산은 다루지 않았다. GenericXLog 자체(PostgreSQL `access/transam/generic_xlog.c`)의 차분 계산은 범위 밖이다.
