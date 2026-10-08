# grouping_planner

상위: [쿼리 실행 파이프라인](../README.md)

**`Path` 를 층층이 쌓는** 함수다. 먼저 `query_planner` 가 FROM/WHERE 부분, 즉 스캔과 조인의 경로들을 만든다. 그 위에 그룹/집계, 윈도 함수, DISTINCT, ORDER BY 단계가 있으면 단계마다 **새 "upper relation" 을 만들고 아래 relation 의 경로들 위에 한 층씩 얹는다.** 마지막으로 FOR UPDATE 의 `LockRows`, `LIMIT`, 그리고 INSERT/UPDATE/DELETE/MERGE 면 `ModifyTable` 을 붙여 최종 relation 에 넣는다. 가장 싼 경로를 고르는 일은 부른 쪽([07])에 남긴다(L1562-L1563 주석).

## 위치

`optimizer` / `plan` / `planner.c` L1567-L2303 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L1567-L2303))

## 실제 코드

LIMIT 이 있으면 가져올 행 비율을 고친다.

`optimizer` / `plan` / `planner.c` L1567-L1599 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L1567-L1599))

```c
// plan/planner.c L1567-L1599
grouping_planner(PlannerInfo *root, double tuple_fraction,
				 SetOperationStmt *setops)
{
	Query	   *parse = root->parse;
	int64		offset_est = 0;
	int64		count_est = 0;
	double		limit_tuples = -1.0;
	bool		have_postponed_srfs = false;
	PathTarget *final_target;
	List	   *final_targets;
	List	   *final_targets_contain_srfs;
	bool		final_target_parallel_safe;
	RelOptInfo *current_rel;
	RelOptInfo *final_rel;
	FinalPathExtraData extra;
	ListCell   *lc;

	/* Tweak caller-supplied tuple_fraction if have LIMIT/OFFSET */
	if (parse->limitCount || parse->limitOffset)
	{
		tuple_fraction = preprocess_limit(root, tuple_fraction,
										  &offset_est, &count_est);

// ... (L1590-L1593 생략: 주석)
		if (count_est > 0 && offset_est >= 0)
			limit_tuples = (double) count_est + (double) offset_est;
	}

	/* Make tuple_fraction accessible to lower-level routines */
	root->tuple_fraction = tuple_fraction;
```

집합 연산이 없는 보통의 경우, 스캔/조인 경로를 만드는 자리다.

`optimizer` / `plan` / `planner.c` L1780-L1798 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L1780-L1798))

```c
// plan/planner.c L1780-L1798
		/*
		 * Generate the best unsorted and presorted paths for the scan/join
		 * portion of this Query, ie the processing represented by the
		 * FROM/WHERE clauses.  (Note there may not be any presorted paths.)
		 * We also generate (in standard_qp_callback) pathkey representations
		 * of the query's sort clause, distinct clause, etc.
		 */
		current_rel = query_planner(root, standard_qp_callback, &qp_extra);

// ... (L1789-L1797 생략: 주석)
		final_target = create_pathtarget(root, root->processed_tlist);
```

스캔/조인 위에 upper 단계를 하나씩 얹는다.

`optimizer` / `plan` / `planner.c` L1925-L1996 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L1925-L1996))

```c
// plan/planner.c L1925-L1996
		/*
		 * If we have grouping and/or aggregation, consider ways to implement
		 * that.  We build a new upperrel representing the output of this
		 * phase.
		 */
		if (have_grouping)
		{
			current_rel = create_grouping_paths(root,
												current_rel,
												grouping_target,
												grouping_target_parallel_safe,
												gset_data);
// ... (L1937-L1941 생략: SRF 보정)
		}

		/*
		 * If we have window functions, consider ways to implement those.  We
		 * build a new upperrel representing the output of this phase.
		 */
		if (activeWindows)
		{
			current_rel = create_window_paths(root,
											  current_rel,
											  grouping_target,
											  sort_input_target,
											  sort_input_target_parallel_safe,
											  wflists,
											  activeWindows);
// ... (L1957-L1961 생략: SRF 보정)
		}

		/*
		 * If there is a DISTINCT clause, consider ways to implement that. We
		 * build a new upperrel representing the output of this phase.
		 */
		if (parse->distinctClause)
		{
			current_rel = create_distinct_paths(root,
												current_rel,
												sort_input_target);
		}
	}							/* end of if (setOperations) */

	/*
	 * If ORDER BY was given, consider ways to implement that, and generate a
	 * new upperrel containing only paths that emit the correct ordering and
	 * project the correct final_target.  We can apply the original
	 * limit_tuples limit in sort costing here, but only if there are no
	 * postponed SRFs.
	 */
	if (parse->sortClause)
	{
		current_rel = create_ordered_paths(root,
										   current_rel,
										   final_target,
										   final_target_parallel_safe,
										   have_postponed_srfs ? -1.0 :
										   limit_tuples);
// ... (L1991-L1995 생략: SRF 보정)
	}
```

