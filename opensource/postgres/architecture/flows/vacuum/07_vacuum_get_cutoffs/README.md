# vacuum_get_cutoffs

상위: [vacuum](../README.md)

**이번 VACUUM 의 세 기준선을 계산한다.** OldestXmin 은 "이보다 먼저 끝난 트랜잭션이 지운 행은 아무도 못 본다"는 선이라 삭제와 freeze 의 상한이 되고, FreezeLimit 은 "이보다 오래된 XID 는 반드시 얼린다"는 선이며, 반환값은 이번 VACUUM 이 aggressive(all-visible 페이지도 건너뛰지 않고 relfrozenxid 를 FreezeLimit 이상으로 반드시 올린다)인지다. OldestXmin 은 ProcArray 에서 구하고, FreezeLimit 과 aggressive 판정선(`aggressiveXIDCutoff`)은 `nextXid` 에서 나이를 빼서 만들며, FreezeLimit 은 OldestXmin 을 넘지 못하게 깎는다. MultiXact 쪽도 같은 모양(`MultiXactCutoff` 는 `nextMXID` 에서 나이를 빼고 `OldestMxact` 로 깎는다)이다. 오래 열린 트랜잭션이 OldestXmin 을 붙잡으면 FreezeLimit 도 함께 붙잡힌다.

## 위치

`commands` / `vacuum.c` L1115-L1274 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L1115-L1274))

## 실제 코드

`commands` / `vacuum.c` L1103-L1274 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/vacuum.c#L1103-L1274))

