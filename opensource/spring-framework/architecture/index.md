# architecture 인덱스

Spring Framework의 동작을 호출 흐름 단위로 위에서 아래로 따라가는 지도다. 쓰던 애노테이션이나 클래스에서 거꾸로 찾아 들어가려면 [진입점 인덱스](entry-index.md)를 먼저 본다. 흐름 하나가 폴더 하나이고, 그 안에서는 폴더 하나가 메서드 하나다. 각 README는 위치, 실제 코드, 그 코드의 아스키 워크플로우, 결과가 쓰이는 곳 순서로 되어 있고, 설명 안의 메서드 이름을 누르면 그 메서드 폴더로 들어간다.

| 흐름 | 진입점 | 내용 |
|------|--------|------|
| [resource-environment](resource-environment/README.md) | `ResourceLoader` / `Environment` | 위치 문자열이 리소스가 되고 ${...} 가 값이 되기까지. 메서드 폴더 3개와 SPI 4종 |
| [container-refresh](container-refresh/README.md) | `AbstractApplicationContext.refresh` | 설정 클래스가 빈 정의로 펼쳐지고 싱글톤과 Lifecycle 빈이 시작되기까지, 메서드 폴더 20개와 SPI 6종 |
| [bean-creation](bean-creation/README.md) | `AbstractBeanFactory.getBean` | 빈 하나가 만들어져 주입·초기화·프록시·소멸 등록을 거치기까지, 메서드 폴더 9개와 SPI 6종 |
| [aop-proxy](aop-proxy/README.md) | `AbstractAutoProxyCreator.postProcessAfterInitialization` | 빈이 프록시로 바뀌고 호출 시 어드바이스 체인이 도는 과정, 메서드 폴더 9개와 SPI 4종 |
| [transaction](transaction/README.md) | `TransactionInterceptor.invoke` | @Transactional 메서드에서 트랜잭션이 열리고 커밋/롤백되기까지, 메서드 폴더 8개와 SPI 5종 |
| [caching](caching/README.md) | `CacheInterceptor.invoke` | @Cacheable 메서드에서 캐시 조회, 실행, 저장, 제거가 일어나는 순서. 메서드 폴더 3개와 SPI 5종 |
| [scheduling-async](scheduling-async/README.md) | `@Scheduled` 후처리기 / `AsyncExecutionInterceptor` | 주기 작업 등록과 비동기 호출 전환을 함께. 메서드 폴더 3개와 SPI 5종 |
| [jdbc](jdbc/README.md) | `JdbcTemplate.execute` | 커넥션 획득, SQL 실행, 결과 매핑, 예외 변환까지. 메서드 폴더 3개와 SPI 4종 |
| [r2dbc](r2dbc/README.md) | `DatabaseClient` / `R2dbcTransactionManager` | 논블로킹 드라이버로 쿼리를 조립하고 구독 시점에 실행하기까지, 커넥션은 구독 컨텍스트에 묶인다. 메서드 폴더 6개와 SPI 6종 |
| [orm-jpa](orm-jpa/README.md) | `LocalContainerEntityManagerFactoryBean` / `JpaTransactionManager` | EntityManagerFactory 생성, @PersistenceContext 공유 프록시, 트랜잭션 바인딩과 예외 변환. 메서드 폴더 9개와 SPI 5종 |
| [event-publishing](event-publishing/README.md) | `AbstractApplicationContext.publishEvent` | 이벤트가 발행되어 리스너와 @EventListener 메서드로 전달되기까지, 메서드 폴더 4개와 SPI 4종 |
| [webmvc-request-processing](webmvc-request-processing/README.md) | `FrameworkServlet.processRequest` | HTTP 요청 하나가 `DispatcherServlet`을 거쳐 응답이 되기까지, 메서드 폴더 19개와 SPI 8종 |
| [webflux-request-processing](webflux-request-processing/README.md) | `HttpWebHandlerAdapter.handle` | 리액티브 스택에서 요청이 Mono 파이프라인으로 조립되어 응답이 되기까지, 메서드 폴더 4개와 SPI 5종 |
| [functional-endpoints](functional-endpoints/README.md) | `RouterFunction` / `HandlerFunction` | 람다로 쓴 엔드포인트가 라우팅되고 응답을 쓰기까지, 서블릿과 리액티브를 나란히. 메서드 폴더 7개와 SPI 6종 |
| [websocket-stomp](websocket-stomp/README.md) | `WebSocketHttpRequestHandler` / `StompSubProtocolHandler` | 핸드셰이크로 연결이 승격되고 STOMP 프레임이 채널을 거쳐 브로커와 @MessageMapping 에 닿기까지. 메서드 폴더 8개와 SPI 6종 |
| [sockjs](sockjs/README.md) | `SockJsHttpRequestHandler` / `TransportHandlingSockJsService` | WebSocket 을 못 쓸 때 HTTP 요청 여러 개를 세션 하나로 엮는 폴백. 메서드 폴더 5개와 SPI 5종 |
| [rsocket](rsocket/README.md) | `RSocketRequester` / `MessagingRSocket` | 프레임 타입이 곧 상호작용이 되는 경로. 요청자 인코딩부터 라우팅과 응답 반환까지. 메서드 폴더 5개와 SPI 5종 |
| [http-client](http-client/README.md) | `RestClient` / `WebClient` | 클라이언트가 요청을 보내고 응답을 객체로 바꾸기까지, 동기와 리액티브를 나란히. 메서드 폴더 4개와 SPI 4종 |
| [test-context](test-context/README.md) | `TestContextManager` / `MockMvc` | 테스트 컨텍스트가 캐시되고 주입되는 과정과 MockMvc 호출 경로. 메서드 폴더 3개와 SPI 5종 |
| [spel](spel/README.md) | `ExpressionParser` / `SpelExpression` | 식 문자열이 구문 트리로 파싱되고 평가 문맥 위에서 값이 되기까지. 메서드 폴더 4개와 SPI 5종 |
| [messaging-jms](messaging-jms/README.md) | `JmsTemplate` / 리스너 컨테이너 | 메시지 송신과 @JmsListener 수신, 커밋과 롤백 규칙. 메서드 폴더 4개와 SPI 4종 |
| [validation-binding](validation-binding/README.md) | `DataBinder` | 요청 값이 객체 필드로 들어가고 @Valid 검증 오류가 모이기까지. 메서드 폴더 2개와 SPI 4종 |

