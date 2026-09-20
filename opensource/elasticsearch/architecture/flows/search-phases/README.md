# 검색 페이즈

검색 요청 하나가 **여러 페이즈를 차례로 거쳐** 응답이 되기까지다. 페이즈마다 샤드에 흩어졌다 모이고, 모인 결과로 다음 페이즈가 정해진다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 페이즈 계약과 전이 표다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 사이클이 아니라 체인이다

 [01] start                                    L232
        +-- 샤드가 0개면 => 빈 응답 후 끝        L241
        +-- [02] executePhase(this)             L247
              this 가 SearchPhase 다 (L79 extends SearchPhase)

 [02] executePhase                             L430   private, 호출처 둘뿐 (L247, L426)
        +-- phase.run()                         L432
        +-- catch (RuntimeException)
              => onPhaseFailure                 L437

 페이즈마다 run() 이 다르다
   1회차  ASAA.run  L251  (final. 아래 [03]~[05] 가 여기 딸린 것이다)
   2회차~ DfsQueryPhase.run / RankFeaturePhase.run / FetchSearchPhase.run
          ExpandSearchPhase.run / FetchLookupFieldsPhase.run

 [08] executeNextPhase                         L343
        +-- 다음 페이즈를 만들어 executePhase 를 다시 부른다  L426
        +-- 이것은 중첩 호출이다. 되돌아가는 것이 아니라 스택이 쌓인다
              FetchSearchPhase 와 RankFeaturePhase 는 run 첫 줄에서 포크해 스택을 푼다
              ExpandSearchPhase 는 안 풀어서 마지막 두 페이즈가 한 스택에 겹친다
```

```text
 1회차의 샤드 팬아웃 ([03]~[07])

 [03] run                                      L251
        +-- outstandingShards 가 이미 0이면 [07] 로 직행   L253-255
        +-- [04] doRun(shardIndexMap)           L261

 [04] doRun                                    L264
        주의 - 이것이 기본 경로가 아니다
        SearchQueryThenFetchAsyncAction L508 이 오버라이드하고
        search.batched_query_phase 기본값이 true 다 (SearchService L327)
        |
        +-- 샤드마다
              routing 이 없으면 failOnUnavailable -> [06]     L273
              아니면 [05] performPhaseOnShard                 L275

 [05] performPhaseOnShard                      L280
        +-- 노드당 동시 요청 제한이 있으면 submit            L287
        |     허가가 남아 있으면 그 자리에서 실행된다
        |     없으면 ~~> 큐에 쌓였다가 나중에
        +-- executePhaseOnShard  추상                        L318
              ~~> 성공 -> onShardResult -> [07]
              ~~> 실패 -> [06] onShardFailure

 [06] onShardFailure (4-arg)                   L454
        +-- 재시도 가능하고 복제본이 남았으면
        |     performPhaseOnShard 로 되돌아간다              L464
        |     outstandingShards 를 건드리지 않는다
        +-- 아니면 finishOneShard                            L476

 [07] onShardResult -> finishOneShard -> onPhaseDone   L558, L480, L864
        +-- outstandingShards 가 0이 되면 onPhaseDone         L483
        +-- onPhaseDone 은 [08] 을 부른다                     L866
```

```text
 페이즈 전이 표

 query,  rank 없음 : query → fetch → expand → fetch_lookup_fields        4개
 query,  rank 있음 : query → rank-feature → fetch → expand → lookup      5개
 dfs,    rank 없음 : dfs → dfs_query → fetch → expand → lookup           5개
 dfs,    rank 있음 : dfs → dfs_query → rank-feature → fetch → … → lookup 6개
 open_pit          : open_pit → 익명 페이즈                               2개
 샤드 0개          : start L241 에서 즉시 종료                            0개

 같은 페이즈로 되돌아가는 전이는 없다. 각 페이즈의 다음이 고정이다
 그래서 상한이 여섯이다
```

```text
 executeNextPhase 로 들어오는 입구가 다섯이다

 ASAA.onPhaseDone            L866   1회차만
 DfsQueryPhase               L135
 RankFeaturePhase            L278
 FetchSearchPhase            L278
 ExpandSearchPhase           L187

 ASAA.onPhaseDone 은 private 이고 호출처가 L254 와 L484 둘뿐이다
 그래서 2회차부터는 각 페이즈가 executeNextPhase 를 직접 부른다
