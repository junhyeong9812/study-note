# ServerLoop

상위: [연결과 backend 기동](../README.md)

**postmaster 의 한가한 루프이자 모든 연결의 입구다.** 리슨 소켓과 latch 를 한 `WaitEventSet` 으로 기다리다가, 연결이 오면 `accept` 하고 [02] `BackendStartup` 에 넘긴 뒤 **자기 쪽 소켓은 바로 닫는다.** 연결을 받는 일 말고도 신호 처리, 빠진 백그라운드 프로세스 띄우기, 잠금 파일 점검을 같은 루프가 돌린다.

## 위치

`postmaster` / `postmaster.c` L1653-L1803 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L1653-L1803))

## 실제 코드

루프의 앞쪽이다. 기다렸다가, 깨어난 이유마다 처리한다.

`postmaster` / `postmaster.c` L1653-L1726 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L1653-L1726))

```c
// postmaster/postmaster.c L1653-L1726
ServerLoop(void)
{
	time_t		last_lockfile_recheck_time,
				last_touch_time;
	WaitEvent	events[MAXLISTEN];
	int			nevents;

	ConfigurePostmasterWaitSet(true);
	last_lockfile_recheck_time = last_touch_time = time(NULL);

	for (;;)
	{
		time_t		now;

		nevents = WaitEventSetWait(pm_wait_set,
								   DetermineSleepTime(),
								   events,
								   lengthof(events),
								   0 /* postmaster posts no wait_events */ );

		/*
		 * Latch set by signal handler, or new connection pending on any of
		 * our sockets? If the latter, fork a child process to deal with it.
		 */
		for (int i = 0; i < nevents; i++)
		{
			if (events[i].events & WL_LATCH_SET)
				ResetLatch(MyLatch);

			/*
			 * The following requests are handled unconditionally, even if we
			 * didn't see WL_LATCH_SET.  This gives high priority to shutdown
			 * and reload requests where the latch happens to appear later in
			 * events[] or will be reported by a later call to
			 * WaitEventSetWait().
			 */
			if (pending_pm_shutdown_request)
				process_pm_shutdown_request();
			if (pending_pm_reload_request)
				process_pm_reload_request();
			if (pending_pm_child_exit)
				process_pm_child_exit();
			if (pending_pm_pmsignal)
				process_pm_pmsignal();

			if (events[i].events & WL_SOCKET_ACCEPT)
			{
				ClientSocket s;

				if (AcceptConnection(events[i].fd, &s) == STATUS_OK)
					BackendStartup(&s);

				/* We no longer need the open socket in this process */
				if (s.sock != PGINVALID_SOCKET)
				{
					if (closesocket(s.sock) != 0)
						elog(LOG, "could not close client socket: %m");
				}
			}
		}

		/*
		 * If we need to launch any background processes after changing state
		 * or because some exited, do so now.
		 */
		LaunchMissingBackgroundProcesses();

		/* If we need to signal the autovacuum launcher, do so now */
		if (avlauncher_needs_signal)
		{
			avlauncher_needs_signal = false;
			if (AutoVacLauncherPMChild != NULL)
				signal_child(AutoVacLauncherPMChild, SIGUSR2);
		}
```

루프의 뒤쪽은 비싼 점검을 시간 간격을 두고 한다.

`postmaster` / `postmaster.c` L1745-L1803 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/postmaster.c#L1745-L1803))

```c
// postmaster/postmaster.c L1745-L1803
		now = time(NULL);

// ... (L1747-L1755 생략: 주석)
		if ((Shutdown >= ImmediateShutdown || FatalError) &&
			AbortStartTime != 0 &&
			(now - AbortStartTime) >= SIGKILL_CHILDREN_AFTER_SECS)
		{
			/* We were gentle with them before. Not anymore */
			ereport(LOG,
			/* translator: %s is SIGKILL or SIGABRT */
					(errmsg("issuing %s to recalcitrant children",
							send_abort_for_kill ? "SIGABRT" : "SIGKILL")));
			TerminateChildren(send_abort_for_kill ? SIGABRT : SIGKILL);
			/* reset flag so we don't SIGKILL again */
			AbortStartTime = 0;
		}

// ... (L1770-L1779 생략: 주석)
		if (now - last_lockfile_recheck_time >= 1 * SECS_PER_MINUTE)
		{
			if (!RecheckDataDirLockFile())
			{
				ereport(LOG,
						(errmsg("performing immediate shutdown because data directory lock file is invalid")));
				kill(MyProcPid, SIGQUIT);
			}
			last_lockfile_recheck_time = now;
		}

		/*
		 * Touch Unix socket and lock files every 58 minutes, to ensure that
		 * they are not removed by overzealous /tmp-cleaning tasks.  We assume
		 * no one runs cleaners with cutoff times of less than an hour ...
		 */
		if (now - last_touch_time >= 58 * SECS_PER_MINUTE)
		{
			TouchSocketFiles();
			TouchSocketLockFiles();
			last_touch_time = now;
		}
	}
}
```

`accept` 는 libpq 쪽에 있다. 실패하면 0.1초 쉬고 돌아온다.

`libpq` / `pqcomm.c` L794-L818 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/libpq/pqcomm.c#L794-L818))

