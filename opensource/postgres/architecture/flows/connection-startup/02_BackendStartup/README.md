# BackendStartup

상위: [연결과 backend 기동](../README.md)

postmaster 가 연결 하나를 위해 **자리를 잡고 자식을 띄우는** 함수다. 볼거리는 두 가지다. 거절할 연결도 **일단 fork 한다**(dead-end 자식) - 거절 메시지를 클라이언트 프로토콜에 맞춰 보내는 일을 postmaster 가 하지 않기 위해서다. 그리고 슬롯은 fork **전에** 잡는다 - 메모리나 슬롯이 모자라는 실패를 fork 전에 깨끗이 처리하려고서다(L3531-L3534 주석).

## 위치

`postmaster` / `postmaster.c` L3518-L3597 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L3518-L3597))

## 실제 코드

`postmaster` / `postmaster.c` L3518-L3597 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L3518-L3597))

```c
// postmaster/postmaster.c L3518-L3597
BackendStartup(ClientSocket *client_sock)
{
	PMChild    *bn = NULL;
	pid_t		pid;
	BackendStartupData startup_data;
	CAC_state	cac;

	/*
	 * Capture time that Postmaster got a socket from accept (for logging
	 * connection establishment and setup total duration).
	 */
	startup_data.socket_created = GetCurrentTimestamp();

	/*
	 * Allocate and assign the child slot.  Note we must do this before
	 * forking, so that we can handle failures (out of memory or child-process
	 * slots) cleanly.
	 */
	cac = canAcceptConnections(B_BACKEND);
	if (cac == CAC_OK)
	{
		/* Can change later to B_WAL_SENDER */
		bn = AssignPostmasterChildSlot(B_BACKEND);
		if (!bn)
		{
			/*
			 * Too many regular child processes; launch a dead-end child
			 * process instead.
			 */
			cac = CAC_TOOMANY;
		}
	}
	if (!bn)
	{
		bn = AllocDeadEndChild();
		if (!bn)
		{
			ereport(LOG,
					(errcode(ERRCODE_OUT_OF_MEMORY),
					 errmsg("out of memory")));
			return STATUS_ERROR;
		}
	}

	/* Pass down canAcceptConnections state */
	startup_data.canAcceptConnections = cac;
	bn->rw = NULL;

	/* Hasn't asked to be notified about any bgworkers yet */
	bn->bgworker_notify = false;

	pid = postmaster_child_launch(bn->bkend_type, bn->child_slot,
								  &startup_data, sizeof(startup_data),
								  client_sock);
	if (pid < 0)
	{
		/* in parent, fork failed */
		int			save_errno = errno;

		(void) ReleasePostmasterChildSlot(bn);
		errno = save_errno;
		ereport(LOG,
				(errmsg("could not fork new process for connection: %m")));
		report_fork_failure_to_client(client_sock, save_errno);
		return STATUS_ERROR;
	}

	/* in parent, successful fork */
	ereport(DEBUG2,
			(errmsg_internal("forked new %s, pid=%d socket=%d",
							 GetBackendTypeDesc(bn->bkend_type),
							 (int) pid, (int) client_sock->sock)));

	/*
	 * Everything's been successful, it's safe to add this backend to our list
	 * of backends.
	 */
	bn->pid = pid;
	return STATUS_OK;
}
```

서버 상태가 연결을 받을 수 있는지 고르는 쪽이다. 여기서는 결과만 정하고, 거절 통보는 자식이 한다.

`postmaster` / `postmaster.c` L1811-L1843 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L1811-L1843))

