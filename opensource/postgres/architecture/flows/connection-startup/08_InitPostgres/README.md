# InitPostgres

상위: [연결과 backend 기동](../README.md)

backend 를 **다른 backend 에게 보이게 하고, 인증하고, 데이터베이스 하나에 붙이는** 함수다. 모든 일이 한 트랜잭션 안에서 일어난다 - 인증과 데이터베이스 조회가 카탈로그를 읽어야 하기 때문이다. 순서가 까다롭다(L707-L708 주석 "Be very careful with the order"). 데이터베이스에 락을 잡고, **그 뒤에** `pg_database` 를 다시 읽고, **그 뒤에야** `MyDatabaseId` 를 정한다. 동시에 일어나는 `DROP DATABASE` 와 엇갈리지 않기 위해서다.

## 위치

`utils` / `init` / `postinit.c` L712-L1237 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L712-L1237))

## 실제 코드

`ProcArray` 에 오르고, 공유 무효화와 시간 제한 처리기를 등록하고, 캐시를 준비한다.

`utils` / `init` / `postinit.c` L712-L829 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L712-L829))

```c
// init/postinit.c L712-L829
InitPostgres(const char *in_dbname, Oid dboid,
			 const char *username, Oid useroid,
			 bits32 flags,
			 char *out_dbname)
{
	bool		bootstrap = IsBootstrapProcessingMode();
	bool		am_superuser;
	char	   *fullpath;
	char		dbname[NAMEDATALEN];
	int			nfree = 0;

	elog(DEBUG3, "InitPostgres");

	/*
	 * Add my PGPROC struct to the ProcArray.
	 *
	 * Once I have done this, I am visible to other backends!
	 */
	InitProcessPhase2();

	/* Initialize status reporting */
	pgstat_beinit();

// ... (L735-L739 생략: 주석)
	if (!bootstrap)
	{
		pgstat_bestart_initial();
		INJECTION_POINT("init-pre-auth", NULL);
	}

	/*
	 * Initialize my entry in the shared-invalidation manager's array of
	 * per-backend data.
	 */
	SharedInvalBackendInit(false);

	ProcSignalInit(MyCancelKey, MyCancelKeyLength);

	/*
	 * Also set up timeout handlers needed for backend operation.  We need
	 * these in every case except bootstrap.
	 */
	if (!bootstrap)
	{
		RegisterTimeout(DEADLOCK_TIMEOUT, CheckDeadLockAlert);
		RegisterTimeout(STATEMENT_TIMEOUT, StatementTimeoutHandler);
		RegisterTimeout(LOCK_TIMEOUT, LockTimeoutHandler);
		RegisterTimeout(IDLE_IN_TRANSACTION_SESSION_TIMEOUT,
						IdleInTransactionSessionTimeoutHandler);
		RegisterTimeout(TRANSACTION_TIMEOUT, TransactionTimeoutHandler);
		RegisterTimeout(IDLE_SESSION_TIMEOUT, IdleSessionTimeoutHandler);
		RegisterTimeout(CLIENT_CONNECTION_CHECK_TIMEOUT, ClientCheckTimeoutHandler);
		RegisterTimeout(IDLE_STATS_UPDATE_TIMEOUT,
						IdleStatsUpdateTimeoutHandler);
	}

// ... (L772-L799 생략: 독립 실행 backend 의 StartupXLOG)

// ... (L801-L806 생략: 주석)
	RelationCacheInitialize();
	InitCatalogCache();
	InitPlanCache();

	/* Initialize portal manager */
	EnablePortalManager();

// ... (L814-L817 생략: 주석)
	RelationCacheInitializePhase2();

// ... (L820-L828 생략: 주석)
	before_shmem_exit(ShutdownPostgres, 0);
```

첫 트랜잭션을 열고, 인증하고, 세션 사용자를 정한다. 일반 연결은 마지막 `else` 로 간다.

`utils` / `init` / `postinit.c` L840-L907 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L840-L907))

```c
// init/postinit.c L840-L907
	/*
	 * Start a new transaction here before first access to db.
	 */
	if (!bootstrap)
	{
		/* statement_timestamp must be set for timeouts to work correctly */
		SetCurrentStatementStartTimestamp();
		StartTransactionCommand();

// ... (L849-L854 생략: 주석)
		XactIsoLevel = XACT_READ_COMMITTED;
	}

	/*
	 * Perform client authentication if necessary, then figure out our
	 * postgres user ID, and see if we are a superuser.
	 *
	 * In standalone mode, autovacuum worker processes and slot sync worker
	 * process, we use a fixed ID, otherwise we figure it out from the
	 * authenticated user name.
	 */
// ... (L866-L895 생략: 부트스트랩, autovacuum, 독립 실행, bgworker 분기)
	else
	{
		/* normal multiuser case */
		Assert(MyProcPort != NULL);
		PerformAuthentication(MyProcPort);
		InitializeSessionUserId(username, useroid, false);
		/* ensure that auth_method is actually valid, aka authn_id is not NULL */
		if (MyClientConnectionInfo.authn_id)
			InitializeSystemUser(MyClientConnectionInfo.authn_id,
								 hba_authname(MyClientConnectionInfo.auth_method));
		am_superuser = superuser();
	}
```

