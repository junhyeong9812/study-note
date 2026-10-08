# 프로세스 모델

상위: [PostgreSQL 아키텍처 지도](../../README.md)

PostgreSQL 서버는 **스레드가 아니라 프로세스의 묶음**이다. 맨 위에 postmaster 프로세스 하나가 있고, 나머지는 전부 postmaster 가 `fork` 한 자식이다. 연결마다 붙는 backend, 그리고 checkpointer, bgwriter, walwriter, autovacuum launcher 같은 백그라운드 프로세스가 모두 같은 자리 [`postmaster_child_launch`](../../flows/connection-startup/03_postmaster_child_launch/README.md)에서 태어난다. postmaster 는 공유 메모리를 만들기만 하고 스스로는 거의 만지지 않는다. 그래서 자식 하나가 죽어도 postmaster 는 살아남아 나머지 자식을 내리고 공유 메모리를 다시 만든다. 프로세스 사이의 신호선은 두 종류다. 자식이 postmaster 에게 부탁할 때는 공유 메모리의 플래그를 세우고 `SIGUSR1` 을 보낸다(PMSignal). 자식끼리 깨울 때는 상대 `PGPROC` 안의 latch 를 set 한다. 이 편은 **누가 누구를 띄우고, 어떤 상태에서 무엇이 살아 있고, 누가 누구를 깨우는가**를 한 자리에 모은다. 연결 하나가 backend 가 되는 과정은 [연결과 backend 기동](../../flows/connection-startup/README.md) 흐름이 따라간다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다. 기본 설정(`max_connections` 100 등)으로 계산한 숫자는 그렇다고 밝혔다.

## 전체 그림

```text
 누가 누구를 띄우는가 (기본 설정의 primary, 화살표 = fork)

 postmaster  (PostmasterMain, postmaster/postmaster.c L494)
   |  L1004  CreateSharedMemoryAndSemaphores   공유 메모리 생성
   |  L1380  UpdatePMState(PM_STARTUP)
   +--> L1383        io_worker x 3          io_method=worker, io_workers=3 이 기본
   +--> L1386-L1387  checkpointer           시작부터 끝까지
   +--> L1388-L1389  bgwriter               시작부터 끝까지
   +--> L1394        startup                WAL redo. 끝나면 exit(0)
   |      L2320  startup 이 exit(0) 하면 PM_RUN
   +--> L3305-L3306  walwriter              PM_RUN 에서만
   +--> L3313-L3317  autovacuum launcher    PM_RUN 에서만
   |      L3779-L3783  launcher 의 PMSignal 을 받아 postmaster 가 autovacuum worker 를 fork
   +--> L3379        bgworker               logical replication launcher 등
   +--> L1703        backend                연결마다 (ServerLoop -> BackendStartup)
   |      replication=true 로 붙은 연결은 walsender 가 된다
   +--> 설정했을 때만  archiver, syslogger, walsummarizer, walreceiver, slotsync worker

 모든 화살표는 같은 함수를 지난다
   StartChildProcess(type)                 postmaster.c L3942   백그라운드 프로세스
   BackendStartup                          postmaster.c L3518   backend
     -> postmaster_child_launch            launch_backend.c L229
          -> fork_process, 자식은 child_process_kinds[type].main_fn 으로
```

```text
 누가 누구를 깨우는가 (세 가지 신호선)

 1  자식 -> postmaster       PMSignal
      PMSignalState->PMSignalFlags[reason] = true; kill(PostmasterPid, SIGUSR1)
                                                     (storage/ipc/pmsignal.c L171-L173)
      postmaster 의 SIGUSR1 핸들러는 플래그만 세우고 자기 latch 를 set 한다
      ServerLoop 가 깨어 process_pm_pmsignal 을 부른다

 2  postmaster -> 자식       유닉스 신호
      SIGTERM  끝내라 (backend, autovacuum, bgworker ...)
      SIGINT   checkpointer 에게: shutdown checkpoint 를 써라   L3020
      SIGUSR2  checkpointer, archiver, walsender, io_worker 에게: 마지막 정리 후 끝내라
      SIGQUIT  즉시 끝내라 (immediate shutdown, 자식 crash)
      SIGHUP   설정 다시 읽어라

 3  자식 -> 자식             latch
      SetLatch(&GetPGProcByNumber(n)->procLatch)
      잠든 상대에게는 kill(owner_pid, SIGURG)   (storage/ipc/waiteventset.c L2035)
      상대는 WaitLatch(MyLatch, ...) 에서 깨어 공유 메모리의 요청을 읽는다
```

postmaster 가 공유 메모리를 거의 만지지 않는 이유는 파일 머리 주석에 있다. postmaster 는 `PGPROC` 배열의 일원이 아니라서 잠금 관리자에 참여할 수 없다. 공유 메모리를 많이 만지면 망가진 backend 와 함께 죽기 쉽다. 떨어져 있어야 backend crash 뒤에 공유 메모리를 리셋해 복구할 수 있다(postmaster.c L15-L23, L48-L51).

## 자식의 종류 - BackendType 과 child_process_kinds[]

모든 프로세스는 `MyBackendType` 하나로 자기 종류를 안다. 열거형은 세 무리로 나뉜다. 트랜잭션을 돌릴 수 있는 backend 류, `PGPROC` 은 있지만 데이터베이스에 붙지 않는 보조(auxiliary) 프로세스, 공유 메모리에 붙지 않는 logger 다.

