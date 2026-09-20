# MasterService.innerExecuteTasks

상위: [클러스터 상태 갱신](../README.md)

실행기를 부르는 유일한 자리다. 그리고 **실행기를 못 믿는 장치가 셋** 걸려 있다 — 버전을 건드렸는지, 태스크를 다 처리했는지, 응답 헤더를 흘렸는지.

## 위치

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1227-L1284 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1227-L1284))

## 실제 코드

실행기를 부른다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1238-L1245 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1238-L1245))

```java
// MasterService.java L1239-L1245
                final var updatedState = executor.execute(
                    new ClusterStateTaskExecutor.BatchExecutionContext<>(
                        previousClusterState,
                        executionResults,
                        threadContext::newStoredContext
                    )
                );
```

버전을 건드렸으면 예외다.

```java
// MasterService.java L1246-L1254
                if (versionNumbersPreserved(previousClusterState, updatedState) == false) {
                    // Shenanigans! Executors mustn't meddle with version numbers. Perhaps the executor based its update on the wrong
                    // initial state, potentially losing an intervening cluster state update. That'd be very bad!
                    final var exception = new IllegalStateException(
                        "cluster state update executor did not preserve version numbers: [" + summary.toString() + "]"
                    );
                    assert threadContext.getTransient(TEST_ONLY_EXECUTOR_MAY_CHANGE_VERSION_NUMBER_TRANSIENT_NAME) != null : exception;
                    throw exception;
                }
```

> Shenanigans! Executors mustn't meddle with version numbers. Perhaps the executor based its update on the wrong initial state, potentially losing an intervening cluster state update. That'd be very bad!

그런데 그 예외는 바로 아래 `catch` 가 잡는다.

```java
// MasterService.java L1269-L1272
                for (final var executionResult : executionResults) {
                    executionResult.onBatchFailure(e);
                }
                return previousClusterState;
```

`finally` 에 헤더 검사가 있다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L1273-L1282 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L1273-L1282))

버전 검사 자체에는 예외가 하나 있다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L676-L688 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L676-L688))

```java
// MasterService.java L676-L688
    private static boolean versionNumbersPreserved(ClusterState oldState, ClusterState newState) {
        if (oldState.nodes().getMasterNodeId() == null && newState.nodes().getMasterNodeId() != null) {
            return true; // NodeJoinExecutor is special, we trust it to do the right thing with versions
        }

        if (oldState.version() != newState.version()) {
            return false;
        }
        if (oldState.metadata().version() != newState.metadata().version()) {
            return false;
        }
        return true;
    }
```

버전을 붙이는 것은 여기다.

`server` / `org.elasticsearch.cluster.service` / `MasterService.java` L651-L670 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/service/MasterService.java#L651-L670))

```java
// MasterService.java L654-L657
            Builder builder = incrementVersion(newClusterState);
            if (previousClusterState.metadata() != newClusterState.metadata()) {
                builder.metadata(newClusterState.metadata().withIncrementedVersion());
            }
```

> only the master controls the version numbers

## 동작 흐름

```text
 innerExecuteTasks                                L1227
 L1234  threadContext.newStoredContext() 로 감싼다
 L1238  try
 L1239    executor.execute(new BatchExecutionContext<>(previousClusterState,
                                                       executionResults,
                                                       threadContext::newStoredContext))
 L1246    versionNumbersPreserved 가 거짓이면
 L1249      IllegalStateException 을 만들고
 L1252      assert (테스트 전용 transient 가 걸려 있어야 한다)
 L1253      throw
 L1255    return updatedState
 L1256  catch (Exception e)
 L1257    trace 로그 (이전 상태를 통째로 덤프한다)
 L1269    태스크마다 onBatchFailure(e)
 L1272    return previousClusterState
 L1273  finally
 L1274    assert 응답 헤더가 비어 있다

 executeTasks                                     L1195
 L1202  innerExecuteTasks 를 부르고
 L1203  마스터를 제거하는 갱신이면 AssertionError
 L1208  assert assertAllTasksComplete(...)
```

