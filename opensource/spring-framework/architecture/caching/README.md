# Spring 캐시 추상화

`@Cacheable`이 붙은 메서드를 호출했을 때 캐시를 먼저 보고, 없을 때만 실제 메서드를 부르고, 결과를 저장하기까지의 흐름을 위에서 아래로 따라간다. `@CachePut`과 `@CacheEvict`도 같은 인터셉터가 한 번에 처리한다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 캐시 추상화의 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 어디에서 들어오는가

`@Cacheable`도 트랜잭션과 같은 구조다. `@EnableCaching`이 어드바이저를 등록하고, [AOP 프록시](../aop-proxy/README.md)가 만들어지고, 프록시 호출이 인터셉터 체인을 돌 때 `CacheInterceptor`가 끼어든다.

```text
 @EnableCaching
   --> CachingConfigurationSelector --> ProxyCachingConfiguration
         @Bean BeanFactoryCacheOperationSourceAdvisor    (어드바이저)
         @Bean AnnotationCacheOperationSource            (어디에 붙었나 판정)
         @Bean CacheInterceptor                          (무엇을 할지)
   --> 프록시.메서드() --> ReflectiveMethodInvocation.proceed --> CacheInterceptor.invoke
```

## 전체 그림

```text
 CacheInterceptor.invoke(invocation)
   invocation.proceed() 를 CacheOperationInvoker 로 감싸 넘긴다
 |
 +-- [01] CacheAspectSupport.execute
        이 메서드에 붙은 캐시 연산 목록(@Cacheable/@CachePut/@CacheEvict)을 모아 컨텍스트 구성
        연산이 없으면 그냥 타깃 실행
        |
        +-- sync = true 인 @Cacheable --> executeSynchronized (Cache.get(key, Callable) 에 맡긴다)
        |
        +-- 일반 경로
              1) beforeInvocation = true 인 @CacheEvict 먼저 수행
              |
              2) [01-01] findCachedValue     @Cacheable 조회
              |      condition 통과 --> 키 생성 --> 캐시들에서 조회
              |      찾으면 그 값이 곧 결과 후보
              |
              3) [01-02] evaluate
                    캐시 적중 + @CachePut 없음 --> 타깃을 부르지 않고 그 값 사용
                    그 밖                      --> 타깃 실행
                    캐시 미스였으면 @Cacheable 저장 요청 수집
                    @CachePut 저장 요청 수집 --> 순서대로 put
                    beforeInvocation = false 인 @CacheEvict 수행
```

## 단계

1. [CacheAspectSupport.execute](01_CacheAspectSupport.execute/README.md)가 연산 목록을 모아 전체 순서를 지휘한다.

## 결과가 쓰이는 곳

```text
 캐시 적중
      --> 타깃 메서드가 호출되지 않는다 (트랜잭션, DB 접근도 일어나지 않는다)
      --> 반환 타입이 Optional 이면 다시 감싸서 돌려준다

 캐시 저장
      --> CacheManager 가 준 Cache 구현에 위임 (ConcurrentMap, Caffeine, Redis 등)
      --> unless 조건과 null 저장 여부가 저장 시점에 판정된다

 자기 호출
      --> AOP 프록시를 거치지 않으므로 캐시가 적용되지 않는다
          (같은 클래스 안에서 this.cachedMethod() 호출)
```

## 다루지 않는 것

리액티브 반환 타입(`Mono`, `Flux`)과 `CompletableFuture` 경로는 같은 메서드 안에서 갈라지지만, 이 지도는 동기 경로를 따라간다. JSR-107(JCache) 애노테이션 지원도 별도 계열이다.

## 하위 메서드

- [01 CacheAspectSupport.execute](01_CacheAspectSupport.execute/README.md)
- [spi](spi/README.md) — 캐시, 캐시 매니저, 키 생성기, 오류 처리기