`include` / `miscadmin.h` L331-L375 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/miscadmin.h#L331-L375))

```c
// miscadmin.h L331-L375
/*
 * MyBackendType indicates what kind of a backend this is.
 *
 * If you add entries, please also update the child_process_kinds array in
 * launch_backend.c.
 */
typedef enum BackendType
{
	B_INVALID = 0,

	/* Backends and other backend-like processes */
	B_BACKEND,
	B_DEAD_END_BACKEND,
	B_AUTOVAC_LAUNCHER,
	B_AUTOVAC_WORKER,
	B_BG_WORKER,
	B_WAL_SENDER,
	B_SLOTSYNC_WORKER,

	B_STANDALONE_BACKEND,

	/*
	 * Auxiliary processes. These have PGPROC entries, but they are not
	 * attached to any particular database, and cannot run transactions or
	 * even take heavyweight locks. There can be only one of each of these
	 * running at a time, except for IO workers.
	 *
	 * If you modify these, make sure to update NUM_AUXILIARY_PROCS and the
	 * glossary in the docs.
	 */
	B_ARCHIVER,
	B_BG_WRITER,
	B_CHECKPOINTER,
	B_IO_WORKER,
	B_STARTUP,
	B_WAL_RECEIVER,
	B_WAL_SUMMARIZER,
	B_WAL_WRITER,

	/*
	 * Logger is not connected to shared memory and does not have a PGPROC
	 * entry.
	 */
	B_LOGGER,
} BackendType;
```

postmaster 는 이 열거형을 인덱스로 하는 표에서 이름과 main 함수를 고른다. `shmem_attach` 가 false 인 것은 logger 뿐이다(standalone 은 postmaster 가 띄우지 않는다).

`postmaster` / `launch_backend.c` L169-L208 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/launch_backend.c#L169-L208))

```c
// postmaster/launch_backend.c L169-L208
/*
 * Information needed to launch different kinds of child processes.
 */
typedef struct
{
	const char *name;
	void		(*main_fn) (const void *startup_data, size_t startup_data_len);
	bool		shmem_attach;
} child_process_kind;

static child_process_kind child_process_kinds[] = {
	[B_INVALID] = {"invalid", NULL, false},

	[B_BACKEND] = {"backend", BackendMain, true},
	[B_DEAD_END_BACKEND] = {"dead-end backend", BackendMain, true},
	[B_AUTOVAC_LAUNCHER] = {"autovacuum launcher", AutoVacLauncherMain, true},
	[B_AUTOVAC_WORKER] = {"autovacuum worker", AutoVacWorkerMain, true},
	[B_BG_WORKER] = {"bgworker", BackgroundWorkerMain, true},

	/*
	 * WAL senders start their life as regular backend processes, and change
	 * their type after authenticating the client for replication.  We list it
	 * here for PostmasterChildName() but cannot launch them directly.
	 */
	[B_WAL_SENDER] = {"wal sender", NULL, true},
	[B_SLOTSYNC_WORKER] = {"slot sync worker", ReplSlotSyncWorkerMain, true},

	[B_STANDALONE_BACKEND] = {"standalone backend", NULL, false},

	[B_ARCHIVER] = {"archiver", PgArchiverMain, true},
	[B_BG_WRITER] = {"bgwriter", BackgroundWriterMain, true},
	[B_CHECKPOINTER] = {"checkpointer", CheckpointerMain, true},
	[B_IO_WORKER] = {"io_worker", IoWorkerMain, true},
	[B_STARTUP] = {"startup", StartupProcessMain, true},
	[B_WAL_RECEIVER] = {"wal_receiver", WalReceiverMain, true},
	[B_WAL_SUMMARIZER] = {"wal_summarizer", WalSummarizerMain, true},
	[B_WAL_WRITER] = {"wal_writer", WalWriterMain, true},

	[B_LOGGER] = {"syslogger", SysLoggerMain, false},
};
```

```text
 종류별 자리 (기본 설정으로 계산)

 BackendType          PMChild pool             PGPROC list                 언제 뜨나, 비고
 B_BACKEND            220                      freeProcs 100               연결마다. 풀 = 2*(100+10), walsender 와 같이 쓴다
 B_WAL_SENDER         (B_BACKEND pool)         walsenderFreeProcs 10       replication 연결
 B_DEAD_END_BACKEND   -                        -                           연결을 못 받을 때. 풀 없이 AllocDeadEndChild
                                                                           InitProcess 전에 끝나 PGPROC 도 없다
 B_AUTOVAC_LAUNCHER   1                        autovacFreeProcs 16+2       PM_RUN
 B_AUTOVAC_WORKER     16                       autovacFreeProcs            launcher 가 요청할 때마다
 B_SLOTSYNC_WORKER    1                        autovacFreeProcs            PM_HOT_STANDBY
 B_BG_WORKER          8                        bgworkerFreeProcs 8         등록된 bgworker
 B_ARCHIVER           1                        AuxiliaryProcs              archive_mode 일 때
 B_BG_WRITER          1                        AuxiliaryProcs              PM_STARTUP 부터
 B_CHECKPOINTER       1                        AuxiliaryProcs              PM_STARTUP 부터
 B_IO_WORKER          32 (MAX_IO_WORKERS)      AuxiliaryProcs              io_method=worker (기본 3 개)
 B_STARTUP            1                        AuxiliaryProcs              PM_STARTUP, 복구
 B_WAL_RECEIVER       1                        AuxiliaryProcs              standby
 B_WAL_SUMMARIZER     1                        AuxiliaryProcs              summarize_wal
 B_WAL_WRITER         1                        AuxiliaryProcs              PM_RUN
 B_LOGGER             1                        -                           logging_collector. 공유 메모리에 붙지 않는다

 PMChild 풀 크기      postmaster/pmchild.c L100-L119
 PGPROC 목록          storage/lmgr/proc.c L328-L351 (InitProcGlobal), 고르는 곳 L416-L423 (InitProcess)
 AuxiliaryProcs       NUM_AUXILIARY_PROCS = 6 + MAX_IO_WORKERS = 38   (include/storage/proc.h L460-L461)
                      6 인 이유: walwriter 는 startup 이 끝난 뒤에만 뜨므로 둘이 한 칸을 나눈다
                      (proc.h L451-L458 주석)
```

