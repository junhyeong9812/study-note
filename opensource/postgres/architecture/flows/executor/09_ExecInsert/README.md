# ExecInsert

상위: [executor](../README.md)

**행 하나를 테이블에 넣는 순서가 전부 이 함수에 적혀 있다.** BEFORE ROW 트리거가 값을 바꿀 기회를 먼저 받고, 그 값으로 생성 열을 계산하고, RLS 와 NOT NULL, CHECK 제약을 검사한 뒤에야 힙에 넣는다. 힙에 들어간 행의 위치(TID)를 받아 인덱스에 넣고, 유일성 위반은 이때 인덱스 쪽에서 드러난다. 마지막으로 AFTER ROW 트리거 이벤트를 큐에 쌓고, 뷰의 `WITH CHECK OPTION` 과 `RETURNING` 을 처리한다.

## 위치

`executor` / `nodeModifyTable.c` L850-L1356 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L850-L1356))

## 실제 코드

시작 부분이다. 파티션 테이블이면 실제로 넣을 파티션을 고르고, 인덱스를 열고, BEFORE ROW 트리거를 쏜다. 트리거가 `NULL` 을 돌려주면 이 행은 조용히 건너뛴다.

`executor` / `nodeModifyTable.c` L849-L913 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L849-L913))

```c
// nodeModifyTable.c L849-L913
static TupleTableSlot *
ExecInsert(ModifyTableContext *context,
		   ResultRelInfo *resultRelInfo,
		   TupleTableSlot *slot,
		   bool canSetTag,
		   TupleTableSlot **inserted_tuple,
		   ResultRelInfo **insert_destrel)
{
	ModifyTableState *mtstate = context->mtstate;
	EState	   *estate = context->estate;
	Relation	resultRelationDesc;
	List	   *recheckIndexes = NIL;
	TupleTableSlot *planSlot = context->planSlot;
	TupleTableSlot *result = NULL;
	TransitionCaptureState *ar_insert_trig_tcs;
	ModifyTable *node = (ModifyTable *) mtstate->ps.plan;
	OnConflictAction onconflict = node->onConflictAction;
	PartitionTupleRouting *proute = mtstate->mt_partition_tuple_routing;
	MemoryContext oldContext;

	/*
	 * If the input result relation is a partitioned table, find the leaf
	 * partition to insert the tuple into.
	 */
	if (proute)
	{
		ResultRelInfo *partRelInfo;

		slot = ExecPrepareTupleRouting(mtstate, estate, proute,
									   resultRelInfo, slot,
									   &partRelInfo);
		resultRelInfo = partRelInfo;
	}

	ExecMaterializeSlot(slot);

	resultRelationDesc = resultRelInfo->ri_RelationDesc;

	/*
	 * Open the table's indexes, if we have not done so already, so that we
	 * can add new index entries for the inserted tuple.
	 */
	if (resultRelationDesc->rd_rel->relhasindex &&
		resultRelInfo->ri_IndexRelationDescs == NULL)
		ExecOpenIndices(resultRelInfo, onconflict != ONCONFLICT_NONE);

	/*
	 * BEFORE ROW INSERT Triggers.
	 *
	 * Note: We fire BEFORE ROW TRIGGERS for every attempted insertion in an
	 * INSERT ... ON CONFLICT statement.  We cannot check for constraint
	 * violations before firing these triggers, because they can change the
	 * values to insert.  Also, they can run arbitrary user-defined code with
	 * side-effects that we can't cancel by just not inserting the tuple.
	 */
	if (resultRelInfo->ri_TrigDesc &&
		resultRelInfo->ri_TrigDesc->trig_insert_before_row)
	{
		/* Flush any pending inserts, so rows are visible to the triggers */
		if (estate->es_insert_pending_result_relations != NIL)
			ExecPendingInserts(estate);

		if (!ExecBRInsertTriggers(estate, resultRelInfo, slot))
			return NULL;		/* "do nothing" */
	}
```

일반 테이블 경로다. INSTEAD OF 트리거(뷰)와 외래 테이블 경로는 줄였다. 생성 열 계산, RLS 정책, 제약, 파티션 제약 검사가 이 순서로 온다.

`executor` / `nodeModifyTable.c` L915-L1108 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L915-L1108))