```

```text
 이름이 같은데 다른 메서드가 여럿이다

 onPhaseDone   ASAA L864 / ExpandSearchPhase L186 / RankFeaturePhase L189
                 셋 다 private 이고 서로 무관하다
 onShardFailure ASAA L454 (4-arg, 재시도 있음) / ASAA L506 (3-arg, 기록만)
                 2회차 이후 페이즈는 CountedCollector 를 통해 3-arg 만 부른다
                 즉 재시도는 1회차에만 있다
 doRun          ASAA L264 / SQTF L508 오버라이드 / 그 밖에 AbstractRunnable.doRun 여럿
 run            SearchPhase 구현이 명명 6개 + 익명 4개
```

## 어디에서 쓰이는가

```text
 [트랜스포트 액션] 검색 액션의 doExecute 뒤가 이 흐름이다
 [구조: 샤드 모델] 어느 샤드들에 물어볼지는 이미 정해진 뒤다
 [구조: 클러스터 상태] 샤드 라우팅이 그 입력이다
```

앞 흐름은 [트랜스포트 액션](../transport-action/README.md), 샤드 배치는 [샤드 모델](../../structure/shard-model/README.md)에 있다.

## 단계

1. [start](01_AbstractSearchAsyncAction.start/README.md)가 첫 페이즈를 띄운다.
2. [executePhase](02_AbstractSearchAsyncAction.executePhase/README.md)가 페이즈 하나를 돌린다.
3. [run](03_AbstractSearchAsyncAction.run/README.md)이 1회차의 샤드 작업을 시작한다.
4. [doRun](04_AbstractSearchAsyncAction.doRun/README.md)이 샤드마다 요청을 건다.
5. [performPhaseOnShard](05_AbstractSearchAsyncAction.performPhaseOnShard/README.md)가 실제로 보낸다.
6. [onShardFailure](06_AbstractSearchAsyncAction.onShardFailure/README.md)가 실패를 재시도하거나 접는다.
7. [onPhaseDone](07_AbstractSearchAsyncAction.onPhaseDone/README.md)이 샤드를 세어 페이즈를 끝낸다.
8. [executeNextPhase](08_AbstractSearchAsyncAction.executeNextPhase/README.md)가 다음 페이즈로 넘긴다.

## 결과가 쓰이는 곳

```text
 outstandingShards
      --> 페이즈 종료의 유일한 판정 기준이다
      --> 초기값이 shardsIts.size() 다 (L156). getNumShards() 와 다르다
      --> finishOneShard 에서만 줄고, 재시도는 건드리지 않는다
      --> 그래서 샤드 하나는 복제본이 몇 개든 정확히 한 번만 카운터를 내린다

 successfulOps
      --> 0이 아니라 skippedCount 로 시작한다 (L157)
      --> 늘기만 하는 것이 아니라 줄기도 한다 (L539)
          뒤 페이즈에서 앞 페이즈의 성공 샤드가 실패하는 경우다

 results
      --> 페이즈마다 다른 객체에 모인다
      --> 마지막에 합쳐져 SearchResponse 가 된다

 종료 지점
      --> sendSearchResponse 는 둘 (FetchLookupFieldsPhase L147, open_pit L461)
      --> onPhaseFailure 로 끝나는 길이 열 곳 넘는다
```

## 다루지 않는 것

각 페이즈의 내부(`DfsQueryPhase`, `RankFeaturePhase`, `FetchSearchPhase`, `ExpandSearchPhase`, `FetchLookupFieldsPhase`), 배치 쿼리 경로(`SearchQueryThenFetchAsyncAction.doRun`)의 노드별 묶기와 BwC 폴백, `QueryPhaseResultConsumer` 의 부분 리듀스, `CanMatchPreFilterSearchPhase` 가 이 앞에 붙는 방식, 스크롤 검색 계열(`SearchScrollAsyncAction`, 별도 계층), 샤드 쪽 실행(`SearchService.executeQueryPhase`)은 같은 뼈대의 곁가지라 요약만 했다.

## 하위 메서드

- [01 start](01_AbstractSearchAsyncAction.start/README.md)
- [02 executePhase](02_AbstractSearchAsyncAction.executePhase/README.md)
- [03 run](03_AbstractSearchAsyncAction.run/README.md)
- [04 doRun](04_AbstractSearchAsyncAction.doRun/README.md)
- [05 performPhaseOnShard](05_AbstractSearchAsyncAction.performPhaseOnShard/README.md)
- [06 onShardFailure](06_AbstractSearchAsyncAction.onShardFailure/README.md)
- [07 onPhaseDone](07_AbstractSearchAsyncAction.onPhaseDone/README.md)
- [08 executeNextPhase](08_AbstractSearchAsyncAction.executeNextPhase/README.md)
- [spi](spi/README.md) — 페이즈 계약, 전이 표
