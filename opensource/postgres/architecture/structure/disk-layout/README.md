# 디스크 배치

상위: [PostgreSQL 아키텍처 지도](../../README.md)

PostgreSQL 클러스터 하나는 **데이터 디렉터리(PGDATA) 하나**에 통째로 들어 있다. 테이블과 인덱스는 `base/<DB oid>/<relfilenode>` 파일이고, 모든 DB 가 함께 쓰는 공유 카탈로그는 `global/`, WAL 은 `pg_wal/`, 트랜잭션의 커밋 여부는 `pg_xact/` 에 있다. 릴레이션 하나는 fork 마다 파일이 따로 있다. 본체(main)는 접미사가 없고, 빈 공간 지도는 `_fsm`, 가시성 지도는 `_vm`, unlogged 릴레이션의 초기 이미지는 `_init` 이 붙는다. fork 하나가 1GB(`RELSEG_SIZE` 131072 블록)를 넘으면 `.1`, `.2` 로 이어지는 세그먼트 파일로 갈린다. 그래서 "릴레이션의 블록 N" 은 나눗셈 두 번으로 파일과 오프셋이 정해진다. 클러스터 전체의 상태(마지막 체크포인트 위치, 정상 종료 여부, 빌드 상수)는 `global/pg_control` 파일 하나가 들고 있다. 파일 안 8KB 페이지의 내부는 [페이지와 튜플 레이아웃](../page-tuple-layout/README.md)이, 이 파일을 읽고 쓰는 길은 [버퍼 관리](../../flows/buffer-manager/README.md)가, `pg_control` 을 갱신하는 길은 [체크포인트](../../flows/checkpoint/README.md)가 다룬다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이다. 이 편은 `src/common`, `src/bin` 아래 파일도 인용하므로 경로를 `src/` 부터 적고, `src/backend/` 아래 파일만 그 뒤부터 적는다.

## 전체 그림

`initdb` 는 PGDATA 를 만들 때 하위 디렉터리 목록을 배열 하나로 들고 차례로 만든다. 아래 나무는 그 목록에 파일 이름 규칙을 겹친 것이다.

```text
 $PGDATA/                         initdb 가 만드는 하위 디렉터리 (initdb.c L231-L255)
 |
 +-- PG_VERSION                   "18"  (PG_MAJORVERSION)
 +-- global/                      공유 카탈로그. spcOid = GLOBALTABLESPACE_OID 1664, dbOid = 0
 |     +-- pg_control             ControlFileData. 파일은 8192바이트, 앞 296바이트만 쓴다
 |     +-- pg_filenode.map        매핑된 공유 카탈로그의 oid -> relfilenode
 |     +-- <relfilenode>[_fork][.seg]
 +-- base/                        기본 테이블스페이스 pg_default. spcOid = DEFAULTTABLESPACE_OID 1663
 |     +-- 1/                     template1 (oid 1, initdb.c L246 "base/1")
 |     +-- 4/  5/                 template0, postgres (Template0DbOid 4, PostgresDbOid 5)
 |     +-- <dbOid>/
 |           +-- PG_VERSION
 |           +-- pg_filenode.map  이 DB 의 매핑된 카탈로그
 |           +-- 16385            main fork, 세그먼트 0
 |           +-- 16385.1          main fork, 세그먼트 1   (블록 131072 부터)
 |           +-- 16385_fsm        free space map fork
 |           +-- 16385_vm         visibility map fork
 |           +-- 16385_init       init fork (unlogged 릴레이션만)
 |           +-- t3_16390         임시 릴레이션. t<procNumber>_<relfilenode>
 +-- pg_tblspc/
 |     +-- <spcOid>  --> 심볼릭 링크. 그 아래 PG_18_202506291/<dbOid>/<relfilenode>
 +-- pg_wal/                      WAL 세그먼트 000000010000000000000001 ...  (WAL 레코드 형식 편)
 |     +-- archive_status/  summaries/
 +-- pg_xact/                     트랜잭션마다 커밋 상태 2비트. SLRU 파일 0000, 0001 ...
 +-- pg_multixact/offsets/  pg_multixact/members/
 +-- pg_subtrans/  pg_commit_ts/  pg_serial/  pg_twophase/  pg_snapshots/  pg_notify/
 +-- pg_replslot/  pg_logical/{snapshots,mappings}/  pg_stat/  pg_stat_tmp/  pg_dynshmem/
```

릴레이션 하나가 파일로 펼쳐지는 모양은 다음과 같다. fork 는 독립된 파일 묶음이고, 세그먼트 번호는 fork 안에서 0 부터 센다.

```text
 RelFileLocator {spcOid 1663, dbOid 5, relNumber 16385}  +  ForkNumber  +  BlockNumber

 MAIN_FORKNUM 0         base/5/16385        base/5/16385.1      base/5/16385.2 ...
                        blk 0..131071       131072..262143      262144..
 FSM_FORKNUM 1          base/5/16385_fsm    (_fsm.1 ...)
 VISIBILITYMAP_FORKNUM 2  base/5/16385_vm
 INIT_FORKNUM 3         base/5/16385_init

 세그먼트 하나 = RELSEG_SIZE 블록 x BLCKSZ = 131072 x 8192 = 1073741824 바이트 (1GB)
```

## relfilenode 와 RelFileLocator

파일 이름의 숫자는 테이블의 oid 가 아니라 `pg_class.relfilenode` 다. 릴레이션에 새 물리 파일을 붙여야 하는 경우가 있어서 둘을 나눠 두었다(relfilelocator.h 주석 L35-L37 "because we need to be able to assign new physical files to relations"). 물리 파일을 찾는 데 필요한 값은 셋뿐이다. 테이블스페이스, 데이터베이스, relfilenode 다.

`src` / `include` / `storage` / `relfilelocator.h` L20-L77 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/relfilelocator.h#L20-L77))

