# architecture 인덱스

Spring Framework의 동작을 호출 흐름 단위로 위에서 아래로 따라가는 지도다. 흐름 하나가 폴더 하나이고, 그 안에서는 폴더 하나가 메서드 하나다. 각 README는 위치, 실제 코드, 그 코드의 아스키 워크플로우, 결과가 쓰이는 곳 순서로 되어 있고, 설명 안의 메서드 이름을 누르면 그 메서드 폴더로 들어간다.

| 흐름 | 진입점 | 내용 |
|------|--------|------|
| [webmvc-request-processing](webmvc-request-processing/README.md) | `FrameworkServlet.processRequest` | HTTP 요청 하나가 `DispatcherServlet`을 거쳐 응답이 되기까지, 메서드 폴더 19개와 SPI 8종 |

다음 후보는 컨테이너 기동(`refresh`), 빈 생성(`getBean`), AOP 프록시 호출, 트랜잭션, WebFlux 요청 처리 순이다.
