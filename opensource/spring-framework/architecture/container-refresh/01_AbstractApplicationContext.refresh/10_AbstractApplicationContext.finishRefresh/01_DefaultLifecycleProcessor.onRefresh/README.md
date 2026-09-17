# DefaultLifecycleProcessor.onRefresh

상위: [AbstractApplicationContext.finishRefresh](../README.md)

`autoStartup`이 켜진 [SmartLifecycle](../../../spi/SmartLifecycle/README.md) 빈을 phase 값이 작은 그룹부터 시작한다. 같은 그룹 안에서는 의존하는 빈을 먼저 시작한다. 하나라도 시작에 실패하면 이미 시작한 빈을 멈추고 예외를 던진다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `DefaultLifecycleProcessor.java` L295-L315 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/DefaultLifecycleProcessor.java#L295-L315))

```java
// DefaultLifecycleProcessor.java L295-L315
public void onRefresh() {
    if (checkpointOnRefresh) {
        checkpointOnRefresh = false;
        new CracDelegate().checkpointRestore();
    }
    if (exitOnRefresh) {
        Runtime.getRuntime().halt(0);
    }

    this.stoppedBeans = null;
    try {
        startBeans(true);
    }
    catch (ApplicationContextException ex) {
        // Some bean failed to auto-start within context refresh:
        // stop already started beans on context refresh failure.
        stopBeans(false);
        throw ex;
    }
    this.running = true;
}
```

`spring-context` / `org.springframework.context.support` / `DefaultLifecycleProcessor.java` L365-L381 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/DefaultLifecycleProcessor.java#L365-L381))

```java
// DefaultLifecycleProcessor.java L365-L381
private void startBeans(boolean autoStartupOnly) {
    Map<String, Lifecycle> lifecycleBeans = getLifecycleBeans();
    Map<Integer, LifecycleGroup> phases = new TreeMap<>();

    lifecycleBeans.forEach((beanName, bean) -> {
        if (!autoStartupOnly || isAutoStartupCandidate(beanName, bean)) {
            int startupPhase = getPhase(bean);
            phases.computeIfAbsent(
                    startupPhase, phase -> new LifecycleGroup(phase, lifecycleBeans, autoStartupOnly, false))
                        .add(beanName, bean);
        }
    });

    if (!phases.isEmpty()) {
        phases.values().forEach(LifecycleGroup::start);
    }
}
```

`spring-context` / `org.springframework.context.support` / `DefaultLifecycleProcessor.java` L395-L413 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/DefaultLifecycleProcessor.java#L395-L413))

```java
// DefaultLifecycleProcessor.java L395-L413
private void doStart(Map<String, ? extends Lifecycle> lifecycleBeans, String beanName,
        boolean autoStartupOnly, @Nullable List<CompletableFuture<?>> futures) {

    Lifecycle bean = lifecycleBeans.remove(beanName);
    if (bean != null && bean != this) {
        String[] dependenciesForBean = getBeanFactory().getDependenciesForBean(beanName);
        for (String dependency : dependenciesForBean) {
            doStart(lifecycleBeans, dependency, autoStartupOnly, futures);
        }
        if (!bean.isRunning() && (!autoStartupOnly || toBeStarted(beanName, bean))) {
            if (futures != null) {
                futures.add(CompletableFuture.runAsync(() -> doStart(beanName, bean), getBootstrapExecutor()));
            }
            else {
                doStart(beanName, bean);
            }
        }
    }
}
```

phase 그룹 하나를 시작하는 코드다.

`spring-context` / `org.springframework.context.support` / `DefaultLifecycleProcessor.java` L603-L631 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/DefaultLifecycleProcessor.java#L603-L631))

