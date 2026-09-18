# AbstractApplicationEventMulticaster.getApplicationListeners

상위: [SimpleApplicationEventMulticaster.multicastEvent](../README.md)

이벤트 타입과 소스 타입에 맞는 리스너만 골라 정렬해 돌려준다. 같은 조합은 캐시하므로, 두 번째 발행부터는 선별 비용이 거의 없다.

## 실제 코드

`spring-context` / `org.springframework.context.event` / `AbstractApplicationEventMulticaster.java` L187-L223 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/AbstractApplicationEventMulticaster.java#L187-L223))

```java
// AbstractApplicationEventMulticaster.java L187-L223
 */
protected Collection<ApplicationListener<?>> getApplicationListeners(
        ApplicationEvent event, ResolvableType eventType) {

    Object source = event.getSource();
    Class<?> sourceType = (source != null ? source.getClass() : null);
    ListenerCacheKey cacheKey = new ListenerCacheKey(eventType, sourceType);

    // Potential new retriever to populate
    CachedListenerRetriever newRetriever = null;

    // Quick check for existing entry on ConcurrentHashMap
    CachedListenerRetriever existingRetriever = this.retrieverCache.get(cacheKey);
    if (existingRetriever == null) {
        // Caching a new ListenerRetriever if possible
        if (this.beanClassLoader == null ||
                (ClassUtils.isCacheSafe(event.getClass(), this.beanClassLoader) &&
                        (sourceType == null || ClassUtils.isCacheSafe(sourceType, this.beanClassLoader)))) {
            newRetriever = new CachedListenerRetriever();
            existingRetriever = this.retrieverCache.putIfAbsent(cacheKey, newRetriever);
            if (existingRetriever != null) {
                newRetriever = null;  // no need to populate it in retrieveApplicationListeners
            }
        }
    }

    if (existingRetriever != null) {
        Collection<ApplicationListener<?>> result = existingRetriever.getApplicationListeners();
        if (result != null) {
            return result;
        }
        // If result is null, the existing retriever is not fully populated yet by another thread.
        // Proceed like caching wasn't possible for this current local attempt.
    }

    return retrieveApplicationListeners(eventType, sourceType, newRetriever);
}
```