PMChild 풀과 `PGPROC` 목록은 서로 다른 상한이다. postmaster 는 공유 메모리의 `PGPROC` 를 보지 않으므로 자기 쪽 표(`PMChild`)로 자식 수를 센다. backend 풀을 `PGPROC` 수의 두 배로 잡는 이유와, 진짜 상한이 `InitProcess` 의 `freeProcs` 라는 점은 [연결과 backend 기동](../../flows/connection-startup/README.md)의 "연결 수를 거르는 세 자리"에 있다.

## postmaster 상태 기계 - PMState

postmaster 의 상태는 열세 값의 `pmState` 하나다. 기동, 복구, 정상 운영, 종료, crash 뒤 재초기화가 모두 이 변수 위에서 일어난다. 주석이 규칙 둘을 적어 두었다. 일반 backend 는 `PM_RUN` 과 `PM_HOT_STANDBY` 에서만 띄우고, 그 밖의 상태에서 온 연결은 오류 메시지만 보내고 죽는 dead-end 자식이 받는다. 그리고 이 변수는 "왜" 종료 쪽 상태에 들어왔는지 구별하지 않으므로 `Shutdown` 과 `FatalError` 를 같이 봐야 한다.

`postmaster` / `postmaster.c` L335-L352 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L335-L352))

```c
// postmaster/postmaster.c L335-L352
typedef enum
{
	PM_INIT,					/* postmaster starting */
	PM_STARTUP,					/* waiting for startup subprocess */
	PM_RECOVERY,				/* in archive recovery mode */
	PM_HOT_STANDBY,				/* in hot standby mode */
	PM_RUN,						/* normal "database is alive" state */
	PM_STOP_BACKENDS,			/* need to stop remaining backends */
	PM_WAIT_BACKENDS,			/* waiting for live backends to exit */
	PM_WAIT_XLOG_SHUTDOWN,		/* waiting for checkpointer to do shutdown
								 * ckpt */
	PM_WAIT_XLOG_ARCHIVAL,		/* waiting for archiver and walsenders to
								 * finish */
	PM_WAIT_IO_WORKERS,			/* waiting for io workers to exit */
	PM_WAIT_CHECKPOINTER,		/* waiting for checkpointer to shut down */
	PM_WAIT_DEAD_END,			/* waiting for dead-end children to exit */
	PM_NO_CHILDREN,				/* all important children have exited */
} PMState;
```

```text
 상태 전이 (줄은 모두 postmaster.c, UpdatePMState 를 부르는 줄)

 PM_INIT
   |  PostmasterMain                                         L1380
   v
 PM_STARTUP  ---------------------------------------------+  checkpointer, bgwriter, startup 이 돈다
   |  PMSIGNAL_RECOVERY_STARTED (startup 이 보냄)  L3714    |
   v                                                       |
 PM_RECOVERY                                               |  아카이브 복구, standby
   |  PMSIGNAL_BEGIN_HOT_STANDBY                   L3735    |
   v                                                       |
 PM_HOT_STANDBY  (읽기 전용 연결을 받는다)                 |
   |  startup 이 exit(0)                           L2320    |  crash 복구만이면 바로 여기로
   v                                                       |
 PM_RUN  +-------------------------------------------------+
   |  smart: 연결을 막고(connsAllowed=false L2127) backend 가 0 이 되면   L2877
   |  fast:  바로                                            L2173
   v
 PM_STOP_BACKENDS   SIGTERM 을 대상 무리에 보낸다           L2980
   |                                                       L2982
   v
 PM_WAIT_BACKENDS   backend, autovacuum, bgworker, walwriter, bgwriter ... 가 0 이 될 때까지
   |  0 이 되면 checkpointer 에 SIGINT                       L3020-L3021
   v
 PM_WAIT_XLOG_SHUTDOWN   checkpointer 가 shutdown checkpoint 를 쓴다
   |  PMSIGNAL_XLOG_IS_SHUTDOWN (checkpointer.c L609)
   |  archiver, walsender 에 SIGUSR2                         L3806, L3812
   v                                                       L3814
 PM_WAIT_XLOG_ARCHIVAL   archiver 와 walsender 가 마지막 WAL 을 내보내고 끝낼 때까지
   |  io_worker 에 SIGUSR2                                   L3065-L3066
   v
 PM_WAIT_IO_WORKERS
   |  checkpointer 에 SIGUSR2                                L3078, L3087
   v
 PM_WAIT_CHECKPOINTER
   |  checkpointer 가 끝나면 (process_pm_child_exit)         L2376
   v
 PM_WAIT_DEAD_END   dead-end 자식이 다 빠질 때까지 연결을 아예 받지 않는다
   |                                                       L3123
   v
 PM_NO_CHILDREN     logger 만 남았다
   |  Shutdown 이면 ExitPostmaster                           L3139-L3155
   |  FatalError 면 공유 메모리를 다시 만들고 PM_STARTUP     L3184-L3204
```

