# ivfflathandler

상위: [거리 연산자와 Index AM 연결](../README.md)

**`ivfflat` 접근 메서드의 핸들러다.** 능력 칸은 [hnswhandler](../01_hnswhandler/README.md)와 한 글자도 다르지 않고, 다른 것은 지원 함수 수(`amsupport = 5`)와 함수 포인터의 이름뿐이다. IVFFlat 은 빌드 때 k-means 를 돌리므로 "k-means 에 쓸 거리"와 "k-means 에 쓸 정규화"를 따로 받는 지원 함수 두 칸이 더 있다.

## 위치

`src` / `ivfflat.c` L184-L319 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfflat.c#L184-L319))

## 실제 코드

`sql` / `vector.sql` L350-L357 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L350-L357))

```sql
-- vector.sql L350-L357
CREATE FUNCTION ivfflathandler(internal) RETURNS index_am_handler
	AS 'MODULE_PATHNAME' LANGUAGE C;

COMMENT ON FUNCTION ivfflathandler(internal) IS 'ivfflat index access method handler';

CREATE ACCESS METHOD ivfflat TYPE INDEX HANDLER ivfflathandler;

COMMENT ON ACCESS METHOD ivfflat IS 'ivfflat index access method';
```

```c
// ivfflat.c L178-L319
/*
 * Define index handler
 *
 * See https://www.postgresql.org/docs/current/index-api.html
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(ivfflathandler);
Datum
ivfflathandler(PG_FUNCTION_ARGS)
{
// ... (L187-L243 생략: PostgreSQL 19 이상 분기, 같은 값을 정적 구조체로 적는다)
#else
	IndexAmRoutine *amroutine = makeNode(IndexAmRoutine);

	amroutine->amstrategies = 0;
	amroutine->amsupport = 5;
	amroutine->amoptsprocnum = 0;
	amroutine->amcanorder = false;
	amroutine->amcanorderbyop = true;
#if PG_VERSION_NUM >= 180000
	amroutine->amcanhash = false;
	amroutine->amconsistentequality = false;
	amroutine->amconsistentordering = false;
#endif
	amroutine->amcanbackward = false;	/* can change direction mid-scan */
	amroutine->amcanunique = false;
	amroutine->amcanmulticol = false;
	amroutine->amoptionalkey = true;
	amroutine->amsearcharray = false;
	amroutine->amsearchnulls = false;
	amroutine->amstorage = false;
	amroutine->amclusterable = false;
	amroutine->ampredlocks = false;
	amroutine->amcanparallel = false;
#if PG_VERSION_NUM >= 170000
	amroutine->amcanbuildparallel = true;
#endif
	amroutine->amcaninclude = false;
	amroutine->amusemaintenanceworkmem = false; /* not used during VACUUM */
#if PG_VERSION_NUM >= 160000
	amroutine->amsummarizing = false;
#endif
	amroutine->amparallelvacuumoptions = VACUUM_OPTION_PARALLEL_BULKDEL;
	amroutine->amkeytype = InvalidOid;

	/* Interface functions */
	amroutine->ambuild = ivfflatbuild;
	amroutine->ambuildempty = ivfflatbuildempty;
	amroutine->aminsert = ivfflatinsert;
#if PG_VERSION_NUM >= 170000
	amroutine->aminsertcleanup = NULL;
#endif
	amroutine->ambulkdelete = ivfflatbulkdelete;
	amroutine->amvacuumcleanup = ivfflatvacuumcleanup;
	amroutine->amcanreturn = NULL;	/* tuple not included in heapsort */
	amroutine->amcostestimate = ivfflatcostestimate;
#if PG_VERSION_NUM >= 180000
	amroutine->amgettreeheight = NULL;
#endif
	amroutine->amoptions = ivfflatoptions;
	amroutine->amproperty = NULL;	/* TODO AMPROP_DISTANCE_ORDERABLE */
	amroutine->ambuildphasename = ivfflatbuildphasename;
	amroutine->amvalidate = ivfflatvalidate;
#if PG_VERSION_NUM >= 140000
	amroutine->amadjustmembers = NULL;
#endif
	amroutine->ambeginscan = ivfflatbeginscan;
	amroutine->amrescan = ivfflatrescan;
	amroutine->amgettuple = ivfflatgettuple;
	amroutine->amgetbitmap = NULL;
	amroutine->amendscan = ivfflatendscan;
	amroutine->ammarkpos = NULL;
	amroutine->amrestrpos = NULL;

	/* Interface functions to support parallel index scans */
	amroutine->amestimateparallelscan = NULL;
	amroutine->aminitparallelscan = NULL;
	amroutine->amparallelrescan = NULL;

#if PG_VERSION_NUM >= 180000
	amroutine->amtranslatestrategy = NULL;
	amroutine->amtranslatecmptype = NULL;
#endif

	PG_RETURN_POINTER(amroutine);
#endif
}
```