마지막 몇 자리를 superuser 에게 남기는 검사다.

`utils` / `init` / `postinit.c` L927-L952 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L927-L952))

```c
// init/postinit.c L927-L952
	/*
	 * The last few regular connection slots are reserved for superusers and
	 * roles with privileges of pg_use_reserved_connections.  We do not apply
	 * these limits to background processes, since they all have their own
	 * pools of PGPROC slots.
	 *
	 * Note: At this point, the new backend has already claimed a proc struct,
	 * so we must check whether the number of free slots is strictly less than
	 * the reserved connection limits.
	 */
	if (AmRegularBackendProcess() && !am_superuser &&
		(SuperuserReservedConnections + ReservedConnections) > 0 &&
		!HaveNFreeProcs(SuperuserReservedConnections + ReservedConnections, &nfree))
	{
		if (nfree < SuperuserReservedConnections)
			ereport(FATAL,
					(errcode(ERRCODE_TOO_MANY_CONNECTIONS),
					 errmsg("remaining connection slots are reserved for roles with the %s attribute",
							"SUPERUSER")));

		if (!has_privs_of_role(GetUserId(), ROLE_PG_USE_RESERVED_CONNECTIONS))
			ereport(FATAL,
					(errcode(ERRCODE_TOO_MANY_CONNECTIONS),
					 errmsg("remaining connection slots are reserved for roles with privileges of the \"%s\" role",
							"pg_use_reserved_connections")));
	}
```

데이터베이스를 찾고, 락을 잡고, 다시 확인한다.

`utils` / `init` / `postinit.c` L1002-L1131 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L1002-L1131))

```c
// init/postinit.c L1002-L1131
	if (bootstrap)
	{
		dboid = Template1DbOid;
		MyDatabaseTableSpace = DEFAULTTABLESPACE_OID;
	}
	else if (in_dbname != NULL)
	{
		HeapTuple	tuple;
		Form_pg_database dbform;

		tuple = GetDatabaseTuple(in_dbname);
		if (!HeapTupleIsValid(tuple))
			ereport(FATAL,
					(errcode(ERRCODE_UNDEFINED_DATABASE),
					 errmsg("database \"%s\" does not exist", in_dbname)));
		dbform = (Form_pg_database) GETSTRUCT(tuple);
		dboid = dbform->oid;
	}
// ... (L1020-L1034 생략: 데이터베이스 없는 background worker)

// ... (L1036-L1056 생략: 주석)
	if (!bootstrap)
		LockSharedObject(DatabaseRelationId, dboid, 0, RowExclusiveLock);

// ... (L1060-L1064 생략: 주석)
	if (!bootstrap)
	{
		HeapTuple	tuple;
		Form_pg_database datform;

		tuple = GetDatabaseTupleByOid(dboid);
		if (HeapTupleIsValid(tuple))
			datform = (Form_pg_database) GETSTRUCT(tuple);

		if (!HeapTupleIsValid(tuple) ||
			(in_dbname && namestrcmp(&datform->datname, in_dbname)))
		{
			if (in_dbname)
				ereport(FATAL,
						(errcode(ERRCODE_UNDEFINED_DATABASE),
						 errmsg("database \"%s\" does not exist", in_dbname),
						 errdetail("It seems to have just been dropped or renamed.")));
			else
				ereport(FATAL,
						(errcode(ERRCODE_UNDEFINED_DATABASE),
						 errmsg("database %u does not exist", dboid)));
		}

		strlcpy(dbname, NameStr(datform->datname), sizeof(dbname));

		if (database_is_invalid_form(datform))
		{
			ereport(FATAL,
					errcode(ERRCODE_OBJECT_NOT_IN_PREREQUISITE_STATE),
					errmsg("cannot connect to invalid database \"%s\"", dbname),
					errhint("Use DROP DATABASE to drop invalid databases."));
		}

		MyDatabaseTableSpace = datform->dattablespace;
		MyDatabaseHasLoginEventTriggers = datform->dathasloginevt;
		/* pass the database name back to the caller */
		if (out_dbname)
			strcpy(out_dbname, dbname);
	}

// ... (L1105-L1115 생략: 주석)
	MyDatabaseId = dboid;

// ... (L1118-L1129 생략: 주석)
	MyProc->databaseId = MyDatabaseId;

```