```c
// src/include/storage/relfilelocator.h L20-L77
/*
 * RelFileLocator must provide all that we need to know to physically access
 * a relation, with the exception of the backend's proc number, which can be
 * provided separately.  Note, however, that a "physical" relation is
 * comprised of multiple files on the filesystem, as each fork is stored as
 * a separate file, and each fork can be divided into multiple segments. See
 * md.c.
 *
 * spcOid identifies the tablespace of the relation.  It corresponds to
 * pg_tablespace.oid.
 *
 * dbOid identifies the database of the relation.  It is zero for
 * "shared" relations (those common to all databases of a cluster).
 * Nonzero dbOid values correspond to pg_database.oid.
 *
 * relNumber identifies the specific relation.  relNumber corresponds to
 * pg_class.relfilenode (NOT pg_class.oid, because we need to be able
 * to assign new physical files to relations in some situations).
 * Notice that relNumber is only unique within a database in a particular
 * tablespace.
 *
 * Note: spcOid must be GLOBALTABLESPACE_OID if and only if dbOid is
 * zero.  We support shared relations only in the "global" tablespace.
 *
 // ... (L44-L56 생략: pg_class 의 reltablespace 0 과 relfilenode 0(매핑된 카탈로그)은 여기서 허용하지 않는다는 주석)
 */
typedef struct RelFileLocator
{
	Oid			spcOid;			/* tablespace */
	Oid			dbOid;			/* database */
	RelFileNumber relNumber;	/* relation */
} RelFileLocator;

/*
 * Augmenting a relfilelocator with the backend's proc number provides all the
 * information we need to locate the physical storage.  'backend' is
 * INVALID_PROC_NUMBER for regular relations (those accessible to more than
 * one backend), or the owning backend's proc number for backend-local
 * relations.  Backend-local relations are always transient and removed in
 * case of a database crash; they are never WAL-logged or fsync'd.
 */
typedef struct RelFileLocatorBackend
{
	RelFileLocator locator;
	ProcNumber	backend;
} RelFileLocatorBackend;
```

`RelFileNumber` 는 `Oid` 와 같은 32비트 정수다. 기본이 아닌 테이블스페이스 아래에는 메이저 버전마다 따로 쓰는 하위 디렉터리(relpath.h 주석 L30-L31 "major-version-specific tablespace subdirectories")가 하나 더 끼고, 그 이름에 메이저 버전과 카탈로그 버전이 들어간다.

`src` / `include` / `common` / `relpath.h` L22-L46 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/common/relpath.h#L22-L46))

```c
// src/include/common/relpath.h L22-L46
/*
 * RelFileNumber data type identifies the specific relation file name.
 */
typedef Oid RelFileNumber;
#define InvalidRelFileNumber		((RelFileNumber) InvalidOid)
#define RelFileNumberIsValid(relnumber) \
				((bool) ((relnumber) != InvalidRelFileNumber))

/*
 * Name of major-version-specific tablespace subdirectories
 */
#define TABLESPACE_VERSION_DIRECTORY	"PG_" PG_MAJORVERSION "_" \
									CppAsString2(CATALOG_VERSION_NO)

/*
 * Tablespace path (relative to installation's $PGDATA).
 *
 * These values should not be changed as many tools rely on it.
 */
#define PG_TBLSPC_DIR "pg_tblspc"
#define PG_TBLSPC_DIR_SLASH "pg_tblspc/"	/* required for strings
											 * comparisons */

/* Characters to allow for an OID in a relation path */
#define OIDCHARS		10		/* max chars printed by %u */
```

```text
 TABLESPACE_VERSION_DIRECTORY = "PG_" PG_MAJORVERSION "_" CATALOG_VERSION_NO
                              = "PG_" "18" "_" "202506291"           (catversion.h L60)
                              = "PG_18_202506291"
```

## fork 와 파일 이름 규칙

fork 는 enum 넷이고, 이름 배열의 순서가 그대로 번호다. main 은 이름이 있지만 파일 이름에는 붙지 않는다.

`src` / `include` / `common` / `relpath.h` L48-L73 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/common/relpath.h#L48-L73))

```c
// src/include/common/relpath.h L48-L73
/*
 * Stuff for fork names.
 *
 * The physical storage of a relation consists of one or more forks.
 * The main fork is always created, but in addition to that there can be
 * additional forks for storing various metadata. ForkNumber is used when
 * we need to refer to a specific fork in a relation.
 */
typedef enum ForkNumber
{
	InvalidForkNumber = -1,
	MAIN_FORKNUM = 0,
	FSM_FORKNUM,
	VISIBILITYMAP_FORKNUM,
	INIT_FORKNUM,

	/*
	 * NOTE: if you add a new fork, change MAX_FORKNUM and possibly
	 * FORKNAMECHARS below, and update the forkNames array in
	 * src/common/relpath.c
	 */
} ForkNumber;

#define MAX_FORKNUM		INIT_FORKNUM

#define FORKNAMECHARS	4		/* max chars for a fork name */
```

`src` / `common` / `relpath.c` L26-L38 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/common/relpath.c#L26-L38))

```c
// src/common/relpath.c L26-L38
/*
 * Lookup table of fork name by fork number.
 *
 * If you add a new entry, remember to update the errhint in
 * forkname_to_number() below, and update the SGML documentation for
 * pg_relation_size().
 */
const char *const forkNames[] = {
	[MAIN_FORKNUM] = "main",
	[FSM_FORKNUM] = "fsm",
	[VISIBILITYMAP_FORKNUM] = "vm",
	[INIT_FORKNUM] = "init",
};
```

경로를 만드는 함수는 하나다. 테이블스페이스가 `global` 인지, `base` 인지, 그 밖인지로 세 갈래, 각 갈래에서 임시 릴레이션인지(`procNumber` 가 있는지)와 main fork 인지로 다시 네 갈래가 된다.

`src` / `common` / `relpath.c` L132-L222 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/common/relpath.c#L132-L222))

