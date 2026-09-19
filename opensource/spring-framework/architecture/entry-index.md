# 진입점 인덱스

흐름 지도를 "내가 쓰는 것"에서 거꾸로 찾아 들어가는 색인이다. 스프링 동작이 시작되는 자리는 두 가지다. 하나는 **내가 호출하는 것**이고, 다른 하나는 **내가 선언하면 스프링이 호출하는 것**이다. 아래 두 표는 그 둘을 각각 처리 주체와 흐름 노드로 잇는다.

흐름 전체 목록은 [architecture 인덱스](index.md)에 있다. 기준 커밋은 각 흐름 README에 적힌 `c1d4a766929`(2026-09-10)다.

## 선언형 진입점 — 애노테이션

내가 붙이면 스프링이 찾아서 호출한다. "처리 주체"는 그 애노테이션을 실제로 읽어 동작으로 바꾸는 클래스다.

### 컨테이너와 빈

| 애노테이션 | 처리 주체 | 들어가는 자리 |
|---|---|---|
| `@Configuration` | `ConfigurationClassPostProcessor` | [설정 클래스 파싱](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/README.md) |
| `@Bean` | `ConfigurationClassBeanDefinitionReader` | [빈 정의 등록](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/02_ConfigurationClassBeanDefinitionReader.loadBeanDefinitions/README.md) |
| `@Import`, `@ImportSelector` | `ConfigurationClassParser.processImports` | [import 처리](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/01_ConfigurationClassParser.parse/01_ConfigurationClassParser.processImports/README.md) |
| `@Component`, `@Service`, `@Controller`, `@RestController` | `ClassPathScanningCandidateComponentProvider` → `ClassPathBeanDefinitionScanner` | [설정 클래스 파싱](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/README.md) |
| `@ComponentScan` | `ComponentScanAnnotationParser`, `ClassPathBeanDefinitionScanner` | [설정 클래스 파싱](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/01_ConfigurationClassParser.parse/README.md) |
| `@PropertySource` | `PropertySourceRegistry` (파서 안에서) | [설정 클래스 파싱](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/01_ConfigurationClassParser.parse/README.md) |
| `@EnableTransactionManagement`, `@EnableAsync`, `@EnableCaching`, `@EnableWebMvc` | 각 `@Import` 대상 설정 클래스 (예: `ProxyAsyncConfiguration`) | [import 처리](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/01_ConfigurationClassParser.parse/01_ConfigurationClassParser.processImports/README.md) |
| `@Conditional`, `@Profile` | `ConditionEvaluator`, `ProfileCondition` | [설정 클래스 파싱](container-refresh/01_AbstractApplicationContext.refresh/04_AbstractApplicationContext.invokeBeanFactoryPostProcessors/01_PostProcessorRegistrationDelegate.invokeBeanFactoryPostProcessors/01_ConfigurationClassPostProcessor.processConfigBeanDefinitions/01_ConfigurationClassParser.parse/README.md) |
| `@Autowired`, `@Inject` | `AutowiredAnnotationBeanPostProcessor` | [프로퍼티 주입](bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/02_AbstractAutowireCapableBeanFactory.populateBean/README.md) |
| `@Qualifier`, `@Primary`, `@Fallback` | `QualifierAnnotationAutowireCandidateResolver.checkQualifiers`(후보 필터) / `DefaultListableBeanFactory.determineAutowireCandidate`(@Primary, @Fallback) | [의존성 해소](bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/02_AbstractAutowireCapableBeanFactory.populateBean/01_DefaultListableBeanFactory.resolveDependency/README.md) |
| `@Value` | `AutowiredAnnotationBeanPostProcessor` + 값 해석기 | [의존성 해소](bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/02_AbstractAutowireCapableBeanFactory.populateBean/01_DefaultListableBeanFactory.resolveDependency/README.md), [플레이스홀더 치환](resource-environment/02_PropertySourcesPropertyResolver.getProperty/01_AbstractPropertyResolver.resolvePlaceholders/README.md) |
| `@Resource` | `CommonAnnotationBeanPostProcessor` | [프로퍼티 주입](bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/02_AbstractAutowireCapableBeanFactory.populateBean/README.md) |
| `@PostConstruct`, `@PreDestroy` | `CommonAnnotationBeanPostProcessor` (상위 `InitDestroyAnnotationBeanPostProcessor`) | [초기화 콜백](bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/03_AbstractAutowireCapableBeanFactory.initializeBean/README.md), [소멸 등록](bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/04_AbstractBeanFactory.registerDisposableBeanIfNecessary/README.md) |
| `@Scope` | `AnnotationScopeMetadataResolver`, `ScopedProxyUtils` | [빈 조회](bean-creation/01_AbstractBeanFactory.doGetBean/README.md), [Scope SPI](bean-creation/spi/Scope/README.md) |
| `@Lazy` | `AnnotationConfigUtils`(정의의 lazyInit) / `ContextAnnotationAutowireCandidateResolver`(주입 지점 지연 프록시) | [싱글톤 선생성](container-refresh/01_AbstractApplicationContext.refresh/09_AbstractApplicationContext.finishBeanFactoryInitialization/01_DefaultListableBeanFactory.preInstantiateSingletons/README.md), [의존성 해소](bean-creation/01_AbstractBeanFactory.doGetBean/02_AbstractAutowireCapableBeanFactory.createBean/01_AbstractAutowireCapableBeanFactory.doCreateBean/02_AbstractAutowireCapableBeanFactory.populateBean/01_DefaultListableBeanFactory.resolveDependency/README.md) |
| `@DependsOn` | `AnnotationConfigUtils`(정의에 기록) → `AbstractBeanFactory.doGetBean`(먼저 생성) | [빈 조회](bean-creation/01_AbstractBeanFactory.doGetBean/README.md) |