```c
// vacuum.c L1103-L1274
/*
 * vacuum_get_cutoffs() -- compute OldestXmin and freeze cutoff points
 *
 * The target relation and VACUUM parameters are our inputs.
 *
 * Output parameters are the cutoffs that VACUUM caller should use.
 *
 * Return value indicates if vacuumlazy.c caller should make its VACUUM
 * operation aggressive.  An aggressive VACUUM must advance relfrozenxid up to
 * FreezeLimit (at a minimum), and relminmxid up to MultiXactCutoff (at a
 * minimum).
 */
bool
vacuum_get_cutoffs(Relation rel, const VacuumParams *params,
				   // ... (L1117-L1136 생략: 지역 변수와 params 의 나이 값 복사)
	/* Set pg_class fields in cutoffs */
	cutoffs->relfrozenxid = rel->rd_rel->relfrozenxid;
	cutoffs->relminmxid = rel->rd_rel->relminmxid;

	/*
	 * Acquire OldestXmin.
	 *
	 * We can always ignore processes running lazy vacuum.  This is because we
	 * use these values only for deciding which tuples we must keep in the
	 * tables.  Since lazy vacuum doesn't write its XID anywhere (usually no
	 * XID assigned), it's safe to ignore it.  In theory it could be
	 * problematic to ignore lazy vacuums in a full vacuum, but keep in mind
	 * that only one vacuum process can be working on a particular table at
	 * any time, and that each vacuum is always an independent transaction.
	 */
	cutoffs->OldestXmin = GetOldestNonRemovableTransactionId(rel);

	Assert(TransactionIdIsNormal(cutoffs->OldestXmin));

	// ... (L1156-L1159 생략: OldestMxact)
	/* Acquire next XID/next MXID values used to apply age-based settings */
	nextXID = ReadNextTransactionId();
	// ... (L1162-L1170 생략: MultiXact 다음 값과 실효 freeze 나이)
	/*
	 * Almost ready to set freeze output parameters; check if OldestXmin or
	 * OldestMxact are held back to an unsafe degree before we start on that
	 */
	safeOldestXmin = nextXID - autovacuum_freeze_max_age;
	if (!TransactionIdIsNormal(safeOldestXmin))
		safeOldestXmin = FirstNormalTransactionId;
	// ... (L1178-L1180 생략: MultiXact 안전선)
	if (TransactionIdPrecedes(cutoffs->OldestXmin, safeOldestXmin))
		ereport(WARNING,
				(errmsg("cutoff for removing and freezing tuples is far in the past"),
				 errhint("Close open transactions soon to avoid wraparound problems.\n"
						 "You might also need to commit or roll back old prepared transactions, or drop stale replication slots.")));
	// ... (L1186-L1190 생략: MultiXact 경고)

	/*
	 * Determine the minimum freeze age to use: as specified by the caller, or
	 * vacuum_freeze_min_age, but in any case not more than half
	 * autovacuum_freeze_max_age, so that autovacuums to prevent XID
	 * wraparound won't occur too frequently.
	 */
	if (freeze_min_age < 0)
		freeze_min_age = vacuum_freeze_min_age;
	freeze_min_age = Min(freeze_min_age, autovacuum_freeze_max_age / 2);
	Assert(freeze_min_age >= 0);

	/* Compute FreezeLimit, being careful to generate a normal XID */
	cutoffs->FreezeLimit = nextXID - freeze_min_age;
	if (!TransactionIdIsNormal(cutoffs->FreezeLimit))
		cutoffs->FreezeLimit = FirstNormalTransactionId;
	/* FreezeLimit must always be <= OldestXmin */
	if (TransactionIdPrecedes(cutoffs->OldestXmin, cutoffs->FreezeLimit))
		cutoffs->FreezeLimit = cutoffs->OldestXmin;

	// ... (L1211-L1230 생략: MultiXactCutoff (XID 와 같은 꼴))
	/*
	 * Finally, figure out if caller needs to do an aggressive VACUUM or not.
	 *
	 * Determine the table freeze age to use: as specified by the caller, or
	 * the value of the vacuum_freeze_table_age GUC, but in any case not more
	 * than autovacuum_freeze_max_age * 0.95, so that if you have e.g nightly
	 * VACUUM schedule, the nightly VACUUM gets a chance to freeze XIDs before
	 * anti-wraparound autovacuum is launched.
	 */
	if (freeze_table_age < 0)
		freeze_table_age = vacuum_freeze_table_age;
	freeze_table_age = Min(freeze_table_age, autovacuum_freeze_max_age * 0.95);
	Assert(freeze_table_age >= 0);
	aggressiveXIDCutoff = nextXID - freeze_table_age;
	if (!TransactionIdIsNormal(aggressiveXIDCutoff))
		aggressiveXIDCutoff = FirstNormalTransactionId;
	if (TransactionIdPrecedesOrEquals(cutoffs->relfrozenxid,
									  aggressiveXIDCutoff))
		return true;

	// ... (L1251-L1270 생략: MultiXact 기준 aggressive 판정 (XID 와 같은 꼴))

	/* Non-aggressive VACUUM */
	return false;
}
```

## 동작 흐름

```text
 vacuum_get_cutoffs(rel, params, cutoffs)
 L1138  cutoffs->relfrozenxid = pg_class.relfrozenxid
 L1152  OldestXmin = GetOldestNonRemovableTransactionId(rel)     procarray.c L2005 -> ComputeXidHorizons
 L1161  nextXID = ReadNextTransactionId()
 L1175  safeOldestXmin = nextXID - autovacuum_freeze_max_age     OldestXmin 이 이보다 오래면 WARNING
 L1198  freeze_min_age = -1 이면 vacuum_freeze_min_age
 L1200    단 autovacuum_freeze_max_age / 2 를 넘지 않는다
 L1204  FreezeLimit = nextXID - freeze_min_age
 L1208    OldestXmin 보다 새로우면 OldestXmin 으로 깎는다
 L1224  MultiXactCutoff = nextMXID - multixact_freeze_min_age     (L1219 에서 effective_multixact_freeze_max_age / 2 로 상한)
 L1229    OldestMxact (L1157) 보다 새로우면 OldestMxact 로 깎는다
 L1240  freeze_table_age = -1 이면 vacuum_freeze_table_age
 L1242    단 autovacuum_freeze_max_age * 0.95 를 넘지 않는다
 L1244  aggressiveXIDCutoff = nextXID - freeze_table_age
 L1247  relfrozenxid <= aggressiveXIDCutoff 이면 return true (aggressive)
 L1268  relminmxid <= aggressiveMXIDCutoff 이면 return true     MultiXact 나이로도 aggressive 가 된다
 L1273  return false
```