```c
// src/common/relpath.c L132-L222
/*
 * GetRelationPath - construct path to a relation's file
 *
 * The result is returned in-place as a struct, to make it suitable for use in
 * critical sections etc.
 *
 * Note: ideally, procNumber would be declared as type ProcNumber, but
 * relpath.h would have to include a backend-only header to do that; doesn't
 * seem worth the trouble considering ProcNumber is just int anyway.
 */
RelPathStr
GetRelationPath(Oid dbOid, Oid spcOid, RelFileNumber relNumber,
				int procNumber, ForkNumber forkNumber)
{
	RelPathStr	rp;

	if (spcOid == GLOBALTABLESPACE_OID)
	{
		/* Shared system relations live in {datadir}/global */
		Assert(dbOid == 0);
		Assert(procNumber == INVALID_PROC_NUMBER);
		if (forkNumber != MAIN_FORKNUM)
			sprintf(rp.str, "global/%u_%s",
					relNumber, forkNames[forkNumber]);
		else
			sprintf(rp.str, "global/%u",
					relNumber);
	}
	else if (spcOid == DEFAULTTABLESPACE_OID)
	{
		/* The default tablespace is {datadir}/base */
		if (procNumber == INVALID_PROC_NUMBER)
		{
			if (forkNumber != MAIN_FORKNUM)
			{
				sprintf(rp.str, "base/%u/%u_%s",
						dbOid, relNumber,
						forkNames[forkNumber]);
			}
			else
				sprintf(rp.str, "base/%u/%u",
						dbOid, relNumber);
		}
		else
		{
			if (forkNumber != MAIN_FORKNUM)
				sprintf(rp.str, "base/%u/t%d_%u_%s",
						dbOid, procNumber, relNumber,
						forkNames[forkNumber]);
			else
				sprintf(rp.str, "base/%u/t%d_%u",
						dbOid, procNumber, relNumber);
		}
	}
	else
	{
		/* All other tablespaces are accessed via symlinks */
		if (procNumber == INVALID_PROC_NUMBER)
		{
			if (forkNumber != MAIN_FORKNUM)
				sprintf(rp.str, "%s/%u/%s/%u/%u_%s",
						PG_TBLSPC_DIR, spcOid,
						TABLESPACE_VERSION_DIRECTORY,
						dbOid, relNumber,
						forkNames[forkNumber]);
			else
				sprintf(rp.str, "%s/%u/%s/%u/%u",
						PG_TBLSPC_DIR, spcOid,
						TABLESPACE_VERSION_DIRECTORY,
						dbOid, relNumber);
		}
		else
		{
			if (forkNumber != MAIN_FORKNUM)
				sprintf(rp.str, "%s/%u/%s/%u/t%d_%u_%s",
						PG_TBLSPC_DIR, spcOid,
						TABLESPACE_VERSION_DIRECTORY,
						dbOid, procNumber, relNumber,
						forkNames[forkNumber]);
			else
				sprintf(rp.str, "%s/%u/%s/%u/t%d_%u",
						PG_TBLSPC_DIR, spcOid,
						TABLESPACE_VERSION_DIRECTORY,
						dbOid, procNumber, relNumber);
		}
	}

	Assert(strnlen(rp.str, REL_PATH_STR_MAXLEN + 1) <= REL_PATH_STR_MAXLEN);

	return rp;
}
```

```text
 GetRelationPath 의 열 가지 모양 (relpath.c L148-L216)

 spcOid             procNumber  fork   path
 -----------------  ----------  -----  -----------------------------------------------------------
 1664 (global)      INVALID     main   global/<rel>
                                other  global/<rel>_<fork>
 1663 (pg_default)  INVALID     main   base/<db>/<rel>
                                other  base/<db>/<rel>_<fork>
                    N           main   base/<db>/t<N>_<rel>
                                other  base/<db>/t<N>_<rel>_<fork>
 other              INVALID     main   pg_tblspc/<spc>/PG_18_202506291/<db>/<rel>
                                other  pg_tblspc/<spc>/PG_18_202506291/<db>/<rel>_<fork>
                    N           main   pg_tblspc/<spc>/PG_18_202506291/<db>/t<N>_<rel>
                                other  pg_tblspc/<spc>/PG_18_202506291/<db>/t<N>_<rel>_<fork>

 INVALID = INVALID_PROC_NUMBER (영구 릴레이션),  N = 임시 릴레이션을 가진 backend 의 procNumber

 global 은 dbOid = 0 이고 임시 릴레이션이 없다 (L151-L152 Assert)
 결과는 palloc 이 아니라 고정 길이 구조체 RelPathStr 로 돌려준다 (크리티컬 섹션에서도 부를 수 있게, L134-L135)
```

호출자는 보통 매크로로 부른다. 영구 릴레이션이면 `relpathperm`, `SMgrRelation` 이 들고 있는 `RelFileLocatorBackend` 를 그대로 넘기면 `relpath` 다.

`src` / `include` / `common` / `relpath.h` L136-L152 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/common/relpath.h#L136-L152))

```c
// src/include/common/relpath.h L136-L152
/*
 * Wrapper macros for GetRelationPath.  Beware of multiple
 * evaluation of the RelFileLocator or RelFileLocatorBackend argument!
 */

/* First argument is a RelFileLocator */
#define relpathbackend(rlocator, backend, forknum) \
	GetRelationPath((rlocator).dbOid, (rlocator).spcOid, (rlocator).relNumber, \
					backend, forknum)

/* First argument is a RelFileLocator */
#define relpathperm(rlocator, forknum) \
	relpathbackend(rlocator, INVALID_PROC_NUMBER, forknum)

/* First argument is a RelFileLocatorBackend */
#define relpath(rlocator, forknum) \
	relpathbackend((rlocator).locator, (rlocator).backend, forknum)
```

## 1GB 세그먼트

