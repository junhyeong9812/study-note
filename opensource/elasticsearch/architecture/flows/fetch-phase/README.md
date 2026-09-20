# 페치 페이즈

쿼리 페이즈가 **어느 문서인지**만 정하고 끝나면, 그 문서를 실제로 가져오는 것이 이 페이즈다. 사용자가 받는 `_source` 가 여기서 온다. [검색 페이즈](../search-phases/README.md) 체인의 한 칸이고, 폴더 하나가 메서드 하나다. [spi](spi/README.md)는 샤드 세기와 검색 컨텍스트 생명주기다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [01] run                                          L79
      +-- context.execute(AbstractRunnable)         L80
            ~~> 검색 스레드풀로 포크한다
                (TransportSearchAction.asyncSearchExecutor 가 고른다. 기본은 SEARCH)
            +-- doRun -> [02] innerRun               L84
            +-- onFailure -> onPhaseFailure          L89
                  innerRun 이하의 모든 동기 예외가 여기로 모인다
                  (AbstractRunnable L26-32)

 [02] innerRun                                      L94
      +-- reducedQueryPhase 를 구한다                L98
      |     RankFeaturePhase 를 거쳤으면 이미 있고
      |     아니면 resultConsumer.reduce() 로 지금 만든다. 이것도 던질 수 있다
      |
      +-- 샤드 1개 최적화 (4조건 AND)                L102-105
      |     +-- [05] moveToNextPhase(기존 결과)      L109
      |           페치 요청을 하나도 안 보낸다
      |
      +-- 가져올 문서가 0개                          L113
      |     +-- 모든 샤드의 컨텍스트를 놓아준다      L115-116
      |     +-- [05] moveToNextPhase(빈 배열)        L117
      |
      +-- 아니면 [03] innerRunFetch                  L119

 [03] innerRunFetch                                 L124
      +-- docIdsToLoad = fillDocIdsToLoad(...)       L137
      +-- counter = CountedCollector(..., docIdsToLoad.length, moveToNextPhase, ...)  L139
      |
      +-- 첫 루프 - 요청을 보낸다                    L145
      |     가져올 것 없으면 countDown                L158
      |     아니면 [04] executeFetch                  L160
      |
      +-- 둘째 루프 - 안 쓸 컨텍스트를 놓아준다      L169

 [04] executeFetch                                  L201
      +-- contextId 를 꺼낸다                        L210
      +-- getConnection                              L241
      |     실패하면 listener.onFailure 후 return     L243
      +-- buildShardSearchRequest                    L246   try 밖이다
      +-- sendExecuteFetch                           L250
            ~~> 응답이 오면 리스너로
                성공 -> counter.onResult              L218
                실패 -> counter.onFailure + 컨텍스트 해제  L229, L234

 [05] moveToNextPhase                               L271
      +-- context.executeNextPhase(NAME, 서플라이어)  L278
            서플라이어 안에서 merge 하고 ExpandSearchPhase 를 만든다  L279-281
            다만 executeNextPhase 가 서플라이어를 안 부르는 실패 갈래가 넷 있다
```

```text
 루프를 둘로 나눈 의도와 실제

 주석이 의도를 적어 두었다 (L149-152)
   결과가 있는 샤드는 컨텍스트를 놓아야 하는데
   응답에 기여하는 페치 요청을 먼저 보내고 나서 하겠다

 그런데 보장은 약하다
   첫 루프의 마지막 countDown 이 카운터를 0으로 만들면
   moveToNextPhase 가 그 자리에서 동기로 실행된다
   그러면 둘째 루프의 정리는 다음 페이즈가 시작된 뒤에 돈다

 가져올 문서가 있는 샤드가 하나도 없으면 실제로 그렇게 된다
```

```text
 검색 컨텍스트를 놓아주는 자리가 넷이다

 코디네이터가 직접                               판정
   L116  가져올 문서가 0개일 때 전부             releaseIrrelevantSearchContext
   L173  이번에 안 쓸 샤드                       의 5겹 게이트를 지나야 한다
   L234  페치가 실패했을 때
   ASAA L829-841  페이즈가 실패했을 때 일괄      다른 판정 (contextId 있고 PIT 아니면)

 데이터 노드가 알아서
   샤드 1개 최적화 경로는 코디네이터가 한 번도 안 부른다
   데이터 노드가 query+fetch 를 한 컨텍스트에서 끝내고 스스로 닫는다

 그리고 해제는 "시도"일 뿐이다
   releaseIrrelevantSearchContext 의 catch 가 실패를 삼킨다 (SearchPhase L89-91)
