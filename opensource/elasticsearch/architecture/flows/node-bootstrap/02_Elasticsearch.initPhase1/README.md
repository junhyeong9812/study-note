# Elasticsearch.initPhase1

상위: [노드 기동](../README.md)

**CLI 인자를 읽고 로깅을 켠다.** 그게 전부여야 한다고 javadoc 이 못박는다 — 로깅 초기화가 이 단계의 마지막이라 그 앞에서 하는 일은 진단이 안 되기 때문이다.

## 위치

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L128-L162 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L128-L162))

## 실제 코드

```java
// Elasticsearch.java L128-L162
    private static Bootstrap initPhase1() {
        final PrintStream out = getStdout();
        final PrintStream err = getStderr();
        final ServerArgs args;

        try {
            initSecurityProperties();
            LogConfigurator.registerErrorListener();

            BootstrapInfo.init();

            // note that reading server args does *not* close System.in, as it will be read from later for shutdown notification
            var in = new InputStreamStreamInput(System.in);
            args = new ServerArgs(in);

            // mostly just paths are used in phase 1, so secure settings are not needed
            Environment nodeEnv = new Environment(args.nodeSettings(), args.configDir());

            BootstrapInfo.setConsole(ConsoleLoader.loadConsole(nodeEnv));

            // DO NOT MOVE THIS
            // Logging must remain the last step of phase 1. Anything init steps needing logging should be in phase 2.
            LogConfigurator.setClusterName(ClusterName.CLUSTER_NAME_SETTING.get(args.nodeSettings()).value());
            LogConfigurator.setNodeName(Node.NODE_NAME_SETTING.get(args.nodeSettings()));
            LogConfigurator.configure(nodeEnv, args.quiet() == false);
        } catch (Throwable t) {
            // any exception this early needs to be fully printed and fail startup
            t.printStackTrace(err);
            err.flush();
            Bootstrap.exit(1); // mimic JDK exit code on exception
            return null; // unreachable, to satisfy compiler
        }

        return new Bootstrap(out, err, args);
    }
```

## 동작 흐름

```text
 L134  initSecurityProperties()
 L135  LogConfigurator.registerErrorListener()
 L137  BootstrapInfo.init()
 L140  new InputStreamStreamInput(System.in)
 L141  args = new ServerArgs(in)
 L144  nodeEnv = new Environment(args.nodeSettings(), args.configDir())
 L146  BootstrapInfo.setConsole(ConsoleLoader.loadConsole(nodeEnv))
 L150  LogConfigurator.setClusterName(...)
 L151  LogConfigurator.setNodeName(...)
 L152  LogConfigurator.configure(nodeEnv, args.quiet() == false)
 L153  catch (Throwable t)
       L155  t.printStackTrace(err)
       L156  err.flush()
       L157  Bootstrap.exit(1)
       L158  return null
 L161  return new Bootstrap(out, err, args)
```

```text
 javadoc 이 이 단계를 정의한다 (L124-126)

   "Phase 1 consists of some static initialization, reading args from
    the CLI process, and finally initializing logging. As little as
    possible should be done in this phase because initializing logging
    is the last step."

 그리고 L148-149 가 대문자로 못박는다

   "DO NOT MOVE THIS
    Logging must remain the last step of phase 1. Anything init steps
    needing logging should be in phase 2."
```

```text
 예외 처리가 다른 이유

 주석은 이렇게만 말한다 (L154)
   "any exception this early needs to be fully printed and fail startup"

 왜 "fully printed" 인가는 주석이 말하지 않는다
 다만 로깅 설정이 이 단계의 마지막(L152)이므로
 그 앞에서 실패하면 로거로 찍을 수가 없다
 그래서 stderr 에 스택을 직접 쏟는 것으로 보인다

 [01] 의 catch 는 Bootstrap 을 거치는데
 그 경로가 logger.error 를 쓰므로 여기서는 쓸 수 없다
```

```text
 Environment 를 두 번 만든다

 여기 L144 와 [03] 의 L176 이다

 주석이 여기 것의 성격을 말한다 (L143)
   "mostly just paths are used in phase 1, so secure settings are not needed"

 즉 1단계 것은 경로만 쓰는 가벼운 것이고
 2단계에서 비밀 설정을 포함해 다시 만든다
```

```text
 stdin 을 닫지 않는다

 주석이 이유를 적어 두었다 (L139)
   "note that reading server args does *not* close System.in,
    as it will be read from later for shutdown notification"

 나중이란 [04] L473 의 CLI 모니터 스레드다
 그 스레드가 같은 stdin 에서 종료 신호를 읽는다

 그리고 ServerArgs 는 여기서 비밀 설정까지 읽는다
 2단계의 args.secrets() 는 재읽기가 아니라 그것을 꺼내는 것이다
```

```text
 exit(1) 이 셧다운 훅을 안 돌린다

 훅 등록은 2단계 L199 다
 여기서 죽으면 아직 등록 전이라 shutdown() 이 돌지 않는다

 그래서 이 단계의 실패는 정리할 것도 없는 실패다
```

## 결과가 쓰이는 곳

```text
 Bootstrap 객체
      --> out, err, args 를 담아 [01] 로 돌아간다
      --> 이후 단계가 여기에 environment, secureSettings, pluginsLoader 를 채운다

 로깅 설정
      --> 2단계부터 logger 를 쓸 수 있다
      --> logSystemInfo 가 2단계 첫 문장인 것도 그 덕이다

 ServerArgs
      --> nodeSettings, configDir, pidFile, daemonize, quiet, secrets
      --> 부모 CLI 가 스트림으로 넘겨준 것이다
```

## 다루지 않는 것

`ServerArgs` 의 직렬화 형식과 비밀 설정 읽기, `LogConfigurator` 의 설정 파일 해석, `ConsoleLoader` 와 콘솔 감지, `initSecurityProperties` 의 프로퍼티 재정의, `Environment` 가 경로를 해석하는 규칙은 같은 뼈대의 곁가지라 요약만 했다.
