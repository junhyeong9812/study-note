# GenericApplicationContext.refreshForAotProcessing

상위: [Spring AOT 처리](../README.md)

`refresh()`의 앞부분만 골라 실행하는 메서드다. 빈 정의를 확정하는 데까지만 가고, 싱글톤은 만들지 않는다.

## 실제 코드

`spring-context` / `org.springframework.context.support` / `GenericApplicationContext.java` L412-L424 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/support/GenericApplicationContext.java#L412-L424))

```java
// GenericApplicationContext.java L412-L424
public void refreshForAotProcessing(RuntimeHints runtimeHints) {
    if (logger.isDebugEnabled()) {
        logger.debug("Preparing bean factory for AOT processing");
    }
    prepareRefresh();
    obtainFreshBeanFactory();
    prepareBeanFactory(this.beanFactory);
    postProcessBeanFactory(this.beanFactory);
    invokeBeanFactoryPostProcessors(this.beanFactory);
    this.beanFactory.freezeConfiguration();
    PostProcessorRegistrationDelegate.invokeMergedBeanDefinitionPostProcessors(this.beanFactory);
    preDetermineBeanTypes(runtimeHints);
}
```

## 동작 흐름

```text
 refreshForAotProcessing(runtimeHints)
 |
 | L416 prepareRefresh()                     활성 표시, 필수 프로퍼티 검증
 | L417 obtainFreshBeanFactory()             빈 팩토리 확보
 | L418 prepareBeanFactory(beanFactory)      기본 후처리기와 Aware 등록
 | L419 postProcessBeanFactory(beanFactory)  하위 클래스 훅
 | L420 invokeBeanFactoryPostProcessors(...) 설정 클래스 파싱, 스캔, 빈 정의 생성
 |
 | L421 beanFactory.freezeConfiguration()
 |        더 이상 빈 정의가 바뀌지 않는다고 못박는다
 |
 | L422 invokeMergedBeanDefinitionPostProcessors(...)
 |        주입 메타데이터 같은 병합 정의 후처리를 미리 돌린다
 |
 +-- L423 preDetermineBeanTypes(runtimeHints)
        빈 타입을 미리 확정해 프록시가 필요한지 판단한다
        필요하면 ClassHintUtils.registerProxyIfNecessary 로 힌트를 남긴다
```

```text
 refresh 와 무엇이 다른가

 refresh()                      refreshForAotProcessing()
 01 prepareRefresh              같다
 02 obtainFreshBeanFactory      같다
 03 prepareBeanFactory          같다
 04 invokeBeanFactoryPostProcessors  같다
 05 registerBeanPostProcessors  없음
 06~08 메시지 소스, 멀티캐스터, 리스너  없음
 09 finishBeanFactoryInitialization  없음 (싱글톤을 만들지 않는다)
 10 finishRefresh               없음

 대신 freezeConfiguration 과 타입 사전 확정이 붙는다
```

## 결과가 쓰이는 곳

```text
 확정된 빈 정의
      --> 이것이 코드 생성의 입력이다. 정의 하나가 등록 메서드 하나가 된다
      --> @Configuration 파싱 결과가 여기 다 들어 있다

 freezeConfiguration
      --> 이후 정의가 바뀌지 않으니 코드로 고정해도 안전하다는 근거다
      --> 런타임에 정의를 바꾸는 코드가 AOT 에서 동작하지 않는 이유이기도 하다

 미리 확정한 빈 타입
      --> 프록시가 필요한 빈을 빌드 시점에 알 수 있다
      --> 그 프록시 클래스가 CGLIB 핸들러에 걸려 파일로 저장된다

 싱글톤을 만들지 않는다는 점
      --> 애플리케이션 빈의 생성자가 빌드 시점에 실행되지 않는다
      --> DB 연결 같은 부작용이 빌드 중에 일어나지 않는다
      --> 다만 빈 팩토리 후처리기와 AOT 처리기 구현 빈은 예외다
          이 단계에서 실제로 만들어지므로 그 의존성까지 함께 생성된다
```

런타임에 같은 단계를 수행하는 흐름은 [컨테이너 기동](../../container-refresh/01_AbstractApplicationContext.refresh/README.md)에 있다.
