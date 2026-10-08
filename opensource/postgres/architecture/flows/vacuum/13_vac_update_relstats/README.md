# vac_update_relstats

상위: [vacuum](../README.md)

**VACUUM 의 결과를 pg_class 에 남긴다.** relpages, reltuples, relallvisible, relallfrozen 과 relfrozenxid, relminmxid 를 고치는데, 보통의 UPDATE 가 아니라 **그 행을 제자리에서 덮어쓴다**(`systable_inplace_update_*`). 주석은 이것이 트랜잭션 의미를 어기는 일임을 인정하고 이유를 둘 든다. 보통 UPDATE 로 하면 pg_class 자체를 vacuum 할 때마다 pg_class 에 죽은 행이 생기고, `PROC_IN_VACUUM` 을 세운 lazy vacuum 은 보통 갱신을 하면 안 된다는 것이다(L1409-L1421). relfrozenxid 는 앞으로만 간다. 테이블이 끝나면 [02] 가 `vac_update_datfrozenxid` 로 DB 의 모든 relfrozenxid 최솟값을 `pg_database.datfrozenxid` 에 같은 방식으로 쓰고, 그 값이 올랐으면 pg_xact 의 오래된 부분을 잘라낸다.

## 위치

`commands` / `vacuum.c` L1441-L1602 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L1441-L1602))

## 실제 코드

`commands` / `vacuum.c` L1401-L1602 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L1401-L1602))

```c
// vacuum.c L1401-L1602
/*
 *	vac_update_relstats() -- update statistics for one relation
 *
 *		Update the whole-relation statistics that are kept in its pg_class
 *		row.  There are additional stats that will be updated if we are
 *		doing ANALYZE, but we always update these stats.  This routine works
 *		for both index and heap relation entries in pg_class.
 *
 *		We violate transaction semantics here by overwriting the rel's
 *		existing pg_class tuple with the new values.  This is reasonably
 *		safe as long as we're sure that the new values are correct whether or
 *		not this transaction commits.  The reason for doing this is that if
 *		we updated these tuples in the usual way, vacuuming pg_class itself
 *		wouldn't work very well --- by the time we got done with a vacuum
 *		cycle, most of the tuples in pg_class would've been obsoleted.  Of
 *		course, this only works for fixed-size not-null columns, but these are.
 *
 *		Another reason for doing it this way is that when we are in a lazy
 *		VACUUM and have PROC_IN_VACUUM set, we mustn't do any regular updates.
 *		Somebody vacuuming pg_class might think they could delete a tuple
 *		marked with xmin = our xid.
 // ... (L1422-L1439 생략: DDL 플래그(relhasindex 등)를 고쳐도 되는 조건)
 */
void
vac_update_relstats(Relation relation,
					BlockNumber num_pages, double num_tuples,
					BlockNumber num_all_visible_pages,
					BlockNumber num_all_frozen_pages,
					bool hasindex, TransactionId frozenxid,
					MultiXactId minmulti,
					bool *frozenxid_updated, bool *minmulti_updated,
					bool in_outer_xact)
{
	// ... (L1451-L1461 생략: 지역 변수)

	rd = table_open(RelationRelationId, RowExclusiveLock);

	/* Fetch a copy of the tuple to scribble on */
	ScanKeyInit(&key[0],
				Anum_pg_class_oid,
				BTEqualStrategyNumber, F_OIDEQ,
				ObjectIdGetDatum(relid));
	systable_inplace_update_begin(rd, ClassOidIndexId, true,
								  NULL, 1, key, &ctup, &inplace_state);
	if (!HeapTupleIsValid(ctup))
		elog(ERROR, "pg_class entry for relid %u vanished during vacuuming",
			 relid);
	pgcform = (Form_pg_class) GETSTRUCT(ctup);

	/* Apply statistical updates, if any, to copied tuple */

	dirty = false;
	if (pgcform->relpages != (int32) num_pages)
	{
		pgcform->relpages = (int32) num_pages;
		dirty = true;
	}
	if (pgcform->reltuples != (float4) num_tuples)
	{
		pgcform->reltuples = (float4) num_tuples;
		dirty = true;
	}
	if (pgcform->relallvisible != (int32) num_all_visible_pages)
	{
		pgcform->relallvisible = (int32) num_all_visible_pages;
		dirty = true;
	}
	if (pgcform->relallfrozen != (int32) num_all_frozen_pages)
	{
		pgcform->relallfrozen = (int32) num_all_frozen_pages;
		dirty = true;
	}
// ... (L1500-L1525 생략: relhasindex, relhasrules, relhastriggers 정리)

	/*
	 * Update relfrozenxid, unless caller passed InvalidTransactionId
	 * indicating it has no new data.
	 *
	 * Ordinarily, we don't let relfrozenxid go backwards.  However, if the
	 * stored relfrozenxid is "in the future" then it seems best to assume
	 * it's corrupt, and overwrite with the oldest remaining XID in the table.
	 * This should match vac_update_datfrozenxid() concerning what we consider
	 * to be "in the future".
	 */
	oldfrozenxid = pgcform->relfrozenxid;
	futurexid = false;
	if (frozenxid_updated)
		*frozenxid_updated = false;
	if (TransactionIdIsNormal(frozenxid) && oldfrozenxid != frozenxid)
	{
		bool		update = false;

		if (TransactionIdPrecedes(oldfrozenxid, frozenxid))
			update = true;
		else if (TransactionIdPrecedes(ReadNextTransactionId(), oldfrozenxid))
			futurexid = update = true;

		if (update)
		{
			pgcform->relfrozenxid = frozenxid;
			dirty = true;
			if (frozenxid_updated)
				*frozenxid_updated = true;
		}
	}

	// ... (L1559-L1580 생략: relminmxid (relfrozenxid 와 같은 꼴))

	/* If anything changed, write out the tuple. */
	if (dirty)
		systable_inplace_update_finish(inplace_state, ctup);
	else
		systable_inplace_update_cancel(inplace_state);

	table_close(rd, RowExclusiveLock);

	// ... (L1590-L1601 생략: 미래 값을 덮어썼다는 WARNING)
}
```

