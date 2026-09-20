# TransportShardBulkAction.performOnPrimary (private 12-arg)

상위: [문서 색인](../README.md)

러너블 하나를 만들어 **항목을 while 로 돈다**. 이 흐름의 심장이고, 한 번에 끝나지 않을 수 있는 이유도 여기 있다. 공개 오버로드가 둘 더 있지만 기본값만 채워 이쪽으로 내려온다.

## 위치

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L379-L468 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L379-L468))

## 실제 코드

루프를 다시 켜는 장치다. 이 한 줄이 [05](../05_TransportShardBulkAction.handleMappingUpdateRequired/README.md)로 흘러간다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L395-L395 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L395-L395))

```java
// TransportShardBulkAction.java L395-L395
            private final ActionListener<Void> onMappingUpdateDone = ActionListener.wrap(v -> executor.execute(this), this::onRejection);
```

루프 본체다. `false` 가 오면 빠져나간다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L398-L418 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L398-L418))

```java
// TransportShardBulkAction.java L398-L418
            protected void doRun() throws Exception {
                while (context.hasMoreOperationsToExecute()) {
                    if (executeBulkItemRequest(
                        context,
                        updateHelper,
                        nowInMillisSupplier,
                        mappingUpdater,
                        waitForMappingUpdate,
                        onMappingUpdateDone,
                        documentParsingProvider
                    ) == false) {
                        // We are waiting for a mapping update on another thread, that will invoke this action again once its done
                        // so we just break out here.
                        return;
                    }
                    assert context.isInitial(); // either completed and moved to next or reset
                }
                primary.getBulkOperationListener().afterBulk(request.totalSizeInBytes(), System.nanoTime() - startBulkTime);
                // We're done, there's no more operations to execute so we resolve the wrapped listener
                finishRequest();
            }
```

거부되면 남은 항목을 전부 실패로 적고 끝낸다.

`server` / `org.elasticsearch.action.bulk` / `TransportShardBulkAction.java` L420-L452 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/action/bulk/TransportShardBulkAction.java#L420-L452))

```java
// TransportShardBulkAction.java L420-L452
            @Override
            public void onRejection(Exception e) {
                // We must finish the outstanding request. Finishing the outstanding request can include
                // refreshing and fsyncing. Therefore, we must force execution on the WRITE thread.
                executor.execute(new ActionRunnable<>(listener) {

                    @Override
                    protected void doRun() {
                        // Fail all operations after a bulk rejection hit an action that waited for a mapping update and finish the request
                        while (context.hasMoreOperationsToExecute()) {
                            context.setRequestToExecute(context.getCurrent());
                            final DocWriteRequest<?> docWriteRequest = context.getRequestToExecute();
                            onComplete(
                                exceptionToResult(
                                    e,
                                    primary,
                                    docWriteRequest.opType() == DocWriteRequest.OpType.DELETE,
                                    docWriteRequest.version(),
                                    docWriteRequest.id()
                                ),
                                context,
                                null
                            );
                        }
                        finishRequest();
                    }

                    @Override
                    public boolean isForceExecution() {
                        return true;
                    }
                });
            }
```

## 동작 흐름

```text
 L393  new ActionRunnable<>(listener) { ... }.run()      L467 에서 바로 돈다

 L395  onMappingUpdateDone = ActionListener.wrap(
           v -> executor.execute(this),
           this::onRejection)
         이것이 [04] 와 [05] 에 itemDoneListener 로 전달된다

 L398  doRun
       L399  while (context.hasMoreOperationsToExecute())
             L400  executeBulkItemRequest(...)
                   true  -> 다음 항목
                   false -> L411 return    매핑 갱신을 기다린다
             L413  assert context.isInitial()
       L415  afterBulk 통계
       L417  finishRequest   => WritePrimaryResult

 L421  onRejection(e)
       L424  executor.execute(새 ActionRunnable)   ~~> 다른 스레드
             L429  while (남은 항목)
                   L430  setRequestToExecute(getCurrent())
                   L432  onComplete(exceptionToResult(e, ...), context, null)
             L444  finishRequest
       L448  isForceExecution() = true
```

```text
 루프가 빠져나가는 길이 넷이다

 1. hasMoreOperationsToExecute 가 false      정상 종료
 2. executeBulkItemRequest 가 false          매핑 갱신 대기
 3. executeBulkItemRequest 가 예외를 던짐    요청 전체 실패
 4. 재제출이 거부됨                          onRejection

 3번이 그래프에서 잘 안 보인다
 executeBulkItemRequest 는 throws Exception 인데 (L483)
 L400 호출부에 try/catch 가 없다

 그래서 엔진 IOException 이 올라오면
 AbstractRunnable.run 의 catch 가 받아 (L28)
 ActionRunnable.onFailure 로 (L152) 요청 전체를 실패시킨다
 남은 항목은 손도 못 댄다
```

```text
 루프가 돌아오는 길

 2번으로 빠져나간 뒤 매핑 갱신이 끝나면
 [05] 가 itemDoneListener.onResponse(null) 을 부른다   L626, L634

 그 리스너가 L395 다
   v -> executor.execute(this)

 ~~> 같은 러너블을 WRITE executor 에 다시 넣는다
     새 스레드에서 doRun 이 처음부터 돈다
     어디까지 했는지는 context 가 안다

 즉 doRun 은 한 요청에 여러 번 돌 수 있다
 매핑이 바뀌는 문서가 섞여 있으면 그만큼 나눠 돈다
```

```text
 onRejection 이 어디서 오는가

 L395 wrap 의 onResponse 가 executor.execute(this) 를 부르는데
 그게 거부되면 wrap 이 잡아 this::onRejection 으로 보낸다

 최초 실행 L467 은 executor 를 거치지 않으므로
 이 경로가 onRejection 의 유일한 입구다

 그때 새로 만드는 러너블은 isForceExecution 이 true 라 (L448)
 큐가 가득 차도 들어간다
 남은 항목을 실패로 적는 일마저 거부되면 안 되기 때문이다
```

```text
 공개 오버로드 둘은 기본값만 채운다

 L327  8-arg  -> postWriteRefresh=null, DocumentParsingProvider.EMPTY_INSTANCE
 L351  10-arg -> new BulkPrimaryExecutionContext(request, primary), System.nanoTime()

 두 번째가 만드는 context 는 2-arg 생성자라
 압력 트래커가 noop 이고 미리 푼 update 가 비어 있다

 운영 경로는 [02] 가 12-arg 를 직접 부르므로
 공개 오버로드는 테스트에서만 쓰인다
```

## 결과가 쓰이는 곳

```text
 WritePrimaryResult
      --> finishRequest 가 만든다 (L455-465)
      --> context 가 모아 둔 응답과 translog 위치를 담는다
      --> 이것이 레플리카로 가는 근거다

 onMappingUpdateDone
      --> [04] 에 itemDoneListener 로 흘러간다
      --> 루프 재진입 장치이자 거부 감지기다

 afterBulk
      --> 프라이머리의 bulk 통계다
      --> startBulkTime 부터의 시간을 잰다
      --> 배치 경로에서는 [01] L234 가 따로 부른다
```

## 다루지 않는 것

`ActionRunnable` 과 `AbstractRunnable` 의 실행·거부 처리, `WritePrimaryResult` 의 내용과 레플리카 전송, `ActionListener.completeWith` 의 예외 처리, WRITE 스레드풀의 큐 정책은 같은 뼈대의 곁가지라 요약만 했다.
