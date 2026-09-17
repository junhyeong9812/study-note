# ConfigurationClassParser.parse

상위: [ConfigurationClassPostProcessor.processConfigBeanDefinitions](../README.md)

설정 클래스 하나를 읽어 `ConfigurationClass` 모델로 만든다. 모델에는 `@Bean` 메서드 목록, import 된 설정, `@ImportResource`, 등록기(Registrar)가 담긴다. `@ComponentScan`만은 모델에 담지 않고 **파싱 도중 바로 스캔해 정의를 등록**한다. 부모 클래스와 중첩 클래스까지 재귀로 내려간다.

## 실제 코드

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassParser.java` L168-L201 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassParser.java#L168-L201))

```java
// ConfigurationClassParser.java L168-L201
public void parse(Set<BeanDefinitionHolder> configCandidates) {
    for (BeanDefinitionHolder holder : configCandidates) {
        BeanDefinition bd = holder.getBeanDefinition();
        try {
            ConfigurationClass configClass;
            if (bd instanceof AnnotatedBeanDefinition annotatedBeanDef) {
                configClass = parse(annotatedBeanDef, holder.getBeanName());
            }
            else if (bd instanceof AbstractBeanDefinition abstractBeanDef && abstractBeanDef.hasBeanClass()) {
                configClass = parse(abstractBeanDef.getBeanClass(), holder.getBeanName());
            }
            else {
                configClass = parse(bd.getBeanClassName(), holder.getBeanName());
            }

            // Downgrade to lite (no enhancement) in case of no instance-level @Bean methods.
            if (!configClass.getMetadata().isAbstract() && !configClass.hasNonStaticBeanMethods() &&
                    ConfigurationClassUtils.CONFIGURATION_CLASS_FULL.equals(
                            bd.getAttribute(ConfigurationClassUtils.CONFIGURATION_CLASS_ATTRIBUTE))) {
                bd.setAttribute(ConfigurationClassUtils.CONFIGURATION_CLASS_ATTRIBUTE,
                        ConfigurationClassUtils.CONFIGURATION_CLASS_LITE);
            }
        }
        catch (BeanDefinitionStoreException ex) {
            throw ex;
        }
        catch (Throwable ex) {
            throw new BeanDefinitionStoreException(
                    "Failed to parse configuration class [" + bd.getBeanClassName() + "]", ex);
        }
    }

    this.deferredImportSelectorHandler.process();
}
```

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassParser.java` L248-L295 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassParser.java#L248-L295))

```java
// ConfigurationClassParser.java L248-L295
protected void processConfigurationClass(ConfigurationClass configClass, Predicate<String> filter) {
    if (this.conditionEvaluator.shouldSkip(configClass.getMetadata(), ConfigurationPhase.PARSE_CONFIGURATION)) {
        return;
    }

    ConfigurationClass existingClass = this.configurationClasses.get(configClass);
    if (existingClass != null) {
        if (configClass.isImported()) {
            if (existingClass.isImported()) {
                existingClass.mergeImportedBy(configClass);
            }
            // Otherwise ignore new imported config class; existing non-imported class overrides it.
            return;
        }
        else if (configClass.isScanned()) {
            if (existingClass.isImported()) {
                String beanName = configClass.getBeanName();
                if (StringUtils.hasLength(beanName) && this.registry.containsBeanDefinition(beanName)) {
                    this.registry.removeBeanDefinition(beanName);
                }
            }
            // An implicitly scanned bean definition should not override an explicit import.
            return;
        }
        else {
            // Explicit bean definition found, probably replacing an import.
            // Let's remove the old one and go with the new one.
            this.configurationClasses.remove(configClass);
            removeKnownSuperclass(configClass.getMetadata().getClassName(), false);
        }
    }

    // Recursively process the configuration class and its superclass hierarchy.
    SourceClass sourceClass = null;
    try {
        sourceClass = asSourceClass(configClass, filter);
        do {
            sourceClass = doProcessConfigurationClass(configClass, sourceClass, filter);
        }
        while (sourceClass != null);
    }
    catch (IOException ex) {
        throw new BeanDefinitionStoreException(
                "I/O failure while processing configuration class [" + sourceClass + "]", ex);
    }

    this.configurationClasses.put(configClass, configClass);
}
```

`spring-context` / `org.springframework.context.annotation` / `ConfigurationClassParser.java` L305-L405 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/annotation/ConfigurationClassParser.java#L305-L405))

