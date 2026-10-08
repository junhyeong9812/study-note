# AutoVacLauncherMain

상위: [vacuum](../README.md)

**autovacuum launcher 프로세스의 본체다.** launcher 자신은 테이블을 만지지 않는다. DB 목록을 `autovacuum_naptime`(기본 60 초) 안에 고르게 흩어 두고, 다음 DB 의 차례가 올 때까지 잠들었다가, 빈 worker 슬롯이 있으면 [04] 를 돌릴 worker 하나를 postmaster 에 요청한다. 어느 DB 로 보낼지는 `do_start_worker` 가 정하는데, XID wraparound 위험이 있는 DB 가 있으면 시간표를 무시하고 그 DB 부터 보낸다.

## 위치

`postmaster` / `autovacuum.c` L367-L741 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L367-L741))

## 실제 코드

`postmaster` / `autovacuum.c` L367-L741 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L367-L741))

```c
// autovacuum.c L367-L741
void
AutoVacLauncherMain(const void *startup_data, size_t startup_data_len)
{
	sigjmp_buf	local_sigjmp_buf;
// ... (L371-L559 생략: 프로세스 초기화, 시그널, 오류 복구 지점, 비상 모드 (autovacuum=off 인데 wraparound 로 깨어난 경우))

	AutoVacuumShmem->av_launcherpid = MyProcPid;

	/*
	 * Create the initial database list.  The invariant we want this list to
	 * keep is that it's ordered by decreasing next_time.  As soon as an entry
	 * is updated to a higher time, it will be moved to the front (which is
	 * correct because the only operation is to add autovacuum_naptime to the
	 * entry, and time always increases).
	 */
	rebuild_database_list(InvalidOid);

	/* loop until shutdown request */
	while (!ShutdownRequestPending)
	{
		struct timeval nap;
		TimestampTz current_time = 0;
		bool		can_launch;

		/*
		 * This loop is a bit different from the normal use of WaitLatch,
		 * because we'd like to sleep before the first launch of a child
		 * process.  So it's WaitLatch, then ResetLatch, then check for
		 * wakening conditions.
		 */

		launcher_determine_sleep(av_worker_available(), false, &nap);

		/*
		 * Wait until naptime expires or we get some type of signal (all the
		 * signal handlers will wake us by calling SetLatch).
		 */
		(void) WaitLatch(MyLatch,
						 WL_LATCH_SET | WL_TIMEOUT | WL_EXIT_ON_PM_DEATH,
						 (nap.tv_sec * 1000L) + (nap.tv_usec / 1000L),
						 WAIT_EVENT_AUTOVACUUM_MAIN);

		ResetLatch(MyLatch);

		ProcessAutoVacLauncherInterrupts();

		// ... (L601-L634 생략: worker 가 끝났거나 fork 가 실패했다는 SIGUSR2 처리)

		/*
		 * There are some conditions that we need to check before trying to
		 * start a worker.  First, we need to make sure that there is a worker
		 * slot available.  Second, we need to make sure that no other worker
		 * failed while starting up.
		 */

		current_time = GetCurrentTimestamp();
		LWLockAcquire(AutovacuumLock, LW_SHARED);

		can_launch = av_worker_available();

		if (AutoVacuumShmem->av_startingWorker != NULL)
		// ... (L649-L698 생략: 시작 중인 worker 가 너무 오래 걸리면 슬롯을 회수한다)
		LWLockRelease(AutovacuumLock);	/* either shared or exclusive */

		/* if we can't do anything, just go back to sleep */
		if (!can_launch)
			continue;

		/* We're OK to start a new worker */

		if (dlist_is_empty(&DatabaseList))
		{
			/*
			 * Special case when the list is empty: start a worker right away.
			 * This covers the initial case, when no database is in pgstats
			 * (thus the list is empty).  Note that the constraints in
			 * launcher_determine_sleep keep us from starting workers too
			 * quickly (at most once every autovacuum_naptime when the list is
			 * empty).
			 */
			launch_worker(current_time);
		}
		else
		{
			/*
			 * because rebuild_database_list constructs a list with most
			 * distant adl_next_worker first, we obtain our database from the
			 * tail of the list.
			 */
			avl_dbase  *avdb;

			avdb = dlist_tail_element(avl_dbase, adl_node, &DatabaseList);

			/*
			 * launch a worker if next_worker is right now or it is in the
			 * past
			 */
			if (TimestampDifferenceExceeds(avdb->adl_next_worker,
										   current_time, 0))
				launch_worker(current_time);
		}
	}

	AutoVacLauncherShutdown();
}
```

worker 를 보낼 DB 를 고르는 부분이다. 위험한 DB 가 하나라도 있으면 나머지는 보지 않는다.

`postmaster` / `autovacuum.c` L1165-L1272 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/postmaster/autovacuum.c#L1165-L1272))

