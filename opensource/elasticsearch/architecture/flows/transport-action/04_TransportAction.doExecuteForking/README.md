# TransportAction.doExecuteForking

상위: [트랜스포트 액션](../README.md)

한 줄짜리 메서드인데, **이 흐름에서 스레드가 갈리는 유일한 자리**다. 그리고 그 한 줄 뒤에 딸린 실패 경로가 본문보다 길다.

## 위치

`server` / `org.elasticsearch.action.support` / `TransportAction.java` L99-L101 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/TransportAction.java#L99-L101))

## 실제 코드

```java
// TransportAction.java L99-L101
    private void doExecuteForking(Task task, Request request, ActionListener<Response> listener) {
        executor.execute(ActionRunnable.wrap(listener, l -> doExecute(task, request, listener)));
    }
```

## 동작 흐름

```text
 L100  executor.execute(ActionRunnable.wrap(listener, l -> doExecute(task, request, listener)))
       |
       +-- 제출에 성공하면
       |     ~~> 다른 스레드가 AbstractRunnable.run 을 돈다
       |           L27  doRun() -> ActionRunnable L101 consumer.accept(listener)
       |                -> doExecute(...)
       |           L28  doExecute 가 동기로 던지면
       |                => onFailure(t) -> listener.onFailure   그 스레드에서 끝
       |           L31  finally onAfter()
       |
       +-- 큐가 거부하면 (EsThreadPoolExecutor L158)
             L159  ActionRunnable 은 AbstractRunnable 이므로
             L167  abstractRunnable.onRejection(e)
                   -> AbstractRunnable L53 onFailure(e)
                   -> ActionRunnable L152 listener.onFailure(e)
             => 호출한 스레드에서 끝난다. doExecute 는 시작도 안 한다
             L169  finally onAfter()
```

```text
 거부는 예외로 올라오지 않는다

 EsThreadPoolExecutor.execute 가 잡아서 처리한다 (L158-173)
 AbstractRunnable 이면 리스너로 보내고
 아니면 다시 던진다 (L172)

 그래서 [03] 의 L140 catch 는 이 거부를 보지 못한다
 이미 리스너가 완료된 뒤이기 때문이다
```

```text
 참조 해제 시점이 여기서 어긋난다

 [03] L134 의 try-with-resources 는
 handler.execute 가 반환할 때 releaseRef 를 닫는다

 포크한 경우 handler.execute 는
 스레드풀에 제출만 하고 바로 반환한다

 즉 doExecute 가 시작하기도 전에 요청 참조가 내려간다
 handleExecution 의 주석이 말하는 "체인 끝까지 갔다"는
 여기서는 "제출까지 갔다"는 뜻이다
```

```text
 람다가 인자를 쓰지 않는다

 L100  ActionRunnable.wrap(listener, l -> doExecute(task, request, listener))

 람다 파라미터 l 대신 바깥의 listener 를 그대로 쓴다
 ActionRunnable.wrap 이 consumer.accept(listener) 로
 같은 객체를 넘기므로 (ActionRunnable L101) 동작은 같다
```

## 결과가 쓰이는 곳

```text
 갈아탄 스레드
      --> doExecute 부터는 그 액션의 스레드풀 위다
      --> 필터는 이미 지난 뒤다. 필터는 호출한 스레드에서 돌았다

 거부 경로
      --> 부하가 높을 때 요청이 여기서 되돌아온다
      --> 클라이언트는 EsRejectedExecutionException 을 받는다
      --> doExecute 가 한 번도 불리지 않았다는 뜻이다

 onAfter
      --> 성공, 예외, 거부 어느 쪽이든 마지막에 불린다 (AbstractRunnable L31, L39)
      --> ActionRunnable 은 이것을 쓰지 않는다
```

## 다루지 않는 것

스레드풀 종류와 큐 크기, `EsAbortPolicy` 의 거부 규칙과 `isForceExecution`, `ActionRunnable` 의 다른 팩터리(`supply`, `wrapReleasing` 등), `AbstractRunnable` 의 `onAfter` 를 쓰는 다른 구현, 액션별 `doExecute` 구현은 같은 뼈대의 곁가지라 요약만 했다.