최종 relation 을 만들고, 살아남은 경로마다 LockRows, Limit, ModifyTable 을 붙인다.

`optimizer` / `plan` / `planner.c` L1998-L2264 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L1998-L2264))

```c
// plan/planner.c L1998-L2060
	/*
	 * Now we are prepared to build the final-output upperrel.
	 */
	final_rel = fetch_upper_rel(root, UPPERREL_FINAL, NULL);

// ... (L2003-L2022 생략: 병렬 가능 여부와 FDW 정보 물려주기)
	/*
	 * Generate paths for the final_rel.  Insert all surviving paths, with
	 * LockRows, Limit, and/or ModifyTable steps added if needed.
	 */
	foreach(lc, current_rel->pathlist)
	{
		Path	   *path = (Path *) lfirst(lc);

		/*
		 * If there is a FOR [KEY] UPDATE/SHARE clause, add the LockRows node.
		 * (Note: we intentionally test parse->rowMarks not root->rowMarks
		 * here.  If there are only non-locking rowmarks, they should be
		 * handled by the ModifyTable node instead.  However, root->rowMarks
		 * is what goes into the LockRows node.)
		 */
		if (parse->rowMarks)
		{
			path = (Path *) create_lockrows_path(root, final_rel, path,
												 root->rowMarks,
												 assign_special_exec_param(root));
		}

		/*
		 * If there is a LIMIT/OFFSET clause, add the LIMIT node.
		 */
		if (limit_needed(parse))
		{
			path = (Path *) create_limit_path(root, final_rel, path,
											  parse->limitOffset,
											  parse->limitCount,
											  parse->limitOption,
											  offset_est, count_est);
		}

		/*
		 * If this is an INSERT/UPDATE/DELETE/MERGE, add the ModifyTable node.
		 */
		if (parse->commandType != CMD_SELECT)
```

```c
// plan/planner.c L2243-L2264
			path = (Path *)
				create_modifytable_path(root, final_rel,
										path,
										parse->commandType,
										parse->canSetTag,
										parse->resultRelation,
										rootRelation,
										root->partColsUpdated,
										resultRelations,
										updateColnosLists,
										withCheckOptionLists,
										returningLists,
										rowMarks,
										parse->onConflict,
										mergeActionLists,
										mergeJoinConditions,
										assign_special_exec_param(root));
		}

		/* And shove it into final_rel */
		add_path(final_rel, path);
	}
```

함수의 끝이다. `set_cheapest` 는 하지 않는다.

