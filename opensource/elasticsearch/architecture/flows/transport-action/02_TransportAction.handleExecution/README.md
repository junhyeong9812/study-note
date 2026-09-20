# TransportAction.handleExecution

상위: [트랜스포트 액션](../README.md)

[execute](../01_TransportAction.execute/README.md)와 `executeDirect` 가 모이는 자리다. 검증하고, 요청 참조 수를 올리고, 필터 체인을 만들어 [proceed](../03_RequestFilterChain.proceed/README.md)로 넘긴다. 짧은데 **리스너가 여러 겹으로 싸이는 곳**이라 순서가 중요하다.

## 위치

`server` / `org.elasticsearch.action.support` / `TransportAction.java` L67-L97 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/TransportAction.java#L67-L97))

## 실제 코드

```java
// TransportAction.java L67-L97
    private void handleExecution(
        Task task,
        Request request,
        ActionListener<Response> listener,
        TransportActionHandler<Request, Response> handler
    ) {
        final ActionRequestValidationException validationException;
        try {
            validationException = request.validate();
        } catch (Exception e) {
            assert false : new AssertionError("validating of request [" + request + "] threw exception", e);
            logger.warn("validating of request [" + request + "] threw exception", e);
            listener.onFailure(e);
            return;
        }
        if (validationException != null) {
            listener.onFailure(validationException);
            return;
        }
        if (task != null && request.getShouldStoreResult()) {
            listener = new TaskResultStoringActionListener<>(taskManager, task, listener);
        }

        // Note on request refcounting: we can be sure that either we get to the end of the chain (and execute the actual action) or
        // we complete the response listener and short-circuit the outer chain, so we release our request ref on both paths, using
        // Releasables#releaseOnce to avoid a double-release.
        request.mustIncRef();
        final var releaseRef = Releasables.releaseOnce(request::decRef);
        RequestFilterChain<Request, Response> requestFilterChain = new RequestFilterChain<>(this, logger, handler, releaseRef);
        requestFilterChain.proceed(task, actionName, request, ActionListener.runBefore(listener, releaseRef::close));
    }
```

## 동작 흐름

```text
 L74  request.validate()
      |
      +-- 예외를 던지면                                L76
      |     L77  assert false : new AssertionError(...)
      |           assert 가 켜져 있으면 여기서 AssertionError 가 난다
      |           L79 까지 가지 못하고 위로 던져진다
      |     L78  logger.warn(...)
      |     L79  listener.onFailure(e)   => 끝
      |
      +-- 검증 오류를 돌려주면                          L82
            L83  listener.onFailure(validationException)   => 끝

 L86  task != null && request.getShouldStoreResult()
      +-- listener 를 TaskResultStoringActionListener 로 바꾼다  L87
            끝나면 결과를 인덱스에 저장한다

 L93  request.mustIncRef()
 L94  releaseRef = Releasables.releaseOnce(request::decRef)
 L95  new RequestFilterChain(this, logger, handler, releaseRef)
 L96  chain.proceed(task, actionName, request,
                    ActionListener.runBefore(listener, releaseRef::close))
```

```text
 리스너가 세 겹이 된다

 바깥부터
   runBefore(releaseRef::close)        L96  완료 직전에 참조를 놓는다
   TaskResultStoringActionListener     L87  결과를 저장한다 (조건부)
   원래 listener

 순서가 이렇다는 것은
 참조 해제가 결과 저장보다 먼저 돈다는 뜻이다

 runBefore 는 안쪽을 assertOnce 로 한 번 더 감싼다
 그 assertOnce 는 assert 가 켜져 있을 때만 실제로 감싼다
```

```text
 참조 수를 왜 여기서 올리는가

 주석이 직접 적어 두었다 (L90-92)
   체인 끝까지 가서 실제 액션을 실행하거나
   리스너를 완료시키고 체인을 짧게 끊거나 둘 중 하나다
   그래서 양쪽 경로에서 다 놓아야 하고
   releaseOnce 로 이중 해제를 막는다

 놓는 자리가 둘이다
   L134  체인 끝의 try-with-resources
   L96   리스너 완료 직전의 runBefore

 먼저 오는 쪽이 놓고 나머지는 아무 일도 하지 않는다
```

```text
 handler 는 이미 정해져 있다

 execute 가 골라서 넘겨준 것이다 (L63)
 이 메서드는 그것을 체인에 실어 나르기만 한다

 그래서 포크 여부가 필터보다 먼저 정해진다
 필터는 언제나 호출한 스레드에서 돈다
```

## 결과가 쓰이는 곳

```text
 검증 실패
      --> 필터도 타지 않고 끝난다
      --> 즉 보안 필터가 보기 전에 거절되는 요청이 있다

 TaskResultStoringActionListener
      --> getShouldStoreResult 인 요청에만 붙는다
      --> reindex, force merge, ml 의 긴 작업들이 그렇다
      --> 저장에 실패하면 원래 오류 대신 저장 오류가 나갈 수 있다

 releaseRef
      --> 포크하면 제출 직후에 닫힌다
      --> 그 시점에 doExecute 는 아직 시작도 안 했을 수 있다

 RequestFilterChain
      --> 요청 하나에 하나씩 새로 만든다
      --> 안에 AtomicInteger 하나를 들고 몇 번째 필터인지 센다
```

## 다루지 않는 것

`ActionRequest.validate` 구현들, `TaskResultStoringActionListener` 와 `TaskManager.storeResult` 의 저장 경로, `Releasables.releaseOnce` 의 구현, `ActionListener.runBefore` / `assertOnce` 의 래핑 세부, `getShouldStoreResult` 를 켜는 요청 종류는 같은 뼈대의 곁가지라 요약만 했다.