```text
 crash 경로 - backend 하나가 비정상 종료하면

 SIGCHLD -> process_pm_child_exit -> CleanupBackend -> HandleChildCrash   L2772
   -> HandleFatalError(PMQUIT_FOR_CRASH)                    L2686
        SetQuitSignalReason, 모든 자식에 SIGQUIT             L2693, L2706
          (send_abort_for_crash 면 SIGABRT, L2695-L2698)
        FatalError = true                                    L2708
        PM_WAIT_BACKENDS 로                                   L2729
 -> 대상 무리가 0 (FatalError 라 checkpointer, archiver, io_worker, walsender 까지)   L2925-L2930
 -> PM_WAIT_DEAD_END -> PM_NO_CHILDREN
 -> shmem_exit, CreateSharedMemoryAndSemaphores, startup 을 다시 띄운다   L3184-L3209
    restart_after_crash 가 꺼져 있으면 대신 종료한다            L3172-L3177
```

기동 쪽 화살표는 startup 의 종료 하나로 모인다. crash 복구만 하면 `PM_STARTUP` 에서, hot standby 없이 아카이브 복구를 하면 `PM_RECOVERY` 에서, hot standby 면 `PM_HOT_STANDBY` 에서 startup 이 exit(0) 하고, 어느 쪽이든 L2320 에서 `PM_RUN` 이 된다. `PostmasterStateMachine` 은 신호 셋(종료 요청, 자식 종료, PMSignal)을 처리한 뒤마다 불린다. 종료 쪽 상태만 앞으로 민다. 기동 쪽 전이(`PM_STARTUP` 에서 `PM_RUN` 까지)는 위 그림처럼 `process_pm_child_exit` 와 `process_pm_pmsignal` 안에 있다. 아래는 `PM_STOP_BACKENDS` 와 `PM_WAIT_BACKENDS` 를 처리하는 앞부분이다.

`postmaster` / `postmaster.c` L2864-L3022 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L2864-L3022))

```c
// postmaster/postmaster.c L2864-L3022
static void
PostmasterStateMachine(void)
{
	/* If we're doing a smart shutdown, try to advance that state. */
// ... (L2868-L2880 생략: smart shutdown 이면 backend 가 0 일 때 PM_STOP_BACKENDS 로)
	/*
	 * In the PM_WAIT_BACKENDS state, wait for all the regular backends and
	 * processes like autovacuum and background workers that are comparable to
	 * backends to exit.
	 *
	 * PM_STOP_BACKENDS is a transient state that means the same as
	 * PM_WAIT_BACKENDS, but we signal the processes first, before waiting for
	 * them.  Treating it as a distinct pmState allows us to share this code
	 * across multiple shutdown code paths.
	 */
	if (pmState == PM_STOP_BACKENDS || pmState == PM_WAIT_BACKENDS)
	{
		BackendTypeMask targetMask = BTYPE_MASK_NONE;

		/*
		 * PM_WAIT_BACKENDS state ends when we have no regular backends, no
		 * autovac launcher or workers, and no bgworkers (including
		 * unconnected ones).
		 */
		targetMask = btmask_add(targetMask,
								B_BACKEND,
								B_AUTOVAC_LAUNCHER,
								B_AUTOVAC_WORKER,
								B_BG_WORKER);

		/*
		 * No walwriter, bgwriter, slot sync worker, or WAL summarizer either.
		 */
		targetMask = btmask_add(targetMask,
								B_WAL_WRITER,
								B_BG_WRITER,
								B_SLOTSYNC_WORKER,
								B_WAL_SUMMARIZER);

		/* If we're in recovery, also stop startup and walreceiver procs */
		targetMask = btmask_add(targetMask,
								B_STARTUP,
								B_WAL_RECEIVER);

		/*
		 * If we are doing crash recovery or an immediate shutdown then we
		 * expect archiver, checkpointer, io workers and walsender to exit as
		 * well, otherwise not.
		 */
		if (FatalError || Shutdown >= ImmediateShutdown)
			targetMask = btmask_add(targetMask,
									B_CHECKPOINTER,
									B_ARCHIVER,
									B_IO_WORKER,
									B_WAL_SENDER);
// ... (L2931-L2968 생략: USE_ASSERT_CHECKING 블록: 모든 종류가 targetMask 나 remainMask 에 들었는지 검사)

		/* If we had not yet signaled the processes to exit, do so now */
		if (pmState == PM_STOP_BACKENDS)
		{
			/*
			 * Forget any pending requests for background workers, since we're
			 * no longer willing to launch any new workers.  (If additional
			 * requests arrive, BackgroundWorkerStateChange will reject them.)
			 */
			ForgetUnstartedBackgroundWorkers();

			SignalChildren(SIGTERM, targetMask);

			UpdatePMState(PM_WAIT_BACKENDS);
		}

		/* Are any of the target processes still running? */
		if (CountChildren(targetMask) == 0)
		{
			if (Shutdown >= ImmediateShutdown || FatalError)
			{
// ... (L2990-L2995 생략: 주석)
				UpdatePMState(PM_WAIT_DEAD_END);
				ConfigurePostmasterWaitSet(false);
				SignalChildren(SIGQUIT, btmask(B_DEAD_END_BACKEND));

// ... (L3000-L3004 생략: 주석)
			}
			else
			{
// ... (L3008-L3012 생략: 주석: 정상 종료면 이제 shutdown checkpoint 차례)
				Assert(Shutdown > NoShutdown);
				/* Start the checkpointer if not running */
				if (CheckpointerPMChild == NULL)
					CheckpointerPMChild = StartChildProcess(B_CHECKPOINTER);
				/* And tell it to write the shutdown checkpoint */
				if (CheckpointerPMChild != NULL)
				{
					signal_child(CheckpointerPMChild, SIGINT);
					UpdatePMState(PM_WAIT_XLOG_SHUTDOWN);
				}
```

