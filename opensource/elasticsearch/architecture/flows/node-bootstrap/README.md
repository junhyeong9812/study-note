# 노드 기동

`bin/elasticsearch` 가 JVM 을 띄운 뒤 **노드가 요청을 받을 준비가 되기까지**다. 분기가 거의 없고 **순서가 전부**인 흐름이라, 소스에 `DO NOT MOVE THIS` 가 두 번 대문자로 박혀 있다. 폴더 하나가 메서드 하나이고, [spi](spi/README.md)에 순서 제약 표가 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 [01] main                                          L95
      +-- [02] initPhase1()                          L97
      +-- [03] initPhase2(bootstrap)                 L101
      +-- [04] initPhase3(bootstrap)                 L102
      +-- catch (NodeValidationException)            L103  종료 코드 78
      +-- catch (Throwable)                          L105  종료 코드 1
            둘 다 System.exit 으로 끝나므로 셧다운 훅이 돈다

 [02] initPhase1   로깅을 켜는 것이 마지막이다        L128
 [03] initPhase2   entitlement 를 설치하는 것이 마지막이다  L169
 [04] initPhase3   노드를 만들고 시작하고 준비 신호를 보낸다  L437
```

```text
 단계 경계가 무엇으로 정해지는가

 소스 javadoc 이 직접 말한다

 1단계 (L124-126)
   "As little as possible should be done in this phase because
    initializing logging is the last step."

 2단계 (L167)
   "Phase 2 consists of everything that must occur up to and
    including entitlement initialization."

 3단계 (L422-423)
   "Phase 3 consists of everything after entitlements are initialized.
    Up until now, the system has been single threaded. This phase can
    spawn threads, write to the log, and is subject to the entitlement policy."

 즉 경계를 만드는 것은 둘이다
   로깅 설정  (1단계 끝)
   entitlement 설치 (2단계 끝)
```

```text
 3단계가 끝나면 만족해야 하는 것 넷 (javadoc L425-431)

   노드 컴포넌트가 만들어지고 시작됐다
   정리가 끝났다 (예: 비밀 설정이 닫혔다)
   메인 스레드 외에 최소 하나가 살아 있고 메인이 끝난 뒤에도 산다
   부모 CLI 프로세스에 준비됐다고 알렸다

 세 번째가 keepAliveThread 다 (L677-683, L688)
 메인 스레드가 return 해도 JVM 이 안 죽는 이유다
```

```text
 BootstrapChecks 는 정의와 실행이 떨어져 있다

 정의  initPhase3 L440-449
         new Node(...) { validateNodeBeforeAcceptingRequests 를 오버라이드 }
         그 안에서 BootstrapChecks.check 를 부른다 (L447)

 실행  node.start() 안이다 (Node L358-362)
         즉 L455 INSTANCE.start() 를 거쳐야 돈다

 Node 의 javadoc 이 그 자리를 계약으로 못박는다 (Node L664-668)
   "Hook for validating the node after network services are started
    but before the cluster service is started and before the network
    service starts accepting incoming network requests."

 실제 순서 (Node.start 안)
   transportService.start()        L319
   gatewayMetaState.start()        L328   디스크 메타데이터를 읽는다
   BootstrapChecks.check           L358   그 메타데이터를 검사에 넘긴다
   coordinator.start()             L369
   clusterService.start()          L370
   transportService.acceptIncomingRequests()  L373
```

```text
 이 흐름에도 콜백 경계가 있다

 Node.start 안                    L391-417
   마스터가 아직 없으면 ClusterStateObserver 리스너를 걸고
   latch.await() 로 막힌다
   기동 중 셧다운이 시작되면 거기서 early return 한다 (L423-427)

 waitForNodeReady                 L552-554
   readiness 소켓이 바인드될 때까지 리스너를 걸고 await 한다

 윈도우 콘솔 핸들러               L511-518
   CTRL_CLOSE_EVENT 가 오면 다른 스레드에서 shutdown() 을 부른다

 즉 "전 구간 단일 스레드" 는 3단계 시작 전까지의 이야기다
```

```text
 shutdown 으로 들어오는 길이 둘이다

 L199  JVM 셧다운 훅 (elasticsearch-shutdown)
         System.exit 이 불리면 돈다
           main 의 catch 두 개                L104, L106
           CLI 모니터 스레드의 exit            L578, L581
           OS 시그널
 L514  윈도우 콘솔 CTRL_CLOSE_EVENT 핸들러
         훅이 아니라 직접 부른다. 다른 스레드다

 안 도는 경우도 있다
   1단계 실패 (L157)   훅 등록이 2단계(L199)라 아직 없다
   스레드 안 Error     ElasticsearchUncaughtExceptionHandler 가
                       halt() 를 써서 훅을 일부러 건너뛴다

 훅이 하나 더 있다
   initPidFile 의 pidfile-cleanup (L596-602). shutdown() 과 무관하게 병렬로 돈다
```

## 어디에서 쓰이는가

```text
 [구조: 노드 역할] 이 과정에서 역할이 정해지고 클러스터 상태에 실린다
 [구조: 디스크 배치] node.lock 을 잡는 것도 노드 구성 중이다
 [REST 디스패치] 핸들러 등록은 노드 구성 중에 끝난다
```

노드가 뜬 뒤의 요청 처리는 [REST 디스패치](../rest-dispatch/README.md)에 있다.

## 단계

1. [main](01_Elasticsearch.main/README.md)이 세 단계를 부르고 실패를 받는다.
2. [initPhase1](02_Elasticsearch.initPhase1/README.md)이 인자를 읽고 로깅을 켠다.
3. [initPhase2](03_Elasticsearch.initPhase2/README.md)가 entitlement 설치까지 준비한다.
4. [initPhase3](04_Elasticsearch.initPhase3/README.md)가 노드를 만들고 시작한다.
5. [shutdown](05_Elasticsearch.shutdown/README.md)이 종료를 처리한다.

## 결과가 쓰이는 곳

```text
 Bootstrap 객체
      --> 1단계가 만들고 2단계가 채운다 (SetOnce 셋)
      --> 3단계가 읽는다. 순서를 어기면 런타임에 걸린다

 keepAliveThread
      --> 메인 스레드가 끝나도 JVM 을 붙잡는다
      --> 셧다운 훅의 countDown 이 풀어 준다

 SERVER_READY_MARKER
      --> 부모 CLI 프로세스가 이것을 보고 성공을 판정한다
      --> 이 뒤에 나는 오류는 CLI 에 전달할 방법이 없다

 종료 코드
      --> NodeValidationException 이면 78 (ExitCodes.CONFIG)
      --> 그 외는 1
```

## 다루지 않는 것

`NodeConstruction.prepareConstruction` 의 노드 조립(서비스 수십 개와 의존 관계), `EntitlementBootstrap.bootstrap` 의 정책 설치, `BootstrapChecks` 의 개별 검사 항목과 강제 조건, `Node.start()` 가 서비스를 시작하는 전체 순서, `Node.close()` 의 종료 순서, 플러그인 로딩(`PluginsLoader`)과 모듈 레이어, 네이티브 접근(`NativeAccess`)과 시스템 콜 필터는 같은 뼈대의 곁가지라 요약만 했다. 순서 제약 자체는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 main](01_Elasticsearch.main/README.md)
- [02 initPhase1](02_Elasticsearch.initPhase1/README.md)
- [03 initPhase2](03_Elasticsearch.initPhase2/README.md)
- [04 initPhase3](04_Elasticsearch.initPhase3/README.md)
- [05 shutdown](05_Elasticsearch.shutdown/README.md)
- [spi](spi/README.md) — 순서 제약 표