```c
// libpq/pqcomm.c L794-L818
AcceptConnection(pgsocket server_fd, ClientSocket *client_sock)
{
	/* accept connection and fill in the client (remote) address */
	client_sock->raddr.salen = sizeof(client_sock->raddr.addr);
	if ((client_sock->sock = accept(server_fd,
									(struct sockaddr *) &client_sock->raddr.addr,
									&client_sock->raddr.salen)) == PGINVALID_SOCKET)
	{
		ereport(LOG,
				(errcode_for_socket_access(),
				 errmsg("could not accept new connection: %m")));

		/*
		 * If accept() fails then postmaster.c will still see the server
		 * socket as read-ready, and will immediately try again.  To avoid
		 * uselessly sucking lots of CPU, delay a bit before trying again.
		 * (The most likely reason for failure is being out of kernel file
		 * table slots; we can do little except hope some will get freed up.)
		 */
		pg_usleep(100000L);		/* wait 0.1 sec */
		return STATUS_ERROR;
	}

	return STATUS_OK;
}
```

## 동작 흐름

```text
 L1660  ConfigurePostmasterWaitSet(true)       리슨 소켓들 + latch 를 pm_wait_set 에 등록
 L1663  for (;;)
 L1667    nevents = WaitEventSetWait(pm_wait_set, DetermineSleepTime(), events, ...)
            잠드는 시간은 DetermineSleepTime 이 정한다 (아래 L1740-L1743 주석: 최대 1분)

 L1677    깨어난 이벤트마다
 L1679      WL_LATCH_SET 이면 ResetLatch
 L1689-L1696  신호 처리기가 세운 플래그를 여기서 처리한다
              shutdown, reload(SIGHUP), 자식 종료(SIGCHLD), pmsignal
 L1698      WL_SOCKET_ACCEPT 이면
 L1702        AcceptConnection -> accept()       ClientSocket 에 fd 와 원격 주소
 L1703        성공이면 [02] BackendStartup(&s)
 L1706-L1709  s.sock 을 닫는다                    성공이든 실패든 postmaster 는 소켓을 들고 있지 않는다

 L1718    LaunchMissingBackgroundProcesses       checkpointer, walwriter 등 빠진 것을 띄운다
 L1721    autovacuum launcher 에 SIGUSR2 가 필요하면 보낸다

 L1745    now = time(NULL)
 L1756    종료 중인데 자식이 안 죽으면 SIGKILL_CHILDREN_AFTER_SECS 뒤 SIGKILL (또는 SIGABRT)
 L1780    1분마다 postmaster.pid 재확인. 잘못되면 자기에게 SIGQUIT
 L1796    58분마다 소켓 파일과 잠금 파일의 시각을 갱신
```

연결 하나가 이 루프에서 머무는 시간은 `accept` 와 `fork` 뿐이다. 인증이나 시작 패킷 읽기는 이 루프를 막지 않는다.

```text
 postmaster 가 연결 하나에 쓰는 일 (시간 순, 오른쪽은 클라이언트 소켓 fd 의 상태)

 줄      postmaster 의 호출              fd 상태
 L1667   WaitEventSetWait                WL_SOCKET_ACCEPT 로 깨어남
 L1702   accept()                        생김 (postmaster 가 가짐)
 L1703   BackendStartup -> fork          자식도 같은 fd 를 물려받음
 L1708   closesocket(s.sock)             postmaster 쪽은 닫힘
 L1667   WaitEventSetWait                이제 자식 혼자 가짐

 시작 패킷이 늦게 오거나 인증이 느려도 postmaster 는 이미 다음 연결을 기다리고 있다
```

```text
 accept 가 실패하면 (pqcomm.c L798-L815)

 LOG "could not accept new connection"
 pg_usleep(100000)   0.1 초 쉰다
   주석 L806-L812: 리슨 소켓이 계속 read-ready 로 보여서 바로 다시 깨어나므로,
   CPU 를 헛되이 쓰지 않으려고 잠깐 멈춘다. 흔한 원인은 커널 파일 테이블 고갈
 STATUS_ERROR -> BackendStartup 을 부르지 않는다
 s.sock 은 PGINVALID_SOCKET 이라 L1706 의 close 도 건너뛴다
```

## 결과가 쓰이는 곳

```text
 ClientSocket s (fd + 원격 주소)
      --> [02] BackendStartup 이 postmaster_child_launch 에 넘긴다
      --> 자식에서는 MyClientSocket 으로 복사된다 (launch_backend.c L283-L284)

 LaunchMissingBackgroundProcesses
      --> [체크포인트] 의 checkpointer, [vacuum] 의 autovacuum launcher 등이 여기서 (다시) 뜬다
```

## 다루지 않는 것

`DetermineSleepTime` 의 시간 계산, `ConfigurePostmasterWaitSet` 과 `WaitEventSet` 구현(epoll/kqueue/poll), 신호 처리 함수들(`process_pm_shutdown_request`, `process_pm_reload_request`, `process_pm_child_exit`, `process_pm_pmsignal`), `LaunchMissingBackgroundProcesses` 가 무엇을 언제 띄우는지, 종료 시 `TerminateChildren` 은 postmaster 운영의 곁가지라 요약만 했다.
