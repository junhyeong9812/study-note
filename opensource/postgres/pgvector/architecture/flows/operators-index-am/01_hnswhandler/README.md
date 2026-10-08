# hnswhandler

상위: [거리 연산자와 Index AM 연결](../README.md)

**`hnsw` 접근 메서드의 핸들러다.** PostgreSQL 이 이 AM 을 쓰는 인덱스를 열 때마다 불러서 `IndexAmRoutine` 하나를 받는다. 그 안의 불리언 칸은 "이 AM 이 무엇을 할 수 있는가"를, 함수 포인터 칸은 "그 일을 어느 함수가 하는가"를 적는다. HNSW 는 정렬 연산자로 순서 있는 결과를 내는 것(`amcanorderbyop`)만 할 수 있고, 유일 인덱스·다중 열·역방향 스캔·비트맵 스캔은 하지 않는다.

## 위치

`src` / `hnsw.c` L267-L402 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnsw.c#L267-L402))

## 실제 코드

SQL 쪽에서 핸들러 함수를 만들고 접근 메서드에 묶는다.

`sql` / `vector.sql` L359-L366 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/sql/vector.sql#L359-L366))

```sql
-- vector.sql L359-L366
CREATE FUNCTION hnswhandler(internal) RETURNS index_am_handler
	AS 'MODULE_PATHNAME' LANGUAGE C;

COMMENT ON FUNCTION hnswhandler(internal) IS 'hnsw index access method handler';

CREATE ACCESS METHOD hnsw TYPE INDEX HANDLER hnswhandler;

COMMENT ON ACCESS METHOD hnsw IS 'hnsw index access method';
```

PostgreSQL 19 이상은 같은 값을 정적 구조체 초기화로 적고(L270-L326), 그 아래 판은 `makeNode` 로 만든 구조체에 하나씩 대입한다. 두 분기의 값은 같으므로 아래 분기를 본다.

```c
// hnsw.c L261-L402
/*
 * Define index handler
 *
 * See https://www.postgresql.org/docs/current/index-api.html
 */
FUNCTION_PREFIX PG_FUNCTION_INFO_V1(hnswhandler);
Datum
hnswhandler(PG_FUNCTION_ARGS)
{
// ... (L270-L326 생략: PostgreSQL 19 이상 분기, 같은 값을 정적 구조체로 적는다)
#else
	IndexAmRoutine *amroutine = makeNode(IndexAmRoutine);

	amroutine->amstrategies = 0;
	amroutine->amsupport = 3;
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
	amroutine->ambuild = hnswbuild;
	amroutine->ambuildempty = hnswbuildempty;
	amroutine->aminsert = hnswinsert;
#if PG_VERSION_NUM >= 170000
	amroutine->aminsertcleanup = NULL;
#endif
	amroutine->ambulkdelete = hnswbulkdelete;
	amroutine->amvacuumcleanup = hnswvacuumcleanup;
	amroutine->amcanreturn = NULL;
	amroutine->amcostestimate = hnswcostestimate;
#if PG_VERSION_NUM >= 180000
	amroutine->amgettreeheight = NULL;
#endif
	amroutine->amoptions = hnswoptions;
	amroutine->amproperty = NULL;	/* TODO AMPROP_DISTANCE_ORDERABLE */
	amroutine->ambuildphasename = hnswbuildphasename;
	amroutine->amvalidate = hnswvalidate;
#if PG_VERSION_NUM >= 140000
	amroutine->amadjustmembers = NULL;
#endif
	amroutine->ambeginscan = hnswbeginscan;
	amroutine->amrescan = hnswrescan;
	amroutine->amgettuple = hnswgettuple;
	amroutine->amgetbitmap = NULL;
	amroutine->amendscan = hnswendscan;
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

## 동작 흐름

```text
 hnswhandler                                         L267
   L328  amroutine = makeNode(IndexAmRoutine)        부를 때마다 새로 만든다 (19 미만)
   능력 칸
     L330  amstrategies   = 0      검색 전략 번호를 쓰지 않는다 (WHERE 조건 없음)
     L331  amsupport      = 3      지원 함수 1 거리, 2 정규화, 3 타입 정보 (hnsw.h L37-L39)
     L333  amcanorder     = false  값 자체의 순서는 없다
     L334  amcanorderbyop = true   ORDER BY col <op> const 를 인덱스로 처리
     L340  amcanbackward  = false
     L341  amcanunique    = false
     L342  amcanmulticol  = false  열 하나만
     L343  amoptionalkey  = true   첫 열에 조건이 없어도 스캔 가능
     L345  amsearchnulls  = false  IS NULL 검색 없음 (NULL 은 넣지도 않는다, hnswinsert.c L784)
     L349  amcanparallel  = false  병렬 스캔 없음
     L351  amcanbuildparallel = true  (17 이상) 병렬 빌드는 한다
     L358  amparallelvacuumoptions = VACUUM_OPTION_PARALLEL_BULKDEL
   함수 칸
     L362  ambuild          = hnswbuild           --> [HNSW 빌드]
     L363  ambuildempty     = hnswbuildempty      UNLOGGED 테이블의 init fork
     L364  aminsert         = hnswinsert
     L368  ambulkdelete     = hnswbulkdelete
     L369  amvacuumcleanup  = hnswvacuumcleanup
     L371  amcostestimate   = hnswcostestimate    --> [04]
     L375  amoptions        = hnswoptions         --> [03]
     L382  ambeginscan      = hnswbeginscan       --> [HNSW 검색]
     L383  amrescan         = hnswrescan
     L384  amgettuple       = hnswgettuple
     L385  amgetbitmap      = NULL                비트맵 스캔 없음
     L386  amendscan        = hnswendscan
   L400  return amroutine