```c
// nodeModifyTable.c L915-L1108
	/* INSTEAD OF ROW INSERT Triggers */
	if (resultRelInfo->ri_TrigDesc &&
		resultRelInfo->ri_TrigDesc->trig_insert_instead_row)
	{
		if (!ExecIRInsertTriggers(estate, resultRelInfo, slot))
			return NULL;		/* "do nothing" */
	}
	// ... (L922-L1046 생략: 외래 테이블이면 FDW 의 ExecForeignInsert (배치 포함))
	else
	{
		WCOKind		wco_kind;

		/*
		 * Constraints and GENERATED expressions might reference the tableoid
		 * column, so (re-)initialize tts_tableOid before evaluating them.
		 */
		slot->tts_tableOid = RelationGetRelid(resultRelationDesc);

		/*
		 * Compute stored generated columns
		 */
		if (resultRelationDesc->rd_att->constr &&
			resultRelationDesc->rd_att->constr->has_generated_stored)
			ExecComputeStoredGenerated(resultRelInfo, estate, slot,
									   CMD_INSERT);

		/*
		 * Check any RLS WITH CHECK policies.
		 *
		 * Normally we should check INSERT policies. But if the insert is the
		 * result of a partition key update that moved the tuple to a new
		 * partition, we should instead check UPDATE policies, because we are
		 * executing policies defined on the target table, and not those
		 * defined on the child partitions.
		 *
		 * If we're running MERGE, we refer to the action that we're executing
		 * to know if we're doing an INSERT or UPDATE to a partition table.
		 */
		if (mtstate->operation == CMD_UPDATE)
			wco_kind = WCO_RLS_UPDATE_CHECK;
		else if (mtstate->operation == CMD_MERGE)
			wco_kind = (mtstate->mt_merge_action->mas_action->commandType == CMD_UPDATE) ?
				WCO_RLS_UPDATE_CHECK : WCO_RLS_INSERT_CHECK;
		else
			wco_kind = WCO_RLS_INSERT_CHECK;

		/*
		 * ExecWithCheckOptions() will skip any WCOs which are not of the kind
		 * we are looking for at this point.
		 */
		if (resultRelInfo->ri_WithCheckOptions != NIL)
			ExecWithCheckOptions(wco_kind, resultRelInfo, slot, estate);

		/*
		 * Check the constraints of the tuple.
		 */
		if (resultRelationDesc->rd_att->constr)
			ExecConstraints(resultRelInfo, slot, estate);

		/*
		 * Also check the tuple against the partition constraint, if there is
		 * one; except that if we got here via tuple-routing, we don't need to
		 * if there's no BR trigger defined on the partition.
		 */
		if (resultRelationDesc->rd_rel->relispartition &&
			(resultRelInfo->ri_RootResultRelInfo == NULL ||
			 (resultRelInfo->ri_TrigDesc &&
			  resultRelInfo->ri_TrigDesc->trig_insert_before_row)))
			ExecPartitionCheck(resultRelInfo, slot, estate, true);

```

힙과 인덱스에 넣는 부분이다. `ON CONFLICT` 가 있으면 추측 삽입(speculative insertion)을 하는데, 그 경로는 줄였다.

`executor` / `nodeModifyTable.c` L1109-L1245 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L1109-L1245))

```c
// nodeModifyTable.c L1109-L1245
		if (onconflict != ONCONFLICT_NONE && resultRelInfo->ri_NumIndices > 0)
		{
			// ... (L1111-L1229 생략: ON CONFLICT 의 추측 삽입 (사전 충돌 검사, 추측 토큰, 재시도))
		}
		else
		{
			/* insert the tuple normally */
			table_tuple_insert(resultRelationDesc, slot,
							   estate->es_output_cid,
							   0, NULL);

			/* insert index entries for tuple */
			if (resultRelInfo->ri_NumIndices > 0)
				recheckIndexes = ExecInsertIndexTuples(resultRelInfo,
													   slot, estate, false,
													   false, NULL, NIL,
													   false);
		}
	}
```

뒷부분이다. 처리 행 수를 올리고, AFTER ROW 트리거를 큐에 쌓고, 뷰 검사와 RETURNING 을 한다.

`executor` / `nodeModifyTable.c` L1247-L1356 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L1247-L1356))

