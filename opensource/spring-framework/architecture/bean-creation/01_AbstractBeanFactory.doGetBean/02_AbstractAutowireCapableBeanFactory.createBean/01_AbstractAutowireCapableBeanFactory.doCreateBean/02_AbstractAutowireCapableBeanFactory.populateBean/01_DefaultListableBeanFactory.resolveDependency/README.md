# DefaultListableBeanFactory.resolveDependency

상위: [AbstractAutowireCapableBeanFactory.populateBean](../README.md)

주입 지점 하나(필드, 생성자 파라미터, 세터 파라미터)에 넣을 값을 결정한다. `@Value` 해석, 이름 일치, 타입 후보 수집, `@Primary`와 `@Qualifier` 판정이 모두 여기서 일어난다.

## 실제 코드

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultListableBeanFactory.java` L1637-L1659 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultListableBeanFactory.java#L1637-L1659))

```java
// DefaultListableBeanFactory.java L1637-L1659
public @Nullable Object resolveDependency(DependencyDescriptor descriptor, @Nullable String requestingBeanName,
        @Nullable Set<String> autowiredBeanNames, @Nullable TypeConverter typeConverter) throws BeansException {

    descriptor.initParameterNameDiscovery(getParameterNameDiscoverer());
    if (Optional.class == descriptor.getDependencyType()) {
        return createOptionalDependency(descriptor, requestingBeanName, autowiredBeanNames, null);
    }
    else if (ObjectFactory.class == descriptor.getDependencyType() ||
            ObjectProvider.class == descriptor.getDependencyType()) {
        return new DependencyObjectProvider(descriptor, requestingBeanName);
    }
    else if (jakartaInjectProviderClass == descriptor.getDependencyType()) {
        return new Jsr330Factory().createDependencyProvider(descriptor, requestingBeanName);
    }
    else if (descriptor.supportsLazyResolution()) {
        Object result = getAutowireCandidateResolver().getLazyResolutionProxyIfNecessary(
                descriptor, requestingBeanName);
        if (result != null) {
            return result;
        }
    }
    return doResolveDependency(descriptor, requestingBeanName, autowiredBeanNames, typeConverter);
}
```

`spring-beans` / `org.springframework.beans.factory.support` / `DefaultListableBeanFactory.java` L1662-L1776 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-beans/src/main/java/org/springframework/beans/factory/support/DefaultListableBeanFactory.java#L1662-L1776))

```java
// DefaultListableBeanFactory.java L1662-L1776
public @Nullable Object doResolveDependency(DependencyDescriptor descriptor, @Nullable String beanName,
        @Nullable Set<String> autowiredBeanNames, @Nullable TypeConverter typeConverter) throws BeansException {

    InjectionPoint previousInjectionPoint = ConstructorResolver.setCurrentInjectionPoint(descriptor);
    try {
        // Step 1: pre-resolved shortcut for single bean match, for example, from @Autowired
        Object shortcut = descriptor.resolveShortcut(this);
        if (shortcut != null) {
            return shortcut;
        }

        Class<?> type = descriptor.getDependencyType();

        // Step 2: pre-defined value or expression, for example, from @Value
        Object value = getAutowireCandidateResolver().getSuggestedValue(descriptor);
        if (value != null) {
            if (value instanceof String strValue) {
                String resolvedValue = resolveEmbeddedValue(strValue);
                BeanDefinition bd = (beanName != null && containsBean(beanName) ?
                        getMergedBeanDefinition(beanName) : null);
                value = evaluateBeanDefinitionString(resolvedValue, bd);
            }
            TypeConverter converter = (typeConverter != null ? typeConverter : getTypeConverter());
            try {
                return converter.convertIfNecessary(value, type, descriptor.getTypeDescriptor());
            }
            catch (UnsupportedOperationException ex) {
                // A custom TypeConverter which does not support TypeDescriptor resolution...
                return (descriptor.getField() != null ?
                        converter.convertIfNecessary(value, type, descriptor.getField()) :
                        converter.convertIfNecessary(value, type, descriptor.getMethodParameter()));
            }
        }

        // Step 3: shortcut for declared dependency name or qualifier-suggested name matching target bean name
        if (descriptor.usesStandardBeanLookup()) {
            String dependencyName = descriptor.getDependencyName();
            if (dependencyName == null || !containsBean(dependencyName)) {
                String suggestedName = getAutowireCandidateResolver().getSuggestedName(descriptor);
                dependencyName = (suggestedName != null && containsBean(suggestedName) ? suggestedName : null);
            }
            if (dependencyName != null) {
                dependencyName = canonicalName(dependencyName);  // dependency name can be alias of target name
                if (isTypeMatch(dependencyName, type) && isAutowireCandidate(dependencyName, descriptor) &&
                        !isFallback(dependencyName) && !hasPrimaryConflict(dependencyName, type) &&
                        !isSelfReference(beanName, dependencyName)) {
                    if (autowiredBeanNames != null) {
                        autowiredBeanNames.add(dependencyName);
                    }
                    Object dependencyBean = resolveBean(dependencyName, descriptor.getResolvableType());
                    return resolveInstance(dependencyBean, descriptor, type, dependencyName);
                }
            }
        }

        // Step 4a: multiple beans as stream / array / standard collection / plain map
        Object multipleBeans = resolveMultipleBeans(descriptor, beanName, autowiredBeanNames, typeConverter);
        if (multipleBeans != null) {
            return multipleBeans;
        }
        // Step 4b: direct bean matches, possibly direct beans of type Collection / Map
        Map<String, Object> matchingBeans = findAutowireCandidates(beanName, type, descriptor);
        if (matchingBeans.isEmpty()) {
            // Step 4c (fallback): custom Collection / Map declarations for collecting multiple beans
            multipleBeans = resolveMultipleBeansFallback(descriptor, beanName, autowiredBeanNames, typeConverter);
            if (multipleBeans != null) {
                return multipleBeans;
            }
            // Raise exception if nothing found for required injection point
            if (isRequired(descriptor)) {
                raiseNoMatchingBeanFound(type, descriptor.getResolvableType(), descriptor);
            }
            return null;
        }

        String autowiredBeanName;
        Object instanceCandidate;

        // Step 5: determine single candidate
        if (matchingBeans.size() > 1) {
            autowiredBeanName = determineAutowireCandidate(matchingBeans, descriptor);
            if (autowiredBeanName == null) {
                if (isRequired(descriptor) || !indicatesArrayCollectionOrMap(type)) {
                    // Raise exception if no clear match found for required injection point
                    return descriptor.resolveNotUnique(descriptor.getResolvableType(), matchingBeans);
                }
                else {
                    // In case of an optional Collection/Map, silently ignore a non-unique case:
                    // possibly it was meant to be an empty collection of multiple regular beans
                    // (before 4.3 in particular when we didn't even look for collection beans).
                    return null;
                }
            }
            instanceCandidate = matchingBeans.get(autowiredBeanName);
        }
        else {
            // We have exactly one match.
            Map.Entry<String, Object> entry = matchingBeans.entrySet().iterator().next();
            autowiredBeanName = entry.getKey();
            instanceCandidate = entry.getValue();
        }

        // Step 6: validate single result
        if (autowiredBeanNames != null) {
            autowiredBeanNames.add(autowiredBeanName);
        }
        if (instanceCandidate instanceof Class) {
            instanceCandidate = descriptor.resolveCandidate(autowiredBeanName, type, this);
        }
        return resolveInstance(instanceCandidate, descriptor, type, autowiredBeanName);
    }
    finally {
        ConstructorResolver.setCurrentInjectionPoint(previousInjectionPoint);
    }
}
```

## 동작 흐름

```text
 resolveDependency(descriptor, beanName, autowiredBeanNames, typeConverter)
 |
 +-- L1641 특수 타입 먼저 처리
 |     Optional<T>                    --> createOptionalDependency (없으면 Optional.empty)
 |     ObjectFactory / ObjectProvider --> 지금 해석하지 않고 제공자 객체를 반환
 |     jakarta.inject.Provider        --> 같은 방식의 제공자
 |     @Lazy 지원 대상                --> 지연 프록시를 반환 (실제 해석은 첫 호출 때)
 |
 +-- doResolveDependency
       |
       | Step 1 L1668 resolveShortcut      이전 해석 결과 재사용 (프로토타입 반복 생성 최적화)
       |
       | Step 2 L1676 @Value 등 제안 값
       |          문자열이면 ${...} 해석 --> SpEL 평가 --> TypeConverter 로 대상 타입 변환
       |
       | Step 3 L1697 이름 일치 지름길
       |          주입 지점 이름(또는 @Qualifier 가 제안한 이름)과 같은 빈이 있고
       |          타입이 맞고, 자기 자신이 아니고, primary 충돌이 없으면 --> 그 빈
       |
       | Step 4a L1718 컬렉션/배열/맵/스트림 --> 해당 타입 빈을 모아서 반환
       | Step 4b L1723 findAutowireCandidates    타입으로 후보 수집
       |            resolvableDependencies 표(ApplicationContext 등)를 먼저 보고
       |            그다음 타입이 맞는 빈 이름들을 후보로
       |
       +-- 후보 0개 --> required 면 NoSuchBeanDefinitionException
       +-- 후보 1개 --> 그 빈
       +-- 후보 여러 개 --> determineAutowireCandidate (L2038)
                  1) @Primary 후보
                  2) 주입 지점 이름과 같은 빈 이름
                  3) @Qualifier 가 제안한 이름과 같은 빈 이름
                  4) @Priority 값이 가장 높은 후보
                  5) 유일한 default-candidate
                  6) resolvableDependencies 에 직접 등록된 객체
                못 고르면 NoUniqueBeanDefinitionException
```

## 결과가 쓰이는 곳

```text
 반환한 값
      --> populateBean 의 field.set / setter 호출 인자
      --> createBeanInstance 의 생성자 인자

 autowiredBeanNames 에 기록한 이름
      --> registerDependentBean 으로 의존 관계 기록
          --> 소멸 순서(의존하는 쪽 먼저) 와 순환 검사에 사용

 resolveShortcut 캐시
      --> 같은 주입 지점을 다시 해석할 때 후보 탐색 생략

 실패 예외
      NoSuchBeanDefinitionException     --> 빈이 없음
      NoUniqueBeanDefinitionException   --> 후보가 여럿인데 고를 수 없음
      --> doCreateBean --> BeanCreationException 으로 감싸져 기동 실패로 이어짐
```

`ObjectProvider`로 감싸면 이 해석이 주입 시점이 아니라 사용 시점으로 미뤄진다. 순환 참조나 선택적 의존성을 다룰 때 쓰는 방법이다.