### AOP와 횡단 관심사

| 애노테이션 | 처리 주체 | 들어가는 자리 |
|---|---|---|
| `@Aspect`, `@Before`, `@Around` 등 | `AnnotationAwareAspectJAutoProxyCreator`, `ReflectiveAspectJAdvisorFactory` | [어드바이저 선별](aop-proxy/01_AbstractAutoProxyCreator.postProcessAfterInitialization/01_AbstractAutoProxyCreator.wrapIfNecessary/01_AbstractAdvisorAutoProxyCreator.findEligibleAdvisors/README.md), [Advisor SPI](aop-proxy/spi/Advisor/README.md) |
| `@Transactional` | `BeanFactoryTransactionAttributeSourceAdvisor` → `TransactionInterceptor` | [트랜잭션 진입](transaction/01_TransactionAspectSupport.invokeWithinTransaction/README.md) |
| `@Cacheable`, `@CachePut`, `@CacheEvict` | `BeanFactoryCacheOperationSourceAdvisor` → `CacheInterceptor` | [캐시 처리](caching/01_CacheAspectSupport.execute/README.md) |
| `@Scheduled` | `ScheduledAnnotationBeanPostProcessor` | [작업 등록](scheduling-async/01_ScheduledAnnotationBeanPostProcessor.postProcessAfterInitialization/README.md) |
| `@Async` | `AsyncAnnotationBeanPostProcessor` → `AnnotationAsyncExecutionInterceptor` | [비동기 전환](scheduling-async/03_AsyncExecutionInterceptor.invoke/README.md) |
| `@EventListener` | `EventListenerMethodProcessor` → `ApplicationListenerMethodAdapter` | [리스너 메서드 호출](event-publishing/03_ApplicationListenerMethodAdapter.processEvent/README.md) |
| `@TransactionalEventListener` | `TransactionalApplicationListenerMethodAdapter` | [리스너 메서드 호출](event-publishing/03_ApplicationListenerMethodAdapter.processEvent/README.md), [동기화 SPI](transaction/spi/TransactionSynchronization/README.md) |

### 웹과 메시징