```c
// nodeModifyTable.c L1247-L1356
	if (canSetTag)
		(estate->es_processed)++;

	// ... (L1250-L1274 생략: 파티션 키 UPDATE 로 옮겨 온 행의 전이 테이블 처리)

	/* AFTER ROW INSERT Triggers */
	ExecARInsertTriggers(estate, resultRelInfo, slot, recheckIndexes,
						 ar_insert_trig_tcs);

	list_free(recheckIndexes);

	/*
	 * Check any WITH CHECK OPTION constraints from parent views.  We are
	 * required to do this after testing all constraints and uniqueness
	 * violations per the SQL spec, so we do it after actually inserting the
	 * record into the heap and all indexes.
	 *
	 * ExecWithCheckOptions will elog(ERROR) if a violation is found, so the
	 * tuple will never be seen, if it violates the WITH CHECK OPTION.
	 *
	 * ExecWithCheckOptions() will skip any WCOs which are not of the kind we
	 * are looking for at this point.
	 */
	if (resultRelInfo->ri_WithCheckOptions != NIL)
		ExecWithCheckOptions(WCO_VIEW_CHECK, resultRelInfo, slot, estate);

	/* Process RETURNING if present */
	if (resultRelInfo->ri_projectReturning)
	{
		TupleTableSlot *oldSlot = NULL;

		// ... (L1302-L1330 생략: 파티션 간 UPDATE 의 OLD 행 변환)

		result = ExecProcessReturning(context, resultRelInfo, CMD_INSERT,
									  oldSlot, slot, planSlot);

		/*
		 * For a cross-partition UPDATE, release the old tuple, first making
		 * sure that the result slot has a local copy of any pass-by-reference
		 * values.
		 */
		if (context->cpDeletedSlot)
		{
			ExecMaterializeSlot(result);
			ExecClearTuple(oldSlot);
			if (context->cpDeletedSlot != oldSlot)
				ExecClearTuple(context->cpDeletedSlot);
			context->cpDeletedSlot = NULL;
		}
	}

	if (inserted_tuple)
		*inserted_tuple = slot;
	if (insert_destrel)
		*insert_destrel = resultRelInfo;

	return result;
}
```

AFTER ROW 트리거는 여기서 실행하지 않는다. 이벤트를 저장할 뿐이다.

`commands` / `trigger.c` L2548-L2572 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/commands/trigger.c#L2548-L2572))

```c
// trigger.c L2548-L2572
void
ExecARInsertTriggers(EState *estate, ResultRelInfo *relinfo,
					 TupleTableSlot *slot, List *recheckIndexes,
					 TransitionCaptureState *transition_capture)
{
	TriggerDesc *trigdesc = relinfo->ri_TrigDesc;

	if (relinfo->ri_FdwRoutine && transition_capture &&
		transition_capture->tcs_insert_new_table)
	{
		Assert(relinfo->ri_RootResultRelInfo);
		ereport(ERROR,
				(errcode(ERRCODE_FEATURE_NOT_SUPPORTED),
				 errmsg("cannot collect transition tuples from child foreign tables")));
	}

	if ((trigdesc && trigdesc->trig_insert_after_row) ||
		(transition_capture && transition_capture->tcs_insert_new_table))
		AfterTriggerSaveEvent(estate, relinfo, NULL, NULL,
							  TRIGGER_EVENT_INSERT,
							  true, NULL, slot,
							  recheckIndexes, NULL,
							  transition_capture,
							  false);
}
```

제약 검사는 NOT NULL 을 열 순서대로 먼저 보고, 그다음 CHECK 를 본다.

`executor` / `execMain.c` L1983-L2034 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execMain.c#L1983-L2034))

```c
// execMain.c L1983-L2034
void
ExecConstraints(ResultRelInfo *resultRelInfo,
				TupleTableSlot *slot, EState *estate)
{
	Relation	rel = resultRelInfo->ri_RelationDesc;
	TupleDesc	tupdesc = RelationGetDescr(rel);
	TupleConstr *constr = tupdesc->constr;
	Bitmapset  *modifiedCols;
	List	   *notnull_virtual_attrs = NIL;

	Assert(constr);				/* we should not be called otherwise */

	/*
	 * Verify not-null constraints.
	 *
	 * Not-null constraints on virtual generated columns are collected and
	 * checked separately below.
	 */
	if (constr->has_not_null)
	{
		for (AttrNumber attnum = 1; attnum <= tupdesc->natts; attnum++)
		{
			Form_pg_attribute att = TupleDescAttr(tupdesc, attnum - 1);

			if (att->attnotnull && att->attgenerated == ATTRIBUTE_GENERATED_VIRTUAL)
				notnull_virtual_attrs = lappend_int(notnull_virtual_attrs, attnum);
			else if (att->attnotnull && slot_attisnull(slot, attnum))
				ReportNotNullViolationError(resultRelInfo, slot, estate, attnum);
		}
	}

	/*
	 * Verify not-null constraints on virtual generated column, if any.
	 */
	if (notnull_virtual_attrs)
	{
		AttrNumber	attnum;

		attnum = ExecRelGenVirtualNotNull(resultRelInfo, slot, estate,
										  notnull_virtual_attrs);
		if (attnum != InvalidAttrNumber)
			ReportNotNullViolationError(resultRelInfo, slot, estate, attnum);
	}

	/*
	 * Verify check constraints.
	 */
	if (rel->rd_rel->relchecks > 0)
	{
		const char *failed;

		if ((failed = ExecRelCheck(resultRelInfo, slot, estate)) != NULL)
```

