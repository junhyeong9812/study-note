# spi

상위: [노드 기동](../README.md)

이 흐름의 실체는 계약이 아니라 **순서**다. 소스가 순서를 못박은 자리를 모았다. 인용은 주석 원문이고, 그 아래 설명은 원문이 이유를 말하지 않을 때 내가 붙인 것이다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19).

## 대문자로 못박은 둘

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L148-L152 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L148-L152))

```java
// Elasticsearch.java L148-L152
            // DO NOT MOVE THIS
            // Logging must remain the last step of phase 1. Anything init steps needing logging should be in phase 2.
            LogConfigurator.setClusterName(ClusterName.CLUSTER_NAME_SETTING.get(args.nodeSettings()).value());
            LogConfigurator.setNodeName(Node.NODE_NAME_SETTING.get(args.nodeSettings()));
            LogConfigurator.configure(nodeEnv, args.quiet() == false);
```

> Logging must remain the last step of phase 1. Anything init steps needing logging should be in phase 2.

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L465-L469 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L465-L469))

```java
// Elasticsearch.java L465-L469
        // DO NOT MOVE THIS
        // Signaling readiness to accept requests must remain the last step of initialization. Note that it is extremely
        // important closing the err stream to the CLI when daemonizing is the last statement since that is the only
        // way to pass errors to the CLI
        bootstrap.sendCliMarker(BootstrapInfo.SERVER_READY_MARKER);
```

> Signaling readiness to accept requests must remain the last step of initialization. Note that it is extremely important closing the err stream to the CLI when daemonizing is the last statement since that is the only way to pass errors to the CLI

```text
 둘째 주석이 두 문장인 이유

 sendCliMarker(L469) 가 초기화의 마지막이고
 closeStreams(L471) 가 문장으로서 마지막이다

 그래서 daemonize 분기가 둘로 쪼개져 있다
   L461-463  콘솔 appender 제거   마커보다 앞
   L470-472  스트림 닫기          마커보다 뒤

 마커를 보낸 뒤에는 CLI 에 오류를 전할 방법이 없다는 것이
 주석이 말하는 이유다
```

## entitlement 앞에 있어야 하는 것들

`EntitlementBootstrap.bootstrap`(L277)이 2단계의 끝이다. 그 앞에 와야 하는 것을 주석이 하나씩 적어 두었다.

```text
 주석이 "before entitlements" 라고 직접 말하는 것

 L196  "initialize probes before entitlements are installed"
         initializeProbes()                L197
 L205  "Log ifconfig output before entitlements are installed"
         IfConfig.logIfNecessary()         L206
 L211  "ReleaseVersions does nontrivial static initialization ...
         load it now (before entitlements) to be sure"
 L214  "ReferenceDocs class does nontrivial static initialization ...
         (before entitlements)"
 L217  "The following classes use MethodHandles.lookup during
         initialization, load them now (before entitlements)"
 L225  "... load it now (before entitlements) to be sure"
         ensureInitialized(...)            L208-228
 L230  "load the plugin Java modules and layers now for use in entitlements"
         loadModulesBundles / loadPluginsBundles   L232-233

 앞의 넷은 "정책이 걸리기 전에 해 두자"이고
 마지막 하나는 데이터 의존이다 - 플러그인 레이어가 정책의 입력이다
```

```text
 주석은 없지만 코드가 증명하는 것

 spawnNativeControllers(L186)는 프로세스를 띄운다
 그런데 entitlementSelfTest(L296)가 하는 일이
 "ProcessBuilder.start 가 막혔는지" 확인하는 것이다

 즉 entitlement 설치 후에는 프로세스를 못 띄운다
 그래서 네이티브 컨트롤러는 그 앞이어야 한다
 (주석은 없다. 두 코드를 나란히 놓고 내가 판단한 것이다)
```

## 보안 초기화 앞

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L181-L184 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L181-L184))

```java
// Elasticsearch.java L181-L184
        // install the default uncaught exception handler; must be done before security is
        // initialized as we do not want to grant the runtime permission
        // setDefaultUncaughtExceptionHandler
        Thread.setDefaultUncaughtExceptionHandler(new ElasticsearchUncaughtExceptionHandler());
```

> install the default uncaught exception handler; must be done before security is initialized as we do not want to grant the runtime permission setDefaultUncaughtExceptionHandler

이 주석은 이유까지 말한다 — 그 권한을 주고 싶지 않아서다.