```java
// ConfigurationClassParser.java L305-L405
protected final @Nullable SourceClass doProcessConfigurationClass(
        ConfigurationClass configClass, SourceClass sourceClass, Predicate<String> filter)
        throws IOException {

    if (configClass.getMetadata().isAnnotated(Component.class.getName())) {
        // Recursively process any member (nested) classes first
        processMemberClasses(configClass, sourceClass, filter);
    }

    // Process any @PropertySource annotations
    for (AnnotationAttributes propertySource : AnnotationConfigUtils.attributesForRepeatable(
            sourceClass.getMetadata(), org.springframework.context.annotation.PropertySource.class,
            PropertySources.class, true)) {
        if (this.propertySourceRegistry != null) {
            this.propertySourceRegistry.processPropertySource(propertySource);
        }
        else {
            logger.info("Ignoring @PropertySource annotation on [" + sourceClass.getMetadata().getClassName() +
                    "]. Reason: Environment must implement ConfigurableEnvironment");
        }
    }

    // Search for locally declared @ComponentScan annotations first.
    Set<AnnotationAttributes> componentScans = AnnotationConfigUtils.attributesForRepeatable(
            sourceClass.getMetadata(), ComponentScan.class, ComponentScans.class,
            MergedAnnotation::isDirectlyPresent);

    // Fall back to searching for @ComponentScan meta-annotations (which indirectly
    // includes locally declared composed annotations).
    if (componentScans.isEmpty()) {
        componentScans = AnnotationConfigUtils.attributesForRepeatable(sourceClass.getMetadata(),
                ComponentScan.class, ComponentScans.class, MergedAnnotation::isMetaPresent);
    }

    if (!componentScans.isEmpty()) {
        List<Condition> registerBeanConditions = collectRegisterBeanConditions(configClass);
        if (!registerBeanConditions.isEmpty()) {
            throw new ApplicationContextException(
                    "Component scan for configuration class [%s] could not be used with conditions in REGISTER_BEAN phase: %s"
                            .formatted(configClass.getMetadata().getClassName(), registerBeanConditions));
        }
        for (AnnotationAttributes componentScan : componentScans) {
            // The config class is annotated with @ComponentScan -> perform the scan immediately
            Set<BeanDefinitionHolder> scannedBeanDefinitions =
                    this.componentScanParser.parse(componentScan, sourceClass.getMetadata().getClassName());
            // Check the set of scanned definitions for any further config classes and parse recursively if needed
            for (BeanDefinitionHolder holder : scannedBeanDefinitions) {
                BeanDefinition bdCand = holder.getBeanDefinition().getOriginatingBeanDefinition();
                if (bdCand == null) {
                    bdCand = holder.getBeanDefinition();
                }
                if (ConfigurationClassUtils.checkConfigurationClassCandidate(bdCand, this.metadataReaderFactory)) {
                    parse(bdCand.getBeanClassName(), holder.getBeanName());
                }
            }
        }
    }

    // Process any @Import annotations
    processImports(configClass, sourceClass, getImports(sourceClass), filter, true);

    // Process any @ImportResource annotations
    AnnotationAttributes importResource =
            AnnotationConfigUtils.attributesFor(sourceClass.getMetadata(), ImportResource.class);
    if (importResource != null) {
        String[] resources = importResource.getStringArray("locations");
        Class<? extends BeanDefinitionReader> readerClass = importResource.getClass("reader");
        for (String resource : resources) {
            String resolvedResource = this.environment.resolveRequiredPlaceholders(resource);
            configClass.addImportedResource(resolvedResource, readerClass);
        }
    }

    // Process individual @Bean methods
    Set<MethodMetadata> beanMethods = retrieveBeanMethodMetadata(sourceClass);
    for (MethodMetadata methodMetadata : beanMethods) {
        if (methodMetadata.isAnnotated("kotlin.jvm.JvmStatic") && !methodMetadata.isStatic()) {
            continue;
        }
        configClass.addBeanMethod(new BeanMethod(methodMetadata, configClass));
    }

    // Process default methods on interfaces
    processInterfaces(configClass, sourceClass);

    // Process superclass, if any
    if (sourceClass.getMetadata().hasSuperClass()) {
        String superclass = sourceClass.getMetadata().getSuperClassName();
        if (superclass != null && !superclass.startsWith("java")) {
            boolean superclassKnown = this.knownSuperclasses.containsKey(superclass);
            this.knownSuperclasses.add(superclass, configClass);
            if (!superclassKnown) {
                // Superclass found, return its annotation metadata and recurse
                return sourceClass.getSuperClass();
            }
        }
    }

    // No superclass -> processing is complete
    return null;
}
```