## 동작 흐름

```text
 L873  파티션 라우팅이 있으면 ExecPrepareTupleRouting -> resultRelInfo = 리프 파티션
 L883  ExecMaterializeSlot(slot)               슬롯이 자기 사본을 갖게 한다
 L891  인덱스가 있는데 아직 안 열었으면 ExecOpenIndices   첫 행에서만

 L904  BEFORE ROW INSERT 트리거가 있으면
 L908    미뤄 둔 배치 삽입을 먼저 흘린다
 L911    ExecBRInsertTriggers                   false 면 L912 return NULL ("do nothing")
 L916  INSTEAD OF ROW 트리거 (뷰)               false 면 return NULL
 L922  외래 테이블이면 FDW 경로                  (생략)
 L1047 일반 테이블
 L1055   tts_tableOid 설정
 L1060   GENERATED STORED 열 계산               BEFORE 트리거가 바꾼 값을 보고 계산한다
 L1077   RLS WITH CHECK 정책 종류 고르기
 L1090   ExecWithCheckOptions(WCO_RLS_...)      정책 위반이면 ERROR
 L1096   ExecConstraints                         NOT NULL -> CHECK
 L1103   파티션이고 (직접 넣었거나 BR 트리거가 있으면) ExecPartitionCheck

 L1109   ON CONFLICT 이고 인덱스가 있으면 추측 삽입     (생략)
 L1231   아니면
 L1234     table_tuple_insert(rel, slot, es_output_cid, 0, NULL)   --> [행 쓰기와 WAL 기록]
             돌아오면 slot->tts_tid 에 힙 위치(블록, 줄)가 들어 있다
 L1239     인덱스가 있으면
 L1240       ExecInsertIndexTuples(resultRelInfo, slot, estate, ...)  --> [nbtree 삽입과 분할]
               slot->tts_tid 를 인덱스 항목의 TID 로 쓴다 (execIndexing.c L319)

 L1247 canSetTag 면 es_processed++
 L1277 ExecARInsertTriggers                     AFTER ROW 이벤트를 큐에 저장
 L1294 WITH CHECK OPTION (뷰)                   힙, 인덱스에 다 넣은 뒤 검사 (L1282-L1287 주석)
 L1298 RETURNING 이 있으면 ExecProcessReturning -> result
 L1355 return result                             RETURNING 이 없으면 NULL
```

검사와 쓰기의 순서를 한 줄로 세우면 아래와 같다. 앞쪽 검사에 걸리면 힙에 아무것도 쓰지 않고 끝나지만, 유일성 위반은 힙에 행을 넣은 뒤 인덱스에서 걸린다.