```c
// autovacuum.c L1165-L1272
	avdb = NULL;
	for_xid_wrap = false;
	for_multi_wrap = false;
	current_time = GetCurrentTimestamp();
	foreach(cell, dblist)
	{
		avw_dbase  *tmp = lfirst(cell);
		dlist_iter	iter;

		/* Check to see if this one is at risk of wraparound */
		if (TransactionIdPrecedes(tmp->adw_frozenxid, xidForceLimit))
		{
			if (avdb == NULL ||
				TransactionIdPrecedes(tmp->adw_frozenxid,
									  avdb->adw_frozenxid))
				avdb = tmp;
			for_xid_wrap = true;
			continue;
		}
		else if (for_xid_wrap)
			continue;			/* ignore not-at-risk DBs */
		else if (MultiXactIdPrecedes(tmp->adw_minmulti, multiForceLimit))
		{
			if (avdb == NULL ||
				MultiXactIdPrecedes(tmp->adw_minmulti, avdb->adw_minmulti))
				avdb = tmp;
			for_multi_wrap = true;
			continue;
		}
		else if (for_multi_wrap)
			continue;			/* ignore not-at-risk DBs */

		// ... (L1197-L1238 생략: pgstat 항목이 없거나 방금 처리한 DB 는 건너뛴다)
		/*
		 * Remember the db with oldest autovac time.  (If we are here, both
		 * tmp->entry and db->entry must be non-null.)
		 */
		if (avdb == NULL ||
			tmp->adw_entry->last_autovac_time < avdb->adw_entry->last_autovac_time)
			avdb = tmp;
	}

	/* Found a database -- process it */
	if (avdb != NULL)
	{
		WorkerInfo	worker;
		dlist_node *wptr;

		LWLockAcquire(AutovacuumLock, LW_EXCLUSIVE);

		/*
		 * Get a worker entry from the freelist.  We checked above, so there
		 * really should be a free slot.
		 */
		wptr = dclist_pop_head_node(&AutoVacuumShmem->av_freeWorkers);

		worker = dlist_container(WorkerInfoData, wi_links, wptr);
		worker->wi_dboid = avdb->adw_datid;
		worker->wi_proc = NULL;
		worker->wi_launchtime = GetCurrentTimestamp();

		AutoVacuumShmem->av_startingWorker = worker;

		LWLockRelease(AutovacuumLock);

		SendPostmasterSignal(PMSIGNAL_START_AUTOVAC_WORKER);

```

## 동작 흐름

```text
 AutoVacLauncherMain
 L570  rebuild_database_list                 DB 마다 adl_next_worker 를 naptime 안에 고르게 배치
 L573  while (!ShutdownRequestPending)
         L586  launcher_determine_sleep       목록 끝 DB 의 next_worker 까지 잘 시간
         L592  WaitLatch(nap)                  worker 종료(SIGUSR2)나 설정 변경이 깨울 수 있다
         L646  can_launch = av_worker_available()     빈 슬롯이 있나
         L648  시작 중인 worker 가 있으면 can_launch = false
         L717  목록이 비었으면 바로 launch_worker
         L736  목록 끝 DB 의 next_worker 가 지났으면 launch_worker
                 do_start_worker (L1090)
                   L1132  xidForceLimit = nextXid - autovacuum_freeze_max_age
                   L1175  datfrozenxid < xidForceLimit 인 DB 가 있으면 그중 가장 오래된 것
                   L1243  아니면 last_autovac_time 이 가장 오래된 DB
                   L1260  av_freeWorkers 에서 슬롯 하나, wi_dboid = 그 DB
                   L1271  SendPostmasterSignal(PMSIGNAL_START_AUTOVAC_WORKER)
                 launch_worker 가 그 DB 의 next_worker = now + naptime 으로 옮긴다 (L1328)
```

DB 들의 차례는 naptime 을 DB 수로 나눈 간격으로 돈다(`rebuild_database_list`, L1039). 기본값으로 DB 세 개가 pgstat 에 있을 때의 시간표다.

```text
 autovacuum_naptime = 60 s, nelems = 3
 millis_increment = 1000.0 * 60 / 3 = 20000 ms

 rebuild 시각 T 에서 (L1049-L1055)
 next_worker  T+20 s    T+40 s    T+60 s
 DB           db_a      db_b      db_c
 차례가 와서 worker 를 받으면 launch_worker 가 그 DB 를 now + 60 s 로 옮긴다
 그래서 각 DB 는 대략 60 초마다 한 번씩 worker 를 받는다

 슬롯(autovacuum_max_workers = 3)이 다 차 있으면 L586 에서 naptime 만큼 자고,
 worker 가 끝날 때 SIGUSR2 로 깨어난다
```

wraparound 우선 규칙은 숫자로 보면 분명하다. `autovacuum_freeze_max_age` 기본값은 2 억이다(guc_tables.c L3584).

```text
 nextXid = 250,000,000
 xidForceLimit = 250,000,000 - 200,000,000 = 50,000,000

 DB      datfrozenxid    last_autovac_time   선택
 db_a    120,000,000     10 min ago          위험 아님
 db_b     40,000,000     1 min ago           위험 (40M < 50M)  -> 선택
 db_c     45,000,000     30 min ago          위험 (45M < 50M), 하지만 db_b 의 datfrozenxid 가 더 오래됐다

 for_xid_wrap 이 켜지면 위험하지 않은 DB 는 L1184 에서 건너뛴다
```

## 결과가 쓰이는 곳

```text
 AutoVacuumShmem->av_startingWorker, wi_dboid
      --> postmaster 가 StartAutovacuumWorker 로 worker 를 띄운다 (postmaster.c L3783)
      --> worker 가 AutoVacWorkerMain 에서 이 슬롯을 집어 wi_dboid 에 접속한다
 DatabaseList 의 adl_next_worker
      --> 다음 잠들 시간 (launcher_determine_sleep)
```

## 다루지 않는 것

비용 한도 재분배(`autovac_recalculate_workers_for_balance`), worker fork 실패 재시도, `autovacuum = off` 에서 wraparound 때문에 한 번만 도는 비상 모드, MultiXact wraparound 판정(`MultiXactMemberFreezeThreshold`)은 다루지 않았다.