읽는 순서는 위에서 아래다. 컨테이너 기동이 싱글톤을 만들 때 빈 생성 흐름으로 들어가고, 빈 생성의 마지막에서 AOP 프록시 흐름이 갈라지고, 그 인터셉터 체인 위에서 트랜잭션 흐름이 돈다. 기동이 끝나며 발행하는 `ContextRefreshedEvent`가 MVC 요청 처리의 전략 목록을 채운다. 함수형 엔드포인트는 그 MVC와 WebFlux의 뼈대에 다른 구현을 끼운 갈래라 두 흐름 다음에 읽으면 된다. JPA 연동은 빈 생성과 트랜잭션 골격 위에 얹히므로 그 둘을 읽은 뒤에 보면 된다. R2DBC 는 JDBC 흐름과 짝을 이루므로 그 뒤에 나란히 읽으면 차이가 잘 보인다. WebSocket/STOMP 는 요청-응답이 아니라 양방향 메시지라 MVC 흐름을 읽은 뒤에 보면 대비가 분명하다. RSocket 은 STOMP 와 같은 메시징 골격을 쓰되 프레임 타입이 상호작용을 정하므로 WebSocket/STOMP 다음에 읽으면 대비가 분명하다. SockJS 는 WebSocket/STOMP 의 앞단이라 그 흐름을 읽은 뒤에 보면 된다. 지금까지 22개 흐름을 그렸다. 남은 후보는 외부 브로커 릴레이와 AOT/네이티브다.