`optimizer` / `plan` / `planner.c` L2297-L2303 ([GitHub](https://github.com/postgres/postgres/blob/724edf9bde9d356724ad384a2e196edc3c9f80f7/src/backend/optimizer/plan/planner.c#L2297-L2303))

```c
// plan/planner.c L2297-L2303
	/* Let extensions possibly add some more paths */
	if (create_upper_paths_hook)
		(*create_upper_paths_hook) (root, UPPERREL_FINAL,
									current_rel, final_rel, &extra);

	/* Note: currently, we leave it to callers to do set_cheapest() */
}
```

## 동작 흐름

```text
 L1585  LIMIT / OFFSET 이 있으면 preprocess_limit -> tuple_fraction, offset_est, count_est
 L1594  LIMIT 값을 알면 limit_tuples = count + offset   (정렬 비용을 줄여 잡는 데 쓴다)
 L1599  root->tuple_fraction = tuple_fraction

 L1601  집합 연산(UNION 등)이면  plan_set_operations
 L1657  아니면
 L1683    GROUP BY / grouping sets 전처리
 L1700    preprocess_targetlist
 L1787    current_rel = query_planner(root, ...)        FROM + WHERE 의 경로들
 L1798    final_target = create_pathtarget(...)
 L1906    apply_scanjoin_target_to_paths                 스캔/조인 경로가 낼 열 맞추기
 L1930    have_grouping  -> create_grouping_paths        UPPERREL_GROUP_AGG
 L1948    activeWindows  -> create_window_paths          UPPERREL_WINDOW
 L1968    distinctClause -> create_distinct_paths        UPPERREL_DISTINCT
 L1983  sortClause     -> create_ordered_paths           UPPERREL_ORDERED

 L2001  final_rel = fetch_upper_rel(root, UPPERREL_FINAL, NULL)
 L2027  foreach path in current_rel->pathlist
 L2038    rowMarks (FOR UPDATE 등) 면 create_lockrows_path
 L2048    limit_needed 면 create_limit_path
 L2060    SELECT 가 아니면 create_modifytable_path    INSERT / UPDATE / DELETE / MERGE
 L2263    add_path(final_rel, path)
 L2270  상위 질의가 쓸 수 있으면 부분(병렬) 경로도 넘긴다
 L2291  FDW, L2298 create_upper_paths_hook           확장이 경로를 더할 수 있다
 L2302  set_cheapest 는 부른 쪽이 한다
```

각 단계는 아래 단계의 relation 을 입력으로 받아 새 relation 을 돌려준다. 단계가 필요 없으면 건너뛰므로, 질의의 절이 곧 층의 수다.

```text
 upper relation 의 층 (아래에서 위로, 필요한 것만 생긴다)

 UPPERREL_FINAL       L2027-L2264  add_path                LockRows? -> Limit? -> ModifyTable?
        ^
 UPPERREL_ORDERED     L1985        create_ordered_paths    ORDER BY
        ^
 UPPERREL_DISTINCT    L1970        create_distinct_paths   DISTINCT
        ^
 UPPERREL_WINDOW      L1950        create_window_paths     윈도 함수
        ^
 UPPERREL_GROUP_AGG   L1932        create_grouping_paths   GROUP BY, 집계
        ^
 scan/join rel        L1787        query_planner           FROM, WHERE (SeqScan, IndexScan, 조인 경로들)

 relation 마다 pathlist 에 후보 경로 여러 개가 있다
 위 층은 아래 층의 후보 각각 위에 자기 노드를 얹어 후보를 만든다
```

예시 질의 둘이 어떤 층을 지나 어떤 꼭대기 노드를 갖게 되는지 보면 이렇다.

```text
 예시 1  SELECT dept, count(*) FROM emp GROUP BY dept ORDER BY dept LIMIT 5

 L1585  limitCount 5 -> preprocess_limit, limit_tuples = 5 + 0 = 5
 L1787  scan/join   emp 스캔 경로들
 L1932  GROUP_AGG   그룹 집계 경로들. create_grouping_paths -> add_paths_to_grouping_rel (L7247) 에서
        L7262-L7315  can_sort 면 입력을 dept 순으로 맞춘 뒤 (make_ordered_path 가 필요하면 Sort 나 Incremental Sort 를 얹음) Agg(AGG_SORTED)
        L7406-L7427  can_hash 면 Agg(AGG_HASHED)
 L1985  ORDERED     dept 순서를 보장하는 경로만 남긴다 (필요하면 Sort 를 얹는다)
 L2050  FINAL       각 경로 위에 Limit
 최종 계획의 꼭대기 노드는 Limit 이다

 예시 2  INSERT INTO t SELECT * FROM s

 L1787  scan/join   s 스캔 경로들
 L2060  FINAL       commandType 이 CMD_INSERT -> create_modifytable_path
 최종 계획의 꼭대기 노드는 ModifyTable 이다   --> [executor] ExecModifyTable
```

## 결과가 쓰이는 곳

```text
 UPPERREL_FINAL 의 pathlist
      --> [07] subquery_planner 가 set_cheapest (L1280)
      --> standard_planner 가 get_cheapest_fractional_path 로 하나를 고른다 (L452)

 root->processed_tlist
      --> create_plan 이 최종 Plan 의 대상 목록에 쓴다 (L1558-L1560 주석)

 ModifyTable 경로
      --> [executor] 의 ExecModifyTable 이 되어 행 쓰기 흐름으로 이어진다
```

## 다루지 않는 것

`query_planner` 안의 스캔 경로 생성과 조인 순서 탐색(`make_one_rel`, 동적 계획법, GEQO), 각 `create_*_paths` 의 경로 후보와 비용 비교, 해시 집계와 정렬 집계의 선택, 집합 연산 계획(`plan_set_operations`), SRF 보정(`adjust_paths_for_srfs`), 부분 집계와 병렬 경로는 이 흐름의 곁가지라 요약만 했다.