## 누가 언제 띄우는가 - LaunchMissingBackgroundProcesses

백그라운드 프로세스를 띄우는 판단은 한 함수에 모여 있다. `ServerLoop` 가 한 바퀴 돌 때마다(L1718) 부르고, 상태와 설정에 맞는데 없는 것만 띄운다. 그래서 bgwriter 가 정상 종료(exit 0)하면 다음 바퀴에 새로 뜬다. 0 이 아닌 종료는 crash 로 다룬다(L2343-L2355).

`postmaster` / `postmaster.c` L3266-L3320 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L3266-L3320))

```c
// postmaster/postmaster.c L3266-L3320
static void
LaunchMissingBackgroundProcesses(void)
{
	/* Syslogger is active in all states */
	if (SysLoggerPMChild == NULL && Logging_collector)
		StartSysLogger();

// ... (L3273-L3280 생략: 주석: 설정이 바뀌었거나 이전 시작이 실패했을 수 있다)
	maybe_adjust_io_workers();

// ... (L3283-L3291 생략: 주석: shutdown checkpoint 용 재기동은 PostmasterStateMachine 몫)
	if (pmState == PM_RUN || pmState == PM_RECOVERY ||
		pmState == PM_HOT_STANDBY || pmState == PM_STARTUP)
	{
		if (CheckpointerPMChild == NULL)
			CheckpointerPMChild = StartChildProcess(B_CHECKPOINTER);
		if (BgWriterPMChild == NULL)
			BgWriterPMChild = StartChildProcess(B_BG_WRITER);
	}
// ... (L3300-L3304 생략: 주석)
	if (WalWriterPMChild == NULL && pmState == PM_RUN)
		WalWriterPMChild = StartChildProcess(B_WAL_WRITER);

// ... (L3308-L3312 생략: 주석: binary upgrade 에서는 autovacuum 을 띄우지 않는다)
	if (!IsBinaryUpgrade && AutoVacLauncherPMChild == NULL &&
		(AutoVacuumingActive() || start_autovac_launcher) &&
		pmState == PM_RUN)
	{
		AutoVacLauncherPMChild = StartChildProcess(B_AUTOVAC_LAUNCHER);
		if (AutoVacLauncherPMChild != NULL)
			start_autovac_launcher = false; /* signal processed */
	}
```

```text
 상태별로 살아 있는 백그라운드 프로세스 (LaunchMissingBackgroundProcesses 의 조건)

 process               STARTUP  RECOVERY  HOT_STANDBY  RUN   postmaster.c   조건
 syslogger             o        o         o            o     L3270          logging_collector
 io_worker             o        o         o            o     L3281          io_method=worker
 checkpointer          o        o         o            o     L3292-L3298
 bgwriter              o        o         o            o     L3292-L3298
 walwriter             -        -         -            o     L3305
 autovacuum launcher   -        -         -            o     L3313-L3315    autovacuum (기본 on)
 archiver              -        always    always       o     L3326-L3330    archive_mode
 slotsync worker       -        -         o            -     L3340-L3343    sync_replication_slots
 walreceiver           o        o         o            -     L3358-L3364    startup 이 요청할 때
 walsummarizer         -        -         o            o     L3372-L3375    summarize_wal
 bgworker              *        *         *            *     L3378-L3379    * 워커마다 bgw_start_time 이 정한다

 기본 설정이면 syslogger, archiver, walsummarizer, walreceiver, slotsync 는 뜨지 않는다
 (logging_collector, summarize_wal 기본 false, archive_mode 기본 off)
```

## 신호선 1 - postmaster 의 신호 처리

postmaster 의 신호 핸들러는 **일을 하지 않는다.** 플래그 하나를 세우고 자기 latch 를 set 할 뿐이다. 실제 처리는 `ServerLoop` 의 `WaitEventSetWait` 가 깨어난 뒤 메인 루프에서 한다(`ServerLoop` 본문은 [ServerLoop](../../flows/connection-startup/01_ServerLoop/README.md)). 핸들러 등록은 `PostmasterMain` L551-L559 다.

`postmaster` / `postmaster.c` L1974-L1979 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L1974-L1979))

