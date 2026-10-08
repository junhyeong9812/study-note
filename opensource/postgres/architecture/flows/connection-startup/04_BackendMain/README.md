# BackendMain

상위: [연결과 backend 기동](../README.md)

**연결 backend 의 main 함수다.** 세 줄짜리 지휘자로, 시작 패킷 받기([05]), 공유 메모리에 자기 `PGPROC` 잡기, 메시지 루프 들어가기([07])를 **이 순서로** 부른다. 순서가 중요하다. 시작 패킷을 받는 동안은 공유 메모리를 건드리지 않아야, 클라이언트가 늦을 때 `_exit(1)` 로 깨끗이 끝낼 수 있다(backend_startup.c L186-L195 주석).

## 위치

`tcop` / `backend_startup.c` L76-L125 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L76-L125))

## 실제 코드

`tcop` / `backend_startup.c` L76-L125 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/tcop/backend_startup.c#L76-L125))

```c
// tcop/backend_startup.c L76-L125
BackendMain(const void *startup_data, size_t startup_data_len)
{
	const BackendStartupData *bsdata = startup_data;

	Assert(startup_data_len == sizeof(BackendStartupData));
	Assert(MyClientSocket != NULL);

#ifdef EXEC_BACKEND

	/*
	 * Need to reinitialize the SSL library in the backend, since the context
	 * structures contain function pointers and cannot be passed through the
	 * parameter file.
	 *
	 * If for some reason reload fails (maybe the user installed broken key
	 * files), soldier on without SSL; that's better than all connections
	 * becoming impossible.
	 *
	 * XXX should we do this in all child processes?  For the moment it's
	 * enough to do it in backend children.
	 */
#ifdef USE_SSL
	if (EnableSSL)
	{
		if (secure_initialize(false) == 0)
			LoadedSSL = true;
		else
			ereport(LOG,
					(errmsg("SSL configuration could not be loaded in child process")));
	}
#endif
#endif

	/* Perform additional initialization and collect startup packet */
	BackendInitialize(MyClientSocket, bsdata->canAcceptConnections);

	/*
	 * Create a per-backend PGPROC struct in shared memory.  We must do this
	 * before we can use LWLocks or access any shared memory.
	 */
	InitProcess();

	/*
	 * Make sure we aren't in PostmasterContext anymore.  (We can't delete it
	 * just yet, though, because InitPostgres will need the HBA data.)
	 */
	MemoryContextSwitchTo(TopMemoryContext);

	PostgresMain(MyProcPort->database_name, MyProcPort->user_name);
}
```

`InitProcess` 가 `PGPROC` 를 꺼내는 자리다. 일반 backend 의 리스트 `freeProcs` 가 비면 여기서 연결이 끝난다.

`storage` / `lmgr` / `proc.c` L412-L458 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L412-L458))

```c
// lmgr/proc.c L412-L458
	/*
	 * Decide which list should supply our PGPROC.  This logic must match the
	 * way the freelists were constructed in InitProcGlobal().
	 */
	if (AmAutoVacuumWorkerProcess() || AmSpecialWorkerProcess())
		procgloballist = &ProcGlobal->autovacFreeProcs;
	else if (AmBackgroundWorkerProcess())
		procgloballist = &ProcGlobal->bgworkerFreeProcs;
	else if (AmWalSenderProcess())
		procgloballist = &ProcGlobal->walsenderFreeProcs;
	else
		procgloballist = &ProcGlobal->freeProcs;

	/*
	 * Try to get a proc struct from the appropriate free list.  If this
	 * fails, we must be out of PGPROC structures (not to mention semaphores).
	 *
	 * While we are holding the ProcStructLock, also copy the current shared
	 * estimate of spins_per_delay to local storage.
	 */
	SpinLockAcquire(ProcStructLock);

	set_spins_per_delay(ProcGlobal->spins_per_delay);

	if (!dlist_is_empty(procgloballist))
	{
		MyProc = dlist_container(PGPROC, links, dlist_pop_head_node(procgloballist));
		SpinLockRelease(ProcStructLock);
	}
	else
	{
		/*
		 * If we reach here, all the PGPROCs are in use.  This is one of the
		 * possible places to detect "too many backends", so give the standard
		 * error message.  XXX do we need to give a different failure message
		 * in the autovacuum case?
		 */
		SpinLockRelease(ProcStructLock);
		if (AmWalSenderProcess())
			ereport(FATAL,
					(errcode(ERRCODE_TOO_MANY_CONNECTIONS),
					 errmsg("number of requested standby connections exceeds \"max_wal_senders\" (currently %d)",
							max_wal_senders)));
		ereport(FATAL,
				(errcode(ERRCODE_TOO_MANY_CONNECTIONS),
				 errmsg("sorry, too many clients already")));
	}
```

