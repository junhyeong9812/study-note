# Elasticsearch.initPhase2

상위: [노드 기동](../README.md)

**entitlement 를 설치하기까지** 해야 하는 전부다. 130줄이 전부 직선이고 조건 분기가 **하나도 없다** — 대신 각 호출이 "entitlement 앞이어야 한다"는 이유로 그 자리에 있다.

## 위치

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L169-L299 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L169-L299))

## 실제 코드

환경을 만들고 예외 핸들러를 건다.

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L171-L189 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L171-L189))

```java
// Elasticsearch.java L171-L189
        logSystemInfo();

        final ServerArgs args = bootstrap.args();
        final SecureSettings secrets = args.secrets();
        bootstrap.setSecureSettings(secrets);
        Environment nodeEnv = createEnvironment(args.configDir(), args.nodeSettings(), secrets);
        bootstrap.setEnvironment(nodeEnv);

        initPidFile(args.pidFile());

        // install the default uncaught exception handler; must be done before security is
        // initialized as we do not want to grant the runtime permission
        // setDefaultUncaughtExceptionHandler
        Thread.setDefaultUncaughtExceptionHandler(new ElasticsearchUncaughtExceptionHandler());

        bootstrap.spawner().spawnNativeControllers(nodeEnv);

        nodeEnv.validateNativesConfig(); // temporary directories are important for JNA
        initializeNatives(
```

entitlement 앞에 해 둘 것들.

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L196-L208 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L196-L208))

```java
// Elasticsearch.java L196-L208
        // initialize probes before entitlements are installed
        initializeProbes();

        Runtime.getRuntime().addShutdownHook(new Thread(Elasticsearch::shutdown, "elasticsearch-shutdown"));

        // look for jar hell
        final Logger logger = LogManager.getLogger(JarHell.class);
        JarHell.checkJarHell(logger::debug);

        // Log ifconfig output before entitlements are installed
        IfConfig.logIfNecessary();

        ensureInitialized(
```

정책을 만들어 설치하고 검증한다.

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L262-L298 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L262-L298))

```java
// Elasticsearch.java L262-L298
        var pluginPolicyPatches = collectPluginPolicyPatches(modulesBundles, pluginsBundles, logger);
        var pluginPolicies = PolicyUtils.createPluginPolicies(pluginData, pluginPolicyPatches, Build.current().version());
        var serverPolicyPatch = PolicyUtils.parseEncodedPolicyIfExists(
            System.getProperty(SERVER_POLICY_PATCH_NAME),
            Build.current().version(),
            false,
            "server",
            PolicyManager.SERVER_LAYER_MODULES.stream().map(Module::getName).collect(Collectors.toUnmodifiableSet())
        );

        pluginsLoader = PluginsLoader.createPluginsLoader(modulesBundles, pluginsBundles, findPluginsWithNativeAccess(pluginPolicies));

        var scopeResolver = ScopeResolver.create(pluginsLoader.pluginLayers(), APM_AGENT_PACKAGE_NAME);
        Map<String, Collection<Path>> pluginSourcePaths = Stream.concat(modulesBundles.stream(), pluginsBundles.stream())
            .collect(Collectors.toUnmodifiableMap(bundle -> bundle.pluginDescriptor().getName(), bundle -> List.of(bundle.getDir())));
        EntitlementBootstrap.bootstrap(
            serverPolicyPatch,
            pluginPolicies,
            PolicyUtils.stablePluginSyntheticModuleNames(pluginData),
            scopeResolver::resolveClassToScope,
            nodeEnv.settings()::getValues,
            nodeEnv.dataDirs(),
            nodeEnv.sharedDataDir(),
            nodeEnv.repoDirs(),
            nodeEnv.configDir(),
            nodeEnv.libDir(),
            nodeEnv.modulesDir(),
            nodeEnv.pluginsDir(),
            pluginSourcePaths,
            nodeEnv.logsDir(),
            nodeEnv.tmpDir(),
            args.pidFile(),
            Set.of(EntitlementSelfTester.class.getPackage())
        );
        entitlementSelfTest();

        bootstrap.setPluginsLoader(pluginsLoader);
```

## 동작 흐름

