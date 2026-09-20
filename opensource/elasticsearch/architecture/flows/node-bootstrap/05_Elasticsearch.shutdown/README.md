# Elasticsearch.shutdown

상위: [노드 기동](../README.md)

노드를 닫고 **keepAlive 래치를 풀어 JVM 을 놓아준다.** 들어오는 길이 둘이고, 아예 안 도는 경우도 둘 있다.

## 위치

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L691-L717 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L691-L717))

## 실제 코드

```java
// Elasticsearch.java L691-L717
    private static void shutdown() {
        ElasticsearchProcess.markStopping();

        if (INSTANCE == null) {
            return; // never got far enough
        }
        var es = INSTANCE;
        try {
            es.node.prepareForClose();
            IOUtils.close(es.node, es.spawner);
            if (es.node.awaitClose(10, TimeUnit.SECONDS) == false) {
                throw new IllegalStateException(
                    "Node didn't stop within 10 seconds. " + "Any outstanding requests or tasks might get killed."
                );
            }
        } catch (IOException ex) {
            throw new ElasticsearchException("Failure occurred while shutting down node", ex);
        } catch (InterruptedException e) {
            LogManager.getLogger(Elasticsearch.class).warn("Thread got interrupted while waiting for the node to shutdown.");
            Thread.currentThread().interrupt();
        } finally {
            LoggerContext context = (LoggerContext) LogManager.getContext(false);
            Configurator.shutdown(context);

            es.keepAliveLatch.countDown();
        }
    }
```

## 동작 흐름

```text
 L692  ElasticsearchProcess.markStopping()
 L694  INSTANCE == null 이면 return
         주석 L695: "never got far enough"
 L698  try
       L699  es.node.prepareForClose()
       L700  IOUtils.close(es.node, es.spawner)
       L701  es.node.awaitClose(10, SECONDS)
             false 면 IllegalStateException     L702-705
 L706  catch (IOException)      -> ElasticsearchException
 L708  catch (InterruptedException) -> warn + interrupt
 L711  finally
       L713  Configurator.shutdown(로깅 컨텍스트)
       L715  es.keepAliveLatch.countDown()
```

```text
 들어오는 길이 둘이다

 L199  JVM 셧다운 훅 (elasticsearch-shutdown)
         System.exit 이 불리면 JVM 이 돌린다
           [01] 의 catch 둘            L104, L106
           CLI 모니터 스레드의 exit     L578, L581
           OS 의 SIGTERM / SIGINT

 L514  윈도우 콘솔 CTRL_CLOSE_EVENT 핸들러
         훅이 아니라 그 핸들러 스레드에서 직접 부른다
         initializeNatives 안에 있다 (L509-520)
```

```text
 안 도는 경우도 둘이다

 1단계 실패 (L157 Bootstrap.exit(1))
   훅 등록이 2단계 L199 라 아직 없다

 스레드 안의 Error
   ElasticsearchUncaughtExceptionHandler 가 halt() 를 쓴다
   그 주석이 이유를 적어 두었다 - 셧다운 훅이 도는 것을 막으려고

 그리고 INSTANCE 가 null 이면 (L694) 들어와도 바로 나간다
   훅은 2단계에 걸리고 INSTANCE 는 3단계 L450 에서 생긴다
   그 사이에 실패하면 이 갈래다
```

```text
 finally 가 둘을 한다

 L713  로깅을 닫는다
 L715  keepAliveLatch 를 푼다

 순서가 이렇다는 것은 로그를 다 쏟고 나서 JVM 을 놓아준다는 뜻이다
 (주석은 없다. 두 줄의 순서를 보고 내가 판단한 것이다)

 L702 의 IllegalStateException 은 아래 두 catch 어느 쪽도 안 잡는다
 finally 만 돌고 훅 스레드 밖으로 나간다
```

```text
 닫는 순서가 셋으로 나뉜다

 prepareForClose   ShutdownPrepareService 가 종료를 준비한다
 close             Node 의 서비스들을 역순으로 멈추고 닫는다
 awaitClose        스레드풀이 끝나기를 10초 기다린다

 세 번째가 실패하면 예외를 던진다
 메시지가 사정을 말한다 - 진행 중인 요청이나 태스크가 죽을 수 있다
```

```text
 훅이 하나 더 있다

 initPidFile 이 pidfile-cleanup 훅을 따로 건다 (L596-602)
 pidfile 을 지우기만 하고 이 메서드와 무관하다

 JVM 훅은 병렬로 돌므로 둘 사이에 순서가 없다
```

## 결과가 쓰이는 곳

```text
 keepAliveLatch.countDown
      --> keepAliveThread 가 풀려 끝난다
      --> 비-데몬 스레드가 사라지면 JVM 이 종료된다
      --> 이것이 안 불리면 프로세스가 안 죽는다

 markStopping
      --> 라이프사이클이 "종료 중"을 알게 된다
      --> 그 뒤 start 시도에 다른 메시지가 나간다

 awaitClose 의 10초
      --> 넘기면 예외를 던지지만 종료는 계속된다
      --> finally 가 이미 등록돼 있기 때문이다
```

## 다루지 않는 것

`Node.close()` 의 서비스 종료 순서와 그 주석들(`IndicesService` 를 마지막에 멈추는 이유 등), `ShutdownPrepareService.prepareForShutdown` 의 준비 작업, `Node.awaitClose` 의 스레드풀 종료와 샤드 확인, `Spawner.close` 의 네이티브 컨트롤러 정리, `ElasticsearchUncaughtExceptionHandler` 의 분류 규칙은 같은 뼈대의 곁가지라 요약만 했다.