```text
 행 하나 (일반 테이블, ON CONFLICT 없음)

     함수                          줄      하는 일과 여기서 실패하면
  1  ExecBRInsertTriggers          L911    BEFORE ROW 트리거. 힙에 쓴 것 없음 (NULL 이면 조용히 건너뜀)
  2  ExecComputeStoredGenerated    L1062   생성 열 계산. 힙에 쓴 것 없음
  3  ExecWithCheckOptions          L1090   RLS 정책. 힙에 쓴 것 없음
  4  ExecConstraints               L1096   NOT NULL, CHECK. 힙에 쓴 것 없음
  5  ExecPartitionCheck            L1107   파티션 제약. 힙에 쓴 것 없음
  6  table_tuple_insert            L1234   힙 삽입과 WAL 기록
  7  ExecInsertIndexTuples         L1240   인덱스 삽입. 힙에는 이미 들어갔다
  8  ExecARInsertTriggers          L1277   AFTER ROW 이벤트를 큐에 쌓는다. 실행은 [10]
  9  ExecWithCheckOptions          L1295   뷰 WITH CHECK OPTION. 힙, 인덱스에 이미 들어갔다
 10  ExecProcessReturning          L1332   RETURNING

 7 의 유일성 검사 (execIndexing.c)
   유일 인덱스이고 즉시 검사면 UNIQUE_CHECK_YES (L435)
     index AM 이 중복을 보면 ERROR -> 트랜잭션 abort -> 6 에서 넣은 힙 행은 죽은 행으로 남는다
   DEFERRABLE 이면 UNIQUE_CHECK_PARTIAL (L437)
     의심 인덱스를 recheckIndexes 로 돌려주고 (L512), 8 의 AFTER ROW 이벤트에 실려
     unique_key_recheck 제약 트리거가 나중에 다시 본다 (catalog/index.c L2048-L2051)
```

인덱스 삽입이 힙 삽입 뒤에 오는 이유는 인덱스 항목이 힙 위치를 가리켜야 하기 때문이다. 힙 쪽이 TID 를 슬롯에 적어 돌려주고, 인덱스 쪽이 그 TID 를 받아 쓴다.

```text
 slot->tts_tid 가 건너가는 길

 [09] L1234 table_tuple_insert
        -> heapam_tuple_insert                    access/heap/heapam_handler.c L244
             heap_insert(...)                      L255  힙 페이지에 넣고 tuple->t_self 에 TID
             ItemPointerCopy(&tuple->t_self, &slot->tts_tid)   L256
 [09] L1240 ExecInsertIndexTuples(resultRelInfo, slot, ...)
        tupleid = &slot->tts_tid                  execIndexing.c L319
        인덱스마다 index_insert(..., tupleid, heapRelation, checkUnique, ...)  L450
                                                     --> [nbtree 삽입과 분할] 의 btinsert

 예: t2 의 블록 7, 줄 3 에 들어갔다면 tts_tid = (7,3)
     t2 의 인덱스 둘(pk, idx_b)에 각각 (키, (7,3)) 항목이 생긴다
```

RETURNING 과 AFTER ROW 트리거가 보는 값은 BEFORE ROW 트리거가 바꾼 뒤의 값이다. 슬롯 하나가 처음부터 끝까지 같은 행을 들고 가기 때문이다.

```text
 BEFORE ROW 트리거가 NEW.b := 99 로 바꾼 경우  (입력 행 (a=12, b=1))

 단계                    슬롯 내용
 [08] ExecGetInsertNewTuple    (12, 1)
 L911 ExecBRInsertTriggers     (12, 99)    트리거가 돌려준 행을 슬롯에 넣는다 (trigger.c L2520)
 L1096 ExecConstraints         (12, 99)    CHECK (b < 50) 이 있으면 여기서 ERROR
 L1234 table_tuple_insert      (12, 99)    힙에 들어가는 값
 L1277 AFTER ROW 큐            (12, 99)
 L1332 RETURNING b             99
```

## 결과가 쓰이는 곳

```text
 힙 행과 인덱스 항목
      --> 이 트랜잭션이 커밋하면 다른 스냅샷에 보인다 --> [커밋], [MVCC 가시성과 스냅샷]
 estate->es_processed
      --> "INSERT 0 3" 의 3
 AFTER ROW 이벤트 (recheckIndexes 포함)
      --> [10] AfterTriggerEndQuery 가 실행한다
      --> DEFERRABLE 유일 제약의 재검사(unique_key_recheck)도 이 큐로 간다
 result (RETURNING 슬롯)
      --> [08] ExecModifyTable 이 그대로 위로 돌려준다
```

## 다루지 않는 것

`INSERT ... ON CONFLICT` 의 추측 삽입(`ExecCheckIndexConstraints`, `SpeculativeInsertionLockAcquire`, `table_tuple_insert_speculative`, `ExecOnConflictUpdate`), 외래 테이블과 배치 삽입(`ExecForeignInsert`, `ExecBatchInsert`), 파티션 라우팅(`ExecPrepareTupleRouting`), 트리거 함수 호출 자체(`ExecCallTriggerFunc`), 생성 열 계산(`ExecComputeStoredGenerated`), RLS 정책 구성, 배제 제약(exclusion constraint)은 행 삽입의 곁가지라 요약만 했다.