`spring-context` / `org.springframework.context.event` / `AbstractApplicationEventMulticaster.java` L232-L327 ([GitHub](https://github.com/spring-projects/spring-framework/blob/c1d4a76692949bdcdebae4b98b104174e4b951cf/spring-context/src/main/java/org/springframework/context/event/AbstractApplicationEventMulticaster.java#L232-L327))

```java
// AbstractApplicationEventMulticaster.java L232-L327
@SuppressWarnings("NullAway") // Dataflow analysis limitation
private Collection<ApplicationListener<?>> retrieveApplicationListeners(
        ResolvableType eventType, @Nullable Class<?> sourceType, @Nullable CachedListenerRetriever retriever) {

    List<ApplicationListener<?>> allListeners = new ArrayList<>();
    Set<ApplicationListener<?>> filteredListeners = (retriever != null ? new LinkedHashSet<>() : null);
    Set<String> filteredListenerBeans = (retriever != null ? new LinkedHashSet<>() : null);

    Set<ApplicationListener<?>> listeners;
    Set<String> listenerBeans;
    synchronized (this.defaultRetriever) {
        listeners = new LinkedHashSet<>(this.defaultRetriever.applicationListeners);
        listenerBeans = new LinkedHashSet<>(this.defaultRetriever.applicationListenerBeans);
    }

    // Add programmatically registered listeners, including ones coming
    // from ApplicationListenerDetector (singleton beans and inner beans).
    for (ApplicationListener<?> listener : listeners) {
        if (supportsEvent(listener, eventType, sourceType)) {
            if (retriever != null) {
                filteredListeners.add(listener);
            }
            allListeners.add(listener);
        }
    }

    // Add listeners by bean name, potentially overlapping with programmatically
    // registered listeners above - but here potentially with additional metadata.
    if (!listenerBeans.isEmpty()) {
        ConfigurableBeanFactory beanFactory = getBeanFactory();
        for (String listenerBeanName : listenerBeans) {
            try {
                if (supportsEvent(beanFactory, listenerBeanName, eventType)) {
                    ApplicationListener<?> listener =
                            beanFactory.getBean(listenerBeanName, ApplicationListener.class);

                    // Despite best efforts to avoid it, unwrapped proxies (singleton targets) can end up in the
                    // list of programmatically registered listeners. In order to avoid duplicates, we need to find
                    // and replace them by their proxy counterparts, because if both a proxy and its target end up
                    // in 'allListeners', listeners will fire twice.
                    ApplicationListener<?> unwrappedListener =
                            (ApplicationListener<?>) AopProxyUtils.ultimateSingletonTarget(listener);
                    if (listener != unwrappedListener) {
                        if (filteredListeners != null && filteredListeners.contains(unwrappedListener)) {
                            filteredListeners.remove(unwrappedListener);
                            filteredListeners.add(listener);
                        }
                        if (allListeners.contains(unwrappedListener)) {
                            allListeners.remove(unwrappedListener);
                            allListeners.add(listener);
                        }
                    }

                    if (!allListeners.contains(listener) && supportsEvent(listener, eventType, sourceType)) {
                        if (retriever != null) {
                            if (beanFactory.isSingleton(listenerBeanName)) {
                                filteredListeners.add(listener);
                            }
                            else {
                                filteredListenerBeans.add(listenerBeanName);
                            }
                        }
                        allListeners.add(listener);
                    }
                }
                else {
                    // Remove non-matching listeners that originally came from
                    // ApplicationListenerDetector, possibly ruled out by additional
                    // BeanDefinition metadata (for example, factory method generics) above.
                    Object listener = beanFactory.getSingleton(listenerBeanName);
                    if (retriever != null) {
                        filteredListeners.remove(listener);
                    }
                    allListeners.remove(listener);
                }
            }
            catch (NoSuchBeanDefinitionException ex) {
                // Singleton listener instance (without backing bean definition) disappeared -
                // probably in the middle of the destruction phase
            }
        }
    }

    AnnotationAwareOrderComparator.sort(allListeners);
    if (retriever != null) {
        if (CollectionUtils.isEmpty(filteredListenerBeans)) {
            retriever.applicationListeners = new LinkedHashSet<>(allListeners);
            retriever.applicationListenerBeans = filteredListenerBeans;
        }
        else {
            retriever.applicationListeners = filteredListeners;
            retriever.applicationListenerBeans = filteredListenerBeans;
        }
    }
    return allListeners;
}
```

## 동작 흐름

```text
 getApplicationListeners(event, eventType)
 |
 | L193 cacheKey = (이벤트 타입, 소스 타입)
 |
 +-- L199 캐시에 있음 --> 그 목록 반환
 |      (다른 스레드가 채우는 중이면 캐시 없이 직접 계산)
 |
 +-- L222 retrieveApplicationListeners(eventType, sourceType, retriever)
       |
       | [1] L242 등록된 리스너 스냅샷을 잠금 아래에서 복사
       |       객체로 등록된 리스너 + 이름만 등록된 리스너 빈
       |
       | [2] L249 객체 리스너
       |       supportsEvent(listener, eventType, sourceType) 로 거른다
       |         GenericApplicationListener 면 제네릭 타입/소스 타입 질의
       |         일반 ApplicationListener 면 선언된 제네릭 타입으로 판정
       |
       | [3] L260 이름만 등록된 리스너 빈
       |       먼저 빈 정의의 타입 정보로 거른다 (인스턴스화 전 1차 판정)
       |       통과하면 getBean 으로 인스턴스를 얻어 다시 판정
       |       프록시와 원본이 중복으로 들어가지 않게 교체 처리
       |
       | [4] L315 AnnotationAwareOrderComparator.sort
       |       @Order / Ordered 로 실행 순서 확정
       |
       +-- L316 캐시에 저장 (싱글톤은 객체로, 그 밖은 이름으로)
```

## 결과가 쓰이는 곳

```text
 반환 목록
      --> multicastEvent 가 이 순서대로 호출
      --> 이벤트 타입이 다르면 다른 목록 (캐시 키가 다름)

 [3] 의 1차 판정 (인스턴스화 전)
      --> 리스너 빈을 불필요하게 만들지 않는다
      --> 기동 초기에 발행된 이벤트가 엉뚱한 빈을 앞당겨 생성하는 것을 줄인다

 캐시
      --> 리스너를 나중에 추가하면 무효화된다 (addApplicationListener 가 캐시를 비운다)
      --> 프로토타입 리스너 빈은 이름으로 캐시되어 발행 때마다 새로 조회된다
```

리스너가 호출되지 않을 때 확인할 지점이 이 메서드다. 제네릭 타입이 맞지 않으면 `supportsEvent`에서 걸러지고, 그 판단은 이벤트 타입과 리스너 선언 타입의 `ResolvableType` 비교로 이뤄진다.
