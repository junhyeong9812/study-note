# TransportAction.execute

상위: [트랜스포트 액션](../README.md)

포크할지 말지만 정하고 [handleExecution](../02_TransportAction.handleExecution/README.md)으로 넘긴다. 바로 위에 `executeDirect` 가 있는데, 둘의 차이는 **넘기는 handler 하나뿐**이다.

## 위치

`server` / `org.elasticsearch.action.support` / `TransportAction.java` L51-L65 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/TransportAction.java#L51-L65))

## 실제 코드

```java
// TransportAction.java L51-L65 (javadoc 생략)
    protected final void executeDirect(Task task, Request request, ActionListener<Response> listener) {
        handleExecution(task, request, listener, this::doExecute);
    }

    public final void execute(Task task, Request request, ActionListener<Response> listener) {
        handleExecution(
            task,
            request,
            listener,
            executor == EsExecutors.DIRECT_EXECUTOR_SERVICE ? this::doExecute : this::doExecuteForking
        );
    }
```

## 동작 흐름

```text
 [executeDirect] L54
   L55  handleExecution(task, request, listener, this::doExecute)
          언제나 doExecute 다. 분기가 없다

 [execute] L58
   L63  executor == EsExecutors.DIRECT_EXECUTOR_SERVICE
          ? this::doExecute
          : this::doExecuteForking
```

```text
 왜 executeDirect 는 포크하지 않는가

 전송 핸들러를 등록할 때 executor 를 이미 넘겼다
   HandledTransportAction L45-52
     registerRequestHandler(actionName, executor, ..., 
                            (request, channel, task) -> executeDirect(...))

 전송 계층이 그 executor 위에서 핸들러를 부른다
 도착한 시점에 이미 제 스레드풀이므로 또 갈아탈 이유가 없다
 즉 "포크가 없다"가 아니라 "전송 계층이 이미 했다"가 맞다

 등록하는 곳도 HandledTransportAction 하나가 아니다
 자기 생성자에서 같은 패턴으로 직접 등록하는 클래스가 비테스트 25곳 있다

 반대로 execute 는 아무 스레드에서나 불릴 수 있다
 그래서 액션이 원하는 스레드로 옮겨 준다
```

```text
 동일성 비교로 판정한다

 L63 은 equals 가 아니라 == 다

 DIRECT_EXECUTOR_SERVICE 는 EsExecutors 의 단일 인스턴스이고
 그 클래스는 private static final 이라 밖에서 만들 수 없다
 그래서 "직접 실행"을 뜻하는 executor 는 이 하나뿐이고
 동일성 비교가 안전하다
```

```text
 두 메서드 다 final 이다

 액션 구현이 이 순서를 바꿀 수 없다
 바꿀 수 있는 것은 doExecute 뿐이다 (L103 추상)
```

## 결과가 쓰이는 곳

```text
 고른 handler
      --> handleExecution 이 그대로 들고 다닌다
      --> 체인 끝(L135)에서 이것이 불린다
      --> 즉 포크 여부가 체인보다 먼저 정해지고, 실행은 체인 뒤다
          필터는 언제나 호출한 스레드에서 돈다

 execute 의 호출자
      --> 대개 TaskManager L217 이다 (클라이언트 경로)
      --> 다른 액션이 직접 부르기도 한다
          TransportSingleItemBulkWriteAction L49 등
          이때는 태스크를 새로 만들지 않고 물려받는다
```

## 다루지 않는 것

`Executor` 종류와 스레드풀 설정, `HandledTransportAction` 이 전송 핸들러를 등록하는 세부와 직렬화(`Writeable.Reader`), `ChannelActionListener`, `localOnly()` 플레이스홀더, 액션별 `doExecute` 구현은 같은 뼈대의 곁가지라 요약만 했다.