```c
// postmaster/postmaster.c L1974-L1979
static void
handle_pm_pmsignal_signal(SIGNAL_ARGS)
{
	pending_pm_pmsignal = true;
	SetLatch(MyLatch);
}
```

`postmaster` / `postmaster.c` L2222-L2227 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L2222-L2227))

```c
// postmaster/postmaster.c L2222-L2227
static void
handle_pm_child_exit_signal(SIGNAL_ARGS)
{
	pending_pm_child_exit = true;
	SetLatch(MyLatch);
}
```

```text
 postmaster 가 받는 신호

 signal    handler                             flag                           process_pm_*
 SIGHUP    handle_pm_reload_request_signal     pending_pm_reload_request      _reload_request
 SIGTERM   handle_pm_shutdown_request_signal   pending_pm_shutdown_request    _shutdown_request   smart
 SIGINT    handle_pm_shutdown_request_signal   + pending_pm_fast_...          _shutdown_request   fast
 SIGQUIT   handle_pm_shutdown_request_signal   + pending_pm_immediate_...     _shutdown_request   immediate
 SIGUSR1   handle_pm_pmsignal_signal           pending_pm_pmsignal            _pmsignal
 SIGCHLD   handle_pm_child_exit_signal         pending_pm_child_exit          _child_exit

 ServerLoop 는 이벤트마다 네 플래그를 순서대로 확인한다   L1689-L1696
   종료 -> 설정 -> 자식 종료 -> PMSignal
```

## 신호선 2 - PMSignal (자식이 postmaster 에게)

자식이 postmaster 에게 "무엇을 해 달라"고 할 때는 이유별 플래그를 공유 메모리에 세우고 `SIGUSR1` 하나만 보낸다. 신호 하나에 이유가 여럿 겹쳐도 플래그로 구별된다. 같은 이유가 빠르게 두 번 오면 한 번으로 보일 수 있는데, 지금 쓰임에는 괜찮다고 주석이 적었다.

`include` / `storage` / `pmsignal.h` L27-L45 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/pmsignal.h#L27-L45))

```c
// storage/pmsignal.h L27-L45
/*
 * Reasons for signaling the postmaster.  We can cope with simultaneous
 * signals for different reasons.  If the same reason is signaled multiple
 * times in quick succession, however, the postmaster is likely to observe
 * only one notification of it.  This is okay for the present uses.
 */
typedef enum
{
	PMSIGNAL_RECOVERY_STARTED,	/* recovery has started */
	PMSIGNAL_RECOVERY_CONSISTENT,	/* recovery has reached consistent state */
	PMSIGNAL_BEGIN_HOT_STANDBY, /* begin Hot Standby */
	PMSIGNAL_ROTATE_LOGFILE,	/* send SIGUSR1 to syslogger to rotate logfile */
	PMSIGNAL_START_AUTOVAC_LAUNCHER,	/* start an autovacuum launcher */
	PMSIGNAL_START_AUTOVAC_WORKER,	/* start an autovacuum worker */
	PMSIGNAL_BACKGROUND_WORKER_CHANGE,	/* background worker state change */
	PMSIGNAL_START_WALRECEIVER, /* start a walreceiver */
	PMSIGNAL_ADVANCE_STATE_MACHINE, /* advance postmaster's state machine */
	PMSIGNAL_XLOG_IS_SHUTDOWN,	/* ShutdownXLOG() completed */
} PMSignalReason;
```

`storage` / `ipc` / `pmsignal.c` L164-L174 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/pmsignal.c#L164-L174))

```c
// storage/ipc/pmsignal.c L164-L174
void
SendPostmasterSignal(PMSignalReason reason)
{
	/* If called in a standalone backend, do nothing */
	if (!IsUnderPostmaster)
		return;
	/* Atomically set the proper flag */
	PMSignalState->PMSignalFlags[reason] = true;
	/* Send signal to postmaster */
	kill(PostmasterPid, SIGUSR1);
}
```

```text
 PMSignal 을 보내는 곳 -> postmaster 가 하는 일

 PMSIGNAL_*               sender        function, file line                         postmaster 가 하는 일
 RECOVERY_STARTED         startup       PerformWalRecovery  xlogrecovery.c L1719    PM_RECOVERY 로 (L3714)
 RECOVERY_CONSISTENT      startup       CheckRecoveryConsistency  L2276              reachedConsistency = true
 BEGIN_HOT_STANDBY        startup       CheckRecoveryConsistency  L2298              PM_HOT_STANDBY 로 (L3735)
 START_WALRECEIVER        startup       RequestXLogStreaming  walreceiverfuncs.c L322  다음 바퀴에 walreceiver fork
 START_AUTOVAC_LAUNCHER   backend       GetNewTransactionId  varsup.c L145          wraparound 가 가까우면. 플래그만 세운다
 START_AUTOVAC_WORKER     av launcher   do_start_worker  autovacuum.c L1271         StartAutovacuumWorker (L3783)
 BACKGROUND_WORKER_CHANGE backend       RegisterDynamicBackgroundWorker  bgworker.c L1125   워커 목록 갱신
                                        TerminateBackgroundWorker  bgworker.c L1316
 ADVANCE_STATE_MACHINE    walsender     InitWalSender  walsender.c L315             PostmasterStateMachine
 XLOG_IS_SHUTDOWN         checkpointer  CheckpointerMain  checkpointer.c L609       PM_WAIT_XLOG_ARCHIVAL 로 (L3814)
 ROTATE_LOGFILE           backend       pg_rotate_logfile  signalfuncs.c L317       syslogger 에 SIGUSR1
```