```text
 L1253 의 throw 는 밖으로 안 나간다 - 다만 assert 가 꺼져 있을 때만이다

 L1238 의 try 안에 있고 L1256 의 catch 가 잡는다
 그래서 버전 조작은 "예외로 배치가 터지는 것"이 아니라
 **모든 태스크가 실패하고 상태는 그대로인 것**이 된다

 그런데 그 위에 assert 가 한 줄 있다 (L1252)
   assert threadContext.getTransient(TEST_ONLY_...) != null : exception;

 -ea 로 돌고 테스트용 transient 가 없으면 이 줄이 먼저 터진다
 그리고 AssertionError 는 Error 라서 L1256 의 catch (Exception) 이 못 잡는다

 즉 갈래가 둘이다
   운영 (assert 꺼짐)   L1252 는 no-op, L1253 이 catch 에 잡힌다
   테스트 (-ea)         L1252 가 AssertionError 를 던지고 밖으로 나간다

 (주석은 없다. assert 의 위치와 catch 의 타입을 맞춰 보고 내가 판단한 것이다)

 그리고 L1272 가 previousClusterState 를 돌려주므로
 호출자의 L368 참조 비교가 참이 되어 상태 불변 갈래로 간다

 (주석은 없다. try/catch 의 범위와 반환값을 이어 보고 내가 판단한 것이다)
```

```text
 버전 검사에 면제가 하나 있다 (L677-679)

 이전 상태에 마스터가 없고 새 상태에 있으면 무조건 통과한다

 주석이 이유를 적어 두었다
   "NodeJoinExecutor is special, we trust it to do the right thing with versions"

 마스터 선출 자체가 버전 규칙 밖이라는 뜻이다
```

```text
 patchVersions 도 참조 비교로 시작한다 (L652)

 previousClusterState != newClusterState 일 때만 손댄다

 그 안에서 또 한 번 참조 비교를 한다 (L655)
   메타데이터 **객체**가 달라졌을 때만 메타데이터 버전을 올린다

 즉 상태가 바뀌어도 메타데이터가 그대로면 메타데이터 버전은 안 오른다
```

```text
 실행기를 못 믿는 장치가 셋이다

 1. 버전을 건드렸나      L1246-1253   IllegalStateException (catch 에 흡수)
                                   -ea 면 L1252 의 assert 가 먼저 터진다
 2. 태스크를 다 처리했나  L1208 -> L1212-1223  assert
      executionResults 중 incomplete() 인 것이 있으면 안 된다
 3. 응답 헤더를 흘렸나    L1273-1282  assert (finally)
      메시지가 대안까지 적어 준다 - TaskContext#captureResponseHeaders 를 쓰거나
      BatchExecutionContext#dropHeadersContext 로 억누르라고

 2번과 3번은 assert 라 -ea 일 때만 돈다
 1번의 throw 는 실제 코드지만 그 위의 L1252 는 assert 다

 그리고 assert 가 터지면 AssertionError 다 - Error 라서
 catch (Exception) 을 전부 통과해 밖으로 나간다
```

```text
 L1206 의 AssertionError 는 assert 문이 아니다

   throw new AssertionError("update task submitted to MasterService cannot remove master")

 무조건 던진다. -ea 와 무관하다

 그리고 Error 이므로 ActionListener.run 의 catch(Exception)도
 AbstractRunnable 의 catch(Exception)도 잡지 못한다
 즉 배치 완료 리스너까지 못 가고 onCompletion 도 안 돈다

 (그 뒤를 스레드풀이 어떻게 처리하는지는 확인하지 못했다)
```

## 결과가 쓰이는 곳

```text
 돌려준 ClusterState
      --> patchVersions 를 거쳐 호출자의 참조 비교로 간다
      --> previousClusterState 그대로면 발행을 건너뛴다

 ExecutionResult 들
      --> 실행기가 success / onFailure 로 채워 둔 것을
          호출자가 통지 단계에서 읽는다

 저장된 스레드 문맥
      --> 실행기가 헤더를 흘려도 여기서 막힌다
      --> 태스크별 헤더는 ExecutionResult 가 따로 들고 있다
```

## 다루지 않는 것

`ClusterStateTaskExecutor.execute` 구현들의 사정, `BatchExecutionContext` 가 실행기에 주는 것들(`initialState`, `taskContexts`, `dropHeadersContext`), `ThreadContext` 의 저장·복원 규칙, `TEST_ONLY_EXECUTOR_MAY_CHANGE_VERSION_NUMBER_TRANSIENT_NAME` 의 테스트 용법, `ClusterState.Builder.incrementVersion` 의 구현은 같은 뼈대의 곁가지라 요약만 했다. 실행기 계약은 [spi](../spi/README.md)에 있다.
