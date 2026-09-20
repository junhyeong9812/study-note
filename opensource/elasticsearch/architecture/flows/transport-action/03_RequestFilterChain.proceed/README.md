# RequestFilterChain.proceed

상위: [트랜스포트 액션](../README.md)

필터를 **하나씩 태우고 마지막에 실제 액션을 부른다**. 필터가 스스로 이 메서드를 다시 불러 사슬을 잇는 구조라, 필터가 안 부르면 거기서 끊긴다.

## 위치

`server` / `org.elasticsearch.action.support` / `TransportAction.java` L127-L144 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/support/TransportAction.java#L127-L144))

## 실제 코드

```java
// TransportAction.java L127-L144
        @Override
        public void proceed(Task task, String actionName, Request request, ActionListener<Response> listener) {
            int i = index.getAndIncrement();
            try {
                if (i < this.action.filters.length) {
                    this.action.filters[i].apply(task, actionName, request, listener, this);
                } else if (i == this.action.filters.length) {
                    try (releaseRef) {
                        handler.execute(task, request, listener);
                    }
                } else {
                    listener.onFailure(new IllegalStateException("proceed was called too many times"));
                }
            } catch (Exception e) {
                logger.trace("Error during transport action execution.", e);
                listener.onFailure(e);
            }
        }
```

## 동작 흐름

```text
 L129  i = index.getAndIncrement()
         몇 번째 호출인지 센다. AtomicInteger 다

 L131  i < filters.length
       +-- L132  filters[i].apply(task, actionName, request, listener, this)
             필터에게 자기 자신(this)을 체인으로 넘긴다
             필터가 chain.proceed 를 부르면 i 가 하나 올라간 채 다시 여기로 온다

 L133  i == filters.length
       +-- L134  try (releaseRef)
             +-- L135  handler.execute(task, request, listener)
                   execute 로 왔으면 doExecute 또는 doExecuteForking
                   executeDirect 로 왔으면 doExecute

 L137  i > filters.length
       +-- L138  listener.onFailure(IllegalStateException("proceed was called too many times"))

 L140  catch (Exception e)
       +-- L141  logger.trace(...)
       +-- L142  listener.onFailure(e)
```

```text
 필터가 사슬을 잇는 방법이 셋이다

 1. chain.proceed 를 부른다        다음 필터로 간다
 2. listener 를 완료시키고 만다    체인이 끊긴다. 액션은 안 돈다
 3. 예외를 던진다                  L140 의 catch 가 받아 L142 로 보낸다

 2번을 쓰는 예가 라이선스 검사다
 3번을 쓰는 예가 SecurityActionFilter 의 라이선스 만료 처리다
```

```text
 돌아오는 것이 같은 스레드라고 단정할 수 없다

 ActionFilter.Simple             동기다. apply 가 true 면 대신 proceed 를 부른다
 MappedActionFilters             동기로 내부 체인에 넘긴다
 SecurityActionFilter            SubscribableListener 로 일부러 끊는다

 SecurityActionFilter 의 주석이 이유를 적어 두었다 (L196-198)
   인증과 인가가 현재 스레드에서 끝나는 흔한 경우에
   쌓인 함수 호출 스택을 풀고 나서 체인의 나머지로 내려가려고

 그래서 chain.proceed 가 L202 의 리스너 콜백 안에서 불린다
 인증이 원격 조회로 비동기가 되면 그 스레드가 이어받는다
```

```text
 catch 가 두 가지를 다 받는다

 L140 의 catch 는 L132 의 filters[i].apply 와
 L135 의 handler.execute 를 함께 감싼다

 그래서 "필터가 던진 예외"와
 "doExecute 가 동기로 던진 예외"가 같은 자리로 온다
 포크한 뒤에 던진 것은 여기 안 온다. 그쪽은 04 에서 다룬다
```

## 결과가 쓰이는 곳

```text
 index
      --> AtomicInteger 라 여러 스레드가 나눠 진행해도 센다
      --> 필터가 비동기로 돌아와도 자리를 잃지 않는다
      --> MappedActionFilters 의 내부 체인은 plain int 를 쓴다 (L58)
          과다 호출 방어도 없다. 바깥 체인과 성질이 다르다

 releaseRef
      --> 여기서만 닫힌다. 체인이 끝까지 간 경우다
      --> 끊긴 경우는 handleExecution 의 runBefore 가 닫는다

 "proceed was called too many times"
      --> 필터가 실수로 두 번 부른 것을 잡는다
      --> 예외를 던지지 않고 리스너로 보낸다
```

## 다루지 않는 것

각 `ActionFilter` 구현의 내부 판단(`SecurityActionFilter` 의 인증·인가, `MlUpgradeModeActionFilter` 의 금지 액션 목록), `SubscribableListener` 의 동작, 필터 등록과 정렬이 일어나는 기동 경로(`ActionModule.setupActionFilters`), `MappedActionFilters` 의 액션별 매핑 내부는 같은 뼈대의 곁가지라 요약만 했다. `doExecute` 안쪽도 범위 밖이다.
