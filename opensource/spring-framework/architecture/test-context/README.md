# Spring 테스트 컨텍스트

`@SpringBootTest`나 `@ContextConfiguration`이 붙은 테스트가 실행될 때, 컨텍스트가 만들어지고 캐시되고 테스트 인스턴스에 의존성이 주입되기까지의 흐름을 위에서 아래로 따라간다. `MockMvc`로 컨트롤러를 호출하는 경로도 함께 다룬다. 폴더 하나가 메서드 하나이고, 설명 안의 메서드 이름을 누르면 그 메서드의 폴더로 들어간다. [spi](spi/README.md)는 테스트 지원의 확장 인터페이스다.

기준 커밋: spring-framework `main` [`c1d4a766929`](https://github.com/spring-projects/spring-framework/tree/c1d4a76692949bdcdebae4b98b104174e4b951cf) (2026-09-10). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 JUnit 5 --> SpringExtension (확장)
 |
 +-- [01] TestContextManager 의 콜백들
        beforeTestClass        클래스 단위 준비
        prepareTestInstance    테스트 인스턴스에 의존성 주입      <-- @Autowired 가 채워지는 곳
        beforeTestMethod       메서드 실행 전 (트랜잭션 시작 등)
        afterTestMethod        메서드 실행 후 (롤백 등)
        afterTestClass         정리
        |
        +-- 각 콜백이 등록된 TestExecutionListener 들을 순서대로 호출
              DependencyInjectionTestExecutionListener   주입
              DirtiesContextTestExecutionListener        컨텍스트 폐기 표시
              TransactionalTestExecutionListener         @Transactional 테스트
              SqlScriptsTestExecutionListener            @Sql 실행
              BeanOverrideTestExecutionListener 등       @MockitoBean
 |
 +-- [02] TestContext.getApplicationContext
        |
        +-- [02-01] DefaultCacheAwareContextLoaderDelegate.loadContext
               MergedContextConfiguration 을 키로 캐시 조회
               있으면 재사용, 없으면 ContextLoader 로 새로 만들어 캐시에 저장
               = 같은 설정을 쓰는 테스트 클래스들이 컨텍스트 하나를 공유한다

 [별도] MockMvc

 mockMvc.perform(get("/users/42"))
 |
 +-- [03] MockMvc.perform
        MockHttpServletRequest 생성, RequestContextHolder 바인딩
        MockFilterChain --> DispatcherServlet.service
        = 서버를 띄우지 않고 [MVC 요청 처리](../webmvc-request-processing/README.md) 흐름을 그대로 탄다
```

## 단계

1. [TestContextManager.prepareTestInstance](01_TestContextManager.prepareTestInstance/README.md)가 리스너들을 호출해 테스트 인스턴스를 준비한다.
2. [DefaultCacheAwareContextLoaderDelegate.loadContext](02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md)가 컨텍스트를 캐시에서 찾거나 새로 만든다.
3. [MockMvc.perform](03_MockMvc.perform/README.md)이 서블릿 컨테이너 없이 요청을 디스패처로 보낸다.

## 결과가 쓰이는 곳

```text
 캐시된 ApplicationContext
      --> 같은 MergedContextConfiguration 을 가진 모든 테스트가 공유
      --> 테스트 스위트 전체 실행 시간을 좌우하는 요소
      --> @MockitoBean 은 contextCustomizers 를 통해 키를 바꾸므로 컨텍스트가 하나 더 생긴다
      --> @DirtiesContext 는 키를 바꾸지 않는다. 같은 키의 컨텍스트를 캐시에서 제거하고
          닫을 뿐이어서, 다음 요청 때 같은 키로 다시 만들어진다

 주입된 테스트 인스턴스
      --> 필드의 @Autowired, @Value 가 채워진 상태로 테스트 메서드 실행
      --> 테스트 인스턴스는 컨테이너가 만든 빈이 아니다 (주입만 받는다)

 MockMvc 결과
      --> MvcResult 에 요청/응답/핸들러/모델이 모두 담긴다
      --> 실제 서버와 달리 같은 스레드에서 동기로 끝난다
```

## 다루지 않는 것

`@Sql` 스크립트 실행, 트랜잭션 테스트의 롤백 처리, `@MockitoBean`의 빈 오버라이드 구현은 각각 별도 리스너의 내부다. `WebTestClient`와 `RestTestClient`는 클라이언트 쪽 도구라 [HTTP 클라이언트](../http-client/README.md) 계열에 가깝다.

## 하위 메서드

- [01 TestContextManager.prepareTestInstance](01_TestContextManager.prepareTestInstance/README.md)
- [02 DefaultCacheAwareContextLoaderDelegate.loadContext](02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md)
- [03 MockMvc.perform](03_MockMvc.perform/README.md)
- [spi](spi/README.md) — 테스트 컨텍스트, 리스너, 컨텍스트 로더, 캐시