```

```text
 컨텍스트가 새는 길이 하나 있다

 getConnection 이 실패하면 (L241-243)
   listener.onFailure -> finally L234 -> releaseIrrelevantSearchContext
   그런데 그 안 L87 이 같은 getConnection 을 다시 부른다
   같은 이유로 또 실패하고 L89 catch 가 삼킨다

 그 뒤 onPhaseFailure -> raisePhaseFailure 도 getConnection 을 쓴다 (L834)
 노드에 닿지 못하는 상황이면 셋 다 실패한다

 결국 데이터 노드의 keep-alive 만료를 기다리게 된다
```

```text
 샤드를 세는 방식이 앞 흐름과 다르다

 검색 페이즈 1회차  outstandingShards   재시도해도 한 번만 내린다
 이 페이즈          CountedCollector    CountDown 하나. 재시도가 없다

 expectedOps 는 docIdsToLoad.length 다 (L141)
   그 길이는 context.results.getNumShards() 다 (L99)
   context.getNumShards() 와 다르다. 뒤엣것은 skipped 를 더한다

 RankFeaturePhase 는 같은 구조를 쓰면서 context.getNumShards() 를 쓴다 (L102)
 두 페이즈의 회계 기준이 다르다
```

## 어디에서 쓰이는가

```text
 [검색 페이즈] 체인에서 query 나 rank-feature 다음 칸이다
 [구조: 샤드 모델] 어느 샤드에 무엇이 있는지는 쿼리 페이즈가 이미 정했다
 [구조: 지속성] 데이터 노드에서 실제 문서를 읽는 것은 Lucene 이다
```

앞 흐름은 [검색 페이즈](../search-phases/README.md)에 있다. 다음 칸은 `ExpandSearchPhase` 이고 이 문서에서 다루지 않는다.

## 단계

1. [run](01_FetchSearchPhase.run/README.md)이 검색 스레드로 포크한다.
2. [innerRun](02_FetchSearchPhase.innerRun/README.md)이 페치를 건너뛸지 정한다.
3. [innerRunFetch](03_FetchSearchPhase.innerRunFetch/README.md)가 샤드마다 요청을 건다.
4. [executeFetch](04_FetchSearchPhase.executeFetch/README.md)가 실제로 보낸다.
5. [moveToNextPhase](05_FetchSearchPhase.moveToNextPhase/README.md)가 결과를 합쳐 다음으로 넘긴다.

## 결과가 쓰이는 곳

```text
 FetchSearchResult
      --> 문서 본문과 하이라이트가 담긴다
      --> merge 가 쿼리 결과의 순서에 맞춰 붙인다

 SearchResponseSections
      --> 서플라이어 안에서 만들어진다 (L279)
      --> addReleasable 로 등록되지만 풀리는 것은 검색 전체가 끝날 때다

 검색 컨텍스트
      --> 안 쓸 것은 여기서 닫는다
      --> 못 닫으면 데이터 노드의 keep-alive 가 정리한다

 페이즈 소요시간
      --> moveToNextPhase 가 기록한다 (L277)
      --> 페치가 느린지 쿼리가 느린지 나눠서 보인다
```

## 다루지 않는 것

`SearchPhaseController.merge` 와 `getHits` 의 결과 병합, 청크 페치 경로(`TransportFetchPhaseCoordinationAction`)와 그 조건, 데이터 노드 쪽 페치 실행(`SearchService.executeFetchPhase`)과 `singleSession` 해제, `ExpandSearchPhase` 이후, `RankFeaturePhase` 의 재점수, rank 점수 설명(`splitRankDocsPerShard`)과 스크롤용 `lastEmittedDocPerShard` 는 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 run](01_FetchSearchPhase.run/README.md)
- [02 innerRun](02_FetchSearchPhase.innerRun/README.md)
- [03 innerRunFetch](03_FetchSearchPhase.innerRunFetch/README.md)
- [04 executeFetch](04_FetchSearchPhase.executeFetch/README.md)
- [05 moveToNextPhase](05_FetchSearchPhase.moveToNextPhase/README.md)
- [spi](spi/README.md) — 샤드 세기, 컨텍스트 생명주기