기본 설정(`vacuum_freeze_min_age` 5 천만, `vacuum_freeze_table_age` 1 억 5 천만, `autovacuum_freeze_max_age` 2 억, guc_tables.c L2800, L2810, L3584)으로 계산한 값이다. XID 가 2 억 개 쓰인 클러스터에서 짧은 트랜잭션만 돌고 있는 경우와, 오래된 트랜잭션 하나가 OldestXmin 을 붙잡은 경우를 나란히 놓았다.

```text
 nextXID = 200,000,000
 A: 짧은 트랜잭션만 돈다
 B: XID 120,000,000 이 연 트랜잭션이 아직 열려 있다

                       line    A                          B
 OldestXmin            L1152   199,990,000                120,000,000
 safeOldestXmin        L1175   200M - 200M = 0 -> 3       0 -> 3   (no WARNING)
 freeze_min_age        L1200   min(50M, 100M) = 50M       50M
 FreezeLimit           L1204   150,000,000                150,000,000
                       L1208   150,000,000 (kept)         120,000,000 (clamped to OldestXmin)
 freeze_table_age      L1242   min(150M, 190M) = 150M     150M
 aggressiveXIDCutoff   L1244   50,000,000                 50,000,000

 relfrozenxid = 40,000,000  -> 40M <= 50M -> aggressive
 relfrozenxid = 100,000,000 -> 일반 (all-visible 페이지를 건너뛸 수 있다)
```

세 선이 XID 축 위에 놓이는 순서는 늘 같다. FreezeLimit ≤ OldestXmin < nextXID 이고, relfrozenxid 는 그보다 왼쪽 어딘가다(A, relfrozenxid 40M 기준).

```text
 XID -->
   40M        50M                   150M                199.99M     200M
   |----------|---------------------|-------------------|-----------|
   R          C                     F                   O           N

 R  relfrozenxid          이 테이블에 남아 있을 수 있는 가장 오래된 XID
 C  aggressiveXIDCutoff   R 이 이보다 오래면 aggressive
 F  FreezeLimit           이보다 오래된 XID 가 있는 페이지는 반드시 얼린다
 O  OldestXmin            이보다 먼저 끝난 트랜잭션이 지운 행은 치울 수 있다
 N  nextXID               다음에 나눠 줄 XID
```

## 결과가 쓰이는 곳

```text
 cutoffs->OldestXmin
      --> [10] heap_prune_satisfies_vacuum 이 xmax < OldestXmin 인 RECENTLY_DEAD 를 DEAD 로 본다
      --> heap_prepare_freeze_tuple 이 xmin < OldestXmin 이면 얼릴 수 있다고 본다
      --> [06] 이 NewRelfrozenXid 의 시작값으로 쓴다
 cutoffs->FreezeLimit
      --> heap_tuple_should_freeze: xmin < FreezeLimit 이면 그 페이지를 반드시 얼린다
 반환값 aggressive
      --> [08] find_next_unskippable_block 이 all-visible 페이지를 건너뛸 수 있는지
```

## 다루지 않는 것

MultiXact 기준선의 세부(`MultiXactMemberFreezeThreshold` 가 member 공간 부족 때 나이를 줄이는 규칙, `MultiXactCutoff` 가 freeze 에서 쓰이는 방식), `GetOldestNonRemovableTransactionId` 가 공유 카탈로그·임시 테이블·복제 슬롯을 나눠 계산하는 방식(`ComputeXidHorizons`), wraparound failsafe 의 기준(`vacuum_failsafe_age`)은 다루지 않았다.