| 애노테이션 | 처리 주체 | 들어가는 자리 |
|---|---|---|
| `@RequestMapping`, `@GetMapping` 등 | `RequestMappingHandlerMapping` → `RequestMappingHandlerAdapter` | [핸들러 조회](webmvc-request-processing/02_DispatcherServlet.doDispatch/02_DispatcherServlet.getHandler/01_AbstractHandlerMapping.getHandler/01_AbstractHandlerMethodMapping.lookupHandlerMethod/README.md), [핸들러 호출](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/README.md) |
| `@RequestBody`, `@ResponseBody` | `RequestResponseBodyMethodProcessor` | [인자 해석](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/01_InvocableHandlerMethod.getMethodArgumentValues/README.md), [본문 쓰기](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/03_HandlerMethodReturnValueHandlerComposite.handleReturnValue/01_AbstractMessageConverterMethodProcessor.writeWithMessageConverters/README.md) |
| `@RequestParam`, `@PathVariable` | `RequestParamMethodArgumentResolver`, `PathVariableMethodArgumentResolver` | [인자 해석](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/01_InvocableHandlerMethod.getMethodArgumentValues/README.md) |
| `@ModelAttribute` | `ModelFactory`, `ModelAttributeMethodProcessor` | [모델 준비](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/01_ModelFactory.initModel/README.md) |
| `@InitBinder` | `RequestMappingHandlerAdapter`(메서드 수집) → `InitBinderDataBinderFactory` | [핸들러 호출](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/README.md) |
| `@Valid`(인자) | `ValidationAnnotationUtils` → `ModelAttributeMethodProcessor` / `AbstractMessageConverterMethodArgumentResolver` → `DataBinder.validate` | [검증](validation-binding/02_DataBinder.validate/README.md) |
| `@Validated`(클래스 수준) | `MethodValidationPostProcessor` → `MethodValidationInterceptor` (DataBinder 와 무관한 별도 AOP) | [검증](validation-binding/02_DataBinder.validate/README.md) |
| `@ResponseStatus` | `ServletInvocableHandlerMethod`(반환 시 설정), `ResponseStatusExceptionResolver`(예외 시) | [반환값 처리](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/02_ServletInvocableHandlerMethod.invokeAndHandle/README.md) |
| `@SessionAttributes` | `SessionAttributesHandler` → `ModelFactory` | [모델 준비](webmvc-request-processing/02_DispatcherServlet.doDispatch/05_RequestMappingHandlerAdapter.invokeHandlerMethod/01_ModelFactory.initModel/README.md) |
| `@ControllerAdvice`, `@ExceptionHandler` | `ExceptionHandlerExceptionResolver` | [예외 처리](webmvc-request-processing/02_DispatcherServlet.doDispatch/06_DispatcherServlet.processDispatchResult/01_DispatcherServlet.processHandlerException/README.md) |
| `@HttpExchange` | `HttpServiceProxyFactory` | [HTTP 클라이언트](http-client/README.md) |
| `@MessageMapping` (STOMP) | `SimpAnnotationMethodMessageHandler` | [목적지 라우팅](websocket-stomp/04_AbstractMethodMessageHandler.handleMessage/README.md) |
| `@MessageMapping` (RSocket) | `RSocketMessageHandler` | [라우팅](rsocket/03_AbstractMethodMessageHandler.handleMessage/README.md), [프레임 조건](rsocket/spi/RSocketFrameTypeMessageCondition/README.md) |
| `@ConnectMapping` | `RSocketMessageHandler` | [프레임 조건](rsocket/spi/RSocketFrameTypeMessageCondition/README.md) |
| `@RSocketExchange` | `RSocketServiceProxyFactory` | [선언형 클라이언트](rsocket/spi/RSocketExchange/README.md) |
| `@SendTo` | JMS: `MessagingMessageListenerAdapter` / STOMP: `SendToMethodReturnValueHandler` | [JMS 리스너 응답](messaging-jms/02_AbstractMessageListenerContainer.executeListener/01_MessagingMessageListenerAdapter.onMessage/README.md), [STOMP 라우팅](websocket-stomp/04_AbstractMethodMessageHandler.handleMessage/README.md) |
| `@JmsListener` | `JmsListenerAnnotationBeanPostProcessor` | [리스너 호출](messaging-jms/02_AbstractMessageListenerContainer.executeListener/01_MessagingMessageListenerAdapter.onMessage/README.md) |

### 데이터 접근과 테스트

