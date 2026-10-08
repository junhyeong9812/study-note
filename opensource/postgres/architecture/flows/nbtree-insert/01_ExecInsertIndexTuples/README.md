# ExecInsertIndexTuples

상위: [nbtree 삽입과 분할](../README.md)

**힙에 행을 넣은 뒤, 그 테이블의 인덱스마다 인덱스 튜플 하나씩을 넣는 executor 쪽 입구다.** 인덱스마다 유일성 검사 방식(`checkUnique`)을 정하고 `index_insert` 를 부른다. 인덱스 AM 이 무엇이든 여기까지는 같고, B-tree 로 갈라지는 것은 다음 단계다.

## 위치

`executor` / `execIndexing.c` L310-L519 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execIndexing.c#L310-L519))

## 실제 코드

함수 머리다. 넣을 힙 튜플의 TID 는 슬롯에 이미 들어 있다. 힙 삽입이 먼저 끝났다는 뜻이다.

`executor` / `execIndexing.c` L310-L350 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execIndexing.c#L310-L350))

```c
// execIndexing.c L310-L350
ExecInsertIndexTuples(ResultRelInfo *resultRelInfo,
					  TupleTableSlot *slot,
					  EState *estate,
					  bool update,
					  bool noDupErr,
					  bool *specConflict,
					  List *arbiterIndexes,
					  bool onlySummarizing)
{
	ItemPointer tupleid = &slot->tts_tid;
	List	   *result = NIL;
	int			i;
	int			numIndices;
	RelationPtr relationDescs;
	Relation	heapRelation;
	IndexInfo **indexInfoArray;
	ExprContext *econtext;
	Datum		values[INDEX_MAX_KEYS];
	bool		isnull[INDEX_MAX_KEYS];

	Assert(ItemPointerIsValid(tupleid));

	/*
	 * Get information from the result relation info structure.
	 */
	numIndices = resultRelInfo->ri_NumIndices;
	relationDescs = resultRelInfo->ri_IndexRelationDescs;
	indexInfoArray = resultRelInfo->ri_IndexRelationInfo;
	heapRelation = resultRelInfo->ri_RelationDesc;

	/* Sanity check: slot must belong to the same rel as the resultRelInfo. */
	Assert(slot->tts_tableOid == RelationGetRelid(heapRelation));

	/*
	 * We will use the EState's per-tuple context for evaluating predicates
	 * and index expressions (creating it if it's not already there).
	 */
	econtext = GetPerTupleExprContext(estate);

	/* Arrange for econtext's scan tuple to be the tuple under test */
	econtext->ecxt_scantuple = slot;
```

인덱스마다 한 바퀴를 돈다. 부분 인덱스 조건을 보고, 인덱스 키 값을 계산하고, 유일성 검사 방식을 정해서 `index_insert` 로 넘긴다.

`executor` / `execIndexing.c` L355-L457 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execIndexing.c#L355-L457))

