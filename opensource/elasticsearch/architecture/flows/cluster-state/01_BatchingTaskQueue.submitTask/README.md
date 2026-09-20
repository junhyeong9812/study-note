# BatchingTaskQueue.submitTask

상위: [클러스터 상태 갱신](../README.md)

태스크가 큐에 들어가는 자리다. 서른 줄인데 **경합이 하나 들어 있다** — 실행과 타임아웃이 같은 참조를 두고 다투고, 주석이 그 규약을 한 줄로 못박는다.

## 위치

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1873-L1908 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1873-L1908))

## 실제 코드

태스크를 원자 참조에 담는다.

```java
// MasterService.java L1874-L1875
            final var taskHolder = new AtomicReference<>(task);
            final Scheduler.Cancellable timeoutCancellable;
```

타임아웃이 무한이 아니면 `generic` 스레드에 핸들러를 건다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1876-L1892 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1876-L1892))

```java
// MasterService.java L1880-L1884
                    timeoutCancellable = threadPool.schedule(
                        new TaskTimeoutHandler<>(timeout, source, taskHolder),
                        timeout,
                        threadPool.generic()
                    );
```

그리고 큐에 넣는다.

```java
// MasterService.java L1894-L1907
            perPriorityQueue.queuedTasksCount.getAndIncrement();
            final var entry = new Entry<>(
                source,
                taskHolder,
                insertionIndexSupplier.getAsLong(),
                threadPool.relativeTimeInMillis(),
                threadPool.getThreadContext().newRestorableContext(true),
                timeoutCancellable
            );
            queue.add(entry);

            if (queueSize.getAndIncrement() == 0) {
                perPriorityQueue.execute(processor);
            }
```

경합의 규약은 필드 주석에 있다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1770-L1772 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1770-L1772))

> atomically read and set to null by at most one of {execute, timeout}

## 동작 흐름

```text
 L1874  taskHolder = new AtomicReference<>(task)
 L1876  타임아웃이 무한이면 스케줄 안 한다
 L1880  아니면 TaskTimeoutHandler 를 generic 스레드에 스케줄한다
 L1885  스케줄이 거부되면
 L1887    task.onFailure(NotMasterException)
 L1890    => 여기서 끝낸다. 큐에 안 넣는다
 L1894  queuedTasksCount 를 올린다
 L1895  Entry 를 만든다
 L1903  queue.add(entry)
 L1905  queueSize 가 0 -> 1 이면
 L1906    perPriorityQueue.execute(processor)
```

```text
 실행과 타임아웃이 경합한다

 taskHolder 에서 태스크를 꺼내는 곳이 둘이다

   Entry.acquireForExecution   L1923-1929   taskHolder.getAndSet(null)
   TaskTimeoutHandler.completeTask L1803-1809  taskHolder.getAndSet(null)

 둘 다 getAndSet(null) 이라 **최대 하나만** null 아닌 값을 받는다
 주석도 "at most one" 이라고 적는다 - 안전성 보장이지 생존성 보장이 아니다

 그래서
   실행이 이기면  acquireForExecution 이 타임아웃 스케줄을 취소한다 (L1925-1927)
                  취소가 늦었으면 핸들러가 돌되 null 을 받아 아무것도 안 한다
   타임아웃이 이기면 task.onFailure(ProcessClusterEventTimeoutException)
                  그리고 Processor.run 이 null 을 받아 건너뛴다 (L1971-1972)
```

```text
 그래서 큐에 있는 항목 수와 태스크 수가 다를 수 있다

 Processor.run 은 queueSize 만큼 poll 하지만 (L1964-1969)
 acquireForExecution 이 null 을 주면 세지 않는다 (L1971-1978)

 그 결과 taskCount 가 0 이면 배치를 아예 안 돌린다 (L1980-1983)
 전부 타임아웃된 경우다
```

```text
 겹 1 의 배칭이 여기서 정해진다

 L1905  if (queueSize.getAndIncrement() == 0) { … }

 즉 **큐가 비어 있었을 때만** Processor 를 우선순위 큐에 넣는다
 이미 하나 들어 있으면 그냥 queue.add 만 하고 끝이다

 그래서 큐당 대기 중인 Processor 가 언제나 최대 하나이고
 그 Processor 가 돌 때 그동안 쌓인 것을 통째로 가져간다

 배치 크기를 정하는 것은 설정값이 아니라 **타이밍**이다
 (주석은 없다. 두 카운터의 쓰임을 보고 내가 판단한 것이다)
```

```text
 스케줄 거부는 큐에 못 들어간다

 L1885-1891 의 catch 는 큐에 넣기 **전**이다
 그래서 셧다운 중에 들어온 태스크는
 NotMasterException 을 받고 바로 끝난다

 assert 가 그 상황을 좁힌다 (L1886)
   e instanceof EsRejectedExecutionException esre && esre.isExecutorShutdown()
```

## 결과가 쓰이는 곳

```text
 Entry
      --> Processor.run 이 poll 해서 ExecutionResult 로 바꾼다
      --> storedContextSupplier 가 제출 당시 스레드 문맥을 들고 있다

 queueSize
      --> 겹 1 의 배칭 경계다
      --> Processor.run 이 getAndSet(0) 으로 통째로 가져간다

 timeoutCancellable
      --> acquireForExecution 이 실행을 이기면 취소한다
      --> 취소를 못 해도 completeTask 가 null 을 받아 무해하다
```

## 다루지 않는 것

`PerPriorityQueue.execute` 이후의 처리기 포크(그쪽은 [queuesProcessor](../02_MasterService.queuesProcessor/README.md)에 있다), `ThreadContext.newRestorableContext` 가 보존하는 것, `insertionIndexSupplier` 와 `insertionTimeMillis` 가 쓰이는 지표 계산(`getMaxTaskWaitTime`, `pendingTasks`), `isInfiniteTaskTimeout` 의 판정, `MasterServiceTaskQueue` 인터페이스의 나머지는 같은 뼈대의 곁가지라 요약만 했다.