| 애노테이션 | 처리 주체 | 들어가는 자리 |
|---|---|---|
| `@PersistenceContext`, `@PersistenceUnit` | `PersistenceAnnotationBeanPostProcessor` | [주입](orm-jpa/02_PersistenceAnnotationBeanPostProcessor.postProcessProperties/README.md), [공유 프록시](orm-jpa/02_PersistenceAnnotationBeanPostProcessor.postProcessProperties/01_SharedEntityManagerCreator.createSharedEntityManager/README.md) |
| `@Repository` | `PersistenceExceptionTranslationPostProcessor` | [예외 번역 SPI](orm-jpa/spi/PersistenceExceptionTranslator/README.md) |
| `@ContextConfiguration` | `TestContextManager`, `ContextLoader` | [컨텍스트 로딩](test-context/02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md) |
| `@DirtiesContext` | `DirtiesContextTestExecutionListener`, `DirtiesContextBeforeModesTestExecutionListener` | [컨텍스트 로딩](test-context/02_DefaultCacheAwareContextLoaderDelegate.loadContext/README.md) |
| `@ActiveProfiles`, `@TestPropertySource` | `MergedContextConfiguration` 캐시 키 구성 | [컨텍스트 캐시](test-context/spi/ContextCache/README.md) |
| `@Sql` | `SqlScriptsTestExecutionListener` | [리스너 SPI](test-context/spi/TestExecutionListener/README.md) |
| `@MockitoBean` | `BeanOverrideBeanFactoryPostProcessor`, `BeanOverrideTestExecutionListener` | [리스너 SPI](test-context/spi/TestExecutionListener/README.md) |

## 호출형 진입점 — 내가 부르는 것

| 진입점 | 흐름 |
|---|---|
| `ApplicationContext` 생성 / `refresh()` | [컨테이너 기동](container-refresh/README.md) |
| `getBean(...)` | [빈 생성](bean-creation/README.md) |
| `ResourceLoader.getResource`, `Environment.getProperty` | [리소스와 환경](resource-environment/README.md) |
| `ApplicationEventPublisher.publishEvent` | [이벤트 발행](event-publishing/README.md) |
| `ExpressionParser.parseExpression` | [SpEL](spel/README.md) |
| HTTP 요청 (서블릿 컨테이너가 호출) | [MVC 요청 처리](webmvc-request-processing/README.md) |
| HTTP 요청 (리액티브 서버가 호출) | [WebFlux 요청 처리](webflux-request-processing/README.md) |
| `RouterFunctions.route()` 로 만든 라우터 | [함수형 엔드포인트](functional-endpoints/README.md) |
| `RestClient`, `WebClient` | [HTTP 클라이언트](http-client/README.md) |
| `JdbcTemplate` | [JDBC](jdbc/README.md) |
| `DatabaseClient` | [R2DBC](r2dbc/README.md) |
| `EntityManager` (주입받은 프록시) | [JPA 연동](orm-jpa/README.md) |
| `JmsTemplate` | [메시징(JMS)](messaging-jms/README.md) |
| `RSocketRequester` | [RSocket](rsocket/README.md) |
| WebSocket 핸드셰이크 요청 | [WebSocket과 STOMP](websocket-stomp/README.md) |
| `DataBinder` | [검증과 데이터 바인딩](validation-binding/README.md) |
| `MockMvc`, `TestContextManager` | [테스트 컨텍스트](test-context/README.md) |

## 읽는 법

```text
 "이 애노테이션이 언제 어떻게 동작하지?"
   위 표에서 처리 주체를 확인한다
   링크를 따라 그 처리 주체가 호출되는 자리로 들어간다
     --> 앞뒤 단계와 결과가 어디로 가는지가 그 노드에 있다

 컨테이너와 AOP 절은 대개 이 셋 중 하나다
   BeanFactoryPostProcessor   빈 정의를 만들거나 고친다 (@Configuration, @Bean, @EventListener 수집)
   BeanPostProcessor          만들어진 빈에 개입한다 (@Autowired, @PostConstruct, @Scheduled)
   Advisor + 인터셉터          프록시를 씌워 호출을 가로챈다 (@Transactional, @Cacheable)
   세 칸은 배타적이지 않다. @Async 와 @Repository 의 후처리기는
   BeanPostProcessor 이면서 Advisor 를 붙인다

 웹, 메시징, 테스트 절은 그 흐름의 전용 장치다
   HandlerMapping / HandlerAdapter / ArgumentResolver / ExceptionResolver
   MessageHandler / TestExecutionListener
```