```c
// execIndexing.c L355-L457
	for (i = 0; i < numIndices; i++)
	{
		Relation	indexRelation = relationDescs[i];
		IndexInfo  *indexInfo;
		bool		applyNoDupErr;
		IndexUniqueCheck checkUnique;
		bool		indexUnchanged;
		bool		satisfiesConstraint;

		if (indexRelation == NULL)
			continue;

		indexInfo = indexInfoArray[i];

		/* If the index is marked as read-only, ignore it */
		if (!indexInfo->ii_ReadyForInserts)
			continue;

		/*
		 * Skip processing of non-summarizing indexes if we only update
		 * summarizing indexes
		 */
		if (onlySummarizing && !indexInfo->ii_Summarizing)
			continue;

		/* Check for partial index */
		if (indexInfo->ii_Predicate != NIL)
		{
			ExprState  *predicate;

			/*
			 * If predicate state not set up yet, create it (in the estate's
			 * per-query context)
			 */
			predicate = indexInfo->ii_PredicateState;
			if (predicate == NULL)
			{
				predicate = ExecPrepareQual(indexInfo->ii_Predicate, estate);
				indexInfo->ii_PredicateState = predicate;
			}

			/* Skip this index-update if the predicate isn't satisfied */
			if (!ExecQual(predicate, econtext))
				continue;
		}

		/*
		 * FormIndexDatum fills in its values and isnull parameters with the
		 * appropriate values for the column(s) of the index.
		 */
		FormIndexDatum(indexInfo,
					   slot,
					   estate,
					   values,
					   isnull);

		/* Check whether to apply noDupErr to this index */
		applyNoDupErr = noDupErr &&
			(arbiterIndexes == NIL ||
			 list_member_oid(arbiterIndexes,
							 indexRelation->rd_index->indexrelid));

		/*
		 * The index AM does the actual insertion, plus uniqueness checking.
		 *
		 * For an immediate-mode unique index, we just tell the index AM to
		 * throw error if not unique.
		 *
		 * For a deferrable unique index, we tell the index AM to just detect
		 * possible non-uniqueness, and we add the index OID to the result
		 * list if further checking is needed.
		 *
		 * For a speculative insertion (used by INSERT ... ON CONFLICT), do
		 * the same as for a deferrable unique index.
		 */
		if (!indexRelation->rd_index->indisunique)
			checkUnique = UNIQUE_CHECK_NO;
		else if (applyNoDupErr)
			checkUnique = UNIQUE_CHECK_PARTIAL;
		else if (indexRelation->rd_index->indimmediate)
			checkUnique = UNIQUE_CHECK_YES;
		else
			checkUnique = UNIQUE_CHECK_PARTIAL;

		/*
		 * There's definitely going to be an index_insert() call for this
		 * index.  If we're being called as part of an UPDATE statement,
		 * consider if the 'indexUnchanged' = true hint should be passed.
		 */
		indexUnchanged = update && index_unchanged_by_update(resultRelInfo,
															 estate,
															 indexInfo,
															 indexRelation);

		satisfiesConstraint =
			index_insert(indexRelation, /* index relation */
						 values,	/* array of index Datums */
						 isnull,	/* null flags */
						 tupleid,	/* tid of heap tuple */
						 heapRelation,	/* heap relation */
						 checkUnique,	/* type of uniqueness check to do */
						 indexUnchanged,	/* UPDATE without logical change? */
						 indexInfo);	/* index AM may need this */
```

배제 제약(exclusion constraint) 검사를 건너뛰면, 남은 일은 "다시 확인해야 할 인덱스" 목록을 모으는 것이다.

`executor` / `execIndexing.c` L502-L519 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/execIndexing.c#L502-L519))

```c
// execIndexing.c L502-L519
		if ((checkUnique == UNIQUE_CHECK_PARTIAL ||
			 indexInfo->ii_ExclusionOps != NULL) &&
			!satisfiesConstraint)
		{
			/*
			 * The tuple potentially violates the uniqueness or exclusion
			 * constraint, so make a note of the index so that we can re-check
			 * it later.  Speculative inserters are told if there was a
			 * speculative conflict, since that always requires a restart.
			 */
			result = lappend_oid(result, RelationGetRelid(indexRelation));
			if (indexRelation->rd_index->indimmediate && specConflict)
				*specConflict = true;
		}
	}

	return result;
}
```

일반 `INSERT` 는 힙에 넣은 직후 이 함수를 부른다.

`executor` / `nodeModifyTable.c` L1229-L1243 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/executor/nodeModifyTable.c#L1229-L1243))

```c
// nodeModifyTable.c L1229-L1243
			/* Since there was no insertion conflict, we're done */
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
```

## 동작 흐름