`md.c` 는 fork 하나를 `RELSEG_SIZE` 블록짜리 파일 여러 개로 나눠 저장한다. 앞 세그먼트들은 꽉 차 있고, 마지막 하나만 덜 차 있다. 잘라낸(truncate) 뒤의 세그먼트는 지우지 않고 길이 0 으로 남긴다. 다른 backend 나 checkpointer 가 그 파일을 열어 둔 채일 수 있기 때문이다(md.c L58-L66).

`storage` / `smgr` / `md.c` L43-L85 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/smgr/md.c#L43-L85))

```c
// storage/smgr/md.c L43-L85
/*
 * The magnetic disk storage manager keeps track of open file
 * descriptors in its own descriptor pool.  This is done to make it
 * easier to support relations that are larger than the operating
 * system's file size limit (often 2GBytes).  In order to do that,
 * we break relations up into "segment" files that are each shorter than
 * the OS file size limit.  The segment size is set by the RELSEG_SIZE
 * configuration constant in pg_config.h.
 *
 * On disk, a relation must consist of consecutively numbered segment
 * files in the pattern
 *	-- Zero or more full segments of exactly RELSEG_SIZE blocks each
 *	-- Exactly one partial segment of size 0 <= size < RELSEG_SIZE blocks
 *	-- Optionally, any number of inactive segments of size 0 blocks.
 * The full and partial segments are collectively the "active" segments.
 * Inactive segments are those that once contained data but are currently
 * not needed because of an mdtruncate() operation.  The reason for leaving
 * them present at size zero, rather than unlinking them, is that other
 * backends and/or the checkpointer might be holding open file references to
 * such segments.  If the relation expands again after mdtruncate(), such
 * that a deactivated segment becomes active again, it is important that
 * such file references still be valid --- else data might get written
 * out to an unlinked old copy of a segment file that will eventually
 * disappear.
 *
 // ... (L68-L78 생략: 열린 세그먼트 fd 배열(md_seg_fds)과 그 길이(md_num_open_segs)에 대한 설명)
 */

typedef struct _MdfdVec
{
	File		mdfd_vfd;		/* fd number in fd.c's pool */
	BlockNumber mdfd_segno;		/* segment number, from 0 */
} MdfdVec;
```

`RELSEG_SIZE` 는 소스 상수가 아니라 빌드 설정이다. `configure` 의 `--with-segsize`(GB 단위, 기본 1)에서 `RELSEG_SIZE = (1024 / blocksize) * segsize * 1024` 로 계산된다(configure.ac L284-L308). 기본 블록 크기 8kB 면 `(1024 / 8) * 1 * 1024 = 131072` 블록이다. 이 값은 `pg_control` 의 `relseg_size` 에도 적혀서, 다른 값으로 빌드한 서버가 이 PGDATA 를 열면 `ReadControlFile` 이 FATAL 로 시작을 멈춘다(xlog.c L4460-L4468).

세그먼트 파일 이름은 fork 경로 뒤에 `.세그먼트번호` 를 붙인 것이다. 세그먼트 0 에는 아무것도 붙지 않는다.

`storage` / `smgr` / `md.c` L1676-L1694 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/smgr/md.c#L1676-L1694))

```c
// storage/smgr/md.c L1676-L1694
/*
 * Return the filename for the specified segment of the relation. The
 * returned string is palloc'd.
 */
static MdPathStr
_mdfd_segpath(SMgrRelation reln, ForkNumber forknum, BlockNumber segno)
{
	RelPathStr	path;
	MdPathStr	fullpath;

	path = relpath(reln->smgr_rlocator, forknum);

	if (segno > 0)
		sprintf(fullpath.str, "%s.%u", path.str, segno);
	else
		strcpy(fullpath.str, path.str);

	return fullpath;
}
```

블록 번호에서 세그먼트와 파일 안 위치를 고르는 것은 나눗셈과 나머지다. 읽기 경로(`mdreadv`)를 예로 든다. 쓰기(`mdwritev`, L1082), 확장(`mdextend`, L508), AIO 읽기 시작(`mdstartreadv`, L1000)도 같은 식을 쓴다.

`storage` / `smgr` / `md.c` L1756-L1763 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/smgr/md.c#L1756-L1763))

```c
// storage/smgr/md.c L1756-L1763
	targetseg = blkno / ((BlockNumber) RELSEG_SIZE);

	/* if an existing and opened segment, we're done */
	if (targetseg < reln->md_num_open_segs[forknum])
	{
		v = &reln->md_seg_fds[forknum][targetseg];
		return v;
	}
```

`storage` / `smgr` / `md.c` L862-L871 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/smgr/md.c#L862-L871))

```c
// storage/smgr/md.c L862-L871
		v = _mdfd_getseg(reln, forknum, blocknum, false,
						 EXTENSION_FAIL | EXTENSION_CREATE_RECOVERY);

		seekpos = (off_t) BLCKSZ * (blocknum % ((BlockNumber) RELSEG_SIZE));

		Assert(seekpos < (off_t) BLCKSZ * RELSEG_SIZE);

		nblocks_this_segment =
			Min(nblocks,
				RELSEG_SIZE - (blocknum % ((BlockNumber) RELSEG_SIZE)));
```

```text
 예: base/5/16385 의 main fork 블록 200000 을 읽는다 (BLCKSZ 8192, RELSEG_SIZE 131072)

 targetseg = 200000 / 131072            = 1        -> _mdfd_segpath -> "base/5/16385.1"
 seekpos   = 8192 * (200000 % 131072)
           = 8192 * 68928               = 564658176  (0x21A80000)

 base/5/16385      [블록 0 ............................ 블록 131071]   1073741824 바이트
 base/5/16385.1    [블록 131072 ... 블록 200000 ... 블록 262143]
                                    ^
                                    파일 안 오프셋 564658176

 한 번의 mdreadv 는 세그먼트 경계를 넘지 않는다
   nblocks_this_segment = min(nblocks, 131072 - 68928) = min(nblocks, 62144)   (L869-L871)
   더 남았으면 while 을 한 바퀴 더 돌아 다음 세그먼트를 연다
```

