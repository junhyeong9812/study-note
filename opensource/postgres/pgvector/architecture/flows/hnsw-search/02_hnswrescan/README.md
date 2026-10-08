# hnswrescan

상위: [HNSW 검색](../README.md)

**스캔을 처음 상태로 되돌리고 새 ORDER BY 키를 받는 `amrescan` 이다.** 실행기는 스캔을 시작할 때 한 번, 그리고 중첩 루프의 안쪽처럼 검색 값이 바뀔 때마다 이것을 부른다. 이전 탐색의 후보·방문 집합은 모두 `tmpCtx` 에 있으므로 그 컨텍스트를 비우는 것으로 한꺼번에 버린다.

## 위치

`src` / `hnswscan.c` L171-L189 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswscan.c#L171-L189))

## 실제 코드

```c
// hnswscan.c L168-L189
/*
 * Start or restart an index scan
 */
void
hnswrescan(IndexScanDesc scan, ScanKey keys, int nkeys, ScanKey orderbys, int norderbys)
{
	HnswScanOpaque so = (HnswScanOpaque) scan->opaque;

	so->first = true;
	/* v and discarded are allocated in tmpCtx */
	so->v.tids = NULL;
	so->discarded = NULL;
	so->tuples = 0;
	so->previousDistance = -get_float8_infinity();
	MemoryContextReset(so->tmpCtx);

	if (keys && scan->numberOfKeys > 0)
		memmove(scan->keyData, keys, scan->numberOfKeys * sizeof(ScanKeyData));

	if (orderbys && scan->numberOfOrderBys > 0)
		memmove(scan->orderByData, orderbys, scan->numberOfOrderBys * sizeof(ScanKeyData));
}
```

스캔을 닫는 쪽이다.

`src` / `hnswscan.c` L341-L350 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswscan.c#L341-L350))

```c
// hnswscan.c L338-L350
/*
 * End a scan and release resources
 */
void
hnswendscan(IndexScanDesc scan)
{
	HnswScanOpaque so = (HnswScanOpaque) scan->opaque;

	MemoryContextDelete(so->tmpCtx);

	pfree(so);
	scan->opaque = NULL;
}
```

## 동작 흐름

```text
 hnswrescan(scan, keys, nkeys, orderbys, norderbys)  L171
   L176  first = true                  다음 gettuple 에서 탐색을 새로 한다
   L178  v.tids = NULL, discarded = NULL   가리키던 메모리는 곧 사라진다 (주석 L177)
   L180  tuples = 0                    반복 스캔이 센 튜플 수
   L181  previousDistance = -무한대    strict_order 비교 기준
   L182  MemoryContextReset(tmpCtx)    이전 후보, 원소, 방문 해시 전부
   L184  keys 가 있으면 keyData 로 복사       (HNSW 는 WHERE 키를 쓰지 않는다)
   L187  orderbys 가 있으면 orderByData 로 복사   <-> 의 오른쪽 값이 여기 들어온다

 hnswendscan(scan)                                   L341
   L346  MemoryContextDelete(tmpCtx)
   L348  pfree(so)
```

```text
 중첩 루프에서 안쪽이 HNSW 스캔일 때

 바깥 행 1   rescan(q1) -> gettuple ... (LIMIT 까지)
 바깥 행 2   rescan(q2) -> tmpCtx 비움 -> gettuple 에서 q2 로 새 탐색
 ...
 끝          endscan
```

## 결과가 쓰이는 곳

```text
 scan->orderByData[0].sk_argument
      --> [04] GetScanValue 가 검색 값으로 꺼낸다
 first = true
      --> [03] hnswgettuple 이 첫 호출 분기로 들어간다
```

## 다루지 않는 것

실행기가 rescan 을 부르는 시점(`ExecReScanIndexScan`)은 PostgreSQL 쪽이라 다루지 않았다.