autovacuum worker 는 launcher 가 직접 띄우지 않는다. launcher 가 공유 메모리에 "다음 워커는 이 데이터베이스"라고 적고 `PMSIGNAL_START_AUTOVAC_WORKER` 를 보내면, postmaster 가 `StartAutovacuumWorker` 로 fork 한다. 모든 fork 는 postmaster 의 일이다.

## 신호선 3 - latch (자식이 자식에게)

latch 는 "깨어나서 확인해 봐"라는 한 비트짜리 신호다. 모든 `PGPROC` 에 하나씩 있다(`procLatch`, `InitProcGlobal` 이 공유 latch 로 만든다). 깨우는 쪽은 상대의 latch 를 set 하고, 상대가 자고 있으면 `SIGURG` 를 보낸다. 무엇을 할지는 latch 가 아니라 공유 메모리의 다른 필드(요청 플래그, LSN 등)가 알린다.

`include` / `storage` / `latch.h` L113-L122 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/include/storage/latch.h#L113-L122))

```c
// storage/latch.h L113-L122
typedef struct Latch
{
	sig_atomic_t is_set;
	sig_atomic_t maybe_sleeping;
	bool		is_shared;
	int			owner_pid;
#ifdef WIN32
	HANDLE		event;
#endif
} Latch;
```

`storage` / `ipc` / `latch.c` L289-L346 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/ipc/latch.c#L289-L346))

```c
// storage/ipc/latch.c L289-L346
void
SetLatch(Latch *latch)
{
#ifndef WIN32
	pid_t		owner_pid;
#else
	HANDLE		handle;
#endif

	/*
	 * The memory barrier has to be placed here to ensure that any flag
	 * variables possibly changed by this process have been flushed to main
	 * memory, before we check/set is_set.
	 */
	pg_memory_barrier();

	/* Quick exit if already set */
	if (latch->is_set)
		return;

	latch->is_set = true;

	pg_memory_barrier();
	if (!latch->maybe_sleeping)
		return;

#ifndef WIN32

// ... (L317-L338 생략: 주석: owner_pid 를 한 번만 읽는 이유와 경합 설명)
	owner_pid = latch->owner_pid;
	if (owner_pid == 0)
		return;
	else if (owner_pid == MyProcPid)
		WakeupMyProc();
	else
		WakeupOtherProc(owner_pid);

```

리눅스 빌드는 `epoll` 과 `signalfd` 로 기다리므로(waiteventset.c L103-L110), 다른 프로세스가 보낸 `SIGURG` 가 `WaitLatch` 의 `epoll_wait` 를 깨운다.

```text
 backend 가 백그라운드 프로세스를 깨우는 자리 (모두 SetLatch(&...->procLatch))

 caller                  file line                               wakes          깨는 자리, 조건
 XLogSetAsyncXactLSN     access/transam/xlog.c L2657             walwriter      WalWriterMain WaitLatch L268
                                                                                비동기 커밋이 WAL 을 남겼을 때
 RequestCheckpoint       postmaster/checkpointer.c L1070         checkpointer   CheckpointerMain WaitLatch L580
 ForwardSyncRequest      postmaster/checkpointer.c L1197         checkpointer   fsync 요청 큐가 절반 넘게 찼을 때 (L1184-L1186)
 StrategyGetBuffer       storage/buffer/freelist.c L242          bgwriter       BackgroundWriterMain WaitLatch L307
                                                                                bgwriter 가 잠들며 bgwprocno 를 남겼을 때만
 PgArchWakeup            postmaster/pgarch.c L292                archiver       pgarch_MainLoop WaitLatch L359
                                                                                XLogArchiveNotify (xlogarchive.c L485) 뒤
 WalSndWakeup            replication/walsender.c L3748           walsender      조건 변수 wal_flush_cv, wal_replay_cv
                                                                                XLogFlush 가 WalSndWakeupProcessRequests 로 (xlog.c L2913)
 RequestXLogStreaming    replication/walreceiverfuncs.c L324     walreceiver    떠 있으면 latch, 아니면 PMSignal (L322)

 backend 끼리
 ProcWakeup              storage/lmgr/proc.c L1761               lock waiter    ProcSleep 에서 자는 heavyweight lock 대기자
 ProcSendSignal          storage/lmgr/proc.c L2024               pin waiter     cleanup lock 대기자 (bufmgr.c L3269) 등
 SyncRepWakeQueue        replication/syncrep.c L948              backend        동기 복제를 기다리는 backend. walsender 가 부른다
 ConditionVariableSignal storage/lmgr/condition_variable.c L271  CV sleeper     조건 변수에서 자는 프로세스

 walwriterProc, checkpointerProc 번호는 PROC_HDR 에 있다 (include/storage/proc.h L422-L423)
```

latch 와 별개로 backend 에게 "인터럽트를 처리하라"고 할 때는 `SendProcSignal`(storage/ipc/procsignal.c L293)이 이유 플래그를 세우고 `SIGUSR1` 을 보낸다. sinval catchup, `LISTEN/NOTIFY`, 병렬 쿼리 메시지, 복구 충돌, 전역 barrier 가 이 길을 쓴다(include/storage/procsignal.h L30-L52). PMSignal 과 모양이 같지만 받는 이가 postmaster 가 아니라 특정 backend 다.