```java
// DefaultLifecycleProcessor.java L603-L631
public void start() {
    if (this.members.isEmpty()) {
        return;
    }
    if (logger.isDebugEnabled()) {
        logger.debug("Starting beans in phase " + this.phase);
    }
    Long concurrentStartup = determineConcurrentStartup(this.phase);
    List<CompletableFuture<?>> futures = (concurrentStartup != null ? new ArrayList<>() : null);
    for (LifecycleGroupMember member : this.members) {
        doStart(this.lifecycleBeans, member.name, this.autoStartupOnly, futures);
    }
    if (concurrentStartup != null && !CollectionUtils.isEmpty(futures)) {
        try {
            CompletableFuture.allOf(futures.toArray(new CompletableFuture<?>[0]))
                    .get(concurrentStartup, TimeUnit.MILLISECONDS);
        }
        catch (Exception ex) {
            if (ex instanceof ExecutionException exEx) {
                Throwable cause = exEx.getCause();
                if (cause instanceof ApplicationContextException acEx) {
                    throw acEx;
                }
            }
            throw new ApplicationContextException("Failed to start beans in phase " + this.phase +
                    " within timeout of " + concurrentStartup + "ms", ex);
        }
    }
}
```

## 동작 흐름

```text
 onRefresh()
 |
 | L296 CRaC 체크포인트 설정이면 체크포인트/복원      (spring.context.checkpoint=onRefresh)
 | L300 exitOnRefresh 설정이면 즉시 JVM 종료          (spring.context.exit=onRefresh, L101)
 |        기동 직후 종료가 필요한 경우용 (예: JVM CDS 아카이브를 만드는 학습 실행)
 |
 +-- try  startBeans(autoStartupOnly = true)
 |     catch ApplicationContextException --> stopBeans() 후 다시 던짐
 +-- running = true

 startBeans(autoStartupOnly)
 |
 | lifecycleBeans = Lifecycle 타입 빈 전부
 | phases = TreeMap<phase, LifecycleGroup>   (키 오름차순)
 |
 +-- 각 빈
 |     autoStartup 후보인가?   SmartLifecycle 이고 isAutoStartup() == true
 |       (일반 Lifecycle 은 refresh 때 자동 시작 대상이 아님)
 |     phase = SmartLifecycle.getPhase()  (일반 Lifecycle 은 0, SmartLifecycle 기본값은 Integer.MAX_VALUE)
 |     phases[phase] 그룹에 추가
 |
 +-- 그룹마다 오름차순으로 LifecycleGroup.start()
       동시 시작 설정이 있으면 futures 준비
       멤버마다 doStart(lifecycleBeans, 이름)
         lifecycleBeans 에서 꺼냄 (중복 시작 방지)
         이 빈이 의존하는 빈부터 재귀로 doStart   (phase 와 무관하게 먼저)
         아직 실행 중이 아니고 시작 대상이면
           futures 있음 --> bootstrapExecutor 로 비동기 bean.start()
           없음        --> bean.start()
             실패 --> ApplicationContextException("Failed to start bean")
       futures 가 있으면 timeout 안에 모두 끝나기를 기다림
```

```text
 phase 예시
   -100   데이터 소스 준비 같은 선행 작업
      0   일반 Lifecycle, 기본값을 바꾼 컴포넌트
   ...
   MAX    SmartLifecycle 기본값 --> 가장 늦게 시작, 가장 먼저 정지
```

## 결과가 쓰이는 곳

```text
 running = true
      --> isRunning() --> refresh 실패 처리(refresh L635)와 close() 에서 stop 여부 판단

 phase 순서
      --> 정지(stopBeans) 는 같은 그룹 구조를 역순 TreeMap 으로 만든다 (L438)
          = 늦게 시작한 것이 먼저 멈춘다 (요청을 받는 웹 서버가 먼저 멈추고, 앞 phase 의 컴포넌트가 뒤에 멈춤)
          싱글톤 파괴 (DB 풀 close 등) 는 Lifecycle 정지가 모두 끝난 뒤

 start() 가 던진 예외
      --> onRefresh 의 catch --> stopBeans --> finishRefresh 밖으로 --> refresh 의 catch
          --> destroyBeans --> 컨텍스트 기동 실패
```