데이터베이스 디렉터리를 확인하고, 세션 설정을 적용하고, 트랜잭션을 닫는다.

`utils` / `init` / `postinit.c` L1140-L1237 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/utils/init/postinit.c#L1140-L1237))

```c
// init/postinit.c L1140-L1237
	/*
	 * Now we should be able to access the database directory safely. Verify
	 * it's there and looks reasonable.
	 */
	fullpath = GetDatabasePath(MyDatabaseId, MyDatabaseTableSpace);

	if (!bootstrap)
	{
		if (access(fullpath, F_OK) == -1)
		{
			if (errno == ENOENT)
				ereport(FATAL,
						(errcode(ERRCODE_UNDEFINED_DATABASE),
						 errmsg("database \"%s\" does not exist",
								dbname),
						 errdetail("The database subdirectory \"%s\" is missing.",
								   fullpath)));
			else
				ereport(FATAL,
						(errcode_for_file_access(),
						 errmsg("could not access directory \"%s\": %m",
								fullpath)));
		}

		ValidatePgVersion(fullpath);
	}

	SetDatabasePath(fullpath);
	pfree(fullpath);

// ... (L1170-L1175 생략: 주석)
	RelationCacheInitializePhase3();

	/* set up ACL framework (so CheckMyDatabase can check permissions) */
	initialize_acl();

// ... (L1181-L1186 생략: 주석)
	if (!bootstrap)
		CheckMyDatabase(dbname, am_superuser,
						(flags & INIT_PG_OVERRIDE_ALLOW_CONNS) != 0);

// ... (L1191-L1195 생략: 주석)
	if (MyProcPort != NULL)
		process_startup_options(MyProcPort, am_superuser);

	/* Process pg_db_role_setting options */
	process_settings(MyDatabaseId, GetSessionUserId());

	/* Apply PostAuthDelay as soon as we've read all options */
	if (PostAuthDelay > 0)
		pg_usleep(PostAuthDelay * 1000000L);

// ... (L1206-L1210 생략: 주석)
	/* set default namespace search path */
	InitializeSearchPath();

	/* initialize client encoding */
	InitializeClientEncoding();

	/* Initialize this backend's session state. */
	InitializeSession();

// ... (L1220-L1226 생략: 주석)
	if ((flags & INIT_PG_LOAD_SESSION_LIBS) != 0)
		process_session_preload_libraries();

	/* fill in the remainder of this entry in the PgBackendStatus array */
	if (!bootstrap)
		pgstat_bestart_final();

	/* close the transaction we started above */
	if (!bootstrap)
		CommitTransactionCommand();
}
```

## 동작 흐름

```text
 L730  InitProcessPhase2              PGPROC 를 ProcArray 에 넣는다. 이 순간부터 다른 backend 에 보인다
 L733  pgstat_beinit, L742 pgstat_bestart_initial    pg_stat_activity 에 첫 줄
 L750  SharedInvalBackendInit         카탈로그 무효화 메시지를 받을 자리
 L752  ProcSignalInit(취소 키)
 L760-L769  DEADLOCK / STATEMENT / LOCK / IDLE_* / TRANSACTION / CLIENT_CHECK 타이머 등록
 L807-L809  relcache, catcache, plancache 의 해시 테이블만 만든다 (아직 카탈로그 접근 없음)
 L812  EnablePortalManager            포털 해시 테이블
 L818  RelationCacheInitializePhase2  공유 카탈로그 (pg_database, pg_authid 등)
 L829  before_shmem_exit(ShutdownPostgres)

 L846-L847  StartTransactionCommand   여기서부터 L1236 까지 트랜잭션 하나
 L855  XactIsoLevel = READ COMMITTED  hot standby 에서 serializable 이면 실패하므로

 L896  일반 연결이면
 L900    [09] PerformAuthentication(MyProcPort)
 L901    InitializeSessionUserId(username)    pg_authid 조회, 로그인 권한
 L906    am_superuser = superuser()
 L937  예약 슬롯 검사                  (아래 그림)
 L955  walsender 면 REPLICATION 권한 확인
 L973  물리 복제 walsender 면 여기서 끝 (데이터베이스에 붙지 않는다)

 L1012  GetDatabaseTuple(in_dbname)    이름으로 pg_database 조회, 없으면 FATAL
 L1058  LockSharedObject(DatabaseRelationId, dboid, RowExclusiveLock)
 L1070  GetDatabaseTupleByOid(dboid)   락을 잡은 뒤 다시 조회
 L1074  사라졌거나 이름이 바뀌었으면 FATAL "It seems to have just been dropped or renamed."
 L1090  invalid 데이터베이스면 FATAL
 L1116  MyDatabaseId = dboid
 L1130  MyProc->databaseId = MyDatabaseId
 L1138  InvalidateCatalogSnapshot

 L1144  fullpath = GetDatabasePath     기본 테이블스페이스면 base/<dboid>
 L1148  access(fullpath) 실패면 FATAL, L1164 ValidatePgVersion
 L1176  RelationCacheInitializePhase3  이제 진짜 카탈로그 접근이 가능
 L1188  CheckMyDatabase                datallowconn, CONNECT 권한, datconnlimit, 로캘
 L1197  process_startup_options        시작 패킷의 options 와 GUC
 L1200  process_settings               ALTER ROLE / DATABASE ... SET 값
 L1212  InitializeSearchPath, L1215 클라이언트 인코딩, L1218 InitializeSession
 L1228  session_preload_libraries
 L1236  CommitTransactionCommand
```