## 동작 흐름

```text
 parse(candidates)
 |
 +-- for holder in candidates
 |     정의 종류별로 메타데이터 확보 (애노테이션 정의 / 로드된 클래스 / 클래스 이름으로 ASM 읽기)
 |     processConfigurationClass(configClass)
 |     L184 FULL 로 표시됐지만 인스턴스 @Bean 메서드가 하나도 없음 --> LITE 로 강등 (강화 불필요)
 |
 +-- L200 deferredImportSelectorHandler.process()
          DeferredImportSelector 는 모든 후보 파싱이 끝난 뒤 여기서 한꺼번에 처리
          (Spring Boot 자동 설정이 사용자 설정보다 뒤에 오는 이유)

 processConfigurationClass(configClass)
 |
 | L249 @Conditional 평가 (PARSE_CONFIGURATION 단계) --> 조건 불만족이면 통째로 건너뜀
 |
 | L253 같은 클래스를 이미 처리했음
 |        새 것이 import 됨   --> 기존도 import 면 importedBy 병합, 아니면 무시
 |        새 것이 스캔됨      --> 기존이 import 면 스캔으로 생긴 정의를 제거
 |        새 것이 명시 등록   --> 기존 모델 제거 후 다시 처리
 |
 | L284 do { sourceClass = doProcessConfigurationClass(...) }  부모 클래스가 나오면 반복
 +-- L294 configurationClasses 에 모델 저장

 doProcessConfigurationClass(configClass, sourceClass)
 |
 | [1] @Component 이면 중첩 클래스 먼저                                L309-L312
 |       중첩 클래스 중 설정 후보 --> processConfigurationClass (재귀)
 |
 | [2] @PropertySource                                                L315-L325
 |       Environment 에 프로퍼티 소스 추가   (이후 @Value, @Conditional 에서 사용 가능)
 |
 | [3] @ComponentScan (직접 선언 우선, 없으면 메타 애노테이션)          L328-L361
 |       componentScanParser.parse()  --> 패키지 스캔, 정의 즉시 등록
 |       스캔된 정의 중 설정 후보 --> parse(...) 재귀
 |
 | [4] @Import                                                        L364
 |       processImports()
 |
 | [5] @ImportResource                                                L367-L376
 |       XML 위치를 모델에 기록 (등록은 reader 가 함)
 |
 | [6] @Bean 메서드                                                    L379-L385
 |       리플렉션은 메서드 순서를 보장하지 않아 ASM 으로 선언 순서를 다시 읽음 (L459)
 |       --> configClass.addBeanMethod
 |
 | [7] 인터페이스의 default @Bean 메서드                               L388
 |
 +-- [8] 부모 클래스                                                   L391-L404
          java.* 가 아니고 처음 보는 부모 --> return 부모 SourceClass  (processConfigurationClass 가 반복)
          그 밖 --> return null  (끝)
```

- [4]의 [processImports](01_ConfigurationClassParser.processImports/README.md)가 `@Import` 대상을 종류별로 나눠 처리한다.

## 결과가 쓰이는 곳

```text
 configurationClasses (모델 목록)
      --> processConfigBeanDefinitions L455 getConfigurationClasses()
      --> ConfigurationClassBeanDefinitionReader.loadBeanDefinitions 의 입력

 모델 안의 내용 --> reader 가 무엇으로 바꾸나
      beanMethods                    --> @Bean 1개당 빈 정의 1개
      importedBy (import 된 설정)     --> 설정 클래스 자신의 빈 정의
      importedResources              --> XmlBeanDefinitionReader 로 읽어 등록
      importBeanDefinitionRegistrars --> registrar.registerBeanDefinitions 호출
      beanRegistrars                 --> BeanRegistrar 호출

 [2] 에서 추가한 프로퍼티 소스
      --> 같은 파싱 중 뒤따르는 @Conditional(@ConditionalOnProperty 류) 평가에 바로 반영

 [3] 에서 즉시 등록한 스캔 정의
      --> 모델을 거치지 않으므로 loadBeanDefinitions 를 기다리지 않고 이미 레지스트리에 있다
```

## 하위 메서드

- [01 ConfigurationClassParser.processImports](01_ConfigurationClassParser.processImports/README.md)