`freeProcs` 의 길이는 서버 기동 때 `max_connections` 로 정해진다.

`storage` / `lmgr` / `proc.c` L328-L333 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/storage/lmgr/proc.c#L328-L333))

```c
// lmgr/proc.c L328-L333
		if (i < MaxConnections)
		{
			/* PGPROC for normal backend, add to freeProcs list */
			dlist_push_tail(&ProcGlobal->freeProcs, &proc->links);
			proc->procgloballist = &ProcGlobal->freeProcs;
		}
```

## 동작 흐름

```text
 L78   bsdata = postmaster 가 넘긴 BackendStartupData
 L80   Assert(크기가 맞고 MyClientSocket 이 있음)

 #ifdef EXEC_BACKEND
 L97-L106  SSL 라이브러리를 자식에서 다시 초기화 (함수 포인터는 파일로 못 넘기므로)
 #endif

 L110  [05] BackendInitialize(MyClientSocket, bsdata->canAcceptConnections)
         시작 패킷을 받고 Port 를 채운다. 실패나 취소 요청이면 이 안에서 proc_exit
 L116  InitProcess()
         L409  RegisterPostmasterChildActive
         L416-L423  종류별 리스트 고르기
                      autovacuum / 특수 워커  autovacFreeProcs
                      bgworker                bgworkerFreeProcs
                      walsender               walsenderFreeProcs
                      그 밖 (일반 연결)       freeProcs
         L436  리스트가 비지 않았으면 pop -> MyProc
         L441  비었으면 FATAL
                 walsender  "number of requested standby connections exceeds max_wal_senders"
                 그 밖      "sorry, too many clients already"
 L122  TopMemoryContext 로 전환 (PostmasterContext 는 HBA 데이터 때문에 아직 지우지 않음)
 L124  [07] PostgresMain(MyProcPort->database_name, MyProcPort->user_name)
         돌아오지 않는다
```

시작 패킷을 받는 구간과 공유 메모리를 쓰는 구간이 이 함수에서 정확히 나뉜다.

```text
 BackendMain 의 세 구간

 줄     호출                  구간과 공유 메모리, SIGTERM / 시간 초과 시
 L110   BackendInitialize     시작 패킷 받기. 공유 메모리 안 건드림. _exit(1) (process_startup_packet_die)
 L116   InitProcess           PGPROC 잡기. 공유 메모리를 처음 건드림. 이후로는 정상 종료 경로만
 L124   PostgresMain          세션과 루프. die() 가 쿼리 취소 후 종료

 BackendInitialize 끝의 check_on_shmem_exit_lists_are_empty (backend_startup.c L365)
   "아직 공유 메모리를 건드린 정리 콜백이 없다" 를 확인하는 안전장치다
```

```text
 PGPROC 리스트와 max_connections (기본값 100, proc.c L328)

 InitProcGlobal 이 만든 PGPROC 배열의 앞 MaxConnections 개
   -> freeProcs  (일반 연결 backend 몫)

 앞선 연결이 모두 살아 있다면, 연결 k 번째가 InitProcess 를 지나면 freeProcs 에 100 - k 개가 남는다
   k = 101 이면 리스트가 비어 L455 FATAL
   (98~100 번째가 superuser 일 때만 100 개가 다 찬다. 일반 역할이면 [08] 의 예약 검사가
    PGPROC 를 쥔 채 FATAL 로 끝나고, 종료하면서 PGPROC 를 돌려준다 -> 08 문서)
 PMChild 슬롯은 220 개라 101 번째 연결도 fork 까지는 간다 (02 문서)
   그리고 여기서 거절된다
```

## 결과가 쓰이는 곳

```text
 MyProcPort (Port)
      --> [07] PostgresMain 의 인자 database_name, user_name

 MyProc (PGPROC)
      --> [08] InitPostgres 의 InitProcessPhase2 가 ProcArray 에 올린다
      --> 이후 락 대기, 스냅샷, 신호가 모두 이 구조체로 이 backend 를 찾는다
```

## 다루지 않는 것

`InitProcess` 의 나머지(세마포어, latch, `PGPROC` 필드 초기화), 보조 프로세스용 `InitAuxiliaryProcess`, `EXEC_BACKEND` 의 SSL 재초기화(`secure_initialize`)는 곁가지라 요약만 했다. `PGPROC` 구조는 구조 편 공유 메모리에서 다룬다.
