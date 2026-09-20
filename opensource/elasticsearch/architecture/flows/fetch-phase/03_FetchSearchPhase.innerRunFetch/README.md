# FetchSearchPhase.innerRunFetch

상위: [페치 페이즈](../README.md)

샤드마다 **"이 문서들을 가져와라"** 를 보낸다. 루프가 둘인데 그 순서에 의도가 있고, 그 의도가 항상 지켜지지는 않는다.

## 위치

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L124-L177 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L124-L177))

## 실제 코드

보낼 것을 준비하고 카운터를 만든다.

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L130-L144 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L130-L144))

```java
// FetchSearchPhase.java L130-L144
        ArraySearchPhaseResults<FetchSearchResult> fetchResults = new ArraySearchPhaseResults<>(numShards);
        final List<Map<Integer, RankDoc>> rankDocsPerShard = false == shouldExplainRankScores(context.getRequest())
            ? null
            : splitRankDocsPerShard(scoreDocs, numShards);
        final ScoreDoc[] lastEmittedDocPerShard = context.getRequest().scroll() != null
            ? SearchPhaseController.getLastEmittedDocPerShard(reducedQueryPhase, numShards)
            : null;
        final List<Integer>[] docIdsToLoad = SearchPhaseController.fillDocIdsToLoad(numShards, scoreDocs);
        context.addReleasable(fetchResults);
        final CountedCollector<FetchSearchResult> counter = new CountedCollector<>(
            fetchResults,
            docIdsToLoad.length, // we count down every shard in the result no matter if we got any results or not
            () -> moveToNextPhase(fetchResults.getAtomicArray(), reducedQueryPhase, phaseStartTimeInNanos),
            context
        );
```

첫 루프가 보내고, 둘째 루프가 정리한다.

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L145-L176 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L145-L176))

```java
// FetchSearchPhase.java L145-L176
        for (int i = 0; i < docIdsToLoad.length; i++) {
            List<Integer> entry = docIdsToLoad[i];
            SearchPhaseResult shardPhaseResult = searchPhaseShardResults.get(i);
            if (entry == null) { // no results for this shard ID
                // if we got some hits from this shard we have to release the context
                // we do this below after sending out the fetch requests relevant to the search to give priority to those requests
                // that contribute to the final search response
                // in any case we count down this result since we don't talk to this shard anymore
                if (shardPhaseResult != null) {
                    // notifying the listener here as otherwise the search operation might finish before we
                    // get a chance to notify the progress listener for some fetch results
                    progressListener.notifyFetchResult(i);
                }
                counter.countDown();
            } else {
                executeFetch(
                    shardPhaseResult,
                    counter,
                    entry,
                    rankDocsPerShard == null || rankDocsPerShard.get(i).isEmpty() ? null : new RankDocShardInfo(rankDocsPerShard.get(i)),
                    (lastEmittedDocPerShard != null) ? lastEmittedDocPerShard[i] : null
                );
            }
        }
        for (int i = 0; i < docIdsToLoad.length; i++) {
            if (docIdsToLoad[i] == null) {
                SearchPhaseResult shardPhaseResult = searchPhaseShardResults.get(i);
                if (shardPhaseResult != null) {
                    releaseIrrelevantSearchContext(shardPhaseResult, context);
                }
            }
        }
```

## 동작 흐름

```text
 L130  fetchResults = new ArraySearchPhaseResults<>(numShards)
 L131  rank 점수를 설명해야 하면 샤드별로 쪼갠다
 L134  스크롤이면 샤드별 마지막 문서를 구한다
 L137  docIdsToLoad = fillDocIdsToLoad(numShards, scoreDocs)
         길이가 numShards 인 배열. 가져올 것 없는 샤드는 null
 L138  context.addReleasable(fetchResults)
 L139  counter = CountedCollector(fetchResults, docIdsToLoad.length,
                                  moveToNextPhase 람다, context)

 L145  첫 루프
       L148  entry == null (이 샤드에서 가져올 문서 없음)
       |     L153  결과가 있었으면 notifyFetchResult
       |     L158  counter.countDown()
       L159  아니면
             L160  executeFetch(...)

 L169  둘째 루프
       L170  docIdsToLoad[i] == null 이고 결과가 있으면
             L173  releaseIrrelevantSearchContext
```

