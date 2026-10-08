# postmaster_child_launch

상위: [연결과 backend 기동](../README.md)

**fork 가 일어나는 단 한 자리다.** 일반 빌드에서는 `fork_process` 한 번으로 갈라지고, 자식은 postmaster 의 소켓과 대기 집합을 닫은 뒤 **종류별 표 `child_process_kinds[]` 에서 고른 main 함수로 들어가 돌아오지 않는다.** backend 뿐 아니라 checkpointer, walwriter, autovacuum 같은 모든 postmaster 자식이 이 함수로 태어난다.

## 위치

`postmaster` / `launch_backend.c` L229-L295 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/launch_backend.c#L229-L295))

## 실제 코드

`postmaster` / `launch_backend.c` L229-L295 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/launch_backend.c#L229-L295))

```c
// postmaster/launch_backend.c L229-L295
postmaster_child_launch(BackendType child_type, int child_slot,
						void *startup_data, size_t startup_data_len,
						ClientSocket *client_sock)
{
	pid_t		pid;

	Assert(IsPostmasterEnvironment && !IsUnderPostmaster);

	/* Capture time Postmaster initiates process creation for logging */
	if (IsExternalConnectionBackend(child_type))
		((BackendStartupData *) startup_data)->fork_started = GetCurrentTimestamp();

#ifdef EXEC_BACKEND
	pid = internal_forkexec(child_process_kinds[child_type].name, child_slot,
							startup_data, startup_data_len, client_sock);
	/* the child process will arrive in SubPostmasterMain */
#else							/* !EXEC_BACKEND */
	pid = fork_process();
	if (pid == 0)				/* child */
	{
		/* Capture and transfer timings that may be needed for logging */
		if (IsExternalConnectionBackend(child_type))
		{
			conn_timing.socket_create =
				((BackendStartupData *) startup_data)->socket_created;
			conn_timing.fork_start =
				((BackendStartupData *) startup_data)->fork_started;
			conn_timing.fork_end = GetCurrentTimestamp();
		}

		/* Close the postmaster's sockets */
		ClosePostmasterPorts(child_type == B_LOGGER);

		/* Detangle from postmaster */
		InitPostmasterChild();

		/* Detach shared memory if not needed. */
		if (!child_process_kinds[child_type].shmem_attach)
		{
			dsm_detach_all();
			PGSharedMemoryDetach();
		}

		/*
		 * Enter the Main function with TopMemoryContext.  The startup data is
		 * allocated in PostmasterContext, so we cannot release it here yet.
		 * The Main function will do it after it's done handling the startup
		 * data.
		 */
		MemoryContextSwitchTo(TopMemoryContext);

		MyPMChildSlot = child_slot;
		if (client_sock)
		{
			MyClientSocket = palloc(sizeof(ClientSocket));
			memcpy(MyClientSocket, client_sock, sizeof(ClientSocket));
		}

		/*
		 * Run the appropriate Main function
		 */
		child_process_kinds[child_type].main_fn(startup_data, startup_data_len);
		pg_unreachable();		/* main_fn never returns */
	}
#endif							/* EXEC_BACKEND */
	return pid;
}
```

자식 종류마다 들어갈 함수와 공유 메모리에 붙을지를 적은 표다. 연결 backend 와 거절용 dead-end backend 가 같은 `BackendMain` 을 쓴다.

`postmaster` / `launch_backend.c` L172-L208 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/launch_backend.c#L172-L208))