락과 재확인의 순서가 이 함수의 핵심이다. `DROP DATABASE` 와 엇갈리는 경우를 그리면 왜 이 순서인지 보인다.

```text
 동시에 DROP DATABASE shop 이 도는 경우

 backend (InitPostgres)                         DROP DATABASE 쪽
 L1012  GetDatabaseTuple("shop") -> oid 16384
                                                pg_database 행 삭제, 커밋 준비
 L1058  LockSharedObject(16384, RowExclusive)   DROP 이 락을 쥐고 있으면 여기서 기다린다
                                                커밋, 락 해제
 L1070  GetDatabaseTupleByOid(16384) -> 없음
 L1077  FATAL "database "shop" does not exist"
        "It seems to have just been dropped or renamed."

 반대로 backend 가 먼저 락을 잡으면
   L1130 MyProc->databaseId 를 세운 뒤 커밋(L1236)으로 락을 놓는다
   DROP 은 락을 얻은 뒤 ProcArray 에서 이 backend 를 보게 된다 (주석 L1044-L1046)
   (주석 L1042-L1049: 락을 잡기 전에 ProcArray 에 자신을 알리면 교착이 된다)
```

```text
 예약 슬롯 검사 (L937-L952, 기본값 max_connections 100, superuser_reserved 3, reserved 0)

 조건: 일반 backend 이고, superuser 가 아니고, 예약 합 3 > 0 이고,
       freeProcs 에 3 개가 남아 있지 않음  (HaveNFreeProcs(3, &nfree), proc.c L782)

 이 backend 는 이미 PGPROC 하나를 쥐었다 ([04] InitProcess). 그래서 k 번째 연결이면 남은 수는 100 - k

 k     free   일반 역할 / superuser
 96    4      둘 다 통과
 97    3      둘 다 통과
 98    2      일반 역할 FATAL (nfree 2 < 3, "... reserved for roles with the SUPERUSER attribute") / superuser 통과
 100   0      일반 역할 FATAL / superuser 통과
 101   -      둘 다 [04] InitProcess 에서 이미 FATAL

 free = 이 backend 가 PGPROC 를 쥔 뒤 freeProcs 에 남은 수

 reserved_connections 를 쓰면 nfree 가 superuser_reserved 이상일 때
 pg_use_reserved_connections 권한으로 들어올 수 있다 (L947)
```

## 결과가 쓰이는 곳

```text
 ProcArray 의 내 PGPROC
      --> [MVCC 가시성과 스냅샷] GetSnapshotData 가 이 배열을 훑는다
      --> MyProc->databaseId 로 데이터베이스별 backend 를 센다 (CountOtherDBBackends)

 MyDatabaseId, DatabasePath
      --> 이후 모든 릴레이션 파일 경로와 카탈로그 조회의 기준

 세션 사용자, am_superuser
      --> 이후 권한 검사, GUC 설정 권한 (PGC_SU_BACKEND / PGC_BACKEND, L1249)

 relcache / catcache / 포털 관리자
      --> [쿼리 실행 파이프라인] 의 분석, 계획, Portal 이 모두 이것을 쓴다
```

## 다루지 않는 것

`CheckMyDatabase` 의 세부 검사(로캘, 연결 수 제한 `datconnlimit`), `InitializeSessionUserId` 의 역할 조회, relcache 초기화 단계별 내용, `process_settings` 의 `pg_db_role_setting` 조회, bootstrap 과 독립 실행 모드와 background worker 분기, `ShutdownPostgres` 의 정리 내용은 곁가지라 요약만 했다.