```text
 ExecInsert (nodeModifyTable.c)
   L1234  table_tuple_insert         힙에 먼저 넣는다. slot->tts_tid 가 정해진다
   L1240  ExecInsertIndexTuples      그 TID 를 인덱스마다 넣는다
            |
            v
 L355  for (i = 0; i < numIndices; i++)
 L364    indexRelation == NULL        -> 건너뜀
 L370    !ii_ReadyForInserts          -> 건너뜀 (CREATE INDEX CONCURRENTLY 준비 중)
 L377    onlySummarizing 이고 요약 인덱스가 아님 -> 건너뜀
 L381    부분 인덱스면 WHERE 조건을 평가, 거짓이면 건너뜀 (L397)
 L405    FormIndexDatum               표현식 인덱스면 여기서 식을 계산한다
 L430    checkUnique 결정 (아래 표)
 L444    indexUnchanged = UPDATE 인데 인덱스 키가 안 바뀌었나 (힌트)
 L449    index_insert(...)            --> [02]
 L502    PARTIAL 인데 false 가 돌아왔으면 result 목록에 이 인덱스 OID 추가
 L518  return result                  호출자가 지연 재검사에 쓴다
```

유일성 검사 방식은 네 줄로 정해진다. 여기서 정한 값이 [06] `_bt_check_unique` 의 행동을 가른다.

```text
 checkUnique 결정 (L430-L437)

 L430  !indisunique           UNIQUE_CHECK_NO        검사 안 함
 L432  applyNoDupErr          UNIQUE_CHECK_PARTIAL   ON CONFLICT 중재 인덱스. 기다리지 않고 "중복일 수 있음"만
 L434  indimmediate           UNIQUE_CHECK_YES       보통의 UNIQUE, PK. 중복이면 에러, 진행 중이면 기다림
 L436  그 밖 (DEFERRABLE)     UNIQUE_CHECK_PARTIAL   일단 넣고 나중에 다시 확인

 네 번째 값 UNIQUE_CHECK_EXISTING 은 여기서 쓰지 않는다
   지연 제약의 재검사 트리거가 쓴다 (commands/constraint.c L175)
```

힙이 먼저고 인덱스가 나중이라는 순서가 중요하다. 유일성 위반이 인덱스 단계에서 발견되면 이미 힙에 들어간 행은 지울 수 없고, 에러로 트랜잭션이 중단되면서 그 행은 커밋되지 않은 죽은 튜플로 남는다.

```text
 INSERT INTO t(id) VALUES (5)  -- id 는 PRIMARY KEY, 5 는 이미 있음

 시간 ->
 table_tuple_insert         힙 페이지에 (xmin = 내 xid) 튜플이 생긴다
 ExecInsertIndexTuples
   index_insert -> ... -> _bt_check_unique
     중복 발견 -> ereport(ERROR "duplicate key value violates ...")
 트랜잭션 abort              힙 튜플은 xmin 이 abort 된 죽은 튜플로 남는다
                             나중에 vacuum 이 치운다
```

## 결과가 쓰이는 곳

```text
 result (재검사할 인덱스 OID 목록)
      --> ExecInsert 가 recheckIndexes 로 받아 ExecARInsertTriggers 에 넘긴다
          (nodeModifyTable.c L1277). 지연 유일성 제약의 재검사 트리거가 여기서 걸린다

 *specConflict
      --> INSERT ... ON CONFLICT 의 투기적 삽입이 충돌을 알게 되고
          처음부터 다시 시도한다 (nodeModifyTable.c L1223-L1227)
```

## 다루지 않는 것

배제 제약 검사(`check_exclusion_or_unique_constraint`), 표현식 인덱스의 값 계산(`FormIndexDatum`), `UPDATE` 에서 `indexUnchanged` 힌트를 정하는 `index_unchanged_by_update`, `ON CONFLICT` 의 투기적 삽입 전체 절차, 요약 인덱스(BRIN)만 갱신하는 HOT 경로는 이 흐름의 곁가지라 요약만 했다.
