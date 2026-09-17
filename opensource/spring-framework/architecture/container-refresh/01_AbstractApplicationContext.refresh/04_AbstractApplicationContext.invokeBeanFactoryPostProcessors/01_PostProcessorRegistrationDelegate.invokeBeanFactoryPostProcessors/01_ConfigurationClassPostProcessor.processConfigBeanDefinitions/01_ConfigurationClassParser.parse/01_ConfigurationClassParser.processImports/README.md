# ConfigurationClassParser.processImports

상위: [ConfigurationClassParser.parse](../README.md)

`@Import`에 적힌 클래스를 종류별로 처리한다. `@EnableXxx` 애노테이션이 동작하는 원리가 여기에 있다. `@EnableXxx`는 대부분 `@Import(XxxSelector.class)`나 `@Import(XxxRegistrar.class)`를 품은 메타 애노테이션이다.

## 실제 코드

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassParser.java` L581-L652 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassParser.java#L581-L652))

```java
// ConfigurationClassParser.java L581-L652
private void processImports(ConfigurationClass configClass, SourceClass currentSourceClass,
        Collection<SourceClass> importCandidates, Predicate<String> filter, boolean checkForCircularImports) {

    if (importCandidates.isEmpty()) {
        return;
    }

    if (checkForCircularImports && isChainedImportOnStack(configClass)) {
        this.problemReporter.error(new CircularImportProblem(configClass, this.importStack));
    }
    else {
        this.importStack.push(configClass);
        try {
            for (SourceClass candidate : importCandidates) {
                if (candidate.isAssignable(ImportSelector.class)) {
                    // Candidate class is an ImportSelector -> delegate to it to determine imports
                    Class<?> candidateClass = candidate.loadClass();
                    ImportSelector selector = ParserStrategyUtils.instantiateClass(candidateClass, ImportSelector.class,
                            this.environment, this.resourceLoader, this.registry);
                    Predicate<String> selectorFilter = selector.getExclusionFilter();
                    if (selectorFilter != null) {
                        filter = filter.or(selectorFilter);
                    }
                    if (selector instanceof DeferredImportSelector deferredImportSelector) {
                        this.deferredImportSelectorHandler.handle(configClass, deferredImportSelector);
                    }
                    else {
                        String[] importClassNames = selector.selectImports(currentSourceClass.getMetadata());
                        Collection<SourceClass> importSourceClasses = asSourceClasses(importClassNames, filter);
                        processImports(configClass, currentSourceClass, importSourceClasses, filter, false);
                    }
                }
                else if (candidate.isAssignable(BeanRegistrar.class)) {
                    Class<?> candidateClass = candidate.loadClass();
                    BeanRegistrar registrar = (BeanRegistrar) BeanUtils.instantiateClass(candidateClass);
                    AnnotationMetadata metadata = currentSourceClass.getMetadata();
                    if (registrar instanceof ImportAware importAware) {
                        importAware.setImportMetadata(metadata);
                    }
                    configClass.addBeanRegistrar(metadata.getClassName(), registrar);
                }
                else if (candidate.isAssignable(ImportBeanDefinitionRegistrar.class)) {
                    // Candidate class is an ImportBeanDefinitionRegistrar ->
                    // delegate to it to register additional bean definitions
                    Class<?> candidateClass = candidate.loadClass();
                    ImportBeanDefinitionRegistrar registrar =
                            ParserStrategyUtils.instantiateClass(candidateClass, ImportBeanDefinitionRegistrar.class,
                                    this.environment, this.resourceLoader, this.registry);
                    configClass.addImportBeanDefinitionRegistrar(registrar, currentSourceClass.getMetadata());
                }
                else {
                    // Candidate class not an ImportSelector or ImportBeanDefinitionRegistrar ->
                    // process it as an @Configuration class
                    this.importStack.registerImport(
                            currentSourceClass.getMetadata(), candidate.getMetadata().getClassName());
                    processConfigurationClass(candidate.asConfigClass(configClass), filter);
                }
            }
        }
        catch (BeanDefinitionStoreException ex) {
            throw ex;
        }
        catch (Throwable ex) {
            throw new BeanDefinitionStoreException(
                    "Failed to process import candidates for configuration class [" +
                    configClass.getMetadata().getClassName() + "]: " + ex.getMessage(), ex);
        }
        finally {
            this.importStack.pop();
        }
    }
}
```

## 동작 흐름

```text
 processImports(configClass, currentSourceClass, importCandidates, filter, checkForCircularImports)
 |
 +-- 후보 없음 --> return
 +-- import 체인에 자기 자신이 있음 --> CircularImportProblem 오류
 |
 +-- importStack.push(configClass)
 |   for candidate in importCandidates
 |     |
 |     +-- ImportSelector 구현                                       L595-L612
 |     |     인스턴스 생성 (Aware 콜백 포함)
 |     |     selector 의 제외 필터를 filter 에 합침
 |     |     DeferredImportSelector --> 나중 처리 대기열로   (parse 끝의 process)
 |     |     그 밖 --> selectImports(메타데이터) 가 돌려준 클래스 이름들로 processImports 재귀
 |     |
 |     +-- BeanRegistrar 구현                                        L613-L621
 |     |     인스턴스 생성, ImportAware 면 메타데이터 주입 --> 모델에 기록
 |     |
 |     +-- ImportBeanDefinitionRegistrar 구현                        L622-L630
 |     |     인스턴스 생성 --> 모델에 (registrar, import 한 클래스 메타데이터) 기록
 |     |     등록 자체는 reader.loadBeanDefinitions 에서
 |     |
 |     +-- 그 밖 (일반 클래스)                                        L631-L637
 |           importStack 에 "누가 누구를 import 했나" 기록
 |           processConfigurationClass(candidate, importedBy = configClass)   설정 클래스로 재귀
 |
 +-- finally importStack.pop()
```

`@EnableScheduling`을 예로 들면 다음과 같이 흐른다.

```text
 @EnableScheduling
   = @Import(SchedulingConfiguration.class)          일반 클래스 가지
 --> processConfigurationClass(SchedulingConfiguration)
 --> 그 안의 @Bean ScheduledAnnotationBeanPostProcessor 가 모델에 추가
 --> reader 가 빈 정의로 등록
 --> registerBeanPostProcessors 에서 처리기로 등록
 --> @Scheduled 메서드가 스케줄됨
```

## 결과가 쓰이는 곳

```text
 importStack (ImportRegistry)
      --> processConfigBeanDefinitions L494 싱글톤 등록
      --> ImportAware 빈이 "나를 import 한 클래스"의 애노테이션 속성을 읽음
          예: @EnableAsync --> AsyncConfigurationSelector --> ProxyAsyncConfiguration
              이 설정 클래스(AbstractAsyncConfiguration implements ImportAware)가
              setImportMetadata 로 @EnableAsync 의 속성을 읽는다

 모델에 기록된 registrar
      --> ConfigurationClassBeanDefinitionReader.loadBeanDefinitionsFromImportBeanDefinitionRegistrars
          예: @EnableAspectJAutoProxy --> AspectJAutoProxyRegistrar
              --> AnnotationAwareAspectJAutoProxyCreator 정의 등록 (AOP 프록시 생성기)

 대기열의 DeferredImportSelector
      --> 모든 사용자 설정 파싱 후 처리 --> @ConditionalOnMissingBean 류가 사용자 빈을 볼 수 있다
```