DB 단위로 올리는 쪽이다.

`commands` / `vacuum.c` L1623-L1822 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L1623-L1822))

```c
// vacuum.c L1623-L1822
void
vac_update_datfrozenxid(void)
{
	// ... (L1626-L1638 생략: 지역 변수)

	/*
	 * Restrict this task to one backend per database.  This avoids race
	 * conditions that would move datfrozenxid or datminmxid backward.  It
	 * avoids calling vac_truncate_clog() with a datfrozenxid preceding a
	 * datfrozenxid passed to an earlier vac_truncate_clog() call.
	 */
	LockDatabaseFrozenIds(ExclusiveLock);

	/*
	 * Initialize the "min" calculation with
	 * GetOldestNonRemovableTransactionId(), which is a reasonable
	 * approximation to the minimum relfrozenxid for not-yet-committed
	 * pg_class entries for new tables; see AddNewRelationTuple().  So we
	 * cannot produce a wrong minimum by starting with this.
	 */
	newFrozenXid = GetOldestNonRemovableTransactionId(NULL);

	// ... (L1657-L1661 생략: MultiXact 시작값)

	/*
	 * Identify the latest relfrozenxid and relminmxid values that we could
	 * validly see during the scan.  These are conservative values, but it's
	 * not really worth trying to be more exact.
	 */
	lastSaneFrozenXid = ReadNextTransactionId();
	lastSaneMinMulti = ReadNextMultiXactId();

	/*
	 * We must seqscan pg_class to find the minimum Xid, because there is no
	 * index that can help us here.
	 *
	 * See vac_truncate_clog() for the race condition to prevent.
	 */
	relation = table_open(RelationRelationId, AccessShareLock);

	scan = systable_beginscan(relation, InvalidOid, false,
							  NULL, 0, NULL);

	while ((classTup = systable_getnext(scan)) != NULL)
	{
		volatile FormData_pg_class *classForm = (Form_pg_class) GETSTRUCT(classTup);
		TransactionId relfrozenxid = classForm->relfrozenxid;
		TransactionId relminmxid = classForm->relminmxid;

		/*
		 * Only consider relations able to hold unfrozen XIDs (anything else
		 * should have InvalidTransactionId in relfrozenxid anyway).
		 */
		if (classForm->relkind != RELKIND_RELATION &&
			classForm->relkind != RELKIND_MATVIEW &&
			classForm->relkind != RELKIND_TOASTVALUE)
		{
			Assert(!TransactionIdIsValid(relfrozenxid));
			Assert(!MultiXactIdIsValid(relminmxid));
			continue;
		}

		// ... (L1701-L1714 생략: 값이 비어 있을 수 있고 미래 값이면 포기하는 이유)

		if (TransactionIdIsValid(relfrozenxid))
		{
			Assert(TransactionIdIsNormal(relfrozenxid));

			/* check for values in the future */
			if (TransactionIdPrecedes(lastSaneFrozenXid, relfrozenxid))
			{
				bogus = true;
				break;
			}

			/* determine new horizon */
			if (TransactionIdPrecedes(relfrozenxid, newFrozenXid))
				newFrozenXid = relfrozenxid;
		}

		// ... (L1732-L1744 생략: relminmxid (같은 꼴))
	}

	/* we're done with pg_class */
	systable_endscan(scan);
	table_close(relation, AccessShareLock);

	/* chicken out if bogus data found */
	if (bogus)
		return;

	Assert(TransactionIdIsNormal(newFrozenXid));
	Assert(MultiXactIdIsValid(newMinMulti));

	/* Now fetch the pg_database tuple we need to update. */
	relation = table_open(DatabaseRelationId, RowExclusiveLock);

	// ... (L1761-L1778 생략: pg_database 행을 제자리 갱신용으로 가져온다)

	/*
	 * As in vac_update_relstats(), we ordinarily don't want to let
	 * datfrozenxid go backward; but if it's "in the future" then it must be
	 * corrupt and it seems best to overwrite it.
	 */
	if (dbform->datfrozenxid != newFrozenXid &&
		(TransactionIdPrecedes(dbform->datfrozenxid, newFrozenXid) ||
		 TransactionIdPrecedes(lastSaneFrozenXid, dbform->datfrozenxid)))
	{
		dbform->datfrozenxid = newFrozenXid;
		dirty = true;
	}
	else
		newFrozenXid = dbform->datfrozenxid;

	// ... (L1795-L1805 생략: datminmxid (같은 꼴))
	if (dirty)
		systable_inplace_update_finish(inplace_state, tuple);
	else
		systable_inplace_update_cancel(inplace_state);

	heap_freetuple(tuple);
	table_close(relation, RowExclusiveLock);

	/*
	 * If we were able to advance datfrozenxid or datminmxid, see if we can
	 * truncate pg_xact and/or pg_multixact.  Also do it if the shared
	 * XID-wrap-limit info is stale, since this action will update that too.
	 */
	if (dirty || ForceTransactionIdLimitUpdate())
		vac_truncate_clog(newFrozenXid, newMinMulti,
						  lastSaneFrozenXid, lastSaneMinMulti);
}
```