## 커밋 로그 파일 (pg_xact)

데이터 파일 밖에서 가시성 판정이 가장 자주 읽는 파일은 `pg_xact/` 다. 트랜잭션 id 하나에 2비트를 써서 진행 중, 커밋, abort, 하위 커밋 넷을 구분한다. 파일은 SLRU(작은 LRU 버퍼를 거치는 단순 페이지 파일) 형식이고, 8192바이트 페이지 32장이 파일 하나다.

`src` / `include` / `access` / `clog.h` L26-L30 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/clog.h#L26-L30))

```c
// src/include/access/clog.h L26-L30

#define TRANSACTION_STATUS_IN_PROGRESS		0x00
#define TRANSACTION_STATUS_COMMITTED		0x01
#define TRANSACTION_STATUS_ABORTED			0x02
#define TRANSACTION_STATUS_SUB_COMMITTED	0x03
```

`access` / `transam` / `clog.c` L61-L89 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/clog.c#L61-L89))

```c
// access/transam/clog.c L61-L89
/* We need two bits per xact, so four xacts fit in a byte */
#define CLOG_BITS_PER_XACT	2
#define CLOG_XACTS_PER_BYTE 4
#define CLOG_XACTS_PER_PAGE (BLCKSZ * CLOG_XACTS_PER_BYTE)
#define CLOG_XACT_BITMASK	((1 << CLOG_BITS_PER_XACT) - 1)

/*
 * Because space used in CLOG by each transaction is so small, we place a
 * smaller limit on the number of CLOG buffers than SLRU allows.  No other
 * SLRU needs this.
 */
#define CLOG_MAX_ALLOWED_BUFFERS \
	Min(SLRU_MAX_ALLOWED_BUFFERS, \
		(((MaxTransactionId / 2) + (CLOG_XACTS_PER_PAGE - 1)) / CLOG_XACTS_PER_PAGE))


/*
 * Although we return an int64 the actual value can't currently exceed
 * 0xFFFFFFFF/CLOG_XACTS_PER_PAGE.
 */
static inline int64
TransactionIdToPage(TransactionId xid)
{
	return xid / (int64) CLOG_XACTS_PER_PAGE;
}

#define TransactionIdToPgIndex(xid) ((xid) % (TransactionId) CLOG_XACTS_PER_PAGE)
#define TransactionIdToByte(xid)	(TransactionIdToPgIndex(xid) / CLOG_XACTS_PER_BYTE)
#define TransactionIdToBIndex(xid)	((xid) % (TransactionId) CLOG_XACTS_PER_BYTE)
```

`src` / `include` / `access` / `slru.h` L39-L39 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/slru.h#L39-L39))

```c
// src/include/access/slru.h L39-L39
#define SLRU_PAGES_PER_SEGMENT	32
```

`access` / `transam` / `slru.c` L90-L115 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/slru.c#L90-L115))

```c
// access/transam/slru.c L90-L115
static inline int
SlruFileName(SlruCtl ctl, char *path, int64 segno)
{
	if (ctl->long_segment_names)
	{
		/*
		 * We could use 16 characters here but the disadvantage would be that
		 * the SLRU segments will be hard to distinguish from WAL segments.
		 *
		 * For this reason we use 15 characters. It is enough but also means
		 * that in the future we can't decrease SLRU_PAGES_PER_SEGMENT easily.
		 */
		Assert(segno >= 0 && segno <= INT64CONST(0xFFFFFFFFFFFFFFF));
		return snprintf(path, MAXPGPATH, "%s/%015" PRIX64, ctl->Dir, segno);
	}
	else
	{
		/*
		 * Despite the fact that %04X format string is used up to 24 bit
		 * integers are allowed. See SlruCorrectSegmentFilenameLength()
		 */
		Assert(segno >= 0 && segno <= INT64CONST(0xFFFFFF));
		return snprintf(path, MAXPGPATH, "%s/%04X", (ctl)->Dir,
						(unsigned int) segno);
	}
}
```

```text
 xid 1000000 의 커밋 상태는 어디에 있나 (BLCKSZ 8192)

 CLOG_XACTS_PER_PAGE      = 8192 * 4             = 32768
 TransactionIdToPage      = 1000000 / 32768      = 30       페이지 번호
 segno                    = 30 / 32              = 0        -> pg_xact/0000  (%04X)
 TransactionIdToPgIndex   = 1000000 % 32768      = 16960    페이지 안 xid 순번
 TransactionIdToByte      = 16960 / 4            = 4240     바이트
 TransactionIdToBIndex    = 16960 % 4            = 0        bshift = 0 * 2 = 0 (clog.c L739)

 file offset              = (30 % 32) * 8192 + 4240 = 250000   ( = 1000000 / 4 )

 byte 4240 of page 30
  bit  7 6   5 4   3 2   1 0
      +-----+-----+-----+-----+
      | +3  | +2  | +1  | xid |    xid 1000000 은 아래 2비트
      +-----+-----+-----+-----+    01 = COMMITTED, 10 = ABORTED

 파일 하나 = 32 페이지 x 32768 = 1048576 개 xid,  크기 256KB
```

`pg_multixact/offsets`, `pg_multixact/members`, `pg_subtrans`, `pg_commit_ts` 도 같은 SLRU 형식이고 디렉터리만 다르다(`SimpleLruInit` 호출, multixact.c L2134-L2145, subtrans.c L244-L245, commit_ts.c L556-L557). pg_xact 를 실제로 읽는 쪽은 [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md)의 `TransactionIdDidCommit` 이다.

## pg_control

`global/pg_control` 은 릴레이션이 아닌 고정 형식 파일이다. 마지막 체크포인트 레코드의 위치와 그 사본, 클러스터 상태, 그리고 빌드 상수(블록 크기, 세그먼트 크기 등)를 담는다. 서버는 시작할 때 이 파일부터 읽어 어디서 복구를 시작할지 정한다.

