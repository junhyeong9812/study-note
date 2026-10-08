# StartupProcessMain

상위: [WAL redo (복구)](../README.md)

**startup 프로세스의 진입점이고, 시그널과 standby 용 타임아웃을 설정한 뒤 `StartupXLOG` 하나를 부르고 끝나는 함수다.** 복구가 끝나면 `proc_exit(0)` 으로 나가고, postmaster 는 종료 코드 0 을 "복구 성공"으로 읽는다(주석 L260-L263). 정상 종료 뒤의 기동처럼 재생할 WAL 이 없을 때도 이 프로세스가 `StartupXLOG` 를 돌린다.

## 위치

`src/backend/postmaster` / `startup.c` L215-L265 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/startup.c#L215-L265))

## 실제 코드

```c
// postmaster/startup.c L215-L265
void
StartupProcessMain(const void *startup_data, size_t startup_data_len)
{
	Assert(startup_data_len == 0);

	MyBackendType = B_STARTUP;
	AuxiliaryProcessMainCommon();

	/* Arrange to clean up at startup process exit */
	on_shmem_exit(StartupProcExit, 0);

	/*
	 * Properly accept or ignore signals the postmaster might send us.
	 */
	pqsignal(SIGHUP, StartupProcSigHupHandler); /* reload config file */
	pqsignal(SIGINT, SIG_IGN);	/* ignore query cancel */
	pqsignal(SIGTERM, StartupProcShutdownHandler);	/* request shutdown */
	/* SIGQUIT handler was already set up by InitPostmasterChild */
	InitializeTimeouts();		/* establishes SIGALRM handler */
	pqsignal(SIGPIPE, SIG_IGN);
	pqsignal(SIGUSR1, procsignal_sigusr1_handler);
	pqsignal(SIGUSR2, StartupProcTriggerHandler);

	/*
	 * Reset some signals that are accepted by postmaster but not here
	 */
	pqsignal(SIGCHLD, SIG_DFL);

	/*
	 * Register timeouts needed for standby mode
	 */
	RegisterTimeout(STANDBY_DEADLOCK_TIMEOUT, StandbyDeadLockHandler);
	RegisterTimeout(STANDBY_TIMEOUT, StandbyTimeoutHandler);
	RegisterTimeout(STANDBY_LOCK_TIMEOUT, StandbyLockTimeoutHandler);

	/*
	 * Unblock signals (they were blocked when the postmaster forked us)
	 */
	sigprocmask(SIG_SETMASK, &UnBlockSig, NULL);

	/*
	 * Do what we came for.
	 */
	StartupXLOG();

	/*
	 * Exit normally. Exit code 0 tells postmaster that we completed recovery
	 * successfully.
	 */
	proc_exit(0);
}
```

## 동작 흐름

```text
 StartupProcessMain

 L220  MyBackendType = B_STARTUP
 L221  AuxiliaryProcessMainCommon            보조 프로세스 공통 초기화
 L224  on_shmem_exit(StartupProcExit)        끝날 때 standby 복구 환경 정리
 L229-L241  시그널
 L246-L248  standby 충돌 해결용 타임아웃 셋 등록
 L253  시그널 차단 해제
 L258  StartupXLOG()                          [02] 여기서 복구가 전부 일어난다
 L264  proc_exit(0)
```

startup 프로세스가 받는 시그널은 복구를 바깥에서 조종하는 손잡이다.

```text
 signal   handler                      effect
 SIGHUP   StartupProcSigHupHandler     설정 다시 읽기 (primary_conninfo 바뀌면 walreceiver 재시작)
 SIGINT   SIG_IGN                      쿼리 취소는 무시
 SIGTERM  StartupProcShutdownHandler   종료 요청. restore_command 실행 중이면 바로 exit(1)
 SIGUSR1  procsignal_sigusr1_handler   ProcSignal (barrier 등)
 SIGUSR2  StartupProcTriggerHandler    promote 요청
```

## 결과가 쓰이는 곳

```text
 종료 코드 0
      --> postmaster 가 startup 종료를 보고 PM_RUN 으로 넘어가 연결을 받는다 (postmaster/postmaster.c L2320)
 종료 코드 3
      --> recovery_target_action = shutdown 일 때 PerformWalRecovery 가 proc_exit(3) (xlogrecovery.c L1887)
          postmaster 는 EXIT_STATUS_3 을 보고 서버를 내린다 (postmaster.c L2268)
```

## 다루지 않는 것

`AuxiliaryProcessMainCommon` 의 초기화, standby 타임아웃 핸들러(`StandbyDeadLockHandler` 등), `PreRestoreCommand`/`PostRestoreCommand` 의 SIGTERM 처리는 요약만 했다.