## 동작 흐름

```text
 vac_update_relstats(rel, num_pages, num_tuples, allvisible, allfrozen, hasindex, frozenxid, ...)
 L1463  pg_class 를 RowExclusiveLock 으로 연다
 L1470  systable_inplace_update_begin                 자기 행의 사본을 얻고 버퍼를 잠근다
 L1480  relpages, reltuples, relallvisible, relallfrozen 이 다르면 바꾸고 dirty
 L1541  frozenxid 가 유효하고 다르면
          L1545  예전 값보다 새로우면 update
          L1547  예전 값이 nextXid 보다 "미래"면 손상으로 보고 update + WARNING
 L1583  dirty 면 systable_inplace_update_finish      제자리 덮어쓰기
        아니면 cancel

 vac_update_datfrozenxid
 L1646  LockDatabaseFrozenIds(ExclusiveLock)          DB 당 한 backend 만
 L1655  newFrozenXid = GetOldestNonRemovableTransactionId(NULL)   시작값
 L1682  pg_class 전체를 seqscan
          L1728  relfrozenxid 가 더 오래되면 newFrozenXid = relfrozenxid
          L1721  미래 값이 있으면 bogus -> 아무것도 안 하고 return
 L1785  datfrozenxid 보다 새로우면 덮어쓰고 dirty
 L1819  dirty 면 vac_truncate_clog                    모든 DB 의 최소 datfrozenxid 로 pg_xact 를 자른다
```