`src` / `include` / `catalog` / `pg_control.h` L85-L239 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/catalog/pg_control.h#L85-L239))

```c
// src/include/catalog/pg_control.h L85-L239
/*
 * System status indicator.  Note this is stored in pg_control; if you change
 * it, you must bump PG_CONTROL_VERSION
 */
typedef enum DBState
{
	DB_STARTUP = 0,
	DB_SHUTDOWNED,
	DB_SHUTDOWNED_IN_RECOVERY,
	DB_SHUTDOWNING,
	DB_IN_CRASH_RECOVERY,
	DB_IN_ARCHIVE_RECOVERY,
	DB_IN_PRODUCTION,
} DBState;

/*
 * Contents of pg_control.
 */

typedef struct ControlFileData
{
	/*
	 * Unique system identifier --- to ensure we match up xlog files with the
	 * installation that produced them.
	 */
	uint64		system_identifier;

	/*
	 * Version identifier information.  Keep these fields at the same offset,
	 * especially pg_control_version; they won't be real useful if they move
	 * around.  (For historical reasons they must be 8 bytes into the file
	 * rather than immediately at the front.)
	 *
	 * pg_control_version identifies the format of pg_control itself.
	 * catalog_version_no identifies the format of the system catalogs.
	 *
	 * There are additional version identifiers in individual files; for
	 * example, WAL logs contain per-page magic numbers that can serve as
	 * version cues for the WAL log.
	 */
	uint32		pg_control_version; /* PG_CONTROL_VERSION */
	uint32		catalog_version_no; /* see catversion.h */

	/*
	 * System status data
	 */
	DBState		state;			/* see enum above */
	pg_time_t	time;			/* time stamp of last pg_control update */
	XLogRecPtr	checkPoint;		/* last check point record ptr */

	CheckPoint	checkPointCopy; /* copy of last check point record */

	XLogRecPtr	unloggedLSN;	/* current fake LSN value, for unlogged rels */

	/*
	 // ... (L140-L166 생략: minRecoveryPoint, backupStartPoint, backupEndPoint, backupEndRequired 의 뜻 (아카이브 복구와 백업용))
	 */
	XLogRecPtr	minRecoveryPoint;
	TimeLineID	minRecoveryPointTLI;
	XLogRecPtr	backupStartPoint;
	XLogRecPtr	backupEndPoint;
	bool		backupEndRequired;

	/*
	 * Parameter settings that determine if the WAL can be used for archival
	 * or hot standby.
	 */
	int			wal_level;
	bool		wal_log_hints;
	int			MaxConnections;
	int			max_worker_processes;
	int			max_wal_senders;
	int			max_prepared_xacts;
	int			max_locks_per_xact;
	bool		track_commit_timestamp;

	/*
	 * This data is used to check for hardware-architecture compatibility of
	 * the database and the backend executable.  We need not check endianness
	 * explicitly, since the pg_control version will surely look wrong to a
	 * machine of different endianness, but we do need to worry about MAXALIGN
	 * and floating-point format.  (Note: storage layout nominally also
	 * depends on SHORTALIGN and INTALIGN, but in practice these are the same
	 * on all architectures of interest.)
	 *
	 * Testing just one double value is not a very bulletproof test for
	 * floating-point compatibility, but it will catch most cases.
	 */
	uint32		maxAlign;		/* alignment requirement for tuples */
	double		floatFormat;	/* constant 1234567.0 */
#define FLOATFORMAT_VALUE	1234567.0

	/*
	 * This data is used to make sure that configuration of this database is
	 * compatible with the backend executable.
	 */
	uint32		blcksz;			/* data block size for this DB */
	uint32		relseg_size;	/* blocks per segment of large relation */

	uint32		xlog_blcksz;	/* block size within WAL files */
	uint32		xlog_seg_size;	/* size of each WAL segment */

	uint32		nameDataLen;	/* catalog name field width */
	uint32		indexMaxKeys;	/* max number of columns in an index */

	uint32		toast_max_chunk_size;	/* chunk size in TOAST tables */
	uint32		loblksize;		/* chunk size in pg_largeobject */

	bool		float8ByVal;	/* float8, int8, etc pass-by-value? */

	/* Are data pages protected by checksums? Zero if no checksum version */
	uint32		data_checksum_version;

	/*
	 * True if the default signedness of char is "signed" on a platform where
	 * the cluster is initialized.
	 */
	bool		default_char_signedness;

	/*
	 * Random nonce, used in authentication requests that need to proceed
	 * based on values that are cluster-unique, like a SASL exchange that
	 * failed at an early stage.
	 */
	char		mock_authentication_nonce[MOCK_AUTH_NONCE_LEN];

	/* CRC of all above ... MUST BE LAST! */
	pg_crc32c	crc;
} ControlFileData;
```

```text
 ControlFileData 앞부분 바이트 배치 (x86-64, 이 태그의 pg_control.h 를 컴파일해 offsetof 확인)

 offset  size  field                 뜻
 ------  ----  --------------------  ------------------------------------------
      0     8  system_identifier     initdb 때 정한 고유 번호. WAL 긴 페이지 헤더에도 들어간다
      8     4  pg_control_version    1800 (PG_CONTROL_VERSION)
     12     4  catalog_version_no    202506291
     16     4  state                 DBState. DB_SHUTDOWNED = 1, DB_IN_PRODUCTION = 6
     24     8  time                  마지막 갱신 시각
     32     8  checkPoint            마지막 체크포인트 레코드의 LSN
     40    88  checkPointCopy        그 레코드 본문(CheckPoint)의 사본. redo, nextXid, nextOid ...
    128     8  unloggedLSN
    ...        minRecoveryPoint, wal_level, max_connections ... blcksz, relseg_size,
               xlog_blcksz, xlog_seg_size, data_checksum_version ...
    292     4  crc                   앞 292바이트의 CRC-32C. 반드시 마지막 필드
    296        sizeof(ControlFileData)

 파일 크기는 PG_CONTROL_FILE_SIZE = 8192. 296 뒤는 0 으로 채운다
 갱신은 한 번의 write 로 원자적이어야 하므로 크기 상한은 512 (PG_CONTROL_MAX_SAFE_SIZE)
```