```

PostgreSQL 이 이 표를 어떻게 쓰는지는 서버 쪽 일이지만, 어느 칸이 어느 단계에서 읽히는지는 이렇게 이어진다.

```text
 CREATE INDEX ... USING hnsw (embedding vector_cosine_ops)
   index_build -> amroutine->ambuild = hnswbuild

 INSERT INTO items ...
   ExecInsertIndexTuples -> index_insert -> rd_indam->aminsert = hnswinsert
   (상위 지도 nbtree 삽입과 분할 [02] index_insert 와 같은 자리)

 SELECT ... ORDER BY embedding <=> $1 LIMIT 5
   플래너   amcanorderbyop 를 보고 인덱스 경로 후보로 올린다
            amcostestimate = hnswcostestimate 로 비용을 받는다
   실행기   ambeginscan -> amrescan -> amgettuple (LIMIT 까지 반복) -> amendscan

 VACUUM
   ambulkdelete = hnswbulkdelete -> amvacuumcleanup = hnswvacuumcleanup
```

`amgettuple` 이 돌려주는 힙 TID 마다 `xs_recheck = false`, `xs_recheckorderby = false` 를 둔다(hnswscan.c L329-L330). 실행기가 거리를 다시 계산해 정렬을 고치지 않는다는 뜻이고, 그래서 인덱스가 돌려준 순서가 그대로 결과 순서가 된다. `hnsw.iterative_scan = relaxed_order` 에서는 이어 붙인 배치 사이에 순서가 조금 어긋날 수 있고, `strict_order` 는 앞보다 가까운 것을 버려서(hnswscan.c L318-L324) 순서를 지킨다.

## 결과가 쓰이는 곳

```text
 IndexAmRoutine *
      --> relcache 가 인덱스 relation 의 rd_indam 으로 붙들고 있는다
      --> 이후 모든 AM 호출은 rd_indam->... 함수 포인터를 거친다
```

## 다루지 않는 것

`amproperty = NULL`(주석 L376: `AMPROP_DISTANCE_ORDERABLE` 미구현), `amcanreturn = NULL`(인덱스 전용 스캔 없음), 17·18 에서 추가된 칸(`aminsertcleanup`, `amgettreeheight`, `amtranslatestrategy` 등)의 의미는 다루지 않았다. `hnswbulkdelete` 와 `hnswvacuumcleanup` 의 본문(hnswvacuum.c)도 범위 밖이다.
