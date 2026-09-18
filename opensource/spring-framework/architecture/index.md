# architecture 인덱스

Spring Framework의 동작을 호출 흐름 단위로 위에서 아래로 따라가는 지도다. 흐름 하나가 폴더 하나이고, 그 안에서는 폴더 하나가 메서드 하나다. 각 README는 위치, 실제 코드, 그 코드의 아스키 워크플로우, 결과가 쓰이는 곳 순서로 되어 있고, 설명 안의 메서드 이름을 누르면 그 메서드 폴더로 들어간다.

| 흐름 | 진입점 | 내용 |
|------|--------|------|
| [container-refresh](container-refresh/README.md) | `AbstractApplicationContext.refresh` | 설정 클래스가 빈 정의로 펼쳐지고 싱글톤과 Lifecycle 빈이 시작되기까지, 메서드 폴더 20개와 SPI 6종 |
| [bean-creation](bean-creation/README.md) | `AbstractBeanFactory.getBean` | 빈 하나가 만들어져 주입·초기화·프록시·소멸 등록을 거치기까지, 메서드 폴더 9개와 SPI 6종 |
| [aop-proxy](aop-proxy/README.md) | `AbstractAutoProxyCreator.postProcessAfterInitialization` | 빈이 프록시로 바뀌고 호출 시 어드바이스 체인이 도는 과정, 메서드 폴더 9개와 SPI 4종 |
| [transaction](transaction/README.md) | `TransactionInterceptor.invoke` | @Transactional 메서드에서 트랜잭션이 열리고 커밋/롤백되기까지, 메서드 폴더 8개와 SPI 5종 |
| [event-publishing](event-publishing/README.md) | `AbstractApplicationContext.publishEvent` | 이벤트가 발행되어 리스너와 @EventListener 메서드로 전달되기까지, 메서드 폴더 4개와 SPI 4종 |
| [webmvc-request-processing](webmvc-request-processing/README.md) | `FrameworkServlet.processRequest` | HTTP 요청 하나가 `DispatcherServlet`을 거쳐 응답이 되기까지, 메서드 폴더 19개와 SPI 8종 |
| [webflux-request-processing](webflux-request-processing/README.md) | `HttpWebHandlerAdapter.handle` | 리액티브 스택에서 요청이 Mono 파이프라인으로 조립되어 응답이 되기까지, 메서드 폴더 5개와 SPI 5종 |

읽는 순서는 위에서 아래다. 컨테이너 기동이 싱글톤을 만들 때 빈 생성 흐름으로 들어가고, 빈 생성의 마지막에서 AOP 프록시 흐름이 갈라지고, 그 인터셉터 체인 위에서 트랜잭션 흐름이 돈다. 기동이 끝나며 발행하는 `ContextRefreshedEvent`가 MVC 요청 처리의 전략 목록을 채운다. 다음 후보는 RestClient/WebClient, 캐시, 스케줄링과 비동기, JDBC 순이다.