크기 상수 둘의 이유는 소스 주석에 있다. 512 는 흔한 디스크 섹터 크기라 한 번의 쓰기가 원자적이게 하는 상한이고, 8192 는 형식이 바뀌어도 파일 크기를 같게 두어 "읽기 실패" 대신 "버전이 다르다" 오류를 내게 하려는 크기다.

`src` / `include` / `catalog` / `pg_control.h` L241-L256 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/catalog/pg_control.h#L241-L256))

```c
// src/include/catalog/pg_control.h L241-L256
/*
 * Maximum safe value of sizeof(ControlFileData).  For reliability's sake,
 * it's critical that pg_control updates be atomic writes.  That generally
 * means the active data can't be more than one disk sector, which is 512
 * bytes on common hardware.  Be very careful about raising this limit.
 */
#define PG_CONTROL_MAX_SAFE_SIZE	512

/*
 * Physical size of the pg_control file.  Note that this is considerably
 * bigger than the actually used size (ie, sizeof(ControlFileData)).
 * The idea is to keep the physical size constant independent of format
 * changes, so that ReadControlFile will deliver a suitable wrong-version
 * message instead of a read error if it's looking at an incompatible file.
 */
#define PG_CONTROL_FILE_SIZE		8192
```

`src` / `include` / `access` / `xlog_internal.h` L146-L150 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/access/xlog_internal.h#L146-L150))

```c
// src/include/access/xlog_internal.h L146-L150
/*
 * The XLog directory and control file (relative to $PGDATA)
 */
#define XLOGDIR				"pg_wal"
#define XLOG_CONTROL_FILE	"global/pg_control"
```

파일을 처음 만드는 곳은 initdb 의 bootstrap 단계에서 `BootStrapXLOG` 가 부르는 `WriteControlFile` 이다(xlog.c L5219). 빌드 상수를 채우고 CRC 를 계산한 뒤 8192바이트를 한 번에 쓰고 fsync 한다.

`access` / `transam` / `xlog.c` L4234-L4316 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L4234-L4316))

```c
// access/transam/xlog.c L4234-L4316
static void
WriteControlFile(void)
{
	int			fd;
	char		buffer[PG_CONTROL_FILE_SIZE];	/* need not be aligned */

	/*
	 * Initialize version and compatibility-check fields
	 */
	ControlFile->pg_control_version = PG_CONTROL_VERSION;
	ControlFile->catalog_version_no = CATALOG_VERSION_NO;

	ControlFile->maxAlign = MAXIMUM_ALIGNOF;
	ControlFile->floatFormat = FLOATFORMAT_VALUE;

	ControlFile->blcksz = BLCKSZ;
	ControlFile->relseg_size = RELSEG_SIZE;
	ControlFile->xlog_blcksz = XLOG_BLCKSZ;
	ControlFile->xlog_seg_size = wal_segment_size;

	ControlFile->nameDataLen = NAMEDATALEN;
	ControlFile->indexMaxKeys = INDEX_MAX_KEYS;

	ControlFile->toast_max_chunk_size = TOAST_MAX_CHUNK_SIZE;
	ControlFile->loblksize = LOBLKSIZE;

	ControlFile->float8ByVal = FLOAT8PASSBYVAL;

	// ... (L4262-L4287 생략: default_char_signedness 를 true 로 두는 이유 (pg_upgrade 호환))

	/* Contents are protected with a CRC */
	INIT_CRC32C(ControlFile->crc);
	COMP_CRC32C(ControlFile->crc,
				ControlFile,
				offsetof(ControlFileData, crc));
	FIN_CRC32C(ControlFile->crc);

	/*
	 * We write out PG_CONTROL_FILE_SIZE bytes into pg_control, zero-padding
	 * the excess over sizeof(ControlFileData).  This reduces the odds of
	 * premature-EOF errors when reading pg_control.  We'll still fail when we
	 * check the contents of the file, but hopefully with a more specific
	 * error than "couldn't read pg_control".
	 */
	memset(buffer, 0, PG_CONTROL_FILE_SIZE);
	memcpy(buffer, ControlFile, sizeof(ControlFileData));

	fd = BasicOpenFile(XLOG_CONTROL_FILE,
					   O_RDWR | O_CREAT | O_EXCL | PG_BINARY);
	if (fd < 0)
		ereport(PANIC,
				(errcode_for_file_access(),
				 errmsg("could not create file \"%s\": %m",
						XLOG_CONTROL_FILE)));

	errno = 0;
	pgstat_report_wait_start(WAIT_EVENT_CONTROL_FILE_WRITE);
	if (write(fd, buffer, PG_CONTROL_FILE_SIZE) != PG_CONTROL_FILE_SIZE)
```

그 뒤로는 체크포인트가 끝날 때마다 `checkPoint` 와 `checkPointCopy` 를 바꿔 쓴다. 정상 종료 체크포인트면 `state` 도 `DB_SHUTDOWNED` 가 된다.

`access` / `transam` / `xlog.c` L7289-L7309 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/access/transam/xlog.c#L7289-L7309))

```c
// access/transam/xlog.c L7289-L7309
	/*
	 * Update the control file.
	 */
	LWLockAcquire(ControlFileLock, LW_EXCLUSIVE);
	if (shutdown)
		ControlFile->state = DB_SHUTDOWNED;
	ControlFile->checkPoint = ProcLastRecPtr;
	ControlFile->checkPointCopy = checkPoint;
	/* crash recovery should always recover to the end of WAL */
	ControlFile->minRecoveryPoint = InvalidXLogRecPtr;
	ControlFile->minRecoveryPointTLI = 0;

	/*
	 * Persist unloggedLSN value. It's reset on crash recovery, so this goes
	 * unused on non-shutdown checkpoints, but seems useful to store it always
	 * for debugging purposes.
	 */
	ControlFile->unloggedLSN = pg_atomic_read_membarrier_u64(&XLogCtl->unloggedLSN);

	UpdateControlFile();
	LWLockRelease(ControlFileLock);
```

