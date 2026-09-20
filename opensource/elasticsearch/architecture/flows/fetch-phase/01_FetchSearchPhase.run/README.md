# FetchSearchPhase.run

상위: [페치 페이즈](../README.md)

열네 줄인데 하는 일은 **스레드를 갈아타는 것**뿐이다. 그리고 그 러너블의 `onFailure` 가 이 페이즈의 동기 구간에서 나는 **모든 예외를 받는 그물**이 된다.

## 위치

`server` / `org.elasticsearch.action.search` / `FetchSearchPhase.java` L78-L92 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/search/FetchSearchPhase.java#L78-L92))

## 실제 코드

```java
// FetchSearchPhase.java L78-L92
    @Override
    protected void run() {
        context.execute(new AbstractRunnable() {

            @Override
            protected void doRun() throws Exception {
                innerRun();
            }

            @Override
            public void onFailure(Exception e) {
                context.onPhaseFailure(NAME, "", e);
            }
        });
    }
```

## 동작 흐름

```text
 L80  context.execute(new AbstractRunnable(){...})
        ~~> 검색 스레드풀로 넘긴다
        AbstractSearchAsyncAction L898-900 이 executor.execute 를 부른다

 L83  doRun -> innerRun()
 L88  onFailure -> context.onPhaseFailure(NAME, "", e)
```

```text
 어느 스레드풀인가

 executor 는 액션 생성자가 받아 둔 것이다 (AbstractSearchAsyncAction L170)
 그 값을 정하는 곳은 TransportSearchAction.asyncSearchExecutor (L2044-2065)

 기본은 ThreadPool.Names.SEARCH 다 (ExecutorSelector L74)
 시스템 인덱스나 시스템 데이터스트림이면
 SYSTEM_READ 또는 SYSTEM_CRITICAL_READ 가 된다

 rewrite 와 can-match 에 쓰이는 SEARCH_COORDINATION 과는 다른 풀이다
```

```text
 onFailure 가 그물이다

 AbstractRunnable.run 이 이렇게 생겼다 (L25-33)
   try { doRun(); } catch (Exception t) { onFailure(t); } finally { onAfter(); }

 innerRun 은 throws Exception 이다 (L94)
 그래서 이 페이즈의 동기 구간에서 나는 예외가 전부 여기로 모인다
   reduce() 가 던진 것                    L98
   executeFetch 가 리스너 등록 전에 던진 것  L210, L246
   마지막 countDown 이 불러낸 merge 의 예외

 거부도 같은 길이다 (AbstractRunnable L52-54)
   onRejection 의 기본 구현이 onFailure 를 부른다
```

```text
 왜 포크하는가

 앞 페이즈의 마지막 샤드 응답이 이 페이즈를 시작시킨다
 그 스레드는 전송 계층의 것이거나 리듀스 스레드다

 거기서 결과 병합과 페치 요청 조립을 하면
 그 스레드가 오래 묶인다

 그래서 검색 스레드풀로 넘기고 그 스레드를 놓아준다
 [검색 페이즈]의 스택이 여기서 풀리는 것도 그 덕이다
```

## 결과가 쓰이는 곳

```text
 갈아탄 스레드
      --> innerRun 이하가 전부 이 스레드에서 돈다
      --> 페치 응답이 오면 또 다른 스레드가 이어받는다

 onPhaseFailure
      --> raisePhaseFailure 로 가서 (AbstractSearchAsyncAction L828)
          성공했던 결과들의 검색 컨텍스트를 일괄 해제하고
          리스너를 실패로 완료시킨다
      --> 그래서 이 페이즈가 죽어도 컨텍스트는 대체로 정리된다
```

## 다루지 않는 것

`AbstractRunnable` 의 실행·거부 처리, `TransportSearchAction.asyncSearchExecutor` 가 풀을 고르는 규칙, `ExecutorSelector` 와 시스템 인덱스 분류, `onPhaseFailure` / `raisePhaseFailure` 의 응답 조립은 같은 뼈대의 곁가지라 요약만 했다.
