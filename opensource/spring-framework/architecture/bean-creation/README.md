# Spring 빈 생성

`getBean(name)` 한 번이 객체 하나를 만들어 돌려주기까지의 흐름을 위에서 아래로 따라간다. 인스턴스를 만들고, 의존성을 주입하고, 초기화 콜백을 부르고, 프록시를 씌우고, 소멸 콜백을 등록하는 전 과정이다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 이 과정에 끼어드는 확장 인터페이스 모음이다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 이 흐름을 부르는 쪽

```text
 [컨테이너 기동] preInstantiateSingletons --> getBean(이름)        lazy 아닌 싱글톤 전부
 [주입] doResolveDependency --> resolveBean --> getBean(이름)      @Autowired 대상
 [사용자 코드] context.getBean(Foo.class)
 [@Bean 메서드] 설정 클래스 인스턴스를 얻기 위한 getBean
 [스코프] scope.get(이름, factory) --> createBean                  request, session 등
```

시작점은 [컨테이너 기동](../container-refresh/README.md)의 [preInstantiateSingletons](../container-refresh/01_AbstractApplicationContext.refresh/09_AbstractApplicationContext.finishBeanFactoryInitialization/01_DefaultListableBeanFactory.preInstantiateSingletons/README.md)다.

## 전체 그림

```text
 AbstractBeanFactory.getBean(name)
 |
 +-- [01] doGetBean
      |
      +-- 싱글톤 캐시 조회 (1차) --> 있으면 바로 반환
      |
      +-- [01-01] DefaultSingletonBeanRegistry.getSingleton(name, factory)
      |      생성 잠금, 생성 중 표시, 끝나면 캐시에 등록
      |      |
      |      +-- [01-02] createBean
      |             |
      |             +-- resolveBeforeInstantiation ---> InstantiationAwareBeanPostProcessor  (spi)
      |             |     처리기가 객체를 돌려주면 여기서 끝 (프록시 대체)
      |             |
      |             +-- doCreateBean
      |                   |
      |                   +-- createBeanInstance          생성자 또는 팩토리 메서드로 인스턴스화
      |                   |     +-- instantiateUsingFactoryMethod   @Bean 메서드
      |                   |     +-- autowireConstructor             생성자 주입
      |                   |
      |                   +-- applyMergedBeanDefinitionPostProcessors ---> MergedBeanDefinitionPostProcessor (spi)
      |                   |     @Autowired, @PostConstruct 위치를 미리 스캔해 캐시
      |                   |
      |                   +-- addSingletonFactory(조기 참조)   순환 참조 대비
      |                   |
      |                   +-- populateBean               필드/세터 주입
      |                   |     +-- resolveDependency    후보 탐색, @Qualifier, @Primary 판정
      |                   |
      |                   +-- initializeBean
      |                   |     +-- invokeAwareMethods                 BeanNameAware 등          (spi)
      |                   |     +-- BeanPostProcessor 초기화 전 콜백   @PostConstruct, *Aware
      |                   |     +-- invokeInitMethods                  InitializingBean, init-method (spi)
      |                   |     +-- BeanPostProcessor 초기화 후 콜백   AOP 프록시 생성
      |                   |
      |                   +-- registerDisposableBeanIfNecessary        @PreDestroy, DisposableBean
      |
      +-- getObjectForBeanInstance ---> FactoryBean  (spi)
             FactoryBean 이면 getObject() 결과를 대신 반환
```

## 단계

1. [AbstractBeanFactory.doGetBean](01_AbstractBeanFactory.doGetBean/README.md)이 캐시 조회, 스코프 분기, 의존 빈 선행 생성을 맡고 실제 생성은 아래로 넘긴다.

## 결과가 쓰이는 곳

```text
 완성된 빈
      +-- 싱글톤     --> singletonObjects 캐시 --> 이후 getBean 은 캐시에서 즉시 반환
      +-- 프로토타입 --> 호출자에게만 전달, 컨테이너는 보관하지 않음 (소멸 콜백도 없음)
      +-- 스코프 빈  --> Scope 구현이 보관 (예: HTTP 세션 속성)

 소멸 콜백 등록분
      --> 컨테이너 close 시 @PreDestroy, DisposableBean.destroy, destroy-method 실행
```

## 다루지 않는 것

AOP 프록시가 만들어지는 내부(어드바이저 선택, JDK 프록시와 CGLIB 선택)는 [AOP 프록시](../aop-proxy/README.md) 흐름에서 다룬다. 이 지도에서는 초기화 후 콜백이 프록시를 돌려준다는 지점까지만 표시했다.

## 하위 메서드

- [01 AbstractBeanFactory.doGetBean](01_AbstractBeanFactory.doGetBean/README.md)
- [spi](spi/README.md) — 빈 생성 중간의 확장 인터페이스