```text
 pg_control 이 바뀌는 때 (xlog.c)

 L4235       WriteControlFile                 initdb bootstrap. O_CREAT | O_EXCL 로 새로 만든다
 L6982       state = DB_SHUTDOWNING           정상 종료 체크포인트 시작
 L7294       state = DB_SHUTDOWNED            정상 종료 체크포인트 끝
 L7295-L7296 checkPoint, checkPointCopy       모든 체크포인트 끝
 L6253       state = DB_IN_ARCHIVE_RECOVERY   아카이브 복구 중
 L6207       state = DB_IN_PRODUCTION         복구 끝, 운영 시작

 시작 때 state 가 DB_SHUTDOWNED 가 아니면 InRecovery = true   (xlogrecovery.c L940-L941)
 checkPointCopy.redo 부터 WAL 을 다시 읽는다
```

갱신은 `UpdateControlFile` -> `update_controlfile`(src/common/controldata_utils.c L189) 이 맡는다. 체크포인트가 이 갱신에 이르는 길은 [CreateCheckPoint](../../flows/checkpoint/03_CreateCheckPoint/README.md)에 있다.

## db-engine 에서는

db-engine 의 저장 단위는 **파일 하나**다. `PagedFile` 이 `RandomAccessFile` 하나를 열고, 페이지 번호에 4096 을 곱한 위치를 읽고 쓴다. fork 도, 세그먼트도, 클러스터 상태 파일도 없다.

```text
 같은 문제(블록 번호 -> 파일과 오프셋), 두 구현

 PostgreSQL                                      db-engine (PagedFile)
 ----------------------------------------------  ---------------------------------------
 (spcOid, dbOid, relNumber, fork, blockNum)      PageId(fileId, pageNumber)
        |                                               |
        v  GetRelationPath                              v
 base/5/16385[_fsm|_vm|_init]                    생성자에 넘긴 path 하나
        |                                               |
        v  blockNum / 131072  -> ".1" ".2" ...          v  (분할 없음)
 세그먼트 파일                                    같은 파일
        |                                               |
        v  8192 * (blockNum % 131072)                   v  pageNumber * 4096
 파일 안 오프셋                                    파일 안 오프셋

 페이지 크기
   PostgreSQL  8192 (BLCKSZ, 빌드 설정)
   db-engine   4096 (Page.PAGE_SIZE)
 확장
   PostgreSQL  mdextend 가 블록을 붙이고, 세그먼트를 넘으면 새 파일을 만든다
   db-engine   allocatePage 가 0 으로 채운 4096바이트를 파일 끝에 쓴다
 클러스터 상태
   PostgreSQL  global/pg_control (296바이트 + CRC)
   db-engine   없음. 마지막 적용 LSN 은 recovery.meta (08-02)
```

db-engine 은 파일 크기를 `pageCount = length / 4096` 으로 바로 얻는다. PostgreSQL 은 fork 마다 세그먼트를 차례로 열어 마지막 덜 찬 세그먼트를 찾아야 길이를 안다(md.c L52-L56 의 규칙). 세그먼트 분할은 OS 파일 크기 한도를 피하려는 장치라고 md.c 주석(L44-L50)이 밝힌다. 챕터: [02-01-page-pagedfile](../../../../../project/db-engine/02-01-page-pagedfile/).

## 어디에서 쓰이는가

```text
 [버퍼 관리]          BufferTag 의 (spcOid, dbOid, relNumber, forkNum) 로 smgr 을 열고
                      blockNum 으로 mdreadv / mdwritev 가 세그먼트와 오프셋을 고른다
                      더러운 버퍼를 쓰는 FlushBuffer -> smgrwrite (bufmgr.c L4393)
 [행 쓰기와 WAL 기록] 릴레이션 확장은 fork 끝에 블록을 붙인다 (hio.c 의 확장 경로)
                      WAL 블록 참조에는 RelFileLocator 12바이트 + BlockNumber 4바이트가 실린다
 [MVCC 가시성]        TransactionIdDidCommit 이 pg_xact 의 2비트를 읽는다
 [체크포인트]         더러운 버퍼를 쓰고 세그먼트 파일마다 fsync 요청을 처리한 뒤
                      pg_control 의 checkPoint 를 바꾼다
 [WAL redo]           시작할 때 pg_control 의 state 와 checkPointCopy.redo 로 복구 여부와 시작점을 정한다
```

흐름 문서: [버퍼 관리](../../flows/buffer-manager/README.md)(쓰기는 [FlushBuffer](../../flows/buffer-manager/09_FlushBuffer/README.md)), [체크포인트](../../flows/checkpoint/README.md), [MVCC 가시성과 스냅샷](../../flows/mvcc-visibility/README.md), [WAL redo](../../flows/wal-redo/README.md). WAL 쪽 파일 배치는 [WAL 레코드 형식](../wal-record-format/README.md)에 있다.

## 다루지 않는 것

매핑된 카탈로그의 `pg_filenode.map` 형식(relmapper.c), 새 relfilenode 번호를 고르는 `GetNewRelFileNumber`(catalog.c L557), FSM 과 VM 파일 안의 페이지 구조, 테이블스페이스 심볼릭 링크를 만들고 지우는 과정(tablespace.c), `pg_xact` 이외 SLRU 의 내부 형식(multixact 의 offsets/members 배치, commit_ts 의 레코드), 세그먼트 fd 를 여닫는 `fd.c` 의 가상 파일 디스크립터, `pg_stat/` 과 `pg_logical/` 같은 부가 디렉터리의 내용은 곁가지라 다루지 않았다.