보통 UPDATE 와 제자리 갱신의 차이는 pg_class 에 무엇이 남는가다.

```text
 pg_class 의 테이블 t 행 (heap page 3, lp 5)

 보통 UPDATE 였다면
   (3,5) xmin=100 xmax=900   relfrozenxid=500      죽은 버전 하나가 남는다
   (3,9) xmin=900            relfrozenxid=700      새 버전
   VACUUM 이 끝날 때마다 pg_class 에 죽은 행이 쌓인다

 systable_inplace_update (실제)
   (3,5) xmin=100            relfrozenxid=700      같은 자리, 같은 xmin
   VACUUM 이 이 트랜잭션을 abort 해도 값은 남는다
   -> "이 트랜잭션이 커밋되든 말든 맞는 값"일 때만 쓸 수 있다 (L1409-L1412)
```

relfrozenxid 와 datfrozenxid 가 오르는 것이 XID wraparound 를 막는 마지막 고리다. 값이 오르면 그만큼 pg_xact 의 앞부분이 필요 없어진다.

```text
 DB demo 의 테이블들 (vacuum 후)
   t1.relfrozenxid  150,000,000
   t2.relfrozenxid  160,000,000
   pg_toast_t1      155,000,000
   GetOldestNonRemovableTransactionId(NULL) = 199,990,000   (시작값, 이보다 작은 것만 반영)

 newFrozenXid = min(199,990,000, 150M, 160M, 155M) = 150,000,000
 pg_database.datfrozenxid  100,000,000 -> 150,000,000   (L1785-L1791)

 vac_truncate_clog (vacuum.c L1843)
   모든 DB 의 datfrozenxid 최솟값을 frozenXID 로                  (L1924-L1926)
   TruncateCLOG(frozenXID)                                        (L1981)
   SetTransactionIdLimit(frozenXID)  -> 경고/거부 한계를 다시 잡는다 (L1991)

 pg_xact 세그먼트 파일 하나 = SLRU_PAGES_PER_SEGMENT(32) * CLOG_XACTS_PER_PAGE(32768) = 1,048,576 XID
```

## 결과가 쓰이는 곳

```text
 pg_class.relfrozenxid
      --> 다음 VACUUM 의 [07] aggressive 판정
      --> autovacuum 의 relation_needs_vacanalyze wraparound 강제 판정
 pg_class.reltuples, relpages
      --> 플래너의 행 수 추정, autovacuum 임계값 계산 ([04])
 pg_class.relallvisible
      --> index-only scan 비용 추정
 pg_database.datfrozenxid
      --> autovacuum launcher 의 DB 선택 ([03] do_start_worker)
      --> vac_truncate_clog 의 pg_xact 잘라내기
```

## 다루지 않는 것

제자리 갱신의 잠금과 무효화(`systable_inplace_update_begin`, `heap_inplace_lock`), DDL 플래그 정리, `vac_truncate_clog` 의 세부와 `TruncateCLOG`·`TruncateMultiXact`, XID 한계 경고(`SetTransactionIdLimit`), MultiXact 쪽 값은 다루지 않았다.
