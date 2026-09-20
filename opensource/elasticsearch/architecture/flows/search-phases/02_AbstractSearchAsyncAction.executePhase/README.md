# AbstractSearchAsyncAction.executePhase

상위: [검색 페이즈](../README.md)

**페이즈 하나를 돌리는 열 줄**이다. 체인의 모든 칸이 이 메서드를 지난다. `private` 이고 호출처가 둘뿐이라 — 시작과 전이 — 체인의 목이 여기다.

## 위치

`server` / `org.elasticsearch.action.search` / `AbstractSearchAsyncAction.java` L430-L439 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/AbstractSearchAsyncAction.java#L430-L439))

## 실제 코드

```java
// AbstractSearchAsyncAction.java L430-L439
    private void executePhase(SearchPhase phase) {
        try {
            phase.run();
        } catch (RuntimeException e) {
            if (logger.isDebugEnabled()) {
                logger.debug(() -> format("Failed to execute [%s] while moving to [%s] phase", request, phase.getName()), e);
            }
            onPhaseFailure(phase.getName(), "", e);
        }
    }
```

## 동작 흐름

```text
 L432  phase.run()
 L433  catch (RuntimeException e)
       L434  디버그 로그
       L437  onPhaseFailure(phase.getName(), "", e)
```

```text
 호출처가 둘뿐이다

 L247  start 에서 첫 페이즈
 L426  executeNextPhase 에서 다음 페이즈

 private 이라 페이즈가 스스로 자기를 실행할 수 없다
 반드시 이 둘 중 하나를 거친다
```

```text
 중첩 호출이지 되돌아감이 아니다

 L426 이 이 메서드를 부르고
 이 메서드가 phase.run() 을 부른다

 그래서 페이즈가 이어질수록 스택이 쌓인다

 다만 모든 페이즈가 쌓는 것은 아니다
   FetchSearchPhase.run L80      context.execute 로 포크. 스택을 푼다
   RankFeaturePhase.run L80      같음
   DfsQueryPhase.run             샤드 요청만 보내고 반환
   ExpandSearchPhase.run L71     collapse 가 아니면 그 자리에서 다음으로
                                 그래서 expand 와 fetch_lookup_fields 가 한 스택에 겹친다

 페이즈 수가 최대 여섯이라 상한은 있다
```

```text
 RuntimeException 만 잡는다

 checked 예외와 Error 는 호출자에게 전파된다
 SearchPhase.run 이 throws 를 선언하지 않으므로
 checked 예외가 올라올 일은 없다

 그런데 이 catch 가 모든 페이즈 실패를 잡는 것은 아니다
   executeNextPhase 의 nextPhaseSupplier.get() (L413) 은 이 try 밖이다
   FetchSearchPhase 는 그 서플라이어 안에서 결과 병합을 한다 (L279)
   거기서 나는 예외는 이 catch 가 못 받는다
```

```text
 run 이 페이즈마다 다르다

 1회차   ASAA.run L251 (final)
 2회차~  DfsQueryPhase L67, RankFeaturePhase L79, FetchSearchPhase L79,
         ExpandSearchPhase L68, FetchLookupFieldsPhase L78
         그리고 open_pit 의 익명 구현 (TransportOpenPointInTimeAction L460)

 즉 [03]~[07] 은 1회차에만 해당한다
```

## 결과가 쓰이는 곳

```text
 phase.run()
      --> 페이즈마다 하는 일이 완전히 다르다
      --> 1회차는 샤드에 흩어지고, fetch 는 문서를 가져오고,
          expand 는 collapse 를 펼치고, lookup 은 참조 필드를 채운다

 onPhaseFailure
      --> raisePhaseFailure 를 거쳐 리스너를 실패로 완료시킨다 (L828-843)
      --> 체인이 여기서 끊긴다

 phase.getName()
      --> 실패 응답에 어느 페이즈에서 죽었는지 실린다
      --> 메트릭 기록에도 쓰인다
```

## 다루지 않는 것

각 `SearchPhase` 구현의 `run()` 내부, `onPhaseFailure` 와 `raisePhaseFailure` 의 응답 조립, `context.execute` 가 쓰는 SEARCH_COORDINATION 스레드풀, `SearchPhase` 의 `doCheckNoMissingShards` 는 같은 뼈대의 곁가지라 요약만 했다.
