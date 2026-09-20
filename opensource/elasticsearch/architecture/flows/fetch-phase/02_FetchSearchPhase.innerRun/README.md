# FetchSearchPhase.innerRun

상위: [페치 페이즈](../README.md)

**페치를 아예 안 해도 되는 경우를 먼저 걸러낸다.** 둘 다 걸리지 않을 때만 [innerRunFetch](../03_FetchSearchPhase.innerRunFetch/README.md)로 간다.

## 위치

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L94-L122 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L94-L122))

## 실제 코드

```java
// FetchSearchPhase.java L94-L122
    private void innerRun() throws Exception {
        assert this.reducedQueryPhase == null ^ this.resultConsumer == null;
        long phaseStartTimeInNanos = System.nanoTime();
        // depending on whether we executed the RankFeaturePhase we may or may not have the reduced query result computed already
        final var reducedQueryPhase = this.reducedQueryPhase == null ? resultConsumer.reduce() : this.reducedQueryPhase;
        final int numShards = context.results.getNumShards();
        // Usually when there is a single shard, we force the search type QUERY_THEN_FETCH. But when there's kNN, we might
        // still use DFS_QUERY_THEN_FETCH, which does not perform the "query and fetch" optimization during the query phase.
        final boolean queryAndFetchOptimization = context.getNumShards() == 1
            && context.getRequest().hasKnnSearch() == false
            && reducedQueryPhase.queryPhaseRankCoordinatorContext() == null
            && (context.getRequest().source() == null || context.getRequest().source().rankBuilder() == null);
        if (queryAndFetchOptimization) {
            assert assertConsistentWithQueryAndFetchOptimization();
            // query AND fetch optimization
            moveToNextPhase(searchPhaseShardResults, reducedQueryPhase, phaseStartTimeInNanos);
        } else {
            ScoreDoc[] scoreDocs = reducedQueryPhase.sortedTopDocs().scoreDocs();
            // no docs to fetch -- sidestep everything and return
            if (scoreDocs.length == 0) {
                // we have to release contexts here to free up resources
                searchPhaseShardResults.asList()
                    .forEach(searchPhaseShardResult -> releaseIrrelevantSearchContext(searchPhaseShardResult, context));
                moveToNextPhase(new AtomicArray<>(0), reducedQueryPhase, phaseStartTimeInNanos);
            } else {
                innerRunFetch(scoreDocs, numShards, reducedQueryPhase, phaseStartTimeInNanos);
            }
        }
    }
```

## 동작 흐름

```text
 L98  reducedQueryPhase 를 구한다
        this.reducedQueryPhase 가 있으면 그것 (RankFeaturePhase 를 거친 경우)
        없으면 resultConsumer.reduce() 로 지금 만든다
        reduce 는 throws Exception 이다. 던지면 [01] 의 onFailure 로 간다

 L99  numShards = context.results.getNumShards()

 L102 샤드 1개 최적화 판정 (넷 다 참이어야 한다)
        context.getNumShards() == 1
        hasKnnSearch() == false
        queryPhaseRankCoordinatorContext() == null
        source == null 이거나 rankBuilder() == null

 L106 최적화가 되면
        L109  moveToNextPhase(searchPhaseShardResults, ...)
              페치 요청을 하나도 안 보낸다

 L110 아니면
        L111  scoreDocs = reducedQueryPhase.sortedTopDocs().scoreDocs()
        L113  길이가 0이면
              L115  모든 결과에 releaseIrrelevantSearchContext
              L117  moveToNextPhase(빈 배열, ...)
        L118  아니면
              L119  innerRunFetch(scoreDocs, numShards, ...)
```

```text
 두 numShards 가 다른 값이다

 L99   context.results.getNumShards()      결과 배열의 크기
 L102  context.getNumShards()              그것 + skippedCount
                                           (AbstractSearchAsyncAction L613)

 최적화 판정은 뒤엣것을 쓴다
 can_match 로 걸러진 샤드가 하나라도 있으면
 실제로 물어본 샤드가 하나여도 최적화가 안 걸린다

 아래 innerRunFetch 는 앞엣것을 쓴다
```

```text
 샤드가 하나면 왜 페치를 건너뛰는가

 주석이 사정을 적어 두었다 (L100-101)
   보통 샤드가 하나면 QUERY_THEN_FETCH 로 강제한다
   다만 kNN 이 있으면 DFS_QUERY_THEN_FETCH 를 쓸 수 있고
   그때는 쿼리 페이즈에서 query-and-fetch 최적화를 안 한다

 즉 조건이 맞으면 데이터 노드가 쿼리와 페치를 한 번에 끝냈다
 코디네이터는 이미 문서를 들고 있다

 그래서 컨텍스트를 놓아줄 필요도 없다
 데이터 노드가 그 자리에서 닫았기 때문이다
```

```text
 문서가 0개면 컨텍스트부터 닫는다

 주석이 이유를 적어 두었다 (L114)
   자원을 풀어 주려고 여기서 컨텍스트를 놓는다

 쿼리 페이즈가 끝나면 샤드마다 컨텍스트가 열려 있다
 가져갈 문서가 없으면 그것들이 전부 쓸모없다

 asList() 는 null 을 거르므로 (AtomicArray)
 실패한 샤드는 순회 대상이 아니다
```

## 결과가 쓰이는 곳

```text
 reducedQueryPhase
      --> 어느 샤드의 몇 번 문서를 가져올지가 여기 들어 있다
      --> merge 가 나중에 이것과 페치 결과를 합친다

 최적화 경로
      --> 페치 요청이 0건이다
      --> 응답 지연이 크게 줄어든다

 빈 배열 경로
      --> moveToNextPhase 에 빈 AtomicArray 를 넘긴다
      --> merge 가 히트 없는 응답을 만든다
```

## 다루지 않는 것

`QueryPhaseResultConsumer.reduce` 의 결과 병합, `SortedTopDocs` 와 정렬, kNN 검색과 `DFS_QUERY_THEN_FETCH` 의 관계, `queryPhaseRankCoordinatorContext` 의 의미, `releaseIrrelevantSearchContext` 의 판정(자세한 것은 [spi](../spi/README.md)에 있다)은 같은 뼈대의 곁가지라 요약만 했다.