```text
 L171  logSystemInfo()                주석 L170: "always start by dumping ..."
 L176  createEnvironment(...)         비밀 설정을 포함한 환경
 L179  initPidFile(...)               pidfile 정리 훅을 하나 더 건다 (L596-602)
 L184  setDefaultUncaughtExceptionHandler(...)
 L186  spawnNativeControllers(...)    프로세스를 띄운다
 L188  validateNativesConfig()
 L189  initializeNatives(...)
 L197  initializeProbes()
 L199  addShutdownHook(Elasticsearch::shutdown)
 L203  JarHell.checkJarHell(...)
 L206  IfConfig.logIfNecessary()
 L208  ensureInitialized(... 클래스 아홉 개 ...)
 L232  loadModulesBundles / loadPluginsBundles
 L262  collectPluginPolicyPatches
 L263  createPluginPolicies
 L264  서버 정책 패치를 읽는다
 L272  createPluginsLoader(..., findPluginsWithNativeAccess(...))
 L274  ScopeResolver.create(...)
 L277  EntitlementBootstrap.bootstrap(...)      <- 2단계의 끝
 L296  entitlementSelfTest()
 L298  bootstrap.setPluginsLoader(...)
```

```text
 조건 분기가 없다

 이 메서드 본문에 if 도 삼항도 early return 도 catch 도 없다
 130줄이 전부 순차 호출이다

 그래서 읽을 것은 "무엇을 하는가" 가 아니라 "왜 이 순서인가" 다
 주석이 그 답을 여러 군데 적어 두었다 (정리는 spi 에 있다)
```

```text
 initializeNatives 안에 기동 실패 경로가 있다

 L490  루트로 실행 중이면
         throw new RuntimeException("can not run elasticsearch as root")
 L494  시스템 콜 필터를 설치한다 (8.0.0 부터 항상 true)
 L504  mlockAll 이면 메모리를 잠근다
 L509  윈도우면 콘솔 컨트롤 핸들러를 건다
         CTRL_CLOSE_EVENT 가 오면 shutdown() 을 부른다  <- 두 번째 진입점
 L522  리눅스면 coredump 필터를 쓴다

 루트 검사는 여기서 죽는 유일한 검사다
 나머지는 설정에 따라 건너뛴다
```

```text
 entitlementSelfTest 는 성공이 예외다

 L372  ProcessBuilder::start 를 시도한다
 L373  리플렉션으로도 시도한다

 각각에서 예외가 안 나면
   throw new IllegalStateException("... incorrectly permitted")

 예외의 원인 사슬에 NotEntitledException 이 있으면 통과다
 아니면 "Failed entitlement protection self-test"

 즉 "막히는 것"을 확인하는 검사라 정상 경로가 예외다
 주석이 위치 제약도 적어 두었다 (L370)
   "note this must be outside the entitlements lib"
```

```text
 셧다운 훅이 여기서 둘 등록된다

 L179 initPidFile 안의 pidfile-cleanup (L596-602)
 L199 elasticsearch-shutdown

 JVM 훅은 병렬로 돌므로 둘 사이에 순서가 없다
 앞엣것은 pidfile 을 지우기만 하고 shutdown() 과 무관하다

 그리고 L199 이전에 실패하면 훅이 아예 없다
```

## 결과가 쓰이는 곳

```text
 Bootstrap 에 채워지는 셋
      --> setSecureSettings(L175), setEnvironment(L177), setPluginsLoader(L298)
      --> SetOnce 라서 3단계가 읽을 때 채워져 있어야 한다

 entitlement 정책
      --> 이 뒤로는 파일 쓰기, 프로세스 생성, 네이티브 로딩이 정책을 탄다
      --> 3단계가 정책 아래에서 도는 이유다

 네이티브 컨트롤러
      --> 플러그인이 띄운 별도 프로세스다
      --> 펌프 스레드가 그 출력을 읽는다

 예외 핸들러
      --> 이후 모든 스레드의 미처리 예외를 받는다
      --> Error 면 halt 라서 셧다운 훅을 건너뛴다
```

## 다루지 않는 것

`EntitlementBootstrap.bootstrap` 의 정책 설치, `PolicyUtils` 의 정책 생성과 패치 병합, `PluginsLoader` 의 번들 로딩과 모듈 레이어, `initializeNatives` 가 부르는 `NativeAccess` 구현, `JarHell` 검사, `ensureInitialized` 가 미리 로드하는 클래스들의 개별 사정, `Spawner` 의 컨트롤러 관리와 펌프 스레드는 같은 뼈대의 곁가지라 요약만 했다. 순서 제약은 [spi](../spi/README.md)에 모았다.
