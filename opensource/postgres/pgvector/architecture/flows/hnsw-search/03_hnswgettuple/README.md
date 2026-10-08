# hnswgettuple

상위: [HNSW 검색](../README.md)

**실행기가 다음 행을 달라고 할 때마다 불리는 `amgettuple` 이고, 이 흐름의 지휘자다.** 첫 호출에서만 스캔 잠금을 잡고 그래프를 탐색해 후보 목록 `so->w` 를 만든다. 그 뒤로는 목록 끝(가장 가까운 원소)에서 힙 TID 를 하나씩 꺼내 돌려준다. 원소 하나가 힙 TID 를 여러 개 가질 수 있으므로 원소 하나가 여러 번에 걸쳐 나간다. 목록이 비면 반복 스캔 설정에 따라 멈추거나, 버린 후보에서 탐색을 이어 간다.

## 위치

`src` / `hnswscan.c` L194-L336 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswscan.c#L194-L336))

## 실제 코드

```c
// hnswscan.c L191-L336
/*
 * Fetch the next tuple in the given scan
 */
bool
hnswgettuple(IndexScanDesc scan, ScanDirection dir)
{
	HnswScanOpaque so = (HnswScanOpaque) scan->opaque;
	MemoryContext oldCtx = MemoryContextSwitchTo(so->tmpCtx);

	/*
	 * Index can be used to scan backward, but Postgres doesn't support
	 * backward scan on operators
	 */
	Assert(ScanDirectionIsForward(dir));

	if (so->first)
	{
		Datum		value;

		/* Count index scan for stats */
		pgstat_count_index_scan(scan->indexRelation);
#if PG_VERSION_NUM >= 180000
		if (scan->instrument)
			scan->instrument->nsearches++;
#endif

		/* Safety check */
		if (scan->orderByData == NULL)
			elog(ERROR, "cannot scan hnsw index without order");

		/* Requires MVCC-compliant snapshot as not able to maintain a pin */
		/* https://www.postgresql.org/docs/current/index-locking.html */
		if (!IsMVCCSnapshot(scan->xs_snapshot))
			elog(ERROR, "non-MVCC snapshots are not supported with hnsw");

		/* Get scan value */
		value = GetScanValue(scan);

		/*
		 * Get a shared lock. This allows vacuum to ensure no in-flight scans
		 * before marking tuples as deleted.
		 */
		LockPage(scan->indexRelation, HNSW_SCAN_LOCK, ShareLock);

		so->w = GetScanItems(scan, value);

		/* Release shared lock */
		UnlockPage(scan->indexRelation, HNSW_SCAN_LOCK, ShareLock);

		so->first = false;

#if defined(HNSW_MEMORY)
		ShowMemoryUsage(so);
#endif
	}

	for (;;)
	{
		char	   *base = NULL;
		HnswSearchCandidate *sc;
		HnswElement element;
		ItemPointer heaptid;

		if (list_length(so->w) == 0)
		{
			if (hnsw_iterative_scan == HNSW_ITERATIVE_SCAN_OFF)
				break;

			/* Empty index */
			if (so->discarded == NULL)
				break;

			/* Reached max number of tuples or memory limit */
			if (so->tuples >= hnsw_max_scan_tuples || MemoryContextMemAllocated(so->tmpCtx, false) > so->maxMemory)
			{
				if (pairingheap_is_empty(so->discarded))
					break;

				/* Return remaining tuples */
				so->w = lappend(so->w, HnswGetSearchCandidate(w_node, pairingheap_remove_first(so->discarded)));
			}
			else
			{
				/*
				 * Locking ensures when neighbors are read, the elements they
				 * reference will not be deleted (and replaced) during the
				 * iteration.
				 *
				 * Elements loaded into memory on previous iterations may have
				 * been deleted (and replaced), so when reading neighbors, the
				 * element version must be checked.
				 */
				LockPage(scan->indexRelation, HNSW_SCAN_LOCK, ShareLock);

				so->w = ResumeScanItems(scan);

				UnlockPage(scan->indexRelation, HNSW_SCAN_LOCK, ShareLock);

#if defined(HNSW_MEMORY)
				ShowMemoryUsage(so);
#endif
			}

			if (list_length(so->w) == 0)
				break;
		}

		sc = llast(so->w);
		element = HnswPtrAccess(base, sc->element);

		/* Move to next element if no valid heap TIDs */
		if (element->heaptidsLength == 0)
		{
			so->w = list_delete_last(so->w);

			/* Mark memory as free for next iteration */
			if (hnsw_iterative_scan != HNSW_ITERATIVE_SCAN_OFF)
			{
				pfree(element);
				pfree(sc);
			}

			continue;
		}

		heaptid = &element->heaptids[--element->heaptidsLength];

		if (hnsw_iterative_scan == HNSW_ITERATIVE_SCAN_STRICT)
		{
			if (sc->distance < so->previousDistance)
				continue;

			so->previousDistance = sc->distance;
		}

		MemoryContextSwitchTo(oldCtx);

		scan->xs_heaptid = *heaptid;
		scan->xs_recheck = false;
		scan->xs_recheckorderby = false;
		return true;
	}

	MemoryContextSwitchTo(oldCtx);
	return false;
}
```