```c
// postmaster/launch_backend.c L172-L208
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

자식이 가장 먼저 닫는 것들이다. postmaster 의 대기 집합과 postmaster 사망 감시 파이프의 쓰기 쪽이다.

`postmaster` / `postmaster.c` L1855-L1879 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L1855-L1879))

```c
// postmaster/postmaster.c L1855-L1879
void
ClosePostmasterPorts(bool am_syslogger)
{
	/* Release resources held by the postmaster's WaitEventSet. */
	if (pm_wait_set)
	{
		FreeWaitEventSetAfterFork(pm_wait_set);
		pm_wait_set = NULL;
	}

#ifndef WIN32

	/*
	 * Close the write end of postmaster death watch pipe. It's important to
	 * do this as early as possible, so that if postmaster dies, others won't
	 * think that it's still running because we're holding the pipe open.
	 */
	if (close(postmaster_alive_fds[POSTMASTER_FD_OWN]) != 0)
		ereport(FATAL,
				(errcode_for_file_access(),
				 errmsg_internal("could not close postmaster death monitoring pipe in child process: %m")));
	postmaster_alive_fds[POSTMASTER_FD_OWN] = -1;
	/* Notify fd.c that we released one pipe FD. */
	ReleaseExternalFD();
#endif
```

## 동작 흐름

```text
 L235  Assert(postmaster 안이고 아직 자식이 아님)
 L238  외부 연결 backend 면 startup_data->fork_started = 지금 시각

 #ifdef EXEC_BACKEND  (Windows 등)
 L242    internal_forkexec  -> 자식은 SubPostmasterMain 으로 들어온다 (이 문서 밖)
 #else
 L246    pid = fork_process()
 L247    pid == 0 이면 (자식)
 L250-L257  conn_timing 에 socket_create, fork_start, fork_end 기록
 L260       ClosePostmasterPorts         pm_wait_set 해제, 사망 감시 파이프 쓰기 끝 닫기 ...
 L263       InitPostmasterChild          IsUnderPostmaster = true, latch 준비, setsid,
                                         SIGQUIT 처리기 (utils/init/miscinit.c L96)
 L266       shmem_attach 가 false 인 종류면 공유 메모리에서 떨어진다 (B_LOGGER 등)
 L278       TopMemoryContext 로 전환
 L280       MyPMChildSlot = child_slot
 L281-L284  클라이언트 소켓이 있으면 MyClientSocket 에 복사
 L290       child_process_kinds[child_type].main_fn(startup_data, len)
 L291       pg_unreachable()             main_fn 은 돌아오지 않는다
 #endif
 L294  return pid                         부모: 자식 pid,  fork 실패: -1
```

fork 뒤 두 프로세스가 같은 줄에서 갈라진다. 부모는 바로 `ServerLoop` 로 돌아가고, 자식은 이 함수를 빠져나오지 않는다.

```text
 fork 한 번, 두 갈래 (일반 빌드)

                    fork_process()  L246
                         |
          +--------------+---------------+
          | pid > 0                      | pid == 0
          v                              v
   postmaster                       자식
   L294 return pid                  L260 ClosePostmasterPorts
   BackendStartup L3595             L263 InitPostmasterChild
     bn->pid = pid                  L280 MyPMChildSlot
   ServerLoop L1708                 L283 MyClientSocket = 복사본
     closesocket(s.sock)            L290 BackendMain(startup_data)
   다음 연결을 기다린다                   [04] 로, 돌아오지 않음

 공유 메모리는 fork 로 그대로 물려받는다
   그래서 자식은 붙을 필요가 없고, 필요 없는 종류만 L268-L269 에서 떨어진다
```

```text
 child_process_kinds[] 에서 이 흐름이 쓰는 두 줄 (L182-L183)

 kind                 name                main_fn       shmem_attach
 B_BACKEND            "backend"           BackendMain   true
 B_DEAD_END_BACKEND   "dead-end backend"  BackendMain   true

 B_WAL_SENDER 는 main_fn 이 NULL 이다 (L193)
   walsender 는 직접 띄우지 않는다. 일반 backend 로 태어나 시작 패킷의
   replication 옵션을 본 뒤 종류를 바꾼다 (주석 L188-L192)
```

## 결과가 쓰이는 곳

```text
 자식 프로세스
      --> BackendMain 으로 들어가 [04] 부터 이 흐름의 나머지를 진행한다

 MyClientSocket
      --> [05] BackendInitialize 가 pq_init 으로 Port 를 만들 때 쓴다

 pid (부모 쪽)
      --> PMChild 에 기록되어 신호 보내기와 종료 감지에 쓰인다
```

## 다루지 않는 것

`fork_process` 내부, `InitPostmasterChild` 가 하는 신호 및 프로세스 설정 전체, `EXEC_BACKEND` 경로의 `internal_forkexec` / `save_backend_variables` / `SubPostmasterMain`, 다른 자식 종류의 main 함수들은 이 흐름의 곁가지라 요약만 했다.
