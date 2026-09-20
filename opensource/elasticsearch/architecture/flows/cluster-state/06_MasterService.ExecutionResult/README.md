# MasterService.ExecutionResult

상위: [클러스터 상태 갱신](../README.md)

태스크 하나의 실행 문맥이다. **실행기가 여기에 결과를 적고, 발행이 끝난 뒤 마스터 서비스가 그것을 읽어 통지한다.** 그 사이에는 아무도 알림을 받지 않는다.

## 위치

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L972-L1193 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L972-L1193))

## 실제 코드

필드 다섯이 상태를 담는다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L978-L991 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L978-L991))

```java
// MasterService.java L978-L991
        @Nullable // if the task is incomplete or failed or onPublicationSuccess supplied
        Consumer<ClusterState> publishedStateConsumer;

        @Nullable // if the task is incomplete or failed or publishedStateConsumer supplied
        Runnable onPublicationSuccess;

        @Nullable // if the task is incomplete or failed or doesn't listen for acks
        ClusterStateAckListener clusterStateAckListener;

        @Nullable // if the task is incomplete or succeeded
        Exception failure;

        @Nullable
        Map<String, List<String>> responseHeaders;
```

미완료 판정이 그 셋을 본다.

```java
// MasterService.java L1009-L1012
        private boolean incomplete() {
            assert assertMasterUpdateOrTestThread();
            return publishedStateConsumer == null && onPublicationSuccess == null && failure == null;
        }
```

배치 실패는 성공 쪽을 지운다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1102-L1108 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1102-L1108))

```java
// MasterService.java L1102-L1108
        void onBatchFailure(Exception failure) {
            // if the whole batch resulted in an exception then this overrides any task-level results whether successful or not
            this.failure = Objects.requireNonNull(failure);
            this.onPublicationSuccess = null;
            this.publishedStateConsumer = null;
            this.clusterStateAckListener = null;
        }
```

> if the whole batch resulted in an exception then this overrides any task-level results whether successful or not

성공 통지가 실패 통지로 빠질 수 있다.

```java
// MasterService.java L1111-L1114
            if (publishedStateConsumer == null && onPublicationSuccess == null) {
                notifyFailure();
                return;
            }
```

ack 리스너는 성공한 태스크만 받는다.

```java
// MasterService.java L1180-L1187
        ContextPreservingAckListener getContextPreservingAckListener() {
            assert incomplete() == false;
            if (clusterStateAckListener == null || failure != null) {
                return null;
            } else {
                return new ContextPreservingAckListener(clusterStateAckListener, threadContextSupplier, this::restoreResponseHeaders);
            }
        }
```

## 동작 흐름

```text
 실행기가 채우는 쪽

 success(Runnable)                           L1028
 success(Consumer<ClusterState>)             L1036
 success(Runnable, ClusterStateAckListener)  L1044
 success(Consumer, ClusterStateAckListener)  L1054
 onFailure(Exception)                        L1063   기록만 한다. 통지 안 한다

 마스터 서비스가 읽는 쪽

 incomplete()                    L1009  셋 다 null 이면 참
 onBatchFailure(Exception)       L1102  failure 를 세우고 성공 쪽 셋을 지운다
 onPublishSuccess(ClusterState)  L1110  소비자가 없으면 notifyFailure 로 빠진다
 onClusterStateUnchanged(...)    L1127  위와 몸통이 사실상 같다
 onPublishFailure(Exception)     L1144  이미 실패였으면 감싸고 addSuppressed
 notifyFailure()                 L1169  task.onFailure(failure)
 getContextPreservingAckListener L1180  실패했으면 null
```

```text
 통지가 미뤄진다

 실행기가 onFailure(L1063)를 불러도 그 자리에서 안 알린다
 failure 필드에 적어 둘 뿐이다

 실제 통지는 발행이 끝난 뒤다
   onPublishSuccess(L1110)가 순회하다가
   성공 소비자가 둘 다 없는 것을 보고 notifyFailure 로 보낸다 (L1111-1113)

 즉 **실패한 태스크도 성공한 태스크와 같은 쓸기에서 통지된다**

 예외는 하나다 - "마스터가 아님" 갈래만 그 자리에서 알린다 (L353-354)
 (주석은 없다. onFailure 와 notifyFailure 의 호출 위치를 비교해 내가 판단한 것이다)
```

