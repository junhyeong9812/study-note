# Elasticsearch.main

상위: [노드 기동](../README.md)

열네 줄이다. 세 단계를 차례로 부르고 실패를 종료 코드로 바꾼다. **1단계만 밖에 있고** 나머지 둘이 try 안에 있는 것이 이 메서드의 전부다.

## 위치

`server` / `org.elasticsearch.bootstrap` / `Elasticsearch.java` L95-L108 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/bootstrap/Elasticsearch.java#L95-L108))

## 실제 코드

```java
// Elasticsearch.java L95-L108
    public static void main(final String[] args) {

        Bootstrap bootstrap = initPhase1();
        assert bootstrap != null;

        try {
            initPhase2(bootstrap);
            initPhase3(bootstrap);
        } catch (NodeValidationException e) {
            bootstrap.exitWithNodeValidationException(e);
        } catch (Throwable t) {
            bootstrap.exitWithUnknownException(t);
        }
    }
```

## 동작 흐름

```text
 L97   bootstrap = initPhase1()
 L98   assert bootstrap != null
 L100  try
       L101  initPhase2(bootstrap)
       L102  initPhase3(bootstrap)
 L103  catch (NodeValidationException e)
       L104  bootstrap.exitWithNodeValidationException(e)
 L105  catch (Throwable t)
       L106  bootstrap.exitWithUnknownException(t)
```

```text
 1단계가 try 밖인 이유

 initPhase1 은 자기 안에 catch (Throwable) 을 가지고 있다 (L153)
 거기서 stderr 에 직접 찍고 Bootstrap.exit(1) 한다

 로깅이 아직 안 켜졌기 때문이다
 이 메서드의 catch 는 Bootstrap 을 거치는데
 그 경로가 logger.error 와 printLogsSuggestion 을 쓴다
 (printLogsSuggestion 에는 assert basePath != null : "logging wasn't initialized" 가 있다)

 즉 1단계 실패는 이 메서드까지 올라오지 않는다
```

```text
 종료 코드가 둘이다

 NodeValidationException  ExitCodes.CONFIG = 78
 그 외 Throwable          1

 앞엣것은 BootstrapChecks 가 던지는 것이다
 설정이 잘못됐다는 뜻이라 별도 코드를 쓴다

 로그도 다르다
   NodeValidationException  메시지만 찍는다
   그 외                    스택까지 찍는다
```

```text
 여기서 exit 하면 셧다운 훅이 돈다

 exitWithNodeValidationException 도 exitWithUnknownException 도
 결국 System.exit 을 부른다

 그러면 2단계에서 등록한 훅(L199)이 실행된다

 그 시점에 INSTANCE 가 있으면 부분 기동된 노드를 닫는다
 예를 들어 node.start() 안의 BootstrapChecks 가 실패한 경우다
 없으면 shutdown 이 즉시 return 한다
```

```text
 이 catch 가 못 잡는 것

 스레드 안에서 나는 미처리 예외는 여기로 안 온다
 2단계가 설치한 ElasticsearchUncaughtExceptionHandler 가 받는다 (L184)

 그 핸들러는 Error 계열에서 halt() 를 쓴다
 주석이 이유를 적어 두었다 - 셧다운 훅이 도는 것을 막으려고
```

## 결과가 쓰이는 곳

```text
 Bootstrap 객체
      --> 1단계가 만들어 돌려주고
      --> 2단계가 채우고 3단계가 읽는다

 종료 코드
      --> 부모 CLI 프로세스가 이것으로 실패 종류를 안다
      --> 78 이면 설정 문제라고 안내한다

 정상 종료
      --> main 은 return 하지만 JVM 은 안 죽는다
      --> keepAliveThread 가 비-데몬으로 남아 있기 때문이다
```

## 다루지 않는 것

`Bootstrap` 의 종료 처리(`gracefullyExit`, `printLogsSuggestion`)와 종료 코드 정의, `ElasticsearchUncaughtExceptionHandler` 의 분류와 `halt` 사용, `NodeValidationException` 을 던지는 `BootstrapChecks` 의 판정은 같은 뼈대의 곁가지라 요약만 했다. 단계 경계의 근거는 [spi](../spi/README.md)에 있다.
