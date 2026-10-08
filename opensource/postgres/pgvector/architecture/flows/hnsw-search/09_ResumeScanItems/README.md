# ResumeScanItems

상위: [HNSW 검색](../README.md)

**반복 스캔(`hnsw.iterative_scan` 이 `relaxed_order` 나 `strict_order`)에서 후보 목록이 바닥났을 때 0층 탐색을 이어 가는 함수다.** 첫 탐색과 이전 이어가기에서 W 밖으로 밀려나 `discarded` 힙에 모인 후보 중 가장 가까운 `ef_search` 개를 새 진입점 목록으로 삼아 `HnswSearchLayer` 를 다시 부른다. 방문 집합은 이어 쓰므로 이미 본 원소는 다시 펼치지 않는다.

## 위치

`src` / `hnswscan.c` L66-L92 ([GitHub](https://github.com/pgvector/pgvector/blob/f37c13f68b57d2c3472b2214fbcff699d6d34876/src/hnswscan.c#L66-L92))

## 실제 코드

```c
// hnswscan.c L63-L92
/*
 * Resume scan at ground level with discarded candidates
 */
static List *
ResumeScanItems(IndexScanDesc scan)
{
	HnswScanOpaque so = (HnswScanOpaque) scan->opaque;
	Relation	index = scan->indexRelation;
	List	   *ep = NIL;
	char	   *base = NULL;
	int			batch_size = hnsw_ef_search;

	if (pairingheap_is_empty(so->discarded))
		return NIL;

	/* Get next batch of candidates */
	for (int i = 0; i < batch_size; i++)
	{
		HnswSearchCandidate *sc;

		if (pairingheap_is_empty(so->discarded))
			break;

		sc = HnswGetSearchCandidate(w_node, pairingheap_remove_first(so->discarded));

		ep = lappend(ep, sc);
	}

	return HnswSearchLayer(base, &so->q, ep, batch_size, 0, index, &so->support, so->m, false, NULL, &so->v, &so->discarded, false, &so->tuples);
}
```

## 동작 흐름

```text
 hnswgettuple 에서 so->w 가 비었고 iterative_scan != off      (hnswscan.c L254)
   tuples >= hnsw.max_scan_tuples (기본 20000) 또는 tmpCtx > maxMemory
     -> 이어가지 않는다. discarded 에서 하나씩 꺼내 그대로 낸다     L264-L270
   아니면 LockPage(SCAN) -> ResumeScanItems -> UnlockPage

 ResumeScanItems(scan)                               L66
   L73   batch_size = hnsw_ef_search
   L75   discarded 가 비었으면 NIL
   L79   가장 가까운 것부터 batch_size 개를 discarded 에서 꺼내 ep 로
   L91   HnswSearchLayer(ep, ef = batch_size, lc = 0,
                         v = &so->v, discarded = &so->discarded,
                         initVisited = false, tuples = &so->tuples)
           ep 는 이미 방문한 원소라 v 에 다시 넣지 않는다 (initVisited = false)
           새로 밀려난 후보는 같은 discarded 에 쌓인다
```

[07] 의 예를 이어 본다. 첫 탐색 결과 C, F 를 다 낸 뒤 w 가 비었다.

```text
 discarded = {D4, B9, A25, E64},  ef_search = 2

 ep = [D4, B9]                     가장 가까운 2개
 HnswSearchLayer
   W 에 D4, B9 (wlen 2)
   c = D4  f = B9   D 의 이웃 C 는 이미 봄
   c = B9  f = B9   B 의 이웃 A, C 는 이미 봄
 결과 w = [B9, D4]                 -> D, B 순으로 낸다
 discarded = {A25, E64}            다음에 또 비면 A, E 에서 시작

 strict_order 면 직전에 낸 거리(C 의 1)보다 가까운 것은 건너뛴다
   D4, B9 는 1 보다 멀어 그대로 나간다
```

이어가기에서 내는 결과는 첫 탐색 결과보다 멀 수도, 가까울 수도 있다. `relaxed_order` 는 그대로 내고 `strict_order` 는 직전보다 가까운 것을 버린다([03] L318).

## 결과가 쓰이는 곳

```text
 새 w
      --> hnswgettuple 이 다시 끝에서부터 꺼낸다
 so->tuples
      --> 본 원소 수가 hnsw.max_scan_tuples 에 닿으면 더 이어가지 않는다
          (주석 hnsw.c L101: 근사값이고 첫 스캔에는 영향이 없다)
```

## 다루지 않는 것

반복 스캔에서 이미 낸 원소의 메모리를 바로 해제하는 부분(hnswgettuple L307-L311)과, 실행기가 `WHERE` 조건으로 행을 계속 거를 때 몇 번이나 이어가는지는 질의마다 달라 다루지 않았다.