```text
 onPublishSuccess 와 onClusterStateUnchanged 가 거의 같다

 둘 다
   소비자가 둘 다 없으면 notifyFailure 로 빠지고
   있으면 문맥을 복원하고 헤더를 되살린 뒤
   onPublicationSuccess 를 우선, 없으면 publishedStateConsumer 를 부른다

 다른 것은 실패 시 로그 문구뿐이다
   "new cluster state"       L1123
   "unchanged cluster state" L1140

 그래서 실행기 예외로 상태가 안 바뀐 경우에도
 실패한 태스크가 제대로 통지된다
```

```text
 onBatchFailure 는 이미 성공한 태스크도 덮는다

 L1104  failure 를 세우고
 L1105  onPublicationSuccess = null
 L1106  publishedStateConsumer = null
 L1107  clusterStateAckListener = null

 주석이 그것을 명시한다 (L1103)
   "if the whole batch resulted in an exception then this overrides any task-level
    results whether successful or not"

 그리고 다른 메서드들과 달리 assert incomplete() 가 없다
 이미 완료된 것도 덮어쓰기 위해서다
```

```text
 ack 리스너가 명시 등록인 이유가 주석에 있다 (L1014-1025)

 예전에는 태스크가 ClusterStateAckListener 를 구현하기만 하면
 자동으로 ack 를 받았다. 원문은 그것을 이렇게 말한다

   "This implicit behaviour was a little troublesome and was removed in favour of
    having the executor explicitly register an ack listener (where necessary) for
    each task it successfully executes."

 되돌아가는 것을 막으려고 success() 안에 assert 를 넣었다

   "We protect against this with some weird-looking assertions in the success()
    methods below which insist that ack-listening tasks register themselves as
    their own ack listener."

 그래서 L1029-1030 같은 assert 가 이상하게 생긴 것이다
 그리고 옛 동작은 unbatched 실행기에 남아 있다고 적어 두었다 (L1024-1025)
```

```text
 onPublishFailure 는 예외를 겹쳐 쌓는다 (L1144-1167)

 태스크가 이미 실패였으면
   L1150  발행 예외 타입으로 새 예외를 만들고
   L1156  원래 실패를 addSuppressed 로 붙인다
   L1157  notifyFailure()

 성공했던 태스크면 그냥 task.onFailure(e) 다 (L1162)

 assert 가 받는 타입을 좁힌다 (L1145)
   FailedToCommitClusterStateException 또는 NotMasterException
```

## 결과가 쓰이는 곳

```text
 incomplete()
      --> assertAllTasksComplete(L1212)가 배치 끝에 검사한다
      --> 실행기가 태스크를 방치하면 assert 로 잡힌다

 failure
      --> 통지 때 task.onFailure 의 인자가 된다
      --> ack 리스너를 null 로 만드는 조건이기도 하다

 responseHeaders
      --> 통지 직전에 restoreResponseHeaders 로 되살린다
      --> 실행기가 흘린 헤더는 innerExecuteTasks 의 finally 가 막는다

 storedContextSupplier
      --> 제출 당시 스레드 문맥이다
      --> 모든 통지가 그 문맥에서 일어난다
```

## 다루지 않는 것

`ClusterStateTaskExecutor.TaskContext` 인터페이스의 나머지 메서드, `captureResponseHeaders` 와 `restoreResponseHeaders` 의 구현, `ContextPreservingAckListener`(L812)와 `TaskAckListener`(L860), `CompositeTaskAckListener`(L955)의 ack 집계, `UnbatchedExecutor`(L708)가 옛 암묵 동작을 유지하는 방식은 같은 뼈대의 곁가지라 요약만 했다.