## 비밀 설정

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L452-L453 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L452-L453))

```java
// Elasticsearch.java L452-L453
        // any secure settings must be read during node construction
        IOUtils.close(bootstrap.secureSettings());
```

> any secure settings must be read during node construction

```text
 그래서 순서가 이렇다

 L440  new Node(...)     구성 중에 keystore 를 다 읽는다
 L453  IOUtils.close(secureSettings)
 L455  INSTANCE.start()

 읽는 시점 자체는 더 앞이다
 ServerArgs 가 1단계에서 이미 스트림에서 읽어 둔다 (ServerArgs L68)
 2단계의 args.secrets() 는 재읽기가 아니라 그것을 꺼내는 것이다
```

## stdin 을 닫지 않는다

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L139-L141 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L139-L141))

```java
// Elasticsearch.java L139-L141
            // note that reading server args does *not* close System.in, as it will be read from later for shutdown notification
            var in = new InputStreamStreamInput(System.in);
            args = new ServerArgs(in);
```

> note that reading server args does *not* close System.in, as it will be read from later for shutdown notification

```text
 나중이 어디인가

 L473  startCliMonitorThread(System.in)

 그 스레드가 stdin 에서 1바이트를 읽고 (L573)
   SERVER_SHUTDOWN_MARKER 면 exit(0)
   그 외거나 EOF 면 exit(1)

 즉 부모 CLI 가 죽으면 노드도 죽는다
 데몬 모드에서는 이 스레드를 안 띄운다
```

## Node.start 안의 순서

`BootstrapChecks` 가 어디에 놓이는지는 `Node` 의 javadoc 이 계약으로 못박는다.

```text
 Node L664-668
   "Hook for validating the node after network services are started
    but before the cluster service is started and before the network
    service starts accepting incoming network requests."

 실제 순서
   transportService.start()                   L319
   gatewayMetaState.start()                   L328
   validateNodeBeforeAcceptingRequests        L358   <- BootstrapChecks
   coordinator.start()                        L369
   clusterService.start()                     L370
   transportService.acceptIncomingRequests()  L373

 앞에 transport 가 있어야 하는 이유는 boundAddress 를 넘기기 때문이고
 gatewayMetaState 가 있어야 하는 이유는 주석이 적어 두었다 (Node L354-355)
   플러그인이 복구된 상태를 근거로 조건을 강제할 수 있게 하려고

 뒤에 acceptIncomingRequests 가 와야 하는 이유는
 검사에 실패한 노드가 이미 요청을 받고 있으면 안 되기 때문이다
```

## 셧다운 훅 등록 시점

```text
 훅 등록은 2단계다 (L199)

 그래서 실패 시점에 따라 다르다
   1단계 실패 (L157)          훅이 없다. 그냥 죽는다
   2단계 L199 이후 실패       훅은 돌지만 INSTANCE 가 null 이라 즉시 return
   3단계 L450 이후 실패       INSTANCE 가 있으므로 노드를 닫는다

 shutdown 의 null 체크(L694-696)와 그 주석 "never got far enough" 가
 이 사정을 가리킨다
```

## 결과가 쓰이는 곳

```text
 단계 경계
      --> 어떤 작업을 어디에 둘지의 기준이다
      --> 로깅이 필요하면 2단계, entitlement 에 막히면 2단계 앞

 Bootstrap 의 SetOnce 셋
      --> secureSettings / environment / pluginsLoader
      --> 2단계가 쓰고 3단계가 읽는다. 순서 위반이 런타임에 걸린다

 순서를 어겼을 때
      --> 로깅 전 로그는 유실되고
      --> entitlement 후 네이티브 작업은 막히고
      --> 마커 뒤 오류는 CLI 에 안 간다
```

## 다루지 않는 것

`EntitlementBootstrap` 이 정책을 설치하는 방식과 `NotEntitledException`, `ensureInitialized` 가 미리 로드하는 클래스 아홉 개의 개별 사정, `Node.start()` 의 나머지 서비스 시작 순서와 그 주석들, `Node.close()` 의 종료 순서(`IndicesService` 를 마지막에 멈추는 이유 등), `BootstrapChecks` 의 개별 검사와 `es.enforce.bootstrap.checks` 프로퍼티, `Spawner` 의 네이티브 컨트롤러 관리는 같은 뼈대의 곁가지라 요약만 했다.