## 동작 흐름

```text
 hnswgettuple(scan, dir)                             L194
   L198  tmpCtx 로 전환
   L206  first 이면
           L211  pgstat_count_index_scan
           L218  orderByData == NULL -> "cannot scan hnsw index without order"
           L223  MVCC 스냅샷이 아니면 오류      핀을 쥐고 있지 않으므로 (주석 L221-L222)
           L227  [04] GetScanValue
           L233  LockPage(HNSW_SCAN_LOCK = 블록 번호 1, ShareLock)
           L235  so->w = [05] GetScanItems(scan, value)
           L238  UnlockPage
           L240  first = false

   L247  for (;;)
           L254  w 가 비었으면
                   iterative_scan = off           -> break (끝)
                   discarded == NULL (빈 인덱스)  -> break
                   tuples >= max_scan_tuples 또는 메모리 > maxMemory
                     discarded 에서 가장 가까운 하나를 w 에 (더 탐색하지 않고)
                   아니면
                     LockPage -> [09] ResumeScanItems -> UnlockPage
                   여전히 비었으면 break
           L298  sc = llast(w)                    가장 가까운 후보
           L302  heaptidsLength == 0 이면 w 에서 빼고 다음 (반복 스캔이면 메모리 해제)
           L316  heaptid = heaptids[--heaptidsLength]    뒤에서부터 하나
           L318  strict_order 이고 거리 < previousDistance -> 건너뜀
                 아니면 previousDistance = 거리
           L328  xs_heaptid = heaptid, recheck 없음 -> return true
   L335  return false
```

`so->w` 가 어떤 순서로 소비되는지가 핵심이다. `HnswSearchLayer` 는 결과 힙에서 먼 것부터 꺼내 목록에 붙이므로 목록 끝이 가장 가깝다.

```text
 ef_search = 3 으로 0층 탐색이 끝난 뒤 (거리 = L2 제곱)

 so->w  [ X (9)  Y (4)  Z (1) ]          Z.heaptids = {t1, t2}
                          ^ llast

 호출 1   Z 에서 heaptids[1] = t2 를 낸다   Z.heaptidsLength 2 -> 1
 호출 2   Z 에서 heaptids[0] = t1          1 -> 0
 호출 3   Z 는 0 개 -> w 에서 빼고 Y 의 t3
 호출 4   X 의 t4
 호출 5   w 가 비었다
            iterative_scan = off  -> false. LIMIT 10 이어도 4 행에서 끝난다
            relaxed_order         -> ResumeScanItems 로 더 찾는다
```

```text
 반복 스캔 두 모드의 차이 (L318)

 relaxed_order   이어서 찾은 후보를 거리와 상관없이 낸다
                 앞서 낸 것보다 가까운 행이 뒤에 나올 수 있다
 strict_order    previousDistance 보다 가까운 후보는 내지 않고 건너뛴다
                 결과는 거리 순을 지키지만 건너뛴 만큼 행이 빠진다
```

## 결과가 쓰이는 곳

```text
 true + scan->xs_heaptid
      --> 실행기가 힙에서 튜플을 읽고 스냅샷으로 가시성을 본다
          안 보이는 튜플이면 다시 hnswgettuple 을 부른다 (그래서 ef_search 보다 적게 나올 수 있다)
 false
      --> 인덱스 스캔 끝
```

## 다루지 않는 것

PostgreSQL 18 의 `scan->instrument->nsearches`(L212-L215), `HNSW_MEMORY` 빌드의 메모리 로그는 다루지 않았다. 스캔 잠금을 VACUUM 이 어떻게 쓰는지는 주석(L229-L232: 지우기 전에 진행 중인 스캔이 없음을 확인)만 옮긴다.