## db-engine 에서는

db-engine 에는 프로세스가 하나뿐이고 감독자도 없다. 연결의 상한과 실행 단위는 `ConnectionPool` 하나가 맡는다. PostgreSQL 이 프로세스를 나눠 얻는 것, 즉 한 연결의 crash 가 다른 연결을 죽이지 않고 감독자가 공유 상태를 리셋하는 구조는 db-engine 에 해당하는 자리가 없다.

```text
 같은 문제(동시에 여러 일을 돌리기), 두 구현 (위 PostgreSQL / 아래 db-engine)

 실행 단위
   PostgreSQL  연결 1개 = OS 프로세스 1개 (fork). 백그라운드 일도 각자 프로세스
   db-engine   JVM 프로세스 1개 안의 Executors.newFixedThreadPool(capacity) 스레드

 상한
   PostgreSQL  postmaster 의 PMChild 풀 220 -> InitProcess 의 freeProcs 100
   db-engine   openSession 의 require(sessions.size < capacity), 기본 16

 감독자
   PostgreSQL  postmaster. SIGCHLD 로 자식의 죽음을 알고 PMState 를 진행한다
               crash 면 모두 SIGQUIT -> 공유 메모리 재생성 -> startup 재기동
   db-engine   없음. 작업 예외는 Future 안에 갇히고 세션은 그대로 남는다

 백그라운드 일
   PostgreSQL  checkpointer, bgwriter, walwriter, autovacuum 이 latch 로 깨어 일한다
   db-engine   없음. flush, checkpoint, sync 는 부른 스레드가 그 자리에서 한다

 서로 깨우기
   PostgreSQL  SetLatch -> SIGURG, PMSignal -> SIGUSR1
   db-engine   같은 힙을 쓰는 스레드라 신호가 필요 없다. Future.get() 으로 기다린다
```

db-engine 13-01 은 `newFixedThreadPool` 의 큐가 무제한이라 세션이 몰리면 작업이 조용히 쌓인다고 적었다. PostgreSQL 은 큐 대신 프로세스를 만들고, 자리가 없으면 연결 자체를 거절한다. 13-01 이 "세션이 닫힐 때 열린 트랜잭션은 commit인가 abort인가?" 에 "답은 abort다." 라고 적은 자리는 PostgreSQL 에서 backend 가 끝날 때 `proc_exit` 가 부르는 종료 콜백 `ShutdownPostgres` 의 `AbortOutOfAnyTransaction` 이 맡는다(utils/init/postinit.c L829, L1346). 챕터: [13-01-connection-pool](../../../../../project/db-engine/13-01-connection-pool/).

## 어디에서 쓰이는가

```text
 [연결과 backend 기동]   ServerLoop -> BackendStartup -> postmaster_child_launch -> BackendMain
                         pmState 가 PM_RUN 이나 PM_HOT_STANDBY 가 아니면 canAcceptConnections 가 거절
 [체크포인트]            checkpointer 가 latch 에서 깨어 CreateCheckPoint. 종료 때 SIGINT 로 shutdown checkpoint
 [WAL redo (복구)]       startup 프로세스. PMSignal 로 PM_RECOVERY, PM_HOT_STANDBY 를 알린다
 [버퍼 관리]             StrategyGetBuffer 가 bgwriter 의 latch 를 set 한다
 [heavyweight lock]      ProcSleep 에서 자고 ProcWakeup 의 SetLatch 로 깬다
 [스트리밍 복제]         walsender 는 backend 로 태어나 replication 연결이 된다. 종료 때 SIGUSR2
 [vacuum]                autovacuum launcher 가 PMSignal 로 worker 를 요청한다
```

흐름 문서: [연결과 backend 기동](../../flows/connection-startup/README.md), [버퍼 관리](../../flows/buffer-manager/README.md), [heavyweight lock](../../flows/heavyweight-lock/README.md), [체크포인트](../../flows/checkpoint/README.md), [WAL redo (복구)](../../flows/wal-redo/README.md), [스트리밍 복제](../../flows/streaming-replication/README.md), [vacuum](../../flows/vacuum/README.md). 프로세스들이 함께 쓰는 자리는 [공유 메모리](../shared-memory/README.md)에 있다.

## 다루지 않는 것

`EXEC_BACKEND`(Windows) 의 `internal_forkexec` 와 `SubPostmasterMain`, 보조 프로세스 공통 초기화(`AuxiliaryProcessMainCommon`, `InitAuxiliaryProcess`), 각 백그라운드 프로세스 본체의 일(bgwriter 의 `BgBufferSync`, walwriter 의 `XLogBackgroundFlush`, archiver 의 `pgarch_ArchiverCopyLoop`), bgworker 등록과 재시작 규칙(`bgw_restart_time`, `maybe_start_bgworkers` 내부), io_worker 수 조절(`maybe_adjust_io_workers`) 세부, 병렬 쿼리 워커, `postmaster.pid` 의 상태 줄, systemd 알림, SIGKILL 타임아웃(`SIGKILL_CHILDREN_AFTER_SECS`), postmaster 사망 감지(`WL_EXIT_ON_PM_DEATH`, `PostmasterIsAlive`)는 같은 뼈대의 곁가지라 요약만 했다.