```text
 루프를 둘로 나눈 의도

 주석이 적어 두었다 (L149-152)
   이 샤드에서 히트를 받았으면 컨텍스트를 놓아야 한다
   그런데 최종 응답에 기여하는 페치 요청을 먼저 보내고
   그 뒤에 하겠다

 즉 정리보다 요청이 급하다는 우선순위다
```

```text
 그 의도가 항상 지켜지지는 않는다

 첫 루프의 마지막 countDown(L158)이 카운터를 0으로 만들면
 그 자리에서 onFinish 가 돈다 (CountedCollector L41)
 그것이 moveToNextPhase 이고, 거기서 다음 페이즈까지 이어진다

 그러면 둘째 루프는 다음 페이즈가 시작된 뒤에 돈다

 가져올 문서가 있는 샤드가 하나도 없으면 실제로 그렇게 된다
 (그런 경우는 innerRun L113 이 먼저 걸러내지만,
  일부 샤드만 문서를 내고 그 응답이 동기로 돌아오는 경우도 있다)
```

```text
 카운터가 모자랄 수 있다

 정상이면 인덱스마다 정확히 한 번씩 센다
   entry == null      -> L158 countDown
   entry != null      -> executeFetch 가 성공이든 실패든 한 번

 그런데 executeFetch 가 리스너를 부르기 전에 던지면
 그 샤드도, 루프의 남은 샤드도 세어지지 않는다
   L210  queryResult 와 rankFeatureResult 가 둘 다 null 이면 NPE
   L246  buildShardSearchRequest 는 try 밖이다

 그 예외는 [01] 의 onFailure 로 가서 페이즈를 실패시키므로
 검색이 매달리지는 않는다

 CountedCollector 의 assert 는 초과만 잡고 미달은 못 잡는다 (L39)
```

```text
 세는 기준이 numShards 다

 expectedOps = docIdsToLoad.length (L141)
 그 길이는 fillDocIdsToLoad 에 넘긴 numShards 다
 그리고 그것은 innerRun L99 의 context.results.getNumShards() 다

 주석이 의도를 적어 두었다 (L141)
   결과가 있든 없든 모든 샤드를 센다

 참고로 RankFeaturePhase 는 같은 구조를 쓰면서
 context.getNumShards() 를 쓴다 (L102, L105)
 skipped 를 더한 값이라 기준이 다르다
```

## 결과가 쓰이는 곳

```text
 docIdsToLoad
      --> 샤드마다 가져올 문서 번호 목록이다
      --> null 인 자리가 "이 샤드는 상위 N건에 못 들었다"는 뜻이다

 fetchResults
      --> 페치 결과가 모이는 배열이다
      --> addReleasable 로 등록되지만 풀리는 것은 검색 전체가 끝날 때다

 counter
      --> 0이 되면 moveToNextPhase 가 돈다
      --> 재시도가 없어서 한 샤드는 한 번만 센다

 둘째 루프의 해제
      --> 이번에 안 쓸 샤드의 컨텍스트를 닫는다
      --> 못 닫아도 조용히 넘어간다 (판정은 spi 참조)
```

## 다루지 않는 것

`SearchPhaseController.fillDocIdsToLoad` 의 배열 채우기, `splitRankDocsPerShard` 와 rank 점수 설명, 스크롤용 `getLastEmittedDocPerShard`, `ArraySearchPhaseResults` 의 참조 수 관리, `CountDown` 의 구현은 같은 뼈대의 곁가지라 요약만 했다. 컨텍스트 해제 판정은 [spi](../spi/README.md)에 있다.