```c
// postmaster/postmaster.c L1811-L1843
static CAC_state
canAcceptConnections(BackendType backend_type)
{
	CAC_state	result = CAC_OK;

	Assert(backend_type == B_BACKEND || backend_type == B_AUTOVAC_WORKER);

	/*
	 * Can't start backends when in startup/shutdown/inconsistent recovery
	 * state.  We treat autovac workers the same as user backends for this
	 * purpose.
	 */
	if (pmState != PM_RUN && pmState != PM_HOT_STANDBY)
	{
		if (Shutdown > NoShutdown)
			return CAC_SHUTDOWN;	/* shutdown is pending */
		else if (!FatalError && pmState == PM_STARTUP)
			return CAC_STARTUP; /* normal startup */
		else if (!FatalError && pmState == PM_RECOVERY)
			return CAC_NOTHOTSTANDBY;	/* not yet ready for hot standby */
		else
			return CAC_RECOVERY;	/* else must be crash recovery */
	}

	/*
	 * "Smart shutdown" restrictions are applied only to normal connections,
	 * not to autovac workers.
	 */
	if (!connsAllowed && backend_type == B_BACKEND)
		return CAC_SHUTDOWN;	/* shutdown is pending */

	return result;
}
```

슬롯 풀의 크기와 꺼내는 쪽이다. 일반 backend 풀은 `max_connections` 의 두 배 남짓이다.

`postmaster` / `pmchild.c` L91-L100 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/pmchild.c#L91-L100))

```c
// postmaster/pmchild.c L91-L100
	/*
	 * We allow more connections here than we can have backends because some
	 * might still be authenticating; they might fail auth, or some existing
	 * backend might exit before the auth cycle is completed.  The exact
	 * MaxConnections limit is enforced when a new backend tries to join the
	 * PGPROC array.
	 *
	 * WAL senders start out as regular backends, so they share the same pool.
	 */
	pmchild_pools[B_BACKEND].size = 2 * (MaxConnections + max_wal_senders);
```

`postmaster` / `pmchild.c` L162-L200 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/pmchild.c#L162-L200))

```c
// postmaster/pmchild.c L162-L200
AssignPostmasterChildSlot(BackendType btype)
{
	dlist_head *freelist;
	PMChild    *pmchild;

	if (pmchild_pools[btype].size == 0)
		elog(ERROR, "cannot allocate a PMChild slot for backend type %d", btype);

	freelist = &pmchild_pools[btype].freelist;
	if (dlist_is_empty(freelist))
		return NULL;

	pmchild = dlist_container(PMChild, elem, dlist_pop_head_node(freelist));
	pmchild->pid = 0;
	pmchild->bkend_type = btype;
	pmchild->rw = NULL;
	pmchild->bgworker_notify = true;

	/*
	 * pmchild->child_slot for each entry was initialized when the array of
	 * slots was allocated.  Sanity check it.
	 */
	if (!(pmchild->child_slot >= pmchild_pools[btype].first_slotno &&
		  pmchild->child_slot < pmchild_pools[btype].first_slotno + pmchild_pools[btype].size))
	{
		elog(ERROR, "pmchild freelist for backend type %d is corrupt",
			 pmchild->bkend_type);
	}

	dlist_push_head(&ActiveChildList, &pmchild->elem);

	/* Update the status in the shared memory array */
	MarkPostmasterChildSlotAssigned(pmchild->child_slot);

	elog(DEBUG2, "assigned pm child slot %d for %s",
		 pmchild->child_slot, PostmasterChildName(btype));

	return pmchild;
}
```

## 동작 흐름

```text
 L3529  startup_data.socket_created = 지금 시각     log_connections 의 setup 시간 측정용

 L3536  cac = canAcceptConnections(B_BACKEND)
          pmState 가 PM_RUN / PM_HOT_STANDBY 가 아니면 (L1823)
            종료 중            CAC_SHUTDOWN
            PM_STARTUP         CAC_STARTUP
            PM_RECOVERY        CAC_NOTHOTSTANDBY
            그 밖 (크래시 복구) CAC_RECOVERY
          smart shutdown 으로 새 연결 금지면 CAC_SHUTDOWN   (L1839)
          아니면 CAC_OK

 L3537  CAC_OK 이면
 L3540    bn = AssignPostmasterChildSlot(B_BACKEND)   freelist 에서 하나
 L3541    없으면 cac = CAC_TOOMANY
 L3550  bn 이 없으면 (CAC_OK 가 아니었거나 슬롯이 없었으면)
 L3552    bn = AllocDeadEndChild()                    슬롯 번호 없는 palloc 구조체
 L3553    그것도 실패면 LOG "out of memory", STATUS_ERROR

 L3563  startup_data.canAcceptConnections = cac     자식에게 판정을 넘긴다
 L3569  pid = [03] postmaster_child_launch(bn->bkend_type, bn->child_slot, ...)
            bkend_type 은 B_BACKEND 또는 B_DEAD_END_BACKEND
 L3572  pid < 0 (fork 실패)
 L3577    ReleasePostmasterChildSlot(bn)
 L3581    report_fork_failure_to_client          비차단으로 한 번만 send 시도 (L3607-L3627)
 L3582    STATUS_ERROR
 L3595  bn->pid = pid                             이제 postmaster 가 이 자식을 추적한다
```