지원 함수 번호는 헤더에 있다.

`src` / `ivfflat.h` L39-L44 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/ivfflat.h#L39-L44))

```c
// ivfflat.h L39-L44
/* Support functions */
#define IVFFLAT_DISTANCE_PROC 1
#define IVFFLAT_NORM_PROC 2
#define IVFFLAT_KMEANS_DISTANCE_PROC 3
#define IVFFLAT_KMEANS_NORM_PROC 4
#define IVFFLAT_TYPE_INFO_PROC 5
```

## 동작 흐름

```text
 ivfflathandler                                      L184
   능력 칸        hnswhandler 와 같다 (L247-L276)
                  amcanorderbyop = true, amcanorder = false, amcanmulticol = false ...
   L248  amsupport = 5
   함수 칸
     L279  ambuild      = ivfflatbuild       --> [IVFFlat 빌드와 검색]
     L281  aminsert     = ivfflatinsert
     L285  ambulkdelete = ivfflatbulkdelete
     L288  amcostestimate = ivfflatcostestimate
     L292  amoptions    = ivfflatoptions     lists 하나 (L156-L167)
     L299  ambeginscan  = ivfflatbeginscan
     L301  amgettuple   = ivfflatgettuple
```

연산자 클래스가 다섯 칸을 어떻게 채우는지 보면 두 AM 의 차이가 드러난다.

```text
 지원 함수 번호   HNSW (hnsw.h L37-L39)       IVFFlat (ivfflat.h L40-L44)
 1               DISTANCE_PROC              DISTANCE_PROC
 2               NORM_PROC                  NORM_PROC
 3               TYPE_INFO_PROC             KMEANS_DISTANCE_PROC
 4               -                          KMEANS_NORM_PROC
 5               -                          TYPE_INFO_PROC

 vector_cosine_ops USING ivfflat (vector.sql L419-L425)
   1 vector_negative_inner_product   목록과 항목의 거리
   2 vector_norm                     넣는 값과 찾는 값을 정규화할지
   3 vector_spherical_distance       k-means 거리 (삼각 부등식을 만족해야 한다)
   4 vector_norm                     k-means 표본을 정규화할지
 vector_l2_ops USING ivfflat (L406-L410)
   1 vector_l2_squared_distance
   3 l2_distance                     k-means 는 제곱 아닌 L2 를 쓴다
```

k-means 쪽 거리가 따로 있는 이유는 소스 주석에 있다. Elkan k-means 는 삼각 부등식으로 거리 계산을 건너뛰는데, 제곱 L2 와 음의 내적은 그 부등식을 만족하지 않는다(ivfkmeans.c L238-L242, vector.c L699-L701).

## 결과가 쓰이는 곳

```text
 IndexAmRoutine *
      --> ivfflat 인덱스의 rd_indam
      --> FUNCTION 3, 4 는 IvfflatKmeans 와 표본 정규화(AddSample)에서만 읽힌다
      --> FUNCTION 5 가 없으면 vector 용 기본 타입 정보 (ivfutils.c L413-L424)
```

## 다루지 않는 것

`ivfflatcostestimate`(L85)는 `probes / lists` 비율로 시작 비용을 나누는 간단한 식이라 [hnswcostestimate](../04_hnswcostestimate/README.md)에서 함께 짚는다. VACUUM 함수(ivfvacuum.c)는 범위 밖이다.
