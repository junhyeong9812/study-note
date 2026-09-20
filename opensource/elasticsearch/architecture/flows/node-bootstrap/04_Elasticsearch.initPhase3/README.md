# Elasticsearch.initPhase3

상위: [노드 기동](../README.md)

**노드를 만들고 시작하고 준비 신호를 보낸다.** 이 단계부터 entitlement 정책 아래에서 돌고, 스레드를 띄울 수 있고, 로그를 쓸 수 있다.

## 위치

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L437-L475 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L437-L475))

## 실제 코드

```java
// Elasticsearch.java L438-L474
        checkLucene();

        Node node = new Node(bootstrap.environment(), bootstrap.pluginsLoader()) {
            @Override
            protected void validateNodeBeforeAcceptingRequests(
                final BootstrapContext context,
                final BoundTransportAddress boundTransportAddress,
                List<BootstrapCheck> checks
            ) throws NodeValidationException {
                BootstrapChecks.check(context, boundTransportAddress, checks);
            }
        };
        INSTANCE = new Elasticsearch(bootstrap.spawner(), node);

        // any secure settings must be read during node construction
        IOUtils.close(bootstrap.secureSettings());

        INSTANCE.start();

        if (ReadinessService.enabled(bootstrap.environment())) {
            waitForNodeReady(INSTANCE.node.injector().getInstance(ReadinessService.class));
        }

        if (bootstrap.args().daemonize()) {
            LogConfigurator.removeConsoleAppender();
        }

        // DO NOT MOVE THIS
        // Signaling readiness to accept requests must remain the last step of initialization. Note that it is extremely
        // important closing the err stream to the CLI when daemonizing is the last statement since that is the only
        // way to pass errors to the CLI
        bootstrap.sendCliMarker(BootstrapInfo.SERVER_READY_MARKER);
        if (bootstrap.args().daemonize()) {
            bootstrap.closeStreams();
        } else {
            startCliMonitorThread(System.in);
        }
```

## 동작 흐름

```text
 L438  checkLucene()
 L440  new Node(environment, pluginsLoader) { ... }
         익명 서브클래스가 validateNodeBeforeAcceptingRequests 를 오버라이드
         그 안에서 BootstrapChecks.check 를 부른다 (L447)
         정의일 뿐이다. 실행은 아래 L455 를 거친다
 L450  INSTANCE = new Elasticsearch(spawner, node)
 L453  IOUtils.close(bootstrap.secureSettings())
 L455  INSTANCE.start()
         L687  node.start()
         L688  keepAliveThread.start()
 L457  ReadinessService 가 켜져 있으면
         L458  waitForNodeReady(...)
 L461  daemonize 면
         L462  LogConfigurator.removeConsoleAppender()
 L469  bootstrap.sendCliMarker(SERVER_READY_MARKER)
 L470  daemonize 면
         L471  bootstrap.closeStreams()
       아니면
         L473  startCliMonitorThread(System.in)
```

```text
 javadoc 이 이 단계를 정의한다 (L422-423)

   "Phase 3 consists of everything after entitlements are initialized.
    Up until now, the system has been single threaded. This phase can
    spawn threads, write to the log, and is subject to the entitlement policy."

 그리고 끝났을 때 만족해야 하는 것을 넷으로 적는다 (L425-431)
   노드 컴포넌트가 만들어지고 시작됐다
   정리가 끝났다
   메인 외에 최소 하나의 스레드가 살아 있고 메인 종료 후에도 산다
   부모 CLI 에 알렸다
```

```text
 new Node(...) 한 줄이 노드 조립 전체다

 Node 의 생성자는 필드 대입만 한다 (Node L199-211)
 실제 조립은 NodeConstruction.prepareConstruction 이다 (Node L193)

 그 클래스의 javadoc 이 왜 밖으로 뺐는지 적어 두었다 (NodeConstruction L304-310)
   "Constructing a Node is a complex operation, involving many
    interdependent services. Separating out this logic into a dedicated
    class is a lot clearer and more flexible than doing all this logic
    inside a constructor in Node."

 동기 호출이다. 별도 스레드가 아니다
 실패하면 열어 둔 자원을 닫고 다시 던진다
```

```text
 BootstrapChecks 는 여기서 실행되지 않는다

 L440-449 는 오버라이드를 정의할 뿐이다
 실행은 L455 INSTANCE.start() -> node.start() -> Node L358 이다

 Node 의 javadoc 이 그 자리를 계약으로 말한다 (Node L664-668)
   "Hook for validating the node after network services are started
    but before the cluster service is started and before the network
    service starts accepting incoming network requests."

 검사가 실패하면 NodeValidationException 이 올라와
 [01] 의 catch 가 종료 코드 78 로 끝낸다
```

```text
 node.start() 안에 콜백 대기가 있다

 마스터가 아직 없으면 (Node L388)
   ClusterStateObserver 리스너를 걸고 latch.await() 로 막힌다 (L391-417)
   initialStateTimeout 까지 기다린다

 기동 중 셧다운이 시작되면 거기서 early return 한다 (L423-427)
 그러면 HTTP 서버도 ReadinessService 도 시작되지 않는다

 그런데 이 메서드는 그 사정을 모르고 L457 로 계속 간다
 (ReadinessService 가 안 떴을 때 waitForNodeReady 가 어떻게 되는지는
  ReadinessService 를 끝까지 읽지 않아 확인하지 못했다)
```

```text
 waitForNodeReady 는 블로킹이다

 L552  readiness 소켓이 바인드되면 countDown 하는 리스너를 건다
 L554  ready.await()

 이미 바인드돼 있으면 리스너가 즉시 불린다
 아니면 다른 스레드가 바인드할 때까지 메인 스레드가 멈춘다
```

```text
 daemonize 분기가 둘로 쪼개져 있다

 L461-463  콘솔 appender 제거      마커보다 앞
 L470-472  스트림 닫기              마커보다 뒤

 주석이 그 이유를 말한다 (L465-468)
   마커가 초기화의 마지막이어야 하고
   스트림 닫기가 문장으로서 마지막이어야 한다
   그것이 CLI 에 오류를 전할 유일한 방법이기 때문이다

 데몬이 아니면 대신 CLI 모니터 스레드를 띄운다 (L473)
   stdin 에서 1바이트를 읽어
   종료 마커면 exit(0), 그 외나 EOF 면 exit(1)
   즉 부모 CLI 가 죽으면 노드도 죽는다
```

## 결과가 쓰이는 곳

```text
 INSTANCE
      --> 셧다운 훅이 이것을 본다
      --> L450 이전에 실패하면 훅이 즉시 return 한다

 keepAliveThread
      --> 비-데몬이라 메인이 끝나도 JVM 이 산다
      --> javadoc 의 셋째 조건이 이것이다

 SERVER_READY_MARKER
      --> 부모 CLI 가 이것을 보고 성공으로 판정한다
      --> 이 뒤의 오류는 전달할 수단이 없다

 닫힌 비밀 설정
      --> 노드 구성이 끝났으니 keystore 를 메모리에 둘 이유가 없다
```

## 다루지 않는 것

`NodeConstruction.prepareConstruction` 의 서비스 조립, `Node.start()` 가 서비스를 시작하는 전체 순서, `BootstrapChecks` 의 개별 검사와 강제 조건, `ReadinessService` 의 소켓 바인딩과 클러스터 상태 연동, `checkLucene` 의 버전 검사, `sendCliMarker` 와 부모 CLI 프로토콜은 같은 뼈대의 곁가지라 요약만 했다.