거절할 연결도 fork 한다는 점이 이 함수의 핵심이다. 판정은 postmaster 가 하고, 통보는 자식이 시작 패킷을 읽은 뒤에 한다.

```text
 cac 별로 누가 무엇을 하는가 (줄은 자식 쪽 backend_startup.c)

 cac                 fork 하는 종류       줄     자식이 시작 패킷 뒤에 하는 일
 CAC_OK              B_BACKEND            -      인증 -> 루프
 CAC_TOOMANY         B_DEAD_END_BACKEND   L340   FATAL "sorry, too many clients already" (슬롯 없음)
 CAC_STARTUP         B_DEAD_END_BACKEND   L306   FATAL "the database system is starting up"
 CAC_SHUTDOWN        B_DEAD_END_BACKEND   L330   FATAL "... is shutting down"
 CAC_RECOVERY        B_DEAD_END_BACKEND   L335   FATAL "... is in recovery mode"
 CAC_NOTHOTSTANDBY   B_DEAD_END_BACKEND   L311   hot standby 설정과 일관성 도달 여부로 FATAL 셋 중 하나

 child_process_kinds[B_DEAD_END_BACKEND].main_fn 도 BackendMain 이다 (launch_backend.c L183)
 그래서 거절도 정상 연결과 같은 길로 시작 패킷까지 읽는다
   주석 (backend_startup.c L297-L300): 인증을 하기 전에 거절해서 낭비를 줄이고,
   pg_ping 같은 도구가 서버 상태를 알 수 있게 한다
```

```text
 PMChild 슬롯 풀 (pmchild.c, 기본값 max_connections 100, max_wal_senders 10)

 pmchild_pools[B_BACKEND].size = 2 * (100 + 10) = 220      L100
   walsender 도 처음엔 일반 backend 로 시작하므로 같은 풀을 쓴다 (주석 L98)

 AssignPostmasterChildSlot(B_BACKEND)
   freelist 가 비었으면 NULL        L171-L172   -> BackendStartup 이 CAC_TOOMANY 로
   pop -> pid=0, bkend_type 설정     L174-L178
   ActiveChildList 에 넣는다          L191
   공유 메모리 PMChildFlags 에 표시   L194

 슬롯이 220 개여도 실제로 일하는 backend 는 PGPROC 수(100)를 넘지 못한다
   나머지는 인증 중이거나 InitProcess 에서 거절될 연결의 몫이다 (주석 L91-L96)
```

## 결과가 쓰이는 곳

```text
 PMChild bn
      --> ActiveChildList 에 올라 자식이 죽으면 process_pm_child_exit 가 찾아 슬롯을 반납한다
      --> bn->child_slot 이 자식의 MyPMChildSlot 이 된다 (launch_backend.c L280)

 startup_data.canAcceptConnections
      --> [05] BackendInitialize 가 시작 패킷 뒤 이것으로 FATAL 을 낼지 정한다
```

## 다루지 않는 것

`AllocDeadEndChild` 로 만든 자식의 수명 관리, 슬롯 반납(`ReleasePostmasterChildSlot`)과 `PMChildFlags` 의 의미, `pmState` 전이(`PostmasterStateMachine`), autovacuum worker 가 같은 `canAcceptConnections` 를 쓰는 경로(`StartAutovacuumWorker`)는 곁가지라 요약만 했다.
